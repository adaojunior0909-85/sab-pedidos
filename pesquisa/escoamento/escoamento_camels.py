# Escoamento do SAB x vazão observada do CAMELS-BR (protocolo: ../PROTOCOLO_ESCOAMENTO_CAMELS.md). Só LÊ o Earth Engine.
# Para cada ano de 1981 a 2018 e cada uma das 512 bacias, a média na bacia (pixel pesado pela fração dentro dela) do
# total mensal de: M0 (escoamento total entregue: gravado x fator de leitura dos dias V1.0), M1 (gravado), M2 (ERA5-Land
# mensal puro), M3 (coeficiente do ERA5-Land x chuva do SAB) e P (chuva do SAB). Grava um CSV por ano em
# pesquisa/resultados_escoamento/anos/ (retoma de onde parou; TEMPO_MAX_MIN limita cada vez: sai com código 3 se
# faltarem anos). As métricas e a decisão do protocolo: escoamento_metricas.py.
#     python pesquisa/escoamento/escoamento_camels.py [ano_ini ano_fim]
import glob
import json
import os
import sys
import time

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
import ee  # noqa: E402
import sab_pedido as sp  # noqa: E402

DADOS = os.path.join(RAIZ, 'pesquisa', 'dados', 'camels')
SAIDA = os.path.join(RAIZ, 'pesquisa', 'resultados_escoamento')
ANOS = os.path.join(SAIDA, 'anos')
ee.Initialize(project=sp.PROJETO)
ERA5M = ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY_AGGR')


def padronizar(img):
    return ee.Image(ee.Algorithms.If(img.bandNames().contains('precipitation_mm'),
                                     img.select(sp.BANDAS_ANTIGAS, sp.BANDAS_SAB), img.select(sp.BANDAS_SAB)))


def bacias():
    g = json.load(open(os.path.join(DADOS, 'bacias.geojson')))
    return [ee.Feature(ee.Geometry(f['geometry']), {'id': f['properties']['id']}) for f in g['features']]


def pilha_do_ano(ano):
    bandas = []
    for m in range(1, 13):
        ini = ee.Date.fromYMD(ano, m, 1)
        fim = ini.advance(1, 'month')
        c = sp._correcao_mes(m)
        dia = ee.ImageCollection(sp.SAB).filterDate(ini, fim).map(padronizar)
        m1 = dia.map(lambda i: i.select('runoff_sup_mm').add(i.select('runoff_sub_mm'))).sum()
        m0 = dia.map(lambda i: ee.Image(ee.Algorithms.If(           # a correção de leitura só vale nos dias V1.0
            ee.String(ee.Algorithms.If(i.propertyNames().contains('versao_algoritmo'), i.get('versao_algoritmo'),
                                       'V1.0')).equals('V1.0'),
            i.select('runoff_sup_mm').multiply(c.select('c_rsup')).add(i.select('runoff_sub_mm').multiply(c.select('c_rsub'))),
            i.select('runoff_sup_mm').add(i.select('runoff_sub_mm'))))).sum()
        p = dia.select('pr_mm').sum()
        e = ee.Image(ERA5M.filterDate(ini, fim).first())
        ro = e.select('surface_runoff_sum').add(e.select('sub_surface_runoff_sum')).multiply(1000)
        tp = e.select('total_precipitation_sum').multiply(1000)
        m3 = ro.divide(tp.max(1)).clamp(0, 1).multiply(p)
        bandas += [m0.rename(f'M0_{m:02d}'), m1.rename(f'M1_{m:02d}'), ro.rename(f'M2_{m:02d}'),
                   m3.rename(f'M3_{m:02d}'), p.rename(f'P_{m:02d}')]
    return ee.Image.cat(bandas).toFloat()


def extrair(ano, feats, partes=1):
    """partes > 1 divide as bacias em pedidos menores (usado quando o pedido inteiro estoura)."""
    img = pilha_do_ano(ano)
    n = -(-len(feats) // partes)
    todas = []
    for i in range(0, len(feats), n):
        todas += img.reduceRegions(collection=ee.FeatureCollection(feats[i:i + n]), reducer=ee.Reducer.mean(),
                                   crs=sp.CRS, crsTransform=sp.TRANSFORM, tileScale=8).getInfo()['features']
    linhas = []
    for f in todas:
        pr = f['properties']
        for m in range(1, 13):
            linhas.append({'id': pr['id'], 'ano': ano, 'mes': m,
                           **{k: pr.get(f'{k}_{m:02d}') for k in ('M0', 'M1', 'M2', 'M3', 'P')}})
    return pd.DataFrame(linhas)


def main(a0=1981, a1=2018):
    os.makedirs(ANOS, exist_ok=True)
    fc = bacias()
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)
    for ano in range(a0, a1 + 1):
        arq = os.path.join(ANOS, f'{ano}.csv.gz')
        if os.path.exists(arq):
            continue
        if time.time() > limite:
            print('Tempo desta vez acabou; a próxima retoma daqui.')
            raise SystemExit(3)
        t0 = time.time()
        for tentativa in range(4):
            try:
                df = extrair(ano, fc, (1, 4, 16, 64)[tentativa])
                break
            except Exception as e:  # noqa: BLE001
                print(f'   ⚠️ {ano}: {str(e)[:150]} | nova tentativa em {30 * (tentativa + 1)} s, em pedidos menores', flush=True)
                time.sleep(30 * (tentativa + 1))
        else:
            raise RuntimeError(f'{ano}: não deu depois de 4 tentativas')
        df.round(3).to_csv(arq, index=False)
        print(f'   {ano}: {df.id.nunique()} bacias em {time.time() - t0:.0f} s', flush=True)
    print(f'Anos prontos: {len(glob.glob(os.path.join(ANOS, "*.csv.gz")))}')


if __name__ == '__main__':
    main(*map(int, sys.argv[1:3])) if len(sys.argv) >= 3 else main()
