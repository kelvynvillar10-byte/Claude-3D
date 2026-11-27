#!/usr/bin/env python3
"""EP02 — atuação do Juca e da Jandira (escala humana). Mesmas ferramentas da cena de prova aprovada
(producoes/teste_animacao_dinamica/codigo/atuacao.py: trajeto sem pé deslizando, virar, pulo, pose viva, câmera que
acompanha), generalizadas para qualquer personagem do rig adulto. Não altera nenhum rig.

Unidades: posições no mundo em metros (chão z = 0). Altura em cena: Juca 1,75 m, Jandira 1,65 m (5 H cada).
"""
import copy, math, sys
from pathlib import Path
import numpy as np

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[2]
for sub in ("personagens/adultos", "producoes/teste_animacao_dinamica/codigo"):
    sys.path.insert(0, str(RAIZ / sub))
import rig_adulto as RA, poses as PO                                         # noqa: E402
import atuacao as AT                                                         # noqa: E402  (câmera, compor, tela, poeira)

JUCA = RA.carregar("juca"); JAND = RA.carregar("jandira")
ALTURA = {"Juca": 1.75, "Jandira": 1.65}
suave, saida, lerp = AT.suave, AT.saida, AT.lerp


def altura(P):
    return ALTURA[P.nome]


def vel(P, tipo):
    """Velocidade do ciclo do rig convertida para m/s (H/s × altura/5): o pé de apoio não desliza."""
    v = P.A.CAMINHADA["v"] if tipo == "caminhada" else P.A.CORRIDA["v"]
    return v * altura(P) / 5.0


BRACOS = ("braco_d", "braco_e", "antebraco_d", "antebraco_e")


def espelhar_bracos(extra, vista):
    if vista != "costas":
        return dict(extra)
    return {k: (-v if k in BRACOS else v) for k, v in extra.items()}


def parado(P, vista, t, extra=None, tremer=0.0, base=None):
    """Pose VIVA (respiração, peso, cabeça) sobre uma pose base (de pé por padrão)."""
    p = copy.deepcopy(base) if base is not None else P.H.pose_base(vista)
    p.update(espelhar_bracos(extra or {}, vista))
    p["respira"] = math.sin(2 * math.pi * t / (3.1 - 1.6 * tremer))
    p["cabeca"] = p.get("cabeca", 0.0) + 1.8 * math.sin(2 * math.pi * t / 2.7)
    p["tronco"] = p.get("tronco", 0.0) + 1.0 * math.sin(2 * math.pi * t / 3.9)
    r = list(p.get("raiz", [0.0, 0.0]))
    if base is None:
        r[0] += 0.012 * math.sin(2 * math.pi * t / 3.9)
    if tremer:
        r[0] += tremer * 0.006 * math.sin(2 * math.pi * t * 11.0)
        p["cabeca"] += tremer * 1.2 * math.sin(2 * math.pi * t * 9.0)
    p["raiz"] = r
    return p


class Trajeto:
    """Ações de um personagem no tempo local do plano (mesma lógica do atuacao.Trajeto aprovado).
    tipos: andar/correr, parar, pose (extra), funcao (fn(t)→pose, com 'ease'), virar, pulo, sentar (de pé → sentado)."""

    def __init__(self, P, placa, pos0, vista, direcao=1, rosto="neutro", base=None):
        self.P = P; self.placa = placa; self.pos0 = np.asarray(pos0, float); self.vista0 = vista; self.dir0 = direcao
        self.base0 = base; self.acoes = []; self.rostos = [(0.0, rosto, None, None)]; self.objetos = []

    def faz(self, **a):
        self.acoes.append(a); return self

    def rosto(self, t, nome, olhar=None, extra=None):
        self.rostos.append((t, nome, olhar, extra)); return self

    def _rosto(self, t):
        P = self.P
        idx = max([i for i, r in enumerate(self.rostos) if t >= r[0]] or [0])
        atual = self.rostos[idx]; ant = self.rostos[idx - 1] if idx > 0 else None
        e = P.A.rosto_com_piscada(atual[1], t + 0.37 * len(atual[1]))
        if atual[3]:
            e.update(atual[3])
        if ant is not None and t - atual[0] < 0.15:
            ea = P.G.expr(ant[1])
            if ant[3]:
                ea.update(ant[3])
            e = P.G.mistura_expr(ea, e, (t - atual[0]) / 0.15)
            for k in ("olheira", "barba"):
                if k in (atual[3] or {}):
                    e[k] = atual[3][k]
        if atual[2] is not None:
            e["olhar"] = tuple(atual[2])
        return e

    def estado(self, t):
        P = self.P; pos = self.pos0.copy(); vista = self.vista0; direcao = self.dir0
        base = self.base0(vista, t) if callable(self.base0) else self.base0
        pose = parado(P, vista, t, base=base); ultima_loc = None
        dx, dz = AT.eixo_tela(self.placa) if self.placa is not None else (np.array([1.0, 0, 0]), np.array([0, 1.0, 0]))
        for a in self.acoes:
            if t < a["t0"]:
                break
            tl = t - a["t0"]; fim = a.get("dur", 0.0); k = min(1.0, tl / fim) if fim else 1.0
            tp = a["tipo"]
            if tp in ("andar", "correr"):
                tipo = "caminhada" if tp == "andar" else "corrida"
                eixo = a["eixo_vet"] if "eixo_vet" in a else (dx if a.get("eixo", "lado") == "lado" else dz)
                tt = min(tl, fim); sinal = a.get("sentido", 1)
                pos = pos + np.asarray(eixo) * sinal * vel(P, tipo) * tt * (-1 if a.get("para_tras") else 1)
                vista = a.get("vista", "perfil")
                if vista == "perfil":
                    direcao = a.get("direcao", sinal)
                fase = (-tt if a.get("para_tras") else tt) + a.get("fase0", 0.0)
                pose, _ = P.A.pose_locomocao(fase, vista=vista, tipo=tipo); ultima_loc = pose
                if "bracos" in a:                                   # braços ocupados (ex.: segurando a caixa)
                    bp = a["bracos"](vista, tt) if callable(a["bracos"]) else a["bracos"]
                    for kk in ("braco_d", "braco_e", "antebraco_d", "antebraco_e", "mao_d", "mao_e", "dedos_d", "dedos_e", "mao_vista_d", "mao_vista_e",
                               "esc_braco_d", "esc_braco_e", "esc_antebraco_d", "esc_antebraco_e"):
                        if kk in bp:
                            pose[kk] = copy.deepcopy(bp[kk])
                        else:
                            pose.pop(kk, None) if kk.startswith("esc_") else None
            elif tp == "parar":
                alvo = parado(P, vista, t, a.get("extra"), a.get("tremer", 0.0), base=base)
                pose = AT.misturar(ultima_loc or pose, alvo, suave(k)); ultima_loc = None
            elif tp == "pose":
                alvo = parado(P, vista, t, a["extra"], a.get("tremer", 0.0), base=base)
                pose = AT.misturar(pose, alvo, suave(tl / a.get("ease", 0.18)))
            elif tp == "funcao":
                alvo = a["fn"](vista, t, tl)
                pose = AT.misturar(pose, alvo, suave(tl / a.get("ease", 0.2)))
            elif tp == "virar":
                seq = a["vistas"]; i = min(len(seq) - 1, int(tl / a.get("passo", 0.09)))
                vista = seq[i]; direcao = a.get("direcao", direcao)
                if a.get("base"):
                    base = a["base"](vista, t)
                pose = parado(P, vista, t, a.get("extra"), a.get("tremer", 0.0), base=base); ultima_loc = None
            elif tp == "pulo":
                d = a.get("dur", 0.4); h = a.get("altura", 0.5)          # altura em H
                if tl < d:
                    if tl < 0.07:
                        dy = 0.12 * math.sin(math.pi * tl / 0.07)
                    else:
                        u = (tl - 0.07) / (d - 0.07); dy = -h * 4 * u * (1 - u)
                    pose = copy.deepcopy(pose); r = list(pose.get("raiz", [0, 0])); r[1] += dy; pose["raiz"] = r
                    br = a.get("bracos", 60) * math.sin(math.pi * min(1, tl / d)) * (-1 if vista == "costas" else 1)
                    if a.get("punhos"):
                        pose["braco_d"] = pose.get("braco_d", 0) + 150 * math.sin(math.pi * min(1, tl / d) / 2)
                        pose["braco_e"] = pose.get("braco_e", 0) - 150 * math.sin(math.pi * min(1, tl / d) / 2)
                        pose["antebraco_d"] = 25; pose["antebraco_e"] = -25
                        pose["dedos_d"] = P.G.mao("punho"); pose["dedos_e"] = P.G.mao("punho")
                    else:
                        pose["braco_d"] = pose.get("braco_d", 0) + br; pose["braco_e"] = pose.get("braco_e", 0) - br
        return dict(P=P, pos=pos, vista=vista, direcao=direcao, pose=pose, rosto=self._rosto(t) if vista != "costas" else None)


# ---------------------------------------------------------------- poses prontas (base) para os planos
def base_sentado(P, dy=None):
    return lambda vista, t: PO.sentado(P, vista, dy)


def base_jogando(P, intensidade=1.0, dy=None):
    def f(vista, t):
        p, _, _ = PO.jogando(P, vista, t, dy=dy, intensidade=intensidade); return p
    return f


def jogando_info(P, vista, t, intensidade=1.0, dy=None):
    """(pose, centro do controle em H (mundo do desenho), ângulo) — para desenhar o controle nas mãos."""
    return PO.jogando(P, vista, t, dy=dy, intensidade=intensidade)


def maos_caixa(P, larg=1.1, alt=0.85):
    def f(vista, t):
        p, _ = PO.segurando_caixa(P, vista, larg=larg, alt=alt); return p
    return f


def caixa_centro(P, vista, raiz_y=0.0):
    yc = -(P.H.PROP["barra_camisa"] + 0.25) + raiz_y
    return (0.0 if vista != "perfil" else 0.62, yc)
