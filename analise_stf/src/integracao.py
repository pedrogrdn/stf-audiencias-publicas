"""Integração menções × atores (nível A direto; nível B apenas diagnóstico).

Não altera nenhuma fonte. IDs de menção e de ator não coincidem; a ponte usa
(audiência, nome normalizado) com split pelo separador explícito do campo.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

from auditar_base import COLUNAS, ler_planilha, sha

ROOT = Path(__file__).resolve().parents[2]
F_MENC = ROOT / 'dados/planilhas/analise_final_mencoes.xlsx'
F_PROV = ROOT / 'dados/fontes/base_consolidada.json'
F_EXT = ROOT / 'dados/fontes/extracao/ocorrencias_classificadas.csv'
F_RESUMO = ROOT / 'dados/fontes/extracao/resumo_execucao.csv'
F_ATORES = ROOT / 'dados/fontes/atores/classificacao_final_pessoas_entidades.xlsx'
F_ATORES_JSON = F_ATORES.parent / 'consolidacao_revisada.json'
AUTORIA_NAO_PLENA = {'Não identificado automaticamente', 'Alexandre', None, ''}  # regra de auditar_base.py
META_RELATOR = 'relator identificado nos metadados do acórdão'


def entradas() -> dict[str, Path]:
    return {'mencoes_xlsx': F_MENC, 'proveniencia_json': F_PROV, 'extracao_csv': F_EXT,
            'resumo_extracao_csv': F_RESUMO, 'atores_xlsx': F_ATORES, 'atores_json': F_ATORES_JSON}


def norm(texto) -> str:
    """Normalização conservadora da chave: sem acentos, caixa, pontuação e espaços."""
    if texto is None or (isinstance(texto, float) and pd.isna(texto)):
        return ''
    t = unicodedata.normalize('NFKD', str(texto))
    t = ''.join(c for c in t if not unicodedata.combining(c)).casefold()
    return re.sub(r'\s+', ' ', re.sub(r'[^0-9a-z]+', ' ', t)).strip()


def dividir(valor, sep: str) -> list[str]:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)) or not str(valor).strip():
        return []
    return [p.strip() for p in str(valor).split(sep) if p.strip()]


def ler_mencoes() -> pd.DataFrame:
    cab, linhas = ler_planilha(F_MENC, 'Menções')
    df = pd.DataFrame(linhas).rename(columns=COLUNAS)
    df['data_julgamento'] = pd.to_datetime(df['data_julgamento'])
    return df


def construir_AB(m: pd.DataFrame, a: pd.DataFrame, res_A: pd.DataFrame, cfg: dict):
    """Sensibilidade A+B. Unidade de referência do vínculo institucional = ENTIDADE (audiência, entidade normalizada).

    A categoria da entidade é proxy: categoria(s) da participação das pessoas afiliadas àquela entidade na audiência.
    Várias pessoas da mesma entidade NÃO viram várias menções nem pesos: a categoria entra uma vez por (menção, categoria).
    Entidade com categorias distintas entre afiliados = contraditória → irresolvida (não entra nas categorias).
    Várias entidades citadas com categorias diferentes = menção multirrótulo resolvida."""
    sep, cats = cfg['separador_multivalor'], cfg['categorias']
    ae = a[a['entidade_norm'] != '']
    ent = ae.groupby(['audiencia', 'entidade_norm']).agg(entidade=('entidade', 'first'), n_grafias_entidade=('entidade', 'nunique'), n_pessoas_afiliadas=('ator_id', 'nunique'),
                                                        categorias=('categoria_final', lambda s: sorted(set(s)))).reset_index()
    ent['n_categorias'] = ent['categorias'].map(len)
    ent['status_categoria'] = ent['n_categorias'].map(lambda n: 'unica' if n == 1 else 'contraditoria_irresolvida')
    ent['categoria_entidade'] = [c[0] if n == 1 else None for c, n in zip(ent['categorias'], ent['n_categorias'])]
    eidx = {(r.audiencia, r.entidade_norm): r for r in ent.itertuples()}
    por_A = {k: set(g['categoria_final']) for k, g in res_A.groupby('ocorrencia_id')}
    nA = res_A.groupby('ocorrencia_id')['ator_id'].nunique().to_dict()
    out, cit = [], {}
    for r in m.itertuples():
        tp, ti = dividir(r.pessoa, sep), dividir(r.instituicao, sep)
        cA = por_A.get(r.id, set())
        res_e, con_e, sem_e = set(), set(), set()
        for tok in ti:
            k = (int(r.audiencia), norm(tok))
            e = eidx.get(k)
            if e is None:
                sem_e.add(k)
            elif e.status_categoria == 'unica':
                res_e.add(k)
            else:
                con_e.add(k)
        cB = {eidx[k].categoria_entidade for k in res_e}
        for k in res_e | con_e:
            cit[k] = cit.get(k, 0) + 1
        todas = sorted(cA | cB)
        n_pess_nao_res = max(0, len({norm(t) for t in tp}) - nA.get(r.id, 0)) if tp else 0
        nao_res = n_pess_nao_res + len(con_e) + len(sem_e)
        if todas:
            estado = 'classificado'
        elif tp or ti:
            estado = 'identificado_irresolvido_categoria_contraditoria' if con_e else 'identificado_sem_classificacao'
        elif r.ext_tipo_alvo == 'audiencia_publica':
            estado = 'generica_nao_aplicavel'   # alvo da extração confirma que se refere à audiência; campos vazios isolados não bastam
        else:
            estado = 'sem_nome_alvo_nao_generico'
        fonte = 'A+B' if (cA and cB) else 'A' if cA else 'B' if cB else ''
        out.append({'id': r.id, 'estado_ator': estado, 'n_atores_A': nA.get(r.id, 0), 'n_entidades_B_resolvidas': len(res_e),
                    'n_entidades_B_contraditorias': len(con_e), 'n_entidades_B_sem_correspondencia': len(sem_e),
                    'n_categorias': len(todas), 'multirrotulo': len(todas) > 1, 'categorias': json.dumps(todas, ensure_ascii=False),
                    'fonte_categoria': fonte, 'categorias_somente_via_B': json.dumps(sorted(cB - cA), ensure_ascii=False),
                    'misto_classificado_e_nao_resolvido': bool(todas and nao_res > 0),
                    **{c: (k in todas) for k, c in cats.items()}})
    ent['n_mencoes_que_citam'] = [cit.get((r.audiencia, r.entidade_norm), 0) for r in ent.itertuples()]
    ent['categorias'] = ent['categorias'].map(lambda c: json.dumps(c, ensure_ascii=False))
    return pd.DataFrame(out), ent


def carregar(cfg: dict) -> dict:
    sep = cfg['separador_multivalor']
    cats = cfg['categorias']
    todas = ler_mencoes()
    val: dict = {'n_linhas_planilha': len(todas), 'n_colunas_planilha': len(COLUNAS),
                 'ids_unicos_planilha': bool(todas['id'].is_unique)}
    m = todas[todas['corpus'] == 'Incorporar'].copy().reset_index(drop=True)
    val['n_incorporadas'] = len(m)
    val['tipos_incorporadas'] = m['tipo'].value_counts().to_dict()
    # sidecars: extração (alvo/tipo_alvo) e proveniência (origem, método de autoria)
    ext = pd.read_csv(F_EXT, usecols=['ocorrencia_id', 'alvo_id', 'alvo_canonico', 'tipo_alvo', 'pessoa', 'instituicao'])  # ordem do arquivo; renomeado por nome
    ext = ext.rename(columns={'ocorrencia_id': 'id', 'alvo_id': 'ext_alvo_id', 'alvo_canonico': 'ext_alvo_canonico',
                              'tipo_alvo': 'ext_tipo_alvo', 'pessoa': 'ext_pessoa', 'instituicao': 'ext_instituicao'})
    prov = pd.DataFrame(json.loads(F_PROV.read_text())['records'])[['id', 'origem', 'metodo_ministro', 'modalidade_revisao', 'tipo_consolidado', 'corpus_consolidado']]
    assert ext['id'].is_unique and prov['id'].is_unique
    m = m.merge(ext, on='id', how='left', validate='1:1').merge(prov, on='id', how='left', validate='1:1')
    val['sidecars_sem_correspondencia'] = int(m['ext_tipo_alvo'].isna().sum() + m['origem'].isna().sum())
    val['xlsx_igual_proveniencia_tipo_corpus'] = bool(((m['tipo'] == m['tipo_consolidado']) & (m['corpus'] == m['corpus_consolidado'])).all())
    val['origem_incorporadas'] = m['origem'].value_counts().to_dict()
    val['pessoa_xlsx_igual_extracao'] = bool((m['pessoa'].fillna('') == m['ext_pessoa'].fillna('')).all())
    val['instituicao_xlsx_igual_extracao'] = bool((m['instituicao'].fillna('') == m['ext_instituicao'].fillna('')).all())

    # ---------------- atores ----------------
    _, rows = ler_planilha(F_ATORES, 'Classificação final')
    a = pd.DataFrame(rows).rename(columns={'Audiência': 'audiencia', 'Nome': 'nome', 'Entidade': 'entidade',
                                           'Menção incorporada': 'mencao_incorporada_xlsx', 'Classificação': 'categoria_final'})
    a['audiencia'] = a['audiencia'].astype(int)
    a['nome_norm'] = a['nome'].map(norm)
    a['entidade_norm'] = a['entidade'].map(norm)
    aj = pd.DataFrame(json.loads(F_ATORES_JSON.read_text())['registros'])
    aj['audiencia'] = aj['audiencia'].astype(int)
    aj['nome_norm'] = aj['nome'].map(norm)
    aj = aj.rename(columns={'id': 'ator_id', 'classificacao': 'categoria_json_classificacao', 'categoria_revisada': 'categoria_json_revisada',
                            'comentario': 'comentario_json', 'entidade': 'entidade_json', 'mencao_incorporada': 'mencao_json'})
    val['atores_xlsx'] = len(a)
    val['atores_chave_unica_xlsx'] = not a.duplicated(['audiencia', 'nome_norm']).any()
    val['atores_chave_unica_json'] = not aj.duplicated(['audiencia', 'nome_norm']).any()
    a = a.merge(aj[['audiencia', 'nome_norm', 'ator_id', 'categoria_json_classificacao', 'categoria_json_revisada', 'comentario_json', 'entidade_json', 'mencao_json']],
                on=['audiencia', 'nome_norm'], how='outer', validate='1:1', indicator=True)
    val['atores_linhas_igualdade_xlsx_json'] = int((a['_merge'] == 'both').sum())
    a = a[a['_merge'] == 'both'].drop(columns='_merge')
    val['ator_ids_unicos'] = bool(a['ator_id'].is_unique)
    val['ator_ids_padrao_APxx_Pxxx'] = bool(a['ator_id'].str.fullmatch(r'AP\d+_P\d+').all())
    val['atores_prefixo_E'] = int(a['ator_id'].str.contains('_E').sum())
    val['atores_entidade_igual'] = bool((a['entidade'].fillna('') == a['entidade_json'].fillna('')).all())
    val['atores_indicador_igual'] = bool((a['mencao_incorporada_xlsx'] == a['mencao_json']).all())
    a['divergencia_categoria_json'] = a['categoria_final'] != a['categoria_json_classificacao']
    # histórico do JSON (categoria_revisada = 'Pendente'): NÃO é erro da planilha final e não autoriza alterar a categoria do XLSX
    a['historico_json_revisada_pendente'] = a['categoria_json_revisada'].fillna('') == 'Pendente'
    val['atores_categorias_xlsx'] = a['categoria_final'].value_counts().to_dict()
    val['atores_categoria_vazia'] = int(a['categoria_final'].isna().sum())
    val['atores_categoria_fora_do_esquema'] = sorted(set(a['categoria_final']) - set(cats))
    val['atores_divergencia_json_xlsx'] = int(a['divergencia_categoria_json'].sum())
    val['atores_historico_json_revisada_pendente'] = int(a['historico_json_revisada_pendente'].sum())
    val['atores_historico_pendente_por_categoria_final'] = a.loc[a['historico_json_revisada_pendente'], 'categoria_final'].value_counts().to_dict()
    val['divergencia_json_xlsx_por_categoria_final'] = a.loc[a['divergencia_categoria_json'], 'categoria_final'].value_counts().to_dict()
    a = a.sort_values(['audiencia', 'ator_id']).reset_index(drop=True)

    # ---------------- ponte A: pessoa ----------------
    idx = {}
    for r in a.itertuples():
        idx.setdefault((r.audiencia, r.nome_norm), []).append(r)
    pa = []  # linhas da ponte (inclui não resolvidos para rastreio)
    for r in m.itertuples():
        for ordem, tok in enumerate(dividir(r.pessoa, sep)):
            cand = idx.get((int(r.audiencia), norm(tok)), [])
            ids = sorted({c.ator_id for c in cand})
            base = {'ocorrencia_id': r.id, 'audiencia': int(r.audiencia), 'ordem_no_campo': ordem, 'campo_origem': 'pessoa',
                    'nome_ou_entidade_original': tok, 'nome_ou_entidade_normalizado': norm(tok), 'nivel_vinculo': 'A'}
            if len(ids) == 1:
                c = cand[0]
                exato = any(x.nome == tok for x in cand)
                pa.append(base | {'status': 'resolvido', 'ator_id': c.ator_id, 'categoria_final': c.categoria_final,
                                  'categoria_json': c.categoria_json_classificacao,
                                  'flag_divergencia_json_xlsx': bool(c.divergencia_categoria_json),
                                  'caminho_match': 'exato' if exato else 'normalizado',
                                  'rotulo_exibicao': cfg['alias_exibicao'].get(c.categoria_final, c.categoria_final)})
            else:
                pa.append(base | {'status': 'ambiguo' if len(ids) > 1 else 'sem_correspondencia', 'ator_id': ';'.join(ids) or None,
                                  'categoria_final': None, 'categoria_json': None, 'flag_divergencia_json_xlsx': None,
                                  'caminho_match': None, 'rotulo_exibicao': None})
    ponte = pd.DataFrame(pa)
    val['tokens_pessoa_total'] = len(ponte)
    val['tokens_pessoa_status'] = ponte['status'].value_counts().to_dict()
    res = ponte[ponte['status'] == 'resolvido']
    n_antes = len(res)
    res = res.drop_duplicates(['ocorrencia_id', 'ator_id'])  # dedup por caminhos/repetição do mesmo nome
    val['pares_A_antes_dedup'] = n_antes
    val['pares_mencao_pessoa_A'] = len(res)
    val['mencoes_diretas_A'] = int(res['ocorrencia_id'].nunique())
    val['atores_diretos_A'] = int(res['ator_id'].nunique())
    val['caminho_match'] = res['caminho_match'].value_counts().to_dict()
    ponte_dedup = pd.concat([res, ponte[ponte['status'] != 'resolvido']], ignore_index=True)

    # ---------------- indicador "Menção incorporada" (metadado do ator) ----------------
    diretos = set(res['ator_id'])
    a['mencao_derivada_nivel_A'] = a['ator_id'].isin(diretos)
    a['mencao_derivada_texto'] = a['mencao_derivada_nivel_A'].map({True: 'Sim', False: 'Não'})
    a['discorda_indicador_xlsx'] = a['mencao_derivada_texto'] != a['mencao_incorporada_xlsx']
    val['indicador_discordancias_com_derivado_A'] = int(a['discorda_indicador_xlsx'].sum())
    val['indicador_sim_xlsx'] = int((a['mencao_incorporada_xlsx'] == 'Sim').sum())
    a['n_mencoes_nivel_A'] = a['ator_id'].map(res.groupby('ator_id').size()).fillna(0).astype(int)

    # ---------------- ponte B (diagnóstico) ----------------
    ent_idx = {}
    for r in a.itertuples():
        if r.entidade_norm:
            ent_idx.setdefault((r.audiencia, r.entidade_norm), []).append(r)
    pb, diag_b = [], []
    for r in m.itertuples():
        toks = dividir(r.instituicao, sep)
        if not toks:
            continue
        casadas, cats_all = 0, set()
        for tok in toks:
            cand = ent_idx.get((int(r.audiencia), norm(tok)), [])
            casadas += bool(cand)
            for c in cand:
                cats_all.add(c.categoria_final)
                pb.append({'ocorrencia_id': r.id, 'ator_id': c.ator_id, 'audiencia': int(r.audiencia), 'campo_origem': 'instituicao',
                           'nome_ou_entidade_original': tok, 'nivel_vinculo': 'B', 'categoria_final': c.categoria_final,
                           'categoria_json': c.categoria_json_classificacao,
                           'flag_divergencia_json_xlsx': bool(c.divergencia_categoria_json),
                           'inferencia': 'candidato de proveniência: categoria da participação de pessoa afiliada à entidade citada; unidade do vínculo = entidade, não pessoa; uso só na sensibilidade A+B'})
        diag_b.append({'ocorrencia_id': r.id, 'audiencia': int(r.audiencia), 'n_instituicoes_citadas': len(toks), 'n_instituicoes_com_entidade_correspondente': casadas,
                       'categorias_candidatas_B': json.dumps(sorted(cats_all), ensure_ascii=False), 'n_categorias_candidatas_B': len(cats_all),
                       'ambigua_B': len(cats_all) > 1, 'tem_vinculo_A': r.id in set(res['ocorrencia_id'])})
    ponte_b = pd.DataFrame(pb)
    diag_b = pd.DataFrame(diag_b)
    val['B_mencoes_com_instituicao'] = len(diag_b)
    val['B_mencoes_com_correspondencia'] = int((diag_b['n_instituicoes_com_entidade_correspondente'] > 0).sum())
    val['B_mencoes_categoria_unica'] = int((diag_b['n_categorias_candidatas_B'] == 1).sum())
    val['B_mencoes_ambiguas'] = int(diag_b['ambigua_B'].sum())
    val['B_uso'] = 'somente_sensibilidade_A+B (decisão do pesquisador em config/decisao_vinculo_institucional.json)'

    # ---------------- tabela principal de menções (1 linha por ocorrência) ----------------
    resolv = res.groupby('ocorrencia_id')
    flags = {c: set() for c in cats}
    por_m = {k: g for k, g in resolv}
    tok_cnt = ponte.groupby('ocorrencia_id')['status'].value_counts().unstack(fill_value=0)
    for col in ['resolvido', 'ambiguo', 'sem_correspondencia']:
        if col not in tok_cnt:
            tok_cnt[col] = 0
    out = []
    for r in m.itertuples():
        g = por_m.get(r.id)
        categorias = sorted(set(g['categoria_final'])) if g is not None else []
        n_at = int(g['ator_id'].nunique()) if g is not None else 0
        tc = tok_cnt.loc[r.id] if r.id in tok_cnt.index else None
        n_res = int(tc['resolvido']) if tc is not None else 0
        n_amb = int(tc['ambiguo']) if tc is not None else 0
        n_sem = int(tc['sem_correspondencia']) if tc is not None else 0
        tem_p, tem_i = bool(dividir(r.pessoa, sep)), bool(dividir(r.instituicao, sep))
        if n_at > 0:
            estado = 'classificado'
        elif tem_p or tem_i:
            estado = 'identificado_sem_classificacao'
        elif r.ext_tipo_alvo == 'audiencia_publica':
            estado = 'generica_nao_aplicavel'
        else:
            estado = 'sem_nome_alvo_nao_generico'
        out.append({'ocorrencia_id': r.id, 'estado_ator': estado, 'n_atores_A': n_at, 'n_categorias': len(categorias),
                    'multirrotulo': len(categorias) > 1, 'categorias': json.dumps(categorias, ensure_ascii=False),
                    'mista_classificado_e_nao_resolvido': bool(n_at > 0 and (n_amb + n_sem) > 0),
                    'n_pessoas_tokens': n_res + n_amb + n_sem, 'n_pessoas_resolvidas_tokens': n_res,
                    'n_pessoas_ambiguas': n_amb, 'n_pessoas_sem_correspondencia': n_sem,
                    'tem_pessoa_campo': tem_p, 'tem_instituicao_campo': tem_i,
                    'classificado_com_instituicao_nao_vinculada_A': bool(n_at > 0 and tem_i),
                    'tem_divergencia_json_xlsx': bool(g['flag_divergencia_json_xlsx'].any()) if g is not None else False,
                    **{c: (k in categorias) for k, c in cats.items()}})
    pm = pd.DataFrame(out)
    m = m.merge(pm, left_on='id', right_on='ocorrencia_id', validate='1:1').drop(columns='ocorrencia_id')
    # derivados
    m['arg'] = (m['tipo'] == 'Argumento').astype(int)
    m['classe'] = m['processo'].str.extract(r'^([A-Za-zÇç]+)')[0]
    m['tipo_alvo_derivado'] = [('Pessoa e instituição' if p and i else 'Pessoa' if p else 'Instituição' if i else 'Sem pessoa/instituição nos campos')
                               for p, i in zip(m['tem_pessoa_campo'], m['tem_instituicao_campo'])]
    m['individualizada'] = (m['tem_pessoa_campo'] | m['tem_instituicao_campo']).astype(int)
    m['autoria_plena'] = (~m['ministro'].isin(AUTORIA_NAO_PLENA)).astype(int)
    m['atribuicao_metadado'] = (m['metodo_ministro'] == META_RELATOR).astype(int)
    m['intervalo_anos'] = m['ano_julgamento'].astype(int) - m['ano_audiencia'].astype(int)
    rel = pd.read_csv(F_RESUMO)[['arquivo_acordao', 'relator_identificado']].drop_duplicates('arquivo_acordao')
    m = m.merge(rel, left_on='arquivo', right_on='arquivo_acordao', how='left').drop(columns='arquivo_acordao')
    m['ministro_eh_relator'] = ((m['ministro'] == m['relator_identificado']) & (m['autoria_plena'] == 1)).astype(int)
    m['relator_indeterminado'] = (m['relator_identificado'].isna() | (m['relator_identificado'] == 'Não identificado automaticamente') | (m['autoria_plena'] == 0)).astype(int)
    m['documento'] = m['arquivo'] + '|' + m['data_julgamento'].dt.strftime('%Y-%m-%d')
    m['audiencia'] = m['audiencia'].astype(int)
    m['ano_julgamento'] = m['ano_julgamento'].astype(int)
    m['ano_audiencia'] = m['ano_audiencia'].astype(int)
    val['estados'] = m['estado_ator'].value_counts().to_dict()
    val['soma_estados_igual_incorporadas'] = bool(sum(val['estados'].values()) == len(m))
    val['mencoes_classificadas'] = int((m['estado_ator'] == 'classificado').sum())
    val['mencoes_mistas'] = int(m['mista_classificado_e_nao_resolvido'].sum())
    val['mencoes_multirrotulo'] = int(m['multirrotulo'].sum())
    val['categorias_mencoes_flags'] = {k: int(m[c].sum()) for k, c in cats.items()}
    val['genericas_tipo_alvo'] = m.loc[m['estado_ator'] == 'generica_nao_aplicavel', 'ext_tipo_alvo'].value_counts().to_dict()
    val['sem_nome_nao_generico_tipo_alvo'] = m.loc[m['estado_ator'] == 'sem_nome_alvo_nao_generico', 'ext_tipo_alvo'].value_counts().to_dict()
    ref = cfg['referencia_plano_integracao']
    val['confere_referencia_plano'] = {
        'pares_mencao_pessoa': val['pares_mencao_pessoa_A'] == ref['pares_mencao_pessoa'],
        'mencoes_diretas': val['mencoes_diretas_A'] == ref['mencoes_diretas'],
        'atores_diretos': val['atores_diretos_A'] == ref['atores_diretos'],
        'incorporadas': val['n_incorporadas'] == ref['mencoes_incorporadas'],
        'atores': val['atores_xlsx'] == ref['atores'],
        'tipos': [val['tipos_incorporadas'].get(k) for k in ('Contexto', 'Relato', 'Argumento')] == [ref['contexto'], ref['relato'], ref['argumento']],
        'origem_claude': val['origem_incorporadas'].get('Claude sem revisão humana') == ref['origem_claude_sem_revisao'],
        'origem_humana': val['origem_incorporadas'].get('Humana consolidada') == ref['origem_humana']}
    ab, ent = construir_AB(m, a, res, cfg)
    val['AB_estados'] = ab['estado_ator'].value_counts().to_dict()
    val['AB_mencoes_classificadas'] = int((ab['estado_ator'] == 'classificado').sum())
    val['AB_mencoes_classificadas_somente_via_B'] = int((ab['fonte_categoria'] == 'B').sum())
    val['AB_mencoes_mistas'] = int(ab['misto_classificado_e_nao_resolvido'].sum())
    val['AB_mencoes_multirrotulo'] = int(ab['multirrotulo'].sum())
    val['AB_entidades_total'] = len(ent)
    val['AB_entidades_contraditorias'] = int((ent['status_categoria'] != 'unica').sum())
    val['AB_categorias_mencoes_flags'] = {k: int(ab[c].sum()) for k, c in cats.items()}
    return {'mencoes': m, 'atores': a, 'ponte': ponte_dedup, 'ponte_B': ponte_b, 'diag_B': diag_b, 'mencoes_AB': ab, 'entidades_B': ent, 'validacao': val}


def hashes_entradas() -> dict:
    return {k: {'caminho': str(p.relative_to(ROOT)), 'sha256': sha(p)} for k, p in entradas().items()}
