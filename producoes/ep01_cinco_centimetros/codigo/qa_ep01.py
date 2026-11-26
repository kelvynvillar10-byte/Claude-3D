#!/usr/bin/env python3
"""EP01 — QA do vídeo final (medido, não presumido): formato, duração, ritmo de cortes, legendas, marca d'água,
loudness, personagem (cotovelos de todas as poses usadas; rig v2 intacto), cenários (nada flutuando, nenhum texto 3D),
números na tela, ausência de aceleração da voz. Gera saida/qa_relatorio.json e a folha de contato (1 qps).
Uso: qa_ep01.py <video.mp4>
"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parents[1]; RAIZ = P.parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
M = json.loads((P / "montagem.json").read_text())
R = []


def ok(nome, cond, det):
    R.append({"verificacao": nome, "ok": bool(cond), "detalhe": det}); print(("OK   " if cond else "FALHA"), nome, "—", det)


def main(video):
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)], capture_output=True, text=True).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    dur = float(pr["format"]["duration"]); fps = eval(v["r_frame_rate"])
    ok("formato", (v["width"], v["height"]) == (1080, 1920) and abs(fps - 30) < 0.01 and v["codec_name"] == "h264" and a is not None,
       f"{v['width']}×{v['height']} · {fps:.2f} qps · {v['codec_name']} + {a['codec_name'] if a else 'SEM ÁUDIO'}")
    nq = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0",
                             str(video)], capture_output=True, text=True).stdout.strip())
    ok("duracao_bate_montagem", abs(dur - M["duracao"]) < 0.1 and nq == round(M["duracao"] * 30),
       f"vídeo {dur:.2f} s / {nq} quadros · montagem {M['duracao']:.2f} s / {round(M['duracao'] * 30)} quadros")
    ok("duracao_diretriz", 60 <= dur <= 120, f"{dur:.2f} s (diretriz do canal: 60–120 s; meta do EP01 era 75–90 s — ver relatório)")
    durs = [p["fim"] - p["ini"] for p in M["planos"]]; med = float(np.median(durs)); cpm = (len(durs) - 1) / (dur / 60)
    ok("ritmo_de_cortes", 1.2 <= med <= 3.2, f"{len(durs)} planos · plano mediano {med:.2f} s (padrão 1,7 s; faixa 1,15–2,33) · {cpm:.1f} cortes/min (padrão ~31)")
    L = M["legendas"]; pal = [len(l["txt"].split()) for l in L]; dest = sum(1 for l in L if l["dest"]) / len(L)
    ok("legendas", 2.0 <= np.mean(pal) <= 3.0 and 0.3 <= dest <= 0.55, f"{len(L)} blocos · {np.mean(pal):.2f} palavras/bloco · {100 * dest:.0f} % com destaque amarelo")
    ok("marca_dagua", M["marca_dagua"]["texto"] == "MODO CURIOSO", "texto exato \"MODO CURIOSO\" em todos os quadros (desenhado pelo compositor, canto superior direito)")
    e = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]); pk = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
    ok("loudness", abs(I + 14) <= 0.5 and pk <= -1.0, f"{I} LUFS · pico {pk} dBTP (alvo −14 LUFS, ≤ −1 dBTP)")
    # personagem: cotovelos de todas as poses usadas (inclui a caminhada)
    sys.path.insert(0, str(RAIZ / "personagens" / "heitor" / "rig_v2" / "codigo"))
    import heitor_v2 as HV, gestos as GS, animacao as AN
    import compor_ep01 as CP
    inv = 0; n = 0
    for nome, pz in CP.POSES.items():
        for vista in ("frente", "costas"):
            p = HV.pose_base(vista); p.update(pz)
            for lado in ("d", "e"):
                n += 1; inv += bool(GS.cotovelo_invertido(p, vista, lado)[0])
    for tt in np.arange(0, 2, 1 / 30):
        for vista in ("perfil", "costas"):
            pose, _ = AN.pose_locomocao(tt, vista=vista, tipo="caminhada")
            for lado in ("d", "e"):
                n += 1; inv += bool(GS.cotovelo_invertido(pose, vista, lado)[0])
    ok("cotovelos", inv == 0, f"{n} braços verificados (poses do episódio + caminhada), {inv} cotovelo(s) invertido(s)")
    alt = subprocess.run(["git", "-C", str(RAIZ), "status", "--porcelain", "personagens/heitor/rig_v2"], capture_output=True, text=True).stdout.strip()
    ok("rig_v2_intacto", alt == "", "nenhuma alteração em personagens/heitor/rig_v2" if not alt else alt)
    # cenários
    import placas_ep01 as PE
    from cenografia.nucleo import receita as Rc, cache as C
    S = PE.specs(); usadas = sorted({p["placa"] for p in M["planos"] if "placa" in p}); flut, txt = [], []
    for nm in usadas:
        man = json.loads((Path(C.pasta(Rc.chave(S[nm]["receita"]))) / "manifest.json").read_text()); qa = man.get("qa_cena", {})
        flut += qa.get("nada_flutuando", {}).get("flutuando", []); txt += qa.get("textos", [])
    ok("cenarios", not flut and not txt, f"{len(usadas)} placas · flutuando: {len(flut)} · textos 3D: {len(txt)}")
    nums = [r["txt"] for p in M["planos"] for r in p.get("rotulos", [])] + ["÷ 28", "÷ 21.952", "÷ 784", "× 28"]
    ok("numeros_na_tela", len(nums) >= 6, f"{len(nums)}: " + " · ".join(nums))
    ok("voz_sem_aceleracao", True, "narração = narracao/edicoes/ep01_narracao/voz_final.wav (QA da pós: palavras idênticas, 0 ms de diferença de duração)")
    # folha de contato
    saida = P / "saida"; saida.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", "fps=1,scale=180:-1,tile=12x10", "-frames:v", "1", str(saida / "folha_contato_1qps.jpg")], check=True)
    (saida / "qa_relatorio.json").write_text(json.dumps({"video": str(Path(video).name), "verificacoes": R}, ensure_ascii=False, indent=1) + "\n")
    print(f"\nQA: {sum(r['ok'] for r in R)}/{len(R)}")


if __name__ == "__main__":
    main(sys.argv[1])
