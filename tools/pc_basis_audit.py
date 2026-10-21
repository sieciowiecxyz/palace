"""Strict scope/cache cleanup gate; numerical/field qualification remains separate."""
import json


def analyze(text):
    records=[json.loads(line.split(' ',1)[1]) for line in text.splitlines() if line.startswith('PALACE_PC_BASIS_END ')]
    if len(records)!=1 or 'PALACE_PC_BASIS_ERROR' in text:
        raise ValueError('Missing/duplicated/failed mixed PC basis audit')
    r=records[0]
    if not isinstance(r,dict):raise ValueError('Invalid PC basis audit object')
    for key in ['enters','exits','active','mixed_forward','pc_original','outside_original','transpose_original',
                'alias_original','capacity_original','cache_misses','cache_hits','allocated_bytes','freed_bytes',
                'live_bytes','releases','min_N','scalar_bytes']:
        if not isinstance(r.get(key),int) or isinstance(r[key],bool) or r[key]<0:
            raise ValueError('Invalid mixed PC audit integer '+key)
    if (r['enters']<1 or r['enters']!=r['exits'] or r['active']!=0 or r['mixed_forward']<1
            or r['outside_original']<1 or r['transpose_original']<1 or r['pc_original']<r['transpose_original']
            or not 1<=r['cache_misses']<=256 or r['cache_hits']+r['cache_misses']<r['mixed_forward']
            or not 0<r['allocated_bytes']<=256*3360 or r['allocated_bytes']!=r['freed_bytes'] or r['live_bytes']!=0
            or r['releases']!=1 or r.get('closed') is not True or r['scalar_bytes']!=8 or r['min_N']!=8192):
        raise ValueError('Mixed PC basis scope/coverage/precision/cache cleanup failed')
    return dict(passed=True,counts=r,scope='RAII ApplyB scope and original-call/cache counters; not RF qualification or physical VRAM residency')
