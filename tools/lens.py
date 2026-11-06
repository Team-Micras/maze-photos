import json,os,sys,cv2,numpy as np
from scipy.optimize import least_squares
sys.path.insert(0,os.path.dirname(__file__))
import fit
R=os.path.expanduser('~/.cache/maze-dataset/')
# Model: image = c + (q-c)(1 + k1 r^2), q = H(u,v), r = |q-c| / (half the image diagonal), c = image centre.
def distort(q,k1,c,s):
    d=q-c;r2=(d**2).sum(-1,keepdims=True)/s**2;return c+d*(1+k1*r2)
def undistort(p,k1,c,s):
    q=p.copy()
    for _ in range(30): d=q-c;q=c+(p-c)/(1+k1*(d**2).sum(-1,keepdims=True)/s**2)
    return q
def homog(h,uv):
    H=np.append(h,1).reshape(3,3);x=np.c_[uv,np.ones(len(uv))]@H.T;return x[:,:2]/x[:,2:]
def model(h,k1,uv,c,s): return distort(homog(h,uv),k1,c,s)
def posts(n,Hh,Vv):
    out=[]
    for i in range(n+1):
        for j in range(n+1):
            dirs={'E':j<n and Hh[i,j],'W':j>0 and Hh[i,j-1],'S':i<n and Vv[i,j],'N':i>0 and Vv[i-1,j]}
            inside={'E':j<n,'W':j>0,'S':i<n,'N':i>0}
            if (dirs['E'] or dirs['W']) and (dirs['N'] or dirs['S']): out.append((j,i,{k:bool(v) for k,v in dirs.items() if inside[k]}))
    return out
STEP={'E':(1,0),'W':(-1,0),'S':(0,1),'N':(0,-1)}
def detect(f,P,pred,ppc):
    h,w=f.shape;Rr=max(3,int(0.3*ppc));off=np.stack(np.meshgrid(np.arange(-Rr,Rr+1),np.arange(-Rr,Rr+1)),-1).reshape(-1,2).astype(np.float32)
    ts=np.linspace(0.12,0.45,8);found=[]
    for (j,i,dirs),p0 in zip(P,pred):
        sc=np.zeros(len(off));nw=0;no=0;ok=True
        for k,wall in dirs.items():
            dx,dy=STEP[k];a=pred_at(j+dx,i+dy,j,i);
            v=(a-p0)
            pts=p0[None,None]+off[:,None]+ts[None,:,None]*v[None,None]
            x=pts[...,0].round().astype(int);y=pts[...,1].round().astype(int)
            if x.min()<0 or y.min()<0 or x.max()>=w or y.max()>=h: ok=False;break
            m=f[y,x].mean(1)
            if wall: sc+=m;nw+=1
            else: sc-=m*0.5;no+=1
        if not ok: found.append(None);continue
        b=off[np.argmax(sc)];edge=np.abs(b).max()>=Rr
        found.append(None if edge else p0+b)
    return found
pred_at=None
def fitmodel(uv,img_pts,c,s,k1free,h0):
    def res(x):
        h=x[:8];k1=x[8] if k1free else 0.0
        return (model(h,k1,uv,c,s)-img_pts).ravel()
    x0=np.r_[h0,0.0] if k1free else h0
    sc=np.r_[np.abs(h0)+1e-3,0.1] if k1free else np.abs(h0)+1e-3
    keep=np.ones(len(uv),bool)
    for _ in range(3):
        r=least_squares(lambda x:(res(x).reshape(-1,2)[keep]).ravel(),x0,x_scale=sc,method='lm' if keep.sum()*2>=len(x0) else 'trf')
        x0=r.x;e=np.linalg.norm(res(x0).reshape(-1,2),axis=1);nk=e<max(3*np.median(e[keep]),1.0)
        if (nk==keep).all(): break
        keep=nk
    return x0[:8],(x0[8] if k1free else 0.0),keep
def hvec(C,n):
    H=cv2.getPerspectiveTransform(np.float32([[0,0],[n,0],[n,n],[0,n]]),np.float32(C));H=H/H[2,2];return H.ravel()[:8]
def run(e,draw=True):
    global pred_at
    img=cv2.imread(R+f"frames/{e['id']}.jpg");h,w=img.shape[:2];c=np.array([w/2,h/2]);s=np.hypot(w,h)/2
    n,Hh,Vv=fit.parse(fit.V+e['mazeFiles'][0]);f=fit.features(img);ppc=e['pxPerCell']
    P=posts(n,Hh,Vv);uv=np.array([(j,i) for j,i,_ in P],float)
    h0=hvec(e['corners'],n);k=0.0
    hh,kk=h0,0.0
    for rnd in range(3):
        pred_at=lambda a,b,j,i:model(hh,kk,np.array([[a,b]],float),c,s)[0] if True else None
        pred=model(hh,kk,uv,c,s)
        # stub direction: towards the neighbour post, scaled to one cell
        def pa(a,b,j,i,_h=hh,_k=kk): return model(_h,_k,np.array([[a,b]],float),c,s)[0]
        pred_at=pa
        D=detect(f,P,pred,ppc);m=np.array([d is not None for d in D]);ip=np.array([d if d is not None else (0,0) for d in D],float)
        hH,_,keepH=fitmodel(uv[m],ip[m],c,s,False,h0)
        hK,kK,keepK=fitmodel(uv[m],ip[m],c,s,True,hH)
        hh,kk=hK,kK
    err=lambda hv,k1,keep:np.linalg.norm(model(hv,k1,uv[m],c,s)-ip[m],axis=1)[keep]
    both=keepH&keepK
    e0=err(h0,0,both);e1=err(hH,0,both);e2=err(hK,kK,both)
    corner_uv=np.array([[0,0],[n,0],[n,n],[0,n]],float)
    cornersImg=model(hK,kK,corner_uv,c,s)
    # largest distance between the k1 model and the homography closest to it over the maze, in cells
    g=np.array([(a,b) for a in np.linspace(0,n,9) for b in np.linspace(0,n,9)])
    mg=model(hK,kK,g,c,s);Hb,_=cv2.findHomography(g,mg,0)
    bend=np.linalg.norm(cv2.perspectiveTransform(g[None],Hb)[0]-mg,axis=1).max()/ppc
    r=dict(h=[float(v) for v in hK],posts=int(both.sum()),before=float(e0.mean()),hFit=float(e1.mean()),k1Fit=float(e2.mean()),k1=float(kK),bendCells=float(bend),
           cornersImage=[[round(float(x),1),round(float(y),1)] for x,y in cornersImg])
    if draw:
        o=img.copy();lw=max(1,w//700)
        def poly(hv,k1,a,b,col):
            t=np.linspace(0,1,12)[:,None];pts=model(hv,k1,np.array(a)*(1-t)+np.array(b)*t,c,s);cv2.polylines(o,[np.int32(pts.round())],False,col,lw+1)
        for i in range(n+1):
            for j in range(n):
                if Hh[i,j]: poly(h0,0,(j,i),(j+1,i),(0,0,255))
        for i in range(n):
            for j in range(n+1):
                if Vv[i,j]: poly(h0,0,(j,i),(j,i+1),(0,0,255))
        for i in range(n+1):
            for j in range(n):
                if Hh[i,j]: poly(hK,kK,(j,i),(j+1,i),(0,255,0))
        for i in range(n):
            for j in range(n+1):
                if Vv[i,j]: poly(hK,kK,(j,i),(j,i+1),(0,255,0))
        for p in ip[m][both]: cv2.circle(o,tuple(np.int32(p.round())),lw+2,(255,255,0),-1)
        cv2.rectangle(o,(0,0),(w,30),(0,0,0),-1)
        cv2.putText(o,f"{e['id']}  red: homography  green: homography+k1={kK:.3f}  cyan: detected posts  mean err {e0.mean():.1f}->{e2.mean():.1f}px",(8,21),0,0.6,(255,255,255),1)
        os.makedirs(R+'lens',exist_ok=True);cv2.imwrite(R+f"lens/{e['id']}.jpg",o,[cv2.IMWRITE_JPEG_QUALITY,85])
    return r
if __name__=='__main__':
    D=json.load(open(R+'dataset.json'));only=sys.argv[1:]
    for e in D:
        if e['match']!='confirmed' or (only and e['id'] not in only): continue
        r=run(e);e['lensFit']=r
        print(f"{e['id']:36s} ppc {e['pxPerCell']:5.1f} posts {r['posts']:4d} err px corners-H {r['before']:5.2f} postfit-H {r['hFit']:5.2f} postfit-H+k1 {r['k1Fit']:5.2f}  k1 {r['k1']:+.4f} bend {r['bendCells']:.2f} cell",flush=True)
    if not only: json.dump(D,open(R+'dataset.json','w'),indent=1,ensure_ascii=False)
