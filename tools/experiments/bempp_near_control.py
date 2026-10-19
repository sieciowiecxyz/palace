"""Small regular-kernel equivalence and adaptive near-panel control, not RF qualification."""
import argparse
import json
from pathlib import Path
import resource
import time
import numpy as np
import bempp_cl.api as bem
from bempp_cl.api.integration.triangle_gauss import rule
import bempp_pairing as pairing
import bempp_transmission as transmission
import maxwell_near as near


def native(space,t,h,points,k,order):
    params=bem.DefaultParameters()
    params.quadrature.regular=order
    opts=dict(parameters=params,device_interface='numba',precision='double')
    electric=bem.operators.potential.maxwell.electric_field(space,points.T.copy(),k,**opts)
    magnetic=bem.operators.potential.maxwell.magnetic_field(space,points.T.copy(),k,**opts)
    t,h=bem.GridFunction(space,coefficients=t),bem.GridFunction(space,coefficients=h)
    return np.stack([(electric*t).T,(magnetic*t).T,(electric*h).T,(magnetic*h).T],axis=1)


def relative(a,b):return float(np.linalg.norm(a-b)/np.linalg.norm(b))


def run(level,output,backend='numpy'):
    if level!=1:raise ValueError('Near control is deliberately bounded at level1')
    start=time.monotonic()
    if backend=='numba':import maxwell_near_jit as kernel
    elif backend=='numpy':kernel=near
    else:raise ValueError('Unknown near-panel backend')
    jit_setup_seconds=None
    rows=[]
    k=np.sqrt(2.94)
    quadrature=rule(8)
    for name in ['single_panel','closed_polyhedron']:
        if name=='single_panel':
            vertices=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
            grid=bem.Grid(vertices.T,np.array([[0,1,2]],dtype=np.uint32).T)
            space=bem.function_space(grid,'RWG',0,include_boundary_dofs=True)
            points=np.array([[.23,.19,.002],[.23,.19,.02],[.23,.19,.2],
                             [.23,.19,-.02],[.6,-.4,.3],[.2,.3,1.4]])
        else:
            grid=transmission.surface(1)
            space=bem.function_space(grid,'RWG',0)
            points=np.array([[0.,0.,0.],[.17,-.12,.23],[.3,.4,1.4]])
        index=np.arange(space.global_dof_count)
        t=np.sin(index+.2)+.3j*np.cos(index+.7)
        h=np.cos(index+.4)-.2j*np.sin(index+.9)
        panels=near.panels(space,t,h)
        if backend=='numba' and jit_setup_seconds is None:
            before=time.monotonic()
            kernel.integrate(points[0],panels[0],k,*quadrature)
            kernel.adaptive(points[0],panels[0],k,*pairing.quadrature(6),ratio=2.)
            jit_setup_seconds=time.monotonic()-before
        exact=native(space,t,h,points,k,8)
        regular=np.asarray([sum((kernel.integrate(point,panel,k,*quadrature) for panel in panels),np.zeros((4,3),complex)) for point in points])
        row=dict(name=name,triangles=grid.number_of_elements,dofs=space.global_dof_count,
                 regular_vs_native_relative=relative(regular,exact),operators=['Tt','Kt','Th','Kh'],
                 regular_vs_native_by_operator=[relative(regular[:,i],exact[:,i]) for i in range(4)])
        if max(row['regular_vs_native_by_operator'])>1e-12:raise ValueError('Physical panel kernel disagrees with pinned native potential')
        if backend=='numba':
            python_regular=np.asarray([sum((near.integrate(point,panel,k,*quadrature) for panel in panels),np.zeros((4,3),complex)) for point in points])
            row['jit_vs_numpy_regular']=max(relative(regular[:,i],python_regular[:,i]) for i in range(4))
            if row['jit_vs_numpy_regular']>1e-12:raise ValueError('JIT regular panel kernel differs from NumPy reference')
        if name=='single_panel':
            ratio_study=[]
            for ratio in [2.,4.]:
                values=[]
                stats=[]
                for order in [6,8]:
                    begin=time.monotonic()
                    q=pairing.quadrature(order)
                    fields=[];leaves=hits=depth=0
                    for point in points:
                        field,info=kernel.adaptive(point,panels[0],k,*q,ratio=ratio)
                        fields.append(field);leaves+=info['leaves'];hits+=info['depth_hits'];depth=max(depth,info['max_depth'])
                    values.append(np.asarray(fields))
                    stats.append(dict(order=order,leaves=leaves,depth_hits=hits,max_depth=depth,seconds=time.monotonic()-begin))
                ratio_study.append(dict(ratio=ratio,stats=stats,global_relative=relative(values[0],values[1]),
                    max_point_operator=max(relative(values[0][p,i],values[1][p,i]) for p in range(len(points)) for i in range(4))))
                if backend=='numba':
                    before=time.monotonic()
                    python_values=np.asarray([near.adaptive(point,panels[0],k,*pairing.quadrature(8),ratio=ratio)[0] for point in points])
                    ratio_study[-1]['numpy_q8_seconds']=time.monotonic()-before
                    ratio_study[-1]['jit_vs_numpy_q8']=max(relative(values[1][p,i],python_values[p,i]) for p in range(len(points)) for i in range(4))
                    if ratio_study[-1]['jit_vs_numpy_q8']>1e-12:raise ValueError('JIT adaptive kernel differs from NumPy reference')
                np.savez(output/f'panel-ratio{int(ratio)}.npz',adaptive6=values[0],adaptive8=values[1])
            row.update(adaptive_q6_vs8_relative=relative(values[0],values[1]),adaptive_stats=stats,
                       adaptive_q6_vs8_max_point_operator=max(relative(values[0][p,i],values[1][p,i]) for p in range(len(points)) for i in range(4)),
                       regular_q8_vs_adaptive_q8_relative=relative(regular,values[1]),ratio_study=ratio_study)
            # Constant tangential currents give an independent Laplace normal check.
            constant=np.stack([np.tile([1.,0.,0.],(3,1)),np.tile([0.,1.,0.],(3,1))])
            static_panel=(panels[0][0],constant,np.zeros(2))
            static_k=1e-5
            computed=[];solid_angle=[];depth_hits=0
            for point in points:
                field,info=kernel.adaptive(point,static_panel,static_k,*pairing.quadrature(8),ratio=2.)
                computed.append((field[1,1]-field[3,0])/2)
                solid_angle.append(near.laplace_normal_reference(static_panel[0],point))
                depth_hits+=info['depth_hits']
            static_error=float(np.max(abs(np.asarray(computed)-solid_angle)))
            area=np.linalg.norm(np.cross(vertices[1]-vertices[0],vertices[2]-vertices[0]))/2
            max_kr=static_k*np.max(np.linalg.norm(points[:,None,:]-vertices[None,:,:],axis=2))
            row['static_normal_control']=dict(k=static_k,absolute_error=static_error,depth_hits=depth_hits,
                helmholtz_vs_laplace_bound=(1+max_kr)*static_k**2*area/(8*np.pi),
                reference='SciPy1.15.3 calculate_solid_angles, Van Oosterom-Strackee',target=1e-8)
            np.savez(output/'panel-fields.npz',points=points,regular=regular,native=exact,adaptive6=values[0],adaptive8=values[1])
        rows.append(row)
        print(json.dumps(dict(stage=name+'_complete',elapsed_s=time.monotonic()-start)),flush=True)
    control=bool(max(r['regular_vs_native_relative'] for r in rows)<1e-12 and
                 all(r['max_point_operator']<1e-6 and not any(s['depth_hits'] for s in r['stats']) for r in rows[0]['ratio_study']) and
                 rows[0]['static_normal_control']['absolute_error']<1e-8 and not rows[0]['static_normal_control']['depth_hits'])
    report=dict(scope=__doc__,level=level,backend=backend,jit_compile_or_load_seconds=jit_setup_seconds,rows=rows,execution_passed=True,analytic_target_passed=False,
                jit_nopython_signatures=[str(s) for s in kernel._adaptive.nopython_signatures] if backend=='numba' else None,
                operator_control_passed=control,target=dict(native_kernel=1e-12,adaptive_quadrature=1e-6),
                elapsed_seconds=time.monotonic()-start,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                limitations=['Operator equivalence and adaptive self-convergence only, not an analytic physical solution',
                             'No correction of saved whole-volume potentials or antenna promotion yet'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--near-backend',choices=['numpy','numba'],default='numpy')
    args=parser.parse_args()
    run(args.level,args.output,args.near_backend)
