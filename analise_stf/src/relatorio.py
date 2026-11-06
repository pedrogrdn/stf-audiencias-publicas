"""Relatório consolidado único H1–H22 (Markdown + HTML). Todo número substantivo vem do código (fx/fi registram os números)."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from auditar_base import md_tabela
from hipoteses import fx, fi, fp

NOTA_H8 = '**Nota metodológica sobre H8 (dependência conceitual).** A metodologia de classificação adotada (documento raiz METODOLOGIA_ANALISE_MENCOES_AUDIENCIAS.md, seção 14.2) afirma: "Estar no voto, fora do relatório ou próximo de uma conclusão é indício, mas não condição suficiente." Assim, a localização/contexto argumentativo foi um dos indícios usados para decidir o tipo (Contexto, Relato ou Argumento). A associação H8 entre local e tipo não é, portanto, validação independente da tipologia, e parte do padrão pode refletir a própria operacionalização. Isso não configura tautologia estrita (há Argumentos no Relatório) e não descarta os contrastes estatísticos: indica apenas risco de dependência conceitual/incorporação do contexto e exige cautela interpretativa. Nada disso permite inferir eficácia democrática, mudança de voto ou impacto causal. A nota é relevante porque H8 concentra os achados com BH < 0,05.'

COLS_MATRIZ = ['Hipótese', 'Análise', 'Escopo do teste', 'Teste', 'Pergunta', 'Variáveis', 'Unidade', 'N', 'Método', 'Estimativa', 'Incerteza', 'valor-p', 'valor-p BH', 'Robustez', 'Interpretação', 'Limitações', 'Situação']
PRINCIPAL = 'Principal (A)'


ESC_PREV, ESC_ADIC, ESC_ELEG, ESC_AB = 'previsto principal', 'adicional local×eixo', 'sensibilidade de elegibilidade', 'sensibilidade de vínculo A+B'


def escopo_teste(analise: str, teste: str, familia: str) -> str:
    """Escopo público do teste (independe do cenário de dados): previsto principal | adicional local×eixo | sensibilidade de elegibilidade | sensibilidade de vínculo A+B (combináveis com '; ')."""
    partes = []
    if '[análise adicional]' in teste or familia == 'F_adicional':
        partes.append(ESC_ADIC)
    if 'sensibilidade exploratória de elegibilidade' in teste:
        partes.append(ESC_ELEG)
    if analise != PRINCIPAL:
        partes.append(ESC_AB)
    return '; '.join(partes) if partes else ESC_PREV


def matriz_publica(df: pd.DataFrame) -> pd.DataFrame:
    df = df.assign(**{'Escopo do teste': [escopo_teste(a, t, f) for a, t, f in zip(df['Analise'], df['Teste'], df['Familia'])]})
    d = df.rename(columns={'Hipotese': 'Hipótese', 'Analise': 'Análise', 'Variaveis': 'Variáveis', 'Metodo': 'Método', 'valor_p': 'valor-p', 'valor_p_BH': 'valor-p BH',
                           'Interpretacao': 'Interpretação', 'Limitacoes': 'Limitações', 'Situacao': 'Situação', 'Familia': 'Família'})
    return d[COLS_MATRIZ + ['Família', 'estimativa_num', 'ic_inf', 'ic_sup']]


def _inviavel(s):
    return s.str.startswith('Inviável')


def resumo_hipoteses(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Contagens por hipótese separadas por escopo: previsto principal (A) | adicional/sensibilidade de elegibilidade (A) | sensibilidade A+B."""
    pub = matriz_publica(df)
    rows = []
    for h, c in cfg['hipoteses'].items():
        g = pub[pub['Hipótese'] == h]
        a = g[g['Análise'] == PRINCIPAL]
        prev = a[a['Escopo do teste'] == ESC_PREV]
        ext = a[a['Escopo do teste'] != ESC_PREV]
        ab = g[g['Análise'] != PRINCIPAL]
        bhmin = prev['valor-p BH'].min()
        n_ext_p, n_prev_p = int(ext['valor-p'].notna().sum()), int(prev['valor-p'].notna().sum())
        obs = []
        if len(prev) and n_prev_p == 0 and _inviavel(prev['Situação']).sum() == len(prev):
            obs.append(f'sem teste viável no escopo previsto principal ({len(prev)} linhas inviáveis)')
        if n_ext_p:
            obs.append(f'{n_ext_p} valor(es)-p vêm de análises adicionais/sensibilidade de elegibilidade, não do escopo previsto principal')
        rows.append({'Hipótese': h, 'Pergunta': c['Pergunta'], 'Linhas previstas (A)': len(prev), 'Previstos com valor-p': n_prev_p,
                     'Previstos inviáveis': int(_inviavel(prev['Situação']).sum()), 'Descritivos': int(prev['Situação'].str.startswith(('Descritivo', 'Exploratório descritivo')).sum()),
                     'menor valor-p BH (previstos)': fx(bhmin, 4) if np.isfinite(bhmin) else 'n/a',
                     'Linhas adicionais/elegibilidade (A)': len(ext), 'Adicionais com valor-p': n_ext_p,
                     'Linhas A+B': len(ab), 'A+B com valor-p': int(ab['valor-p'].notna().sum()),
                     'Família BH (previstos)': ', '.join(sorted(set(prev['Família']))), 'Observação de escopo': '; '.join(obs)})
    return pd.DataFrame(rows)


def _curto(s, n=190):
    s = str(s)
    return s if len(s) <= n else s[:n - 1] + '…'


def _resultado(r, alfa):
    if np.isfinite(r['valor-p']):
        q = r['valor-p BH']
        return 'compatível com associação exploratória' if q < alfa else 'inconclusivo (sem evidência suficiente; não prova ausência)'
    return r['Situação'].split(':')[0]


def escrever(ctx, ctx_ab, mat: pd.DataFrame, val: dict, check: dict, figs: list[dict], caminho: Path, comando: str, modo: str, decisao: dict, raiz: Path):
    P, cfg = ctx.P, ctx.cfg
    alfa = P['alfa_bh']
    pub = matriz_publica(mat)
    prin, sens = pub[pub['Análise'] == PRINCIPAL], pub[pub['Análise'] != PRINCIPAL]
    prev = prin[prin['Escopo do teste'] == ESC_PREV]
    adic = prin[prin['Escopo do teste'] != ESC_PREV]
    n_adic_loc = int((adic['Escopo do teste'] == ESC_ADIC).sum()), int(adic[adic['Escopo do teste'] == ESC_ADIC]['valor-p'].notna().sum())
    n_adic_eleg = int((adic['Escopo do teste'] == ESC_ELEG).sum()), int(adic[adic['Escopo do teste'] == ESC_ELEG]['valor-p'].notna().sum())
    h19_prev = prev[prev['Hipótese'] == 'H19']
    L = []
    w = L.append
    nm = val['n_incorporadas']
    m = ctx.m
    tipos = val['tipos_incorporadas']
    if modo != 'final':
        w('> **RODADA RÁPIDA — NÃO É O RESULTADO FINAL.** Poucas permutações/bootstraps; não citar estes números.\n')
    w('# Relatório consolidado H1–H22 — audiências públicas do STF\n')
    w('Data de referência: 05/11/2026. Gerado por `run_all.py` (Python local, sem API). Análises **exploratórias e observacionais**: descrevem as menções observadas nas audiências cujo texto foi extraído; não estimam probabilidade de aproveitamento de contribuição, favorecimento, exclusão nem representatividade, pois não há universo completo de participantes nem de votos. Estas são correções de **análise e código**; o corpus e as classificações não foram reclassificados.\n')
    w('## 1. Resumo\n')
    n_p = int(prin['valor-p'].notna().sum())
    sig = prin[prin['valor-p BH'] < alfa]
    w(f'- Corpus: {fi(nm)} menções incorporadas (Contexto {fi(tipos["Contexto"])}, Relato {fi(tipos["Relato"])}, Argumento {fi(tipos["Argumento"])}); taxa argumentativa global {fx(100 * tipos["Argumento"] / nm, 2)}% (denominador: menções incorporadas); {fi(m.audiencia.nunique())} audiências; {fi(m.documento.nunique())} documentos.')
    w(f'- **Unidade inferencial: a audiência.** Nenhuma menção foi permutada ou tratada como réplica independente. Contrastes internos são reduzidos a um valor por audiência; heterogeneidade e concentração (H3, H6, H10, H21) são **descritivas**, sem valor-p.')
    w(f'- **Três eixos de leitura, que não se misturam:** (i) *cenário de dados* — coluna Análise: Principal (A) × Sensibilidade A+B; (ii) *estimando principal previsto* — coluna Escopo do teste = "{ESC_PREV}"; (iii) *análises adicionais* — "{ESC_ADIC}" e "{ESC_ELEG}" (ambas feitas sobre dados A) e "{ESC_AB}" (dados A+B; pode combinar com elegibilidade).')
    w(f'- Cenário A (coluna Análise = Principal (A)): {fi(len(prin))} linhas e {fi(n_p)} valores-p, dos quais **{fi(len(prev))} linhas e {fi(int(prev["valor-p"].notna().sum()))} valores-p são do escopo previsto principal**, {fi(n_adic_loc[0])} linhas ({fi(n_adic_loc[1])} valores-p) são adicionais local×eixo (H15) e {fi(n_adic_eleg[0])} linhas ({fi(n_adic_eleg[1])} valores-p) são sensibilidade de elegibilidade (H19). Entre as {fi(len(prev))} previstas: {fi(_inviavel(prev["Situação"]).sum())} inviáveis por suporte e {fi(prev["Situação"].str.startswith(("Descritivo", "Exploratório descritivo")).sum())} descritivas.')
    w(f'- **H19 — estimando principal sem teste viável:** {fi(_inviavel(h19_prev["Situação"]).sum())} das {fi(len(h19_prev))} comparações previstas (uma por categoria) são inviáveis por suporte; os {fi(int(prin[(prin["Hipótese"] == "H19")]["valor-p"].notna().sum()))} valores-p de H19 em A vêm **exclusivamente** da sensibilidade de elegibilidade (≥{fi(P["min_mencoes_sens_elegibilidade"])} menções por grupo), exploratória e não confirmatória.')
    w(f'- Sensibilidade de vínculo A+B (decisão do pesquisador): {fi(len(sens))} linhas, {fi(int(sens["valor-p"].notna().sum()))} com valor-p, **separadas** do cenário A; não alteram o estimando principal. Total geral da matriz: {fi(len(pub))} linhas; {fi(int(pub["valor-p"].notna().sum()))} valores-p ({fi(n_p)} em A + {fi(int(sens["valor-p"].notna().sum()))} em A+B). Os {fi(n_p)} de A **não** são todos do escopo principal previsto.')
    w(f'- Com BH < {fx(alfa, 2)} no cenário A: {fi(len(sig))} testes ({", ".join(sorted(set(sig["Hipótese"]), key=lambda x: int(x[1:])))}); ver §10 para leitura e ressalvas (em especial H4, confundido com local).')
    w(f'- Apenas até {fi(m.audiencia.nunique())} audiências são unidades inferenciais; as {fi(nm)} menções são unidades de contagem.\n')
    w('## 2. Decisões e precedência\n')
    w(f'1. **Vínculo institucional (decisão do pesquisador, `config/decisao_vinculo_institucional.json`):** {decisao["decisao_pesquisador"]}. Análise principal: {decisao["analise_principal"]}. Sensibilidade: {decisao["sensibilidade"]}. A decisão não está mais pendente.')
    w(f'2. Categoria do ator: **o XLSX final é a autoridade** (inclui Partido Político). A categoria do JSON (`classificacao`) coincide com o XLSX em {fi(check["json_classificacao_igual_xlsx"])}/{fi(val["atores_xlsx"])} linhas. O campo `categoria_revisada = Pendente` do JSON ({fi(check["historico_json_revisada_pendente"])} linhas, todas com categoria final {", ".join(check["historico_json_revisada_pendente_categoria_final"])}) é **histórico** e não autoriza alterar a categoria da planilha nem indica erro dela; não há divergência final de rótulos.')
    w(f'3. Os rótulos finais (tipo da menção e categoria do ator) são usados como estão; nada foi reavaliado. Proveniência das {fi(nm)} inclusões: {fi(val["origem_incorporadas"].get("Claude sem revisão humana"))} sem revisão humana registrada e {fi(val["origem_incorporadas"].get("Humana consolidada"))} humanas consolidadas. A incerteza de classificação, cobertura e vieses **não** está representada em nenhum IC: os ICs por reamostragem (bootstrap) de audiências descrevem só a variabilidade das audiências observadas sob essa reamostragem; não pressupõem amostra probabilística nem representatividade.')
    w(f'4. A coluna "Menção incorporada" da lista de atores é metadado e não filtro: o corpus é a decisão `Incorporar`. Discordâncias entre o indicador Sim/Não e o derivado da ponte A: {fi(val["indicador_discordancias_com_derivado_A"])}; zeros não são inferidos de linhas ausentes.')
    w(f'5. AP33: o cadastro traz intervalo julgamento−audiência = {fi(check["intervalo_ap33_preservado_dado_original"])} ano; o dado original é **preservado** e não tratado como duração negativa verdadeira. Fica fora do denominador de H2 e H16 (explícito na coluna N/Limitações) e entra nas demais análises com o ano de julgamento cadastrado; sensibilidade com o valor mantido em H2.\n')
    w('## 3. Integração e validações\n')
    w(f'Chave: (audiência, nome normalizado) — {cfg["normalizacao_chave"]} Separador do campo Pessoa: `{cfg["separador_multivalor"]}`. IDs de menção e de ator não coincidem; sem fuzzy. As validações críticas **interrompem** a execução antes de qualquer resultado (`src/validacao.py`); as contagens abaixo foram recalculadas das fontes brutas.\n')
    v = [('Linhas da planilha de menções', val['n_linhas_planilha'], f'colunas: {fi(check["n_colunas_planilha"])}'), ('Incorporadas (IDs únicos)', val['n_incorporadas'], f'recalculado da planilha: {fi(check["n_incorporadas_recalculado"])}'),
         ('Atores (XLSX = JSON)', val['atores_linhas_igualdade_xlsx_json'], f'IDs únicos; prefixo E: {fi(val["atores_prefixo_E"])}'),
         ('Tokens de pessoa (campo Pessoa)', val['tokens_pessoa_total'], f'status: {val["tokens_pessoa_status"]}'), ('Pares menção–pessoa únicos (nível A)', val['pares_mencao_pessoa_A'], f'plano: {fi(cfg["referencia_plano_integracao"]["pares_mencao_pessoa"])}'),
         ('Menções com vínculo direto A', val['mencoes_diretas_A'], f'plano: {fi(cfg["referencia_plano_integracao"]["mencoes_diretas"])}'), ('Atores com menção direta A', val['atores_diretos_A'], f'plano: {fi(cfg["referencia_plano_integracao"]["atores_diretos"])}'),
         ('Menções classificadas multirrótulo (A)', val['mencoes_multirrotulo'], 'flags sobrepõem-se; cada menção conta uma vez no universo'), ('Menções mistas A (classificado + pessoa não resolvida)', val['mencoes_mistas'], 'explícitas na tabela principal')]
    w(md_tabela([{'Item': a, 'Valor': fi(b) if isinstance(b, (int, np.integer)) else b, 'Observação': c} for a, b, c in v], ['Item', 'Valor', 'Observação']) + '\n')
    estados = sorted(set(val['estados']) | set(val['AB_estados']))
    w('Estados mutuamente exclusivos por menção (cada menção em exatamente um): `classificado` (≥1 vínculo com categoria válida; **Outros e Partido Político são categorias válidas, não NA**), `identificado_sem_classificacao` (há pessoa/instituição nos campos, mas sem vínculo direto — não é Outros nem genérico), `identificado_irresolvido_categoria_contraditoria` (entidade cujas pessoas afiliadas têm categorias distintas), `generica_nao_aplicavel` (**exige** que o alvo da extração confirme "audiência pública" além dos campos vazios) e `sem_nome_alvo_nao_generico`.\n')
    w(md_tabela([{'Estado': e, 'A (principal)': fi(val['estados'].get(e, 0)), '% A': fx(100 * val['estados'].get(e, 0) / nm, 1), 'A+B (sensibilidade)': fi(val['AB_estados'].get(e, 0)), '% A+B': fx(100 * val['AB_estados'].get(e, 0) / nm, 1)} for e in estados], ['Estado', 'A (principal)', '% A', 'A+B (sensibilidade)', '% A+B']) + '\n')
    w('Categorias entre as menções classificadas (prevalências **sobrepostas**; não somam o total):\n')
    w(md_tabela([{'Categoria': cfg['alias_exibicao'].get(k, k), 'Menções A': fi(n), 'Menções A+B': fi(val['AB_categorias_mencoes_flags'][k]), 'Atores na lista final': fi(val['atores_categorias_xlsx'].get(k, 0))} for k, n in val['categorias_mencoes_flags'].items()], ['Categoria', 'Menções A', 'Menções A+B', 'Atores na lista final']) + '\n')
    w(f'**Sensibilidade A+B — construção.** A unidade do vínculo institucional é a **entidade** (audiência, entidade normalizada), não a pessoa afiliada: {fi(val["AB_entidades_total"])} entidades; {fi(val["AB_entidades_contraditorias"])} com categorias contraditórias entre afiliados (ficariam irresolvidas). A categoria da entidade é um **proxy** (categoria da participação das pessoas afiliadas). Pessoas afiliadas não são contadas como mencionadas: a categoria entra uma vez por (menção, categoria). Vários alvos com categorias distintas formam menção multirrótulo resolvida ({fi(val["AB_mencoes_multirrotulo"])} menções em A+B). Menções classificadas: {fi(val["mencoes_classificadas"])} em A e {fi(val["AB_mencoes_classificadas"])} em A+B ({fi(val["AB_mencoes_classificadas_somente_via_B"])} só via B); menções mistas (classificadas e com algum alvo não resolvido) em A+B: {fi(val["AB_mencoes_mistas"])}. Candidatos de proveniência: `data/processed/ponte_B_candidatos_proveniencia.csv`; entidades: `data/processed/entidades_B.csv`.\n')
    w('## 4. Desenho inferencial\n')
    w(f'- Unidade: audiência. Contrastes internos (H4, H8, H11, H12, H17, H19) são calculados dentro de audiência (ou documento×audiência em H4) e reduzidos a **um valor por audiência**; o estimando é a média dessas diferenças (pesos iguais). IC: bootstrap percentil (reamostragem) de audiências. Regra de emissão: comparações entre eixos exigem ≥{fi(P["min_audiencias_ci"])} audiências **em cada eixo**; contrastes internos e correlações exigem ≥{fi(P["min_audiencias_ci"])} audiências no total; o N dos grupos (ex.: 9+10) aparece na coluna N e na Incerteza. Ex.: H20 tem 19 audiências elegíveis (9+10) e, por ter menos de {fi(P["min_audiencias_ci"])} em um eixo, não emite IC. p: **inversão de sinais** das diferenças por audiência — exato (2^n) para n ≤ 16 e Monte Carlo com +1 acima disso — que **assume simetria em torno de zero sob a nula**; não é teste exato geral de igualdade nem causal. p e IC referem-se à mesma média; a mediana é descritiva e é outro estimando.')
    w(f'- Comparações entre audiências (H1, H2, H5, H9, H15, H20, H22): permutação de rótulos/valores **entre audiências** (trocabilidade das audiências sob a nula; eixos, classes e anos não foram randomizados). Seeds por análise: `(seed global {fi(P["seed"])}, CRC32 do rótulo)`; {fi(P["n_permutacoes"])} permutações e {fi(P["n_bootstrap"])} réplicas bootstrap; p Monte Carlo = (extremos+1)/(B+1).')
    w('- H13/H16: OLS por audiência com erros-padrão HC3 (t, n−k g.l.) e bootstrap de audiências estratificado por eixo; aproximação com poucas audiências, não causal; posto, suporte por eixo e alavancagem verificados; comparação com modelo sem interação.')
    w('- H3, H6, H10, H21: descrição com denominadores, **sem valor-p** (qualquer teste por permutação de menções ou binomial pressuporia menções independentes).')
    w(f'- Suporte predefinido: ≥{fi(P["min_audiencias_teste"])} audiências por teste; ≥{fi(P["min_mencoes_por_grupo_na_audiencia"])} menções por grupo e audiência (H4: ≥{fi(P["min_mencoes_por_grupo_no_documento"])} por documento×audiência). Abaixo do suporte o resultado é descritivo/inviável, **sem valor-p** e sem ajuste de limiares para obter testes. A única alternativa é a sensibilidade exploratória de elegibilidade de H19 (≥{fi(P["min_mencoes_sens_elegibilidade"])} por grupo), executada para todas as categorias, rotulada como não confirmatória e em família BH própria.')
    w('- Famílias BH predeterminadas (config), aplicadas só aos testes efetivamente executados; NA preservado: ' + '; '.join(f'{f}: {", ".join(h)}' for f, h in cfg['familias_BH'].items()) + '. Linhas A+B e sensibilidades de elegibilidade têm famílias próprias e não entram na família principal.')
    w('- A reamostragem de blocos não estima erro de classificação, cobertura documental nem vieses; ICs condicionam-se à classificação final.\n')
    w('## 5. Matriz resumida por hipótese\n')
    w(md_tabela(resumo_hipoteses(mat, cfg).to_dict('records'), ['Hipótese', 'Linhas previstas (A)', 'Previstos com valor-p', 'Previstos inviáveis', 'Descritivos', 'menor valor-p BH (previstos)', 'Linhas adicionais/elegibilidade (A)', 'Adicionais com valor-p', 'Linhas A+B', 'A+B com valor-p', 'Observação de escopo']) + '\n')
    w('Contagens por escopo: *previstas* = estimando principal previsto (cenário A); *adicionais/elegibilidade* = análises extras sobre A (H15 local×eixo; H19 elegibilidade); *A+B* = sensibilidade de vínculo. Perguntas por hipótese: `results/h1_h22/resumo_por_hipotese.csv`.\n')
    w('A matriz completa (14 colunas exigidas + Análise, Escopo do teste, Teste, Família e valores numéricos; H1–H22 todas presentes, inclusive inviáveis) está em `results/h1_h22/matriz_resultados_H1_H22.csv`.\n')
    w('## 6. Resultados por hipótese (cenário A; escopo indicado quando não é o previsto principal)\n')
    for h, g in prin.groupby('Hipótese', sort=False):
        w(f'### {h} — {cfg["hipoteses"][h]["Pergunta"]}\n')
        for row in g.to_dict('records'):
            p, q = row['valor-p'], row['valor-p BH']
            ptxt = f'valor-p {fp(p)}; BH {fp(q)}' if np.isfinite(p) else 'sem valor-p'
            tag = '' if row['Escopo do teste'] == ESC_PREV else f' [escopo: {row["Escopo do teste"]}]'
            w(f'- **{row["Teste"]}**{tag} — N: {row["N"]}. {row["Estimativa"]}. {row["Incerteza"]}. {ptxt}. *{row["Situação"]}.*')
            if row['Robustez'] and row['Robustez'] != 'n/a':
                w(f'  - Robustez: {row["Robustez"]}')
            w(f'  - {row["Interpretação"]}')
        lims = list(dict.fromkeys(g['Limitações'].tolist()))
        w('\n  Limitações: ' + ' | '.join(l for l in lims if l) + '\n')
        if str(g['Hipótese'].iloc[0]) == 'H8':
            w('\n  '+NOTA_H8+'\n')
    w('## 7. Sensibilidade A+B (H19–H22) — separada da análise principal\n')
    w('Mesmos métodos e suportes da análise principal, aplicados à classificação ampliada por entidade (proxy). Comparação com A:\n')
    comp = []
    chave = lambda s: re.sub(r'\s*\[A\+B\]', '', s)
    pa = prin.set_index(['Hipótese', 'Teste'])
    for r in sens.to_dict('records'):
        k = (r['Hipótese'], chave(r['Teste']))
        a = pa.loc[k] if k in pa.index else None
        def cel(x):
            if x is None:
                return '—'
            if np.isfinite(x['valor-p']):
                return f'{fx(x["estimativa_num"], 3, True)} (p {fp(x["valor-p"])}; q {fp(x["valor-p BH"])})'
            return 'sem teste (' + x['Situação'].split(':')[0] + ')'
        if r['Hipótese'] in ('H19', 'H20', 'H22') and not r['Situação'].startswith('Inviável') or (a is not None and np.isfinite(a['valor-p'])):
            comp.append({'Hipótese': r['Hipótese'], 'Teste': _curto(chave(r['Teste']), 95), 'A (principal)': cel(a), 'A+B (sensibilidade)': cel(pd.Series(r))})
    if comp:
        w(md_tabela(comp, ['Hipótese', 'Teste', 'A (principal)', 'A+B (sensibilidade)']) + '\n')
    for h, g in sens.groupby('Hipótese', sort=False):
        w(f'**{h} (A+B):** ' + ' | '.join(f'{_curto(chave(r["Teste"]), 80)} → {_curto(r["Estimativa"], 120)}; {"valor-p " + fp(r["valor-p"]) + "; BH " + fp(r["valor-p BH"]) if np.isfinite(r["valor-p"]) else r["Situação"].split(":")[0]}' for r in g.to_dict('records')) + '\n')
    w('## 8. Figuras\n')
    w('Cada figura declara unidade e denominador e aponta seus dados (CSV). PNG 300 dpi e SVG em `results/figures/`; nenhuma figura codifica significância.\n')
    w(md_tabela([{'Figura': f['arquivo_png'], 'Hipóteses': f['hipoteses'], 'Unidade': f['unidade'], 'Denominador': f['denominador'], 'Dados': f'results/figures/{f["dados"]}'} for f in figs], ['Figura', 'Hipóteses', 'Unidade', 'Denominador', 'Dados']) + '\n')
    for f in figs:
        w(f'![{f["hipoteses"]} — {f["arquivo_png"]} (unidade: {f["unidade"]}; denominador: {f["denominador"]})](../results/figures/{f["arquivo_png"]})\n')
    w('## 9. Sensibilidades predefinidas\n')
    w('Retirar uma audiência por vez e a maior audiência; sem Relatório; sem AP33; sem atribuição de ministro por metadado (autoria plena); apenas local Voto (H4); peso por menção versus por audiência; valor cadastrado da AP33 mantido em H2; sensibilidade de elegibilidade (≥2 por grupo) em H19; nível A+B (§7). As estimativas estão na coluna Robustez da matriz.')
    fr_p = raiz / 'results/diagnostics/frases_repetidas_entre_documentos.csv'
    if fr_p.exists():
        fr = pd.read_csv(fr_p)
        w(f'Frases repetidas entre processos ({fi(fr["grupo_texto"].nunique())} grupos, {fi(len(fr))} ocorrências no diagnóstico anterior) **não** foram colapsadas: não há regra autorizada; as contagens preservam todas as ocorrências.\n')
    w('## 10. Conclusão\n')
    ex = prin[prin['valor-p'].notna()]
    n_sig = int((ex['valor-p BH'] < alfa).sum())
    w(f'**Panorama.** No cenário A houve {fi(len(ex))} testes com valor-p, dos quais {fi(int((ex['Escopo do teste'] == ESC_PREV).sum()))} do escopo previsto principal e {fi(int((ex['Escopo do teste'] != ESC_PREV).sum()))} de análises adicionais/sensibilidade de elegibilidade; {fi(n_sig)} com BH < {fx(alfa, 2)} e {fi(len(ex) - n_sig)} inconclusivos. Resultados não significativos, inviáveis e descritivos são resultados científicos: indicam que, com {fi(m.audiencia.nunique())} audiências, a maioria das associações investigadas não é distinguível do acaso ou não tem suporte para teste. A ausência de significância não prova ausência de efeito.\n')
    w('**Testes com BH abaixo do limiar (leitura exploratória):**\n')
    if n_sig:
        for r in ex[ex['valor-p BH'] < alfa].to_dict('records'):
            conf = ' **Confundido com o local do acórdão; não atribui efeito à função de relator.**' if r['Hipótese'] == 'H4' else ''
            w(f'- {r["Hipótese"]}, {_curto(r["Teste"], 120)}: {r["Estimativa"]}; {r["Incerteza"]}; valor-p {fp(r["valor-p"])}, BH {fp(r["valor-p BH"])}.{conf}')
        w('\nSão contrastes por audiência sob hipótese de simetria; descrevem as audiências observadas, não causam nem generalizam.\n')
    else:
        w('- Nenhum teste da análise principal atingiu BH abaixo do limiar.\n')
    w('**Medidas de associação, intervalos e p/q de todos os testes executados (cenário A; coluna Escopo distingue previstos de adicionais):**\n')
    tab = [{'H': r['Hipótese'], 'Escopo': r['Escopo do teste'], 'Teste': _curto(r['Teste'], 85), 'Estimativa': _curto(r['Estimativa'], 100), 'Incerteza': _curto(r['Incerteza'], 90), 'p': fp(r['valor-p']), 'q (BH)': fp(r['valor-p BH']), 'Leitura': _resultado(r, alfa)} for r in ex.to_dict('records')]
    w(md_tabela(tab, ['H', 'Escopo', 'Teste', 'Estimativa', 'Incerteza', 'p', 'q (BH)', 'Leitura']) + '\n')
    w('**Descritivos (sem valor-p):**\n')
    for r in prin[prin['Situação'].str.startswith(('Descritivo', 'Exploratório descritivo'))].to_dict('records'):
        w(f'- {r["Hipótese"]}, {_curto(r["Teste"], 100)}: {_curto(r["Estimativa"], 330)}.')
    w('\n**Inviáveis por suporte (não testados):**\n')
    for r in prin[_inviavel(prin['Situação'])].to_dict('records'):
        w(f'- {r["Hipótese"]}, {_curto(r["Teste"], 100)}: {_curto(r["Situação"], 240)}.')
    h19 = prin[prin['Hipótese'] == 'H19']
    h19x = h19[h19['Escopo do teste'] == ESC_ELEG]
    h19p = h19[h19['Escopo do teste'] == ESC_PREV]
    w(f'\n**H19 e o critério predefinido.** No escopo previsto principal (≥{fi(P["min_mencoes_por_grupo_na_audiencia"])} menções por grupo em ≥{fi(P["min_audiencias_teste"])} audiências) **nenhuma categoria teve teste viável**: {fi(_inviavel(h19p["Situação"]).sum())} das {fi(len(h19p))} linhas previstas são inviáveis. Os {fi(h19x["valor-p"].notna().sum())} valores-p de H19 em A pertencem à sensibilidade de elegibilidade (≥{fi(P["min_mencoes_sens_elegibilidade"])} por grupo; {fi(len(h19x))} linhas, uma por categoria): exploratória, não confirmatória e fora do escopo principal.\n')
    w('**Sensibilidade A+B.** ' + (f'No conjunto A+B ({fi(val["AB_mencoes_classificadas"])} menções classificadas contra {fi(val["mencoes_classificadas"])} em A), {fi(sens["valor-p"].notna().sum())} linhas tiveram valor-p; {fi((sens["valor-p BH"] < alfa).sum())} com BH < {fx(alfa, 2)} nas suas famílias próprias. ' if len(sens) else '') + 'A análise principal e seu estimando permanecem os de A; compare as estimativas na tabela do §7 e trate a diferença entre A e A+B como medida de sensibilidade ao proxy institucional.\n')
    w('**Contribuições (sem apoio em referências bibliográficas, que não foram buscadas ou inventadas).**\n')
    h8 = ex[ex['Hipótese'] == 'H8']
    loc_sig = int((h8['valor-p BH'] < alfa).sum())
    w(f'- Descritiva: base estruturada de {fi(nm)} menções em {fi(m.audiencia.nunique())} audiências, com três funções (Contexto, Relato, Argumento) e proxies de individualização de alvo; a taxa argumentativa é medida de composição das menções observadas, não de aproveitamento de contribuições.')
    w(f'- Estrutura do acórdão: {fi(loc_sig)} de {fi(len(h8))} contrastes de taxa de Argumento entre locais tiveram BH < {fx(alfa, 2)}; as estimativas e ICs estão na tabela acima. A composição por local (3 categorias) é apresentada em H8 sem teste de associação com menções como réplicas. Cautela: o local é um dos indícios da própria classificação do tipo (METODOLOGIA, §14.2), logo o padrão não é validação independente da tipologia (ver nota em H8 e §11).')
    w('- Metodológica: separar unidade de contagem (menção) de unidade inferencial (audiência); declarar a hipótese de simetria do teste de inversão de sinais; marcar suporte insuficiente em vez de reduzir limiares; manter heterogeneidade e concentração como descrição quando a inferência exigiria independência entre menções.')
    w('- Agenda: construir denominador de votos/manifestações elegíveis; validar amostra humana dos rótulos para estimar erro de classificação; ampliar a cobertura de classificação dos atores; revisar a cronologia cadastral da AP33.\n')
    w('## 11. Limitações gerais\n')
    w('- '+NOTA_H8+'\n')
    n_meta = int(m['atribuicao_metadado'].sum())
    n_np = int((m['autoria_plena'] == 0).sum())
    for t_ in [f'Levantamento condicionado à extração e aos critérios de inclusão; não é censo de menções nem de audiências; a ausência de candidatos (AP44) não significa ausência de referências.',
               f'{fi(n_meta)} menções têm ministro atribuído por metadado (relator) e {fi(n_np)} têm autoria não plena: o nome do ministro não prova que proferiu a passagem; o Relatório é parte estrutural do documento, não voto pessoal; H21 não indica preferência individual.',
               'H4: o relator aparece quase só em "Voto do Relator"; a comparação mistura relator e local e a comparação restrita ao local Voto não tem audiências elegíveis; não se atribui efeito à função de relator.',
               'AP33: intervalo cadastrado −1 preservado como dado original, fora de H2/H16.',
               'Individualização (H11/H12/H17) é proxy do preenchimento de campos; não indica ação, influência nem contribuição específica.',
               'Incidências por categoria são prevalências sobrepostas (multirrótulo); nunca somar como partição. Partido Político: atores na lista, mas nenhuma menção vinculada em A nem em A+B; sem estimativa.',
               'Categoria institucional (A+B) é proxy da participação de pessoas afiliadas à entidade; só sensibilidade.',
               'Poucas audiências por teste (frequentemente 5–20 elegíveis): baixa potência; testes de inversão de sinais dependem da hipótese de simetria; processos conexos compartilham texto.',
               'A incerteza da classificação por IA e da extração não é propagada; não há universo de participantes nem de votos.']:
        w(f'- {t_}')
    w('\n## 12. Reprodução\n')
    w('```\n' + comando + '\n```\n')
    w(f'Python local em `.venv`; versões em `requirements.lock`; SHA-256 de entradas (antes e depois), scripts, configuração (inclusive decisão sobre B), seeds por análise e saídas em `results/manifesto_execucao.json`. Modo desta execução: **{modo}**.\n')
    w('## 13. Arquivos\n')
    w('- `data/processed/`: `mencoes_principal_atores.csv` (1 linha por menção, nível A), `mencoes_sensibilidade_AB.csv`, `atores_classificados.csv`, `ponte_mencao_ator.csv`, `ponte_B_candidatos_proveniencia.csv`, `entidades_B.csv`, `diagnostico_B_por_mencao.csv`.\n- `results/h1_h22/`: matriz CSV/JSON (principal e A+B), resumo, tabelas `T_*.csv`, `validacao_integracao.json`, `numeros_relatorio.json`.\n- `results/figures/`: PNG/SVG, `dados/` e `figuras_indice.csv`.\n')
    caminho.write_text('\n'.join(L), encoding='utf-8')


def escrever_html(md_path: Path, html_path: Path, fig_dir: Path):
    import markdown
    corpo = markdown.markdown(md_path.read_text(encoding='utf-8'), extensions=['tables', 'toc', 'fenced_code'])

    def emb(mt):
        alt, src = mt.group(1), mt.group(2)
        svg = (fig_dir / Path(src).name.replace('.png', '.svg'))
        if svg.exists():
            return f'<img alt="{alt}" src="data:image/svg+xml;base64,{base64.b64encode(svg.read_bytes()).decode()}" style="max-width:100%">'
        return mt.group(0)
    corpo = re.sub(r'<img alt="([^"]*)" src="([^"]+)"\s*/?>', emb, corpo)
    css = ('body{font-family:system-ui,Helvetica,Arial,sans-serif;max-width:1100px;margin:2em auto;padding:0 1em;line-height:1.45;color:#222}'
           'table{border-collapse:collapse;font-size:.82em;margin:1em 0;display:block;overflow-x:auto}th,td{border:1px solid #ccc;padding:3px 6px;vertical-align:top}'
           'th{background:#f0f0f0}code{background:#f4f4f4;padding:0 3px}blockquote{background:#fff3cd;margin:1em 0;padding:.5em 1em}img{margin:.5em 0}')
    html_path.write_text(f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Relatório H1–H22 — audiências públicas do STF</title><style>{css}</style></head><body>{corpo}</body></html>', encoding='utf-8')
