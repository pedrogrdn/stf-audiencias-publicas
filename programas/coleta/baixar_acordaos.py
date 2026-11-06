#!/usr/bin/env python3
"""Conclui downloads de acórdãos do STF registrados em controle_acordaos.xlsx."""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import truststore

truststore.inject_into_ssl()

import openpyxl
import requests

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
except ImportError:  # O instalador passa a incluir Selenium; mensagem amigável para ambientes antigos.
    webdriver = None
    ChromeOptions = None


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)
TIMEOUT = (20, 180)
MAX_HTML_DEPTH = 2
PDF_MAGIC = b"%PDF-"


class BaixadorChrome:
    """Usa Chrome somente quando o AWS WAF recusa a sessão requests."""

    def __init__(self, pasta_base: Path) -> None:
        if webdriver is None or ChromeOptions is None:
            raise RuntimeError(
                "O STF exigiu navegador, mas Selenium não está instalado. Rode: "
                ".venv/bin/python -m pip install selenium"
            )
        # Downloads temporários fora do Google Drive evitam sincronização/cache
        # reutilizando o arquivo anterior.
        self.raiz_temporaria = Path(tempfile.mkdtemp(prefix="stf_acordaos_"))
        self.pasta = self.raiz_temporaria / "downloads"
        self.perfil = self.raiz_temporaria / "perfil_chrome"
        self.pasta.mkdir(parents=True, exist_ok=True)
        self.perfil.mkdir(parents=True, exist_ok=True)
        options = ChromeOptions()
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": str(self.pasta.resolve()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
                "profile.default_content_setting_values.automatic_downloads": 1,
            },
        )
        options.add_argument(f"--user-agent={USER_AGENT}")
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1100,800")
        options.add_argument(f"--user-data-dir={self.perfil.resolve()}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        try:
            self.driver = webdriver.Chrome(options=options)
        except Exception as exc:
            shutil.rmtree(self.raiz_temporaria, ignore_errors=True)
            raise RuntimeError(
                "Não foi possível iniciar o Google Chrome automático. Feche todas "
                "as janelas do Chrome e execute novamente. Detalhe: " + str(exc)
            ) from exc
        # Abre primeiro o portal para o desafio JavaScript gerar os cookies do STF.
        self.driver.get("https://portal.stf.jus.br/")
        time.sleep(5)

    def obter_pdf(self, url: str) -> tuple[bytes, str]:
        for arquivo in self.pasta.iterdir():
            if arquivo.is_file():
                arquivo.unlink()

        self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        separador = "&" if "?" in url else "?"
        url_sem_cache = f"{url}{separador}_={time.time_ns()}"
        self.driver.get(url_sem_cache)
        limite = time.monotonic() + 240
        ultimo_tamanho = -1
        tamanho_estavel_desde = time.monotonic()
        while time.monotonic() < limite:
            parciais = list(self.pasta.glob("*.crdownload"))
            completos = [p for p in self.pasta.iterdir() if p.is_file() and p not in parciais]
            if completos and not parciais:
                arquivo = max(completos, key=lambda p: p.stat().st_mtime)
                tamanho = arquivo.stat().st_size
                if tamanho != ultimo_tamanho:
                    ultimo_tamanho = tamanho
                    tamanho_estavel_desde = time.monotonic()
                conteudo = arquivo.read_bytes()
                if pdf_completo(conteudo) and time.monotonic() - tamanho_estavel_desde >= 2:
                    return limpar_prefixo_pdf(conteudo), url
            time.sleep(1)
        raise RuntimeError(
            "O Chrome não recebeu um PDF completo em 240 segundos. Verifique se apareceu "
            "algum aviso ou desafio na janela do navegador."
        )

    def fechar(self) -> None:
        try:
            self.driver.quit()
        finally:
            shutil.rmtree(self.raiz_temporaria, ignore_errors=True)


def criar_sessao() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": (
                "application/pdf,application/octet-stream;q=0.9,"
                "text/html,application/xhtml+xml;q=0.8,*/*;q=0.7"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
    )
    return session


def normalizar_url(valor: object) -> str | None:
    if valor is None:
        return None
    texto = html.unescape(str(valor).strip()).replace("\\/", "/")
    # A coluna url_paginado pode conter uma chamada JavaScript, não um URL.
    chamada = re.search(
        r"abrirInteiroTeorPaginado\(\s*(\d+)\s*,\s*['\"]([^'\"]+)['\"]"
        r"\s*,\s*['\"]([^'\"]*)['\"]\s*,\s*['\"][^'\"]*['\"]"
        r"\s*,\s*['\"]([^'\"]+)['\"]",
        texto,
        flags=re.I,
    )
    if chamada:
        doc_id, _classe, _numero, doc_tp = chamada.groups()
        return (
            "https://redir.stf.jus.br/paginadorpub/paginador.jsp"
            f"?docTP={doc_tp}&docID={doc_id}"
        )
    match = re.search(r"https?://[^\s'\"<>]+", texto, flags=re.I)
    if match:
        return match.group(0).rstrip(");,]")
    return None


def parece_pdf(conteudo: bytes) -> bool:
    # Alguns proxies acrescentam poucos bytes antes da assinatura do arquivo.
    return PDF_MAGIC in conteudo[:1024]


def pdf_completo(conteudo: bytes) -> bool:
    """Exige cabeçalho, tabela de referências e marcador final do PDF."""
    if not parece_pdf(conteudo) or len(conteudo) < 1024:
        return False
    final = conteudo[-8192:]
    return b"startxref" in final and b"%%EOF" in final


def limpar_prefixo_pdf(conteudo: bytes) -> bytes:
    inicio = conteudo.find(PDF_MAGIC, 0, 1024)
    return conteudo[inicio:] if inicio > 0 else conteudo


def extrair_urls_html(conteudo: bytes, url_base: str) -> list[str]:
    texto = html.unescape(conteudo.decode("utf-8", errors="replace"))
    texto = texto.replace("\\/", "/").replace("\\u0026", "&")
    candidatos: list[str] = []

    padroes = (
        r"(?:src|href|data|content)\s*=\s*['\"]([^'\"]+)['\"]",
        r"https?://[^\s'\"<>]+",
        r"['\"]([^'\"]*(?:\.pdf(?:\?[^'\"]*)?|downloadPeca\.asp\?[^'\"]+|"
        r"paginador\.jsp\?[^'\"]+))['\"]",
    )
    for padrao in padroes:
        for achado in re.findall(padrao, texto, flags=re.I):
            bruto = achado if isinstance(achado, str) else achado[0]
            url = urljoin(url_base, bruto.strip().rstrip(");,]"))
            parsed = urlparse(url)
            if parsed.scheme in {"http", "https"} and (
                ".pdf" in url.lower()
                or "downloadpeca.asp" in url.lower()
                or "paginador.jsp" in url.lower()
            ):
                candidatos.append(url)

    # Mantém a ordem da página e elimina repetições.
    return list(dict.fromkeys(candidatos))


def obter_pdf(
    session: requests.Session,
    url_inicial: str,
    referer: str | None = None,
) -> tuple[bytes, str]:
    fila: list[tuple[str, int, str | None]] = [(url_inicial, 0, referer)]
    visitados: set[str] = set()
    ultimo_detalhe = "nenhuma resposta recebida"

    while fila:
        url, profundidade, origem = fila.pop(0)
        if url in visitados:
            continue
        visitados.add(url)
        headers = {"Referer": origem} if origem else {}
        resposta = session.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        conteudo = resposta.content
        content_type = resposta.headers.get("Content-Type", "")
        ultimo_detalhe = (
            f"HTTP {resposta.status_code}, Content-Type {content_type or 'ausente'}, "
            f"{len(conteudo)} bytes, URL {resposta.url}"
        )
        resposta.raise_for_status()

        # Cabeçalho e final estrutural são exigidos; o Content-Type não basta.
        if pdf_completo(conteudo):
            return limpar_prefixo_pdf(conteudo), resposta.url

        if profundidade < MAX_HTML_DEPTH and (
            "html" in content_type.lower() or conteudo.lstrip().startswith(b"<")
        ):
            for candidato in extrair_urls_html(conteudo, resposta.url):
                if candidato not in visitados:
                    fila.append((candidato, profundidade + 1, resposta.url))

    raise RuntimeError(
        "O STF não devolveu um PDF válido. Última resposta: " + ultimo_detalhe
    )


def nome_pdf(numero_audiencia: object, classe: object, numero: object) -> str:
    audiencia = int(numero_audiencia)
    num = str(numero).strip()
    if num.isdigit():
        num = num.zfill(3)
    return f"AP_{audiencia:02d}_{str(classe).strip().upper()}_{num}.pdf"


def localizar_planilha(base: Path, fornecida: str | None) -> Path:
    if fornecida:
        return Path(fornecida).expanduser().resolve()
    opcoes = (base / "resultados" / "controle_acordaos.xlsx", base / "controle_acordaos.xlsx")
    for opcao in opcoes:
        if opcao.exists():
            return opcao
    raise FileNotFoundError(
        "Não encontrei resultados/controle_acordaos.xlsx nem controle_acordaos.xlsx."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--planilha", help="caminho opcional para controle_acordaos.xlsx")
    parser.add_argument("--forcar", action="store_true", help="baixa novamente PDFs já registrados")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    planilha = localizar_planilha(base, args.planilha)
    pasta_pdf = base / "acordaos"
    pasta_pdf.mkdir(parents=True, exist_ok=True)

    workbook = openpyxl.load_workbook(planilha)
    sheet = workbook.active
    cabecalhos = {cell.value: cell.column for cell in sheet[1]}
    obrigatorios = {"numero_audiencia", "classe", "numero", "status_merito"}
    faltantes = obrigatorios - cabecalhos.keys()
    if faltantes:
        raise ValueError("Colunas ausentes na planilha: " + ", ".join(sorted(faltantes)))

    def garantir_coluna(nome: str) -> int:
        if nome not in cabecalhos:
            coluna = sheet.max_column + 1
            sheet.cell(1, coluna, nome)
            cabecalhos[nome] = coluna
        return cabecalhos[nome]

    for campo in (
        "download_realizado", "arquivo_pdf", "url_pdf_final", "hash_sha256",
        "possivel_duplicata", "mensagem_download", "erro",
    ):
        garantir_coluna(campo)

    session = criar_sessao()
    chrome: BaixadorChrome | None = None
    hashes: dict[str, str] = {}
    baixados = 0
    falhas = 0

    for linha in range(2, sheet.max_row + 1):
        def valor(nome: str) -> object:
            return sheet.cell(linha, cabecalhos[nome]).value if nome in cabecalhos else None

        if str(valor("status_merito") or "").upper() != "MERITO_PUBLICADO":
            continue
        if valor("download_realizado") is True and not args.forcar:
            arquivo_registrado = valor("arquivo_pdf")
            caminho_registrado = pasta_pdf / str(arquivo_registrado or "")
            if caminho_registrado.is_file() and pdf_completo(caminho_registrado.read_bytes()):
                continue
            print(
                f"  {valor('classe')} {valor('numero')}: "
                "arquivo anterior incompleto; refazendo..."
            )

        identificacao = f"{valor('classe')} {valor('numero')}"
        # As fontes originais têm prioridade. url_pdf_final é um resultado de
        # execução anterior e pode estar contaminado após uma falha/cache.
        urls = [
            normalizar_url(valor("url_integral")),
            normalizar_url(valor("url_paginado")),
            normalizar_url(valor("url_pdf_final")),
        ]
        urls = list(dict.fromkeys(url for url in urls if url))
        if not urls:
            sheet.cell(linha, cabecalhos["erro"], "Nenhum URL de acórdão disponível.")
            falhas += 1
            print(f"  {identificacao}: sem URL")
            continue

        erro_final = ""
        for url in urls:
            try:
                try:
                    conteudo, url_final = obter_pdf(
                        session, url, normalizar_url(valor("url_processo"))
                    )
                except RuntimeError as exc:
                    # HTTP 202 + HTML curto é o desafio AWS WAF observado no STF.
                    if "HTTP 202" not in str(exc):
                        raise
                    if chrome is None:
                        print("  STF solicitou validação de navegador; abrindo o Chrome...")
                        chrome = BaixadorChrome(pasta_pdf)
                    conteudo, url_final = chrome.obter_pdf(url)
                nome = nome_pdf(valor("numero_audiencia"), valor("classe"), valor("numero"))
                destino = pasta_pdf / nome
                temporario = destino.with_suffix(".pdf.part")
                temporario.write_bytes(conteudo)
                temporario.replace(destino)
                digest = hashlib.sha256(conteudo).hexdigest()
                duplicata = digest in hashes and hashes[digest] != nome
                hashes.setdefault(digest, nome)

                sheet.cell(linha, cabecalhos["download_realizado"], True)
                sheet.cell(linha, cabecalhos["arquivo_pdf"], nome)
                sheet.cell(linha, cabecalhos["url_pdf_final"], url_final)
                sheet.cell(linha, cabecalhos["hash_sha256"], digest)
                sheet.cell(linha, cabecalhos["possivel_duplicata"], duplicata)
                sheet.cell(linha, cabecalhos["mensagem_download"], "PDF baixado e validado pela assinatura %PDF-.")
                sheet.cell(linha, cabecalhos["erro"], None)
                baixados += 1
                print(f"  {identificacao}: OK -> {nome}")
                break
            except (requests.RequestException, RuntimeError, OSError) as exc:
                erro_final = str(exc)
        else:
            sheet.cell(linha, cabecalhos["download_realizado"], False)
            sheet.cell(linha, cabecalhos["mensagem_download"], "Download não concluído.")
            sheet.cell(linha, cabecalhos["erro"], erro_final)
            falhas += 1
            print(f"  {identificacao}: FALHOU -> {erro_final}")

    workbook.save(planilha)
    if chrome is not None:
        chrome.fechar()
    print(f"\nPDFs baixados nesta execução: {baixados}")
    print(f"Falhas: {falhas}")
    print(f"Planilha atualizada: {planilha}")
    print(f"Pasta dos PDFs: {pasta_pdf}")
    return 1 if falhas else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)
