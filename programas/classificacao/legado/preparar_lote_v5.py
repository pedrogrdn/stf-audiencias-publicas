"""Novo diagnóstico offline, focado nos incorporados restantes."""
import json
from collections import Counter, defaultdict
import validar_corpus as runner

ROOT = runner.ROOT
DATA = ROOT / 'corpus_novo_lote_v5'
NOTE = ('Diagnóstico com gabarito histórico: 19 Argumentos, 4 Relatos, 7 exclusões, '
        'nenhum Contexto. Casos ainda não avaliados pelo Claude por ID ou menção '
        'normalizada, oriundos do treino local. Não é validação independente. '
        'Composição diferente dos lotes anteriores; porcentagens globais não diretamente comparáveis.')
ADDITION = '''
Critérios adicionais para distinguir Relato de Argumento:
Avalie a função da contribuição na sequência do raciocínio, e não sua forma de citação. Quando o julgador desenvolve uma premissa factual ou normativa e convoca a declaração do expositor como evidência, fundamento, explicação ou contraponto dessa premissa, classifique Argumento. Não é necessário que ele diga expressamente que concorda ou que a fala mudou sua decisão. Expressões como “donde”, “nesse sentido” ou “conforme” podem sinalizar conexão, mas nunca determinam o rótulo sozinhas. A conexão substantiva precisa estar demonstrada no contexto disponível. A mera enumeração ou síntese de posições continua Relato; estar em um voto não basta para Argumento.
Para nota de rodapé ou nota final, a unidade interpretativa inclui a nota e o parágrafo que a chama. Uma nota descritiva pode exercer função argumentativa ao fundamentar uma proposição do julgador nesse parágrafo. Não use notas vizinhas como substituto do chamado. Se o chamado não estiver nos recortes e for necessário para distinguir Relato de Argumento, preserve Incorporar quando seguro e use tipo Indeterminado. Não presuma Relato apenas porque a nota reproduz uma fala, nem Argumento apenas porque ela cita um expositor. Não há acesso autônomo ao PDF; não simule consulta às páginas ausentes.
'''

def main():
    if DATA.exists():
        raise SystemExit('Lote v5 existente; não sobrescrever.')
    source = ROOT / 'registros.json'
    records = json.loads(source.read_text())
    prior_files = sorted(ROOT.glob('claude_*/predicoes.json'))
    prior = {r['id'] for p in prior_files for r in json.loads(p.read_text())}
    norm = lambda s: ' '.join(s.casefold().split())
    seen = {norm(r['payload']['mencao']) for rows in records.values()
            for r in rows if r['id'] in prior}
    for p in ROOT.glob('*/entradas.json'):
        for r in json.loads(p.read_text()):
            if r['id'] in prior:
                seen.add(norm(json.loads(r['messages'][0]['content'])['mencao']))
    chosen = []
    for corpus, tipo, count in [('Incorporar', 'Argumento', 19),
                                ('Incorporar', 'Relato', 4), ('Excluir', None, 7)]:
        groups = defaultdict(list)
        for r in sorted(records['treino'], key=lambda r: r['id']):
            if r['id'] not in prior and r['corpus'] == corpus and r['tipo'] == tipo:
                groups[int(r['audiencia'])].append(r)
        n = 0
        while n < count:
            progress = False
            for ap in sorted(groups):
                while groups[ap]:
                    r = groups[ap].pop(0)
                    key = norm(r['payload']['mencao'])
                    if key in seen:
                        continue
                    chosen.append(r); seen.add(key); n += 1; progress = True
                    break
                if n == count:
                    break
            if not progress:
                raise ValueError(f'Casos únicos insuficientes: {corpus}/{tipo}')
    chosen.sort(key=lambda r: r['id'])
    assert len(chosen) == len({r['id'] for r in chosen}) == 30
    assert not {r['id'] for r in chosen} & prior
    old = (ROOT / 'corpus_novo_lote_v4/instrucoes.txt').read_text()
    prompt = old.replace('Responda exclusivamente JSON', ADDITION + '\nResponda exclusivamente JSON')
    inputs = [{'id': r['id'], 'system': prompt, 'messages': [
        {'role': 'user', 'content': json.dumps(r['payload'], ensure_ascii=False)}]} for r in chosen]
    gold = [{k: r[k] for k in ['id', 'audiencia', 'corpus', 'tipo']} for r in chosen]
    revised = json.loads((ROOT / 'corpus_novo_lote_v4/gabarito_original.json').read_text())
    decisions = [
        {'id': 'AP01-AP_01_ADI_3510-00009', 'corpus': 'Incorporar', 'tipo': 'Argumento', 'motivo': 'Pesquisador manteve a função argumentativa.'},
        {'id': 'AP03-AP_03_ADPF_054-00132', 'corpus': 'Incorporar', 'tipo': 'Argumento', 'motivo': 'Pesquisador conferiu o chamado da nota 77 na página PDF 60 e identificou função argumentativa.'},
        {'id': 'AP14-AP_14_ADI_5035-00036', 'corpus': 'Excluir', 'tipo': None, 'motivo': 'Pesquisador aplicou a regra de exclusão de partes.'},
    ]
    mapping = {r['id']: r for r in revised}
    for d in decisions:
        mapping[d['id']].update(corpus=d['corpus'], tipo=d['tipo'])
    predictions = json.loads((ROOT / 'claude_novo_lote_v4/predicoes.json').read_text())
    corpus_hits = full_hits = type_hits = incorporated = 0
    for r in predictions:
        g, x = mapping[r['id']], r['previsto'] or {}
        ok = g['corpus'] == x.get('corpus')
        complete = ok and (g['corpus'] == 'Excluir' or g['tipo'] == x.get('tipo'))
        corpus_hits += ok; full_hits += complete
        if g['corpus'] == 'Incorporar':
            incorporated += 1; type_hits += complete
    assert (corpus_hits, full_hits, type_hits, incorporated) == (30, 28, 12, 14)
    DATA.mkdir()
    runner.save(DATA / 'entradas.json', inputs)
    runner.save(DATA / 'gabarito_original.json', gold)
    (DATA / 'instrucoes.txt').write_text(prompt)
    runner.save(DATA / 'gabarito_v4_revisado.json', revised)
    runner.save(DATA / 'revisao_v4.json', {
        'origem': 'Decisões expressas do pesquisador na conversa; apenas três divergências revistas.',
        'decisoes': decisions, 'n': 30, 'corpus_acertos': corpus_hits,
        'classificacao_completa_acertos': full_hits, 'incorporados_revisados': incorporated,
        'tipo_acertos_nos_incorporados': type_hits,
        'nota': 'Pós-revisão: 28/30 completos inclui 16 exclusões; tipo entre incorporados é 12/14 (85,7%). Não é validação independente.'})
    runner.save(DATA / 'manifesto.json', {
        'n': 30, 'finalidade': NOTE,
        'sha256': {n: runner.digest(DATA / n) for n in ['entradas.json', 'gabarito_original.json',
            'instrucoes.txt', 'gabarito_v4_revisado.json', 'revisao_v4.json']},
        'fonte_sha256': runner.digest(source),
        'predicoes_anteriores_sha256': {str(p.relative_to(ROOT)): runner.digest(p) for p in prior_files},
        'audiencias': dict(Counter(r['audiencia'] for r in chosen)),
        'selecao': 'Todos os 23 incorporados inéditos restantes no treino local e 7 exclusões; rodízio por audiência dentro da categoria.',
        'limites': ['Sem exemplos de Contexto. Não mede desempenho nessa categoria.',
                   'Gabarito histórico pode divergir das regras atuais.',
                   'Recortes originais preservados: chamados de notas podem estar ausentes. Nenhum contexto novo foi extraído de PDFs.',
                   'Não houve controle de equivalência semântica nem separação por audiência inédita.']})
    runner.DATA = DATA
    runner.load()
    print('30 casos preparados e verificados offline. Nenhuma API chamada.')
    print('Audiências:', dict(Counter(r['audiencia'] for r in chosen)))

if __name__ == '__main__':
    main()
