#!/usr/bin/env python3
"""Coleta documentos oficiais úteis à identificação de participantes das APs do STF."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

from preparar_acoes_stf import PADRAO_AUDIENCIA, URL_BASE, USER_AGENT


BASE_DIR = Path(__file__).resolve().parent
PASTA_ACORDAOS = BASE_DIR / "acordaos"
PASTA_DOCUMENTOS = BASE_DIR / "documentos_audiencias"
MANIFESTO = PASTA_DOCUMENTOS / "manifesto.json"

ROTULOS_RELEVANTES = re.compile(
    r"habilitad|inscrit|expositor|participante|cronograma|programa|"
    r"transcri|taquigr|convoca|edital|ata\b|retifica|atualiza",
    re.I,
)
EXTENSOES = {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt"}


def texto(valor: object) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()


def audiencias_com_acordao() -> set[int]:
    encontrados = set()
    for caminho in PASTA_ACORDAOS.glob("AP_*_*.pdf"):
        achado = re.match(r"AP_(\d+)_", caminho.name)
        if achado:
            encontrados.add(int(achado.group(1)))
    return encontrados


def opcoes_chrome(downloads: Path, perfil: Path) -> ChromeOptions:
    opcoes = ChromeOptions()
    opcoes.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(downloads.resolve()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_setting_values.automatic_downloads": 1,
        },
    )
    for argumento in (
        "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
        "--disable-gpu", "--disable-blink-features=AutomationControlled",
        "--window-size=1400,1000",
    ):
        opcoes.add_argument(argumento)
    opcoes.add_argument(f"--user-agent={USER_AGENT}")
    opcoes.add_argument(f"--user-data-dir={perfil.resolve()}")
    opcoes.add_experimental_option("excludeSwitches", ["enable-automation"])
    return opcoes


def inventariar(driver: webdriver.Chrome, alvos: set[int]) -> list[dict[str, object]]:
    registros: list[dict[str, object]] = []
    vistos: set[tuple[int, str]] = set()
    for pagina in range(1, 10):
        url_pagina = f"{URL_BASE}?pagina={pagina}&tipo=realizada"
        driver.get(url_pagina)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        blocos = soup.select("div.audiencia")
        if not blocos:
            break
        numeros_pagina = set()
        for bloco in blocos:
            titulo = texto(bloco.get_text(" ", strip=True))
            achado = PADRAO_AUDIENCIA.search(titulo)
            if not achado:
                continue
            numero = int(achado.group(1))
            numeros_pagina.add(numero)
            if numero not in alvos:
                continue
            for link in bloco.select("a[href]"):
                rotulo = texto(link.get_text(" ", strip=True))
                url = urljoin(url_pagina, link.get("href", ""))
                if not ROTULOS_RELEVANTES.search(rotulo):
                    continue
                chave = (numero, url)
                if chave in vistos:
                    continue
                vistos.add(chave)
                registros.append({
                    "numero_audiencia": numero,
                    "rotulo": rotulo,
                    "url": url,
                    "url_pagina": url_pagina,
                    "status": "pendente",
                })
        print(f"Página {pagina}: {sorted(numeros_pagina)}", flush=True)
        if numeros_pagina and min(numeros_pagina) <= min(alvos):
            break
    return registros


def nome_destino(item: dict[str, object], indice: int) -> str:
    url = str(item["url"])
    sufixo = Path(urlparse(url).path).suffix.lower()
    if sufixo not in EXTENSOES:
        sufixo = ".html"
    rotulo = re.sub(r"[^a-z0-9]+", "_", texto(item["rotulo"]).casefold()).strip("_")[:55]
    return f"{indice:03d}_{rotulo or 'documento'}{sufixo}"


def aguardar_download(downloads: Path, inicio: float, limite_segundos: int = 180) -> Path | None:
    limite = time.monotonic() + limite_segundos
    estavel: dict[Path, tuple[int, float]] = {}
    while time.monotonic() < limite:
        parciais = list(downloads.glob("*.crdownload"))
        candidatos = [p for p in downloads.iterdir() if p.is_file() and p.stat().st_mtime >= inicio]
        for caminho in candidatos:
            tamanho = caminho.stat().st_size
            anterior = estavel.get(caminho)
            if anterior and anterior[0] == tamanho and time.monotonic() - anterior[1] >= 1.5 and not parciais:
                return caminho
            if not anterior or anterior[0] != tamanho:
                estavel[caminho] = (tamanho, time.monotonic())
        time.sleep(0.5)
    return None


def baixar(driver: webdriver.Chrome, downloads: Path, item: dict[str, object], indice: int) -> None:
    pasta = PASTA_DOCUMENTOS / f"AP_{int(item['numero_audiencia']):02d}"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / nome_destino(item, indice)
    if destino.exists() and destino.stat().st_size > 100:
        item.update(status="existente", arquivo=str(destino.relative_to(BASE_DIR)))
        return
    antes = {p.name for p in downloads.iterdir() if p.is_file()}
    inicio = time.time() - 0.1
    driver.get(str(item["url"]))
    recebido = aguardar_download(downloads, inicio, 45)
    if recebido and recebido.name not in antes:
        sufixo_real = recebido.suffix.lower()
        if sufixo_real in EXTENSOES and destino.suffix != sufixo_real:
            destino = destino.with_suffix(sufixo_real)
        shutil.move(str(recebido), destino)
    else:
        corpo = driver.page_source.encode("utf-8", errors="replace")
        if len(corpo) <= 500 or b"403 Forbidden" in corpo:
            item.update(status="erro", erro="STF recusou ou não entregou o documento")
            return
        destino = destino.with_suffix(".html")
        destino.write_bytes(corpo)
    dados = destino.read_bytes()
    if not dados:
        item.update(status="erro", erro="arquivo vazio")
        destino.unlink(missing_ok=True)
        return
    item.update(
        status="baixado", arquivo=str(destino.relative_to(BASE_DIR)),
        tamanho_bytes=len(dados), sha256=hashlib.sha256(dados).hexdigest(),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--somente-inventario", action="store_true")
    args = parser.parse_args()
    alvos = audiencias_com_acordao()
    PASTA_DOCUMENTOS.mkdir(exist_ok=True)
    raiz = Path(tempfile.mkdtemp(prefix="stf_docs_ap_"))
    downloads = raiz / "downloads"
    perfil = raiz / "perfil"
    downloads.mkdir(); perfil.mkdir()
    driver = webdriver.Chrome(options=opcoes_chrome(downloads, perfil))
    try:
        driver.get("https://portal.stf.jus.br/")
        time.sleep(4)
        itens = inventariar(driver, alvos)
        if not args.somente_inventario:
            for indice, item in enumerate(itens, 1):
                print(f"[{indice}/{len(itens)}] AP {item['numero_audiencia']}: {item['rotulo']}", flush=True)
                try:
                    baixar(driver, downloads, item, indice)
                except Exception as exc:  # preserva o progresso e permite revisão pontual
                    item.update(status="erro", erro=f"{type(exc).__name__}: {exc}")
                MANIFESTO.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")
        MANIFESTO.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Manifesto: {MANIFESTO}")
    finally:
        driver.quit()
        shutil.rmtree(raiz, ignore_errors=True)


if __name__ == "__main__":
    main()
