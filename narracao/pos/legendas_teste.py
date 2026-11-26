#!/usr/bin/env python3
"""Vídeo de CONFERÊNCIA da sincronia: narração final + legendas de 2–3 palavras geradas de `voz_palavras.json`
(caixa alta, Roboto Condensed ExtraBold, palavras de destaque em amarelo #ffc21f). Serve para o diretor ouvir e ver se as
palavras batem com a fala. Não é a legenda final do vídeo.
Uso: legendas_teste.py <pasta da narração editada>
"""
import json, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FONTES = RAIZ / "assets" / "fontes"


def _t(s):
    h = int(s // 3600); m = int(s % 3600 // 60); x = s % 60
    return f"{h}:{m:02d}:{x:05.2f}"


def blocos(pal, destaques, max_pal=3, quebra=0.25):
    out, cur = [], []
    for k, p in enumerate(pal):
        cur.append((k, p))
        prox = pal[k + 1] if k + 1 < len(pal) else None
        fim_frase = p["w"][-1:] in ".?!…" or (prox is not None and prox["ini"] - p["fim"] >= quebra)
        if len(cur) >= max_pal or fim_frase or prox is None:
            out.append(cur); cur = []
    res = []
    for i, b in enumerate(out):
        ini = b[0][1]["ini"]; fim = out[i + 1][0][1]["ini"] if i + 1 < len(out) else b[-1][1]["fim"] + 0.3
        txt = " ".join(("{\\c&H1FC2FF&}" + p["w"].upper() + "{\\c&HFFFFFF&}") if k in destaques else p["w"].upper() for k, p in b)
        res.append((ini, fim, txt))
    return res


def main(pasta):
    pasta = Path(pasta)
    pal = json.loads((pasta / "voz_palavras.json").read_text())
    det = json.loads((pasta / "palavras_final_detalhe.json").read_text())
    # palavras do texto (com pontuação) para quebrar nas frases
    texto = (pasta / "texto.txt").read_text()
    for p, d in zip(pal, det):
        fim_c = d["c1"]; p["w"] = texto[d["c0"]:fim_c] + ("".join(c for c in texto[fim_c:fim_c + 2] if c in ".?!…")[:1])
    dr = json.loads((pasta / "direcao_edicao.json").read_text())
    dest = {x["i"] for f in dr["frases"] for x in f["destaques"]}
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
           "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: L,Roboto Condensed ExtraBold,96,&H00FFFFFF,&H00FFFFFF,&H000C111A,&H64000000,1,0,0,0,100,100,0,0,1,7,4,2,60,60,520,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for ini, fim, txt in blocos(pal, dest):
        ass.append(f"Dialogue: 0,{_t(ini)},{_t(fim)},L,,0,0,0,,{txt}")
    arq = pasta / "conferencia_legendas.ass"; arq.write_text("\n".join(ass) + "\n")
    saida = pasta / "conferencia_sincronia.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x1f2a44:s=540x960:r=30", "-i", str(pasta / "voz_final.mp3"),
                    "-vf", f"scale=1080:1920,subtitles={arq}:fontsdir={FONTES},scale=540:960", "-shortest",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-c:a", "aac", "-b:a", "160k", str(saida)], check=True)
    return saida


if __name__ == "__main__":
    print(main(sys.argv[1]))
