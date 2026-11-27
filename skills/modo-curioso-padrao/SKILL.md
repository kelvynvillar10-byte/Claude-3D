---
name: "modo-curioso-padrao"
description: "Padrão de produção dos vídeos \"E se…?\" do Modo Curioso, medido em 20 referências. Use ao roteirizar, animar, editar ou revisar qualquer vídeo do canal."
---

# Padrão Modo Curioso

Base: 21 vídeos de referência medidos quadro a quadro (≈36 min, ≈105 mil quadros; o v21 é a referência de ANIMAÇÃO de personagem: câmera por fluxo óptico, cortes, cor em Lab, OCR das legendas, áudio EBU R128) + revisão visual de 1 quadro por segundo. Números = mediana (faixa típica p25–p75). Guia visual com gráficos: https://claude.ai/artifact/D6R7BkymKEDAH7QLAZFYgt

## 0. Regras fixas do canal (valem sempre, acima de tudo)
- Nada de personagens, logos, marcas ou trechos com direito autoral. As referências citam anime, jogos e pessoas reais — nós NÃO. Não copiar personagem nem arte de terceiros: recriar no nosso estilo. Exceção decidida pelo diretor no EP02: a NARRAÇÃO pode citar o nome de um produto como fã ("PS5", "GTA 6"); na IMAGEM nunca há logotipo, arte, fonte, mapa ou design de terceiros (console, controle, jogo e cidade sempre genéricos, desenho próprio).
- Nunca usar foto real de criança.
- Temas de guerra só em tom sério.
- **Identidade oficial (fonte da verdade: `docs/IDENTIDADE_OFICIAL.md` no repositório Claude-3D; ver seção 0.1).**
- Marca d'água em todo vídeo novo: exatamente **"MODO CURIOSO"**, tudo em maiúsculas, no canto superior direito ("MODO" branco com 60 % de opacidade, "CURIOSO" em amarelo #ffc21f, fonte condensada, ~30 px em 1080 de largura), fixa do início ao fim.
- Camiseta de TODO personagem oficial: estampa exatamente **"Modo Curioso"** (M e C maiúsculos). Nunca o @ de outro produtor nem qualquer marca de terceiros. Marca DENTRO do cenário (telas, envelopes, fichas, placas, letreiros, faixas): exatamente **"MODO CURIOSO"**, tudo em maiúsculas (ID-004).
- Efeitos sonoros baixos, por baixo da voz.
- Voz (regra de 26/11/2026): pausas dirigidas por intenção na pós-produção (`narracao/pos/`): suspense e revelação até 0,7 s, surpresa até 0,5 s, ação até 0,15 s, nunca ≥ 0,8 s; pausa sem pontuação > 0,25 s vira 0,10 s. NUNCA acelerar com rubberband (gera eco/voz duplicada) nem mudar o tom; a velocidade se ajusta na geração.
- Personagens reutilizáveis entre temas, trocando só a roupa.

## 0.1 Identidade oficial (decisões ID-001 a ID-004, de 25/11/2026 — prevalecem sobre qualquer instrução antiga)
| ID | Decisão |
|---|---|
| ID-001 | Narração com voz sintética licenciada, de características semelhantes às referências, sem clonar a identidade vocal de ninguém. Perfil alvo e teste de aprovação em `docs/IDENTIDADE_OFICIAL.md`. |
| ID-002 | Todo personagem oficial veste a estampa "Modo Curioso" no peito: Nunito ExtraBold, serigrafia fosca, centrada, com 50–60 % da largura do peito. Em camiseta média ou escura, "Modo" #f2efe8 + "Curioso" #ffc21f; em camiseta clara, as duas palavras em #1f2a44. A estampa recebe a sombra do tecido e segue o tronco e as dobras; completa de frente, comprimida em 3/4, ausente de perfil e nas costas. Em figurino que não é camiseta, vai como patch bordado no peito. Sempre a partir do arquivo-mestre vetorial, nunca redigitada nem gerada por IA de imagem. |
| ID-003 | Grafia: camiseta = **"Modo Curioso"** (M e C maiúsculos); marca d'água = **"MODO CURIOSO"** (tudo maiúsculo). Qualquer outra grafia é erro. |
| ID-004 | Marca dentro dos cenários (telas, envelopes, fichas, placas e elementos visuais de identificação): sempre **"MODO CURIOSO"**, tudo em maiúsculas, a partir do arquivo-mestre, legível e sem abreviação. Permanente. A única aplicação em maiúsculas e minúsculas é o vestuário dos personagens ("Modo Curioso"). |

## 1. Formato
- Vertical 1080×1920, 30 qps (60 opcional).
- **Duração (diretriz permanente, 26/11/2026):** formato principal de 1 a 2 min (60–120 s); vídeo longo só como formato especial, quando o tema justificar. Definir pela força do tema e pela necessidade narrativa: não prolongar artificialmente, não cortar informação importante só para caber em 2 min. (Referências medidas: 81–141 s, mediana 91 s.)
- ~47 planos por vídeo; 31 cortes por minuto (30–33).

## 2. Roteiro
- **0–1 s, gancho.** Duas aberturas:
  - Parte 1: "E se tu acordasse amanhã e realmente ___?!" (8 de 20). A frase vem quebrada em 3–5 legendas dentro do 1º segundo.
  - Continuação: ação já em andamento com nome próprio ("O Pedro acordou sendo de borracha…", "O Otávio fugiu da cadeia…") ou "Tu é o Pedro e tem o elemento ___" (12 de 20).
- Narração em 2ª pessoa ("tu", "tua mão") + um personagem nomeado vivendo a situação.
- **Cada poder vira ciência com NÚMERO REAL mostrado na tela**: densidade 0,92, 194 dB, 1,00 atm, 21 % O₂, 120 m/s, tempo de reação 0,16 s, 3 mm, 700 kg, 4.000 bar, ×20.000. Um conceito a cada 8–12 s.
- Contraste "no filme × na vida real".
- Gag físico a cada 10–15 s; rival/antagonista no meio; clímax perto de 70–75 %.
- Foreshadowing: sombra gigante na parede, detalhe que só se explica na próxima parte.
- **Final (últimos 5 s):** "Segue aí" (18 de 20) + gancho de série "pra ver ___ na parte dois" (14 de 20) e/ou pergunta para comentário "Comenta aí: qual ___ tu queria ter?" (7 de 20).
- Narração rápida e contínua: ≈195 palavras/min, sem pausas longas.

## 3. Personagens
- 2D chapado (ou toon com cara de 2D): cores lisas, 1 tom de sombra, contorno fino escuro opcional; cabeça grande e redonda; olhos pequenos escuros com brilho que viram brancos e arregalados no susto; SOBRANCELHA GROSSA carrega a expressão; pálpebra meio fechada = tédio/convencido; boca simples (linha, "o", aberta).
- Animação base: pose a pose com pose segurada; SEM sincronia labial (boca fixa no plano; a fala vai na legenda); piscada ocasional; o movimento vem muito da câmera e dos efeitos.
- Nível acima (referência v21, a mais animada: movimento local 3× a mediana, 19 % da tela em movimento): bonecos 2D recortados com membros girando nas juntas e interpolação suave com easing, animados NO 1 (todo quadro muda, nada de quadro repetido).
  - Sempre vivo: mesmo parado, respira e balança a cabeça de leve.
  - Expressão troca DENTRO do plano nas batidas da fala (surpreso → olhos apertados "><" → bravo), 2–3 trocas por close.
  - Toda ação tem antecipação → golpe → overshoot e assentamento; ciclos completos de corrida.
  - Soco termina em quadro de impacto (estilhaços brancos sobre azul-marinho, 1–2 quadros).
  - Use esse nível nos momentos de poder e ação; no resto, o nível base basta.
- Antagonista pode ter mais detalhe que o herói. Multidões = mesmo modelo variando roupa, cabelo e pele.
- Elenco do canal — **Heitor (v3)**: 10–12 anos, ~4 cabeças de altura, cabeça redonda, SEM bochecha rosada, cabelo liso castanho-escuro com franja lateral (#3a2316 / sombra #24140a / brilho #5c3a25), olhos castanhos (#6a3d20), pele #ffd9c2 (sombra #efb594), camiseta azul #3d80d8 (sombra #2b61b0, gola #2855a0) com a estampa "Modo Curioso" no peito ("Modo" #f2efe8, "Curioso" #ffc21f, Nunito ExtraBold), calça jeans #34507f (sombra #243a60) com barra dobrada #4a6b9f, tênis branco #f6f4f0 com faixa azul. Vistas: frente, 3/4, perfil, costas; expressões: neutro, feliz, surpreso, triste, assustado, preocupado, bravo, pensativo, sonolento.
- **Rig oficial do Heitor: v2.2** (v2 aprovado em 25/11/2026; v2.1 ombros arredondados e v2.2 braço encaixado um pouco abaixo da linha do ombro, para o ombro não subir — ambos aprovados em 27/11/2026), em `personagens/heitor/rig_v2/` no repositório Claude-3D. É vetor 2D por código (skia-python), com esqueleto, 4 vistas, 5 dedos por mão e rosto paramétrico. Nunca redesenhar o Heitor nem gerá-lo por IA de imagem: sempre posar o rig. Regras de animação verificadas por script:
  - Cotovelo só dobra no sentido anatômico. De perfil, o antebraço vai para a frente. De frente ou de costas, um cotovelo acima do ombro nunca aponta para a cabeça; aceno, "mãos ao alto" e punho erguido têm o antebraço PARA CIMA. Use a IK com escolha automática do cotovelo.
  - Pé de apoio plantado (deslize zero) em caminhada, corrida e parada.
  - Troca de desenho de olho (pequeno escuro ↔ arregalado branco) escondida por uma piscada; troca de boca com a boca quase fechada.
  - Objeto segurado preso ao ponto de pega da mão. Com a palma para a câmera, o objeto aparece NA FRENTE da mão.
  - Estampa "Modo Curioso" nunca espelhada (inclusive nas vistas viradas para a esquerda).
  - No cenário 3D: fundo estático do Blender + Heitor 2D posicionado e escalado por âncoras 3D → 2D (altura 1,40 m), com sombra de contato no chão.
- Elenco do canal — **Juca e Jandira** (adultos, casal do EP02; aprovados em 27/11/2026), rig adulto **v1.1** em `personagens/adultos/` (mesmo rig do Heitor, sem alterá-lo: cópia própria por personagem; 5 cabeças de altura; braço encaixado 0,10 H abaixo da linha do ombro). Juca: ~28 anos, pele morena, cabelo crespo curto preto, barba rala, camiseta verde #2f8f5f com "Modo Curioso", moletom cinza, chinelo; 1,75 m em cena. Jandira: ~27 anos, cabelo longo ondulado castanho-escuro com risca lateral, cílios, camiseta roxa #7a55c7 com "Modo Curioso", jeans, tênis branco com faixa roxa; 1,65 m em cena. Expressões extras: vidrado, irritada, desconfiada; rosto com olheira e barba por fazer (0–1). Poses e objetos genéricos do EP02 em `personagens/adultos/poses.py`.

## 3.1 Animação dinâmica (diretriz permanente do diretor, 27/11/2026)
- **Princípio:** aparência de animação 3D cinematográfica, com personagens vivos, câmera dinâmica e acontecimentos acompanhando a narração. Em cada cena, algo está acontecendo; piscada e respiração sozinhas não bastam.
- **Personagens:**
  - caminhada com ciclo completo, corrida, mudança de direção e fuga;
  - braços, pernas, tronco e cabeça naturais;
  - reações (surpresa, medo, curiosidade, susto, alívio) e olhar dirigido aos objetos;
  - interação física com objetos e cenário; mudança de postura e deslocamento no ambiente.
  - Ninguém congelado na mesma pose por vários segundos. Toda ação tem início, desenvolvimento e conclusão, sem repetição mecânica.
- **Câmera:**
  - nunca parada a cena inteira;
  - travelling lateral e frontal, aproximação e afastamento, zoom controlado, câmera acompanhando o personagem;
  - mudança de ângulo, câmera baixa, plano aberto, close expressivo, movimento ligado à ação.
  - A câmera conta a história.
- **Cenário vivo** quando fizer sentido: tecido ao vento, poeira e partículas, água ondulando, vegetação balançando, objetos reagindo a impacto, luz e sombra acompanhando os acontecimentos. Nada de movimento aleatório só para preencher.
- **Ação e narração conectadas:** cada trecho falado tem representação visual. Perigo = ver o perigo se aproximando; descoberta = reação visual; ação = acompanhar o desenvolvimento.
- **Ritmo e montagem:** dinâmico, sem cortes aleatórios. Alternar planos rápidos (ação/impacto), médios (desenvolvimento), closes (emoção/descoberta) e abertos (ambiente/escala). Referência de **1,5 a 2 s por plano** nas sequências dinâmicas.
**Aprovado pelo diretor em 27/11/2026: a cena de prova `producoes/teste_animacao_dinamica/` é o PADRÃO de animação a partir do EP02** ("Ficou muito melhor… quero isso mesmo… essa ficou boa, aproveite"). O que vale:
- As imagens acompanham a narração conforme ela passa. Pode trocar de cena rápido e voltar a uma cena anterior.
- Em todo plano há **aproximação de câmera, expressões e movimentos** dos personagens.
- Efeitos ligados à ação: zoom brusco, tremida no impacto, borrão de movimento, poeira, sombra que passa.
- Ferramentas: `producoes/teste_animacao_dinamica/codigo/atuacao.py` (trajeto sem pé deslizando, virar, pulo, tropeço, câmera que acompanha sem revelar a borda, poeira) e o QA `qa_teste.py` (movimento por quadro, câmera, mapa fala → imagem, cotovelos, pés).
- Linha de base aprovada (mesmo trecho do EP01): 13 planos em 19,7 s, mediana de 1,35 s, câmera em movimento em 100 % dos quadros, 91 % dos quadros com ação visível.

**Reforço do diretor (27/11/2026), vale para o próximo vídeo:**
- **Movimento o tempo todo.** Nenhum personagem estático: em todo plano o personagem está fazendo alguma coisa (andando, correndo, reagindo, olhando, gesticulando, interagindo); respiração e piscada não contam como ação. A câmera também está em movimento em todos os planos.
- **O vídeo acompanha a narração, palavra a palavra.** Tudo o que a narração diz aparece na tela no momento em que é dito:
  - objeto citado: é mostrado;
  - ação descrita: acontece;
  - perigo: se aproxima;
  - número: vira rótulo.
- **Mapa fala → imagem:** a decupagem é feita a partir dos tempos das palavras (`voz_palavras.json`). Cada termo-chave do roteiro recebe um evento visual.
- **Metas do QA para o próximo vídeo:**
  - 100 % dos planos com câmera em movimento;
  - personagem em ação em todos os planos em que aparece;
  - nenhuma pose parada por mais de ~1 s;
  - cada termo-chave da narração com evento visual em até ±0,3 s da palavra;
  - planos de 1,5–2 s nas sequências dinâmicas.
- **Medida do EP01 (linha de base, para comparar):**
  - 41 planos; locomoção em 1; troca de expressão dentro do plano em 6;
  - travelling/pan em 3 dos 34 planos com cenário; zoom mediano de 10 % no plano;
  - só 3 planos entre 1,5 e 2 s, e 12 acima de 3 s;
  - cenário parado (só vento, sombra e pata em 2D).

## 4. Cenários
- Ambientes com perspectiva real e materiais (madeira, tijolo, azulejo, grama, asfalto, pedra) e MUITOS objetos de contexto (prateleiras, letreiros, fios, plantas, carros, toldos). Profundidade com desfoque no fundo, névoa quente ao longe e primeiro plano desfocado às vezes.
- Inserts científicos em fundo escuro (azul-marinho ou roxo) com bokeh e partículas: átomos como esferas ou blocos com a letra (H azul, O vermelho), moléculas, neurônios, raio-x holográfico azul, câmera térmica (roxo → laranja → amarelo, com escala e mira), visão noturna verde, corte de pele/estômago, Terra e Lua no espaço.

## 5. Luz, sombra e cor (alvos medidos)
- Brilho médio 53 % (46–56); saturação 39 % (35–46); contraste 17 %.
- Luz MOTIVADA e quente: sol dourado rasante pela janela, abajur, poste, tocha. Noite azul-roxa com uma fonte laranja.
- Sombras com tinta roxo-azulada (Lab a ≈ +7, b ≈ −10); altas luzes quentes (b ≈ +19).
- Vinheta forte: cantos com ~62 % do brilho do centro (57–66 %).
- Bloom nas luzes, poeira/partículas no feixe de luz, grão de filme leve.

## 6. Câmera (nada fica parado: só 7,5 % dos planos sem movimento)
| Movimento | % dos planos | Valores |
|---|---|---|
| Push-in lento | 62 % | 5,9 %/s (3,3–9,8); total 9 % no plano (5,5–15) |
| Tilt | 24 % | 16 % da altura |
| Pan | 22 % | 14 % da largura |
| Crash-zoom | 13 % | +40 % ou mais no plano |
| Chicote (whip) | 11 % | 0,13 s; 8 por minuto |
| Giro (roll) | 10 % | ~6° |
| Pull-out | 10 % | −7 %/s; total −13 % |
| Pull-out forte (revelação) | 6 % | −40 a −80 % no plano |
- Curva de velocidade: ease-out em 52 % dos planos, ease-in-out em 26 %, ease-in em 13 %.
- Punch-zoom: +7 % em 0,18 s (forte: até +75 %), 5 por minuto.
- Tremida curta de impacto: 28 por minuto, amplitude ~1,4 % do quadro, 0,25–0,6 s.
- "Mergulho de escala": zoom contínuo enorme (×20 ou mais) da mão até a pele, as células e os átomos.

## 7. Cortes e ritmo
- Plano mediano 1,7 s (1,15–2,33); 10 % abaixo de 0,73 s e 10 % acima de 3,2 s.
- Episódio de AÇÃO de série (v21): mais rápido, 52 cortes/min e plano mediano 1,0 s.
- Ritmo constante (≈0,5 corte/s), um pouco mais rápido entre 50 % e 80 % do vídeo e mais calmo nos últimos 10 %.
- Primeiro corte em ~1,9 s.
- Transições: corte seco (dominante), chicote, fusão rápida (1,7/min), flash branco raro (0,9/min). Quadros segurados ~5/min em momentos de suspense.

## 8. Efeitos que se repetem
- Rótulo com linha-guia e número grande ("160", "80 kg", "0,16 s", "1,00 atm"), branco ou amarelo, fonte arredondada.
- Medidas: régua, seta de força ("+10", "×8"), contador (tempo, dB, °C), barra de medidor.
- Partículas: poeira dourada, faíscas, bolhas, vapor, letras flutuando sobre objetos.
- Poderes (v21): grito = anéis de choque transparentes saindo da boca + rachaduras se espalhando no vidro quadro a quadro; levitação = contorno brilhante e corpo subindo devagar; raio-x azul; gelo; feixes de energia. Vilão gigante pode ser 3D detalhado contracenando com heróis 2D.
- Personagem "fantasma" translúcido azul para comparar (pessoa média, intangível, invisível).
- Quadro de impacto: silhuetas claras sobre linhas radiais em 1–2 quadros.
- Inset redondo (lupa) mostrando detalhe; tela dividida ao meio com linha de luz para comparar.
- Telas: celular na mão com app de vídeo e views; ficha "CONFIDENCIAL"; notebook com loja.

## 9. Legendas
- CAIXA ALTA, fonte condensada bold (ex.: Roboto Condensed 800), branca, contorno escuro #1a110c com ~12 % do tamanho da letra + sombra deslocada.
- 2–3 palavras (média 2,9); 0,8 s por bloco (0,63–1,0); ~68 blocos por minuto; troca exatamente na fala.
- Letra com ~3 % da altura da tela; bloco com ~46 % da largura.
- Posição: terço inferior é o padrão (centro a 70–80 % da altura em 41 % das legendas; 60–70 % em 24 %). Sobe para 15–30 % (topo) quando o rosto ou a ação estão embaixo. Nunca cobrir o rosto.
- Destaque: uma palavra-chave ou número em amarelo-dourado #ffc21f em ~42 % dos blocos.
- Entrada: pop sutil de 97 % para 100 % em 2 quadros (sem quique exagerado).
- Falas de personagem entre aspas.

## 10. Áudio
- −14 LUFS integrado (−14,3 a −14,0); LRA ~3,7 LU; pico −0,8 dBTP.
- Graves ~29 % da energia; banda de voz ~44 %.
- ~1,6 eventos sonoros por segundo (whoosh, impacto, pop em cada corte e efeito), sempre baixos por baixo da voz.
- Narração contínua com música de fundo e ducking.
- Voz oficial (ID-001): voz sintética LICENCIADA, criada a partir de uma descrição de características gerais (masculina, 25–35 anos, médio-grave e quente, ~111 Hz, rápida ~5,5 sílabas/s, expressiva, português do Brasil com "tu" e vocabulário gaúcho). NUNCA clonar a voz das referências ou de qualquer pessoa sem autorização por escrito. Fornecedor recomendado: ElevenLabs Voice Design, sujeito ao teste de amostra. Candidata atual (26/11/2026, escolhida pelo diretor, ainda não aprovada como ID-001): MiniMax `Portuguese_CaptivatingStoryteller`, gerada pelo diretor no site MiniMax Audio e finalizada em `narracao/pos/` (−16 LUFS na narração; mix final −14 LUFS). EP02: narração com a voz do próprio diretor (autorizada por ele), tratada com o preset `narracao/pos/preset_ep02_voz_diretor.json` (`NARRACAO_PRESET=`), que contém os agudos da voz grave.

## 11. Checklist antes de entregar
1. Gancho dentro do 1º segundo, quebrado em 3–5 legendas.
2. Pelo menos 6 números reais na tela, cada um com rótulo grande.
3. Plano mediano entre 1,5 e 2,0 s; nenhum plano parado sem câmera, salvo suspense.
4. Push-in na maioria dos planos, com ease-out.
5. Sombras roxo-azuladas, luz quente motivada, vinheta, grão.
6. Legendas: 2–3 palavras, amarelo em ~4 de cada 10, sem cobrir rosto.
7. −14 LUFS, efeitos baixos, voz sem aceleração.
8. Marca d'água exatamente "MODO CURIOSO" (maiúsculas) + camisetas com exatamente "Modo Curioso" (M e C maiúsculos) + toda marca dentro do cenário com exatamente "MODO CURIOSO" (ID-004).
9. Nenhum personagem, logo ou pessoa real de terceiros.
10. Final com "Segue aí" + gancho de parte 2 ou pergunta para comentário.
11. Personagem: só o rig oficial (Heitor v2), 0 cotovelos invertidos (`verificar_cotovelos.py`), pé de apoio sem deslize, estampa legível de frente e em 3/4.
12. Marca dentro do cenário ("MODO CURIOSO") nunca cortada nem coberta pelo personagem ou por objetos: oclusão medida quadro a quadro = 0.
