# Per-video measurement: cuts, camera motion (similarity transform via LK flow), light/colour, audio.
import cv2, numpy as np, json, subprocess, sys, re, os
src, tag, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
step = 2 if fps > 45 else 1           # analyse at ~30 fps
afps = fps/step
W_, H_ = 270, 480
prev = None; prevhist = None; pts = None
rows = []
idx = -1
while True:
    ok, fr = cap.read()
    if not ok: break
    idx += 1
    if idx % step: continue
    t = idx/fps
    sm = cv2.resize(fr, (W_, H_), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0,1,2], None, [8,4,4], [0,180,0,256,0,256]); hist = cv2.normalize(hist, None).flatten()
    r = {'t': round(t,3), 'Y': float(g.mean()/255), 'S': float(hsv[...,1].mean()/255), 'C': float(g.std()/255)}
    # vignette: corner patches vs centre
    c = g[H_//3:2*H_//3, W_//3:2*W_//3].mean()
    k = 40; corners = np.mean([g[:k,:k].mean(), g[:k,-k:].mean(), g[-k:,:k].mean(), g[-k:,-k:].mean()])
    r['vig'] = float(corners/max(c,1))
    if prev is not None:
        r['hd'] = float(cv2.compareHist(prevhist, hist, cv2.HISTCMP_BHATTACHARYYA))
        r['md'] = float(np.abs(g.astype(int)-prev.astype(int)).mean()/255)
        s=1; ang=0; tx=0; ty=0; inl=0
        if pts is not None and len(pts) > 12:
            nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, g, pts, None, winSize=(21,21), maxLevel=3)
            good0 = pts[st==1]; good1 = nxt[st==1]
            if len(good0) > 10:
                M, inliers = cv2.estimateAffinePartial2D(good0, good1, method=cv2.RANSAC, ransacReprojThreshold=2.0)
                if M is not None:
                    s = float(np.hypot(M[0,0], M[1,0])); ang = float(np.degrees(np.arctan2(M[1,0], M[0,0])))
                    # translation of image centre
                    cx, cy = W_/2, H_/2
                    nx = M[0,0]*cx + M[0,1]*cy + M[0,2]; ny = M[1,0]*cx + M[1,1]*cy + M[1,2]
                    tx = float((nx-cx)/W_); ty = float((ny-cy)/H_); inl = float(inliers.mean())
                # local (non-camera) motion: residual flow magnitude of outliers
                if M is not None:
                    pred = (good0 @ M[:, :2].T) + M[:, 2]
                    res = np.linalg.norm(good1 - pred, axis=1)
                    r['local'] = float(np.mean(res > 2.0))
        r.update({'zoom': s, 'rot': ang, 'tx': tx, 'ty': ty, 'inl': inl})
    pts = cv2.goodFeaturesToTrack(g, 300, 0.01, 7)
    prev = g; prevhist = hist
    rows.append(r)
cap.release()
# Lab colour stats at 2 fps (shadow / highlight tint)
cap = cv2.VideoCapture(src); labs = []; idx = -1
every = int(round(fps/2))
while True:
    ok, fr = cap.read()
    if not ok: break
    idx += 1
    if idx % every: continue
    sm = cv2.resize(fr, (W_, H_), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(sm, cv2.COLOR_BGR2LAB).reshape(-1,3).astype(float)
    L = lab[:,0]*100/255; a = lab[:,1]-128; b = lab[:,2]-128
    sh = L < np.percentile(L, 20); hi = L > np.percentile(L, 85)
    labs.append([float(a[sh].mean()), float(b[sh].mean()), float(a[hi].mean()), float(b[hi].mean())])
cap.release()
labs = np.array(labs)
# audio: EBU R128 + silences
ebu = subprocess.run(['ffmpeg','-nostats','-i',src,'-filter_complex','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
def grab(p):
    m = re.findall(p, ebu); return float(m[-1]) if m else None
audio = {'I': grab(r'I:\s+(-?[\d.]+) LUFS'), 'LRA': grab(r'LRA:\s+(-?[\d.]+) LU'), 'TP': grab(r'Peak:\s+(-?[\d.]+) dBFS')}
sil = subprocess.run(['ffmpeg','-nostats','-i',src,'-af','silencedetect=n=-35dB:d=0.25','-f','null','-'],capture_output=True,text=True).stderr
audio['silences'] = [(float(a), float(b)) for a,b in re.findall(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)', sil)]
# onsets (sound events): astats-free approach using ffmpeg 'aubio'-less energy flux on 20ms frames
raw = subprocess.run(['ffmpeg','-v','error','-i',src,'-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
x = np.frombuffer(raw, np.int16).astype(float)/32768
hop = 320; nfr = len(x)//hop
fr = x[:nfr*hop].reshape(nfr, hop)
spec = np.abs(np.fft.rfft(fr*np.hanning(hop), axis=1))
flux = np.maximum(0, np.diff(np.log1p(spec*10), axis=0)).sum(axis=1)
thr = np.median(flux) + 2.5*np.std(flux)
on = [i for i in range(1,len(flux)-1) if flux[i]>thr and flux[i]>=flux[i-1] and flux[i]>=flux[i+1]]
# de-bounce 120 ms
ons=[]; last=-1
for i in on:
    if (i-last)*hop/16000 > 0.12: ons.append(round((i+1)*hop/16000,3)); last=i
E = np.abs(np.fft.rfft(x)); fq = np.fft.rfftfreq(len(x), 1/16000); P = E**2
audio['bass_share'] = float(P[fq<250].sum()/P.sum()); audio['voice_share'] = float(P[(fq>=300)&(fq<3400)].sum()/P.sum())
audio['onsets'] = ons
json.dump({'tag':tag,'src':os.path.basename(src),'fps':fps,'frames':n,'afps':afps,'rows':rows,'lab':labs.tolist(),'audio':audio}, open(f'{outdir}/{tag}.json','w'))
print(tag, 'done', len(rows))
