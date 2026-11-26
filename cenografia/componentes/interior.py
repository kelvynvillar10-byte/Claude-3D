"""Cenografia — kit de INTERIOR (E10, EP01 "5 centímetros"): quarto em escala real filmado em escala MACRO.

Tudo em metros, nas medidas reais de um quarto brasileiro (pé-direito 2,6 m, cama de solteiro com o colchão a ~0,5 m,
criado-mudo de 0,55 m, celular de 15 cm, degrau de 18 cm). O Heitor entra no compositor com 0,05 m de altura: a escala
vem das medidas reais, não de truque. Componentes:
- camera_macro   lente de perto: plano de corte de 2 mm e profundidade de campo física (foco e abertura)
- quarto         piso de tábuas, paredes pintadas, rodapé, teto, janela aberta com caixilho e cortinas
- cama           estrado de madeira, colchão, edredom caindo pelas bordas (dobras = "dunas"), travesseiros
- criado_mudo    gaveta e puxador, abajur (luz no grupo "artificial"), livros
- celular        apoiado num suporte; tela acesa com papel de parede abstrato (SEM texto, SEM marca)
- tapete, chinelos, carrinho (brinquedo genérico), quadro (arte abstrata, sem texto), estante com livros e caixas
- moeda (genérica: aro, relevo radial; não reproduz moeda real), gota, poca, migalhas, poeira
Materiais do kit (com relevo fino que aguenta o close macro): tecido (trama), água, metal de moeda, pão, tela.
Nada aqui tem texto 3D.
"""
import math
import bpy, bmesh
from mathutils import Vector
from cenografia.nucleo.registro import componente
from cenografia.nucleo import geometria as G, materiais as M
from cenografia.nucleo.materiais import lin

TEXTOS_KIT = []


# ------------------------------------------------------------------ materiais do kit
def tecido(cor="#e9e4da", trama_por_m=900.0, rug=0.85, estampa=None):
    """Tecido de algodão: trama fina em relevo (visível no macro), leve variação de tom e brilho aveludado."""
    chave = ("tecido", cor, trama_por_m, rug, estampa)
    if chave in M._CACHE:
        return M._CACHE[chave]
    t = M._NT("tecido"); v = t.coord("Object")
    w1 = t.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", Scale=trama_por_m, Distortion=0.6, **{"Detail": 1.0}); t.l(v, w1.inputs["Vector"])
    w2 = t.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y", Scale=trama_por_m, Distortion=0.6, **{"Detail": 1.0}); t.l(v, w2.inputs["Vector"])
    trama = t.n("ShaderNodeMath", operation="MULTIPLY"); t.l(w1.outputs["Factor"], trama.inputs[0]); t.l(w2.outputs["Factor"], trama.inputs[1])
    var = t.ruido(v, 8.0, 4.0, 0.55)
    base = t.mistura(lin(cor), M._escurece(cor, 0.86), t.mat_valor(var, 0.0, 0.6))
    if estampa:                                        # listras largas (lençol/edredom estampado)
        lst = t.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", Scale=estampa[1], Distortion=0.0); t.l(v, lst.inputs["Vector"])
        mk = t.n("ShaderNodeMapRange"); mk.inputs["From Min"].default_value = 0.48; mk.inputs["From Max"].default_value = 0.52
        t.l(lst.outputs["Factor"], mk.inputs["Value"]); base = t.mistura(base, lin(estampa[0]), mk.outputs["Result"])
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = rug
    if "Sheen Weight" in t.b.inputs:
        t.b.inputs["Sheen Weight"].default_value = 0.35
    # a trama só existe de perto: entre 0,6 m e 1,5 m da câmera o relevo some (de longe ela vira moiré)
    cam = t.n("ShaderNodeCameraData")
    fade = t.n("ShaderNodeMapRange"); fade.inputs["From Min"].default_value = 0.6; fade.inputs["From Max"].default_value = 1.5
    fade.inputs["To Min"].default_value = 0.25; fade.inputs["To Max"].default_value = 0.0; t.l(cam.outputs["View Distance"], fade.inputs["Value"])
    bp = t.n("ShaderNodeBump"); bp.inputs["Distance"].default_value = 0.0004
    t.l(fade.outputs["Result"], bp.inputs["Strength"]); t.l(trama.outputs[0], bp.inputs["Height"]); t.l(bp.outputs["Normal"], t.b.inputs["Normal"])
    return M._guardar(chave, t.m)


def agua():
    chave = ("agua",)
    if chave in M._CACHE:
        return M._CACHE[chave]
    t = M._NT("agua"); t.b.inputs["Base Color"].default_value = (1, 1, 1, 1)
    t.b.inputs["Transmission Weight"].default_value = 1.0; t.b.inputs["IOR"].default_value = 1.333
    t.b.inputs["Roughness"].default_value = 0.02
    return M._guardar(chave, t.m)


def metal_moeda(cor="#d8b265", rug=0.5):
    """Metal de moeda (latão/aço): micro-riscos e pátina nas reentrâncias, sem desenho de moeda real."""
    chave = ("metal_moeda", cor, rug)
    if chave in M._CACHE:
        return M._CACHE[chave]
    t = M._NT("metal_moeda"); v = t.coord("Object")
    risco = t.ruido(t.coord("Object", (1.0, 60.0, 1.0)), 300.0, 2.0, 0.5)
    patina = t.ruido(v, 900.0, 3.0, 0.6)
    base = t.mistura(lin(cor), M._escurece(cor, 0.55), t.mat_valor(patina, 0.0, 0.35))
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Metallic"].default_value = 1.0
    t.l(t.mat_valor(risco, rug - 0.12, rug + 0.12), t.b.inputs["Roughness"])
    return M._guardar(chave, t.m)


def pao(cor="#d9a861"):
    chave = ("pao", cor)
    if chave in M._CACHE:
        return M._CACHE[chave]
    t = M._NT("pao"); v = t.coord("Object")
    poros = t.n("ShaderNodeTexVoronoi", Scale=1800.0); t.l(v, poros.inputs["Vector"])
    var = t.ruido(v, 400.0, 3.0, 0.6)
    base = t.mistura(lin(cor), M._escurece(cor, 0.6), t.mat_valor(var, 0.0, 0.7))
    t.l(base, t.b.inputs["Base Color"]); t.b.inputs["Roughness"].default_value = 0.8
    if "Subsurface Weight" in t.b.inputs:
        t.b.inputs["Subsurface Weight"].default_value = 0.2
    t.l(t.relevo(poros.outputs["Distance"], 0.5, 0.0006), t.b.inputs["Normal"])
    return M._guardar(chave, t.m)


def tela(cor_a="#2b5bd7", cor_b="#ff8a3d", forca=2.2):
    """Tela acesa: degradê abstrato com ondas suaves (papel de parede genérico, sem ícones nem texto)."""
    chave = ("tela", cor_a, cor_b, forca)
    if chave in M._CACHE:
        return M._CACHE[chave]
    t = M._NT("tela"); v = t.coord("Object")
    sep = t.n("ShaderNodeSeparateXYZ"); t.l(v, sep.inputs["Vector"])
    onda = t.n("ShaderNodeTexWave", wave_type="BANDS", Scale=12.0, Distortion=3.0); t.l(v, onda.inputs["Vector"])
    f = t.mat_valor(onda.outputs["Factor"], 0.0, 1.0)
    cor = t.mistura(lin(cor_a), lin(cor_b), f)
    t.b.inputs["Base Color"].default_value = (0.01, 0.01, 0.012, 1); t.b.inputs["Roughness"].default_value = 0.05
    t.l(cor, t.b.inputs["Emission Color"]); t.b.inputs["Emission Strength"].default_value = forca
    return M._guardar(chave, t.m)


def plastico(cor, rug=0.35):
    return M.pintura(cor, rug=rug, metal=0.0, desgaste=0.05)


# ------------------------------------------------------------------ utilidades
def _grade(nome, x0, y0, x1, y1, nx, ny, z_de, mat, col, espessura=0.0, liso=True, sub=0):
    """Malha em grade com z = z_de(x, y) (edredom, poça, tapete com ondulação)."""
    bm = bmesh.new(); vs = []
    for j in range(ny + 1):
        linha = []
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny
            linha.append(bm.verts.new((x, y, z_de(x, y))))
        vs.append(linha)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    o = G._obj(nome, bm, mat, col, liso=liso)
    if espessura:
        s = o.modifiers.new("espessura", "SOLIDIFY"); s.thickness = espessura; s.offset = -1.0
    if sub:
        m = o.modifiers.new("sub", "SUBSURF"); m.levels = sub; m.render_levels = sub
    return o


def _suave(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def _marcar(objs, **props):
    for o in objs:
        for k, v in props.items():
            o[k] = v


# ------------------------------------------------------------------ câmera macro
@componente("camera_macro")
def camera_macro(ctx, p, rng, col):
    """Ajusta a câmera da cena para o macro: corte a 2 mm e profundidade de campo física. Não cria geometria."""
    cam = bpy.context.scene.camera
    cam.data.clip_start = p.get("clip_inicio_m", 0.002)
    if p.get("foco_m"):
        cam.data.dof.use_dof = True
        cam.data.dof.focus_distance = float(p["foco_m"])
        cam.data.dof.aperture_fstop = float(p.get("abertura_f", 2.8))
        cam.data.dof.aperture_blades = int(p.get("laminas", 7))


# ------------------------------------------------------------------ quarto
@componente("quarto")
def quarto(ctx, p, rng, col):
    x0, x1, y0, y1 = p.get("x0", -1.7), p.get("x1", 1.7), p.get("y0", -1.9), p.get("y1", 1.9)
    h = p.get("pe_direito", 2.6); esp = 0.12
    # piso de tábuas (3 tons, frestas reais de 1,5 mm, comprimentos alternados)
    tons = p.get("tons_piso", ["#9a6a43", "#8a5d3a", "#a8774c"])
    larg = p.get("tabua_m", 0.14); fresta = 0.0015; i = 0; x = x0
    while x < x1 - 1e-6:
        xe = min(x1, x + larg)
        corte = rng.uniform(0.6, 2.4); ys = [y0, min(y1, y0 + corte)]
        while ys[-1] < y1 - 1e-6:
            ys.append(min(y1, ys[-1] + rng.uniform(1.2, 2.4)))
        for k in range(len(ys) - 1):
            G.caixa(f"tabua_{i}_{k}", (x + fresta / 2, ys[k] + fresta / 2, -0.02), (xe - fresta / 2, ys[k + 1] - fresta / 2, 0.0),
                    M.madeira(tons[rng.randrange(len(tons))], escala=p.get("veio", 3.0)), col, chanfro=0.0008)
        x = xe; i += 1
    G.caixa("contrapiso", (x0, y0, -0.06), (x1, y1, -0.02), M.concreto("#5b5249"), col)
    # paredes (a parede y0 tem a janela)
    parede = M.pintura(p.get("cor_parede", "#cfe0e6"), rug=0.75, desgaste=0.08)
    jx0, jx1 = p.get("janela_x", (-1.5, -0.3)); jz0, jz1 = p.get("janela_z", (0.95, 2.15))
    G.caixa("parede_y0_esq", (x0 - esp, y0 - esp, 0), (jx0, y0, h), parede, col)
    G.caixa("parede_y0_dir", (jx1, y0 - esp, 0), (x1 + esp, y0, h), parede, col)
    G.caixa("parede_y0_baixo", (jx0, y0 - esp, 0), (jx1, y0, jz0), parede, col)
    G.caixa("parede_y0_cima", (jx0, y0 - esp, jz1), (jx1, y0, h), parede, col)
    G.caixa("parede_y1", (x0 - esp, y1, 0), (x1 + esp, y1 + esp, h), parede, col)
    G.caixa("parede_x0", (x0 - esp, y0, 0), (x0, y1, h), parede, col)
    G.caixa("parede_x1", (x1, y0, 0), (x1 + esp, y1, h), parede, col)
    G.caixa("teto", (x0 - esp, y0 - esp, h), (x1 + esp, y1 + esp, h + esp), M.pintura("#f1efe9", rug=0.9), col)["suspenso"] = True
    rod = M.pintura("#f4f1ea", rug=0.5)
    for nome, c0, c1 in [("rod_y1", (x0, y1 - 0.012, 0), (x1, y1, 0.08)), ("rod_x0", (x0, y0, 0), (x0 + 0.012, y1, 0.08)),
                         ("rod_x1", (x1 - 0.012, y0, 0), (x1, y1, 0.08)), ("rod_y0a", (x0, y0, 0), (jx0, y0 + 0.012, 0.08)),
                         ("rod_y0b", (jx1, y0, 0), (x1, y0 + 0.012, 0.08)), ("rod_y0c", (jx0, y0, 0), (jx1, y0 + 0.012, 0.08))]:
        G.caixa(nome, c0, c1, rod, col, chanfro=0.002)
    # janela: caixilho branco, folhas de correr abertas (o vidro fica atrás da parede), peitoril
    cx = M.pintura("#f3f2ee", rug=0.35)
    G.caixa("peitoril", (jx0 - 0.04, y0 - esp - 0.03, jz0 - 0.03), (jx1 + 0.04, y0 + 0.03, jz0), M.concreto("#d9d4c8"), col, chanfro=0.004)
    for nome, c0, c1 in [("caix_esq", (jx0, y0 - 0.06, jz0), (jx0 + 0.04, y0, jz1)), ("caix_dir", (jx1 - 0.04, y0 - 0.06, jz0), (jx1, y0, jz1)),
                         ("caix_cima", (jx0, y0 - 0.06, jz1 - 0.04), (jx1, y0, jz1))]:
        G.caixa(nome, c0, c1, cx, col, chanfro=0.003)
    # luz difusa do céu entrando pela janela (área do tamanho do vão, grupo "ceu")
    L = bpy.data.lights.new("luz_janela", "AREA"); L.shape = "RECTANGLE"; L.size = jx1 - jx0; L.size_y = jz1 - jz0
    L.energy = p.get("janela_w", 160.0); L.color = lin(p.get("cor_ceu_janela", "#dfe9ff"))[:3]
    oj = bpy.data.objects.new("luz_janela", L); bpy.context.scene.collection.objects.link(oj)
    oj.location = ((jx0 + jx1) / 2, y0 + 0.01, (jz0 + jz1) / 2); oj.rotation_euler = (math.radians(-90), 0, 0); oj.lightgroup = "ceu"
    # cortinas (painéis ondulados, do teto até perto do chão)
    cort = tecido(p.get("cor_cortina", "#f0d9a8"), trama_por_m=500)
    for lado, xa, xb in (("esq", jx0 - 0.45, jx0 + 0.05), ("dir", jx1 - 0.05, jx1 + 0.45)):
        bm = bmesh.new(); n = 24; topo = h - 0.08; base = 0.06; vs = []
        for j in range(2):
            vs.append([bm.verts.new((xa + (xb - xa) * i / n, y0 + 0.07 + 0.035 * math.sin(i * math.pi / 2.2), topo if j else base)) for i in range(n + 1)])
        for i in range(n):
            bm.faces.new((vs[0][i], vs[0][i + 1], vs[1][i + 1], vs[1][i]))
        o = G._obj(f"cortina_{lado}", bm, cort, col, liso=True)
        s = o.modifiers.new("esp", "SOLIDIFY"); s.thickness = 0.004
        o["suspenso"] = True
    G.cilindro_eixo("varao", (jx0 - 0.5, y0 + 0.07, h - 0.07), (jx1 + 0.5, y0 + 0.07, h - 0.07), 0.012, M.pintura("#3a3a3c", rug=0.3, metal=0.6), col)
    bpy.data.objects["varao"]["suspenso"] = True


# ------------------------------------------------------------------ cama
def superficie_edredom(p, seed, x, y):
    """Altura do topo do edredom sobre o colchão (sempre acima dele): dunas suaves de ±dunas_m.
    Função pura: o teste usa a mesma para pôr o Heitor em pé em cima do edredom."""
    zc = p.get("h_estrado", 0.30) + p.get("h_colchao", 0.20); d = p.get("dunas_m", 0.018)
    return zc + 0.006 + d + d * (0.6 * math.sin(7.0 * x + seed) * math.sin(5.0 * y + 0.3 * seed) + 0.4 * math.sin(13.0 * y - 4.0 * x))


@componente("cama")
def cama(ctx, p, rng, col):
    x0, x1, y0, y1 = p["x0"], p["x1"], p["y0"], p["y1"]             # y1 = cabeceira
    madeira = M.madeira(p.get("cor_madeira", "#c79a6b"), escala=2.5)
    h_estrado = p.get("h_estrado", 0.30); h_colchao = p.get("h_colchao", 0.20)
    for i, (px, py) in enumerate([(x0 + 0.04, y0 + 0.04), (x1 - 0.04, y0 + 0.04), (x0 + 0.04, y1 - 0.04), (x1 - 0.04, y1 - 0.04)]):
        G.caixa(f"pe_cama_{i}", (px - 0.03, py - 0.03, 0), (px + 0.03, py + 0.03, h_estrado - 0.06), madeira, col, chanfro=0.004)
    G.caixa("estrado", (x0, y0, h_estrado - 0.06), (x1, y1, h_estrado), madeira, col, chanfro=0.006)["suspenso"] = True   # sobre os pés
    G.caixa("cabeceira", (x0 - 0.02, y1, 0), (x1 + 0.02, y1 + 0.04, h_estrado + 0.55), madeira, col, chanfro=0.008)
    zc = h_estrado + h_colchao
    G.caixa("colchao", (x0 + 0.01, y0 + 0.01, h_estrado), (x1 - 0.01, y1 - 0.01, zc), tecido("#f2f0eb", 800), col, chanfro=0.035)
    # edredom: cobre o colchão e cai pelas bordas; superfície com "dunas" suaves (vira deserto no macro)
    cor = p.get("cor_edredom", "#6f9ed6"); ed = tecido(cor, 700, estampa=(p.get("cor_listra", "#f1e7d0"), 9.0) if p.get("listras", False) else None)
    caida = p.get("caida_m", 0.24); seed = rng.uniform(0, 100)
    fx0, fx1, fy0, fy1 = x0 - 0.06, x1 + 0.06, y0 - 0.06, y1 - 0.42        # termina antes dos travesseiros

    def z_ed(x, y):
        dx = max(x0 - x, x - x1, 0.0); dy = max(y0 - y, 0.0)
        borda = max(dx, dy)
        return superficie_edredom(p, seed, x, y) - caida * _suave(borda / 0.06) - 0.02 * _suave(borda / 0.06)
    # grade densa + bordas que descem: x além do colchão vira a "parede" do edredom
    ext = 0.06
    o = _grade("edredom", fx0, fy0, fx1, fy1, 90, 110, z_ed, ed, col, espessura=0.012, sub=1)
    o.modifiers.new("chanfro", "BEVEL").width = 0.004
    _marcar([o], suspenso=True)                                       # apoiado no colchão (o raio pega o próprio edredom)
    # dobra do edredom aberta perto dos travesseiros (rolo)
    if p.get("dobra", False):
        G.cilindro_eixo("edredom_dobra", (fx0 + 0.02, fy1 + 0.03, zc + 0.04), (fx1 - 0.02, fy1 + 0.03, zc + 0.04), 0.045, ed, col, lados=24)
        bpy.data.objects["edredom_dobra"]["suspenso"] = True
    # travesseiros
    for k, (xa, xb) in enumerate(p.get("travesseiros", [(x0 + 0.06, x1 - 0.06)])):
        t = G.caixa(f"travesseiro_{k}", (xa, y1 - 0.38, zc), (xb, y1 - 0.05, zc + p.get("h_travesseiro", 0.17)), tecido(p.get("cor_fronha", "#f3e3b5"), 850), col)
        sub = t.modifiers.new("sub", "SUBSURF"); sub.levels = 3; sub.render_levels = 3
        G.deformar_ruido(t, forca=0.01, escala=0.08, semente=k)
        t["suspenso"] = True


# ------------------------------------------------------------------ criado-mudo, abajur, livros, celular
@componente("criado_mudo")
def criado_mudo(ctx, p, rng, col):
    x, y = p["x"], p["y"]; L, P, A = p.get("largura", 0.45), p.get("profundidade", 0.38), p.get("altura", 0.55)
    m = M.madeira(p.get("cor", "#e9e2d3"), escala=2.0, pintada=p.get("pintura", "#f3efe6"))
    G.caixa("cm_corpo", (x - L / 2, y - P / 2, 0.05), (x + L / 2, y + P / 2, A - 0.025), m, col, chanfro=0.004)["suspenso"] = True
    G.caixa("cm_tampo", (x - L / 2 - 0.01, y - P / 2 - 0.01, A - 0.025), (x + L / 2 + 0.01, y + P / 2 + 0.01, A), m, col, chanfro=0.005)
    for i, (px, py) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        G.caixa(f"cm_pe_{i}", (x + px * (L / 2 - 0.03) - 0.015, y + py * (P / 2 - 0.03) - 0.015, 0), (x + px * (L / 2 - 0.03) + 0.015, y + py * (P / 2 - 0.03) + 0.015, 0.05), m, col)
    fr = y - P / 2
    G.caixa("cm_gaveta", (x - L / 2 + 0.02, fr - 0.006, A - 0.2), (x + L / 2 - 0.02, fr, A - 0.06), m, col, chanfro=0.003)["suspenso"] = True
    G.cilindro_eixo("cm_puxador", (x, fr - 0.006, A - 0.13), (x, fr - 0.026, A - 0.13), 0.009, M.pintura("#b08d57", rug=0.25, metal=0.9), col)
    bpy.data.objects["cm_puxador"]["suspenso"] = True
    # abajur
    ax, ay = x + p.get("abajur_dx", -0.11), y + p.get("abajur_dy", 0.06)
    G.cilindro("abajur_base", (ax, ay, A), 0.06, 0.03, plastico("#e4d7bf"), col, lados=32, chanfro=0.004)
    G.cilindro("abajur_haste", (ax, ay, A + 0.03), 0.008, 0.22, M.pintura("#b08d57", rug=0.3, metal=0.9), col, lados=16)
    cup = G.cilindro("abajur_cupula", (ax, ay, A + 0.2), 0.12, 0.16, tecido("#f4ead2", 600), col, lados=48, raio_topo=0.07)
    s = cup.modifiers.new("esp", "SOLIDIFY"); s.thickness = 0.003
    cup["suspenso"] = True
    G.esfera("abajur_lampada", (ax, ay, A + 0.26), 0.03, M.emissor("#ffd59a", p.get("lampada_forca", 0.0)), col)
    bpy.data.objects["abajur_lampada"]["suspenso"] = True
    from cenografia.nucleo import luz as Lz
    if p.get("abajur_watts", 0.0) > 0:                                 # de manhã o abajur fica apagado
        Lz.luz_ponto("abajur_luz", (ax, ay, A + 0.26), p["abajur_watts"], "#ffc98a", "artificial", raio=0.03)
    # livros empilhados
    zt = A; cores = ["#b8403a", "#2f6aa3", "#e1b33f", "#4f8a5b"]
    for k in range(p.get("livros", 3)):
        e = rng.uniform(0.018, 0.03); w = rng.uniform(0.13, 0.17); d = rng.uniform(0.19, 0.23); ang = rng.uniform(-0.2, 0.2)
        bx, by = x + 0.09, y + 0.05
        b = G.caixa(f"livro_{k}", (-w / 2, -d / 2, 0), (w / 2, d / 2, e), plastico(cores[k % 4], 0.55), col, chanfro=0.0015)
        b.location = (bx, by, zt); b.rotation_euler.z = ang
        zt += e
    ctx.setdefault("tampos", []).append({"x": x, "y": y, "z": A})


@componente("celular")
def celular(ctx, p, rng, col):
    """Celular de pé num suporte (15 cm de altura, 7,2 cm de largura). Tela acesa abstrata."""
    x, y, z = p["x"], p["y"], p["z"]; ang = math.radians(p.get("giro_graus", 0.0)); incl = math.radians(p.get("inclinacao_graus", 14.0))
    Wc, Hc, E = 0.072, 0.152, 0.0085
    sup = M.pintura("#2a2a2e", rug=0.4, metal=0.2)
    base = G.caixa("suporte_base", (-0.045, -0.04, 0), (0.045, 0.04, 0.006), sup, col, chanfro=0.002)
    enc = G.caixa("suporte_encosto", (-0.035, 0.012, 0.004), (0.035, 0.018, 0.07), sup, col, chanfro=0.0015)
    enc.rotation_euler.x = -incl
    corpo = G.caixa("celular_corpo", (-Wc / 2, -E / 2, 0), (Wc / 2, E / 2, Hc), M.pintura("#1c1d22", rug=0.3, metal=0.5), col, chanfro=0.004)
    tl = G.caixa("celular_tela", (-Wc / 2 + 0.003, -E / 2 - 0.0004, 0.004), (Wc / 2 - 0.003, -E / 2 + 0.0002, Hc - 0.004),
                 tela(p.get("cor_a", "#2b5bd7"), p.get("cor_b", "#ff8a3d"), p.get("forca", 2.2)), col, chanfro=0.0)
    for o in (corpo, tl):
        o.rotation_euler.x = -incl; o.location = (0, 0.008, 0.006)
    raiz = bpy.data.objects.new("celular_raiz", None); col.objects.link(raiz); raiz.location = (x, y, z); raiz.rotation_euler.z = ang
    for o in (base, enc, corpo, tl):
        o.parent = raiz
    tl.lightgroup = "artificial"                                        # a tela acende pelo grupo "artificial" no compositor
    for o in (enc, corpo, tl):
        o["suspenso"] = True                                          # apoiados no suporte inclinado


# ------------------------------------------------------------------ chão: tapete, chinelos, carrinho, moeda, gota, poça, migalhas, poeira
@componente("tapete")
def tapete(ctx, p, rng, col):
    x0, y0, x1, y1 = p["x0"], p["y0"], p["x1"], p["y1"]
    m = tecido(p.get("cor", "#c9b48d"), trama_por_m=220, rug=0.95, estampa=(p.get("cor_listra", "#7b5a3a"), 3.0))
    o = _grade("tapete", x0, y0, x1, y1, 40, 40, lambda x, y: 0.0 + 0.0015 * math.sin(9 * x) * math.sin(7 * y), m, col, espessura=0.008)
    o.location.z = 0.008


@componente("chinelos")
def chinelos(ctx, p, rng, col):
    x, y, ang = p["x"], p["y"], math.radians(p.get("giro_graus", 0))
    for k, dx in enumerate((-0.06, 0.06)):
        sola = G.caixa(f"chinelo_sola_{k}", (-0.045, -0.12, 0.0), (0.045, 0.12, 0.016), M.borracha(p.get("cor", "#2f6aa3")), col, chanfro=0.008)
        tira = G.caixa(f"chinelo_tira_{k}", (-0.04, -0.03, 0.016), (0.04, 0.0, 0.03), M.borracha("#f3f1ea"), col, chanfro=0.004)
        for o in (sola, tira):
            o.location = (x + dx * math.cos(ang), y + dx * math.sin(ang), 0.0); o.rotation_euler.z = ang + (0.12 if k else -0.08)
        tira["suspenso"] = True


@componente("carrinho")
def carrinho(ctx, p, rng, col):
    """Brinquedo genérico (sem marca): carroceria arredondada, rodas pretas."""
    x, y, ang = p["x"], p["y"], math.radians(p.get("giro_graus", 0))
    cor = p.get("cor", "#d8453b")
    corpo = G.caixa("carrinho_corpo", (-0.035, -0.07, 0.012), (0.035, 0.07, 0.035), plastico(cor, 0.25), col, chanfro=0.01)
    cab = G.caixa("carrinho_cabine", (-0.028, -0.025, 0.035), (0.028, 0.03, 0.055), plastico("#bfe3f2", 0.1), col, chanfro=0.008)
    rodas = [G.cilindro_eixo(f"carrinho_roda_{i}", (sx * 0.036, sy * 0.045, 0.012), (sx * 0.046, sy * 0.045, 0.012), 0.012, M.borracha(), col, lados=24)
             for i, (sx, sy) in enumerate([(1, 1), (-1, 1), (1, -1), (-1, -1)])]
    raiz = bpy.data.objects.new("carrinho_raiz", None); col.objects.link(raiz); raiz.location = (x, y, 0.0); raiz.rotation_euler.z = ang
    for o in [corpo, cab] + rodas:
        o.parent = raiz
        o["suspenso"] = True


@componente("moeda")
def moeda(ctx, p, rng, col):
    """Moeda GENÉRICA (não reproduz moeda real): disco de 27 mm × 1,95 mm, aro em relevo e raios em baixo-relevo."""
    x, y, z = p["x"], p["y"], p.get("z", 0.0); r = p.get("diametro_m", 0.027) / 2; e = p.get("espessura_m", 0.00195)
    met = metal_moeda(p.get("cor", "#c9a15a"))
    d = G.cilindro(f"moeda_{p.get('nome', 0)}", (x, y, z), r, e, met, col, lados=96, chanfro=0.00025)
    aro = G.cilindro(f"moeda_aro_{p.get('nome', 0)}", (x, y, z + e), r * 0.98, 0.00025, met, col, lados=96)
    sol = aro.modifiers.new("aro", "SOLIDIFY"); sol.thickness = r * 0.1
    nucleo = G.cilindro(f"moeda_nucleo_{p.get('nome', 0)}", (x, y, z + e), r * 0.5, 0.0002, metal_moeda(p.get("cor_nucleo", "#b7b8b4")), col, lados=64)
    for o in (aro, nucleo):
        o["suspenso"] = True


@componente("gota")
def gota(ctx, p, rng, col):
    """Gota d'água parada: calota achatada (tensão superficial), água com refração."""
    x, y, z, r = p["x"], p["y"], p.get("z", 0.0), p.get("raio_m", 0.002)
    o = G.esfera(f"gota_{p.get('nome', 0)}", (0, 0, 0), r, agua(), col, sub=4)
    bm = bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts:
        v.co.z = max(v.co.z * p.get("achatamento", 0.65), -0.15 * r)   # calota: base plana apoiada no chão
        v.co.z += 0.15 * r + 0.00005
    bm.to_mesh(o.data); bm.free()
    o.location = (x, y, z)


@componente("poca")
def poca(ctx, p, rng, col):
    """Poça rasa de contorno irregular (menisco arredondado na borda)."""
    cx, cy, R, prof = p["x"], p["y"], p.get("raio_m", 0.05), p.get("espessura_m", 0.0015)
    ph = [rng.uniform(0, math.tau) for _ in range(3)]

    def raio(a):
        return R * (1 + 0.18 * math.sin(3 * a + ph[0]) + 0.1 * math.sin(5 * a + ph[1]) + 0.06 * math.sin(9 * a + ph[2]))
    bm = bmesh.new(); n = 96; centro = bm.verts.new((cx, cy, prof)); anel_ext = []; anel_int = []
    for i in range(n):
        a = math.tau * i / n; rr = raio(a)
        anel_int.append(bm.verts.new((cx + 0.85 * rr * math.cos(a), cy + 0.85 * rr * math.sin(a), prof)))
        anel_ext.append(bm.verts.new((cx + rr * math.cos(a), cy + rr * math.sin(a), 0.00005)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((centro, anel_int[i], anel_int[j]))
        bm.faces.new((anel_int[i], anel_ext[i], anel_ext[j], anel_int[j]))
    o = G._obj(f"poca_{p.get('nome', 0)}", bm, agua(), col, liso=True)
    sub = o.modifiers.new("sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 2


@componente("migalhas")
def migalhas(ctx, p, rng, col):
    """Migalhas de pão espalhadas (1–6 mm), formas irregulares."""
    x0, y0, x1, y1 = p["area"]; n = p.get("n", 14); z = p.get("z", 0.0)
    for k, (x, y) in enumerate(G.espalhar(rng, (x0, y0, x1, y1), n, dist_min=p.get("dist_min", 0.006))):
        r = rng.uniform(*p.get("raio_m", (0.0008, 0.003)))
        o = G.esfera(f"migalha_{k}", (x, y, z + r * 0.55), r, pao(), col, sub=2)
        o.scale = (rng.uniform(0.8, 1.4), rng.uniform(0.7, 1.2), rng.uniform(0.45, 0.7)); o.location = (x * (1 - o.scale.x), y * (1 - o.scale.y), (z + r * 0.55) * (1 - o.scale.z))
        G.deformar_ruido(o, forca=r * 0.35, escala=r * 1.5, semente=k)
    if p.get("grande"):                                                # uma migalha "maior que o Heitor" (para a cena da força)
        gx, gy, gr = p["grande"]
        o = G.esfera("migalha_grande", (gx, gy, gr * 0.6), gr, pao(), col, sub=3)
        o.scale = (1.3, 1.0, 0.65); o.location = (gx * (1 - 1.3), 0, gr * 0.6 * (1 - 0.65))
        G.deformar_ruido(o, forca=gr * 0.3, escala=gr * 1.2, semente=99)


@componente("poeira")
def poeira(ctx, p, rng, col):
    """Grãos e fiapos de poeira no chão (só aparecem no macro): realismo de escala."""
    x0, y0, x1, y1 = p["area"]; z = p.get("z", 0.0)
    m = M.pintura("#b9ada0", rug=0.95)
    for k in range(p.get("n", 40)):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if rng.random() < 0.3:                                         # fiapo
            a = rng.uniform(0, math.tau); L = rng.uniform(0.003, 0.012)
            o = G.cilindro_eixo(f"fiapo_{k}", (x, y, z + 0.00012), (x + L * math.cos(a), y + L * math.sin(a), z + 0.00012), 0.00011, m, col, lados=6)
        else:
            o = G.esfera(f"grao_{k}", (x, y, z + 0.0002), rng.uniform(0.00012, 0.0004), m, col, sub=1)
        o["suspenso"] = True


# ------------------------------------------------------------------ parede: quadro, estante
@componente("quadro")
def quadro(ctx, p, rng, col):
    """Quadro com arte abstrata (planetas e órbitas em formas geométricas — sem texto, sem personagem)."""
    x, y, z, L, A = p["x"], p["y"], p["z"], p.get("largura", 0.5), p.get("altura", 0.7)
    mold = G.caixa("quadro_moldura", (x - L / 2, y - 0.025, z - A / 2), (x + L / 2, y, z + A / 2), M.pintura("#2c2622", rug=0.4), col, chanfro=0.004)
    fundo = G.caixa("quadro_fundo", (x - L / 2 + 0.03, y - 0.027, z - A / 2 + 0.03), (x + L / 2 - 0.03, y - 0.024, z + A / 2 - 0.03),
                    M.pintura("#1f2a44", rug=0.8), col)
    objs = [mold, fundo]
    for k, (dx, dz, r, cor) in enumerate([(-0.07, 0.1, 0.09, "#ffc21f"), (0.1, -0.12, 0.05, "#3d80d8"), (0.08, 0.17, 0.025, "#e9e4da")]):
        o = G.cilindro_eixo(f"quadro_planeta_{k}", (x + dx, y - 0.026, z + dz), (x + dx, y - 0.031, z + dz), r, M.pintura(cor, rug=0.7), col, lados=48)
        objs.append(o)
    _marcar(objs, suspenso=True)


@componente("estante")
def estante(ctx, p, rng, col):
    x0, x1, y, z0, n = p["x0"], p["x1"], p["y"], p.get("z0", 1.2), p.get("prateleiras", 2)
    m = M.madeira("#d9b48a", escala=2.5)
    cores = ["#b8403a", "#2f6aa3", "#e1b33f", "#4f8a5b", "#8b5ca8", "#e07f3a"]
    objs = []
    for k in range(n):
        z = z0 + 0.38 * k
        objs.append(G.caixa(f"prat_{k}", (x0, y - 0.24, z), (x1, y, z + 0.022), m, col, chanfro=0.002))
        xx = x0 + 0.03
        while xx < x1 - 0.06:
            if rng.random() < 0.18:
                w = rng.uniform(0.1, 0.16); objs.append(G.caixa(f"caixa_{k}_{xx:.2f}", (xx, y - 0.2, z + 0.022), (xx + w, y - 0.03, z + 0.022 + rng.uniform(0.08, 0.14)),
                                                              plastico(cores[rng.randrange(6)], 0.6), col, chanfro=0.004)); xx += w + 0.01
            else:
                w = rng.uniform(0.018, 0.035); hh = rng.uniform(0.16, 0.24)
                objs.append(G.caixa(f"livro_e_{k}_{xx:.3f}", (xx, y - 0.19, z + 0.022), (xx + w, y - 0.03, z + 0.022 + hh),
                                    plastico(cores[rng.randrange(6)], 0.55), col, chanfro=0.0012)); xx += w + 0.002
    _marcar(objs, suspenso=True)


# ------------------------------------------------------------------ E10 parte 2: escada e sala
@componente("escada")
def escada(ctx, p, rng, col):
    """Escada reta subindo em +y: degraus maciços até o chão (nada flutua), focinho com chanfro, espelho pintado,
    paredes laterais e corrimão. Medidas reais: espelho 18 cm, piso 28 cm (NBR 9050: 16–18 cm e 28–32 cm)."""
    x0, x1, y0 = p["x0"], p["x1"], p["y0"]; n = p.get("degraus", 8); e = p.get("espelho_m", 0.18); d = p.get("piso_m", 0.28)
    piso_m = M.madeira(p.get("cor_piso", "#a8774c"), escala=3.0); esp_m = M.pintura(p.get("cor_espelho", "#f1ede4"), rug=0.6, desgaste=0.1)
    for i in range(n):
        ya, yb, zt = y0 + i * d, y0 + (i + 1) * d, (i + 1) * e
        G.caixa(f"degrau_corpo_{i}", (x0, ya, 0), (x1, yb, zt - 0.025), esp_m, col)
        G.caixa(f"degrau_piso_{i}", (x0, ya - 0.02, zt - 0.025), (x1, yb, zt), piso_m, col, chanfro=0.004)["suspenso"] = True
    yf = y0 + n * d
    G.caixa("patamar", (x0, yf, 0), (x1, yf + p.get("patamar_m", 1.0), n * e), piso_m, col, chanfro=0.004)
    parede = M.pintura(p.get("cor_parede", "#e8d9bf"), rug=0.75, desgaste=0.1)
    if p.get("parede_esq", True):
        G.caixa("escada_parede_esq", (x0 - 0.12, y0 - 1.5, 0), (x0, yf + 1.0, n * e + 2.6), parede, col)
    if p.get("parede_dir", True):
        G.caixa("escada_parede_dir", (x1, y0 - 1.5, 0), (x1 + 0.12, yf + 1.0, n * e + 2.6), parede, col)
    G.caixa("escada_teto", (x0 - 0.12, y0 - 1.5, n * e + 2.6), (x1 + 0.12, yf + 1.0, n * e + 2.72), M.pintura("#f1efe9", rug=0.9), col)["suspenso"] = True
    # corrimão na parede direita (90 cm acima do focinho), com suportes
    h = 0.9; met = M.pintura("#8c8f94", rug=0.3, metal=0.8)
    a = (x1 - 0.06, y0 - 0.1, h + 0.0); b = (x1 - 0.06, yf, n * e + h)
    G.cilindro_eixo("corrimao", a, b, 0.02, met, col)["suspenso"] = True
    for k in range(3):
        t = (k + 0.5) / 3; py = a[1] + (b[1] - a[1]) * t; pz = a[2] + (b[2] - a[2]) * t
        G.cilindro_eixo(f"corrimao_suporte_{k}", (x1, py, pz - 0.05), (x1 - 0.06, py, pz - 0.02), 0.008, met, col)["suspenso"] = True
    # piso de baixo (chão do corredor) diante da escada
    G.caixa("corredor_piso", (x0 - 0.12, y0 - 1.5, -0.02), (x1 + 0.12, y0, 0.0), M.madeira(p.get("cor_corredor", "#9a6a43"), escala=3.0), col)


@componente("sofa")
def sofa(ctx, p, rng, col):
    """Sofá de 3 lugares (assento a 45 cm, encosto a 85 cm), tecido com trama, almofadas soltas, pés de madeira."""
    x, y, L, P = p["x"], p["y"], p.get("largura", 2.0), p.get("profundidade", 0.9)
    tec = tecido(p.get("cor", "#8a6f9e"), 600); mad = M.madeira("#5a3d28", escala=2.0)
    x0, x1, y0, y1 = x - L / 2, x + L / 2, y - P / 2, y + P / 2
    for i, (px, py) in enumerate([(x0 + 0.08, y0 + 0.08), (x1 - 0.08, y0 + 0.08), (x0 + 0.08, y1 - 0.08), (x1 - 0.08, y1 - 0.08)]):
        G.cilindro(f"sofa_pe_{i}", (px, py, 0), 0.022, 0.12, mad, col, lados=16, raio_topo=0.016)
    G.caixa("sofa_base", (x0, y0, 0.12), (x1, y1, 0.32), tec, col, chanfro=0.03)["suspenso"] = True
    G.caixa("sofa_encosto", (x0, y1 - 0.22, 0.32), (x1, y1, 0.85), tec, col, chanfro=0.05)
    for lado, (xa, xb) in (("esq", (x0, x0 + 0.2)), ("dir", (x1 - 0.2, x1))):
        G.caixa(f"sofa_braco_{lado}", (xa, y0, 0.32), (xb, y1 - 0.2, 0.62), tec, col, chanfro=0.05)
    n = 3; w = (L - 0.4) / n
    for k in range(n):
        c = G.caixa(f"sofa_assento_{k}", (x0 + 0.2 + k * w + 0.005, y0 + 0.02, 0.32), (x0 + 0.2 + (k + 1) * w - 0.005, y1 - 0.22, 0.45), tec, col, chanfro=0.04)
        G.deformar_ruido(c, forca=0.008, escala=0.2, semente=k)
    for k in range(2):
        a = G.caixa(f"sofa_almofada_{k}", (-0.22, -0.07, 0), (0.22, 0.07, 0.42), tecido(p.get("cor_almofada", "#e7c35a"), 600), col, chanfro=0.06)
        a.location = (x0 + 0.45 + k * (L - 0.9), y1 - 0.32, 0.45); a.rotation_euler = (math.radians(-12), 0, math.radians(rng.uniform(-8, 8)))
        a["suspenso"] = True


@componente("mesa_centro")
def mesa_centro(ctx, p, rng, col):
    x, y, L, P, A = p["x"], p["y"], p.get("largura", 0.9), p.get("profundidade", 0.5), p.get("altura", 0.4)
    m = M.madeira(p.get("cor", "#b98a5e"), escala=2.5)
    G.caixa("mesa_tampo", (x - L / 2, y - P / 2, A - 0.03), (x + L / 2, y + P / 2, A), m, col, chanfro=0.006)["suspenso"] = True
    for i, (px, py) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        G.caixa(f"mesa_pe_{i}", (x + px * (L / 2 - 0.05) - 0.025, y + py * (P / 2 - 0.05) - 0.025, 0), (x + px * (L / 2 - 0.05) + 0.025, y + py * (P / 2 - 0.05) + 0.025, A - 0.03), m, col)


@componente("luminaria_teto")
def luminaria_teto(ctx, p, rng, col):
    """Plafon redondo no teto (vidro leitoso aceso) + luz de área no grupo "artificial"."""
    x, y, z = p["x"], p["y"], p["z"]
    o = G.cilindro("plafon", (x, y, z - 0.06), 0.16, 0.06, M.emissor("#fff1d6", p.get("forca_vidro", 3.0)), col, lados=48, chanfro=0.01)
    o["suspenso"] = True; o.lightgroup = "artificial"
    L = bpy.data.lights.new("plafon_luz", "AREA"); L.shape = "DISK"; L.size = 0.3; L.energy = p.get("watts", 60.0); L.color = lin("#ffe2b8")[:3]
    lo = bpy.data.objects.new("plafon_luz", L); bpy.context.scene.collection.objects.link(lo); lo.location = (x, y, z - 0.07); lo.lightgroup = "artificial"
