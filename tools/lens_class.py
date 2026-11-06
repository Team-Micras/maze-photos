import json,os
R=os.path.expanduser('~/.cache/maze-dataset/')
D=json.load(open(R+'dataset.json'))
def cls(k1): a=abs(k1); return 'none' if a<0.05 else 'mild' if a<0.2 else 'fisheye'
EYE={'chubu-japan-2026-classic-unknown':'fisheye','uk-2025-classic-unknown':'fisheye','apec-2017-classic-unknown':'fisheye','all-japan-2019-classic-unknown':'none','all-japan-2017-classic-unknown':'none'}
for e in D:
    if 'lensFit' in e: e['k1']=round(e['lensFit']['k1'],4);e['distortion']=cls(e['k1']);e['distortionFrom']='k1 fit on the maze posts (|k1|<0.05 none, <0.2 mild)'
    else:
        e['k1']=None;e['distortion']=next(v for k,v in EYE.items() if e['id'].startswith(k));e['distortionFrom']='owner review / by eye (no maze file)'
json.dump(D,open(R+'dataset.json','w'),indent=1,ensure_ascii=False)
import collections;print(collections.Counter(e['distortion'] for e in D));print([(e['id'],e['k1']) for e in D if e['distortion']!='none'])
