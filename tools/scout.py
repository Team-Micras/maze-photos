import sys,subprocess,os
from concurrent.futures import ThreadPoolExecutor
vid,a,b,step=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]); ln=int(sys.argv[5]) if len(sys.argv)>5 else 3
R=os.path.expanduser('~/.cache/maze-dataset/work/scout/'+vid); os.makedirs(R,exist_ok=True)
def go(s):
    jpg=f'{R}/{s}.jpg'
    if os.path.exists(jpg): return
    mp4=f'{R}/{s}.mp4'
    subprocess.run(['yt-dlp','-q','--no-progress','--js-runtimes','node','--download-sections',f'*{s}-{s+ln}','-f','134/18/bv*[height<=360]','-o',mp4,f'https://www.youtube.com/watch?v={vid}'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if os.path.exists(mp4):
        subprocess.run(['ffmpeg','-v','error','-y','-ss','1','-i',mp4,'-frames:v','1','-vf','scale=320:180','-update','1',jpg]); os.remove(mp4)
with ThreadPoolExecutor(6) as ex: list(ex.map(go,range(a,b+1,step)))
fs=sorted(int(f[:-4]) for f in os.listdir(R) if f.endswith('.jpg'))
for k in range(0,len(fs),36):
    ch=fs[k:k+36]
    subprocess.run(['montage','-label','%t']+[f'{R}/{s}.jpg' for s in ch]+['-tile','6x','-geometry','256x144+1+1','-pointsize','14','-fill','yellow',f'{os.path.dirname(R)}/mont_{vid}_{k//36}.jpg'])
print(vid,len(fs))
