#!/usr/bin/env python3
"""Testes e demonstração da EXTENSÃO X4 (elasticidade) — PROPOSTA, aguardando aprovação.

X4_1 partes intactas: mão, manga, barra da calça e tênis idênticos ao rig sem esticar (recortes comparados pixel a pixel)
X4_2 espessura do membro esticado = a do membro normal (mesmo ponto relativo do osso)
X4_3 volta exata: no fim da mola o desenho é IDÊNTICO ao do rig sem extensão (bytes)
X4_4 alcance: a palma chega ao alvo (px); escorço usado
X4_5 juntas e escorço dentro dos limites ao longo das animações
X4_6 estampa legível (OCR) durante o alcance de frente; tronco e cabeça idênticos nas pernas de pau (só sobem)
X4_7 determinismo e tempo · X4_8 folha · X4_9 vídeo na rua (com X1) · X4_10 integridade
"""
import copy, hashlib, json, math, subprocess, sys, time, unicodedata
from pathlib import Path
import numpy as np, cv2, skia

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[3]
for p in (RAIZ, RAIZ / "cenografia" / "testes", AQUI, AQUI.parent / "x1_tom_de_luz"):
    sys.path.insert(0, str(p))
import elasticidade as X4                                           # noqa: E402
HV, GE, X2, X3 = X4.HV, X4.GE, X4.X2, X4.X3
OUT = AQUI / "saidas"; OUT.mkdir(exist_ok=True)
ALT = 800; WS, HS = 2400, 1700; U = ALT / 4; X0, Y0 = 1200, 1600
ALVOS = [("frente", "e", (3.4, -3.0)), ("frente", "d", (-3.6, -3.4)), ("frente", "e", (1.6, -6.0)), ("perfil", "d", (4.6, -2.6)), ("perfil", "d", (3.2, -5.4))]
res = {}


def render(pose, vista, rosto=None, x=X0, y=Y0):
    s = skia.Surface(WS, HS); c = s.getCanvas(); c.clear(0); X4.desenhar(c, x, y, ALT, vista=vista, pose=pose, rosto=rosto)
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.int16)


def recorte(img, cx, cy, r):
    return img[int(round(cy - r)):int(round(cy + r)), int(round(cx - r)):int(round(cx + r))]


def t_partes():
    out = {}
    for vista, lado, alvo in ALVOS:
        p, erro, esc = X4.alcance(HV.pose_base(vista), vista, lado, alvo)
        if p.get(f"mao_vista_{lado}"):
            pass
        q = copy.deepcopy(p); q[f"esc_antebraco_{lado}"] = 1.0           # mesmos ângulos, sem esticar
        pa, pb = X3.palma(p, vista, lado), X3.palma(q, vista, lado)
        A = render(p, vista)
        B = render(q, vista, x=X0 + (pa[0] - pb[0]) * U, y=Y0 + (pa[1] - pb[1]) * U)   # o normal deslocado: as duas mãos no mesmo lugar
        r = 0.30 * U; cx, cy = X0 + pa[0] * U, Y0 + pa[1] * U
        ca = recorte(A, cx, cy, r); cb = recorte(B, cx, cy, r)
        # só a MÃO: pixels além do punho (no sistema do osso da mão, y local > 0); o antebraço afina diferente ao esticar
        Mm = HV.esqueleto(p, vista)[f"mao_{lado}"]; w0 = Mm.mapXY(0, 0); w1 = Mm.mapXY(0, 1)
        ax_ = np.array([w1.x() - w0.x(), w1.y() - w0.y()]); ax_ /= np.linalg.norm(ax_)
        yy, xx = np.mgrid[0:ca.shape[0], 0:ca.shape[1]]; gx = (xx + int(round(cx - r)) - X0) / U - w0.x(); gy = (yy + int(round(cy - r)) - Y0) / U - w0.y()
        alem = (gx * ax_[0] + gy * ax_[1]) > 0.01
        ma, mb = (ca[..., 3] > 127) & alem, (cb[..., 3] > 127) & alem; iou = float((ma & mb).sum() / max((ma | mb).sum(), 1))
        Bm = render(q, vista); Ms = HV.esqueleto(p, vista)[f"braco_{lado}"].mapXY(0, 0.08)
        sa = recorte(A, X0 + Ms.x() * U, Y0 + Ms.y() * U, 0.22 * U); sb = recorte(Bm, X0 + Ms.x() * U, Y0 + Ms.y() * U, 0.22 * U)
        dm = np.abs(ca - cb).max(-1)[alem]; ds = np.abs(sa - sb).max(-1)
        out[f"alcance {vista} {lado} → {alvo}"] = {"escorco_antebraco": round(esc, 2), "mao_iou": round(iou, 4),
                                                  "mao_pixels_iguais_pct": round(100 * float((dm <= 2).mean()), 2), "mao_dif_max_8bit": int(dm.max()),
                                                  "manga_pixels_iguais_pct": round(100 * float((ds <= 2).mean()), 2), "manga_dif_max_8bit": int(ds.max())}
    for vista in ("frente", "perfil"):
        for k in (1.8, 2.6):
            p = HV.pose_base(vista); X4.pernas_de_pau(p, k); q = HV.pose_base(vista); A, B = render(p, vista), render(q, vista)
            pes = (slice(int(Y0 - 0.55 * U), HS), slice(0, WS))                 # tênis + barra da calça: do joelho para baixo não muda
            sobe = int(round((k - 1) * X4.L_COXA * U))
            tronco_a = A[int(Y0 - 4.05 * U - sobe):int(Y0 - 1.75 * U - sobe)]; tronco_b = B[int(Y0 - 4.05 * U):int(Y0 - 1.75 * U)]
            dif = np.abs(tronco_a - tronco_b).max(-1)
            dp = np.abs(A[pes] - B[pes]).max(-1)
            out[f"pernas de pau {vista} ×{k}"] = {"tenis_e_barra_pixels_iguais_pct": round(100 * float((dp <= 2).mean()), 3), "tenis_e_barra_dif_max_8bit": int(dp.max()),
                                                   "tenis_e_barra_pixels_diferentes": int((dp > 2).sum()),
                                                   "tronco_e_cabeca_iguais_deslocados_pct": round(100 * float((dif <= 2).mean()), 2),
                                                   "subida_px": sobe}
    return out


def _largura(img, p0, p1, frac):
    """Largura (px) do membro no ponto 'frac' do segmento p0→p1, medida na perpendicular."""
    p0, p1 = np.array(p0), np.array(p1); d = (p1 - p0) / np.linalg.norm(p1 - p0); n = np.array([-d[1], d[0]]); c = p0 + (p1 - p0) * frac
    a = [img[int(round(c[1] + n[1] * s)), int(round(c[0] + n[0] * s)), 3] > 127 for s in np.arange(-60, 60.5, 0.5)]
    return 0.5 * sum(a)


def t_espessura():
    out = {}
    for vista, lado, alvo in [ALVOS[0], ALVOS[1], ALVOS[3]]:     # o alvo (1,6; −6,0) é excluído: o braço normal cruza a cabeça e a medida pega a cabeça
        p, _, esc = X4.alcance(HV.pose_base(vista), vista, lado, alvo); q = copy.deepcopy(p); q[f"esc_antebraco_{lado}"] = 1.0
        A, B = render(p, vista), render(q, vista); res_ = []
        for img, pp in ((A, p), (B, q)):
            M = HV.esqueleto(pp, vista); e = M[f"antebraco_{lado}"].mapXY(0, 0); w = M[f"mao_{lado}"].mapXY(0, 0)
            res_.append(_largura(img, (X0 + e.x() * U, Y0 + e.y() * U), (X0 + w.x() * U, Y0 + w.y() * U), 0.5))
        out[f"{vista} {lado} ×{esc:.2f}"] = {"largura_esticado_px": res_[0], "largura_normal_px": res_[1], "diferenca_px": round(res_[0] - res_[1], 2)}
    return out


def t_volta():
    out = {}; T = X4.duracao_mola()
    for vista, lado, alvo in ALVOS[:2] + ALVOS[3:4]:
        base = HV.pose_base(vista); p, _, _ = X4.alcance(base, vista, lado, alvo, k=X4.mola(T + 0.01))
        out[f"alcance {vista} {lado}: mola no fim"] = X4.mola(T + 0.01)
        out[f"alcance {vista} {lado}: desenho identico ao rig"] = bool(np.array_equal(render(p, vista), render(HV.pose_base(vista), vista)))
    p = HV.pose_base("perfil"); X4.pernas_de_pau(p, 1.0 + 1.6 * X4.mola(T + 0.01))
    out["pernas de pau: desenho identico ao rig"] = bool(np.array_equal(render(p, "perfil"), render(HV.pose_base("perfil"), "perfil")))
    return out


def t_alcance_juntas():
    out = {"alcance": {}, "violacoes": {}}; tot = 0; T = X4.duracao_mola()
    for vista, lado, alvo in ALVOS:
        p, erro, esc = X4.alcance(HV.pose_base(vista), vista, lado, alvo)
        out["alcance"][f"{vista} {lado} → {alvo}"] = {"erro_px_a_800px": round(erro * U, 3), "escorco": round(esc, 2)}
        for k in range(int(T * 30) + 2):
            q, _, _ = X4.alcance(HV.pose_base(vista), vista, lado, alvo, k=X4.mola(k / 30)); f = X4.limites(q, vista); tot += 1
            if f:
                out["violacoes"].setdefault(f"{vista} {lado} {alvo}", []).append({"t": round(k / 30, 2), "fora": f})
    for vista in ("frente", "perfil"):
        for k in range(int(T * 30) + 2):
            q = HV.pose_base(vista); X4.pernas_de_pau(q, 1 + 1.6 * X4.mola(k / 30)); f = X4.limites(q, vista); tot += 1
            if f:
                out["violacoes"].setdefault(f"pernas {vista}", []).append({"t": round(k / 30, 2), "fora": f})
    out["poses_verificadas"] = tot; out["violacoes"] = out["violacoes"] or "nenhuma"
    return out


def t_estampa():
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(); out = {}
    for vista, lado, alvo in [a for a in ALVOS if a[0] == "frente"]:
        p, _, _ = X4.alcance(HV.pose_base(vista), vista, lado, alvo); img = render(p, vista, "alegria").astype(np.float32)
        a = img[..., 3:] / 255; rgb = (img[..., :3] * a + 237 * (1 - a)).astype(np.uint8)
        txt = " ".join(t for _, t, cf in (ocr(rgb[..., ::-1].copy())[0] or []))
        norm = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode().upper().replace(" ", "")
        out[f"{lado} → {alvo}"] = {"texto": txt, "MODO_CURIOSO_lido": "MODOCURIOSO" in norm}
    return out


def t_det_tempo():
    p, _, _ = X4.alcance(HV.pose_base("frente"), "frente", "e", ALVOS[0][2]); a, b = render(p, "frente"), render(p, "frente")
    ts = []
    for k in range(20):
        t0 = time.perf_counter(); X4.alcance(HV.pose_base("frente"), "frente", "e", ALVOS[0][2], k=X4.mola(k / 30)); ts.append(time.perf_counter() - t0)
    return {"mesmo_quadro_identico": bool(np.array_equal(a, b)), "calculo_da_pose_ms": round(1000 * float(np.mean(ts)), 2)}


def folha():
    from e0_testes import _texto
    cel = []
    def q(pose, vista, rot, alvo=None, larg=560):
        s = skia.Surface(larg, 760); c = s.getCanvas(); c.clear(skia.ColorSetRGB(214, 219, 226)); x, y = larg / 2, 720; u = 300 / 4
        if alvo:
            x = larg / 2 - alvo[0] * u * 0.5
            c.drawCircle(x + alvo[0] * u, y + alvo[1] * u, 9, skia.Paint(AntiAlias=True, Color=skia.ColorSetRGB(240, 140, 40)))
        X4.desenhar(c, x, y, 300, vista=vista, pose=pose, rosto="alegria" if vista != "costas" else None)
        return _texto(s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].copy(), [rot], 16, 20)
    for vista, lado, alvo in ALVOS:
        p, _, esc = X4.alcance(HV.pose_base(vista), vista, lado, alvo); cel.append(q(p, vista, f"alcance {vista} ×{esc:.1f}", alvo, 760))
    for k in (1.0, 1.8, 2.6):
        for vista in ("frente", "perfil"):
            p = HV.pose_base(vista); X4.pernas_de_pau(p, k); cel.append(q(p, vista, f"pernas de pau {vista} ×{k}", None, 380))
    linhas = [np.hstack(cel[:5]), np.hstack(cel[5:] + [np.full((760, 3800 - 380 * 6, 3), 214, np.uint8)])]
    cv2.imwrite(str(OUT / "X4_folha.jpg"), np.vstack(linhas)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    return {"arquivo": "saidas/X4_folha.jpg"}


def t_video(previa=None):
    import e6_cena_prova as E6, e1_testes as T1, e0_testes as T0
    from cenografia.nucleo.atmosfera import Atmosfera
    import tom_de_luz as X1
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "X4_elasticidade_demo.mp4")]
    pr = None if previa else subprocess.Popen(cmd, stdin=subprocess.PIPE); n = 0; tempos = []; quadros = []; t00 = time.time(); T = X4.duracao_mola()
    tomadas = [("manha_frente", "frente", (-5.1, 6.0, 0.154), "alcance", (-4.15, 8.96, 2.25), 2.6, "elasticidade: alcance (teste, não é história)"),
               ("tarde_perfil", "perfil", (-5.1, 2.7, 0.154), "alcance", (-6.9, 4.4, 1.45), 2.6, "elasticidade: alcance (teste, não é história)"),
               ("tarde_perfil", "perfil", (-5.1, 2.7, 0.154), "pernas", None, 2.8, "elasticidade: pernas de pau (teste, não é história)")]
    for ti, (nome, vista, pe, tipo, alvo, dur, rot) in enumerate(tomadas):
        tom = next(x for x in E6.PLANO["tomadas"] if x["nome"] == nome); P, _, _ = E6.placa(tom); A = Atmosfera(P, "limpo", 11); pe = np.array(pe)
        for k in range(int(dur * 30)):
            if previa is not None and (ti, k) not in previa:
                continue
            t = k / 30; tm = max(0.0, t - 0.35); m = X4.mola(tm, 0.35, dur - 0.35 - 0.45 - 0.45, 0.45)
            def desenh(cv, proj, t=t, m=m):
                x, y, _ = proj(*E6.projetar(P, pe)); _, yt, _ = proj(*E6.projetar(P, pe + [0, 0, 1.4])); alt = y - yt; u = alt / 4
                base = HV.pose_base(vista); base["respira"] = math.sin(2 * math.pi * t / 2.8)
                if tipo == "alcance":
                    ax, ay, _ = proj(*E6.projetar(P, alvo)); lado = "e" if (vista == "frente" and ax > x) else "d"
                    pose, _, _ = X4.alcance(base, vista, lado, ((ax - x) / u, (ay - y) / u), k=m); rosto = "surpresa" if m > 0.5 else "alegria"
                else:
                    pose = base; X4.pernas_de_pau(pose, 1.0 + 1.6 * m); pose["cabeca"] = -6.0 * m * math.sin(t * 3); rosto = "alegria"
                cv.drawOval(skia.Rect.MakeXYWH(x - 0.16 * alt, y - 0.014 * alt, 0.32 * alt, 0.028 * alt),
                            skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(110, 40, 28, 22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.01 * alt)))
                X4.desenhar(cv, x, y, alt, vista=vista, pose=pose, rosto=__import__("animacao").rosto_com_piscada(rosto, t))
            tom_fn = X1.fazer_tom({"pe_mundo": tuple(pe), "altura_m": 1.4}); tq = time.time()
            img = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[tom["horario"]])),
                           personagem=desenh, profundidade_personagem=E6.projetar(P, pe)[2], semente_grao=n, ceu_extra=A.ceu(t), tom_personagem=tom_fn)
            tempos.append(time.time() - tq); q = T0._marca(T0._texto(img, [rot], 40, 40))
            if previa is not None:
                quadros.append(cv2.resize(q, (360, 640))); continue
            pr.stdin.write(np.ascontiguousarray(q).tobytes()); n += 1
            if k % 26 == 18:
                quadros.append(cv2.resize(q, (360, 640), interpolation=cv2.INTER_AREA))
    if previa is not None:
        cv2.imwrite(sys.argv[2], np.hstack(quadros)[..., ::-1]); return {}
    pr.stdin.close(); pr.wait()
    cv2.imwrite(str(OUT / "X4_elasticidade_quadros.jpg"), np.hstack(quadros[:9])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
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
        t_video([(0, 12), (0, 30), (0, 60), (1, 30), (1, 55), (2, 25), (2, 45), (2, 70), (2, 83)]); sys.exit()
    so = sys.argv[1:]; caminho = OUT / "x4_metricas.json"
    if caminho.exists():
        res = json.loads(caminho.read_text())
    for nome, f in (("X4_1_partes", t_partes), ("X4_2_espessura", t_espessura), ("X4_3_volta", t_volta), ("X4_4_5_alcance_juntas", t_alcance_juntas),
                    ("X4_6_estampa", t_estampa), ("X4_7_det_tempo", t_det_tempo), ("X4_8_folha", folha), ("X4_9_video", t_video), ("X4_10_integridade", t_integridade)):
        if so and nome not in so:
            continue
        t = time.time(); r = f(); r["_duracao_teste_s"] = round(time.time() - t, 1); res[nome] = r
        print(nome, json.dumps(r, ensure_ascii=False, default=str)[:1600], flush=True)
        caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
