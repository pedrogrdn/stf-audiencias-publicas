"""Verificação não destrutiva dos acórdãos principais das audiências cadastradas."""
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import openpyxl
import localizar_acordaos_stf as localizar

OUT = BASE/'outputs/atualizacao_20261105'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    control = BASE/'resultados/controle_acordaos_todos.xlsx'
    wb = openpyxl.load_workbook(control, read_only=True, data_only=True)
    values = list(wb.active.values)
    rows = [dict(zip(values[0], r)) for r in values[1:]]
    wb.close()
    pending = [r for r in rows if r['status_merito'] != 'MERITO_PUBLICADO']
    path = OUT/'consultas_stf.json'
    report = json.loads(path.read_text()) if path.exists() else {
        'data':'2026-11-05', 'controle_sha256':hashlib.sha256(control.read_bytes()).hexdigest(),
        'escopo':'Acórdãos principais dos processos já cadastrados; não coleta novas audiências nem todos os recursos incidentais.',
        'publicados_no_controle_anterior':50, 'consultas':[], 'previstas':len(pending),
        'concluida':False,
    }
    assert report['controle_sha256']==hashlib.sha256(control.read_bytes()).hexdigest()
    done={r['chave'] for r in report['consultas'] if r['resultado']['status_merito']!='ERRO_LOCALIZACAO'}
    driver=localizar.criar_navegador(Path(tempfile.mkdtemp(prefix='stf_atualizacao_20261105_')))
    driver.set_page_load_timeout(45)
    try:
        driver.get('https://jurisprudencia.stf.jus.br/')
        time.sleep(8)
        for r in pending:
            ap=int(r['numero_audiencia']);cl=r['classe'];num=int(r['numero'])
            note=None
            if ap==48:
                cl,num='ARE',1542420
                note='Correção já documentada na metodologia: AP48 = ARE1542420, não ADI7788. Controle original preservado.'
            key=f'{ap}:{cl}:{num}'
            if key in done:continue
            try:
                result=localizar.localizar(driver,cl,num)
                if result['status_merito']=='SEM_ACORDAO_PRINCIPAL_PUBLICADO':
                    result['status_merito']='NAO_LOCALIZADO_NA_CONSULTA'
                    result['confianca']='LIMITADA_A_BUSCA'
                    result['evidencia_status']+=' Resultado de busca, não certificação de inexistência; consulta limitada aos dez primeiros resultados e ao título principal.'
            except Exception as e:
                result={'status_merito':'ERRO_LOCALIZACAO','erro':str(e)[:700],
                        'evidencia_status':'Falha técnica não demonstra ausência de acórdão.'}
            report['consultas']=[x for x in report['consultas'] if x['chave']!=key]
            report['consultas'].append({'chave':key,'audiencia':ap,'classe':cl,'numero':num,
                'status_anterior':r['status_merito'],'consulta_url':localizar.url_pesquisa(cl,num),
                'nota':note,'resultado':result})
            report['concluida']=len(report['consultas'])==len(pending) and all(x['resultado']['status_merito']!='ERRO_LOCALIZACAO' for x in report['consultas'])
            path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
            print(f"{len(report['consultas'])}/{len(pending)} AP{ap} {cl} {num}: {result['status_merito']}",flush=True)
    finally:driver.quit()
    assert report['controle_sha256']==hashlib.sha256(control.read_bytes()).hexdigest()
    print(path)

if __name__=='__main__':main()
