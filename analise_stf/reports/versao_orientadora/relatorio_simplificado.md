# Audiências públicas e acórdãos do STF — versão simplificada

*Apoio para conversa com a orientadora. Números de resultados já calculados; nada recalculado. Relatório técnico completo: [relatorio_consolidado_H1_H22.html](../relatorio_consolidado_H1_H22.html). AP = audiência pública; pp = pontos percentuais.*

<div class="destaque" markdown="1">

## Principais conclusões

1. **O que há:** 1288 menções a audiências públicas em 46 documentos, ligadas a 30 audiências. Cerca de 39 em cada 100 são *Argumento* (501 de 1288); não equivale a 39% das contribuições aproveitadas.
2. **Achado mais claro: o lugar no acórdão.** Argumento é raro no Relatório (7,4%) e comum no Voto do Relator (49,2%) e nos demais votos (43,4%). Média por AP: +54,0 pp (Voto do Relator − Relatório; 16 AP; faixa +40,3 a +66,4) e +31,7 pp (Voto − Relatório; 17 AP; faixa +20,1 a +43,2).
3. **Relator:** +23,6 pp (24 AP), mas **misturado com o lugar**; não se conclui efeito da função de relator.
4. **Não identificamos diferença consistente** para ano, intervalo, eixo, classe e presença de nome. Com poucas audiências, isso **não prova ausência**.
5. **Atores:** só 307 menções têm categoria de ator por vínculo direto; a comparação principal é inviável nas 6 categorias.
6. **Cuidado:** é um levantamento, não um censo; taxa por categoria não mede representatividade, favorecimento ou exclusão.

</div>

## 1. O que estudamos e o que temos

Cada ocorrência selecionada para o corpus, extraída dos acórdãos e referente à audiência ou aos seus participantes, é uma *menção* (uma linha por ocorrência), classificada em um de três tipos excludentes: **Contexto** (refere-se à existência, organização ou participação na audiência, sem uso substantivo), **Relato** (sintetiza o que foi dito, sem mobilizar na argumentação) ou **Argumento** (mobiliza a contribuição no raciocínio, inclusive para discutir ou discordar dela). São 509 Contexto, 278 Relato e 501 Argumento, total 1288.

A **taxa de Argumento** é 501/1288 = 38,9%: cerca de 39 em cada 100 menções válidas. O denominador são as menções encontradas, não tudo o que foi dito.

![O que as menções fazem, no total e em cada parte do acórdão?](graficos/fig1_tipo_por_local.svg)

**Figura 1 — O que as menções fazem, no total e em cada parte do acórdão?** *Compara:* os três tipos no total e em cada lugar (Relatório, Voto do Relator, Voto). *Como ler:* cada barra soma 100%; mais verde, mais Argumento. *Resultado:* Argumento: 7,4% no Relatório, 49,2% no Voto do Relator, 43,4% nos demais votos. *Base:* 1288 menções (contagem direta).

## 2. Como fizemos e por quê

- **Menções do mesmo acórdão não são independentes** (mesmo texto, processo e julgadores). Tratá-las como 1288 casos daria falsa precisão; por isso comparamos **audiências inteiras** (até 30).
- **Comparação dentro de cada audiência:** por exemplo, a taxa de Argumento do Voto menos a do Relatório, e depois a média entre audiências.
- **Faixa de incerteza (intervalo de confiança de 95%):** quanto a média variaria se as audiências observadas fossem reamostradas. Mede a incerteza do método, **não** o erro da classificação por IA.
- **Simulações** (embaralhamentos; retirar uma audiência por vez) verificam a estabilidade dos resultados.
- **Correção para várias comparações:** com muitos testes, coincidências aparecem. Só destacamos como evidência estatística o que resiste à correção; diferença observada é outra coisa.
- **Regressão:** só para comparar tendências entre eixos; não prova causa.
- Sem base suficiente, o teste **não é feito**. “Sem diferença detectada” não é “não há diferença”.

## 3. Resultados por tema

### 3.1 Lugar no acórdão (H8, H15, H17)

- **Pergunta.** O tipo de menção varia conforme a parte do acórdão?
- **Variáveis.** *Local* (Relatório, Voto do Relator, Voto) e *tipo de menção*.
- **O que fizemos e por quê.** Em cada audiência com menções nos dois lugares, subtraímos as taxas de Argumento e tiramos a média (H8). H15 examina a composição das menções entre as partes do acórdão por eixo (a interação da taxa foi análise adicional); H17, a associação entre parte do acórdão e presença de pessoa/instituição nomeada: ambas sem diferença detectada.
- **Ressalva.** O lugar foi um dos indícios usados para classificar o tipo (metodologia, §14.2). A associação não valida a classificação de modo independente; não é tautologia estrita (há 18 Argumentos no Relatório).

![Quanto a taxa de Argumento muda de um lugar do acórdão para outro?](graficos/fig2_diferencas_local_relator.svg)

**Figura 2 — Quanto a taxa de Argumento muda de um lugar do acórdão para outro?** *Compara:* a taxa entre lugares, na mesma audiência (e relator × demais, H4). *Como ler:* ponto = média entre audiências; barra = faixa de incerteza; a leitura também considera a correção para várias comparações. *Resultado:* Voto do Relator − Relatório: +54,0 pp (16 AP; +40,3 a +66,4). Voto − Relatório: +31,7 (17 AP; +20,1 a +43,2). Voto − Voto do Relator: −20,1 (20 AP; −33,8 a −6,7). *Base:* audiências com menções nos dois lugares; média por audiência.

### 3.2 Ministros e relatoria (H3, H4, H7, H14, H21)

- **Pergunta.** A taxa varia entre ministros? O relator argumenta mais?
- **Variáveis.** *Ministro atribuído* (pelo voto ou, em 291 menções, pelo relator indicado nos metadados) e *relator cadastrado*.
- **O que fizemos e por quê.** H3 descreve taxas por ministro (mín. 15 menções). H4 compara o relator com os demais julgadores fora do Relatório. H7, H14 e H21 (ministro × eixo, ano, categoria) são descritivos, sem base para modelo.
- **Ressalva.** H4 está confundido com o local: o relator quase só aparece no Voto do Relator, e restrita ao Voto faltam audiências.

![A taxa de Argumento varia entre ministros?](graficos/fig3_ministros.svg)

**Figura 3 — A taxa de Argumento varia entre ministros?** *Compara:* a fração de Argumento nas menções de cada ministro. *Como ler:* cada bolha é um ministro; texto = Argumentos de total de menções; bolha maior, mais menções. *Resultado:* Vai de 7,7% a 100,0% (15 de 15 em Celso de Mello, poucas menções); descrição, sem teste. *Base:* 12 ministros com ao menos 15 menções em 3+ audiências.

### 3.3 Tempo (H1, H2, H13, H14, H16, H22)

- **Pergunta.** A taxa muda com o ano, ou com o intervalo entre audiência e julgamento? A tendência difere entre eixos?
- **Variáveis.** *Ano do julgamento* e *intervalo* (anos entre audiência e julgamento).
- **O que fizemos e por quê.** Correlação de ordem (anos maiores acompanham taxas maiores?), um ponto por audiência; e regressão simples para ver se a inclinação difere entre eixos (H13, H16). Intervalo (H2): correlação +0,02; H13 e H16: não identificamos diferença consistente no recorte. H22 está em 3.7.
- **Ressalva.** A AP33 tem intervalo cadastrado −1 (inconsistente): mantido nos dados, fora dos cálculos de intervalo (H2 e H16); dado original preservado, vínculo/data por esclarecer.

![A taxa de Argumento mudou com o passar dos anos?](graficos/fig4_tempo.svg)

**Figura 4 — A taxa de Argumento mudou com o passar dos anos?** *Compara:* a taxa de cada audiência, por ano do julgamento. *Como ler:* cada bolha é uma audiência (tamanho = menções); procure subida ou descida geral. *Resultado:* Sem direção clara no recorte: correlação −0,17, faixa que inclui zero. *Base:* 30 audiências, 1288 menções.

### 3.4 Eixos temáticos e classe processual (H5, H6, H9)

- **Pergunta.** Os eixos (Personalidade, 12 AP; ambiental, políticas públicas e mercado, 18 AP) e as classes processuais diferem na taxa?
- **Variáveis.** *Eixo temático*; *classe processual* (audiências de classe única).
- **O que fizemos e por quê.** Diferença entre as médias por audiência dos eixos (H5) e comparação ADI, ADPF e RE (H9). H6 descreve a variação entre audiências do mesmo eixo. H15 e H20 cruzam eixo com local e com atores (3.1, 3.7).
- **Ressalva.** Poucas audiências por grupo; classes com uma só audiência ficam fora.

![Eixo temático ou classe processual mudam a taxa de Argumento?](graficos/fig5_eixo_classe.svg)

**Figura 5 — Eixo temático ou classe processual mudam a taxa de Argumento?** *Compara:* a taxa de cada audiência entre eixos e entre classes. *Como ler:* cada bolha é uma audiência; compare a altura típica dos grupos; tracejado = taxa geral. *Resultado:* Os grupos se sobrepõem. Eixos: +3,0 pp (faixa −11,1 a +17,2). Classes (média por audiência): ADI 40% (n=14); ADPF 28% (n=4); RE 26% (n=7). Não identificamos diferença consistente no recorte. *Base:* 30 audiências (eixos); 25 de classe única (classes).

### 3.5 Concentração e perfis (H10, H18)

- **Pergunta.** Os Argumentos se concentram em poucas audiências, documentos ou ministros? As audiências formam perfis típicos?
- **Variáveis.** *Contagem* de menções e de Argumentos por unidade; *composição* Contexto/Relato/Argumento de cada audiência.
- **O que fizemos e por quê.** Medimos quanto as 3 maiores unidades concentram (H10, descritivo) e buscamos grupos de audiências parecidas (H18, exploratório; gráfico T4). Nenhum agrupamento foi estável o bastante para declarar perfis.
- **Ressalva.** Poucas unidades; apenas descrição.

![Os Argumentos se concentram em poucas audiências, documentos ou ministros?](graficos/fig6_concentracao.svg)

**Figura 6 — Os Argumentos se concentram em poucas audiências, documentos ou ministros?** *Compara:* quanto as 3 maiores unidades concentram das menções e dos Argumentos. *Como ler:* azul = menções; verde = Argumentos; verde maior que azul indica Argumentos mais concentrados. *Resultado:* Levemente mais concentrados: nas audiências, 39,5% dos Argumentos contra 37,8% das menções. *Base:* 1288 menções, 501 Argumentos; ministros com autoria plena.

### 3.6 Quem é nomeado (H11, H12, H17)

- **Pergunta.** Menções que nomeiam pessoa ou instituição são mais argumentativas?
- **Variáveis.** *Pessoa/instituição nomeada*: pessoa, instituição, ambas ou nenhuma nos campos da menção.
- **O que fizemos e por quê.** Comparamos, em cada audiência, a taxa de Argumento entre os tipos (H11, H12) e descrevemos a associação com a parte do acórdão (H17).
- **Ressalva.** Reflete o preenchimento de campos; 670 menções não nomeiam ninguém.

![As menções nomeiam pessoas ou instituições?](graficos/fig7_nomeados.svg)

**Figura 7 — As menções nomeiam pessoas ou instituições?** *Compara:* os tipos de nome em cada lugar do acórdão. *Como ler:* cada barra soma 100%. *Resultado:* No Relatório predominam menções com pessoa ou instituição identificada (145/242 com nome, 59,9%); nos votos ficam abaixo da metade (Voto do Relator 239/504 com nome, 47,4%; Voto 234/542 com nome, 43,2%). Após as cautelas estatísticas, não detectamos diferença consistente de taxa argumentativa por presença de nome. *Base:* 1288 menções.

### 3.7 Categorias de atores (H19–H22)

- **Pergunta.** Menções ligadas a acadêmicos, sociedade civil, atores públicos etc. têm taxa diferente, entre eixos, ministros ou anos?
- **Variáveis.** *Categoria de ator* (6) e *vínculo*. **A** (principal): o nome do participante aparece na menção (307 menções; 141 vínculos pessoa/AP). **B** (só sensibilidade): vínculo pela entidade, elevando para 616. 670 menções são genéricas (não se aplica); 311 ficam sem vínculo direto (sobretudo entidades), das quais 309 ganham vínculo B e 2 seguem sem categoria.
- **O que fizemos e por quê.** As comparações exigem audiências com e sem a categoria; sem base, o teste não foi feito.
- **Resultado.** **H19** inviável nas 6 categorias; seus 2 valores-p em A vêm de uma sensibilidade de elegibilidade (≥2 por grupo), exploratória. **H20** e **H22**: nenhuma associação detectada após correção (não prova ausência). **H21**: descritiva; modelo não estimado.
- **Ressalva.** Categorias se sobrepõem (24 menções com mais de uma em A; 31 em A+B): não somar percentuais. Taxa por categoria não é representatividade, favorecimento nem exclusão.

![Que atores aparecem nas menções?](graficos/fig8_categorias_atores.svg)

**Figura 8 — Que atores aparecem nas menções?** *Compara:* menções com ator identificado e menções ligadas a cada categoria. *Como ler:* à esquerda, as faixas somam o total; à direita, cada barra é independente (categorias se sobrepõem). *Resultado:* Descrição bruta, sem teste: Acadêmicos 59 de 102 (57,8%); Atores públicos 12 de 77 (15,6%). Partido Político: nenhuma menção, logo sem taxa. *Base:* A: 307 classificadas; A+B: 616; total 1288. Categorias com 10 menções têm pouca base.

## 4. Quadro de consulta: variáveis e gráficos

| Variável | O que é | Usada em | Gráfico |
|---|---|---|---|
| Ano do julgamento / da audiência | Ano do acórdão (e da audiência) | H1, H13, H22 | Fig. 4 |
| Intervalo | Anos entre audiência e julgamento | H2, H16 | Fig. T1 |
| Eixo / tema | Personalidade ou ambiental/políticas/mercado | H5, H6, H13, H15, H20 | Fig. 4, 5 |
| Ministro atribuído | Nome associado à passagem pela extração, às vezes só por metadados | H3, H4, H7, H14, H21 | Fig. 3 |
| Local | Relatório, Voto do Relator ou Voto | H8, H15, H17 | Fig. 1, 2, 7 |
| Classe processual | ADI, ADPF, RE etc. | H9 | Fig. 5 |
| Tipo de menção | Contexto, Relato ou Argumento (o que se estuda) | todas | Fig. 1 |
| Pessoa/instituição nomeada | Campos com pessoa, instituição, ambas ou nenhuma | H11, H12, H17 | Fig. 7 |
| Categoria de ator | Públicos, privados, sociedade civil, acadêmicos, partido, outros | H19–H22 | Fig. 8, T5 |
| Vínculo A/B | A: nome direto; B: via entidade (só sensibilidade) | H19–H22 | Fig. 8 |
| Contagem/concentração | Menções e Argumentos por audiência, documento, ministro | H10, H18 | Fig. 6 |

*ID, página, arquivo e fonte servem só à auditoria; não entram nas análises.*

<details markdown="1">
<summary>5. Quadro das 22 hipóteses (clique para abrir)</summary>

Quatro situações: **diferença observada** (resiste à correção), **comparação inconclusiva** (feita, sem diferença detectada; não prova ausência), **descritivo** (sem teste, por desenho) e **teste não feito** (dados insuficientes).

| H | Pergunta simples | Variáveis | Conclusão / situação | Gráfico |
|---|---|---|---|---|
| H1 | A taxa de Argumento muda conforme o ano do julgamento? | ano do julgamento; tipo de menção | Não identificamos tendência consistente no recorte (correlação −0,17, numa escala de −1 a +1; faixa −0,56 a +0,29 inclui zero). | Fig. 4 |
| H2 | Muda conforme o intervalo (anos) entre audiência e julgamento? | intervalo; tipo de menção | Não identificamos tendência consistente no recorte (correlação +0,02; faixa −0,39 a +0,43). | Fig. T1 (opcional) |
| H3 | A taxa de Argumento difere entre ministros? | ministro atribuído; tipo de menção | Só descrição, sem teste: entre os 12 ministros com base mínima, vai de 7,7% a 100,0% (mínimo de 15 menções cada; o máximo é 15 de 15). | Fig. 3 |
| H4 | O relator tem taxa de Argumento maior que os demais julgadores? | ministro atribuído; relator cadastrado; local | **Diferença observada**: +23,6 pp (24 audiências; faixa +11,3 a +35,5), mas **misturada com o local**: não dá para atribuir à função de relator. | Fig. 2 e 3 |
| H5 | Os dois eixos temáticos diferem na taxa de Argumento? | eixo; tipo de menção | Sem diferença detectada (+3,0 pp, ambiental/mercado menos personalidade; faixa −11,1 a +17,2; p ajustado 0,71). | Fig. 5 |
| H6 | Quanto as audiências variam entre si dentro de cada eixo? | eixo; taxa por audiência | Só descrição: há grande variação entre audiências do mesmo eixo (ver pontos da Fig. 5); não houve teste. | Fig. 5 e T2 (opcional) |
| H7 | O padrão por ministro depende do eixo? | ministro; eixo | Descritivo: só 8 ministros têm base nos dois eixos; modelo desaconselhado, nenhum teste. | — (tabela técnica; Fig. 3 mostra só ministros) |
| H8 | O tipo de menção depende de onde ela está no acórdão? | local; tipo de menção | **Diferença observada**: Argumento é raro no Relatório e comum nos votos; média por audiência +54,0 pp (Voto do Relator − Relatório) e +31,7 pp (Voto − Relatório); mesmo após correção. Local também serviu de indício para classificar. | Fig. 1 e Fig. 2 |
| H9 | Muda conforme a classe processual (ADI, ADPF, RE)? | classe processual; tipo de menção | Sem diferença detectada (médias por audiência: ADI 40% (n=14); ADPF 28% (n=4); RE 26% (n=7); p ajustado 0,33). | Fig. 5 |
| H10 | Os Argumentos são mais concentrados que as menções? | contagem de menções e de Argumentos por unidade | Só descrição: levemente mais concentrados (3 maiores audiências: 39,5% dos Argumentos contra 37,8% das menções); sem teste. | Fig. 6 |
| H11 | A taxa muda conforme o tipo de nome citado (pessoa, instituição, ambos)? | pessoa/instituição nomeada; tipo de menção | Sem diferença detectada após correção; a maior ('pessoa e instituição', −15,1 pp) não se sustenta (p ajustado 0,23). | Fig. 7 |
| H12 | A taxa de Argumento varia conforme a menção nomear alguém? | com nome × sem nome; tipo de menção | Sem diferença detectada (−5,2 pp; faixa −16,1 a +6,1; p ajustado 0,63). | Fig. 7 |
| H13 | A tendência ao longo dos anos difere entre eixos? | ano do julgamento; eixo | Sem diferença detectada entre as tendências (p ajustado 0,89). | Fig. 4 |
| H14 | A taxa de cada ministro varia com o tempo? | ministro; ano | Descritivo: só 8 ministros com 3+ anos de base; modelo desaconselhado, nenhum teste. | — (tabela técnica) |
| H15 | A distribuição das menções entre as partes do acórdão (composição) difere entre eixos? | local; eixo | Sem diferença detectada (menor p ajustado 0,71); análise adicional também inconclusiva. | Fig. T3 (opcional) |
| H16 | A relação com o intervalo difere entre eixos? | intervalo; eixo | Sem diferença detectada (p ajustado 0,89). | Fig. T1 (opcional) |
| H17 | A presença de pessoa/instituição nomeada se associa à parte do acórdão? | pessoa/instituição nomeada; local | Sem diferença detectada (menor p ajustado 0,33); a distribuição por lugar é descrita na Fig. 7. | Fig. 7 |
| H18 | As audiências formam perfis típicos de composição? | composição Contexto/Relato/Argumento por audiência | Exploratório: nenhum agrupamento atingiu o critério de estabilidade; não declaramos perfis. | Fig. T4 (opcional) |
| H19 | Menções com cada categoria de ator têm taxa diferente das sem ela? | categoria de ator; vínculo A/B; tipo de menção | **Teste não feito** no critério principal em todas as 6 categorias (poucas audiências com e sem a categoria). Os 2 valores-p em A vêm de uma sensibilidade mais frouxa (≥2 por grupo): exploratória, inconclusiva. | Fig. 8 |
| H20 | As categorias de ator aparecem de modo diferente entre eixos? | categoria de ator; eixo | Nenhuma associação detectada após correção (menor p ajustado 0,87); não prova ausência. Partido Político sem menções. | Fig. T5 (opcional) e Fig. 8 |
| H21 | A taxa de Argumento por ministro varia conforme a categoria de ator? | ministro; categoria de ator; tipo de menção | **Descritiva; modelo não estimado** por falta de base (células pequenas). Não é preferência individual. | Fig. T6 (opcional) |
| H22 | A presença de cada categoria de ator e a taxa de Argumento mudam com os anos? | categoria de ator; ano do julgamento | Nenhuma associação detectada após correção (menor p ajustado 0,55); 4 comparações sem base; não prova ausência. | Fig. T7 (opcional) |

</details>

<details markdown="1">
<summary>Gráficos técnicos opcionais (mais complexos)</summary>

![O intervalo entre audiência e julgamento se associa à taxa de Argumento?](graficos/tecnicos/fig02_intervalo_taxa.svg)

**Figura T1 — O intervalo entre audiência e julgamento se associa à taxa de Argumento?** (H2, H16). Versão técnica original; leitura detalhada no relatório completo.

![Quanto varia a taxa entre audiências do mesmo eixo?](graficos/tecnicos/fig03_eixos_e_heterogeneidade.svg)

**Figura T2 — Quanto varia a taxa entre audiências do mesmo eixo?** (H5, H6). Versão técnica original; leitura detalhada no relatório completo.

![A composição entre relatório e votos varia por eixo?](graficos/tecnicos/fig08_h15_local_por_eixo.svg)

**Figura T3 — A composição entre relatório e votos varia por eixo?** (H15). Versão técnica original; leitura detalhada no relatório completo.

![As audiências formam perfis parecidos de composição?](graficos/tecnicos/fig10_h18_pca_composicao.svg)

**Figura T4 — As audiências formam perfis parecidos de composição?** (H18). Versão técnica original; leitura detalhada no relatório completo.

![As categorias de ator aparecem de modo diferente nos dois eixos?](graficos/tecnicos/fig13_h20_incidencia_por_eixo.svg)

**Figura T5 — As categorias de ator aparecem de modo diferente nos dois eixos?** (H20). Versão técnica original; leitura detalhada no relatório completo.

![A taxa de Argumento por ministro muda conforme a categoria de ator?](graficos/tecnicos/fig14_h21_ministro_x_categoria.svg)

**Figura T6 — A taxa de Argumento por ministro muda conforme a categoria de ator?** (H21). Versão técnica original; leitura detalhada no relatório completo.

![As categorias de ator mudam ao longo dos anos?](graficos/tecnicos/fig15_h22_composicao_e_aproveitamento.svg)

**Figura T7 — As categorias de ator mudam ao longo dos anos?** (H22). Versão técnica original; leitura detalhada no relatório completo.

</details>

## 6. Para discutir com a orientadora

**Contribuição empírica.** O estudo descreve quantitativamente o corpus. As comparações mais nítidas foram entre partes do acórdão (Relatório × votos); os demais resultados, inconclusivos ou sem suporte, não provam que tema, tempo ou atores sejam irrelevantes. Parte dessa associação também pode refletir o uso do local como indício na classificação.
**Contribuição metodológica.** Audiência como unidade, correção para várias comparações e transparência sobre o que não foi testado. Das 40 comparações com valor-p no cenário principal, 4 (em H4, H8) resistem à correção.

**Limites.**
- Não é censo de menções nem de audiências; a lista de participantes também não é o universo completo.
- No máximo 30 unidades por comparação: pouco poder de detecção.
- 291 atribuições de ministro vêm de metadados; 17 têm nomes incompletos.
- 1019 das 1288 classificações foram feitas por IA sem revisão humana; esse erro está **fora** das faixas de incerteza.
- AP33 tem cadastro inconsistente (intervalo −1): ficou fora dos cálculos de intervalo; dado original preservado.

**Questões para aprofundamento qualitativo.**
1. Ler os Argumentos do Voto do Relator e do Relatório: qual a função de cada parte?
2. Como separar relator e lugar?
3. O que ficou fora do levantamento (contribuições e votos sem menção)?
4. Em que contextos surgem as diferenças descritivas entre categorias de ator (por exemplo, Acadêmicos e Atores públicos), e por que nenhuma menção liga a partidos?
5. Revisão humana por amostra poderia estimar o erro da IA.

## Notas e fontes

Números extraídos de `results/h1_h22/matriz_resultados_H1_H22.csv`, `resumo_por_hipotese.csv`, `validacao_integracao.json`, `results/figures/dados/*.csv` e `data/processed/*.csv` (somente leitura). Gráficos 1–8 redesenhados por `gerar_relatorio_simplificado.py` a partir desses dados; os T1–T7 são cópias dos gráficos técnicos originais. Entradas e SHA-256 (antes/depois): `manifesto_versao_orientadora.json`. Detalhes, fórmulas e robustez: [relatório técnico](../relatorio_consolidado_H1_H22.html).
