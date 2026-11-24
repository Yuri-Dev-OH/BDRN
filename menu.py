from pymongo.errors import PyMongoError

from mymongo import conectar
import usuarios
import vendedores
import produtos
import favoritos
import compras


def menu_usuarios(db):
    while True:
        print("\nUsuários: 1-Cadastrar  2-Consultar  3-Atualizar  4-Excluir  V-Voltar")
        opcao = input("Opção: ").strip().upper()
        if opcao == "1":
            usuarios.criar_usuario(db.usuarios)
        elif opcao == "2":
            usuarios.listar_usuarios(db.usuarios)
        elif opcao == "3":
            usuarios.atualizar_usuario(db.usuarios)
        elif opcao == "4":
            usuarios.excluir_usuario(db.usuarios)
        elif opcao == "V":
            return
        else:
            print("Opção inválida.")


def submenu(db, modulo):
    while True:
        print(f"\n{modulo.__name__}: 1-Cadastrar  2-Consultar  3-Atualizar  4-Excluir  V-Voltar")
        opcao = input("Opção: ").strip().upper()
        if opcao == "1":
            modulo.cadastrar(db)
        elif opcao == "2":
            modulo.consultar(db)
        elif opcao == "3":
            modulo.atualizar(db)
        elif opcao == "4":
            modulo.apagar(db)
        elif opcao == "V":
            return
        else:
            print("Opção inválida.")


def main():
    client, db = conectar()
    try:
        while True:
            print("\n1 - Usuários\n2 - Vendedores\n3 - Produtos\n4 - Favoritos\n5 - Compras\nS - Sair")
            opcao = input("Opção: ").strip().upper()
            try:
                if opcao == "1":
                    menu_usuarios(db)
                elif opcao == "2":
                    submenu(db, vendedores)
                elif opcao == "3":
                    submenu(db, produtos)
                elif opcao == "4":
                    submenu(db, favoritos)
                elif opcao == "5":
                    submenu(db, compras)
                elif opcao == "S":
                    break
                else:
                    print("Opção inválida.")
            except PyMongoError:
                print("Erro no MongoDB. Confira a conexão, as permissões e o IP liberado no Atlas.")
    finally:
        client.close()


if __name__ == "__main__":
    try:
        main()
    except PyMongoError:
        print("Não foi possível conectar ao MongoDB.")
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma encerrado.")
