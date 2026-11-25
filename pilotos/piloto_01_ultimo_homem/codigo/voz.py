#!/usr/bin/env python3
"""Piloto 01 — narração TEMPORÁRIA com espeak-ng (substituível pela voz oficial ID-001).

Sintetiza cada bloco de legenda separadamente, corta o silêncio das bordas e monta a
narração com pausas no padrão do canal (dentro da frase: 0,06 s; fim de frase: 0,18 s).
Assim o tempo exato de cada bloco é conhecido (substitui o "with-timestamps" do TTS oficial).

Saída: voz/voz.wav (48 kHz mono) e voz/tempos.json (blocos e palavras com início/fim).
Uso: .venv/bin/python codigo/voz.py [--wpm 182]
"""
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
import soundfile as sf

P = Path(__file__).resolve().parents[1]
rot = json.loads((P / "roteiro.json").read_text())
wpm = int(sys.argv[sys.argv.index("--wpm") + 1]) if "--wpm" in sys.argv else rot["voz"]["velocidade_wpm"]
SR = 48000


def sintetiza(txt):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(["espeak-ng", "-v", rot["voz"]["voz"], "-s", str(wpm), "-p", str(rot["voz"]["tom"]),
                        "-a", "160", "-w", f.name, txt], check=True)
        out = subprocess.run(["ffmpeg", "-v", "error", "-i", f.name, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
    y = np.frombuffer(out, np.float32).copy()
    env = np.convolve(np.abs(y), np.ones(480) / 480, "same")
    on = np.where(env > 0.01 * env.max())[0]
    return y[max(0, on[0] - 240): on[-1] + 240]


partes, blocos, t = [], [], 0.0
for i, b in enumerate(rot["blocos"]):
    y = sintetiza(b["fala"])
    ini, fim = t, t + len(y) / SR
    palavras, letras = b["txt"].split(), sum(len(w) for w in b["txt"].split())
    acc, pal = ini, []
    for w in palavras:
        d = (fim - ini) * len(w) / letras
        pal.append({"w": w, "ini": round(acc, 3), "fim": round(acc + d, 3)}); acc += d
    blocos.append({**b, "ini": round(ini, 3), "fim": round(fim, 3), "palavras": pal})
    partes.append(y)
    fim_frase = b["fala"].rstrip()[-1] in ".?!"
    gap = 0.18 if fim_frase else 0.06
    if i < len(rot["blocos"]) - 1:
        partes.append(np.zeros(int(gap * SR), np.float32)); t = fim + gap
voz = np.concatenate(partes)
voz = voz / np.abs(voz).max() * 0.89
(P / "voz").mkdir(exist_ok=True)
sf.write(P / "voz" / "voz.wav", voz, SR, subtype="PCM_24")
dur = len(voz) / SR
(P / "voz" / "tempos.json").write_text(json.dumps({"wpm": wpm, "duracao_voz": round(dur, 3), "blocos": blocos},
                                                     ensure_ascii=False, indent=1))
print(f"voz: {dur:.2f} s com {wpm} wpm · {sum(len(b['txt'].split()) for b in blocos)} palavras")
for b in blocos:
    print(f"  {b['ini']:5.2f}–{b['fim']:5.2f}  plano {b['plano']}  {b['txt']}")
