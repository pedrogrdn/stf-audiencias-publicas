"""Teste manual autorizado: nenhum acesso à API na importação ou no --verificar."""
import argparse
from chave_claude import obter_chave
import hashlib
import json
from pathlib import Path
import sys
import time
from normalizar_tipo import parse_tipo

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'tipo_v3'
OUT=ROOT/'claude_tipo_v1'
MODEL='claude-sonnet-5'
MAX_OUTPUT=500
INPUT_PRICE=2/1_000_000
OUTPUT_PRICE=10/1_000_000

def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2))

def prepare():
    manifest=json.loads((DATA/'manifesto.json').read_text())
    source=DATA/'dados/valid.jsonl'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=manifest['dados_sha256']['valid']:
        raise ValueError('Os dados mudaram. Conferir a versão antes de executar.')
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    ids=json.loads((DATA/'ids_rotulos.json').read_text())['valid']
    assert len(rows)==len(ids) and len(rows)>0
    requests=[]
    for r,i in zip(rows,ids):
        msgs=r['messages']
        assert [m['role'] for m in msgs]==['system','user','assistant']
        assert json.loads(msgs[-1]['content'])['tipo']==i['tipo']
        requests.append({'model':MODEL,'system':msgs[0]['content'],'messages':[{'role':'user','content':msgs[1]['content']}]})
    return requests,ids

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verificar',action='store_true');args=parser.parse_args()
    requests,ids=prepare()
    if args.verificar:
        print(f'{len(ids)} casos validados. Apenas instruções e texto do usuário no envio. Nenhuma chamada à API.');return
    if OUT.exists():raise SystemExit('Há uma execução anterior nesta pasta. Não repetir automaticamente: envie o resultado ou erro para conferência.')
    if not sys.stdin.isatty():raise SystemExit('Abra no Terminal interativo para digitar a chave de forma oculta.')
    import httpx
    print(f'Claude Sonnet 5: somente os {len(ids)} casos selecionados, sem gabarito e sem treinamento.')
    print('Os trechos serão enviados à Anthropic. Preços de referência: US$ 2/M entrada e US$ 10/M saída.')
    print('Raciocínio estendido desativado; até 500 tokens de saída por caso. Sem ferramentas, busca web ou cache explícito.')
    if input('Autoriza contar os tokens desses textos na API? Digite SIM: ').strip()!='SIM':return
    key=obter_chave()
    if not key:raise SystemExit('Chave vazia; nenhuma chamada feita.')
    workspace=input('Workspace ID, somente se a chave exigir (caso contrário, Enter): ').strip()
    headers={'x-api-key':key,'anthropic-version':'2023-06-01'}
    if workspace:headers['anthropic-workspace-id']=workspace
    with httpx.Client(base_url='https://api.anthropic.com',headers=headers,timeout=120,follow_redirects=False,trust_env=False) as client:
        def call(endpoint,body):
            try:response=client.post(endpoint,json=body)
            except httpx.HTTPError:
                raise RuntimeError('Falha de conexão ou timeout. Não houve repetição automática. Uma requisição pode ter sido processada; confira antes de repetir.') from None
            if not response.is_success:
                hints={401:'Verifique a chave.',403:'Verifique as permissões e o workspace.',400:'Verifique configuração, créditos e acesso ao modelo.',404:'Modelo ou endpoint indisponível para a conta.',429:'Limite de uso atingido; não houve repetição automática.'}
                raise RuntimeError(f'API retornou HTTP {response.status_code}. '+hints.get(response.status_code,'Consulte o Console. Nenhuma repetição automática.'))
            return response.json()
        counts=[call('/v1/messages/count_tokens',r)['input_tokens'] for r in requests]
        estimate=sum(counts)*INPUT_PRICE+len(ids)*MAX_OUTPUT*OUTPUT_PRICE
        print(f'Entrada total: {sum(counts)} tokens. Estimativa com saída máxima: US$ {estimate:.4f}, antes de impostos.')
        if estimate>0.50:raise SystemExit('Estimativa acima de US$ 0,50. Execução de classificação bloqueada.')
        if input(f'Iniciar as {len(ids)} classificações? Digite SIM: ').strip()!='SIM':return
        OUT.mkdir()
        save(OUT/'config.json',{'modelo':MODEL,'thinking':'disabled','max_tokens':MAX_OUTPUT,'tokens_contados':counts,'estimativa_usd':estimate,'precos_referencia':{'entrada_por_milhao':2,'saida_por_milhao':10},'sha256_dados':hashlib.sha256((DATA/'dados/valid.jsonl').read_bytes()).hexdigest(),'nota':'Amostra de desenvolvimento. Comparação sem fine-tuning e sem gabarito enviado. Amostragem padrão do fornecedor, não temperatura zero.'})
        results=[]
        try:
            for n,(request,i) in enumerate(zip(requests,ids),1):
                t=time.perf_counter()
                data=call('/v1/messages',request|{'max_tokens':MAX_OUTPUT,'thinking':{'type':'disabled'}})
                raw=''.join(b.get('text','') for b in data.get('content',[]) if b.get('type')=='text')
                label=parse_tipo(raw, data.get('stop_reason'))
                results.append({'id':i['id'],'humano':i['tipo'],'ia':label,'saida_bruta':raw,'stop_reason':data.get('stop_reason'),'usage':data.get('usage',{}),'modelo_retornado':data.get('model'),'response_id':data.get('id'),'segundos':round(time.perf_counter()-t,3)})
                save(OUT/'predicoes.json',results);print(f'Claude: {n}/{len(ids)} concluídos',flush=True)
        except RuntimeError as e:
            save(OUT/'interrupcao.json',{'concluidos':len(results),'mensagem':str(e),'repeticao_automatica':False});raise
    metrics={'n':len(ids),'acertos':sum(r['humano']==r['ia'] for r in results),'invalidas':sum(r['ia'] is None for r in results),'por_categoria':{}}
    for label in ['Contexto','Relato','Argumento']:
        support=sum(r['humano']==label for r in results);pred=sum(r['ia']==label for r in results);tp=sum(r['humano']==r['ia']==label for r in results)
        metrics['por_categoria'][label]={'suporte':support,'acertos':tp,'precisao':tp/pred if pred else None,'recall':tp/support if support else None,'f1':2*tp/(support+pred) if support+pred else None}
    metrics['tokens_entrada']=sum(r['usage'].get('input_tokens',0) for r in results)
    metrics['tokens_saida']=sum(r['usage'].get('output_tokens',0) for r in results)
    metrics['custo_estimado_usd']=metrics['tokens_entrada']*INPUT_PRICE+metrics['tokens_saida']*OUTPUT_PRICE
    save(OUT/'metricas.json',metrics);print(json.dumps(metrics,ensure_ascii=False,indent=2));print(OUT)

if __name__=='__main__':
    try:main()
    except (RuntimeError,ValueError) as e:print(str(e),file=sys.stderr);sys.exit(1)
    except KeyboardInterrupt:print('\nInterrompido. Não repetir antes de conferir o resultado parcial.',file=sys.stderr);sys.exit(130)
