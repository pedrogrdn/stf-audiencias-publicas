"""H1–H22. Unidade inferencial: AUDIÊNCIA. Menções nunca são permutadas nem tratadas como réplicas independentes.

Situações possíveis: 'Executado (exploratório)', 'Descritivo ...', 'Inviável ...', 'Exploratório: sensibilidade ...'.
Hipóteses de heterogeneidade/concentração (H3, H6, H10, H21) são DESCRITIVAS: sem valor-p."""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.stats import rankdata

import estatistica as E

EIXO_A = 'Direitos ambientais, políticas públicas e liberdade de mercado'
EIXO_P = 'Direitos da Personalidade'
EIXO_CURTO = {EIXO_A: 'Ambiental/políticas/mercado', EIXO_P: 'Personalidade'}
LOCAIS = ['Relatório', 'Voto do Relator', 'Voto']
PARES_LOCAL = [('Voto do Relator', 'Relatório'), ('Voto', 'Relatório'), ('Voto', 'Voto do Relator')]
ALVOS = ['Pessoa', 'Instituição', 'Pessoa e instituição']
SEM_NOME = 'Sem pessoa/instituição nos campos'
SCEN = {
    'sem_Relatório': lambda d: d[d.local != 'Relatório'],
    'sem_AP33': lambda d: d[d.audiencia != 33],
    'apenas_local_Voto': lambda d: d[d.local == 'Voto'],
    'sem_maior_audiência': lambda d: d[d.audiencia != d.audiencia.value_counts().idxmax()],
    'autoria_plena_sem_atribuição_por_metadado': lambda d: d[(d.autoria_plena == 1) & (d.atribuicao_metadado == 0)],
}
ROB_PADRAO = ('sem_Relatório', 'sem_AP33', 'sem_maior_audiência', 'autoria_plena_sem_atribuição_por_metadado')
NUMS: set = set()   # registro de todo número formatado (reconciliação relatório × código)


def fx(x, d=3, sinal=False):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return 'n/d'
    s = f'{x:+.{d}f}' if sinal else f'{x:.{d}f}'
    NUMS.add(s.lstrip('+-').replace('.', ','))
    return s.replace('.', ',')


def fp(p) -> str:
    """valor-p legível: <0,001 quando menor que 0,001 (valores exatos permanecem na coluna numérica)."""
    if p is None or not np.isfinite(p):
        return 'n/d'
    if p < 0.001:
        NUMS.add('0,001')
        return '<0,001'
    return fx(p, 3)


def fi(x) -> str:
    s = f'{int(x)}'
    NUMS.add(s)
    return s


def slug(t: str) -> str:
    return re.sub(r'[^0-9A-Za-zÀ-ÿ]+', '_', t).strip('_')[:90]


def sinal_igual(vals, ref):
    v = np.array([x for x in vals if np.isfinite(x)])
    return int((np.sign(v) == np.sign(ref)).sum()), len(v)


class Ctx:
    def __init__(self, cfg, m, a, saida, nivel='A'):
        self.cfg, self.P = cfg, cfg['parametros']
        m = m.copy()
        m['eixo_curto'] = m['eixo'].map(EIXO_CURTO)
        m['doc_aud'] = m['documento'] + '|AP' + m['audiencia'].astype(str)
        self.m, self.a, self.saida, self.nivel = m, a, saida, nivel
        self.rows, self.tabs, self.extra, self.seeds = [], {}, {}, {}
        self.fam = {h: f for f, hs in cfg['familias_BH'].items() for h in hs}
        self.cats = cfg['categorias']
        self.sens = nivel != 'A'
        self.rotulo_analise = 'Principal (A)' if nivel == 'A' else 'Sensibilidade A+B'

    def rng(self, tag):
        tag = f'{self.nivel}|{tag}'
        import zlib
        self.seeds[tag] = {'seed_global': self.P['seed'], 'crc32_rotulo': zlib.crc32(tag.encode('utf-8'))}
        return E.rng_tag(self.P['seed'], tag)

    def tab(self, nome, df):
        self.tabs[('AB_' if self.sens else '') + nome] = df

    def linha(self, h, teste, N, metodo, estimativa='n/d', incerteza='n/d', p=np.nan, robustez='', sentido='', limitacoes='',
              situacao='Executado (exploratório)', est=np.nan, lo=np.nan, hi=np.nan, pergunta=None, variaveis=None, unidade=None, familia=None):
        c = self.cfg['hipoteses'][h]
        fam = familia or (f'F_sensAB_{h}' if self.sens else self.fam.get(h, 'sem_familia'))
        self.rows.append({'Hipotese': h, 'Analise': self.rotulo_analise, 'Teste': teste + (' [A+B]' if self.sens else ''), 'Pergunta': pergunta or c['Pergunta'],
                          'Variaveis': variaveis or c['Variaveis'], 'Unidade': unidade or c['Unidade'], 'N': N, 'Metodo': metodo, 'Estimativa': estimativa,
                          'Incerteza': incerteza, 'valor_p': p, 'valor_p_BH': np.nan, 'Robustez': robustez, 'Interpretacao': '', 'Limitacoes': limitacoes,
                          'Situacao': situacao, 'Familia': fam, 'estimativa_num': est, 'ic_inf': lo, 'ic_sup': hi, '_sentido': sentido})

    def robustez(self, tag, calc, d, usar=ROB_PADRAO, loo=True, extra=None):
        Bs = min(1999, self.P['n_permutacoes'])
        partes = []
        main = calc(d, 0, None)[0]
        for nome in usar:
            try:
                r = calc(SCEN[nome](d), Bs, self.rng(f'{tag}|{nome}'))
                est, p = r[0], r[1]
                nn = f', {fi(r[2])} AP' if len(r) > 2 else ''
            except Exception:
                est, p, nn = np.nan, np.nan, ''
            partes.append(f'{nome}: {fx(est, 3, True)} (p={fp(p)}{nn})')
        if loo:
            ests = []
            for au in sorted(d.audiencia.unique()):
                try:
                    ests.append(calc(d[d.audiencia != au], 0, None)[0])
                except Exception:
                    pass
            ests = np.array([e for e in ests if np.isfinite(e)])
            if len(ests) and np.isfinite(main):
                ig, tot = sinal_igual(ests, main)
                partes.append(f'retirar uma audiência: {fx(ests.min(), 3, True)} a {fx(ests.max(), 3, True)}, mesmo sinal em {fi(ig)}/{fi(tot)}')
        if extra:
            partes += extra
        return '; '.join(partes)


def _ic_txt(lo, hi, n, minimo, tipo='bootstrap de audiências'):
    if np.isfinite(lo):
        return f'IC95% {tipo} [{fx(lo, 3, True)}; {fx(hi, 3, True)}] (n={n})'
    if isinstance(n, str) and '+' in n:   # comparação entre eixos (n = AP no eixo A + AP no eixo B)
        return f'IC não emitido (comparação entre eixos exige ≥{minimo} audiências em cada eixo; n={n})'
    return f'IC não emitido (exige ≥{minimo} audiências no total; n={n})'


# ----------------------------------------------------------------------------- blocos reutilizáveis
def teste_correlacao(ctx, h, teste, d, xcol, ycol_fn, tag, filtro=None, min_unid=None, sentido='', lim='', usar=ROB_PADRAO, extra_rob=None, n_extra=''):
    P = ctx.P
    min_unid = min_unid or P['min_audiencias_teste']

    def tab(dd):
        t = ycol_fn(dd)
        t = t[t[xcol].notna()] if xcol in t else t
        return filtro(t) if filtro else t

    def calc(dd, B, rng):
        t = tab(dd)
        r, p, _ = E.spearman_ap(t[xcol], t['y'], B, rng)
        return r, p, len(t)

    t = tab(d)
    n, nd = len(t), t[xcol].nunique()
    metodo = 'Spearman entre audiências (uma observação por audiência; pesos iguais); p por permutação entre audiências (Monte Carlo, +1); IC por bootstrap de audiências'
    if n < min_unid or nd < 3:
        ctx.linha(h, teste, f'{n} audiências{n_extra}', metodo, situacao=f'Inviável: {n} audiências e {nd} valores distintos de {xcol} (mínimo {min_unid} e 3)', sentido=sentido, limitacoes=lim)
        return None
    r, p, ci = E.spearman_ap(t[xcol], t['y'], P['n_permutacoes'], ctx.rng(tag), ci_B=P['n_bootstrap'] if n >= P['min_audiencias_ci'] else 0, rng_ci=ctx.rng(tag + '|boot'))
    ctx.linha(h, teste, f'{n} audiências; {fi(t["n"].sum()) if "n" in t else ""} menções{n_extra}', metodo, f'ρ de Spearman = {fx(r, 3, True)}',
              _ic_txt(*ci, n, P['min_audiencias_ci']), p, ctx.robustez(tag, calc, d, usar, extra=extra_rob), sentido, lim, est=r, lo=ci[0], hi=ci[1])
    return r


def teste_contraste(ctx, h, teste, d, grupo, g1, g0, y, tag, min_n=None, sentido='', lim='', usar=('sem_AP33', 'sem_maior_audiência', 'autoria_plena_sem_atribuição_por_metadado'),
                    bloco='audiencia', pergunta=None, familia=None, situacao_ok='Executado (exploratório)', rotulo_extra='', tabela=True):
    """Contraste g1−g0 de y calculado dentro de audiência (ou documento×audiência) e reduzido a UM valor por audiência.
    Inferência sobre a MÉDIA das diferenças por audiência: IC bootstrap de audiências (≥10) e teste de inversão de sinais
    (hipótese adicional de simetria em torno de zero sob a nula). Abaixo do suporte predefinido: apenas descrição, sem p e sem IC."""
    P = ctx.P
    min_n = min_n or P['min_mencoes_por_grupo_na_audiencia']
    min_aud = P['min_audiencias_teste']
    c = E.contraste_por_audiencia(d, grupo, g1, g0, y, min_n, bloco)
    nap = len(c)
    if tabela:
        ctx.tab(slug(f'{h}_{teste}{rotulo_extra}'), c.assign(minimo_por_grupo=min_n))
    metodo = (f'Contraste {g1} − {g0} em {y}, calculado dentro de cada {"audiência" if bloco == "audiencia" else "documento×audiência"} (mín. {fi(min_n)} menções por grupo) e reduzido a um valor por audiência; '
              f'estimando = média das diferenças por audiência (pesos iguais). IC: bootstrap percentil de audiências. p: inversão de sinais das diferenças por audiência, '
              f'que ASSUME simetria em torno de zero sob a nula (não é teste exato geral de igualdade nem causal). Menções não são permutadas.')

    def calc(dd, B, rng):
        cc = E.contraste_por_audiencia(dd, grupo, g1, g0, y, min_n, bloco)
        if len(cc) == 0:
            return np.nan, np.nan, 0
        p = E.sign_flip_media(cc['contraste'], B, rng)[1] if (B > 0 and len(cc) >= min_aud) else np.nan
        return float(cc['contraste'].mean()), p, len(cc)

    nm = int(c['n_g1'].sum() + c['n_g0'].sum()) if nap else 0
    if nap < min_aud:
        est = float(c['contraste'].mean()) if nap else np.nan
        ctx.linha(h, teste, f'{fi(nap)} audiências elegíveis; {fi(nm)} menções', metodo,
                  f'contraste médio descritivo = {fx(est, 3, True)} ({fi(nap)} audiências)' if nap else 'n/d', 'não emitida (suporte insuficiente)',
                  situacao=f'Inviável: suporte insuficiente no critério predefinido (≥{fi(min_n)} menções por grupo em ≥{fi(min_aud)} audiências; elegíveis: {fi(nap)})' + (' [sensibilidade exploratória de elegibilidade]' if rotulo_extra else ''),
                  sentido=sentido, limitacoes=lim, pergunta=pergunta, est=est, familia=familia)
        return c
    obs, p, desc = E.sign_flip_media(c['contraste'], P['n_permutacoes'], ctx.rng(tag))
    lo, hi = E.bootstrap_media(c['contraste'], P['n_bootstrap'], ctx.rng(tag + '|boot')) if nap >= P['min_audiencias_ci'] else (np.nan, np.nan)
    pesos = (c['n_g1'] * c['n_g0'] / (c['n_g1'] + c['n_g0']))
    ph = float((c['contraste'] * pesos).sum() / pesos.sum())
    extra = [f'peso por menção (n1·n0/(n1+n0)): {fx(ph, 3, True)}', f'mediana por audiência (descritiva; estimando distinto da média): {fx(float(c["contraste"].median()), 3, True)}',
             f'audiências com contraste >0: {fi((c["contraste"] > 0).sum())}, <0: {fi((c["contraste"] < 0).sum())}, =0: {fi((c["contraste"] == 0).sum())}']
    rob = ctx.robustez(tag, calc, d, usar, extra=extra)
    ctx.linha(h, teste, f'{fi(nap)} audiências elegíveis; {fi(nm)} menções', metodo + f' p {desc}.', f'contraste médio por audiência = {fx(obs, 3, True)} ({fx(100 * obs, 1, True)} p.p.)',
              _ic_txt(lo, hi, nap, P['min_audiencias_ci']), p, rob, sentido, lim, situacao=situacao_ok, est=obs, lo=lo, hi=hi, pergunta=pergunta, familia=familia)
    return c


def teste_interacao(ctx, h, teste, t, xcol, tag, sentido, lim):
    """taxa por audiência ~ x + eixo + x·eixo (OLS, pesos iguais). Incerteza: HC3 (t, n−k g.l.) e bootstrap estratificado de audiências.
    Aproximação com poucas audiências; não causal. Verifica posto, suporte por eixo e alavancagem; compara com modelo sem interação."""
    P = ctx.P
    t = t.copy()
    t['g'] = (t['eixo'] == EIXO_A).astype(int)
    por = t.groupby('g')
    nA, nB = por.size().get(1, 0), por.size().get(0, 0)
    dA, dB = por[xcol].nunique().get(1, 0), por[xcol].nunique().get(0, 0)
    metodo = ('OLS por audiência (taxa ~ x + eixo + x·eixo; x centrado; pesos iguais); EP robustos HC3 com IC e p por t (n−k g.l.) — aproximação com poucas audiências; '
              'IC adicional por bootstrap de audiências estratificado por eixo. Não causal.')
    if min(nA, nB) < P['min_audiencias_teste'] or min(dA, dB) < 3:
        ctx.linha(h, teste, f'{fi(nA)}+{fi(nB)} audiências', metodo, situacao=f'Inviável: audiências por eixo {fi(nA)}/{fi(nB)}; valores distintos de {xcol} por eixo {fi(dA)}/{fi(dB)} (mínimo {fi(P["min_audiencias_teste"])} e 3)', sentido=sentido, limitacoes=lim)
        return
    xc = t[xcol].to_numpy(float) - t[xcol].mean()
    y, g = t['taxa'].to_numpy(float), t['g'].to_numpy(float)
    fit = E.ols_hc3(y, np.column_stack([np.ones(len(t)), xc, g, xc * g]))
    if not fit['ok']:
        ctx.linha(h, teste, f'{fi(len(t))} audiências', metodo, situacao=f'Inviável: modelo com interação não estimável (posto {fi(fit["rank"])} de {fi(fit["k"])}; {fit.get("motivo", "")})', sentido=sentido, limitacoes=lim)
        return
    b, se, lo, hi, pv = fit['b'], fit['se'], fit['lo'], fit['hi'], fit['p']
    V = fit['V']
    sl1 = b[1] + b[3]
    se1 = float(np.sqrt(V[1, 1] + V[3, 3] + 2 * V[1, 3]))
    bl, bh_, nvalid = E.boot_interacao(y, xc, g, P['n_bootstrap'], ctx.rng(tag + '|boot'))
    red = E.ols_hc3(y, np.column_stack([np.ones(len(t)), xc, g]))
    loo = []
    for i in range(len(t)):
        mk = np.arange(len(t)) != i
        f2 = E.ols_hc3(y[mk], np.column_stack([np.ones(mk.sum()), xc[mk] - xc[mk].mean(), g[mk], (xc[mk] - xc[mk].mean()) * g[mk]]))
        if f2['ok']:
            loo.append(f2['b'][3])
    ig, tot = sinal_igual(loo, b[3])
    ctx.linha(h, teste, f'{fi(len(t))} audiências ({fi(nA)} ambiental/mercado; {fi(nB)} personalidade)', metodo,
              f'interação (inclinação ambiental − personalidade) = {fx(b[3], 4, True)} por unidade de x; inclinação personalidade {fx(b[1], 4, True)} (EP HC3 {fx(se[1], 4)}); ambiental {fx(sl1, 4, True)} (EP HC3 {fx(se1, 4)}); R² = {fx(fit["r2"], 3)}',
              f'EP HC3 {fx(se[3], 4)}; IC95% HC3 [{fx(lo[3], 4, True)}; {fx(hi[3], 4, True)}]; IC95% bootstrap de audiências [{fx(bl, 4, True)}; {fx(bh_, 4, True)}] ({fi(nvalid)} réplicas válidas)',
              float(pv[3]), f'posto {fi(fit["rank"])}/{fi(fit["k"])}; alavancagem máxima {fx(fit["hmax"], 2)}; modelo sem interação: inclinação comum {fx(red["b"][1], 4, True)} (EP HC3 {fx(red["se"][1], 4)}); retirar uma audiência: {fx(min(loo), 4, True)} a {fx(max(loo), 4, True)}, mesmo sinal em {fi(ig)}/{fi(tot)}',
              sentido, lim, est=float(b[3]), lo=float(lo[3]), hi=float(hi[3]))


def taxa_y(dd, col='arg'):
    t = E.aud_tabela(dd, col)
    t['y'] = t['taxa']
    return t


# ----------------------------------------------------------------------------- H1–H18
def h1_h2(ctx):
    m, P = ctx.m, ctx.P
    t = E.aud_tabela(m)
    ctx.tab('audiencias_base', t)
    ano = m.groupby('ano_julgamento').agg(n_audiencias=('audiencia', 'nunique'), n_mencoes=('arg', 'size'), n_argumentos=('arg', 'sum'),
                                          n_contexto=('tipo', lambda x: (x == 'Contexto').sum()), n_relato=('tipo', lambda x: (x == 'Relato').sum())).reset_index()
    ano['taxa_agregada'] = ano['n_argumentos'] / ano['n_mencoes']
    ano['taxa_contexto'] = ano['n_contexto'] / ano['n_mencoes']
    ano['taxa_relato'] = ano['n_relato'] / ano['n_mencoes']
    ano['media_taxa_por_audiencia'] = ano['ano_julgamento'].map(t.groupby('ano_julgamento')['taxa'].mean())
    ctx.tab('H1_por_ano_julgamento', ano)
    lim = ('Poucas audiências por ano; composição temática varia com o calendário; eixos não randomizados; ano de julgamento único por audiência (AP5 tem duas datas no mesmo ano). '
           'Taxa = composição das menções observadas, não probabilidade de aproveitamento.')

    def wc(dd, B, rng):
        tt = taxa_y(dd)
        x, y, w = tt['ano_julgamento'].to_numpy(float), tt['taxa'].to_numpy(float), tt['n'].to_numpy(float)

        def wcorr(x, Y, W):
            mx, my = (W * x).sum(-1, keepdims=True) / W.sum(-1, keepdims=True), (W * Y).sum(-1, keepdims=True) / W.sum(-1, keepdims=True)
            return (W * (x - mx) * (Y - my)).sum(-1) / np.sqrt((W * (x - mx) ** 2).sum(-1) * (W * (Y - my) ** 2).sum(-1))
        obs = float(wcorr(x, y, w))
        if B <= 0:
            return obs, np.nan
        idx = rng.permuted(np.tile(np.arange(len(x)), (B, 1)), axis=1)   # permuta (y, peso) entre AUDIÊNCIAS
        return obs, E.pmc(obs, wcorr(x, y[idx], w[idx]))
    wr = wc(m, P['n_permutacoes'], ctx.rng('H1|ponderado'))
    teste_correlacao(ctx, 'H1', 'Ano do julgamento × taxa por audiência', m, 'ano_julgamento', taxa_y, 'H1|ano_julgamento', sentido='ρ>0: audiências julgadas mais tarde têm taxa argumentativa maior', lim=lim,
                     extra_rob=[f'Pearson ponderado por menções (permutação entre audiências): {fx(wr[0], 3, True)} (p={fp(wr[1])})'])
    teste_correlacao(ctx, 'H1', 'Ano da audiência × taxa por audiência (secundário)', m, 'ano_audiencia', taxa_y, 'H1|ano_audiencia', sentido='ρ>0: audiências mais recentes têm taxa maior', lim=lim)
    # H2: AP33 tem intervalo cadastrado −1 (dado original preservado; não é duração negativa verdadeira)
    neg = t[t.intervalo < 0]
    ap33 = ', '.join(f'AP{fi(r.audiencia)} ({fi(r.n)} menções; intervalo cadastrado {fi(r.intervalo)} ano)' for r in neg.itertuples())

    def calc_neg(dd, B, rng):
        tt = taxa_y(dd)
        r, p, _ = E.spearman_ap(tt['intervalo'], tt['taxa'], B, rng)
        return r, p
    r_all = calc_neg(m, P['n_permutacoes'], ctx.rng('H2|com_cadastro_negativo'))
    n_exc = int(neg['n'].sum())
    teste_correlacao(ctx, 'H2', 'Intervalo em anos (julgamento − audiência) × taxa', m, 'intervalo', taxa_y, 'H2|intervalo', filtro=lambda tt: tt[tt.intervalo >= 0],
                     sentido='ρ>0: maior intervalo em anos associado a taxa maior', usar=('sem_Relatório', 'sem_maior_audiência', 'autoria_plena_sem_atribuição_por_metadado'),
                     lim=f'Diferença de anos (não duração em dias). DENOMINADOR EXCLUÍDO: {ap33} — o valor −1 é o dado original preservado (inconsistência cadastral não resolvida), não duração negativa verdadeira; fora do estimando de H2, mantido em todas as demais análises. ' + lim,
                     extra_rob=[f'sensibilidade com o valor cadastrado (−1) mantido, todas as {fi(len(t))} audiências: ρ={fx(r_all[0], 3, True)} (p={fp(r_all[1])})'], n_extra=f' (excluídas: {fi(len(neg))} audiência com {fi(n_exc)} menções)')
    ctx.extra['h2_excluidas'] = ap33


def h16_h13(ctx):
    t = E.aud_tabela(ctx.m)
    lim = 'Interação com poucas audiências por eixo; eixos e calendário confundidos; observacional; modelo parcimonioso, não causal.'
    teste_interacao(ctx, 'H16', 'Intervalo × eixo', t[t.intervalo >= 0], 'intervalo', 'H16', 'positivo: inclinação da taxa por ano de intervalo maior no eixo ambiental/mercado', lim + ' AP33 (intervalo cadastrado −1) fora deste denominador.')
    teste_interacao(ctx, 'H13', 'Ano do julgamento × eixo', t, 'ano_julgamento', 'H13', 'positivo: tendência temporal mais crescente no eixo ambiental/mercado', lim)
    ctx.tab('H13_audiencias_por_ano_eixo', t.groupby(['ano_julgamento', 'eixo']).agg(n_audiencias=('audiencia', 'size'), n_mencoes=('n', 'sum'), n_argumentos=('k', 'sum')).reset_index())


def suporte_ministros(ctx):
    m = ctx.m
    g = m.groupby('ministro').agg(n_mencoes=('arg', 'size'), n_argumentos=('arg', 'sum'), n_audiencias=('audiencia', 'nunique'), n_documentos=('documento', 'nunique'),
                                 n_anos=('ano_julgamento', 'nunique'), n_atribuicao_metadado=('atribuicao_metadado', 'sum'), autoria_plena=('autoria_plena', 'max'),
                                 n_relatorio=('local', lambda x: (x == 'Relatório').sum())).reset_index()
    g['taxa'] = g['n_argumentos'] / g['n_mencoes']
    sv = m[m.local != 'Relatório'].groupby('ministro')['arg'].agg(['size', 'sum']).rename(columns={'size': 'n_fora_relatorio', 'sum': 'arg_fora_relatorio'})
    g = g.merge(sv, left_on='ministro', right_index=True, how='left').fillna({'n_fora_relatorio': 0, 'arg_fora_relatorio': 0})
    g['taxa_fora_relatorio'] = np.where(g['n_fora_relatorio'] > 0, g['arg_fora_relatorio'] / g['n_fora_relatorio'].replace(0, np.nan), np.nan)
    ctx.tab('suporte_ministros', g.sort_values('n_mencoes', ascending=False))
    return g


def h3(ctx):
    """DESCRITIVO. Sem valor-p: permutar menções dentro do documento trataria menções como réplicas independentes."""
    P, m = ctx.P, ctx.m
    g = suporte_ministros(ctx)
    ok = g[(g.autoria_plena == 1) & (g.n_mencoes >= P['min_mencoes_ministro']) & (g.n_audiencias >= P['min_audiencias_ministro'])].copy()
    ok['com_suporte'] = True
    ctx.tab('H3_ministros_com_suporte', ok)
    d = m[m.ministro.isin(ok.ministro)]
    docs = d.groupby('documento')['ministro'].nunique()
    inf = docs[docs >= 2].index
    linhas = []
    for doc in inf:
        x = d[d.documento == doc].groupby('ministro')['arg'].agg(['size', 'sum'])
        x = x[x['size'] >= P['min_mencoes_por_grupo_no_documento']]
        if len(x) >= 2:
            tx = x['sum'] / x['size']
            linhas.append({'documento': doc, 'n_ministros': len(x), 'n_mencoes': int(x['size'].sum()), 'amplitude_taxas': float(tx.max() - tx.min()), 'taxa_min': float(tx.min()), 'taxa_max': float(tx.max())})
    dd = pd.DataFrame(linhas)
    ctx.tab('H3_amplitude_dentro_documento', dd)
    q = ok['taxa'].quantile([.25, .5, .75]) if len(ok) else pd.Series([np.nan] * 3, index=[.25, .5, .75])
    n_meta = int(m['atribuicao_metadado'].sum())
    n_np = int((m['autoria_plena'] == 0).sum())
    est = (f'{fi(len(ok))} ministros com suporte; taxa observada por ministro: mín {fx(ok.taxa.min(), 3)}, quartis {fx(q[.25], 3)}/{fx(q[.5], 3)}/{fx(q[.75], 3)}, máx {fx(ok.taxa.max(), 3)}; '
           f'{fi(len(dd))} documentos com ≥2 ministros (≥{fi(P["min_mencoes_por_grupo_no_documento"])} menções cada), amplitude mediana de taxas dentro do documento {fx(dd.amplitude_taxas.median(), 3) if len(dd) else "n/d"}') if len(ok) else 'n/d'
    ctx.linha('H3', 'Heterogeneidade observada entre ministros (descrição com denominadores)', f'{fi(len(ok))} ministros (≥{fi(P["min_mencoes_ministro"])} menções, ≥{fi(P["min_audiencias_ministro"])} audiências, autoria plena); {fi(ok.n_mencoes.sum())} menções',
              'Tabelas de n, Argumentos e taxa por ministro e amplitude das taxas entre ministros do mesmo documento. SEM valor-p: permutar menções (ou rótulos de ministro) entre menções do documento trataria menções como réplicas independentes, o que não é autorizado.',
              est, 'não emitida (descrição)', np.nan, 'Ver T_H3_ministros_com_suporte.csv, T_suporte_ministros.csv e T_H3_amplitude_dentro_documento.csv', '',
              f'{fi(n_meta)} menções têm ministro atribuído por metadado (relator), não por fala: não é autoria pessoal; {fi(n_np)} sem autoria plena; sem universo de votos; Relatório ≠ voto; local de menção não controlado; taxas com denominador pequeno são instáveis; sem inferência sobre preferências individuais.',
              situacao='Descritivo (heterogeneidade observada; sem valor-p)', est=np.nan)


def h4(ctx):
    P, m = ctx.P, ctx.m
    d = m[(m.local != 'Relatório') & (m.relator_indeterminado == 0)].copy()
    rel = m[(m.local == 'Relatório')].groupby('ministro_eh_relator').agg(n=('arg', 'size'), k=('arg', 'sum'), taxa=('arg', 'mean')).reset_index()
    ctx.tab('H4_relatorio_descritivo_separado', rel)
    xt = d.groupby(['local', 'ministro_eh_relator']).agg(n=('arg', 'size'), k=('arg', 'sum'), n_audiencias=('audiencia', 'nunique')).reset_index()
    xt['taxa'] = xt['k'] / xt['n']
    ctx.tab('H4_relator_x_local', xt)
    n_rel_voto = int(((d.local == 'Voto') & (d.ministro_eh_relator == 1)).sum())
    n_rel_total = int((d.ministro_eh_relator == 1).sum())
    mn = P['min_mencoes_por_grupo_no_documento']
    lim = (f'CONFUSÃO RELATOR × LOCAL: só {fi(n_rel_voto)} de {fi(n_rel_total)} menções do relator (fora do Relatório) estão em local=Voto (as demais em Voto do Relator); o contraste mistura relator e local e NÃO mede efeito da função de relator. '
           'Associação documental exploratória. Relator cadastrado extraído automaticamente; Voto não garante autoria de outro julgador; processos conexos compartilham texto (blocos documento×audiência; um valor por audiência); sem universo de votos.')
    teste_contraste(ctx, 'H4', 'Relator cadastrado − demais julgadores (fora do Relatório; associação documental exploratória)', d, 'ministro_eh_relator', 1, 0, 'arg', 'H4', min_n=mn, bloco='doc_aud',
                    sentido='positivo: taxa argumentativa maior nas menções atribuídas ao relator cadastrado do que às dos demais ministros no mesmo documento (confundido com local)',
                    usar=('sem_AP33', 'sem_maior_audiência', 'autoria_plena_sem_atribuição_por_metadado'), lim=lim)
    dv = d[d.local == 'Voto']
    teste_contraste(ctx, 'H4', 'Relator cadastrado − demais (apenas local = Voto, controla o local)', dv, 'ministro_eh_relator', 1, 0, 'arg', 'H4|voto', min_n=mn, bloco='doc_aud',
                    sentido='positivo: relator com taxa maior em local=Voto', usar=('sem_AP33',), lim='Controla o local; se não houver audiências elegíveis, o efeito da função de relator não é separável do local nestes dados.')


def h5_h6(ctx):
    P, m = ctx.P, ctx.m

    def calc(dd, B, rng):
        t = taxa_y(dd)
        r = E.diff_grupos_ap(t['taxa'], (t.eixo == EIXO_A).astype(int), B, rng)
        return r[0], r[1], len(t)
    t = taxa_y(m)
    nA, nB = int((t.eixo == EIXO_A).sum()), int((t.eixo != EIXO_A).sum())
    est, p, ci = E.diff_grupos_ap(t['taxa'], (t.eixo == EIXO_A).astype(int), P['n_permutacoes'], ctx.rng('H5'), P['n_bootstrap'] if min(nA, nB) >= P['min_audiencias_ci'] else 0, rng_ci=ctx.rng('H5|boot'))
    pool = m.groupby('eixo')['arg'].agg(['sum', 'size'])
    pa, pb = pool.loc[EIXO_A, 'sum'] / pool.loc[EIXO_A, 'size'], pool.loc[EIXO_P, 'sum'] / pool.loc[EIXO_P, 'size']
    ctx.tab('H5_por_eixo', pd.DataFrame({'eixo': list(pool.index), 'n_audiencias': [int((t.eixo == e).sum()) for e in pool.index], 'n_mencoes': pool['size'].values, 'n_argumentos': pool['sum'].values,
                                         'taxa_agregada': (pool['sum'] / pool['size']).values, 'media_taxa_por_audiencia': [t[t.eixo == e].taxa.mean() for e in pool.index],
                                         'mediana_taxa_por_audiencia': [t[t.eixo == e].taxa.median() for e in pool.index]}))
    ctx.linha('H5', 'Eixo ambiental/mercado − personalidade (taxa por audiência)', f'{fi(nA)} vs {fi(nB)} audiências; {fi(len(m))} menções',
              'Diferença de médias de taxas por audiência (pesos iguais); p por permutação dos rótulos de eixo ENTRE audiências (trocabilidade das audiências sob a nula; eixos não randomizados); IC por bootstrap de audiências dentro de eixo',
              f'Δ = {fx(est, 3, True)} ({fx(100 * est, 1, True)} p.p.)', _ic_txt(*ci, f'{fi(nA)}+{fi(nB)}', P['min_audiencias_ci']), p,
              ctx.robustez('H5', calc, m, extra=[f'peso por menção (taxas agregadas; estimando distinto): {fx(pa - pb, 3, True)} ({fx(pa, 3)} vs {fx(pb, 3)})']),
              'Δ>0: taxa argumentativa média maior no eixo ambiental/mercado', 'Eixos não randomizados; audiências não amostradas aleatoriamente; sem efeito causal do tema; sem representatividade.', est=est, lo=ci[0], hi=ci[1])
    # H6: descrição da heterogeneidade observada entre audiências, sem valor-p
    rows, resumo = [], []
    for e in (EIXO_A, EIXO_P):
        d = m[m.eixo == e]
        tt = taxa_y(d).sort_values('taxa')
        q = tt['taxa'].quantile([.25, .5, .75])
        ext_b = ', '.join(f'AP{fi(r.audiencia)} {fx(r.taxa, 2)} (n={fi(r.n)})' for r in tt.head(3).itertuples())
        ext_a = ', '.join(f'AP{fi(r.audiencia)} {fx(r.taxa, 2)} (n={fi(r.n)})' for r in tt.tail(3).iloc[::-1].itertuples())
        for r in tt.itertuples():
            rows.append({'eixo': e, 'audiencia': r.audiencia, 'n_mencoes': r.n, 'n_argumentos': r.k, 'taxa': r.taxa})
        resumo.append({'eixo': e, 'n_audiencias': len(tt), 'n_mencoes': int(tt.n.sum()), 'taxa_min': tt.taxa.min(), 'q1': q[.25], 'mediana': q[.5], 'q3': q[.75], 'taxa_max': tt.taxa.max(),
                       'dp_taxas_audiencia': tt.taxa.std(), 'taxa_agregada': tt.k.sum() / tt.n.sum()})
        ctx.linha('H6', f'Heterogeneidade observada entre audiências — {EIXO_CURTO[e]}', f'{fi(len(tt))} audiências; {fi(tt.n.sum())} menções',
                  'Descrição das taxas por audiência (mín, quartis, máx, desvio-padrão) e casos extremos com denominador. SEM valor-p: testar heterogeneidade "além do acaso binomial" exigiria tratar menções como independentes.',
                  f'taxas por audiência: mín {fx(tt.taxa.min(), 2)}, quartis {fx(q[.25], 2)}/{fx(q[.5], 2)}/{fx(q[.75], 2)}, máx {fx(tt.taxa.max(), 2)}; desvio-padrão {fx(tt.taxa.std(), 3)}; menores: {ext_b}; maiores: {ext_a}',
                  'não emitida (descrição)', np.nan, 'Ver T_H6_taxas_por_audiencia.csv e T_H6_resumo_por_eixo.csv', '',
                  'Descrição; não identifica a causa da dispersão; tema específico confunde-se com audiência; taxas com poucos denominadores oscilam muito; dependência entre menções do mesmo texto.',
                  situacao='Descritivo (heterogeneidade observada; sem valor-p)')
    ctx.tab('H6_taxas_por_audiencia', pd.DataFrame(rows))
    ctx.tab('H6_resumo_por_eixo', pd.DataFrame(resumo))


def h7_h14(ctx):
    P, m = ctx.P, ctx.m
    d = m[m.autoria_plena == 1]
    t = d.groupby(['ministro', 'eixo_curto']).agg(n=('arg', 'size'), k=('arg', 'sum'), n_aud=('audiencia', 'nunique')).reset_index()
    t['taxa'] = t['k'] / t['n']
    ctx.tab('H7_ministro_x_eixo', t)
    w = t.pivot(index='ministro', columns='eixo_curto', values=['n', 'n_aud']).fillna(0)
    ambos = [x for x in w.index if (w.loc[x, ('n', 'Personalidade')] >= P['min_mencoes_ministro']) and (w.loc[x, ('n', 'Ambiental/políticas/mercado')] >= P['min_mencoes_ministro'])
             and (w.loc[x, ('n_aud', 'Personalidade')] >= 3) and (w.loc[x, ('n_aud', 'Ambiental/políticas/mercado')] >= 3)]
    n_meta = int(m['atribuicao_metadado'].sum())
    ctx.linha('H7', 'Ministro × eixo', f'{fi(d.ministro.nunique())} ministros com autoria plena; {fi(len(ambos))} com suporte nos dois eixos', 'Tabela descritiva com denominadores; sem modelo de interação ampla',
              f'{fi(len(ambos))} ministros com ≥{fi(P["min_mencoes_ministro"])} menções e ≥3 audiências em ambos os eixos', 'não emitida', situacao='Descritivo (interação ampla desaconselhada; suporte listado)',
              limitacoes=f'Células escassas; atribuição automática; autoria por metadado em {fi(n_meta)} menções; ministros diferem em audiências e documentos; sem universo de votos.', robustez='n/a')
    t2 = d.groupby(['ministro', 'ano_julgamento']).agg(n=('arg', 'size'), k=('arg', 'sum')).reset_index()
    t2['taxa'] = t2['k'] / t2['n']
    ctx.tab('H14_ministro_x_ano', t2)
    anos = t2[t2.n >= 5].groupby('ministro').size()
    ctx.linha('H14', 'Ministro × ano', f'{fi(d.ministro.nunique())} ministros; {fi((anos >= 3).sum())} com ≥3 anos com ≥5 menções', 'Tabela descritiva ministro × ano; sem modelo', f'{fi((anos >= 3).sum())} ministros com cobertura de ≥3 anos', 'não emitida',
              situacao='Descritivo (modelo amplo desaconselhado)', limitacoes='Composição da Corte e atribuição documental variam; ausência de linha ≠ voto sem menção; confunde-se com audiência/documento.', robustez='n/a')


def h8_h15_h17_h11_h12(ctx):
    m, P = ctx.m, ctx.P
    tl = m.groupby('local').agg(n=('arg', 'size'), n_arg=('arg', 'sum'), n_aud=('audiencia', 'nunique')).reset_index()
    tl['taxa_agregada'] = tl['n_arg'] / tl['n']
    ctx.tab('H8_por_local', tl)
    # distribuição tripla Contexto/Relato/Argumento por local (descritiva, 3 categorias)
    ct = pd.crosstab(m['local'], m['tipo'])[['Contexto', 'Relato', 'Argumento']]
    ctx.tab('H8_local_x_tipo', ct.assign(n=ct.sum(axis=1)).reset_index())
    ap_sh = m.groupby(['audiencia', 'local'])['tipo'].value_counts(normalize=True).unstack(fill_value=0).reset_index()
    ctx.tab('H8_composicao_tripla_por_audiencia_local', m.groupby(['audiencia', 'local'])['tipo'].value_counts().unstack(fill_value=0).reset_index())
    mean_sh = ap_sh.groupby('local')[['Contexto', 'Relato', 'Argumento']].mean()
    txt = '; '.join(f'{loc}: Contexto {fx(100 * ct.loc[loc, "Contexto"] / ct.loc[loc].sum(), 1)}%, Relato {fx(100 * ct.loc[loc, "Relato"] / ct.loc[loc].sum(), 1)}%, Argumento {fx(100 * ct.loc[loc, "Argumento"] / ct.loc[loc].sum(), 1)}% (n={fi(ct.loc[loc].sum())})' for loc in LOCAIS)
    ctx.linha('H8', 'Distribuição Contexto/Relato/Argumento por local (3 categorias, descritiva)', f'{fi(len(m))} menções; {fi(m.audiencia.nunique())} audiências', 'Proporções condicionais por local (agregado por menção) e médias por audiência em tabela; sem teste de associação com menções como réplicas',
              txt, 'não emitida (descrição)', np.nan, 'Médias das proporções por audiência: ' + '; '.join(f'{loc}: C {fx(mean_sh.loc[loc, "Contexto"], 3)}/R {fx(mean_sh.loc[loc, "Relato"], 3)}/A {fx(mean_sh.loc[loc, "Argumento"], 3)}' for loc in LOCAIS), '',
              'Local extraído automaticamente; menções do mesmo documento/ministro são correlacionadas; o Relatório tem função documental distinta; agregado por menção e média por audiência respondem a perguntas diferentes.', situacao='Descritivo (3 categorias; sem valor-p)')
    lim8 = 'Local extraído automaticamente; menções do mesmo documento correlacionadas (um valor por audiência); relatório tem função documental distinta; observacional.'
    res_loc = {}
    for g1, g0 in PARES_LOCAL:
        res_loc[(g1, g0)] = teste_contraste(ctx, 'H8', f'Taxa argumentativa: {g1} − {g0}', m[m.local.isin([g1, g0])], 'local', g1, g0, 'arg', f'H8|{g1}|{g0}',
                                            sentido=f'positivo: taxa argumentativa maior em "{g1}" do que em "{g0}" na mesma audiência', lim=lim8)
    # H15 ORIGINAL: composição da localização (prevalência por AP) × eixo; AP é a unidade
    n_ap = m.groupby('audiencia').size()
    elig = n_ap[n_ap >= P['min_mencoes_por_grupo_na_audiencia']].index
    mm = m[m.audiencia.isin(elig)]
    comp = pd.crosstab(mm['audiencia'], mm['local'])
    comp = comp.reindex(columns=LOCAIS, fill_value=0)
    sh = comp.div(comp.sum(axis=1), axis=0)
    eixo_ap = m.groupby('audiencia')['eixo'].first()
    tcomp = sh.assign(n=comp.sum(axis=1), eixo=eixo_ap.reindex(sh.index)).reset_index()
    ctx.tab('H15_composicao_local_por_audiencia', tcomp)
    ctx.tab('H15_local_x_eixo_pooled', pd.crosstab(m['eixo_curto'], m['local']).reset_index())
    nA, nB = int((tcomp.eixo == EIXO_A).sum()), int((tcomp.eixo == EIXO_P).sum())
    for loc in LOCAIS:
        def calc(dd, B, rng, loc=loc):
            n2 = dd.groupby('audiencia').size()
            d2 = dd[dd.audiencia.isin(n2[n2 >= P['min_mencoes_por_grupo_na_audiencia']].index)]
            s = d2.assign(f=(d2.local == loc).astype(int)).groupby('audiencia').agg(v=('f', 'mean'), eixo=('eixo', 'first'))
            r = E.diff_grupos_ap(s['v'], (s.eixo == EIXO_A).astype(int), B, rng)
            return r[0], r[1], len(s)
        est, p, ci = E.diff_grupos_ap(sh[loc].to_numpy(), (tcomp.eixo == EIXO_A).astype(int), P['n_permutacoes'], ctx.rng(f'H15|{loc}'), P['n_bootstrap'] if min(nA, nB) >= P['min_audiencias_ci'] else 0, rng_ci=ctx.rng(f'H15|{loc}|boot'))
        pool = m.groupby('eixo_curto')['local'].apply(lambda s: (s == loc).mean())
        ctx.linha('H15', f'Prevalência de menções em "{loc}": ambiental/mercado − personalidade', f'{fi(nA)}+{fi(nB)} audiências (≥{fi(P["min_mencoes_por_grupo_na_audiencia"])} menções); {fi(len(mm))} menções',
                  'Fração de menções da audiência em cada local (composição; soma 1 por audiência); diferença de médias entre eixos com audiência como unidade; p por permutação do eixo entre audiências; IC bootstrap de audiências. Os três locais são partes de uma composição (dependentes entre si).',
                  f'Δ da fração em "{loc}" = {fx(est, 3, True)} ({fx(100 * est, 1, True)} p.p.)', _ic_txt(*ci, f'{fi(nA)}+{fi(nB)}', P['min_audiencias_ci']), p,
                  ctx.robustez(f'H15|{loc}', calc, m, ('sem_AP33', 'sem_maior_audiência'), extra=[f'agregado por menção: ' + '; '.join(f'{e} {fx(v, 3)}' for e, v in pool.items())]),
                  f'positivo: maior fração de menções em "{loc}" no eixo ambiental/mercado', 'Localização extraída automaticamente; composição de locais depende da estrutura do acórdão e do relator; observacional; 3 locais não são testes independentes.', est=est, lo=ci[0], hi=ci[1])
    # análise ADICIONAL (não substitui H15): interação local × eixo no contraste de taxa de Argumento
    for g1, g0 in PARES_LOCAL:
        c = res_loc[(g1, g0)]
        if c is None or len(c) == 0:
            ctx.linha('H15', f'[análise adicional] Contraste de Argumento {g1} − {g0}: diferença entre eixos', '0 audiências elegíveis', 'Diferença entre eixos dos contrastes por audiência', situacao='Inviável: nenhuma audiência elegível', familia='F_adicional')
            continue
        eix = c['audiencia'].map(eixo_ap).eq(EIXO_A).astype(int).to_numpy()
        nA2, nB2 = int(eix.sum()), int((1 - eix).sum())
        metodo = 'ANÁLISE ADICIONAL (interação local × eixo na taxa de Argumento; não substitui H15): diferença entre eixos das médias dos contrastes por audiência; p por permutação do eixo entre audiências; IC bootstrap de audiências'
        if min(nA2, nB2) < P['min_audiencias_teste']:
            ctx.linha('H15', f'[análise adicional] Contraste de Argumento {g1} − {g0}: diferença entre eixos', f'{fi(nA2)}+{fi(nB2)} audiências elegíveis', metodo,
                      situacao=f'Inviável: audiências elegíveis por eixo {fi(nA2)}/{fi(nB2)} (mínimo {fi(P["min_audiencias_teste"])})', limitacoes='Poucas audiências com os dois locais em cada eixo.', robustez='n/a', familia='F_adicional')
            continue
        v = c['contraste'].to_numpy()
        est, p, ci = E.diff_grupos_ap(v, eix, P['n_permutacoes'], ctx.rng(f'H15x|{g1}|{g0}'), P['n_bootstrap'] if min(nA2, nB2) >= P['min_audiencias_ci'] else 0, rng_ci=ctx.rng(f'H15x|{g1}|{g0}|boot'))
        loo = [E.diff_grupos_ap(np.delete(v, i), np.delete(eix, i), 0, None)[0] for i in range(len(v))]
        ig, tot = sinal_igual(loo, est)
        ctx.linha('H15', f'[análise adicional] Contraste de Argumento {g1} − {g0}: diferença entre eixos', f'{fi(nA2)}+{fi(nB2)} audiências elegíveis', metodo, f'Δ de contrastes = {fx(est, 3, True)}',
                  _ic_txt(*ci, f'{fi(nA2)}+{fi(nB2)}', P['min_audiencias_ci']), p, f'retirar uma audiência elegível: {fx(min(loo), 3, True)} a {fx(max(loo), 3, True)}, mesmo sinal em {fi(ig)}/{fi(tot)}',
                  'positivo: o contraste de local é maior no eixo ambiental/mercado', 'Interação de segunda ordem com poucas audiências; observacional; exploratória.', est=est, lo=ci[0], hi=ci[1], familia='F_adicional')
    # H11: tipo de alvo derivado × função (3 categorias) e contrastes de Argumento
    tt = pd.crosstab(m['tipo_alvo_derivado'], m['tipo']).reset_index()
    tt['n'] = tt[['Argumento', 'Contexto', 'Relato']].sum(axis=1)
    for c in ('Argumento', 'Contexto', 'Relato'):
        tt[f'prop_{c}'] = tt[c] / tt['n']
    ctx.tab('H11_tipo_alvo_x_tipo_mencao', tt)
    ctx.linha('H11', 'Distribuição Contexto/Relato/Argumento por tipo de alvo derivado (3 categorias, descritiva)', f'{fi(len(m))} menções', 'Proporções condicionais por tipo de alvo derivado (agregado por menção); sem teste com menções como réplicas',
              '; '.join(f'{r.tipo_alvo_derivado}: C {fx(100 * r.prop_Contexto, 1)}%, R {fx(100 * r.prop_Relato, 1)}%, A {fx(100 * r.prop_Argumento, 1)}% (n={fi(r.n)})' for r in tt.itertuples()), 'não emitida (descrição)', np.nan, 'T_H11_tipo_alvo_x_tipo_mencao.csv', '',
              'Proxy por campos Pessoa/Instituição preenchidos; não indica ação, influência ou individualização substantiva; campos vazios isolados não provam referência genérica.', situacao='Descritivo (3 categorias; sem valor-p)')
    lim11 = 'Proxy por campos Pessoa/Instituição preenchidos; não indica ação, influência ou individualização substantiva; campos vazios não provam referência genérica; nº de alvos ≠ nº de contribuições.'
    for alvo in ALVOS:
        teste_contraste(ctx, 'H11', f'Taxa argumentativa: {alvo} − {SEM_NOME}', m[m.tipo_alvo_derivado.isin([alvo, SEM_NOME])], 'tipo_alvo_derivado', alvo, SEM_NOME, 'arg', f'H11|{alvo}',
                        sentido=f'positivo: taxa argumentativa maior em menções com "{alvo}" do que sem nome, na mesma audiência', lim=lim11, usar=('sem_Relatório', 'sem_AP33', 'sem_maior_audiência'))
    teste_contraste(ctx, 'H12', 'Individualizada (pessoa ou instituição nos campos) − sem nome', m, 'individualizada', 1, 0, 'arg', 'H12',
                    sentido='positivo: taxa argumentativa maior nas menções com nome nos campos do que sem nome, na mesma audiência', lim=lim11 + ' H12 agrega os contrastes de H11 (não são independentes).', usar=('sem_Relatório', 'sem_AP33', 'sem_maior_audiência'))
    # H17: alvo × localização
    ax = pd.crosstab(m['tipo_alvo_derivado'], m['local'])[LOCAIS]
    ctx.tab('H17_alvo_x_local', ax.reset_index())
    axp = ax.div(ax.sum(axis=0), axis=1)
    ctx.linha('H17', 'Distribuição do tipo de alvo por local (4 categorias, descritiva)', f'{fi(len(m))} menções', 'Proporção de cada tipo de alvo derivado dentro de cada local (agregado por menção); sem teste com menções como réplicas',
              '; '.join(f'{loc}: ' + ', '.join(f'{a_} {fx(100 * axp.loc[a_, loc], 1)}%' for a_ in ax.index) + f' (n={fi(ax[loc].sum())})' for loc in LOCAIS), 'não emitida (descrição)', np.nan, 'T_H17_alvo_x_local.csv', '',
              lim11 + ' Local extraído automaticamente.', situacao='Descritivo (4 categorias; sem valor-p)')
    for g1, g0 in PARES_LOCAL:
        teste_contraste(ctx, 'H17', f'Proporção individualizada (alvo com nome): {g1} − {g0}', m[m.local.isin([g1, g0])], 'local', g1, g0, 'individualizada', f'H17|{g1}|{g0}',
                        sentido=f'positivo: maior proporção de menções com nome nos campos em "{g1}" do que em "{g0}"', lim=lim11 + ' Local extraído automaticamente; um valor por audiência.', usar=('sem_AP33', 'sem_maior_audiência'))


def h9(ctx):
    m, P = ctx.m, ctx.P
    t = taxa_y(m)
    cls = m.groupby('audiencia')['classe'].agg(lambda s: sorted(set(s)))
    t['classes'] = t['audiencia'].map(cls)
    t['classe_unica'] = t['classes'].map(lambda c: c[0] if len(c) == 1 else None)
    tab = m.groupby('classe').agg(n_mencoes=('arg', 'size'), n_argumentos=('arg', 'sum'), n_audiencias=('audiencia', 'nunique'), n_documentos=('documento', 'nunique')).reset_index()
    tab['taxa_agregada'] = tab['n_argumentos'] / tab['n_mencoes']
    tab['n_audiencias_classe_unica'] = tab['classe'].map(t.groupby('classe_unica').size()).fillna(0).astype(int)
    tab['testada'] = tab['n_audiencias_classe_unica'] >= 3
    ctx.tab('H9_por_classe', tab)
    elig = tab.loc[tab.testada, 'classe'].tolist()

    def kw(vals, lab):
        r = rankdata(vals)
        N = len(r)
        s = sum(r[lab == g].sum() ** 2 / (lab == g).sum() for g in set(lab))
        return 12 / (N * (N + 1)) * s - 3 * (N + 1)

    def calc(dd, B, rng):
        tt = taxa_y(dd)
        tt['cu'] = tt['audiencia'].map(cls).map(lambda c: c[0] if len(c) == 1 else None)
        tt = tt[tt.cu.isin(elig)]
        v, lab = tt['taxa'].to_numpy(), tt['cu'].to_numpy()
        if len(set(lab)) < 2:
            return np.nan, np.nan, 0
        obs = kw(v, lab)
        if B <= 0:
            return obs, np.nan, len(tt)
        null = np.array([kw(v, rng.permutation(lab)) for _ in range(B)])   # permuta rótulos entre AUDIÊNCIAS
        return obs, E.pmc(obs, null, 'greater'), len(tt)
    ctx.tab('H9_audiencias_classe', t[['audiencia', 'classes', 'classe_unica', 'n', 'k', 'taxa']].assign(classes=lambda x: x.classes.map(json.dumps)))
    if len(elig) < 2:
        ctx.linha('H9', 'Classe processual', f'{fi(len(elig))} classes com ≥3 audiências de classe única', 'Kruskal–Wallis com permutação entre audiências', situacao='Inviável: menos de 2 classes com ≥3 audiências de classe única')
        return
    obs, p, nn = calc(m, P['n_permutacoes'], ctx.rng('H9'))
    medias = t[t.classe_unica.isin(elig)].groupby('classe_unica').taxa.agg(['mean', 'size'])
    ctx.linha('H9', f'Classe processual ({", ".join(elig)})', f'{fi(nn)} audiências de classe única; classes testadas: {", ".join(elig)}', 'H de Kruskal–Wallis sobre taxas por audiência; p por permutação dos rótulos de classe entre audiências; classes com <3 audiências ficam só descritivas',
              f'H = {fx(obs, 3)}; médias das taxas por audiência: ' + '; '.join(f'{c} {fx(v["mean"], 2)} (n={fi(v["size"])})' for c, v in medias.iterrows()), 'IC não emitido', p,
              ctx.robustez('H9', calc, m, ('sem_AP33', 'sem_maior_audiência'), loo=False), 'p pequeno: taxas de audiência diferem entre as classes testadas',
              'Classe e tema confundidos; audiências com várias classes excluídas do teste; classes raras ficam sem teste; observacional.', est=obs)


def h10(ctx):
    """DESCRITIVO: Gini, top-k e n efetivo de menções e de argumentos com denominadores. Sem valor-p."""
    m = ctx.m
    out = []
    for nome, col, d in (('audiência', 'audiencia', m), ('documento', 'documento', m), ('ministro (autoria plena)', 'ministro', m[m.autoria_plena == 1])):
        g = d.groupby(col)['arg'].agg(['size', 'sum'])
        tot, a = g['size'].to_numpy(float), g['sum'].to_numpy(float)
        top = lambda x, k: float(np.sort(x)[::-1][:k].sum() / x.sum())
        ent = lambda x: float(np.exp(-(x / x.sum() * np.log(np.where(x > 0, x / x.sum(), 1))).sum()))
        gm, ga = E.gini(tot), E.gini(a)
        out.append({'unidade': nome, 'n_unidades': len(tot), 'n_mencoes': int(tot.sum()), 'n_argumentos': int(a.sum()), 'gini_mencoes': gm, 'gini_argumentos': ga, 'diferenca_gini': ga - gm,
                    'top1_mencoes': top(tot, 1), 'top1_argumentos': top(a, 1), 'top3_mencoes': top(tot, 3), 'top3_argumentos': top(a, 3), 'n_efetivo_mencoes': ent(tot), 'n_efetivo_argumentos': ent(a)})
        ctx.linha('H10', f'Concentração de argumentos por {nome} (descritiva)', f'{fi(len(tot))} unidades; {fi(tot.sum())} menções; {fi(a.sum())} argumentos',
                  'Gini, participação dos maiores (top-1/top-3) e número efetivo (exp. da entropia) de argumentos vs. menções. SEM valor-p: permutar Argumento entre menções trataria menções como réplicas independentes.',
                  f'Gini argumentos {fx(ga, 3)} vs menções {fx(gm, 3)}; top-3 argumentos {fx(100 * top(a, 3), 1)}% vs menções {fx(100 * top(tot, 3), 1)}%; n efetivo argumentos {fx(ent(a), 1)} vs menções {fx(ent(tot), 1)}',
                  'não emitida (descrição)', np.nan, 'T_H10_concentracao.csv', '', 'Reflete extensão e cobertura documental, não escolhas individuais; unidades com zero menções não observadas; ministro tem atribuição por metadado em parte das menções.',
                  situacao='Descritivo (concentração observada; sem valor-p)', est=ga - gm)
    ctx.tab('H10_concentracao', pd.DataFrame(out))
    ctx.extra['lorenz'] = True


def h18(ctx):
    m = ctx.m
    c = pd.crosstab(m['audiencia'], m['tipo'])[['Contexto', 'Relato', 'Argumento']]
    prop = c.div(c.sum(axis=1), axis=0)
    ctx.tab('H18_composicao_por_audiencia', prop.assign(n=c.sum(axis=1)).reset_index())
    cl = np.log((c + 0.5).div((c + 0.5).sum(axis=1), axis=0))
    clr = cl.sub(cl.mean(axis=1), axis=0).to_numpy()
    u, s, vt = np.linalg.svd(clr - clr.mean(0), full_matrices=False)
    var = s ** 2 / (s ** 2).sum()
    scores = (u * s)[:, :2]
    ctx.tab('H18_pca_clr', pd.DataFrame({'audiencia': c.index, 'PC1': scores[:, 0], 'PC2': scores[:, 1], 'n': c.sum(axis=1).values}))
    lk = linkage(clr, 'ward')
    base = {k: fcluster(lk, k, 'maxclust') for k in (2, 3, 4)}
    rng = ctx.rng('H18')
    est = {}
    for k, lab in base.items():
        aris = []
        for _ in range(500):
            cb = np.vstack([rng.multinomial(int(c.loc[a].sum()), c.loc[a].to_numpy() / c.loc[a].sum()) for a in c.index])
            clb = np.log((cb + 0.5) / (cb + 0.5).sum(1, keepdims=True))
            clb = clb - clb.mean(1, keepdims=True)
            aris.append(E.ari(lab, fcluster(linkage(clb, 'ward'), k, 'maxclust')))
        est[k] = (float(np.median(aris)), float(np.quantile(aris, .1)))
    ctx.tab('H18_estabilidade_clusters', pd.DataFrame([{'k': k, 'ARI_mediana': v[0], 'ARI_p10': v[1], 'tamanhos': json.dumps(np.bincount(base[k])[1:].tolist())} for k, v in est.items()]))
    ctx.extra['h18_clusters'] = {k: base[k].tolist() for k in base}
    best = max(est, key=lambda k: est[k][0])
    ARI_MIN = 0.8
    estavel = est[best][0] >= ARI_MIN
    ctx.linha('H18', 'Perfis de composição por audiência (PCA CLR; agrupamento hierárquico de Ward)', f'{fi(len(c))} audiências', 'Composição Contexto/Relato/Argumento por audiência (soma 1); PCA de log-razões centradas; Ward com k=2–4; estabilidade por reamostragem multinomial das menções DENTRO de cada audiência (500 réplicas; ARI) — medida descritiva otimista que supõe menções independentes dentro da audiência',
              f'PC1 explica {fx(100 * var[0], 1)}% da variação da composição (3 partes têm só 2 dimensões); ARI mediana: ' + '; '.join(f'k={fi(k)}: {fx(v[0], 2)}' for k, v in est.items()), 'sem p-valor (exploratório)', np.nan,
              f'ARI por k na tabela H18_estabilidade_clusters; critério de perfil estável: ARI mediana ≥{fx(ARI_MIN, 1)}' + ('' if estavel else ' (nenhum k atingiu o critério: não se declara perfil)'), '',
              situacao='Exploratório descritivo (sem inferência)', limitacoes='Perfis não são classes preexistentes; tamanhos muito desiguais; a reamostragem multinomial só capta variação de amostragem das menções (supondo independência), não erro de classificação, cobertura ou viés; dependência documental ignorada.')


# ----------------------------------------------------------------------------- H19–H22 (A ou A+B)
def h19_h22(ctx):
    m, P, cats = ctx.m, ctx.P, ctx.cats
    cl = m[m.estado_ator == 'classificado'].copy()
    disp = lambda k: ctx.cfg['alias_exibicao'].get(k, k)
    nivel = 'A+B' if ctx.sens else 'A'
    nome_nivel = ('Sensibilidade A+B (vínculo institucional via entidade, proxy)' if ctx.sens else 'Nível A (pessoa nomeada por audiência e nome)')
    min3, min_alt = P['min_mencoes_por_grupo_na_audiencia'], P['min_mencoes_sens_elegibilidade']
    desc = []
    for k, col in cats.items():
        s, o = cl[cl[col]], cl[~cl[col]]
        desc.append({'categoria': k, 'rotulo_exibicao': disp(k), 'n_mencoes_com': len(s), 'n_argumentos_com': int(s.arg.sum()), 'taxa_com': s.arg.mean() if len(s) else np.nan,
                     'n_mencoes_sem': len(o), 'n_argumentos_sem': int(o.arg.sum()), 'taxa_sem': o.arg.mean() if len(o) else np.nan, 'n_audiencias_com': s.audiencia.nunique(),
                     'n_mencoes_unica_categoria': int((s.n_categorias == 1).sum()), 'denominador_vinculadas': len(cl)})
    ctx.tab('H19_descritivo_categorias', pd.DataFrame(desc))
    lim = (f'{nome_nivel}; multirrótulo: categorias sobrepõem-se; rótulos finais do XLSX; sem universo de participantes: sem afirmar favorecimento/exclusão/representatividade; '
           'presença do nome na menção não prova que a contribuição foi aproveitada; ' + ('categoria institucional é proxy (categoria da participação de pessoas afiliadas à entidade) — sensibilidade, não análise principal.' if ctx.sens else 'vínculo institucional (B) só aparece na sensibilidade A+B.'))
    for k, col in cats.items():
        sub = cl.copy()
        sub['flag'] = sub[col].astype(int)
        if sub['flag'].sum() == 0:
            ctx.linha('H19', f'Categoria {disp(k)}: presente − ausente', '0 menções vinculadas com a categoria', 'Contraste por audiência', situacao=f'Inviável: nenhuma menção vinculada com a categoria ({nivel})', limitacoes=lim)
            continue
        kw = dict(sentido=f'positivo: taxa argumentativa maior nas menções vinculadas à categoria {disp(k)} do que nas vinculadas a outras categorias, na mesma audiência', lim=lim,
                  usar=('sem_AP33', 'sem_maior_audiência', 'autoria_plena_sem_atribuição_por_metadado'), pergunta=ctx.cfg['hipoteses']['H19']['Pergunta'])
        teste_contraste(ctx, 'H19', f'Categoria {disp(k)}: presente − ausente (taxa argumentativa)', sub, 'flag', 1, 0, 'arg', f'H19|{k}', min_n=min3, **kw)
        # sensibilidade EXPLORATÓRIA de elegibilidade (≥2 por grupo), executada para TODAS as categorias com menções (sem seleção por significância)
        kw2 = dict(kw, lim=lim + ' SENSIBILIDADE EXPLORATÓRIA DE ELEGIBILIDADE (≥2 menções por grupo): não é confirmação nem substitui o critério predefinido.')
        teste_contraste(ctx, 'H19', f'Categoria {disp(k)}: presente − ausente [sensibilidade exploratória de elegibilidade: ≥{fi(min_alt)} por grupo]', sub, 'flag', 1, 0, 'arg', f'H19|{k}|elegib{min_alt}', min_n=min_alt,
                        familia=('F_sensAB_elegibilidade' if ctx.sens else 'F_sens_elegibilidade'), situacao_ok='Exploratório: sensibilidade de elegibilidade (não confirmação)', rotulo_extra=f'elegib{min_alt}', **kw2)
    # H20: incidência por eixo (AP é a unidade)
    est = m.groupby(['eixo_curto', 'estado_ator']).size().unstack(fill_value=0)
    est['n_total'] = est.sum(axis=1)
    ctx.tab('H20_estados_por_eixo', est.reset_index())
    inc, frac = [], []
    for e, d in cl.groupby('eixo_curto'):
        for k, col in cats.items():
            inc.append({'eixo': e, 'categoria': k, 'n_com_categoria': int(d[col].sum()), 'denominador_mencoes_classificadas': len(d), 'incidencia': d[col].mean(), 'denominador_total_mencoes_eixo': int((m.eixo_curto == e).sum())})
            frac.append({'eixo': e, 'categoria': k, 'composicao_fracionaria': float((d[col] / d['n_categorias']).sum() / len(d)), 'denominador': len(d)})
    ctx.tab('H20_incidencia_por_eixo', pd.DataFrame(inc))
    ctx.tab('H20_composicao_fracionaria_por_eixo', pd.DataFrame(frac))

    def inc_aud(dd, col):
        g = dd[dd.estado_ator == 'classificado'].groupby('audiencia').agg(n=(col, 'size'), v=(col, 'mean'), eixo=('eixo', 'first'))
        return g[g.n >= P['min_mencoes_classificadas_audiencia']].reset_index()
    for k, col in cats.items():
        def calc(dd, B, rng, col=col):
            g = inc_aud(dd, col)
            r = E.diff_grupos_ap(g['v'], (g.eixo == EIXO_A).astype(int), B, rng)
            return r[0], r[1], len(g)
        g = inc_aud(m, col)
        nA, nB = int((g.eixo == EIXO_A).sum()), int((g.eixo != EIXO_A).sum())
        metodo = (f'Diferença (ambiental − personalidade) das médias de incidência da categoria entre menções classificadas, por audiência (≥{fi(P["min_mencoes_classificadas_audiencia"])} classificadas); '
                  'p por permutação do eixo entre audiências; IC por bootstrap de audiências')
        total = int(cl[col].sum())
        ctx.tab(f'H20_incidencia_por_audiencia_{slug(k)}', g)
        if total == 0 or min(nA, nB) < P['min_audiencias_teste']:
            ctx.linha('H20', f'Incidência de {disp(k)}: ambiental − personalidade', f'{fi(nA)}+{fi(nB)} audiências elegíveis; {fi(total)} menções com a categoria', metodo, situacao=f'Inviável: audiências elegíveis por eixo {fi(nA)}/{fi(nB)} (mínimo {fi(P["min_audiencias_teste"])}) e {fi(total)} menções com a categoria', limitacoes='Incidência entre classificadas é prevalência sobreposta (não soma 100%).')
            continue
        e_, p, ci = E.diff_grupos_ap(g['v'], (g.eixo == EIXO_A).astype(int), P['n_permutacoes'], ctx.rng(f'H20|{k}'), P['n_bootstrap'] if min(nA, nB) >= P['min_audiencias_ci'] else 0, rng_ci=ctx.rng(f'H20|{k}|boot'))
        pooled = {e: d[col].mean() for e, d in cl.groupby('eixo_curto')}
        ctx.linha('H20', f'Incidência de {disp(k)}: ambiental − personalidade', f'{fi(nA)}+{fi(nB)} audiências elegíveis; {fi(g.n.sum())} menções classificadas', metodo, f'Δ incidência = {fx(e_, 3, True)}', _ic_txt(*ci, f'{fi(nA)}+{fi(nB)}', P['min_audiencias_ci']), p,
                  ctx.robustez(f'H20|{k}', calc, m, ('sem_AP33', 'sem_maior_audiência'), extra=['incidência agregada por menção (estimando distinto): ' + '; '.join(f'{e} {fx(v, 3)}' for e, v in pooled.items())]),
                  f'positivo: maior incidência de {disp(k)} entre menções classificadas no eixo ambiental/mercado',
                  f'{nome_nivel}; incidência sobreposta (multirrótulo), não composição partitiva; cobertura de classificação difere entre eixos; observacional.', est=e_, lo=ci[0], hi=ci[1])
    # H21: tabela ministro × categoria COM aproveitamento argumentativo; sem modelo/valor-p
    rows, long = [], []
    for mi, g in cl.groupby('ministro'):
        r = {'ministro': mi, 'n_mencoes_classificadas': len(g), 'n_argumentos_classificadas': int(g.arg.sum()), 'taxa_arg_classificadas': g.arg.mean(), 'n_audiencias': g.audiencia.nunique(), 'n_documentos': g.documento.nunique(),
             'autoria_plena': int(g.autoria_plena.max()), 'n_atribuicao_metadado': int(g.atribuicao_metadado.sum())}
        r.update({k: int(g[c].sum()) for k, c in cats.items()})
        rows.append(r)
        for k, c in cats.items():
            s = g[g[c]]
            long.append({'ministro': mi, 'categoria': k, 'n_mencoes_com_categoria': len(s), 'n_argumento': int(s.arg.sum()), 'taxa_argumento': (s.arg.mean() if len(s) else np.nan),
                         'n_audiencias': s.audiencia.nunique(), 'n_atribuicao_metadado': int(s.atribuicao_metadado.sum()), 'autoria_plena': int(g.autoria_plena.max())})
    tab21 = pd.DataFrame(rows).sort_values('n_mencoes_classificadas', ascending=False)
    long21 = pd.DataFrame(long)
    ctx.tab('H21_ministro_x_categoria', tab21)
    ctx.tab('H21_ministro_x_categoria_aproveitamento', long21)
    ok = tab21[(tab21.autoria_plena == 1) & (tab21.n_mencoes_classificadas >= P['min_mencoes_ministro']) & (tab21.n_audiencias >= P['min_audiencias_ministro'])].ministro.tolist()
    lg = long21[long21.ministro.isin(ok)]
    cel5 = lg[lg.n_mencoes_com_categoria >= 5]
    n_min_2cat = int((cel5.groupby('ministro').size() >= 2).sum())
    n_meta = int(cl['atribuicao_metadado'].sum())
    viavel = n_min_2cat >= 4
    base_txt = (f'{fi(len(ok))} ministros com suporte (≥{fi(P["min_mencoes_ministro"])} classificadas, ≥{fi(P["min_audiencias_ministro"])} audiências, autoria plena); células ministro×categoria com ≥5 menções: {fi(len(cel5))}; '
                f'ministros com ≥2 categorias com ≥5 menções: {fi(n_min_2cat)}; {fi(n_meta)} das {fi(len(cl))} menções classificadas têm ministro atribuído por metadado')
    for k, col in cats.items():
        s = long21[long21.categoria == k]
        s5 = s[s.n_mencoes_com_categoria >= 5]
        tot_n, tot_k = int(s.n_mencoes_com_categoria.sum()), int(s.n_argumento.sum())
        ctx.linha('H21', f'Ministro × {disp(k)}: aproveitamento argumentativo (n Argumento / n menções com a categoria)', f'{fi(tot_n)} menções classificadas com a categoria; {fi(len(s5))} ministros com ≥5 menções nela',
                  'Tabela por ministro e categoria com nArgumento, nMenções e taxa; SEM valor-p e sem modelo (ver linha de viabilidade do modelo)',
                  (f'agregado por menção: {fi(tot_k)}/{fi(tot_n)} = {fx(tot_k / tot_n, 3)}; entre ministros com ≥5 menções: taxas {fx(s5.taxa_argumento.min(), 2)}–{fx(s5.taxa_argumento.max(), 2)}' if len(s5) else f'agregado por menção: {fi(tot_k)}/{fi(tot_n)}' + (f' = {fx(tot_k / tot_n, 3)}' if tot_n else '') + '; nenhum ministro com ≥5 menções'),
                  'não emitida (descrição)', np.nan, 'T_H21_ministro_x_categoria_aproveitamento.csv', '',
                  f'Não interpretar como preferência individual: {fi(n_meta)} menções classificadas têm ministro atribuído por metadado (relator), não por fala; menções repetidas no mesmo documento; células escassas; sem universo de votos.',
                  situacao='Descritivo (sem valor-p; não é preferência individual)' if tot_n else f'Inviável: nenhuma menção vinculada com a categoria ({nivel})')
    ctx.linha('H21', 'Modelo ministro × categoria no aproveitamento argumentativo (viabilidade)', f'{base_txt}',
              'Modelo hierárquico (Argumento ~ ministro × categoria, efeitos de audiência/documento) ou teste com menções como réplicas: NÃO executado',
              'modelo não estimado', 'não emitida', situacao=('Inviável: ' if not viavel else 'Descritivo: modelo não executado — ') + f'suporte insuficiente para interação ministro × categoria (critério: ≥4 ministros com ≥2 categorias com ≥5 menções; observado {fi(n_min_2cat)}); atribuição por metadado e dependência dentro de documento/audiência impedem inferência individual',
              limitacoes='Ver tabelas T_H21_*. Sem valor-p artificial.')
    ctx.extra['h21_suporte' + ('_AB' if ctx.sens else '')] = {'ministros_com_suporte': len(ok), 'celulas_ge5': len(cel5), 'ministros_2cat_ge5': n_min_2cat}
    # H22: duas dimensões — (a) composição de categorias; (b) aproveitamento argumentativo por categoria — ambas por ano
    t = cl.groupby('audiencia').agg(n=('arg', 'size'), taxa_arg_classificadas=('arg', 'mean'), ano_julgamento=('ano_julgamento', 'min'), eixo=('eixo', 'first'), **{c: (c, 'mean') for c in cats.values()}).reset_index()
    ctx.tab('H22_audiencias_classificadas', t)
    ano = cl.groupby('ano_julgamento').agg(n_audiencias=('audiencia', 'nunique'), n_classificadas=('arg', 'size'), n_argumentos=('arg', 'sum'), **{c: (c, 'sum') for c in cats.values()}).reset_index()
    ano['taxa_arg_classificadas'] = ano['n_argumentos'] / ano['n_classificadas']
    ctx.tab('H22_por_ano', ano)
    serie = []
    for k, col in cats.items():
        for y_, d in cl.groupby('ano_julgamento'):
            s = d[d[col]]
            serie.append({'ano_julgamento': y_, 'categoria': k, 'n_classificadas_ano': len(d), 'n_com_categoria': len(s), 'incidencia': len(s) / len(d), 'n_argumento_com_categoria': int(s.arg.sum()),
                          'taxa_argumento_com_categoria': (s.arg.mean() if len(s) else np.nan), 'n_audiencias_com_categoria': s.audiencia.nunique()})
    ctx.tab('H22_serie_categoria_ano', pd.DataFrame(serie))
    apcat = []
    for k, col in cats.items():
        for au, d in cl[cl[col]].groupby('audiencia'):
            apcat.append({'categoria': k, 'audiencia': au, 'ano_julgamento': int(d.ano_julgamento.min()), 'n_com_categoria': len(d), 'n_argumento': int(d.arg.sum()), 'taxa_argumento': d.arg.mean()})
    apcat = pd.DataFrame(apcat, columns=['categoria', 'audiencia', 'ano_julgamento', 'n_com_categoria', 'n_argumento', 'taxa_argumento'])
    ctx.tab('H22_ap_taxa_argumento_por_categoria', apcat)
    lim22 = f'{nome_nivel}; poucas audiências elegíveis e poucos anos; tema confundido com calendário; incidência sobreposta; observacional.'
    min_c = P['min_mencoes_classificadas_audiencia']
    alvos = [('composição', 'taxa argumentativa entre classificadas', 'taxa_arg_classificadas')] + [('composição', f'incidência de {disp(k)}', c) for k, c in cats.items()]
    for dim, nome, col in alvos:
        def tabf(dd, col=col):
            c2 = dd[dd.estado_ator == 'classificado']
            g = c2.groupby('audiencia').agg(n=('arg', 'size'), y=(col if col != 'taxa_arg_classificadas' else 'arg', 'mean'), ano_julgamento=('ano_julgamento', 'min'))
            return g[g.n >= min_c].reset_index()
        _h22_spearman(ctx, f'Ano do julgamento × {nome}', nome, tabf, f'H22|{col}', cl, col if col != 'taxa_arg_classificadas' else None, min_c, lim22, nivel)
    # (b) aproveitamento argumentativo por categoria × ano (Argumento entre menções COM a categoria, por audiência)
    mc = P['min_mencoes_por_grupo_na_audiencia']
    for k, col in cats.items():
        def tabf(dd, col=col):
            c2 = dd[(dd.estado_ator == 'classificado') & dd[col]]
            g = c2.groupby('audiencia').agg(n=('arg', 'size'), y=('arg', 'mean'), ano_julgamento=('ano_julgamento', 'min'))
            return g[g.n >= mc].reset_index()
        _h22_spearman(ctx, f'Ano do julgamento × taxa argumentativa das menções com {disp(k)} (≥{fi(mc)} por audiência)', f'taxa argumentativa em {disp(k)}', tabf, f'H22|arg|{col}', cl, col, mc, lim22 + ' Aproveitamento argumentativo por categoria.', nivel)


def _h22_spearman(ctx, teste, nome, tabf, tag, cl, col, min_c, lim, nivel):
    P, m = ctx.P, ctx.m

    def calc(dd, B, rng):
        g = tabf(dd)
        r, p, _ = E.spearman_ap(g['ano_julgamento'], g['y'], B, rng)
        return r, p, len(g)
    if col is not None and cl[col].sum() == 0:
        ctx.linha('H22', teste, '0 menções com a categoria', 'Spearman por audiência', situacao=f'Inviável: nenhuma menção vinculada com a categoria ({nivel})')
        return
    g = tabf(m)
    n, ny = len(g), g.ano_julgamento.nunique()
    metodo = f'Spearman entre ano do julgamento e {nome} por audiência; p por permutação entre audiências; IC bootstrap de audiências se ≥{fi(P["min_audiencias_ci"])}'
    if n < P['min_audiencias_teste'] or ny < 4:
        ctx.linha('H22', teste, f'{fi(n)} audiências; {fi(ny)} anos', metodo, f'descrição: ver T_H22_serie_categoria_ano.csv e T_H22_ap_taxa_argumento_por_categoria.csv',
                  situacao=f'Inviável/descritivo: {fi(n)} audiências elegíveis e {fi(ny)} anos (mínimo {fi(P["min_audiencias_teste"])} e 4); série por ano em tabela', limitacoes=lim)
        return
    r, p, ci = E.spearman_ap(g['ano_julgamento'], g['y'], P['n_permutacoes'], ctx.rng(tag), P['n_bootstrap'] if n >= P['min_audiencias_ci'] else 0, rng_ci=ctx.rng(tag + '|boot'))
    ctx.linha('H22', teste, f'{fi(n)} audiências; {fi(g.n.sum())} menções; {fi(ny)} anos', metodo, f'ρ = {fx(r, 3, True)}', _ic_txt(*ci, n, P['min_audiencias_ci']), p,
              ctx.robustez(tag, calc, m, ('sem_AP33', 'sem_maior_audiência')), f'ρ>0: {nome} cresce com o ano do julgamento', lim, est=r, lo=ci[0], hi=ci[1])


def interpretar(df: pd.DataFrame, alfa: float) -> pd.DataFrame:
    df = df.copy()
    txt = []
    for r in df.itertuples():
        s = r.Situacao
        if np.isfinite(r.valor_p):
            q = r.valor_p_BH
            base = (r._asdict().get('_sentido') or '').strip()
            expl = ' (sensibilidade exploratória; não confirmatório)' if s.startswith('Exploratório: sensibilidade') else ''
            if q < alfa:
                f = f'valor-p {fx(r.valor_p, 4)}; BH {fx(q, 4)} < {fx(alfa, 2)}: compatível com associação exploratória nesta amostra de audiências observadas{expl}'
            else:
                f = f'valor-p {fx(r.valor_p, 4)}; BH {fx(q, 4)} ≥ {fx(alfa, 2)}: sem evidência suficiente de associação; isso não prova ausência de efeito{expl}'
            txt.append((base + '. ' if base else '') + f + '. Associação observacional, não causal, sem representatividade populacional.')
        elif s.startswith('Inviável'):
            txt.append('Teste não realizado por suporte insuficiente; nenhum valor-p calculado. ' + s.split(': ', 1)[-1])
        else:
            txt.append('Descrição/exploração sem teste inferencial; não interpretar como associação.')
    df['Interpretacao'] = txt
    return df


def executar(ctx: Ctx) -> pd.DataFrame:
    for f in (h1_h2, h16_h13, h3, h4, h5_h6, h7_h14, h8_h15_h17_h11_h12, h9, h10, h18, h19_h22):
        f(ctx)
    return pd.DataFrame(ctx.rows)


def finalizar(frames: list[pd.DataFrame], alfa: float) -> pd.DataFrame:
    df = pd.concat(frames, ignore_index=True)
    df = E.bh(df)
    df = interpretar(df, alfa)
    df['_ord'] = df['Hipotese'].str[1:].astype(int)
    df['_sens'] = (df['Analise'] != 'Principal (A)').astype(int)
    df = df.sort_values(['_ord', '_sens'], kind='stable').drop(columns=['_ord', '_sens']).reset_index(drop=True)
    return df
