#!/usr/bin/env python3
"""EP01 — áudio: narração final (narracao/edicoes/ep01_narracao/voz_final.wav, −16 LUFS, sem aceleração) + efeitos
sonoros e trilha PROCEDURAIS (gerados aqui, sem biblioteca de terceiros: biblioteca de música/SFX ainda é pendência do
diretor) + ducking da trilha sob a voz + master −14 LUFS / pico ≤ −1 dBTP (ganho fixo + limitador, como a pós da voz).
Saída: saida/mix.wav (48 kHz, estéreo, 24 bits).
"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf
from scipy import signal

P = Path(__file__).resolve().parents[1]; RAIZ = P.parents[1]
M = json.loads((P / "montagem.json").read_text())
SR = 48000; N = int(round(M["duracao"] * SR))
rng = np.random.default_rng(11)


def db(x):
    return 10 ** (x / 20)


def env(n, a=0.01, r=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(r, 1e-4))


def bp(x, lo, hi, o=2):
    b, a = signal.butter(o, [lo / (SR / 2), hi / (SR / 2)], "band"); return signal.lfilter(b, a, x)


def lp(x, f, o=2):
    b, a = signal.butter(o, f / (SR / 2), "low"); return signal.lfilter(b, a, x)


def ruido(n):
    return rng.standard_normal(n)


def sfx(ev):
    tipo = ev["tipo"]
    if tipo == "pop":
        n = int(0.05 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * (1300 - 5000 * t) * t) * env(n, 0.002, 0.015) * db(-27)
    if tipo == "whoosh":
        d = 0.3; n = int(d * SR); t = np.arange(n) / SR; x = ruido(n); out = np.zeros(n)
        for i, f in enumerate(np.linspace(350, 2400, 8)):
            seg = slice(int(i * n / 8), int((i + 1) * n / 8)); out[seg] = bp(x, f * 0.7, f * 1.3)[seg]
        return out * np.sin(np.pi * t / d) ** 2 * db(-20)
    if tipo == "impacto_grave":
        n = int(0.8 * SR); t = np.arange(n) / SR; f = 58 * np.exp(-t * 2.4) + 34
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.004, 0.28) * db(-13) + lp(ruido(n), 2400) * env(n, 0.001, 0.02) * db(-26)
    if tipo == "riser":
        d = ev["dur"]; n = int(d * SR); t = np.arange(n) / SR
        tom = np.sin(2 * np.pi * np.cumsum(160 + 480 * (t / d) ** 2) / SR)
        return (tom * 0.5 + bp(ruido(n), 700, 3800) * 0.5) * (t / d) ** 2 * db(-27)
    if tipo == "gota":                                                 # pingo: tom que sobe rápido + ressonância curta
        n = int(0.25 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * np.cumsum(900 + 2600 * np.minimum(1, t / 0.03)) / SR) * env(n, 0.001, 0.05) * db(-22)
    if tipo == "patinhas":                                             # passinhos rápidos da aranha (tique-tiques secos)
        n = int(ev["dur"] * SR); out = np.zeros(n); tt = 0.0
        while tt < ev["dur"]:
            i = int(tt * SR); m = int(0.008 * SR)
            if i + m < n:
                out[i:i + m] += bp(ruido(m), 2500, 7000) * env(m, 0.0005, 0.002)
            tt += rng.uniform(0.03, 0.07)
        return out * db(-24)
    if tipo == "chiado_gato":                                          # chiado (ruído filtrado com envelope), não é gravação de animal
        n = int(0.7 * SR); t = np.arange(n) / SR
        return bp(ruido(n), 1800, 6500) * np.minimum(1, t / 0.05) * np.exp(-np.maximum(0, t - 0.3) / 0.2) * db(-24)
    if tipo == "vento":
        d = ev["dur"]; n = int(d * SR); t = np.arange(n) / SR
        return bp(ruido(n), 220, 1100) * np.sin(np.pi * t / d) ** 2 * (0.7 + 0.3 * np.sin(2 * np.pi * 1.3 * t)) * db(-24)
    return None


def trilha(dur):
    """Trilha leve de curiosidade: pad em Ré menor com arpejo suave (procedural), timbre quente e discreto."""
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    acordes = [(146.83, 174.61, 220.0), (116.54, 146.83, 174.61), (130.81, 164.81, 196.0), (110.0, 138.59, 164.81)]   # Dm Bb C A
    passo = 4.0
    for k, ac in enumerate(acordes * int(math.ceil(dur / (passo * len(acordes))) + 1)):
        i0 = int(k * passo * SR); i1 = min(n, int((k + 1) * passo * SR) + int(0.5 * SR))
        if i0 >= n:
            break
        tt = t[i0:i1] - t[i0]; seg = np.zeros(i1 - i0)
        for f in ac:
            seg += np.sin(2 * np.pi * f * tt) * 0.6 + np.sin(2 * np.pi * 2 * f * tt) * 0.12
        fade = np.minimum(1, tt / 0.6) * np.minimum(1, (tt[-1] - tt + 1e-6) / 0.5)
        x[i0:i1] += seg * fade
        for j in range(8):                                             # arpejo: notas curtas a cada meio segundo
            a0 = int((k * passo + j * 0.5) * SR)
            if a0 >= n:
                break
            f = ac[j % 3] * 2; m = min(n - a0, int(0.45 * SR)); tm = np.arange(m) / SR
            x[a0:a0 + m] += np.sin(2 * np.pi * f * tm) * np.exp(-tm / 0.18) * 0.35
    x = lp(x, 2200)
    fade = np.minimum(1, t / 1.0) * np.minimum(1, (dur - t) / 1.2)
    return x / (np.abs(x).max() + 1e-9) * fade * db(-22)


def ambiente(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return lp(ruido(n), 350) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.17 * t)) * db(-40)


import math                                                            # noqa: E402

voz, sr_v = sf.read(RAIZ / M["voz"], dtype="float64")
assert sr_v == SR, sr_v
if voz.ndim > 1:
    voz = voz.mean(1)
pista_voz = np.zeros(N); pista_voz[:min(N, len(voz))] = voz[:N]
musica = np.zeros(N); efeitos = np.zeros((N, 2))
for ev in M["sfx"]:
    i = int(ev["t"] * SR)
    if i >= N:
        continue
    if ev["tipo"] in ("trilha", "ambiente"):
        x = (trilha if ev["tipo"] == "trilha" else ambiente)(ev["dur"]); musica[i:i + len(x)] += x[:N - i]; continue
    x = sfx(ev)
    if x is None:
        continue
    x = x[:N - i]; pan = {"whoosh": (1.0, 0.7), "patinhas": (0.7, 1.0), "chiado_gato": (1.0, 0.85)}.get(ev["tipo"], (1.0, 1.0))
    efeitos[i:i + len(x), 0] += x * pan[0]; efeitos[i:i + len(x), 1] += x * pan[1]

# ducking: a trilha desce ~9 dB enquanto a voz fala (ataque/soltura suaves)
e = np.sqrt(np.convolve(pista_voz ** 2, np.ones(int(0.05 * SR)) / int(0.05 * SR), "same"))
alvo = np.where(e > 0.01, db(-9), 1.0)
b_, a_ = signal.butter(1, 4.0 / (SR / 2)); g = signal.filtfilt(b_, a_, alvo)
mix = np.stack([pista_voz, pista_voz], 1) + np.stack([musica * g, musica * g], 1) + efeitos



def medir(arq):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(arq), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return (float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1]),
            float(re.findall(r"LRA:\s+(-?[\d.]+) LU", e)[-1]))


(P / "saida").mkdir(exist_ok=True); bruto = P / "_cache" / "mix_bruto.wav"; bruto.parent.mkdir(exist_ok=True)
sf.write(bruto, mix.astype(np.float32), SR, subtype="FLOAT")
ganho = -14.0 - medir(bruto)[0]                                          # medido no ESTÉREO (as duas pistas somam)
for passada in range(3):                                               # ganho fixo + limitador de pico (sobreamostragem 4×)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto), "-af",
                    f"volume={ganho:.3f}dB,aresample=192000:resampler=soxr,alimiter=limit=0.84:attack=3:release=60:level=disabled:latency=1,aresample=48000:resampler=soxr",
                    "-c:a", "pcm_s24le", str(P / "saida" / "mix.wav")], check=True)
    I, pico, lra = medir(P / "saida" / "mix.wav")
    if abs(I + 14.0) < 0.15:
        break
    ganho += -14.0 - I
print(f"master: {I} LUFS · pico {pico} dBTP · LRA {lra} LU · ganho {ganho:+.2f} dB")
