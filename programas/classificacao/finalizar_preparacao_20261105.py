"""Registra resultado da consulta e libera somente o lote da base verificada."""
import hashlib
import json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
CHECK=BASE/'outputs/atualizacao_20261105/consultas_stf.json'
OUT=BASE/'outputs/execucao_integral_20261105'

def main():
    report=json.loads(CHECK.read_text())
    assert report['concluida'] and len(report['consultas'])==28
    for r in report['consultas']:
        result=r['resultado']
        assert result['status_merito'] in {'SEM_ACORDAO_PRINCIPAL_PUBLICADO','NAO_LOCALIZADO_NA_CONSULTA'},'Há achado novo ou consulta incompleta: integrar antes de liberar.'
        if result['status_merito']=='SEM_ACORDAO_PRINCIPAL_PUBLICADO':
            result.update(status_merito='NAO_LOCALIZADO_NA_CONSULTA',confianca='LIMITADA_A_BUSCA')
            result['evidencia_status']+=' Resultado de busca, não certificação de inexistência; consulta limitada aos dez primeiros resultados e ao título principal.'
    CHECK.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    lines=['# Verificação de acórdãos — 5 de novembro de 2026','',
        'Foram consultadas na jurisprudência oficial do STF as 28 combinações audiência/processo que não tinham acórdão principal publicado no controle anterior. Nenhum novo acórdão principal foi localizado nessas consultas. As 50 publicações já cadastradas foram preservadas, sem novo download.',
        '', 'Escopo e limites: busca pelo número do processo na base de acórdãos, título principal e seção de julgamentos conjuntos; dez primeiros resultados por consulta. Não é certidão de inexistência, busca de novas audiências, nem levantamento de todos os recursos ou decisões incidentais. Os 50 processos com publicação já cadastrada não foram reconsultados. A ausência de título principal não exclui a existência de decisões cautelares, agravos ou repercussão geral.',
        '', 'A AP48 foi consultada como ARE 1542420, corrigindo a referência anterior a ADI 7788, conforme registro metodológico. A planilha original de controle não foi alterada.',
        '', '| Audiência | Processo | Consulta oficial | Resultado |','|---|---|---|---|']
    for r in sorted(report['consultas'],key=lambda x:(x['audiencia'],x['classe'],x['numero'])):
        lines.append(f"| {r['audiencia']} | {r['classe']} {r['numero']} | [STF]({r['consulta_url']}) | Principal não localizado na consulta |")
    (CHECK.parent/'RELATORIO.md').write_text('\n'.join(lines)+'\n')
    release={'liberado':True,'escopo':'Base existente: 50 PDFs; nenhum novo principal localizado na consulta dos 28 registros pendentes.',
        'consulta_sha256':hashlib.sha256(CHECK.read_bytes()).hexdigest(),
        'limite':'Busca limitada aos dez primeiros resultados por processo; não certifica inexistência de outras publicações.'}
    (OUT/'liberacao.json').write_text(json.dumps(release,ensure_ascii=False,indent=2))
    print('Relatório registrado e lote liberado. Nenhuma chamada à API Claude.')

if __name__=='__main__':main()
