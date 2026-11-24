import hashlib
import os

from comum import listar, selecionar


def ler_obrigatorio(campo):
    valor = input(campo + ": ").strip()
    while not valor:
        valor = input("Preencha " + campo + ": ").strip()
    return valor


def proteger_senha(senha):
    salt = os.urandom(16)
    resumo = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, 600000)
    return f"pbkdf2_sha256$600000${salt.hex()}${resumo.hex()}"


def ler_enderecos():
    enderecos = []
    while True:
        print("\nCadastro de endereço")
        endereco = {}
        for campo in ["rua", "num", "bairro", "cidade", "estado", "cep"]:
            endereco[campo] = ler_obrigatorio(campo)
        enderecos.append(endereco)
        if input("Adicionar outro endereço? (S/N): ").strip().upper() != "S":
            return enderecos


def criar_usuario(colecao):
    usuario = {}
    for campo in ["nome", "email", "telefone", "cpf"]:
        usuario[campo] = ler_obrigatorio(campo)
    if colecao.find_one({"cpf": usuario["cpf"]}):
        print("Já existe um usuário com esse CPF.")
        return
    usuario["senha"] = proteger_senha(ler_obrigatorio("senha"))
    usuario["enderecos"] = ler_enderecos()
    colecao.insert_one(usuario)
    print("Usuário cadastrado.")


def listar_usuarios(colecao):
    listar(colecao)


def atualizar_usuario(colecao):
    usuario = selecionar(colecao, "usuário")
    if usuario is None:
        return
    print("Deixe em branco para manter o valor atual.")
    dados = {}
    for campo in ["nome", "email", "telefone", "cpf"]:
        valor = input(f"{campo} [{usuario.get(campo, '')}]: ").strip()
        if valor:
            dados[campo] = valor
    if "cpf" in dados and colecao.find_one({"cpf": dados["cpf"], "_id": {"$ne": usuario["_id"]}}):
        print("Esse CPF já está cadastrado.")
        return
    senha = input("Nova senha (Enter para manter): ").strip()
    if senha:
        dados["senha"] = proteger_senha(senha)
    if input("Substituir os endereços? (S/N): ").strip().upper() == "S":
        dados["enderecos"] = ler_enderecos()
    if dados:
        resultado = colecao.update_one({"_id": usuario["_id"]}, {"$set": dados})
        print("Usuário atualizado." if resultado.matched_count else "Usuário não encontrado.")
    else:
        print("Nenhuma alteração feita.")


def excluir_usuario(colecao):
    usuario = selecionar(colecao, "usuário")
    if usuario is None:
        return
    resposta = input(f"Excluir {usuario.get('nome', usuario['_id'])}? (S/N): ").strip().upper()
    if resposta == "S":
        db = colecao.database
        if db.compras.find_one({"usuario_id": usuario["_id"]}):
            print("Usuário ligado a compras. Remova esses vínculos primeiro.")
            return
        resultado = colecao.delete_one({"_id": usuario["_id"]})
        print("Usuário excluído." if resultado.deleted_count else "Usuário não encontrado.")
    else:
        print("Exclusão cancelada.")
