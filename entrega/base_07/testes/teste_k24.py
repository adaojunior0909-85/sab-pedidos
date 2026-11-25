# Testes offline das funções puras da K24 (Tmax da previsão GFS x recorde do pixel)
import os, sys
from datetime import datetime, timedelta, timezone
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ns = {'__name__': 'k24_teste'}
exec(compile(open(os.path.join(AQUI, 'validacoes', 'K24_auditoria_tmax_gfs.py'), encoding='utf-8').read(), 'k24', 'exec'), ns)
falhas = 0
def confere(c, t):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + t); falhas += 0 if c else 1
BRT = timezone(timedelta(hours=-3))
mj = ns['minutos_ate_janela']
confere(mj(datetime(2026, 11, 10, 21, 50, tzinfo=BRT)) == 60 and mj(datetime(2026, 11, 10, 23, 30, tzinfo=BRT)) == 0,
        'janela 22h50-01h00; 21h50 = 60 min (o limite para começar)')
# agregar_blocos: dois blocos, um dia
p1 = {'max': {'e_20261102': 1.7, 't_20261102': 44.28}, 'g': {'g0_20261102_mean': 0.01, 'g0_20261102_count': 1000,
      'g1_20261102_mean': 0.004, 'g1_20261102_count': 1000, 'g2_20261102_mean': 0.0, 'g2_20261102_count': 1000},
      'c': {'c0_20261102': 42.6, 'c1_20261102': 43.6, 'c2_20261102': 44.28}}
p2 = {'max': {'e_20261102': -0.5, 't_20261102': 41.0}, 'g': {'g0_20261102_mean': 0.0, 'g0_20261102_count': 3000,
      'g1_20261102_mean': 0.0, 'g1_20261102_count': 3000, 'g2_20261102_mean': 0.0, 'g2_20261102_count': 3000},
      'c': {'c0_20261102': 41.0, 'c1_20261102': 41.0, 'c2_20261102': 41.0}}
t = ns['agregar_blocos']([p1, p2], ['2026-11-02'], True)
r = t.iloc[0]
confere(r['tmax_max'] == 44.28 and r['excesso_max'] == 1.7 and r['n_pix'] == 4000, 'agregar: máximos entre blocos e pixels somados')
confere(abs(r['pct_acima_0'] - 100 * 10 / 4000) < 1e-9 and abs(r['pct_acima_1'] - 100 * 4 / 4000) < 1e-9,
        'agregar: % ponderada pelos pixels de cada bloco')
confere(r['tmax_max_teto_0'] == 42.6 and r['tmax_max_teto_2'] == 44.28, 'agregar: máxima nacional com o teto de cada folga')
confere(abs(ns['pct_pixel_dias'](t, 1) - 0.1) < 1e-9, 'pct_pixel_dias')
confere(ns['decidir_p1'](0.12, 0.03) and not ns['decidir_p1'](0.12, 0.05) and not ns['decidir_p1'](0.04, 0.0),
        'P1: >= 3x o ERA5 e >= 0,05%')
x, rz = ns['bruto_de_calibrado'](43.36, 36.0, 34.5, 1.5, 2.0, 'L1')
confere(abs(rz - 0.75) < 1e-12 and abs((36.0 + (x - 34.5) * rz) - 43.36) < 1e-9, 'bruto_de_calibrado inverte a conta do motor')
_, rz = ns['bruto_de_calibrado'](40, 36, 34, 3.0, 1.0, 'L6a10')
confere(rz == 1.0, 'razão limitada a 1,0 nas faixas longas (K11), como no motor')
_, rz = ns['bruto_de_calibrado'](40, 36, 34, 0.2, 2.0, 'L1')
confere(rz == 0.5, 'razão com piso 0,5, como no motor')
tg = pd.DataFrame({'tmax_max_teto_0': [42.6, 42.0], 'tmax_max_teto_1': [43.6, 43.0], 'tmax_max_teto_2': [44.28, 44.0]})
f, det = ns['escolher_folga'](tg, 41.43, {0: 0.4, 1: 0.12, 2: 0.03})
confere(f == 0 and det[0][3] and not det[1][3] and not det[2][3] and abs(det[2][1] - 2.85) < 1e-9
        and abs(det[1][1] - 2.17) < 1e-9, 'folga: 2 °C repete o salto (+2,85) e 1 °C ainda salta +2,17 -> 0 °C')
f, _ = ns['escolher_folga'](tg, 41.43, {0: 0.6, 1: 0.12, 2: 0.03})
confere(f is None, 'folga: 0 °C pegaria 0,6% (> 0,5%) e as outras saltam demais -> nenhuma')
f, det = ns['escolher_folga'](tg, 41.43, {0: 0.9, 1: 0.8, 2: 0.6})
confere(f is None, 'folga: nenhuma quando o teto pegaria demais')
print('\nTODOS OS TESTES PASSARAM' if not falhas else f'\n{falhas} FALHA(S)'); sys.exit(1 if falhas else 0)
