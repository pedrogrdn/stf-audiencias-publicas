"""Consolida decisões confirmadas na conversa e prepara diagnóstico offline."""
import json
from collections import Counter, defaultdict
import validar_corpus as runner

ROOT = runner.ROOT
DATA = ROOT / 'corpus_novo_lote_v4'
NOTE = ('Novo lote diagnóstico não avaliado anteriormente pelo Claude por ID ou menção '
        'normalizada. Origem: treino local. Gabarito histórico, não revisto previamente '
        'pelas regras atuais. Não é teste independente da pesquisa. Apenas um Contexto.')
ADDITION = '''
Esclarecimentos decorrentes da revisão humana do lote anterior:
- Distinga a voz do julgador da alegação de uma parte que ele está reproduzindo. Exclua a mera reprodução, pelo julgador, de uma alegação de requerente ou requerido que cita uma fala da audiência, mesmo quando o participante citado não seja parte. A remissão expressa à audiência não elimina essa exclusão. Não aplique essa regra a uma retomada própria e identificável do julgador da contribuição da audiência. Se a cadeia de atribuição não puder ser determinada, use Indeterminado.
- Leia a frase destacada junto à continuação disponível. Se a frase seguinte retoma o mesmo participante por cargo, instituição ou pronome e apresenta sua posição na audiência, essa continuidade integra a classificação da menção: pode ser Relato, mesmo quando a primeira frase isolada só informa participação. Exija correferência identificável; não transfira conteúdo de outro participante ou de discussão vizinha. Não invente uma continuação ausente.
'''

def main():
    if DATA.exists():
        raise SystemExit('Lote v4 já existe; não sobrescrever.')
    # Transcrição das oito decisões da planilha, conferidas e confirmadas na conversa.
    decisions = [
        (1, 'AP01-AP_01_ADI_3510-00016', 'Alterar', 'Incorporar', 'Argumento'),
        (2, 'AP03-AP_03_ADPF_054-00047', 'Manter', 'Excluir', None),
        (3, 'AP12-AP_12_ADI_4650-00007', 'Alterar', 'Excluir', None),
        (4, 'AP12-AP_12_ADI_4650-00017', 'Alterar', 'Excluir', None),
        (5, 'AP14-AP_14_ADI_5035-00006', 'Alterar', 'Excluir', None),
        (6, 'AP14-AP_14_ADI_5035-00013', 'Manter', 'Incorporar', 'Relato'),
        (7, 'AP15-AP_15_ADI_5062-00038', 'Alterar', 'Incorporar', 'Relato'),
        (8, 'AP32-AP_32_ADPF_635-00256', 'Alterar', 'Excluir', None),
    ]
    gold_path = ROOT / 'corpus_novo_lote_v3/gabarito_original.json'
    revised = json.loads(gold_path.read_text())
    by_id = {r['id']: r for r in revised}
    for _, ident, _, corpus, tipo in decisions:
        by_id[ident].update(corpus=corpus, tipo=tipo)
    predictions = json.loads((ROOT / 'claude_novo_lote_v3/predicoes.json').read_text())
    corpus_hits = full_hits = 0
    for r in predictions:
        g, x = by_id[r['id']], r['previsto'] or {}
        ok = g['corpus'] == x.get('corpus')
        corpus_hits += ok
        full_hits += ok and (g['corpus'] == 'Excluir' or g['tipo'] == x.get('tipo'))
    assert (corpus_hits, full_hits) == (29, 28)

    source = ROOT / 'registros.json'
    records = json.loads(source.read_text())
    prior_files = sorted(ROOT.glob('claude_*/predicoes.json'))
    prior = {r['id'] for p in prior_files for r in json.loads(p.read_text())}
    norm = lambda s: ' '.join(s.casefold().split())
    seen = {norm(r['payload']['mencao']) for rows in records.values()
            for r in rows if r['id'] in prior}
    # Inclui textos efetivamente enviados, mesmo se não estiverem em registros.json.
    for p in ROOT.glob('*/entradas.json'):
        for r in json.loads(p.read_text()):
            if r['id'] in prior:
                seen.add(norm(json.loads(r['messages'][0]['content'])['mencao']))
    chosen = []
    for corpus, tipo, count in [('Excluir', None, 15), ('Incorporar', 'Contexto', 1),
                                ('Incorporar', 'Relato', 7), ('Incorporar', 'Argumento', 7)]:
        groups = defaultdict(list)
        for r in sorted(records['treino'], key=lambda r: r['id']):
            if r['id'] not in prior and r['corpus'] == corpus and r['tipo'] == tipo:
                groups[int(r['audiencia'])].append(r)
        n = 0
        while n < count:
            progressed = False
            for ap in sorted(groups):
                while groups[ap]:
                    r = groups[ap].pop(0)
                    key = norm(r['payload']['mencao'])
                    if key in seen:
                        continue
                    chosen.append(r); seen.add(key); n += 1; progressed = True
                    break
                if n == count:
                    break
            if not progressed:
                raise ValueError(f'Exemplos únicos insuficientes: {corpus}/{tipo}')
    chosen.sort(key=lambda r: r['id'])
    assert len(chosen) == len({r['id'] for r in chosen}) == 30
    assert not {r['id'] for r in chosen} & prior
    old_prompt = (ROOT / 'corpus_novo_lote_v3/instrucoes.txt').read_text()
    prompt = old_prompt.replace('Somente para Incorporar, classifique tipo:',
                                ADDITION + '\nSomente para Incorporar, classifique tipo:')
    inputs = [{'id': r['id'], 'system': prompt, 'messages': [
        {'role': 'user', 'content': json.dumps(r['payload'], ensure_ascii=False)}]} for r in chosen]
    gold = [{k: r[k] for k in ['id', 'audiencia', 'corpus', 'tipo']} for r in chosen]
    DATA.mkdir()
    runner.save(DATA / 'entradas.json', inputs)
    runner.save(DATA / 'gabarito_original.json', gold)
    (DATA / 'instrucoes.txt').write_text(prompt)
    runner.save(DATA / 'gabarito_v3_revisado.json', revised)
    runner.save(DATA / 'revisao_v3.json', {
        'fonte': 'Decisões da planilha conferidas na conversa e autorizadas pelo pesquisador',
        'planilha_sha256': runner.digest(ROOT / 'revisao_8_casos_novo_lote.xlsx'),
        'gabarito_original_sha256': runner.digest(gold_path),
        'decisoes': [dict(zip(['caso', 'id', 'decisao', 'corpus', 'tipo'], d)) for d in decisions],
        'n': 30, 'revisados': 8, 'corpus_acertos': corpus_hits,
        'classificacao_completa_acertos': full_hits,
        'nota': 'Concordância pós-revisão de divergências. Outros 22 gabaritos preservados. Não é nova validação.'})
    runner.save(DATA / 'manifesto.json', {
        'n': 30, 'finalidade': NOTE,
        'sha256': {n: runner.digest(DATA / n) for n in [
            'entradas.json', 'gabarito_original.json', 'instrucoes.txt',
            'gabarito_v3_revisado.json', 'revisao_v3.json']},
        'fonte_sha256': runner.digest(source),
        'predicoes_anteriores_sha256': {str(p.relative_to(ROOT)): runner.digest(p) for p in prior_files},
        'audiencias': dict(Counter(r['audiencia'] for r in chosen)),
        'selecao': '15 Excluir, 1 Contexto, 7 Relato, 7 Argumento; rodízio por audiência dentro de cada grupo.',
        'contexto': 'Recortes originais preservados. Sem consulta autônoma aos PDFs. Sem controle de equivalência semântica entre passagens.',
        'limites': ['Gabarito histórico pode divergir das regras atuais.',
                   'Apenas um Contexto: não permite estimar desempenho robusto nessa categoria.',
                   'Origem no treino local; audiências já utilizadas em desenvolvimento.']})
    runner.DATA = DATA
    runner.load()
    print('30 casos preparados offline. Nenhuma chamada à API.')
    print('Audiências:', dict(Counter(r['audiencia'] for r in chosen)))

if __name__ == '__main__':
    main()
