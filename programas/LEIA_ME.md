# Programas históricos

`coleta/`: programas originais para coleta, busca e OCR. `classificacao/`: executores e consolidadores efetivamente usados, com dependências legadas em `legado/`. `historico_mlx/`: configuração e dados do experimento local; pesos e ambientes não foram incluídos.

São registros do procedimento, não um comando universal independente de seus insumos. Caminhos relativos nesses programas descrevem a organização original do projeto. Para reconstruir o trabalho de classificação, use o mapa em `documentacao/proveniencia_arquivos.csv` e os insumos preservados em `classificacao/rodadas/`. Os documentos integrais estão em `fontes_documentais/`; os caches intermediários de OCR não foram incluídos. O índice e hashes estão em `dados/fontes/documentos_fontes.csv`. A reprodução estatística usa as tabelas extraídas fornecidas e dispensa PDFs, macOS e API.

Uma nova classificação pelo modelo pode produzir respostas diferentes e gerar cobrança. Nenhum comando de reprodução estatística chama APIs. Os nomes de modelo, limites e preços presentes nos scripts são registros históricos, não uma afirmação de disponibilidade ou preço atuais. Não execute os programas de API por engano: cada um preserva suas autorizações, limites e instruções originais. Nenhuma chave de API é distribuída. OCR Apple Vision e treinamento MLX exigem ambiente Apple compatível, fora dos requisitos estatísticos.

A classificação inicial de participantes utilizou cinco categorias; a revisão final acrescentou Partido Político. A planilha final e a tabela `dados/participantes.csv` são a referência para as seis categorias finais; não reconstrua o resultado final apenas pela primeira proposta automática.

Para reconstruir os caminhos históricos dos arquivos disponíveis sem executar modelos: `python programas/restaurar_classificacao.py --destino /caminho/novo/fora/do/pacote`. Nessa pasta, `python scripts/executar_integral_claude.py --verificar` confere offline o lote de 3.010 casos e as 445 decisões humanas preservadas. A restauração também repõe os documentos integrais nos caminhos históricos; não inclui ambientes ou credenciais e nunca chama APIs.
