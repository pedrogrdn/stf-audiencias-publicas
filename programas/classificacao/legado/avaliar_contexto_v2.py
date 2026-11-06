import argparse
import json
import hashlib
import time
from pathlib import Path
import executar as engine

ROOT=Path(__file__).resolve().parent/'contexto_v2'

def metrics(preds):
    joint=[p for p in preds if p['tarefa']=='conjunta']
    applicable=[p for p in preds if p['humano']['corpus']=='Incorporar']
    result={'n':len(preds),'invalidas':sum(bool(p['erro']) for p in preds),'segundos':sum(p['segundos'] for p in preds)}
    if joint:
        result.update({'acertos_corpus':sum(p['previsto']['corpus']==p['humano']['corpus'] for p in preds),'acertos_completos':sum(p['previsto']==p['humano'] and not p['erro'] for p in preds),'incorporaveis':len(applicable),'incorporaveis_recuperadas':sum(p['previsto']['corpus']=='Incorporar' for p in applicable)})
    result['tipo_sobre_incorporados']={'n':len(applicable),'acertos':sum(p['previsto']['tipo']==p['humano']['tipo'] and not p['erro'] for p in applicable)}
    result['confusao_tipo']=[{'humano':g,'ia':q,'n':sum(p['humano']['tipo']==g and p['previsto']['tipo']==q for p in applicable)} for g in ['Contexto','Relato','Argumento'] for q in ['Contexto','Relato','Argumento','Indeterminado',None] if any(p['humano']['tipo']==g and p['previsto']['tipo']==q for p in applicable)]
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--experimento',choices=['conjunta_contexto','tipo_original','tipo_contexto'],required=True);args=parser.parse_args()
    engine.verify_source()
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler
    import mlx.core as mx
    rows=json.loads((ROOT/'desenvolvimento_contexto.json').read_text())
    tipo=args.experimento.startswith('tipo')
    if tipo:rows=[r for r in rows if r['corpus']=='Incorporar']
    output=ROOT/args.experimento
    output.mkdir(exist_ok=False)
    engine.dump(output/'config.json',{'experimento':args.experimento,'temperatura':0,'max_tokens_saida':100,'treinamento_novo':False,'modelo':str(engine.MODEL),'sha256_dados':hashlib.sha256((ROOT/'desenvolvimento_contexto.json').read_bytes()).hexdigest(),'sha256_adaptador':hashlib.sha256((engine.ROOT/'adaptadores/adapters.safetensors').read_bytes()).hexdigest()})
    model,tok=engine.init_model(engine.ROOT/'adaptadores')
    preds=[]
    for i,r in enumerate(rows):
        payload=r['payload'] if args.experimento=='tipo_original' else r['payload_contexto']
        system=r['messages'][0]['content']
        if tipo:system+='\nNesta avaliação isolada, o vínculo ao corpus já foi confirmado por humano. Não reavalie corpus. Retorne somente {"tipo":"Contexto"}, {"tipo":"Relato"}, {"tipo":"Argumento"} ou {"tipo":"Indeterminado"}, conforme o texto.'
        prompt=tok.apply_chat_template([{'role':'system','content':system},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}],tokenize=False,add_generation_prompt=True)
        n=len(tok.encode(prompt))
        if n>12000:raise RuntimeError(f'Contexto de {r["id"]}: {n} tokens; acima do limite conservador. Nenhum corte automático.')
        t=time.perf_counter();mx.reset_peak_memory()
        raw=generate(model,tok,prompt=prompt,max_tokens=100,sampler=make_sampler(temp=0),verbose=False)
        pred={'corpus':None,'tipo':None};error=''
        try:
            if tipo:
                obj=json.loads(raw)
                if not isinstance(obj,dict) or set(obj)!={'tipo'} or obj['tipo'] not in ['Contexto','Relato','Argumento','Indeterminado']:raise ValueError('Esquema tipo inválido')
                pred={'corpus':'Incorporar','tipo':obj['tipo']}
            else:pred=engine.check_json(raw)
        except (ValueError,TypeError):error='Saída inválida'
        preds.append({'id':r['id'],'tarefa':'tipo' if tipo else 'conjunta','humano':{'corpus':r['corpus'],'tipo':r['tipo']},'previsto':pred,'erro':error,'saida_bruta':raw,'tokens_entrada':n,'segundos':round(time.perf_counter()-t,3),'pico_mlx_gb':mx.get_peak_memory()/1e9})
        engine.dump(output/'predicoes.json',preds)
        print(f'{args.experimento}: {i+1}/{len(rows)}; {n} tokens',flush=True)
    engine.dump(output/'metricas.json',metrics(preds));print(json.dumps(metrics(preds),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
