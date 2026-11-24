import unittest

import vendedores
from tests.base import BaseTeste

CAMPOS = ["Loja X", "João", "j@x.com", "1177", "12345678000199", "CNPJ"]


class TestVendedores(BaseTeste):
    def test_cadastrar(self):
        self.rodar(vendedores.cadastrar, self.db, entradas=CAMPOS)
        v = self.db.vendedores.find_one({"documento": "12345678000199"})
        self.assertEqual(v["nome_loja"], "Loja X")
        self.assertEqual((v["reputacao"], v["total_vendas"], v["ativo"]), (0, 0, True))

    def test_cadastrar_documento_duplicado(self):
        self.rodar(vendedores.cadastrar, self.db, entradas=CAMPOS)
        saida = self.rodar(vendedores.cadastrar, self.db, entradas=CAMPOS)
        self.assertIn("já cadastrado", saida)
        self.assertEqual(self.db.vendedores.count_documents({}), 1)

    def test_consultar(self):
        vid = self.novo_vendedor()
        saida = self.rodar(vendedores.consultar, self.db, entradas=[str(vid)])
        self.assertIn("Loja", saida)
        saida = self.rodar(vendedores.consultar, self.db, entradas=[""])
        self.assertIn("Loja", saida)

    def test_atualizar(self):
        vid = self.novo_vendedor()
        self.rodar(vendedores.atualizar, self.db,
                   entradas=[str(vid), "Loja Nova", "", "", "", "", "", "N"])
        v = self.db.vendedores.find_one({"_id": vid})
        self.assertEqual(v["nome_loja"], "Loja Nova")
        self.assertEqual(v["email"], "l@x.com")
        self.assertFalse(v["ativo"])

    def test_atualizar_documento_duplicado(self):
        self.novo_vendedor(documento="1")
        vid = self.novo_vendedor(documento="2")
        saida = self.rodar(vendedores.atualizar, self.db,
                           entradas=[str(vid), "", "", "", "", "1", "", ""])
        self.assertIn("já cadastrado", saida)
        self.assertEqual(self.db.vendedores.find_one({"_id": vid})["documento"], "2")

    def test_apagar(self):
        vid = self.novo_vendedor()
        self.rodar(vendedores.apagar, self.db, entradas=[str(vid), "S"])
        self.assertEqual(self.db.vendedores.count_documents({}), 0)

    def test_apagar_bloqueado_por_produto(self):
        vid = self.novo_vendedor()
        self.novo_produto(vid)
        saida = self.rodar(vendedores.apagar, self.db, entradas=[str(vid)])
        self.assertIn("ligado a produtos ou compras", saida)
        self.assertEqual(self.db.vendedores.count_documents({}), 1)

    def test_apagar_bloqueado_por_compra(self):
        vid = self.novo_vendedor()
        uid = self.novo_usuario()
        pid = self.novo_produto(self.novo_vendedor(documento="2"))
        self.nova_compra(uid, pid, vid)
        saida = self.rodar(vendedores.apagar, self.db, entradas=[str(vid)])
        self.assertIn("ligado a produtos ou compras", saida)


if __name__ == "__main__":
    unittest.main()
