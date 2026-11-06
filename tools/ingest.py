import json,sys,os,cv2,numpy as np,shutil,subprocess
sys.path.insert(0,os.path.dirname(__file__))
import fit
R=os.path.expanduser('~/.cache/maze-dataset/')
def load(): return json.load(open(R+'dataset.json')) if os.path.exists(R+'dataset.json') else []
def save(D): json.dump(D,open(R+'dataset.json','w'),indent=1,ensure_ascii=False)
def vmeta(vid):
    P=R+'work/videos.json';M=json.load(open(P)) if os.path.exists(P) else {}
    if vid not in M:
        o=subprocess.run(['yt-dlp','--skip-download','--no-warnings','--print','%(license)s|%(channel)s|%(channel_url)s|%(upload_date)s|%(title)s','--',vid],capture_output=True,text=True).stdout.strip().split('\n')[-1].split('|',4)
        M[vid]=dict(license=o[0],channel=o[1],channelUrl=o[2],uploadDate=o[3],title=o[4]);json.dump(M,open(P,'w'),indent=1,ensure_ascii=False)
    return M[vid]
def lic(m): return 'CC-BY' if 'Creative Commons' in (m.get('license') or '') else 'reference-only'
def nextid(D,base):
    k=1
    ids={e['id'] for e in D}
    while f'{base}-{k}' in ids: k+=1
    return f'{base}-{k}'
def add(frame,corners,n,expect,comp,year,cat,video=None,t=None,view='oblique',licence=None,source=None,notes='',inv=False,base=None,maze=None,jit=None):
    D=load();r=fit.fit(frame,corners,n,inv,None,None,expect,(8 if n==32 else 0) if jit is None else jit)
    sc,nb=r['score'],r['nextBest'];files=r['mazeFiles']
    allf=files+[f for nr in r['near'] for f in nr['files']]
    inexp=bool(expect) and any(e in f for f in allf for e in expect)
    if expect and not any(e in f for f in files for e in expect):
        for nr in r['near']:
            if nr['wallsDiffering']<=2 and any(e in f for f in nr['files'] for e in expect):
                r['near'].append(dict(files=files,wallsDiffering=nr['wallsDiffering']));r['near'].remove(nr);files=nr['files'];break
    if sc>=0.25 and sc-nb>=0.15: match='confirmed'
    elif sc>=0.2 and sc-nb>=0.15 and not inexp: match='likely'
    elif sc>=0.2 and inexp and sc-nb>=0.05: match='likely'
    elif sc>=0.25 and inexp: match='likely'
    elif sc>=0.15 and inexp and sc-nb>=0.08: match='likely'
    elif sc>=0.12 and inexp and sc-nb>=0.07: match='likely'
    else: match='unknown'
    if match!='unknown' and not inexp and expect: notes=(notes+' ' if notes else '')+'Matched a maze file other than the expected one for this contest and year (a reused maze).'
    if source is None:
        m=vmeta(video);source=dict(type='youtube',url=f'https://www.youtube.com/watch?v={video}&t={int(t)}s',timestamp=t,channel=m['channel'],channelUrl=m['channelUrl'],uploadDate=m['uploadDate'],title=m['title'])
        licence=licence or lic(m)
    if match=='unknown':
        mf=[];oc=fit.outline_refine(cv2.imread(frame),corners,n,inv);C=[[round(float(x),1),round(float(y),1)] for x,y in oc];ori=None
        bid=base or f'{comp}-{year}-{cat}'.lower().replace(' ','-')+'-unknown'
    else:
        mf=files;C=r['corners'];ori=r['orientation'];pf=next((f for f in files if expect and any(e in f for e in expect)),files[0]);bid=base or os.path.basename(pf)[:-4].lower()
    id_=nextid(D,bid)
    img=cv2.imread(frame);cv2.imwrite(R+f'frames/{id_}.jpg',img,[cv2.IMWRITE_JPEG_QUALITY,92])
    if match!='unknown':
        fl=fit.library(n);Hh,Vv=next((h,v) for f,h,v in fl if f[0]==files[0])
        fit.overlay(img,Hh,Vv,C,n,R+f'overlays/{id_}.jpg',f'{id_}  {match}  score {sc:.2f} next {nb:.2f}')
    else:
        o=img.copy();cv2.polylines(o,[np.int32(C)],True,(0,255,255),max(2,img.shape[1]//500));cv2.imwrite(R+f'overlays/{id_}.jpg',o,[cv2.IMWRITE_JPEG_QUALITY,85])
    c=np.array(C);ppc=float(np.mean([np.linalg.norm(c[i]-c[(i+1)%4]) for i in range(4)])/n)
    e=dict(id=id_,mazeFiles=mf,competition=comp,year=year,category=cat,source=source,licence=licence,corners=C,cornersOrder='NW,NE,SE,SW (file order)' if match!='unknown' else 'TL,TR,BR,BL (photo order, rough)',orientation=ori,match=match,score=sc,nextBest=nb,nextBestFiles=r['nextBestFiles'] if match!='unknown' else r['nextBestFiles'],bestGuess=files if match=='unknown' else None,nearIdentical=(r['near'] if match!='unknown' else []),view=view,pxPerCell=round(ppc,1),gridSize=n,notes=notes)
    D.append(e);save(D);print(id_,match,sc,nb,files[:1]);return e
