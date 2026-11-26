# Pós-produção da narração (fluxo aprovado em 26/11/2026)

O diretor gera a narração no site **MiniMax Audio** com a voz `Portuguese_CaptivatingStoryteller` e envia o áudio junto com o
texto exato. Este módulo transforma esse áudio na narração final do Modo Curioso. **Nada aqui chama API nem gasta créditos.**

## Passo a passo
```
# 0. (opcional, antes de gerar) ficha de geração por trecho: intenção, velocidade, volume, tom, emoção e pausa sugerida
.venv/bin/python narracao/pos/processar.py ficha roteiro.txt --saida ficha.md

# 1. análise: copia o original (intacto, com SHA-256), mede, alinha as palavras e grava o RASCUNHO da direção
.venv/bin/python narracao/pos/processar.py analisar narracao_do_site.mp3 --texto roteiro.txt --nome ep01_narracao

# 2. o Claude revisa narracao/edicoes/ep01_narracao/direcao_edicao.json frase a frase e marca "revisado": true

# 3. finalização: edição, tratamento, tempos finais, marcações, QA e relatório
.venv/bin/python narracao/pos/processar.py finalizar ep01_narracao
```

## Entregas (`narracao/edicoes/<nome>/`)
| Arquivo | O que é |
|---|---|
| `original/` | o áudio enviado, sem nenhuma alteração, e o `SHA256.txt` |
| `voz_final.wav` | narração final, 48 kHz, 24 bits |
| `voz_final.mp3` | a mesma narração em 320 kbps, para ouvir e revisar |
| `voz_palavras.json` | início e fim de cada palavra **no áudio final** |
| `marcacoes.json` | frases e intenções, destaques, pausas, cortes visuais, impactos, espaços para efeitos sonoros e transições |
| `conferencia_sincronia.mp4` | narração final com legendas de 2–3 palavras tiradas do `voz_palavras.json`, para conferir a sincronia (não é a legenda final) |
| `relatorio.md` | análise, direção, cada edição com o motivo, tratamento aplicado, QA e limitações |
| `analise.json`, `direcao_edicao.json`, `qa.json`, `imagens/` | dados de apoio: forma de onda e espectro, antes e depois |

## O que a edição faz e o que não faz
- **Faz:**
  - pausas por intenção (tabela em `direcao_edicao.py`);
  - destaque de até 2 dB em palavras-chave;
  - nível por frase de até ±2 dB;
  - tratamento condicional: graves, cliques, ruído, equalização, de-esser, compressão moderada e loudness;
  - transições suaves, só dentro das pausas.
- **Não faz:**
  - não muda o conteúdo falado;
  - não acelera nem desacelera;
  - não muda o tom;
  - não corta palavras: o QA confere que cada palavra é idêntica ao original, fora o ganho dirigido;
  - não adiciona efeitos sonoros.
- **Limite honesto:** a edição não cria interpretação que não foi gravada. Quando uma frase sai monótona, o relatório marca e recomenda gerar de novo só aquela frase.

## Regras de pausa (aprovadas)
- **Tetos por intenção:**
  - suspense e revelação: até 0,7 s;
  - surpresa: até 0,5 s;
  - ação: até 0,15 s.
- **Nunca ≥ 0,8 s.**
- **Vírgulas:** mantêm a pausa natural, dentro de uma faixa que depende da intenção.
- **Pausa sem pontuação:** acima de 0,25 s é inadequada e vira 0,10 s.
- **Início e fim:** 0,15 s no início e 0,50 s no final.
- **Respirações:** ficam quando cabem na pausa-alvo.

## Tratamento (`preset_v1.json`, a "assinatura sonora")
| Etapa | Quando entra | Ajuste |
|---|---|---|
| Filtro de graves | sempre | 75 Hz |
| Remoção de cliques | só se houver cliques | — |
| Redução de ruído | só se o piso das pausas passar de −65 dBFS | leve |
| Equalização | sempre | corpo +1,5 dB em 150 Hz; lama −1,5 dB em 320 Hz; presença +1,5 dB em 3,5 kHz; ar +1 dB em 10 kHz (sem o "ar" quando a sibilância já está alta) |
| De-esser | só se a sibilância estiver alta | — |
| Compressão | sempre | 2,5:1 |
| Loudness | sempre | ganho fixo até −16 LUFS e limitador de pico verdadeiro em −1,5 dBTP |

Na F2, os ajustes são calibrados com a escuta do diretor. O atraso de cada filtro é medido e compensado, então os tempos das palavras valem para o arquivo final.

## Alinhamento de palavras
**Principal: Whisper local** (`faster-whisper`, modelo "medium", CPU, sem API e sem créditos). Aprovado pelo diretor em 26/11/2026.
1. Transcreve o que foi falado, com o tempo de cada palavra.
2. Compara com o texto informado. Se o áudio não tiver exatamente o roteiro, as diferenças aparecem no terminal e no relatório. Sem texto, usa a própria transcrição.
3. Ajusta os tempos pelas pausas medidas: nenhuma palavra começa ou termina dentro de um silêncio.

A edição só mexe no **silêncio medido** dentro de cada pausa, então as caudas das palavras ficam intactas.

Na 1ª narração real do EP01, o Whisper rodado de novo no áudio FINAL encontrou as 235 palavras, com diferença de início de 96 ms no p90.

O modelo (~1,5 GB) é baixado do Hugging Face no primeiro uso de cada container novo. A rede do ambiente libera `huggingface.co`, `us.aws.cdn.hf.co` e os servidores de download do HF.

**Reserva (sem modelos externos, usada no teste F0):**
- referência do espeak-ng com tempos exatos;
- DTW com mediana de 3 vozes, ancorado nas pausas reais.

Funciona bem em vozes parecidas com a referência. Na voz real da MiniMax, errou trechos inteiros quando o texto não era exatamente o falado.

## Teste
`.venv/bin/python narracao/pos/testes/teste_f0.py`. O teste roda o fluxo inteiro com uma narração sintética "estragada" de propósito: outra voz, tom deslocado, pausa de 1,1 s no meio da frase, ruído, clique e MP3 de 44,1 kHz. O exemplo de saída fica em `testes/saidas/f0_exemplo/`, sem o WAV.
