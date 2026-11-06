"""Carrega credencial local sem imprimir ou persistir seu conteúdo."""
import getpass
from pathlib import Path

KEY_FILE = Path(__file__).resolve().parents[3] / 'claude.txt'

def obter_chave(path=None):
    source = KEY_FILE if path is None else Path(path)
    try:
        key = source.read_text(encoding='utf-8-sig').strip()
    except FileNotFoundError:
        key = getpass.getpass('Chave API (oculta): ').strip()
    except (OSError, UnicodeError):
        raise SystemExit('Não foi possível ler claude.txt. Confira o acesso e a codificação UTF-8.') from None
    if not key:
        raise SystemExit('Chave vazia. Informe somente a chave em claude.txt.')
    if any(c.isspace() for c in key):
        raise SystemExit('Formato inválido: claude.txt deve conter somente a chave, em uma linha.')
    return key
