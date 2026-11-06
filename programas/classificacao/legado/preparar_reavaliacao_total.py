"""Prepara os 300 registros, sem API e sem alterar experimentos anteriores."""
import copy
import json
from collections import Counter
import validar_corpus as helper

ROOT = helper.ROOT
DATA = ROOT / 'reavaliacao_total_v6_1'
NOTE = ('Reavaliação da base de desenvolvimento completa, incluindo casos já usados em ajustes '
        'e casos ainda não enviados ao Claude. Não é validação independente. Gabarito histórico '
        'com revisões humanas registradas sobrepostas; tipos sem decisão humana não são inventados. '
        'Recortes originais, sem expansão de PDFs. Sem classificação de participantes ou teor.')

def main():
    if DATA.exists():
        raise SystemExit('Preparação existente; não sobrescrever.')
    records = json.loads((ROOT/'registros.json').read_text())
    allrows = [r for rows in records.values() for r in rows]
    assert len(allrows) == len({r['id'] for r in allrows}) == 300
    gold = {r['id']:{k:r[k] for k in ['id','audiencia','corpus','tipo']} for r in allrows}
    sources = ['revisao_humana_v3/decisoes_corpus.json',
        'multiaudiencias_revisao_v2/decisoes_corpus.json',
        'ajuste_corpus_v2/gabarito_original.json',
        'decisoes_corpus_pos_v2.json',
        'corpus_novo_lote_v4/gabarito_v3_revisado.json',
        'corpus_novo_lote_v5/gabarito_v4_revisado.json',
        'revisao_humana_lote_v5/gabarito_revisado.json']
    audit = []
    for name in sources:
        data = json.loads((ROOT/name).read_text())
        rows = data['decisoes'] if isinstance(data,dict) else data
        for r in rows:
            assert r['id'] in gold
            g = gold[r['id']]; before = copy.deepcopy(g)
            g['corpus'] = r['corpus']
            if g['corpus'] == 'Excluir':
                g['tipo'] = None
            elif 'tipo' in r:
                g['tipo'] = r['tipo']
            elif before['corpus'] != 'Incorporar':
                g['tipo'] = None
            audit.append({'id':r['id'],'fonte':name,'antes':before,'depois':copy.deepcopy(g)})
    promptpath = ROOT/'revisao_humana_lote_v5/instrucoes_v6_1.txt'
    prompt = promptpath.read_text()
    inputs = [{'id':r['id'],'system':prompt,'messages':[{'role':'user','content':json.dumps(r['payload'],ensure_ascii=False)}]} for r in allrows]
    prior = {r['id'] for p in ROOT.glob('claude_*/predicoes.json') for r in json.loads(p.read_text())}
    DATA.mkdir()
    helper.save(DATA/'entradas.json',inputs)
    helper.save(DATA/'gabarito_original.json',[gold[r['id']] for r in allrows])
    helper.save(DATA/'historico_revisoes.json',audit)
    (DATA/'instrucoes.txt').write_text(prompt)
    helper.save(DATA/'manifesto.json',{'n':300,'finalidade':NOTE,
        'sha256':{n:helper.digest(DATA/n) for n in ['entradas.json','gabarito_original.json','historico_revisoes.json','instrucoes.txt']},
        'fontes_sha256':{n:helper.digest(ROOT/n) for n in ['registros.json',*sources,'revisao_humana_lote_v5/instrucoes_v6_1.txt']},
        'audiencias':dict(Counter(r['audiencia'] for r in allrows)),
        'categorias':dict(Counter(str((r['corpus'],r['tipo'])) for r in gold.values())),
        'ids_ja_avaliados':sorted(set(gold)&prior),
        'incorporados_sem_tipo':[r['id'] for r in gold.values() if r['corpus']=='Incorporar' and r['tipo'] is None],
        'unidade':'Todos os 300 IDs originais, sem remover menções textualmente repetidas. Não interpretar como 300 observações independentes.'})
    helper.DATA=DATA; helper.load()
    print(json.dumps(json.loads((DATA/'manifesto.json').read_text())['categorias'],ensure_ascii=False))
    print('300 casos preparados offline; nenhuma API chamada.')

if __name__ == '__main__':
    main()
