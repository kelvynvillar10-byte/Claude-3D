# Relatório da etapa E8 (parte 3): poder de aranha

26/11/2026 · Autorizada pelo diretor depois da aprovação da extensão X3 ("Pode começar").
- O rig v2 não foi alterado. O Heitor é desenhado com a **X3** (escalada, balanço no fio, gesto de lançar) e a **X2** (corpo inclinado e vento) e iluminado pela **X1**. As três estão aprovadas.
- **A elasticidade não foi iniciada.**
- Nenhum episódio ou história foi produzido.

## O que foi construído: `efeitos/poderes/aranha.py`
Um arquivo, registrado com `@efeito("aranha")`, que usa só o núcleo e as extensões aprovadas. Tem 6 fases, 3 intensidades, contatos na mão e na âncora, segurança, proteção do rosto e da estampa, e marcas que ficam.

Como o voo, **o poder controla o movimento do Heitor**. A cena só chama `desenhar_heitor(ctx, canvas)`; assim, o fio e o corpo estão sempre sincronizados.

| Modo | Sequência |
|---|---|
| `lancar` (de frente) | gesto de lançar (o próprio do Modo Curioso, palma aberta), o fio voa até o alvo e **gruda**, ele puxa, puxão, solta (o fio afrouxa e some). **O grude fica** |
| `balancar` (de perfil) | lança o fio para o alto e ele gruda; o fio **encurta** e ele sai do chão balançando. No **ponto mais baixo**, o puxão: tensão máxima, o fio vibra, tremida. Ele **solta** com o impulso do fio e sai do quadro; o fio volta e some, **o grude fica** |
| `escalar` (de costas) | escala a parede deixando **pegadas de grude**, para, lança um **leque de 4 fios**, uma **rede** se forma anel por anel, ele se puxa até a rede, que **estica e vibra**, e fica preso nela. **A rede e as pegadas ficam** |

| Fase | O que acontece |
|---|---|
| início | gesto (ou escalada com pegadas) |
| ativação | o fio sai da mão, ondulando, e **gruda** no alvo (mancha de grude: miolo, fios radiais e dois anéis) |
| uso | fio tenso (puxar), fio encurtando (sair do chão) ou a rede se formando |
| impacto | puxão máximo: o fio vibra; tremida (moderado/extremo); **quadro de impacto** (extremo) |
| dissipação | solta: o fio afrouxa ou volta e some; ou a rede balança e assenta |
| encerramento | o que fica: grude, pegadas e rede |

Outros pontos:
- **Família de cor:** seda marfim (`#ece3c6`) com um brilho branco fino. O fio **não emite luz**.
- **Intensidades:**
  - discreto: fio fino, grude pequeno, sem tremida;
  - moderado: fio mais grosso, tremida leve;
  - extremo: fio duplo no balanço, tremida forte e quadro de impacto.
- **Contato no balanço:** de perfil, a mão que segura fica atrás da cabeça (é a proporção do rig: o braço não passa da altura da cabeça). Por isso o fio sai do **alto do punho fechado**, que aparece acima do cabelo.

## Vídeo: `testes/e8_aranha/E8_aranha.mp4`
11,4 s (343 quadros) · 1080×1920 · 30 q/s · marca d'água "MODO CURIOSO" · legenda "aranha (teste, não é história)", com a intensidade e a **fase atual**. Quadros: `E8_aranha_quadros.jpg`.

| Clipe | Horário | Vista | Modo | Lugar |
|---|---|---|---|---|
| aranha · discreto | manhã | frente | lança e gruda | a placa "30" |
| aranha · moderado | tarde | perfil | balança e solta | o letreiro da quitanda |
| aranha · extremo | noite | costas | escala, rede, se puxa | o pilar entre as lojas e a fachada |

A placa do extremo é a da parede da X3, renderizada à noite para este clipe em 8,7 min. Ela fica no cache de placas.

## Medidas
| Teste | Resultado |
|---|---|
| **Ordem das intensidades, no MESMO clipe** (balançar, tarde) | pico de energia: discreto **0,002** < moderado **0,012** < extremo **0,028** ✅. Pico no impacto nos três |
| **Contatos** (no desenho real, a cada 3 quadros com o fio esticado) | o fio sai da mão (pixel de pele) em **100 %** nos 3 clipes; chega na âncora com erro **0,0 px** |
| **Família de cor** (ΔE) | × camiseta **76,7** · × ar do voo **23,8** · × eletricidade **44,8** · × "Modo" da estampa 12,4 (os dois são claros; o fio é fino e não cobre a estampa: ver proteção) |
| **Paleta do Heitor** (X1 desligada só aqui) | **99,97 % idêntica** em 93.234 pixels sem efeito na frente; os outros diferem no máximo **1 nível** (de 256) |
| **Segurança** (flashes por segundo, vídeo pronto) | **2 no vídeo inteiro**, no máximo **1 por segundo** (limite 3) |
| **Proteção do rosto e da estampa** (cobertura máxima) | discreto 0,00 / 0,00 · moderado: rosto **0,35** (o fio passa na frente do rosto no balanço e é limitado) · extremo 0,35 / 0,00 |
| **Determinismo** | mesmo quadro duas vezes: **idêntico** |
| **Regressão** | as 3 tomadas da cena de prova, sem efeitos: **idênticas** à referência da E7 |
| **Integridade** | assinatura de rig v2, identidade e skill **idêntica** (`068bf373…8342`); F1 6/6 OK |

### Tempo de composição (CPU, 1080×1920, com o Heitor, a X1 e o céu animado)
| Clipe | Média | Máximo |
|---|---|---|
| discreto | 3,54 s por quadro | 4,76 s |
| moderado | 3,36 s por quadro | 4,95 s |
| extremo | 5,16 s por quadro | 6,88 s |

Os 11,4 s de vídeo levaram ~23 min de composição.

## Problemas encontrados e corrigidos
1. **A mão passava na frente do rosto ao abaixar o braço.** A transição de poses interpolava o ângulo do braço pelo caminho longo, por exemplo de −200° a −8°. Agora os ângulos ficam entre −180° e 180° e o braço desce pelo lado.
2. **No balanço, o Heitor saía do quadro antes do puxão.** O pêndulo foi ajustado para que o ponto mais baixo caia no começo do impacto. A soltura vem depois, com um impulso do fio.
3. **O fio parecia sair do cabelo:** a palma fica atrás da cabeça no perfil. Agora o fio sai do alto do punho, que aparece.
4. **Medição corrigida:** a linha da palma (mistura de pele com a sombra da pele) era contada como erro de contato.

## Limitações (registradas, não escondidas)
1. **O fio e a rede são 2D** na tela (com profundidade para a oclusão), sem física de corda: tensão, vibração e afrouxar são desenhados, não simulados.
2. **O balanço é um pêndulo desenhado na tela**, e a âncora pode estar um pouco mais funda que o Heitor. Em câmeras muito oblíquas isso apareceria.
3. **De perfil, a mão do fio fica atrás da cabeça:** limite de proporção do rig (cabeça grande, braço curto).
4. **Pegadas e grude são decalques** (não deformam a parede).
5. **Energia medida** serve para comparar intensidades do mesmo poder, não poderes diferentes.

## Como reproduzir
```
.venv/bin/python cenografia/testes/e8_aranha_testes.py                      # tudo (vídeo ≈ 20 min; placa da parede à noite ≈ 9 min se não estiver no cache)
.venv/bin/python cenografia/testes/e8_aranha_testes.py previa /caminho.jpg  # quadros-chave
```

## Próximos passos (cada um só com aprovação)
1. **Proposta X4, elasticidade:** membros elásticos, só braços e pernas, apresentada à parte com justificativa, demonstração e testes; depois o poder de elasticidade (E8 parte 4).
2. **E9:** combinações (teste de ação de 10–15 s, sem história) e relatório final.
3. Os **dois achados da E8 parte 2** continuam aguardando sua decisão.
