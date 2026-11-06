"""Registra triagem interpretativa do Codex, sem alterar gabaritos ou previsões."""
import json,hashlib,re
from pathlib import Path
from collections import Counter
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'outputs/01a02b49-a916-75a0-80da-a7b4fcc952c1/consolidacao_integral_20261105'
SRC=OUT/'base_consolidada.json'
d=json.loads(SRC.read_text());rows=d['pendencias']
assert len(rows)==112
pdf=json.loads(Path('/tmp/triagem_textos_stf.json').read_text())
from pypdf import PdfReader
extra_doc=PdfReader(BASE/'acordaos/AP_36_ADI_7187.pdf')
pdf['AP_36_ADI_7187.pdf']=['']*len(extra_doc.pages)
for p in [10,11,33,34,35]:pdf['AP_36_ADI_7187.pdf'][p-1]=extra_doc.pages[p-1].extract_text() or ''
meta={r['ocorrencia_id']:r for r in json.loads((BASE/'outputs/execucao_integral_20261105/metadados_originais.json').read_text())}
decisions={}
def setcases(nums,status,corpus,tipo,group,reason,action='Conferir a sugestão; não é necessário redigir justificativa.'):
    for n in nums:
        assert n not in decisions,n
        decisions[n]={'status_triagem':status,'sugestao_corpus':corpus,'sugestao_tipo':tipo,'grupo':group,'fundamento':reason,'proximo_passo':action}
S='Sugestão definida';C='Conferência pontual';M='Decisão metodológica'
setcases([1],C,'Incorporar','Relato','Descrição de pesquisa',
 'A continuação atribui a Cláudia Batista estudo de células-tronco neurais, não só formação acadêmica. Há evidência de fala no cadastro. Sugiro Relato pela descrição da atividade de pesquisa; conferir se você entende que esta identificação já contém contribuição substantiva.',
 'Confirmar se a descrição do objeto da pesquisa supera a identificação biográfica.')
setcases([2,3],S,'Incorporar','Argumento','Notas com chamado localizado',
 'Na p. 376, o julgador enfrenta os exemplos de embriões congelados por mais de três anos como contraponto; as notas 45 e 47 sustentam precisamente esses exemplos. Discordância também constitui uso argumentativo.')
setcases([4],S,'Incorporar','Argumento','Contribuição intelectual',
 'A entrevista de Mayana Zatz é convocada para apoiar a distinção entre células embrionárias e adultas e a ponderação desenvolvida no voto. A participação consta do cadastro documental.')
setcases([5,6],S,'Incorporar','Argumento','Contribuição intelectual',
 'As pp. 432–433 apresentam e transcrevem documento científico do grupo da Academia Brasileira de Ciências para enfrentar as teses da ação. Mayana Zatz e Antonio Carlos Campos de Carvalho têm evidência de participação no cadastro. A identificação dos autores continua na transcrição substantiva.')
setcases([7,8,10,29,30,31],M,'Indeterminado',None,'Resoluções técnicas do CFM',
 'O contexto atribui ao CFM definições técnicas de morte/anencefalia por meio de resolução normativa. Não é mera menção nominal, mas a regra congelada não decide expressamente se uma resolução deve ser tratada como manifestação intelectual do participante ou apenas como norma aplicada.',
 'Decidir uma vez para o grupo: a extensão bibliográfica abrange conteúdo técnico de resoluções? Não generalizar para toda menção ao CFM.')
setcases([9],S,'Incorporar','Argumento','Continuação entre páginas',
 'A passagem da p. 52 continua na p. 53 com a tese de Débora Diniz sobre autonomia e doação de órgãos, mobilizada na discussão do dever de manter a gestação.')
note_cases={11:25,12:27,13:33,14:34,15:35,16:39,18:43,19:49,20:50,21:55,22:67,23:82,24:86,25:94,28:106}
setcases(list(note_cases),S,'Incorporar','Argumento','Notas com chamado localizado',
 'O chamado foi localizado no voto: a fala documenta uma premissa médica, a diferenciação de situações ou uma razão sobre autonomia/sofrimento utilizada pelo julgador. A nota não é apenas registro da realização da audiência.')
setcases([17,26],C,'Incorporar','Argumento','Representação de autoridade pública',
 'O chamado identifica contribuição substantiva do Ministro da Saúde (nota 41) ou da Ministra de Políticas para as Mulheres (nota 104). A função argumentativa é identificável. O Presidente da República figura como interessado na ação; falta decidir se estas falas ministeriais representam a parte neste contexto, sem excluir automaticamente todo agente público.',
 'Conferir a representação processual da autoridade; se representar parte excluída, aplicar a regra prioritária de exclusão.')
setcases([27],C,'Excluir',None,'Atribuição à arguente',
 'Na p. 67, a nota 105 acompanha “O que a arguente pretende é...”. Sugiro excluir pela atribuição à pretensão da parte, mas a indicação da transcrição na nota requer conferir a cadeia de atribuição antes de fechar.',
 'Confirmar a aplicação da regra de reprodução de posição da parte a este trecho.')
setcases([32,33,34,35],S,'Incorporar','Argumento','Notas com chamado localizado',
 'Os chamados nas pp. 380, 381, 399 e 413 vinculam as notas a premissas ou teses enfrentadas por Cezar Peluso. A função é argumentativa, inclusive como contraponto; não depende de concordância com o expositor.')
setcases([36,38,41,44,45],S,'Excluir',None,'Atuação institucional sem contribuição',
 'A passagem comenta que outro ministro trouxe à tona a questão da ANVISA. Não atribui posição ou pesquisa à agência nem identifica contribuição dela na audiência; o assunto da discussão não basta para esse vínculo.')
setcases([37,43],S,'Incorporar','Argumento','Contribuição intelectual',
 'O artigo de Ingo Sarlet é citado como magistério doutrinário que sustenta a proibição de retrocesso no direito à saúde. A evidência de participação está no cadastro da AP04; aplica-se a extensão bibliográfica.')
setcases([39,40,42],C,'Excluir',None,'Atribuições legais da ANVISA',
 'No recorte, a agência aparece por suas funções de registro e controle de medicamentos, sem atribuição de fala ou conclusão de estudo. Sugiro excluir, mas o PDF é digitalização sem texto extraível nestas páginas e o início anterior da seção não foi recuperado nesta triagem.',
 'Conferir o início da seção na página anterior: se houver atribuição direta à exposição da ANVISA, reconsiderar.')
setcases([46],S,'Incorporar','Argumento','Resposta inválida examinada',
 'Os dados do MEC apresentados na audiência fundamentam a premissa da desigualdade racial. Nas pp. 1–2, figuram DEM como requerente e órgãos/autoridades da UnB como interessados; a resposta do Claude presume indevidamente que o MEC é parte só por integrar o Executivo. Não há evidência dessa condição no material consultado.')
setcases([47,48,49],C,'Indeterminado',None,'Dados oficiais e posição processual',
 'Há resultados estatísticos atribuídos ao Ministério da Saúde/DATASUS, e não só nome de órgão. O cadastro registra a participação do Ministério. Antes de aplicar a extensão a pesquisas, é necessário conferir se a fonte atua como representante de parte neste processo e a atribuição do estudo.',
 'Conferir a posição processual e a autoria dos dados; não excluir apenas porque a instituição é um ministério.')
setcases([50,51,52],M,'Indeterminado',None,'Estudos e atos regulatórios da ANATEL',
 'A menção envolve dados de reclamações e justificativas de regulação atribuídos à ANATEL. É preciso delimitar a extensão metodológica: estudo/posição técnica externa pode ser elegível; simples exercício de competência normativa não é contribuição de audiência.',
 'Decidir a distinção entre manifestação técnica e ato regulatório; os casos 50 e 52 repetem o mesmo trecho em acórdãos distintos.')
setcases([53,76,77,83,87,88,89,103,107,109,110,112],S,'Excluir',None,'Cabeçalho processual',
 'O contexto contém AM. CURIAE., ADV. ou PROC. e a identificação dos sujeitos processuais. É cabeçalho do processo, não lista de participantes da audiência. A exclusão é desta menção, não da entidade como participante.')
setcases([54],S,'Incorporar','Argumento','Notas com chamado localizado',
 'O chamado da nota 54 está na p. 57: o dado de Carlos Minc sobre o gasto com ensino religioso sustenta a crítica ao impacto do modelo confessional e sua compatibilidade com a laicidade.')
setcases([55],S,'Incorporar','Contexto','Resposta inválida examinada',
 'O relator registra a realização da audiência como razão procedimental para rejeitar novo ingresso. Não mobiliza contribuição substantiva. Corrige-se apenas como sugestão o campo corpus inválido, sem alterar a resposta original.')
setcases([56],S,'Incorporar','Argumento','Continuação entre páginas',
 'Nas pp. 45–46, a audiência delimita o problema de compatibilizar persecução penal, soberania e privacidade. A discussão é retomada pelo julgador para fundamentar a necessidade de aperfeiçoamento normativo; não é só registro de realização.')
setcases([57],S,'Excluir',None,'Atuação institucional sem contribuição',
 'A referência é ao trabalho/projeto Amazônia Protege do MPF; o recorte não retoma posição, estudo ou fala atribuída ao participante na audiência. Uma atuação institucional não equivale automaticamente à contribuição intelectual.')
setcases([58],S,'Excluir',None,'Composição de outro colegiado',
 'A tabela é de composição do COFA (governos e sociedade civil), conforme o parágrafo logo abaixo. Não lista participantes da audiência pública.')
setcases([59],S,'Excluir',None,'Contribuição de parte',
 'A p. 1 identifica a União como interessada, e a ação trata da omissão da União na gestão do Fundo. A menção retoma a motivação do então Ministro do Meio Ambiente sobre essa atuação governamental; aplica-se a exclusão de contribuição da parte, mesmo com função argumentativa.')
setcases([60,62,64,65,66,67,69],S,'Excluir',None,'Atuação institucional sem contribuição',
 'O MP/RJ é mencionado como destinatário de deveres, responsável pelo controle ou agente de cumprimento das medidas. Não há contribuição de audiência ou estudo atribuído à instituição nessa menção.')
setcases([61],S,'Excluir',None,'Manifestação durante o julgamento',
 'O contexto é esclarecimento em sessão de julgamento sobre a ouvidoria do CNMP, seguido de intervenção de ministros; não exposição na audiência estudada nem referência bibliográfica a pesquisa.')
setcases([63],S,'Excluir',None,'Manifestação processual',
 'A proposta do MP/RJ integra a sequência de manifestações e notas técnicas juntadas nos autos sobre metas para 2024, não a audiência. O recorte não identifica obra ou pesquisa própria à qual aplicar a exceção bibliográfica.')
setcases([68,78,79,84,85,90,91,94,95],M,'Indeterminado',None,'Revista não equivale a autoria institucional',
 'A entidade é identificada no nome da revista/boletim, mas a tese é atribuída a autores do artigo. Publicar em revista de participante não demonstra que a tese seja institucional nem que os autores participaram. Evitar transferir automaticamente a autoria intelectual à editora.',
 'Decidir uma vez se a publicação por entidade participante basta; minha recomendação é exigir autoria/posição institucional ou participação dos autores, em vez de incluir pelo nome da revista.')
setcases([70,71],S,'Incorporar','Argumento','Relatório institucional substantivo',
 'O relatório Panorama do Acesso à Justiça é expressamente atribuído ao CNJ, participante cadastrado. Seus resultados sustentam o cabimento do habeas corpus coletivo. É análogo à decisão metodológica anterior de admitir relatório do CNJ, não audiência prevista em legislação.')
setcases([72,73,81,86,93],S,'Excluir',None,'Lista de amici confirmada',
 'A introdução na p. 63 da ADI 6298 distingue as transcrições da audiência e, em seguida, a admissão de entidades como amici. Os trechos correspondentes nos acórdãos conjuntos reproduzem essa lista processual, não os expositores.')
setcases([74,80],S,'Excluir',None,'Manifestação durante o julgamento',
 'O extrato informa suspensão do julgamento após sustentações orais e enumera quem falou pelas partes/amici. Não se trata da audiência pública.')
setcases([75],S,'Excluir',None,'Manifestação processual',
 'A continuação na p. 232 da ADI 6298 atribui ao TJBA pronunciamento nos autos (e-doc. 274), com pedido de modulação. Não identifica fala de audiência nem obra intelectual externa.')
setcases([82],S,'Excluir',None,'Implementação normativa',
 'O CNJ aparece como órgão que deverá fixar diretrizes para reorganizar os tribunais. A menção é a competência de implementação, não ao conteúdo de um relatório citado nem a contribuição na audiência.')
setcases([92,96],C,'Excluir',None,'Coordenador não equivale a autor do trecho',
 'O trecho doutrinário é atribuído a Andrey Borges de Mendonça; Gustavo Badaró aparece na coordenação da obra. Sugiro não imputar automaticamente ao coordenador a tese de capítulo assinado por outro autor.',
 'Confirmar que a extensão bibliográfica exige autoria da contribuição, não apenas coordenação do livro.')
setcases([97],S,'Excluir',None,'Lista de amici confirmada',
 'A p. 10 da ADI 7187 introduz a lista com “admiti como amicus curiae”; a p. 11 contém sua continuação. Não é lista da audiência.')
setcases([98],C,'Indeterminado',None,'Citação indireta em documento normativo',
 'As pp. 33–35 reproduzem a exposição de motivos da MP 621/2013. Os números são atribuídos ao CFM dentro desse documento. Convém distinguir a retomada do estudo pelo julgador da reprodução de justificativa legislativa e aplicar a extensão a fontes externas sem confundi-la com participação na audiência.',
 'Definir se essa cadeia de citação indireta constitui retomada suficiente do estudo do participante.')
setcases([99,100],S,'Incorporar','Argumento','Relatório institucional substantivo',
 'O voto retoma expressamente levantamento do CFM, reproduzido em pesquisa, sobre infraestrutura das escolas médicas. O cadastro confirma participação do Conselho. Os resultados apoiam a discussão substantiva da abertura de vagas; não é simples menção a norma.')
setcases([101],S,'Excluir',None,'Outra audiência ou previsão genérica',
 'A passagem doutrinária trata de consulta/audiência pública na análise de impacto regulatório, prevista no Decreto 10.411/2020. Não é a audiência específica da ADI 7187.')
setcases([102],S,'Incorporar','Argumento','Continuação entre páginas',
 'A p. 234 continua a frase com dados e posição de Isabella Henriques na audiência sobre proteção de crianças e dever de cuidado. O voto os mobiliza para sustentar proteção especial no ambiente digital.')
setcases([104],S,'Excluir',None,'Lista de amici confirmada',
 'O chamado da nota 2 na p. 380 diz que mais de vinte entidades foram admitidas como amici. A nota das pp. 447–448 identifica esses amici; a audiência aparece depois, em frase distinta.')
setcases([105],C,'Incorporar','Argumento','Autoria de publicação institucional',
 'O chamado da nota 65 está na p. 543 e usa pesquisa divulgada no InternetLab como exemplo de erro de moderação. Sugiro Argumento se a publicação for tratada como pesquisa institucional; os autores são nomeados e não se deve equiparar qualquer hospedagem de texto a autoria da instituição.',
 'Confirmar a atribuição institucional da pesquisa, distinguindo publicação própria de mera hospedagem editorial.')
setcases([106,108],S,'Excluir',None,'Atuação institucional sem contribuição',
 'A ANPD é indicada pelo julgador como possível fiscalizadora dos deveres das plataformas. Não há posição ou pesquisa atribuída à ANPD nem menção à sua contribuição na audiência.')
setcases([111],M,'Indeterminado',None,'Parecer juntado por amicus',
 'A tese é de Ana Frazão em parecer juntado pelo Instituto Alana. A participação do Alana está documentada, mas a regra de exclusão de petições e a extensão a manifestações intelectuais precisam ser conciliadas aqui: juntada pelo amicus não basta para atribuir a autoria do parecer à entidade.',
 'Decidir se parecer de terceiro juntado pelo participante entra pela extensão intelectual, exigindo atribuição substantiva; não confundir amicus com parte automaticamente excluída.')
assert set(decisions)==set(range(1,113)),sorted(set(range(1,113))-set(decisions))
# Registra trechos adicionais efetivamente consultados, em páginas PDF (1-based).
extra={2:('AP_01_ADI_3510.pdf',[376]),3:('AP_01_ADI_3510.pdf',[376]),5:('AP_01_ADI_3510.pdf',[432,433]),6:('AP_01_ADI_3510.pdf',[432,433]),9:('AP_03_ADPF_054.pdf',[52,53]),17:('AP_03_ADPF_054.pdf',[1,46]),26:('AP_03_ADPF_054.pdf',[1,66,67]),27:('AP_03_ADPF_054.pdf',[67]),32:('AP_03_ADPF_054.pdf',[380]),33:('AP_03_ADPF_054.pdf',[381]),34:('AP_03_ADPF_054.pdf',[399]),35:('AP_03_ADPF_054.pdf',[413]),46:('AP_05_ADPF_186.pdf',[1,2,105]),54:('AP_17_ADI_4439.pdf',[57]),56:('AP_29_ADC_051.pdf',[45,46]),59:('AP_31_ADO_059.pdf',[1,157]),72:('AP_35_ADI_6298.pdf',[63]),73:('AP_35_ADI_6298.pdf',[63,65]),75:('AP_35_ADI_6298.pdf',[231,232]),81:('AP_35_ADI_6298.pdf',[63]),86:('AP_35_ADI_6298.pdf',[63]),93:('AP_35_ADI_6298.pdf',[63]),102:('AP_38_RE_1037396.pdf',[233,234]),104:('AP_38_RE_1037396.pdf',[380,447,448]),105:('AP_38_RE_1037396.pdf',[543,594])}
for n,note in note_cases.items():
    page=next(i+1 for i,t in enumerate(pdf['AP_03_ADPF_054.pdf'][:70]) if re.search(r'\[\s*'+str(note)+r'\s*\]',t))
    extra[n]=('AP_03_ADPF_054.pdf',[page]);decisions[n]['fundamento']+=f' Chamado da nota {note}: p. {page} do PDF.'
extra[97]=('AP_36_ADI_7187.pdf',[10,11])
extra[98]=('AP_36_ADI_7187.pdf',[33,35])
result=[]
for n,r in enumerate(rows,1):
    x=r|decisions[n]|{'caso':n,'autor_triagem':'Codex; sugestão não confirmada pelo pesquisador','decisao_humana':None,'evidencia_adicional':'','paginas_consultadas':'Contexto da extração, p. '+str(r['pagina_pdf'])}
    if n in extra:
        filename,pp=extra[n];x['paginas_consultadas']=filename+' — PDF '+', '.join(map(str,pp))
        x['evidencia_adicional']='\n\n'.join(f'PDF {p}: '+re.sub(r'\s+',' ',pdf[filename][p-1].split('Documento assinado')[0]) for p in pp)
    x['evidencia_participacao_cadastrada']=meta[r['id']]['evidencia_participacao']
    result.append(x)
summary={'n':112,'status':dict(Counter(r['status_triagem'] for r in result)),
    'sugestoes':dict(Counter((r['sugestao_corpus'] or '')+' / '+(r['sugestao_tipo'] or 'não aplicável') for r in result)),
    'nota':'Triagem interpretativa offline do Codex. Não é gabarito humano, nova execução do Claude ou estimativa de acurácia. Base original preservada.'}
sources={str(SRC.relative_to(BASE)):hashlib.sha256(SRC.read_bytes()).hexdigest()}
for f,_ in extra.values():sources['acordaos/'+f]=hashlib.sha256((BASE/'acordaos'/f).read_bytes()).hexdigest()
(OUT/'triagem_pendencias.json').write_text(json.dumps({'resumo':summary,'records':result,'fontes_sha256':sources},ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
