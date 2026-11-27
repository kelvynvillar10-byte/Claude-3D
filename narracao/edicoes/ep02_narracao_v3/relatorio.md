# Relatório de edição — ep02_narracao_v3

- Original: `3e86c073-MiniMax_2026-11-27_09_54_28_Kelvyn_Villar_Rodrigues_6.wav` (pcm_s16le, 32000 Hz, 81.14 s), SHA-256 `f99d9ee66a6c6bfc…` — **preservado sem alterações**.
- Final: `voz_final.wav` (48 kHz, 24 bits) e `voz_final.mp3` (320 kbps), 81.85 s (+0.71 s).
- Direção de edição revisada: sim.
- QA: **13/13** verificações OK.

## 1. Análise da narração original (medido)

- Loudness -22.7 LUFS, pico -2.9 dBTP; piso nas pausas -63.1 dBFS; 1 clique(s) candidato(s); 0 respiração(ões) detectada(s).
- Tom mediano 98.6 Hz, faixa 5.3 semitons.

| Frase | Intenção | Duração | Palavras/s | Variação de tom | Nível vs. mediana | Maior pausa interna | Observação |
|---|---|---|---|---|---|---|---|
| 1 | Curiosidade | 3.29 s | 4.86 | 3.6 st | -0.6 dB | 0.0 s | — |
| 2 | Explicação | 3.86 s | 3.11 | 5.58 st | -0.7 dB | 0.23 s | — |
| 3 | Entusiasmo | 3.16 s | 3.16 | 6.9 st | 0.9 dB | 0.28 s | pausa interna longa |
| 4 | Suspense | 1.01 s | 1.98 | 2.01 st | -1.4 dB | 0.25 s | — |
| 5 | Entusiasmo | 1.13 s | 3.54 | 5.87 st | 2.8 dB | 0.0 s | — |
| 6 | Entusiasmo | 1.69 s | 2.96 | 5.01 st | -1.1 dB | 0.09 s | — |
| 7 | Descoberta/revelação | 3.51 s | 2.56 | 5.6 st | -1.2 dB | 0.25 s | — |
| 8 | Explicação | 5.22 s | 3.45 | 4.12 st | -0.7 dB | 0.2 s | — |
| 9 | Surpresa | 2.16 s | 2.78 | 7.71 st | 0.9 dB | 0.0 s | — |
| 10 | Explicação | 3.72 s | 3.76 | 4.98 st | -0.3 dB | 0.28 s | pausa interna longa |
| 11 | Explicação | 3.77 s | 2.92 | 3.8 st | 0.4 dB | 0.5 s | pausa interna longa |
| 12 | Suspense | 3.04 s | 3.29 | 5.9 st | -1.3 dB | 0.27 s | pausa interna longa |
| 13 | Descoberta/revelação | 3.45 s | 3.19 | 3.74 st | 0.6 dB | 0.26 s | pausa interna longa |
| 14 | Explicação | 2.28 s | 3.51 | 3.39 st | 0.6 dB | 0.18 s | — |
| 15 | Explicação | 3.91 s | 2.3 | 4.6 st | 0.4 dB | 0.45 s | pausa interna longa |
| 16 | Explicação | 3.39 s | 3.24 | 4.57 st | -0.1 dB | 0.23 s | — |
| 17 | Surpresa | 2.25 s | 2.67 | 5.36 st | 0.0 dB | 0.27 s | pausa interna longa |
| 18 | Descoberta/revelação | 4.25 s | 4.24 | 3.64 st | -0.5 dB | 0.0 s | — |
| 19 | Suspense | 1.84 s | 3.26 | 4.86 st | -0.9 dB | 0.11 s | — |
| 20 | Entusiasmo | 2.72 s | 3.31 | 6.2 st | 0.0 dB | 0.0 s | — |
| 21 | Suspense | 0.99 s | 4.04 | 6.37 st | 0.1 dB | 0.0 s | — |
| 22 | Surpresa | 1.59 s | 3.77 | 4.74 st | 0.3 dB | 0.08 s | — |
| 23 | Suspense | 1.88 s | 3.19 | 4.3 st | 1.0 dB | 0.0 s | — |
| 24 | Curiosidade | 2.88 s | 3.82 | 3.24 st | -1.3 dB | 0.0 s | — |
| 25 | Curiosidade | 3.5 s | 3.14 | 5.99 st | 0.4 dB | 0.59 s | pausa interna longa |

Alinhamento das palavras: **whisper**.

**O áudio não tem exatamente o texto do roteiro informado** (o que vale é o falado):

| Tempo | Tipo | Roteiro | Falado |
|---|---|---|---|
| 3.98 s | trocado | Juca | Juka |
| 18.24 s | trocado | Juca | Juka |
| 28.84 s | trocado | Juca | Juka |
| 48.7 s | trocado | Juca | Juka |
| 56.54 s | trocado | Juca | Juka |
| 69.72 s | trocado | Juca | Juka |
| 76.42 s | trocado | à | a |

## 2. Direção (intenção por frase)

- **1. Curiosidade** — “E se sua namorada chegasse em casa com uma surpresa que mudaria sua vida para sempre?” · destaques: sempre (+1.5 dB) · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (^\s*e se\b)
- **2. Explicação** — “Juca estava tranquilamente no sofá quando ela apareceu segurando uma caixa enorme.” · destaques: enorme (+1.5 dB) · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho: sem pista → explicação
- **3. Entusiasmo** — “Ao abrir, ele encontrou um PlayStation 5 novinho em folha!” · destaques: 5 (+1.5 dB) · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (!\s*$)
- **4. Suspense** — “Mas espera...” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (\.\.\.|…)
- **5. Entusiasmo** — “tinha mais uma surpresa!” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (!\s*$)
- **6. Entusiasmo** — “GTA 6 já estava instalado!” · destaques: 6 (+1.5 dB) · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (!\s*$)
- **7. Descoberta/revelação** — “Naquele instante, Juca descobriu o verdadeiro significado da felicidade.” · destaques: felicidade (+1.5 dB) · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (\bdescobri)
- **8. Explicação** — “Seus olhos brilharam, seu coração acelerou e ele abraçou o videogame como se tivesse encontrado um tesouro perdido.” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho: sem pista → explicação
- **9. Surpresa** — “Ele simplesmente não conseguia acreditar naquilo!” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (\bsimplesmente\b)
- **10. Explicação** — “Juca ligou o console, pegou o controle e começou sua aventura em Vice City.” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho: sem pista → explicação
- **11. Explicação** — “Cada carro, cada rua e cada detalhe do jogo pareciam incríveis.” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho: sem pista → explicação
- **12. Suspense** — “Ele estava tão impressionado que nem percebeu o tempo passando.” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — virada do tempo — pausa antes da sequência de horas
- **13. Descoberta/revelação** — “Duas horas depois, a namorada percebeu que ele ainda estava jogando.” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (\bpercebe[ur])
- **14. Explicação** — “Cinco horas depois, a comida já estava fria.” · destaques: fria (+1.5 dB) · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho: sem pista → explicação
- **15. Explicação** — “Dez horas depois, Juca continuava exatamente no mesmo lugar.” · destaques: dez (+1.0 dB) · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho: sem pista → explicação
- **16. Explicação** — “O sofá já parecia ter se tornado sua nova residência oficial.” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho: sem pista → explicação
- **17. Surpresa** — “Quando amanheceu, Juca ainda estava jogando.” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revelação do amanhecer
- **18. Descoberta/revelação** — “A namorada começou a perceber que aquele presente talvez tivesse sido um dos maiores erros da sua vida.” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (\bpercebe[ur])
- **19. Suspense** — “Afinal, ela queria agradar o namorado...” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (\.\.\.|…)
- **20. Entusiasmo** — “Mas acabou criando um verdadeiro morador de Vice City!” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (!\s*$)
- **21. Suspense** — “E o mais impressionante?” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — pergunta de suspense antes da revelação final
- **22. Surpresa** — “Juca ainda estava na primeira missão!” · destaques: primeira (+1.5 dB) · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revelação (piada principal)
- **23. Suspense** — “Agora imagine receber um presente desses...” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (\.\.\.|…)
- **24. Curiosidade** — “Você conseguiria desligar o videogame para dar atenção à sua namorada?” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (\?\s*$)
- **25. Curiosidade** — “Ou também desapareceria da vida real para morar em Vice City?” · destaques: — · Claude: mesma direção revisada do EP02 (1ª geração) aplicada à 3ª geração — revisado (rascunho mantido) — rascunho por regra (\?\s*$)

## 3. Edições de pausa

| Onde | Tipo | Original | Final | Motivo |
|---|---|---|---|---|
| — | pausa inicial | 0.120 s | 0.150 s | início padronizado |
| enorme → Ao | frase | 0.350 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| abrir → ele | virgula | 0.280 s | 0.180 s | vírgula/pausa interna (Entusiasmo): faixa 0.08–0.18 s |
| folha → Mas | frase | 0.390 s | 0.450 s | entre frases: Suspense (antes) → 0.45 s |
| espera → tinha | frase | 0.740 s | 0.600 s | entre frases: Suspense (depois) → 0.60 s |
| surpresa → GTA | frase | 0.390 s | 0.250 s | entre frases: Entusiasmo (depois) → 0.25 s |
| instalado → Naquele | frase | 0.380 s | 0.600 s | entre frases: Descoberta/revelação (antes) → 0.60 s |
| felicidade → Seus | frase | 0.410 s | 0.450 s | entre frases: Descoberta/revelação (depois) → 0.45 s |
| perdido → Ele | frase | 0.400 s | 0.500 s | entre frases: Surpresa (antes) → 0.50 s |
| naquilo → Juca | frase | 0.400 s | 0.350 s | entre frases: Surpresa (depois) → 0.35 s |
| console → pegou | virgula | 0.280 s | 0.220 s | vírgula/pausa interna (Explicação): faixa 0.10–0.22 s |
| City → Cada | frase | 0.390 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| jogo → pareciam | nenhuma | 0.270 s | 0.100 s | pausa sem pontuação de 0.27 s (inadequada) → 0.10 s |
| incríveis → Ele | frase | 0.430 s | 0.600 s | entre frases: Suspense (antes) → 0.60 s |
| impressionado → que | nenhuma | 0.270 s | 0.100 s | pausa sem pontuação de 0.27 s (inadequada) → 0.10 s |
| passando → Duas | frase | 0.390 s | 0.600 s | entre frases: Suspense (depois) → 0.60 s |
| jogando → Cinco | frase | 0.380 s | 0.450 s | entre frases: Descoberta/revelação (depois) → 0.45 s |
| fria → Dez | frase | 0.380 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| depois → Juca | virgula | 0.280 s | 0.220 s | vírgula/pausa interna (Explicação): faixa 0.10–0.22 s |
| lugar → O | frase | 0.400 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| oficial → Quando | frase | 0.380 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| amanheceu → Juca | virgula | 0.270 s | 0.220 s | vírgula/pausa interna (Surpresa): faixa 0.10–0.22 s |
| jogando → A | frase | 0.410 s | 0.600 s | entre frases: Descoberta/revelação (antes) → 0.60 s |
| vida → Afinal | frase | 0.390 s | 0.450 s | entre frases: Suspense (antes) → 0.45 s |
| Afinal → ela | virgula | 0.110 s | 0.160 s | vírgula/pausa interna (Suspense): faixa 0.16–0.32 s |
| namorado → Mas | frase | 0.410 s | 0.600 s | entre frases: Suspense (depois) → 0.60 s |
| City → E | frase | 0.390 s | 0.250 s | entre frases: Entusiasmo (depois) → 0.25 s |
| impressionante → Juca | frase | 0.400 s | 0.600 s | entre frases: Suspense (depois) → 0.60 s |
| missão → Agora | frase | 0.400 s | 0.500 s | entre frases: Surpresa (depois) → 0.50 s |
| desses → Você | frase | 0.410 s | 0.600 s | entre frases: Suspense (depois) → 0.60 s |
| namorada → Ou | frase | 0.400 s | 0.380 s | entre frases: Curiosidade (depois) → 0.38 s |
| — | pausa final | 0.173 s | 0.500 s | final padronizado |

## 4. Tratamento

- ganho de entrada +2.6 dB (de -22.6 para -20 LUFS) antes da compressão
- filtro de graves em 75 Hz (sempre: tira ronco e subgrave sem efeito na voz)
- remoção de cliques: 1 candidato(s) detectado(s)
- redução de ruído leve: piso nas pausas em -63.1 dBFS
- equalização: corpo +1.0 dB em 150 Hz, lama -1.0 dB em 320 Hz, presenca_contida -1.0 dB em 3200 Hz, contencao_agudos -3.0 dB em 5000 Hz
- de-esser: não aplicado (sibilância em -16.22 dB do total)
- compressão moderada 1.8:1 a partir de -24 dB
- loudness: ganho fixo até -16.0 LUFS e limitador de pico verdadeiro (sobreamostragem 4×) em -1.5 dBTP; resultado -16.0 LUFS, -1.8 dBTP; limitador agindo em 1.47 % do tempo (mais de 1 dB em 0.47 %, mais de 3 dB em 0.0 %; máximo 2.7 dB, em picos isolados)

## 5. Controle de qualidade

- ✅ **original_preservado**: SHA-256 f99d9ee66a6c6bfc… igual ao registrado
- ✅ **palavras_intactas**: diferença máxima entre cada palavra do original (com o ganho dirigido) e a editada: 0.00e+00 (arredondamento de tempo ≤ 1 amostra)
- ✅ **sem_aceleracao**: maior diferença de duração de uma palavra: 0.00 ms (233 palavras)
- ✅ **tempos_coerentes**: palavras em ordem, sem sobreposição e dentro do áudio final
- ✅ **pausas_dentro_das_regras**: maior silêncio interno medido no final: 0.600 s (teto 0.7 s; proibido ≥ 0,8 s)
- ✅ **pausas_com_fala_preservadas**: 0 pausa(s) não editada(s) por conter fala (listadas no relatório)
- ✅ **loudness**: -16.0 LUFS (alvo -16.0 ± 0,6)
- ✅ **pico_verdadeiro**: -1.8 dBTP (máx. -1.5)
- ✅ **sem_clipagem**: 0 amostra(s) em fundo de escala
- ✅ **tom_preservado**: tom mediano 98.6 → 98.6 Hz (+0.00 %); faixa 5.3 → 5.3 semitons
- ✅ **timbre_sem_exagero**: variação por banda (dB, final − original): graves_20_80 +0.22, corpo_80_250 +0.43, lama_250_500 -0.38, medios_500_2k -0.50, presenca_2k_5k +0.81, sibilancia_5k_10k +1.01, ar_10k_mais +0.14
- ✅ **sincronia_final**: deslocamento entre o áudio editado e o tratado: 0 amostra(s) (os tempos das palavras valem para o final)
- ✅ **atraso_dos_filtros_compensado**: atraso medido e compensado: filtros 1200 amostra(s), loudness 0 amostra(s)

## 6. Marcações para a edição audiovisual

30 cortes visuais, 14 impactos, 9 espaços para efeitos sonoros e 19 transições em `marcacoes.json` (tempos do áudio final). Nenhum efeito sonoro foi adicionado.

## 7. Limitações

- Tempos das palavras pelo Whisper (reconhecimento de fala local) com ajuste pelas pausas; conferir no vídeo de conferência.
- A edição não cria interpretação que não foi gravada: frases marcadas como monótonas precisam de nova geração.
- Análise por medição (energia, tom, espectro); a avaliação de ouvido é do diretor.
