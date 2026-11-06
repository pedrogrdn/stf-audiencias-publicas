"""H23 — adendo independente (exploratório). Reexecutável SEM API:  .venv/bin/python testar_H23.py
Lê fontes (somente leitura), escreve apenas em data/H23, results/H23, reports/H23_participacao.
Não executa o pipeline H1–H22 e não altera nenhuma fonte/resultado existente."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / 'src'))
import estatistica as E  # noqa: E402
import integracao as I  # noqa: E402

PROTO = AQUI / 'config/H23_participacao.json'
D_OUT, R_OUT, REP = AQUI / 'data/H23', AQUI / 'results/H23', AQUI / 'reports/H23_participacao'
PUB, DEM = 'publico', 'demais'
ROTULO = {PUB: 'Atores públicos', DEM: 'Demais (acad., privados, soc. civil, partidos, outros)'}


# ------------------------------------------------------------------ utilidades
def sha_arq(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_dir(d: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(d.rglob('*')):
        if p.is_file():
            h.update(str(p.relative_to(d)).encode()); h.update(sha_arq(p).encode())
    return h.hexdigest()


def hashes_protegidos() -> dict:
    out = {'entradas_integracao': I.hashes_entradas(), 'processed': {p.name: sha_arq(p) for p in sorted((AQUI / 'data/processed').glob('*.csv'))},
           'results_h1_h22': sha_dir(AQUI / 'results/h1_h22'), 'config_H1_H22': sha_arq(AQUI / 'config/analise_H1_H22.json')}
    for r in ['relatorio_consolidado_H1_H22.html', 'relatorio_consolidado_H1_H22.md']:
        out[r] = sha_arq(AQUI / 'reports' / r)
    out['versao_orientadora'] = sha_dir(AQUI / 'reports/versao_orientadora')
    return out


def macrogrupo(cat: str, proto: dict) -> str:
    return PUB if cat in proto['grupos']['publico'] else DEM


# ------------------------------------------------------------------ construção
def mencoes_validas(m: pd.DataFrame) -> pd.DataFrame:
    """Só menções incorporadas (corpus 'Incorporar'); exclusões de partes/bibliografia/contexto da extração permanecem."""
    return m[m['corpus'] == 'Incorporar']


def construir_participantes(a: pd.DataFrame, ponte: pd.DataFrame, m: pd.DataFrame, proto: dict) -> pd.DataFrame:
    """1 linha por participação (AP,pessoa). Denominador = TODOS os atores; sem filtro por indicador."""
    mv = mencoes_validas(m).set_index('id')
    pa = ponte[(ponte['status'] == 'resolvido') & (ponte['ocorrencia_id'].isin(mv.index))].copy()
    pa['tipo'] = pa['ocorrencia_id'].map(mv['tipo'])
    pa['uni'] = pa['ocorrencia_id'].map(mv['n_pessoas_tokens']) == 1
    pa = pa.drop_duplicates(['ocorrencia_id', 'ator_id'])
    g = pa.groupby('ator_id')
    p = a[['ator_id', 'audiencia', 'nome', 'nome_norm', 'entidade', 'categoria_final', 'mencao_incorporada_xlsx']].copy()
    p = p.rename(columns={'categoria_final': 'categoria_original', 'mencao_incorporada_xlsx': 'indicador_mencao_xlsx_metadado'})
    p['macrogrupo'] = p['categoria_original'].map(lambda c: macrogrupo(c, proto))
    p['n_mencoes_nominais'] = p['ator_id'].map(g.size()).fillna(0).astype(int)
    for t in ['Argumento', 'Relato', 'Contexto']:
        p[f'n_{t.lower()}_nominais'] = p['ator_id'].map(pa[pa['tipo'] == t].groupby('ator_id').size()).fillna(0).astype(int)
    p['n_argumento_unipessoa'] = p['ator_id'].map(pa[(pa['tipo'] == 'Argumento') & pa['uni']].groupby('ator_id').size()).fillna(0).astype(int)
    p['any_mencao'] = (p['n_mencoes_nominais'] > 0).astype(int)
    p['any_arg'] = (p['n_argumento_nominais'] > 0).astype(int)
    p['any_arg_unipessoa'] = (p['n_argumento_unipessoa'] > 0).astype(int)
    p['nome_repete_em_outra_AP'] = p.duplicated('nome_norm', keep=False)
    return p.sort_values(['audiencia', 'ator_id']).reset_index(drop=True)


def mencao_grupo(m: pd.DataFrame, ponte: pd.DataFrame, ab: pd.DataFrame, proto: dict) -> pd.DataFrame:
    """1 linha por menção Argumento: flags de macrogrupo (A) e (A+B); cada menção 1x por macrogrupo."""
    mv = mencoes_validas(m)
    mv = mv[mv['tipo'] == 'Argumento'][['id', 'audiencia', 'arquivo', 'n_pessoas_tokens']]
    pa = ponte[ponte['status'] == 'resolvido'].copy()
    pa['mg'] = pa['categoria_final'].map(lambda c: macrogrupo(c, proto))
    fl = pa.groupby('ocorrencia_id')['mg'].agg(lambda s: set(s))
    mv = mv.assign(A_pub=mv['id'].map(lambda i: PUB in fl.get(i, set())), A_dem=mv['id'].map(lambda i: DEM in fl.get(i, set())))
    abx = ab.set_index('id')
    outros = [c for c in ['cat_privados', 'cat_atores_privados', 'cat_sociedade_civil', 'cat_academicos', 'cat_partido_politico', 'cat_outros']]
    mv['AB_pub'] = mv['id'].map(abx['cat_atores_publicos']).astype(bool)
    mv['AB_dem'] = mv['id'].map(abx[[c for c in outros if c in abx]].any(axis=1)).astype(bool)
    return mv.reset_index(drop=True)


def tabela_ap(p: pd.DataFrame, mg: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por AP (todas as 31). Grupo sem participante => taxa NaN (indefinida), nunca 0."""
    rows = []
    for ap, g in p.groupby('audiencia'):
        r = {'audiencia': int(ap), 'n_participantes': len(g)}
        for k in (PUB, DEM):
            s = g[g['macrogrupo'] == k]
            n = len(s)
            r[f'n_{k}'] = n
            r[f'k_arg_{k}'] = int(s['any_arg'].sum())
            r[f'k_arg_uni_{k}'] = int(s['any_arg_unipessoa'].sum())
            r[f'k_qualquer_mencao_{k}'] = int(s['any_mencao'].sum())
            r[f'alcance_{k}'] = r[f'k_arg_{k}'] / n if n else np.nan
            r[f'alcance_uni_{k}'] = r[f'k_arg_uni_{k}'] / n if n else np.nan
            x = mg[mg['audiencia'] == ap]
            for lab, col in [('A', 'A_' + ('pub' if k == PUB else 'dem')), ('AB', 'AB_' + ('pub' if k == PUB else 'dem'))]:
                sel = x[x[col]]
                r[f'mencoes_arg_{lab}_{k}'] = len(sel)
                r[f'intens_{lab}_{k}'] = len(sel) / n if n else np.nan
                if lab == 'A':
                    r[f'docs_arg_A_{k}'] = sel['arquivo'].nunique()
                    r[f'intens_docs_A_{k}'] = sel['arquivo'].nunique() / n if n else np.nan
        r['k_arg_total'] = r['k_arg_publico'] + r['k_arg_demais']
        r['elegivel'] = bool(r['n_publico'] >= 1 and r['n_demais'] >= 1)
        r['motivo_inelegivel'] = '' if r['elegivel'] else ('sem participante nos demais' if r['n_demais'] == 0 else 'sem participante público')
        r['elegivel_ge3'] = bool(r['n_publico'] >= 3 and r['n_demais'] >= 3)
        for k in (PUB, DEM):
            r[f'esperado_arg_{k}'] = r['k_arg_total'] * r[f'n_{k}'] / r['n_participantes']
            r[f'obs_menos_esp_{k}'] = r[f'k_arg_{k}'] - r[f'esperado_arg_{k}']
        for nome, a_, b_ in [('alcance', 'alcance_demais', 'alcance_publico'), ('alcance_uni', 'alcance_uni_demais', 'alcance_uni_publico'),
                             ('intens_A', 'intens_A_demais', 'intens_A_publico'), ('intens_AB', 'intens_AB_demais', 'intens_AB_publico'),
                             ('intens_docs', 'intens_docs_A_demais', 'intens_docs_A_publico')]:
            r[f'dif_{nome}'] = (r[a_] - r[b_]) * (100 if nome.startswith('alcance') else 1) if r['elegivel'] else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ inferência
def contraste(d, tag: str, seed: int, B: int, min_ci: int) -> dict:
    d = np.asarray(d, float); d = d[np.isfinite(d)]
    n = len(d)
    out = {'n_AP': n, 'media': float(d.mean()) if n else np.nan, 'mediana': float(np.median(d)) if n else np.nan,
           'n_pos': int((d > 1e-12).sum()), 'n_neg': int((d < -1e-12).sum()), 'n_zero': int((np.abs(d) <= 1e-12).sum())}
    if n < 2:
        return out | {'p_bruto': np.nan, 'ic95_lo': np.nan, 'ic95_hi': np.nan, 'metodo_p': 'n/d'}
    _, p, desc = E.sign_flip_media(d, B, E.rng_tag(seed, tag + '_signflip'))
    out |= {'p_bruto': p, 'metodo_p': desc + '; simetria das diferenças sob H0'}
    if n >= min_ci:
        lo, hi = E.bootstrap_media(d, B, E.rng_tag(seed, tag + '_boot'))
        out |= {'ic95_lo': lo, 'ic95_hi': hi, 'ic_metodo': f'bootstrap percentil de AP inteiras (B={B})'}
    else:
        out |= {'ic95_lo': np.nan, 'ic95_hi': np.nan, 'ic_metodo': f'não reportado (n_AP<{min_ci})'}
    return out


def wilcoxon(d) -> dict:
    from scipy.stats import wilcoxon as w
    d = np.asarray(d, float); d = d[np.isfinite(d)]
    if (np.abs(d) > 1e-12).sum() < 5:
        return {'p_wilcoxon': np.nan}
    return {'p_wilcoxon': float(w(d, zero_method='wilcox', method='auto').pvalue)}


def loo(ap: pd.DataFrame, col: str, seed: int, B: int, min_ci: int) -> pd.DataFrame:
    e = ap[ap['elegivel']]
    rows = []
    for _, r in e.iterrows():
        d = e.loc[e['audiencia'] != r['audiencia'], col].to_numpy()
        c = contraste(d, f'H23_loo_{col}_{int(r["audiencia"])}', seed, B, 10 ** 9)
        rows.append({'desfecho': col, 'AP_removida': int(r['audiencia']), 'n_AP': c['n_AP'], 'media': c['media'], 'p_bruto': c['p_bruto']})
    return pd.DataFrame(rows)


def pooled(ap: pd.DataFrame, p: pd.DataFrame, apenas_elegiveis: bool) -> dict:
    s = ap[ap['elegivel']] if apenas_elegiveis else ap
    r = {'escopo': 'AP elegíveis' if apenas_elegiveis else 'todas as AP', 'n_AP': len(s)}
    for k in (PUB, DEM):
        n, kk = s[f'n_{k}'].sum(), s[f'k_arg_{k}'].sum()
        r |= {f'n_{k}': int(n), f'k_arg_{k}': int(kk), f'alcance_pooled_{k}': kk / n if n else np.nan,
              f'mencoes_A_{k}': int(s[f'mencoes_arg_A_{k}'].sum()), f'intens_pooled_A_{k}': s[f'mencoes_arg_A_{k}'].sum() / n if n else np.nan,
              f'esperado_estratificado_{k}': s[f'esperado_arg_{k}'].sum()}
    K = r['k_arg_publico'] + r['k_arg_demais']
    r['K_pessoas_com_arg'] = int(K)
    r['dif_pooled_alcance_pp'] = (r['alcance_pooled_demais'] - r['alcance_pooled_publico']) * 100
    r['dif_pooled_intens'] = r['intens_pooled_A_demais'] - r['intens_pooled_A_publico']
    r['share_roster_publico_pooled'] = r['n_publico'] / (r['n_publico'] + r['n_demais'])
    r['share_arg_publico_pooled'] = r['k_arg_publico'] / K if K else np.nan
    r['share_arg_publico_esperado_estratificado'] = r['esperado_estratificado_publico'] / K if K else np.nan
    return r


# ------------------------------------------------------------------ figuras
def fig_b64(fig) -> str:
    b = io.BytesIO(); fig.savefig(b, format='png', dpi=130, bbox_inches='tight'); return base64.b64encode(b.getvalue()).decode()


def figuras(ap: pd.DataFrame, pl: dict, res: dict, loo_df: pd.DataFrame) -> dict[str, tuple[str, bytes]]:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out = {}
    e = ap[ap['elegivel']].sort_values('dif_alcance').reset_index(drop=True)
    # F1 alcance por AP
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    y = np.arange(len(e))
    ax.hlines(y, e['alcance_publico'] * 100, e['alcance_demais'] * 100, color='#bbb')
    ax.scatter(e['alcance_publico'] * 100, y, c='#1f4e79', label='Públicos', zorder=3)
    ax.scatter(e['alcance_demais'] * 100, y, c='#d98c1f', label='Demais', zorder=3)
    ax.set_yticks(y); ax.set_yticklabels([f"AP{int(a):02d} (n={int(a_p)}|{int(a_d)})" for a, a_p, a_d in zip(e['audiencia'], e['n_publico'], e['n_demais'])], fontsize=7)
    ax.set_xlabel('% dos participantes com ≥1 menção Argumento (vínculo nominal A)')
    ax.set_title(f'Alcance individual por AP elegível (n={len(e)} AP; participantes {int(e.n_publico.sum())} públicos | {int(e.n_demais.sum())} demais)', fontsize=9)
    ax.legend(); out['fig1_alcance_por_AP.png'] = ('Alcance por AP', fig_b64(fig)); plt.close(fig)
    # F2 composição
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    v = [pl['all']['share_roster_publico_pooled'], pl['all']['share_arg_publico_esperado_estratificado'], pl['all']['share_arg_publico_pooled']]
    ax.bar(['Roster (pooled)\n405 participantes', 'Esperado entre\npessoas com Arg\n(estratificado por AP)', 'Observado entre\npessoas com Arg\n(pooled)'], np.array(v) * 100, color=['#999', '#8fb3d9', '#1f4e79'])
    for i, x in enumerate(v): ax.text(i, x * 100 + 1, f'{x * 100:.1f}%', ha='center')
    ax.set_ylabel('% de atores públicos'); ax.set_ylim(0, 100)
    ax.set_title(f"Parcela de públicos (31 AP; {pl['all']['K_pessoas_com_arg']} pessoas com Argumento)", fontsize=9)
    out['fig2_composicao_obs_esp.png'] = ('Composição', fig_b64(fig)); plt.close(fig)
    # F3 intensidade por AP
    e = e.sort_values('dif_intens_A').reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    ax.barh(np.arange(len(e)), e['dif_intens_A'], color=np.where(e['dif_intens_A'] >= 0, '#d98c1f', '#1f4e79'))
    ax.set_yticks(np.arange(len(e))); ax.set_yticklabels([f"AP{int(a):02d}" for a in e['audiencia']], fontsize=7); ax.axvline(0, color='k', lw=.8)
    ax.set_xlabel('Diferença (demais − públicos) em menções Argumento por participante do grupo')
    ax.set_title(f'Intensidade por AP elegível (n={len(e)}); laranja = maior nos demais', fontsize=9)
    out['fig3_intensidade_por_AP.png'] = ('Intensidade', fig_b64(fig)); plt.close(fig)
    # F4 sensibilidades (dois painéis: escalas distintas)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, pref, tit, xl in [(axs[0], ('A_', 'S1_alcance', 'S4_'), 'Alcance', 'diferença média (p.p.)'), (axs[1], ('B_intens', 'S1_intens', 'S5_', 'S6_'), 'Intensidade', 'menções Argumento por participante')]:
        items = [(k, v) for k, v in res.items() if k.startswith(pref)]
        for i, (k, v) in enumerate(items[::-1]):
            ax.scatter(v['media'], i, c='k')
            if np.isfinite(v.get('ic95_lo', np.nan)): ax.hlines(i, v['ic95_lo'], v['ic95_hi'], color='k')
        ax.set_yticks(range(len(items))); ax.set_yticklabels([f"{k} (n={v['n_AP']})" for k, v in items[::-1]], fontsize=7)
        ax.axvline(0, color='r', lw=.8); ax.set_xlabel(f'{xl}, demais − públicos'); ax.set_title(tit, fontsize=9)
    fig.subplots_adjust(wspace=0.85)
    fig.suptitle('Sensibilidades: estimativa por AP e IC95% bootstrap (n AP indicado)', fontsize=9)
    out['fig4_sensibilidades.png'] = ('Sensibilidades', fig_b64(fig)); plt.close(fig)
    return out


# ------------------------------------------------------------------ relatório
def f(x, d=2): return 'n/d' if x is None or not np.isfinite(x) else f'{x:.{d}f}'.replace('.', ',')


def texto_relatorio(proto, p, ap, res, pl, loo_df, val, fam) -> str:
    A, B_ = res['A_alcance'], res['B_intensidade']
    P = pl['all']; PE = pl['eleg']
    inel = ap[~ap['elegivel']]
    def veredito(r, unid):
        if not np.isfinite(r['p_bruto']): return 'inconclusivo (sem teste)'
        sig = r['p_ajust'] < 0.05
        dire = 'maior nos demais' if r['media'] > 0 else 'maior nos públicos' if r['media'] < 0 else 'sem diferença média'
        return (f'H0 rejeitada ao nível 5% (p ajustado BH = {f(r["p_ajust"], 3)}); direção {dire}' if sig else
                f'H0 NÃO rejeitada (p ajustado BH = {f(r["p_ajust"], 3)}); estimativa pontual {dire}, sem evidência suficiente — resultado inconclusivo/negativo, não prova de igualdade')
    ci = lambda r, esc='': (f'IC95% [{f(r["ic95_lo"])}; {f(r["ic95_hi"])}]{esc}' if np.isfinite(r.get('ic95_lo', np.nan)) else 'IC não reportado')
    s1, s4, s5, s6 = res['S1_alcance_ge3'], res['S4_alcance_unipessoa'], res['S5_intens_AB'], res['S6_intens_docs']
    lo_a = loo_df[loo_df.desfecho == 'dif_alcance']; lo_b = loo_df[loo_df.desfecho == 'dif_intens_A']
    maior_cont = 'públicos' if P['k_arg_publico'] > P['k_arg_demais'] else 'demais'
    maior_taxa = 'públicos' if P['alcance_pooled_publico'] > P['alcance_pooled_demais'] else 'demais'
    L = []
    L += ['# H23 — Presença argumentativa dos participantes e tamanho dos macrogrupos', '',
          '> **Hipótese exploratória**, formulada após H1–H22 por solicitação do pesquisador; não é pré-registro confirmatório. Protocolo: `config/H23_participacao.json` (salvo antes dos testes).', '',
          '## Resumo executivo', '',
          f'- **Pergunta:** a presença argumentativa dos participantes é proporcional ao tamanho dos macrogrupos (públicos × demais) em cada audiência?',
          f'- **Denominador:** {len(p)} participações (pessoa×audiência) em {p.audiencia.nunique()} AP, todas classificadas ({int((p.macrogrupo == PUB).sum())} públicos, {int((p.macrogrupo == DEM).sum())} demais), {p.nome_norm.nunique()} nomes distintos. Nenhuma lacuna de classificação.',
          f'- **Alcance (primário):** entre as {A["n_AP"]} AP elegíveis, diferença média (demais − públicos) = **{f(A["media"])} p.p.** ({ci(A, " p.p.")}); {A["n_pos"]} AP com taxa maior nos demais, {A["n_neg"]} nos públicos, {A["n_zero"]} empates; p bruto {f(A["p_bruto"], 4)}, p ajustado {f(A["p_ajust"], 4)}. {veredito(A, "pp")}.',
          f'- **Intensidade (secundário):** diferença média = **{f(B_["media"], 3)} menções Argumento por participante** ({ci(B_)}); p bruto {f(B_["p_bruto"], 4)}, p ajustado {f(B_["p_ajust"], 4)}. {veredito(B_, "int")}.',
          f'- **Pooled (descritivo, ponderado por participante, 31 AP):** {P["k_arg_publico"]}/{P["n_publico"]} públicos ({f(P["alcance_pooled_publico"] * 100, 1)}%) e {P["k_arg_demais"]}/{P["n_demais"]} demais ({f(P["alcance_pooled_demais"] * 100, 1)}%) têm ≥1 Argumento nominal. Maior contagem absoluta: {maior_cont}; maior taxa: {maior_taxa}.',
          '- Associação nominal a menção argumentativa; não é adesão, convencimento, eficácia nem favorecimento, e não há efeito causal. Resultado restrito ao cadastro documentado.', '',
          '## 1. Dados e denominador', '',
          f'Coorte = todos os participantes documentados (XLSX final de classificação, recalculado: {val["n_xlsx"]} linhas; {val["n_aps"]} AP; todas as AP têm documento em `resumo_execucao.csv`). Macrogrupo derivado: *público* = "Atores públicos"; *demais* = Acadêmicos, Atores privados, Sociedade civil, Partido Político, Outros. A categoria original foi preservada (`categoria_original`). O indicador "Menção incorporada" Sim/Não é só metadado, não filtro: participantes sem menção e a AP44 ({int((p.audiencia == 44).sum())} participantes, zero menções recuperadas) permanecem. **Ausência de menção recuperada é zero observado**, não prova de que a pessoa nunca tenha sido citada. As {len(p)} participações (pessoa×audiência) vs {p.nome_norm.nunique()} nomes distintos: a repetição de nome entre AP é papel de participação distinto e não foi fundida.', '',
          f'Elegibilidade do contraste pareado: ≥1 participante em cada macrogrupo na AP. Elegíveis: **{int(ap.elegivel.sum())} de {len(ap)}**. Excluídas: ' + ('; '.join(f'AP{int(r.audiencia):02d} ({r.motivo_inelegivel}; n público={int(r.n_publico)}, demais={int(r.n_demais)})' for r in inel.itertuples()) or 'nenhuma') + '. Grupo ausente é taxa indefinida, não zero. AP elegíveis sem nenhum Argumento nos dois grupos entram com diferença 0 (' + str(int(((ap.elegivel) & (ap.k_arg_total == 0)).sum())) + ' AP).', '',
          '## 2. Medidas', '',
          '- **Alcance (A, primária):** participante com ≥1 vínculo nominal (nível A) a menção classificada Argumento; binário, conta uma vez por AP. Denominador: todos os participantes do macrogrupo, inclusive os com 0 menções. Trechos multiautores podem ligar várias pessoas à mesma menção: é associação nominal, não autoria inequívoca.',
          '- **Intensidade (B, secundária):** menções Argumento associadas ao macrogrupo ÷ participantes documentados do grupo, por AP. Cada menção conta uma vez por macrogrupo (se cita 5 pessoas do mesmo grupo, vale 1; se cita os dois grupos, entra nos dois: não é partição). Pode superar 1; é contagem por participante, não probabilidade. Mede frequência de referências, complementando a diversidade de pessoas.',
          '- **Referência de proporcionalidade:** sem tempo de fala, a referência é igualdade por participante (não direito a nº de citações). Esperado por AP = pessoas com Argumento na AP × fração de participantes do grupo na AP.', '',
          '## 3. Estatística', '',
          f'Unidade independente = AP. Estimando principal: média, com pesos iguais por AP, da diferença (demais − públicos). Teste de inversão de sinais das diferenças por AP ({A["metodo_p"]}); simetria das diferenças sob H0 é hipótese adicional explícita. IC95% por bootstrap de AP inteiras (9999, seed {proto["seeds"]["seed_global"]}), reportado se ≥10 AP. Não se permutam participantes nem menções; sem Fisher/qui-quadrado. Família H23 = {{alcance, intensidade}} com Benjamini–Hochberg (α=0,05); sensibilidades ficam fora da família.', '',
          '| Teste | n AP | Diferença média | IC95% | p bruto | p ajustado (BH) | + / − / 0 |', '|---|---|---|---|---|---|---|',
          f'| A alcance (p.p.) | {A["n_AP"]} | {f(A["media"])} | [{f(A["ic95_lo"])}; {f(A["ic95_hi"])}] | {f(A["p_bruto"], 4)} | {f(A["p_ajust"], 4)} | {A["n_pos"]}/{A["n_neg"]}/{A["n_zero"]} |',
          f'| B intensidade (menções/participante) | {B_["n_AP"]} | {f(B_["media"], 3)} | [{f(B_["ic95_lo"], 3)}; {f(B_["ic95_hi"], 3)}] | {f(B_["p_bruto"], 4)} | {f(B_["p_ajust"], 4)} | {B_["n_pos"]}/{B_["n_neg"]}/{B_["n_zero"]} |', '',
          '![Figura 1](figuras/fig1_alcance_por_AP.png)', '',
          f'*Figura 1. Variáveis: % de participantes com ≥1 Argumento nominal, por macrogrupo, em cada AP elegível (n AP={A["n_AP"]}; denominadores entre parênteses: públicos|demais). Linha cinza = diferença.*', '',
          '## 4. Observado × esperado (descritivo, sem teste adicional)', '',
          '| Escopo | Roster público | Arg. público esperado (estratificado por AP) | Arg. público observado | Observado − esperado (pessoas) |', '|---|---|---|---|---|',
          f'| Todas as 31 AP (pooled para roster e observado; esperado estratificado) | {f(P["share_roster_publico_pooled"] * 100, 1)}% ({P["n_publico"]}/{P["n_publico"] + P["n_demais"]}) | {f(P["share_arg_publico_esperado_estratificado"] * 100, 1)}% ({f(P["esperado_estratificado_publico"], 1)}/{P["K_pessoas_com_arg"]}) | {f(P["share_arg_publico_pooled"] * 100, 1)}% ({P["k_arg_publico"]}/{P["K_pessoas_com_arg"]}) | {f(P["k_arg_publico"] - P["esperado_estratificado_publico"], 1)} |',
          f'| {PE["n_AP"]} AP elegíveis | {f(PE["share_roster_publico_pooled"] * 100, 1)}% ({PE["n_publico"]}/{PE["n_publico"] + PE["n_demais"]}) | {f(PE["share_arg_publico_esperado_estratificado"] * 100, 1)}% ({f(PE["esperado_estratificado_publico"], 1)}/{PE["K_pessoas_com_arg"]}) | {f(PE["share_arg_publico_pooled"] * 100, 1)}% ({PE["k_arg_publico"]}/{PE["K_pessoas_com_arg"]}) | {f(PE["k_arg_publico"] - PE["esperado_estratificado_publico"], 1)} |', '',
          'O roster "pooled" soma todas as participações sem considerar AP; o "esperado estratificado" respeita a composição de cada AP e é a referência primária de proporcionalidade. Compartilha a pergunta do teste de alcance e não é um teste independente.', '',
          '![Figura 2](figuras/fig2_composicao_obs_esp.png)', '',
          f'*Figura 2. Parcela de atores públicos no roster (405 participantes), esperada entre as {P["K_pessoas_com_arg"]} pessoas com Argumento (estratificada por AP) e observada (pooled). Denominador: 31 AP.*', '',
          '## 5. Intensidade', '', '![Figura 3](figuras/fig3_intensidade_por_AP.png)', '',
          f'*Figura 3. Diferença (demais − públicos) em menções Argumento por participante do grupo, por AP elegível (n={B_["n_AP"]}). Cada menção conta uma vez por macrogrupo.* Pooled (descritivo): públicos {P["mencoes_A_publico"]}/{P["n_publico"]} = {f(P["intens_pooled_A_publico"], 3)}; demais {P["mencoes_A_demais"]}/{P["n_demais"]} = {f(P["intens_pooled_A_demais"], 3)} (as menções multigrupo entram nos dois, portanto os numeradores não somam as menções distintas).', '',
          '## 6. Sensibilidades (exploratórias, fora da família, p sem ajuste)', '',
          '| Análise | n AP | Diferença média | IC95% | p bruto | observação |', '|---|---|---|---|---|---|']
    for k, v in res.items():
        if k.startswith('S') or k == 'B_wilcoxon':
            esc = 'p.p.' if 'alcance' in k else 'menções/part.'
            L.append(f'| {k} ({esc}) | {v["n_AP"]} | {f(v["media"], 3)} | ' + (f'[{f(v["ic95_lo"], 3)}; {f(v["ic95_hi"], 3)}]' if np.isfinite(v.get('ic95_lo', np.nan)) else '—') + f' | {f(v["p_bruto"], 4)} | {v.get("nota", "")} |')
    L += ['', f'Leave-one-AP-out, alcance: média entre {f(lo_a.media.min())} e {f(lo_a.media.max())} p.p.; p bruto entre {f(lo_a.p_bruto.min(), 3)} e {f(lo_a.p_bruto.max(), 3)}; {int((lo_a.p_bruto < .05).sum())}/{len(lo_a)} remoções com p<0,05. Intensidade: média entre {f(lo_b.media.min(), 3)} e {f(lo_b.media.max(), 3)}; p entre {f(lo_b.p_bruto.min(), 3)} e {f(lo_b.p_bruto.max(), 3)}; {int((lo_b.p_bruto < .05).sum())}/{len(lo_b)} com p<0,05. (Descritivo; não se escolhe a de menor p.)', '',
          '![Figura 4](figuras/fig4_sensibilidades.png)', '',
          '*Figura 4. Diferença média por AP (demais − públicos) em cada análise; barras = IC95% bootstrap quando reportado. Escalas de alcance (p.p.) e intensidade (menções/participante) diferem; comparar apenas sinal e ordem de grandeza dentro de cada desfecho.*', '',
          '## 7. Maior contagem × maior taxa', '',
          f'Entre os {P["K_pessoas_com_arg"]} participantes com Argumento nominal, {P["k_arg_publico"]} são públicos e {P["k_arg_demais"]} demais (maior contagem: {maior_cont}). Porém o roster tem {P["n_publico"]} públicos e {P["n_demais"]} demais; a taxa é {f(P["alcance_pooled_publico"] * 100, 1)}% nos públicos e {f(P["alcance_pooled_demais"] * 100, 1)}% nos demais (maior taxa: {maior_taxa}). Contagem mede volume de nomes; taxa corrige pelo tamanho do grupo; o contraste por AP corrige também pela composição de cada audiência. Pooled (' + f(P['dif_pooled_alcance_pp'], 1) + ' p.p. demais − públicos) e média por AP (' + f(A['media'], 1) + ' p.p.) são estimandos diferentes e podem divergir: AP com muitos participantes de um só grupo e zero Argumento pesam no pooled, mas valem uma AP cada na média por AP.', '',
          '## 8. Ressalvas e comentário sobre o problema central', '',
          '- Resultados restritos ao cadastro documentado (31 AP, 405 participações); completude para todas as audiências do STF não é premissa. Regras de exclusão (partes processuais, citações bibliográficas, contexto da extração) permanecem e podem afetar os padrões; a codificação não foi reaberta.',
          f'- A sensibilidade A+B (S5) acrescenta menções a instituições ao macrogrupo; sua estimativa ({f(res["S5_intens_AB"]["media"], 3)}) {"mantém" if np.sign(res["S5_intens_AB"]["media"]) == np.sign(B_["media"]) else "INVERTE"} o sinal da intensidade principal, de modo que a conclusão sobre intensidade depende do tipo de vínculo considerado.',
          '- Vínculo nominal A apenas; vínculo institucional B só na sensibilidade de intensidade e só em macrogrupo, sem atribuir menção a todos os afiliados.',
          '- Trechos multiautores associam várias pessoas à mesma menção (sensibilidade S4 usa só menções unipessoa).',
          '- Sem tempo de fala; "proporcionalidade" = referência igual por participante. Sem causalidade, favorecimento ou adesão: "presença" = mobilização argumentativa.',
          '- Número pequeno de AP: inferência por AP com poucos blocos; testes têm pouca potência. Não significância ≠ equivalência.',
          '- Hipótese exploratória pós-H1–22; o p ajustado cobre apenas os 2 testes H23.',
          '- **Problema central:** o resultado informa se, no cadastro, atores públicos (operacionalmente o contraste do problema de pesquisa) e os demais aparecem em menções argumentativas em proporção a seu peso numérico nas audiências; não responde sobre influência, acolhimento ou eficácia.', '',
          '## 9. Reprodução (sem API)', '', '```', '.venv/bin/python testar_H23.py', '.venv/bin/python -m pytest tests/test_H23.py -q', '```', '',
          'Saídas: `data/H23/participantes.csv`, `results/H23/*` (inclui `manifesto_H23.json` com hashes antes/depois, versões e seeds). Nenhum resultado H1–H22, classificação ou relatório existente foi alterado (hashes verificados).']
    return '\n'.join(L)


def md_para_html(md: str, figs: dict) -> str:
    import html, re
    out, tab, code = [], [], False
    def inline(s):
        s = html.escape(s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s); s = re.sub(r'\*(.+?)\*', r'<i>\1</i>', s)
        return re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    def flush():
        if tab:
            rows = [r for r in tab if not set(r.replace('|', '').strip()) <= set('-')]
            h = '<table>' + ''.join(('<tr>' + ''.join(f'<{"th" if i == 0 else "td"}>{inline(c.strip())}</{"th" if i == 0 else "td"}>' for c in r.strip('|').split('|')) + '</tr>') for i, r in enumerate(rows)) + '</table>'
            out.append(h); tab.clear()
    lst = False
    for ln in md.split('\n'):
        if ln.startswith('```'):
            flush(); code = not code; out.append('<pre>' if code else '</pre>'); continue
        if code: out.append(html.escape(ln)); continue
        if ln.startswith('|'): tab.append(ln); continue
        flush()
        if lst and not ln.startswith('- '): out.append('</ul>'); lst = False
        mm = re.match(r'!\[(.*?)\]\(figuras/(.+?)\)', ln)
        if mm: out.append(f'<img src="data:image/png;base64,{figs[mm.group(2)][1]}" alt="{mm.group(1)}">')
        elif ln.startswith('# '): out.append(f'<h1>{inline(ln[2:])}</h1>')
        elif ln.startswith('## '): out.append(f'<h2>{inline(ln[3:])}</h2>')
        elif ln.startswith('> '): out.append(f'<blockquote>{inline(ln[2:])}</blockquote>')
        elif ln.startswith('- '):
            if not lst: out.append('<ul>'); lst = True
            out.append(f'<li>{inline(ln[2:])}</li>')
        elif ln.strip(): out.append(f'<p>{inline(ln)}</p>')
    flush()
    css = 'body{font-family:Georgia,serif;max-width:900px;margin:2em auto;line-height:1.5;padding:0 1em}table{border-collapse:collapse;font-size:.85em;margin:1em 0}td,th{border:1px solid #bbb;padding:3px 7px}img{max-width:100%}blockquote{background:#fff4d6;padding:.5em 1em;margin:1em 0}pre{background:#eee;padding:.5em}'
    return f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>H23</title><style>{css}</style></head><body>{"".join(out)}</body></html>'


# ------------------------------------------------------------------ principal
def executar() -> dict:
    proto = json.loads(PROTO.read_text(encoding='utf-8'))
    cfg = json.loads((AQUI / 'config/analise_H1_H22.json').read_text(encoding='utf-8'))
    seed, B, min_ci = proto['seeds']['seed_global'], proto['seeds']['B_signflip_MC'], 10
    antes = hashes_protegidos()
    d = I.carregar(cfg)
    m, a, ponte, ab = d['mencoes'], d['atores'], d['ponte'], d['mencoes_AB']
    # conferência com os CSV já gerados (valores e IDs)
    proc = AQUI / 'data/processed'
    conf = {}
    for nome, df, chave in [('atores_classificados', a, 'ator_id'), ('mencoes_principal_atores', m, 'id'), ('mencoes_sensibilidade_AB', ab, 'id')]:
        c = pd.read_csv(proc / f'{nome}.csv', encoding='utf-8-sig')
        conf[nome] = bool(len(c) == len(df) and set(c[chave]) == set(df[chave]))
    conf['ponte_pares'] = bool(len(pd.read_csv(proc / 'ponte_mencao_ator.csv', encoding='utf-8-sig')) == len(ponte) == 380)
    assert all(conf.values()), conf
    esp = proto['coorte']['esperado']
    assert len(a) == esp['participacoes'] and a['audiencia'].nunique() == esp['audiencias'], 'coorte divergente'
    p = construir_participantes(a, ponte, m, proto)
    assert len(p) == 405 and not p.duplicated(['audiencia', 'ator_id']).any() and not p.duplicated(['audiencia', 'nome_norm']).any()
    assert (p.macrogrupo == PUB).sum() == esp['publico'] and (p.macrogrupo == DEM).sum() == esp['demais'] and p.nome_norm.nunique() == esp['nomes_distintos']
    mg = mencao_grupo(m, ponte, ab, proto)
    # coerência: flags A recomputados vs flags da tabela principal de menções
    mm = m.set_index('id').loc[mg['id']]
    assert (mg['A_pub'].to_numpy() == mm['cat_atores_publicos'].to_numpy()).all()
    assert (mg['AB_pub'] | ~mg['A_pub']).all() and (mg['AB_dem'] | ~mg['A_dem']).all()   # A+B ⊇ A
    ap = tabela_ap(p, mg)
    e = ap[ap['elegivel']]
    R_OUT.mkdir(parents=True, exist_ok=True); D_OUT.mkdir(parents=True, exist_ok=True); REP.mkdir(parents=True, exist_ok=True); (REP / 'figuras').mkdir(exist_ok=True)
    res = {}
    res['A_alcance'] = contraste(e['dif_alcance'], 'H23_A', seed, B, min_ci)
    res['B_intensidade'] = contraste(e['dif_intens_A'], 'H23_B', seed, B, min_ci)
    adj = E.bh(pd.DataFrame({'Familia': ['H23_principais'] * 2, 'teste': ['A', 'B'], 'valor_p': [res['A_alcance']['p_bruto'], res['B_intensidade']['p_bruto']]}))
    res['A_alcance']['p_ajust'], res['B_intensidade']['p_ajust'] = [float(x) for x in adj['valor_p_BH']]
    g3 = ap[ap['elegivel_ge3']]
    res['S1_alcance_ge3'] = contraste(g3['dif_alcance'] if len(g3) else [], 'H23_sens_S1a', seed, B, min_ci) | {'nota': 'AP com ≥3 por grupo'}
    res['S1_intens_ge3'] = contraste(g3['dif_intens_A'] if len(g3) else [], 'H23_sens_S1b', seed, B, min_ci) | {'nota': 'AP com ≥3 por grupo'}
    res['S4_alcance_unipessoa'] = contraste(e['dif_alcance_uni'], 'H23_sens_S4', seed, B, min_ci) | {'nota': 'só menções unipessoa (todo participante com Argumento tem ≥1 Argumento unipessoa: estimativa idêntica)'}
    res['S5_intens_AB'] = contraste(e['dif_intens_AB'], 'H23_sens_S5', seed, B, min_ci) | {'nota': 'A+B em macrogrupo, sem atribuição individual; inclui referências a instituições'}
    res['S6_intens_docs'] = contraste(e['dif_intens_docs'], 'H23_sens_S6', seed, B, min_ci) | {'nota': 'documentos distintos'}
    pw = wilcoxon(e['dif_intens_A'])['p_wilcoxon']
    res['B_wilcoxon'] = {'n_AP': res['B_intensidade']['n_AP'], 'media': res['B_intensidade']['mediana'], 'p_bruto': pw, 'p_wilcoxon': pw, 'nota': 'S7: coluna "diferença" = MEDIANA; p = Wilcoxon signed-rank (zeros descartados)'}
    res['S8_AP44'] = {'elegivel': bool(ap.loc[ap.audiencia == 44, 'elegivel'].iloc[0]), 'n_participantes': int(ap.loc[ap.audiencia == 44, 'n_participantes'].iloc[0]),
                      'mencoes_nominais': int(p.loc[p.audiencia == 44, 'n_mencoes_nominais'].sum())}
    res['S8_AP44'] |= {'n_AP': 0, 'media': np.nan, 'p_bruto': np.nan}
    loo_df = pd.concat([loo(ap, 'dif_alcance', seed, B, min_ci), loo(ap, 'dif_intens_A', seed, B, min_ci)])
    pl = {'all': pooled(ap, p, False), 'eleg': pooled(ap, p, True)}
    res_vis = {k: v for k, v in res.items() if k != 'S8_AP44'}
    val = {'n_xlsx': len(a), 'n_aps': int(a.audiencia.nunique())}
    figs = figuras(ap, pl, res_vis, loo_df)
    md = texto_relatorio(proto, p, ap, res_vis, pl, loo_df, val, None)
    for nome, (_, b) in figs.items():
        (REP / 'figuras' / nome).write_bytes(base64.b64decode(b))
    (REP / 'relatorio_H23.md').write_text(md, encoding='utf-8')
    (REP / 'relatorio_H23.html').write_text(md_para_html(md, figs), encoding='utf-8')
    p.to_csv(D_OUT / 'participantes.csv', index=False, encoding='utf-8-sig')
    ap.to_csv(R_OUT / 'por_AP.csv', index=False, encoding='utf-8-sig')
    mg.to_csv(R_OUT / 'mencoes_argumento_macrogrupo.csv', index=False, encoding='utf-8-sig')
    loo_df.to_csv(R_OUT / 'leave_one_AP_out.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame([pl['all'], pl['eleg']]).to_csv(R_OUT / 'global_pooled.csv', index=False, encoding='utf-8-sig')
    inf = pd.DataFrame([{'analise': k} | {kk: vv for kk, vv in v.items()} for k, v in res.items()])
    inf.to_csv(R_OUT / 'inferencia.csv', index=False, encoding='utf-8-sig')
    (R_OUT / 'inferencia.json').write_text(json.dumps(res | {'pooled': pl}, ensure_ascii=False, indent=2, default=lambda o: None if isinstance(o, float) and np.isnan(o) else (o.item() if hasattr(o, 'item') else str(o))), encoding='utf-8')
    depois = hashes_protegidos()
    assert antes == depois, 'fonte/resultado existente foi alterado!'
    man = {'protocolo': {'arquivo': str(PROTO.relative_to(AQUI)), 'sha256': sha_arq(PROTO)}, 'script': {'arquivo': 'testar_H23.py', 'sha256': sha_arq(Path(__file__))},
           'comando': '.venv/bin/python testar_H23.py', 'seed': seed, 'B': B, 'hashes_antes': antes, 'hashes_depois': depois, 'inalterados': antes == depois,
           'conferencia_csv_processed': conf, 'versoes': {'python': platform.python_version(), 'pandas': pd.__version__, 'numpy': np.__version__},
           'saidas': {str(x.relative_to(AQUI)): sha_arq(x) for x in sorted([*D_OUT.glob('*'), *R_OUT.glob('*'), *REP.rglob('*')]) if x.is_file() and x.name != 'manifesto_H23.json'}}
    (R_OUT / 'manifesto_H23.json').write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'res': res, 'pl': pl, 'ap': ap, 'p': p}


if __name__ == '__main__':
    r = executar()
    for k, v in r['res'].items():
        print(k, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk in ('n_AP', 'media', 'ic95_lo', 'ic95_hi', 'p_bruto', 'p_ajust', 'n_pos', 'n_neg', 'n_zero', 'elegivel', 'mencoes_nominais')})
