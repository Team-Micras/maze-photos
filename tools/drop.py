import json,os,sys
R=os.path.expanduser('~/.cache/maze-dataset/');D=json.load(open(R+'dataset.json'));k=[]
for e in D:
    if e['id'] in sys.argv[1:]:
        for d in('frames','overlays'):
            try: os.remove(f"{R}{d}/{e['id']}.jpg")
            except: pass
    else: k.append(e)
json.dump(k,open(R+'dataset.json','w'),indent=1,ensure_ascii=False);print(len(k))
