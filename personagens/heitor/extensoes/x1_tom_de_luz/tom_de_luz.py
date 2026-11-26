"""EXTENSÃO X1 (APROVADA em 26/11/2026) — TOM DE LUZ NO PERSONAGEM. Não altera o rig v2: atua DEPOIS do desenho, sobre a camada do
Heitor (RGBA), dentro do compositor (encaixe `tom_personagem`). O desenho (forma, contorno, alfa) não muda; só a luz.

Formato: o mesmo que o compositor recebe (cor não pré-multiplicada, como o skia entrega).

Três partes, todas medidas na própria cena:
1. TOM DO PLANO — cor (e, à noite, brilho) da luz ambiente, medida no cenário em volta do personagem.
   De dia: só a cor (o brilho fica igual). À noite: escurece até um PISO de legibilidade (0,62).
2. LUZ DE CONTORNO (rim) — borda do lado do sol/lua (direção do manifesto da placa), na cor do horário; e um degradê
   leve de volume (o lado da luz um pouco mais claro).
3. LUZ DOS EFEITOS — cada luz de efeito (posição 3D, cor, força) acende o lado do personagem voltado para ela
   (brilho difuso + contorno), caindo com a distância.
Limites de identidade: alfa idêntico; brilho somado limitado (MAX_SOMA); piso de brilho à noite; a estampa continua
legível (medido no teste).
"""
import math
import numpy as np
import cv2

PISO_NOITE = 0.62          # o Heitor nunca escurece mais que isto (legibilidade)
MAX_SOMA = 0.55            # luz somada máxima (linear) por pixel
FORCA_RIM = {"manha": 0.30, "meio_dia": 0.22, "tarde_dourada": 0.42, "crepusculo": 0.45, "noite": 0.20}
COR_RIM = {"manha": (1.0, 0.93, 0.80), "meio_dia": (1.0, 0.98, 0.92), "tarde_dourada": (1.0, 0.78, 0.50), "crepusculo": (1.0, 0.62, 0.55),
           "noite": (0.62, 0.72, 1.0)}
VOLUME = {"noite": 0.05}   # degradê de volume (dia: 0,10)
GANHO_RIM = 1.6            # contorno: luz somada = albedo × cor × força × ganho
FORCA_EFEITO_MAX = 1.5     # teto da força de uma luz de efeito no personagem


def _lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def _srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def parametros(P, cam, fundo_display, alfa, personagem, luzes=None, forca=1.0):
    """Calcula os parâmetros do tom no quadro (para registro e testes) a partir da cena."""
    I = P.m["intrinsecos"]; pos, dr, dx, cima = (np.asarray(I[k], float) for k in ("pos", "dir", "dir_x", "cima"))

    def tela(p):
        d = np.asarray(p, float) - pos; z = float(d @ dr); u = P.cx + P.f * float(d @ dx) / z; v = P.cy - P.f * float(d @ cima) / z
        x, y, s = P.projetar_ponto(u, v, z, **cam); return np.array([x, y]), z
    pe = np.asarray(personagem["pe_mundo"], float); h = personagem.get("altura_m", 1.4); centro = pe + [0, 0, h * 0.55]
    c_tela, zc = tela(centro); preset = P.m.get("preset_luz", "tarde_dourada"); noite = bool(P.m.get("noite"))
    # 1) ambiente: anel em volta da silhueta, no cenário já mapeado
    m = (alfa > 0.5).astype(np.uint8)
    anel = cv2.dilate(m, np.ones((41, 41), np.uint8)) - cv2.dilate(m, np.ones((9, 9), np.uint8))
    amb = _lin(np.median(fundo_display[anel > 0], axis=0)) if anel.any() else np.array([0.3, 0.3, 0.3])
    lum = float(0.2126 * amb[0] + 0.7152 * amb[1] + 0.0722 * amb[2]); croma = amb / max(amb.mean(), 1e-6)
    if noite:
        mult = float(np.clip(lum / 0.30, PISO_NOITE, 0.85)); s = 0.35
    elif preset == "crepusculo":
        mult = 0.88; s = 0.3
    else:
        mult = 1.0; s = 0.22
    tinta = np.clip(mult * (1 + s * (croma - 1)), 0.5 * mult, 1.4 * mult)
    # 2) sol/lua → direção na tela (do centro do personagem para a luz)
    sol = np.asarray(P.m.get("sol_dir", (0.3, -0.5, 0.8)), float)
    p2, _ = tela(centro + sol * 2.0); dl = p2 - c_tela; dl /= np.linalg.norm(dl) + 1e-9
    rims = [{"dir": dl, "cor": np.array(COR_RIM.get(preset, (1, 1, 1))), "forca": FORCA_RIM.get(preset, 0.3) * forca}]
    # 3) luzes dos efeitos
    brilhos = []
    for L in luzes or []:
        q = np.asarray(L["pos"], float); pl, _ = tela(q); d = pl - c_tela; d /= np.linalg.norm(d) + 1e-9
        dist = float(np.linalg.norm(q - centro)); I_ = min(FORCA_EFEITO_MAX, L["forca"] / (dist * dist + 0.3 ** 2) * 0.35) * forca
        cor = np.asarray(L["cor"], float) if not isinstance(L["cor"], str) else np.array([int(L["cor"][i:i + 2], 16) / 255 for i in (1, 3, 5)])
        brilhos.append({"dir": d, "cor": cor, "forca": I_})
    return {"tinta": tinta, "rims": rims, "brilhos": brilhos, "centro": c_tela, "altura_px": abs(tela(pe)[0][1] - tela(pe + [0, 0, h])[0][1]),
            "volume": VOLUME.get(preset, 0.10) * forca, "ambiente_lin": amb, "multiplicador": mult}


def aplicar(fig, prm):
    """fig: RGBA (0..1, exibição) no formato que o compositor recebe do skia (`toarray` padrão = cor NÃO pré-multiplicada).
    Retorna o mesmo formato, com o tom aplicado. Alfa intacto."""
    A = fig[..., 3]; dentro = A > 1e-4
    if not dentro.any():
        return fig
    ys, xs = np.nonzero(dentro); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    pad = 24; y0, x0 = max(0, y0 - pad), max(0, x0 - pad); y1, x1 = min(fig.shape[0], y1 + pad), min(fig.shape[1], x1 + pad)
    f = fig[y0:y1, x0:x1]; a = f[..., 3:4]; rgb = np.where(a > 1e-4, f[..., :3], 0)
    lin = _lin(rgb).astype(np.float32)
    H_px = max(prm["altura_px"], 10.0); c = prm["centro"] - [x0, y0]
    yy, xx = np.mgrid[0:f.shape[0], 0:f.shape[1]].astype(np.float32); rel = np.stack([xx - c[0], yy - c[1]], -1) / (H_px * 0.35)
    out = lin * prm["tinta"].astype(np.float32)[None, None, :]
    soma = np.zeros_like(out)
    # Luz somada = albedo × cor da luz × força (como luz de verdade): o traço preto do contorno do rig continua preto,
    # e a camiseta azul recebe brilho azul, não branco. Só no miolo opaco (peso alfa⁴): a borda suavizada do desenho
    # quase não muda (o compositor soma a cor da borda sem ponderar pelo alfa; ver PROPOSTA, seção "achado").
    for rim in prm["rims"]:      # volume + contorno do lado da luz principal
        d = rim["dir"].astype(np.float32); lado = np.clip((rel * d).sum(-1), -1, 1)
        out = out * (1 + prm["volume"] * lado)[..., None]
        soma += _contorno(a[..., 0], d, H_px)[..., None] * (rim["cor"] * rim["forca"] * GANHO_RIM).astype(np.float32) * lin
    for b in prm["brilhos"]:     # luz dos efeitos: difusa do lado voltado + contorno
        d = b["dir"].astype(np.float32); lado = np.clip(0.5 + 0.5 * (rel * d).sum(-1), 0, 1)
        soma += (lado ** 1.5 * 0.5 * b["forca"])[..., None] * b["cor"].astype(np.float32) * lin
        soma += _contorno(a[..., 0], d, H_px)[..., None] * (b["cor"] * b["forca"] * GANHO_RIM).astype(np.float32) * lin
    soma *= (a ** 4)
    lum_soma = soma.max(-1, keepdims=True)
    soma = soma * np.minimum(1.0, MAX_SOMA / np.maximum(lum_soma, 1e-6))
    res = _srgb(out + soma).astype(np.float32)
    nova = fig.copy(); nova[y0:y1, x0:x1, :3] = np.where(a > 1e-4, res, f[..., :3])
    return nova


def _contorno(a, d, H_px):
    """Borda da silhueta do lado da direção d (largura ~1,2 % da altura)."""
    w = max(2.0, 0.012 * H_px)
    M = np.float32([[1, 0, -d[0] * w], [0, 1, -d[1] * w]])
    vizinho = cv2.warpAffine(a, M, (a.shape[1], a.shape[0]), flags=cv2.INTER_LINEAR, borderValue=0)   # alfa do pixel em direção à luz
    e = np.clip(a - vizinho, 0, 1) * (a > 0.99)
    return cv2.GaussianBlur(e, (0, 0), w * 0.35) * (a > 0.99)


def fazer_tom(personagem, luzes=None, forca=1.0, registro=None):
    """Devolve a função para o encaixe `tom_personagem` do compositor: f(fig, fundo_display, P, cam) → fig."""
    def tom(fig, fundo, P, cam):
        prm = parametros(P, cam, fundo, fig[..., 3], personagem, luzes, forca)
        if registro is not None:
            registro.append(prm)
        return aplicar(fig, prm)
    return tom
