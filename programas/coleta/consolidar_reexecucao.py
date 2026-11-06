#!/usr/bin/env python3
"""Substitui audiências reexecutadas no resultado integral de forma atômica."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import date
from pathlib import Path

import analisar_mencoes_audiencias as analise


VERSAO_CONSOLIDADA = "0.6.1-consolidado-ap3-ap4"


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integral", type=Path, required=True)
    parser.add_argument("--atualizacao", type=Path, required=True)
    return parser.parse_args()


def ordenar_ocorrencias(linha: dict[str, str]) -> tuple[object, ...]:
    return (
        int(linha["audiencia"]),
        linha["arquivo_acordao"],
        int(linha["pagina_pdf"]),
        linha["ocorrencia_id"],
    )


def ordenar_resumo(linha: dict[str, str]) -> tuple[object, ...]:
    return int(linha["audiencia"]), linha["arquivo_acordao"]


def main() -> None:
    args = argumentos()
    integral = args.integral.resolve()
    atualizacao = args.atualizacao.resolve()
    manifesto_anterior = json.loads(
        (integral / "manifesto_execucao.json").read_text(encoding="utf-8")
    )
    manifesto_atualizacao = json.loads(
        (atualizacao / "manifesto_execucao.json").read_text(encoding="utf-8")
    )

    ocorrencias_anteriores = analise.ler_csv(
        integral / "ocorrencias_classificadas.csv"
    )
    ocorrencias_novas = analise.ler_csv(
        atualizacao / "ocorrencias_classificadas.csv"
    )
    resumos_anteriores = analise.ler_csv(integral / "resumo_execucao.csv")
    resumos_novos = analise.ler_csv(atualizacao / "resumo_execucao.csv")
    for linha in ocorrencias_anteriores:
        if not linha.get("metodo_extracao_texto"):
            linha["metodo_extracao_texto"] = "camada textual nativa"
    for linha in resumos_anteriores:
        if not linha.get("metodo_extracao_texto"):
            linha["metodo_extracao_texto"] = "camada textual nativa"

    arquivos_substituidos = {linha["arquivo_acordao"] for linha in resumos_novos}
    ocorrencias = [
        linha for linha in ocorrencias_anteriores
        if linha["arquivo_acordao"] not in arquivos_substituidos
    ] + ocorrencias_novas
    resumos = [
        linha for linha in resumos_anteriores
        if linha["arquivo_acordao"] not in arquivos_substituidos
    ] + resumos_novos
    ocorrencias.sort(key=ordenar_ocorrencias)
    resumos.sort(key=ordenar_resumo)

    ids = [linha["ocorrencia_id"] for linha in ocorrencias]
    if len(ids) != len(set(ids)):
        raise ValueError("A consolidação produziria identificadores duplicados.")
    if len(resumos) != int(manifesto_anterior["total_acordaos"]):
        raise ValueError("A consolidação alteraria a quantidade de acórdãos do corpus.")

    temporario = integral / ".consolidacao_temporaria"
    if temporario.exists():
        shutil.rmtree(temporario)
    temporario.mkdir(parents=True)

    campos_ocorrencias = analise.campos_ocorrencias()
    analise.escrever_csv(
        temporario / "ocorrencias_classificadas.csv",
        ocorrencias,
        campos_ocorrencias,
    )
    pendentes = [
        linha for linha in ocorrencias if linha["status_revisao"] == "pendente"
    ]
    analise.escrever_csv(
        temporario / "revisao_pendente.csv",
        pendentes,
        campos_ocorrencias,
    )
    campos_resumo = list(dict.fromkeys(
        [campo for linha in resumos_novos + resumos_anteriores for campo in linha]
    ))
    analise.escrever_csv(
        temporario / "resumo_execucao.csv",
        resumos,
        campos_resumo,
    )
    analise.criar_pacotes_revisao(
        pendentes,
        temporario / "pacotes_revisao.jsonl",
    )

    audiencias = sorted({int(linha["audiencia"]) for linha in resumos})
    metodos_extracao = Counter(
        linha.get("metodo_extracao_texto", "") or "não registrado na versão anterior"
        for linha in ocorrencias
    )
    manifesto = {
        "data_execucao": date.today().isoformat(),
        "versao_metodo": VERSAO_CONSOLIDADA,
        "versoes_linhas": sorted({linha["versao_metodo"] for linha in ocorrencias}),
        "modo_execucao": "consolidado",
        "audiencias_reexecutadas": manifesto_atualizacao.get(
            "audiencias_analisadas", []
        ),
        "arquivos_substituidos": sorted(arquivos_substituidos),
        "acordaos": manifesto_anterior["acordaos"],
        "audiencias_analisadas": audiencias,
        "total_acordaos": len(resumos),
        "total_audiencias": len(audiencias),
        "arquivo_termos": manifesto_atualizacao["arquivo_termos"],
        "arquivo_participantes": manifesto_atualizacao["arquivo_participantes"],
        "contexto_caracteres": manifesto_atualizacao["contexto_caracteres"],
        "metodos_extracao_texto": dict(sorted(metodos_extracao.items())),
        "total_ocorrencias": len(ocorrencias),
        "total_mencoes_expressas": sum(
            linha["tipo_alvo"] == "audiencia_publica" for linha in ocorrencias
        ),
        "total_alvos_em_contexto_explicito": sum(
            linha["tipo_alvo"] != "audiencia_publica"
            and linha["vinculo_audiencia"] == "vínculo explícito"
            for linha in ocorrencias
        ),
        "total_candidatos_vinculo_implicito": sum(
            linha["vinculo_audiencia"] == "candidato a vínculo implícito"
            for linha in ocorrencias
        ),
        "total_mencoes_preliminares": sum(
            linha["status_revisao"]
            in {"Parte do corpus - automático", "Parte do corpus"}
            for linha in ocorrencias
        ),
        "total_revisao_pendente": len(pendentes),
        "total_parte_corpus_automatico": sum(
            linha["status_revisao"] == "Parte do corpus - automático"
            for linha in ocorrencias
        ),
        "total_excluido_corpus_automatico": sum(
            linha["status_revisao"] == "Excluído do corpus - automático"
            for linha in ocorrencias
        ),
    }
    (temporario / "manifesto_execucao.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    for nome in [
        "ocorrencias_classificadas.csv",
        "revisao_pendente.csv",
        "resumo_execucao.csv",
        "pacotes_revisao.jsonl",
        "manifesto_execucao.json",
    ]:
        (temporario / nome).replace(integral / nome)
    temporario.rmdir()

    print(f"Arquivos substituídos: {len(arquivos_substituidos)}")
    print(f"Ocorrências consolidadas: {len(ocorrencias)}")
    print(f"Pendentes consolidados: {len(pendentes)}")


if __name__ == "__main__":
    main()
