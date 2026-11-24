# CRUD Mercado Livre

## Como rodar

No terminal, dentro da pasta do projeto:

```powershell
python -m pip install -r requirements.txt
python menu.py
```

A conexão está em `mymongo.py`, usando o banco `db_mercado_livre`.
Copie `.env.example` para `.env` e preencha `MONGO_URI` (o `.env` não vai para o git).
Seu IP precisa estar liberado no MongoDB Atlas.

Índices e validadores: `python setup_db.py` (verifica) e `python setup_db.py --aplicar`.
Testes (usam um banco temporário no mesmo cluster):
`python -m unittest discover -s tests -t .`

## Como usar

Escolha a coleção no menu e depois cadastrar, consultar, atualizar ou excluir.
Cada coleção tem seu arquivo Python. `comum.py` reúne a leitura de IDs, números,
listagem e confirmação de exclusão usadas pelos novos arquivos.

1. Cadastre um usuário e um vendedor.
2. Consulte os vendedores e copie o ID para cadastrar um produto.
3. Para favoritar, informe o ID do usuário e do produto. Os favoritos ficam dentro
   do documento do usuário, no array `favoritos` (`produto_id`, `nome`, `data_favoritado`);
   não existe mais a coleção `favoritos`.
4. Para comprar, informe o ID do usuário e adicione produtos e quantidades.
   O vendedor de cada item vem automaticamente do cadastro do produto.

Copie apenas o valor do ID, sem `ObjectId(...)` e sem aspas.
São aceitos os IDs numéricos das imagens e os ObjectId dos novos cadastros.

Todas as coleções usam o ID do registro para atualizar e excluir.
Todas as consultas usam o ID do próprio registro; Enter lista todos.
Em compras, informe o ID da compra; em favoritos, o ID do usuário e o ID do produto favoritado.
Na atualização, Enter mantém os campos atuais,
exceto em favoritos, onde é informado o ID do novo produto.

Cada compra guarda uma lista `itens` com `produto_id`, `vendedor_id`, `quantidade`
e `preco_unitario`. Pode haver produtos de diferentes vendedores na mesma compra.
O subtotal e o total com frete são calculados no cadastro. Alterar o preço ou
vendedor do produto depois não muda os dados já registrados na compra.
Na atualização da compra é possível mudar o status, o status do pagamento e o frete.
Para corrigir usuário ou itens, exclua a compra e cadastre novamente.

Este é um CRUD de registros: não processa pagamentos, não baixa estoque nem
atualiza automaticamente reputação ou total de vendas do vendedor.
Não permite excluir usuários, vendedores ou produtos que ainda tenham vínculos.
Remova primeiro os favoritos, compras ou produtos relacionados, conforme a mensagem.
Excluir um usuário apaga também os favoritos dele.

As senhas dos usuários são guardadas como hash e não aparecem na consulta.
`__pycache__` é um cache que o Python pode criar automaticamente e pode ser apagado.
