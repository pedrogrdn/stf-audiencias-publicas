import json
import shutil
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI / 'src'))
sys.path.insert(0, str(AQUI))


@pytest.fixture(scope='session')
def cfg():
    return json.loads((AQUI / 'config/analise_H1_H22.json').read_text(encoding='utf-8'))


@pytest.fixture(scope='session')
def dados(cfg):
    import integracao
    return integracao.carregar(cfg)


@pytest.fixture(scope='session')
def execucoes():
    import run_all
    import integracao
    base = AQUI / '.scratch'
    shutil.rmtree(base, ignore_errors=True)
    antes = integracao.hashes_entradas()
    r1 = run_all.executar(base / 'a', quick=True, figs=False)
    r2 = run_all.executar(base / 'b', quick=True, figs=False)
    r3 = run_all.executar(base / 'c', quick=True, seed=7, figs=False)
    depois = integracao.hashes_entradas()
    yield {'a': (base / 'a', r1), 'b': (base / 'b', r2), 'c': (base / 'c', r3), 'antes': antes, 'depois': depois}
    shutil.rmtree(base, ignore_errors=True)
