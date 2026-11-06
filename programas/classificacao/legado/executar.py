"""Execução local; não chama APIs de classificação nem envia documentos."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
MODEL = PROJECT / '.local-mlx/modelo'

def dump(path, obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2))

def verify_source():
    manifest = json.loads((ROOT/'manifesto.json').read_text())
    actual = hashlib.sha256((ROOT.parent/manifest['source']).read_bytes()).hexdigest()
    if actual != manifest['sha256']:
        raise SystemExit('A planilha original mudou. Reprepare os dados antes de executar.')

def audit():
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    groups = json.loads((ROOT/'registros.json').read_text())
    result = {}
    for split,rows in groups.items():
        counts = [len(tokenizer.encode(tokenizer.apply_chat_template(r['messages'],tokenize=False),add_special_tokens=False)) for r in rows]
        for r,n in zip(rows,counts): r['tokens_com_resposta']=n
        ordered = sorted(counts)
        result[split] = {'n':len(counts),'total_tokens':sum(counts),'min':min(counts),'mediana':ordered[len(ordered)//2],'max':max(counts),'acima_2048':sum(n>2048 for n in counts),'acima_4096':sum(n>4096 for n in counts)}
    dump(ROOT/'registros.json',groups)
    dump(ROOT/'tokens.json',result)
    (ROOT/'requirements.lock.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
    print(json.dumps(result,indent=2))

def init_model(adapter=None):
    import mlx.core as mx
    from mlx_lm import load
    mx.set_memory_limit(8*1024**3)
    mx.set_cache_limit(512*1024**2)
    return load(str(MODEL),adapter_path=str(adapter) if adapter else None)

def check_json(raw):
    obj=json.loads(raw)
    if not isinstance(obj,dict) or set(obj) != {'corpus','tipo'}: raise ValueError('Esquema inválido')
    if obj['corpus'] not in ['Incorporar','Excluir','Indeterminado']: raise ValueError('Corpus inválido')
    if obj['corpus']=='Incorporar':
        if obj['tipo'] not in ['Contexto','Relato','Argumento','Indeterminado']: raise ValueError('Tipo inválido')
    elif obj['tipo'] is not None: raise ValueError('Tipo não aplicável')
    return obj

def evaluate(args):
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler
    if args.split=='teste' and not args.confirmar_teste_final:
        raise SystemExit('Teste reservado. Use --confirmar-teste-final apenas após congelar a configuração.')
    if args.modo=='ajustado' and not (ROOT/'adaptadores/adapters.safetensors').exists():
        raise SystemExit('Não há adaptador real treinado. Execute o treinamento primeiro.')
    model,tok=init_model(ROOT/'adaptadores' if args.modo=='ajustado' else None)
    rows=json.loads((ROOT/'registros.json').read_text())[args.split]
    if args.limite: rows=rows[:args.limite]
    out=ROOT/'resultados'/time.strftime('%Y%m%d_%H%M%S')
    out.mkdir(parents=True,exist_ok=False)
    predictions=[]
    for i,r in enumerate(rows):
        prompt=tok.apply_chat_template(r['messages'][:-1],tokenize=False,add_generation_prompt=True)
        t=time.perf_counter()
        raw=generate(model,tok,prompt=prompt,max_tokens=100,sampler=make_sampler(temp=0),verbose=False)
        try:
            pred=check_json(raw); error=''
        except (ValueError,TypeError):
            pred={'corpus':None,'tipo':None}; error='Saída inválida; revisar'
        predictions.append({'id':r['id'],'corpus_humano':r['corpus'],'tipo_humano':r['tipo'],'corpus_ia':pred['corpus'],'tipo_ia':pred['tipo'],'erro':error,'segundos':round(time.perf_counter()-t,3),'saida_bruta':raw})
        dump(out/'predicoes.json',predictions)
        print(f'{i+1}/{len(rows)} concluídos',flush=True)
    with (out/'comparacao.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(predictions[0]),delimiter=';'); writer.writeheader(); writer.writerows(predictions)
    metrics={'modo':args.modo,'conjunto':args.split,'n':len(rows),'parcial':bool(args.limite),'invalidas':sum(bool(p['erro']) for p in predictions),'acuracia_corpus':sum(p['corpus_ia']==p['corpus_humano'] for p in predictions)/len(rows),'acerto_conjunto_corpus_tipo':sum(not p['erro'] and p['corpus_ia']==p['corpus_humano'] and p['tipo_ia']==p['tipo_humano'] for p in predictions)/len(rows)}
    metrics['por_categoria']={}
    for task,labels in [('corpus',['Incorporar','Excluir']),('tipo',['Contexto','Relato','Argumento'])]:
        for label in labels:
            applicable=[p for p in predictions if task=='corpus' or p['corpus_humano']=='Incorporar']
            gold=sum(p[f'{task}_humano']==label for p in applicable)
            predicted=sum(p[f'{task}_ia']==label for p in applicable)
            tp=sum(p[f'{task}_ia']==label and p[f'{task}_humano']==label for p in applicable)
            metrics['por_categoria'][label]={'suporte':gold,'precisao':tp/predicted if predicted else None,'recall':tp/gold if gold else None,'f1':2*tp/(gold+predicted) if gold+predicted else None}
    metrics['nota_tipo']='Tipo avaliado nos incorporados humanos; exclusão incorreta pelo modelo conta como erro. Categoria sem suporte não tem recall estimável.'
    dump(out/'metricas.json',metrics)
    print(out)

def train(args):
    import mlx.core as mx
    tokens=json.loads((ROOT/'tokens.json').read_text())
    longest=max(tokens[s]['max'] for s in ['treino','desenvolvimento'])
    if longest>8192: raise SystemExit('Há contexto acima de 8192 tokens. Rever configuração sem cortar textos automaticamente.')
    target=ROOT/'adaptadores'
    if target.exists(): raise SystemExit('Já existe pasta de adaptadores. Preserve a execução anterior antes de iniciar outra.')
    mx.set_memory_limit(8*1024**3); mx.set_cache_limit(512*1024**2)
    config={'modelo':str(MODEL),'iteracoes':args.iters,'seed':42,'num_layers':4,'batch_size':1,'max_seq_length':longest,'learning_rate':1e-5,'teor':False,'participantes':False}
    dump(ROOT/'config_execucao.json',config)
    sys.argv=['mlx_lm.lora','--model',str(MODEL),'--train','--data',str(ROOT/'dados'),'--adapter-path',str(target),'--iters',str(args.iters),'--batch-size','1','--num-layers','4','--max-seq-length',str(longest),'--grad-checkpoint','--mask-prompt','--seed','42','--learning-rate','0.00001','--steps-per-report','10','--steps-per-eval','100','--val-batches','-1','--save-every','100']
    runpy.run_module('mlx_lm.lora',run_name='__main__')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('acao',choices=['verificar','avaliar','treinar'])
    parser.add_argument('--modo',choices=['base','ajustado'],default='base')
    parser.add_argument('--split',choices=['desenvolvimento','teste'],default='desenvolvimento')
    parser.add_argument('--confirmar-teste-final',action='store_true')
    parser.add_argument('--limite',type=int)
    parser.add_argument('--iters',type=int,default=210)
    args=parser.parse_args()
    if args.iters<1 or (args.limite is not None and args.limite<1): parser.error('Quantidade deve ser positiva')
    verify_source()
    if args.acao=='verificar': audit()
    elif args.acao=='avaliar': evaluate(args)
    else:
        audit()
        train(args)

if __name__=='__main__': main()
