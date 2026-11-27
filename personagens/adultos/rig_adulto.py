#!/usr/bin/env python3
"""Rig adulto do Modo Curioso — Juca e Jandira (PROPOSTA, aguardando aprovação do diretor).

Derivado do rig oficial do Heitor (v2.1) SEM alterá-lo: cada personagem carrega uma CÓPIA própria dos módulos
heitor_v2 / animacao / gestos (importlib, nomes de módulo separados) e troca só o que define o personagem:
paleta, proporções de adulto (5 H em vez de 4 H), ossos, larguras, cabelo, tronco, calça e calçado.
Esqueleto, FK, IK, mãos de 5 dedos, rosto paramétrico, expressões, caminhada/corrida e a regra do cotovelo
são os mesmos do rig v2.1 (aprovados).

Uso:
    import rig_adulto as RA
    J = RA.carregar("juca")          # J.H (rig), J.A (animação), J.G (gestos)
    J.H.desenhar(canvas, x_pe, y_pe, altura_px, vista="frente", direcao=1, pose=None, rosto="alegria")

Parâmetros extras do rosto (opcionais, 0–1): "olheira" (olheiras) e "barba" (barba por fazer).
"""
import copy, importlib.util, json, math, sys
from pathlib import Path
from types import SimpleNamespace
import skia

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
RIG = RAIZ / "personagens" / "heitor" / "rig_v2" / "codigo"
ESPECS = json.loads((AQUI / "modelos.json").read_text())


def _hex(v):
    return 0xFF000000 | int(v.lstrip("#"), 16)


def _carregar_modulo(nome, arquivo):
    spec = importlib.util.spec_from_file_location(nome, arquivo)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


_CACHE = {}


def carregar(nome):
    if nome in _CACHE:
        return _CACHE[nome]
    esp = ESPECS[nome]
    H = _carregar_modulo(f"rig_{nome}", RIG / "heitor_v2.py")
    _aplicar(H, esp)
    salvo = {k: sys.modules.get(k) for k in ("heitor_v2", "animacao")}
    try:
        sys.modules["heitor_v2"] = H
        A = _carregar_modulo(f"animacao_{nome}", RIG / "animacao.py")
        sys.modules["animacao"] = A
        G = _carregar_modulo(f"gestos_{nome}", RIG / "gestos.py")
    finally:
        for k, v in salvo.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    r = SimpleNamespace(nome=esp["nome"], H=H, A=A, G=G, esp=esp, altura_H=esp["proporcoes_H"]["topo_cabeca"])
    _CACHE[nome] = r
    return r


# ====================================================================== aplicação do modelo
def _aplicar(H, esp):
    mod = copy.deepcopy(H.MOD)
    mod["nome"] = esp["nome"]; mod["versao"] = esp["versao"]; mod["barba_base"] = esp.get("barba_base", 0.0)
    mod["paleta"].update(esp["paleta"]); mod["proporcoes_H"] = esp["proporcoes_H"]; mod["ossos_H"].update(esp["ossos_H"])
    H.MOD = mod
    H.C = {k: _hex(v) for k, v in mod["paleta"].items()}
    H.PROP = mod["proporcoes_H"]; H.OSS = mod["ossos_H"]
    P = H.PROP; L = esp["larguras_H"]
    H._ALT_PELVE = P["barra_camisa"]
    H.OMBRO_Y = -(P["ombro"] - P["barra_camisa"])
    H.PESCOCO_Y = -(P["pescoco"] - P["barra_camisa"])
    bx, qx = L["braco_x"], L["coxa_x"]
    ab = L.get("braco_ang", 8.0)                      # v1.1: braços mais junto ao corpo em repouso
    H.LAYOUT = {
        "frente": {"braco_d": (-bx, ab), "braco_e": (bx, -ab), "coxa_d": (-qx, 0), "coxa_e": (qx, 0)},
        "costas": {"braco_d": (bx, -ab), "braco_e": (-bx, ab), "coxa_d": (qx, 0), "coxa_e": (-qx, 0)},
        "tres_quartos": {"braco_d": (-bx * 0.79, ab * 0.75), "braco_e": (bx * 0.70, -ab * 0.5), "coxa_d": (-qx * 0.8, 0), "coxa_e": (qx * 0.63, 0)},
        "perfil": {"braco_d": (-0.03, 2), "braco_e": (0.05, -2), "coxa_d": (-0.03, 0), "coxa_e": (0.06, 0)},
    }
    em = L["escala_mao"]
    H.ENCAIXE = {k: (x * em, y * em) for k, (x, y) in H.ENCAIXE.items()}
    _mao_orig = H.desenhar_mao

    def desenhar_mao(c, dedos, vista="dorso", espelho=False, lado_luz=1, objeto=None):
        c.save(); c.scale(em, em)
        obj = None
        if objeto:   # o objeto é desenhado no sistema da mão SEM a escala da mão adulta
            def obj(cc, v):
                cc.save(); cc.scale(1 / em, 1 / em); objeto(cc, v); cc.restore()
        _mao_orig(c, dedos, vista, espelho, lado_luz, obj); c.restore()
    H.desenhar_mao = desenhar_mao

    lb, la, lc, lk = L["braco"], L["antebraco"], L["coxa"], L["canela"]
    H.forma_braco = lambda: H.capsula(H.OSS["braco"], lb[0], lb[1])
    H.forma_antebraco = lambda: H.capsula(H.OSS["antebraco"] + 0.02, la[0], la[1])
    H.forma_coxa = lambda: H.capsula(H.OSS["coxa"] + 0.04, lc[0], lc[1])

    def forma_canela():
        p = skia.Path(); Lc = H.OSS["canela"] - 0.02
        p.moveTo(-lk[0] / 2, -0.04); p.lineTo(lk[0] / 2, -0.04); p.lineTo(lk[1] / 2, Lc); p.lineTo(-lk[1] / 2, Lc); p.close()
        return p
    H.forma_canela = forma_canela
    H._forma_tronco = lambda vista: _forma_tronco(H, esp, vista)
    H.desenhar_tronco = lambda c, vista, ll, esp_: _desenhar_tronco(H, esp, c, vista, ll, esp_)
    H.desenhar_quadril = lambda c, vista, ll: _desenhar_quadril(H, esp, c, vista, ll)
    H.desenhar_cabeca = lambda c, vista, e, ll: _desenhar_cabeca(H, esp, c, vista, e, ll)
    if esp["calca"] == "moletom":
        H.desenhar_barra = lambda c, ll, dist=False: _punho_moletom(H, c, ll, dist)
    if esp["calcado"] == "chinelo":
        H.desenhar_pe = lambda c, vista, ll, dist=False: _chinelo(H, c, vista, ll, dist)
    H.EXPRESSOES.update({
        "vidrado": H._expr(branco=True, pupila=0.42, palp_sup=0.18, sobr=(0.05, 0.05, 0.03), boca="sorriso_aberto",
                           abertura=0.3, sorriso=0.8, largura=0.95, dentes=True),
        "irritada": H._expr(palp_sup=0.42, sobr=(-0.06, 0.04, 0.0), boca="linha", sorriso=-0.45, largura=0.8, assimetria=0.3),
        "desconfiada": H._expr(palp_sup=0.5, olhar=(0.5, 0.0), sobr=(-0.02, 0.03, 0.0), sobr_e=(0.07, 0.07, 0.03),
                               boca="meio_sorriso", sorriso=-0.3, assimetria=0.6),
    })
    H.desenhar = lambda *a, **k: _desenhar(H, esp, *a, **k)


# ====================================================================== tronco e quadril
def _forma_tronco(H, esp, vista):
    L = esp["larguras_H"]; top, hem = H.OMBRO_Y - 0.1, 0.0
    om, ci, ba = L["ombro"], L["cintura"], L["barra"]
    meio = top * 0.45
    p = skia.Path()
    if vista in ("frente", "costas", "tres_quartos"):
        k = 1.0 if vista != "tres_quartos" else 0.84
        g = L.get("gola", 0.14) * k; qd, qc = L.get("trapezio", (0.075, 0.21))   # v1.1: trapézio desce mais devagar
        p.moveTo(-g, top - 0.025); p.lineTo(g, top - 0.025)
        p.cubicTo(g + 0.09 * k, top - 0.02, om * k - 0.17 * k, top + qd * 0.45, om * k - 0.085 * k, top + qd)
        p.cubicTo(om * k - 0.03 * k, top + qd + 0.025, om * k, top + qc - 0.07, om * k, top + qc)
        p.cubicTo(om * k + 0.01, meio, ci * k, meio * 0.5, ba * k, hem)
        p.lineTo(-ba * k, hem)
        p.cubicTo(-ci * k, meio * 0.5, -om * k - 0.01, meio, -om * k, top + qc)
        p.cubicTo(-om * k, top + qc - 0.07, -om * k + 0.03 * k, top + qd + 0.025, -om * k + 0.085 * k, top + qd)
        p.cubicTo(-om * k + 0.17 * k, top + qd * 0.45, -g - 0.09 * k, top - 0.02, -g, top - 0.025)
        if vista == "tres_quartos":
            p.transform(skia.Matrix.Translate(0.02, 0))
    else:
        fr, fc, fb = L["perfil_frente"]; tr_, tc, tb = L["perfil_costas"]
        p.moveTo(-0.10, top - 0.025); p.lineTo(0.08, top - 0.025)
        p.cubicTo(0.16, top - 0.015, fr, top + 0.05, fr, top + 0.22)
        p.cubicTo(fr + 0.01, meio, fc, meio * 0.5, fb, hem)
        p.lineTo(-tb, hem)
        p.cubicTo(-tc, meio * 0.5, -tr_ - 0.01, meio, -tr_, top + 0.16)
        p.cubicTo(-tr_ + 0.02, top + 0.03, -0.16, top - 0.015, -0.10, top - 0.025)
    p.close(); return p


def _desenhar_tronco(H, esp, c, vista, lado_luz, espelhado):
    C = H.C; L = esp["larguras_H"]
    tr = _forma_tronco(H, esp, vista); top = H.OMBRO_Y - 0.1
    c.drawPath(tr, H.tinta(C["camisa"]))
    if vista in ("frente", "tres_quartos"):
        larg = 0.56 * 0.86 * (2 * L["ombro"] / 0.97) * (H.MOD["estampa"]["tres_quartos"]["compressao"] if vista == "tres_quartos" else 1.0)
        cx = 0.0 if vista == "frente" else 0.07
        H._estampa(c, cx, top + L["estampa_y"], larg, curva=0.6 if vista == "frente" else 0.9,
                   perspectiva=0.0 if vista == "frente" else 0.18, espelhado=espelhado)
    H.sombra(c, tr, C["camisa_s"], lado_luz, 0.28, multiplicar=_hex(esp["multiplicar_sombra"]))
    for s in (-1, 1):   # dobras do tecido
        if vista == "perfil" and s < 0:
            continue
        x0 = s * (L["cintura"] * 0.8 if vista != "perfil" else 0.12)
        pth = skia.Path(); pth.moveTo(x0, top * 0.55); pth.quadTo(x0 - s * 0.07, top * 0.45, x0 - s * 0.04, top * 0.33)
        c.drawPath(pth, H.traco(C["camisa_s"], 0.018))
    b = tr.getBounds()
    c.save(); c.clipPath(tr, doAntiAlias=True)
    c.drawLine(b.left(), -0.035, b.right(), -0.035, H.traco(C["gola"], 0.012)); c.restore()
    c.drawPath(tr, H.contorno())
    OY = H.OMBRO_Y
    if vista == "frente":
        dec = skia.Path(); dec.moveTo(-0.18, OY - 0.1); dec.quadTo(0, OY + 0.11, 0.18, OY - 0.1); dec.close()
        c.drawPath(dec, H.tinta(C["pele_s"])); c.drawPath(dec, H.traco(C["gola"], 0.045))
    elif vista == "tres_quartos":
        dec = skia.Path(); dec.moveTo(-0.08, OY - 0.1); dec.quadTo(0.07, OY + 0.09, 0.21, OY - 0.1); dec.close()
        c.drawPath(dec, H.tinta(C["pele_s"])); c.drawPath(dec, H.traco(C["gola"], 0.045))
    elif vista == "perfil":
        c.drawLine(-0.02, OY - 0.1, 0.16, OY - 0.06, H.traco(C["gola"], 0.045))
    else:
        c.drawLine(-0.18, OY - 0.1, 0.18, OY - 0.1, H.traco(C["gola"], 0.045))


def _desenhar_quadril(H, esp, c, vista, lado_luz):
    C = H.C; L = esp["larguras_H"]
    w = L["quadril"] * {"frente": 1.0, "costas": 1.0, "tres_quartos": 0.88, "perfil": 0.62}[vista]
    q = H.rrect(-w, -0.02, w, 0.26, 0.07)
    H.preenche(c, q, C["jeans"], C["jeans_s"], lado_luz, 0.25)
    if esp["calca"] == "moletom":
        c.save(); c.clipPath(q, doAntiAlias=True)
        c.drawRect(skia.Rect.MakeLTRB(-w, -0.02, w, 0.06), H.tinta(C["barra"]))   # cós de elástico
        for k in range(-6, 7):
            c.drawLine(k * w / 6.5, -0.01, k * w / 6.5, 0.05, H.traco(C["jeans_s"], 0.006))
        c.restore()
        if vista == "frente":   # cordão
            for s in (-1, 1):
                pth = skia.Path(); pth.moveTo(s * 0.04, 0.03); pth.quadTo(s * 0.07, 0.12, s * 0.05, 0.2)
                c.drawPath(pth, H.traco(0xFFF2EFE8, 0.016))
        c.drawPath(q, H.contorno())
    else:
        if vista == "frente":
            for s in (-1, 1):
                pth = skia.Path(); pth.moveTo(s * (w - 0.07), 0.0); pth.quadTo(s * (w - 0.1), 0.12, s * (w - 0.24), 0.14)
                c.drawPath(pth, H.traco(C["barra"], 0.012))
            c.drawLine(0.0, 0.0, 0.0, 0.22, H.traco(C["jeans_s"], 0.012))
        elif vista == "costas":
            for s in (-1, 1):
                c.drawPath(H.rrect(s * (w * 0.62) - 0.09, 0.05, s * (w * 0.62) + 0.09, 0.21, 0.02), H.traco(C["barra"], 0.012))


def _punho_moletom(H, c, lado_luz, distante=False):
    C = H.C; L = H.OSS["canela"]
    b = H.rrect(-0.15, L - 0.16, 0.15, L - 0.015, 0.05)
    H.preenche(c, b, C["jeans_s"] if distante else C["barra"], C["jeans_s"], lado_luz, 0.25)
    c.save(); c.clipPath(b, doAntiAlias=True)
    for k in range(-5, 6):
        c.drawLine(k * 0.027, L - 0.16, k * 0.027, L - 0.015, H.traco(C["jeans_s"], 0.006))
    c.restore()


def _chinelo(H, c, vista, lado_luz, distante=False):
    """Pé descalço no chinelo (origem no tornozelo; o chão fica 0,22 H abaixo)."""
    C = H.C
    pele, pele_s = (C["pele_s"], C["pele_s"]) if distante else (C["pele"], C["pele_s"])
    tira = C["tenis_faixa"]; sola_top = C["tenis"]; sola = C["sola"]
    if vista in ("frente", "costas"):
        s_ = H.rrect(-0.2, 0.175, 0.2, 0.222, 0.025)
        c.drawPath(s_, H.tinta(sola)); c.drawRect(skia.Rect.MakeLTRB(-0.19, 0.175, 0.19, 0.19), H.tinta(sola_top))
        c.drawPath(s_, H.contorno())
        f = H.rrect(-0.14, -0.04, 0.14, 0.185, 0.09)
        H.preenche(c, f, pele, pele_s, lado_luz, 0.3, linha=False)
        if vista == "frente":
            for k in range(5):   # dedos do pé
                x = -0.1 + k * 0.05
                c.drawLine(x, 0.15, x, 0.18, H.traco(pele_s, 0.008))
        c.drawPath(f, H.contorno())
        if vista == "frente":   # tiras em V
            for s in (-1, 1):
                c.drawLine(0.0, 0.13, s * 0.13, 0.07, H.traco(tira, 0.04))
            c.drawCircle(0.0, 0.13, 0.025, H.tinta(tira))
        else:
            c.drawLine(-0.13, 0.08, 0.13, 0.08, H.traco(tira, 0.03))
    else:
        if vista == "tres_quartos":
            c.save(); c.scale(0.8, 1.0)
        s_ = skia.Path(); s_.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-0.17, 0.175, 0.35, 0.222), 0.02, 0.02))
        c.drawPath(s_, H.tinta(sola)); c.drawRect(skia.Rect.MakeLTRB(-0.16, 0.175, 0.34, 0.19), H.tinta(sola_top))
        c.drawPath(s_, H.contorno())
        f = skia.Path(); f.moveTo(-0.11, -0.04); f.lineTo(0.06, -0.04); f.quadTo(0.24, 0.05, 0.31, 0.12)
        f.quadTo(0.34, 0.17, 0.3, 0.182); f.lineTo(-0.12, 0.182); f.quadTo(-0.17, 0.08, -0.11, -0.04); f.close()
        H.preenche(c, f, pele, pele_s, lado_luz, 0.25, linha=False); c.drawPath(f, H.contorno())
        c.drawLine(0.05, 0.07, 0.2, 0.14, H.traco(tira, 0.04))
        if vista == "tres_quartos":
            c.restore()


# ====================================================================== cabeça
def _regiao(pts):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.lineTo(pts[-1][0], -3.0); p.lineTo(pts[0][0], -3.0); p.close(); return p


def _suaviza(pts):
    """Caminho suave (Catmull-Rom → Bézier) por uma lista de pontos, fechando para cima (região do cabelo)."""
    p = skia.Path(); p.moveTo(*pts[0])
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    return p


def _fecha_cima(p, pts):
    p.lineTo(pts[-1][0], -3.0); p.lineTo(pts[0][0], -3.0); p.close(); return p


def _uniao(a, b):
    return skia.Op(a, b, skia.PathOp.kUnion_PathOp) or a


def _inter(a, b):
    return skia.Op(a, b, skia.PathOp.kIntersect_PathOp) or a


# linhas do cabelo (bordas inferiores) por personagem e vista, em coordenadas da cabeça (hy = centro)
def _cabelo_juca(H, vista, hy, rw):
    sh = {"frente": 0.0, "tres_quartos": 0.12, "perfil": 0.26, "costas": 0.0}[vista]
    if vista == "frente":
        borda = [(-0.62, hy + 0.06), (-0.49, hy + 0.02), (-0.44, hy - 0.16), (-0.30, hy - 0.25), (0.0, hy - 0.29),
                 (0.30, hy - 0.25), (0.44, hy - 0.16), (0.49, hy + 0.02), (0.62, hy + 0.06)]
        arco = (195, 345)
    elif vista == "tres_quartos":
        borda = [(-0.66, hy + 0.16), (-0.50, hy + 0.12), (-0.44, hy - 0.04), (-0.30, hy - 0.08), (-0.24, hy + 0.04),
                 (-0.17, hy - 0.2), (0.12, hy - 0.29), (0.40, hy - 0.22), (0.5, hy - 0.08), (0.66, hy - 0.04)]
        arco = (170, 340)
    elif vista == "perfil":
        borda = [(-0.68, hy + 0.36), (-0.44, hy + 0.32), (-0.22, hy + 0.12), (-0.17, hy - 0.08), (-0.02, hy - 0.06),
                 (0.04, hy + 0.05), (0.09, hy - 0.17), (0.30, hy - 0.28), (0.47, hy - 0.22), (0.7, hy - 0.2)]
        arco = (140, 330)
    else:
        borda = [(-0.66, hy + 0.3), (-0.47, hy + 0.2), (-0.2, hy + 0.3), (0.0, hy + 0.33), (0.2, hy + 0.3),
                 (0.47, hy + 0.2), (0.66, hy + 0.3)]
        arco = (150, 390)
    regiao = _fecha_cima(_suaviza(borda), borda)
    cx = -0.03 if vista == "perfil" else 0.0
    forma = H.oval(cx, hy - 0.05, rw * 1.05, 0.53)
    a0, a1 = arco
    n = 15
    for i in range(n + 1):   # cachos do contorno (cabelo crespo curto)
        t = math.radians(a0 + (a1 - a0) * i / n)
        x = cx + rw * 1.05 * math.cos(t); y = hy - 0.05 + 0.53 * math.sin(t)
        forma = _uniao(forma, H.oval(x, y, 0.075, 0.07))
    return _inter(forma, regiao), None, sh


def _cabelo_jandira(H, vista, hy, rw):
    """Cabelo longo ondulado com risca lateral: (frente do cabelo, cabelo de trás, deslocamento)."""
    sh = {"frente": 0.0, "tres_quartos": 0.12, "perfil": 0.26, "costas": 0.0}[vista]

    def mecha(x0, y0, x1, y1, w0, w1, onda=0.03):
        p = skia.Path(); n = 8
        esq, dir_ = [], []
        for i in range(n + 1):
            t = i / n; x = x0 + (x1 - x0) * t + onda * math.sin(t * math.pi * 2.2); y = y0 + (y1 - y0) * t
            w = w0 + (w1 - w0) * t
            esq.append((x - w / 2, y)); dir_.append((x + w / 2, y))
        p.moveTo(*esq[0])
        for q in esq[1:]:
            p.lineTo(*q)
        p.quadTo(x1, y1 + w1 * 0.8, *dir_[-1])
        for q in reversed(dir_[:-1]):
            p.lineTo(*q)
        p.close(); return p

    if vista == "costas":
        tras = None
        frente = H.oval(0, hy - 0.04, rw * 1.08, 0.55)
        corpo = skia.Path(); corpo.moveTo(-0.55, hy); corpo.cubicTo(-0.62, hy + 0.6, -0.6, hy + 0.95, -0.42, hy + 1.18)
        for k in range(6):   # pontas onduladas
            x = -0.42 + (k + 0.5) * 0.14
            corpo.quadTo(x, hy + 1.28 - 0.04 * (k % 2), x + 0.07, hy + 1.18)
        corpo.cubicTo(0.6, hy + 0.95, 0.62, hy + 0.6, 0.55, hy); corpo.close()
        frente = _uniao(frente, corpo)
        return frente, tras, sh
    # cabelo de trás (atrás da cabeça e do corpo)
    if vista == "frente":
        tras = skia.Path(); tras.moveTo(-0.55, hy - 0.1); tras.cubicTo(-0.66, hy + 0.4, -0.66, hy + 0.85, -0.5, hy + 1.1)
        tras.quadTo(-0.3, hy + 1.2, 0.0, hy + 1.12); tras.quadTo(0.3, hy + 1.2, 0.5, hy + 1.1)
        tras.cubicTo(0.66, hy + 0.85, 0.66, hy + 0.4, 0.55, hy - 0.1); tras.close()
    elif vista == "tres_quartos":
        tras = skia.Path(); tras.moveTo(-0.52, hy - 0.2); tras.cubicTo(-0.72, hy + 0.4, -0.74, hy + 0.9, -0.52, hy + 1.14)
        tras.quadTo(-0.2, hy + 1.22, 0.1, hy + 1.1); tras.cubicTo(0.3, hy + 0.8, 0.42, hy + 0.4, 0.4, hy - 0.1); tras.close()
    else:
        tras = skia.Path(); tras.moveTo(-0.2, hy - 0.45); tras.cubicTo(-0.75, hy - 0.3, -0.72, hy + 0.5, -0.62, hy + 1.1)
        tras.quadTo(-0.42, hy + 1.24, -0.14, hy + 1.12); tras.cubicTo(-0.1, hy + 0.7, 0.0, hy + 0.3, 0.05, hy - 0.2); tras.close()
    # frente do cabelo: calota + franja lateral + mechas que emolduram o rosto
    if vista == "frente":
        borda = [(-0.62, hy + 0.5), (-0.5, hy + 0.45), (-0.43, hy + 0.1), (-0.38, hy - 0.14), (-0.22, hy - 0.26), (-0.1, hy - 0.32),
                 (0.08, hy - 0.24), (0.28, hy - 0.16), (0.40, hy - 0.06), (0.44, hy + 0.12), (0.5, hy + 0.45), (0.62, hy + 0.5)]
        regiao = _fecha_cima(_suaviza(borda), borda)
        cal = _inter(H.oval(0, hy - 0.02, rw * 1.1, 0.56), regiao)
    elif vista == "tres_quartos":
        borda = [(-0.66, hy + 0.4), (-0.5, hy + 0.3), (-0.42, hy - 0.06), (-0.28, hy - 0.1), (-0.2, hy - 0.22),
                 (0.02, hy - 0.3), (0.26, hy - 0.2), (0.44, hy - 0.08), (0.5, hy + 0.1), (0.66, hy + 0.2)]
        regiao = _fecha_cima(_suaviza(borda), borda)
        cal = _inter(H.oval(-0.01, hy - 0.05, rw * 1.08, 0.55), regiao)
    else:
        borda = [(-0.7, hy + 0.5), (-0.45, hy + 0.42), (-0.2, hy + 0.2), (-0.17, hy - 0.1), (0.0, hy - 0.12),
                 (0.12, hy - 0.22), (0.32, hy - 0.3), (0.48, hy - 0.2), (0.7, hy - 0.2)]
        regiao = _fecha_cima(_suaviza(borda), borda)
        cal = _inter(H.oval(-0.04, hy - 0.05, rw * 1.1, 0.56), regiao)
    return cal, tras, sh


def _desenhar_cabelo_tras(H, esp, c, vista, lado_luz):
    if esp["cabelo"] != "longo":
        return
    hy = -0.58; rw = H.PROP["largura_cabeca"] / 2
    _, tras, _ = _cabelo_jandira(H, vista, hy, rw)
    if tras is None:
        return
    C = H.C
    c.drawPath(tras, H.tinta(C["cabelo_s"]))
    c.save(); c.clipPath(tras, doAntiAlias=True)
    for k in range(6):
        x0 = -0.5 + k * 0.2
        pth = skia.Path(); pth.moveTo(x0, hy + 0.1); pth.quadTo(x0 + 0.06, hy + 0.6, x0 - 0.02, hy + 1.1)
        c.drawPath(pth, H.traco(0xFF0F0806, 0.016))
    c.restore()
    c.drawPath(tras, H.contorno())


def _desenhar_cabeca(H, esp, c, vista, e, lado_luz):
    C = H.C
    hy = -0.58; rw, rh = H.PROP["largura_cabeca"] / 2, 0.5
    pb = esp["larguras_H"].get("pescoco_baixo", 0.14)          # v1.1: pescoço desce até a gola (ombro mais baixo)
    pesc = H.rrect(-0.11, -0.12, 0.11, pb, 0.04)
    c.drawPath(pesc, H.tinta(C["pele_s"]))
    sh = {"frente": 0.0, "tres_quartos": 0.12, "perfil": 0.26, "costas": 0.0}[vista]

    def orelha(x, esc=1.0):
        o = H.oval(x, hy + 0.04, 0.095 * esc, 0.12); H.preenche(c, o, C["pele"], C["pele_s"], lado_luz, 0.35)
        dob = skia.Path(); dob.moveTo(x - 0.02 * esc, hy - 0.02); dob.quadTo(x + 0.05 * esc * (1 if x > 0 else -1), hy + 0.04, x - 0.01 * esc, hy + 0.1)
        c.drawPath(dob, H.traco(C["pele_s"], 0.014))
    longo = esp["cabelo"] == "longo"   # cabelo longo cobre as orelhas na frente e no 3/4
    if vista == "costas" or (vista == "frente" and not longo):
        orelha(-rw); orelha(rw)
    elif vista == "tres_quartos" and not longo:
        orelha(-rw * 0.95)
    # queixo um pouco mais longo que o do Heitor (adulto)
    cab = H.oval(0, hy, rw * (1.04 if vista == "perfil" else 1.0), rh)
    qx = rh * esp["queixo"]
    if vista != "costas":
        qz = H.oval(0.0 + (rw * 0.35 if vista == "perfil" else sh * 0.6), hy + 0.2, rw * (0.62 if vista == "perfil" else 0.74), 0.30 + qx)
        cab = _uniao(cab, qz)
    if vista == "perfil":
        nariz = skia.Path(); nariz.moveTo(rw * 0.94, hy + 0.06); nariz.quadTo(rw * 1.18, hy + 0.16, rw * 0.95, hy + 0.21); nariz.close()
        cab = _uniao(cab, nariz)
    H.preenche(c, cab, C["pele"], C["pele_s"], lado_luz, 0.36)
    if vista == "perfil":
        orelha(-0.06, 0.85)
    if vista != "costas":
        _barba(H, c, vista, e, hy, rw, sh, cab)
        olho_y = hy + 0.06

        def pl(x):
            return C["pele_s"] if x * lado_luz > 0.06 else C["pele"]
        if vista == "perfil":
            c.save(); c.clipPath(cab, doAntiAlias=True)
        olhos = []
        if vista == "frente":
            olhos = [(-0.205, 1.0, -1), (0.205, 1.0, 1)]
        elif vista == "tres_quartos":
            olhos = [(-0.2 + sh, 1.0, -1), (0.2 + sh * 0.8, 0.78, 1)]
        else:
            olhos = [(rw * 0.55, 0.62, 1)]
        for (x, ex, lado) in olhos:
            _olheira(H, c, x, olho_y, ex, e)
            H._olho(c, x, olho_y, e, ex, pele_lid=pl(x))
            if esp["cilios"]:
                _cilios(H, c, x, olho_y, ex, lado if vista == "frente" else 1, e)
        if vista == "frente":
            H._sobrancelha(c, -0.205, olho_y - 0.17, e["sobr"], -1); H._sobrancelha(c, 0.205, olho_y - 0.17, e["sobr_e"] or e["sobr"], 1)
            nar = skia.Path(); nar.moveTo(0.012, hy + 0.13); nar.quadTo(0.052, hy + 0.19, -0.008, hy + 0.205)
            c.drawPath(nar, H.traco(C["pele_s"], 0.02))
            H._boca(c, 0.0 + e["assimetria"] * 0.02, hy + 0.31, e)
        elif vista == "tres_quartos":
            H._sobrancelha(c, -0.2 + sh, olho_y - 0.17, e["sobr"], -1); H._sobrancelha(c, 0.2 + sh * 0.8, olho_y - 0.17, e["sobr_e"] or e["sobr"], 1, 0.78)
            nar = skia.Path(); nar.moveTo(0.04 + sh, hy + 0.12); nar.quadTo(0.11 + sh, hy + 0.19, 0.03 + sh, hy + 0.21)
            c.drawPath(nar, H.traco(C["pele_s"], 0.02))
            H._boca(c, sh * 0.9, hy + 0.31, e, 0.85)
        else:
            H._sobrancelha(c, rw * 0.55, olho_y - 0.17, e["sobr_e"] or e["sobr"], 1, 0.7)
            H._boca(c, rw * 0.66, hy + 0.32, e, 0.5)
            c.restore()
    if esp["cabelo"] == "crespo_curto":
        cb, _, _ = _cabelo_juca(H, vista, hy, rw)
    else:
        cb, _, _ = _cabelo_jandira(H, vista, hy, rw)
    c.drawPath(cb, H.tinta(C["cabelo"])); H.sombra(c, cb, C["cabelo_s"], lado_luz, 0.32)
    c.save(); c.clipPath(cb, doAntiAlias=True)
    if esp["cabelo"] == "crespo_curto":   # textura de cachinhos
        for i in range(-4, 5):
            for j in range(4):
                x = i * 0.1 + (0.05 if j % 2 else 0); y = hy - 0.48 + j * 0.11
                a = skia.Path(); a.addArc(skia.Rect.MakeXYWH(x - 0.03, y - 0.025, 0.06, 0.05), 200, 220)
                c.drawPath(a, H.traco(C["cabelo_s"], 0.014))
        br = skia.Path(); br.moveTo(-0.26 + sh * 0.5, hy - 0.44); br.quadTo(-0.05 + sh * 0.5, hy - 0.53, 0.14 + sh * 0.5, hy - 0.45)
        c.drawPath(br, H.traco(C["cabelo_b"], 0.05))
    else:
        for k in range(6):
            x0 = -0.4 + k * 0.16
            pth = skia.Path(); pth.moveTo(x0, hy - 0.5); pth.quadTo(x0 + 0.1, hy - 0.25, x0 + 0.02, hy + (0.9 if vista == "costas" else 0.0))
            c.drawPath(pth, H.traco(C["cabelo_s"], 0.016))
        br = skia.Path(); br.moveTo(-0.3 + sh * 0.5, hy - 0.4); br.quadTo(-0.05 + sh * 0.5, hy - 0.52, 0.2 + sh * 0.5, hy - 0.42)
        c.drawPath(br, H.traco(C["cabelo_b"], 0.05))
    c.restore()
    c.drawPath(cb, H.contorno())


def _olheira(H, c, x, y, ex, e):
    k = e.get("olheira", 0.0)
    if k <= 0:
        return
    p = skia.Path(); p.moveTo(x - 0.075 * ex, y + 0.075); p.quadTo(x, y + 0.13, x + 0.075 * ex, y + 0.075)
    c.drawPath(p, H.traco(0xFF6B4A7A, 0.022 * k + 0.004)); pt = H.traco(0xFF6B4A7A, 0.05); pt.setAlphaf(0.35 * k); c.drawPath(p, pt)


def _cilios(H, c, x, y, ex, lado, e):
    if e["branco"]:
        r = 0.105
    else:
        r = 0.07
    ps = e["palp_sup"]
    if ps >= 0.99:
        y0 = y + 0.01
    else:
        y0 = y - r + 2 * r * ps
    yc = max(y0, y - r * 0.55) if ps < 0.99 else y0
    xe = x + lado * r * ex * 0.92
    for k, (dx, dy) in enumerate(((0.05, -0.03), (0.055, 0.005))):
        c.drawLine(xe, yc + k * 0.02, xe + lado * dx * ex, yc + dy + k * 0.02, H.traco(H.C["pupila"], 0.017))


def _barba(H, c, vista, e, hy, rw, sh, cab):
    k = e.get("barba", H.MOD.get("barba_base", 0.0))
    if k <= 0:
        return
    if vista == "frente":
        z = H.oval(0, hy + 0.3, rw * 0.78, 0.26)
    elif vista == "tres_quartos":
        z = H.oval(sh * 0.8, hy + 0.3, rw * 0.7, 0.26)
    else:
        z = H.oval(rw * 0.5, hy + 0.3, rw * 0.55, 0.25)
    z = skia.Op(z, H.oval(0, hy - 0.2, rw * 1.2, 0.42), skia.PathOp.kDifference_PathOp) or z
    z = _inter(z, cab)
    c.drawPath(z, H.tinta(H.C["cabelo"], 0.30 * k))


# ====================================================================== montagem
def _desenhar(H, esp, c, x_pe, y_pe, altura_px, vista="frente", direcao=1, pose=None, rosto=None, luz=-1):
    pose = pose or H.pose_base(vista)
    if H.AUDITORIA is not None:
        H.AUDITORIA.append((vista, {k: v for k, v in pose.items() if not callable(v)}))
    e = rosto if isinstance(rosto, dict) else H.EXPRESSOES[rosto or "neutro"]
    u = altura_px / H.PROP["topo_cabeca"]
    c.save(); c.translate(x_pe, y_pe); c.scale(u * direcao, u)
    espelhado = direcao < 0
    luz_local = luz * direcao
    M = H.esqueleto(pose, vista)

    def com(m, f):
        c.save(); c.concat(m); f(H._lado_luz(m, luz_local)); c.restore()

    if vista != "costas":
        com(M["cabeca"], lambda ll: _desenhar_cabelo_tras(H, esp, c, vista, ll))
    for item in H.ORDEM[vista]:
        dist = item.endswith("*"); nome = item.rstrip("*")
        if nome.startswith("perna_"):
            s = nome[-1]
            com(M[f"pe_{s}"], lambda ll: H.desenhar_pe(c, vista, ll, dist))
            H.membro(c, [(M[f"canela_{s}"], H.forma_canela(), H._lado_luz(M[f"canela_{s}"], luz_local)),
                         (M[f"coxa_{s}"], H.forma_coxa(), H._lado_luz(M[f"coxa_{s}"], luz_local))], H.C["jeans"], H.C["jeans_s"], dist)
            com(M[f"canela_{s}"], lambda ll: H.desenhar_barra(c, ll, dist))
        elif nome == "quadril":
            com(M["raiz"], lambda ll: H.desenhar_quadril(c, vista, ll))
        elif nome == "tronco":
            com(M["tronco"], lambda ll: H.desenhar_tronco(c, vista, ll, espelhado))
        elif nome == "cabeca":
            com(M["cabeca"], lambda ll: H.desenhar_cabeca(c, vista, e, ll))
        elif nome.startswith("braco_"):
            s = nome[-1]
            mv = pose.get(f"mao_vista_{s}") or H.VISTA_MAO[vista]
            espelho_mao = (s == "e") if vista in ("frente", "tres_quartos", "perfil") else (s == "d")
            H.membro(c, [(M[f"antebraco_{s}"], H.forma_antebraco(), H._lado_luz(M[f"antebraco_{s}"], luz_local)),
                         (M[f"braco_{s}"], H.forma_braco(), H._lado_luz(M[f"braco_{s}"], luz_local))], H.C["pele"], H.C["pele_s"], dist)
            com(M[f"mao_{s}"], lambda ll: H.desenhar_mao(c, pose[f"dedos_{s}"], mv, espelho_mao, ll, pose.get(f"objeto_{s}")))
            com(M[f"braco_{s}"], lambda ll: H.desenhar_manga(c, ll, dist))
    c.restore()
    return M
