# Monta a tabela final da K26 por década (1961-2026) a partir das pastas K26_rodada* de validacoes/resultados.
# Só lê os CSV das rodadas (pixels ENTREGUES: A, B, C_interior).   python3 -I montar_tabela_decadas.py
import os, sys, pandas as pd
P = os.path.dirname(os.path.abspath(__file__))          # a saída fica ao lado deste arquivo
R = os.path.dirname(P)                                  # validacoes/resultados
fontes = [('1961-1970', 5, 'v1.12', f'{R}/K26_rodada5_v1.12_2026-11-22'),
          ('1971-1980', 6, 'v1.12', f'{R}/K26_rodada6_v1.12_2026-11-22'),
          ('1981-1990', 7, 'v1.8', f'{R}/K26_rodada7_v1.8_2026-11-18'),
          ('1991-2000', 8, 'v1.9', f'{R}/K26_rodada8_v1.9_2026-11-18'),
          ('2001-2025', 12, 'v1.11', f'{R}/K26_rodada12_v1.11_2026-11-19'),
          ('2026', 1, 'v1.12', f'{R}/K26_rodada1_v1.12_2026-11-22')]
ENT = ['A', 'B', 'C_interior']
cols = ['runoff_sup_gt_pr', 'runoff_sup_gt_pr_10', 'runoff_sup_gt_pr_50', 'runoff_sup_gt_200', 'rs_gt_rso_motor',
        'rs_gt_rso_audit', 'rs_zero', 'eto_zero_com_rs', 'rs_lt_003ra', 'rs_ge_ra', 'etr_gt_eto', 'transp_gt_etr',
        'tmax_lt_tmin', 'rh_fora', 'solo_gt_max', 'negativo', 'vpd_incoerente', 'pr_ge_450', 'u2_fora', 't_fora']
linhas, extremos, h = [], [], []
for per, rod, ver, d in fontes:
    c = pd.read_csv(f'{d}/K26_CD_por_classe.csv', sep=';', decimal=',')
    e = c[c.nome_classe.isin(ENT)]
    n = e.n_pix.sum()
    l = {'periodo': per, 'rodada': rod, 'versao': ver, 'pixel_dias': int(n)}
    for k in cols:
        v = int(e[k].sum()) if k in e else None
        l[k] = v
    for k in ('rs_zero', 'eto_zero_com_rs', 'rs_gt_rso_motor'):
        for cl in ENT:
            r = c[c.nome_classe == cl]
            l[f'{k}__{cl}'] = int(r[k].sum()) if k in c and len(r) else 0
    linhas.append(l)
    x = pd.read_csv(f'{d}/K26_B_extremos_fora_da_faixa.csv', sep=';', decimal=',')
    x = x[x.nome_classe.isin(ENT)]
    for var in x.variavel.unique():
        y = x[x.variavel == var].sort_values('maximo_absoluto').iloc[-1]
        extremos.append({'periodo': per, 'variavel': var, 'max': y.maximo_absoluto, 'classe': y.nome_classe,
                         'mes': y.mes, 'meses_classe_fora': int((x.variavel == var).sum())})
    r = pd.read_csv(f'{d}/K26_RESUMO.csv', sep=';', decimal=',')
    h.append({'periodo': per, **{row.item: row.status for row in r.itertuples()}})
T = pd.DataFrame(linhas)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 80)
print(T[['periodo', 'versao', 'pixel_dias']].to_string(index=False))
pct = T[['periodo']].copy()
for k in ('runoff_sup_gt_pr', 'runoff_sup_gt_pr_10', 'runoff_sup_gt_pr_50', 'runoff_sup_gt_200', 'rs_gt_rso_motor', 'rs_zero'):
    pct[k + '_%'] = (100 * T[k] / T.pixel_dias).round(5)
print(pct.to_string(index=False))
print(T[['periodo'] + [c for c in T if '__' in c]].to_string(index=False))
nz = [k for k in cols if T[k].fillna(0).sum() > 0]
print('com algo:', nz)
print('sempre zero:', [k for k in cols if k not in nz])
print(T[['periodo'] + nz].to_string(index=False))
print(pd.DataFrame(extremos).to_string(index=False))
print(pd.DataFrame(h).to_string(index=False))
T.to_csv(os.path.join(P, 'K26_tabela_decadas.csv'), sep=';', decimal=',', index=False)
pd.DataFrame(extremos).to_csv(os.path.join(P, 'K26_extremos_decadas.csv'), sep=';', decimal=',', index=False)
