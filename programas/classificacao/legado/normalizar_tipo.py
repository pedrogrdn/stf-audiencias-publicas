"""Reavaliação exclusivamente offline; não altera previsões originais."""
import hashlib
import json
import re
from pathlib import Path

LABELS = ('Contexto', 'Relato', 'Argumento', 'Indeterminado')

def parse_tipo(raw, stop_reason='end_turn'):
    if stop_reason != 'end_turn' or not isinstance(raw, str):
        return None
    text = raw.strip()
    fence = re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    if fence:
        text = fence.group(1)
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError('Chave duplicada')
            obj[key] = value
        return obj
    try:
        obj = json.loads(text, object_pairs_hook=unique)
        if isinstance(obj, dict) and set(obj) == {'tipo'} and obj['tipo'] in LABELS:
            return obj['tipo']
    except (ValueError, TypeError):
        pass
    return None

def metrics(rows, field):
    result = {'n': len(rows), 'acertos': sum(r['humano'] == r[field] for r in rows),
              'invalidas': sum(r[field] is None for r in rows), 'por_categoria': {}}
    for label in LABELS[:3]:
        support = sum(r['humano'] == label for r in rows)
        predicted = sum(r[field] == label for r in rows)
        tp = sum(r['humano'] == r[field] == label for r in rows)
        result['por_categoria'][label] = {'suporte': support, 'acertos': tp,
            'precisao': tp / predicted if predicted else None,
            'recall': tp / support if support else None,
            'f1': 2 * tp / (support + predicted) if support + predicted else None}
    return result

def main():
    root = Path(__file__).resolve().parent
    out = root / 'normalizacao_v1'
    out.mkdir(exist_ok=True)
    summary = {}
    reference = None
    for name, folder in [('local_base', 'tipo_v3/avaliacao_base'),
                         ('local_ajustado', 'tipo_v3/avaliacao_ajustado'),
                         ('claude', 'claude_tipo_v1')]:
        source = root / folder / 'predicoes.json'
        rows = json.loads(source.read_text())
        ids = {r['id']: r['humano'] for r in rows}
        if reference is None:
            reference = ids
        assert ids == reference and len(rows) == 11
        for row in rows:
            row['ia_normalizada'] = parse_tipo(row['saida_bruta'], row.get('stop_reason', 'end_turn'))
        summary[name] = {'origem': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                         'estrita_salva': metrics(rows, 'ia'), 'normalizada': metrics(rows, 'ia_normalizada')}
        (out / f'{name}_predicoes.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    (out / 'metricas.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    for name, result in summary.items():
        print(name, result['normalizada'])

if __name__ == '__main__':
    main()
