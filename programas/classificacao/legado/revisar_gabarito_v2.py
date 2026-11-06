"""Aplica exclusivamente as duas correções humanas autorizadas, offline."""
import hashlib
import json
from pathlib import Path
from normalizar_tipo import metrics, parse_tipo

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'revisao_humana_v2'
CHANGES = {'AP38-AP_38_RE_1057258-00032', 'AP38-AP_38_RE_1037396-00169'}

def main():
    if OUT.exists():
        raise SystemExit('Versão já existe; nenhum arquivo sobrescrito.')
    sources = [ROOT/'tipo_v3/ids_rotulos.json', ROOT/'claude_tipo_v1/predicoes.json',
               ROOT/'claude_engajamento_v1/predicoes.json']
    original = {p: p.read_bytes() for p in sources}
    ids = json.loads(original[sources[0]])['valid']
    assert len(ids) == 11 and len({r['id'] for r in ids}) == 11
    revised = []
    for row in ids:
        row = dict(row)
        if row['id'] in CHANGES:
            assert row['tipo'] == 'Argumento'
            row['tipo'] = 'Relato'
        revised.append(row)
    assert sum(a != b for a, b in zip(ids, revised)) == 2
    gold = {r['id']:r['tipo'] for r in revised}
    outputs = {}
    summary = {}
    for source in sources[1:]:
        rows = json.loads(original[source])
        assert {r['id'] for r in rows} == set(gold) and len(rows) == 11
        updated = []
        for row in rows:
            updated.append(dict(row, humano_original=row['humano'], humano=gold[row['id']],
                ia=parse_tipo(row['saida_bruta'], row.get('stop_reason', 'end_turn'))))
        name = source.parent.name
        summary[name] = metrics(updated, 'ia')
        summary[name]['divergencias'] = [r['id'] for r in updated if r['humano'] != r['ia']]
        outputs[name+'_predicoes.json'] = updated
    docs = json.loads((ROOT/'contexto_v2/indice_documentos.json').read_text())
    pages = docs['acordaos/AP_38_RE_1057258.pdf']
    outputs['evidencias_nota_brasilcon.json'] = {'fonte':'contexto_v2/indice_documentos.json',
        'arquivo':'acordaos/AP_38_RE_1057258.pdf',
        'paginas':[{'pagina_pdf':n,'texto':pages[n-1]} for n in [242,243,310,311]],
        'conclusao':'Chamado [2] no parágrafo 10 informa admissão de amici curiae. A nota lista instituições. Não foi comprovada, nessa ligação, a remissão a uma contribuição usada como argumento. Rótulo humano Argumento preservado; conexão substantiva pendente.'}
    outputs['ids_rotulos.json'] = {'valid':revised}
    outputs['metricas.json'] = summary
    outputs['alteracoes.json'] = {'data':'2026-09-13','origem':'Revisão expressa do usuário nesta conversa',
        'alteracoes':[{'id':i,'antes':'Argumento','depois':'Relato',
          'motivo':'Síntese das posições dos participantes, sem relação com a argumentação para a decisão.'} for i in sorted(CHANGES)],
        'mantidos':{'AP38-AP_38_RE_1057258-00011':'Argumento','AP38-AP_38_RE_1037396-00083':'Contexto'},
        'fontes_sha256':{str(p):hashlib.sha256(b).hexdigest() for p,b in original.items()},
        'nota':'Reavaliação pós-inspeção de desenvolvimento, não melhora do modelo nem teste independente. Nenhum dado de treino, teste reservado, planilha original ou execução anterior foi alterado.'}
    OUT.mkdir()
    for name, value in outputs.items():
        (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2))
    assert all(p.read_bytes() == b for p,b in original.items())
    for name, value in summary.items():
        print(name, value)

if __name__ == '__main__':
    main()
