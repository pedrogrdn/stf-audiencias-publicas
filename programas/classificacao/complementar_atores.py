import sys,json,re
from pathlib import Path
from classificar_atores import P,O,norm,save
from pypdf import PdfReader
rows=json.loads((O/'entradas.json').read_text());extra=[]
ocr=json.loads((P/'resultados/ocr_documentos_audiencias/AP_01_120_notas_taquigr_ficas.json').read_text())['paginas']
docs={}
for p in (P/'documentos_audiencias/AP_03').glob('*.pdf'):
    if 'taquigraf' in p.name:
        docs[str(p.relative_to(P))]=[page.extract_text() or '' for page in PdfReader(p).pages]
try:
    from docx import Document
    p=P/'documentos_audiencias/AP_03/116_notas_taquigr_ficas.docx'
    docs[str(p.relative_to(P))]=['\n'.join(x.text for x in Document(p).paragraphs)]
except ImportError:pass
for r in rows:
    if sum(len(e['texto']) for e in r['excertos'])>=100:continue
    ex=[]
    sources={r['fonte_cadastro']:[x['texto'] for x in ocr]} if r['audiencia']==1 else docs
    name=norm(r['nome']);tokens=name.split()
    for file,pages in sources.items():
        hits=[]
        for i,text in enumerate(pages):
            nt=norm(text);pos=nt.find(name)
            if pos<0 and len(tokens)>2:
                pos=nt.find(' '.join(tokens[:2]))
                if pos>=0 and tokens[-1] not in nt[pos:pos+150]:pos=-1
            if pos>=0:hits.append((i,pos,text))
        for i,pos,text in hits[:2]:
            start=max(0,pos-1400);excerpt=text[start:start+6500]
            ex.append({'arquivo':file,'pagina_pdf':i+1 if file.endswith('.pdf') else None,'texto':excerpt,'extracao':'OCR local existente' if r['audiencia']==1 else 'texto documental'})
            if i+1<len(pages) and len(excerpt)<3000:ex.append({'arquivo':file,'pagina_pdf':i+2 if file.endswith('.pdf') else None,'texto':pages[i+1][:3500]})
        if len(ex)>=4:break
    if not ex and r['audiencia']==1:
        for page in [int(x) for x in re.findall(r'\d+',r['paginas_cadastro'])][:1]:
            for i in range(max(0,page-2),min(len(ocr),page+1)):ex.append({'arquivo':r['fonte_cadastro'],'pagina_pdf':i+1,'texto':ocr[i]['texto']})
    extra.append(r|{'excertos':ex})
save(O/'complementos_contexto.json',extra)
print('Complementados:',len(extra),'sem texto:',[(x['id'],x['nome']) for x in extra if not x['excertos']])
