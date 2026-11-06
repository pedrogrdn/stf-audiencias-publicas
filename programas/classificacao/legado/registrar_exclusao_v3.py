"""Registra exclusão autorizada; reavalia respostas existentes, sem API."""
import hashlib
import json
from pathlib import Path
from normalizar_tipo import metrics

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'revisao_humana_v2'
OUT = ROOT / 'revisao_humana_v3'
EXCLUDED = 'AP38-AP_38_RE_1057258-00011'

def main():
    if OUT.exists():
        raise SystemExit('Versão já existe; nada sobrescrito.')
    originals = {p:p.read_bytes() for p in SOURCE.glob('*.json')}
    ids = json.loads((SOURCE/'ids_rotulos.json').read_text())['valid']
    assert len(ids) == 11 and sum(r['id'] == EXCLUDED for r in ids) == 1
    active = [r for r in ids if r['id'] != EXCLUDED]
    files = {'ids_rotulos.json':{'valid':active},
        'decisoes_corpus.json': [{'id':r['id'], 'corpus':'Excluir' if r['id']==EXCLUDED else 'Incorporar',
            'tipo':None if r['id']==EXCLUDED else r['tipo']} for r in ids],
        'alteracoes.json': {'origem':'Confirmação expressa do usuário nesta conversa',
            'versao_anterior':'revisao_humana_v2',
            'alteracoes':[{'id':EXCLUDED,'antes':{'corpus':'Incorporar','tipo':'Argumento'},
                'depois':{'corpus':'Excluir','tipo':None},
                'motivo':'Usuário confirmou confusão entre notas 1 e 2; a nota 2 lista amici curiae.'}],
            'fontes_sha256':{str(p):hashlib.sha256(b).hexdigest() for p,b in originals.items()},
            'nota':'Versão vigente do gabarito de desenvolvimento. Arquivos históricos, planilha original, treino e teste reservado preservados.'}}
    summary = {}
    for name in ['claude_tipo_v1', 'claude_engajamento_v1']:
        rows = json.loads((SOURCE/(name+'_predicoes.json')).read_text())
        kept = [r for r in rows if r['id'] != EXCLUDED]
        assert len(kept) == 10 and {r['id'] for r in kept} == {r['id'] for r in active}
        files[name+'_predicoes.json'] = kept
        summary[name] = metrics(kept,'ia')
        summary[name]['divergencias'] = [r['id'] for r in kept if r['humano'] != r['ia']]
    files['metricas.json'] = summary
    OUT.mkdir()
    for name,obj in files.items():
        (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
    assert all(p.read_bytes()==b for p,b in originals.items())
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
