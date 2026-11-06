"""Prepara todos os candidatos das APs 2 e 13, offline e sem gabarito enviado."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
DATA = ROOT/'piloto_ap02_ap13_v1'
SOURCE = PROJECT/'resultados/analise_integral/ocorrencias_classificadas.csv'
PROMPT = ROOT/'reavaliacao_total_conciliada_v6_1/instrucoes.txt'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    if DATA.exists(): raise SystemExit('Preparação existente; não sobrescrever.')
    with SOURCE.open(encoding='utf-8-sig',newline='') as f:
        rows=[r for r in csv.DictReader(f) if int(r['audiencia']) in (2,13)]
    rows.sort(key=lambda r:r['ocorrencia_id'])
    assert Counter(int(r['audiencia']) for r in rows)=={2:22,13:39}
    assert len({r['ocorrencia_id'] for r in rows})==61
    previous_files=sorted(ROOT.glob('claude_*/predicoes.json'))
    previous={r['id'] for p in previous_files for r in json.loads(p.read_text())}
    assert not previous.intersection(r['ocorrencia_id'] for r in rows)
    prompt=PROMPT.read_text()
    inputs=[]
    for r in rows:
        payload={'audiencia':int(r['audiencia']),'processo':r['processo'],
            'ministro':r['ministro'],'local':r['local_no_acordao'],'pagina_pdf':int(r['pagina_pdf']),
            'alvos':r['alvo_canonico'],'mencao':r['frase'],'contexto_acordao':r['contexto_ampliado'],
            'arquivo_audiencia':Path(r['arquivo_fonte_audiencia']).name if r['arquivo_fonte_audiencia'] else None,
            'pagina_audiencia':r['pagina_fonte_audiencia'] or None,'trecho_audiencia':r['trecho_fonte_audiencia'] or None}
        assert payload['mencao'] and payload['contexto_acordao']
        inputs.append({'id':r['ocorrencia_id'],'system':prompt,'messages':[{'role':'user','content':json.dumps(payload,ensure_ascii=False)}]})
    DATA.mkdir()
    save(DATA/'entradas.json',inputs)
    save(DATA/'metadados_originais.json',rows)
    (DATA/'instrucoes.txt').write_text(prompt,encoding='utf-8')
    save(DATA/'manifesto.json',{'n':61,'audiencias':{'2':22,'13':39},
        'sha256':{n:digest(DATA/n) for n in ['entradas.json','metadados_originais.json','instrucoes.txt']},
        'fontes_sha256':{str(SOURCE):digest(SOURCE),str(PROMPT):digest(PROMPT)},
        'predicoes_anteriores_sha256':{str(p):digest(p) for p in previous_files},
        'status_automaticos_originais':dict(Counter(r['status_revisao'] for r in rows)),
        'finalidade':'Piloto integral dos candidatos recuperados nas APs 2 e 13. Revisão humana de todas as respostas, inclusive exclusões. Não há gabarito humano desta rodada.',
        'limites':['61 ocorrências candidatas da extração de 31/08/2026, não censo garantido de todas as menções existentes nos PDFs.',
          'Instruções v6.1 congeladas e idênticas às da reavaliação dos 300.',
          'Pré-classificações automáticas são apenas metadados locais: não são gabarito nem são enviadas à API.',
          'Recortes originais preservados, sem leitura autônoma de PDFs pela API. Vínculos de transcrição não foram reconferidos.',
          'IDs não encontrados nas predições anteriores consultadas. Isso não assegura independência semântica de todos os trechos.',
          'Audiências escolhidas intencionalmente por diversidade e viabilidade; não constituem amostra probabilística.']})
    print('61 candidatos preparados offline: AP 2 = 22; AP 13 = 39. Nenhuma API chamada.')

if __name__=='__main__': main()
