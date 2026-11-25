# Validação de 2026 (ERA5 calibrado) contra referências INDEPENDENTES do ERA5, enquanto não há estações de 2026
# disponíveis (o GSOD da NOAA vai até 2025 e o portal do INMET recusa acesso de fora do Brasil). Só LÊ o Earth Engine.
#   A. CHUVA: total mensal do SAB x CHIRPS (UCSB, satélite + estações; o IMERG mensal no Earth Engine para em set/2025), por região e pixel a
#      pixel (correlação espacial), nos meses de 2026 e, como régua, nos mesmos meses de 2024 (SAB = BR-DWGD, observado).
#   B. CALOR: anomalia da Tmax do SAB (mês de 2026 menos a média do mesmo mês em 2003-2024, BR-DWGD) x anomalia da
#      temperatura da superfície de dia do MODIS (MOD11A2, mesma conta). Se o calor de out/nov de 2026 for real, os dois
#      mostram o mesmo padrão; a régua é a mesma conta em 2024.
# Saída: pesquisa/resultados_2026/ (CSV e RESULTADOS.md).
#     python pesquisa/validar_2026_independente.py
import os
import sys
from datetime import date

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
sys.path.insert(0, AQUI)
import ee  # noqa: E402
import sab_pedido as sp  # noqa: E402
from hindcast import UF_REGIAO, sem_acento  # noqa: E402

ee.Initialize(project=sp.PROJETO)
SAIDA = os.path.join(AQUI, 'resultados_2026')
CRS, TRANSFORM = sp.CRS, sp.TRANSFORM
BRASIL = ee.Geometry.Rectangle([-74.0, -34.0, -34.0, 5.5], None, False)
CLASSE = ee.Image(sp.MASCARA).select('classe').unmask(0, False)
ENTREGUE = CLASSE.gte(1).And(CLASSE.lte(3))
CHIRPS = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD').select('precipitation')   # mm por pêntada
MODIS = ee.ImageCollection('MODIS/061/MOD11A2').select('LST_Day_1km')


def sab(ini, fim):
    def padronizar(img):
        return ee.Image(ee.Algorithms.If(img.bandNames().contains('precipitation_mm'),
                                         img.select(sp.BANDAS_ANTIGAS, sp.BANDAS_SAB), img.select(sp.BANDAS_SAB)))
    return ee.ImageCollection(sp.SAB).filterDate(ini, fim).map(padronizar)


def regioes():
    gaul = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
    nomes = gaul.aggregate_array('ADM1_NAME').getInfo()
    feats = []
    for reg in ('Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'):
        ufs = [n for n in nomes if UF_REGIAO.get(sem_acento(n)) == reg]
        feats.append(ee.Feature(gaul.filter(ee.Filter.inList('ADM1_NAME', ufs)).union(100).geometry(100), {'regiao': reg}))
    feats.append(ee.Feature(gaul.union(100).geometry(100), {'regiao': 'Brasil'}))
    return ee.FeatureCollection(feats)


def ultimo(col):
    return ee.Date(col.aggregate_max('system:time_start')).format('YYYY-MM-dd').getInfo()


def comparar(a, b, rotulo, regs):
    """Média regional dos dois campos e correlação espacial (pixels entregues, grade do SAB)."""
    par = ee.Image.cat([a.rename('sab'), b.rename('ref')]).updateMask(ENTREGUE)
    med = par.reduceRegions(collection=regs, reducer=ee.Reducer.mean(), crs=CRS, crsTransform=TRANSFORM,
                            tileScale=8).getInfo()
    cor = par.reduceRegion(ee.Reducer.pearsonsCorrelation(), BRASIL, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10,
                           tileScale=8).getInfo()
    linhas = [{'comparacao': rotulo, 'regiao': f['properties']['regiao'], 'sab': f['properties'].get('sab'),
               'referencia': f['properties'].get('ref')} for f in med['features']]
    for x in linhas:
        x['correlacao_espacial_brasil'] = cor.get('correlation')
    return linhas


def main():
    os.makedirs(SAIDA, exist_ok=True)
    regs = regioes()
    fim_imerg, fim_modis = ultimo(CHIRPS.filterDate('2026-01-01', '2027-01-01')), ultimo(MODIS.filterDate('2026-01-01', '2027-01-01'))
    inv = ee.ImageCollection(sp.SAB).filterDate('2026-01-01', '2027-01-01')
    vers = dict(zip(inv.aggregate_array('system:index').getInfo(), inv.aggregate_array('versao').getInfo()))
    ult_era5 = max(k for k, v in vers.items() if v == 'provisoria_era5')[4:].replace('_', '-')
    print(f'Última pêntada do CHIRPS: {fim_imerg} | último MODIS: {fim_modis} | último dia ERA5 do SAB: {ult_era5}', flush=True)
    linhas = []
    # A. chuva mensal: meses de 2026 com CHIRPS (a última pêntada começa no dia 26) e com o mês inteiro em ERA5 no SAB, e os mesmos meses de 2024
    meses = [m for m in range(1, 13) if f'2026-{m:02d}-26' <= fim_imerg and date(2026, m, 28) < date.fromisoformat(ult_era5)]
    for ano in (2026, 2024):
        for m in meses:
            ini = ee.Date.fromYMD(ano, m, 1)
            fim = ini.advance(1, 'month')
            s = sab(ini, fim).select('pr_mm').sum()
            r = CHIRPS.filterDate(ini, fim).sum()
            linhas += [dict(x, ano=ano, mes=m, variavel='chuva_mm_mes') for x in comparar(s, r, f'chuva {ano}-{m:02d}', regs)]
            print(f'   chuva {ano}-{m:02d} pronta', flush=True)
    # B. anomalia de calor: meses de 2026 com MODIS, contra 2003-2024; régua: os mesmos meses de 2024 contra 2003-2023
    meses_t = [m for m in (9, 10, 11) if f'2026-{m:02d}-20' <= fim_modis and f'2026-{m:02d}-15' <= ult_era5]
    for ano in (2026, 2024):
        for m in meses_t:
            ini = ee.Date.fromYMD(ano, m, 1)
            fim = ee.Date.fromYMD(ano, m, 15) if (ano == 2026 and m == 11) else ini.advance(1, 'month')
            base = (2003, ano - 1 if ano == 2024 else 2024)
            filtro = ee.Filter.calendarRange(m, m, 'month')
            clima_t = sab(f'{base[0]}-01-01', f'{base[1] + 1}-01-01').filter(filtro).select('tmax_C').mean()
            clima_l = MODIS.filterDate(f'{base[0]}-01-01', f'{base[1] + 1}-01-01').filter(filtro).mean()
            a_t = sab(ini, fim).select('tmax_C').mean().subtract(clima_t)
            a_l = MODIS.filterDate(ini, fim).mean().subtract(clima_l).multiply(0.02)
            linhas += [dict(x, ano=ano, mes=m, variavel='anomalia_tmax_x_lst_C')
                       for x in comparar(a_t, a_l, f'anomalia {ano}-{m:02d}', regs)]
            print(f'   anomalia {ano}-{m:02d} pronta', flush=True)
    df = pd.DataFrame(linhas)
    df.to_csv(os.path.join(SAIDA, 'validacao_2026_independente.csv'), index=False)
    resumo(df, fim_imerg, fim_modis, ult_era5)


def resumo(df, fim_imerg, fim_modis, ult_era5):
    L = ['# 2026 (ERA5 calibrado) contra referências independentes do ERA5', '',
         f'Gerado com: CHIRPS (pêntadas) até {fim_imerg}, MODIS até {fim_modis}, SAB ERA5 até {ult_era5}. A régua é 2024, '
         'quando o SAB é o BR-DWGD (observado): 2026 está bom se concordar com os satélites tanto quanto 2024 concorda.', '']
    c = df[df.variavel == 'chuva_mm_mes'].copy()
    if len(c):
        meses = sorted(c.mes.unique())
        L += ['## Chuva mensal: SAB x CHIRPS', '', f'Meses {meses[0]} a {meses[-1]}; viés do TOTAL do período (os meses '
              'secos não pesam mais que os chuvosos).', '',
              '| Ano | Região | Total SAB (mm) | Total CHIRPS (mm) | Viés do SAB (%) | Correlação espacial média (Brasil) |',
              '|---|---|---|---|---|---|']
        for (ano, reg), g in c.sort_values('ano', ascending=False).groupby(['ano', 'regiao'], sort=False):
            L.append(f'| {ano} | {reg} | {g.sab.sum():.0f} | {g.referencia.sum():.0f} | '
                     f'{100 * (g.sab.sum() / g.referencia.sum() - 1):+.1f} | {g.correlacao_espacial_brasil.mean():.2f} |')
        L.append('')
    t = df[df.variavel == 'anomalia_tmax_x_lst_C']
    if len(t):
        L += ['## Calor: anomalia da Tmax do SAB x anomalia da temperatura de superfície do MODIS', '',
              '| Mês | Região | Anomalia Tmax SAB (°C) | Anomalia LST MODIS (°C) | Correlação espacial (Brasil) |',
              '|---|---|---|---|---|']
        L.insert(len(L) - 3, 'Atenção: o Terra (MODIS) saiu da órbita fixa em 2022 e passa cada vez mais cedo, então a '
                 'temperatura de superfície dele esfria artificialmente ano a ano; o NÍVEL da anomalia do MODIS não '
                 'serve. O que vale é a CORRELAÇÃO ESPACIAL (o desenho do calor no mapa), comparada à de 2024.')
        L.insert(len(L) - 3, '')
        for r in t.sort_values(['ano', 'mes', 'regiao']).itertuples():
            L.append(f'| {r.ano}-{r.mes:02d} | {r.regiao} | {r.sab:+.2f} | {r.referencia:+.2f} | '
                     f'{r.correlacao_espacial_brasil:.2f} |')
    with open(os.path.join(SAIDA, 'RESULTADOS.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
