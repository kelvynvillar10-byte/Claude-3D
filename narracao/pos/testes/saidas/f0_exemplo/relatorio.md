# Relatório de edição — teste_f0

- Original: `narracao_teste.mp3` (mp3, 44100 Hz, 23.32 s), SHA-256 `4194e1c2b3fc5b7f…` — **preservado sem alterações**.
- Final: `voz_final.wav` (48 kHz, 24 bits) e `voz_final.mp3` (320 kbps), 23.15 s (-0.17 s).
- Direção de edição revisada: **NÃO** (execução de teste).
- QA: **13/13** verificações OK.

## 1. Análise da narração original (medido)

- Loudness -22.0 LUFS, pico -3.3 dBTP; piso nas pausas -57.2 dBFS; 1 clique(s) candidato(s); 0 respiração(ões) detectada(s).
- Tom mediano 105.1 Hz, faixa 4.8 semitons.

| Frase | Intenção | Duração | Palavras/s | Variação de tom | Nível vs. mediana | Maior pausa interna | Observação |
|---|---|---|---|---|---|---|---|
| 1 | Mistério | 3.9 s | 3.59 | 3.94 st | -0.3 dB | 0.0 s | — |
| 2 | Explicação | 2.42 s | 1.65 | 6.6 st | 0.1 dB | 0.13 s | — |
| 3 | Ação | 7.39 s | 1.89 | 4.6 st | 0.5 dB | 1.07 s | pausa interna longa |
| 4 | Explicação | 0.7 s | 2.86 | 1.5 st | 0.9 dB | 0.0 s | — |
| 5 | Explicação | 0.54 s | 1.85 | 1.58 st | 2.8 dB | 0.0 s | — |
| 6 | Descoberta/revelação | 2.17 s | 3.23 | 8.7 st | -0.7 dB | 0.0 s | — |
| 7 | Entusiasmo | 1.28 s | 3.12 | 5.07 st | -0.2 dB | 0.0 s | — |
| 8 | Tensão | 2.62 s | 3.44 | 4.8 st | -0.4 dB | 0.0 s | — |

Alinhamento das palavras: **espeak**.

## 2. Direção (intenção por frase)

- **1. Mistério** — “E se o chão da sua casa guardasse um segredo de milhões de anos?” · destaques: segredo (+1.5 dB), milhões (+1.5 dB) · rascunho por regra (\bsegredo)
- **2. Explicação** — “Parece impossível, mas aconteceu.” · destaques: impossível (+1.5 dB) · rascunho: sem pista → explicação
- **3. Ação** — “Em 1991, um agricultor cavava um poço quando a pá bateu em algo duro.” · destaques: 1991 (+1.5 dB) · rascunho por regra (\bbat[eiu])
- **4. Explicação** — “Ele parou.” · destaques: — · rascunho: sem pista → explicação
- **5. Explicação** — “Olhou.” · destaques: — · rascunho: sem pista → explicação
- **6. Descoberta/revelação** — “E percebeu que aquilo não era pedra.” · destaques: — · rascunho por regra (\bpercebe[ur])
- **7. Entusiasmo** — “Era um osso gigante.” · destaques: — · rascunho por regra (\bgigante)
- **8. Tensão** — “E a cidade inteira nunca mais foi a mesma.” · destaques: nunca (+1.5 dB) · rascunho por regra (\bnunca mais\b)

## 3. Edições de pausa

| Onde | Tipo | Original | Final | Motivo |
|---|---|---|---|---|
| — | pausa inicial | 0.000 s | 0.150 s | início padronizado |
| anos → Parece | frase | 0.350 s | 0.400 s | entre frases: Mistério (depois) → 0.40 s |
| cavava → um | nenhuma | 1.070 s | 0.100 s | pausa sem pontuação de 1.07 s (inadequada) → 0.10 s |
| duro → Ele | frase | 0.310 s | 0.150 s | entre frases: Ação (depois) → 0.15 s |
| parou → Olhou | frase | 0.360 s | 0.300 s | entre frases: Explicação (depois) → 0.30 s |
| Olhou → E | frase | 0.310 s | 0.600 s | entre frases: Descoberta/revelação (antes) → 0.60 s |
| pedra → Era | frase | 0.320 s | 0.450 s | entre frases: Descoberta/revelação (depois) → 0.45 s |
| gigante → E | frase | 0.310 s | 0.250 s | entre frases: Entusiasmo (depois) → 0.25 s |
| — | pausa final | 0.044 s | 0.500 s | final padronizado |

## 4. Tratamento

- ganho de entrada +1.6 dB (de -21.6 para -20 LUFS) antes da compressão
- filtro de graves em 75 Hz (sempre: tira ronco e subgrave sem efeito na voz)
- remoção de cliques: 1 candidato(s) detectado(s)
- redução de ruído leve: piso nas pausas em -57.2 dBFS
- equalização: corpo +1.5 dB em 150 Hz, lama -1.5 dB em 320 Hz, presença +1.5 dB em 3500 Hz (sem o reforço de 'ar': a sibilância já está alta)
- de-esser: sibilância em -14.64 dB do total (acima de -16)
- compressão moderada 2.5:1 a partir de -24 dB
- loudness: ganho fixo até -16.0 LUFS e limitador de pico verdadeiro (sobreamostragem 4×) em -1.5 dBTP; resultado -16.0 LUFS, -1.8 dBTP; limitador agindo em 0.54 % do tempo (mais de 1 dB em 0.15 %, mais de 3 dB em 0.0 %; máximo 1.8 dB, em picos isolados)

## 5. Controle de qualidade

- ✅ **original_preservado**: SHA-256 4194e1c2b3fc5b7f… igual ao registrado
- ✅ **palavras_intactas**: diferença máxima entre cada palavra do original (com o ganho dirigido) e a editada: 0.00e+00 (arredondamento de tempo ≤ 1 amostra)
- ✅ **sem_aceleracao**: maior diferença de duração de uma palavra: 0.00 ms (55 palavras)
- ✅ **tempos_coerentes**: palavras em ordem, sem sobreposição e dentro do áudio final
- ✅ **pausas_dentro_das_regras**: maior silêncio interno medido no final: 0.000 s (teto 0.7 s; proibido ≥ 0,8 s)
- ✅ **pausas_com_fala_preservadas**: 0 pausa(s) não editada(s) por conter fala (listadas no relatório)
- ✅ **loudness**: -16.0 LUFS (alvo -16.0 ± 0,6)
- ✅ **pico_verdadeiro**: -1.8 dBTP (máx. -1.5)
- ✅ **sem_clipagem**: 0 amostra(s) em fundo de escala
- ✅ **tom_preservado**: tom mediano 105.1 → 105.1 Hz (+0.00 %); faixa 4.8 → 4.8 semitons
- ✅ **timbre_sem_exagero**: variação por banda (dB, final − original): graves_20_80 -1.36, corpo_80_250 +1.25, lama_250_500 -0.34, medios_500_2k -0.76, presenca_2k_5k +0.98, sibilancia_5k_10k +2.54, ar_10k_mais +0.86
- ✅ **sincronia_final**: deslocamento entre o áudio editado e o tratado: 0 amostra(s) (os tempos das palavras valem para o final)
- ✅ **atraso_dos_filtros_compensado**: atraso medido e compensado: filtros 1200 amostra(s), loudness 0 amostra(s)

## 6. Marcações para a edição audiovisual

7 cortes visuais, 7 impactos, 4 espaços para efeitos sonoros e 6 transições em `marcacoes.json` (tempos do áudio final). Nenhum efeito sonoro foi adicionado.

## 7. Limitações

- Tempos das palavras pelo Whisper (reconhecimento de fala local) com ajuste pelas pausas; conferir no vídeo de conferência.
- A edição não cria interpretação que não foi gravada: frases marcadas como monótonas precisam de nova geração.
- Análise por medição (energia, tom, espectro); a avaliação de ouvido é do diretor.
