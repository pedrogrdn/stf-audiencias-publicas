import sys,json,re,csv,hashlib
from collections import Counter
from classificar_atores import O,P,CATS,save,norm
rows=json.loads((O/'entradas.json').read_text());supp=json.loads((O/'complementos_contexto.json').read_text())
byid={r['id']:r for r in rows};mapped={};invalid=[];usage=[];canonical={norm(x):x for x in CATS}
canonical.update({norm('Ator público'):'Atores públicos',norm('Ator privado'):'Atores privados',norm('Acadêmico'):'Acadêmicos',norm('Outro'):'Outros'})
for filename in ['respostas.json','respostas_complementos.json']:
    data=json.loads((O/filename).read_text())
    for batch in data.values():
        res=batch['resposta'];usage.append(res.get('usage',{}))
        text=''.join(x.get('text','') for x in res.get('content',[]) if x.get('type')=='text')
        try:
            obj=json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip()))['resultados']
            assert res.get('stop_reason')=='end_turn' and len(obj)==len(batch['ids']) and {x['id'] for x in obj}==set(batch['ids'])
            for x in obj:
                c=x.get('categoria');x['categoria']=canonical.get(norm(c)) if c else None
                assert not c or x['categoria']
                mapped[x['id']]=x|{'origem_resposta':filename}
        except (ValueError,AssertionError,KeyError,TypeError):invalid.extend(batch['ids'])
for r in supp:byid[r['id']]=r
out=[]
for ident,r in byid.items():
    x=mapped.get(ident,{'categoria':None,'revisar':True,'motivo_revisao':'Resposta ausente ou inválida','evidencia':'','justificativa':'','instituicao_identificada':'','qualificacao_identificada':''})
    evidence=norm(x.get('evidencia','')).strip(' "“”«»')
    sources=[(e['texto'],e['arquivo'],str(e.get('pagina_pdf') or ''),'Excerto documental') for e in r['excertos']]+[(r[k],r['fonte_cadastro'],r['paginas_cadastro'],'Cadastro documental') for k in ['instituicao_cadastro','qualificacao_cadastro','evidencia_cadastro']]
    matched=next(((f,p,t) for text,f,p,t in sources if evidence and evidence in norm(text)),None)
    if not matched and evidence:
        chunks=[re.sub(r'[^A-Z0-9]','',norm(z)) for z in re.split(r'\[\s*\.\.\.\s*\]|\.\.\.|…',x.get('evidencia',''))]
        chunks=[z for z in chunks if z]
        for text,f,p,t in sources:
            compact=re.sub(r'[^A-Z0-9]','',norm(text));cursor=0;found=bool(chunks)
            for chunk in chunks:
                pos=compact.find(chunk,cursor)
                if pos<0:found=False;break
                cursor=pos+len(chunk)
            if found:
                matched=(f,p,t);x['correspondencia_citacao']='Normalização de pontuação, quebra de linha, acentos e/ou trechos com reticências';break
    if not matched:
        x['revisar']=True;x['motivo_revisao']=(x.get('motivo_revisao','')+'; conferir citação: não localizada literalmente').strip('; ')
    if not x['categoria']:x['revisar']=True
    out.append(r|{'classificacao':x,'fonte_evidencia':matched[0] if matched else r['fonte_cadastro'],'pagina_evidencia':matched[1] if matched else r['paginas_cadastro'],'tipo_evidencia':matched[2] if matched else 'Conferir'})
assert len(out)==405 and len({r['id'] for r in out})==405
save(O/'classificacoes_documentais.json',out)
it=sum(u.get('input_tokens',0) for u in usage);ot=sum(u.get('output_tokens',0) for u in usage)
summary={'n':len(out),'pessoas_distintas':len({norm(r['nome']) for r in out}),'audiencias':len({r['audiencia'] for r in out}),'por_categoria':dict(Counter(r['classificacao']['categoria'] or 'Pendente' for r in out)),'revisar':sum(bool(r['classificacao'].get('revisar')) for r in out),'sem_categoria':sum(not r['classificacao']['categoria'] for r in out),'respostas_invalidas_finais':sum(r['id'] not in mapped for r in out),'tokens_entrada':it,'tokens_saida':ot,'custo_estimado_usd_referencia':(it*2+ot*10)/1e6,'nota':'Predições documentais, sem validação humana ou estimativa de acurácia. O custo inclui os complementos de contexto.'}
save(O/'resumo_final.json',summary)
save(O/'manifesto_final.json',{'modelo':'claude-sonnet-5','unidade':'pessoa por audiência','registros':405,'sha256':{name:hashlib.sha256((O/name).read_bytes()).hexdigest() for name in ['entradas.json','complementos_contexto.json','instrucoes_v1.txt','respostas.json','respostas_complementos.json','classificacoes_documentais.json']},'normalizacao_rotulos':'Capitalização e formas singulares Ator público, Ator privado, Acadêmico e Outro normalizadas para os cinco rótulos canônicos. Sem alteração semântica das categorias.','prioridade_contexto':'Respostas com contexto documental complementado substituem as primeiras respostas desses mesmos IDs; ambas foram preservadas.','revisao_humana':'Não realizada nesta etapa.'})
(O/'LEIA_ME.md').write_text(f'''# Classificação documental dos participantes — 5 de novembro de 2026

Foram processados {summary['n']} registros de pessoa por audiência, referentes a {summary['pessoas_distintas']} nomes distintos em {summary['audiencias']} audiências do cadastro limpo. O universo é o cadastro disponível no repositório, não todos os participantes de todas as audiências do STF. Uma mesma pessoa pode representar vínculos diferentes em audiências distintas.

## Procedimento

O cadastro `resultados/participantes_relacional_limpo.csv` forneceu nome, vínculo, qualificação e referência documental. Foram recuperados trechos das notas e transcrições locais junto às páginas indicadas. Para 46 registros sem texto inicial suficiente, o contexto foi complementado com o OCR local existente (AP 1) e com notas em PDF/DOCX (AP 3). Nenhuma pesquisa externa foi utilizada. Os campos do cadastro também foram fornecidos como evidência documental; uma indicação de cargo ou vínculo pode ter origem no cadastro curado.

O Claude recebeu os critérios de Atores públicos, Atores privados, Sociedade civil, Acadêmicos e Outros, conforme `instrucoes_v1.txt`. A condição de participação naquela audiência orienta o enquadramento. OAB, conselhos profissionais e sindicatos de trabalhadores foram incluídos em Sociedade civil; associações patronais em Atores privados; estatais em Atores públicos; participação científica em Acadêmicos. Ausência de informação não equivale a Outros. Partidos políticos e dupla representação podem exigir decisão metodológica adicional.

Foi utilizada classificação por instruções, sem treinamento ou fine-tuning, com `claude-sonnet-5`, raciocínio estendido desativado, em grupos de até oito registros. Os textos foram enviados à API da Anthropic sem ferramentas ou busca externa. Respostas, entradas, instruções e somas de verificação foram preservadas. As respostas dos 46 complementos substituem as primeiras respostas dos mesmos IDs, mantendo ambas para rastreabilidade.

## Uso da planilha

`classificacao_participantes.xlsx` contém o resumo, os 405 participantes e os critérios. Na aba Participantes, filtre **Revisar = Sim**: são {summary['revisar']} casos destacados, dos quais {summary['sem_categoria']} ficaram sem categoria. Os demais podem ser usados como classificação automática provisória; não foram considerados confirmados por humano. Preencha Categoria revisada e Comentário somente onde desejar registrar uma decisão. O campo Tem menção incorporada compara a pessoa e audiência à base consolidada revisada de menções.

A coluna Evidência documental reproduz uma citação curta, e a fonte/página permite localizá-la. Uma verificação adicional procurou a citação nos trechos ou campos do cadastro enviados; falhas de correspondência literal foram sinalizadas. Essa conferência é de rastreabilidade textual e não mede a acurácia da classificação. A coluna Instituição documentada pode complementar o vínculo original quando a fala explicita outra instituição; a coluna Instituição no cadastro conserva o valor inicial.

## Limites e custo

As quantidades por categoria são distribuições de predições, não estimativas de acurácia. Lacunas do cadastro, OCR, contexto parcial, representação partidária e vínculos múltiplos podem afetar o enquadramento. A classificação de uma participação não descreve necessariamente a natureza jurídica da instituição ou todos os vínculos históricos da pessoa. O cadastro operacional conserva uma associação institucional selecionada por pessoa e audiência, conforme a metodologia anterior.

Foram registrados {it:,} tokens de entrada e {ot:,} de saída, incluindo os complementos. Custo estimado de US$ {summary['custo_estimado_usd_referencia']:.6f}, pelas tarifas de referência de US$ 2/M de entrada e US$ 10/M de saída, antes de impostos. O faturamento efetivo deve ser conferido no console da API.
''')
with (O/'classificacao_participantes.csv').open('w',encoding='utf-8-sig',newline='') as f:
    wr=csv.writer(f);wr.writerow(['ID','Audiência','Nome','Instituição cadastro','Instituição identificada','Qualificação identificada','Categoria sugerida','Revisar','Motivo revisão','Evidência','Justificativa','Fonte','Página','Mencionado no corpus'])
    for r in out:
        x=r['classificacao'];wr.writerow([r['id'],r['audiencia'],r['nome'],r['instituicao_cadastro'],x.get('instituicao_identificada',''),x.get('qualificacao_identificada',''),x['categoria'] or 'Pendente','Sim' if x.get('revisar') else 'Não',x.get('motivo_revisao',''),x.get('evidencia',''),x.get('justificativa',''),r['fonte_evidencia'],r['pagina_evidencia'],'Sim' if r['mencionado_corpus'] else 'Não'])
print(json.dumps(summary,ensure_ascii=False,indent=2))
