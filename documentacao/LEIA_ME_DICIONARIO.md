# Dicionário e convenções

DICIONARIO_DADOS.csv descreve 235 campos das nove tabelas principais. Cada linha identifica tabela, campo, tipo observado, significado, quantidade de vazios e valores observados quando há até oito valores distintos. A coluna de vazios é descrição da distribuição, não regra para converter vazios em zero. datapackage.json registra tipos, chaves e relações. INDICE_TABELAS_ANALITICAS.csv cataloga 122 tabelas de resultados e seus cabeçalhos.

Campos de contexto podem conter parágrafos, aspas e quebras de linha; use um leitor CSV, não contagem de linhas do arquivo. Separador: vírgula; codificação: UTF-8 com BOM; datas na tabela de consulta: AAAA-MM-DD. Em listas multivalor, o separador de nomes é |; campos explicitamente descritos como listas JSON devem ser interpretados como JSON, sem produto cartesiano.

Tabelas de consulta: mencoes_todas contém o final de todas as 3.455 candidatas, com propostas e revisão em colunas separadas; mencoes_incorporadas contém os 1.288 IDs incorporados e os campos analíticos usados. As planilhas originais e sidecars são preservados separadamente. A coluna corpus é a decisão final; campos históricos da extração ou propostas do modelo não são gabarito.

Os campos de arquivos auxiliares em dados/fontes/ conservam os cabeçalhos originais e são insumos de seleção/extração, não novas medidas de resultado. Para esses registros, consulte os programas originais correspondentes e o mapa de proveniência. O campo de categoria revisada do JSON de atores pode conter Pendente histórico; prevalece categoria_final do cadastro final.

Há contagens com universos distintos: 49 audiências no quadro institucional, 31 com documentos examinados, 30 com menções incorporadas, 28 com os dois macrogrupos para H23. Não os intercambie. Categorias de ator podem se sobrepor numa menção. Referência genérica à audiência é não aplicável para categoria, identificação não resolvida é dado não classificável pelo vínculo escolhido e Outros é uma categoria válida.
