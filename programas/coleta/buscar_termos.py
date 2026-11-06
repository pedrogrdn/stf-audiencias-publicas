#!/usr/bin/env python3
"""
Fase 2 opcional: busca termos nos PDFs já baixados.

Leia um termo por linha em termos.txt. O resultado é salvo em
resultados/resultado_busca.xlsx.
"""
from pathlib import Path
import re
import pandas as pd
import fitz  # PyMuPDF

BASE_DIR = Path(__file__).resolve().parent
PASTA_PDFS = BASE_DIR / "acordaos"
ARQUIVO_TERMOS = BASE_DIR / "termos.txt"
CONTROLE = BASE_DIR / "resultados" / "controle_acordaos_todos.xlsx"
SAIDA = BASE_DIR / "resultados" / "resultado_busca.xlsx"
CONTEXTO = 450  # caracteres antes e depois da ocorrência


def squish(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def carregar_termos():
    if not ARQUIVO_TERMOS.exists():
        raise FileNotFoundError("Não encontrei termos.txt na pasta do projeto.")
    termos = []
    for linha in ARQUIVO_TERMOS.read_text(encoding="utf-8").splitlines():
        t = linha.strip()
        if t and not t.startswith("#"):
            termos.append(t)
    if not termos:
        raise ValueError("termos.txt não contém nenhum termo de busca.")
    return termos


def main():
    termos = carregar_termos()
    resultados = []

    print(f"Buscando {len(termos)} termo(s) em PDFs de {PASTA_PDFS.name}/")

    for pdf in sorted(PASTA_PDFS.glob("*.pdf")):
        print(f"  {pdf.name}")
        doc = fitz.open(pdf)
        for pagina_idx, pagina in enumerate(doc, start=1):
            texto = squish(pagina.get_text("text"))
            if not texto:
                continue
            for termo in termos:
                padrao = re.compile(re.escape(termo), flags=re.IGNORECASE)
                for m in padrao.finditer(texto):
                    ini = max(0, m.start() - CONTEXTO)
                    fim = min(len(texto), m.end() + CONTEXTO)
                    resultados.append({
                        "arquivo_pdf": pdf.name,
                        "pagina_pdf": pagina_idx,
                        "termo_buscado": termo,
                        "termo_encontrado": m.group(0),
                        "trecho": texto[ini:fim],
                    })

    out = pd.DataFrame(resultados)

    # Acrescenta metadados da coleta quando disponíveis.
    if CONTROLE.exists() and not out.empty:
        ctrl = pd.read_excel(CONTROLE)
        colunas = [c for c in [
            "arquivo_pdf", "numero_audiencia", "classe", "numero",
            "incidente", "status_merito", "url_processo"
        ] if c in ctrl.columns]
        if "arquivo_pdf" in colunas:
            out = out.merge(ctrl[colunas].drop_duplicates("arquivo_pdf"), on="arquivo_pdf", how="left")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    out.to_excel(SAIDA, index=False)
    print(f"\nConcluído. Ocorrências: {len(out)}")
    print(f"Resultado: {SAIDA}")


if __name__ == "__main__":
    main()
