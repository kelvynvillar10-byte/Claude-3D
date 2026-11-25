#!/usr/bin/env python3
"""Cenografia — testes da etapa E0 (fundamentos). Renderiza, MEDE e documenta.

E0-1 cache (hit/miss, invalidação por receita e por código, arquivo corrompido)
E0-2 reprodutibilidade (render de novo, do zero → comparação pixel a pixel)
E0-3 folha de camadas (cada camada, profundidade, composição)
E0-4 vídeo de paralaxe (camadas surgindo + movimento de câmera 2.5D, Heitor rig v2 no plano dele)
E0-5 paralaxe 2.5D × render REAL da câmera movida (erro medido)
E0-6 reiluminação por grupos de luz × render REAL com as luzes alteradas (erro medido)
E0-7 vídeo de iluminação (tarde → anoitecer; luz de efeito azul pulsando no cenário)
E0-8 composição final + medidas de cor (alvos do skill)
E0-9 desempenho (render, composição por quadro, disco, memória)
E0-10 integridade (Heitor rig v2, ID-001..ID-004 e skill sem alteração; paleta do Heitor intacta no quadro)
Saídas: cenografia/testes/e0/ (vídeos, folhas, e0_metricas.json). Placas: .cache/ e _tmp/ (fora do Git).
"""
import hashlib, json, math, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2, skia

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "personagens" / "heitor" / "rig_v2" / "codigo"))
from cenografia import construir as CO                                   # noqa: E402
from cenografia.nucleo import receita as R, cache as C, medidas as MD     # noqa: E402
from cenografia.nucleo.compositor import Placa, _srgb, filmico           # noqa: E402
from cenografia.nucleo.render import ler_exr                             # noqa: E402
import heitor_v2 as HV, animacao as AN                                    # noqa: E402

OUT = RAIZ / "cenografia" / "testes" / "e0"; OUT.mkdir(parents=True, exist_ok=True)
TMP = RAIZ / "_tmp" / "e0"; TMP.mkdir(parents=True, exist_ok=True)
REC = RAIZ / "cenografia" / "receitas" / "e0_calcada.json"
FPS = 30; W, H = 1080, 1920
GRADE = dict(exposicao=-0.9, bloom=0.2, bloom_limiar=1.0, sombra_tinta=0.05, luz_quente=1.0, saturacao=1.12, vinheta=0.32, grao=0.012)
NEVOA = dict(cor="#d9c2a6", densidade=0.006)
CAM_FINAL = dict(tx=0.30, ty=0.05, tz=1.4)
PESOS_NOITE = {"ceu": (0.35, "#8fa6ff"), "sol": (0.12, "#ff8a5c"), "artificial": (2.5, None), "efeito": (6.0, "#5fb8ff")}
ROB = skia.Typeface.MakeFromFile(str(RAIZ / "assets" / "fontes" / "RobotoCondensed-ExtraBold.ttf"))
NUN = skia.Typeface.MakeFromFile(str(RAIZ / "assets" / "fontes" / "Nunito-ExtraBold.ttf"))
res = {}


def suave(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def _texto(rgb, linhas, y0=60, tam=34, cor=0xFFFFFFFF):
    a = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)]).copy()
    s = skia.Surface(a); c = s.getCanvas(); f = skia.Font(NUN, tam)
    for i, t in enumerate(linhas):
        c.drawString(t, 36, y0 + i * (tam + 10), f, skia.Paint(AntiAlias=True, Color=0xCC000000, Style=skia.Paint.kStroke_Style, StrokeWidth=6))
        c.drawString(t, 36, y0 + i * (tam + 10), f, skia.Paint(AntiAlias=True, Color=cor))
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].copy()


def _marca(rgb):
    """Marca d'água oficial "MODO CURIOSO" (Roboto Condensed ExtraBold, 30 px, canto superior direito)."""
    a = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)]).copy()
    s = skia.Surface(a); c = s.getCanvas(); alt = 30; f = skia.Font(ROB, alt / 0.711)
    w1, w2, esp = f.measureText("MODO"), f.measureText("CURIOSO"), f.measureText(" ")
    x = rgb.shape[1] - 40 - (w1 + esp + w2); base = 60 + alt
    c.drawString("MODO", x, base, f, skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(153, 255, 255, 255)))
    c.drawString("CURIOSO", x + w1 + esp, base, f, skia.Paint(AntiAlias=True, Color=0xFFFFC21F))
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].copy()


def heitor(placa, t):
    """Heitor rig v2 OFICIAL, sem alteração: de frente, parado (respiração e piscada), no plano da âncora."""
    pe, topo = placa.m["ancoras"]["heitor_pe"], placa.m["ancoras"]["heitor_topo"]

    def desenhar(cv, proj):
        x, y, _ = proj(*pe); _, yt, _ = proj(*topo); alt = y - yt
        cv.drawOval(skia.Rect.MakeXYWH(x - 0.16 * alt, y - 0.014 * alt, 0.32 * alt, 0.028 * alt),
                    skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(110, 40, 28, 22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.01 * alt)))
        pose = HV.pose_base("frente"); pose["respira"] = math.sin(2 * math.pi * t / 2.8)
        HV.desenhar(cv, x, y, alt, vista="frente", pose=pose, rosto=AN.rosto_com_piscada("neutro", t))
    return desenhar


def video(nome, n, quadro):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / f"{nome}.mp4")]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); tempos = []
    for q in range(n):
        t = time.time(); img = quadro(q, q / FPS); tempos.append(time.time() - t)
        pr.stdin.write(np.ascontiguousarray(img).tobytes())
    pr.stdin.close(); pr.wait()
    return {"quadros": n, "composicao_media_s": round(float(np.mean(tempos)), 3), "composicao_max_s": round(float(np.max(tempos)), 3)}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------ E0-1 / E0-2 cache e reprodutibilidade
def t_cache():
    r = R.carregar(REC); k = R.chave(r)
    t = time.time(); k2, man, hit = CO.construir(REC); dt = time.time() - t
    out = {"chave": k[:16], "segunda_construcao": "HIT" if hit else "MISS", "segunda_construcao_s": round(dt, 2),
           "render_original_por_camada_s": man["tempo_render_s"], "render_original_total_s": man["tempo_total_s"],
           "montagem_cena_s": man["tempo_montagem_s"], "objetos_na_cena": man["objetos"], "resolucao_placa": man["resolucao"],
           "amostras": man["amostras"], "arquivos_no_manifesto": len(man["arquivos"])}
    # invalidação pela receita: 1 cm a mais na posição do banco; outra semente
    r2 = json.loads(json.dumps(r)); r2["componentes"][12]["params"]["x"] += 0.01
    r3 = json.loads(json.dumps(r)); r3["semente"] += 1
    out["chave_muda_com_1cm_no_banco"] = R.chave(r2) != k; out["chave_muda_com_outra_semente"] = R.chave(r3) != k
    # invalidação pelo código: cópia do código com uma linha a mais no gerador → outra chave
    copia = TMP / "codigo_copia"; shutil.rmtree(copia, ignore_errors=True)
    shutil.copytree(R.CENOGRAFIA, copia / "cenografia", ignore=shutil.ignore_patterns("testes", "__pycache__"))
    (copia / "cenografia" / "componentes" / "provisorios_e0.py").write_text((copia / "cenografia" / "componentes" / "provisorios_e0.py").read_text() + "\n# alteração\n")
    orig = R.CENOGRAFIA; R.CENOGRAFIA = copia / "cenografia"; k_cod = R.chave(r); R.CENOGRAFIA = orig
    out["chave_muda_com_mudanca_no_codigo_do_gerador"] = k_cod != k
    # arquivo corrompido → cache inválido (testado numa CÓPIA do cache)
    cc = TMP / "cache_copia"; shutil.rmtree(cc, ignore_errors=True); shutil.copytree(C.pasta(k), cc / k)
    orig_c = C.RAIZ_CACHE; C.RAIZ_CACHE = cc
    antes = C.valido(k); alvo = cc / k / "meio" / "luz_sol.exr"; b = bytearray(alvo.read_bytes()); b[len(b) // 2] ^= 0xFF; alvo.write_bytes(bytes(b))
    depois = C.valido(k); (cc / k / "perto" / "alfa.exr").unlink(); sem_arquivo = C.valido(k); C.RAIZ_CACHE = orig_c
    out.update(cache_valido_antes=antes, cache_valido_com_1_byte_alterado=depois, cache_valido_sem_1_arquivo=sem_arquivo)
    shutil.rmtree(cc, ignore_errors=True); shutil.rmtree(copia, ignore_errors=True)
    return out


def t_repro():
    r = R.carregar(REC); k = R.chave(r); dest = TMP / "repro"
    t = time.time(); CO.construir(REC, destino=dest); dt = time.time() - t
    iguais, difs = 0, {}
    arquivos = sorted(p.relative_to(C.pasta(k)) for p in C.pasta(k).rglob("*.exr"))
    for rel in arquivos:
        a, b = C.pasta(k) / rel, dest / rel
        if sha(a) == sha(b):
            iguais += 1
        else:
            A, B = ler_exr(a), ler_exr(b); fin = np.isfinite(A) & np.isfinite(B)
            difs[str(rel)] = round(float(np.abs(A - B)[fin].max()), 6)
    return {"render_do_zero_s": round(dt, 1), "arquivos_exr": len(arquivos), "identicos_byte_a_byte": iguais,
            "diferentes": difs, "maior_diferenca_linear": max(difs.values()) if difs else 0.0}


# ------------------------------------------------------------------ E0-3 folha de camadas
def t_folha(P):
    x0, y0 = (P.W - W) // 2, (P.H - H) // 2; tw, th = 270, 480
    xadrez = ((np.indices((H, W)).sum(0) // 24) % 2 * 40 + 150).astype(np.uint8)[..., None].repeat(3, 2)
    quadros = []
    for c in P.m["camadas"]:
        L = P.iluminar(c, P.m["pesos_padrao"]); a = P.camadas[c]["alfa"]
        cor = _srgb(filmico(L * 2 ** GRADE["exposicao"] / np.maximum(a[..., None], 1e-4)))
        im = (cor * 255)[y0:y0 + H, x0:x0 + W] * a[y0:y0 + H, x0:x0 + W, None] + xadrez * (1 - a[y0:y0 + H, x0:x0 + W, None])
        cob = round(100 * float(a[y0:y0 + H, x0:x0 + W].mean()), 1)
        quadros.append(_texto(cv2.resize(im.astype(np.uint8), (tw, th)), [c.upper(), f"cobre {cob}%", f"z~{P.camadas[c]['z_med']:.0f} m" if c != "ceu" else "infinito"], 30, 18))
    # profundidade combinada (camada mais próxima visível) em escala log
    Z = np.full((P.H, P.W), 5e3, np.float32)
    for c in P.m["camadas"][1:]:
        Z = np.where(P.camadas[c]["alfa"] > 0.5, np.minimum(Z, P.camadas[c]["prof"]), Z)
    zz = np.clip(np.log(Z[y0:y0 + H, x0:x0 + W]) / np.log(150), 0, 1)
    prof = cv2.applyColorMap((255 - zz * 255).astype(np.uint8), cv2.COLORMAP_MAGMA)[..., ::-1]
    sem = P.compor(grade=GRADE, nevoa=NEVOA)
    com = P.compor(grade=GRADE, nevoa=NEVOA, personagem=heitor(P, 0.0))
    extra = [_texto(cv2.resize(prof, (tw, th)), ["PROFUNDIDADE", "perto = claro"], 30, 18),
             _texto(cv2.resize(sem, (tw, th)), ["COMPOSIÇÃO", "sem personagem"], 30, 18),
             _texto(cv2.resize(com, (tw, th)), ["COMPOSIÇÃO", "+ Heitor rig v2"], 30, 18)]
    linha1 = np.hstack(quadros); linha2 = np.hstack(extra + [np.full((th, tw * 2, 3), 30, np.uint8)])
    folha = np.vstack([linha1, linha2])
    cv2.imwrite(str(OUT / "E0_folha_camadas.png"), folha[..., ::-1])
    cv2.imwrite(str(OUT / "E0_composicao_final.png"), _marca(com)[..., ::-1])
    return com, {"cobertura_pct_por_camada": {c: round(100 * float(P.camadas[c]['alfa'][y0:y0 + H, x0:x0 + W].mean()), 1) for c in P.m["camadas"]},
                 "profundidade_mediana_m": {c: round(P.camadas[c]["z_med"], 1) for c in P.m["camadas"] if c != "ceu"}}


# ------------------------------------------------------------------ E0-4 vídeo de paralaxe
def t_paralaxe(P):
    ordem = P.m["camadas"]; n = int(8.0 * FPS)
    etapas = ["ceu", "longe", "meio", "HEITOR", "perto", "frente"]

    def quadro(q, t):
        if t < 3.0:   # camadas entrando uma a uma
            k = min(len(etapas), int(t / 0.5) + 1); mostrar = etapas[:k]
            cams = [c for c in ordem if c in mostrar]
            img = P.compor(grade=GRADE, nevoa=NEVOA, camadas=cams, personagem=heitor(P, t) if "HEITOR" in mostrar else None, semente_grao=q)
            nomes = {"ceu": "céu", "longe": "longe", "meio": "meio", "HEITOR": "Heitor (rig v2)", "perto": "perto", "frente": "frente"}
            return _marca(_texto(img, ["E0 · camadas", " + ".join(nomes[m] for m in mostrar)], 1760, 30))
        s = suave((t - 3.0) / 4.5)
        cam = {k: v * s for k, v in CAM_FINAL.items()}
        img = P.compor(grade=GRADE, nevoa=NEVOA, cam=cam, personagem=heitor(P, t), semente_grao=q)
        return _marca(_texto(img, ["E0 · paralaxe 2.5D por pixel", f"câmera: {cam['tz']:.2f} m à frente, {cam['tx']:.2f} m à direita"], 1760, 30))
    return video("E0_camadas_e_paralaxe", n, quadro)


# ------------------------------------------------------------------ E0-5 / E0-6 comparação com render real
def _tom_real(pasta, P, grade):
    img = ler_exr(pasta / "imagem.exr")[..., :3] * 2 ** grade.get("exposicao", 0.0)
    d = P._tom(img, grade); d = P._final(d, dict(grade, grao=0.0), 0)
    x0, y0 = (P.W - W) // 2, (P.H - H) // 2
    return d[y0:y0 + H, x0:x0 + W]


def t_real(P, nome, cam=None, pesos=None, luzes=None):
    dest = TMP / f"real_{nome}"; shutil.rmtree(dest, ignore_errors=True)
    t_r = CO.render_verificacao(REC, dest, cam=cam, luzes=luzes)
    g = dict(GRADE, grao=0.0)
    real = _tom_real(dest, P, g); comp = P.compor(pesos=pesos, cam=cam, grade=g)
    met, d = MD.comparar(comp, real)
    mapa = cv2.applyColorMap(np.clip(d * 8, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)[..., ::-1]
    lado = np.hstack([_texto(comp, ["COMPOSITOR 2.5D"], 60, 36), _texto(real, ["RENDER REAL (Blender)"], 60, 36), _texto(mapa, ["DIFERENÇA ×8"], 60, 36)])
    cv2.imwrite(str(OUT / f"E0_{nome}_2.5D_x_real.png"), cv2.resize(lado, (lado.shape[1] // 2, lado.shape[0] // 2))[..., ::-1])
    return dict(met, render_real_s=t_r)


# ------------------------------------------------------------------ E0-7 vídeo de iluminação
def t_iluminacao(P):
    n = int(7.0 * FPS); base = P.m["pesos_padrao"]

    def mix(a, b, k):
        out = {}
        for g in P.grupos:
            wa, ca = (a[g] if isinstance(a[g], tuple) else (a[g], None)); wb, cb = (b[g] if isinstance(b[g], tuple) else (b[g], None))
            out[g] = (wa + (wb - wa) * k, cb or ca)
        return out
    noite = dict(PESOS_NOITE, efeito=(0.0, "#5fb8ff"))

    def quadro(q, t):
        k = suave(t / 4.0); p = mix(base, noite, k)
        if t > 4.6:   # luz de efeito (azul) pulsando: prévia de como um poder vai iluminar o cenário
            pulso = max(0.0, math.sin(2 * math.pi * 3.0 * (t - 4.6))) ** 2 * (0.6 + 0.4 * math.sin(37 * t) ** 2)
            p["efeito"] = (7.0 * pulso, "#5fb8ff")
        neb = dict(NEVOA, cor="#d9c2a6" if k < 0.5 else "#6a6f8c")
        img = P.compor(pesos=p, grade=GRADE, nevoa=neb, personagem=heitor(P, t), semente_grao=q)
        leg = "tarde → anoitecer (só pesos dos grupos de luz)" if t <= 4.6 else "luz de EFEITO azul no cenário (sem novo render)"
        return _marca(_texto(img, ["E0 · reiluminação no compositor", leg], 1760, 30))
    return video("E0_iluminacao", n, quadro)


# ------------------------------------------------------------------ E0-10 integridade
def t_integridade(P, com):
    caminhos = ["personagens/heitor/rig_v2", "docs/IDENTIDADE_OFICIAL.md", "skills/"]
    # o verificador da F1 regera o relatório dele; se o rig está intacto, o arquivo sai idêntico ao versionado
    f1 = subprocess.run([str(RAIZ / ".venv/bin/python"), "codigo/verificar_f1.py"], cwd=RAIZ / "personagens/heitor/rig_v2", capture_output=True, text=True).stdout
    ls = subprocess.run(["git", "ls-files", "-s"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout
    dif = subprocess.run(["git", "status", "--porcelain", "--"] + caminhos, cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    ass = hashlib.sha256(ls.encode()).hexdigest()
    # paleta do Heitor no quadro: Heitor sozinho (mesmo desenho) × quadro composto, nos pixels do personagem não cobertos pela camada da frente
    s = skia.Surface(P.W, P.H); cv = s.getCanvas(); cv.clear(0); heitor(P, 0.0)(cv, lambda x, y, z: P.projetar_ponto(x, y, z))
    so = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
    x0, y0 = (P.W - W) // 2, (P.H - H) // 2; so = so[y0:y0 + H, x0:x0 + W]
    sem_grade = P.compor(grade=dict(GRADE, vinheta=0.0, grao=0.0), nevoa=NEVOA, personagem=heitor(P, 0.0))
    a_fr = P.camadas["frente"]["alfa"][y0:y0 + H, x0:x0 + W] + P.camadas["perto"]["alfa"][y0:y0 + H, x0:x0 + W]
    m = (so[..., 3] == 255) & (a_fr < 0.01)
    dif_px = np.abs(sem_grade.astype(int) - so[..., :3].astype(int)).max(axis=2)[m]
    return {"assinatura_rig_identidade_skill": ass, "alteracoes_pendentes_nesses_caminhos": dif or "nenhuma",
            "verificar_f1_vistas_ok": f1.count("| OK |"),
            "heitor_pixels_medidos": int(m.sum()), "heitor_pixels_identicos_pct": round(100 * float((dif_px == 0).mean()), 2),
            "heitor_maior_diferenca_8bit": int(dif_px.max()) if dif_px.size else None}


if __name__ == "__main__":
    so = sys.argv[1:]
    caminho = OUT / "e0_metricas.json"
    if caminho.exists():
        res = json.loads(caminho.read_text())

    def rodar(nome, f):
        if so and nome not in so:
            return
        t = time.time(); res[nome] = f(); res[nome]["_duracao_teste_s"] = round(time.time() - t, 1)
        print(nome, json.dumps(res[nome], ensure_ascii=False)[:600], flush=True)
        caminho.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    rodar("E0_1_cache", t_cache)
    rodar("E0_2_reprodutibilidade", t_repro)
    t = time.time(); P = Placa(C.pasta(R.chave(R.carregar(REC)))); t_carga = time.time() - t
    estado = {}

    def folha():
        com, m = t_folha(P); estado["com"] = com
        m["medidas_cor_quadro_final"] = MD.quadro(com); m["alvos_skill"] = MD.ALVOS; return m
    rodar("E0_3_folha_e_composicao", folha)
    rodar("E0_4_video_paralaxe", lambda: t_paralaxe(P))
    rodar("E0_5_paralaxe_x_real", lambda: t_real(P, "paralaxe", cam=CAM_FINAL))
    rodar("E0_6_reiluminacao_x_real", lambda: t_real(P, "reiluminacao", pesos=PESOS_NOITE,
                                                         luzes={g: (v[0], v[1]) for g, v in PESOS_NOITE.items()}))
    rodar("E0_7_video_iluminacao", lambda: t_iluminacao(P))

    def desempenho():
        tam = sum(p.stat().st_size for p in C.pasta(R.chave(R.carregar(REC))).rglob("*") if p.is_file())
        t = time.time(); P.compor(grade=GRADE, nevoa=NEVOA, personagem=heitor(P, 0.0), cam=CAM_FINAL); tq = time.time() - t
        return {"placa_disco_MB": round(tam / 2 ** 20, 1), "carregar_placa_s": round(t_carga, 2), "compor_1_quadro_com_camera_e_heitor_s": round(tq, 2)}
    rodar("E0_9_desempenho", desempenho)
    rodar("E0_10_integridade", lambda: t_integridade(P, estado.get("com")))
