"""Consolidação offline da planilha e confirmação dos casos 68 e 69 no chat."""
import json
import hashlib
from collections import Counter
from pathlib import Path
import openpyxl

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'revisao_humana_piloto_ap09_ap16_ap22_20261015'
SHEET=Path(__file__).resolve().parents[3] / 'entradas_externas_migracao' / 'revisao_piloto_ap09_ap16_ap22.xlsx'
PRED=ROOT/'claude_piloto_ap09_ap16_ap22_v1/predicoes.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists(), 'Consolidação existente; não sobrescrever.'
sources={str(p):sha(p) for p in [SHEET,PRED]}
pred={r['id']:r['previsto'] for r in json.loads(PRED.read_text())}
w=openpyxl.load_workbook(SHEET,read_only=True,data_only=False)
s=w['Revisão']; headers=[c.value for c in s[5]]
decisions=[]; gold=[]; seen=set()
overrides={'AP22-AP_22_RE_1010606-00014':68,'AP22-AP_22_RE_1010606-00015':69}
for rownum, row in enumerate(s.iter_rows(min_row=6,values_only=True),6):
    d=dict(zip(headers,row));i=d.get('ID')
    if not i:continue
    assert i in pred and i not in seen
    seen.add(i);x=pred[i]
    assert (d['Corpus Claude'],d['Tipo Claude'])==(x['corpus'],x['tipo'] or 'Não se aplica')
    assert d['Decisão'] in ['Aceitar Claude','Alterar','Conferir contexto']
    c,t=(x['corpus'],x['tipo']) if d['Decisão']=='Aceitar Claude' else (d['Corpus final'],d['Tipo final'])
    if d['Decisão']=='Aceitar Claude':
        assert d['Corpus final'] in [None,c] and d['Tipo final'] in [None,t]
    assert i in overrides or (c=='Excluir' and t is None) or (c=='Incorporar' and t in ['Contexto','Relato','Argumento'])
    record={'caso':d['Caso'],'id':i,'celulas':f'Revisão!D{rownum}:G{rownum}',
        'decisao_planilha':d['Decisão'],'corpus_planilha':c,'tipo_planilha':t,'comentario':d['Comentário opcional']}
    if i in overrides:
        assert d['Caso']==overrides[i]
        c,t=('Incorporar','Argumento') if d['Caso']==68 else ('Excluir',None)
        record['confirmacao_chat']='Usuário confirmou em 15/10/2026: caso 68 Incorporar — Argumento; caso 69 Excluir. Prevalece sobre a planilha.'
    record.update(corpus=c,tipo=t);decisions.append(record)
    gold.append({'id':i,'audiencia':int(d['AP']),'corpus':c,'tipo':t})
w.close()
assert seen==set(pred) and len(gold)==84
def summarize(rows):
    corpus=full=0; matrix=Counter(); types={}; distribution=Counter()
    for g in rows:
        x=pred[g['id']];ok=g['corpus']==x['corpus']
        corpus+=ok;full+=ok and (g['corpus']=='Excluir' or g['tipo']==x['tipo'])
        matrix[g['corpus']+' -> '+x['corpus']]+=1
        distribution[g['tipo'] if g['corpus']=='Incorporar' else 'Excluir']+=1
    for label in ['Contexto','Relato','Argumento']:
        support=sum(g['tipo']==label for g in rows)
        hits=sum(g['tipo']==label and pred[g['id']]=={'corpus':'Incorporar','tipo':label} for g in rows)
        types[label]={'suporte_humano':support,'acertos':hits,'recall':hits/support if support else None}
    return {'n':len(rows),'corpus_acertos':corpus,'classificacao_completa_acertos':full,
        'distribuicao_humana':dict(distribution),'matriz_corpus':dict(matrix),'por_tipo':types}
report=summarize(gold)
report['por_audiencia']={str(a):summarize([g for g in gold if g['audiencia']==a]) for a in [9,16,22]}
report['nota']='Concordância das predições congeladas com revisão humana integral e duas confirmações no chat. Revisão não cega, com respostas do Claude visíveis. Três audiências selecionadas intencionalmente. Não mede recuperação de menções ausentes da extração nem generalização para todas as audiências. Nenhuma nova API chamada.'
errors=[{'caso':d['caso'],'id':d['id'],'humano':{'corpus':d['corpus'],'tipo':d['tipo']},'claude':pred[d['id']]} for d in decisions if (d['corpus'],d['tipo'])!=(pred[d['id']]['corpus'],pred[d['id']]['tipo'])]
assert (report['corpus_acertos'],report['classificacao_completa_acertos'],len(errors))==(76,75,9)
assert all(sha(Path(p))==h for p,h in sources.items())
OUT.mkdir()
def save(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
save('decisoes.json',decisions);save('gabarito_revisado.json',gold);save('metricas_pos_revisao.json',report)
save('divergencias_remanescentes.json',errors);save('pendencias.json',[])
save('manifesto.json',{'fontes_sha256':sources,'data':'2026-10-15','confirmacoes_chat':overrides,
    'observacao':'A planilha original foi preservada. As decisões finais, incluindo as confirmações do chat, estão em decisoes.json e gabarito_revisado.json.',
    'arquivos_sha256':{p.name:sha(p) for p in OUT.iterdir()}})
print(json.dumps(report,ensure_ascii=False,indent=2))

