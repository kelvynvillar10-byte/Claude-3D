#!/usr/bin/env python3
"""EP02 — "E se sua namorada te desse um PS5 com GTA 6 instalado?" — decupagem, animação e composição.

Padrão de animação dinâmica aprovado (27/11/2026): cada plano é uma função do tempo local que devolve o ESTADO do quadro
(placa, câmera em movimento, atores com ação, luz da hora, tela da TV, grafismos). O mapa fala → imagem (palavra, instante,
plano, ação) fica em MAPA e vai para saida/mapa_fala_imagem.json. Visual SEM marca de terceiros: a narração cita o console
e o jogo (fala do diretor, como fã), mas na tela o videogame, o controle, o jogo e a cidade são genéricos, sem logotipo.

Uso: cenas_ep02.py [--png pasta --quadros 0,30,...]  |  [--seg arq --de N --ate M]  |  (sem argumentos: vídeo sem áudio)
"""
import copy, json, math, os, re, subprocess, sys
from pathlib import Path
import numpy as np, cv2, skia

AQUI = Path(__file__).resolve().parent; P_ = AQUI.parent; RAIZ = P_.parents[1]
for sub in ("", "cenografia/testes", "personagens/heitor/extensoes/x1_tom_de_luz"):
    sys.path.insert(0, str(RAIZ / sub))
sys.path.insert(0, str(AQUI))
import atores_ep02 as AE, graficos_ep02 as GF, placas_ep02 as PL                # noqa: E402
import e10_testes as ET                                                         # noqa: E402
import tom_de_luz as X1                                                         # noqa: E402
from cenografia.nucleo.compositor import Placa                                  # noqa: E402

AT, PO = AE.AT, AE.PO
J, D = AE.JUCA, AE.JAND
FPS = 30; OW, OH = 1080, 1920
NARR = RAIZ / "narracao" / "edicoes" / "ep02_narracao"
PAL = json.loads((NARR / "voz_palavras.json").read_text())
FIM_VOZ = PAL[-1]["fim"]; DUR = 88.4
S = PL.specs()
_PL = {}
V = np.asarray
suave, saida, lerp = AE.suave, AE.saida, AE.lerp


def placa(nome):
    if nome not in _PL:
        if len(_PL) >= int(os.environ.get("MAX_PLACAS", "3")):
            _PL.pop(next(iter(_PL)))
        _PL[nome] = Placa(PL.pasta(nome, S))
    return _PL[nome]


def w(palavra, n=1):
    """Instante (s) da n-ésima ocorrência de uma palavra na narração final."""
    k = 0
    for p in PAL:
        if p["w"].lower().strip(".,!?…") == palavra.lower():
            k += 1
            if k == n:
                return p["ini"]
    raise KeyError(palavra)


# ======================================================================= luz por hora do dia
HORAS = {   # pesos dos grupos de luz da placa (o sol não muda de lugar: muda força e cor) + exposição
    "tarde":     dict(pesos={"ceu": (0.55, "#ffe9c9"), "sol": 1.0, "artificial": 0.12}, exp=0.0),
    "fim_tarde": dict(pesos={"ceu": (0.45, "#ffb27a"), "sol": (0.55, "#ff9a5a"), "artificial": 0.55}, exp=-0.05),
    "noite":     dict(pesos={"ceu": (0.10, "#3a4f9a"), "sol": 0.0, "artificial": 0.95}, exp=-0.15),
    "madrugada": dict(pesos={"ceu": (0.05, "#2a3a7a"), "sol": 0.0, "artificial": (0.45, "#ffcf9a")}, exp=-0.35),
    "amanhecer": dict(pesos={"ceu": (0.55, "#ffb6c8"), "sol": (0.30, "#ff9ab0"), "artificial": 0.35}, exp=-0.05),
}
COR_TV = ["#5fb8ff", "#ff5fa8", "#ffb35f", "#7d5fff", "#5fffc0"]


def _mistura_hora(h0, h1, k):
    a, b = HORAS[h0]["pesos"], HORAS[h1]["pesos"]; out = {}
    for g in set(a) | set(b):
        va, vb = a.get(g, 0.0), b.get(g, 0.0)
        wa, ca = (va if isinstance(va, tuple) else (va, "#ffffff")); wb, cb = (vb if isinstance(vb, tuple) else (vb, "#ffffff"))
        c0 = np.array([int(ca[i:i + 2], 16) for i in (1, 3, 5)]); c1 = np.array([int(cb[i:i + 2], 16) for i in (1, 3, 5)])
        cc = (c0 * (1 - k) + c1 * k).astype(int)
        out[g] = (wa * (1 - k) + wb * k, "#%02x%02x%02x" % tuple(cc))
    return out, lerp(HORAS[h0]["exp"], HORAS[h1]["exp"], k)


def luz(hora, t=0.0, tv=0.0, para=None, k=0.0):
    pesos, exp = _mistura_hora(hora, para or hora, k)
    if tv > 0:   # a TV ilumina a sala com as cores do jogo (troca suave)
        i = int(t * 1.3) % len(COR_TV); f = (t * 1.3) % 1.0
        c0 = np.array([int(COR_TV[i][j:j + 2], 16) for j in (1, 3, 5)]); c1 = np.array([int(COR_TV[(i + 1) % 5][j:j + 2], 16) for j in (1, 3, 5)])
        cc = (c0 * (1 - suave(f)) + c1 * suave(f)).astype(int)
        pesos["efeito"] = (tv * (0.85 + 0.15 * math.sin(t * 9.0) * math.sin(t * 3.1)), "#%02x%02x%02x" % tuple(cc))
    else:
        pesos["efeito"] = 0.0
    grade = dict(ET.GRADE); grade["exposicao"] = grade.get("exposicao", 0.0) + exp
    return pesos, grade


# ======================================================================= o jogo (cidade genérica)
_JOGO = {}


def jogo(nome, t, W=1080, H=1920, carro=False, vel=None, missao=True, zoom0=1.0, zoom1=1.25, dur=2.0, tx=0.0, hora_k=0.0):
    """Quadro do 'jogo': placa da cidade (crepúsculo) com movimento de câmera + HUD do canal. Retrato 1080×1920."""
    chave = (nome, round(t * 15) / 15, carro, vel is not None, missao, zoom0, zoom1, dur, tx)
    if chave in _JOGO:
        return _JOGO[chave]
    t = chave[1]; P = placa(nome); k = min(1.0, t / dur)
    cam = {"zoom": lerp(zoom0, zoom1, saida(k)), "tx": tx * k}
    img = np.ascontiguousarray(P.compor(pesos={"ceu": 1.0, "sol": 1.0, "artificial": 1.4, "efeito": 0.0}, cam=cam,
                                        grade=dict(ET.T1.GRADE if hasattr(ET, "T1") else ET.GRADE, saturacao=1.35), semente_grao=int(t * 30)))
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.drawImage(GF.skimg(img), 0, 0)
    if carro:
        GF.linhas_velocidade(cv, t, W, H, 1.0, cy=H * 0.55)
        GF.carro_jogador(cv, W / 2, H * 0.78, 520, t)
    GF.hud(cv, t, W, H, velocidade=vel, missao_pct=3, escala=1.3, k_missao=1.0 if missao else 0.0)
    out = GF.snap(s)
    if len(_JOGO) > 40:
        _JOGO.pop(next(iter(_JOGO)))
    _JOGO[chave] = out
    return out


def faixa_tv(img):
    """Recorte 16:9 do quadro retrato do jogo (o que aparece na TV)."""
    h = int(img.shape[1] * 9 / 16); y0 = int(img.shape[0] * 0.42) - h // 2
    return cv2.resize(img[y0:y0 + h], (960, 540), interpolation=cv2.INTER_AREA)


def tv_conteudo(modo, t, k=0.0):
    if modo == "ligando":
        return GF.tela_ligando(t)
    if modo == "instalando":
        return GF.tela_instalacao(t, k)
    if modo == "jogo":
        return faixa_tv(jogo("G1_rua_baixa", t % 6.0, carro=True, vel=118 + 6 * math.sin(t * 2), missao=False, zoom0=1.0, zoom1=1.3, dur=6.0))
    if modo == "missao":
        return GF.tela_missao(t, 3, fundo=faixa_tv(jogo("G1_rua_baixa", 1.0, carro=False, missao=False)))
    return None


TV_CANTOS = [(-0.613, 2.128, 1.393), (0.613, 2.128, 1.393), (0.613, 2.128, 0.707), (-0.613, 2.128, 0.707)]
CONSOLE_RACK = (-0.42, 1.92, 0.5)                 # o console em pé sobre o rack (desenho 2D, sem marca)
PRATO = (0.12, -0.52, 0.42)


# ======================================================================= atores e posições
def ator(tr, t, **props):
    st = tr.estado(t); st.update(props); return st


def juca_sentado(Pc, vista, rosto="neutro", jogar=True, intensidade=1.0, pos=None, direcao=1):
    base = AE.base_jogando(J, intensidade) if jogar else AE.base_sentado(J)
    p0 = pos if pos is not None else {"frente": (0.0, -1.12, 0.0), "perfil": (0.0, -1.55, 0.0), "costas": (0.0, -1.62, 0.0),
                                      "tres_quartos": (0.0, -1.2, 0.0)}[vista]
    return AE.Trajeto(J, Pc, p0, vista, direcao, rosto=rosto, base=base)


# ======================================================================= planos
# Cada plano: (id, início, fim, função(tl, dur) → estado, entrada). Estado: placa, cam, atores, hora, tv, tela, extras.
def P01(tl, d):   # "E se sua namorada chegasse em casa": a Jandira entra pela porta com a caixa enorme
    Pc = placa("C5_porta"); dx, dz = AT.eixo_tela(Pc)
    tr = AE.Trajeto(D, Pc, V([-2.55, 0.75, 0.0]), "frente", 1, rosto="alegria", base=AE.maos_caixa(D))
    tr.faz(tipo="andar", t0=0.0, dur=d, vista="frente", eixo_vet=V([1.0, 0.0, 0.0]), sentido=1, bracos=AE.maos_caixa(D))
    st = ator(tr, tl, caixa=True)
    cam = AT.seguir(Pc, lambda s: tr.estado(s)["pos"] + [0, 0, 1.15], tl, 0.5, 0.42, lerp(1.0, 1.35, saida(tl / d)), atraso=0.25)
    return dict(placa="C5_porta", cam=cam, atores=[st], hora="tarde")


def P02(tl, d):   # "com uma surpresa que mudaria sua vida": zoom brusco na caixa, brilhos
    Pc = placa("C5_porta"); t = tl + 1.85
    tr = AE.Trajeto(D, Pc, V([-2.55, 0.75, 0.0]), "frente", 1, rosto="alegria", base=AE.maos_caixa(D))
    tr.faz(tipo="andar", t0=0.0, dur=2.6, vista="frente", eixo_vet=V([1.0, 0.0, 0.0]), sentido=1, bracos=AE.maos_caixa(D))
    tr.faz(tipo="parar", t0=2.6, dur=0.25)
    st = ator(tr, t, caixa=True, brilho_caixa=suave((tl - 0.3) / 0.6))
    k = saida(min(1, max(0, tl - (w("surpresa") - 1.85 - 0.05)) / 0.22))
    z = lerp(1.35, 2.3, k)
    cam = AT.seguir(Pc, lambda s: tr.estado(s)["pos"] + [0, 0, 0.75 * k + 1.15 * (1 - k)], t, 0.5, lerp(0.42, 0.5, k), z, atraso=0.0)
    return dict(placa="C5_porta", cam=cam, atores=[st], hora="tarde", tremida=(0.36, 0.6), brilhos_caixa=True)


def P03(tl, d):   # "para sempre?": o Juca no sofá vira a cabeça, curioso
    Pc = placa("C2_sofa"); tr = juca_sentado(Pc, "frente", "neutro", jogar=False)
    tr.faz(tipo="virar", t0=0.12, vistas=["tres_quartos"], direcao=-1, base=AE.base_sentado(J))
    tr.rosto(0.12, "surpresa", (-0.8, -0.1)).rosto(0.45, "pensativo", (-0.9, 0.0))
    st = ator(tr, tl)
    cam = AT.seguir(Pc, lambda s: V([0, -1.45, 1.15]), tl, 0.5, 0.40, lerp(1.25, 1.75, saida(tl / 0.3)), atraso=0.0)
    return dict(placa="C2_sofa", cam=cam, atores=[st], hora="tarde")


def _relax(vista, t, tl=0):
    p = PO.sentado(J, vista)
    p.update({"braco_d": -150, "antebraco_d": -120, "braco_e": -150, "antebraco_e": -120, "tronco": -8, "cabeca": -6})
    return p


def P04(tl, d):   # "Juca estava tranquilamente no sofá": relaxado, mãos atrás da cabeça, travelling
    Pc = placa("C3_lado"); tr = juca_sentado(Pc, "perfil", "sonolento", jogar=False)
    tr.faz(tipo="funcao", t0=0.0, fn=lambda v, t, tl_: AE.parado(J, v, t, base=_relax(v, t)), ease=0.01)
    tr.rosto(0.0, "convencido").rosto(0.9, "sonolento").rosto(1.4, "dormindo", None, {"boca": "o", "abertura": 0.5})
    st = ator(tr, tl)
    cam = AT.seguir(Pc, lambda s: V([0.0 + 0.25 * s, -1.5, 0.95]), tl, 0.5, 0.45, lerp(1.15, 1.3, suave(tl / d)), atraso=0.0)
    return dict(placa="C3_lado", cam=cam, atores=[st], hora="tarde")


def P05(tl, d):   # "quando ela apareceu segurando": ela atravessa a sala; a câmera acompanha
    Pc = placa("C1_geral")
    tr = AE.Trajeto(D, Pc, V([-2.1, 0.55, 0.0]), "perfil", 1, rosto="alegria", base=AE.maos_caixa(D))
    eixo = V([0.75, -0.66, 0.0]); eixo = eixo / np.linalg.norm(eixo)
    tr.faz(tipo="andar", t0=0.0, dur=d, vista="tres_quartos", eixo_vet=eixo, sentido=1, bracos=AE.maos_caixa(D))
    sj = juca_sentado(Pc, "tres_quartos", "surpresa", jogar=False, direcao=-1)
    sj.rosto(0.0, "neutro", (-0.7, 0)).rosto(0.55, "surpresa", (-0.9, -0.2))
    st = ator(tr, tl, caixa=True, direcao=-1)
    cam = AT.seguir(Pc, lambda s: 0.6 * (tr.estado(s)["pos"] + [0, 0, 1.0]) + 0.4 * V([0, -1.4, 0.9]), tl, 0.5, 0.48, lerp(1.3, 1.45, suave(tl / d)), atraso=0.3)
    return dict(placa="C1_geral", cam=cam, atores=[st, ator(sj, tl)], hora="tarde")


def P06(tl, d):   # "uma caixa enorme": ela entra no quadro com a caixa; zoom brusco
    Pc = placa("C2_sofa"); dx, _ = AT.eixo_tela(Pc)
    tr = AE.Trajeto(D, Pc, V([0.95, -1.3, 0.0]), "perfil", -1, rosto="alegria", base=AE.maos_caixa(D))
    tr.faz(tipo="andar", t0=0.0, dur=0.45, vista="perfil", eixo_vet=-dx * -1, sentido=1, direcao=1, bracos=AE.maos_caixa(D))
    tr.faz(tipo="virar", t0=0.45, vistas=["tres_quartos", "frente"], passo=0.08, direcao=1, base=AE.maos_caixa(D))
    sj = juca_sentado(Pc, "frente", "surpresa", jogar=False); sj.rosto(0.3, "surpresa", (0.6, -0.3))
    k = saida(min(1, max(0, tl - (w("enorme") - 7.5)) / 0.2))
    cam = AT.seguir(Pc, lambda s: V([0.45, -1.25, 1.0]), tl, 0.5, 0.48, lerp(1.0, 1.35, k), atraso=0.0)
    return dict(placa="C2_sofa", cam=cam, atores=[ator(sj, tl), ator(tr, tl, caixa=True)], hora="tarde", tremida=(0.39, 0.62))


def P07(tl, d):   # "Ao abrir, ele encontrou": a tampa abre, luz dourada no rosto dele
    Pc = placa("C2_sofa"); tr = juca_sentado(Pc, "frente", "surpresa", jogar=False)
    def abre(v, t, tl_):
        p = PO.sentado(J, v); p["tronco"] = 10 * suave(tl_ / 0.3)
        PO._ik_par(J, p, v, {"d": (-0.35, -1.6), "e": (0.35, -1.6)}, "aberta"); return p
    tr.faz(tipo="funcao", t0=0.0, fn=abre, ease=0.25)
    tr.rosto(0.0, "pensativo", (0, 0.6)).rosto(w("abrir") - 8.45 + 0.1, "surpresa", (0, 0.7)).rosto(1.0, "vidrado", (0, 0.5))
    ka = suave((tl - (w("abrir") - 8.45)) / 0.35)
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.0, 0.9]), tl, 0.5, 0.52, lerp(1.25, 1.6, suave(tl / d)), atraso=0.0)
    return dict(placa="C2_sofa", cam=cam, atores=[ator(tr, tl)], hora="tarde", caixa_mesa=dict(tampa=ka, brilho=ka), luz_caixa=ka)


def P08(tl, d):   # "um PlayStation 5 novinho em folha!": o videogame sobe da caixa (insert)
    return dict(insert=lambda t: GF.insert_console(t, tl / d), tremida=(0.0, 0.2))


def P09(tl, d):   # "Mas espera...": ela levanta o dedo, sorriso de quem guarda segredo
    Pc = placa("C1_geral")
    tr = AE.Trajeto(D, Pc, V([0.9, -0.6, 0.0]), "tres_quartos", 1, rosto="desconfiada")
    def dedo(v, t, tl_):
        p = AE.parado(D, v, t); p.update({"braco_d": 150, "antebraco_d": 35, "dedos_d": D.G.mao("apontar"), "mao_vista_d": "palma"}); return p
    tr.faz(tipo="funcao", t0=0.15, fn=dedo, ease=0.2)
    tr.rosto(0.0, "convencido", (-0.4, 0)).rosto(0.3, "desconfiada", (-0.6, 0))
    cam = AT.seguir(Pc, lambda s: V([0.9, -0.6, 1.4]), tl, 0.5, 0.42, lerp(1.6, 2.1, saida(tl / d)), atraso=0.0)
    sj = juca_sentado(Pc, "tres_quartos", "surpresa", jogar=False, direcao=-1)
    return dict(placa="C1_geral", cam=cam, atores=[ator(sj, tl), ator(tr, tl)], hora="tarde")


def P10(tl, d):   # "tinha mais uma surpresa!": a TV liga
    Pc = placa("C7_tv")
    cam = AT.seguir(Pc, lambda s: V([0.0, 2.1, 1.0]), tl, 0.5, 0.42, lerp(1.0, 1.2, saida(tl / d)), atraso=0.0)
    return dict(placa="C7_tv", cam=cam, atores=[], hora="tarde", tv=("ligando", tl, 0), tvluz=0.6 * suave(tl / 0.3), console_luz=1.0)


def P11(tl, d):   # "GTA 6 já estava instalado!": barra até 100 %, zoom na tela
    Pc = placa("C7_tv"); k = (tl) / (w("instalado") - 14.75 + 0.35)
    z = lerp(1.2, 1.75, saida(min(1, max(0, tl - (w("instalado") - 14.75 - 0.05)) / 0.25)))
    cam = AT.seguir(Pc, lambda s: V([0.0, 2.1, 1.05]), tl, 0.5, 0.42, z, atraso=0.0)
    return dict(placa="C7_tv", cam=cam, atores=[], hora="tarde", tv=("instalando", tl, k), tvluz=0.8, console_luz=1.0,
                tremida=(w("instalado") - 14.75, w("instalado") - 14.75 + 0.3))


def P12(tl, d):   # "Naquele instante,": close no rosto; os olhos se arregalam com a luz da TV
    Pc = placa("C2_sofa"); tr = juca_sentado(Pc, "frente", "surpresa", jogar=False)
    tr.rosto(0.0, "surpresa", (0, -0.1)).rosto(0.55, "vidrado", (0, -0.1))
    tr.faz(tipo="pose", t0=0.0, extra={"tronco": -6, "cabeca": -4}, ease=0.4)
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.35, 1.35]), tl, 0.5, 0.42, lerp(1.9, 2.6, suave(tl / d)), atraso=0.0)
    return dict(placa="C2_sofa", cam=cam, atores=[ator(tr, tl)], hora="tarde", tvluz=0.8)


def _levanta(v, t, tl_):
    k = suave(tl_ / 0.8); a = PO.sentado(J, v); b = J.H.pose_base(v)
    p = AT.misturar(a, b, k); p["tronco"] = p.get("tronco", 0) + 18 * math.sin(math.pi * k); return p


def P13(tl, d):   # "Juca descobriu o verdadeiro significado": ele se levanta devagar, maravilhado
    Pc = placa("C3_lado"); tr = juca_sentado(Pc, "perfil", "vidrado", jogar=False)
    tr.faz(tipo="funcao", t0=0.2, fn=_levanta, ease=0.05)
    tr.faz(tipo="pose", t0=1.3, extra={"braco_d": -60, "antebraco_d": -80, "braco_e": -50, "antebraco_e": -70, "cabeca": -8}, ease=0.5)
    tr.rosto(0.0, "vidrado").rosto(1.2, "alegria", (0.5, -0.4))
    cam = AT.seguir(Pc, lambda s: tr.estado(s)["pos"] + [0, 0, lerp(0.95, 1.35, suave((s - 0.2) / 1.0))], tl, 0.5, 0.42, lerp(1.25, 1.45, suave(tl / d)), atraso=0.25)
    return dict(placa="C3_lado", cam=cam, atores=[ator(tr, tl)], hora="tarde", tvluz=0.8)


def P14(tl, d):   # "felicidade": pulo de comemoração com os punhos para cima
    Pc = placa("C1_geral")
    tr = AE.Trajeto(J, Pc, V([0.0, -1.0, 0.0]), "frente", 1, rosto="alegria")
    tr.faz(tipo="pulo", t0=0.05, dur=0.6, altura=0.8, punhos=True)
    tr.faz(tipo="pose", t0=0.65, extra={"braco_d": 150, "antebraco_d": 25, "braco_e": -150, "antebraco_e": -25}, ease=0.15)
    tr.rosto(0.0, "alegria", None, {"abertura": 0.9})
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.0, 1.0]), tl, 0.5, 0.5, lerp(1.55, 1.75, suave(tl / d)), atraso=0.0)
    return dict(placa="C1_geral", cam=cam, atores=[ator(tr, tl)], hora="tarde", tvluz=0.8, confete=tl, tremida=(0.62, 0.9))


def P15(tl, d):   # "Seus olhos brilharam": close nos olhos com estrelas
    Pc = placa("C2_sofa")
    tr = AE.Trajeto(J, Pc, V([0.0, -1.0, 0.0]), "frente", 1, rosto="vidrado")
    tr.rosto(0.0, "vidrado", (0, -0.2), {"pupila": 0.25})
    st = ator(tr, tl)
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.0, 1.6]), tl, 0.5, 0.42, lerp(2.4, 3.0, saida(tl / d)), atraso=0.0)
    return dict(placa="C2_sofa", cam=cam, atores=[st], hora="tarde", tvluz=0.8, estrelas_olhos=tl)


def P16(tl, d):   # "seu coração acelerou": coração e 72 → 140 BPM
    return dict(insert=lambda t: GF.insert_coracao(t, tl / d))


def _abraco(P, v, t, tl_):
    p = AE.parado(P, v, t); yc = -(P.H.PROP["ombro"] - 0.45)
    alvos = {"d": (0.42, yc + 0.05), "e": (0.62, yc - 0.05)} if v == "perfil" else {"d": (-0.30, yc), "e": (0.30, yc)}
    PO._ik_par(P, p, v, alvos, "segurar"); p["cabeca"] = 8 + 4 * math.sin(t * 5); p["tronco"] = 4 * math.sin(t * 2.5)
    return p


def P17(tl, d):   # "e ele abraçou o videogame": abraço apertado, balançando
    Pc = placa("C3_lado")
    tr = AE.Trajeto(J, Pc, V([0.0, -1.2, 0.0]), "perfil", 1, rosto="alegria")
    tr.faz(tipo="funcao", t0=0.0, fn=lambda v, t, tl_: _abraco(J, v, t, tl_), ease=0.2)
    tr.rosto(0.0, "alegria", None, {"palp_sup": 1.0, "sorriso": 1.0}).rosto(0.9, "dormindo", None, {"boca": "sorriso_aberto", "abertura": 0.4, "sorriso": 1.0})
    cam = AT.seguir(Pc, lambda s: tr.estado(s)["pos"] + [0, 0, 1.35], tl, 0.5, 0.42, lerp(1.6, 1.95, suave(tl / d)), atraso=0.0)
    return dict(placa="C3_lado", cam=cam, atores=[ator(tr, tl, console_abraco=True)], hora="tarde", tvluz=0.8, coracoes=tl)


def P18(tl, d):   # "como se tivesse encontrado um tesouro perdido"
    return dict(insert=lambda t: GF.insert_tesouro(t, tl / d))


def P19(tl, d):   # "Ele simplesmente não": ergue o videogame e balança a cabeça, sem acreditar
    Pc = placa("C2_sofa")
    tr = AE.Trajeto(J, Pc, V([0.0, -1.0, 0.0]), "frente", 1, rosto="surpresa")
    def ergue(v, t, tl_):
        p = AE.parado(J, v, t); PO._ik_par(J, p, v, {"d": (-0.22, -(J.H.PROP["topo_cabeca"] + 0.25)), "e": (0.22, -(J.H.PROP["topo_cabeca"] + 0.25))}, "segurar")
        p["cabeca"] = 9 * math.sin(tl_ * 14); return p
    tr.faz(tipo="funcao", t0=0.0, fn=ergue, ease=0.25)
    tr.rosto(0.0, "surpresa", (0, -0.9)).rosto(0.6, "alegria", (0, -0.9))
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.0, 1.55]), tl, 0.5, 0.45, lerp(1.35, 1.6, suave(tl / d)), atraso=0.0)
    return dict(placa="C2_sofa", cam=cam, atores=[ator(tr, tl, console_erguido=True)], hora="tarde", tvluz=0.8)


def P20(tl, d):   # "conseguia acreditar naquilo!": a Jandira ri e bate palmas
    Pc = placa("C5_porta")
    tr = AE.Trajeto(D, Pc, V([-1.3, 0.2, 0.0]), "tres_quartos", 1, rosto="alegria")
    def palmas(v, t, tl_):
        p = AE.parado(D, v, t); ab = 0.08 + 0.10 * abs(math.sin(tl_ * 9)); yc = -(D.H.PROP["ombro"] - 0.55)
        PO._ik_par(D, p, v, {"d": (-ab, yc), "e": (ab, yc)}, "aberta"); p["cabeca"] = 5 * math.sin(tl_ * 6); return p
    tr.faz(tipo="funcao", t0=0.0, fn=palmas, ease=0.15)
    tr.rosto(0.0, "alegria", None, {"palp_sup": 0.6, "abertura": 0.8})
    cam = AT.seguir(Pc, lambda s: V([-1.3, 0.2, 1.35]), tl, 0.5, 0.45, lerp(1.4, 1.65, suave(tl / d)), atraso=0.0)
    return dict(placa="C5_porta", cam=cam, atores=[ator(tr, tl)], hora="tarde")


def P21(tl, d):   # "Juca ligou o console": ele entra, aperta o botão; a luz azul acende e a TV acorda
    Pc = placa("C7_tv"); dx, _ = AT.eixo_tela(Pc)
    tr = AE.Trajeto(J, Pc, V([0.6, 1.55, 0.0]), "perfil", -1, rosto="alegria")
    tr.faz(tipo="andar", t0=0.0, dur=0.45, vista="perfil", eixo_vet=-dx, sentido=1, direcao=-1)
    def aperta(v, t, tl_):
        p = AE.parado(J, v, t); p["tronco"] = 22; ik = (0.55, -0.85 + 0.03 * math.sin(tl_ * 20) * (tl_ < 0.3))
        PO._ik_par(J, p, v, {"d": ik}, "apontar"); return p
    tr.faz(tipo="funcao", t0=0.45, fn=aperta, ease=0.15)
    on = tl > (w("ligou") - 30.9 + 0.12)
    cam = AT.seguir(Pc, lambda s: V([-0.2, 1.9, 0.75]), tl, 0.5, 0.5, lerp(1.25, 1.45, suave(tl / d)), atraso=0.0)
    return dict(placa="C7_tv", cam=cam, atores=[ator(tr, tl)], hora="tarde", tv=("ligando", tl, 0) if on else None,
                tvluz=0.6 if on else 0.0, console_luz=1.0 if on else 0.0)


def P22(tl, d):   # "pegou o controle": pega o controle na mesa e pula no sofá
    Pc = placa("C1_geral")
    tr = AE.Trajeto(J, Pc, V([0.45, -0.95, 0.0]), "tres_quartos", -1, rosto="alegria")
    def pula(v, t, tl_):
        k = suave(tl_ / 0.55); a = J.H.pose_base(v); b = PO.jogando(J, v, t)[0]
        p = AT.misturar(a, b, k); r = list(p["raiz"]); r[1] -= 0.9 * math.sin(math.pi * min(1, tl_ / 0.55)); p["raiz"] = r; return p
    tr.faz(tipo="funcao", t0=0.1, fn=pula, ease=0.02)
    st = ator(tr, tl); k = suave((tl - 0.1) / 0.55)
    st["pos"] = V([0.45, -0.95, 0.0]) * (1 - k) + V([0.0, -1.2, 0.0]) * k
    cam = AT.seguir(Pc, lambda s: V([0.2, -1.1, 0.9]), tl, 0.5, 0.5, lerp(1.6, 1.8, suave(tl / d)), atraso=0.0)
    return dict(placa="C1_geral", cam=cam, atores=[dict(st, controle=k > 0.5)], hora="tarde", tvluz=0.8, tremida=(0.62, 0.85))


def P23(tl, d):   # "e começou sua aventura em Vice City": por cima do ombro, a câmera mergulha na TV
    Pc = placa("C4_ombro"); tr = juca_sentado(Pc, "costas", None, jogar=True)
    z = lerp(1.0, 2.6, suave((tl - 0.4) / (d - 0.4)) ** 1.6)
    cam = AT.seguir(Pc, lambda s: V([0.0, 2.13, 1.05]), tl, 0.5, lerp(0.40, 0.45, suave(tl / d)), z, atraso=0.0)
    return dict(placa="C4_ombro", cam=cam, atores=[ator(tr, tl, controle=True)], hora="tarde", tv=("jogo", tl, 0), tvluz=0.9)


def P24(tl, d):   # "Cada carro": dentro do jogo, o carro acelera
    return dict(insert=lambda t: jogo("G1_rua_baixa", tl + 0.5, carro=True, vel=96 + 30 * suave(tl / d), zoom0=1.05, zoom1=1.35, dur=1.5))


def P25(tl, d):   # "cada rua": a rua vista do alto
    return dict(insert=lambda t: jogo("G2_rua_alta", tl, zoom0=1.0, zoom1=1.25, dur=d, tx=1.2))


def P26(tl, d):   # "e cada detalhe do jogo": as fachadas de perto
    return dict(insert=lambda t: jogo("G3_calcada", tl, zoom0=1.15, zoom1=1.6, dur=d, tx=-0.6))


def P27(tl, d):   # "pareciam incríveis.": o Juca vidrado, iluminado pela TV
    Pc = placa("C2_sofa"); tr = juca_sentado(Pc, "frente", "vidrado", intensidade=1.2)
    tr.rosto(0.0, "vidrado", (0, -0.1), {"abertura": 0.6}).rosto(1.1, "vidrado", (0, -0.1), {"abertura": 0.95})
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.3, 1.1]), tl, 0.5, 0.45, lerp(1.45, 1.85, suave(tl / d)), atraso=0.0)
    return dict(placa="C2_sofa", cam=cam, atores=[ator(tr, tl, controle=True)], hora="tarde", tvluz=1.0)


def P28(tl, d):   # "Ele estava tão impressionado": de perfil, inclinado, apertando os botões
    Pc = placa("C3_lado"); tr = juca_sentado(Pc, "perfil", "vidrado", intensidade=1.8)
    tr.faz(tipo="pose", t0=0.0, extra={"tronco": -16, "cabeca": -6}, ease=0.6)
    cam = AT.seguir(Pc, lambda s: V([0.15 + 0.15 * s, -1.5, 1.05]), tl, 0.5, 0.45, lerp(1.35, 1.55, suave(tl / d)), atraso=0.0)
    return dict(placa="C3_lado", cam=cam, atores=[ator(tr, tl, controle=True)], hora="tarde", tvluz=1.0)


def P29(tl, d):   # "que nem percebeu o tempo passando.": time-lapse — a luz muda, a Jandira passa rápido
    Pc = placa("C1_geral"); tr = juca_sentado(Pc, "tres_quartos", "vidrado", direcao=-1)
    k = suave(tl / d)
    td = AE.Trajeto(D, Pc, V([-2.1, 0.4, 0.0]), "perfil", 1, rosto="neutro")
    eixo = V([1.0, -0.25, 0.0]); td.faz(tipo="andar", t0=0.0, dur=d, vista="perfil", eixo_vet=eixo / np.linalg.norm(eixo), sentido=1)
    sd = ator(td, tl * 3.0, fantasma=0.55)
    cam = AT.seguir(Pc, lambda s: V([-0.3, -0.6, 1.0]), tl, 0.5, 0.48, lerp(1.25, 1.15, suave(tl / d)), atraso=0.0)
    h = int(16 + 2 * k); m = int((2 * k * 60) % 60)
    return dict(placa="C1_geral", cam=cam, atores=[ator(tr, tl * 3, controle=True), sd], hora="tarde", hora_para="fim_tarde", hora_k=k,
                tvluz=1.0, relogio=(f"{h:02d}:{m:02d}", 1.0), sombras_correm=k)


def P30(tl, d):   # "Duas horas depois,"
    Pc = placa("C2_sofa"); tr = juca_sentado(Pc, "frente", "vidrado")
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.3, 1.0]), tl, 0.5, 0.52, lerp(1.2, 1.4, suave(tl / d)), atraso=0.0)
    return dict(placa="C2_sofa", cam=cam, atores=[ator(tr, tl, controle=True)], hora="fim_tarde", tvluz=1.0,
                cartela=("2", "HORAS", "DEPOIS", tl / 0.35), relogio=("18:00", tl / 0.3))


def P31(tl, d):   # "a namorada percebeu que ele ainda estava jogando": ela na porta, de braços cruzados
    Pc = placa("C5_porta")
    tr = AE.Trajeto(D, Pc, V([-2.5, 0.75, 0.0]), "frente", 1, rosto="desconfiada", base=lambda v, t: PO.bracos_cruzados(D, v) if v == "frente" else None)
    tr.faz(tipo="andar", t0=0.9, dur=0.9, vista="frente", eixo_vet=V([1.0, 0.0, 0.0]), sentido=1)
    tr.faz(tipo="parar", t0=1.8, dur=0.3)
    tr.faz(tipo="funcao", t0=1.85, fn=lambda v, t, tl_: AE.parado(D, v, t, base=PO.bracos_cruzados(D, v)), ease=0.25)
    tr.rosto(0.0, "desconfiada", (0.6, 0.1)).rosto(1.9, "irritada", (0.7, 0.2))
    cam = AT.seguir(Pc, lambda s: tr.estado(s)["pos"] + [0, 0, 1.3], tl, 0.5, 0.42, lerp(1.3, 1.7, suave(tl / d)), atraso=0.3)
    return dict(placa="C5_porta", cam=cam, atores=[ator(tr, tl)], hora="fim_tarde")


def P32(tl, d):   # "Cinco horas depois,": o prato quente na mesa, noite
    Pc = placa("C6_mesa"); tr = juca_sentado(Pc, "frente", "vidrado")
    cam = AT.seguir(Pc, lambda s: V([0.12, -0.52, 0.45]), tl, 0.5, 0.68, lerp(1.0, 1.2, suave(tl / d)), atraso=0.0)
    return dict(placa="C6_mesa", cam=cam, atores=[ator(tr, tl, controle=True, desfoque=9)], hora="noite", tvluz=1.0,
                cartela=("5", "HORAS", "DEPOIS", tl / 0.35), relogio=("21:00", tl / 0.3), vapor=1.0)


def P33(tl, d):   # "a comida já estava fria.": o vapor some, o termômetro cai
    Pc = placa("C6_mesa"); tr = juca_sentado(Pc, "frente", "vidrado")
    k = suave(tl / (d * 0.8))
    cam = AT.seguir(Pc, lambda s: V([0.12, -0.52, 0.43]), tl, 0.5, 0.62, lerp(1.25, 1.75, suave(tl / d)), atraso=0.0)
    return dict(placa="C6_mesa", cam=cam, atores=[ator(tr, tl, controle=True, desfoque=12)], hora="noite", tvluz=1.0,
                vapor=1 - k, termometro=(lerp(65, 22, k), min(1, tl / 0.3)))


def P34(tl, d):   # "Dez horas depois,": madrugada, só a TV e o abajur
    Pc = placa("C1_geral"); tr = juca_sentado(Pc, "tres_quartos", "vidrado", direcao=-1)
    tr.rosto(0.0, "vidrado", None, {"olheira": 0.6})
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.3, 0.9]), tl, 0.5, 0.52, lerp(1.1, 1.3, suave(tl / d)), atraso=0.0)
    return dict(placa="C1_geral", cam=cam, atores=[ator(tr, tl, controle=True)], hora="madrugada", tvluz=1.4,
                cartela=("10", "HORAS", "DEPOIS", tl / 0.35), relogio=("02:00", tl / 0.3))


def P35(tl, d):   # "Juca continuava exatamente no mesmo lugar.": rótulo 0 m
    Pc = placa("C3_lado"); tr = juca_sentado(Pc, "perfil", "vidrado", intensidade=0.8)
    tr.rosto(0.0, "vidrado", None, {"olheira": 0.75, "barba": 0.6})
    k = (tl - (w("exatamente") - 51.85)) / 0.35
    cam = AT.seguir(Pc, lambda s: V([0.1, -1.5, 1.0]), tl, 0.5, 0.48, lerp(1.25, 1.55, suave(tl / d)), atraso=0.0)
    return dict(placa="C3_lado", cam=cam, atores=[ator(tr, tl, controle=True)], hora="madrugada", tvluz=1.4,
                rotulo_juca=("0 m", "SAIU DO LUGAR", k))


def P36(tl, d):   # "O sofá já parecia ter se tornado sua nova residência oficial": recuo, placa de residência
    Pc = placa("C2_sofa"); tr = juca_sentado(Pc, "frente", "vidrado", intensidade=0.8)
    tr.rosto(0.0, "vidrado", None, {"olheira": 0.8, "barba": 0.75})
    z = lerp(2.0, 1.0, saida(tl / 1.6))
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.35, 1.05]), tl, 0.5, 0.45, z, atraso=0.0)
    k = (tl - (w("residência") - 54.65)) / 0.35
    return dict(placa="C2_sofa", cam=cam, atores=[ator(tr, tl, controle=True)], hora="madrugada", tvluz=1.4, lixo=min(1, tl / 1.5),
                residencia=k)


def P37(tl, d):   # "Quando amanheceu,": o dia nasce na janela
    Pc = placa("C1_geral"); tr = juca_sentado(Pc, "tres_quartos", "vidrado", direcao=-1)
    tr.rosto(0.0, "vidrado", None, {"olheira": 1.0, "barba": 1.0})
    k = suave(tl / d)
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.6, 1.3]), tl, 0.5, 0.42, lerp(1.0, 1.2, k), atraso=0.0)
    return dict(placa="C1_geral", cam=cam, atores=[ator(tr, tl, controle=True)], hora="madrugada", hora_para="amanhecer", hora_k=k, tvluz=1.0,
                relogio=("06:12", tl / 0.3))


def P38(tl, d):   # "Juca ainda estava jogando.": barba e olheiras, olho tremendo
    Pc = placa("C2_sofa"); tr = juca_sentado(Pc, "frente", "vidrado", intensidade=0.7)
    e = {"olheira": 1.0, "barba": 1.0, "palp_sup": 0.32 + 0.1 * (math.sin(tl * 23) > 0.6)}
    tr.rosto(0.0, "vidrado", (0, -0.1), e)
    cam = AT.seguir(Pc, lambda s: V([0.0, -1.3, 1.3]), tl, 0.5, 0.42, lerp(1.9, 2.5, suave(tl / d)), atraso=0.0)
    return dict(placa="C2_sofa", cam=cam, atores=[ator(tr, tl, controle=True)], hora="amanhecer", tvluz=1.0)


def P39(tl, d):   # "A namorada começou a perceber que aquele presente": ela acorda, se espreguiça e para
    Pc = placa("C5_porta")
    tr = AE.Trajeto(D, Pc, V([-2.45, 0.75, 0.0]), "frente", 1, rosto="sonolento")
    def espreguica(v, t, tl_):
        p = AE.parado(D, v, t); k = math.sin(math.pi * min(1, tl_ / 1.0))
        p.update({"braco_d": 165 * k, "antebraco_d": 30 * k, "braco_e": -165 * k, "antebraco_e": -30 * k, "tronco": 6 * k}); return p
    tr.faz(tipo="funcao", t0=0.0, fn=espreguica, ease=0.1)
    tr.faz(tipo="pose", t0=1.05, extra={"braco_d": 20, "braco_e": -20}, ease=0.2)
    tp = w("perceber") - 61.3
    tr.rosto(0.0, "sonolento", None, {"boca": "o", "abertura": 0.8}).rosto(tp, "surpresa", (0.7, 0.1)).rosto(tp + 0.6, "preocupacao", (0.7, 0.1))
    cam = AT.seguir(Pc, lambda s: V([-2.45, 0.75, 1.25]), tl, 0.5, 0.42, lerp(1.4, 1.9, suave((tl - tp) / 0.3)), atraso=0.0)
    return dict(placa="C5_porta", cam=cam, atores=[ator(tr, tl)], hora="amanhecer")


def P40(tl, d):   # "talvez tivesse sido um dos maiores erros da sua vida.": mão na testa, zoom brusco
    Pc = placa("C1_geral")
    tr = AE.Trajeto(D, Pc, V([0.95, -0.55, 0.0]), "tres_quartos", 1, rosto="preocupacao")
    def testa(v, t, tl_):
        p = AE.parado(D, v, t); PO._ik_par(D, p, v, {"d": (-0.05, -(D.H.PROP["topo_cabeca"] - 0.35))}, "aberta"); p["cabeca"] = -6; return p
    te = w("erros") - 63.9
    tr.faz(tipo="funcao", t0=te - 0.25, fn=testa, ease=0.2)
    tr.rosto(0.0, "preocupacao", (-0.6, 0.1)).rosto(te, "triste", None, {"palp_sup": 1.0})
    sj = juca_sentado(Pc, "tres_quartos", "vidrado", direcao=-1); sj.rosto(0, "vidrado", None, {"olheira": 1.0, "barba": 1.0})
    k = saida(min(1, max(0, tl - te + 0.05) / 0.2))
    cam = AT.seguir(Pc, lambda s: V([0.95, -0.55, 1.0 + 0.45 * k]), tl, 0.5, 0.45, lerp(1.35, 2.3, k), atraso=0.0)
    return dict(placa="C1_geral", cam=cam, atores=[ator(sj, tl, controle=True), ator(tr, tl)], hora="amanhecer", tvluz=1.0,
                tremida=(te, te + 0.35), dessatura=0.6 * k)


def P41(tl, d):   # "Afinal, ela queria agradar o namorado...": lembrança (sépia) da chegada com a caixa
    st = P01(tl * 0.8, 1.85 * 1.2); st["sepia"] = True; return st


def P42(tl, d):   # "Mas acabou criando um verdadeiro morador de Vice City!": o Juca andando dentro do jogo
    Pc = placa("G3_calcada")
    tr = AE.Trajeto(J, Pc, V([-5.05, 6.5, 0.15]), "frente", 1, rosto="vidrado")
    tr.faz(tipo="andar", t0=0.0, dur=d, vista="frente", eixo_vet=V([0.0, -1.0, 0.0]), sentido=1)
    tr.rosto(0.0, "vidrado", None, {"olheira": 1.0, "barba": 1.0, "abertura": 0.7})
    cam = AT.seguir(Pc, lambda s: tr.estado(s)["pos"] + [0, 0, 1.2], tl, 0.5, 0.45, lerp(1.3, 1.6, suave(tl / d)), atraso=0.3)
    return dict(placa="G3_calcada", cam=cam, atores=[ator(tr, tl, controle=True)], hora="cidade", hud=True)


def P43(tl, d):   # "E o mais impressionante?": aproximação lenta por cima do ombro
    Pc = placa("C4_ombro"); tr = juca_sentado(Pc, "costas", None, intensidade=0.7)
    cam = AT.seguir(Pc, lambda s: V([0.0, 2.13, 1.05]), tl, 0.5, 0.42, lerp(1.05, 1.5, suave(tl / d)), atraso=0.0)
    return dict(placa="C4_ombro", cam=cam, atores=[ator(tr, tl, controle=True)], hora="amanhecer", tv=("jogo", tl + 3, 0), tvluz=1.0)


def P44(tl, d):   # "Juca ainda estava na primeira missão!": MISSÃO 1 · 3 %
    Pc = placa("C7_tv"); tp = w("primeira") - 73.95
    z = lerp(1.15, 1.9, saida(min(1, max(0, tl - tp) / 0.22)))
    cam = AT.seguir(Pc, lambda s: V([0.0, 2.1, 1.05]), tl, 0.5, 0.42, z, atraso=0.0)
    return dict(placa="C7_tv", cam=cam, atores=[], hora="amanhecer", tv=("missao", tl, 0), tvluz=1.0, console_luz=1.0,
                tremida=(tp, tp + 0.3), rotulo_tv=("3 %", "DA MISSÃO 1", (tl - tp - 0.2) / 0.35))


def P45(tl, d):   # "Agora imagine receber um presente desses...": a sala inteira, recuo lento
    Pc = placa("C1_geral"); sj = juca_sentado(Pc, "tres_quartos", "vidrado", direcao=-1)
    sj.rosto(0, "vidrado", None, {"olheira": 1.0, "barba": 1.0})
    tr = AE.Trajeto(D, Pc, V([1.0, -0.5, 0.0]), "tres_quartos", -1, rosto="irritada",
                    base=lambda v, t: PO.bracos_cruzados(D, "frente") if v == "frente" else None)
    tr.faz(tipo="virar", t0=0.6, vistas=["frente"], direcao=1, base=lambda v, t: PO.bracos_cruzados(D, "frente"))
    cam = AT.seguir(Pc, lambda s: V([0.4, -1.0, 1.0]), tl, 0.5, 0.48, lerp(1.6, 1.15, saida(tl / d)), atraso=0.0)
    return dict(placa="C1_geral", cam=cam, atores=[ator(sj, tl, controle=True), ator(tr, tl)], hora="amanhecer", tvluz=1.0)


def P46(tl, d):   # "Você conseguiria desligar o videogame": o dedo vai e volta do botão
    Pc = placa("C7_tv")
    tr = AE.Trajeto(J, Pc, V([0.05, 1.55, 0.0]), "perfil", -1, rosto="preocupacao")
    def hesita(v, t, tl_):
        p = AE.parado(J, v, t); p["tronco"] = 18; dd = 0.12 * (0.5 + 0.5 * math.sin(tl_ * 6.5))
        PO._ik_par(J, p, v, {"d": (0.42 + dd, -0.88)}, "apontar"); return p
    tr.faz(tipo="funcao", t0=0.0, fn=hesita, ease=0.2)
    tr.rosto(0.0, "preocupacao", None, {"olheira": 1.0, "barba": 1.0})
    cam = AT.seguir(Pc, lambda s: V([-0.25, 1.85, 0.7]), tl, 0.5, 0.5, lerp(1.4, 1.75, suave(tl / d)), atraso=0.0)
    return dict(placa="C7_tv", cam=cam, atores=[ator(tr, tl)], hora="amanhecer", tv=("jogo", tl + 5, 0), tvluz=1.0, console_luz=1.0)


def P47(tl, d):   # "para dar atenção à sua namorada?": ela olha para nós, sobrancelha erguida, pé batendo
    Pc = placa("C5_porta")
    tr = AE.Trajeto(D, Pc, V([-1.6, 0.35, 0.0]), "frente", 1, rosto="desconfiada",
                    base=lambda v, t: PO.bracos_cruzados(D, "frente"))
    tr.faz(tipo="funcao", t0=0.0, fn=lambda v, t, tl_: dict(AE.parado(D, v, t, base=PO.bracos_cruzados(D, "frente")),
                                                            canela_d=-14 * max(0, math.sin(tl_ * 12)), pe_d=10 * max(0, math.sin(tl_ * 12))), ease=0.1)
    tr.rosto(0.0, "desconfiada", (0.0, 0.0))
    cam = AT.seguir(Pc, lambda s: V([-1.6, 0.35, 1.35]), tl, 0.5, 0.42, lerp(1.6, 2.0, suave(tl / d)), atraso=0.0)
    return dict(placa="C5_porta", cam=cam, atores=[ator(tr, tl)], hora="amanhecer")


def P48(tl, d):   # "Ou também desapareceria da vida real para morar em Vice City?": sugado para dentro da TV
    Pc = placa("C4_ombro"); tr = juca_sentado(Pc, "costas", None, intensidade=0.7)
    k = suave((tl - 0.4) / (d - 0.6))
    st = ator(tr, tl, controle=True, sugado=k)
    cam = AT.seguir(Pc, lambda s: V([0.0, 2.13, 1.05]), tl, 0.5, 0.42, lerp(1.0, 1.35, k), atraso=0.0)
    return dict(placa="C4_ombro", cam=cam, atores=[st], hora="amanhecer", tv=("jogo", tl + 8, 0), tvluz=1.0 + 1.0 * k, espiral=k)


def P49(tl, d):   # cartela final: "Comenta aí" + "Segue aí"
    return dict(insert=lambda t: GF.cartela_final(t, tl / d))


def _c(pal, n=1, ant=0.08):
    return round(w(pal, n) - ant, 3)


PLANOS = [  # (id, início, fim, função, entrada)
    ("P01", 0.00, 1.85, P01, None), ("P02", 1.85, 3.55, P02, "corte"), ("P03", 3.55, 4.40, P03, "chicote"),
    ("P04", 4.40, 6.15, P04, "corte"), ("P05", 6.15, 7.50, P05, "corte"), ("P06", 7.50, 8.45, P06, "chicote"),
    ("P07", 8.45, 9.85, P07, "corte"), ("P08", 9.85, 12.00, P08, "flash"), ("P09", 12.00, 13.25, P09, "corte"),
    ("P10", 13.25, 14.75, P10, "chicote"), ("P11", 14.75, 16.90, P11, "corte"), ("P12", 16.90, 18.30, P12, "corte"),
    ("P13", 18.30, 20.85, P13, "corte"), ("P14", 20.85, 21.95, P14, "corte"), ("P15", 21.95, 23.20, P15, "corte"),
    ("P16", 23.20, 24.35, P16, "flash"), ("P17", 24.35, 25.75, P17, "corte"), ("P18", 25.75, 28.20, P18, "corte"),
    ("P19", 28.20, 29.40, P19, "corte"), ("P20", 29.40, 30.90, P20, "corte"), ("P21", 30.90, 32.35, P21, "chicote"),
    ("P22", 32.35, 33.30, P22, "corte"), ("P23", 33.30, 35.25, P23, "corte"), ("P24", 35.25, 36.05, P24, "flash"),
    ("P25", 36.05, 36.95, P25, "chicote"), ("P26", 36.95, 38.25, P26, "chicote"), ("P27", 38.25, 39.90, P27, "corte"),
    ("P28", 39.90, 41.65, P28, "corte"), ("P29", 41.65, 43.80, P29, "corte"), ("P30", 43.80, 45.05, P30, "corte"),
    ("P31", 45.05, 47.75, P31, "chicote"), ("P32", 47.75, 49.15, P32, "corte"), ("P33", 49.15, 50.65, P33, "corte"),
    ("P34", 50.65, 51.85, P34, "corte"), ("P35", 51.85, 54.65, P35, "corte"), ("P36", 54.65, 58.45, P36, "corte"),
    ("P37", 58.45, 59.70, P37, "corte"), ("P38", 59.70, 61.30, P38, "corte"), ("P39", 61.30, 63.90, P39, "chicote"),
    ("P40", 63.90, 66.80, P40, "corte"), ("P41", 66.80, 69.60, P41, "fusao"), ("P42", 69.60, 72.30, P42, "flash"),
    ("P43", 72.30, 73.95, P43, "corte"), ("P44", 73.95, 76.15, P44, "corte"), ("P45", 76.15, 78.70, P45, "corte"),
    ("P46", 78.70, 80.60, P46, "corte"), ("P47", 80.60, 82.45, P47, "chicote"), ("P48", 82.45, 85.40, P48, "corte"),
    ("P49", 85.40, DUR, P49, "flash"),
]

MAPA = [  # palavra (como falada), plano e a ação que está na tela naquele instante
    ("namorada", "P01", "a Jandira entra pela porta com a caixa enorme; a câmera avança"),
    ("surpresa", "P02", "zoom brusco na caixa, brilhos em volta"),
    ("sempre", "P03", "o Juca vira a cabeça no sofá, curioso"),
    ("tranquilamente", "P04", "ele relaxa no sofá com as mãos atrás da cabeça e cochila"),
    ("apareceu", "P05", "ela atravessa a sala com a caixa; ele se vira"),
    ("enorme", "P06", "ela entra no quadro com a caixa; zoom brusco"),
    ("abrir", "P07", "a tampa abre e a luz dourada ilumina o rosto dele"),
    ("PlayStation", "P08", "o videogame genérico sobe da caixa (sem logotipo); rótulo 0 h de uso"),
    ("espera", "P09", "ela levanta o dedo com sorriso de segredo"),
    ("surpresa", "P10", "a TV liga", 2),
    ("instalado", "P11", "a barra da tela chega a 100 %; zoom na TV"),
    ("instante", "P12", "close: os olhos dele se arregalam com a luz da TV"),
    ("descobriu", "P13", "ele se levanta devagar, maravilhado"),
    ("felicidade", "P14", "pulo de comemoração com os punhos para cima"),
    ("olhos", "P15", "close: estrelas nos olhos"),
    ("coração", "P16", "coração batendo, 72 → 140 BPM"),
    ("abraçou", "P17", "ele abraça o videogame e balança"),
    ("tesouro", "P18", "o videogame brilha como um tesouro, moedas caindo"),
    ("simplesmente", "P19", "ele ergue o videogame e balança a cabeça"),
    ("acreditar", "P20", "a Jandira ri e bate palmas"),
    ("ligou", "P21", "ele aperta o botão: a luz azul acende e a TV liga"),
    ("controle", "P22", "ele pega o controle e pula no sofá"),
    ("aventura", "P23", "por cima do ombro, a câmera mergulha na TV"),
    ("carro", "P24", "dentro do jogo: o carro acelera, 120 km/h"),
    ("rua", "P25", "a rua vista do alto"),
    ("detalhe", "P26", "as fachadas de perto"),
    ("incríveis", "P27", "o Juca vidrado, iluminado pela TV"),
    ("impressionado", "P28", "de perfil, inclinado, apertando os botões"),
    ("tempo", "P29", "time-lapse: a luz muda e a Jandira passa rápido; relógio 16:00 → 18:00"),
    ("Duas", "P30", "cartela 2 HORAS DEPOIS"),
    ("percebeu", "P31", "a Jandira na porta, de braços cruzados", 2),
    ("Cinco", "P32", "cartela 5 HORAS DEPOIS; o prato fumegando; noite"),
    ("fria", "P33", "o vapor some; termômetro 65 → 22 °C"),
    ("Dez", "P34", "cartela 10 HORAS DEPOIS; madrugada"),
    ("exatamente", "P35", "rótulo 0 m: ele não saiu do lugar"),
    ("residência", "P36", "rótulo NOVA RESIDÊNCIA OFICIAL sobre o sofá"),
    ("amanheceu", "P37", "o dia nasce na janela; relógio 06:12"),
    ("jogando", "P38", "close: barba, olheiras, olho tremendo", 2),
    ("perceber", "P39", "ela se espreguiça na porta e para, assustada"),
    ("erros", "P40", "mão na testa; zoom brusco"),
    ("agradar", "P41", "lembrança em sépia da chegada com a caixa"),
    ("morador", "P42", "o Juca andando dentro do jogo"),
    ("impressionante", "P43", "aproximação lenta por cima do ombro"),
    ("primeira", "P44", "MISSÃO 1 · 3 %; zoom brusco"),
    ("imagine", "P45", "a sala inteira; ela de braços cruzados"),
    ("desligar", "P46", "o dedo vai e volta do botão"),
    ("atenção", "P47", "ela olha para nós, batendo o pé"),
    ("desapareceria", "P48", "o Juca é sugado para dentro da TV"),
]


# ======================================================================= legendas
DESTAQUES = {"PLAYSTATION", "5", "GTA", "6", "FELICIDADE", "TESOURO", "DUAS", "CINCO", "DEZ", "FRIA", "AMANHECEU", "ERROS", "PRIMEIRA",
             "MISSÃO", "VICE", "CITY", "ENORME", "SURPRESA", "CORAÇÃO", "RESIDÊNCIA", "INSTALADO", "VIDEOGAME", "DESAPARECERIA"}


def legendas():
    det = json.loads((NARR / "palavras_final_detalhe.json").read_text()); texto = (NARR / "texto.txt").read_text()
    blocos, cur = [], []
    for k, (p, dd) in enumerate(zip(PAL, det)):
        pont = texto[dd["c1"]:dd["c1"] + 2]; cur.append((p, pont))
        prox = PAL[k + 1] if k + 1 < len(PAL) else None
        quebra = bool(re.match(r"\s*[.?!…,:]", pont)) or (prox is not None and prox["ini"] - p["fim"] >= 0.25)
        if len(cur) >= 3 or quebra or prox is None or (len(cur) == 2 and len("".join(x[0]["w"] for x in cur)) > 15):
            blocos.append(cur); cur = []
    out = []
    for i, b in enumerate(blocos):
        ini = b[0][0]["ini"]; fim = blocos[i + 1][0][0]["ini"] if i + 1 < len(blocos) else b[-1][0]["fim"] + 0.35
        fim = min(fim, b[-1][0]["fim"] + 0.6)
        palavras = [x[0]["w"].upper() + ("?" if "?" in x[1] else "") + ("!" if "!" in x[1] else "") for x in b]
        dest = [x[0]["w"].upper() for x in b if x[0]["w"].upper() in DESTAQUES]
        out.append({"ini": round(ini, 3), "fim": round(fim, 3), "txt": " ".join(palavras), "dest": dest})
    return out


LEG = GF.Legendas(legendas())


# ======================================================================= composição
def plano_em(t):
    for p in PLANOS:
        if p[1] <= t < p[2]:
            return p
    return PLANOS[-1]


def proj_ator(P, st):
    alt = AE.altura(st["P"]); pos = V(st["pos"], float)
    return ET.projetar(P, tuple(pos)), ET.projetar(P, (pos[0], pos[1], pos[2] + alt))


def _desenhar_rig(cv, st, x, y, tam, pose):
    H = st["P"].H
    for tent in range(4):
        try:
            cv.save(); H.desenhar(cv, x, y, tam, vista=st["vista"], direcao=st["direcao"], pose=pose, rosto=st["rosto"]); cv.restore(); return
        except RuntimeError:
            cv.restore(); pose = dict(pose)
            for k in AE.BRACOS:
                pose[k] = pose.get(k, 0.0) + 0.3 * (tent + 1)


def desenhar_ator(cv, st, x, y, tam, t):
    P = st["P"]; u = tam / 5.0; pose = dict(st["pose"]); vista = st["vista"]; dr = st["direcao"]
    def mundo(hx, hy):
        return x + hx * u * dr, y + hy * u
    camada = st.get("fantasma") or st.get("desfoque") or st.get("sugado")
    if camada:
        p = skia.Paint()
        if st.get("fantasma"):
            p.setAlphaf(st["fantasma"])
        if st.get("desfoque"):
            p.setImageFilter(skia.ImageFilters.Blur(st["desfoque"], st["desfoque"]))
        if st.get("sugado"):
            k = st["sugado"]; p.setAlphaf(max(0.0, 1 - k * 1.1))
        cv.saveLayer(None, p)
    # objetos presos às mãos (desenho próprio): controle, caixa, videogame abraçado/erguido
    if st.get("controle") and vista == "perfil":
        pose["objeto_d"] = PO.objeto_mundo(lambda cc, px, py: PO.controle(cc, px + 0.1 * u, py - 0.05 * u, u * 1.1, -25, perfil=True))
    if st.get("caixa") and vista == "perfil":
        pose["objeto_d"] = PO.objeto_mundo(lambda cc, px, py: PO.caixa_presente(cc, *mundo(0.62, -(P.H.PROP["barra_camisa"] + 0.25) + pose["raiz"][1]), u, larg=0.8, alt=0.85))
    if st.get("sugado"):
        k = st["sugado"]; cv.save(); cv.translate(x, y - tam * 0.5); cv.rotate(-200 * k * k); cv.scale(1 - 0.85 * k, 1 - 0.85 * k); cv.translate(-x, -(y - tam * 0.5))
    _desenhar_rig(cv, dict(st), x, y, tam, pose)
    if st.get("controle") and vista in ("frente", "tres_quartos"):
        _, (cx, cy), ang = PO.jogando(P, vista if vista != "tres_quartos" else "frente", t)
        PO.controle(cv, *mundo(cx * 0.9, cy), u, ang * dr)
    if st.get("caixa") and vista in ("frente", "tres_quartos"):
        bx, by = AE.caixa_centro(P, "frente", pose.get("raiz", [0, 0])[1])
        PO.caixa_presente(cv, *mundo(bx, by), u, larg=1.1, alt=0.85, brilho=st.get("brilho_caixa", 0.0))
    if st.get("console_abraco"):
        yc = -(P.H.PROP["ombro"] - 0.5)
        if vista == "perfil":
            pass
        PO.console(cv, *mundo(0.42 if vista == "perfil" else 0.0, yc), u * 1.4, deitado=False, luz=0.8)
        if vista == "perfil":   # o braço de perto passa por cima do videogame
            p2 = dict(pose); _desenhar_rig_braco = None
    if st.get("console_erguido"):
        PO.console(cv, *mundo(0.0, -(P.H.PROP["topo_cabeca"] + 0.35)), u * 1.4, deitado=True, luz=1.0)
    if st.get("sugado"):
        cv.restore()
    if camada:
        cv.restore()


def cena_canvas(Pc, est, t):
    """Função para o compositor: desenha a TV, os objetos 2D e os atores (do mais longe para o mais perto)."""
    atores = [(st, *proj_ator(Pc, st)) for st in est.get("atores", [])]
    atores.sort(key=lambda r: -r[1][2])

    def desenhar(cv, proj):
        if est.get("tv") and est["tv"] is not None:
            modo, tt, kk = est["tv"]; img = tv_conteudo(modo, tt, kk)
            if img is not None:
                cantos = []
                for c in TV_CANTOS:
                    a, b, _ = proj(*ET.projetar(Pc, c)); cantos.append((a, b))
                GF.warp_tela(cv, img, cantos, brilho=1.0)
        if est.get("console_luz") is not None or est["placa"] in ("C7_tv",):
            pe = ET.projetar(Pc, CONSOLE_RACK); tp = ET.projetar(Pc, (CONSOLE_RACK[0], CONSOLE_RACK[1], CONSOLE_RACK[2] + 0.32))
            x, y, _ = proj(*pe); _, yt, _ = proj(*tp); h = y - yt
            PO.console(cv, x, y - h / 2, h, luz=est.get("console_luz") or 0.0)
            if est.get("console_luz"):
                cv.drawCircle(x, y - h / 2, h * 0.5, GF.pt(0xFF4FC3F7, 0.25 * est["console_luz"], MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, h * 0.2)))
        for st, pe, tp in atores:
            x, y, _ = proj(*pe); _, yt, _ = proj(*tp)
            desenhar_ator(cv, st, x, y, y - yt, t)
        if est.get("caixa_mesa"):   # a caixa fica NA FRENTE do Juca (está na mesa, mais perto da câmera)
            cm = est["caixa_mesa"]; pe = ET.projetar(Pc, (-0.12, -0.55, 0.4)); tp = ET.projetar(Pc, (-0.12, -0.55, 0.4 + 0.42))
            x, y, _ = proj(*pe); _, yt, _ = proj(*tp); h = y - yt
            PO.caixa_presente(cv, x, y - h * 0.5, h / 0.85, larg=1.1, alt=0.85, tampa=cm["tampa"], brilho=cm["brilho"])
    perto = min((r[1][2] for r in atores), default=None)
    return desenhar, perto, atores


def tela(Pc, cam, p):
    return AT.tela(Pc, cam, p, OW, OH)


def sombras(cv, Pc, cam, est):
    for st in est.get("atores", []):
        if st.get("sugado", 0) > 0.6:
            continue
        alt = AE.altura(st["P"]); pos = V(st["pos"], float)
        pe = ET.projetar(Pc, (pos[0], pos[1], pos[2])); tp = ET.projetar(Pc, (pos[0], pos[1], pos[2] + alt))
        x, y = tela(Pc, cam, pe); _, yt = tela(Pc, cam, tp); tam = y - yt
        a = int(110 * (st.get("fantasma") or 1.0))
        cv.drawOval(skia.Rect.MakeXYWH(x - 0.16 * tam, y - 0.012 * tam, 0.32 * tam, 0.03 * tam),
                    skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(a, 28, 20, 18), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.012 * tam)))


def cabeca_tela(Pc, cam, st, com_tam=False):
    """Centro da cabeça na tela (e, opcional, a altura do personagem em px na tela)."""
    alt = AE.altura(st["P"]); pos = V(st["pos"], float)
    dy = -st["pose"].get("raiz", [0, 0])[1] * alt / 5.0
    _, yt = tela(Pc, cam, ET.projetar(Pc, (pos[0], pos[1], pos[2] + alt + dy - 0.1 * alt)))
    x, yp = tela(Pc, cam, ET.projetar(Pc, tuple(pos))); _, ytopo = tela(Pc, cam, ET.projetar(Pc, (pos[0], pos[1], pos[2] + alt)))
    return (x, yt, yp - ytopo) if com_tam else (x, yt)


def extras(cv, Pc, cam, est, tl, t):
    """Grafismo 2D por cima da cena (depois da composição): números, cartelas, vapor, estrelas, confete etc."""
    if est.get("vapor") is not None and est["vapor"] > 0:
        x, y = tela(Pc, cam, ET.projetar(Pc, PRATO)); GF.vapor(cv, x, y - 20, t, est["vapor"], esc=cam.get("zoom", 1.0) * 1.2)
    if est.get("termometro"):
        temp, k = est["termometro"]; GF.termometro(cv, OW * 0.16, OH * 0.47, temp, k)
    if est.get("brilhos_caixa") and est.get("atores"):
        st = est["atores"][0]; x, y = cabeca_tela(Pc, cam, st); GF.brilhos(cv, x, y + 360, 320, t, n=16)
    if est.get("estrelas_olhos") is not None and est.get("atores"):
        st = est["atores"][0]; x, y, tam = cabeca_tela(Pc, cam, st, True)
        uu = tam / 5.0; dxo = 0.205 * uu; yy = y + 0.04 * uu
        for sx in (-1, 1):
            GF.brilhos(cv, x + sx * dxo, yy, 0.09 * uu, t * 1.3, n=6, cor=0xFFFFE08A, semente=7 + sx, forca=1.4)
    if est.get("coracoes") is not None and est.get("atores"):
        st = est["atores"][0]; x, y = cabeca_tela(Pc, cam, st)
        for i in range(5):
            f = (tl * 0.9 + i / 5) % 1.0; xx = x + 120 * math.sin(i * 2.3 + f * 4); yy = y + 40 - f * 380
            _coracao(cv, xx, yy, 28 + 14 * i % 3, (1 - f))
    if est.get("confete") is not None:
        _confete(cv, est["confete"])
    if est.get("lixo"):
        _lixo(cv, Pc, cam, est["lixo"])
    if est.get("residencia") is not None and est["residencia"] > 0:
        x, y = tela(Pc, cam, ET.projetar(Pc, (0.0, -1.7, 0.95))); _residencia(cv, x, y, est["residencia"])
    if est.get("rotulo_juca") and est.get("atores"):
        txt, sub, k = est["rotulo_juca"]; st = est["atores"][0]; x, y = cabeca_tela(Pc, cam, st)
        GF.rotulo(cv, txt, sub, x + 40, y + 260, 1, k=k)
    if est.get("rotulo_tv"):
        txt, sub, k = est["rotulo_tv"]; x, y = tela(Pc, cam, ET.projetar(Pc, (0.3, 2.12, 0.85))); GF.rotulo(cv, txt, sub, x, y, 1, k=k)
    if est.get("cartela"):
        n, l1, l2, k = est["cartela"]; GF.cartela_tempo(cv, n, l1, k, y=0.27, sub=l2)
    if est.get("relogio"):
        h, k = est["relogio"]; GF.relogio_digital(cv, h, OW * 0.5, OH * 0.12 + 40, k)
    if est.get("hud"):
        GF.hud(cv, t, OW, OH, velocidade=None, missao_pct=3, escala=1.3)
    if est.get("espiral"):
        _espiral(cv, Pc, cam, est["espiral"], t)


def _coracao(cv, x, y, r, a):
    p = skia.Path(); p.moveTo(x, y + r * 0.9)
    p.cubicTo(x - r * 1.4, y + r * 0.05, x - r * 0.95, y - r * 1.05, x, y - r * 0.35); p.cubicTo(x + r * 0.95, y - r * 1.05, x + r * 1.4, y + r * 0.05, x, y + r * 0.9)
    cv.drawPath(p, GF.pt(0xFFE2384D, a)); cv.drawPath(p, GF.borda(GF.ESCURO, 4, a))


def _confete(cv, tl):
    rng = np.random.default_rng(3); cores = [0xFFFFC21F, 0xFF3D80D8, 0xFFE2384D, 0xFF5CFFB0, 0xFFB57BFF]
    for i in range(70):
        x0 = rng.uniform(0, OW); v = rng.uniform(500, 900); y = -60 + tl * v - rng.uniform(0, 400)
        if y < -60 or y > OH:
            continue
        x = x0 + 60 * math.sin(tl * 4 + i); a = tl * 8 + i
        cv.save(); cv.translate(x, y); cv.rotate(math.degrees(a)); cv.scale(abs(math.cos(a)) + 0.2, 1)
        cv.drawRect(skia.Rect.MakeXYWH(-10, -6, 20, 12), GF.pt(cores[i % 5])); cv.restore()


def _lixo(cv, Pc, cam, k):
    """Embalagens genéricas (sem marca) se acumulando em volta do sofá."""
    rng = np.random.default_rng(11); cores = [0xFFE2384D, 0xFF3D80D8, 0xFFFFC21F, 0xFF5CFFB0]
    for i in range(9):
        if k < i / 9:
            continue
        x, y = tela(Pc, cam, ET.projetar(Pc, (rng.uniform(-0.9, 0.9), rng.uniform(-1.25, -0.95), 0.0)))
        s = 40 * cam.get("zoom", 1.0) * rng.uniform(0.8, 1.3)
        cv.save(); cv.translate(x, y - s * 0.4); cv.rotate(rng.uniform(-40, 40))
        if i % 2:
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-s * 0.5, -s * 0.7, s, s * 1.4), s * 0.15, s * 0.15), GF.pt(cores[i % 4]))
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-s * 0.5, -s * 0.7, s, s * 1.4), s * 0.15, s * 0.15), GF.borda(GF.ESCURO, 3))
        else:
            cv.drawRect(skia.Rect.MakeXYWH(-s * 0.3, -s * 0.5, s * 0.6, s), GF.pt(0xFFC9CED6)); cv.drawRect(skia.Rect.MakeXYWH(-s * 0.3, -s * 0.2, s * 0.6, s * 0.35), GF.pt(cores[i % 4]))
            cv.drawRect(skia.Rect.MakeXYWH(-s * 0.3, -s * 0.5, s * 0.6, s), GF.borda(GF.ESCURO, 3))
        cv.restore()


def _residencia(cv, x, y, k):
    if k <= 0:
        return
    s = GF.pop(k); cv.save(); cv.translate(x, y - 330 * s)
    casa = skia.Path(); casa.moveTo(-70 * s, -10 * s); casa.lineTo(0, -75 * s); casa.lineTo(70 * s, -10 * s); casa.close()
    cv.drawPath(casa, GF.pt(GF.AMARELO)); cv.drawPath(casa, GF.borda(GF.ESCURO, 7 * s))
    cv.drawRect(skia.Rect.MakeXYWH(-50 * s, -12 * s, 100 * s, 70 * s), GF.pt(GF.AMARELO)); cv.drawRect(skia.Rect.MakeXYWH(-50 * s, -12 * s, 100 * s, 70 * s), GF.borda(GF.ESCURO, 7 * s))
    cv.drawRect(skia.Rect.MakeXYWH(-14 * s, 18 * s, 28 * s, 40 * s), GF.pt(GF.ESCURO))
    cv.restore()
    GF.centro(cv, "NOVA RESIDÊNCIA", x, y - 170 * s, 96 * s, GF.BRANCO); GF.centro(cv, "OFICIAL", x, y - 75 * s, 96 * s, GF.AMARELO)


def _espiral(cv, Pc, cam, k, t):
    cx, cy = 0.0, 0.0
    for c in TV_CANTOS:
        x, y = tela(Pc, cam, ET.projetar(Pc, c)); cx += x / 4; cy += y / 4
    for i in range(10):
        a = t * 5 + i * 0.63; r = 900 * (1 - ((t * 0.8 + i / 10) % 1.0))
        pth = skia.Path(); pth.addArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), math.degrees(a), 70)
        cv.drawPath(pth, GF.borda([0xFF5FB8FF, 0xFFFF5FA8, 0xFFFFC21F][i % 3], 10, 0.5 * k))


def sepia(img, k=1.0):
    g = img.astype(np.float32) @ np.array([[0.393, 0.349, 0.272], [0.769, 0.686, 0.534], [0.189, 0.168, 0.131]], np.float32)
    g = np.clip(g, 0, 255); out = img.astype(np.float32) * (1 - k) + g * k
    h, w_ = out.shape[:2]; yy, xx = np.mgrid[0:h, 0:w_]; v = 1 - 0.55 * (((xx - w_ / 2) / (w_ / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    return np.clip(out * v[..., None], 0, 255).astype(np.uint8)


def estado(n):
    t = n / FPS; pid, ini, fim, fn, ent = plano_em(t); tl = t - ini
    est = fn(tl, fim - ini); est.update(id=pid, tl=tl, entrada=ent, t=t, dur=fim - ini)
    if est.get("cam"):   # deriva: a câmera nunca fica parada
        est["cam"] = dict(est["cam"], zoom=est["cam"]["zoom"] * (1 + 0.03 * tl / (fim - ini)))
    return est


def quadro(n):
    est = estado(n); tl, t = est["tl"], est["t"]; rosto_y = None
    if est.get("insert"):
        img = est["insert"](t)
    else:
        Pc = placa(est["placa"]); cam = est["cam"]
        if est["hora"] == "cidade":
            pesos, grade = {"ceu": 1.0, "sol": 1.0, "artificial": 1.4, "efeito": 0.0}, dict(ET.GRADE, saturacao=1.35)
        else:
            pesos, grade = luz(est["hora"], t, est.get("tvluz", 0.0), est.get("hora_para"), est.get("hora_k", 0.0))
        if est.get("luz_caixa"):
            pesos["efeito"] = (1.6 * est["luz_caixa"], "#ffd36a")
        des, perto, atores = cena_canvas(Pc, est, t)
        kw = dict(pesos=pesos, grade=grade, semente_grao=n)
        if perto is not None or est.get("tv") or est["placa"] == "C7_tv":
            dprof = perto if perto is not None else ET.projetar(Pc, (0.0, 2.1, 1.0))[2]
            kw.update(personagem=des, profundidade_personagem=dprof)
            if atores:
                st0 = min(atores, key=lambda r: r[1][2])[0]
                kw["tom_personagem"] = X1.fazer_tom({"pe_mundo": list(map(float, st0["pos"])), "altura_m": AE.altura(st0["P"])})
                _, rosto_y = cabeca_tela(Pc, cam, st0); rosto_y += 0.12 * OH * cam.get("zoom", 1.0) * 0.3
        img = np.ascontiguousarray(AT.compor(Pc, cam, **kw))
        if est.get("dessatura"):
            g = img.mean(2, keepdims=True); img = (img * (1 - est["dessatura"]) + g * est["dessatura"]).astype(np.uint8)
        s = skia.Surface(OW, OH); cv = s.getCanvas(); cv.drawImage(GF.skimg(img), 0, 0)
        sombras(cv, Pc, cam, est); extras(cv, Pc, cam, est, tl, t)
        img = GF.snap(s)
        if est.get("sepia"):
            img = sepia(img)
    ent = est["entrada"]
    if ent == "chicote" and tl < 0.13:
        kx = int(140 * (1 - tl / 0.13)) * 2 + 1; img = cv2.blur(img, (max(3, kx), 1))
    elif ent == "flash" and tl < 0.12:
        a = 0.85 * (1 - tl / 0.12); img = (img * (1 - a) + 255 * a).astype(np.uint8)
    elif ent == "fusao" and tl < 0.25:
        ant = quadro_bruto(n - int(tl * FPS) - 1)
        a = tl / 0.25; img = (ant * (1 - a) + img * a).astype(np.uint8)
    tr = est.get("tremida")
    if tr and tr[0] <= tl <= tr[1]:
        rng = np.random.default_rng(n); amp = 0.014 * OW * (1 - (tl - tr[0]) / max(1e-3, tr[1] - tr[0]))
        Mt = np.float32([[1.03, 0, rng.uniform(-amp, amp) - 0.015 * OW], [0, 1.03, rng.uniform(-amp, amp) - 0.015 * OH]])
        img = cv2.warpAffine(img, Mt, (OW, OH), borderMode=cv2.BORDER_REFLECT)
    s = skia.Surface(OW, OH); cv = s.getCanvas(); cv.drawImage(GF.skimg(img), 0, 0)
    if t < FIM_VOZ + 0.1 and est["id"] != "P49":
        LEG.desenhar(cv, t, rosto_y)
    GF.marca_dagua(cv)
    return GF.snap(s)


_BRUTO = {}


def quadro_bruto(n):
    if n not in _BRUTO:
        _BRUTO.clear(); _BRUTO[n] = quadro(n)
    return _BRUTO[n]


def segmento(n0, n1, saida_):
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "pipe:0",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", str(saida_)], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        ff.stdin.write(np.ascontiguousarray(quadro(n)).tobytes())
        if (n - n0) % 60 == 0:
            print(f"{saida_.name}: {n - n0}/{n1 - n0}", flush=True)
    ff.stdin.close(); ff.wait()


def main():
    a = sys.argv; N = int(round(DUR * FPS))
    sd = P_ / "saida"; sd.mkdir(exist_ok=True)
    mapa = []
    for item in MAPA:
        pal, pid, acao = item[:3]; n = item[3] if len(item) > 3 else 1; tt = w(pal, n)
        mapa.append(dict(palavra=pal, t=round(tt, 3), plano=pid, plano_no_instante=plano_em(tt)[0], acao=acao))
    (sd / "mapa_fala_imagem.json").write_text(json.dumps(mapa, ensure_ascii=False, indent=1) + "\n")
    (sd / "legendas.json").write_text(json.dumps(LEG.b, ensure_ascii=False, indent=1) + "\n")
    (sd / "planos.json").write_text(json.dumps([dict(id=p[0], ini=p[1], fim=round(p[2], 3), entrada=p[4]) for p in PLANOS], ensure_ascii=False, indent=1) + "\n")
    if "--png" in a:
        pasta = Path(a[a.index("--png") + 1]); pasta.mkdir(parents=True, exist_ok=True)
        for n in [int(x) for x in a[a.index("--quadros") + 1].split(",")]:
            cv2.imwrite(str(pasta / f"q{n:04d}.png"), cv2.cvtColor(quadro(n), cv2.COLOR_RGB2BGR))
        return
    if "--seg" in a:
        segmento(int(a[a.index("--de") + 1]), int(a[a.index("--ate") + 1]), Path(a[a.index("--seg") + 1])); return
    trab = int(os.environ.get("TRABALHADORES", "4")); tmp = P_ / "_cache" / "segmentos"; tmp.mkdir(parents=True, exist_ok=True)
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
