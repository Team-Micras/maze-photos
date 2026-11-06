import json,os
R=os.path.expanduser('~/.cache/maze-dataset/')
D=json.load(open(R+'dataset.json'));V=json.load(open(R+'verdicts.json'))
for e in D:
    v=V.get(e['id'])
    if not v: continue
    e['review']=dict(reviewedBy='owner',**{k:v[k] for k in ('verdict','comment','cornersOk') if k in v})
    if e['match']=='likely' and v.get('verdict')=='ok': e['match']='confirmed';e['promotedFrom']='likely'
    if e['id']=='all-japan-2019-classic-unknown-2': e['exclude']='walls removed lying on the board'
json.dump(D,open(R+'dataset.json','w'),indent=1,ensure_ascii=False)
import collections;print(collections.Counter(e['match'] for e in D),sum('review' in e for e in D),[e['id'] for e in D if 'review' not in e])
