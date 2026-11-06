"""Importa revisão enviada pelo pesquisador por ID, preservando fontes e previsões."""
import json,hashlib,csv,shutil
from pathlib import Path
from collections import Counter
import openpyxl
BASE=Path(__file__).resolve().parents[1]
ROOT=BASE/'outputs/01a02b49-a916-75a0-80da-a7b4fcc952c1'
OLD=ROOT/'consolidacao_integral_20261105'
OUT=ROOT/'consolidacao_integral_revisada_20261105'
ATTACH=Path('/tmp/codex-remote-attachments/01a02b49-a916-75a0-80da-a7b4fcc952c1/52CC75DE-0E74-4A5F-8194-892C1ACD6455/1-Copy-of-triagem_inicial_pendencias.xlsx')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2))
def main():
    assert not OUT.exists(),'Saída já existente; não sobrescrever revisão.'
    source=json.loads((OLD/'base_consolidada.json').read_text())
    triage=json.loads((OLD/'triagem_pendencias.json').read_text())
    byid={r['id']:r for r in triage['records']}
    wb=openpyxl.load_workbook(ATTACH,read_only=True,data_only=True)
    cells=list(wb['Triagem'].values);header=cells[0];decisions={};revisions=[]
    for line,values in enumerate(cells[1:],2):
        r=dict(zip(header,values));ident=r['ID estável'];assert ident in byid and ident not in decisions
        t=byid[ident]
        for h,k in [('Caso original','caso'),('Sugestão corpus','sugestao_corpus'),('Sugestão tipo','sugestao_tipo'),('Alvo','alvo'),('Menção','mencao'),('Audiência','audiencia'),('Processo','processo'),('Página PDF','pagina_pdf')]:
            assert (r[h] or None)==(t[k] or None),f'Campo de referência alterado: {ident} {h}'
        choice=r['Sua decisão']
        if choice=='Aceitar sugestão':
            assert not r['Corpus se alterar'] and not r['Tipo se alterar']
            corpus,tipo=t['sugestao_corpus'],t['sugestao_tipo']
        elif choice=='Alterar':corpus,tipo=r['Corpus se alterar'],r['Tipo se alterar']
        else:raise ValueError(f'Decisão não conclusiva: {ident}: {choice}')
        assert corpus in ['Incorporar','Excluir']
        assert (corpus=='Excluir' and tipo is None) or (corpus=='Incorporar' and tipo in ['Contexto','Relato','Argumento'])
        decisions[ident]={'id':ident,'caso':t['caso'],'decisao':choice,'corpus':corpus,'tipo':tipo,'comentario':r['Seu comentário'],'linha_planilha':line,'celulas':f'Triagem!J{line}:M{line}',
            'sugestao_corpus':t['sugestao_corpus'],'sugestao_tipo':t['sugestao_tipo'],
            'modalidade':'Confirmação de sugestão do Codex' if choice=='Aceitar sugestão' else 'Rótulo indicado pelo pesquisador'}
        revisions.append(t|{'decisao_humana':choice,'corpus_humano':corpus,'tipo_humano':tipo,'comentario':r['Seu comentário'],
            'revisao_corpus':r['Corpus se alterar'],'revisao_tipo':r['Tipo se alterar']})
    wb.close();assert set(decisions)==set(byid) and len(decisions)==112
    updated=[]
    for old in source['records']:
        r=old.copy();g=decisions.get(r['id'])
        if g:
            assert not r['corpus_humano'],'Não sobrescrever decisão humana anterior.'
            r.update(corpus_consolidado=g['corpus'],tipo_consolidado=g['tipo'],corpus_humano=g['corpus'],tipo_humano=g['tipo'],
                origem='Humana consolidada',pendencia='Nenhuma sinalizada',fonte_decisao=str((OUT/'decisoes_revisadas.json').relative_to(BASE)))
        r['modalidade_revisao']=g['modalidade'] if g else 'Revisão humana anterior' if old['origem']=='Humana consolidada' else 'Sem revisão humana'
        r['decisao_triagem']=g['decisao'] if g else None
        r['caso_triagem']=g['caso'] if g else None
        updated.append(r)
        assert (r['corpus_claude'],r['tipo_claude'])==(old['corpus_claude'],old['tipo_claude'])
    summary=source['resumo'].copy()
    summary.update(n_humanos=557,n_novos=3010,n_sem_revisao_humana=2898,n_execucao_claude=3010,n_pendencias=0,
        corpus=dict(Counter(r['corpus_consolidado'] for r in updated)),
        tipo_incorporados=dict(Counter(r['tipo_consolidado'] for r in updated if r['corpus_consolidado']=='Incorporar')),
        pendencias={},revisao_112=dict(Counter(r['decisao'] for r in decisions.values())),
        resultado_revisao=dict(Counter((r['tipo'] if r['corpus']=='Incorporar' else 'Excluir') for r in decisions.values())),
        nota='As 112 pendências sinalizadas foram resolvidas pelo pesquisador. 557 decisões humanas consolidadas e 2898 previsões sem revisão humana. Revisão orientada por sugestões, não auditoria independente; não estima acurácia.')
    assert len(updated)==3455 and sum(r['origem']=='Humana consolidada' for r in updated)==557
    assert all(r['corpus_consolidado'] in ['Incorporar','Excluir'] for r in updated)
    OUT.mkdir()
    shutil.copy2(ATTACH,OUT/'revisao_recebida.xlsx')
    save(OUT/'decisoes_revisadas.json',list(decisions.values()))
    sources={str((OLD/'base_consolidada.json').relative_to(BASE)):sha(OLD/'base_consolidada.json'),str((OLD/'triagem_pendencias.json').relative_to(BASE)):sha(OLD/'triagem_pendencias.json'),'revisao_recebida.xlsx':sha(ATTACH)}
    save(OUT/'base_consolidada.json',{'records':updated,'pendencias':[],'revisoes':revisions,'resumo':summary,'fontes_sha256':sources})
    with (OUT/'mencoes_consolidadas.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(updated[0]));w.writeheader();w.writerows(updated)
    assert sha(ATTACH)==sha(OUT/'revisao_recebida.xlsx')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
