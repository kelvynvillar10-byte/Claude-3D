# Cenografia — biblioteca de cenários do Modo Curioso Studio AI

Direção aprovada pelo diretor em 25/11/2026:
- cenografia **procedural no Blender** (Cycles, CPU) e poderes/efeitos **2D e 2.5D no compositor**;
- estilo **estilizado com acabamento cinematográfico**;
- ambientação padrão **bairro urbano brasileiro**;
- sem sites externos de texturas ou modelos.

**Etapas:** E0 (fundamentos) aprovada em 25/11/2026. E1 (materiais, céu e atmosfera, tempo de render) aprovada. **E2 (ruas e calçadas) em andamento.** Os componentes de cena da E0 são provisórios; os kits detalhados vêm nas etapas E2–E5, e só com autorização.

O personagem oficial é o **Heitor rig v2** (`personagens/heitor/rig_v2/`). A cenografia **não altera o rig**: o Heitor é desenhado por cima do cenário pelo compositor, com a paleta oficial intacta. Valem as decisões ID-001 a ID-004 (`docs/IDENTIDADE_OFICIAL.md`).

## Como funciona
```
receita JSON ──► construir.py ──► Blender (Cycles CPU) ──► PLACA em camadas (cache) ──► compositor 2.5D ──► quadro
                  (chave = hash      componentes            céu · longe · meio ·          luz por grupo, névoa,
                   da receita          registrados          perto · frente;               câmera com paralaxe,
                   + código)                                cada camada com uma passada   Heitor rig v2, gradação
                                                            por grupo de luz, alfa e
                                                            profundidade (EXR linear)
```

| Peça | Arquivo | O que faz |
|---|---|---|
| Receita | `receitas/*.json`, `nucleo/receita.py` | Descreve a cena inteira (saída, câmera, horário, camadas, componentes com parâmetros e semente). Valida a receita e calcula a **chave**: hash da receita + versão do núcleo + código dos geradores |
| Componentes | `nucleo/registro.py`, `componentes/*.py` | `@componente("nome")` registra um gerador. A receita chama pelo nome. Kits novos só registram funções, sem mexer no núcleo |
| Materiais | `nucleo/materiais.py` | Biblioteca procedural (asfalto com agregado e rachaduras, concreto em placas, reboco com escorridos e sujeira na base, tijolo, pintura, vidro, emissor, folhagem, terra). Parâmetros: cor, escala, desgaste, sujeira |
| Geometria | `nucleo/geometria.py` | Primitivas com **chanfro real**, deformação orgânica, espalhamento por semente com distância mínima |
| Luz | `nucleo/luz.py` | Céu físico do Blender + sol por preset de horário. **Grupos de luz:** `ceu`, `sol`, `artificial`, `efeito` |
| Câmera | `nucleo/camera.py` | Overscan (a placa é 25 % maior, mesmo enquadramento central), intrínsecos e âncoras 3D → 2D |
| Render | `nucleo/render.py` | Uma passada por camada. Os objetos das outras camadas **continuam fazendo sombra e reflexo**, mas não aparecem para a câmera, então cada camada sai inteira, sem buracos. EXR linear com uma passada limpa (OIDN) por grupo de luz, mais alfa e profundidade |
| Cache | `nucleo/cache.py` | `.cache/cenografia/<chave>/` (fora do Git) com manifesto e sha256 de cada arquivo. Arquivo faltando ou alterado invalida o cache |
| Compositor | `nucleo/compositor.py` | Reiluminação (Σ peso × cor × passada), névoa por distância, **paralaxe por pixel** pela profundidade, personagem entre as camadas, mapeamento fílmico e gradação (sombras roxo-azuladas, altas luzes quentes, brilho, vinheta, grão) |
| QA | `nucleo/medidas.py`, `testes/e0_testes.py`, `testes/e1_testes.py` | Medidas de cor iguais às da auditoria das referências; testes da E0 e da E1 |
| **E1 · materiais de bairro** | `nucleo/materiais.py` | + calçada portuguesa, ladrilho hidráulico, pastilha, azulejo, telha cerâmica, concreto aparente, metal com ferrugem, madeira (pintada ou não), grama; `PALETA_BAIRRO`; **umidade** (piso molhado com poças); mapeamento parede/piso para padrões em superfícies verticais |
| **E1 · horários** | `nucleo/luz.py` | manhã, meio-dia, tarde dourada, crepúsculo, noite (céu em degradê + lua como luz fria). Cada horário é uma placa (o sol muda de lugar) |
| **E1 · céu e clima** | `nucleo/ceu2d.py`, `nucleo/atmosfera.py` | Nuvens 2D em 3 camadas com deriva e luz do sol; lua com fase; estrelas; chuva em 3 profundidades. Climas: limpo, nublado, neblina, chuva (chuva usa a placa com piso molhado) |
| **E1 · tempo de render** | `construir.py` (`amostras_por_camada`) | Amostras por camada (céu 4 · longe 16 · meio 24 · perto 24 · frente 16): ~2,8 min por placa, dentro da meta |
| **E2 · kit de rua** | `componentes/rua.py` | `rua_trecho` (asfalto com remendos, faixas, sarjeta, tampas, bocas de lobo, calçada por lote com rebaixo de garagem, piso tátil, canteiros, folhas e mato), `cruzamento` (esquinas arredondadas, zebras, faixas de retenção), `poste_concreto` (cruzeta, isoladores, luminária LED acesa no grupo artificial, transformador, número), `fiacao` (catenárias e sobras de cabo), `semaforo`, `placa_rua`, `placa_regulamentacao`, `hidrante`, `lixeira_poste` |
| **E2 · QA da cena** | `nucleo/qa_cena.py` | Roda no Blender antes do render e vai para o manifesto: nada flutuando (raio para baixo; peças presas marcadas `suspenso`), lista exata dos textos 3D (comparada com `textos_permitidos` da receita), medidas de escala |

## Uso
```
.venv/bin/python cenografia/construir.py cenografia/receitas/e0_calcada.json      # renderiza, ou HIT no cache
.venv/bin/python cenografia/testes/e0_testes.py                                    # todos os testes da E0
```
```python
from cenografia.nucleo.compositor import Placa
P = Placa(".cache/cenografia/<chave>")
quadro = P.compor(pesos={"ceu": 1, "sol": 1, "artificial": 0.25, "efeito": (6, "#5fb8ff")},
                  cam={"tx": 0.3, "tz": 1.4}, nevoa={"cor": "#d9c2a6", "densidade": 0.006},
                  personagem=funcao_que_desenha_o_heitor, grade={...})
```

Resultados e limitações: [`testes/E0_RELATORIO.md`](testes/E0_RELATORIO.md) e [`testes/E1_RELATORIO.md`](testes/E1_RELATORIO.md) e [`testes/E2_RELATORIO.md`](testes/E2_RELATORIO.md).
