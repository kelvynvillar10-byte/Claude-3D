#!/usr/bin/env python3
"""Piloto 01 — compositor (skia + NumPy) → FFmpeg (H.264 1080×1920, 30 qps).

Lê montagem.json. Para cada quadro: fundo do Blender (com névoa pelo mapa de profundidade)
sob a câmera virtual (zoom/pan/giro, punch, tremida), personagem 2D do rig na posição das
âncoras 3D com a tinta de luz do plano, primeiro plano, efeitos; depois acabamento comum
(gradação: sombra azul-arroxeada / alta luz quente, bloom, vinheta, grão) e, por cima,
legendas e marca d'água "MODO CURIOSO" (fora da gradação).

Uso: .venv/bin/python codigo/compor.py [--audio saida/mix.wav] [--saida saida/x.mp4] [--quadros 0:300] [--png pasta]
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np, cv2, skia

P = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(P / "codigo"))
import heitor_rig as rig   # noqa: E402

M = json.loads((P / "montagem.json").read_text())
R = P / "_cache" / "render"
ANC = json.loads((R / "ancoras.json").read_text())
FON = P.parents[1] / "assets" / "fontes"
ROBOTO = skia.Typeface.MakeFromFile(str(FON / "RobotoCondensed-ExtraBold.ttf"))
FPS, DUR = M["fps"], M["duracao"]; OW, OH = M["resolucao"]
BW, BH = ANC["_resolucao"]
args = sys.argv
AUDIO = args[args.index("--audio") + 1] if "--audio" in args else None
SAIDA = args[args.index("--saida") + 1] if "--saida" in args else str(P / "saida" / "sem_audio.mp4")
QA, QB = (map(int, args[args.index("--quadros") + 1].split(":"))) if "--quadros" in args else (0, int(round(DUR * FPS)))
PNG = Path(args[args.index("--png") + 1]) if "--png" in args else None
AMOSTRA = skia.SamplingOptions(skia.CubicResampler.Mitchell())


def ease(x, tipo):
    x = min(1.0, max(0.0, x))
    if tipo == "ease_out":
        return 1 - (1 - x) ** 3
    if tipo == "ease_in_out":
        return 3 * x * x - 2 * x ** 3
    return x


def img_np(path):
    if not Path(path).exists():
        return None
    a = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if a is None:
        return None
    if a.shape[2] == 3:
        a = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    return cv2.cvtColor(a, cv2.COLOR_BGRA2RGBA)


def np_skia(a):
    return skia.Image.fromarray(np.ascontiguousarray(a), colorType=skia.ColorType.kRGBA_8888_ColorType)


# ---------- pré-processamento dos fundos (névoa atmosférica pelo mapa de profundidade)
NEVOA_COR = np.array([236, 205, 172], np.float32)
FUNDOS = {}
for pl in M["planos"]:
    for suf in ("_fundo", "_fundo_acesa", "_frente"):
        a = img_np(R / f"{pl['fundo']}{suf}.png")
        if a is None:
            continue
        if suf != "_frente" and pl.get("exposicao", {}).get(suf.strip("_")):
            g = pl["exposicao"][suf.strip("_")]
            a = a.copy(); a[..., :3] = np.clip(a[..., :3].astype(np.float32) * g, 0, 255).astype(np.uint8)
        if suf != "_frente":
            nev = img_np(R / f"{pl['fundo']}_nevoa.png")
            k = 0.62 if "nevoa_forte" in pl.get("efeitos", []) else (0.42 if "nevoa" in pl.get("efeitos", []) else 0.12)
            if nev is not None and k > 0:
                m = (nev[..., 0].astype(np.float32) / 255.0) ** 1.3 * k
                rgb = a[..., :3].astype(np.float32)
                a = a.copy(); a[..., :3] = np.clip(rgb * (1 - m[..., None]) + NEVOA_COR * m[..., None], 0, 255).astype(np.uint8)
        FUNDOS[pl["fundo"] + suf] = np_skia(a)

# direção do corpo deitado: do centro da cabeça para o centro do cobertor (máscara do primeiro plano)
CORPO = {}
for pl in M["planos"]:
    fr = img_np(R / f"{pl['fundo']}_frente.png")
    if fr is not None:
        ys, xs = np.nonzero(fr[..., 3] > 128); CORPO[pl["fundo"]] = (float(xs.mean()), float(ys.mean()))

# ---------- inserto do planeta: fundo azul-marinho com bokeh + pontos de luz das pessoas
rng = np.random.default_rng(5)
BOKEH = [(rng.uniform(0, BW), rng.uniform(0, BH), rng.uniform(10, 60), rng.uniform(0.04, 0.16)) for _ in range(40)]
ESTRELAS = [(rng.uniform(0, BW), rng.uniform(0, BH), rng.uniform(0.6, 1.8), rng.uniform(0.3, 0.9)) for _ in range(160)]
_PONTOS = []
while len(_PONTOS) < 320:
    x, y = rng.uniform(-1, 1, 2)
    if x * x + y * y < 0.82:
        _PONTOS.append((x, y, rng.uniform(0, 1)))


def poeira(seed, n=70):
    r = np.random.default_rng(seed)
    return [(r.uniform(0, BW), r.uniform(0, BH), r.uniform(0.8, 2.6), r.uniform(-6, 6), r.uniform(-14, -4), r.uniform(0.25, 0.7))
            for _ in range(n)]


POEIRA = {pl["id"]: poeira(hash(pl["id"]) % 1000) for pl in M["planos"]}


def plano_em(t):
    for i, pl in enumerate(M["planos"]):
        if pl["ini"] <= t < pl["fim"]:
            return i, pl
    return len(M["planos"]) - 1, M["planos"][-1]


def ancora(pl, k):
    return ANC.get(pl["fundo"], {}).get(k)


def camera(pl, t):
    cam = pl["camera"]; tl = t - pl["ini"]; d = cam.get("dur_mov", pl["fim"] - pl["ini"])
    e = ease(tl / d, cam.get("curva", "linear"))
    z = cam["z"][0] + (cam["z"][1] - cam["z"][0]) * e
    for pu in cam.get("punch", []):
        dt = t - pu["t"]
        if 0 <= dt < 0.35:
            z *= 1 + pu["amp"] * (min(1, dt / 0.06) * math.exp(-max(0, dt - 0.06) / 0.12))
    if "alvo" in cam and ancora(pl, cam["alvo"]):
        ax, ay, _ = ancora(pl, cam["alvo"])
        cx, cy = BW / 2 + (ax - BW / 2) * 0.55, BH / 2 + (ay - BH / 2) * 0.55
    else:
        rx, ry = cam.get("centro_rel", [0.5, 0.5]); cx, cy = BW * rx, BH * ry
    if "pan" in cam:
        cx += cam["pan"][0] + (cam["pan"][1] - cam["pan"][0]) * e
    hw, hh = OW / 2 / z, OH / 2 / z
    cx = min(max(cx, hw), BW - hw); cy = min(max(cy, hh), BH - hh)
    ox = oy = rot = 0.0
    if "tremida" in cam:
        tr = cam["tremida"]; dt = tl
        if dt < tr["dur"]:
            a = tr["amp"] * OH * math.exp(-dt / (tr["dur"] / 3))
            ox = a * math.sin(dt * 2 * math.pi * 21); oy = a * math.cos(dt * 2 * math.pi * 17 + 1.3); rot = 0.6 * math.sin(dt * 40)
    if "vibra" in cam:
        vb = cam["vibra"]; dt = t - vb["t"]
        for k in range(vb["pulsos"]):
            if 0 <= dt - k * 0.38 < 0.24:
                a = vb["amp"] * OH; ox += a * math.sin(dt * 2 * math.pi * 31); oy += a * math.cos(dt * 2 * math.pi * 27)
    return z, cx, cy, ox, oy, rot


def aplica_camera(c, z, cx, cy, ox, oy, rot):
    c.translate(OW / 2 + ox, OH / 2 + oy); c.rotate(rot); c.scale(z, z); c.translate(-cx, -cy)


def expr_em(pers, t):
    e = pers["expr"][0][1]
    for t0, ex in pers["expr"]:
        if t >= t0:
            e = ex
    return e


def olhar_em(pers, t):
    v = 0.0
    for t0, val in pers.get("olhar", []):
        if t >= t0:
            v = val
    return v


def desenha_personagem(c, pl, t):
    pers = pl.get("personagem")
    if not pers:
        return
    ex = expr_em(pers, t); ol = olhar_em(pers, t)
    if pl["id"] == "P4" and 4.62 <= t < 4.72:   # piscada (personagem sempre vivo)
        ex = "dormindo"
    resp = math.sin(2 * math.pi * t / 3.0)
    tr, tg, tb = [v / 255 for v in pers.get("tinta", [255, 255, 255])]
    tinta_f = skia.ColorFilters.Matrix([tr, 0, 0, 0, 0, 0, tg, 0, 0, 0, 0, 0, tb, 0, 0, 0, 0, 0, 1, 0])  # multiplica RGB, preserva alfa
    if pers["pose"] == "deitado":
        hx, hy, _ = ancora(pl, "cabeca"); tx, ty, _ = ancora(pl, "cabeca_topo"); px, py = CORPO[pl["fundo"]]
        u = 2 * math.hypot(hx - tx, hy - ty)
        vx, vy = px - hx, py - hy; n = math.hypot(vx, vy); vx, vy = vx / n, vy / n
        th = math.degrees(math.atan2(-vx, vy))
        fx, fy = hx + vx * 3.48 * u, hy + vy * 3.48 * u
        args_ = dict(vista=pers["vista"], expr=ex, x_pe=fx, y_pe=fy, altura_px=4 * u, luz=pers["luz"], rot=th, olhar=ol, respira=resp)
    else:
        px, py, _ = ancora(pl, "pe"); hx, hy, _ = ancora(pl, "cabeca")
        alt = py - hy
        args_ = dict(vista=pers["vista"], expr=ex, x_pe=px, y_pe=py, altura_px=alt, luz=pers["luz"], olhar=ol, respira=resp)
        if pers.get("sombra_chao"):
            sp = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(120, 20, 18, 30), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, alt * 0.02))
            c.drawOval(skia.Rect.MakeXYWH(px - alt * 0.16, py - alt * 0.02, alt * 0.32, alt * 0.05), sp)
    if pers.get("contraluz"):   # halo quente de contraluz (janela atrás)
        halo = skia.Paint(ColorFilter=skia.ColorFilters.Blend(skia.ColorSetARGB(200, 255, 214, 160), skia.BlendMode.kSrcIn),
                          ImageFilter=skia.ImageFilters.Blur(args_["altura_px"] * 0.012, args_["altura_px"] * 0.012))
        c.saveLayer(paint=halo); rig.desenhar(c, **args_); c.restore()
    lay = skia.Paint(ColorFilter=tinta_f)
    c.saveLayer(paint=lay); rig.desenhar(c, **args_); c.restore()


def desenha_poeira(c, pl, t):
    for (x, y, r, vx, vy, a) in POEIRA[pl["id"]]:
        tt = t - pl["ini"]
        xx, yy = x + vx * tt * 3, y + vy * tt * 3
        p = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(255 * a * (0.6 + 0.4 * math.sin(t * 3 + x))), 255, 228, 180),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.8))
        c.drawCircle(xx, yy, r * 1.6, p)


def numero_br(v):
    return f"{int(round(v)):,}".replace(",", ".")


def desenha_terra(c, pl, t):
    grad = skia.GradientShader.MakeRadial(skia.Point(BW / 2, BH * 0.45), BH * 0.75, [0xFF1B2A4E, 0xFF0B1226])
    c.drawPaint(skia.Paint(Shader=grad))
    for x, y, r, a in ESTRELAS:
        c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(a * 200), 220, 230, 255)))
    for x, y, r, a in BOKEH:
        c.drawCircle(x, y + (t - pl["ini"]) * 12, r, skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(a * 255), 120, 160, 255),
                                                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.45)))
    terra = FUNDOS[pl["fundo"] + "_fundo"]
    tl = t - pl["ini"]
    c.save(); c.translate(BW / 2, BH * 0.47); c.rotate(-6 * tl); c.translate(-BW / 2, -BH / 2)
    c.drawImage(terra, 0, 0, AMOSTRA)
    c.restore()
    # luzes das pessoas: apagam uma a uma entre t0 e t1
    ct = pl["contador"]; p = min(1, max(0, (t - ct["t0"]) / (ct["t1"] - ct["t0"])))
    raio = BW * 0.205
    for (x, y, lim) in _PONTOS:
        if p > lim * 0.98 and not (x == _PONTOS[0][0]):
            continue
        a = 1.0 if p <= lim * 0.98 else 1.0
        c.drawCircle(BW / 2 + x * raio, BH * 0.47 + y * raio, 3.2,
                     skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(230 * a), 255, 210, 120),
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2.2)))
    return p


def desenha_contador_rotulo(c, pl, t, p, z_tela):
    """Rótulo com número grande e linha-guia (em coordenadas de tela, fora da câmera)."""
    ct = pl["contador"]
    v = ct["de"] if p <= 0 else max(ct["ate"], ct["de"] ** (1 - p))
    if p >= 0.999:
        v = ct["ate"]
    tl = t - pl["ini"]; pop = min(1.0, 0.94 + tl / 0.1 * 0.06)
    num = numero_br(v)
    f = skia.Font(ROBOTO, 110 * pop); f2 = skia.Font(ROBOTO, 40)
    w = f.measureText(num); x0 = OW / 2 - w / 2; y0 = 380
    sombra = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(150, 0, 0, 0), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
    c.drawString(num, x0 + 4, y0 + 6, f, sombra)
    c.drawString(num, x0, y0, f, skia.Paint(AntiAlias=True, Color=0xFFFFC21F))
    sub = pl["rotulo"]["sub"]; ws = f2.measureText(sub)
    c.drawString(sub, OW / 2 - ws / 2, y0 + 62, f2, skia.Paint(AntiAlias=True, Color=0xE6FFFFFF))
    lp = skia.Paint(AntiAlias=True, Color=0xCCFFFFFF, StrokeWidth=3)
    c.drawLine(OW / 2, y0 + 82, OW / 2, y0 + 190, lp); c.drawCircle(OW / 2, y0 + 196, 7, skia.Paint(AntiAlias=True, Color=0xFFFFFFFF))


# ---------- acabamento comum
def gradua(a, t):
    f = a[..., :3].astype(np.float32) / 255.0
    L = (0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2])[..., None]
    ws = (1 - L) ** 1.4; wh = L ** 2.0
    f = f * (1 - 0.18 * ws) + ws * np.array([0.030, -0.006, 0.105], np.float32) + wh * np.array([0.035, 0.012, -0.035], np.float32)  # sombra azul-arroxeada, alta luz quente
    # bloom
    pequeno = cv2.resize(f, (OW // 4, OH // 4), interpolation=cv2.INTER_AREA)
    br = np.clip(pequeno - 0.72, 0, None)
    br = cv2.GaussianBlur(br, (0, 0), 9)
    f = f + cv2.resize(br, (OW, OH), interpolation=cv2.INTER_LINEAR) * 0.55
    f = f * VINHETA[..., None]
    rng_ = np.random.default_rng(int(t * 1000))
    gr = rng_.normal(0, 0.012, (OH // 2, OW // 2)).astype(np.float32)
    f = f + cv2.resize(gr, (OW, OH), interpolation=cv2.INTER_NEAREST)[..., None]
    a = a.copy(); a[..., :3] = np.clip(f * 255, 0, 255).astype(np.uint8)
    return a


yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
_r = np.sqrt(((xx - OW / 2) / (OW / 2)) ** 2 + ((yy - OH / 2) / (OH / 2)) ** 2) / math.sqrt(2)
VINHETA = (1 - 0.55 * np.clip((_r - 0.2) / 0.8, 0, 1) ** 1.4).astype(np.float32)   # vinheta forte (alvo: cantos ~60 % do centro)


def legenda(c, t):
    for lg in M["legendas"]:
        if lg["ini"] <= t < lg["fim"]:
            tl = t - lg["ini"]; esc = 0.97 + 0.03 * min(1, tl / (2 / FPS))
            tam = 81 * esc; f = skia.Font(ROBOTO, tam)
            palavras = lg["txt"].split(); dest = set(lg["dest"].split())
            esp = f.measureText(" "); larg = sum(f.measureText(w) for w in palavras) + esp * (len(palavras) - 1)
            if larg > OW * 0.84:
                tam *= OW * 0.84 / larg; f = skia.Font(ROBOTO, tam); esp = f.measureText(" ")
                larg = sum(f.measureText(w) for w in palavras) + esp * (len(palavras) - 1)
            cy = OH * (0.215 if lg["pos"] == "topo" else 0.72)
            base = cy + tam * 0.711 / 2; x = OW / 2 - larg / 2
            for w in palavras:
                limpo = w.strip("?!.,")
                cor = 0xFFFFC21F if (limpo in dest or w in dest) else 0xFFFFFFFF
                sh = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(140, 0, 0, 0), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3))
                c.drawString(w, x + 3, base + 5, f, sh)
                st = skia.Paint(AntiAlias=True, Color=0xFF1A110C, Style=skia.Paint.kStroke_Style, StrokeWidth=tam * 0.711 * 0.24,
                                StrokeJoin=skia.Paint.kRound_Join)
                c.drawString(w, x, base, f, st)
                c.drawString(w, x, base, f, skia.Paint(AntiAlias=True, Color=cor))
                x += f.measureText(w) + esp


def marca_dagua(c):
    md = M["marca_dagua"]; tam = md["altura_px"] / 0.711; f = skia.Font(ROBOTO, tam)
    w1, w2, esp = f.measureText("MODO"), f.measureText("CURIOSO"), f.measureText(" ")
    x = OW - md["margem_dir"] - (w1 + esp + w2); base = md["margem_topo"] + md["altura_px"]
    c.drawString("MODO", x, base, f, skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(153, 255, 255, 255)))
    c.drawString("CURIOSO", x + w1 + esp, base, f, skia.Paint(AntiAlias=True, Color=0xFFFFC21F))


def quadro(n):
    t = n / FPS
    i, pl = plano_em(t)
    s = skia.Surface(OW, OH); c = s.getCanvas(); c.clear(0xFF000000)
    z, cx, cy, ox, oy, rot = camera(pl, t)
    c.save(); aplica_camera(c, z, cx, cy, ox, oy, rot)
    p_cont = None
    if "insert_terra" in pl.get("efeitos", []):
        p_cont = desenha_terra(c, pl, t)
    else:
        fundo = FUNDOS[pl["fundo"] + "_fundo"]
        c.drawImage(fundo, 0, 0, AMOSTRA)
        if "tela_acende" in pl and t >= pl["tela_acende"]:
            a = min(1.0, (t - pl["tela_acende"]) / (2 / FPS))
            c.drawImage(FUNDOS[pl["fundo"] + "_fundo_acesa"], 0, 0, AMOSTRA, skia.Paint(Alphaf=a))
        desenha_personagem(c, pl, t)
        if pl["fundo"] + "_frente" in FUNDOS:
            c.drawImage(FUNDOS[pl["fundo"] + "_frente"], 0, 0, AMOSTRA)
        if "poeira_luz" in pl.get("efeitos", []):
            desenha_poeira(c, pl, t)
    c.restore()
    if p_cont is not None:
        desenha_contador_rotulo(c, pl, t, p_cont, z)
    a = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
    a = gradua(a, t)
    # transições
    for tr in M["transicoes"]:
        if tr["tipo"] == "chicote" and abs(t - tr["t"]) <= tr["dur"] / 2 + 1e-6:
            k = int(90 * (1 - abs(t - tr["t"]) / (tr["dur"] / 2 + 1e-6))) * 2 + 1
            a[..., :3] = cv2.blur(a[..., :3], (max(3, k), 1))
    ent = pl.get("entrada")
    if ent:
        dt = t - pl["ini"]
        if ent["tipo"] == "flash" and dt < ent["dur"]:
            al = 0.85 * (1 - dt / ent["dur"]); a[..., :3] = (a[..., :3] * (1 - al) + 255 * al).astype(np.uint8)
        if ent["tipo"] == "fusao" and dt < ent["dur"] and i > 0:
            pass  # fusão curta tratada pelo bloom + corte (planos muito curtos)
    s2 = skia.Surface(OW, OH); c2 = s2.getCanvas()
    c2.drawImage(np_skia(a), 0, 0)
    legenda(c2, t); marca_dagua(c2)
    return s2.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3]


def main():
    if PNG:
        PNG.mkdir(parents=True, exist_ok=True)
        for n in range(QA, QB):
            cv2.imwrite(str(PNG / f"q{n:04d}.png"), cv2.cvtColor(quadro(n), cv2.COLOR_RGB2BGR))
        return
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-"]
    if AUDIO:
        cmd += ["-i", AUDIO, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart", SAIDA]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(QA, QB):
        pr.stdin.write(quadro(n).tobytes())
        if n % 30 == 0:
            print(f"quadro {n}/{QB}", flush=True)
    pr.stdin.close(); pr.wait()
    print("ok:", SAIDA)


if __name__ == "__main__":
    main()
