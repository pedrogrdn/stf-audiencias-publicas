"""Versão metodológica posterior à revisão dos 60 casos. Preparação sem API."""
import json
import sys
import validar_corpus as runner

ROOT=runner.ROOT
DATA=ROOT/'ajuste_corpus_v2'
NOTE='Ajuste nos mesmos 60 casos já revisados; não é validação independente. Corpus comparado à revisão humana; tipos históricos não foram revistos nesta etapa e são apenas diagnósticos.'
RULES='''Regras de incorporação, na ordem abaixo:
1. Exclua contribuições de requerentes e requeridos, mesmo apresentadas na audiência. Terceiros e amici curiae continuam elegíveis. Identifique a posição processual por evidência, nunca pelo tipo de instituição.
2. Incorpore menções à realização, organização ou participação na audiência específica estudada e contribuições substantivas nela apresentadas.
3. Escolha metodológica adicional: incorpore citações de livros e artigos de participantes confirmados, ainda que não haja remissão expressa à audiência. Não exija comprovar que a mesma posição foi defendida oralmente. Isso não demonstra influência causal da audiência nem identidade de posições. Não invente a participação: coincidência do nome com alvo de busca não basta. Para a AP 19, a participação de Édis Milaré foi confirmada pelo pesquisador. Essa confirmação não se estende automaticamente a homônimos ou outras pessoas.
4. A exceção bibliográfica não se estende à simples autoria de projeto de lei. Exclua menções que apenas atribuem projeto legislativo a alguém, mesmo sendo participante. Distinga essa referência de uma contribuição efetivamente apresentada na audiência.
5. Exclua referências a outras audiências, a atos processuais descritos na legislação e a audiências que o CNJ deveria realizar para implementação normativa. Não exclua toda menção ao CNJ: sua participação na audiência estudada continua elegível.
6. Incorpore listas de participantes da audiência quando o contexto identificar esse vínculo. Não confunda com listas de amici curiae, habilitações processuais ou outras relações de entidades. O nome de uma entidade, sozinho, não resolve a origem da lista. Para notas, examine seu chamado.
7. Exclua alegações ou petições sem vínculo com a audiência, ressalvada a exceção bibliográfica expressa acima. Se faltar informação decisiva sobre origem de uma lista, identidade, participação ou posição processual, use Indeterminado, não exclusão automática.
'''

def prepare():
    from openpyxl import load_workbook
    if DATA.exists():raise SystemExit('Preparação existente; não sobrescrever.')
    inputs=json.loads((ROOT/'validacao_reservada_v1/entradas.json').read_text())
    old=json.loads((ROOT/'validacao_reservada_v1/gabarito_original.json').read_text())
    book=ROOT/'revisao_cega_corpus_60.xlsx'
    sheet=load_workbook(book,data_only=True)['Revisão']
    headers=[c.value for c in sheet[4]]
    decisions={}
    for row in sheet.iter_rows(min_row=5,max_row=64,values_only=True):
        r=dict(zip(headers,row));assert r['Decisão'] in ['Incorporar','Excluir']
        assert r['ID'] not in decisions
        decisions[r['ID']]=r['Decisão']
    assert len(decisions)==60 and set(decisions)=={r['id'] for r in inputs}
    # Preserve os tipos históricos, sem atribuir tipo novo a uma incorporação revista.
    assert all(decisions[r['id']]==r['corpus'] for r in old), 'Corpus mudou: revisar cobertura dos tipos antes de preparar.'
    gold=[dict(r,corpus=decisions[r['id']]) for r in old]
    original=inputs[0]['system'];start=original.index('Incorporar exige');end=original.index('Somente para Incorporar')
    prompt=original[:start]+RULES+original[end:]
    for r in inputs:r['system']=prompt
    DATA.mkdir();runner.save(DATA/'entradas.json',inputs);runner.save(DATA/'gabarito_original.json',gold)
    (DATA/'instrucoes.txt').write_text(prompt)
    runner.save(DATA/'manifesto.json',{'sha256':{n:runner.digest(DATA/n) for n in ['entradas.json','gabarito_original.json','instrucoes.txt']},
       'planilha_revisada_sha256':runner.digest(book),'n':60,'finalidade':NOTE,
       'alteracoes':'Regras gerais revistas e confirmação de participação de Édis Milaré fornecida pelo pesquisador. Nenhum rótulo por caso é enviado.',
       'contextos':'Mesmos recortes de v1; listas sem introdução podem continuar indeterminadas.',
       'precos':'Tarifas de referência herdadas; limite estimado US$ 0,50.'})

if __name__=='__main__':
    runner.DATA=DATA;runner.OUT=ROOT/'claude_ajuste_corpus_v2';runner.EXPERIMENT_NOTE=NOTE
    if '--preparar' in sys.argv:
        prepare();runner.load();print('60 entradas validadas. Revisão humana importada. Nenhuma API chamada.')
    else:
        try:runner.main()
        except RuntimeError as e:raise SystemExit(str(e))
