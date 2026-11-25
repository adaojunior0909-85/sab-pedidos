# Métricas e decisão do protocolo (../PROTOCOLO_ESCOAMENTO_CAMELS.md) a partir de pesquisa/resultados_escoamento/anos/
# e da vazão do CAMELS-BR. Não fala com o Earth Engine. Saída: pesquisa/resultados_escoamento/ (metricas_bacias.csv,
# RESULTADOS.md).
#     python pesquisa/escoamento/escoamento_metricas.py
import glob
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
DADOS = os.path.join(RAIZ, 'pesquisa', 'dados', 'camels')
SAIDA = os.path.join(RAIZ, 'pesquisa', 'resultados_escoamento')
METODOS = ('M0', 'M1', 'M2', 'M3')
NOMES = {'M0': 'M0 atual (entregue)', 'M1': 'M1 gravado', 'M2': 'M2 ERA5-Land puro', 'M3': 'M3 coef. ERA5 × chuva SAB'}
MIN_MESES = 24
METADES = {'1981-1999': (1981, 1999), '2000-2018': (2000, 2018)}


def kge(s, o):
    if len(o) < MIN_MESES or o.std() == 0 or s.std() == 0 or o.mean() <= 0:
        return np.nan, np.nan, np.nan
    r = np.corrcoef(s, o)[0, 1]
    beta, alfa = s.mean() / o.mean(), s.std() / o.std()
    return 1 - np.sqrt((r - 1) ** 2 + (alfa - 1) ** 2 + (beta - 1) ** 2), 100 * (beta - 1), r


def metricas(d):
    linhas = []
    for (gid, per), g in d.groupby(['id', 'periodo']):
        x = {'id': gid, 'periodo': per, 'meses': len(g)}
        for m in METODOS:
            x[f'kge_{m}'], x[f'vies_{m}'], x[f'r_{m}'] = kge(g[m].values, g.q_obs_mm.values)
        linhas.append(x)
    return pd.DataFrame(linhas)


def main():
    arqs = sorted(glob.glob(os.path.join(SAIDA, 'anos', '*.csv.gz')))
    if len(arqs) < 38:
        print(f'Só {len(arqs)} de 38 anos prontos; rode antes o escoamento_camels.py.')
        raise SystemExit(1)
    s = pd.concat(pd.read_csv(a, dtype={'id': str}) for a in arqs)
    q = pd.read_csv(os.path.join(DADOS, 'vazao_mensal.csv.gz'), dtype={'id': str})
    b = pd.read_csv(os.path.join(DADOS, 'bacias.csv'), dtype={'gauge_id': str})
    regiao = dict(zip(b.gauge_id, b.gauge_region))
    d = q.merge(s, on=['id', 'ano', 'mes']).dropna(subset=list(METODOS))
    tudo = d.assign(periodo='1981-2018')
    partes = [tudo] + [d[d.ano.between(a, z)].assign(periodo=k) for k, (a, z) in METADES.items()]
    mt = metricas(pd.concat(partes))
    mt['regiao'] = mt.id.map(regiao)
    mt.round(4).to_csv(os.path.join(SAIDA, 'metricas_bacias.csv'), index=False)

    def teste(per, m):
        g = mt[mt.periodo == per].dropna(subset=['kge_M0', f'kge_{m}'])
        ganho = g[f'kge_{m}'].median() - g.kge_M0.median()
        frac = (g[f'kge_{m}'] > g.kge_M0).mean()
        return ganho, frac, len(g)

    L = ['# Escoamento do SAB contra a vazão observada (CAMELS-BR), 1981–2018', '',
         'Protocolo fixado antes de rodar: `pesquisa/PROTOCOLO_ESCOAMENTO_CAMELS.md`. Total mensal na bacia; '
         f'bacias com pelo menos {MIN_MESES} meses válidos. Fonte da vazão: CAMELS-BR v1.1 (Chagas et al., 2020, '
         'doi:10.5281/zenodo.3964745, CC-BY-4.0).', '', '## Brasil (mediana entre as bacias)', '',
         '| Método | Período | Bacias | KGE | Viés (%) | |Viés| (%) | r |', '|---|---|---|---|---|---|---|']
    for per in ['1981-2018', *METADES]:
        g = mt[mt.periodo == per]
        for m in METODOS:
            L.append(f'| {NOMES[m]} | {per} | {g[f"kge_{m}"].notna().sum()} | {g[f"kge_{m}"].median():.2f} | '
                     f'{g[f"vies_{m}"].median():+.0f} | {g[f"vies_{m}"].abs().median():.0f} | {g[f"r_{m}"].median():.2f} |')
    L += ['', '## Por região hidrográfica (1981–2018, mediana)', '',
          '| Região | Bacias | KGE M0 | Viés M0 (%) | KGE M1 | KGE M2 | KGE M3 | Viés M3 (%) |', '|---|---|---|---|---|---|---|---|']
    for reg, g in mt[mt.periodo == '1981-2018'].groupby('regiao'):
        L.append(f'| {reg} | {len(g)} | {g.kge_M0.median():.2f} | {g.vies_M0.median():+.0f} | {g.kge_M1.median():.2f} | '
                 f'{g.kge_M2.median():.2f} | {g.kge_M3.median():.2f} | {g.vies_M3.median():+.0f} |')
    L += ['', '## Regra de decisão (as quatro condições)', '',
          '| Candidato | 1. KGE +0,10 (todo) | 2. melhora em ≥ 60% | 3. vale nas duas metades | 4. |viés| não piora | Passa? |',
          '|---|---|---|---|---|---|']
    aprovados = []
    vies0 = mt[mt.periodo == '1981-2018'].vies_M0.abs().median()
    for m in ('M1', 'M2', 'M3'):
        ganho, frac, _ = teste('1981-2018', m)
        c1, c2 = ganho >= 0.10, frac >= 0.60
        c3 = all(teste(p, m)[0] >= 0.10 and teste(p, m)[1] >= 0.60 for p in METADES)
        c4 = mt[mt.periodo == '1981-2018'][f'vies_{m}'].abs().median() <= vies0
        ok = c1 and c2 and c3 and c4
        if ok:
            aprovados.append((mt[mt.periodo == '1981-2018'][f'kge_{m}'].median(), m))
        L.append(f'| {NOMES[m]} | {"✅" if c1 else "❌"} ({ganho:+.2f}) | {"✅" if c2 else "❌"} ({100 * frac:.0f}%) | '
                 f'{"✅" if c3 else "❌"} | {"✅" if c4 else "❌"} | {"**sim**" if ok else "não"} |')
    L += ['', '## Decisão', '']
    if aprovados:
        m = max(aprovados)[1]
        L.append(f'**{NOMES[m]}** passou nas quatro condições: vira a base do escoamento de um `SAB_V2`, montado em '
                 'paralelo e auditado antes. O banco atual não muda.')
    else:
        L.append('Nenhum candidato passou nas quatro condições: **o M0 fica**. O dicionário ganha o aviso quantitativo '
                 '(KGE e viés do M0 por região, tabela acima).')
    with open(os.path.join(SAIDA, 'RESULTADOS.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    sys.exit(main())
