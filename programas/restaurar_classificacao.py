#!/usr/bin/env python3
"""Restaura a organização histórica da classificação em pasta nova. Nunca chama APIs."""
from pathlib import Path
import argparse,csv,shutil,json
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--destino',type=Path,required=True);a=p.parse_args();dest=a.destino.expanduser().resolve()
 if dest.exists():raise SystemExit('Destino já existe; escolha pasta nova, fora do pacote.')
 if dest==ROOT or ROOT in dest.parents:raise SystemExit('Escolha destino fora do pacote de referência.')
 dest.mkdir(parents=True)
 with (ROOT/'documentacao/proveniencia_arquivos.csv').open(encoding='utf-8-sig',newline='') as f:records=list(csv.DictReader(f))
 seen=set();n=0
 for r in records:
  rel=Path(r['origem_no_projeto'])
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('Caminho não seguro na proveniência')
  if rel.parts[0]=='analise_stf' or r['origem_no_projeto'] in seen:continue
  src=ROOT/r['arquivo_no_pacote'];target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target);seen.add(r['origem_no_projeto']);n+=1
 (dest/'LEIA_PRIMEIRO_RESTAURACAO.md').write_text('Esta pasta reconstitui insumos e programas históricos disponíveis no pacote. Nenhuma API foi chamada. Os documentos integrais incluídos foram restaurados. Caches de OCR e ambientes não foram distribuídos e podem precisar de regeneração. Para verificar o lote de 3.010 casos sem API, executar python scripts/executar_integral_claude.py --verificar. Reclassificar é outra operação, sujeita a custo, credencial própria e confirmação explícita. As respostas preservadas impedem repetir cobranças automaticamente: nunca apague resultados para repetir chamadas sem uma nova pasta de trabalho e revisão do orçamento.\n')
 print(json.dumps({'arquivos_restaurados':n,'destino':str(dest),'chamadas_api':0},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
