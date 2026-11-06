import cv2,numpy as np,sys
def quad(img,vmax=95):
    h,w=img.shape[:2];s=640/w;sm=cv2.resize(img,None,fx=s,fy=s)
    g=cv2.cvtColor(sm,cv2.COLOR_BGR2GRAY);m=((g<vmax)).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8));m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not cs: return None
    c=max(cs,key=cv2.contourArea);hull=cv2.convexHull(c)
    for eps in np.linspace(0.01,0.08,15):
        ap=cv2.approxPolyDP(hull,eps*cv2.arcLength(hull,True),True)
        if len(ap)==4: break
    if len(ap)!=4: ap=cv2.boxPoints(cv2.minAreaRect(hull))
    p=np.float32(ap).reshape(4,2)/s
    c=p.mean(0);a=np.arctan2(p[:,1]-c[1],p[:,0]-c[0]);p=p[np.argsort(a)]
    return p,cv2.contourArea(c if False else hull)*1.0/(sm.shape[0]*sm.shape[1])
if __name__=='__main__':
    im=cv2.imread(sys.argv[1]);p,a=quad(im);print(' '.join(f'{x:.0f},{y:.0f}' for x,y in p),round(a,2))
