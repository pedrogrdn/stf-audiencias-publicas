"""Primitivas estatísticas. A unidade inferencial é SEMPRE a audiência (AP); menções nunca são permutadas
nem tratadas como réplicas independentes. Seeds por análise (rótulo); p Monte Carlo com correção +1."""
from __future__ import annotations

import zlib

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import rankdata
from statsmodels.stats.multitest import multipletests

EPS = 1e-12


def rng_tag(seed: int, tag: str) -> np.random.Generator:
    """Gerador independente e estável por análise: (seed global, CRC32 do rótulo)."""
    return np.random.default_rng([seed, zlib.crc32(tag.encode('utf-8'))])


def pmc(obs: float, null, alt: str = 'two') -> float:
    """p Monte Carlo: (1 + #extremos) / (B + 1)."""
    null = np.asarray(null, dtype=float)
    if not np.isfinite(obs) or len(null) == 0:
        return float('nan')
    c = (np.abs(null) >= abs(obs) - EPS).sum() if alt == 'two' else (null >= obs - EPS).sum()
    return float((1 + c) / (len(null) + 1))


def aud_tabela(m: pd.DataFrame, y: str = 'arg') -> pd.DataFrame:
    g = m.groupby('audiencia')
    t = g.agg(n=(y, 'size'), k=(y, 'sum'), eixo=('eixo', 'first'), ano_julgamento=('ano_julgamento', 'min'),
              ano_audiencia=('ano_audiencia', 'first'), n_doc=('documento', 'nunique')).reset_index()
    t['taxa'] = t['k'] / t['n']
    t['intervalo'] = t['ano_julgamento'] - t['ano_audiencia']   # dado original; AP33 = -1 preservado
    return t


def _pearson_rows(X, y):
    Xc = X - X.mean(axis=-1, keepdims=True)
    yc = y - y.mean(axis=-1, keepdims=True)
    den = np.sqrt((Xc ** 2).sum(-1) * (yc ** 2).sum(-1))
    with np.errstate(invalid='ignore', divide='ignore'):
        return (Xc * yc).sum(-1) / den


def spearman_ap(x, y, B: int, rng, ci_B: int = 0, rng_ci=None):
    """Spearman entre duas variáveis POR AUDIÊNCIA. p: permutação de y entre audiências (trocabilidade das AP sob nula
    de ausência de associação); IC: bootstrap percentil de audiências."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    nan = float('nan')
    if n < 4 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return nan, nan, (nan, nan)
    rx, ry = rankdata(x), rankdata(y)
    obs = float(_pearson_rows(rx, ry))
    p = nan
    if B > 0:
        Y = rng.permuted(np.tile(ry, (B, 1)), axis=1)
        p = pmc(obs, _pearson_rows(rx[None, :], Y))
    ci = (nan, nan)
    if ci_B > 0:
        idx = (rng_ci or rng).integers(0, n, size=(ci_B, n))
        r = _pearson_rows(rankdata(x[idx], axis=1), rankdata(y[idx], axis=1))
        r = r[np.isfinite(r)]
        if len(r) > 100:
            ci = (float(np.quantile(r, .025)), float(np.quantile(r, .975)))
    return obs, p, ci


def diff_grupos_ap(v, lab, B: int, rng, ci_B: int = 0, rng_ci=None):
    """média(lab==1) − média(lab==0) entre AUDIÊNCIAS. p: permutação dos rótulos entre audiências; IC: bootstrap dentro do grupo."""
    v, lab = np.asarray(v, float), np.asarray(lab, int)
    a, b = v[lab == 1], v[lab == 0]
    nan = float('nan')
    if len(a) < 2 or len(b) < 2:
        return nan, nan, (nan, nan)
    obs = a.mean() - b.mean()
    p = nan
    if B > 0:
        V = rng.permuted(np.tile(v, (B, 1)), axis=1)
        na = len(a)
        p = pmc(obs, V[:, :na].mean(1) - V[:, na:].mean(1))
    ci = (nan, nan)
    if ci_B > 0:
        r2 = rng_ci or rng
        d = a[r2.integers(0, len(a), (ci_B, len(a)))].mean(1) - b[r2.integers(0, len(b), (ci_B, len(b)))].mean(1)
        ci = (float(np.quantile(d, .025)), float(np.quantile(d, .975)))
    return float(obs), p, ci


def contraste_por_audiencia(m: pd.DataFrame, grupo: str, g1, g0, y: str, min_n: int, bloco: str = 'audiencia') -> pd.DataFrame:
    """Contraste média(y|g1) − média(y|g0) calculado DENTRO de cada bloco e reduzido a UM valor por audiência.

    bloco='audiencia': o valor da audiência é a diferença direta.
    bloco='doc_aud'  : diferenças por (documento, audiência), com média simples dentro da audiência.
    Só entram blocos com >= min_n menções em cada grupo. Nenhuma menção é permutada."""
    sub = m[m[grupo].isin([g1, g0])]
    linhas = []
    for (b, aud), d in sub.groupby([bloco, 'audiencia']):
        d1, d0 = d.loc[d[grupo] == g1, y].to_numpy(float), d.loc[d[grupo] == g0, y].to_numpy(float)
        if len(d1) < min_n or len(d0) < min_n:
            continue
        linhas.append({'bloco': b, 'audiencia': int(aud), 'n_g1': len(d1), 'n_g0': len(d0), 'y_g1': d1.mean(), 'y_g0': d0.mean(), 'contraste': d1.mean() - d0.mean()})
    blocos = pd.DataFrame(linhas, columns=['bloco', 'audiencia', 'n_g1', 'n_g0', 'y_g1', 'y_g0', 'contraste'])
    if blocos.empty:
        return pd.DataFrame(columns=['audiencia', 'n_blocos', 'n_g1', 'n_g0', 'y_g1', 'y_g0', 'contraste'])
    ap = blocos.groupby('audiencia').agg(n_blocos=('bloco', 'size'), n_g1=('n_g1', 'sum'), n_g0=('n_g0', 'sum'), y_g1=('y_g1', 'mean'),
                                         y_g0=('y_g0', 'mean'), contraste=('contraste', 'mean')).reset_index()
    return ap


def sign_flip_media(d, B: int, rng, exato_ate: int = 16):
    """Teste de inversão de sinais da MÉDIA das diferenças por audiência.
    Hipótese ADICIONAL: sob a nula, a distribuição das diferenças por audiência é simétrica em torno de zero.
    Exato (2^n) para n <= exato_ate; senão Monte Carlo com +1. Retorna (média, p, descrição)."""
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    n = len(d)
    if n < 2:
        return float('nan'), float('nan'), 'n/d'
    obs = float(d.mean())
    if n <= exato_ate:
        signs = ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1) * 2 - 1
        null = signs @ d / n
        p = float((np.abs(null) >= abs(obs) - EPS).sum() / len(null))
        return obs, p, f'exato ({2 ** n} inversões)'
    if B <= 0:
        return obs, float('nan'), 'não calculado'
    S = rng.choice(np.array([-1.0, 1.0]), size=(B, n))
    return obs, pmc(obs, S @ d / n), f'Monte Carlo ({B} inversões, +1)'


def bootstrap_media(vals, B: int, rng):
    vals = np.asarray(vals, float)
    d = vals[rng.integers(0, len(vals), (B, len(vals)))].mean(1)
    return float(np.quantile(d, .025)), float(np.quantile(d, .975))


def ols_hc3(y, X):
    """OLS com erros-padrão HC3 (leverage 1 ⇒ HC3 indefinido ⇒ None). IC e p por t com n−k g.l. (aproximação com poucas unidades)."""
    y, X = np.asarray(y, float), np.asarray(X, float)
    n, k = X.shape
    rank = int(np.linalg.matrix_rank(X))
    if rank < k or n <= k:
        return {'ok': False, 'rank': rank, 'k': k, 'n': n}
    xtxi = np.linalg.inv(X.T @ X)
    b = xtxi @ X.T @ y
    e = y - X @ b
    h = np.einsum('ij,jk,ik->i', X, xtxi, X)
    if (h >= 1 - 1e-9).any():
        return {'ok': False, 'rank': rank, 'k': k, 'n': n, 'motivo': 'alavancagem 1'}
    V = xtxi @ (X.T * ((e / (1 - h)) ** 2)) @ X @ xtxi
    se = np.sqrt(np.diag(V))
    df = n - k
    t = b / se
    p = 2 * stats.t.sf(np.abs(t), df)
    q = stats.t.ppf(.975, df)
    r2 = 1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum() if np.ptp(y) > 0 else float('nan')
    return {'ok': True, 'b': b, 'se': se, 'p': p, 'lo': b - q * se, 'hi': b + q * se, 'df': df, 'rank': rank, 'k': k, 'n': n, 'r2': float(r2), 'hmax': float(h.max()), 'V': V}


def boot_interacao(y, x, g, B: int, rng):
    """Bootstrap de audiências, estratificado por eixo, do coeficiente de interação x·g (modelo y ~ 1 + x + g + x·g)."""
    y, x, g = (np.asarray(v, float) for v in (y, x, g))
    i1, i0 = np.flatnonzero(g == 1), np.flatnonzero(g == 0)
    out = []
    for _ in range(B):
        idx = np.r_[rng.choice(i1, len(i1)), rng.choice(i0, len(i0))]
        xc = x[idx] - x[idx].mean()
        X = np.column_stack([np.ones(len(idx)), xc, g[idx], xc * g[idx]])
        if np.linalg.matrix_rank(X) < 4:
            continue
        out.append(np.linalg.lstsq(X, y[idx], rcond=None)[0][3])
    out = np.array(out)
    if len(out) < 100:
        return float('nan'), float('nan'), len(out)
    return float(np.quantile(out, .025)), float(np.quantile(out, .975)), len(out)


def gini(x) -> float:
    x = np.sort(np.asarray(x, float))
    if len(x) == 0 or x.sum() == 0:
        return float('nan')
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum()))


def bh(df: pd.DataFrame, fam_col: str = 'Familia', p_col: str = 'valor_p', out: str = 'valor_p_BH') -> pd.DataFrame:
    """Benjamini–Hochberg por família sobre os testes efetivamente executados (p não-NA); NA preservado."""
    df = df.copy()
    if df[fam_col].isna().any() or (df[fam_col] == 'sem_familia').any():
        raise ValueError('teste sem família BH predeterminada')
    df[out] = np.nan
    for _, g in df.groupby(fam_col):
        ok = g[p_col].notna()
        if ok.sum():
            df.loc[g.index[ok], out] = multipletests(g.loc[ok, p_col].to_numpy(float), method='fdr_bh')[1]
    return df


def ari(a, b) -> float:
    from math import comb
    a, b = np.asarray(a), np.asarray(b)
    tab = pd.crosstab(a, b).to_numpy()
    s = sum(comb(int(v), 2) for v in tab.ravel())
    sa = sum(comb(int(v), 2) for v in tab.sum(1))
    sb = sum(comb(int(v), 2) for v in tab.sum(0))
    tot = comb(int(tab.sum()), 2)
    exp = sa * sb / tot if tot else 0
    mx = (sa + sb) / 2
    return float((s - exp) / (mx - exp)) if mx != exp else 1.0
