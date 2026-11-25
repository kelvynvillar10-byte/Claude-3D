"""Cenografia — CÉU e ATMOSFERA em 2D no compositor (E1).

Por que 2D: nuvens volumétricas no Cycles em CPU custariam minutos por quadro e não animariam. Aqui elas são
campos de densidade procedurais (fBm com distorção de domínio), iluminados pela direção do sol na tela, em 3 camadas
de profundidade que derivam com velocidades diferentes (paralaxe de céu). Tudo determinístico pela semente.

- nuvens(...)  → camadas RGBA lineares, prontas para entrar ENTRE o céu e o resto da cena
- estrelas(...), lua(...) → noite (lua com fase e halo; estrelas com cintilação)
- chuva(...)   → riscos de chuva em 3 profundidades (com borrão de movimento) — vai NA FRENTE de tudo
Climas (no compositor): limpo, nublado (cobertura alta + luz difusa), neblina (névoa densa), chuva (nublado +
riscos + placa com piso molhado).
"""
import math
import numpy as np, cv2


def _ruido_valor(h, w, celulas, rng):
    """Ruído de valor suave: grade aleatória ampliada com interpolação bicúbica."""
    gh, gw = max(2, int(h / celulas)) + 3, max(2, int(w / celulas)) + 3
    g = rng.random((gh, gw)).astype(np.float32)
    return cv2.resize(g, (int(gw * celulas), int(gh * celulas)), interpolation=cv2.INTER_CUBIC)[:h, :w]


def fbm(h, w, escala_px, oitavas, rng, rug=0.55):
    acc = np.zeros((h, w), np.float32); amp, tot, cel = 1.0, 0.0, float(escala_px)
    for _ in range(oitavas):
        acc += amp * _ruido_valor(h, w, max(2.0, cel), rng); tot += amp; amp *= rug; cel /= 2.0
    return acc / tot


def campo_nuvens(h, w, semente, escala_px=520.0, cobertura=0.45, achatamento=2.4, distorcao=0.35):
    """Densidade 0–1 de nuvens (estilizadas: bordas definidas, miolo macio). Mais 'cumulus' com cobertura baixa."""
    rng = np.random.default_rng(semente)
    hh = int(h / achatamento) + 8                                 # nuvens achatadas na vertical (perspectiva do céu)
    wx = fbm(hh, w, escala_px * 0.6, 3, rng); wy = fbm(hh, w, escala_px * 0.6, 3, rng)
    base = fbm(hh, w, escala_px, 5, rng)
    xx, yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(hh, dtype=np.float32))
    d = cv2.remap(base, xx + (wx - 0.5) * escala_px * distorcao, yy + (wy - 0.5) * escala_px * distorcao * 0.5,
                  cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    limiar = 1.0 - cobertura
    d = np.clip((d - limiar * 0.62 - 0.19) / 0.16, 0, 1)
    d = d * d * (3 - 2 * d)
    return cv2.resize(d, (w, h), interpolation=cv2.INTER_CUBIC)


def iluminar_nuvens(dens, sol_tela_dir, cor_luz, cor_sombra, cor_borda, espessura_px=28.0):
    """Lado virado para o sol mais claro (diferença de densidade deslocada), miolo na cor de sombra, borda fina
    contra o sol com 'prata' (luz atravessando a borda)."""
    dx, dy = sol_tela_dir
    M = np.float32([[1, 0, dx * espessura_px], [0, 1, dy * espessura_px]])
    deslocada = cv2.warpAffine(dens, M, (dens.shape[1], dens.shape[0]), borderMode=cv2.BORDER_REFLECT)
    luz = np.clip(dens - deslocada + 0.55, 0, 1)[..., None]
    borda = np.clip(dens * (1 - dens) * 4, 0, 1)[..., None]
    cor = cor_sombra * (1 - luz) + cor_luz * luz
    cor = cor + cor_borda * borda * 0.6
    return cor.astype(np.float32), dens.astype(np.float32)


def direcao_sol_na_tela(intr, sol_dir_mundo):
    """Direção 2D (unitária) na tela, do centro para onde o sol está (mesmo fora do quadro)."""
    d = np.array(sol_dir_mundo, np.float32)
    dx = float(np.dot(d, intr["dir_x"])); dy = -float(np.dot(d, intr["cima"])); dz = float(np.dot(d, intr["dir"]))
    v = np.array([dx, dy if dz > -0.2 else dy], np.float32); n = float(np.linalg.norm(v)) or 1.0
    return (v[0] / n, v[1] / n)


def estrelas(h, w, semente, densidade=0.0009, t=0.0):
    rng = np.random.default_rng(semente); n = int(h * w * densidade)
    ys, xs = rng.integers(0, h, n), rng.integers(0, w, n)
    brilho = rng.pareto(2.5, n).astype(np.float32) * 0.15 + 0.05
    fase = rng.random(n) * 6.283
    cint = 0.75 + 0.25 * np.sin(fase + t * (1.5 + rng.random(n) * 3.0))
    img = np.zeros((h, w), np.float32); np.add.at(img, (ys, xs), brilho * cint)
    img = cv2.GaussianBlur(img, (0, 0), 0.8) * 6.0
    cor = np.array([0.85, 0.9, 1.0], np.float32)
    return img[..., None] * cor


def lua(h, w, cx, cy, raio, fase=0.7, semente=1, brilho=2.0):
    """Disco da lua com fase (0 nova → 1 cheia), textura de mares e halo. Retorna RGB linear e alfa."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = (xx - cx) / raio, (yy - cy) / raio; r2 = dx * dx + dy * dy
    disco = np.clip((1 - np.sqrt(r2)) * raio / 1.5, 0, 1)
    # terminador: elipse deslocada (fase)
    k = 1 - 2 * fase
    lado = dx - k * np.sqrt(np.clip(1 - dy * dy, 0, 1))
    acesa = np.clip(lado * raio / 2.0 + 0.5, 0, 1) if fase < 1 else np.ones_like(dx)
    rng = np.random.default_rng(semente)
    mares = 0.82 + 0.18 * cv2.resize(rng.random((9, 9)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    cor = np.array([1.0, 0.97, 0.9], np.float32) * brilho
    rgb = (disco * acesa * mares)[..., None] * cor
    halo = np.exp(-np.maximum(0, np.sqrt(r2) - 1) * 2.5)[..., None] * np.array([0.25, 0.3, 0.42], np.float32) * 0.5 * fase
    return rgb + halo, disco


def chuva(h, w, semente, t, intensidade=1.0, vento=0.18, profundidades=((0.25, 0.35, 900), (0.55, 0.6, 500), (1.0, 1.0, 160))):
    """Riscos de chuva (RGB linear aditivo + alfa) em 3 profundidades: (escala, brilho, quantidade).
    Cada gota cai com velocidade proporcional à proximidade; o risco é o borrão de movimento em 1/48 s."""
    rng = np.random.default_rng(semente); img = np.zeros((h, w), np.float32)
    for esc, bri, n in profundidades:
        n = int(n * intensidade)
        x0 = rng.random(n) * w; y0 = rng.random(n) * h; vel = (2600 + rng.random(n) * 900) * esc
        comp = vel / 48.0; y = (y0 + vel * t) % (h + comp) - comp; x = (x0 + vel * vento * t) % w
        esp = max(1, int(round(2.2 * esc)))
        for xi, yi, ci in zip(x, y, comp):
            cv2.line(img, (int(xi), int(yi)), (int(xi + ci * vento), int(yi + ci)), float(bri) * 0.35, esp, cv2.LINE_AA)
    img = cv2.GaussianBlur(img, (0, 0), 0.7)
    return img[..., None] * np.array([0.8, 0.85, 0.95], np.float32), np.clip(img * 1.6, 0, 0.8)
