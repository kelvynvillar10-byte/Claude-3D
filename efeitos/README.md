# Efeitos e poderes

- `nucleo/`: núcleo de efeitos (E7). Base (parâmetros, intensidades, fases, registro, mesa), partículas, curvas fractais, corda, distorção, marcas, rastros, quadro de impacto, tremida, contatos, segurança de flashes e proteção de rosto e estampa. A luz 2D e os encaixes ficam no compositor da cenografia (`cenografia/nucleo/compositor.py`).
- `demos/`: plugins de demonstração do núcleo. **Não são poderes.**
- `poderes/`: um arquivo por poder. **E8 parte 1: `eletricidade.py` e `terra.py`** (não mexem no rig). **E8 parte 2: `voo.py`** (usa a extensão X2 aprovada; o poder controla o movimento do Heitor e a cena pede `estado(t)`). Aranha e elasticidade só depois das extensões do rig aprovadas.

## Uso
```python
from efeitos.nucleo.base import Params, Mesa, carregar_plugins
REG = carregar_plugins()
ef = REG["demo_faiscas"](Params(intensidade="moderado", cor="#ffb347", duracao=2.8), inicio=0.0)
mesa = Mesa([ef], fps=30)
mesa.preparar(placa, cam, t, quadro, personagem={"pe_mundo": (x, y, z), "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1})
img = placa.compor(..., personagem=desenhista, profundidade_personagem=z_pe, efeitos=mesa, deslocamento_px=mesa.tremida())
```
Testes e resultados: `cenografia/testes/e7_testes.py` / `E7_RELATORIO.md` (núcleo) e `e8_testes.py` / `E8_RELATORIO.md` (poderes, parte 1) e `e8_voo_testes.py` / `E8_VOO_RELATORIO.md` (voo).
