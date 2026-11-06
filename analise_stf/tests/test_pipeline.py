"""Estatística, determinismo, suporte, unidade audiência, A+B, reconciliação e preservação."""
import itertools
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import estatistica as E

AQUI = Path(__file__).resolve().parents[1]


def test_pmc_correcao_mais_um_nunca_zero():
    assert E.pmc(10.0, np.zeros(99)) == 1 / 100
    assert E.pmc(0.0, np.ones(9)) == 1.0
    assert np.isnan(E.pmc(float('nan'), np.zeros(5)))


def test_sign_flip_exato_bate_com_forca_bruta():
    d = np.array([0.3, -0.1, 0.25, 0.4, 0.05, -0.02])
    obs, p, desc = E.sign_flip_media(d, 0, None)
    vals = [abs(np.dot(s, d) / len(d)) for s in itertools.product([-1, 1], repeat=len(d))]
    assert abs(p - np.mean([v >= abs(obs) - 1e-12 for v in vals])) < 1e-12 and 'exato' in desc
    big = np.random.default_rng(0).normal(0.3, 0.1, 30)
    o2, p2, d2 = E.sign_flip_media(big, 999, E.rng_tag(1, 'x'))
    assert 1 / 1000 <= p2 <= 0.01 and 'Monte Carlo' in d2


def test_spearman_ap_detecta_e_nao_inventa():
    x = np.arange(30.0)
    r, p, _ = E.spearman_ap(x, x + np.random.default_rng(0).normal(0, 1, 30), 999, E.rng_tag(1, 'a'))
    assert r > .95 and p <= 0.002
    assert E.spearman_ap(x, np.random.default_rng(3).permutation(x), 999, E.rng_tag(1, 'b'))[1] > 0.01
    assert np.isnan(E.spearman_ap(x[:3], x[:3], 99, E.rng_tag(1, 'c'))[0])


def test_contraste_reduz_a_um_valor_por_audiencia_sem_permutar_mencoes():
    rows = [(a, g, 1 if (g == 1 and i % 2) else 0) for a in range(6) for g in (0, 1) for i in range(6)]
    m = pd.DataFrame(rows, columns=['audiencia', 'g', 'y'])
    c = E.contraste_por_audiencia(m, 'g', 1, 0, 'y', 3)
    assert len(c) == 6 and c.audiencia.is_unique and np.allclose(c.contraste, 0.5)
    assert len(E.contraste_por_audiencia(m, 'g', 1, 0, 'y', 7)) == 0
    src = (AQUI / 'src/hipoteses.py').read_text(encoding='utf-8') + (AQUI / 'src/estatistica.py').read_text(encoding='utf-8')
    assert 'heterogeneidade_em_blocos' not in src and 'interacao_freedman_lane' not in src and 'contraste_intra' not in src


def test_ols_hc3_rank_e_coeficientes():
    rng = np.random.default_rng(1)
    x = rng.normal(size=40); y = 2 * x + rng.normal(size=40)
    X = np.column_stack([np.ones(40), x])
    f = E.ols_hc3(y, X)
    assert f['ok'] and abs(f['b'][1] - 2) < .6 and f['lo'][1] < f['b'][1] < f['hi'][1]
    assert not E.ols_hc3(y, np.column_stack([X, x]))['ok']  # posto deficiente


def bh_manual(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); q = np.empty(n)
    run = 1.0
    for rank in range(n, 0, -1):
        i = o[rank - 1]; run = min(run, p[i] * n / rank); q[i] = run
    return q


def test_bh_correto_por_familia_preserva_na_e_exige_familia():
    df = pd.DataFrame({'Familia': ['a'] * 4 + ['b'] * 2 + ['c'], 'valor_p': [.01, .02, .03, .5, .04, np.nan, np.nan]})
    q = E.bh(df)['valor_p_BH']
    assert np.allclose(q[:4], bh_manual([.01, .02, .03, .5])) and np.isclose(q[4], .04) and q[5:].isna().all()
    with pytest.raises(ValueError):
        E.bh(pd.DataFrame({'Familia': ['sem_familia'], 'valor_p': [.1]}))


def test_seeds_por_analise_distintas_e_estaveis():
    a1, a2, b = E.rng_tag(5, 'H1').random(3), E.rng_tag(5, 'H1').random(3), E.rng_tag(5, 'H2').random(3)
    assert (a1 == a2).all() and not (a1 == b).all()


def test_determinismo_mesma_seed_mesmos_bytes(execucoes):
    (da, ra), (db, rb) = execucoes['a'], execucoes['b']
    for rel in ['results/h1_h22/matriz_resultados_H1_H22.csv', 'data/processed/mencoes_principal_atores.csv', 'data/processed/ponte_mencao_ator.csv',
                'results/h1_h22/matriz_resultados_H1_H22.json', 'reports/relatorio_consolidado_H1_H22.md']:
        assert (da / rel).read_bytes() == (db / rel).read_bytes(), rel
    pa, pc = ra['mat'].valor_p.to_numpy(float), execucoes['c'][1]['mat'].valor_p.to_numpy(float)
    assert (np.isnan(pa) == np.isnan(pc)).all() and not np.allclose(pa[~np.isnan(pa)], pc[~np.isnan(pc)])
    assert (ra['mat'].N == execucoes['c'][1]['mat'].N).all()


def test_matriz_cobre_H1_H22_e_regras_de_valor_p(execucoes):
    d, r = execucoes['a']
    mat = pd.read_csv(d / 'results/h1_h22/matriz_resultados_H1_H22.csv')
    exig = ['Hipótese', 'Pergunta', 'Variáveis', 'Unidade', 'N', 'Método', 'Estimativa', 'Incerteza', 'valor-p', 'valor-p BH', 'Robustez', 'Interpretação', 'Limitações', 'Situação', 'Análise']
    assert all(c in mat.columns for c in exig)
    prin = mat[mat['Análise'] == 'Principal (A)']
    assert set(prin['Hipótese']) == {f'H{i}' for i in range(1, 23)}   # inclusive inviáveis
    com_p = mat['valor-p'].notna()
    assert (~mat.loc[com_p, 'Situação'].str.startswith(('Inviável', 'Descritivo'))).all()
    assert mat.loc[~com_p, 'valor-p BH'].isna().all()
    mc = com_p & ~mat['Método'].str.contains('p exato (', regex=False)
    assert (mat.loc[mc, 'valor-p'] >= 1 / 500).all() and mc.sum() > 0 and (mat.loc[com_p, 'valor-p BH'] >= mat.loc[com_p, 'valor-p'] - 1e-12).all()
    # BH recomputado de forma independente, por Família
    for _, g in mat[com_p].groupby('Família'):
        assert np.allclose(g['valor-p BH'], bh_manual(g['valor-p']))
    # sem valor-p em hipóteses de heterogeneidade/concentração (pseudorreplicação)
    assert prin[prin['Hipótese'].isin(['H3', 'H6', 'H10', 'H21'])]['valor-p'].isna().all()
    # H19 principal: critério predefinido; alternativa só como sensibilidade rotulada
    h19 = prin[prin['Hipótese'] == 'H19']
    alt = h19[h19['Teste'].str.contains('sensibilidade exploratória')]
    princ = h19[~h19['Teste'].str.contains('sensibilidade exploratória')]
    assert princ['valor-p'].isna().all() and princ['Situação'].str.startswith('Inviável').all()
    assert alt['Situação'].str.startswith(('Exploratório: sensibilidade', 'Inviável')).all() and (alt['Família'] == 'F_sens_elegibilidade').all()
    # H15 original = composição por local; H17 = alvo×local; H22 com as duas dimensões; H21 com nArgumento/nMenções
    assert prin[(prin['Hipótese'] == 'H15') & prin['Teste'].str.startswith('Prevalência')].shape[0] == 3
    assert prin[(prin['Hipótese'] == 'H15') & prin['Teste'].str.contains('análise adicional')]['Família'].eq('F_adicional').all()
    assert prin[prin['Hipótese'] == 'H17']['Teste'].str.contains('Distribuição do tipo de alvo').any()
    h22 = prin[prin['Hipótese'] == 'H22']['Teste']
    assert h22.str.contains('incidência').any() and h22.str.contains('taxa argumentativa das menções com').any()
    h21 = prin[prin['Hipótese'] == 'H21']
    assert h21['Teste'].str.contains('Argumento').any() and h21['Teste'].str.contains('Modelo').any()
    t21 = pd.read_csv(d / 'results/h1_h22/T_H21_ministro_x_categoria_aproveitamento.csv')
    assert {'n_mencoes_com_categoria', 'n_argumento', 'taxa_argumento'} <= set(t21.columns)
    # principal sem A+B; sensibilidade separada e só H19–H22
    assert set(mat[mat['Análise'] != 'Principal (A)']['Hipótese']) <= {'H19', 'H20', 'H21', 'H22'}
    assert not prin['Método'].str.contains(r'A\+B').any()


def test_ap33_preservada_e_fora_de_h2_h16(execucoes):
    d, r = execucoes['a']
    mat = r['mat']
    m = r['ctx'].m
    assert (m[m.audiencia == 33].intervalo_anos == -1).all()
    for h in ('H2', 'H16'):
        row = mat[(mat.Hipotese == h) & (mat.Analise == 'Principal (A)')].iloc[0]
        assert '29' in row.N and ('AP33' in row.Limitacoes or 'AP33' in row.N)


def test_n_nao_infla_por_mencao(execucoes):
    mat = execucoes['a'][1]['mat']
    assert mat[(mat.Hipotese == 'H1')].iloc[0].N.startswith('30 audiências; 1288 menções')


def test_fontes_manifesto_e_decisao(execucoes):
    assert execucoes['antes'] == execucoes['depois']
    man = execucoes['a'][1]['manifesto']
    assert man['entradas_antes'] == man['entradas_depois'] == execucoes['antes'] and man['entradas_inalteradas'] and man['chamadas_api'] == 0
    assert man['modo'] == 'rapida_NAO_FINAL' and man['seeds_por_analise'] and man['decisao_vinculo_institucional']['sha256']
    assert 'config/decisao_vinculo_institucional.json' in man['configuracao'] and man['pacotes']['numpy']
    crcs = [v['crc32_rotulo'] for v in man['seeds_por_analise'].values()]
    assert len(crcs) == len(set(crcs))
    assert man['validacoes_criticas']['json_classificacao_igual_xlsx'] == 405 and man['validacoes_criticas']['n_incorporadas_recalculado'] == 1288


def test_quick_nao_escreve_nos_diretorios_finais():
    import run_all
    with pytest.raises(SystemExit):
        run_all.executar(AQUI, quick=True, figs=False)


def test_relatorio_numeros_reconciliados_com_o_codigo(execucoes):
    d, r = execucoes['a']
    rel = (d / 'reports/relatorio_consolidado_H1_H22.md').read_text(encoding='utf-8')
    assert rel.startswith('> **RODADA RÁPIDA')
    nums = set(json.loads((d / 'results/h1_h22/numeros_relatorio.json').read_text(encoding='utf-8')))
    corpo = re.sub(r'```.*?```', '', rel, flags=re.S)
    corpo = re.sub(r'`[^`]*`|!\[[^\]]*\]\([^)]*\)|\bH\d+\b|\bAP\d+\b|\bF_\w+|[Bb]\d+|\bk=\d|^#+ .*$|^\d+\. ', '', corpo, flags=re.M)
    dec = set(re.findall(r'\d+,\d+', corpo))
    faltam = sorted(x for x in dec if x.lstrip('-+−') not in nums)
    assert not faltam, f'decimais do relatório sem origem no código: {faltam[:10]}'
    # HTML gerado com figuras incorporadas só na rodada com figuras (aqui figs=False): relatório existe
    mat = pd.read_csv(d / 'results/h1_h22/matriz_resultados_H1_H22.csv')
    for h in (f'H{i}' for i in range(1, 23)):
        assert f'### {h} ' in rel and h in set(mat['Hipótese'])


def test_escopo_do_teste_separa_previsto_adicional_e_sensibilidades(execucoes):
    import relatorio
    d, r = execucoes['a']
    mat = pd.read_csv(d / 'results/h1_h22/matriz_resultados_H1_H22.csv')
    assert 'Escopo do teste' in mat.columns and mat['Escopo do teste'].notna().all()
    prin = mat[mat['Análise'] == 'Principal (A)']
    # escopo A+B sempre rotulado; adicionais/elegibilidade nunca contam como previsto principal
    assert mat[mat['Análise'] != 'Principal (A)']['Escopo do teste'].str.contains('sensibilidade de vínculo A+B', regex=False).all()
    assert prin[prin['Teste'].str.contains('análise adicional')]['Escopo do teste'].eq('adicional local×eixo').all()
    assert prin[prin['Teste'].str.contains('sensibilidade exploratória de elegibilidade')]['Escopo do teste'].eq('sensibilidade de elegibilidade').all()
    h19 = prin[(prin['Hipótese'] == 'H19') & (prin['Escopo do teste'] == 'previsto principal')]
    assert len(h19) and h19['valor-p'].isna().all()          # H19 principal previsto: nenhum teste viável
    res = pd.read_csv(d / 'results/h1_h22/resumo_por_hipotese.csv').set_index('Hipótese')
    assert res.loc['H19', 'Previstos com valor-p'] == 0 and 'sensibilidade de elegibilidade' in res.loc['H19', 'Observação de escopo']
    # contagens separadas somam o total de A, sem reclassificar A+B como A
    assert (res['Linhas previstas (A)'] + res['Linhas adicionais/elegibilidade (A)']).sum() == len(prin)
    assert res['Linhas A+B'].sum() == (mat['Análise'] != 'Principal (A)').sum()
    assert relatorio.escopo_teste('Sensibilidade A+B', 'x [sensibilidade exploratória de elegibilidade: ≥2]', 'F') == 'sensibilidade de elegibilidade; sensibilidade de vínculo A+B'


def test_razao_textual_do_ic_ausente():
    import hipoteses
    assert 'em cada eixo' in hipoteses._ic_txt(np.nan, np.nan, '9+10', 10) and 'n=9+10' in hipoteses._ic_txt(np.nan, np.nan, '9+10', 10)
    assert 'no total' in hipoteses._ic_txt(np.nan, np.nan, 7, 10)
    assert 'menos de' not in hipoteses._ic_txt(np.nan, np.nan, '9+10', 10)
    assert hipoteses._ic_txt(0.1, 0.2, 12, 10).startswith('IC95%')


def test_limpeza_arquiva_so_obsoleto_do_pipeline_sem_apagar(tmp_path):
    import limpeza
    for sub in ('data/processed', 'results/h1_h22', 'results/figures/dados', 'results/tables'):
        (tmp_path / sub).mkdir(parents=True)
    arq = {'data/processed/atores_classificados.csv': 'a', 'data/processed/atores_classificados 2.csv': 'b', 'data/processed/ponte_B_diagnostico.csv': 'c',
           'data/processed/audiencia.csv': 'fase1', 'results/h1_h22/T_H6_heterogeneidade.csv': 'velho', 'results/h1_h22/T_H1.csv': 'ok', 'results/figures/fig01.png': 'ok',
           'results/figures/fig01 2.png': 'dup', 'results/tables/por_eixo.csv': 'fase1'}
    for k, v in arq.items():
        (tmp_path / k).write_text(v)
    atuais = {'data/processed/atores_classificados.csv', 'results/h1_h22/T_H1.csv', 'results/figures/fig01.png'}
    mov = limpeza.arquivar_obsoletos(tmp_path, atuais)
    movidos = {m['caminho_original'] for m in mov}
    assert movidos == {'data/processed/atores_classificados 2.csv', 'data/processed/ponte_B_diagnostico.csv', 'results/h1_h22/T_H6_heterogeneidade.csv', 'results/figures/fig01 2.png'}
    assert all((tmp_path / k).exists() for k in atuais | {'data/processed/audiencia.csv', 'results/tables/por_eixo.csv'})
    assert all((tmp_path / m['arquivado_em']).exists() for m in mov) and (tmp_path / 'historico/rascunhos_pre_revisao/NAO_USAR.md').exists()
    assert limpeza.arquivar_obsoletos(tmp_path, atuais) == []   # idempotente
