#!/usr/bin/env python
"""Pipeline completo H1–H22 (sem API, sem rede).
Uso: .venv/bin/python run_all.py                # rodada FINAL (escreve em data/, results/, reports/)
     .venv/bin/python run_all.py --quick        # rodada RÁPIDA (escreve em quick_runs/, nunca em results/)
Ordem: hash das fontes (antes) → integração → validações críticas (interrompem) → análises → hash (depois, deve ser idêntico)."""
from __future__ import annotations

import argparse
import importlib.metadata as im
import json
import platform
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / 'src'))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import figuras, hipoteses, integracao, limpeza, relatorio, validacao  # noqa: E402
from auditar_base import sha  # noqa: E402

CMD = '.venv/bin/python run_all.py'


def _sens_frame(d: dict) -> pd.DataFrame:
    m, ab = d['mencoes'], d['mencoes_AB']
    drop = ['estado_ator', 'n_atores_A', 'n_categorias', 'multirrotulo', 'categorias', 'mista_classificado_e_nao_resolvido'] + [c for c in m.columns if c.startswith('cat_')]
    return m.drop(columns=drop).merge(ab, on='id', validate='1:1')


def executar(saida: Path, quick=False, seed=None, perms=None, boot=None, figs=True, escrever_relatorio=True) -> dict:
    saida = Path(saida).resolve()
    if quick and saida == AQUI:
        raise SystemExit('rodada rápida não pode escrever nos diretórios finais; use outro destino')
    cfg = json.loads((AQUI / 'config/analise_H1_H22.json').read_text(encoding='utf-8'))
    modo = 'rapida_NAO_FINAL' if quick else 'final'
    if quick:
        cfg['parametros'].update(n_permutacoes=499, n_bootstrap=300)
    if seed is not None:
        cfg['parametros']['seed'] = seed
    if perms:
        cfg['parametros']['n_permutacoes'] = perms
    if boot:
        cfg['parametros']['n_bootstrap'] = boot
    t0 = time.time()
    hipoteses.NUMS.clear()
    antes = integracao.hashes_entradas()
    decisao = validacao.decisao_vinculo()
    d = integracao.carregar(cfg)
    check = validacao.validar_integridade(d, cfg)          # levanta ValidacaoErro: nada é produzido se falhar
    proc, res, fig = saida / 'data/processed', saida / 'results/h1_h22', saida / 'results/figures'
    for p in (proc, res, fig, saida / 'reports'):
        p.mkdir(parents=True, exist_ok=True)
    csv = lambda df, p: df.to_csv(p, index=False, encoding='utf-8-sig')
    csv(d['mencoes'], proc / 'mencoes_principal_atores.csv')
    csv(d['mencoes_AB'], proc / 'mencoes_sensibilidade_AB.csv')
    csv(d['atores'], proc / 'atores_classificados.csv')
    csv(d['ponte'], proc / 'ponte_mencao_ator.csv')
    csv(d['ponte_B'], proc / 'ponte_B_candidatos_proveniencia.csv')
    csv(d['entidades_B'], proc / 'entidades_B.csv')
    csv(d['diag_B'], proc / 'diagnostico_B_por_mencao.csv')
    (res / 'validacao_integracao.json').write_text(json.dumps({'contagens_e_verificacoes': check, 'integracao': d['validacao']}, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    ctx = hipoteses.Ctx(cfg, d['mencoes'], d['atores'], saida, 'A')
    hipoteses.executar(ctx)
    ctx_ab = hipoteses.Ctx(cfg, _sens_frame(d), d['atores'], saida, 'A+B')
    hipoteses.h19_h22(ctx_ab)
    mat = hipoteses.finalizar([pd.DataFrame(ctx.rows), pd.DataFrame(ctx_ab.rows)], cfg['parametros']['alfa_bh'])
    pub = relatorio.matriz_publica(mat)
    csv(pub, res / 'matriz_resultados_H1_H22.csv')
    csv(relatorio.resumo_hipoteses(mat, cfg), res / 'resumo_por_hipotese.csv')
    for nome, df in {**ctx.tabs, **ctx_ab.tabs}.items():
        csv(df, res / f'T_{hipoteses.slug(nome)}.csv')
    (res / 'matriz_resultados_H1_H22.json').write_text(json.dumps({'modo': modo, 'parametros': cfg['parametros'], 'resultados': json.loads(pub.to_json(orient='records', force_ascii=False))}, ensure_ascii=False, indent=2), encoding='utf-8')
    figs_out = figuras.gerar(ctx, mat, fig, ctx_ab) if figs else []
    if figs:
        csv(pd.DataFrame(figs_out), fig / 'figuras_indice.csv')
    cmd = CMD + (' --quick' if quick else '')
    if escrever_relatorio:
        md = saida / 'reports/relatorio_consolidado_H1_H22.md'
        relatorio.escrever(ctx, ctx_ab, mat, d['validacao'], check, figs_out, md, cmd, modo, decisao, AQUI)
        if figs:
            relatorio.escrever_html(md, saida / 'reports/relatorio_consolidado_H1_H22.html', fig)
        (res / 'numeros_relatorio.json').write_text(json.dumps(sorted(hipoteses.NUMS), ensure_ascii=False), encoding='utf-8')
    # registro de saídas ATUAIS (única fonte para limpeza e manifesto)
    atuais = {f'data/processed/{n}' for n in ('mencoes_principal_atores.csv', 'mencoes_sensibilidade_AB.csv', 'atores_classificados.csv', 'ponte_mencao_ator.csv', 'ponte_B_candidatos_proveniencia.csv', 'entidades_B.csv', 'diagnostico_B_por_mencao.csv')}
    atuais |= {f'results/h1_h22/{n}' for n in ('validacao_integracao.json', 'matriz_resultados_H1_H22.csv', 'matriz_resultados_H1_H22.json', 'resumo_por_hipotese.csv')}
    atuais |= {f'results/h1_h22/T_{hipoteses.slug(n)}.csv' for n in {**ctx.tabs, **ctx_ab.tabs}}
    if escrever_relatorio:
        atuais |= {'results/h1_h22/numeros_relatorio.json', 'reports/relatorio_consolidado_H1_H22.md'} | ({'reports/relatorio_consolidado_H1_H22.html'} if figs else set())
    if figs:
        atuais |= {'results/figures/figuras_indice.csv'} | {f'results/figures/{f[k]}' for f in figs_out for k in ('arquivo_png', 'arquivo_svg', 'dados')}
    arquivados = limpeza.arquivar_obsoletos(saida, atuais) if (figs and escrever_relatorio) else []
    depois = integracao.hashes_entradas()
    if antes != depois:
        raise validacao.ValidacaoErro('fontes de entrada foram modificadas durante a execução')
    pacotes = {p: im.version(p) for p in ('pandas', 'numpy', 'scipy', 'statsmodels', 'matplotlib', 'openpyxl', 'markdown')}
    cfg_dec = AQUI / 'config/decisao_vinculo_institucional.json'
    # saídas = registro atual (cópias/legados arquivados ficam de fora); documentação = demais arquivos de reports/ (revisão, plano, diagnóstico)
    docs = {str(p.relative_to(saida)) for p in (saida / 'reports').iterdir() if p.is_file() and not p.name.startswith('.') and not re.search(r' 2(\.[^.]+)?$', p.name)}
    saidas = {r: sha(saida / r) for r in sorted(atuais | docs) if (saida / r).is_file()}
    fase1 = {str(p.relative_to(saida)): sha(p) for p in sorted(proc.iterdir()) if p.is_file() and str(p.relative_to(saida)) not in atuais and not re.search(r' 2(\.[^.]+)?$', p.name)}
    man = {'modo': modo, 'executado_em_utc': datetime.now(timezone.utc).isoformat(), 'duracao_s': round(time.time() - t0, 1), 'python': sys.version, 'plataforma': platform.platform(),
           'pacotes': pacotes, 'seed_global': cfg['parametros']['seed'], 'seeds_por_analise': {**ctx.seeds, **ctx_ab.seeds}, 'parametros': cfg['parametros'], 'comando': cmd, 'chamadas_api': 0,
           'entradas_antes': antes, 'entradas_depois': depois, 'entradas_inalteradas': antes == depois,
           'decisao_vinculo_institucional': {'arquivo': 'config/decisao_vinculo_institucional.json', 'sha256': sha(cfg_dec), 'conteudo': decisao,
                                              'escolha_efetiva': 'analise principal = A; B somente em sensibilidade A+B'},
           'scripts': {str(p.relative_to(AQUI)): sha(p) for p in sorted([AQUI / 'run_all.py', *(AQUI / 'src').glob('*.py')])},
           'configuracao': {'config/analise_H1_H22.json': sha(AQUI / 'config/analise_H1_H22.json'), 'config/decisao_vinculo_institucional.json': sha(cfg_dec)},
           'validacoes_criticas': check, 'arquivados_nesta_execucao': arquivados, 'derivados_fase1_preservados_fora_das_saidas': fase1, 'requirements_lock_sha256': sha(AQUI / 'requirements.lock') if (AQUI / 'requirements.lock').exists() else None, 'saidas': saidas}
    (saida / 'results/manifesto_execucao.json').write_text(json.dumps(man, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    return {'mat': mat, 'ctx': ctx, 'ctx_ab': ctx_ab, 'validacao': d['validacao'], 'check': check, 'manifesto': man}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--saida', type=Path)
    ap.add_argument('--quick', action='store_true', help='499 permutações / 300 bootstraps; saída separada em quick_runs/ (NÃO é resultado final)')
    ap.add_argument('--seed', type=int)
    ap.add_argument('--sem-figuras', action='store_true')
    a = ap.parse_args()
    destino = a.saida or (AQUI / 'quick_runs' if a.quick else AQUI)
    r = executar(destino, a.quick, a.seed, figs=not a.sem_figuras)
    m = r['mat']
    print(f'ok ({r["manifesto"]["modo"]}): {len(m)} linhas; {int(m.valor_p.notna().sum())} com valor-p; {int(m.Situacao.str.startswith("Inviável").sum())} inviáveis; {r["manifesto"]["duracao_s"]}s')
