"""Alinhamento de palavras SEM modelos externos (opção 1 aprovada pelo diretor).

1. O espeak-ng (biblioteca do sistema, via ctypes) lê o MESMO texto e informa, pelos eventos de palavra, a amostra exata
   em que cada palavra começa na voz de referência.
2. DTW (librosa) entre os MFCC da referência e os da narração real transfere esses inícios para a narração real.
   Áudios longos: DTW grosso (40 ms) para achar a região de cada frase e DTW fino (10 ms) dentro dela.
3. Ajuste pelas pausas medidas na narração real: nenhuma palavra começa ou termina dentro de um silêncio.
A precisão é MEDIDA no teste F0 (referência espeak contra outra voz espeak com tempos verdadeiros) e informada no relatório.
"""
import ctypes, re
import numpy as np

SR_REF = 16000
HOP = 160                      # 10 ms a 16 kHz
PALAVRA = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]+(?:[-'’][0-9A-Za-zÀ-ÖØ-öø-ÿ]+)*")


def tokens(texto):
    """Palavras do texto com a posição (caractere) de cada uma."""
    return [{"w": m.group(0), "c0": m.start(), "c1": m.end()} for m in PALAVRA.finditer(texto)]


# ------------------------------------------------------------------ espeak-ng (referência com tempos exatos)
class _EV(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("unique_identifier", ctypes.c_uint), ("text_position", ctypes.c_int),
                ("length", ctypes.c_int), ("audio_position", ctypes.c_int), ("sample", ctypes.c_int),
                ("user_data", ctypes.c_void_p), ("id", ctypes.c_char * 8)]


_LIB = None
_SR_ESPEAK = None


def _lib():
    global _LIB, _SR_ESPEAK
    if _LIB is None:
        _LIB = ctypes.CDLL("libespeak-ng.so.1")
        _SR_ESPEAK = _LIB.espeak_Initialize(2, 0, None, 0)          # AUDIO_OUTPUT_SYNCHRONOUS
    return _LIB


def falar_espeak(texto, voz="pt-br", velocidade=175, tom=50, faixa=50):
    """Sintetiza com o espeak-ng e devolve (áudio float32 a 16 kHz, inícios das palavras em segundos por token).
    Os inícios vêm dos eventos de palavra da própria biblioteca (não são estimados)."""
    import librosa
    lib = _lib()
    buf, evs = [], []
    CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.POINTER(_EV))

    def cb(wav, n, ev):
        if n > 0:
            buf.append(np.ctypeslib.as_array(wav, (n,)).copy())
        i = 0
        while ev[i].type != 0:
            if ev[i].type == 1:                                        # espeakEVENT_WORD
                evs.append((ev[i].text_position - 1, ev[i].sample))
            i += 1
        return 0
    c = CB(cb)
    lib.espeak_SetSynthCallback(c)
    lib.espeak_SetVoiceByName(voz.encode())
    for p, v in ((1, velocidade), (3, tom), (4, faixa)):             # RATE, PITCH, RANGE
        lib.espeak_SetParameter(p, int(v), 0)
    t = texto.encode("utf-8")
    lib.espeak_Synth(t, len(t) + 1, 0, 1, 0, 1, None, None)
    lib.espeak_Synchronize()
    y = (np.concatenate(buf).astype(np.float32) / 32768.0) if buf else np.zeros(1, np.float32)
    toks = tokens(texto)
    ini = []
    for tk in toks:
        cand = [s for pos, s in evs if tk["c0"] <= pos < tk["c1"]]
        ini.append(min(cand) / _SR_ESPEAK if cand else None)
    _interpolar(ini)
    y16 = librosa.resample(y, orig_sr=_SR_ESPEAK, target_sr=SR_REF)
    return y16, ini


def _interpolar(v):
    idx = [i for i, x in enumerate(v) if x is not None]
    if not idx:
        return
    for i in range(len(v)):
        if v[i] is None:
            a = max([j for j in idx if j < i], default=None); b = min([j for j in idx if j > i], default=None)
            v[i] = v[a] if b is None else v[b] if a is None else v[a] + (v[b] - v[a]) * (i - a) / (b - a)


# ------------------------------------------------------------------ DTW
def _feat(y16):
    import librosa
    m = librosa.feature.mfcc(y=y16, sr=SR_REF, n_mfcc=13, n_fft=400, hop_length=HOP, n_mels=40, fmin=60, fmax=7600)
    d = librosa.feature.delta(m, width=5)
    f = np.vstack([m, d])
    return ((f - f.mean(1, keepdims=True)) / (f.std(1, keepdims=True) + 1e-6)).astype(np.float32)


def _dtw_mapa(fa, fb, subseq=False):
    """DTW; devolve, para cada quadro de A, o quadro médio correspondente de B. `subseq`: A pode cair em qualquer trecho de B
    (usado nas janelas finas, para a janela não ser obrigada a começar/terminar junto com A)."""
    import librosa
    _, wp = librosa.sequence.dtw(X=fa, Y=fb, metric="euclidean", backtrack=True, subseq=subseq)
    wp = wp[::-1]
    mapa = np.zeros(fa.shape[1])
    for i in range(fa.shape[1]):
        mapa[i] = wp[wp[:, 0] == i, 1].mean()
    return mapa


def _pool(f, k):
    n = f.shape[1] // k
    return f[:, :n * k].reshape(f.shape[0], n, k).mean(2)


def mapear(ref16, real16, limite_celulas=2.5e7):
    """Mapa quadro-a-quadro (10 ms) da referência para a narração real."""
    fa, fb = _feat(ref16), _feat(real16)
    if fa.shape[1] * fb.shape[1] <= limite_celulas:
        return _dtw_mapa(fa, fb)
    k = 4                                                            # grosso: 40 ms
    grosso = _dtw_mapa(_pool(fa, k), _pool(fb, k)) * k
    mapa = np.interp(np.arange(fa.shape[1]), np.arange(len(grosso)) * k, grosso)
    # fino em janelas de ~20 s da referência, cada uma contra a região correspondente da real (±1,5 s)
    passo = 2000; margem = 150
    for a in range(0, fa.shape[1], passo):
        b = min(fa.shape[1], a + passo)
        ra = int(max(0, mapa[a] - margem)); rb = int(min(fb.shape[1], mapa[b - 1] + margem))
        if rb - ra < 10:
            continue
        if rb - ra < b - a:
            continue
        sub = _dtw_mapa(fa[:, a:b], fb[:, ra:rb], subseq=True) + ra
        mapa[a:b] = sub
    return np.maximum.accumulate(mapa)


# ------------------------------------------------------------------ alinhamento completo
def alinhar(texto, real48, falas, silencios, sr=48000):
    """Palavras com início e fim (s) na narração real. `falas`/`silencios` vêm de audio.segmentar."""
    import librosa
    toks = tokens(texto)
    if not toks:
        return []
    ref16, ini_ref = falar_espeak(texto)
    real16 = librosa.resample(real48, orig_sr=sr, target_sr=SR_REF)
    mapa = mapear(ref16, real16)
    ini = []
    for t in ini_ref:
        q = min(len(mapa) - 1, int(round(t * SR_REF / HOP)))
        ini.append(float(mapa[q]) * HOP / SR_REF)
    fim_fala = falas[-1][1] if falas else len(real48) / sr
    ini_fala = falas[0][0] if falas else 0.0
    ini[0] = min(ini[0], ini_fala) if abs(ini[0] - ini_fala) < 0.35 else ini[0]
    ini = list(np.maximum.accumulate(ini))
    fim = ini[1:] + [fim_fala]
    pal = [{"i": k, "w": tk["w"], "c0": tk["c0"], "c1": tk["c1"], "ini": ini[k], "fim": fim[k]} for k, tk in enumerate(toks)]
    _ajustar_pelas_pausas(pal, falas, silencios)
    for p in pal:
        p["ini"] = round(p["ini"], 3); p["fim"] = round(p["fim"], 3)
    return pal


def _ajustar_pelas_pausas(pal, falas, silencios, tol=0.15):
    """Fronteira entre duas palavras perto de um silêncio → a primeira termina no início do silêncio e a segunda começa
    no fim dele. Nenhum início/fim fica dentro de um silêncio."""
    internos = [s for s in silencios if s[0] > 0 and falas and s[1] < falas[-1][1] + 1e-6]
    for k in range(len(pal) - 1):
        b = pal[k + 1]["ini"]
        perto = [s for s in internos if s[0] - tol <= b <= s[1] + tol]
        if perto:
            s = min(perto, key=lambda s: abs((s[0] + s[1]) / 2 - b))
            if s[0] > pal[k]["ini"] + 0.03:
                pal[k]["fim"] = s[0]                                    # a palavra seguinte começa quando o silêncio acaba
                pal[k + 1]["ini"] = s[1] if s[1] < pal[k + 1]["fim"] else pal[k + 1]["ini"]
    for a, b in internos:                                            # silêncio longo DENTRO de uma palavra é fronteira
        if b - a < 0.15:
            continue
        for k, p in enumerate(pal):
            if p["ini"] < a and b < p["fim"]:
                if (p["fim"] - b) <= (a - p["ini"]) and k + 1 < len(pal):      # mais perto do fim: fronteira k | k+1
                    p["fim"] = a; pal[k + 1]["ini"] = min(pal[k + 1]["ini"], b)
                elif k > 0:                                                     # mais perto do início: fronteira k-1 | k
                    pal[k - 1]["fim"] = min(pal[k - 1]["fim"], a); p["ini"] = b
                break
    for p in pal:                                                    # início/fim nunca dentro de um silêncio
        for a, b in internos:
            if a < p["ini"] < b:
                p["ini"] = b
            if a < p["fim"] < b:
                p["fim"] = a
    for k, p in enumerate(pal):
        p["fim"] = max(p["fim"], p["ini"] + 0.04)
        if k + 1 < len(pal):
            p["fim"] = min(p["fim"], pal[k + 1]["ini"]) if pal[k + 1]["ini"] > p["ini"] + 0.04 else p["fim"]
    if falas:
        pal[-1]["fim"] = max(pal[-1]["fim"], min(falas[-1][1], pal[-1]["ini"] + 3.0))
