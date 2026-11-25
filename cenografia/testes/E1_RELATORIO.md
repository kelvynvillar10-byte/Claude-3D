# Relatório da etapa E1 — materiais, céu e atmosfera, tempo de render

25/11/2026 · Autorizada pelo diretor após a aprovação da E0. **E1 APROVADA pelo diretor em 25/11/2026; E2 autorizada.** Nenhum episódio ou história foi produzido. O Heitor rig v2 não foi alterado.

Cena de teste: `receitas/e1_calcada.json`, a mesma calçada da E0, agora com os materiais de bairro brasileiro. Os volumes (prédios, poste, banco, vaso) **continuam provisórios**; os kits detalhados são das etapas E2–E5.

## O que foi construído
| Item | Onde | Resumo |
|---|---|---|
| Otimização do render | `construir.py` (`amostras_por_camada`) | Amostras por camada: céu 4 · longe 16 · meio 24 · perto 24 · frente 16 |
| Materiais de bairro brasileiro (16 na folha) | `nucleo/materiais.py` | Calçada portuguesa (pedras individuais com rejunte, em ondas), ladrilho hidráulico, pastilha, azulejo, telha cerâmica, concreto aparente (fôrma de tábua), metal com ferrugem, madeira (natural ou pintada descascando), grama; `PALETA_BAIRRO` mais saturada; **umidade** (piso molhado com poças) |
| Mapeamento parede/piso | `materiais._NT.planar` | Os padrões (tijolo, ladrilho, tábuas) agora funcionam em paredes. Antes viravam listras verticais |
| Horários | `nucleo/luz.py` | manhã, meio-dia, tarde dourada, crepúsculo (sol 1,5° acima do horizonte, céu rosado), noite (céu em degradê + lua como luz fria) |
| Céu 2D | `nucleo/ceu2d.py` | Nuvens estilizadas tipo cumulus em 3 camadas com deriva (cobertura exata pelo percentil, volume pelo gradiente, base escura, borda clara contra o sol); lua com fase e halo; estrelas com cintilação; chuva em 3 profundidades com borrão de movimento |
| Atmosfera por clima | `nucleo/atmosfera.py` | limpo · nublado · neblina · chuva sobre qualquer horário. A névoa converge para a **cor do céu no horizonte**, então céu e cena enevoada ficam coerentes; a chuva usa a placa com piso molhado |

## Tempo real de render (4 núcleos, sem GPU) — tarefa da E0 resolvida
**Perfil da camada mais lenta ("meio")**, medido sem nenhum outro processo disputando a CPU:

| Configuração | Tempo |
|---|---|
| 64 amostras, completo (com limpeza de ruído e gravação) | 165,0 s |
| 64 amostras, só o render | 154,5 s |
| 16 amostras, só o render | 39,1 s |
| 1 amostra (preparo da cena) | 3,1 s |

→ O tempo é **proporcional às amostras**. A limpeza de ruído e a gravação custam ~10 s. **A hipótese registrada na E0 estava errada**, e a medição de 32 amostras da E0 foi feita com a CPU disputada; as duas coisas foram corrigidas no relatório da E0.

**Qualidade × amostras** (placa inteira, comparada com 64 amostras em tudo):

| Amostras por camada (céu/longe/meio/perto/frente) | Tempo | × 64 amostras |
|---|---|---|
| 64 em todas (código novo) | 408,6 s | **idêntico** à placa da E0 (PSNR 138 dB): o código novo não mudou a placa |
| **4 / 16 / 24 / 24 / 16 (escolhida)** | **141 s** | PSNR **44,9 dB**, erro médio 1,3/255; a olho, igual (só um leve alisamento da textura fina do concreto) |
| 4 / 12 / 16 / 16 / 12 | 110 s | PSNR 43,8 dB |

**Cena da E1 (materiais mais pesados): 10 placas** (5 horários × piso seco e molhado): **média de 164 s (2,7 min), máximo de 170 s. As 10 ficaram dentro da meta de 3–5 min.** Antes eram ~400 s, ou seja, ficou **~2,5 vezes mais rápido**.

## Folha de materiais (`testes/e1/E1_folha_materiais.png`, render de 118 s)
16 painéis de 0,9 m em escala real, com luz rasante da tarde. Medidas por amostra em `e1_materiais.json`:
- **Paleta de fachada saturada:** reboco ocre 65 %, verde-água 61 %, pastilha 49 %, telha 51 %, metal 58 %.
- **Textura com relevo e variação:** calçada portuguesa (variação de luminância 15,8 %), ladrilho (14,7 %), tijolo (11,1 %), pastilha (5,6 %).
- **Lisos de propósito** (variação de 1–1,5 %): rebocos, azulejo, concreto aparente.

## Céu e atmosfera: grade 5 horários × 4 climas (`testes/e1/E1_grade_horarios_climas.png`)
Medidas de cada célula, com as mesmas fórmulas da auditoria das referências:

| | limpo (brilho · saturação) | nublado | neblina | chuva |
|---|---|---|---|---|
| manhã | 52,4 % · 33,8 % | 51,7 · 24,5 | 62,5 · 12,2 | 52,6 · 19,8 |
| meio-dia | 54,1 · **36,6** | 52,6 · 28,0 | 61,2 · 13,4 | 51,3 · 25,6 |
| tarde dourada | 53,8 · 29,9 | 53,0 · 16,6 | 63,8 · 15,8 | 52,7 · 14,6 |
| crepúsculo | 37,4 · 43,3 | 38,3 · 28,3 | 47,1 · 19,8 | 38,3 · 23,6 |
| noite | 28,3 · 50,9 | 27,1 · 46,8 | 25,7 · 47,5 | 24,2 · 45,8 |

Leitura contra os alvos do skill (brilho 46–56 %, saturação 35–46 %; alvos medidos em planos diurnos das referências):
- **Dia limpo:** brilho 52–54 % ✅ em manhã, meio-dia e tarde. Saturação: meio-dia ✅ 36,6 %; manhã 33,8 % e tarde 29,9 % ficam um pouco abaixo. A saturação melhorou em relação à E0 (30,7 %).
- **Nublado, neblina e chuva:** dessaturam e clareiam de propósito (céu leitoso, cor apagada). Não são comparáveis ao alvo diurno.
- **Crepúsculo e noite:** fora do alvo diurno por natureza. A noite segue a regra do skill, "noite azul-roxa com uma fonte laranja": céu azul, postes quentes. Sombras roxo-azuladas (a ≈ +7…+13, b ≈ −15…−17) em quase todas as células ✅.
- **Vinheta:** 43–56 % de dia; o alvo é 57–66 %, então os cantos estão mais escuros que nas referências. Ver limitações.

## Vídeo de atmosfera (`testes/e1/E1_atmosfera.mp4`, 16 s)
Sequência: manhã → meio-dia → tarde → tarde nublada → tarde com chuva → crepúsculo → noite → noite com neblina, com fusões de 0,5 s, nuvens derivando, chuva caindo, lua e o Heitor rig v2 parado (respiração e piscada).
- **Continuidade do céu:** diferença média entre quadros de 2,2/255 e máxima de 2,7/255 fora das fusões. Não há saltos.
- **Composição:** 2,29 s por quadro em média, 5,2 s no máximo (nas fusões, que compõem dois planos).

## Determinismo e integridade
| Teste | Resultado |
|---|---|
| Mesmo clima e mesma semente, duas vezes | **Quadro idêntico** (mesmo sha256) |
| Outra semente | Quadro diferente (nuvens em outro lugar) |
| Assinatura de `personagens/heitor/rig_v2/`, `docs/IDENTIDADE_OFICIAL.md`, `skills/` | **Idêntica** à de antes da E0 (`068bf373…8342`); nenhuma alteração pendente |
| Verificação da F1 do rig | 6/6 vistas OK |
| Paleta do Heitor no quadro | 191.462 pixels, **100 % idênticos** ao rig sozinho |
| ID-001 a ID-004 | Inalteradas. Marca d'água "MODO CURIOSO" nos vídeos; estampa "Modo Curioso" vem do rig |

## Problemas encontrados e corrigidos
1. **A hipótese de tempo da E0 estava errada** (o custo vem das amostras, não da limpeza de ruído); a medição de 32 amostras foi feita com a CPU disputada. Relatório da E0 corrigido.
2. **Padrões de tijolo, ladrilho e tábua viravam listras em paredes.** Os nós do Blender só usam o plano XY. Criado o mapeamento parede/piso. Isso também afetava o tijolo e as manchas do reboco na E0.
3. **As manchas de chuva do reboco pareciam chapa ondulada** (listras finas e densas). Ficaram mais largas e esparsas.
4. **Ladrilho sem o círculo central:** a profundidade entrava na distância ao centro. Corrigido.
5. **Asfalto sem textura visível** (variação de 0,4 %). Ganhou agregado médio e mais contraste (variação de 1,0 %).
6. **Painéis da folha de materiais giravam em torno da origem do mundo** e metade sumia atrás do fundo. Corrigido.
7. **Nuvens invisíveis** (limiar fixo). Agora o limiar sai do percentil, e a cobertura é exatamente a pedida.
8. **Nuvens abaixo do horizonte** (termo de compensação por camada) **e esticadas na vertical** (o "achatamento" fazia o contrário). Corrigido.
9. **Nuvens sem contraste:** o céu fica perto do teto do mapeamento de tons. Criados o ganho do céu (−0,9 stop só no céu visto) e um sombreamento mais forte.
10. **Neblina invertida:** o céu ficava mais escuro que os prédios enevoados. A névoa agora converge para a cor do horizonte, aplicada à cena e ao céu.
11. **O dia ficou lavado** com a névoa do item 10 (brilho de 61–65 %): o horizonte de dia é muito claro. A névoa manteve a cor do horizonte e ganhou um teto de brilho. Resultado: 52–54 %.
12. **A chave do cache incluía o código do compositor.** Cada ajuste de nuvem ou névoa forçava renderizar as placas de novo. Agora a chave só considera o código que roda no Blender.
13. **Noite dourada demais:** calçada saturada sob os postes. Exposição e cor das lâmpadas ajustadas (lâmpada mais branca, peso menor).

## Limitações (registradas, não escondidas)
1. **Nuvens estilizadas, mas ainda simples.** Leem como cumulus e céu encoberto, mas não têm o acabamento de pintura de cenário de cinema. Nesta composição de rua estreita aparece pouco céu. **A aprovação estética do céu é sua**; posso refinar (mais camadas de detalhe, formatos por tipo de nuvem) a partir do seu retorno.
2. **O Heitor não recebe a luz do cenário.** No crepúsculo, na noite e na chuva, isso fica mais visível que na E0. Corrigir exige uma extensão de iluminação do personagem, que só faço com aprovação específica e apresentada à parte.
3. **Chuva só com riscos.** Não há respingos no chão, ondas nas poças nem molhado no personagem. O reflexo das poças é o do render (fixo na placa).
4. **Piso molhado exige outra placa** por horário: mais ~2,8 min de render cada.
5. **Saturação da tarde (29,9 %) e da manhã (33,8 %)** um pouco abaixo do alvo; **vinheta** abaixo do alvo de dia (cantos mais escuros). Nesta cena, o poste escuro em primeiro plano e a fachada da esquerda pesam nos cantos. Afinar por cena.
6. **Composição mais lenta com o céu animado:** 2,3 s/quadro. Um vídeo de 90 s levaria ~1,7 h de composição em CPU. A otimizar: nuvens em resolução menor, cache entre quadros.
7. **Estrelas muito discretas** em 1080×1920. A lua aparece bem.
8. **Calçada portuguesa:** a onda de 1,6 m é marcante e domina o chão nesta cena. A escala é parâmetro e pode ser ajustada por cena.
9. **O teto de brilho da névoa (0,75) e o ganho do céu (0,55) foram ajustados nesta cena** e precisam ser conferidos em outras composições (E2+).

## Como reproduzir
```
.venv/bin/python cenografia/testes/e1_materiais.py      # folha de materiais (~2 min)
.venv/bin/python cenografia/testes/e1_testes.py         # placas (10 × ~2,7 min na 1ª vez), grade, vídeo, determinismo, integridade
```

## Próxima etapa (só com aprovação): E2 — ruas e calçadas
Quarteirão modular: asfalto com remendos e faixas, meio-fio e sarjeta, bueiros, calçadas, postes e placas (só textos inventados ou "MODO CURIOSO").
