"""Teste offline da validação K11 (sem Earth Engine e sem Drive): dados sintéticos em que o GFS amortece a
variância nos prazos longos. Confere que o script roda até o fim, gera o zip e que o M1 corta as previsões
além do limite físico nos prazos 8 e 13 (o problema de Casa Nova de 22/10/2026).
Rodar: python3 testes/teste_k11.py (a partir da pasta do pacote)."""
import os, sys, pickle, subprocess, tempfile, glob
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, '..', 'validacoes', 'K11_validacao_razao_desvios_prazos_longos.py')
rng = np.random.default_rng(1)
dias = pd.date_range('2019-07-01', '2025-12-31')
linhas, npt = [], 30
clim = rng.uniform(26, 34, npt)
for L in (1, 3, 8, 13):
    hab = {1: 0.9, 3: 0.8, 8: 0.5, 13: 0.3}[L]
    amort = {1: 1.2, 3: 1.0, 8: 0.6, 13: 0.45}[L]
    for p in range(npt):
        sazonal = 3 * np.sin(2 * np.pi * dias.dayofyear / 365)
        anom = rng.normal(0, 2, len(dias))
        o = clim[p] + sazonal + anom
        g = clim[p] - 3 + sazonal + amort * (hab * anom + np.sqrt(1 - hab ** 2) * rng.normal(0, 2, len(dias)))
        linhas.append(pd.DataFrame({'pid': p, 'L': L, 'ok': 1, 'dia': dias.strftime('%Y-%m-%d'), 'o_tmax': o,
                                    'o_tmin': o - 11 + rng.normal(0, 1, len(dias)), 'g_tmax': g,
                                    'g_tmin': g - 10 + rng.normal(0, 1, len(dias))}))
falhas = 0
with tempfile.TemporaryDirectory() as d:
    arq = os.path.join(d, 'dados.pkl')
    with open(arq, 'wb') as f:
        pickle.dump((pd.concat(linhas, ignore_index=True), {}), f)
    env = dict(os.environ, K11_DADOS_LOCAIS=arq)
    p = subprocess.run([sys.executable, SCRIPT], cwd=d, env=env, capture_output=True, text=True, timeout=1800)
    saida = p.stdout + p.stderr

    def confere(c, m):
        global falhas
        print(('  OK   ' if c else '  FALHA ') + m)
        falhas += 0 if c else 1

    confere(p.returncode == 0, f'K11 roda até o fim (código {p.returncode})')
    confere('RESULTADO FINAL K11' in saida and 'Nada foi gravado no Earth Engine.' in saida, 'resultado final e aviso de só leitura')
    zips = glob.glob(os.path.join(d, 'validacao_K11_*.zip'))
    confere(len(zips) == 1, 'zip gerado')
    pastas = [x for x in glob.glob(os.path.join(d, 'validacao_K11_*')) if os.path.isdir(x)]
    comp = pd.read_csv(os.path.join(pastas[0], 'K11_A_comparacoes.csv'), sep=';', decimal=',')
    m1 = comp[(comp['metodo'].str.startswith('M1')) & (comp['var'] == 'tmax')].iloc[0]
    confere(m1['excede_fisico_metodo_pct'] <= m1['excede_fisico_M0_pct'] and m1['excede_fisico_M0_pct'] > 0,
            f"M1 reduz o que passa do limite físico nos prazos 8 e 13 ({m1['excede_fisico_M0_pct']:.3f}% -> {m1['excede_fisico_metodo_pct']:.3f}%)")
    met = pd.read_csv(os.path.join(pastas[0], 'K11_A_metricas.csv'), sep=';', decimal=',')
    a = met[(met['var'] == 'tmax') & (met['grupo'] == 'prazo 1')].set_index('metodo')['MAE']
    confere(abs(a[[i for i in a.index if i.startswith('M0')][0]] - a[[i for i in a.index if i.startswith('M1')][0]]) < 1e-12,
            'no prazo 1 o M1 é idêntico ao M0')
    if p.returncode != 0:
        print(saida[-3000:])
print('TODOS OS TESTES PASSARAM' if not falhas else f'{falhas} FALHA(S)')
sys.exit(1 if falhas else 0)
