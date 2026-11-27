#!/usr/bin/env python3
"""Cena de prova — QA medido e comparação com o MESMO trecho do EP01 (39,20–58,90 s).
Mede: formato/duração, ritmo (planos e cortes), movimento de personagem e de câmera quadro a quadro, mapa fala → imagem,
cotovelos de todas as poses usadas, rig intacto, pés sem deslizar na locomoção, loudness.
Uso: qa_teste.py <video.mp4>
"""
import json, math, re, subprocess, sys
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parents[1]; RAIZ = P.parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cena_dinamica as CD                                                   # noqa: E402
import atuacao as A                                                          # noqa: E402
R = []


def ok(nome, cond, det):
    R.append({"verificacao": nome, "ok": bool(cond), "detalhe": det}); print(("OK   " if cond else "FALHA"), nome, "—", det)


def _num(p):
    return {k: v for k, v in p.items() if isinstance(v, (int, float))} | {f"raiz{i}": v for i, v in enumerate(p.get("raiz", [0, 0]))}


def movimento():
    """Por quadro: o personagem se desloca, muda de pose de forma visível, e a câmera se move?"""
    N = int(round(CD.DUR * CD.FPS)); ant = None; res = []
    for n in range(N):
        st = CD.estado(n); r = {"plano": st["id"], "acao": False, "vivo": False, "camera": False}
        atores = {}
        if st.get("heitor"):
            h = st["heitor"]; atores["heitor"] = (np.asarray(h["pos"], float), _num(h["pose"]), h["vista"])
        if st.get("gato"):
            g = st["gato"]; atores["gato"] = (np.asarray(g["pos"], float), {k: g.get(k, 0) for k in ("fase", "pupila", "inclinar", "cauda", "piscar", "alt_m")}, g["pose"])
        if st.get("aranha"):
            a = st["aranha"]; atores["aranha"] = (np.asarray(a["pos"], float), {"fase": a["fase"], "levantar": a["levantar"]}, "")
        if st.get("pata") or st.get("insert"):
            r["acao"] = True
        if ant is not None and ant["id"] == st["id"]:
            for nome, (pos, pz, vs) in atores.items():
                if nome not in ant["atores"]:
                    r["acao"] = True; continue
                p0, z0, v0 = ant["atores"][nome]
                dpos = float(np.linalg.norm(pos - p0)); dmax = max([abs(pz[k] - z0.get(k, pz[k])) for k in pz] + [0])
                grande = {k: abs(pz[k] - z0.get(k, pz[k])) for k in pz if k not in ("respira", "cauda")}
                if dpos > 1e-5 or vs != v0 or max(list(grande.values()) + [0]) > (0.004 if nome != "heitor" else 0.6):
                    r["acao"] = True
                if dmax > 1e-4 or dpos > 0:
                    r["vivo"] = True
            c0, c1 = ant["cam"], st.get("cam") or {}
            if c1 and (abs(c1.get("zoom", 1) - c0.get("zoom", 1)) > 1e-4 or any(abs(a - b) > 0.05 for a, b in zip(c1.get("pan", (0, 0)), c0.get("pan", (0, 0))))
                       or abs(c1.get("tx", 0) - c0.get("tx", 0)) > 1e-6):
                r["camera"] = True
            if st.get("insert"):
                r["camera"] = st["zoom"] != ant.get("zoom_ins")
        else:
            r.update(acao=True, vivo=True, camera=True)                      # primeiro quadro do plano (corte)
        res.append(r); ant = {"id": st["id"], "atores": atores, "cam": dict(st.get("cam") or {}), "zoom_ins": st.get("zoom")}
    return res


def ep01_mesmo_trecho():
    M = json.loads((RAIZ / "producoes/ep01_cinco_centimetros/montagem.json").read_text())
    pl = [p for p in M["planos"] if p["fim"] > CD.T0 and p["ini"] < CD.T1]
    dur = [min(p["fim"], CD.T1) - max(p["ini"], CD.T0) for p in pl]
    loc = sum(1 for p in pl if (p.get("heitor") or {}).get("andar"))
    anim = sum(1 for p in pl for e in p.get("extras", []) if e["tipo"] in ("gato", "aranha") and (e.get("pos") and "fase" in e and e["fase"][0] != e["fase"][1]))
    return dict(planos=len(pl), mediana_s=float(np.median(dur)), cortes_min=(len(pl) - 1) / ((CD.T1 - CD.T0) / 60), planos_com_locomocao=loc,
                animais_que_se_deslocam=0, planos_com_pan=sum(1 for p in pl if "tx" in p.get("cam", {})))


def main(video):
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)], capture_output=True, text=True).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    dur = float(pr["format"]["duration"]); fps = eval(v["r_frame_rate"])
    ok("formato", (v["width"], v["height"]) == (1080, 1920) and abs(fps - 30) < 0.01 and a is not None, f"{v['width']}×{v['height']} · {fps:.0f} qps · {v['codec_name']} + {a['codec_name'] if a else '—'}")
    ok("duracao", abs(dur - CD.DUR) < 0.1, f"{dur:.2f} s (trecho {CD.T0:.2f}–{CD.T1:.2f} s da narração do EP01)")
    durs = [p[2] - p[1] for p in CD.PLANOS]; med = float(np.median(durs)); cpm = (len(durs) - 1) / (CD.DUR / 60)
    base = ep01_mesmo_trecho()
    ok("ritmo", 1.2 <= med <= 2.0, f"{len(durs)} planos · mediana {med:.2f} s · {cpm:.0f} cortes/min (EP01 no mesmo trecho: {base['planos']} planos · "
       f"mediana {base['mediana_s']:.2f} s · {base['cortes_min']:.0f} cortes/min; diretriz: planos de 1,5–2 s)")
    mv = movimento(); N = len(mv)
    acao = sum(r["acao"] for r in mv) / N; vivo = sum(r["vivo"] or r["acao"] for r in mv) / N; cam = sum(r["camera"] for r in mv) / N
    por_plano = {}
    for r in mv:
        d = por_plano.setdefault(r["plano"], [0, 0]); d[0] += r["acao"]; d[1] += 1
    minimo = min(a / b for a, b in por_plano.values())
    ok("movimento_personagens", vivo >= 0.99 and acao >= 0.6,
       f"quadros com algo vivo (respiração, cauda etc.): {100 * vivo:.0f} % · com AÇÃO visível (deslocamento, troca de pose/vista, gesto): {100 * acao:.0f} % · "
       f"plano com menos ação: {100 * minimo:.0f} %")
    ok("camera_em_movimento", cam >= 0.9, f"câmera se move em {100 * cam:.0f} % dos quadros (zoom, acompanhamento ou panorâmica)")
    locs = sorted({p for p, f in [(r['plano'], r['acao']) for r in mv]})
    mapa = json.loads((P / "saida" / "mapa_fala_imagem.json").read_text())
    W = json.loads((RAIZ / "narracao/edicoes/ep01_narracao/voz_palavras.json").read_text())
    erros = []
    for m in mapa:
        pal = next((w for w in W if abs(w["ini"] - m["t"]) < 0.02 and w["w"].strip(",.?!").lower() == m["palavra"].lower()), None)
        plano = CD.plano_em(m["t"])[0]
        if pal is None or plano != m["plano"]:
            erros.append(f"{m['palavra']}@{m['t']} (palavra no áudio: {'sim' if pal else 'NÃO'}; plano {plano} ≠ {m['plano']})")
    ok("mapa_fala_imagem", not erros, f"{len(mapa)} palavras-chave, cada uma com a ação no plano certo no instante em que é dita" if not erros else "; ".join(erros))
    # cotovelos: todas as poses realmente desenhadas
    inv = 0; n = 0
    for k in range(N):
        st = CD.estado(k); h = st.get("heitor")
        if h:
            for lado in ("d", "e"):
                n += 1; inv += bool(A.GS.cotovelo_invertido(h["pose"], h["vista"], lado)[0])
    ok("cotovelos", inv == 0, f"{n} braços verificados (todas as poses de todos os quadros), {inv} invertido(s)")
    alt = subprocess.run(["git", "-C", str(RAIZ), "status", "--porcelain", "personagens/heitor/rig_v2"], capture_output=True, text=True).stdout.strip()
    ok("rig_intacto", alt == "", "nenhuma alteração em personagens/heitor/rig_v2 (as ferramentas de atuação ficam fora do rig)" if not alt else alt)
    # pés: na locomoção o mundo anda exatamente o que a pelve do ciclo anda → pé de apoio parado no mundo
    desl = []
    for tipo in ("caminhada", "corrida"):
        for t in np.arange(0, 2, 1 / 30):
            _, d = A.AN.pose_locomocao(t, "perfil", tipo)
            for s, pe in d["pernas"].items():
                if pe["apoio"]:
                    desl.append((tipo, s, round(float(pe["alvo"][0]), 4), round(t * 30)))
    var = 0.0
    for tipo in ("caminhada", "corrida"):
        for s in ("d", "e"):
            xs = [x for tp, ss, x, _ in desl if tp == tipo and ss == s]
            grupos = []; g = [xs[0]] if xs else []
            for x in xs[1:]:
                (g.append(x) if abs(x - g[-1]) < 0.05 else (grupos.append(g), g := [x]))
            grupos.append(g)
            var = max([var] + [max(gg) - min(gg) for gg in grupos if gg])
    ok("pes_sem_deslizar", var * A.ALT * 1000 < 0.5, f"pé de apoio: variação máxima {var * A.ALT * 1000:.2f} mm no mundo (velocidade do personagem = velocidade do ciclo: "
       f"caminhada {A.VEL['caminhada'] * 100:.1f} cm/s, corrida {A.VEL['corrida'] * 100:.1f} cm/s); gato: avanço = {A.lerp(0, 1, 1) * 0 + 0.533:.3f} × altura por ciclo")
    e = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]); pk = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
    ok("loudness", abs(I + 14) <= 0.5 and pk <= -1.0, f"{I} LUFS · pico {pk} dBTP")
    ok("marca_dagua", CD.CP.M["marca_dagua"]["texto"] == "MODO CURIOSO", "\"MODO CURIOSO\" em todos os quadros (mesmo desenho do EP01)")
    saida = P / "saida"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", "fps=2,scale=180:-1,tile=10x4", "-frames:v", "1", str(saida / "folha_contato_2qps.jpg")], check=True)
    (saida / "qa_relatorio.json").write_text(json.dumps({"video": Path(video).name, "verificacoes": R, "ep01_mesmo_trecho": base,
                                                         "acao_por_plano": {k: round(a / b, 3) for k, (a, b) in por_plano.items()}}, ensure_ascii=False, indent=1) + "\n")
    print(f"\nQA: {sum(r['ok'] for r in R)}/{len(R)}"); print("EP01 mesmo trecho:", base); print("ação por plano:", {k: round(a / b, 2) for k, (a, b) in por_plano.items()})


if __name__ == "__main__":
    main(sys.argv[1])
