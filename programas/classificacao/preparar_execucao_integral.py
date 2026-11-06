"""Prepara lote imutável preservando as decisões humanas; não chama APIs."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE/'outputs/01a02b49-a916-75a0-80da-a7b4fcc952c1/mlx_local'
OUT=BASE/'outputs/execucao_integral_20261105'
PROMPT=ROOT/'reavaliacao_total_conciliada_v6_1/instrucoes.txt'
SOURCE=BASE/'resultados/analise_integral/ocorrencias_classificadas.csv'
SHA_PROMPT='44437f55f69c0c52ee561af71d2db58fb62152d4a0a9b13cfa0b29d1c7bb9ca5'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    assert sha(PROMPT)==SHA_PROMPT,'Instruções divergentes da versão congelada.'
    assert not OUT.exists(),'Preparação existente: não sobrescrever um lote já preparado.'
    with SOURCE.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    byid={r['ocorrencia_id']:r for r in rows}
    assert len(rows)==len(byid)
    gold={};sources={str(SOURCE.relative_to(BASE)):sha(SOURCE),str(PROMPT.relative_to(BASE)):sha(PROMPT)}
    for folder,inputs in [
        ('revisao_humana_total_final_20261013','reavaliacao_total_conciliada_v6_1'),
        ('revisao_humana_piloto_ap02_ap13_20261014','piloto_ap02_ap13_v1'),
        ('revisao_humana_piloto_ap09_ap16_ap22_20261015','piloto_ap09_ap16_ap22_v1')]:
        gp=ROOT/folder/'gabarito_revisado.json';ip=ROOT/inputs/'entradas.json'
        sources[str(gp.relative_to(BASE))]=sha(gp);sources[str(ip.relative_to(BASE))]=sha(ip)
        original={r['id']:json.loads(r['messages'][0]['content']) for r in json.loads(ip.read_text())}
        for g in json.loads(gp.read_text()):
            ident=g['id'];assert ident not in gold and ident in byid
            r=byid[ident];p=original[ident]
            assert r['frase']==p['mencao'] and r['alvo_canonico']==p['alvos'],f'Conteúdo mudou: {ident}'
            assert r['processo']==p['processo'] and int(r['pagina_pdf'])==int(p['pagina_pdf'])
            gold[ident]=g|{'origem':'revisao_humana','fonte':str(gp.relative_to(BASE))}
    assert len(gold)==445
    pending=sorted((r for r in rows if r['ocorrencia_id'] not in gold),key=lambda r:(int(r['audiencia']),r['ocorrencia_id']))
    instructions=PROMPT.read_text();inputs=[]
    for r in pending:
        payload={'audiencia':int(r['audiencia']),'processo':r['processo'],'ministro':r['ministro'],
            'local':r['local_no_acordao'],'pagina_pdf':int(r['pagina_pdf']),'alvos':r['alvo_canonico'],
            'mencao':r['frase'],'contexto_acordao':r['contexto_ampliado'],
            'arquivo_audiencia':Path(r['arquivo_fonte_audiencia']).name if r['arquivo_fonte_audiencia'] else None,
            'pagina_audiencia':r['pagina_fonte_audiencia'] or None,'trecho_audiencia':r['trecho_fonte_audiencia'] or None}
        assert payload['mencao'] and payload['contexto_acordao']
        inputs.append({'id':r['ocorrencia_id'],'system':instructions,'messages':[{'role':'user','content':json.dumps(payload,ensure_ascii=False)}]})
    OUT.mkdir(parents=True)
    save(OUT/'entradas.json',inputs);save(OUT/'decisoes_humanas_preservadas.json',list(gold.values()))
    save(OUT/'metadados_originais.json',rows)
    (OUT/'instrucoes_v6_1.txt').write_text(instructions)
    save(OUT/'manifesto.json',{'data':'2026-11-05','modelo':'claude-sonnet-5','max_tokens':200,
        'thinking':{'type':'disabled'},'n_total':len(rows),'n_humanos_preservados':len(gold),'n_classificar':len(inputs),
        'por_audiencia':dict(sorted(Counter(int(r['audiencia']) for r in pending).items())),
        'fontes_sha256':sources,'sha256':{p.name:sha(p) for p in OUT.iterdir() if p.is_file()},
        'nota':'Lote da extração existente, sem reclassificar os 445 IDs humanos. A liberação depende da verificação dos acórdãos. Não inclui documentos novos sem extração e revisão de cobertura.'})
    print(f'{len(inputs)} entradas preparadas; {len(gold)} decisões humanas preservadas. Nenhuma API chamada.')

if __name__=='__main__':main()
