# Testes offline das funções puras da K23 (auditoria da emenda ERA5 -> GFS da Tmax)
import os, sys
from datetime import datetime, timedelta, timezone
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ns = {'__name__': 'k23_teste'}
exec(compile(open(os.path.join(AQUI, 'validacoes', 'K23_auditoria_emenda_tmax.py'), encoding='utf-8').read(), 'k23', 'exec'), ns)
falhas = 0
def confere(c, t):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + t); falhas += 0 if c else 1
BRT = timezone(timedelta(hours=-3))
mj = ns['minutos_ate_janela']
confere(mj(datetime(2026, 11, 9, 22, 5, tzinfo=BRT)) == 45 and mj(datetime(2026, 11, 9, 23, 0, tzinfo=BRT)) == 0
        and mj(datetime(2026, 11, 9, 0, 59, tzinfo=BRT)) == 0, 'janela única 22h50-01h00; 22h05 = 45 min')
inv = [{'data': '2026-10-31', 'versao': 'provisoria_era5'}, {'data': '2026-11-01', 'versao': 'provisoria_era5'},
       {'data': '2026-11-02', 'versao': 'provisoria_gfs'}, {'data': '2026-11-03', 'versao': 'provisoria_gfs'}]
confere(ns['emenda_do_inventario'](inv) == ('2026-11-01', '2026-11-02'), 'emenda = último ERA5 -> 1º GFS depois dele')
confere(ns['emenda_do_inventario'](inv[:2]) == ('2026-11-01', None), 'sem GFS: None')
r = {'d_mean': -0.4, 'd_stdDev': 1.8, 'd_p1': -5, 'd_p99': 4, 'a_p99': 5.1, 'g5_mean': 0.012}
s = ns['stats_par'](r)
confere(s['abs_media'] == 0.4 and s['p99_abs'] == 5.1 and abs(s['pct_acima_5'] - 1.2) < 1e-9, 'stats_par')
rng = np.random.default_rng(1)
nat = [{'abs_media': abs(rng.normal(0, .5)), 'desvio': rng.uniform(1.2, 2.2), 'p99_abs': rng.uniform(4, 7)} for _ in range(80)]
ok, det = ns['decidir_c']({'abs_media': .3, 'desvio': 1.6, 'p99_abs': 5}, nat)
confere(ok and all(v[2] for v in det.values()), 'C: emenda típica dentro do p95 natural -> OK')
ok, det = ns['decidir_c']({'abs_media': .3, 'desvio': 3.5, 'p99_abs': 5}, nat)
confere(not ok and not det['desvio'][2], 'C: desvio da emenda acima do p95 natural -> ATENÇÃO')
confere(not ns['decidir_c']({'abs_media': .1, 'desvio': 1, 'p99_abs': 3}, nat[:5])[0], 'C: menos de 10 pares naturais -> não decide OK')
serie = pd.DataFrame({'data': ['2020-10-15', '2020-10-16', '2020-10-17', '2020-10-19'], 'max': [40, 42.5, 41, 44]})
sl = ns['saltos_maximo'](serie)
confere(list(np.round(sl, 2)) == [2.5, 1.5], 'D: só pares de dias seguidos (o buraco de 17 para 19 fica fora)')
saltos = np.r_[np.full(90, 1.0), np.full(10, 3.0)]
ok, f, p95 = ns['decidir_d'](saltos, 2.8)
confere(ok and abs(f - .10) < 1e-9, 'D: 10% dos saltos >= 2,8 -> OK')
ok, f, _ = ns['decidir_d'](np.r_[np.full(97, 1.0), np.full(3, 3.0)], -2.8)
confere(not ok and abs(f - .03) < 1e-9, 'D: 3% -> ATENÇÃO (sinal do salto não importa)')
confere(not ns['decidir_d'](np.ones(50), 1)[0], 'D: menos de 100 pares -> não decide OK')
confere(ns['decidir_e'](44.3, 43.5) and not ns['decidir_e'](44.3, 43.0) and not ns['decidir_e'](44.3, float('nan')),
        'E: até 1 °C acima do recorde do pixel')
print('\nTODOS OS TESTES PASSARAM' if not falhas else f'\n{falhas} FALHA(S)'); sys.exit(1 if falhas else 0)
