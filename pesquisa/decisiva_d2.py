# Análise decisiva, D2 (pesquisa/PROTOCOLO_ANALISE_DECISIVA.md): as referências de chuva entre si, sem o BR-DWGD.
# Razão anual entre bases de famílias diferentes, por região; mudança de 2020–2024 contra 2010–2019. Valor do par de
# famílias = mediana dos pares de bases. Regra: família com ≥ 2 pares mudando > 5% (e os pares sem ela não) quebrou.
#     python pesquisa/decisiva_d2.py
import itertools
import os
import sys

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import auditoria_a1_a2 as A  # noqa: E402

SAIDA = os.path.join(AQUI, 'resultados_decisiva')
FAM = ['F1', 'F2', 'F3', 'F5']


def main():
    d = A.carregar()
    d = d[(d.variavel == 'pr_mm') & d.familia.isin(FAM)]
    g = d.groupby(['regiao', 'base', 'familia', 'ano']).agg(n=('mes', 'nunique'), ref=('referencia', 'sum')).reset_index()
    g = g[g.n == 12]
    linhas = []
    for reg, s in g.groupby('regiao'):
        bases = s[['base', 'familia']].drop_duplicates().values.tolist()
        for (b1, f1), (b2, f2) in itertools.combinations(bases, 2):
            if f1 == f2:
                continue
            x = s[s.base == b1].set_index('ano').ref / s[s.base == b2].set_index('ano').ref
            x = x.dropna()
            antes, depois = x.loc[2010:2019], x.loc[2020:2024]
            if len(antes) < 8 or len(depois) < 4:
                continue
            linhas.append({'regiao': reg, 'par': '/'.join(sorted([f1, f2])), 'bases': f'{b1}/{b2}' if f1 < f2 else f'{b2}/{b1}',
                           'mudanca': 100 * ((depois.mean() / antes.mean()) ** (1 if f1 < f2 else -1) - 1)})
    t = pd.DataFrame(linhas)
    os.makedirs(SAIDA, exist_ok=True)
    t.to_csv(os.path.join(SAIDA, 'D2_pares_bases.csv'), index=False)
    p = t.groupby(['regiao', 'par']).mudanca.median().unstack()
    L = ['# D2. As referências de chuva entre si (sem o BR-DWGD)', '',
         'Mudança da razão anual entre famílias, 2020–2024 contra 2010–2019 (%; mediana dos pares de bases). F1 = IMERG, '
         'PERSIANN, GLDAS-2.1 e NASA POWER (GPCC/GPCP); F2 = TerraClimate; F3 = CHIRPS; F5 = ERA5-Land. Regra: uma família '
         'com ≥ 2 pares mudando mais de 5% (e os pares sem ela, não) quebrou em 2020.', '',
         '| Região | ' + ' | '.join(p.columns) + ' | Família que quebrou |', '|---|' + '---|' * (len(p.columns) + 1)]
    quebras = {}
    for reg, r in p.iterrows():
        q = []
        for f in FAM:
            com = [c for c in p.columns if f in c.split('/') and pd.notna(r[c])]
            sem = [c for c in p.columns if f not in c.split('/') and pd.notna(r[c])]
            if sum(abs(r[c]) > 5 for c in com) >= 2 and not any(abs(r[c]) > 5 for c in sem):
                q.append(f)
        quebras[reg] = q
        L.append(f'| {reg} | ' + ' | '.join('-' if pd.isna(r[c]) else f'{r[c]:+.1f}' for c in p.columns) +
                 f' | {", ".join(q) or "nenhuma"} |')
    L.append('')
    with open(os.path.join(SAIDA, 'RESULTADOS_D2.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
