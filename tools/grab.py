import sys,subprocess,os,cv2,glob,shutil
vid=sys.argv[1]
R=os.path.expanduser('~/.cache/maze-dataset/work/cand');os.makedirs(R,exist_ok=True)
for t in map(int,sys.argv[2:]):
    out=f'{R}/{vid}_{t}.jpg'
    if os.path.exists(out): continue
    d=f'{R}/tmp_{vid}_{t}';os.makedirs(d,exist_ok=True)
    subprocess.run(['yt-dlp','-q','--no-progress','--js-runtimes','node','--download-sections',f'*{max(0,t-2)}-{t+3}','-f','bv*[height<=1080]','-o',f'{d}/c.%(ext)s',f'https://www.youtube.com/watch?v={vid}'],stderr=subprocess.DEVNULL)
    clips=glob.glob(d+'/c.*')
    if not clips: print('fail',vid,t);shutil.rmtree(d);continue
    subprocess.run(['ffmpeg','-v','error','-y','-i',clips[0],'-vf','fps=2','-q:v','2',d+'/f_%02d.jpg'])
    best=None
    for f in sorted(glob.glob(d+'/f_*.jpg')):
        im=cv2.imread(f,0);s=cv2.Laplacian(im,cv2.CV_64F).var()
        if best is None or s>best[0]: best=(s,f)
    if best: shutil.copy(best[1],out);print(out,round(best[0]),cv2.imread(out).shape)
    shutil.rmtree(d)
