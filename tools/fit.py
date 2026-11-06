import cv2,numpy as np,sys,json,os,hashlib,argparse
V='/home/santi/Code/MicroMouse/Micras/worktrees/maze-studio-photo/vendor/mazefiles/'
def parse(p):
    L=[l for l in open(p).read().split('\n') if l]
    n=(len(L)-1)//2
    if len(L)!=2*n+1 or len(L[0])!=4*n+1: return None
    Hh=np.array([[L[2*i][4*j+1:4*j+4]=='---' for j in range(n)] for i in range(n+1)])
    Vv=np.array([[L[2*i+1][4*j]=='|' for j in range(n+1)] for i in range(n)])
    return n,Hh,Vv
_cache={}
def library(n):
    if n in _cache: return _cache[n]
    g={}
    for d in ('classic','halfsize'):
        for f in sorted(os.listdir(V+d)):
            if not f.endswith('.txt'): continue
            h=hashlib.md5(open(V+d+'/'+f,'rb').read()).hexdigest()
            g.setdefault(h,[]).append(f'{d}/{f}')
    out=[]
    for fl in g.values():
        m=parse(V+fl[0])
        if m and m[0]==n and 0.15<(m[1][1:n].mean()+m[2][:,1:n].mean())/2<0.85 and not any(x in fl[0] for x in ('empty','test')): out.append((fl,m[1],m[2]))
    _cache[n]=out; return out
def cellw(Hh,Vv,n): return {'N':Hh[:n],'S':Hh[1:],'W':Vv[:,:n],'E':Vv[:,1:]}
def rot(d): return {'E':np.rot90(d['N'],-1),'S':np.rot90(d['E'],-1),'W':np.rot90(d['S'],-1),'N':np.rot90(d['W'],-1)}
def mir(d): return {'N':d['N'][:,::-1],'S':d['S'][:,::-1],'E':d['W'][:,::-1],'W':d['E'][:,::-1]}
def tohv(d,n):
    Hh=np.zeros((n+1,n),bool);Vv=np.zeros((n,n+1),bool)
    Hh[:n]=d['N'];Hh[n]=d['S'][n-1];Vv[:,:n]=d['W'];Vv[:,n]=d['E'][:,n-1]; return Hh,Vv
def variants(Hh,Vv,n):
    d=cellw(Hh,Vv,n); mk=np.zeros((n,n),int); mk[0,0]=1;mk[0,n-1]=2;mk[n-1,n-1]=3;mk[n-1,0]=4
    out=[]
    for f in (0,1):
        dd=mir(d) if f else d; m=mk[:,::-1] if f else mk
        for k in range(4):
            H2,V2=tohv(dd,n)
            pos={}
            for v,(r,c) in {1:(0,0),2:(0,n-1),3:(n-1,n-1),4:(n-1,0)}.items(): pass
            where={int(m[r,c]):i for i,(r,c) in enumerate([(0,0),(0,n-1),(n-1,n-1),(n-1,0)]) if m[r,c]}
            out.append((k,f,np.concatenate([H2[1:n].ravel(),V2[:,1:n].ravel()]),[where[1],where[2],where[3],where[4]]))
            dd=rot(dd); m=np.rot90(m,-1)
    return out
def edge_pts(n,ts):
    E=[]
    for i in range(1,n):
        for j in range(n): E.append(((j,i),(j+1,i)))
    for i in range(n):
        for j in range(1,n): E.append(((j,i),(j,i+1)))
    return np.array([[a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t] for a,b in E for t in ts],np.float32),len(E)
def features(img,inv=False):
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV); g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)
    f=np.maximum(g/255,((hsv[...,1]>110)&(hsv[...,2]>100)).astype(np.float32))
    if inv: f=1-g/255
    return cv2.GaussianBlur(f,(0,0),1.5)
class Fitter:
    def __init__(s,img,n,inv=False):
        s.img=img;s.n=n;s.f=features(img,inv);s.ts=np.linspace(.25,.75,9);s.A,s.ne=edge_pts(n,s.ts)
        s.lib=library(n);s.var=[[variants(h,v,n) for _,h,v in [(0,x[1],x[2])]][0] for x in s.lib]
        s.T=np.array([[v[2] for v in vs] for vs in s.var]) # maze,8,edges
    def feats(s,C):
        n=s.n;H=cv2.getPerspectiveTransform(np.float32([[0,0],[n,0],[n,n],[0,n]]),np.float32(C))
        p=cv2.perspectiveTransform(s.A[None],H)[0]; h,w=s.img.shape[:2]
        x=np.clip(p[:,0],0,w-1).astype(int);y=np.clip(p[:,1],0,h-1).astype(int)
        ins=(p[:,0]>=0)&(p[:,0]<w)&(p[:,1]>=0)&(p[:,1]<h)
        v=np.where(ins,s.f[y,x],np.nan).reshape(s.ne,len(s.ts)); return np.nanmean(v,1)
    def scores(s,C):
        f=s.feats(C);ok=~np.isnan(f);f=np.where(ok,f,0.0)
        T=s.T&ok[None,None];Fm=ok[None,None]
        nt=T.sum(-1);nf=(Fm&~s.T).sum(-1)
        st=(T*f).sum(-1)/np.maximum(nt,1); sf=((Fm&~s.T)*f).sum(-1)/np.maximum(nf,1)
        return st-sf
    def one(s,C,mi,vi):
        f=s.feats(C);ok=~np.isnan(f);t=s.T[mi,vi]
        a=t&ok;b=(~t)&ok
        return (f[a].mean() if a.any() else 0)-(f[b].mean() if b.any() else 0)
    def rank(s,C):
        S=s.scores(C);best=S.max(1);arg=S.argmax(1);o=np.argsort(-best)
        return [(int(i),float(best[i]),int(arg[i])) for i in o]
    def refine(s,C,mi,vi,steps=(32,16,8,4,2,1,.5)):
        C=np.float32(C).copy();sc=lambda C:s.one(C,mi,vi);cur=sc(C)
        for st in steps:
            imp=True
            while imp:
                imp=False
                for k in range(4):
                    for d in range(2):
                        for sg in (-1,1):
                            D=C.copy();D[k,d]+=sg*st;v=sc(D)
                            if v>cur+1e-5:cur,C,imp=v,D,True
        return C,cur
def run(frame,corners,n=16,inv=False,expect=None,steps=(16,8,4,2,1,.5),jit=0):
    img=cv2.imread(frame) if isinstance(frame,str) else frame
    F=Fitter(img,n,inv);C0=np.float32(corners)
    cand=[i for i,x in enumerate(F.lib) if expect and any(e in f for f in x[0] for e in expect)]
    done={};best=None
    def refine_all(mi):
        r=None
        rng=np.random.RandomState(0)
        starts=[C0]+[C0+rng.uniform(-20,20,(4,2)).astype(np.float32) for _ in range(jit)]
        for vi in range(8):
            for C1 in starts:
                C,s=F.refine(C1,mi,vi,steps)
                if r is None or s>r[0]: r=(s,C,vi)
        return r
    for mi in cand+[m for m,_,_ in F.rank(C0)[:3]]:
        if mi in done: continue
        done[mi]=refine_all(mi)
    for _ in range(2):
        bm=max(done,key=lambda m:done[m][0]);C=done[bm][1]
        top=F.rank(C)[0][0]
        if top in done: break
        done[top]=refine_all(top)
    bm=max(done,key=lambda m:done[m][0]);s,C,vi=done[bm]
    rk=F.rank(C);tv=F.T[bm,vi]
    ham=lambda j:int(min((F.T[j,v]!=tv).sum() for v in range(8)))
    near=[(j,ham(j)) for j in range(len(F.lib)) if j!=bm]
    near=[(j,h) for j,h in near if h<=4]
    nearset={j for j,_ in near}
    nb=[x for x in rk if x[0]!=bm and x[0] not in nearset][0]
    return dict(img=img,F=F,mi=bm,score=s,next=nb[1],nextFiles=F.lib[nb[0]][0],cornersPhoto=C,variant=vi,near=[dict(files=F.lib[j][0],wallsDiffering=h) for j,h in sorted(near,key=lambda x:x[1])])
def fileorder(C,where):
    return [C[w] for w in where]
def overlay(img,mazeHh,mazeVv,fileCorners,n,out,label=None):
    C=np.float32(fileCorners);H=cv2.getPerspectiveTransform(np.float32([[0,0],[n,0],[n,n],[0,n]]),C)
    P=lambda u,v:tuple(int(round(c)) for c in cv2.perspectiveTransform(np.float32([[[u,v]]]),H)[0,0])
    o=img.copy();w=max(1,img.shape[1]//500)
    for i in range(n+1):
        for j in range(n):
            if mazeHh[i,j]:cv2.line(o,P(j,i),P(j+1,i),(0,255,0),w+1)
    for i in range(n):
        for j in range(n+1):
            if mazeVv[i,j]:cv2.line(o,P(j,i),P(j,i+1),(0,255,0),w+1)
    for k,c in enumerate(C):
        cv2.circle(o,(int(c[0]),int(c[1])),5*w,(255,0,255),max(2,w));cv2.putText(o,['NW','NE','SE','SW'][k],(int(c[0])+8,int(c[1])-8),0,0.4*w+.4,(255,0,255),max(1,w))
    if label:
        cv2.rectangle(o,(0,0),(o.shape[1],28),(0,0,0),-1);cv2.putText(o,label,(8,20),0,0.6,(255,255,255),1)
    cv2.imwrite(out,o,[cv2.IMWRITE_JPEG_QUALITY,85])
def fit(frame,corners,n=16,inv=False,out=None,label=None,expect=None,jit=0):
    r=run(frame,corners,n,inv,expect,jit=jit);F=r['F'];mi=r['mi'];vi=r['variant']
    k,f,_,where=F.var[mi][vi]
    fc=[r['cornersPhoto'][w] for w in where]
    fl,Hh,Vv=F.lib[mi]
    res=dict(mazeFiles=fl,score=round(float(r['score']),3),nextBest=round(float(r['next']),3),nextBestFiles=r['nextFiles'][:2],
        corners=[[round(float(x),1),round(float(y),1)] for x,y in fc],orientation=dict(rotation=k*90,mirror=bool(f)),n=n,photoCorners=[[float(x),float(y)] for x,y in r['cornersPhoto']],variant=int(vi),near=r['near'])
    if out: overlay(r['img'],Hh,Vv,fc,n,out,label)
    return res
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('frame');ap.add_argument('corners');ap.add_argument('--n',type=int,default=16);ap.add_argument('--inv',action='store_true');ap.add_argument('--out');ap.add_argument('--jit',type=int,default=0);ap.add_argument('--expect',nargs='*')
    a=ap.parse_args()
    C=[[float(v) for v in c.split(',')] for c in a.corners.split()]
    print(json.dumps(fit(a.frame,C,a.n,a.inv,a.out,None,a.expect,a.jit)))
def outline_refine(img,C,n,inv=False):
    f=features(img,inv);h,w=img.shape[:2];C=np.float32(C).copy()
    ts=np.linspace(0.04,0.96,60)
    def sc(C):
        H=cv2.getPerspectiveTransform(np.float32([[0,0],[n,0],[n,n],[0,n]]),C)
        pts=[]
        for a,b in (((0,0),(n,0)),((n,0),(n,n)),((n,n),(0,n)),((0,n),(0,0))):
            pts+= [[a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t] for t in ts]
        p=cv2.perspectiveTransform(np.float32(pts)[None],H)[0]
        ok=(p[:,0]>=0)&(p[:,0]<w-1)&(p[:,1]>=0)&(p[:,1]<h-1)
        if ok.sum()<20: return -1
        return f[p[ok,1].astype(int),p[ok,0].astype(int)].mean()
    cur=sc(C)
    for st in (8,4,2,1,.5):
        imp=True
        while imp:
            imp=False
            for k in range(4):
                for d in range(2):
                    for sg in(-1,1):
                        D=C.copy();D[k,d]+=sg*st;v=sc(D)
                        if v>cur+1e-5:cur,C,imp=v,D,True
    return C
def diffcheck(frame,photoCorners,variant,fileA,fileB,n=16,inv=False):
    img=cv2.imread(frame) if isinstance(frame,str) else frame;F=Fitter(img,n,inv)
    idx={x[0][0]:i for i,x in enumerate(F.lib)}
    ia,ib=idx[fileA],idx[fileB];f=F.feats(np.float32(photoCorners))
    ta,tb=F.T[ia,variant],F.T[ib,variant];d=np.where(ta!=tb)[0];ok=~np.isnan(f)
    wall=f[ok&ta&tb].mean();gap=f[ok&~ta&~tb].mean()
    return dict(n=len(d),wall=round(float(wall),3),gap=round(float(gap),3),edges=[(int(e),round(float(f[e]),3),bool(ta[e]),bool(tb[e])) for e in d])
