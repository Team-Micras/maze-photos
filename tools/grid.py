import cv2,sys
im=cv2.imread(sys.argv[1]);h,w=im.shape[:2];s=1000/w if w>1000 else 1.0
o=cv2.resize(im,None,fx=s,fy=s) if s!=1 else im.copy();st=100 if w>1000 else 50
for x in range(0,w,st):
    X=int(x*s);cv2.line(o,(X,0),(X,o.shape[0]),(0,255,255) if x%500==0 else (0,160,160),1);cv2.putText(o,str(x),(X+2,12),0,0.4,(0,255,255),1)
for y in range(0,h,st):
    Y=int(y*s);cv2.line(o,(0,Y),(o.shape[1],Y),(0,255,255) if y%500==0 else (0,160,160),1);cv2.putText(o,str(y),(2,Y-2),0,0.4,(0,255,255),1)
cv2.imwrite(sys.argv[2],o,[cv2.IMWRITE_JPEG_QUALITY,80])
