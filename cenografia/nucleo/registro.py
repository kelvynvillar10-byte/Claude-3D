"""Cenografia — registro de COMPONENTES (E0).

Um componente é uma função geradora registrada por nome:  @componente("predio_bloco")
def predio(ctx, params, rng, col): ...   (cria objetos bpy na coleção 'col', usando só 'params' e 'rng')
A receita chama os componentes pelo nome. Novos kits (E1–E5) só registram funções novas: o núcleo não muda.
ctx: dict com 'cena', 'receita', 'luz' (funções de luz), 'mat' (biblioteca de materiais), 'geo' (geometria).
"""
REGISTRO = {}


def componente(nome):
    def dec(f):
        if nome in REGISTRO:
            raise ValueError(f"componente '{nome}' registrado duas vezes")
        REGISTRO[nome] = f
        f.nome_componente = nome
        return f
    return dec


def carregar_kits():
    """Importa os módulos de componentes (cada import registra os seus)."""
    import importlib, pkgutil
    import cenografia.componentes as pacote
    for m in pkgutil.iter_modules(pacote.__path__):
        importlib.import_module(f"cenografia.componentes.{m.name}")
    return REGISTRO
