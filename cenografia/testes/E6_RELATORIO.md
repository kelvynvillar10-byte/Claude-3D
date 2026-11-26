# Relatório da etapa E6 — cena de prova

26/11/2026 · Autorizada pelo diretor junto com a aprovação da E5 ("Autorizado e aprovado"). **E6 APROVADA pelo diretor em 26/11/2026; E7 autorizada.** **É um vídeo de TESTE, não uma história:** não há roteiro, falas, narração nem episódio. O Heitor rig v2 não foi alterado.

Escopo do plano aprovado: "rua de bairro montada por receita, em 3 horários, com o Heitor v2 andando e câmera em paralaxe. É um vídeo de teste, não história."

## O vídeo: `testes/e6/E6_cena_prova.mp4`
17 s · 1080×1920 · 30 q/s · 510 quadros · marca d'água "MODO CURIOSO" (ID-004) · sem áudio.

| Tomada | Horário | O que mostra | Câmera (2.5D sobre a placa) |
|---|---|---|---|
| 1 · `manha_frente` | manhã | O Heitor vem pela calçada **em direção à câmera**: passa sob o ipê rosa, ao lado do hidrante e da placa "30" | **recua** 0,7 m (paralaxe de profundidade) |
| 2 · `tarde_perfil` | tarde dourada | Ele atravessa o quadro **de perfil** na frente da loja HORTIFRUTI (toldo, prateleiras); o poste passa na frente dele | **acompanha** de lado, 0,8 m (paralaxe lateral) |
| 3 · `noite_costas` | noite | Ele se afasta **de costas**, sob os postes acesos, com as vitrines e os faróis do trânsito ao fundo | **avança** 0,6 m |

Entre as tomadas há fusão de 0,5 s. A legenda de teste diz "cena de prova (teste, não é história)". Folha de quadros: `E6_quadros.jpg`, com 4 quadros por tomada.

**Tudo é receita:**
- `receitas/e6_rua.json`: o cenário, que é o quarteirão da E5 com um **corredor livre** na calçada;
- `receitas/e6_cena_prova.json`: as tomadas, com horário, câmera, caminho, vista do personagem e movimento de câmera.

Trocar uma tomada é trocar o JSON.

## Como o Heitor anda (sem alterar o rig)
- **Pose:** vem do **ciclo de caminhada do próprio rig v2** (`animacao.pose_locomocao`), nas vistas frente, perfil e costas. É o mesmo ciclo aprovado na F2: pé de apoio plantado, braço oposto à perna, piscada.
- **Velocidade no mundo:** é **a do ciclo**, 1,8 H/s com H = altura da cabeça = 0,35 m, ou seja **0,63 m/s**. Andar mais rápido faria o pé deslizar.
- **Posição e tamanho:** em cada quadro, a posição do Heitor no mundo é projetada com a **mesma geometria da câmera do Blender** (intrínsecos da placa). O movimento de câmera 2.5D é aplicado também a ele.
- **Oclusão:** teste de profundidade por pixel. O que está mais perto da câmera passa na frente dele (o poste na tomada de perfil).

## Medidas
### Render das placas (4 núcleos, sem GPU, 1080×1920)
| Placa | Montagem | Total | Camada "meio" |
|---|---|---|---|
| manhã (câmera da calçada) | 40 s | 225,6 s | 101,5 s |
| tarde (câmera do outro lado da rua) | 42 s | 248,2 s | 142,5 s |
| noite (câmera da calçada) | 49 s | 254,2 s | 112,0 s |

**As 3 ficaram dentro da meta de 3–5 min.** Cada placa é renderizada uma vez só e serve a todos os quadros da tomada.

### Composição do vídeo
- **2,0 s por quadro em média** (máximo de 4,7 s, nas fusões, que compõem dois quadros).
- Os 510 quadros levaram ~17 min. Somando as 3 placas (~12 min), **o vídeo de 17 s levou ~29 min em CPU**.

### Qualidade
| Teste | Resultado |
|---|---|
| **Caminho livre** (no Blender: 114 raios por tomada, no centro e a ±25 cm do caminho) | **Nenhum obstáculo** entre 20 cm e 1,5 m nas 3 tomadas |
| **Deslize do pé de apoio** (perfil; pé desenhado × ponto parado no mundo, mesmo movimento de câmera) | 14 apoios medidos: **máximo de 0,09 px**, média de 0,08 px. O pé não desliza |
| **Continuidade** (diferença média entre quadros consecutivos, fora das fusões) | média de 3,3/255, máxima de 4,6/255: **sem saltos** |
| Altura do Heitor na tela (placa) | frente: 371 → 549 px (aproxima); perfil: 586 px (constante, mesma distância); costas: 800 → 470 px (afasta) |
| Oclusão | Na tomada de perfil, o poste cobre o Heitor em 6 quadros; nas outras, ele não fica atrás de nada |
| **Paleta do Heitor no quadro** (um quadro por tomada, pixels não cobertos) | **100 % idênticos** ao rig sozinho nas 3 tomadas (38.709 / 56.510 / 82.959 pixels) |
| Mesmo quadro renderizado duas vezes | **Idêntico** |
| Nada flutuando / nada atravessando no cenário | 0 / 0 nas 3 placas |
| Assinatura de `personagens/heitor/rig_v2/`, `docs/IDENTIDADE_OFICIAL.md`, `skills/` | **Idêntica** (`068bf373…8342`); nenhuma alteração pendente |
| Verificação F1 do rig | 6/6 vistas OK |
| ID-001 a ID-004 | Inalteradas. Estampa "Modo Curioso" na camiseta (vem do rig); marca d'água "MODO CURIOSO" |

### Cor (quadro a 40 % de cada tomada; alvos do skill para planos diurnos: brilho 46–56 %, saturação 35–46 %, vinheta 57–66 %)
| Tomada | Brilho | Saturação | Vinheta | Sombras (a, b) |
|---|---|---|---|---|
| manhã | 50,5 ✅ | 38,8 ✅ | 79,1 ⚠️ | +7, −19 ✅ |
| tarde | 42,9 ⚠️ | 48,2 ⚠️ (acima) | 48,0 ⚠️ | +6, −11 ✅ |
| noite | 30,1 | 48,0 | 83,2 | +14, −20 ✅ |

A tomada da manhã fica dentro do alvo de brilho e saturação. Na tarde, a vitrine iluminada e o toldo saturam o quadro, e a fachada próxima deixa as bordas claras. A gradação foi a mesma das etapas anteriores, sem ajuste por tomada: **isso é trabalho de correção de cor por plano, que fica para a produção.**

## Problemas encontrados e corrigidos
1. **Medição errada do pé na 1ª versão** (28–42 px de "deriva"). A medida incluía o movimento da câmera, que move legitimamente na tela até um ponto parado. Refeita contra um ponto parado no mundo: 0,09 px.
2. **Vídeo de 20,7 MB** por causa do grão de filme. Recomprimido para 4,3 MB, com diferença imperceptível (PSNR médio de 38,7 dB contra o original).

## Limitações (registradas, não escondidas)
1. **O Heitor não recebe a luz do cenário.** À noite ele fica mais aceso que a rua, e de dia não passa pela sombra das árvores. É a limitação mais visível do vídeo. Corrigir exige uma extensão de iluminação do personagem, que **só faço com aprovação específica**, apresentada à parte com demonstração.
2. **Caminhada de frente e de costas é projeção do ciclo de perfil** (limitação já registrada na F2): mais contida e com profundidade aproximada. **Não há caminhada em 3/4**, por isso não há tomadas em diagonal.
3. **Velocidade fixa em 0,63 m/s** (passeio lento). Para andar mais rápido sem o pé deslizar, seria preciso outro ciclo no rig, o que é uma extensão.
4. **A câmera 2.5D tem limite:** o movimento cabe na margem da placa (25 %). Um travelling longo, acompanhando o personagem por vários metros, exige outra placa ou uma placa mais larga.
5. **Mundo parado:** carros parados, nada se move além do céu (nuvens e lua). Árvores sem vento.
6. **Sem áudio.** Música, efeitos e voz dependem das pendências do diretor (biblioteca de música e SFX, voz).
7. **Correção de cor por tomada não foi feita** (ver "Cor").

## Como reproduzir
```
.venv/bin/python cenografia/testes/e6_cena_prova.py    # 3 placas (~4 min cada na 1ª vez), caminho, pé, integridade e vídeo (~17 min)
```

## Próxima etapa (só com aprovação): E7 — núcleo de efeitos
Pelo plano aprovado: partículas, curvas, luz 2D, distorção, fases (início, ativação, uso, impacto, dissipação, encerramento) e registro de plugins. É a base dos poderes (E8: eletricidade e terra primeiro).
