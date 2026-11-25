# TODAS as métricas de TODAS as comparações com referências de fora, região por região e mês a mês, num arquivo só,
# para replicação e auditoria. Não fala com o Earth Engine: lê os CSV brutos que cada validação gravou (os valores
# mensais por região, ou por bacia no escoamento) e escreve:
#   pesquisa/METRICAS_COMPLETAS.csv.gz   uma linha por comparação x referência x variável x região x período x mês
#   pesquisa/DADOS_PAREADOS.csv.gz       os pares (SAB, referência) de que saíram as métricas, no mesmo formato
# Os métodos (fontes, agregação, unidades, fórmulas e regras) estão em pesquisa/METODOS_REPLICACAO.md.
#     python pesquisa/metricas_completas.py
import glob
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SOMAS = {'pr_mm', 'pr_chirps', 'chuva_mm_mes', 'et_potencial', 'et_real', 'transpiracao_mm', 'runoff_sup_mm',
         'runoff_sub_mm', 'escoamento', 'escoamento_total'}
REF_SOLO = {'umidade_0_5cm': 'SMAP L3 enhanced (NASA/SMAP/SPL3SMP_E/006)', 'tfolha_C': 'MODIS Aqua LST dia (MYD11A2)',
            'tsolo_C': 'MODIS Aqua LST noite (MYD11A2)', 'et_real': 'MODIS MOD16A2GF'}


def ler(padrao):
    arqs = sorted(glob.glob(os.path.join(AQUI, padrao)))
    return pd.concat(pd.read_csv(a, dtype={'id': str}) for a in arqs) if arqs else None


def pares():
    """Todos os pares mensais num formato só: comparacao, referencia, variavel, regiao, ano, mes, sab, ref."""
    P = []
    d = ler('resultados_2026/validacao_2026_independente.csv')
    if d is not None:
        d = d.rename(columns={'referencia': 'ref'})
        d['referencia'] = np.where(d.variavel == 'chuva_mm_mes', 'CHIRPS pentadas (UCSB-CHG/CHIRPS/PENTAD)',
                                   'MODIS Terra LST dia, anomalia (MOD11A2)')
        P.append(d.assign(comparacao='2026_e_regua_2024_x_satelite'))
    d = ler('resultados_solo_folha/series_mensais.csv')
    if d is not None:
        P.append(d.rename(columns={'referencia': 'ref'}).assign(comparacao='solo_folha_et_x_satelite_2016_2021',
                                                                 referencia=lambda x: x.variavel.map(REF_SOLO)))
    d = ler('resultados_metodo_2026/parte_a/*.csv')
    if d is not None:
        P.append(d.rename(columns={'metodo_2026': 'sab', 'entregue': 'ref'}).assign(
            comparacao='metodo_2026_aplicado_2021_2025', referencia='SAB entregue (BR-DWGD nas 8 variáveis do núcleo)'))
    d = ler('resultados_metodo_2026/parte_b_gldas.csv')
    if d is not None:
        P.append(d.rename(columns={'gldas': 'ref'}).assign(comparacao='2026_e_regua_2022_2024_x_gldas',
                                                           referencia='GLDAS-2.1 Noah 3h (NASA/GLDAS/V021/NOAH/G025/T3H)'))
    d = ler('resultados_historico/anos/*.csv')
    if d is not None:
        d = d.rename(columns={'referencia': 'ref'})
        d['referencia'] = np.where(d.variavel == 'pr_chirps', 'CHIRPS pentadas', 'TerraClimate (IDAHO_EPSCOR/TERRACLIMATE)')
        P.append(d.assign(comparacao='historico_1961_2025'))
    s = ler('resultados_escoamento/anos/*.csv.gz')
    q = ler('dados/camels/vazao_mensal.csv.gz')
    b = ler('dados/camels/bacias.csv')
    if s is not None and q is not None:
        reg = dict(zip(b.gauge_id.astype(str), b.gauge_region))
        e = q.merge(s, on=['id', 'ano', 'mes'])
        for m, nome in (('M0', 'entregue'), ('M1', 'gravado'), ('M2', 'era5land_puro'), ('M3', 'coef_era5_x_chuva_sab')):
            x = e[['id', 'ano', 'mes', m, 'q_obs_mm']].rename(columns={m: 'sab', 'q_obs_mm': 'ref'})
            x['regiao'] = x.id.map(reg)
            P.append(x.assign(comparacao=f'escoamento_{nome}_x_camels_br_1981_2018', variavel='escoamento_total',
                              referencia='vazão observada CAMELS-BR v1.1 (ANA), mm/mês'))
    if not P:
        return pd.DataFrame()
    df = pd.concat(P, ignore_index=True)
    cols = ['comparacao', 'referencia', 'variavel', 'regiao', 'ano', 'mes', 'sab', 'ref'] + (['id'] if 'id' in df else [])
    return df[cols].dropna(subset=['sab', 'ref'])


def metricas(g, var):
    s, o = g.sab.to_numpy(float), g.ref.to_numpy(float)
    n = len(s)
    x = {'n': n, 'media_sab': s.mean(), 'media_ref': o.mean(), 'vies': (s - o).mean(),
         'vies_pct': 100 * (s.sum() / o.sum() - 1) if o.sum() else np.nan,
         'mae': np.abs(s - o).mean(), 'rmse': np.sqrt(((s - o) ** 2).mean()),
         'desvio_sab': s.std(ddof=1) if n > 1 else np.nan, 'desvio_ref': o.std(ddof=1) if n > 1 else np.nan}
    ok = n >= 3 and s.std() > 0 and o.std() > 0
    x['r'] = np.corrcoef(s, o)[0, 1] if ok else np.nan
    if ok and o.mean() != 0:
        x['kge'] = 1 - np.sqrt((x['r'] - 1) ** 2 + (s.std() / o.std() - 1) ** 2 + (s.mean() / o.mean() - 1) ** 2)
    else:
        x['kge'] = np.nan
    x['nse'] = 1 - ((s - o) ** 2).sum() / ((o - o.mean()) ** 2).sum() if ok else np.nan
    if 'anom_sab' in g and n >= 3:
        a, b = g.anom_sab.to_numpy(float), g.anom_ref.to_numpy(float)
        x['r_anomalias'] = np.corrcoef(a, b)[0, 1] if a.std() > 0 and b.std() > 0 else np.nan
    x['soma'] = var in SOMAS
    return x


def periodos(anos):
    """'todos', cada ano e, em séries longas, cada década."""
    p = {'todos': anos}
    for a in anos:
        p[str(a)] = [a]
    if max(anos) - min(anos) >= 15:
        for d in range(min(anos) // 10 * 10, max(anos) + 1, 10):
            ds = [a for a in anos if d <= a < d + 10]
            if ds:
                p[f'{max(d, min(anos))}-{min(d + 9, max(anos))}'] = ds
    return p


def main():
    df = pares()
    if df.empty:
        print('Nenhum CSV de validação encontrado.')
        return
    # bacias: além de cada região hidrográfica, o Brasil (todas as bacias juntas)
    esc = df[df.comparacao.str.startswith('escoamento')]
    df = pd.concat([df, esc.assign(regiao='Brasil')], ignore_index=True) if len(esc) else df
    df['id'] = df['id'].fillna('') if 'id' in df else ''      # '' = valor de região (o id é a bacia no escoamento)
    chave = ['comparacao', 'referencia', 'variavel', 'regiao', 'id']
    df['anom_sab'] = df.sab - df.groupby(chave + ['mes']).sab.transform('mean')
    df['anom_ref'] = df.ref - df.groupby(chave + ['mes']).ref.transform('mean')
    # os pares do escoamento (por bacia) já estão em resultados_escoamento/anos/ + dados/camels/vazao_mensal.csv.gz
    (df[~df.comparacao.str.startswith('escoamento')].drop(columns=['anom_sab', 'anom_ref', 'id']).round(4)
     .to_csv(os.path.join(AQUI, 'DADOS_PAREADOS.csv.gz'), index=False))
    L = []
    for (comp, ref, var, reg), g in df.groupby(['comparacao', 'referencia', 'variavel', 'regiao']):
        anos = sorted(g.ano.unique().astype(int))
        for nome_p, anos_p in periodos(anos).items():
            gp = g[g.ano.isin(anos_p)]
            for mes in ['todos'] + list(range(1, 13)):
                gm = gp if mes == 'todos' else gp[gp.mes == mes]
                if len(gm) < 2:                      # um valor só: está nos DADOS_PAREADOS
                    continue
                L.append({'comparacao': comp, 'referencia': ref, 'variavel': var, 'regiao': reg, 'periodo': nome_p,
                          'mes': mes, **metricas(gm, var)})
    out = pd.DataFrame(L)
    out.round(4).to_csv(os.path.join(AQUI, 'METRICAS_COMPLETAS.csv.gz'), index=False)
    print(f'{len(df):,} pares; {len(out):,} linhas de métricas; comparações: {sorted(out.comparacao.unique())}')


if __name__ == '__main__':
    sys.exit(main())
