# Notas de versão

## v1.0.2 — DOI e metadados de citação

- Adiciona o badge do Zenodo ao README, com DOI do conjunto de versões: [10.5281/zenodo.24021782](https://doi.org/10.5281/zenodo.24021782).
- Registra a citação específica da versão arquivada v1.0.1: [10.5281/zenodo.24021783](https://doi.org/10.5281/zenodo.24021783).
- Atualiza `CITATION.cff`, `datapackage.json`, `manifesto_dados.json` e os checksums.
- Mantém autoria exclusiva de Pedro H. Giordano, CC BY 4.0 para dados/documentação autorais e MIT para código autoral.

Atualização exclusivamente documental e de metadados. Os dados, classificações, documentos-fonte e resultados estatísticos permanecem inalterados. A configuração `.zenodo.json` não fixa o DOI de uma versão anterior, permitindo que a integração registre a nova versão.

## v1.0.1 — Arquivamento no Zenodo

Versão arquivada em 6 de novembro de 2026: https://zenodo.org/records/24021783 . DOI da versão: 10.5281/zenodo.24021783; DOI do conjunto: 10.5281/zenodo.24021782.

## v1.0.0 — Audiências públicas do STF: dados, documentos e código

Primeira versão do banco documental e dos programas de classificação e análise das referências às audiências públicas do Supremo Tribunal Federal nos acórdãos examinados.

### Conteúdo

- 3.455 passagens candidatas, com decisões finais, propostas automáticas e revisões registradas.
- 1.288 menções incorporadas: 509 Contextos, 278 Relatos e 501 Argumentos; 2.167 exclusões preservadas.
- 405 participações classificadas em seis categorias institucionais e vínculos entre participantes e menções.
- 50 acórdãos integrais e 125 documentos de audiências, com índice de fontes e hashes.
- Instruções e registros de 13 etapas de classificação e revisão, além do experimento local MLX sem pesos.
- Código, configurações e resultados das análises exploratórias H1–H23.
- Dicionário de dados, proveniência e verificação offline de integridade.

### Verificação e reprodução

A reprodução foi conferida em 40 testes. A reprodução independente conferiu equivalência numérica das 111 linhas da matriz H1–H22 e dos nove registros de H23. Os documentos foram preservados sem alteração de bytes e possuem SHA-256 no índice. `python3 reproduzir.py --verificar` confere a integridade sem chamadas à API; testes e recálculo estão descritos no README.

### Escopo e limites

A busca abrangeu 50 documentos vinculados a 31 audiências; as menções incorporadas se distribuem por 46 documentos e 30 audiências. O cadastro de participantes contém 31 audiências, das quais 28 permitem o contraste entre macrogrupos de H23. Esses denominadores não são intercambiáveis.

Entre as inclusões finais, 269 possuem decisão humana consolidada registrada e 1.019 permanecem sem revisão humana registrada. Os resultados são observacionais e exploratórios. Presença argumentativa não demonstra concordância, convencimento ou influência causal; os intervalos não abrangem erros de recuperação e classificação.

### Consulta

Comece por `README.md`, `dados/mencoes_todas.csv`, `dados/participantes.csv` e `documentacao/DICIONARIO_DADOS.csv`. Os documentos integrais estão em `fontes_documentais/`.

### Licenças

Dados e documentação autorais sob CC BY 4.0; código autoral sob MIT. Autoria: Pedro H. Giordano. Os documentos oficiais e materiais de terceiros mantêm seus créditos e regime jurídico próprios.
