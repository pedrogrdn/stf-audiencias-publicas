"""Conciliação conservadora por processo, sem previsões do modelo."""
import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parents[2]
SOURCE = ROOT/'reavaliacao_total_v6_1'
OUT = ROOT/'reavaliacao_total_conciliada_v6_1'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s): return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip()

def main():
    if OUT.exists(): raise SystemExit('Conciliação existente; não sobrescrever.')
    if (ROOT/'claude_reavaliacao_total_v6_1').exists(): raise SystemExit('Execução antiga existente: conferir antes de conciliar.')
    inputs=json.loads((SOURCE/'entradas.json').read_text())
    original=json.loads((SOURCE/'gabarito_original.json').read_text())
    gold=copy.deepcopy(original); byid={r['id']:r for r in gold}
    payloads={r['id']:json.loads(r['messages'][0]['content']) for r in inputs}
    names=sorted({r['id'].split('-',1)[1].rsplit('-',1)[0] for r in inputs})
    headers={}; sources={}
    # Somente marcadores formais inequívocos de polos; INTDO/AMICUS/ADV não viram parte automaticamente.
    marker=re.compile(r'(?m)^\s*(REQTE|REQDO|RECTE|RECDO|AGTE|AGDO|IMPTE|ADV|PROC|INTDO|RELATOR|AM\.\s*CURIAE)[^\n]*\n')
    for name in names:
        pdf=BASE/'acordaos'/f'{name}.pdf'
        with pymupdf.open(pdf) as doc: text=doc[0].get_text()
        sources[str(pdf.relative_to(BASE))]=sha(pdf)
        method='camada textual'
        if len(text.strip())<200:
            cache=BASE/'resultados/ocr_acordaos'/f'{name}.json'
            text=json.loads(cache.read_text())['paginas'][0]['texto']
            sources[str(cache.relative_to(BASE))]=sha(cache); method='OCR previamente existente'
        # Recorte do rol antes da ementa; preserva o texto integral da primeira página para auditoria.
        end=re.search(r'(?mi)^\s*EMENTA\s*:',text)
        segment=text[:end.start()] if end else text
        marks=list(marker.finditer(segment)); parties=[]
        for j,m in enumerate(marks):
            if m.group(1) not in {'REQTE','REQDO','RECTE','RECDO','AGTE','AGDO','IMPTE'}:continue
            stop=marks[j+1].start() if j+1<len(marks) else len(segment)
            value=' '.join(segment[m.end():stop].split()).lstrip(':• ')
            if value: parties.append({'marcador':m.group(1),'nome_extraido':value})
        headers[name]={'arquivo':str(pdf.relative_to(BASE)),'pagina_pdf':1,'metodo':method,'texto':text,'polos_extraidos':parties}
    audit=[]; checks=[]
    aliases={'conselho federal da ordem dos advogados do brasil cfoab':['conselho federal da oab','ordem dos advogados do brasil'],
             'associacao medica brasileira':['associacao medica brasileira']}
    for row in inputs:
        i=row['id']; name=i.split('-',1)[1].rsplit('-',1)[0]; p=payloads[i]
        targets=[norm(t) for t in p['alvos'].split('|')]; hits=[]
        for party in headers[name]['polos_extraidos']:
            pn=norm(party['nome_extraido']); keys=[pn,*aliases.get(pn,[])]
            for target in targets:
                if target in keys: hits.append({'alvo':target,**party})
        check={'id':i,'alvos':p['alvos'],'fonte_cabecalho':headers[name]['arquivo'],'pagina_pdf':1,'correspondencias':hits,
               'status':'sem correspondência nominal inequívoca; não equivale a comprovar ausência de papel processual'}
        if hits:
            if len(targets)==1:
                check['status']='correspondência exata com polo formal'
                if byid[i]['corpus']!='Excluir':
                    audit.append({'id':i,'antes':copy.deepcopy(byid[i]),'motivo':'Correspondência nominal exata com polo formal no mesmo processo','evidencia':hits})
                    byid[i].update(corpus='Excluir',tipo=None)
            else: check['status']='múltiplos alvos: não excluir a frase automaticamente'
        checks.append(check)
    # Propagação limitada de decisão humana sobre a mesma fala no julgamento conjunto.
    target='AP14-AP_14_ADI_5037-00004'; precedent='AP14-AP_14_ADI_5035-00006'
    assert norm(payloads[target]['mencao'])==norm(payloads[precedent]['mencao'])
    assert byid[precedent]['corpus']=='Excluir'
    assert 'ADVOGADO-GERAL DA UNIÃO' in headers['AP_14_ADI_5037']['texto']
    audit.append({'id':target,'antes':copy.deepcopy(byid[target]),'motivo':'Mesma fala de Adams já excluída pelo pesquisador no acórdão conjunto; identidade textual conferida.',
        'precedente_humano':precedent,'fonte_decisao':'corpus_novo_lote_v4/revisao_v3.json',
        'evidencia':payloads[target]['mencao'],'pagina_ocorrencia':payloads[target]['pagina_pdf']})
    byid[target].update(corpus='Excluir',tipo=None)
    pending={
      'AP14-AP_14_ADI_5037-00006':'Associação Médica Brasileira: requerente da ADI 5035, mas ocorrência na ADI 5037. Não propagar condição de parte entre ações conexas sem decisão metodológica.',
      'AP05-AP_05_ADPF_186-00015':'Manifestação de Eunice Durham lida pela procuradora do DEM. Não confundir leitura de contribuição alheia com alegação própria da parte.',
      'AP15-AP_15_ADI_5062-00049':'Humberto Costa / Senado: Congresso consta como interessado. Não equiparar automaticamente senador, Senado, Congresso e parte.',
      'AP15-AP_15_ADI_5065-00046':'Mesmo ponto sobre Humberto Costa / Senado em ação conexa.',
    }
    for c in checks:
        if c['id'] in pending: c['status']='pendência metodológica separada das métricas principais'
    OUT.mkdir()
    def save(n,x): (OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2))
    save('entradas.json',inputs);save('gabarito_original.json',gold)
    (OUT/'instrucoes.txt').write_text((SOURCE/'instrucoes.txt').read_text())
    save('cabecalhos_processuais.json',headers);save('conferencia_300_ids.json',checks)
    save('alteracoes_partes.json',audit)
    save('pendencias_partes.json',[{'id':i,'motivo':v,'gabarito_provisorio':byid[i],'alvo':payloads[i]['alvos'],'frase':payloads[i]['mencao']} for i,v in pending.items()])
    save('manifesto.json',{'n':300,'sha256':{p.name:sha(p) for p in OUT.iterdir()},
        'fontes_sha256':sources,'preparacao_anterior_sha256':sha(SOURCE/'manifesto.json'),
        'ids_fora_metricas_principais':list(pending),
        'nota':'Conciliação conservadora. INTDO e representantes não foram equiparados automaticamente a partes. Cabeçalhos com E OUTROS podem ser incompletos. Ausência de correspondência não prova elegibilidade. Quatro casos com decisão metodológica necessária continuam nas predições, fora das métricas principais.',
        'alteracoes':len(audit)})
    assert json.loads((OUT/'entradas.json').read_text())==inputs
    print('300 entradas preservadas;',len(audit),'alteração(ões);',len(pending),'pendências fora das métricas principais.')
    for a in audit:print(a['id'],a['motivo'])

if __name__=='__main__':main()
