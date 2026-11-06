"""Testes de H23: comportamento sobre dados reais e casos sintéticos (não espelham código/texto)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
import testar_H23 as H  # noqa: E402
import integracao  # noqa: E402

PROTO = json.loads((AQUI / 'config/H23_participacao.json').read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def real(dados):
    p = H.construir_participantes(dados['atores'], dados['ponte'], dados['mencoes'], PROTO)
    mg = H.mencao_grupo(dados['mencoes'], dados['ponte'], dados['mencoes_AB'], PROTO)
    return p, mg, H.tabela_ap(p, mg), dados


def test_405_recalculado_do_xlsx_e_31_ap(real):
    p, _, ap, d = real
    _, rows = integracao.ler_planilha(integracao.F_ATORES, 'Classificação final')
    x = pd.DataFrame(rows)
    assert len(x) == len(p) == 405 and x['Audiência'].astype(int).nunique() == len(ap) == 31
    assert set(zip(x['Audiência'].astype(int), x['Nome'])) == set(zip(p['audiencia'], p['nome']))
    assert (p.macrogrupo == 'publico').sum() == 138 and (p.macrogrupo == 'demais').sum() == 267 and p.nome_norm.nunique() == 391
    orig = {(int(a), n): c for a, n, c in zip(x['Audiência'], x['Nome'], x['Classificação'])}
    assert all(orig[(a, n)] == c for a, n, c in zip(p.audiencia, p.nome, p.categoria_original))   # categoria original preservada


def test_sem_duplicata_por_participante_e_ids(real):
    p, *_ = real
    assert not p.duplicated(['audiencia', 'ator_id']).any() and p.ator_id.is_unique
    assert not p.duplicated(['audiencia', 'nome_norm']).any()


def test_zero_observado_nao_mencionados_ficam_no_denominador(real):
    p, _, ap, _ = real
    assert (p.any_mencao == 0).sum() == 405 - 141            # inclui os 'Não' do indicador
    assert set(p.loc[p.any_mencao == 0, 'any_arg']) == {0}
    assert (p.audiencia == 44).sum() == 2 and p.loc[p.audiencia == 44, 'any_mencao'].sum() == 0
    assert (ap.n_publico + ap.n_demais == ap.n_participantes).all() and ap.n_participantes.sum() == 405


def test_indicador_sim_nao_nao_e_filtro(real):
    p, *_ = real
    assert {'Sim', 'Não'} <= set(p.indicador_mencao_xlsx_metadado)
    assert (p.indicador_mencao_xlsx_metadado == 'Não').sum() > 0


def test_ap_sem_grupo_e_indefinida_e_inelegivel_nao_zero(real):
    _, _, ap, _ = real
    sem = ap[(ap.n_publico == 0) | (ap.n_demais == 0)]
    assert len(sem) == 3 and not sem.elegivel.any()
    assert sem.apply(lambda r: np.isnan(r.alcance_publico) if r.n_publico == 0 else np.isnan(r.alcance_demais), axis=1).all()
    assert sem.dif_alcance.isna().all()
    zeros = ap[ap.elegivel & (ap.k_arg_total == 0)]
    assert len(zeros) > 0 and (zeros.dif_alcance == 0).all()       # permanecem, diferença 0


def _sint():
    a = pd.DataFrame({'ator_id': ['AP01_P001', 'AP01_P002', 'AP01_P003', 'AP01_P004'], 'audiencia': 1, 'nome': list('abcd'), 'nome_norm': list('abcd'),
                      'entidade': 'Ent X', 'categoria_final': ['Atores públicos', 'Atores públicos', 'Acadêmicos', 'Outros'], 'mencao_incorporada_xlsx': 'Não'})
    m = pd.DataFrame({'id': ['m1', 'm2', 'm3'], 'audiencia': 1, 'arquivo': ['x.pdf'] * 3, 'tipo': ['Argumento'] * 3, 'corpus': 'Incorporar', 'n_pessoas_tokens': [2, 2, 1]})
    return a, m


def test_macrogrupo_dedup_multiplos_atores_sintetico():
    a, m = _sint()
    pt = pd.DataFrame({'ocorrencia_id': ['m1', 'm1', 'm2', 'm2', 'm3'], 'ator_id': ['AP01_P001', 'AP01_P002', 'AP01_P001', 'AP01_P003', 'AP01_P004'],
                       'status': 'resolvido', 'categoria_final': ['Atores públicos', 'Atores públicos', 'Atores públicos', 'Acadêmicos', 'Outros']})
    ab = pd.DataFrame({'id': ['m1', 'm2', 'm3'], 'cat_atores_publicos': [True, True, False], 'cat_atores_privados': False, 'cat_sociedade_civil': False,
                       'cat_academicos': [False, True, False], 'cat_partido_politico': False, 'cat_outros': [False, False, True]})
    mg = H.mencao_grupo(m, pt, ab, PROTO)
    p = H.construir_participantes(a, pt, m, PROTO)
    t = H.tabela_ap(p, mg).iloc[0]
    assert t.mencoes_arg_A_publico == 2           # m1 (2 públicos) conta 1; m2 (ambos os grupos) também conta no público
    assert t.mencoes_arg_A_demais == 2            # m2 e m3; m2 entra nos dois grupos (não é partição)
    assert t.mencoes_arg_A_publico + t.mencoes_arg_A_demais == 4 > len(mg)
    assert t.k_arg_publico == 2 and t.k_arg_demais == 2 and t.intens_A_publico == 1.0
    assert t.esperado_arg_publico == pytest.approx(4 * 2 / 4)


def test_ab_nao_atribui_individualmente_sintetico():
    a, m = _sint()
    a, m = a.iloc[:2], m.iloc[:1].assign(n_pessoas_tokens=0)
    pt = pd.DataFrame(columns=['ocorrencia_id', 'ator_id', 'status', 'categoria_final'])
    ab = pd.DataFrame({'id': ['m1'], 'cat_atores_publicos': [True], 'cat_atores_privados': False, 'cat_sociedade_civil': False, 'cat_academicos': False,
                       'cat_partido_politico': False, 'cat_outros': False})
    mg = H.mencao_grupo(m, pt, ab, PROTO)
    p = H.construir_participantes(a, pt, m, PROTO)
    t = H.tabela_ap(p, mg).iloc[0]
    assert t.mencoes_arg_AB_publico == 1 and t.mencoes_arg_A_publico == 0       # entra só no macrogrupo, via B
    assert p.any_arg.sum() == 0 and p.n_mencoes_nominais.sum() == 0             # nenhum afiliado recebe a menção


def test_corpus_nao_incorporado_e_excluido_sintetico():
    m = pd.DataFrame({'id': ['a', 'b'], 'corpus': ['Incorporar', 'Excluir'], 'tipo': 'Argumento'})
    assert list(H.mencoes_validas(m)['id']) == ['a']


def test_corpus_real_todos_incorporados(real):
    *_, d = real
    assert (d['mencoes'].corpus == 'Incorporar').all() and len(d['mencoes']) == 1288


def test_consistencia_tabelas_resultados(real):
    p, mg, ap, _ = real
    R = AQUI / 'results/H23'
    saved = pd.read_csv(R / 'por_AP.csv', encoding='utf-8-sig')
    part = pd.read_csv(AQUI / 'data/H23/participantes.csv', encoding='utf-8-sig')
    assert len(part) == 405 and part.any_arg.sum() == p.any_arg.sum() == saved.k_arg_total.sum()
    pd.testing.assert_series_equal(saved['dif_alcance'], ap['dif_alcance'], check_names=False, check_dtype=False)
    inf = json.loads((R / 'inferencia.json').read_text(encoding='utf-8'))
    manual = np.mean([100 * (g[g.macrogrupo == 'demais'].any_arg.mean() - g[g.macrogrupo == 'publico'].any_arg.mean())
                      for _, g in part.groupby('audiencia') if g.macrogrupo.nunique() == 2])
    assert inf['A_alcance']['media'] == pytest.approx(manual) and inf['A_alcance']['n_AP'] == 28
    assert inf['A_alcance']['p_ajust'] >= inf['A_alcance']['p_bruto'] - 1e-12


def test_cobertura_ap_com_documento(real):
    p, *_ = real
    res = pd.read_csv(integracao.F_RESUMO)
    col = [c for c in res.columns if 'audi' in c.lower()][0]
    assert set(p.audiencia) <= set(res[col].astype(str).str.extract(r'(\d+)')[0].astype(int))


def test_manifesto_fontes_inalteradas():
    man = json.loads((AQUI / 'results/H23/manifesto_H23.json').read_text(encoding='utf-8'))
    assert man['inalterados'] and man['hashes_antes'] == man['hashes_depois'] == H.hashes_protegidos()
    assert man['protocolo']['sha256'] == H.sha_arq(H.PROTO)


def test_sign_flip_sintetico_exato():
    r = H.contraste([1, 1, 1, 1, 1, 1], 't', 1, 999, 10)
    assert r['p_bruto'] == pytest.approx(2 / 64) and np.isnan(r['ic95_lo'])    # exato; sem IC com n<10
