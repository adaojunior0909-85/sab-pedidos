# Teste do teste: gera dados ARTIFICIAIS no formato do extrator, com sinais conhecidos, roda o hindcast e confere se
# ele acha o sinal onde ele existe e NÃO inventa acerto onde só há ruído. Não usa Earth Engine.
#     python pesquisa/teste_sintetico.py
# Sinais plantados (só nos dados artificiais):
#   - Tmax no Sul, de setembro a dezembro: +0,8 °C por °C do Niño 3.4 relativo (o Niño persiste de um mês a outro);
#   - chuva no Sul, de setembro a dezembro: x exp(0,35 x Niño 3.4 relativo);
#   - Tmin em todo o Brasil: tendência de +0,3 °C por década, sem ENSO;
#   - Nordeste e Norte: só ruído (sem tendência e sem ENSO) em chuva e Tmax.
import csv
import gzip
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import hindcast as hc  # noqa: E402

rng = np.random.default_rng(int(os.environ.get("SEMENTE", "7")))
ANOS = np.arange(1981, 2026)
n_m = len(ANOS) * 12 + 12


def ar1(n, phi, sd):
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + rng.normal(0, sd)
    return x


def gerar(pasta):
    os.makedirs(os.path.join(pasta, 'brdwgd'), exist_ok=True)
    nino = ar1(n_m, 0.92, 0.35)
    trop = ar1(n_m, 0.9, 0.05)
    sst = pd.DataFrame({'ano': 1981 + np.arange(n_m) // 12, 'mes': np.arange(n_m) % 12 + 1})
    sst = sst[(sst.ano >= 1982) & (sst.ano <= 2025)]
    mi = ((sst.ano - 1981) * 12 + sst.mes - 1).to_numpy()
    sst['n_dias'] = [(pd.Timestamp(a, m, 1) + pd.offsets.MonthEnd(0)).day for a, m in zip(sst.ano, sst.mes)]
    sst['nino34'] = 27 + nino[mi] + trop[mi]
    sst['tropical'] = 26 + trop[mi]
    for c in ('nino12', 'tna', 'tsa', 'atsw', 'iod_w', 'iod_e'):
        sst[c] = 25 + ar1(n_m, 0.8, 0.3)[mi]
    sst.to_csv(os.path.join(pasta, 'sst_mensal.csv'), index=False)
    rel = nino                                              # Niño 3.4 relativo verdadeiro (mensal)
    ufs = ['Paraná'] * 12 + ['Rio Grande do Sul'] * 6 + ['Bahia'] * 8 + ['Ceará'] * 6 + ['Amazonas'] * 6 + \
          ['Goiás'] * 6 + ['São Paulo'] * 6
    pts = [{'id': f'P{i + 1:04d}', 'lat': '-25.0', 'lon': '-53.0', 'uf': u,
            'grupo': 'Cascavel' if i == 0 else 'BR_1grau'} for i, u in enumerate(ufs)]
    with open(os.path.join(pasta, 'pontos.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(pts[0]))
        w.writeheader()
        w.writerows(pts)
    for ano in ANOS:
        linhas = []
        for p in pts:
            sul = p['uf'] in ('Paraná', 'Rio Grande do Sul')
            l = {'id': p['id'], 'ano': ano}
            for q in range(24):
                m = q // 2 + 1
                r = rel[(ano - 1981) * 12 + m - 1]
                prim = sul and m in (9, 10, 11, 12)
                tx = 28 + 3 * np.cos(2 * np.pi * (m - 1) / 12) + (0.8 * r if prim else 0) + rng.normal(0, 0.8)
                tn = 16 + 3 * np.cos(2 * np.pi * (m - 1) / 12) + 0.03 * (ano - 2000) + rng.normal(0, 0.8)
                pr = rng.gamma(2.0, 30.0) * (np.exp(0.35 * r) if prim else 1.0)
                l.update({f'pr_{q:02d}': f'{pr:.2f}', f'tx_{q:02d}': f'{tx:.2f}', f'tn_{q:02d}': f'{tn:.2f}',
                          f'n_{q:02d}': hc.dias_quinzena(ano, q)})
            linhas.append(l)
        with gzip.open(os.path.join(pasta, 'brdwgd', f'{ano}.csv.gz'), 'wt', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0]))
            w.writeheader()
            w.writerows(linhas)


if __name__ == '__main__':
    pasta = tempfile.mkdtemp(prefix='sab_sintetico_')
    gerar(pasta)
    saida = os.path.join(pasta, 'resultados')
    subprocess.run([sys.executable, os.path.join(AQUI, 'hindcast.py'), '--dados', pasta, '--saida', saida], check=True)
    esc = pd.read_csv(os.path.join(saida, 'metodo_escolhido_por_celula.csv'))
    falhas = 0

    def confere(cond, msg):
        global falhas
        print(('  ok   ' if cond else '  FALHA ') + msg)
        falhas += 0 if cond else 1

    def produto(v, alvo, est, reg):
        r = esc[(esc.variavel == v) & (esc.alvo == alvo) & (esc.estacao == est) & (esc.regiao == reg)]
        return r.iloc[0] if len(r) else None
    sem = 'sem sinal: média histórica'
    r = produto('tx', 'Q1', 'SON', 'Sul')
    confere(r is not None and r['produto'] != sem and r['MSESS'] > 0 and r['metodo'].split('_')[0].rstrip('t') in ('E1', 'E2', 'R1', 'R2', 'ENS'), f"Tmax Sul primavera (sinal ENSO): {r['metodo']} MSESS {r['MSESS']:+.2f} -> {r['produto']}")
    r = produto('pr', 'Q1', 'SON', 'Sul')
    confere(r is not None and r['MSESS'] > 0, f"Chuva Sul primavera (sinal ENSO): {r['metodo']} MSESS {r['MSESS']:+.2f} -> {r['produto']}")
    r = produto('tn', 'M2', 'JJA', 'Nordeste')
    confere(r is not None and r['produto'] != sem, f"Tmin Nordeste (só tendência): {r['metodo']} MSESS {r['MSESS']:+.2f} -> {r['produto']}")
    ruido = esc[esc.regiao.isin(['Nordeste', 'Norte']) & esc.variavel.isin(['pr', 'tx'])]
    falsos = (ruido['produto'] != sem).sum()
    confere(falsos <= 0.1 * len(ruido), f'Só ruído (Norte/Nordeste, chuva e Tmax): {falsos} de {len(ruido)} células aprovadas por engano (aceito até 10%)')
    print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TESTE SINTÉTICO OK') + f' | dados e resultados em {pasta}')
    sys.exit(1 if falhas else 0)
