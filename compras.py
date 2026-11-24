from datetime import datetime, timezone

from comum import selecionar, numero, excluir, listar
from usuarios import ler_obrigatorio


def cadastrar(db):
    usuario = selecionar(db.usuarios, "usuário")
    if usuario is None:
        return
    itens = []
    while True:
        produto = selecionar(db.produtos, "produto")
        if produto is None:
            return
        vendedor = db.vendedores.find_one({"_id": produto.get("vendedor_id")})
        if vendedor is None:
            print("Produto sem vendedor válido. Corrija o cadastro.")
            return
        quantidade = numero("Quantidade", inteiro=True)
        if quantidade == 0:
            print("A quantidade deve ser maior que zero.")
            return
        itens.append({"produto_id": produto["_id"], "vendedor_id": vendedor["_id"],
                      "quantidade": quantidade, "preco_unitario": produto["preco"]})
        if input("Adicionar outro produto? (S/N): ").strip().upper() != "S":
            break
    endereco = {}
    print("Endereço de entrega")
    for campo in ["rua", "num", "bairro", "cidade", "estado", "cep"]:
        endereco[campo] = ler_obrigatorio(campo)
    pagamento = {"forma": ler_obrigatorio("Forma de pagamento"), "status": "Pendente"}
    subtotal = round(sum(item["quantidade"] * item["preco_unitario"] for item in itens), 2)
    frete = numero("Frete")
    compra = {"usuario_id": usuario["_id"], "data_compra": datetime.now(timezone.utc),
              "itens": itens, "endereco_entrega": endereco, "pagamento": pagamento,
              "subtotal": subtotal, "frete": frete, "valor_total": round(subtotal + frete, 2),
              "status_compra": "Em preparação"}
    resultado = db.compras.insert_one(compra)
    print("Compra cadastrada. ID:", resultado.inserted_id, "Total:", compra["valor_total"])


def consultar(db):
    listar(db.compras)


def atualizar(db):
    compra = selecionar(db.compras, "compra")
    if compra is None:
        return
    print("Enter mantém o valor atual. Os itens da compra são mantidos.")
    dados = {}
    status = input(f"Status da compra [{compra.get('status_compra', '')}]: ").strip()
    if status:
        dados["status_compra"] = status
    pagamento = input("Status do pagamento (Enter mantém): ").strip()
    if pagamento:
        dados["pagamento.status"] = pagamento
    frete = numero("Frete", atual=compra.get("frete", 0))
    dados["frete"] = frete
    dados["valor_total"] = round(compra["subtotal"] + frete, 2)
    db.compras.update_one({"_id": compra["_id"]}, {"$set": dados})
    print("Compra atualizada.")


def apagar(db):
    compra = selecionar(db.compras, "compra")
    if compra is not None:
        excluir(db.compras, compra)
