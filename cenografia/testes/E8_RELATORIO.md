# Relatório da etapa E8 (parte 1) — poderes: eletricidade e terra

26/11/2026 · Autorizada pelo diretor junto com a aprovação da E7 ("Autorizado e aprovado"). Pela regra aprovada, **eletricidade e terra vêm primeiro e não mexem no rig.**
- **Voo, aranha e elasticidade NÃO foram iniciados:** dependem de extensões do rig que precisam de aprovação específica.
- **E8 parte 1 APROVADA pelo diretor em 26/11/2026.**
- Nenhum episódio ou história foi produzido.
- O Heitor rig v2 não foi alterado: ele foi apenas **posado** com a API do próprio rig (`mira_braco` para apontar o braço ao alvo, com o cotovelo sempre anatômico; `mistura_expr` para a expressão de neutro → bravo).

## O que foi construído (`efeitos/poderes/`)
Cada poder é **um arquivo**, registrado com `@efeito`, que usa só o núcleo da E7. Os dois têm as 6 fases, as 3 intensidades, contatos no rig e no cenário, regras de segurança e proteção, e **marcas que ficam** depois do fim do efeito.

### Eletricidade (`eletricidade.py`)
**Família de cores:** ciano-claro com núcleo quase branco.

| Fase | O que acontece |
|---|---|
| início | estalos: faíscas pequenas na mão; arcos curtos começam a correr pelo **contorno do corpo** |
| ativação | os arcos pelo corpo aumentam; a mão acende; luz ciano no cenário (luz 2D) |
| uso | **raio fractal da mão ao alvo**, redesenhado a cada 2 quadros (3 no discreto), com ramos |
| impacto | raio mais forte; faíscas no alvo; **marca queimada** (alvo no chão); tremida; **quadro de impacto** (extremo) |
| dissipação | arcos residuais, fumaça no alvo, luz caindo |
| encerramento | estalos finais; a marca queimada fica |

**Por intensidade:**
- **discreto:** só o corpo e a mão;
- **moderado:** acrescenta o raio até o alvo;
- **extremo:** 3 raios mais grossos, chão, impacto, tremida forte.

**Mão do contato:** a do lado do alvo; de frente, a mão esquerda do Heitor fica à direita da tela. Assim o braço não cruza o peito.

### Terra (`terra.py`)
**Família de cores:** terra e ocre, com poeira bege.

| Fase | O que acontece |
|---|---|
| início | tremor leve; poeira nos pés |
| ativação | **rachadura corre dos pés até o alvo**, crescendo no plano do chão em perspectiva; **onda de terra** levanta a calçada (moderado/extremo) |
| uso | **pedaços do chão se soltam e flutuam**. A face de cima é **recortada do próprio fundo**, a espessura tem lados sombreados pelo sol do horário, e fica um **buraco escuro** no lugar. Pedrinhas sobem |
| impacto | os pedaços disparam; **pilar de rocha** sobe com assentamento, iluminado pela direção do sol ou da lua da placa (extremo); **cratera**; detritos; tremida; quadro de impacto (extremo) |
| dissipação | os pedaços caem e somem na poeira |
| encerramento | poeira assentando; **rachadura, buracos, cratera e pilar ficam** |

**Pedaços:** só ficam os que estão em chão **visível** na imagem, com profundidade conferida pixel a pixel. Assim a textura recortada é sempre chão, nunca um hidrante ou um toldo na frente. Dos candidatos sorteados, ficam os 6 (moderado) ou 8 (extremo) primeiros que passam.

**Brilho:** pedra, terra e pilar acompanham o brilho do chão daquele horário (amostrado no fundo).

### Mudança no núcleo
A mesa passou a desenhar os **resíduos** de efeitos que já acabaram mas deixam marca (`deixa_marca = True`). Antes, a rachadura, o pilar e o queimado sumiam no último quadro do efeito. Corrigido.

## Vídeo: `testes/e8/E8_poderes.mp4`
19,6 s (588 quadros) · 1080×1920 · 30 q/s · marca d'água "MODO CURIOSO" · legenda "poderes (teste, não é história)", com o poder, a intensidade e a **fase atual**.

São 6 clipes na rua da E6, com leve avanço de câmera:

| Clipe | Horário | Alvo |
|---|---|---|
| eletricidade · discreto | manhã | (sem raio: corpo e mão) |
| eletricidade · moderado | manhã | placa "30" (metal) |
| eletricidade · extremo | noite | chão à frente (queimado, impacto) |
| terra · discreto | manhã | calçada, à direita |
| terra · moderado | noite | calçada, à esquerda |
| terra · extremo | manhã | calçada, à direita (pilar) |

Folha com 2 quadros de cada clipe: `E8_quadros.jpg`.

## Medidas
| Teste | Resultado |
|---|---|
| **Ordem das intensidades** (pico de energia que o poder põe no quadro) | Eletricidade: discreto **0,049** < moderado **0,441** < extremo **0,888** ✅. Terra: discreto **0,018** < moderado **0,064** < extremo **0,112** ✅. A energia mede cobertura e brilho e não compara um poder com o outro (a terra cobre pouco e não brilha) |
| **Energia por fase** (moderado) | Eletricidade: início 0,004 · ativação 0,060 · uso 0,191 · **impacto 0,383** · dissipação 0,069 · encerramento 0,025, o pico no impacto. Terra: cresce até a dissipação (0,061) e fica (0,057), porque buracos e rachadura permanecem |
| **Contatos do raio** | Ponta na **mão do rig**: erro **0,0 px**. Ponta no **alvo**: erro **0,0 px** |
| **Redesenho** | **15 por segundo** (a cada 2 quadros) no moderado e no extremo. O "4" aparece nos segundos parciais, no começo e no fim do uso |
| **Família de cor × camiseta** (#3d80d8, ΔE CIELAB) | Halo da eletricidade **65,2** · núcleo **68,4** · terra **78,8** · rocha **67,6** · poeira **77,4**. Todos muito acima de 25: bem distintos do azul da camiseta |
| **Segurança** (flashes por segundo, vídeo pronto) | Máximo de **1 por segundo** em cada clipe e no vídeo inteiro (3 no total, um por impacto). O limite é 3 |
| **Proteção do rosto e da estampa** | Cobertura máxima **0,35 / 0,35** na eletricidade (os arcos pelo corpo são limitados no rosto e na estampa). Na terra: 0,00 / 0,02 |
| **Paleta do Heitor** (eletricidade discreta, arcos ativos) | **100 % idêntica** ao rig sozinho em 85.999 pixels sem efeito na frente. 7.813 pixels têm arco na frente, de propósito |
| **Terra: textura recortada** | Pedaço parado no lugar: face de cima × fundo, erro médio **0,0** (6.932 pixels) |
| **Terra: rachadura** | Cresce sem nunca voltar ✅ |
| **Determinismo** | Mesmo quadro duas vezes: **idêntico** |
| **Integridade** | Assinatura de rig v2, identidade e skill **idêntica** (`068bf373…8342`); F1 6/6 OK |

### Tempo de composição (CPU, 1080×1920, com o Heitor e o céu animado)
| Clipe | Média | Máximo |
|---|---|---|
| eletricidade discreto / moderado / extremo | 3,83 / 4,42 / 4,82 s por quadro | 4,37 / 5,55 / 5,87 s |
| terra discreto / moderado / extremo | 2,72 / 3,25 / 3,32 s por quadro | 3,32 / 3,88 / 4,29 s |

Os 19,6 s de vídeo levaram ~38 min de composição. As placas já estavam prontas, vindas da E6 e da E7.

## Problemas encontrados e corrigidos
1. **Braço cruzando o peito:** o Heitor apontava com o braço direito para alvos à direita da tela. Agora aponta com a mão do lado do alvo.
2. **Pilar escondido atrás do Heitor** (alvo bem atrás dele) e **invisível à noite** (rocha escura contra o céu escuro). Alvos deslocados para os lados; a terra extrema foi para a manhã; piso de brilho maior.
3. **Pilar degenerado numa lasca:** os ângulos dos vértices eram sorteados livres e se concentraram num só lado (0,45–3,28 rad). Agora são igualmente espaçados com variação; o mesmo vale para os pedaços. O topo do pilar some quando a câmera está abaixo dele.
4. **As marcas sumiam no fim do efeito.** A mesa agora desenha os resíduos.
5. **Pedaço com textura de hidrante e toldo:** o chão daquele ponto estava escondido na imagem. Agora só ficam pedaços em chão visível.
6. **Pedaços parecendo tábuas** (câmera baixa mostrava só o lado). A face de cima inclina para a câmera.
7. **Medições erradas, corrigidas:**
   - textura recortada medida com os lados incluídos e com o fundo do horário errado;
   - pedaços desenhados juntos, um cobrindo o outro. Medido pedaço por pedaço, dá 0,0, e os pedaços passaram a ser desenhados em ordem de profundidade.

## Limitações (registradas, não escondidas)
1. **O Heitor não recebe a luz do raio** (nem a sombra da poeira). A luz no personagem é calculada e registrada, mas não aplicada. É a **extensão de iluminação do rig, que depende da sua aprovação**, e é a limitação mais visível da eletricidade à noite.
2. **Pose simples:** o Heitor só aponta um braço (sem antecipação de corpo inteiro, sem passo). Gestos mais fortes, como as duas mãos ou agachar e bater no chão, precisariam de poses novas do rig, que é extensão.
3. **Os pedaços de terra são lajes com lados lisos**, e a cratera e o queimado são decalques planos. Leem bem em plano médio; de perto parecem recorte.
4. **Pilar com 7 faces e fendas desenhadas:** sem textura de rocha detalhada. Para planos de destaque, a proposta prevê rochas 3D pré-renderizadas.
5. **A luz 2D do raio não faz sombra** (limitação da E7).
6. **Energia medida** é cobertura + brilho: serve para comparar intensidades do mesmo poder, não poderes diferentes.

## Como reproduzir
```
.venv/bin/python cenografia/testes/e8_testes.py                         # vídeo (≈ 38 min) + medidas
.venv/bin/python cenografia/testes/e8_testes.py previa /caminho/previa.jpg   # quadros-chave (≈ 10 min)
```

## Próximos passos (cada um só com aprovação)
1. **Extensões do rig** necessárias para os próximos poderes, apresentadas à parte com justificativa, demonstração e testes de identidade, como manda a regra:
   - **tom de luz no personagem** (melhora a eletricidade e todos os poderes com luz);
   - **poses de voo** e roupa e cabelo ao vento (voo);
   - **poses de escalada e balanço** (aranha);
   - **membros elásticos**, só braços e pernas (elasticidade).
2. Depois de cada extensão aprovada: **voo, aranha, elasticidade** (E8, parte 2).
3. **E9:** combinações (teste de ação de 10–15 s, sem história) e relatório final.
