# Teste offline das funções puras da K26 (nenhuma fala com o Earth Engine).
# Rodar:  python -I teste_k26.py   (precisa de numpy e pandas)
import importlib.util
import os

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
ALVO = os.path.abspath(os.path.join(AQUI, '..', '..', 'K26_auditoria_final.py'))
spec = importlib.util.spec_from_file_location('k26', ALVO)
K = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K)


def confere(cond, msg):
    assert cond, msg
    print('ok  ' + msg)


# fator_candidato
f = K.fator_candidato([10.0, 0.0], [1.0, 0.0], 0.0, 5.0)
confere(np.allclose(f, [5.0, 0.0]), 'K=0 com teto 5: 10/1 vira 5; mês seco 0/0 vira 0')
confere(np.allclose(K.fator_candidato([3.0], [1.0], None, None), [1.0]), 'sem_fator devolve 1')
confere(np.allclose(K.fator_candidato([0.0], [0.0], 1.0, 5.0), [1.0]), 'K=1 estabiliza 0/0 em 1')

# avaliar_fatores: SMAP = 2 x ERA5, chuva sempre acima
rng = np.random.default_rng(1)
linhas = []
for pid in range(5):
    for d in pd.date_range('2015-04-01', '2025-12-31', freq='3D'):
        e = float(rng.gamma(0.5, 2.0))
        linhas.append({'pid': pid, 'data': d.strftime('%Y-%m-%d'), 'era': e, 'smap': 2 * e, 'pr': 4 * e + 1})
df = pd.DataFrame(linhas)
t = K.avaliar_fatores(df, 'smap', 'era', K.CANDIDATOS_R, K.R_ANOS_TREINO, K.R_ANOS_TESTE, pr='pr')
v = t.set_index('candidato')
confere(abs(v.loc['atual_teto5', 'vies_total_pct']) < 1.0, 'fator 2 dentro do teto: viés ~0')
confere(abs(v.loc['sem_fator', 'vies_total_pct'] + 50) < 1.0, 'sem fator: viés -50%')
confere(v.loc['atual_teto5', 'pct_acima_chuva'] == 0.0, 'chuva sempre acima: 0% acima da chuva')
t2, esc = K.escolher_fator(t, com_chuva=True)
confere(esc is not None and t2.set_index('candidato').loc[esc, 'aprovado'], f'escolhe um aprovado ({esc})')
confere(not t2.set_index('candidato').loc['sem_fator', 'aprovado'], 'sem_fator reprovado pelo viés')

# avaliar_vento: ERA5 com o dobro da variância do BR-DWGD
linhas = []
for pid in range(4):
    for d in pd.date_range('2016-01-01', '2025-12-31'):
        z = float(rng.normal())
        linhas.append({'pid': pid, 'data': d.strftime('%Y-%m-%d'), 'br_u2': 1.5 + 0.3 * z,
                       'era_dia': 2.0 + 0.6 * z, 'era_hora': 2.0 + 0.6 * z})
V = K.avaliar_vento(pd.DataFrame(linhas), K.V_ANOS_TREINO, K.V_ANOS_TESTE).set_index(['fonte', 'metodo'])
confere(abs(V.loc[('era_dia', 'media'), 'razao_desvio'] - 1.5) < 0.05, 'média preserva a variância relativa: 1,5')
confere(abs(V.loc[('era_dia', 'variancia'), 'razao_desvio'] - 1.0) < 0.05, 'variância corrige a razão para 1')
confere(bool(V.loc[('era_dia', 'variancia'), 'aprovado']), 'variância aprovada no caso sintético')
confere(not bool(V.loc[('era_dia', 'media'), 'aprovado']), 'média reprovada pela razão dos desvios')

# extremos_fora_da_faixa: o 1.099 mm de fevereiro que o histograma da K25 perdeu
mom = pd.DataFrame([{'mes': '2026-02', 'nome_classe': 'A', 'variavel': 'runoff_sup_mm',
                     'minimo_absoluto': 0.0, 'maximo_absoluto': 1099.5},
                    {'mes': '2026-02', 'nome_classe': 'A', 'variavel': 'pr_mm',
                     'minimo_absoluto': 0.0, 'maximo_absoluto': 300.0}])
ext = K.extremos_fora_da_faixa(mom)
confere(list(ext['variavel']) == ['runoff_sup_mm'], 'extremo absoluto acima de 500 mm é marcado')

# ajustar_vazias_por_desenho: tsolo vazio no GFS não é vazamento; no ERA5 é
p = pd.DataFrame([{'data': 'a', 'rota': 'GFS', 'versao': 'provisoria_gfs', 'tsolo_C': 0, 'pr_mm': 10, 'maximo': 10},
                  {'data': 'b', 'rota': 'ERA5', 'versao': 'provisoria_era5', 'tsolo_C': 0, 'pr_mm': 10, 'maximo': 10},
                  {'data': 'c', 'rota': 'GFS', 'versao': 'provisoria_gfs_incompleta', 'tsolo_C': 0, 'pr_mm': 0,
                   'maximo': 10}])
q = K.ajustar_vazias_por_desenho(p, ['tsolo_C', 'pr_mm'])
q = K.ajustar_vazias_por_desenho(q, ['tsolo_C', 'pr_mm'], K.VAZIAS_POR_VERSAO, coluna='versao')
confere(list(q['tsolo_C']) == [10, 0, 10], 'tsolo isento só no GFS')
confere(list(q['pr_mm']) == [10, 10, 10], 'chuva isenta no GFS incompleto')

# utilidades
confere(K.meses_entre('2015-04-01', '2016-02-01') == ['2015-04', '2015-05', '2015-06', '2015-07', '2015-08',
                                                       '2015-09', '2015-10', '2015-11', '2015-12', '2016-01'],
        'meses_entre exclui o mês final')
confere(len(K.dias_do_mes_calendario('2024-02')) == 29, 'fevereiro bissexto tem 29 dias')
confere(K.datas_da_janela('2026-03-01', 2) == ['2026-02-27', '2026-02-28', '2026-03-01', '2026-03-02', '2026-03-03'],
        'janela de ±2 dias atravessa o mês')
lon, lat = K.X0 + 10.5 * K.DX, K.Y0 - 20.5 * K.DX
reg = [['id', 'longitude', 'latitude', 'time', 'x'], ['i', lon, lat, 1767225600000, 1.0]]
r = K.regiao_para_pid(reg, {(10, 20): 7})
confere(list(r['pid']) == [7] and list(r['data']) == ['2026-01-01'], 'getRegion volta ao pid pelo índice da grade')
confere(K.RODADAS[K.RODADA][2] == K.PARTES, 'PARTES de acordo com a RODADA')
confere(K.RODADAS_EM_SEQUENCIA == [1, 5, 6] and all(r in K.RODADAS for r in K.RODADAS_EM_SEQUENCIA),
        'arquivo entregue com a sequência das rodadas que faltam: 1, 5 e 6 (v1.12)')
K.preparar_rodada(5, K.datetime(2026, 11, 22, 8, 0, tzinfo=K.BRT))
confere((K.RODADA, K.ANO_INI, K.ANO_FIM, K.DURACAO_ESTIMADA_MIN) == (5, 1961, 1970, 90)
        and K.ACUMULADO.endswith('K26_acumulado_rodada5') and 'K26_rodada5_20261122_080000' in K.PASTA
        and K.RESULTADOS == [], 'preparar_rodada troca anos, duração, pasta, checkpoint e zera os resultados')
confere(sum(K.DURACOES_MIN.get(r, 90) for r in K.RODADAS_EM_SEQUENCIA) == 225, 'sequência estimada em 225 min')

# avaliar_umidade: ERA5 mais seco e com o dobro da variação do SMAP
linhas = []
for pid in range(4):
    for d in pd.date_range('2015-04-01', '2025-12-31', freq='2D'):
        z = float(rng.normal())
        linhas.append({'pid': pid, 'data': d.strftime('%Y-%m-%d'), 'smap': 0.30 + 0.03 * z, 'era': 0.25 + 0.06 * z})
S = K.avaliar_umidade(pd.DataFrame(linhas), 'smap', 'era', K.R_ANOS_TREINO, K.R_ANOS_TESTE).set_index('candidato')
confere(set(S.index) == {'atual', 'cru', 'aditivo', 'variancia', 'eqm'}, 'umidade: os 5 candidatos medidos')
confere(abs(S.loc['variancia', 'razao_desvio'] - 1) < 0.05 and bool(S.loc['variancia', 'aprovado']),
        'umidade: variância acerta a razão dos desvios e é aprovada')
confere(abs(S.loc['eqm', 'vies']) < 0.01 and bool(S.loc['eqm', 'aprovado']), 'umidade: quantis sem viés e aprovado')
confere(not bool(S.loc['atual', 'aprovado']), 'umidade: o fator multiplicativo dobra a variação e é reprovado')
confere(S.loc['cru', 'vies'] < -0.04, 'umidade: cru fica 0,05 mais seco')
# assinatura de versão: a constante, a 1ª linha e o topo da lista VERSÕES têm de dizer a mesma coisa
with open(ALVO, encoding='utf-8') as f:
    linhas = f.read().splitlines()
num = K.VERSAO.split(' ')[1]                                   # 'v1.3'
topo = next(l for l in linhas if l.startswith('#   v'))
confere(f'K26 {num} ' in linhas[0] and topo.startswith(f'#   {num} '),
        f'versão {num} igual na constante, na 1ª linha e no topo da lista VERSÕES')
print('\nTODOS OS TESTES DA K26 PASSARAM')
