# Contexto do projeto (para quem for continuar o trabalho)

Documento de handoff: o que o exercício pede, como o projeto estava, o que foi
mudado e como está agora. Escrito para outro assistente ou desenvolvedor entender
o estado atual sem ler o histórico da conversa.

## 1. O exercício (`EX2.pdf`)

Disciplina: Banco de Dados Não Relacional (Fatec São José dos Campos).
Enunciado resumido: criar conta gratuita no MongoDB Atlas e implementar **em Python**
as funções de manipulação da base do **Mercado Livre (EX1)** criada no MongoDB:

- a. Insert em todas as coleções
- b. Update em todas as coleções
- c. Search em todas as coleções
- d. Delete em todas as coleções

Entrega: `NomeEX2_BDNR.pdf`.

## 2. Como o projeto estava

CRUD em Python (pymongo) com menu de terminal (`menu.py`), um módulo por coleção:
`usuarios.py`, `vendedores.py`, `produtos.py`, `favoritos.py`, `compras.py`, mais
`comum.py` (leitura de IDs/números, listagem, exclusão) e `mymongo.py` (conexão).

Banco `db_mercado_livre`, **5 coleções**: `usuarios`, `vendedores`, `produtos`,
`favoritos`, `compras`.

- `favoritos` era uma coleção própria: `{usuario_id, produto_id, data_favoritado}`.
- Não havia índices (além de `_id`) nem validação no banco; unicidade (CPF, documento,
  favorito repetido) era checada só no Python, com `find_one` antes do insert.
- A URI do Atlas, com usuário e senha, estava escrita direto em `mymongo.py`.
- Não havia testes automatizados nem repositório git.

## 3. O que foi mudado

1. **Favoritos embutidos em `usuarios`** (pedido do dono do projeto). A coleção
   `favoritos` foi **removida do Atlas**, depois de migrar os 3 registros existentes.
   Agora cada usuário tem:
   ```json
   "favoritos": [{"produto_id": <id>, "nome": "str", "data_favoritado": <date>}]
   ```
   - `favoritos.py` opera nesse array (`$push`, `$set` com `favoritos.$`, `$pull`).
     Consulta/atualização/exclusão usam o ID do usuário + ID do produto favoritado.
   - `usuarios.py`: excluir usuário só é bloqueado por compras (favoritos saem junto).
   - `produtos.py`: exclusão é bloqueada se o produto está nos favoritos de algum
     usuário; renomear o produto propaga o novo nome para os favoritos
     (`update_many` com `array_filters`).
2. **`setup_db.py`** (novo). Sem argumentos só verifica duplicados (somente leitura);
   com `--aplicar` cria índices e validadores. Idempotente.
   - Únicos parciais (só para strings): `usuarios.cpf`, `vendedores.documento`.
   - Simples: `usuarios.favoritos.produto_id`, `produtos.vendedor_id`,
     `compras.usuario_id`, `compras.itens.produto_id`, `compras.itens.vendedor_id`,
     `compras.vendedor_id` (formato antigo, ainda consultado em `vendedores.apagar`).
   - Validadores `$jsonSchema` com `validationLevel="moderate"` em `usuarios`,
     `vendedores`, `produtos`, `compras` (tipos, mínimos, campos obrigatórios).
     "moderate" porque há dados antigos com IDs numéricos que não precisam passar.
   - Já aplicado no Atlas real.
3. **Testes** em `tests/` (`unittest`, sem dependência nova): 74 testes, todos passando.
   Cada classe cria um banco temporário `db_mercado_livre_test_<id>` no mesmo cluster,
   aplica `aplicar_schema` e o apaga no fim; o banco real não é tocado. O `input()` é
   simulado com `unittest.mock`. Cobrem CRUD completo das 4 coleções, regras de bloqueio
   de exclusão, índices únicos, validadores e um fluxo ponta a ponta.
4. **Credencial fora do código.** `mymongo.py` lê `MONGO_URI` do ambiente ou de `.env`
   (parser próprio, sem python-dotenv). `.env` está no `.gitignore`; `.env.example`
   mostra o formato.
5. **Git.** Repositório criado e enviado para `https://github.com/Yuri-Dev-OH/BDRN.git`
   (branch `main`).

## 4. Como está agora, em relação ao PDF

| Requisito | Situação |
|---|---|
| Conta MongoDB Atlas | Cluster `dbmercadolivre`, banco `db_mercado_livre` |
| Insert em todas as coleções | `usuarios`, `vendedores`, `produtos`, `compras` têm cadastro próprio; favoritos é insert no array de `usuarios` |
| Update em todas as coleções | Idem, via menu (Enter mantém o valor atual) |
| Search em todas as coleções | Por ID ou lista completa; senha nunca é exibida |
| Delete em todas as coleções | Com confirmação e bloqueio quando há vínculos |
| Entrega em PDF | **Pendente**: o `NomeEX2_BDNR.pdf` não faz parte do repositório |

Ponto de atenção sobre o PDF: o enunciado fala em "todas as coleções". Com a mudança,
`favoritos` deixou de ser coleção; o requisito de favoritos é atendido pelas operações
sobre o subdocumento em `usuarios`. Vale deixar isso explícito no PDF de entrega.

## 5. Como rodar

```powershell
python -m pip install -r requirements.txt
copy .env.example .env          # depois preencha MONGO_URI no .env
python menu.py                  # aplicação
python setup_db.py              # verifica duplicados (leitura)
python setup_db.py --aplicar    # cria índices e validadores
python -m unittest discover -s tests -t .   # testes (precisam do Atlas e do IP liberado)
```

## 6. Limitações e pendências conhecidas

- O `nome` dentro de `favoritos` é uma cópia: sincroniza ao renomear pelo menu, mas
  não se o banco for alterado por fora.
- Não há índice único impedindo o mesmo produto duas vezes em `favoritos`; só o código
  verifica (pode falhar com acessos simultâneos). Não há limite de tamanho do array.
- É um CRUD de registros: não baixa estoque, não processa pagamento e não atualiza
  `reputacao`/`total_vendas` do vendedor (decisão original, descrita no README).
- `listar()` imprime tudo quando se aperta Enter (sem paginação).
- `menu.py` e o tratamento de `PyMongoError` não têm testes.
- As credenciais do cluster (no `.env` local) são fracas e o repositório parece
  público: trocar a senha no Atlas e usar um usuário de menor permissão.
- Os testes exigem rede e IP liberado no Atlas.
