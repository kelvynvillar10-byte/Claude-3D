# Relatório da etapa E9: combinações de poderes (teste de ação)

26/11/2026 · Autorizada pelo diretor junto com a aprovação da E8 parte 4 ("Aprovado e pode seguir"). **É um teste de ação, NÃO é história:** não há roteiro, falas, narração nem episódio.
- O rig v2 não foi alterado.
- Usa só o que já foi aprovado: núcleo E7, os 5 poderes da E8 e as extensões X1–X4.
- Nada novo foi criado no núcleo nem nos poderes; esta etapa só **combina e mede**.

## O que foi feito: `cenografia/testes/e9_testes.py`
Três planos. Em cada um, um poder **dominante** (que também move o Heitor) e um **secundário**; a mesa do núcleo reduz o secundário a 0,5.

| Plano | Horário · vista | Dominante | Secundário | Extra |
|---|---|---|---|---|
| C1 | manhã · frente | **terra extremo**: rachadura, pedaços, pilar, cratera | **eletricidade moderada** no mesmo alvo: o raio sai da mão que comanda a terra | um 3º efeito ligado de propósito (poeira de demonstração), que a mesa **tem de suprimir** |
| C2 | tarde · perfil | **elasticidade**: pega a laranja na prateleira | **eletricidade**: a mão e o corpo elétricos enquanto o braço estica | — |
| C3 | noite · costas | **voo**: decolagem vertical, rachadura, anéis e cone de vapor | **eletricidade**: arcos pelo corpo durante a subida | — |

## Vídeo: `testes/e9/E9_combinacoes.mp4`
10,2 s (306 quadros) · 1080×1920 · 30 q/s · marca d'água "MODO CURIOSO" · legenda "combinações (teste, não é história)", com a combinação e a fase do dominante. Quadros: `E9_quadros.jpg`.

## Medidas
| Teste | Resultado |
|---|---|
| **Regra da mesa** (a cada quadro, nos 3 planos) | **0 quadros** com dois dominantes; o secundário nunca passa de **0,5** do dominante. No C1, o 3º efeito esteve ativo em 91 quadros e foi **suprimido e registrado nos 91** |
| **Contatos** | C1: o raio sai da mão do rig com erro **0,0 px**. C2 (braço esticado pela X4) e C3 (voando pela X2): o brilho da mão da eletricidade cai sobre a pele no desenho real em **100 %** (21 e 17 amostras) |
| **Segurança** (vídeo pronto) | **2 flashes no vídeo inteiro**, no máximo **1 por segundo** (limite 3) |
| **Proteção do rosto e da estampa** | máximo **0,35** nos 3 planos (limitado, nunca acima) |
| **Determinismo** | mesmo quadro duas vezes: **idêntico** |
| **Regressão** | as 3 tomadas da cena de prova, sem efeitos: **idênticas** à referência da E7 |
| **Integridade** | assinatura de rig v2, identidade e skill **idêntica** (`068bf373…8342`); F1 6/6 OK |

### Tempo de composição (CPU, 1080×1920, 2–3 efeitos, X1, céu animado)
| Plano | Média | Máximo |
|---|---|---|
| C1 (terra + eletricidade + 3º suprimido) | 6,56 s por quadro | 8,23 s |
| C2 (elasticidade + eletricidade) | 5,36 s por quadro | 9,79 s |
| C3 (voo + eletricidade) | 6,69 s por quadro | 9,43 s |

Combinar dois poderes custa ~1,5–2× o tempo de um poder sozinho. Os 10,2 s levaram ~32 min de composição.

## O que eu vi nos quadros
- **C1:** o raio e a rachadura saem da mesma mão e vão ao mesmo alvo; o pilar sobe com o raio ainda no ar; quadro de impacto no pico.
- **C2:** o braço esticado com arcos elétricos; a laranja vem na mão elétrica.
- **C3:** a decolagem com os arcos e os anéis de vapor juntos.

**O que não foi verificado:** a leitura estética das combinações é sua.

## Limitações (registradas, não escondidas)
1. **Só 2 poderes ao mesmo tempo** por plano, por regra da mesa (1 dominante + 1 secundário). Um terceiro é suprimido de propósito.
2. **Só a eletricidade foi usada como secundária**, porque os outros 4 poderes também movem o corpo do Heitor, e dois poderes não podem mover o corpo ao mesmo tempo. Combinar, por exemplo, voo com aranha pede uma coreografia própria (um passa o controle do corpo para o outro), que é trabalho de produção.
3. **O achado do núcleo** (brilhos lidos não pré-multiplicados, E8 parte 2) continua: a eletricidade secundária aparece com o mesmo brilho aprovado na E8 parte 1.

## Como reproduzir
```
.venv/bin/python cenografia/testes/e9_testes.py          # tudo (vídeo ≈ 35 min)
.venv/bin/python cenografia/testes/e9_testes.py E9_contatos
```

## Encerramento
O relatório final de toda a fase (E0–E9) está em [`../RELATORIO_FINAL.md`](../RELATORIO_FINAL.md).
