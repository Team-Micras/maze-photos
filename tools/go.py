import sys,os,subprocess;sys.path.insert(0,os.path.dirname(__file__))
import ingest,warnings;warnings.filterwarnings('ignore')
C=os.path.expanduser('~/.cache/maze-dataset/work/cand/')
def go(vid,times,corners,n,expect,comp,year,cat,view='oblique',notes='',inv=False,jit=None):
    subprocess.run(['python3',os.path.dirname(__file__)+'/grab.py',vid]+[str(t) for t in times],stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
    for t in times:
        f=f'{C}{vid}_{t}.jpg'
        if not os.path.exists(f): print('missing',vid,t);continue
        ingest.add(f,corners,n,expect,comp,year,cat,vid,t,view,notes=notes,inv=inv,jit=jit)
