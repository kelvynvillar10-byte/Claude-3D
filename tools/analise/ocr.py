import subprocess, numpy as np, json, sys
from rapidocr_onnxruntime import RapidOCR
src, tag, outdir = sys.argv[1:4]
import os
lock=f'{outdir}/{tag}_ocr.lock'
if os.path.exists(f'{outdir}/{tag}_ocr.json') or os.path.exists(lock): sys.exit(0)
open(lock,'w').close()
w,h=360,640; fps=2
raw=subprocess.run(['ffmpeg','-nostdin','-v','error','-i',src,'-vf',f'fps={fps},scale={w}:{h}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
fr=np.frombuffer(raw,np.uint8).reshape(-1,h,w,3)
o=RapidOCR(); res=[]
for i,f in enumerate(fr):
    r,_=o(f)
    dets=[]
    for box,txt,conf in (r or []):
        b=np.array(box); x0,y0=b.min(0); x1,y1=b.max(0)
        crop=f[int(y0):int(y1),int(x0):int(x1)].astype(int)
        R,G,B=crop[...,0],crop[...,1],crop[...,2]
        white=((R>215)&(G>215)&(B>215)).sum(); yel=((R>200)&(G>150)&(B<110)).sum()
        dets.append({'txt':txt,'conf':float(conf),'yc':float((y0+y1)/2/h),'hh':float((y1-y0)/h),'ww':float((x1-x0)/w),'white':int(white),'yel':int(yel)})
    res.append({'t':i/fps,'d':dets})
json.dump(res,open(f'{outdir}/{tag}_ocr.json','w'),ensure_ascii=False)
print(tag,'ocr done',len(res))
