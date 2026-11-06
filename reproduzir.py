#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Pedro H. Giordano
"""Verificação e reprodução offline do pacote STF. Não chama classificadores nem APIs."""
from pathlib import Path
import argparse,csv,json,hashlib,collections,sys,shutil,subprocess,datetime,math
ROOT=Path(__file__).resolve().parent
csv.field_size_limit(sys.maxsize)
def rows(name):
 with (ROOT/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verificar():
 allm=rows('dados/mencoes_todas.csv');inc=rows('dados/mencoes_incorporadas.csv');a=rows('dados/participantes.csv');edge=rows('dados/vinculos_mencao_participante.csv');h=rows('dados/participantes_H23.csv');ap=rows('dados/resumo_audiencias_H23.csv')
 checks={
 '3455_candidatos_ids_unicos':len(allm)==len({x['id'] for x in allm})==3455,
 '1288_incorporados_ids_unicos':len(inc)==len({x['id'] for x in inc})==1288,
 'decisoes_conclusivas':collections.Counter(x['corpus'] for x in allm)=={'Incorporar':1288,'Excluir':2167},
 'tipos_finais':collections.Counter(x['tipo'] for x in inc)=={'Contexto':509,'Relato':278,'Argumento':501},
 'corpus_final_vista_incorporados':{x['id'] for x in inc}=={x['id'] for x in allm if x['corpus']=='Incorporar'},
 '405_participacoes_unicas':len(a)==len({x['ator_id'] for x in a})==len({(x['audiencia'],x['nome_norm']) for x in a})==405,
 '6_categorias_405_classificados':collections.Counter(x['categoria_final'] for x in a)=={'Atores públicos':138,'Sociedade civil':120,'Acadêmicos':83,'Atores privados':38,'Outros':19,'Partido Político':7},
 '380_pares_307_mencoes_141_participacoes':len(edge)==len({(x['ocorrencia_id'],x['ator_id']) for x in edge})==380 and len({x['ocorrencia_id'] for x in edge})==307 and len({x['ator_id'] for x in edge})==141,
 'chaves_estrangeiras_validas':{x['ocorrencia_id'] for x in edge}<={x['id'] for x in inc} and {x['ator_id'] for x in edge}<={x['ator_id'] for x in a},
 'H23_preserva_405_participantes':len(h)==405 and {x['ator_id'] for x in h}=={x['ator_id'] for x in a},
 'H23_31_AP_28_comparaveis':len(ap)==len({x['audiencia'] for x in ap})==31 and sum(x['elegivel'].lower()=='true' for x in ap)==28,
 'contexto_preservado':all(x['contexto_acordao'] for x in allm)}
 docs=rows('dados/fontes/documentos_fontes.csv')
 checks['50_acordaos_125_documentos_audiencias']=collections.Counter(x['tipo'] for x in docs)=={'acordao':50,'documento_audiencia':125}
 checks['documentos_integrais_hashes_validos']=all((ROOT/x['arquivo_no_pacote']).is_file() and hashfile(ROOT/x['arquivo_no_pacote'])==x['sha256'] for x in docs)
 assert all(checks.values()),[k for k,v in checks.items() if not v]
 manifest=ROOT/'SHA256SUMS.txt';integrity=0
 if manifest.exists():
  for line in manifest.read_text().splitlines():
   digest,name=line.split('  ',1);p=ROOT/name
   assert p.is_file() and hashfile(p)==digest,'Integridade divergente: '+name
   integrity+=1
 # Checagem conservadora: nomes nunca são usados para decidir categoria ou inclusão.
 report={'validacoes':checks,'arquivos_sha256_verificados':integrity,'chamadas_api':0,'estado':'aprovado'}
 print(json.dumps(report,ensure_ascii=False,indent=2));return report

def workspace(kind):
 dest=ROOT/'reproducoes'/(kind+'_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
 dest.mkdir(parents=True)
 shutil.copytree(ROOT/'analise_stf',dest/'analise_stf',ignore=shutil.ignore_patterns('__pycache__','.scratch','.pytest_cache'))
 shutil.copytree(ROOT/'dados',dest/'dados')
 return dest

def run(args,cwd,log):
 with log.open('w',encoding='utf-8') as stream:
  r=subprocess.run([sys.executable,*args],cwd=cwd,stdout=stream,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError('Comando falhou; consulte '+str(log))

def comparar(a,b,keys,cols):
 def read(p):
  with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
 x,y=read(a),read(b);assert len(x)==len(y),(str(a),len(x),len(y))
 sx={tuple(z[k] for k in keys):z for z in x};sy={tuple(z[k] for k in keys):z for z in y};assert sx.keys()==sy.keys()
 for key in sx:
  for col in cols:
   av,bv=sx[key][col],sy[key][col]
   if av==bv:continue
   try:
    v,w=float(av),float(bv)
    assert math.isclose(v,w,rel_tol=1e-11,abs_tol=1e-12) or (math.isnan(v) and math.isnan(w)),(key,col,av,bv)
   except ValueError:raise AssertionError((key,col,av,bv))
 return {'linhas':len(x),'campos_comparados':cols,'equivalente':True}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verificar',action='store_true');p.add_argument('--testes',action='store_true');p.add_argument('--analises',action='store_true');a=p.parse_args()
 if not any(vars(a).values()):a.verificar=True
 verificar()
 if a.testes:
  w=workspace('testes');run(['testar_H23.py'],w/'analise_stf',w/'preparacao_snapshot_H23.log');run(['-m','pytest','tests','-q','-p','no:cacheprovider'],w/'analise_stf',w/'testes.log');print((w/'testes.log').read_text());print('Testes em',w)
 if a.analises:
  w=workspace('analises');base=w/'analise_stf'
  run(['run_all.py'],base,w/'H1_H22.log')
  run(['testar_H23.py'],base,w/'H23.log')
  results={
   'H1_H22':comparar(ROOT/'analise_stf/results/h1_h22/matriz_resultados_H1_H22.csv',base/'results/h1_h22/matriz_resultados_H1_H22.csv',['Hipótese','Análise','Escopo do teste','Teste'],['estimativa_num','ic_inf','ic_sup','valor-p','valor-p BH']),
   'H23':comparar(ROOT/'analise_stf/results/H23/inferencia.csv',base/'results/H23/inferencia.csv',['analise'],['media','ic95_lo','ic95_hi','p_bruto','p_ajust'])}
  (w/'comparacao_resultados.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False,indent=2));print('Análises em',w)
if __name__=='__main__':main()
