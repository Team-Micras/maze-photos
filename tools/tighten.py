import json,os,sys,cv2,numpy as np
sys.path.insert(0,os.path.dirname(__file__))
import fit
R=os.path.expanduser('~/.cache/maze-dataset/')
def walls(e):
    n,Hh,Vv=fit.parse(fit.V+e['mazeFiles'][0]); return n,Hh,Vv
class Contrast:
    def __init__(s,img,n,Hh,Vv):
        s.f=fit.features(img);s.n=n;s.h,s.w=img.shape[:2];ts=np.linspace(.25,.75,9)
        E=[((j,i),(j+1,i),Hh[i,j]) for i in range(1,n) for j in range(n)]+[((j,i),(j,i+1),Vv[i,j]) for i in range(n) for j in range(1,n)]
        s.T=np.array([e[2] for e in E]);s.ne=len(E);s.nt=len(ts)
        s.A=np.array([[a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t] for a,b,_ in E for t in ts],np.float32)
    def __call__(s,C):
        n=s.n;H=cv2.getPerspectiveTransform(np.float32([[0,0],[n,0],[n,n],[0,n]]),np.float32(C))
        p=cv2.perspectiveTransform(s.A[None],H)[0]
        ins=(p[:,0]>=0)&(p[:,0]<s.w-1)&(p[:,1]>=0)&(p[:,1]<s.h-1)
        v=np.full(len(p),np.nan,np.float32);v[ins]=s.f[p[ins,1].astype(int),p[ins,0].astype(int)]
        f=np.nanmean(v.reshape(s.ne,s.nt),1);ok=~np.isnan(f)
        return f[ok&s.T].mean()-f[ok&~s.T].mean()
def descend(sc,C,steps):
    C=np.float32(C).copy();cur=sc(C)
    for st in steps:
        imp=True
        while imp:
            imp=False
            for k in range(4):
                for d in range(2):
                    for sg in(-1,1):
                        D=C.copy();D[k,d]+=sg*st;v=sc(D)
                        if v>cur+1e-6:cur,C,imp=v,D,True
    return C,cur
if __name__=='__main__':
    D=json.load(open(R+'dataset.json'))
    for e in D:
        if e['match']!='confirmed': continue
        img=cv2.imread(R+f"frames/{e['id']}.jpg");n,Hh,Vv=walls(e);assert n==e['gridSize']
        sc=Contrast(img,n,Hh,Vv);C0=np.float32(e.get('cornersPrev',e['corners']))
        s0=sc(C0);ppc=e['pxPerCell'];C,s=descend(sc,C0,[x*ppc/40 for x in (4,2,1,.5,.25)])
        mv=np.linalg.norm(C-C0,axis=1)
        e.setdefault('cornersPrev',e['corners']);e['corners']=[[round(float(x),1),round(float(y),1)] for x,y in C];e['contrast']=round(float(s),3)
        fit.overlay(img,Hh,Vv,C,n,R+f"overlays/{e['id']}.jpg",f"{e['id']}  confirmed  contrast {s:.2f}  (corners tightened)")
        print(f"{e['id']:38s} contrast {s0:.3f}->{s:.3f}  corner moves px {' '.join(f'{m:5.1f}' for m in mv)}  ({mv.max()/ppc:.2f} cell)")
    json.dump(D,open(R+'dataset.json','w'),indent=1,ensure_ascii=False)
