#!/usr/bin/env python3
"""Localiza, na jurisprudência do STF, o acórdão principal de cada ação."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

import openpyxl
import truststore
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

truststore.inject_into_ssl()

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_ACOES = BASE_DIR / "acoes_audiencias_stf.xlsx"
ARQUIVO_CONTROLE = BASE_DIR / "resultados" / "controle_acordaos_todos.xlsx"
ARQUIVO_NAO_LOCALIZADOS = BASE_DIR / "resultados" / "acordaos_nao_localizados.xlsx"
BASE_JURIS = "https://jurisprudencia.stf.jus.br"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)
COLUNAS = [
    "numero_audiencia", "classe", "numero", "observacao_entrada", "incidente",
    "url_processo", "status_merito", "confianca", "evidencia_status",
    "data_julgamento_sinal", "resultado_sinal", "rotulo_acordao_encontrado",
    "url_integral", "url_paginado", "download_realizado", "arquivo_pdf",
    "url_pdf_final", "hash_sha256", "possivel_duplicata", "mensagem_download", "erro",
]


def texto(valor: object) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()


def inteiro(valor: object) -> int:
    return int(float(str(valor).replace(".", "")))


def url_pesquisa(classe: str, numero: int) -> str:
    termo = quote(f"{classe} {numero}")
    return (
        f"{BASE_JURIS}/pages/search?classeNumeroIncidente={termo}&base=acordaos"
        "&sinonimo=true&plural=true&radicais=false&buscaExata=true&page=1&pageSize=10"
        "&sort=_score&sortBy=desc&isAdvanced=true"
    )


def criar_navegador(perfil: Path) -> webdriver.Chrome:
    opcoes = ChromeOptions()
    opcoes.add_argument("--headless=new")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--disable-gpu")
    opcoes.add_argument("--disable-blink-features=AutomationControlled")
    opcoes.add_argument("--window-size=1400,1000")
    opcoes.add_argument(f"--user-agent={USER_AGENT}")
    opcoes.add_argument(f"--user-data-dir={perfil}")
    opcoes.add_experimental_option("excludeSwitches", ["enable-automation"])
    opcoes.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=opcoes)


def preparar_controle() -> tuple[openpyxl.Workbook, object, dict[tuple[int, str, int], int]]:
    origem = openpyxl.load_workbook(ARQUIVO_ACOES, data_only=True)
    aba_origem = origem[origem.sheetnames[0]]
    cab = {texto(c.value): c.column for c in aba_origem[1]}
    obrigatorias = {"numero_audiencia", "classe", "numero"}
    if faltantes := obrigatorias - set(cab):
        raise ValueError("Colunas ausentes em acoes_audiencias_stf.xlsx: " + ", ".join(faltantes))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "controle"
    ws.append(COLUNAS)
    mapa: dict[tuple[int, str, int], int] = {}
    for linha in range(2, aba_origem.max_row + 1):
        def valor(nome: str):
            return aba_origem.cell(linha, cab[nome]).value if nome in cab else None
        audiencia = inteiro(valor("numero_audiencia"))
        classe = texto(valor("classe")).upper()
        numero = inteiro(valor("numero"))
        dados = {
            "numero_audiencia": audiencia, "classe": classe, "numero": numero,
            "observacao_entrada": valor("observacao"), "incidente": valor("incidente"),
            "url_processo": valor("url_processo"), "status_merito": "PENDENTE_LOCALIZAR_ACORDAO",
            "confianca": "PENDENTE", "download_realizado": False,
            "possivel_duplicata": False,
        }
        ws.append([dados.get(c) for c in COLUNAS])
        mapa[(audiencia, classe, numero)] = ws.max_row
    estilizar(ws)
    ARQUIVO_CONTROLE.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ARQUIVO_CONTROLE)
    return wb, ws, mapa


def carregar_ou_preparar(forcar: bool):
    if forcar or not ARQUIVO_CONTROLE.exists():
        return preparar_controle()
    wb = openpyxl.load_workbook(ARQUIVO_CONTROLE)
    ws = wb[wb.sheetnames[0]]
    cab = {texto(c.value): c.column for c in ws[1]}
    if not set(COLUNAS).issubset(cab):
        return preparar_controle()
    mapa = {}
    for lin in range(2, ws.max_row + 1):
        chave = (
            inteiro(ws.cell(lin, cab["numero_audiencia"]).value),
            texto(ws.cell(lin, cab["classe"]).value).upper(),
            inteiro(ws.cell(lin, cab["numero"]).value),
        )
        mapa[chave] = lin
    return wb, ws, mapa


def estilizar(ws) -> None:
    ws.freeze_panes = "A2"
    preenchimento = PatternFill("solid", fgColor="1F4E78")
    for celula in ws[1]:
        celula.fill = preenchimento
        celula.font = Font(color="FFFFFF", bold=True)
        celula.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 24
    for letra, largura in {"A": 18, "B": 12, "C": 14, "D": 38, "E": 16, "F": 38,
                            "G": 28, "H": 14, "I": 52, "J": 20, "K": 22, "L": 28,
                            "M": 48, "N": 48, "O": 18, "P": 34, "Q": 48, "R": 28,
                            "S": 20, "T": 46, "U": 38}.items():
        ws.column_dimensions[letra].width = largura
    for row in ws.iter_rows(min_row=2):
        for celula in row:
            celula.alignment = Alignment(vertical="top", wrap_text=celula.column >= 4)
    if not ws.tables:
        tabela = Table(displayName="ControleAcordaosTodos", ref=ws.dimensions)
        tabela.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(tabela)


def urls_rede(driver: webdriver.Chrome) -> list[str]:
    urls = []
    for item in driver.get_log("performance"):
        try:
            msg = json.loads(item["message"])["message"]
            if msg["method"] == "Network.requestWillBeSent":
                urls.append(msg["params"]["request"]["url"])
        except (KeyError, TypeError, json.JSONDecodeError):
            continue
    return urls


def url_pdf_do_inteiro_teor(driver: webdriver.Chrome, url_detalhe: str) -> str | None:
    driver.get(url_detalhe)
    espera = WebDriverWait(driver, 35)
    icone = espera.until(EC.element_to_be_clickable((By.XPATH, "//mat-icon[@mattooltip='Inteiro teor']")))
    urls_rede(driver)
    janela_original = driver.current_window_handle
    janelas_antes = set(driver.window_handles)
    driver.execute_script("arguments[0].click()", icone)
    limite = time.monotonic() + 12
    candidatos: list[str] = []
    while time.monotonic() < limite:
        time.sleep(0.5)
        candidatos.extend(urls_rede(driver))
        novas = set(driver.window_handles) - janelas_antes
        if novas:
            driver.switch_to.window(novas.pop())
            candidatos.append(driver.current_url)
            driver.close()
            driver.switch_to.window(janela_original)
            break
    for url in reversed(candidatos):
        baixa = url.casefold()
        if "paginador" in baixa or "redir.stf.jus.br" in baixa or baixa.endswith(".pdf"):
            return url
    return None


def localizar(driver: webdriver.Chrome, classe: str, numero: int) -> dict[str, object]:
    rotulo = f"{classe} {numero}"
    driver.get(url_pesquisa(classe, numero))
    espera = WebDriverWait(driver, 20)
    try:
        def resultados_prontos(navegador) -> bool:
            corpo = texto(navegador.find_element(By.TAG_NAME, "body").text)
            if "Nenhum resultado encontrado na base Acórdãos" in corpo:
                return True
            contagem = re.search(r"(\d+)\s+resultado\(s\)\s+para:", corpo, re.I)
            if not contagem:
                return False
            if int(contagem.group(1)) == 0:
                return True
            return bool(navegador.find_elements(By.CSS_SELECTOR, "a[href*='/pages/search/'] h4"))

        espera.until(resultados_prontos)
        # A seção de ocorrências relacionadas é inserida logo após o cartão.
        time.sleep(0.8)
    except TimeoutException:
        raise RuntimeError("A página de jurisprudência não terminou de carregar.")

    exatos = []
    for titulo in driver.find_elements(By.XPATH, "//h4"):
        if texto(titulo.text).upper() == rotulo.upper():
            exatos.append(titulo)
    if not exatos:
        # Em julgamentos conjuntos, o STF indexa o PDF sob uma das ações e
        # relaciona as demais em "Acórdãos no mesmo sentido". Esses links
        # contêm a classe e o número canônicos no próprio obterInteiroTeor.
        for link_mesmo_sentido in driver.find_elements(
            By.CSS_SELECTOR, "a[onclick*='obterInteiroTeor']"
        ):
            # O Angular mantém onclick no HTML renderizado, mas o Chrome pode
            # devolver None ao consultar somente o atributo DOM.
            chamada = html.unescape(link_mesmo_sentido.get_attribute("outerHTML") or "")
            achado = re.search(
                r"openPopup\(['\"](https?://[^'\"]*obterInteiroTeor\.asp\?[^'\"]+)['\"]",
                chamada, re.I,
            )
            if not achado:
                continue
            url_candidata = achado.group(1)
            numero_url = re.search(r"[?&]numero=(\d+)", url_candidata, re.I)
            classe_url = re.search(r"[?&]classe=([A-Z]+)", url_candidata, re.I)
            if not numero_url or not classe_url:
                continue
            if inteiro(numero_url.group(1)) != numero or classe_url.group(1).upper() != classe:
                continue
            contexto = texto(link_mesmo_sentido.find_element(By.XPATH, "./ancestor::p[1]").text)
            julgamento = re.search(r"JULG-(\d{2}-\d{2}-\d{4})", contexto, re.I)
            publicacao = re.search(r"PUBLIC\s+(\d{2}-\d{2}-\d{4})", contexto, re.I)
            data_julgamento = julgamento.group(1).replace("-", "/") if julgamento else None
            data_publicacao = publicacao.group(1).replace("-", "/") if publicacao else None
            return {
                "status_merito": "MERITO_PUBLICADO", "confianca": "ALTA",
                "evidencia_status": (
                    f"{rotulo} consta na seção 'Acórdãos no mesmo sentido' de um julgamento "
                    f"conjunto; julgamento {data_julgamento or 'não informado'}; publicação "
                    f"{data_publicacao or 'não informada'}."
                ),
                "data_julgamento_sinal": data_julgamento,
                "resultado_sinal": "Acórdão localizado em julgamento conjunto",
                "rotulo_acordao_encontrado": rotulo,
                "url_integral": url_candidata, "url_paginado": url_candidata, "erro": None,
            }
        return {
            "status_merito": "SEM_ACORDAO_PRINCIPAL_PUBLICADO", "confianca": "ALTA",
            "evidencia_status": f"A busca exata por {rotulo} não apresentou acórdão com esse título.",
        }

    titulo = exatos[0]
    link = titulo.find_element(By.XPATH, "./ancestor::a[1]")
    url_detalhe = link.get_attribute("href")
    bloco = titulo.find_element(
        By.XPATH, "./ancestor::div[contains(@class,'hide-in-print-espelho')][1]"
    )
    bloco_texto = texto(bloco.text)
    julgamento = re.search(r"Julgamento:\s*(\d{2}/\d{2}/\d{4})", bloco_texto, re.I)
    publicacao = re.search(r"Publica(?:ção|cao):\s*(\d{2}/\d{2}/\d{4})", bloco_texto, re.I)
    url_pdf = url_pdf_do_inteiro_teor(driver, url_detalhe)
    if not url_pdf:
        return {
            "status_merito": "ACORDAO_LOCALIZADO_SEM_LINK_PDF", "confianca": "ALTA",
            "rotulo_acordao_encontrado": rotulo,
            "data_julgamento_sinal": julgamento.group(1) if julgamento else None,
            "evidencia_status": f"Acórdão principal localizado em {url_detalhe}, mas o link do inteiro teor não foi capturado.",
            "erro": "O STF não expôs o endereço do PDF ao navegador automático.",
        }
    return {
        "status_merito": "MERITO_PUBLICADO", "confianca": "ALTA",
        "evidencia_status": (
            f"Resultado exato {rotulo}; julgamento "
            f"{julgamento.group(1) if julgamento else 'não informado'}; publicação "
            f"{publicacao.group(1) if publicacao else 'não informada'}."
        ),
        "data_julgamento_sinal": julgamento.group(1) if julgamento else None,
        "resultado_sinal": "Acórdão principal localizado na base de jurisprudência",
        "rotulo_acordao_encontrado": rotulo, "url_integral": url_pdf,
        "url_paginado": url_pdf, "erro": None,
    }


def atualizar(ws, linha: int, dados: dict[str, object]) -> None:
    cab = {texto(c.value): c.column for c in ws[1]}
    for nome, valor in dados.items():
        if nome in cab:
            ws.cell(linha, cab[nome], valor)


def salvar_nao_localizados(ws) -> int:
    """Cria uma lista simples somente com o que ainda requer conferência."""
    cab = {texto(c.value): c.column for c in ws[1]}
    colunas = [
        "numero_audiencia", "classe", "numero", "status_merito",
        "evidencia_status", "url_processo", "observacao_entrada", "erro",
    ]
    wb_lista = openpyxl.Workbook()
    lista = wb_lista.active
    lista.title = "nao_localizados"
    lista.append(colunas)
    for linha in range(2, ws.max_row + 1):
        status = texto(ws.cell(linha, cab["status_merito"]).value).upper()
        if status != "MERITO_PUBLICADO":
            lista.append([ws.cell(linha, cab[nome]).value for nome in colunas])
    estilizar(lista)
    # A tabela criada por estilizar usa um nome fixo; neste arquivo ele é único.
    wb_lista.save(ARQUIVO_NAO_LOCALIZADOS)
    return lista.max_row - 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limite", type=int, help="processa somente esta quantidade (útil para teste)")
    parser.add_argument(
        "--processo", action="append", metavar="CLASSE_NUMERO",
        help="restringe o teste a um processo; pode ser repetido (ex.: ADI_3510)",
    )
    parser.add_argument(
        "--revisar-sem-acordao", action="store_true",
        help="repete a busca dos registros antes classificados como sem acórdão",
    )
    parser.add_argument("--forcar", action="store_true", help="recria e pesquisa novamente toda a planilha")
    args = parser.parse_args()
    if not ARQUIVO_ACOES.exists():
        raise FileNotFoundError("Execute primeiro PREPARAR_ACOES_STF.command.")

    wb, ws, mapa = carregar_ou_preparar(args.forcar)
    cab = {texto(c.value): c.column for c in ws[1]}
    pendentes = []
    for chave, linha in mapa.items():
        status = texto(ws.cell(linha, cab["status_merito"]).value).upper()
        elegiveis = {"", "PENDENTE_LOCALIZAR_ACORDAO", "ERRO_LOCALIZACAO"}
        if args.revisar_sem_acordao:
            elegiveis.add("SEM_ACORDAO_PRINCIPAL_PUBLICADO")
        if args.forcar or status in elegiveis:
            pendentes.append((chave, linha))
    if args.processo:
        escolhidos = {
            (p.rsplit("_", 1)[0].upper(), inteiro(p.rsplit("_", 1)[1]))
            for p in args.processo
        }
        pendentes = [item for item in pendentes if (item[0][1], item[0][2]) in escolhidos]
    if args.limite is not None:
        pendentes = pendentes[:max(0, args.limite)]
    if not pendentes:
        quantidade = salvar_nao_localizados(ws)
        print("Nenhum processo pendente de localização.")
        print(f"Lista para conferência ({quantidade}): {ARQUIVO_NAO_LOCALIZADOS}")
        return 0

    raiz = Path(tempfile.mkdtemp(prefix="stf_localizador_"))
    driver = criar_navegador(raiz / "perfil")
    totais: dict[str, int] = {}
    try:
        driver.get("https://jurisprudencia.stf.jus.br/")
        time.sleep(4)
        for indice, ((audiencia, classe, numero), linha) in enumerate(pendentes, 1):
            print(f"[{indice}/{len(pendentes)}] Audiência {audiencia}: {classe} {numero}")
            try:
                dados = localizar(driver, classe, numero)
                print(f"  {dados['status_merito']}")
            except Exception as exc:
                dados = {
                    "status_merito": "ERRO_LOCALIZACAO", "confianca": "PENDENTE",
                    "erro": texto(exc), "evidencia_status": "Falha técnica durante a consulta ao STF.",
                }
                print(f"  ERRO: {exc}")
            atualizar(ws, linha, dados)
            wb.save(ARQUIVO_CONTROLE)
            status = str(dados["status_merito"])
            totais[status] = totais.get(status, 0) + 1
    finally:
        driver.quit()
        shutil.rmtree(raiz, ignore_errors=True)
        wb.save(ARQUIVO_CONTROLE)

    print("\nLocalização concluída:")
    for status, quantidade in sorted(totais.items()):
        print(f"  {status}: {quantidade}")
    print(f"Planilha atualizada: {ARQUIVO_CONTROLE}")
    quantidade = salvar_nao_localizados(ws)
    print(f"Lista para conferência ({quantidade}): {ARQUIVO_NAO_LOCALIZADOS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
