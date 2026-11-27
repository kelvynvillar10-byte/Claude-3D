# Heitor — rig v2 (OFICIAL)

**Status: aprovado pelo diretor em 25/11/2026 como o rig oficial do Heitor** · **v2.2 (27/11/2026, aprovada): o braço se encaixa 0,08 H abaixo da linha do ombro (`ombro_braco` 2,68 H em `modelo.json`; a camiseta continua em 2,76 H) e o topo do braço fica dentro da manga (`braco_topo`), para o ombro não subir; F1 6/6, 0 cotovelos invertidos** (fases F1–F4; relatório final em [`RELATORIO_FINAL.md`](RELATORIO_FINAL.md)). Substitui o rig v1 do piloto 01 na produção. O piloto 01 continua como registro histórico, feito com o v1. As decisões ID-001 a ID-004 não mudaram. Os vídeos de teste em `testes/` foram renderizados durante a fase de proposta, por isso trazem o rótulo "PROPOSTA".

## Como usar na produção
- **Rig:** `codigo/heitor_v2.py`, função `desenhar(canvas, x_pe, y_pe, altura_px, vista, direcao, pose, rosto)`. Vistas: frente, tres_quartos, perfil, costas (direção −1 espelha; a estampa nunca espelha).
- **Animação:**
  - `codigo/animacao.py`: caminhada e corrida, camadas, piscada.
  - `codigo/gestos.py`: clipes com curvas, transição de expressões, IK de braço com cotovelo anatômico, mira, objeto na mão e regra do cotovelo.
  - `codigo/fala.py`: sincronia labial.
- **No cenário 3D:** o fundo vem do Blender e o Heitor é posicionado e escalado pelas âncoras 3D → 2D (exemplo completo: `codigo/cena_t8_blender.py` + `t8()` em `codigo/testes_f4.py`).
- **QA do personagem:**
  - `codigo/verificar_f1.py`: consistência entre vistas e estampa.
  - `codigo/verificar_cotovelos.py`: cotovelos.
  - Medição de oclusão da marca no cenário: ver `t8()`.

Fonte da verdade do personagem: a especificação oficial (`docs/IDENTIDADE_OFICIAL.md` e o skill), transcrita em [`modelo.json`](modelo.json): paleta hex, proporções em H (altura da cabeça; altura total 4 H), comprimento dos ossos e limites das juntas.

## O que a F1 entrega

| Item | Arquivo |
|---|---|
| Modelo (paleta, proporções, ossos, limites) | `modelo.json` |
| Rig: esqueleto com FK, peças por osso, 4 vistas, mãos, rosto | `codigo/heitor_v2.py` |
| Folha de modelo: giro com linhas de alinhamento (frente, 3/4, perfil, costas + espelhos) | `folhas/folha_modelo_v2.png` |
| Folha de mãos: 7 poses × dorso/palma/lado, cada dedo sozinho, contagem 1–5 | `folhas/folha_maos_v2.png` |
| Folha de expressões: 11 expressões de frente; surpresa, medo, alegria, preocupação em 3/4 e perfil | `folhas/folha_expressoes_v2.png` |
| Folha de articulações: poses estáticas que exercitam todas as juntas | `folhas/folha_articulacoes_v2.png` |
| Verificação automática de consistência entre ângulos | `verificacao/f1_consistencia.md` (+ `.json`) |

Para gerar tudo de novo: `../../../.venv/bin/python codigo/folhas.py && ../../../.venv/bin/python codigo/verificar_f1.py`

## Como o rig funciona
- **Esqueleto (FK):** raiz (pelve) → tronco → cabeça; tronco → braço → antebraço → mão → 5 dedos; raiz → coxa → canela → pé. Cada peça é desenhada **no sistema do seu osso**, então ombro, cotovelo, punho, quadril, joelho e tornozelo articulam de verdade.
- **Juntas limpas:** cada membro é preenchido por segmento e recebe **um contorno contínuo da união**, então a junta não "quebra" ao dobrar. Os dedos usam a mesma técnica.
- **Mãos:** polegar com 2 falanges e os outros quatro dedos com 3, cada junta com ângulo próprio. Na vista de dorso ou palma, a flexão encurta a falange (escorço), e acima de 90° ela dobra sobre a palma (punho). Na vista de lado, a flexão é rotação real.
- **Rosto paramétrico:** olhos pequenos e escuros com brilho (branco e arregalado só em surpresa e medo); pálpebras superior e inferior na cor da pele em volta; sobrancelha grossa por 3 parâmetros (canto interno, canto externo, arco); biblioteca de bocas. Sem bochecha rosada.
- **Identidade:** estampa "Modo Curioso" em Nunito ExtraBold, recebendo a sombra do tecido. Comprimida e deslocada no 3/4; ausente no perfil e nas costas. **Nunca espelhada**, nem nas vistas espelhadas.
- **Mais detalhe, dentro do estilo 2D chapado com 1 tom de sombra:** mechas e brilho no cabelo, dobra da orelha, dobras e costura da camiseta, bolsos e costuras do jeans, barra dobrada com espessura, tênis com sola, cadarço e faixa.

## Resultado da verificação automática (F1)
As 6 vistas passaram com tolerância de ±2 % da altura: topo 4,01 H, olhos 3,44 H, barra da camiseta 1,73 H e barra da calça iguais em todas as vistas. 96–97 % dos pixels caem na paleta oficial (o resto é antisserrilhado). A estampa foi lida por OCR na frente e no 3/4, inclusive espelhado, e não aparece no perfil nem nas costas.

## Limitações conhecidas (F1)
1. **Mudança de ângulo é discreta**, entre 4 vistas desenhadas (padrão do 2D), sem rotação contínua. A transição entre vistas será tratada na F2.
2. **Espelhos:** nas vistas viradas para a esquerda, o desenho é espelhado, então a franja e o redemoinho do cabelo trocam de lado anatômico. A estampa foi protegida contra isso; o cabelo ainda não.
3. **Mãos de frente para a câmera** são estilizadas. Em tamanho de cena, os detalhes dos dedos ficam pequenos (a mão tem ~0,4 H).
4. **Escorço** só existe nos dedos. Um braço apontando direto para a câmera, por exemplo, exige desenho específico (ainda não feito).
5. **Ainda não há IK, ciclos de caminhada e corrida, objetos nem animação.** Isso é da F2 a F4, que não foram iniciadas.
6. **O espessamento do contorno é proporcional à altura do personagem.** Em closes muito grandes, o traço fica mais grosso. Precisa de um limite por tamanho de tela.
7. **Blender CPU:** não afeta o personagem, que é 2D e leva milissegundos por quadro. Continua valendo o plano da arquitetura: fundos estáticos em camadas no Blender e personagem no skia.

## Fase F2 (concluída e aprovada pelo diretor em 25/11/2026)
IK, sistema de animação com camadas, caminhada (perfil, frente, costas) e corrida. Testes em vídeo e métricas: [`testes/F2_RELATORIO.md`](testes/F2_RELATORIO.md).

## Fase F4 (concluída e aprovada pelo diretor em 25/11/2026) e relatório final
Expressões animadas em 3 vistas com piscadas e fala de teste com sincronia labial (T7). Teste em cena: fundo 3D do Blender e Heitor 2D com âncoras (T8). Relatório: [`testes/F4_RELATORIO.md`](testes/F4_RELATORIO.md). **Relatório final do rig v2:** [`RELATORIO_FINAL.md`](RELATORIO_FINAL.md).

## Fase F3 (concluída e aprovada pelo diretor em 25/11/2026)
Dedos individuais, segurar e soltar um objeto (IK até o ponto de pega, objeto preso à mão, queda com quique), acenar, apontar (mira) e reações (susto e comemoração). Testes em vídeo e métricas: [`testes/F3_RELATORIO.md`](testes/F3_RELATORIO.md). Código: `codigo/gestos.py` e `codigo/testes_f3.py`.

## Plano original da F2
IK de 2 ossos (pé plantado e mão em alvo), sistema de animação com camadas, caminhada de frente, perfil e costas, e corrida, com os testes T2 e T3 renderizados em MP4 e medidos (deslize do pé, ciclo, ângulos).
