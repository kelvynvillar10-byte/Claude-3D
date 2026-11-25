"""Cenografia — kit de VEÍCULOS (E4): 5 carrocerias, ônibus urbano e moto, procedurais, sem marca nem modelo real.

Carroceria = LOFT de seções transversais ao longo do comprimento (frente em +x local):
- perfil do teto por tipo (capô, para-brisa, teto, vigia/tampa traseira), em pontos de controle;
- fundo na altura da soleira, subindo em ARCO sobre cada roda (a caixa de roda aparece de lado);
- planta arredondada (superelipse) e "tumblehome" (a parte de cima é mais estreita que a de baixo);
- cada face recebe o material pela posição e pela normal: pintura, vidro (para-brisa, janelas laterais com colunas
  A/B/C, vigia), lona (capota marítima da picape), faixa e teto (ônibus).
Peças: rodas (pneu + aro com raios, malha compartilhada), caixas de roda escuras, para-choques, grade, faróis e
lanternas (acendem com farois=True, no grupo de luz 'artificial'), placas SEM caracteres (modelo Mercosul em branco,
para não reproduzir placa real), retrovisores, frisos de porta e maçanetas.

Tipos: hatch, seda, suv, picape (com capota marítima), furgao, onibus, moto.
Componentes: veiculo (um veículo) e estacionamento (carros parados junto ao meio-fio, por semente).
"""
import math
import bpy, bmesh
from mathutils import Vector
from cenografia.nucleo.registro import componente
from cenografia.nucleo import geometria as G, materiais as M, luz as LZ

CORES = [("#e9e9e6", 0.28, 0.1), ("#a9adb3", 0.22, 0.6), ("#5b6067", 0.15, 0.5), ("#1d1f22", 0.15, 0.3),
         ("#9e1f1f", 0.07, 0.35), ("#1f4e8c", 0.06, 0.4), ("#c9b48a", 0.04, 0.4), ("#2f6b4f", 0.03, 0.4)]   # (cor, peso, metal)

# u = posição relativa ao comprimento (0 = ponta da frente, 1 = traseira); alturas em metros
TIPOS = {
    "hatch": dict(L=3.90, W=1.72, r=0.30, tw=0.19, soleira=0.30, cintura=0.95, rodas=(0.17, 0.80), farol_z=0.68, lanterna_z=0.92,
                  topo=[(0, 0.60), (0.04, 0.76), (0.25, 0.92), (0.42, 1.44), (0.80, 1.47), (0.95, 1.10), (1.0, 0.86)],
                  para_brisa=(0.255, 0.42), vigia=(0.81, 0.95), laterais=[(0.43, 0.60), (0.635, 0.79)], frisos=[0.43, 0.62]),
    "seda": dict(L=4.50, W=1.75, r=0.31, tw=0.20, soleira=0.30, cintura=0.95, rodas=(0.16, 0.74), farol_z=0.68, lanterna_z=0.86,
                 topo=[(0, 0.60), (0.04, 0.76), (0.27, 0.93), (0.44, 1.42), (0.69, 1.44), (0.84, 1.00), (0.97, 0.97), (1.0, 0.78)],
                 para_brisa=(0.275, 0.44), vigia=(0.70, 0.84), laterais=[(0.45, 0.575), (0.605, 0.73)], frisos=[0.45, 0.59]),
    "suv": dict(L=4.40, W=1.82, r=0.35, tw=0.22, soleira=0.42, cintura=1.06, rodas=(0.17, 0.79), farol_z=0.86, lanterna_z=1.10,
                topo=[(0, 0.80), (0.04, 0.96), (0.24, 1.10), (0.38, 1.62), (0.88, 1.66), (0.97, 1.32), (1.0, 1.02)],
                para_brisa=(0.245, 0.38), vigia=(0.885, 0.97), laterais=[(0.39, 0.58), (0.61, 0.86)], frisos=[0.39, 0.60]),
    "picape": dict(L=5.30, W=1.86, r=0.37, tw=0.24, soleira=0.48, cintura=1.08, rodas=(0.17, 0.76), farol_z=0.92, lanterna_z=1.05,
                   topo=[(0, 0.85), (0.03, 1.00), (0.20, 1.13), (0.32, 1.78), (0.585, 1.80), (0.61, 1.30), (0.985, 1.28), (1.0, 1.05)],
                   para_brisa=(0.205, 0.32), vigia=(0.586, 0.61), laterais=[(0.33, 0.45), (0.475, 0.575)], frisos=[0.33, 0.46],
                   lona=(0.615, 0.985)),
    "furgao": dict(L=5.00, W=1.95, r=0.34, tw=0.22, soleira=0.40, cintura=1.08, rodas=(0.16, 0.77), farol_z=0.90, lanterna_z=1.00,
                   topo=[(0, 0.95), (0.05, 1.10), (0.12, 1.22), (0.26, 2.30), (0.32, 2.42), (0.99, 2.42), (1.0, 2.20)],
                   para_brisa=(0.125, 0.26), vigia=(2.0, 2.0), laterais=[(0.27, 0.355)], frisos=[0.27, 0.36, 0.55]),
    "onibus": dict(L=12.0, W=2.55, r=0.50, tw=0.30, soleira=0.38, cintura=1.45, rodas=(0.17, 0.70), farol_z=0.75, lanterna_z=0.85,
                   topo=[(0, 2.55), (0.006, 2.92), (0.025, 3.06), (0.99, 3.06), (1.0, 2.80)],
                   para_brisa=(0.0, 0.03), vigia=(2.0, 2.0), laterais=[(0.035, 0.985)], frisos=[], portas=[(0.03, 0.11), (0.46, 0.54)], colunas=1.25,
                   linhas=[0.95, 1.28], janela_topo=2.62),
}
NOMES = {"hatch": "hatch compacto", "seda": "sedã", "suv": "SUV", "picape": "picape cabine dupla", "furgao": "furgão de entrega",
         "onibus": "ônibus urbano", "moto": "moto 150 cc"}


def _interp(pts, u):
    u = min(max(u, pts[0][0]), pts[-1][0])
    for (u0, z0), (u1, z1) in zip(pts, pts[1:]):
        if u0 <= u <= u1:
            return z0 + (z1 - z0) * ((u - u0) / max(u1 - u0, 1e-9))
    return pts[-1][1]


def _largura(T, u, n=5.0):
    return T["W"] * (1 - abs(2 * u - 1) ** n) ** (1 / n)


def _fundo(T, u):
    L, r = T["L"], T["r"]; z = T["soleira"] + (0.1 if (u < 0.05 or u > 0.96) else 0.0)
    ra = r + 0.07; x = u * L
    for uw in T["rodas"]:
        d = abs(x - uw * L)
        if d < ra:
            z = max(z, r + math.sqrt(ra * ra - d * d))
    return z


def _secao(T, u):
    """Seção transversal (lista de (y, z)) na posição u: retângulo de cantos arredondados, mais estreito em cima."""
    z0, z1 = _fundo(T, u), _interp(T["topo"], u); a = _largura(T, u) / 2
    cint = min(max(T["cintura"], z0 + 0.06), z1 - 0.04)
    at = a * (0.87 if z1 - cint > 0.3 else 0.97)
    rb = min(0.07, (cint - z0) * 0.45, a * 0.3); rt = min(0.17, (z1 - cint) * 0.45, at * 0.35)
    pts = []

    def arco(cy, cz, r, t0, t1):
        for k in range(4):
            t = math.radians(t0 + (t1 - t0) * k / 3); pts.append((cy + r * math.cos(t), cz + r * math.sin(t)))
    # linhas extras de vértices (sempre o mesmo número por seção, para o loft): faixas de pintura e topo das janelas
    baixo = [min(max(z, z0 + rb + 0.001), cint - 0.001) for z in T.get("linhas", [])]
    jt = T.get("janela_topo")
    jt = None if jt is None else min(max(jt, cint + 0.001), z1 - rt - 0.001)
    arco(-a + rb, z0 + rb, rb, 180, 270); arco(a - rb, z0 + rb, rb, 270, 360)
    pts += [(a, z) for z in sorted(baixo)] + [(a, cint)]
    if jt is not None:
        pts.append((a + (at - a) * (jt - cint) / max(z1 - rt - cint, 1e-6), jt))
    arco(at - rt, z1 - rt, rt, 0, 90); arco(-at + rt, z1 - rt, rt, 90, 180)
    if jt is not None:
        pts.append((-(a + (at - a) * (jt - cint) / max(z1 - rt - cint, 1e-6)), jt))
    pts += [(-a, cint)] + [(-a, z) for z in sorted(baixo, reverse=True)]
    return pts


def _carroceria(nome, T, mats, col, n_secoes=48, uniforme=False):
    """Loft das seções → malha com materiais por face. Frente em x = +L/2."""
    L = T["L"]; bm = bmesh.new(); aneis = []
    if uniforme:   # passo constante (ônibus: as colunas das janelas caem sempre na mesma face)
        us = [0.004 + 0.992 * i / (n_secoes - 1) for i in range(n_secoes)]
    else:          # mais seções nas pontas (onde a forma muda mais)
        us = [0.004 + 0.992 * (0.5 - 0.5 * math.cos(math.pi * i / (n_secoes - 1))) for i in range(n_secoes)]
    for u in us:
        x = L / 2 - u * L
        aneis.append([bm.verts.new((x, y, z)) for y, z in _secao(T, u)])
    n = len(aneis[0])
    for A, B in zip(aneis, aneis[1:]):
        for j in range(n):
            bm.faces.new((A[j], A[(j + 1) % n], B[(j + 1) % n], B[j]))
    bm.faces.new(list(reversed(aneis[0]))); bm.faces.new(aneis[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # material por face: 0 pintura, 1 vidro, 2 lona, 3 faixa, 4 teto
    for f in bm.faces:
        c = f.calc_center_median(); nz, ny = f.normal.z, f.normal.y; u = (L / 2 - c.x) / L
        topo = _interp(T["topo"], u); lado = abs(ny) > 0.6; idx = 0
        if c.z > T["cintura"] + 0.02:
            if lado and c.z < min(topo - 0.035, T.get("janela_topo", 99.0)) and any(a <= u <= b for a, b in T["laterais"]):
                idx = 1
                if T.get("colunas") and (u * L) % T["colunas"] < 0.12:
                    idx = 0                              # colunas entre as janelas do ônibus
            if not lado and (T["para_brisa"][0] <= u <= T["para_brisa"][1] or T["vigia"][0] <= u <= T["vigia"][1]):
                idx = 1
        if "portas" in T and lado and ny < 0 and any(a <= u <= b for a, b in T["portas"]) and T["soleira"] + 0.12 < c.z < T.get("janela_topo", topo - 0.3):
            idx = 1                                      # portas do ônibus (lado direito = −y), de vidro quase até o chão
        if "lona" in T and nz > 0.5 and T["lona"][0] <= u <= T["lona"][1]:
            idx = 2
        if T.get("faixa") and lado and T["faixa"][0] < c.z < T["faixa"][1] and idx == 0:
            idx = 3
        if T.get("teto_cor") and nz > 0.85 and idx == 0:
            idx = 4
        f.material_index = idx; f.smooth = True
    for e in bm.edges:                                   # arestas vivas (> 35°) continuam vivas no sombreamento suave
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(35):
            e.smooth = False
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    o = bpy.data.objects.new(nome, me); col.objects.link(o); o["suspenso"] = True
    return o


def _roda_malha(r, tw, estilo):
    """Pneu (cilindro com ombro arredondado) + aro com 5 raios + cubo. Eixo em y. Malha compartilhada por chave."""
    nome = f"proto_roda_{r:.2f}_{tw:.2f}_{estilo}"
    me = bpy.data.meshes.get(nome)
    if me is not None:
        return me
    bm = bmesh.new()

    def cil(raio, larg, idx, seg=28, chanfro=0.0):
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=raio, radius2=raio, depth=larg)
        vs = g["verts"]
        for v in vs:
            v.co = Vector((v.co.x, v.co.z, v.co.y))        # eixo z → eixo y
        fs = list({f for v in vs for f in v.link_faces})
        for f in fs:
            f.material_index = idx; f.smooth = True
        if chanfro > 0:
            es = [e for e in {e for v in vs for e in v.link_edges} if e.calc_face_angle(0) > 1.0]
            bmesh.ops.bevel(bm, geom=es, offset=chanfro, segments=3, affect="EDGES")
    cil(r, tw, 0, 32, chanfro=min(0.06, r * 0.18))
    cil(r * 0.64, tw + 0.012, 1, 28)
    cil(r * 0.5, tw + 0.016, 2, 24)
    for k in range(5):
        a = 2 * math.pi * k / 5
        g = bmesh.ops.create_cube(bm, size=1.0)
        for v in g["verts"]:
            x, y, z = v.co.x * r * 0.44, v.co.y * (tw + 0.026), v.co.z * r * 0.11
            x += r * 0.28
            v.co = Vector((x * math.cos(a) - z * math.sin(a), y, x * math.sin(a) + z * math.cos(a)))
        for f in {f for v in g["verts"] for f in v.link_faces}:
            f.material_index = 1
    cil(r * 0.13, tw + 0.03, 1, 16)
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free()
    aro = {"prata": M.pintura("#c9ccd1", rug=0.25, metal=0.9), "preto": M.pintura("#2a2c30", rug=0.35, metal=0.6),
           "aco": M.pintura("#8d9299", rug=0.4, metal=0.7)}[estilo]
    for m in (M.borracha("#1d1d1f"), aro, M.pintura("#18191b", rug=0.7)):
        me.materials.append(m)
    return me


def _rodas(nome, T, col, estilo):
    me = _roda_malha(T["r"], T["tw"], estilo); L, W = T["L"], T["W"]; out = []
    for i, uw in enumerate(T["rodas"]):
        x = L / 2 - uw * L
        for s in (-1, 1):
            o = bpy.data.objects.new(f"{nome}_roda{i}{'e' if s > 0 else 'd'}", me); col.objects.link(o)
            o.location = (x, s * (W / 2 - T["tw"] / 2 - 0.03), T["r"]); out.append(o)      # pneu toca o chão (z = 0)
        # caixa de roda escura (sem ela, vê-se através do arco)
        ra = T["r"] + 0.07
        G.caixa(f"{nome}_caixaroda{i}", (x - ra, -W / 2 + T["tw"] + 0.06, T["r"]), (x + ra, W / 2 - T["tw"] - 0.06, T["r"] + ra - 0.02),
                M.pintura("#121214", rug=0.9), col)["suspenso"] = True
    return out


def _detalhes_carro(nome, T, col, rng, pint, farois):
    L, W = T["L"], T["W"]; esc = M.pintura("#232528", rug=0.55); cromo = M.pintura("#c9ccd1", rug=0.2, metal=0.9)
    plast = M.pintura("#2b2d31", rug=0.6) if rng.random() < 0.6 else pint
    lf = M.lente("#f4f2ec", 18.0 if farois else 0.0); lt = M.lente("#c4161c", 6.0 if farois else 0.0)
    xs = L / 2
    for c0, c1, m, t in (((xs - 0.12, -0.46 * W, T["soleira"] + 0.02), (xs + 0.03, 0.46 * W, T["soleira"] + 0.22), plast, "pchoque_f"),
                         ((-xs - 0.03, -0.46 * W, T["soleira"] + 0.04), (-xs + 0.12, 0.46 * W, T["soleira"] + 0.24), plast, "pchoque_t"),
                         ((xs - 0.05, -0.24 * W, T["farol_z"] - 0.13), (xs + 0.012, 0.24 * W, T["farol_z"] - 0.03), esc, "grade")):
        G.caixa(f"{nome}_{t}", c0, c1, m, col, chanfro=0.03)["suspenso"] = True
    for s in (-1, 1):
        o = G.caixa(f"{nome}_farol{s}", (xs - 0.1, s * 0.30 * W - 0.15, T["farol_z"] - 0.06), (xs - 0.005, s * 0.30 * W + 0.15, T["farol_z"] + 0.06), lf, col, chanfro=0.02)
        o["suspenso"] = True; o.lightgroup = "artificial" if farois else ""
        o = G.caixa(f"{nome}_lanterna{s}", (-xs + 0.005, s * 0.36 * W - 0.13, T["lanterna_z"] - 0.07), (-xs + 0.09, s * 0.36 * W + 0.13, T["lanterna_z"] + 0.07), lt, col, chanfro=0.02)
        o["suspenso"] = True; o.lightgroup = "artificial" if farois else ""
        # retrovisor na base da coluna A
        xa = L / 2 - T["para_brisa"][0] * L - 0.12; ya = _largura(T, T["para_brisa"][0] + 0.03) / 2
        G.caixa(f"{nome}_retro{s}", (xa - 0.1, s * ya - 0.05 if s > 0 else s * (ya + 0.17), T["cintura"] + 0.02),
                (xa + 0.06, s * (ya + 0.17) if s > 0 else s * ya + 0.05, T["cintura"] + 0.15), plast, col, chanfro=0.02)["suspenso"] = True
        # frisos de porta e maçanetas
        for uf in T["frisos"]:
            yb = _largura(T, uf) / 2 + 0.002
            G.caixa(f"{nome}_friso{s}_{uf}", (L / 2 - uf * L - 0.004, s * yb - 0.004, T["soleira"] + 0.08), (L / 2 - uf * L + 0.004, s * yb + 0.004, T["cintura"] - 0.01), esc, col)["suspenso"] = True
            G.caixa(f"{nome}_maca{s}_{uf}", (L / 2 - uf * L - 0.2, s * yb - 0.012, T["cintura"] - 0.14), (L / 2 - uf * L - 0.06, s * yb + 0.012, T["cintura"] - 0.1), cromo, col)["suspenso"] = True
    # placas Mercosul EM BRANCO (sem caracteres: não reproduz placa real)
    branco = M.pintura("#f4f3ef", rug=0.4); azul = M.pintura("#1d4f9c", rug=0.4)
    for s, x in ((1, xs + 0.03), (-1, -xs - 0.03)):
        z = T["soleira"] + 0.06 if s > 0 else T["lanterna_z"] - 0.28
        x0, x1 = sorted((x, x + s * 0.006))
        G.caixa(f"{nome}_placa{s}", (x0, -0.2, z), (x1, 0.2, z + 0.13), branco, col)["suspenso"] = True
        x0, x1 = sorted((x + s * 0.006, x + s * 0.008))
        G.caixa(f"{nome}_placab{s}", (x0, -0.2, z + 0.1), (x1, 0.2, z + 0.13), azul, col)["suspenso"] = True
    if farois:   # faróis acesos iluminam o chão à frente
        for s in (-1, 1):
            LZ.luz_ponto(f"{nome}_luzfarol{s}", (xs + 0.05, s * 0.30 * W, T["farol_z"]), 220, "#fff4e0", "artificial", raio=0.05,
                         tipo="SPOT", alvo=(xs + 8.0, s * 0.30 * W, 0.0), angulo=55)


def _carro(nome, tipo, col, rng, p):
    T = dict(TIPOS[tipo])
    if p.get("cor"):
        cor, metal = p["cor"], p.get("metal", 0.4)
    else:
        cor, _, metal = rng.choices(CORES, weights=[c[1] for c in CORES])[0]
    pint = M.pintura_automotiva(cor, metal, sujeira=rng.uniform(0.15, 0.45))
    vidro = M.vidro("#1c2630", 0.05); lona = M.pintura("#1b1c1e", rug=0.75)
    _carroceria(f"{nome}_carroceria", T, [pint, vidro, lona, pint, pint], col)
    _rodas(nome, T, col, p.get("aro") or rng.choice(["prata", "preto", "aco"]))
    _detalhes_carro(nome, T, col, rng, pint, p.get("farois", False))
    if tipo == "picape":   # santantônio atrás da cabine
        x = T["L"] / 2 - 0.615 * T["L"] - 0.08
        for s in (-1, 1):
            G.cilindro_eixo(f"{nome}_santo{s}", (x, s * 0.78, 1.28), (x, s * 0.78, 1.62), 0.03, M.pintura("#2a2c30", rug=0.4, metal=0.6), col)["suspenso"] = True
        G.cilindro_eixo(f"{nome}_santot", (x, -0.78, 1.62), (x, 0.78, 1.62), 0.03, M.pintura("#2a2c30", rug=0.4, metal=0.6), col)["suspenso"] = True
    return T


def _onibus(nome, col, rng, p):
    T = dict(TIPOS["onibus"])
    cores = p.get("cores") or rng.choice([("#e9e6dc", "#1d6fb8"), ("#e9e6dc", "#2f8f4e"), ("#f2c230", "#2b2e33"), ("#e9e6dc", "#c8231f"), ("#d9702c", "#ede6d8")])
    T["faixa"] = (0.95, 1.28); T["teto_cor"] = True
    pint = M.pintura_automotiva(cores[0], 0.2, sujeira=0.5); faixa = M.pintura_automotiva(cores[1], 0.2, sujeira=0.4)
    vidro = M.vidro("#1a242c", 0.05)
    _carroceria(f"{nome}_carroceria", T, [pint, vidro, pint, faixa, M.pintura_automotiva("#f1efe8", 0.1, 0.2)], col, n_secoes=97, uniforme=True)
    _rodas(nome, T, col, "aco")
    farois = p.get("farois", False); L, W = T["L"], T["W"]; xs = L / 2; esc = M.pintura("#232528", rug=0.55)
    lf = M.lente("#f4f2ec", 18.0 if farois else 0.0); lt = M.lente("#c4161c", 6.0 if farois else 0.0)
    G.caixa(f"{nome}_pchoque_f", (xs - 0.1, -0.48 * W, 0.32), (xs + 0.06, 0.48 * W, 0.6), esc, col, chanfro=0.03)["suspenso"] = True
    G.caixa(f"{nome}_pchoque_t", (-xs - 0.06, -0.48 * W, 0.32), (-xs + 0.1, 0.48 * W, 0.6), esc, col, chanfro=0.03)["suspenso"] = True
    for s in (-1, 1):
        o = G.caixa(f"{nome}_farol{s}", (xs - 0.03, s * 0.38 * W - 0.16, T["farol_z"] - 0.07), (xs + 0.012, s * 0.38 * W + 0.16, T["farol_z"] + 0.07), lf, col, chanfro=0.02)
        o["suspenso"] = True; o.lightgroup = "artificial" if farois else ""
        o = G.caixa(f"{nome}_lanterna{s}", (-xs - 0.012, s * 0.4 * W - 0.1, 1.0), (-xs + 0.02, s * 0.4 * W + 0.1, 1.6), lt, col, chanfro=0.02)
        o["suspenso"] = True; o.lightgroup = "artificial" if farois else ""
        # retrovisores grandes em haste
        G.cilindro_eixo(f"{nome}_haste{s}", (xs - 0.05, s * W / 2, 2.3), (xs + 0.35, s * (W / 2 + 0.25), 2.25), 0.02, esc, col)["suspenso"] = True
        G.caixa(f"{nome}_retro{s}", (xs + 0.3, s * (W / 2 + 0.25) - 0.06, 1.85), (xs + 0.4, s * (W / 2 + 0.25) + 0.06, 2.25), esc, col, chanfro=0.02)["suspenso"] = True
    # letreiro de itinerário (palavra comum + número de linha) acima do para-brisa
    G.caixa(f"{nome}_letreiro", (xs - 0.02, -0.95, 2.66), (xs + 0.015, 0.95, 2.92), M.pintura("#111214", rug=0.4), col)["suspenso"] = True
    amb = M.emissor("#ffb02e", 4.0)
    for corpo, y, tam in (("101", -0.7, 0.17), ("CENTRO", 0.15, 0.17)):
        t = G.texto(f"{nome}_itin_{corpo}", corpo, (xs + 0.017, y, 2.79), tam, amb, col, rot=(math.radians(90), 0, math.radians(90)))
        t.lightgroup = "artificial"
    branco = M.pintura("#f4f3ef", rug=0.4)
    G.caixa(f"{nome}_placa", (xs + 0.06, -0.2, 0.62), (xs + 0.066, 0.2, 0.75), branco, col)["suspenso"] = True
    if farois:
        for s in (-1, 1):
            LZ.luz_ponto(f"{nome}_luzfarol{s}", (xs + 0.1, s * 0.38 * W, T["farol_z"]), 260, "#fff4e0", "artificial", raio=0.05,
                         tipo="SPOT", alvo=(xs + 10.0, s * 0.38 * W, 0.0), angulo=60)
    return T


def _moto(nome, col, rng, p):
    """Moto de rua (~150 cc) estacionada no descanso lateral. Frente em +x."""
    cor = p.get("cor") or rng.choice(["#c8231f", "#1d1f22", "#1f4e8c", "#e9e9e6", "#2f6b4f"])
    pint = M.pintura_automotiva(cor, 0.4, 0.3); esc = M.pintura("#232528", rug=0.5); cromo = M.pintura("#c9ccd1", rug=0.2, metal=0.9)
    r = 0.30; me = _roda_malha(r, 0.11, "preto")
    for nm, x in (("rodaf", 0.68), ("rodat", -0.66)):
        o = bpy.data.objects.new(f"{nome}_{nm}", me); col.objects.link(o); o.location = (x, 0, r)
    # quadro, garfo, balança
    for a, b, rr in (((0.68, 0, r), (0.48, 0, 0.98), 0.03), ((-0.66, 0, r), (-0.05, 0, 0.42), 0.035), ((0.45, 0, 0.92), (-0.1, 0, 0.62), 0.04),
                     ((-0.1, 0, 0.62), (-0.05, 0, 0.42), 0.04)):
        G.cilindro_eixo(f"{nome}_tubo{a[0]:.2f}{b[0]:.2f}", a, b, rr, esc, col)["suspenso"] = True
    tanque = G.esfera(f"{nome}_tanque", (0, 0, 0), 0.22, pint, col, sub=3); tanque.scale = (1.35, 0.85, 0.7); tanque.location = (0.22, 0, 0.9); tanque["suspenso"] = True
    G.caixa(f"{nome}_banco", (-0.62, -0.13, 0.82), (0.05, 0.13, 0.92), M.pintura("#18191b", rug=0.8), col, chanfro=0.04)["suspenso"] = True
    G.caixa(f"{nome}_rabeta", (-0.78, -0.11, 0.78), (-0.4, 0.11, 0.86), pint, col, chanfro=0.03)["suspenso"] = True
    G.caixa(f"{nome}_motor", (-0.15, -0.14, 0.32), (0.25, 0.14, 0.64), M.pintura("#4a4d52", rug=0.5, metal=0.6), col, chanfro=0.03)["suspenso"] = True
    G.cilindro_eixo(f"{nome}_escap", (0.0, -0.16, 0.38), (-0.75, -0.17, 0.5), 0.045, cromo, col)["suspenso"] = True
    G.cilindro_eixo(f"{nome}_guidao", (0.5, -0.36, 1.08), (0.5, 0.36, 1.08), 0.016, cromo, col)["suspenso"] = True
    G.cilindro_eixo(f"{nome}_mesa", (0.48, 0, 0.98), (0.5, 0, 1.08), 0.03, esc, col)["suspenso"] = True
    farol = G.esfera(f"{nome}_farol", (0.6, 0, 1.0), 0.09, M.lente("#f4f2ec", 18.0 if p.get("farois") else 0.0), col, sub=2); farol["suspenso"] = True
    G.caixa(f"{nome}_paralama", (0.55, -0.07, 0.64), (0.85, 0.07, 0.66), pint, col)["suspenso"] = True
    G.caixa(f"{nome}_lanterna", (-0.8, -0.06, 0.8), (-0.77, 0.06, 0.86), M.lente("#c4161c", 6.0 if p.get("farois") else 0.0), col)["suspenso"] = True
    G.caixa(f"{nome}_placa", (-0.84, -0.1, 0.62), (-0.835, 0.1, 0.75), M.pintura("#f4f3ef", rug=0.4), col)["suspenso"] = True
    G.cilindro_eixo(f"{nome}_descanso", (-0.05, 0.12, 0.4), (0.02, 0.32, 0.0), 0.015, esc, col)["suspenso"] = True
    return {"L": 2.0, "W": 0.75, "r": r}


# ------------------------------------------------------------------ montagem no mundo
def construir_veiculo(tipo, nome, col, rng, x, y, rot_graus, p):
    raiz = bpy.data.objects.new(nome, None); col.objects.link(raiz)
    antes = set(col.objects); luzes0 = {o.name for o in bpy.data.objects if o.type == "LIGHT"}
    if tipo == "onibus":
        T = _onibus(nome, col, rng, p)
    elif tipo == "moto":
        T = _moto(nome, col, rng, p)
    else:
        T = _carro(nome, tipo, col, rng, p)
    for o in col.objects:
        if o not in antes and o.parent is None and o is not raiz:
            o.parent = raiz
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.name not in luzes0 and o.parent is None:
            o.parent = raiz
    raiz.location = (x, y, p.get("z", 0.0)); raiz.rotation_euler = (math.radians(p.get("inclinacao", -5.0 if tipo == "moto" else 0.0)), 0, math.radians(rot_graus))
    raiz["veiculo"] = tipo; raiz["dims"] = [T["L"], T["W"]]
    return raiz, T


@componente("veiculo")
def veiculo(ctx, p, rng, col):
    """Um veículo: tipo, x, y, rot_graus (0 = frente para +x), cor/metal opcionais, farois (bool)."""
    construir_veiculo(p["tipo"], p.get("nome", f"{p['tipo']}_{p['x']}_{p['y']}"), col, rng, p["x"], p["y"], p.get("rot_graus", 0.0), p)


@componente("estacionamento")
def estacionamento(ctx, p, rng, col):
    """Carros parados junto ao meio-fio (paralelos), por semente. params: lado (±1), y0, y1, largura_pista (7),
    ocupacao (0,7), evitar [[y_a, y_b], …] (esquina, hidrante, garagem), tipos {tipo: peso}. Mão de direção brasileira:
    do lado +x os carros olham para +y; do lado −x, para −y."""
    lado = p.get("lado", 1); Lp = p.get("largura_pista", 7.0); y = p["y0"]
    tipos = p.get("tipos", {"hatch": 0.35, "seda": 0.25, "suv": 0.2, "picape": 0.1, "furgao": 0.1})
    evitar = p.get("evitar", []); nome = p.get("nome", f"estac_{lado}"); i = 0
    while y < p["y1"]:
        tipo = rng.choices(list(tipos), weights=list(tipos.values()))[0]; T = TIPOS[tipo]; Lv = T["L"]
        y_c = y + Lv / 2
        livre = y + Lv <= p["y1"] and not any(a - 0.3 < y_c + d < b + 0.3 for a, b in evitar for d in (-Lv / 2, 0, Lv / 2))
        if livre and rng.random() < p.get("ocupacao", 0.7):
            x = lado * (Lp / 2 - 0.12 - T["W"] / 2)
            construir_veiculo(tipo, f"{nome}_{i}_{tipo}", col, rng, x, y_c, 90.0 if lado > 0 else -90.0, {})
            i += 1
        y += Lv + rng.uniform(0.7, 1.8)
