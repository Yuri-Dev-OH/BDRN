"""Fluxo ponta a ponta usando apenas as funções dos módulos (como no menu)."""
import unittest

import compras
import favoritos
import produtos
import usuarios
import vendedores
from tests.base import BaseTeste, ENDERECO


class TestFluxoCompleto(BaseTeste):
    def test_crud_completo_em_todas_as_colecoes(self):
        db = self.db

        # CREATE
        self.rodar(vendedores.cadastrar, db,
                   entradas=["Loja", "João", "j@x.com", "1177", "123", "CNPJ"])
        vid = db.vendedores.find_one()["_id"]
        self.rodar(produtos.cadastrar, db,
                   entradas=[str(vid), "Notebook", "d", "Info", "Dell", "Novo", "100", "5"])
        pid = db.produtos.find_one()["_id"]
        self.rodar(usuarios.criar_usuario, db.usuarios,
                   entradas=["Ana", "a@x.com", "1199", "111", "senha"] + ENDERECO + ["N"])
        uid = db.usuarios.find_one()["_id"]
        self.rodar(favoritos.cadastrar, db, entradas=[str(uid), str(pid)])
        self.rodar(compras.cadastrar, db,
                   entradas=[str(uid), str(pid), "2", "N"] + ENDERECO + ["Pix", "10"])
        cid = db.compras.find_one()["_id"]
        for nome in ("vendedores", "produtos", "usuarios", "compras"):
            self.assertEqual(db[nome].count_documents({}), 1, nome)

        # READ
        for funcao, entrada, texto in [
            (vendedores.consultar, str(vid), "Loja"),
            (produtos.consultar, str(pid), "Notebook"),
            (usuarios.listar_usuarios, str(uid), "Ana"),
            (favoritos.consultar, str(uid), "Notebook"),
            (compras.consultar, str(cid), "Em preparação"),
        ]:
            alvo = db.usuarios if funcao is usuarios.listar_usuarios else db
            self.assertIn(texto, self.rodar(funcao, alvo, entradas=[entrada]))

        # UPDATE
        self.rodar(vendedores.atualizar, db, entradas=[str(vid), "Loja 2", "", "", "", "", "", ""])
        self.rodar(produtos.atualizar, db,
                   entradas=[str(pid), "Notebook 2", "", "", "", "", "150", "", "N", ""])
        self.rodar(usuarios.atualizar_usuario, db.usuarios,
                   entradas=[str(uid), "Ana 2", "", "", "", "", "N"])
        self.rodar(compras.atualizar, db, entradas=[str(cid), "Enviado", "Pago", ""])
        self.assertEqual(db.vendedores.find_one()["nome_loja"], "Loja 2")
        self.assertEqual(db.produtos.find_one()["preco"], 150.0)
        self.assertEqual(db.usuarios.find_one()["nome"], "Ana 2")
        self.assertEqual(db.usuarios.find_one()["favoritos"][0]["nome"], "Notebook 2")
        self.assertEqual(db.compras.find_one()["status_compra"], "Enviado")

        # DELETE: tudo bloqueado enquanto houver vínculos
        self.assertIn("ligado", self.rodar(vendedores.apagar, db, entradas=[str(vid)]))
        self.assertIn("ligado", self.rodar(produtos.apagar, db, entradas=[str(pid)]))
        self.assertIn("ligado", self.rodar(usuarios.excluir_usuario, db.usuarios, entradas=[str(uid), "S"]))

        # DELETE na ordem correta
        self.rodar(compras.apagar, db, entradas=[str(cid), "S"])
        self.rodar(favoritos.apagar, db, entradas=[str(uid), str(pid), "S"])
        self.assertEqual(db.usuarios.find_one()["favoritos"], [])
        self.rodar(produtos.apagar, db, entradas=[str(pid), "S"])
        self.rodar(vendedores.apagar, db, entradas=[str(vid), "S"])
        self.rodar(usuarios.excluir_usuario, db.usuarios, entradas=[str(uid), "S"])
        for nome in ("vendedores", "produtos", "usuarios", "compras"):
            self.assertEqual(db[nome].count_documents({}), 0, nome)


if __name__ == "__main__":
    unittest.main()
