import numpy as np, subprocess, sys
from PIL import Image
W=sys.argv[1]; R=sys.argv[2]
names=[l.split() for l in open(W+'/mapnames.txt')]
w,h=48,85
def frames(f):
    out=subprocess.run(['ffmpeg','-v','error','-i',f'{R}/{f}','-vf',f'fps=4,scale={w}:{h}','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True).stdout
    return np.frombuffer(out,np.uint8).reshape(-1,h,w).astype(float)
F={m:frames(f) for m,f in names}
def crop(a): return a[15:,:]  # drop top band (timestamp label)
for v in range(1,21):
    row=[]
    for k in (0,2,4):
        b=np.asarray(Image.open(f'{R}/v{v:02d}_{k}.jpg').convert('L').resize((w,h)),float)
        best=(1e9,None,None)
        for m,arr in F.items():
            d=np.abs(arr[:,15:,:]-b[15:,:]).mean(axis=(1,2))
            i=int(d.argmin())
            if d[i]<best[0]: best=(d[i],m,i/4)
        row.append(best)
    print(f'v{v:02d}', ' | '.join(f'{m} t={t:.2f} d={d:.1f}' for d,m,t in row))
