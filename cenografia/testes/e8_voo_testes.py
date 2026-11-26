#!/usr/bin/env python3
"""E8 parte 2 — testes do PODER DE VOO (efeitos/poderes/voo.py), com as extensões aprovadas X1 (tom de luz) e X2 (voo).
O rig v2 não é alterado: o Heitor é desenhado pela X2 (que só usa a API do rig).

V1 vídeo: 3 clipes (discreto: paira de frente, manhã · moderado: decola e sai voando de perfil, tarde ·
   extremo: decolagem vertical de costas, noite) + energia por fase, cobertura do rosto/estampa e tempo por quadro
V2 ordem das intensidades no MESMO clipe (sair voando, tarde): pico de energia discreto < moderado < extremo
V3 contatos: o ponto do pé cai no tênis e o da cabeça na cabeça, no desenho real; rastro nasce no pé; sombra × altura
V4 família de cor × camiseta e × eletricidade (ΔE)
V5 segurança: flashes por segundo no vídeo pronto (≤ 3)      V6 proteção: cobertura máxima do rosto e da estampa (≤ 0,35)
V7 paleta do Heitor idêntica ao desenho da X2 sozinho, nos pixels sem efeito na frente
V8 determinismo     V9 regressão (cena de prova sem efeitos idêntica à referência da E7)     V10 integridade
"""
import hashlib, json, math, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2, skia

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "personagens" / "heitor" / "extensoes" / "x1_tom_de_luz"))
from cenografia.nucleo.atmosfera import Atmosfera                          # noqa: E402
from cenografia.nucleo.compositor import Placa                             # noqa: E402
import e0_testes as T0, e1_testes as T1, e6_cena_prova as E6, e8_testes as E8   # noqa: E402
from efeitos.nucleo.base import Params, Mesa, REGISTRO                     # noqa: E402
from efeitos.nucleo import seguranca as SG                                 # noqa: E402
from efeitos.poderes import voo as PV, eletricidade as EL                  # noqa: E402
import tom_de_luz as X1                                                    # noqa: E402
X2 = PV.X2; HV = PV.HV
OUT = RAIZ / "cenografia" / "testes" / "e8_voo"; OUT.mkdir(parents=True, exist_ok=True)
FPS = 30; W, H = 1080, 1920
TOM = {"manha": "manha_frente", "tarde": "tarde_perfil", "noite": "noite_costas"}
CLIPES = [  # nome, intensidade, horário, kw do poder, duração (s), movimento de câmera
    ("voo_discreto", "discreto", "manha", {"modo": "pairar", "origem": (-5.1, 6.0, 0.154), "vista": "frente"}, 4.0, {"tz": (0.0, 0.25)}),
    ("voo_moderado", "moderado", "tarde", {"modo": "sair_voando", "origem": (-5.1, 3.1, 0.154), "direcao": (0, 1, 0), "vista": "perfil"}, 4.2, {"tx": (-0.2, 0.25)}),
    ("voo_extremo", "extremo", "noite", {"modo": "subir", "origem": (-5.1, 6.4, 0.154), "direcao": (0, 1, 0), "vista": "costas"}, 4.0, {"tz": (0.0, 0.3), "ty": (0.0, 0.08)}),
]
res = {}


def placas():
    out = {}
    for hor, nome in TOM.items():
        tom = next(x for x in E6.PLANO["tomadas"] if x["nome"] == nome); out[hor] = E6.placa(tom)[0]
    return out


def criar(clipe, PL, intensidade=None):
    nome, intens, hor, kw, dur, _ = clipe; P = PL[hor]; kw = dict(kw, fundo=E8.fundo(P, E6_HOR[hor]))
    ef = REGISTRO["voo"](Params(intensidade=intensidade or intens, duracao=dur, semente=21), **kw)
    return ef, P, Atmosfera(P, "limpo", 11)


E6_HOR = {"manha": "manha", "tarde": "tarde_dourada", "noite": "noite"}


def cam_de(clipe, t):
    u = min(1.0, t / clipe[4]); s = u * u * (3 - 2 * u)
    return {k: a + (b - a) * s for k, (a, b) in clipe[5].items()}


def desenhista(ef, mesa, ctx_t=None, so_heitor=False):
    def f(cv, proj):
        ctx = mesa.ctx; tl = ef.tl(ctx); e = ef.estado(tl); x, y, alt, _ = ef.tela_personagem(ctx)
        rosto = T0.AN.rosto_com_piscada(e["rosto"], tl) if e["vista"] != "costas" else None
        X2.desenhar(cv, x, y, alt, vista=e["vista"], direcao=e["direcao"], pose=e["pose"], rosto=rosto, inclinacao=e["inclinacao"],
                    vento=ef.vento_tela(ctx), t=tl)
    return f


def preparar(mesa, ef, P, cam, t, k):
    ctx_pc = ef.personagem(None, t - ef.inicio)
    mesa.preparar(P, cam, t, k, ctx_pc)


def quadro(P, A, mesa, ef, clipe, t, k, com_x1=True, cam=None, grade_extra=None, efeitos=True):
    cam = cam_de(clipe, t) if cam is None else cam; hor = clipe[2]
    preparar(mesa, ef, P, cam, t, k)
    g = A.grade(dict(T1.GRADE, exposicao=T1.EXPOSICAO[E6_HOR[hor]], **(grade_extra or {})))
    tom = X1.fazer_tom(ef.personagem(None, t)["pe_mundo"] and {"pe_mundo": ef.personagem(None, t)["pe_mundo"], "altura_m": 1.4},
                       luzes=mesa.luzes(P, cam)) if com_x1 else None
    _, _, _, zp = ef.tela_personagem(mesa.ctx)
    img = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=g, cam=cam, personagem=desenhista(ef, mesa),
                   profundidade_personagem=zp + cam.get("tz", 0.0), efeitos=mesa if efeitos else None,
                   deslocamento_px=mesa.tremida() if efeitos else (0, 0), semente_grao=k, ceu_extra=A.ceu(t), tom_personagem=tom)
    return img


# ------------------------------------------------------------------ V1 / V5 / V6: vídeo + medidas por quadro
def t_video(PL):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "E8_voo.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); out = {}; folha = []; q = 0; lums_total = []
    for clipe in CLIPES:
        ef, P, A = criar(clipe, PL); mesa = E8.MesaMedida([ef], fps=FPS); n = int(clipe[4] * FPS)
        energia = {}; cob = {"rosto": 0.0, "estampa": 0.0}; tempos = []; lums = []
        for k in range(n):
            t = k / FPS; t0 = time.time(); img = quadro(P, A, mesa, ef, clipe, t, q); tempos.append(time.time() - t0)
            fase = ef.fases.em(t)[0] or "—"
            energia.setdefault(fase, []).append(mesa.energia + sum(L["forca"] for L in mesa.luzes(P, cam_de(clipe, t))) / 10)
            if mesa.cobertura:
                cob = {kk: max(cob[kk], mesa.cobertura[kk]) for kk in cob}
            img = T0._texto(img, ["E8 · voo (teste, não é história)", f"voo · {clipe[1]}", f"fase: {fase}"], 1745, 25)
            img = T0._marca(img); pr.stdin.write(np.ascontiguousarray(img).tobytes()); q += 1
            l = SG.luminancia_relativa(cv2.resize(img, (135, 240), interpolation=cv2.INTER_AREA)); lums.append(l); lums_total.append(l)
            if k in (int(n * 0.2), int(n * 0.4), int(n * 0.62), int(n * 0.8)):
                folha.append(T0._texto(cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA), [f"{clipe[1]} {t:.1f}s {fase}"], 20, 17))
        out[clipe[0]] = {"quadros": n, "composicao_media_s": round(float(np.mean(tempos)), 2), "composicao_max_s": round(float(np.max(tempos)), 2),
                         "energia_media_por_fase": {f: round(float(np.mean(v)), 4) for f, v in energia.items()},
                         "energia_pico": round(float(max(max(v) for v in energia.values())), 4),
                         "cobertura_max_rosto_estampa": cob, "flashes": SG.analisar_flashes(lums, FPS)}
        print(clipe[0], json.dumps(out[clipe[0]], ensure_ascii=False)[:600], flush=True)
    pr.stdin.close(); pr.wait()
    cv2.imwrite(str(OUT / "E8_voo_quadros.jpg"), np.vstack([np.hstack(folha[i:i + 4]) for i in range(0, 12, 4)])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    out["_flashes_video_inteiro"] = SG.analisar_flashes(lums_total, FPS)
    return out


# ------------------------------------------------------------------ V2: ordem das intensidades no mesmo clipe
def t_ordem(PL):
    out = {}; clipe = CLIPES[1]
    for intens in ("discreto", "moderado", "extremo"):
        ef, P, A = criar(clipe, PL, intens); mesa = Mesa([ef], fps=FPS); n = int(clipe[4] * FPS); por_fase = {}
        for k in range(n):
            t = k / FPS; cam = cam_de(clipe, t); preparar(mesa, ef, P, cam, t, k)
            if k % 2:
                continue
            e = 0.0
            for onde in ("chao", "atras", "frente"):
                c = mesa.desenhar(P, cam, onde)
                if c is not None:
                    e += float(c["rgba"][..., 3].mean() + c["add"].max(axis=2).mean())
            d = mesa.distorcao(P, cam); e += 0.0 if d is None else float(np.abs(d[0]).mean() + np.abs(d[1]).mean()) / 50
            dx, dy = mesa.tremida(); e += math.hypot(dx, dy) / 500 + sum(L["forca"] for L in mesa.luzes(P, cam)) / 10
            por_fase.setdefault(ef.fases.em(t)[0], []).append(e)
        out[intens] = {"energia_pico": round(max(max(v) for v in por_fase.values()), 4),
                       "energia_media_por_fase": {f: round(float(np.mean(v)), 4) for f, v in por_fase.items()}}
    pk = [out[i]["energia_pico"] for i in ("discreto", "moderado", "extremo")]
    out["discreto_menor_que_moderado_menor_que_extremo"] = bool(pk[0] < pk[1] < pk[2])
    out["obs"] = "energia = cobertura + brilho das camadas + distorção + tremida + luz, no MESMO clipe (decolar e sair voando, tarde)"
    return out


# ------------------------------------------------------------------ V3: contatos no desenho real
CORES_TENIS = {"tenis", "tenis_s", "tenis_faixa", "sola", "contorno"}
CORES_CABECA = {"pele", "pele_s", "cabelo", "cabelo_s", "cabelo_b", "olho", "pupila", "branco_olho", "contorno", "boca", "boca_interna", "lingua", "dentes"}
PAL = {k: np.array([int(v[i:i + 2], 16) for i in (1, 3, 5)]) for k, v in HV.MOD["paleta"].items()}


def _cai_em(rgb, cores, tol=14):
    """O pixel tem uma das cores da lista (≤ tol por canal)? (a faixa do tênis tem a MESMA cor da camiseta)"""
    if any(int(np.abs(rgb.astype(int) - PAL[k]).max()) <= tol for k in cores if k in PAL):
        return True
    c0 = PAL["contorno"].astype(float); x = rgb.astype(float)            # borda suavizada de um traço do rig (mistura com o contorno)
    for k in cores:
        if k in PAL and k != "contorno":
            d = PAL[k] - c0; t = float(np.clip((x - c0) @ d / max(d @ d, 1e-9), 0, 1))
            if np.abs(x - (c0 + t * d)).max() <= 8:
                return True
    return False


def _classe(rgb):
    best, d = "outra", 40
    for k, p in PAL.items():
        dd = int(np.abs(rgb.astype(int) - p).max())
        if dd < d:
            best, d = k, dd
    return best


def t_contatos(PL):
    out = {}
    for clipe in CLIPES:
        ef, P, A = criar(clipe, PL); mesa = Mesa([ef], fps=FPS); n = int(clipe[4] * FPS); reg = {"pe": [], "cabeca": [], "rastro_px": [], "sombra": []}
        for k in range(n):
            t = k / FPS; cam = cam_de(clipe, t); preparar(mesa, ef, P, cam, t, k)
            if k % 6:
                continue
            ctx = mesa.ctx; x, y, alt, _ = ef.tela_personagem(ctx)
            if not (0 < x < P.W and 0 < y < P.H):
                continue
            s = skia.Surface(P.W, P.H); cv = s.getCanvas(); cv.clear(0); desenhista(ef, mesa)(cv, None)
            img = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
            pes = ("pe_d", "pe_e") if clipe[3]["vista"] != "perfil" else ("pe_d",)   # de perfil, o pé de trás pode estar escondido
            for nome, cores, chave in [(p_, CORES_TENIS, "pe") for p_ in pes] + [("cabeca", CORES_CABECA, "cabeca")]:
                px, py, _ = ef.ponto(ctx, nome); ix, iy = int(round(px)), int(round(py))
                if 0 <= ix < P.W and 0 <= iy < P.H:
                    a = img[iy, ix, 3]; c = _classe(img[iy, ix, :3]) if a > 200 else "fora do desenho"
                    ok = a > 200 and _cai_em(img[iy, ix, :3], cores); reg[chave].append(ok)
                    if not ok:
                        reg.setdefault("falhas", []).append((k, nome, c, [int(v) for v in img[iy, ix]]))
            for nome, hh in ef.hist.items():
                if hh and getattr(ef, "hist_novo", {}).get(nome):
                    xa, ya, _, _ = ctx.tela(hh[-1]); px, py, _ = ef.ponto(ctx, nome); reg["rastro_px"].append(math.hypot(xa - px, ya - py))
            ef.ultima_sombra = None; tela_ = __import__("efeitos.nucleo.base", fromlist=["Tela"]).Tela(P.W, P.H); ef._sombra(ctx, tela_)
            if ef.ultima_sombra is not None:
                reg["sombra"].append((round(ef.estado(ef.tl(ctx))["altura_chao"], 2), round(ef.ultima_sombra["alfa"], 3)))
        sb = sorted(set(reg["sombra"]))
        out[clipe[0]] = {"pe_no_tenis_pct": round(100 * float(np.mean(reg["pe"])), 1) if reg["pe"] else None, "amostras_pe": len(reg["pe"]),
                         "cabeca_na_cabeca_pct": round(100 * float(np.mean(reg["cabeca"])), 1) if reg["cabeca"] else None,
                         "rastro_nasce_no_pe_erro_px_max": round(max(reg["rastro_px"]), 2) if reg["rastro_px"] else None,
                         "sombra_some_com_a_altura": bool(all(b[1] <= a[1] + 0.002 for a, b in zip(sb, sb[1:]))) if len(sb) > 1 else None,
                         "sombra_altura_alfa_amostras": sb[:: max(1, len(sb) // 6)], "falhas": reg.get("falhas", [])[:8]}
    return out


# ------------------------------------------------------------------ V4: cor
def t_cor(PL):
    cam = E8._lab("#3d80d8"); out = {"ar": {"cor": PV.AR, "delta_E_camiseta": round(float(np.linalg.norm(E8._lab(PV.AR) - cam)), 1),
                                            "delta_E_eletricidade": round(float(np.linalg.norm(E8._lab(PV.AR) - E8._lab(EL.HALO))), 1)}}
    for clipe in CLIPES:
        ef, P, A = criar(clipe, PL); ef.preparar(__import__("efeitos.nucleo.base", fromlist=["Contexto"]).Contexto(P, {}, 0.0))
        h = "#%02x%02x%02x" % tuple(int(v * 255) for v in ef.cor_p)
        out[f"poeira_{clipe[2]}"] = {"cor": h, "delta_E_camiseta": round(float(np.linalg.norm(E8._lab(h) - cam)), 1)}
    out["regra"] = "ΔE > 25: cor bem diferente (a partir de ~10 já se distingue)"
    return out


# ------------------------------------------------------------------ V7 / V8
def t_heitor_det(PL):
    out = {}; clipe = CLIPES[0]; ef, P, A = criar(clipe, PL); mesa = E8.MesaMedida([ef], fps=FPS); k = int(2.0 * FPS)
    for kk in range(k):
        preparar(mesa, ef, P, {}, kk / FPS, kk)
    t = k / FPS; preparar(mesa, ef, P, {}, t, k)
    sem = P.compor(pesos=A.pesos(), nevoa=A.nevoa(), grade=dict(T1.GRADE, exposicao=T1.EXPOSICAO["manha"], vinheta=0.0, grao=0.0),
                   personagem=desenhista(ef, mesa), profundidade_personagem=ef.tela_personagem(mesa.ctx)[3], efeitos=mesa)
    s = skia.Surface(P.W, P.H); cv = s.getCanvas(); cv.clear(0); desenhista(ef, mesa)(cv, None)
    so = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
    x0, y0 = (P.W - W) // 2, (P.H - H) // 2; so = so[y0:y0 + H, x0:x0 + W]; occ = P.ultima_oclusao[y0:y0 + H, x0:x0 + W]
    fr = mesa.ultima_frente; cobf = (fr["rgba"][..., 3] + fr["add"].max(axis=2))[y0:y0 + H, x0:x0 + W] if fr is not None else np.zeros((H, W))
    m = (so[..., 3] == 255) & (occ < 0.01) & (cobf < 0.004); cob = (so[..., 3] == 255) & (cobf >= 0.004)
    dif = np.abs(sem.astype(int) - so[..., :3].astype(int)).max(axis=2)[m]
    out["paleta_heitor"] = {"pixels_sem_efeito_na_frente": int(m.sum()), "identicos_pct": round(100 * float((dif == 0).mean()), 2),
                            "pixels_do_heitor_com_ar_na_frente": int(cob.sum()), "obs": "X1 desligada aqui: compara o desenho da X2 sozinho com o quadro"}
    hs = []
    for _ in range(2):
        ef, P, A = criar(CLIPES[2], PL); mesa = Mesa([ef], fps=FPS); kq = int(1.9 * FPS)
        for kk in range(kq):
            preparar(mesa, ef, P, cam_de(CLIPES[2], kk / FPS), kk / FPS, kk)
        hs.append(hashlib.sha256(quadro(P, A, mesa, ef, CLIPES[2], kq / FPS, kq).tobytes()).hexdigest())
    out["mesmo_quadro_duas_vezes_identico"] = hs[0] == hs[1]
    return out


def t_regressao():
    ref = json.loads((RAIZ / "cenografia" / "testes" / "e7" / "regressao_ref.json").read_text()); out = {}
    for tom in E6.PLANO["tomadas"]:
        P = Placa(ref[tom["nome"]]["placa"]); A = Atmosfera(P, tom["clima"], 11); img, _ = E6.quadro(P, A, tom, 2.0, 60)
        out[tom["nome"]] = hashlib.sha256(img.tobytes()).hexdigest() == ref[tom["nome"]]["sha256"]
    return {"cena_de_prova_identica_a_referencia": out}


def previa(PL, saida):
    ims = []
    for clipe in CLIPES:
        ef, P, A = criar(clipe, PL); mesa = Mesa([ef], fps=FPS); n = int(clipe[4] * FPS)
        alvos = sorted({int(n * f) for f in (0.15, 0.3, 0.45, 0.62, 0.72, 0.85)})
        for k in range(max(alvos) + 1):
            if k in alvos:
                img = quadro(P, A, mesa, ef, clipe, k / FPS, k)
                ims.append(T0._texto(cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA), [f"{clipe[0]} {k / FPS:.2f}s {ef.fases.em(k / FPS)[0]}"], 20, 16))
            else:
                preparar(mesa, ef, P, cam_de(clipe, k / FPS), k / FPS, k)
    cv2.imwrite(saida, np.vstack([np.hstack(ims[i:i + 6]) for i in range(0, len(ims), 6)])[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])


if __name__ == "__main__":
    so = sys.argv[1:]
    if so and so[0] == "previa":
        previa(placas(), so[1]); sys.exit(0)
    caminho = OUT / "e8_voo_metricas.json"
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
    rodar("V4_cor", t_cor, PL)
    rodar("V3_contatos", t_contatos, PL)
    rodar("V2_ordem", t_ordem, PL)
    rodar("V7_V8_heitor_det", t_heitor_det, PL)
    rodar("V9_regressao", t_regressao)
    rodar("V1_video", t_video, PL)
    rodar("V10_integridade", E8.t_integridade)
