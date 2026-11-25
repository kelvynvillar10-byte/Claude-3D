#!/usr/bin/env python3
"""Piloto 01 — áudio: voz (temporária) + efeitos sonoros e trilha PROCEDURAIS (gerados aqui,
sem biblioteca de terceiros) + ducking + master em −14 LUFS / pico real ≤ −1 dBTP.

Lê montagem.json (eventos "sfx") e voz/voz.wav. Saída: saida/mix.wav (48 kHz, estéreo, 24 bits).
"""
import json, subprocess
from pathlib import Path
import numpy as np, soundfile as sf
from scipy import signal

P = Path(__file__).resolve().parents[1]
M = json.loads((P / "montagem.json").read_text())
SR = 48000; N = int(M["duracao"] * SR)
rng = np.random.default_rng(11)


def db(x):
    return 10 ** (x / 20)


def env(n, a=0.01, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(r, 1e-4))
    return e


def bp(x, lo, hi, ordem=2):
    b, a = signal.butter(ordem, [lo / (SR / 2), hi / (SR / 2)], "band"); return signal.lfilter(b, a, x)


def lp(x, f, ordem=2):
    b, a = signal.butter(ordem, f / (SR / 2), "low"); return signal.lfilter(b, a, x)


def ruido(n):
    return rng.standard_normal(n)


def sfx(tipo, ev):
    if tipo == "pop":
        n = int(0.06 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * (1400 - 6000 * t) * t) * env(n, 0.002, 0.018) * db(-20)
    if tipo in ("whoosh", "fusao_whoosh"):
        d = 0.32 if tipo == "whoosh" else 0.22; n = int(d * SR); t = np.arange(n) / SR
        x = ruido(n); out = np.zeros(n)
        for i, f in enumerate(np.linspace(400, 2600, 8)):   # varredura de banda
            seg = slice(int(i * n / 8), int((i + 1) * n / 8)); out[seg] = bp(x, f * 0.7, f * 1.3)[seg]
        e = np.sin(np.pi * t / d) ** 2
        return out * e * db(-17 if tipo == "whoosh" else -22)
    if tipo == "impacto_grave":
        n = int(0.9 * SR); t = np.arange(n) / SR
        f = 58 * np.exp(-t * 2.2) + 32
        corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.004, 0.32)
        clique = lp(ruido(n), 2500) * env(n, 0.001, 0.02)
        return (corpo * db(-10) + clique * db(-24))
    if tipo == "vento":
        n = int(1.4 * SR); t = np.arange(n) / SR
        return bp(ruido(n), 250, 900) * np.sin(np.pi * t / 1.4) ** 2 * db(-30)
    if tipo == "ticks":
        n = int(ev["dur"] * SR); out = np.zeros(n); k = 0; tt = 0.0
        while tt < ev["dur"]:
            i = int(tt * SR); m = int(0.012 * SR)
            if i + m < n:
                out[i:i + m] += np.sin(2 * np.pi * 2300 * np.arange(m) / SR) * env(m, 0.0005, 0.003)
            k += 1; tt += max(0.03, 0.11 * (0.9 ** k))
        return out * db(-26)
    if tipo == "riser":
        n = int(ev["dur"] * SR); t = np.arange(n) / SR; d = ev["dur"]
        tom = np.sin(2 * np.pi * np.cumsum(180 + 520 * (t / d) ** 2) / SR)
        return (tom * 0.5 + bp(ruido(n), 800, 4000) * 0.5) * (t / d) ** 2 * db(-24)
    if tipo == "vibracao":
        out = np.zeros(int(1.3 * SR))
        for k in range(ev["pulsos"]):
            n = int(0.24 * SR); t = np.arange(n) / SR
            zumbido = np.sign(np.sin(2 * np.pi * 172 * t)) * 0.6 + np.sin(2 * np.pi * 344 * t) * 0.4
            chacoalho = bp(ruido(n), 900, 3500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 43 * t)))
            pulso = (lp(zumbido, 1800) * 0.8 + chacoalho * 0.25) * np.minimum(1, t / 0.01) * np.minimum(1, (0.24 - t) / 0.02)
            i = int(k * 0.38 * SR); out[i:i + n] += pulso
        return out * db(-15)
    return None


def trilha(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for f, a in ((55.0, 0.9), (110.0, 0.6), (164.81, 0.35), (261.63, 0.18), (329.63, 0.1)):   # Lá menor, grave
        x += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.23 * t + f))
    x = lp(x, 900)
    fade = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.05)
    return x * fade * db(-24)


def ambiente(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return lp(ruido(n), 380) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.17 * t)) * db(-34)


voz, sr_v = sf.read(P / M["voz"], dtype="float64")
assert sr_v == SR
pista_voz = np.zeros(N); pista_voz[:min(N, len(voz))] = voz[:N]
musica = np.zeros(N); efeitos = np.zeros((N, 2))
for ev in M["sfx"]:
    i = int(ev["t"] * SR)
    if ev["tipo"] == "trilha":
        x = trilha(ev["dur"]); musica[i:i + len(x)] += x[:N - i]; continue
    if ev["tipo"] == "ambiente":
        x = ambiente(ev["dur"]); musica[i:i + len(x)] += x[:N - i]; continue
    x = sfx(ev["tipo"], ev)
    if x is None:
        continue
    x = x[:N - i]
    pan = {"whoosh": (1.0, 0.7), "fusao_whoosh": (0.8, 1.0), "vibracao": (0.9, 1.0)}.get(ev["tipo"], (1.0, 1.0))
    efeitos[i:i + len(x), 0] += x * pan[0]; efeitos[i:i + len(x), 1] += x * pan[1]

# ducking: trilha e ambiente descem ~10 dB quando a voz fala
e = np.sqrt(np.convolve(pista_voz ** 2, np.ones(int(0.05 * SR)) / int(0.05 * SR), "same"))
alvo = np.where(e > 0.02, db(-10), 1.0)
a_ = np.exp(-1 / (0.03 * SR)); g = np.empty(N); acc = 1.0
for k in range(N):   # ataque/soltura suaves
    acc = alvo[k] + (acc - alvo[k]) * a_; g[k] = acc
mix = np.stack([pista_voz, pista_voz], 1) + np.stack([musica * g, musica * g], 1) + efeitos
(P / "saida").mkdir(exist_ok=True)
bruto = P / "_cache" / "mix_bruto.wav"; bruto.parent.mkdir(exist_ok=True)
sf.write(bruto, mix / max(1.0, np.abs(mix).max()) * 0.9, SR, subtype="FLOAT")

# master: loudnorm em duas passadas (EBU R128) → −14 LUFS, pico real −1 dBTP
med = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(bruto), "-af", "loudnorm=I=-14:TP=-1.6:LRA=7:print_format=json",
                      "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(med[med.rindex("{"):med.rindex("}") + 1])
filtro = (f"loudnorm=I=-14:TP=-1.6:LRA=7:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
          f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto), "-af", filtro, "-ar", "48000", "-c:a", "pcm_s24le",
                str(P / "saida" / "mix.wav")], check=True)
fin = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(P / "saida" / "mix.wav"), "-af", "ebur128=peak=true", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
import re
print("medido no bruto:", j["input_i"], "LUFS ·", j["input_tp"], "dBTP")
print("master:", re.findall(r"I:\s+(-?[\d.]+) LUFS", fin)[-1], "LUFS · pico", re.findall(r"Peak:\s+(-?[\d.]+) dBFS", fin)[-1], "dBTP · LRA",
      re.findall(r"LRA:\s+(-?[\d.]+) LU", fin)[-1], "LU")
