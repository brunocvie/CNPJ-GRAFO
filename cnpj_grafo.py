import networkx as nx
from pyvis.network import Network
import re
import os
import sqlite3
from datetime import datetime

# 1. Lista de CNPJs de entrada

### Inisiar os números dos CNPJs que se deseja consultar separados por virgula e entre aspas, exemplo: "00.000.000/0001-00", "00.000.0000/0001-00" ###
cnpjs_raw = [cnpjs_raw = "00.000.000/0001-00", "00.000.000/0001-00" ]

def limpar_cnpj(cnpj):
    """Remove caracteres não numéricos do CNPJ."""
    dado = re.sub(r'\D', '', cnpj)
    return dado[-14:].zfill(14)

# 2. Simulação de busca de dados (SUBSTITUA PELA SUA LÓGICA REAL)
def buscar_dados_cnpj(cursor, cnpj_limpo):
    # 1. Lista de CNPJs de entrada
    query_estabelecimento = """
            SELECT
                nome_fantasia,
                razao_social,
                data_inicio_atividades,
                tipo_logradouro || ' ' || logradTeleouro || ' ' || numero || ' ' || complemento || ' ' || bairro AS Endereco,
                cep,
                nome_municipio,
                uf,
                ddd1 || telefone1 || ', ' || ddd2 || telefone2 AS Telefone,
                correio_eletronico
            FROM estabelecimento
            WHERE cnpj = ?
        """

    query_socios = "SELECT nome_socio FROM socios WHERE cnpj = ?"

    empresa = {
        "CNPJ": cnpj_limpo, # Importante guardar a chave
        "Nome_Fantasia": None,
        "Razao_Social": None,
        "Data_Inicio": None,
        "Endereco": None,
        "CEP": None,
        "Cidade": None,
        "Estado": None,
        "Telefones": None,
        "Correio_Eletronico": None,
        "Socios": set() # Usamos set (conjunto) para facilitar comparação
    }

    try:
        cursor.execute(query_estabelecimento, (cnpj_limpo,))
        row = cursor.fetchone()

        if row:
            empresa["Nome_Fantasia"] = row[0]
            empresa["Razao_Social"] = row[1]

            if row[2]:
                try:
                    dt = datetime.strptime(row[2], '%Y%m%d')
                    empresa["Data_Inicio"] = dt.strftime('%d/%m/%Y')
                except ValueError:
                    empresa["Data_Inicio"] = row[2]

            empresa["Endereco"] = row[3]
            empresa["CEP"] = row[4]
            empresa["Cidade"] = row[5]
            empresa["Estado"] = row[6]

            if row[7]:
                empresa["Telefones"] = row[7].replace(" ,", "").strip()

            empresa["Correio_Eletronico"] = row[8]

            # Buscar Sócios
            cursor.execute(query_socios, (cnpj_limpo,))
            socios_rows = cursor.fetchall()
            # Guarda apenas os nomes em um conjunto para comparação rápida
            empresa["Socios"] = {s[0] for s in socios_rows}

            with open("entidade-CNPJ" + cnpj_limpo + ".txt", "a", encoding="utf-8") as f:
                f.write("Nome Fantasia: " + empresa["Nome_Fantasia"] + "\n")
                f.write("Razão Social: " + empresa["Razao_Social"] + "\n")
                f.write("Data Início: " + empresa["Data_Inicio"] + "\n")
                f.write("Endereço: " + empresa["Endereco"] + "\n")
                f.write("CEP: " + empresa["CEP"] + "\n")
                f.write("Cidade: " + empresa["Cidade"] + "\n")
                f.write("Estado: " + empresa["Estado"] + "\n")
                f.write("Telefones: "+ empresa["Telefones"] + "\n")
                f.write("Correio Eletrônico: " + empresa["Correio_Eletronico"] + "\n")
                for s in empresa["Socios"]:
                    f.write("Sócio: " + s + "\n")


        return empresa

    except sqlite3.Error as e:
        print(f"Erro ao buscar CNPJ {cnpj_limpo}: {e}")
        return empresa
# 3. Construção do Grafo com NetworkX
#### Insira o caminho da pasta onde está localizado o arquivo DB ###

DB_PATH = r"C:\caminho\pasta\arquivoDB"

# Context manager garante que a conexão será fechada mesmo em caso de erro

G = nx.Graph()

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()

    for cnpj in cnpjs_raw:

        cnpj_limpo = limpar_cnpj(cnpj)
        dados = buscar_dados_cnpj(cursor, cnpj_limpo)

        if not dados:
            continue
        # O Nó principal agora exibe o CNPJ como label, como você pediu
        G.add_node(cnpj_limpo, label=cnpj_limpo, title=f"Empresa: {cnpj_limpo}", type='CNPJ')

        # --- FUNÇÃO AUXILIAR PARA CRIAR CONEXÕES DE DADOS ---
        # Evita criar nós de valores vazios (None, " ", etc)
        def adicionar_conexao(valor, tipo_dado):
            if valor and str(valor).strip() and str(valor) != "None":
                # Adiciona o nó do dado (se já existir, o NetworkX apenas aproveita o existente)
                G.add_node(valor, label=str(valor), title=f"{tipo_dado}: {valor}", type=tipo_dado)
                # Conecta o CNPJ a esse dado
                G.add_edge(cnpj_limpo, valor, relation=f"Possui {tipo_dado}")

        # Criando os nós para cada tipo de dado
        if dados['Nome_Fantasia']:
            adicionar_conexao(dados['Nome_Fantasia'], "Nome Fantasia")

        if dados['Razao_Social']:
            adicionar_conexao(dados['Razao_Social'], "Razão Social")

        adicionar_conexao(dados['Correio_Eletronico'], 'Email')
        adicionar_conexao(dados['Cidade'], 'Cidade')
        adicionar_conexao(dados['Estado'], 'Estado')
        adicionar_conexao(dados['Endereco'], 'Endereco')
        adicionar_conexao(dados['CEP'], "CEP")
        adicionar_conexao(dados['Data_Inicio'], 'Data_Inicio')

        # Tratamento especial para telefones (separar por vírgula se houver mais de um)
        if dados['Telefones']:
            lista_telefones = dados['Telefones'].split(',')
            for tel in lista_telefones:
                adicionar_conexao(tel.strip(), 'Telefone')

        # Adiciona os Sócios
        for socio in dados["Socios"]:
            adicionar_conexao(socio, 'Sócio')

# 4. Geração do HTML com Pyvis (Agora com cores para cada tipo de dado)
# 4. Geração do HTML com Pyvis
def gerar_visualizacao(nx_graph):

    total_nos = nx_graph.number_of_nodes()
    total_conexoes = nx_graph.number_of_edges()

    # Criando o texto que vai aparecer no topo da página
    titulo_pagina = f"Grafo de Relações | Total de Nós: {total_nos} | Total de Conexões: {total_conexoes}"

    # --- ALTERADO: Adicionando o parâmetro 'heading' ---
    net = Network(height="800px", width="100%", heading=titulo_pagina, notebook=False, cdn_resources='in_line', select_menu=True, filter_menu=True)

    estilos = {
        'CNPJ':     {"color": "#e74c3c", "shape": "box", "size": 35}, # Vermelho grande
        'Sócio':    {"color": "#3498db", "shape": "dot", "size": 15}, # Azul
        'Email':    {"color": "#9b59b6", "shape": "dot", "size": 12}, # Roxo
        'Telefone': {"color": "#e67e22", "shape": "dot", "size": 12}, # Laranja
        'Cidade':   {"color": "#2ecc71", "shape": "dot", "size": 20}, # Verde
        'Estado':   {"color": "#1abc9c", "shape": "dot", "size": 25}, # Verde-azulado
        'Endereco': {"color": "#95a5a6", "shape": "dot", "size": 10}, # Cinza
    }

    for node, data in nx_graph.nodes(data=True):
        tipo = data.get('type', 'CNPJ')
        estilo = estilos.get(tipo, {"color": "#bdc3c7", "shape": "dot", "size": 10})

        net.add_node(node,
                     label=data.get('label', ''),
                     title=data.get('title', ''),
                     color=estilo["color"],
                     shape=estilo["shape"],
                     size=estilo["size"])

    for s, t, d in nx_graph.edges(data=True):
        net.add_edge(s, t, label=d.get('relation', ''), color="#bdc3c7")

    net.show_buttons(filter_=['physics'])

    output_path = os.path.abspath("grafo_cnpjs_socios.html")
    html_data = net.generate_html()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_data)
    print(f"Grafo gerado com sucesso: {output_path}")

def relatorio_vinculos_comuns(grafo_nx):
    """
    Analisa o grafo para encontrar nós que conectam múltiplos CNPJs.
    Salva em um arquivo TXT de relatório final.
    """
    print("\n Analisando topologia do grafo para encontrar vínculos cruzados...")

    # Criamos uma versão não direcionada para facilitar a busca de vizinhos
    G_undirected = grafo_nx.to_undirected()

    cnpjs = [n for n, d in G_undirected.nodes(data=True) if d.get('type') == 'CNPJ']

    relatorio_linhas = []
    relatorio_linhas.append(f"=== RELATÓRIO DE VÍNCULOS CRIMINAIS/SOCIETÁRIOS ===")
    relatorio_linhas.append(f"Gerado em: {datetime.now()}")
    relatorio_linhas.append(f"Total de CNPJs analisados: {len(cnpjs)}")
    relatorio_linhas.append("-" * 50)

    encontrou_vinculo = False

    # Iteramos por todos os nós que NÃO são CNPJs (Sócios, Endereços, E-mails, etc.)
    for node, data in G_undirected.nodes(data=True):
        tipo_no = data.get('type', 'Unknown')

        # Ignoramos o próprio nó CNPJ, queremos o que conecta eles
        if tipo_no == 'CNPJ':
            continue

        # Pega todos os vizinhos desse nó
        vizinhos = list(G_undirected.neighbors(node))

        # Filtra para ver quantos desses vizinhos são CNPJs
        cnpjs_conectados = []
        for v in vizinhos:
            # Verifica se o vizinho é um CNPJ (olhando os atributos do grafo original ou do undirected)
            if G_undirected.nodes[v].get('type') == 'CNPJ':
                cnpjs_conectados.append(v)

        # SE houver mais de 1 CNPJ conectado a este nó, temos um vínculo!
        if len(cnpjs_conectados) > 1:
            encontrou_vinculo = True
            cnpjs_str = ", ".join(cnpjs_conectados)
            msg = f"⚠️ VÍNCULO DETECTADO: O atributo [{tipo_no}] '{node}' conecta as empresas: {cnpjs_str}"
            relatorio_linhas.append(msg)
            print(msg) # Imprime no console também

    if not encontrou_vinculo:
        relatorio_linhas.append("Nenhum vínculo cruzado entre empresas diferentes foi encontrado.")

    # Salva o relatório
    nome_arquivo = f"Relatorio_Final_vinculos.txt"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(relatorio_linhas))

    print(f"\n Relatório de inteligência salvo em: {nome_arquivo}")


gerar_visualizacao(G)
relatorio_vinculos_comuns(G)
