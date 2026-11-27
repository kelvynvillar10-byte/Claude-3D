#!/usr/bin/env python3
"""EP02 — áudio: narração final do diretor (narracao/edicoes/ep02_narracao/voz_final.wav, −16 LUFS, sem aceleração) +
trilha e efeitos PROCEDURAIS (gerados aqui; nenhuma biblioteca de terceiros) sincronizados às AÇÕES da decupagem +
ducking da trilha sob a voz + master −14 LUFS / pico ≤ −1 dBTP. Reaproveita os sintetizadores do EP01 sem alterá-los.
Saída: saida/mix.wav (48 kHz, estéreo, 24 bits)."""
import json, math, re, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf
from scipy import signal

P = Path(__file__).resolve().parents[1]; RAIZ = P.parents[1]
fonte = (RAIZ / "producoes/ep01_cinco_centimetros/codigo/audio_ep01.py").read_text()
ns = {"__file__": str(RAIZ / "producoes/ep01_cinco_centimetros/codigo/audio_ep01.py")}
exec(compile(fonte[:fonte.index("voz, sr_v = sf.read")], "audio_ep01", "exec"), ns)
ini_medir = fonte.index("def medir(arq):"); exec(compile(fonte[ini_medir:fonte.index("(P / \"saida\").mkdir")], "audio_ep01_medir", "exec"), ns)
SR = ns["SR"]; db, env, bp, lp, ruido, sfx0 = ns["db"], ns["env"], ns["bp"], ns["lp"], ns["ruido"], ns["sfx"]
PLANOS = json.loads((P / "saida" / "planos.json").read_text())
DUR = PLANOS[-1]["fim"]; N = int(round(DUR * SR))
rng = np.random.default_rng(23)


def tom(f, d, a=0.002, r=0.2, harm=(1.0,)):
    n = int(d * SR); t = np.arange(n) / SR; x = sum(h * np.sin(2 * np.pi * f * (k + 1) * t) for k, h in enumerate(harm))
    return x * env(n, a, r)


def sfx(tipo, dur=0.0):
    if tipo in ("pop", "whoosh", "impacto_grave", "riser", "gota", "vento"):
        return sfx0({"tipo": tipo, "dur": dur or 1.0})
    if tipo == "passos":                                   # passos de adulto no piso de madeira: baque grave + estalo
        n = int(dur * SR); out = np.zeros(n); tt = 0.03
        while tt < dur:
            i = int(tt * SR); m = int(0.12 * SR)
            if i + m < n:
                tm = np.arange(m) / SR
                out[i:i + m] += (np.sin(2 * np.pi * 95 * tm) * env(m, 0.002, 0.04) + bp(ruido(m), 900, 3000) * env(m, 0.001, 0.01) * 0.4)
            tt += 0.45
        return out * db(-24)
    if tipo == "brilho":                                   # sininhos (arpejo agudo)
        out = np.zeros(int(0.9 * SR))
        for k, f in enumerate((1568, 1976, 2349, 3136)):
            x = tom(f, 0.6, 0.001, 0.25, (1.0, 0.3)); i = int(k * 0.07 * SR); out[i:i + len(x)] += x
        return out * db(-26)
    if tipo == "ding":
        return tom(1760, 0.8, 0.001, 0.3, (1.0, 0.4, 0.15)) * db(-23)
    if tipo == "liga":                                     # TV/console ligando: bipe suave + zumbido que sobe
        n = int(0.7 * SR); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * np.cumsum(300 + 900 * t) / SR) * env(n, 0.05, 0.3) * 0.5 + tom(880, 0.7, 0.001, 0.12)) * db(-24)
    if tipo == "clique":
        n = int(0.04 * SR); return bp(ruido(n), 2000, 6000) * env(n, 0.0005, 0.006) * db(-22)
    if tipo == "progresso":                                # tiques da barra de instalação
        n = int(dur * SR); out = np.zeros(n); tt = 0.0; k = 0
        while tt < dur:
            x = tom(1200 + 40 * k, 0.05, 0.001, 0.02); i = int(tt * SR); out[i:i + len(x)] += x[:n - i]; tt += 0.11; k += 1
        return out * db(-28)
    if tipo == "coracao":                                  # "tum-tum" acelerando (72 → 140 BPM)
        n = int(dur * SR); out = np.zeros(n); tt = 0.0
        while tt < dur:
            bpm = 72 + 68 * min(1, tt / (dur * 0.77))
            for dt, g in ((0.0, 1.0), (0.18, 0.6)):
                i = int((tt + dt) * SR); m = int(0.16 * SR)
                if i + m < n:
                    tm = np.arange(m) / SR; out[i:i + m] += g * np.sin(2 * np.pi * (60 - 40 * tm) * tm) * env(m, 0.004, 0.05)
            tt += 60 / bpm
        return out * db(-12)
    if tipo == "moedas":
        n = int(dur * SR); out = np.zeros(n)
        for _ in range(int(dur * 9)):
            i = int(rng.uniform(0, dur - 0.3) * SR); x = tom(rng.uniform(2500, 4200), 0.25, 0.0005, 0.06, (1.0, 0.5)); out[i:i + len(x)] += x
        return out * db(-30)
    if tipo == "motor":                                    # motor do carro do jogo: serra grave filtrada subindo
        n = int(dur * SR); t = np.arange(n) / SR; f = 70 + 60 * (t / dur)
        x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) + 0.5 * signal.sawtooth(2 * np.pi * np.cumsum(f * 2.01) / SR)
        return lp(x, 900) * np.minimum(1, t / 0.08) * np.minimum(1, (dur - t) / 0.15) * db(-24)
    if tipo == "relogio":                                  # tique-taque acelerado (passagem do tempo)
        n = int(dur * SR); out = np.zeros(n); tt = 0.0; k = 0
        while tt < dur:
            m = int(0.02 * SR); i = int(tt * SR)
            if i + m < n:
                out[i:i + m] += bp(ruido(m), 3000 if k % 2 else 2200, 7000) * env(m, 0.0005, 0.004)
            tt += max(0.06, 0.25 - 0.19 * tt / dur); k += 1
        return out * db(-20)
    if tipo == "esfria":                                   # tom que desce (temperatura caindo)
        n = int(dur * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * np.cumsum(900 - 600 * t / dur) / SR) * env(n, 0.05, dur) * db(-30)
    if tipo == "passaros":                                 # gorjeios sintéticos (não é gravação)
        n = int(dur * SR); out = np.zeros(n)
        for _ in range(int(dur * 3)):
            i = int(rng.uniform(0, dur - 0.25) * SR); m = int(0.12 * SR); tm = np.arange(m) / SR; f0 = rng.uniform(2800, 4200)
            x = np.sin(2 * np.pi * np.cumsum(f0 + 1500 * np.sin(2 * np.pi * 25 * tm)) / SR) * env(m, 0.005, 0.04); out[i:i + m] += x
        return out * db(-30)
    if tipo == "fracasso":                                 # "uó-uó-uóóó" descendente (cômico)
        out = np.zeros(int(1.6 * SR))
        for k, (f, d) in enumerate(((392, 0.3), (370, 0.3), (349, 0.3), (330, 0.7))):
            n = int(d * SR); t = np.arange(n) / SR
            x = signal.sawtooth(2 * np.pi * np.cumsum(f * (1 + 0.02 * np.sin(2 * np.pi * 6 * t))) / SR, 0.5)
            i = int(sum(dd for _, dd in ((392, 0.3), (370, 0.3), (349, 0.3))[:k]) * SR); out[i:i + n] += lp(x, 1500) * env(n, 0.02, d * 0.8)
        return out * db(-26)
    if tipo == "boing":
        n = int(0.5 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * np.cumsum(220 + 180 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)) / SR) * env(n, 0.002, 0.3) * db(-24)
    if tipo == "redemoinho":
        n = int(dur * SR); t = np.arange(n) / SR
        return (bp(ruido(n), 300, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * (2 + 6 * t / dur) * t)) * (t / dur) ** 1.5) * db(-22)
    if tipo == "baque":
        n = int(0.35 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * (80 - 30 * t) * t) * env(n, 0.003, 0.09) * db(-17)
    raise KeyError(tipo)


def P_(pid):
    return next(p for p in PLANOS if p["id"] == pid)["ini"]


EVENTOS = [  # (instante, tipo, duração)
    (0.0, "passos", 1.85), (2.15, "brilho", 0), (6.15, "passos", 1.35), (7.82, "impacto_grave", 0), (8.70, "riser", 0.6), (9.30, "brilho", 0),
    (9.90, "brilho", 0), (10.30, "riser", 1.2), (11.4, "ding", 0), (12.30, "boing", 0), (13.25, "liga", 0), (14.9, "progresso", 1.0), (15.95, "ding", 0),
    (16.95, "riser", 1.2), (20.9, "whoosh", 0), (21.48, "baque", 0), (21.5, "brilho", 0), (22.3, "brilho", 0), (23.2, "coracao", 1.15),
    (24.4, "brilho", 0), (25.8, "moedas", 2.3), (28.3, "boing", 0), (31.3, "clique", 0), (31.36, "liga", 0), (32.45, "whoosh", 0), (32.95, "baque", 0),
    (33.4, "riser", 1.85), (35.25, "motor", 1.6), (36.05, "whoosh", 0), (36.95, "whoosh", 0), (41.7, "relogio", 2.1), (43.85, "ding", 0),
    (45.1, "passos", 0.9), (47.8, "ding", 0), (49.3, "esfria", 1.3), (50.7, "ding", 0), (52.95, "boing", 0), (57.25, "ding", 0),
    (58.45, "passaros", 2.8), (62.40, "impacto_grave", 0), (65.65, "fracasso", 0), (66.8, "riser", 0.5), (69.6, "motor", 1.2),
    (73.95, "boing", 0), (75.12, "fracasso", 0), (79.6, "clique", 0), (80.2, "clique", 0), (82.5, "redemoinho", 2.9), (85.3, "impacto_grave", 0),
    (85.6, "brilho", 0),
]


def trilha_ep02(dur):
    """Trilha de comédia leve em Dó maior (C–G–Am–F, 112 BPM): baixo saltitante, pad e arpejo; mais "synth" no jogo."""
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n); bpm = 112; bt = 60 / bpm
    acordes = [(130.81, 164.81, 196.0), (98.0, 123.47, 146.83), (110.0, 130.81, 164.81), (87.31, 110.0, 130.81)]
    k = 0; tt = 0.0
    while tt < dur:
        ac = acordes[k % 4]; i0 = int(tt * SR); L = int(4 * bt * SR); i1 = min(n, i0 + L + int(0.3 * SR)); seg_t = np.arange(i1 - i0) / SR
        pad = sum(np.sin(2 * np.pi * f * 2 * seg_t) for f in ac) * 0.25 * np.minimum(1, seg_t / 0.3) * np.minimum(1, (seg_t[-1] - seg_t + 1e-6) / 0.3)
        x[i0:i1] += pad
        for b in range(4):                                 # baixo nos tempos
            a0 = int((tt + b * bt) * SR); m = min(n - a0, int(0.28 * SR))
            if m <= 0:
                break
            tm = np.arange(m) / SR; f = ac[0] / 2 * (1.5 if b == 3 else 1.0)
            x[a0:a0 + m] += np.sin(2 * np.pi * f * tm) * np.exp(-tm / 0.12) * 0.9
        for j in range(8):                                 # arpejo em colcheias
            a0 = int((tt + j * bt / 2) * SR); m = min(n - a0, int(0.22 * SR))
            if m <= 0:
                break
            tm = np.arange(m) / SR; f = ac[j % 3] * 4
            jogo = 33.3 <= tt + j * bt / 2 <= 39.9 or 69.6 <= tt <= 72.3
            onda = signal.square(2 * np.pi * f * tm, 0.3) * 0.25 if jogo else np.sin(2 * np.pi * f * tm)
            x[a0:a0 + m] += onda * np.exp(-tm / 0.09) * 0.32
        tt += 4 * bt; k += 1
    x = lp(x, 3000)
    # dinâmica: mais baixa e escura no amanhecer triste (61–69 s), sobe no final
    g = np.ones(n); g[(t > 61.0) & (t < 69.5)] = 0.55
    g = signal.filtfilt(*signal.butter(1, 1.0 / (SR / 2)), g)
    fade = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 1.5)
    return x / (np.abs(x).max() + 1e-9) * fade * g * db(-21)


if __name__ == "__main__":
    voz, sr_v = sf.read(RAIZ / "narracao/edicoes/ep02_narracao/voz_final.wav", dtype="float64")
    assert sr_v == SR
    voz = voz.mean(1) if voz.ndim > 1 else voz
    pista_voz = np.zeros(N); pista_voz[:min(N, len(voz))] = voz[:N]
    efeitos = np.zeros((N, 2))
    eventos = list(EVENTOS)
    for p in PLANOS[1:]:                                   # um efeito em cada corte (baixo, por baixo da voz)
        eventos.append((max(0.0, p["ini"] - (0.12 if p["entrada"] == "chicote" else 0.0)),
                        {"chicote": "whoosh", "flash": "impacto_grave", "fusao": "riser"}.get(p["entrada"], "pop"), 0.25))
    for t0, tipo, d in eventos:
        x = sfx(tipo, d); i = int(t0 * SR)
        if i >= N:
            continue
        x = x[:N - i]; pan = {"whoosh": (1.0, 0.7), "passos": (0.85, 1.0), "moedas": (0.9, 1.0), "passaros": (0.7, 1.0)}.get(tipo, (1.0, 1.0))
        efeitos[i:i + len(x), 0] += x * pan[0]; efeitos[i:i + len(x), 1] += x * pan[1]
    musica = trilha_ep02(DUR) + ns["ambiente"](DUR)
    e = np.sqrt(np.convolve(pista_voz ** 2, np.ones(int(0.05 * SR)) / int(0.05 * SR), "same"))
    b_, a_ = signal.butter(1, 4.0 / (SR / 2)); g = signal.filtfilt(b_, a_, np.where(e > 0.01, db(-9), 1.0))
    mix = np.stack([pista_voz] * 2, 1) + np.stack([musica * g] * 2, 1) + efeitos
    saida = P / "saida"; saida.mkdir(exist_ok=True); bruto = P / "_cache" / "mix_bruto.wav"; bruto.parent.mkdir(exist_ok=True)
    sf.write(bruto, mix.astype(np.float32), SR, subtype="FLOAT")
    ganho = -14.0 - ns["medir"](bruto)[0]
    for _ in range(4):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto), "-af",
                        f"volume={ganho:.3f}dB,aresample=192000:resampler=soxr,alimiter=limit=0.84:attack=3:release=60:level=disabled:latency=1,aresample=48000:resampler=soxr",
                        "-c:a", "pcm_s24le", str(saida / "mix.wav")], check=True)
        I, pico, lra = ns["medir"](saida / "mix.wav")
        if abs(I + 14.0) < 0.15:
            break
        ganho += -14.0 - I
    (saida / "sfx.json").write_text(json.dumps([dict(t=round(a, 3), tipo=b, dur=c) for a, b, c in sorted(eventos)], ensure_ascii=False, indent=1) + "\n")
    print(f"master: {I} LUFS · pico {pico} dBTP · LRA {lra} LU · {len(eventos)} efeitos")
