#!/usr/bin/env python3
"""Cena de prova — áudio: o mesmo trecho da narração final do EP01 (39,20–58,90 s), sem edição na voz, com efeitos
sincronizados às AÇÕES novas (passos da aranha e do gato, zoom brusco, pata, tropeço, bote) e a mesma trilha procedural.
Reaproveita os sintetizadores do EP01 (audio_ep01.py) sem alterá-los. Master: −14 LUFS, pico ≤ −1 dBTP."""
import re, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf
from scipy import signal

P = Path(__file__).resolve().parents[1]; RAIZ = P.parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cena_dinamica as CD                                                   # noqa: E402

fonte = (RAIZ / "producoes/ep01_cinco_centimetros/codigo/audio_ep01.py").read_text()
ns = {"__file__": str(RAIZ / "producoes/ep01_cinco_centimetros/codigo/audio_ep01.py")}
exec(compile(fonte[:fonte.index("voz, sr_v = sf.read")], "audio_ep01", "exec"), ns)     # só as funções (sfx, trilha, ambiente, medir)
ini_medir = fonte.index("def medir(arq):"); exec(compile(fonte[ini_medir:fonte.index("(P / \"saida\").mkdir")], "audio_ep01_medir", "exec"), ns)
SR = ns["SR"]; T0, DUR = CD.T0, CD.DUR; N = int(round(DUR * SR))

EVENTOS = [  # (instante absoluto, tipo, duração)
    (40.40, "whoosh", 0), (40.50, "riser", 0.85), (41.40, "whoosh", 0), (43.00, "pop", 0),
    (44.05, "patinhas", 0.55), (44.32, "impacto_grave", 0), (44.42, "pop", 0), (45.55, "riser", 0.4), (46.10, "patinhas", 0.9),
    (46.95, "whoosh", 0), (47.00, "patinhas_gato", 1.4), (49.35, "pop", 0), (52.85, "impacto_grave", 0),
    (54.25, "passos", 0.9), (55.50, "whoosh", 0), (56.50, "impacto_grave", 0), (56.52, "chiado_gato", 0),
    (57.50, "whoosh", 0), (57.55, "passos_corrida", 1.3), (58.15, "impacto_grave", 0),
]


def efeito(tipo, dur):
    if tipo == "patinhas_gato":                                     # passos macios do gato: tique grave abafado
        x = ns["sfx"]({"tipo": "patinhas", "dur": dur}); return ns["lp"](x, 900) * 2.2
    if tipo in ("passos", "passos_corrida"):                        # passinhos do Heitor (em escala de 5 cm: tiques secos)
        n = int(dur * SR); out = np.zeros(n); per = 0.43 if tipo == "passos" else 0.28; tt = 0.02
        while tt < dur:
            i = int(tt * SR); m = int(0.012 * SR)
            if i + m < n:
                out[i:i + m] += ns["bp"](ns["ruido"](m), 1500, 5000) * ns["env"](m, 0.0005, 0.004)
            tt += per / 2
        return out * ns["db"](-26)
    return ns["sfx"]({"tipo": tipo, "dur": dur})


voz, sr = sf.read(RAIZ / "narracao/edicoes/ep01_narracao/voz_final.wav", dtype="float64")
assert sr == SR
voz = voz.mean(1) if voz.ndim > 1 else voz
i0 = int(T0 * SR); pista_voz = voz[i0:i0 + N]
pista_voz = pista_voz * np.minimum(1, np.arange(N) / (0.02 * SR)) * np.minimum(1, (N - np.arange(N)) / (0.25 * SR))
musica = ns["trilha"](DUR) + ns["ambiente"](DUR)
efeitos = np.zeros((N, 2))
for t, tipo, d in EVENTOS:
    x = efeito(tipo, d); i = int((t - T0) * SR); x = x[:N - i]
    pan = {"whoosh": (1.0, 0.7), "patinhas": (0.7, 1.0), "chiado_gato": (1.0, 0.85), "patinhas_gato": (0.8, 1.0)}.get(tipo, (1.0, 1.0))
    efeitos[i:i + len(x), 0] += x * pan[0]; efeitos[i:i + len(x), 1] += x * pan[1]
e = np.sqrt(np.convolve(pista_voz ** 2, np.ones(int(0.05 * SR)) / int(0.05 * SR), "same"))
b_, a_ = signal.butter(1, 4.0 / (SR / 2)); g = signal.filtfilt(b_, a_, np.where(e > 0.01, ns["db"](-9), 1.0))
mix = np.stack([pista_voz] * 2, 1) + np.stack([musica * g] * 2, 1) + efeitos

saida = P / "saida"; saida.mkdir(exist_ok=True); bruto = P / "_cache" / "mix_bruto.wav"; bruto.parent.mkdir(exist_ok=True)
sf.write(bruto, mix.astype(np.float32), SR, subtype="FLOAT")
ganho = -14.0 - ns["medir"](bruto)[0]
for _ in range(3):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto), "-af",
                    f"volume={ganho:.3f}dB,aresample=192000:resampler=soxr,alimiter=limit=0.84:attack=3:release=60:level=disabled:latency=1,aresample=48000:resampler=soxr",
                    "-c:a", "pcm_s24le", str(saida / "mix.wav")], check=True)
    I, pico, lra = ns["medir"](saida / "mix.wav")
    if abs(I + 14.0) < 0.15:
        break
    ganho += -14.0 - I
print(f"master: {I} LUFS · pico {pico} dBTP · LRA {lra} LU")
