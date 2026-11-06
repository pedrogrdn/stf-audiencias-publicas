"""Figuras (PNG 300 dpi + SVG com texto editável). Cada figura declara unidade e denominador e grava os dados em results/figures/dados/.
Nenhuma figura codifica significância; estimativas e intervalos são mostrados como tal."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from hipoteses import EIXO_A, EIXO_CURTO, LOCAIS

COR = {'Ambiental/políticas/mercado': '#1b6ca8', 'Personalidade': '#d1495b'}
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 100, 'svg.fonttype': 'none'})


class Reg:
    def __init__(self, pasta: Path):
        self.pasta, self.itens = pasta, []
        (pasta / 'dados').mkdir(parents=True, exist_ok=True)

    def salvar(self, fig, nome, hip, unidade, denom, dados: pd.DataFrame, legenda=''):
        for ext in ('png', 'svg'):
            fig.savefig(self.pasta / f'{nome}.{ext}', dpi=300 if ext == 'png' else None, bbox_inches='tight', metadata={'Date': None} if ext == 'svg' else None)
        plt.close(fig)
        dados.to_csv(self.pasta / 'dados' / f'{nome}.csv', index=False, encoding='utf-8-sig')
        self.itens.append({'arquivo_png': f'{nome}.png', 'arquivo_svg': f'{nome}.svg', 'hipoteses': hip, 'unidade': unidade, 'denominador': denom, 'dados': f'dados/{nome}.csv', 'legenda': legenda})


def _t(ax, titulo, sub):
    ax.set_title(f'{titulo}\n{sub}', fontsize=8, loc='left')


def gerar(ctx, mat: pd.DataFrame, pasta: Path, ctx_ab=None) -> list[dict]:
    m, T, cats = ctx.m, ctx.tabs, ctx.cats
    R = Reg(pasta)
    t = T['audiencias_base'].copy()
    t['ec'] = t['eixo'].map(EIXO_CURTO)
    nA = len(t)
    # 1 tempo
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for e, g in t.groupby('ec'):
        ax.scatter(g.ano_julgamento, g.taxa, s=15 + 2 * g.n, alpha=.6, color=COR[e], label=f'{e} ({len(g)} audiências)')
    ap = T['H1_por_ano_julgamento']
    ax.plot(ap.ano_julgamento, ap.taxa_agregada, 'k--', lw=1, label='taxa agregada por ano (todas as menções)')
    ax.set(xlabel='Ano do julgamento', ylabel='Taxa argumentativa (Argumentos / menções)')
    _t(ax, 'H1/H13 — taxa argumentativa por audiência e ano do julgamento', f'Unidade: audiência (N={nA}); área ∝ nº de menções; denominador da taxa: menções da audiência')
    ax.legend(frameon=False, fontsize=7)
    R.salvar(fig, 'fig01_taxa_por_ano_julgamento', 'H1, H13', 'audiência', f'{nA} audiências; {len(m)} menções', t[['audiencia', 'eixo', 'ano_julgamento', 'n', 'k', 'taxa']])
    # 2 intervalo
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for e, g in t.groupby('ec'):
        ok = g[g.intervalo >= 0]
        ax.scatter(ok.intervalo, ok.taxa, s=15 + 2 * ok.n, alpha=.6, color=COR[e], label=e)
    neg = t[t.intervalo < 0]
    ax.scatter(neg.intervalo, neg.taxa, s=60, facecolors='none', edgecolors='k', label=f'AP33: intervalo cadastrado −1 (dado original; fora de H2/H16)')
    ax.set(xlabel='Intervalo em anos (ano julgamento − ano audiência)', ylabel='Taxa argumentativa')
    _t(ax, 'H2/H16 — intervalo e taxa por audiência', f'Unidade: audiência (N={nA - len(neg)} no estimando; {len(neg)} excluída por cadastro −1)')
    ax.legend(frameon=False, fontsize=7)
    R.salvar(fig, 'fig02_intervalo_taxa', 'H2, H16', 'audiência', f'{nA - len(neg)} audiências no estimando', t[['audiencia', 'eixo', 'intervalo', 'n', 'k', 'taxa']])
    # 3 eixos + H6
    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    rng = np.random.default_rng(1)
    for i, (e, g) in enumerate(t.groupby('ec')):
        ax.scatter(i + rng.uniform(-.12, .12, len(g)), g.taxa, s=15 + 2 * g.n, alpha=.6, color=COR[e])
        ax.hlines(g.taxa.mean(), i - .25, i + .25, color='k')
        for r in g.sort_values('taxa').iloc[[0, -1]].itertuples():
            ax.text(i + .15, r.taxa, f'AP{r.audiencia} (n={r.n})', fontsize=6)
    ax.set(xticks=[0, 1], xticklabels=sorted(COR), ylabel='Taxa argumentativa por audiência')
    _t(ax, 'H5/H6 — taxa por audiência dentro de cada eixo (traço = média das audiências)', f'Unidade: audiência (N={nA}); extremos rotulados com n de menções')
    R.salvar(fig, 'fig03_eixos_e_heterogeneidade', 'H5, H6', 'audiência', f'{nA} audiências', t[['audiencia', 'eixo', 'n', 'k', 'taxa']])
    # 4 forest
    base = mat[(mat.Analise == 'Principal (A)') & mat.estimativa_num.notna() & ~mat.Situacao.str.startswith('Inviável') & mat.Hipotese.isin(['H4', 'H8', 'H11', 'H12', 'H15', 'H17', 'H20'])].copy()
    base = base[~base.Teste.str.contains('Prevalência') | True]
    if len(base):
        fig, ax = plt.subplots(figsize=(8.4, 0.26 * len(base) + 1.8))
        y = np.arange(len(base))[::-1]
        ax.axvline(0, color='gray', lw=.8)
        for yi, r in zip(y, base.itertuples()):
            if np.isfinite(r.ic_inf):
                ax.hlines(yi, r.ic_inf, r.ic_sup, color='#444')
            ax.plot(r.estimativa_num, yi, 'o', color='#1b6ca8')
        ax.set_yticks(y)
        ax.set_yticklabels([f'{r.Hipotese} {r.Teste[:62]} [N: {str(r.N).split(";")[0]}]' for r in base.itertuples()], fontsize=6)
        ax.set_xlabel('Estimativa (média por audiência) e IC95% por reamostragem (bootstrap) de audiências (ver regra de emissão abaixo)')
        _t(ax, 'Contrastes e diferenças por audiência (exploratórios; H4 confundido com local)', 'Unidade: audiência; sem marcação de significância; sem IC: comparação entre eixos com <10 AP em algum eixo, ou contraste interno com <10 AP no total (N dos grupos na matriz)')
        R.salvar(fig, 'fig04_contrastes', 'H4, H8, H11, H12, H15, H17, H20', 'audiência', 'ver N na matriz (coluna N)', base[['Hipotese', 'Teste', 'N', 'estimativa_num', 'ic_inf', 'ic_sup']])
    # 5 Lorenz + Gini
    fig, axs = plt.subplots(1, 2, figsize=(9, 4.2))
    g = m.groupby('audiencia')['arg'].agg(['size', 'sum'])
    for col, lab, c in (('size', 'menções', '#888'), ('sum', 'argumentos', '#1b6ca8')):
        v = np.sort(g[col].to_numpy(float))
        axs[0].plot(np.r_[0, np.arange(1, len(v) + 1) / len(v)], np.r_[0, np.cumsum(v) / v.sum()], color=c, label=lab)
    axs[0].plot([0, 1], [0, 1], 'k:', lw=.7)
    axs[0].set(xlabel='Fração acumulada de audiências', ylabel='Fração acumulada')
    axs[0].legend(frameon=False)
    h10 = T['H10_concentracao']
    x = np.arange(len(h10))
    axs[1].bar(x - .2, h10.gini_mencoes, .4, label='Gini menções', color='#888')
    axs[1].bar(x + .2, h10.gini_argumentos, .4, label='Gini argumentos', color='#1b6ca8')
    for xi, r in zip(x, h10.itertuples()):
        axs[1].text(xi, max(r.gini_mencoes, r.gini_argumentos) + .01, f'{r.n_unidades} unid.', ha='center', fontsize=6)
    axs[1].set_xticks(x); axs[1].set_xticklabels(h10.unidade, fontsize=7)
    axs[1].legend(frameon=False, fontsize=7)
    fig.suptitle(f'H10 — concentração (descritiva): Lorenz por audiência e Gini por unidade\nUnidades: audiência, documento, ministro (autoria plena); denominadores = menções e argumentos', fontsize=8, x=0.01, y=1.06, ha='left')
    R.salvar(fig, 'fig05_h10_concentracao', 'H10', 'audiência, documento, ministro', f'{len(m)} menções; {int(m.arg.sum())} argumentos', h10)
    # 6 H3 taxas por ministro
    h3 = T['H3_ministros_com_suporte'].sort_values('taxa')
    if len(h3):
        fig, ax = plt.subplots(figsize=(6.5, 0.32 * len(h3) + 1.6))
        ax.barh(h3.ministro, h3.taxa, color='#1b6ca8')
        for i, r in enumerate(h3.itertuples()):
            ax.text(r.taxa + .01, i, f'{r.n_argumentos}/{r.n_mencoes}', va='center', fontsize=6)
        ax.set(xlabel='Taxa argumentativa observada (Argumentos / menções do ministro)')
        _t(ax, 'H3 — taxa observada por ministro com suporte (descritiva; sem teste)', f'Unidade: ministro (N={len(h3)}); rótulo = nArgumento/nMenções; menções atribuídas por metadado ≠ autoria pessoal')
        R.salvar(fig, 'fig06_h3_taxa_por_ministro', 'H3', 'ministro', f'{len(h3)} ministros; {int(h3.n_mencoes.sum())} menções', h3)
    # 7 H8 local: composição tripla + taxa por audiência
    lt = T['H8_local_x_tipo'].set_index('local').loc[LOCAIS]
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    bot = np.zeros(3)
    for c_, col in (('Contexto', '#bbb'), ('Relato', '#e0a030'), ('Argumento', '#1b6ca8')):
        v = (lt[c_] / lt['n']).to_numpy()
        axs[0].bar(LOCAIS, v, bottom=bot, label=c_, color=col)
        bot += v
    for i, loc in enumerate(LOCAIS):
        axs[0].text(i, 1.01, f'n={lt.loc[loc, "n"]}', ha='center', fontsize=7)
    axs[0].legend(frameon=False, fontsize=7); axs[0].set_ylabel('Proporção das menções do local (agregado por menção)')
    dd = []
    for i, loc in enumerate(LOCAIS):
        gg = m[m.local == loc].groupby('audiencia')['arg'].agg(['size', 'mean'])
        gg = gg[gg['size'] >= 3]
        axs[1].scatter(i + np.random.default_rng(i).uniform(-.12, .12, len(gg)), gg['mean'], s=10 + 2 * gg['size'], alpha=.55)
        axs[1].hlines(gg['mean'].mean(), i - .25, i + .25, color='k')
        dd.append(gg.reset_index().assign(local=loc))
    axs[1].set(xticks=[0, 1, 2], xticklabels=LOCAIS, ylabel='Taxa argumentativa por audiência (≥3 menções no local)')
    fig.suptitle('H8 — distribuição Contexto/Relato/Argumento por local (esq., agregado por menção) e taxa por audiência (dir.)\nUnidades: menção (esq., descritivo) e audiência (dir.)', fontsize=8, x=0.01, y=1.06, ha='left')
    R.salvar(fig, 'fig07_h8_local', 'H8', 'menção (descrição) e audiência', f'{len(m)} menções; audiências com ≥3 menções por local no painel direito', pd.concat(dd).rename(columns={'size': 'n', 'mean': 'taxa'}))
    # 8 H15 composição local × eixo
    comp = T['H15_composicao_local_por_audiencia'].copy()
    comp['ec'] = comp['eixo'].map(EIXO_CURTO)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for j, loc in enumerate(LOCAIS):
        for i, (e, g) in enumerate(comp.groupby('ec')):
            xx = j + (i - .5) * .35
            ax.scatter(xx + np.random.default_rng(j * 2 + i).uniform(-.05, .05, len(g)), g[loc], s=8 + 2 * g.n, alpha=.5, color=COR[e], label=e if j == 0 else None)
            ax.hlines(g[loc].mean(), xx - .12, xx + .12, color='k')
    ax.set(xticks=range(3), xticklabels=LOCAIS, ylabel='Fração das menções da audiência no local')
    _t(ax, 'H15 — composição por local × eixo (distribuição das localizações)', f'Unidade: audiência (N={len(comp)}, ≥3 menções); traço = média das audiências; área ∝ nº de menções')
    ax.legend(frameon=False, fontsize=7)
    R.salvar(fig, 'fig08_h15_local_por_eixo', 'H15', 'audiência', f'{len(comp)} audiências', comp)
    # 9 H17 alvo × local
    ax_ = T['H17_alvo_x_local'].set_index('tipo_alvo_derivado')[LOCAIS]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bot = np.zeros(3)
    pal = ['#1b6ca8', '#6aa84f', '#e0a030', '#bbb']
    for (idx, row), col in zip(ax_.iterrows(), pal):
        v = (row / ax_.sum()).to_numpy()
        ax.bar(LOCAIS, v, bottom=bot, label=idx, color=col)
        bot += v
    for i, loc in enumerate(LOCAIS):
        ax.text(i, 1.01, f'n={int(ax_[loc].sum())}', ha='center', fontsize=7)
    ax.legend(frameon=False, fontsize=7, loc='upper center', bbox_to_anchor=(.5, -.1), ncol=2)
    ax.set_ylabel('Proporção das menções do local (agregado por menção)')
    _t(ax, 'H17 — tipo de alvo derivado × local (descritivo; proxy por campos preenchidos)', f'Unidade: menção (descrição); denominador = menções por local (n no topo)')
    R.salvar(fig, 'fig09_h17_alvo_por_local', 'H17', 'menção (descrição)', f'{len(m)} menções', T['H17_alvo_x_local'])
    # 10 H18
    pc = T['H18_pca_clr']
    fig, ax = plt.subplots(figsize=(5.8, 4.6))
    ax.scatter(pc.PC1, pc.PC2, s=10 + 2 * pc.n, alpha=.6)
    for r in pc.itertuples():
        ax.text(r.PC1, r.PC2, str(int(r.audiencia)), fontsize=6)
    ax.set(xlabel='PC1 (log-razão centrada)', ylabel='PC2')
    _t(ax, 'H18 — composição Contexto/Relato/Argumento por audiência (exploratório)', f'Unidade: audiência (N={len(pc)}); rótulo = nº da audiência; área ∝ nº de menções')
    R.salvar(fig, 'fig10_h18_pca_composicao', 'H18', 'audiência', f'{len(pc)} audiências', pc)
    # 11 estados A vs A+B e categorias
    if ctx_ab is not None:
        ea = T['H20_estados_por_eixo'].set_index('eixo_curto')
        eb = ctx_ab.tabs['AB_H20_estados_por_eixo'].set_index('eixo_curto')
        est_all = sorted(set(ea.columns) | set(eb.columns) - {'n_total'})
        est_all = [c for c in ['classificado', 'identificado_sem_classificacao', 'identificado_irresolvido_categoria_contraditoria', 'generica_nao_aplicavel', 'sem_nome_alvo_nao_generico'] if c in ea.columns or c in eb.columns]
        fig, axs = plt.subplots(1, 2, figsize=(11, 4.3))
        tot = pd.DataFrame({'A (principal)': ea[[c for c in est_all if c in ea]].sum(), 'A+B (sensibilidade)': eb[[c for c in est_all if c in eb]].sum()}).reindex(est_all).fillna(0)
        (tot / tot.sum()).T.plot.bar(stacked=True, ax=axs[0], rot=0)
        for i, c_ in enumerate(tot.columns):
            axs[0].text(i, 1.01, f'N={int(tot[c_].sum())}', ha='center', fontsize=7)
        axs[0].set(ylabel='Proporção das menções incorporadas'); axs[0].legend(fontsize=6, frameon=False, loc='upper center', bbox_to_anchor=(.5, -.1), ncol=2)
        da = T['H19_descritivo_categorias'].set_index('rotulo_exibicao')['n_mencoes_com']
        db = ctx_ab.tabs['AB_H19_descritivo_categorias'].set_index('rotulo_exibicao')['n_mencoes_com']
        pd.DataFrame({'A (principal)': da, 'A+B (sensibilidade)': db}).plot.bar(ax=axs[1], rot=25)
        axs[1].set(ylabel='Menções com a categoria (sobreposto; entre classificadas)', xlabel='')
        fig.suptitle('Cobertura de vínculos: nível A (principal) × A+B (sensibilidade)\nUnidade: menção (contagem; 1 linha por menção); categorias sobrepostas não somam o total', fontsize=8, x=0.01, y=1.06, ha='left')
        R.salvar(fig, 'fig11_estados_A_vs_AB', 'H19–H22', 'menção (contagem)', f'{len(m)} menções incorporadas', tot.reset_index().rename(columns={'index': 'estado'}))
        # 12 H19 taxas com/sem A vs A+B
        fig, ax = plt.subplots(figsize=(8, 4.2))
        a_ = T['H19_descritivo_categorias']; b_ = ctx_ab.tabs['AB_H19_descritivo_categorias']
        ok = a_[(a_.n_mencoes_com > 0) | (b_.n_mencoes_com > 0)].index
        xx = np.arange(len(ok))
        for off, (df_, nm, col) in zip((-.3, -.1, .1, .3), ((a_, 'A com', '#1b6ca8'), (a_, 'A sem', '#a9c9e3'), (b_, 'A+B com', '#d1495b'), (b_, 'A+B sem', '#efb3bc'))):
            vv = df_.loc[ok, 'taxa_com' if nm.endswith('com') else 'taxa_sem']
            nn = df_.loc[ok, 'n_mencoes_com' if nm.endswith('com') else 'n_mencoes_sem']
            ax.bar(xx + off, vv.fillna(0), .2, label=nm, color=col)
            for xi, v, n in zip(xx + off, vv.fillna(0), nn):
                ax.text(xi, v + .01, f'{n}', ha='center', fontsize=5)
        ax.set_xticks(xx); ax.set_xticklabels(a_.loc[ok, 'rotulo_exibicao'], rotation=15)
        ax.set(ylabel='Taxa argumentativa (agregado por menção)'); ax.legend(frameon=False, fontsize=7, ncol=4)
        _t(ax, 'H19 — taxa argumentativa com/sem a categoria (descritivo agregado por menção; testes usam um valor por audiência)', 'Unidade: menção (descrição); rótulo = nº de menções no denominador; barras A (principal) e A+B (sensibilidade)')
        R.salvar(fig, 'fig12_h19_taxas_por_categoria', 'H19', 'menção (descrição)', f'{int(a_.denominador_vinculadas.iloc[0])} classificadas em A; {int(b_.denominador_vinculadas.iloc[0])} em A+B', pd.concat([a_.assign(nivel='A'), b_.assign(nivel='A+B')]))
    # 13 H20
    inc = T['H20_incidencia_por_eixo'].pivot(index='categoria', columns='eixo', values='incidencia')
    fig, ax = plt.subplots(figsize=(7, 4.2))
    inc.plot.bar(ax=ax, rot=25, color=[COR[c] for c in inc.columns])
    den = T['H20_incidencia_por_eixo'].groupby('eixo')['denominador_mencoes_classificadas'].first().to_dict()
    ax.set(ylabel='Proporção das menções classificadas do eixo', xlabel='')
    ax.legend([f'{c} (n={den[c]})' for c in inc.columns], frameon=False, fontsize=7)
    _t(ax, 'H20 — incidência de categorias entre menções classificadas, por eixo (nível A; sobreposta)', 'Unidade: menção (descrição agregada por menção); inferência em H20 usa a incidência por audiência')
    R.salvar(fig, 'fig13_h20_incidencia_por_eixo', 'H20', 'menção (descrição agregada por menção)', f'{sum(den.values())} menções classificadas', T['H20_incidencia_por_eixo'])
    # 14 H21 heatmap com nArg/n
    h = T['H21_ministro_x_categoria'].head(15)
    lg = T['H21_ministro_x_categoria_aproveitamento'].set_index(['ministro', 'categoria'])
    fig, ax = plt.subplots(figsize=(8, 0.38 * len(h) + 1.8))
    mat_ = h[list(cats)].to_numpy()
    ax.imshow(mat_, cmap='Blues')
    ax.set_xticks(range(len(cats))); ax.set_xticklabels([ctx.cfg['alias_exibicao'].get(k, k) for k in cats], rotation=30, ha='right')
    ax.set_yticks(range(len(h))); ax.set_yticklabels([f'{r.ministro}{"*" if r.autoria_plena == 0 else ""}' for r in h.itertuples()], fontsize=7)
    for i, r in enumerate(h.itertuples()):
        for j, k in enumerate(cats):
            ax.text(j, i, f'{int(lg.loc[(r.ministro, k), "n_argumento"])}/{int(lg.loc[(r.ministro, k), "n_mencoes_com_categoria"])}', ha='center', va='center', fontsize=6)
    ax.set_title('H21 — nArgumento/nMenções por ministro × categoria (nível A; cor = nº de menções)\nUnidade: célula ministro×categoria; descritivo; * autoria não plena; atribuição por metadado ≠ preferência individual', fontsize=8, loc='left')
    R.salvar(fig, 'fig14_h21_ministro_x_categoria', 'H21', 'ministro × categoria', f'{int(h.n_mencoes_classificadas.sum())} menções classificadas nos 15 ministros mais frequentes', T['H21_ministro_x_categoria_aproveitamento'])
    # 15 H22: duas dimensões
    s = T['H22_serie_categoria_ano']
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
    for k, c in cats.items():
        d = s[s.categoria == k]
        if d.n_com_categoria.sum() == 0:
            continue
        lab = ctx.cfg['alias_exibicao'].get(k, k)
        axs[0].plot(d.ano_julgamento, d.incidencia, 'o-', ms=3, label=lab)
        dd = d[d.n_com_categoria >= 5]
        axs[1].plot(dd.ano_julgamento, dd.taxa_argumento_com_categoria, 'o-', ms=3, label=lab)
    a = T['H22_por_ano']
    for r in a.itertuples():
        axs[0].text(r.ano_julgamento, 1.02, f'{r.n_classificadas}', ha='center', fontsize=6)
    axs[0].set(xlabel='Ano do julgamento', ylabel='Incidência entre classificadas (agregado por menção)', ylim=(0, 1.08), title='(a) composição (n classificadas no topo)', xticks=sorted(a.ano_julgamento.unique()))
    axs[1].set(xlabel='Ano do julgamento', ylabel='Taxa argumentativa entre menções com a categoria', ylim=(0, 1.02), title='(b) aproveitamento (anos com ≥5 menções na categoria)')
    for ax_i in axs:
        ax_i.tick_params(axis='x', rotation=90, labelsize=7)
    axs[0].legend(frameon=False, fontsize=7)
    fig.suptitle('H22 — composição de categorias e aproveitamento argumentativo por ano (nível A, descritivo agregado por menção)\nUnidade: menção classificada agregada por ano; os testes usam um valor por audiência', fontsize=8, x=0.01, y=1.06, ha='left')
    R.salvar(fig, 'fig15_h22_composicao_e_aproveitamento', 'H22', 'menção classificada por ano (descrição); audiência (teste)', f'{int(a.n_classificadas.sum())} menções classificadas', s)
    # 16 H9 classes
    h9 = T['H9_audiencias_classe'].dropna(subset=['classe_unica'])
    cl_ = T['H9_por_classe']
    fig, ax = plt.subplots(figsize=(7, 4.2))
    classes = sorted(h9.classe_unica.unique())
    for i, c in enumerate(classes):
        g = h9[h9.classe_unica == c]
        ax.scatter(i + np.random.default_rng(i).uniform(-.1, .1, len(g)), g.taxa, s=12 + 2 * g.n, alpha=.6)
        ax.hlines(g.taxa.mean(), i - .25, i + .25, color='k')
    ax.set_xticks(range(len(classes))); ax.set_xticklabels([f'{c}\n({(h9.classe_unica == c).sum()} AP)' for c in classes], fontsize=7)
    ax.set(ylabel='Taxa argumentativa por audiência')
    _t(ax, 'H9 — taxa por audiência segundo a classe processual (audiências de classe única)', f'Unidade: audiência (N={len(h9)}); traço = média; classes com poucas audiências ficam só descritivas')
    R.salvar(fig, 'fig16_h9_classe', 'H9', 'audiência', f'{len(h9)} audiências de classe única', h9)
    return R.itens
