# Modo Curioso Studio AI

Estúdio de produção dos vídeos verticais "E se…?" do canal **Modo Curioso**: animação 2D sobre cenários 3D, narração rápida, ciência com números reais e identidade visual consistente.

**Estado atual:** Etapa 1 concluída (auditoria das referências, identidade oficial, arquitetura técnica e ambiente reproduzível). **O vídeo-piloto ainda não foi iniciado.**

## Começar numa sessão nova

```bash
bash ambiente/restaurar.sh            # instala tudo nas versões travadas e verifica
.venv/bin/python ambiente/verificar.py
```
Resultado esperado: `RESULTADO: AMBIENTE PRONTO`. Procedimento completo, Docker e solução de problemas: [`ambiente/RESTAURAR.md`](ambiente/RESTAURAR.md).

## Mapa do repositório

| Pasta / arquivo | Conteúdo |
|---|---|
| [`docs/IDENTIDADE_OFICIAL.md`](docs/IDENTIDADE_OFICIAL.md) | **Fonte da verdade da identidade:** voz (ID-001), estampa "Modo Curioso" (ID-002), grafias oficiais (ID-003) |
| [`docs/AUDITORIA_REFERENCIAS.md`](docs/AUDITORIA_REFERENCIAS.md) | Inventário e análise medida dos 13 MP4 de referência |
| [`docs/MANUAL_DIRECAO_ARTE.md`](docs/MANUAL_DIRECAO_ARTE.md) | Personagens, cenários, luz, cor |
| [`docs/MANUAL_ANIMACAO.md`](docs/MANUAL_ANIMACAO.md) | Poses, expressões, câmera, efeitos |
| [`docs/PADRAO_EDICAO.md`](docs/PADRAO_EDICAO.md) | Ritmo, legendas, sincronia, áudio |
| [`docs/PIPELINE_PRODUCAO.md`](docs/PIPELINE_PRODUCAO.md) | Etapas de produção e **arquitetura técnica (seção 15)** |
| `docs/evidencias/`, `docs/dados/` | Folhas de contato e medições da auditoria |
| [`ambiente/`](ambiente/) | Instalação, versões exatas, verificação, restauração |
| [`Dockerfile`](Dockerfile) | Imagem reproduzível do ambiente |
| [`tools/analise/`](tools/analise/) | Scripts de medição (também servem de QA automático) |
| [`skills/modo-curioso-padrao/`](skills/modo-curioso-padrao/) | Skill do canal alinhado à identidade oficial |
| `assets/fontes/` | Nunito e Roboto Condensed (OFL), com instâncias ExtraBold |
| `snaptik_*.mp4`, `v*_*.jpg`, `index.html` | Material de referência original (de outro criador; só para estudo) |

## Regras que nunca mudam
- Camiseta dos personagens: **"Modo Curioso"**. Marca d'água: **"MODO CURIOSO"**.
- Nada de personagem, marca ou obra de terceiros. Nenhuma voz clonada sem autorização.
- Nenhuma chave de API no repositório.
