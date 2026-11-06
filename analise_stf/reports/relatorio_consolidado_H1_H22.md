# Relatório consolidado H1–H22 — audiências públicas do STF

Data de referência: 05/11/2026. Gerado por `run_all.py` (Python local, sem API). Análises **exploratórias e observacionais**: descrevem as menções observadas nas audiências cujo texto foi extraído; não estimam probabilidade de aproveitamento de contribuição, favorecimento, exclusão nem representatividade, pois não há universo completo de participantes nem de votos. Estas são correções de **análise e código**; o corpus e as classificações não foram reclassificados.

## 1. Resumo

- Corpus: 1288 menções incorporadas (Contexto 509, Relato 278, Argumento 501); taxa argumentativa global 38,90% (denominador: menções incorporadas); 30 audiências; 46 documentos.
- **Unidade inferencial: a audiência.** Nenhuma menção foi permutada ou tratada como réplica independente. Contrastes internos são reduzidos a um valor por audiência; heterogeneidade e concentração (H3, H6, H10, H21) são **descritivas**, sem valor-p.
- **Três eixos de leitura, que não se misturam:** (i) *cenário de dados* — coluna Análise: Principal (A) × Sensibilidade A+B; (ii) *estimando principal previsto* — coluna Escopo do teste = "previsto principal"; (iii) *análises adicionais* — "adicional local×eixo" e "sensibilidade de elegibilidade" (ambas feitas sobre dados A) e "sensibilidade de vínculo A+B" (dados A+B; pode combinar com elegibilidade).
- Cenário A (coluna Análise = Principal (A)): 74 linhas e 40 valores-p, dos quais **66 linhas e 35 valores-p são do escopo previsto principal**, 3 linhas (3 valores-p) são adicionais local×eixo (H15) e 5 linhas (2 valores-p) são sensibilidade de elegibilidade (H19). Entre as 66 previstas: 14 inviáveis por suporte e 17 descritivas.
- **H19 — estimando principal sem teste viável:** 6 das 6 comparações previstas (uma por categoria) são inviáveis por suporte; os 2 valores-p de H19 em A vêm **exclusivamente** da sensibilidade de elegibilidade (≥2 menções por grupo), exploratória e não confirmatória.
- Sensibilidade de vínculo A+B (decisão do pesquisador): 37 linhas, 21 com valor-p, **separadas** do cenário A; não alteram o estimando principal. Total geral da matriz: 111 linhas; 61 valores-p (40 em A + 21 em A+B). Os 40 de A **não** são todos do escopo principal previsto.
- Com BH < 0,05 no cenário A: 4 testes (H4, H8); ver §10 para leitura e ressalvas (em especial H4, confundido com local).
- Apenas até 30 audiências são unidades inferenciais; as 1288 menções são unidades de contagem.

## 2. Decisões e precedência

1. **Vínculo institucional (decisão do pesquisador, `config/decisao_vinculo_institucional.json`):** Vínculo indireto somente em análise de sensibilidade. Análise principal: A: pessoa identificada por audiência e nome. Sensibilidade: A+B: acrescenta vínculos por entidade, com categoria compatível e procedência explícita. A decisão não está mais pendente.
2. Categoria do ator: **o XLSX final é a autoridade** (inclui Partido Político). A categoria do JSON (`classificacao`) coincide com o XLSX em 405/405 linhas. O campo `categoria_revisada = Pendente` do JSON (7 linhas, todas com categoria final Partido Político) é **histórico** e não autoriza alterar a categoria da planilha nem indica erro dela; não há divergência final de rótulos.
3. Os rótulos finais (tipo da menção e categoria do ator) são usados como estão; nada foi reavaliado. Proveniência das 1288 inclusões: 1019 sem revisão humana registrada e 269 humanas consolidadas. A incerteza de classificação, cobertura e vieses **não** está representada em nenhum IC: os ICs por reamostragem (bootstrap) de audiências descrevem só a variabilidade das audiências observadas sob essa reamostragem; não pressupõem amostra probabilística nem representatividade.
4. A coluna "Menção incorporada" da lista de atores é metadado e não filtro: o corpus é a decisão `Incorporar`. Discordâncias entre o indicador Sim/Não e o derivado da ponte A: 0; zeros não são inferidos de linhas ausentes.
5. AP33: o cadastro traz intervalo julgamento−audiência = -1 ano; o dado original é **preservado** e não tratado como duração negativa verdadeira. Fica fora do denominador de H2 e H16 (explícito na coluna N/Limitações) e entra nas demais análises com o ano de julgamento cadastrado; sensibilidade com o valor mantido em H2.

## 3. Integração e validações

Chave: (audiência, nome normalizado) — NFKD sem diacriticos; casefold; caracteres nao alfanumericos viram espaco; espacos colapsados. Sem fuzzy. Chave = (audiencia, nome normalizado). Separador do campo Pessoa: ` | `. IDs de menção e de ator não coincidem; sem fuzzy. As validações críticas **interrompem** a execução antes de qualquer resultado (`src/validacao.py`); as contagens abaixo foram recalculadas das fontes brutas.

| Item | Valor | Observação |
|---|---|---|
| Linhas da planilha de menções | 3455 | colunas: 20 |
| Incorporadas (IDs únicos) | 1288 | recalculado da planilha: 1288 |
| Atores (XLSX = JSON) | 405 | IDs únicos; prefixo E: 0 |
| Tokens de pessoa (campo Pessoa) | 380 | status: {'resolvido': 380} |
| Pares menção–pessoa únicos (nível A) | 380 | plano: 380 |
| Menções com vínculo direto A | 307 | plano: 307 |
| Atores com menção direta A | 141 | plano: 141 |
| Menções classificadas multirrótulo (A) | 24 | flags sobrepõem-se; cada menção conta uma vez no universo |
| Menções mistas A (classificado + pessoa não resolvida) | 0 | explícitas na tabela principal |

Estados mutuamente exclusivos por menção (cada menção em exatamente um): `classificado` (≥1 vínculo com categoria válida; **Outros e Partido Político são categorias válidas, não NA**), `identificado_sem_classificacao` (há pessoa/instituição nos campos, mas sem vínculo direto — não é Outros nem genérico), `identificado_irresolvido_categoria_contraditoria` (entidade cujas pessoas afiliadas têm categorias distintas), `generica_nao_aplicavel` (**exige** que o alvo da extração confirme "audiência pública" além dos campos vazios) e `sem_nome_alvo_nao_generico`.

| Estado | A (principal) | % A | A+B (sensibilidade) | % A+B |
|---|---|---|---|---|
| classificado | 307 | 23,8 | 616 | 47,8 |
| generica_nao_aplicavel | 670 | 52,0 | 670 | 52,0 |
| identificado_sem_classificacao | 311 | 24,1 | 2 | 0,2 |

Categorias entre as menções classificadas (prevalências **sobrepostas**; não somam o total):

| Categoria | Menções A | Menções A+B | Atores na lista final |
|---|---|---|---|
| Atores públicos | 77 | 263 | 138 |
| Atores privados | 10 | 21 | 38 |
| Sociedade civil | 141 | 250 | 120 |
| Acadêmicos | 102 | 114 | 83 |
| Partidos Políticos | 0 | 0 | 7 |
| Outros | 10 | 10 | 19 |

**Sensibilidade A+B — construção.** A unidade do vínculo institucional é a **entidade** (audiência, entidade normalizada), não a pessoa afiliada: 326 entidades; 0 com categorias contraditórias entre afiliados (ficariam irresolvidas). A categoria da entidade é um **proxy** (categoria da participação das pessoas afiliadas). Pessoas afiliadas não são contadas como mencionadas: a categoria entra uma vez por (menção, categoria). Vários alvos com categorias distintas formam menção multirrótulo resolvida (31 menções em A+B). Menções classificadas: 307 em A e 616 em A+B (309 só via B); menções mistas (classificadas e com algum alvo não resolvido) em A+B: 11. Candidatos de proveniência: `data/processed/ponte_B_candidatos_proveniencia.csv`; entidades: `data/processed/entidades_B.csv`.

## 4. Desenho inferencial

- Unidade: audiência. Contrastes internos (H4, H8, H11, H12, H17, H19) são calculados dentro de audiência (ou documento×audiência em H4) e reduzidos a **um valor por audiência**; o estimando é a média dessas diferenças (pesos iguais). IC: bootstrap percentil (reamostragem) de audiências. Regra de emissão: comparações entre eixos exigem ≥10 audiências **em cada eixo**; contrastes internos e correlações exigem ≥10 audiências no total; o N dos grupos (ex.: 9+10) aparece na coluna N e na Incerteza. Ex.: H20 tem 19 audiências elegíveis (9+10) e, por ter menos de 10 em um eixo, não emite IC. p: **inversão de sinais** das diferenças por audiência — exato (2^n) para n ≤ 16 e Monte Carlo com +1 acima disso — que **assume simetria em torno de zero sob a nula**; não é teste exato geral de igualdade nem causal. p e IC referem-se à mesma média; a mediana é descritiva e é outro estimando.
- Comparações entre audiências (H1, H2, H5, H9, H15, H20, H22): permutação de rótulos/valores **entre audiências** (trocabilidade das audiências sob a nula; eixos, classes e anos não foram randomizados). Seeds por análise: `(seed global 20261105, CRC32 do rótulo)`; 9999 permutações e 4999 réplicas bootstrap; p Monte Carlo = (extremos+1)/(B+1).
- H13/H16: OLS por audiência com erros-padrão HC3 (t, n−k g.l.) e bootstrap de audiências estratificado por eixo; aproximação com poucas audiências, não causal; posto, suporte por eixo e alavancagem verificados; comparação com modelo sem interação.
- H3, H6, H10, H21: descrição com denominadores, **sem valor-p** (qualquer teste por permutação de menções ou binomial pressuporia menções independentes).
- Suporte predefinido: ≥5 audiências por teste; ≥3 menções por grupo e audiência (H4: ≥2 por documento×audiência). Abaixo do suporte o resultado é descritivo/inviável, **sem valor-p** e sem ajuste de limiares para obter testes. A única alternativa é a sensibilidade exploratória de elegibilidade de H19 (≥2 por grupo), executada para todas as categorias, rotulada como não confirmatória e em família BH própria.
- Famílias BH predeterminadas (config), aplicadas só aos testes efetivamente executados; NA preservado: F_temporal: H1, H2, H13, H16; F_ministros: H3, H4, H7, H14; F_tema: H5, H6, H15; F_estrutura: H8, H9, H10, H17, H18; F_alvos: H11, H12; F_H19: H19; F_H20: H20; F_H21: H21; F_H22: H22; F_adicional: (análises adicionais: H15 interação local×eixo); F_sens_elegibilidade: (H19 com ≥2 menções por grupo; sensibilidade exploratória); F_sensAB_H19: (H19 A+B); F_sensAB_H20: (H20 A+B); F_sensAB_H21: (H21 A+B); F_sensAB_H22: (H22 A+B); F_sensAB_elegibilidade: (H19 A+B, ≥2 por grupo). Linhas A+B e sensibilidades de elegibilidade têm famílias próprias e não entram na família principal.
- A reamostragem de blocos não estima erro de classificação, cobertura documental nem vieses; ICs condicionam-se à classificação final.

## 5. Matriz resumida por hipótese

| Hipótese | Linhas previstas (A) | Previstos com valor-p | Previstos inviáveis | Descritivos | menor valor-p BH (previstos) | Linhas adicionais/elegibilidade (A) | Adicionais com valor-p | Linhas A+B | A+B com valor-p | Observação de escopo |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | 2 | 2 | 0 | 0 | 0,8878 | 0 | 0 | 0 | 0 |  |
| H2 | 1 | 1 | 0 | 0 | 0,9341 | 0 | 0 | 0 | 0 |  |
| H3 | 1 | 0 | 0 | 1 | n/a | 0 | 0 | 0 | 0 |  |
| H4 | 2 | 1 | 1 | 0 | 0,0015 | 0 | 0 | 0 | 0 |  |
| H5 | 1 | 1 | 0 | 0 | 0,7122 | 0 | 0 | 0 | 0 |  |
| H6 | 2 | 0 | 0 | 2 | n/a | 0 | 0 | 0 | 0 |  |
| H7 | 1 | 0 | 0 | 1 | n/a | 0 | 0 | 0 | 0 |  |
| H8 | 4 | 3 | 0 | 1 | 0,0002 | 0 | 0 | 0 | 0 |  |
| H9 | 1 | 1 | 0 | 0 | 0,3263 | 0 | 0 | 0 | 0 |  |
| H10 | 3 | 0 | 0 | 3 | n/a | 0 | 0 | 0 | 0 |  |
| H11 | 4 | 3 | 0 | 1 | 0,2261 | 0 | 0 | 0 | 0 |  |
| H12 | 1 | 1 | 0 | 0 | 0,6328 | 0 | 0 | 0 | 0 |  |
| H13 | 1 | 1 | 0 | 0 | 0,8878 | 0 | 0 | 0 | 0 |  |
| H14 | 1 | 0 | 0 | 1 | n/a | 0 | 0 | 0 | 0 |  |
| H15 | 3 | 3 | 0 | 0 | 0,7122 | 3 | 3 | 0 | 0 | 3 valor(es)-p vêm de análises adicionais/sensibilidade de elegibilidade, não do escopo previsto principal |
| H16 | 1 | 1 | 0 | 0 | 0,8878 | 0 | 0 | 0 | 0 |  |
| H17 | 4 | 3 | 0 | 1 | 0,3263 | 0 | 0 | 0 | 0 |  |
| H18 | 1 | 0 | 0 | 1 | n/a | 0 | 0 | 0 | 0 |  |
| H19 | 6 | 0 | 6 | 0 | n/a | 5 | 2 | 11 | 7 | sem teste viável no escopo previsto principal (6 linhas inviáveis); 2 valor(es)-p vêm de análises adicionais/sensibilidade de elegibilidade, não do escopo previsto principal |
| H20 | 6 | 5 | 1 | 0 | 0,8651 | 0 | 0 | 6 | 5 |  |
| H21 | 7 | 0 | 2 | 5 | n/a | 0 | 0 | 7 | 0 |  |
| H22 | 13 | 9 | 4 | 0 | 0,5513 | 0 | 0 | 13 | 9 |  |

Contagens por escopo: *previstas* = estimando principal previsto (cenário A); *adicionais/elegibilidade* = análises extras sobre A (H15 local×eixo; H19 elegibilidade); *A+B* = sensibilidade de vínculo. Perguntas por hipótese: `results/h1_h22/resumo_por_hipotese.csv`.

A matriz completa (14 colunas exigidas + Análise, Escopo do teste, Teste, Família e valores numéricos; H1–H22 todas presentes, inclusive inviáveis) está em `results/h1_h22/matriz_resultados_H1_H22.csv`.

## 6. Resultados por hipótese (cenário A; escopo indicado quando não é o previsto principal)

### H1 — A taxa argumentativa por audiência varia com o ano do julgamento?

- **Ano do julgamento × taxa por audiência** — N: 30 audiências; 1288 menções. ρ de Spearman = -0,170. IC95% bootstrap de audiências [-0,555; +0,287] (n=30). valor-p 0,370; BH 0,888. *Executado (exploratório).*
  - Robustez: sem_Relatório: -0,268 (p=0,150, 30 AP); sem_AP33: -0,187 (p=0,328, 29 AP); sem_maior_audiência: -0,149 (p=0,457, 29 AP); autoria_plena_sem_atribuição_por_metadado: -0,155 (p=0,395, 29 AP); retirar uma audiência: -0,235 a -0,083, mesmo sinal em 30/30; Pearson ponderado por menções (permutação entre audiências): -0,506 (p=0,032)
  - valor-p 0,3696; BH 0,8878 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Ano da audiência × taxa por audiência (secundário)** — N: 30 audiências; 1288 menções. ρ de Spearman = -0,073. IC95% bootstrap de audiências [-0,436; +0,334] (n=30). valor-p 0,710; BH 0,888. *Executado (exploratório).*
  - Robustez: sem_Relatório: -0,233 (p=0,193, 30 AP); sem_AP33: -0,126 (p=0,504, 29 AP); sem_maior_audiência: -0,056 (p=0,781, 29 AP); autoria_plena_sem_atribuição_por_metadado: -0,191 (p=0,354, 29 AP); retirar uma audiência: -0,127 a +0,023, mesmo sinal em 27/30
  - valor-p 0,7102; BH 0,8878 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Poucas audiências por ano; composição temática varia com o calendário; eixos não randomizados; ano de julgamento único por audiência (AP5 tem duas datas no mesmo ano). Taxa = composição das menções observadas, não probabilidade de aproveitamento.

### H2 — O intervalo em anos (julgamento − audiência) associa-se à taxa argumentativa?

- **Intervalo em anos (julgamento − audiência) × taxa** — N: 29 audiências; 1285 menções (excluídas: 1 audiência com 3 menções). ρ de Spearman = +0,017. IC95% bootstrap de audiências [-0,390; +0,428] (n=29). valor-p 0,934; BH 0,934. *Executado (exploratório).*
  - Robustez: sem_Relatório: +0,120 (p=0,558, 29 AP); sem_maior_audiência: +0,014 (p=0,947, 28 AP); autoria_plena_sem_atribuição_por_metadado: +0,287 (p=0,128, 28 AP); retirar uma audiência: -0,063 a +0,132, mesmo sinal em 20/30; sensibilidade com o valor cadastrado (−1) mantido, todas as 30 audiências: ρ=-0,061 (p=0,750)
  - valor-p 0,9341; BH 0,9341 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Diferença de anos (não duração em dias). DENOMINADOR EXCLUÍDO: AP33 (3 menções; intervalo cadastrado -1 ano) — o valor −1 é o dado original preservado (inconsistência cadastral não resolvida), não duração negativa verdadeira; fora do estimando de H2, mantido em todas as demais análises. Poucas audiências por ano; composição temática varia com o calendário; eixos não randomizados; ano de julgamento único por audiência (AP5 tem duas datas no mesmo ano). Taxa = composição das menções observadas, não probabilidade de aproveitamento.

### H3 — A taxa argumentativa observada difere entre ministros, inclusive dentro do mesmo documento? (descrição com denominadores)

- **Heterogeneidade observada entre ministros (descrição com denominadores)** — N: 12 ministros (≥15 menções, ≥3 audiências, autoria plena); 1161 menções. 12 ministros com suporte; taxa observada por ministro: mín 0,077, quartis 0,305/0,338/0,406, máx 1,000; 32 documentos com ≥2 ministros (≥2 menções cada), amplitude mediana de taxas dentro do documento 0,500. não emitida (descrição). sem valor-p. *Descritivo (heterogeneidade observada; sem valor-p).*
  - Robustez: Ver T_H3_ministros_com_suporte.csv, T_suporte_ministros.csv e T_H3_amplitude_dentro_documento.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.

  Limitações: 291 menções têm ministro atribuído por metadado (relator), não por fala: não é autoria pessoal; 17 sem autoria plena; sem universo de votos; Relatório ≠ voto; local de menção não controlado; taxas com denominador pequeno são instáveis; sem inferência sobre preferências individuais.

### H4 — Relator cadastrado vs. demais julgadores fora do Relatório, pareados no documento

- **Relator cadastrado − demais julgadores (fora do Relatório; associação documental exploratória)** — N: 24 audiências elegíveis; 959 menções. contraste médio por audiência = +0,236 (+23,6 p.p.). IC95% bootstrap de audiências [+0,113; +0,355] (n=24). valor-p 0,002; BH 0,002. *Executado (exploratório).*
  - Robustez: sem_AP33: +0,236 (p=0,002, 24 AP); sem_maior_audiência: +0,241 (p=0,003, 23 AP); autoria_plena_sem_atribuição_por_metadado: +0,241 (p=0,001, 23 AP); retirar uma audiência: +0,210 a +0,264, mesmo sinal em 29/29; peso por menção (n1·n0/(n1+n0)): +0,113; mediana por audiência (descritiva; estimando distinto da média): +0,226; audiências com contraste >0: 20, <0: 4, =0: 0
  - valor-p 0,0015; BH 0,0015 < 0,05: compatível com associação exploratória nesta amostra de audiências observadas. Associação observacional, não causal, sem representatividade populacional.
- **Relator cadastrado − demais (apenas local = Voto, controla o local)** — N: 0 audiências elegíveis; 0 menções. n/d. não emitida (suporte insuficiente). sem valor-p. *Inviável: suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 0).*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 0)

  Limitações: CONFUSÃO RELATOR × LOCAL: só 0 de 504 menções do relator (fora do Relatório) estão em local=Voto (as demais em Voto do Relator); o contraste mistura relator e local e NÃO mede efeito da função de relator. Associação documental exploratória. Relator cadastrado extraído automaticamente; Voto não garante autoria de outro julgador; processos conexos compartilham texto (blocos documento×audiência; um valor por audiência); sem universo de votos. | Controla o local; se não houver audiências elegíveis, o efeito da função de relator não é separável do local nestes dados.

### H5 — Os dois eixos temáticos diferem na taxa argumentativa?

- **Eixo ambiental/mercado − personalidade (taxa por audiência)** — N: 18 vs 12 audiências; 1288 menções. Δ = +0,030 (+3,0 p.p.). IC95% bootstrap de audiências [-0,111; +0,172] (n=18+12). valor-p 0,712; BH 0,712. *Executado (exploratório).*
  - Robustez: sem_Relatório: +0,020 (p=0,817, 30 AP); sem_AP33: +0,013 (p=0,872, 29 AP); sem_maior_audiência: +0,019 (p=0,807, 29 AP); autoria_plena_sem_atribuição_por_metadado: +0,046 (p=0,601, 29 AP); retirar uma audiência: +0,011 a +0,062, mesmo sinal em 30/30; peso por menção (taxas agregadas; estimando distinto): +0,036 (0,409 vs 0,373)
  - valor-p 0,7122; BH 0,7122 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Eixos não randomizados; audiências não amostradas aleatoriamente; sem efeito causal do tema; sem representatividade.

### H6 — Quanta heterogeneidade observada há entre audiências dentro dos eixos? (descrição; sem teste de pseudorreplicação)

- **Heterogeneidade observada entre audiências — Ambiental/políticas/mercado** — N: 18 audiências; 585 menções. taxas por audiência: mín 0,00, quartis 0,20/0,39/0,59, máx 0,70; desvio-padrão 0,231; menores: AP28 0,00 (n=2), AP41 0,06 (n=34), AP38 0,14 (n=84); maiores: AP18 0,70 (n=10), AP8 0,70 (n=70), AP33 0,67 (n=3). não emitida (descrição). sem valor-p. *Descritivo (heterogeneidade observada; sem valor-p).*
  - Robustez: Ver T_H6_taxas_por_audiencia.csv e T_H6_resumo_por_eixo.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Heterogeneidade observada entre audiências — Personalidade** — N: 12 audiências; 703 menções. taxas por audiência: mín 0,17, quartis 0,21/0,28/0,47, máx 0,71; desvio-padrão 0,177; menores: AP13 0,17 (n=29), AP5 0,19 (n=27), AP11 0,21 (n=14); maiores: AP4 0,71 (n=75), AP17 0,60 (n=15), AP1 0,49 (n=45). não emitida (descrição). sem valor-p. *Descritivo (heterogeneidade observada; sem valor-p).*
  - Robustez: Ver T_H6_taxas_por_audiencia.csv e T_H6_resumo_por_eixo.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.

  Limitações: Descrição; não identifica a causa da dispersão; tema específico confunde-se com audiência; taxas com poucos denominadores oscilam muito; dependência entre menções do mesmo texto.

### H7 — Interação ministro × eixo

- **Ministro × eixo** — N: 20 ministros com autoria plena; 8 com suporte nos dois eixos. 8 ministros com ≥15 menções e ≥3 audiências em ambos os eixos. não emitida. sem valor-p. *Descritivo (interação ampla desaconselhada; suporte listado).*
  - Descrição/exploração sem teste inferencial; não interpretar como associação.

  Limitações: Células escassas; atribuição automática; autoria por metadado em 291 menções; ministros diferem em audiências e documentos; sem universo de votos.

### H8 — A distribuição Contexto/Relato/Argumento varia com o local no acórdão? (3 categorias descritivas + contraste de Argumento por audiência)

- **Distribuição Contexto/Relato/Argumento por local (3 categorias, descritiva)** — N: 1288 menções; 30 audiências. Relatório: Contexto 50,8%, Relato 41,7%, Argumento 7,4% (n=242); Voto do Relator: Contexto 31,5%, Relato 19,2%, Argumento 49,2% (n=504); Voto: Contexto 41,9%, Relato 14,8%, Argumento 43,4% (n=542). não emitida (descrição). sem valor-p. *Descritivo (3 categorias; sem valor-p).*
  - Robustez: Médias das proporções por audiência: Relatório: C 0,795/R 0,181/A 0,024; Voto do Relator: C 0,263/R 0,161/A 0,576; Voto: C 0,513/R 0,140/A 0,347
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Taxa argumentativa: Voto do Relator − Relatório** — N: 16 audiências elegíveis; 595 menções. contraste médio por audiência = +0,540 (+54,0 p.p.). IC95% bootstrap de audiências [+0,403; +0,664] (n=16). valor-p <0,001; BH <0,001. *Executado (exploratório).*
  - Robustez: sem_AP33: +0,540 (p=<0,001, 16 AP); sem_maior_audiência: +0,535 (p=<0,001, 15 AP); autoria_plena_sem_atribuição_por_metadado: +0,500 (p=n/d, 2 AP); retirar uma audiência: +0,509 a +0,573, mesmo sinal em 30/30; peso por menção (n1·n0/(n1+n0)): +0,485; mediana por audiência (descritiva; estimando distinto da média): +0,538; audiências com contraste >0: 16, <0: 0, =0: 0
  - valor-p 0,0000; BH 0,0002 < 0,05: compatível com associação exploratória nesta amostra de audiências observadas. Associação observacional, não causal, sem representatividade populacional.
- **Taxa argumentativa: Voto − Relatório** — N: 17 audiências elegíveis; 676 menções. contraste médio por audiência = +0,317 (+31,7 p.p.). IC95% bootstrap de audiências [+0,201; +0,432] (n=17). valor-p <0,001; BH <0,001. *Executado (exploratório).*
  - Robustez: sem_AP33: +0,317 (p=<0,001, 17 AP); sem_maior_audiência: +0,312 (p=<0,001, 16 AP); autoria_plena_sem_atribuição_por_metadado: +0,181 (p=n/d, 3 AP); retirar uma audiência: +0,292 a +0,337, mesmo sinal em 30/30; peso por menção (n1·n0/(n1+n0)): +0,369; mediana por audiência (descritiva; estimando distinto da média): +0,391; audiências com contraste >0: 15, <0: 0, =0: 2
  - valor-p 0,0002; BH 0,0007 < 0,05: compatível com associação exploratória nesta amostra de audiências observadas. Associação observacional, não causal, sem representatividade populacional.
- **Taxa argumentativa: Voto − Voto do Relator** — N: 20 audiências elegíveis; 931 menções. contraste médio por audiência = -0,201 (-20,1 p.p.). IC95% bootstrap de audiências [-0,338; -0,067] (n=20). valor-p 0,010; BH 0,024. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,201 (p=0,013, 20 AP); sem_maior_audiência: -0,229 (p=0,005, 19 AP); autoria_plena_sem_atribuição_por_metadado: -0,207 (p=0,015, 19 AP); retirar uma audiência: -0,234 a -0,172, mesmo sinal em 30/30; peso por menção (n1·n0/(n1+n0)): -0,095; mediana por audiência (descritiva; estimando distinto da média): -0,208; audiências com contraste >0: 5, <0: 15, =0: 0
  - valor-p 0,0103; BH 0,0240 < 0,05: compatível com associação exploratória nesta amostra de audiências observadas. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Local extraído automaticamente; menções do mesmo documento/ministro são correlacionadas; o Relatório tem função documental distinta; agregado por menção e média por audiência respondem a perguntas diferentes. | Local extraído automaticamente; menções do mesmo documento correlacionadas (um valor por audiência); relatório tem função documental distinta; observacional.


  **Nota metodológica sobre H8 (dependência conceitual).** A metodologia de classificação adotada (documento raiz METODOLOGIA_ANALISE_MENCOES_AUDIENCIAS.md, seção 14.2) afirma: "Estar no voto, fora do relatório ou próximo de uma conclusão é indício, mas não condição suficiente." Assim, a localização/contexto argumentativo foi um dos indícios usados para decidir o tipo (Contexto, Relato ou Argumento). A associação H8 entre local e tipo não é, portanto, validação independente da tipologia, e parte do padrão pode refletir a própria operacionalização. Isso não configura tautologia estrita (há Argumentos no Relatório) e não descarta os contrastes estatísticos: indica apenas risco de dependência conceitual/incorporação do contexto e exige cautela interpretativa. Nada disso permite inferir eficácia democrática, mudança de voto ou impacto causal. A nota é relevante porque H8 concentra os achados com BH < 0,05.

### H9 — A taxa argumentativa difere entre classes processuais?

- **Classe processual (ADI, ADPF, RE)** — N: 25 audiências de classe única; classes testadas: ADI, ADPF, RE. H = 2,941; médias das taxas por audiência: ADI 0,40 (n=14); ADPF 0,28 (n=4); RE 0,26 (n=7). IC não emitido. valor-p 0,233; BH 0,326. *Executado (exploratório).*
  - Robustez: sem_AP33: +2,941 (p=0,233, 25 AP); sem_maior_audiência: +3,174 (p=0,188, 24 AP)
  - valor-p 0,2331; BH 0,3263 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Classe e tema confundidos; audiências com várias classes excluídas do teste; classes raras ficam sem teste; observacional.

### H10 — Argumentos estão mais concentrados do que as menções (audiência, documento, ministro)? (Gini/top-k descritivos)

- **Concentração de argumentos por audiência (descritiva)** — N: 30 unidades; 1288 menções; 501 argumentos. Gini argumentos 0,578 vs menções 0,504; top-3 argumentos 39,5% vs menções 37,8%; n efetivo argumentos 16,7 vs menções 19,2. não emitida (descrição). sem valor-p. *Descritivo (concentração observada; sem valor-p).*
  - Robustez: T_H10_concentracao.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Concentração de argumentos por documento (descritiva)** — N: 46 unidades; 1288 menções; 501 argumentos. Gini argumentos 0,450 vs menções 0,398; top-3 argumentos 25,9% vs menções 23,5%; n efetivo argumentos 30,5 vs menções 33,5. não emitida (descrição). sem valor-p. *Descritivo (concentração observada; sem valor-p).*
  - Robustez: T_H10_concentracao.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Concentração de argumentos por ministro (autoria plena) (descritiva)** — N: 20 unidades; 1271 menções; 495 argumentos. Gini argumentos 0,595 vs menções 0,564; top-3 argumentos 54,3% vs menções 50,4%; n efetivo argumentos 10,6 vs menções 11,6. não emitida (descrição). sem valor-p. *Descritivo (concentração observada; sem valor-p).*
  - Robustez: T_H10_concentracao.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.

  Limitações: Reflete extensão e cobertura documental, não escolhas individuais; unidades com zero menções não observadas; ministro tem atribuição por metadado em parte das menções.

### H11 — A função da menção varia com o tipo de alvo (proxy por campos preenchidos)?

- **Distribuição Contexto/Relato/Argumento por tipo de alvo derivado (3 categorias, descritiva)** — N: 1288 menções. Instituição: C 34,7%, R 31,2%, A 34,1% (n=311); Pessoa: C 9,5%, R 40,0%, A 50,5% (n=95); Pessoa e instituição: C 30,7%, R 38,7%, A 30,7% (n=212); Sem pessoa/instituição nos campos: C 48,8%, R 9,1%, A 42,1% (n=670). não emitida (descrição). sem valor-p. *Descritivo (3 categorias; sem valor-p).*
  - Robustez: T_H11_tipo_alvo_x_tipo_mencao.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Taxa argumentativa: Pessoa − Sem pessoa/instituição nos campos** — N: 8 audiências elegíveis; 342 menções. contraste médio por audiência = +0,057 (+5,7 p.p.). IC não emitido (exige ≥10 audiências no total; n=8). valor-p 0,633; BH 0,633. *Executado (exploratório).*
  - Robustez: sem_Relatório: +0,161 (p=0,312, 6 AP); sem_AP33: +0,057 (p=0,633, 8 AP); sem_maior_audiência: -0,015 (p=0,875, 7 AP); retirar uma audiência: -0,015 a +0,097, mesmo sinal em 27/29; peso por menção (n1·n0/(n1+n0)): +0,235; mediana por audiência (descritiva; estimando distinto da média): -0,086; audiências com contraste >0: 3, <0: 5, =0: 0
  - valor-p 0,6328; BH 0,6328 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Taxa argumentativa: Instituição − Sem pessoa/instituição nos campos** — N: 16 audiências elegíveis; 746 menções. contraste médio por audiência = -0,037 (-3,7 p.p.). IC95% bootstrap de audiências [-0,165; +0,102] (n=16). valor-p 0,609; BH 0,633. *Executado (exploratório).*
  - Robustez: sem_Relatório: +0,026 (p=0,657, 13 AP); sem_AP33: -0,037 (p=0,609, 16 AP); sem_maior_audiência: -0,068 (p=0,335, 15 AP); retirar uma audiência: -0,073 a -0,001, mesmo sinal em 30/30; peso por menção (n1·n0/(n1+n0)): +0,001; mediana por audiência (descritiva; estimando distinto da média): -0,076; audiências com contraste >0: 7, <0: 9, =0: 0
  - valor-p 0,6094; BH 0,6328 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Taxa argumentativa: Pessoa e instituição − Sem pessoa/instituição nos campos** — N: 14 audiências elegíveis; 565 menções. contraste médio por audiência = -0,151 (-15,1 p.p.). IC95% bootstrap de audiências [-0,286; -0,014] (n=14). valor-p 0,057; BH 0,226. *Executado (exploratório).*
  - Robustez: sem_Relatório: -0,077 (p=0,393, 10 AP); sem_AP33: -0,151 (p=0,057, 14 AP); sem_maior_audiência: -0,156 (p=0,069, 13 AP); retirar uma audiência: -0,190 a -0,114, mesmo sinal em 29/29; peso por menção (n1·n0/(n1+n0)): -0,063; mediana por audiência (descritiva; estimando distinto da média): -0,126; audiências com contraste >0: 4, <0: 10, =0: 0
  - valor-p 0,0565; BH 0,2261 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Proxy por campos Pessoa/Instituição preenchidos; não indica ação, influência ou individualização substantiva; campos vazios isolados não provam referência genérica. | Proxy por campos Pessoa/Instituição preenchidos; não indica ação, influência ou individualização substantiva; campos vazios não provam referência genérica; nº de alvos ≠ nº de contribuições.

### H12 — Menções com pessoa/instituição nomeada vs. sem nome nos campos: taxa argumentativa

- **Individualizada (pessoa ou instituição nos campos) − sem nome** — N: 23 audiências elegíveis; 1222 menções. contraste médio por audiência = -0,052 (-5,2 p.p.). IC95% bootstrap de audiências [-0,161; +0,061] (n=23). valor-p 0,389; BH 0,633. *Executado (exploratório).*
  - Robustez: sem_Relatório: +0,001 (p=0,992, 19 AP); sem_AP33: -0,052 (p=0,401, 23 AP); sem_maior_audiência: -0,068 (p=0,236, 22 AP); retirar uma audiência: -0,080 a -0,027, mesmo sinal em 30/30; peso por menção (n1·n0/(n1+n0)): +0,024; mediana por audiência (descritiva; estimando distinto da média): -0,068; audiências com contraste >0: 7, <0: 16, =0: 0
  - valor-p 0,3888; BH 0,6328 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Proxy por campos Pessoa/Instituição preenchidos; não indica ação, influência ou individualização substantiva; campos vazios não provam referência genérica; nº de alvos ≠ nº de contribuições. H12 agrega os contrastes de H11 (não são independentes).

### H13 — A tendência temporal difere entre eixos?

- **Ano do julgamento × eixo** — N: 30 audiências (18 ambiental/mercado; 12 personalidade). interação (inclinação ambiental − personalidade) = +0,0107 por unidade de x; inclinação personalidade -0,0179 (EP HC3 0,0075); ambiental -0,0072 (EP HC3 0,0184); R² = 0,092. EP HC3 0,0199; IC95% HC3 [-0,0301; +0,0515]; IC95% bootstrap de audiências [-0,0305; +0,0388] (4999 réplicas válidas). valor-p 0,595; BH 0,888. *Executado (exploratório).*
  - Robustez: posto 4/4; alavancagem máxima 0,40; modelo sem interação: inclinação comum -0,0122 (EP HC3 0,0099); retirar uma audiência: -0,0032 a +0,0174, mesmo sinal em 29/30
  - valor-p 0,5949; BH 0,8878 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Interação com poucas audiências por eixo; eixos e calendário confundidos; observacional; modelo parcimonioso, não causal.

### H14 — Evolução temporal por ministro

- **Ministro × ano** — N: 20 ministros; 8 com ≥3 anos com ≥5 menções. 8 ministros com cobertura de ≥3 anos. não emitida. sem valor-p. *Descritivo (modelo amplo desaconselhado).*
  - Descrição/exploração sem teste inferencial; não interpretar como associação.

  Limitações: Composição da Corte e atribuição documental variam; ausência de linha ≠ voto sem menção; confunde-se com audiência/documento.

### H15 — A distribuição das menções entre relatório e votos (composição por local) difere entre os eixos?

- **Prevalência de menções em "Relatório": ambiental/mercado − personalidade** — N: 17+12 audiências (≥3 menções); 1286 menções. Δ da fração em "Relatório" = -0,038 (-3,8 p.p.). IC95% bootstrap de audiências [-0,194; +0,107] (n=17+12). valor-p 0,618; BH 0,712. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,026 (p=0,736, 28 AP); sem_maior_audiência: -0,040 (p=0,623, 28 AP); retirar uma audiência: -0,061 a +0,008, mesmo sinal em 29/30; agregado por menção: Ambiental/políticas/mercado 0,157; Personalidade 0,213
  - valor-p 0,6179; BH 0,7122 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Prevalência de menções em "Voto do Relator": ambiental/mercado − personalidade** — N: 17+12 audiências (≥3 menções); 1286 menções. Δ da fração em "Voto do Relator" = +0,112 (+11,2 p.p.). IC95% bootstrap de audiências [-0,058; +0,275] (n=17+12). valor-p 0,188; BH 0,712. *Executado (exploratório).*
  - Robustez: sem_AP33: +0,099 (p=0,263, 28 AP); sem_maior_audiência: +0,100 (p=0,264, 28 AP); retirar uma audiência: +0,079 a +0,146, mesmo sinal em 30/30; agregado por menção: Ambiental/políticas/mercado 0,455; Personalidade 0,339
  - valor-p 0,1882; BH 0,7122 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Prevalência de menções em "Voto": ambiental/mercado − personalidade** — N: 17+12 audiências (≥3 menções); 1286 menções. Δ da fração em "Voto" = -0,073 (-7,3 p.p.). IC95% bootstrap de audiências [-0,227; +0,084] (n=17+12). valor-p 0,369; BH 0,712. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,073 (p=0,395, 28 AP); sem_maior_audiência: -0,060 (p=0,475, 28 AP); retirar uma audiência: -0,111 a -0,040, mesmo sinal em 30/30; agregado por menção: Ambiental/políticas/mercado 0,388; Personalidade 0,448
  - valor-p 0,3690; BH 0,7122 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **[análise adicional] Contraste de Argumento Voto do Relator − Relatório: diferença entre eixos** [escopo: adicional local×eixo] — N: 10+6 audiências elegíveis. Δ de contrastes = +0,066. IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=10+6). valor-p 0,659; BH 0,856. *Executado (exploratório).*
  - Robustez: retirar uma audiência elegível: -0,021 a +0,166, mesmo sinal em 15/16
  - valor-p 0,6587; BH 0,8562 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **[análise adicional] Contraste de Argumento Voto − Relatório: diferença entre eixos** [escopo: adicional local×eixo] — N: 10+7 audiências elegíveis. Δ de contrastes = -0,024. IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=10+7). valor-p 0,850; BH 0,856. *Executado (exploratório).*
  - Robustez: retirar uma audiência elegível: -0,075 a +0,040, mesmo sinal em 12/17
  - valor-p 0,8502; BH 0,8562 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **[análise adicional] Contraste de Argumento Voto − Voto do Relator: diferença entre eixos** [escopo: adicional local×eixo] — N: 12+8 audiências elegíveis. Δ de contrastes = -0,029. IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=12+8). valor-p 0,856; BH 0,856. *Executado (exploratório).*
  - Robustez: retirar uma audiência elegível: -0,095 a +0,057, mesmo sinal em 16/20
  - valor-p 0,8562; BH 0,8562 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Localização extraída automaticamente; composição de locais depende da estrutura do acórdão e do relator; observacional; 3 locais não são testes independentes. | Interação de segunda ordem com poucas audiências; observacional; exploratória.

### H16 — O efeito do intervalo difere entre eixos?

- **Intervalo × eixo** — N: 29 audiências (17 ambiental/mercado; 12 personalidade). interação (inclinação ambiental − personalidade) = +0,0614 por unidade de x; inclinação personalidade -0,0651 (EP HC3 0,0474); ambiental -0,0036 (EP HC3 0,0368); R² = 0,055. EP HC3 0,0600; IC95% HC3 [-0,0622; +0,1851]; IC95% bootstrap de audiências [-0,0296; +0,2233] (4999 réplicas válidas). valor-p 0,316; BH 0,888. *Executado (exploratório).*
  - Robustez: posto 4/4; alavancagem máxima 0,61; modelo sem interação: inclinação comum -0,0130 (EP HC3 0,0225); retirar uma audiência: +0,0309 a +0,0951, mesmo sinal em 29/29
  - valor-p 0,3161; BH 0,8878 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Interação com poucas audiências por eixo; eixos e calendário confundidos; observacional; modelo parcimonioso, não causal. AP33 (intervalo cadastrado −1) fora deste denominador.

### H17 — As referências individualizadas (tipo de alvo) distribuem-se diferentemente entre relatório e votos?

- **Distribuição do tipo de alvo por local (4 categorias, descritiva)** — N: 1288 menções. Relatório: Instituição 23,1%, Pessoa 7,9%, Pessoa e instituição 28,9%, Sem pessoa/instituição nos campos 40,1% (n=242); Voto do Relator: Instituição 26,0%, Pessoa 5,2%, Pessoa e instituição 16,3%, Sem pessoa/instituição nos campos 52,6% (n=504); Voto: Instituição 22,9%, Pessoa 9,2%, Pessoa e instituição 11,1%, Sem pessoa/instituição nos campos 56,8% (n=542). não emitida (descrição). sem valor-p. *Descritivo (4 categorias; sem valor-p).*
  - Robustez: T_H17_alvo_x_local.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Proporção individualizada (alvo com nome): Voto do Relator − Relatório** — N: 16 audiências elegíveis; 595 menções. contraste médio por audiência = -0,031 (-3,1 p.p.). IC95% bootstrap de audiências [-0,248; +0,162] (n=16). valor-p 0,775; BH 0,775. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,031 (p=0,775, 16 AP); sem_maior_audiência: -0,015 (p=0,896, 15 AP); retirar uma audiência: -0,068 a +0,025, mesmo sinal em 27/30; peso por menção (n1·n0/(n1+n0)): -0,113; mediana por audiência (descritiva; estimando distinto da média): +0,056; audiências com contraste >0: 8, <0: 7, =0: 1
  - valor-p 0,7753; BH 0,7753 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Proporção individualizada (alvo com nome): Voto − Relatório** — N: 17 audiências elegíveis; 676 menções. contraste médio por audiência = -0,070 (-7,0 p.p.). IC95% bootstrap de audiências [-0,263; +0,135] (n=17). valor-p 0,515; BH 0,600. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,070 (p=0,504, 17 AP); sem_maior_audiência: -0,071 (p=0,529, 16 AP); retirar uma audiência: -0,121 a -0,019, mesmo sinal em 30/30; peso por menção (n1·n0/(n1+n0)): -0,127; mediana por audiência (descritiva; estimando distinto da média): -0,041; audiências com contraste >0: 6, <0: 10, =0: 1
  - valor-p 0,5147; BH 0,6005 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Proporção individualizada (alvo com nome): Voto − Voto do Relator** — N: 20 audiências elegíveis; 931 menções. contraste médio por audiência = -0,087 (-8,7 p.p.). IC95% bootstrap de audiências [-0,202; +0,046] (n=20). valor-p 0,207; BH 0,326. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,087 (p=0,192, 20 AP); sem_maior_audiência: -0,091 (p=0,183, 19 AP); retirar uma audiência: -0,131 a -0,065, mesmo sinal em 30/30; peso por menção (n1·n0/(n1+n0)): -0,049; mediana por audiência (descritiva; estimando distinto da média): -0,057; audiências com contraste >0: 7, <0: 12, =0: 1
  - valor-p 0,2073; BH 0,3263 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Proxy por campos Pessoa/Instituição preenchidos; não indica ação, influência ou individualização substantiva; campos vazios não provam referência genérica; nº de alvos ≠ nº de contribuições. Local extraído automaticamente. | Proxy por campos Pessoa/Instituição preenchidos; não indica ação, influência ou individualização substantiva; campos vazios não provam referência genérica; nº de alvos ≠ nº de contribuições. Local extraído automaticamente; um valor por audiência.

### H18 — Perfis exploratórios de composição Contexto/Relato/Argumento por audiência

- **Perfis de composição por audiência (PCA CLR; agrupamento hierárquico de Ward)** — N: 30 audiências. PC1 explica 67,2% da variação da composição (3 partes têm só 2 dimensões); ARI mediana: k=2: 0,26; k=3: 0,37; k=4: 0,39. sem p-valor (exploratório). sem valor-p. *Exploratório descritivo (sem inferência).*
  - Robustez: ARI por k na tabela H18_estabilidade_clusters; critério de perfil estável: ARI mediana ≥0,8 (nenhum k atingiu o critério: não se declara perfil)
  - Descrição/exploração sem teste inferencial; não interpretar como associação.

  Limitações: Perfis não são classes preexistentes; tamanhos muito desiguais; a reamostragem multinomial só capta variação de amostragem das menções (supondo independência), não erro de classificação, cobertura ou viés; dependência documental ignorada.

### H19 — Menções vinculadas a cada categoria de ator têm taxa argumentativa diferente das vinculadas sem a categoria? (principal: A; sensibilidade: A+B)

- **Categoria Atores públicos: presente − ausente (taxa argumentativa)** — N: 4 audiências elegíveis; 191 menções. contraste médio descritivo = -0,093 (4 audiências). não emitida (suporte insuficiente). sem valor-p. *Inviável: suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 4).*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 4)
- **Categoria Atores públicos: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2 por grupo]** [escopo: sensibilidade de elegibilidade] — N: 9 audiências elegíveis; 223 menções. contraste médio por audiência = +0,049 (+4,9 p.p.). IC não emitido (exige ≥10 audiências no total; n=9). valor-p 0,938; BH 0,938. *Exploratório: sensibilidade de elegibilidade (não confirmação).*
  - Robustez: sem_AP33: +0,049 (p=0,938, 9 AP); sem_maior_audiência: +0,059 (p=0,938, 8 AP); autoria_plena_sem_atribuição_por_metadado: +0,149 (p=0,625, 6 AP); retirar uma audiência: -0,069 a +0,090, mesmo sinal em 24/25; peso por menção (n1·n0/(n1+n0)): -0,094; mediana por audiência (descritiva; estimando distinto da média): +0,000; audiências com contraste >0: 2, <0: 4, =0: 3
  - valor-p 0,9375; BH 0,9375 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito (sensibilidade exploratória; não confirmatório). Associação observacional, não causal, sem representatividade populacional.
- **Categoria Atores privados: presente − ausente (taxa argumentativa)** — N: 1 audiências elegíveis; 13 menções. contraste médio descritivo = +0,233 (1 audiências). não emitida (suporte insuficiente). sem valor-p. *Inviável: suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 1).*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 1)
- **Categoria Atores privados: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2 por grupo]** [escopo: sensibilidade de elegibilidade] — N: 1 audiências elegíveis; 13 menções. contraste médio descritivo = +0,233 (1 audiências). não emitida (suporte insuficiente). sem valor-p. *Inviável: suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 1) [sensibilidade exploratória de elegibilidade].*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 1) [sensibilidade exploratória de elegibilidade]
- **Categoria Sociedade civil: presente − ausente (taxa argumentativa)** — N: 4 audiências elegíveis; 191 menções. contraste médio descritivo = -0,060 (4 audiências). não emitida (suporte insuficiente). sem valor-p. *Inviável: suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 4).*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 4)
- **Categoria Sociedade civil: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2 por grupo]** [escopo: sensibilidade de elegibilidade] — N: 8 audiências elegíveis; 219 menções. contraste médio por audiência = -0,104 (-10,4 p.p.). IC não emitido (exige ≥10 audiências no total; n=8). valor-p 0,625; BH 0,938. *Exploratório: sensibilidade de elegibilidade (não confirmação).*
  - Robustez: sem_AP33: -0,104 (p=0,625, 8 AP); sem_maior_audiência: -0,105 (p=0,688, 7 AP); autoria_plena_sem_atribuição_por_metadado: -0,143 (p=n/d, 4 AP); retirar uma audiência: -0,177 a +0,024, mesmo sinal em 24/25; peso por menção (n1·n0/(n1+n0)): -0,045; mediana por audiência (descritiva; estimando distinto da média): -0,038; audiências com contraste >0: 2, <0: 4, =0: 2
  - valor-p 0,6250; BH 0,9375 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito (sensibilidade exploratória; não confirmatório). Associação observacional, não causal, sem representatividade populacional.
- **Categoria Acadêmicos: presente − ausente (taxa argumentativa)** — N: 4 audiências elegíveis; 187 menções. contraste médio descritivo = -0,006 (4 audiências). não emitida (suporte insuficiente). sem valor-p. *Inviável: suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 4).*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 4)
- **Categoria Acadêmicos: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2 por grupo]** [escopo: sensibilidade de elegibilidade] — N: 4 audiências elegíveis; 187 menções. contraste médio descritivo = -0,006 (4 audiências). não emitida (suporte insuficiente). sem valor-p. *Inviável: suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 4) [sensibilidade exploratória de elegibilidade].*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 4) [sensibilidade exploratória de elegibilidade]
- **Categoria Partidos Políticos: presente − ausente** — N: 0 menções vinculadas com a categoria. n/d. n/d. sem valor-p. *Inviável: nenhuma menção vinculada com a categoria (A).*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. nenhuma menção vinculada com a categoria (A)
- **Categoria Outros: presente − ausente (taxa argumentativa)** — N: 2 audiências elegíveis; 30 menções. contraste médio descritivo = -0,138 (2 audiências). não emitida (suporte insuficiente). sem valor-p. *Inviável: suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 2).*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 2)
- **Categoria Outros: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2 por grupo]** [escopo: sensibilidade de elegibilidade] — N: 3 audiências elegíveis; 129 menções. contraste médio descritivo = -0,247 (3 audiências). não emitida (suporte insuficiente). sem valor-p. *Inviável: suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 3) [sensibilidade exploratória de elegibilidade].*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 3) [sensibilidade exploratória de elegibilidade]

  Limitações: Nível A (pessoa nomeada por audiência e nome); multirrótulo: categorias sobrepõem-se; rótulos finais do XLSX; sem universo de participantes: sem afirmar favorecimento/exclusão/representatividade; presença do nome na menção não prova que a contribuição foi aproveitada; vínculo institucional (B) só aparece na sensibilidade A+B. | Nível A (pessoa nomeada por audiência e nome); multirrótulo: categorias sobrepõem-se; rótulos finais do XLSX; sem universo de participantes: sem afirmar favorecimento/exclusão/representatividade; presença do nome na menção não prova que a contribuição foi aproveitada; vínculo institucional (B) só aparece na sensibilidade A+B. SENSIBILIDADE EXPLORATÓRIA DE ELEGIBILIDADE (≥2 menções por grupo): não é confirmação nem substitui o critério predefinido.

### H20 — A incidência de categorias de ator entre menções classificadas difere entre eixos?

- **Incidência de Atores públicos: ambiental − personalidade** — N: 9+10 audiências elegíveis; 298 menções classificadas. Δ incidência = -0,082. IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=9+10). valor-p 0,574; BH 0,865. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,082 (p=0,574, 19 AP); sem_maior_audiência: -0,068 (p=0,647, 18 AP); retirar uma audiência: -0,175 a -0,040, mesmo sinal em 30/30; incidência agregada por menção (estimando distinto): Ambiental/políticas/mercado 0,275; Personalidade 0,244
  - valor-p 0,5742; BH 0,8651 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Incidência de Atores privados: ambiental − personalidade** — N: 9+10 audiências elegíveis; 298 menções classificadas. Δ incidência = +0,110. IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=9+10). valor-p 0,381; BH 0,865. *Executado (exploratório).*
  - Robustez: sem_AP33: +0,110 (p=0,379, 19 AP); sem_maior_audiência: +0,104 (p=0,537, 18 AP); retirar uma audiência: +0,006 a +0,141, mesmo sinal em 30/30; incidência agregada por menção (estimando distinto): Ambiental/políticas/mercado 0,087; Personalidade 0,017
  - valor-p 0,3805; BH 0,8651 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Incidência de Sociedade civil: ambiental − personalidade** — N: 9+10 audiências elegíveis; 298 menções classificadas. Δ incidência = -0,032. IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=9+10). valor-p 0,849; BH 0,865. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,032 (p=0,850, 19 AP); sem_maior_audiência: +0,018 (p=0,918, 18 AP); retirar uma audiência: -0,114 a +0,018, mesmo sinal em 24/30; incidência agregada por menção (estimando distinto): Ambiental/políticas/mercado 0,203; Personalidade 0,534
  - valor-p 0,8488; BH 0,8651 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Incidência de Acadêmicos: ambiental − personalidade** — N: 9+10 audiências elegíveis; 298 menções classificadas. Δ incidência = -0,152. IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=9+10). valor-p 0,360; BH 0,865. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,152 (p=0,372, 19 AP); sem_maior_audiência: -0,178 (p=0,301, 18 AP); retirar uma audiência: -0,250 a -0,081, mesmo sinal em 30/30; incidência agregada por menção (estimando distinto): Ambiental/políticas/mercado 0,377; Personalidade 0,319
  - valor-p 0,3601; BH 0,8651 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Incidência de Partidos Políticos: ambiental − personalidade** — N: 9+10 audiências elegíveis; 0 menções com a categoria. n/d. n/d. sem valor-p. *Inviável: audiências elegíveis por eixo 9/10 (mínimo 5) e 0 menções com a categoria.*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. audiências elegíveis por eixo 9/10 (mínimo 5) e 0 menções com a categoria
- **Incidência de Outros: ambiental − personalidade** — N: 9+10 audiências elegíveis; 298 menções classificadas. Δ incidência = -0,006. IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=9+10). valor-p 0,865; BH 0,865. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,006 (p=0,855, 19 AP); sem_maior_audiência: -0,010 (p=0,725, 18 AP); retirar uma audiência: -0,032 a +0,016, mesmo sinal em 29/30; incidência agregada por menção (estimando distinto): Ambiental/políticas/mercado 0,058; Personalidade 0,025
  - valor-p 0,8651; BH 0,8651 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.

  Limitações: Nível A (pessoa nomeada por audiência e nome); incidência sobreposta (multirrótulo), não composição partitiva; cobertura de classificação difere entre eixos; observacional. | Incidência entre classificadas é prevalência sobreposta (não soma 100%).

### H21 — Ministro × categoria de ator no aproveitamento argumentativo (nArgumento/nMenções por célula; modelo só se houver suporte)

- **Ministro × Atores públicos: aproveitamento argumentativo (n Argumento / n menções com a categoria)** — N: 77 menções classificadas com a categoria; 4 ministros com ≥5 menções nela. agregado por menção: 12/77 = 0,156; entre ministros com ≥5 menções: taxas 0,08–0,32. não emitida (descrição). sem valor-p. *Descritivo (sem valor-p; não é preferência individual).*
  - Robustez: T_H21_ministro_x_categoria_aproveitamento.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Ministro × Atores privados: aproveitamento argumentativo (n Argumento / n menções com a categoria)** — N: 10 menções classificadas com a categoria; 0 ministros com ≥5 menções nela. agregado por menção: 4/10 = 0,400; nenhum ministro com ≥5 menções. não emitida (descrição). sem valor-p. *Descritivo (sem valor-p; não é preferência individual).*
  - Robustez: T_H21_ministro_x_categoria_aproveitamento.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Ministro × Sociedade civil: aproveitamento argumentativo (n Argumento / n menções com a categoria)** — N: 141 menções classificadas com a categoria; 5 ministros com ≥5 menções nela. agregado por menção: 39/141 = 0,277; entre ministros com ≥5 menções: taxas 0,03–0,47. não emitida (descrição). sem valor-p. *Descritivo (sem valor-p; não é preferência individual).*
  - Robustez: T_H21_ministro_x_categoria_aproveitamento.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Ministro × Acadêmicos: aproveitamento argumentativo (n Argumento / n menções com a categoria)** — N: 102 menções classificadas com a categoria; 7 ministros com ≥5 menções nela. agregado por menção: 59/102 = 0,578; entre ministros com ≥5 menções: taxas 0,43–1,00. não emitida (descrição). sem valor-p. *Descritivo (sem valor-p; não é preferência individual).*
  - Robustez: T_H21_ministro_x_categoria_aproveitamento.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Ministro × Partidos Políticos: aproveitamento argumentativo (n Argumento / n menções com a categoria)** — N: 0 menções classificadas com a categoria; 0 ministros com ≥5 menções nela. agregado por menção: 0/0; nenhum ministro com ≥5 menções. não emitida (descrição). sem valor-p. *Inviável: nenhuma menção vinculada com a categoria (A).*
  - Robustez: T_H21_ministro_x_categoria_aproveitamento.csv
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. nenhuma menção vinculada com a categoria (A)
- **Ministro × Outros: aproveitamento argumentativo (n Argumento / n menções com a categoria)** — N: 10 menções classificadas com a categoria; 1 ministros com ≥5 menções nela. agregado por menção: 1/10 = 0,100; entre ministros com ≥5 menções: taxas 0,00–0,00. não emitida (descrição). sem valor-p. *Descritivo (sem valor-p; não é preferência individual).*
  - Robustez: T_H21_ministro_x_categoria_aproveitamento.csv
  - Descrição/exploração sem teste inferencial; não interpretar como associação.
- **Modelo ministro × categoria no aproveitamento argumentativo (viabilidade)** — N: 4 ministros com suporte (≥15 classificadas, ≥3 audiências, autoria plena); células ministro×categoria com ≥5 menções: 10; ministros com ≥2 categorias com ≥5 menções: 3; 92 das 307 menções classificadas têm ministro atribuído por metadado. modelo não estimado. não emitida. sem valor-p. *Inviável: suporte insuficiente para interação ministro × categoria (critério: ≥4 ministros com ≥2 categorias com ≥5 menções; observado 3); atribuição por metadado e dependência dentro de documento/audiência impedem inferência individual.*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. suporte insuficiente para interação ministro × categoria (critério: ≥4 ministros com ≥2 categorias com ≥5 menções; observado 3); atribuição por metadado e dependência dentro de documento/audiência impedem inferência individual

  Limitações: Não interpretar como preferência individual: 92 menções classificadas têm ministro atribuído por metadado (relator), não por fala; menções repetidas no mesmo documento; células escassas; sem universo de votos. | Ver tabelas T_H21_*. Sem valor-p artificial.

### H22 — A composição de categorias de ator e o aproveitamento argumentativo por categoria evoluem com o ano de julgamento?

- **Ano do julgamento × taxa argumentativa entre classificadas** — N: 19 audiências; 298 menções; 11 anos. ρ = -0,132. IC95% bootstrap de audiências [-0,534; +0,319] (n=19). valor-p 0,586; BH 0,753. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,132 (p=0,590, 19 AP); sem_maior_audiência: -0,143 (p=0,588, 18 AP); retirar uma audiência: -0,237 a -0,020, mesmo sinal em 30/30
  - valor-p 0,5859; BH 0,7533 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Ano do julgamento × incidência de Atores públicos** — N: 19 audiências; 298 menções; 11 anos. ρ = -0,101. IC95% bootstrap de audiências [-0,544; +0,385] (n=19). valor-p 0,678; BH 0,763. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,101 (p=0,677, 19 AP); sem_maior_audiência: -0,123 (p=0,619, 18 AP); retirar uma audiência: -0,218 a +0,011, mesmo sinal em 28/30
  - valor-p 0,6783; BH 0,7631 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Ano do julgamento × incidência de Atores privados** — N: 19 audiências; 298 menções; 11 anos. ρ = -0,281. IC95% bootstrap de audiências [-0,617; +0,100] (n=19). valor-p 0,245; BH 0,551. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,281 (p=0,249, 19 AP); sem_maior_audiência: -0,247 (p=0,340, 18 AP); retirar uma audiência: -0,366 a -0,191, mesmo sinal em 30/30
  - valor-p 0,2450; BH 0,5513 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Ano do julgamento × incidência de Sociedade civil** — N: 19 audiências; 298 menções; 11 anos. ρ = +0,318. IC95% bootstrap de audiências [-0,231; +0,730] (n=19). valor-p 0,179; BH 0,551. *Executado (exploratório).*
  - Robustez: sem_AP33: +0,318 (p=0,184, 19 AP); sem_maior_audiência: +0,224 (p=0,387, 18 AP); retirar uma audiência: +0,210 a +0,424, mesmo sinal em 30/30
  - valor-p 0,1789; BH 0,5513 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Ano do julgamento × incidência de Acadêmicos** — N: 19 audiências; 298 menções; 11 anos. ρ = -0,153. IC95% bootstrap de audiências [-0,634; +0,328] (n=19). valor-p 0,533; BH 0,753. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,153 (p=0,511, 19 AP); sem_maior_audiência: -0,133 (p=0,586, 18 AP); retirar uma audiência: -0,258 a -0,008, mesmo sinal em 30/30
  - valor-p 0,5335; BH 0,7533 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Ano do julgamento × incidência de Partidos Políticos** — N: 0 menções com a categoria. n/d. n/d. sem valor-p. *Inviável: nenhuma menção vinculada com a categoria (A).*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. nenhuma menção vinculada com a categoria (A)
- **Ano do julgamento × incidência de Outros** — N: 19 audiências; 298 menções; 11 anos. ρ = -0,345. IC95% bootstrap de audiências [-0,647; +0,021] (n=19). valor-p 0,149; BH 0,551. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,345 (p=0,145, 19 AP); sem_maior_audiência: -0,324 (p=0,197, 18 AP); retirar uma audiência: -0,437 a -0,280, mesmo sinal em 30/30
  - valor-p 0,1495; BH 0,5513 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Ano do julgamento × taxa argumentativa das menções com Atores públicos (≥3 por audiência)** — N: 6 audiências; 64 menções; 5 anos. ρ = -0,394. IC não emitido (exige ≥10 audiências no total; n=6). valor-p 0,469; BH 0,753. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,394 (p=0,472, 6 AP); sem_maior_audiência: -0,287 (p=0,746, 5 AP); retirar uma audiência: -0,671 a +0,000, mesmo sinal em 29/30
  - valor-p 0,4692; BH 0,7533 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Ano do julgamento × taxa argumentativa das menções com Atores privados (≥3 por audiência)** — N: 2 audiências; 2 anos. descrição: ver T_H22_serie_categoria_ano.csv e T_H22_ap_taxa_argumento_por_categoria.csv. n/d. sem valor-p. *Inviável/descritivo: 2 audiências elegíveis e 2 anos (mínimo 5 e 4); série por ano em tabela.*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. 2 audiências elegíveis e 2 anos (mínimo 5 e 4); série por ano em tabela
- **Ano do julgamento × taxa argumentativa das menções com Sociedade civil (≥3 por audiência)** — N: 6 audiências; 128 menções; 5 anos. ρ = +0,154. IC não emitido (exige ≥10 audiências no total; n=6). valor-p 0,791; BH 0,791. *Executado (exploratório).*
  - Robustez: sem_AP33: +0,154 (p=0,797, 6 AP); sem_maior_audiência: -0,057 (p=0,893, 5 AP); retirar uma audiência: -0,057 a +0,894, mesmo sinal em 27/30
  - valor-p 0,7911; BH 0,7911 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Ano do julgamento × taxa argumentativa das menções com Acadêmicos (≥3 por audiência)** — N: 7 audiências; 91 menções; 6 anos. ρ = -0,542. IC não emitido (exige ≥10 audiências no total; n=7). valor-p 0,228; BH 0,551. *Executado (exploratório).*
  - Robustez: sem_AP33: -0,542 (p=0,211, 7 AP); sem_maior_audiência: -0,353 (p=0,494, 6 AP); retirar uma audiência: -0,924 a -0,353, mesmo sinal em 30/30
  - valor-p 0,2284; BH 0,5513 ≥ 0,05: sem evidência suficiente de associação; isso não prova ausência de efeito. Associação observacional, não causal, sem representatividade populacional.
- **Ano do julgamento × taxa argumentativa das menções com Partidos Políticos (≥3 por audiência)** — N: 0 menções com a categoria. n/d. n/d. sem valor-p. *Inviável: nenhuma menção vinculada com a categoria (A).*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. nenhuma menção vinculada com a categoria (A)
- **Ano do julgamento × taxa argumentativa das menções com Outros (≥3 por audiência)** — N: 2 audiências; 2 anos. descrição: ver T_H22_serie_categoria_ano.csv e T_H22_ap_taxa_argumento_por_categoria.csv. n/d. sem valor-p. *Inviável/descritivo: 2 audiências elegíveis e 2 anos (mínimo 5 e 4); série por ano em tabela.*
  - Teste não realizado por suporte insuficiente; nenhum valor-p calculado. 2 audiências elegíveis e 2 anos (mínimo 5 e 4); série por ano em tabela

  Limitações: Nível A (pessoa nomeada por audiência e nome); poucas audiências elegíveis e poucos anos; tema confundido com calendário; incidência sobreposta; observacional. | Nível A (pessoa nomeada por audiência e nome); poucas audiências elegíveis e poucos anos; tema confundido com calendário; incidência sobreposta; observacional. Aproveitamento argumentativo por categoria.

## 7. Sensibilidade A+B (H19–H22) — separada da análise principal

Mesmos métodos e suportes da análise principal, aplicados à classificação ampliada por entidade (proxy). Comparação com A:

| Hipótese | Teste | A (principal) | A+B (sensibilidade) |
|---|---|---|---|
| H19 | Categoria Atores públicos: presente − ausente (taxa argumentativa) | sem teste (Inviável) | +0,038 (p 0,594; q 0,594) |
| H19 | Categoria Atores públicos: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2… | +0,049 (p 0,938; q 0,938) | +0,000 (p 0,994; q 1,000) |
| H19 | Categoria Atores privados: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2… | sem teste (Inviável) | -0,003 (p 1,000; q 1,000) |
| H19 | Categoria Sociedade civil: presente − ausente (taxa argumentativa) | sem teste (Inviável) | -0,074 (p 0,270; q 0,594) |
| H19 | Categoria Sociedade civil: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2… | -0,104 (p 0,625; q 0,938) | -0,061 (p 0,270; q 1,000) |
| H19 | Categoria Acadêmicos: presente − ausente (taxa argumentativa) | sem teste (Inviável) | -0,077 (p 0,562; q 0,594) |
| H19 | Categoria Acadêmicos: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2 por … | sem teste (Inviável) | -0,014 (p 0,906; q 1,000) |
| H20 | Incidência de Atores públicos: ambiental − personalidade | -0,082 (p 0,574; q 0,865) | -0,008 (p 0,961; q 0,961) |
| H20 | Incidência de Atores privados: ambiental − personalidade | +0,110 (p 0,381; q 0,865) | +0,038 (p 0,485; q 0,961) |
| H20 | Incidência de Sociedade civil: ambiental − personalidade | -0,032 (p 0,849; q 0,865) | -0,018 (p 0,888; q 0,961) |
| H20 | Incidência de Acadêmicos: ambiental − personalidade | -0,152 (p 0,360; q 0,865) | -0,149 (p 0,269; q 0,961) |
| H20 | Incidência de Outros: ambiental − personalidade | -0,006 (p 0,865; q 0,865) | -0,009 (p 0,580; q 0,961) |
| H22 | Ano do julgamento × taxa argumentativa entre classificadas | -0,132 (p 0,586; q 0,753) | -0,091 (p 0,660; q 0,747) |
| H22 | Ano do julgamento × incidência de Atores públicos | -0,101 (p 0,678; q 0,763) | +0,221 (p 0,298; q 0,537) |
| H22 | Ano do julgamento × incidência de Atores privados | -0,281 (p 0,245; q 0,551) | -0,227 (p 0,283; q 0,537) |
| H22 | Ano do julgamento × incidência de Sociedade civil | +0,318 (p 0,179; q 0,551) | +0,141 (p 0,507; q 0,747) |
| H22 | Ano do julgamento × incidência de Acadêmicos | -0,153 (p 0,533; q 0,753) | -0,430 (p 0,036; q 0,329) |
| H22 | Ano do julgamento × incidência de Outros | -0,345 (p 0,149; q 0,551) | -0,316 (p 0,138; q 0,413) |
| H22 | Ano do julgamento × taxa argumentativa das menções com Atores públicos (≥3 por audiência) | -0,394 (p 0,469; q 0,753) | -0,091 (p 0,747; q 0,747) |
| H22 | Ano do julgamento × taxa argumentativa das menções com Sociedade civil (≥3 por audiência) | +0,154 (p 0,791; q 0,791) | +0,116 (p 0,729; q 0,747) |
| H22 | Ano do julgamento × taxa argumentativa das menções com Acadêmicos (≥3 por audiência) | -0,542 (p 0,228; q 0,551) | -0,610 (p 0,091; q 0,410) |

**H19 (A+B):** Categoria Atores públicos: presente − ausente (taxa argumentativa) → contraste médio por audiência = +0,038 (+3,8 p.p.); valor-p 0,594; BH 0,594 | Categoria Atores públicos: presente − ausente [sensibilidade exploratória de el… → contraste médio por audiência = +0,000 (+0,0 p.p.); valor-p 0,994; BH 1,000 | Categoria Atores privados: presente − ausente (taxa argumentativa) → contraste médio descritivo = +0,025 (4 audiências); Inviável | Categoria Atores privados: presente − ausente [sensibilidade exploratória de el… → contraste médio por audiência = -0,003 (-0,3 p.p.); valor-p 1,000; BH 1,000 | Categoria Sociedade civil: presente − ausente (taxa argumentativa) → contraste médio por audiência = -0,074 (-7,4 p.p.); valor-p 0,270; BH 0,594 | Categoria Sociedade civil: presente − ausente [sensibilidade exploratória de el… → contraste médio por audiência = -0,061 (-6,1 p.p.); valor-p 0,270; BH 1,000 | Categoria Acadêmicos: presente − ausente (taxa argumentativa) → contraste médio por audiência = -0,077 (-7,7 p.p.); valor-p 0,562; BH 0,594 | Categoria Acadêmicos: presente − ausente [sensibilidade exploratória de elegibi… → contraste médio por audiência = -0,014 (-1,4 p.p.); valor-p 0,906; BH 1,000 | Categoria Partidos Políticos: presente − ausente → n/d; Inviável | Categoria Outros: presente − ausente (taxa argumentativa) → contraste médio descritivo = -0,250 (2 audiências); Inviável | Categoria Outros: presente − ausente [sensibilidade exploratória de elegibilida… → contraste médio descritivo = -0,308 (3 audiências); Inviável

**H20 (A+B):** Incidência de Atores públicos: ambiental − personalidade → Δ incidência = -0,008; valor-p 0,961; BH 0,961 | Incidência de Atores privados: ambiental − personalidade → Δ incidência = +0,038; valor-p 0,485; BH 0,961 | Incidência de Sociedade civil: ambiental − personalidade → Δ incidência = -0,018; valor-p 0,888; BH 0,961 | Incidência de Acadêmicos: ambiental − personalidade → Δ incidência = -0,149; valor-p 0,269; BH 0,961 | Incidência de Partidos Políticos: ambiental − personalidade → n/d; Inviável | Incidência de Outros: ambiental − personalidade → Δ incidência = -0,009; valor-p 0,580; BH 0,961

**H21 (A+B):** Ministro × Atores públicos: aproveitamento argumentativo (n Argumento / n mençõ… → agregado por menção: 101/263 = 0,384; entre ministros com ≥5 menções: taxas 0,00–0,88; Descritivo (sem valor-p; não é preferência individual) | Ministro × Atores privados: aproveitamento argumentativo (n Argumento / n mençõ… → agregado por menção: 4/21 = 0,190; entre ministros com ≥5 menções: taxas 0,00–0,50; Descritivo (sem valor-p; não é preferência individual) | Ministro × Sociedade civil: aproveitamento argumentativo (n Argumento / n mençõ… → agregado por menção: 56/250 = 0,224; entre ministros com ≥5 menções: taxas 0,00–0,50; Descritivo (sem valor-p; não é preferência individual) | Ministro × Acadêmicos: aproveitamento argumentativo (n Argumento / n menções co… → agregado por menção: 59/114 = 0,518; entre ministros com ≥5 menções: taxas 0,00–1,00; Descritivo (sem valor-p; não é preferência individual) | Ministro × Partidos Políticos: aproveitamento argumentativo (n Argumento / n me… → agregado por menção: 0/0; nenhum ministro com ≥5 menções; Inviável | Ministro × Outros: aproveitamento argumentativo (n Argumento / n menções com a … → agregado por menção: 1/10 = 0,100; entre ministros com ≥5 menções: taxas 0,00–0,00; Descritivo (sem valor-p; não é preferência individual) | Modelo ministro × categoria no aproveitamento argumentativo (viabilidade) → modelo não estimado; Descritivo

**H22 (A+B):** Ano do julgamento × taxa argumentativa entre classificadas → ρ = -0,091; valor-p 0,660; BH 0,747 | Ano do julgamento × incidência de Atores públicos → ρ = +0,221; valor-p 0,298; BH 0,537 | Ano do julgamento × incidência de Atores privados → ρ = -0,227; valor-p 0,283; BH 0,537 | Ano do julgamento × incidência de Sociedade civil → ρ = +0,141; valor-p 0,507; BH 0,747 | Ano do julgamento × incidência de Acadêmicos → ρ = -0,430; valor-p 0,036; BH 0,329 | Ano do julgamento × incidência de Partidos Políticos → n/d; Inviável | Ano do julgamento × incidência de Outros → ρ = -0,316; valor-p 0,138; BH 0,413 | Ano do julgamento × taxa argumentativa das menções com Atores públicos (≥3 por … → ρ = -0,091; valor-p 0,747; BH 0,747 | Ano do julgamento × taxa argumentativa das menções com Atores privados (≥3 por … → descrição: ver T_H22_serie_categoria_ano.csv e T_H22_ap_taxa_argumento_por_categoria.csv; Inviável/descritivo | Ano do julgamento × taxa argumentativa das menções com Sociedade civil (≥3 por … → ρ = +0,116; valor-p 0,729; BH 0,747 | Ano do julgamento × taxa argumentativa das menções com Acadêmicos (≥3 por audiê… → ρ = -0,610; valor-p 0,091; BH 0,410 | Ano do julgamento × taxa argumentativa das menções com Partidos Políticos (≥3 p… → n/d; Inviável | Ano do julgamento × taxa argumentativa das menções com Outros (≥3 por audiência) → descrição: ver T_H22_serie_categoria_ano.csv e T_H22_ap_taxa_argumento_por_categoria.csv; Inviável/descritivo

## 8. Figuras

Cada figura declara unidade e denominador e aponta seus dados (CSV). PNG 300 dpi e SVG em `results/figures/`; nenhuma figura codifica significância.

| Figura | Hipóteses | Unidade | Denominador | Dados |
|---|---|---|---|---|
| fig01_taxa_por_ano_julgamento.png | H1, H13 | audiência | 30 audiências; 1288 menções | results/figures/dados/fig01_taxa_por_ano_julgamento.csv |
| fig02_intervalo_taxa.png | H2, H16 | audiência | 29 audiências no estimando | results/figures/dados/fig02_intervalo_taxa.csv |
| fig03_eixos_e_heterogeneidade.png | H5, H6 | audiência | 30 audiências | results/figures/dados/fig03_eixos_e_heterogeneidade.csv |
| fig04_contrastes.png | H4, H8, H11, H12, H15, H17, H20 | audiência | ver N na matriz (coluna N) | results/figures/dados/fig04_contrastes.csv |
| fig05_h10_concentracao.png | H10 | audiência, documento, ministro | 1288 menções; 501 argumentos | results/figures/dados/fig05_h10_concentracao.csv |
| fig06_h3_taxa_por_ministro.png | H3 | ministro | 12 ministros; 1161 menções | results/figures/dados/fig06_h3_taxa_por_ministro.csv |
| fig07_h8_local.png | H8 | menção (descrição) e audiência | 1288 menções; audiências com ≥3 menções por local no painel direito | results/figures/dados/fig07_h8_local.csv |
| fig08_h15_local_por_eixo.png | H15 | audiência | 29 audiências | results/figures/dados/fig08_h15_local_por_eixo.csv |
| fig09_h17_alvo_por_local.png | H17 | menção (descrição) | 1288 menções | results/figures/dados/fig09_h17_alvo_por_local.csv |
| fig10_h18_pca_composicao.png | H18 | audiência | 30 audiências | results/figures/dados/fig10_h18_pca_composicao.csv |
| fig11_estados_A_vs_AB.png | H19–H22 | menção (contagem) | 1288 menções incorporadas | results/figures/dados/fig11_estados_A_vs_AB.csv |
| fig12_h19_taxas_por_categoria.png | H19 | menção (descrição) | 307 classificadas em A; 616 em A+B | results/figures/dados/fig12_h19_taxas_por_categoria.csv |
| fig13_h20_incidencia_por_eixo.png | H20 | menção (descrição agregada por menção) | 307 menções classificadas | results/figures/dados/fig13_h20_incidencia_por_eixo.csv |
| fig14_h21_ministro_x_categoria.png | H21 | ministro × categoria | 304 menções classificadas nos 15 ministros mais frequentes | results/figures/dados/fig14_h21_ministro_x_categoria.csv |
| fig15_h22_composicao_e_aproveitamento.png | H22 | menção classificada por ano (descrição); audiência (teste) | 307 menções classificadas | results/figures/dados/fig15_h22_composicao_e_aproveitamento.csv |
| fig16_h9_classe.png | H9 | audiência | 28 audiências de classe única | results/figures/dados/fig16_h9_classe.csv |

![H1, H13 — fig01_taxa_por_ano_julgamento.png (unidade: audiência; denominador: 30 audiências; 1288 menções)](../results/figures/fig01_taxa_por_ano_julgamento.png)

![H2, H16 — fig02_intervalo_taxa.png (unidade: audiência; denominador: 29 audiências no estimando)](../results/figures/fig02_intervalo_taxa.png)

![H5, H6 — fig03_eixos_e_heterogeneidade.png (unidade: audiência; denominador: 30 audiências)](../results/figures/fig03_eixos_e_heterogeneidade.png)

![H4, H8, H11, H12, H15, H17, H20 — fig04_contrastes.png (unidade: audiência; denominador: ver N na matriz (coluna N))](../results/figures/fig04_contrastes.png)

![H10 — fig05_h10_concentracao.png (unidade: audiência, documento, ministro; denominador: 1288 menções; 501 argumentos)](../results/figures/fig05_h10_concentracao.png)

![H3 — fig06_h3_taxa_por_ministro.png (unidade: ministro; denominador: 12 ministros; 1161 menções)](../results/figures/fig06_h3_taxa_por_ministro.png)

![H8 — fig07_h8_local.png (unidade: menção (descrição) e audiência; denominador: 1288 menções; audiências com ≥3 menções por local no painel direito)](../results/figures/fig07_h8_local.png)

![H15 — fig08_h15_local_por_eixo.png (unidade: audiência; denominador: 29 audiências)](../results/figures/fig08_h15_local_por_eixo.png)

![H17 — fig09_h17_alvo_por_local.png (unidade: menção (descrição); denominador: 1288 menções)](../results/figures/fig09_h17_alvo_por_local.png)

![H18 — fig10_h18_pca_composicao.png (unidade: audiência; denominador: 30 audiências)](../results/figures/fig10_h18_pca_composicao.png)

![H19–H22 — fig11_estados_A_vs_AB.png (unidade: menção (contagem); denominador: 1288 menções incorporadas)](../results/figures/fig11_estados_A_vs_AB.png)

![H19 — fig12_h19_taxas_por_categoria.png (unidade: menção (descrição); denominador: 307 classificadas em A; 616 em A+B)](../results/figures/fig12_h19_taxas_por_categoria.png)

![H20 — fig13_h20_incidencia_por_eixo.png (unidade: menção (descrição agregada por menção); denominador: 307 menções classificadas)](../results/figures/fig13_h20_incidencia_por_eixo.png)

![H21 — fig14_h21_ministro_x_categoria.png (unidade: ministro × categoria; denominador: 304 menções classificadas nos 15 ministros mais frequentes)](../results/figures/fig14_h21_ministro_x_categoria.png)

![H22 — fig15_h22_composicao_e_aproveitamento.png (unidade: menção classificada por ano (descrição); audiência (teste); denominador: 307 menções classificadas)](../results/figures/fig15_h22_composicao_e_aproveitamento.png)

![H9 — fig16_h9_classe.png (unidade: audiência; denominador: 28 audiências de classe única)](../results/figures/fig16_h9_classe.png)

## 9. Sensibilidades predefinidas

Retirar uma audiência por vez e a maior audiência; sem Relatório; sem AP33; sem atribuição de ministro por metadado (autoria plena); apenas local Voto (H4); peso por menção versus por audiência; valor cadastrado da AP33 mantido em H2; sensibilidade de elegibilidade (≥2 por grupo) em H19; nível A+B (§7). As estimativas estão na coluna Robustez da matriz.
Frases repetidas entre processos (144 grupos, 417 ocorrências no diagnóstico anterior) **não** foram colapsadas: não há regra autorizada; as contagens preservam todas as ocorrências.

## 10. Conclusão

**Panorama.** No cenário A houve 40 testes com valor-p, dos quais 35 do escopo previsto principal e 5 de análises adicionais/sensibilidade de elegibilidade; 4 com BH < 0,05 e 36 inconclusivos. Resultados não significativos, inviáveis e descritivos são resultados científicos: indicam que, com 30 audiências, a maioria das associações investigadas não é distinguível do acaso ou não tem suporte para teste. A ausência de significância não prova ausência de efeito.

**Testes com BH abaixo do limiar (leitura exploratória):**

- H4, Relator cadastrado − demais julgadores (fora do Relatório; associação documental exploratória): contraste médio por audiência = +0,236 (+23,6 p.p.); IC95% bootstrap de audiências [+0,113; +0,355] (n=24); valor-p 0,002, BH 0,002. **Confundido com o local do acórdão; não atribui efeito à função de relator.**
- H8, Taxa argumentativa: Voto do Relator − Relatório: contraste médio por audiência = +0,540 (+54,0 p.p.); IC95% bootstrap de audiências [+0,403; +0,664] (n=16); valor-p <0,001, BH <0,001.
- H8, Taxa argumentativa: Voto − Relatório: contraste médio por audiência = +0,317 (+31,7 p.p.); IC95% bootstrap de audiências [+0,201; +0,432] (n=17); valor-p <0,001, BH <0,001.
- H8, Taxa argumentativa: Voto − Voto do Relator: contraste médio por audiência = -0,201 (-20,1 p.p.); IC95% bootstrap de audiências [-0,338; -0,067] (n=20); valor-p 0,010, BH 0,024.

São contrastes por audiência sob hipótese de simetria; descrevem as audiências observadas, não causam nem generalizam.

**Medidas de associação, intervalos e p/q de todos os testes executados (cenário A; coluna Escopo distingue previstos de adicionais):**

| H | Escopo | Teste | Estimativa | Incerteza | p | q (BH) | Leitura |
|---|---|---|---|---|---|---|---|
| H1 | previsto principal | Ano do julgamento × taxa por audiência | ρ de Spearman = -0,170 | IC95% bootstrap de audiências [-0,555; +0,287] (n=30) | 0,370 | 0,888 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H1 | previsto principal | Ano da audiência × taxa por audiência (secundário) | ρ de Spearman = -0,073 | IC95% bootstrap de audiências [-0,436; +0,334] (n=30) | 0,710 | 0,888 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H2 | previsto principal | Intervalo em anos (julgamento − audiência) × taxa | ρ de Spearman = +0,017 | IC95% bootstrap de audiências [-0,390; +0,428] (n=29) | 0,934 | 0,934 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H4 | previsto principal | Relator cadastrado − demais julgadores (fora do Relatório; associação documental exp… | contraste médio por audiência = +0,236 (+23,6 p.p.) | IC95% bootstrap de audiências [+0,113; +0,355] (n=24) | 0,002 | 0,002 | compatível com associação exploratória |
| H5 | previsto principal | Eixo ambiental/mercado − personalidade (taxa por audiência) | Δ = +0,030 (+3,0 p.p.) | IC95% bootstrap de audiências [-0,111; +0,172] (n=18+12) | 0,712 | 0,712 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H8 | previsto principal | Taxa argumentativa: Voto do Relator − Relatório | contraste médio por audiência = +0,540 (+54,0 p.p.) | IC95% bootstrap de audiências [+0,403; +0,664] (n=16) | <0,001 | <0,001 | compatível com associação exploratória |
| H8 | previsto principal | Taxa argumentativa: Voto − Relatório | contraste médio por audiência = +0,317 (+31,7 p.p.) | IC95% bootstrap de audiências [+0,201; +0,432] (n=17) | <0,001 | <0,001 | compatível com associação exploratória |
| H8 | previsto principal | Taxa argumentativa: Voto − Voto do Relator | contraste médio por audiência = -0,201 (-20,1 p.p.) | IC95% bootstrap de audiências [-0,338; -0,067] (n=20) | 0,010 | 0,024 | compatível com associação exploratória |
| H9 | previsto principal | Classe processual (ADI, ADPF, RE) | H = 2,941; médias das taxas por audiência: ADI 0,40 (n=14); ADPF 0,28 (n=4); RE 0,26 (n=7) | IC não emitido | 0,233 | 0,326 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H11 | previsto principal | Taxa argumentativa: Pessoa − Sem pessoa/instituição nos campos | contraste médio por audiência = +0,057 (+5,7 p.p.) | IC não emitido (exige ≥10 audiências no total; n=8) | 0,633 | 0,633 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H11 | previsto principal | Taxa argumentativa: Instituição − Sem pessoa/instituição nos campos | contraste médio por audiência = -0,037 (-3,7 p.p.) | IC95% bootstrap de audiências [-0,165; +0,102] (n=16) | 0,609 | 0,633 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H11 | previsto principal | Taxa argumentativa: Pessoa e instituição − Sem pessoa/instituição nos campos | contraste médio por audiência = -0,151 (-15,1 p.p.) | IC95% bootstrap de audiências [-0,286; -0,014] (n=14) | 0,057 | 0,226 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H12 | previsto principal | Individualizada (pessoa ou instituição nos campos) − sem nome | contraste médio por audiência = -0,052 (-5,2 p.p.) | IC95% bootstrap de audiências [-0,161; +0,061] (n=23) | 0,389 | 0,633 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H13 | previsto principal | Ano do julgamento × eixo | interação (inclinação ambiental − personalidade) = +0,0107 por unidade de x; inclinação personalida… | EP HC3 0,0199; IC95% HC3 [-0,0301; +0,0515]; IC95% bootstrap de audiências [-0,0305; +0,0… | 0,595 | 0,888 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H15 | previsto principal | Prevalência de menções em "Relatório": ambiental/mercado − personalidade | Δ da fração em "Relatório" = -0,038 (-3,8 p.p.) | IC95% bootstrap de audiências [-0,194; +0,107] (n=17+12) | 0,618 | 0,712 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H15 | previsto principal | Prevalência de menções em "Voto do Relator": ambiental/mercado − personalidade | Δ da fração em "Voto do Relator" = +0,112 (+11,2 p.p.) | IC95% bootstrap de audiências [-0,058; +0,275] (n=17+12) | 0,188 | 0,712 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H15 | previsto principal | Prevalência de menções em "Voto": ambiental/mercado − personalidade | Δ da fração em "Voto" = -0,073 (-7,3 p.p.) | IC95% bootstrap de audiências [-0,227; +0,084] (n=17+12) | 0,369 | 0,712 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H15 | adicional local×eixo | [análise adicional] Contraste de Argumento Voto do Relator − Relatório: diferença en… | Δ de contrastes = +0,066 | IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=10+6) | 0,659 | 0,856 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H15 | adicional local×eixo | [análise adicional] Contraste de Argumento Voto − Relatório: diferença entre eixos | Δ de contrastes = -0,024 | IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=10+7) | 0,850 | 0,856 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H15 | adicional local×eixo | [análise adicional] Contraste de Argumento Voto − Voto do Relator: diferença entre e… | Δ de contrastes = -0,029 | IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=12+8) | 0,856 | 0,856 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H16 | previsto principal | Intervalo × eixo | interação (inclinação ambiental − personalidade) = +0,0614 por unidade de x; inclinação personalida… | EP HC3 0,0600; IC95% HC3 [-0,0622; +0,1851]; IC95% bootstrap de audiências [-0,0296; +0,2… | 0,316 | 0,888 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H17 | previsto principal | Proporção individualizada (alvo com nome): Voto do Relator − Relatório | contraste médio por audiência = -0,031 (-3,1 p.p.) | IC95% bootstrap de audiências [-0,248; +0,162] (n=16) | 0,775 | 0,775 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H17 | previsto principal | Proporção individualizada (alvo com nome): Voto − Relatório | contraste médio por audiência = -0,070 (-7,0 p.p.) | IC95% bootstrap de audiências [-0,263; +0,135] (n=17) | 0,515 | 0,600 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H17 | previsto principal | Proporção individualizada (alvo com nome): Voto − Voto do Relator | contraste médio por audiência = -0,087 (-8,7 p.p.) | IC95% bootstrap de audiências [-0,202; +0,046] (n=20) | 0,207 | 0,326 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H19 | sensibilidade de elegibilidade | Categoria Atores públicos: presente − ausente [sensibilidade exploratória de elegibi… | contraste médio por audiência = +0,049 (+4,9 p.p.) | IC não emitido (exige ≥10 audiências no total; n=9) | 0,938 | 0,938 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H19 | sensibilidade de elegibilidade | Categoria Sociedade civil: presente − ausente [sensibilidade exploratória de elegibi… | contraste médio por audiência = -0,104 (-10,4 p.p.) | IC não emitido (exige ≥10 audiências no total; n=8) | 0,625 | 0,938 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H20 | previsto principal | Incidência de Atores públicos: ambiental − personalidade | Δ incidência = -0,082 | IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=9+10) | 0,574 | 0,865 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H20 | previsto principal | Incidência de Atores privados: ambiental − personalidade | Δ incidência = +0,110 | IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=9+10) | 0,381 | 0,865 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H20 | previsto principal | Incidência de Sociedade civil: ambiental − personalidade | Δ incidência = -0,032 | IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=9+10) | 0,849 | 0,865 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H20 | previsto principal | Incidência de Acadêmicos: ambiental − personalidade | Δ incidência = -0,152 | IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=9+10) | 0,360 | 0,865 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H20 | previsto principal | Incidência de Outros: ambiental − personalidade | Δ incidência = -0,006 | IC não emitido (comparação entre eixos exige ≥10 audiências em cada eixo; n=9+10) | 0,865 | 0,865 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H22 | previsto principal | Ano do julgamento × taxa argumentativa entre classificadas | ρ = -0,132 | IC95% bootstrap de audiências [-0,534; +0,319] (n=19) | 0,586 | 0,753 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H22 | previsto principal | Ano do julgamento × incidência de Atores públicos | ρ = -0,101 | IC95% bootstrap de audiências [-0,544; +0,385] (n=19) | 0,678 | 0,763 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H22 | previsto principal | Ano do julgamento × incidência de Atores privados | ρ = -0,281 | IC95% bootstrap de audiências [-0,617; +0,100] (n=19) | 0,245 | 0,551 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H22 | previsto principal | Ano do julgamento × incidência de Sociedade civil | ρ = +0,318 | IC95% bootstrap de audiências [-0,231; +0,730] (n=19) | 0,179 | 0,551 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H22 | previsto principal | Ano do julgamento × incidência de Acadêmicos | ρ = -0,153 | IC95% bootstrap de audiências [-0,634; +0,328] (n=19) | 0,533 | 0,753 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H22 | previsto principal | Ano do julgamento × incidência de Outros | ρ = -0,345 | IC95% bootstrap de audiências [-0,647; +0,021] (n=19) | 0,149 | 0,551 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H22 | previsto principal | Ano do julgamento × taxa argumentativa das menções com Atores públicos (≥3 por audiê… | ρ = -0,394 | IC não emitido (exige ≥10 audiências no total; n=6) | 0,469 | 0,753 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H22 | previsto principal | Ano do julgamento × taxa argumentativa das menções com Sociedade civil (≥3 por audiê… | ρ = +0,154 | IC não emitido (exige ≥10 audiências no total; n=6) | 0,791 | 0,791 | inconclusivo (sem evidência suficiente; não prova ausência) |
| H22 | previsto principal | Ano do julgamento × taxa argumentativa das menções com Acadêmicos (≥3 por audiência) | ρ = -0,542 | IC não emitido (exige ≥10 audiências no total; n=7) | 0,228 | 0,551 | inconclusivo (sem evidência suficiente; não prova ausência) |

**Descritivos (sem valor-p):**

- H3, Heterogeneidade observada entre ministros (descrição com denominadores): 12 ministros com suporte; taxa observada por ministro: mín 0,077, quartis 0,305/0,338/0,406, máx 1,000; 32 documentos com ≥2 ministros (≥2 menções cada), amplitude mediana de taxas dentro do documento 0,500.
- H6, Heterogeneidade observada entre audiências — Ambiental/políticas/mercado: taxas por audiência: mín 0,00, quartis 0,20/0,39/0,59, máx 0,70; desvio-padrão 0,231; menores: AP28 0,00 (n=2), AP41 0,06 (n=34), AP38 0,14 (n=84); maiores: AP18 0,70 (n=10), AP8 0,70 (n=70), AP33 0,67 (n=3).
- H6, Heterogeneidade observada entre audiências — Personalidade: taxas por audiência: mín 0,17, quartis 0,21/0,28/0,47, máx 0,71; desvio-padrão 0,177; menores: AP13 0,17 (n=29), AP5 0,19 (n=27), AP11 0,21 (n=14); maiores: AP4 0,71 (n=75), AP17 0,60 (n=15), AP1 0,49 (n=45).
- H7, Ministro × eixo: 8 ministros com ≥15 menções e ≥3 audiências em ambos os eixos.
- H8, Distribuição Contexto/Relato/Argumento por local (3 categorias, descritiva): Relatório: Contexto 50,8%, Relato 41,7%, Argumento 7,4% (n=242); Voto do Relator: Contexto 31,5%, Relato 19,2%, Argumento 49,2% (n=504); Voto: Contexto 41,9%, Relato 14,8%, Argumento 43,4% (n=542).
- H10, Concentração de argumentos por audiência (descritiva): Gini argumentos 0,578 vs menções 0,504; top-3 argumentos 39,5% vs menções 37,8%; n efetivo argumentos 16,7 vs menções 19,2.
- H10, Concentração de argumentos por documento (descritiva): Gini argumentos 0,450 vs menções 0,398; top-3 argumentos 25,9% vs menções 23,5%; n efetivo argumentos 30,5 vs menções 33,5.
- H10, Concentração de argumentos por ministro (autoria plena) (descritiva): Gini argumentos 0,595 vs menções 0,564; top-3 argumentos 54,3% vs menções 50,4%; n efetivo argumentos 10,6 vs menções 11,6.
- H11, Distribuição Contexto/Relato/Argumento por tipo de alvo derivado (3 categorias, descritiva): Instituição: C 34,7%, R 31,2%, A 34,1% (n=311); Pessoa: C 9,5%, R 40,0%, A 50,5% (n=95); Pessoa e instituição: C 30,7%, R 38,7%, A 30,7% (n=212); Sem pessoa/instituição nos campos: C 48,8%, R 9,1%, A 42,1% (n=670).
- H14, Ministro × ano: 8 ministros com cobertura de ≥3 anos.
- H17, Distribuição do tipo de alvo por local (4 categorias, descritiva): Relatório: Instituição 23,1%, Pessoa 7,9%, Pessoa e instituição 28,9%, Sem pessoa/instituição nos campos 40,1% (n=242); Voto do Relator: Instituição 26,0%, Pessoa 5,2%, Pessoa e instituição 16,3%, Sem pessoa/instituição nos campos 52,6% (n=504); Voto: Instituição 22,9%, Pessoa 9,2%, Pessoa e instituição 11,1%, Sem pessoa/instit….
- H18, Perfis de composição por audiência (PCA CLR; agrupamento hierárquico de Ward): PC1 explica 67,2% da variação da composição (3 partes têm só 2 dimensões); ARI mediana: k=2: 0,26; k=3: 0,37; k=4: 0,39.
- H21, Ministro × Atores públicos: aproveitamento argumentativo (n Argumento / n menções com a categoria): agregado por menção: 12/77 = 0,156; entre ministros com ≥5 menções: taxas 0,08–0,32.
- H21, Ministro × Atores privados: aproveitamento argumentativo (n Argumento / n menções com a categoria): agregado por menção: 4/10 = 0,400; nenhum ministro com ≥5 menções.
- H21, Ministro × Sociedade civil: aproveitamento argumentativo (n Argumento / n menções com a categoria): agregado por menção: 39/141 = 0,277; entre ministros com ≥5 menções: taxas 0,03–0,47.
- H21, Ministro × Acadêmicos: aproveitamento argumentativo (n Argumento / n menções com a categoria): agregado por menção: 59/102 = 0,578; entre ministros com ≥5 menções: taxas 0,43–1,00.
- H21, Ministro × Outros: aproveitamento argumentativo (n Argumento / n menções com a categoria): agregado por menção: 1/10 = 0,100; entre ministros com ≥5 menções: taxas 0,00–0,00.

**Inviáveis por suporte (não testados):**

- H4, Relator cadastrado − demais (apenas local = Voto, controla o local): Inviável: suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 0).
- H19, Categoria Atores públicos: presente − ausente (taxa argumentativa): Inviável: suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 4).
- H19, Categoria Atores privados: presente − ausente (taxa argumentativa): Inviável: suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 1).
- H19, Categoria Atores privados: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2 por …: Inviável: suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 1) [sensibilidade exploratória de elegibilidade].
- H19, Categoria Sociedade civil: presente − ausente (taxa argumentativa): Inviável: suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 4).
- H19, Categoria Acadêmicos: presente − ausente (taxa argumentativa): Inviável: suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 4).
- H19, Categoria Acadêmicos: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2 por grupo]: Inviável: suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 4) [sensibilidade exploratória de elegibilidade].
- H19, Categoria Partidos Políticos: presente − ausente: Inviável: nenhuma menção vinculada com a categoria (A).
- H19, Categoria Outros: presente − ausente (taxa argumentativa): Inviável: suporte insuficiente no critério predefinido (≥3 menções por grupo em ≥5 audiências; elegíveis: 2).
- H19, Categoria Outros: presente − ausente [sensibilidade exploratória de elegibilidade: ≥2 por grupo]: Inviável: suporte insuficiente no critério predefinido (≥2 menções por grupo em ≥5 audiências; elegíveis: 3) [sensibilidade exploratória de elegibilidade].
- H20, Incidência de Partidos Políticos: ambiental − personalidade: Inviável: audiências elegíveis por eixo 9/10 (mínimo 5) e 0 menções com a categoria.
- H21, Ministro × Partidos Políticos: aproveitamento argumentativo (n Argumento / n menções com a categori…: Inviável: nenhuma menção vinculada com a categoria (A).
- H21, Modelo ministro × categoria no aproveitamento argumentativo (viabilidade): Inviável: suporte insuficiente para interação ministro × categoria (critério: ≥4 ministros com ≥2 categorias com ≥5 menções; observado 3); atribuição por metadado e dependência dentro de documento/audiência impedem inferência individual.
- H22, Ano do julgamento × incidência de Partidos Políticos: Inviável: nenhuma menção vinculada com a categoria (A).
- H22, Ano do julgamento × taxa argumentativa das menções com Atores privados (≥3 por audiência): Inviável/descritivo: 2 audiências elegíveis e 2 anos (mínimo 5 e 4); série por ano em tabela.
- H22, Ano do julgamento × taxa argumentativa das menções com Partidos Políticos (≥3 por audiência): Inviável: nenhuma menção vinculada com a categoria (A).
- H22, Ano do julgamento × taxa argumentativa das menções com Outros (≥3 por audiência): Inviável/descritivo: 2 audiências elegíveis e 2 anos (mínimo 5 e 4); série por ano em tabela.

**H19 e o critério predefinido.** No escopo previsto principal (≥3 menções por grupo em ≥5 audiências) **nenhuma categoria teve teste viável**: 6 das 6 linhas previstas são inviáveis. Os 2 valores-p de H19 em A pertencem à sensibilidade de elegibilidade (≥2 por grupo; 5 linhas, uma por categoria): exploratória, não confirmatória e fora do escopo principal.

**Sensibilidade A+B.** No conjunto A+B (616 menções classificadas contra 307 em A), 21 linhas tiveram valor-p; 0 com BH < 0,05 nas suas famílias próprias. A análise principal e seu estimando permanecem os de A; compare as estimativas na tabela do §7 e trate a diferença entre A e A+B como medida de sensibilidade ao proxy institucional.

**Contribuições (sem apoio em referências bibliográficas, que não foram buscadas ou inventadas).**

- Descritiva: base estruturada de 1288 menções em 30 audiências, com três funções (Contexto, Relato, Argumento) e proxies de individualização de alvo; a taxa argumentativa é medida de composição das menções observadas, não de aproveitamento de contribuições.
- Estrutura do acórdão: 3 de 3 contrastes de taxa de Argumento entre locais tiveram BH < 0,05; as estimativas e ICs estão na tabela acima. A composição por local (3 categorias) é apresentada em H8 sem teste de associação com menções como réplicas. Cautela: o local é um dos indícios da própria classificação do tipo (METODOLOGIA, §14.2), logo o padrão não é validação independente da tipologia (ver nota em H8 e §11).
- Metodológica: separar unidade de contagem (menção) de unidade inferencial (audiência); declarar a hipótese de simetria do teste de inversão de sinais; marcar suporte insuficiente em vez de reduzir limiares; manter heterogeneidade e concentração como descrição quando a inferência exigiria independência entre menções.
- Agenda: construir denominador de votos/manifestações elegíveis; validar amostra humana dos rótulos para estimar erro de classificação; ampliar a cobertura de classificação dos atores; revisar a cronologia cadastral da AP33.

## 11. Limitações gerais

- **Nota metodológica sobre H8 (dependência conceitual).** A metodologia de classificação adotada (documento raiz METODOLOGIA_ANALISE_MENCOES_AUDIENCIAS.md, seção 14.2) afirma: "Estar no voto, fora do relatório ou próximo de uma conclusão é indício, mas não condição suficiente." Assim, a localização/contexto argumentativo foi um dos indícios usados para decidir o tipo (Contexto, Relato ou Argumento). A associação H8 entre local e tipo não é, portanto, validação independente da tipologia, e parte do padrão pode refletir a própria operacionalização. Isso não configura tautologia estrita (há Argumentos no Relatório) e não descarta os contrastes estatísticos: indica apenas risco de dependência conceitual/incorporação do contexto e exige cautela interpretativa. Nada disso permite inferir eficácia democrática, mudança de voto ou impacto causal. A nota é relevante porque H8 concentra os achados com BH < 0,05.

- Levantamento condicionado à extração e aos critérios de inclusão; não é censo de menções nem de audiências; a ausência de candidatos (AP44) não significa ausência de referências.
- 291 menções têm ministro atribuído por metadado (relator) e 17 têm autoria não plena: o nome do ministro não prova que proferiu a passagem; o Relatório é parte estrutural do documento, não voto pessoal; H21 não indica preferência individual.
- H4: o relator aparece quase só em "Voto do Relator"; a comparação mistura relator e local e a comparação restrita ao local Voto não tem audiências elegíveis; não se atribui efeito à função de relator.
- AP33: intervalo cadastrado −1 preservado como dado original, fora de H2/H16.
- Individualização (H11/H12/H17) é proxy do preenchimento de campos; não indica ação, influência nem contribuição específica.
- Incidências por categoria são prevalências sobrepostas (multirrótulo); nunca somar como partição. Partido Político: atores na lista, mas nenhuma menção vinculada em A nem em A+B; sem estimativa.
- Categoria institucional (A+B) é proxy da participação de pessoas afiliadas à entidade; só sensibilidade.
- Poucas audiências por teste (frequentemente 5–20 elegíveis): baixa potência; testes de inversão de sinais dependem da hipótese de simetria; processos conexos compartilham texto.
- A incerteza da classificação por IA e da extração não é propagada; não há universo de participantes nem de votos.

## 12. Reprodução

```
.venv/bin/python run_all.py
```

Python local em `.venv`; versões em `requirements.lock`; SHA-256 de entradas (antes e depois), scripts, configuração (inclusive decisão sobre B), seeds por análise e saídas em `results/manifesto_execucao.json`. Modo desta execução: **final**.

## 13. Arquivos

- `data/processed/`: `mencoes_principal_atores.csv` (1 linha por menção, nível A), `mencoes_sensibilidade_AB.csv`, `atores_classificados.csv`, `ponte_mencao_ator.csv`, `ponte_B_candidatos_proveniencia.csv`, `entidades_B.csv`, `diagnostico_B_por_mencao.csv`.
- `results/h1_h22/`: matriz CSV/JSON (principal e A+B), resumo, tabelas `T_*.csv`, `validacao_integracao.json`, `numeros_relatorio.json`.
- `results/figures/`: PNG/SVG, `dados/` e `figuras_indice.csv`.
