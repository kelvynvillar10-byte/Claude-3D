# Relatório da etapa E3 — prédios

25/11/2026 · Autorizada pelo diretor junto com a aprovação da E2 ("Autorizado"). **E3 APROVADA pelo diretor em 25/11/2026; E4 autorizada.** Nenhum episódio ou história foi produzido. O Heitor rig v2 não foi alterado.

Escopo do plano aprovado: "Fachadas em 3 estilos; folha com variações por semente". A gramática de fachada segue a seção 2.4 da proposta: térreo comercial, andares, extras e topo.

## O que foi construído (`componentes/predios.py`)
| Estilo | O que tem |
|---|---|
| **Residencial** (3–6 andares) | Portaria com marquise e luz, número (só algarismos), interfone, portão de garagem, janelas gradeadas no térreo, rodapé de pastilha ou concreto. **Coluna da escada saliente** em outra cor ou pastilha, com janelinhas nos patamares. Padrão de vãos **simétrico e repetido** em todos os andares, como num prédio real: janela, janela dupla, banheiro (basculante) e varanda. Varandas com grade de ferro ou mureta e varal com roupas. Ar-condicionado sob ou ao lado das janelas. Cinta entre andares. Platibanda com rufo, torre com caixa d'água, parabólicas e antenas de TV |
| **Comercial** (loja + 0–2 andares) | 1 ou 2 lojas. **Aberta:** interior aceso, prateleiras com produtos genéricos, balcão, porta de enrolar recolhida e luz que derrama na calçada à noite. **Fechada:** porta de enrolar canelada. Pilares, letreiro com **palavra comum** (PADARIA, MERCADINHO, BAZAR, FARMÁCIA…; nunca marca), toldo listrado desbotado, piso de ladrilho hidráulico. Andares de cima com janelas largas e placa "ALUGA-SE" nas salas vagas. **Lateral de esquina:** portas de enrolar e janelas gradeadas no térreo |
| **Sobrado** (2 pavimentos) | Casa **recuada atrás do muro**: muro com capa, portão de garagem, portão social gradeado, arandela, número, piso da garagem. Na casa: porta de madeira, janelas com ou sem grade, varanda opcional com varal, **telhado cerâmico de duas águas** com oitões e caixa d'água |

**Componentes registrados:**
- `fachada_quadra`: divide uma frente de quadra em lotes por semente (estilo, largura, altura e cores). O lote da ponta ganha **fachada lateral** quando é esquina. A fachada pode ficar no plano x (rua principal) ou y (rua transversal, fundo).
- `predio_residencial`, `predio_comercial`, `sobrado`: lote isolado.
- `chao`: terreno simples.

**Materiais novos** (`nucleo/materiais.py`):
- `chapa_ondulada` (porta de enrolar, persiana);
- `listrado` (toldo);
- `reboco(detalhe=…)`: manchas de repintura, variação de tom e granulado. Com o valor padrão 0, o reboco da E1 e da E2 fica igual.

**Cores de fachada:** as da `PALETA_BAIRRO` são puxadas 25 % para um cinza quente. A gradação da série satura ×1,95, e a cor pura numa parede grande ao sol virava neon.

**Instâncias:** molduras, folhas de janela, grades, ar-condicionado, lajes e guarda-corpos de varanda usam malha compartilhada. No quarteirão, **700 dos 2.607 objetos de malha** saem de **37 protótipos**.

## Folha de variações (`testes/e3/E3_variacoes.jpg`)
3 estilos × 4 sementes, um lote por célula (540×960, céu + 1 camada, 4/16 amostras). As 12 células renderizaram em **12,3 s em média** (máx. 14,6 s).
- **Residencial:** 3 a 6 andares, com ou sem coluna da escada, varandas com mureta, cintas.
- **Comercial:** 1 ou 2 lojas, abertas ou fechadas, com ou sem toldo, com ou sem andares e "ALUGA-SE".
- **Sobrado:** muros e portões de cores diferentes, varanda com grade, janelas gradeadas.

## Cenas de prova: o quarteirão da E2 com os prédios da E3
`receitas/e3_quarteirao.json` traz 11 frentes de quadra:
- os dois lados da rua, antes e depois do cruzamento;
- as quatro pontas da rua transversal;
- os fundos da transversal e da rua principal.

São **28 prédios** e 2.732 objetos. Imagens:
- `E3_cenas.png` (as 4 lado a lado);
- cada cena em 1080×1920: `E3_calcada_tarde.jpg`, `E3_esquina_tarde.jpg`, `E3_calcada_noite.jpg`, `E3_esquina_chuva.jpg`;
- `E3_antes_depois.png` (E2 × E3, mesma câmera e mesma luz).

### Tempo real de render (4 núcleos, sem GPU, 1080×1920, 4/16/24/24/16 amostras)
| Placa | Tempo | Camada mais lenta |
|---|---|---|
| calçada · tarde | 169,5 s | meio 93,9 s |
| esquina · tarde | 151,8 s | meio 61,1 s |
| calçada · noite | 175,3 s | meio 98,6 s |
| esquina · chuva | 161,0 s | meio 70,0 s |

**As 4 placas ficaram dentro da meta de 3–5 min:** média de 164 s (2,7 min). Na E2 a média foi 150 s. Com 2,4× mais objetos (2.732 contra 1.148), o tempo subiu ~10 %.

### Medidas de cor (alvos do skill: brilho 46–56 %, saturação 35–46 %, vinheta 57–66 %)
| Cena | Brilho | Saturação | Vinheta | Sombras (a, b) |
|---|---|---|---|---|
| calçada · tarde | 52,9 ✅ | 30,9 ⚠️ | 67,4 (+1,4) | +9, −12 ✅ (na E2: +14, −3) |
| esquina · tarde | 46,1 ✅ | 28,0 ⚠️ | 70,7 ⚠️ | +8, −20 ✅ |
| calçada · noite | 30,9 (noite) | 49,0 (noite) | 72,5 | +14, −22 ✅ |
| esquina · chuva | 51,3 | 12,7 (chuva) | 60,8 ✅ | +3, −13 ✅ |

- **Vinheta e sombras melhoraram** na calçada em relação à E2 (82 % → 67 %; as sombras agora são roxo-azuladas).
- **A saturação de dia continua abaixo do alvo** (28–31 %): a névoa de profundidade e a luz dourada lavam as cores ao longe. É ajuste de gradação por cena, não do kit.

## QA automático
| Teste | Resultado |
|---|---|
| **Nada flutuando** (579 malhas por cena; 12 células da folha) | **0 objetos flutuando** em tudo |
| **Textos** | **Nenhum fora da regra.** Encontrados: nomes de rua inventados, palavras comuns de comércio (AÇOUGUE, BAZAR, CHAVEIRO, HORTIFRUTI, LANCHONETE, MERCADINHO, PADARIA, PAPELARIA, SALÃO, ÓTICA), "ALUGA-SE" e números só com algarismos (casas e postes). Nenhuma marca de terceiros. "MODO CURIOSO" não aparece nesta cena; quando aparecer, só nesta grafia (ID-004) |
| OCR | **Não executado** (não há OCR no ambiente). A conferência é feita na fonte: o texto exato de cada objeto de texto |
| **Escala** | 28 prédios com corpo de 3,45 m (loja térrea) até 20,75 m (residencial de 6 andares). Pé-direito de 2,9 m nos andares e 3,2–3,3 m no térreo; calçada a 15 cm; vão de janela padrão de 1,20 × 1,25 m (moldura medida: 1,44 × 1,45 m). Na loja térrea, o "corpo" medido é só a laje de 0,35 m sobre a loja |

## Área vazia (`E3_area_vazia.png`)
| Cena | E2 | E3 |
|---|---|---|
| calçada · tarde | 8,4 % | **7,8 %** |
| esquina · tarde | 19,6 % | **25,5 %** ⚠️ |

**A métrica piorou na esquina, e eu não vou esconder isso.** Ela mede variação fina de luminância em blocos de 60 px. A parede azul que dominava a esquina na E2 era de **pastilha**, e o rejunte em grade conta como "detalhe". Na E3 o lugar dela é de um prédio de reboco: entre as janelas, o reboco tem variação larga e suave, que a métrica não pega.

A olho (`E3_antes_depois.png`), a esquina da E3 tem janelas, ar-condicionado, loja aberta, porta de enrolar e fachada lateral, onde antes havia um paredão liso. Mas isso é avaliação visual, não medida.

Reforcei o detalhe do reboco duas vezes, e a métrica quase não mudou: 25,9 % → 25,5 %. **Conclusão: esta métrica não serve para julgar fachadas de reboco.** Na esquina, o maior bloco "vazio" continua sendo o asfalto em primeiro plano (limitação já registrada na E2).

## Determinismo, cache e integridade
| Teste | Resultado |
|---|---|
| Mesma receita montada duas vezes | **Geometria idêntica** (2.732 objetos) |
| Outra semente | Outros prédios (2.917 objetos) |
| Cache | 2ª chamada: HIT em 2,1 s |
| Assinatura de `personagens/heitor/rig_v2/`, `docs/IDENTIDADE_OFICIAL.md`, `skills/` | **Idêntica** à de antes da E0 (`068bf373…8342`); nenhuma alteração pendente |
| Verificação F1 do rig | 6/6 vistas OK |
| Paleta do Heitor no quadro | 191.418 pixels, **100 % idênticos** ao rig sozinho |
| ID-001 a ID-004 | Inalteradas |

## Problemas encontrados e corrigidos
1. **O parâmetro da largura do lote (`L`) escondia o módulo de luz** (`L.luz_ponto`). Renomeado antes do 1º teste.
2. **Janelas acesas de dia pareciam tinta amarela.** Luz mais branca e mais fraca, e menos janelas acesas (15 %).
3. **Fachada residencial lisa demais.** Entraram a coluna da escada e a cinta mais frequente.
4. **Térreo lateral das lojas de esquina era uma parede lisa.** Entraram portas de enrolar, janelas gradeadas, rodapé e viga.
5. **Faixa de vazio no horizonte** atrás dos prédios baixos da folha. Criado o componente `chao`.
6. **Cores de parede saturadas ao sol, com cara de videogame.** Ficaram 25 % mais próximas de tinta real.
7. **Reboco chapado.** Ganhou detalhe; na 1ª versão o contraste ficou fraco demais (4–10 %) e foi reforçado.

## Limitações (registradas, não escondidas)
1. **Só fachadas planas com peças salientes.** As janelas não têm recuo real na parede, e não há interiores além da loja (o fundo da loja é um painel aceso). De perto, a janela parece "colada".
2. **Telhado só no sobrado.** Prédios e lojas têm terraço com platibanda, que é o mais comum no bairro, mas não há telhado aparente de fibrocimento nem puxadinhos.
3. **Faltam pichação, cartazes, fios entrando nas casas, grades de varanda variadas e plantas nas janelas.** Ficam para a E5 (ambientação), com aprovação.
4. **As fachadas laterais só existem nas esquinas.** As empenas entre prédios de alturas diferentes são lisas, como na vida real, mas sem marca de umidade forte.
5. **O Heitor não recebe a luz do cenário** (à noite, as lojas acesas não iluminam o personagem). Corrigir isso exige uma extensão do rig, só com aprovação.
6. **A métrica de área vazia não mede bem fachadas de reboco** (ver acima).
7. **A saturação de dia (28–31 %) continua abaixo do alvo de 35–46 %**, como na E2.

## Como reproduzir
```
.venv/bin/python cenografia/testes/e3_testes.py                  # folha, 4 placas (~2,7 min cada na 1ª vez), QA, área vazia, determinismo, integridade
.venv/bin/python cenografia/testes/e3_testes.py E3_1_variacoes   # só a folha de variações (~2,5 min)
```

## Próxima etapa (só com aprovação): E4 — veículos
Pelo plano aprovado: 5 carrocerias, ônibus e moto, com giro de 360° de cada um, sem marcas nem modelos reais.
