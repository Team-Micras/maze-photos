import cv2,numpy as np,sys
# usage: zoom.py frame.jpg out.jpg half x,y [x,y ...] -> zoomed crops with absolute-coordinate grid (10 px, labels every 50)
img=cv2.imread(sys.argv[1]);out=sys.argv[2];half=int(sys.argv[3]);z=max(2,int(260/half));tiles=[]
for s in sys.argv[4:]:
    x,y=map(int,map(float,s.split(',')));pad=cv2.copyMakeBorder(img,half,half,half,half,cv2.BORDER_CONSTANT,value=(60,0,60))
    c=cv2.resize(pad[y:y+2*half,x:x+2*half],None,fx=z,fy=z,interpolation=cv2.INTER_NEAREST)
    for a in range((x-half)//10*10,x+half+1,10):
        X=(a-x+half)*z
        if 0<=X<c.shape[1]:
            cv2.line(c,(X,0),(X,c.shape[0]),(0,0,255) if a%50==0 else (110,110,110),1)
            if a%50==0: cv2.putText(c,str(a),(X+2,c.shape[0]-6),0,0.45,(0,255,255),1)
    for b in range((y-half)//10*10,y+half+1,10):
        Y=(b-y+half)*z
        if 0<=Y<c.shape[0]:
            cv2.line(c,(0,Y),(c.shape[1],Y),(0,0,255) if b%50==0 else (110,110,110),1)
            if b%50==0: cv2.putText(c,str(b),(2,Y-3),0,0.45,(0,255,255),1)
    tiles.append(c)
while len(tiles)%2: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[i:i+2]) for i in range(0,len(tiles),2)]))
