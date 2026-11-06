import os,hashlib,re,csv,json,sys
V='/home/santi/Code/MicroMouse/Micras/worktrees/maze-studio-photo/vendor/mazefiles/'
R=os.path.expanduser('~/.cache/maze-dataset/')
def groups():
    g={}
    for d in ('classic','halfsize'):
        for f in sorted(os.listdir(V+d)):
            if f.endswith('.txt'): g.setdefault(hashlib.md5(open(V+d+'/'+f,'rb').read()).hexdigest(),[]).append(f'{d}/{f}')
    return list(g.values())
def info(files):
    best=None
    for f in files:
        cat,n=f.split('/'); n=n[:-4]; l=n.lower()
        y=re.search(r'(?<!\d)(19[89]\d|20[0-2]\d)(?!\d)',n)
        y=int(y.group(1)) if y else None
        if y is None:
            m=re.search(r'(?:uk|japan|taiwan|apec|us|minos|c|sg|kor|hk|jc|ies|iee)(\d\d)(?!\d)',l)
            if m: y=int(m.group(1)); y+=2000 if y<30 else 1900
        comp='other'
        for k,v in [('alljapan','All Japan'),('japan','All Japan'),('apec','APEC'),('uknov','UK Nov/Autumn'),('uk','UK'),('taiwan','Taiwan'),('minos','Minos'),('portugal','Portugal'),('br20','Brazil'),('chubu','Chubu Japan'),('tyubu','Chubu Japan'),('eastjapan','East Japan'),('higashi','East Japan'),('kansai','Kansai Japan'),('kyushu','Kyushu Japan'),('hokuriku','Hokuriku Japan'),('hokkaido','Hokkaido Japan'),('northeast','Northeast Japan'),('student','All Japan student'),('aamc','All America (AAMC)'),('allamerica','All America (AAMC)'),('us','US'),('camm','CAMM'),('oshw','OSHW'),('sd','sd'),('kor','Korea'),('hk','Hong Kong'),('sg','Singapore'),('ph-','Philippines'),('ies','IEEE/IES'),('iee','IEE UK'),('euro','Euromouse'),('c00','C00'),('map','map')]:
            if l.startswith(k): comp=v; break
        sub=''
        if cat=='halfsize': sub='halfsize'
        elif re.search(r'frsh|novice|student',l): sub='fresh/novice/student'
        elif re.search(r'(exp|ef|eq|expert|final|f$|q$)',l): sub='expert/classic'
        else: sub='classic'
        c=(0 if y else 1, -(y or 0))
        if best is None or c<best[0]: best=(c,comp,y,sub)
    return best[1],best[2],best[3]
def priority(comp,y):
    if y is None or y<2015: return 3 if (y and y>=2009) else 4
    big=comp in('All Japan','APEC','UK','UK Nov/Autumn','Taiwan','Minos','Portugal','Brazil','Chubu Japan','East Japan','Kansai Japan')
    return 1 if big else 2
def build():
    D=json.load(open(R+'dataset.json')) if os.path.exists(R+'dataset.json') else []
    S=json.load(open(R+'searched.json')) if os.path.exists(R+'searched.json') else {}
    found={}
    for e in D:
        for f in e['mazeFiles']: found.setdefault(f,[]).append(e)
    rows=[]
    for fl in groups():
        comp,y,sub=info(fl); k=fl[0]
        fr=[e for f in fl for e in found.get(f,[])]
        seen={e['id'] for e in fr}; fr=[e for e in D if e['id'] in seen]
        srch=next((S[f] for f in fl if f in S),'')
        rows.append(dict(maze_id=os.path.basename(k)[:-4],files=' | '.join(fl),competition=comp,year=y or '',category=sub,priority=priority(comp,y),
            sources_searched=srch,frames=len(fr),best_match=(sorted({e['match'] for e in fr})[0] if fr else ''),licences=','.join(sorted({e['licence'] for e in fr})),frame_ids=' '.join(e['id'] for e in fr)))
    rows.sort(key=lambda r:(r['priority'],-(r['year'] or 0) if r['year'] else 0,r['maze_id']))
    w=csv.DictWriter(open(R+'coverage.csv','w',newline=''),fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return rows
if __name__=='__main__':
    r=build(); print(len(r),'mazes')
