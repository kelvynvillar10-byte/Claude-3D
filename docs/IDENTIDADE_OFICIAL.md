# Identidade Oficial — Modo Curioso Studio AI

Registro das decisões de identidade do canal. Cada decisão tem número, data, status e regras. Elas valem para todos os vídeos e todos os personagens oficiais, e prevalecem sobre os outros documentos em caso de conflito.

| ID | Decisão | Data | Status |
|---|---|---|---|
| ID-001 | Narração com voz sintética licenciada, de características semelhantes às referências, **sem clonar** a voz de terceiros | 25/11/2026 | **Atualizada em 27/11/2026: a voz padrão do canal é a do próprio diretor** (voz dele gerada por ele no MiniMax Audio; autorização do dono da voz). Continua proibido clonar a voz de terceiros |
| ID-002 | Marca **"Modo Curioso"** estampada na camiseta de todos os personagens oficiais, no lugar da identificação de outro produtor | 25/11/2026 | **Aprovada e permanente** |
| ID-003 | Grafia oficial da marca: **"Modo Curioso"** na camiseta (M e C maiúsculos) e **"MODO CURIOSO"** na marca d'água (tudo maiúsculo) | 25/11/2026 | **Confirmada e permanente** |
| ID-004 | Marca dentro dos cenários (telas, envelopes, fichas, placas e elementos visuais de identificação): sempre **"MODO CURIOSO"**, tudo em maiúsculas | 25/11/2026 | **Aprovada e permanente** |

Regra fixa relacionada: nada de personagem, marca ou obra de terceiros (ver `MANUAL_DIRECAO_ARTE.md`, seção 0).

**Fonte da verdade:** este documento. O skill `modo-curioso-padrao` e os manuais foram alinhados a ele em 25/11/2026 (ID-001 a ID-004). A cópia versionada do skill está em `skills/modo-curioso-padrao/SKILL.md`.

---

## ID-001 — Narração

> **Decisão do diretor, 27/11/2026 (depois do EP02):** "Eu quero manter a minha como padrão." A narração oficial do canal passa
> a ser a **voz do próprio diretor**, gerada por ele no MiniMax Audio (voz "Kelvyn villar Rodrigues", usada no EP02) e enviada
> com o texto. Pós-produção em `narracao/pos/` com o preset `preset_ep02_voz_diretor.json`. A voz é dele, então a regra
> "nunca clonar voz sem autorização por escrito" está cumprida por ele mesmo; a proibição de clonar terceiros continua.
> As seções abaixo (análise das referências, voz sintética licenciada) ficam como histórico.

### 1.1 O que a análise da narração das referências mostra

**Método.** Medição acústica do áudio dos 13 MP4 com `tools/analise/voz.py`:
- tom (F0) por pYIN a cada 10 ms;
- faixa de entonação em semitons;
- sílabas por segundo, contando picos de energia na banda de voz;
- duração das frases (trechos falados contínuos);
- direção do final de frase (sobe ou desce);
- brilho (centroide espectral).

Dados completos em `docs/dados/narracao_acustica_13_mp4.json`.

**Limite importante:** eu não escuto o áudio. Timbre e entonação vêm de números; **sotaque e pronúncia não podem ser confirmados por medição**. O que digo sobre sotaque vem do texto da narração, lido nas legendas por OCR. A narração também tem música e efeitos por baixo, o que adiciona algum ruído às medidas de tom.

| Característica | Medido (mediana dos 13; faixa) | Leitura |
|---|---|---|
| Tom médio (F0) | **111 Hz** (105–116 Hz) | Voz masculina adulta, registro médio-grave (barítono leve). Quase idêntico nos 13 vídeos: **é muito provavelmente a mesma voz em todas as referências**, seja um locutor, seja uma voz sintética fixa |
| Tom típico (p10–p90) | 68–158 Hz | Desce bastante no fim das frases e sobe nas ênfases |
| Faixa de entonação (p5–p95) | **17 semitons** (15–21) | Muito expressiva, de contador de histórias, não de leitura neutra. Pode estar um pouco inflada pela música ao fundo |
| Velocidade | **5,5 sílabas/s** enquanto fala (5,2–6,0); ≥ 146 palavras/min na legenda | Rápida. Coerente com os ≈195 palavras/min do Padrão |
| Fala contínua | 58 % do tempo com voz (sem contar consoantes surdas); nenhuma pausa ≥ 0,8 s em 11 de 13 vídeos | Narração sem respiro longo |
| Duração da frase falada | **0,9 s** (0,7–1,2) | Rajadas curtas, do tamanho de um bloco de legenda de 2–3 palavras |
| Final de frase | **60 % descem**, 18 % sobem | Tom afirmativo de crônica. As subidas marcam pergunta e suspense ("…e realmente controlasse o magnetismo?!") |
| Brilho (centroide) | ~1,2 kHz | Timbre quente, não metálico nem estridente |
| Variação de volume na fala | ~8 dB (desvio padrão) | Dinâmica viva, com ênfases, mas comprimida no master (LRA 3,8 LU) |

**Sotaque e linguagem (pelo texto da narração):**
- Português do Brasil com marcas do **Rio Grande do Sul**: "tu" com o verbo na 2ª pessoa ("E SE TU ACORDASSE", "TU CORRESSE", "TU PUDESSE", "TU É O…"), "TAVA", "BAH", "GURI", referências a Porto Alegre e ao Guaíba (v01), "LANCHERIA".
- A pronúncia gaúcha **não foi verificada por escuta**. Ela precisa ser validada por um ouvinte humano no teste de amostra.

**Emoção e estilo (texto + prosódia):** narrador jovem adulto, animado, curioso, com humor e ironia leve; acelera nas sequências de ação, enfatiza números e palavras-chave (as mesmas que ficam amarelas na legenda) e fecha com chamada direta ("SEGUE AÍ…", "COMENTA AÍ…").

### 1.2 Perfil de voz alvo do Modo Curioso

| Parâmetro | Alvo |
|---|---|
| Gênero / idade aparente | Masculina, 25–35 anos |
| Tom médio | 100–120 Hz |
| Faixa de entonação | ≥ 12 semitons (expressiva) |
| Velocidade | 5,2–5,8 sílabas/s faladas (~190–200 palavras/min depois de comprimir as pausas) |
| Pausas | Nenhuma ≥ 0,8 s depois da compressão (regra: ≥ 0,8 s vira 0,42 s; 0,18–0,8 s vira 0,18 s). **Nunca acelerar com time-stretch** |
| Final de frase | Maioria descendente; sobe em pergunta e suspense |
| Timbre | Quente, médio-grave, dicção clara |
| Sotaque | Português do Brasil, com "tu" e o vocabulário gaúcho no texto; sotaque gaúcho na pronúncia **se** o fornecedor entregar com qualidade (ver 1.4) |
| Emoção | Curioso, animado, irônico leve; ênfase nos números |
| Master | −14 LUFS integrado, pico ≤ −1 dBTP |

### 1.3 O que é proibido
1. **Clonar** a voz das referências ou de qualquer pessoa sem autorização por escrito. Isso inclui subir trechos dos MP4 de referência em qualquer ferramenta de clonagem ou de "voz parecida".
2. Pedir a uma ferramenta que imite uma pessoa específica (locutor, influenciador, ator).
3. Usar voz de plano gratuito ou sem licença comercial.

O que é permitido: criar uma **voz nova** a partir de uma **descrição textual de características gerais** (gênero, idade, timbre, sotaque, ritmo, emoção). Características gerais não são identidade de ninguém.

### 1.4 Opção de voz sintética licenciada

Pesquisa feita em 25/11/2026. **Nenhum dos grandes fornecedores oferece pronta uma voz com sotaque gaúcho.** As vozes pt-BR de catálogo têm sotaque "neutro" (paulista/carioca).

| Opção | Como funciona | Prós | Contras |
|---|---|---|---|
| **A. ElevenLabs Voice Design (recomendada)** | Cria uma voz sintética **nova** a partir de uma descrição em texto (idade, gênero, sotaque, estilo). A voz recebe um ID e vira a voz oficial do canal | Uso comercial da saída nos planos pagos; voz original, não clonada; pt-BR suportado; endpoint `with-timestamps` devolve o tempo de cada caractere, o que resolve o alinhamento de legendas (hoje o Whisper está bloqueado aqui) | O sotaque gaúcho na pronúncia não é garantido: precisa de teste. Exige plano pago e liberar `api.elevenlabs.io` na rede do ambiente |
| B. Locutor gaúcho contratado + voz profissional licenciada | Contrata um locutor real do RS, com contrato que autorize por escrito o uso e a criação de uma voz sintética dele para o canal | Sotaque autêntico garantido; totalmente legal **com autorização** | Custo e prazo de contrato; depende de uma pessoa |
| C. Vozes pt-BR de catálogo (Azure Neural, Google Chirp 3 HD) | Voz pronta de catálogo, ajustada por SSML (velocidade, tom) | Barata, estável, dá o tempo de cada palavra | Sotaque neutro, sem marca regional; menos expressiva para humor |

**Recomendação:** começar pela **opção A**. Se o teste mostrar que o sotaque gaúcho não fica convincente, decidir entre **B** (autenticidade) e aceitar pt-BR neutro com o vocabulário gaúcho só no texto (A ou C). Antes de assinar, confira os termos e o preço do plano no site do fornecedor: eu não verifiquei preços.

**Descrição de partida para o Voice Design** (rascunho, a refinar no teste; o campo costuma funcionar melhor em inglês):

> Brazilian Portuguese male narrator, 28 to 32 years old, from Porto Alegre, Rio Grande do Sul, with a natural gaúcho accent. Warm, medium-low voice, clear diction. Fast, energetic storytelling pace for short social videos, curious and slightly ironic tone, expressive intonation that rises on questions and falls at the end of statements. Clean studio recording, no background noise.

### 1.5 Teste de aprovação da voz (antes do piloto)
1. Gerar de 3 a 5 vozes candidatas a partir da descrição acima.
2. Gravar com cada uma o mesmo texto de teste, com 30–40 s, que contenha: "E se tu acordasse amanhã e…?!", "bah", "guri", "tava", três números com unidade ("4.000 bar", "0,14 segundo", "1.400 quilômetros por hora"), uma pergunta, uma frase de suspense e "Segue aí pra ver na parte dois".
3. Medir cada amostra com `tools/analise/voz.py` contra o perfil da seção 1.2.
4. Escuta humana (você): sotaque, naturalidade, humor, pronúncia dos números.
5. Aprovar uma voz. Registrar aqui o fornecedor, o ID da voz, o modelo, os parâmetros (estabilidade, estilo, velocidade) e a data. **Essa voz passa a ser fixa no canal.**

---

## ID-002 — Marca "Modo Curioso" na camiseta

### 2.1 Decisão
Nas referências, a camiseta dos personagens traz a identificação de outro produtor. **No Modo Curioso, todo personagem oficial veste a marca "Modo Curioso" no peito.** É permanente, faz parte do modelo do personagem e substitui qualquer identificação de terceiros, que nunca aparece.

### 2.2 Especificação da estampa

| Item | Regra |
|---|---|
| Texto | **Modo Curioso**, exatamente assim: duas palavras, **M e C maiúsculos** e o resto minúsculo, sem "@", sem ponto, sem endereço (ID-003). Nunca "MODO CURIOSO", "modo curioso" ou "ModoCurioso" na camiseta |
| Fonte | Arredondada bold, a mesma família dos rótulos do canal: **Nunito ExtraBold** (licença livre OFL) |
| Cores (camiseta média ou escura) | "Modo" em branco-tecido `#f2efe8` + "Curioso" em amarelo `#ffc21f` (mesmo par de cores da marca d'água) |
| Cores (camiseta clara: branca, amarela, creme) | As duas palavras em azul-marinho `#1f2a44` |
| Posição | Centrada no peito, com a linha de base a ~1/3 da distância entre a gola e a barra |
| Tamanho | Largura de 50–60 % da largura do peito na vista de frente (a mesma ocupação da estampa das referências) |
| Acabamento | Aparência de **serigrafia (silk) fosca**: sem contorno, sem brilho, sem sombra projetada, sem degradê; a cor da tinta um pouco menos saturada que a cor pura |

### 2.3 Integração natural ao tecido
1. **A estampa recebe a mesma luz da camiseta.** No rig ela fica **abaixo** da camada de sombra do tronco: quando o tecido escurece, a estampa escurece junto, com o mesmo tom de sombra.
2. **A estampa segue o corpo.** Ela é filha da camada do tronco: mesma posição, rotação, escala e pivô. Ela acompanha a respiração e a inclinação do tronco.
3. **Curvatura do peito:** um arco leve (a palavra "curva" com o peito), mais forte na vista 3/4.
4. **Dobras:** quando o tronco dobra ou torce (correr, agachar, apanhar), a estampa deforma com a malha do tecido (warp do rig), nunca fica "colada" reta por cima.
5. **Oclusão:** braço, mão, objeto ou alça à frente do peito cobrem a estampa normalmente.
6. **Pós-produção:** gradação de cor, grão, bloom e vinheta afetam a estampa como o resto da imagem. Nenhum tratamento especial que a destaque.

### 2.4 Consistência em poses, ângulos e cenas

| Vista | Como a estampa aparece |
|---|---|
| Frente | Completa, 100 % da largura especificada |
| 3/4 | Comprimida no sentido horizontal (75–85 %), deslocada para o lado mais distante, com o arco mais acentuado; as letras do lado distante ficam um pouco menores |
| Perfil | **Não aparece** (nunca um pedaço deformado de letra na borda) |
| Costas | **Sem estampa** (costas limpas) |
| Close de rosto | A parte visível aparece cortada pelo enquadramento, nítida |
| Plano geral | Se a altura da letra ficar abaixo de ~12 px numa tela de 1080 de largura, a estampa vira um bloco simplificado com as mesmas cores, sem tentar desenhar letras ilegíveis |

Para garantir a consistência:
- Existe **um arquivo-mestre vetorial** (`assets/marca/camiseta_modo_curioso.svg`) e variantes pré-deformadas para frente, 3/4 esquerda e 3/4 direita. **Ninguém redigita a marca à mão**, nem em ferramenta de imagem.
- A folha de modelo de cada personagem mostra a estampa nas 4 vistas e é a referência de aprovação.
- No QA, a estampa é conferida em todo plano em que o peito aparece de frente ou em 3/4.

### 2.5 A quem se aplica
- **Todos os personagens oficiais**, protagonistas e elenco fixo, começando pelo **Heitor**.
- Quando o figurino não é camiseta (uniforme escolar, jaleco, túnica, armadura), a marca vai como **patch bordado** no peito, na mesma posição, com as mesmas cores e a mesma fonte, em tamanho proporcional.
- Figurantes e multidões podem usar camiseta lisa ou a marca em tamanho pequeno. Nunca outra marca.
- **Heitor:** a estampa substitui o "selo amarelo `#ffd23f`" da especificação anterior. Na camiseta azul `#3d80d8` fica "Modo" em `#f2efe8` e "Curioso" em `#ffc21f`.

### 2.6 O que é proibido
- Qualquer identificação de outro produtor, @, logo ou marca de terceiros, em qualquer peça, cenário ou tela.
- Distorcer, contornar, colocar brilho ou mudar a fonte da marca.
- Gerar a escrita por IA de imagem sem o arquivo-mestre (é a principal fonte de letras erradas e de inconsistência entre planos).

---

## ID-003 — Grafia oficial da marca

### 3.1 Decisão (confirmada em 25/11/2026)

| Aplicação | Grafia exata | Observação |
|---|---|---|
| **Camiseta dos personagens** (estampa ou patch) | **Modo Curioso** | M e C maiúsculos, o resto minúsculo. Especificação na seção 2.2 |
| **Marca d'água dos vídeos** | **MODO CURIOSO** | Tudo em maiúsculas. Especificação na seção 3.2 |

As cores e as outras especificações já definidas continuam valendo, sem mudança.

### 3.2 Especificação da marca d'água

| Item | Regra |
|---|---|
| Texto | **MODO CURIOSO**, exatamente assim, tudo em maiúsculas, em uma linha |
| Posição | Canto superior direito, alinhada à direita, dentro da área segura (margens sugeridas, a confirmar no teste: ~40 px da borda direita e ~60 px do topo, em 1080×1920) |
| Fonte | Condensada bold, a mesma família das legendas (Roboto Condensed 800) |
| Tamanho | ~30 px de altura de letra em 1080 de largura |
| Cores | "MODO" em branco com 60 % de opacidade; "CURIOSO" em amarelo `#ffc21f` |
| Duração | Fixa do primeiro ao último quadro, em todo vídeo |
| Camada | Acima de tudo (depois das legendas), sem receber gradação de cor, vinheta ou grão |
| Proibido | Animar, trocar de canto, mudar a grafia, trocar a fonte, pôr contorno colorido ou fundo |

### 3.3 Resumo para conferência (QA)
- Camiseta: "Modo Curioso". Marca d'água: "MODO CURIOSO". Marca dentro do cenário: "MODO CURIOSO" (ID-004). Qualquer outra grafia é erro e reprova o plano.
- Nunca aparece identificação de outro produtor (@, logo, nome).

---

## ID-004 — Marca dentro dos cenários

### 4.1 Decisão (aprovada oficialmente em 25/11/2026)
Toda aparição da marca Modo Curioso **dentro dos cenários** usa exatamente:

**MODO CURIOSO**

Tudo em letras maiúsculas. A regra é **permanente** e vale para todos os vídeos e materiais futuros.

### 4.2 Abrangência
Vale para qualquer elemento visual de identificação dentro da cena, por exemplo:
- telas (celular, notebook, TV, monitor, app, notícia, vídeo viral);
- envelopes, fichas, dossiês, crachás, carimbos, documentos "CONFIDENCIAL";
- placas de rua, letreiros, fachadas, faixas, cartazes, outdoors;
- embalagens, rótulos de produto, adesivos, bandeiras e qualquer outro objeto de cena que identifique o canal.

### 4.3 Quadro geral das grafias (ID-002, ID-003 e ID-004)

| Onde a marca aparece | Grafia exata | Decisão |
|---|---|---|
| Camiseta e patch bordado do figurino dos personagens | **Modo Curioso** | ID-002 / ID-003 |
| Marca d'água do vídeo | **MODO CURIOSO** | ID-003 |
| Qualquer elemento dentro do cenário (telas, envelopes, fichas, placas, letreiros, faixas…) | **MODO CURIOSO** | ID-004 |

A única aplicação em maiúsculas e minúsculas é o **vestuário dos personagens** (camiseta e patch). Todo o resto é **MODO CURIOSO**.

### 4.4 Regras de execução
1. O texto é inserido a partir de um arquivo-mestre vetorial (`assets/marca/cenario_MODO_CURIOSO.svg`), com o texto convertido em curvas. Nunca é redigitado à mão nem gerado por IA de imagem.
2. O texto é sempre legível e completo. Se não couber, use um enquadramento ou objeto em que caiba, nunca uma abreviação ("MC", "Modo C."), ponto, "@" ou endereço.
3. A marca recebe a luz, a perspectiva e a gradação da cena como o resto do objeto.
4. Nunca aparece identificação de outro produtor (@, logo, nome) em nenhum objeto de cena.

### 4.5 Controle de qualidade (QA)
- Em todo plano com marca no cenário, confira se ela diz exatamente **MODO CURIOSO**.
- Na conferência automática, o OCR das folhas de contato procura qualquer grafia da marca. "Modo Curioso" só é aceito na camiseta ou no patch; em qualquer outro lugar, o plano reprova.
- Qualquer outra grafia ("Modo Curioso" num objeto de cena, "modo curioso", "ModoCurioso", "MC") **reprova o plano**.
