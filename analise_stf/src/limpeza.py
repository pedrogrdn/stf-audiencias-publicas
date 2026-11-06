"""Arquiva (move, sem apagar) saídas OBSOLETAS deste pipeline para historico/rascunhos_pre_revisao/.
Critério: registro de saídas atuais da execução (tabelas ctx.tabs, figuras_indice, arquivos fixos). Só entram na limpeza
 - results/h1_h22 e results/figures (diretórios exclusivos do pipeline): qualquer arquivo fora do registro atual;
 - data/processed: apenas cópias ' 2' de saídas do pipeline e nomes legados explícitos (LEGADOS_PROCESSED).
Derivados da Fase 1 (data/processed/audiencia*.csv etc.), results/tables, results/diagnostics, reports/*.md autorais e data/original NÃO são tocados."""
from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path

from auditar_base import sha

LEGADOS_PROCESSED = {'ponte_B_diagnostico.csv'}
DESTINO = 'historico/rascunhos_pre_revisao'
NOTA = """# NÃO USAR — rascunhos e cópias pré-revisão

Arquivos aqui foram **movidos** (nada foi apagado) de `data/processed/`, `results/h1_h22/` ou `results/figures/` por não pertencerem ao registro de saídas
da execução final do pipeline (`run_all.py`): cópias duplicadas (sufixo ` 2`, geradas fora do pipeline) ou saídas de versões anteriores à revisão metodológica.
Podem conter orientação antiga, resultados descartados ou valores-p superados. **Não citar, não usar em análises e não tratar como artefatos finais.**
O índice (`indice_arquivados.csv`) registra caminho original, SHA-256 e motivo. Os artefatos válidos estão listados em `results/manifesto_execucao.json`.
"""


def _relativos(saida: Path, caminhos) -> set[str]:
    return {str(Path(p).resolve().relative_to(saida)) for p in caminhos}


def arquivar_obsoletos(saida: Path, atuais: set[str]) -> list[dict]:
    """atuais: caminhos relativos a `saida` das saídas correntes do pipeline."""
    saida = Path(saida).resolve()
    dest = saida / DESTINO
    mov = []

    def mover(p: Path, motivo: str):
        rel = p.relative_to(saida)
        alvo = dest / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        i = 1
        while alvo.exists():
            alvo = alvo.with_name(f'{alvo.stem}__dup{i}{alvo.suffix}'); i += 1
        h = sha(p)
        shutil.move(str(p), str(alvo))
        mov.append({'caminho_original': str(rel), 'arquivado_em': str(alvo.relative_to(saida)), 'sha256': h, 'motivo': motivo})

    for sub in ('results/h1_h22', 'results/figures', 'results/figures/dados'):
        pasta = saida / sub
        if pasta.exists():
            for p in sorted(pasta.iterdir()):
                if p.is_file() and str(p.relative_to(saida)) not in atuais:
                    mover(p, 'cópia duplicada " 2" (fora do pipeline)' if re.search(r' 2(\.[^.]+)?$', p.name) else 'fora do registro de saídas atuais do pipeline')
    proc = saida / 'data/processed'
    if proc.exists():
        for p in sorted(proc.iterdir()):
            if not p.is_file() or str(p.relative_to(saida)) in atuais:
                continue
            m = re.match(r'^(.*) 2(\.[^.]+)$', p.name)
            if (m and f'data/processed/{m.group(1)}{m.group(2)}' in atuais) or p.name in LEGADOS_PROCESSED:
                mover(p, 'cópia duplicada " 2" de saída do pipeline' if m else 'nome legado do pipeline (orientação antiga)')
    if mov or dest.exists():
        dest.mkdir(parents=True, exist_ok=True)
        (dest / 'NAO_USAR.md').write_text(NOTA, encoding='utf-8')
        idx = dest / 'indice_arquivados.csv'
        antigo = list(csv.DictReader(idx.open(encoding='utf-8'))) if idx.exists() else []
        with idx.open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=['caminho_original', 'arquivado_em', 'sha256', 'motivo'])
            w.writeheader(); w.writerows(antigo + mov)
    return mov
