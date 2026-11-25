"""Cenografia — COMPOSITOR 2.5D (E0): camadas + grupos de luz + profundidade → quadro final.

Tudo em luz LINEAR até o mapeamento de tons:
1. Reiluminação: cor_camada = Σ_g peso_g · cor_g · passada_g   (grupos "sol", "artificial", "efeito")
2. Névoa por profundidade (perspectiva aérea): mistura com a cor do horizonte conforme a distância real (m).
3. Câmera 2.5D com PARALAXE POR PIXEL: para um deslocamento da câmera (tx, ty, tz em metros, no referencial
   da câmera), cada pixel se move segundo a sua profundidade Z:  u' = (u·Z − f·tx) / (Z − tz).
   Resolvido por remapeamento inverso com 2 iterações de ponto fixo; a profundidade das áreas transparentes é
   preenchida com a do pixel válido mais próximo (sem "rasgos" na borda dos objetos).
4. Composição camada a camada (alfa pré-multiplicado), do céu para a frente; o personagem entra entre as camadas
   "meio" e "perto" (ou onde a receita mandar), no plano de profundidade da âncora.
5. Mapeamento de tons fílmico + sRGB; gradação: sombras roxo-azuladas, altas luzes quentes, brilho (bloom),
   vinheta e grão — alvos do skill (seção 5).
O personagem (Heitor rig v2) é desenhado SEM nenhuma alteração do rig e entra DEPOIS do mapeamento de tons,
para não alterar a paleta oficial; só vinheta e grão globais passam por cima.
"""
import json, math
from pathlib import Path
import numpy as np, cv2
from scipy import ndimage


def _srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def _lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def hexlin(h):
    h = h.lstrip("#"); return _lin(np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)).astype(np.float32)


def filmico(x):
    """Curva fílmica (aproximação ACES de Narkowicz) — comprime altas luzes sem estourar."""
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)


class Placa:
    """Carrega uma placa renderizada (pasta com manifest.json e uma subpasta por camada)."""

    def __init__(self, pasta):
        from .render import ler_exr
        self.pasta = Path(pasta); self.m = json.loads((self.pasta / "manifest.json").read_text())
        self.W, self.H = self.m["resolucao"]; I = self.m["intrinsecos"]
        self.f, self.cx, self.cy = I["f_px"], I["cx"], I["cy"]
        self.grupos = self.m["grupos_luz"]; self.camadas = {}
        for c in self.m["camadas"]:
            d = self.pasta / c
            luz = {g: ler_exr(d / f"luz_{g}.exr")[..., :3] for g in self.grupos}
            alfa = ler_exr(d / "alfa.exr")[..., 0] if c != "ceu" else np.ones((self.H, self.W), np.float32)
            prof = ler_exr(d / "profundidade.exr")[..., 0].astype(np.float32)
            prof = np.where(np.isfinite(prof) & (prof < 5e3), prof, 5e3).astype(np.float32)
            valido = alfa > 0.5
            if c != "ceu" and valido.any():   # profundidade das áreas vazias = a do pixel válido mais próximo
                idx = ndimage.distance_transform_edt(~valido, return_distances=False, return_indices=True)
                prof = prof[idx[0], idx[1]]
            self.camadas[c] = {"luz": luz, "alfa": alfa, "prof": prof,
                               "z_med": float(np.median(prof[valido])) if (c != "ceu" and valido.any()) else 5e3}
        uu, vv = np.meshgrid(np.arange(self.W, dtype=np.float32), np.arange(self.H, dtype=np.float32))
        self.u, self.v = uu - self.cx, vv - self.cy

    # ---------------------------------------------------------------- iluminação
    def iluminar(self, camada, pesos):
        """pesos: {grupo: (intensidade, cor_hex_ou_None)} → RGB linear pré-multiplicado."""
        L = self.camadas[camada]["luz"]; out = np.zeros_like(L[self.grupos[0]])
        for g in self.grupos:
            w, cor = pesos.get(g, (0.0, None)) if isinstance(pesos.get(g), (tuple, list)) else (pesos.get(g, 0.0), None)
            if w:
                out += L[g] * (w * (hexlin(cor) if cor else 1.0))
        return out

    # ---------------------------------------------------------------- câmera 2.5D
    def mapa_paralaxe(self, camada, tx=0.0, ty=0.0, tz=0.0, zoom=1.0):
        """Mapa inverso (destino → origem) para o deslocamento de câmera dado. Retorna (map_x, map_y) em px."""
        Z = self.camadas[camada]["prof"]
        up, vp = self.u / zoom, self.v / zoom              # zoom (lente) atua no destino
        if camada == "ceu" or (tx == 0 and ty == 0 and tz == 0):
            return (up + self.cx).astype(np.float32), (vp + self.cy).astype(np.float32)
        Zs = Z
        for _ in range(2):
            u = (up * (Zs - tz) + self.f * tx) / Zs
            v = (vp * (Zs - tz) - self.f * ty) / Zs
            Zs = cv2.remap(Z, (u + self.cx).astype(np.float32), (v + self.cy).astype(np.float32), cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE)
        u = (up * (Zs - tz) + self.f * tx) / Zs; v = (vp * (Zs - tz) - self.f * ty) / Zs
        return (u + self.cx).astype(np.float32), (v + self.cy).astype(np.float32)

    def projetar_ponto(self, x, y, z, tx=0.0, ty=0.0, tz=0.0, zoom=1.0):
        """Ponto da placa (px) de profundidade z → posição e escala após o movimento de câmera."""
        u, v = x - self.cx, y - self.cy
        s = z / (z - tz)
        return (self.cx + zoom * (u * z - self.f * tx) / (z - tz), self.cy + zoom * (v * z + self.f * ty) / (z - tz), s * zoom)

    # ---------------------------------------------------------------- quadro
    def _pilha(self, cams, pesos, cam, nevoa):
        """Compõe (linear, pré-multiplicado) as camadas dadas, do fundo para a frente. Retorna (rgb, alfa)."""
        acc = np.zeros((self.H, self.W, 3), np.float32); alfa = np.zeros((self.H, self.W), np.float32)
        for c in cams:
            L = self.iluminar(c, pesos); a = self.camadas[c]["alfa"]
            if nevoa and c != "ceu":
                Z = self.camadas[c]["prof"]; h = 1 - np.exp(-nevoa["densidade"] * np.maximum(0, Z - nevoa.get("inicio_m", 0)))
                L = L * (1 - h[..., None]) + hexlin(nevoa["cor"]) * nevoa.get("forca", 1.0) * (h * a)[..., None]
            mx, my = self.mapa_paralaxe(c, **cam)
            L = cv2.remap(L, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            if c != "ceu":
                a = cv2.remap(a, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            acc = L + acc * (1 - a[..., None]); alfa = a + alfa * (1 - a)
        return acc, alfa

    def compor(self, pesos=None, cam=None, nevoa=None, personagem=None, plano_personagem="meio", grade=None, semente_grao=0,
               saida=(1080, 1920), camadas=None):
        """Retorna o quadro final RGB uint8 (recorte central do tamanho 'saida').
        personagem: função(canvas_skia, projecao) que desenha em RGBA na resolução da placa;
        projecao(x, y, z) → (x', y', escala) aplica o mesmo movimento de câmera ao plano do personagem."""
        pesos = pesos or self.m["pesos_padrao"]; cam = cam or {}; grade = grade or {}
        exp = 2.0 ** grade.get("exposicao", 0.0)
        ordem = [c for c in self.m["camadas"] if camadas is None or c in camadas]
        if personagem is None:
            acc, _ = self._pilha(ordem, pesos, cam, nevoa)
            disp = self._tom(acc * exp, grade)
        else:
            disp = self._com_personagem(pesos, cam, nevoa, personagem, plano_personagem, grade, exp, ordem)
        disp = self._final(disp, grade, semente_grao)
        W0, H0 = saida; x0 = (self.W - W0) // 2; y0 = (self.H - H0) // 2
        return disp[y0:y0 + H0, x0:x0 + W0]

    def _tom(self, lin, grade):
        # bloom: altas luzes borradas somadas (antes da curva)
        if grade.get("bloom", 0.0) > 0:
            br = np.maximum(lin - grade.get("bloom_limiar", 1.0), 0)
            br = cv2.GaussianBlur(br, (0, 0), self.H / 90)
            lin = lin + grade["bloom"] * br
        x = filmico(lin)
        # gradação: sombras roxo-azuladas, altas luzes quentes, saturação
        lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
        x = x + grade.get("sombra_tinta", 0.0) * (1 - lum) ** 3 * np.array([0.55, 0.35, 1.0], np.float32)
        x = x * (1 + grade.get("luz_quente", 0.0) * lum * np.array([0.06, 0.02, -0.06], np.float32))
        sat = grade.get("saturacao", 1.0)
        x = lum + (x - lum) * sat
        return np.clip(_srgb(np.clip(x, 0, 1)), 0, 1).astype(np.float32)

    def _com_personagem(self, pesos, cam, nevoa, personagem, plano, grade, exp, ordem):
        """Camadas até 'plano' (mapeadas) + personagem (sRGB, paleta intacta) + camadas da frente (mapeadas)."""
        import skia
        todas = self.m["camadas"]; i = todas.index(plano)
        fundo, _ = self._pilha([c for c in todas[:i + 1] if c in ordem], pesos, cam, nevoa)
        frente, a_fr = self._pilha([c for c in todas[i + 1:] if c in ordem], pesos, cam, nevoa)
        d = self._tom(fundo * exp, grade)
        s = skia.Surface(self.W, self.H); cv = s.getCanvas(); cv.clear(0)
        personagem(cv, lambda x, y, z: self.projetar_ponto(x, y, z, **cam))
        fig = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0
        d = fig[..., :3] + d * (1 - fig[..., 3:4])                          # skia: RGBA pré-multiplicado
        if (a_fr > 0).any():
            d_fr = self._tom(frente * exp / np.maximum(a_fr[..., None], 1e-4), grade)
            d = d_fr * a_fr[..., None] + d * (1 - a_fr[..., None])
        return d

    def _final(self, disp, grade, semente):
        H, W = disp.shape[:2]
        if grade.get("vinheta", 0.0) > 0:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
            disp = disp * (1 - grade["vinheta"] * np.clip(r, 0, 1) ** 2.2)[..., None]
        if grade.get("grao", 0.0) > 0:
            rng = np.random.default_rng(semente)
            g = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
            g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
            disp = disp + grade["grao"] * g[..., None]
        return (np.clip(disp, 0, 1) * 255 + 0.5).astype(np.uint8)
