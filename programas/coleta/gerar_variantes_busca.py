#!/usr/bin/env python3
"""Gera a tabela operacional de termos para busca nos acórdãos."""

from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


BASE = Path(__file__).resolve().parent
ORIGEM = BASE / "resultados" / "participantes_relacional_limpo.csv"
SAIDA = BASE / "resultados" / "termos_busca_acordaos.csv"
SAIDA_ATIVOS = BASE / "resultados" / "termos_busca_acordaos_ativos.csv"
COLISOES = BASE / "resultados" / "variantes_busca_colisoes.csv"
ALIASES_DOCUMENTAIS = BASE / "resultados" / "aliases_participantes_manuais.csv"

CONECTORES_NOME = {"da", "das", "de", "do", "dos", "e"}
SUFIXOS_NOME = {"filho", "filha", "neto", "neta", "junior", "júnior", "sobrinho", "sobrinha", "jr"}
SIGLAS_BLOQUEADAS = {
    "STF", "DF", "SP", "RJ", "BR", "S/A", "SA", "PP", "PT", "PL", "PS", "EM",
    "DO", "DA", "DE", "DOS", "DAS", "E", "BRASIL", "FEDERAL", "NACIONAL", "ESTADO",
}
INSTITUICOES_GENERICAS = {
    "ministerio da saude", "ministerio da defesa", "senado", "senado federal",
    "camara dos deputados", "governo do estado de sao paulo", "universidade de sao paulo",
    "ministerio publico federal", "advocacia-geral da uniao", "defensoria publica da uniao",
}

CAMPOS = [
    "numero_audiencia", "alvo_id", "tipo_alvo", "pessoa", "instituicao", "qualificacao",
    "termo_canonico", "termo_busca", "termo_normalizado", "tipo_variante",
    "origem_variante", "prioridade", "risco_falso_positivo", "usar_na_busca", "observacao",
]


def sem_acentos(valor: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", valor) if not unicodedata.combining(c))


def normalizar_busca(valor: str) -> str:
    s = sem_acentos(valor).casefold()
    s = s.replace("’", "'").replace("`", "'")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def limpo(valor: str) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip(" \t\r\n-–—,;:.")


def extrair_siglas(instituicao: str) -> list[str]:
    candidatas = []
    candidatas.extend(re.findall(r"\(([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{2,15})\)", instituicao))
    candidatas.extend(re.findall(r"(?:[-–—]\s*)([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{2,15})\s*$", instituicao))
    if re.fullmatch(r"[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{2,15}", instituicao.strip()):
        candidatas.append(instituicao.strip())
    saida = []
    for candidato in candidatas:
        for parte in [candidato, *re.split(r"[/]", candidato)]:
            parte = limpo(parte).upper()
            if parte and parte not in SIGLAS_BLOQUEADAS and parte not in saida:
                saida.append(parte)
    return saida


def instituicao_sem_sigla(instituicao: str) -> str:
    s = re.sub(r"\s*\([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{2,15}\)\s*$", "", instituicao)
    s = re.sub(r"\s*[-–—]\s*[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{2,15}\s*$", "", s)
    return limpo(s)


def assinatura_instituicao(instituicao: str) -> str:
    base = instituicao_sem_sigla(instituicao)
    base = re.sub(r"\b(?:ltda\.?|s/?a)\b", "", base, flags=re.I)
    return normalizar_busca(base or instituicao)


def adicionar(saida: list[dict[str, str]], *, audiencia: str, alvo_id: str, tipo_alvo: str,
              pessoa: str = "", instituicao: str = "", qualificacao: str = "",
              canonico: str, termo: str, tipo_variante: str, origem: str,
              prioridade: str, risco: str, usar: str = "sim", observacao: str = "") -> None:
    termo = limpo(termo)
    normalizado = normalizar_busca(termo)
    if len(normalizado) < 3:
        return
    saida.append({
        "numero_audiencia": audiencia,
        "alvo_id": alvo_id,
        "tipo_alvo": tipo_alvo,
        "pessoa": pessoa,
        "instituicao": instituicao,
        "qualificacao": qualificacao,
        "termo_canonico": canonico,
        "termo_busca": termo,
        "termo_normalizado": normalizado,
        "tipo_variante": tipo_variante,
        "origem_variante": origem,
        "prioridade": prioridade,
        "risco_falso_positivo": risco,
        "usar_na_busca": usar,
        "observacao": observacao,
    })


def variantes_pessoa(nome: str) -> list[tuple[str, str, str, str, str]]:
    """termo, tipo, prioridade, risco, usar"""
    variantes = [(nome, "nome_completo", "alta", "baixo", "sim")]
    tokens = nome.split()
    conteudo = [t for t in tokens if normalizar_busca(t) not in CONECTORES_NOME]

    sem_iniciais = " ".join(t for t in tokens if not re.fullmatch(r"[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ]\.?", t))
    if normalizar_busca(sem_iniciais) != normalizar_busca(nome):
        variantes.append((sem_iniciais, "nome_sem_iniciais", "alta", "baixo", "sim"))

    if conteudo and normalizar_busca(conteudo[-1]) in SUFIXOS_NOME and len(tokens) >= 3:
        sem_sufixo = " ".join(tokens[:-1])
        variantes.append((sem_sufixo, "nome_sem_sufixo", "media", "medio", "sim"))

    if len(conteudo) >= 4:
        variantes.append((" ".join(conteudo[:2] + conteudo[-1:]), "dois_primeiros_ultimo", "media", "medio", "sim"))
        variantes.append((" ".join(conteudo[:1] + conteudo[-2:]), "primeiro_dois_ultimos", "media", "medio", "sim"))

    if len(conteudo) >= 3:
        curto = " ".join([conteudo[0], conteudo[-1]])
        variantes.append((curto, "primeiro_ultimo", "revisao", "alto", "nao"))
    return variantes


def variantes_instituicao(inst: str) -> list[tuple[str, str, str, str, str]]:
    variantes = [(inst, "instituicao_completa", "alta", "baixo", "sim")]
    sem_sigla = instituicao_sem_sigla(inst)
    if sem_sigla and normalizar_busca(sem_sigla) != normalizar_busca(inst):
        risco = "alto" if normalizar_busca(sem_sigla) in INSTITUICOES_GENERICAS else "baixo"
        variantes.append((sem_sigla, "instituicao_sem_sigla", "alta", risco, "sim"))
    sem_sufixo = limpo(re.sub(r"\b(?:Ltda\.?|S/?A)\b\.?$", "", sem_sigla or inst, flags=re.I))
    if sem_sufixo and normalizar_busca(sem_sufixo) != normalizar_busca(sem_sigla or inst):
        variantes.append((sem_sufixo, "instituicao_sem_sufixo_societario", "media", "medio", "sim"))
    for sigla in extrair_siglas(inst):
        letras = len(re.sub(r"[^A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ]", "", sigla))
        if letras <= 2:
            prioridade, risco, usar = "revisao", "alto", "nao"
        elif letras == 3:
            prioridade, risco, usar = "media", "alto", "sim"
        else:
            prioridade, risco, usar = "alta", "medio", "sim"
        variantes.append((sigla, "sigla_explicita", prioridade, risco, usar))
    return variantes


def main() -> None:
    participantes = list(csv.DictReader(ORIGEM.open(encoding="utf-8-sig")))
    aliases_por_pessoa: dict[tuple[int, str], list[dict[str, str]]] = defaultdict(list)
    if ALIASES_DOCUMENTAIS.exists():
        for alias in csv.DictReader(ALIASES_DOCUMENTAIS.open(encoding="utf-8-sig")):
            aliases_por_pessoa[
                (int(alias["numero_audiencia"]), normalizar_busca(alias["pessoa_canonica"]))
            ].append(alias)
    termos: list[dict[str, str]] = []

    for n, termo in enumerate(["audiência pública", "audiências públicas"], 1):
        adicionar(
            termos, audiencia="", alvo_id=f"GLOBAL-AP-{n:02d}", tipo_alvo="audiencia_publica",
            canonico="audiência pública", termo=termo, tipo_variante="singular" if n == 1 else "plural",
            origem="regra_geral", prioridade="alta", risco="baixo",
            observacao="Aplicar a todos os acórdãos, independentemente da audiência vinculada.",
        )

    pessoas = [r for r in participantes if r["pessoa"]]
    for seq, r in enumerate(pessoas, 1):
        ap = int(r["numero_audiencia"])
        alvo_id = f"AP{ap:02d}-P{seq:04d}"
        for termo, tipo, prioridade, risco, usar in variantes_pessoa(r["pessoa"]):
            adicionar(
                termos, audiencia=str(ap), alvo_id=alvo_id, tipo_alvo="pessoa",
                pessoa=r["pessoa"], instituicao=r["instituicao"], qualificacao=r["qualificacao"],
                canonico=r["pessoa"], termo=termo, tipo_variante=tipo,
                origem="lista_relacional_limpa" if tipo == "nome_completo" else "regra_automatica",
                prioridade=prioridade, risco=risco, usar=usar,
            )
        for alias in aliases_por_pessoa.get((ap, normalizar_busca(r["pessoa"])), []):
            adicionar(
                termos, audiencia=str(ap), alvo_id=alvo_id, tipo_alvo="pessoa",
                pessoa=r["pessoa"], instituicao=r["instituicao"], qualificacao=r["qualificacao"],
                canonico=r["pessoa"], termo=alias["variante"],
                tipo_variante="nome_observado_na_fonte", origem="fonte_documental",
                prioridade="alta", risco="baixo", usar="sim",
                observacao=(
                    f"Grafia observada em {alias['arquivo_fonte']}. "
                    f"{alias.get('observacao', '')}"
                ).strip(),
            )

    # Instituições são alvos próprios e aparecem uma única vez por audiência.
    inst_por_ap: dict[tuple[int, str], dict[str, str]] = {}
    for r in participantes:
        if not r["instituicao"]:
            continue
        ap = int(r["numero_audiencia"])
        assinatura = assinatura_instituicao(r["instituicao"])
        inst_por_ap.setdefault((ap, assinatura), r)
    for seq, ((ap, _), r) in enumerate(sorted(inst_por_ap.items()), 1):
        inst = r["instituicao"]
        alvo_id = f"AP{ap:02d}-I{seq:04d}"
        for termo, tipo, prioridade, risco, usar in variantes_instituicao(inst):
            adicionar(
                termos, audiencia=str(ap), alvo_id=alvo_id, tipo_alvo="instituicao",
                instituicao=inst, canonico=inst, termo=termo, tipo_variante=tipo,
                origem="lista_relacional_limpa" if tipo == "instituicao_completa" else "regra_automatica",
                prioridade=prioridade, risco=risco, usar=usar,
                observacao="Instituição tratada como alvo independente da pessoa relacionada.",
            )

    # Remove variantes idênticas do mesmo alvo, preservando a primeira regra.
    unicos: dict[tuple[str, str], dict[str, str]] = {}
    preferencia_origem = {
        "nome_completo": 0,
        "instituicao_completa": 0,
        "nome_observado_na_fonte": 1,
    }
    for t in termos:
        k = (t["alvo_id"], t["termo_normalizado"])
        anterior = unicos.get(k)
        if anterior is None or preferencia_origem.get(t["tipo_variante"], 2) < preferencia_origem.get(anterior["tipo_variante"], 2):
            unicos[k] = t
    termos = list(unicos.values())

    # Colisões dentro da mesma audiência são mantidas para auditoria. Como o
    # objetivo é detectar qualquer participante, uma variante segura pode
    # permanecer ativa uma única vez, mesmo que aponte para mais de um alvo.
    por_termo: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for t in termos:
        if t["numero_audiencia"]:
            por_termo[(t["numero_audiencia"], t["termo_normalizado"])].append(t)
    colisoes: list[dict[str, str]] = []
    for grupo in por_termo.values():
        alvos = {t["alvo_id"] for t in grupo}
        if len(alvos) <= 1:
            continue
        descricao = " | ".join(dict.fromkeys(t["termo_canonico"] for t in grupo))
        preferencia = {
            "nome_completo": 0, "nome_observado_na_fonte": 1,
            "instituicao_completa": 2, "sigla_explicita": 3,
            "nome_sem_iniciais": 4, "nome_sem_sufixo": 5,
            "dois_primeiros_ultimo": 6, "primeiro_dois_ultimos": 7,
            "instituicao_sem_sigla": 8, "instituicao_sem_sufixo_societario": 9,
            "primeiro_ultimo": 10,
        }
        candidatos_ativos = [t for t in grupo if t["usar_na_busca"] == "sim"]
        escolhido = min(candidatos_ativos, key=lambda t: preferencia.get(t["tipo_variante"], 99)) if candidatos_ativos else None
        for t in grupo:
            t["risco_falso_positivo"] = "alto"
            if t is escolhido:
                t["observacao"] = f"Termo compartilhado, mantido uma única vez na busca: {descricao}"
            else:
                t["usar_na_busca"] = "nao"
                t["prioridade"] = "revisao"
                t["observacao"] = f"Duplicata de termo compartilhado na mesma audiência: {descricao}"
            colisoes.append(t.copy())

    ordem = {"audiencia_publica": 0, "pessoa": 1, "instituicao": 2}
    termos.sort(key=lambda t: (
        int(t["numero_audiencia"] or 0), ordem[t["tipo_alvo"]],
        normalizar_busca(t["termo_canonico"]), t["tipo_variante"], t["termo_normalizado"],
    ))
    colisoes.sort(key=lambda t: (int(t["numero_audiencia"]), t["termo_normalizado"], t["alvo_id"]))

    termos_ativos = [t for t in termos if t["usar_na_busca"] == "sim"]
    for caminho, linhas in [(SAIDA, termos), (SAIDA_ATIVOS, termos_ativos), (COLISOES, colisoes)]:
        with caminho.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(linhas)

    ativos = len(termos_ativos)
    print(f"Termos gerados: {len(termos)}")
    print(f"Termos ativos para busca: {ativos}")
    print(f"Termos para revisão: {len(termos) - ativos}")
    print(f"Linhas em colisão: {len(colisoes)}")


if __name__ == "__main__":
    main()
