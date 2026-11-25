# Relatório da etapa E0 — fundamentos da biblioteca de cenografia

25/11/2026 · Autorizada pelo diretor: só a E0 (implementação, testes e documentação dos fundamentos). **E0 APROVADA pelo diretor em 25/11/2026; E1 autorizada.** Nenhum episódio ou história foi produzido. O Heitor rig v2 não foi alterado.

Cena de teste: `receitas/e0_calcada.json`, uma calçada de bairro vista à altura dos olhos. **Os componentes são provisórios** (prédios, poste, banco e vaso simples), feitos só para exercitar o núcleo. O detalhamento é das etapas E1–E5.

## O que foi construído
| Fundamento | Onde | Situação |
|---|---|---|
| Receita JSON + validação + chave (hash da receita, da versão e do código dos geradores) | `nucleo/receita.py` | ✅ |
| Registro de componentes (`@componente`) | `nucleo/registro.py`, `componentes/` | ✅ |
| Materiais procedurais (10) e geometria com chanfro | `nucleo/materiais.py`, `nucleo/geometria.py` | ✅ (os kits finais são da E1) |
| Céu físico + sol por preset; **4 grupos de luz** (`ceu`, `sol`, `artificial`, `efeito`) | `nucleo/luz.py` | ✅ |
| Câmera com overscan de 25 %, intrínsecos, âncoras 3D → 2D | `nucleo/camera.py` | ✅ |
| Render por camada (céu, longe, meio, perto, frente) sem buracos; EXR linear com uma passada limpa por grupo de luz, alfa e profundidade | `nucleo/render.py` | ✅ |
| Cache com manifesto e sha256 por arquivo | `nucleo/cache.py`, `construir.py` | ✅ |
| Compositor 2.5D: reiluminação, névoa, **paralaxe por pixel**, **teste de profundidade do personagem**, mapeamento fílmico e gradação | `nucleo/compositor.py` | ✅ |
| Medidas de cor iguais às da auditoria das referências | `nucleo/medidas.py` | ✅ |

## Demonstração visual (arquivos em `testes/e0/`)
| Arquivo | O que mostra |
|---|---|
| `E0_folha_camadas.png` | As 5 camadas separadas (sobre xadrez), com cobertura e profundidade mediana de cada uma; mapa de profundidade; composição sem e com o Heitor |
| `E0_camadas_e_paralaxe.mp4` (8 s) | As camadas entram uma a uma (céu → longe → meio → Heitor → perto → frente). Depois a câmera avança 1,4 m e vai 0,30 m para a direita com paralaxe por pixel. No fim, o poste da frente passa na frente do Heitor (teste de profundidade) |
| `E0_iluminacao.mp4` (7 s) | Tarde → anoitecer **só mudando os pesos e as cores dos grupos de luz** (o céu escurece, o sol esfria, janelas e postes acendem). Depois uma **luz de efeito azul pulsando no cenário**, como prévia de como um poder vai iluminar a rua, sem novo render |
| `E0_paralaxe_2.5D_x_real.png` | Compositor 2.5D × render real do Blender com a câmera de fato movida, mais o mapa de diferença |
| `E0_reiluminacao_2.5D_x_real.png` | Reiluminação no compositor × render real com as luzes de fato alteradas, mais o mapa de diferença |
| `E0_composicao_final.png` | Quadro final com gradação, Heitor e marca d'água |

## Resultados medidos (`testes/e0/e0_metricas.json`)

### Tempo real de render (4 núcleos de CPU, sem GPU)
| Item | Medido |
|---|---|
| Placa completa (5 camadas, 1350×2400, 64 amostras + remoção de ruído) | **396 s (6,6 min)**: céu 30 s · longe 122 s · meio 152 s · perto 34 s · frente 58 s |
| CPU e memória | 1.522 s de CPU (os 4 núcleos ocupados); pico de memória de 3,5 GB |
| Disco por placa (EXR half, ZIP) | 63 MB, fora do Git (`.cache/`) |
| Mesma placa com 32 amostras | 310 s (22 % mais rápido); quadro praticamente idêntico ao de 64 (PSNR 46 dB). **⚠ Medição inválida, corrigida na E1:** esse render rodou ao mesmo tempo que outros testes e disputou a CPU. Medido sozinho na E1, o tempo é proporcional às amostras (camada "meio": 64 → 154,5 s; 16 → 39,1 s; preparo 3,1 s; remoção de ruído e gravação ~10 s) |
| Composição por quadro (1080×1920 final) | Câmera andando e luz fixa: **1,17 s/quadro**. Luz mudando a cada quadro: **1,81 s/quadro**. Carregar a placa: 3,5 s |

### Cache e reprodutibilidade
| Teste | Resultado |
|---|---|
| Segunda construção da mesma receita | **HIT em 0,06 s** (contra 396 s sem cache) |
| Mudança de 1 cm na posição do banco; outra semente; uma linha a mais no código do gerador | Chave nova nos 3 casos → MISS (✅) |
| 1 byte alterado num EXR; um arquivo apagado | Cache reconhecido como **inválido** nos 2 casos (✅) |
| Render do zero da mesma receita | **35 de 35 EXR idênticos pixel a pixel** (diferença máxima 0,0). Os bytes dos arquivos diferem; não verifiquei em qual campo do EXR (provavelmente metadados) |

### Iluminação, paralaxe e composição
| Teste | Resultado |
|---|---|
| **Reiluminação × render real** (céu 0,35 azulado, sol 0,12 avermelhado, artificial ×2,5, efeito azul) | Erro médio **1,4/255**, 0,7 % dos pixels acima de 12, **PSNR 42,6 dB**: o compositor reproduz o render real |
| **Paralaxe 2.5D × câmera real movida** (1,4 m à frente, 0,30 m à direita, 0,05 m acima) | Erro médio 4,1/255, 7,3 % dos pixels acima de 12, PSNR 28,4 dB. Brilho médio igual (134,6 × 134,7). O erro restante está nas **áreas reveladas** atrás de objetos da mesma camada (o vaso tapando a vitrine; a borda do poste) e em linhas finas (juntas da calçada, bordas de janela) |
| Alinhamento geométrico da paralaxe | 0,6 px no chão perto da câmera; ≤ 0,7 px na fachada, na calçada distante e no prédio do fundo |
| Ordem das camadas × profundidade | ≤ 0,05 % de pixels violando (só bordas antisserrilhadas), depois da correção abaixo |
| Teste de profundidade do Heitor | No quadro de teste, nada mais perto cobre o Heitor (0 px). No fim do vídeo, o poste da frente o cobre corretamente |
| Cor do quadro final × alvos do skill | Brilho **51,6 %** (alvo 46–56 ✅) · vinheta **59,8 %** (57–66 ✅) · sombras a +8,4 / b −7,9 (≈ +7 / −10 ✅) · altas luzes b **18,5** (≈ +19 ✅) · saturação **30,7 %** (alvo 35–46 ❌, ver limitações) · contraste 18,7 % (≈ 17) |

### Integridade (Heitor rig v2 e decisões oficiais)
| Verificação | Resultado |
|---|---|
| Assinatura de `personagens/heitor/rig_v2/`, `docs/IDENTIDADE_OFICIAL.md` e `skills/` (sha256 dos arquivos no Git) | **Idêntica antes e depois da E0** (`068bf373…8342`); nenhuma alteração pendente nesses caminhos |
| Verificação da F1 do rig (6 vistas) | 6/6 OK, relatório regerado idêntico ao versionado |
| Paleta do Heitor no quadro composto | **191.462 pixels do Heitor idênticos (100 %)** ao desenho do rig sozinho; diferença máxima 0. Ele entra depois do mapeamento de tons, então nem a gradação altera as cores oficiais |
| ID-001 a ID-004 | Inalteradas. Marca d'água "MODO CURIOSO" nos vídeos, com a mesma especificação do piloto. A estampa "Modo Curioso" vem do rig, sem mudança |

## Problemas encontrados pelos testes e corrigidos
1. **A primeira comparação paralaxe × real dava erro alto (PSNR 24 dB).** O erro era do teste: o render real tinha todas as luzes no peso 1, e o compositor usava os pesos padrão do preset. Com pesos iguais, o brilho bate.
2. **Desalinhamento de ~6 px no chão perto da câmera.** Duas iterações de ponto fixo não bastavam onde a profundidade muda rápido. Com 4 iterações, ficou em 0,6 px, sem custo de tempo.
3. **O personagem entrava numa posição fixa da pilha de camadas.** Assim, um objeto da camada "perto" a 9 m poderia cobrir o Heitor a 4,2 m. Substituído por um **teste de profundidade por pixel**: o Heitor só é coberto pelo que está mais perto da câmera que ele.
4. **Ordem de camadas errada na primeira versão da cena** (0,73 % dos pixels sobrepostos). O fim da rua (camada "meio", a ~78 m) era desenhado por cima dos prédios do fundo (camada "longe", a ~72 m). O teste novo de ordem detectou; a receita foi corrigida e a E0 refeita inteira (0,05 %).
5. **O primeiro vídeo de iluminação começava magenta.** A cor da noite entrava com peso cheio desde o primeiro quadro. Agora intensidade e cor são interpoladas juntas, em luz linear.
6. **Gradação fora dos alvos do skill** (saturação 19,6 %, vinheta 85 %, altas luzes sem calor). Ajustada; ficou dentro dos alvos, exceto a saturação.
7. **Composição lenta (~3 s/quadro).** Agora há cache das camadas iluminadas quando a luz não muda, bloom em 1/4 da resolução e vinheta pré-calculada: 1,17–1,81 s/quadro.
8. **A cena saía lavada e quase toda na sombra.** O sol estava atrás dos prédios e o céu dominava a exposição. O sol foi reposicionado e o céu virou um grupo de luz próprio.

## Limitações (registradas, não escondidas)
1. **Tempo de render acima da meta.** A placa leva 6,6 min; a meta da proposta era 3–5 min. A hipótese registrada aqui (custo fixo de preparo e remoção de ruído) **estava errada**: o perfil da E1, medido sem CPU disputada, mostrou que o tempo é proporcional às amostras. A otimização é feita na E1 (amostras por camada).
2. **A paralaxe 2.5D não revela o que estava escondido dentro de uma mesma camada.** Movimentos de câmera grandes mostram o erro nas bordas. Regra para as próximas etapas: objetos que precisam se descolar do fundo (vasos, postes, carros em primeiro plano) vão em camadas próprias; movimentos fortes de câmera usam render real.
3. **Saturação abaixo do alvo (30,7 %, alvo 35–46 %).** A paleta provisória é pálida (concreto e creme). Forçar a gradação deixaria o quadro artificial; a correção é a paleta dos materiais da E1.
4. **O Heitor não recebe a luz do cenário.** No anoitecer e na luz de efeito azul, ele continua com as cores oficiais de dia, e a diferença aparece no vídeo. Corrigir isso exige uma extensão de iluminação do personagem. Pelas suas regras, ela **não foi feita** e, se for o caso, será proposta separadamente, com demonstração e testes.
5. **A posição do sol e as sombras são fixas na placa.** O compositor muda intensidade e cor, não a direção. Um horário com sol em outro lugar exige outro render.
6. **Os componentes são provisórios**, sem o acabamento da proposta (calçada portuguesa, fachadas com gramática, árvores, veículos). São das etapas E1–E5.
7. **Disco:** 63 MB por placa (fora do Git). Muitos planos por episódio vão exigir política de limpeza do cache. O Git LFS só entra se algum arquivo pesado precisar ser versionado; na E0 não foi necessário.

## Como reproduzir
```
.venv/bin/python cenografia/construir.py cenografia/receitas/e0_calcada.json     # ~6,6 min na 1ª vez; depois HIT
.venv/bin/python cenografia/testes/e0_testes.py                                   # todos os testes (~40 min: inclui render do zero e 2 renders de verificação)
```

## Próxima etapa (só com aprovação): E1
Materiais (paleta mais saturada e acabamento), céu e atmosfera, com as otimizações de tempo de render da limitação 1 medidas.
