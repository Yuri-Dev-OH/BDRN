import unittest
from datetime import datetime

import usuarios
from tests.base import BaseTeste, ENDERECO


class TestUsuarios(BaseTeste):
    DADOS = ["Ana", "a@x.com", "1199", "12345678901"]

    def criar(self, dados=None, senha="senha123", enderecos=(ENDERECO,)):
        entradas = list(dados or self.DADOS) + [senha]
        for i, end in enumerate(enderecos):
            entradas += end + ["S" if i < len(enderecos) - 1 else "N"]
        return self.rodar(usuarios.criar_usuario, self.db.usuarios, entradas=entradas)

    # Create
    def test_criar_usuario(self):
        self.assertIn("Usuário cadastrado", self.criar())
        u = self.db.usuarios.find_one({"cpf": "12345678901"})
        self.assertEqual(u["nome"], "Ana")
        self.assertTrue(u["senha"].startswith("pbkdf2_sha256$"))
        self.assertNotIn("senha123", u["senha"])
        self.assertEqual(len(u["enderecos"]), 1)

    def test_criar_com_dois_enderecos(self):
        self.criar(enderecos=(ENDERECO, ENDERECO))
        self.assertEqual(len(self.db.usuarios.find_one()["enderecos"]), 2)

    def test_criar_cpf_duplicado(self):
        self.criar()
        saida = self.rodar(usuarios.criar_usuario, self.db.usuarios, entradas=self.DADOS)
        self.assertIn("Já existe", saida)
        self.assertEqual(self.db.usuarios.count_documents({}), 1)

    def test_campo_obrigatorio_reprompt(self):
        self.criar(dados=["", "Ana", "a@x.com", "1199", "12345678901"])
        self.assertEqual(self.db.usuarios.find_one()["nome"], "Ana")

    # Read
    def test_listar_todos_sem_senha(self):
        self.criar()
        saida = self.rodar(usuarios.listar_usuarios, self.db.usuarios, entradas=[""])
        self.assertIn("Ana", saida)
        self.assertNotIn("pbkdf2", saida)

    def test_listar_por_id(self):
        uid = self.novo_usuario()
        self.novo_usuario(cpf="2", nome="Bruno")
        saida = self.rodar(usuarios.listar_usuarios, self.db.usuarios, entradas=[str(uid)])
        self.assertIn("Ana", saida)
        self.assertNotIn("Bruno", saida)

    def test_listar_id_inexistente_e_invalido(self):
        saida = self.rodar(usuarios.listar_usuarios, self.db.usuarios, entradas=[self.id_inexistente()])
        self.assertIn("Nenhum registro", saida)
        saida = self.rodar(usuarios.listar_usuarios, self.db.usuarios, entradas=["abc"])
        self.assertIn("ID inválido", saida)

    # Update
    def test_atualizar_mantem_campos_em_branco(self):
        uid = self.novo_usuario()
        self.rodar(usuarios.atualizar_usuario, self.db.usuarios,
                   entradas=[str(uid), "Ana Maria", "", "", "", "", "N"])
        u = self.db.usuarios.find_one({"_id": uid})
        self.assertEqual(u["nome"], "Ana Maria")
        self.assertEqual(u["email"], "a@x.com")
        self.assertEqual(u["senha"], "hash")

    def test_atualizar_senha_e_enderecos(self):
        uid = self.novo_usuario()
        self.rodar(usuarios.atualizar_usuario, self.db.usuarios,
                   entradas=[str(uid), "", "", "", "", "nova123", "S"] + ENDERECO + ["N"])
        u = self.db.usuarios.find_one({"_id": uid})
        self.assertTrue(u["senha"].startswith("pbkdf2_sha256$"))
        self.assertEqual(u["enderecos"][0]["rua"], "Rua A")

    def test_atualizar_cpf_duplicado(self):
        self.novo_usuario(cpf="1")
        uid = self.novo_usuario(cpf="2", nome="Bruno")
        saida = self.rodar(usuarios.atualizar_usuario, self.db.usuarios,
                           entradas=[str(uid), "", "", "", "1"])
        self.assertIn("já está cadastrado", saida)
        self.assertEqual(self.db.usuarios.find_one({"_id": uid})["cpf"], "2")

    def test_atualizar_sem_alteracao(self):
        uid = self.novo_usuario()
        saida = self.rodar(usuarios.atualizar_usuario, self.db.usuarios,
                           entradas=[str(uid), "", "", "", "", "", "N"])
        self.assertIn("Nenhuma alteração", saida)

    # Delete
    def test_excluir_usuario(self):
        uid = self.novo_usuario()
        self.rodar(usuarios.excluir_usuario, self.db.usuarios, entradas=[str(uid), "S"])
        self.assertIsNone(self.db.usuarios.find_one({"_id": uid}))

    def test_excluir_cancelado(self):
        uid = self.novo_usuario()
        saida = self.rodar(usuarios.excluir_usuario, self.db.usuarios, entradas=[str(uid), "N"])
        self.assertIn("cancelada", saida)
        self.assertIsNotNone(self.db.usuarios.find_one({"_id": uid}))

    def test_excluir_bloqueado_por_compra(self):
        uid = self.novo_usuario()
        vid = self.novo_vendedor()
        self.nova_compra(uid, self.novo_produto(vid), vid)
        saida = self.rodar(usuarios.excluir_usuario, self.db.usuarios, entradas=[str(uid), "S"])
        self.assertIn("ligado a compras", saida)
        self.assertIsNotNone(self.db.usuarios.find_one({"_id": uid}))

    def test_excluir_usuario_leva_favoritos_junto(self):
        vid = self.novo_vendedor()
        pid = self.novo_produto(vid)
        uid = self.novo_usuario(favoritos=[{"produto_id": pid, "nome": "Notebook",
                                            "data_favoritado": datetime.now()}])
        self.rodar(usuarios.excluir_usuario, self.db.usuarios, entradas=[str(uid), "S"])
        self.assertEqual(self.db.usuarios.count_documents({}), 0)

    def test_excluir_id_inexistente(self):
        saida = self.rodar(usuarios.excluir_usuario, self.db.usuarios, entradas=[self.id_inexistente()])
        self.assertIn("não encontrado", saida)


if __name__ == "__main__":
    unittest.main()
