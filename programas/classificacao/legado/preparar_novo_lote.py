"""Novo lote de 30 casos: preparação offline, sem API."""
import json
from collections import defaultdict, Counter
import validar_corpus as runner

ROOT=runner.ROOT
DATA=ROOT/'corpus_novo_lote_v3'
NOTE='Novo lote diagnóstico, não avaliado anteriormente pelo Claude por ID ou menção idêntica. Origem: treino local. Gabarito histórico; corpus é o foco e tipos são diagnósticos. Não é teste independente da pesquisa.'
ADDITION='''
Esclarecimento sobre listas: diferencie participantes da audiência de entidades habilitadas como amici curiae no processo. A condição de amicus não exclui a entidade; é a falta de vínculo desta menção com a audiência que pode excluir a ocorrência. Numeração de processo e documento após os nomes é indício para conferir a origem da lista, nunca motivo automático de exclusão. A introdução da lista, inclusive na página anterior, pode ser decisiva. Se ela não estiver nos recortes enviados e o vínculo não puder ser determinado, use Indeterminado. Não simule consulta a páginas ausentes.
'''

def main():
    if DATA.exists():raise SystemExit('Lote existente; não sobrescrever.')
    source=ROOT/'registros.json'
    records=json.loads(source.read_text())
    allrows={r['id']:r for group in records.values() for r in group}
    prior=set()
    for p in ROOT.glob('claude_*/predicoes.json'):
        prior.update(r['id'] for r in json.loads(p.read_text()))
    norm=lambda s:' '.join(s.lower().split())
    seen={norm(allrows[i]['payload']['mencao']) for i in prior if i in allrows}
    chosen=[]
    # Apenas quatro Contextos não avaliados restam; priorizar diversidade disponível.
    for corpus,label,count in [('Excluir',None,15),('Incorporar',None,15)]:
        groups=defaultdict(list)
        for r in sorted(records['treino'],key=lambda r:r['id']):
            if r['id'] not in prior and r['corpus']==corpus and (label is None or r['tipo']==label):groups[int(r['audiencia'])].append(r)
        n=0
        while n<count:
            progress=False
            for ap in sorted(groups):
                while groups[ap]:
                    r=groups[ap].pop(0);key=norm(r['payload']['mencao'])
                    if key in seen:continue
                    chosen.append(r);seen.add(key);n+=1;progress=True;break
                if n==count:break
            if not progress:raise ValueError('Casos únicos insuficientes')
    chosen.sort(key=lambda r:r['id'])
    assert len(chosen)==30 and not {r['id'] for r in chosen}&prior
    old=(ROOT/'ajuste_corpus_v2/instrucoes.txt').read_text()
    prompt=old.replace('Somente para Incorporar, classifique tipo:',ADDITION+'\nSomente para Incorporar, classifique tipo:')
    inputs=[{'id':r['id'],'system':prompt,'messages':[{'role':'user','content':json.dumps(r['payload'],ensure_ascii=False)}]} for r in chosen]
    gold=[{k:r[k] for k in ['id','audiencia','corpus','tipo']} for r in chosen]
    DATA.mkdir();runner.save(DATA/'entradas.json',inputs);runner.save(DATA/'gabarito_original.json',gold);(DATA/'instrucoes.txt').write_text(prompt)
    runner.save(DATA/'manifesto.json',{'n':30,'sha256':{n:runner.digest(DATA/n) for n in ['entradas.json','gabarito_original.json','instrucoes.txt']},
       'fonte_sha256':runner.digest(source),'finalidade':NOTE,'audiencias':dict(Counter(r['audiencia'] for r in chosen)),
       'selecao':'15 Excluir e 15 Incorporar. Rodízio por audiência; IDs e menções textualmente idênticas às já avaliadas são evitados, não toda equivalência semântica.',
       'contexto':'Recortes originais preservados. Não houve expansão das páginas nem verificação adicional de posição processual.'})
    # Registro separado das decisões sobre o lote anterior; não altera execução nem planilha.
    revision=ROOT/'decisoes_corpus_pos_v2.json'
    if not revision.exists():runner.save(revision,{'origem':'Confirmações do usuário na conversa',
       'decisoes':[{'caso':36,'id':'AP35-AP_35_ADI_6299-00033','corpus':'Excluir'},
                    {'caso':40,'id':'AP35-AP_35_ADI_6300-00093','corpus':'Excluir'},
                    {'caso':42,'id':'AP35-AP_35_ADI_6298-00293','corpus':'Incorporar'},
                    {'caso':47,'id':'AP35-AP_35_ADI_6300-00059','corpus':'Incorporar'}],
       'nota':'Caso 42 é decisão específica; não estabelece regra geral de inclusão de relatórios.'})
    runner.DATA=DATA;runner.load();print('30 casos preparados offline:',Counter(r['audiencia'] for r in chosen))

if __name__=='__main__':main()
