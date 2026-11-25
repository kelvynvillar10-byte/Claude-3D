"""Cenografia — COMPOSITOR 2.5D (E0): camadas + grupos de luz + profundidade → quadro final.

Tudo em luz LINEAR até o mapeamento de tons:
1. Reiluminação: cor_camada = Σ_g peso_g · cor_g · passada_g   (grupos "sol", "artificial", "efeito")
2. Névoa por profundidade (perspectiva aérea): mistura com a cor do horizonte conforme a distância real (m).
3. Câmera 2.5D com PARALAXE POR PIXEL: para um deslocamento da câmera (tx, ty, tz em metros, no referencial
   da câmera), cada pixel se move segundo a sua profundidade Z:  u' = (u·Z − f·tx) / (Z − tz).
   Resolvido por remapeamento inverso com 4 iterações de ponto fixo; a profundidade das áreas transparentes é
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
        """pesos: {grupo: intensidade | (intensidade, cor)}; cor = hex, RGB linear (3 valores) ou None → RGB linear pré-multiplicado."""
        L = self.camadas[camada]["luz"]; out = np.zeros_like(L[self.grupos[0]])
        for g in self.grupos:
            w, cor = pesos.get(g, (0.0, None)) if isinstance(pesos.get(g), (tuple, list)) else (pesos.get(g, 0.0), None)
            if w:
                tinta = 1.0 if cor is None else (hexlin(cor) if isinstance(cor, str) else np.asarray(cor, np.float32))
                out += L[g] * (w * tinta)
        return out

    # ---------------------------------------------------------------- câmera 2.5D
    def mapa_paralaxe(self, camada, tx=0.0, ty=0.0, tz=0.0, zoom=1.0):
        """Mapa inverso (destino → origem) para o deslocamento de câmera dado. Retorna (map_x, map_y) em px."""
        Z = self.camadas[camada]["prof"]
        up, vp = self.u / zoom, self.v / zoom              # zoom (lente) atua no destino
        if camada == "ceu" or (tx == 0 and ty == 0 and tz == 0):
            return (up + self.cx).astype(np.float32), (vp + self.cy).astype(np.float32)
        Zs = Z
        for _ in range(getattr(self, "iteracoes_paralaxe", 4)):   # 4: erro ≤ 0,6 px no chão perto (medido na E0)
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
    def _iluminada(self, c, pesos, nevoa):
        """Camada reiluminada + névoa, guardada em cache enquanto pesos e névoa não mudam (ex.: só a câmera anda)."""
        chave = (c, json.dumps(pesos, sort_keys=True, default=str), json.dumps(nevoa, sort_keys=True, default=str))
        cache = self.__dict__.setdefault("_cache_luz", {})
        if chave in cache:
            return cache[chave]
        L = self.iluminar(c, pesos); a = self.camadas[c]["alfa"]
        if nevoa and c != "ceu":
            Z = self.camadas[c]["prof"]; h = 1 - np.exp(-nevoa["densidade"] * np.maximum(0, Z - nevoa.get("inicio_m", 0)))
            L = L * (1 - h[..., None]) + hexlin(nevoa["cor"]) * nevoa.get("forca", 1.0) * (h * a)[..., None]
        if len(cache) > 3 * len(self.m["camadas"]):
            cache.clear()
        cache[chave] = L
        return L

    def _pilha(self, cams, pesos, cam, nevoa, oclusao_ate_m=None):
        """Compõe (linear, pré-multiplicado) as camadas dadas, do fundo para a frente. Retorna (rgb, alfa, oclusao):
        oclusao = cobertura (0–1) do que está MAIS PERTO da câmera que 'oclusao_ate_m' (profundidade após o movimento),
        usada para o teste de profundidade do personagem."""
        acc = np.zeros((self.H, self.W, 3), np.float32); alfa = np.zeros((self.H, self.W), np.float32)
        livre = np.ones((self.H, self.W), np.float32)
        for c in cams:
            L = self._iluminada(c, pesos, nevoa); a = self.camadas[c]["alfa"]
            mx, my = self.mapa_paralaxe(c, **cam)
            L = cv2.remap(L, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            if c != "ceu":
                a = cv2.remap(a, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
                if oclusao_ate_m is not None:
                    Z = cv2.remap(self.camadas[c]["prof"], mx, my, cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE) - cam.get("tz", 0.0)
                    livre *= 1 - a * (Z < oclusao_ate_m)
            acc = L + acc * (1 - a[..., None]); alfa = a + alfa * (1 - a)
        return acc, alfa, 1 - livre

    def compor(self, pesos=None, cam=None, nevoa=None, personagem=None, profundidade_personagem=None, grade=None, semente_grao=0,
               saida=(1080, 1920), camadas=None, espessura_m=0.25):
        """Retorna o quadro final RGB uint8 (recorte central do tamanho 'saida').
        personagem: função(canvas_skia, projecao) que desenha em RGBA na resolução da placa;
        projecao(x, y, z) → (x', y', escala) aplica o mesmo movimento de câmera ao plano do personagem.
        profundidade_personagem (m, ao longo do eixo da câmera): TESTE DE PROFUNDIDADE por pixel — o personagem só é
        coberto pelo que está mais perto da câmera que ele (menos 'espessura_m', para o chão logo à frente dos pés)."""
        pesos = pesos or self.m["pesos_padrao"]; cam = cam or {}; grade = grade or {}
        exp = 2.0 ** grade.get("exposicao", 0.0)
        ordem = [c for c in self.m["camadas"] if camadas is None or c in camadas]
        if personagem is None:
            acc, _, _ = self._pilha(ordem, pesos, cam, nevoa)
            disp = self._tom(acc * exp, grade)
        else:
            disp = self._com_personagem(pesos, cam, nevoa, personagem, profundidade_personagem, grade, exp, ordem, espessura_m)
        disp = self._final(disp, grade, semente_grao)
        W0, H0 = saida; x0 = (self.W - W0) // 2; y0 = (self.H - H0) // 2
        return disp[y0:y0 + H0, x0:x0 + W0]

    def _tom(self, lin, grade):
        # bloom: altas luzes borradas somadas (antes da curva)
        if grade.get("bloom", 0.0) > 0:
            br = np.maximum(lin - grade.get("bloom_limiar", 1.0), 0)
            pq = cv2.resize(br, (br.shape[1] // 4, br.shape[0] // 4), interpolation=cv2.INTER_AREA)   # borrão em 1/4 da resolução
            pq = cv2.GaussianBlur(pq, (0, 0), self.H / 360)
            lin = lin + grade["bloom"] * cv2.resize(pq, (br.shape[1], br.shape[0]), interpolation=cv2.INTER_LINEAR)
        x = filmico(lin)
        # gradação: sombras roxo-azuladas, altas luzes quentes, saturação
        lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
        x = x + grade.get("sombra_tinta", 0.0) * (1 - lum) ** 3 * np.array([0.55, 0.35, 1.0], np.float32)
        x = x * (1 + grade.get("luz_quente", 0.0) * lum * np.array([0.06, 0.02, -0.06], np.float32))
        sat = grade.get("saturacao", 1.0)
        x = lum + (x - lum) * sat
        return np.clip(_srgb(np.clip(x, 0, 1)), 0, 1).astype(np.float32)

    def _com_personagem(self, pesos, cam, nevoa, personagem, D, grade, exp, ordem, espessura_m):
        """Cena inteira (mapeada) + personagem (sRGB, paleta intacta) com teste de profundidade por pixel."""
        import skia
        if D is None:
            raise ValueError("profundidade_personagem é obrigatória (teste de profundidade)")
        acc, _, occ = self._pilha(ordem, pesos, cam, nevoa, oclusao_ate_m=D - cam.get("tz", 0.0) - espessura_m)
        d = self._tom(acc * exp, grade)
        s = skia.Surface(self.W, self.H); cv = s.getCanvas(); cv.clear(0)
        personagem(cv, lambda x, y, z: self.projetar_ponto(x, y, z, **cam))
        fig = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0
        vis = (1 - occ)[..., None]                                   # skia: RGBA pré-multiplicado
        self.ultima_oclusao = occ
        return fig[..., :3] * vis + d * (1 - fig[..., 3:4] * vis)

    def _final(self, disp, grade, semente):
        H, W = disp.shape[:2]
        if grade.get("vinheta", 0.0) > 0:
            chave = (H, W, grade["vinheta"]); vc = self.__dict__.setdefault("_cache_vinheta", {})
            if chave not in vc:
                yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
                vc[chave] = (1 - grade["vinheta"] * np.clip(r, 0, 1) ** 2.2)[..., None].astype(np.float32)
            disp = disp * vc[chave]
        if grade.get("grao", 0.0) > 0:
            rng = np.random.default_rng(semente)
            g = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
            g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
            disp = disp + grade["grao"] * g[..., None]
        return (np.clip(disp, 0, 1) * 255 + 0.5).astype(np.uint8)
