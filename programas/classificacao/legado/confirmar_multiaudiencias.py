"""Consolida decisões humanas confirmadas; não executa modelos."""
import hashlib
import json
from pathlib import Path
from normalizar_tipo import metrics, parse_tipo

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'multiaudiencias_revisao_v2'
CHANGES={
 'AP01-AP_01_ADI_3510-00002':'Relato',
 'AP01-AP_01_ADI_3510-00004':'Relato',
 'AP01-AP_01_ADI_3510-00005':'Relato',
 'AP01-AP_01_ADI_3510-00011':'Argumento',
 'AP04-AP_04_SS_2944-00012':'Argumento',
 'AP04-AP_04_SS_3345-00015':'Argumento',
 'AP03-AP_03_ADPF_054-00030':'Relato',
 'AP14-AP_14_ADI_5035-00005':'Contexto',
 'AP12-AP_12_ADI_4650-00006':None,
 'AP32-AP_32_ADPF_635-00105':None,
}

def main():
    if OUT.exists(): raise SystemExit('Versão existente; nada sobrescrito.')
    sources=[ROOT/'multiaudiencias_v1/ids_rotulos.json',ROOT/'claude_multiaudiencias_v1/predicoes.json',ROOT/'revisao_11_divergencias.xlsx']
    before={p:p.read_bytes() for p in sources}
    ids=json.loads(before[sources[0]])['valid']
    pred=json.loads(before[sources[1]])
    assert len(ids)==len(pred)==30 and set(CHANGES)<=set(r['id'] for r in ids)
    revised=[];decisions=[];audit=[]
    for r in ids:
        label=CHANGES.get(r['id'],r['tipo'])
        decisions.append(dict(r,corpus='Excluir' if label is None else 'Incorporar',tipo=label))
        if label is not None: revised.append(dict(r,tipo=label))
        if r['id'] in CHANGES:
            audit.append({'id':r['id'],'antes':{'corpus':'Incorporar','tipo':r['tipo']},
              'depois':{'corpus':'Excluir' if label is None else 'Incorporar','tipo':label}})
    gold={r['id']:r['tipo'] for r in revised}
    rows=[dict(r,humano_original=r['humano'],humano=gold[r['id']],ia=parse_tipo(r['saida_bruta'],r.get('stop_reason','end_turn'))) for r in pred if r['id'] in gold]
    result=metrics(rows,'ia')
    result['divergencias']=[{'id':r['id'],'humano':r['humano'],'ia':r['ia']} for r in rows if r['humano']!=r['ia']]
    result['finalidade']='Reavaliação de desenvolvimento após revisão humana dos erros. Não estima desempenho independente.'
    assert len(revised)==28 and result['acertos']==27
    OUT.mkdir()
    outputs={'ids_rotulos.json':{'valid':revised},'decisoes_corpus.json':decisions,'predicoes.json':rows,'metricas.json':result,
      'alteracoes.json':{'origem':'Planilha revisada pelo usuário e confirmação posterior dos casos 2, 3 e 11 nesta conversa',
        'alteracoes':audit,'fontes_sha256':{str(p):hashlib.sha256(b).hexdigest() for p,b in before.items()},
        'preservacao':'Planilha humana, dados de treino, teste reservado e execuções originais não sobrescritos.'}}
    for name,obj in outputs.items(): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
    assert all(p.read_bytes()==b for p,b in before.items())
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
