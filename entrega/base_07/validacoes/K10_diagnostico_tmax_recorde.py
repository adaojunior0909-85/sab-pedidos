# >>> DIAGNÓSTICO K10 (22/10/2026): Tmax da previsão acima do recorde do INMET. SÓ LEITURA. Cole inteiro, sem editar. <<<
# =========================================================================================
# POR QUE EXISTE
#   A auditoria 08 de 22/10/2026 (J5a) achou um dia de previsão GFS com Tmax máxima nacional acima do
#   recorde do INMET (44,8 °C): 2026-10-26, 45,24 °C (rodada 2026-10-21 00Z, prazo L6). Para decidir o
#   que fazer, é preciso saber ONDE é o pixel e POR QUÊ:
#     (a) o GFS bruto já passa do recorde ali (viés do modelo), ou
#     (b) o GFS bruto está abaixo e a calibração (escala de variância) empurrou para cima, ou
#     (c) é um pixel de borda/fora do Brasil que só entra pela máscara fracionária da auditoria.
#
# O QUE FAZ (nada é criado, apagado ou exportado; não trava a sessão)
#   1. Tmax máxima de cada dia GFS do SAB_V1 em 2026, dentro do Brasil (mesma máscara da J5).
#   2. Para cada dia com máximo acima de LIMIAR_ANALISE: o pixel do máximo (lat/lon, estado, município,
#      classe da máscara de qualidade, fração do pixel dentro do Brasil) e quantos pixels passam do
#      recorde.
#   3. No pixel: Tmax gravada, Tmax do GFS bruto da mesma rodada (refeita como no motor), médias e
#      desvios da matriz V2.1 da faixa do prazo, razão dos desvios, a Tmax recalculada pela escala de
#      variância (tem de bater com a gravada, a menos do ajuste de amplitude mínima) e a parte do
#      aquecimento que vem do modelo e a que vem da calibração.
#   4. No pixel: maior Tmax do histórico do SAB (1961-2025, BR-DWGD) e maior Tmax dos dias ERA5 de 2026.
#   5. Diagnóstico em uma linha por dia: (a), (b) ou (c).
# =========================================================================================
import math
from datetime import datetime, timedelta, timezone

import ee
import pandas as pd

PROJETO = 'clima-492922'
SAB = f'projects/{PROJETO}/assets/SAB_V1'
MATRIZ = f'projects/{PROJETO}/assets/SICSB_MATRIZ_GFS_V2'
MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
COL_GFS = 'NOAA/GFS0P25'
RECORDE = 44.8              # recorde do INMET (Araçuaí-MG, 19/11/2023)
LIMIAR_ANALISE = 44.0       # analisa os dias GFS cujo máximo nacional passa deste valor
RAZAO_MIN, RAZAO_MAX = 0.5, 2.0   # mesmos limites do motor V1.5 (RAZAO_DESVIO_MIN/MAX)
RAZAO_MAX_LONGO = 1.0             # [K11] teto da Tmax/Tmin nos prazos de 6 dias em diante (RAZAO_DESVIO_MAX_LONGO)
AMPLITUDE_MIN_C = 1.0
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
MS_DIA = 86400000

print(f"🔎 K10: Tmax da previsão acima do recorde | {datetime.now(timezone(timedelta(hours=-3))):%Y-%m-%d %H:%M} (BRT)")
try:
    ee.Initialize(project=PROJETO)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJETO)

GAUL_BR = ee.FeatureCollection('FAO/GAUL/2015/level0').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
GAUL2 = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
LIMITES = GAUL_BR.geometry().bounds()
FRACAO_BR = ee.Image.constant(1).clipToCollection(GAUL_BR).mask()   # fração do pixel dentro do Brasil (como a J5)


def gi(obj):
    return obj.getInfo()


def expandir_borda(img):
    return img.unmask(img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMean(1, 'square', 'pixels'))


def prazo_L(dia_ms, creation_ms):
    return math.ceil(((dia_ms + MS_DIA - creation_ms) / 3600000.0) / 24.0 - 1e-9)


def faixa(L):
    return 'L1' if L <= 1 else ('L2a5' if L <= 5 else ('L6a10' if L <= 10 else 'L11a15'))


def tmax_bruta_gfs(dia_ms, creation_ms):
    """Como o motor: saídas da rodada na janela (00Z, 24Z] do dia, uma por hora, bilinear, máximo da T2m."""
    col = (ee.ImageCollection(COL_GFS).filterDate(creation_ms, creation_ms + 3600 * 1000)
           .filter(ee.Filter.eq('creation_time', creation_ms))
           .filter(ee.Filter.gt('forecast_time', dia_ms)).filter(ee.Filter.lte('forecast_time', dia_ms + MS_DIA))
           .filter(ee.Filter.gt('forecast_hours', 0)))
    col = ee.ImageCollection(col.distinct('forecast_hours')).map(lambda i: i.resample('bilinear'))
    return col.select('temperature_2m_above_ground').max().rename('tmax_bruta'), col.size()


# 1. Máximo nacional de cada dia GFS de 2026
gfs = ee.ImageCollection(SAB).filterDate('2026-01-01', '2027-01-01').filter(ee.Filter.eq('versao', 'provisoria_gfs'))


def resumo_dia(img):
    s = img.select('tmax_C').updateMask(FRACAO_BR)
    r = ee.Image.cat([s, s.gt(RECORDE).rename('acima')]).reduceRegion(
        reducer=ee.Reducer.max().combine(ee.Reducer.sum().unweighted(), sharedInputs=True),
        geometry=LIMITES, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4)
    return ee.Feature(None, r).set({'t': img.get('system:time_start'), 'rodada': img.get('rodada_gfs_ms'),
                                    'conf': img.get('Confianca_Prazo')})


feats = gi(ee.FeatureCollection(gfs.map(resumo_dia)))['features']
dias = pd.DataFrame([f['properties'] for f in feats])
dias['dia'] = pd.to_datetime(dias['t'].astype('float64'), unit='ms', utc=True).dt.strftime('%Y-%m-%d')
dias = dias.sort_values('dia')
dias['L'] = [prazo_L(int(t), int(r)) for t, r in zip(dias['t'], dias['rodada'])]
print("\n=== 1. Tmax máxima nacional dos dias de previsão (dentro do Brasil, como a J5) ===")
print(dias[['dia', 'L', 'conf', 'tmax_C_max', 'acima_sum']].rename(
    columns={'tmax_C_max': 'Tmax_max', 'acima_sum': f'pixels_>{RECORDE}'}).round(2).to_string(index=False))

alvo = dias[dias['tmax_C_max'] > LIMIAR_ANALISE]
if alvo.empty:
    print(f"\n✅ Nenhum dia de previsão com Tmax máxima acima de {LIMIAR_ANALISE} °C nesta rodada. Nada a diagnosticar.")
else:
    hist = ee.ImageCollection(SAB).filterDate('1961-01-01', '2026-01-01').select('tmax_C')
    era5_26 = (ee.ImageCollection(SAB).filterDate('2026-01-01', '2027-01-01')
               .filter(ee.Filter.eq('versao', 'provisoria_era5')).select('tmax_C'))
    linhas = []
    for _, d in alvo.iterrows():
        t, rod = int(d['t']), int(d['rodada'])
        L = prazo_L(t, rod)
        fx = faixa(L)
        mes = d['dia'][5:7]
        img = gfs.filter(ee.Filter.eq('system:time_start', t)).first()
        s = img.select('tmax_C').updateMask(FRACAO_BR)
        # 2. pixel do máximo: max com 3 entradas (Tmax, lon, lat) devolve a posição do máximo
        lonlat = ee.Image.pixelLonLat()
        pos = gi(ee.Image.cat([s, lonlat.select('longitude'), lonlat.select('latitude')]).reduceRegion(
            reducer=ee.Reducer.max(3), geometry=LIMITES, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4))
        lon, lat = pos['max1'], pos['max2']
        pt = ee.Geometry.Point([lon, lat])
        # 3. valores no pixel
        bruta, n_saidas = tmax_bruta_gfs(t, rod)
        mat = ee.Image(f'{MATRIZ}/Matriz_GFS_{mes}')
        nomes = {k: f'Tmax_{k}_{fx}' for k in ('m_sicsb', 'm_gfs', 's_sicsb', 's_gfs')}
        partes = [img.select(['tmax_C', 'tmin_C']), bruta,
                  FRACAO_BR.rename('fracao_br'),
                  ee.Image(MASCARA).select('classe').rename('classe'),
                  hist.max().rename('tmax_hist_max'),
                  era5_26.max().rename('tmax_era5_2026_max')]
        partes += [expandir_borda(mat.select(b)).rename(k) for k, b in nomes.items()]
        v = gi(ee.Image.cat(partes).reduceRegion(reducer=ee.Reducer.first(), geometry=pt, crs=CRS,
                                                 crsTransform=TRANSFORM))
        lugar = gi(GAUL2.filterBounds(pt).first())
        uf_mun = (lugar['properties'].get('ADM1_NAME'), lugar['properties'].get('ADM2_NAME')) if lugar else (None, None)
        # [K11] o teto depende da faixa e do teto gravado no dia (dias gravados antes da K11 não têm a propriedade: 2.0)
        teto_gravado = gi(img.get('teto_razao_temp_gfs')) or RAZAO_MAX
        razao = min(max(v['s_sicsb'] / max(v['s_gfs'], 1e-3), RAZAO_MIN), float(teto_gravado))
        recalc = v['m_sicsb'] + (v['tmax_bruta'] - v['m_gfs']) * razao
        # decomposição: Tmax gravada = bruta + (deslocamento da média) + (efeito da razão sobre a anomalia)
        desloc_media = v['m_sicsb'] - v['m_gfs']
        efeito_razao = (v['tmax_bruta'] - v['m_gfs']) * (razao - 1)
        if v['fracao_br'] is not None and v['fracao_br'] < 0.5:
            diag = '(c) pixel de borda: menos da metade dentro do Brasil'
        elif v['tmax_bruta'] > RECORDE:
            diag = '(a) o GFS bruto já passa do recorde: viés do modelo'
        elif recalc > RECORDE:
            diag = '(b) GFS bruto abaixo do recorde; a calibração empurrou para cima'
        elif recalc > v['tmax_hist_max'] + 1.0:
            diag = 'abaixo do recorde, mas mais de 1 °C acima do maior valor do histórico no pixel'
        else:
            diag = 'abaixo do recorde e dentro do histórico do pixel (+1 °C): plausível'
        linhas.append({
            'dia': d['dia'], 'prazo': f'L{L}', 'faixa': fx, 'Tmax_max_BR': round(d['tmax_C_max'], 2),
            f'pixels_>{RECORDE}': int(d['acima_sum'] or 0), 'lat': round(lat, 3), 'lon': round(lon, 3),
            'UF': uf_mun[0], 'municipio': uf_mun[1], 'classe_mascara': v.get('classe'),
            'fracao_no_BR': round(v['fracao_br'], 2) if v['fracao_br'] is not None else None,
            'Tmax_gravada': round(v['tmax_C'], 2), 'Tmin_gravada': round(v['tmin_C'], 2),
            'Tmax_GFS_bruto': round(v['tmax_bruta'], 2), 'saidas_GFS': gi(n_saidas),
            'm_sicsb': round(v['m_sicsb'], 2), 'm_gfs': round(v['m_gfs'], 2),
            's_sicsb': round(v['s_sicsb'], 2), 's_gfs': round(v['s_gfs'], 2), 'razao_desvios': round(razao, 3),
            'teto_razao_gravado': float(teto_gravado),
            'Tmax_recalculada': round(recalc, 2), 'desloc_media': round(desloc_media, 2),
            'efeito_razao': round(efeito_razao, 2),
            'Tmax_hist_max_1961_2025': round(v['tmax_hist_max'], 2) if v['tmax_hist_max'] is not None else None,
            'Tmax_ERA5_2026_max': round(v['tmax_era5_2026_max'], 2) if v['tmax_era5_2026_max'] is not None else None,
            'diagnostico': diag})
    tab = pd.DataFrame(linhas)
    print(f"\n=== 2 a 4. Pixel do máximo de cada dia acima de {LIMIAR_ANALISE} °C ===")
    print(tab.T.to_string(header=False))
    print("\n=== 5. Diagnóstico ===")
    for _, x in tab.iterrows():
        print(f"   {x['dia']} ({x['prazo']}, {x['UF']}/{x['municipio']}): gravada {x['Tmax_gravada']} °C | "
              f"GFS bruto {x['Tmax_GFS_bruto']} °C | deslocamento da média {x['desloc_media']:+.2f} °C | "
              f"efeito da razão dos desvios {x['efeito_razao']:+.2f} °C | máximo do histórico no pixel "
              f"{x['Tmax_hist_max_1961_2025']} °C -> {x['diagnostico']}")
        if abs(x['Tmax_recalculada'] - x['Tmax_gravada']) > 0.6:
            print(f"   ⚠️ a Tmax recalculada ({x['Tmax_recalculada']}) difere da gravada em mais de 0,6 °C: "
                  f"confira se a rodada e a faixa do dia são as esperadas (o ajuste de amplitude mínima só muda poucos décimos).")
    tab.to_csv('K10_diagnostico_tmax.csv', sep=';', decimal=',', index=False, encoding='utf-8-sig')
    print("\n💾 K10_diagnostico_tmax.csv salvo em /content (baixe e me envie junto com esta saída).")
print("\n✅ K10 encerrado (nada foi gravado).")
