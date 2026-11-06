"""Validações críticas de integridade. Qualquer falha LEVANTA ValidacaoErro (o pipeline para antes de produzir resultados).
Contagens são recalculadas das fontes brutas (pandas direto), não copiadas de constantes."""
from __future__ import annotations

import json

import pandas as pd

import integracao as I


class ValidacaoErro(AssertionError):
    pass


def _exigir(cond, msg: str, reg: dict, chave: str, valor=None):
    reg[chave] = valor if valor is not None else bool(cond)
    if not cond:
        raise ValidacaoErro(msg)


def validar_integridade(d: dict, cfg: dict) -> dict:
    reg: dict = {}
    m, a, ponte, ab, ent = d['mencoes'], d['atores'], d['ponte'], d['mencoes_AB'], d['entidades_B']
    cats = set(cfg['categorias'])
    ref = cfg['referencia_plano_integracao']
    # ---- fonte bruta, recalculada
    raw = pd.read_excel(I.F_MENC, sheet_name='Menções')
    _exigir(raw['ID da ocorrência'].is_unique, 'IDs de ocorrência duplicados na planilha', reg, 'planilha_ids_unicos')
    reg['n_linhas_planilha'] = len(raw)
    reg['n_colunas_planilha'] = int(raw.shape[1])
    inc = raw[raw['Decisão de inclusão'] == 'Incorporar']
    reg['n_incorporadas_recalculado'] = len(inc)
    _exigir(len(m) == len(inc) and set(m['id']) == set(inc['ID da ocorrência']), 'corpus incorporado diverge da planilha', reg, 'corpus_igual_planilha')
    _exigir(m['id'].is_unique, 'menções duplicadas no corpus', reg, 'mencoes_ids_unicos')
    tipos = inc['Tipo da menção'].value_counts().to_dict()
    reg['tipos_recalculados'] = tipos
    _exigir(int(m['arg'].sum()) == tipos.get('Argumento', 0), 'Argumento diverge da planilha', reg, 'argumento_confere')
    # ---- atores: XLSX é a autoridade
    xl = pd.read_excel(I.F_ATORES, sheet_name='Classificação final')
    reg['n_atores_xlsx_recalculado'] = len(xl)
    _exigir(len(a) == len(xl) and a['ator_id'].is_unique, 'atores divergem ou IDs duplicados', reg, 'atores_ids_unicos')
    _exigir(not xl.duplicated(['Audiência', 'Nome']).any(), 'chave (audiência, nome) duplicada no XLSX', reg, 'xlsx_chave_unica')
    _exigir(xl['Classificação'].notna().all() and set(xl['Classificação']) <= cats, 'categoria vazia ou fora do esquema no XLSX', reg, 'xlsx_categorias_validas')
    mm = a.merge(xl.rename(columns={'Audiência': 'audiencia', 'Nome': 'nome', 'Classificação': 'cat_xlsx'})[['audiencia', 'nome', 'cat_xlsx']], on=['audiencia', 'nome'], validate='1:1')
    _exigir(len(mm) == len(xl) and (mm['categoria_final'] == mm['cat_xlsx']).all(), 'categoria final diverge do XLSX (autoridade)', reg, 'categoria_final_igual_xlsx')
    reg['categorias_xlsx_recalculado'] = xl['Classificação'].value_counts().to_dict()
    _exigir(a['categoria_final'].value_counts().to_dict() == reg['categorias_xlsx_recalculado'], 'contagens de categorias divergem', reg, 'contagens_categoria_confere')
    n_json_div = int((a['categoria_final'] != a['categoria_json_classificacao']).sum())
    _exigir(n_json_div == 0, f'{n_json_div} categorias divergentes entre XLSX e JSON (classificacao)', reg, 'json_classificacao_igual_xlsx', 405 - n_json_div)
    reg['historico_json_revisada_pendente'] = int(a['historico_json_revisada_pendente'].sum())
    reg['historico_json_revisada_pendente_categoria_final'] = a.loc[a['historico_json_revisada_pendente'], 'categoria_final'].value_counts().to_dict()
    _exigir(int((a['categoria_final'] == 'Partido Político').sum()) == int((xl['Classificação'] == 'Partido Político').sum()), 'Partido Político foi alterado', reg, 'partido_politico_preservado')
    # ---- ponte A
    ok = ponte[ponte['status'] == 'resolvido']
    _exigir(len(ok) == len(ponte), 'tokens de pessoa não resolvidos/ambíguos na ponte', reg, 'ponte_todos_resolvidos', len(ponte))
    _exigir(not ok.duplicated(['ocorrencia_id', 'ator_id']).any(), 'duplicatas (menção, ator) na ponte', reg, 'ponte_sem_duplicatas')
    mp = ok.merge(a[['ator_id', 'audiencia', 'categoria_final']], on='ator_id', suffixes=('', '_ator'))
    _exigir(len(mp) == len(ok) and (mp['audiencia'] == mp['audiencia_ator']).all(), 'ponte cruza audiências', reg, 'ponte_mesma_audiencia')
    _exigir((mp['categoria_final'] == mp['categoria_final_ator']).all(), 'categoria da ponte diverge do cadastro de atores', reg, 'ponte_categoria_igual_cadastro')
    reg.update({'pares_mencao_pessoa_A': len(ok), 'mencoes_diretas_A': int(ok['ocorrencia_id'].nunique()), 'atores_diretos_A': int(ok['ator_id'].nunique())})
    for k, kref in (('pares_mencao_pessoa_A', 'pares_mencao_pessoa'), ('mencoes_diretas_A', 'mencoes_diretas'), ('atores_diretos_A', 'atores_diretos')):
        _exigir(reg[k] == ref[kref], f'{k}={reg[k]} difere da referência do plano ({ref[kref]})', reg, f'confere_{k}', reg[k])
    # ---- estados
    est_a = m['estado_ator']
    _exigir(est_a.notna().all() and est_a.value_counts().sum() == len(m), 'estados não particionam as menções (A)', reg, 'estados_A_particao')
    _exigir(ab['id'].is_unique and set(ab['id']) == set(m['id']), 'tabela A+B não cobre cada menção uma vez', reg, 'AB_uma_linha_por_mencao')
    flags = [c for c in ab.columns if c.startswith('cat_')]
    _exigir((ab[flags].sum(axis=1) == ab['n_categorias']).all(), 'flags de categoria inconsistentes (A+B)', reg, 'AB_flags_consistentes')
    cl_ab = ab['estado_ator'] == 'classificado'
    _exigir(((ab['n_categorias'] > 0) == cl_ab).all(), 'estado classificado ≠ ter categoria válida (A+B)', reg, 'AB_classificado_iff_categoria')
    _exigir(m.loc[m['estado_ator'] == 'classificado', 'id'].isin(ab.loc[cl_ab, 'id']).all(), 'sensibilidade A+B perdeu menções classificadas em A', reg, 'AB_contem_A')
    gen = ab.merge(m[['id', 'ext_tipo_alvo', 'tem_pessoa_campo', 'tem_instituicao_campo']], on='id')
    g = gen[gen['estado_ator'] == 'generica_nao_aplicavel']
    _exigir((g['ext_tipo_alvo'] == 'audiencia_publica').all() and (~g['tem_pessoa_campo'] & ~g['tem_instituicao_campo']).all(), 'genérica sem confirmação do alvo', reg, 'generica_exige_alvo_audiencia')
    outros_validos = gen[(gen['cat_outros']) & (gen['estado_ator'] != 'classificado')]
    _exigir(len(outros_validos) == 0, 'Outros fora de classificado', reg, 'outros_nao_e_NA')
    _exigir(ent.duplicated(['audiencia', 'entidade_norm']).sum() == 0, 'entidade duplicada', reg, 'entidades_chave_unica')
    contra = ent[ent['status_categoria'] != 'unica']
    pend = ab[ab['n_entidades_B_contraditorias'] > 0]
    _exigir(not (pend.loc[pend['estado_ator'] == 'classificado', 'n_categorias'] == 0).any(), 'entidade contraditória classificada', reg, 'contraditoria_irresolvida')
    reg['AB_entidades_contraditorias'] = len(contra)
    reg['A_estados'] = est_a.value_counts().to_dict()
    reg['AB_estados'] = ab['estado_ator'].value_counts().to_dict()
    reg['categorias_flags_A'] = {k: int(m[c].sum()) for k, c in cfg['categorias'].items()}
    reg['categorias_flags_AB'] = {k: int(ab[c].sum()) for k, c in cfg['categorias'].items()}
    # ---- AP33: dado original preservado
    ap33 = m[m['audiencia'] == 33]
    _exigir(len(ap33) > 0 and (ap33['intervalo_anos'] == ap33['ano_julgamento'] - ap33['ano_audiencia']).all(), 'intervalo da AP33 alterado', reg, 'intervalo_ap33_preservado_dado_original', int(ap33['intervalo_anos'].iloc[0]))
    return reg


def decisao_vinculo() -> dict:
    p = I.ROOT / 'analise_stf/config/decisao_vinculo_institucional.json'
    dec = json.loads(p.read_text(encoding='utf-8'))
    if not (dec.get('analise_principal', '').startswith('A') and 'sensibilidade' in dec.get('decisao_pesquisador', '').lower()):
        raise ValidacaoErro('decisão do pesquisador sobre o vínculo institucional ausente ou diferente do esperado')
    return dec
