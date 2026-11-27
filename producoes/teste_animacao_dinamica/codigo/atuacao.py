"""Ferramentas de ANIMAÇÃO DINÂMICA (proposta A1 atuação + A2 câmera + A3 cenário vivo), usadas na cena de prova.
Não alteram o rig v2.1: só calculam poses (dicionários de ângulos) e posições a partir das funções públicas dele.

Princípios:
- Locomoção sem pé deslizando: o personagem avança no mundo exatamente à velocidade do ciclo do rig
  (caminhada 1,80 H/s, corrida 4,00 H/s; H = altura do Heitor), na direção que a câmera vê como "direita da tela".
- Andar para trás = o mesmo ciclo com o tempo invertido (cada pé continua parado no chão durante o apoio).
- Virar: perfil → três-quartos → frente (ou costas), um desenho por etapa, como no 2D tradicional.
- Câmera que acompanha: tx/ty resolvidos para manter um ponto do mundo num lugar da tela, com atraso natural
  (média do alvo nos últimos 0,3 s) e limite para não revelar a borda da placa.
"""
import copy, math, sys
from pathlib import Path
import numpy as np, skia

RAIZ = Path(__file__).resolve().parents[3]
for sub in ("personagens/heitor/rig_v2/codigo", "cenografia/testes"):
    sys.path.insert(0, str(RAIZ / sub))
import heitor_v2 as HV, animacao as AN, gestos as GS        # noqa: E402
import e10_testes as ET                                      # noqa: E402

ALT = 0.05                                                   # Heitor a 5 cm (m)
VEL = {"caminhada": AN.CAMINHADA["v"] * ALT, "corrida": AN.CORRIDA["v"] * ALT}   # m/s no mundo


def suave(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def saida(x):
    x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3


def lerp(a, b, k):
    return a + (b - a) * k


# ---------------------------------------------------------------- poses
def _padrao(ch):
    return 1.0 if ch.startswith("esc_") else 0.0


def misturar(p1, p2, k):
    """Mistura duas poses do rig (ângulos numéricos interpolados; mãos e listas tratadas à parte)."""
    out = {}
    for ch in set(p1) | set(p2):
        a, b = p1.get(ch, _padrao(ch)), p2.get(ch, _padrao(ch))
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            out[ch] = lerp(a, b, k)
        elif isinstance(a, list) and isinstance(b, list):
            out[ch] = [lerp(x, y, k) for x, y in zip(a, b)]
        else:
            out[ch] = copy.deepcopy(b if k >= 0.5 else a)
    return out


BRACOS = ("braco_d", "braco_e", "antebraco_d", "antebraco_e")


def espelhar_bracos(extra, vista):
    """Gestos escritos na convenção da FRENTE (braco_d > 0 = abre para fora); nas costas o desenho é espelhado,
    então o sinal inverte para o braço continuar abrindo para fora (e não cruzar o corpo)."""
    if vista != "costas":
        return dict(extra)
    return {k: (-v if k in BRACOS else v) for k, v in extra.items()}


def parado(vista, t, extra=None, tremer=0.0):
    """Pose de pé VIVA: respiração, balanço do peso, cabeça que não fica imóvel; 'tremer' (0–1) para medo."""
    p = HV.pose_base(vista); p.update(espelhar_bracos(extra or {}, vista))
    p["respira"] = math.sin(2 * math.pi * t / (3.1 - 1.6 * tremer))
    p["cabeca"] = p.get("cabeca", 0.0) + 1.8 * math.sin(2 * math.pi * t / 2.7)
    p["tronco"] = p.get("tronco", 0.0) + 1.2 * math.sin(2 * math.pi * t / 3.9)
    r = list(p.get("raiz", [0.0, 0.0])); r[0] += 0.012 * math.sin(2 * math.pi * t / 3.9)
    if tremer:
        r[0] += tremer * 0.006 * math.sin(2 * math.pi * t * 11.0)
        p["cabeca"] += tremer * 1.2 * math.sin(2 * math.pi * t * 9.0)
    p["raiz"] = r
    return p


def locomocao(t, vista, tipo="caminhada"):
    pose, _ = AN.pose_locomocao(t, vista=vista, tipo=tipo); return pose


def eixo_tela(P):
    """Vetor do chão (m) que a câmera da placa vê como 'para a direita da tela'; e o que vê como 'para longe'."""
    I = P.m["intrinsecos"]; dx = np.asarray(I["dir_x"], float); dx[2] = 0; dz = np.asarray(I["dir"], float); dz[2] = 0
    return dx / np.linalg.norm(dx), dz / np.linalg.norm(dz)


class Trajeto:
    """Sequência de ações do Heitor no tempo local do plano. Cada ação: dict(tipo, t0, dur, ...).
    tipos: 'andar'/'correr' (eixo, sentido: +1 direita/longe, −1 esquerda/perto; para_tras), 'parar' (mistura com a pose de pé),
    'pose' (pose-alvo misturada em 'ease' s), 'virar' (sequência de vistas), 'pulo' (susto: sai do chão e volta),
    'tropeco' (desequilíbrio com braços)."""

    def __init__(self, P, pos0, vista, direcao=1, extra=None, rosto="neutro"):
        self.P = P; self.pos0 = np.asarray(pos0, float); self.vista0 = vista; self.dir0 = direcao
        self.extra0 = extra or {}; self.acoes = []; self.rostos = [(0.0, rosto, None)]

    def faz(self, **a):
        self.acoes.append(a); return self

    def rosto(self, t, nome, olhar=None):
        self.rostos.append((t, nome, olhar)); return self

    def _rosto(self, t):
        idx = max([i for i, r in enumerate(self.rostos) if t >= r[0]] or [0])
        atual = self.rostos[idx]; ant = self.rostos[idx - 1] if idx > 0 else None
        e = AN.rosto_com_piscada(atual[1], t + 0.37 * len(atual[1]))
        if ant is not None and t - atual[0] < 0.15:                 # transição de expressão em 0,15 s
            e = GS.mistura_expr(GS.expr(ant[1]), e, (t - atual[0]) / 0.15)
        olhar = atual[2]
        if olhar is not None:
            e["olhar"] = tuple(olhar)
        return e

    def estado(self, t):
        """→ dict(pos (m), vista, direcao, pose, rosto, no_chao)."""
        pos = self.pos0.copy(); vista = self.vista0; direcao = self.dir0
        pose = parado(vista, t, self.extra0); ultima_loc = None
        dx, dz = eixo_tela(self.P)
        for a in self.acoes:
            if t < a["t0"]:
                break
            tl = t - a["t0"]; fim = a.get("dur", 0.0); k = min(1.0, tl / fim) if fim else 1.0
            tp = a["tipo"]
            if tp in ("andar", "correr"):
                tipo = "caminhada" if tp == "andar" else "corrida"
                eixo = dx if a.get("eixo", "lado") == "lado" else dz
                tt = min(tl, fim); sinal = a.get("sentido", 1)          # sentido = para onde ele OLHA; para trás anda ao contrário
                pos = pos + eixo * sinal * VEL[tipo] * tt * (-1 if a.get("para_tras") else 1)
                vista = a.get("vista", "perfil")
                if vista == "perfil":
                    direcao = sinal
                fase = (-tt if a.get("para_tras") else tt) + a.get("fase0", 0.0)
                pose = locomocao(fase, vista, tipo); ultima_loc = pose
                if tl > fim:                                        # acabou: segura a última pose até a próxima ação
                    pose = ultima_loc
            elif tp == "parar":
                base = parado(vista, t, a.get("extra"), a.get("tremer", 0.0))
                pose = misturar(ultima_loc or pose, base, suave(k)); ultima_loc = None
            elif tp == "pose":
                alvo = parado(vista, t, a["extra"], a.get("tremer", 0.0))
                pose = misturar(pose, alvo, suave(tl / a.get("ease", 0.18)))
            elif tp == "virar":
                seq = a["vistas"]; i = min(len(seq) - 1, int(tl / a.get("passo", 0.09)))
                vista = seq[i]; direcao = a.get("direcao", direcao)
                pose = parado(vista, t, a.get("extra"), a.get("tremer", 0.0)); ultima_loc = None
            elif tp == "pulo":                                      # susto: agacha 0,06 s, sobe, cai e amortece
                d = a.get("dur", 0.38); h = a.get("altura", 0.10)
                if tl < d:
                    if tl < 0.06:
                        dy = 0.03 * math.sin(math.pi * tl / 0.06)
                    else:
                        u = (tl - 0.06) / (d - 0.06); dy = -h * 4 * u * (1 - u)
                    pose = copy.deepcopy(pose); r = list(pose.get("raiz", [0, 0])); r[1] += dy; pose["raiz"] = r
                    br = a.get("bracos", 60) * math.sin(math.pi * min(1, tl / d)) * (-1 if vista == "costas" else 1)
                    pose["braco_d"] = pose.get("braco_d", 0) + br; pose["braco_e"] = pose.get("braco_e", 0) - br
            elif tp == "tropeco":                                   # desequilíbrio: tronco balança, braços giram, quadril cai e volta
                d = a.get("dur", 0.9)
                if tl < d:
                    u = tl / d; amp = math.sin(math.pi * u); sg = -1 if vista == "costas" else 1
                    pose = copy.deepcopy(pose)
                    pose["tronco"] = pose.get("tronco", 0) + a.get("lado", 1) * 14 * amp * math.sin(2 * math.pi * u * 1.5)
                    pose["braco_d"] = sg * (70 + 70 * amp + 25 * math.sin(2 * math.pi * u * 3))
                    pose["braco_e"] = -sg * (70 + 70 * amp + 25 * math.sin(2 * math.pi * u * 3 + 1.2))
                    pose["antebraco_d"] = 20 * sg; pose["antebraco_e"] = -20 * sg
                    pose["cabeca"] = pose.get("cabeca", 0) - a.get("lado", 1) * 8 * amp
                    r = list(pose.get("raiz", [0, 0])); r[0] += a.get("lado", 1) * 0.05 * amp; pose["raiz"] = r
        return dict(pos=pos, vista=vista, direcao=direcao, pose=pose, rosto=self._rosto(t) if vista != "costas" else None)


# ---------------------------------------------------------------- câmera
def enquadrar(P, ponto, x_frac, y_frac, zoom, OW=1080, OH=1920):
    """Recorte (pan_x, pan_y em px da placa) que leva o ponto do mundo para (x_frac, y_frac) da tela, com o zoom dado."""
    u, v, z = ET.projetar(P, ponto)
    X = x_frac * OW + (P.W - OW) / 2; Y = y_frac * OH + (P.H - OH) / 2
    return (u - P.cx) - (X - P.cx) / zoom, (v - P.cy) - (Y - P.cy) / zoom, z


def _z_perto(P):
    if not hasattr(P, "_z_perto"):
        zs = []
        for c, d in P.camadas.items():
            if c == "ceu":
                continue
            Z = d["prof"]; Z = Z[np.isfinite(Z) & (Z > 0)]
            if Z.size:
                zs.append(float(np.percentile(Z, 0.2)))
        P._z_perto = min(zs) if zs else 0.05
    return P._z_perto


def seguir(P, alvo_em, t, x_frac, y_frac, zoom, atraso=0.3, paralaxe=0.35, OW=1080, OH=1920):
    """Câmera que acompanha um alvo (função t → ponto do mundo), com atraso natural (média do enquadramento ideal nos
    últimos 'atraso' s; determinístico por quadro). Devolve dict(zoom, tx, ty, pan): o recorte 2D (pan) faz o
    enquadramento sem nunca sair da placa; uma parte do movimento vira translação real da câmera (tx/ty), com
    paralaxe, limitada pela sobra que resta medida no chão mais próximo da lente."""
    amostras = [t - atraso * i / 6 for i in range(7)]
    pxs, pys, zs = zip(*[enquadrar(P, alvo_em(max(0.0, s)), x_frac, y_frac, zoom, OW, OH) for s in amostras])
    px, py = float(np.mean(pxs)), float(np.mean(pys))
    mx = max(0.0, (P.W - OW / zoom) / 2 - 6); my = max(0.0, (P.H - OH / zoom) / 2 - 6)
    px = max(-mx, min(mx, px)); py = max(-my, min(my, py))
    zp = _z_perto(P)                                            # translação: só o que sobra da margem no plano mais perto
    tx = max(-(mx - abs(px)) * zp / P.f, min((mx - abs(px)) * zp / P.f, paralaxe * px * float(np.mean(zs)) / P.f))
    ty = -max(-(my - abs(py)) * zp / P.f, min((my - abs(py)) * zp / P.f, paralaxe * py * float(np.mean(zs)) / P.f)) * 0.0
    return dict(zoom=zoom, tx=tx, ty=ty, pan=(px - tx * P.f / float(np.mean(zs)), py))


def compor(P, cam, **kw):
    """Placa.compor com recorte deslocado (pan) — sem mexer no compositor: desloca a grade de destino e a projeção."""
    pan = cam.get("pan", (0.0, 0.0)); c = {k: v for k, v in cam.items() if k != "pan"}; z = c.get("zoom", 1.0)
    U0, V0, proj0 = P.u, P.v, P.projetar_ponto
    P.u = U0 + pan[0] * z; P.v = V0 + pan[1] * z

    def proj(x, y, zz, **k):
        a, b, s = proj0(x, y, zz, **k); return a - z * pan[0], b - z * pan[1], s
    P.projetar_ponto = proj
    try:
        return P.compor(cam=c, **kw)
    finally:
        P.u, P.v = U0, V0; del P.projetar_ponto


def tela(P, cam, p, OW=1080, OH=1920):
    """Ponto da placa (px, px, prof) → tela final, com o mesmo movimento de câmera e recorte."""
    pan = cam.get("pan", (0.0, 0.0)); c = {k: v for k, v in cam.items() if k != "pan"}; z = c.get("zoom", 1.0)
    x, y, _ = P.projetar_ponto(*p, **c); return x - z * pan[0] - (P.W - OW) / 2, y - z * pan[1] - (P.H - OH) / 2


# ---------------------------------------------------------------- cenário vivo
class Poeira:
    """Partículas de poeira no feixe de luz: flutuam devagar, cintilam e têm paralaxe com a câmera."""

    def __init__(self, n=90, semente=3, area=(0.0, 1.0, 0.05, 0.75), cor=(255, 236, 190)):
        rng = np.random.default_rng(semente)
        self.x = rng.uniform(area[0], area[1], n); self.y = rng.uniform(area[2], area[3], n)
        self.z = rng.uniform(0.0, 1.0, n)                           # 0 = perto da lente (grande e desfocada), 1 = longe
        self.f = rng.uniform(0, 2 * math.pi, n); self.v = rng.uniform(0.006, 0.02, n); self.cor = cor

    def desenhar(self, cv, t, tx=0.0, ty=0.0, zoom=1.0, OW=1080, OH=1920, forca=1.0):
        for i in range(len(self.x)):
            par = 1.0 / (0.25 + self.z[i])                          # paralaxe: o perto anda mais quando a câmera anda
            x = ((self.x[i] + 0.012 * math.sin(t * 0.7 + self.f[i]) - tx * 2.2 * par) % 1.2 - 0.1) * OW
            y = ((self.y[i] - self.v[i] * t + 0.01 * math.cos(t * 0.9 + self.f[i]) + ty * 2.2 * par) % 1.0) * OH
            x = OW / 2 + (x - OW / 2) * zoom; y = OH / 2 + (y - OH / 2) * zoom
            perto = self.z[i] < 0.18
            r = (14 + 22 * (0.18 - self.z[i]) / 0.18) if perto else 2.0 + 3.5 * (1 - self.z[i])
            a = (0.5 + 0.5 * math.sin(t * 2.3 + self.f[i] * 3)) * (40 if perto else 170) * forca
            p = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(a), *self.cor),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * (0.6 if perto else 0.5)))
            cv.drawCircle(x, y, r, p)
