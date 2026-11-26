#!/usr/bin/env python3
"""F0 da pós-produção: testa todo o fluxo SEM áudio real e SEM créditos.

Narração sintética: espeak-ng (voz diferente da referência do alinhamento) com tempos VERDADEIROS de cada palavra, depois
"estragada" de propósito: tom deslocado (+2 semitons, sem mudar a duração), equalização diferente, pausa de 1,1 s no meio
de uma frase, ruído de fundo, um clique e conversão para MP3 44,1 kHz (como um download do site).
Mede: precisão do alinhamento contra os tempos verdadeiros; integridade das palavras; regras de pausa; loudness; QA.
"""
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import audio as AU, alinhar as AL, processar as PR   # noqa: E402

TEXTO = ("E se o chão da sua casa guardasse um segredo de milhões de anos? Parece impossível, mas aconteceu. "
         "Em 1991, um agricultor cavava um poço quando a pá bateu em algo duro. Ele parou. Olhou. "
         "E percebeu que aquilo não era pedra. Era um osso gigante. E a cidade inteira nunca mais foi a mesma.")
SAIDA = AQUI / "saidas"
res = []


def ok(nome, cond, det=""):
    res.append({"teste": nome, "ok": bool(cond), "detalhe": det})
    print(("OK   " if cond else "FALHA"), nome, det)


def narracao_sintetica(pasta):
    import librosa, soundfile as sf
    y16, ini = AL.falar_espeak(TEXTO, voz="pt-br+m3", velocidade=158, tom=38, faixa=60)
    y = librosa.resample(y16, orig_sr=16000, target_sr=48000)
    toks = AL.tokens(TEXTO)
    k = next(i for i, t in enumerate(toks) if t["w"] == "cavava")          # pausa de 1,1 s ENTRE "cavava" e "um" (sem pontuação)
    corte = int(ini[k + 1] * 48000) - int(0.03 * 48000)
    e = AU.energia_db(y[corte - 2400:corte + 2400]); corte = corte - 2400 + int(np.argmin(e)) * 480
    y = np.concatenate([y[:corte], np.zeros(int(1.1 * 48000), np.float32), y[corte:]])
    verd = [t + (1.1 if t * 48000 >= corte else 0) for t in ini]
    bruto = pasta / "bruto.wav"; sf.write(bruto, y, 48000)
    voz = pasta / "voz_alterada.wav"                                     # outra "voz": tom +2 semitons (mesma duração) e EQ
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto), "-af",
                    "rubberband=pitch=1.12246:transients=smooth,equalizer=f=250:t=q:w=1:g=3,equalizer=f=6500:t=q:w=1:g=4",
                    str(voz)], check=True)
    y, _ = sf.read(voz, dtype="float32")
    rng = np.random.default_rng(7)
    y = y + rng.normal(0, 10 ** (-56 / 20), len(y)).astype(np.float32)   # ruído de fundo
    k_anos = next(i for i, t in enumerate(toks) if t["w"] == "Parece")    # clique na pausa antes de "Parece"
    cl = int(verd[k_anos] * 48000) - int(0.12 * 48000); y[cl] += 0.5; y[cl + 1] -= 0.4
    sf.write(pasta / "voz_final_bruta.wav", y, 48000)
    mp3 = pasta / "narracao_teste.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pasta / "voz_final_bruta.wav"), "-ar", "44100", "-b:a", "128k", str(mp3)], check=True)
    return mp3, verd


def main():
    SAIDA.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        mp3, verd = narracao_sintetica(tmp)
        base = tmp / "edicoes"
        pasta, an, d = PR.analisar(mp3, TEXTO, "teste_f0", base=base)
        pal = json.loads((pasta / "palavras_original.json").read_text())
        # o MP3 e o pitch-shift podem atrasar o sinal: mede o atraso global contra a verdade pela 1ª palavra e desconta
        err = np.array([p["ini"] - t for p, t in zip(pal, verd)])
        off = float(np.median(err)); e = np.abs(err - off)
        ok("alinhamento_precisao", np.percentile(e, 90) <= 0.060,
           f"{len(pal)} palavras · erro médio {e.mean() * 1000:.0f} ms · p90 {np.percentile(e, 90) * 1000:.0f} ms · máx {e.max() * 1000:.0f} ms "
           f"(atraso global do MP3 {off * 1000:.0f} ms descontado)")
        sus = [p for p in an["pausas_suspeitas"]]
        ok("pausa_inadequada_detectada", any(p["depois_de"] == "cavava" for p in sus), f"suspeitas: {[(p['depois_de'], p['dur']) for p in sus]}")
        ok("clique_detectado", len(an["cliques"]) >= 1, f"{len(an['cliques'])} candidato(s): {an['cliques'][:5]}")
        ok("rascunho_com_intencoes_variadas", len({f['intencao'] for f in d['frases']}) >= 3,
           " / ".join(f"{f['n']}:{f['intencao']}" for f in d["frases"]))
        orig_sha = AU.sha256(mp3)
        pasta, R = PR.finalizar("teste_f0", sem_revisao=True, base=base)
        for r in R:
            ok("qa:" + r["verificacao"], r["ok"], r["detalhe"])
        ok("original_de_entrada_intacto", AU.sha256(mp3) == orig_sha, "o arquivo enviado não foi tocado")
        pf = json.loads((pasta / "voz_palavras.json").read_text())
        k = next(i for i, p in enumerate(pf) if p["w"] == "cavava")
        ok("pausa_inadequada_corrigida", pf[k + 1]["ini"] - pf[k]["fim"] <= 0.15, f"cavava→um: {pf[k + 1]['ini'] - pf[k]['fim']:.3f} s")
        for nomearq in ("voz_final.wav", "voz_final.mp3", "voz_palavras.json", "marcacoes.json", "relatorio.md", "qa.json"):
            ok("entrega:" + nomearq, (pasta / nomearq).exists())
        info = AU.info(pasta / "voz_final.wav")
        ok("wav_48k", info["taxa_hz"] == 48000, str(info))
        mk = json.loads((pasta / "marcacoes.json").read_text())
        ok("marcacoes", mk["cortes_visuais"] and mk["impactos"] and mk["pausas"],
           f"{len(mk['cortes_visuais'])} cortes, {len(mk['impactos'])} impactos, {len(mk['espacos_para_sfx'])} SFX, {len(mk['transicoes'])} transições")
        import shutil
        dest = SAIDA / "f0_exemplo"; shutil.rmtree(dest, ignore_errors=True); shutil.copytree(pasta, dest)
        shutil.copy2(mp3, dest / "entrada_sintetica.mp3")
        (dest / "voz_final.wav").unlink()                                   # o WAV fica fora do Git (o MP3 basta para ouvir)
    # áudio longo (~2,5 min): exercita o DTW em duas escalas (grosso + janelas finas)
    import librosa, time
    texto = " ".join([TEXTO] * 7)
    y16, verd2 = AL.falar_espeak(texto, voz="pt-br+m3", velocidade=158, tom=38)
    y = librosa.resample(y16, orig_sr=16000, target_sr=48000)
    t0 = time.time(); falas, sil, _ = AU.segmentar(y); pal = AL.alinhar(texto, y, falas, sil); dt = time.time() - t0
    e = np.abs(np.array([p["ini"] for p in pal]) - np.array(verd2))
    ok("alinhamento_audio_longo", np.percentile(e, 90) <= 0.060 and e.max() <= 0.150,
       f"{len(y) / 48000:.0f} s, {len(pal)} palavras em {dt:.1f} s · erro médio {e.mean() * 1000:.0f} ms · p90 {np.percentile(e, 90) * 1000:.0f} ms · máx {e.max() * 1000:.0f} ms")
    (SAIDA / "f0_resultado.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    n = sum(r["ok"] for r in res)
    print(f"\nF0: {n}/{len(res)} OK · chamadas à MiniMax: 0 · créditos: 0")
    return n == len(res)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
