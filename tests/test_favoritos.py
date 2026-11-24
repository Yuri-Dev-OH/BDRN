import unittest
from datetime import datetime

import favoritos
from tests.base import BaseTeste


class TestFavoritos(BaseTeste):
    def setUp(self):
        super().setUp()
        vid = self.novo_vendedor()
        self.uid = self.novo_usuario()
        self.p1 = self.novo_produto(vid, nome="Notebook")
        self.p2 = self.novo_produto(vid, nome="Mouse")

    def favoritos_do_usuario(self):
        return self.db.usuarios.find_one({"_id": self.uid}).get("favoritos", [])

    def favoritar(self, produto):
        return self.rodar(favoritos.cadastrar, self.db, entradas=[str(self.uid), str(produto)])

    def test_colecao_favoritos_nao_e_usada(self):
        self.favoritar(self.p1)
        self.assertNotIn("favoritos", self.db.list_collection_names())

    def test_cadastrar(self):
        self.assertIn("Favorito cadastrado", self.favoritar(self.p1))
        (fav,) = self.favoritos_do_usuario()
        self.assertEqual(fav["produto_id"], self.p1)
        self.assertEqual(fav["nome"], "Notebook")
        self.assertIsInstance(fav["data_favoritado"], datetime)
        self.assertEqual(set(fav), {"produto_id", "nome", "data_favoritado"})

    def test_cadastrar_varios(self):
        self.favoritar(self.p1)
        self.favoritar(self.p2)
        self.assertEqual(len(self.favoritos_do_usuario()), 2)

    def test_cadastrar_duplicado(self):
        self.favoritar(self.p1)
        self.assertIn("já está nos favoritos", self.favoritar(self.p1))
        self.assertEqual(len(self.favoritos_do_usuario()), 1)

    def test_cadastrar_usuario_ou_produto_inexistente(self):
        saida = self.rodar(favoritos.cadastrar, self.db, entradas=[self.id_inexistente()])
        self.assertIn("não encontrado", saida)
        saida = self.rodar(favoritos.cadastrar, self.db, entradas=[str(self.uid), self.id_inexistente()])
        self.assertIn("não encontrado", saida)
        self.assertEqual(self.favoritos_do_usuario(), [])

    def test_consultar_por_usuario(self):
        self.favoritar(self.p1)
        saida = self.rodar(favoritos.consultar, self.db, entradas=[str(self.uid)])
        self.assertIn("Notebook", saida)

    def test_consultar_todos_lista_so_quem_tem_favoritos(self):
        self.novo_usuario(cpf="2", nome="SemFavoritos")
        self.favoritar(self.p1)
        saida = self.rodar(favoritos.consultar, self.db, entradas=[""])
        self.assertIn("Notebook", saida)
        self.assertNotIn("SemFavoritos", saida)

    def test_consultar_sem_resultado(self):
        saida = self.rodar(favoritos.consultar, self.db, entradas=[""])
        self.assertIn("Nenhum registro", saida)

    def test_atualizar_troca_produto_e_renova_data(self):
        self.favoritar(self.p1)
        antes = self.favoritos_do_usuario()[0]["data_favoritado"]
        self.rodar(favoritos.atualizar, self.db, entradas=[str(self.uid), str(self.p1), str(self.p2)])
        (fav,) = self.favoritos_do_usuario()
        self.assertEqual((fav["produto_id"], fav["nome"]), (self.p2, "Mouse"))
        self.assertGreaterEqual(fav["data_favoritado"], antes)

    def test_atualizar_para_produto_ja_favoritado(self):
        self.favoritar(self.p1)
        self.favoritar(self.p2)
        saida = self.rodar(favoritos.atualizar, self.db,
                           entradas=[str(self.uid), str(self.p1), str(self.p2)])
        self.assertIn("já existe", saida)
        self.assertEqual([f["produto_id"] for f in self.favoritos_do_usuario()], [self.p1, self.p2])

    def test_atualizar_favorito_inexistente(self):
        self.favoritar(self.p1)
        saida = self.rodar(favoritos.atualizar, self.db, entradas=[str(self.uid), str(self.p2)])
        self.assertIn("Favorito não encontrado", saida)

    def test_atualizar_usuario_sem_favoritos(self):
        saida = self.rodar(favoritos.atualizar, self.db, entradas=[str(self.uid)])
        self.assertIn("não tem favoritos", saida)

    def test_apagar(self):
        self.favoritar(self.p1)
        self.favoritar(self.p2)
        self.rodar(favoritos.apagar, self.db, entradas=[str(self.uid), str(self.p1), "S"])
        self.assertEqual([f["produto_id"] for f in self.favoritos_do_usuario()], [self.p2])

    def test_apagar_cancelado(self):
        self.favoritar(self.p1)
        saida = self.rodar(favoritos.apagar, self.db, entradas=[str(self.uid), str(self.p1), "N"])
        self.assertIn("cancelada", saida)
        self.assertEqual(len(self.favoritos_do_usuario()), 1)

    def test_favoritos_isolados_por_usuario(self):
        outro = self.novo_usuario(cpf="2", nome="Bruno")
        self.favoritar(self.p1)
        self.rodar(favoritos.cadastrar, self.db, entradas=[str(outro), str(self.p1)])
        self.rodar(favoritos.apagar, self.db, entradas=[str(self.uid), str(self.p1), "S"])
        self.assertEqual(self.favoritos_do_usuario(), [])
        self.assertEqual(len(self.db.usuarios.find_one({"_id": outro})["favoritos"]), 1)


if __name__ == "__main__":
    unittest.main()
