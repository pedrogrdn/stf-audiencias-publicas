"""Consolidação offline, com origem explícita e preservação de todas as respostas."""
import json,hashlib,csv,re
from pathlib import Path
from collections import Counter
import openpyxl
BASE=Path(__file__).resolve().parents[1]
DATA=BASE/'outputs/execucao_integral_20261105'
ROOT=BASE/'outputs/01a02b49-a916-75a0-80da-a7b4fcc952c1/mlx_local'
OUT=BASE/'outputs/01a02b49-a916-75a0-80da-a7b4fcc952c1/consolidacao_integral_20261105'
sources={}
def read(p):
    sources[str(p.relative_to(BASE))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return json.loads(p.read_text())
def main():
    manifest=read(DATA/'manifesto.json')
    for name,sha in manifest['sha256'].items():assert hashlib.sha256((DATA/name).read_bytes()).hexdigest()==sha
    meta=read(DATA/'metadados_originais.json');responses=read(DATA/'respostas.json')
    gold={r['id']:r for r in read(DATA/'decisoes_humanas_preservadas.json')}
    inputs={r['id'] for r in read(DATA/'entradas.json')}
    assert set(responses)==inputs and not inputs&set(gold)
    assert len(meta)==len({r['ocorrencia_id'] for r in meta})==len(inputs|set(gold))==3455
    historic={}
    for folder in ['claude_reavaliacao_total_conciliada_v6_1','claude_piloto_ap02_ap13_v1','claude_piloto_ap09_ap16_ap22_v1']:
        for r in read(ROOT/folder/'predicoes.json'):historic[r['id']]=r
    assert set(historic)==set(gold)
    catalog=BASE/'outputs/corpus_audiencias_stf_20260821/corpus_audiencias_publicas_stf.xlsx'
    sources[str(catalog.relative_to(BASE))]=hashlib.sha256(catalog.read_bytes()).hexdigest()
    wb=openpyxl.load_workbook(catalog,read_only=True,data_only=True)
    hearings={r[0]:{'ano':r[1],'tema':r[3]} for r in list(wb['Tabela para artigo'].values)[1:] if isinstance(r[0],int)};wb.close()
    rows=[];pending=[]
    for m in sorted(meta,key=lambda r:(int(r['audiencia']),r['ocorrencia_id'])):
        ident=m['ocorrencia_id'];ap=int(m['audiencia']);g=gold.get(ident)
        pred=historic[ident]['previsto'] if g else responses[ident]['classificacao']
        final=g or pred or {};raw=historic[ident]['saida_bruta'] if g else ''.join(b.get('text','') for b in responses[ident]['resposta']['content'] if b['type']=='text')
        reason=('Resposta inválida' if not final else 'Corpus indeterminado' if final['corpus']=='Indeterminado' else 'Tipo indeterminado' if final.get('tipo')=='Indeterminado' else '')
        row={'id':ident,'audiencia':ap,'ano_audiencia':hearings.get(ap,{}).get('ano'),'tema':hearings.get(ap,{}).get('tema'),
            'processo':m['processo'],'pagina_pdf':int(m['pagina_pdf']),'ministro':m['ministro'],'alvo':m['alvo_canonico'],'mencao':m['frase'],
            'corpus_consolidado':final.get('corpus') or 'Resposta inválida','tipo_consolidado':final.get('tipo'),
            'origem':'Humana consolidada' if g else 'Claude sem revisão humana',
            'corpus_claude':pred.get('corpus') if pred else None,'tipo_claude':pred.get('tipo') if pred else None,
            'corpus_humano':g['corpus'] if g else None,'tipo_humano':g['tipo'] if g else None,
            'pendencia':reason or 'Nenhuma sinalizada','local':m['local_no_acordao'],'ano_julgamento':int(m['ano']) if m['ano'] else None,
            'data_julgamento':m['data_julgamento'],'pessoa':m['pessoa'],'instituicao':m['instituicao'],
            'arquivo_acordao':m['arquivo_acordao'],'url_acordao':m['url_acordao'],'fonte_decisao':g['fonte'] if g else str((DATA/'respostas.json').relative_to(BASE)),
            'modelo':'claude-sonnet-5','instrucoes':'v6.1','metodo_ministro':m['ministro_metodo'],'n_alvos':int(m['quantidade_alvos_na_frase'])}
        rows.append(row)
        if reason:pending.append(row|{'contexto':m['contexto_ampliado'],'trecho_audiencia':m['trecho_fonte_audiencia'],'resposta_bruta':raw,'revisao_corpus':None,'revisao_tipo':None,'comentario':None})
    assert len(pending)==112
    summary={'n_total':len(rows),'n_humanos':len(gold),'n_novos':len(responses),'n_pendencias':len(pending),
        'corpus':dict(Counter(r['corpus_consolidado'] for r in rows)),
        'tipo_incorporados':dict(Counter(r['tipo_consolidado'] for r in rows if r['corpus_consolidado']=='Incorporar')),
        'pendencias':dict(Counter(r['pendencia'] for r in pending)),
        'tokens_entrada':sum(r['resposta']['usage']['input_tokens'] for r in responses.values()),
        'tokens_saida':sum(r['resposta']['usage']['output_tokens'] for r in responses.values())}
    summary['custo_usd']=(2*summary['tokens_entrada']+10*summary['tokens_saida'])/1e6
    summary['nota']='Distribuição mista: decisões humanas consolidadas e previsões novas sem revisão. Não é acurácia. Pendências não foram convertidas em exclusões.'
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'base_consolidada.json').write_text(json.dumps({'records':rows,'pendencias':pending,'resumo':summary,'fontes_sha256':sources},ensure_ascii=False,indent=2))
    with (OUT/'mencoes_consolidadas.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    assert all(hashlib.sha256((BASE/p).read_bytes()).hexdigest()==h for p,h in sources.items())
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
