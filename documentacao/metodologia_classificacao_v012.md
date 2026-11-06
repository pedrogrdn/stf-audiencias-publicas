# Metodologia para análise de menções às audiências públicas nos acórdãos do STF

**Status:** documento metodológico em desenvolvimento

**Versão:** 0.12

**Data da versão:** 5 de novembro de 2026

**Recorte da atualização:** testes, pilotos, execução das 3.010 menções restantes, revisão das 112 pendências sinalizadas e organização da base final por eixo temático e por pessoa. Não estabelece protocolo de auditoria amostral ou intervalos de confiança. A versão deste documento (0.12) difere da versão das instruções utilizadas (v6.1), que permanece preservada.

**Nota de leitura:** as regras e execuções das versões anteriores foram preservadas como histórico. As escolhas posteriores aos testes de IA estão consolidadas na seção 14 e prevalecem, para a classificação atual, sobre as exclusões históricas de bibliografia, terceiros e *amici curiae* e sobre a tipologia exploratória da seção 8. A atualização deste documento não implica migração automática de toda a base canônica.

## 1. Finalidade do documento

Este documento registra as decisões metodológicas adotadas para identificar e analisar, nos acórdãos do Supremo Tribunal Federal, menções às audiências públicas e ao conteúdo apresentado por seus participantes.

Ele deve funcionar como um documento vivo. À medida que as listas de participantes, as regras de busca e os procedimentos de classificação forem aperfeiçoados, as mudanças relevantes também deverão ser registradas aqui. O objetivo é impedir que decisões tomadas durante o desenvolvimento do código se tornem implícitas ou se percam ao longo da pesquisa.

## 2. Pergunta de pesquisa operacional

A pergunta central desta etapa não é simplesmente se o nome de um participante aparece no acórdão. A pergunta é:

> Uma determinada passagem do acórdão retoma, atribui, discute ou utiliza conteúdo apresentado em audiência pública?

Essa formulação é necessária porque uma pessoa que participou de uma audiência também pode aparecer no mesmo processo em outra qualidade, por exemplo como advogado, representante de uma parte, *amicus curiae*, autor de obra citada, perito ou autoridade pública.

A simples coincidência entre um nome constante da lista de participantes e um nome encontrado no acórdão não demonstra que o acórdão esteja mencionando a audiência ou utilizando a contribuição feita nela.

Na versão 0.9, adotou-se uma ampliação deliberada do corpus: referências a livros e artigos de participantes confirmados também são elegíveis, mesmo sem remissão expressa à audiência. A pergunta operacional passa a abranger tanto a presença da audiência e de suas contribuições quanto a presença bibliográfica de seus participantes nas decisões. Essa segunda modalidade não comprova que a posição foi apresentada oralmente nem que a audiência causou sua utilização. Essa delimitação deverá constar da formulação definitiva da pergunta e da interpretação dos resultados na dissertação.

## 3. Escopo

### 3.1. Incluído no escopo

- menções expressas à realização de audiência pública;
- atribuições expressas de argumentos, dados ou esclarecimentos a participantes da audiência;
- referências coletivas aos expositores, especialistas ouvidos ou manifestações apresentadas na audiência;
- possíveis retomadas implícitas de argumentos da audiência, quando houver correspondência verificável com a transcrição ou outro documento oficial;
- identificação da forma como o conteúdo da audiência aparece no acórdão, como relatório, fundamentação, contraposição, crítica ou simples descrição.

### 3.2. Fora do escopo, salvo quando necessário para distinguir contextos

- mapear todas as atuações processuais dos participantes;
- classificar de maneira completa partes, advogados e *amici curiae*;
- considerar toda menção nominal a um participante como efeito da audiência;
- inferir influência causal sem evidência textual suficiente;
- avaliar, nesta etapa, a correção jurídica ou científica dos argumentos apresentados.

Outros papéis processuais podem ser registrados como contexto negativo, isto é, para justificar por que determinada ocorrência nominal não foi classificada como menção relacionada à audiência.

## 4. Unidade de análise

A unidade básica de análise é a **ocorrência contextualizada** ou **passagem argumentativa**, composta por:

- acórdão e processo;
- página do PDF;
- trecho no qual ocorre a menção;
- contexto imediatamente anterior e posterior;
- pessoa ou coletividade mencionada, quando identificável;
- possível conteúdo correspondente nos documentos da audiência;
- classificação do vínculo com a audiência;
- evidências que sustentam a classificação.

A classificação não deve ser atribuída globalmente à pessoa. Uma mesma pessoa pode ter várias ocorrências no mesmo acórdão, e cada ocorrência deve ser avaliada separadamente.

Para a base operacional, uma ocorrência corresponde a uma frase contextualizada em um acórdão, página e parágrafo. Todos os alvos recuperados na mesma frase são reunidos em uma única linha. Assim, se a frase mencionar uma instituição e a pessoa que a representa, ambas continuam sendo pesquisadas, mas o resultado registra uma passagem com os dois alvos separados por ` | `. O parágrafo completo permanece como contexto para aplicação das regras e revisão.

Se o mesmo alvo aparecer mais de uma vez na frase, o programa conserva uma única linha e registra o total em `quantidade_mencoes_na_frase`. O campo `quantidade_alvos_na_frase` informa quantos alvos canônicos distintos foram reunidos. O mesmo alvo em frases diferentes permanece em linhas distintas, ainda que as frases estejam no mesmo parágrafo ou na mesma página.

Exemplo hipotético:

1. “Na audiência pública, a professora Ana afirmou...” — ocorrência relacionada à audiência;
2. “A advogada Ana requereu...” — ocorrência processual sem vínculo demonstrado com a audiência;
3. “Segundo artigo publicado por Ana...” — citação bibliográfica elegível sob a regra da versão 0.9 se Ana for participante confirmada e não estiver abrangida pela exclusão das partes; não equivale a vínculo oral comprovado.

Ao final, as ocorrências podem ser agregadas por pessoa, audiência ou processo, sem apagar as classificações individuais.

## 5. Fontes documentais

As principais fontes previstas são:

- acórdãos e votos armazenados em `acordaos/`;
- transcrições e notas taquigráficas armazenadas em `documentos_audiencias/`, únicas fontes admitidas para comprovar presença na lista operacional de participantes;
- programações, relações de habilitados, convocações e demais documentos oficiais, mantidos apenas como fontes contextuais e de auditoria, sem força autônoma para incluir participantes;
- lista relacional versionada de participantes em `resultados/participantes_relacional_limpo.csv`;
- arquivo operacional de variantes em `resultados/termos_busca_acordaos_ativos.csv`;
- planilhas de controle que vinculam audiência, processo e arquivo do acórdão;
- resultados intermediários de busca, sempre preservando arquivo, página e trecho.

Cada conclusão deve ser rastreável até as fontes utilizadas. Sempre que possível, devem ser registrados o arquivo, a página e a passagem textual relevante.

### 5.1. Levantamento dos documentos das audiências

O levantamento documental foi realizado audiência por audiência a partir das páginas oficiais do STF. Foram reunidos, sempre que disponíveis:

- relação de inscritos ou habilitados;
- convocação e decisões de organização da audiência;
- cronograma ou programação nominal;
- transcrição e notas taquigráficas;
- documentos complementares disponibilizados na página da audiência;
- o próprio acórdão ou os acórdãos vinculados à audiência.

A coleta resultou, nesta versão, em 125 documentos oficiais distribuídos por 31 audiências públicas, armazenados em subpastas de `documentos_audiencias/`. O arquivo `documentos_audiencias/manifesto.json` registra a audiência, o rótulo apresentado pelo STF e o caminho local de cada documento.

Não se presume que relações de habilitados, editais, convocações, cronogramas ou programações comprovem comparecimento. A partir da versão 0.7, uma pessoa ou instituição somente integra a lista operacional quando sua presença está registrada nas notas taquigráficas ou na transcrição da própria audiência. Os demais documentos continuam disponíveis para compreender a organização do evento, localizar possíveis substituições e auditar exclusões, mas não geram participantes por si sós.

Documentos meramente bibliográficos ou de legislação correlata não foram considerados evidência de participação. Pessoas e instituições neles mencionadas podem ser relevantes para o tema, mas não necessariamente estiveram presentes na audiência.

### 5.2. Exceções documentais relevantes

Três conjuntos documentais exigiram tratamento específico:

- a audiência pública 1 possui notas taquigráficas em PDF integralmente digitalizado. As 231 páginas receberam OCR local Apple Vision; somente os 22 falantes identificados nos cabeçalhos das notas foram mantidos. Os nomes provenientes apenas da relação de habilitados foram excluídos;
- a audiência pública 3 possui quatro arquivos de notas taquigráficas, correspondentes a 26 e 28 de agosto e 4 e 16 de setembro de 2008. Substituições, representantes adicionais, depoentes e grafias alternativas foram confirmados nesses próprios arquivos; o cronograma deixou de ser fonte de inclusão;
- a audiência pública 4 disponibiliza as notas taquigráficas em página HTML oficial, com programação e links individuais para as falas. Somente nomes vinculados às falas dessa página foram incorporados, com exclusão dos ministros do STF que conduziram os trabalhos.

Essas exceções permanecem identificadas nos campos de método, fonte, arquivo, página e evidência da lista relacional.

### 5.3. Consolidação do corpus de audiências e ações

Antes da análise das menções, foi elaborado um quadro de delimitação do corpus com uma linha por audiência pública realizada. O levantamento combinou:

- as páginas oficiais de audiências públicas realizadas do STF, distribuídas nas páginas de paginação `https://portal.stf.jus.br/audienciapublica/audienciaPublica.asp?pagina=1&tipo=realizada` a `pagina=5`;
- a planilha operacional `acoes_audiencias_stf.xlsx`, construída durante a coleta e o download dos acórdãos;
- os metadados dos processos e dos acórdãos armazenados no projeto;
- notícias e páginas oficiais específicas do STF, utilizadas para confirmar informações ausentes ou ambíguas, especialmente o ministro convocante.

A consolidação realizada em 21 de agosto de 2026 identificou 49 audiências públicas realizadas e 78 relações entre audiência e ação. O resultado foi preservado em `outputs/corpus_audiencias_stf_20260821/corpus_audiencias_publicas_stf.xlsx`, com as folhas `Tabela para artigo`, `Fontes` e `Metodologia`.

Foram adotados os seguintes critérios:

- **número da audiência:** manteve-se a numeração atribuída pelo STF;
- **ano:** registrou-se o ano em que a audiência efetivamente ocorreu, e não o ano de autuação da ação, de convocação ou de publicação do acórdão;
- **ação:** classe e número foram apresentados juntos; quando uma audiência esteve vinculada a mais de uma ação, todas foram conservadas na mesma célula, separadas por ponto e vírgula;
- **tema:** foi redigida uma síntese curta e normalizada do título ou da descrição oficial, preservando o conteúdo substantivo e retirando informações meramente logísticas;
- **ministro ou ministros convocantes:** foram registrados somente quando a convocação ou a condução conjunta pôde ser confirmada em fonte oficial; nas audiências conjuntas, todos os convocantes confirmados foram mantidos;
- **rastreabilidade:** a folha `Fontes` conserva os endereços oficiais consultados e a folha `Metodologia` registra os critérios de composição da tabela.

A unidade usada nesse quadro é a audiência, não a ação. Por isso, a existência de várias ações na mesma linha não representa duplicidade: preserva o vínculo de uma única audiência com todos os processos que compõem seu objeto. Inversamente, uma ação poderá aparecer em mais de uma etapa documental do projeto sem que isso implique a existência de uma nova audiência.

Foram objeto de verificação individual as seguintes situações:

- **audiência 21:** foram mantidas conjuntamente a ADI 5527 e a ADPF 403, convocadas por Rosa Weber e Edson Fachin;
- **audiência 38:** foram mantidos conjuntamente o RE 1037396 e o RE 1057258, convocados por Dias Toffoli e Luiz Fux;
- **audiência 39:** foram preservadas a ADO 84 e a ADPF 1143, pois a conversão da primeira classe na segunda integra a trajetória processual relevante para a delimitação do corpus;
- **audiência 48:** adotou-se o ARE 1542420, coerente com o título e a descrição oficial sobre direitos autorais no ambiente digital. A referência à ADI 7788 no rodapé da página foi tratada como inconsistência material da página oficial, pois essa ação corresponde à audiência 46.

Os ministros convocantes das audiências 22, 23, 24 e 25, que exigiram complementação, foram confirmados em páginas ou notícias oficiais do STF como, respectivamente, Dias Toffoli, Rosa Weber, Luiz Fux e Ricardo Lewandowski.

O quadro consolidado delimita o universo documental da pesquisa, mas não substitui a verificação da disponibilidade de acórdão de mérito. Uma audiência pode integrar o corpus institucional e ainda não possuir acórdão principal publicado, ou possuir mais de um processo com situações documentais diferentes. Essa disponibilidade deve continuar sendo registrada separadamente nas planilhas de controle da coleta.

## 6. Distinções conceituais fundamentais

### 6.1. Menção à pessoa não equivale a menção à audiência

Encontrar o nome de um participante é apenas um mecanismo de recuperação de candidatos. A ocorrência somente será considerada relacionada à audiência quando o próprio acórdão ou a comparação documental fornecer evidência do vínculo.

### 6.2. Participação na audiência não equivale a *amicus curiae*

Participação como expositor e admissão formal como *amicus curiae* são relações distintas. Uma pessoa ou instituição pode ocupar ambas as posições, apenas uma delas ou nenhuma delas. Essa condição não deve ser inferida somente pela presença do nome.

### 6.3. Correspondência temática não equivale automaticamente a retomada

O fato de o acórdão discutir o mesmo tema tratado na audiência não basta para atribuir a passagem a um participante. Para classificar uma retomada implícita, deve haver correspondência suficientemente específica entre as passagens, considerada em conjunto com autoria, vocabulário, dados, exemplos ou estrutura do argumento.

### 6.4. Ausência do nome não equivale a ausência de menção

O acórdão pode se referir coletivamente a “especialistas ouvidos”, “expositores”, “participantes da audiência” ou “dados apresentados perante esta Corte”. Por isso, a pesquisa não pode depender exclusivamente da lista nominal.

## 7. Classificação do vínculo com a audiência

Cada ocorrência candidata deverá receber uma das seguintes classificações principais.

### 7.1. Vínculo explícito

O texto do acórdão relaciona expressamente a passagem à audiência pública.

Exemplos de indícios:

- “na audiência pública”;
- “durante a audiência”;
- “conforme esclarecido pelo expositor”;
- “os especialistas ouvidos por esta Corte”;
- “os dados apresentados na audiência”.

O vínculo explícito pode ser nominal, quando identifica uma pessoa, ou coletivo/anônimo, quando se refere ao conjunto dos participantes.

### 7.2. Vínculo implícito comprovável

O acórdão não menciona expressamente a audiência, mas atribui ou reproduz conteúdo que pode ser relacionado de maneira suficientemente segura a uma manifestação registrada na transcrição ou em outro documento oficial da audiência.

Essa classificação exige comparação entre, no mínimo:

- a passagem do acórdão;
- a passagem correspondente do documento da audiência;
- a identificação do participante ou da fonte, quando disponível.

Devem ser evitadas classificações baseadas apenas em semelhança temática genérica.

### 7.3. Sem vínculo demonstrável

A pessoa, instituição ou ideia aparece no acórdão, mas não há evidência suficiente de que a ocorrência retome a audiência.

Exemplos:

- nome no cabeçalho como advogado;
- atuação como parte ou *amicus curiae* sem referência à audiência;
- citação bibliográfica independente;
- menção institucional genérica;
- coincidência nominal sem correspondência contextual.

### 7.4. Indeterminado

Há indícios de relação com a audiência, mas as fontes disponíveis não permitem decisão segura. Esses casos devem ser encaminhados para revisão humana e não convertidos automaticamente em ocorrência positiva ou negativa.

### 7.5. Pré-classificações operacionais do programa

Para organizar a revisão sem antecipar uma conclusão substantiva, o programa utiliza rótulos operacionais mais granulares:

- `vínculo explícito`: a regra encontrou evidência forte de que a audiência mencionada é a audiência do processo;
- `vínculo explícito provável`: há expressão literal relacionada à audiência, mas o trecho ainda requer confirmação humana de escopo e de uso;
- `sem vínculo com a audiência pesquisada`: a passagem se refere expressamente a outra audiência, por exemplo uma audiência realizada no processo legislativo;
- `alvo em contexto explícito`: uma pessoa ou instituição da lista aparece na mesma passagem em que a audiência do processo é mencionada;
- `candidato a vínculo implícito`: o alvo aparece sem expressão explícita da audiência e deve ser comparado com a transcrição ou com outra fonte oficial;
- `sem vínculo demonstrável neste trecho`: a ocorrência recuperada, isoladamente, não contém evidência do vínculo.

Esses rótulos são resultados de triagem. Somente a revisão das evidências poderá convertê-los nas categorias analíticas finais descritas nas seções 7.1 a 7.4.

### 7.6. Status operacional da ocorrência

A classificação textual e o status são campos distintos. A classificação descreve o vínculo que o programa encontrou; o status informa se a ocorrência integra o corpus nesta etapa. Para simplificar a revisão, somente cinco valores são admitidos:

- `Parte do corpus - automático`: menção expressa à audiência pesquisada reconhecida por regra de alta precisão;
- `Excluído do corpus - automático`: referência a outra audiência ou ocorrência nominal em contexto processual negativo no mesmo parágrafo;
- `pendente`: a evidência automática não permite decisão segura;
- `Excluído do corpus`: exclusão confirmada por revisão humana;
- `Parte do corpus`: inclusão confirmada por revisão humana.

Uma pessoa ou instituição encontrada no mesmo parágrafo de uma referência à audiência permanece `pendente`. Essa proximidade é um indício forte, mas não basta para inclusão automática, pois o parágrafo ainda pode mencionar o alvo em outra qualidade. A inclusão automática fica restrita à própria expressão de audiência pública quando o escopo da audiência pesquisada é identificado com alta precisão.

## 8. Tipos de uso do conteúdo da audiência

**Histórico:** a lista exploratória abaixo foi substituída, para os experimentos atuais, pelas três categorias de engajamento da seção 14.2. Não constitui uma lista de subcategorias manuais obrigatórias.

Além do vínculo, as ocorrências positivas poderão receber uma segunda classificação, referente ao uso feito no acórdão:

- descrição da realização ou do procedimento da audiência;
- síntese da manifestação de participante;
- citação ou paráfrase de argumento;
- uso de dado, exemplo ou evidência empírica;
- fundamento favorável à conclusão do voto;
- argumento mencionado para ser afastado ou criticado;
- registro de divergência entre participantes;
- referência coletiva sem argumento individualizável;
- outro tipo, acompanhado de justificativa.

A presença de um argumento no voto não deve ser automaticamente interpretada como concordância. O campo de tipo de uso deve distinguir adoção, descrição, crítica e rejeição sempre que o contexto permitir.

## 9. Fluxo de trabalho

As três primeiras etapas deste fluxo já foram parcialmente implementadas na preparação da lista relacional e do arquivo de variantes. As etapas posteriores descrevem a aplicação desses insumos aos acórdãos e permanecem sujeitas à validação empírica.

### Etapa 1 — Consolidar as relações básicas

Relacionar, com identificadores estáveis:

- audiência pública;
- processo ou processos vinculados;
- acórdão correspondente;
- documentos oficiais da audiência;
- participantes e variantes de seus nomes.

A lista de participantes pode continuar sendo revisada durante o desenvolvimento. Toda versão usada em uma execução deve ser identificável.

### Etapa 2 — Preparar os textos

- extrair o texto dos PDFs preservando a associação com as páginas;
- registrar páginas sem texto ou com provável problema de OCR;
- normalizar espaços e caracteres somente para a busca;
- conservar o texto original para apresentação da evidência;
- reconstruir e preservar o parágrafo completo no qual o alvo aparece;
- quando possível, preservar seções e marcadores de voto.

Alguns acórdãos contêm duas camadas textuais idênticas na mesma posição da página. Para impedir a duplicação artificial das ocorrências, o piloto elimina blocos que possuam simultaneamente o mesmo texto e as mesmas coordenadas. A página renderizada deve ser consultada em amostra para confirmar que a remoção não apagou conteúdo visualmente distinto.

Na versão 0.6.1, o programa mede a densidade da camada textual de cada PDF antes da busca. Arquivos com menos de 200 caracteres extraídos por página são tratados como digitalizados ou insuficientes e exigem uma camada de OCR válida. No macOS, `ocr_pdf_vision.swift` renderiza as páginas e usa Apple Vision com idioma `pt-BR`; o resultado é armazenado em `resultados/ocr_acordaos/` para reuso e auditoria. Se não houver OCR disponível, ou se ele continuar insuficiente, a execução é interrompida para o arquivo em vez de registrar falsamente zero ocorrência.

O texto reconhecido permanece inalterado no trecho apresentado como evidência. Somente a representação usada para busca recebe correções conservadoras, de mesmo comprimento, para confusões gráficas observadas em expressões de alta relevância, como `audiencla` por `audiencia` e `publlca` por `publica`. O campo técnico `metodo_extracao_texto` distingue `camada textual nativa` de `OCR Apple Vision` em cada ocorrência.

### Etapa 3 — Recuperar ocorrências candidatas

A recuperação deve combinar pelo menos duas estratégias.

#### Rota A — Expressões relacionadas à audiência

Buscar “audiência pública” e variantes contextuais, incluindo referências indiretas a expositores, especialistas ouvidos, manifestações e dados apresentados.

#### Rota B — Nomes e instituições participantes

Buscar nomes completos, variantes justificadas, formas abreviadas e instituições associadas. Cada termo nominal ou institucional deve ser aplicado somente aos acórdãos vinculados à respectiva audiência. As expressões gerais “audiência pública” e “audiências públicas”, por sua vez, devem ser aplicadas a todos os acórdãos. Essa rota tem a finalidade de encontrar candidatos e não de classificá-los automaticamente como menções à audiência.

Poderão ser incluídas buscas aproximadas para erros de OCR, desde que o resultado indique o método pelo qual o candidato foi recuperado.

Quando variantes sobrepostas identificarem o mesmo alvo na mesma posição — por exemplo, nome completo e forma abreviada —, elas serão consolidadas em uma única ocorrência, preservando-se a relação das variantes acionadas. A versão 0.8 consolida, em seguida, repetições do mesmo alvo na frase e alvos distintos encontrados na mesma frase. `termo_busca` preserva as variantes acionadas, `quantidade_mencoes_na_frase` preserva o total de menções e `quantidade_alvos_na_frase` preserva o total de alvos canônicos. Siglas são procuradas com respeito à caixa original para reduzir falsos positivos causados por palavras comuns, especialmente em textos ou citações em língua estrangeira.

### Etapa 4 — Montar o contexto

Para cada candidato, conservar contexto suficiente para interpretar a passagem. Na saída canônica, `trecho_acordao` contém o parágrafo completo delimitado por linhas em branco e `pagina_acordao` contém a página física do PDF. Uma janela ampliada continua disponível em `contexto_acordao` para auxiliar a decisão, mas não substitui a evidência paragráfica. Também são conservados, quando recuperáveis:

- parágrafo anterior e posterior;
- título ou seção;
- identificação do ministro e do voto;
- página anterior ou seguinte quando a frase estiver interrompida.

O piloto também identifica automaticamente, quando a estrutura do acórdão permite, o ministro responsável pela passagem. Para facilitar o tratamento posterior dos votos, o local analítico foi reduzido a três valores: `Relatório`, `Voto do Relator` e `Voto`. A última categoria engloba voto-vista, voto-vogal, antecipação, observação, esclarecimentos e manifestações de ministros distintos do relator. O resultado conserva ainda a página física do PDF; a numeração interna e o cabeçalho estrutural detalhado permanecem disponíveis no CSV completo para auditoria. A identificação automática de ministro e seção permanece sujeita a revisão, sobretudo em debates, citações de votos alheios e documentos com cabeçalhos irregulares.

### Etapa 5 — Aplicar regras de alta precisão

**Compatibilidade:** esta etapa documenta regras determinísticas das versões 0.5 a 0.8. Exclusões por bibliografia, terceiro ou *amicus curiae* não representam integralmente a decisão atual da seção 14.1. Antes da produção do corpus definitivo, será necessário compatibilizar código, insumos e decisões humanas; os testes de IA não efetuaram essa migração integral.

Regras determinísticas podem reconhecer ocorrências claramente processuais ou claramente ligadas à audiência. Exemplos:

- marcadores como `ADV.(A/S)`, `REQTE.`, `REQDO.` e `INTDO.` ajudam a identificar ocorrências que, isoladamente, não demonstram vínculo com a audiência;
- expressões como “na audiência pública” ou “especialistas ouvidos” constituem evidência forte de vínculo explícito.

As regras devem registrar qual padrão foi acionado. Elas não devem eliminar a ocorrência nem substituir a evidência original.

As ocorrências de pessoas e instituições são marcadas como `Excluído do corpus - automático` quando o mesmo parágrafo fornece evidência processual negativa de alta precisão. Desde a versão 0.5, isso abrange:

- `amicus curiae`, `amici curiae`, abreviações equivalentes ou “amigo da Corte”;
- indicação expressa da qualidade de parte ou marcador processual formal de parte;
- indicação expressa da qualidade de terceiro interessado ou interveniente;
- enumeração documental que combine `peça` e `petição`, como “peça 219, pet. 20648/2023”.

Na versão 0.7.0 foram acrescentadas duas famílias de regras:

- `EXC-BIBLIOGRAFIA`: exclui a ocorrência quando o alvo integra referência a livro, artigo acadêmico, capítulo, entrevista, revista, DOI, ISBN ou endereço bibliográfico. A regra exige marcador direto ou proximidade direcional suficientemente forte; a mera palavra “artigo” em referência a dispositivo legal não aciona a exclusão;
- `EXC-REQUERENTE` e `EXC-REPRESENTANTE-PROCESSUAL`: excluem ocorrências próximas a rótulos formais ou verbos que indiquem autoria, requerimento ou protocolo da ação, bem como atuação como advogado, procurador ou representante processual. Quando o parágrafo enumera vários sujeitos, o programa usa o rótulo formal mais próximo para evitar atribuir a qualidade de requerente ou advogado a um nome posterior não relacionado.

A regra é aplicada à unidade paragráfica reconstruída, e não a uma janela genérica de caracteres. Linhas em branco, inclusive as que contêm espaços residuais do PDF, separam os parágrafos. Essa restrição é essencial: um cabeçalho de *amicus curiae* em outro ponto da página não deve excluir uma passagem substantiva, e uma enumeração de petições não deve contaminar o parágrafo seguinte que descreve a audiência.

A prioridade de decisão é: contexto processual negativo no mesmo parágrafo; referência expressa a outra audiência; referência expressa à audiência pesquisada; candidato pendente. Todas as exclusões permanecem na tabela central, com trecho, código da regra e justificativa, para permitir auditoria e revisão por amostragem.

Na versão 0.8, cada alvo é classificado antes da consolidação da frase. Se todos os alvos levarem ao mesmo status, a frase conserva esse status e reúne os códigos das regras. Se a frase combinar um alvo excluído automaticamente e outro pendente, prevalece `pendente`, com o código `MULTIPLOS-ALVOS-PENDENTE`, evitando excluir toda a passagem por causa do papel processual de apenas um dos nomes. Uma referência explícita de alta precisão à audiência pesquisada conserva `Parte do corpus - automático`, ainda que a mesma frase contenha outros alvos.

### Etapa 6 — Comparar acórdão e documentos da audiência

Nos candidatos sem decisão clara, comparar a passagem do acórdão com as falas e documentos associados ao possível participante.

A comparação poderá utilizar busca lexical, medidas de similaridade e um modelo de linguagem. O modelo deve receber apenas o contexto relevante e retornar uma classificação estruturada, acompanhada das evidências encontradas nos dois documentos.

O modelo não deve ser instruído a preencher lacunas por plausibilidade. Quando não houver evidência suficiente, a resposta correta será “indeterminado” ou “sem vínculo demonstrável”, conforme o caso.

No piloto, a recuperação da passagem de comparação foi implementada antes de qualquer classificação semântica por IA. Para cada candidato implícito, o programa procura primeiro o alvo nas transcrições e notas oficiais da audiência, dando preferência a cabeçalhos de fala e a passagens nominalmente atribuídas. Essa passagem é anexada ao pacote de revisão como fonte candidata; sua simples recuperação não comprova que o acórdão retomou o argumento.

### Etapa 7 — Revisar casos selecionados

Devem ser priorizados para revisão humana:

- vínculos implícitos;
- ocorrências classificadas como indeterminadas;
- correspondências baseadas em nome abreviado ou busca aproximada;
- casos em que regras e modelo divergem;
- passagens sem participante individualizado;
- classificações de influência ou adoção de argumento;
- ocorrências com problemas de OCR ou contexto incompleto.

### Etapa 8 — Agregar sem perder a granularidade

Os resultados poderão ser resumidos por audiência, acórdão, voto ou participante. Entretanto, a tabela de ocorrências deverá ser preservada como base auditável.

Um resumo poderá afirmar, por exemplo, que uma pessoa aparece cinco vezes no acórdão, sendo duas ocorrências ligadas à audiência, duas relacionadas a outra atuação processual e uma indeterminada.

## 10. Construção da lista relacional e das variantes de busca

### 10.1. Extração inicial dos participantes

As notas taquigráficas e transcrições de cada audiência foram processadas para localizar blocos nominais e relações entre pessoa, instituição e qualificação. A extração combinou diferentes métodos, conforme a estrutura do documento:

- leitura do texto nativo de PDFs e páginas HTML;
- reconhecimento óptico de caracteres nos documentos digitalizados;
- identificação de cabeçalhos de fala nas transcrições e notas taquigráficas;
- OCR local dos documentos taquigráficos sem camada textual, com conservação do número da página;
- complementação manual curada somente quando a própria transcrição ou nota registra a pessoa, a instituição, a substituição ou a grafia alternativa, mas sua estrutura impede extração relacional suficientemente segura.

Os complementos manuais estão registrados em `resultados/complementos_participantes_manuais.csv`. A base conserva, para cada registro, os métodos empregados, os rótulos e arquivos das fontes, as páginas e um exemplo da evidência, de modo que a origem de cada inclusão possa ser auditada.

### 10.2. Limpeza e filtros de elegibilidade

A lista inicial continha, além de participantes, ruídos de OCR, fragmentos de cabeçalhos, qualificações profissionais, termos processuais e nomes mencionados apenas em bibliografia ou legislação. A limpeza não foi realizada por uma única lista genérica de palavras proibidas. As exclusões foram separadas por motivo no código, permitindo distinguir:

- `TERMOS_PROCESSUAIS`: classes processuais e expressões como ADI, ADPF, acórdão, relator, requerente e *amicus curiae*;
- `QUALIFICACOES_SEM_NOME`: funções ou qualificações isoladas, como membro, expositor, representante, advogado ou promotor de justiça;
- `FRAGMENTOS_OCR`: trechos truncados ou combinações textuais sem identidade autônoma;
- `INSTITUICOES_COMO_PESSOA`: entidades que foram incorretamente capturadas no campo de pessoa.

Essa separação é importante porque uma expressão recusada como nome de pessoa pode ser válida em outro campo. Fundo Amazônia, Povo Guajajara, APA Xingu, CGOPE e World Intellectual Property Organization, por exemplo, não são pessoas, mas podem constituir instituições legítimas quando a fonte comprovar sua participação. Do mesmo modo, uma ocorrência da WIPO encontrada apenas em referência bibliográfica foi descartada por ausência de evidência de participação, e não pelo nome da instituição em si.

Foram adotadas ainda as seguintes regras:

- candidatos provenientes apenas de relação de habilitados, edital, convocação, cronograma, programação ou documento complementar foram excluídos com o motivo `fonte_fora_do_escopo_de_presenca`;
- ministros do STF que presidiram, conduziram ou intervieram na audiência foram excluídos da lista de participantes usada na análise;
- falas do cerimonial ou do mestre de cerimônias também foram excluídas;
- ministros de Estado, como o Ministro da Saúde, foram mantidos, pois a exclusão alcança apenas integrantes do STF e funções cerimoniais;
- nomes ou instituições mencionados somente em bibliografia, legislação ou descrição temática foram descartados quando não havia outra evidência de participação;
- toda exclusão automática relevante foi registrada com seu motivo em `resultados/participantes_descartes_limpeza.csv`.

### 10.3. Classificação relacional e elaboração da tabela

A unidade da tabela de participantes passou a ser a relação observada entre pessoa e instituição na audiência, e não uma lista independente de termos. Sempre que a fonte permitiu, pessoa e instituição foram preservadas na mesma linha. Uma entrada como “AUGUSTO CANIZELLA CHAGAS (PRESIDENTE DA UNE)”, portanto, gera uma relação em que a pessoa é Augusto Canizella Chagas e a instituição é UNE; ambos dão origem a termos próprios no arquivo de busca.

Qualificações sem instituição — por exemplo, advogado, professor, pesquisador ou ministro de Estado — foram armazenadas em coluna própria e não tratadas como instituição. A classificação de cada linha obedece a três categorias:

- `pessoa_com_instituicao`: pessoa identificada e vinculada a uma instituição;
- `pessoa_sem_instituicao`: pessoa identificada, mas sem instituição comprovada, podendo haver apenas qualificação;
- `instituicao_sem_pessoa`: instituição cuja participação foi documentada sem a identificação segura de uma pessoa.

A versão atual de `resultados/participantes_relacional_limpo.csv` contém 405 registros distribuídos da seguinte forma:

| Classificação | Registros |
|---|---:|
| Pessoa com instituição | 259 |
| Pessoa sem instituição | 146 |
| Instituição sem pessoa | 0 |
| **Total** | **405** |

A tabela relacional possui os campos `numero_audiencia`, `classificacao`, `pessoa`, `instituicao`, `qualificacao`, `quantidade_evidencias`, `metodos_extracao`, `rotulos_fontes`, `arquivos_fontes`, `paginas_fontes` e `evidencia_exemplo`. A planilha correspondente está em `outputs/participantes_relacional_limpo_20260822/participantes_audiencias_lista_relacional_limpa.xlsx`.

### 10.4. Deduplicação de pessoas e relações institucionais

Para evitar que a mesma pessoa fosse pesquisada repetidamente na mesma audiência, os nomes foram comparados em forma normalizada, desconsiderando diferenças de caixa, acentuação, apóstrofos, hífens e pontuação. Grafias abreviadas somente foram consolidadas quando havia compatibilidade entre os nomes e apoio da instituição ou das demais evidências. Assim, por exemplo, “ANA LUIZA D'ÁVILA VIANA” e “Ana Luiza D’Ávila Viana” são tratadas como a mesma pessoa; “Paulo Sérgio de Marco Leal” e “PAULO SÉRGIO LEAL” também podem ser unificados quando ambos estão associados à FEPLANA.

Quando a mesma pessoa apareceu ligada a mais de uma instituição na mesma audiência, foi conservada somente a primeira associação institucional encontrada na ordem das notas ou transcrições. As demais relações institucionais foram removidas para fins da lista operacional, sem criar registros nominais duplicados. Após essa etapa, a base contém 405 registros com pessoa identificada e não há repetição nominal exata dentro da mesma audiência.

Essa regra simplifica a busca nominal e impede a contagem artificial de uma pessoa como vários participantes. Ela não pretende afirmar que a pessoa representou apenas uma instituição historicamente; registra apenas qual relação foi selecionada para a tabela operacional desta pesquisa.

### 10.5. Elaboração das variantes

As variantes foram geradas pelo programa `gerar_variantes_busca.py` a partir da lista relacional limpa. O arquivo completo `resultados/termos_busca_acordaos.csv` contém 1.401 termos. Destes, 1.091 compõem o arquivo operacional `resultados/termos_busca_acordaos_ativos.csv`, enquanto 310 permanecem inativos para busca automática por exigirem revisão ou apresentarem maior risco de falso positivo.

Foram adotadas as seguintes regras para nomes de pessoas:

- o nome completo é sempre incluído como variante ativa;
- podem ser geradas formas sem iniciais ou sem sufixos como Filho, Neto e Júnior;
- podem ser geradas combinações formadas pelos dois primeiros nomes e o último sobrenome ou pelo primeiro nome e os dois últimos sobrenomes;
- a combinação reduzida a primeiro nome e último sobrenome permanece, por padrão, inativa e destinada à revisão, devido ao maior risco de homônimos.

Para instituições:

- a denominação completa é sempre incluída como variante ativa;
- podem ser geradas formas sem a sigla explicitada entre parênteses e sem sufixos societários, como Ltda. ou S.A.;
- somente siglas expressamente presentes na fonte são utilizadas, sem criação automática de novos acrônimos;
- siglas de duas letras permanecem inativas para revisão; siglas de três letras podem ser ativadas, mas recebem indicação de maior risco.

Além das variantes nominais e institucionais, foram criados dois termos globais — “audiência pública” e “audiências públicas” — sem número de audiência, para aplicação a todo o conjunto de acórdãos. Qualificações profissionais são mantidas apenas como contexto e não geram termos de busca.

### 10.6. Normalização, colisões e arquivo operacional

Cada variante possui uma forma de busca e uma forma normalizada. A normalização aplica decomposição Unicode, conversão para minúsculas, remoção de acentos, substituição da pontuação por espaços e redução de espaços sucessivos. A busca nos acórdãos deverá aplicar a mesma transformação ao texto da página e procurar a sequência normalizada como substring. O trecho original, contudo, deverá ser conservado como evidência.

Foram também verificadas colisões, isto é, situações em que duas linhas da mesma audiência geravam o mesmo `termo_normalizado`. O arquivo operacional admite no máximo uma linha para cada par formado por audiência e termo normalizado. Quando existe uma variante segura compartilhada, ela é mantida uma única vez; duplicatas e variantes ambíguas permanecem inativas. As quatro linhas em colisão auditadas estão registradas em `resultados/variantes_busca_colisoes.csv`.

Não há nomes completos nem denominações institucionais completas inativos na versão atual. A redução afeta somente variantes potencialmente ambíguas ou redundantes.

O arquivo de variantes contém os campos `numero_audiencia`, `alvo_id`, `tipo_alvo`, `pessoa`, `instituicao`, `qualificacao`, `termo_canonico`, `termo_busca`, `termo_normalizado`, `tipo_variante`, `origem_variante`, `prioridade`, `risco_falso_positivo`, `usar_na_busca` e `observacao`. Os tipos de alvo são `audiencia_publica`, `pessoa` e `instituicao`. A versão em planilha está em `outputs/variantes_busca_acordaos_20260822/variantes_busca_acordaos.xlsx`.

Na aplicação aos acórdãos, termos de pessoa e instituição devem ser pesquisados exclusivamente nos processos vinculados à audiência indicada na linha. Os dois termos globais são a única exceção. A identificação do alvo, o termo canônico, a variante efetivamente encontrada, a página e o contexto deverão acompanhar cada ocorrência recuperada.

## 11. Estrutura mínima dos resultados

A tabela principal de ocorrências deverá conter, sempre que disponível:

| Campo | Descrição |
|---|---|
| `ocorrencia_id` | identificador único da ocorrência |
| `numero_audiencia` | identificador da audiência pública |
| `processo` | classe e número do processo |
| `ano` | ano do julgamento do acórdão |
| `arquivo_acordao` | arquivo analisado |
| `pagina_acordao` | página do PDF |
| `pagina_documento` | número de página impresso no acórdão, quando recuperável |
| `ministro` | ministro responsável pela passagem, quando identificável |
| `ministro_metodo` | forma pela qual a autoria da passagem foi identificada |
| `local_tipo` | local analítico simplificado: Relatório, Voto do Relator ou Voto |
| `local_titulo` | cabeçalho específico encontrado no acórdão |
| `local_no_acordao` | uma das três categorias simplificadas de local |
| `frase` | frase que define a unidade da ocorrência |
| `trecho_acordao` | parágrafo completo no qual o alvo foi localizado |
| `contexto_acordao` | contexto ampliado usado na decisão |
| `alvo_id` | identificador estável do alvo que originou a busca |
| `tipo_alvo` | audiência pública, pessoa ou instituição; pode reunir mais de um tipo separado por ` | ` |
| `pessoa_id` | identificador do participante, quando aplicável |
| `pessoa_mencionada` | nome encontrado ou atribuído |
| `instituicao_mencionada` | instituição encontrada ou atribuída, quando aplicável |
| `termo_canonico` | forma principal de cada nome, instituição ou expressão; múltiplos alvos aparecem separados por ` | ` |
| `termo_busca` | variante que recuperou a ocorrência |
| `termo_normalizado` | forma normalizada usada na comparação |
| `quantidade_mencoes_na_frase` | quantidade total de menções recuperadas na frase consolidada |
| `quantidade_alvos_na_frase` | quantidade de alvos canônicos distintos reunidos na frase |
| `mencao_coletiva` | indicação de referência não individualizada |
| `vinculo_audiencia` | explícito, implícito comprovável, sem vínculo demonstrável ou indeterminado |
| `tipo_uso` | forma de utilização do conteúdo no acórdão |
| `arquivo_fonte_audiencia` | documento usado na comparação |
| `pagina_fonte_audiencia` | página da evidência na audiência |
| `trecho_fonte_audiencia` | passagem correspondente |
| `metodo_recuperacao` | termo, nome, variante, instituição, similaridade etc. |
| `metodo_classificacao` | regra, modelo, revisão humana ou combinação |
| `regra_acionada` | regra determinística aplicada, se houver |
| `confianca` | medida auxiliar de confiança |
| `status_revisao` | um dos cinco status definidos na seção 7.6 |
| `regra_decisao` | código da regra automática que determinou ou encaminhou o status |
| `justificativa` | razão sucinta da classificação |
| `versao_metodo` | versão metodológica utilizada |
| `versao_lista_participantes` | versão da lista usada na execução |

A confiança não substitui a evidência nem deve ser interpretada automaticamente como probabilidade estatística, salvo se o procedimento vier a ser calibrado especificamente para isso.

## 12. Regras de decisão e cautelas

1. Toda ocorrência deve conservar a passagem original e a página.
2. O nome de um participante, isoladamente, não constitui evidência de vínculo.
3. O mesmo participante pode receber classificações diferentes em ocorrências diferentes.
4. Referências coletivas à audiência devem ser registradas mesmo sem nomes.
5. Argumentos semelhantes só configuram vínculo implícito quando a correspondência for específica e documentável.
6. Não se deve confundir citação, adoção, crítica e rejeição de um argumento.
7. Ausência de ocorrência recuperada não prova ausência de menção, especialmente em PDFs com OCR deficiente.
8. Casos duvidosos devem permanecer indeterminados até revisão.
9. Resultados negativos também devem ser conservados quando forem necessários para demonstrar que uma menção nominal foi examinada e descartada.
10. Nenhuma classificação produzida automaticamente deve perder a indicação do método, da versão e das fontes utilizadas.

> **Compatibilidade dos resultados anteriores.** As execuções de busca nos acórdãos realizadas antes da versão 0.7 utilizaram uma lista de participantes mais ampla. Seus resultados permanecem como registro histórico, mas não devem ser usados na análise substantiva sem nova execução com a lista e as variantes regeneradas sob o critério exclusivo de notas taquigráficas e transcrições.

## 13. Validação do método

Antes da análise integral, deverá ser construída uma amostra de validação manual com diversidade de:

- audiências e temas;
- ministros e estilos de redação;
- tipos de documento e qualidade de OCR;
- menções explícitas, implícitas, negativas e indeterminadas;
- participantes com múltiplos papéis no processo;
- referências coletivas sem identificação nominal.

A avaliação deve medir separadamente:

- capacidade de recuperar ocorrências relevantes;
- precisão da classificação do vínculo;
- desempenho em vínculos explícitos e implícitos;
- frequência de falsos positivos causados por outros papéis processuais;
- frequência de menções coletivas não recuperadas;
- concordância entre revisores humanos, quando houver mais de um.

Para evitar resultados excessivamente otimistas, a validação deve separar acórdãos inteiros entre desenvolvimento e teste. Ocorrências do mesmo acórdão não devem ser distribuídas entre os dois conjuntos quando isso puder causar vazamento de contexto.

### 13.1. Piloto executado em cinco acórdãos

A primeira execução de validação foi feita em cinco acórdãos escolhidos intencionalmente para variar ano, extensão do documento e quantidade de participantes levantados. Quando uma audiência estava vinculada a mais de um acórdão, foi selecionado apenas um deles nesta etapa, evitando que uma audiência conjunta dominasse a amostra.

| Audiência | Processo | Ano do julgamento | Participantes na lista | Páginas do PDF | Razão da escolha |
|---:|---|---:|---:|---:|---|
| 2 | ADPF 101 | 2009 | 4 | 278 | poucos participantes e acórdão antigo |
| 7 | ADI 3937 | 2017 | 3 | 284 | menor lista de participantes da amostra |
| 18 | ADI 5072 | 2020 | 13 | quantidade intermediária de participantes |
| 30 | ADPF 708 | 2022 | 40 | muitos participantes e acórdão curto |
| 38 | RE 1037396 | 2025 | 55 | muitos participantes e acórdão muito longo, com vários votos |

Na versão `0.5.1-piloto-final` do programa, a busca recuperou 1.204 ocorrências candidatas. Após as novas regras, 79 menções expressas à audiência pesquisada receberam o status `Parte do corpus - automático`, 808 ocorrências receberam `Excluído do corpus - automático` e 317 permaneceram `pendente`. Entre as exclusões automáticas, 796 decorreram da presença de *amicus curiae* ou expressão equivalente no mesmo parágrafo, 8 da qualidade de parte ou terceiro, 2 de enumeração de peça e petição e 2 de referência expressa a outra audiência.

Entre as 317 pendências há 13 expressões de audiência pública cujo escopo ainda não foi determinado e 304 ocorrências nominais ou institucionais. Em 284 dessas 304 ocorrências, o programa anexou uma passagem candidata de transcrição ou nota oficial para comparação humana.

Esses números medem recuperação e triagem, não influência da audiência. Eles não devem ser apresentados como quantidade final de argumentos aproveitados pelo STF antes da revisão das ocorrências.

O principal caso de controle negativo surgiu no RE 1037396. As páginas 18 e 259 do PDF contêm referências a audiências públicas ouvidas durante o debate legislativo do Marco Civil da Internet. Embora a expressão literal coincida com o termo global de busca, essas ocorrências não dizem respeito à audiência pública do STF vinculada ao processo e receberam o status `Excluído do corpus - automático`. O caso demonstra por que a expressão literal, isoladamente, não pode gerar resultado positivo.

Na página 965 do mesmo acórdão, a enumeração de IBDCivil, CEPI/FGV, ABERT, EDUCAFRO, Instituto Alana, IDV, Ministério Público de São Paulo e SIGILO, acompanhada de números de peça e petição, foi excluída automaticamente. A descrição da audiência pública localizada no parágrafo seguinte permaneceu no corpus. A inspeção visual da página confirmou que se tratava de unidades paragráficas distintas.

Os arquivos desta versão do piloto são produzidos em `resultados/piloto_mencoes_audiencias_final/`. O arquivo canônico `ocorrencias_classificadas.csv` conserva todas as ocorrências, inclusive as inclusões automáticas, as exclusões automáticas e as pendências, além dos campos técnicos necessários à auditoria. O arquivo `revisao_pendente.csv` é um subconjunto operacional e não substitui o arquivo canônico.

A planilha foi reduzida a três páginas: `Ocorrências`, que é a página inicial e reúne todas as linhas e classificações; `Resumo`, com totais por audiência e status; e `Dicionário`, que documenta todas as colunas exibidas, os cinco status e cada código de regra. A página central começa diretamente na linha de cabeçalho, sem título ou subtítulo, e apresenta somente 14 colunas essenciais. O CSV completo conserva campos técnicos adicionais para auditoria.

### 13.2. Operacionalização das execuções

Durante o refinamento e a revisão, as execuções deverão ser feitas preferencialmente em lotes informados por número de audiência. O parâmetro `--audiencias` seleciona todas as ações e todos os acórdãos mapeados para cada audiência pedida, evitando que um processo associado seja omitido inadvertidamente. Por exemplo:

```bash
.venv/bin/python analisar_mencoes_audiencias.py \
  --audiencias 2 7 18 30 38 \
  --saida resultados/lote_audiencias_02_07_18_30_38
```

O parâmetro `--acordaos` fica reservado a diagnósticos pontuais em arquivos específicos. Depois de estabilizadas a lista de participantes e as regras de classificação, a rodada integral deverá ser executada uma única vez com:

```bash
.venv/bin/python analisar_mencoes_audiencias.py \
  --todos \
  --saida resultados/analise_integral
```

Essa estratégia combina controle durante a revisão com cobertura integral na produção final. O manifesto de cada execução registra o modo usado, as audiências solicitadas, os arquivos efetivamente analisados e a versão do método.

O CSV canônico representa o resultado produzido pelo programa no momento da execução. Alterações manuais feitas posteriormente na planilha não são sincronizadas automaticamente com esse CSV. Antes da constituição do corpus definitivo, será necessário consolidar os status revisados em um novo CSV versionado; somente as linhas com `Parte do corpus - automático` ou `Parte do corpus` integrarão o corpus analítico.

### 13.3. Execução integral do corpus disponível

A versão `0.6.0-corpus-integral` foi executada em 22 de agosto de 2026 com o parâmetro `--todos`. A rodada cobriu os 50 PDFs existentes em `acordaos/`, todos com metadados válidos, distribuídos por 31 audiências públicas. Naquele resultado, os cinco acórdãos incidentais vinculados à audiência 4 foram preservados no resumo, mas apareceram sem ocorrências. A investigação posterior demonstrou que esse zero era um falso negativo causado pela ausência de camada textual útil; os números desta subseção permanecem como registro histórico e foram substituídos, para uso corrente, pela consolidação descrita na subseção 13.4.

A execução recuperou 5.744 ocorrências, classificadas da seguinte forma:

| Status automático | Ocorrências |
|---|---:|
| Parte do corpus - automático | 480 |
| Excluído do corpus - automático | 2.085 |
| pendente | 3.179 |
| **Total** | **5.744** |

As 2.085 exclusões automáticas compreendem 1.948 ocorrências de *amicus curiae* ou equivalente, 64 referências à qualidade de terceiro, 17 referências à qualidade de parte, 4 enumerações de peça e petição, 46 menções expressas a audiência de outro órgão ou procedimento e 6 alvos nominais localizados no mesmo parágrafo de referência a outra audiência.

Entre as 3.179 pendências, 672 são expressões de audiência pública cujo escopo não foi determinado automaticamente; 149 reúnem alvo e audiência pesquisada no mesmo parágrafo; 112 têm audiência em parágrafo vizinho; 37 reúnem alvo e audiência de escopo incerto; e 2.209 são candidatos a vínculo implícito. O programa anexou passagem candidata de transcrição ou nota oficial a 2.369 pendências, para apoiar a comparação humana.

Quanto ao local no acórdão, foram registradas 783 ocorrências em `Relatório`, 2.142 em `Voto do Relator` e 2.819 em `Voto`. Esses totais descrevem a distribuição da triagem e não devem ser interpretados como medida de influência antes da revisão das pendências.

Os produtos canônicos da rodada integral são:

- `resultados/analise_integral/ocorrencias_classificadas.csv`: todas as 5.744 ocorrências e seus campos de auditoria;
- `resultados/analise_integral/revisao_pendente.csv`: subconjunto das 3.179 pendências;
- `resultados/analise_integral/pacotes_revisao.jsonl`: um pacote estruturado para cada pendência;
- `resultados/analise_integral/resumo_execucao.csv`: uma linha para cada um dos 50 acórdãos, inclusive aqueles sem ocorrência;
- `resultados/analise_integral/manifesto_execucao.json`: versão, parâmetros, insumos, audiências e arquivos analisados;
- `outputs/analise_integral_20260822/analise_integral_acordaos.xlsx`: planilha com as páginas `Ocorrências`, `Resumo` e `Dicionário`.

Foram verificados a unicidade dos 5.744 identificadores, a presença dos campos obrigatórios, a igualdade entre os 3.179 pacotes JSONL e as linhas pendentes do CSV, a conciliação dos totais por status e por acórdão e a ausência de erros de fórmula na planilha exportada.

### 13.4. Reexecução das audiências 3 e 4 e consolidação 0.6.1

Em 22 de agosto de 2026, as audiências 3 e 4 foram reexecutadas isoladamente com a versão `0.6.1-ocr-atualizacao-ap3-ap4` e depois incorporadas aos produtos canônicos em `resultados/analise_integral/`. A consolidação substituiu somente as linhas dos seis acórdãos reprocessados, preservando as outras 44 linhas de resumo e as ocorrências das demais audiências. O campo `versao_metodo` conserva essa história por ocorrência.

Na audiência 3, a lista ativa passou de 4 para 93 termos, compostos por 58 pessoas, 33 instituições e 2 expressões globais. A ADPF 54 passou de 95 para 305 ocorrências: 55 `Parte do corpus - automático`, 13 `Excluído do corpus - automático` e 237 `pendente`.

Na audiência 4, os cinco PDFs tinham em média menos de sete caracteres nativos por página. O OCR recuperou 150 ocorrências, distribuídas da seguinte forma:

| Processo | Ocorrências | Parte - automático | Excluído - automático | Pendente |
|---|---:|---:|---:|---:|
| SS 2361 | 26 | 12 | 0 | 14 |
| SS 2944 | 27 | 11 | 0 | 16 |
| SS 3345 | 31 | 11 | 0 | 20 |
| SS 3355 | 34 | 11 | 1 | 22 |
| STA 278 | 32 | 12 | 0 | 20 |
| **Total** | **150** | **57** | **1** | **92** |

A base consolidada passou a conter 6.104 ocorrências: 537 `Parte do corpus - automático`, 2.095 `Excluído do corpus - automático` e 3.472 `pendente`. Dessas linhas, 5.954 vieram da camada textual nativa e 150 de `OCR Apple Vision`. A distribuição por local no acórdão é 898 em `Relatório`, 2.221 em `Voto do Relator` e 2.985 em `Voto`.

Foram novamente verificados a unicidade dos 6.104 identificadores, a presença dos campos obrigatórios, a igualdade entre as 3.472 linhas pendentes e os pacotes JSONL, a soma das 50 linhas do resumo, os totais por status e a ausência de erros de fórmula após reabrir a planilha XLSX. O programa possui 19 testes automatizados aprovados, incluindo os controles de densidade textual, confusões conservadoras de OCR e identificação de ministro em texto reconhecido.

### 13.5. Reexecução integral com deduplicação, referências e papéis processuais

Em 29 de agosto de 2026, todo o corpus foi reexecutado com a versão `0.7.0-deduplicacao-referencias-partes-paragrafos`, após a regeneração da lista de participantes e dos termos ativos descrita na versão 0.7. A execução com `--todos` cobriu novamente 50 PDFs de 31 audiências e substituiu os produtos canônicos em `resultados/analise_integral/`.

A rodada produziu 3.847 ocorrências contextualizadas:

| Status automático | Ocorrências |
|---|---:|
| Parte do corpus - automático | 500 |
| Excluído do corpus - automático | 1.026 |
| pendente | 2.321 |
| **Total** | **3.847** |

Foram consolidadas 239 repetições do mesmo alvo canônico dentro do mesmo parágrafo. O CSV preserva a contagem em `quantidade_mencoes_no_paragrafo`; depois da consolidação não restaram duplicatas pela chave formada por arquivo, página, tipo de alvo, termo canônico e parágrafo completo.

As 1.026 exclusões automáticas compreendem 662 ocorrências de *amicus curiae* ou equivalente, 266 de advogado ou representante processual, 47 de requerente ou responsável por requerer/protocolar a ação, 8 referências bibliográficas, 2 enumerações de peça e petição, 1 terceiro e 40 referências a audiência diversa. Essas regras são de triagem e permanecem reversíveis na planilha: a linha, a página, o parágrafo completo, o código e a justificativa continuam disponíveis para auditoria.

Quanto à extração, 3.701 linhas vieram da camada textual nativa e 146 de `OCR Apple Vision`. Quanto ao local, foram registradas 667 ocorrências em `Relatório`, 1.354 em `Voto do Relator` e 1.826 em `Voto`.

Os totais desta rodada não são diretamente comparáveis aos 6.104 registros da consolidação 0.6.1. Além das 239 repetições consolidadas e das novas exclusões, a lista operacional de participantes foi restringida e os termos ativos foram regenerados a partir de notas taquigráficas e transcrições. Portanto, a redução decorre principalmente da mudança dos insumos de busca, e não deve ser interpretada como simples efeito das regras de deduplicação.

Os três acórdãos vinculados à audiência 44 ficaram sem ocorrência. Foi verificado que os termos atualmente ativos dessa audiência — duas pessoas, uma instituição, suas variantes e as expressões globais — não aparecem nos PDFs. Trata-se, portanto, de resultado da lista operacional atual, e não de falha de extração ou de uma exclusão automática.

As validações finais confirmaram 3.847 identificadores únicos, ausência de campos obrigatórios vazios, páginas dentro dos limites de cada PDF, igualdade entre as 2.321 pendências do CSV e os 2.321 pacotes JSONL, conciliação das 50 linhas do resumo e ausência de erros de fórmula após reabrir a planilha. A suíte contém 31 testes automatizados aprovados, inclusive casos de repetição no mesmo parágrafo, ocorrências em parágrafos diferentes, referência bibliográfica, dispositivo legal, requerente, representante processual e preservação do parágrafo integral.

### 13.6. Unidade por frase e consolidação de múltiplos alvos

Em 31 de agosto de 2026, o corpus integral foi reexecutado com a versão `0.8.0-unidade-frase-multiplos-alvos`. A mudança respondeu a ocorrências nas quais pessoa e instituição eram recuperadas como alvos diferentes na mesma frase e, por isso, apareciam em linhas separadas. A busca continua sendo feita por todos os termos, mas a saída passou a ter uma linha por frase dentro de seu parágrafo contextual.

O caso usado como regressão foi a passagem da ADPF 54 que menciona conjuntamente a Advocacia-Geral da União e Evandro Costa Gama. As antigas linhas `AP03-AP_03_ADPF_054-00071` e `AP03-AP_03_ADPF_054-00072` foram substituídas por uma única ocorrência. O campo de alvos contém `Advocacia-Geral da União | Evandro Costa Gama`, enquanto a frase, a página e o parágrafo completo permanecem disponíveis.

A rodada produziu os seguintes totais:

| Status automático | Passagens |
|---|---:|
| Parte do corpus - automático | 529 |
| Excluído do corpus - automático | 838 |
| pendente | 2.088 |
| **Total** | **3.455** |

Em 341 frases foi recuperado mais de um alvo. A consolidação reuniu 526 alvos que anteriormente gerariam linhas adicionais e preservou 105 repetições do mesmo alvo dentro da frase sem multiplicar as linhas. O mesmo alvo em frases distintas voltou a gerar ocorrências distintas; portanto, essa contagem não deve ser comparada diretamente com a consolidação por parágrafo da versão 0.7.0.

Quanto à extração, 3.312 passagens vieram da camada textual nativa e 143 de `OCR Apple Vision`. Quanto ao local, foram registradas 471 ocorrências em `Relatório`, 1.262 em `Voto do Relator` e 1.722 em `Voto`.

As verificações confirmaram 3.455 identificadores únicos, ausência de duplicatas pela chave formada por arquivo, página, frase e parágrafo completo, ausência de campos obrigatórios vazios, páginas dentro dos limites dos PDFs e igualdade entre as 2.088 pendências do CSV e os 2.088 pacotes JSONL. A planilha foi reaberta após a exportação, apresentou os mesmos totais e não contém erros de fórmula. A suíte passou a ter 35 testes automatizados, incluindo pessoa e instituição na mesma frase, abreviação `Dr.` sem divisão indevida, repetições na mesma frase e camadas textuais repetidas.

## 14. Uso de código e modelos de linguagem

O procedimento previsto é híbrido:

- **código determinístico** para extração, normalização, busca ampla, regras transparentes, organização e rastreabilidade;
- **modelo de linguagem** para interpretar contexto e comparar passagens nos casos em que regras literais forem insuficientes;
- **revisão humana** para decisões metodologicamente sensíveis ou incertas.

Após a versão 0.8, foram realizados ajuste local de modelo e experimentos de classificação por API. Não se treinou um modelo do zero. O ajuste local de parâmetros e a classificação por instruções de um modelo remoto são estratégias distintas e não devem ser apresentados como um único treinamento.

### 14.1. Escolhas de incorporação consolidadas

A avaliação semântica utiliza `Incorporar`, `Excluir` e, quando a evidência é insuficiente, `Indeterminado`. Nas planilhas, `Conferir contexto` significa revisão pendente: não confirma o rótulo anterior nem equivale a exclusão. Esses valores não substituem retroativamente os cinco status históricos da seção 7.6.

As decisões adotadas pelo pesquisador foram:

1. **Audiência pesquisada:** incorporar referências à realização, organização, participação ou contribuições da audiência vinculada aos processos estudados. Excluir referências a outras audiências, a atos processuais genéricos e a audiências previstas para implementação normativa que não correspondam ao evento pesquisado. Não excluir toda menção ao CNJ: importa a função da passagem e a audiência a que ela se refere.
2. **Partes:** excluir contribuições de requerentes e requeridos, mesmo quando apresentadas na audiência. A exclusão depende da posição processual demonstrada, não da natureza da instituição. Ser autoridade, advogado ou integrante do sistema de justiça não substitui essa verificação. Casos de representação e citação mediada podem exigir exame individual.
3. **Terceiros e amici curiae:** continuam elegíveis quando a ocorrência tiver vínculo com a audiência. Admissão processual não comprova presença no evento, mas também não autoriza excluir automaticamente todas as contribuições de uma entidade.
4. **Listas de entidades:** incorporar listas de participantes da audiência quando essa origem estiver identificada. Distingui-las de listas de habilitação processual. Números de processos, documentos, peças ou petições são indícios para conferir a origem, não motivos autônomos de exclusão. A introdução da lista, inclusive na página anterior, pode ser decisiva.
5. **Bibliografia:** incorporar livros e artigos de participantes confirmados, mesmo sem referência expressa à audiência. Essa escolha vale para todos os participantes elegíveis, não apenas Édis Milaré. Não se presume como fato a identidade entre posições escrita e oral, nem influência causal do evento. Coincidência nominal não basta para confirmar identidade ou participação.
6. **Atuação legislativa:** a exceção bibliográfica não abrange automaticamente a mera autoria de projeto de lei. As referências a projetos atribuídos a Sarney Filho, sem retomada de contribuição da audiência, foram mantidas como exclusões.
7. **Notas e documentos citados:** relacionar a nota ao seu próprio chamado e distinguir depoimentos da audiência de petições ou outros documentos. O uso argumentativo de um documento não basta, sozinho, para torná-lo elegível. A nota BRASILCON na AP 38 foi excluída após o pesquisador reconhecer que se tratava de lista de *amici curiae*, não da nota argumentativa inicialmente considerada.

A aceitação individual de uma referência a relatório do CNJ não estabeleceu uma regra geral para relatórios institucionais. Nas instruções v6.1, a extensão passou a abranger livros, artigos, pesquisas e outras manifestações intelectuais de participantes confirmados, exigindo retomada identificável de posição, conclusão, explicação ou resultado substantivo. Uma referência meramente nominal, biográfica ou histórica não basta por essa via. Isso não afeta a inclusão de menções à participação na própria audiência como Contexto. O contraste entre as referências a FHC nas páginas 182 e 202 motivou a precisão: exclusão da menção pessoal desconexa e inclusão da atribuição de contribuição substantiva. A presunção metodológica não prova identidade com a fala oral nem autoriza atribuir ao autor posição política mais ampla do que aquela sustentada pelo trecho. Na dúvida, o programa deve encaminhar para conferência, sem inventar participação ou contexto.

Não foi acrescentada uma subcategoria manual obrigatória de vínculo. Texto, alvo, fonte, página e registro das decisões sustentam a auditoria. A comprovação de participação continua seguindo a seção 5: uma obra citada não é, por si, prova de presença na audiência. A inclusão bibliográfica é uma via de elegibilidade ao corpus, não deve ser convertida artificialmente em vínculo implícito comprovado com a fala.

### 14.2. Classificação de engajamento e etapas adiadas

Somente as ocorrências incorporadas recebem tipo de engajamento. A tipologia foi reduzida a três categorias, sem subcategorias manuais obrigatórias:

| Código preservado nos programas | Denominação conceitual | Critério |
|---|---|---|
| Contexto | Sem contribuição substantiva | Informa realização, organização ou participação na audiência, sem mobilizar conteúdo substantivo de uma contribuição. |
| Relato | Engajamento descritivo | Reproduz ou sintetiza posições sem relacioná-las à construção do raciocínio para decidir. |
| Argumento | Engajamento argumentativo | Mobiliza a contribuição como premissa, evidência, apoio ou contraponto na discussão ou linha de raciocínio do julgador, mesmo sem adesão explícita. |

O critério é a função da ocorrência contextualizada, não palavras isoladas como “afirmou” ou “concordo”. Uma fala pode conter argumentos e ser apenas relatada pelo julgador. Uma transcrição literal pode, por outro lado, ser utilizada argumentativamente. Estar no voto, fora do relatório ou próximo de uma conclusão é indício, mas não condição suficiente.

Uma referência à mera realização da audiência permanece `Contexto`, inclusive quando utilizada em discussão sobre contraditório. Isso distingue o uso da existência do evento do engajamento com uma contribuição substantiva. O contexto deve esclarecer a menção sem transferir automaticamente à frase a função argumentativa de todo o voto.

As categorias não são uma escala validada de influência crescente. `Argumento` não implica concordância ou acolhimento. Para incorporados cujo tipo não possa ser decidido, admite-se `Indeterminado`; para excluídos, o tipo não se aplica.

A classificação de teor (`Reitera`, `Refuta`, `Convence`) foi adiada. Não foram encontrados exemplos humanos de `Refuta` ou `Convence` nos lotes iniciais revisados, impossibilitando avaliar adequadamente essas classes naquele material. A classificação institucional também ficou fora dos testes correntes. Foram discutidas para etapa posterior Instituições Públicas, Entes Federados, Sistema de Justiça, Acadêmicos, Associações de Classe, Associações Civis e Associações Comerciais, sem subcategorias obrigatórias.

### 14.3. Exemplos humanos e ajuste local

Foram preparados e classificados pelo pesquisador 300 exemplos: 210 de treino, 30 de desenvolvimento e 60 inicialmente reservados para teste. A separação foi por audiência: desenvolvimento na AP 38; reserva nas APs 19 e 35; treino nas APs 1, 3, 4, 5, 8, 12, 14, 15, 18 e 32. O treino continha 90 incorporados: 14 Contexto, 32 Relato e 44 Argumento.

O desenvolvimento continha inicialmente dez incorporados. Uma revisão humana acrescentou uma ocorrência de Contexto, levando o subconjunto de tipo a 11 casos: cinco Contexto, dois Relato e quatro Argumento. Revisões posteriores alteraram novamente esse gabarito. Denominador e versão dos rótulos devem, portanto, acompanhar cada resultado.

O piloto local utilizou Qwen2.5-3B-Instruct quantizado em quatro bits, com adaptadores LoRA via MLX LM. A configuração conjunta de corpus e tipo previa 210 etapas, quatro camadas ajustadas, lote unitário, taxa de aprendizagem de 0,00001 e semente 42. Posteriormente, a tarefa de tipo foi isolada, partindo novamente do modelo-base, com 90 exemplos incorporados e 270 etapas planejadas, equivalentes a três passagens pelos dados.

No teste de tipo isolado, modelo-base e ajustado acertaram três dos 11 exemplos de desenvolvimento. O diagnóstico do ajustado nos próprios 90 exemplos de treino produziu 69 acertos (76,7%): três de 14 Contexto, 24 de 32 Relato e 42 de 44 Argumento. Esse diagnóstico não estima generalização, pois os exemplos haviam sido usados no ajuste. A dificuldade, sobretudo em Contexto, motivou a comparação remota; não demonstra inadequação de modelos locais em geral.

As amostras eram de desenvolvimento e diagnóstico, não amostras probabilísticas de todas as pendências. Passagens semelhantes ou repetidas em acórdãos relacionados foram detectadas, como as duas menções da ANER. Separar audiências reduz vazamento entre conjuntos, mas não torna independentes as ocorrências dentro de cada conjunto.

### 14.4. Uso do Claude e seleção de contexto

Os scripts e registros remotos utilizaram o identificador `claude-sonnet-5`. Não houve fine-tuning do Claude: foram enviados instruções e recortes, sem o gabarito humano, com resposta em JSON. Não foram habilitados ferramentas de busca, consulta autônoma aos PDFs ou raciocínio estendido. O limite de saída era de 500 tokens por caso nos testes de tipo e 200 nos testes conjuntos.

Ter os acórdãos no computador não dá acesso a eles ao modelo. Uma rodada da AP 38 acrescentou duas páginas anteriores e duas posteriores e, para a nota BRASILCON, o parágrafo distante que a referenciava. A ampliação alterou decisões individuais, mas não o total inicial de sete acertos em 11. Como contexto e instruções mudaram conjuntamente, não se isolou o efeito de cada mudança.

Foram identificados recortes interrompidos, notas distantes de seus chamados, metadados imprecisos de ministro/seção e transcrições recuperadas que apenas apresentavam o expositor. Coincidência lexical ou cabeçalho de fala não comprova correspondência substantiva. Selecionar contexto pertinente continua sendo uma etapa a aperfeiçoar, especialmente para listas e documentos citados.

### 14.5. Formato de resposta e definição das métricas

Na primeira rodada remota, quatro respostas foram consideradas inválidas porque o JSON veio envolto em bloco Markdown. A normalização offline passou a aceitar um único bloco externo com JSON e categorias válidas, sem corrigir rótulos nem extrair respostas de prosa arbitrária. O resultado passou de cinco acertos e quatro inválidas para sete acertos e nenhuma inválida. A mesma regra foi aplicada aos modelos locais comparáveis; as saídas brutas e os resultados estritos foram preservados.

As avaliações conjuntas distinguem:

- **concordância de corpus:** comparação de Incorporar/Excluir com a referência humana, contando abstenção como não acerto;
- **classificação completa:** corpus correto e, para incorporados humanos, tipo correto;
- **tipo nos incorporados humanos:** inclui as perdas da etapa de corpus, para não ocultar menções excluídas pelo modelo;
- **tipo condicionado à incorporação por ambos:** diagnóstico complementar, que não representa desempenho completo;
- **resposta inválida:** falha de formato, diferente de abstenção substantiva ou tipo não aplicável.

O campo histórico `invalidas` da rotina de tipo também conta valores ausentes por exclusão do modelo. As 14 “inválidas” de tipo da primeira rodada de 60 casos eram exclusões, não respostas malformadas. Essa nomenclatura deverá ser explicada ou substituída no relato final. Classes sem suporte humano não permitem estimar sensibilidade.

### 14.6. Resultados remotos e custos

Os resultados abaixo correspondem ao gabarito usado em cada execução, salvo a normalização de formato indicada. Não constituem uma série diretamente comparável: amostras, tarefas, instruções e contextos variam.

| Experimento | Casos | Corpus correto | Tipo ou classificação completa | Custo estimado (US$) |
|---|---:|---:|---|---:|
| AP 38, tipo, contexto original | 11 | Não avaliado | Tipo: 7/11 após normalização; originalmente 5/11 | 0,0411 |
| AP 38, tipo, contexto ampliado | 11 | Não avaliado | Tipo: 7/11 | 0,2083 |
| Primeiro lote multiaudiências, tipo | 30 | Não avaliado | Tipo: 19/30 | 0,1245 |
| Primeira rodada reservada, APs 19 e 35 | 60 | 39/60 | Completa: 37/60 | 0,3233 |
| Repetição dos 60 após ajuste de regras | 60 | 56/60 | Completa: 49/60 | 0,3810 |
| Novo lote sem IDs ou menções idênticas já avaliadas pelo Claude | 30 | 24/30 | Completa: 22/30 | 0,1781 |

Os custos são estimativas dos scripts, não comprovantes de faturamento. Usaram tarifas de referência de US$ 2 por milhão de tokens de entrada e US$ 10 por milhão de saída, antes de impostos. As primeiras rodadas exigiam confirmação humana de envio e custo, com bloqueio acima de US$ 0,50 estimado por rodada. Esse teto não foi universal: as execuções posteriores tiveram limites próprios, inclusive autorização expressa para concluir a reavaliação dos 300 acima de US$ 2. Na AP 38, a expansão elevou a entrada de 19.663 para 103.331 tokens, ilustrando o custo de ampliar texto sem ganho global de concordância naquele teste.

### 14.7. Revisão humana e resultados recalculados

As revisões corrigiram anotações individuais e esclareceram critérios ainda instáveis. As decisões foram tomadas pelo pesquisador, com exame de contexto e registro por ID. Não obstante, revisões motivadas por divergências conhecidas podem induzir as decisões; seus resultados recalculados não são validação independente.

Na AP 38, as duas passagens da ANER passaram de Argumento para Relato, e a nota BRASILCON foi excluída. As duas execuções remotas passaram retrospectivamente a nove acertos em dez casos de tipo. Restou apenas um Argumento humano, insuficiente para avaliação estável dessa categoria.

No primeiro lote multiaudiências, oito rótulos de tipo foram alterados e duas ocorrências excluídas, produzindo 27 acertos em 28 casos remanescentes (96,4%). A conferência de Mayana Zatz e Lenise Garcia mostrou transcrições no relatório, apresentando correntes de opinião. Outra passagem do Ministério Público provinha de manifestação processual. A função da ocorrência e a origem da fonte, não só o vocabulário, orientaram a revisão. O percentual recalculado não é melhora do modelo.

Após a primeira rodada reservada, os 60 casos foram revistos em planilha sem rótulos anteriores nem respostas individuais do Claude, incluindo concordâncias e divergências. O pesquisador já conhecia os resultados agregados: houve cegamento às respostas por caso, não cegamento integral nem segundo codificador. Foram mantidas 30 inclusões e 30 exclusões. Nessa fase, explicitaram-se a inclusão bibliográfica de participantes e as exclusões de outras audiências e de simples autoria legislativa.

A repetição desses 60 casos produziu 56 acertos de corpus (93,3%). Posteriormente, o pesquisador aceitou Incorporar para a referência a relatório do CNJ do caso 42, `AP35-AP_35_ADI_6298-00293`, mantendo os casos 36 e 40 como Excluir e 47 como Incorporar. Isso eleva retrospectivamente a concordância de corpus a 57/60 (95%), sem nova inferência. Não se reavaliou o tipo do novo incorporado para calcular uma métrica completa revisada.

O lote v3 reuniu 15 inclusões e 15 exclusões históricas de dez audiências, selecionadas do treino local e ainda não avaliadas pelo Claude por ID ou menção textualmente idêntica. A seleção não exclui toda repetição semântica. Foram 24/30 acertos de corpus e 22/30 completos. As seis divergências de corpus e duas de tipo foram reunidas em planilha. Essa revisão foi posteriormente devolvida e consolidada: 29/30 de corpus e 28/30 completos, com oito divergências revistas e 22 gabaritos preservados. As etapas subsequentes constam da seção 14.10. Entre as questões estão alegações da OAB como requerente, entrevista de participante, contribuição citada por outro interveniente e previsão legal acompanhada da descrição de audiência efetivamente realizada.

### 14.8. Limitações e critérios para o relato final

Os experimentos mostram desacordos decorrentes de critérios e anotações ainda em consolidação, além de limitações do modelo e do contexto. Não autorizam uma taxa única de sucesso para todas as pendências ou substituição integral da revisão humana.

Os testes medem classificação entre candidatos já recuperados, não a recuperação de todas as menções existentes nos acórdãos. Também não estimam concordância entre pesquisadores, pois não houve segundo codificador independente. A reserva de 60 casos não tinha exemplos humanos de Relato; o lote v4 tinha apenas um Contexto entre os incorporados. Essa composição limita comparações por classe.

Para uma validação final, deverão ser congelados critérios e gabarito compatíveis, reservado material não usado para ajustar instruções, assegurado suporte às três classes e considerado o agrupamento por audiência e por passagens semelhantes. O conjunto inicialmente reservado perdeu essa condição após exame, revisão e reutilização. Lotes posteriores provenientes do treino local são diagnósticos adicionais.

A anotação foi simplificada: alvo e frase ao lado da decisão, contexto disponível, opções de resposta e comentários facultativos. Nos testes, o JSON não exigia justificativa extensa. As evidências permanecem nos recortes e documentos; escolhas metodológicas e casos sensíveis são registrados separadamente. Essa prática substitui, nesta fase, a previsão inicial de justificativa obrigatória em cada resposta.

### 14.9. Rastreabilidade dos experimentos

Os registros estão em `outputs/01a02b49-a916-75a0-80da-a7b4fcc952c1/mlx_local/`. Os principais conjuntos são:

- `manifesto.json`, `registros.json`, `config_execucao.json` e `tipo_v3/`: composição, parâmetros e avaliações locais;
- `normalizacao_v1/`: reinterpretação de formato sem nova inferência;
- `claude_tipo_v1/`, `claude_engajamento_v1/`, `claude_multiaudiencias_v1/`: primeiras execuções remotas;
- `revisao_humana_v3/`, `multiaudiencias_revisao_v2/`: gabaritos e métricas derivados da revisão;
- `validacao_reservada_v1/`, `claude_reservado_v1/`, `ajuste_corpus_v2/`, `claude_ajuste_corpus_v2/`: entradas, instruções e resultados dos 60 casos;
- `revisao_cega_corpus_60.xlsx`, `decisoes_corpus_pos_v2.json`: revisão de corpus e decisões posteriores, inclusive caso 42;
- `corpus_novo_lote_v3/`, `claude_novo_lote_v3/`, `revisao_8_casos_novo_lote.xlsx`: lote v3 e planilha de revisão, posteriormente consolidada.

As execuções conservam respostas e métricas, e os manifestos registram hashes dos insumos quando implementados. Uma decisão registrada neste documento ou em arquivo de revisão não deve ser presumida como propagada à planilha anterior, aos dados de treino, aos adaptadores ou ao CSV canônico. A consolidação definitiva exige aplicação explícita por ID, preservando os estados anteriores. Credenciais de API não integram os artefatos científicos e não devem ser publicadas.


### 14.10. Continuidade do desenvolvimento: lotes v4 e v5

O lote v4 continha 30 casos ainda não avaliados pelo Claude por ID ou menção normalizada, oriundos do treino local: 15 exclusões e 15 inclusões históricas (um Contexto, sete Relatos e sete Argumentos). Produziu 29/30 de corpus e 27/30 completos. Após a revisão das três divergências, foram 30/30 de corpus e 28/30 completos; entre os 14 incorporados da referência atualizada, 12 tipos corretos. A nota 77 da ADPF 54 foi interpretada com seu chamado na página PDF 60: embora reproduzisse uma posição, exercia função argumentativa naquele parágrafo. A revisão também aplicou a exclusão de partes a uma inclusão histórica. Os resultados recalculados utilizam as mesmas predições, não uma nova execução.

O lote v5 continha 30 casos, com 19 Argumentos, quatro Relatos e sete exclusões históricas, sem Contexto. A execução produziu 28/30 de corpus e 21/30 completos. A revisão das nove divergências alterou quatro decisões, mantendo 21 gabaritos não revistos nessa etapa: 29/30 de corpus, 25/30 completos e 17/22 tipos corretos entre incorporados. A composição diferente impede interpretar a variação percentual entre lotes como melhora ou piora isolada do modelo.

Essas revisões explicitaram os seguintes critérios nas instruções:
- distinguir reprodução de alegação de parte de retomada própria da contribuição pelo julgador;
- considerar a continuação que retoma comprovadamente o mesmo participante, sem transferir conteúdo de discussão vizinha;
- examinar a nota e seu chamado: nota apenas biográfica permanece Contexto, enquanto nota que sustenta ou identifica uma tese enfrentada pode integrar Argumento, inclusive como contraponto;
- reconhecer resultados e objetivos de pesquisas como conteúdo substantivo, mesmo em enumerações;
- não classificar automaticamente sínteses jornalísticas ou transcrições como Argumento apenas por estarem em um voto;
- exigir contribuição substantiva identificável na extensão a manifestações intelectuais externas à audiência, preservadas as exclusões prioritárias de partes e de mera autoria legislativa.

O custo estimado foi US$ 0,197258 no v4 (94.754 tokens de entrada e 775 de saída) e US$ 0,238606 no v5 (115.308 e 799). Não houve respostas inválidas nessas duas execuções.

### 14.11. Reavaliação dos 300 casos com instruções v6.1

Antes da execução, o gabarito histórico foi conciliado com as decisões humanas acumuladas e com a exclusão de partes, para evitar tratar como erro do modelo uma inclusão incompatível com a regra atual. A conciliação examinou cabeçalhos por processo, sem usar predições como fundamento. Não equiparou automaticamente interessado, advogado ou amicus a parte, nem transferiu condição processual entre ações conexas. Foi registrada uma alteração por identidade textual de fala anteriormente excluída em julgamento conjunto. Quatro casos dependentes de decisão metodológica permaneceram separados das métricas principais.

As 300 entradas foram preservadas. Na comparação inicial, havia 296 casos avaliáveis para corpus e 295 para classificação completa, pois um incorporado não tinha tipo humano definido. Foram 261/296 de corpus (88,2%), 249/295 completos (84,4%) e 101/118 tipos corretos entre incorporados humanos (85,6%). A execução consumiu 1.495.035 tokens de entrada e 7.540 de saída, com custo estimado de US$ 3,06547 e nenhuma resposta inválida.

A planilha de revisão reuniu 51 casos. O pesquisador devolveu o arquivo preenchido em outro computador, que foi preservado como fonte, e resolveu duas pendências adicionais na conversa. A consolidação final de 13/10/2026 registrou 14 alterações e 37 manutenções, sem pendências. Os outros 249 casos não foram revistos nessa etapa, conservando as decisões anteriores.

Com a referência final, as mesmas predições produziram 266/300 de corpus (88,7%), 258/300 completos (86,0%) e 108/122 tipos corretos nos incorporados (88,5%). Trata-se de reavaliação da base de desenvolvimento, incluindo casos usados no refinamento das instruções, e não de validação independente. Não se deve apresentar a revisão das 51 divergências como nova revisão integral e cega dos 300, nem a mudança de métricas como novo treinamento.

### 14.12. Pilotos integrais dos candidatos recuperados em cinco audiências

A etapa seguinte aplicou as mesmas instruções v6.1 em duas rodadas, sem modificá-las entre elas: APs 2 e 13, seguidas das APs 9, 16 e 22. A escolha foi intencional, considerando diversidade temática e viabilidade de revisão integral. Foram incluídos todos os candidatos recuperados pela extração de 31/08/2026 nas audiências escolhidas, inclusive os automaticamente excluídos e pendentes. Os status automáticos não foram usados como gabarito nem enviados para orientar as respostas.

“Integral” designa todos os candidatos daquela extração, não um censo comprovado de todas as menções existentes nos PDFs. Os IDs dos pilotos não constavam das predições anteriores consultadas, mas isso não assegura ausência de semelhanças semânticas. Os modelos receberam frase, alvo, contexto disponível do acórdão, metadados e trecho da audiência quando disponível. Não tiveram consulta autônoma aos documentos completos.

O identificador foi `claude-sonnet-5`, com raciocínio estendido desativado e limite de 200 tokens de saída por ocorrência. O texto das instruções usado na reavaliação dos 300 e nos dois pilotos é idêntico, com SHA-256 `44437f55f69c0c52ee561af71d2db58fb62152d4a0a9b13cfa0b29d1c7bb9ca5`. Não houve fine-tuning do Claude. As decisões abaixo atualizam a referência humana, não os parâmetros do modelo.

As planilhas apresentaram alvo, frase, decisão, corpus final, tipo final e comentário opcional na mesma tabela, além de contexto em aba própria. As opções foram Aceitar Claude, Alterar e Conferir contexto. Todos os 145 casos, incluindo exclusões, receberam revisão. As respostas do modelo estavam visíveis: não houve cegamento nem segundo codificador independente.

#### 14.12.1. Resultados após revisão humana

| AP | Tema / processo | Candidatos | Excluir | Contexto | Relato | Argumento | Corpus correto | Classificação completa |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2 | Pneus / ADPF 101 | 22 | 7 | 6 | 6 | 3 | 21/22 | 21/22 |
| 13 | Biografias / ADI 4815 | 39 | 10 | 11 | 13 | 5 | 36/39 | 33/39 |
| 9 | Campos eletromagnéticos / RE 627189 | 29 | 5 | 10 | 0 | 14 | 29/29 | 29/29 |
| 16 | Diferença de classe no SUS / RE 581488 | 25 | 3 | 9 | 4 | 9 | 23/25 | 22/25 |
| 22 | Direito ao esquecimento / RE 1010606 | 30 | 14 | 8 | 4 | 4 | 24/30 | 24/30 |
| **Total** | **Cinco audiências** | **145** | **39** | **44** | **27** | **35** | **133/145** | **129/145** |

As colunas Excluir, Contexto, Relato e Argumento descrevem a referência humana final; as duas últimas comparam com as predições originais preservadas. A primeira rodada teve 57/61 de corpus (93,4%) e 54/61 completos (88,5%). A segunda teve 76/84 (90,5%) e 75/84 (89,3%), respectivamente. No conjunto, foram 91,7% de concordância de corpus e 89,0% de classificação completa.

Entre os 106 incorporados humanos, houve 43/44 Contextos, 25/27 Relatos e 31/35 Argumentos corretamente incorporados e tipificados. Esses valores são sensibilidades por categoria, não precisão das predições. Incluem as perdas por exclusão indevida.

#### 14.12.2. Decisões e padrões de divergência

Na primeira rodada, foram corrigidos casos de cabeçalhos do IHGB e três Relatos que o pesquisador identificou como Argumentos. Paulo Janissek passou de exclusão do modelo para Incorporar — Relato. Os casos 25 e 61, com o mesmo registro de falas no julgamento, foram confirmados como Excluir na conversa, prevalecendo a decisão sobre a aceitação anterior do caso 25 na planilha. A consolidação de 14/10/2026 preservou o arquivo original. Houve quatro erros de corpus e três erros de tipo, estes de Argumento humano para Relato automático.

Na segunda rodada, o arquivo devolvido continha 73 aceitações, dez alterações e uma pendência. As confirmações finais de 15/10/2026 foram:
- caso 68, `AP22-AP_22_RE_1010606-00014`, página PDF 53: Incorporar — Argumento. A menção “Audiência Pública STF” integra a referência à exposição de Anderson Schreiber mobilizada na sequência do raciocínio;
- caso 69, `AP22-AP_22_RE_1010606-00015`, página PDF 54: Excluir. A contribuição é atribuída ao advogado dos recorrentes; manteve-se a exclusão de partes, mesmo com referência expressa à audiência.

As demais decisões foram preservadas. Os casos 51 e 53 da AP 16 foram incorporados como Contexto e Relato, em oposição às exclusões do modelo; o caso 54 passou de Contexto para Argumento. Na AP 22, seis inclusões indevidas foram excluídas: dois cabeçalhos e quatro registros repetidos de sustentação oral relacionados ao ITS Rio. Isso não estabeleceu exclusão geral de amici, mas aplicação do critério da função da ocorrência.

A segunda rodada terminou sem pendências, com oito divergências de corpus e uma de tipo. O modelo identificou corretamente 26 dos 27 Argumentos humanos, contra cinco de oito na primeira rodada. A diferença descreve esses conjuntos: não houve novo treinamento ou alteração de instruções entre eles. Argumento também não era a menor categoria do treino local inicial (44 de 90 incorporados), e aquele ajuste local não foi transferido ao Claude.

#### 14.12.3. Consumo e limites do relato

| Rodada | Casos | Tokens de entrada | Tokens de saída | Custo estimado (US$) |
|---|---:|---:|---:|---:|
| APs 2 e 13 | 61 | 300.003 | 1.606 | 0,616066 |
| APs 9, 16 e 22 | 84 | 405.765 | 2.168 | 0,833210 |
| **Total dos pilotos** | **145** | **705.768** | **3.774** | **1,449276** |

Não houve respostas inválidas. Os resumos imediatamente posteriores à API eram distribuições de predições, não medidas de acurácia. Os resultados de concordância só foram calculados após a revisão humana. Custos são estimativas pelas tarifas registradas, não comprovantes, e a consolidação das revisões não fez novas chamadas à API.

As cinco audiências constituem uma demonstração do procedimento em conjuntos completos de candidatos e permitem descrever os casos revisados. Não demonstram generalização para todas as audiências, recuperação completa de menções ou concordância entre pesquisadores. Repetições entre páginas permaneceram como ocorrências distintas da extração; a contagem de erros não equivale necessariamente a igual número de problemas textuais independentes.

### 14.13. Fontes locais das atualizações e estado de consolidação

Além dos registros da seção 14.9, os seguintes artefatos, relativos à pasta `mlx_local/` ali indicada, sustentam esta atualização:

- `corpus_novo_lote_v4/revisao_v3.json` e `corpus_novo_lote_v5/revisao_v4.json`: revisões dos lotes v3 e v4;
- `claude_novo_lote_v4/metricas.json`, `claude_novo_lote_v5/metricas.json` e `revisao_humana_lote_v5/`: resultados originais e revisão v5;
- `reavaliacao_total_conciliada_v6_1/`: instruções, entradas, conciliação de partes, fontes e hashes;
- `claude_reavaliacao_total_conciliada_v6_1/` e `revisao_humana_total_final_20261013/`: predições originais e referência final dos 300;
- `piloto_ap02_ap13_v1/`, `piloto_ap09_ap16_ap22_v1/` e as respectivas pastas `claude_piloto_.../`: entradas, instruções, configuração e consumo dos pilotos;
- `revisao_humana_piloto_ap02_ap13_20261014/` e `revisao_humana_piloto_ap09_ap16_ap22_20261015/`: decisões por ID, confirmações na conversa, gabaritos finais, métricas, divergências, pendências vazias e manifestos de procedência.

Ao término desses testes, existem referências humanas consolidadas para 445 IDs distintos da extração de 3.455 candidatos: 300 do desenvolvimento e 145 dos pilotos. Isso não significa que os 445 foram novamente revisados de forma integral nesta etapa: a reavaliação dos 300 teve revisão direcionada de 51 casos, enquanto os pilotos tiveram revisão de todos os 145. A documentação não substitui nem sobrescreve a base canônica; a aplicação das decisões deve respeitar os IDs e a precedência das confirmações humanas. O texto distingue experimentos executados de sugestões futuras e não inclui o planejamento posterior de auditoria ou inferência estatística.

### 14.14. Execução das menções restantes e revisão das pendências

Em novembro de 2026, a classificação com Claude Sonnet 5 e instruções v6.1 foi concluída para os 3.010 candidatos restantes da extração existente. As 445 decisões humanas consolidadas anteriormente foram preservadas. A rodada consumiu 14.611.678 tokens de entrada e 72.119 de saída, com custo estimado de US$ 29,944546 pelas tarifas de referência, antes de impostos e sem incluir testes anteriores.

As previsões originais foram: 1.047 incorporações, 1.879 exclusões, 81 decisões de corpus indeterminadas e três respostas inválidas. Entre as incorporações, houve 435 Contextos, 213 Relatos, 371 Argumentos e 28 tipos indeterminados. Esses números descrevem previsões, não acurácia.

Os 112 casos sinalizados (81 de corpus, 28 de tipo e três respostas inválidas) receberam triagem interpretativa do Codex, com consulta ao contexto e a páginas dos acórdãos, inclusive chamados de notas. O pesquisador revisou a planilha dessa triagem: aceitou 89 sugestões e indicou novos rótulos em 23 casos. O resultado dessa revisão foi 71 exclusões, 39 Argumentos, um Relato e um Contexto. Todas as 112 pendências receberam decisão conclusiva. A revisão foi orientada por sugestões de IA, não cega, e limitada aos casos sinalizados; não constitui amostra aleatória ou validação independente das demais previsões.

Decisões específicas relevantes para o registro, sem generalização automática para ocorrências não revisadas:

- No grupo do CFM na ADPF 54, os casos 7, 8, 29, 30 e 31 foram excluídos. O caso 10, que retoma a caracterização substantiva do feto como natimorto cerebral, foi incorporado como Argumento. Não se deve resumir essas decisões a uma exclusão de toda referência ao CFM.
- Os casos 50–52 sobre atuação regulatória da ANATEL foram excluídos. Também foram excluídos os nove casos em que a instituição aparecia como nome de revista/boletim (68, 78, 79, 84, 85, 90, 91, 94 e 95) e os dois em que Badaró figurava como coordenador de obra cujo trecho era atribuído a outro autor (92 e 96). São decisões sobre a atribuição da contribuição, não exclusões de todos os trabalhos dessas instituições ou pessoas.
- O parecer juntado pelo Instituto Alana no caso 111, os dados do Ministério da Saúde nos casos 47–49 e a citação indireta na exposição de motivos do caso 98 foram excluídos. Já o estudo divulgado pelo InternetLab no caso 105 foi incorporado como Argumento.
- As contribuições ministeriais dos casos 17 e 26 e os dados do MEC no caso 46 foram incorporados como Argumento; a fala do Ministro do Meio Ambiente no caso 59 foi excluída. A condição de órgão público, isoladamente, não determina o enquadramento como contribuição de parte.
- Diversas notas foram incorporadas como Argumento após a localização do chamado no raciocínio do julgador. As respostas originais do Claude, inclusive as inválidas, permanecem preservadas para distinguir erro de formato, falta de contexto e decisão humana posterior.

A base resultante reúne 3.455 ocorrências: 1.288 incorporadas (509 Contextos, 278 Relatos e 501 Argumentos) e 2.167 excluídas. Há 557 decisões humanas consolidadas e 2.898 previsões sem revisão humana. Ausência de pendências sinalizadas não significa ausência de erros. Os números dos casos acima referem-se à coluna `Caso original` da triagem e são vinculados a IDs estáveis no registro de revisão.

A versão revisada está em `outputs/01a02b49-a916-75a0-80da-a7b4fcc952c1/consolidacao_integral_revisada_20261105/`, com a cópia recebida, decisões por ID e célula de origem, JSON e CSV consolidados. A base anterior e as instruções congeladas não foram sobrescritas. As decisões deste lote não foram propagadas automaticamente para casos semelhantes ainda não revisados.

### 14.15. Eixos temáticos e unidades de contagem na análise final

O pesquisador atribuiu um eixo temático a cada audiência. Na aba `Menções` de `analise_final_mencoes.xlsx`, cada ocorrência recebe o eixo correspondente ao número da audiência, inclusive quando excluída do corpus. O eixo caracteriza a audiência como um todo; não classifica o assunto de cada passagem. Foi acrescentado após a classificação, sem nova chamada ao Claude nem alteração das decisões de inclusão ou de tipo.

| Eixo temático | Números das audiências | Ocorrências identificadas | Incorporadas | Excluídas |
|---|---|---:|---:|---:|
| Direitos ambientais, políticas públicas e liberdade de mercado | 2, 6, 7, 8, 9, 10, 12, 14, 18, 19, 28, 29, 30, 31, 33, 36, 38 e 41 | 1.216 | 585 | 631 |
| Direitos da Personalidade | 1, 3, 4, 5, 11, 13, 15, 16, 17, 22, 32 e 35 | 2.239 | 703 | 1.536 |
| **Total** | **30 audiências com ocorrências na base final** | **3.455** | **1.288** | **2.167** |

Para descrever a composição do corpus por tipo de menção, o denominador é o número de ocorrências **incorporadas** no recorte. Por exemplo, a proporção de Argumentos entre as menções incorporadas do primeiro eixo tem denominador 585. Já a proporção de candidatos incorporados nesse eixo tem denominador 1.216. Essas contagens são de ocorrências, não de pessoas ou de audiências.

A planilha auxiliar `pessoas_incorporadas.xlsx`, na mesma pasta da base revisada indicada na seção 14.14, tem outra unidade: um nome distinto identificado no campo de pessoa das ocorrências incorporadas. Os nomes agrupados em uma ocorrência foram separados; para cada nome, buscou-se o vínculo institucional nos cadastros de participantes da respectiva audiência (`resultados/listas_participantes_revisadas.csv` e, na ausência de correspondência, `resultados/participantes_relacional_limpo.csv`). A simples presença de uma instituição no mesmo trecho não foi tomada como prova de vínculo. A lista reúne 137 nomes, dos quais 77 têm instituição registrada e 60 ficaram com o campo em branco. Campo vazio indica ausência de vínculo identificado no cadastro, não ausência de filiação. Menções genéricas à audiência e menções exclusivamente institucionais não geram nomes nessa lista.

## 15. Reprodutibilidade e controle de versões

Cada execução relevante deverá registrar:

- data da execução;
- versão do código ou *commit*;
- versão deste documento;
- versão da lista de participantes;
- arquivos de entrada utilizados;
- parâmetros de busca e contexto;
- regras ativas;
- modelo e instrução utilizados, quando houver IA;
- resultados automáticos e correções humanas.

Alterações metodológicas que possam mudar os resultados devem gerar nova versão deste documento e, quando necessário, nova execução do corpus.

Na fase de preparação dos insumos, `limpar_lista_relacional.py` reproduz a limpeza e a deduplicação da tabela de participantes, e `gerar_variantes_busca.py` reproduz a tabela de termos. Uma execução da pesquisa deverá registrar precisamente qual versão dos arquivos `resultados/participantes_relacional_limpo.csv` e `resultados/termos_busca_acordaos_ativos.csv` foi utilizada, preferencialmente com data, *commit* e soma de verificação.

## 16. Questões em aberto

As seguintes decisões deverão ser refinadas durante o desenvolvimento:

- qual extensão de contexto é suficiente para cada tipo de acórdão;
- quais expressões coletivas adicionais relacionadas à audiência devem integrar a busca, além dos dois termos globais já ativos;
- quais dos 310 termos reservados para revisão deverão ser ativados após a validação no corpus;
- como representar menções coletivas que não permitem identificar participantes;
- qual limiar de correspondência é aceitável para vínculo implícito;
- como distinguir inspiração temática de efetiva retomada documental;
- como classificar referências feitas no relatório, nos votos, em citações de terceiros e na ementa;
- como registrar votos que atribuem genericamente dados à audiência sem indicar a fala de origem;
- quais ocorrências exigirão dupla revisão humana;
- qual amostra de ocorrências extraídas por OCR deverá receber dupla conferência
  contra a imagem da página;
- quais métricas serão utilizadas no relatório final da pesquisa.

## 17. Registro de alterações

| Versão | Data | Alteração |
|---|---|---|
| 0.12 | 2026-11-05 | Registro dos dois eixos temáticos nas 30 audiências com ocorrências, dos denominadores por eixo e dos critérios da lista de pessoas e instituições. |
| 0.11 | 2026-11-05 | Execução de 3.010 menções com v6.1, triagem e revisão humana das 112 pendências, decisões específicas e consolidação de 3.455 ocorrências. Separação entre 557 decisões humanas e 2.898 previsões não revisadas; sem alterar o prompt congelado. |
| 0.10 | 2026-10-15 | Atualização até o último piloto revisado: lotes v4/v5, extensão a contribuições intelectuais, conciliação de partes, reavaliação dos 300, instruções v6.1 idênticas nos cinco pilotos, decisões finais, resultados originais versus pós-revisão, custos e rastreabilidade. Sem incorporar planejamento posterior de auditoria ou intervalos. |
| 0.9 | 2026-09-14 | Decisões pós-testes sobre partes, terceiros, amici, bibliografia, listas e outras audiências; três categorias de engajamento; ajuste local MLX e avaliações Claude; distinção entre resultados originais e pós-revisão; limitações de contexto, amostragem e validação independente. |
| 0.8 | 2026-08-31 | Adoção da frase contextualizada como unidade da ocorrência; consolidação de pessoa, instituição e expressão na mesma linha; preservação das contagens de menções e alvos; regra conservadora para classificações conflitantes; reexecução integral, atualização dos produtos e 35 testes aprovados. |
| 0.7.1 | 2026-08-31 | Documentação da execução integral 0.7.0; deduplicação por alvo e parágrafo com contagem preservada; exclusões de referências bibliográficas, requerentes e representantes processuais; parágrafo completo e página nas saídas; atualização dos CSVs, JSONL, manifesto, planilha e validações. |
| 0.7 | 2026-08-29 | Restrição da lista operacional de participantes às notas taquigráficas e transcrições; exclusão de habilitados, convocados e programados sem confirmação nessas fontes; OCR das 231 páginas das notas da audiência 1; regeneração da lista relacional e das variantes. |
| 0.6.1 | 2026-08-22 | Detecção de PDFs com camada textual insuficiente; OCR Apple Vision com cache e interrupção segura; reexecução das audiências 3 e 4; consolidação parcial rastreável; atualização dos CSVs, JSONL, manifesto, planilha e validações. |
| 0.6 | 2026-08-22 | Execução integral dos 50 acórdãos vinculados a 31 audiências; criação dos produtos canônicos em `resultados/analise_integral/`; resumo por audiência e processo; validação de cobertura, IDs, campos, pacotes de revisão e fórmulas. |
| 0.5.1 | 2026-08-22 | Fechamento do piloto: criação do CSV canônico `ocorrencias_classificadas.csv`, seleção de lotes por `--audiencias`, registro do modo de execução no manifesto e remoção do título e subtítulo da página central da planilha. |
| 0.5 | 2026-08-22 | Inclusão das exclusões automáticas por *amicus curiae*, parte, terceiro e enumeração de peça/petição no mesmo parágrafo; adoção dos cinco status; redução do local a Relatório, Voto do Relator e Voto; centralização da planilha e reexecução do piloto. |
| 0.4 | 2026-08-22 | Documentação do programa e do piloto em cinco acórdãos; inclusão das pré-classificações operacionais, autoria e local estrutural da passagem, deduplicação de camadas textuais e variantes, comparação com transcrições e controle de referências a outras audiências. |
| 0.3 | 2026-08-22 | Registro da construção do quadro consolidado do corpus: fontes oficiais, unidade por audiência, critérios para ano, ações, tema e convocantes, rastreabilidade e tratamento das audiências 21, 38, 39 e 48. |
| 0.2 | 2026-08-22 | Documentação do levantamento de 121 documentos de 31 audiências, dos filtros e critérios de elegibilidade, da tabela relacional pessoa–instituição, da deduplicação e da geração, normalização e auditoria das variantes operacionais de busca. |
| 0.1 | 2026-08-22 | Criação do documento; definição da pergunta operacional, unidade de análise, tipologia de vínculo, fluxo de trabalho, estrutura dos resultados e cautelas iniciais. |
