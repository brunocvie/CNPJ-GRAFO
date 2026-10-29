# CNPJ-GRAFO
Projeto de criação de grafos através de dados extraídos da base pública da Receita Federal

Link para a os dados: https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj

Para o código conseguir fazer as consultas é necessário converter os arquivos da Receita Federal em formato sqlite. Para a conversão foi utilizado o projeto da REDE-CNPJ, disponível em: https://github.com/rictom/rede-cnpj.

Após a conversão é necessário fazer um processo de desnormalização do banco de dados através do seguintes critérios:

* Criar uma coluna na tabela Estabelecimento com o nome de município e importar os dados da tabela municipio através da correlação do código por município;
* Criar uma coluna na tabela Estabelecimento com a razão social das empresas e importar os dados da tabela empresas através da correlação do código cnpj_basico;
* Criar uma coluna na tabela Estabelecimento com o número de CNPJ completo (14 dígitos numéricos) e importar os dados da tabela socios através da correlação do código cnpj_básico.

Com o banco de dados criado e desnormalizado, basta indicar o caminho do arquivo e os CNPJs que se deseja descobrir os relacionamentos. A saída é um arquivo HTML dinâmico e um arquivo TXT indicando as entidades e os relacionamentos entre os CNPJs.

OBS.: O código foi criado para usar apenas o padrão numérico de CNPJs.
