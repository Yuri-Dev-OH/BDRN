"""Favoritos embutidos no documento do usuário (campo `favoritos`).

Cada favorito tem o formato:
    {"produto_id": ..., "nome": str, "data_favoritado": datetime}
"""
from datetime import datetime, timezone

from comum import selecionar, converter_id


def montar_favorito(produto):
    """Cria o subdocumento de favorito a partir de um produto."""
    return {
        "produto_id": produto["_id"],
        "nome": produto.get("nome", ""),
        "data_favoritado": datetime.now(timezone.utc),
    }


def ja_favoritou(db, usuario_id, produto_id):
    return db.usuarios.find_one({"_id": usuario_id, "favoritos.produto_id": produto_id}) is not None


def cadastrar(db):
    usuario = selecionar(db.usuarios, "usuário")
    if usuario is None:
        return
    produto = selecionar(db.produtos, "produto")
    if produto is None:
        return
    if ja_favoritou(db, usuario["_id"], produto["_id"]):
        print("Esse produto já está nos favoritos do usuário.")
        return
    db.usuarios.update_one({"_id": usuario["_id"]}, {"$push": {"favoritos": montar_favorito(produto)}})
    print("Favorito cadastrado.")


def consultar(db):
    texto = input("ID do usuário (Enter lista todos com favoritos): ").strip()
    filtro = {"favoritos.0": {"$exists": True}}
    if texto:
        codigo = converter_id(texto)
        if codigo is None:
            return
        filtro = {"_id": codigo}
    encontrou = False
    for usuario in db.usuarios.find(filtro, {"nome": 1, "favoritos": 1}):
        print({"usuario_id": usuario["_id"], "nome": usuario.get("nome"), "favoritos": usuario.get("favoritos", [])})
        encontrou = True
    if not encontrou:
        print("Nenhum registro encontrado.")


def selecionar_favorito(usuario):
    """Pede o ID do produto favoritado e devolve o favorito do usuário."""
    if not usuario.get("favoritos"):
        print("O usuário não tem favoritos.")
        return None
    codigo = converter_id(input("ID do produto favoritado: ").strip())
    if codigo is None:
        return None
    for favorito in usuario["favoritos"]:
        if favorito["produto_id"] == codigo:
            return favorito
    print("Favorito não encontrado.")
    return None


def atualizar(db):
    usuario = selecionar(db.usuarios, "usuário")
    if usuario is None:
        return
    favorito = selecionar_favorito(usuario)
    if favorito is None:
        return
    print("Informe o novo produto do favorito.")
    produto = selecionar(db.produtos, "produto")
    if produto is None:
        return
    if produto["_id"] != favorito["produto_id"] and ja_favoritou(db, usuario["_id"], produto["_id"]):
        print("Esse favorito já existe.")
        return
    db.usuarios.update_one(
        {"_id": usuario["_id"], "favoritos.produto_id": favorito["produto_id"]},
        {"$set": {"favoritos.$": montar_favorito(produto)}},
    )
    print("Favorito atualizado.")


def apagar(db):
    usuario = selecionar(db.usuarios, "usuário")
    if usuario is None:
        return
    favorito = selecionar_favorito(usuario)
    if favorito is None:
        return
    if input("Confirmar exclusão? (S/N): ").strip().upper() != "S":
        print("Exclusão cancelada.")
        return
    resultado = db.usuarios.update_one(
        {"_id": usuario["_id"]}, {"$pull": {"favoritos": {"produto_id": favorito["produto_id"]}}}
    )
    print("Favorito excluído." if resultado.modified_count else "Favorito não encontrado.")
