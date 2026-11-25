import json,sys,re,glob,numpy as np
W=sys.argv[1]; s=json.load(open(W+'/subs.json'))
import os
mp={l.split()[0]:l.split()[-1] for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'mapa_mp4_referencias.txt'))}
f=lambda x,n=1: ('%.*f'%(n,x)).replace('.',',')
print('### Tabela E — legendas (OCR a 2 qps)\n')
print('| Ref. | Blocos/min | Palavras/bloco | Palavras/min na tela | Blocos com destaque amarelo | Centro vertical (mediana) | No topo (< 35 %) | Entre 60 % e 80 % | Altura da letra | Largura do bloco |')
print('|'+'---|'*10)
V=sorted(s)
for v in V:
    o=s[v]; print(f"| {v} | {f(o['blocks_pm'])} | {f(o['words_per_block'],2)} | {o['wpm_on_screen']} | {o['pct_yellow']} % | {o['yc_med']} % | {o['pct_top_<35']} % | {o['pct_60_80']} % | {f(o['letter_h_pct'])} % | {o['block_w_pct']} % |")
med=lambda k: float(np.median([s[v][k] for v in V]))
print(f"| **Mediana** | {f(med('blocks_pm'))} | {f(med('words_per_block'),2)} | {round(med('wpm_on_screen'))} | {round(med('pct_yellow'))} % | {round(med('yc_med'))} % | {round(med('pct_top_<35'))} % | {round(med('pct_60_80'))} % | {f(med('letter_h_pct'))} % | {round(med('block_w_pct'))} % |")
h=np.sum([s[v]['hist10'] for v in V],axis=0); h=h/h.sum()*100
print('\nDistribuição vertical de todos os blocos (centro do texto, % da altura): '+' · '.join(f"{i*10}–{i*10+10} %: {round(x)} %" for i,x in enumerate(h)))
print('\n### Tabela F — primeiros e últimos blocos lidos por OCR\n')
print('| Ref. | Primeiros 5 blocos | Últimos 5 blocos |'); print('|---|---|---|')
for v in V: print(f"| {v} | {' / '.join(s[v]['first5'])} | {' / '.join(s[v]['last5'])} |")
# numeric labels: detections with digits not in subtitle band
print('\n### Números na tela (detecções de OCR com algarismos, excluindo legendas)\n')
print('| Ref. | Rótulos numéricos distintos | Exemplos |'); print('|---|---|---|')
inv={b:a for a,b in mp.items()}
for v in V:
    d=json.load(open(f"{W}/out/{inv[v]}_ocr.json")); seen=[]
    for fr in d:
        for x in fr['d']:
            if x['conf']>=0.7 and re.search(r'\d',x['txt']) and '@' not in x['txt']:
                t=x['txt'].strip()
                if not any(t==y for y in seen): seen.append(t)
    print(f"| {v} | {len(seen)} | {', '.join(seen[:12])} |")
