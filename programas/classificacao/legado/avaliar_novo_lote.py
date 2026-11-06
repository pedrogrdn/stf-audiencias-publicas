import validar_corpus as runner
from preparar_novo_lote import DATA, NOTE
if __name__=='__main__':
    runner.DATA=DATA;runner.OUT=runner.ROOT/'claude_novo_lote_v3';runner.EXPERIMENT_NOTE=NOTE
    try:runner.main()
    except RuntimeError as e:raise SystemExit(str(e))
