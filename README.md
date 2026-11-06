# Audiências públicas do STF — dados, documentos e código

**Preparação para a primeira versão pública, 6 de novembro de 2026. DOI e licença pública ainda não atribuídos.**

Repositório de dados da pesquisa sobre presença das audiências públicas e de seus participantes nos acórdãos do STF. A interpretação é desenvolvida na dissertação; aqui se preservam dados, classificações, contexto, procedência e programas.

## Comece pelos dados

| Arquivo | Unidade / tamanho | Uso |
|---|---|---|
| `dados/mencoes_todas.csv` | 3.455 ocorrências, incluindo 2.167 exclusões | Decisão final, propostas Claude, decisões humanas, metadados e contexto |
| `dados/mencoes_incorporadas.csv` | 1.288 ocorrências | Base principal com variáveis analíticas, vínculos e contexto |
| `dados/participantes.csv` | 405 participações pessoa × audiência | Cadastro completo e categoria final, inclusive sem menção |
| `dados/vinculos_mencao_participante.csv` | 380 pares; 307 menções; 141 participações | Relação muitos-para-muitos, sem duplicar as menções |
| `dados/entidades_sensibilidade.csv` | 326 entidades por audiência | Base do vínculo institucional apenas complementar |
| `dados/participantes_H23.csv` | 405 participações | Alcance nominal e contagens para H23 |
| `dados/resumo_audiencias_H23.csv` | 31 audiências, 28 comparáveis | Denominadores e diferenças por grupo |

`dados/planilhas/` e `dados/fontes/atores/` preservam as duas planilhas finais originais; CSV é a alternativa aberta de consulta. `dados/fontes/` guarda os seis insumos da integração e o índice dos documentos, com URLs e hashes quando disponíveis. Todos os CSVs usam UTF-8 com BOM, vírgula, ponto decimal e campos entre aspas quando necessários; trechos podem ocupar várias linhas. Vazio não equivale a zero. O dicionário identifica tipos e convenções.

## Conteúdo

- `fontes_documentais/`: 50 acórdãos integrais e 125 documentos de audiências, com organização original por audiência e processo.
- `documentacao/`: dicionário, decisões metodológicas, escopo e limites, proveniência e guia de depósito.
- `classificacao/`: instruções congeladas, índice e insumos/saídas de 13 etapas de classificação e revisão; não são 13 testes independentes.
- `programas/`: coleta e classificação originais; histórico do experimento MLX sem pesos.
- `analise_stf/`: código original de H1–H23, configurações, testes e resultados de referência. Apenas os caminhos de cinco entradas foram adaptados a este repositório; a lógica estatística não foi modificada.
- `reproduzir.py`: verificação offline, testes e reprodução isolada, sem API.
- `verificacao/`: resultados de conferência e inventário SHA-256.
- `metadados/`: rascunho para o Zenodo. Confirmar autoria e licenças antes da publicação.

Não inclui chaves, ambientes Python/Node/MLX, pesos de modelos, capturas de tela, arquivos de inspeção do editor ou manuscritos em revisão. Os 50 acórdãos e os 125 documentos de audiências disponíveis no acervo foram incluídos integralmente, além dos contextos e excertos usados na classificação. O índice informa o caminho de cada documento no repositório, procedência e SHA-256. Caminhos históricos em manifestações de procedência não são caminhos requeridos para executar a reprodução.

## Reprodução estatística sem API

Recomendado Python 3.12. `python3 reproduzir.py --verificar` usa apenas a biblioteca padrão. Para testes e reprodução, criar ambiente com `python3 -m venv .venv`, ativá-lo e instalar `python -m pip install -r requirements.txt`. Em seguida:

```sh
python reproduzir.py --verificar
python reproduzir.py --testes
python reproduzir.py --analises
```

As análises são executadas numa cópia em `reproducoes/`, preservando os dados e resultados de referência. Os resultados numéricos são comparados aos preservados. A instalação das dependências pode precisar de internet; a execução estatística não acessa APIs e não depende de credencial. Uma nova chamada ao classificador é outra operação, sujeita a autorização e custo; não é necessária para reproduzir os cálculos.

## Leitura responsável

Foram incorporados 509 Contextos, 278 Relatos e 501 Argumentos. Apenas 269 inclusões possuem decisão humana registrada; 1.019 permanecem sem revisão humana registrada. A taxa textual é Argumentos / menções incorporadas, não a proporção de todos os argumentos orais utilizada. Alcance e intensidade de H23 usam participações como denominador, com regras distintas. As análises são exploratórias, observacionais e restritas ao cadastro documentado. Consulte `documentacao/ESCOPO_E_LIMITES.md` antes de reutilizar as taxas.

## Citação e publicação

A autoria e o licenciamento devem ser confirmados pelos responsáveis. O rascunho de citação não contém DOI inventado. Guia: `documentacao/COMO_DEPOSITAR_NO_ZENODO.md`. Esta preparação não publica arquivos e não concede uma licença em nome dos autores.

O quadro institucional de 49 audiências, suas fontes oficiais, o controle documental e os complementos manuais de recuperação estão em `dados/fontes/`; esses quadros têm recortes distintos do corpus de menções incorporadas. A restauração offline dos programas históricos é descrita em `programas/LEIA_ME.md`.

## Acervo documental integral

`fontes_documentais/acordaos/` contém os 50 PDFs do acervo examinado, inclusive aqueles sem menções incorporadas. `fontes_documentais/documentos_audiencias/` preserva os 125 documentos das audiências: 116 PDFs, seis DOCX e três HTML, mais um JSON de metadados de coleta. São 175 documentos, além do metadado. A inclusão do acervo auxiliar não transforma listas de habilitados ou programações em prova de comparecimento. O índice `dados/fontes/documentos_fontes.csv` mantém audiência, nome original, caminho no repositório, tamanho, hash e URL quando disponível. Os arquivos não foram convertidos, editados ou regravados.
