import json
import hashlib
from pathlib import Path
from avaliar_contexto_v2 import metrics

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'contexto_v2'
joint=OUT/'conjunta_contexto'
if (joint/'metricas.json').exists() and not (joint/'config.json').exists():
    (joint/'config.json').write_text(json.dumps({'experimento':'conjunta_contexto','temperatura':0,'max_tokens_saida':100,'treinamento_novo':False,'registro_reconstituido_apos_execucao':True,'sha256_dados':hashlib.sha256((OUT/'desenvolvimento_contexto.json').read_bytes()).hexdigest(),'sha256_adaptador':hashlib.sha256((ROOT/'adaptadores/adapters.safetensors').read_bytes()).hexdigest()},indent=2))
rows=json.loads((OUT/'desenvolvimento_corrigido.json').read_text())
gold={r['id']:{'corpus':r['corpus'],'tipo':r['tipo']} for r in rows}
summary={}
for mode,folder in [('base_original','20260910_163111'),('ajustado_original','20260910_171311')]:
    old=json.loads((ROOT/'resultados'/folder/'predicoes.json').read_text())
    preds=[{'id':p['id'],'tarefa':'conjunta','humano':gold[p['id']],'previsto':{'corpus':p['corpus_ia'],'tipo':p['tipo_ia']},'erro':p['erro'],'segundos':p['segundos']} for p in old]
    summary[mode]=metrics(preds)
    (OUT/f'{mode}_recalculado.json').write_text(json.dumps({'fonte_execucao':folder,'predicoes_reavaliadas':preds,'metricas':summary[mode]},ensure_ascii=False,indent=2))
for experiment in ['conjunta_contexto','tipo_original','tipo_contexto']:
    path=OUT/experiment/'metricas.json'
    if path.exists():summary[experiment]=json.loads(path.read_text())
(OUT/'comparacao.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
labels={'base_original':'Base, contexto original','ajustado_original':'Ajustado, contexto original','conjunta_contexto':'Ajustado, contexto ampliado','tipo_original':'Somente tipo, contexto original','tipo_contexto':'Somente tipo, contexto ampliado'}
report=['# Avaliação com contexto local — desenvolvimento','',
        'Gabarito revisado: 30 casos, 11 Incorporar e 19 Excluir. A correção humana foi aplicada apenas na versão 2, preservando a origem e as execuções anteriores. Nenhum novo treinamento foi realizado.','',
        '| Experiência | Casos | Respostas inválidas | Acertos de corpus | Acertos completos | Acertos de tipo nos incorporados humanos |',
        '|---|---:|---:|---:|---:|---:|']
for key,m in summary.items():
    type_result=m['tipo_sobre_incorporados']
    report.append(f"| {labels[key]} | {m['n']} | {m['invalidas']} | {str(m['acertos_corpus'])+'/'+str(m['n']) if 'acertos_corpus' in m else 'Não avaliado'} | {str(m['acertos_completos'])+'/'+str(m['n']) if 'acertos_completos' in m else 'Não avaliado'} | {type_result['acertos']}/{type_result['n']} |")
if 'conjunta_contexto' in summary:
    m=summary['conjunta_contexto'];before=summary['ajustado_original']
    report+=['','## Interpretação', '',f"Na tarefa conjunta, o contexto ampliado recuperou {m['incorporaveis_recuperadas']} das {m['incorporaveis']} incorporações humanas, contra {before['incorporaveis_recuperadas']} com o contexto original."]
    if m['acertos_completos']<before['acertos_completos']:
        report+=['','O contexto ampliado não deve substituir o fluxo anterior. Nesta experiência, fornecer mais texto piorou o desempenho. Não houve aplicação aos pendentes.']
    report+=['','O próximo experimento deve tratar seleção de evidências e adequação das instruções/formato como hipóteses a testar, não simplesmente aumentar o número de etapas de treinamento. É necessário distinguir contexto, relato e argumento antes de automatizar a classificação do corpus.']
report+=['','Na tarefa conjunta, uma exclusão indevida conta como erro de tipo. Na tarefa isolada, o modelo recebe a informação humana de que a menção pertence ao corpus: esses números não são diretamente equivalentes a um fluxo autônomo. Respostas inválidas contam como erro, sem normalização posterior dos rótulos.','',
         '## Recuperação documental','',
         'Foram indexadas 1.323 páginas do RE 1037396, 1.118 do RE 1057258 e 360 da transcrição da audiência. A consulta é automática no programa, não uma abertura autônoma de PDFs pelo modelo. A página central, trechos das páginas vizinhas e dois resultados de busca lexical na transcrição são acrescentados ao contexto original. As fontes e os textos efetivamente entregues estão registrados na pasta desta versão.','',
         'Uma busca lexical pode recuperar passagens inadequadas. Presença do participante na transcrição não comprova que uma citação autônoma dele no acórdão derive da audiência. Nem o inteiro teor nem páginas de outras audiências foram enviados integralmente ao modelo em cada classificação.','',
         '## Limitações','',
         'Esta é uma comparação exploratória em 30 casos de uma única audiência de desenvolvimento. As métricas não são uma estimativa final para o corpus. O teste final permanece reservado. A tarefa de tipo contém cinco Contexto, dois Relato e quatro Argumento.','',
         'O modelo foi treinado com contexto mais curto e saída conjunta; a versão ampliada e a tarefa isolada mudam essas condições. Eventual queda não demonstra que o contexto documental seja inútil. Não se deve corrigir o gabarito para aumentar a concordância com a IA.','',
         '## Arquivos','',
         '- `correcoes.json`: alteração humana e sua origem.','- `comparacao.json`: métricas consolidadas.','- `rastreabilidade.json`: páginas e localização dos trechos recuperados.','- `desenvolvimento_contexto.json`: entradas documentais utilizadas.','- Pastas `conjunta_contexto`, `tipo_original` e `tipo_contexto`: respostas por caso e métricas.','',
         'O modelo ajustado existente e os dados de treino não foram alterados. Para consultar as métricas novamente, use CONTEXTO_V2.command, opção 1. O menu anterior continua representando a versão histórica.']
(OUT/'RELATORIO.md').write_text('\n'.join(report)+'\n')
