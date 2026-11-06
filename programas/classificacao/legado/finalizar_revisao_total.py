"""Aplica apenas as duas decisões confirmadas no chat, sem API."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'revisao_humana_total_20261013'
OUT = ROOT / 'revisao_humana_total_final_20261013'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists(), 'Resultado existente; não sobrescrever.'
gold = read(SOURCE/'gabarito_revisado.json')
decisions = read(SOURCE/'decisoes.json')
predpath = ROOT/'claude_reavaliacao_total_conciliada_v6_1/predicoes.json'
pred = {r['id']:r['previsto'] for r in read(predpath)}
updates = {
    'AP01-AP_01_ADI_3510-00002': ('Alterar','Contexto'),
    'AP01-AP_01_ADI_3510-00020': ('Manter','Argumento'),
}
assert {d['id'] for d in read(SOURCE/'pendencias.json')} == set(updates)
confirmed=[]
for d in decisions:
    if d['id'] in updates:
        action, category=updates[d['id']]
        assert d['decisao']=='Conferir contexto'
        d.update(decisao=action,corpus='Incorporar',tipo=category,
                 fonte_decisao='Confirmação expressa do usuário no chat em 2026-10-13')
        confirmed.append(copy.deepcopy(d))
for g in gold:
    if g['id'] in updates: g.update(corpus='Incorporar',tipo=updates[g['id']][1])
assert len(gold)==len(pred)==300 and len(decisions)==51
assert all(d['decisao'] in ['Manter','Alterar'] for d in decisions)
assert all(g['corpus']=='Excluir' or g['tipo'] in ['Contexto','Relato','Argumento'] for g in gold)
matrix=Counter(); ch=fh=th=inc=0; errors=[]
for g in gold:
    x=pred[g['id']]; ok=g['corpus']==x['corpus']; full=ok and (g['corpus']=='Excluir' or g['tipo']==x['tipo'])
    ch+=ok; fh+=full; inc+=g['corpus']=='Incorporar'; th+=full and g['corpus']=='Incorporar'
    matrix[g['corpus']+' -> '+x['corpus']]+=1
    if not full: errors.append({'id':g['id'],'humano':g,'claude':x})
report={'n':300,'casos_revisados':51,'decisoes':dict(Counter(d['decisao'] for d in decisions)),
        'pendencias':0,'corpus_acertos':ch,'classificacao_completa_acertos':fh,
        'tipo_nos_incorporados':{'n':inc,'acertos':th},'matriz_corpus':dict(matrix),
        'nota':'Concordância pós-revisão dos 51 casos, incluindo duas decisões confirmadas no chat. Os outros 249 casos não foram revistos nesta etapa. Mesmas predições, nenhuma API chamada. Não é validação independente.'}
assert (ch,fh,th,inc)==(266,258,108,122)
OUT.mkdir()
def save(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
save('decisoes_confirmadas_chat.json',confirmed)
save('decisoes.json',decisions)
save('gabarito_revisado.json',gold)
save('pendencias.json',[])
save('metricas_pos_revisao.json',report)
save('divergencias_remanescentes.json',errors)
save('manifesto.json',{'fontes_sha256':{str(p):sha(p) for p in [SOURCE/'gabarito_revisado.json',SOURCE/'decisoes.json',SOURCE/'pendencias.json',predpath]},'ids_fora_metricas_principais':[],'fonte_complementar':'Decisões expressas no chat: caso 1 aceita Claude; caso 3 mantém gabarito.','arquivos_sha256':{p.name:sha(p) for p in OUT.iterdir()},'preservacao':'Planilha recebida, consolidação anterior e predições não alteradas.'})
print(json.dumps(report,ensure_ascii=False,indent=2))
