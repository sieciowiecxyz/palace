#!/usr/bin/env python3
"""Source-based gprMax storage/CFL planning, never a solver or accuracy benchmark.

Six real Yee fields plus six uint32 material IDs. PML auxiliary arrays,
coefficients, interfaces, geometry tags and outputs are excluded from base bytes.
Streaming time assumes ideal bandwidth for fields only, not measured runtime.
"""
import argparse
import json
import math

C = 299792458.0


def positive(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
        raise ValueError('Expected finite positive number')
    return value


def vector(values):
    if len(values) != 3:
        raise ValueError('Expected three spatial dimensions')
    return [positive(v) for v in values]


def estimate(length_mm, step_mm, time_ns=100, precision='single', padding=0,
             bandwidth_gbs=896):
    length_mm, step_mm = vector(length_mm), vector(step_mm)
    positive(time_ns); positive(bandwidth_gbs)
    if precision not in ['single', 'double']:
        raise ValueError('Expected single/double precision')
    if isinstance(padding, bool) or not isinstance(padding, int) or padding < 0:
        raise ValueError('Expected nonnegative integer padding')
    cells = [math.ceil(length/step)+2*padding for length, step in zip(length_mm, step_mm)]
    nodes, volumes = math.prod(n+1 for n in cells), math.prod(cells)
    size = 4 if precision == 'single' else 8
    fields, ids = nodes*6*size, nodes*6*4
    dt = 1/(C*math.sqrt(sum(1/(h*.001)**2 for h in step_mm)))
    steps = math.ceil(time_ns*1e-9/dt)
    return dict(length_mm=length_mm, step_mm=step_mm, cells=cells, nodes=nodes,
                precision=precision, padding_per_side_cells=padding,
                device_base_bytes=fields+ids, fields_bytes=fields, ids_bytes=ids,
                host_build_base_bytes=fields+ids+22*volumes,
                dt_seconds=dt, time_ns=time_ns, steps=steps,
                field_only_ideal_streaming_seconds=2*fields*steps/(bandwidth_gbs*1e9),
                bandwidth_gbs=bandwidth_gbs,
                full_field_DFT_one_frequency_bytes=2*fields,
                scope='Planning only: base arrays omit overhead; host bytes are logical allocations, not RSS. Ideal fields-only streaming excludes IDs/PML/stencil/compute, not measured time')


def hsg_estimate(length_mm, step_mm, fine_length_mm, ratio, time_ns=100):
    if isinstance(ratio, bool) or not isinstance(ratio, int) or ratio <= 1 or ratio % 2 == 0:
        raise ValueError('Refining HSG ratio must be an odd integer >1')
    length_mm, step_mm, fine_length_mm = vector(length_mm), vector(step_mm), vector(fine_length_mm)
    # Pinned gprMax defaults: IS/OS separation3 coarse cells, separation r//2+2
    # fine cells, plus six subgrid PML cells. Both main and fine grids use FP64.
    padding = 3*ratio + ratio//2+2+6
    main = estimate(length_mm, step_mm, time_ns, 'double')
    # Cover the requested working region using whole coarse cells at its faces.
    aligned = [math.ceil(length/step)*step for length, step in zip(fine_length_mm, step_mm)]
    fine = estimate(aligned, [h/ratio for h in step_mm], time_ns, 'double', padding)
    if any(fine_length+2*padding*step/ratio > domain
           for fine_length, step, domain in zip(aligned, step_mm, length_mm)):
        raise ValueError('Padded subgrid does not fit inside main domain')
    return dict(main=main, fine=fine, ratio=ratio, requested_fine_length_mm=fine_length_mm,
                device_base_bytes=main['device_base_bytes']+fine['device_base_bytes'],
                host_build_base_bytes=main['host_build_base_bytes']+fine['host_build_base_bytes'],
                field_only_ideal_streaming_seconds=main['field_only_ideal_streaming_seconds']+fine['field_only_ideal_streaming_seconds'],
                scope='Single-box HSG lower storage estimate, not placement/stability/geometry/port validation; excludes interface/PML auxiliaries')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--length-mm', nargs=3, type=float, required=True)
    parser.add_argument('--step-mm', nargs=3, type=float, required=True)
    parser.add_argument('--time-ns', type=float, default=100)
    parser.add_argument('--precision', choices=['single', 'double'], default='single')
    parser.add_argument('--hsg-box-mm', nargs=3, type=float)
    parser.add_argument('--hsg-ratio', type=int)
    args = parser.parse_args()
    if (args.hsg_box_mm is None) != (args.hsg_ratio is None):
        parser.error('HSG requires both box and ratio')
    result = (hsg_estimate(args.length_mm, args.step_mm, args.hsg_box_mm, args.hsg_ratio, args.time_ns)
              if args.hsg_box_mm else estimate(args.length_mm, args.step_mm, args.time_ns, args.precision))
    print(json.dumps(result, indent=2, allow_nan=False))
