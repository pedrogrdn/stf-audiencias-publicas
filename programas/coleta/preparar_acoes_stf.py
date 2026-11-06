#!/usr/bin/env python3
"""Coleta as audiências públicas realizadas no portal do STF e prepara a coleta."""

from __future__ import annotations

import re
import shutil
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import openpyxl
import truststore
from bs4 import BeautifulSoup
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

truststore.inject_into_ssl()

BASE_DIR = Path(__file__).resolve().parent
URL_BASE = "https://portal.stf.jus.br/audienciapublica/audienciaPublica.asp"
ARQUIVO_ACOES = BASE_DIR / "acoes_audiencias_stf.xlsx"
ARQUIVO_CONTROLE = BASE_DIR / "resultados" / "controle_acordaos_todos.xlsx"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)

PADRAO_AUDIENCIA = re.compile(r"Audi[êe]ncia\s+P[úu]blica.*?[nN][º°o]?\s*(\d+)", re.I)
PADRAO_PROCESSO = re.compile(
    r"\b(ADI|ADPF|ADC|ADO|ARE|RE|HC|SL|STA|SS|MI|RCL|ACO|AO|PET|INQ|AP)S?"
    r"\s*(?:n[º°o]\s*)?(\d[\d.]*)\b",
    re.I,
)
CORRECOES_POR_INCIDENTE = {
    # O HTML antigo exibe visualmente "RE 586.224", mas separa o número em tags.
    "2616565": ("RE", 586224),
}


def texto_limpo(valor: object) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()


def extrair_processo(texto: str) -> tuple[str, int] | None:
    achado = PADRAO_PROCESSO.search(texto_limpo(texto).replace(".532.603", "1532603"))
    if not achado:
        return None
    return achado.group(1).upper(), int(achado.group(2).replace(".", ""))


def criar_navegador(perfil: Path) -> webdriver.Chrome:
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1300,1000")
    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_argument(f"--user-data-dir={perfil}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(options=options)


def urls_acordaos(bloco) -> list[str]:
    encontrados: list[str] = []
    for link in bloco.select("a[href]"):
        rotulo = texto_limpo(link.get_text(" ", strip=True)).casefold()
        href = urljoin(URL_BASE, link.get("href", ""))
        if (
            "acórdão" in rotulo
            or "acordão" in rotulo
            or "acordao" in rotulo
        ) and (
            "paginador" in href.casefold()
            or "abririnteiroteor" in href.casefold()
            or "jurisprudencia" in href.casefold()
            or ".pdf" in href.casefold()
        ):
            encontrados.append(href)
    return list(dict.fromkeys(encontrados))


def processos_do_bloco(bloco) -> list[dict[str, object]]:
    # A linha "Referência" é canônica. Ela preserva a classe mesmo quando os
    # links individuais mostram somente os números (ex.: ADIs 7688, 7695 e 7697).
    referencia_no = bloco.find(string=re.compile(r"Refer[êe]ncia\s*:", re.I))
    referencia_tag = referencia_no.parent if referencia_no else None
    while referencia_tag and referencia_tag.parent != bloco:
        texto_atual = texto_limpo(referencia_tag.get_text(" ", strip=True))
        if referencia_tag.name in {"p", "div", "li"} and len(texto_atual) >= 15:
            break
        referencia_tag = referencia_tag.parent
    referencia = texto_limpo(
        referencia_tag.get_text(" ", strip=True) if referencia_tag else ""
    )
    referencia = referencia.split(":", 1)[-1]
    referencia = re.sub(r"\s*\.\s*", ".", referencia)
    canonicos: list[tuple[str, int]] = []
    classes = "ADI|ADPF|ADC|ADO|ARE|RE|HC|SL|STA|SS|MI|RCL|ACO|AO|PET|INQ|AP"
    grupos = list(
        re.finditer(
            rf"\b({classes})S?\s+(.+?)(?=\b(?:{classes})S?\s+|$)",
            referencia,
            re.I | re.S,
        )
    )
    for grupo in grupos:
        classe = grupo.group(1).upper()
        for numero_texto in re.findall(r"\d[\d.]*", grupo.group(2)):
            canonicos.append((classe, int(numero_texto.replace(".", ""))))

    links = []
    processos_links = []
    for link in bloco.select('a[href*="processos/detalhe.asp"]'):
        href = urljoin(URL_BASE, link.get("href", ""))
        incidente = parse_qs(urlparse(href).query).get("incidente", [None])[0]
        links.append({"incidente": incidente, "url_processo": href})
        processo_link = extrair_processo(link.get_text(" ", strip=True))
        if processo_link:
            processos_links.append(processo_link)

    canonicos = list(dict.fromkeys(canonicos))

    if links and len(processos_links) == len(links):
        return [
            {
                "classe": CORRECOES_POR_INCIDENTE.get(str(links[i]["incidente"]), processo)[0],
                "numero": CORRECOES_POR_INCIDENTE.get(str(links[i]["incidente"]), processo)[1],
                **links[i],
            }
            for i, processo in enumerate(processos_links)
        ]

    if canonicos:
        return [
            {
                "classe": classe, "numero": numero,
                "incidente": links[i]["incidente"] if i < len(links) else None,
                "url_processo": links[i]["url_processo"] if i < len(links) else None,
            }
            for i, (classe, numero) in enumerate(canonicos)
        ]

    return [
        {"classe": processo[0], "numero": processo[1], **links[i]}
        for i, processo in enumerate(processos_links)
    ]


def extrair_pagina(html: str, url_pagina: str) -> list[dict[str, object]]:
    soup = BeautifulSoup(html, "html.parser")
    registros: list[dict[str, object]] = []
    for bloco in soup.select("div.audiencia"):
        titulo_tag = bloco.select_one("div.chamada-audiencia strong")
        titulo = texto_limpo(titulo_tag.get_text(" ", strip=True) if titulo_tag else "")
        numero_match = PADRAO_AUDIENCIA.search(titulo)
        if not numero_match:
            continue
        audiencia = int(numero_match.group(1))
        periodo = [texto_limpo(x.get_text(" ", strip=True)) for x in bloco.select("div.periodo span")]
        data_cadastro = periodo[0] if periodo else None
        data_realizacao = periodo[1] if len(periodo) > 1 else None
        paragrafos = [texto_limpo(p.get_text(" ", strip=True)) for p in bloco.select("p")]
        tema_tag = bloco.select_one("div.conteudo strong")
        tema = texto_limpo(tema_tag.get_text(" ", strip=True) if tema_tag else "")
        if tema.casefold().startswith(("referência", "data designada", "local:")):
            tema = ""
        resumo = tema or next((p for p in paragrafos if len(p) >= 40), "")
        processos = processos_do_bloco(bloco)
        acordaos = urls_acordaos(bloco)

        for indice, processo in enumerate(processos):
            if len(acordaos) == 1:
                url_acordao = acordaos[0]
            elif len(acordaos) == len(processos):
                url_acordao = acordaos[indice]
            else:
                url_acordao = None
            registros.append(
                {
                    "numero_audiencia": audiencia,
                    **processo,
                    "data_cadastro_stf": data_cadastro,
                    "data_realizacao": data_realizacao,
                    "observacao": resumo,
                    "url_pagina_audiencia": url_pagina,
                    "url_acordao_pagina": url_acordao,
                    "quantidade_links_acordao": len(acordaos),
                }
            )
    return registros


def coletar() -> list[dict[str, object]]:
    raiz = Path(tempfile.mkdtemp(prefix="stf_audiencias_"))
    driver = criar_navegador(raiz / "perfil")
    registros: list[dict[str, object]] = []
    assinaturas: set[tuple[int, ...]] = set()
    try:
        for pagina in range(1, 21):
            url = f"{URL_BASE}?pagina={pagina}&tipo=realizada"
            driver.get(url)
            time.sleep(3 if pagina == 1 else 1)
            itens = extrair_pagina(driver.page_source, url)
            if not itens:
                break
            assinatura = tuple(sorted({int(x["numero_audiencia"]) for x in itens}))
            if assinatura in assinaturas:
                break
            assinaturas.add(assinatura)
            registros.extend(itens)
            audiencias = sorted({int(x["numero_audiencia"]) for x in itens}, reverse=True)
            print(f"  Página {pagina}: audiências {audiencias[-1]} a {audiencias[0]}")
    finally:
        driver.quit()
        shutil.rmtree(raiz, ignore_errors=True)

    unicos: dict[tuple[int, str, int, str], dict[str, object]] = {}
    for item in registros:
        chave = (
            int(item["numero_audiencia"]), str(item["classe"]), int(item["numero"]),
            str(item.get("incidente") or ""),
        )
        unicos[chave] = item
    return sorted(
        unicos.values(), key=lambda x: (int(x["numero_audiencia"]), str(x["classe"]), int(x["numero"]))
    )


def estilizar_planilha(sheet, nome_tabela: str) -> None:
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    cabecalho = PatternFill("solid", fgColor="1F4E78")
    for cell in sheet[1]:
        cell.fill = cabecalho
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(vertical="center")
    sheet.row_dimensions[1].height = 24
    for coluna, largura in {
        "A": 18, "B": 12, "C": 14, "D": 16, "E": 18, "F": 18,
        "G": 32, "H": 18, "I": 42, "J": 18, "K": 18, "L": 24,
        "M": 28, "N": 28, "O": 18, "P": 24, "Q": 28, "R": 28,
        "S": 20, "T": 34, "U": 28,
    }.items():
        sheet.column_dimensions[coluna].width = largura
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=cell.column >= 7)
    tabela = Table(displayName=nome_tabela, ref=sheet.dimensions)
    tabela.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False,
        showRowStripes=True, showColumnStripes=False,
    )
    sheet.add_table(tabela)


def salvar_acoes(registros: list[dict[str, object]]) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "acoes"
    colunas = [
        "numero_audiencia", "classe", "numero", "observacao", "data_realizacao",
        "incidente", "url_processo", "url_acordao_pagina", "url_pagina_audiencia",
    ]
    ws.append(colunas)
    for r in registros:
        ws.append([r.get(c) for c in colunas])
    estilizar_planilha(ws, "AcoesAudienciasSTF")
    wb.save(ARQUIVO_ACOES)


def salvar_controle(registros: list[dict[str, object]]) -> None:
    ARQUIVO_CONTROLE.parent.mkdir(parents=True, exist_ok=True)
    anteriores: dict[tuple[int, str, int], dict[str, object]] = {}
    if ARQUIVO_CONTROLE.exists():
        wb_anterior = openpyxl.load_workbook(ARQUIVO_CONTROLE, data_only=False)
        ws_anterior = wb_anterior[wb_anterior.sheetnames[0]]
        cab_anterior = {texto_limpo(c.value): c.column for c in ws_anterior[1]}
        if {"numero_audiencia", "classe", "numero"}.issubset(cab_anterior):
            for linha in range(2, ws_anterior.max_row + 1):
                chave = (
                    int(ws_anterior.cell(linha, cab_anterior["numero_audiencia"]).value),
                    texto_limpo(ws_anterior.cell(linha, cab_anterior["classe"]).value).upper(),
                    int(ws_anterior.cell(linha, cab_anterior["numero"]).value),
                )
                anteriores[chave] = {
                    nome: ws_anterior.cell(linha, coluna).value
                    for nome, coluna in cab_anterior.items()
                }

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "controle"
    colunas = [
        "numero_audiencia", "classe", "numero", "observacao_entrada", "incidente",
        "url_processo", "status_merito", "confianca", "evidencia_status",
        "data_julgamento_sinal", "resultado_sinal", "rotulo_acordao_encontrado",
        "url_integral", "url_paginado", "download_realizado", "arquivo_pdf",
        "url_pdf_final", "hash_sha256", "possivel_duplicata", "mensagem_download", "erro",
    ]
    ws.append(colunas)
    chaves_atuais: set[tuple[int, str, int]] = set()
    for r in registros:
        chave = (int(r["numero_audiencia"]), str(r["classe"]), int(r["numero"]))
        chaves_atuais.add(chave)
        url_acordao = r.get("url_acordao_pagina")
        status = "PENDENTE_LOCALIZAR_ACORDAO"
        evidencia = (
            "A página da audiência contém um link rotulado Acórdão, ainda não validado como mérito principal."
            if url_acordao else
            "A página oficial da audiência informa o processo, mas não fornece link de Acórdão."
        )
        linha = dict(anteriores.get(chave, {}))
        linha.update({
            "numero_audiencia": r.get("numero_audiencia"), "classe": r.get("classe"),
            "numero": r.get("numero"), "observacao_entrada": r.get("observacao"),
            "incidente": r.get("incidente"), "url_processo": r.get("url_processo"),
        })
        if chave not in anteriores:
            linha.update({
                "status_merito": status, "confianca": "PENDENTE",
                "evidencia_status": evidencia, "rotulo_acordao_encontrado": None,
                "url_integral": None, "url_paginado": url_acordao,
                "download_realizado": False, "possivel_duplicata": False,
            })
        elif not linha.get("url_paginado") and url_acordao:
            linha["url_paginado"] = url_acordao
        ws.append([linha.get(c) for c in colunas])

    # Mantém registros históricos caso uma audiência desapareça temporariamente
    # da página do STF, sem perder PDFs, hashes ou decisões já localizadas.
    for chave, linha in anteriores.items():
        if chave not in chaves_atuais:
            ws.append([linha.get(c) for c in colunas])
    estilizar_planilha(ws, "ControleAcordaosTodos")
    wb.save(ARQUIVO_CONTROLE)


def main() -> None:
    print("STF - coleta da lista de audiências públicas realizadas")
    registros = coletar()
    if not registros:
        raise RuntimeError("Nenhuma audiência/processo foi encontrado no portal do STF.")
    salvar_acoes(registros)
    salvar_controle(registros)
    audiencias = {int(r["numero_audiencia"]) for r in registros}
    com_acordao = sum(bool(r.get("url_acordao_pagina")) for r in registros)
    print(f"\nAudiências identificadas: {len(audiencias)}")
    print(f"Processos identificados: {len(registros)}")
    print(f"Processos com link de acórdão na página: {com_acordao}")
    print(f"Planilha para revisão: {ARQUIVO_ACOES}")
    print(f"Controle para download: {ARQUIVO_CONTROLE}")


if __name__ == "__main__":
    main()
