#!/usr/bin/env python3
"""Heitor — rig 2D vetorial v1 (PROPOSTA, aguardando aprovação; não é o modelo oficial).

Construído só a partir da especificação do skill/IDENTIDADE_OFICIAL.md:
10–12 anos, ~4 cabeças de altura, cabeça redonda, SEM bochecha rosada, cabelo liso castanho-escuro
com franja lateral, olhos castanhos, pele #ffd9c2, camiseta azul #3d80d8 com a estampa "Modo Curioso"
(ID-002/ID-003), calça jeans com barra dobrada, tênis branco com faixa azul.
Vistas nesta versão: frente e costas (3/4 e perfil ficam para a v2).

API: desenhar(canvas, vista, expr, x_pe, y_pe, altura_px, luz=-1, rot=0, olhar=0.0, boca=None, extra={})
"""
import json
from pathlib import Path
import skia

P = Path(__file__).resolve().parents[1]
FON = P.parents[1] / "assets" / "fontes"
C = {  # paleta travada (hex da especificação)
    "pele": 0xFFFFD9C2, "pele_s": 0xFFEFB594,
    "cabelo": 0xFF3A2316, "cabelo_s": 0xFF24140A, "cabelo_b": 0xFF5C3A25,
    "olho": 0xFF6A3D20, "pupila": 0xFF2A160B,
    "camisa": 0xFF3D80D8, "camisa_s": 0xFF2B61B0, "gola": 0xFF2855A0,
    "jeans": 0xFF34507F, "jeans_s": 0xFF243A60, "barra": 0xFF4A6B9F,
    "tenis": 0xFFF6F4F0, "tenis_s": 0xFFD9D4CC, "tenis_faixa": 0xFF3D80D8,
    "contorno": 0xFF2A1D17, "boca": 0xFF7A3B2E, "lingua": 0xFFD9786B, "branco": 0xFFFFFFFF,
    "estampa_modo": 0xFFF2EFE8, "estampa_curioso": 0xFFFFC21F,
}
RIG = {
    "nome": "Heitor", "versao": "v1-PROPOSTA", "altura_cabecas": 4.0, "altura_m": 1.40,
    "vistas": ["frente", "costas"], "expressoes": ["neutro", "dormindo", "acordando", "surpreso", "assustado"],
    "paleta": {k: "#%06x" % (v & 0xFFFFFF) for k, v in C.items()},
    "estampa": {"texto": "Modo Curioso", "fonte": "Nunito-ExtraBold", "largura_rel_peito": 0.56,
                "cores": {"Modo": "#f2efe8", "Curioso": "#ffc21f"}, "acabamento": "serigrafia fosca, recebe a sombra do tecido"},
}
_NUNITO = skia.Typeface.MakeFromFile(str(FON / "Nunito-ExtraBold.ttf"))


def _pt(c, cor):
    return skia.Paint(AntiAlias=True, Color=cor)


def _contorno(u):
    return skia.Paint(AntiAlias=True, Color=C["contorno"], Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.0, 0.018 * u),
                      StrokeJoin=skia.Paint.kRound_Join)


def _sombra_lado(c, forma, cor, luz, cx, u, frac=0.32, multiplicar=None):
    """Um tom de sombra em crescente no lado oposto à luz (forma menos a forma deslocada para a luz)."""
    b = forma.getBounds()
    desl = skia.Path(forma); desl.offset(luz * b.width() * frac * 0.9, -b.height() * 0.02)
    cresc = skia.Op(forma, desl, skia.PathOp.kDifference_PathOp)
    if cresc is None:
        return
    if multiplicar is not None:   # escurece o que estiver embaixo (tecido + estampa), como luz real
        c.drawPath(cresc, skia.Paint(AntiAlias=True, Color=multiplicar, BlendMode=skia.BlendMode.kMultiply))
    else:
        c.drawPath(cresc, _pt(c, cor))


def _rrect(x0, y0, x1, y1, r):
    p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r)); return p


def _estampa(c, cx, y_base, larg_alvo, u, curva=0.0):
    """Estampa "Modo Curioso" em curvas, com leve arco do peito (serigrafia fosca)."""
    f = skia.Font(_NUNITO, 100)
    pal = [("Modo", C["estampa_modo"]), ("Curioso", C["estampa_curioso"])]
    larg = sum(f.measureText(t) for t, _ in pal) + f.measureText(" ")
    esc = larg_alvo / larg
    c.save(); c.translate(cx - larg_alvo / 2, y_base); c.scale(esc, esc)
    x = 0.0
    for i, (t, cor) in enumerate(pal):
        for ch in t:
            w = f.measureText(ch)
            xm = (x + w / 2) / larg - 0.5   # -0.5..0.5
            dy = curva * 100 * (xm * xm * 4 - 1) * -0.06
            c.save(); c.translate(x, dy); c.rotate(curva * xm * 10)
            p = skia.Paint(AntiAlias=True, Color=cor); p.setAlphaf(0.93)   # tinta fosca, levemente translúcida
            c.drawString(ch, 0, 0, f, p); c.restore()
            x += w
        if i == 0:
            x += f.measureText(" ")
    c.restore()


def _olhos(c, u, cx, y, expr, olhar, vista):
    dx = 0.205 * u
    for s in (-1, 1):
        ox = cx + s * dx
        if expr == "dormindo":
            p = skia.Path(); p.moveTo(ox - 0.075 * u, y); p.quadTo(ox, y + 0.05 * u, ox + 0.075 * u, y)
            c.drawPath(p, skia.Paint(AntiAlias=True, Color=C["pupila"], Style=skia.Paint.kStroke_Style,
                                     StrokeWidth=0.03 * u, StrokeCap=skia.Paint.kRound_Cap))
        elif expr in ("surpreso", "assustado"):
            r = 0.095 * u if expr == "surpreso" else 0.11 * u
            c.drawCircle(ox, y, r, _pt(c, C["branco"]))
            c.drawCircle(ox, y, r, _contorno(u))
            pr = 0.045 * u if expr == "surpreso" else 0.028 * u
            c.drawCircle(ox + olhar * 0.03 * u, y, pr, _pt(c, C["pupila"]))
        else:
            r = 0.068 * u
            c.drawCircle(ox + olhar * 0.05 * u, y, r, _pt(c, C["olho"]))
            c.drawCircle(ox + olhar * 0.05 * u, y, r * 0.55, _pt(c, C["pupila"]))
            c.drawCircle(ox + olhar * 0.05 * u - r * 0.35, y - r * 0.35, r * 0.3, _pt(c, C["branco"]))
            if expr == "acordando":   # pálpebra meio fechada
                c.save(); c.clipRect(skia.Rect.MakeLTRB(ox - r - 2, y - r - 2, ox + r + 2, y + 0.1 * r))
                c.drawCircle(ox + olhar * 0.05 * u, y, r + 1, _pt(c, C["pele_s"])); c.restore()
                c.drawLine(ox - r, y + 0.1 * r, ox + r, y + 0.1 * r,
                           skia.Paint(AntiAlias=True, Color=C["pupila"], StrokeWidth=0.022 * u, StrokeCap=skia.Paint.kRound_Cap))


def _sobrancelhas(c, u, cx, y, expr):
    ang = {"neutro": 0, "dormindo": -4, "acordando": -6, "surpreso": 10, "assustado": 18}.get(expr, 0)
    dy = {"surpreso": -0.06, "assustado": -0.085}.get(expr, 0.0) * u
    for s in (-1, 1):
        c.save(); c.translate(cx + s * 0.21 * u, y + dy); c.rotate(-s * ang)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-0.1 * u, -0.026 * u, 0.1 * u, 0.026 * u), 0.026 * u, 0.026 * u),
                    _pt(c, C["cabelo"]))
        c.restore()


def _boca(c, u, cx, y, expr, boca):
    forma = boca or {"neutro": "linha", "dormindo": "o_peq", "acordando": "linha", "surpreso": "o", "assustado": "aberta"}[expr]
    sp = skia.Paint(AntiAlias=True, Color=C["boca"], Style=skia.Paint.kStroke_Style, StrokeWidth=0.026 * u,
                    StrokeCap=skia.Paint.kRound_Cap)
    if forma == "linha":
        p = skia.Path(); p.moveTo(cx - 0.07 * u, y); p.quadTo(cx, y + 0.012 * u, cx + 0.07 * u, y); c.drawPath(p, sp)
    elif forma == "o_peq":
        c.drawOval(skia.Rect.MakeXYWH(cx - 0.025 * u, y - 0.018 * u, 0.05 * u, 0.04 * u), _pt(c, C["boca"]))
    elif forma == "o":
        c.drawOval(skia.Rect.MakeXYWH(cx - 0.045 * u, y - 0.04 * u, 0.09 * u, 0.1 * u), _pt(c, C["boca"]))
    else:  # aberta (susto)
        r = skia.Rect.MakeXYWH(cx - 0.09 * u, y - 0.04 * u, 0.18 * u, 0.15 * u)
        c.drawOval(r, _pt(c, C["boca"]))
        c.save(); c.clipRect(skia.Rect.MakeLTRB(r.left(), y + 0.05 * u, r.right(), r.bottom()))
        c.drawOval(skia.Rect.MakeXYWH(cx - 0.06 * u, y + 0.03 * u, 0.12 * u, 0.1 * u), _pt(c, C["lingua"])); c.restore()


def desenhar(c, vista, expr, x_pe, y_pe, altura_px, luz=-1, rot=0.0, olhar=0.0, boca=None, respira=0.0, extra=None):
    """Desenha o Heitor com os pés em (x_pe, y_pe) e altura total altura_px (4 cabeças)."""
    u = altura_px / 4.0
    c.save(); c.translate(x_pe, y_pe); c.rotate(rot); c.scale(1.0, 1.0)
    cx = 0.0
    k = 1.0 + respira * 0.015   # respiração: tronco sobe/desce de leve
    # ---- pernas e tênis
    for s in (-1, 1):
        perna = _rrect(cx + s * 0.03 * u if s > 0 else cx - 0.38 * u, -1.80 * u, cx + 0.38 * u if s > 0 else cx - 0.03 * u, -0.25 * u, 0.08 * u)
        c.drawPath(perna, _pt(c, C["jeans"])); _sombra_lado(c, perna, C["jeans_s"], luz, cx + s * 0.2 * u, u, 0.25)
        c.drawPath(perna, _contorno(u))
        barra = _rrect(cx + (0.02 * u if s > 0 else -0.40 * u), -0.40 * u, cx + (0.40 * u if s > 0 else -0.02 * u), -0.25 * u, 0.04 * u)
        c.drawPath(barra, _pt(c, C["barra"])); c.drawPath(barra, _contorno(u))
        bx = cx + s * 0.22 * u
        tenis = skia.Path(); tenis.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(bx - 0.2 * u, -0.27 * u, bx + 0.2 * u, 0.0), 0.1 * u, 0.1 * u))
        c.drawPath(tenis, _pt(c, C["tenis"])); _sombra_lado(c, tenis, C["tenis_s"], luz, bx, u, 0.3)
        c.drawRect(skia.Rect.MakeLTRB(bx - 0.19 * u, -0.12 * u, bx + 0.19 * u, -0.08 * u), _pt(c, C["tenis_faixa"]))
        c.drawPath(tenis, _contorno(u))
    # ---- braços (atrás do tronco)
    for s in (-1, 1):
        braco = _rrect(cx + s * 0.47 * u - 0.085 * u, -2.75 * u * k, cx + s * 0.47 * u + 0.085 * u, -1.55 * u, 0.085 * u)
        c.drawPath(braco, _pt(c, C["pele"])); _sombra_lado(c, braco, C["pele_s"], luz, cx + s * 0.47 * u, u, 0.2)
        c.drawPath(braco, _contorno(u))
        c.drawCircle(cx + s * 0.47 * u, -1.5 * u, 0.1 * u, _pt(c, C["pele"])); c.drawCircle(cx + s * 0.47 * u, -1.5 * u, 0.1 * u, _contorno(u))
    # ---- mangas (atrás das bordas do tronco)
    for s_ in (-1, 1):
        manga = _rrect(cx + s_ * 0.44 * u - 0.13 * u, -2.86 * u * k, cx + s_ * 0.44 * u + 0.13 * u, -2.40 * u, 0.11 * u)
        c.drawPath(manga, _pt(c, C["camisa"])); _sombra_lado(c, manga, C["camisa_s"], luz, cx, u, 0.35); c.drawPath(manga, _contorno(u))
    # ---- tronco (camiseta)
    tronco = skia.Path()
    tronco.moveTo(cx - 0.42 * u, -2.86 * u * k); tronco.lineTo(cx + 0.42 * u, -2.86 * u * k)
    tronco.quadTo(cx + 0.47 * u, -2.3 * u, cx + 0.42 * u, -1.72 * u)
    tronco.lineTo(cx - 0.42 * u, -1.72 * u); tronco.quadTo(cx - 0.47 * u, -2.3 * u, cx - 0.42 * u, -2.86 * u * k); tronco.close()
    c.drawPath(tronco, _pt(c, C["camisa"]))
    if vista == "frente":
        _estampa(c, cx, -2.36 * u * k, 0.56 * 0.86 * u, u, curva=0.6)   # 56 % da largura do peito
    _sombra_lado(c, tronco, C["camisa_s"], luz, cx, u, 0.28, multiplicar=0xFFB3C2CF)  # estampa recebe a sombra do tecido
    c.drawPath(tronco, _contorno(u))
    # ---- pescoço e gola (decote em U na frente; reta nas costas)
    pesc = _rrect(cx - 0.11 * u, -3.02 * u * k, cx + 0.11 * u, -2.84 * u * k, 0.04 * u)
    c.drawPath(pesc, _pt(c, C["pele_s"]))
    if vista == "frente":
        dec = skia.Path(); dec.moveTo(cx - 0.17 * u, -2.86 * u * k)
        dec.quadTo(cx, -2.66 * u * k, cx + 0.17 * u, -2.86 * u * k); dec.close()
        c.drawPath(dec, _pt(c, C["pele_s"]))
        c.drawPath(dec, skia.Paint(AntiAlias=True, Color=C["gola"], Style=skia.Paint.kStroke_Style, StrokeWidth=0.045 * u,
                                   StrokeJoin=skia.Paint.kRound_Join))
    else:
        c.drawLine(cx - 0.17 * u, -2.86 * u * k, cx + 0.17 * u, -2.86 * u * k,
                   skia.Paint(AntiAlias=True, Color=C["gola"], StrokeWidth=0.045 * u, StrokeCap=skia.Paint.kRound_Cap))
    # ---- cabeça
    hy = -3.48 * u * k
    cab = skia.Path(); cab.addOval(skia.Rect.MakeLTRB(cx - 0.46 * u, hy - 0.5 * u, cx + 0.46 * u, hy + 0.5 * u))
    for s in (-1, 1):
        c.drawCircle(cx + s * 0.46 * u, hy + 0.04 * u, 0.1 * u, _pt(c, C["pele"])); c.drawCircle(cx + s * 0.46 * u, hy + 0.04 * u, 0.1 * u, _contorno(u))
    c.drawPath(cab, _pt(c, C["pele"])); _sombra_lado(c, cab, C["pele_s"], luz, cx, u, 0.36); c.drawPath(cab, _contorno(u))
    if vista == "frente":
        _olhos(c, u, cx, hy + 0.06 * u, expr, olhar, vista)
        _sobrancelhas(c, u, cx, hy - 0.12 * u, expr)
        nariz = skia.Path(); nariz.moveTo(cx + 0.01 * u, hy + 0.13 * u); nariz.quadTo(cx + 0.05 * u, hy + 0.19 * u, cx - 0.01 * u, hy + 0.2 * u)
        c.drawPath(nariz, skia.Paint(AntiAlias=True, Color=C["pele_s"], Style=skia.Paint.kStroke_Style, StrokeWidth=0.02 * u, StrokeCap=skia.Paint.kRound_Cap))
        _boca(c, u, cx, hy + 0.3 * u, expr, boca)
    # ---- cabelo (liso, franja lateral varrendo da esquerda para a direita)
    cab_p = skia.Path()
    if vista == "frente":
        cab_p.moveTo(cx - 0.49 * u, hy + 0.02 * u)
        cab_p.cubicTo(cx - 0.55 * u, hy - 0.62 * u, cx + 0.55 * u, hy - 0.66 * u, cx + 0.49 * u, hy + 0.0 * u)
        cab_p.lineTo(cx + 0.42 * u, hy - 0.08 * u)
        cab_p.cubicTo(cx + 0.30 * u, hy - 0.18 * u, cx + 0.05 * u, hy - 0.12 * u, cx - 0.12 * u, hy - 0.26 * u)  # ponta da franja
        cab_p.cubicTo(cx - 0.22 * u, hy - 0.16 * u, cx - 0.34 * u, hy - 0.16 * u, cx - 0.42 * u, hy - 0.04 * u)
        cab_p.close()
    else:   # costas: o cabelo cobre a parte de trás da cabeça
        cab_p.moveTo(cx - 0.49 * u, hy + 0.1 * u)
        cab_p.cubicTo(cx - 0.56 * u, hy - 0.66 * u, cx + 0.56 * u, hy - 0.66 * u, cx + 0.49 * u, hy + 0.1 * u)
        cab_p.cubicTo(cx + 0.4 * u, hy + 0.42 * u, cx - 0.4 * u, hy + 0.42 * u, cx - 0.49 * u, hy + 0.1 * u); cab_p.close()
    c.drawPath(cab_p, _pt(c, C["cabelo"])); _sombra_lado(c, cab_p, C["cabelo_s"], luz, cx, u, 0.34)
    brilho = skia.Path(); brilho.moveTo(cx - 0.28 * u, hy - 0.4 * u); brilho.quadTo(cx - 0.05 * u, hy - 0.5 * u, cx + 0.16 * u, hy - 0.42 * u)
    c.drawPath(brilho, skia.Paint(AntiAlias=True, Color=C["cabelo_b"], Style=skia.Paint.kStroke_Style, StrokeWidth=0.045 * u, StrokeCap=skia.Paint.kRound_Cap))
    c.drawPath(cab_p, _contorno(u))
    c.restore()


def folha_de_modelo(arquivo):
    W_, H_ = 2400, 1500
    s = skia.Surface(W_, H_); c = s.getCanvas(); c.clear(0xFFEDEBE6)
    f = skia.Font(_NUNITO, 46); fp = skia.Paint(AntiAlias=True, Color=0xFF1F2A44)
    c.drawString("HEITOR — rig v1 (PROPOSTA, aguardando aprovação)", 60, 80, f, fp)
    f2 = skia.Font(_NUNITO, 30)
    c.drawString("Frente · Costas · expressões: neutro, dormindo, acordando, surpreso, assustado. 3/4 e perfil: v2.", 60, 130, f2, fp)
    desenhar(c, "frente", "neutro", 330, 1380, 1100)
    desenhar(c, "costas", "neutro", 830, 1380, 1100)
    for i, e in enumerate(["neutro", "dormindo", "acordando", "surpreso", "assustado"]):
        x = 1250 + (i % 3) * 380; y = 700 if i < 3 else 1400
        c.save(); c.clipRect(skia.Rect.MakeXYWH(x - 180, y - 520, 360, 480))
        desenhar(c, "frente", e, x, y + 900, 1500)
        c.restore()
        c.drawString(e, x - 70, y - 10, f2, fp)
    s.makeImageSnapshot().save(str(arquivo), skia.kPNG)


if __name__ == "__main__":
    d = P / "recursos" / "heitor_rig_v1_PROPOSTA"; d.mkdir(parents=True, exist_ok=True)
    (d / "rig.json").write_text(json.dumps(RIG, ensure_ascii=False, indent=1))
    folha_de_modelo(d / "folha_de_modelo_v1.png")
    print("ok", d)
