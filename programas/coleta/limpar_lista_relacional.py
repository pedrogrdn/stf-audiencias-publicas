#!/usr/bin/env python3
"""Reconstrói uma lista relacional e conservadora de participantes das APs."""

from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


BASE = Path(__file__).resolve().parent
ORIGEM = BASE / "resultados" / "participantes_candidatos.csv"
SAIDA = BASE / "resultados" / "participantes_relacional_limpo.csv"
DESCARTES = BASE / "resultados" / "participantes_descartes_limpeza.csv"
COMPLEMENTOS = BASE / "resultados" / "complementos_participantes_manuais.csv"

# Formas efetivamente usadas nas fontes da AP 3. A canonização evita que uma
# mesma pessoa ocupe duas linhas; as grafias observadas continuam preservadas
# no arquivo próprio de variantes para a busca nos acórdãos.
ALIASES_NOMINAIS_POR_AUDIENCIA = {
    (3, "paulo silveira martins"): "Paulo Silveira Martins Leão Junior",
    (3, "mario gisi"): "Mário José Gisi",
    (3, "marlene rossi"): "Marlene Rossi Severino Nobre",
    (3, "ieda teresinha do nascimento verreschi"): "Ieda Therezinha do Nascimento Verreschi",
}

MINISTROS_STF = {
    "alexandre de moraes", "andre luiz de almeida mendonca", "andre mendonca",
    "ayres britto", "carlos ayres britto", "carlos britto", "carlos mario velloso", "carmen lucia",
    "celso de mello", "cezar peluso", "cristiano zanin", "dias toffoli",
    "edson fachin", "ellen gracie", "eros grau", "flavio dino", "gilmar mendes",
    "ilmar galvao", "joaquim barbosa", "kassio nunes marques", "luiz fux",
    "marco aurelio", "menezes direito", "nelson jobim", "octavio gallotti",
    "ricardo lewandowski", "roberto barroso", "luis roberto barroso", "rosa weber",
    "sepulveda pertence", "sidney sanches", "francisco rezek",
}

MARCADORES_INSTITUICAO = (
    "associação", "instituto", "conselho", "universidade", "ministério", "secretaria",
    "tribunal", "câmara", "partido", "confederação", "federação", "fundação",
    "organização", "comissão", "sociedade", "laboratório", "frente", "agência",
    "autoridade", "observatório", "procuradoria", "defensoria", "empresa", "sindicato",
    "ordem dos", "união nacional", "rede de", "fórum", "banco", "senado", "governo",
    "academia", "centro de", "comitê", "núcleo", "faculdade", "departamento",
    "companhia", "central única", "operador nacional", "movimento dos", "coalizão",
    "escola", "serviço", "servico",
    "advocacia-geral", "anistia internacional", "human rights watch", "transparência internacional",
    "university", "organization", "organisation", "medical center", "policy network",
    "conferência", "município", "diretoria", "assespro",
)

TERMOS_PROCESSUAIS = {
    "adi", "adpf", "adc", "ado", "re", "are", "hc", "sl", "sta", "ss", "stf",
    "codigo eleitoral", "código eleitoral", "lei", "acordao", "acórdão", "relator",
    "requerente", "amicus", "atuacao individual",
    "atuação individual", "intervencao de terceiro", "intervenção de terceiro",
    "ato do presidente do senado federal", "hipotese configuradora", "prisao-albergue",
    "reconhecimento da pratica", "excelentissimo ministro", "excelentíssimo ministro",
    "horario", "horário", "intervalo", "documento assinado", "supremo tribunal federal",
    "tese de repercussao geral", "tese de repercussão geral",
    "abertura dos trabalhos", "principio republicano", "princípio republicano",
}

QUALIFICACOES_SEM_NOME = {
    "membro", "expositor", "representante", "superintendente do cade",
    "consultor juridico", "consultor jurídico", "consultora juridica", "consultora jurídica",
    "chefe-geral", "promotor de justica", "promotor de justiça", "delegado nacional",
    "ex-ministro do tse",
}

FRAGMENTOS_OCR = {
    "engenharia", "saude publica", "saúde pública", "sistemas eletricos", "sistemas elétricos",
    "economia aplicada", "ambiental do", "sustentabilidade da", "pecuaria e",
    "pecuária e", "new technologies", "international postdoctoral", "jurisdiction policy",
    "intervenc ao de terceiro", "usuarios e gestores", "usuários e gestores",
    "trabalhadoras rurais senm terra", "goethe universt",
    "eesp e embaixador especial da fao", "ambiente e recursos hidricos",
    "ambiente e recursos hídricos",
}

INSTITUICOES_COMO_PESSOA = {
    "world intellectual property organization", "cgope", "fundo amazonia", "fundo amazônia",
    "povo guajajara", "apa xingu",
}

BLACKLIST_SIGLAS = {
    "ADI", "ADPF", "ADC", "ADO", "RE", "ARE", "HC", "SL", "STA", "SS", "STF",
    "DF", "SP", "RJ", "BR", "EM", "PP", "PL", "S/A", "SA", "GERAL", "GERAIS",
    "GLOBAL", "LIVRE", "RURAL", "PUBLICA", "PÚBLICA", "HUMANOS", "JUSTICA",
    "JUSTIÇA", "PROFESSOR", "PROFESSORA", "PESQUISADOR", "PESQUISADORA", "MEDICO",
    "MÉDICO", "MEDICOS", "MÉDICOS", "ADVOGADO", "REPRESENTANTE", "MEMBRO",
    "PRESIDENTE", "DIRETOR", "DIRETORA", "SECRETARIA", "SECRETÁRIA", "BANCO",
    "BANCADA", "COMPOSITOR", "CRIANCA", "CRIANÇA", "CRUZADO", "JANEIRO", "PARA",
    "PARÁ", "PARAIBA", "PARAÍBA", "PELO", "SUL", "MATA", "MATAR", "ACADEMIA",
    "OBSERVATORIO", "OBSERVATÓRIO", "DEPARTAMENTO", "ESCOLA", "SENADO", "TSE",
    "SENADOR", "SENADORA", "PROCURADOR", "PROCURADORA", "DEFENSOR", "DEFENSORA",
    "UNIAO", "UNIÃO", "SAUDE", "SAÚDE", "SILVA", "RONDONIA", "RONDÔNIA",
    "TRABALHO", "CIVIL", "ELETRICISTA", "NACIONAL", "GERAL", "REPUBLICA", "REPÚBLICA",
    "BRASIL", "ESTADO", "FEDERAL", "INSTITUTO", "ASSOCIACAO", "ASSOCIAÇÃO",
}

CARGOS = (
    "advogado", "advogada", "professor", "professora", "pesquisador", "pesquisadora",
    "presidente", "vice-presidente", "diretor", "diretora", "coordenador", "coordenadora",
    "secretário", "secretária", "ministro de estado", "ministra de estado", "deputado",
    "deputada", "senador", "senadora", "procurador", "procuradora", "defensor",
    "defensora", "economista", "médico", "médica", "engenheiro", "engenheira",
    "consultor", "consultora", "assessor", "assessora", "jornalista", "cientista",
    "reitor", "reitora", "governador", "governadora", "prefeito", "prefeita",
    "embaixador", "general", "especialista", "superintendente", "desembargador",
    "desembargadora", "juiz", "juíza", "promotor", "promotora", "parlamentar",
    "advogado-geral", "advogada-geral", "procurador-geral", "procuradora-geral",
    "coordenador-geral", "coordenadora-geral", "diretor-geral", "diretora-geral",
    "subprocurador-geral", "subprocuradora-geral", "gerente", "chefe", "delegado",
    "delegada", "conselheiro", "conselheira",
)

_TITULOS_PREFIXO = (
    "Exmo", "Exma", "Senhor", "Senhora", "Sr", "Sra", "Dr", "Dra", "Doutor",
    "Doutora", "Prof", "Professor Doutor", "Professora Doutora", "Dom", "Dona",
    "Major", "Capitão", "Magnífico", "General de Brigada", "Deputado Federal",
    "Ministro", "Ministra",
)
PREFIXO_PESSOA = re.compile(
    r"^(?:(?:" + "|".join(
        re.escape(x) for x in sorted((*_TITULOS_PREFIXO, *CARGOS), key=len, reverse=True)
    ) + r")\.?\s+)+",
    re.I,
)


def sem_acentos(valor: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", valor) if not unicodedata.combining(c))


def chave(valor: str) -> str:
    return re.sub(r"\s+", " ", sem_acentos(valor).casefold()).strip()


def chave_pessoa(valor: str) -> str:
    """Chave nominal insensível também a apóstrofos, hífens e pontuação."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", sem_acentos(valor).casefold())).strip()


def fonte_comprova_presenca(origem: dict[str, str]) -> bool:
    """Restringe a elegibilidade às notas taquigráficas/transcrições."""
    identificacao = chave(
        f"{origem.get('rotulo_fonte', '')} {origem.get('arquivo_fonte', '')}"
    )
    return "taquigraf" in identificacao or "transcri" in identificacao


def limpo(valor: str) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip(" \t\r\n-–—,;:.()")


def limpo_instituicao(valor: str) -> str:
    """Limpa pontuação periférica sem apagar parênteses de siglas."""
    return re.sub(r"\s+", " ", str(valor or "")).strip(" \t\r\n-–—,;:.")


def prefixo_qualificacao(valor: str) -> tuple[str, str | None]:
    original = limpo(re.sub(
        r"\s+e\s+(?:Dr\.?a?|Prof\.?|Professor(?:a)?(?:\s+Doutor(?:a)?)?)\s*$",
        "", valor, flags=re.I,
    ))
    original = re.sub(r"\b(Advogad[oa]|Procurador[ae]?|Coordenador[ae]?|Diretor[ae]?)-\s+Geral\b", r"\1-Geral", original, flags=re.I)
    m = PREFIXO_PESSOA.match(original)
    if not m:
        return original, None
    prefixo = limpo(m.group(0))
    prefixo = re.sub(
        r"\b(?:Exm[oa]|Senhor(?:a)?|Sr|Sra|Dr|Dra|Doutor(?:a)?|Prof|Professor(?:a)?|Dom|Dona|Magnífico)\.?\b",
        "", prefixo, flags=re.I,
    )
    prefixo = limpo(prefixo)
    return limpo(original[m.end():]), prefixo or None


def contem_termo(texto_normalizado: str, termo: str) -> bool:
    """Compara códigos e expressões por limites de palavra."""
    t = chave(termo)
    return bool(re.search(rf"(?<!\w){re.escape(t)}(?!\w)", texto_normalizado))


def pessoa_valida(valor: str) -> tuple[str | None, str | None]:
    nome, titulo = prefixo_qualificacao(valor)
    k = chave(nome)
    if k in MINISTROS_STF:
        return None, "ministro_do_stf"
    if "mestre de cerimon" in k or k in {"de cerimonia", "de cerimonias"}:
        return None, "cerimonial"
    if any(contem_termo(k, x) for x in TERMOS_PROCESSUAIS):
        return None, "termo_processual"
    if any(contem_termo(k, x) for x in QUALIFICACOES_SEM_NOME):
        return None, "qualificacao_sem_nome"
    if any(contem_termo(k, x) for x in FRAGMENTOS_OCR):
        return None, "fragmento_ocr_ou_textual"
    if any(contem_termo(k, x) for x in INSTITUICOES_COMO_PESSOA):
        return None, "instituicao_capturada_como_pessoa"
    if any(contem_termo(k, x) for x in MARCADORES_INSTITUICAO):
        return None, "instituicao_nao_pessoa"
    if re.search(r"\d|[/=:;]", nome) or len(nome) > 100:
        return None, "formato_invalido"
    palavras = nome.split()
    if not 2 <= len(palavras) <= 10:
        return None, "quantidade_de_palavras_invalida"
    conectores = {"da", "das", "de", "do", "dos", "e"}
    descritores_de_cargo = {
        "civil", "eletricista", "executivo", "executiva", "nacional", "geral",
        "legislativo", "legislativa", "senior", "senior", "presidente", "titular",
        "publico", "publica", "estadual", "municipal", "federal", "do", "da", "de",
        "dos", "das", "e", "junto", "responsavel", "regulacao", "implementacao",
        "sustentabilidade", "operacoes", "programas", "projetos", "gabinete",
        "seccional", "relacoes", "juridico", "juridica",
    }
    if chave(palavras[0]) in descritores_de_cargo:
        return None, "qualificacao_sem_nome"
    if chave(palavras[-1]) in conectores | {"des", "te", "mar", "edu"}:
        return None, "nome_truncado"
    principais = [p for p in palavras if chave(p) not in conectores]
    if len(principais) < 2:
        return None, "nome_incompleto"
    for p in principais:
        if re.fullmatch(r"[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ]\.?", p):
            continue
        if not re.match(r"^[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇÑ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇÑáàâãéèêíìîóòôõúùûçñ'’.-]+$", p):
            return None, "capitalizacao_incompativel"
    if all(chave(p) in {chave(c) for c in CARGOS} for p in principais):
        return None, "somente_cargo"
    return nome, titulo


def sigla_valida(valor: str) -> bool:
    s = limpo(valor)
    bloqueadas = {sem_acentos(x).upper() for x in BLACKLIST_SIGLAS}
    cargos = {sem_acentos(c).upper() for c in CARGOS}
    return (
        bool(re.fullmatch(r"[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{1,11}", s))
        and sem_acentos(s).upper() not in bloqueadas
        and sem_acentos(s).upper() not in cargos
    )


def instituicao_valida(valor: str, aceitar_sigla: bool = False) -> str | None:
    s = limpo_instituicao(valor)
    if chave(s) == "escola de gente claudia werneck":
        s = "Escola de Gente"
    s = re.sub(r"\s*\(([A-Z0-9./-]{2,12})$", r" (\1)", s)
    s = re.sub(r"^\s*(?:ADI|ADPF|ADC|ADO)\s*[\d\s./-]*?(?:DF|SP|RJ)?\s*", "", s, flags=re.I)
    s = re.sub(r"^(?:AMICUS\s+[^–—-]+)\s*[–—-]\s*", "", s, flags=re.I)
    s = re.sub(r"^\s*(?:\(?[ivxlcdm]+\)?\s*)?\d{1,2}h\d*(?:min)?\s*:\s*", "", s, flags=re.I)
    s = re.sub(r"^\s*\(?[ivxlcdm]+\)?[.)]\s*", "", s, flags=re.I)
    s = re.sub(r"\s+amicus\s+curiae\b.*$", "", s, flags=re.I)
    s = re.sub(r"^Seção\s+\d+\s*:\s*[^:]+:\s*", "", s, flags=re.I)
    s = re.split(r",\s*(?:Membro|responsável|representante|que)\b", s, maxsplit=1, flags=re.I)[0]
    if re.match(r"^Comissão de Juristas\b", s, re.I):
        s = "Comissão de Juristas"
    s = re.sub(r"^(?:representantes?\s+d[aeo]s?|órgãos?\s+e\s+entidades|entidade)\s*", "", s, flags=re.I)
    if (not s or len(s) > 150 or chave(s.split()[-1]) in {"de", "da", "do", "das", "dos", "e"}
            or re.search(r"\b(?:Expositor|Expositora|Horário|Documento assinado|Publique-se)\b", s, re.I)):
        return None
    if re.search(r"\b\d+\s*min\b|\b\d{1,2}h\d*\b", s, re.I):
        return None
    k = chave(s)
    if k in {chave(x) for x in TERMOS_PROCESSUAIS}:
        return None
    if k in {chave(x) for x in QUALIFICACOES_SEM_NOME | FRAGMENTOS_OCR}:
        return None
    if k in {chave(x) for x in INSTITUICOES_COMO_PESSOA}:
        return s
    if aceitar_sigla and sigla_valida(s):
        return s
    if len(s.split()) == 1 and chave(s) not in {"senado"}:
        return None
    if any(contem_termo(k, x) for x in MARCADORES_INSTITUICAO):
        return s
    return None


def cortar_fim(valor: str) -> str:
    s = re.split(
        r"\b(?:que\s+particip|participará|participara|Documento assinado|Publique-se|Brasília,|"
        r"\d+\)\s*Horário|\d+\)\s*Horario|INTERVALO|Encerramento)\b",
        valor, maxsplit=1, flags=re.I,
    )[0]
    return limpo(s)


def separar_qualificacao_instituicao(valor: str) -> tuple[str | None, str | None]:
    q = cortar_fim(valor)
    if not q:
        return None, None
    # Instituição pura ou sigla pura. Exige que a denominação comece como
    # instituição; cargo que apenas menciona uma instituição é separado abaixo.
    kq = chave(q)
    comeca_cargo = any(kq.startswith(chave(x)) for x in CARGOS)
    inicia_instituicao = any(re.match(rf"^{re.escape(chave(x))}(?!\w)", kq) for x in MARCADORES_INSTITUICAO)
    if sigla_valida(q) or (not comeca_cargo and inicia_instituicao):
        inst = instituicao_valida(q, aceitar_sigla=True)
        if inst:
            return None, inst

    # Localiza a primeira denominação institucional dentro da qualificação.
    posicoes = []
    for marcador in MARCADORES_INSTITUICAO:
        m_marcador = re.search(rf"(?<!\w){re.escape(chave(marcador))}(?!\w)", kq)
        if m_marcador:
            posicoes.append(m_marcador.start())
    if posicoes:
        pos = min(posicoes)
        inst = instituicao_valida(q[pos:], aceitar_sigla=True)
        qual = limpo(q[:pos].rstrip(" de da do dos das,;")) or None
        return qual, inst

    # Cargo + preposição + sigla: "Presidente da UNE".
    cargos = "|".join(re.escape(x) for x in sorted(CARGOS, key=len, reverse=True))
    m = re.match(rf"^({cargos})(?:\s+[^,;]{{0,50}}?)?\s+(?:d[aeo]s?|junto\s+à)\s+(.+)$", q, re.I)
    if m:
        candidato = limpo(m.group(2))
        inst = instituicao_valida(candidato, aceitar_sigla=True)
        if inst:
            return limpo(m.group(1)), inst

    # Cargo/qualificação sem instituição.
    if len(q) <= 120 and any(chave(c) in kq for c in CARGOS):
        return q, None
    return None, None


def parenteses_da_fala(nome: str, evidencia: str) -> str | None:
    pos = chave(evidencia).find(chave(nome))
    if pos < 0:
        return None
    trecho = evidencia[pos + len(nome):]
    m = re.search(r"\(([^)]{2,180})\)", trecho)
    return limpo(m.group(1)) if m else None


def separar_instituicao_embutida_no_nome(valor: str) -> tuple[str, str | None]:
    s = limpo(valor)
    for m in reversed(list(re.finditer(r"\s+d[ao]s?\s+", s, re.I))):
        pessoa_candidata = limpo(s[:m.start()])
        # Evita converter sobrenomes em caixa alta (p.ex. "DA SILVA") em sigla.
        inst_candidata = instituicao_valida(s[m.end():], aceitar_sigla=False)
        if inst_candidata and pessoa_valida(pessoa_candidata)[0]:
            return pessoa_candidata, inst_candidata
    return s, None


def instituicao_antes_expositor(evidencia: str, marcador_inicio: int) -> str | None:
    antes = evidencia[max(0, marcador_inicio - 220):marcador_inicio]
    antes = re.split(r"(?:\d+[.)]\s*Horário[^.]*\.|\d+[.)]|;|\.)", antes)[-1]
    antes = re.sub(r"^.*?\b(?:horas?|minutos?)\b\s*", "", antes, flags=re.I)
    antes = limpo(antes.rstrip("("))
    # Tenta a denominação completa e, em seguida, eventual sigla final.
    inst = instituicao_valida(antes)
    if inst:
        return inst
    m = re.search(r"([A-Z][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇÑáàâãéèêíìîóòôõúùûçñ .&/-]{3,130}\([A-Z0-9./-]{2,12}\))$", antes)
    return instituicao_valida(m.group(1)) if m else None


def instituicao_do_item_numerado(evidencia: str, pos_nome: int) -> str | None:
    """Recupera a entidade em listas como '1) Entidade (Pessoa, Pessoa)' ."""
    if pos_nome < 0:
        return None
    marcadores = list(re.finditer(r"(?:^|[:;.]\s+)(?:\d+|[ivxlcdm]+)[.)]\s*", evidencia[:pos_nome], re.I))
    if not marcadores:
        return None
    inicio = marcadores[-1].end()
    antes = evidencia[inicio:pos_nome]
    entidade = antes.rsplit("(", 1)[0]
    return instituicao_valida(entidade, aceitar_sigla=True)


def corrigir_nome_por_evidencia(nome: str, evidencia: str) -> str:
    if "Eric H. Holder Jr" in evidencia and chave(nome) == "holder jr":
        return "Eric H. Holder Jr."
    if "Coriolano Aurélio de A. Camargo Santos" in evidencia and chave(nome) in {
        "camargo santos", "conselheiro seccional dr", "coriolano aurelio de",
    }:
        return "Coriolano Aurélio de A. Camargo Santos"
    if "Maurício Soares Bugarini" in evidencia:
        return re.sub(r"Maurício Soares(?:\s+Bugarini)?", "Maurício Soares Bugarini", nome)
    return nome


def separar_pessoas_coordenadas(valor: str) -> list[tuple[str, str | None]]:
    """Separa 'Pessoa A e Pessoa B', preservando sobrenomes como 'e Cruz'."""
    s = limpo(valor)
    sobrenomes_pos_e = {"cruz", "silva", "sousa", "souza", "sa", "sá", "costa"}
    for m in re.finditer(r"\s+e\s+", s, re.I):
        direita = limpo(s[m.end():])
        if chave(direita.split()[0]) in sobrenomes_pos_e:
            continue
        p1, t1 = pessoa_valida(s[:m.start()])
        p2, t2 = pessoa_valida(direita)
        if p1 and p2:
            return [(p1, t1), (p2, t2)]
    pessoa, titulo = pessoa_valida(s)
    return [(pessoa, titulo)] if pessoa else []


def extrair_pessoas_pos_marcador(trecho: str) -> list[tuple[str, str | None, int, int]]:
    limite = re.split(r"\b(?:que\s+particip|Documento assinado|Publique-se|\d+[.)]\s*Horário)\b", trecho[:300], maxsplit=1, flags=re.I)[0]
    prefixo = (
        r"(?:(?:Exm[oa]\.?\s+)?(?:Sra?\.?|Dra?\.?|Prof\.?)|Professor(?:a)?\s+Doutor(?:a)?|"
        r"Professor(?:a)?|Doutor(?:a)?|Ministr[oa](?:\s+de\s+Estado)?|Deputad[oa](?:\s+Federal)?|"
        r"Senador(?:a)?|Embaixador|General(?:\s+de\s+Brigada)?|Secretári[oa](?:\s+de\s+Estado)?)"
    )
    nome = (
        r"([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇÑ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇÑáàâãéèêíìîóòôõúùûçñ'’.-]+"
        r"(?:\s+(?:d[aeo]s?|e|[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇÑ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇÑáàâãéèêíìîóòôõúùûçñ'’.-]+)){1,7})"
    )
    padrao = re.compile(rf"{prefixo}\s+{nome}", re.I)
    saida = []
    for m in padrao.finditer(limite):
        pessoa, titulo_ou_motivo = pessoa_valida(m.group(0))
        if pessoa:
            saida.append((pessoa, titulo_ou_motivo, m.start(), m.end()))
    if not saida:
        # Algumas programações omitem honorífico, mas o nome vem imediatamente
        # após o marcador. Não procura nomes no restante da qualificação.
        ancorado = re.match(rf"\s*{nome}", limite)
        if ancorado:
            pessoa, titulo_ou_motivo = pessoa_valida(ancorado.group(0))
            if pessoa:
                saida.append((pessoa, titulo_ou_motivo, ancorado.start(), ancorado.end()))
    return saida


def adicionar(registros: list[dict[str, object]], origem: dict[str, str], pessoa: str | None,
              instituicao: str | None, qualificacao: str | None, metodo: str) -> None:
    if not pessoa and not instituicao:
        return
    registros.append({
        "numero_audiencia": int(origem["numero_audiencia"]),
        "pessoa": pessoa,
        "instituicao": instituicao,
        "qualificacao": qualificacao,
        "metodo_extracao": metodo,
        "tipo_evidencia": origem["tipo_evidencia"],
        "rotulo_fonte": origem["rotulo_fonte"],
        "arquivo_fonte": origem["arquivo_fonte"],
        "pagina_fonte": origem["pagina_fonte"],
        "evidencia": origem["evidencia"],
    })


def processar_linha(origem: dict[str, str], registros: list[dict[str, object]], descartes: list[dict[str, object]]) -> None:
    tipo, evidencia = origem["tipo_evidencia"], origem["evidencia"]
    ap = int(origem["numero_audiencia"])
    nome_bruto = ALIASES_NOMINAIS_POR_AUDIENCIA.get(
        (ap, chave_pessoa(origem["nome"])), origem["nome"]
    )
    gerou = False

    if not fonte_comprova_presenca(origem):
        descartes.append({**origem, "motivo_descarte": "fonte_fora_do_escopo_de_presenca"})
        return

    # Bibliografia e legislação correlata podem conter pessoas e instituições,
    # mas não constituem evidência de participação na audiência.
    rotulo_normalizado = chave(origem.get("rotulo_fonte", ""))
    if "bibliografia" in rotulo_normalizado or "legislacao correlata" in rotulo_normalizado:
        descartes.append({**origem, "motivo_descarte": "fonte_sem_evidencia_de_participacao"})
        return

    if tipo == "fala_transcrita":
        nome_base, inst_embutida = separar_instituicao_embutida_no_nome(nome_bruto)
        pessoa, titulo_ou_motivo = pessoa_valida(nome_base)
        if pessoa:
            parenteses = parenteses_da_fala(pessoa, evidencia) or ""
            if "mestre de cerimon" in chave(parenteses):
                motivo = "cerimonial"
                pessoa = None
            qual, inst = separar_qualificacao_instituicao(parenteses) if pessoa else (None, None)
        if pessoa:
            qual = " | ".join(x for x in [titulo_ou_motivo, qual] if x) or None
            adicionar(registros, origem, pessoa, inst or inst_embutida, qual, "cabecalho_de_fala")
            gerou = True
        else:
            motivo = titulo_ou_motivo

    elif tipo == "cronograma":
        m = re.match(r"\s*(?:\d{1,2}h(?:\d{1,2})?|\d{1,2}:\d{2})\s*[-–—]\s*(.+)", evidencia, re.I)
        conteudo = m.group(1) if m else evidencia
        partes = [limpo(x) for x in re.split(r"\s+[-–—]\s+", conteudo) if limpo(x)]
        if partes:
            # Duas pessoas compartilhando a mesma instituição/horário.
            dupla = separar_pessoas_coordenadas(partes[0])
            if len(dupla) == 2:
                (p1, t1), (p2, t2) = dupla
                qual, inst = separar_qualificacao_instituicao(" - ".join(partes[1:]))
                adicionar(registros, origem, p1, inst, " | ".join(x for x in [t1, qual] if x) or None, "dupla_no_cronograma")
                adicionar(registros, origem, p2, inst, " | ".join(x for x in [t2, qual] if x) or None, "dupla_no_cronograma")
                gerou = True
                partes = []
        if partes:
            primeiro_pessoa, primeiro_titulo = pessoa_valida(partes[0])
            primeiro_inst = instituicao_valida(partes[0])
            if primeiro_pessoa:
                qual, inst = separar_qualificacao_instituicao(" - ".join(partes[1:]))
                qual = " | ".join(x for x in [primeiro_titulo, qual] if x) or None
                adicionar(registros, origem, primeiro_pessoa, inst, qual, "linha_de_cronograma")
                gerou = True
            elif primeiro_inst and len(partes) >= 2:
                pessoa, titulo = pessoa_valida(partes[1])
                qual, inst_qual = separar_qualificacao_instituicao(" - ".join(partes[2:]))
                adicionar(registros, origem, pessoa, primeiro_inst, " | ".join(x for x in [titulo, qual] if x) or None, "linha_de_cronograma")
                gerou = True
            elif primeiro_inst:
                adicionar(registros, origem, None, primeiro_inst, None, "instituicao_em_cronograma")
                gerou = True

    elif tipo == "expositor_expresso":
        nome_corrigido = corrigir_nome_por_evidencia(nome_bruto, evidencia)
        nomes = separar_pessoas_coordenadas(nome_corrigido)
        for pessoa_inicial, titulo_inicial in nomes:
            nome_base, inst_embutida = separar_instituicao_embutida_no_nome(pessoa_inicial)
            pessoa, titulo_ou_motivo = pessoa_valida(nome_base)
            titulo_ou_motivo = titulo_ou_motivo or titulo_inicial
            if not pessoa:
                continue
            pos_nome = chave(evidencia).find(chave(pessoa))
            marcadores = list(re.finditer(r"Expositor(?:a|es|as)?\s*:\s*", evidencia, re.I))
            marcador = next((m for m in reversed(marcadores) if pos_nome < 0 or m.start() <= pos_nome), None)
            if marcador:
                inst_pre = instituicao_antes_expositor(evidencia, marcador.start())
                pos_original = evidencia.casefold().find(pessoa.casefold(), marcador.end())
                inst_item = instituicao_do_item_numerado(evidencia, pos_original)
                resto = evidencia[pos_original + len(pessoa):] if pos_original >= 0 else evidencia[marcador.end():]
                m_parentese = re.match(r"\s*\(([^)]{2,180})\)", resto)
                qual_txt = m_parentese.group(1) if m_parentese else re.split(r"[.;]", resto, maxsplit=1)[0]
                qual, inst_qual = separar_qualificacao_instituicao(qual_txt)
                adicionar(registros, origem, pessoa, inst_pre or inst_item or inst_qual or inst_embutida,
                          " | ".join(x for x in [titulo_ou_motivo, qual] if x) or None,
                          "candidato_apos_marcador_expositor")
                gerou = True
        if not gerou:
            motivo = "nome_invalido_ou_fragmentado"

    elif tipo == "lista_nominal":
        pessoa, titulo_ou_motivo = pessoa_valida(nome_bruto)
        inst = instituicao_valida(nome_bruto)
        if pessoa:
            adicionar(registros, origem, pessoa, None, titulo_ou_motivo, "lista_nominal_pessoa")
            gerou = True
        elif inst:
            adicionar(registros, origem, None, inst, None, "lista_nominal_instituicao")
            gerou = True
        else:
            motivo = titulo_ou_motivo

    if not gerou:
        descartes.append({**origem, "motivo_descarte": locals().get("motivo") or "sem_entidade_relacional_confiavel"})


def limpar_qualificacao(valor: object) -> str | None:
    s = limpo(str(valor or ""))
    if not s:
        return None
    s = re.sub(r"\bMembr$", "Membro", s, flags=re.I)
    s = re.sub(r"\brepresentant$", "Representante", s, flags=re.I)
    s = re.sub(r"\bVice-President$", "Vice-Presidente", s, flags=re.I)
    s = re.sub(r"\bPresident$", "Presidente", s, flags=re.I)
    s = re.sub(r"\bOrçament$", "Orçamento", s, flags=re.I)
    s = re.sub(r"\s*,?\s*(?:que|e\s+(?:Senhor(?:a)?\s+)?Dr\.?a?)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s+\d+\s*$", "", s)
    s = re.sub(r"\s+(?:de|da|do|das|dos|e)$", "", s, flags=re.I)
    return limpo(s) or None


def canonizar_siglas_institucionais(registros: list[dict[str, object]]) -> None:
    """Une, para a mesma pessoa/AP, 'UNE' e a denominação completa com '(UNE)'."""
    completos: dict[tuple[int, str, str], str] = {}
    for r in registros:
        if not r["pessoa"] or not r["instituicao"]:
            continue
        inst = str(r["instituicao"])
        if len(inst.split()) < 2:
            continue
        for sigla in re.findall(r"\b[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{1,11}\b", inst):
            if sigla_valida(sigla):
                completos[(int(r["numero_audiencia"]), chave_pessoa(str(r["pessoa"])), chave(sigla))] = inst
    for r in registros:
        if r["pessoa"] and r["instituicao"]:
            k = (int(r["numero_audiencia"]), chave_pessoa(str(r["pessoa"])), chave(str(r["instituicao"])))
            if k in completos:
                r["instituicao"] = completos[k]


def instituicoes_equivalentes(a: str, b: str) -> bool:
    if chave(a) == chave(b):
        return True
    sem_sigla = lambda s: re.sub(
        r"\s*\([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{2,12}\)\s*$", "", s
    )
    if chave(sem_sigla(a)) == chave(sem_sigla(b)):
        return True
    siglas_a = {chave(x) for x in re.findall(r"\b[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{2,11}\b", a)}
    siglas_b = {chave(x) for x in re.findall(r"\b[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ0-9./-]{2,11}\b", b)}
    if siglas_a & siglas_b:
        return True
    return (sigla_valida(a) and chave(a) in siglas_b) or (sigla_valida(b) and chave(b) in siglas_a)


def aliases_pessoas(registros: list[dict[str, object]]) -> dict[tuple[int, str], str]:
    """Une grafias abreviadas da mesma pessoa quando a instituição confirma o vínculo."""
    conectores = {"da", "das", "de", "do", "dos", "e"}
    por_ap: dict[int, list[dict[str, object]]] = defaultdict(list)
    vistos: set[tuple[int, str]] = set()
    for r in registros:
        if not r["pessoa"]:
            continue
        ap, kp = int(r["numero_audiencia"]), chave_pessoa(str(r["pessoa"]))
        if (ap, kp) not in vistos:
            por_ap[ap].append({"chave": kp, "nome": str(r["pessoa"]), "instituicoes": []})
            vistos.add((ap, kp))
        item = next(x for x in por_ap[ap] if x["chave"] == kp)
        if r["instituicao"]:
            item["instituicoes"].append(str(r["instituicao"]))

    aliases: dict[tuple[int, str], str] = {}
    for ap, pessoas in por_ap.items():
        for i, atual in enumerate(pessoas):
            tokens_atual = [x for x in atual["chave"].split() if x not in conectores]
            destino = atual["chave"]
            for anterior in pessoas[:i]:
                tokens_anterior = [x for x in anterior["chave"].split() if x not in conectores]
                if not tokens_atual or not tokens_anterior:
                    continue
                mesmos_extremos = tokens_atual[0] == tokens_anterior[0] and tokens_atual[-1] == tokens_anterior[-1]
                nomes_compativeis = set(tokens_atual).issubset(tokens_anterior) or set(tokens_anterior).issubset(tokens_atual)
                inst_compativeis = any(
                    instituicoes_equivalentes(a, b)
                    for a in atual["instituicoes"] for b in anterior["instituicoes"]
                )
                if mesmos_extremos and nomes_compativeis and inst_compativeis:
                    destino = aliases.get((ap, anterior["chave"]), anterior["chave"])
                    break
            aliases[(ap, atual["chave"])] = destino
    return aliases


def consolidar(registros: list[dict[str, object]]) -> list[dict[str, object]]:
    canonizar_siglas_institucionais(registros)
    aliases = aliases_pessoas(registros)
    chave_relacional = lambda r: aliases.get(
        (int(r["numero_audiencia"]), chave_pessoa(str(r["pessoa"]))),
        chave_pessoa(str(r["pessoa"])),
    )
    # Para cada pessoa na mesma audiência, conserva somente a primeira
    # instituição encontrada nas fontes. As demais relações institucionais da
    # pessoa são retiradas para que ela ocupe uma única linha na lista final.
    primeira_instituicao: dict[tuple[int, str], str] = {}
    for r in registros:
        if r["pessoa"] and r["instituicao"]:
            kp = (int(r["numero_audiencia"]), chave_relacional(r))
            primeira_instituicao.setdefault(kp, chave(str(r["instituicao"])))
    registros = [
        r for r in registros
        if not (r["pessoa"] and r["instituicao"])
        or chave(str(r["instituicao"])) == primeira_instituicao[
            (int(r["numero_audiencia"]), chave_relacional(r))
        ]
    ]
    # Uma pessoa/instituição só recebe a classe "sem" se não houver vínculo em
    # nenhuma das fontes da mesma audiência.
    pessoas_vinculadas = {(r["numero_audiencia"], chave_relacional(r)) for r in registros if r["pessoa"] and r["instituicao"]}
    inst_vinculadas = [
        (int(r["numero_audiencia"]), str(r["instituicao"]))
        for r in registros if r["pessoa"] and r["instituicao"]
    ]
    grupos: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for r in registros:
        pessoa, inst = r["pessoa"], r["instituicao"]
        if pessoa and not inst and (r["numero_audiencia"], chave_relacional(r)) in pessoas_vinculadas:
            continue
        if inst and not pessoa and any(
            int(r["numero_audiencia"]) == ap and instituicoes_equivalentes(str(inst), vinculada)
            for ap, vinculada in inst_vinculadas
        ):
            continue
        if pessoa and inst:
            classe = "pessoa_com_instituicao"
        elif pessoa:
            classe = "pessoa_sem_instituicao"
        else:
            classe = "instituicao_sem_pessoa"
        k = (r["numero_audiencia"], chave_relacional(r) if pessoa else "", chave(str(inst or "")), classe)
        grupos[k].append(r)

    saida = []
    for grupo in grupos.values():
        base = grupo[0]
        unicos = lambda campo: list(dict.fromkeys(limpo(str(x[campo])) for x in grupo if x.get(campo)))
        qualificacoes_por_chave: dict[str, str] = {}
        for q in (limpar_qualificacao(x.get("qualificacao")) for x in grupo):
            if not q:
                continue
            kq = chave(q)
            anterior = qualificacoes_por_chave.get(kq)
            if anterior is None or (anterior.isupper() and not q.isupper()):
                qualificacoes_por_chave[kq] = q
        qualificacoes = list(qualificacoes_por_chave.values())
        fontes = unicos("arquivo_fonte")
        paginas = unicos("pagina_fonte")
        metodos = unicos("metodo_extracao")
        rotulos = unicos("rotulo_fonte")
        saida.append({
            "numero_audiencia": base["numero_audiencia"],
            "classificacao": ("pessoa_com_instituicao" if base["pessoa"] and base["instituicao"] else
                              "pessoa_sem_instituicao" if base["pessoa"] else "instituicao_sem_pessoa"),
            "pessoa": max(
                (str(x["pessoa"]) for x in grupo if x.get("pessoa")),
                key=lambda s: (not s.isupper(), len(s)), default=None,
            ),
            "instituicao": max(
                (str(x["instituicao"]) for x in grupo if x.get("instituicao")),
                key=lambda s: (len(s.split()) > 1, len(s)), default=None,
            ),
            "qualificacao": " | ".join(qualificacoes) or None,
            "quantidade_evidencias": len(grupo),
            "metodos_extracao": " | ".join(metodos),
            "rotulos_fontes": " | ".join(rotulos),
            "arquivos_fontes": " | ".join(fontes),
            "paginas_fontes": " | ".join(paginas),
            "evidencia_exemplo": base["evidencia"],
        })
    return sorted(saida, key=lambda x: (int(x["numero_audiencia"]), x["classificacao"], chave(str(x["pessoa"] or x["instituicao"]))))


def escrever(caminho: Path, linhas: list[dict[str, object]]) -> None:
    campos = list(linhas[0]) if linhas else []
    with caminho.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        if campos:
            w.writeheader(); w.writerows(linhas)


def main() -> None:
    origens = list(csv.DictReader(ORIGEM.open(encoding="utf-8-sig")))
    registros: list[dict[str, object]] = []
    descartes: list[dict[str, object]] = []
    for origem in origens:
        processar_linha(origem, registros, descartes)
    if COMPLEMENTOS.exists():
        for item in csv.DictReader(COMPLEMENTOS.open(encoding="utf-8-sig")):
            origem = {
                "numero_audiencia": item["numero_audiencia"],
                "tipo_evidencia": "complemento_curado_documento_oficial",
                "rotulo_fonte": item["rotulo_fonte"],
                "arquivo_fonte": item["arquivo_fonte"],
                "pagina_fonte": item["pagina_fonte"],
                "evidencia": item["evidencia"],
            }
            if not fonte_comprova_presenca(origem):
                descartes.append({
                    "numero_audiencia": item["numero_audiencia"],
                    "nome": item["pessoa"] or item["instituicao"],
                    "tipo_evidencia": "complemento_curado_documento_oficial",
                    "rotulo_fonte": item["rotulo_fonte"],
                    "arquivo_fonte": item["arquivo_fonte"],
                    "pagina_fonte": item["pagina_fonte"],
                    "evidencia": item["evidencia"],
                    "motivo_descarte": "fonte_fora_do_escopo_de_presenca",
                })
                continue
            adicionar(
                registros, origem, limpo(item["pessoa"]) or None,
                limpo_instituicao(item["instituicao"]) or None,
                limpo(item["qualificacao"]) or None,
                "complemento_curado_documento_oficial",
            )
    final = consolidar(registros)
    escrever(SAIDA, final)
    escrever(DESCARTES, descartes)
    contagem = defaultdict(int)
    for x in final:
        contagem[x["classificacao"]] += 1
    print(f"Registros relacionais: {len(final)}")
    print(dict(contagem))
    print(f"Candidatos descartados: {len(descartes)}")


if __name__ == "__main__":
    main()
