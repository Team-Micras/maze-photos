import cv2,numpy as np,json,os,sys
sys.path.insert(0,os.path.dirname(__file__))
from lens import model
R=os.path.expanduser('~/.cache/maze-dataset/')
W=json.load(open(R+'heldout/wrong.json'));E={e['id']:e for e in json.load(open(R+'dataset.json'))}
V='/home/santi/Code/MicroMouse/Micras/worktrees/maze-studio-photo/vendor/mazefiles/'
# Same drawing as maze-studio-photo/tools/diff.py, any size; distorted frames are drawn through their k1 lens fit so the lines sit on the walls.
for f,d in W.items():
    if 'wrong' not in d: continue
    n=d['size'];img=cv2.imread(R+f'frames/{f}.jpg');h,w=img.shape[:2];e=E[f]
    L=[l for l in open(V+d['mazeFile']).read().split('\n') if l][:2*n+1]
    Hh=np.array([[L[2*i][4*j+1:4*j+4]=='---' for j in range(n)] for i in range(n+1)])
    Vv=np.array([[L[2*i+1][4*j]=='|' for j in range(n+1)] for i in range(n)])
    wrong={(dr,x,y) for dr,x,y,_ in d['wrong']}
    lens=e['distortion']!='none' and e.get('lensFit')
    if lens:
        hv,k1=np.array(e['lensFit']['h']),e['lensFit']['k1'];c=np.array([w/2,h/2]);s=np.hypot(w,h)/2
        P=lambda u,v:tuple(int(round(q)) for q in model(hv,k1,np.array([[u,v]],float),c,s)[0])
    else:
        H=cv2.getPerspectiveTransform(np.float32([[0,0],[n,0],[n,n],[0,n]]),np.float32(d['corners']))
        P=lambda u,v:tuple(int(round(q)) for q in cv2.perspectiveTransform(np.float32([[[u,v]]]),H)[0,0])
    lw=max(2,w//(400 if n==16 else 700))
    ov=img.copy();marks=[]
    for i in range(n+1):
        for j in range(n):
            t=Hh[i,j]
            if ('horizontal',j,n-i) in wrong: marks.append(((j,i),(j+1,i),t))
            elif t: cv2.line(ov,P(j,i),P(j+1,i),(80,220,80),lw)
    for i in range(n):
        for j in range(n+1):
            t=Vv[i,j]
            if ('vertical',j,n-1-i) in wrong: marks.append(((j,i),(j,i+1),t))
            elif t: cv2.line(ov,P(j,i),P(j,i+1),(80,220,80),lw)
    img=cv2.addWeighted(ov,0.55,img,0.45,0)
    for a,b,t in marks:
        cv2.line(img,P(*a),P(*b),(0,0,0),3*lw+4)
        cv2.line(img,P(*a),P(*b),(40,40,255) if t else (255,230,0),3*lw)
    lab=f"{f}  {len(marks)} erros   verde=certa  vermelho=parede nao vista  ciano=parede inventada"+("  (desenho com k1)" if lens else "")
    cv2.rectangle(img,(0,0),(img.shape[1],34),(0,0,0),-1)
    cv2.putText(img,lab,(10,24),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2)
    cv2.imwrite(R+f'heldout/diff/{f}.jpg',img,[cv2.IMWRITE_JPEG_QUALITY,85])
print(len(os.listdir(R+'heldout/diff')))
