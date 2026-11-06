import cv2,numpy as np,sys,json,os
# usage: corners_view.py id out.jpg [half=px] [overlay path]  -> 4 corner crops of the overlay, zoomed, with a 10px grid
R=os.path.expanduser('~/.cache/maze-dataset/')
i=sys.argv[1];out=sys.argv[2];half=int(sys.argv[3]) if len(sys.argv)>3 else 60
src=sys.argv[4] if len(sys.argv)>4 else R+f'overlays/{i}.jpg'
e=next(x for x in json.load(open(R+'dataset.json')) if x['id']==i)
img=cv2.imread(src);h,w=img.shape[:2];z=max(2,int(240/half))
tiles=[]
for k,(x,y) in enumerate(e['corners']):
    x,y=int(x),int(y);pad=cv2.copyMakeBorder(img,half,half,half,half,cv2.BORDER_CONSTANT,value=(40,0,40))
    c=pad[y:y+2*half,x:x+2*half].copy();c=cv2.resize(c,None,fx=z,fy=z,interpolation=cv2.INTER_NEAREST)
    for g in range(0,2*half,10):
        col=(0,0,255) if g==half else (90,90,90)
        cv2.line(c,(g*z,0),(g*z,c.shape[0]),col,1);cv2.line(c,(0,g*z),(c.shape[1],g*z),col,1)
    cv2.putText(c,f'{k} ({x},{y}) grid10px',(4,18),0,0.55,(0,255,255),2);tiles.append(c)
cv2.imwrite(out,np.vstack([np.hstack(tiles[:2]),np.hstack(tiles[2:])]))
