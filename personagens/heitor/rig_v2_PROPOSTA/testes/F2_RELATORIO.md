# Relatório da fase F2 — Heitor rig v2 (PROPOSTA)

25/11/2026 · Movimento: IK, sistema de animação com camadas, caminhada (perfil, frente, costas) e corrida.
**Nada aqui está aprovado automaticamente.** O desenho da F1 foi aprovado como base; a F2 aguarda avaliação.

## O que foi construído
| Componente | Arquivo | Função |
|---|---|---|
| IK de 2 ossos | `codigo/animacao.py` (`ik2`) | Coxa + canela alcançam o alvo do tornozelo; joelho dobra para a frente |
| Ciclo de caminhada | `animacao.py` (`CAMINHADA`) | 0,86 s/ciclo (~140 passos/min); apoio 62 %; pé plantado; balanço em arco; rolagem calcanhar → ponta; pelve mais baixa no apoio duplo; braço oposto à perna |
| Ciclo de corrida | `animacao.py` (`CORRIDA`) | 0,56 s/ciclo; apoio 38 % (fase de voo); tronco a 12°; cotovelos a ~90°; mãos semifechadas; pouso com joelho flexionado |
| Frente e costas | `animacao.py` + `heitor_v2.py` | Mesmos dados do perfil projetados com **escorço** (escala por osso: o osso encurta quando aponta para a câmera), profundidade do pé, balanço lateral do quadril e contra-rotação dos ombros |
| Camadas | `animacao.py` (`misturar`) | Pose base + sobreposições parciais com peso (0–1) e máscara de juntas |
| Rosto vivo | `animacao.py` | Piscada automática (3–4 quadros, a cada ~3,4 s) e respiração |
| Testes | `codigo/testes_f2.py` | Renderiza, mede e gera folhas |

## Testes executados (vídeo renderizado + medição pela cinemática real do rig)
Vídeos em 1080×1920, 30 qps, H.264. A câmera acompanha a pelve; as marcas no chão (perfil) andam com o mundo, então um pé que deslizasse ficaria visível.

| Teste | Arquivo | Resultado medido | Verificação visual |
|---|---|---|---|
| T2 caminhada · perfil | `T2_caminhada_perfil.mp4` | Erro de IK 0; **deslize do pé de apoio 0,0 % da altura**; maior variação 12,5°/quadro (joelho em balanço); braço × perna **−0,90** (em oposição); 25 quadros de apoio duplo; nenhum de voo | Ciclo completo coerente: contato, apoio, impulso, balanço |
| T2 caminhada · frente | `T2_caminhada_frente.mp4` | Maior variação 2,2°/quadro; tornozelo entre 0,25 e 0,29 H | Pés alternam, braços balançam cruzando para o meio do corpo, quadril balança. **Movimento mais contido que no perfil** (limitação do 2D, abaixo) |
| T2 caminhada · costas | `T2_caminhada_costas.mp4` | Maior variação 2,2°/quadro; tornozelo entre 0,20 e 0,32 H | Igual à frente, espelhado em profundidade |
| T3 corrida · perfil | `T3_corrida_perfil.mp4` | Erro de IK 0; **deslize 0,0 %**; **15 quadros em voo**, 0 de apoio duplo; braço × perna −0,83; maior variação 22,9°/quadro | Tronco inclinado, chute do calcanhar, cotovelos a 90°, pouso amortecido |
| T2 camadas | `T2_camadas_caminhada_olha_cima.mp4` | Mesmas métricas da caminhada (a camada não perturbou as pernas) | A camada só na cabeça inclina para olhar para cima com peso gradual; o braço incluído de propósito na camada **foi ignorado pela máscara**; expressão troca para alegria e volta; a piscada continua |

Cada teste tem `*_folha.jpg` (1 ciclo quadro a quadro) e `*_sobreposicao.png` (onion skin do ciclo). As métricas estão em `f2_metricas.json`.

## Problemas encontrados pelos testes e corrigidos
1. **Braços em fase com as pernas** (correlação +0,85): erro de sinal. Corrigido para −0,90.
2. **Salto de 33° num quadro** no joelho, na passagem do apoio para o balanço: o alvo do tornozelo caía de 0,33 H para 0,22 H. O balanço agora parte da altura em que o apoio terminou: 12,5°/quadro.
3. **Corrida com extensão de joelho de ~1.000°/s** antes do pouso (ritmo de velocista adulto). Ciclo alongado, chute suavizado e pelve mais baixa para pousar com o joelho flexionado: 22,9°/quadro.
4. **Frente e costas tímidos demais** (braços quase parados). Reforçados o balanço dos braços, a profundidade do pé e o balanço do quadril.
5. **O teste de camada dizia "olhar para trás"**, mas a rotação 2D faz a cabeça **inclinar para cima**. Renomeado para descrever o que de fato acontece.
6. A F1 foi reverificada depois das mudanças no esqueleto: as 6 vistas continuam OK.

## Limitações (registradas, não escondidas)
1. **Frente e costas são uma projeção 2D do ciclo de perfil.** Funcionam e são consistentes, mas o movimento é visivelmente mais contido que no perfil. A perna que vem para a câmera não cresce em tamanho; só encurta e desce. Na vista de costas, o antebraço que vai para a frente fica muito curto por escorço.
2. **Contato com o chão na frente e nas costas é aproximado:** o tornozelo varia de 0,20 a 0,32 H por causa do ajuste de profundidade, então o pé pode parecer flutuar ou afundar até ~0,03 H (~9 px num personagem de 1.150 px). No perfil o contato é exato (0,22 H).
3. **Sem 3/4 animado ainda.** O ciclo existe para perfil, frente e costas; o 3/4 precisaria de uma projeção própria.
4. **Virar a cabeça para trás, ou qualquer giro, exige trocar a vista** (por exemplo, a cabeça em 3/4 sobre o corpo de perfil). Ainda não implementado.
5. **Mãos na caminhada usam a vista padrão da vista do corpo.** Na frente, as mãos aparecem de lado, pequenas. Os dedos não animam durante a locomoção, exceto a mão semifechada da corrida.
6. **Blender CPU:** não afeta estes testes (personagem 2D, ~4 s para renderizar 100 quadros). Para levar o Heitor a um cenário 3D, segue valendo o plano da arquitetura: fundos estáticos do Blender em camadas e personagem no skia, com âncoras 3D → 2D.
7. **Naturalidade:** as métricas garantem pé plantado, continuidade e oposição braço/perna. A avaliação de "natural" é visual e cabe ao diretor.

## Próxima fase (só com autorização): F3
Mãos e gestos animados: dedos individuais em movimento (T4), segurar e soltar um objeto com IK do braço até o objeto (T5), acenar e apontar (T6), reações. Na F4: expressões animadas (T7), teste em cena (T8) e relatório final.
