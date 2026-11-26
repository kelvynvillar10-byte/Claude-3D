# Relatório da etapa E7 — núcleo de efeitos

26/11/2026 · Autorizada pelo diretor junto com a aprovação da E6 ("Autorizado e aprovado"). **Aguardando avaliação do diretor. A E8 (poderes) não foi iniciada.** Nenhum episódio ou história foi produzido. O Heitor rig v2 não foi alterado. **Nenhum poder foi feito:** os efeitos do vídeo são demonstrações de cada peça do núcleo.

Escopo do plano aprovado: "partículas, curvas, luz 2D, distorção, fases e registro de plugins". Seguimos a seção 3.1 da proposta (núcleo comum aos poderes) e a 3.3 (clareza, proteção de rosto e estampa, limite de flashes).

## O que foi construído (`efeitos/`)
| Peça | Arquivo | O que faz |
|---|---|---|
| **Parâmetros e intensidades** | `nucleo/base.py` | Todo efeito recebe os mesmos parâmetros: intensidade (**discreto ×0,45 · moderado ×1 · extremo ×1,8**), velocidade, cor, escala, duração, direção e semente |
| **Fases** | `nucleo/base.py` | Início → ativação → uso → impacto → dissipação → encerramento, cada fase com sua curva (`testes/e7/E7_fases.png`) |
| **Camadas por quadro** | `nucleo/base.py` + compositor | Marcas no chão; atrás do personagem; na frente do personagem; luz no cenário; tremida; distorção; quadro de impacto. **Toda camada tem profundidade por pixel**: o cenário mais perto a cobre |
| **Registro de plugins** | `nucleo/base.py` | `@efeito("nome")`. **Um poder novo é um arquivo novo em `efeitos/poderes/`**, que se registra sozinho; nada do núcleo é refeito |
| **Mesa (combinação)** | `nucleo/base.py` | No máximo **1 efeito dominante + 1 secundário (×0,5)** por plano; o resto é suprimido e registrado |
| **Partículas** | `nucleo/particulas.py` | Determinísticas por semente, em metros no mundo: gravidade, vento, arrasto, turbulência, quique no chão. Estilos: faísca (com rastro de movimento), poeira, fumaça e brilho |
| **Curvas fractais** | `nucleo/curvas.py` | Deslocamento do ponto médio em 3D com ramificações. **Pontas exatas nos contatos.** Redesenho a cada 2 quadros. Halo colorido + núcleo claro |
| **Corda com física** | `nucleo/corda.py` | Verlet com restrição de comprimento; ponta presa e ponta móvel ou solta (pêndulo). Base para teias |
| **Luz 2D no cenário** | compositor (`luz_extra`) | Ponto de luz que ilumina a placa usando o **albedo** e a **profundidade** (posição e normal de cada pixel): albedo × força × cosseno ÷ (d² + r²), antes do mapeamento de tons e com a névoa |
| **Distorção** | `nucleo/distorcao.py` | Onda de choque (anel achatado pela perspectiva) e calor (tremulação acima de uma fonte) |
| **Marcas que ficam** | `nucleo/marcas.py` | Queimado e rachadura, projetados no chão em perspectiva real (homografia dos 4 cantos) |
| **Rastros** | `nucleo/rastros.py` | Fita que segue o histórico de posições; borrão direcional |
| **Quadro de impacto** | `nucleo/impacto.py` | Padrão do skill: silhueta clara sobre linhas radiais e estilhaços brancos sobre azul-marinho, por 2 quadros |
| **Tremida** | `nucleo/tremida.py` | Padrão do skill: ~1,4 % do quadro, 0,25–0,6 s, decaindo; desloca o recorte pela margem da placa (não aparece borda) |
| **Contatos** | `nucleo/contatos.py` | Mão, pé, cabeça e peito **calculados com o esqueleto do próprio rig v2** (só leitura), e qualquer ponto 3D do cenário (fachada, poste, chão) |
| **Segurança (fotossensíveis)** | `nucleo/seguranca.py` | O governador limita os **flashes por segundo** (3); o analisador confere o vídeo pronto (regra de "flash geral" da WCAG 2.3.1, simplificada) |
| **Proteção de rosto e estampa** | `nucleo/protecao.py` | Na camada da frente, o efeito cobre **no máximo 35 %** do rosto e da estampa "Modo Curioso" |

**Mudanças na cenografia** (compatíveis com tudo o que já existia):
- a placa grava também o **albedo** de cada camada;
- o compositor ganhou os encaixes dos efeitos (`compor(..., efeitos=mesa, deslocamento_px=...)`).

**Sem efeitos, o caminho do código é o mesmo, e o quadro sai idêntico** (ver E7-1).

**Luz no personagem ("tom de luz"):** o núcleo calcula e registra a luz que o efeito jogaria no Heitor, mas **não a aplica**. Aplicar é extensão do rig e depende de aprovação específica.

## Vídeo de demonstração: `testes/e7/E7_nucleo_efeitos.mp4`
23,4 s · 1080×1920 · 30 q/s · marca d'água "MODO CURIOSO" · legenda "demonstração, não é poder", com a **fase atual** de cada efeito.

São 8 cenas curtas na rua da E6, com o Heitor parado (respirando e piscando) e um leve avanço de câmera:
1. faíscas saindo da mão;
2. arco fractal da mão até a fachada;
3. poeira;
4. calor com fumaça;
5. corda presa na fachada (a mão solta no impacto);
6. onda de choque com tremida, rachadura e quadro de impacto;
7. orbe de luz à noite;
8. combinação (faíscas dominantes + orbe secundário).

Folha com um quadro de cada: `E7_cenas.jpg`. Luz 2D antes/depois: `E7_luz2d.jpg`.

## Medidas
| Teste | Resultado |
|---|---|
| **E7-1 Regressão** (assinatura guardada antes da mudança) | Os 3 quadros da E6, compostos com o código novo e sem efeitos, saem **idênticos**. A placa nova, que ganhou a passada de albedo, também dá o **mesmo quadro** |
| **E7-2 Fases** (3 s) | Limites: início 0–0,24 · ativação 0,24–0,66 · uso 0,66–1,80 · impacto 1,80–2,10 · dissipação 2,10–2,76 · encerramento 2,76–3,00 s. Pico no impacto: 1,35. O envelope começa e termina em zero; maior salto entre amostras de 1 ms: 0,023 (contínuo) |
| **E7-3 Partículas** | Mesma semente: **idênticas**; outra semente: diferentes |
| ↳ queda livre em 1 s | 5,054 m contra 5,095 m da fórmula: erro de **4,1 cm**, do passo fixo da simulação |
| ↳ quique (restituição 0,5) | Rebote de **0,245 m**; esperado 0,25 m |
| ↳ arrasto (velocidade terminal g/k) | **4,905 m/s**, igual à fórmula |
| ↳ vento de 1,5 m/s | Velocidade horizontal **1,500 m/s** |
| **E7-4 Corda** | Esticamento máximo de **0,73 %**. Pêndulo de 1 m: período de **1,69 s**, entre a haste uniforme (1,64 s) e o pêndulo simples (2,01 s), como esperado para uma corda |
| **E7-5 Curva fractal** | Erro nas pontas: **0,0 m** (toca exatamente os contatos). 65 pontos e 3 ramos. Determinística. Muda a cada 2 quadros |
| **E7-6 Luz 2D** | **Céu intacto**: 8 de 253.432 pixels de céu mudaram (bordas). Força recuperada a partir da imagem: **3,0** a menos de 2 m e **3,0** a mais de 3 m, igual à usada. Ou seja, **a queda com a distância segue a fórmula** |
| **E7-7 Profundidade** | Brilho **atrás do hidrante**: 23 % visível (o hidrante cobre o resto); **na frente**: 100 % visível |
| **E7-8 Segurança** (estrobo que pisca a 7,5/s) | Sem governador: **8 flashes em 1 s**. Com governador: **3 em 1 s**, exatamente o limite. Testado com área mínima de 5 % da tela, mais rigoroso que os 25 % da regra |
| **E7-9 Proteção** (brilho forte sobre o rosto) | Sem proteção: cobertura **1,00** no rosto e na estampa. Com proteção: **0,35** e **0,35**, o limite |
| **E7-10 Combinação** (3 efeitos ativos) | Ganhos: faíscas (extremo) ×1 · poeira ×0,5 · calor (discreto) **×0, suprimido e registrado** |
| **E7-11 Registro** | Um arquivo novo com `@efeito("poder_de_teste")` **registrou sozinho**, sem tocar no núcleo |
| **E7-13 Integridade** | Assinatura de rig v2, identidade e skill **idêntica** (`068bf373…8342`); F1 6/6 OK |

### Tempo de composição (CPU, 1080×1920, com o Heitor e o céu animado)
| Cena | Média | Máximo |
|---|---|---|
| calor + fumaça | 2,24 s/quadro | 2,65 s |
| corda | 2,36 | 2,70 |
| faíscas | 3,32 | 5,08 |
| arco fractal | 3,37 | 3,72 |
| poeira | 3,43 | 6,20 |
| onda de choque (com marca e poeira) | 3,69 | 7,70 |
| orbe com luz 2D | 3,82 | 5,19 |
| combinação (2 efeitos) | 4,82 | 5,32 |

Sem efeitos, a composição da E6 era ~2,0 s por quadro; **cada efeito soma ~0,2–1,8 s**. Os picos vêm de muitas partículas de poeira desenhadas uma a uma em Python. Os 23,4 s do vídeo levaram ~40 min. Otimização possível: desenhar as partículas em lote.

## Problemas encontrados e corrigidos
1. **O 1º arco saiu grosso demais** e crescia em direção à lente (alvo a 2 m da câmera). Traço mais fino e alvo na fachada.
2. **Onda de choque quase invisível** (rachadura fina, longe). Rachadura maior e à frente do Heitor, anel de poeira visível e distorção mais forte.
3. **Orbe estourando em disco branco.** Núcleo menor e halo mais suave.
4. **Medição do quique** pegava o 2º contato com o chão (rebote "0"). A simulação estava certa (0,245 m); a medição foi corrigida.
5. **Analisador de flashes contava cada inversão como um flash** (dava 6/s com o governador). Pela regra, flash é um **par** sobe+desce; corrigido, dá 3/s.
6. **A proteção limitava alfa e brilho separadamente** (cobertura somada de 0,70). Agora limita a soma: 0,35.
7. **O teste da luz 2D misturava canais de cor** e não chegava à força usada; refeito canal a canal.
8. **A seta "↔" aparecia como caixa** na legenda (a fonte não tem esse caractere). Trocada por texto.

## Limitações (registradas, não escondidas)
1. **O Heitor não recebe a luz dos efeitos** (faíscas, orbe): o "tom de luz" é calculado e registrado, mas não aplicado. É extensão do rig, que depende da sua aprovação.
2. **A luz 2D não projeta sombras:** ilumina o cenário pela profundidade e pela normal, mas um objeto não faz sombra em outro. As luzes de efeito pré-posicionadas no Blender (grupo de luz "efeito", da E0) continuam disponíveis para sombra real em posições fixas.
3. **Cada curva tem uma profundidade única** (a média), não por segmento. Um raio longo que passa atrás e na frente de um objeto pode ser coberto de uma vez.
4. **Poeira e fumaça são manchas suaves**, sem volume nem luz própria. Leem como nuvem de poeira, sem acabamento de simulação.
5. **A composição ficou mais lenta com efeitos** (2,2–4,8 s por quadro). Viável em CPU, mas um plano de ação longo pede otimização das partículas.
6. **A regra de flashes é simplificada** (não considera vermelho saturado nem a área exata de 341×256 px da norma).
7. **Os demos não são poderes.** Eletricidade, terra, voo, aranha e elasticidade são da E8. Voo, aranha e elasticidade dependem de extensões do rig, só com aprovação específica.

## Como reproduzir
```
.venv/bin/python cenografia/testes/e7_testes.py                       # tudo (≈ 55 min com o vídeo)
.venv/bin/python cenografia/testes/e7_testes.py E7_3_particulas E7_4_corda E7_5_curva   # só a física (segundos)
```

## Próxima etapa (só com aprovação): E8 — poderes
Pelo plano aprovado: **primeiro eletricidade e terra**, que não mexem no rig, usando só o núcleo. Cada poder será um arquivo em `efeitos/poderes/`, com as fases, as 3 intensidades, a família de cores própria (contrastando com o azul da camiseta), os contatos no rig e no cenário, a luz no cenário e as regras de segurança e proteção. Voo, aranha e elasticidade só avançam depois da aprovação das extensões do rig que eles exigem.
