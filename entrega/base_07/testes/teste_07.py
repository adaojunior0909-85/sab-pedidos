# Teste offline do 07a/07b_normais_CONFERIR (V4: M07-05, M07-03, M07-01, M07-02). Sem Earth Engine.
# As funções e constantes são tiradas do próprio 07a (ast), então o teste exercita o código do Colab.
# Rodar: python3 testes/teste_07.py  (a partir da pasta do pacote)
import ast
import calendar
import math
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

import os
SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '07a_normais_CONFERIR_1991_2020.py')
FUNCOES = {'dias_verif', 'meses_da_serie_base', 'anos_com_chuva', 'valores_como_referencia',
           'problemas_coerencia', 'comparar', 'comparar_percentis', 'quantil_local', 'percentil_da_banda',
           'limiares_locais', 'gama_local', 'dias_medios_mes'}
CONSTANTES = {'SIMULAR', 'MODO_CONFERENCIA', 'VERIFICAR', 'MESES_VERIFICACAO', 'DIAS_VERIFICACAO', 'DIAS_POR_MES',
              'RELATORIO_SPI_20', 'MIN_ANOS_COM_CHUVA_LEITURA', 'RELATORIO_QUALIDADE', 'MES_RELATORIO_QUALIDADE',
              'ANOS_MINIMOS', 'JANELA_LIMIARES', 'FRACAO_MIN_JANELA', 'UMIDADE_MAX_FISICA', 'LIMIAR_ZERO_CHUVA_MM',
              'MIN_ANOS_COM_CHUVA_SPI', 'MIN_DIAS_UMIDOS', 'VARS_SOMA', 'VARS_CONTAGEM', 'VARS_MEDIA',
              'VARS_EXTREMO', 'VARS_TOTAL', 'VARS_DIA', 'VARS_MES', 'QUANTIS_CHUVA', 'ESCALAS_SPI', 'ESCALAS_SPEI',
              'PERIODOS'}


def carregar():
    corpo = []
    for n in ast.parse(open(SCRIPT, encoding='utf-8').read()).body:
        if isinstance(n, ast.FunctionDef) and n.name in FUNCOES:
            corpo.append(n)
        elif isinstance(n, ast.Assign) and any(getattr(t, 'id', None) in CONSTANTES for t in n.targets):
            corpo.append(n)
    ns = {'np': np, 'pd': pd, 'math': math, 'calendar': calendar}
    exec(compile(ast.Module(body=corpo, type_ignores=[]), SCRIPT, 'exec'), ns)
    faltam = (FUNCOES | CONSTANTES) - set(ns)
    assert not faltam, f'não achei no script: {faltam}'
    return ns


S = carregar()
FALHAS = []


def ok(cond, msg):
    print(('  ok   ' if cond else '  FALHA ') + msg)
    if not cond:
        FALHAS.append(msg)


print('1. Configuração da conferência (M07-02, M07-05, M07-03, Q1)')
ok(S['MODO_CONFERENCIA'] is True and S['SIMULAR'] is True and S['VERIFICAR'] is True,
   'MODO_CONFERENCIA = True com SIMULAR = True e VERIFICAR = True')
ok(S['MESES_VERIFICACAO'] == (1, 2, 8), f"meses conferidos {S['MESES_VERIFICACAO']}")
ok(S['RELATORIO_SPI_20'] is True and S['MIN_ANOS_COM_CHUVA_LEITURA'] == 20, 'relatório do SPI ligado, regra dos 20')
ok(S['RELATORIO_QUALIDADE'] is True and S['MES_RELATORIO_QUALIDADE'] == 1, 'relatório Q1 ligado, janeiro')

print('2. Dias de verificação por mês (M07-05)')
dv = S['dias_verif']
ok(dv(1) == (1, 15, 31) and dv(8) == (1, 15, 31), f'janeiro e agosto {dv(1)} {dv(8)}')
ok(dv(2) == (1, 15, 28), f'fevereiro {dv(2)} (limiar só até o dia 28)')
ok(all(dv(m) == (1, 15, 30) for m in (4, 6, 9, 11)), 'meses de 30 dias: dia 31 vira 30')
for m in range(1, 13):
    ultimo = 28 if m == 2 else calendar.monthrange(2001, m)[1]
    ok(max(dv(m)) == ultimo and 15 in dv(m) and 1 in dv(m), f'mês {m:02d}: dias {dv(m)} existem no limiar (até {ultimo})')
mb = S['meses_da_serie_base']
ok(mb(2, dv(2)) == {2, 1, 12, 11, 10, 9, 3}, f'série-base de fevereiro inclui março (janela do dia 28): {sorted(mb(2, dv(2)))}')
ok(mb(1, dv(1)) == {1, 12, 11, 10, 9, 8, 2}, 'série-base de janeiro igual à de antes (V3)')
ok(mb(8, dv(8)) == {8, 7, 6, 5, 4, 3, 9}, 'série-base de agosto igual à de antes (V3)')
ok(mb(2, (1, 15)) == {2, 1, 12, 11, 10, 9}, 'sem dia perto do fim, não lê o mês seguinte')

print('3. Janelas dos limiares em fevereiro: lado local = lado Earth Engine (mesmas datas)')
a0, a1 = S['PERIODOS']['1991_2020']['anos']
datas = pd.date_range(f'{a0 - 1}-07-01', f'{a1}-12-31')
serie = pd.DataFrame({'nome': 'P', 'data': datas, 'tmax_C': datas.map(pd.Timestamp.toordinal).astype(float)})
serie['tmin_C'] = serie['tmax_C'] - 1e6
J = S['JANELA_LIMIARES']
n_min = math.ceil(S['FRACAO_MIN_JANELA'] * (2 * J + 1) * (a1 - a0 + 1))
for mes in (1, 2, 8):
    jan = S['limiares_locais'](serie, a0, a1, mes, dv(mes))['P']
    for d in dv(mes):
        esperado = set()
        lim_ini, lim_fim = date(a0, 1, 1), date(a1, 12, 31)
        for a in range(a0, a1 + 1):            # mesma conta de imagem_limiares (ee.Filter.date)
            c = date(a, mes, d)
            ini, fim = max(c - timedelta(days=J), lim_ini), min(c + timedelta(days=J), lim_fim)
            esperado |= {(ini + timedelta(days=i)).toordinal() for i in range((fim - ini).days + 1)}
        local = set(jan[f'tx90_d{d:02d}'].astype(int).tolist())
        ok(local == esperado and len(local) >= n_min, f'mês {mes:02d} dia {d:02d}: {len(local)} dias na janela (mínimo {n_min})')
fev = S['limiares_locais'](serie, a0, a1, 2, (28,))['P']['tx90_d28']
bis = [pd.Timestamp.fromordinal(int(x)) for x in fev if pd.Timestamp.fromordinal(int(x)).month == 2 and
       pd.Timestamp.fromordinal(int(x)).day == 29]
ok(len(bis) == 8, f'janela do dia 28/02 inclui os 8 dias 29/02 de 1991-2020 ({len(bis)})')

print('4. Regra do SPI: round(n × (1 − q0)) >= 20 com q0 em float32 (M07-03)')
q0 = np.float32(1 / 3)
bruto32 = np.float32(30) * (np.float32(1) - q0)
ok(bruto32 < 20 and f'{bruto32:.6f}' == '19.999998', f'30 × (1 − float32(1/3)) = {bruto32:.6f} em float32')
ok(30 * (1 - float(q0)) < 20, f'e {30 * (1 - float(q0)):.9f} em double: o problema é o q0 gravado, não a conta')
ok(S['anos_com_chuva'](30, q0) == 20, 'com o round: 20 anos com chuva')
erros_sem_round, casos = [], 0
for n in range(1, 31):
    for n_pos in range(0, n + 1):
        for q in (np.float32((n - n_pos) / n), np.float32(n - n_pos) / np.float32(n)):   # dois jeitos de chegar ao float32
            casos += 1
            r = S['anos_com_chuva'](n, q)
            r32 = np.round(np.float32(n) * (np.float32(1) - q))                         # conta toda em float32 (EE)
            if not (r == n_pos and r32 == n_pos and (r >= 20) == (n_pos >= 20)):
                FALHAS.append(f'anos_com_chuva({n}, {q}) = {r}/{r32}, esperado {n_pos}')
            if (n * (1 - float(q)) >= 20) != (n_pos >= 20):
                erros_sem_round.append((n, n_pos))
ok(not [f for f in FALHAS if f.startswith('anos_com_chuva')], f'round recupera n_pos em todos os {casos} casos (n de 1 a 30)')
ok((30, 20) in erros_sem_round, f'sem o round a regra erra em {sorted(set(erros_sem_round))}')
for n_pos in (9, 10, 19, 20, 21, 30):          # q0 do cálculo local (gama_local) segue a mesma regra
    tot = [0.0] * (30 - n_pos) + list(np.linspace(20, 200, n_pos))
    g = S['gama_local'](tot)
    if n_pos >= S['MIN_ANOS_COM_CHUVA_SPI']:
        ok(S['anos_com_chuva'](g['n'], np.float32(g['q0'])) == n_pos, f'gama_local com {n_pos} anos com chuva: q0 float32 -> {n_pos}')
    else:
        ok(np.isnan(g['q0']), f'gama_local com {n_pos} anos com chuva: SPI não ajustado (mínimo 10)')

print('5. Coerência física em função (mesmo bloco de antes, agora também nos gravados)')
dm = S['dias_medios_mes'](a0, a1, 2)
ok(abs(dm - (28 + 8 / 30)) < 1e-12, f'dias médios de fevereiro 1991-2020 = {dm:.4f}')
vals_n = {'P': dict({f'{v}_n': 30.0 for v in S['VARS_MES']}, nome='P', txx_media=35.0, tmax_C_media=30.0,
                    tmed_C_media=25.0, tmin_C_media=20.0, tnn_media=15.0, rx1day_media=50.0, pr_mm_media=200.0,
                    dias_chuva_1mm_media=10.0, dias_secos_media=dm - 10, graus_dia_media=300.0,
                    pr_mm_q20=100.0, pr_mm_q40=150.0, pr_mm_q60=200.0, pr_mm_q80=260.0, pr_mm_t33=140.0,
                    pr_mm_t67=230.0, soil_moisture_0_100cm_m3_m3_media=0.4, et_real_media=80.0,
                    et_potencial_media=120.0, spei1_n=30.0, spei1_alfa=20.0, spei3_n=30.0, spei3_alfa=40.0,
                    spi1_q0=0.0, pr_p95_umido=30.0, pr_p99_umido=60.0)}
vals_l = {'P': {'nome': 'P', 'tx90_d15': 33.0, 'tx10_d15': 27.0, 'tn90_d15': 22.0, 'tn10_d15': 16.0}}
pc = S['problemas_coerencia']
ok(pc(['P'], vals_n, vals_l, dv(2), dm) == [], 'ponto coerente: nenhum problema')
ruim = {'P': dict(vals_n['P'], tmed_C_media=31.0, spi1_q0=None, pr_p99_umido=20.0, spei3_alfa=None, pr_mm_q60=None)}
msgs = pc(['P'], ruim, {'P': dict(vals_l['P'], tn10_d15=None)}, dv(2), dm)
ok(len(msgs) == 5 and any('TXx' in m for m in msgs) and any('P99' in m for m in msgs) and any('SPEI-3' in m for m in msgs)
   and any('quintis' in m for m in msgs) and any('dia 15' in m for m in msgs), f'5 problemas acusados: {msgs}')
ok(pc(['P'], vals_n, {'P': {}}, (1, 28), dm) == [], 'sem dia 15 conferido, limiares do dia 15 não são exigidos')

print('6. Limiares gravados x recálculo do Earth Engine e x faixa local (M07-01, c3 e c4)')
bandas = ['tx90_d01', 'tx10_d01', 'tx90_d28']
ee_l = {'P': {'nome': 'P', 'tx90_d01': 31.25, 'tx10_d01': None, 'tx90_d28': 30.0}, 'Q': {'nome': 'Q', 'tx90_d01': 20.0}}
g_l = {'P': {'nome': 'P', 'tx90_d01': 31.2500004, 'tx10_d01': None, 'tx90_d28': 30.0}, 'Q': {'nome': 'Q', 'tx90_d01': 20.0}}
ref = S['valores_como_referencia'](ee_l, ['P', 'Q'], bandas)
ok(np.isnan(ref['Q']['tx90_d28']) and np.isnan(ref['P']['tx10_d01']), 'banda ausente ou mascarada vira NaN')
c4 = S['comparar'](g_l, ref)
ok(len(c4) == 6 and bool(c4.ok.all()), 'gravado = recálculo (float32, ausentes dos dois lados)')
g2 = {'P': dict(g_l['P'], tx90_d28=30.2), 'Q': dict(g_l['Q'], tx90_d28=25.0)}
c4 = S['comparar'](g2, ref)
ok(int((~c4.ok).sum()) == 2, 'acusa valor diferente e valor só no gravado')
jan = S['limiares_locais'](serie.assign(tmax_C=np.random.default_rng(1).normal(30, 3, len(serie))), a0, a1, 2, (1, 28))
x = jan['P']['tx90_d28']
gl = {'P': {b: S['quantil_local'](v, S['percentil_da_banda'](b), 8) for b, v in jan['P'].items()}}
c3 = S['comparar_percentis'](gl, jan, n_min)
ok(bool(c3.ok.all()) and len(c3) == 8, 'percentis tipo 8 dos limiares de fevereiro caem na faixa (c3)')
gl['P']['tx90_d28'] = float(np.max(x)) + 1
ok(not bool(S['comparar_percentis'](gl, jan, n_min).ok.all()), 'limiar gravado fora da faixa é acusado')

print(f"\n{'TODOS OS TESTES PASSARAM' if not FALHAS else f'{len(FALHAS)} FALHA(S): ' + str(FALHAS[:5])}")
sys.exit(1 if FALHAS else 0)
