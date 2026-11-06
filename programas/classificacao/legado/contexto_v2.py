"""Preparação auditável de contexto; executar com o Python documental."""
import collections
import copy
import hashlib
import json
import math
import difflib
import sys
from pathlib import Path
import re
import unicodedata
from pypdf import PdfReader
import openpyxl

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
OUT=ROOT/'contexto_v2'

def norm(s):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()).strip()

def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def clean_page(text):
    # Some STF PDFs repeat the entire text layer. Retain one copy only
    # when the bodies on both sides of the repeated header agree closely.
    parts=text.split('Supremo Tribunal Federal')
    if len(parts)==2:
        a=parts[0].split('Documento assinado digitalmente')[0]
        b=parts[1].split('Documento assinado digitalmente')[0]
        if len(a)>200 and difflib.SequenceMatcher(None,norm(a),norm(b),autojunk=False).ratio()>.85:
            return a.strip()
    return text

def main():
    reuse='--reutilizar-indice' in sys.argv
    if reuse and any((OUT/e/'metricas.json').exists() for e in ['conjunta_contexto','tipo_original','tipo_contexto']):
        raise RuntimeError('Versão já avaliada. Crie nova versão em vez de alterar seus dados.')
    OUT.mkdir(exist_ok=reuse)
    rows=copy.deepcopy(json.loads((ROOT/'registros.json').read_text())['desenvolvimento'])
    byid={r['id']:r for r in rows}
    review=ROOT/'revisao_9_casos.xlsx'
    w=openpyxl.load_workbook(review,read_only=True,data_only=True)
    changes=[]
    for line in w['Revisão'].iter_rows(min_row=8,max_row=16,values_only=True):
        _,ident,oldc,oldt,newc,newt,need,note=line[:8]
        r=byid[ident]
        assert (r['corpus'],r['tipo'])==(oldc,oldt)
        c=newc or oldc
        t=(newt or oldt) if c=='Incorporar' else None
        assert c in ['Incorporar','Excluir','Indeterminado']
        assert c!='Incorporar' or t in ['Contexto','Relato','Argumento','Indeterminado']
        if (c,t)!=(oldc,oldt):changes.append({'id':ident,'antes':{'corpus':oldc,'tipo':oldt},'depois':{'corpus':c,'tipo':t},'origem':'revisao_9_casos.xlsx'})
        r['corpus'],r['tipo']=c,t
        r['messages'][-1]['content']=json.dumps({'corpus':c,'tipo':t},ensure_ascii=False)
    save('correcoes.json',{'arquivo_sha256':digest(review),'alteracoes':changes})
    save('desenvolvimento_corrigido.json',rows)
    paths={PROJECT/'acordaos'/ (r['id'].split('-',1)[1].rsplit('-',1)[0]+'.pdf') for r in rows}
    paths.update((PROJECT/'documentos_audiencias/AP_38').glob('*transcri*.pdf'))
    docs=json.loads((OUT/'indice_documentos.json').read_text()) if reuse else {}
    if reuse:
        for source in json.loads((OUT/'fontes.json').read_text()):
            assert digest(PROJECT/source['arquivo'])==source['sha256'], 'Documento mudou; índice deve ser reconstruído em nova versão'
    if not reuse:
        for p in sorted(paths):
            pages=[pg.extract_text() or '' for pg in PdfReader(p).pages]
            if sum(len(t.strip()) for t in pages)<200:raise RuntimeError(f'PDF sem texto utilizável: {p}')
            docs[str(p.relative_to(PROJECT))]=pages
        save('indice_documentos.json',docs)
    save('fontes.json',[{'arquivo':str(p.relative_to(PROJECT)),'sha256':digest(p),'paginas':len(docs[str(p.relative_to(PROJECT))])} for p in sorted(paths)])
    cleaned={p:[clean_page(t) for t in pages] for p,pages in docs.items()}
    save('limpeza.json',{'regra':'Remover camada textual duplicada apenas se corpos concordarem acima de 0.85; texto bruto preservado no índice','paginas_deduplicadas':sum(a!=b for p in docs for a,b in zip(docs[p],cleaned[p]))})
    transcripts={p:pages for p,pages in cleaned.items() if p.startswith('documentos_audiencias/')}
    stop=set('a o de da do dos das em no na nos nas e que os as um uma para por com se ao aos sobre como pelo pela foi tem mais sua seu este esta isso nao'.split())
    def words(text):return {w for w in re.findall(r'[a-z]{4,}',norm(text)) if w not in stop}
    chunks=[]
    for file,pages in transcripts.items():
        for page,text in enumerate(pages,1):
            for start in range(0,len(text),1800):
                fragment=text[start:start+2200]
                chunks.append({'arquivo':file,'pagina_pdf':page,'inicio_caractere':start,'texto':fragment,'terms':words(fragment)})
    df=collections.Counter(w for c in chunks for w in c['terms'])
    traces=[]
    for r in rows:
        p=r['payload'];file='acordaos/'+r['id'].split('-',1)[1].rsplit('-',1)[0]+'.pdf'
        pages=cleaned[file];page=int(p['pagina_pdf']);assert 1<=page<=len(pages)
        selected=[]
        for n in range(max(1,page-1),min(len(pages),page+1)+1):
            original=pages[n-1]
            start=max(0,len(original)-1800) if n<page else 0
            end=min(len(original),1800) if n>page else len(original)
            selected.append({'arquivo':file,'pagina_pdf':n,'inicio_caractere_texto_limpo':start,'fim_caractere_texto_limpo':end,'texto':original[start:end]})
        # Headings are evidence candidates, not an inferred speaker identity.
        headings=[]
        for n in range(page,max(0,page-25),-1):
            lines=pages[n-1].splitlines()
            found=[x.strip() for x in lines if re.fullmatch(r'\s*(?:V\s*O\s*T\s*O(?:\s*[-–].*)?|Voto Vogal|RELAT[ÓO]RIO(?:\s*[-–].*)?|VOTO[- ]VISTA|VOTO DO SENHOR MINISTRO.*)\s*',x,re.I)]
            if found:
                headings=[{'pagina_pdf':n,'cabecalhos':found}];break
        query=words(str(p['alvos'])+' '+str(p['mencao']))
        names=words(p['alvos'])
        ranked=[]
        for c in chunks:
            overlap=query & c['terms']
            score=sum(math.log((1+len(chunks))/(1+df[t]))*(3 if t in names else 1) for t in overlap)
            if score>0: ranked.append((score,c))
        ranked.sort(key=lambda x:(-x[0],x[1]['arquivo'],x[1]['pagina_pdf'],x[1]['inicio_caractere']))
        retrieved=[];seen=set()
        for score,c in ranked:
            key=(c['arquivo'],c['pagina_pdf'])
            if key in seen:continue
            seen.add(key);retrieved.append({k:v for k,v in c.items() if k!='terms'}|{'pontuacao_lexical':round(score,4)})
            if len(retrieved)==2:break
        extra={'paginas_vizinhas_acordao':selected,'cabecalhos_anteriores_detectados':headings,'trechos_recuperados_audiencia':retrieved,'aviso_recuperacao':'Busca lexical automática: semelhança ou presença na transcrição não prova que a menção do acórdão decorre da audiência. Cabeçalho detectado pode pertencer a outra seção; use o contexto textual.'}
        r['payload_contexto']=p|extra
        traces.append({'id':r['id'],'pagina_ancora':page,'mencao_encontrada_na_pagina':norm(p['mencao']) in norm(pages[page-1]),'fontes_acordao':[{'arquivo':file,'pagina_pdf':x['pagina_pdf']} for x in selected],'fontes_audiencia':[{k:v for k,v in x.items() if k!='texto'} for x in retrieved],'cabecalhos':headings})
    save('desenvolvimento_contexto.json',rows)
    save('rastreabilidade.json',traces)
    print(json.dumps({'casos':len(rows),'correcoes':changes,'documentos':len(docs),'ancoras_confirmadas':sum(t['mencao_encontrada_na_pagina'] for t in traces)},ensure_ascii=False))

if __name__=='__main__':main()
