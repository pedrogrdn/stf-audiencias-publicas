"""Fase 1: auditoria e preparação estrutural; não estima modelos nem altera fontes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import importlib.metadata
import json
import platform
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import openpyxl

COLUNAS = {
    'ID da ocorrência': 'id', 'Audiência': 'audiencia',
    'Ano da audiência': 'ano_audiencia', 'Processo': 'processo',
    'Página PDF': 'pagina_pdf', 'Ministro': 'ministro',
    'Alvo da menção': 'alvo', 'Menção': 'mencao',
    'Decisão de inclusão': 'corpus', 'Tipo da menção': 'tipo',
    'Tema da audiência': 'tema', 'Local no acórdão': 'local',
    'Ano do julgamento': 'ano_julgamento', 'Data do julgamento': 'data_julgamento',
    'Pessoa mencionada': 'pessoa', 'Instituição mencionada': 'instituicao',
    'Número de alvos': 'numero_alvos', 'Arquivo do acórdão': 'arquivo',
    'Fonte do acórdão': 'url', 'Eixo temático': 'eixo',
}
EIXO_A = 'Direitos ambientais, políticas públicas e liberdade de mercado'
EIXO_B = 'Direitos da Personalidade'
APS_A = {2, 6, 7, 8, 9, 10, 12, 14, 18, 19, 28, 29, 30, 31, 33, 36, 38, 41}
APS_B = {1, 3, 4, 5, 11, 13, 15, 16, 17, 22, 32, 35}
BASE_REL = 'outputs/01a02b49-a916-75a0-80da-a7b4fcc952c1/consolidacao_integral_revisada_20261105'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalizar(texto):
    # Somente para detecção de repetições; os textos originais são preservados.
    return re.sub(r'\s+', ' ', str(texto or '')).strip().casefold()


def identificador(*partes):
    return hashlib.sha256(json.dumps(partes, ensure_ascii=False).encode()).hexdigest()[:20]


def vazio(v):
    return v is None or (isinstance(v, str) and not v.strip())


def percentual(v):
    return f'{100 * v:.2f}%'.replace('.', ',')


def inteiro(v):
    return f'{v:,}'.replace(',', '.')


def ler_planilha(path, aba):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        it = iter(wb[aba].values)
        head = next(it)
        return list(head), [dict(zip(head, row)) for row in it if any(not vazio(v) for v in row)]
    finally:
        wb.close()


def salvar_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else ['sem_registros']
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def md_tabela(rows, colunas):
    linhas = ['| ' + ' | '.join(colunas) + ' |', '|' + '|'.join('---' for _ in colunas) + '|']
    for row in rows:
        linhas.append('| ' + ' | '.join(str(row.get(c, '')).replace('|', '/') .replace('\n', ' ') for c in colunas) + ' |')
    return '\n'.join(linhas)


def agregar(rows, keys):
    grupos = defaultdict(list)
    for r in rows:
        grupos[tuple(r[k] for k in keys)].append(r)
    saida = []
    for chave, grupo in sorted(grupos.items(), key=lambda kv: str(kv[0])):
        tipos = Counter(r['tipo'] for r in grupo)
        saida.append(dict(zip(keys, chave)) | {
            'n_mencoes': len(grupo), 'n_contexto': tipos['Contexto'],
            'n_relato': tipos['Relato'], 'n_argumento': tipos['Argumento'],
            'taxa_argumentativa': tipos['Argumento'] / len(grupo),
            'n_arquivos': len({r['arquivo'] for r in grupo}),
            'n_processos': len({r['processo'] for r in grupo}),
            'n_rotulos_ministro': len({r['ministro'] for r in grupo}),
            'n_ap': len({r['audiencia'] for r in grupo}),
            'n_relatorio': sum(r['local'] == 'Relatório' for r in grupo),
            'n_voto_relator': sum(r['local'] == 'Voto do Relator' for r in grupo),
            'n_voto': sum(r['local'] == 'Voto' for r in grupo),
            'n_autoria_nao_plena': sum(r['autoria_completa'] == 0 for r in grupo),
            'n_atribuicao_por_metadados': sum(r['metodo_ministro'] == 'relator identificado nos metadados do acórdão' for r in grupo),
            'ids_ocorrencias': [r['id'] for r in grupo],
        })
    return saida


def executar(args):
    projeto = args.project.resolve()
    source = (args.source or projeto / BASE_REL / 'analise_final_mencoes.xlsx').resolve()
    out = (args.out or projeto / 'analise_stf').resolve()
    specs = Path(__file__).resolve().parents[1] / 'config/hipoteses.json'
    inputs = {
        'planilha_final': source,
        'proveniencia': projeto / BASE_REL / 'base_consolidada.json',
        'extracao': projeto / 'resultados/analise_integral/ocorrencias_classificadas.csv',
        'resumo_extracao': projeto / 'resultados/analise_integral/resumo_execucao.csv',
        'catalogo': projeto / 'outputs/corpus_audiencias_stf_20260821/corpus_audiencias_publicas_stf.xlsx',
        'controle': projeto / 'resultados/controle_acordaos_todos.xlsx',
        'cadastro_acoes': projeto / 'acoes_audiencias_stf.xlsx',
        'atualizacao_documental': projeto / 'outputs/atualizacao_20261105/RELATORIO.md',
        'metodologia': projeto / 'METODOLOGIA_ANALISE_MENCOES_AUDIENCIAS.md',
        'hipoteses': specs,
    }
    pedido = Path(__file__).resolve().parents[1] / 'data/original/pedido_analise_estatistica.md'
    if pedido.exists():
        inputs['pedido'] = pedido
    hashes = {key: sha(p) for key, p in inputs.items()}
    head, raw = ler_planilha(source, 'Menções')
    faltantes = set(COLUNAS) - set(head)
    if faltantes - {'Eixo temático'}:
        raise ValueError(f'Colunas ausentes: {faltantes}')
    if len({r['ID da ocorrência'] for r in raw}) != len(raw):
        raise ValueError('IDs duplicados: interrompida a preparação.')
    with inputs['extracao'].open(encoding='utf-8-sig') as f:
        extra = {r['ocorrencia_id']: r for r in csv.DictReader(f)}
    with inputs['resumo_extracao'].open(encoding='utf-8-sig') as f:
        resumo_extra = list(csv.DictReader(f))
    origens = {r['id']: r for r in json.loads(inputs['proveniencia'].read_text())['records']}
    if set(origens) != {r['ID da ocorrência'] for r in raw}:
        raise ValueError('IDs da fonte de proveniência não conciliam com a planilha.')
    relator = {r['arquivo_acordao']: r['relator_identificado'] for r in resumo_extra}
    rows = []
    for original in raw:
        r = {novo: original.get(antigo) for antigo, novo in COLUNAS.items()}
        for k in ['audiencia', 'ano_audiencia', 'ano_julgamento', 'pagina_pdf', 'numero_alvos']:
            if not vazio(r[k]):
                if int(r[k]) != float(r[k]):
                    raise ValueError(f'Inteiro inválido: {r["id"]}, {k}')
                r[k] = int(r[k])
        expected = EIXO_A if r['audiencia'] in APS_A else EIXO_B if r['audiencia'] in APS_B else None
        if not expected:
            raise ValueError(f'Audiência fora do mapeamento: {r["audiencia"]}')
        if r['eixo'] not in (None, '', expected):
            raise ValueError(f'Eixo divergente: {r["id"]}')
        r['eixo'] = expected
        if r['corpus'] not in {'Incorporar', 'Excluir'}:
            raise ValueError(f'Decisão não conclusiva: {r["id"]}')
        if r['corpus'] == 'Incorporar' and r['tipo'] not in {'Contexto', 'Relato', 'Argumento'}:
            raise ValueError(f'Tipo não conclusivo: {r["id"]}')
        o = origens[r['id']]
        if (r['corpus'], r['tipo'] or None) != (o['corpus_consolidado'], o['tipo_consolidado'] or None):
            raise ValueError(f'Classificação divergente entre fontes: {r["id"]}')
        data = r['data_julgamento']
        if isinstance(data, (date, datetime)):
            data = data.isoformat()[:10]
        elif isinstance(data, str):
            data = datetime.strptime(data, '%d/%m/%Y').date().isoformat()
        else:
            raise ValueError(f'Data inválida: {r["id"]}')
        r['data_julgamento'] = data
        if int(data[:4]) != r['ano_julgamento']:
            raise ValueError(f'Ano/data divergentes: {r["id"]}')
        r['classe_processual'] = re.match(r'^([A-Z]+)\s+\d+', r['processo']).group(1)
        r['defasagem_anos_cadastrada'] = r['ano_julgamento'] - r['ano_audiencia']
        r['cronologia_inconsistente'] = int(r['defasagem_anos_cadastrada'] < 0)
        r['indicador_argumento'] = int(r['tipo'] == 'Argumento') if r['corpus'] == 'Incorporar' else None
        # IDs documentais, não atestados de identidade de sessão/julgamento conjunto.
        r['julgamento_documental_id'] = identificador(r['arquivo'], data)
        r['bloco_ap_data_id'] = identificador(r['audiencia'], data)
        r['autoria_completa'] = int(r['ministro'] not in {'Não identificado automaticamente', 'Alexandre', None, ''})
        r['metodo_ministro'] = extra.get(r['id'], {}).get('ministro_metodo', 'não disponível')
        r['relator_cadastrado_automatico'] = relator.get(r['arquivo'])
        if not r['autoria_completa'] or r['relator_cadastrado_automatico'] in {None, '', 'Não identificado automaticamente'}:
            r['compatibilidade_com_relator'] = 'Indeterminada'
        else:
            r['compatibilidade_com_relator'] = 'Mesmo nome do relator cadastrado' if r['ministro'] == r['relator_cadastrado_automatico'] else 'Nome distinto do relator cadastrado'
        r['origem_classificacao'] = o['origem']
        pessoa, instituicao = not vazio(r['pessoa']), not vazio(r['instituicao'])
        r['tipo_alvo_derivado'] = 'Pessoa e instituição' if pessoa and instituicao else 'Pessoa' if pessoa else 'Instituição' if instituicao else 'Sem pessoa/instituição nos campos'
        r['frase_normalizada_sha256'] = hashlib.sha256(normalizar(r['mencao']).encode()).hexdigest()
        rows.append(r)
    inc = [r for r in rows if r['corpus'] == 'Incorporar']
    assert len(inc) + sum(r['corpus'] == 'Excluir' for r in rows) == len(rows)
    if any(r['id'] not in extra for r in inc):
        raise ValueError('Metadados de extração ausentes para incorporados.')
    tabela_dir = out / 'results/tables'
    diag_dir = out / 'results/diagnostics'
    processed = out / 'data/processed'
    for d in [tabela_dir, diag_dir, processed, out / 'reports']:
        d.mkdir(parents=True, exist_ok=True)
    salvar_csv(processed / 'mencoes_incorporadas.csv', inc)
    niveis = {
        'ministro_julgamento_documental': ['audiencia', 'julgamento_documental_id', 'arquivo', 'processo', 'data_julgamento', 'ministro'],
        'audiencia_julgamento_documental': ['audiencia', 'julgamento_documental_id', 'arquivo', 'processo', 'data_julgamento', 'eixo', 'ano_audiencia', 'ano_julgamento'],
        'audiencia': ['audiencia', 'eixo', 'ano_audiencia', 'tema'],
        'audiencia_data_provisoria': ['audiencia', 'data_julgamento', 'bloco_ap_data_id', 'eixo'],
    }
    bases = {nome: agregar(inc, keys) for nome, keys in niveis.items()}
    for nome, base in bases.items():
        assert sum(r['n_mencoes'] for r in base) == len(inc)
        assert sum(r['n_argumento'] for r in base) == sum(r['indicador_argumento'] for r in inc)
        salvar_csv(processed / f'{nome}.csv', base)
    for nome, keys in {
        'por_ministro': ['ministro'], 'por_local': ['local'],
        'por_ano_julgamento': ['ano_julgamento'], 'por_classe': ['classe_processual'],
        'por_eixo': ['eixo'], 'por_alvo': ['tipo_alvo_derivado'],
        'ministro_eixo': ['ministro', 'eixo'],
        'local_eixo': ['local', 'eixo'],
    }.items():
        salvar_csv(tabela_dir / f'{nome}.csv', [{k: v for k, v in r.items() if k != 'ids_ocorrencias'} for r in agregar(inc, keys)])
    ausencias = [{'variavel': k, 'tipo_python_observado': ', '.join(sorted({type(r[k]).__name__ for r in raw if not vazio(r[k])})), 'ausentes_total': sum(vazio(r[k]) for r in raw), 'ausentes_incorporadas': sum(vazio(r[COLUNAS[k]]) for r in inc)} for k in head]
    salvar_csv(diag_dir / 'variaveis_e_ausencias.csv', ausencias)
    texto_grupos = defaultdict(list)
    estritos = defaultdict(list)
    for r in rows:
        ex = extra[r['id']]
        estritos[(r['arquivo'], r['pagina_pdf'], r['frase_normalizada_sha256'], normalizar(ex['trecho']))].append(r)
    for r in inc:
        texto_grupos[(r['audiencia'], r['data_julgamento'], r['frase_normalizada_sha256'])].append(r)
    duplicatas_estritas = [g for g in estritos.values() if len(g) > 1]
    repeticoes = [g for g in texto_grupos.values() if len({r['arquivo'] for r in g}) > 1]
    rep = []
    for g in repeticoes:
        for r in g:
            rep.append({k: r[k] for k in ['id', 'audiencia', 'processo', 'arquivo', 'pagina_pdf', 'data_julgamento', 'ministro', 'tipo', 'mencao']} | {'grupo_texto': identificador(g[0]['audiencia'], g[0]['data_julgamento'], g[0]['frase_normalizada_sha256']), 'tipos_distintos_no_grupo': len({x['tipo'] for x in g})})
    salvar_csv(diag_dir / 'frases_repetidas_entre_documentos.csv', rep)
    issues = []
    for r in inc:
        motivos = []
        if r['cronologia_inconsistente']:
            motivos.append('Ano de julgamento anterior ao ano cadastrado da audiência')
        if not r['autoria_completa']:
            motivos.append('Nome do ministro ausente ou abreviado; sem unificação automática')
        if r['local'] in {'Relatório', 'Voto do Relator'} and r['compatibilidade_com_relator'] == 'Nome distinto do relator cadastrado':
            motivos.append('Local atribuído ao relator com nome de ministro distinto no cadastro automático')
        for motivo in motivos:
            issues.append({'id': r['id'], 'audiencia': r['audiencia'], 'processo': r['processo'], 'pagina_pdf': r['pagina_pdf'], 'ministro': r['ministro'], 'local': r['local'], 'motivo': motivo, 'ano_audiencia': r['ano_audiencia'], 'data_julgamento': r['data_julgamento']})
    salvar_csv(diag_dir / 'alertas_metadados.csv', issues)
    classes = agregar(inc, ['classe_processual'])
    locais = agregar(inc, ['local'])
    arquivos_inc = {r['arquivo'] for r in inc}
    arquivos_any = {r['arquivo'] for r in rows}
    files_map = defaultdict(set)
    process_map = defaultdict(set)
    for r in inc:
        files_map[r['arquivo']].add(r['audiencia'])
        process_map[r['processo']].add(r['audiencia'])
    with open(inputs['resumo_extracao'], encoding='utf-8-sig') as f:
        doc_rows = list(csv.DictReader(f))
    cobertura = []
    _, catalogo = ler_planilha(inputs['catalogo'], 'Tabela para artigo')
    _, controle = ler_planilha(inputs['controle'], 'controle')
    for c in catalogo:
        ap = c['Número da audiência']
        if not isinstance(ap, int):
            continue
        docs = [d for d in doc_rows if int(d['audiencia']) == ap]
        selected = [r for r in rows if r['audiencia'] == ap]
        valid = [r for r in inc if r['audiencia'] == ap]
        controle_ap = [r for r in controle if r['numero_audiencia'] == ap]
        cobertura.append({'audiencia': ap, 'ano': c['Ano de realização'], 'tema': c['Tema da audiência'], 'n_arquivos_extracao': len(docs), 'n_candidatos': len(selected), 'n_incorporados': len(valid), 'status': 'Com incorporações' if valid else 'Documentos sem candidatos recuperados' if docs and not selected else 'Somente exclusões' if selected else 'Sem documento na extração', 'status_controle': dict(Counter(r['status_merito'] for r in controle_ap))})
    salvar_csv(diag_dir / 'cobertura_catalogo.csv', cobertura)
    doc_counts = Counter(r['arquivo'] for r in inc)
    docs = []
    for d in doc_rows:
        ds = [r for r in inc if r['arquivo'] == d['arquivo_acordao']]
        docs.append({'audiencia': int(d['audiencia']), 'processo': d['processo'], 'arquivo': d['arquivo_acordao'], 'paginas_pdf': int(d['paginas_pdf']), 'candidatos_extraidos': int(d['ocorrencias_candidatas']), 'incorporados': doc_counts[d['arquivo_acordao']], 'relator_cadastrado': d['relator_identificado'], 'metodo_extracao': d['metodo_extracao_texto'], 'datas_observadas': sorted({r['data_julgamento'] for r in ds})})
    salvar_csv(diag_dir / 'documentos_examinados.csv', docs)
    rotulos = sorted({r['ministro'] for r in inc})
    completas = sorted({r['ministro'] for r in inc if r['autoria_completa']})
    pareados = defaultdict(set)
    for r in inc:
        if r['local'] != 'Relatório' and r['compatibilidade_com_relator'] != 'Indeterminada':
            pareados[r['arquivo']].add(r['compatibilidade_com_relator'])
    pares = sum(len(v) == 2 for v in pareados.values())
    suporte_ministros = []
    for ministro in rotulos:
        grupo = [r for r in inc if r['ministro'] == ministro]
        suporte_ministros.append({'ministro': ministro, 'n_mencoes': len(grupo), 'n_audiencias': len({r['audiencia'] for r in grupo}), 'n_documentos': len({r['arquivo'] for r in grupo}), 'n_anos': len({r['ano_julgamento'] for r in grupo}), 'n_eixos': len({r['eixo'] for r in grupo}), 'n_votos_observados_sem_relatorio': len({r['arquivo'] for r in grupo if r['local'] != 'Relatório'}), 'n_atribuicao_por_metadados': sum(r['metodo_ministro'] == 'relator identificado nos metadados do acórdão' for r in grupo)})
    salvar_csv(diag_dir / 'suporte_ministros.csv', suporte_ministros)
    # Não se interpreta rótulo de ministro incompleto como pessoa independente.
    ano_support = [{'ano': ano, 'n_ap': len({r['audiencia'] for r in inc if r['ano_julgamento'] == ano}), 'n_documentos': len({r['arquivo'] for r in inc if r['ano_julgamento'] == ano}), 'n_mencoes': sum(r['ano_julgamento'] == ano for r in inc)} for ano in sorted({r['ano_julgamento'] for r in inc})]
    salvar_csv(diag_dir / 'suporte_anos.csv', ano_support)
    por_eixo = agregar(inc, ['eixo'])
    for e in por_eixo:
        aps = [r for r in bases['audiencia'] if r['eixo'] == e['eixo']]
        e['media_taxas_por_audiencia'] = sum(r['taxa_argumentativa'] for r in aps) / len(aps)
        e['n_audiencias'] = len(aps)
    salvar_csv(tabela_dir / 'por_eixo.csv', [{k: v for k, v in r.items() if k != 'ids_ocorrencias'} for r in por_eixo])
    total = Counter(r['tipo'] for r in inc)
    diagnostico = {
        'n_total': len(rows), 'n_incorporadas': len(inc), 'n_excluidas': len(rows) - len(inc),
        'categorias': dict(total), 'colunas': len(head), 'aps': len({r['audiencia'] for r in inc}),
        'processos_incorporados': len({r['processo'] for r in inc}), 'arquivos_incorporados': len(arquivos_inc),
        'arquivos_com_candidatos': len(arquivos_any), 'arquivos_extracao': len(doc_rows),
        'aps_extracao': len({int(r['audiencia']) for r in doc_rows}), 'audiencias_catalogo': len(cobertura),
        'ministros_rotulos': len(rotulos), 'nomes_completos_distintos': len(completas),
        'n_autoria_nao_plena': sum(not r['autoria_completa'] for r in inc),
        'n_atribuicao_por_metadados': sum(r['metodo_ministro'] == 'relator identificado nos metadados do acórdão' for r in inc),
        'n_cronologia_inconsistente': sum(r['cronologia_inconsistente'] for r in inc),
        'n_incompatibilidade_local_relator': sum('Local atribuído' in r['motivo'] for r in issues),
        'n_grupos_frases_entre_documentos': len(repeticoes), 'n_mencoes_nesses_grupos': sum(map(len, repeticoes)),
        'n_grupos_texto_com_tipos_distintos': sum(len({r['tipo'] for r in g}) > 1 for g in repeticoes),
        'n_grupos_duplicatas_estritas': len(duplicatas_estritas),
        'n_documentos_papel_pareado_provisorio': pares,
        'processos_com_multiplas_aps': {k: sorted(v) for k, v in process_map.items() if len(v) > 1},
        'arquivos_com_multiplas_aps': {k: sorted(v) for k, v in files_map.items() if len(v) > 1},
        'tamanhos_bases': {k: len(v) for k, v in bases.items()},
        'proveniencia_total': dict(Counter(r['origem_classificacao'] for r in rows)),
        'proveniencia_incorporadas': dict(Counter(r['origem_classificacao'] for r in inc)),
        'tipos_sem_pessoa_instituicao': dict(Counter(r['tipo_alvo_derivado'] for r in inc)),
    }
    (diag_dir / 'auditoria.json').write_text(json.dumps(diagnostico, ensure_ascii=False, indent=2), encoding='utf-8')
    plano = json.loads(specs.read_text())
    for h in plano:
        h['Situacao'] = h.pop('situacao')
        h['N'] = h.pop('n_template').format(**diagnostico)
        h['Estimativa'] = 'Não calculada na Fase 1'
        h['Incerteza'] = 'Não estimada na Fase 1'
        h['Significancia'] = 'Não testada'
    salvar_csv(tabela_dir / 'matriz_viabilidade_H1_H18.csv', plano)
    vars_table = md_tabela([{'Variável': a['variavel'], 'Ausências em 1.288': a['ausentes_incorporadas'], 'Tipo lido': a['tipo_python_observado']} for a in ausencias], ['Variável', 'Ausências em 1.288', 'Tipo lido'])
    eixos_table = md_tabela([{'Eixo': e['eixo'], 'Audiências': e['n_audiencias'], 'Menções incorporadas': e['n_mencoes'], 'Argumentos': e['n_argumento'], 'Taxa agregada': percentual(e['taxa_argumentativa']), 'Média por audiência': percentual(e['media_taxas_por_audiencia'])} for e in por_eixo], ['Eixo', 'Audiências', 'Menções incorporadas', 'Argumentos', 'Taxa agregada', 'Média por audiência'])
    class_table = md_tabela([{'Classe': r['classe_processual'], 'Menções': r['n_mencoes'], 'Audiências': r['n_ap'], 'Arquivos': r['n_arquivos']} for r in classes], ['Classe', 'Menções', 'Audiências', 'Arquivos'])
    local_table = md_tabela([{'Local': r['local'], 'Menções': r['n_mencoes'], 'Audiências': r['n_ap']} for r in locais], ['Local', 'Menções', 'Audiências'])
    hip_table = md_tabela([{'H': h['Hipotese'], 'Pergunta': h['Pergunta'], 'Viabilidade': h['Situacao'], 'Unidade e suporte': h['N'], 'Restrição principal': h['Limitacoes']} for h in plano], ['H', 'Pergunta', 'Viabilidade', 'Unidade e suporte', 'Restrição principal'])
    report = f'''# Diagnóstico prévio da análise estatística das audiências públicas do STF

Fase 1 — planejamento e auditoria. Referência documental: 5 de novembro de 2026. Nenhum teste inferencial ou modelo foi executado. Este diagnóstico preserva a decisão de inclusão e o tipo de todas as ocorrências.

## 1. Resultado da conferência

A planilha contém **{inteiro(len(rows))} ocorrências**, **{inteiro(len(inc))} incorporadas** e **{inteiro(len(rows)-len(inc))} excluídas**. O corpus analítico tem {total['Contexto']} Contextos, {total['Relato']} Relatos e {total['Argumento']} Argumentos. A taxa argumentativa global é {percentual(total['Argumento']/len(inc))}, com denominador 1.288 menções incorporadas. Ela descreve a composição do corpus e não a probabilidade de aproveitar uma contribuição apresentada à audiência.

A aba Menções tem **{len(head)} colunas**, pois Eixo temático já foi acrescentado às 19 inicialmente descritas no projeto. Os IDs são únicos; todas as decisões são conclusivas e conciliam com o JSON de proveniência. Não foram encontradas duplicatas pela chave arquivo, página, frase normalizada e trecho de origem ({len(duplicatas_estritas)} grupos). Nenhuma ocorrência foi removida.

Há **{diagnostico['processos_incorporados']} processos e {diagnostico['arquivos_incorporados']} arquivos com incorporações**, não 46 julgamentos comprovadamente independentes. Existem {diagnostico['ministros_rotulos']} rótulos no campo Ministro: {diagnostico['nomes_completos_distintos']} nomes completos distintos, mais Alexandre e Não identificado automaticamente. O diagnóstico não unifica identidades.

## 2. Cobertura documental e população de referência

O catálogo institucional local contém {len(cobertura)} audiências; a extração examinou {len(doc_rows)} arquivos de {diagnostico['aps_extracao']} audiências. Há candidatos em {len(arquivos_any)} arquivos de 30 audiências. A AP 44 possui três arquivos examinados sem candidatos recuperados. A ADC 81 da AP 36 contém candidatos, todos excluídos; a AP 36 permanece representada pela ADI 7187.

As 30 audiências com incorporações correspondem exatamente ao mapeamento temático de 18 e 12 audiências:

{eixos_table}

A taxa agregada divide Argumentos por menções incorporadas no eixo; a média por audiência dá o mesmo peso a cada audiência, independentemente de seu número de menções. São descrições iniciais, sem teste de diferença ou intervalo inferencial.

O banco é um levantamento das ocorrências recuperadas no recorte documental disponível, condicionado à extração e aos critérios de inclusão. Não é um censo comprovado de todas as menções existentes nos PDFs nem de todas as audiências do STF. O controle e a verificação local de atualização de 05/11/2026 registram restrições de publicação e de busca. AP 44 sem candidatos não significa ausência comprovada de referências; as demais audiências sem documentos não devem receber taxas iguais a zero. Não há universo de votos elegíveis para estimar a probabilidade de mencionar a audiência.

## 3. Variáveis e ausências

{vars_table}

Ausência nos campos Pessoa e Instituição é frequentemente estrutural, pois há referências genéricas à audiência. A categoria derivada “Sem pessoa/instituição nos campos” não assegura que o texto seja genérico; o enquadramento principal utiliza apenas a presença desses campos, sem recodificação textual. A coluna Número de alvos mede os alvos extraídos, não participantes únicos. Não foram encontrados campos de Reitera, Refuta ou Convence na base final; essas subcategorias não serão reconstruídas nem incorporadas ao plano principal.

{local_table}

{class_table}

## 4. Unidades analíticas preparadas

- Menção: {len(inc)} linhas incorporadas, com os IDs originais, campos originais e variáveis derivadas separadas.
- Ministro × julgamento documental: {len(bases['ministro_julgamento_documental'])} combinações observadas. A chave documental é arquivo + data cadastrada. Inclui rótulos incompletos e pode reunir relatório e voto; não é cadastro de votos nem garante autoria validada.
- Audiência × julgamento documental: {len(bases['audiencia_julgamento_documental'])} combinações observadas.
- Audiência: {len(bases['audiencia'])} linhas, com sucessos (Argumentos), total de menções incorporadas, proporção e contagens das três categorias.
- Diagnóstico auxiliar audiência × data: {len(bases['audiencia_data_provisoria'])} blocos. Serve para localizar processos potencialmente conexos, sem afirmar identidade de julgamento apenas por coincidência de data.

As somas das quatro bases agregadas conciliam com 1.288 menções e 501 Argumentos. Apenas combinações observadas foram geradas; não foram inventados votos, ministros ausentes ou zeros. No recorte observado, nenhum processo nem arquivo está vinculado a mais de uma audiência. Há audiências com vários processos e, na AP 5, duas datas distintas; as relações não são um-para-um.

## 5. Restrições que afetam a inferência

### 5.1. Repetição textual entre processos

Foram identificados **{len(repeticoes)} grupos de frases normalizadas idênticas**, na mesma audiência e data, presentes em mais de um arquivo, envolvendo **{sum(map(len,repeticoes))} ocorrências**. {diagnostico['n_grupos_texto_com_tipos_distintos']} grupos contêm mais de um tipo classificado. Isso é um sinal para auditar o contexto compartilhado, não prova de duplicação indevida ou erro de classificação: uma mesma frase pode exercer funções distintas. Os grupos estão em results/diagnostics/frases_repetidas_entre_documentos.csv, com IDs, páginas e processos. Nenhum rótulo foi escolhido como prevalente e nenhuma linha foi deduplicada por texto.

Não multiplicar o N inferencial pelo número de processos com textos comuns. A análise inicial por audiência preserva as ocorrências como unidade de contagem, mas usa até 30 blocos para a incerteza. Ela ainda dá maior peso interno a passagens que se repetem entre processos. Uma análise alternativa por passagem documental compartilhada exigirá regra explícita de identificação, resolução de contextos e denominador próprio antes de sua execução. Essa decisão não será feita silenciosamente.

### 5.2. Autoria e localização

Há **{diagnostico['n_autoria_nao_plena']} menções com autoria não plena** (13 Alexandre, quatro não identificadas). Outras **{diagnostico['n_atribuicao_por_metadados']}** receberam o nome do relator por metadados, em vez de cabeçalho ou fala. Assim, presença de um nome não prova que esse ministro proferiu a passagem. O relatório pertence à estrutura documental e não deve ser tratado como voto argumentativo pessoal. A informação de relator disponível é extraída automaticamente: a variável de comparação registra compatibilidade de nomes, sem validar cargo ou autoria.

Há ainda {diagnostico['n_incompatibilidade_local_relator']} ocorrências da AP 41 na página PDF 46 que recebem localização Relatório, mas estão atribuídas a nomes distintos do relator cadastrado. Isso pode refletir falas dentro de uma seção ou limite da extração, não necessariamente erro; consta dos alertas e não foi corrigido automaticamente.

Há {pares} arquivos com menções fora do relatório atribuídas tanto ao relator cadastrado quanto a outro nome completo. Esse é suporte documental provisório para H4, sujeito à validação de autoria e à dependência entre processos conexos. Não há denominador de todos os votos. H3, H4, H7 e H14 devem começar por descrição; modelos individuais exigem tratamento prévio dessa limitação.

### 5.3. Cronologia

Três menções incorporadas na AP 33 (HC 165704) têm julgamento cadastrado em **20/10/2020** e audiência em **2021**. Os IDs terminam em 00001, 00002 e 00010. O conflito também existe no cadastro de ações (audiência: 14/06/2021) e na extração. A auditoria não escolhe qual metadado está correto. O intervalo cadastrado de −1 ano foi preservado e sinalizado. H2 e H16 dependem de esclarecimento desse vínculo temporal; não é aceitável interpretar o valor negativo como tempo de processamento de contribuição futura. H1 pode descrever o ano cadastrado, com sensibilidade futura à AP 33.

Datas exatas de audiências existem em outro cadastro, mas precisam de tratamento para eventos com vários dias: por exemplo, a AP 3 possui várias sessões e o cadastro exibe somente uma data. A preparação usa diferença de anos, não duração exata em dias.

### 5.4. Origem dos rótulos e incerteza

O conjunto integral tem 557 decisões humanas consolidadas e 2.898 previsões sem revisão humana. No corpus incorporado, a distribuição de proveniência é {json.dumps(diagnostico['proveniencia_incorporadas'],ensure_ascii=False)}. Isso não é uma estimativa de erro; os casos revisados não constituem auditoria aleatória. Intervalos de um modelo ou bootstrap de audiências refletiriam a variabilidade sob o desenho/hipóteses adotados e os rótulos observados, não os erros de extração, autoria ou classificação. Não se pode converter a acurácia dos pilotos em margem de erro uniforme dos resultados finais.

## 6. Viabilidade das hipóteses H1–H18

“Viável descritivamente” significa que os campos permitem a descrição; não significa que já exista teste executado, estimativa causal ou conjunto independente de unidades. Os N abaixo indicam suportes observados. A matriz completa, com método proposto e robustez, está em results/tables/matriz_viabilidade_H1_H18.csv.

{hip_table}

## 7. Plano recomendado para a implementação integral

1. Começar pelas descrições de composição por audiência, eixo, ano, classe, localização e alvo; H5, H6, H8, H10, H11 e H12 têm campos diretamente utilizáveis. Produzir gráficos e proporções com denominadores expressos.
2. Para H5, distinguir proporção agregada de menções e média de proporções por audiência (cada uma das 30 com o mesmo peso). A primeira mede composição das menções; a segunda, a audiência média observada. Descrever a heterogeneidade e fazer retirada de uma audiência por vez. Um contraste entre eixos não identifica efeito causal do tema.
3. Antes de testes temporais ou por ministro, esclarecer a cronologia da AP 33 e validar a operacionalização de autoria/relatoria. Uma análise de sensibilidade restrita às atribuições por cabeçalho/fala será útil, mas esse método também não constitui validação manual.
4. Definir cada estimando e unidade de reamostragem. Para comparações temáticas, considerar reamostragem de audiências dentro de cada eixo (18 e 12), condicionada a uma interpretação de superpopulação/exchangeabilidade. Um teste de permutação de rótulos de eixo somente é defensável com hipótese explícita de exchangeabilidade sob a nula; os eixos não foram randomizados. Não usar Fisher ou qui-quadrado nas 1.288 menções como se fossem independentes.
5. Para alvos e localização, preferir contrastes dentro de audiência, com suporte pareado documentado, e reamostragem de blocos; há reutilização de ministros e possível dependência institucional além desses blocos. Modelos binomiais de sucessos/totais ainda precisam tratar sobredispersão e dependência; agregar por si só não resolve esses problemas.
6. Regressões parcimoniosas somente após definir clusters, exposições e suporte: no máximo poucos preditores substantivos com 30 audiências. Não ajustar uma interação para cada ministro/ano. Modelos de contagem não terão offset de votos nem extensão de voto, porque tais exposições não estão disponíveis. Páginas do PDF são metadado do documento, não extensão de cada voto.
7. Se houver testes, separar famílias temáticas de comparações antes de executá-los, registrar valores-p brutos e ajuste Benjamini–Hochberg nos testes executados (não nos resultados inviáveis). Interpretar como exploração de associações. Verificar se múltiplos testes reaproveitam o mesmo contraste (por exemplo, H11/H12 e H2/H16).
8. Relatar toda a base e sensibilidades predefinidas: sem relatório; sem alvos não individualizados; atribuição por cabeçalho/fala; retirada de uma audiência por vez; versão de ocorrência textual compartilhada somente se autorizada e operacionalizada. Não selecionar exclusões para obter significância.

As taxas observadas no recorte documental não precisam de intervalo para serem descritas. Qualquer intervalo para além desse recorte requer explicitar população-alvo, mecanismo de seleção e modelo de variabilidade. Bootstrap não elimina seleção documental, confundimento nem erro de medição.

## 8. Rastreabilidade e próximo passo

O script src/auditar_base.py registra checksums dos insumos e de si próprio, verifica a preservação dos arquivos e gera CSVs derivados e manifesto. A planilha original e as instruções v6.1 não são editadas. O pedido integral está preservado em data/original/pedido_analise_estatistica.md. Os CSVs usam UTF-8 com BOM e mantêm IDs; campos com listas são JSON. A matriz de viabilidade não é matriz de resultados de testes: estimativas, intervalos e significância estão marcados como não executados.

A implementação integral deverá partir deste diagnóstico e das restrições acima. Não houve instalação de bibliotecas, chamada de API, alteração de classificação ou decisão automática sobre os conflitos identificados.
'''
    (out / 'reports/diagnostico_fase1.md').write_text(report, encoding='utf-8')
    if any(sha(inputs[k]) != v for k, v in hashes.items()):
        raise RuntimeError('Um insumo mudou durante a execução.')
    package_names = ['openpyxl', 'pandas', 'numpy', 'scipy', 'statsmodels', 'matplotlib']
    manifest = {
        'fase': '1 — auditoria; sem inferência',
        'executado_em_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'plataforma': platform.platform(),
        'pacotes_disponiveis': {k: bool(importlib.util.find_spec(k)) for k in package_names},
        'versoes_pacotes': {k: importlib.metadata.version(k) for k in package_names if importlib.util.find_spec(k)},
        'script_sha256': sha(Path(__file__)),
        'entradas': {k: {'caminho': str(p.relative_to(projeto)) if p.is_relative_to(projeto) else str(p), 'sha256': hashes[k]} for k, p in inputs.items()},
        'saidas_sha256': {str(p.relative_to(out)): sha(p) for folder in [processed, tabela_dir, diag_dir, out/'reports'] for p in sorted(folder.glob('*')) if p.is_file() and p.name != 'manifesto.json'},
        'invariantes': ['IDs únicos', 'eixos reconciliados', 'tipos e inclusão idênticos ao consolidado', 'somas das bases conciliadas', 'insumos preservados por checksum'],
    }
    (diag_dir / 'manifesto.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(diagnostico, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--out', type=Path)
    executar(parser.parse_args())
