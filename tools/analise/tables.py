import json,sys,numpy as np
W=sys.argv[1]; s=json.load(open(W+'/summary.json'))
idx={'v01':(99,53,32,1.75,66,-13.9),'v06':(87,47,32,1.77,58,-14.2),'v07':(85,36,25,2.26,62,-14.1),'v10':(124,69,34,1.83,67,-14.1),'v12':(81,41,30,1.40,67,-14.1),'v13':(86,43,30,1.25,60,-14.2),'v14':(89,46,31,1.38,58,-14.1),'v15':(92,51,33,1.48,56,-14.1),'v16':(137,69,30,1.83,55,-21.0),'v17':(134,72,32,1.67,42,-14.3),'v18':(141,88,37,1.58,62,-14.1),'v19':(131,75,34,1.60,56,-14.3),'v20':(117,60,31,1.91,61,-14.1)}
f=lambda x,n=2: ('%.*f'%(n,x)).replace('.',',')
V=sorted(s)
print('### Tabela A — ritmo e câmera\n')
print('| Ref. | Duração (s) | Planos | Cortes/min | Plano mediano (s) | p10–p90 (s) | 1º corte (s) | Planos c/ movimento | Push-in | Push-in %/s (med.) | Push-in total (med.) | Pull-out | Crash-zoom | Chicote/min* | Flash/min | Quadro segurado/min |')
print('|'+'---|'*16)
for v in V:
    o=s[v]; print(f"| {v} | {f(o['dur'],1)} | {o['shots']} | {f(o['cpm'],1)} | {f(o['shot_med'])} | {f(o['shot_p10'])}–{f(o['shot_p90'])} | {f(o['first_cut'])} | {o['pct_moved']} % | {o['pct_push']} % | {f(o['push_rate_med'],1)} | {f(o['push_tot_med'],1)} % | {o['pct_pull']} % | {o['pct_crash']} % | {f(o['whip_pm'],1)} | {f(o['flash_pm'],1)} | {f(o['held_pm'],1)} |")
med=lambda k: float(np.median([s[v][k] for v in V]))
print(f"| **Mediana** | {f(med('dur'),1)} | {f(med('shots'),0)} | {f(med('cpm'),1)} | {f(med('shot_med'))} | {f(med('shot_p10'))}–{f(med('shot_p90'))} | {f(med('first_cut'))} | {f(med('pct_moved'),0)} % | {f(med('pct_push'),0)} % | {f(med('push_rate_med'),1)} | {f(med('push_tot_med'),1)} % | {f(med('pct_pull'),0)} % | {f(med('pct_crash'),0)} % | {f(med('whip_pm'),1)} | {f(med('flash_pm'),1)} | {f(med('held_pm'),1)} |")
print('\n### Tabela B — luz, cor e animação\n')
print('| Ref. | Luma Y | Saturação | Contraste (σ) | Vinheta (cantos/centro) | Sombra Lab a | Sombra Lab b | Alta luz Lab a | Alta luz Lab b | Movimento local | Pan** | Tilt** | Giro** |')
print('|'+'---|'*13)
for v in V:
    o=s[v]; print(f"| {v} | {f(o['Y'])} | {f(o['S'])} | {f(o['C'])} | {f(o['vig'])} | {f(o['sh_a'],1)} | {f(o['sh_b'],1)} | {f(o['hi_a'],1)} | {f(o['hi_b'],1)} | {f(o['local_motion'],3)} | {o['pct_pan']} % | {o['pct_tilt']} % | {o['pct_roll']} % |")
print(f"| **Mediana** | {f(med('Y'))} | {f(med('S'))} | {f(med('C'))} | {f(med('vig'))} | {f(med('sh_a'),1)} | {f(med('sh_b'),1)} | {f(med('hi_a'),1)} | {f(med('hi_b'),1)} | {f(med('local_motion'),3)} | {f(med('pct_pan'),0)} % | {f(med('pct_tilt'),0)} % | {f(med('pct_roll'),0)} % |")
print('\n### Tabela C — áudio\n')
print('| Ref. | LUFS integrado | LRA (LU) | Pico (dBFS, true peak) | Graves <250 Hz | Banda de voz 300–3400 Hz | Eventos sonoros/s | Cortes com evento sonoro (±100 ms) | Pausas ≥ 0,8 s no meio |')
print('|'+'---|'*9)
for v in V:
    o=s[v]; print(f"| {v} | {f(o['LUFS'],1)} | {f(o['LRA'],1)} | {f(o['TP'],1)} | {f(o['bass'],1)} % | {f(o['voice'],1)} % | {f(o['onsets_ps'])} | {o['cuts_on_sound']} % | {o['long_pauses']} |")
print(f"| **Mediana** | {f(med('LUFS'),1)} | {f(med('LRA'),1)} | {f(med('TP'),1)} | {f(med('bass'),1)} % | {f(med('voice'),1)} % | {f(med('onsets_ps'))} | {f(med('cuts_on_sound'),0)} % | {f(med('long_pauses'),0)} |")
print('\n### Tabela D — conferência com o relatório `index.html` (mesmos vídeos)\n')
print('| Ref. | Duração idx / nossa | Planos idx / nosso | Cortes/min idx / nosso | Plano mediano idx / nosso | Vinheta idx / nossa | LUFS idx / nosso |')
print('|'+'---|'*7)
for v in V:
    o=s[v]; i=idx[v]; print(f"| {v} | {i[0]} / {f(o['dur'],1)} | {i[1]} / {o['shots']} | {i[2]} / {f(o['cpm'],1)} | {f(i[3])} / {f(o['shot_med'])} | {i[4]} % / {round(o['vig']*100)} % | {f(i[5],1)} / {f(o['LUFS'],1)} |")
dec=np.array([s[v]['cut_deciles'] for v in V]).mean(0)
print('\nCortes por segundo ao longo do vídeo (média dos 13; 0 % = início): '+' · '.join(f"{i*10}–{i*10+10} %: {f(x)}" for i,x in enumerate(dec)))
