# Teste offline da K22 (conferência depois de implantar o motor V1.6): regras puras e o contrato com o motor.
# Rodar: python3 testes/teste_k22.py
import os
import sys
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, '..')
SRC = open(os.path.join(RAIZ, 'validacoes', 'K22_conferencia_v16.py'), encoding='utf-8').read()
MOTOR = open(os.path.join(RAIZ, '05a_motor_sab_v1_6_SIMULACAO.py'), encoding='utf-8').read()
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


ns = {'__name__': 'teste_k22'}
exec(compile(SRC, 'K22', 'exec'), ns)
BRT = timezone(timedelta(hours=-3))

print('[janelas]')
mj = ns['minutos_ate_janela']
confere(mj(datetime(2026, 11, 6, 23, 30, tzinfo=BRT)) == 0 and mj(datetime(2026, 11, 6, 0, 45, tzinfo=BRT)) == 0,
        'v2: dentro da janela única (22h50 à 01h00)')
confere(mj(datetime(2026, 11, 6, 22, 10, tzinfo=BRT)) == 40 and mj(datetime(2026, 11, 6, 6, 30, tzinfo=BRT)) == 980,
        'v2: 22h10 = 40 min até a janela; manhã livre')

print('[inventário]')
base = [{'data': f'2026-01-{d:02d}', 'versao': 'provisoria_era5', 'alg': 'V1.6'} for d in range(1, 21)]
st, tab, txt = ns['resumir_inventario'](base + [{'data': '2026-11-10', 'versao': 'provisoria_gfs', 'alg': 'V1.6'}])
confere(st == 'OK' and '21 dias' in txt, 'tudo na V1.6: OK')
st, _, txt = ns['resumir_inventario'](base + [{'data': '2026-02-01', 'versao': 'provisoria_era5', 'alg': 'V1.5'}])
confere(st == 'ESPERAR' and '1 de 21' in txt, 'um dia ainda na V1.5: esperar a próxima rodada')
confere(ns['resumir_inventario']([])[0] == 'FALHA', 'nenhum dia: falha')

print('[coerência]')
linhas = [{'data': '2026-01-15', 'tipo': 'ERA5', 'n_pix': 80000, 'rs_acima': 0, 'ur_fora': 0, 'etr_acima': 0,
           'transp_acima': 0, 'chuva_acima': 0}, {'data': '2026-11-10', 'tipo': 'GFS', 'n_pix': 79000, 'rs_acima': 0,
                                                  'ur_fora': 0, 'etr_acima': 0, 'transp_acima': 0}]
confere(ns['resumir_coerencia'](linhas)[0] == 'OK', 'sem problemas: OK (dia GFS sem a coluna da chuva)')
linhas[0]['rs_acima'] = 3
confere(ns['resumir_coerencia'](linhas)[0] == 'FALHA' and 'rs_acima 3' in ns['resumir_coerencia'](linhas)[1],
        'radiação acima do céu claro acusada')

print('[emenda: razão dos desvios]')
rng = np.random.default_rng(5)
linhas, br = [], []
for pid in range(20):
    for mes in range(1, 11):
        br.append({'pid': pid, 'mes': mes, 'RH_sd': 8.0, 'u2_sd': 0.6, 'RH_m': 75.0, 'u2_m': 2.0})
        for dia in range(1, 29):
            linhas.append({'pid': pid, 'data': f'2026-{mes:02d}-{dia:02d}', 'RH': rng.normal(76, 8),
                           'u2': rng.normal(2.0, 0.6 * 1.7)})
r = ns['razao_desvios'](pd.DataFrame(linhas), pd.DataFrame(br))
confere(abs(r['RH'][0] - 1.0) < 0.05 and abs(r['RH'][1] - 1.0) < 0.3, f'UR com o desvio do BR-DWGD: razão {r["RH"][0]:.3f}')
confere(abs(r['u2'][0] - 1.7) < 0.08, f'vento com 1,7x o desvio: razão {r["u2"][0]:.3f}')
confere(ns['decidir_emenda'](r), 'v2: vento 1,7x (correção na média) não reprova: só a UR conta')
confere(ns['decidir_emenda']({'RH': (1.02, 0), 'u2': (0.95, 0)}), 'as duas na faixa: OK')
confere(not ns['decidir_emenda']({'RH': (1.24, 0), 'u2': (1.0, 0)}), 'v2: UR 1,24 (como antes da V1.6): falha')
confere(ns['METODO_ESPERADO'] == 'UR eqm; vento media' and "f'UR {METODO_UR_ERA5}; vento {METODO_VENTO_ERA5}'" in MOTOR
        and "METODO_UR_ERA5 = 'eqm'" in MOTOR and "METODO_VENTO_ERA5 = 'media'" in MOTOR,
        'v2: método esperado = o que o motor V1.6 grava (UR eqm; vento media)')

print('[contrato com o motor]')
for trecho in ("J.multiply(2.0 * math.pi / 365.0).cos().multiply(0.033).add(1.0)",
               "J.multiply(2.0 * math.pi / 365.0).subtract(1.39).sin().multiply(0.409)",
               "multiply(0.00002).add(0.75)"):
    confere(trecho in SRC and trecho in MOTOR, f'Rso com a mesma conta do motor: {trecho[:35]}')
confere(ns['FATOR_TETO_CHUVA'] == 1.5 and 'FATOR_TETO_CHUVA = 1.5' in MOTOR, 'mesmo teto da chuva do motor')
confere("select('pr_max_br')" in SRC and ns['ASSET_EQM'].endswith('SICSB_EQM_1986_2025'), 'teto lido da matriz EQM')
confere("filter(ee.Filter.eq('versao_algoritmo', VERSAO_NOVA)).size()" in SRC, 'confere que o histórico não tem a V1.6')
confere('ee.batch.Task.start = _bloqueado' in SRC, 'somente leitura')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
