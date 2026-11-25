"""Componentes PROVISÓRIOS da E0 — só para exercitar o núcleo (camadas, luz, paralaxe, cache).

Não são o kit final: ruas, prédios, veículos e ambientação detalhados são das etapas E2–E5.
Mesmo assim já usam os materiais procedurais, chanfros e variação por semente da biblioteca.
"""
import math
from cenografia.nucleo.registro import componente
from cenografia.nucleo import geometria as G, materiais as M, luz as L


def _mat(spec, padrao):
    """spec: None → material padrão; dict {"nome": ..., parâmetros} → material do catálogo (E1)."""
    if not spec:
        return padrao()
    spec = dict(spec); return M.por_nome(spec.pop("nome"), **spec)


@componente("rua_reta")
def rua_reta(ctx, p, rng, col):
    """Rua ao longo de y: pista de asfalto, faixa central tracejada, meio-fios chanfrados e calçadas em placas."""
    y0, y1 = p.get("y0", -2.0), p.get("y1", 80.0); larg = p.get("largura_pista", 7.0); calc = p.get("largura_calcada", 3.2)
    um = p.get("umidade", 0.0)
    G.caixa("pista", (-larg / 2, y0, -0.05), (larg / 2, y1, 0.0), M.asfalto(desgaste=p.get("desgaste", 0.55), umidade=um), col)
    tinta = M.pintura("#e9e2cf", rug=0.7, desgaste=0.6)
    y = y0 + 1.0; i = 0
    while y < y1 - 3:
        G.caixa(f"faixa{i}", (-0.07, y, 0.0), (0.07, y + 2.2, 0.004), tinta, col); y += 5.0; i += 1
    for s in (-1, 1):
        xm = s * larg / 2
        G.caixa(f"meiofio{s}", (xm if s > 0 else xm - 0.18, y0, -0.05), (xm + 0.18 if s > 0 else xm, y1, 0.15),
                M.concreto("#b9b2a4", placa_m=(1.2, 0.18), desgaste=0.5, sujeira=0.6), col, chanfro=0.03)
        xc0, xc1 = (xm + 0.18, xm + 0.18 + calc) if s > 0 else (xm - 0.18 - calc, xm - 0.18)
        mat_calc = _mat(dict(p["calcada"], umidade=um) if p.get("calcada") else None, lambda: M.concreto("#aaa294", placa_m=(1.0, 1.0), umidade=um))
        G.caixa(f"calcada{s}", (xc0, y0, -0.05), (xc1, y1, 0.13), mat_calc, col)


@componente("predio_bloco")
def predio_bloco(ctx, p, rng, col):
    """Prédio provisório: volume com fachada voltada para a rua (lado ±1), janelas recuadas com moldura e peitoril,
    algumas acesas (grupo 'artificial'), térreo comercial com porta e vitrine, platibanda no topo."""
    x0, x1, y0, y1, alt = p["x0"], p["x1"], p["y0"], p["y1"], p["altura"]; lado = p.get("lado", 1)   # lado: fachada em x0 (+1) ou x1 (−1)
    if p.get("mat"):
        mat = _mat(p["mat"], None)
    else:
        mat = M.tijolo(p.get("cor", "#9c4f35")) if p.get("material") == "tijolo" else M.reboco(p.get("cor", "#e2c9a4"), desgaste=p.get("desgaste", 0.4))
    nome = p.get("nome", f"predio_{int(x0)}_{int(y0)}")
    G.caixa(nome, (x0, y0, 0), (x1, y1, alt), mat, col, chanfro=0.02)
    fx = x0 if lado > 0 else x1; dx = -lado
    G.caixa(nome + "_plat", (min(fx, fx + dx * 0.25) if True else 0, y0 - 0.05, alt), (max(fx, fx + dx * 0.25), y1 + 0.05, alt + 0.45),
            M.reboco("#f1e8d8", desgaste=0.5), col, chanfro=0.02)
    moldura = M.pintura("#f3eee4", rug=0.6); vid = M.vidro(); acesa = M.emissor("#ffcf8a", 3.5)
    cortinas = ["#c9b79a", "#8fa7b8", "#d9cfc0", "#b98c7a"]
    jl, jh = p.get("janela", (1.1, 1.4)); passo_y, passo_z = p.get("passo", (2.6, 3.0))
    nj = max(1, int((y1 - y0 - 1.0) / passo_y)); nz = max(0, int((alt - 3.6) / passo_z))
    for k in range(nz):
        z = 3.6 + k * passo_z + 0.5
        for j in range(nj):
            yc = y0 + (y1 - y0) / 2 + (j - (nj - 1) / 2) * passo_y
            fora = fx - dx * 0.0
            # moldura (saliente) + vidro recuado + peitoril
            G.caixa(f"{nome}_mol_{k}_{j}", (min(fora, fora - dx * 0.06), yc - jl / 2 - 0.1, z - 0.1), (max(fora, fora - dx * 0.06), yc + jl / 2 + 0.1, z + jh + 0.1), moldura, col)
            liga = rng.random() < p.get("acesas", 0.25)
            m_v = acesa if liga else (vid if rng.random() < 0.6 else M.pintura(rng.choice(cortinas), rug=0.8))
            o = G.caixa(f"{nome}_vid_{k}_{j}", (min(fora, fora - dx * 0.075), yc - jl / 2, z), (max(fora, fora - dx * 0.075), yc + jl / 2, z + jh), m_v, col)
            if liga:
                o.lightgroup = "artificial"
            G.caixa(f"{nome}_pei_{k}_{j}", (min(fora, fora - dx * 0.16), yc - jl / 2 - 0.15, z - 0.16), (max(fora, fora - dx * 0.16), yc + jl / 2 + 0.15, z - 0.08),
                    moldura, col, chanfro=0.01)
    # térreo comercial: porta de enrolar + vitrine acesa + toldo
    if p.get("terreo", True):
        yc = (y0 + y1) / 2
        G.caixa(nome + "_porta", (min(fx, fx - dx * 0.05), yc - 1.6, 0.13), (max(fx, fx - dx * 0.05), yc - 0.1, 2.6), M.pintura("#6d737a", rug=0.5, metal=0.4, desgaste=0.5), col)
        vit = G.caixa(nome + "_vitrine", (min(fx, fx - dx * 0.05), yc + 0.2, 0.6), (max(fx, fx - dx * 0.05), yc + 2.4, 2.5), M.emissor("#ffe2b0", 1.6), col)
        vit.lightgroup = "artificial"
        G.caixa(nome + "_toldo", (min(fx, fx - dx * 1.1), yc - 1.8, 2.75), (max(fx, fx - dx * 1.1), yc + 2.6, 2.85), M.pintura(p.get("toldo", "#2f5d62"), rug=0.8), col, chanfro=0.02)


@componente("poste")
def poste(ctx, p, rng, col):
    x, y = p["x"], p["y"]; alt = p.get("altura", 6.5); lado = p.get("lado", 1)
    metal = M.pintura("#3d4148", rug=0.45, metal=0.6, desgaste=0.3)
    G.cilindro(f"poste_{x}_{y}", (x, y, 0.13), 0.09, alt, metal, col, raio_topo=0.06)
    G.cilindro(f"poste_base_{x}_{y}", (x, y, 0.13), 0.15, 0.5, metal, col)
    ponta = (x + lado * 1.3, y, alt + 0.05)
    G.cilindro_eixo(f"poste_braco_{x}_{y}", (x, y, alt - 0.1), ponta, 0.045, metal, col)
    G.caixa(f"poste_lum_{x}_{y}", (ponta[0] - 0.28, y - 0.14, alt - 0.08), (ponta[0] + 0.28, y + 0.14, alt + 0.06), metal, col, chanfro=0.02)
    lamp = G.caixa(f"poste_lamp_{x}_{y}", (ponta[0] - 0.22, y - 0.1, alt - 0.1), (ponta[0] + 0.22, y + 0.1, alt - 0.08), M.emissor("#ffe8c8", 18.0), col)
    lamp.lightgroup = "artificial"
    L.luz_ponto(f"poste_luz_{x}_{y}", (ponta[0], y, alt - 0.2), p.get("watts", 650), "#ffe3bd", "artificial", raio=0.15,
                tipo="SPOT", alvo=(ponta[0], y, 0), angulo=120)


@componente("arbusto_vaso")
def arbusto_vaso(ctx, p, rng, col):
    x, y = p["x"], p["y"]; r = p.get("raio", 0.45)
    G.caixa(f"vaso_{x}_{y}", (x - r, y - r, 0.13), (x + r, y + r, 0.7), M.concreto("#8d8577", placa_m=(0.6, 0.3)), col, chanfro=0.03)
    G.caixa(f"terra_{x}_{y}", (x - r + 0.05, y - r + 0.05, 0.7), (x + r - 0.05, y + r - 0.05, 0.72), M.terra(), col)
    for i in range(3):
        o = G.esfera(f"arb_{x}_{y}_{i}", (x + rng.uniform(-0.15, 0.15), y + rng.uniform(-0.15, 0.15), 0.95 + i * 0.18), r * (0.85 - i * 0.12),
                     M.folhagem(rng.choice(["#4f7a3a", "#5b8540", "#466e35"])), col)
        G.deformar_ruido(o, forca=0.12, escala=0.25)


@componente("banco")
def banco(ctx, p, rng, col):
    x, y = p["x"], p["y"]; comp = p.get("comprimento", 1.6)
    ferro = M.pintura("#2b2e33", rug=0.4, metal=0.6); mad = M.pintura("#8a5a3b", rug=0.75, desgaste=0.5)
    for s in (-1, 1):
        G.caixa(f"banco_pe{s}_{x}", (x - 0.25, y + s * (comp / 2 - 0.15) - 0.03, 0.13), (x + 0.25, y + s * (comp / 2 - 0.15) + 0.03, 0.55), ferro, col)
    for i in range(3):
        G.caixa(f"banco_ripa{i}_{x}", (x - 0.25 + i * 0.17, y - comp / 2, 0.55), (x - 0.25 + i * 0.17 + 0.14, y + comp / 2, 0.59), mad, col, chanfro=0.008)
    for i in range(2):
        G.caixa(f"banco_enc{i}_{x}", (x + 0.27, y - comp / 2, 0.7 + i * 0.16), (x + 0.31, y + comp / 2, 0.82 + i * 0.16), mad, col, chanfro=0.008)
