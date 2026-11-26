#!/usr/bin/env python3
"""Testes e demonstração da EXTENSÃO X3 (aranha) — APROVADA pelo diretor em 26/11/2026.

X3_1 apoios plantados: na escalada, mão/pé parado não desliza (px, no desenho), e a IK alcança a pegada (H)
X3_2 contatos no desenho real: o ponto da pegada cai na mão (pele) ou no tênis; no balanço, o fio chega na mão
X3_3 juntas e cotovelos (limites do modelo + regra do cotovelo do rig) ao longo dos ciclos e no gesto de lançar
X3_4 estampa legível (OCR) no gesto de lançar (de frente), para alvos em várias direções
X3_5 determinismo · X3_6 tempo de desenho · X3_7 folha · X3_8 vídeo na rua (com X1 e X2) · X3_9 integridade
"""
import copy, hashlib, json, math, subprocess, sys, time, unicodedata
from pathlib import Path
import numpy as np, cv2, skia

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[3]
for p in (RAIZ, RAIZ / "cenografia" / "testes", AQUI, AQUI.parent / "x1_tom_de_luz"):
    sys.path.insert(0, str(p))
import aranha as X3                                                 # noqa: E402
HV, GE, X2 = X3.HV, X3.GE, X3.X2
OUT = AQUI / "saidas"; OUT.mkdir(exist_ok=True)
PAL = {k: np.array([int(v[i:i + 2], 16) for i in (1, 3, 5)]) for k, v in HV.MOD["paleta"].items()}
MAO = {"pele", "pele_s", "contorno"}; TENIS = {"tenis", "tenis_s", "tenis_faixa", "sola", "contorno"}
ALT = 900; WS, HS = 1400, 1500
res = {}


def _cai_em(rgb, cores, tol=14):
    x = rgb.astype(float)
    if any(np.abs(x - PAL[k]).max() <= tol for k in cores):
        return True
    c0 = PAL["contorno"].astype(float)
    for k in cores:
        if k != "contorno":
            d = PAL[k] - c0; t = float(np.clip((x - c0) @ d / max(d @ d, 1e-9), 0, 1))
            if np.abs(x - (c0 + t * d)).max() <= 8:
                return True
    return False


def _img(desenho):
    s = skia.Surface(WS, HS); c = s.getCanvas(); c.clear(0); r = desenho(c)
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType), r


# ------------------------------------------------------------------ testes
def t_plantados():
    out = {}
    for vista in ("costas", "perfil"):
        E = X3.Escalada(vista); x0, y0 = WS / 2, HS - 60; desl = {}; alc = []
        anterior = {}
        for k in range(0, int(E.T * 2 * 30) + 1):
            t = k / 30; _, erros = E.pose(t); alc += list(erros.values())
            for nome in ("mao_d", "mao_e", "pe_d", "pe_e"):
                _, plantado = E.apoio(nome, t); p = np.array(E.ponto_tela(x0, y0, ALT, t, nome))
                if plantado and nome in anterior and anterior[nome][1]:
                    desl.setdefault(nome, []).append(float(np.linalg.norm(p - anterior[nome][0])))
                anterior[nome] = (p, plantado)
        out[vista] = {"deslize_max_px_por_quadro": {k: round(max(v), 3) for k, v in desl.items()},
                      "alcance_ik_erro_max_H": round(max(alc), 4), "altura_px": ALT,
                      "sobe_H_por_s": round(E.v, 3)}
    return out


def t_contatos():
    out = {}
    for vista in ("costas", "perfil"):
        E = X3.Escalada(vista); ok = {"mao": [], "pe": []}
        for k in range(0, int(E.T * 30), 3):
            t = k / 30; x0, y0 = WS / 2, HS - 60 + E.v * t * ALT / 4       # mantém o Heitor no quadro
            img, _ = _img(lambda c: E.desenhar(c, x0, y0, ALT, t))
            for nome in ("mao_d", "mao_e", "pe_d", "pe_e") if vista == "costas" else ("mao_d", "mao_e", "pe_d"):   # perfil: o pé de trás pode ficar escondido
                _, plantado = E.apoio(nome, t)
                if not plantado:
                    continue
                px, py = E.ponto_tela(x0, y0, ALT, t, nome); ix, iy = int(round(px)), int(round(py))
                if nome.startswith("pe_"):              # tornozelo → um pouco abaixo, no tênis
                    q = HV.esqueleto(E.pose(t)[0], vista)[nome].mapXY(0.10 if vista == "perfil" else 0.0, 0.10)
                    o = E.origem(t); ix, iy = int(round(x0 + (o[0] + q.x()) * ALT / 4)), int(round(y0 + (o[1] + q.y()) * ALT / 4))
                cores = MAO if nome.startswith("mao") else TENIS
                ok[nome[:3].rstrip("_")].append(bool(img[iy, ix, 3] > 200 and _cai_em(img[iy, ix, :3], cores)))
        out[f"escalada_{vista}"] = {"mao_na_mao_pct": round(100 * np.mean(ok["mao"]), 1), "pe_no_tenis_pct": round(100 * np.mean(ok["pe"]), 1),
                                    "amostras": len(ok["mao"]) + len(ok["pe"])}
    B = X3.Balanco(); oks = []
    for k in range(0, 72, 4):
        t = k / 30; ax, ay, L = WS / 2, 60, 520
        img, mao = _img(lambda c: B.desenhar(c, ax, ay, L, ALT * 0.8, t))
        ix, iy = int(round(mao[0])), int(round(mao[1])); oks.append(bool(img[iy, ix, 3] > 200 and _cai_em(img[iy, ix, :3], MAO)))
    out["balanco_fio_chega_na_mao_pct"] = round(100 * np.mean(oks), 1); out["balanco_amostras"] = len(oks)
    return out


def t_juntas():
    out = {}; tot = 0
    for vista in ("costas", "perfil"):
        E = X3.Escalada(vista)
        for k in range(0, int(E.T * 30) + 1):
            p, _ = E.pose(k / 30); f = X3.limites(p, vista); tot += 1
            if f:
                out.setdefault(f"escalada_{vista}", []).append({"t": round(k / 30, 2), "fora": f})
    B = X3.Balanco()
    for k in range(0, int(B.T * 30) + 1):
        p = B.pose(k / 30); f = X3.limites(p, "perfil"); tot += 1
        if f:
            out.setdefault("balanco", []).append({"t": round(k / 30, 2), "fora": f})
    for vista, lado, alvo in alvos_lancar():
        p = HV.pose_base(vista); X3.pose_lancar(p, vista, lado, alvo); f = X3.limites(p, vista); tot += 1
        if f:
            out.setdefault("lancar", []).append({"vista": vista, "alvo": alvo, "fora": f})
    return {"poses_verificadas": tot, "violacoes": out or "nenhuma"}


def alvos_lancar():
    """(vista, mão, alvo em H): para cima à direita/esquerda, para a frente-alto, para o lado (frente e perfil)."""
    return [("frente", "e", (2.6, -4.6)), ("frente", "d", (-2.6, -4.6)), ("frente", "e", (3.2, -3.0)), ("frente", "d", (-3.2, -2.6)),
            ("perfil", "d", (3.0, -4.4)), ("perfil", "d", (3.4, -3.0))]


def t_estampa():
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(); out = {}; erros = {}
    for vista, lado, alvo in [a for a in alvos_lancar() if a[0] == "frente"]:
        p = HV.pose_base(vista); erros[f"{lado} {alvo}"] = round(X3.pose_lancar(p, vista, lado, alvo), 2)
        img, _ = _img(lambda c: HV.desenhar(c, WS / 2, HS - 80, ALT, vista="frente", pose=p, rosto="convencido"))
        a = img[..., 3:].astype(np.float32) / 255; rgb = (img[..., :3] * a + 237 * (1 - a)).astype(np.uint8)
        txt = " ".join(t for _, t, cf in (ocr(rgb[..., ::-1].copy())[0] or []))
        norm = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode().upper().replace(" ", "")
        out[f"mão {lado} → alvo {alvo}"] = {"texto": txt, "MODO_CURIOSO_lido": "MODOCURIOSO" in norm}
    out["_erro_de_mira_graus"] = erros
    return out


def t_det_tempo():
    E = X3.Escalada("costas"); B = X3.Balanco()
    a, _ = _img(lambda c: E.desenhar(c, WS / 2, HS - 60, ALT, 0.8)); b, _ = _img(lambda c: E.desenhar(c, WS / 2, HS - 60, ALT, 0.8))
    c1, _ = _img(lambda c: B.desenhar(c, WS / 2, 60, 520, ALT * 0.8, 0.5)); c2, _ = _img(lambda c: B.desenhar(c, WS / 2, 60, 520, ALT * 0.8, 0.5))
    tempos = {}
    for nome, f in (("escalada_costas", lambda c, t: X3.Escalada("costas").desenhar(c, WS / 2, HS - 60, ALT, t)),
                    ("escalada_perfil", lambda c, t: X3.Escalada("perfil").desenhar(c, WS / 2, HS - 60, ALT, t)),
                    ("balanco", lambda c, t: B.desenhar(c, WS / 2, 60, 520, ALT * 0.8, t))):
        ts = []
        for k in range(20):
            s = skia.Surface(WS, HS); cv = s.getCanvas(); t0 = time.perf_counter(); f(cv, k / 30); ts.append(time.perf_counter() - t0)
        tempos[nome + "_ms"] = round(1000 * float(np.mean(ts)), 1)
    return {"escalada_mesmo_quadro_identico": bool(np.array_equal(a, b)), "balanco_mesmo_quadro_identico": bool(np.array_equal(c1, c2)),
            "tempo_desenho_cpu": tempos}


def folha():
    from e0_testes import _texto
    cel = []; fundo = np.array([214, 219, 226])
    def quadro(desenho, rot, parede=None):
        s = skia.Surface(520, 760); c = s.getCanvas(); c.clear(skia.ColorSetRGB(*fundo))
        if parede:
            c.drawRect(skia.Rect.MakeLTRB(*parede), skia.Paint(Color=skia.ColorSetRGB(196, 178, 156)))
        desenho(c); return _texto(s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].copy(), [rot], 16, 20)
    for t in (0.0, 0.35, 0.7, 1.05):
        E = X3.Escalada("costas"); cel.append(quadro(lambda c, E=E, t=t: E.desenhar(c, 260, 700 + E.v * t * 100, 400, t), f"escalada de costas · {t:.2f}s", (130, 0, 390, 760)))
    for t in (0.0, 0.7):
        E = X3.Escalada("perfil"); cel.append(quadro(lambda c, E=E, t=t: E.desenhar(c, 220, 700 + E.v * t * 100, 400, t), f"escalada de perfil · {t:.2f}s", (220 + 0.66 * 100, 0, 520, 760)))
    B = X3.Balanco()
    for t in (0.0, 0.6, 1.2, 1.8):
        def d(c, t=t):
            m = B.desenhar(c, 260, 30, 250, 330, t, rosto="alegria")
            c.drawLine(260, 30, m[0], m[1], skia.Paint(AntiAlias=True, StrokeWidth=2, Color=skia.ColorSetRGB(110, 110, 110)))
        cel.append(quadro(d, f"balanço · {t:.1f}s (fio provisório)"))
    for vista, lado, alvo in alvos_lancar():
        p = HV.pose_base(vista); X3.pose_lancar(p, vista, lado, alvo)
        cel.append(quadro(lambda c, p=p, vista=vista: HV.desenhar(c, 260, 720, 400, vista=vista, pose=p, rosto="convencido"), f"lançar · {vista} · alvo {alvo}"))
    linhas = [np.hstack(cel[i:i + 8]) for i in range(0, 16, 8)]
    cv2.imwrite(str(OUT / "X3_folha.jpg"), np.vstack(linhas)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    return {"arquivo": "saidas/X3_folha.jpg", "quadros": len(cel)}


# ------------------------------------------------------------------ vídeo na rua
TOM_PAREDE = {"nome": "x3_parede", "vista": "costas", "horario": "tarde_dourada", "clima": "limpo",
              "camera": {"pos": [1.0, 6.2, 2.0], "alvo": [-6.0, 6.2, 2.7], "lente_mm": 30}}


def _mundo(P, u, v, z):
    I = P.m["intrinsecos"]; pos, dr, dx, cima = (np.asarray(I[k], float) for k in ("pos", "dir", "dir_x", "cima"))
    return pos + z * (dr + (u - P.cx) / P.f * dx - (v - P.cy) / P.f * cima)


def t_video(previa=None):
    import e6_cena_prova as E6, e1_testes as T1, e0_testes as T0
    from cenografia.nucleo.atmosfera import Atmosfera
    import tom_de_luz as X1
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "X3_aranha_demo.mp4")]
    pr = None if previa else subprocess.Popen(cmd, stdin=subprocess.PIPE); n = 0; tempos = []; quadros = []; t00 = time.time()
    Hm = 0.35
    # tomada 1: escalada de costas no pilar entre as lojas (placa nova, câmera de frente para a parede)
    P, _, _ = E6.placa(TOM_PAREDE); A = Atmosfera(P, "limpo", 11); E = X3.Escalada("costas")
    pe0 = _mundo(P, 455, 0, 1.0); base = _mundo(P, 455, 1300, 7.55)        # 25 cm à frente do pilar (7,8 m)
    base = np.array([base[0], base[1], 0.154 + 0.45])                          # começa já na parede, 45 cm acima da calçada
    for k in range(int(4.5 * 30)):
        if previa is not None and ("p", k) not in previa:
            continue
        t = k / 30; o = E.origem(t); pw = base + [0, 0, -o[1] * Hm]
        u_ = min(1.0, t / 4.5); cam = {"ty": 0.0 + 0.10 * (u_ * u_ * (3 - 2 * u_))}
        def desenh(cv, proj, t=t, pw=pw):
            x, y, _ = proj(*E6.projetar(P, pw)); _, yt, _ = proj(*E6.projetar(P, pw + [0, 0, 1.4]))
            E.desenhar(cv, x, y, y - yt, t)
        tom = X1.fazer_tom({"pe_mundo": tuple(pw), "altura_m": 1.4})
        tq = time.time()
        img = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO["tarde_dourada"])), cam=cam,
                       personagem=desenh, profundidade_personagem=E6.projetar(P, pw)[2], semente_grao=n, ceu_extra=A.ceu(t), tom_personagem=tom)
        tempos.append(time.time() - tq); q = T0._marca(T0._texto(img, ["aranha: escalada (teste, não é história)"], 40, 40))
        if previa is not None:
            quadros.append(cv2.resize(q, (360, 640))); continue
        pr.stdin.write(np.ascontiguousarray(q).tobytes()); n += 1
        if k % 45 == 22:
            quadros.append(cv2.resize(q, (360, 640), interpolation=cv2.INTER_AREA))
    # tomada 2: balanço no fio (tarde, perfil), fio provisório até uma âncora acima do quadro
    tom2 = next(x for x in E6.PLANO["tomadas"] if x["nome"] == "tarde_perfil"); P2, _, _ = E6.placa(tom2); A2 = Atmosfera(P2, "limpo", 11)
    B = X3.Balanco(amplitude=22.0, periodo=2.6); anc = np.array([-5.4, 3.55, 5.0]); L_m = 3.0
    for k in range(int(5.2 * 30)):
        if previa is not None and ("b", k) not in previa:
            continue
        t = 0.65 + k / 30; cam = {"tx": -0.1 + 0.2 * k / 156}
        def desenh2(cv, proj, t=t):
            ax, ay, _ = proj(*E6.projetar(P2, anc)); _, ay2, _ = proj(*E6.projetar(P2, anc - [0, 0, L_m]))
            _, yb, _ = proj(*E6.projetar(P2, anc - [0, 0, L_m + 1.4])); alt = yb - ay2; L = ay2 - ay
            mao = B.desenhar(cv, ax, ay, L, alt, t, rosto=__import__("animacao").rosto_com_piscada("alegria", t))
            cv.drawLine(ax, ay, mao[0], mao[1], skia.Paint(AntiAlias=True, StrokeWidth=max(1.5, alt * 0.004), Color=skia.ColorSetARGB(230, 236, 236, 230)))
        pel = anc - [0, 0, L_m + 0.6]
        tom = X1.fazer_tom({"pe_mundo": tuple(pel - [0, 0, 0.6]), "altura_m": 1.4})
        tq = time.time()
        img = P2.compor(pesos=A2.pesos(), nevoa=A2.nevoa(), grade=A2.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO["tarde_dourada"])), cam=cam,
                        personagem=desenh2, profundidade_personagem=E6.projetar(P2, pel)[2], semente_grao=n, ceu_extra=A2.ceu(t), tom_personagem=tom)
        tempos.append(time.time() - tq); q = T0._marca(T0._texto(img, ["aranha: balanço · fio provisório (teste, não é história)"], 40, 40))
        if previa is not None:
            quadros.append(cv2.resize(q, (360, 640))); continue
        pr.stdin.write(np.ascontiguousarray(q).tobytes()); n += 1
        if k % 45 == 22:
            quadros.append(cv2.resize(q, (360, 640), interpolation=cv2.INTER_AREA))
    # tomada 3: gesto de lançar (manhã, frente)
    tom3 = next(x for x in E6.PLANO["tomadas"] if x["nome"] == "manha_frente"); P3, _, _ = E6.placa(tom3); A3 = Atmosfera(P3, "limpo", 11)
    pe3 = np.array([-5.1, 6.0, 0.154])
    for k in range(int(2.5 * 30)):
        if previa is not None and ("l", k) not in previa:
            continue
        t = k / 30; kk = GE.curva(min(1.0, t / 0.35), "volta") if t < 1.8 else 1 - GE.curva((t - 1.8) / 0.5, "suave")
        base3 = HV.pose_base("frente"); alvo = X3.pose_lancar(copy.deepcopy(base3), "frente", "e", (2.6, -4.6))
        mira = HV.pose_base("frente"); X3.pose_lancar(mira, "frente", "e", (2.6, -4.6))
        p = X2.transicao(base3, mira, max(0.0, min(1.0, kk))) if kk < 1.0 else mira
        rosto = GE.mistura_expr(HV.EXPRESSOES["neutro"], HV.EXPRESSOES["convencido"], max(0.0, min(1.0, kk)))
        def desenh3(cv, proj, p=p, rosto=rosto):
            x, y, _ = proj(*E6.projetar(P3, pe3)); _, yt, _ = proj(*E6.projetar(P3, pe3 + [0, 0, 1.4])); alt = y - yt
            cv.drawOval(skia.Rect.MakeXYWH(x - 0.16 * alt, y - 0.014 * alt, 0.32 * alt, 0.028 * alt),
                        skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(110, 40, 28, 22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.01 * alt)))
            HV.desenhar(cv, x, y, alt, vista="frente", pose=p, rosto=rosto)
        tom = X1.fazer_tom({"pe_mundo": tuple(pe3), "altura_m": 1.4}); tq = time.time()
        img = P3.compor(pesos=A3.pesos(), nevoa=A3.nevoa(), grade=A3.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO["manha"])),
                        personagem=desenh3, profundidade_personagem=E6.projetar(P3, pe3)[2], semente_grao=n, ceu_extra=A3.ceu(t), tom_personagem=tom)
        tempos.append(time.time() - tq); q = T0._marca(T0._texto(img, ["aranha: gesto de lançar (teste, não é história)"], 40, 40))
        if previa is not None:
            quadros.append(cv2.resize(q, (360, 640))); continue
        pr.stdin.write(np.ascontiguousarray(q).tobytes()); n += 1
        if k % 45 == 22:
            quadros.append(cv2.resize(q, (360, 640), interpolation=cv2.INTER_AREA))
    if previa is not None:
        cv2.imwrite(sys.argv[2], np.hstack(quadros)[..., ::-1]); return {}
    pr.stdin.close(); pr.wait()
    cv2.imwrite(str(OUT / "X3_aranha_quadros.jpg"), np.hstack(quadros)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
    return {"quadros": n, "duracao_s": round(n / 30, 1), "composicao_media_s": round(float(np.mean(tempos)), 2),
            "composicao_max_s": round(float(np.max(tempos)), 2), "tempo_total_s": round(time.time() - t00, 1)}


def t_integridade():
    caminhos = ["personagens/heitor/rig_v2", "docs/IDENTIDADE_OFICIAL.md", "skills/"]
    ls = subprocess.run(["git", "ls-files", "-s"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout
    dif = subprocess.run(["git", "status", "--porcelain", "--"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    f1 = subprocess.run([str(RAIZ / ".venv/bin/python"), "codigo/verificar_f1.py"], cwd=RAIZ / "personagens/heitor/rig_v2", capture_output=True, text=True).stdout
    return {"assinatura_rig_identidade_skill": hashlib.sha256(ls.encode()).hexdigest(), "alteracoes_pendentes_nesses_caminhos": dif or "nenhuma",
            "verificar_f1_vistas_ok": f1.count("| OK |")}


if __name__ == "__main__":
    if sys.argv[1:2] == ["previa"]:
        t_video([("p", 10), ("p", 70), ("p", 130), ("b", 10), ("b", 50), ("b", 90), ("b", 140), ("l", 5), ("l", 40)]); sys.exit()
    so = sys.argv[1:]; caminho = OUT / "x3_metricas.json"
    if caminho.exists():
        res = json.loads(caminho.read_text())
    for nome, f in (("X3_1_plantados", t_plantados), ("X3_2_contatos", t_contatos), ("X3_3_juntas", t_juntas), ("X3_4_estampa", t_estampa),
                    ("X3_5_6_det_tempo", t_det_tempo), ("X3_7_folha", folha), ("X3_8_video", t_video), ("X3_9_integridade", t_integridade)):
        if so and nome not in so:
            continue
        t = time.time(); r = f(); r["_duracao_teste_s"] = round(time.time() - t, 1); res[nome] = r
        print(nome, json.dumps(r, ensure_ascii=False, default=str)[:1500], flush=True)
        caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
