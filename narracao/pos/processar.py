#!/usr/bin/env python3
"""Pós-produção da narração do Modo Curioso (áudio gerado pelo diretor no MiniMax Audio). Nada aqui chama API nem gasta créditos.

Comandos:
  processar.py ficha <roteiro.txt> [--saida ficha.md]          ficha de geração para o MiniMax Audio (por trecho)
  processar.py analisar <audio> --texto <roteiro.txt> --nome <nome>
        copia o original (intacto, com SHA-256), mede tudo, alinha as palavras e grava o RASCUNHO da direção de edição
  processar.py finalizar <nome> [--sem-revisao]
        aplica a direção REVISADA: edição de pausas e destaques, tratamento (preset), tempos das palavras do áudio final,
        marcações, QA e relatório

Pasta de cada narração: narracao/edicoes/<nome>/
  original/<arquivo> + original/SHA256.txt · texto.txt · analise.json · palavras_original.json · direcao_edicao.json
  voz_final.wav (48 kHz, 24 bits) · voz_final.mp3 (320 kbps) · voz_palavras.json · marcacoes.json · qa.json · relatorio.md · imagens/
"""
import json, shutil, sys
from pathlib import Path
import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import audio as AU            # noqa: E402
import alinhar as AL          # noqa: E402
import direcao_edicao as DE   # noqa: E402
import editar as ED           # noqa: E402
import tratar as TR           # noqa: E402
import marcacoes as MK        # noqa: E402
import qa as QA               # noqa: E402

EDICOES = AQUI.parent / "edicoes"
SR = AU.SR


def _json(caminho, obj):
    Path(caminho).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def analisar(caminho_audio, texto, nome, base=EDICOES):
    pasta = Path(base) / nome
    (pasta / "original").mkdir(parents=True, exist_ok=True); (pasta / "imagens").mkdir(exist_ok=True)
    orig = pasta / "original" / Path(caminho_audio).name
    if not orig.exists():
        shutil.copy2(caminho_audio, orig)
    sha = AU.sha256(orig)
    if AU.sha256(caminho_audio) != sha:
        raise SystemExit("PARADO: já existe um original diferente com esse nome nesta pasta (o original nunca é sobrescrito)")
    (pasta / "original" / "SHA256.txt").write_text(f"{sha}  {orig.name}\n")
    (pasta / "texto.txt").write_text(texto)
    y = AU.ler(orig)
    falas, sil, seg = AU.segmentar(y)
    resp = AU.respiracoes(y, sil)
    pal = AL.alinhar(texto, y, falas, sil)
    d = DE.rascunho(texto, pal)
    por_frase = []
    for f in d["frases"]:
        a, b = pal[f["palavras"][0]]["ini"], pal[f["palavras"][1]]["fim"]
        trecho = y[int(a * SR):int(b * SR)]
        t = AU.tom(trecho) if b - a > 0.3 else {"faixa_semitons": None, "mediana_hz": None}
        e = AU.energia_db(trecho); e = e[e > seg["limiar_db"]]
        n_pal = f["palavras"][1] - f["palavras"][0] + 1
        internas = [pal[k + 1]["ini"] - pal[k]["fim"] for k in range(f["palavras"][0], f["palavras"][1])]
        por_frase.append({"n": f["n"], "ini": a, "fim": b, "duracao_s": round(b - a, 3), "palavras": n_pal,
                          "palavras_por_s": round(n_pal / max(b - a, 1e-3), 2), "tom_mediano_hz": t["mediana_hz"],
                          "variacao_tom_semitons": t["faixa_semitons"], "nivel_db": round(float(np.median(e)), 1) if len(e) else None,
                          "maior_pausa_interna_s": round(max(internas), 3) if internas else 0.0,
                          "monotona": bool(t["faixa_semitons"] is not None and t["faixa_semitons"] < 2.0 and b - a >= 1.2)})
    niveis = [p["nivel_db"] for p in por_frase if p["nivel_db"] is not None]
    med = float(np.median(niveis)) if niveis else 0
    for p in por_frase:
        p["desvio_nivel_db"] = round(p["nivel_db"] - med, 1) if p["nivel_db"] is not None else None
    pausas = [{"depois_de": pal[k]["w"], "antes_de": pal[k + 1]["w"], "ini": pal[k]["fim"], "dur": round(pal[k + 1]["ini"] - pal[k]["fim"], 3),
               "tipo": ED._tipo_fronteira(texto, pal[k], pal[k + 1])} for k in range(len(pal) - 1)]
    an = {"arquivo": orig.name, "sha256": sha, "formato": AU.info(orig), "duracao_s": round(len(y) / SR, 3),
          "segmentacao": seg, "falas": falas, "silencios": sil, "respiracoes": resp,
          "piso_ruido_db": AU.piso_ruido_db(y, sil), "cliques": AU.cliques(y), "bandas": AU.espectro_bandas(y),
          "loudness": AU.loudness(y), "tom": AU.tom(y), "por_frase": por_frase,
          "pausas_entre_palavras": pausas,
          "pausas_suspeitas": [p for p in pausas if (p["tipo"] == "nenhuma" and p["dur"] > DE.PAUSA_INADEQUADA) or p["dur"] >= 0.8],
          "picos": {"amostra_max": round(float(np.abs(y).max()), 4), "clipadas": int((np.abs(y) >= 0.999).sum())}}
    _json(pasta / "analise.json", an)
    _json(pasta / "palavras_original.json", pal)
    if not (pasta / "direcao_edicao.json").exists() or not json.loads((pasta / "direcao_edicao.json").read_text()).get("revisado"):
        _json(pasta / "direcao_edicao.json", d)
    AU.imagem_onda(orig, pasta / "imagens" / "original_onda.png")
    return pasta, an, d


def finalizar(nome, sem_revisao=False, base=EDICOES):
    pasta = Path(base) / nome
    d = json.loads((pasta / "direcao_edicao.json").read_text())
    if not d.get("revisado") and not sem_revisao:
        raise SystemExit("PARADO: a direção de edição ainda não foi revisada (\"revisado\": false)")
    an = json.loads((pasta / "analise.json").read_text())
    pal = json.loads((pasta / "palavras_original.json").read_text())
    texto = (pasta / "texto.txt").read_text()
    erros = DE.validar(d, len(pal))
    if erros:
        raise SystemExit("PARADO: direção inválida: " + "; ".join(erros))
    orig = pasta / "original" / an["arquivo"]
    if AU.sha256(orig) != an["sha256"]:
        raise SystemExit("PARADO: o original mudou desde a análise")
    y = AU.ler(orig)
    editado, pf, ops, g = ED.editar(y, SR, texto, pal, d, an["respiracoes"], an["segmentacao"]["limiar_db"])
    com_ganho = (y * (10 ** (g / 20))).astype(np.float32)
    medidas = {"cliques": an["cliques"], "piso_ruido_db": an["piso_ruido_db"], "bandas": an["bandas"]}
    pr = TR.carregar_preset()
    final, trat = TR.tratar(editado, SR, medidas, pr)
    AU.gravar_wav(final, pasta / "voz_final.wav"); AU.gravar_mp3(final, pasta / "voz_final.mp3", kbps=pr["mp3_kbps"])
    _json(pasta / "voz_palavras.json", [{"w": p["w"], "ini": p["ini"], "fim": p["fim"]} for p in pf])
    _json(pasta / "palavras_final_detalhe.json", pf)
    mk = MK.gerar(pf, d, len(final) / SR)
    _json(pasta / "marcacoes.json", mk)
    R, med = QA.verificar({"original": y, "com_ganho": com_ganho, "editado": editado, "final": final, "sr": SR, "palavras_orig": pal,
                           "palavras_final": pf, "ops": ops, "preset": pr, "sha_registrado": an["sha256"], "caminho_original": orig, "trat": trat})
    _json(pasta / "qa.json", {"verificacoes": R, "medidas": med})
    AU.imagem_onda(pasta / "voz_final.wav", pasta / "imagens" / "final_onda.png")
    AU.imagem_espectro(orig, pasta / "imagens" / "original_espectro.png")
    AU.imagem_espectro(pasta / "voz_final.wav", pasta / "imagens" / "final_espectro.png")
    (pasta / "relatorio.md").write_text(relatorio(nome, an, d, ops, trat, R, med, mk, len(y) / SR, len(final) / SR))
    return pasta, R


def relatorio(nome, an, d, ops, trat, R, med, mk, dur0, dur1):
    L0, L1 = an["loudness"], med["loudness_final"]
    lin = [f"# Relatório de edição — {nome}", "",
           f"- Original: `{an['arquivo']}` ({an['formato']['codec']}, {an['formato']['taxa_hz']} Hz, {dur0:.2f} s), SHA-256 `{an['sha256'][:16]}…` — **preservado sem alterações**.",
           f"- Final: `voz_final.wav` (48 kHz, 24 bits) e `voz_final.mp3` (320 kbps), {dur1:.2f} s ({dur1 - dur0:+.2f} s).",
           f"- Direção de edição revisada: {'sim' if d.get('revisado') else '**NÃO** (execução de teste)'}.",
           f"- QA: **{sum(r['ok'] for r in R)}/{len(R)}** verificações OK.", "",
           "## 1. Análise da narração original (medido)", "",
           f"- Loudness {L0['integrado_lufs']} LUFS, pico {L0['pico_verdadeiro_dbtp']} dBTP; piso nas pausas {an['piso_ruido_db']} dBFS; "
           f"{len(an['cliques'])} clique(s) candidato(s); {len(an['respiracoes'])} respiração(ões) detectada(s).",
           f"- Tom mediano {an['tom']['mediana_hz']} Hz, faixa {an['tom']['faixa_semitons']} semitons.", "",
           "| Frase | Intenção | Duração | Palavras/s | Variação de tom | Nível vs. mediana | Maior pausa interna | Observação |",
           "|---|---|---|---|---|---|---|---|"]
    pf = {p["n"]: p for p in an["por_frase"]}
    for f in d["frases"]:
        p = pf.get(f["n"], {})
        obs = []
        if p.get("monotona"):
            obs.append("ritmo/tom monótono (variação < 2 semitons) — edição não resolve; considerar regenerar")
        if p.get("maior_pausa_interna_s", 0) > DE.PAUSA_INADEQUADA:
            obs.append("pausa interna longa")
        lin.append(f"| {f['n']} | {DE.NOMES[f['intencao']]} | {p.get('duracao_s')} s | {p.get('palavras_por_s')} | {p.get('variacao_tom_semitons')} st | "
                   f"{p.get('desvio_nivel_db')} dB | {p.get('maior_pausa_interna_s')} s | {'; '.join(obs) or '—'} |")
    lin += ["", "## 2. Direção (intenção por frase)", ""]
    for f in d["frases"]:
        dest = ", ".join(f"{x['w']} (+{x['db']} dB)" for x in f["destaques"]) or "—"
        lin.append(f"- **{f['n']}. {DE.NOMES[f['intencao']]}** — “{f['texto']}” · destaques: {dest} · {f['justificativa']}"
                   + (f" · {f['nota']}" if f.get("nota") else ""))
    lin += ["", "## 3. Edições de pausa", "", "| Onde | Tipo | Original | Final | Motivo |", "|---|---|---|---|---|"]
    for o in ops:
        lin.append(f"| {o.get('entre', '—')} | {o['tipo']} | {o['original_s']:.3f} s | {o['final_s']:.3f} s | {o['motivo']}"
                   + (f" · **{o['nota']}**" if o.get("nota") else "") + " |")
    lin += ["", "## 4. Tratamento", ""] + [f"- {x}" for x in trat["decisoes"]]
    lin += ["", "## 5. Controle de qualidade", ""] + [f"- {'✅' if r['ok'] else '❌'} **{r['verificacao']}**: {r['detalhe']}" for r in R]
    lin += ["", "## 6. Marcações para a edição audiovisual", "",
            f"{len(mk['cortes_visuais'])} cortes visuais, {len(mk['impactos'])} impactos, {len(mk['espacos_para_sfx'])} espaços para efeitos sonoros "
            f"e {len(mk['transicoes'])} transições em `marcacoes.json` (tempos do áudio final). Nenhum efeito sonoro foi adicionado.", "",
            "## 7. Limitações", "",
            "- O alinhamento de palavras usa o espeak-ng como referência e DTW: precisão medida no teste F0 contra tempos verdadeiros; "
            "na voz real ela depende da semelhança entre as vozes e é conferida pela escuta do diretor.",
            "- A edição não cria interpretação que não foi gravada: frases marcadas como monótonas precisam de nova geração.",
            "- Análise por medição (energia, tom, espectro); a avaliação de ouvido é do diretor."]
    return "\n".join(lin) + "\n"


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    if a[0] == "ficha":
        cfg = json.loads((AQUI.parent / "config_voz.json").read_text())
        txt = DE.ficha_geracao(Path(a[1]).read_text().strip(), cfg)
        if "--saida" in a:
            Path(a[a.index("--saida") + 1]).write_text(txt + "\n")
        print(txt)
    elif a[0] == "analisar":
        pasta, an, d = analisar(a[1], Path(a[a.index("--texto") + 1]).read_text().strip(), a[a.index("--nome") + 1])
        print(f"análise em {pasta}: {len(d['frases'])} frases, {len(an['pausas_suspeitas'])} pausa(s) suspeita(s); revisar direcao_edicao.json")
    elif a[0] == "finalizar":
        pasta, R = finalizar(a[1], "--sem-revisao" in a)
        print(f"{sum(r['ok'] for r in R)}/{len(R)} verificações OK · {pasta}")
        for r in R:
            print(("OK   " if r["ok"] else "FALHA"), r["verificacao"], "—", r["detalhe"])
