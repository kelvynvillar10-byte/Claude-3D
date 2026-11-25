# Padrão de Edição — Modo Curioso Studio AI

Versão 1.0 · Etapa 1. Ritmo, cortes, transições, legendas, rótulos, sincronia e áudio. Baseado nas medições dos **13 MP4 processados** (tabelas completas em `AUDITORIA_REFERENCIAS.md`) e no Padrão Modo Curioso (versão do skill / `index.html`).

Convenção: **[medido]** = medido por nós nos 13 MP4. **[visto]** = observado quadro a quadro. **[padrão]** = Padrão / `index.html`, não reverificado.

---

## 1. Formato de entrega
- Vertical **1080×1920**, 30 qps (60 opcional). Das 13 referências: 9 em 60 qps HEVC, 3 em 30 qps H.264 1080p e 1 em 576×1024 (v12) [medido].
- Duração: **85–100 s** para episódio avulso ou parte 1 (mediana 91 s [padrão]); **115–140 s** para episódio de série [medido: v10, v16–v20 têm de 117 a 141 s].

## 2. Ritmo de cortes

| Métrica | Alvo | Medido (mediana dos 13) [medido] | Padrão [padrão] |
|---|---|---|---|
| Plano mediano | **1,5–2,0 s** | 1,73 s (vídeos de 1,25 a 2,40 s) | 1,70 s |
| 10 % mais curtos | < 0,8 s | 0,81 s | 0,73 s |
| 10 % mais longos | > 3,2 s | 3,26 s | 3,16 s |
| Cortes por minuto | **28–34** | 28,4 (22,5–32,7)* | 32 |
| Planos por vídeo de 91 s | ~45–50 | 47 | 47 |
| Primeiro corte | **1–2 s** | 2,0 s (0,5–4,6 s) | 1,9 s |

\* Nosso detector conta 5–12 % menos cortes que o relatório (perde cortes entre planos de cor parecida). O valor real fica entre as duas colunas.

**Curva ao longo do vídeo** [medido, cortes por segundo, média dos 13]:

| 0–10 % | 10–20 % | 20–30 % | 30–40 % | 40–50 % | 50–60 % | 60–70 % | 70–80 % | 80–90 % | 90–100 % |
|---|---|---|---|---|---|---|---|---|---|
| 0,43 | 0,46 | 0,43 | 0,45 | 0,46 | **0,56** | **0,52** | **0,60** | 0,41 | 0,41 |

Regra: ritmo constante de ~0,45 corte/s, **acelerando entre 50 % e 80 %** (rival e clímax), e mais calmo nos últimos 20 % (resolução e chamada final). O relatório dos 20 vídeos mostra o mesmo desenho [padrão].

**Exceções** [medido]: v07 (magnetismo) é o mais lento, com 22,5 cortes/min e plano mediano de 2,4 s, porque segura planos de explicação. v13 (gravidade) é o mais rápido, com plano mediano de 1,25 s.

## 3. Movimento de câmera na montagem
Ver `MANUAL_ANIMACAO.md`, seção 5. Na edição:
- **Nenhum plano parado**, salvo suspense [medido: 86–100 % dos planos têm movimento; mediana 96 %].
- **Push-in na maioria:** 64–85 % dos planos [medido], mediana de 6,1 %/s e total de 9,2 % no plano. Padrão: 62 %, 5,9 %/s, 9,3 %.
- Pull-out em ~10–15 % dos planos (revelação). Crash-zoom em ~10–25 % [medido; padrão 13 %].

## 4. Transições

| Transição | Frequência | Uso |
|---|---|---|
| Corte seco | dominante | padrão |
| Chicote (whip pan) | ~8/min [padrão]; nosso detector, conservador, acha 0–7/min | mudança de lugar ou ação rápida; 0,13 s com borrão de movimento |
| Fusão rápida | ~1,7/min [padrão] | passagem de tempo, entrada em insert |
| Flash branco | ~1/min [padrão]; medido 0–3/min | impacto, poder, clímax (v01, v12, v15) |
| Fade | raro (0,1/min) [padrão] | só no fim, para o cartão final |
| Quadro segurado | ~5/min [padrão] | suspense; segura a imagem antes da revelação |
| Flashback | sépia (v16) ou P&B frio (v18) [visto] | passado |

## 5. Legendas

### 5.1 Estilo [visto + padrão]
- **CAIXA ALTA**, fonte **condensada bold** (Roboto Condensed 800 ou equivalente livre), **branca**, **contorno escuro** (`#1a110c`, ~12 % do tamanho da letra) + **sombra deslocada**. Confirmado em resolução cheia (v14, v18, v17).
- Altura da letra: **~3 % da altura da tela** (~58 px em 1920). Bloco com ~45 % da largura.
- **Destaque:** uma palavra-chave ou número em **amarelo-dourado `#ffc21f`** (ex.: "O **MAGNETISMO**?!", "QUE NEM O **LUFFY**", "1000 DE **QI**?", "NA PARTE **QUATRO**").
- **Falas de personagem entre aspas** ("OLHA O LOUCO", "SEGUREM ELES.").
- Entrada: pop sutil de **97 % para 100 % em 2 quadros**. Sem quique exagerado, sem animação de saída.

### 5.2 Conteúdo e tempo
- **2–3 palavras por bloco**; cada bloco dura ~0,8 s; ~68 blocos por minuto [padrão]. Nossa medição por OCR está na seção 5.4.
- A legenda transcreve a narração **palavra por palavra**, trocando exatamente na fala.
- O gancho do 1º segundo vem quebrado em 3–5 blocos.

### 5.3 Posição [visto + padrão]
- Padrão: **terço inferior** (centro do texto entre 60 % e 80 % da altura).
- **Sobe para o topo (15–30 %)** quando o rosto ou a ação estão embaixo (visto em todos os 13: v01 alterna topo e baixo; v18 usa muito o topo).
- **Nunca cobrir o rosto.** A posição muda de plano para plano conforme o enquadramento.
- Nunca acima de 10 % (marca d'água e interface do app) nem abaixo de 85 % (interface do app).

### 5.4 Medição por OCR nos 13 MP4 [medido]
| Métrica | Medido (mediana dos 13) | Faixa | Padrão |
|---|---|---|---|
| Blocos por minuto | 64 | 53–77 | 68 |
| Palavras por bloco | 2,26 (OCR subestima) | 2,18–2,49 | 2,9 |
| Palavras/min na tela | ≥ 146 | 121–168 | ≈195 (narração) |
| Blocos com destaque amarelo | 43 % | **0–61 %** (v16, v18, v19 quase sem amarelo) | 42 % |
| Centro vertical | 66 % da altura | 52–74 % | terço inferior |
| Blocos entre 60 % e 80 % | 84 % | 49–96 % | 65 % |
| Blocos no topo (< 35 %) | 16 % | 4–50 % | ~25 % |
| Altura da letra | 2,8 % da tela | 2,8–2,9 % | 3,1 % |
| Largura do bloco | 44 % | 43–47 % | 46 % |

Decisão para o Modo Curioso: o destaque amarelo é **obrigatório** (~40 % dos blocos), apesar de três episódios de série das referências não usarem. Isso dá identidade e ajuda a leitura dos números. Detalhes na auditoria, seção 5.

## 6. Rótulos e números na tela
- Pelo menos **6 números reais por vídeo** [padrão], cada um com rótulo grande e linha-guia (ver o Manual de Direção de Arte, seção 5).
- O rótulo entra **junto com a palavra do número** na narração, com o mesmo pop da legenda.
- O rótulo fica perto do objeto e longe da legenda. Se a legenda está embaixo, o rótulo vai para o meio ou para o topo.
- Unidades em minúsculas ("km/h", "°C", "t", "kg"); legendas pequenas de contexto em caixa alta pequena ("PESO", "REAÇÃO", "GANHO").

## 7. Sincronia narração × imagem

| Evento | Regra | Evidência |
|---|---|---|
| Troca de legenda | exatamente no início da palavra | [padrão] e [visto] |
| Corte | **no fim de uma frase ou bloco de legenda**, ou na palavra-chave | [visto] nas folhas de contato: cada plano carrega 1–3 blocos de legenda |
| SFX | em cada corte e em cada efeito | [medido] 21–59 % dos cortes têm um evento sonoro em ±100 ms (mediana 43 %) |
| Efeito visual | começa na palavra que o nomeia ("…e a porta **voou**") | [visto] |
| Número | entra junto com a palavra do número | [visto] |
| Expressão / pose | troca na batida da frase | [visto] (v10, v18) |

Observação honesta: sem reconhecimento de fala (o modelo Whisper foi bloqueado pela rede do ambiente) não medimos o atraso exato entre a palavra falada e a legenda. A sincronia acima vem da observação e da coincidência entre cortes e eventos sonoros.

## 8. Áudio

| Métrica | Alvo | Medido (13 MP4) [medido] | Padrão [padrão] |
|---|---|---|---|
| Loudness integrado | **−14 LUFS** (±0,5) | −13,9 a −14,3 em 12 de 13; **v16 = −21,0** (fora do padrão) | −14,1 |
| LRA | 3–4 LU | mediana 3,8 (2,8–6,8) | 3,6 |
| Pico real | ≤ −1,0 dBTP | mediana −0,7; v06 e v20 passam de 0 dBFS (clip) | −0,8 |
| Graves (< 250 Hz) | ~30–40 % da energia | mediana 38 % | 29 % |
| Banda de voz (300–3400 Hz) | ~45 % | mediana 47 % | 44 % |
| Eventos sonoros | ~1,6/s | mediana 1,65/s (1,2–1,9) | 1,6/s |
| Pausas ≥ 0,8 s no meio | nenhuma | 0 em 11 de 13; 1 em v01 e v13 | — |

Regras:
1. **Narração contínua** e rápida, com a voz oficial do canal (ID-001, `IDENTIDADE_OFICIAL.md`); só comprimir pausas, nunca acelerar (ver o Pipeline, seção 4).
2. **Música por baixo** com ducking (−12 a −18 dB sob a voz).
3. **SFX baixos**, por baixo da voz: whoosh no chicote, impacto na tremida, pop no rótulo e na legenda de destaque, riser antes do clímax.
4. Master final: −14 LUFS integrado, true peak ≤ −1,0 dBTP. **Não repetir** o clip do v06/v20 nem o volume baixo do v16.

## 9. Abertura e fechamento

**Abertura (0–1 s)** [visto nos 13]:
- Parte 1: "E SE TU ACORDASSE / AMANHÃ / E ___?!" com o personagem acordando na cama (v07, v14, v15) ou "E SE TU PUDESSE…" (v20).
- Continuação: ação em andamento com nome próprio ("O WILL TAVA / BORRIFANDO…", v01; "CORTOU A CASA", v10; "O REI MAGO", v16) ou "TU É O ___ / E TEM O ELEMENTO ___" (v12, v13).
- Sem logo, sem vinheta de abertura, sem tela de título.

**Fechamento (últimos 5 s)** [visto]:
- "SEGUE AÍ PRA VER ___ NA PARTE ___" (v07, v10, v17, v18, v20), "FIM DA TEMPORADA" (v16), ou pergunta para comentário: "NOS COMENTÁRIOS…" (v12), "TU QUERIA TER?" (v13).
- Imagem final: close sorrindo ou convencido, silhueta, ou cenário calmo ao pôr do sol. O ritmo desacelera.
- Nas referências a marca do criador aparece centralizada no fim (v01). **Nós:** a marca d'água MODO CURIOSO fica fixa o vídeo todo; nada de cartão final com marca de terceiros.

## 10. Acabamento comum (aplicado a todos os planos)
1. Gradação: sombras com tinta azul-arroxeada (Lab b ≈ −10), altas luzes quentes (Lab b ≈ +18) [medido: medianas −11,5 e +17,7].
2. Vinheta: cantos com ~57–62 % do brilho do centro [medido: mediana 0,57].
3. Grão de filme leve e bloom nas luzes [visto].
4. Marca d'água MODO CURIOSO (canto superior direito).

## 11. Checklist de edição
1. Gancho dentro do 1º segundo, quebrado em 3–5 legendas?
2. Plano mediano entre 1,5 e 2,0 s? Aceleração entre 50 % e 80 %?
3. Push-in na maioria dos planos; nenhum plano parado sem motivo?
4. Legendas: 2–3 palavras, caixa alta, destaque amarelo, sem cobrir rosto, trocando na fala?
5. Pelo menos 6 números reais com rótulo?
6. SFX em cortes e efeitos, baixos?
7. −14 LUFS, true peak ≤ −1 dBTP, sem pausas longas, voz sem aceleração?
8. Final com "Segue aí" + gancho de parte, ou pergunta para comentário?
9. Marca d'água + marca no cenário? Nenhum elemento de terceiros?
