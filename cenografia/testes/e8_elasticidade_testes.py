#!/usr/bin/env python3
"""E8 parte 4 — testes do PODER DE ELASTICIDADE (efeitos/poderes/elasticidade.py), com as extensões aprovadas X1 e X4.
O rig v2 não é alterado.

L1 vídeo: 3 clipes (discreto: toca a placa, de frente, manhã · moderado: pega a fruta na prateleira, de perfil, tarde ·
   extremo: pernas de pau e pisão, de costas, noite) + energia por fase, cobertura, tempo
L2 ordem das intensidades no MESMO clipe (pegar)   L3 contatos: a palma chega ao alvo (px); pés no chão nas pernas de pau
L4 família de cor (ΔE)   L5 segurança (flashes)   L6 proteção   L7 paleta do Heitor   L8 determinismo · L9 regressão · L10 integridade
"""
import hashlib, json, math, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2, skia

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "personagens" / "heitor" / "extensoes" / "x1_tom_de_luz"))
from cenografia.nucleo.atmosfera import Atmosfera                          # noqa: E402
import e0_testes as T0, e1_testes as T1, e6_cena_prova as E6, e8_testes as E8   # noqa: E402
import e8_voo_testes as EV                                                 # noqa: E402
from efeitos.nucleo.base import Params, Mesa, REGISTRO                     # noqa: E402
from efeitos.nucleo import seguranca as SG                                 # noqa: E402
from efeitos.poderes import elasticidade as PE, aranha as PA, eletricidade as EL, voo as PV   # noqa: E402
import tom_de_luz as X1                                                    # noqa: E402
OUT = RAIZ / "cenografia" / "testes" / "e8_elasticidade"; OUT.mkdir(parents=True, exist_ok=True)
FPS = 30; W, H = 1080, 1920
PAREDE_NOITE = {"nome": "x3_parede_noite", "vista": "costas", "horario": "noite", "clima": "limpo",
                "camera": {"pos": [1.0, 6.2, 2.0], "alvo": [-6.0, 6.2, 2.7], "lente_mm": 30}}
HOR = {"manha": "manha", "tarde": "tarde_dourada", "noite": "noite"}
res = {}


def _mundo(P, u, v, z):
    I = P.m["intrinsecos"]; pos, dr, dx, cima = (np.asarray(I[k], float) for k in ("pos", "dir", "dir_x", "cima"))
    return pos + z * (dr + (u - P.cx) / P.f * dx - (v - P.cy) / P.f * cima)


def placas():
    out = {}
    for hor, nome in (("manha", "manha_frente"), ("tarde", "tarde_perfil"), ("noite", "noite_costas")):
        out[hor] = E6.placa(next(x for x in E6.PLANO["tomadas"] if x["nome"] == nome))[0]
    return out


def clipes(PL):
    return [
        ("elasticidade_discreto", "discreto", "manha", {"modo": "tocar", "origem": (-5.1, 6.0, 0.154), "alvo": (-4.15, 8.96, 2.25)}, {"tz": (0.0, 0.2)}),
        ("elasticidade_moderado", "moderado", "tarde", {"modo": "pegar", "origem": (-5.1, 2.7, 0.154), "alvo": (-6.9, 4.4, 1.45)}, {"tx": (-0.15, 0.1)}),
        ("elasticidade_extremo", "extremo", "noite", {"modo": "pernas_de_pau", "origem": (-5.1, 5.6, 0.154)}, {"tz": (0.0, 0.25)}),
    ]


def criar(clipe, PL, intensidade=None):
    nome, intens, hor, kw, _ = clipe; P = PL[hor]
    ef = REGISTRO["elasticidade"](Params(intensidade=intensidade or intens, semente=41), **kw)
    return ef, P, Atmosfera(P, "limpo", 11)


def cam_de(clipe, ef, t):
    u = min(1.0, t / ef.fases.duracao); s = u * u * (3 - 2 * u)
    return {k: a + (b - a) * s for k, (a, b) in clipe[4].items()}


def preparar(mesa, ef, P, cam, t, k):
    from efeitos.nucleo.base import Contexto
    ctx = Contexto(P, cam, t, k, FPS); mesa.preparar(P, cam, t, k, ef.personagem(ctx))


def desenhista(ef, mesa):
    def f(cv, proj):
        ef.desenhar_heitor(mesa.ctx, cv)
    return f


def quadro(P, A, mesa, ef, clipe, t, k, com_x1=True, cam=None):
    cam = cam_de(clipe, ef, t) if cam is None else cam; hor = clipe[2]
    preparar(mesa, ef, P, cam, t, k)
    tom = X1.fazer_tom({"pe_mundo": mesa.ctx.personagem["pe_mundo"], "altura_m": 1.4}, luzes=mesa.luzes(P, cam)) if com_x1 else None
    zp = ef.estado(mesa.ctx)["z"]
    return P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[HOR[hor]])), cam=cam,
                    personagem=desenhista(ef, mesa), profundidade_personagem=zp + cam.get("tz", 0.0), efeitos=mesa,
                    deslocamento_px=mesa.tremida(), semente_grao=k, ceu_extra=A.ceu(t), tom_personagem=tom)


def t_video(PL):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "E8_elasticidade.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); out = {}; folha = []; q = 0; lums_total = []
    for clipe in clipes(PL):
        ef, P, A = criar(clipe, PL); mesa = E8.MesaMedida([ef], fps=FPS); n = int(ef.fases.duracao * FPS)
        energia = {}; cob = {"rosto": 0.0, "estampa": 0.0}; tempos = []; lums = []
        for k in range(n):
            t = k / FPS; t0 = time.time(); img = quadro(P, A, mesa, ef, clipe, t, q); tempos.append(time.time() - t0)
            fase = ef.fases.em(t)[0] or "—"; energia.setdefault(fase, []).append(mesa.energia)
            if mesa.cobertura:
                cob = {kk: max(cob[kk], mesa.cobertura[kk]) for kk in cob}
            img = T0._marca(T0._texto(img, ["E8 · elasticidade (teste, não é história)", f"elasticidade · {clipe[1]}", f"fase: {fase}"], 1745, 25))
            pr.stdin.write(np.ascontiguousarray(img).tobytes()); q += 1
            l = SG.luminancia_relativa(cv2.resize(img, (135, 240), interpolation=cv2.INTER_AREA)); lums.append(l); lums_total.append(l)
            if k in (int(n * 0.25), int(n * 0.45), int(n * 0.62), int(n * 0.85)):
                folha.append(T0._texto(cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA), [f"{clipe[1]} {t:.1f}s {fase}"], 20, 17))
        out[clipe[0]] = {"quadros": n, "composicao_media_s": round(float(np.mean(tempos)), 2), "composicao_max_s": round(float(np.max(tempos)), 2),
                         "energia_media_por_fase": {f: round(float(np.mean(v)), 4) for f, v in energia.items()},
                         "energia_pico": round(float(max(max(v) for v in energia.values())), 4),
                         "cobertura_max_rosto_estampa": cob, "flashes": SG.analisar_flashes(lums, FPS)}
        print(clipe[0], json.dumps(out[clipe[0]], ensure_ascii=False)[:600], flush=True)
    pr.stdin.close(); pr.wait()
    cv2.imwrite(str(OUT / "E8_elasticidade_quadros.jpg"), np.vstack([np.hstack(folha[i:i + 4]) for i in range(0, 12, 4)])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    out["_flashes_video_inteiro"] = SG.analisar_flashes(lums_total, FPS)
    return out


def t_ordem(PL):
    out = {}; clipe = clipes(PL)[1]   # pegar (tarde)
    for intens in ("discreto", "moderado", "extremo"):
        ef, P, A = criar(clipe, PL, intens); mesa = Mesa([ef], fps=FPS); n = int(ef.fases.duracao * FPS); por_fase = {}
        for k in range(0, n, 2):
            t = k / FPS; cam = cam_de(clipe, ef, t); preparar(mesa, ef, P, cam, t, k); e = 0.0
            for onde in ("chao", "atras", "frente"):
                c = mesa.desenhar(P, cam, onde)
                if c is not None:
                    e += float(c["rgba"][..., 3].mean() + c["add"].max(axis=2).mean())
            dx, dy = mesa.tremida(); e += math.hypot(dx, dy) / 500
            por_fase.setdefault(ef.fases.em(t)[0], []).append(e)
        out[intens] = {"energia_pico": round(max(max(v) for v in por_fase.values()), 4),
                       "energia_media_por_fase": {f: round(float(np.mean(v)), 4) for f, v in por_fase.items()}}
    pk = [out[i]["energia_pico"] for i in ("discreto", "moderado", "extremo")]
    out["discreto_menor_que_moderado_menor_que_extremo"] = bool(pk[0] < pk[1] < pk[2])
    return out


def t_contatos(PL):
    """Alcance: a palma chega ao alvo (px) no ápice e cai sobre pele no desenho; pernas de pau: a sola fica no chão (px)."""
    out = {}
    for clipe in clipes(PL):
        ef, P, A = criar(clipe, PL); mesa = Mesa([ef], fps=FPS); n = int(ef.fases.duracao * FPS); erro = []; pele = []; sola = []; vib = []
        for k in range(n):
            t = k / FPS; cam = cam_de(clipe, ef, t); preparar(mesa, ef, P, cam, t, k)
            if k % 3:
                continue
            e = ef.estado(mesa.ctx)
            s = skia.Surface(P.W, P.H); cv = s.getCanvas(); cv.clear(0); ef.desenhar_heitor(mesa.ctx, cv)
            img = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
            if ef.modo in ("tocar", "pegar"):
                if ef.fases.em(t)[0] == "uso":                     # esticado: contato com a mola em repouso (k = 1) e a vibração em volta dele
                    x0, y0, alt, _ = ef._base(mesa.ctx); u = alt / 4.0; ax, ay, _ = e["alvo_tela"]
                    p1, _, _ = PE.X4.alcance(PE.HV.pose_base(ef.vista), ef.vista, e["lado"], ((ax - x0) / u, (ay - y0) / u), k=1.0)
                    q = PE.X3.palma(p1, ef.vista, e["lado"]); erro.append(math.hypot(x0 + q[0] * u - ax, y0 + q[1] * u - ay))
                    vib.append(math.hypot(e["palma"][0] - ax, e["palma"][1] - ay))
                ix, iy = int(round(e["palma"][0])), int(round(e["palma"][1]))
                if 0 <= ix < P.W and 0 <= iy < P.H:
                    pele.append(bool(img[iy, ix, 3] > 200 and _na_pele(img[iy, ix, :3])))
            else:
                col = img[:, int(e["x"]) - int(e["alt"] * 0.2):int(e["x"]) + int(e["alt"] * 0.2), 3]
                ys = np.nonzero(col.max(axis=1) > 127)[0]; sola.append(float(ys.max() - e["y"]) if len(ys) else None)
        r = {}
        if erro:
            r["palma_no_alvo_com_mola_em_repouso_erro_px_max"] = round(max(erro), 3); r["amostras"] = len(erro)
            r["vibracao_da_mola_em_volta_do_alvo_px_max"] = round(max(vib), 1)
        if pele:
            r["palma_sobre_pele_pct"] = round(100 * float(np.mean(pele)), 1)
        if sola:
            v = [x for x in sola if x is not None]; r["sola_em_relacao_ao_chao_px_min_max"] = (round(min(v), 2), round(max(v), 2))
        out[clipe[0]] = r
    return out


def _na_pele(rgb):
    """Pele (também a linha da palma: mistura pele → sombra da pele) ou o contorno dela."""
    if EV._cai_em(rgb, {"pele", "pele_s", "contorno"}):
        return True
    a, b = EV.PAL["pele"].astype(float), EV.PAL["pele_s"].astype(float); d = b - a; x = rgb.astype(float)
    t = float(np.clip((x - a) @ d / (d @ d), 0, 1)); return bool(np.abs(x - (a + t * d)).max() <= 8)


def t_cor():
    cam = E8._lab("#3d80d8"); l = E8._lab(PE.MOLA)
    return {"mola": PE.MOLA, "delta_E_camiseta": round(float(np.linalg.norm(l - cam)), 1), "delta_E_pele": round(float(np.linalg.norm(l - E8._lab("#ffd9c2"))), 1),
            "delta_E_eletricidade": round(float(np.linalg.norm(l - E8._lab(EL.HALO))), 1), "delta_E_ar_do_voo": round(float(np.linalg.norm(l - E8._lab(PV.AR))), 1),
            "delta_E_seda_da_aranha": round(float(np.linalg.norm(l - E8._lab(PA.SEDA))), 1), "delta_E_curioso_da_estampa": round(float(np.linalg.norm(l - E8._lab("#ffc21f"))), 1)}


def t_heitor_det(PL):
    out = {}; clipe = clipes(PL)[0]; ef, P, A = criar(clipe, PL); mesa = E8.MesaMedida([ef], fps=FPS); k = int(1.2 * FPS)
    for kk in range(k + 1):
        preparar(mesa, ef, P, {}, kk / FPS, kk)
    sem = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=dict(T1.GRADE, exposicao=T1.EXPOSICAO["manha"], vinheta=0.0, grao=0.0),
                   personagem=desenhista(ef, mesa), profundidade_personagem=ef.estado(mesa.ctx)["z"], efeitos=mesa)
    s = skia.Surface(P.W, P.H); cv = s.getCanvas(); cv.clear(0); ef.desenhar_heitor(mesa.ctx, cv)
    so = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
    x0, y0 = (P.W - W) // 2, (P.H - H) // 2; so = so[y0:y0 + H, x0:x0 + W]; occ = P.ultima_oclusao[y0:y0 + H, x0:x0 + W]
    fr = mesa.ultima_frente; cobf = (fr["rgba"][..., 3] + fr["add"].max(axis=2))[y0:y0 + H, x0:x0 + W] if fr is not None else np.zeros((H, W))
    m = (so[..., 3] == 255) & (occ < 0.01) & (cobf < 0.004); dif = np.abs(sem.astype(int) - so[..., :3].astype(int)).max(axis=2)[m]
    out["paleta_heitor"] = {"pixels_sem_efeito_na_frente": int(m.sum()), "identicos_pct": round(100 * float((dif == 0).mean()), 2),
                            "diferenca_max_8bit": int(dif.max()) if dif.size else 0, "pixels_do_heitor_com_efeito_na_frente": int(((so[..., 3] == 255) & (cobf >= 0.004)).sum())}
    hs = []
    for _ in range(2):
        cl = clipes(PL)[2]; ef, P, A = criar(cl, PL); mesa = Mesa([ef], fps=FPS); kq = int(2.2 * FPS)
        for kk in range(kq):
            preparar(mesa, ef, P, cam_de(cl, ef, kk / FPS), kk / FPS, kk)
        hs.append(hashlib.sha256(quadro(P, A, mesa, ef, cl, kq / FPS, kq).tobytes()).hexdigest())
    out["mesmo_quadro_duas_vezes_identico"] = hs[0] == hs[1]
    return out


def previa(PL, saida):
    ims = []
    for clipe in clipes(PL):
        ef, P, A = criar(clipe, PL); mesa = Mesa([ef], fps=FPS); n = int(ef.fases.duracao * FPS)
        alvos = sorted({int(n * f) for f in (0.12, 0.25, 0.38, 0.5, 0.62, 0.8)})
        for k in range(max(alvos) + 1):
            if k in alvos:
                img = quadro(P, A, mesa, ef, clipe, k / FPS, k)
                ims.append(T0._texto(cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA), [f"{clipe[0]} {k / FPS:.2f}s {ef.fases.em(k / FPS)[0]}"], 20, 16))
            else:
                preparar(mesa, ef, P, cam_de(clipe, ef, k / FPS), k / FPS, k)
    cv2.imwrite(saida, np.vstack([np.hstack(ims[i:i + 6]) for i in range(0, len(ims), 6)])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])


if __name__ == "__main__":
    so = sys.argv[1:]
    if so and so[0] == "previa":
        previa(placas(), so[1]); sys.exit(0)
    caminho = OUT / "e8_elasticidade_metricas.json"
    if caminho.exists():
        res = json.loads(caminho.read_text())
    PL = placas()

    def rodar(nome, f, *a):
        if so and nome not in so:
            return
        t = time.time(); res[nome] = f(*a)
        if isinstance(res[nome], dict):
            res[nome]["_duracao_teste_s"] = round(time.time() - t, 1)
        print(nome, json.dumps(res[nome], ensure_ascii=False, default=str)[:1200], flush=True)
        caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    rodar("L4_cor", t_cor)
    rodar("L3_contatos", t_contatos, PL)
    rodar("L2_ordem", t_ordem, PL)
    rodar("L7_L8_heitor_det", t_heitor_det, PL)
    rodar("L9_regressao", EV.t_regressao)
    rodar("L1_video", t_video, PL)
    rodar("L10_integridade", E8.t_integridade)
