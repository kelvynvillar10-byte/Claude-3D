#!/usr/bin/env python3
"""EP02 — refaz só alguns planos e emenda no vídeo já renderizado (sem refazer o episódio inteiro).
Uso: refazer_planos.py P02,P03,... [--trabalhadores 3]
1) renderiza cada plano pedido em _cache/refazer/<id>.mp4 (em paralelo, MAX_PLACAS=2);
2) remonta _cache/video_sem_audio.mp4 quadro a quadro: plano refeito onde houver, original no resto."""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np

AQUI = Path(__file__).resolve().parent; P_ = AQUI.parent
FPS = 30; OW, OH = 1080, 1920
planos = {p["id"]: p for p in json.loads((P_ / "saida" / "planos.json").read_text())}
ids = sys.argv[1].split(",")
trab = int(sys.argv[sys.argv.index("--trabalhadores") + 1]) if "--trabalhadores" in sys.argv else 3
pasta = P_ / "_cache" / "refazer"; pasta.mkdir(parents=True, exist_ok=True)
faixas = {i: (int(round(planos[i]["ini"] * FPS)), int(round(planos[i]["fim"] * FPS))) for i in ids}
fila = sorted(ids, key=lambda i: -(faixas[i][1] - faixas[i][0]))
grupos = [[] for _ in range(trab)]; carga = [0] * trab
for i in fila:                                   # distribui por carga (quadros)
    k = carga.index(min(carga)); grupos[k].append(i); carga[k] += faixas[i][1] - faixas[i][0]
procs = []
for g in grupos:
    if not g:
        continue
    cmd = " && ".join(f"{sys.executable} {AQUI / 'cenas_ep02.py'} --seg {pasta / (i + '.mp4')} --de {faixas[i][0]} --ate {faixas[i][1]}" for i in g)
    procs.append(subprocess.Popen(cmd, shell=True, env=dict(os.environ, OMP_NUM_THREADS="1", MAX_PLACAS="2")))
for p in procs:
    p.wait()
for i in ids:
    nq = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries", "stream=nb_read_frames",
                             "-of", "csv=p=0", str(pasta / f"{i}.mp4")], capture_output=True, text=True).stdout.strip() or 0)
    if nq != faixas[i][1] - faixas[i][0]:
        raise SystemExit(f"PARADO: {i} tem {nq} quadros (esperado {faixas[i][1] - faixas[i][0]})")


def leitor(arq):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(arq), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)


orig = P_ / "_cache" / "video_sem_audio.mp4"; novo = P_ / "_cache" / "video_sem_audio_novo.mp4"
r0 = leitor(orig); tam = OW * OH * 3
w = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "pipe:0",
                      "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", str(novo)], stdin=subprocess.PIPE)
inicio = {a: i for i, (a, b) in faixas.items()}; atual = None; fim_atual = -1; n = 0
while True:
    q = r0.stdout.read(tam)
    if len(q) < tam:
        break
    if n in inicio:
        atual = leitor(pasta / f"{inicio[n]}.mp4"); fim_atual = faixas[inicio[n]][1]
    if atual is not None and n < fim_atual:
        q = atual.stdout.read(tam)
        if n == fim_atual - 1:
            atual.stdout.close(); atual.wait(); atual = None
    w.stdin.write(q); n += 1
w.stdin.close(); w.wait()
os.replace(novo, orig)
print(f"ok: {n} quadros; refeitos: {', '.join(ids)}")
