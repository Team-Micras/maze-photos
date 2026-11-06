import json,os
R=os.path.expanduser('~/.cache/maze-dataset/')
# Corners read by eye on zoomed crops (top of the corner posts, TL,TR,BR,BL photo order); a corner below the frame is extrapolated from the post spacing along its two borders.
FIX={
 'all-japan-2019-classic-unknown-1':[[278,22.5],[955,53],[1073,607],[166,580]],
 'all-japan-2019-classic-unknown-2':[[278.5,26.5],[954,55],[1072,610],[164,582]],
 'uk-2025-classic-unknown-1':[[517,116],[1437,165],[1400,1118],[446,1056]],
 'uk-2025-classic-unknown-2':[[519,120],[1441,167],[1400,1120],[445,1055]],
 'uk-2025-classic-unknown-3':[[520,120],[1445,169],[1401,1120],[446,1055]],
 'apec-2017-classic-unknown-1':[[581,119],[1376,70],[1571,981],[432,980]],
 'apec-2017-classic-unknown-2':[[579,118],[1375,67],[1567,980],[434,980]],
}
D=json.load(open(R+'dataset.json'))
for e in D:
    if e['id'] in FIX:
        e.setdefault('cornersPrev',e['corners']);e['corners']=FIX[e['id']];e['cornersFixed']=True
        e['cornersOrder']='TL,TR,BR,BL (photo order, by eye on zoomed crops)'
json.dump(D,open(R+'dataset.json','w'),indent=1,ensure_ascii=False)
