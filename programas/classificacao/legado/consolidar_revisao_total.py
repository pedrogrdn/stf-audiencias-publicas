"""Consolida a revisão recebida, preservando planilhas e predições originais."""
import copy
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve().parents[3] / 'entradas_externas_migracao' / 'revisao_reavaliacao_300.xlsx'
OUT = ROOT / 'revisao_humana_total_20261013'
BASE = ROOT / 'reavaliacao_total_conciliada_v6_1'
PRED = ROOT / 'claude_reavaliacao_total_conciliada_v6_1/predicoes.json'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not OUT.exists(), 'Consolidação já existe; não sobrescrever.'
    before = {str(p): sha(p) for p in [SOURCE, BASE/'gabarito_original.json', PRED, ROOT/'revisao_reavaliacao_300.xlsx']}
    original = {r['id']: r for r in read(BASE/'gabarito_original.json')}
    gold = copy.deepcopy(original)
    pred = {r['id']: r['previsto'] for r in read(PRED)}
    inputs = {r['id']: json.loads(r['messages'][0]['content']) for r in read(BASE/'entradas.json')}
    oldpending = {r['id'] for r in read(BASE/'pendencias_partes.json')}
    expected = {i for i,g in gold.items() if i in oldpending or g['corpus'] != pred[i]['corpus'] or (g['corpus']=='Incorporar' and g['tipo'] != pred[i]['tipo'])}
    w = openpyxl.load_workbook(SOURCE, read_only=True, data_only=False)
    s = w['Revisão']; headers = [c.value for c in s[5]]
    decisions = []; pending = []; seen = set()
    for rownum, row in enumerate(s.iter_rows(min_row=6, values_only=True), 6):
        d = dict(zip(headers,row)); i = d.get('ID')
        if i is None: continue
        assert i in expected and i not in seen, i
        seen.add(i); g = gold[i]; x = pred[i]; p = inputs[i]
        assert d['Alvo']==p['alvos'] and d['Frase / menção']==p['mencao'], i
        assert d['Corpus referência']==g['corpus'], i
        assert d['Tipo referência']==(g['tipo'] or ('Não definido' if g['corpus']=='Incorporar' else 'Não se aplica')), i
        assert d['Corpus Claude']==x['corpus'] and d['Tipo Claude']==(x['tipo'] or 'Não se aplica'), i
        record = {'caso':d['Caso'],'id':i,'celulas':f'Revisão!D{rownum}:G{rownum}','decisao':d['Decisão'],'comentario':d['Comentário opcional'],'original':copy.deepcopy(g),'claude':x}
        if d['Decisão']=='Conferir contexto':
            assert not d['Corpus final'] and not d['Tipo final']
            record.update(alvo=p['alvos'],frase=p['mencao'],audiencia=p['audiencia'],processo=p['processo'],pagina_pdf=p['pagina_pdf'])
            pending.append(record); decisions.append(record); continue
        assert d['Decisão'] in ['Manter','Alterar'], i
        c = d['Corpus final'] or (g['corpus'] if d['Decisão']=='Manter' else None)
        t = d['Tipo final'] or (g['tipo'] if d['Decisão']=='Manter' else None)
        assert c in ['Incorporar','Excluir'] and ((c=='Excluir' and t is None) or (c=='Incorporar' and t in ['Contexto','Relato','Argumento'])), i
        if d['Decisão']=='Manter': assert (c,t)==(g['corpus'],g['tipo']), i
        record.update(corpus=c,tipo=t); decisions.append(record)
        g.update(corpus=c,tipo=t)
    w.close()
    assert seen==expected and len(seen)==51
    unresolved = {d['id'] for d in pending}
    eligible = [g for i,g in gold.items() if i not in unresolved]
    def scores(gs):
        matrix=Counter(); ch=fh=th=inc=0; errors=[]
        for g in gs:
            x=pred[g['id']]; ok=g['corpus']==x['corpus']; full=ok and (g['corpus']=='Excluir' or g['tipo']==x['tipo'])
            ch+=ok; fh+=full; inc+=g['corpus']=='Incorporar'; th+=full and g['corpus']=='Incorporar'
            matrix[g['corpus']+' -> '+x['corpus']]+=1
            if not full: errors.append({'id':g['id'],'humano':g,'claude':x})
        return {'n':len(gs),'corpus_acertos':ch,'classificacao_completa_acertos':fh,'tipo_nos_incorporados':{'n':inc,'acertos':th},'matriz_corpus':dict(matrix)},errors
    report, errors = scores(eligible)
    report.update(casos_recebidos=51,decisoes_concluidas=49,decisoes=dict(Counter(d['decisao'] for d in decisions)),pendencias=len(pending),pendencias_anteriores_resolvidas=4,
        nota='Concordância pós-revisão das divergências nas mesmas predições. 249 casos não foram revistos nesta etapa. Dois casos pendentes fora das métricas principais. Não é validação independente nem nova execução do modelo.')
    assert len(eligible)+len(pending)==300
    assert all(sha(Path(p))==v for p,v in before.items())
    OUT.mkdir()
    shutil.copy2(SOURCE, OUT/'revisao_recebida.xlsx')
    def save(n,o): (OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
    save('decisoes.json',decisions)
    save('gabarito_revisado.json',list(gold.values()))
    save('pendencias.json',pending)
    save('metricas_pos_revisao.json',report)
    save('divergencias_remanescentes.json',errors)
    save('manifesto.json',{'data_consolidacao':'2026-10-13','fontes_sha256':before,'ids_fora_metricas_principais':sorted(unresolved),'observacao':'Gabaritos dos dois pendentes preservados provisoriamente. Exclusões comentadas como Interessado aplicadas apenas às ocorrências decididas, sem regra geral. Nenhuma API chamada.','arquivos_sha256':{p.name:sha(p) for p in OUT.iterdir()}})
    assert sha(OUT/'revisao_recebida.xlsx')==before[str(SOURCE)]
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(pending,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
