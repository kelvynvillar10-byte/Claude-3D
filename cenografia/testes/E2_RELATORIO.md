# Relatório da etapa E2 — ruas e calçadas (quarteirão modular)

25/11/2026 · Autorizada pelo diretor após a aprovação da E1. **E2 APROVADA pelo diretor em 25/11/2026; E3 autorizada.** Nenhum episódio ou história foi produzido. O Heitor rig v2 não foi alterado.

Cena de teste: `receitas/e2_quarteirao.json`: um quarteirão de bairro com um trecho de rua, um cruzamento e a continuação da rua depois dele. **Os prédios continuam provisórios** (volumes da E0); prédios detalhados são a E3.

## O que foi construído
| Componente | Onde | O que tem |
|---|---|---|
| `rua_trecho` | `componentes/rua.py` | Asfalto com detalhe (pedrisco, manchas, fissuras, **óleo no centro das faixas**), remendos, faixa dupla amarela ou tracejada branca, tampas de bueiro, sarjeta, meio-fio em segmentos com **rebaixo de garagem e rampa**, **calçada por lote** (cada casa com seu piso: portuguesa, ladrilho hidráulico, concreto), piso tátil em alguns lotes, canteiros elevados, bocas de lobo com grelha, folhas secas e mato nas juntas |
| `cruzamento` | idem | 4 esquinas com **meio-fio arredondado** (raio 2,2 m), faixas de pedestre (zebra) nos 4 lados, linhas de retenção, faixa amarela de alerta no piso, braços da rua transversal |
| `poste_concreto` | idem | Poste cônico com cruzeta e isoladores, braço com luminária LED (acende de noite: grupo de luz "artificial"), transformador opcional, **número** pintado voltado para a rua |
| `fiacao` | idem | Cabos pendurados entre postes da mesma linha (3 de energia + 2 de telefonia/internet) e rolos de sobra de cabo |
| `semaforo` | idem | Veicular (vermelho/amarelo/verde, lente acesa emite luz) + foco de pedestre |
| `placa_rua` | idem | Placas azuis com nomes **inventados** ("R. DAS JABUTICABAS", "R. VAGALUME") |
| `placa_regulamentacao` | idem | Velocidade máxima (número) e proibido estacionar; sem marcas |
| `hidrante`, `lixeira_poste` | idem | Mobiliário de calçada |
| QA da cena | `nucleo/qa_cena.py` | Roda no Blender antes do render e vai para o manifesto da placa (ver abaixo) |
| Texto 3D | `nucleo/geometria.py` (`texto`) | Fonte oficial do repositório (Roboto Condensed ExtraBold) |
| Materiais | `nucleo/materiais.py` | `asfalto(detalhe=…, faixas_x=…)` e `concreto(detalhe=…)`. Com o valor padrão 0, ficam **iguais aos da E1**, que não muda |

## Cenas de prova (`testes/e2/`)
`E2_cenas.png` (as 5 lado a lado) e cada uma em 1080×1920: `E2_calcada_tarde.jpg`, `E2_esquina_tarde.jpg`, `E2_de_cima_tarde.jpg`, `E2_calcada_noite.jpg`, `E2_esquina_chuva.jpg`. O Heitor rig v2 aparece de frente, parado, só para dar escala. A vista de cima é de conferência do piso, sem personagem.

`E2_folha_componentes.jpg`: o kit enfileirado numa calçada, com rótulos.

### Tempo real de render (4 núcleos, sem GPU, 1080×1920, amostras 4/16/24/24/16)
| Placa | Tempo | Mais lenta |
|---|---|---|
| calçada · tarde | 155,6 s | meio 84,0 s |
| esquina · tarde | 130,8 s | meio 58,9 s |
| de cima · tarde | 169,9 s | meio 119,8 s |
| calçada · noite | 161,3 s | meio 89,2 s |
| esquina · chuva (piso molhado) | 131,7 s | meio 61,5 s |
| folha de componentes (1920×1080, 2 camadas) | 63,8 s | — |

**As 5 placas ficaram dentro da meta de 3–5 min:** média de 150 s (2,5 min) e máximo de 170 s, com 1.148 objetos por cena. A placa da vista de cima foi medida numa rodada isolada (mesmo código); as outras quatro, na rodada final.

### Medidas de cor (mesmas fórmulas da auditoria; alvos do skill: brilho 46–56 %, saturação 35–46 %, vinheta 57–66 %)
| Cena | Brilho | Saturação | Vinheta | Sombras (a, b) |
|---|---|---|---|---|
| calçada · tarde | 51,6 ✅ | 29,4 ⚠️ | 82,1 ⚠️ | +14, −3 ⚠️ (quentes, não roxo-azuladas) |
| esquina · tarde | 45,5 (−0,5) | 39,2 ✅ | 70,2 ⚠️ | +9, −21 ✅ |
| de cima · tarde | 34,9 ⚠️ | 34,1 (−0,9) | 56,2 (−0,8) | +12, −19 ✅ |
| calçada · noite | 29,8 (noite) | 58,9 (noite) | 66,9 | +16, −19 ✅ |
| esquina · chuva | 52,1 | 17,6 (chuva: dessatura de propósito) | 61,8 ✅ | +4, −15 ✅ |

Leitura:
- **Calçada · tarde:** a fachada laranja da esquerda e o ladrilho iluminado deixam os cantos claros (vinheta 82 %) e puxam as sombras para o quente.
- **Vista de cima:** escura porque metade do quadro é calçada na sombra do prédio.

A grade de cor é a mesma da E1 e não foi ajustada por cena. É ajuste de composição, não do kit.

## QA automático
| Teste | Resultado |
|---|---|
| **Nada flutuando** (421 malhas por cena; raio para baixo a partir do topo de cada peça, folga máxima 2 cm) | **0 objetos flutuando** nas 5 cenas e na folha de componentes |
| **Textos** (lista exata dos textos 3D da cena × `textos_permitidos` da receita) | Encontrados: "214", "215", "216", "217", "30", "R. DAS JABUTICABAS", "R. VAGALUME". **Nenhum fora da lista.** Nenhuma marca de terceiros. Não há "MODO CURIOSO" na cena da E2; quando houver, só nesta grafia (ID-004) |
| OCR nas imagens | **Não executado:** não há OCR instalado no ambiente. A conferência é feita na fonte (o texto exato de cada objeto), o que é mais rigoroso que OCR. Instalar OCR seria mudança de dependência e não foi feita |
| **Escala** (medida no Blender) | Pista 6,4 m + 2 sarjetas de 0,3 m = 7,0 m (2 faixas de 3,2 m) · meio-fio 15 cm de largura e 15 cm de altura · poste com 9,5 m de altura · faixa de pedestre: listras de 0,40 m × 3,0 m · calçada 3,2 m |

**O QA encontrou e eu corrigi 4 defeitos reais:**
1. A porta dos prédios provisórios começava 13 cm acima do chão.
2. Os semáforos estavam em cima da curva do meio-fio da esquina, sem calçada embaixo. Foram para a calçada.
3. Folhas secas e mato ficavam a 15 cm de altura sobre o **rebaixo de garagem**, que fica a 3 cm. Agora seguem a superfície real (pista, rebaixo ou rampa).
4. Peças presas (bicos do hidrante, ripas do banco, partes da fachada) eram acusadas por engano. Agora são marcadas como "suspenso".

## Área vazia (`E2_area_vazia.png`, magenta = bloco sem detalhe)
Blocos de 60×60 px fora do céu com desvio de luminância < 1,2 %, medidos sem grão e sem personagem:

| Cena | Área vazia |
|---|---|
| **calçada · tarde (E2)** | **8,4 %** |
| calçada · tarde (E1, referência: mesma posição de câmera, rua reta) | 19,7 % |
| esquina · tarde | 19,6 % |
| de cima · tarde | 35,2 % |

Na vista de calçada, a cena da E2 tem **menos da metade** da área vazia da E1. **Na esquina e na vista de cima, o que sobra vazio é o asfalto de perto e as paredes lisas dos prédios provisórios.**

Tentei melhorar o asfalto. O detalhe está no render: o asfalto varia ~11 % nas passadas de luz. Mas ele fica na sombra dos prédios e a gradação comprime os escuros, então lê como liso. A vista de cima até piorou na métrica (35 %, antes 27–29 %), sem diferença que eu enxergue na imagem. Ou seja, **a métrica não confirma melhora do asfalto**, e eu não vou afirmar que ela existe.

## Determinismo, cache e integridade
| Teste | Resultado |
|---|---|
| Mesma receita montada duas vezes | **Geometria idêntica** (hash de todos os vértices e posições, 1.148 objetos) |
| Outra semente | Geometria diferente (outros lotes, remendos, folhas) |
| Cache | 2ª chamada: HIT em 1,9 s |
| Assinatura de `personagens/heitor/rig_v2/`, `docs/IDENTIDADE_OFICIAL.md`, `skills/` | **Idêntica** à de antes da E0 (`068bf373…8342`); nenhuma alteração pendente |
| Verificação F1 do rig | 6/6 vistas OK |
| Paleta do Heitor no quadro | 191.418 pixels, **100 % idênticos** ao rig sozinho |
| ID-001 a ID-004 | Inalteradas |

## Problemas encontrados e corrigidos
1. Os 4 defeitos de apoio achados pelo QA (acima).
2. **Erro de cache de fonte** entre cenas (`VectorFont has been removed`). O cache de fontes agora é limpo a cada montagem.
3. **Textos 3D apareciam em todas as camadas de profundidade.** O tipo FONT não era tratado no render por camadas. Corrigido.
4. **O raio do QA partia do meio do objeto** e não achava apoio para peças grossas. Agora parte do topo e ignora o próprio objeto.
5. **Na vista da esquina, o Heitor ficou fora do quadro** (âncora a 31° do eixo; o campo é de ±16°). Câmera reapontada; o Heitor está na esquina, junto ao semáforo.
6. **Vazio no fim da rua transversal** (o chão acabava a 24 m e via-se o "nada"). Entraram prédios de fundo nas duas pontas.
7. **O detalhe novo do asfalto e do concreto saiu zerado na 1ª versão.** Errei a faixa dos fatores: o ruído do Blender fica entre 0,3 e 0,7, e o mapeamento dava ≤ 0 nessa faixa. Detectado medindo as passadas de luz e corrigido.

## Limitações (registradas, não escondidas)
1. **Prédios provisórios** dominam a esquina (paredes azuis lisas). São a maior fonte de "vazio" que restou e são escopo da E3.
2. **Asfalto em sombra lê liso** de perto (ver "área vazia"). Opções: marcas maiores e mais claras (remendos de cor diferente, pintura gasta, bueiros), ou a gradação preservar mais os escuros. Prefiro decidir com você.
3. **As nuvens 2D em quadro largo (paisagem) parecem camuflagem.** Por isso a folha de componentes usa o céu do render. Nos quadros verticais da série o céu aparece pouco e lê bem. Afinar o céu é tarefa a parte.
4. **O Heitor não recebe a luz do cenário** (de noite e na chuva fica mais aceso que a rua). Corrigir exige uma extensão de iluminação do personagem, que só faço com aprovação específica.
5. **Rolo de sobra de cabo** lê como um aro solto perto do poste. Funciona de longe, mas é simples.
6. **Sem veículos, pessoas, sujeira de rua nem pichação.** Veículos são a E4.
7. **OCR não instalado** (ver QA).
8. A placa de rua é pequena: legível de perto (calçada) e ilegível de longe, como na vida real.

## Como reproduzir
```
.venv/bin/python cenografia/testes/e2_testes.py         # 5 placas (~2,5 min cada na 1ª vez), folha, QA, área vazia, determinismo, integridade
.venv/bin/python cenografia/testes/e2_testes.py E2_3_qa # só um teste
```

## Próxima etapa (só com aprovação): E3 — prédios
Kit de fachadas de bairro brasileiro: sobrados, prédios baixos, comércio de térreo (portas de enrolar, toldos, letreiros só com nomes inventados ou "MODO CURIOSO"), muros, grades, portões, telhados, caixas-d'água, antenas e varais, substituindo os volumes provisórios.
