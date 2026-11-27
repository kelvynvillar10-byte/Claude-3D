#!/usr/bin/env python3
"""Cena de prova da ANIMAÇÃO DINÂMICA (~20 s): o mesmo trecho da narração do EP01 (39,2–58,9 s, "Mas existe um perigo
ainda maior… e você poderia estar em perigo"), refeito com a diretriz de 27/11/2026:
personagens sempre em movimento, câmera que acompanha a ação, cenário vivo e cada palavra-chave com ação na tela.

Cada plano é uma função do tempo local que devolve o ESTADO do quadro (câmera, Heitor, gato, aranha, pata, efeitos).
O mapa fala → imagem (palavra, instante, ação na tela) fica em MAPA e vai para saida/mapa_fala_imagem.json.
Uso: cena_dinamica.py [--png pasta --quadros 0,30,...]  (sem argumentos: gera o vídeo sem áudio em paralelo)
"""
import json, math, os, subprocess, sys
from pathlib import Path
import numpy as np, cv2, skia

P_ = Path(__file__).resolve().parents[1]; RAIZ = P_.parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(RAIZ))
for sub in ("producoes/ep01_cinco_centimetros/codigo", "personagens/animais", "personagens/heitor/extensoes/x1_tom_de_luz"):
    sys.path.insert(0, str(RAIZ / sub))
import atuacao as A                                                          # noqa: E402
import placas_teste as PT                                                    # noqa: E402
import compor_ep01 as CP                                                     # noqa: E402  (legenda, marca d'água, olho, sombra do gato)
import gato as GATO, aranha as ARANHA                                        # noqa: E402
import tom_de_luz as X1                                                      # noqa: E402
from cenografia.nucleo.compositor import Placa                               # noqa: E402

FPS = 30; OW, OH = 1080, 1920; ALT = A.ALT
T0, T1 = 39.20, 58.90                                                        # trecho da narração do EP01 (s)
DUR = round(T1 - T0, 3)
S = PT.specs()
GR = A.ET.GRADE; PESOS = A.ET.PESOS
_PL = {}


def placa(nome):
    if nome not in _PL:
        if len(_PL) >= int(os.environ.get("MAX_PLACAS", "2")):
            _PL.pop(next(iter(_PL)))
        _PL[nome] = Placa(PT.pasta(nome, S))
    return _PL[nome]


def em(t_abs):
    return t_abs - T0


V = np.asarray
POEIRA = A.Poeira(n=90, semente=3)


# ======================================================================= planos
# T1 (lateral, rente ao tapete): D01 e D02 dividem o mesmo trajeto do Heitor
def _traj_t1():
    P = placa("T1_sala_lado")
    tr = A.Trajeto(P, [0.225, -0.07, 0.008], "perfil", 1, rosto="pensativo")
    tr.faz(tipo="andar", t0=0.0, dur=1.38, sentido=1)                       # anda pelo tapete desde o 1º quadro
    tr.faz(tipo="parar", t0=1.38, dur=0.22)
    tr.faz(tipo="virar", t0=1.45, vistas=["tres_quartos", "frente"], passo=0.08, direcao=1)
    tr.faz(tipo="pose", t0=1.62, extra={"tronco": 4, "braco_d": 18, "braco_e": -18, "antebraco_d": 25, "antebraco_e": -25}, ease=0.2)
    tr.rosto(0.75, "preocupacao", (0.6, 0.0)).rosto(1.50, "preocupacao", (0.0, 0.0)).rosto(1.55, "medo", (0.0, 0.1))
    return P, tr


def D01(tl):                                                                 # 39,20 "Mas existe um perigo"
    P, tr = _traj_t1(); h = tr.estado(tl); z = A.lerp(1.45, 1.35, tl / 1.25)
    cam = A.seguir(P, lambda s: tr.estado(s)["pos"] + [0, 0, 0.03], tl, 0.40, 0.60, z, atraso=0.35)
    return dict(placa="T1_sala_lado", cam=cam, heitor=h, poeira=1.0)


def D02(tl):                                                                 # 40,45 "ainda maior": para, vira para nós, punch-in
    P, tr = _traj_t1(); t = tl + 1.25; h = tr.estado(t)
    z = A.lerp(1.40, 1.95, A.saida(tl / 0.55))
    cam = A.seguir(P, lambda s: tr.estado(s)["pos"] + [0, 0, 0.038], t, 0.5, 0.47, z, atraso=0.2)
    return dict(placa="T1_sala_lado", cam=cam, heitor=h, poeira=1.0)


def D03(tl):                                                                 # 41,45 "os animais da sua própria casa"
    P = placa("G_sala_gato")
    tr = A.Trajeto(P, [0.36, -0.08, 0.008], "frente", 1, rosto="preocupacao")
    tr.faz(tipo="andar", t0=0.0, dur=0.95, vista="frente", eixo="prof", sentido=-1)   # vem na direção da câmera, olhando em volta
    tr.faz(tipo="parar", t0=0.95, dur=0.25, tremer=0.6)
    tr.rosto(0.0, "preocupacao", (-0.7, 0.0)).rosto(0.55, "preocupacao", (0.7, 0.0)).rosto(1.05, "medo", (0.3, -0.6))
    h = tr.estado(tl); z = A.lerp(1.55, 1.12, A.suave(tl / 1.55))
    cam = A.seguir(P, lambda s: tr.estado(s)["pos"] + [0, 0, 0.03], tl, 0.42, 0.62, z, atraso=0.3)
    return dict(placa="G_sala_gato", cam=cam, heitor=h, poeira=0.8,
                sombra_gato=dict(x=A.lerp(1.05, 0.62, A.suave(tl / 1.4)), y=0.60, alt=A.lerp(0.34, 0.46, A.suave(tl / 1.4))))


def _traj_h():
    P = placa("H_aranha_canto"); dx, _ = A.eixo_tela(P)
    marca = V(S["H_aranha_canto"]["heitor"], float)
    tr = A.Trajeto(P, marca - dx * A.VEL["caminhada"] * 0.80, "perfil", 1, rosto="pensativo")
    tr.faz(tipo="andar", t0=0.0, dur=0.80, sentido=1)
    tr.faz(tipo="parar", t0=0.80, dur=0.22)
    tr.faz(tipo="virar", t0=1.20, vistas=["frente", "tres_quartos"], passo=0.08, direcao=-1)      # sente algo atrás: vira
    tr.faz(tipo="pulo", t0=1.42, dur=0.36, altura=0.10, bracos=55)                                   # "aranha!": pulo de susto
    tr.faz(tipo="pose", t0=1.80, extra={"braco_d": 32, "braco_e": -32, "antebraco_d": 22, "antebraco_e": -22}, tremer=0.7)
    tr.faz(tipo="andar", t0=2.75, dur=0.60, sentido=-1, para_tras=True)                              # recua sem tirar os olhos dela
    tr.faz(tipo="parar", t0=3.35, dur=0.2, tremer=1.0, extra={"braco_d": -30, "antebraco_d": -45, "braco_e": -20, "antebraco_e": -40})  # perfil: braços à frente
    tr.rosto(1.20, "surpresa", (-0.7, 0.0)).rosto(1.40, "medo", (-0.8, 0.0))
    return P, tr, dx


def _aranha_em(t, dx):                                                       # t: local do bloco H (0 = 43,00 s)
    alvo = V([1.865, 1.716, 0.0]); ini = alvo - dx * 0.11
    if t < 1.05:
        return None
    u = min(1.0, (t - 1.05) / 0.5); pos = ini + (alvo - ini) * A.saida(u); fase = 0.0
    fase = 2.4 * (t - 1.05) if u < 1 else 2.4 * 0.5 + 0.6 * (t - 1.55)
    lev = 0.0
    if t > 2.55:
        lev = A.saida((t - 2.55) / 0.35)                                     # "assustadora": ergue as patas da frente
    if t > 2.9:                                                              # avança devagar na direção do Heitor
        pos = alvo + dx * 0.035 * A.suave((t - 2.9) / 1.0); fase += 1.6 * min(1.0, (t - 2.9))
    return dict(pos=pos, larg_m=0.05, fase=fase, levantar=lev)


def D04(tl):                                                                 # 43,00 "…casa" → chega ao canto
    P, tr, dx = _traj_h(); h = tr.estado(tl); z = 1.15
    cam = A.seguir(P, lambda s: tr.estado(s)["pos"] + [0, 0, 0.03], tl, 0.52, 0.58, z, atraso=0.35)
    return dict(placa="H_aranha_canto", cam=cam, heitor=h, aranha=_aranha_em(tl, dx), poeira=0.6)


def D05(tl):                                                                 # 44,05 "Uma aranha" — crash zoom
    P, tr, dx = _traj_h(); t = tl + 1.05; h = tr.estado(t); ar = _aranha_em(t, dx)
    k = A.saida((t - 1.29) / 0.22) if t > 1.29 else 0.0                     # "aranha" = 44,34 s
    z = A.lerp(1.15, 1.75, k)
    alvo = lambda s: (h["pos"] + [0, 0, 0.03]) * (1 - k) + (ar["pos"] + [0, 0, 0.01]) * k if ar else h["pos"]
    cam = A.seguir(P, alvo, t, A.lerp(0.52, 0.45, k), A.lerp(0.58, 0.55, k), z, atraso=0.0)
    return dict(placa="H_aranha_canto", cam=cam, heitor=h, aranha=ar, poeira=0.6,
                tremida=(0.0, 0.25) if k > 0 else None, tremida_ini=0.24)


def D06(tl):                                                                 # 45,20 "parecer assustadora": ela ergue as patas, ele recua
    P, tr, dx = _traj_h(); t = tl + 2.20; h = tr.estado(t); ar = _aranha_em(t, dx)
    z = A.lerp(1.55, 1.08, A.suave(tl / 1.3))
    alvo = lambda s: 0.5 * (tr.estado(s)["pos"] + [0, 0, 0.03]) + 0.5 * (_aranha_em(s, dx)["pos"] + [0, 0, 0.01])
    cam = A.seguir(P, alvo, t, 0.5, 0.57, z, atraso=0.3)
    return dict(placa="H_aranha_canto", cam=cam, heitor=h, aranha=ar, poeira=0.6, tremida=(0.42, 0.75))


def _gato_andando(t, ini, para, alt_m, T=0.85, dx=None):
    """Gato andando em linha reta: avança AVANCO_POR_CICLO × altura por ciclo (patas não deslizam)."""
    v = GATO.AVANCO_POR_CICLO * alt_m / T; dist = float(np.linalg.norm(V(para) - V(ini)))
    d = min(dist, v * t); pos = V(ini) + (V(para) - V(ini)) * (d / dist)
    return pos, d / (GATO.AVANCO_POR_CICLO * alt_m), d >= dist


def D07(tl):                                                                 # 47,00 "E um gato curioso": o gato entra andando
    P = placa("T1_sala_lado"); _, tr1 = _traj_t1()
    tr = A.Trajeto(P, tr1.estado(3.0)["pos"], "frente", 1, rosto="medo")
    tr.faz(tipo="virar", t0=0.35, vistas=["tres_quartos"], direcao=1, tremer=0.5)
    tr.faz(tipo="pose", t0=0.5, extra={"tronco": -5, "cabeca": -6, "braco_d": 20, "braco_e": -20}, tremer=0.6)
    tr.rosto(0.0, "medo", (0.0, 0.0)).rosto(0.35, "surpresa", (0.8, -0.3)).rosto(0.75, "medo", (0.7, -0.9))
    h = tr.estado(tl)
    pos, fase, chegou = _gato_andando(tl, [0.78, 0.13, 0.008], [0.47, 0.13, 0.008], 0.25, T=0.62)
    g = dict(pos=pos, alt_m=0.25, pose="andando", direcao=-1, fase=fase, cauda=math.sin(2 * math.pi * tl * 1.1), olhar=-0.4,
             pupila=0.3, inclinar=6 * math.sin(2 * math.pi * tl * 0.5))
    z = A.lerp(1.15, 1.0, A.suave(tl / 1.4))
    alvo = lambda s: 0.5 * (h["pos"] + [0, 0, 0.03]) + 0.5 * (_gato_andando(s, [0.78, 0.13, 0.008], [0.47, 0.13, 0.008], 0.25, T=0.62)[0] + [0, 0, 0.12])
    cam = A.seguir(P, alvo, tl, 0.5, 0.55, z, atraso=0.35)
    return dict(placa="T1_sala_lado", cam=cam, heitor=h, gato=g, poeira=1.0)


def _t2_heitor(tl0):
    P = placa("T2_sala_baixo")
    tr = A.Trajeto(P, S["T2_sala_baixo"]["heitor"], "costas", 1)
    tr.faz(tipo="pose", t0=0.0, extra={"tronco": -3, "braco_d": 16, "braco_e": -16}, tremer=0.4)
    tr.faz(tipo="pose", t0=2.3, extra={"tronco": -2, "braco_d": 28, "braco_e": -28, "antebraco_d": 20, "antebraco_e": -20}, tremer=1.0)
    tr.faz(tipo="andar", t0=5.85, dur=0.9, vista="costas", eixo="prof", sentido=1, para_tras=True)   # recua devagar
    tr.faz(tipo="tropeco", t0=7.10, dur=0.95, lado=1)                                                 # "errado": tropeça
    tr.faz(tipo="pose", t0=8.05, extra={"braco_d": 40, "braco_e": -40, "antebraco_d": 15, "antebraco_e": -15}, tremer=1.0)
    tr.faz(tipo="pulo", t0=8.15, dur=0.36, altura=0.12, bracos=70)                                     # a pata desce: pulo
    tr.faz(tipo="virar", t0=8.7, vistas=["perfil"], direcao=-1, tremer=1.0)                          # vira para fugir
    tr.rosto(8.7, "medo", (-0.6, -0.2))
    return P, tr


def _gato_t2(t):                                                             # t: local do bloco T2 (0 = 48,40 s)
    base = dict(pos=V([0.585, 0.10, 0.008]), direcao=-1, olhar=-0.35)
    if t < 2.15:                                                             # sentado: "parecia inofensivo"
        incl = 14 * A.suave((t - 0.9) / 0.4) - 14 * A.suave((t - 1.9) / 0.4)
        pis = math.sin(math.pi * min(1, max(0, (t - 1.35) / 0.35))) if 1.35 <= t <= 1.7 else 0.0
        return dict(base, alt_m=0.28, pose="sentado", pupila=0.22, piscar=pis, inclinar=incl, cauda=math.sin(2 * math.pi * t * 0.55))
    pup = A.lerp(0.3, 1.0, A.saida((t - 2.6) / 1.6))                         # "verdadeiro predador": pupila dilata
    return dict(base, alt_m=0.19, pose="agachado", pupila=pup, piscar=0.0, inclinar=0.0,
                cauda=math.sin(2 * math.pi * t * 1.8) * 0.9, olhar=-0.35 - 0.25 * A.suave((t - 5.8) / 1.0))


def D08(tl):                                                                 # 48,40 "que antes parecia inofensivo"
    P, tr = _t2_heitor(0); h = tr.estado(tl); g = _gato_t2(tl)
    z = A.lerp(1.25, 1.12, A.suave(tl / 2.1))
    k = A.suave((tl - 0.2) / 1.3)                                           # tilt: do Heitor para o rosto do gato
    alvo = lambda s: (h["pos"] + [0, 0, 0.035]) * (1 - k) + (g["pos"] + [-0.04, 0, 0.23]) * k
    cam = A.seguir(P, alvo, tl, 0.5, A.lerp(0.62, 0.42, k), z, atraso=0.0)
    return dict(placa="T2_sala_baixo", cam=cam, heitor=h, gato=g, poeira=0.9)


def D09(tl):                                                                 # 50,55 "agora seria um verdadeiro": agacha, pupila abre
    P, tr = _t2_heitor(0); t = tl + 2.15; h = tr.estado(t); g = _gato_t2(t)
    z = A.lerp(1.08, 1.42, A.suave(tl / 2.3))
    cam = A.seguir(P, lambda s: g["pos"] + [-0.05, 0, 0.14], t, 0.5, 0.47, z, atraso=0.0)
    return dict(placa="T2_sala_baixo", cam=cam, heitor=h, gato=g, poeira=0.7)


def D10(tl):                                                                 # 52,85 "predador": olho em close
    return dict(insert="olho", pupila=A.lerp(0.35, 1.0, A.saida(min(1, tl / 0.5))), zoom=A.lerp(1.0, 1.45, A.saida(tl / 1.3)),
                tremida=(0.1, 0.5))


def D11(tl):                                                                 # 54,15 "Um único movimento errado": recua e tropeça
    P, tr = _t2_heitor(0); t = tl + 5.75; h = tr.estado(t); g = _gato_t2(t)
    z = 1.05
    cam = A.seguir(P, lambda s: 0.6 * (tr.estado(s)["pos"] + [0, 0, 0.03]) + 0.4 * (g["pos"] + [0, 0, 0.1]), t, 0.5, 0.58, z, atraso=0.35)
    return dict(placa="T2_sala_baixo", cam=cam, heitor=h, gato=g, poeira=0.7, tremida=(1.42, 1.75))


def D12(tl):                                                                 # 56,50 "e você poderia": a pata desce
    P, tr = _t2_heitor(0); t = tl + 8.1; h = tr.estado(t); g = _gato_t2(t)
    z = 1.12
    cam = A.seguir(P, lambda s: tr.estado(s)["pos"] + [0, 0, 0.03], t, 0.5, 0.64, z, atraso=0.3)
    kk = A.saida(min(1.0, tl * 2.2))
    return dict(placa="T2_sala_baixo", cam=cam, heitor=h, gato=g, poeira=0.7,
                pata=dict(x=0.56, y=A.lerp(-0.30, 0.30, kk), tam=0.42, garras=kk), tremida=(0.4, 0.75))


def D13(tl):                                                                 # 57,55 "estar em perigo": ele corre, o gato salta
    P = placa("G_sala_gato")
    tr = A.Trajeto(P, [0.36, -0.10, 0.008], "perfil", -1, rosto="medo")
    tr.faz(tipo="correr", t0=0.0, dur=1.6, sentido=-1).rosto(0.0, "medo", (-0.7, 0.0))
    h = tr.estado(tl)
    ini, fim = V([0.60, 0.06, 0.008]), V([0.40, -0.06, 0.008]); u = A.suave((tl - 0.30) / 0.25)
    pos = ini + (fim - ini) * u; pos = pos + [0, 0, 0.06 * 4 * u * (1 - u)]                      # bote do gato (arco)
    g = dict(pos=pos, alt_m=0.19, pose="agachado", direcao=-1, pupila=1.0, olhar=-0.9, cauda=math.sin(2 * math.pi * tl * 2.2))
    z = 1.25
    cam = A.seguir(P, lambda s: tr.estado(s)["pos"] + [0, 0, 0.03], tl, 0.5, 0.62, z, atraso=0.25)
    puff = dict(pos=fim, t=tl - 0.55) if tl > 0.55 else None
    return dict(placa="G_sala_gato", cam=cam, heitor=h, gato=g, poeira=0.8, puff=puff,
                tremida=(0.55, 0.9))


PLANOS = [  # (id, início absoluto, fim absoluto, função, entrada)
    ("D01", 39.20, 40.45, D01, None), ("D02", 40.45, 41.45, D02, "corte"), ("D03", 41.45, 43.00, D03, "chicote"),
    ("D04", 43.00, 44.05, D04, "corte"), ("D05", 44.05, 45.20, D05, "corte"), ("D06", 45.20, 47.00, D06, "corte"),
    ("D07", 47.00, 48.40, D07, "chicote"), ("D08", 48.40, 50.55, D08, "corte"), ("D09", 50.55, 52.85, D09, "corte"),
    ("D10", 52.85, 54.15, D10, "corte"), ("D11", 54.15, 56.50, D11, "corte"), ("D12", 56.50, 57.55, D12, "flash"),
    ("D13", 57.55, 58.90, D13, "chicote"),
]

MAPA = [  # palavra (como falada), instante (s, absoluto) e a ação que está na tela naquele momento
    ("perigo", 40.17, "D01", "o Heitor caminha pelo tapete; a câmera acompanha"),
    ("maior", 40.73, "D02", "ele para, vira para a câmera assustado; aproximação rápida"),
    ("animais", 41.79, "D03", "a sombra do gato varre o chão enquanto ele olha em volta"),
    ("casa", 43.11, "D04", "câmera recua e revela a sala; ele chega ao canto da parede"),
    ("aranha", 44.34, "D05", "a aranha entra correndo; zoom brusco nela; ele pula de susto"),
    ("assustadora", 45.64, "D06", "ela ergue as patas da frente; ele recua tremendo"),
    ("gato", 47.35, "D07", "o gato entra andando no quadro"),
    ("curioso", 47.63, "D07", "o gato inclina a cabeça; o Heitor olha para cima"),
    ("inofensivo", 49.39, "D08", "o gato sentado inclina a cabeça e pisca devagar; câmera sobe até o rosto dele"),
    ("predador", 52.92, "D10", "close do olho: a pupila dilata"),
    ("movimento", 54.99, "D11", "o Heitor recua passo a passo"),
    ("errado", 55.55, "D11", "ele tropeça e quase cai"),
    ("perigo", 58.06, "D13", "ele corre; o gato dá o bote onde ele estava (impacto)"),
]


# ======================================================================= composição
def plano_em(t_abs):
    for p in PLANOS:
        if p[1] <= t_abs < p[2]:
            return p
    return PLANOS[-1]


def _proj(P, pos, alt):
    return A.ET.projetar(P, tuple(pos)), A.ET.projetar(P, (pos[0], pos[1], pos[2] + alt))


def desenhar_heitor(cv, x, y, tam, d):
    """Desenha com o rig; se a união de contornos do skia falhar num ângulo degenerado, repete com 0,3° de diferença nos braços."""
    pose = d["pose"]
    for tentativa in range(4):
        try:
            cv.save(); A.HV.desenhar(cv, x, y, tam, vista=d["vista"], direcao=d["direcao"], pose=pose, rosto=d["rosto"]); cv.restore(); return
        except RuntimeError:
            cv.restore(); pose = dict(pose)
            for k in A.BRACOS:
                pose[k] = pose.get(k, 0.0) + 0.3 * (tentativa + 1)
    raise RuntimeError("rig: união de contornos falhou mesmo com a perturbação")


def desenhista(P, st):
    atores = []
    h = st.get("heitor")
    if h is not None:
        atores.append(("heitor", h, *_proj(P, h["pos"], ALT)))
    if st.get("gato"):
        g = st["gato"]; atores.append(("gato", g, *_proj(P, g["pos"], g["alt_m"])))
    if st.get("aranha"):
        a = st["aranha"]; atores.append(("aranha", a, *_proj(P, a["pos"], a["larg_m"])))
    atores.sort(key=lambda r: -r[2][2])                                      # do mais longe para o mais perto

    def desenhar(cv, proj):
        for tipo, d, pe, topo in atores:
            x, y, _ = proj(*pe); _, yt, _ = proj(*topo); tam = y - yt
            if tipo == "heitor":
                desenhar_heitor(cv, x, y, tam, d)
            elif tipo == "gato":
                GATO.desenhar(cv, x, y, tam, pose=d["pose"], direcao=d["direcao"], olhar=d.get("olhar", 0.0), pupila=d.get("pupila", 0.25),
                              piscar=d.get("piscar", 0.0), fase=d.get("fase", 0.0), cauda=d.get("cauda", 0.0), inclinar=d.get("inclinar", 0.0))
            else:
                ARANHA.desenhar(cv, x, y, tam, fase=d["fase"], levantar_frente=d["levantar"])
    perto = min(atores, key=lambda r: r[2][2]) if atores else None
    return desenhar, (h and _proj(P, h["pos"], ALT)), perto


def sombras(cv, P, cam, st):
    """Sombras de contato desenhadas DEPOIS da composição, na tela (assim a borda semitransparente não clareia)."""
    for chave, alt_k, larg, alfa in (("heitor", None, 0.42, 120), ("gato", "alt_m", 1.0, 110), ("aranha", "larg_m", 0.9, 90)):
        d = st.get(chave)
        if not d:
            continue
        pos = np.asarray(d["pos"], float); alt = ALT if alt_k is None else d[alt_k]
        z_chao = 0.008 if pos[2] > 0.004 else pos[2]
        no_ar = max(0.0, pos[2] - z_chao); k = max(0.3, 1 - no_ar / 0.08)
        pe = A.ET.projetar(P, (pos[0], pos[1], z_chao)); tp = A.ET.projetar(P, (pos[0], pos[1], z_chao + alt))
        x, y = tela(P, cam, pe); _, yt = tela(P, cam, tp); tam = y - yt
        if chave == "heitor":                                                # pulo: a sombra encolhe com a altura do salto
            k *= max(0.5, 1 + 4 * min(0.0, d["pose"].get("raiz", [0, 0])[1]))
        cv.drawOval(skia.Rect.MakeXYWH(x - larg / 2 * tam * k, y - 0.03 * tam, larg * tam * k, 0.06 * tam),
                    skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(alfa * k), 28, 20, 18), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.025 * tam)))


def tela(P, cam, p):
    return A.tela(P, cam, p, OW, OH)


def puff(cv, P, cam, pf):
    if pf["t"] > 0.6:
        return
    pe = A.ET.projetar(P, tuple(pf["pos"])); x, y = tela(P, cam, pe); s = cam.get("zoom", 1.0)
    r0 = 0.06 * P.f / pe[2] * s; u = pf["t"] / 0.6; rng = np.random.default_rng(9)
    for i in range(14):
        a = math.pi * (0.05 + 0.9 * i / 13); d = r0 * (0.3 + 1.4 * u) * rng.uniform(0.7, 1.2)
        cv.drawCircle(x + d * math.cos(a) * 1.6, y - d * math.sin(a) * 0.6, r0 * (0.18 + 0.25 * u),
                      skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(150 * (1 - u)), 235, 220, 195), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r0 * 0.12)))


def estado(n):
    t = T0 + n / FPS; pid, ini, fim, fn, ent = plano_em(t); tl = t - ini
    st = fn(tl); st.update(id=pid, tl=tl, entrada=ent, t=t)
    if st.get("cam"):                                                        # deriva: a câmera nunca fica parada (zoom +3,5 % no plano)
        st["cam"] = dict(st["cam"], zoom=st["cam"]["zoom"] * (1 + 0.035 * tl / (fim - ini)))
    return st


def quadro(n):
    st = estado(n); tl = st["tl"]; rosto_y = None
    if st.get("insert") == "olho":
        img = CP.insert_olho(dict(zoom=[st["zoom"], st["zoom"]], pupila=[st["pupila"], st["pupila"]]), 0.0)
    else:
        P = placa(st["placa"]); cam = st["cam"]
        des, hp, perto = desenhista(P, st)
        kw = dict(grade=GR, pesos=PESOS, semente_grao=n, cam=cam)
        if perto is not None:
            kw.update(personagem=des, profundidade_personagem=(hp[0][2] if hp else perto[2][2]))
        if st.get("heitor") is not None:
            kw["tom_personagem"] = X1.fazer_tom({"pe_mundo": list(map(float, st["heitor"]["pos"])), "altura_m": ALT})
            xt, yt = tela(P, cam, hp[1]); xp, yp = tela(P, cam, hp[0]); rosto_y = yt + (yp - yt) * 0.15
        kw.pop("cam"); img = np.ascontiguousarray(A.compor(P, cam, **kw))
        if st.get("sombra_gato"):
            sg = st["sombra_gato"]; img = CP.sombra_gato(img, dict(x=[sg["x"], sg["x"]], y=sg["y"], alt=[sg["alt"], sg["alt"]]), 0.0)
        # borrão de movimento da câmera (panorâmica rápida): desloca a mesma profundidade do alvo entre quadros
        if n > 0 and st["tl"] >= 1 / FPS and hp:
            ant = estado(n - 1); x0 = tela(P, ant["cam"], hp[0])[0]; x1 = tela(P, cam, hp[0])[0]
            dxp = abs(x1 - x0)
            if dxp > 6:
                k = int(min(41, dxp * 0.8)) | 1; img = cv2.blur(img, (k, 1))
        s = skia.Surface(OW, OH); cv = s.getCanvas(); cv.drawImage(CP._skimg(img), 0, 0)
        sombras(cv, P, cam, st)
        if st.get("poeira"):
            POEIRA.desenhar(cv, st["t"], cam.get("tx", 0), cam.get("ty", 0), cam.get("zoom", 1), forca=st["poeira"])
        if st.get("puff"):
            puff(cv, P, cam, st["puff"])
        if st.get("pata"):
            pt = st["pata"]; GATO.pata(cv, OW * pt["x"], OH * pt["y"], OH * pt["tam"], garras=pt["garras"])
        img = CP._snap(s)
    # transição de entrada
    ent = st["entrada"]
    if ent == "chicote" and tl < 0.13:
        kx = int(140 * (1 - tl / 0.13)) * 2 + 1; img = cv2.blur(img, (max(3, kx), 1))
    elif ent == "flash" and tl < 0.12:
        a = 0.85 * (1 - tl / 0.12); img = (img * (1 - a) + 255 * a).astype(np.uint8)
    tr = st.get("tremida")
    if tr and tr[0] <= tl <= tr[1]:
        rng = np.random.default_rng(n); amp = 0.014 * OW * (1 - (tl - tr[0]) / max(1e-3, tr[1] - tr[0]))
        Mt = np.float32([[1.03, 0, rng.uniform(-amp, amp) - 0.015 * OW], [0, 1.03, rng.uniform(-amp, amp) - 0.015 * OH]])
        img = cv2.warpAffine(img, Mt, (OW, OH), borderMode=cv2.BORDER_REFLECT)
    s = skia.Surface(OW, OH); cv = s.getCanvas(); cv.drawImage(CP._skimg(img), 0, 0)
    lg = next((l for l in CP.M["legendas"] if l["ini"] <= st["t"] < l["fim"]), None)
    if lg is not None and lg["ini"] >= T0 - 0.05:                            # só as legendas deste trecho da narração
        CP.legenda(cv, st["t"], rosto_y)
    CP.marca_dagua(cv)
    return CP._snap(s)


def segmento(n0, n1, saida):
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "pipe:0",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", str(saida)], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        ff.stdin.write(np.ascontiguousarray(quadro(n)).tobytes())
        if (n - n0) % 60 == 0:
            print(f"{saida.name}: {n - n0}/{n1 - n0}", flush=True)
    ff.stdin.close(); ff.wait()


def main():
    a = sys.argv; N = int(round(DUR * FPS))
    saida = P_ / "saida"; saida.mkdir(exist_ok=True)
    (saida / "mapa_fala_imagem.json").write_text(json.dumps(
        [dict(palavra=w, t=t, plano=p, acao=ac) for w, t, p, ac in MAPA], ensure_ascii=False, indent=1) + "\n")
    if "--png" in a:
        pasta = Path(a[a.index("--png") + 1]); pasta.mkdir(parents=True, exist_ok=True)
        for n in [int(x) for x in a[a.index("--quadros") + 1].split(",")]:
            cv2.imwrite(str(pasta / f"q{n:04d}.png"), cv2.cvtColor(quadro(n), cv2.COLOR_RGB2BGR))
        return
    if "--seg" in a:
        segmento(int(a[a.index("--de") + 1]), int(a[a.index("--ate") + 1]), Path(a[a.index("--seg") + 1])); return
    trab = int(os.environ.get("TRABALHADORES", "3")); tmp = P_ / "_cache" / "segmentos"; tmp.mkdir(parents=True, exist_ok=True)
    cortes = [round(N * i / trab) for i in range(trab + 1)]
    procs = [subprocess.Popen([sys.executable, __file__, "--seg", str(tmp / f"seg_{i}.mp4"), "--de", str(cortes[i]), "--ate", str(cortes[i + 1])],
                              env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")) for i in range(trab)]
    for p in procs:
        p.wait()
    for i in range(trab):
        nq = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries", "stream=nb_read_frames",
                                 "-of", "csv=p=0", str(tmp / f"seg_{i}.mp4")], capture_output=True, text=True).stdout.strip() or 0)
        if nq != cortes[i + 1] - cortes[i]:
            raise SystemExit(f"PARADO: seg_{i} tem {nq} quadros (esperado {cortes[i + 1] - cortes[i]})")
    (tmp / "lista.txt").write_text("".join(f"file '{tmp / f'seg_{i}.mp4'}'\n" for i in range(trab)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"), "-c", "copy",
                    str(P_ / "_cache" / "video_sem_audio.mp4")], check=True)
    print("ok:", P_ / "_cache" / "video_sem_audio.mp4")


if __name__ == "__main__":
    main()
