# Relatório da etapa E5 — ambientação

25–26/11/2026 · Autorizada pelo diretor junto com a aprovação da E4 ("Aprovar e autorizar"). **Aguardando avaliação do diretor. A E6 não foi iniciada.** Nenhum episódio ou história foi produzido. O Heitor rig v2 não foi alterado.

Escopo do plano aprovado (seção 2.5 da proposta):
- árvores com tronco ramificado por algoritmo e copa em aglomerados de folhas, não esferas;
- vegetação baixa e mobiliário urbano;
- comércio (vitrines com produtos genéricos, mesas de bar);
- **espalhamento por semente e com regras (nada flutuando, nada atravessando)**, para evitar áreas vazias e repetição visível.

## O que foi construído (`componentes/ambientacao.py`)
| Grupo | Peças |
|---|---|
| **Árvores** | **Frondosa** (copa larga e densa, tipo árvore de calçada genérica), **ipê** florido amarelo ou rosa (tronco alto, galhos esparsos) e **palmeira** (estipe curvo e folhas pendentes). Tronco e galhos gerados por ramificação recursiva por semente. Copa: aglomerados irregulares (ruído fractal) nas pontas **e no meio dos galhos**, para a copa não ficar oca |
| **Vegetação** | arbusto; vaso com planta |
| **Mobiliário** | banco de praça (concreto e madeira), contêiner de lixo com rodas, sacos de lixo, ponto de ônibus (abrigo com placa "ÔNIBUS"), banca de revistas (letreiro "BANCA", revistas sem texto), cones, bicicleta |
| **Comércio** | mesas de bar com cadeiras plásticas (cores lisas, sem marca), engradados, bancada de frutas |

Os aglomerados de folhas são **4 malhas-protótipo instanciadas**: no quarteirão, 399 instâncias variando escala, giro e cor.

### Regras de espalhamento
| Componente | O que faz |
|---|---|
| `arborizacao` | Planta árvores nos canteiros da rua e **abre canteiros novos** ao longo do meio-fio (passo de ~8 m). Só abre sobre calçada livre (nada em cima: poste, toldo, marquise). **Se a copa atravessar** uma fachada, varanda, toldo, poste ou carro, tenta uma árvore menor (75 % e depois 60 %); se ainda atravessar, põe um arbusto ou deixa o canteiro vazio |
| `ambientacao` | Espalha mobiliário em faixas da calçada (junto ao meio-fio ou junto às fachadas, virado para a rua), respeitando:<br>• apoio real (raio para baixo, só na altura da calçada);<br>• coluna livre (raio para cima);<br>• **áreas livres** (lugar do Heitor e frente das câmeras);<br>• distância mínima entre peças;<br>• **teste de colisão por triângulos (BVH)**: se atravessar algo, sorteia outro lugar |
| `mesas_bar` | Acha as lojas cujo letreiro diz LANCHONETE ou PADARIA e põe mesas e engradados na calçada em frente |
| `arvore`, `mobiliario` | Peça isolada, posicionada à mão |

**QA da cena: novo teste "nada atravessando"** (`nucleo/qa_cena.py`). Depois de tudo montado, confere de novo cada peça de ambientação contra a geometria vizinha. O chão não conta: tudo com topo até 20 cm (pista, calçada, piso tátil, folhas). Bordas de canteiro contam.

## Folhas (`testes/e5/E5_folha_arvores.jpg`, `E5_folha_mobiliario.jpg`)
Árvores: frondosa (duas sementes), ipê amarelo, ipê rosa, palmeira e arbusto. Mobiliário e comércio: as 11 peças. 1920×1080, render de ~39 s cada. **Nada flutuando, nada atravessando.**

## Cenas de prova: o quarteirão da E4 ambientado
`receitas/e5_quarteirao.json`. Os volumes provisórios da E0 (banco e vaso) saíram. O espalhamento colocou:
- **10 árvores**: 2 em canteiros da rua e 8 em canteiros novos;
- **5 arbustos**, **8 vasos**, **4 bancos**, **6 grupos de sacos de lixo**, **2 contêineres**, **2 bicicletas**;
- **1 ponto de ônibus**, **1 grupo de cones**, **1 bancada de frutas**;
- **4 mesas de bar e 2 pilhas de engradados**, em frente à lanchonete e à padaria.

São 3.947 objetos no total.

Imagens:
- `E5_cenas.png` (as 4 lado a lado);
- cada cena em 1080×1920: `E5_calcada_tarde.jpg`, `E5_esquina_tarde.jpg`, `E5_rua_tarde.jpg` (**vista nova**, da calçada da direita), `E5_calcada_noite.jpg`;
- `E5_antes_depois.png` (E4 × E5).

### Tempo real de render (4 núcleos, sem GPU, 1080×1920)
| Placa | Montagem (com testes de colisão) | Total | Camada "meio" |
|---|---|---|---|
| calçada · tarde | 38 s | 236,3 s | 106,9 s |
| esquina · tarde | 44 s | 206,4 s | 65,5 s |
| calçada da direita · tarde | 38 s | 217,3 s | 98,6 s |
| calçada · noite | 35 s | 241,3 s | 114,7 s |

**As 4 placas ficaram dentro da meta de 3–5 min**: média de 225 s (3,8 min), máximo de 241 s. Esta é a etapa mais pesada até agora: na E4 a média foi 176 s. Ver "Problemas encontrados" para como saímos de 320 s.

### Medidas de cor (alvos do skill: brilho 46–56 %, saturação 35–46 %, vinheta 57–66 %)
| Cena | Brilho | Saturação | Vinheta | Sombras (a, b) |
|---|---|---|---|---|
| calçada · tarde | 46,8 ✅ | 33,2 (−1,8) | 79,0 ⚠️ | +9, −12 ✅ |
| esquina · tarde | 45,6 (−0,4) | 27,9 ⚠️ | 70,8 ⚠️ | +8, −19 ✅ |
| calçada da direita · tarde | 46,6 ✅ | **38,9 ✅** | **59,2 ✅** | +8, −19 ✅ |
| calçada · noite | 30,7 | 48,1 | 75,7 | +14, −20 ✅ |

**A vista nova da calçada da direita é a primeira cena diurna, entre as dos relatórios finais da E1 à E5, dentro dos três alvos** (brilho, saturação e vinheta). As copas coloridas (ipê) e a luz de lado ajudam. A saturação da calçada subiu de 31 % para 33 % com as árvores.

## QA automático
| Teste | Resultado |
|---|---|
| Nada flutuando | **0** nas 4 cenas e nas 2 folhas |
| **Nada atravessando** (46 peças conferidas por cena) | **0** nas 4 cenas e nas 2 folhas |
| Textos | **Nenhum fora da regra.** Novos: "ÔNIBUS" e "BANCA" (palavras comuns). Revistas e mesas sem texto nem marca |
| OCR | Não executado (não há OCR no ambiente); a conferência é feita na fonte |

**O teste "nada atravessando" pegou 5 casos reais durante o desenvolvimento**, todos corrigidos:
1. duas copas de árvore se encostando;
2. cones dentro da banca;
3. um vaso dentro de um canteiro de árvore, porque o espalhamento aceitava apoio de até 30 cm e a borda do canteiro tem 23 cm;
4. um vaso encostado na borda de um canteiro;
5. o tronco plantado no solo do canteiro. Este é intencional, e agora fica registrado no objeto.

## Área vazia
| Cena | E4 | E5 |
|---|---|---|
| calçada · tarde | 8,5 % | 8,9 % |
| esquina · tarde | 25,3 % | 25,5 % |

**A métrica não mudou de forma significativa.** Na calçada, as peças novas ocupam áreas que já tinham detalhe (calçada portuguesa, fachadas). Na esquina, nada da E5 aparece no enquadramento: o canteiro e as calçadas dessa vista ficaram livres pelas regras. Como registrado na E3, essa métrica mede variação fina de luminância e não captura bem "riqueza de cena". **A avaliação de riqueza aqui é visual** (`E5_antes_depois.png`), não medida.

## Determinismo e integridade
| Teste | Resultado |
|---|---|
| Mesma receita montada duas vezes | **Geometria idêntica** (3.947 objetos), mesmo com o espalhamento e as tentativas de colocação |
| Outra semente | Outras árvores e outro mobiliário |
| Cache | 2ª chamada: HIT em 2,3 s |
| Assinatura de `personagens/heitor/rig_v2/`, `docs/IDENTIDADE_OFICIAL.md`, `skills/` | **Idêntica** (`068bf373…8342`); nenhuma alteração pendente |
| Verificação F1 do rig | 6/6 vistas OK |
| Paleta do Heitor no quadro | 191.418 pixels, **100 % idênticos** ao rig sozinho |
| ID-001 a ID-004 | Inalteradas |

## Problemas encontrados e corrigidos
1. **Render de 320 s** na 1ª rodada, acima da meta. Havia duas causas:
   - o material de folha usava espalhamento subsuperficial, caro na CPU. As copas da E5 agora usam 0; o material da E1 continua igual.
   - a montagem levava 60–68 s, porque o teste de colisão recalculava a geometria dos ~4.000 objetos a cada peça. Entrou um cache das caixas e BVH dos objetos parados, e os aglomerados passaram a ter 642 vértices em vez de 2.562.
   
   **Resultado: montagem de 35–44 s e render de 206–241 s.**
2. **Árvore logo à frente da câmera da calçada:** escurecia o quadro (brilho 38,9 %) e a copa escura contava como "vazio" (23 %). Entrou uma área livre de árvores na frente da câmera.
3. **Banca logo à frente da câmera da calçada da direita:** quadro bloqueado. Entrou uma área livre também para essa câmera.
4. **Aglomerados facetados e copa "pirulito"** (só no topo). Menos ruído fino, aglomerados no meio dos galhos e tronco mais baixo na frondosa.
5. **Folha de mobiliário cortando peças** nas bordas. Câmera mais afastada.
6. **Os 5 casos de "atravessando"** listados no QA.

## Limitações (registradas, não escondidas)
1. **Árvores estilizadas.** As copas são aglomerados lisos, sem folhas individuais nem luz atravessando. Leem bem de média e longa distância e combinam com o estilo, mas de perto parecem "algodão". Folhas individuais custariam muito tempo de render em CPU.
2. **Árvores e fiação:** os fios são curvas, não malhas, e ficam fora do teste de colisão. Uma copa pode cruzar os fios, como acontece muito na vida real.
3. **As áreas livres são dadas na receita** (lugar do Heitor, frente das câmeras). Portas de loja e garagens ainda não são detectadas sozinhas: uma peça pode ficar em frente a uma porta.
4. **Mobiliário simples:** contêiner, banco e banca são volumes com poucos detalhes. A bicicleta lê bem de longe.
5. **A ambientação aumentou o tempo de render** (média de 3,8 min). Cabe na meta, mas sobra pouca folga para cenas mais cheias. A próxima otimização seria render das copas em camada separada com menos amostras.
6. **O Heitor não recebe a luz do cenário** (sombra das árvores, luz das vitrines). Corrigir isso exige uma extensão do rig, só com aprovação.
7. **Saturação da esquina de dia** (27,9 %) continua abaixo do alvo, como nas etapas anteriores.

## Como reproduzir
```
.venv/bin/python cenografia/testes/e5_testes.py                # folhas, 4 placas (≈ 4 min cada na 1ª vez), QA, área vazia, determinismo, integridade
.venv/bin/python cenografia/testes/e5_testes.py E5_1_folhas    # só as folhas
```

## Próxima etapa (só com aprovação): E6 — cena de prova
Pelo plano aprovado: a "rua de bairro" montada por receita, em 3 horários, com o **Heitor v2 andando** e câmera em paralaxe. **É um vídeo de teste, não uma história.** Será o primeiro vídeo com toda a cenografia junta (céu, rua, prédios, veículos e ambientação).
