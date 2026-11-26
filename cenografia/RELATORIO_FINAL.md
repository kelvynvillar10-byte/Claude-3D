# Relatório final: cenografia, efeitos e poderes (E0–E9)

26/11/2026 · Modo Curioso Studio AI · **Documento de encerramento das etapas de cenografia e efeitos, para avaliação do diretor.** Nenhum episódio ou história foi produzido: tudo aqui são **testes**. O rig v2 do Heitor nunca foi alterado; a assinatura de rig v2, identidade e skill é a mesma do início ao fim (`068bf373…8342`), e o F1 dá 6/6 em toda etapa.

## 1. O que existe agora
| Parte | Onde | O que faz |
|---|---|---|
| **Cenografia procedural** | `cenografia/` | Bairro urbano brasileiro montado por **receita JSON** no Blender, em CPU: ruas e calçadas, prédios (3 estilos), veículos (sem marca), árvores, vegetação, mobiliário e comércio. Tudo é espalhado por semente e passa por QA: nada flutuando, nada atravessando, textos permitidos |
| **Placas 2.5D** | `cenografia/nucleo/compositor.py` | Cada câmera vira camadas (céu, longe, meio, perto, frente) com grupos de luz, profundidade e albedo. O compositor faz paralaxe, névoa, 5 horários e 4 climas, e põe o Heitor com teste de profundidade por pixel |
| **Núcleo de efeitos** | `efeitos/nucleo/` | Parâmetros comuns, 3 intensidades, 6 fases, partículas, curvas, corda, distorção, marcas, rastros, tremida, quadro de impacto, contatos no rig, **segurança de flashes**, **proteção de rosto e estampa** e a **mesa** (1 dominante + 1 secundário) |
| **5 poderes** | `efeitos/poderes/` | eletricidade, terra, voo, aranha, elasticidade |
| **4 extensões do personagem** (fora do rig) | `personagens/heitor/extensoes/` | X1 tom de luz · X2 voo · X3 aranha · X4 elasticidade |

## 2. Etapas e aprovações
| Etapa | Entrega | Aprovação |
|---|---|---|
| E0 | fundamentos (receita, registro, materiais, render por camadas, QA) | 25/11 |
| E1 | materiais de bairro, céu e atmosfera, tempo de render | 25/11 |
| E2 | ruas e calçadas (quarteirão modular, cruzamento) | 25/11 |
| E3 | prédios (residencial, comercial, sobrado) | 25/11 |
| E4 | veículos (5 carrocerias, ônibus, moto; sem marca nem placa real) | 25/11 |
| E5 | ambientação (árvores, vegetação, mobiliário, comércio, espalhamento) | 26/11 |
| E6 | cena de prova (rua de bairro, 3 horários, Heitor andando) | 26/11 |
| E7 | núcleo de efeitos | 26/11 |
| E8 parte 1 | eletricidade e terra | 26/11 |
| X1 | tom de luz no personagem | 26/11 |
| X2 | voo (poses, corpo inclinado, roupa e cabelo ao vento) | 26/11 |
| E8 parte 2 | poder de voo | 26/11 |
| X3 | aranha (escalada, balanço, gesto de lançar) | 26/11 |
| E8 parte 3 | poder de aranha | 26/11 |
| X4 | elasticidade (antebraço e coxa esticam) | 26/11 |
| E8 parte 4 | poder de elasticidade | 26/11 |
| **E9** | **combinações (teste de ação, 10,2 s: terra + eletricidade, elasticidade + eletricidade, voo + eletricidade) e este relatório** | **aguardando** |

Cada etapa tem o seu relatório em `cenografia/testes/` (E0–E8) e cada extensão a sua proposta em `personagens/heitor/extensoes/xN_*/`.

## 3. Os 5 poderes (resumo medido)
| Poder | Cor | Modos | Ordem das intensidades | Contatos | Flashes (máx/s) |
|---|---|---|---|---|---|
| eletricidade | ciano `#6ff4ff` | raio da mão ao alvo; arcos no corpo; queimado | ✅ | raio na mão e no alvo: 0,0 px | 1 |
| terra | terra/ocre | rachadura, pedaços do chão, pilar, cratera | ✅ | textura recortada = fundo (erro 0,0) | 1 |
| voo | branco-ar `#e9f0ff` | pairar, sair voando, decolagem vertical | ✅ | pé no tênis 100 %; rastro no pé 0 px | 1 |
| aranha | seda `#ece3c6` | lançar e grudar, balançar, escalar com rede | ✅ | fio na mão 100 %; na âncora 0 px | 1 |
| elasticidade | rosa-mola `#ff6fb5` | tocar, pegar, pernas de pau | ✅ | palma no alvo 0 px; sola no chão ≤ 1,2 px | 0 |

Todos:
- respeitam a **proteção** do rosto e da estampa (cobertura ≤ 0,35);
- têm cor bem distinta da camiseta (ΔE ≥ 60);
- são **determinísticos** (o mesmo quadro sai idêntico);
- **não mexem no rig**.

Nenhum copia gesto ou golpe de personagem de terceiros. Em especial, ficaram de fora o gesto de lançar teia conhecido e o soco esticado.

## 4. As 4 extensões do personagem
| Extensão | Como (sem alterar o rig) | Garantia medida |
|---|---|---|
| X1 tom de luz | ajusta a cor da camada do Heitor dentro do compositor, conforme a luz da cena e dos efeitos | silhueta idêntica; estampa ≥ 92 % do contraste; desligada = idêntico |
| X2 voo | poses do próprio rig + giro do desenho + camada de vento atrás | rig intacto (só o cós do jeans pode ser coberto pela barra solta); 484 poses sem violação |
| X3 aranha | IK do próprio rig com apoios presos na parede; pêndulo em torno da mão | deslize ≤ 0,003 px; contatos 100 % |
| X4 elasticidade | escorço do próprio rig > 1 só no antebraço e na coxa; a mão é sempre a do rig | mão IoU 1,0; volta exata (idêntico byte a byte) |

## 5. Guia rápido para a produção
- **Cenário:** receita JSON → `cenografia/construir.py` (com cache) → `Placa`. No render da placa, conte ~3–9 min por câmera em CPU (medido por etapa).
- **Compor um quadro:**
  ```
  Placa.compor(pesos, nevoa, grade, cam, personagem, profundidade_personagem, efeitos=mesa, deslocamento_px=mesa.tremida(), tom_personagem=X1.fazer_tom(...))
  ```
  Conte 2–6 s por quadro 1080×1920 em CPU com efeitos.
- **Heitor:**
  - `heitor_v2.desenhar` (andar, gestos);
  - `voo.desenhar` (X2);
  - `aranha.Escalada/Balanco` (X3);
  - `elasticidade.desenhar` (X4).
- **Poderes:** `REGISTRO["nome"](Params(intensidade=...), **kw)` numa `Mesa`. No voo, na aranha e na elasticidade, o poder também move o Heitor (`estado`/`desenhar_heitor`).
- **Sempre na saída:** marca d'água "MODO CURIOSO"; verificar flashes (`seguranca.analisar_flashes`).

## 6. Achados em aberto (dependem do diretor; não corrigidos)
1. **Borda do Heitor no compositor:** a camada não pré-multiplicada é somada como pré-multiplicada; a borda fica 1 px mais clara. **O diretor decidiu NÃO corrigir.**
2. **Núcleo de efeitos (E7/E8-1) lê o skia não pré-multiplicado:** os brilhos ficam ~5,6× mais fortes que o código diz. O visual aprovado da eletricidade depende disso; corrigir pede novo ajuste e nova aprovação. Os poderes de voo, aranha e elasticidade já leem do jeito certo. **Sem decisão.**
3. **Auxiliar `altura_pelve` da X2** induz pés afundados ao agachar, se usado como "pelve". Os poderes usam a referência certa; proposta de corrigir o texto e o auxiliar da X2. **Sem decisão.**

## 7. Limitações gerais (registradas, não escondidas)
- **Efeitos 2D/2.5D** sobre placas: sem sombra de efeito no cenário, sem física de corda e sem deformação real do cenário (marcas são decalques).
- **A câmera se move sobre a placa** (paralaxe 2.5D), não dentro da cena 3D: grandes mudanças de ângulo pedem outra placa.
- **O personagem é 2D** com proporção de cartum (cabeça grande): limita poses (por exemplo, a mão no balanço fica atrás da cabeça, de perfil).
- **Tudo em CPU.** Um minuto de vídeo leva horas de composição.

## 8. O que falta para produzir (decisões do diretor, de antes desta fase)
- aprovar a arquitetura;
- plano e chave da ElevenLabs (voz);
- biblioteca de música e SFX;
- liberação de hosts na rede;
- avaliação do piloto técnico 01, feito com o rig v1.

**Nenhum episódio, piloto ou produção em escala começa sem a autorização explícita do diretor.**
