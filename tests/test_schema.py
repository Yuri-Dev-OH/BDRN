"""Testa índices e validadores $jsonSchema aplicados por setup_db.py."""
import unittest
from datetime import datetime

from bson import ObjectId
from pymongo.errors import DuplicateKeyError, WriteError

from tests.base import BaseTeste


class TestSchema(BaseTeste):
    def test_indices_criados(self):
        esperados = {
            "usuarios": ["cpf_1", "favoritos.produto_id_1"],
            "vendedores": ["documento_1"],
            "produtos": ["vendedor_id_1"],
            "compras": ["usuario_id_1", "itens.produto_id_1", "itens.vendedor_id_1", "vendedor_id_1"],
        }
        for colecao, nomes in esperados.items():
            existentes = self.db[colecao].index_information()
            for nome in nomes:
                self.assertIn(nome, existentes, f"{colecao}.{nome}")

    def test_cpf_unico(self):
        self.novo_usuario(cpf="1")
        with self.assertRaises(DuplicateKeyError):
            self.novo_usuario(cpf="1", nome="Outro")

    def test_documento_vendedor_unico(self):
        self.novo_vendedor(documento="1")
        with self.assertRaises(DuplicateKeyError):
            self.novo_vendedor(documento="1")

    def test_usuario_sem_cpf_rejeitado(self):
        with self.assertRaises(WriteError):
            self.db.usuarios.insert_one({"nome": "Sem CPF"})

    def test_produto_preco_invalido(self):
        vid = self.novo_vendedor()
        base = {"nome": "X", "vendedor_id": vid, "estoque": 1}
        for preco in ("10", -1):
            with self.assertRaises(WriteError, msg=f"preco={preco!r}"):
                self.db.produtos.insert_one({**base, "preco": preco})

    def test_produto_estoque_deve_ser_inteiro_nao_negativo(self):
        vid = self.novo_vendedor()
        base = {"nome": "X", "vendedor_id": vid, "preco": 1.0}
        for estoque in (1.5, -1):
            with self.assertRaises(WriteError, msg=f"estoque={estoque!r}"):
                self.db.produtos.insert_one({**base, "estoque": estoque})

    def test_produto_valido_aceita_int_e_double(self):
        vid = self.novo_vendedor()
        for preco in (10, 10.5):
            self.db.produtos.insert_one({"nome": "X", "vendedor_id": vid, "preco": preco, "estoque": 1})

    def test_compra_sem_itens_rejeitada(self):
        with self.assertRaises(WriteError):
            self.db.compras.insert_one({"usuario_id": ObjectId(), "itens": [], "valor_total": 0})

    def test_compra_quantidade_zero_rejeitada(self):
        item = {"produto_id": ObjectId(), "quantidade": 0, "preco_unitario": 1.0}
        with self.assertRaises(WriteError):
            self.db.compras.insert_one({"usuario_id": ObjectId(), "itens": [item], "valor_total": 1})

    def test_favorito_malformado_rejeitado(self):
        uid = self.novo_usuario()
        with self.assertRaises(WriteError):
            self.db.usuarios.update_one({"_id": uid}, {"$push": {"favoritos": {"produto_id": ObjectId()}}})
        with self.assertRaises(WriteError):
            self.db.usuarios.update_one({"_id": uid}, {"$push": {"favoritos": {
                "produto_id": ObjectId(), "nome": "X", "data_favoritado": "ontem"}}})

    def test_favorito_valido_aceito(self):
        uid = self.novo_usuario()
        self.db.usuarios.update_one({"_id": uid}, {"$push": {"favoritos": {
            "produto_id": ObjectId(), "nome": "X", "data_favoritado": datetime.now()}}})

    def test_vendedor_ativo_deve_ser_booleano(self):
        vid = self.novo_vendedor()
        with self.assertRaises(WriteError):
            self.db.vendedores.update_one({"_id": vid}, {"$set": {"ativo": "sim"}})


if __name__ == "__main__":
    unittest.main()
