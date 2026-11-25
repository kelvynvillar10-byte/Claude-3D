# Relatório da etapa E4 — veículos

25/11/2026 · Autorizada pelo diretor junto com a aprovação da E3 ("Aprovo e autorizo"). **E4 APROVADA pelo diretor em 25/11/2026; E5 autorizada.** Nenhum episódio ou história foi produzido. O Heitor rig v2 não foi alterado.

Escopo do plano aprovado: "5 carrocerias, ônibus e moto; giro de 360° de cada um". **Sem marca, sem logotipo e sem modelo real.** As placas são o modelo Mercosul **em branco, sem caracteres**, para não reproduzir uma placa real.

## O que foi construído (`componentes/veiculos.py`)
**Carroceria por loft** de seções transversais ao longo do comprimento:
- perfil de teto por tipo (capô, para-brisa, teto, vigia ou tampa);
- fundo que sobe em **arco** sobre cada roda;
- planta arredondada;
- parte de cima mais estreita que a de baixo.

Cada face recebe o material pela posição e pela normal: pintura, vidro (para-brisa, janelas laterais entre as colunas A/B/C, vigia), lona, faixa e teto.

| Tipo | Destaques |
|---|---|
| hatch compacto | traseira curta e inclinada |
| sedã | três volumes (porta-malas) |
| SUV | mais alto, soleira e rodas maiores |
| picape cabine dupla | **capota marítima** e santantônio (muito comum no Brasil) |
| furgão de entrega | baú alto sem janelas, lateral lisa (sem marca) |
| ônibus urbano | 12 m; janelas com colunas a cada 1,25 m; **portas de vidro do lado direito**; faixa de cor e teto claro; letreiro de itinerário "101 · CENTRO" (número e palavra comum); retrovisores em haste |
| moto 150 cc | quadro tubular, tanque, banco, escapamento, guidão, farol, descanso lateral (estacionada levemente inclinada) |

**Peças comuns:**
- rodas (pneu com ombro + aro com 5 raios + cubo; malha compartilhada) e caixas de roda escuras;
- para-choques, grade, faróis e lanternas (acendem com `farois=True`, no grupo de luz "artificial", com foco de luz no chão à frente);
- retrovisores, frisos de porta e maçanetas;
- cores com peso de frota brasileira (branco, prata, cinza e preto são a maioria).

**Materiais novos:** `pintura_automotiva` (base metálica + verniz, poeira embaixo) e `lente` (farol e lanterna, apagada ou acesa).

**Componentes:**
- `veiculo`: um veículo, com tipo, posição, giro, cor e faróis;
- `estacionamento`: carros parados junto ao meio-fio, por semente, pela mão de direção brasileira, evitando trechos dados (esquina, hidrante, garagem).

## Giro de 360° (`testes/e4/E4_giro_360.mp4` e `E4_giro_angulos.jpg`)
- **Vídeo:** os 7 veículos em grade, 48 ângulos (7,5° por quadro), duas voltas, 6 s.
- **Folha:** 8 ângulos por veículo.
- Estúdio: piso de concreto, céu de meio-dia. 480×360, 24 amostras com redução de ruído do Cycles.
- **Tempo real: ~2,0 s por quadro** (1,9–2,2 s); 336 quadros em ~11 min.

## Escala (medida no Blender)
| Veículo | Comprimento × largura × altura (m) | Largura com retrovisores | Roda (Ø) | Faixa típica de referência* | Pneus no chão |
|---|---|---|---|---|---|
| hatch | 3,98 × 1,75 × 1,46 | 2,05 | 0,60 | 3,8–4,1 × 1,65–1,76 × 1,42–1,56 ✅ | ✅ |
| sedã | 4,58 × 1,78 × 1,44 | 2,09 | 0,62 | 4,4–4,75 × 1,70–1,82 × 1,40–1,50 ✅ | ✅ |
| SUV | 4,48 × 1,85 × 1,66 | 2,15 | 0,70 | 4,2–4,6 × 1,76–1,87 × 1,58–1,72 ✅ | ✅ |
| picape | 5,38 × 1,89 × 1,80 | 2,18 | 0,74 | 5,1–5,4 × 1,80–1,92 × 1,74–1,86 ✅ | ✅ |
| furgão | 5,08 × 1,98 × 2,42 | 2,22 | 0,68 | 4,8–5,5 × 1,90–2,06 × 2,25–2,60 ✅ | ✅ |
| ônibus | 12,13 × 2,55 × 3,06 | 3,17 | 1,00 | 11,5–13,2 × 2,45–2,60 × 2,95–3,35 ✅ | ✅ |
| moto | 1,94 × 0,72 (no guidão) × 1,13 | — | 0,61 | 1,9–2,1 × 0,70–0,82 × 1,00–1,15 ✅ | ✅ (−6 mm: inclinação no descanso) |

\* As faixas de referência são **valores típicos de mercado, de conhecimento geral. Não foram medidos neste projeto** e servem só para conferir a ordem de grandeza.

**Todos os 7 ficaram dentro da faixa, e todos os pneus tocam o chão** (|z| ≤ 1 cm).

## Cenas de prova: o quarteirão da E3 com veículos
`receitas/e4_quarteirao.json` tem **14 veículos**:
- **estacionados por semente** nos dois lados da rua: 7 hatch, 2 sedãs, 2 SUVs, 1 picape. Evitam a esquina, o hidrante e a frente do Heitor.
- **em trânsito:** o ônibus na faixa da direita depois do cruzamento; um sedã vermelho e uma moto esperando na rua transversal.

À noite, os 3 veículos em trânsito acendem os faróis.

Imagens: `E4_cenas.png` (as 4 cenas lado a lado), cada cena em 1080×1920 e `E4_antes_depois.png` (E3 × E4).

### Tempo real de render (4 núcleos, sem GPU, 1080×1920)
| Placa | Tempo | Camada "meio" |
|---|---|---|
| calçada · tarde | 180,2 s | 100,6 s |
| esquina · tarde | 162,7 s | 66,8 s |
| calçada · noite (faróis) | 195,6 s | 109,2 s |
| esquina · noite (faróis) | 167,7 s | 69,4 s |

**As 4 placas ficaram dentro da meta de 3–5 min:** média de 176 s (2,9 min). Na E3 a média foi 164 s; com +392 objetos de veículos (3.124 no total), o tempo subiu ~7 %.

### Medidas de cor
| Cena | Brilho | Saturação | Vinheta | Sombras (a, b) |
|---|---|---|---|---|
| calçada · tarde | 52,3 ✅ | 31,3 ⚠️ | 67,9 | +9, −12 ✅ |
| esquina · tarde | 45,8 (−0,2) | 28,2 ⚠️ | 70,7 | +8, −20 ✅ |
| calçada · noite | 31,1 | 48,7 | 72,9 | +14, −21 ✅ |
| esquina · noite | 23,9 | 43,2 | 59,7 | +12, −18 ✅ |

São praticamente as mesmas da E3: os veículos não mudaram a cor do quadro. A saturação de dia continua abaixo do alvo, como na E2 e na E3. A esquina à noite é a cena mais escura (23,9 %): só os postes, os faróis e as janelas acesas iluminam.

## QA automático, determinismo e integridade
| Teste | Resultado |
|---|---|
| Nada flutuando (≈ 650 malhas por cena) | **0** nas 4 cenas. As carrocerias são marcadas como apoiadas nas rodas; quem é verificado contra o chão são os pneus |
| Textos | **Nenhum fora da regra.** Novos: "CENTRO" e "101" (letreiro do ônibus). **Placas de veículo sem caracteres.** Nenhuma marca, logotipo ou modelo real |
| OCR | Não executado (não há OCR no ambiente); a conferência é feita na fonte |
| Mesma receita montada duas vezes | **Geometria idêntica** |
| Outra semente | Outros carros estacionados |
| Assinatura de `personagens/heitor/rig_v2/`, `docs/IDENTIDADE_OFICIAL.md`, `skills/` | **Idêntica** (`068bf373…8342`); nenhuma alteração pendente |
| Verificação F1 do rig | 6/6 vistas OK |
| Paleta do Heitor no quadro | 191.418 pixels, **100 % idênticos** ao rig sozinho |
| ID-001 a ID-004 | Inalteradas |

## Problemas encontrados e corrigidos
1. **A 1ª versão do para-brisa não virava vidro.** A regra excluía faces no topo da seção, e o para-brisa fica justamente lá. A regra foi separada para janelas laterais e vidros de frente e de trás.
2. **No ônibus, a faixa de cor e o friso do teto não apareciam** (faltavam vértices nessas alturas), e **as colunas das janelas saíam irregulares** (seções concentradas nas pontas). Entraram linhas extras de vértices e seções com passo constante.
3. **Hatch com cara de perua:** teto mais curto e traseira mais inclinada.
4. **A moto saiu 15 cm sobreposta ao sedã** na prévia do quarteirão. Foi para junto do meio-fio.
5. **Medidas erradas na 1ª rodada** (pneu em z = −r, alturas infladas): medi antes de o Blender atualizar as transformações dos filhos. Agora a cena é atualizada antes de medir.
6. **Pneu 11 cm mais largo que o previsto e geometria NÃO determinística.** O chanfro do pneu empurrava as tampas para fora e recebia as arestas em ordem variável (conjunto do Python). Foi trocado por um ombro feito com dois cilindros: largura exata e mesma geometria a cada montagem. **O teste de determinismo pegou isso.**
7. **Estúdio do giro superexposto.** Exposição −1,2.

## Limitações (registradas, não escondidas)
1. **Formas estilizadas e simples.** Os veículos leem bem como tipos (hatch, sedã, SUV, picape, furgão, ônibus, moto), mas as laterais são lisas: não têm vincos de carroceria nem detalhes de farol e grade. **De perto (≤ 3 m), parecem maquete.** Para planos fechados, eu refinaria o tipo que a cena usar.
2. **Sem interior:** os vidros são escuros e refletem o céu, sem bancos nem volante. Em plano próximo à noite, isso aparece.
3. **A moto é a mais simples:** sem raios nem corrente, e o garfo é um tubo. Lê como moto de longe e na folha, mas não de perto.
4. **Veículos parados.** Rodas que giram, trânsito em movimento e luzes de freio animadas são parte do sistema de animação da cena de prova (E6), não deste kit.
5. **Sem motorista nem passageiros.** Pessoas não fazem parte do plano aprovado; o único personagem é o Heitor.
6. **O Heitor não recebe a luz dos faróis.** Corrigir isso exige uma extensão de iluminação do rig, só com aprovação.
7. **Saturação de dia** abaixo do alvo, como nas etapas anteriores.

## Como reproduzir
```
.venv/bin/python cenografia/testes/e4_testes.py                       # giro (≈ 11 min), 4 placas (≈ 3 min cada na 1ª vez), QA, integridade
.venv/bin/python cenografia/testes/e4_testes.py E4_1_giro_e_escala    # só o giro e as medidas
```

## Próxima etapa (só com aprovação): E5 — ambientação
Pelo plano aprovado:
- árvores (tronco ramificado por algoritmo, copa em aglomerados), arbustos e vegetação baixa;
- mobiliário (bancos, lixeiras, ponto de ônibus, banca, cones, bicicleta, sacos de lixo);
- comércio (vitrines com produtos genéricos, mesas de bar);
- espalhamento por regras: nada flutuando, nada atravessando.
