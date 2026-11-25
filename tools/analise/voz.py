import sys, json, subprocess, numpy as np, librosa, scipy.signal as ss
src, tag, outdir = sys.argv[1:4]
sr=16000
raw=subprocess.run(['ffmpeg','-nostdin','-v','error','-i',src,'-ac','1','-ar',str(sr),'-f','s16le','-'],capture_output=True).stdout
y=np.frombuffer(raw,np.int16).astype(np.float32)/32768
hop=160
f0,vflag,vprob=librosa.pyin(y,fmin=65,fmax=450,sr=sr,frame_length=1024,hop_length=hop)
f0v=f0[vflag & ~np.isnan(f0)]
st=12*np.log2(f0v/np.median(f0v))
# phrases: voiced runs, gaps >=0.15s split
v=vflag.astype(int); t=np.arange(len(v))*hop/sr
runs=[];i=0
while i<len(v):
    if v[i]:
        j=i
        while j<len(v) and (v[j] or (j+15<len(v) and v[j:j+15].any())): j+=1
        if j-i>=30: runs.append((i,j))
        i=j
    else: i+=1
ends=[]
for a,b in runs:
    seg=f0[a:b]; ok=~np.isnan(seg)
    if ok.sum()<20: continue
    s=seg[ok]; tail=s[-max(8,len(s)//5):]; head=s[:len(s)-len(tail)]
    if len(head)<5: continue
    ends.append(12*np.log2(np.median(tail)/np.median(head)))
ends=np.array(ends)
# syllable nuclei: band energy envelope peaks during voiced
b,a=ss.butter(4,[300/(sr/2),3000/(sr/2)],'band'); yb=ss.filtfilt(b,a,y)
env=np.sqrt(ss.convolve(yb**2,np.ones(400)/400,'same'))[::hop]
env_db=20*np.log10(env+1e-6)
pk,_=ss.find_peaks(env_db,prominence=2.0,distance=int(0.09*sr/hop))
pk=[p for p in pk if p<len(vflag) and vflag[p]]
dur=len(y)/sr; voiced_time=vflag.mean()*dur
cent=librosa.feature.spectral_centroid(y=y,sr=sr,n_fft=1024,hop_length=hop)[0][:len(vflag)]
rms=librosa.feature.rms(y=y,frame_length=1024,hop_length=hop)[0][:len(vflag)]
rv=20*np.log10(rms[vflag[:len(rms)]]+1e-6)
res={'tag':tag,'dur':dur,'f0_med':float(np.median(f0v)),'f0_p10':float(np.percentile(f0v,10)),'f0_p90':float(np.percentile(f0v,90)),
 'range_st_p5_p95':float(np.percentile(st,95)-np.percentile(st,5)),'f0_sd_st':float(np.std(st)),
 'voiced_frac':float(vflag.mean()),'syll_per_s_total':len(pk)/dur,'syll_per_s_voiced':len(pk)/max(voiced_time,1e-6),
 'phrases':len(ends),'phrase_len_med_s':float(np.median([(b-a)*hop/sr for a,b in runs])),
 'end_fall_pct':float((ends<-1).mean()*100),'end_rise_pct':float((ends>1).mean()*100),'end_med_st':float(np.median(ends)),
 'centroid_voiced_hz':float(np.median(cent[vflag[:len(cent)]])),'rms_sd_db':float(np.std(rv))}
json.dump(res,open(f'{outdir}/{tag}_voice.json','w'))
print(tag,'voice done')
