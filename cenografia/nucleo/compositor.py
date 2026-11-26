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


def cor_lin(c):
    """Cor como hex ('#rrggbb') ou RGB linear (3 valores) → array linear."""
    return hexlin(c) if isinstance(c, str) else np.asarray(c, np.float32)


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
            alb = d / "albedo.exr"
            self.camadas[c] = {"luz": luz, "alfa": alfa, "prof": prof,
                               "albedo": ler_exr(alb)[..., :3] if (c != "ceu" and alb.exists()) else None,   # E7 (placas antigas: None)
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
            L = L * (1 - h[..., None]) + cor_lin(nevoa["cor"]) * nevoa.get("forca", 1.0) * (h * a)[..., None]
        if len(cache) > 3 * len(self.m["camadas"]):
            cache.clear()
        cache[chave] = L
        return L

    # ---------------------------------------------------------------- E7: luz 2D dos efeitos
    def geometria_camada(self, c):
        """Posição no mundo (m) e normal de cada pixel da camada, a partir da profundidade e da câmera (cache)."""
        g = self.__dict__.setdefault("_cache_geo", {})
        if c not in g:
            I = self.m["intrinsecos"]; Z = self.camadas[c]["prof"]
            pos, dr, cima, dx = (np.asarray(I[k], np.float32) for k in ("pos", "dir", "cima", "dir_x"))
            raio = dr[None, None, :] + (self.u / self.f)[..., None] * dx[None, None, :] - (self.v / self.f)[..., None] * cima[None, None, :]
            X = pos[None, None, :] + raio * Z[..., None]
            gx = np.gradient(X, axis=1); gy = np.gradient(X, axis=0)
            n = np.cross(gy, gx); n /= np.linalg.norm(n, axis=2, keepdims=True) + 1e-9
            vira = (n * (pos[None, None, :] - X)).sum(2) < 0          # normal voltada para a câmera
            n[vira] *= -1
            g[c] = (X.astype(np.float32), n.astype(np.float32))
        return g[c]

    def luz_extra(self, c, luzes):
        """Luz de pontos (efeitos) sobre a camada: albedo × Σ forca·cor·max(0, n·l)/(d² + raio²). Linear. Sem sombras."""
        alb = self.camadas[c].get("albedo")
        if not luzes or alb is None:
            return None
        X, n = self.geometria_camada(c); E = np.zeros_like(X)
        for L in luzes:
            d = np.asarray(L["pos"], np.float32)[None, None, :] - X; d2 = (d * d).sum(2)
            lam = np.maximum(0.0, (n * d).sum(2) / np.sqrt(d2 + 1e-9)) * L.get("difusa", 1.0) + (1 - L.get("difusa", 1.0))
            E += (L["forca"] * lam / (d2 + L.get("raio", 0.3) ** 2))[..., None] * cor_lin(L.get("cor", (1, 1, 1)))
        return alb * E

    def _pilha(self, cams, pesos, cam, nevoa, oclusao_ate_m=None, ceu_extra=None, luzes=None, frontal=False):
        """Compõe (linear, pré-multiplicado) as camadas dadas, do fundo para a frente. Retorna (rgb, alfa, oclusao):
        oclusao = cobertura (0–1) do que está MAIS PERTO da câmera que 'oclusao_ate_m' (profundidade após o movimento),
        usada para o teste de profundidade do personagem."""
        acc = np.zeros((self.H, self.W, 3), np.float32); alfa = np.zeros((self.H, self.W), np.float32)
        livre = np.ones((self.H, self.W), np.float32)
        zf = np.full((self.H, self.W), 5e3, np.float32) if frontal else None
        for c in cams:
            L = self._iluminada(c, pesos, nevoa); a = self.camadas[c]["alfa"]
            if luzes and c != "ceu":
                ex = self.luz_extra(c, luzes)
                if ex is not None:
                    if nevoa:
                        Z = self.camadas[c]["prof"]; ex = ex * np.exp(-nevoa["densidade"] * np.maximum(0, Z - nevoa.get("inicio_m", 0)))[..., None]
                    L = L + ex * a[..., None]
            mx, my = self.mapa_paralaxe(c, **cam)
            L = cv2.remap(L, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            if c == "ceu" and ceu_extra is not None:      # nuvens, lua, estrelas: entram no céu, atrás de tudo
                L = ceu_extra(L)
            if c != "ceu":
                a = cv2.remap(a, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
                if oclusao_ate_m is not None or frontal:
                    Z = cv2.remap(self.camadas[c]["prof"], mx, my, cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE) - cam.get("tz", 0.0)
                    if oclusao_ate_m is not None:
                        livre *= 1 - a * (Z < oclusao_ate_m)
                    if frontal:
                        zf = np.where(a > 0.5, np.minimum(zf, Z), zf)
            acc = L + acc * (1 - a[..., None]); alfa = a + alfa * (1 - a)
        if frontal:
            self.ultima_prof_frontal = zf
        return acc, alfa, 1 - livre

    def compor(self, pesos=None, cam=None, nevoa=None, personagem=None, profundidade_personagem=None, grade=None, semente_grao=0,
               saida=(1080, 1920), camadas=None, espessura_m=0.25, ceu_extra=None, frente_extra=None, efeitos=None, deslocamento_px=(0, 0),
               tom_personagem=None):
        """Retorna o quadro final RGB uint8 (recorte central do tamanho 'saida').
        personagem: função(canvas_skia, projecao) que desenha em RGBA na resolução da placa;
        projecao(x, y, z) → (x', y', escala) aplica o mesmo movimento de câmera ao plano do personagem.
        profundidade_personagem (m, ao longo do eixo da câmera): TESTE DE PROFUNDIDADE por pixel — o personagem só é
        coberto pelo que está mais perto da câmera que ele (menos 'espessura_m', para o chão logo à frente dos pés)."""
        pesos = pesos or self.m["pesos_padrao"]; cam = cam or {}; grade = grade or {}
        exp = 2.0 ** grade.get("exposicao", 0.0)
        ordem = [c for c in self.m["camadas"] if camadas is None or c in camadas]
        if efeitos is not None:                             # E7: núcleo de efeitos (o caminho sem efeitos não muda)
            return self._com_efeitos(pesos, cam, nevoa, personagem, profundidade_personagem, grade, exp, ordem, espessura_m,
                                     ceu_extra, frente_extra, efeitos, semente_grao, saida, deslocamento_px, tom_personagem)
        if personagem is None:
            acc, _, _ = self._pilha(ordem, pesos, cam, nevoa, ceu_extra=ceu_extra)
            disp = self._tom(acc * exp, grade)
        else:
            disp = self._com_personagem(pesos, cam, nevoa, personagem, profundidade_personagem, grade, exp, ordem, espessura_m, ceu_extra,
                                        tom_personagem)
        if frente_extra is not None:                       # chuva etc.: na frente de TUDO, inclusive do personagem
            disp = frente_extra(disp)
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

    def _com_personagem(self, pesos, cam, nevoa, personagem, D, grade, exp, ordem, espessura_m, ceu_extra=None, tom_personagem=None):
        """Cena inteira (mapeada) + personagem (sRGB, paleta intacta) com teste de profundidade por pixel."""
        import skia
        if D is None:
            raise ValueError("profundidade_personagem é obrigatória (teste de profundidade)")
        acc, _, occ = self._pilha(ordem, pesos, cam, nevoa, oclusao_ate_m=D - cam.get("tz", 0.0) - espessura_m, ceu_extra=ceu_extra)
        d = self._tom(acc * exp, grade)
        s = skia.Surface(self.W, self.H); cv = s.getCanvas(); cv.clear(0)
        personagem(cv, lambda x, y, z: self.projetar_ponto(x, y, z, **cam))
        fig = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0
        if tom_personagem is not None:          # extensão X1 (tom de luz no personagem) — só com aprovação; None = sem mudança
            fig = tom_personagem(fig, d, self, cam)
        vis = (1 - occ)[..., None]                                   # skia: RGBA pré-multiplicado
        self.ultima_oclusao = occ
        return fig[..., :3] * vis + d * (1 - fig[..., 3:4] * vis)

    def _com_efeitos(self, pesos, cam, nevoa, personagem, D, grade, exp, ordem, espessura_m, ceu_extra, frente_extra, ef, semente,
                     saida, desloc, tom_personagem=None):
        """Ordem: cenário (+ luz dos efeitos, antes do mapeamento de tons) → marcas no chão → efeitos ATRÁS do
        personagem → personagem → efeitos NA FRENTE → distorção → quadro de impacto (se houver) → vinheta e grão →
        recorte (deslocado pela tremida). Cada camada de efeito tem profundidade por pixel: o que está mais perto da
        câmera no cenário a cobre."""
        import skia
        luzes = ef.luzes(self, cam)
        oc = (D - cam.get("tz", 0.0) - espessura_m) if (personagem is not None and D is not None) else None
        acc, _, occ = self._pilha(ordem, pesos, cam, nevoa, oclusao_ate_m=oc, ceu_extra=ceu_extra, luzes=luzes, frontal=True)
        zf = self.ultima_prof_frontal; d = self._tom(acc * exp, grade)

        def aplicar(d, camada, tol=0.15):
            if camada is None:
                return d
            vis = (camada["z"] <= zf + tol).astype(np.float32)[..., None]
            if camada.get("rgba") is not None:
                d = camada["rgba"][..., :3] * vis + d * (1 - camada["rgba"][..., 3:4] * vis)
            if camada.get("add") is not None:
                d = d + camada["add"] * vis
            return d
        d = aplicar(d, ef.desenhar(self, cam, "chao"), tol=0.35)
        d = aplicar(d, ef.desenhar(self, cam, "atras"))
        self.ultimo_alfa_personagem = None
        if personagem is not None:
            s = skia.Surface(self.W, self.H); cv = s.getCanvas(); cv.clear(0)
            personagem(cv, lambda x, y, z: self.projetar_ponto(x, y, z, **cam))
            fig = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255.0
            if tom_personagem is not None:      # extensão X1 (tom de luz no personagem) — só com aprovação; None = sem mudança
                fig = tom_personagem(fig, d, self, cam)
            vis = (1 - occ)[..., None]; self.ultima_oclusao = occ
            d = fig[..., :3] * vis + d * (1 - fig[..., 3:4] * vis); self.ultimo_alfa_personagem = fig[..., 3] * vis[..., 0]
        d = aplicar(d, ef.desenhar(self, cam, "frente"))
        dist = ef.distorcao(self, cam)
        if dist is not None:
            dx, dy = dist
            d = cv2.remap(d.astype(np.float32), (self.u + self.cx + dx).astype(np.float32), (self.v + self.cy + dy).astype(np.float32),
                          cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        imp = ef.impacto(self, self.ultimo_alfa_personagem)
        if imp is not None:
            d = imp
        d = np.clip(d, 0, 1)
        if frente_extra is not None:
            d = frente_extra(d)
        d = self._final(d, grade, semente)
        W0, H0 = saida; ox, oy = desloc
        x0 = int(np.clip((self.W - W0) // 2 + ox, 0, self.W - W0)); y0 = int(np.clip((self.H - H0) // 2 + oy, 0, self.H - H0))
        return d[y0:y0 + H0, x0:x0 + W0]

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
