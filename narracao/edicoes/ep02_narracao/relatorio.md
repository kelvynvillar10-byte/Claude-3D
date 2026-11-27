# Relatório de edição — ep02_narracao

- Original: `40fc7a35-MiniMax_2026-11-26_22_56_13_Kelvyn_villar_Rodrigues.mp3` (mp3, 44100 Hz, 87.83 s), SHA-256 `788c83bdf4981169…` — **preservado sem alterações**.
- Final: `voz_final.wav` (48 kHz, 24 bits) e `voz_final.mp3` (320 kbps), 85.86 s (-1.97 s).
- Direção de edição revisada: sim.
- QA: **13/13** verificações OK.

## 1. Análise da narração original (medido)

- Loudness -22.2 LUFS, pico -2.4 dBTP; piso nas pausas -63.5 dBFS; 1 clique(s) candidato(s); 0 respiração(ões) detectada(s).
- Tom mediano 86.8 Hz, faixa 4.1 semitons.

| Frase | Intenção | Duração | Palavras/s | Variação de tom | Nível vs. mediana | Maior pausa interna | Observação |
|---|---|---|---|---|---|---|---|
| 1 | Curiosidade | 3.8 s | 4.21 | 2.54 st | -1.5 dB | 0.06 s | — |
| 2 | Explicação | 3.75 s | 3.2 | 4.2 st | 0.0 dB | 0.21 s | — |
| 3 | Entusiasmo | 3.21 s | 3.12 | 4.77 st | 0.8 dB | 0.28 s | pausa interna longa |
| 4 | Suspense | 0.65 s | 3.08 | 1.38 st | 1.3 dB | 0.0 s | — |
| 5 | Entusiasmo | 1.23 s | 3.25 | 3.12 st | 1.8 dB | 0.0 s | — |
| 6 | Entusiasmo | 1.54 s | 3.25 | 4.54 st | 0.1 dB | 0.0 s | — |
| 7 | Descoberta/revelação | 4.83 s | 1.86 | 5.0 st | -0.1 dB | 0.3 s | pausa interna longa |
| 8 | Explicação | 6.01 s | 3.0 | 3.7 st | -0.3 dB | 0.29 s | pausa interna longa |
| 9 | Surpresa | 2.28 s | 2.63 | 4.9 st | -1.7 dB | 0.0 s | — |
| 10 | Explicação | 4.08 s | 3.43 | 3.8 st | -0.2 dB | 0.44 s | pausa interna longa |
| 11 | Explicação | 4.1 s | 2.68 | 2.31 st | -0.1 dB | 0.23 s | — |
| 12 | Suspense | 3.29 s | 3.04 | 5.7 st | -0.3 dB | 0.22 s | — |
| 13 | Descoberta/revelação | 3.62 s | 3.04 | 3.47 st | 1.3 dB | 0.3 s | pausa interna longa |
| 14 | Explicação | 2.58 s | 3.1 | 2.7 st | -0.1 dB | 0.29 s | pausa interna longa |
| 15 | Explicação | 3.99 s | 2.26 | 4.6 st | 0.6 dB | 0.31 s | pausa interna longa |
| 16 | Explicação | 3.52 s | 3.13 | 3.5 st | -1.4 dB | 0.15 s | — |
| 17 | Surpresa | 2.29 s | 2.62 | 4.35 st | -0.2 dB | 0.52 s | pausa interna longa |
| 18 | Descoberta/revelação | 5.31 s | 3.39 | 2.74 st | -0.3 dB | 0.32 s | pausa interna longa |
| 19 | Suspense | 2.2 s | 2.73 | 2.7 st | 1.8 dB | 0.18 s | — |
| 20 | Entusiasmo | 2.46 s | 3.66 | 2.79 st | 0.1 dB | 0.0 s | — |
| 21 | Suspense | 1.01 s | 3.96 | 3.49 st | 0.9 dB | 0.0 s | — |
| 22 | Surpresa | 1.69 s | 3.55 | 4.1 st | 0.8 dB | 0.0 s | — |
| 23 | Suspense | 1.98 s | 3.03 | 7.4 st | -1.5 dB | 0.0 s | — |
| 24 | Curiosidade | 3.54 s | 3.11 | 3.1 st | 0.5 dB | 0.28 s | pausa interna longa |
| 25 | Curiosidade | 2.83 s | 3.89 | 2.96 st | 2.0 dB | 0.0 s | — |

Alinhamento das palavras: **whisper**.

**O áudio não tem exatamente o texto do roteiro informado** (o que vale é o falado):

| Tempo | Tipo | Roteiro | Falado |
|---|---|---|---|
| 4.6 s | trocado | Juca | Juka |
| 18.56 s | trocado | Juca | Juka |
| 32.02 s | trocado | Juca | Juka |
| 53.46 s | trocado | Juca | Juka |
| 61.82 s | trocado | Juca | Juka |
| 76.12 s | trocado | Juca | Juka |

## 2. Direção (intenção por frase)

- **1. Curiosidade** — “E se sua namorada chegasse em casa com uma surpresa que mudaria sua vida para sempre?” · destaques: sempre (+1.5 dB) · Claude: revisado (rascunho mantido) — rascunho por regra (^\s*e se\b)
- **2. Explicação** — “Juca estava tranquilamente no sofá quando ela apareceu segurando uma caixa enorme.” · destaques: enorme (+1.5 dB) · Claude: revisado (rascunho mantido) — rascunho: sem pista → explicação
- **3. Entusiasmo** — “Ao abrir, ele encontrou um PlayStation 5 novinho em folha!” · destaques: 5 (+1.5 dB) · Claude: revisado (rascunho mantido) — rascunho por regra (!\s*$)
- **4. Suspense** — “Mas espera...” · destaques: — · Claude: revisado (rascunho mantido) — rascunho por regra (\.\.\.|…)
- **5. Entusiasmo** — “tinha mais uma surpresa!” · destaques: — · Claude: revisado (rascunho mantido) — rascunho por regra (!\s*$)
- **6. Entusiasmo** — “GTA 6 já estava instalado!” · destaques: 6 (+1.5 dB) · Claude: revisado (rascunho mantido) — rascunho por regra (!\s*$)
- **7. Descoberta/revelação** — “Naquele instante, Juca descobriu o verdadeiro significado da felicidade.” · destaques: felicidade (+1.5 dB) · Claude: revisado (rascunho mantido) — rascunho por regra (\bdescobri)
- **8. Explicação** — “Seus olhos brilharam, seu coração acelerou e ele abraçou o videogame como se tivesse encontrado um tesouro perdido.” · destaques: — · Claude: revisado (rascunho mantido) — rascunho: sem pista → explicação
- **9. Surpresa** — “Ele simplesmente não conseguia acreditar naquilo!” · destaques: — · Claude: revisado (rascunho mantido) — rascunho por regra (\bsimplesmente\b)
- **10. Explicação** — “Juca ligou o console, pegou o controle e começou sua aventura em Vice City.” · destaques: — · Claude: revisado (rascunho mantido) — rascunho: sem pista → explicação
- **11. Explicação** — “Cada carro, cada rua e cada detalhe do jogo pareciam incríveis.” · destaques: — · Claude: revisado (rascunho mantido) — rascunho: sem pista → explicação
- **12. Suspense** — “Ele estava tão impressionado que nem percebeu o tempo passando.” · destaques: — · Claude: virada do tempo — pausa antes da sequência de horas
- **13. Descoberta/revelação** — “Duas horas depois, a namorada percebeu que ele ainda estava jogando.” · destaques: — · Claude: revisado (rascunho mantido) — rascunho por regra (\bpercebe[ur])
- **14. Explicação** — “Cinco horas depois, a comida já estava fria.” · destaques: fria (+1.5 dB) · Claude: revisado (rascunho mantido) — rascunho: sem pista → explicação
- **15. Explicação** — “Dez horas depois, Juca continuava exatamente no mesmo lugar.” · destaques: dez (+1.0 dB) · Claude: revisado (rascunho mantido) — rascunho: sem pista → explicação
- **16. Explicação** — “O sofá já parecia ter se tornado sua nova residência oficial.” · destaques: — · Claude: revisado (rascunho mantido) — rascunho: sem pista → explicação
- **17. Surpresa** — “Quando amanheceu, Juca ainda estava jogando.” · destaques: — · Claude: revelação do amanhecer
- **18. Descoberta/revelação** — “A namorada começou a perceber que aquele presente talvez tivesse sido um dos maiores erros da sua vida.” · destaques: — · Claude: revisado (rascunho mantido) — rascunho por regra (\bpercebe[ur])
- **19. Suspense** — “Afinal, ela queria agradar o namorado...” · destaques: — · Claude: revisado (rascunho mantido) — rascunho por regra (\.\.\.|…)
- **20. Entusiasmo** — “Mas acabou criando um verdadeiro morador de Vice City!” · destaques: — · Claude: revisado (rascunho mantido) — rascunho por regra (!\s*$)
- **21. Suspense** — “E o mais impressionante?” · destaques: — · Claude: pergunta de suspense antes da revelação final
- **22. Surpresa** — “Juca ainda estava na primeira missão!” · destaques: primeira (+1.5 dB) · Claude: revelação (piada principal)
- **23. Suspense** — “Agora imagine receber um presente desses...” · destaques: — · Claude: revisado (rascunho mantido) — rascunho por regra (\.\.\.|…)
- **24. Curiosidade** — “Você conseguiria desligar o videogame para dar atenção à sua namorada?” · destaques: — · Claude: revisado (rascunho mantido) — rascunho por regra (\?\s*$)
- **25. Curiosidade** — “Ou também desapareceria da vida real para morar em Vice City?” · destaques: — · Claude: revisado (rascunho mantido) — rascunho por regra (\?\s*$)

## 3. Edições de pausa

| Onde | Tipo | Original | Final | Motivo |
|---|---|---|---|---|
| — | pausa inicial | 0.160 s | 0.150 s | início padronizado |
| sempre → Juca | frase | 0.480 s | 0.380 s | entre frases: Curiosidade (depois) → 0.38 s |
| enorme → Ao | frase | 0.470 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| abrir → ele | virgula | 0.280 s | 0.180 s | vírgula/pausa interna (Entusiasmo): faixa 0.08–0.18 s |
| folha → Mas | frase | 0.500 s | 0.450 s | entre frases: Suspense (antes) → 0.45 s |
| espera → tinha | frase | 0.470 s | 0.600 s | entre frases: Suspense (depois) → 0.60 s |
| surpresa → GTA | frase | 0.480 s | 0.250 s | entre frases: Entusiasmo (depois) → 0.25 s |
| instalado → Naquele | frase | 0.440 s | 0.600 s | entre frases: Descoberta/revelação (antes) → 0.60 s |
| instante → Juca | virgula | 0.300 s | 0.250 s | vírgula/pausa interna (Descoberta/revelação): faixa 0.12–0.25 s |
| significado → da | nenhuma | 0.270 s | 0.100 s | pausa sem pontuação de 0.27 s (inadequada) → 0.10 s |
| felicidade → Seus | frase | 0.390 s | 0.450 s | entre frases: Descoberta/revelação (depois) → 0.45 s |
| brilharam → seu | virgula | 0.240 s | 0.220 s | vírgula/pausa interna (Explicação): faixa 0.10–0.22 s |
| acelerou → e | nenhuma | 0.290 s | 0.100 s | pausa sem pontuação de 0.29 s (inadequada) → 0.10 s |
| naquilo → Juca | frase | 0.530 s | 0.350 s | entre frases: Surpresa (depois) → 0.35 s |
| console → pegou | virgula | 0.260 s | 0.220 s | vírgula/pausa interna (Explicação): faixa 0.10–0.22 s |
| City → Cada | frase | 0.500 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| incríveis → Ele | frase | 0.510 s | 0.600 s | entre frases: Suspense (antes) → 0.60 s |
| passando → Duas | frase | 0.500 s | 0.600 s | entre frases: Suspense (depois) → 0.60 s |
| depois → a | virgula | 0.300 s | 0.250 s | vírgula/pausa interna (Descoberta/revelação): faixa 0.12–0.25 s |
| jogando → Cinco | frase | 0.500 s | 0.450 s | entre frases: Descoberta/revelação (depois) → 0.45 s |
| depois → a | virgula | 0.290 s | 0.220 s | vírgula/pausa interna (Explicação): faixa 0.10–0.22 s |
| fria → Dez | frase | 0.510 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| depois → Juca | virgula | 0.300 s | 0.220 s | vírgula/pausa interna (Explicação): faixa 0.10–0.22 s |
| continuava → exatamente | nenhuma | 0.310 s | 0.100 s | pausa sem pontuação de 0.31 s (inadequada) → 0.10 s |
| lugar → O | frase | 0.470 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| oficial → Quando | frase | 0.480 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| amanheceu → Juca | virgula | 0.280 s | 0.220 s | vírgula/pausa interna (Surpresa): faixa 0.10–0.22 s |
| jogando → A | frase | 0.450 s | 0.600 s | entre frases: Descoberta/revelação (antes) → 0.60 s |
| perceber → que | nenhuma | 0.320 s | 0.100 s | pausa sem pontuação de 0.32 s (inadequada) → 0.10 s |
| vida → Afinal | frase | 0.490 s | 0.450 s | entre frases: Suspense (antes) → 0.45 s |
| namorado → Mas | frase | 0.460 s | 0.600 s | entre frases: Suspense (depois) → 0.60 s |
| City → E | frase | 0.370 s | 0.250 s | entre frases: Entusiasmo (depois) → 0.25 s |
| impressionante → Juca | frase | 0.500 s | 0.600 s | entre frases: Suspense (depois) → 0.60 s |
| desses → Você | frase | 0.480 s | 0.600 s | entre frases: Suspense (depois) → 0.60 s |
| videogame → para | nenhuma | 0.280 s | 0.100 s | pausa sem pontuação de 0.28 s (inadequada) → 0.10 s |
| namorada → Ou | frase | 0.480 s | 0.380 s | entre frases: Curiosidade (depois) → 0.38 s |
| — | pausa final | 0.271 s | 0.500 s | final padronizado |

## 4. Tratamento

- ganho de entrada +2.0 dB (de -22.0 para -20 LUFS) antes da compressão
- filtro de graves em 75 Hz (sempre: tira ronco e subgrave sem efeito na voz)
- remoção de cliques: 1 candidato(s) detectado(s)
- redução de ruído leve: piso nas pausas em -63.5 dBFS
- equalização: corpo +1.0 dB em 150 Hz, lama -1.0 dB em 320 Hz, presenca_contida -1.0 dB em 3200 Hz, contencao_agudos -3.0 dB em 5000 Hz
- de-esser: não aplicado (sibilância em -17.61 dB do total)
- compressão moderada 1.8:1 a partir de -24 dB
- loudness: ganho fixo até -16.0 LUFS e limitador de pico verdadeiro (sobreamostragem 4×) em -1.5 dBTP; resultado -16.1 LUFS, -1.8 dBTP; limitador agindo em 4.99 % do tempo (mais de 1 dB em 2.47 %, mais de 3 dB em 0.24 %; máximo 5.6 dB, em picos isolados)

## 5. Controle de qualidade

- ✅ **original_preservado**: SHA-256 788c83bdf4981169… igual ao registrado
- ✅ **palavras_intactas**: diferença máxima entre cada palavra do original (com o ganho dirigido) e a editada: 0.00e+00 (arredondamento de tempo ≤ 1 amostra)
- ✅ **sem_aceleracao**: maior diferença de duração de uma palavra: 0.00 ms (233 palavras)
- ✅ **tempos_coerentes**: palavras em ordem, sem sobreposição e dentro do áudio final
- ✅ **pausas_dentro_das_regras**: maior silêncio interno medido no final: 0.600 s (teto 0.7 s; proibido ≥ 0,8 s)
- ✅ **pausas_com_fala_preservadas**: 0 pausa(s) não editada(s) por conter fala (listadas no relatório)
- ✅ **loudness**: -16.1 LUFS (alvo -16.0 ± 0,6)
- ✅ **pico_verdadeiro**: -1.8 dBTP (máx. -1.5)
- ✅ **sem_clipagem**: 0 amostra(s) em fundo de escala
- ✅ **tom_preservado**: tom mediano 86.8 → 87.3 Hz (+0.58 %); faixa 4.1 → 4.1 semitons
- ✅ **timbre_sem_exagero**: variação por banda (dB, final − original): graves_20_80 -0.53, corpo_80_250 +1.25, lama_250_500 -0.44, medios_500_2k -0.95, presenca_2k_5k +1.15, sibilancia_5k_10k +2.21, ar_10k_mais +1.57
- ✅ **sincronia_final**: deslocamento entre o áudio editado e o tratado: 0 amostra(s) (os tempos das palavras valem para o final)
- ✅ **atraso_dos_filtros_compensado**: atraso medido e compensado: filtros 1200 amostra(s), loudness 0 amostra(s)

## 6. Marcações para a edição audiovisual

32 cortes visuais, 14 impactos, 9 espaços para efeitos sonoros e 19 transições em `marcacoes.json` (tempos do áudio final). Nenhum efeito sonoro foi adicionado.

## 7. Limitações

- Tempos das palavras pelo Whisper (reconhecimento de fala local) com ajuste pelas pausas; conferir no vídeo de conferência.
- A edição não cria interpretação que não foi gravada: frases marcadas como monótonas precisam de nova geração.
- Análise por medição (energia, tom, espectro); a avaliação de ouvido é do diretor.
