"""Execução interativa do piloto. --verificar não acessa rede ou credenciais."""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from preparar_piloto_ap02_ap13 import ROOT, DATA, digest, save
from chave_claude import obter_chave
from reavaliar_todos import parse
from avaliar_claude import MODEL, INPUT_PRICE, OUTPUT_PRICE

OUT=ROOT/'claude_piloto_ap02_ap13_v1'
MAX_TOKENS=200
CAP=1.00

def load():
    manifest=json.loads((DATA/'manifesto.json').read_text())
    assert all(digest(DATA/n)==h for n,h in manifest['sha256'].items()), 'Arquivos modificados.'
    rows=json.loads((DATA/'entradas.json').read_text())
    assert len(rows)==len({r['id'] for r in rows})==61
    assert all(set(r)=={'id','system','messages'} and len(r['messages'])==1 and r['messages'][0]['role']=='user' for r in rows)
    return rows,manifest

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--verificar',action='store_true');args=ap.parse_args()
    rows,manifest=load()
    if args.verificar:
        print('61 entradas verificadas offline. Instruções congeladas; sem gabarito enviado; nenhuma API chamada.');return
    if OUT.exists(): raise SystemExit('Resultado ou execução parcial existente. Não repetir: conferir arquivos antes de retomar.')
    if not sys.stdin.isatty(): raise SystemExit('Execute no Terminal interativo.')
    print(f'AP 2: 22 candidatos; AP 13: 39 candidatos. Modelo herdado: {MODEL}.')
    print('Serão enviados os recortes à Anthropic; sem ferramentas, sem acesso autônomo a PDFs e sem treinamento.')
    print('Tarifas HISTÓRICAS de referência: US$ 2/M entrada e US$ 10/M saída. Não são cotação atual nem garantia do valor faturado.')
    print(f'Teto da estimativa: US$ {CAP:.2f}. Confira o modelo e as tarifas no Console antes de confirmar.')
    if input('Autoriza contar tokens pela API? Digite SIM: ').strip()!='SIM': return
    key=obter_chave(); workspace=input('Workspace ID, se exigido (ou Enter): ').strip()
    import httpx
    headers={'x-api-key':key,'anthropic-version':'2023-06-01'}
    if workspace:headers['anthropic-workspace-id']=workspace
    requests=[{'model':MODEL,'system':r['system'],'messages':r['messages']} for r in rows]
    with httpx.Client(base_url='https://api.anthropic.com',headers=headers,timeout=120,trust_env=False,follow_redirects=False) as client:
        def call(endpoint,body):
            try: response=client.post(endpoint,json=body)
            except httpx.HTTPError: raise RuntimeError('Falha de conexão. Uma chamada pode ter sido processada; conferir antes de repetir.') from None
            if not response.is_success:
                raise RuntimeError(f'HTTP {response.status_code}. Consulte limites, créditos e acesso ao modelo no Console. Sem repetição automática.')
            return response.json()
        cachepath=ROOT/'contagem_piloto_ap02_ap13_v1.json'
        signature=digest(DATA/'entradas.json')+MODEL
        cache=json.loads(cachepath.read_text()) if cachepath.exists() else {'assinatura':signature,'contagens':[]}
        assert cache['assinatura']==signature and len(cache['contagens'])<=61
        for req in requests[len(cache['contagens']):]:
            cache['contagens'].append(call('/v1/messages/count_tokens',req)['input_tokens'])
            save(cachepath,cache); print(f"Tokens contados: {len(cache['contagens'])}/61",flush=True);time.sleep(1.3)
        estimate=sum(cache['contagens'])*INPUT_PRICE+61*MAX_TOKENS*OUTPUT_PRICE
        print(f"Entrada: {sum(cache['contagens'])} tokens. Estimativa com saída máxima: US$ {estimate:.4f}, antes de impostos.")
        if estimate>CAP: raise SystemExit('Acima do teto estimado. Classificação não iniciada.')
        if input('Iniciar as 61 classificações? Digite SIM: ').strip()!='SIM': return
        OUT.mkdir();save(OUT/'config.json',{'modelo':MODEL,'max_tokens':MAX_TOKENS,'thinking':'disabled','estimativa_usd':estimate,'precos_referencia':{'entrada_por_milhao':INPUT_PRICE*1e6,'saida_por_milhao':OUTPUT_PRICE*1e6},'manifesto':manifest})
        results=[]
        try:
            for n,(req,row) in enumerate(zip(requests,rows),1):
                r=call('/v1/messages',req|{'max_tokens':MAX_TOKENS,'thinking':{'type':'disabled'}})
                raw=''.join(b.get('text','') for b in r.get('content',[]) if b.get('type')=='text')
                results.append({'id':row['id'],'previsto':parse(raw,r.get('stop_reason')),'saida_bruta':raw,'stop_reason':r.get('stop_reason'),'usage':r.get('usage',{}),'modelo_retornado':r.get('model'),'response_id':r.get('id')})
                save(OUT/'predicoes.json',results);print(f'{n}/61 concluídos',flush=True);time.sleep(1.3)
        except (RuntimeError,KeyboardInterrupt):
            save(OUT/'interrupcao.json',{'concluidos':len(results),'nota':'Não reiniciar automaticamente. Conferir eventual chamada processada sem resposta salva.'});raise
    ti=sum(r['usage'].get('input_tokens',0) for r in results);to=sum(r['usage'].get('output_tokens',0) for r in results)
    summary={'n':len(results),'respostas_invalidas':sum(r['previsto'] is None for r in results),'por_audiencia':{},'tokens_entrada':ti,'tokens_saida':to,'custo_estimado_usd':ti*INPUT_PRICE+to*OUTPUT_PRICE,'nota':'Distribuição das predições, NÃO acurácia. Aguarda revisão humana integral; nenhuma pré-classificação automática foi usada como gabarito.'}
    for a in (2,13):
        group=[r for r in results if r['id'].startswith(f'AP{a:02d}-')]
        summary['por_audiencia'][str(a)]={'n':len(group),'corpus':dict(Counter((r['previsto'] or {}).get('corpus','Resposta inválida') for r in group)),'tipo_incorporados':dict(Counter(r['previsto']['tipo'] for r in group if r['previsto'] and r['previsto']['corpus']=='Incorporar'))}
    save(OUT/'resumo_execucao.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2));print(OUT)

if __name__=='__main__':
    try: main()
    except (RuntimeError,AssertionError) as e: raise SystemExit(str(e))
