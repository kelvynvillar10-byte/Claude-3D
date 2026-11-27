#!/usr/bin/env python3
"""Heitor — rig 2D com esqueleto, v2 (OFICIAL, aprovado pelo diretor em 25/11/2026).

Fonte da verdade: ../modelo.json (paleta e proporções da especificação oficial).
- Esqueleto hierárquico com FK: raiz(pelve) → tronco → cabeça; tronco → braço → antebraço → mão → 5 dedos;
  raiz → coxa → canela → pé. Cada peça é desenhada NO SISTEMA DO SEU OSSO, então as juntas articulam.
- Vistas: frente, tres_quartos, perfil, costas (direcao=+1 → voltado para a direita da tela; −1 → espelho).
  A estampa "Modo Curioso" nunca é espelhada (ID-002/ID-003).
- Unidade: H = altura da cabeça (altura total 4 H); origem nos pés, y para baixo (convenção do skia).

API principal:
    desenhar(canvas, x_pe, y_pe, altura_px, vista="frente", direcao=1, pose=None, rosto=None, luz=-1)
    pose_base(vista) -> dict de ângulos (graus) ; EXPRESSOES[nome] -> parâmetros do rosto ; MAOS[nome] -> pose de mão
"""
import copy, json, math
from pathlib import Path
import skia

AQUI = Path(__file__).resolve().parent
RAIZ_REPO = AQUI.parents[3]
MOD = json.loads((AQUI.parent / "modelo.json").read_text())
C = {k: 0xFF000000 | int(v.lstrip("#"), 16) for k, v in MOD["paleta"].items()}
PROP = MOD["proporcoes_H"]; OSS = MOD["ossos_H"]
NUNITO = skia.Typeface.MakeFromFile(str(RAIZ_REPO / "assets" / "fontes" / "Nunito-ExtraBold.ttf"))
LW = 0.018   # espessura do contorno (H)

# ------------------------------------------------------------------ utilidades de desenho
def tinta(cor, a=1.0):
    p = skia.Paint(AntiAlias=True, Color=cor); p.setAlphaf(a); return p


def contorno(w=LW):
    return skia.Paint(AntiAlias=True, Color=C["contorno"], Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap)


def traco(cor, w):
    return skia.Paint(AntiAlias=True, Color=cor, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def capsula(l, w0, w1):
    """Membro afunilado do (0,0) ao (0,l), larguras w0 (topo) e w1 (ponta), pontas arredondadas."""
    p = skia.Path()
    p.moveTo(-w0 / 2, 0); p.lineTo(-w1 / 2, l)
    p.arcTo(skia.Rect.MakeLTRB(-w1 / 2, l - w1 / 2, w1 / 2, l + w1 / 2), 180, -180, False)
    p.lineTo(w0 / 2, 0)
    p.arcTo(skia.Rect.MakeLTRB(-w0 / 2, -w0 / 2, w0 / 2, w0 / 2), 0, -180, False)
    p.close(); return p


def rrect(x0, y0, x1, y1, r):
    p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r)); return p


def oval(cx, cy, rx, ry):
    p = skia.Path(); p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)); return p


def sombra(c, forma, cor, lado, frac=0.3, multiplicar=None):
    """Um tom de sombra em crescente no lado oposto à luz (lado=+1 → sombra à direita do sistema local)."""
    b = forma.getBounds()
    if b.isEmpty():
        return
    d = skia.Path(forma); d.offset(-lado * b.width() * frac, -b.height() * 0.02)
    cr = skia.Op(forma, d, skia.PathOp.kDifference_PathOp)
    if cr is None:
        return
    if multiplicar is not None:
        c.drawPath(cr, skia.Paint(AntiAlias=True, Color=multiplicar, BlendMode=skia.BlendMode.kMultiply))
    else:
        c.drawPath(cr, tinta(cor))


def preenche(c, forma, cor, cor_s, lado, frac=0.3, linha=True):
    c.drawPath(forma, tinta(cor)); sombra(c, forma, cor_s, lado, frac)
    if linha:
        c.drawPath(forma, contorno())


# ------------------------------------------------------------------ esqueleto (FK)
# Posição de cada osso no sistema do pai, por vista (x em H; y para baixo). Ângulo de repouso em graus.
_ALT_PELVE = PROP["barra_camisa"]
OMBRO_Y = -(PROP["ombro"] - _ALT_PELVE)
PESCOCO_Y = -(2.92 - _ALT_PELVE)
LAYOUT = {
    "frente":       {"braco_d": (-0.47, 8), "braco_e": (0.47, -8), "coxa_d": (-0.19, 0), "coxa_e": (0.19, 0)},
    "costas":       {"braco_d": (0.47, -8), "braco_e": (-0.47, 8), "coxa_d": (0.19, 0), "coxa_e": (-0.19, 0)},
    "tres_quartos": {"braco_d": (-0.37, 6), "braco_e": (0.33, -4), "coxa_d": (-0.15, 0), "coxa_e": (0.12, 0)},
    "perfil":       {"braco_d": (-0.03, 2), "braco_e": (0.05, -2), "coxa_d": (-0.03, 0), "coxa_e": (0.06, 0)},
}
# lado "perto" da câmera nas vistas voltadas para a direita (direção +1): o lado direito do personagem
PERTO = {"tres_quartos": "d", "perfil": "d"}


class Pose(dict):
    pass


def pose_base(vista="frente"):
    p = {"raiz": [0.0, 0.0], "tronco": 0.0, "cabeca": 0.0, "respira": 0.0}
    for s in ("d", "e"):
        p.update({f"braco_{s}": 0.0, f"antebraco_{s}": 0.0, f"mao_{s}": 0.0,
                  f"coxa_{s}": 0.0, f"canela_{s}": 0.0, f"pe_{s}": 0.0,
                  f"dedos_{s}": copy.deepcopy(MAOS["relaxada"]), f"mao_vista_{s}": None})
    return p


def _rot(m, x, y, ang, esc=1.0):
    loc = skia.Matrix.Translate(x, y); loc.preRotate(ang)
    if esc != 1.0:   # escorço: o osso encurta quando aponta para a câmera
        loc.preScale(1.0, esc)
    return skia.Matrix.Concat(m, loc)


def esqueleto(pose, vista):
    """Retorna as matrizes de mundo (em H, origem nos pés) de cada osso, já com a pose aplicada (FK)."""
    L = LAYOUT[vista]; M = {}
    base = skia.Matrix(); base.setTranslate(pose["raiz"][0], -_ALT_PELVE + pose["raiz"][1])
    M["raiz"] = base
    M["tronco"] = _rot(base, 0, 0, pose["tronco"])
    resp = 1 + 0.012 * pose.get("respira", 0.0)
    M["cabeca"] = _rot(M["tronco"], 0, PESCOCO_Y * resp, pose["cabeca"])
    # ESCORÇO: o osso encurta no próprio eixo (escala y local) e o filho nasce na ponta ENCURTADA do pai,
    # mas NÃO herda a escala do pai (cada osso tem só o próprio escorço; mão e pé nunca são achatados).
    def filho(pai_sem_esc, esc_pai, comp_pai, ang, esc=1.0):
        return _rot(pai_sem_esc, 0, comp_pai * esc_pai, ang, esc)
    for s in ("d", "e"):
        bx, ba = L[f"braco_{s}"]
        eb, ea = pose.get(f"esc_braco_{s}", 1.0), pose.get(f"esc_antebraco_{s}", 1.0)
        b0 = _rot(M["tronco"], bx, OMBRO_Y * resp, ba + pose[f"braco_{s}"])
        M[f"braco_{s}"] = _rot(M["tronco"], bx, OMBRO_Y * resp, ba + pose[f"braco_{s}"], eb)
        a0 = filho(b0, eb, OSS["braco"], pose[f"antebraco_{s}"])
        M[f"antebraco_{s}"] = filho(b0, eb, OSS["braco"], pose[f"antebraco_{s}"], ea)
        M[f"mao_{s}"] = filho(a0, ea, OSS["antebraco"], pose[f"mao_{s}"])
        cx, ca = L[f"coxa_{s}"]
        ec_, ek = pose.get(f"esc_coxa_{s}", 1.0), pose.get(f"esc_canela_{s}", 1.0)
        c0 = _rot(base, cx, 0.02 + pose.get(f"_prof_{s}", 0.0), ca + pose[f"coxa_{s}"])
        M[f"coxa_{s}"] = _rot(base, cx, 0.02 + pose.get(f"_prof_{s}", 0.0), ca + pose[f"coxa_{s}"], ec_)
        k0 = filho(c0, ec_, OSS["coxa"], pose[f"canela_{s}"])
        M[f"canela_{s}"] = filho(c0, ec_, OSS["coxa"], pose[f"canela_{s}"], ek)
        M[f"pe_{s}"] = filho(k0, ek, OSS["canela"], pose[f"pe_{s}"])
    return M


def ponto_mundo(m, x=0.0, y=0.0):
    return m.mapXY(x, y)


def _lado_luz(m, luz):
    """Em qual lado (local) fica a sombra, dada a luz no mundo (luz=-1: vem da esquerda)."""
    inv = skia.Matrix(); m.invert(inv)
    o = inv.mapXY(0, 0); d = inv.mapXY(-luz, 0)   # direção oposta à luz
    return 1 if (d.x() - o.x()) > 0 else -1


# ------------------------------------------------------------------ mãos (palma + 5 dedos)
_DEDOS = ["indicador", "medio", "anelar", "minimo"]
_BASE_DORSO = {"indicador": (0.066, 0.192, 0.042, 7), "medio": (0.022, 0.200, 0.044, 1),
               "anelar": (-0.024, 0.195, 0.041, -5), "minimo": (-0.066, 0.183, 0.035, -12)}


def _mao(fle=None, abert=0.0, pol=None):
    d = {n: list(v) for n, v in (fle or {}).items()}
    for n in _DEDOS:
        d.setdefault(n, [8, 10, 6])
    d.setdefault("polegar", list(pol or [10, 10]))
    d["abertura"] = abert
    return d


MAOS = {
    "relaxada": _mao({n: [8, 12, 8] for n in _DEDOS}, 0.0, [12, 8]),
    "aberta": _mao({n: [0, 0, 0] for n in _DEDOS}, 1.0, [0, 0]),
    "punho": _mao({n: [95, 100, 70] for n in _DEDOS}, 0.0, [55, 60]),
    "apontar": _mao({"indicador": [0, 0, 0], "medio": [95, 100, 70], "anelar": [95, 100, 70], "minimo": [95, 100, 70]}, 0.0, [45, 50]),
    "segurar": _mao({n: [55, 60, 35] for n in _DEDOS}, 0.2, [30, 25]),
    "acenar": _mao({n: [0, 4, 2] for n in _DEDOS}, 0.7, [5, 0]),
    "joinha": _mao({n: [95, 100, 70] for n in _DEDOS}, 0.0, [-15, -10]),
}
for k in range(1, 6):   # contagem 1–5 (1 = indicador ... 5 = mão aberta com polegar)
    abertos = (["indicador", "medio", "anelar", "minimo"])[:min(k, 4)]
    MAOS[f"conta_{k}"] = _mao({n: ([0, 0, 0] if n in abertos else [95, 100, 70]) for n in _DEDOS}, 0.5 if k > 1 else 0.0,
                              [0, 0] if k == 5 else [50, 55])


def _dedo_cadeia(c, comp, angs, w0, cor, cor_s, lado_luz, proj_dorso=False):
    """Desenha um dedo (cadeia de falanges) com UM contorno contínuo. Retorna as falanges dobradas para trás.
    proj_dorso=True: vista de dorso/palma — a flexão encurta a falange (escorço); >90° ela volta sobre a palma."""
    formas, dobradas = [], []
    if proj_dorso:
        y, cum = 0.0, 0.0
        for i, L in enumerate(comp):
            cum += angs[i]; pr = L * math.cos(math.radians(min(cum, 180))); w = w0 * (1 - 0.08 * i)
            if pr >= 0.003:
                f = capsula(pr, w, w * 0.96); f.offset(0, y); formas.append(f)
            elif pr <= -0.003:
                f = capsula(-pr, w, w); f.offset(0, y + pr); dobradas.append(f)
            y += pr
    else:
        m = skia.Matrix()
        for i, L in enumerate(comp):
            m = skia.Matrix.Concat(m, skia.Matrix.RotateDeg(angs[i]))
            f = capsula(L, w0 * (1 - 0.08 * i), w0 * (1 - 0.08 * (i + 1))); f.transform(m); formas.append(f)
            m = skia.Matrix.Concat(m, skia.Matrix.Translate(0, L))
    uni = None
    for f in formas:
        c.drawPath(f, tinta(cor)); sombra(c, f, cor_s, lado_luz, 0.3)
        uni = f if uni is None else (skia.Op(uni, f, skia.PathOp.kUnion_PathOp) or uni)
    if uni is not None:
        c.drawPath(uni, contorno())
    return dobradas


def desenhar_mao(c, dedos, vista="dorso", espelho=False, lado_luz=1, objeto=None):
    """Mão no sistema do osso 'mao' (origem no punho, +y para as pontas). vista: dorso | palma | lado.
    Cinco dedos individuais: polegar (2 falanges) e indicador, médio, anelar, mínimo (3 falanges cada).
    objeto(c, vista): desenha um objeto segurado no ENCAIXE da mão (ver ENCAIXE), na camada certa:
    dorso → atrás da mão; palma → na frente da mão (mostrando); lado → na frente da palma, atrás do indicador e do polegar."""
    c.save()
    if espelho:
        c.scale(-1, 1)
    ab = dedos.get("abertura", 0.0)
    PL = OSS["dedos"]["polegar"]
    if vista in ("dorso", "palma"):
        sg = 1 if vista == "dorso" else -1
        palma = skia.Path()
        palma.moveTo(-0.082, 0.0); palma.quadTo(-0.1, 0.11, -0.088, 0.185)
        palma.quadTo(0.0, 0.212, 0.09, 0.19); palma.quadTo(0.102, 0.1, 0.082, 0.0); palma.close()
        if sg < 0:
            palma.transform(skia.Matrix.Scale(-1, 1))

        def polegar():
            c.save(); c.translate(0.078 * sg, 0.085)
            c.rotate(-sg * (38 + 22 * ab) + sg * dedos["polegar"][0] * 0.8)
            _dedo_cadeia(c, PL, [0, sg * dedos["polegar"][1]], 0.064, C["pele"], C["pele_s"], lado_luz)
            c.restore()
        if objeto and vista == "dorso":
            objeto(c, vista)
        if vista == "palma":
            polegar()
        c.drawPath(palma, tinta(C["pele"])); sombra(c, palma, C["pele_s"], lado_luz, 0.25); c.drawPath(palma, contorno())
        if vista == "palma":
            for (a0, a1, q) in (((-0.06, 0.09), (0.06, 0.11), (0.0, 0.075)), ((-0.05, 0.135), (0.055, 0.15), (0.0, 0.12))):
                pth = skia.Path(); pth.moveTo(*a0); pth.quadTo(q[0], q[1], *a1); c.drawPath(pth, traco(C["pele_s"], 0.009))
        dobradas = []
        for n in _DEDOS:
            bx, by, w, sp = _BASE_DORSO[n]; bx *= sg
            c.save(); c.translate(bx, by); c.rotate(-sg * sp * (0.4 + 1.3 * ab))
            dob = _dedo_cadeia(c, OSS["dedos"][n], dedos[n], w * 1.28, C["pele"], C["pele_s"], lado_luz, proj_dorso=True)
            if vista == "dorso" and dedos[n][0] < 60:   # nó do dedo (detalhe)
                c.drawLine(-w * 0.3, 0.012, w * 0.3, 0.012, traco(C["pele_s"], 0.008))
            dobradas += [(c.getTotalMatrix(), f) for f in dob]
            c.restore()
        for (m, f) in dobradas:   # dedos dobrados por cima da palma (punho)
            c.save(); c.setMatrix(m); c.drawPath(f, tinta(C["pele_s"])); c.drawPath(f, contorno()); c.restore()
        if objeto and vista == "palma":   # palma para a câmera: o objeto fica NA FRENTE da mão (mostrando o objeto)
            objeto(c, vista)
        if vista == "dorso":
            polegar()
    else:   # vista "lado": dedos empilhados (mínimo atrás → indicador na frente), flexão = rotação real
        palma = skia.Path()
        palma.moveTo(-0.045, 0.0); palma.quadTo(-0.062, 0.1, -0.05, 0.2); palma.quadTo(0.0, 0.215, 0.05, 0.2)
        palma.quadTo(0.064, 0.1, 0.045, 0.0); palma.close()
        # médio/anelar/mínimo como um bloco recuado (em tom de sombra), indicador na frente
        tras = [sum(dedos[n][i] for n in ("medio", "anelar", "minimo")) / 3 for i in range(3)]
        c.save(); c.translate(-0.022, 0.18)
        _dedo_cadeia(c, OSS["dedos"]["medio"], [a * 0.95 for a in tras], 0.068, C["pele_s"], C["pele_s"], lado_luz)
        c.restore()
        def indicador():
            c.save(); c.translate(0.014, 0.188)
            _dedo_cadeia(c, OSS["dedos"]["indicador"], [a * 0.95 for a in dedos["indicador"]], 0.056, C["pele"], C["pele_s"], lado_luz)
            c.restore()
        if not objeto:
            indicador()
        c.drawPath(palma, tinta(C["pele"])); sombra(c, palma, C["pele_s"], lado_luz, 0.25); c.drawPath(palma, contorno())
        if objeto:   # objeto na concha dos dedos: na frente da palma, atrás do indicador (o dedo abraça o objeto)
            objeto(c, vista); indicador()
        c.save(); c.translate(0.04, 0.05); c.rotate(-24 + dedos["polegar"][0] * 0.6)
        _dedo_cadeia(c, PL, [0, dedos["polegar"][1] * 0.6], 0.06, C["pele"], C["pele_s"], lado_luz)
        c.restore()
    c.restore()


# ponto de encaixe de um objeto segurado, no sistema da mão, por vista
ENCAIXE = {"dorso": (0.0, 0.215), "palma": (0.0, 0.2), "lado": (-0.10, 0.17)}


# ------------------------------------------------------------------ rosto
def _expr(**k):
    base = dict(palp_sup=0.12, palp_inf=0.0, branco=False, pupila=1.0, olhar=(0.0, 0.0),
                sobr=(0.0, 0.0, 0.0), sobr_e=None, boca="linha", abertura=0.0, sorriso=0.1, largura=1.0, dentes=False,
                assimetria=0.0)
    base.update(k); return base


EXPRESSOES = {
    "neutro": _expr(palp_sup=0.0),
    "alegria": _expr(palp_inf=0.45, palp_sup=0.05, sobr=(0.03, 0.04, 0.02), boca="sorriso_aberto", abertura=0.55, sorriso=1.0, largura=1.15, dentes=True),
    "surpresa": _expr(branco=True, pupila=0.5, palp_sup=0.0, sobr=(0.09, 0.08, 0.06), boca="o", abertura=0.7),
    "medo": _expr(branco=True, pupila=0.34, palp_sup=0.0, sobr=(0.11, -0.01, 0.0), boca="aberta", abertura=0.8, sorriso=-0.5, largura=1.15, dentes=True),
    "preocupacao": _expr(palp_sup=0.22, sobr=(0.07, -0.03, -0.01), boca="ondulada", sorriso=-0.35, largura=0.85),
    "triste": _expr(palp_sup=0.38, olhar=(0.0, 0.25), sobr=(0.08, -0.04, 0.0), boca="linha", sorriso=-0.7),
    "bravo": _expr(palp_sup=0.32, sobr=(-0.07, 0.03, 0.0), boca="dentes_cerrados", abertura=0.25, sorriso=-0.4, dentes=True),
    "pensativo": _expr(palp_sup=0.18, olhar=(0.6, -0.6), sobr=(0.0, 0.0, 0.0), sobr_e=(0.06, 0.08, 0.03), boca="o_lado", abertura=0.2, largura=0.6, assimetria=0.4),
    "sonolento": _expr(palp_sup=0.62, sobr=(-0.01, -0.02, -0.01), boca="linha", sorriso=0.0, largura=0.7),
    "convencido": _expr(palp_sup=0.48, sobr=(0.0, 0.02, 0.0), boca="meio_sorriso", sorriso=0.6, assimetria=0.8),
    "dormindo": _expr(palp_sup=1.0, boca="o", abertura=0.15, largura=0.5),
}


def _olho(c, x, y, e, esc_x=1.0, lado=1, pele_lid=None):
    pele_lid = pele_lid or C["pele"]
    c.save(); c.translate(x, y); c.scale(esc_x, 1.0)
    ox, oy = e["olhar"]
    if e["branco"]:
        r = 0.105
        c.drawCircle(0, 0, r, tinta(C["branco_olho"]))
        c.drawCircle(ox * 0.035, oy * 0.035, 0.046 * e["pupila"] + 0.006, tinta(C["pupila"]))
        ps = e["palp_sup"]
        if ps > 0:   # pálpebra também no olho arregalado (piscar sem trocar de estilo)
            c.save(); c.clipPath(oval(0, 0, r, r), doAntiAlias=True)
            c.drawRect(skia.Rect.MakeLTRB(-r - 0.01, -r - 0.01, r + 0.01, -r + 2 * r * ps), tinta(pele_lid))
            c.restore()
        if ps >= 0.99:
            c.drawPath(oval(0, 0, r, r), tinta(pele_lid))
            pth = skia.Path(); pth.moveTo(-r, 0.005); pth.quadTo(0, 0.05, r, 0.005); c.drawPath(pth, traco(C["pupila"], 0.026))
        else:
            c.drawCircle(0, 0, r, contorno())
            if ps > 0.15:
                yl = -r + 2 * r * ps; dx = math.sqrt(max(0.0, r * r - yl * yl))
                c.drawLine(-dx, yl, dx, yl, traco(C["pupila"], 0.02))
    else:
        r = 0.07
        clip = oval(0, 0, r + 0.002, r + 0.002)
        c.save(); c.clipPath(clip, doAntiAlias=True)
        c.drawCircle(ox * 0.022, oy * 0.022, r, tinta(C["olho"]))
        c.drawCircle(ox * 0.022, oy * 0.022, r * 0.56, tinta(C["pupila"]))
        c.drawCircle(ox * 0.022 - r * 0.33, oy * 0.022 - r * 0.36, r * 0.27, tinta(C["branco_olho"]))
        c.drawCircle(ox * 0.022 + r * 0.3, oy * 0.022 + r * 0.32, r * 0.1, tinta(C["branco_olho"], 0.8))
        # pálpebras (pele) cobrindo de cima e de baixo
        ps, pi = e["palp_sup"], e["palp_inf"]
        if ps > 0:
            c.drawRect(skia.Rect.MakeLTRB(-r - 0.01, -r - 0.01, r + 0.01, -r + 2 * r * ps), tinta(pele_lid))
        if pi > 0:
            pth = skia.Path(); pth.moveTo(-r - 0.01, r + 0.01); pth.lineTo(-r - 0.01, r - 2 * r * pi * 0.6)
            pth.quadTo(0, r - 2 * r * pi * 1.15, r + 0.01, r - 2 * r * pi * 0.6); pth.lineTo(r + 0.01, r + 0.01); pth.close()
            c.drawPath(pth, tinta(pele_lid))
        c.restore()
        if ps >= 0.99:   # fechado: linha curva
            pth = skia.Path(); pth.moveTo(-r, 0.005); pth.quadTo(0, 0.045, r, 0.005); c.drawPath(pth, traco(C["pupila"], 0.026))
        elif ps > 0.15:
            yl = -r + 2 * r * ps
            c.drawLine(-r * 1.05, yl, r * 1.05, yl, traco(C["pupila"], 0.02))
        if pi > 0.2:
            pth = skia.Path(); pth.moveTo(-r, r - 2 * r * pi * 0.6); pth.quadTo(0, r - 2 * r * pi * 1.15, r, r - 2 * r * pi * 0.6)
            c.drawPath(pth, traco(C["pele_s"], 0.014))
    c.restore()


def _sobrancelha(c, x, y, sob, lado, esc_x=1.0):
    """sob = (altura do canto interno, altura do externo, arco). lado=-1 (esq. da tela) / +1 (dir.)."""
    hi, he, arco = sob
    xi, xe = x - lado * 0.085 * esc_x, x + lado * 0.095 * esc_x
    yi, ye = y - hi, y - he
    pth = skia.Path(); pth.moveTo(xi, yi); pth.quadTo((xi + xe) / 2, (yi + ye) / 2 - 0.03 - arco, xe, ye)
    c.drawPath(pth, traco(C["cabelo"], 0.052))


def _boca(c, x, y, e, esc=1.0):
    tipo, ab, so, la = e["boca"], e["abertura"], e["sorriso"], e["largura"] * esc
    w = 0.075 * la
    if tipo in ("linha", "meio_sorriso", "ondulada"):
        pth = skia.Path()
        if tipo == "ondulada":
            pth.moveTo(x - w, y + 0.01); pth.cubicTo(x - w * 0.4, y - 0.02, x + w * 0.2, y + 0.03, x + w, y + 0.0)
        elif tipo == "meio_sorriso":
            pth.moveTo(x - w, y + 0.005); pth.quadTo(x + w * 0.2, y + 0.03 * so, x + w * 1.1, y - 0.03 * so)
        else:
            pth.moveTo(x - w, y - 0.02 * so); pth.quadTo(x, y + 0.035 * so, x + w, y - 0.02 * so)
        c.drawPath(pth, traco(C["boca"], 0.026))
    elif tipo in ("o", "o_lado"):
        dx = 0.03 if tipo == "o_lado" else 0.0
        c.drawOval(skia.Rect.MakeXYWH(x + dx - 0.03 * la - 0.012, y - 0.03 - 0.02 * ab, 0.06 * la + 0.024, 0.05 + 0.07 * ab), tinta(C["boca_interna"]))
        c.drawOval(skia.Rect.MakeXYWH(x + dx - 0.03 * la - 0.012, y - 0.03 - 0.02 * ab, 0.06 * la + 0.024, 0.05 + 0.07 * ab), traco(C["boca"], 0.012))
    else:   # sorriso_aberto | aberta | dentes_cerrados
        h = 0.04 + 0.11 * ab
        pth = skia.Path()
        cv = 0.05 * so
        pth.moveTo(x - w * 1.1, y - cv); pth.quadTo(x, y - cv * 0.2 - 0.01, x + w * 1.1, y - cv)
        pth.quadTo(x + w * 0.9, y + h, x, y + h + cv * 0.4); pth.quadTo(x - w * 0.9, y + h, x - w * 1.1, y - cv); pth.close()
        c.drawPath(pth, tinta(C["boca_interna"]))
        c.save(); c.clipPath(pth, doAntiAlias=True)
        if e["dentes"]:
            c.drawRect(skia.Rect.MakeLTRB(x - w * 1.2, y - 0.08, x + w * 1.2, y - cv * 0.2 + 0.022), tinta(C["dentes"]))
        if tipo != "dentes_cerrados":
            c.drawOval(skia.Rect.MakeXYWH(x - w * 0.6, y + h * 0.55, w * 1.2, h * 0.7), tinta(C["lingua"]))
        else:
            c.drawRect(skia.Rect.MakeLTRB(x - w * 1.2, y + 0.005, x + w * 1.2, y + 0.08), tinta(C["dentes"]))
            c.drawLine(x - w * 1.2, y + 0.01, x + w * 1.2, y + 0.01, traco(C["boca_interna"], 0.006))
        c.restore()
        c.drawPath(pth, traco(C["boca"], 0.014))


def desenhar_cabeca(c, vista, e, lado_luz):
    """Cabeça no sistema do osso 'cabeca' (origem na base do pescoço)."""
    hy = -0.58   # centro da cabeça acima da base do pescoço
    rw, rh = PROP["largura_cabeca"] / 2, 0.5
    # pescoço
    pesc = rrect(-0.105, -0.12, 0.105, 0.04, 0.04)
    c.drawPath(pesc, tinta(C["pele_s"]))
    sh = {"frente": 0.0, "tres_quartos": 0.12, "perfil": 0.26, "costas": 0.0}[vista]
    # orelhas (atrás da cabeça)
    def orelha(x, esc=1.0):
        o = oval(x, hy + 0.04, 0.095 * esc, 0.12); preenche(c, o, C["pele"], C["pele_s"], lado_luz, 0.35)
        dob = skia.Path(); dob.moveTo(x - 0.02 * esc, hy - 0.02); dob.quadTo(x + 0.05 * esc * (1 if x > 0 else -1), hy + 0.04, x - 0.01 * esc, hy + 0.1)
        c.drawPath(dob, traco(C["pele_s"], 0.014))
    if vista in ("frente", "costas"):
        orelha(-rw); orelha(rw)
    elif vista == "tres_quartos":
        orelha(-rw * 0.95)
    # crânio
    cab = oval(0, hy, rw * (1.04 if vista == "perfil" else 1.0), rh)
    if vista == "perfil":   # nariz e queixo
        nariz = skia.Path(); nariz.moveTo(rw * 0.94, hy + 0.06); nariz.quadTo(rw * 1.16, hy + 0.15, rw * 0.95, hy + 0.2); nariz.close()
        cab = skia.Op(cab, nariz, skia.PathOp.kUnion_PathOp) or cab
    preenche(c, cab, C["pele"], C["pele_s"], lado_luz, 0.36)
    if vista == "perfil":
        orelha(-0.06, 0.85)
    if vista != "costas":
        olho_y = hy + 0.06
        def pl(x):   # tom da pele onde o olho está (o crescente de sombra fica do lado lado_luz)
            return C["pele_s"] if x * lado_luz > 0.06 else C["pele"]
        if vista == "perfil":   # no perfil, olho/boca ficam dentro do contorno da cabeça
            c.save(); c.clipPath(cab, doAntiAlias=True)
        if vista == "frente":
            _olho(c, -0.205, olho_y, e, pele_lid=pl(-0.205)); _olho(c, 0.205, olho_y, e, pele_lid=pl(0.205))
            _sobrancelha(c, -0.205, olho_y - 0.17, e["sobr"], -1); _sobrancelha(c, 0.205, olho_y - 0.17, e["sobr_e"] or e["sobr"], 1)
            nar = skia.Path(); nar.moveTo(0.012, hy + 0.13); nar.quadTo(0.052, hy + 0.19, -0.008, hy + 0.205)
            c.drawPath(nar, traco(C["pele_s"], 0.02))
            _boca(c, 0.0 + e["assimetria"] * 0.02, hy + 0.3, e)
        elif vista == "tres_quartos":
            _olho(c, -0.2 + sh, olho_y, e, 1.0, pele_lid=pl(-0.2 + sh)); _olho(c, 0.2 + sh * 0.8, olho_y, e, 0.78, pele_lid=pl(0.2 + sh * 0.8))
            _sobrancelha(c, -0.2 + sh, olho_y - 0.17, e["sobr"], -1); _sobrancelha(c, 0.2 + sh * 0.8, olho_y - 0.17, e["sobr_e"] or e["sobr"], 1, 0.78)
            nar = skia.Path(); nar.moveTo(0.04 + sh, hy + 0.12); nar.quadTo(0.11 + sh, hy + 0.19, 0.03 + sh, hy + 0.21)
            c.drawPath(nar, traco(C["pele_s"], 0.02))
            _boca(c, sh * 0.9, hy + 0.3, e, 0.85)
        else:   # perfil
            _olho(c, rw * 0.55, olho_y, e, 0.62, pele_lid=pl(rw * 0.55))
            _sobrancelha(c, rw * 0.55, olho_y - 0.17, e["sobr_e"] or e["sobr"], 1, 0.7)
            _boca(c, rw * 0.66, hy + 0.31, e, 0.5)
            c.restore()
    # cabelo (liso, franja lateral) por vista
    cb = skia.Path()
    if vista == "frente":
        cb.moveTo(-0.49, hy + 0.02); cb.cubicTo(-0.55, hy - 0.62, 0.55, hy - 0.66, 0.49, hy)
        cb.lineTo(0.42, hy - 0.08); cb.cubicTo(0.30, hy - 0.18, 0.05, hy - 0.12, -0.12, hy - 0.27)
        cb.cubicTo(-0.22, hy - 0.16, -0.34, hy - 0.16, -0.42, hy - 0.04); cb.close()
    elif vista == "tres_quartos":
        cb.moveTo(-0.50, hy + 0.12); cb.cubicTo(-0.58, hy - 0.60, 0.50, hy - 0.70, 0.49, hy - 0.04)
        cb.lineTo(0.44, hy - 0.12); cb.cubicTo(0.36, hy - 0.2, 0.18, hy - 0.14, 0.02, hy - 0.28)
        cb.cubicTo(-0.08, hy - 0.18, -0.2, hy - 0.16, -0.26, hy - 0.05)
        cb.cubicTo(-0.32, hy + 0.02, -0.38, hy + 0.1, -0.44, hy + 0.2); cb.close()
    elif vista == "perfil":
        cb.moveTo(-0.47, hy + 0.26); cb.cubicTo(-0.62, hy - 0.5, 0.2, hy - 0.72, 0.47, hy - 0.2)
        cb.lineTo(0.5, hy - 0.12); cb.cubicTo(0.38, hy - 0.2, 0.25, hy - 0.18, 0.16, hy - 0.24)
        cb.cubicTo(0.08, hy - 0.1, -0.02, hy - 0.04, -0.12, hy - 0.06)
        cb.cubicTo(-0.2, hy + 0.06, -0.28, hy + 0.2, -0.36, hy + 0.3); cb.close()
    else:
        cb.moveTo(-0.49, hy + 0.1); cb.cubicTo(-0.56, hy - 0.66, 0.56, hy - 0.66, 0.49, hy + 0.1)
        cb.cubicTo(0.4, hy + 0.42, -0.4, hy + 0.42, -0.49, hy + 0.1); cb.close()
    c.drawPath(cb, tinta(C["cabelo"])); sombra(c, cb, C["cabelo_s"], lado_luz, 0.32)
    # mechas (detalhe): traços em tom de sombra e um brilho
    c.save(); c.clipPath(cb, doAntiAlias=True)
    for k in range(5):
        x0 = -0.35 + k * 0.17
        pth = skia.Path(); pth.moveTo(x0, hy - 0.48); pth.quadTo(x0 + 0.08, hy - 0.3, x0 + 0.02, hy - 0.08 + (0.25 if vista == "costas" else 0))
        c.drawPath(pth, traco(C["cabelo_s"], 0.016))
    c.restore()
    br = skia.Path(); br.moveTo(-0.28 + sh * 0.5, hy - 0.41); br.quadTo(-0.05 + sh * 0.5, hy - 0.5, 0.16 + sh * 0.5, hy - 0.42)
    c.drawPath(br, traco(C["cabelo_b"], 0.045))
    c.drawPath(cb, contorno())
    c.drawPath(cab, contorno(LW * 0.9)) if False else None


# ------------------------------------------------------------------ tronco, quadril, estampa
def _estampa(c, cx, y_base, larg, curva=0.6, perspectiva=0.0, espelhado=False):
    f = skia.Font(NUNITO, 100); pal = [("Modo", C["estampa_modo"]), ("Curioso", C["estampa_curioso"])]
    total = f.measureText("Modo Curioso")
    esc = larg / total
    c.save(); c.translate(cx, y_base)
    if espelhado:
        c.scale(-1, 1)   # desfaz o espelho da vista: a estampa continua legível
    c.scale(esc, esc); c.translate(-total / 2, 0)
    x = 0.0
    for i, (t, cor) in enumerate(pal):
        for ch in t:
            w = f.measureText(ch); xm = (x + w / 2) / total - 0.5
            dy = -curva * 6 * (1 - 4 * xm * xm)
            sx = 1.0 - perspectiva * (xm + 0.5)   # letras do lado distante um pouco menores
            c.save(); c.translate(x, dy); c.scale(sx, sx); c.rotate(curva * xm * 10)
            p = tinta(cor, 0.93); c.drawString(ch, 0, 0, f, p); c.restore()
            x += w
        if i == 0:
            x += f.measureText(" ")
    c.restore()


def _forma_tronco(vista):
    """v2.1 (27/11/2026, aprovado pelo diretor): do pescoço ao ombro a linha DESCE em curva (trapézio), sem patamar reto; a quina do ombro é redonda."""
    p = skia.Path(); top, hem = OMBRO_Y - 0.1, 0.0
    if vista in ("frente", "costas"):
        p.moveTo(-0.13, top - 0.025); p.lineTo(0.13, top - 0.025)
        p.cubicTo(0.22, top - 0.02, 0.31, top + 0.035, 0.40, top + 0.075)          # trapézio descendo
        p.cubicTo(0.455, top + 0.10, 0.485, top + 0.14, 0.485, top + 0.20)         # quina redonda do ombro
        p.quadTo(0.49, -0.55, 0.42, hem); p.lineTo(-0.42, hem); p.quadTo(-0.49, -0.55, -0.485, top + 0.20)
        p.cubicTo(-0.485, top + 0.14, -0.455, top + 0.10, -0.40, top + 0.075)
        p.cubicTo(-0.31, top + 0.035, -0.22, top - 0.02, -0.13, top - 0.025)
    elif vista == "tres_quartos":
        p.moveTo(-0.11, top - 0.025); p.lineTo(0.10, top - 0.025)
        p.cubicTo(0.18, top - 0.02, 0.26, top + 0.03, 0.32, top + 0.07)
        p.cubicTo(0.37, top + 0.095, 0.39, top + 0.14, 0.39, top + 0.19)
        p.quadTo(0.43, -0.55, 0.35, hem); p.lineTo(-0.36, hem); p.quadTo(-0.44, -0.55, -0.42, top + 0.19)
        p.cubicTo(-0.42, top + 0.13, -0.39, top + 0.095, -0.34, top + 0.07)
        p.cubicTo(-0.27, top + 0.03, -0.19, top - 0.02, -0.11, top - 0.025)
    else:
        p.moveTo(-0.10, top - 0.025); p.lineTo(0.08, top - 0.025)
        p.cubicTo(0.15, top - 0.015, 0.21, top + 0.03, 0.235, top + 0.10)
        p.quadTo(0.30, -0.6, 0.24, hem); p.lineTo(-0.22, hem); p.quadTo(-0.27, -0.55, -0.225, top + 0.10)
        p.cubicTo(-0.20, top + 0.03, -0.16, top - 0.015, -0.10, top - 0.025)
    p.close(); return p


def desenhar_tronco(c, vista, lado_luz, espelhado):
    tr = _forma_tronco(vista)
    c.drawPath(tr, tinta(C["camisa"]))
    if vista in ("frente", "tres_quartos"):
        larg = 0.56 * 0.86 * (MOD["estampa"]["tres_quartos"]["compressao"] if vista == "tres_quartos" else 1.0)
        cx = 0.0 if vista == "frente" else 0.06
        _estampa(c, cx, -0.64, larg, curva=0.6 if vista == "frente" else 0.9,
                 perspectiva=0.0 if vista == "frente" else 0.18, espelhado=espelhado)
    sombra(c, tr, C["camisa_s"], lado_luz, 0.28, multiplicar=0xFFB3C2CF)   # estampa recebe a sombra do tecido
    # dobras do tecido (detalhe, em tom de sombra) e costura da barra
    for s in (-1, 1):
        if vista == "perfil" and s < 0:
            continue
        x0 = s * (0.33 if vista != "perfil" else 0.12)
        pth = skia.Path(); pth.moveTo(x0, -0.9); pth.quadTo(x0 - s * 0.07, -0.8, x0 - s * 0.04, -0.68)
        c.drawPath(pth, traco(C["camisa_s"], 0.018))
    b = tr.getBounds()
    c.save(); c.clipPath(tr, doAntiAlias=True)
    c.drawLine(b.left(), -0.035, b.right(), -0.035, traco(C["gola"], 0.012)); c.restore()
    c.drawPath(tr, contorno())
    # gola
    if vista == "frente":
        dec = skia.Path(); dec.moveTo(-0.17, OMBRO_Y - 0.1); dec.quadTo(0, OMBRO_Y + 0.1, 0.17, OMBRO_Y - 0.1); dec.close()
        c.drawPath(dec, tinta(C["pele_s"])); c.drawPath(dec, traco(C["gola"], 0.045))
    elif vista == "tres_quartos":
        dec = skia.Path(); dec.moveTo(-0.08, OMBRO_Y - 0.1); dec.quadTo(0.06, OMBRO_Y + 0.08, 0.2, OMBRO_Y - 0.1); dec.close()
        c.drawPath(dec, tinta(C["pele_s"])); c.drawPath(dec, traco(C["gola"], 0.045))
    elif vista == "perfil":
        c.drawLine(-0.02, OMBRO_Y - 0.1, 0.16, OMBRO_Y - 0.06, traco(C["gola"], 0.045))
    else:
        c.drawLine(-0.17, OMBRO_Y - 0.1, 0.17, OMBRO_Y - 0.1, traco(C["gola"], 0.045))


def desenhar_quadril(c, vista, lado_luz):
    """Bloco do quadril (jeans) logo abaixo da barra da camiseta, com bolsos e costuras."""
    w = {"frente": 0.40, "costas": 0.40, "tres_quartos": 0.36, "perfil": 0.24}[vista]
    q = rrect(-w, -0.02, w, 0.2, 0.06)
    preenche(c, q, C["jeans"], C["jeans_s"], lado_luz, 0.25)
    if vista == "frente":
        for s in (-1, 1):
            pth = skia.Path(); pth.moveTo(s * 0.33, 0.0); pth.quadTo(s * 0.3, 0.1, s * 0.18, 0.12); c.drawPath(pth, traco(C["barra"], 0.012))
        c.drawLine(0.0, 0.0, 0.0, 0.17, traco(C["jeans_s"], 0.012))
    elif vista == "costas":
        for s in (-1, 1):
            c.drawPath(rrect(s * 0.28 - 0.08, 0.04, s * 0.28 + 0.08, 0.17, 0.02), traco(C["barra"], 0.012))


def forma_braco():
    return capsula(OSS["braco"], 0.19, 0.165)


def forma_antebraco():
    return capsula(OSS["antebraco"] + 0.02, 0.165, 0.13)


def forma_coxa():
    return capsula(OSS["coxa"] + 0.04, 0.34, 0.29)


def forma_canela():
    p = skia.Path(); L = OSS["canela"] - 0.02
    p.moveTo(-0.145, -0.04); p.lineTo(0.145, -0.04); p.lineTo(0.135, L); p.lineTo(-0.135, L); p.close()
    return p


def desenhar_manga(c, lado_luz, distante=False):
    """v2.1: manga com topo em cúpula: o ombro fica redondo em qualquer ângulo do braço."""
    mr = skia.Path(); r = 0.15                                          # cúpula mais baixa: continua a curva do trapézio
    mr.moveTo(-0.14, 0.26); mr.lineTo(-r, 0.04)
    mr.cubicTo(-r, -0.03, -0.08, -0.07, 0.0, -0.07); mr.cubicTo(0.08, -0.07, r, -0.03, r, 0.04)
    mr.lineTo(0.14, 0.26); mr.quadTo(0.0, 0.275, -0.14, 0.26); mr.close()
    cam, cam_s = (C["camisa_s"], C["camisa_s"]) if distante else (C["camisa"], C["camisa_s"])
    preenche(c, mr, cam, cam_s, lado_luz, 0.3)
    c.drawLine(-0.12, 0.225, 0.12, 0.225, traco(C["gola"], 0.012))


def desenhar_barra(c, lado_luz, distante=False):
    L = OSS["canela"]
    barra = rrect(-0.16, L - 0.17, 0.16, L - 0.02, 0.04)
    preenche(c, barra, C["barra"] if not distante else C["jeans_s"], C["jeans_s"], lado_luz, 0.25)
    c.drawLine(-0.14, L - 0.13, 0.14, L - 0.13, traco(C["jeans_s"], 0.008))


def membro(c, segs, cor, cor_s, distante=False):
    """Preenche cada segmento no seu osso e desenha UM contorno da união (junta contínua ao dobrar)."""
    if distante:
        cor = cor_s
    uni = None
    for m, forma, ll in segs:
        c.save(); c.concat(m); c.drawPath(forma, tinta(cor)); sombra(c, forma, cor_s, ll, 0.25); c.restore()
        w = skia.Path(forma); w.transform(m)
        uni = w if uni is None else (skia.Op(uni, w, skia.PathOp.kUnion_PathOp) or uni)
    if uni is not None:
        c.drawPath(uni, contorno())


def desenhar_pe(c, vista, lado_luz, distante=False):
    t, ts = (C["tenis_s"], C["tenis_s"]) if distante else (C["tenis"], C["tenis_s"])
    if vista in ("frente", "costas"):
        f = rrect(-0.19, -0.02, 0.19, 0.22, 0.1)
        preenche(c, f, t, ts, lado_luz, 0.3, linha=False)
        c.drawRect(skia.Rect.MakeLTRB(-0.18, 0.12, 0.18, 0.155), tinta(C["tenis_faixa"]))
        c.drawRect(skia.Rect.MakeLTRB(-0.18, 0.185, 0.18, 0.215), tinta(C["sola"]))
        if vista == "frente":
            for k in range(3):
                c.drawLine(-0.06, 0.01 + k * 0.03, 0.06, 0.01 + k * 0.03, traco(C["tenis_s"], 0.01))
        c.drawPath(f, contorno())
    else:   # lateral (perfil e 3/4): bico para a frente (+x)
        if vista == "tres_quartos":
            c.save(); c.scale(0.78, 1.0)
        f = skia.Path(); f.moveTo(-0.12, -0.02); f.lineTo(0.08, -0.02); f.quadTo(0.3, 0.04, 0.33, 0.16)
        f.lineTo(0.33, 0.22); f.lineTo(-0.14, 0.22); f.quadTo(-0.17, 0.1, -0.12, -0.02); f.close()
        preenche(c, f, t, ts, lado_luz, 0.25, linha=False)
        c.drawRect(skia.Rect.MakeLTRB(-0.15, 0.185, 0.335, 0.22), tinta(C["sola"]))
        fx = skia.Path(); fx.moveTo(-0.12, 0.13); fx.quadTo(0.1, 0.06, 0.3, 0.12); c.drawPath(fx, traco(C["tenis_faixa"], 0.03))
        for k in range(3):
            c.drawLine(0.0 + k * 0.05, 0.0 + k * 0.02, 0.04 + k * 0.05, 0.03 + k * 0.02, traco(C["tenis_s"], 0.01))
        c.drawPath(f, contorno())
        if vista == "tres_quartos":
            c.restore()


# ------------------------------------------------------------------ montagem do personagem
ORDEM = {   # do fundo para a frente (d = lado direito do personagem)
    "frente": ["perna_d", "perna_e", "quadril", "tronco", "cabeca", "braco_d", "braco_e"],
    "costas": ["perna_d", "perna_e", "quadril", "tronco", "braco_d", "braco_e", "cabeca"],
    "tres_quartos": ["braco_e*", "perna_e*", "perna_d", "quadril", "tronco", "cabeca", "braco_d"],
    "perfil": ["braco_e*", "perna_e*", "perna_d", "quadril", "tronco", "cabeca", "braco_d"],
}
VISTA_MAO = {"frente": "lado", "costas": "lado", "tres_quartos": "dorso", "perfil": "dorso"}


# auditoria opcional: se for uma lista, cada chamada de desenhar() registra (vista, pose) para verificações (ex.: cotovelos)
AUDITORIA = None


def desenhar(c, x_pe, y_pe, altura_px, vista="frente", direcao=1, pose=None, rosto=None, luz=-1):
    pose = pose or pose_base(vista)
    if AUDITORIA is not None:
        AUDITORIA.append((vista, {k: v for k, v in pose.items() if not callable(v)}))
    e = rosto if isinstance(rosto, dict) else EXPRESSOES[rosto or "neutro"]
    u = altura_px / 4.0
    c.save(); c.translate(x_pe, y_pe); c.scale(u * direcao, u)
    espelhado = direcao < 0
    luz_local = luz * direcao
    M = esqueleto(pose, vista)

    def com(m, f):
        c.save(); c.concat(m); f(_lado_luz(m, luz_local)); c.restore()

    for item in ORDEM[vista]:
        dist = item.endswith("*"); nome = item.rstrip("*")
        if nome.startswith("perna_"):
            s = nome[-1]
            com(M[f"pe_{s}"], lambda ll: desenhar_pe(c, vista, ll, dist))
            membro(c, [(M[f"canela_{s}"], forma_canela(), _lado_luz(M[f"canela_{s}"], luz_local)),
                       (M[f"coxa_{s}"], forma_coxa(), _lado_luz(M[f"coxa_{s}"], luz_local))], C["jeans"], C["jeans_s"], dist)
            com(M[f"canela_{s}"], lambda ll: desenhar_barra(c, ll, dist))
        elif nome == "quadril":
            com(M["raiz"], lambda ll: desenhar_quadril(c, vista, ll))
        elif nome == "tronco":
            com(M["tronco"], lambda ll: desenhar_tronco(c, vista, ll, espelhado))
        elif nome == "cabeca":
            com(M["cabeca"], lambda ll: desenhar_cabeca(c, vista, e, ll))
        elif nome.startswith("braco_"):
            s = nome[-1]
            mv = pose.get(f"mao_vista_{s}") or VISTA_MAO[vista]
            espelho_mao = (s == "e") if vista in ("frente", "tres_quartos", "perfil") else (s == "d")
            membro(c, [(M[f"antebraco_{s}"], forma_antebraco(), _lado_luz(M[f"antebraco_{s}"], luz_local)),
                       (M[f"braco_{s}"], forma_braco(), _lado_luz(M[f"braco_{s}"], luz_local))], C["pele"], C["pele_s"], dist)
            com(M[f"mao_{s}"], lambda ll: desenhar_mao(c, pose[f"dedos_{s}"], mv, espelho_mao, ll, pose.get(f"objeto_{s}")))
            com(M[f"braco_{s}"], lambda ll: desenhar_manga(c, ll, dist))
    c.restore()
    return M
