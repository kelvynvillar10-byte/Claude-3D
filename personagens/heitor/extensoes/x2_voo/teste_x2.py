#!/usr/bin/env python3
"""Testes e demonstração da EXTENSÃO X2 (voo) — PROPOSTA, aguardando aprovação.

X2_1 desenho original intacto: com × sem vento, pixel a pixel; o que mudou dentro da silhueta do rig e de que cor era
X2_2 paleta das peças novas (mechas, barra, ondas, mangas)
X2_3 estampa legível (OCR) nas poses de frente, com e sem vento, inclusive com o corpo inclinado
X2_4 limites das juntas e regra do cotovelo em todas as poses, ao longo do tempo e nas transições
X2_5 quanto o vento acrescenta (área e alcance além da silhueta)
X2_6 determinismo; vento zero = desenho sem vento; sem inclinação = rig puro
X2_7 tempo de desenho (CPU)
X2_8 folha de poses (sem | com vento) e vídeo de demonstração na rua da cena de prova (com a X1 ligada)
X2_9 integridade do rig v2 (assinatura) — a extensão fica FORA de rig_v2/
"""
import hashlib, json, math, subprocess, sys, time, unicodedata
from pathlib import Path
import numpy as np, cv2, skia

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "cenografia" / "testes")); sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "x1_tom_de_luz"))
import voo as V                                                     # noqa: E402
HV, AN = V.HV, V.AN
OUT = AQUI / "saidas"; OUT.mkdir(exist_ok=True)
PAL = {k: np.array([int(v[i:i + 2], 16) for i in (1, 3, 5)]) for k, v in HV.MOD["paleta"].items()}
PERMITIDAS_COBRIR = {"jeans", "jeans_s", "barra", "contorno"}      # só o cós do jeans (e as costuras/contorno dele)
NOVAS = {"cabelo", "cabelo_s", "camisa", "camisa_s", "contorno"}
res = {}

# (vista, pose, vento na tela, inclinação, direção) — as situações de uso
CASOS = [("perfil", "agachar", (0.0, 0.0), 0.0, 1), ("perfil", "impulso", (0.0, 0.7), 0.0, 1), ("perfil", "pairar", (0.1, -0.35), 0.0, 1),
         ("perfil", "cruzeiro", (-1.0, 0.0), 72.0, 1), ("perfil", "cruzeiro", (1.0, 0.0), 72.0, -1), ("perfil", "pousar", (0.2, -0.6), -8.0, 1),
         ("frente", "pairar", (0.1, -0.35), 0.0, 1), ("frente", "impulso", (0.0, 0.7), 0.0, 1), ("frente", "curva", (0.5, 0.4), 22.0, 1),
         ("frente", "curva", (-0.5, 0.4), -22.0, 1), ("costas", "pairar", (0.1, -0.35), 0.0, 1), ("costas", "curva", (-0.5, 0.4), -22.0, 1)]
ALT = 900; WS, HS = 1300, 1300


def rot(caso):
    v, n, ve, inc, d = caso; return f"{v} · {n}" + (" (espelho)" if d < 0 else "") + (f" · {inc:+.0f}°" if inc else "")


def raster(caso, t=0.4, **k):
    vista, nome, vento, inc, d = caso
    s = skia.Surface(WS, HS); c = s.getCanvas(); c.clear(0)
    V.desenhar(c, WS / 2, HS * 0.52, ALT, vista=vista, direcao=d, pose=V.pose_voo(nome, vista, t), rosto="alegria" if vista != "costas" else None,
               inclinacao=inc, vento=vento, t=t, **k)
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.int16)


def classe(rgb):
    """Nome da cor da paleta mais próxima (≤ 12 por canal) ou 'mistura' (borda suavizada)."""
    melhor, dist = "mistura", 13
    for k, p in PAL.items():
        dd = int(np.abs(rgb - p).max())
        if dd < dist:
            melhor, dist = k, dd
    return melhor


def classe_nova(rgb):
    """Cor de uma peça nova: uma cor permitida (≤ 12 por canal), 'mistura' (borda suavizada entre DUAS cores permitidas,
    ≤ 8 da reta entre elas) ou o nome da cor oficial mais próxima (que não deveria aparecer)."""
    rgb = rgb.astype(float)
    for k in NOVAS:
        if np.abs(rgb - PAL[k]).max() <= 12:
            return k
    ks = sorted(NOVAS)
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            d = PAL[b] - PAL[a]; tt = np.clip((rgb - PAL[a]) @ d / max(d @ d, 1e-9), 0, 1)
            if np.abs(rgb - (PAL[a] + tt * d)).max() <= 8:
                return "mistura"
    return classe(rgb)


# ------------------------------------------------------------------ testes
def t_intacto():
    out = {}
    for caso in CASOS:
        A = raster(caso, sem_vento=True); B = raster(caso)
        orig = A[..., 3] >= 254; mud = orig & (np.abs(B - A).max(-1) > 2)
        cont = {}
        for y, x in zip(*np.nonzero(mud)):
            k = classe(A[y, x, :3]); cont[k] = cont.get(k, 0) + 1
        indevidas = {k: v for k, v in cont.items() if k not in PERMITIDAS_COBRIR and k != "mistura"}
        out[rot(caso)] = {"pixels_do_rig": int(orig.sum()), "pixels_do_rig_cobertos": int(mud.sum()),
                          "pct_coberto": round(100 * mud.sum() / max(orig.sum(), 1), 2), "cores_cobertas": cont,
                          "cobriu_cor_proibida": indevidas or "nenhuma"}
    return out


def t_paleta():
    out = {}
    for caso in CASOS:
        A = raster(caso, sem_vento=True); B = raster(caso)
        nova = (B[..., 3] >= 254) & (A[..., 3] <= 2)
        if nova.sum() == 0:
            out[rot(caso)] = {"pixels_novos": 0}; continue
        cls = [classe_nova(B[y, x, :3]) for y, x in zip(*np.nonzero(nova))]
        n = len(cls); ok = sum(c in NOVAS for c in cls); mist = sum(c == "mistura" for c in cls)
        out[rot(caso)] = {"pixels_novos": n, "pct_cores_oficiais_permitidas": round(100 * ok / n, 1), "pct_mistura_de_borda": round(100 * mist / n, 1),
                          "outras_cores": sorted({c for c in cls if c not in NOVAS and c != "mistura"}) or "nenhuma"}
    return out


def t_estampa():
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(); out = {}
    for caso in [c for c in CASOS if c[0] == "frente"]:
        for vento_on in (False, True):
            img = raster(caso, sem_vento=not vento_on).astype(np.float32)
            a = img[..., 3:] / 255; rgb = (img[..., :3] * a + 237 * (1 - a)).astype(np.uint8)
            lidas = {}
            for nome_rot, im in (("como aparece na tela", rgb),):
                txt = " ".join(t for _, t, cf in (ocr(im[..., ::-1].copy())[0] or []))
                norm = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode().upper().replace(" ", "")
                lidas[nome_rot] = {"texto": txt, "MODO_CURIOSO_lido": "MODOCURIOSO" in norm}
            out[rot(caso) + (" · com vento" if vento_on else " · sem vento")] = lidas
    return out


def t_limites():
    out = {}; tot = 0
    for vista, nomes in V.POSES.items():
        for nome in nomes:
            for k in range(33):
                p = V.pose_voo(nome, vista, k * 0.1); f = V.limites(p, vista); tot += 1
                if f:
                    out.setdefault(f"{vista} · {nome}", []).append({"t": round(k * 0.1, 1), "fora": f})
    seq = [("perfil", ["agachar", "impulso", "pairar", "cruzeiro", "pousar"]), ("frente", ["pairar", "impulso", "pairar", "curva"]), ("costas", ["pairar", "curva"])]
    for vista, ns in seq:
        base = HV.pose_base(vista); ns = [None] + ns
        for a, b in zip(ns[:-1], ns[1:]):
            pa = base if a is None else V.pose_voo(a, vista, 0.0); pb = V.pose_voo(b, vista, 0.0)
            for i in range(11):
                p = V.transicao(pa, pb, i / 10); f = V.limites(p, vista); tot += 1
                if f:
                    out.setdefault(f"{vista} · {a or 'de pé'} → {b}", []).append({"k": i / 10, "fora": f})
    return {"poses_verificadas": tot, "violacoes": out or "nenhuma"}


def t_acrescimo():
    out = {}; u = ALT / 4
    for caso in CASOS:
        A = raster(caso, sem_vento=True); B = raster(caso)
        sa = A[..., 3] > 127; sb = B[..., 3] > 127; nova = sb & ~sa
        dist = cv2.distanceTransform((~sa).astype(np.uint8), cv2.DIST_L2, 5)
        out[rot(caso)] = {"area_acrescentada_pct": round(100 * nova.sum() / max(sa.sum(), 1), 1),
                          "alcance_max_alem_da_silhueta_H": round(float(dist[nova].max()) / u, 2) if nova.any() else 0.0}
    return out


def t_determinismo():
    c = CASOS[3]; a, b = raster(c), raster(c)
    sem_vento = raster(c, sem_vento=True); zero = raster(c[:2] + ((0.0, 0.0),) + c[3:])
    s = skia.Surface(WS, HS); cv = s.getCanvas(); cv.clear(0)    # rig puro (mesma posição), contra voo.desenhar sem inclinação
    p = V.pose_voo("pairar", "frente", 0.4); u = ALT / 4
    HV.desenhar(cv, WS / 2, HS * 0.52 + V.ALT_PELVE * u, ALT, vista="frente", pose=p, rosto="alegria")
    rig = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.int16)
    ext = raster(("frente", "pairar", (0.0, 0.0), 0.0, 1), sem_vento=True)
    return {"mesmo_quadro_duas_vezes": bool(np.array_equal(a, b)), "vento_zero_igual_sem_vento": bool(np.array_equal(zero, sem_vento)),
            "sem_inclinacao_igual_ao_rig_puro": bool(np.array_equal(rig, ext))}


def t_tempo():
    out = {}
    for nome, k in (("sem vento", {"sem_vento": True}), ("com vento", {})):
        ts = []
        for caso in CASOS:
            t0 = time.perf_counter(); raster(caso, **k); ts.append(time.perf_counter() - t0)
        out[nome + "_ms_medio"] = round(1000 * sum(ts) / len(ts), 1)
    out["obs"] = f"desenho a {ALT} px de altura numa tela {WS}×{HS}, incluindo a leitura do quadro"
    return out


def folha():
    from e0_testes import _texto
    linhas = []
    for i in range(0, len(CASOS), 4):
        cel = []
        for caso in CASOS[i:i + 4]:
            par = []
            for vv in (False, True):
                im = raster(caso, sem_vento=not vv).astype(np.float32); a = im[..., 3:] / 255
                rgb = (im[..., :3] * a + np.array([214, 219, 226]) * (1 - a)).astype(np.uint8)
                rgb = cv2.resize(rgb, (WS * 2 // 5, HS * 2 // 5), interpolation=cv2.INTER_AREA)
                par.append(_texto(rgb, ["com vento" if vv else "sem vento"], 16, 18))
            cel.append(_texto(np.hstack(par), [rot(caso)], 480, 20))
        linhas.append(np.hstack(cel))
    cv2.imwrite(str(OUT / "X2_folha_poses.jpg"), np.vstack(linhas)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    return {"arquivo": "saidas/X2_folha_poses.jpg", "casos": len(CASOS)}


# ------------------------------------------------------------------ demonstração na rua (cena de prova da E6 + X1)
def _suave(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def roteiro_perfil(t):
    """Tomada 1 (tarde, perfil): de pé → agacha → impulso → sobe → paira → inclina e sai voando para a direita."""
    Hm = 1.4 / 4; z0 = 0.154; y0 = 2.8; pe = HV.pose_base("perfil"); rosto = "neutro"
    if t < 0.6:
        pose = pe; zp = z0 + V.altura_pelve(pose) * Hm; y = y0; inc = 0.0; vel = (0.0, 0.0)
    elif t < 1.1:
        k = _suave((t - 0.6) / 0.5); pose = V.transicao(pe, V.pose_voo("agachar", "perfil", t), k); rosto = "convencido"
        zp = z0 + V.altura_pelve(pose) * Hm; y = y0; inc = 0.0; vel = (0.0, 0.0)
    elif t < 2.6:
        k = _suave((t - 1.1) / 0.25); ag = V.pose_voo("agachar", "perfil", t); im = V.pose_voo("impulso", "perfil", t)
        pose = V.transicao(ag, im, k) if t < 1.35 else V.transicao(im, V.pose_voo("pairar", "perfil", t), _suave((t - 1.35) / 1.0))
        subida = 1.1 * (1 - (1 - min(1.0, (t - 1.1) / 1.5)) ** 3)            # sobe 1,1 m desacelerando
        zp = z0 + V.altura_pelve(ag if t < 1.1 else pe) * Hm * (1 - k) + V.ALT_PELVE * Hm * k + subida
        vz = 1.1 * 3 * (1 - min(1.0, (t - 1.1) / 1.5)) ** 2 / 1.5; y = y0; inc = 0.0; vel = (0.0, vz); rosto = "alegria"
    elif t < 4.0:
        pose = V.pose_voo("pairar", "perfil", t); zp = z0 + V.ALT_PELVE * Hm + 1.1 + 0.035 * Hm * 0; y = y0; inc = 0.0; vel = (0.0, 0.0); rosto = "alegria"
    else:
        k = _suave((t - 4.0) / 0.8); pose = V.transicao(V.pose_voo("pairar", "perfil", t), V.pose_voo("cruzeiro", "perfil", t), k)
        inc = 72.0 * k; tt = t - 4.0; y = y0 + 0.9 * tt ** 2 if tt < 1.2 else y0 + 1.296 + 2.16 * (tt - 1.2) + 1.2 * (tt - 1.2) ** 2
        vy = 1.8 * tt if tt < 1.2 else 2.16 + 2.4 * (tt - 1.2); zp = z0 + V.ALT_PELVE * Hm + 1.1 + 0.25 * k; vel = (vy, 0.0); rosto = "alegria"
    vento_tela = (-vel[0] / 5.0, vel[1] / 4.0)                                 # ar relativo = contra a velocidade (tela: +y mundo = +x)
    if 2.0 < t < 4.6:
        vento_tela = (vento_tela[0] + 0.08, vento_tela[1] - 0.32)             # corrente de ar do poder enquanto paira
    return {"mundo_pelve": (-5.1, y, zp), "pose": pose, "inclinacao": inc, "vento": vento_tela, "rosto": rosto, "chao": z0}


def roteiro_frente(t):
    """Tomada 2 (manhã, frente): paira de frente e faz curvas para um lado e para o outro."""
    Hm = 1.4 / 4; s = math.sin(2 * math.pi * t / 4.0); c = math.cos(2 * math.pi * t / 4.0)
    pose = V.transicao(V.pose_voo("pairar", "frente", t), V.pose_voo("curva", "frente", t), _suave(abs(s) * 1.3))
    x = -5.6 + 0.35 * s; vx = 0.35 * 2 * math.pi / 4.0 * c
    return {"mundo_pelve": (x, 7.0, 0.154 + V.ALT_PELVE * Hm + 1.0), "pose": pose, "inclinacao": -22.0 * s,
            "vento": (-vx / 0.9 * 0.6, -0.3), "rosto": "alegria", "chao": 0.154}


def t_video(previa=None):
    import e6_cena_prova as E6, e1_testes as T1, e0_testes as T0
    from cenografia.nucleo.atmosfera import Atmosfera
    import tom_de_luz as X1
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "X2_voo_demo.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); n = 0; t0 = time.time(); tempos = []; quadros = []
    for nome_tom, dur, roteiro, vista in (("tarde_perfil", 6.0, roteiro_perfil, "perfil"), ("manha_frente", 4.0, roteiro_frente, "frente")):
        tom = next(x for x in E6.PLANO["tomadas"] if x["nome"] == nome_tom); P, _, _ = E6.placa(tom); A = Atmosfera(P, tom["clima"], 11)
        for k in range(int(dur * 30)):
            if previa is not None and (nome_tom, k) not in previa:
                continue
            t = k / 30; r = roteiro(t); pm = r["mundo_pelve"]
            pel = E6.projetar(P, pm); chao = E6.projetar(P, (pm[0], pm[1], r["chao"]))
            a_ = E6.projetar(P, (pm[0], pm[1], pm[2] - 0.6)); b_ = E6.projetar(P, (pm[0], pm[1], pm[2] + 0.8))
            altura_ch = pm[2] - r["chao"] - V.ALT_PELVE * 0.35

            def desenhista(cv, proj, r=r, pel=pel, chao=chao, a_=a_, b_=b_, altura_ch=altura_ch, t=t):
                x, y, _ = proj(*pel); _, ya, _ = proj(*a_); _, yb, _ = proj(*b_); alt = (ya - yb) / 1.4 * 1.4
                xc, yc, _ = proj(*chao); f = max(0.15, 1 - altura_ch / 2.5)            # sombra no chão: some com a altura
                cv.drawOval(skia.Rect.MakeXYWH(xc - 0.16 * alt * f, yc - 0.014 * alt, 0.32 * alt * f, 0.028 * alt),
                            skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(110 * f), 40, 28, 22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.01 * alt + 6 * (1 - f))))
                V.desenhar(cv, x, y, alt, vista=vista, direcao=1, pose=r["pose"], rosto=AN.rosto_com_piscada(r["rosto"], t),
                           inclinacao=r["inclinacao"], vento=r["vento"], t=t)
            u_ = t / dur; mov = {kk: aa + (bb - aa) * _suave(u_) for kk, (aa, bb) in tom["movimento"].items()}
            tom_fn = X1.fazer_tom({"pe_mundo": (pm[0], pm[1], pm[2] - V.ALT_PELVE * 0.35), "altura_m": 1.4})
            tq = time.time()
            img = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[tom["horario"]])), cam=mov,
                           personagem=desenhista, profundidade_personagem=pel[2], semente_grao=n, ceu_extra=A.ceu(t), frente_extra=A.frente(t),
                           tom_personagem=tom_fn)
            tempos.append(time.time() - tq)
            q = T0._marca(T0._texto(img, ["voo (teste, não é história)"], 40, 40))
            if previa is not None:
                quadros.append(cv2.resize(q, (540, 960), interpolation=cv2.INTER_AREA)); continue
            pr.stdin.write(np.ascontiguousarray(q).tobytes()); n += 1
            if k % 45 == 20:
                quadros.append(cv2.resize(q, (360, 640), interpolation=cv2.INTER_AREA))
    pr.stdin.close(); pr.wait()
    if previa is not None:
        cv2.imwrite(sys.argv[2], np.hstack(quadros)[..., ::-1]); return {}
    cv2.imwrite(str(OUT / "X2_voo_quadros.jpg"), np.vstack([np.hstack(quadros[i:i + 5]) for i in range(0, len(quadros) - len(quadros) % 5, 5)])[..., ::-1],
                [cv2.IMWRITE_JPEG_QUALITY, 88])
    return {"quadros": n, "duracao_s": round(n / 30, 1), "composicao_media_s": round(sum(tempos) / len(tempos), 2),
            "composicao_max_s": round(max(tempos), 2), "tempo_total_s": round(time.time() - t0, 1)}


def t_integridade():
    caminhos = ["personagens/heitor/rig_v2", "docs/IDENTIDADE_OFICIAL.md", "skills/"]
    ls = subprocess.run(["git", "ls-files", "-s"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout
    dif = subprocess.run(["git", "status", "--porcelain", "--"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    f1 = subprocess.run([str(RAIZ / ".venv/bin/python"), "codigo/verificar_f1.py"], cwd=RAIZ / "personagens/heitor/rig_v2", capture_output=True, text=True).stdout
    return {"assinatura_rig_identidade_skill": hashlib.sha256(ls.encode()).hexdigest(), "alteracoes_pendentes_nesses_caminhos": dif or "nenhuma",
            "verificar_f1_vistas_ok": f1.count("| OK |")}


if __name__ == "__main__":
    if sys.argv[1:2] == ["previa"]:
        t_video([("tarde_perfil", 0), ("tarde_perfil", 30), ("tarde_perfil", 50), ("tarde_perfil", 95), ("tarde_perfil", 140), ("tarde_perfil", 162),
                 ("tarde_perfil", 185), ("manha_frente", 30), ("manha_frente", 90)]); sys.exit()
    so = sys.argv[1:]; caminho = OUT / "x2_metricas.json"
    if caminho.exists():
        res = json.loads(caminho.read_text())
    for nome, f in (("X2_1_intacto", t_intacto), ("X2_2_paleta", t_paleta), ("X2_3_estampa", t_estampa), ("X2_4_limites", t_limites),
                    ("X2_5_acrescimo", t_acrescimo), ("X2_6_determinismo", t_determinismo), ("X2_7_tempo", t_tempo), ("X2_8_folha", folha),
                    ("X2_8_video", t_video), ("X2_9_integridade", t_integridade)):
        if so and nome not in so:
            continue
        t = time.time(); r = f(); r["_duracao_teste_s"] = round(time.time() - t, 1); res[nome] = r
        print(nome, json.dumps(r, ensure_ascii=False, default=str)[:1500], flush=True)
        caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
