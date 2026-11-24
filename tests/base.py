"""Infraestrutura comum dos testes.

Os testes usam um banco temporário (`db_mercado_livre_test_<uuid>`) no mesmo
cluster, com os mesmos índices e validadores do banco real. O banco real
(`db_mercado_livre`) nunca é tocado. O banco temporário é apagado ao final.
"""
import io
import unittest
import uuid
from contextlib import redirect_stdout
from datetime import datetime, timezone
from unittest.mock import patch

from bson import ObjectId

from mymongo import conectar
from setup_db import aplicar_schema

COLECOES = ["usuarios", "vendedores", "produtos", "compras"]
ENDERECO = ["Rua A", "10", "Centro", "São José", "SP", "12200000"]


class BaseTeste(unittest.TestCase):
    client = None
    db = None

    @classmethod
    def setUpClass(cls):
        cls.client, _ = conectar()
        cls.db = cls.client["db_mercado_livre_test_" + uuid.uuid4().hex[:8]]
        # Registrado antes do setup: roda mesmo que aplicar_schema falhe.
        cls.addClassCleanup(cls._limpar)
        with redirect_stdout(io.StringIO()):
            aplicar_schema(cls.db)

    @classmethod
    def _limpar(cls):
        cls.client.drop_database(cls.db.name)
        cls.client.close()

    def setUp(self):
        for nome in COLECOES:
            self.db[nome].delete_many({})

    def rodar(self, funcao, *args, entradas=()):
        """Executa `funcao` simulando `input()` com `entradas`; devolve o stdout.

        Se a função pedir mais entradas do que o fornecido, o teste falha
        (StopIteration), o que denuncia desalinhamento com o fluxo real.
        """
        saida = io.StringIO()
        with patch("builtins.input", side_effect=list(entradas)), redirect_stdout(saida):
            funcao(*args)
        return saida.getvalue()

    # Fixtures inseridas direto no banco (isolam o teste da função testada).
    def novo_usuario(self, cpf="11111111111", nome="Ana", favoritos=None):
        doc = {"nome": nome, "email": "a@x.com", "telefone": "1199", "cpf": cpf,
               "senha": "hash", "enderecos": []}
        if favoritos is not None:
            doc["favoritos"] = favoritos
        return self.db.usuarios.insert_one(doc).inserted_id

    def novo_vendedor(self, documento="99999999000100"):
        return self.db.vendedores.insert_one({
            "nome_loja": "Loja", "nome_responsavel": "Zé", "email": "l@x.com",
            "telefone": "1188", "documento": documento, "tipo_documento": "CNPJ",
            "reputacao": 0, "total_vendas": 0, "ativo": True}).inserted_id

    def novo_produto(self, vendedor_id, nome="Notebook", preco=100.0, estoque=5):
        return self.db.produtos.insert_one({
            "vendedor_id": vendedor_id, "ativo": True, "nome": nome, "descricao": "d",
            "categoria": "c", "marca": "m", "condicao": "Novo",
            "preco": preco, "estoque": estoque}).inserted_id

    def nova_compra(self, usuario_id, produto_id, vendedor_id):
        return self.db.compras.insert_one({
            "usuario_id": usuario_id, "data_compra": datetime.now(timezone.utc),
            "itens": [{"produto_id": produto_id, "vendedor_id": vendedor_id,
                       "quantidade": 1, "preco_unitario": 100.0}],
            "subtotal": 100.0, "frete": 0.0, "valor_total": 100.0,
            "status_compra": "Em preparação"}).inserted_id

    @staticmethod
    def id_inexistente():
        return str(ObjectId())
