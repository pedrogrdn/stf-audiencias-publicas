#!/usr/bin/env python3
"""Extrai ocorrências temáticas e candidatos a participantes para revisão auditável."""

from __future__ import annotations

import csv
import argparse
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree

import fitz
from bs4 import BeautifulSoup


BASE = Path(__file__).resolve().parent
ACORDAOS = BASE / "acordaos"
DOCUMENTOS = BASE / "documentos_audiencias"
RESULTADOS = BASE / "resultados"
OCR_DOCUMENTOS = RESULTADOS / "ocr_documentos_audiencias"
CONTEXTO = 280

PADRAO_AP = re.compile(
    r"\baudi(?:[êe]|e\s*-\s*)ncias?\s+p(?:[úu]|u\s*-\s*)blicas?\b", re.I
)
PREFIXOS = r"(?:Dr\.?|Dra\.?|Prof\.?|Professor(?:a)?|Sr\.?|Sra\.?|Exmo\.?\s*Sr\.?|Ministr[oa](?:\s+de\s+Estado)?|Mestre|Doutor(?:a)?|Deputad[oa]\s+Federal|Embaixador|General\s+de\s+Brigada|Secretári[oa]\s+de\s+Estado|Pesquisador(?:a)?)"
PALAVRA_NOME = r"[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇÑ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇÑáàâãéèêíìîóòôõúùûçñ'’-]+"
NOME = rf"{PALAVRA_NOME}(?:\s+(?:d[aeo]s?|e|{PALAVRA_NOME})){{1,8}}"

# A exclusão é nominal, não baseada no título "Ministro", para preservar
# ministros de Estado e ex-ministros de outros tribunais.
MINISTROS_STF = {
    "alexandre de moraes", "andre luiz de almeida mendonca", "andre mendonca",
    "ayres britto", "carlos ayres britto", "carlos britto", "carlos mario velloso", "carmen lucia",
    "celso de mello", "cezar peluso", "cristiano zanin", "dias toffoli",
    "edson fachin", "ellen gracie", "eros grau", "flavio dino", "gilmar mendes",
    "ilmar galvao", "joaquim barbosa", "kassio nunes marques", "luiz fux",
    "marco aurelio", "menezes direito", "nelson jobim", "octavio gallotti",
    "ricardo lewandowski", "roberto barroso", "luís roberto barroso",
    "rosa weber", "sepulveda pertence", "sidney sanches",
}

TERMOS_INSTITUICAO = {
    "associacao", "instituto", "conselho", "universidade", "ministerio",
    "secretaria", "tribunal", "camara", "partido", "confederacao", "federacao",
    "fundacao", "organizacao", "comissao", "sociedade", "laboratorio", "frente",
    "agencia", "autoridade", "observatorio", "procuradoria", "defensoria", "empresa",
    "sindicato", "ordem dos", "uniao nacional", "rede de", "forum de", "banco central",
    "conferencia", "escola de", "faculdade", "departamento",
}


def squish(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def sem_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def texto_documento(caminho: Path) -> list[tuple[int | None, str]]:
    if caminho.stat().st_size == 0:
        return []
    ext = caminho.suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(caminho)
        paginas = [(i, pagina.get_text("text")) for i, pagina in enumerate(doc, 1)]
        if sum(len(texto.strip()) for _, texto in paginas) >= 200:
            return paginas
        cache = OCR_DOCUMENTOS / f"{caminho.parent.name}_{caminho.stem}.json"
        if cache.exists():
            dados = json.loads(cache.read_text(encoding="utf-8"))
            return [
                (int(pagina["pagina_pdf"]), str(pagina["texto"]))
                for pagina in dados.get("paginas", [])
            ]
        return paginas
    if ext == ".docx":
        with zipfile.ZipFile(caminho) as pacote:
            xml = pacote.read("word/document.xml")
        raiz = ElementTree.fromstring(xml)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        partes = []
        for paragrafo in raiz.iter(ns + "p"):
            # Um único parágrafo do Word pode conter quebras manuais. Elas são
            # estruturalmente relevantes em cronogramas como o da AP 3, no qual
            # instituição e expositor aparecem em linhas diferentes.
            trecho = []
            for no in paragrafo.iter():
                if no.tag == ns + "t":
                    trecho.append(no.text or "")
                elif no.tag in {ns + "br", ns + "cr"}:
                    trecho.append("\n")
                elif no.tag == ns + "tab":
                    trecho.append("\t")
            partes.append("".join(trecho))
        return [(None, "\n".join(partes))]
    if ext == ".html":
        soup = BeautifulSoup(caminho.read_text(encoding="utf-8", errors="replace"), "html.parser")
        return [(None, soup.get_text("\n", strip=True))]
    return []


def nome_valido(nome: str) -> bool:
    n = squish(re.sub(rf"^{PREFIXOS}\s+", "", nome, flags=re.I)).strip(" -–—,;:().")
    palavras = n.split()
    if not 2 <= len(palavras) <= 9 or len(n) > 100:
        return False
    proibidas = {
        "supremo tribunal", "audiência pública", "diário da justiça", "distrito federal",
        "ministério público", "advocacia geral", "presidência da república",
        "sala de sessões", "tribunal federal", "poder público",
        "mestre de cerimonia", "livre iniciativa", "materia ambiental",
        "chefe-geral", "chefe da assessoria", "secretario de politicas",
        "diretor do", "diretora do", "representante da", "representante do",
        "departamento de", "requerente da", "requerente do", "ex-ministro do",
        "atuacao individual", "intervencao ao de terceiro", "intervencao de terceiro",
    }
    baixo = sem_acentos(n).casefold()
    if "intervencao" in baixo.replace(" ", ""):
        return False
    if any(x in baixo for x in proibidas):
        return False
    termos_institucionais = {
        "associacao", "instituto", "conselho", "universidade", "ministerio",
        "secretaria", "tribunal", "camara", "partido", "confederacao",
        "federacao", "fundacao", "organizacao", "comissao", "sociedade",
        "laboratorio", "frente parlamentar", "nucleo de", "agencia nacional",
        "autoridade nacional", "observatorio", "procuradoria", "politicas publicas",
        "seguranca publica", "rio de janeiro", "rio grande do sul", "sao paulo",
    }
    return not any(x in baixo for x in termos_institucionais)


def limpar_nome(nome: str) -> str:
    nome = re.sub(rf"^{PREFIXOS}\s+", "", squish(nome), flags=re.I)
    nome = re.sub(r"\s+\((?:presencial|videoconferência).*", "", nome, flags=re.I)
    nome = re.sub(
        r"\s+(?:Bom|Boa|Excelentíssim[oa])(?:[- ](?:dia|tarde|noite))?\b.*$",
        "", nome, flags=re.I,
    )
    return nome.strip(" -–—,;:().")


def chave(valor: str) -> str:
    return squish(sem_acentos(valor).casefold())


def eh_ministro_stf(nome: str, evidencia: str) -> bool:
    k = chave(nome)
    if k in {chave(x) for x in MINISTROS_STF}:
        return True
    contexto = chave(evidencia)
    return (
        k in contexto
        and ("ministro do supremo tribunal federal" in contexto
             or "ministro aposentado do supremo tribunal federal" in contexto)
    )


def eh_cerimonial(nome: str, evidencia: str) -> bool:
    k_nome, k_evid = chave(nome), chave(evidencia)
    return (
        "mestre de cerimon" in k_nome
        or k_nome in {"de cerimonia", "de cerimonias"}
        or bool(re.search(rf"{re.escape(k_nome)}\s*\([^)]*mestre de cerimon", k_evid))
    )


def parece_instituicao(valor: str) -> bool:
    k = chave(valor)
    return any(termo in k for termo in TERMOS_INSTITUICAO)


def limpar_instituicao(valor: str) -> str | None:
    s = squish(valor).strip(" -–—,;:().")
    ministro_estado = re.match(r"^ministr[oa](?:\s+de\s+estado)?\s+d([ao])\s+(.+)$", s, re.I)
    if ministro_estado:
        prep = "da" if ministro_estado.group(1).casefold() == "a" else "do"
        return f"Ministério {prep} {squish(ministro_estado.group(2))}"
    s = re.sub(
        r"^(?:presidente|vice-presidente|representante|diretor(?:a)?|secretário(?:a)?|"
        r"coordenador(?:a)?|membro|advogad[oa]|ministro de estado|professor(?:a)?)\s+(?:d[aeo]s?|junto à)\s+",
        "", s, flags=re.I,
    )
    if chave(s) in {
        "ministerio", "secretaria", "senador", "senadora", "procurador", "procuradora",
        "educacao", "exteriores", "agricultura", "saude", "catarina", "amazonas",
        "florianopolis",
    }:
        return None
    if parece_instituicao(s):
        return s
    # Prefere a sigla quando a fonte a fornece, porque ela é a variante mais
    # útil para a busca e evita misturar cargo com instituição.
    siglas = re.findall(r"\b[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{1,6}\b", s)
    siglas = [x for x in siglas if sem_acentos(x) not in {
        "STF", "DF", "SR", "SRA", "DR", "DRA", "DA", "DE", "DO", "DAS", "DOS",
        "PAULO", "BRASIL", "ESTADO", "SAUDE", "AGRICULTURA", "PECUARIA",
        "ABASTECIMENTO", "PRESIDENTE", "RELATOR", "RELATORA", "ABERTURA",
        "UNIAO", "FEDERAL", "JUIZ", "JUIZA", "VARA",
    }]
    if siglas:
        return siglas[-1]
    if re.fullmatch(r"[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ]{2,20}", s):
        return s
    return None


def instituicoes_da_evidencia(nome: str, evidencia: str) -> list[str]:
    achados: list[str] = []
    # Ex.: AUGUSTO ... (PRESIDENTE DA UNE) ou NOME (INPA, Pesquisador).
    pos = sem_acentos(evidencia).casefold().find(sem_acentos(nome).casefold())
    trecho = evidencia[pos:] if pos >= 0 else evidencia
    parenteses = re.match(r"[^()]{0,25}\(([^)]{2,180})\)", trecho[len(nome):], re.I)
    if parenteses:
        inst = limpar_instituicao(parenteses.group(1).split(",", 1)[0])
        if inst:
            achados.append(inst)

    # Ex.: "09h45 - Nome - Secretaria ...".
    m = re.search(rf"{re.escape(nome)}\s*[-–—]\s*([^;|]{{2,180}})", evidencia, re.I)
    if m:
        inst = limpar_instituicao(m.group(1))
        if inst:
            achados.append(inst)

    # Ex.: "Instituição (Expositor: Nome, ...)".
    m = re.search(r"([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][^.();]{2,160})\s*\(Expositor(?:a|es|as)?\s*:\s*", evidencia, re.I)
    if m:
        candidato = re.split(r"(?:\d+[.)]|\d{1,2}h\d*\s*[-:])", m.group(1))[-1]
        inst = limpar_instituicao(candidato)
        if inst:
            achados.append(inst)
    return list(dict.fromkeys(achados))


def candidatos_em_texto(texto_bruto: str) -> list[tuple[str, str, str]]:
    texto = texto_bruto.replace("\xad", "")
    plano = squish(texto)
    achados: list[tuple[str, str, str]] = []

    # Fórmula mais confiável nas decisões/programações recentes.
    for m in re.finditer(r"Expositor(?:a|es|as)?\s*:\s*(.{3,260}?)(?=\bque\s+(?:particip|divid)|\)|;)", plano, re.I):
        trecho = m.group(1)
        for n in re.findall(rf"(?:{PREFIXOS}\s+)?({NOME})", trecho):
            achados.append((limpar_nome(n), "expositor_expresso", squish(plano[max(0,m.start()-100):m.end()+120])))

    # Linhas de cronograma no formato "09h30 - Nome - entidade".
    for linha in texto.splitlines():
        linha_l = squish(linha)
        m = re.match(r"(?:\d{1,2}h(?:\d{1,2})?(?:min)?|\d{1,2}:\d{2})\s*[-–—]\s*(.+)", linha_l, re.I)
        if m:
            n = re.match(rf"(?:{PREFIXOS}\s+)?({NOME})(?=\s*[-–—,(])", m.group(1))
            if n:
                achados.append((limpar_nome(n.group(1)), "cronograma", linha_l))

    # Cabeçalhos de fala das notas/transcrições.
    for m in re.finditer(
        rf"(?m)^\s*(?:[•·]\s*)?(?:(?:O|A)\s+)?(?:SR\.?|SRA\.?|DR\.?|DRA\.?|SENHOR(?:A)?|PROFESSOR(?:A)?)\s+(?:MINISTRO\s+)?({NOME})\s*(?:\([^\n]{{0,120}}\))?\s*[:–—-]",
        texto,
    ):
        achados.append((limpar_nome(m.group(1)), "fala_transcrita", squish(m.group(0))))

    # Listas nominais em decisões antigas: marcador, nome, hífen e qualificação.
    for m in re.finditer(rf"(?m)^\s*(?:[-–—•]|\d+[.)])\s*(?:{PREFIXOS}\s+)?({NOME})\s*[-–—]", texto):
        achados.append((limpar_nome(m.group(1)), "lista_nominal", squish(m.group(0))))

    return [(n, tipo, evid) for n, tipo, evid in achados if nome_valido(n)]


def extrair_participantes() -> list[dict[str, object]]:
    manifesto = json.loads((DOCUMENTOS / "manifesto.json").read_text(encoding="utf-8"))
    rotulos = {x.get("arquivo"): x.get("rotulo") for x in manifesto}
    linhas: list[dict[str, object]] = []
    for pasta in sorted(DOCUMENTOS.glob("AP_*")):
        audiencia = int(pasta.name.split("_")[1])
        for arq in sorted(pasta.iterdir()):
            rotulo = rotulos.get(str(arq.relative_to(BASE)), arq.stem)
            for pagina, txt in texto_documento(arq):
                for nome, tipo, evidencia in candidatos_em_texto(txt):
                    linhas.append({
                        "numero_audiencia": audiencia, "nome": nome,
                        "tipo_evidencia": tipo, "rotulo_fonte": rotulo,
                        "arquivo_fonte": str(arq.relative_to(BASE)), "pagina_fonte": pagina,
                        "evidencia": evidencia,
                    })
    # Deduplica a mesma evidência, preservando fontes distintas.
    unicos = {}
    for x in linhas:
        chave = (x["numero_audiencia"], sem_acentos(str(x["nome"])).casefold(), x["arquivo_fonte"], x["tipo_evidencia"])
        unicos[chave] = x
    return sorted(unicos.values(), key=lambda x: (int(x["numero_audiencia"]), sem_acentos(str(x["nome"])).casefold()))


def revisar_listas(participantes: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    lista: list[dict[str, object]] = []
    exclusoes: list[dict[str, object]] = []
    for item in participantes:
        nome = str(item["nome"])
        evidencia = str(item["evidencia"])
        motivo = None
        if eh_ministro_stf(nome, evidencia):
            motivo = "ministro_do_stf"
        elif eh_cerimonial(nome, evidencia):
            motivo = "cerimonial_ou_mestre_de_cerimonias"
        if motivo:
            exclusoes.append({**item, "motivo_exclusao": motivo})
            continue

        # Candidatos institucionais que a heurística anterior classificou como
        # nomes passam para a categoria correta.
        if parece_instituicao(nome):
            lista.append({
                "numero_audiencia": item["numero_audiencia"], "tipo_entrada": "instituicao",
                "entrada": nome, "pessoa_relacionada": None, "instituicao_relacionada": nome,
                "tipo_evidencia": item["tipo_evidencia"], "rotulo_fonte": item["rotulo_fonte"],
                "arquivo_fonte": item["arquivo_fonte"], "pagina_fonte": item["pagina_fonte"],
                "evidencia": evidencia,
            })
            continue

        instituicoes = instituicoes_da_evidencia(nome, evidencia)
        lista.append({
            "numero_audiencia": item["numero_audiencia"], "tipo_entrada": "pessoa",
            "entrada": nome, "pessoa_relacionada": nome,
            "instituicao_relacionada": " | ".join(instituicoes) or None,
            "tipo_evidencia": item["tipo_evidencia"], "rotulo_fonte": item["rotulo_fonte"],
            "arquivo_fonte": item["arquivo_fonte"], "pagina_fonte": item["pagina_fonte"],
            "evidencia": evidencia,
        })
        for instituicao in instituicoes:
            lista.append({
                "numero_audiencia": item["numero_audiencia"], "tipo_entrada": "instituicao",
                "entrada": instituicao, "pessoa_relacionada": nome,
                "instituicao_relacionada": instituicao,
                "tipo_evidencia": item["tipo_evidencia"], "rotulo_fonte": item["rotulo_fonte"],
                "arquivo_fonte": item["arquivo_fonte"], "pagina_fonte": item["pagina_fonte"],
                "evidencia": evidencia,
            })

    unicos = {}
    for x in lista:
        k = (x["numero_audiencia"], x["tipo_entrada"], chave(str(x["entrada"])),
             chave(str(x.get("pessoa_relacionada") or "")), x["arquivo_fonte"], x["tipo_evidencia"])
        unicos[k] = x
    return (
        sorted(unicos.values(), key=lambda x: (int(x["numero_audiencia"]), str(x["tipo_entrada"]), chave(str(x["entrada"])))),
        exclusoes,
    )


def buscar_ap() -> list[dict[str, object]]:
    saida = []
    for pdf in sorted(ACORDAOS.glob("*.pdf")):
        doc = fitz.open(pdf)
        for pagina, pg in enumerate(doc, 1):
            txt = squish(pg.get_text("text"))
            for m in PADRAO_AP.finditer(txt):
                saida.append({
                    "arquivo_pdf": pdf.name, "pagina_pdf": pagina,
                    "termo_encontrado": m.group(0),
                    "trecho": txt[max(0, m.start()-CONTEXTO):min(len(txt), m.end()+CONTEXTO)],
                })
    return saida


def buscar_nomes(participantes: list[dict[str, object]]) -> list[dict[str, object]]:
    por_ap: dict[int, dict[str, str]] = defaultdict(dict)
    for item in participantes:
        nome = str(item["nome"])
        por_ap[int(item["numero_audiencia"])][sem_acentos(nome).casefold()] = nome
    saida = []
    for pdf in sorted(ACORDAOS.glob("AP_*_*.pdf")):
        m_ap = re.match(r"AP_(\d+)_", pdf.name)
        if not m_ap:
            continue
        audiencia = int(m_ap.group(1))
        nomes = por_ap.get(audiencia, {})
        if not nomes:
            continue
        doc = fitz.open(pdf)
        for pagina, pg in enumerate(doc, 1):
            original = squish(pg.get_text("text"))
            normalizado = sem_acentos(original).casefold()
            for chave, nome in nomes.items():
                for achado in re.finditer(rf"(?<!\w){re.escape(chave)}(?!\w)", normalizado):
                    saida.append({
                        "numero_audiencia": audiencia, "arquivo_pdf": pdf.name,
                        "pagina_pdf": pagina, "nome_participante": nome,
                        "trecho": original[max(0, achado.start()-CONTEXTO):min(len(original), achado.end()+CONTEXTO)],
                    })
    return saida


def escrever_csv(caminho: Path, linhas: list[dict[str, object]]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos = list(linhas[0]) if linhas else []
    with caminho.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        if campos:
            w.writeheader(); w.writerows(linhas)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--somente-listas", action="store_true")
    args = parser.parse_args()
    participantes_brutos = extrair_participantes()
    participantes, exclusoes = revisar_listas(participantes_brutos)
    escrever_csv(RESULTADOS / "participantes_candidatos.csv", participantes_brutos)
    escrever_csv(RESULTADOS / "listas_participantes_revisadas.csv", participantes)
    escrever_csv(RESULTADOS / "exclusoes_listas_participantes.csv", exclusoes)
    if args.somente_listas:
        pessoas = { (x["numero_audiencia"], chave(str(x["entrada"]))) for x in participantes if x["tipo_entrada"] == "pessoa" }
        instituicoes = { (x["numero_audiencia"], chave(str(x["entrada"]))) for x in participantes if x["tipo_entrada"] == "instituicao" }
        print(f"Pessoas únicas: {len(pessoas)}")
        print(f"Instituições únicas: {len(instituicoes)}")
        print(f"Exclusões documentadas: {len(exclusoes)}")
        return
    ocorrencias = buscar_ap()
    pessoas_busca = [{**x, "nome": x["entrada"]} for x in participantes if x["tipo_entrada"] == "pessoa"]
    ocorrencias_nomes = buscar_nomes(pessoas_busca)
    escrever_csv(RESULTADOS / "ocorrencias_audiencia_publica.csv", ocorrencias)
    escrever_csv(RESULTADOS / "ocorrencias_nomes_participantes.csv", ocorrencias_nomes)
    resumo = defaultdict(set)
    for p in pessoas_busca:
        resumo[p["numero_audiencia"]].add(sem_acentos(str(p["nome"])).casefold())
    print(f"Ocorrências de audiência pública: {len(ocorrencias)}")
    print(f"Evidências nominais: {len(participantes)}")
    print(f"Ocorrências nominais nos acórdãos: {len(ocorrencias_nomes)}")
    print("Nomes únicos candidatos por audiência:")
    print(dict(sorted((k, len(v)) for k, v in resumo.items())))


if __name__ == "__main__":
    main()
