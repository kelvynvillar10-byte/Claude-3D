"""Cenografia — kit da SALA do EP02 ("E se a sua namorada te desse um videogame…"), escala humana (Juca 1,75 m).

Peças (tudo em metros, medidas reais de uma sala de apartamento brasileiro):
- sofa_janela     sofá de 3 lugares com o encosto virado para a janela (o Juca senta de frente para a TV)
- rack_tv         rack baixo de madeira + TV de 55" na parede; a TELA é um vidro escuro: a imagem do jogo entra no
                  compositor pelos 4 cantos (âncoras), então nada de marca, logotipo ou texto 3D
- porta_corredor  batente com a porta aberta encostada na parede e o corredor escuro (a Jandira entra por ela)
- luminaria_pe    luminária de pé com cúpula de tecido acesa (grupo "artificial") — a luz da madrugada
- prato_comida    prato com arroz, feijão, bife e salada + copo de suco na mesa de centro (a comida que esfria)
Também registra o horário "tarde_sala" (sol baixo e dourado entrando pela janela da parede y0).
Nada aqui tem texto 3D.
"""
import math
import bpy, bmesh
from cenografia.nucleo.registro import componente
from cenografia.nucleo import geometria as G, materiais as M, luz as L
from cenografia.nucleo.materiais import lin
from cenografia.componentes.interior import tecido, plastico, _marcar

L.PRESETS.setdefault("tarde_sala", dict(sol_elev=13.0, sol_azim=205.0, sol_forca=4.6, sol_cor="#ffc98a", sol_raio=1.1,
                                        ceu_forca=0.5, ar=1.0, aerosol=2.4, ozonio=1.0,
                                        pesos={"ceu": 1.0, "sol": 1.0, "artificial": 0.15, "efeito": 0.0}))


@componente("sofa_janela")
def sofa_janela(ctx, p, rng, col):
    """Sofá de 3 lugares (assento a 45 cm, encosto a 85 cm) virado para +y: o encosto fica do lado y0 (janela)."""
    x, y, Lg, P = p["x"], p["y"], p.get("largura", 2.1), p.get("profundidade", 0.92)
    tec = tecido(p.get("cor", "#c25a3f"), 600); mad = M.madeira("#4a3222", escala=2.0)
    x0, x1, y0, y1 = x - Lg / 2, x + Lg / 2, y - P / 2, y + P / 2
    for i, (px, py) in enumerate([(x0 + 0.08, y0 + 0.08), (x1 - 0.08, y0 + 0.08), (x0 + 0.08, y1 - 0.08), (x1 - 0.08, y1 - 0.08)]):
        G.cilindro(f"sofa_pe_{i}", (px, py, 0), 0.022, 0.12, mad, col, lados=16, raio_topo=0.016)
    G.caixa("sofa_base", (x0, y0, 0.12), (x1, y1, 0.32), tec, col, chanfro=0.03)["suspenso"] = True
    G.caixa("sofa_encosto", (x0, y0, 0.32), (x1, y0 + 0.22, 0.85), tec, col, chanfro=0.05)
    for lado, (xa, xb) in (("esq", (x0, x0 + 0.2)), ("dir", (x1 - 0.2, x1))):
        G.caixa(f"sofa_braco_{lado}", (xa, y0 + 0.2, 0.32), (xb, y1, 0.62), tec, col, chanfro=0.05)
    n = 3; w = (Lg - 0.4) / n
    for k in range(n):
        c = G.caixa(f"sofa_assento_{k}", (x0 + 0.2 + k * w + 0.005, y0 + 0.22, 0.32), (x0 + 0.2 + (k + 1) * w - 0.005, y1 - 0.02, 0.45), tec, col, chanfro=0.04)
        G.deformar_ruido(c, forca=0.008, escala=0.2, semente=k)
    for k in range(2):
        a = G.caixa(f"sofa_almofada_{k}", (-0.22, -0.07, 0), (0.22, 0.07, 0.42), tecido(p.get("cor_almofada", "#e7c35a"), 600), col, chanfro=0.06)
        a.location = (x0 + 0.42 + k * (Lg - 0.84), y0 + 0.32, 0.45); a.rotation_euler = (math.radians(12), 0, math.radians(rng.uniform(-8, 8)))
        a["suspenso"] = True
    manta = G.caixa("sofa_manta", (x1 - 0.6, y0 + 0.02, 0.62), (x1 - 0.05, y0 + 0.24, 0.9), tecido(p.get("cor_manta", "#3e6f8f"), 300), col, chanfro=0.03)
    G.deformar_ruido(manta, forca=0.02, escala=0.15, semente=7); manta["suspenso"] = True


@componente("rack_tv")
def rack_tv(ctx, p, rng, col):
    """Rack de 1,8 m e TV de 55" (tela 1,22 × 0,69 m) pendurada na parede y = p['y_parede'], virada para −y."""
    x, yp = p["x"], p["y_parede"]
    m = M.madeira(p.get("cor", "#6b4a33"), escala=2.2); preto = M.pintura("#111214", rug=0.35)
    r0, r1 = yp - 0.42, yp - 0.02
    objs = [G.caixa("rack_corpo", (x - 0.9, r0, 0.12), (x + 0.9, r1, 0.5), m, col, chanfro=0.008)]
    for i, px in enumerate((x - 0.82, x + 0.82)):
        objs.append(G.caixa(f"rack_pe_{i}", (px - 0.03, r0 + 0.05, 0.0), (px + 0.03, r1 - 0.05, 0.12), preto, col))
    for i, px in enumerate((x - 0.6, x, x + 0.6)):   # portas de correr com puxador
        objs.append(G.caixa(f"rack_porta_{i}", (px - 0.29, r0 - 0.006, 0.16), (px + 0.29, r0, 0.46), M.madeira("#7a5640", escala=2.2), col, chanfro=0.003))
        objs.append(G.caixa(f"rack_puxador_{i}", (px - 0.06, r0 - 0.016, 0.42), (px + 0.06, r0 - 0.006, 0.43), M.pintura("#c9c3b8", rug=0.3, metal=0.8), col))
    zc = p.get("z_centro_tela", 1.05); W, H = 1.25, 0.72
    tv = G.caixa("tv_corpo", (x - W / 2, yp - 0.07, zc - H / 2), (x + W / 2, yp - 0.02, zc + H / 2), preto, col, chanfro=0.006)
    tela = G.caixa("tv_tela", (x - W / 2 + 0.012, yp - 0.072, zc - H / 2 + 0.012), (x + W / 2 - 0.012, yp - 0.069, zc + H / 2 - 0.012),
                   M.vidro("#07090c", reflexo=0.12), col)
    objs += [tv, tela]
    # decoração do rack: vaso pequeno, livros deitados e uma caixa de som (sem marca)
    objs.append(G.cilindro("rack_vaso", (x + 0.68, r0 + 0.2, 0.5), 0.05, 0.16, M.pintura("#e9e4da", rug=0.4), col, lados=24, raio_topo=0.035))
    for k in range(3):
        objs.append(G.caixa(f"rack_livro_{k}", (x - 0.82, r0 + 0.08, 0.5 + k * 0.035), (x - 0.55 + k * 0.02, r0 + 0.3, 0.5 + (k + 1) * 0.035 - 0.003),
                            plastico(["#b8403a", "#2f6aa3", "#e1b33f"][k], 0.6), col, chanfro=0.002))
    objs.append(G.caixa("rack_som", (x + 0.38, r0 + 0.1, 0.5), (x + 0.5, r0 + 0.3, 0.72), M.pintura("#2a2d33", rug=0.6), col, chanfro=0.01))
    _marcar(objs, suspenso=True)


@componente("porta_corredor")
def porta_corredor(ctx, p, rng, col):
    """Porta aberta na parede x = p['x_parede'] (vão de 0,9 × 2,1 m centrado em y): batente, folha aberta encostada
    na parede e o corredor escuro dentro do vão (fundo pintado, em leve degradê pela luz)."""
    xp, y = p["x_parede"], p["y"]; w, h = 0.9, 2.1
    bat = M.pintura("#f3f2ee", rug=0.4)
    escuro = M.pintura(p.get("cor_corredor", "#3a3430"), rug=0.9)
    objs = [G.caixa("corredor_fundo", (xp + 0.004, y - w / 2, 0.0), (xp + 0.012, y + w / 2, h), escuro, col)]
    objs.append(G.caixa("corredor_piso", (xp + 0.004, y - w / 2, 0.0), (xp + 0.02, y + w / 2, 0.004), M.madeira("#5d3f29", escala=3.0), col))
    for nome, c0, c1 in [("batente_a", (xp, y - w / 2 - 0.06, 0), (xp + 0.03, y - w / 2, h + 0.06)),
                         ("batente_b", (xp, y + w / 2, 0), (xp + 0.03, y + w / 2 + 0.06, h + 0.06)),
                         ("batente_c", (xp, y - w / 2 - 0.06, h), (xp + 0.03, y + w / 2 + 0.06, h + 0.06))]:
        objs.append(G.caixa(nome, c0, c1, bat, col, chanfro=0.004))
    folha = G.caixa("porta_folha", (xp + 0.03, y + w / 2 + 0.06, 0.01), (xp + 0.07, y + w / 2 + 0.06 + w - 0.04, h - 0.01),
                    M.madeira(p.get("cor_porta", "#a8774c"), escala=2.0), col, chanfro=0.004)
    mac = G.cilindro_eixo("porta_macaneta", (xp + 0.07, y + w / 2 + w - 0.1, 1.0), (xp + 0.12, y + w / 2 + w - 0.1, 1.0), 0.018,
                          M.pintura("#c9c3b8", rug=0.25, metal=0.9), col)
    objs += [folha, mac]
    _marcar(objs, suspenso=True)


@componente("luminaria_pe")
def luminaria_pe(ctx, p, rng, col):
    x, y = p["x"], p["y"]
    met = M.pintura("#2b2b2e", rug=0.35, metal=0.7)
    objs = [G.cilindro("lum_base", (x, y, 0.0), 0.16, 0.025, met, col, lados=32, chanfro=0.006),
            G.cilindro_eixo("lum_haste", (x, y, 0.025), (x, y, 1.45), 0.012, met, col)]
    cup = G.cilindro("lum_cupula", (x, y, 1.38), 0.22, 0.3, M.emissor(p.get("cor_cupula", "#ffe0b0"), p.get("forca_cupula", 2.5)), col,
                     lados=40, raio_topo=0.15)
    cup.lightgroup = "artificial"; objs.append(cup)
    Lz = bpy.data.lights.new("lum_luz", "POINT"); Lz.energy = p.get("watts", 120.0); Lz.color = lin("#ffd29a")[:3]; Lz.shadow_soft_size = 0.12
    lo = bpy.data.objects.new("lum_luz", Lz); bpy.context.scene.collection.objects.link(lo); lo.location = (x, y, 1.5); lo.lightgroup = "artificial"
    _marcar(objs, suspenso=True)


def _bolota(nome, centro, raio, escala, mat, col, sub=3):
    """Esfera achatada no lugar certo (a escala é aplicada nos vértices em volta do centro, não da origem do mundo)."""
    o = G.esfera(nome, (0.0, 0.0, 0.0), raio, mat, col, sub=sub)
    for v in o.data.vertices:
        v.co.x *= escala[0]; v.co.y *= escala[1]; v.co.z *= escala[2]
        v.co.x += centro[0]; v.co.y += centro[1]; v.co.z += centro[2]
    return o


@componente("prato_comida")
def prato_comida(ctx, p, rng, col):
    """Prato feito (arroz, feijão, bife, salada) e um copo de suco sobre a mesa (z = altura do tampo)."""
    x, y, z = p["x"], p["y"], p["z"]
    louca = M.pintura("#f4f1ea", rug=0.25)
    objs = [G.cilindro("prato", (x, y, z), 0.135, 0.018, louca, col, lados=48, raio_topo=0.12, chanfro=0.004)]
    arroz = _bolota("arroz", (x - 0.045, y + 0.03, z + 0.024), 0.055, (1.0, 1.0, 0.45), M.pintura("#efe6cf", rug=0.9), col)
    G.deformar_ruido(arroz, forca=0.004, escala=0.02, semente=1)
    feijao = _bolota("feijao", (x + 0.045, y + 0.04, z + 0.022), 0.05, (1.0, 1.0, 0.35), M.pintura("#4a2a1c", rug=0.55), col)
    bife = _bolota("bife", (x + 0.01, y - 0.05, z + 0.024), 0.06, (1.3, 0.8, 0.25), M.pintura("#7a3f22", rug=0.6), col)
    G.deformar_ruido(bife, forca=0.004, escala=0.03, semente=2)
    salada = _bolota("salada", (x - 0.07, y - 0.035, z + 0.024), 0.036, (1.0, 1.0, 0.6), M.folhagem("#5c9a3a"), col, sub=2)
    tom = G.esfera("tomate", (x - 0.05, y - 0.06, z + 0.03), 0.016, M.pintura("#d23a2a", rug=0.3), col, sub=2)
    garfo = G.caixa("garfo", (x + 0.15, y - 0.08, z), (x + 0.165, y + 0.08, z + 0.004), M.pintura("#c9c3b8", rug=0.25, metal=0.9), col)
    copo = G.cilindro("copo", (x - 0.28, y - 0.1, z), 0.035, 0.12, M.vidro("#dfe8ee", reflexo=0.2), col, lados=32, raio_topo=0.04)
    suco = G.cilindro("suco", (x - 0.28, y - 0.1, z + 0.005), 0.032, 0.085, M.pintura("#f08a24", rug=0.2), col, lados=32, raio_topo=0.035)
    objs += [arroz, feijao, bife, salada, tom, garfo, copo, suco]
    _marcar(objs, suspenso=True)
