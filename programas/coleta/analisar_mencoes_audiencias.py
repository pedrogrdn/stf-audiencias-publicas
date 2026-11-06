#!/usr/bin/env python3
"""Localiza e pré-classifica menções às audiências públicas nos acórdãos.

O programa trabalha em duas camadas:

1. recupera, com alta cobertura, expressões relacionadas à audiência e termos
   nominais/institucionais do arquivo operacional de variantes;
2. aplica regras transparentes para separar menções explícitas à audiência do
   processo, referências a outras audiências e candidatos que exigem revisão
   contextual (humana ou assistida por modelo de linguagem).

A saída principal preserva página, seção, ministro, trecho e método de decisão.
Nenhuma ocorrência nominal é convertida automaticamente em influência da
audiência.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd
import pymupdf


BASE = Path(__file__).resolve().parent
ACORDAOS = BASE / "acordaos"
RESULTADOS = BASE / "resultados"
TERMOS_ATIVOS = RESULTADOS / "termos_busca_acordaos_ativos.csv"
PARTICIPANTES = RESULTADOS / "participantes_relacional_limpo.csv"
CONTROLE = RESULTADOS / "controle_acordaos_todos.xlsx"
VERSAO_METODO = "0.8.0-unidade-frase-multiplos-alvos"
OCR_CACHE = RESULTADOS / "ocr_acordaos"
OCR_SCRIPT = BASE / "ocr_pdf_vision.swift"
LIMIAR_CARACTERES_POR_PAGINA = 200

PILOTO = [
    "AP_02_ADPF_101.pdf",       # 4 participantes; julgamento em 2009
    "AP_07_ADI_3937.pdf",       # 3 participantes; julgamento em 2017
    "AP_18_ADI_5072.pdf",       # 13 participantes; porte intermediário
    "AP_30_ADPF_708.pdf",       # 40 participantes; acórdão curto
    "AP_38_RE_1037396.pdf",     # 55 participantes; acórdão longo e multivotos
]

MINISTROS_CANONICOS = {
    "alexandre de moraes": "Alexandre de Moraes",
    "andre luiz de almeida mendonca": "André Mendonça",
    "andre mendonca": "André Mendonça",
    "ayres britto": "Ayres Britto",
    "carlos ayres britto": "Ayres Britto",
    "carmen lucia": "Cármen Lúcia",
    "celso de mello": "Celso de Mello",
    "cezar peluso": "Cezar Peluso",
    "cristiano zanin": "Cristiano Zanin",
    "dias toffoli": "Dias Toffoli",
    "edson fachin": "Edson Fachin",
    "ellen gracie": "Ellen Gracie",
    "eros grau": "Eros Grau",
    "flavio dino": "Flávio Dino",
    "gilmar mendes": "Gilmar Mendes",
    "joaquim barbosa": "Joaquim Barbosa",
    "kassio nunes marques": "Nunes Marques",
    "luiz fux": "Luiz Fux",
    "marco aurelio": "Marco Aurélio",
    "menezes direito": "Menezes Direito",
    "nunes marques": "Nunes Marques",
    "ricardo lewandowski": "Ricardo Lewandowski",
    "roberto barroso": "Luís Roberto Barroso",
    "luiz roberto barroso": "Luís Roberto Barroso",
    "luis roberto barroso": "Luís Roberto Barroso",
    "rosa weber": "Rosa Weber",
    "sepulveda pertence": "Sepúlveda Pertence",
}

PADROES_OUTRA_AUDIENCIA = [
    r"poder legislativo.{0,180}audiencias? publicas?",
    r"audiencias? publicas?.{0,180}poder legislativo",
    r"congresso nacional.{0,180}audiencias? publicas?",
    r"audiencias? publicas?.{0,180}congresso nacional",
    r"camara dos deputados.{0,180}audiencias? publicas?",
    r"senado federal.{0,180}audiencias? publicas?",
    r"assembleia legislativa.{0,180}audiencias? publicas?",
    r"lei .{0,120}editada pelo poder legislativo apos .{0,80}audiencias? publicas?",
    r"marco civil .{0,180}(?:passou por|apos) .{0,100}audiencias? publicas?",
    r"lei .{0,120}passou por .{0,100}audiencias? publicas?",
]

PADROES_AUDIENCIA_DO_PROCESSO = [
    r"determinei .{0,80}audiencia publica",
    r"convoquei .{0,80}audiencia publica",
    r"design(?:ei|ada|ou) .{0,80}audiencia publica",
    r"realiz(?:ei|ada|ou|ou-se) .{0,80}audiencia publica",
    r"audiencia publica .{0,160}(?:nest[ae]s? autos|nesta acao|neste processo)",
    r"audiencia publica .{0,180}(?:especialistas|expositores|experts|autoridades) ouvid",
    r"audiencia publica .{0,200}(?:transcricao|depoimentos|manifestaram-se|palestrantes)",
    r"(?:relatos|dados|opinioes|exposicoes|argumentos) apresentad[oa]s? .{0,80}audiencia publica",
    r"(?:exposicoes|manifestacoes) feit[oa]s? .{0,80}audiencia publica",
    r"apos a realizacao da audiencia publica",
    r"realizacao de audiencia publica .{0,140}(?:nos termos|presente acao|presentes autos)",
    r"audiencia publica .{0,100}(?:ocorreu|realizada) em \d",
    r"audiencia publica realizada pelo supremo tribunal",
    r"audiencia publica no stf",
    r"audiencia publica .{0,80}nesta corte",
    r"\bna audiencia publica\b",
    r"\bdurante a audiencia publica\b",
    r"\bao longo da audiencia publica\b",
    r"\breferida audiencia publica\b",
    r"\bda audiencia publica\b",
    r"audiencia publica .{0,100}convocada pelo relator",
    r"audiencias? publicas? realizadas? nestes autos",
    r"audiencia publica realizada nest[ae] (?:adpf|adi|ado|re|are|acao|processo)",
]

REGRAS_EXCLUSAO_PROCESSUAL = [
    (
        "EXC-AMICUS",
        "menção expressa a amicus curiae no mesmo parágrafo",
        [
            r"\bamicus curiae\b", r"\bamici curiae\b",
            r"\bam\s*curiae\b", r"\bam\s+curiae\b",
            r"\bamig[oa]s? da corte\b",
        ],
    ),
    (
        "EXC-PECA-PET",
        "enumeração documental de peças e petições no mesmo parágrafo",
        [
            r"\bpeca\s+n?[ºo.]?\s*\d{1,6}.{0,55}\bpet(?:icao)?\s*[.:nºo]*\s*\d+(?:/\d{2,4})?",
            r"\bpet(?:icao)?\s*[.:nºo]*\s*\d+(?:/\d{2,4})?.{0,55}\bpeca\s+n?[ºo.]?\s*\d{1,6}",
        ],
    ),
    (
        "EXC-TERCEIRO",
        "menção expressa à qualidade de terceiro no mesmo parágrafo",
        [
            r"\bna (?:qualidade|condicao) de terceir[oa]s?\b",
            r"\bcomo terceir[oa]s? interessad[oa]s?\b",
            r"\bterceir[oa]s? interessad[oa]s?\b",
            r"\binterveniente\b",
        ],
    ),
    (
        "EXC-PARTE",
        "menção expressa à qualidade de parte no mesmo parágrafo",
        [
            r"\bna (?:qualidade|condicao) de partes?\b",
            r"\bfigura(?:m)? como partes?\b",
        ],
    ),
]

ROTULOS_PROCESSUAIS_PROXIMOS = [
    (
        "EXC-REQUERENTE",
        "o alvo aparece próximo a marcador de quem propôs, protocolou ou requereu a ação",
        [
            r"\breqte\b", r"\brequerentes?\b", r"\bautor a\b",
            r"\bimpetrantes?\b", r"\brecorrentes?\b", r"\brecte\b",
            r"\bagravantes?\b", r"\bembargantes?\b", r"\breclamantes?\b",
            r"\bsuscitantes?\b", r"\bproponentes?\b",
        ],
    ),
    (
        "EXC-REPRESENTANTE-PROCESSUAL",
        "o alvo aparece próximo a marcador formal de representante processual",
        [
            r"\badv(?: a s)?\b",
        ],
    ),
    (
        "EXC-TERCEIRO",
        "o alvo aparece próximo a marcador formal de terceiro ou interessado",
        [
            r"\bintd[oa]\b", r"\bterceir[oa]s? interessad[oa]s?\b",
            r"\bintervenientes?\b",
        ],
    ),
    (
        "EXC-AMICUS",
        "o alvo aparece próximo a marcador formal de amicus curiae",
        [
            r"\bamicus curiae\b", r"\bamici curiae\b",
            r"\bam curiae\b", r"\bamig[oa]s? da corte\b",
        ],
    ),
    (
        "EXC-PARTE",
        "o alvo aparece próximo a marcador formal de outra parte processual",
        [
            r"\breqdo\b", r"\brequerid[oa]s?\b", r"\brecdo\b",
            r"\brecorrid[oa]s?\b", r"\bagravad[oa]s?\b",
            r"\bembargad[oa]s?\b", r"\breus?\b",
        ],
    ),
]

PADROES_REFERENCIA_BIBLIOGRAFICA = [
    r"\b(?:referencias bibliograficas|bibliografia)\b",
]

PADROES_CONTEUDO = [
    "argument", "dados", "depoimento", "destac", "esclarec", "exposic",
    "inform", "manifest", "opiniao", "palestr", "relato", "sustent",
    "testemunho", "tese",
]

PADROES_COLETIVOS = [
    "especialistas", "experts", "expositores", "participantes", "palestrantes",
    "autoridades ouvidas", "pessoas ouvidas",
]

TIPOS_SECAO = [
    (r"^EMENTA\b", "Ementa"),
    (r"^ACORDAO\b", "Acórdão"),
    (r"^RELATORIO\b", "Relatório"),
    (r"^VOTO(?:\s*[-–—]\s*VISTA|\s+VISTA)\b", "Voto-vista"),
    (r"^VOTO(?:\s*[-–—]\s*VOGAL|\s+VOGAL)\b", "Voto-vogal"),
    (r"^ADITAMENTO AO VOTO\b", "Aditamento ao voto"),
    (r"^ANTECIPACAO AO VOTO\b", "Antecipação ao voto"),
    (r"^VOTO\b", "Voto"),
    (r"^ESCLARECIMENT", "Esclarecimentos"),
    (r"^OBSERVACAO", "Observação"),
    (r"^DEBATE", "Debates"),
    (r"^QUESTAO DE ORDEM", "Questão de ordem"),
    (r"^EXTRATO DE ATA", "Extrato de ata"),
]


@dataclass
class EstadoEstrutural:
    secao: str = "Parte não identificada"
    titulo: str = ""
    ministro: str = ""
    ministro_metodo: str = "não identificado"
    relator: str = ""


@dataclass
class Marcador:
    posicao: int
    secao: str | None = None
    titulo: str | None = None
    ministro: str | None = None
    ministro_metodo: str | None = None


@dataclass
class OcorrenciaTemporaria:
    pagina_pdf: int
    inicio: int
    fim: int
    termo_encontrado: str
    termo: dict[str, str]
    variantes: set[str] = field(default_factory=set)
    tipos_variantes: set[str] = field(default_factory=set)
    quantidade_mencoes_na_frase: int = 1


def sem_acentos(valor: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", valor)
        if not unicodedata.combining(c)
    )


def corrigir_confusoes_ocr_normalizadas(valor: str) -> str:
    """Corrige trocas gráficas conservadoras sem alterar o tamanho do texto."""
    correcoes = {
        "audiencla": "audiencia",
        "audlencia": "audiencia",
        "publlca": "publica",
        "pubiica": "publica",
    }
    for incorreto, correto in correcoes.items():
        valor = re.sub(rf"\b{incorreto}\b", correto, valor)
    return valor


def normalizar(valor: str) -> str:
    s = sem_acentos(str(valor or "")).casefold()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return corrigir_confusoes_ocr_normalizadas(s)


def normalizar_com_mapa(valor: str) -> tuple[str, list[int]]:
    caracteres: list[str] = []
    mapa: list[int] = []
    ultimo_espaco = True
    for indice, original in enumerate(valor):
        decomposicao = unicodedata.normalize("NFKD", original).casefold()
        uteis = [c for c in decomposicao if not unicodedata.combining(c)]
        for caractere in uteis:
            if caractere.isalnum():
                caracteres.append(caractere)
                mapa.append(indice)
                ultimo_espaco = False
            elif not ultimo_espaco:
                caracteres.append(" ")
                mapa.append(indice)
                ultimo_espaco = True
    if caracteres and caracteres[-1] == " ":
        caracteres.pop()
        mapa.pop()
    texto = corrigir_confusoes_ocr_normalizadas("".join(caracteres))
    return texto, mapa


def squish(valor: str) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def escrever_csv(caminho: Path, linhas: list[dict[str, object]], campos: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)


def canonizar_ministro(nome: str) -> str:
    nome = re.sub(r"\bPRESIDENTB\b", "PRESIDENTE", nome, flags=re.I)
    nome = re.sub(r"\bMELIO\b", "MELLO", nome, flags=re.I)
    limpo = re.sub(
        r"\b(?:RELATORA?|PRESIDENTE|REDATORA?|REVISORA?)\b.*$", "", nome,
        flags=re.I,
    )
    limpo = squish(limpo).strip(" -–—:(),.;")
    chave = normalizar(limpo)
    if chave in MINISTROS_CANONICOS:
        return MINISTROS_CANONICOS[chave]
    palavras = []
    for p in limpo.title().split():
        palavras.append(p.casefold() if normalizar(p) in {"da", "de", "do", "dos"} else p)
    return " ".join(palavras)


def extrair_relator(textos_iniciais: Iterable[str]) -> str:
    texto = "\n".join(textos_iniciais)
    padroes = [
        r"RELATOR\s*:\s*MIN\.\s*([^\n]{3,70})",
        r"RELATORA\s*:\s*MIN\.\s*([^\n]{3,70})",
        r"RELATOR\(A\)\s*:\s*MIN\.\s*([^\n]{3,70})",
    ]
    for padrao in padroes:
        achado = re.search(padrao, texto, re.I)
        if achado:
            return canonizar_ministro(achado.group(1))
    return ""


def detectar_ministro_linha(linha: str) -> str | None:
    texto = squish(linha)
    padroes = [
        r"(?:O SENHOR|A SENHORA)?\s*MINISTR[OA]\s+([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ\s.'’-]{2,60}?)(?=\s*(?:\(|[-–—:]|$))",
        r"VOTO\s+(?:DO SENHOR|DA SENHORA|DO|DA)\s+MINISTR[OA]\s+([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ\s.'’-]{2,60}?)(?=\s*(?:\(|[-–—:]|$))",
    ]
    for padrao in padroes:
        achado = re.search(padrao, texto)
        if achado:
            candidato = canonizar_ministro(achado.group(1))
            if normalizar(candidato) not in {"relator", "relatora", "presidente"}:
                return candidato
    return None


def detectar_secao_linha(linha: str) -> tuple[str, str] | None:
    titulo = squish(linha).strip(" -–—:.")
    if not titulo or len(titulo) > 130:
        return None
    letras = [c for c in titulo if c.isalpha()]
    proporcao_maiusculas = (
        sum(c.isupper() for c in letras) / len(letras) if letras else 0
    )
    normal = sem_acentos(titulo).upper()
    compacto = re.sub(r"[^A-Z]", "", normal)
    secoes_compactas = [
        ("RELATORIO", "Relatório"),
        ("ACORDAO", "Acórdão"),
        ("VOTOVISTA", "Voto-vista"),
        ("VOTOVOGAL", "Voto-vogal"),
        ("ADITAMENTOAOVOTO", "Aditamento ao voto"),
        ("ANTECIPACAOAOVOTO", "Antecipação ao voto"),
        ("VOTOSPRELIMINAR", "Voto sobre preliminar"),
        ("VOTOPRELIMINAR", "Voto sobre preliminar"),
        ("VOTO", "Voto"),
        ("OBSERVACAO", "Observação"),
        ("DEBATES", "Debates"),
        ("EXTRATODEATA", "Extrato de ata"),
    ]
    for cabecalho, secao in secoes_compactas:
        if compacto == cabecalho:
            return secao, titulo
    # Títulos compostos precisam estar graficamente destacados. Isso impede
    # que frases como "relatório do órgão" alterem o estado estrutural.
    if proporcao_maiusculas < 0.72:
        return None
    for padrao, secao in TIPOS_SECAO:
        if re.match(padrao, normal):
            return secao, titulo
    return None


def marcadores_pagina(texto: str) -> list[Marcador]:
    marcadores: list[Marcador] = []
    posicao = 0
    for linha in texto.splitlines(keepends=True):
        conteudo = linha.strip()
        secao = detectar_secao_linha(conteudo)
        ministro = detectar_ministro_linha(conteudo)
        if secao or ministro:
            marcadores.append(Marcador(
                posicao=posicao,
                secao=secao[0] if secao else None,
                titulo=secao[1] if secao else None,
                ministro=ministro,
                ministro_metodo="cabeçalho ou fala no acórdão" if ministro else None,
            ))
        posicao += len(linha)
    return marcadores


def aplicar_marcadores(
    estado_inicial: EstadoEstrutural,
    marcadores: list[Marcador],
    posicao: int,
) -> EstadoEstrutural:
    estado = EstadoEstrutural(**vars(estado_inicial))
    for marcador in marcadores:
        if marcador.posicao > posicao:
            break
        if marcador.secao:
            estado.secao = marcador.secao
            estado.titulo = marcador.titulo or marcador.secao
            if marcador.secao in {"Ementa", "Acórdão", "Relatório"} and estado.relator:
                estado.ministro = estado.relator
                estado.ministro_metodo = "relator identificado nos metadados do acórdão"
        if marcador.ministro:
            estado.ministro = marcador.ministro
            estado.ministro_metodo = marcador.ministro_metodo or "cabeçalho do acórdão"
    if not estado.ministro and estado.relator and estado.secao in {"Ementa", "Acórdão", "Relatório", "Voto"}:
        estado.ministro = estado.relator
        estado.ministro_metodo = "relator identificado nos metadados do acórdão"
    return estado


def estado_ao_final(estado: EstadoEstrutural, marcadores: list[Marcador]) -> EstadoEstrutural:
    return aplicar_marcadores(estado, marcadores, 10**12)


def pagina_interna(pagina: pymupdf.Page) -> str:
    altura = pagina.rect.height
    candidatos: list[tuple[float, str]] = []
    for bloco in pagina.get_text("blocks"):
        x0, y0, x1, y1, texto = bloco[:5]
        valor = squish(texto)
        if re.fullmatch(r"\d{1,4}", valor) and y0 > altura * 0.78:
            candidatos.append((y0, valor))
    return max(candidatos, default=(0, ""))[1]


def texto_pagina_sem_camadas_duplicadas(pagina: pymupdf.Page) -> str:
    """Reconstrói o texto removendo blocos idênticos na mesma coordenada.

    Alguns inteiros teores recentes contêm duas camadas textuais sobrepostas.
    `page.get_text("text")` devolve as duas e duplica todas as ocorrências. A
    coordenada integra a chave para não eliminar repetições legítimas em
    posições distintas da página.
    """
    unicos: list[tuple[float, float, str]] = []
    vistos: set[tuple[float, float, float, float, str]] = set()
    for bloco in pagina.get_text("blocks", sort=True):
        x0, y0, x1, y1, texto = bloco[:5]
        chave = (
            round(float(x0), 1), round(float(y0), 1),
            round(float(x1), 1), round(float(y1), 1), squish(texto),
        )
        if not chave[-1] or chave in vistos:
            continue
        vistos.add(chave)
        unicos.append((float(y0), float(x0), texto.strip()))
    unicos.sort(key=lambda item: (round(item[0], 1), round(item[1], 1)))
    return "\n\n".join(item[2] for item in unicos)


def camada_textual_insuficiente(textos: list[str]) -> bool:
    if not textos:
        return True
    caracteres = sum(len(squish(texto)) for texto in textos)
    return caracteres / len(textos) < LIMIAR_CARACTERES_POR_PAGINA


def caminho_cache_ocr(caminho_pdf: Path) -> Path:
    return OCR_CACHE / f"{caminho_pdf.stem}.json"


def palavras_customizadas_ocr(termos: list[dict[str, str]]) -> list[str]:
    palavras = {
        termo.get("termo_busca", "").strip()
        for termo in termos
        if termo.get("termo_busca", "").strip()
    }
    palavras.update({"Audiência Pública", "Audiência Pública - Saúde"})
    return sorted(palavras)


def carregar_cache_ocr(
    caminho_pdf: Path,
    paginas_esperadas: int,
    palavras_esperadas: list[str],
) -> list[str] | None:
    cache = caminho_cache_ocr(caminho_pdf)
    if not cache.exists():
        return None
    dados = json.loads(cache.read_text(encoding="utf-8"))
    if (
        dados.get("arquivo_fonte") != caminho_pdf.name
        or int(dados.get("tamanho_fonte", -1)) != caminho_pdf.stat().st_size
        or int(dados.get("paginas_pdf", -1)) != paginas_esperadas
        or int(dados.get("paginas_processadas", -1)) != paginas_esperadas
        or sorted(dados.get("palavras_customizadas", [])) != palavras_esperadas
    ):
        return None
    paginas = dados.get("paginas", [])
    if len(paginas) != paginas_esperadas:
        return None
    return [str(pagina.get("texto", "")) for pagina in paginas]


def gerar_cache_ocr(
    caminho_pdf: Path,
    palavras_customizadas: list[str],
) -> None:
    if not OCR_SCRIPT.exists():
        raise FileNotFoundError(f"Rotina de OCR não encontrada: {OCR_SCRIPT}")
    OCR_CACHE.mkdir(parents=True, exist_ok=True)
    # Use as ferramentas Apple juntas, evitando misturar Swiftly e SDKs Apple.
    comando = ["/usr/bin/xcrun", "--toolchain", "default", "swift"]
    comando.extend([
        str(OCR_SCRIPT), str(caminho_pdf), str(caminho_cache_ocr(caminho_pdf)),
    ])
    ambiente = os.environ.copy()
    ambiente["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
    ambiente["CLANG_MODULE_CACHE_PATH"] = "/private/tmp/stf_swift_module_cache"
    arquivo_palavras = OCR_CACHE / f"{caminho_pdf.stem}.palavras.txt"
    arquivo_palavras.write_text(
        "\n".join(palavras_customizadas) + "\n",
        encoding="utf-8",
    )
    comando.extend(["0", str(arquivo_palavras)])
    print(f"  camada textual insuficiente; executando OCR em {caminho_pdf.name}")
    subprocess.run(comando, check=True, env=ambiente)


def textos_documento(
    caminho_pdf: Path,
    documento: pymupdf.Document,
    termos: list[dict[str, str]],
) -> tuple[list[str], str]:
    textos_nativos = [
        texto_pagina_sem_camadas_duplicadas(pagina) for pagina in documento
    ]
    if not camada_textual_insuficiente(textos_nativos):
        return textos_nativos, "camada textual nativa"
    palavras = palavras_customizadas_ocr(termos)
    textos_ocr = carregar_cache_ocr(caminho_pdf, len(documento), palavras)
    if textos_ocr is None:
        gerar_cache_ocr(caminho_pdf, palavras)
        textos_ocr = carregar_cache_ocr(caminho_pdf, len(documento), palavras)
    if textos_ocr is None or camada_textual_insuficiente(textos_ocr):
        raise RuntimeError(
            f"OCR ausente ou insuficiente para {caminho_pdf.name}; "
            "a análise foi interrompida para evitar falso zero."
        )
    return textos_ocr, "OCR Apple Vision"


def contexto_original(texto: str, inicio: int, fim: int, raio: int) -> str:
    esquerda = max(0, inicio - raio)
    direita = min(len(texto), fim + raio)
    return squish(texto[esquerda:direita])


def limites_bloco_original(texto: str, inicio: int, fim: int) -> tuple[int, int]:
    """Retorna os limites do parágrafo que contém a ocorrência.

    Quando o extrator não fornece uma linha em branco antes ou depois do alvo,
    o limite seguro é a borda da página. Isso evita truncar o parágrafo em uma
    janela arbitrária de caracteres.
    """
    # PyMuPDF pode representar a linha em branco como "\n \n". Considerar
    # somente "\n\n" juntava parágrafos distintos e fazia uma regra de papel
    # processual alcançar texto substantivo vizinho.
    separadores = list(re.finditer(r"\n[ \t]*\n", texto))
    anteriores = [m for m in separadores if m.end() <= inicio]
    posteriores = [m for m in separadores if m.start() >= fim]
    esquerda = anteriores[-1].end() if anteriores else 0
    direita = posteriores[0].start() if posteriores else len(texto)
    return esquerda, direita


def bloco_original(texto: str, inicio: int, fim: int) -> str:
    esquerda, direita = limites_bloco_original(texto, inicio, fim)
    return squish(texto[esquerda:direita])


ABREVIATURAS_SEM_FIM_DE_FRASE = {
    "adv", "art", "arts", "cap", "cf", "coord", "des", "doc", "dr", "dra",
    "ed", "exma", "exmo", "fl", "fls", "inc", "incs", "min", "n", "ns",
    "p", "pp", "proc", "prof", "profa", "rel", "sr", "sra", "v", "vol",
}


def ponto_encerra_frase(texto: str, posicao: int, esquerda: int) -> bool:
    """Distingue ponto final de abreviações frequentes em textos jurídicos."""
    if posicao <= esquerda:
        return False
    if (
        posicao > 0 and posicao + 1 < len(texto)
        and texto[posicao - 1].isdigit() and texto[posicao + 1].isdigit()
    ):
        return False
    prefixo = texto[esquerda:posicao]
    palavra = re.search(r"([A-Za-zÀ-ÖØ-öø-ÿ]+)$", prefixo)
    token = normalizar(palavra.group(1)) if palavra else ""
    if token in ABREVIATURAS_SEM_FIM_DE_FRASE or len(token) == 1:
        return False
    return True


def limites_frase_original(texto: str, inicio: int, fim: int) -> tuple[int, int]:
    """Retorna a frase que contém o alvo, sem perder o parágrafo de evidência."""
    esquerda_paragrafo, direita_paragrafo = limites_bloco_original(texto, inicio, fim)
    limites = [esquerda_paragrafo]
    posicao = esquerda_paragrafo
    while posicao < direita_paragrafo:
        caractere = texto[posicao]
        encerra = caractere in "!?" or (
            caractere == "." and ponto_encerra_frase(
                texto, posicao, limites[-1],
            )
        )
        if encerra:
            final = posicao + 1
            while final < direita_paragrafo and texto[final] in ".!?":
                final += 1
            proximo = final
            while proximo < direita_paragrafo and texto[proximo].isspace():
                proximo += 1
            if proximo < direita_paragrafo:
                limites.append(proximo)
            posicao = final
            continue
        posicao += 1
    limites.append(direita_paragrafo)
    for esquerda, direita in zip(limites, limites[1:]):
        if esquerda <= inicio < direita:
            return esquerda, direita
    return esquerda_paragrafo, direita_paragrafo


def intervalo_normalizado_no_bloco(
    bloco_bruto: str,
    inicio_original: int,
    fim_original: int,
) -> tuple[str, int, int]:
    """Localiza o alvo na representação normalizada do próprio parágrafo."""
    bloco_norm, mapa = normalizar_com_mapa(bloco_bruto)
    if not mapa:
        return bloco_norm, 0, 0
    indices = [
        indice for indice, posicao_original in enumerate(mapa)
        if inicio_original <= posicao_original < fim_original
    ]
    if indices:
        return bloco_norm, indices[0], indices[-1] + 1
    inicio_norm = len(normalizar(bloco_bruto[:inicio_original]))
    fim_norm = min(len(bloco_norm), inicio_norm + len(normalizar(
        bloco_bruto[inicio_original:fim_original]
    )))
    return bloco_norm, inicio_norm, fim_norm


def perto(texto_normalizado: str, inicio: int, fim: int, raio: int = 900) -> str:
    return texto_normalizado[max(0, inicio - raio):min(len(texto_normalizado), fim + raio)]


def classificar_audiencia_explicita(contexto_norm: str) -> tuple[str, str, str]:
    if any(re.search(p, contexto_norm) for p in PADROES_OUTRA_AUDIENCIA):
        return (
            "sem vínculo com a audiência pesquisada",
            "outra audiência pública",
            "O contexto atribui a audiência a outro órgão ou processo legislativo.",
        )
    if any(re.search(p, contexto_norm) for p in PADROES_AUDIENCIA_DO_PROCESSO):
        return (
            "vínculo explícito",
            "audiência pesquisada",
            "O próprio trecho relaciona a audiência aos autos, à convocação ou ao conteúdo colhido no processo.",
        )
    return (
        "vínculo explícito provável",
        "escopo indeterminado",
        "A expressão foi encontrada, mas a janela automática não basta para identificar qual audiência é mencionada.",
    )


def tipo_mencao(contexto_norm: str, tipo_alvo: str) -> str:
    if tipo_alvo in {"pessoa", "instituicao"}:
        return "menção nominal ou institucional"
    tem_conteudo = any(p in contexto_norm for p in PADROES_CONTEUDO)
    tem_coletivo = any(p in contexto_norm for p in PADROES_COLETIVOS)
    if tem_conteudo and tem_coletivo:
        return "conteúdo da audiência e referência coletiva"
    if tem_conteudo:
        return "conteúdo ou argumento da audiência"
    if tem_coletivo:
        return "referência coletiva aos participantes"
    return "registro procedimental da audiência"


def uso_no_acordao(secao: str, classificacao: str, tipo: str) -> str:
    if classificacao == "sem vínculo com a audiência pesquisada":
        return "fora do objeto da pesquisa"
    if "conteúdo" in tipo or "argumento" in tipo:
        if secao == "Relatório":
            return "relato ou contextualização"
        if secao.startswith("Voto") or secao in {"Aditamento ao voto", "Esclarecimentos", "Debates"}:
            return "possível uso na fundamentação; revisar adoção, crítica ou descrição"
    if secao == "Ementa":
        return "síntese no enunciado do acórdão"
    return "registro procedimental ou contextual"


def exclusao_processual_no_paragrafo(
    paragrafo_norm: str,
) -> tuple[str, str] | None:
    """Detecta contextos negativos somente na unidade paragráfica do alvo.

    A restrição ao parágrafo impede que um papel processual mencionado em
    outra passagem da mesma página contamine uma referência substantiva.
    """
    for codigo, descricao, padroes in REGRAS_EXCLUSAO_PROCESSUAL:
        if any(re.search(padrao, paragrafo_norm) for padrao in padroes):
            return codigo, descricao
    return None


def exclusao_papel_processual_proximo(
    paragrafo_norm: str,
    inicio_alvo: int,
    fim_alvo: int,
    raio: int = 180,
) -> tuple[str, str] | None:
    """Classifica o papel processual cujo marcador é o mais próximo do alvo."""
    rotulos_anteriores: list[tuple[int, int, str, str]] = []
    rotulos_posteriores: list[tuple[int, int, str, str]] = []
    for codigo, descricao, padroes in ROTULOS_PROCESSUAIS_PROXIMOS:
        for padrao in padroes:
            for achado in re.finditer(padrao, paragrafo_norm):
                if achado.end() <= inicio_alvo:
                    distancia = inicio_alvo - achado.end()
                    intervalo = paragrafo_norm[achado.end():inicio_alvo]
                    if len(intervalo.split()) <= 1:
                        rotulos_anteriores.append(
                            (distancia, achado.start(), codigo, descricao)
                        )
                elif achado.start() >= fim_alvo:
                    distancia = achado.start() - fim_alvo
                    intervalo = paragrafo_norm[fim_alvo:achado.start()]
                    if len(intervalo.split()) <= 1:
                        rotulos_posteriores.append(
                            (distancia, achado.start(), codigo, descricao)
                        )
                else:
                    rotulos_anteriores.append((0, achado.start(), codigo, descricao))
    rotulos = rotulos_anteriores or rotulos_posteriores
    if rotulos:
        distancia, _, codigo, descricao = min(
            rotulos, key=lambda item: (item[0], -item[1])
        )
        if distancia <= raio:
            return codigo, descricao

    antes = paragrafo_norm[max(0, inicio_alvo - 220):inicio_alvo]
    depois = paragrafo_norm[fim_alvo:min(len(paragrafo_norm), fim_alvo + 180)]
    if re.search(
        r"\b(?:acao|processo|pedido|recurso|mandado)\b.{0,100}"
        r"\b(?:ajuizad[oa]|propost[oa]|protocolad[oa]|impetrad[oa]|requerid[oa])\b"
        r".{0,80}\b(?:por|pela|pelo)\b\s*$",
        antes,
    ) or re.search(
        r"^.{0,80}\b(?:ajuizou|propos|protocolou|impetrou|requereu|aforou)\b"
        r".{0,80}\b(?:acao|processo|pedido|recurso|mandado)\b",
        depois,
    ):
        return (
            "EXC-REQUERENTE",
            "o texto próximo identifica o alvo como quem propôs, protocolou ou requereu a ação",
        )
    if re.search(
        r"^.{0,120}\b(?:legitimidade ativa|legitimad[oa]s? para propor|"
        r"responsavel pelo ajuizamento|proponente da acao)\b",
        depois,
    ):
        return (
            "EXC-REQUERENTE",
            "o texto próximo identifica o alvo pelo papel ativo na propositura da ação",
        )
    return None


def exclusao_referencia_bibliografica_proxima(
    paragrafo_norm: str,
    inicio_alvo: int,
    fim_alvo: int,
    raio: int = 260,
) -> tuple[str, str] | None:
    """Detecta referências bibliográficas próximas ao alvo, sem usar a página toda."""
    antes = paragrafo_norm[max(0, inicio_alvo - raio):inicio_alvo]
    depois = paragrafo_norm[fim_alvo:min(len(paragrafo_norm), fim_alvo + raio)]
    janela = antes + " alvo " + depois
    if any(re.search(padrao, janela) for padrao in PADROES_REFERENCIA_BIBLIOGRAFICA):
        return (
            "EXC-BIBLIOGRAFIA",
            "o alvo aparece em referência próxima a livro, artigo ou outra publicação",
        )

    antes_curto = antes[-140:]
    depois_curto = depois[:180]
    alvo_como_autor = bool(re.search(
        r"\b(?:livro|obra|artigo|paper|ensaio|capitulo|manual|tratado|"
        r"dissertacao|tese de doutorado|tese doctoral)\s+"
        r"(?:de|do|da|publicad[oa] por|escrit[oa] por|assinad[oa] por)\s*$",
        antes_curto,
    ))
    alvo_descrito_como_autor = bool(re.search(
        r"^.{0,45}\b(?:autor(?:a)?|organizad(?:or|ora)|editor(?:a)?)\b"
        r".{0,35}\b(?:livro|obra|artigo|paper|ensaio|capitulo|manual|tratado)\b",
        depois_curto,
    ))
    citacao_direcional = bool(
        re.search(r"\b(?:apud|op cit|ibidem|ibid|idem)\b.{0,70}$", antes_curto)
        or re.search(
            r"^.{0,130}\b(?:entrevista concedida a revista|publicad[oa] na revista|"
            r"publicad[oa] no journal|disponivel em|acesso em|doi|isbn)\b",
            depois_curto,
        )
    )
    dados_editoriais_ao_redor = bool(
        re.search(
            r"\b(?:norma tecnica|manual|tratado|livro|obra|artigo|capitulo)\b"
            r".{0,100}$",
            antes_curto,
        )
        and re.search(r"^.{0,120}\b(?:ed|edicao|editora|doi|isbn)\b", depois_curto)
    )
    if alvo_como_autor or alvo_descrito_como_autor or citacao_direcional or dados_editoriais_ao_redor:
        return (
            "EXC-BIBLIOGRAFIA",
            "o alvo aparece em referência próxima a livro, artigo ou outra publicação",
        )
    return None


def local_simplificado(secao: str, ministro: str, relator: str) -> str:
    """Reduz o local às três categorias adotadas para a análise dos votos."""
    if secao == "Relatório":
        return "Relatório"
    if relator and normalizar(ministro) == normalizar(relator):
        return "Voto do Relator"
    return "Voto"


def localizar_audiencia_proxima(
    texto_norm: str,
    inicio: int,
    fim: int,
    raio: int = 1300,
) -> tuple[int | None, str | None]:
    melhor: tuple[int, int] | None = None
    for achado in re.finditer(r"\baudiencias? publicas?\b", texto_norm):
        distancia = min(abs(achado.start() - fim), abs(inicio - achado.end()))
        if distancia <= raio and (melhor is None or distancia < melhor[0]):
            melhor = (distancia, achado.start())
    if melhor is None:
        return None, None
    pos = melhor[1]
    contexto = perto(texto_norm, pos, pos + len("audiencia publica"), 900)
    _, escopo, _ = classificar_audiencia_explicita(contexto)
    return melhor[0], escopo


def carregar_metadados() -> dict[str, dict[str, object]]:
    quadro = pd.read_excel(CONTROLE)
    saida: dict[str, dict[str, object]] = {}
    for linha in quadro.to_dict(orient="records"):
        arquivo = str(linha.get("arquivo_pdf") or "").strip()
        if not arquivo or arquivo == "nan":
            continue
        data_julgamento = linha.get("data_julgamento_sinal")
        data_texto = "" if pd.isna(data_julgamento) else str(data_julgamento)
        ano = ""
        achado_ano = re.search(r"\b(19|20)\d{2}\b", data_texto)
        if achado_ano:
            ano = achado_ano.group(0)
        numero = linha.get("numero")
        if isinstance(numero, float) and numero.is_integer():
            numero = int(numero)
        saida[arquivo] = {
            "numero_audiencia": int(linha["numero_audiencia"]),
            "processo": f"{linha.get('classe', '')} {numero}",
            "classe": str(linha.get("classe") or ""),
            "numero_processo": str(numero or ""),
            "data_julgamento": data_texto,
            "ano_julgamento": ano,
            "url_processo": str(linha.get("url_processo") or ""),
            "url_acordao": str(linha.get("url_pdf_final") or linha.get("url_integral") or ""),
        }
    return saida


def carregar_fontes_participantes() -> dict[tuple[int, str, str], dict[str, str]]:
    fontes: dict[tuple[int, str, str], dict[str, str]] = {}
    if not PARTICIPANTES.exists():
        return fontes
    for linha in ler_csv(PARTICIPANTES):
        ap = int(linha["numero_audiencia"])
        for tipo, campo in [("pessoa", "pessoa"), ("instituicao", "instituicao")]:
            valor = linha.get(campo, "")
            if not valor:
                continue
            fontes.setdefault((ap, tipo, normalizar(valor)), {
                "arquivos_fontes_participacao": linha.get("arquivos_fontes", ""),
                "paginas_fontes_participacao": linha.get("paginas_fontes", ""),
                "evidencia_participacao": linha.get("evidencia_exemplo", ""),
            })
    return fontes


def contar_participantes() -> dict[int, int]:
    por_ap: dict[int, set[str]] = defaultdict(set)
    if not PARTICIPANTES.exists():
        return {}
    for linha in ler_csv(PARTICIPANTES):
        if linha.get("pessoa"):
            por_ap[int(linha["numero_audiencia"])].add(normalizar(linha["pessoa"]))
    return {ap: len(nomes) for ap, nomes in por_ap.items()}


def arquivos_de_fala(audiencia: int) -> list[Path]:
    pasta = BASE / "documentos_audiencias" / f"AP_{audiencia:02d}"
    if not pasta.exists():
        return []
    prioritarios = []
    for caminho in pasta.iterdir():
        nome = normalizar(caminho.stem)
        if caminho.suffix.casefold() != ".pdf":
            continue
        if any(marcador in nome for marcador in ("transcri", "taquig", "notas", "material dos expositores")):
            prioritarios.append(caminho)
    return sorted(prioritarios)


def carregar_paginas_fontes(
    audiencia: int,
) -> list[tuple[str, int, str, str, list[int]]]:
    paginas: list[tuple[str, int, str, str, list[int]]] = []
    for caminho in arquivos_de_fala(audiencia):
        documento = pymupdf.open(caminho)
        for numero, pagina in enumerate(documento, 1):
            texto = texto_pagina_sem_camadas_duplicadas(pagina)
            texto_norm, mapa = normalizar_com_mapa(texto)
            if texto_norm:
                paginas.append((str(caminho.relative_to(BASE)), numero, texto, texto_norm, mapa))
        documento.close()
    return paginas


def melhor_trecho_fonte(
    paginas: list[tuple[str, int, str, str, list[int]]],
    variantes: list[str],
) -> dict[str, object]:
    melhor: tuple[int, dict[str, object]] | None = None
    termos = sorted({normalizar(v) for v in variantes if normalizar(v)}, key=len, reverse=True)
    for arquivo, pagina, texto, texto_norm, mapa in paginas:
        for termo in termos:
            padrao = re.compile(rf"(?<![a-z0-9]){re.escape(termo)}(?![a-z0-9])")
            for achado in padrao.finditer(texto_norm):
                inicio = mapa[achado.start()]
                fim = mapa[achado.end() - 1] + 1
                vizinhanca_norm = perto(texto_norm, achado.start(), achado.end(), 220)
                pontuacao = 10
                if any(x in vizinhanca_norm for x in (
                    "o senhor", "a senhora", "expositor", "expositora", "representante",
                )):
                    pontuacao += 8
                if any(x in normalizar(arquivo) for x in ("transcri", "taquig", "notas")):
                    pontuacao += 5
                # Favorece cabeçalhos seguidos de fala, não índices nominais.
                depois = texto[fim:min(len(texto), fim + 100)]
                if re.search(r"\s*\([^)]{0,100}\)?\s*[-–—:]", depois):
                    pontuacao += 6
                trecho = squish(texto[max(0, inicio - 260):min(len(texto), fim + 1800)])
                candidato = {
                    "arquivo_fonte_audiencia": arquivo,
                    "pagina_fonte_audiencia": pagina,
                    "trecho_fonte_audiencia": trecho,
                }
                if melhor is None or pontuacao > melhor[0]:
                    melhor = (pontuacao, candidato)
                if pontuacao >= 29:
                    return candidato
    return melhor[1] if melhor else {}


def enriquecer_com_fontes_da_audiencia(
    linhas: list[dict[str, object]],
    termos_ap: dict[int, list[dict[str, str]]],
) -> None:
    variantes_por_alvo: dict[tuple[int, str], list[str]] = defaultdict(list)
    for ap, termos in termos_ap.items():
        if ap == 0:
            continue
        for termo in termos:
            if termo["tipo_alvo"] not in {"pessoa", "instituicao"}:
                continue
            if termo["tipo_variante"] in {
                "nome_completo", "nome_sem_iniciais", "instituicao_completa",
            }:
                variantes_por_alvo[(ap, termo["alvo_id"])].append(termo["termo_busca"])

    paginas_por_ap: dict[int, list[tuple[str, int, str, str, list[int]]]] = {}
    achados: dict[tuple[int, str], dict[str, object]] = {}
    alvos = sorted({
        (int(linha["audiencia"]), detalhe["alvo_id"])
        for linha in linhas
        for detalhe in linha.get("_alvos_detalhados", [])
        if detalhe["tipo_alvo"] in {"pessoa", "instituicao"}
        and linha["status_revisao"] == "pendente"
    })
    for audiencia, alvo_id in alvos:
        if audiencia not in paginas_por_ap:
            print(f"  carregando fontes da AP {audiencia} para comparação contextual")
            paginas_por_ap[audiencia] = carregar_paginas_fontes(audiencia)
        variantes = variantes_por_alvo.get((audiencia, alvo_id), [])
        achados[(audiencia, alvo_id)] = melhor_trecho_fonte(
            paginas_por_ap[audiencia], variantes,
        )

    for linha in linhas:
        fontes_linha: list[tuple[str, dict[str, object]]] = []
        for detalhe in linha.get("_alvos_detalhados", []):
            fonte = achados.get((int(linha["audiencia"]), detalhe["alvo_id"]), {})
            if fonte:
                fontes_linha.append((detalhe["alvo_canonico"], fonte))
        linha.update({
            "arquivo_fonte_audiencia": juntar_unicos(
                fonte.get("arquivo_fonte_audiencia", "")
                for _, fonte in fontes_linha
            ),
            "pagina_fonte_audiencia": juntar_unicos(
                f"{alvo}: {fonte.get('pagina_fonte_audiencia', '')}"
                for alvo, fonte in fontes_linha
                if fonte.get("pagina_fonte_audiencia", "") != ""
            ),
            "trecho_fonte_audiencia": juntar_unicos(
                f"{alvo}: {fonte.get('trecho_fonte_audiencia', '')}"
                for alvo, fonte in fontes_linha
                if fonte.get("trecho_fonte_audiencia", "")
            ),
        })


def termos_por_audiencia() -> dict[int, list[dict[str, str]]]:
    por_ap: dict[int, list[dict[str, str]]] = defaultdict(list)
    globais: list[dict[str, str]] = []
    for termo in ler_csv(TERMOS_ATIVOS):
        if termo.get("usar_na_busca", "sim") != "sim":
            continue
        if termo["tipo_alvo"] == "audiencia_publica" or not termo["numero_audiencia"]:
            globais.append(termo)
        else:
            por_ap[int(termo["numero_audiencia"])].append(termo)
    for ap in list(por_ap):
        por_ap[ap] = globais + por_ap[ap]
    por_ap[0] = globais
    return por_ap


def ocorrencias_pagina(
    texto: str,
    termos: list[dict[str, str]],
    pagina_pdf: int,
) -> list[OcorrenciaTemporaria]:
    texto_norm, mapa = normalizar_com_mapa(texto)
    if not texto_norm or not mapa:
        return []
    por_chave: dict[tuple[int, int, str, str], OcorrenciaTemporaria] = {}
    for termo in termos:
        procurado = termo["termo_normalizado"]
        if not procurado:
            continue
        padrao = re.compile(rf"(?<![a-z0-9]){re.escape(procurado)}(?![a-z0-9])")
        for achado in padrao.finditer(texto_norm):
            inicio = mapa[achado.start()]
            fim = mapa[achado.end() - 1] + 1
            original_encontrado = texto[inicio:fim]
            if termo["tipo_variante"] == "sigla_explicita":
                letras = "".join(c for c in original_encontrado if c.isalpha())
                # A busca normalizada não pode transformar palavras comuns em
                # siglas. Ex.: a sigla ITS não deve recuperar o pronome inglês
                # "its" em referências bibliográficas.
                if letras and not letras.isupper():
                    continue
            chave = (inicio, fim, termo["tipo_alvo"], termo["alvo_id"])
            if chave not in por_chave:
                por_chave[chave] = OcorrenciaTemporaria(
                    pagina_pdf=pagina_pdf,
                    inicio=inicio,
                    fim=fim,
                    termo_encontrado=original_encontrado,
                    termo=termo,
                )
            por_chave[chave].variantes.add(termo["termo_busca"])
            por_chave[chave].tipos_variantes.add(termo["tipo_variante"])
    ordenadas = sorted(
        por_chave.values(), key=lambda o: (o.termo["alvo_id"], o.inicio, -o.fim)
    )
    consolidadas: list[OcorrenciaTemporaria] = []
    for ocorrencia in ordenadas:
        anterior = consolidadas[-1] if consolidadas else None
        if (
            anterior
            and anterior.termo["alvo_id"] == ocorrencia.termo["alvo_id"]
            and ocorrencia.inicio < anterior.fim
        ):
            anterior.inicio = min(anterior.inicio, ocorrencia.inicio)
            anterior.fim = max(anterior.fim, ocorrencia.fim)
            anterior.termo_encontrado = texto[anterior.inicio:anterior.fim]
            anterior.variantes.update(ocorrencia.variantes)
            anterior.tipos_variantes.update(ocorrencia.tipos_variantes)
        else:
            consolidadas.append(ocorrencia)
    # Primeiro, repetimos a busca por todos os alvos, mas consolidamos as
    # repetições literais do mesmo alvo dentro da mesma frase. Alvos distintos
    # na frase serão reunidos depois da classificação individual, preservando
    # pessoa, instituição e as regras acionadas por cada um.
    por_frase_e_alvo: dict[tuple[int, int, str, str], OcorrenciaTemporaria] = {}
    for ocorrencia in sorted(
        consolidadas, key=lambda o: (o.inicio, o.fim, o.termo["alvo_id"])
    ):
        esquerda, direita = limites_frase_original(
            texto, ocorrencia.inicio, ocorrencia.fim,
        )
        chave = (
            esquerda,
            direita,
            ocorrencia.termo["tipo_alvo"],
            normalizar(ocorrencia.termo["termo_canonico"]),
        )
        existente = por_frase_e_alvo.get(chave)
        if existente is None:
            por_frase_e_alvo[chave] = ocorrencia
            continue
        existente.quantidade_mencoes_na_frase += 1
        existente.variantes.update(ocorrencia.variantes)
        existente.tipos_variantes.update(ocorrencia.tipos_variantes)
    return sorted(
        por_frase_e_alvo.values(), key=lambda o: (o.inicio, o.fim, o.termo["alvo_id"])
    )


def juntar_unicos(valores: Iterable[object]) -> str:
    unicos: list[str] = []
    for valor in valores:
        texto = str(valor or "").strip()
        if texto and texto not in unicos:
            unicos.append(texto)
    return " | ".join(unicos)


def tipos_alvo_linha(linha: dict[str, object]) -> set[str]:
    return {
        item.strip() for item in str(linha.get("tipo_alvo", "")).split("|")
        if item.strip()
    }


def tem_tipo_alvo(linha: dict[str, object], tipo: str) -> bool:
    return tipo in tipos_alvo_linha(linha)


def tem_regra(linha: dict[str, object], regra: str) -> bool:
    return regra in {
        item.strip() for item in str(linha.get("regra_decisao", "")).split("|")
        if item.strip()
    }


def tem_valor_composto(linha: dict[str, object], campo: str, valor: str) -> bool:
    return valor in {
        item.strip() for item in str(linha.get(campo, "")).split("|")
        if item.strip()
    }


def consolidar_linhas_mesma_frase(
    linhas: list[dict[str, object]],
    numero_audiencia: int,
    nome_acordao: str,
) -> list[dict[str, object]]:
    """Produz uma linha por frase, reunindo todos os alvos nela recuperados."""
    grupos: dict[tuple[object, str, str], list[dict[str, object]]] = defaultdict(list)
    for linha in linhas:
        chave = (
            linha["pagina_pdf"], normalizar(str(linha["frase"])),
            normalizar(str(linha["trecho"])),
        )
        grupos[chave].append(linha)

    resultado: list[dict[str, object]] = []
    for chave, grupo in grupos.items():
        base = dict(grupo[0])
        detalhes: list[dict[str, str]] = []
        vistos: set[tuple[str, str]] = set()
        for linha in grupo:
            detalhe = {
                "tipo_alvo": str(linha["tipo_alvo"]),
                "alvo_id": str(linha["alvo_id"]),
                "alvo_canonico": str(linha["alvo_canonico"]),
            }
            chave_alvo = (detalhe["tipo_alvo"], detalhe["alvo_id"])
            if chave_alvo not in vistos:
                vistos.add(chave_alvo)
                detalhes.append(detalhe)
        base["_alvos_detalhados"] = detalhes
        base["quantidade_alvos_na_frase"] = len(detalhes)
        mencoes_por_alvo: dict[tuple[str, str], int] = {}
        for linha in grupo:
            chave_alvo = (str(linha["tipo_alvo"]), str(linha["alvo_id"]))
            mencoes_por_alvo[chave_alvo] = max(
                mencoes_por_alvo.get(chave_alvo, 0),
                int(linha.get("quantidade_mencoes_na_frase", 1)),
            )
        base["quantidade_mencoes_na_frase"] = sum(mencoes_por_alvo.values())
        base["repeticoes_mesmo_alvo_na_frase_consolidadas"] = sum(
            max(0, quantidade - 1) for quantidade in mencoes_por_alvo.values()
        )

        for campo in (
            "termo_encontrado", "tipo_alvo", "alvo_id", "alvo_canonico",
            "pessoa", "instituicao", "qualificacao", "vinculo_audiencia",
            "escopo_audiencia", "tipo_mencao", "uso_no_acordao",
            "risco_falso_positivo_termo", "prioridade_termo",
            "variantes_acionadas", "tipos_variantes",
            "arquivos_fontes_participacao", "paginas_fontes_participacao",
            "evidencia_participacao",
        ):
            base[campo] = juntar_unicos(linha.get(campo, "") for linha in grupo)

        distancias = [
            int(linha["distancia_a_expressao_audiencia"])
            for linha in grupo
            if str(linha.get("distancia_a_expressao_audiencia", "")).isdigit()
        ]
        base["distancia_a_expressao_audiencia"] = min(distancias) if distancias else ""

        status = {str(linha["status_revisao"]) for linha in grupo}
        if len(status) == 1:
            base["status_revisao"] = next(iter(status))
        elif "Parte do corpus - automático" in status:
            base["status_revisao"] = "Parte do corpus - automático"
        elif "pendente" in status:
            base["status_revisao"] = "pendente"
        else:
            base["status_revisao"] = "Excluído do corpus - automático"

        regras = juntar_unicos(linha["regra_decisao"] for linha in grupo)
        if "pendente" in status and "Excluído do corpus - automático" in status:
            base["regra_decisao"] = juntar_unicos([
                "MULTIPLOS-ALVOS-PENDENTE", regras,
            ])
        else:
            base["regra_decisao"] = regras
        justificativas = []
        for linha in grupo:
            justificativas.append(
                f"{linha['alvo_canonico']}: {linha['justificativa_pre_classificacao']}"
            )
        base["justificativa_pre_classificacao"] = juntar_unicos(justificativas)
        base["metodo_recuperacao"] = (
            "busca normalizada por termo ativo; consolidação por frase"
        )
        resultado.append(base)

    resultado.sort(key=lambda linha: (
        int(linha["pagina_pdf"]), int(linha["_inicio_frase"]), int(linha["_fim_frase"]),
    ))
    for contador, linha in enumerate(resultado, 1):
        linha["ocorrencia_id"] = (
            f"AP{numero_audiencia:02d}-{nome_acordao}-{contador:05d}"
        )
    return resultado


def analisar_pdf(
    caminho: Path,
    metadado: dict[str, object],
    termos: list[dict[str, str]],
    fontes: dict[tuple[int, str, str], dict[str, str]],
    raio_contexto: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    documento = pymupdf.open(caminho)
    textos, metodo_extracao_texto = textos_documento(caminho, documento, termos)
    relator = extrair_relator(textos[:5])
    estado = EstadoEstrutural(relator=relator)
    if relator:
        estado.ministro = relator
        estado.ministro_metodo = "relator identificado nos metadados do acórdão"

    linhas: list[dict[str, object]] = []
    numero_audiencia = int(metadado["numero_audiencia"])
    contador = 0
    for indice_pagina, (pagina, texto) in enumerate(zip(documento, textos), 1):
        marcadores = marcadores_pagina(texto)
        texto_norm, mapa = normalizar_com_mapa(texto)
        for ocorrencia in ocorrencias_pagina(texto, termos, indice_pagina):
            contador += 1
            estado_ocorrencia = aplicar_marcadores(estado, marcadores, ocorrencia.inicio)
            inicio_norm = 0
            fim_norm = 0
            if mapa:
                # As posições normalizadas são usadas apenas para calcular
                # proximidade. A aproximação por busca do fragmento é segura
                # porque a classificação sempre conserva o texto original.
                termo_norm = normalizar(ocorrencia.termo_encontrado)
                busca_inicio = max(0, ocorrencia.inicio - 40)
                prefixo_norm = normalizar(texto[:busca_inicio])
                inicio_norm = texto_norm.find(termo_norm, len(prefixo_norm))
                if inicio_norm < 0:
                    inicio_norm = max(0, len(prefixo_norm))
                fim_norm = inicio_norm + len(termo_norm)

            contexto = contexto_original(texto, ocorrencia.inicio, ocorrencia.fim, raio_contexto)
            inicio_bloco, fim_bloco = limites_bloco_original(
                texto, ocorrencia.inicio, ocorrencia.fim,
            )
            inicio_frase, fim_frase = limites_frase_original(
                texto, ocorrencia.inicio, ocorrencia.fim,
            )
            bloco_bruto = texto[inicio_bloco:fim_bloco]
            bloco = squish(bloco_bruto)
            frase = squish(texto[inicio_frase:fim_frase])
            contexto_norm = perto(texto_norm, inicio_norm, fim_norm, 1000)
            bloco_norm, inicio_alvo_bloco, fim_alvo_bloco = intervalo_normalizado_no_bloco(
                bloco_bruto,
                ocorrencia.inicio - inicio_bloco,
                ocorrencia.fim - inicio_bloco,
            )
            tipo_alvo = ocorrencia.termo["tipo_alvo"]
            regra_decisao = ""
            status_revisao = "pendente"

            if tipo_alvo == "audiencia_publica":
                vinculo, escopo, justificativa = classificar_audiencia_explicita(bloco_norm)
                distancia_ap = 0
                if vinculo == "vínculo explícito":
                    regra_decisao = "AP-EXP-ALVO"
                    status_revisao = "Parte do corpus - automático"
                elif vinculo == "sem vínculo com a audiência pesquisada":
                    regra_decisao = "AP-EXP-OUTRA"
                    status_revisao = "Excluído do corpus - automático"
                else:
                    regra_decisao = "AP-EXP-PENDENTE"
            else:
                distancia_ap, escopo_proximo = localizar_audiencia_proxima(
                    texto_norm, inicio_norm, fim_norm,
                )
                exclusao = (
                    exclusao_papel_processual_proximo(
                        bloco_norm, inicio_alvo_bloco, fim_alvo_bloco,
                    )
                    or exclusao_referencia_bibliografica_proxima(
                        bloco_norm, inicio_alvo_bloco, fim_alvo_bloco,
                    )
                    or exclusao_processual_no_paragrafo(bloco_norm)
                )
                audiencia_no_paragrafo = bool(
                    re.search(r"\baudiencias? publicas?\b", bloco_norm)
                )
                if exclusao:
                    regra_decisao, motivo_exclusao = exclusao
                    vinculo = "sem vínculo demonstrável neste trecho"
                    if regra_decisao == "EXC-BIBLIOGRAFIA":
                        escopo = "referência bibliográfica excluída"
                    elif regra_decisao == "EXC-REQUERENTE":
                        escopo = "polo ativo processual excluído"
                    else:
                        escopo = "contexto processual excluído"
                    justificativa = (
                        f"Exclusão automática: {motivo_exclusao}. A regra foi aplicada "
                        "somente ao parágrafo que contém o alvo."
                    )
                    status_revisao = "Excluído do corpus - automático"
                elif audiencia_no_paragrafo:
                    vinculo_paragrafo, escopo_paragrafo, justificativa_paragrafo = (
                        classificar_audiencia_explicita(bloco_norm)
                    )
                    if escopo_paragrafo == "audiência pesquisada":
                        vinculo = "vínculo explícito"
                        escopo = "audiência pesquisada"
                        justificativa = (
                            "O alvo e a referência explícita à audiência do processo "
                            "aparecem no mesmo parágrafo; a atribuição individual ainda "
                            "deve ser confirmada."
                        )
                        regra_decisao = "ALVO-AP-MESMO-PARAGRAFO"
                    elif vinculo_paragrafo == "sem vínculo com a audiência pesquisada":
                        vinculo = vinculo_paragrafo
                        escopo = escopo_paragrafo
                        justificativa = justificativa_paragrafo
                        regra_decisao = "ALVO-OUTRA-AP-MESMO-PARAGRAFO"
                        status_revisao = "Excluído do corpus - automático"
                    else:
                        vinculo = "vínculo explícito provável"
                        escopo = "escopo indeterminado"
                        justificativa = (
                            "O alvo e uma expressão de audiência pública aparecem no "
                            "mesmo parágrafo, mas o escopo ainda requer revisão."
                        )
                        regra_decisao = "ALVO-AP-PENDENTE"
                elif distancia_ap is not None and escopo_proximo == "audiência pesquisada":
                    vinculo = "candidato a vínculo implícito"
                    escopo = "a revisar por comparação documental"
                    justificativa = (
                        "Há referência à audiência em outro parágrafo próximo; revisar "
                        "se a passagem nominal efetivamente retoma seu conteúdo."
                    )
                    regra_decisao = "ALVO-AP-OUTRO-PARAGRAFO"
                else:
                    vinculo = "candidato a vínculo implícito"
                    escopo = "a revisar por comparação documental"
                    justificativa = "A ocorrência nominal exige comparação com a transcrição para verificar se retoma a audiência."
                    regra_decisao = "ALVO-IMPLICITO-PENDENTE"

            tipo = tipo_mencao(contexto_norm, tipo_alvo)
            local_titulo = estado_ocorrencia.titulo or estado_ocorrencia.secao
            local = local_simplificado(
                estado_ocorrencia.secao,
                estado_ocorrencia.ministro,
                relator,
            )

            fonte = fontes.get((
                numero_audiencia,
                tipo_alvo,
                normalizar(ocorrencia.termo.get("pessoa") or ocorrencia.termo.get("instituicao") or ocorrencia.termo["termo_canonico"]),
            ), {})
            linhas.append({
                "ocorrencia_id": f"AP{numero_audiencia:02d}-{caminho.stem}-{contador:05d}",
                "audiencia": numero_audiencia,
                "processo": metadado["processo"],
                "classe": metadado["classe"],
                "numero_processo": metadado["numero_processo"],
                "data_julgamento": metadado["data_julgamento"],
                "ano": metadado["ano_julgamento"],
                "arquivo_acordao": caminho.name,
                "pagina_pdf": indice_pagina,
                "pagina_documento": pagina_interna(pagina),
                "ministro": estado_ocorrencia.ministro or "Não identificado automaticamente",
                "ministro_metodo": estado_ocorrencia.ministro_metodo,
                "local_tipo": local,
                "local_titulo": local_titulo,
                "local_no_acordao": local,
                "termo_encontrado": squish(ocorrencia.termo_encontrado),
                "tipo_alvo": tipo_alvo,
                "alvo_id": ocorrencia.termo["alvo_id"],
                "alvo_canonico": ocorrencia.termo["termo_canonico"],
                "pessoa": ocorrencia.termo.get("pessoa", ""),
                "instituicao": ocorrencia.termo.get("instituicao", ""),
                "qualificacao": ocorrencia.termo.get("qualificacao", ""),
                "vinculo_audiencia": vinculo,
                "escopo_audiencia": escopo,
                "tipo_mencao": tipo,
                "uso_no_acordao": uso_no_acordao(estado_ocorrencia.secao, vinculo, tipo),
                "distancia_a_expressao_audiencia": "" if distancia_ap is None else distancia_ap,
                "status_revisao": status_revisao,
                "regra_decisao": regra_decisao,
                "risco_falso_positivo_termo": ocorrencia.termo.get("risco_falso_positivo", ""),
                "prioridade_termo": ocorrencia.termo.get("prioridade", ""),
                "metodo_recuperacao": "busca normalizada por termo ativo",
                "metodo_extracao_texto": metodo_extracao_texto,
                "quantidade_mencoes_na_frase": ocorrencia.quantidade_mencoes_na_frase,
                "quantidade_alvos_na_frase": 1,
                "variantes_acionadas": " | ".join(sorted(ocorrencia.variantes)),
                "tipos_variantes": " | ".join(sorted(ocorrencia.tipos_variantes)),
                "frase": frase,
                "trecho": bloco,
                "contexto_ampliado": contexto,
                "justificativa_pre_classificacao": justificativa,
                "arquivos_fontes_participacao": fonte.get("arquivos_fontes_participacao", ""),
                "paginas_fontes_participacao": fonte.get("paginas_fontes_participacao", ""),
                "evidencia_participacao": fonte.get("evidencia_participacao", ""),
                "url_processo": metadado["url_processo"],
                "url_acordao": metadado["url_acordao"],
                "versao_metodo": VERSAO_METODO,
                "_inicio_frase": inicio_frase,
                "_fim_frase": fim_frase,
            })
        estado = estado_ao_final(estado, marcadores)
    linhas = consolidar_linhas_mesma_frase(
        linhas, numero_audiencia, caminho.stem,
    )
    documento.close()

    resumo = {
        "audiencia": numero_audiencia,
        "processo": metadado["processo"],
        "ano": metadado["ano_julgamento"],
        "arquivo_acordao": caminho.name,
        "paginas_pdf": len(textos),
        "relator_identificado": relator or "Não identificado automaticamente",
        "termos_ativos_aplicados": len(termos),
        "metodo_extracao_texto": metodo_extracao_texto,
        "ocorrencias_candidatas": len(linhas),
        "mencoes_explicitas_audiencia_pesquisada": sum(
            tem_tipo_alvo(x, "audiencia_publica")
            and tem_valor_composto(
                x, "vinculo_audiencia", "vínculo explícito",
            ) for x in linhas
        ),
        "referencias_explicitas_a_outras_audiencias": sum(
            tem_valor_composto(
                x, "escopo_audiencia", "outra audiência pública",
            ) for x in linhas
        ),
        "mencoes_explicitas_provaveis": sum(
            tem_valor_composto(
                x, "vinculo_audiencia", "vínculo explícito provável",
            ) for x in linhas
        ),
        "candidatos_vinculo_implicito": sum(
            tem_valor_composto(
                x, "vinculo_audiencia", "candidato a vínculo implícito",
            ) for x in linhas
        ),
        "ocorrencias_nominais_sem_vinculo_no_trecho": sum(
            tem_valor_composto(
                x, "vinculo_audiencia", "sem vínculo demonstrável neste trecho",
            ) for x in linhas
        ),
        "parte_corpus_automatico": sum(
            x["status_revisao"] == "Parte do corpus - automático" for x in linhas
        ),
        "excluido_corpus_automatico": sum(
            x["status_revisao"] == "Excluído do corpus - automático" for x in linhas
        ),
        "pendentes": sum(x["status_revisao"] == "pendente" for x in linhas),
        "excluidos_amicus": sum(tem_regra(x, "EXC-AMICUS") for x in linhas),
        "excluidos_partes_terceiros": sum(
            any(tem_regra(x, regra) for regra in {
                "EXC-PARTE", "EXC-TERCEIRO", "EXC-REPRESENTANTE-PROCESSUAL",
            }) for x in linhas
        ),
        "excluidos_representantes_processuais": sum(
            tem_regra(x, "EXC-REPRESENTANTE-PROCESSUAL") for x in linhas
        ),
        "excluidos_pecas_peticoes": sum(
            tem_regra(x, "EXC-PECA-PET") for x in linhas
        ),
        "excluidos_referencias_bibliograficas": sum(
            tem_regra(x, "EXC-BIBLIOGRAFIA") for x in linhas
        ),
        "excluidos_requerentes": sum(
            tem_regra(x, "EXC-REQUERENTE") for x in linhas
        ),
        "repeticoes_mesmo_alvo_na_frase_consolidadas": sum(
            int(x["repeticoes_mesmo_alvo_na_frase_consolidadas"]) for x in linhas
        ),
        "alvos_distintos_mesma_frase_consolidados": sum(
            max(0, int(x["quantidade_alvos_na_frase"]) - 1) for x in linhas
        ),
        "versao_metodo": VERSAO_METODO,
    }
    return linhas, resumo


def campos_ocorrencias() -> list[str]:
    return [
        "ocorrencia_id", "audiencia", "processo", "classe", "numero_processo",
        "data_julgamento", "ano", "arquivo_acordao", "pagina_pdf", "pagina_documento",
        "ministro", "ministro_metodo", "local_tipo", "local_titulo", "local_no_acordao",
        "termo_encontrado", "tipo_alvo", "alvo_id", "alvo_canonico", "pessoa",
        "instituicao", "qualificacao", "vinculo_audiencia", "escopo_audiencia",
        "tipo_mencao", "uso_no_acordao", "distancia_a_expressao_audiencia",
        "status_revisao", "regra_decisao", "risco_falso_positivo_termo", "prioridade_termo",
        "metodo_recuperacao", "metodo_extracao_texto",
        "quantidade_mencoes_na_frase", "quantidade_alvos_na_frase",
        "variantes_acionadas", "tipos_variantes", "frase", "trecho",
        "contexto_ampliado", "justificativa_pre_classificacao",
        "arquivos_fontes_participacao", "paginas_fontes_participacao",
        "evidencia_participacao", "url_processo", "url_acordao", "versao_metodo",
        "arquivo_fonte_audiencia", "pagina_fonte_audiencia", "trecho_fonte_audiencia",
    ]


def criar_pacotes_revisao(linhas: list[dict[str, object]], caminho: Path) -> None:
    instrucao = (
        "Classifique apenas esta ocorrência. Verifique se o trecho do acórdão retoma, "
        "atribui, discute ou utiliza conteúdo da audiência pública pesquisada. Não presuma "
        "vínculo pela coincidência do nome. Responda: vinculo_audiencia, tipo_uso, "
        "evidencia e justificativa; use indeterminado quando a prova for insuficiente."
    )
    with caminho.open("w", encoding="utf-8") as arquivo:
        for linha in linhas:
            if linha["status_revisao"] != "pendente":
                continue
            pacote = {
                "ocorrencia_id": linha["ocorrencia_id"],
                "instrucao": instrucao,
                "audiencia": linha["audiencia"],
                "processo": linha["processo"],
                "ministro_contexto": linha["ministro"],
                "local": linha["local_no_acordao"],
                "pagina_pdf": linha["pagina_pdf"],
                "pagina_documento": linha["pagina_documento"],
                "alvos": linha["alvo_canonico"],
                "tipos_alvo": linha["tipo_alvo"],
                "pessoa": linha["pessoa"],
                "instituicao": linha["instituicao"],
                "frase_alvo": linha["frase"],
                "paragrafo_completo_acordao": linha["trecho"],
                "contexto_ampliado": linha["contexto_ampliado"],
                "evidencia_de_participacao": linha["evidencia_participacao"],
                "fontes_da_audiencia": linha["arquivos_fontes_participacao"],
                "arquivo_fala_audiencia": linha["arquivo_fonte_audiencia"],
                "pagina_fala_audiencia": linha["pagina_fonte_audiencia"],
                "trecho_fala_audiencia": linha["trecho_fonte_audiencia"],
            }
            arquivo.write(json.dumps(pacote, ensure_ascii=False) + "\n")


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selecao = parser.add_mutually_exclusive_group()
    selecao.add_argument("--todos", action="store_true", help="analisa todos os PDFs disponíveis")
    selecao.add_argument(
        "--audiencias",
        nargs="+",
        type=int,
        help="analisa todos os acórdãos vinculados aos números de audiência informados",
    )
    selecao.add_argument("--acordaos", nargs="+", help="nomes de arquivos específicos em acordaos/")
    parser.add_argument(
        "--saida",
        type=Path,
        default=RESULTADOS / "piloto_mencoes_audiencias_final",
        help="diretório de saída dos CSVs e pacotes de revisão",
    )
    parser.add_argument("--contexto", type=int, default=900, help="caracteres antes/depois do achado")
    return parser.parse_args()


def selecionar_acordaos(
    args: argparse.Namespace,
    metadados: dict[str, dict[str, object]],
) -> tuple[list[str], str]:
    if args.todos:
        return [p.name for p in sorted(ACORDAOS.glob("*.pdf"))], "todos"
    if args.audiencias:
        solicitadas = set(args.audiencias)
        disponiveis = {
            int(meta["numero_audiencia"]) for meta in metadados.values()
        }
        inexistentes = sorted(solicitadas - disponiveis)
        if inexistentes:
            raise ValueError(
                "Audiências sem acórdão mapeado no controle: "
                + ", ".join(map(str, inexistentes))
            )
        nomes = [
            nome for nome, meta in metadados.items()
            if int(meta["numero_audiencia"]) in solicitadas
        ]
        nomes.sort(key=lambda nome: (
            int(metadados[nome]["numero_audiencia"]), nome,
        ))
        return nomes, "audiencias"
    if args.acordaos:
        return list(args.acordaos), "acordaos"
    return list(PILOTO), "piloto"


def main() -> None:
    args = argumentos()
    metadados = carregar_metadados()
    fontes = carregar_fontes_participantes()
    participantes_por_ap = contar_participantes()
    termos = termos_por_audiencia()

    nomes, modo_execucao = selecionar_acordaos(args, metadados)

    faltantes = [nome for nome in nomes if not (ACORDAOS / nome).exists()]
    sem_metadados = [nome for nome in nomes if nome not in metadados]
    if faltantes:
        raise FileNotFoundError(f"Acórdãos não encontrados: {', '.join(faltantes)}")
    if sem_metadados:
        raise ValueError(f"Acórdãos sem metadados no controle: {', '.join(sem_metadados)}")

    todas: list[dict[str, object]] = []
    resumos: list[dict[str, object]] = []
    for nome in nomes:
        meta = metadados[nome]
        ap = int(meta["numero_audiencia"])
        termos_ap = termos.get(ap, termos[0])
        print(f"Analisando {nome}: AP {ap}, {len(termos_ap)} termos ativos")
        ocorrencias, resumo = analisar_pdf(
            ACORDAOS / nome, meta, termos_ap, fontes, args.contexto,
        )
        todas.extend(ocorrencias)
        resumo["participantes_na_lista"] = participantes_por_ap.get(ap, 0)
        resumos.append(resumo)
        print(f"  candidatos: {len(ocorrencias)}")

    enriquecer_com_fontes_da_audiencia(todas, termos)

    args.saida.mkdir(parents=True, exist_ok=True)
    campos = campos_ocorrencias()
    escrever_csv(args.saida / "ocorrencias_classificadas.csv", todas, campos)

    mencoes_expressas = [
        linha for linha in todas if tem_tipo_alvo(linha, "audiencia_publica")
    ]

    alvos_contexto_explicito = [
        linha for linha in todas
        if tipos_alvo_linha(linha) - {"audiencia_publica"}
        and tem_valor_composto(linha, "vinculo_audiencia", "vínculo explícito")
    ]

    candidatos_implicitos = [
        linha for linha in todas
        if tem_valor_composto(
            linha, "vinculo_audiencia", "candidato a vínculo implícito",
        )
    ]

    mencoes_preliminares = [
        linha for linha in todas
        if linha["status_revisao"] in {"Parte do corpus - automático", "Parte do corpus"}
    ]

    pendentes = [linha for linha in todas if linha["status_revisao"] == "pendente"]
    escrever_csv(args.saida / "revisao_pendente.csv", pendentes, campos)

    campos_resumo = list(resumos[0]) if resumos else []
    escrever_csv(args.saida / "resumo_execucao.csv", resumos, campos_resumo)
    criar_pacotes_revisao(pendentes, args.saida / "pacotes_revisao.jsonl")

    manifesto = {
        "data_execucao": date.today().isoformat(),
        "versao_metodo": VERSAO_METODO,
        "modo_execucao": modo_execucao,
        "acordaos": nomes,
        "audiencias_solicitadas": sorted(set(args.audiencias or [])),
        "audiencias_analisadas": sorted({
            int(metadados[nome]["numero_audiencia"]) for nome in nomes
        }),
        "total_acordaos": len(nomes),
        "total_audiencias": len({
            int(metadados[nome]["numero_audiencia"]) for nome in nomes
        }),
        "arquivo_termos": str(TERMOS_ATIVOS.relative_to(BASE)),
        "arquivo_participantes": str(PARTICIPANTES.relative_to(BASE)),
        "contexto_caracteres": args.contexto,
        "total_ocorrencias": len(todas),
        "total_mencoes_expressas": len(mencoes_expressas),
        "total_alvos_em_contexto_explicito": len(alvos_contexto_explicito),
        "total_candidatos_vinculo_implicito": len(candidatos_implicitos),
        "total_mencoes_preliminares": len(mencoes_preliminares),
        "total_revisao_pendente": len(pendentes),
        "total_parte_corpus_automatico": sum(
            x["status_revisao"] == "Parte do corpus - automático" for x in todas
        ),
        "total_excluido_corpus_automatico": sum(
            x["status_revisao"] == "Excluído do corpus - automático" for x in todas
        ),
    }
    (args.saida / "manifesto_execucao.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saída: {args.saida}")
    print(f"Ocorrências candidatas: {len(todas)}")
    print(f"Menções preliminares: {len(mencoes_preliminares)}")
    print(f"Pendentes de revisão: {len(pendentes)}")


if __name__ == "__main__":
    main()
