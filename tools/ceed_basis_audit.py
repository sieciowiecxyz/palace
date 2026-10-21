"""Check actual libCEED host metadata, not kernel timings or physical residency."""
import json

MODES = {0:'none',1:'interp',2:'grad',4:'div',8:'curl',16:'weight'}
SPACES = {1:'h1',2:'hdiv',3:'hcurl'}
TOPOLOGIES = {(1<<16):'line',(2<<16)|1:'triangle',(2<<16)|2:'quad',
              (3<<16)|3:'tet',(3<<16)|4:'pyramid',(3<<16)|5:'prism',(3<<16)|6:'hex'}


def integer(row, key, minimum=0):
    if not isinstance(row,dict):
        raise ValueError('Basis audit record must be an object')
    v=row.get(key)
    if not isinstance(v,int) or isinstance(v,bool) or v<minimum:
        raise ValueError('Invalid basis audit integer: '+key)
    return v


def analyze(text):
    rows=[];ends=[]
    for line in text.splitlines():
        if line.startswith('PALACE_BASIS_AUDIT '):rows.append(json.loads(line.split(' ',1)[1]))
        elif line.startswith('PALACE_BASIS_AUDIT_END '):ends.append(json.loads(line.split(' ',1)[1]))
    if len(ends)!=1 or not 1<=len(rows)<=2048:
        raise ValueError('Missing/duplicated/overflowed basis audit coverage')
    end=ends[0]
    if integer(end,'groups')!=len(rows) or integer(end,'errors') or integer(end,'overflow'):
        raise ValueError('Basis audit query/coverage error')
    keys=set();calls=0;measured=[]
    for row in rows:
        for key in ['topology','space','P','Q','components','q_components','elements','eval',
                    'transpose','add','input_length','output_length','scalar_bytes','calls']:
            integer(row,key,1 if key in ['P','Q','components','q_components','calls'] else 0)
        if (row['topology'] not in TOPOLOGIES or row['space'] not in SPACES
                or row['eval'] not in MODES or row['transpose'] not in [0,1]
                or row['add'] not in [0,1] or row['scalar_bytes']!=8):
            raise ValueError('Unexpected pinned basis enum/precision')
        identity=tuple((k,row[k]) for k in sorted(row) if k!='calls')
        if identity in keys:raise ValueError('Duplicated basis audit group')
        keys.add(identity);calls+=row['calls']
        n=row['elements']*row['components'];p=row['P'];q=row['Q'];qc=row['q_components']
        incoming,outgoing=(n*q*qc,n*p) if row['transpose'] else (n*p,n*q*qc)
        if row['eval']==16:
            if row['transpose'] or row['input_length']:
                raise ValueError('Unexpected weight apply contract')
            incoming,outgoing=0,row['elements']*q
        if row['input_length']<incoming or row['output_length']<outgoing:
            raise ValueError('Basis vector shorter than required action')
        measured.append(dict(row,space_name=SPACES[row['space']],topology_name=TOPOLOGIES[row['topology']],
                             eval_name=MODES[row['eval']],N=n,
                             input_bytes=8*row['input_length'],output_bytes=8*row['output_length'],
                             required_input_bytes=8*incoming,required_output_bytes=8*outgoing,
                             basis_coefficients_bytes=8*(q if row['eval']==16 else p*q*qc)))
    if integer(end,'calls',1)!=calls:
        raise ValueError('Basis audit calls not fully represented')
    return dict(passed=True,calls=calls,groups=measured,
                scope='Host API metadata/call counts only; no field copies, GPU timings, PC-role attribution or physical residency',
                max_input_vector_bytes=max(r['input_bytes'] for r in measured),
                max_output_vector_bytes=max(r['output_bytes'] for r in measured))
