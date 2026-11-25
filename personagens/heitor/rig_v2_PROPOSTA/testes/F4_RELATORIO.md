# Relatório da fase F4 — Heitor rig v2 (PROPOSTA)

25/11/2026 · Expressões animadas (T7), teste em cena (T8) e relatório final (`RELATORIO_FINAL.md`, na pasta do rig).
**Nada aqui está aprovado automaticamente.** F1, F2 e F3 foram aprovadas pelo diretor; a F4 e o rig v2 como um todo aguardam avaliação.

## O que foi construído
| Componente | Arquivo | Função |
|---|---|---|
| Transição de expressões | `codigo/gestos.py` (`mistura_expr`) | Os parâmetros contínuos interpolam. **A troca de desenho de boca** acontece no meio da transição, com a boca quase fechada. **A troca de estilo de olho** (pequeno e escuro ↔ arregalado e branco) fica **escondida por uma piscada** |
| Pálpebra no olho arregalado | `codigo/heitor_v2.py` (`_olho`) | O olho branco agora pisca; antes não piscava. Sem piscada, o desenho é idêntico ao anterior: as folhas da F1 saíram iguais byte a byte |
| Fala de teste e sincronia labial | `codigo/fala.py` | Voz **temporária** espeak-ng, a mesma do piloto 01. Como o espeak-ng não informa tempos, cada palavra é sintetizada sozinha e o tempo de cada palavra fica **exato**. A abertura da boca segue a energia do áudio; o formato segue as vogais (a → aberta, e/i → larga, o/u → "o"); m/b/p fecham a boca |
| Cenário 3D do T8 | `codigo/cena_t8_blender.py` → `recursos/cena_t8/` | Canto de quarto low-poly no Blender (Cycles **CPU**): piso de tábuas, parede, janela com luz quente, estante, mesa e o pôster **"MODO CURIOSO"** (textura do piloto 01, ID-004). Gera `fundo.png` (1080×1920) e `ancoras.json` (projeção 3D → 2D: escala, chão, tampo da mesa, área do pôster) |
| Teste em cena | `codigo/testes_f4.py` (`t8`) | Heitor 2D sobre o fundo 3D, posicionado e escalado pelas âncoras. Inclui marca d'água oficial e sombras de contato |
| Pegar com o cotovelo certo | `gestos.ik_braco(..., cotovelo=None)` | Escolhe sozinho a solução anatômica (cotovelo para fora, nunca invertido) |
| Mostrar objeto | `heitor_v2.desenhar_mao` | Com a palma para a câmera, o objeto fica **na frente** da mão, mostrando o que segura |

## Testes executados (vídeo renderizado e medição)
Vídeos em 1080×1920, 30 qps, H.264. Todos juntos: `F4_todos_os_testes.mp4` (20,6 s, com áudio). Métricas: `f4_metricas.json`.

### T7 · expressões animadas e fala — `T7_expressoes_fala.mp4` (12 s, com áudio)
**Frente** (grande), **3/4** e **perfil** (embaixo) animados ao mesmo tempo, com a mesma expressão:
- Sequência: neutro (olhando para os lados) → **surpresa** → **medo** (com tremor) → **preocupação** → **alegria** → fala "Calma... acho que vai dar tudo certo!" → neutro.

| Medição | Resultado |
|---|---|
| Trocas de estilo de olho (neutro → surpresa e medo → preocupação) | **2 de 2 escondidas por piscada** (olho fechado no quadro da troca) |
| Trocas de desenho de boca fora da fala | 5. Abertura no quadro da troca: 0,09–0,23 em 4 delas; **0,37 em "o" → "aberta"** (surpresa → medo: as duas bocas são abertas, então a troca aparece mais) |
| Maior salto por quadro (fora das piscadas) | pálpebra 0,045 · pupila 0,041 · pálpebra inferior 0,118 · **sorriso 0,354** (a entrada da alegria usa a curva `volta`, rápida e com overshoot — escolha de atuação) |
| Piscadas automáticas | 4, de 2 a 4 quadros. A de 2 quadros cai junto de uma transição |
| **Sincronia labial** (abertura da boca × energia do áudio) | **Atraso 0 quadros**; correlação **0,92** |
| Boca nas pausas da fala | **Pausas longas (2): boca 100 % fechada**. Em todos os quadros de silêncio, inclusive os intervalos curtos entre palavras: 79 % fechada. Nos intervalos de ~0,07 s a boca não fecha toda, como na fala natural |
| Áudio | −20,2 LUFS integrado, pico −2,0 dBFS (fala curta dentro de 12 s com muito silêncio; um teste, não uma mixagem final) |
| Cotovelos invertidos | 0 |

Verificação visual: as expressões leem nas 3 vistas e o rosto não "pula" nas trocas. Fiz um ajuste: a piscada que esconde a troca de olho não chegava a fechar quando a transição era rápida (0,22 s), e a troca aparecia; agora o olho fica fechado na faixa central da transição.

### T8 · teste em cena — `T8_em_cena.mp4` (8,6 s)
Entra andando de perfil pela esquerda, **para** (o pé de trás assenta ao lado do da frente, com IK), olha a bola com cara de curioso, **pega a bola na mesa**, ergue até o peito, **vira para a câmera** (perfil → 3/4 → frente), **mostra a bola no alto** com surpresa e alegria, abaixa e **acena** com a outra mão.

| Medição | Resultado |
|---|---|
| Fundo 3D | Cycles **CPU**, 64 amostras com denoise, 1080×1920: **75 s** (uma vez; depois é imagem estática) |
| Escala do personagem pela projeção 3D → 2D | 1,40 m a 3,9 m da câmera = **1.005 px**; tampo da mesa a 0,68 m = 1,94 H, coerente com o modelo |
| Pé de apoio na caminhada e na parada | **Deslize 0,0 H** |
| Bola | Pega aos 3,10 s; **165 quadros presa à mão (distância 0,0)**; erro de alcance ≤ 0,0034 H (~1 px) |
| Virada (perfil → 3/4 → frente) | A bola segue um alvo contínuo; maior passo 0,127 H por quadro (~32 px) |
| **Marca no cenário (pôster, ID-004)** | **Nenhum pixel do pôster coberto em nenhum dos 258 quadros** (comparado com o quadro sem o personagem) |
| OCR (quadro de frente) | "MODO CURIOSO" (marca d'água), "MODO" e "CURIOSO" (pôster), **"Modo Curioso"** (camiseta) |
| Cotovelos invertidos | 0 |

**Problemas encontrados pelos testes e corrigidos:**
1. **O pôster ficava atrás da cabeça**, com a marca parcialmente coberta (violação da ID-004). Subi o pôster na parede e criei a medição de oclusão quadro a quadro.
2. **A medição de oclusão dava 4,6 % em todos os quadros**, inclusive sem ninguém na frente. Era a compressão H.264 nas bordas do texto. Agora a referência é o quadro sem o personagem, decodificado do mesmo vídeo: 0,0 %.
3. **Cantos pretos na moldura da janela:** volumes sobrepostos no Blender. Peças refeitas sem sobreposição.
4. **De frente, a bola sumia dentro da mão fechada.** Agora, com a palma para a câmera, a bola é desenhada na frente da mão.
5. **O braço com a bola ficava "em asa"** (cotovelo na altura do ombro). Alvos refeitos para o braço descer ao lado do corpo.
6. **A IK escolhia às vezes o cotovelo errado** ao erguer o braço. Agora escolhe sozinha a solução anatômica.
7. **A regra do cotovelo deixava passar um caso:** com o braço cruzando por cima da cabeça, ela não acusava a inversão. A regra passou a usar a geometria real do esqueleto e acusa esse caso. Ela continua reprovando todos os casos antigos e aprovando as poses corretas, inclusive a pose de "não sei" (antebraços para fora), que é válida. Auditoria: 0 invertidos em F1–F4.

## Efeito nas fases aprovadas (re-medido)
- **F1:** as 4 folhas saíram idênticas byte a byte. Verificação: 6/6 OK.
- **F2:** os 5 vídeos saíram idênticos byte a byte.
- **F3:** as métricas são idênticas. Os vídeos T5, T6 e T6b mudaram **só nas transições de rosto**, que agora são suaves: as trocas de boca e de olho deixaram de "pular".

## Limitações da F4
1. **A voz é temporária** (espeak-ng, robótica) e foi **sintetizada palavra por palavra**, então a fala sai um pouco pausada. Com a voz oficial (ID-001, pendente), os tempos por palavra virão do próprio serviço de voz, como prevê a arquitetura.
2. **O formato da boca por sílaba é aproximado:** o tempo de cada palavra é exato, mas o de cada sílaba é estimado por divisão igual. A abertura segue o áudio de verdade (atraso 0).
3. **A virada é discreta** (perfil → 3/4 → frente, ~4 quadros cada), como no 2D tradicional. A bola acompanha sem saltos grandes, mas não existe rotação contínua do corpo.
4. **Personagem e objeto 2D sobre fundo 3D:**
   - A luz do cenário não muda as cores do Heitor; a sombra de contato no chão é desenhada.
   - O personagem fica num plano fixo de profundidade (3,9 m) e não passa por trás de objetos do cenário. Isso exigiria camadas de primeiro plano, como fizemos no piloto 01.
5. **Câmera fixa no T8.** Movimento de câmera sobre fundo estático é possível com o fundo maior (como no piloto), mas não foi testado aqui.
6. **Blender CPU:** cada fundo leva ~75 s em 1080×1920 com 64 amostras. Isso é aceitável para fundos **estáticos** (renderizados uma vez por plano), mas **inviável para animar a cena 3D quadro a quadro** (~75 s × 30 qps ≈ 37 min por segundo de vídeo). Soluções compatíveis com o ambiente atual:
   - manter o plano da arquitetura: fundo estático + personagem 2D (como aqui);
   - render em resolução menor com upscale;
   - movimentos de câmera 2.5D (fundo em camadas com paralaxe);
   - renderizar só os quadros-chave de câmera e interpolar no compositor.
7. **Naturalidade e atuação** (o tempo das reações, se a fala "parece o Heitor") são avaliação visual e cabem ao diretor.
