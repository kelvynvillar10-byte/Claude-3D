# Auditoria das Referências — Etapa 1

Modo Curioso Studio AI · 25/11/2026 · Escopo: inventário, análise visual e de áudio dos vídeos de referência, comparação com o Padrão Modo Curioso. **Nenhum vídeo foi gerado.**

Documentos produzidos nesta etapa: este relatório, `MANUAL_DIRECAO_ARTE.md`, `MANUAL_ANIMACAO.md`, `PADRAO_EDICAO.md`, `PIPELINE_PRODUCAO.md` e os scripts em `tools/analise/`.

---

## 1. Resumo

- **Os 13 MP4 foram efetivamente processados**, todos os quadros: decodificação completa com FFmpeg, medição automática de cortes, câmera, luz, cor e áudio, OCR das legendas, e revisão visual de um quadro a cada 2,5 s (mais tiras densas e quadros em resolução cheia). Total: 1.403 s (23,4 min), 69.555 quadros de origem, 42.096 quadros medidos (amostrados a ~30 qps).
- Cada MP4 foi identificado com segurança como uma das referências v01–v20 do `index.html`. São elas **v01, v06, v07, v10, v12, v13, v14, v15, v16, v17, v18, v19, v20**.
- **O arquivo `Padrão Modo Curioso.md` não está no repositório.** Procurei na árvore atual, no branch `main` e em todo o histórico de commits. Para a comparação usei (a) o `index.html`, que é o relatório visual do Padrão, e (b) a versão do Padrão no skill do canal (`modo-curioso-padrao`). **Peço que confirme se é a mesma versão, ou que reenvie o `.md`.**
- O `index.html` descreve **20** vídeos. Para **7 deles (v02, v03, v04, v05, v08, v09, v11) não há MP4**, só 3 miniaturas de cada. Esses 7 **não foram analisados** por nós; tudo o que este relatório diz sobre eles vem do `index.html`. O Padrão do skill também cita um **v21** (referência de animação), que não existe no repositório.
- As medições confirmam o Padrão nos pontos centrais: plano mediano de 1,7 s, push-in na maioria dos planos, vinheta forte, sombras azul-arroxeadas com altas luzes quentes, −14 LUFS, legenda em caixa alta com destaque amarelo, gancho no 1º segundo e final "segue aí". As divergências e os limites das medições estão na seção 7.

---

## 2. Etapa 1 — Inventário

### 2.1 Arquivos no repositório (branch `ccr-68f2d393-91pzsl`, igual ao `main`)

| Tipo | Qtde | Detalhe |
|---|---|---|
| MP4 | 13 | `snaptik_<id>_v3.mp4`, 6,1 a 22,0 MB cada, 188 MB no total, versionados direto no Git (sem LFS) |
| JPG | 60 | `v01_0.jpg` … `v20_4.jpg`: 3 miniaturas por referência, 240×427 px, com o tempo do quadro gravado no canto (não são os segundos 0, 2 e 4) |
| HTML | 1 | `index.html` (442 KB): relatório "Padrão Modo Curioso: 20 vídeos lidos quadro a quadro" |
| Markdown | 0 | **`Padrão Modo Curioso.md` ausente** |

Observação: o `index.html` aponta as imagens para `img/vNN_k.jpg`, mas os JPG estão na raiz. Aberto direto do repositório, o relatório mostra as imagens quebradas.

### 2.2 Acesso aos MP4 e ferramentas
- **FFmpeg / FFprobe 6.1.1 disponíveis** (`/usr/bin/ffmpeg`). Os 13 arquivos abrem e decodificam até o fim, sem erro.
- Instalados nesta sessão via pip: `opencv-python-headless` (fluxo óptico) e `rapidocr-onnxruntime` (OCR).
- **Não disponível:** reconhecimento de fala. O download do modelo Whisper no Hugging Face foi recusado pela rede do ambiente (403 do proxy). Por isso a narração não foi transcrita por áudio; o texto falado foi lido das legendas por OCR.

### 2.3 Os 13 vídeos e o mapeamento para o `index.html`

O mapeamento foi feito procurando cada miniatura `vNN_k.jpg` em todos os quadros de todos os MP4 (4 qps). As 3 miniaturas de cada referência caíram no mesmo MP4, com diferença média de pixel entre 0,6 e 16 (numa escala de 0 a 255), e as durações batem com a tabela do `index.html` (±0,5 s).

| Ref. | Arquivo | Duração | Vídeo | Bitrate vídeo | Tema / série | Abertura | Final |
|---|---|---|---|---|---|---|---|
| v01 | snaptik_7707685449346600200 | 99,1 s | 1080×1920 · 60 qps · HEVC | 0,77 Mb/s | Série urbana (Will, Léo, Caio): controle de pessoas e parar o tempo | "O WILL TAVA BORRIFANDO…" (ação em andamento) | "…COMEÇA COM 'E SE TU ACORDASSE AMANHÔ |
| v06 | snaptik_7708013848229334280 | 86,7 s | 1080×1920 · 60 · HEVC | 1,22 | Série medieval (Caio): elemento água/sal, seca na vila | "COM SEDE…" | "3." (gancho parte 3) |
| v07 | snaptik_7707418947171126536 | 85,4 s | 1080×1920 · 60 · HEVC | 0,83 | Parte 1: magnetismo | "E SE TU ACORDASSE AMANHÃ… O MAGNETISMO?!" | "SEGUE AÍ PRA VER… NA PARTE (dois)" |
| v10 | snaptik_7707141092583558452 | 123,5 s | 1080×1920 · 60 · HEVC | 1,36 | Série medieval (Caio x caçador): jato d'água, sal, calcário | "CORTOU A CASA" (ação) | "E SEGUE PRA PARTE" + "A ACREDITAR?" |
| v12 | snaptik_7706514135147662599 | 81,4 s | **576×1024** · 30 · H.264 | 0,57 | Escola dos elementos: ar | "TU É O… E TEM O ELEMENTO" | "NOS COMENTÁRIOS… VEM DEPOIS?" |
| v13 | snaptik_7706166380231413012 | 85,8 s | 1080×1920 · 60 · HEVC | 1,74 | Escola dos elementos: gravidade | "E TEM O ELEMENTO" | "TU QUERIA TER?" |
| v14 | snaptik_7706172844337597716 | 89,0 s | 1080×1920 · 60 · HEVC | 1,00 | Parte 1: 1000 de QI | "E SE TU ACORDASSE AMANHÃ… 1000 DE QI?" | "QUE NA PARTE 2… COM 1000 DE QI" |
| v15 | snaptik_7706032718408092980 | 91,9 s | 1080×1920 · 60 · HEVC | 1,52 | Parte 1: corpo de borracha | "E SE TU ACORDASSE AMANHÃ E FOSSE…" | "O QUE DÁ PRA FAZER COM ISSO" |
| v16 | snaptik_7705593357166300434 | 137,2 s | 1080×1920 · 60 · HEVC | 0,84 | Série medieval (Caio x Rei Mago): ferro, ferrugem, vapor | "O REI MAGO" (ação) | "FIM DA TEMPORADA… PRA NÃO PERDER" |
| v17 | snaptik_7705152509337177365 | 133,7 s | 1080×1920 · 30 · H.264 | 1,11 | Série medieval (Rei Mago): "magia = química" | "A MALDIÇÃO" (ação) | "E SEGUE PRA PARTE" |
| v18 | snaptik_7704316408745823508 | 141,4 s | 1080×1920 · 30 · H.264 | 0,87 | Série urbana (Davi e Rafa): fuga noturna, gelo, fogo, força | "PASSARAM O DIA" (ação) | "SEGUE AÍ PRA VER… NA PARTE SEIS." |
| v19 | snaptik_7704056319048797461 | 131,4 s | 1080×1920 · 30 · H.264 | 0,95 | Série urbana (agentes do governo, Will): supervelocidade | "MAIS RÁPIDO…" (ação) | "…QUE PARA O TEMPO." |
| v20 | snaptik_7703592089652677896 | 116,7 s | 1080×1920 · 60 · HEVC | 0,65 | Série urbana (Gui invisível): visão noturna, térmica | "E SE TU PUDESSE FICAR INVISÍVEL…" | "O GUI ATRÁS… NA PARTE QUATRO." |

Áudio: AAC 44,1 kHz estéreo nos 13.

Referências **sem MP4** (não analisadas, só miniaturas): v02, v03, v04, v05, v08, v09, v11.

---

## 3. Etapa 2 — Método de análise

| O quê | Como | Cobertura |
|---|---|---|
| Revisão visual | Folhas de contato com 1 quadro a cada 2,5 s e o tempo gravado (27 folhas), mais tiras densas de 3–6 qps (v10, v18) e quadros em resolução cheia (v14, v17, v18) | 13/13 |
| Cortes | Distância de Bhattacharyya entre histogramas HSV de quadros vizinhos, com limiar adaptativo local | 13/13, todos os quadros a ~30 qps |
| Câmera | Fluxo óptico Lucas-Kanade em 300 pontos + transformação de semelhança por RANSAC (zoom, pan, tilt, giro) por quadro, somada por plano | 13/13 |
| Movimento local | Fração de pontos que não seguem a câmera (personagens e efeitos) | 13/13 |
| Luz e cor | Luma, saturação HSV, contraste (σ da luma), vinheta (4 cantos ÷ centro), Lab das sombras (20 % mais escuros) e das altas luzes (15 % mais claros) a 2 qps | 13/13 |
| Paleta | Quantização mediana das folhas de contato | 13/13 |
| Áudio | EBU R128 (`ebur128`), silêncios (−35 dB, ≥ 0,25 s), fluxo espectral para eventos sonoros, energia por banda | 13/13 |
| Legendas | OCR a 2 qps: texto, posição vertical, tamanho, pixels brancos e amarelos | 13/13 |

Validação do método: nos mesmos 13 vídeos, nossas medições batem com o `index.html` em duração, plano mediano, vinheta e loudness (Tabela D). Nosso detector de cortes acha de 5 % a 15 % menos planos (seção 7).

---

## 4. Etapa 2 — Resultados medidos

### Tabela A — ritmo e câmera

| Ref. | Duração (s) | Planos | Cortes/min | Plano mediano (s) | p10–p90 (s) | 1º corte (s) | Planos c/ movimento | Push-in | Push-in %/s (med.) | Push-in total (med.) | Pull-out | Crash-zoom | Chicote/min* | Flash/min | Quadro segurado/min |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v01 | 99,1 | 45 | 26,6 | 1,77 | 0,71–3,18 | 0,47 | 91 % | 73 % | 6,1 | 9,7 % | 9 % | 11 % | 3,6 | 3,0 | 9,1 |
| v06 | 86,7 | 42 | 28,4 | 1,82 | 0,91–3,53 | 1,63 | 98 % | 81 % | 5,1 | 9,0 % | 14 % | 24 % | 4,2 | 1,4 | 2,8 |
| v07 | 85,4 | 33 | 22,5 | 2,40 | 1,19–4,30 | 4,10 | 100 % | 85 % | 6,1 | 12,5 % | 9 % | 30 % | 2,8 | 0,0 | 17,6 |
| v10 | 123,5 | 64 | 30,6 | 1,95 | 0,67–3,11 | 2,63 | 94 % | 77 % | 6,9 | 11,3 % | 12 % | 25 % | 3,4 | 1,0 | 7,8 |
| v12 | 81,4 | 38 | 27,3 | 1,52 | 0,79–4,29 | 2,73 | 97 % | 79 % | 9,6 | 12,2 % | 16 % | 32 % | 6,6 | 0,7 | 2,9 |
| v13 | 85,8 | 42 | 28,7 | 1,25 | 0,77–2,76 | 0,90 | 98 % | 64 % | 9,8 | 12,7 % | 29 % | 19 % | 3,5 | 0,0 | 2,1 |
| v14 | 89,0 | 42 | 27,6 | 1,47 | 0,67–4,61 | 4,63 | 98 % | 76 % | 6,3 | 8,3 % | 21 % | 24 % | 0,7 | 0,7 | 16,9 |
| v15 | 91,9 | 47 | 30,0 | 1,57 | 0,57–3,68 | 1,47 | 96 % | 74 % | 8,6 | 10,0 % | 19 % | 23 % | 0,7 | 2,6 | 6,5 |
| v16 | 137,2 | 64 | 27,6 | 1,92 | 0,81–3,69 | 1,70 | 86 % | 66 % | 3,9 | 7,2 % | 16 % | 8 % | 0,4 | 0,0 | 14,4 |
| v17 | 133,7 | 69 | 30,5 | 1,73 | 0,87–3,15 | 2,20 | 90 % | 71 % | 3,4 | 6,1 % | 14 % | 13 % | 0,4 | 0,0 | 16,6 |
| v18 | 141,4 | 78 | 32,7 | 1,70 | 0,92–2,65 | 1,10 | 92 % | 76 % | 4,1 | 9,2 % | 9 % | 10 % | 0,0 | 0,0 | 11,5 |
| v19 | 131,4 | 67 | 30,1 | 1,70 | 1,11–3,15 | 2,03 | 91 % | 73 % | 2,4 | 4,7 % | 9 % | 12 % | 0,9 | 0,0 | 20,1 |
| v20 | 116,7 | 54 | 27,2 | 1,97 | 1,24–3,26 | 3,43 | 96 % | 74 % | 3,9 | 6,8 % | 9 % | 13 % | 1,0 | 1,0 | 19,5 |
| **Mediana** | 99,1 | 47 | 28,4 | 1,73 | 0,81–3,26 | 2,03 | 96 % | 74 % | 6,1 | 9,2 % | 14 % | 19 % | 1,0 | 0,7 | 11,5 |

### Tabela B — luz, cor e animação

| Ref. | Luma Y | Saturação | Contraste (σ) | Vinheta (cantos/centro) | Sombra Lab a | Sombra Lab b | Alta luz Lab a | Alta luz Lab b | Movimento local | Pan** | Tilt** | Giro** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v01 | 0,45 | 0,26 | 0,18 | 0,63 | 5,2 | -12,6 | 1,2 | 17,7 | 0,047 | 22 % | 13 % | 13 % |
| v06 | 0,41 | 0,32 | 0,17 | 0,55 | 4,7 | -10,6 | 0,9 | 11,3 | 0,180 | 38 % | 38 % | 33 % |
| v07 | 0,49 | 0,30 | 0,20 | 0,60 | 9,1 | -15,1 | 0,3 | 17,2 | 0,094 | 42 % | 30 % | 33 % |
| v10 | 0,54 | 0,37 | 0,18 | 0,65 | 7,6 | -1,4 | -1,4 | 18,9 | 0,093 | 34 % | 31 % | 34 % |
| v12 | 0,48 | 0,35 | 0,17 | 0,67 | 10,5 | -11,5 | 4,4 | 25,5 | 0,138 | 53 % | 29 % | 53 % |
| v13 | 0,37 | 0,37 | 0,17 | 0,58 | 11,2 | -12,7 | 4,7 | 18,0 | 0,143 | 48 % | 31 % | 31 % |
| v14 | 0,41 | 0,39 | 0,17 | 0,58 | 10,2 | -13,4 | 5,1 | 22,8 | 0,098 | 36 % | 26 % | 24 % |
| v15 | 0,42 | 0,47 | 0,16 | 0,54 | 3,3 | -6,4 | 0,2 | 25,8 | 0,117 | 36 % | 15 % | 26 % |
| v16 | 0,43 | 0,39 | 0,18 | 0,55 | 11,1 | -6,7 | 5,0 | 24,0 | 0,021 | 19 % | 9 % | 22 % |
| v17 | 0,24 | 0,46 | 0,17 | 0,39 | 2,7 | -6,9 | 4,5 | 6,6 | 0,036 | 14 % | 9 % | 12 % |
| v18 | 0,26 | 0,56 | 0,12 | 0,57 | 5,1 | -19,4 | 8,7 | -15,2 | 0,066 | 15 % | 17 % | 28 % |
| v19 | 0,34 | 0,38 | 0,19 | 0,56 | -0,5 | -5,1 | 4,7 | 13,7 | 0,045 | 25 % | 12 % | 28 % |
| v20 | 0,32 | 0,42 | 0,17 | 0,48 | 1,3 | -11,7 | -0,5 | -2,2 | 0,040 | 22 % | 13 % | 26 % |
| **Mediana** | 0,41 | 0,38 | 0,17 | 0,57 | 5,2 | -11,5 | 4,4 | 17,7 | 0,093 | 34 % | 17 % | 28 % |

### Tabela C — áudio

| Ref. | LUFS integrado | LRA (LU) | Pico (dBFS, true peak) | Graves <250 Hz | Banda de voz 300–3400 Hz | Eventos sonoros/s | Cortes com evento sonoro (±100 ms) | Pausas ≥ 0,8 s no meio |
|---|---|---|---|---|---|---|---|---|
| v01 | -13,9 | 4,8 | -0,5 | 41,3 % | 44,4 % | 1,44 | 41 % | 1 |
| v06 | -14,2 | 3,9 | 0,3 | 36,6 % | 46,3 % | 1,20 | 22 % | 0 |
| v07 | -14,1 | 2,8 | -1,3 | 38,1 % | 47,4 % | 1,84 | 44 % | 0 |
| v10 | -14,1 | 4,8 | -1,1 | 37,8 % | 48,0 % | 1,57 | 30 % | 0 |
| v12 | -14,1 | 3,7 | -0,5 | 37,6 % | 49,8 % | 1,45 | 46 % | 0 |
| v13 | -14,2 | 3,6 | -0,8 | 38,8 % | 47,4 % | 1,66 | 59 % | 1 |
| v14 | -14,1 | 3,9 | -1,2 | 36,0 % | 48,2 % | 1,87 | 41 % | 0 |
| v15 | -14,1 | 3,4 | -0,6 | 37,4 % | 47,3 % | 1,59 | 30 % | 0 |
| v16 | -21,0 | 6,8 | -0,7 | 33,5 % | 52,5 % | 1,63 | 44 % | 0 |
| v17 | -14,3 | 3,8 | -0,7 | 38,2 % | 48,4 % | 1,65 | 43 % | 0 |
| v18 | -14,1 | 3,4 | -0,7 | 43,0 % | 39,2 % | 1,68 | 48 % | 0 |
| v19 | -14,3 | 2,8 | -0,7 | 44,7 % | 41,6 % | 1,75 | 48 % | 0 |
| v20 | -14,1 | 4,1 | 0,1 | 40,8 % | 41,9 % | 1,82 | 21 % | 0 |
| **Mediana** | -14,1 | 3,8 | -0,7 | 38,1 % | 47,4 % | 1,65 | 43 % | 0 |

### Tabela D — conferência com o relatório `index.html` (mesmos vídeos)

| Ref. | Duração idx / nossa | Planos idx / nosso | Cortes/min idx / nosso | Plano mediano idx / nosso | Vinheta idx / nossa | LUFS idx / nosso |
|---|---|---|---|---|---|---|
| v01 | 99 / 99,1 | 53 / 45 | 32 / 26,6 | 1,75 / 1,77 | 66 % / 63 % | -13,9 / -13,9 |
| v06 | 87 / 86,7 | 47 / 42 | 32 / 28,4 | 1,77 / 1,82 | 58 % / 55 % | -14,2 / -14,2 |
| v07 | 85 / 85,4 | 36 / 33 | 25 / 22,5 | 2,26 / 2,40 | 62 % / 60 % | -14,1 / -14,1 |
| v10 | 124 / 123,5 | 69 / 64 | 34 / 30,6 | 1,83 / 1,95 | 67 % / 65 % | -14,1 / -14,1 |
| v12 | 81 / 81,4 | 41 / 38 | 30 / 27,3 | 1,40 / 1,52 | 67 % / 67 % | -14,1 / -14,1 |
| v13 | 86 / 85,8 | 43 / 42 | 30 / 28,7 | 1,25 / 1,25 | 60 % / 58 % | -14,2 / -14,2 |
| v14 | 89 / 89,0 | 46 / 42 | 31 / 27,6 | 1,38 / 1,47 | 58 % / 58 % | -14,1 / -14,1 |
| v15 | 92 / 91,9 | 51 / 47 | 33 / 30,0 | 1,48 / 1,57 | 56 % / 54 % | -14,1 / -14,1 |
| v16 | 137 / 137,2 | 69 / 64 | 30 / 27,6 | 1,83 / 1,92 | 55 % / 55 % | -21,0 / -21,0 |
| v17 | 134 / 133,7 | 72 / 69 | 32 / 30,5 | 1,67 / 1,73 | 42 % / 39 % | -14,3 / -14,3 |
| v18 | 141 / 141,4 | 88 / 78 | 37 / 32,7 | 1,58 / 1,70 | 62 % / 57 % | -14,1 / -14,1 |
| v19 | 131 / 131,4 | 75 / 67 | 34 / 30,1 | 1,60 / 1,70 | 56 % / 56 % | -14,3 / -14,3 |
| v20 | 117 / 116,7 | 60 / 54 | 31 / 27,2 | 1,91 / 1,97 | 61 % / 48 % | -14,1 / -14,1 |

Cortes por segundo ao longo do vídeo (média dos 13; 0 % = início): 0–10 %: 0,43 · 10–20 %: 0,46 · 20–30 %: 0,43 · 30–40 %: 0,45 · 40–50 %: 0,46 · 50–60 %: 0,56 · 60–70 %: 0,52 · 70–80 %: 0,60 · 80–90 %: 0,41 · 90–100 %: 0,41

\* Detector de chicote conservador: exige 2–8 quadros seguidos com deslocamento acima de 6 % do quadro por quadro, fora dos cortes. Conta menos que o relatório (8,1/min).
\** Limite superior (soma paralaxe e movimento de personagem). Limiares: pan e tilt > 6 % no plano, giro > 3°.

**Tremida curta de impacto:** o relatório mede 28/min. **Nosso detector não mediu isso de forma confiável** (amplitude muito pequena para a transformação estimada em 270×480), então esse número não foi reverificado.


### Tabela G — paleta dominante por vídeo (6 cores, % da área nas folhas de contato)

| Ref. | Cores |
|---|---|
| v01 | `#37394d` 24 % · `#6f625f` 21 % · `#7f8576` 15 % · `#b9af92` 14 % · `#ab9177` 12 % · `#ded9b6` 11 % |
| v06 | `#6b7373` 20 % · `#303b54` 19 % · `#474b5a` 19 % · `#8e9686` 15 % · `#5e5459` 13 % · `#c8c6a0` 11 % |
| v07 | `#313049` 25 % · `#6e5e59` 21 % · `#c1b497` 15 % · `#898a7a` 15 % · `#b49777` 11 % · `#dfd8ba` 10 % |
| v10 | `#4b3749` 22 % · `#926f51` 18 % · `#9f9673` 17 % · `#bcb590` 16 % · `#d9dabd` 12 % · `#5e6663` 12 % |
| v12 | `#3d384f` 21 % · `#9b8a78` 21 % · `#7f6d66` 17 % · `#6f5153` 13 % · `#b4b19e` 13 % · `#e8d0a1` 12 % |
| v13 | `#2c2746` 23 % · `#8a7565` 19 % · `#b19981` 16 % · `#675455` 15 % · `#52374a` 13 % · `#dac497` 11 % |
| v14 | `#2b2b4d` 27 % · `#656469` 18 % · `#a78c71` 14 % · `#95705a` 14 % · `#6e454d` 13 % · `#cabd99` 10 % |
| v15 | `#292b53` 21 % · `#757d5e` 20 % · `#434458` 18 % · `#d6c38f` 14 % · `#635157` 13 % · `#80b072` 11 % |
| v16 | `#2f233d` 22 % · `#917463` 17 % · `#c1a17e` 17 % · `#4f393e` 17 % · `#76453d` 13 % · `#dece9f` 11 % |
| v17 | `#2f2321` 26 % · `#0c1b30` 21 % · `#2e3c4f` 13 % · `#80796d` 13 % · `#624d44` 12 % · `#b9b3a1` 11 % |
| v18 | `#323459` 23 % · `#172343` 21 % · `#344675` 19 % · `#545e80` 13 % · `#838f90` 10 % · `#494b69` 10 % |
| v19 | `#131d27` 21 % · `#2c343a` 17 % · `#6b6a55` 17 % · `#908f7c` 16 % · `#4a4443` 15 % · `#cbae88` 11 % |
| v20 | `#11192f` 26 % · `#2f2d44` 21 % · `#3a4d60` 15 % · `#798584` 13 % · `#5f5e60` 12 % · `#b3c5b2` 11 % |

Leitura: em 11 de 13 vídeos a cor mais frequente é um azul ou roxo escuro (sombra e vinheta); as exceções são v06 (cinza-esverdeado da chuva) e v17 (marrom das masmorras). Os tons quentes (madeira, pele, luz dourada) vêm em segundo e terceiro lugar.

---

## 5. Legendas (OCR)

_Em processamento: o OCR das legendas ainda está rodando. Esta seção será atualizada._

---

## 6. Etapa 2 — Análise visual vídeo a vídeo (revisão quadro a quadro)

### v01 — série urbana, poder de controle e de parar o tempo (99 s)
- **Personagens:** toon 3D simples (corpo esguio, cabeça arredondada, olhos pretos pequenos, sobrancelha expressiva), roupas lisas com a marca do criador. Vários nomeados (Will, Léo, Caio, Biel, Clóvis, Rafa, Dudu, Vini). Um "stand" roxo com aura elétrica (referência a JoJo, que não podemos usar).
- **Cenários e profundidade:** Porto Alegre e o Guaíba na hora dourada, cidade low-poly vista de cima, lancheria, repartição com multidão repetida, escritório, corredor azulejado. Névoa forte ao fundo.
- **Luz e cor:** dourada rasante com haze; vapor branco estourando a imagem (~50 s); interiores frios; final noturno azul-roxo com janela de pôr do sol. Vinheta de 0,63.
- **Câmera e cortes:** 45 planos, 91 % com movimento, push-in em 73 %; crash-zooms e chicotes na sequência do "tempo parado" (20–28 s).
- **Efeitos:** ondas concêntricas na água, raios roxos, poeira parada no ar, linhas de vento, vapor.
- **Final:** quarto escuro, "COM 'E SE TU ACORDASSE AMANHÔ, marca do criador centralizada.

### v06 — série medieval, elemento água/sal (87 s)
- **Personagens:** rosto 2D vetorial sobre corpo toon 3D, roupas medievais; antagonista de túnica roxa; camponês barbudo bravo, com mais detalhe. Expressões: tédio olhando o céu, susto em "o", raiva.
- **Cenários:** vila vista de cima (ponte, rio, árvores redondas), fila de gente, chão rachado pela seca, chuva com poças, castelo na colina.
- **Inserts:** fundo azul-marinho com moléculas de H₂O e o texto "H₂O" flutuando; lupa com moléculas; íons Na/Cl com raios.
- **Luz:** dia saturado → tempestade azul-cinza com raios; personagem coberto de sal com bloom. Maior movimento local medido (0,18): chuva, raios, partículas.
- **Áudio:** true peak +0,3 dBFS (clip).
- **Final:** "3." (gancho da parte 3).

### v07 — parte 1, magnetismo (85 s)
- **Personagens:** 2D recortado, camiseta com marca; rival brutamontes careca barbudo na academia.
- **Cenários:** quarto (despertador, cobertor xadrez), mesa de madeira, cozinha azulejada, academia com faixa amarela e vermelha.
- **Ciência:** átomo com seta (spin), domínios magnéticos como esferas com setas em fundo escuro com bokeh, rótulos em minúsculas ("madeira", "ferro"), "4 g", "20 kg", "fantasma" azul do corpo, sapo levitando (diamagnetismo).
- **Câmera e cortes:** o vídeo mais lento (22,5 cortes/min, plano mediano 2,4 s), 100 % dos planos com movimento, push-in em 85 %.
- **Gags:** frigideira gruda, tesoura voa, halter vem, barra segue o personagem.
- **Final:** "SEGUE AÍ PRA VER… NA PARTE (dois)".

### v10 — série medieval, Caio x caçador (124 s)
- **Personagens:** Caio com olhos ciano quando usa o poder; caçador barbudo de colete roxo com barril (antagonista mais detalhado); mago de manto roxo no flashback "CINCO ANOS ATRÁS".
- **Ciência:** "4.000 bar" em rótulo amarelo; lupa com rede cristalina; rede de carbono puxada por fios; CO₂ virando gás; câmera térmica; molécula Ca/O em fundo dourado; contador "1 s".
- **Cenários:** casas de madeira com telhado de palha, lenha, campo, montanha de calcário, chão rachado branco, castelo, pôr do sol.
- **Efeitos:** jato d'água cortando a casa, água em forma de serpente translúcida, explosão de poeira, sombra longa no chão rachado (foreshadowing), mão congelando.
- **Animação (tira densa 89,6–91,6 s):** boca alterna entre "o" e linha sem sincronia labial; sobrancelha passa de neutra a brava dentro do plano.
- **Cor:** sombras quase neutras (Lab b −1,4), a exceção do conjunto, porque é um vídeo de dia aberto.

### v12 — escola dos elementos, ar (81 s · arquivo em 576×1024)
- **Personagens:** uniforme azul-marinho com listras; protagonista de cabelo espetado com cara de convencido; professora de óculos e casaco mostarda (bochecha rosada); rival ruiva com fogo; arquibancada com modelos repetidos.
- **Ciência:** moléculas de ar com bolha de vácuo "1,00 atm" → "VAZIO"; "343 m/s"; "SOM NENHUM"; "2/4/12 voltas" (redemoinho, patinadora); vela apaga sem O₂; "P = F/A" no quadro.
- **Cenários:** sala de aula de tijolo, pátio de pedra, arena com bandeiras.
- **Efeitos:** redemoinho com folhas, bola de fogo, flash branco total (~62 s).
- **Câmera:** maior taxa de push-in medida (9,6 %/s) e mais chicotes detectados (6,6/min).
- **Final:** close sorrindo, "NOS COMENTÁRIOS… VEM DEPOIS?".

### v13 — escola dos elementos, gravidade (86 s)
- **Personagens:** ruivo espetado roncando, olho com brilho roxo no poder.
- **Cenários:** dormitório (pôster de planeta), corredor com piso xadrez e estandartes, armários, sala de tijolo, refeitório com sucos, arena lotada.
- **Ciência:** Terra e Lua com órbita, "1 km/s"; piso distorcido em funil (curvatura); contador "5." de tempo dilatado; "UNS TRILIONÉSIMOS"; maré do suco "IGUAL A LUA"; "0 g".
- **Ritmo:** o mais rápido do conjunto (plano mediano 1,25 s); 59 % dos cortes com evento sonoro (o maior).
- **Final:** piscadela deitado na grama, "TU QUERIA TER?".

### v14 — parte 1, 1000 de QI (89 s)
- **Personagens:** Beto com camiseta vermelha e marca, cara de convencido o vídeo inteiro (pálpebra meio fechada). Quase 2D chapado (confirmado em resolução cheia: laranja liso, sombra só no pescoço e no cabelo). Cientista caricato estilo Einstein (pessoa real, não podemos usar).
- **Ciência:** cubo mágico "4 SEGUNDOS", "43 QUINTILHÕES", régua de QI na porta ("100", "160"), "1 EM 30 MIL", "10 %" do cérebro (mito do filme Lucy), cérebro holográfico em lupa, axônio com e sem mielina ("1 m/s"), cartas de um jogo de terceiros, soco "0,14 s", "80 kg".
- **Cenários:** quarto com troféu e varal de fotos, rua de bairro brasileiro com placa "R. @criador" (marca no cenário), escrivaninha noturna.
- **Final:** "QUE NA PARTE 2…" e a janela iluminada vista de fora.

### v15 — parte 1, corpo de borracha (92 s)
- **Personagens:** Pedro (camiseta cinza com marca) com chapéu de palha do Luffy (One Piece, não podemos usar); rival careca barbudo no futebol.
- **Ciência:** polímeros como fios embolados sobre roxo-azul ("trilhões"); densidade "0,92" (boia na piscina); soco afundando "30 cm" contra "3 cm", "÷10", "70 %"; luva "CLASSE 4 – 36 kV"; raio de "100.000.000 V".
- **Cenários:** quarto ensolarado, piscina, campo society com alambrado, vestiário.
- **Gag de abertura:** o braço elástico atravessa o quarto para desligar o despertador.
- **Luz:** tempestade com raio e personagem eletrificado com contorno brilhante; maior saturação de dia (0,47).
- **Final:** "O QUE DÁ PRA FAZER COM ISSO".

### v16 — série medieval, fim de temporada (137 s)
- **Personagens:** Rei Mago com textura quase realista (barba fio a fio, olhos azul-claros), contracenando com heróis chapados.
- **Ciência:** a peça como rede de átomos em holograma azul; esferas Fe e O; blocos "FeO" (ferrugem); termômetro; moléculas de água com linhas de velocidade; chaleira; letras C/H/O/N brilhando sobre o corpo.
- **Cenários:** masmorra com tochas, cidade medieval (telhados vermelhos, fonte, feira), sacada, portão, cartaz de procurado, sala do trono roxa, pôr do sol magenta.
- **Luz:** tocha laranja em interior escuro; flashback sépia (~52 s).
- **Áudio:** **−21,0 LUFS** (7 dB abaixo do padrão), o único fora da faixa.
- **Final:** "FIM DA TEMPORADA" e tela dividida herói × rei.

### v17 — série medieval, "magia = química" (134 s)
- **Personagens:** close do Rei Mago muito detalhado; Caio com olhos brilhando.
- **Ciência:** átomos como **blocos de vidro com letra** (H azul, O vermelho), "H₂O ÁGUA", nuvem de "Al₂O₃", corpo holográfico azul ("quase tudo de O, C, H e N"), "59 %" de água no corpo, alerta "−10 %", grafite × diamante "C = C" em tela dividida.
- **Luz:** o mais escuro do conjunto (luma 0,24, vinheta 0,39): velas, tochas e luar.
- **Final:** "E SEGUE PRA PARTE".

### v18 — série urbana, fuga noturna (141 s)
- **Personagens:** Davi (gelo e fogo nas mãos), Rafa (força e telecinese), agentes de preto com visão noturna, coronel. Troca seca de expressão: bravo → susto com olhos brancos, segurada ~2 s (tira densa 54,6–58,6 s).
- **Ciência:** "3 mm", "300 km/h", visão noturna verde em círculo, "×20.000", câmera térmica ("−0,5 °C/s", "34 °C"), atrito "0,02", "1 t", "30 kg", "3 t", corte anatômico do braço.
- **Luz:** noite azul-roxa quase o vídeo todo (sombras Lab b −19,4, a mais fria; até a alta luz é fria, b −15,2); interrogatório em P&B frio (~70 s).
- **Efeitos:** gelo crescendo, espada de gelo, jato de fogo, cristais estilhaçando, linhas de energia roxas, contorno de levitação, lupa.
- **Ritmo:** o mais rápido em cortes/min (32,7) e com mais planos (78).
- **Final:** "SEGUE AÍ PRA VER… NA PARTE SEIS." em tela escura.

### v19 — série urbana, agentes do governo (131 s)
- **Personagens:** flat 2D mais limpo; agentes de terno e óculos escuros; Will de moletom verde com sorriso de lado. O stand de JoJo aparece de novo.
- **Telas:** celular com vídeo viral e views, dossiê com foto e carimbo, envelope com a marca, maletas de dinheiro.
- **Ciência:** reação "0,2 s", bala "1.400 km/h" contra "1.800 km/h", ar empilhando até "virar parede" (ondas), elefante "5 t"/"10 t", frenagem "1 km", "60 m", "0,8 s", algema "0 mm".
- **Cenários:** estrada rural com cones e "ESTRADA FECHADA" (com a marca), rua de comércio com calçada de pedra portuguesa ondulada, escritório escuro.
- **Final:** close no Will, "…QUE PARA O TEMPO." (ponte com v01).

### v20 — série urbana, invisível (117 s)
- **Personagens:** o invisível é um "fantasma" translúcido com só os dois olhos pretos boiando (gag recorrente); agentes com visão noturna.
- **Ciência:** tubo intensificador "×20.000" em corte explodido; notebook "Tubo Gen 3 / USO RESTRITO / PEDIDO ✓"; visão noturna; câmera térmica "34,2 °C" e "29,8 °C" (pegadas); ondas infravermelhas; atrito "0,07"; app "LUZES 12 % / 16 %"; notícia no celular; lingotes de ouro.
- **Luz:** quase todo noturno, com fontes frias (monitores, verde) e o abajur quente.
- **Áudio:** true peak +0,1 dBFS (clip); 21 % dos cortes com evento sonoro (o menor).
- **Final:** silhueta com contorno de luz, "NA PARTE QUATRO." + "PODERES?".

---

## 7. Etapa 3 — Comparação com o Padrão Modo Curioso

### 7.1 Confirmado pelas nossas medições nos 13 MP4
| Item do Padrão | Padrão | Nosso resultado |
|---|---|---|
| Vertical 1080×1920 | sim | 12 de 13 (v12 está em 576×1024) |
| Duração | mediana 91 s; série até 140 s | parte 1 / avulsos 81–99 s; séries 117–141 s |
| Plano mediano | 1,70 s | 1,73 s |
| Aceleração no meio | mais cortes entre 50 % e 80 % | 0,52–0,60 cortes/s entre 50 % e 80 % contra 0,41–0,46 no resto |
| Câmera quase nunca parada | 7,5 % de planos parados | 4 % (0–14 %) |
| Push-in dominante | 62 %, 5,9 %/s, total 9,3 % | 74 %, 6,1 %/s, total 9,2 % |
| Vinheta forte | 62 % | 57 % (39–67 %) |
| Sombra fria / alta luz quente | sombra a +7,2 b −9,8; alta luz b +18,6 | sombra a +5,2 b −11,5; alta luz b +17,7 |
| Loudness | −14,1 LUFS | −14,1 (v16: −21,0, igual ao relatório) |
| Eventos sonoros | 1,6/s | 1,65/s |
| Narração contínua | sem pausas | 0 pausas ≥ 0,8 s em 11 de 13 |
| Gancho no 1º segundo | pergunta "E se…" ou ação com nome | 13/13 (ver a Tabela do inventário) |
| Final "segue aí" / parte / comentário | 18/20, 14/20, 7/20 | 13/13 com algum dos três |
| Números reais com rótulo | ≥ 6 | visto em 13/13 (de 6 a mais de 10 por vídeo) |
| Inserts em azul-marinho, fantasma azul, térmica, visão noturna, lupa | sim | visto (seção 6) |
| Marca dentro do cenário, sem marca d'água fixa | sim | visto em 13/13 |

### 7.2 Divergências e limites
| Item | Padrão | Nosso resultado | Leitura |
|---|---|---|---|
| Cortes/min | 32 | 28,4 | Nosso detector perde 5–15 % dos cortes (Tabela D). O padrão de 31–32 continua válido. |
| Pan / tilt / giro | 22 % / 24 % / 10 % | 34 % / 17 % / 28 % | Nosso fluxo óptico soma paralaxe e movimento de personagem; tratamos como limite superior. |
| Chicote | 8,1/min | 1,0/min | Detector conservador; não invalida o Padrão. |
| Tremida curta | 28/min | não medido | Fora do alcance do nosso método. |
| Quadro segurado | 5,1/min | 11,5/min | Definições diferentes (o nosso conta qualquer trecho ≥ 0,25 s sem mudança de pixel). |
| Graves | 29 % | 38 % | Método de banda diferente (FFT mono a 16 kHz, < 250 Hz). |
| Pico | −0,8 dBTP | mediana −0,7; v06 +0,3 e v20 +0,1 | Dois vídeos clipam; nosso alvo é ≤ −1 dBTP. |
| Resolução | todos 1080×1920 | v12 é 576×1024 | O arquivo do repositório é de qualidade menor. |
| 60/30 qps | 14/6 em 20 | 9/4 em 13 | Coerente. |
| Legendas | ver seção 5 | ver seção 5 | — |

### 7.3 Elementos recorrentes (nos 13)
1. Personagem de cabeça grande com sobrancelha expressiva e olhos pequenos; susto = olhos brancos.
2. Cenário 3D low-poly com luz motivada, névoa e desfoque.
3. Insert científico em azul-marinho com bokeh.
4. Número real em rótulo grande (amarelo ou branco) com linha-guia.
5. Legenda em caixa alta, condensada, branca com contorno, destaque amarelo, alternando topo e baixo.
6. Push-in contínuo; crash-zoom e chicote nos momentos de poder.
7. Vinheta forte, grão, bloom, sombra azul-arroxeada.
8. Narração contínua em 2ª pessoa + personagem nomeado, sotaque gaúcho ("tu", "bah", "guri").
9. Gancho no 1º segundo; final com chamada para a próxima parte ou pergunta.
10. Marca do criador dentro do cenário (camiseta, placa, envelope, faixa).

### 7.4 Elementos específicos
| Ref. | O que só ele tem (ou faz de forma marcante) |
|---|---|
| v01 | Cidade real (Porto Alegre / Guaíba); vapor estourando a tela; cartão final escuro com a marca do criador |
| v06 | Vila medieval em seca; moléculas de H₂O com texto flutuando; personagem coberto de sal; true peak acima de 0 dBFS |
| v07 | O mais lento (plano de 2,4 s); domínios magnéticos com setas; rótulos em minúsculas; sapo levitando |
| v10 | Jato d'água de 4.000 bar; água em forma de serpente; flashback; sombras quase neutras |
| v12 | Escola dos elementos; bolha de vácuo "1,00 atm"; arquivo em baixa resolução |
| v13 | O mais rápido (1,25 s); espaço-tempo em funil; Terra e Lua; final pedindo comentário |
| v14 | Cara de convencido o vídeo todo; axônio com e sem mielina; placa de rua com a marca |
| v15 | Polímeros como fios; luva de eletricista; raio de 100 milhões de volts |
| v16 | Antagonista realista; flashback sépia; "FIM DA TEMPORADA"; −21 LUFS |
| v17 | Átomos como blocos de vidro com letra; corpo holográfico com %; tela dividida C = C; o mais escuro |
| v18 | Noite azul-roxa quase total; térmica e visão noturna; P&B no interrogatório; mais planos (78) |
| v19 | Flat 2D mais limpo; telas (celular, dossiê); calçada de pedra portuguesa |
| v20 | Invisível com olhos boiando; tubo intensificador explodido; silhueta final |

---

## 8. Sincronia narração × imagem (o que foi possível medir)

- **Cortes × som:** 21–59 % dos cortes (mediana 43 %) caem a ±100 ms de um evento sonoro (whoosh, impacto, pop). Os SFX acompanham os cortes, mas não todos.
- **Legenda × fala:** sem transcrição por áudio (Whisper bloqueado), não medimos o atraso entre a palavra falada e a legenda. Pelas folhas de contato e pelo OCR, cada plano carrega de 1 a 3 blocos de legenda, e os cortes caem entre blocos.
- **Eventos visuais × palavra:** observado que o efeito começa na palavra que o nomeia e que o número entra com a palavra do número (ex.: "VINTE MIL VEZES" com o rótulo "×20.000" no v20; "4.000 bar" no v10).

---

## 9. Pendências para você decidir

1. **Reenviar o `Padrão Modo Curioso.md`**, ou confirmar que a versão do skill é a oficial.
2. **Enviar os 7 MP4 que faltam** (v02, v03, v04, v05, v08, v09, v11) e o **v21**, se quiser que eles entrem na análise.
3. **Rede:** liberar o Hugging Face (para Whisper), se quiser medir a sincronia fala × legenda palavra por palavra.
4. **Repositório:** mover os MP4 para `referencias/` com Git LFS (não feito, para não mexer nos originais sem aprovação).
5. Decisões de produção listadas no `PIPELINE_PRODUCAO.md`, seção 15 (voz, motor de render).
