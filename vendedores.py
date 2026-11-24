from comum import selecionar, listar, excluir
from usuarios import ler_obrigatorio


def cadastrar(db):
    vendedor = {}
    for campo in ["nome_loja", "nome_responsavel", "email", "telefone", "documento", "tipo_documento"]:
        vendedor[campo] = ler_obrigatorio(campo)
    if db.vendedores.find_one({"documento": vendedor["documento"]}):
        print("Documento já cadastrado.")
        return
    vendedor.update({"reputacao": 0, "total_vendas": 0, "ativo": True})
    resultado = db.vendedores.insert_one(vendedor)
    print("Vendedor cadastrado. ID:", resultado.inserted_id)


def consultar(db):
    listar(db.vendedores)


def atualizar(db):
    vendedor = selecionar(db.vendedores, "vendedor")
    if vendedor is None:
        return
    dados = {}
    print("Enter mantém o valor atual.")
    for campo in ["nome_loja", "nome_responsavel", "email", "telefone", "documento", "tipo_documento"]:
        valor = input(f"{campo} [{vendedor.get(campo, '')}]: ").strip()
        if valor:
            dados[campo] = valor
    if "documento" in dados and db.vendedores.find_one({"documento": dados["documento"], "_id": {"$ne": vendedor["_id"]}}):
        print("Documento já cadastrado.")
        return
    ativo = input("Ativo? S/N (Enter mantém): ").strip().upper()
    if ativo in ("S", "N"):
        dados["ativo"] = ativo == "S"
    if dados:
        db.vendedores.update_one({"_id": vendedor["_id"]}, {"$set": dados})
        print("Vendedor atualizado.")


def apagar(db):
    vendedor = selecionar(db.vendedores, "vendedor")
    if vendedor is None:
        return
    codigo = vendedor["_id"]
    if db.produtos.find_one({"vendedor_id": codigo}) or db.compras.find_one({"$or": [{"itens.vendedor_id": codigo}, {"vendedor_id": codigo}]}):
        print("Vendedor ligado a produtos ou compras. Remova esses vínculos primeiro.")
        return
    excluir(db.vendedores, vendedor)
