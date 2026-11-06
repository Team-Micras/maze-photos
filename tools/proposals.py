import cv2,numpy as np,json,os
R=os.path.expanduser('~/.cache/maze-dataset/')
W=json.load(open(R+'heldout/wrong.json'));res={r['id']:r for r in json.load(open(R+'heldout/results.json'))}
D=json.load(open(R+'dataset.json'))
for e in D:
    if e['id'] not in W or 'proposal' not in W[e['id']]: continue
    d=W[e['id']];n=d['size'];img=cv2.imread(R+f"frames/{e['id']}.jpg");w=img.shape[1]
    H=cv2.getPerspectiveTransform(np.float32([[0,0],[n,0],[n,n],[0,n]]),np.float32(d['corners']))
    P=lambda u,v:tuple(int(round(q)) for q in cv2.perspectiveTransform(np.float32([[[u,v]]]),H)[0,0])
    o=img.copy();lw=max(2,w//500)
    for dr,x,y,c in d['proposal']:
        a,b=((x,n-y),(x+1,n-y)) if dr=='horizontal' else ((x,n-1-y),(x,n-y))
        cv2.line(o,P(*a),P(*b),(0,140,255) if c>=0.3 else (0,200,255),lw if c>=0.3 else max(1,lw-1))
    cv2.polylines(o,[np.int32(np.round(d['corners']))],True,(0,255,255),lw)
    lab=f"{e['id']}  proposal: {len(d['proposal'])} walls (orange; light orange = unsure)  outline = corners"
    cv2.rectangle(o,(0,0),(w,30),(0,0,0),-1);cv2.putText(o,lab,(8,21),0,0.6,(255,255,255),1)
    cv2.imwrite(R+f"overlays/{e['id']}.jpg",o,[cv2.IMWRITE_JPEG_QUALITY,85])
    open(R+f"proposals/{e['id']}.txt",'w').write(d['text']+'\n')
    e['proposal']=dict(walls=len(d['proposal']),unsure=res[e['id']]['unsure'],file=f"proposals/{e['id']}.txt",note='recogniser output at the dataset corners, photo orientation (TL corner = file NW)')
json.dump(D,open(R+'dataset.json','w'),indent=1,ensure_ascii=False)
