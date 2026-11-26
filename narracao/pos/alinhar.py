"""Alinhamento de palavras SEM modelos externos (opção 1 aprovada pelo diretor).

1. O espeak-ng (biblioteca do sistema, via ctypes) lê o MESMO texto e informa, pelos eventos de palavra, a amostra exata
   em que cada palavra começa na voz de referência.
2. DTW (librosa) entre os MFCC da referência e os da narração real transfere esses inícios para a narração real.
   Áudios longos: DTW grosso (40 ms) no áudio inteiro e DTW fino (10 ms) em janelas sobrepostas ancoradas no grosso.
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


def _dtw_mapa(fa, fb):
    """DTW; devolve, para cada quadro de A, o quadro médio correspondente de B."""
    import librosa
    _, wp = librosa.sequence.dtw(X=fa, Y=fb, metric="euclidean", backtrack=True)
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
    k = 4                                                            # grosso: 40 ms, no áudio inteiro
    grosso = _dtw_mapa(_pool(fa, k), _pool(fb, k)) * k
    grosso = np.maximum.accumulate(np.interp(np.arange(fa.shape[1]), np.arange(len(grosso)) * k, grosso))
    # fino: janelas de ~20 s com sobreposição de 3 s, cada uma ANCORADA nas pontas pelo mapa grosso; só o miolo de cada
    # janela é aproveitado (as pontas, onde a âncora pode errar, ficam com a janela vizinha)
    mapa = np.full(fa.shape[1], np.nan); passo, sob = 2000, 300; a = 0
    while a < fa.shape[1]:
        b = min(fa.shape[1], a + passo + sob)
        ra = int(grosso[a]); rb = int(min(fb.shape[1], grosso[b - 1] + 1))
        if rb - ra < 2:
            mapa[a:b] = grosso[a:b]
        else:
            sub = _dtw_mapa(fa[:, a:b], fb[:, ra:rb]) + ra
            i0 = a if a == 0 else a + sob // 2; i1 = b if b == fa.shape[1] else b - sob // 2
            mapa[i0:i1] = sub[i0 - a:i1 - a]
        if b == fa.shape[1]:
            break
        a = b - sob
    mapa = np.where(np.isnan(mapa), grosso, mapa)
    return np.maximum.accumulate(mapa)


# ------------------------------------------------------------------ alinhamento completo
VOZES_REF = [("pt-br", 175, 50), ("pt-br+m3", 155, 38), ("pt", 168, 48)]   # conjunto: a mediana corta erros de uma voz só


def _estimativa_global(texto, real16):
    """Início estimado de cada palavra no áudio inteiro (mediana de 3 vozes de referência)."""
    est = []
    for voz, vel, tom in VOZES_REF:
        ref, ini = falar_espeak(texto, voz=voz, velocidade=vel, tom=tom)
        m = mapear(ref, real16)
        est.append([float(m[min(len(m) - 1, int(round(t * SR_REF / HOP)))]) * HOP / SR_REF for t in ini])
    return np.median(np.array(est), 0)


def _fronteiras(texto, toks):
    """Fronteiras de pontuação entre palavras: (k = palavra antes, peso: 1 fim de frase, 0,6 vírgula, dois-pontos ou reticência)."""
    out = []
    for k in range(len(toks) - 1):
        sep = texto[toks[k]["c1"]:toks[k + 1]["c0"]]
        if re.search(r"[.!?]", sep):
            out.append((k, 1.0))
        elif re.search(r"[,;:—–…]", sep):                             # reticência no meio da frase nem sempre vira pausa
            out.append((k, 0.6))
    return out


def _casar_pausas(fronts, est, pausas):
    """Casa fronteiras de pontuação com pausas reais (programação dinâmica, em ordem). Devolve {k: (ini, fim) da pausa}."""
    nB, nP = len(fronts), len(pausas)
    INF = 1e18
    D = np.full((nB + 1, nP + 1), INF); D[0, 0] = 0; T = np.zeros((nB + 1, nP + 1), int)
    pul_p = lambda p: 0.15 + 0.6 * (p[1] - p[0])                       # pausa sem pontuação (acontece: "apenas… cinco")
    for i in range(nB + 1):
        for j in range(nP + 1):
            if i == 0 and j == 0:
                continue
            best, arg = INF, 0
            if i > 0 and j > 0:
                k, w = fronts[i - 1]; p = pausas[j - 1]
                t = (est[k + 1] + est[k]) / 2 if k + 1 < len(est) else est[k]
                c = D[i - 1, j - 1] + min(abs(t - p[0]), abs(t - p[1]), abs(t - (p[0] + p[1]) / 2)) * 0.8 - w * min(p[1] - p[0], 0.6) * 0.5
                if c < best:
                    best, arg = c, 1
            if i > 0:
                c = D[i - 1, j] + fronts[i - 1][1] * 0.35                 # pontuação sem pausa
                if c < best:
                    best, arg = c, 2
            if j > 0:
                c = D[i, j - 1] + pul_p(pausas[j - 1])
                if c < best:
                    best, arg = c, 3
            D[i, j] = best; T[i, j] = arg
    i, j, casadas = nB, nP, {}
    while i > 0 or j > 0:
        a = T[i, j]
        if a == 1:
            casadas[fronts[i - 1][0]] = pausas[j - 1]; i -= 1; j -= 1
        elif a == 2:
            i -= 1
        else:
            j -= 1
    return casadas


def _dtw_trecho(texto_trecho, real16, sr16=SR_REF):
    """Inícios (s, relativos ao trecho) das palavras de um trecho curto: DTW completo com 3 vozes, mediana."""
    toks = tokens(texto_trecho)
    if len(toks) == 1:
        return [0.0]
    fb = _feat(real16)
    est = []
    for voz, vel, tom in VOZES_REF:
        ref, ini = falar_espeak(texto_trecho, voz=voz, velocidade=vel, tom=tom)
        fa = _feat(ref)
        if fa.shape[1] < 2 or fb.shape[1] < 2:
            continue
        m = _dtw_mapa(fa, fb)
        est.append([float(m[min(len(m) - 1, int(round(t * SR_REF / HOP)))]) * HOP / SR_REF for t in ini])
    if not est:
        n = len(toks); dur = len(real16) / sr16
        return [dur * i / n for i in range(n)]
    v = np.median(np.array(est), 0); v[0] = 0.0
    return list(np.maximum.accumulate(v))


def alinhar(texto, real48, falas, silencios, sr=48000):
    """Palavras com início e fim (s) na narração real. `falas`/`silencios` vêm de audio.segmentar.
    1) estimativa global (DTW, mediana de 3 vozes); 2) as fronteiras de pontuação são casadas com as pausas reais e viram
    ÂNCORAS; 3) cada trecho entre âncoras é alinhado sozinho (o erro não se propaga); 4) ajuste fino pelas pausas."""
    import librosa
    toks = tokens(texto)
    if not toks:
        return []
    real16 = librosa.resample(real48, orig_sr=sr, target_sr=SR_REF)
    est = _estimativa_global(texto, real16)
    ini_fala = falas[0][0] if falas else 0.0
    fim_fala = falas[-1][1] if falas else len(real48) / sr
    pausas = [s for s in silencios if s[0] > ini_fala and s[1] < fim_fala and s[1] - s[0] >= 0.12]
    casadas = _casar_pausas(_fronteiras(texto, toks), est, pausas)
    # trechos entre âncoras
    cortes = sorted(casadas)
    ini = [None] * len(toks)
    inicio_trecho, k0 = ini_fala, 0
    for k in cortes + [len(toks) - 1]:
        k1 = k
        fim_trecho = casadas[k][0] if k in casadas else fim_fala
        a, b = int(inicio_trecho * SR_REF), int(fim_trecho * SR_REF)
        txt = texto[toks[k0]["c0"]:toks[k1]["c1"]]
        rel = _dtw_trecho(txt, real16[a:b]) if b - a > int(0.05 * SR_REF) else [0.0] * (k1 - k0 + 1)
        for j, r in enumerate(rel[:k1 - k0 + 1]):
            ini[k0 + j] = inicio_trecho + r
        if k in casadas:
            inicio_trecho, k0 = casadas[k][1], k + 1
    _interpolar(ini)
    ini = list(np.maximum.accumulate(ini))
    fim = ini[1:] + [fim_fala]
    for k, p in casadas.items():                                       # a palavra antes da âncora termina na pausa
        fim[k] = p[0]
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
