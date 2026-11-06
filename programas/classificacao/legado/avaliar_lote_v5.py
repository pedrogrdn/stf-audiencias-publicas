import validar_corpus as runner
from preparar_lote_v5 import DATA, NOTE

if __name__ == '__main__':
    runner.DATA = DATA
    runner.OUT = runner.ROOT / 'claude_novo_lote_v5'
    runner.EXPERIMENT_NOTE = NOTE
    try:
        runner.main()
    except RuntimeError as exc:
        raise SystemExit(str(exc))
