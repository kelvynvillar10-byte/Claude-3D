# Relatório final — Heitor rig v2 (PROPOSTA)

25/11/2026 · Fases F1 a F4 concluídas. **Status: PROPOSTA aguardando a aprovação final do diretor.** O rig v2 não substitui nada até essa aprovação. As decisões ID-001 a ID-004 não foram alteradas, e o rig v1 do piloto 01 continua intacto.

## Objetivos pedidos × entregue
| Objetivo | Entregue | Onde ver |
|---|---|---|
| Mais detalhe visual, mesma identidade | Mechas e brilho no cabelo, dobras e costura da camiseta, bolsos do jeans, tênis com sola e cadarço; paleta e proporções oficiais (verificação 6/6) | `folhas/`, `verificacao/f1_consistencia.md` |
| Mãos com 5 dedos individuais | Polegar com 2 falanges e os outros dedos com 3; dorso, palma e lado | `folhas/folha_maos_v2.png`, `testes/T4_*` |
| Ombro, cotovelo, punho, quadril, joelho, tornozelo | Esqueleto FK com essas juntas; IK de 2 ossos; escorço sem herança entre ossos | `folhas/folha_articulacoes_v2.png` |
| Rosto melhor | 11 expressões paramétricas; olhar; piscada (também no olho arregalado); transições sem "pulo"; sincronia labial | `testes/T7_*` |
| Sistema de animação reutilizável | `animacao.py` (ciclos, camadas, piscada), `gestos.py` (clipes, curvas, IK de braço, mira, objeto, regra do cotovelo), `fala.py` (sincronia labial) | `codigo/` |
| Caminhada e corrida | Perfil, frente e costas; pé plantado (deslize 0,0); braço em oposição à perna (−0,90) | `testes/T2_*`, `T3_*` |
| Apontar, acenar, segurar, reagir | Mira exata (0,0°), aceno a 2,2 Hz, objeto preso à mão (0,0), susto e comemoração | `testes/T5_*`, `T6_*`, `T6b_*` |
| Preservar a identidade | Estampa "Modo Curioso" lida por OCR e nunca espelhada; marca d'água e pôster "MODO CURIOSO" (ID-004) lidos por OCR; pôster nunca coberto no T8 | relatórios F1, F4 |

## Testes obrigatórios
| Teste | Resultado | Relatório |
|---|---|---|
| Andar de frente, perfil e costas | Feito e medido | F2 |
| Correr | 15 quadros em voo; deslize 0,0 | F2 |
| Dedos individuais | Cada dedo se move sozinho (os outros: 0,0°) | F3 |
| Pegar e soltar objeto | Pega, segura sem descolar, solta, cai e quica | F3 (T5), F4 (T8) |
| Acenar e apontar | 2,2 Hz; mira 0,0° | F3 |
| Surpresa, medo, alegria, preocupação | Estáticas na F1; animadas e em 3 vistas na F4 | F1, F4 |
| Consistência entre ângulos | 6 vistas medidas (topo, olhos, barras ±2 %) | F1 |
| Cena real | Fundo 3D do Blender + personagem 2D, com âncoras | F4 (T8) |

## Correções feitas a pedido do diretor durante o processo
- **Cotovelos invertidos** (aceno, susto, punho e folha da F1). Corrigidos, com regra anatômica verificável e auditoria automática (`verificacao/cotovelos.md`): 0 invertidos em F1–F4.
- **Herança do escorço entre ossos.** Corrigida; a F2 foi re-medida (perfil idêntico; frente e costas com o pé de apoio exato).

## Limitações que continuam (detalhes nos relatórios de cada fase)
1. **Vistas discretas:** frente, 3/4, perfil e costas, sem rotação contínua; as viradas são trocas de desenho.
2. **Caminhada de frente e de costas** é projeção do ciclo de perfil: mais contida, com profundidade aproximada. Não há caminhada em 3/4.
3. **Espelhamento:** nas vistas viradas para a esquerda, o lado do cabelo inverte. A estampa está protegida contra isso; o cabelo, não.
4. **Mãos de frente em tamanho de cena** são pequenas (~115 px); dedos isolados só leem em close.
5. **Voz temporária** (espeak-ng); a sincronia por sílaba é aproximada.
6. **Personagem 2D sobre fundo 3D:** a luz do cenário não muda o personagem, e ele não passa atrás de objetos sem camada de primeiro plano.
7. **Blender CPU:** ~75 s por fundo estático. Animar a cena 3D quadro a quadro é inviável. Seguimos com fundo estático + personagem 2D, conforme a arquitetura.

## Como regerar e verificar tudo
```
cd personagens/heitor/rig_v2_PROPOSTA
../../../.venv/bin/python codigo/folhas.py && ../../../.venv/bin/python codigo/verificar_f1.py
../../../.venv/bin/python codigo/testes_f2.py
../../../.venv/bin/python codigo/testes_f3.py
../../../.venv/bin/python codigo/cena_t8_blender.py --amostras 64   # fundo do T8 (~75 s em CPU)
../../../.venv/bin/python codigo/testes_f4.py
../../../.venv/bin/python codigo/verificar_cotovelos.py
```

## Decisão pendente do diretor
Aprovar (ou não) o **Heitor rig v2** como o rig oficial. Se aprovado, a sugestão é trocar o rig v1 pelo v2 no pipeline (arquitetura, seção 15) e atualizar o skill. Isso **não** inicia nenhum vídeo de história, que continua dependendo da sua autorização.
