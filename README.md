# Audiências públicas do STF — dados, documentos e código

**Autor do banco e do código de pesquisa: Pedro H. Giordano.**

Este repositório reúne os dados da pesquisa sobre referências às audiências públicas e a seus participantes nos acórdãos do Supremo Tribunal Federal. Contém as menções recuperadas, suas classificações, o cadastro dos participantes, os documentos-fonte e os programas de coleta, classificação e análise.

## Dados

| Arquivo | Unidade e dimensão | Conteúdo |
|---|---|---|
| [mencoes_todas.csv](dados/mencoes_todas.csv) | 3.455 ocorrências | Decisões finais, propostas automáticas, revisões e contexto, incluindo 2.167 exclusões |
| [mencoes_incorporadas.csv](dados/mencoes_incorporadas.csv) | 1.288 menções | Base analítica com variáveis, vínculos e contexto |
| [participantes.csv](dados/participantes.csv) | 405 participações pessoa × audiência | Cadastro completo e classificação institucional final |
| [vinculos_mencao_participante.csv](dados/vinculos_mencao_participante.csv) | 380 pares | Relação entre 307 menções e 141 participações, sem duplicar as menções no corpus |
| [entidades_sensibilidade.csv](dados/entidades_sensibilidade.csv) | 326 entidades por audiência | Vínculos institucionais utilizados apenas em análises de sensibilidade |
| [participantes_H23.csv](dados/participantes_H23.csv) | 405 participações | Indicadores de alcance e contagens de presença argumentativa |
| [resumo_audiencias_H23.csv](dados/resumo_audiencias_H23.csv) | 31 audiências | Denominadores por grupo e diferenças; 28 audiências permitem comparação entre os grupos |

Os CSVs usam UTF-8 com BOM, separador vírgula e ponto decimal. Campos textuais podem conter aspas e quebras de linha. Vazio não equivale a zero. As planilhas finais originais estão em `dados/planilhas/` e `dados/fontes/atores/`.

O [dicionário de dados](documentacao/DICIONARIO_DADOS.csv) descreve 235 campos das nove tabelas principais. O [esquema relacional](datapackage.json) registra tipos, chaves e relações. O [índice das tabelas analíticas](documentacao/INDICE_TABELAS_ANALITICAS.csv) relaciona os resultados preservados.

## Organização

- **`dados/`** — bases de consulta, planilhas originais, insumos de integração e quadros de seleção.
- **`fontes_documentais/`** — 50 acórdãos integrais e 125 documentos das audiências, organizados por audiência e arquivo.
- **`classificacao/`** — instruções e registros de 13 etapas de classificação e revisão. Não constituem 13 testes independentes.
- **`programas/`** — coleta, extração, classificação e histórico do experimento MLX, sem pesos de modelos.
- **`analise_stf/`** — código, configurações, testes e resultados das análises exploratórias H1–H23.
- **`documentacao/`** — dicionário, metodologia, escopo, limites e procedência dos arquivos.
- **`verificacao/`** — registros da conferência e reprodução dos resultados.

O [índice documental](dados/fontes/documentos_fontes.csv) identifica cada documento-fonte, seu caminho, tamanho, SHA-256 e URL quando disponível. Os 175 documentos incluem 166 PDFs, seis DOCX e três HTML, além de um JSON de metadados de coleta. Listas de habilitados e programações são fontes auxiliares, sem comprovar por si a participação efetiva.

## Reprodução

Recomenda-se Python 3.12. A verificação de integridade utiliza apenas a biblioteca padrão:

```sh
python3 reproduzir.py --verificar
```

Para os testes e cálculos estatísticos:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python reproduzir.py --testes
python reproduzir.py --analises
```

Os testes e cálculos são executados em uma cópia em `reproducoes/`, preservando as referências distribuídas. A reprodução foi conferida em 40 testes, com equivalência numérica das 111 linhas da matriz H1–H22 e dos nove registros de H23. A execução estatística não chama APIs nem exige credenciais. Reexecutar a classificação por modelo de linguagem é uma operação distinta, descrita em [programas/LEIA_ME.md](programas/LEIA_ME.md).

`SHA256SUMS.txt` permite conferir a integridade dos arquivos. Os hashes também preservam a correspondência dos documentos integrais com o acervo original.

## Escopo e interpretação

As 1.288 menções incorporadas compreendem 509 Contextos, 278 Relatos e 501 Argumentos. Das inclusões finais, 269 possuem decisão humana consolidada registrada e 1.019 não possuem revisão humana registrada. As análises são observacionais e exploratórias, restritas ao cadastro documentado.

A taxa argumentativa textual é a proporção de Argumentos entre menções incorporadas, não a parcela de todas as contribuições orais utilizada. Alcance e intensidade de H23 têm participantes como denominador e regras próprias de contagem. Os intervalos não abrangem erros de recuperação ou classificação, e presença argumentativa não comprova concordância ou influência causal. Consulte [ESCOPO_E_LIMITES.md](documentacao/ESCOPO_E_LIMITES.md) e a [metodologia de classificação](documentacao/metodologia_classificacao_v012.md).

O quadro institucional de 49 audiências, o acervo de 31 audiências examinadas e as 30 com menções incorporadas têm recortes distintos. Os documentos oficiais e seus textos mantêm a autoria e procedência originais.

## Citação

GIORDANO, Pedro H. **Audiências públicas do STF: dados, documentos e código**. Versão 1.0.0. 2026. Disponível em: https://github.com/pedrogrdn/stf-audiencias-publicas.

Os metadados de citação estão em [CITATION.cff](CITATION.cff).
