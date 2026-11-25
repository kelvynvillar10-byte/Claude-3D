# Pipeline de Produção — Modo Curioso Studio AI

Versão 1.0 · Etapa 1 (auditoria). Esta é a proposta técnica. **Nenhum vídeo foi gerado ainda.**

Documentos relacionados: `AUDITORIA_REFERENCIAS.md` (inventário e medições), `MANUAL_DIRECAO_ARTE.md`, `MANUAL_ANIMACAO.md`, `PADRAO_EDICAO.md`.

---

## 1. Visão geral

```
PAUTA → ROTEIRO → VOZ → DECUPAGEM → ASSETS → ANIMAÇÃO → RENDER → MONTAGEM → ÁUDIO → QA → EXPORT
  │        │        │        │          │          │          │          │         │       │
  G0       G1       G2       G3         G4         G5         —          G6        G7      G8
```

Cada etapa entrega um arquivo versionado e passa por um portão de aprovação (G0–G8). Nenhuma etapa começa sem o portão anterior aprovado. Os portões G1, G3 e G8 precisam de aprovação humana. Os outros podem ser checados por script (seção 12).

| Etapa | Entrada | Saída (arquivo) | Portão |
|---|---|---|---|
| 0. Pauta | ideia "E se…?" | `pauta.md` (poder + 6–10 fatos científicos com fonte) | G0: todo número tem fonte |
| 1. Roteiro | pauta | `roteiro.md` com tempo-alvo por frase | G1: estrutura da seção 3 + aprovação humana |
| 2. Voz | roteiro | `voz.wav` + `voz_palavras.json` (tempo de cada palavra) | G2: ritmo e duração |
| 3. Decupagem | roteiro + voz | `decupagem.json` (lista de planos) | G3: aprovação humana |
| 4. Assets | decupagem | personagens, cenários, inserts | G4: confere com o Manual de Direção de Arte |
| 5. Animação | assets + decupagem | camadas por plano | G5: confere com o Manual de Animação |
| 6. Render | camadas | `planos/*.mov` ou sequência PNG | — |
| 7. Montagem | planos + voz | `montagem.json` → `video_sem_mix.mp4` | G6: confere com o Padrão de Edição |
| 8. Áudio | voz + SFX + música | `mix.wav` | G7: −14 LUFS, pico ≤ −1 dBTP |
| 9. QA | vídeo final | `qa_relatorio.json` | G8: checklist + aprovação humana |
| 10. Export | aprovado | `MC_<serie>_<ep>_v<n>.mp4` | — |

---

## 2. Etapa 0: pauta

- Formato: "E se tu acordasse amanhã e ___?" (parte 1) ou continuação de série com personagem nomeado.
- Liste de 6 a 10 conceitos científicos, cada um com **um número real e a fonte**. Exemplos medidos nas referências: densidade 0,92 (borracha boia, v15), 343 m/s (som no ar, v12), 4.000 bar (jato d'água, v10), ×20.000 (intensificador de luz, v18/v20), 59 % de água no corpo (v17), 0,14 s (duração de um soco, v14), 1.400 km/h (bala, v19).
- Contraste "no filme × na vida real" sempre que der.
- Verifique as regras fixas do canal (seção 0 do Manual de Direção de Arte): nada de personagem, logo ou marca de terceiros. As referências citam JoJo (v01, v19), One Piece/Luffy (v15), o filme Lucy e o jogo Clash (v14), e caricaturas de pessoa real (cientista estilo Einstein em v14). Nós não fazemos isso.

## 3. Etapa 1: roteiro

Modelo de 91 s (mediana das referências). Episódios de série podem ir a 117–141 s (v10, v16–v20).

| Tempo | Bloco | Regra |
|---|---|---|
| 0–1 s | Gancho | "E se tu acordasse amanhã e…?!" ou ação em andamento com nome ("O Will tava…", "O Caio…") ou "Tu é o ___ e tem o elemento ___". Quebrado em 3–5 legendas. |
| 1–10 s | Situação | Personagem nomeado + 2ª pessoa ("tu", "tua mão"). Primeiro gag. |
| a cada 8–12 s | Conceito | Um número real na tela por conceito (≥ 6 por vídeo). |
| a cada 10–15 s | Gag físico | Exemplos vistos: braço elástico desliga o despertador (v15), frigideira gruda na mão (v07), olhos boiando do invisível (v20). |
| ~50 % | Rival | Antagonista entra (brutamontes da academia v07, rival do futebol v15, caçador v10, Rei Mago v16/v17). |
| 70–75 % | Clímax | Maior efeito visual do vídeo. |
| últimos 5 s | Final | "Segue aí" + gancho "na parte dois" e/ou pergunta "Comenta aí…" / "Tu queria ter?" (v13). |

- Velocidade de narração: ≈195 palavras/min (dado do Padrão; nossa medição por OCR está em `AUDITORIA_REFERENCIAS.md`). Isso dá cerca de 290–300 palavras para 91 s.
- Escreva o roteiro já dividido em blocos de 2–3 palavras (é como a legenda vai aparecer).
- Falas de personagem entre aspas.

## 4. Etapa 2: voz

- Locução humana ou TTS em português do Brasil, com sotaque e gírias coerentes com o canal ("tu", "bah", "guri" aparecem nas referências).
- Pós-processamento: **só comprimir pausas** (pausa ≥ 0,8 s vira 0,42 s; pausa entre 0,18 e 0,8 s vira 0,18 s). **Nunca acelerar com rubberband/time-stretch**, porque gera eco e voz duplicada.
- Medido nas referências: nenhuma pausa ≥ 0,8 s no meio do vídeo em 12 de 13 vídeos (detector de silêncio a −35 dB).
- Saída obrigatória: alinhamento de palavras (`voz_palavras.json`, início e fim de cada palavra). Ele dirige legendas, cortes e SFX.
- **Pendência técnica:** o modelo de reconhecimento de fala (Whisper) não baixou neste ambiente porque o Hugging Face está bloqueado pela rede. Para alinhar palavras é preciso (a) liberar o host na rede do ambiente, (b) usar um TTS que já devolva os tempos das palavras, ou (c) usar outro serviço de alinhamento.

## 5. Etapa 3: decupagem (`decupagem.json`)

Um registro por plano:

```json
{
  "plano": 12,
  "inicio": 18.40, "fim": 20.05,
  "texto_voz": "a porta de aço voou",
  "cenario": "joalheria_noite",
  "enquadramento": "close",
  "personagens": [{"id": "heitor", "pose": "grito", "expressao": "bravo"}],
  "camera": {"tipo": "push-in", "zoom_total": 0.10, "curva": "ease-out"},
  "efeitos": ["onda_choque", "tremida_impacto"],
  "insert_cientifico": null,
  "rotulo_numero": {"texto": "194 dB", "cor": "amarelo"},
  "legenda_posicao": "baixo",
  "transicao_entrada": "corte",
  "sfx": ["whoosh", "impacto"]
}
```

Alvos para a lista inteira (detalhe no Padrão de Edição): plano mediano de 1,5 a 2,0 s, ≈30 cortes/min, push-in em cerca de 2 de cada 3 planos, primeiro corte entre 1 e 2 s.

## 6. Etapa 4: assets

| Biblioteca | Conteúdo | Formato proposto |
|---|---|---|
| Personagens | Heitor (elenco fixo) + coadjuvantes reutilizáveis, trocando só a roupa | Boneco 2D recortado: cada parte do corpo é uma camada com ponto de pivô (SVG/PNG em camadas). Expressões como trocas de olho, sobrancelha e boca. |
| Cenários | Quarto, cozinha, escola, rua de bairro, academia, campo, vila medieval, laboratório, base noturna | 3D low-poly com materiais simples e luz motivada, renderizado como fundo (ou pintura 2.5D com camadas para paralaxe) |
| Inserts científicos | Átomos, moléculas, neurônio, corpo holográfico, câmera térmica, visão noturna, espaço | Modelos reutilizáveis sobre fundo azul-marinho com bokeh |
| UI/tela | Celular com app, ficha "CONFIDENCIAL", notebook de loja, notícia | Templates vetoriais com a nossa marca |
| Tipografia | Legenda (condensada bold) e rótulos (arredondada) | Fontes livres: Roboto Condensed 800 e, por exemplo, Nunito/Baloo para rótulos |
| Áudio | Whoosh, impacto, pop, riser, ambiente; trilhas | Biblioteca licenciada, com a licença registrada por arquivo |

## 7. Etapa 5: animação

Ver `MANUAL_ANIMACAO.md`. Resumo: animação pose a pose com poses seguradas no nível base. Nível "ação" (antecipação → golpe → overshoot) só nos momentos de poder. O movimento de câmera é aplicado depois, na composição, como transformação 2D da imagem do plano. Por isso o plano é renderizado com margem de segurança (pelo menos 15 % maior que 1080×1920) para permitir push-in, pan e tremida sem borda.

## 8. Etapa 6: render

- Formato final: 1080×1920, 30 qps. Das 13 referências processadas, 9 estão em 60 qps (HEVC) e 4 em 30 qps (H.264). Propomos 30 qps como padrão e 60 qps como opção.
- Camadas separadas por plano: fundo, personagens, FX, rótulos. A legenda **não** entra no render do plano: ela é aplicada na montagem.
- Grão, vinheta e gradação de cor ficam num único passo de acabamento na montagem, para que todos os planos fiquem iguais.

## 9. Etapa 7: montagem

- A montagem é descrita em `montagem.json` (planos, tempos, transições, câmera, legendas) e renderizada por script (FFmpeg, ou um compositor em Python/Node). Assim a edição é reprodutível e dá para checar por script.
- Ordem das camadas: plano → câmera (push/pan/tilt/roll/tremida) → transições → acabamento de cor (sombras roxo-azuladas, vinheta, grão, bloom) → rótulos → legendas → marca d'água.

## 10. Etapa 8: áudio

- Voz é o centro. Música por baixo com ducking. SFX baixos em cada corte e em cada efeito.
- Alvos: −14 LUFS integrado; pico real ≤ −1,0 dBTP (as referências chegam a −0,8 dBTP; deixamos 0,2 dB de folga); LRA de 3 a 4 LU.
- Medido nas referências: −14,1 a −14,3 LUFS em 12 de 13 (o v16 está em −21 LUFS, fora do padrão); 1,6 a 1,8 eventos sonoros por segundo.

## 11. Etapa 10: export

- H.264 High, yuv420p, 1080×1920, 30 qps, CRF 18 (ou VBR 12–16 Mb/s), AAC 48 kHz 192 kb/s, `+faststart`.
- Nome: `MC_<serie>_<episodio>_v<versao>.mp4`. Exemplo: `MC_magnetismo_p1_v3.mp4`.

## 12. QA automático (reaproveita a análise desta auditoria)

Os scripts em `tools/analise/` mediram as referências. Rodados no nosso vídeo final, eles geram `qa_relatorio.json` e comparam com as faixas-alvo:

| Métrica | Alvo | Referências (13 MP4) |
|---|---|---|
| Duração | 85–100 s (série: até 140 s) | 81–141 s |
| Plano mediano | 1,5–2,0 s | 1,25–2,40 s (mediana 1,73) |
| Cortes/min | 27–34 | 22,5–32,7 (mediana 28,4; detector conta 5–12 % a menos) |
| % planos com movimento de câmera | ≥ 85 % | 86–100 % (mediana 96 %) |
| Vinheta (cantos/centro) | 0,50–0,66 | 0,39–0,67 (mediana 0,57) |
| Sombras Lab b | < −4 (tinta azul) | −19,4 a −1,4 (mediana −11,5); 12 de 13 abaixo de −4 |
| Loudness | −14 ± 0,5 LUFS | −13,9 a −14,3 em 12 de 13 (v16: −21,0) |
| Legendas | 2–3 palavras/bloco, centro entre 15 % e 80 % da altura, ~40 % com destaque amarelo | 64 blocos/min; 84 % entre 60 % e 80 % da altura; amarelo em 43 % (0–61 %) |

O que o script não mede (aprovação humana no G8): leitura da história, humor, precisão científica, direitos autorais, expressão dos personagens.

## 13. Estrutura de pastas proposta

```
Claude-3D/
  docs/                      manuais e auditoria
  tools/analise/             scripts de medição e QA
  referencias/               MP4 e miniaturas de referência (mover para Git LFS)
  assets/
    personagens/<id>/        partes, expressões, folha de modelo
    cenarios/<id>/
    inserts/
    ui/  fontes/  audio/sfx/  audio/musica/
  producoes/<serie>_<ep>/
    pauta.md roteiro.md voz.wav voz_palavras.json decupagem.json
    planos/ montagem.json mix.wav qa_relatorio.json export/
```

Observação: hoje os 13 MP4 (~190 MB) estão versionados direto no Git, na raiz. Recomendo movê-los para `referencias/` com Git LFS antes de o repositório crescer. Isso não foi feito nesta etapa, para não mexer nos arquivos originais sem a sua aprovação.

## 14. Ferramentas: o que existe neste ambiente (verificado)

| Ferramenta | Situação |
|---|---|
| FFmpeg / FFprobe 6.1.1 | Disponível. Decodifica H.264 e HEVC dos 13 MP4. |
| Python 3.13 + NumPy, Pillow | Disponível |
| OpenCV 5.1 (headless), RapidOCR | Instalados nesta sessão via pip (fluxo óptico, OCR das legendas) |
| Node 22, Chromium + Playwright | Disponíveis (opção para render 2D vetorial por canvas/SVG) |
| ImageMagick (`convert`) | Disponível |
| Blender | Não instalado. `bpy` 5.3.0 existe no PyPI (Blender como módulo Python, para render 3D sem interface). A validar na próxima etapa. |
| Whisper / reconhecimento de fala | Bloqueado: o download do modelo no Hugging Face foi recusado pela rede do ambiente |
| TTS (voz) | Não definido. Decisão sua (seção 15) |

## 15. Decisões pendentes (suas)

1. **Voz:** locução humana ou TTS (qual serviço e qual voz)?
2. **Motor de render:** 2D vetorial (SVG/canvas, mais rápido e consistente) ou 3D low-poly (Blender/bpy, mais próximo das referências nos cenários)? Recomendo **híbrido**: personagens 2D recortados sobre cenários 3D low-poly renderizados como fundo. É o que as referências fazem.
3. **Rede:** liberar o Hugging Face (alinhamento de palavras com Whisper) ou usar um TTS que já devolva os tempos.
4. **Arquivo `Padrão Modo Curioso.md`:** ele não está no repositório (detalhe na auditoria). Reenviar, ou confirmar que a versão no skill do canal é a oficial.

## 16. Próxima etapa proposta (sem gerar o vídeo completo)

1. Teste técnico de 10 s: 1 cenário, o Heitor, 5 planos, legenda, câmera e mix. Serve para validar o pipeline de ponta a ponta e passar pelo QA automático.
2. Folha de modelo do Heitor nas 4 vistas e 9 expressões, para aprovação.
3. Só depois disso: o primeiro episódio completo.
