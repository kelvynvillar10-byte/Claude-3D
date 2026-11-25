"""Cenografia — kit de AMBIENTAÇÃO (E5): árvores, vegetação, mobiliário urbano, comércio e espalhamento por regras.

Árvores (tronco ramificado por algoritmo; copa em AGLOMERADOS irregulares, não esferas):
- frondosa   copa larga e densa, tipo árvore de calçada (oiti/fícus genérico)
- ipe        tronco alto, galhos esparsos, copa florida (amarela ou rosa) com poucas folhas
- palmeira   estipe levemente curvo + coroa de folhas pendentes
Aglomerados de folhas = poucas malhas-protótipo deformadas por ruído, INSTANCIADAS (escala, giro e cor por objeto).
Vegetação: arbusto, vaso com planta. Mobiliário: banco de praça, contêiner de lixo, sacos de lixo, ponto de ônibus
(abrigo), banca de revistas, cones, bicicleta. Comércio: mesas de bar com cadeiras plásticas, engradados, bancada de
frutas. Textos só com palavras comuns ("ÔNIBUS", "BANCA").

Regras de espalhamento (componentes 'arborizacao', 'ambientacao', 'mesas_bar'):
- nada flutuando: cada peça é apoiada na superfície real (raio para baixo);
- nada atravessando: depois de montada, a peça é testada contra a geometria vizinha (BVH, triângulos reais); se
  atravessar algo (fachada, marquise, toldo, varanda, poste, carro…), é removida e o lugar é sorteado de novo;
- áreas livres (portas, garagens, faixas de pedestre, o lugar do Heitor) e distância mínima entre peças.
Cada peça colocada recebe o rótulo "grupo_amb" (o QA da cena confere "nada atravessando" de novo, no fim).
"""
import math
import bpy, bmesh
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree
from cenografia.nucleo.registro import componente
from cenografia.nucleo import geometria as G, materiais as M

FOLHAS = {"frondosa": ["#3f6b2e", "#4a7a34", "#56853a", "#355f29"], "ipe_amarelo": ["#f2c230", "#e8b21f", "#f6d04a"],
          "ipe_rosa": ["#e07fb0", "#d46aa0", "#ec98c2"], "palmeira": ["#5a8a3a", "#4f7d33"], "arbusto": ["#4f7a3a", "#5b8540", "#466e35"]}
TEXTOS_KIT = ["ÔNIBUS", "BANCA"]


# ------------------------------------------------------------------ infraestrutura
def _raiz(nome, col, loc, rot_z=0.0):
    e = bpy.data.objects.new(nome, None); col.objects.link(e); e.location = loc; e.rotation_euler = (0, 0, rot_z)
    return e


def _adotar(col, raiz, antes, grupo=True):
    """Objetos novos em 'col' viram filhos de 'raiz' e recebem o rótulo do grupo (para o teste de colisão)."""
    for o in col.objects:
        if o not in antes and o is not raiz:
            if o.parent is None:
                o.parent = raiz
            if grupo:
                o["grupo_amb"] = raiz.name
    raiz["grupo_amb"] = raiz.name; raiz["ambientacao"] = True


def _remover(raiz):
    for o in list(raiz.children_recursive) + [raiz]:
        bpy.data.objects.remove(o, do_unlink=True)


def _aglomerado(variante):
    """Malha-protótipo de um aglomerado de folhas: icosfera deformada por ruído fractal (lóbulos irregulares)."""
    nome = f"proto_aglom_{variante}"
    me = bpy.data.meshes.get(nome)
    if me is not None:
        return me
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    off = Vector((variante * 7.31, variante * 3.17, variante * 5.73))
    for v in bm.verts:
        n = v.co.normalized()
        d = 0.34 * noise.fractal(n * 1.5 + off, 0.8, 2.0, 3) + 0.035 * noise.noise(n * 5.0 + off)
        v.co = n * (1.0 + d)
        v.co.z *= 0.78                                   # aglomerados mais largos que altos
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free(); me.materials.append(None)
    return me


def _inst(nome, me, loc, escala, rot, mat, col):
    o = bpy.data.objects.new(nome, me); col.objects.link(o); o.location = loc; o.scale = escala; o.rotation_euler = rot
    o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = mat; o["suspenso"] = True
    return o


def _cone(bm, p0, p1, r0, r1, seg=8):
    d = Vector(p1) - Vector(p0); L = d.length
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=L)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    for v in g["verts"]:
        v.co = q @ Vector((v.co.x, v.co.y, v.co.z + L / 2)) + Vector(p0)
    for f in {f for v in g["verts"] for f in v.link_faces}:
        f.smooth = True


def _galhos(bm, p0, direcao, comp, raio, nivel, rng, pontas, abertura, ramos, meios=None):
    p1 = Vector(p0) + direcao * comp
    _cone(bm, p0, p1, raio, raio * 0.68)
    if meios is not None and nivel == 1:
        meios.append((Vector(p0).lerp(p1, 0.6), direcao))
    if nivel == 0:
        pontas.append((p1, direcao)); return
    n = rng.randint(*ramos)
    base_az = rng.uniform(0, 2 * math.pi)
    for k in range(n):
        az = base_az + 2 * math.pi * k / n + rng.uniform(-0.4, 0.4)
        lateral = Vector((math.cos(az), math.sin(az), 0.0))
        d = (direcao * math.cos(abertura) + lateral * math.sin(abertura)).normalized()
        d.z = max(d.z, 0.15); d.normalize()
        _galhos(bm, p1, d, comp * rng.uniform(0.62, 0.78), raio * 0.62, nivel - 1, rng, pontas, abertura * 0.9, ramos, meios)


# ------------------------------------------------------------------ árvores
def arvore(nome, col, rng, especie="frondosa", escala=1.0, flor="amarelo"):
    """Árvore na origem (base do tronco em z = 0). Retorna a altura aproximada."""
    casca = M.pintura(rng.choice(["#5a4636", "#4d3b2e", "#6b5442"]), rug=0.9, desgaste=0.6)
    if especie == "palmeira":
        return _palmeira(nome, col, rng, escala, casca)
    bm = bmesh.new(); pontas = []; meios = []
    if especie == "ipe":
        h_t, r_t, abertura, nivel, ramos, comp = 2.8, 0.16, math.radians(30), 3, (2, 3), 1.6
    else:
        h_t, r_t, abertura, nivel, ramos, comp = 1.9, 0.2, math.radians(46), 3, (3, 4), 1.45
    h_t *= escala; r_t *= escala; comp *= escala
    incl = Vector((rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), 1.0)).normalized()
    _cone(bm, (0, 0, 0), incl * h_t, r_t * 1.25, r_t, seg=10)
    _galhos(bm, incl * h_t, incl, comp, r_t, nivel, rng, pontas, abertura, ramos, meios)
    me = bpy.data.meshes.new(nome + "_tronco"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(me.name, me); o.data.materials.append(casca); col.objects.link(o)
    # copa: aglomerados nas pontas (e alguns no meio, para não ficar oca)
    cores = FOLHAS["frondosa"] if especie == "frondosa" else FOLHAS["ipe_" + flor]
    tam = (0.75, 1.25) if especie == "frondosa" else (0.5, 0.9)
    i = 0; topo = 0.0
    alvos = pontas + (meios if especie == "frondosa" else meios[: len(meios) // 2])   # meio dos galhos: copa cheia, não oca
    for p, d in alvos:
        for _ in range(1 if especie == "ipe" else rng.randint(1, 2)):
            s = rng.uniform(*tam) * escala
            loc = p + d * s * 0.3 + Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(-0.1, 0.25))) * escala
            cor = rng.choice(cores) if (especie == "frondosa" or rng.random() < 0.85) else rng.choice(FOLHAS["frondosa"])
            _inst(f"{nome}_copa{i}", _aglomerado(rng.randint(0, 3)), loc, (s, s, s), (0, 0, rng.uniform(0, 6.28)), M.folhagem(cor, round(1.0 / max(s, 0.3), 1)), col)
            topo = max(topo, loc.z + s * 0.78); i += 1
    return topo


def _palmeira(nome, col, rng, escala, casca):
    bm = bmesh.new(); h = rng.uniform(6.0, 8.0) * escala; n = 6
    curva = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized() * rng.uniform(0.3, 0.8) * escala
    pts = [Vector((0, 0, 0)) + curva * (i / n) ** 2 + Vector((0, 0, h * i / n)) for i in range(n + 1)]
    for i in range(n):
        _cone(bm, pts[i], pts[i + 1], 0.2 * escala * (1 - 0.25 * i / n), 0.2 * escala * (1 - 0.25 * (i + 1) / n), seg=10)
    me = bpy.data.meshes.new(nome + "_estipe"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(me.name, me); o.data.materials.append(M.pintura("#8a7a62", rug=0.9, desgaste=0.7)); col.objects.link(o)
    topo = pts[-1]; folha = M.folhagem(rng.choice(FOLHAS["palmeira"]), 2.0)
    for k in range(rng.randint(10, 13)):   # folhas: tiras arqueadas e pendentes, mais largas no meio
        az = 2 * math.pi * k / 12 + rng.uniform(-0.2, 0.2); L = rng.uniform(2.2, 3.0) * escala; elev = rng.uniform(0.2, 0.7)
        bmf = bmesh.new(); m = 10; lin_e, lin_d = [], []
        d = Vector((math.cos(az), math.sin(az), 0)); lado = Vector((-d.y, d.x, 0))
        for i in range(m + 1):
            t = i / m; c = topo + d * (L * t) + Vector((0, 0, L * (elev * t - 0.9 * t * t)))
            w = 0.38 * escala * math.sin(math.pi * min(1.0, t * 1.1)) + 0.02
            dobra = Vector((0, 0, -0.08 * escala))
            lin_e.append(bmf.verts.new(c + lado * w + dobra)); lin_d.append(bmf.verts.new(c - lado * w + dobra))
            if i:
                bmf.faces.new((lin_e[i - 1], lin_e[i], lin_d[i], lin_d[i - 1]))
        mef = bpy.data.meshes.new(f"{nome}_folha{k}"); bmf.to_mesh(mef); bmf.free()
        of = bpy.data.objects.new(mef.name, mef); of.data.materials.append(folha); col.objects.link(of); of["suspenso"] = True
        for p in of.data.polygons:
            p.use_smooth = True
    return topo.z + 0.5


def arbusto(nome, col, rng, raio=0.6):
    for i in range(rng.randint(3, 5)):
        s = raio * rng.uniform(0.55, 0.85); a = rng.uniform(0, 6.28); dd = rng.uniform(0, raio * 0.5)
        _inst(f"{nome}_b{i}", _aglomerado(rng.randint(0, 3)), (dd * math.cos(a), dd * math.sin(a), s * 0.62), (s, s, s), (0, 0, a),
              M.folhagem(rng.choice(FOLHAS["arbusto"]), round(1.0 / max(s, 0.3), 1)), col)
    return raio * 1.4


# ------------------------------------------------------------------ mobiliário e comércio (na origem; frente para −x)
def _caixa(nome, c0, c1, mat, col, chanfro=0.0, suspenso=True):
    o = G.caixa(nome, c0, c1, mat, col, chanfro=chanfro)
    if suspenso:
        o["suspenso"] = True
    return o


def _toro(nome, R, r, mat, col, seg=32, seg_r=8):
    """Toro no plano xz (roda de bicicleta)."""
    bm = bmesh.new(); vs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; c = Vector((R * math.cos(a), 0.0, R * math.sin(a))); radial = c.normalized()
        anel = []
        for j in range(seg_r):
            b = 2 * math.pi * j / seg_r
            anel.append(bm.verts.new(c + radial * (r * math.cos(b)) + Vector((0, r * math.sin(b), 0))))
        vs.append(anel)
    for i in range(seg):
        A, B = vs[i], vs[(i + 1) % seg]
        for j in range(seg_r):
            f = bm.faces.new((A[j], A[(j + 1) % seg_r], B[(j + 1) % seg_r], B[j])); f.smooth = True
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nome, me); o.data.materials.append(mat); col.objects.link(o); o["suspenso"] = True
    return o


def banco_praca(nome, col, rng):
    conc = M.concreto("#b8b0a2", placa_m=(0.6, 0.4)); mad = M.madeira(rng.choice(["#8a5a3b", "#7a4a2a"]))
    for s in (-0.7, 0.7):
        _caixa(f"{nome}_pe{s}", (-0.22, s - 0.07, 0.0), (0.22, s + 0.07, 0.42), conc, col, 0.015, suspenso=False)
    for i in range(4):
        _caixa(f"{nome}_ripa{i}", (-0.24 + i * 0.12, -0.95, 0.42), (-0.24 + i * 0.12 + 0.1, 0.95, 0.47), mad, col, 0.008)
    for i in range(2):
        _caixa(f"{nome}_enc{i}", (0.22, -0.95, 0.58 + i * 0.16), (0.26, 0.95, 0.7 + i * 0.16), mad, col, 0.008)
    for s in (-0.7, 0.7):
        _caixa(f"{nome}_sup{s}", (0.2, s - 0.04, 0.42), (0.27, s + 0.04, 0.9), conc, col, 0.01)
    return 0.3


def conteiner(nome, col, rng):
    cor = rng.choice(["#2f7d3a", "#3a3d42", "#d9702c", "#1d4f9c"]); plast = M.pintura(cor, rug=0.55, desgaste=0.5)
    _caixa(f"{nome}_corpo", (-0.55, -0.62, 0.12), (0.55, 0.62, 1.15), plast, col, 0.04)
    _caixa(f"{nome}_tampa", (-0.6, -0.66, 1.15), (0.6, 0.66, 1.22), plast, col, 0.03)
    for sx in (-0.42, 0.42):
        for sy in (-0.5, 0.5):
            G.cilindro_eixo(f"{nome}_rod{sx}{sy}", (sx, sy - 0.03, 0.06), (sx, sy + 0.03, 0.06), 0.06, M.borracha(), col)
    return 0.9


def sacos_lixo(nome, col, rng):
    preto = M.pintura("#18191b", rug=0.25)
    for i in range(rng.randint(2, 4)):
        s = rng.uniform(0.22, 0.32); a = rng.uniform(0, 6.28); dd = rng.uniform(0, 0.25)
        o = _inst(f"{nome}_s{i}", _aglomerado(rng.randint(0, 3)), (dd * math.cos(a), dd * math.sin(a), s * 0.7), (s, s * 0.9, s * 1.1),
                  (0, 0, a), preto, col)
    return 0.55


def ponto_onibus(nome, col, rng):
    metal = M.pintura("#3d4148", rug=0.45, metal=0.6); vidro = M.vidro("#2a3a44", 0.05)
    for y in (-1.5, 1.5):
        for x in (-0.55, 0.55):
            G.cilindro_eixo(f"{nome}_col{x}{y}", (x, y, 0.0), (x, y, 2.45), 0.04, metal, col)
    _caixa(f"{nome}_teto", (-0.85, -1.7, 2.45), (0.75, 1.7, 2.55), M.pintura("#e9e6dc", rug=0.4), col, 0.02)
    _caixa(f"{nome}_fundo", (0.5, -1.45, 0.25), (0.53, 1.45, 2.3), vidro, col)
    _caixa(f"{nome}_banco", (0.1, -1.3, 0.45), (0.5, 1.3, 0.5), metal, col, 0.01)
    _caixa(f"{nome}_placa", (-0.62, 1.42, 1.9), (-0.6, 1.62, 2.35), M.pintura("#1d4f9c", rug=0.4), col)
    G.texto(f"{nome}_txt", "ÔNIBUS", (-0.625, 1.52, 2.12), 0.065, M.pintura("#f4f2ec", rug=0.5), col,
            rot=(math.radians(90), 0, math.radians(-90)))
    return 1.9


def banca(nome, col, rng):
    verde = M.pintura(rng.choice(["#2f6b4f", "#1d4f9c", "#c8231f"]), rug=0.5, desgaste=0.4)
    _caixa(f"{nome}_corpo", (-0.9, -1.4, 0.0), (0.9, 1.4, 2.3), verde, col, 0.02, suspenso=False)
    _caixa(f"{nome}_teto", (-1.4, -1.6, 2.3), (1.1, 1.6, 2.4), verde, col, 0.02)
    _caixa(f"{nome}_vitrine", (-0.92, -1.2, 0.5), (-0.9, 1.2, 1.9), M.emissor("#fff1d6", 0.8), col).lightgroup = "artificial"
    for i in range(12):   # revistas penduradas (retângulos coloridos, sem texto)
        y = -1.1 + (i % 6) * 0.37; z = 1.05 + (i // 6) * 0.45
        _caixa(f"{nome}_rev{i}", (-0.935, y, z), (-0.925, y + 0.28, z + 0.36), M.pintura(rng.choice(["#c8231f", "#e3a12f", "#1d4f9c", "#4fae9c", "#e8806c", "#f4f2ec"]), rug=0.5), col)
    _caixa(f"{nome}_letreiro", (-1.0, -0.8, 2.42), (-0.95, 0.8, 2.72), M.pintura("#f4f2ec", rug=0.4), col)
    G.texto(f"{nome}_txt", "BANCA", (-1.005, 0.0, 2.57), 0.2, M.pintura("#2b2e33", rug=0.5), col, rot=(math.radians(90), 0, math.radians(-90)))
    return 1.7


def cones(nome, col, rng):
    lar = M.pintura("#e8641f", rug=0.5); bra = M.pintura("#f4f2ec", rug=0.5)
    for i in range(rng.randint(2, 3)):
        x, y = 0.0, i * 0.7
        _caixa(f"{nome}_base{i}", (x - 0.19, y - 0.19, 0.0), (x + 0.19, y + 0.19, 0.03), M.pintura("#18191b", rug=0.7), col, suspenso=False)
        G.cilindro(f"{nome}_c{i}", (x, y, 0.03), 0.14, 0.62, lar, col, raio_topo=0.025, lados=20)["suspenso"] = True
        G.cilindro(f"{nome}_f{i}", (x, y, 0.33), 0.088, 0.1, bra, col, raio_topo=0.072, lados=20)["suspenso"] = True
    return 0.5


def bicicleta(nome, col, rng):
    cor = M.pintura(rng.choice(["#c8231f", "#1d4f9c", "#2b2e33", "#2f7d3a", "#e3a12f"]), rug=0.4, metal=0.4); pneu = M.borracha()
    for x in (-0.52, 0.52):
        o = _toro(f"{nome}_aro{x}", 0.32, 0.022, pneu, col); o.location = (x, 0, 0.342)
    for a, b in (((-0.52, 0, 0.34), (0.0, 0, 0.36)), ((0.0, 0, 0.36), (0.38, 0, 0.82)), ((0.38, 0, 0.82), (-0.12, 0, 0.8)),
                 ((-0.12, 0, 0.8), (0.0, 0, 0.36)), ((-0.12, 0, 0.8), (-0.52, 0, 0.34)), ((0.38, 0, 0.82), (0.52, 0, 0.34)),
                 ((0.38, 0, 0.82), (0.36, 0, 0.98)), ((-0.12, 0, 0.8), (-0.14, 0, 0.9))):
        G.cilindro_eixo(f"{nome}_t{a[0]}{b[0]}{b[2]}", a, b, 0.017, cor, col)["suspenso"] = True
    G.cilindro_eixo(f"{nome}_guidao", (0.36, -0.25, 0.98), (0.36, 0.25, 0.98), 0.014, M.pintura("#2b2e33", rug=0.4), col)["suspenso"] = True
    _caixa(f"{nome}_selim", (-0.24, -0.06, 0.9), (-0.04, 0.06, 0.94), M.pintura("#18191b", rug=0.6), col, 0.015)
    return 0.6


def vaso_planta(nome, col, rng):
    G.cilindro(f"{nome}_vaso", (0, 0, 0), 0.28, 0.5, M.pintura(rng.choice(["#b5532f", "#8d8577", "#3a3d42"]), rug=0.7), col, raio_topo=0.34, lados=20)
    arbusto(nome, col, rng, 0.4)
    for o in col.objects:
        if o.name.startswith(nome + "_b"):
            o.location.z += 0.42
    return 0.45


def mesa_bar(nome, col, rng):
    """Mesa plástica de bar com 4 cadeiras (cores lisas, sem marca)."""
    cor = rng.choice(["#e9e9e6", "#c8231f", "#f2c230", "#1d4f9c"]); plast = M.pintura(cor, rug=0.45)
    _caixa(f"{nome}_tampo", (-0.36, -0.36, 0.7), (0.36, 0.36, 0.74), plast, col, 0.015)
    for sx in (-0.3, 0.3):
        for sy in (-0.3, 0.3):
            _caixa(f"{nome}_perna{sx}{sy}", (sx - 0.025, sy - 0.025, 0.0), (sx + 0.025, sy + 0.025, 0.7), plast, col, suspenso=False)
    for k in range(rng.choice([2, 3, 4])):
        a = math.pi / 2 * k + rng.uniform(-0.25, 0.25); d = 0.62
        cx, cy = d * math.cos(a), d * math.sin(a); ux, uy = -math.cos(a), -math.sin(a)   # cadeira de frente para a mesa
        px, py = -uy, ux
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                x = cx + 0.18 * s1 * ux + 0.18 * s2 * px; y = cy + 0.18 * s1 * uy + 0.18 * s2 * py
                _caixa(f"{nome}_cp{k}{s1}{s2}", (x - 0.02, y - 0.02, 0.0), (x + 0.02, y + 0.02, 0.44), plast, col, suspenso=False)
        G.cilindro(f"{nome}_ass{k}", (cx, cy, 0.44), 0.23, 0.04, plast, col, lados=16)["suspenso"] = True
        bx, by = cx - 0.2 * ux, cy - 0.2 * uy
        enc = _caixa(f"{nome}_enc{k}", (-0.2, -0.02, 0.0), (0.2, 0.02, 0.38), plast, col, 0.02)
        enc.location = (bx, by, 0.46); enc.rotation_euler = (math.radians(-10) * 0, 0, a + math.pi / 2)
    return 1.0


def engradados(nome, col, rng):
    cor = M.pintura(rng.choice(["#c8231f", "#e3a12f", "#2f7d3a"]), rug=0.5)
    n = rng.randint(2, 5)
    for i in range(n):
        _caixa(f"{nome}_e{i}", (-0.2, -0.3, i * 0.3), (0.2, 0.3, i * 0.3 + 0.29), cor, col, 0.01, suspenso=(i > 0))
    return 0.4


def bancada_frutas(nome, col, rng):
    mad = M.madeira("#9a6a42")
    _caixa(f"{nome}_mesa", (-0.45, -0.9, 0.0), (0.45, 0.9, 0.75), mad, col, 0.02, suspenso=False)
    cores = ["#e3a12f", "#c8231f", "#5b8540", "#f2c230", "#d9702c"]
    for i in range(6):
        cx = -0.3 + (i % 2) * 0.6 * 0 + (i % 2) * 0.35; cy = -0.6 + (i // 2) * 0.6
        _caixa(f"{nome}_cx{i}", (cx - 0.15, cy - 0.25, 0.75), (cx + 0.15, cy + 0.25, 0.85), M.madeira("#b8875a"), col)
        mat = M.pintura(rng.choice(cores), rug=0.45)
        for j in range(8):
            G.esfera(f"{nome}_f{i}_{j}", (cx + rng.uniform(-0.1, 0.1), cy + rng.uniform(-0.18, 0.18), 0.9 + rng.uniform(0, 0.04)), 0.05, mat, col, sub=1)["suspenso"] = True
    return 1.0


ITENS = {"banco": banco_praca, "conteiner": conteiner, "sacos": sacos_lixo, "ponto_onibus": ponto_onibus, "banca": banca,
         "cones": cones, "bicicleta": bicicleta, "vaso": vaso_planta, "mesa_bar": mesa_bar, "engradados": engradados,
         "frutas": bancada_frutas, "arbusto": lambda n, c, r: arbusto(n, c, r)}
ALTURA = {"banco": 0.95, "conteiner": 1.25, "sacos": 0.7, "ponto_onibus": 2.6, "banca": 2.75, "cones": 0.7, "bicicleta": 1.0,
          "vaso": 1.1, "mesa_bar": 0.9, "engradados": 1.5, "frutas": 1.0, "arbusto": 1.0}


# ------------------------------------------------------------------ regras: apoio e colisão
def _superficie(cena, dg, x, y, z_de=3.0):
    ok, loc, *_ = cena.ray_cast(dg, Vector((x, y, z_de)), Vector((0, 0, -1)))
    return loc.z if ok else None


def _bvh_mundo(o, dg):
    ev = o.evaluated_get(dg); me = ev.to_mesh()
    vs = [o.matrix_world @ v.co for v in me.vertices]; fs = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs) if fs else None


def _bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


def colisoes(cena, objs_grupo, ignorar=(), chao_z=0.2):
    """Objetos da cena (fora do grupo) que a geometria do grupo atravessa. Ignora o chão (topo ≤ 20 cm: pista, calçada, piso tátil, folhas); bordas de canteiro (23 cm) contam."""
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    malhas = [o for o in objs_grupo if o.type == "MESH"]
    if not malhas:
        return []
    mn, mx = _bbox(malhas); nomes = {o.name for o in objs_grupo} | set(ignorar); hits = []
    arvs = None
    for o in cena.objects:
        if o.type != "MESH" or o.name in nomes:
            continue
        a, b = _bbox([o])
        if b.z <= chao_z or a.x > mx.x or b.x < mn.x or a.y > mx.y or b.y < mn.y or a.z > mx.z or b.z < mn.z:
            continue
        if arvs is None:
            arvs = [t for t in (_bvh_mundo(m, dg) for m in malhas) if t is not None]
        t2 = _bvh_mundo(o, dg)
        if t2 is not None and any(t.overlap(t2) for t in arvs):
            hits.append(o.name)
    return hits


def _colocar(cena, col, rng, nome, construtor, posicoes, rot_z, altura, livres, ocupados, raio, max_tent=30):
    """Tenta colocar a peça: apoio real (raio para baixo), coluna livre (raio para cima), áreas livres, distância mínima
    e, por fim, o teste de colisão com a geometria vizinha. Retorna a raiz ou None."""
    dg = bpy.context.evaluated_depsgraph_get()
    for _ in range(max_tent):
        x, y = posicoes()
        if any(a <= x <= b and c <= y <= d for a, c, b, d in livres):
            continue
        if any(math.hypot(x - ox, y - oy) < raio + orr for ox, oy, orr in ocupados):
            continue
        z = _superficie(cena, dg, x, y, z_de=altura + 0.3)
        if z is None or z > 0.2:          # só sobre a calçada: nada de canteiro, poste, toldo ou carro ocupando a coluna
            continue
        ok, *_ = cena.ray_cast(dg, Vector((x, y, z + 0.05)), Vector((0, 0, 1)), distance=altura)
        if ok:
            continue
        antes = set(col.objects); raiz = _raiz(nome, col, (x, y, z), rot_z)
        construtor(nome, col, rng)
        _adotar(col, raiz, antes)
        grupo = [raiz] + list(raiz.children_recursive)
        if colisoes(cena, grupo):
            _remover(raiz); dg = bpy.context.evaluated_depsgraph_get(); continue
        ocupados.append((x, y, raio)); bpy.context.view_layer.update()
        return raiz
    return None


# ------------------------------------------------------------------ componentes registrados
@componente("arvore")
def c_arvore(ctx, p, rng, col):
    antes = set(col.objects); raiz = _raiz(p.get("nome", f"arvore_{p['x']}_{p['y']}"), col, (p["x"], p["y"], p.get("z", 0.0)), p.get("rot", 0.0))
    arvore(raiz.name, col, rng, p.get("especie", "frondosa"), p.get("escala", 1.0), p.get("flor", "amarelo"))
    _adotar(col, raiz, antes)


@componente("mobiliario")
def c_mobiliario(ctx, p, rng, col):
    antes = set(col.objects); raiz = _raiz(p.get("nome", f"{p['tipo']}_{p['x']}_{p['y']}"), col, (p["x"], p["y"], p.get("z", 0.15)), math.radians(p.get("rot_graus", 0.0)))
    ITENS[p["tipo"]](raiz.name, col, rng)
    _adotar(col, raiz, antes)


@componente("arborizacao")
def c_arborizacao(ctx, p, rng, col):
    """Árvores nos canteiros de árvore da rua (objetos '*_terra*' já montados), por semente. Se a copa atravessar algo
    (fachada, varanda, toldo, poste), tenta uma árvore menor; se ainda atravessar, o canteiro fica com um arbusto."""
    cena = ctx["cena"]; bpy.context.view_layer.update()
    especies = p.get("especies", {"frondosa": 0.6, "ipe": 0.3, "palmeira": 0.1})
    canteiros = sorted([o for o in cena.objects if "_terra" in o.name and o.type == "MESH"], key=lambda o: o.name)
    nome = p.get("nome", "arb"); feitos = 0
    for i, t in enumerate(canteiros):
        mn, mx = _bbox([t]); x, y, z = (mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mx.z
        if any(a <= x <= b and c <= y <= d for a, c, b, d in p.get("livres", [])):
            continue
        if "faixa_y" in p and not (p["faixa_y"][0] <= y <= p["faixa_y"][1]):
            continue
        if rng.random() > p.get("ocupacao", 0.85):
            continue
        esp = rng.choices(list(especies), weights=list(especies.values()))[0]; flor = rng.choice(["amarelo", "rosa"])
        colocado = False
        for escala in (rng.uniform(0.9, 1.1), 0.75, 0.6):
            antes = set(col.objects); raiz = _raiz(f"{nome}_{i}_{esp}", col, (x, y, z), rng.uniform(0, 6.28))
            arvore(raiz.name, col, rng, esp, escala, flor); _adotar(col, raiz, antes)
            if not colisoes(cena, [raiz] + list(raiz.children_recursive), ignorar=[t.name]):
                raiz["ignorar_colisao"] = t.name          # o tronco é plantado no solo do canteiro (de propósito)
                colocado = True; feitos += 1; break
            _remover(raiz)
        if not colocado:
            antes = set(col.objects); raiz = _raiz(f"{nome}_{i}_arbusto", col, (x, y, z), 0.0)
            arbusto(raiz.name, col, rng, 0.38); _adotar(col, raiz, antes); raiz["ignorar_colisao"] = t.name
            if colisoes(cena, [raiz] + list(raiz.children_recursive), ignorar=[t.name]):
                _remover(raiz)
    # canteiros NOVOS ao longo do meio-fio (passo regular, com jitter), cada um testado pelas mesmas regras
    dg = bpy.context.evaluated_depsgraph_get(); j = 0
    for x, y0, y1 in p.get("novos_canteiros", []):
        y = y0 + rng.uniform(0, 2.0)
        while y < y1:
            yy = y; y += p.get("passo", 8.0) + rng.uniform(-1.0, 1.5)
            if any(a <= x <= b and c <= yy <= d for a, c, b, d in p.get("livres", [])):
                continue
            pts = [(x + dx, yy + dy) for dx in (-0.55, 0, 0.55) for dy in (-0.55, 0, 0.55)]
            zs = [_superficie(cena, dg, px, py, z_de=6.0) for px, py in pts]
            if any(zz is None or not (0.1 < zz < 0.2) for zz in zs):     # só sobre calçada livre (nada em cima: poste, toldo…)
                continue
            z0 = max(zs); antes = set(col.objects); raiz = _raiz(f"{nome}_n{j}", col, (x, yy, z0), rng.uniform(0, 6.28))
            borda = M.concreto("#bdb6a8", placa_m=(1.0, 0.15), desgaste=0.5)
            for k, (a0, b0, a1, b1) in enumerate(((-0.5, -0.5, 0.5, -0.43), (-0.5, 0.43, 0.5, 0.5), (-0.5, -0.43, -0.43, 0.43), (0.43, -0.43, 0.5, 0.43))):
                G.caixa(f"{raiz.name}_borda{k}", (a0, b0, 0.0), (a1, b1, 0.08), borda, col, chanfro=0.01)
            G.caixa(f"{raiz.name}_solo", (-0.43, -0.43, 0.0), (0.43, 0.43, 0.06), M.terra(), col)
            esp = rng.choices(list(especies), weights=list(especies.values()))[0]; flor = rng.choice(["amarelo", "rosa"])
            ok = False
            for escala in (rng.uniform(0.9, 1.1), 0.75, 0.6):
                antes_a = set(col.objects); sub = _raiz(f"{raiz.name}_{esp}", col, (0, 0, 0.06), 0.0); sub.parent = raiz
                arvore(sub.name, col, rng, esp, escala, flor)
                for o in col.objects:
                    if o not in antes_a and o is not sub and o.parent is None:
                        o.parent = sub
                _adotar(col, raiz, antes)
                if not colisoes(cena, [raiz] + list(raiz.children_recursive)):
                    ok = True; break
                _remover(sub)
            if not ok:
                _remover(raiz); continue
            j += 1; dg = bpy.context.evaluated_depsgraph_get()


@componente("ambientacao")
def c_ambientacao(ctx, p, rng, col):
    """Espalha mobiliário nas calçadas com regras. params: faixas [[x0, y0, x1, y1, rot_graus], …] (onde pode ir, e para
    onde a peça olha), itens {tipo: quantidade}, livres [[x0, y0, x1, y1], …] (portas, garagens, faixa de pedestre,
    lugar do Heitor), dist_min (0,4)."""
    cena = ctx["cena"]; bpy.context.view_layer.update()
    faixas = p["faixas"]; livres = p.get("livres", []); ocup = []; nome = p.get("nome", "amb")
    raios = {"banco": 1.0, "conteiner": 0.9, "sacos": 0.5, "ponto_onibus": 1.9, "banca": 1.7, "cones": 0.6, "bicicleta": 0.7,
             "vaso": 0.45, "mesa_bar": 1.0, "engradados": 0.4, "frutas": 1.0, "arbusto": 0.6}
    k = 0; relatorio = {}
    for tipo, qtd in p["itens"].items():
        relatorio[tipo] = 0
        for _ in range(qtd):
            fx = rng.choice(faixas)
            pos = lambda fx=fx: (rng.uniform(fx[0], fx[2]), rng.uniform(fx[1], fx[3]))
            r = _colocar(cena, col, rng, f"{nome}_{k}_{tipo}", ITENS[tipo], pos, math.radians(fx[4] if len(fx) > 4 else 0.0),
                         ALTURA[tipo], livres, ocup, raios[tipo] + p.get("dist_min", 0.4) / 2)
            k += 1
            if r is not None:
                relatorio[tipo] += 1
    ctx.setdefault("relatorio_ambientacao", {})[nome] = relatorio


@componente("mesas_bar")
def c_mesas_bar(ctx, p, rng, col):
    """Mesas de bar (e engradados) na calçada em frente às lojas cujo letreiro tem um dos nomes dados."""
    cena = ctx["cena"]; bpy.context.view_layer.update()
    nomes = set(p.get("lojas", ["LANCHONETE", "PADARIA"])); ocup = []; k = 0
    for t in sorted([o for o in cena.objects if o.type == "FONT" and o.data.body in nomes], key=lambda o: o.name):
        n = (t.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized(); n.z = 0; n.normalize()
        base = t.matrix_world.translation; ao_longo = Vector((-n.y, n.x, 0))
        for j in range(p.get("mesas_por_loja", 3)):
            def pos(j=j):
                c = base + n * rng.uniform(1.2, 2.3) + ao_longo * rng.uniform(-2.5, 2.5)
                return c.x, c.y
            _colocar(cena, col, rng, f"{p.get('nome', 'bar')}_{k}", mesa_bar, pos, rng.uniform(0, 1.5), ALTURA["mesa_bar"],
                     p.get("livres", []), ocup, 1.05)
            k += 1
        def pos_e():
            c = base + n * 0.5 + ao_longo * rng.uniform(-2.0, 2.0)
            return c.x, c.y
        _colocar(cena, col, rng, f"{p.get('nome', 'bar')}_eng{k}", engradados, pos_e, math.atan2(n.y, n.x), ALTURA["engradados"],
                 p.get("livres", []), ocup, 0.45)
