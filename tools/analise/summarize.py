import json, numpy as np, sys, os, glob
W=sys.argv[1]
mp={l.split()[0]:l.split()[-1] for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'mapa_mp4_referencias.txt'))}
def shots_from(rows):
    t=np.array([r['t'] for r in rows]); hd=np.array([r.get('hd',0) for r in rows]); md=np.array([r.get('md',0) for r in rows])
    inl=np.array([r.get('inl',1) for r in rows])
    cuts=[]
    for i in range(1,len(rows)):
        lo=max(1,i-8); hi=min(len(rows),i+9)
        loc=np.median(hd[lo:hi])
        if hd[i]>0.28 and hd[i]>3*max(loc,0.02) and md[i]>0.04:
            if not cuts or t[i]-cuts[-1]>0.25: cuts.append(t[i])
    return t,cuts
out={}
for f in sorted(glob.glob(W+'/out/m??.json')):
    d=json.load(open(f)); rows=d['rows']; tag=d['tag']; v=mp[tag]
    t,cuts=shots_from(rows); dur=d['frames']/d['fps']
    bounds=[0]+cuts+[dur]; sl=np.diff(bounds)
    z=np.array([r.get('zoom',1) for r in rows]); tx=np.array([r.get('tx',0) for r in rows]); ty=np.array([r.get('ty',0) for r in rows]); ro=np.array([r.get('rot',0) for r in rows])
    Y=np.array([r['Y'] for r in rows]); S=np.array([r['S'] for r in rows]); C=np.array([r['C'] for r in rows]); vig=np.array([r['vig'] for r in rows])
    loc=np.array([r.get('local',0) for r in rows]); md=np.array([r.get('md',0) for r in rows])
    cutidx=set(np.searchsorted(t,cuts))
    # per-shot camera
    sh=[]
    for a,b in zip(bounds[:-1],bounds[1:]):
        m=(t>a+0.05)&(t<b-0.02)
        if m.sum()<3: continue
        zz=z[m]; zz=np.where(np.abs(zz-1)>0.25,1,zz)
        tot_z=np.prod(zz)-1; pan=tx[m][np.abs(tx[m])<0.3].sum(); tilt=ty[m][np.abs(ty[m])<0.3].sum(); roll=ro[m][np.abs(ro[m])<20].sum()
        peak_rate=np.max(np.abs(zz-1))*d['afps']
        moved=abs(tot_z)>0.02 or abs(pan)>0.03 or abs(tilt)>0.03 or abs(roll)>1.5
        sh.append({'dur':b-a,'zoom':tot_z,'zrate':tot_z/(b-a),'pan':pan,'tilt':tilt,'roll':roll,'moved':moved,'crash':tot_z>0.4 or peak_rate>1.5,'local':float(np.mean(loc[m]))})
    def frac(k): return float(np.mean([s[k] for s in sh]))
    push=[s for s in sh if s['zoom']>0.02]; pull=[s for s in sh if s['zoom']<-0.02]
    # whips: very fast lateral motion frames
    sp=np.hypot(tx,ty)
    near=np.zeros(len(t),bool)
    for c in cutidx:
        near[max(0,c-1):c+2]=True
    m=(sp>0.06)&(sp<0.5)&~near
    whips=[]; i=0
    while i<len(m):
        if m[i]:
            j=i
            while j<len(m) and m[j]: j+=1
            if 2<=j-i<=8: whips.append(t[i])
            i=j
        else: i+=1
    # shake: jitter = sign alternation of ty/tx with amplitude
    jit=np.abs(np.diff(np.sign(ty)))*(np.abs(ty[1:])>0.004)
    shakes=[]; win=int(d['afps']*0.3)
    for i in range(0,len(jit)-win):
        if jit[i:i+win].sum()>=6 and (i+1) not in cutidx:
            if not shakes or t[i]-shakes[-1]>0.6: shakes.append(t[i])
    # flash: brightness spike
    flashes=[t[i] for i in range(2,len(Y)-2) if Y[i]-min(Y[i-2],Y[i+2])>0.18 and Y[i]>0.7]
    fl=[];[fl.append(x) for x in flashes if not fl or x-fl[-1]>0.5]
    # held frames (static image >=0.25 s)
    held=0; run=0
    for x in md:
        if x<0.0015: run+=1
        else:
            if run>=int(0.25*d['afps']): held+=1
            run=0
    lab=np.array(d['lab']); lab=lab[~np.isnan(lab).any(1)]
    au=d['audio']; ons=np.array(au['onsets'])
    cut_on=np.mean([np.min(np.abs(ons-c))<0.10 for c in cuts]) if len(ons) and cuts else None
    # cut rate by decile
    dec=np.histogram(np.array(cuts)/dur,bins=10,range=(0,1))[0]/(dur/10)
    sil=au['silences']; longp=sum(1 for e,dd in sil if dd>=0.8 and e<dur-1)
    out[v]={'tag':tag,'src':d['src'],'dur':round(dur,1),'fps':d['fps'],'shots':len(sl),'cpm':round(len(cuts)/dur*60,1),'shot_med':round(float(np.median(sl)),2),
        'shot_p10':round(float(np.percentile(sl,10)),2),'shot_p90':round(float(np.percentile(sl,90)),2),'first_cut':round(cuts[0],2) if cuts else None,
        'Y':round(float(np.median(Y)),3),'S':round(float(np.median(S)),3),'C':round(float(np.median(C)),3),'vig':round(float(np.median(vig)),3),
        'sh_a':round(float(np.median(lab[:,0])),1),'sh_b':round(float(np.median(lab[:,1])),1),'hi_a':round(float(np.median(lab[:,2])),1),'hi_b':round(float(np.median(lab[:,3])),1),
        'pct_moved':round(frac('moved')*100),'pct_push':round(len(push)/len(sh)*100),'pct_pull':round(len(pull)/len(sh)*100),'pct_crash':round(frac('crash')*100),
        'push_rate_med':round(float(np.median([s['zrate'] for s in push]))*100,1) if push else None,'push_tot_med':round(float(np.median([s['zoom'] for s in push]))*100,1) if push else None,
        'pct_pan':round(np.mean([abs(s['pan'])>0.06 for s in sh])*100),'pct_tilt':round(np.mean([abs(s['tilt'])>0.06 for s in sh])*100),'pct_roll':round(np.mean([abs(s['roll'])>3 for s in sh])*100),
        'whip_pm':round(len(whips)/dur*60,1),'shake_pm':round(len(shakes)/dur*60,1),'flash_pm':round(len(fl)/dur*60,1),'held_pm':round(held/dur*60,1),
        'local_motion':round(float(np.median([s['local'] for s in sh])),3),
        'LUFS':au['I'],'LRA':au['LRA'],'TP':au['TP'],'bass':round(au['bass_share']*100,1),'voice':round(au['voice_share']*100,1),'onsets_ps':round(len(ons)/dur,2),
        'cuts_on_sound':round(cut_on*100) if cut_on is not None else None,'long_pauses':longp,'cut_deciles':[round(x,2) for x in dec]}
json.dump(out,open(W+'/summary.json','w'),indent=1,ensure_ascii=False)
for v in sorted(out):
    o=out[v]; print(v,{k:o[k] for k in ['dur','shots','cpm','shot_med','first_cut','Y','S','vig','sh_a','sh_b','hi_b','pct_moved','pct_push','push_rate_med','whip_pm','shake_pm','flash_pm','LUFS','onsets_ps','cuts_on_sound','long_pauses']})
