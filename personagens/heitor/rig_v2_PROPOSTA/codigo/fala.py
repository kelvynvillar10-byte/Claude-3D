#!/usr/bin/env python3
"""Heitor rig v2 (PROPOSTA) — fala de TESTE e sincronia labial (fase F4).

Voz: espeak-ng (TEMPORÁRIA, a mesma do piloto 01; a voz oficial depende da decisão ID-001 — sem clonagem).
Para ter o tempo EXATO de cada palavra (o espeak-ng não informa tempos), cada palavra é sintetizada sozinha e
as palavras são emendadas com pausas curtas. A fala fica um pouco mais pausada que a natural; é aceitável num teste.

Boca por quadro:
- ABERTURA vem do envelope de energia (RMS) do áudio, com ataque rápido e soltura curta → abre quando há som,
  fecha no silêncio.
- FORMATO vem das vogais da palavra (sílabas distribuídas por igual dentro da duração medida da palavra):
  a → boca aberta; e/i → aberta e larga (dentes); o/u → "o". m/b/p no início da sílaba fecham a boca por ~2 quadros.
  O formato por sílaba é APROXIMADO (o tempo de cada palavra é exato; o de cada sílaba, estimado).
"""
import re, subprocess, tempfile
import numpy as np

SR = 48000
VOZ = dict(voz="pt-br", wpm=175, tom=38)
_VOG = "aeiouáéíóúâêôãõàü"


def _sintetiza(palavra):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(["espeak-ng", "-v", VOZ["voz"], "-s", str(VOZ["wpm"]), "-p", str(VOZ["tom"]), "-a", "160",
                        "-w", f.name, palavra], check=True)
        bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", f.name, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                               capture_output=True, check=True).stdout
    y = np.frombuffer(bruto, np.float32).copy()
    env = np.convolve(np.abs(y), np.ones(240) / 240, "same")
    on = np.where(env > 0.02 * env.max())[0]
    return y[on[0]: on[-1] + 1]


def silabas(palavra):
    """Lista de (vogal_núcleo, começa_com_bilabial) — grupos de vogais = sílabas (aproximação do português)."""
    p = palavra.lower()
    out = []
    for m in re.finditer(f"[{_VOG}]+", p):
        antes = p[max(0, m.start() - 1): m.start()]
        out.append((m.group(0)[0], antes in ("m", "b", "p")))
    return out or [("a", False)]


def gerar(frase, pausa=0.07, pausa_pontuacao=0.28):
    """Retorna (áudio float32 mono SR, palavras: [(texto, t0, t1, silabas)])."""
    partes, palavras, t = [], [], 0.0
    for tok in frase.split():
        txt = tok.strip(",.!?…;:")
        y = _sintetiza(txt)
        palavras.append((txt, t, t + len(y) / SR, silabas(txt)))
        partes.append(y); t += len(y) / SR
        gap = pausa_pontuacao if tok[-1] in ",.!?…;:" else pausa
        partes.append(np.zeros(int(gap * SR), np.float32)); t += gap
    y = np.concatenate(partes)
    return y / (np.abs(y).max() + 1e-9) * 0.7, palavras


def rms_por_quadro(y, fps, n):
    passo = SR / fps
    r = np.array([np.sqrt(np.mean(y[int(i * passo): int((i + 1) * passo)] ** 2)) if int(i * passo) < len(y) else 0.0
                  for i in range(n)])
    return r / (r.max() + 1e-9)


def boca_por_quadro(y, palavras, fps, n, inicio=0.0):
    """Lista (len n) de None (sem fala) ou dict(boca, abertura, largura, dentes) — quadros a partir de 'inicio' (s)."""
    q0 = int(round(inicio * fps))
    r = np.zeros(n); rr = rms_por_quadro(y, fps, max(0, n - q0)); r[q0:q0 + len(rr)] = rr
    # envelope: ataque imediato, soltura de ~1–2 quadros (a boca não "treme" entre sílabas)
    env = np.zeros(n); v = 0.0
    for i in range(n):
        v = max(r[i], v * 0.4); env[i] = v
    out = [None] * n
    for i in range(n):
        t = i / fps - inicio
        pal = next((p for p in palavras if p[1] - 0.03 <= t <= p[2] + 0.03), None)
        if pal is None:
            continue
        txt, t0, t1, sil = pal
        k = min(len(sil) - 1, max(0, int((t - t0) / max(1e-6, t1 - t0) * len(sil))))
        vog, bil = sil[k]
        ini_sil = t0 + k * (t1 - t0) / len(sil)
        a = float(min(1.0, env[i] * 1.25))
        if bil and t - ini_sil < 0.07:
            a = 0.0
        if vog in "aáâãà":
            d = dict(boca="aberta", abertura=0.15 + 0.6 * a, largura=1.0, dentes=False)
        elif vog in "eéêiíü":
            d = dict(boca="sorriso_aberto", abertura=0.05 + 0.35 * a, largura=1.15, dentes=True)
        else:
            d = dict(boca="o", abertura=0.1 + 0.6 * a, largura=0.75 if vog in "uú" else 0.9, dentes=False)
        if a < 0.08:
            d = dict(boca="linha", abertura=0.0, largura=0.9, dentes=False)
        out[i] = d
    return out, r


def escrever_wav(caminho, y, inicio=0.0, dur=None):
    pre = np.zeros(int(inicio * SR), np.float32)
    z = np.concatenate([pre, y.astype(np.float32)])
    if dur:
        z = np.concatenate([z, np.zeros(max(0, int(dur * SR) - len(z)), np.float32)])[: int(dur * SR)]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", str(caminho)],
                   input=z.tobytes(), check=True)
