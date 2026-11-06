"""Execução retomável do lote congelado; --verificar não acessa a rede."""
import argparse
import fcntl
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
LEGACY = BASE/'outputs/01a02b49-a916-75a0-80da-a7b4fcc952c1/mlx_local'
sys.path.insert(0, str(LEGACY))
from chave_claude import obter_chave
from reavaliar_todos import parse

DATA = BASE/'outputs/execucao_integral_20261105'
MODEL = 'claude-sonnet-5'

def save(path, value):
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    tmp.replace(path)

def verify():
    manifest=json.loads((DATA/'manifesto.json').read_text())
    for name, expected in manifest['sha256'].items():
        assert hashlib.sha256((DATA/name).read_bytes()).hexdigest()==expected, f'Arquivo alterado: {name}'
    assert manifest['modelo']==MODEL and manifest['max_tokens']==200
    rows=json.loads((DATA/'entradas.json').read_text())
    human=json.loads((DATA/'decisoes_humanas_preservadas.json').read_text())
    assert len({r['id'] for r in rows})==len(rows)==manifest['n_classificar']
    assert not {r['id'] for r in rows}&{r['id'] for r in human}
    return rows, manifest

def summarize(results):
    valid=[r['classificacao'] for r in results.values() if r['classificacao']]
    usage=[r['resposta'].get('usage',{}) for r in results.values()]
    inp=sum(r.get('input_tokens',0) for r in usage)
    out=sum(r.get('output_tokens',0) for r in usage)
    report={'n':len(results),'respostas_invalidas':len(results)-len(valid),
        'corpus':dict(Counter(r['corpus'] for r in valid)),
        'tipo_incorporados':dict(Counter(r['tipo'] for r in valid if r['corpus']=='Incorporar')),
        'tokens_entrada':inp,'tokens_saida':out,'custo_estimado_usd':(2*inp+10*out)/1e6,
        'nota':'Distribuição de previsões, NÃO acurácia. Decisões humanas anteriores preservadas separadamente.'}
    save(DATA/'resumo_execucao.json',report)
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--verificar',action='store_true')
    ap.add_argument('--teto-usd',type=float,default=40)
    args=ap.parse_args()
    rows,manifest=verify()
    print(f"Lote verificado: {len(rows)} classificações; {manifest['n_humanos_preservados']} decisões humanas preservadas.")
    if args.verificar:return
    release=DATA/'liberacao.json'
    if not release.exists() or not json.loads(release.read_text()).get('liberado'):
        raise SystemExit('Lote ainda não liberado: consultar o relatório da atualização dos acórdãos.')
    lock=(DATA/'.execucao.lock').open('w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('Já existe uma execução deste lote.')
    inflight=DATA/'requisicao_em_andamento.json'
    resultpath=DATA/'respostas.json'
    results=json.loads(resultpath.read_text()) if resultpath.exists() else {}
    if inflight.exists():
        ident=json.loads(inflight.read_text())['id']
        if ident in results:inflight.unlink()
        else:raise SystemExit('Uma requisição anterior ficou sem resposta confirmada. Não será repetida automaticamente; solicite conferência do registro requisicao_em_andamento.json.')
    pending=[r for r in rows if r['id'] not in results]
    if not pending:
        print(json.dumps(summarize(results),ensure_ascii=False,indent=2));return
    print(f'{len(pending)} casos pendentes. Os textos serão enviados à Anthropic; sem ferramentas ou acesso autônomo aos PDFs.')
    if input('Autoriza contar os tokens na API? Digite SIM: ').strip()!='SIM':return
    import httpx
    key=obter_chave()
    client=httpx.Client(base_url='https://api.anthropic.com',headers={
        'x-api-key':key,'anthropic-version':'2023-06-01'},timeout=180,trust_env=False,follow_redirects=False)
    countpath=DATA/'contagem_tokens.json'
    counts=json.loads(countpath.read_text()) if countpath.exists() else {}
    try:
        for i,row in enumerate(pending,1):
            if row['id'] in counts:continue
            response=client.post('/v1/messages/count_tokens',json={k:v for k,v in row.items() if k!='id'}|{'model':MODEL})
            if response.status_code!=200:raise SystemExit(f'Contagem interrompida: HTTP {response.status_code}. Retome pelo mesmo comando.')
            counts[row['id']]=response.json()['input_tokens'];save(countpath,counts)
            if i%25==0:print(f'Tokens: {i}/{len(pending)}',flush=True)
            time.sleep(.3)
        estimate=sum(2*counts[r['id']]+10*200 for r in pending)/1e6
        spent=summarize(results)['custo_estimado_usd']
        print(f'Estimativa máxima restante: US$ {estimate:.4f}; já registrado: US$ {spent:.4f}. Tarifas de referência: US$ 2/M entrada e US$ 10/M saída; antes de impostos.')
        if estimate+spent>args.teto_usd:raise SystemExit(f'Estimativa excede o teto total de US$ {args.teto_usd:.2f}. Ajuste --teto-usd se desejar.')
        if input('Iniciar classificações pagas? Digite SIM: ').strip()!='SIM':return
        for row in pending:
            save(inflight,{'id':row['id'],'inicio_unix':time.time(),'modelo':MODEL})
            response=client.post('/v1/messages',json={k:v for k,v in row.items() if k!='id'}|{
                'model':MODEL,'max_tokens':200,'thinking':{'type':'disabled'}})
            if response.status_code!=200:
                if 400<=response.status_code<500:inflight.unlink()
                raise SystemExit(f'Execução interrompida: HTTP {response.status_code}. Respostas anteriores salvas; nenhuma repetição automática.')
            obj=response.json()
            raw=''.join(b.get('text','') for b in obj.get('content',[]) if b.get('type')=='text')
            results[row['id']]={'id':row['id'],'resposta':obj,'request_id':response.headers.get('request-id'),
                'classificacao':parse(raw,obj.get('stop_reason'))}
            save(resultpath,results);inflight.unlink();summarize(results)
            print(f"Claude: {len(results)}/{len(rows)} concluídos",flush=True)
            time.sleep(1.3)
    finally:client.close()
    print(json.dumps(summarize(results),ensure_ascii=False,indent=2))

if __name__=='__main__':
    try:main()
    except (KeyboardInterrupt,Exception) as exc:
        print(f'Execução interrompida ({type(exc).__name__}). Registros já salvos foram preservados. Nenhuma chave será exibida.',file=sys.stderr)
        sys.exit(1)
