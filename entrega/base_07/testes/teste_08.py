# Testes offline (sem Earth Engine) da lógica pura da 08 v4.
# As funções e constantes são extraídas do próprio 08_auditoria_completa_SAB.py pela AST e executadas num
# espaço isolado: testa o código exato que vai para o Colab, sem rodar a conexão com o Earth Engine.
# Rodar: python3 testes/teste_08.py  (a partir da pasta do pacote)
import ast
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(AQUI, '..', '08_auditoria_completa_SAB.py')
ARQ_V3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dados', '08_auditoria_completa_SAB_v3.py')
J5_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dados', 'J5_tmax_2026.csv')   # cópia da auditoria J

FUNCOES = ['ms_para_txt', 'data_ms', 'log', 'achado', 'tem_384', 'tres_apos_240', 'detectar_transicao', 'status_f5',
           'rebaixar_aceito', 'status_d10', 'dias_acima_recorde', 'salto_emenda', 'comparar_gfs_x_era5',
           'confianca_esperada', 'teto_razao_esperado', 'ultimo_dia_continuo_era5', 'checar_d14', 'status_d14', 'avaliar_roni', 'bandas_v21', 'checar_matriz_v21',
           'criterio_detalhe', 'criterio_rs', 'grade_nativa', 'checar_q1', 'avaliar_j1']
CONSTANTES = ['TRANSFORM', 'INICIO_RODADAS_03', 'RECORDE_TMAX_BR', 'SALTO_EMENDA_MAX_C', 'Q1_DIA', 'J1_ESPERADO',
              'J1_C_FORA_APROX', 'J1_TOL_B', 'K1D_C_DENTRO', 'DIAS_CLASSES_Q1', 'Q1_MAX_COINC', 'ORDEM_TRIMESTRES', 'VERSOES_GFS_SAB', 'FAIXAS_V21', 'VARS_V21', 'CONTRATO_V21',
              'METODO_TEMP_GFS_ESPERADO', 'METODO_UR_RS_GFS_ESPERADO', 'TETO_RAZAO_CURTO_ESPERADO', 'TETO_RAZAO_LONGO_ESPERADO', 'CONTRATO_V15', 'ACEITOS', 'ORDEM_STATUS']

FALHAS = []


def confere(cond, msg):
    print(('  ok   ' if cond else '  FALHA ') + msg)
    if not cond:
        FALHAS.append(msg)


def carregar():
    arvore = ast.parse(open(ARQ, encoding='utf-8').read())
    nos, achados = [], set()
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(isinstance(t, ast.Name) and t.id in CONSTANTES for t in no.targets):
            nos.append(no)
            achados |= {t.id for t in no.targets if isinstance(t, ast.Name)}
        elif isinstance(no, ast.FunctionDef) and no.name in FUNCOES:
            no.decorator_list = []
            nos.append(no)
            achados.add(no.name)
    faltam = set(FUNCOES + CONSTANTES) - achados
    assert not faltam, f'não achei no 08: {faltam}'
    ns = {'math': math, 're': re, 'np': np, 'pd': pd, 'datetime': datetime, 'timezone': timezone,
          'timedelta': timedelta, 'ACHADOS': [], 'CONTEXTO': {},
          'ARQ_LOG': os.path.join(tempfile.mkdtemp(), 'LOG.txt')}
    exec(compile(ast.Module(body=nos, type_ignores=[]), ARQ, 'exec'), ns)
    return ns


M = carregar()

# -------------------------------------------------------------------------------------------------
# Estruturas de rodada do GFS (como no F2 do LOG_COMPLETO da 08 atual)
# -------------------------------------------------------------------------------------------------
PRE_2016 = list(range(3, 37, 3))                                                    # 12 imagens, até 36 h
R172 = list(range(1, 121)) + list(range(123, 241, 3)) + list(range(252, 385, 12))  # 172: sem a hora 0
R173 = [0] + R172                                                                   # 173: com a hora 0
R208 = list(range(1, 121)) + list(range(123, 241, 3)) + list(range(243, 385, 3))   # 208: sem a hora 0
R209 = [0] + R208                                                                   # 209: com a hora 0


def antigo_tem_384(h):      # teste da 08 v3 (linha 1046), para mostrar o erro do M08-02
    return max(h) >= 384 and sum(1 for x in h if x <= 120) == 120


print('\n[F5] estruturas de rodada')
confere(len(R172) == 172 and len(R173) == 173 and len(R208) == 208 and len(R209) == 209, 'tamanhos 172/173/208/209')
confere(M['tem_384'](R172) and M['tem_384'](R173), 'tem_384 aceita rodadas com e sem a hora 0')
confere(M['tem_384'](R209) and M['tem_384'](R208), 'tem_384 aceita as rodadas de 208/209 imagens')
confere(not M['tem_384'](PRE_2016) and not M['tem_384']([]), 'tem_384 recusa rodada de 36 h e lista vazia')
confere(not M['tem_384']([h for h in R173 if h != 57]), 'tem_384 recusa rodada sem uma hora entre 1 e 120')
confere(antigo_tem_384(R172) and not antigo_tem_384(R173), 'o teste antigo recusava a rodada com a hora 0 (erro M08-02)')
confere(M['tres_apos_240'](R208) and M['tres_apos_240'](R209), 'tres_apos_240 aceita 208/209')
confere(not M['tres_apos_240'](R172) and not M['tres_apos_240'](R173), 'tres_apos_240 recusa 172/173 (12 em 12 h)')
confere(not M['tres_apos_240']([h for h in R209 if h != 300]), 'tres_apos_240 recusa rodada sem a hora 300')


def serie(ini, fim, regra):
    dias = [d.strftime('%Y-%m-%d') for d in pd.date_range(ini, fim)]
    return dias, {d: regra(d) for d in dias}


print('\n[F5] transição dia a dia (384 h; rodadas com e sem a hora 0; dia sem rodada; falso início)')


def regra_384(d):
    if d == '2016-08-10':
        return None                                    # dia sem rodada 00Z
    if d == '2016-07-05':
        return R173                                    # falso início isolado
    if d < '2016-07-24':
        return PRE_2016
    # depois da transição: até 2017-02-07 a maioria tem a hora 0; depois, sem a hora 0
    return R173 if d < '2017-02-08' else R172


dias, hs = serie('2016-07-01', '2017-03-01', regra_384)
ok = [bool(hs[d]) and M['tem_384'](hs[d]) for d in dias]
d, nota = M['detectar_transicao'](dias, ok)
confere(d == '2016-07-24', f'transição de 384 h em 2016-07-24 (obtido {d} {nota})')
ok_antigo = [bool(hs[x]) and antigo_tem_384(hs[x]) for x in dias]
primeiro_antigo = next(x for x, o in zip(dias, ok_antigo) if o)
confere(primeiro_antigo == '2017-02-08', f'o teste antigo apontaria 2017-02-08, a primeira rodada sem a hora 0 '
        f'(obtido {primeiro_antigo})')

print('\n[F5] transição de 3 em 3 h depois de 240 h')
dias, hs = serie('2019-05-15', '2019-07-15', lambda x: (R173 if x < '2019-06-13' else (R209 if x[-1] in '02468' else R208)))
ok = [bool(hs[x]) and M['tres_apos_240'](hs[x]) for x in dias]
confere(M['detectar_transicao'](dias, ok)[0] == '2019-06-13', '3 h depois de 240 h desde 2019-06-13')
d, nota = M['detectar_transicao'](dias[30:], ok[30:])
confere(d is None and 'já valia' in nota, f'janela começando depois da transição: None ({nota})')
d, nota = M['detectar_transicao'](dias[:20], ok[:20])
confere(d is None and 'não encontrada' in nota, f'janela sem transição: None ({nota})')
confere(M['detectar_transicao']([], [])[0] is None, 'sem dias: None')
# transição com poucas falhas depois (>= 90% em 30 dias) continua valendo
ok2 = [False] * 10 + [True] * 5 + [False] + [True] * 30
dias2 = [f'd{i:02d}' for i in range(len(ok2))]
confere(M['detectar_transicao'](dias2, ok2)[0] == 'd10', 'uma falha isolada depois da transição não muda a data')
ok3 = [False] * 10 + [True] * 2 + [False] * 20 + [True] * 30
dias3 = [f'd{i:02d}' for i in range(len(ok3))]
confere(M['detectar_transicao'](dias3, ok3)[0] == 'd32', 'falso início de 2 dias é ignorado')

print('\n[F5] status contra o início do 03 v4')
confere(M['status_f5']('2016-07-24', '2019-06-13', '2021-03-23') == 'OK', '03 começa depois das duas mudanças: OK')
confere(M['status_f5']('2016-07-24', '2021-06-12', '2021-03-23') == 'ATENÇÃO', '03 antes de uma mudança: ATENÇÃO')
confere(M['status_f5'](None, '2019-06-13', '2021-03-23') == 'INFO', 'data não localizada: INFO')
confere(M['INICIO_RODADAS_03'] == '2021-03-23', 'INICIO_RODADAS_03 = 2021-03-23 (contrato)')

# -------------------------------------------------------------------------------------------------
print('\n[J5] recorde e emenda com os dados reais da auditoria J (J5_tmax_2026.csv)')
j5 = pd.read_csv(J5_CSV, sep=';', decimal=',', encoding='utf-8-sig', index_col='dia')
acima = M['dias_acima_recorde'](j5)
confere([x[0] for x in acima] == ['2026-10-24', '2026-10-25', '2026-10-26', '2026-10-27'],
        f'4 dias acima de 44,8 °C, como a J relatou (obtido {acima})')
confere(M['RECORDE_TMAX_BR'] == 44.8, 'recorde = 44,8 °C')
t = pd.DataFrame({'versao': ['provisoria_era5', 'provisoria_gfs'], 'tmax_max': [44.8, 44.81]}, index=['a', 'b'])
confere(M['dias_acima_recorde'](t) == [('b', 44.81)], 'exatamente 44,8 não conta; 44,81 conta')
e = M['salto_emenda'](j5)
confere(e is not None and e['dia_era5'] == '2026-10-06' and e['dia_gfs'] == '2026-10-07',
        f'emenda 06/10 -> 07/10 (obtido {e and (e["dia_era5"], e["dia_gfs"])})')
confere(e['salto'] == 2.4 and e['atencao'] and e['dias_entre'] == 1, f'salto +2,40 °C > 2 °C: ATENÇÃO (obtido {e})')


def tab_emenda(v_era, v_gfs, dia_gfs='2026-10-07'):
    return pd.DataFrame({'versao': ['provisoria_era5', 'provisoria_era5', 'provisoria_gfs', 'provisoria_gfs'],
                         'tmax_max': [40.0, v_era, v_gfs, 43.0]},
                        index=['2026-10-05', '2026-10-06', dia_gfs, '2026-10-20'])


confere(not M['salto_emenda'](tab_emenda(41.7, 43.7))['atencao'], 'salto de exatamente 2,0 °C: aceito')
confere(M['salto_emenda'](tab_emenda(41.7, 43.71))['atencao'], 'salto de 2,01 °C: ATENÇÃO')
confere(M['salto_emenda'](tab_emenda(44.0, 41.5))['atencao'], 'queda de 2,5 °C também é ATENÇÃO (valor absoluto)')
confere(M['salto_emenda'](tab_emenda(41.7, 42.0, '2026-10-09'))['dias_entre'] == 3, 'lacuna entre ERA5 e GFS é relatada')
confere(M['salto_emenda'](tab_emenda(41.7, 42.0).iloc[::-1])['dia_gfs'] == '2026-10-07', 'entrada fora de ordem')
confere(M['salto_emenda'](j5[j5['versao'] == 'provisoria_era5']) is None, 'sem dias GFS: None')
confere(M['salto_emenda'](j5[j5['versao'] != 'provisoria_era5']) is None, 'sem dias ERA5: None')

print('\n[J5] previsão GFS x ERA5 nas mesmas datas (CSV anterior)')
atual = j5.copy()
for dd in ('2026-10-07', '2026-10-08', '2026-10-09', '2026-10-10'):
    atual.loc[dd, ['versao', 'tmax_max', 'tmax_media']] = ['provisoria_era5', 41.5, 34.0]
cmp = M['comparar_gfs_x_era5'](j5, atual)
confere(list(cmp.index) == ['2026-10-07', '2026-10-08', '2026-10-09', '2026-10-10'], '4 datas que viraram ERA5')
confere(abs(cmp.loc['2026-10-07', 'dif_tmax_max'] - 2.62) < 1e-9, 'diferença GFS - ERA5 = 44,12 - 41,5 = 2,62')
confere(len(M['comparar_gfs_x_era5'](j5, j5)) == 0, 'nenhuma data trocou de fonte: vazio')

# -------------------------------------------------------------------------------------------------
print('\n[M08-08] ACEITOS')
for cod in ('C7', 'E4', 'H2', 'H4'):
    st, motivo = M['rebaixar_aceito'](cod, 'ATENÇÃO', {})
    confere(st == 'INFO' and motivo == M['ACEITOS'][cod], f'{cod}: ATENÇÃO -> INFO com motivo')
confere(set(M['ACEITOS']) == {'C7', 'E4', 'H2', 'H4', 'I1'}, 'ACEITOS = C7, E4, H2, H4, I1')
confere(M['rebaixar_aceito']('C7', 'OK', {}) == ('OK', ''), 'OK não muda')
confere(M['rebaixar_aceito']('C7', 'ERRO', {}) == ('ERRO', ''), 'ERRO nunca é rebaixado')
confere(M['rebaixar_aceito']('F4', 'ATENÇÃO', {}) == ('ATENÇÃO', ''), 'item fora da lista (F4) continua ATENÇÃO')
confere(M['rebaixar_aceito']('E3-rsup', 'ATENÇÃO', {}) == ('ATENÇÃO', ''), 'E3-rsup continua ATENÇÃO')
confere(M['rebaixar_aceito']('I1', 'ATENÇÃO', {'versoes_baselines': {'B1.1'}})[0] == 'INFO', 'I1 só B1.1: INFO')
confere(M['rebaixar_aceito']('I1', 'ATENÇÃO', {'versoes_baselines': {'B1.1', 'SEM_VERSAO'}})[0] == 'ATENÇÃO',
        'I1 com versão diferente de B1.1: continua ATENÇÃO')
# integração com achado(): status final, status original e motivo no significado
M['achado']('C7', 'ATENÇÃO', 'Convenção', 'imerg_12ant_12', 'sig')
M['achado']('F4', 'ATENÇÃO', 'Radiação', 'média do bloco')
a, b = M['ACHADOS'][-2], M['ACHADOS'][-1]
confere(a['status'] == 'INFO' and a['status_original'] == 'ATENÇÃO' and 'ATENÇÃO aceita' in a['significado'],
        'achado(C7) grava INFO, status_original ATENÇÃO e o motivo')
confere(b['status'] == 'ATENÇÃO' and b['status_original'] == 'ATENÇÃO', 'achado(F4) continua ATENÇÃO')
log_txt = open(M['ARQ_LOG'], encoding='utf-8').read()
confere('ℹ️ [C7]' in log_txt and '⚠️ [F4]' in log_txt, 'símbolos no log: ℹ️ C7 e ⚠️ F4')

# -------------------------------------------------------------------------------------------------
print('\n[D10] status por versão')
confere(M['status_d10']([{'alg': 'V1.0', 'n_dif': 0}, {'alg': 'V1.3', 'n_dif': 0}]) == 'OK', 'sem diferença: OK')
confere(M['status_d10']([{'alg': 'V1.0', 'n_dif': 0}, {'alg': 'V1.3', 'n_dif': 4}, {'alg': 'V1.4', 'n_dif': 4}]) == 'INFO',
        'só V1.3/V1.4 diferem (4 pixels): INFO')
confere(M['status_d10']([{'alg': 'V1.5', 'n_dif': 4}]) == 'ATENÇÃO', 'V1.5 diferente: ATENÇÃO')
confere(M['status_d10']([{'alg': 'V1.0', 'n_dif': 1}, {'alg': 'V1.3', 'n_dif': 4}]) == 'ATENÇÃO',
        'dia histórico V1.0 diferente: ATENÇÃO')
# [V4 revisão A-03] dias GFS V1.5 com cobertura contida na canônica: INFO; qualquer pixel fora dela ou fração: ATENÇÃO
g = {'alg': 'V1.5', 'versao': 'provisoria_gfs', 'n_dif': 6, 'so_no_dia': 0, 'so_no_SAB_2025_12_31': 6,
     'fracao_de_mascara_diferente': 0}
confere(M['status_d10']([{'alg': 'V1.0', 'n_dif': 0}, g]) == 'INFO', 'GFS V1.5 só com pixels faltando: INFO')
confere(M['status_d10']([dict(g, versao='provisoria_gfs_incompleta')]) == 'INFO', 'GFS incompleta V1.5 contida: INFO')
confere(M['status_d10']([dict(g, so_no_dia=1, n_dif=7)]) == 'ATENÇÃO', 'GFS V1.5 com pixel fora da canônica: ATENÇÃO')
confere(M['status_d10']([dict(g, fracao_de_mascara_diferente=2, n_dif=8)]) == 'ATENÇÃO', 'GFS V1.5 com fração diferente: ATENÇÃO')
confere(M['status_d10']([dict(g, versao='provisoria_era5')]) == 'ATENÇÃO', 'ERA5 V1.5 com pixels faltando: ATENÇÃO')
confere(M['status_d10']([dict(g, versao='definitiva')]) == 'ATENÇÃO', 'definitiva V1.5 com pixels faltando: ATENÇÃO')
confere(M['status_d10']([g, {'alg': 'V1.0', 'n_dif': 1}]) == 'ATENÇÃO', 'GFS contida + histórico diferente: ATENÇÃO')

# -------------------------------------------------------------------------------------------------
print('\n[D14] confiança por prazo e critérios dos dias de 2026')
rod = M['data_ms']('2026-10-07')
conf = {d: M['confianca_esperada'](M['data_ms'](d), rod) for d in
        ('2026-10-07', '2026-10-11', '2026-10-12', '2026-10-16', '2026-10-17', '2026-10-22')}
confere(conf == {'2026-10-07': 'alta', '2026-10-11': 'alta', '2026-10-12': 'media', '2026-10-16': 'media',
                 '2026-10-17': 'baixa', '2026-10-22': 'baixa'}, f'L1-5 alta, L6-10 media, L11+ baixa ({conf})')


def inv_v15(alg='V1.5'):
    linhas = []
    for d in pd.date_range('2026-01-01', '2026-10-06'):
        linhas.append({'dia': d.strftime('%Y-%m-%d'), 'versao': 'provisoria_era5', 'alg': alg, 'rodada': -1,
                       'Confianca_Prazo': '', 'fonte': 'ECMWF/ERA5_LAND/DAILY_AGGR', 'janela_chuva_utc': '00-24',
                       'matriz_gfs': '', 'metodo_temp_gfs': '', 'metodo_ur_rs_gfs': ''})
    dias_gfs = pd.date_range('2026-10-07', '2026-10-22')
    for i, d in enumerate(dias_gfs):
        ds = d.strftime('%Y-%m-%d')
        linhas.append({'dia': ds, 'versao': 'provisoria_gfs_incompleta' if i == len(dias_gfs) - 1 else 'provisoria_gfs',
                       'alg': alg, 'rodada': rod, 'Confianca_Prazo': M['confianca_esperada'](M['data_ms'](ds), rod),
                       'fonte': 'NOAA/GFS0P25 (rodada 00Z)', 'janela_chuva_utc': '00-24',
                       'matriz_gfs': 'SICSB_MATRIZ_GFS_V2 V2.1', 'metodo_temp_gfs': 'variancia',
                       'metodo_ur_rs_gfs': 'variancia',
                       'teto_razao_temp_gfs': M['teto_razao_esperado'](M['data_ms'](ds), rod)})
    return pd.DataFrame(linhas)


confere(M['CONTRATO_V15']['gfs'].get('metodo_temp_gfs') == 'variancia', 'contrato V1.5: dias GFS com metodo_temp_gfs = variancia')
confere(M['CONTRATO_V15']['gfs'].get('metodo_ur_rs_gfs') == 'variancia', 'contrato V1.5: dias GFS com metodo_ur_rs_gfs = variancia (K9A)')
inv = inv_v15()
res = M['checar_d14'](inv, '2026-10-06')
confere(all(v[0] is not False for v in res.values()), f'inventário V1.5 correto: todos os critérios ({[k for k, v in res.items() if v[0] is False]})')
confere(M['status_d14'](res, inv) == 'OK', 'status OK')
inv13 = inv_v15('V1.3')
res13 = M['checar_d14'](inv13, '2026-10-06')
confere(M['status_d14'](res13, inv13) == 'INFO', 'antes da 5b (V1.3): INFO "aguardando motor V1.5"')
confere(res13['Confianca_Prazo'][0] is None and res13['propriedades_contrato_V1.5'][0] is None,
        'sem dias V1.5: critérios de propriedades não se aplicam')
casos = {
    'datas_contiguas': lambda t: t.drop(index=100),
    'rodada_00Z': lambda t: t.assign(rodada=np.where(t['versao'] != 'provisoria_era5', rod + 6 * 3600000, -1)),
    'Confianca_Prazo': lambda t: t.assign(Confianca_Prazo=np.where(t['dia'] == '2026-10-12', 'alta', t['Confianca_Prazo'])),
    'incompleta_so_no_ultimo_dia': lambda t: t.assign(versao=np.where(t['dia'] == '2026-10-10', 'provisoria_gfs_incompleta', t['versao'])),
    'emenda_ERA5_GFS': lambda t: t[t['dia'] != '2026-10-07'],
    'todos_V1.5': lambda t: t.assign(alg=np.where(t['dia'] == '2026-03-01', 'V1.4', t['alg'])),
    'propriedades_contrato_V1.5': lambda t: t.assign(fonte=np.where(t['dia'] == '2026-10-08', 'NOAA/GFS0P25', t['fonte'])),
    'ordem_das_rotas': lambda t: t.assign(versao=np.where(t['dia'] == '2026-10-15', 'provisoria_era5', t['versao'])),
    'teto_razao_K11': lambda t: t.assign(teto_razao_temp_gfs=np.where(t['dia'] == '2026-10-20', 2.0, t['teto_razao_temp_gfs'])),
}
casos_metodo = {
    'dia GFS gravado com o aditivo': lambda t: t.assign(metodo_temp_gfs=np.where(t['dia'] == '2026-10-09', 'aditivo', t['metodo_temp_gfs'])),
    'dia GFS sem a propriedade': lambda t: t.assign(metodo_temp_gfs=np.where(t['dia'] == '2026-10-20', '', t['metodo_temp_gfs'])),
    'dia GFS com a UR/radiação no método original': lambda t: t.assign(metodo_ur_rs_gfs=np.where(t['dia'] == '2026-10-11', 'original', t['metodo_ur_rs_gfs'])),
    'dia GFS sem metodo_ur_rs_gfs': lambda t: t.assign(metodo_ur_rs_gfs=np.where(t['dia'] == '2026-10-21', '', t['metodo_ur_rs_gfs'])),
}
for nome, mudar in casos_metodo.items():
    t2 = mudar(inv.copy()).reset_index(drop=True)
    r2 = M['checar_d14'](t2, '2026-10-06')
    confere(r2['propriedades_contrato_V1.5'][0] is False and 'metodo_' in r2['propriedades_contrato_V1.5'][1],
            f'método gravado: {nome} acusa ({r2["propriedades_contrato_V1.5"][1][:80]})')
for crit, mudar in casos.items():
    t2 = mudar(inv.copy()).reset_index(drop=True)
    r2 = M['checar_d14'](t2, '2026-10-06')
    confere(r2[crit][0] is False and M['status_d14'](r2, t2) == 'ATENÇÃO', f'{crit} falha quando deveria: {r2[crit][1][:90]}')
te = M['teto_razao_esperado']
confere([te(M['data_ms'](d), rod) for d in ('2026-10-07', '2026-10-11', '2026-10-12', '2026-10-22')] == [2.0, 2.0, 1.0, 1.0],
        f"K11: teto esperado 2.0 nos prazos 1-5 e 1.0 do 6 em diante (rodada {M['ms_para_txt'](rod)})")
t2 = inv.copy()
t2.loc[t2['versao'] != 'provisoria_era5', 'teto_razao_temp_gfs'] = np.nan     # dias gravados antes da K11
r2 = M['checar_d14'](t2, '2026-10-06')
confere(r2['teto_razao_K11'][0] is False, 'K11: dias de prazo 6+ gravados antes da K11 (sem a propriedade) acusam')
u = M['ultimo_dia_continuo_era5']
confere(u({'2026-10-08', '2026-10-11', '2026-10-07'}) == ('2026-10-08', ['2026-10-09', '2026-10-10']),
        'ERA5 com lacuna: último dia contínuo (correção 21/10 18h)')
confere(u({'2026-10-05', '2026-10-06'}) == ('2026-10-06', []), 'ERA5 sem lacuna: último publicado')
r3 = M['checar_d14'](inv, '2026-10-08')
confere(r3['emenda_ERA5_GFS'][0] is False, 'ERA5-Land já andou (G1 = 08/10) e o SAB parou em 06/10: emenda falha')

# -------------------------------------------------------------------------------------------------
print('\n[H5] RONI_CPC_v6 x CPC')
ORD = M['ORDEM_TRIMESTRES']
rng = np.random.default_rng(1)
cpc = pd.DataFrame([{'ano': a, 'Trimestre': t_, 'RONI_2c': round(float(rng.uniform(-2, 2)), 2)}
                    for a in (1950, 1951) for t_ in ORD])
cpc.loc[cpc['RONI_2c'].abs() * 100 % 10 == 5, 'RONI_2c'] += 0.01       # sem empates de arredondamento


def novo_de(c):
    n = c.copy()
    n['RONI'] = n['RONI_2c'].round(1)
    n['mes'] = n['Trimestre'].map({t_: i + 1 for i, t_ in enumerate(ORD)})
    n['t_ms'] = [M['data_ms'](f'{a:04d}-{m:02d}-01') for a, m in zip(n['ano'], n['mes'])]
    n['ano'] = n['ano'].astype(float)                                  # o asset pode devolver 1950.0
    return n


CH = [(1950, 1, '1950_01'), (1950, 2, '1950_02'), (1950, 3, '1950_03')]
st, pr = M['avaliar_roni'](novo_de(cpc), cpc, CH)
confere(st == 'OK' and not pr, f'asset igual ao CPC: OK ({pr})')
st, pr = M['avaliar_roni'](novo_de(cpc.iloc[:-1]), cpc, CH)
confere(st == 'ATENÇÃO' and 'rode o 02' in pr[0], f'CPC com estação nova: ATENÇÃO ({pr})')
st, pr = M['avaliar_roni'](novo_de(cpc).drop(index=5), cpc, CH)
confere(st == 'ERRO', f'estação faltando no meio: ERRO ({pr[:2]})')
n = novo_de(cpc)
n.loc[3, 'mes'] = 5
confere(M['avaliar_roni'](n, cpc, CH)[0] == 'ERRO', 'mês central errado: ERRO')
n = novo_de(cpc)
n.loc[3, 't_ms'] += 86400000
confere(M['avaliar_roni'](n, cpc, CH)[0] == 'ERRO', 'system:time_start errado: ERRO')
# [V4 revisão B-06] a exportação de tabela pode não guardar system:time_start (A CONFIRMAR): sem ele, só ATENÇÃO
n = novo_de(cpc)
n['data_ms'] = n['t_ms']
n['t_ms'] = np.nan
st, pr = M['avaliar_roni'](n, cpc, CH)
confere(st == 'ATENÇÃO' and any('system:time_start não veio' in p for p in pr), f'sem system:time_start, data_ms certo: ATENÇÃO ({pr})')
n.loc[3, 'data_ms'] += 86400000
confere(M['avaliar_roni'](n, cpc, CH)[0] == 'ERRO', 'sem system:time_start e data_ms errado: ERRO')
n = novo_de(cpc)
n.loc[len(n) - 1, 'RONI_2c'] += 0.2
n.loc[len(n) - 1, 'RONI'] = round(n.loc[len(n) - 1, 'RONI_2c'], 1)
st, pr = M['avaliar_roni'](n, cpc, CH)
confere(st == 'ATENÇÃO' and any('revisou' in p for p in pr), f'CPC revisou a última estação: ATENÇÃO ({pr})')
n = novo_de(cpc)
n.loc[2, 'RONI'] += 0.3
confere(M['avaliar_roni'](n, cpc, CH)[0] == 'ERRO', 'valor antigo diferente do CPC: ERRO')
confere(M['avaliar_roni'](novo_de(cpc), cpc, [(1950, 1, '1950.0_01')])[0] == 'ERRO', 'chave do painel mal formada: ERRO')
confere(M['avaliar_roni'](novo_de(cpc), cpc, [])[0] == 'ERRO', 'chave do painel não calculada: ERRO')
n = novo_de(cpc)
n['data_ms'] = n['t_ms']
n['chave_join'] = [f'{int(a):04d}_{m:02d}' for a, m in zip(n['ano'], n['mes'])]
confere(M['avaliar_roni'](n, cpc, CH)[0] == 'OK', 'data_ms e chave_join gravados pelo 02 v4 conferem: OK')
n.loc[4, 'chave_join'] = '1950_5'
confere(M['avaliar_roni'](n, cpc, CH)[0] == 'ERRO', 'chave_join gravada errada: ERRO')
n = novo_de(cpc)
n['data_ms'] = n['t_ms'] + 1
confere(M['avaliar_roni'](n, cpc, CH)[0] == 'ERRO', 'data_ms diferente do mês central: ERRO')

# -------------------------------------------------------------------------------------------------
print('\n[E6] matriz V2.1')
INT16 = {'type': 'PixelType', 'precision': 'int', 'min': -32768, 'max': 32767}
FLT = {'type': 'PixelType', 'precision': 'float'}
confere(len(M['bandas_v21']()) == 100, '100 bandas no contrato')


def meta_ok():
    meta = {}
    for m in range(1, 13):
        bandas = {b: FLT for b in M['bandas_v21']()}          # contrato revisado: n_* em Float32
        props = dict(M['CONTRATO_V21'], mes_referencia=m, gerado_em='2026-10-21T10:00:00+00:00',
                     **{f'n_pares_{fx}': 1000 for fx in M['FAIXAS_V21']})
        meta[f'Matriz_GFS_{m:02d}'] = {'bandas': bandas, 'props': props}
    return meta


confere(M['checar_matriz_v21'](meta_ok()) == [], 'matriz conforme o contrato: sem problemas')
mm = meta_ok()
del mm['Matriz_GFS_12']
confere(any('faltam' in p for p in M['checar_matriz_v21'](mm)), '11 imagens: problema')
mm = meta_ok()
del mm['Matriz_GFS_01']['bandas']['n_L1']
confere(any('bandas' in p for p in M['checar_matriz_v21'](mm)), '99 bandas: problema')
mm = meta_ok()
mm['Matriz_GFS_02']['bandas']['n_L2a5'] = INT16
confere(any('Float32' in p for p in M['checar_matriz_v21'](mm)), 'n_L2a5 Int16 (fora do contrato revisado): problema')
mm = meta_ok()
mm['Matriz_GFS_03']['props']['versao_matriz'] = 'V2'
mm['Matriz_GFS_03']['props']['n_pares_L11a15'] = 0
mm['Matriz_GFS_03']['props']['mes_referencia'] = 4
p = M['checar_matriz_v21'](mm)
confere(len(p) == 3, f'versão, n_pares = 0 e mês errados: 3 problemas ({p})')
confere(M['criterio_detalhe'](0.35, 0.23) and not M['criterio_detalhe'](0.27, 0.23) and not M['criterio_detalhe'](0.29, 0.2),
        'detalhe: >= 1,2 x V1 e >= 0,3')
confere(M['criterio_rs'](0.93) and not M['criterio_rs'](1.0) and not M['criterio_rs'](0.8) and not M['criterio_rs'](None),
        'radiação: 0,85 <= q <= 0,99')

# -------------------------------------------------------------------------------------------------
print('\n[Q1] máscara gravada')
props = {'versao_mascara': 'Q1', 'dia_referencia': '2001-01-15', 'dias_classes': M['DIAS_CLASSES_Q1'],
         'n_classe_1': 70364, 'n_classe_2': 204,
         'n_classe_3': 229, 'n_classe_4': 880, 'gerado_em': 'x'}
cont = {1: 70364, 2: 204, 3: 229, 4: 880}
confere(M['checar_q1'](props, cont, M['TRANSFORM'], 0) == [], 'máscara conforme: sem problemas')
confere(len(M['checar_q1'](dict(props, n_classe_4=881.0), cont, M['TRANSFORM'], 0)) == 1, 'contagem diferente da propriedade')
confere(M['checar_q1'](dict(props, n_classe_4=880.0), cont, M['TRANSFORM'], 0) == [], 'propriedade numérica 880.0 = 880')
confere(len(M['checar_q1'](props, cont, [0.1, 0, -74, 0, -0.1, 5.4], 3)) == 2, 'grade errada e 3 pixels diferentes')
# [V4 revisão B-02] o asset exportado guarda a origem da região de exportação (12 pixels a oeste e ao norte)
T = M['TRANSFORM']
t_exp = [T[0], 0, T[2] - 12 * T[0], 0, T[4], T[5] - 12 * T[4]]
confere(M['grade_nativa'](t_exp) and M['grade_nativa'](T), 'origem deslocada por 12 pixels inteiros: mesma grade')
confere(M['checar_q1'](props, cont, t_exp, 0) == [], 'Q1 sem falso ⚠️ com a origem própria do asset')
confere(not M['grade_nativa']([T[0], 0, T[2] - 0.5 * T[0], 0, T[4], T[5]]), 'meio pixel de deslocamento: outra grade')
confere(not M['grade_nativa']([0.1, 0, T[2], 0, -0.1, T[5]]), 'escala 0,1 exata (≠ BR-DWGD): outra grade')
confere(not M['grade_nativa']([T[0], 0, T[2]]) and not M['grade_nativa'](None), 'transform incompleto: outra grade')
confere(len(M['checar_q1'](dict(props, versao_mascara='Q0'), cont, M['TRANSFORM'], 0)) == 1, 'versão errada')
confere(len(M['checar_q1']({k: v for k, v in props.items() if k != 'dias_classes'}, cont, M['TRANSFORM'], 0)) == 1,
        'máscara gravada antes da v4.1 (sem dias_classes): problema (V41-04)')
confere(M['checar_q1'](props, cont, M['TRANSFORM'], 0, 8) == [], '8 coincidências B -> A: aceitas (V41-07)')
confere(len(M['checar_q1'](props, cont, M['TRANSFORM'], 0, 21)) == 1, '21 coincidências: problema (B inflado?)')

print('\n[J1] classes permanentes')
h = [{'tipo': 'historico', 'A': 70364, 'B': 204, 'C': 1109, 'D': 73} for _ in range(3)]
confere(M['avaliar_j1'](h) == ('INFO', None), 'B 204 e C 1.109 nos 3 dias: INFO; sem definitivas de 2026')
confere(M['avaliar_j1'](h[:2] + [dict(h[0], C=1110)])[0] == 'ATENÇÃO', 'C mudou: ATENÇÃO')
# [V4.1 K1a] coincidências: B cai e A sobe na mesma quantidade
confere(M['avaliar_j1'](h[:2] + [dict(h[0], A=70371, B=197)])[0] == 'INFO', 'B 197 e A 70.371 (coincidência, A+B igual): INFO')
confere(M['avaliar_j1'](h[:2] + [dict(h[0], A=70364, B=197)])[0] == 'ATENÇÃO', 'B 197 sem A subir (A+B mudou): ATENÇÃO')
confere(M['avaliar_j1'](h[:2] + [dict(h[0], A=70378, B=190)])[0] == 'ATENÇÃO', 'B 190 (mais que 10 a menos): ATENÇÃO')
confere(M['avaliar_j1'](h[:2] + [dict(h[0], A=70363, B=205)])[0] == 'INFO', 'B 205 e A 70.363 (arredondamento): INFO')
confere(M['J1_C_FORA_APROX'] == 1060 and M['K1D_C_DENTRO'] == 48, 'referências da K1d (classe 4 ~1.060, classe 3 ~48)')
confere(M['avaliar_j1'](h + [{'tipo': 'definitiva_2026', 'A': 70568, 'B': 0, 'C': 1109, 'D': 73}])[1] == 'OK',
        'definitiva de 2026 com B = 0: OK')
confere(M['avaliar_j1'](h + [{'tipo': 'definitiva_2026', 'A': 70364, 'B': 204, 'C': 1109, 'D': 73}])[1] == 'ATENÇÃO',
        'definitiva de 2026 com B = 204: ATENÇÃO')

# -------------------------------------------------------------------------------------------------
print('\n[estrutura] seções, ordem e códigos antigos')
arv = ast.parse(open(ARQ, encoding='utf-8').read())
ordem = []
for no in arv.body:
    if isinstance(no, ast.FunctionDef):
        for dec in no.decorator_list:
            if isinstance(dec, ast.Call) and getattr(dec.func, 'id', '') == 'secao':
                ordem.append((dec.args[0].value, no))
cods = [c for c, _ in ordem]
confere(cods == ['A', 'B', 'C', 'D', 'D14', 'E', 'E6', 'F', 'G', 'H', 'H5', 'I', 'Q1', 'J1', 'J3', 'J5'],
        f'ordem das seções: antigas na mesma ordem, novas depois da seção-mãe ({cods})')
for c, fn in ordem:
    if c in ('D14', 'E6', 'H5', 'Q1', 'J1', 'J3', 'J5'):
        chamadas = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'achado']
        ultima = fn.body[-1]
        termina = any(isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'achado' for n in ast.walk(ultima))
        confere(bool(chamadas) and termina, f'seção {c} registra e termina em achado(...)')


def codigos_literais(caminho):
    out = set()
    for n in ast.walk(ast.parse(open(caminho, encoding='utf-8').read())):
        if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'achado' and n.args:
            a = n.args[0]
            if isinstance(a, ast.Constant):
                out.add(a.value)
            elif isinstance(a, ast.JoinedStr):
                out.add(''.join(v.value if isinstance(v, ast.Constant) else '{}' for v in a.values))
    return out


v3, v4 = codigos_literais(ARQ_V3), codigos_literais(ARQ)
confere(v3 <= v4, f'todos os códigos da v3 continuam na v4 (faltam {v3 - v4})')
print(f'   códigos novos: {sorted(v4 - v3)}')

print(f'\n{"TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S)"}')
sys.exit(1 if FALHAS else 0)
