import sys,json,re
from classificar_atores import P,O,MODEL,SYSTEM,api,save
rows=json.loads((O/'complementos_contexto.json').read_text());key=(P/'claude.txt').read_text(encoding='utf-8-sig').strip()
path=O/'respostas_complementos.json';results=json.loads(path.read_text()) if path.exists() else {}
bs=[rows[i:i+8] for i in range(0,len(rows),8)];counts=[]
for b in bs:
    body={'model':MODEL,'system':SYSTEM,'messages':[{'role':'user','content':json.dumps([{k:v for k,v in r.items() if k!='mencionado_corpus'} for r in b],ensure_ascii=False)}]}
    counts.append(api('messages/count_tokens',body,key)['input_tokens'])
save(O/'tokens_complementos.json',counts)
estimate=(sum(counts)*2+len(bs)*4000*10)/1e6
print(f'Complementos: estimativa máxima US$ {estimate:.4f}',flush=True)
if estimate>1:raise SystemExit('Complemento acima de US$1; conferir.')
for i,b in enumerate(bs):
    if str(i) in results:continue
    body={'model':MODEL,'system':SYSTEM,'messages':[{'role':'user','content':json.dumps([{k:v for k,v in r.items() if k!='mencionado_corpus'} for r in b],ensure_ascii=False)}],'max_tokens':4000,'thinking':{'type':'disabled'}}
    lock=O/'complemento_em_andamento.json'
    if lock.exists():raise SystemExit('Requisição não confirmada, conferir antes de repetir.')
    save(lock,{'lote':i,'ids':[x['id'] for x in b]})
    res=api('messages',body,key)
    results[str(i)]={'resposta':res,'ids':[x['id'] for x in b]};save(path,results);lock.unlink()
    print(f'Complementos: {sum(len(v["ids"]) for v in results.values())}/{len(rows)}',flush=True)
