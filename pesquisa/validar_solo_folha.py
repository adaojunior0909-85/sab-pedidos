# Umidade do solo, temperatura da folha, temperatura do solo e evapotranspiração real do SAB contra satélites
# independentes, 2016–2021 (o SMAP começa em 04/2015; o Aqua/MODIS sai da órbita fixa em 2022). Só LÊ o Earth Engine.
#   umidade 0-5 cm (entregue)  x SMAP L3 enhanced (NASA/SMAP/SPL3SMP_E/006, soil_moisture_am)
#   temperatura da folha       x temperatura de superfície do Aqua/MODIS (MYD11A2, dia, 13h30)
#   temperatura do solo        x a mesma, à noite (MYD11A2, 01h30)
#   ET real                    x MODIS MOD16A2GF (evapotranspiração, soma de 8 dias)
# Média mensal (soma, na ET) por região; o que conta é a correlação das ANOMALIAS mensais (tirado o ciclo do ano),
# porque a correção de leitura da umidade usa o próprio SMAP na média do mês (o nível não é independente).
# REGRA FIXADA ANTES DE RODAR (25/11/2026), pela mediana das 5 regiões:
#   r >= 0,6 -> mantém como variável; 0,3 <= r < 0,6 -> mantém como ÍNDICE, com aviso no dicionário; r < 0,3 -> recomendo
#   retirar da entrega.
#     python pesquisa/validar_solo_folha.py
import os
import sys

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ee  # noqa: E402
import validar_2026_independente as v  # noqa: E402  (inicia o Earth Engine e traz as regiões)

sp = v.sp
SAIDA = os.path.join(AQUI, 'resultados_solo_folha')
SMAP = ee.ImageCollection('NASA/SMAP/SPL3SMP_E/006').select('soil_moisture_am')
LST = ee.ImageCollection('MODIS/061/MYD11A2')
ET16 = ee.ImageCollection('MODIS/061/MOD16A2GF').select('ET')
ANOS = range(2016, 2022)
PARES = {'umidade_0_5cm': 'SMAP', 'tfolha_C': 'LST dia', 'tsolo_C': 'LST noite', 'et_real': 'MOD16'}


def entregue(ini, fim, m):
    c = sp._correcao_mes(m)

    def corrigir(img):
        alg = ee.String(ee.Algorithms.If(img.propertyNames().contains('versao_algoritmo'), img.get('versao_algoritmo'), 'V1.0'))
        sm = img.select('soil_moisture_0_5cm_m3_m3')
        sm = ee.Image(ee.Algorithms.If(alg.equals('V1.0'), sm.multiply(c.select('c_ssur')).min(c.select('teto_ssur')), sm))
        return img.select(['tfolha_C', 'tsolo_C', 'et_real']).addBands(sm.rename('umidade_0_5cm'))
    return v.sab(ini, fim).map(corrigir)


def pilha(ano):
    b = []
    for m in range(1, 13):
        ini = ee.Date.fromYMD(ano, m, 1)
        fim = ini.advance(1, 'month')
        s = entregue(ini, fim, m)
        lst = LST.filterDate(ini, fim)
        b += [s.select('umidade_0_5cm').mean().rename(f'umidade_0_5cm_sab_{m:02d}'),
              SMAP.filterDate(ini, fim).mean().rename(f'umidade_0_5cm_ref_{m:02d}'),
              s.select('tfolha_C').mean().rename(f'tfolha_C_sab_{m:02d}'),
              lst.select('LST_Day_1km').mean().multiply(0.02).subtract(273.15).rename(f'tfolha_C_ref_{m:02d}'),
              s.select('tsolo_C').mean().rename(f'tsolo_C_sab_{m:02d}'),
              lst.select('LST_Night_1km').mean().multiply(0.02).subtract(273.15).rename(f'tsolo_C_ref_{m:02d}'),
              s.select('et_real').sum().rename(f'et_real_sab_{m:02d}'),
              ET16.filterDate(ini, fim).sum().multiply(0.1).rename(f'et_real_ref_{m:02d}')]
    return ee.Image.cat(b).toFloat().updateMask(v.ENTREGUE)


def main():
    os.makedirs(SAIDA, exist_ok=True)
    regs = v.regioes()
    linhas = []
    for ano in ANOS:
        r = pilha(ano).reduceRegions(collection=regs, reducer=ee.Reducer.mean(), crs=sp.CRS, crsTransform=sp.TRANSFORM,
                                     tileScale=16).getInfo()
        for f in r['features']:
            p = f['properties']
            for m in range(1, 13):
                for var in PARES:
                    linhas.append({'regiao': p['regiao'], 'ano': ano, 'mes': m, 'variavel': var,
                                   'sab': p.get(f'{var}_sab_{m:02d}'), 'referencia': p.get(f'{var}_ref_{m:02d}')})
        print(f'   {ano} pronto', flush=True)
    df = pd.DataFrame(linhas)
    df.to_csv(os.path.join(SAIDA, 'series_mensais.csv'), index=False)
    for k in ('sab', 'referencia'):
        df[f'anom_{k}'] = df[k] - df.groupby(['regiao', 'variavel', 'mes'])[k].transform('mean')
    L = ['# Solo, folha e ET real do SAB contra satélites independentes (2016–2021)', '',
         'Correlação das anomalias mensais (ciclo do ano retirado), por região. Regra fixada antes de rodar: mediana das '
         '5 regiões r ≥ 0,6 mantém; 0,3–0,6 mantém como índice com aviso; < 0,3 recomendo retirar.', '',
         '| Variável | Referência | ' + ' | '.join(['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil'])
         + ' | Mediana (5 regiões) | Viés médio (SAB − ref.) | Recomendação |', '|---' * 11 + '|']
    for var, ref in PARES.items():
        g = df[df.variavel == var].dropna(subset=['anom_sab', 'anom_referencia'])
        r = g.groupby('regiao').apply(lambda x: x.anom_sab.corr(x.anom_referencia))
        med = r.drop('Brasil', errors='ignore').median()
        rec = 'mantém' if med >= 0.6 else ('mantém como índice (aviso)' if med >= 0.3 else 'recomendo retirar')
        vies = (g.sab - g.referencia).mean()
        L.append(f'| {var} | {ref} | ' + ' | '.join(f'{r.get(x, float("nan")):.2f}' for x in
                                                    ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil'])
                 + f' | {med:.2f} | {vies:+.2f} | {rec} |')
    with open(os.path.join(SAIDA, 'RESULTADOS.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
