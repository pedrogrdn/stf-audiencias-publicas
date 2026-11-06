"""Lê a revisão humana sem modificar a planilha nem os resultados originais."""
import copy
import hashlib
import json
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'revisao_humana_lote_v5'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    if OUT.exists():
        raise SystemExit('Consolidação existente; não sobrescrever.')
    sheet = ROOT / 'revisao_9_casos_lote_v5.xlsx'
    goldpath = ROOT / 'corpus_novo_lote_v5/gabarito_original.json'
    predpath = ROOT / 'claude_novo_lote_v5/predicoes.json'
    originals = json.loads(goldpath.read_text())
    gold = {r['id']: copy.deepcopy(r) for r in originals}
    pred = {r['id']: r for r in json.loads(predpath.read_text())}
    assert len(gold) == len(pred) == 30 and set(gold) == set(pred)
    expected = {i for i,g in gold.items() if not pred[i]['previsto'] or
                g['corpus'] != pred[i]['previsto']['corpus'] or
                (g['corpus'] == 'Incorporar' and g['tipo'] != pred[i]['previsto']['tipo'])}
    wb = openpyxl.load_workbook(sheet, read_only=True, data_only=False)
    ws = wb['Revisão']
    headers = [c.value for c in ws[5]]
    decisions = []
    for row in ws.iter_rows(min_row=6, values_only=True):
        d = dict(zip(headers, row))
        if d.get('ID') is None:
            continue
        i = d['ID']; g = gold[i]; x = pred[i]['previsto'] or {}
        assert i in expected
        assert d['Corpus histórico'] == g['corpus']
        assert d['Tipo histórico'] == (g['tipo'] or 'Não se aplica')
        assert d['Corpus Claude'] == x.get('corpus')
        assert d['Tipo Claude'] == (x.get('tipo') or 'Não se aplica')
        assert d['Decisão'] in ['Manter', 'Alterar'], f'Pendente: {i}'
        corpus = d['Corpus final'] or (g['corpus'] if d['Decisão'] == 'Manter' else None)
        tipo = d['Tipo final'] or (g['tipo'] if d['Decisão'] == 'Manter' else None)
        assert corpus in ['Incorporar', 'Excluir']
        assert (corpus == 'Excluir' and tipo is None) or (corpus == 'Incorporar' and tipo in ['Contexto','Relato','Argumento'])
        if d['Decisão'] == 'Manter':
            assert (corpus, tipo) == (g['corpus'], g['tipo'])
        decisions.append({'caso': d['Caso'], 'id': i, 'decisao': d['Decisão'],
            'original': copy.deepcopy(g), 'corpus': corpus, 'tipo': tipo,
            'comentario': d['Comentário opcional'], 'celulas': f'Revisão!D{ws.min_row + d["Caso"] + 4}:G{ws.min_row + d["Caso"] + 4}'})
        g.update(corpus=corpus, tipo=tipo)
    wb.close()
    assert len(decisions) == len({d['id'] for d in decisions}) == 9
    assert {d['id'] for d in decisions} == expected
    corpus_hits = complete_hits = type_hits = incorporated = 0
    errors = []
    matrix = {}
    for i,g in gold.items():
        x = pred[i]['previsto'] or {}
        ok = x.get('corpus') == g['corpus']
        full = ok and (g['corpus'] == 'Excluir' or x.get('tipo') == g['tipo'])
        corpus_hits += ok; complete_hits += full
        if g['corpus'] == 'Incorporar':
            incorporated += 1; type_hits += full
        k = g['corpus'] + ' -> ' + str(x.get('corpus'))
        matrix[k] = matrix.get(k, 0) + 1
        if not full:
            errors.append({'id': i, 'humano': g, 'claude': x})
    assert (corpus_hits, complete_hits, type_hits, incorporated) == (29,25,17,22)
    prompt = (ROOT / 'corpus_novo_lote_v5/instrucoes.txt').read_text()
    addition = '''
Precisões após revisão humana do lote v5:
- Contexto inclui identificação biográfica, formação, cargo e representação institucional do expositor quando a menção apenas o apresenta. Uma nota puramente identificadora não herda automaticamente o tipo Argumento do texto principal. Distinga-a da nota que atribui uma tese ou fornece evidência mobilizada pelo julgador.
- Uma nota que identifica os expositores que sustentam uma tese enfrentada pelo julgador pode integrar Argumento, inclusive como contraponto. Não é necessário que o julgador concorde com eles. Exija conexão identificável com a discussão e examine o chamado da nota.
- Descrição de resultados ou objetivos de pesquisas científicas é conteúdo substantivo: não a reduza a Contexto só por constar de uma lista. Se a contribuição sustenta uma premissa do julgador, é Argumento; se é apenas exposta, é Relato. Isso não dispensa verificar primeiro a elegibilidade para o corpus.
- Sínteses de falas e informações de notícias sobre a audiência podem permanecer Relato mesmo dentro de um voto. Nem a fonte jornalística, nem a localização no voto, nem uma expressão enfática determinam o engajamento por si.
'''
    assert prompt.count('Responda exclusivamente JSON') == 1
    prompt = prompt.replace('Responda exclusivamente JSON', addition + '\nResponda exclusivamente JSON')
    OUT.mkdir()
    def save(name, value):
        (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    save('decisoes.json', decisions)
    save('gabarito_revisado.json', list(gold.values()))
    report = {'n':30, 'casos_revisados':9, 'alterados':sum(d['decisao']=='Alterar' for d in decisions),
        'corpus_acertos':corpus_hits,'classificacao_completa_acertos':complete_hits,
        'tipo_nos_incorporados':{'n':incorporated,'acertos':type_hits}, 'matriz_corpus':matrix,
        'nota':'Concordância pós-revisão das nove divergências; 21 gabaritos não revistos. Mesmas predições, nenhuma nova execução. Não é validação independente.'}
    save('metricas_pos_revisao.json', report)
    save('divergencias_remanescentes.json', errors)
    save('pendencias_metodologicas.json', {'fhc':{
        'caso_7':'Excluir, AP05-AP_05_ADPF_186-00036, página PDF 182',
        'caso_8':'Incorporar / Argumento, AP05-AP_05_ADPF_186-00038, página PDF 202',
        'situacao':'Decisões válidas por ocorrência. Sem justificativa registrada para generalizar a distinção. Não inferir regra de participação por vídeo, inclusão bibliográfica ou exclusão nominal.'}})
    (OUT/'instrucoes_v6.txt').write_text(prompt, encoding='utf-8')
    save('manifesto.json', {'fontes_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [sheet,goldpath,predpath,ROOT/'corpus_novo_lote_v5/instrucoes.txt']},
        'arquivos_sha256':{p.name:digest(p) for p in OUT.iterdir()},
        'estado':'Instruções v6 preparadas, não executadas e sem alteração das instruções históricas ou da planilha.'})
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert digest(sheet) == json.loads((OUT/'manifesto.json').read_text())['fontes_sha256'][sheet.name]

if __name__ == '__main__':
    main()
