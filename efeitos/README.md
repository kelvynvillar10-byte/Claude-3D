# Efeitos e poderes

- `nucleo/`: núcleo de efeitos (E7). Base (parâmetros, intensidades, fases, registro, mesa), partículas, curvas fractais, corda, distorção, marcas, rastros, quadro de impacto, tremida, contatos, segurança de flashes e proteção de rosto e estampa. A luz 2D e os encaixes ficam no compositor da cenografia (`cenografia/nucleo/compositor.py`).
- `demos/`: plugins de demonstração do núcleo. **Não são poderes.**
- `poderes/`: um arquivo por poder (E8, só com aprovação).

## Uso
```python
from efeitos.nucleo.base import Params, Mesa, carregar_plugins
REG = carregar_plugins()
ef = REG["demo_faiscas"](Params(intensidade="moderado", cor="#ffb347", duracao=2.8), inicio=0.0)
mesa = Mesa([ef], fps=30)
mesa.preparar(placa, cam, t, quadro, personagem={"pe_mundo": (x, y, z), "altura_m": 1.4, "pose": pose, "vista": "frente", "direcao": 1})
img = placa.compor(..., personagem=desenhista, profundidade_personagem=z_pe, efeitos=mesa, deslocamento_px=mesa.tremida())
```
Testes e resultados: `cenografia/testes/e7_testes.py` e `cenografia/testes/E7_RELATORIO.md`.
