"""Núcleo de efeitos — base: parâmetros, intensidade, FASES, contexto do quadro, telas com profundidade, registro de
plugins e a MESA (combinação de efeitos + protocolo do compositor da cenografia).

Todo efeito é um plugin com os MESMOS parâmetros (Params): intensidade (discreto | moderado | extremo), velocidade,
cor, escala, duração, direção e semente. Todo efeito passa pelas mesmas FASES, cada uma com sua curva de tempo:
início → ativação → uso → impacto → dissipação → encerramento.
Cada quadro devolve CAMADAS separadas (pela Mesa, para o compositor):
- "chao"   marcas que ficam (queimado, rachadura), sobre o cenário;
- "atras"  atrás do personagem;   "frente"  na frente do personagem (com proteção do rosto e da estampa);
- luzes    luz no cenário (luz 2D com profundidade e albedo da placa);
- luz no personagem (tom de luz): calculada e registrada, mas NÃO aplicada — é extensão do rig, pendente de aprovação;
- tremida de câmera (deslocamento do recorte, pela margem da placa);  distorção (calor, onda de choque);  quadro de impacto.
Toda camada de efeito tem profundidade por pixel: o que estiver mais perto da câmera no cenário a cobre.
"""
import importlib, math, pkgutil
from dataclasses import dataclass, field
import numpy as np

INTENSIDADES = {"discreto": 0.45, "moderado": 1.0, "extremo": 1.8}
FASES = ["inicio", "ativacao", "uso", "impacto", "dissipacao", "encerramento"]
PROPORCAO_FASES = {"inicio": 0.08, "ativacao": 0.14, "uso": 0.38, "impacto": 0.10, "dissipacao": 0.22, "encerramento": 0.08}


# ------------------------------------------------------------------ parâmetros
@dataclass
class Params:
    intensidade: str = "moderado"
    velocidade: float = 1.0
    cor: str = "#ffffff"
    escala: float = 1.0
    duracao: float = 3.0
    direcao: tuple = (0.0, 1.0, 0.0)
    semente: int = 1
    extras: dict = field(default_factory=dict)

    @property
    def fator(self):
        if self.intensidade not in INTENSIDADES:
            raise ValueError(f"intensidade '{self.intensidade}' não existe: use {list(INTENSIDADES)}")
        return INTENSIDADES[self.intensidade]


# ------------------------------------------------------------------ fases
def _curva(nome, x):
    x = min(1.0, max(0.0, x))
    if nome == "linear":
        return x
    if nome == "entra":          # ease-in
        return x * x * x
    if nome == "sai":            # ease-out
        return 1 - (1 - x) ** 3
    if nome == "suave":          # ease-in-out
        return x * x * (3 - 2 * x)
    if nome == "pulso":          # sobe rápido e volta (impacto)
        return math.sin(math.pi * x) ** 0.6
    return x


class Fases:
    """Divide a duração nas 6 fases (proporções ajustáveis). envelope(t) = intensidade 0..1 (impacto pode passar de 1)."""
    CURVAS = {"inicio": "entra", "ativacao": "sai", "uso": "linear", "impacto": "pulso", "dissipacao": "entra", "encerramento": "suave"}
    NIVEL = {"inicio": (0.0, 0.25), "ativacao": (0.25, 1.0), "uso": (1.0, 1.0), "impacto": (1.0, 1.0), "dissipacao": (1.0, 0.15), "encerramento": (0.15, 0.0)}

    def __init__(self, duracao, proporcoes=None, pico_impacto=1.35):
        prop = dict(PROPORCAO_FASES, **(proporcoes or {})); tot = sum(prop[f] for f in FASES)
        self.duracao = duracao; self.limites = []; t = 0.0
        for f in FASES:
            d = duracao * prop[f] / tot; self.limites.append((f, t, t + d)); t += d
        self.pico = pico_impacto

    def em(self, t):
        """(fase, progresso 0..1 dentro da fase) no instante t (s desde o começo do efeito); None fora do efeito."""
        if t < 0 or t > self.duracao:
            return None, 0.0
        for f, a, b in self.limites:
            if t <= b:
                return f, (t - a) / max(b - a, 1e-9)
        return FASES[-1], 1.0

    def envelope(self, t):
        f, x = self.em(t)
        if f is None:
            return 0.0
        a, b = self.NIVEL[f]; c = _curva(self.CURVAS[f], x)
        if f == "impacto":
            return 1.0 + (self.pico - 1.0) * c
        return a + (b - a) * c

    def inicio_de(self, fase):
        return next(a for f, a, b in self.limites if f == fase)


# ------------------------------------------------------------------ contexto do quadro e telas com profundidade
class Contexto:
    """O que um efeito sabe no quadro: placa (geometria da câmera), movimento de câmera, tempo, personagem."""
    def __init__(self, P, cam, t, quadro=0, fps=30, personagem=None):
        self.P, self.cam, self.t, self.quadro, self.fps, self.personagem = P, cam or {}, t, quadro, fps, personagem
        I = P.m["intrinsecos"]
        self._pos, self._dir, self._x, self._y = (np.asarray(I[k], float) for k in ("pos", "dir", "dir_x", "cima"))

    def placa(self, p):
        """Mundo (m) → placa (px) + profundidade ao longo do eixo da câmera (antes do movimento de câmera)."""
        d = np.asarray(p, float) - self._pos; z = float(d @ self._dir)
        return (self.P.cx + self.P.f * float(d @ self._x) / z, self.P.cy - self.P.f * float(d @ self._y) / z, z)

    def tela(self, p):
        """Mundo → tela da placa DEPOIS do movimento de câmera: (x, y, escala, profundidade)."""
        u, v, z = self.placa(p)
        x, y, s = self.P.projetar_ponto(u, v, z, **self.cam)
        return x, y, s, z - self.cam.get("tz", 0.0)

    def px_por_m(self, z):
        return self.P.f / max(z, 0.05)


class Tela:
    """Buffer de efeito na resolução da placa: rgba (pré-multiplicado, espaço de exibição), add (soma de brilho) e z."""
    def __init__(self, W, H):
        self.W, self.H = W, H; self.rgba = None; self.add = None; self.z = None

    def _garantir(self):
        if self.z is None:
            self.rgba = np.zeros((self.H, self.W, 4), np.float32); self.add = np.zeros((self.H, self.W, 3), np.float32)
            self.z = np.full((self.H, self.W), 5e3, np.float32)

    def vazio(self):
        return self.z is None

    def mancha(self, x, y, raio, cor, alfa, z, modo="add", perfil="gauss"):
        """Mancha (sprite) circular suave. cor: RGB 0..1 (exibição). modo add = brilho; alpha = cobre (fumaça, poeira)."""
        if raio < 0.3 or alfa <= 0:
            return
        self._garantir(); r = int(math.ceil(raio * 2.2)) + 1
        x0, x1, y0, y1 = max(0, int(x) - r), min(self.W, int(x) + r + 1), max(0, int(y) - r), min(self.H, int(y) + r + 1)
        if x0 >= x1 or y0 >= y1:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d2 = ((xx - x) ** 2 + (yy - y) ** 2) / (raio * raio)
        k = np.exp(-d2 * 1.6) if perfil == "gauss" else np.clip(1 - np.sqrt(d2), 0, 1)
        k = (k * alfa).astype(np.float32); c = np.asarray(cor, np.float32)
        if modo == "add":
            self.add[y0:y1, x0:x1] += k[..., None] * c
        else:
            a = self.rgba[y0:y1, x0:x1]
            a[..., :3] = c * k[..., None] + a[..., :3] * (1 - k[..., None]); a[..., 3] = k + a[..., 3] * (1 - k)
        zz = self.z[y0:y1, x0:x1]; zz[k > 0.02] = np.minimum(zz[k > 0.02], z)

    def imagem(self, img_rgba_premult, add_rgb, z, mascara=None):
        """Junta uma imagem inteira (ex.: traços do skia) com uma profundidade única."""
        self._garantir()
        if img_rgba_premult is not None:
            a = img_rgba_premult[..., 3:4]
            self.rgba[..., :3] = img_rgba_premult[..., :3] + self.rgba[..., :3] * (1 - a); self.rgba[..., 3:4] = a + self.rgba[..., 3:4] * (1 - a)
            m = img_rgba_premult[..., 3] > 0.02
            self.z[m] = np.minimum(self.z[m], z)
        if add_rgb is not None:
            self.add += add_rgb
            m = add_rgb.max(axis=2) > 0.01
            self.z[m] = np.minimum(self.z[m], z)

    def camada(self):
        return None if self.vazio() else {"rgba": self.rgba, "add": self.add, "z": self.z}


# ------------------------------------------------------------------ efeito (plugin) e registro
REGISTRO = {}


def efeito(nome):
    def dec(cls):
        if nome in REGISTRO:
            raise ValueError(f"efeito '{nome}' registrado duas vezes")
        cls.nome = nome; REGISTRO[nome] = cls
        return cls
    return dec


def carregar_plugins():
    """Importa efeitos/demos/*.py e efeitos/poderes/*.py: cada arquivo registra os seus. Nada do núcleo muda."""
    for pacote in ("efeitos.demos", "efeitos.poderes"):
        mod = importlib.import_module(pacote)
        for m in pkgutil.iter_modules(mod.__path__):
            importlib.import_module(f"{pacote}.{m.name}")
    return REGISTRO


class Efeito:
    """Base de todo efeito. inicio: em que segundo da cena ele começa. Subclasses sobrescrevem o que usam."""
    nome = "base"; familia = "#ffffff"; prioridade = 1

    def __init__(self, params=None, inicio=0.0, **kw):
        self.p = params or Params(); self.inicio = inicio; self.kw = kw
        self.fases = Fases(self.p.duracao / max(self.p.velocidade, 1e-3), kw.get("proporcoes"))
        self.ganho = 1.0                     # ajustado pela Mesa (combinação e segurança de flashes)

    def tl(self, ctx):
        return ctx.t - self.inicio

    def ativo(self, ctx):
        return 0.0 <= self.tl(ctx) <= self.fases.duracao

    def forca(self, ctx):
        """Intensidade efetiva no quadro: envelope da fase × nível de intensidade × ganho da mesa."""
        return self.fases.envelope(self.tl(ctx)) * self.p.fator * self.ganho

    # ganchos (opcionais)
    def preparar(self, ctx): pass
    def luzes(self, ctx): return []
    def desenhar(self, ctx, onde, tela): pass
    def distorcao(self, ctx): return None
    def impacto(self, ctx, alfa_personagem): return None
    def tremida(self, ctx): return (0.0, 0.0)
    def luz_personagem(self, ctx): return None    # (cor, forca) — registrado, não aplicado (extensão do rig pendente)
    def brilho_previsto(self, ctx):
        """Estimativa do brilho que o efeito põe no quadro (para a segurança de flashes)."""
        return sum(L["forca"] for L in self.luzes(ctx)) / 10.0      # 1,0 ≈ clarão forte


# ------------------------------------------------------------------ mesa: combinação + protocolo do compositor
class Mesa:
    """Junta os efeitos de uma cena e fala com o compositor (Placa.compor(..., efeitos=mesa)).
    Regras: no máximo UM efeito dominante por plano + UM secundário com intensidade reduzida (×0,5); o resto é
    suprimido e registrado. Segurança: limite de flashes por segundo (ver seguranca.py). Proteção do rosto e da estampa
    na camada da frente (ver protecao.py)."""
    def __init__(self, efeitos, fps=30, limite_flashes=3, protecao=True, fator_secundario=0.5):
        from .seguranca import Governador
        self.efeitos = list(efeitos); self.fps = fps; self.ctx = None; self.registro = []
        self.governador = Governador(fps=fps, limite=limite_flashes); self.protecao = protecao; self.f2 = fator_secundario

    def preparar(self, P, cam, t, quadro, personagem=None):
        """personagem: {"pe_mundo": (x, y, z), "altura_m": 1.4, "pose", "vista", "direcao"} — a mesa calcula onde ele
        está na tela neste quadro (para contatos e proteção)."""
        self.ctx = Contexto(P, cam, t, quadro, self.fps, None)
        if personagem:
            pc = dict(personagem); x, y, z = pc["pe_mundo"]
            pc["pe_tela"] = self.ctx.tela((x, y, z)); pc["topo_tela"] = self.ctx.tela((x, y, z + pc.get("altura_m", 1.4)))
            self.ctx.personagem = pc
        ativos = [e for e in self.efeitos if e.ativo(self.ctx)]
        ativos.sort(key=lambda e: (-e.prioridade, -e.p.fator))
        for i, e in enumerate(ativos):
            e.ganho = 1.0 if i == 0 else (self.f2 if i == 1 else 0.0)
        suprimidos = [e.nome for e in ativos[2:]]
        if suprimidos:
            self.registro.append({"t": round(t, 3), "suprimidos": suprimidos})
        self.ativos = [e for e in ativos if e.ganho > 0]
        g = self.governador.ganho(sum(e.brilho_previsto(self.ctx) for e in self.ativos), t)
        for e in self.ativos:
            e.ganho *= g
            e.preparar(self.ctx)
        self.luz_personagem = [e.luz_personagem(self.ctx) for e in self.ativos if e.luz_personagem(self.ctx)]
        return self

    # --- protocolo do compositor
    def luzes(self, P, cam):
        return [L for e in self.ativos for L in e.luzes(self.ctx)]

    def desenhar(self, P, cam, onde):
        tela = Tela(P.W, P.H)
        for e in self.ativos:
            e.desenhar(self.ctx, onde, tela)
        cam_ = tela.camada()
        if cam_ is not None and onde == "frente" and self.protecao and self.ctx.personagem:
            from .protecao import proteger
            proteger(cam_, self.ctx)
        return cam_

    def distorcao(self, P, cam):
        campos = [d for d in (e.distorcao(self.ctx) for e in self.ativos) if d is not None]
        if not campos:
            return None
        return sum(c[0] for c in campos), sum(c[1] for c in campos)

    def impacto(self, P, alfa):
        for e in self.ativos:
            im = e.impacto(self.ctx, alfa)
            if im is not None:
                return im
        return None

    def tremida(self):
        dx = dy = 0.0
        for e in self.ativos:
            a, b = e.tremida(self.ctx); dx += a; dy += b
        return dx, dy
