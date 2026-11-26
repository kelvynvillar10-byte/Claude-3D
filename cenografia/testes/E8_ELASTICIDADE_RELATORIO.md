# Relatório da etapa E8 (parte 4): poder de elasticidade

26/11/2026 · Autorizada pelo diretor junto com a aprovação da extensão X4 ("Aprovado e pode continuar"). **E8 parte 4 APROVADA pelo diretor em 26/11/2026** ("Aprovado e pode seguir").
- O rig v2 não foi alterado. O Heitor é desenhado com a **X4** (estica só antebraço e coxa; a mão, a manga, a barra e o tênis são os do rig) e iluminado pela **X1**.
- Com esta parte, os **5 poderes** da ordem aprovada estão feitos: eletricidade, terra, voo, aranha e elasticidade.
- Nenhum episódio ou história foi produzido.

## O que foi construído: `efeitos/poderes/elasticidade.py`
Um arquivo, registrado com `@efeito("elasticidade")`, que usa só o núcleo e a X4. Tem 6 fases, 3 intensidades, contatos na mão e no chão, segurança e proteção do rosto e da estampa. **O poder controla o movimento** (a cena chama `desenhar_heitor`).

| Modo | Sequência |
|---|---|
| `tocar` (de frente) | o braço recua um pouco, **estica** até a placa "30", toca (ondas de mola na mão), **vibra** esticado e volta com um **estalo** (ondas no ombro) e um quique |
| `pegar` (de perfil) | estica até a prateleira da quitanda, **fecha a mão na laranja**, volta num estalo **trazendo a laranja** e fica com ela na mão |
| `pernas_de_pau` (de costas) | as pernas crescem até 2,6×, ele espia por cima, e voltam num estalo: **pisão** (anel de poeira, onda no chão, tremida, quadro de impacto no extremo) |

| Fase | O que acontece |
|---|---|
| início | preparação: o braço recua um pouquinho |
| ativação | **estica** (mola com passada): **linhas de tensão** finas e onduladas ao lado do membro; linhas de velocidade atrás da mão |
| uso | segura esticado e **vibra**; toca ou pega |
| impacto | **estalo de volta** (ondas de mola ")))"), tremida; no extremo, pisão e quadro de impacto |
| dissipação | a mola assenta (quique) e a poeira do pisão baixa |
| encerramento | de volta ao corpo original, **exato** (garantido pela X4) |

Outros pontos:
- **Família de cor:** rosa-mola (`#ff6fb5`) com um tom claro; não emite luz.
- **A laranja** é um objeto simples desenhado pelo próprio poder (não faz parte da placa).
- **Ficaram de fora de propósito** o soco esticado e os golpes de borracha de personagens de terceiros.

## Vídeo: `testes/e8_elasticidade/E8_elasticidade.mp4`
8,9 s (267 quadros) · 1080×1920 · 30 q/s · marca d'água "MODO CURIOSO" · legenda "elasticidade (teste, não é história)", com a intensidade e a **fase atual**. Quadros: `E8_elasticidade_quadros.jpg`.

| Clipe | Horário | Vista | Modo |
|---|---|---|---|
| elasticidade · discreto | manhã | frente | toca a placa "30" |
| elasticidade · moderado | tarde | perfil | pega a laranja na prateleira |
| elasticidade · extremo | noite | costas | pernas de pau e pisão |

## Medidas
| Teste | Resultado |
|---|---|
| **Ordem das intensidades, no MESMO clipe** (pegar, tarde) | pico de energia: discreto **0,002** < moderado **0,011** < extremo **0,026** ✅. Pico no estalo (impacto) |
| **Contatos** | a palma chega ao alvo com erro **0,0 px** (mola em repouso); a vibração da mola passa **6 px** (discreto) e **17 px** (moderado) em volta do alvo, de propósito. A palma cai sobre pele em **100 %**. Nas pernas de pau, a sola fica a **0,2–1,2 px** do chão em todo o clipe |
| **Família de cor** (ΔE) | × camiseta **69,1** · × pele 62,4 · × eletricidade 98,1 · × ar do voo 67,5 · × seda da aranha 72,2 · × "Curioso" da estampa 104,6 |
| **Segurança** (flashes, vídeo pronto) | **0 no vídeo inteiro** |
| **Proteção do rosto e da estampa** | discreto: rosto e estampa **0,35** (as linhas de tensão do braço levantado passam perto, limitadas) · moderado: rosto 0,35 · extremo: 0,00 |
| **Paleta do Heitor** (X1 desligada só aqui) | **100 % idêntica** em 100.905 pixels |
| **Determinismo** | mesmo quadro duas vezes: **idêntico** |
| **Regressão** | as 3 tomadas da cena de prova, sem efeitos: **idênticas** à referência da E7 |
| **Integridade** | assinatura de rig v2, identidade e skill **idêntica** (`068bf373…8342`); F1 6/6 OK |

### Tempo de composição (CPU, 1080×1920, com o Heitor, a X1 e o céu animado)
| Clipe | Média | Máximo |
|---|---|---|
| discreto | 3,32 s por quadro | 4,96 s |
| moderado | 4,33 s por quadro | 6,18 s |
| extremo | 4,27 s por quadro | 5,48 s |

## Problemas encontrados e corrigidos
1. **As linhas de tensão nas pernas pareciam veias rosas por cima do jeans.** Agora ficam só do lado de fora de cada perna, com menos ondulação.
2. **Medição corrigida:** o erro "palma no alvo" misturava a vibração proposital da mola com o contato. Agora são duas medidas separadas.

## Limitações (registradas, não escondidas)
1. **O membro estica em linha reta** (limite da X4): não faz curva nem enrola.
2. **As linhas de tensão e as ondas são 2D**, desenhadas na tela.
3. **A laranja é um objeto simples** do poder: os objetos da prateleira da placa não se mexem.
4. **Energia medida** serve para comparar as intensidades do mesmo poder, não poderes diferentes.

## Como reproduzir
```
.venv/bin/python cenografia/testes/e8_elasticidade_testes.py                      # tudo (vídeo ≈ 18 min)
.venv/bin/python cenografia/testes/e8_elasticidade_testes.py previa /caminho.jpg  # quadros-chave
```

## Próximos passos (cada um só com aprovação)
1. **E9:** combinações de poderes (teste de ação de 10–15 s, sem história) e relatório final da cenografia e dos efeitos.
2. Os **dois achados da E8 parte 2** continuam aguardando sua decisão.
