import unittest

from bson import ObjectId

import compras
from tests.base import BaseTeste, ENDERECO


class TestCompras(BaseTeste):
    def setUp(self):
        super().setUp()
        self.vid = self.novo_vendedor()
        self.vid2 = self.novo_vendedor(documento="2")
        self.uid = self.novo_usuario()
        self.p1 = self.novo_produto(self.vid, nome="Notebook", preco=100.0)
        self.p2 = self.novo_produto(self.vid2, nome="Mouse", preco=50.5)

    def comprar(self, itens, frete="10", pagamento="Cartão"):
        entradas = [str(self.uid)]
        for i, (pid, qtd) in enumerate(itens):
            entradas += [str(pid), str(qtd), "S" if i < len(itens) - 1 else "N"]
        entradas += ENDERECO + [pagamento, frete]
        return self.rodar(compras.cadastrar, self.db, entradas=entradas)

    # Create
    def test_cadastrar_com_dois_vendedores(self):
        self.assertIn("Compra cadastrada", self.comprar([(self.p1, 2), (self.p2, 1)]))
        c = self.db.compras.find_one()
        self.assertEqual(c["usuario_id"], self.uid)
        self.assertEqual(len(c["itens"]), 2)
        self.assertEqual({i["vendedor_id"] for i in c["itens"]}, {self.vid, self.vid2})
        self.assertEqual((c["subtotal"], c["frete"], c["valor_total"]), (250.5, 10.0, 260.5))
        self.assertEqual(c["status_compra"], "Em preparação")
        self.assertEqual(c["pagamento"], {"forma": "Cartão", "status": "Pendente"})
        self.assertEqual(c["endereco_entrega"]["cep"], "12200000")

    def test_cadastrar_quantidade_zero(self):
        saida = self.rodar(compras.cadastrar, self.db, entradas=[str(self.uid), str(self.p1), "0"])
        self.assertIn("maior que zero", saida)
        self.assertEqual(self.db.compras.count_documents({}), 0)

    def test_cadastrar_produto_sem_vendedor_valido(self):
        orfao = self.novo_produto(ObjectId(), nome="Orfao")
        saida = self.rodar(compras.cadastrar, self.db,
                           entradas=[str(self.uid), str(orfao), "1"])
        self.assertIn("sem vendedor válido", saida)
        self.assertEqual(self.db.compras.count_documents({}), 0)

    def test_cadastrar_usuario_inexistente(self):
        saida = self.rodar(compras.cadastrar, self.db, entradas=[self.id_inexistente()])
        self.assertIn("não encontrado", saida)

    def test_preco_na_compra_e_snapshot(self):
        self.comprar([(self.p1, 1)])
        self.db.produtos.update_one({"_id": self.p1}, {"$set": {"preco": 999.0}})
        self.assertEqual(self.db.compras.find_one()["itens"][0]["preco_unitario"], 100.0)

    # Read
    def test_consultar(self):
        cid = self.nova_compra(self.uid, self.p1, self.vid)
        self.assertIn("Em preparação", self.rodar(compras.consultar, self.db, entradas=[str(cid)]))
        self.assertIn("Em preparação", self.rodar(compras.consultar, self.db, entradas=[""]))

    # Update
    def test_atualizar_status_pagamento_e_frete(self):
        cid = self.nova_compra(self.uid, self.p1, self.vid)
        self.rodar(compras.atualizar, self.db, entradas=[str(cid), "Enviado", "Pago", "20"])
        c = self.db.compras.find_one({"_id": cid})
        self.assertEqual(c["status_compra"], "Enviado")
        self.assertEqual(c["pagamento.status"] if "pagamento.status" in c else c["pagamento"]["status"], "Pago")
        self.assertEqual((c["frete"], c["valor_total"]), (20.0, 120.0))
        self.assertEqual(len(c["itens"]), 1)

    def test_atualizar_enter_mantem(self):
        cid = self.nova_compra(self.uid, self.p1, self.vid)
        self.rodar(compras.atualizar, self.db, entradas=[str(cid), "", "", ""])
        c = self.db.compras.find_one({"_id": cid})
        self.assertEqual((c["status_compra"], c["frete"], c["valor_total"]), ("Em preparação", 0.0, 100.0))

    # Delete
    def test_apagar(self):
        cid = self.nova_compra(self.uid, self.p1, self.vid)
        self.rodar(compras.apagar, self.db, entradas=[str(cid), "S"])
        self.assertEqual(self.db.compras.count_documents({}), 0)

    def test_apagar_cancelado(self):
        cid = self.nova_compra(self.uid, self.p1, self.vid)
        self.rodar(compras.apagar, self.db, entradas=[str(cid), "N"])
        self.assertEqual(self.db.compras.count_documents({}), 1)

    def test_apagar_libera_exclusao_de_produto_e_usuario(self):
        import produtos
        import usuarios
        cid = self.nova_compra(self.uid, self.p1, self.vid)
        self.rodar(compras.apagar, self.db, entradas=[str(cid), "S"])
        self.rodar(produtos.apagar, self.db, entradas=[str(self.p1), "S"])
        self.rodar(usuarios.excluir_usuario, self.db.usuarios, entradas=[str(self.uid), "S"])
        self.assertIsNone(self.db.produtos.find_one({"_id": self.p1}))
        self.assertIsNone(self.db.usuarios.find_one({"_id": self.uid}))


if __name__ == "__main__":
    unittest.main()
