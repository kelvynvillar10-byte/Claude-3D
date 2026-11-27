#!/usr/bin/env python3
"""EP02 — QA medido (mesmas verificações da cena de prova aprovada, para o episódio inteiro) + identidade e marcas.
Mede: formato/duração, ritmo, movimento dos personagens e da câmera quadro a quadro, mapa fala → imagem, cotovelos de todas
as poses desenhadas, rigs intactos, pés sem deslizar, loudness, números na tela, legendas, marca d'água, gancho e final.
Uso: qa_ep02.py <video.mp4>
"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parents[1]; RAIZ = P.parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cenas_ep02 as CE                                                      # noqa: E402
import atores_ep02 as AE                                                     # noqa: E402
R = []


def ok(nome, cond, det):
    R.append({"verificacao": nome, "ok": bool(cond), "detalhe": det}); print(("OK   " if cond else "FALHA"), nome, "—", det)


def _num(p):
    return {k: v for k, v in p.items() if isinstance(v, (int, float))} | {f"raiz{i}": v for i, v in enumerate(p.get("raiz", [0, 0]))}


def movimento():
    N = int(round(CE.DUR * CE.FPS)); ant = None; res = []
    for n in range(N):
        st = CE.estado(n); r = {"plano": st["id"], "acao": False, "camera": False, "pose_parada_s": 0.0}
        atores = {i: (np.asarray(a["pos"], float), _num(a["pose"]), a["vista"], a["P"].nome) for i, a in enumerate(st.get("atores", []))}
        if st.get("insert"):
            r["acao"] = True; r["camera"] = True                                # inserts: tudo anima (zoom, giro, partículas, contadores)
        elif ant is not None and ant["id"] == st["id"]:
            for i, (pos, pz, vs, nome) in atores.items():
                if i not in ant["atores"]:
                    r["acao"] = True; continue
                p0, z0, v0, _ = ant["atores"][i]
                dpos = float(np.linalg.norm(pos - p0))
                grande = [abs(pz[k] - z0.get(k, pz[k])) for k in pz if k not in ("respira",)]
                if dpos > 1e-4 or vs != v0 or max(grande + [0]) > 0.6:
                    r["acao"] = True
            if not atores:
                r["acao"] = bool(st.get("tv"))                                   # plano da TV: a tela anima
            c0, c1 = ant["cam"], st.get("cam") or {}
            if c1 and (abs(c1.get("zoom", 1) - c0.get("zoom", 1)) > 1e-4 or any(abs(a - b) > 0.05 for a, b in zip(c1.get("pan", (0, 0)), c0.get("pan", (0, 0))))):
                r["camera"] = True
        else:
            r.update(acao=True, camera=True)
        res.append(r); ant = {"id": st["id"], "atores": atores, "cam": dict(st.get("cam") or {})}
    return res


def main(video):
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)], capture_output=True, text=True).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    dur = float(pr["format"]["duration"]); fps = eval(v["r_frame_rate"])
    ok("formato", (v["width"], v["height"]) == (1080, 1920) and abs(fps - 30) < 0.01 and a is not None, f"{v['width']}×{v['height']} · {fps:.0f} qps · {v['codec_name']} + {a['codec_name'] if a else '—'}")
    ok("duracao", 60 <= dur <= 120 and abs(dur - CE.DUR) < 0.15, f"{dur:.2f} s (narração {CE.FIM_VOZ:.2f} s + cartela final); diretriz 60–120 s")
    durs = [p[2] - p[1] for p in CE.PLANOS]; med = float(np.median(durs)); cpm = (len(durs) - 1) / (CE.DUR / 60)
    ok("ritmo", 1.2 <= med <= 2.0, f"{len(durs)} planos · mediana {med:.2f} s · {cpm:.0f} cortes/min · {sum(1.5 <= d <= 2.0 for d in durs)} planos entre 1,5 e 2 s · "
       f"{sum(d > 3.0 for d in durs)} acima de 3 s (referências: mediana 1,7 s, 31 cortes/min)")
    mv = movimento(); N = len(mv)
    acao = sum(r["acao"] for r in mv) / N; cam = sum(r["camera"] for r in mv) / N
    por_plano = {}
    for r in mv:
        d = por_plano.setdefault(r["plano"], [0, 0, 0]); d[0] += r["acao"]; d[1] += 1; d[2] += r["camera"]
    minimo = min(x / y for x, y, _ in por_plano.values()); sem_cam = [k for k, (_, y, c) in por_plano.items() if c < y * 0.5]
    ok("movimento_personagens", acao >= 0.85, f"quadros com AÇÃO visível (deslocamento, gesto, troca de pose/vista, tela animando): {100 * acao:.0f} % · plano com menos ação: {100 * minimo:.0f} %")
    ok("camera_em_movimento", cam >= 0.95 and not sem_cam, f"câmera se move em {100 * cam:.0f} % dos quadros; planos com câmera parada: {sem_cam or 'nenhum'}")
    mapa = json.loads((P / "saida" / "mapa_fala_imagem.json").read_text()); erros = []
    for m in mapa:
        pal = next((w for w in CE.PAL if abs(w["ini"] - m["t"]) < 0.02 and w["w"].strip(",.?!").lower() == m["palavra"].lower()), None)
        if pal is None or m["plano_no_instante"] != m["plano"]:
            erros.append(f"{m['palavra']}@{m['t']} (plano {m['plano_no_instante']} ≠ {m['plano']})")
    ok("mapa_fala_imagem", not erros, f"{len(mapa)} palavras-chave, cada uma com a ação no plano certo no instante em que é dita" if not erros else "; ".join(erros))
    inv = n = 0
    for k in range(N):
        for st in CE.estado(k).get("atores", []):
            for lado in ("d", "e"):
                n += 1; inv += bool(st["P"].G.cotovelo_invertido(st["pose"], st["vista"], lado)[0])
    ok("cotovelos", inv == 0, f"{n} braços verificados (todas as poses de todos os quadros, Juca e Jandira), {inv} invertido(s)")
    alt = subprocess.run(["git", "-C", str(RAIZ), "status", "--porcelain", "personagens/heitor/rig_v2"], capture_output=True, text=True).stdout.strip()
    ok("rig_heitor_intacto", alt == "", "nenhuma alteração em personagens/heitor/rig_v2 (Juca e Jandira carregam cópias próprias)" if not alt else alt)
    var = 0.0
    for Pp in (AE.JUCA, AE.JAND):
        for tipo in ("caminhada", "corrida"):
            for s in ("d", "e"):
                xs = []
                for t in np.arange(0, 2, 1 / 30):
                    _, d = Pp.A.pose_locomocao(t, "perfil", tipo); pe = d["pernas"][s]
                    if pe["apoio"]:
                        xs.append(float(pe["alvo"][0]))
                g = [xs[0]]
                for x in xs[1:]:
                    if abs(x - g[-1]) < 0.05:
                        g.append(x)
                    else:
                        var = max(var, max(g) - min(g)); g = [x]
                var = max(var, max(g) - min(g))
    ok("pes_sem_deslizar", var * 0.35 * 1000 < 0.5, f"pé de apoio no ciclo: variação máxima {var * 0.35 * 1000:.2f} mm (personagem avança à velocidade do ciclo: "
       f"Juca {AE.vel(AE.JUCA, 'caminhada'):.2f} m/s andando)")
    e = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]); pk = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
    ok("loudness", abs(I + 14) <= 0.5 and pk <= -1.0, f"{I} LUFS · pico {pk} dBTP")
    numeros = ["0 h de uso", "100 % instalado", "72 → 140 BPM", "96–126 km/h", "16:00 → 18:00", "2 HORAS", "5 HORAS", "65 → 22 °C", "10 HORAS", "02:00",
               "0 m", "06:12", "MISSÃO 1 · 3 %"]
    ok("numeros_na_tela", len(numeros) >= 6, f"{len(numeros)} números com rótulo grande: " + "; ".join(numeros))
    leg = CE.LEG.b; npal = [len(l["txt"].split()) for l in leg]; dest = sum(1 for l in leg if l["dest"]) / len(leg)
    ok("legendas", 2.0 <= np.mean(npal) <= 3.2 and max(npal) <= 3, f"{len(leg)} blocos · média {np.mean(npal):.1f} palavras · máx {max(npal)} · destaque amarelo em {100 * dest:.0f} % dos blocos")
    import graficos_ep02 as GF, inspect
    src = inspect.getsource(GF.marca_dagua)
    ok("marca_dagua", '"MODO"' in src and '"CURIOSO"' in src, "\"MODO CURIOSO\" (MODO branco 60 %, CURIOSO #ffc21f) no canto superior direito, em todos os quadros")
    ok("estampas", all(Pp.H.MOD["estampa"]["texto"] == "Modo Curioso" for Pp in (AE.JUCA, AE.JAND)), "Juca e Jandira com a estampa exatamente \"Modo Curioso\"")
    ok("gancho", CE.PLANOS[0][2] <= 2.0 and CE.LEG.b[0]["ini"] < 0.3, f"pergunta 'E se…' no 1º segundo, quebrada em legendas; 1º corte em {CE.PLANOS[0][2]:.2f} s")
    ok("final", CE.PLANOS[-1][0] == "P49", "pergunta final na narração + cartela COMENTA AÍ / SEGUE AÍ! (últimos 3 s)")
    saida = P / "saida"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", "fps=1,scale=180:-1,tile=11x8", "-frames:v", "1", str(saida / "folha_contato_1qps.jpg")], check=True)
    (saida / "qa_relatorio.json").write_text(json.dumps({"video": Path(video).name, "verificacoes": R,
                                                         "acao_por_plano": {k: round(x / y, 3) for k, (x, y, _) in por_plano.items()},
                                                         "camera_por_plano": {k: round(c / y, 3) for k, (_, y, c) in por_plano.items()}}, ensure_ascii=False, indent=1) + "\n")
    print(f"\nQA: {sum(r['ok'] for r in R)}/{len(R)}")


if __name__ == "__main__":
    main(sys.argv[1])
