import json,os,numpy as np,collections
R=os.path.expanduser('~/.cache/maze-dataset/')
rows=[r for r in json.load(open(R+'heldout/results.json')) if r['role']=='heldout']
print('| frame | size | distortion | k1 | px/cell | score | wrong | jitter mean / min | user corners | max conf of a wrong edge | right edges at or under it | wrong >0.5/>0.3/>0.2 | rule-breaking wrong edges |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for r in sorted(rows,key=lambda r:r['score']):
    ic='' if r['imageCornersScore'] is None else f"{r['imageCornersScore']*100:.2f}"
    W=r['wrongEdges'];c=[w['confidence'] for w in W];rb=collections.Counter(x for w in W for x in w['rules'])
    print(f"| {r['id']} | {r['size']} | {r['distortion']} | {r['k1']:+.3f} | {r['pxPerCell']} | {r['score']*100:.2f} | {r['wrong']} | {r['jitterMean']*100:.2f} / {r['jitterMin']*100:.2f} | {ic} | {r['maxWrongConfidence']:.2f} | {r['rightUnderMax'] if W else 0} | {sum(x>0.5 for x in c)}/{sum(x>0.3 for x in c)}/{sum(x>0.2 for x in c)} | {sum(1 for w in W if w['rules'])} {dict(rb) if rb else ''} |")
def avg(sel,k='score'): v=[r[k] for r in rows if sel(r)];return f"{np.mean(v)*100:.2f} (n={len(v)})" if v else '-'
print()
for name,sel in [('all',lambda r:True),('classic 16x16',lambda r:r['size']==16),('half size 32x32',lambda r:r['size']==32),('distortion none',lambda r:r['distortion']=='none'),('distortion mild',lambda r:r['distortion']=='mild'),('distortion fisheye',lambda r:r['distortion']=='fisheye'),('classic, no distortion',lambda r:r['size']==16 and r['distortion']=='none')]:
    sub=[r for r in rows if sel(r)]
    print(f"{name}: exact {avg(sel)}, jitter {avg(sel,'jitterMean')}, zero-wrong frames {sum(r['wrong']==0 for r in sub)}/{len(sub)}")
W=[w for r in rows for w in r['wrongEdges']];c=np.array([w['confidence'] for w in W]);right=np.concatenate([r['rightConfidences'] for r in rows])
print(f"\nwrong edges {len(W)}: conf>0.5 {int((c>0.5).sum())}, >0.3 {int((c>0.3).sum())}, >0.2 {int((c>0.2).sum())}; max {c.max():.3f}; right edges at or under max {int((right<=c.max()).sum())} of {len(right)}")
for name,sel in [('classic',lambda r:r['size']==16),('half size',lambda r:r['size']==32),('none',lambda r:r['distortion']=='none'),('mild',lambda r:r['distortion']=='mild'),('fisheye',lambda r:r['distortion']=='fisheye')]:
    sub=[r for r in rows if sel(r)];cw=np.array([w['confidence'] for r in sub for w in r['wrongEdges']] or [0]);rc=np.concatenate([r['rightConfidences'] for r in sub])
    print(f"  {name}: wrong {sum(r['wrong'] for r in sub)}, max conf {cw.max():.3f}, right edges under it {int((rc<=cw.max()).sum())}/{len(rc)}; 90% of wrong under {np.quantile(cw,0.9):.3f} -> right under {int((rc<=np.quantile(cw,0.9)).sum())}")
rb=collections.Counter(x for w in W for x in w['rules']);print('rules broken by wrong edges:',dict(rb),'wrong edges breaking any rule',sum(1 for w in W if w['rules']),'of',len(W))
print('missed vs invented:',sum(w['truth'] for w in W),sum(not w['truth'] for w in W))
