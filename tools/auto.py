import sys,os,json,cv2,numpy as np
sys.path.insert(0,os.path.dirname(__file__))
import fit
# usage: auto.py VID refframe.jpg "rough corners" mazeSubstr [n] -> scores scout thumbs with the fitted camera
vid,ref,cs,expect=sys.argv[1:5];n=int(sys.argv[5]) if len(sys.argv)>5 else 16
C=[[float(v) for v in c.split(',')] for c in cs.split()]
r=fit.fit(ref,C,n,False,None,None,[expect]);print(r['mazeFiles'][0],r['score'],r['nextBest'])
H,W=cv2.imread(ref).shape[:2];P=np.float32(r['photoCorners']);vi=r['variant']
lib=fit.library(n);mi=[i for i,x in enumerate(lib) if r['mazeFiles'][0] in x[0]][0]
D=os.path.expanduser('~/.cache/maze-dataset/work/scout/'+vid);out=[]
for f in sorted(os.listdir(D),key=lambda x:int(x.split('.')[0]) if x[0].isdigit() else 0):
    if not f.endswith('.jpg'): continue
    im=cv2.imread(D+'/'+f);s=im.shape[1]/W;F=fit.Fitter(im,n) if 'F' not in dir() else F
    F.img=im;F.f=fit.features(im)
    out.append((int(f[:-4]),F.one(P*s,mi,vi)))
for t,sc in out: print(t,round(sc,3))
