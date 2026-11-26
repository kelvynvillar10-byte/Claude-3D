#!/usr/bin/env python3
"""EP01 — composição dos quadros (1080×1920, 30 qps) a partir de montagem.json e das placas do Blender.

Por quadro: placa reiluminada com câmera 2.5D (zoom/pan com paralaxe) → Heitor rig v2 (pose, expressão com piscada,
respiração; tom de luz X1) + gato/aranha (personagens originais 2D) com teste de profundidade → sobreposições
(sombra do gato, pata, migalha, vento, rótulos com número) → transição de entrada → tremida → legenda → marca d'água.
Inserts (quadrado-cubo, olho do gato, cartelas) são 2D puros.
Uso: compor_ep01.py [--de N --ate M] [--png pasta] [--seg arquivo.mp4]   (sem --seg: gera o MP4 inteiro em paralelo)
"""
import json, math, os, subprocess, sys
from pathlib import Path
import numpy as np, cv2, skia

P = Path(__file__).resolve().parents[1]; RAIZ = P.parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
for sub in ("cenografia/testes", "personagens/heitor/rig_v2/codigo", "personagens/animais", "personagens/heitor/extensoes/x1_tom_de_luz",
            "producoes/ep01_cinco_centimetros/inserts"):
    sys.path.insert(0, str(RAIZ / sub))
import placas_ep01 as PE                                                     # noqa: E402
import e10_testes as ET                                                      # noqa: E402
import heitor_v2 as HV, animacao as AN, gestos as GS                         # noqa: E402
import gato as GATO, aranha as ARANHA                                        # noqa: E402
import tom_de_luz as X1                                                      # noqa: E402
import quadrado_cubo as QC                                                   # noqa: E402
from cenografia.nucleo.compositor import Placa                               # noqa: E402

M = json.loads((P / "montagem.json").read_text())
FPS = M["fps"]; OW, OH = M["resolucao"]; ALT = 0.05
ROBOTO = skia.Typeface.MakeFromFile(str(RAIZ / "assets" / "fontes" / "RobotoCondensed-ExtraBold.ttf"))
NUNITO = skia.Typeface.MakeFromFile(str(RAIZ / "assets" / "fontes" / "Nunito-ExtraBold.ttf"))
SPECS = PE.specs()
AMARELO = 0xFFFFC21F

POSES = {"base": {}, "susto": {"braco_d": 38, "braco_e": -38, "antebraco_d": 18, "antebraco_e": -18, "cabeca": 0},
         "recuo": {"tronco": -6, "braco_d": 28, "braco_e": -28, "antebraco_d": 30, "antebraco_e": -30, "cabeca": -4},
         "maos_alto": {"braco_d": 160, "braco_e": -160}, "equilibrio": {"tronco": 9, "cabeca": 6, "braco_d": 80, "braco_e": -70, "antebraco_d": 10, "antebraco_e": -14}}


def ease(x, tipo="saida"):
    return GS.curva(x, {"saida": "saida", "suave": "suave", "entrada": "entrada", "linear": "linear"}.get(tipo, "saida"))


def lerp(a, b, k):
    return a + (b - a) * k


def plano_em(t):
    for i, pl in enumerate(M["planos"]):
        if pl["ini"] <= t < pl["fim"]:
            return i, pl
    return len(M["planos"]) - 1, M["planos"][-1]


_PLACAS = {}


def placa(nome):
    if nome not in _PLACAS:
        if len(_PLACAS) >= 3:                                                 # libera memória (cada placa tem várias camadas EXR)
            _PLACAS.pop(next(iter(_PLACAS)))
        _PLACAS[nome] = Placa(PE.pasta(nome, SPECS))
    return _PLACAS[nome]


def _skimg(a):
    a = np.ascontiguousarray(a)
    if a.shape[2] == 3:
        a = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    return skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType)


def _snap(s):
    return np.asarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType))[..., :3]


# ---------------------------------------------------------------- Heitor
def rosto_em(h, tl):
    rs = h.get("rostos") or [[0, "neutro"]]
    atual = rs[0][1]; ant = None; t0 = 0.0
    for tr, nome in rs:
        if tl >= tr:
            ant, atual, t0 = atual, nome, tr
    if ant is not None and ant != atual and tl - t0 < 0.18:
        return GS.mistura_expr(GS.expr(ant), GS.expr(atual), (tl - t0) / 0.18)
    return AN.rosto_com_piscada(atual, tl + 0.37 * len(atual))


def pose_em(h, tl):
    vista = h.get("vista", "frente")
    if h.get("andar"):
        pose, _ = AN.pose_locomocao(tl, vista=vista, tipo=h["andar"]["tipo"]); return pose
    p = HV.pose_base(vista); p.update(POSES.get(h.get("pose", "base"), {}))
    p["respira"] = math.sin(2 * math.pi * tl / 3.1)
    p["cabeca"] = p.get("cabeca", 0.0) + 1.6 * math.sin(2 * math.pi * tl / 4.3)
    if h.get("vento"):
        p["tronco"] = p.get("tronco", 0) + 3 * math.sin(2 * math.pi * tl * 1.7)
        p["raiz"] = [0.04 * math.sin(2 * math.pi * tl * 1.3), 0.0]
    return p


def heitor_mundo(pl, tl, dur):
    sp = SPECS[pl["placa"]]; h = pl.get("heitor") or {}
    base = list(h.get("pos") or sp.get("heitor") or SPECS["A_despertar"]["heitor"])
    if base[2] is None:
        base[2] = SPECS["A_despertar"]["heitor"][2]
    if h.get("andar"):
        k = min(1.0, tl / dur); para = h["andar"]["para"]
        return [lerp(base[i], para[i], k) for i in range(3)], para
    return base, None


# ---------------------------------------------------------------- desenhos 2D extras
def migalha(cv, x, y, tam):
    rng = np.random.default_rng(5); pts = []
    for i in range(14):
        a = 2 * math.pi * i / 14; r = tam * (0.5 + 0.12 * rng.standard_normal())
        pts.append((x + r * 1.25 * math.cos(a), y + r * 0.8 * math.sin(a)))
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    cv.drawPath(p, skia.Paint(AntiAlias=True, Color=0xFFD9A861)); cv.drawPath(p, skia.Paint(AntiAlias=True, Color=0xFF3A2A18, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.5, tam * 0.05)))
    for i in range(10):
        cv.drawCircle(x + rng.uniform(-0.8, 0.8) * tam, y + rng.uniform(-0.45, 0.45) * tam, tam * rng.uniform(0.04, 0.09), skia.Paint(AntiAlias=True, Color=0xFFB98446))


def desenhista(pl, tl, dur, P, cam):
    h = pl.get("heitor")
    mundo, para = heitor_mundo(pl, tl, dur)
    pe = ET.projetar(P, mundo); topo = ET.projetar(P, (mundo[0], mundo[1], mundo[2] + ALT))
    vista = (h or {}).get("vista", "frente"); direcao = (h or {}).get("direcao", 1)
    if vista == "perfil" and para is not None:
        direcao = 1 if ET.projetar(P, para)[0] >= pe[0] else -1
    extras = []
    for ex in pl.get("extras", []):
        if ex["tipo"] in ("gato", "aranha"):
            q = tuple(ex["pos"]); alt = ex.get("altura_m", ex.get("largura_m"))
            extras.append(dict(ex, pe=ET.projetar(P, q), topo=ET.projetar(P, (q[0], q[1], q[2] + alt))))
    k = tl / dur

    def desenhar(cv, proj):
        for ex in extras:
            x, y, _ = proj(*ex["pe"]); _, yt, _ = proj(*ex["topo"]); tam = y - yt
            sombra = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(110, 30, 22, 20), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.02 * tam))
            if ex["tipo"] == "gato":
                cv.drawOval(skia.Rect.MakeXYWH(x - 0.5 * tam, y - 0.03 * tam, tam, 0.06 * tam), sombra)
                pup = lerp(*ex.get("pupila", [0.25, 0.25]), ease(k, "suave"))
                pisca = 0.0
                if ex.get("piscar") and ex["piscar"][0] <= k <= ex["piscar"][1]:
                    pisca = math.sin(math.pi * (k - ex["piscar"][0]) / (ex["piscar"][1] - ex["piscar"][0]))
                GATO.desenhar(cv, x, y, tam, pose=ex.get("pose", "sentado"), direcao=ex.get("direcao", 1), pupila=pup, piscar=pisca)
            else:
                cv.drawOval(skia.Rect.MakeXYWH(x - 0.4 * tam, y - 0.06 * tam, 0.8 * tam, 0.12 * tam), sombra)
                ARANHA.desenhar(cv, x, y, tam, fase=lerp(*ex.get("fase", [0, 0]), k), levantar_frente=lerp(*ex.get("levantar", [0, 0]), ease(k)))
        if h is None:
            return
        x, y, _ = proj(*pe); _, yt, _ = proj(*topo); alt = y - yt
        cv.drawOval(skia.Rect.MakeXYWH(x - 0.2 * alt, y - 0.02 * alt, 0.4 * alt, 0.04 * alt),
                    skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(120, 30, 22, 20), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.015 * alt)))
        rosto = rosto_em(h, tl) if vista != "costas" else None
        HV.desenhar(cv, x, y, alt, vista=vista, direcao=direcao, pose=pose_em(h, tl), rosto=rosto)
        if any(e["tipo"] == "migalha" for e in pl.get("extras", [])):
            migalha(cv, x, y - alt * 1.08, alt * 0.55)
    return desenhar, mundo, pe, topo


# ---------------------------------------------------------------- sobreposições (coordenadas da tela 1080×1920)
def tela_de_placa(P, cam, p):
    """Ponto da placa (px, z) → tela final (o recorte central depois do movimento de câmera)."""
    x, y, _ = P.projetar_ponto(*p, **cam); return x - (P.W - OW) / 2, y - (P.H - OH) / 2


def rotulo(cv, txt, sub, ax, ay, lado):
    f = skia.Font(NUNITO, 92); w = f.measureText(txt); w2 = skia.Font(NUNITO, 40).measureText(sub or "")
    larg = max(w, w2) + 60
    if lado > 0 and ax + 170 + larg > OW - 30:                         # o rótulo nunca sai da tela: troca de lado se precisar
        lado = -1
    if lado < 0 and ax - 170 - larg < 30:
        lado = 1
    bx = ax + lado * 170; by = max(200, ay - 150)
    lp = skia.Paint(AntiAlias=True, Color=0xFFFFFFFF, StrokeWidth=5, Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap)
    sh = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(150, 0, 0, 0), StrokeWidth=9, Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap)
    pth = skia.Path(); pth.moveTo(ax, ay); pth.lineTo(bx, by); pth.lineTo(bx + lado * 40, by)
    cv.drawPath(pth, sh); cv.drawPath(pth, lp); cv.drawCircle(ax, ay, 9, skia.Paint(AntiAlias=True, Color=0xFFFFFFFF))
    x0 = bx + lado * 52 if lado > 0 else bx - 52 - w
    x0 = min(max(30, x0), OW - 30 - w)
    for st, cor in ((skia.Paint(AntiAlias=True, Color=0xFF1A110C, Style=skia.Paint.kStroke_Style, StrokeWidth=14, StrokeJoin=skia.Paint.kRound_Join), None),
                    (skia.Paint(AntiAlias=True, Color=AMARELO), None)):
        cv.drawString(txt, x0, by + 32, f, st)
    if sub:
        f2 = skia.Font(NUNITO, 40); w2 = f2.measureText(sub); x2 = x0 if lado > 0 else x0 + w - w2
        x2 = min(max(30, x2), OW - 30 - w2)
        cv.drawString(sub, x2, by + 80, f2, skia.Paint(AntiAlias=True, Color=0xFF1A110C, Style=skia.Paint.kStroke_Style, StrokeWidth=8, StrokeJoin=skia.Paint.kRound_Join))
        cv.drawString(sub, x2, by + 80, f2, skia.Paint(AntiAlias=True, Color=0xFFFFFFFF))


def regua(cv, x, y_pe, y_topo):
    p = skia.Paint(AntiAlias=True, Color=0xFFFFFFFF, StrokeWidth=4); xr = x + 46
    cv.drawLine(xr, y_pe, xr, y_topo, p)
    for k in range(6):
        yy = lerp(y_pe, y_topo, k / 5); cv.drawLine(xr - (14 if k % 5 == 0 else 8), yy, xr, yy, p)


def sombra_gato(img, ex, k):
    s = skia.Surface(OW, OH); cv = s.getCanvas(); cv.clear(0)
    x = OW * lerp(*ex["x"], ease(k, "suave")); y = OH * ex["y"]; alt = OH * lerp(*ex["alt"], ease(k, "suave"))
    cv.saveLayer(skia.Rect.MakeWH(OW, OH), skia.Paint(ColorFilter=skia.ColorFilters.Blend(skia.ColorSetARGB(255, 20, 14, 24), skia.BlendMode.kSrcIn),
                                                       ImageFilter=skia.ImageFilters.Blur(10, 10)))
    GATO.desenhar(cv, x, y + alt * 0.5, alt, pose="sentado", direcao=-1)
    cv.restore()
    a = np.asarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).astype(np.float32) / 255
    al = a[..., 3:4] * 0.55
    return (img.astype(np.float32) * (1 - al) + a[..., :3] * 255 * al).astype(np.uint8)


def vento(cv, tl):
    rng = np.random.default_rng(int(tl * 30) // 2)
    for i in range(26):
        y = rng.uniform(0.25, 0.9) * OH; L = rng.uniform(120, 420); x = (rng.uniform(0, 1.4) * OW + tl * 2600) % (OW + 600) - 300
        cv.drawLine(x, y, x + L, y + rng.uniform(-10, 10), skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(rng.uniform(40, 110)), 255, 255, 255),
                                                                     StrokeWidth=rng.uniform(2, 5), StrokeCap=skia.Paint.kRound_Cap))
    for i in range(40):
        x = (rng.uniform(0, 1) * OW + tl * 1900 * rng.uniform(0.6, 1.2)) % OW; y = rng.uniform(0.3, 0.95) * OH
        cv.drawCircle(x, y, rng.uniform(2, 5), skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(150, 230, 220, 200)))


# ---------------------------------------------------------------- inserts 2D
def insert_olho(pl, k):
    s = skia.Surface(OW, OH); cv = s.getCanvas(); cv.clear(0xFF8E9AA8)
    z = lerp(*pl.get("zoom", [1, 1]), ease(k)); L = 620 * z
    GATO.olho(cv, OW / 2, OH * 0.48, L, pupila=lerp(*pl["pupila"], ease(min(1, k * 1.6), "saida")), olhar=0.0)
    return _snap(s)


def _marca(cv, cx, base, tam):
    f = skia.Font(ROBOTO, tam); w1, w2, esp = f.measureText("MODO"), f.measureText("CURIOSO"), f.measureText(" ")
    x = cx - (w1 + esp + w2) / 2
    st = skia.Paint(AntiAlias=True, Color=0xFF1A110C, Style=skia.Paint.kStroke_Style, StrokeWidth=tam * 0.1, StrokeJoin=skia.Paint.kRound_Join)
    cv.drawString("MODO", x, base, f, st); cv.drawString("CURIOSO", x + w1 + esp, base, f, st)
    cv.drawString("MODO", x, base, f, skia.Paint(AntiAlias=True, Color=0xFFFFFFFF)); cv.drawString("CURIOSO", x + w1 + esp, base, f, skia.Paint(AntiAlias=True, Color=AMARELO))


def insert_card(pl, k, tl):
    s = skia.Surface(OW, OH); cv = s.getCanvas()
    QC._fundo(cv, tl * 0.2)                                                       # mesmo fundo dos inserts (azul-marinho, bokeh)
    if pl["insert"] == "card_logo":
        esc = 0.92 + 0.08 * ease(min(1, k * 3), "saida")
        _marca(cv, OW / 2, OH * 0.47, 150 * esc)
        HV.desenhar(cv, OW / 2, OH * 0.66, 260, vista="frente", direcao=1, pose=HV.pose_base("frente") | POSES["maos_alto"], rosto="alegria")
    else:
        linhas = ["COMENTA AÍ:", "QUAL LUGAR", "DA SUA CASA", "VOCÊ TENTARIA", "ALCANÇAR?"]
        f = skia.Font(ROBOTO, 120)
        for i, ln in enumerate(linhas):
            w = f.measureText(ln); y = OH * 0.3 + i * 150; cor = AMARELO if i == 0 else 0xFFFFFFFF
            cv.drawString(ln, OW / 2 - w / 2, y, f, skia.Paint(AntiAlias=True, Color=0xFF1A110C, Style=skia.Paint.kStroke_Style, StrokeWidth=16, StrokeJoin=skia.Paint.kRound_Join))
            cv.drawString(ln, OW / 2 - w / 2, y, f, skia.Paint(AntiAlias=True, Color=cor))
        f2 = skia.Font(ROBOTO, 96); txt = "SEGUE AÍ!"; w = f2.measureText(txt)
        cv.drawString(txt, OW / 2 - w / 2, OH * 0.82, f2, skia.Paint(AntiAlias=True, Color=0xFF1A110C, Style=skia.Paint.kStroke_Style, StrokeWidth=14, StrokeJoin=skia.Paint.kRound_Join))
        cv.drawString(txt, OW / 2 - w / 2, OH * 0.82, f2, skia.Paint(AntiAlias=True, Color=0xFFFFFFFF))
    return _snap(s)


def zoom_centro(img, z):
    if abs(z - 1) < 1e-3:
        return img
    h, w = img.shape[:2]; cw, ch = int(w / z), int(h / z); x0, y0 = (w - cw) // 2, (h - ch) // 2
    return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_CUBIC)


# ---------------------------------------------------------------- legendas e marca
_POS_LEG = {}


def legenda(cv, t, rosto_y, fixo=None):
    for i, lg in enumerate(M["legendas"]):
        if lg["ini"] <= t < lg["fim"]:
            if i not in _POS_LEG:
                _POS_LEG[i] = "topo" if (rosto_y is not None and 0.58 * OH < rosto_y < 0.86 * OH) else "baixo"
            tl = t - lg["ini"]; esc = 0.97 + 0.03 * min(1, tl / (2 / FPS))
            tam = 96 * esc; f = skia.Font(ROBOTO, tam); palavras = lg["txt"].split(); dest = set(lg["dest"])
            esp = f.measureText(" "); larg = sum(f.measureText(w) for w in palavras) + esp * (len(palavras) - 1)
            if larg > OW * 0.84:
                tam *= OW * 0.84 / larg; f = skia.Font(ROBOTO, tam); esp = f.measureText(" ")
                larg = sum(f.measureText(w) for w in palavras) + esp * (len(palavras) - 1)
            cy = OH * (fixo if fixo else (0.215 if _POS_LEG[i] == "topo" else 0.74)); base = cy + tam * 0.711 / 2; x = OW / 2 - larg / 2
            for w in palavras:
                cor = AMARELO if w.strip("?!.,") in dest else 0xFFFFFFFF
                cv.drawString(w, x + 3, base + 6, f, skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(140, 0, 0, 0), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
                cv.drawString(w, x, base, f, skia.Paint(AntiAlias=True, Color=0xFF1A110C, Style=skia.Paint.kStroke_Style, StrokeWidth=tam * 0.711 * 0.24, StrokeJoin=skia.Paint.kRound_Join))
                cv.drawString(w, x, base, f, skia.Paint(AntiAlias=True, Color=cor))
                x += f.measureText(w) + esp


def marca_dagua(cv):
    md = M["marca_dagua"]; tam = md["altura_px"] / 0.711; f = skia.Font(ROBOTO, tam)
    w1, w2, esp = f.measureText("MODO"), f.measureText("CURIOSO"), f.measureText(" ")
    x = OW - md["margem_dir"] - (w1 + esp + w2); base = md["margem_topo"] + md["altura_px"]
    cv.drawString("MODO", x, base, f, skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(153, 255, 255, 255)))
    cv.drawString("CURIOSO", x + w1 + esp, base, f, skia.Paint(AntiAlias=True, Color=AMARELO))


# ---------------------------------------------------------------- quadro
def quadro(n):
    t = n / FPS; i, pl = plano_em(t); dur = pl["fim"] - pl["ini"]; tl = t - pl["ini"]; k = tl / dur
    rosto_y = None
    if "insert" in pl:
        if pl["insert"] == "quadrado_cubo":
            img = zoom_centro(QC.quadro(lerp(*pl["t"], k)), lerp(*pl.get("zoom", [1, 1]), ease(k)))
        elif pl["insert"] == "olho_gato":
            img = insert_olho(pl, k)
        else:
            img = insert_card(pl, k, tl)
    else:
        P = placa(pl["placa"]); e = ease(k, pl.get("ease", "saida"))
        cam = {kk: lerp(*v, e) for kk, v in pl.get("cam", {}).items()}
        h = pl.get("heitor")
        kw = dict(grade=ET.GRADE, pesos=ET.PESOS, semente_grao=n)
        if h is not None or pl.get("extras"):
            des, mundo, pe, topo = desenhista(pl, tl, dur, P, cam)
            kw.update(personagem=des, profundidade_personagem=pe[2])
            if h is not None:
                kw["tom_personagem"] = X1.fazer_tom({"pe_mundo": mundo, "altura_m": ALT})
                xt, yt = tela_de_placa(P, cam, topo); xp, yp = tela_de_placa(P, cam, pe); rosto_y = yt + (yp - yt) * 0.15
        img = np.ascontiguousarray(P.compor(**kw))
        for ex in pl.get("extras", []):
            if ex["tipo"] == "sombra_gato":
                img = sombra_gato(img, ex, k)
        s = skia.Surface(OW, OH); cv = s.getCanvas(); cv.drawImage(_skimg(img), 0, 0)
        if pl.get("efeitos", {}).get("vento"):
            vento(cv, tl)
        for ex in pl.get("extras", []):
            if ex["tipo"] == "pata":
                kk = ease(min(1, k * 1.5), "saida")
                GATO.pata(cv, OW * ex["x"], OH * lerp(*ex["y"], kk), OH * ex["tam"], garras=lerp(*ex["garras"], kk))
        if h is not None:
            xt, yt = tela_de_placa(P, cam, topo); xp, yp = tela_de_placa(P, cam, pe)
            if pl.get("efeitos", {}).get("circulo"):
                r = max(40, (yp - yt) * 1.6)
                cv.drawCircle(xp, (yp + yt) / 2, r, skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(220 * min(1, k * 4)), 255, 194, 31), Style=skia.Paint.kStroke_Style, StrokeWidth=7))
            for rt in pl.get("rotulos", []):
                a_in = min(1.0, max(0.0, (tl - 0.25) / 0.2))
                if a_in <= 0:
                    continue
                if rt["ancora"] == "heitor_topo":
                    ax, ay = xt, yt
                else:
                    ax, ay = tela_de_placa(P, cam, ET.projetar(P, rt["ancora"]))
                if rt.get("regua"):
                    regua(cv, xp, yp, yt)
                cv.saveLayer(skia.Rect.MakeWH(OW, OH), skia.Paint(Alphaf=a_in)); rotulo(cv, rt["txt"], rt.get("sub"), ax, ay, rt.get("lado", 1)); cv.restore()
        else:
            for rt in pl.get("rotulos", []):
                ax, ay = tela_de_placa(P, cam, ET.projetar(P, rt["ancora"])); rotulo(cv, rt["txt"], rt.get("sub"), ax, ay, rt.get("lado", 1))
        img = _snap(s)
    # entrada
    ent = pl.get("entrada")
    if ent == "chicote" and tl < 0.13:
        kx = int(140 * (1 - tl / 0.13)) * 2 + 1; img = cv2.blur(img, (max(3, kx), 1))
    elif ent == "flash" and tl < 0.12:
        a = 0.85 * (1 - tl / 0.12); img = (img * (1 - a) + 255 * a).astype(np.uint8)
    # tremida
    tr = pl.get("efeitos", {}).get("tremida")
    if tr and tr[0] <= tl <= tr[1]:
        rng = np.random.default_rng(n); amp = 0.014 * OW * (1 - (tl - tr[0]) / max(1e-3, tr[1] - tr[0]))
        Mt = np.float32([[1.03, 0, rng.uniform(-amp, amp) - 0.015 * OW], [0, 1.03, rng.uniform(-amp, amp) - 0.015 * OH]])
        img = cv2.warpAffine(img, Mt, (OW, OH), borderMode=cv2.BORDER_REFLECT)
    s = skia.Surface(OW, OH); cv = s.getCanvas(); cv.drawImage(_skimg(img), 0, 0)
    if pl.get("insert") not in ("card_logo", "card_cta"):
        legenda(cv, t, rosto_y, pl.get("legenda_y"))
    marca_dagua(cv)
    return _snap(s)


def segmento(n0, n1, saida):
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "pipe:0",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", str(saida)], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        ff.stdin.write(np.ascontiguousarray(quadro(n)).tobytes())
        if (n - n0) % 60 == 0:
            print(f"{saida.name}: {n - n0}/{n1 - n0}", flush=True)
    ff.stdin.close(); ff.wait()


def main():
    a = sys.argv
    N = int(round(M["duracao"] * FPS))
    if "--png" in a:
        pasta = Path(a[a.index("--png") + 1]); pasta.mkdir(parents=True, exist_ok=True)
        for n in [int(x) for x in a[a.index("--quadros") + 1].split(",")]:
            cv2.imwrite(str(pasta / f"q{n:05d}.png"), cv2.cvtColor(quadro(n), cv2.COLOR_RGB2BGR))
        return
    if "--seg" in a:
        segmento(int(a[a.index("--de") + 1]), int(a[a.index("--ate") + 1]), Path(a[a.index("--seg") + 1])); return
    # paralelo: um processo por faixa contígua de quadros (cada um carrega só as placas das suas cenas)
    trab = int(os.environ.get("TRABALHADORES", "4")); tmp = P / "_cache" / "segmentos"; tmp.mkdir(parents=True, exist_ok=True)
    cortes = [round(N * i / trab) for i in range(trab + 1)]
    procs = [subprocess.Popen([sys.executable, __file__, "--seg", str(tmp / f"seg_{i}.mp4"), "--de", str(cortes[i]), "--ate", str(cortes[i + 1])],
                              env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")) for i in range(trab)]
    for p in procs:
        p.wait()
    (tmp / "lista.txt").write_text("".join(f"file '{tmp / f'seg_{i}.mp4'}'\n" for i in range(trab)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"), "-c", "copy", str(P / "_cache" / "video_sem_audio.mp4")], check=True)
    print("ok:", P / "_cache" / "video_sem_audio.mp4")


if __name__ == "__main__":
    main()
