import math

from bson import ObjectId


def converter_id(texto):
    if ObjectId.is_valid(texto):
        return ObjectId(texto)
    elif texto.isascii() and texto.isdigit() and len(texto) <= 18:
        return int(texto)
    else:
        print("ID inválido. Copie o ID da listagem.")
        return None


def selecionar(colecao, rotulo):
    codigo = converter_id(input(f"ID de {rotulo}: ").strip())
    if codigo is None:
        return None
    registro = colecao.find_one({"_id": codigo})
    if registro is None:
        print("Registro não encontrado.")
    return registro


def numero(campo, inteiro=False, atual=None):
    while True:
        texto = input(f"{campo}" + (f" [{atual}]" if atual is not None else "") + ": ").strip()
        if not texto and atual is not None:
            return atual
        try:
            valor = int(texto) if inteiro else round(float(texto.replace(",", ".")), 2)
            if math.isfinite(valor) and 0 <= valor <= 1000000000:
                return valor
        except ValueError:
            pass
        print("Informe um número válido, não negativo" + (" e inteiro." if inteiro else "."))


def listar(colecao):
    texto = input("ID do registro (Enter lista todos): ").strip()
    filtro = {}
    if texto:
        codigo = converter_id(texto)
        if codigo is None:
            return
        filtro = {"_id": codigo}
    encontrou = False
    for registro in colecao.find(filtro, {"senha": 0}):
        print(registro)
        encontrou = True
    if not encontrou:
        print("Nenhum registro encontrado.")


def excluir(colecao, registro):
    if input("Confirmar exclusão? (S/N): ").strip().upper() == "S":
        resultado = colecao.delete_one({"_id": registro["_id"]})
        print("Registro excluído." if resultado.deleted_count else "Registro não encontrado.")
    else:
        print("Exclusão cancelada.")
