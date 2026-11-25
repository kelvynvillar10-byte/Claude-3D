# Restauração do ambiente — Modo Curioso Studio AI

Como reconstruir o estúdio quando o container do Claude (ou qualquer máquina) for descartado. Tudo o que é necessário está versionado neste repositório. O que não está versionado (`.venv/`, `_tmp/`, renders) é recriado pelos scripts.

## O que fica salvo no GitHub

| O quê | Onde |
|---|---|
| Documentos (auditoria, identidade, manuais, pipeline) | `docs/` |
| Skill do canal alinhado à identidade | `skills/modo-curioso-padrao/SKILL.md` |
| Lista de pacotes de sistema e versões exatas | `ambiente/apt-pacotes.txt`, `ambiente/apt-versoes.lock.txt` |
| Bibliotecas Python (diretas e lock completo) | `ambiente/requirements.in`, `ambiente/requirements.lock.txt` |
| Versões de tudo, em uma tabela | `ambiente/VERSOES.md` |
| Fontes oficiais + hashes | `assets/fontes/`, `ambiente/fontes.sha256` |
| Instalação, verificação, restauração | `ambiente/instalar.sh`, `ambiente/verificar.py`, `ambiente/restaurar.sh` |
| Imagem reproduzível | `Dockerfile`, `.dockerignore` |
| Ferramentas de análise e QA | `tools/analise/` |

## Procedimento A: sessão nova do Claude Code (cloud)

1. Abra uma sessão nova com o repositório `Claude-3D`.
2. Se o ambiente cloud tiver o script de configuração do estúdio (ver "Automação" abaixo), o ambiente já sobe instalado. Confira com:
   ```bash
   .venv/bin/python ambiente/verificar.py
   ```
3. Se não tiver, rode:
   ```bash
   bash ambiente/restaurar.sh --branch ccr-68f2d393-91pzsl
   ```
   (Troque o branch se o trabalho tiver sido mesclado no `main`.)
4. O resultado esperado termina em `RESULTADO: AMBIENTE PRONTO`.
5. Diga ao Claude: "Leia o CLAUDE.md e continue de onde paramos". O `CLAUDE.md` aponta para os documentos e para o estado atual.

Tempo estimado: alguns minutos. O maior download é o Blender (`bpy`, que ocupa ~0,9 GB instalado). O build Docker completo levou ~3 min neste ambiente.

## Procedimento B: máquina Linux própria (Ubuntu 24.04)

```bash
git clone https://github.com/kelvynvillar10-byte/Claude-3D.git
cd Claude-3D
git checkout ccr-68f2d393-91pzsl    # ou main
bash ambiente/restaurar.sh           # usa sudo para o apt, se não for root
```

Sem acesso root: `bash ambiente/restaurar.sh --sem-apt`, com os pacotes de `ambiente/apt-pacotes.txt` instalados por quem administra a máquina.

## Procedimento C: Docker (qualquer sistema com Docker)

```bash
git clone https://github.com/kelvynvillar10-byte/Claude-3D.git && cd Claude-3D
docker build -t modo-curioso-studio .
docker run --rm -v "$PWD":/studio modo-curioso-studio python ambiente/verificar.py
docker run --rm -it -v "$PWD":/studio modo-curioso-studio          # shell de trabalho
```

Ou, num passo: `bash ambiente/restaurar.sh --docker`.

**Atrás de proxy HTTPS com CA própria** (é o caso do ambiente cloud do Claude):
```bash
dockerd > /tmp/dockerd.log 2>&1 &                    # se o daemon não estiver rodando
cp "$SSL_CERT_FILE" ambiente/docker/certs/proxy-ca.crt  # *.crt não é versionado
docker build --network host --build-arg HTTPS_PROXY="$HTTPS_PROXY" -t modo-curioso-studio .
```
Não passe `HTTP_PROXY` nesse ambiente: o proxy recusa HTTP simples, e o apt do Ubuntu sai direto.

## Conferir e corrigir

```bash
.venv/bin/python ambiente/verificar.py            # completo (inclui testes reais de render)
.venv/bin/python ambiente/verificar.py --rapido   # só presença e versões
.venv/bin/python ambiente/verificar.py --rede     # também testa os serviços externos
```

| Resultado | O que fazer |
|---|---|
| `AUSENTE` em programa ou biblioteca do sistema | `bash ambiente/instalar.sh` (com root) |
| `AUSENTE`/`INCOMPATÍVEL` em pacote Python | `bash ambiente/instalar.sh --sem-apt` (o `uv pip sync` volta exatamente ao lock) |
| `INCOMPATÍVEL` em Python | `rm -rf .venv && bash ambiente/instalar.sh --sem-apt` |
| `FALTA`/`INCOMPATÍVEL` em fonte | `git checkout -- assets/fontes ambiente/fontes.sha256`, ou apague a fonte e rode `.venv/bin/python ambiente/fontes.py` |
| `AVISO` de rede (bloqueado) | Liberar o host nas configurações de rede do ambiente (ElevenLabs para a voz; os sites de modelos 3D para os cenários) |
| `AVISO` de GPU | Esperado. A arquitetura usa Blender em CPU (`docs/PIPELINE_PRODUCAO.md`, seção 15.1) |

## Mudar uma dependência (sem perder a reprodutibilidade)

1. Edite `ambiente/requirements.in` (ou `ambiente/apt-pacotes.txt`).
2. Gere o lock: `uv pip compile --python-version 3.13 --python-platform x86_64-manylinux_2_28 ambiente/requirements.in -o ambiente/requirements.lock.txt`
3. `bash ambiente/instalar.sh`. Para apt, atualize também `ambiente/apt-versoes.lock.txt`.
4. `.venv/bin/python ambiente/registrar_versoes.py` (regera `VERSOES.md`).
5. `docker build ...` e o verificador dentro da imagem.
6. Commit e push de tudo junto.

## Automação na sessão cloud (opcional)

O ambiente cloud do Claude pode rodar um **script de configuração** toda vez que um container novo sobe. Com ele, cada sessão já começa com o estúdio instalado:
```bash
if [ -d Claude-3D ]; then (cd Claude-3D && bash ambiente/instalar.sh --sem-verificar); fi
```
Esse script fica salvo nas configurações do ambiente (não no repositório).

**Configurado em 25/11/2026:** ambiente cloud pessoal **"Claude-3D"**, ligado ao repositório `kelvynvillar10-byte/Claude-3D`, com esse script e a mesma rede do ambiente padrão (gerenciadores de pacotes liberados, sem hosts extras). Ao abrir uma sessão nova, escolha o ambiente "Claude-3D". O script só fica comprovado quando uma sessão nova subir nele. Se algo falhar, o Procedimento A continua valendo. Os hosts da ElevenLabs e dos modelos 3D ainda não estão liberados: serão adicionados a esse ambiente quando você aprovar.

## Limites conhecidos
- Python e bibliotecas são idênticos em qualquer lugar (lock + Python do uv). Os pacotes **apt** seguem as atualizações do Ubuntu 24.04. As versões exatas de hoje estão registradas, e `--exato` tenta instalá-las, mas versões antigas podem sair dos espelhos do Ubuntu.
- A imagem base Docker é fixada por digest e não muda.
- Serviços externos (ElevenLabs, bibliotecas de assets) não fazem parte do ambiente: precisam de rede liberada e de credenciais. As chaves nunca vão para o repositório.
