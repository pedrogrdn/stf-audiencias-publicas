"""Reutiliza confirmação, limite de custo e proteção contra repetição."""
import avaliar_claude as runner

if __name__ == '__main__':
    runner.DATA = runner.ROOT / 'engajamento_v1'
    runner.OUT = runner.ROOT / 'claude_engajamento_v1'
    runner.main()
