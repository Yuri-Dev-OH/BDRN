import os
from pathlib import Path

from pymongo import MongoClient


def carregar_env():
    """Carrega variáveis do arquivo .env (ao lado deste módulo) sem sobrescrever o ambiente."""
    caminho = Path(__file__).with_name(".env")
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip("\"'"))


def conectar():
    carregar_env()
    uri = os.environ.get("MONGO_URI")
    if not uri:
        raise SystemExit("Defina MONGO_URI no ambiente ou no arquivo .env (veja .env.example).")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client, client["db_mercado_livre"]
