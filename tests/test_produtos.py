import unittest

import favoritos
import produtos
from tests.base import BaseTeste

CAMPOS = ["Notebook", "desc", "Info", "Dell", "Novo"]


class TestProdutos(BaseTeste):
    def test_cadastrar(self):
        vid = self.novo_vendedor()
        self.rodar(produtos.cadastrar, self.db, entradas=[str(vid)] + CAMPOS + ["3999,90", "5"])
        p = self.db.produtos.find_one({"nome": "Notebook"})
        self.assertEqual((p["preco"], p["estoque"], p["ativo"]), (3999.9, 5, True))
        self.assertEqual(p["vendedor_id"], vid)

    def test_cadastrar_vendedor_inexistente(self):
        saida = self.rodar(produtos.cadastrar, self.db, entradas=[self.id_inexistente()])
        self.assertIn("não encontrado", saida)
        self.assertEqual(self.db.produtos.count_documents({}), 0)

    def test_cadastrar_numero_invalido_reprompt(self):
        vid = self.novo_vendedor()
        self.rodar(produtos.cadastrar, self.db,
                   entradas=[str(vid)] + CAMPOS + ["abc", "-5", "10", "x", "1,5", "3"])
        p = self.db.produtos.find_one()
        self.assertEqual((p["preco"], p["estoque"]), (10.0, 3))

    def test_consultar(self):
        pid = self.novo_produto(self.novo_vendedor())
        self.assertIn("Notebook", self.rodar(produtos.consultar, self.db, entradas=[str(pid)]))
        self.assertIn("Notebook", self.rodar(produtos.consultar, self.db, entradas=[""]))

    def test_atualizar_campos(self):
        pid = self.novo_produto(self.novo_vendedor())
        self.rodar(produtos.atualizar, self.db,
                   entradas=[str(pid), "Novo nome", "", "", "", "", "99,5", "7", "N", "N"])
        p = self.db.produtos.find_one({"_id": pid})
        self.assertEqual((p["nome"], p["preco"], p["estoque"], p["ativo"]), ("Novo nome", 99.5, 7, False))
        self.assertEqual(p["marca"], "m")

    def test_atualizar_mantem_numeros_com_enter(self):
        pid = self.novo_produto(self.novo_vendedor(), preco=50.0, estoque=2)
        self.rodar(produtos.atualizar, self.db,
                   entradas=[str(pid), "", "", "", "", "", "", "", "N", ""])
        p = self.db.produtos.find_one({"_id": pid})
        self.assertEqual((p["preco"], p["estoque"]), (50.0, 2))

    def test_atualizar_trocar_vendedor(self):
        v2 = self.novo_vendedor(documento="2")
        pid = self.novo_produto(self.novo_vendedor())
        self.rodar(produtos.atualizar, self.db,
                   entradas=[str(pid), "", "", "", "", "", "", "", "S", str(v2), ""])
        self.assertEqual(self.db.produtos.find_one({"_id": pid})["vendedor_id"], v2)

    def test_renomear_atualiza_nome_nos_favoritos(self):
        pid = self.novo_produto(self.novo_vendedor())
        outro = self.novo_produto(self.novo_vendedor(documento="2"), nome="Mouse")
        u1 = self.novo_usuario(cpf="1")
        u2 = self.novo_usuario(cpf="2")
        for uid in (u1, u2):
            for prod in (pid, outro):
                self.rodar(favoritos.cadastrar, self.db, entradas=[str(uid), str(prod)])
        self.rodar(produtos.atualizar, self.db,
                   entradas=[str(pid), "Notebook Pro", "", "", "", "", "", "", "N", ""])
        for uid in (u1, u2):
            nomes = {f["produto_id"]: f["nome"] for f in self.db.usuarios.find_one({"_id": uid})["favoritos"]}
            self.assertEqual(nomes[pid], "Notebook Pro")
            self.assertEqual(nomes[outro], "Mouse")

    def test_apagar(self):
        pid = self.novo_produto(self.novo_vendedor())
        self.rodar(produtos.apagar, self.db, entradas=[str(pid), "S"])
        self.assertEqual(self.db.produtos.count_documents({}), 0)

    def test_apagar_bloqueado_por_favorito(self):
        pid = self.novo_produto(self.novo_vendedor())
        uid = self.novo_usuario()
        self.rodar(favoritos.cadastrar, self.db, entradas=[str(uid), str(pid)])
        saida = self.rodar(produtos.apagar, self.db, entradas=[str(pid)])
        self.assertIn("ligado a favoritos ou compras", saida)
        self.assertEqual(self.db.produtos.count_documents({}), 1)

    def test_apagar_bloqueado_por_compra(self):
        vid = self.novo_vendedor()
        pid = self.novo_produto(vid)
        self.nova_compra(self.novo_usuario(), pid, vid)
        saida = self.rodar(produtos.apagar, self.db, entradas=[str(pid)])
        self.assertIn("ligado a favoritos ou compras", saida)


if __name__ == "__main__":
    unittest.main()
