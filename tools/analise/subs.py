import json, glob, sys, re, os, numpy as np, difflib
W=sys.argv[1]
mp={l.split()[0]:l.split()[-1] for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'mapa_mp4_referencias.txt'))}
res={}
for f in sorted(glob.glob(W+'/out/m??_ocr.json')):
    tag=f.split('/')[-1][:3]; v=mp[tag]; d=json.load(open(f))
    seq=[]
    for fr in d:
        c=[x for x in fr['d'] if x['conf']>=0.75 and x['white']+x['yel']>=300 and 0.025<=x['hh']<=0.065 and re.search('[A-ZÀ-Ú]{2}',x['txt']) and '@' not in x['txt'] and x['txt'].upper()==x['txt']]
        if not c: seq.append(None); continue
        m=max(c,key=lambda x:x['white']+x['yel'])
        g=[x for x in c if abs(x['yc']-m['yc'])<0.025]
        x={'txt':' '.join(y['txt'] for y in g),'yc':m['yc'],'hh':m['hh'],'ww':sum(y['ww'] for y in g),'white':sum(y['white'] for y in g),'yel':sum(y['yel'] for y in g)}
        seq.append(x)
    blocks=[]
    for x in seq:
        if x is None: continue
        if blocks and difflib.SequenceMatcher(None,blocks[-1]['txt'].replace(' ',''),x['txt'].replace(' ','')).ratio()>0.75: continue
        blocks.append(x)
    dur=len(d)/2
    words=[len(re.findall(r"[A-Za-zÀ-ú0-9]+",b['txt'])) for b in blocks]
    yc=np.array([b['yc'] for b in blocks]); yel=np.array([b['yel']/(b['white']+b['yel']+1)>0.2 for b in blocks])
    hist=np.histogram(yc,bins=10,range=(0,1))[0]
    res[v]={'blocks':len(blocks),'blocks_pm':round(len(blocks)/dur*60,1),'words_per_block':round(float(np.mean(words)),2),'wpm_on_screen':round(sum(words)/dur*60),
            'pct_yellow':round(float(yel.mean())*100),'yc_med':round(float(np.median(yc))*100),'pct_top_<35':round(float((yc<0.35).mean())*100),'pct_60_80':round(float(((yc>=0.6)&(yc<0.8)).mean())*100),
            'letter_h_pct':round(float(np.median([b['hh'] for b in blocks]))*100*0.72,1),'block_w_pct':round(float(np.median([b['ww'] for b in blocks]))*100),
            'hist10':hist.tolist(),'first5':[b['txt'] for b in blocks[:5]],'last5':[b['txt'] for b in blocks[-5:]]}
json.dump(res,open(W+'/subs.json','w'),indent=1,ensure_ascii=False)
for v in sorted(res): print(v,res[v])
