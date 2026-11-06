import json,os,re,cv2
R=os.path.expanduser('~/.cache/maze-dataset/')
M=json.load(open(os.path.expanduser('~/.cache/maze-photos/manifest.json')))
def key(url):
    if not url: return None
    if url.startswith('file:') or 'sources/' in url: return url.split('sources/')[-1]
    v=re.search(r'(?:v=|youtu\.be/|live/)([\w-]{11})',url);t=re.search(r't=(\d+)',url)
    return (v.group(1),int(t.group(1))) if v and t else None
tuned={key(m['source_url']) for m in M if m['match_confidence'] in('confirmed','likely')}
D=json.load(open(R+'dataset.json'));out=[];skipped=[]
for e in D:
    s=e['source'] or {};k=key(s.get('url') or s.get('file'))
    if e['match']=='confirmed':
        if k in tuned: skipped.append(e['id']);continue
        role='heldout'
    elif e['match']=='unknown': role='unknown'
    else: continue
    if e.get('exclude'): continue
    img=cv2.imread(R+f"frames/{e['id']}.jpg");h,w=img.shape[:2]
    p=R+f"heldout/raw/{e['id']}.rgba"
    if not os.path.exists(p): open(p,'wb').write(cv2.cvtColor(img,cv2.COLOR_BGR2RGBA).tobytes())
    out.append(dict(id=e['id'],role=role,mazeFile=(e['mazeFiles'] or [None])[0],size=e['gridSize'],category=e['category'],corners=e['corners'],
        cornersImage=(e.get('lensFit') or {}).get('cornersImage'),distortion=e['distortion'],k1=e['k1'],pxPerCell=e['pxPerCell'],width=w,height=h))
json.dump(out,open(R+'heldout/index.json','w'),indent=1)
print('tuning duplicates skipped:',skipped);print('heldout',sum(o['role']=='heldout' for o in out),'unknown',sum(o['role']=='unknown' for o in out))
