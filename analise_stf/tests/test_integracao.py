"""Join, contagem única, estados/categorias, filtro de inclusões, nível B isolado."""
import json

import numpy as np
import pandas as pd
import pytest

import integracao as I

CATS = {'Atores públicos', 'Atores privados', 'Sociedade civil', 'Acadêmicos', 'Partido Político', 'Outros'}
ESTADOS = {'classificado', 'identificado_sem_classificacao', 'identificado_irresolvido_categoria_contraditoria', 'generica_nao_aplicavel', 'sem_nome_alvo_nao_generico'}


def test_normalizacao_e_split_conservadores():
    assert I.norm('  Débora   DINIZ. ') == I.norm('debora diniz') == 'debora diniz'
    assert I.norm('Silva, José') == 'silva jose'
    assert I.norm('José da Silva') != I.norm('José Silva')  # sem fuzzy
    assert I.dividir('A | B | C', ' | ') == ['A', 'B', 'C']
    assert I.dividir('SILVA, JOSÉ', ' | ') == ['SILVA, JOSÉ']  # vírgula de nome não separa
    assert I.dividir(None, ' | ') == [] and I.dividir(float('nan'), ' | ') == [] and I.dividir('  ', ' | ') == []


def test_join_independente_bate_com_a_ponte(dados, cfg):
    """Recalcula o join sem usar o código de integração (pandas direto) e compara."""
    raw = pd.read_excel(I.F_MENC, sheet_name='Menções')
    inc = raw[raw['Decisão de inclusão'] == 'Incorporar']
    at = pd.read_excel(I.F_ATORES, sheet_name='Classificação final')
    chaves = set(zip(at['Audiência'].astype(int), at['Nome']))
    pares = set()
    for r in inc.itertuples():
        pessoa = r[inc.columns.get_loc('Pessoa mencionada') + 1]
        if isinstance(pessoa, str):
            for nome in pessoa.split(' | '):
                if (int(r[inc.columns.get_loc('Audiência') + 1]), nome.strip()) in chaves:
                    pares.add((r[1], int(r[inc.columns.get_loc('Audiência') + 1]), nome.strip()))
    pt = dados['ponte']
    ok = pt[pt.status == 'resolvido']
    assert len(ok) == len(pares) == dados['validacao']['pares_mencao_pessoa_A']
    assert ok.ocorrencia_id.nunique() == len({p[0] for p in pares}) == dados['validacao']['mencoes_diretas_A']
    assert ok.ator_id.nunique() == len({(p[1], p[2]) for p in pares}) == dados['validacao']['atores_diretos_A']
    ref = cfg['referencia_plano_integracao']
    assert (len(ok), ok.ocorrencia_id.nunique(), ok.ator_id.nunique()) == (ref['pares_mencao_pessoa'], ref['mencoes_diretas'], ref['atores_diretos'])
    assert (pt.status == 'resolvido').all()  # todos os 380 tokens resolveram; nada ambíguo/sem correspondência


def test_ponte_sem_duplicatas_e_ids_corretos(dados):
    pt = dados['ponte']
    ok = pt[pt.status == 'resolvido']
    assert not ok.duplicated(['ocorrencia_id', 'ator_id']).any()
    assert ok.ator_id.str.fullmatch(r'AP\d+_P\d+').all()
    a = dados['atores']
    assert a.ator_id.is_unique and len(a) == 405
    # audiência da menção = audiência do ator (sem ponte cruzando audiências)
    mp = ok.merge(a[['ator_id', 'audiencia']], on='ator_id', suffixes=('', '_ator'))
    assert (mp.audiencia == mp.audiencia_ator).all()
    assert set(ok.nivel_vinculo) == {'A'}


def test_contagem_unica_por_ocorrencia(dados):
    m = dados['mencoes']
    assert len(m) == 1288 and m.id.is_unique
    n_cat_flags = m[[c for c in m.columns if c.startswith('cat_')]].sum(axis=1)
    assert (n_cat_flags == m.n_categorias).all()
    assert (m.n_atores_A >= m.n_categorias).all()
    assert (m.multirrotulo == (m.n_categorias > 1)).all()
    # mais de um ator da mesma categoria na mesma menção conta a categoria uma vez
    repetidas = m[(m.n_atores_A > m.n_categorias) & (m.n_categorias == 1)]
    assert (repetidas[[c for c in m.columns if c.startswith('cat_')]].sum(axis=1) == 1).all()
    # total global: um tipo por ocorrência
    assert m.arg.sum() == 501 and m.tipo.value_counts().to_dict() == {'Contexto': 509, 'Argumento': 501, 'Relato': 278}


def test_tres_estados_mutuamente_exclusivos_e_categorias_validas(dados):
    m, a = dados['mencoes'], dados['atores']
    assert set(m.estado_ator) <= ESTADOS and m.estado_ator.notna().all()
    assert m.estado_ator.value_counts().sum() == 1288
    cl = m[m.estado_ator == 'classificado']
    assert (cl.n_atores_A > 0).all() and (cl.n_categorias > 0).all()
    ident = m[m.estado_ator == 'identificado_sem_classificacao']
    assert (ident.n_atores_A == 0).all() and (ident.tem_pessoa_campo | ident.tem_instituicao_campo).all()
    gen = m[m.estado_ator == 'generica_nao_aplicavel']
    assert (~gen.tem_pessoa_campo & ~gen.tem_instituicao_campo).all() and (gen.ext_tipo_alvo == 'audiencia_publica').all()
    assert (m[m.estado_ator != 'classificado'].n_categorias == 0).all()  # sem classificação ≠ Outros
    assert not (m.loc[m.estado_ator != 'classificado', 'cat_outros']).any()
    # categorias: XLSX prevalece, Outros é válida, Partido Político preservado, sem vazias
    xl = pd.read_excel(I.F_ATORES, sheet_name='Classificação final')
    assert set(a.categoria_final) == set(xl['Classificação']) == CATS
    assert (a.categoria_final == a.merge(xl.rename(columns={'Audiência': 'audiencia', 'Nome': 'nome'}), on=['audiencia', 'nome'])['Classificação']).all()
    assert (a.categoria_final == 'Partido Político').sum() == 7 and (a.categoria_final == 'Outros').sum() == 19
    assert a.divergencia_categoria_json.sum() == 0 and a.historico_json_revisada_pendente.sum() == 7  # JSON 405/405 = XLSX; Pendente é histórico, não erro


def test_filtro_inclusoes_e_indicador_nao_e_filtro(dados):
    raw = pd.read_excel(I.F_MENC, sheet_name='Menções')
    assert len(raw) == 3455 and raw.shape[1] == 20 and raw['ID da ocorrência'].is_unique
    m = dados['mencoes']
    assert (m.corpus == 'Incorporar').all() and set(m.id) == set(raw.loc[raw['Decisão de inclusão'] == 'Incorporar', 'ID da ocorrência'])
    assert not set(m.id) & set(raw.loc[raw['Decisão de inclusão'] == 'Excluir', 'ID da ocorrência'])
    a = dados['atores']
    assert (a.mencao_incorporada_xlsx == 'Não').sum() == 264 and len(m) == 1288  # indicador não filtra menções
    assert a.discorda_indicador_xlsx.sum() == 0
    assert dados['validacao']['origem_incorporadas'] == {'Claude sem revisão humana': 1019, 'Humana consolidada': 269}


def test_nivel_A_principal_nao_contem_B_e_AB_e_separado(dados):
    m, v = dados['mencoes'], dados['validacao']
    so_inst = m[(m.estado_ator == 'identificado_sem_classificacao')]
    assert len(so_inst) > 0 and not so_inst[[c for c in m.columns if c.startswith('cat_')]].any().any()
    assert v['B_uso'].startswith('somente_sensibilidade')
    assert set(dados['ponte_B'].nivel_vinculo) == {'B'}
    ab = dados['mencoes_AB']
    assert len(ab) == 1288 and ab.id.is_unique
    # A+B só acrescenta: toda menção classificada em A continua com as mesmas categorias
    mm = m.merge(ab, on='id', suffixes=('', '_ab'))
    cl = mm[mm.estado_ator == 'classificado']
    for c in [c for c in m.columns if c.startswith('cat_')]:
        assert (~cl[c] | cl[c + '_ab']).all()
    assert (ab.estado_ator == 'classificado').sum() >= (m.estado_ator == 'classificado').sum()


def _fake(ent_cats, pessoa_cats=()):
    """Mini-cenário sintético para construir_AB: uma audiência, entidade E com pessoas de categorias dadas."""
    import json as _j
    cfg = _j.loads((I.Path(__file__).resolve().parents[1] / 'config/analise_H1_H22.json').read_text(encoding='utf-8'))
    a = pd.DataFrame([{'audiencia': 1, 'nome': f'P{i}', 'entidade': 'Ent X', 'entidade_norm': 'ent x', 'ator_id': f'AP01_P{i:03d}', 'categoria_final': c} for i, c in enumerate(ent_cats)])
    m = pd.DataFrame([{'id': 'm1', 'audiencia': 1, 'pessoa': None, 'instituicao': 'Ent X', 'ext_tipo_alvo': 'instituicao'},
                      {'id': 'm2', 'audiencia': 1, 'pessoa': None, 'instituicao': None, 'ext_tipo_alvo': 'audiencia_publica'},
                      {'id': 'm3', 'audiencia': 1, 'pessoa': None, 'instituicao': None, 'ext_tipo_alvo': 'instituicao'}])
    res = pd.DataFrame(columns=['ocorrencia_id', 'ator_id', 'categoria_final'])
    return I.construir_AB(m, a, res, cfg)


def test_AB_entidade_contraditoria_fica_irresolvida_e_outros_nao_e_NA():
    ab, ent = _fake(['Sociedade civil', 'Acadêmicos'])
    assert ent.status_categoria.iloc[0] == 'contraditoria_irresolvida'
    r = ab.set_index('id')
    assert r.loc['m1', 'estado_ator'] == 'identificado_irresolvido_categoria_contraditoria' and r.loc['m1', 'n_categorias'] == 0
    # genérico exige alvo confirmando audiência; campos vazios isolados não bastam
    assert r.loc['m2', 'estado_ator'] == 'generica_nao_aplicavel' and r.loc['m3', 'estado_ator'] == 'sem_nome_alvo_nao_generico'
    ab2, ent2 = _fake(['Outros', 'Outros', 'Outros'])   # várias pessoas, uma entidade, uma categoria; Outros é válida
    r2 = ab2.set_index('id').loc['m1']
    assert r2.estado_ator == 'classificado' and r2.n_categorias == 1 and bool(r2.cat_outros) and ent2.n_pessoas_afiliadas.iloc[0] == 3
    assert r2.n_entidades_B_resolvidas == 1   # não infla por nº de pessoas afiliadas


def test_validacao_falha_com_duplicata_e_categoria_divergente(dados, cfg):
    import copy
    import validacao as V
    V.validar_integridade(dados, cfg)  # íntegro: passa
    d1 = dict(dados)
    pt = dados['ponte']
    d1['ponte'] = pd.concat([pt, pt.iloc[[0]]], ignore_index=True)
    with pytest.raises(V.ValidacaoErro):
        V.validar_integridade(d1, cfg)
    d2 = dict(dados)
    a = dados['atores'].copy()
    a.loc[a.categoria_final == 'Partido Político', 'categoria_final'] = 'Outros'
    d2['atores'] = a
    with pytest.raises(V.ValidacaoErro):
        V.validar_integridade(d2, cfg)
    d3 = dict(dados)
    a3 = dados['atores'].copy()
    a3.loc[0, 'categoria_json_classificacao'] = 'Outros' if a3.loc[0, 'categoria_final'] != 'Outros' else 'Acadêmicos'
    d3['atores'] = a3
    with pytest.raises(V.ValidacaoErro):
        V.validar_integridade(d3, cfg)


def test_ano_julgamento_unico_por_audiencia(dados):
    m = dados['mencoes']
    assert (m.groupby('audiencia').ano_julgamento.nunique() == 1).all()
    assert m.groupby('audiencia').eixo.nunique().max() == 1
    assert m.audiencia.nunique() == 30
