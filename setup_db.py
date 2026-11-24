"""Cria índices e validadores `$jsonSchema` do banco.

Uso:
    python setup_db.py            # só verifica (somente leitura)
    python setup_db.py --aplicar  # cria índices e validadores

É idempotente: pode ser executado mais de uma vez.
"""
import sys

from pymongo.errors import PyMongoError

from mymongo import conectar

NUMERO = ["int", "long", "double", "decimal"]
INTEIRO = ["int", "long"]

# Índices únicos parciais: ignoram documentos sem o campo (dados antigos).
INDICES_UNICOS = [
    ("usuarios", "cpf"),
    ("vendedores", "documento"),
]

INDICES = [
    ("usuarios", "favoritos.produto_id"),
    ("produtos", "vendedor_id"),
    ("compras", "usuario_id"),
    ("compras", "itens.produto_id"),
    ("compras", "itens.vendedor_id"),
    ("compras", "vendedor_id"),  # formato antigo, usado na checagem de vendedores.apagar
]

VALIDADORES = {
    "usuarios": {
        "required": ["nome", "cpf"],
        "properties": {
            "nome": {"bsonType": "string"},
            "email": {"bsonType": "string"},
            "cpf": {"bsonType": "string"},
            "enderecos": {"bsonType": "array"},
            "favoritos": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["produto_id", "nome", "data_favoritado"],
                    "properties": {
                        "nome": {"bsonType": "string"},
                        "data_favoritado": {"bsonType": "date"},
                    },
                },
            },
        },
    },
    "vendedores": {
        "required": ["nome_loja", "documento"],
        "properties": {
            "nome_loja": {"bsonType": "string"},
            "documento": {"bsonType": "string"},
            "ativo": {"bsonType": "bool"},
            "reputacao": {"bsonType": NUMERO, "minimum": 0},
            "total_vendas": {"bsonType": NUMERO, "minimum": 0},
        },
    },
    "produtos": {
        "required": ["nome", "preco", "estoque", "vendedor_id"],
        "properties": {
            "nome": {"bsonType": "string"},
            "preco": {"bsonType": NUMERO, "minimum": 0},
            "estoque": {"bsonType": INTEIRO, "minimum": 0},
            "ativo": {"bsonType": "bool"},
        },
    },
    "compras": {
        "required": ["usuario_id", "itens", "valor_total"],
        "properties": {
            "itens": {
                "bsonType": "array",
                "minItems": 1,
                "items": {
                    "bsonType": "object",
                    "required": ["produto_id", "quantidade", "preco_unitario"],
                    "properties": {
                        "quantidade": {"bsonType": INTEIRO, "minimum": 1},
                        "preco_unitario": {"bsonType": NUMERO, "minimum": 0},
                    },
                },
            },
            "subtotal": {"bsonType": NUMERO, "minimum": 0},
            "frete": {"bsonType": NUMERO, "minimum": 0},
            "valor_total": {"bsonType": NUMERO, "minimum": 0},
        },
    },
}


def duplicados(colecao, campo):
    """Retorna valores de `campo` repetidos na coleção."""
    pipeline = [
        {"$match": {campo: {"$type": "string"}}},
        {"$group": {"_id": "$" + campo, "n": {"$sum": 1}}},
        {"$match": {"n": {"$gt": 1}}},
    ]
    return [d["_id"] for d in colecao.aggregate(pipeline)]


def aplicar_schema(db):
    """Cria índices e validadores no banco `db`."""
    for nome, campo in INDICES_UNICOS:
        db[nome].create_index(
            campo, unique=True, partialFilterExpression={campo: {"$type": "string"}}
        )
        print(f"Índice único: {nome}.{campo}")
    for nome, campo in INDICES:
        db[nome].create_index(campo)
        print(f"Índice: {nome}.{campo}")
    # Os índices acima já criam as coleções ausentes, então collMod serve para todas.
    for nome, schema in VALIDADORES.items():
        validador = {"$jsonSchema": {"bsonType": "object", **schema}}
        db.command("collMod", nome, validator=validador, validationLevel="moderate")
        print(f"Validador: {nome}")


def main():
    aplicar = "--aplicar" in sys.argv
    client, db = conectar()
    try:
        problemas = False
        for nome, campo in INDICES_UNICOS:
            repetidos = duplicados(db[nome], campo)
            if repetidos:
                problemas = True
                print(f"DUPLICADOS em {nome}.{campo}: {repetidos}")
        if problemas:
            print("Corrija os duplicados antes de criar os índices únicos.")
            return
        print("Sem duplicados em campos únicos.")
        if not aplicar:
            print("Modo verificação. Use --aplicar para criar índices e validadores.")
            return

        aplicar_schema(db)
    finally:
        client.close()


if __name__ == "__main__":
    try:
        main()
    except PyMongoError as erro:
        print("Erro no MongoDB:", erro)
