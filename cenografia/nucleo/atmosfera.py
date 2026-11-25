"""Cenografia — ATMOSFERA (E1): clima sobre uma placa, no compositor.

Horário = placa (o sol tem posição física; ver luz.PRESETS). Clima = camada de compositor sobre a placa:
| clima    | o que muda                                                                                   |
|----------|----------------------------------------------------------------------------------------------|
| limpo    | poucas nuvens (cumulus) iluminadas pelo sol                                                   |
| nublado  | cobertura alta, sol quase apagado (luz difusa), céu acinzentado, mais névoa                   |
| neblina  | névoa densa e clara pela profundidade real, contraste baixo                                    |
| chuva    | nublado + riscos de chuva na frente de tudo + PLACA com piso molhado (umidade nos materiais) |
Noite: estrelas e lua com fase entram no céu; nuvens escuras iluminadas pela lua.
Uso: A = Atmosfera(placa, "nublado", semente); placa.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(g),
     ceu_extra=A.ceu(t), frente_extra=A.frente(t), ...)
"""
import math
import numpy as np, cv2
from . import ceu2d as C2
from .compositor import hexlin

CLIMAS = {
    "limpo":   dict(cobertura=0.30, sol=1.0, ceu=1.0, ceu_cinza=0.0, nevoa_mult=1.0, chuva=0.0, saturacao=1.0, contraste=1.0),
    "nublado": dict(cobertura=0.86, sol=0.12, ceu=0.8, ceu_cinza=0.65, nevoa_mult=2.0, chuva=0.0, saturacao=0.82, contraste=0.9),
    "neblina": dict(cobertura=0.55, sol=0.45, ceu=0.95, ceu_cinza=0.5, nevoa_mult=9.0, chuva=0.0, saturacao=0.75, contraste=0.8),
    "chuva":   dict(cobertura=0.95, sol=0.06, ceu=0.62, ceu_cinza=0.8, nevoa_mult=3.5, chuva=1.0, saturacao=0.8, contraste=0.92),
}
NEVOA_BASE = {"manha": ("#d6dbe0", 0.006), "meio_dia": ("#dfe6ee", 0.004), "tarde_dourada": ("#d9c2a6", 0.006),
              "crepusculo": ("#b9859a", 0.007), "noite": ("#1c2442", 0.010)}


class Atmosfera:
    def __init__(self, placa, clima="limpo", semente=0, deriva_px_s=(5.0, 10.0, 18.0)):
        self.P = placa; self.c = CLIMAS[clima]; self.clima = clima; self.semente = semente
        self.preset = placa.m.get("preset_luz", "tarde_dourada"); self.noite = placa.m.get("noite", False)
        W, H = placa.W, placa.H; I = placa.m["intrinsecos"]
        # linha do horizonte na placa (a câmera pode estar levemente inclinada)
        pitch = math.asin(max(-1.0, min(1.0, I["dir"][2]))); self.y_horiz = I["cy"] + I["f_px"] * math.tan(pitch)
        yy = np.arange(H, dtype=np.float32)[:, None]
        # nuvens só acima do horizonte: some suavemente perto dele (névoa do horizonte) e cresce para o alto
        sobe = np.clip((self.y_horiz - 0.04 * H - yy) / (0.30 * H), 0, 1); sobe = sobe * sobe * (3 - 2 * sobe)
        self.camadas = []
        for k, (esc, ach, vel) in enumerate(((900, 3.0, deriva_px_s[0]), (620, 2.4, deriva_px_s[1]), (420, 1.9, deriva_px_s[2]))):
            cob = min(0.97, self.c["cobertura"] * (0.75 + 0.15 * k))
            d = C2.campo_nuvens(H, W, semente * 31 + k, escala_px=esc, cobertura=cob, achatamento=ach)
            self.camadas.append(((d * sobe).astype(np.float32), vel))
        self.sol_tela = C2.direcao_sol_na_tela(I, placa.m.get("sol_dir", [0.6, 0.6, 0.3]))
        # nível de luz do céu (para as nuvens ficarem no mesmo "brilho" do céu renderizado)
        # GANHO DO CÉU: o céu físico sai perto do teto do mapeamento de tons (lavado, sem cor). Ele é escurecido
        # ~0,9 stop antes das nuvens — o céu ganha cor e as nuvens ganham contraste. Só o céu visto pela câmera muda
        # (a luz que ele joga na cena continua a do render).
        self.ganho_ceu = 0.55 if not placa.m.get("noite") else 1.0
        L = placa.iluminar("ceu", placa.m["pesos_padrao"]) * self.ganho_ceu; topo = L[: int(self.y_horiz * 0.8)]
        self.ceu_medio = topo.reshape(-1, 3).mean(0).astype(np.float32) if topo.size else np.full(3, 0.5, np.float32)
        lum = float(self.ceu_medio @ np.array([0.2126, 0.7152, 0.0722], np.float32))
        sol_cor = hexlin({"manha": "#ffe2bf", "meio_dia": "#fff4e6", "tarde_dourada": "#ffc98a", "crepusculo": "#ff8a55", "noite": "#9fb4ff"}[self.preset])
        roxo = np.array([0.62, 0.58, 0.85], np.float32)                     # sombras roxo-azuladas (alvo do skill)
        cinza = self.c["ceu_cinza"]; sol = self.c["sol"]
        # O céu já está perto do teto do mapeamento de tons: a nuvem só "lê" se o miolo for BEM mais escuro que o céu
        # (≈ 30–45 % dele) e o lado do sol um pouco mais claro e quente.
        self.cor_luz = (self.ceu_medio * 0.5 + sol_cor * lum * (1.1 if not self.noite else 0.5) * (0.4 + 0.6 * sol)).astype(np.float32)
        sombra_ceu = (self.ceu_medio * 0.42 + roxo * lum * 0.18)
        self.cor_sombra = (sombra_ceu * (1 - cinza) + np.full(3, lum * 0.42, np.float32) * cinza).astype(np.float32)
        if self.noite:
            self.cor_sombra = (self.ceu_medio * 0.55).astype(np.float32)
        self.cor_borda = (sol_cor * lum * 0.9 * sol * (1 - cinza)).astype(np.float32)
        if cinza > 0.3:   # encoberto: o "teto" de nuvens é cinza e mais escuro que o céu; o lado iluminado, cinza-claro
            self.cor_luz = (np.full(3, lum * 0.78, np.float32) * cinza + self.cor_luz * (1 - cinza)).astype(np.float32)
        if self.noite:
            self.estrelas_cache = None

    # ------------------------------------------------------------------ pesos, névoa, gradação
    def pesos(self, base=None):
        b = dict(base or self.P.m["pesos_padrao"])
        b["sol"] = (b.get("sol", 1.0) if not isinstance(b.get("sol"), tuple) else b["sol"][0]) * self.c["sol"]
        cinza = self.c["ceu_cinza"]
        cor_ceu = tuple(float(x) for x in (np.ones(3) * (1 - cinza) + np.array([0.82, 0.86, 0.95]) * cinza))
        b["ceu"] = ((b.get("ceu", 1.0) if not isinstance(b.get("ceu"), tuple) else b["ceu"][0]) * self.c["ceu"], cor_ceu)
        return b

    def nevoa(self):
        cor, dens = NEVOA_BASE.get(self.preset, ("#d9c2a6", 0.006))
        if self.clima in ("nublado", "chuva", "neblina") and not self.noite:
            cor = "#c9ced6" if self.clima != "neblina" else "#e6e8ea"
        return {"cor": cor, "densidade": dens * self.c["nevoa_mult"], "forca": 1.0 if not self.noite else 0.8}

    def grade(self, g):
        g = dict(g); g["saturacao"] = g.get("saturacao", 1.0) * self.c["saturacao"]
        if self.c["contraste"] < 1:
            g["exposicao"] = g.get("exposicao", 0.0) + 0.15 * (1 - self.c["contraste"]) * 5
        return g

    # ------------------------------------------------------------------ céu (nuvens, lua, estrelas)
    def ceu(self, t):
        def aplicar(L):
            H, W = L.shape[:2]; out = L * self.ganho_ceu
            if self.noite:
                if self.estrelas_cache is None or abs(self.estrelas_cache[0] - t) > 1e-6:
                    est = C2.estrelas(H, W, self.semente + 7, t=t) * (1 - min(1.0, self.c["cobertura"] * 1.1))
                    acima = (np.arange(H, dtype=np.float32)[:, None, None] < self.y_horiz - 40).astype(np.float32)
                    self.estrelas_cache = (t, est * acima * 0.06)
                out = out + self.estrelas_cache[1]
                lr, la = C2.lua(H, W, W * 0.72, self.y_horiz * 0.28, H * 0.028, fase=0.78, semente=self.semente)
                vis = 1 - 0.85 * self.c["cobertura"]
                out = out * (1 - la[..., None] * vis) + lr * 0.25 * vis
            for d, vel in self.camadas:
                M = np.float32([[1, 0, vel * t], [0, 1, 0]])
                dd = cv2.warpAffine(d, M, (W, H), borderMode=cv2.BORDER_REFLECT)
                cor, a = C2.iluminar_nuvens(dd, self.sol_tela, self.cor_luz, self.cor_sombra, self.cor_borda)
                a = a[..., None] * 0.96
                out = out * (1 - a) + cor * a
            # névoa também no CÉU (neblina, chuva, nublado): sem isso o céu fica mais escuro que os prédios enevoados
            k = {"limpo": 0.0, "nublado": 0.25, "neblina": 0.8, "chuva": 0.45}[self.clima]
            if k > 0:
                nv = self.nevoa(); cor_n = hexlin(nv["cor"]) * float(self.ceu_medio @ np.array([0.2126, 0.7152, 0.0722], np.float32)) * 1.05
                out = out * (1 - k) + cor_n * k
            return out
        return aplicar

    # ------------------------------------------------------------------ chuva (na frente de tudo)
    def frente(self, t):
        if self.c["chuva"] <= 0:
            return None
        P = self.P

        def aplicar(disp):
            H, W = disp.shape[:2]
            rgb, a = C2.chuva(H, W, self.semente + 99, t, self.c["chuva"])
            return np.clip(disp * (1 - a[..., None] * 0.25) + rgb * 0.9, 0, 1)
        return aplicar
