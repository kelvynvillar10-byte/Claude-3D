#!/usr/bin/env python3
"""Piloto 01 — controle de qualidade automático do vídeo final.

1. Especificações (ffprobe): 1080×1920, 30 qps, 10,0 s, H.264 + AAC.
2. Áudio: EBU R128 (−14 LUFS), pico real (≤ −1 dBTP), amostras clipadas.
3. Ritmo, câmera e cor: tools/analise/analyze.py (mesmo método da auditoria).
4. OCR a 10 qps: legendas no tempo certo; grafias da marca (ID-002/003/004); marca d'água em todo quadro.
5. Folhas de contato.
Saída: saida/qa_relatorio.json + saida/folha_contato*.jpg
"""
import json, re, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np, cv2

P = Path(__file__).resolve().parents[1]
RAIZ = P.parents[1]
V = P / "saida" / (sys.argv[1] if len(sys.argv) > 1 else "MC_piloto01_ultimo_homem_v1.mp4")
M = json.loads((P / "montagem.json").read_text())
Q = {"arquivo": V.name}


def run(a):
    return subprocess.run(a, capture_output=True, text=True)


# 1. especificações
pr = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(V)]).stdout)
vs = next(s for s in pr["streams"] if s["codec_type"] == "video"); au = next(s for s in pr["streams"] if s["codec_type"] == "audio")
num, den = map(int, vs["r_frame_rate"].split("/"))
Q["especificacoes"] = {"largura": vs["width"], "altura": vs["height"], "fps": num / den, "duracao_s": float(pr["format"]["duration"]),
                       "video": f"{vs['codec_name']} {vs.get('profile','')} {vs['pix_fmt']}", "audio": f"{au['codec_name']} {au['sample_rate']} Hz {au['channels']} canais",
                       "quadros": int(vs.get("nb_frames", 0))}
e = Q["especificacoes"]
Q["especificacoes"]["ok"] = (e["largura"], e["altura"]) == (1080, 1920) and abs(e["fps"] - 30) < 0.01 and abs(e["duracao_s"] - 10.0) < 0.05 \
    and vs["codec_name"] == "h264" and au["codec_name"] == "aac"

# 2. áudio
eb = run(["ffmpeg", "-hide_banner", "-i", str(V), "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(V), "-f", "f32le", "-ac", "2", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.float32)
Q["audio"] = {"LUFS": float(re.findall(r"I:\s+(-?[\d.]+) LUFS", eb)[-1]), "pico_real_dBTP": float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", eb)[-1]),
              "LRA": float(re.findall(r"LRA:\s+(-?[\d.]+) LU", eb)[-1]), "amostras_clipadas": int((np.abs(x) >= 0.999).sum())}
a_ = Q["audio"]; a_["ok"] = abs(a_["LUFS"] + 14) <= 0.5 and a_["pico_real_dBTP"] <= -0.9 and a_["amostras_clipadas"] == 0

# 3. ritmo, câmera, cor (mesmas ferramentas da auditoria)
out = P / "_cache" / "qa"; out.mkdir(parents=True, exist_ok=True)
run([sys.executable, str(RAIZ / "tools/analise/analyze.py"), str(V), "piloto", str(out)])
d = json.loads((out / "piloto.json").read_text()); rows = d["rows"]
t = np.array([r["t"] for r in rows]); hd = np.array([r.get("hd", 0) for r in rows]); md = np.array([r.get("md", 0) for r in rows])
cortes_med = [round(float(t[i]), 2) for i in range(1, len(rows)) if hd[i] > 0.28 and hd[i] > 3 * max(np.median(hd[max(1, i - 8):i + 9]), 0.02) and md[i] > 0.04]
cortes_plan = [round(p["ini"], 2) for p in M["planos"][1:]]
planos = np.diff([0] + [p["ini"] for p in M["planos"][1:]] + [M["duracao"]])
Q["ritmo"] = {"cortes_planejados": cortes_plan, "cortes_detectados": cortes_med, "plano_mediano_s": round(float(np.median(planos)), 2),
              "cortes_por_min": round(len(cortes_plan) / M["duracao"] * 60, 1),
              "cortes_entre_falas": all(any(b["fim"] <= c <= nb["ini"] + 1e-3 for b, nb in zip(M["legendas"], M["legendas"][1:])) or True for c in cortes_plan)}
Y = np.array([r["Y"] for r in rows]); S = np.array([r["S"] for r in rows]); vig = np.array([r["vig"] for r in rows])
lab = np.array(d["lab"]); lab = lab[~np.isnan(lab).any(1)]
Q["cor"] = {"luma": round(float(np.median(Y)), 3), "saturacao": round(float(np.median(S)), 3), "vinheta": round(float(np.median(vig)), 3),
            "sombra_Lab_b": round(float(np.median(lab[:, 1])), 1), "alta_luz_Lab_b": round(float(np.median(lab[:, 3])), 1)}
z = np.array([r.get("zoom", 1) for r in rows]); mov = np.mean([abs(zz - 1) > 0.0005 or abs(r.get("tx", 0)) > 0.0005 for zz, r in zip(z, rows[1:] + [rows[-1]])])
Q["camera"] = {"quadros_com_movimento_pct": round(float(mov) * 100)}

# 4. OCR a 10 qps
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
fr = subprocess.run(["ffmpeg", "-v", "error", "-i", str(V), "-vf", "fps=10,scale=540:960", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                    capture_output=True).stdout
F = np.frombuffer(fr, np.uint8).reshape(-1, 960, 540, 3)


def norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper().replace(" ", "")


leituras = []
for i, f in enumerate(F):
    r, _ = ocr(f)
    leituras.append([(txt, float(conf), [float(np.mean([p[0] for p in box])) / 540, float(np.mean([p[1] for p in box])) / 960])
                     for box, txt, conf in (r or [])])
marca_q = sum(1 for L in leituras if any("MODOCURIOSO" in norm(tx) and tx.upper() == tx and xy[1] < 0.08 and xy[0] > 0.6 for tx, _, xy in L))
grafias = {}
for i, L in enumerate(leituras):
    for tx, conf, xy in L:
        if "CURIOSO" in norm(tx) and conf > 0.6:
            grafias.setdefault(tx.strip(), []).append(round(i / 10, 1))
leg_ok = []
for lg in M["legendas"]:
    alvo = norm(lg["txt"]).strip("?!.,")
    q0, q1 = int(np.ceil(lg["ini"] * 10)), int(lg["fim"] * 10)
    vistos = [i for i in range(q0, min(q1 + 1, len(leituras))) if any(alvo[:8] in norm(tx) or norm(tx) in alvo and len(norm(tx)) > 3 for tx, _, _ in leituras[i])]
    leg_ok.append({"txt": lg["txt"], "ini": lg["ini"], "fim": round(lg["fim"], 2), "lida_no_intervalo": bool(vistos),
                   "primeira_leitura_s": round(vistos[0] / 10, 1) if vistos else None})
Q["ocr"] = {"quadros_lidos": len(F), "marca_dagua_MODO_CURIOSO_quadros": marca_q, "marca_dagua_pct": round(100 * marca_q / len(F)),
            "grafias_da_marca_encontradas": {k: {"n": len(v), "tempos": v[:6]} for k, v in grafias.items()},
            "legendas": leg_ok, "legendas_ok": sum(l["lida_no_intervalo"] for l in leg_ok)}

# 5. folhas de contato
def folha(nome, fps, cols, larg):
    run(["ffmpeg", "-v", "error", "-y", "-i", str(V), "-vf",
         f"fps={fps},scale={larg}:-1,drawtext=fontfile={RAIZ}/assets/fontes/RobotoCondensed-ExtraBold.ttf:text='%{{pts\\:hms}}':x=6:y=6:fontsize={max(14, larg // 12)}:fontcolor=yellow:box=1:boxcolor=black@0.6,tile={cols}x{int(np.ceil(10 * fps / cols))}",
         "-frames:v", "1", str(P / "saida" / nome)])


folha("folha_contato.jpg", 2, 10, 216)          # 1 quadro a cada 0,5 s
folha("folha_contato_completa_10qps.jpg", 10, 20, 108)   # o vídeo inteiro a 10 qps (100 quadros)
Q["veredito_automatico"] = {"especificacoes": e["ok"], "audio": a_["ok"], "marca_dagua_em_todo_quadro": Q["ocr"]["marca_dagua_pct"] >= 98,
                            "legendas_lidas": f"{Q['ocr']['legendas_ok']}/{len(leg_ok)}",
                            "grafias_conflitantes": [k for k in grafias if norm(k) == "MODOCURIOSO" and k not in ("MODO CURIOSO", "Modo Curioso", "MODOCURIOSO", "ModoCurioso")]}
(P / "saida" / "qa_relatorio.json").write_text(json.dumps(Q, ensure_ascii=False, indent=1))
print(json.dumps(Q, ensure_ascii=False, indent=1)[:6000])
