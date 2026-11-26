"""Áudio da pós-produção: leitura de qualquer formato (ffmpeg), gravação, impressão digital, fala × silêncio,
respirações e medidas (loudness, pico verdadeiro, espectro, tom). Nada aqui altera o arquivo original.
"""
import hashlib, json, re, subprocess
from pathlib import Path
import numpy as np

SR = 48000                    # taxa de trabalho e de entrega
QUADRO = 0.010                # 10 ms por quadro de análise


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def info(caminho):
    """Formato do arquivo original (ffprobe), sem decodificar."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=format_name,duration,bit_rate:stream=codec_name,sample_rate,channels,bits_per_raw_sample",
                        "-of", "json", str(caminho)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout); s = (j.get("streams") or [{}])[0]; f = j.get("format", {})
    return {"formato": f.get("format_name"), "codec": s.get("codec_name"), "taxa_hz": int(s.get("sample_rate", 0) or 0),
            "canais": s.get("channels"), "duracao_s": round(float(f.get("duration", 0) or 0), 3),
            "bitrate": int(f.get("bit_rate", 0) or 0) or None}


def ler(caminho, sr=SR):
    """Decodifica para mono float32 na taxa pedida (alta qualidade: soxr)."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(caminho), "-ac", "1", "-af", f"aresample={sr}:resampler=soxr:precision=28",
                          "-f", "f32le", "pipe:1"], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32).copy()


def gravar_wav(y, caminho, sr=SR):
    import soundfile as sf
    sf.write(str(caminho), np.asarray(y, np.float32), sr, subtype="PCM_24")


def gravar_mp3(y, caminho, sr=SR, kbps=320):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0", "-codec:a", "libmp3lame",
                    "-b:a", f"{kbps}k", str(caminho)], input=np.ascontiguousarray(y, np.float32).tobytes(), check=True)


def filtrar(y, cadeia, sr=SR, sr_saida=None):
    """Aplica uma cadeia de filtros do ffmpeg (float32 de ponta a ponta) e devolve (áudio, stderr)."""
    r = subprocess.run(["ffmpeg", "-v", "info", "-hide_banner", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0", "-af", cadeia,
                        "-ar", str(sr_saida or sr), "-ac", "1", "-f", "f32le", "pipe:1"],
                       input=np.ascontiguousarray(y, np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).copy(), r.stderr.decode(errors="replace")


# ------------------------------------------------------------------ energia, fala e silêncio
def energia_db(y, sr=SR, janela=0.020, passo=QUADRO):
    """RMS em dBFS por quadro (janela de 20 ms, passo de 10 ms)."""
    n = int(janela * sr); h = int(passo * sr)
    if len(y) < n:
        y = np.pad(y, (0, n - len(y)))
    q = np.lib.stride_tricks.sliding_window_view(y, n)[::h]
    return 20 * np.log10(np.sqrt((q.astype(np.float64) ** 2).mean(1)) + 1e-10)


def segmentar(y, sr=SR, limiar_rel_db=-38.0, piso_db=-58.0, pausa_min=0.060, fala_min=0.030):
    """Fala × silêncio por energia com histerese. O limiar é relativo ao nível da fala (percentil 95), mas nunca abaixo
    do piso. Devolve (falas, silencios) em segundos: listas de [ini, fim]."""
    e = energia_db(y, sr)
    ref = np.percentile(e, 95)
    lim = max(ref + limiar_rel_db, piso_db)
    fala = e > lim
    # fecha buracos menores que pausa_min (oclusivas, micro-quedas dentro da palavra)
    n_pausa = int(round(pausa_min / QUADRO)); n_fala = int(round(fala_min / QUADRO))
    runs = _corridas(fala)
    for v, a, b in runs:
        if not v and (b - a) < n_pausa and a > 0 and b < len(fala):
            fala[a:b] = True
    for v, a, b in _corridas(fala):
        if v and (b - a) < n_fala:
            fala[a:b] = False
    falas = [[round(a * QUADRO, 3), round(b * QUADRO, 3)] for v, a, b in _corridas(fala) if v]
    dur = round(len(y) / sr, 3)
    silencios = []; t = 0.0
    for a, b in falas:
        if a > t:
            silencios.append([t, a])
        t = b
    if t < dur:
        silencios.append([t, dur])
    return falas, silencios, {"limiar_db": round(float(lim), 1), "nivel_fala_p95_db": round(float(ref), 1)}


def _corridas(m):
    out = []; i = 0; n = len(m)
    while i < n:
        j = i
        while j < n and m[j] == m[i]:
            j += 1
        out.append((bool(m[i]), i, j)); i = j
    return out


def respiracoes(y, silencios, sr=SR):
    """Respirações dentro das pausas: trecho com energia acima do piso, bem abaixo da fala, e espectro de ruído (planura
    espectral alta). Devolve [ini, fim, nível_db]. Heurística medida, não garantia."""
    import librosa
    out = []
    if not len(y):
        return out
    ref = np.percentile(energia_db(y, sr), 95)
    for a, b in silencios:
        if b - a < 0.15:
            continue
        seg = y[int(a * sr):int(b * sr)]
        e = energia_db(seg, sr)
        ativo = (e > ref - 45) & (e < ref - 12)
        if ativo.sum() * QUADRO < 0.08:
            continue
        idx = np.where(ativo)[0]
        s = seg[idx[0] * int(QUADRO * sr): (idx[-1] + 2) * int(QUADRO * sr)]
        plan = float(np.median(librosa.feature.spectral_flatness(y=s, n_fft=1024, hop_length=480)))
        if plan > 0.08:
            out.append([round(a + idx[0] * QUADRO, 3), round(a + (idx[-1] + 2) * QUADRO, 3), round(float(e[idx].max()), 1)])
    return out


# ------------------------------------------------------------------ medidas
def loudness(y, sr=SR):
    """EBU R128 pelo ffmpeg: integrado (LUFS), faixa (LU) e pico verdadeiro (dBTP)."""
    _, err = filtrar(y, "ebur128=peak=true:framelog=quiet", sr)
    def pega(rotulo):
        m = re.findall(rf"{rotulo}:\s+(-?[\d.]+|-inf)", err)
        return float(m[-1]) if m and m[-1] != "-inf" else None
    return {"integrado_lufs": pega("I"), "faixa_lu": pega("LRA"), "pico_verdadeiro_dbtp": pega("Peak")}


def tom(y, sr=SR):
    """Curva de tom (pyin) a 16 kHz: mediana e faixa (p10–p90) em Hz e em semitons."""
    import librosa
    z = librosa.resample(y, orig_sr=sr, target_sr=16000) if sr != 16000 else y
    f0, voz, _ = librosa.pyin(z, fmin=60, fmax=400, sr=16000, frame_length=1024, hop_length=160)
    f = f0[voz & np.isfinite(f0)]
    if len(f) < 5:
        return {"mediana_hz": None, "p10_hz": None, "p90_hz": None, "faixa_semitons": None, "quadros_com_voz": int(len(f))}
    p10, p50, p90 = np.percentile(f, [10, 50, 90])
    return {"mediana_hz": round(float(p50), 1), "p10_hz": round(float(p10), 1), "p90_hz": round(float(p90), 1),
            "faixa_semitons": round(float(12 * np.log2(p90 / p10)), 2), "quadros_com_voz": int(len(f))}


def espectro_bandas(y, sr=SR):
    """Energia relativa por banda (dB em relação ao total) só nos quadros de fala: corpo, lama, presença, sibilância."""
    from scipy.signal import welch
    f, p = welch(y, sr, nperseg=4096)
    tot = p.sum() + 1e-20
    def banda(a, b):
        return round(float(10 * np.log10(p[(f >= a) & (f < b)].sum() / tot + 1e-20)), 2)
    return {"graves_20_80": banda(20, 80), "corpo_80_250": banda(80, 250), "lama_250_500": banda(250, 500),
            "medios_500_2k": banda(500, 2000), "presenca_2k_5k": banda(2000, 5000), "sibilancia_5k_10k": banda(5000, 10000),
            "ar_10k_mais": banda(10000, sr / 2)}


def piso_ruido_db(y, silencios, sr=SR):
    """Nível do silêncio (mediana do RMS nas pausas ≥ 0,1 s, sem as pontas)."""
    vals = []
    for a, b in silencios:
        if b - a >= 0.1:
            seg = y[int((a + 0.02) * sr):int((b - 0.02) * sr)]
            if len(seg):
                vals.append(20 * np.log10(np.sqrt((seg.astype(np.float64) ** 2).mean()) + 1e-10))
    return round(float(np.median(vals)), 1) if vals else None


def cliques(y, sr=SR, razao=10.0, piso_db=-50.0, silencios=None):
    """Cliques/estalos: impulsos curtos no agudo (> 3 kHz) muito acima do nível local (média de 20 ms em volta).
    Só conta os que caem DENTRO das pausas (`silencios`), onde o clique é inequívoco: dentro da fala, consoantes
    explosivas ("p", "t", "k") produzem o mesmo pico (medido na voz real: 45 falsos positivos, todos na fala)."""
    from scipy.signal import butter, sosfiltfilt
    if len(y) < sr // 10:
        return []
    hp = sosfiltfilt(butter(4, 3000, "highpass", fs=sr, output="sos"), y.astype(np.float64))
    a = np.abs(hp)
    w = int(0.020 * sr)
    local = np.sqrt(np.convolve(a ** 2, np.ones(w) / w, "same")) + 1e-9
    cand = np.where((a / local > razao) & (a > 10 ** (piso_db / 20)))[0]
    out = []
    for i in cand:
        if not out or i / sr - out[-1] > 0.02:
            out.append(round(i / sr, 3))
    if silencios is not None:
        out = [c for c in out if any(a + 0.01 < c < b - 0.01 for a, b in silencios if b - a >= 0.06)]
    return out


def imagem_onda(caminho_audio, caminho_png, titulo=""):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(caminho_audio), "-filter_complex",
                    "showwavespic=s=1600x300:split_channels=0:colors=0x2b6cb0", "-frames:v", "1", str(caminho_png)], check=True)


def imagem_espectro(caminho_audio, caminho_png):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(caminho_audio), "-lavfi",
                    "showspectrumpic=s=1600x400:legend=1:scale=log:fscale=log:stop=16000", "-frames:v", "1", str(caminho_png)], check=True)
