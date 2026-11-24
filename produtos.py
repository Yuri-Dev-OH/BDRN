from comum import selecionar, numero, listar, excluir
from usuarios import ler_obrigatorio


def cadastrar(db):
    vendedor = selecionar(db.vendedores, "vendedor")
    if vendedor is None:
        return
    produto = {"vendedor_id": vendedor["_id"], "ativo": True}
    for campo in ["nome", "descricao", "categoria", "marca", "condicao"]:
        produto[campo] = ler_obrigatorio(campo)
    produto["preco"] = numero("Preço")
    produto["estoque"] = numero("Estoque", inteiro=True)
    resultado = db.produtos.insert_one(produto)
    print("Produto cadastrado. ID:", resultado.inserted_id)


def consultar(db):
    listar(db.produtos)


def atualizar(db):
    produto = selecionar(db.produtos, "produto")
    if produto is None:
        return
    dados = {}
    print("Enter mantém o valor atual.")
    for campo in ["nome", "descricao", "categoria", "marca", "condicao"]:
        valor = input(f"{campo} [{produto.get(campo, '')}]: ").strip()
        if valor:
            dados[campo] = valor
    dados["preco"] = numero("Preço", atual=produto.get("preco", 0))
    dados["estoque"] = numero("Estoque", inteiro=True, atual=produto.get("estoque", 0))
    if input("Trocar vendedor? (S/N): ").strip().upper() == "S":
        vendedor = selecionar(db.vendedores, "vendedor")
        if vendedor is None:
            return
        dados["vendedor_id"] = vendedor["_id"]
    ativo = input("Ativo? S/N (Enter mantém): ").strip().upper()
    if ativo in ("S", "N"):
        dados["ativo"] = ativo == "S"
    db.produtos.update_one({"_id": produto["_id"]}, {"$set": dados})
    if "nome" in dados:
        db.usuarios.update_many(
            {"favoritos.produto_id": produto["_id"]},
            {"$set": {"favoritos.$[f].nome": dados["nome"]}},
            array_filters=[{"f.produto_id": produto["_id"]}],
        )
    print("Produto atualizado.")


def apagar(db):
    produto = selecionar(db.produtos, "produto")
    if produto is None:
        return
    codigo = produto["_id"]
    if db.usuarios.find_one({"favoritos.produto_id": codigo}) or db.compras.find_one({"itens.produto_id": codigo}):
        print("Produto ligado a favoritos ou compras. Remova esses vínculos primeiro.")
        return
    excluir(db.produtos, produto)
