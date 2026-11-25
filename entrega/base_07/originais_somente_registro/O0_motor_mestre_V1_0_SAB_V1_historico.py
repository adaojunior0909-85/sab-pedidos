# ⛔⛔⛔ NÃO EXECUTAR: SCRIPT ORIGINAL GUARDADO SÓ COMO REGISTRO DO MÉTODO (metodologia da tese) ⛔⛔⛔
# Gerou: projects/clima-492922/assets/SAB_V1, histórico 1961–2025 (os 23.741 dias). Prova: este código grava SÓ a propriedade versao = definitiva (sem versao_algoritmo), exatamente o que o Earth Engine mostrou em 03/11/2026, e calibra o solo sem teto (o que explica a umidade de até 0,9989 nos dias antigos). Texto de 05/10/2026; o histórico foi gravado entre 24/08 e 26/09/2026 (data de atualização de cada dia no asset). K17 v3 (03/11/2026): este código, rodado hoje, reproduz o gravado em todas as 16 bandas e classes de 1961 a 2013; em 2020 e 2025 só diferem as variáveis acumuladas do ERA5-Land, revistas na fonte depois da gravação
# Hoje: Histórico travado; a correção de solo e escoamento é feita na leitura (painel e e-mail).
# Substituído por: V1.1 → V1.2 → V1.3 → 05a/05b V1.5 (2026 em diante)
# Por que não rodar: ele RECRIARIA o asset acima; o banco, as calibrações e as validações (K8 a K16, 07a/07b,
#   08) foram aprovados com o asset que já existe. Rodar de novo exigiria refazer e validar tudo.
# Recebido do responsável em 03/11/2026 (motores_V1_0_V1_1_e_utilitarios_recebidos.txt, linhas 4 a 809). Abaixo da linha ORIGINAL, o texto está sem nenhuma
#   mudança. SHA-256 do trecho original: 49cfb5ed102cc683a39ab1af5e3ce6ef270a3c9e35b0d76883d62b8e3812f809
# A linha raise SystemExit abaixo faz a célula parar antes de qualquer import ou gravação.
raise SystemExit('⛔ Script original guardado só como registro. NÃO EXECUTAR (veja o cabeçalho).')
# ================================================ ORIGINAL ================================================
# =========================================================================================
# TÍTULO: MOTOR MESTRE OPERACIONAL SAB V1 - SCRIPT 1 (CONTA CLIMA)
# RESUMO DA FUNÇÃO: Autenticação, Processamento e Tarefas isoladas para clima-492922
# ATUALIZAÇÃO: Arquitetura Sequencial GFS (Polling), AERK Unificado, Delta Exato, Gamma Dinâmico.
# =========================================================================================

import ee
import pandas as pd
import math
import time
from datetime import datetime, timezone, timedelta

# =========================================================================
# 1. SETUP DE VARIÁVEIS GLOBAIS E AUTENTICAÇÃO ISOLADA
# =========================================================================
PROJECT_ID_ATIVO = 'clima-492922'
ASSET_DESTINO = f'projects/{PROJECT_ID_ATIVO}/assets/SAB_V1'
SUFIXO_TASK = 'C1'

fuso_br = timezone(timedelta(hours=-3))
data_extracao_local = datetime.now(fuso_br).strftime('%Y-%m-%d %H:%M:%S')

print(f"🔄 Iniciando sistema de gerenciamento GEE no projeto: {PROJECT_ID_ATIVO}...")
print(f"🕒 Timestamp de Operação (Local/BRT): {data_extracao_local}\n")

try:
    ee.Initialize(project=PROJECT_ID_ATIVO)
except Exception as e:
    print("🔗 Autenticação necessária:")
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID_ATIVO)

ASSET_CLIMATOLOGIA = 'projects/clima-492922/assets/SICSB_1986_2025'
ASSET_DESTINO_MATRIZ_GFS = 'projects/clima-492922/assets/SICSB_MATRIZ_GFS'
ASSET_SOLO = 'projects/clima-492922/assets/SICSB_SOLO_2015_2025'
LIMITE_HISTORICO = '2025-12-31'

limitesRegiao = (ee.FeatureCollection("FAO/GAUL/2015/level0")
                 .filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
                 .geometry().bounds())
poligonoBrasil = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_NAME', 'Brazil')).geometry()
crsNativo = 'EPSG:4326'
transformNativo = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
elevacao_br = ee.Image('USGS/SRTMGL1_003').clip(limitesRegiao)
colChuvaGeral = ee.ImageCollection('projects/ee-alexandrexavier/assets/BR-DWGD')

colecao_era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
ultima_data_era5 = colecao_era5.sort('system:time_start', False).first().date().format('YYYY-MM-dd').getInfo()

try:
    ultima_data_brd = colChuvaGeral.sort('system:time_start', False).first().date().format('YYYY-MM-dd').getInfo()
except Exception:
    ultima_data_brd = LIMITE_HISTORICO

def verificar_se_asset_existe(asset_path):
    try:
        ee.data.getAsset(asset_path)
        return True
    except Exception:
        return False

def mapear_colecao(asset_path):
    b_def, b_era, b_gfs, b_gfs_inc = set(), set(), set(), set()
    if verificar_se_asset_existe(asset_path):
        try:
            col = ee.ImageCollection(asset_path)
            lista = col.map(
                lambda img: ee.Feature(None, {
                    'id': img.id(),
                    'versao': ee.Algorithms.If(img.propertyNames().contains('versao'), img.get('versao'), 'definitiva')
                })
            ).reduceColumns(ee.Reducer.toList().repeat(2), ['id', 'versao']).get('list').getInfo()

            for idx_caminho, versao in zip(lista[0], lista[1]):
                idx = str(idx_caminho).split('/')[-1]
                if versao == 'definitiva': b_def.add(idx)
                elif versao == 'provisoria_era5': b_era.add(idx)
                elif versao == 'provisoria_gfs': b_gfs.add(idx)
                else: b_gfs_inc.add(idx)
        except Exception:
            pass
    return b_def, b_era, b_gfs, b_gfs_inc

# =========================================================================
# 2. FUNÇÕES DE PROCESSAMENTO (ROUTING DEFINITIVO / ERA5 / GFS)
# =========================================================================

def processarDia_Definitivo(data_str):
    dStart = ee.Date(data_str)
    dEnd = dStart.advance(1, 'day')
    mes_str = data_str.split('-')[1]

    cache_clima = ee.Image(f'{ASSET_CLIMATOLOGIA}/Matriz_Clima_{mes_str}')
    imgERA = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').filterBounds(limitesRegiao).filterDate(dStart, dEnd).first()

    pr_raw = imgERA.select('total_precipitation_sum').multiply(1000).max(0)
    tmax_raw = imgERA.select('temperature_2m_max').subtract(273.15).resample('bilinear')
    tmin_raw = imgERA.select('temperature_2m_min').subtract(273.15).resample('bilinear')
    u2_raw = imgERA.select('u_component_of_wind_10m').hypot(imgERA.select('v_component_of_wind_10m')).multiply(0.748).resample('bilinear')
    rs_raw = imgERA.select('surface_solar_radiation_downwards_sum').divide(1000000).resample('bilinear')
    t2m_era = imgERA.select('temperature_2m').subtract(273.15).resample('bilinear')
    tdew_era = imgERA.select('dewpoint_temperature_2m').subtract(273.15).resample('bilinear')
    rh_raw = t2m_era.expression('100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))', {'T': t2m_era, 'Td': tdew_era})
    et_pot_raw = imgERA.select('potential_evaporation_sum').multiply(-1000).max(0)

    def calibrar_estado(img_bruta, prefixo):
        m_br = cache_clima.select(ee.String(prefixo).cat('_m_br'))
        m_era = cache_clima.select(ee.String(prefixo).cat('_m_era'))
        m_br = m_br.unmask(m_br.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        m_era = m_era.unmask(m_era.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        return img_bruta.add(m_br.subtract(m_era))

    def calibrar_fluxo(img_bruta, prefixo):
        m_br = cache_clima.select(ee.String(prefixo).cat('_m_br'))
        m_era = cache_clima.select(ee.String(prefixo).cat('_m_era'))
        m_br = m_br.unmask(m_br.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        m_era = m_era.unmask(m_era.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        fator = m_br.divide(m_era.max(1e-3))
        return img_bruta.multiply(fator)

    pr_calib = calibrar_fluxo(pr_raw, 'pr').max(0).rename('pr_mm')
    u2_calib = calibrar_fluxo(u2_raw, 'u2').max(0).rename('u2')
    rs_calib = calibrar_fluxo(rs_raw, 'Rs').max(0).rename('rs')
    tmax_calib = calibrar_estado(tmax_raw, 'Tmax').rename('tmax_C')
    tmin_calib = calibrar_estado(tmin_raw, 'Tmin').rename('tmin_C')
    rh_calib = calibrar_estado(rh_raw, 'RH').clamp(0, 100).rename('RH')
    et_potencial_calib = calibrar_fluxo(et_pot_raw, 'ET').max(0).rename('et_potencial')

    es_tmax = tmax_calib.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': tmax_calib})
    es_tmin = tmin_calib.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': tmin_calib})
    es = es_tmax.add(es_tmin).divide(2)
    ea = es.multiply(rh_calib).divide(100)
    vpd_era_calib = es.subtract(ea).max(0).rename('vpd')

    cache_solo = ee.Image(f'{ASSET_SOLO}/Matriz_Solo_{mes_str}')
    ssur_era = imgERA.select('volumetric_soil_water_layer_1')
    swat_era = imgERA.expression('(l1*7 + l2*21 + l3*72) / 100', {
        'l1': imgERA.select('volumetric_soil_water_layer_1'),
        'l2': imgERA.select('volumetric_soil_water_layer_2'),
        'l3': imgERA.select('volumetric_soil_water_layer_3')
    })
    rsup_era = imgERA.select('surface_runoff_sum').multiply(1000).max(0)
    rsub_era = imgERA.select('sub_surface_runoff_sum').multiply(1000).max(0)

    def calibrar_solo_fluxo(img_bruta, prefixo):
        m_smap = cache_solo.select(ee.String(prefixo).cat('_m_smap'))
        m_era = cache_solo.select(ee.String(prefixo).cat('_m_era5'))
        m_smap = m_smap.unmask(m_smap.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        m_era = m_era.unmask(m_era.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        fator = m_smap.divide(m_era.max(1e-3))
        return img_bruta.multiply(fator)

    ssur_smap = calibrar_solo_fluxo(ssur_era, 'ssur').max(0).rename('soil_moisture_0_5cm_m3_m3')
    swat_smap = calibrar_solo_fluxo(swat_era, 'swat').max(0).rename('soil_moisture_0_100cm_m3_m3')
    runoff_sup = calibrar_solo_fluxo(rsup_era, 'rsup').max(0).rename('runoff_sup_mm')
    runoff_sub = calibrar_solo_fluxo(rsub_era, 'rsub').max(0).rename('runoff_sub_mm')

    dummyBR = ee.Image.constant([-99999] * 7).rename(['pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs', 'ET'])
    imgBR = colChuvaGeral.filterDate(dStart, dEnd).merge(ee.ImageCollection([dummyBR])).first()
    has_real_br = imgBR.select('pr').gt(-90000)

    tmax_br = imgBR.select('Tmax').multiply(0.00106815).add(15.0)
    tmin_br = imgBR.select('Tmin').multiply(0.00106815).add(15.0)
    rh_br = imgBR.select('RH').multiply(0.39370079).add(-0.393701).clamp(0, 100)

    es_br = tmax_br.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': tmax_br}).add(
            tmin_br.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': tmin_br})).divide(2)
    ea_br = es_br.multiply(rh_br).divide(100)
    vpd_br = es_br.subtract(ea_br).max(0)

    et_pot_br_final = imgBR.select('ET').multiply(0.05118110).add(-0.0511811)
    et_pot_mesclado = et_potencial_calib.where(has_real_br, et_pot_br_final)

    et_real_era = imgERA.select('total_evaporation_sum').multiply(-1000).max(0).rename('et_real').resample('bilinear')
    transpiracao_era = imgERA.select('evaporation_from_bare_soil_sum').multiply(-1000).max(0).rename('transpiracao_mm').resample('bilinear')
    tsolo_era = imgERA.select('soil_temperature_level_1').subtract(273.15).rename('tsolo_C').resample('bilinear')
    tfolha_era = imgERA.select('skin_temperature').subtract(273.15).rename('tfolha_C').resample('bilinear')

    img_interior = ee.Image.cat([
        pr_calib.where(has_real_br, imgBR.select('pr').multiply(0.00686666).add(225.0).max(0)).rename('pr_mm'),
        tmax_calib.where(has_real_br, tmax_br).rename('tmax_C'),
        tmin_calib.where(has_real_br, tmin_br).rename('tmin_C'),
        rh_calib.where(has_real_br, rh_br).rename('RH'),
        et_pot_mesclado.rename('et_potencial'),
        et_real_era, vpd_era_calib.where(has_real_br, vpd_br).rename('vpd'),
        rs_calib.where(has_real_br, imgBR.select('Rs').multiply(0.15708661).add(-0.057087)).rename('rs'),
        u2_calib.where(has_real_br, imgBR.select('u2').multiply(0.05905512).add(-0.059055)).rename('u2'),
        tsolo_era, tfolha_era, transpiracao_era,
        runoff_sup, runoff_sub, ssur_smap, swat_smap
    ]).toFloat()

    img_fallback = ee.Image.cat([
        pr_calib.rename('pr_mm'), tmax_calib.rename('tmax_C'), tmin_calib.rename('tmin_C'),
        rh_calib.rename('RH'), et_potencial_calib.rename('et_potencial'), et_real_era,
        vpd_era_calib.rename('vpd'), rs_calib.rename('rs'), u2_calib.rename('u2'),
        tsolo_era, tfolha_era, transpiracao_era,
        runoff_sup, runoff_sub, ssur_smap, swat_smap
    ]).toFloat()

    borda_expansao = img_fallback.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels')
    img_fallback_expandida = img_fallback.unmask(borda_expansao)

    final_img_raw = img_interior.unmask(img_fallback_expandida)

    et_pot = final_img_raw.select('et_potencial')
    et_real = final_img_raw.select('et_real')
    transp = final_img_raw.select('transpiracao_mm')

    et_pot_segura = et_pot.unmask(et_real)
    et_real_limitada = et_real.min(et_pot_segura).rename('et_real')
    transp_limitada = transp.min(et_real_limitada).rename('transpiracao_mm')

    bandas_consertadas = ee.Image.cat([et_real_limitada, transp_limitada])
    final_img = final_img_raw.addBands(bandas_consertadas, overwrite=True).clip(poligonoBrasil)

    return final_img.set('system:time_start', dStart.millis()).set('versao', 'definitiva')


def processarDia_Rota1(data_str):
    dStart = ee.Date(data_str)
    dEnd = dStart.advance(1, 'day')
    mes_str = data_str.split('-')[1]

    cache_clima = ee.Image(f'{ASSET_CLIMATOLOGIA}/Matriz_Clima_{mes_str}')
    imgERA = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').filterBounds(limitesRegiao).filterDate(dStart, dEnd).first()

    pr_raw = imgERA.select('total_precipitation_sum').multiply(1000).max(0)
    tmax_raw = imgERA.select('temperature_2m_max').subtract(273.15).resample('bilinear')
    tmin_raw = imgERA.select('temperature_2m_min').subtract(273.15).resample('bilinear')
    u2_raw = imgERA.select('u_component_of_wind_10m').hypot(imgERA.select('v_component_of_wind_10m')).multiply(0.748).resample('bilinear')
    rs_raw = imgERA.select('surface_solar_radiation_downwards_sum').divide(1000000).resample('bilinear')
    t2m_era = imgERA.select('temperature_2m').subtract(273.15).resample('bilinear')
    tdew_era = imgERA.select('dewpoint_temperature_2m').subtract(273.15).resample('bilinear')
    rh_raw = t2m_era.expression('100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))', {'T': t2m_era, 'Td': tdew_era})
    et_pot_raw = imgERA.select('potential_evaporation_sum').multiply(-1000).max(0)

    def calibrar_estado(img_bruta, prefixo):
        m_br = cache_clima.select(ee.String(prefixo).cat('_m_br'))
        m_era = cache_clima.select(ee.String(prefixo).cat('_m_era'))
        m_br = m_br.unmask(m_br.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        m_era = m_era.unmask(m_era.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        return img_bruta.add(m_br.subtract(m_era))

    def calibrar_fluxo(img_bruta, prefixo):
        m_br = cache_clima.select(ee.String(prefixo).cat('_m_br'))
        m_era = cache_clima.select(ee.String(prefixo).cat('_m_era'))
        m_br = m_br.unmask(m_br.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        m_era = m_era.unmask(m_era.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        fator = m_br.divide(m_era.max(1e-3))
        return img_bruta.multiply(fator)

    pr_calib = calibrar_fluxo(pr_raw, 'pr').max(0).rename('pr_mm')
    u2_calib = calibrar_fluxo(u2_raw, 'u2').max(0).rename('u2')
    rs_calib = calibrar_fluxo(rs_raw, 'Rs').max(0).rename('rs')
    tmax_calib = calibrar_estado(tmax_raw, 'Tmax').rename('tmax_C')
    tmin_calib = calibrar_estado(tmin_raw, 'Tmin').rename('tmin_C')
    rh_calib = calibrar_estado(rh_raw, 'RH').clamp(0, 100).rename('RH')
    et_potencial_calib = calibrar_fluxo(et_pot_raw, 'ET').max(0).rename('et_potencial')

    es_tmax = tmax_calib.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': tmax_calib})
    es_tmin = tmin_calib.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': tmin_calib})
    es = es_tmax.add(es_tmin).divide(2)
    ea = es.multiply(rh_calib).divide(100)
    vpd = es.subtract(ea).max(0).rename('vpd')

    et_real_era = imgERA.select('total_evaporation_sum').multiply(-1000).max(0).rename('et_real').resample('bilinear')
    transpiracao_era = imgERA.select('evaporation_from_bare_soil_sum').multiply(-1000).max(0).rename('transpiracao_mm').resample('bilinear')
    tsolo_era = imgERA.select('soil_temperature_level_1').subtract(273.15).rename('tsolo_C').resample('bilinear')
    tfolha_era = imgERA.select('skin_temperature').subtract(273.15).rename('tfolha_C').resample('bilinear')

    cache_solo = ee.Image(f'{ASSET_SOLO}/Matriz_Solo_{mes_str}')
    ssur_era = imgERA.select('volumetric_soil_water_layer_1')
    swat_era = imgERA.expression(
        '(l1*7 + l2*21 + l3*72) / 100',
        {
            'l1': imgERA.select('volumetric_soil_water_layer_1'),
            'l2': imgERA.select('volumetric_soil_water_layer_2'),
            'l3': imgERA.select('volumetric_soil_water_layer_3')
        }
    )
    rsup_era = imgERA.select('surface_runoff_sum').multiply(1000).max(0)
    rsub_era = imgERA.select('sub_surface_runoff_sum').multiply(1000).max(0)

    def calibrar_solo_fluxo(img_bruta, prefixo):
        m_smap = cache_solo.select(ee.String(prefixo).cat('_m_smap'))
        m_era = cache_solo.select(ee.String(prefixo).cat('_m_era5'))
        m_smap = m_smap.unmask(m_smap.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        m_era = m_era.unmask(m_era.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
        fator = m_smap.divide(m_era.max(1e-3))
        return img_bruta.multiply(fator)

    ssur_smap = calibrar_solo_fluxo(ssur_era, 'ssur').max(0).rename('soil_moisture_0_5cm_m3_m3')
    swat_smap = calibrar_solo_fluxo(swat_era, 'swat').max(0).rename('soil_moisture_0_100cm_m3_m3')
    runoff_sup = calibrar_solo_fluxo(rsup_era, 'rsup').max(0).rename('runoff_sup_mm')
    runoff_sub = calibrar_solo_fluxo(rsub_era, 'rsub').max(0).rename('runoff_sub_mm')

    img_raw = ee.Image.cat([
        pr_calib, tmax_calib, tmin_calib, rh_calib, et_potencial_calib, et_real_era, vpd,
        rs_calib, u2_calib, tsolo_era, tfolha_era, transpiracao_era,
        runoff_sup, runoff_sub, ssur_smap, swat_smap
    ]).toFloat()

    borda_expansao = img_raw.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels')
    img_expandida = img_raw.unmask(borda_expansao)

    et_pot = img_expandida.select('et_potencial')
    et_real = img_expandida.select('et_real')
    transp = img_expandida.select('transpiracao_mm')

    et_pot_segura = et_pot.unmask(et_real)
    et_real_limitada = et_real.min(et_pot_segura).rename('et_real')
    transp_limitada = transp.min(et_real_limitada).rename('transpiracao_mm')

    bandas_consertadas = ee.Image.cat([et_real_limitada, transp_limitada])
    final_img = img_expandida.addBands(bandas_consertadas, overwrite=True).clip(poligonoBrasil)

    return final_img.set('system:time_start', dStart.millis()).set('versao', 'provisoria_era5')

def processarDia_GFS_Isolado(data_str, estado_anterior):
    lat_rad = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180.0)
    pressao_atm = elevacao_br.multiply(-0.0065).add(293.0).divide(293.0).pow(5.26).multiply(101.3)
    gamma_dinamico = pressao_atm.multiply(0.000665)

    latest_global_run = ee.ImageCollection('NOAA/GFS0P25') \
        .filterBounds(limitesRegiao) \
        .sort('creation_time', False) \
        .first()

    data_atual = ee.Date(data_str)
    mes_str = data_atual.format('MM')

    time_start = data_atual.millis()
    time_end = data_atual.advance(1, 'day').millis()

    runs_before = ee.ImageCollection('NOAA/GFS0P25') \
        .filterBounds(limitesRegiao) \
        .filter(ee.Filter.lte('creation_time', time_start)) \
        .filter(ee.Filter.gte('creation_time', time_start.subtract(ee.Number(48).multiply(3600000))))

    target_run_img = ee.Image(ee.Algorithms.If(
        runs_before.size().gt(0),
        runs_before.sort('creation_time', False).first(),
        latest_global_run
    ))
    creation_time = ee.Number(target_run_img.get('creation_time'))

    gfs_raw = ee.ImageCollection('NOAA/GFS0P25') \
        .filterBounds(limitesRegiao) \
        .filter(ee.Filter.eq('creation_time', creation_time)) \
        .filter(ee.Filter.gte('forecast_time', time_start)) \
        .filter(ee.Filter.lt('forecast_time', time_end))

    col_hora_zero = gfs_raw.filter(ee.Filter.eq('forecast_hours', 0))
    col_acumulo = gfs_raw.filter(ee.Filter.gt('forecast_hours', 0))

    tem_acumulo = col_acumulo.size().gt(0)
    tem_zero = col_hora_zero.size().gt(0)

    dias_horizonte = ee.Number(data_atual.difference(ee.Date(creation_time), 'day'))
    limite_imagens = ee.Number(ee.Algorithms.If(dias_horizonte.lt(5), 24, 8))

    hora_inicio = ee.Number(data_atual.difference(ee.Date(creation_time), 'hour'))
    hora_fim = hora_inicio.add(24)
    horas_precip = ee.List.sequence(hora_inicio.add(6), hora_fim, 6)
    chuva_blocos = gfs_raw.filter(ee.Filter.inList('forecast_hours', horas_precip))

    qtd_imagens = col_acumulo.size()
    qtd_chuva = chuva_blocos.size()

    condicao_imagens = qtd_imagens.gte(limite_imagens)
    condicao_chuva_valida = qtd_chuva.gte(4)

    dados_completos = condicao_imagens.And(condicao_chuva_valida)
    dados_parciais_aceitaveis = qtd_imagens.gt(0)

    flag_versao_gfs = ee.Algorithms.If(dados_completos, 'provisoria_gfs', 'provisoria_gfs_incompleta')

    img_metadados = ee.Image(ee.Algorithms.If(
        tem_acumulo, col_acumulo.first(),
        ee.Algorithms.If(tem_zero, col_hora_zero.first(), ee.Image.constant(0).set('system:version', 0))
    ))
    versao_micro = ee.Number(img_metadados.get('system:version'))
    registro_gee = ee.Algorithms.If(
        versao_micro.gt(0),
        ee.Date(versao_micro.divide(1000)).format('YYYY-MM-dd HH:mm:ss'),
        'N/A (Sintetico)'
    )

    def computar_dinamica_completa():
        def calcular_valores_diarios(col):
            def flag_6h(img):
                fh = ee.Number(img.get('forecast_hours'))
                return img.set('is_6h', fh.mod(6).eq(0))

            col_chuva = col.map(flag_6h).filter(ee.Filter.eq('is_6h', 1))
            img_chuva = ee.Image(ee.Algorithms.If(
                col_chuva.size().gt(0),
                col_chuva.select('total_precipitation_surface').sum(),
                ee.Image.constant(0).rename('total_precipitation_surface')
            ))

            img_tmax = col.select('maximum_temperature_2m_above_ground').max()
            img_tmin = col.select('minimum_temperature_2m_above_ground').min()

            img_rad_rh = col.select([
                'downward_shortwave_radiation_flux',
                'relative_humidity_2m_above_ground'
            ]).mean()

            def add_wind_speed(img):
                ws = img.select('u_component_of_wind_10m_above_ground') \
                    .hypot(img.select('v_component_of_wind_10m_above_ground')) \
                    .rename('wind_speed_10m_above_ground')
                return ws

            img_wind = col.map(add_wind_speed).mean()

            return ee.Image.cat([img_chuva, img_tmax, img_tmin, img_rad_rh, img_wind])

        img_processada = ee.Image(ee.Algorithms.If(
            tem_acumulo,
            calcular_valores_diarios(col_acumulo),
            ee.Image.constant([0, 0, 0, 0, 0, 0]).rename([
                'total_precipitation_surface',
                'maximum_temperature_2m_above_ground',
                'minimum_temperature_2m_above_ground',
                'downward_shortwave_radiation_flux',
                'relative_humidity_2m_above_ground',
                'wind_speed_10m_above_ground'
            ])
        ))

        pr_raw = img_processada.select('total_precipitation_surface').max(0).rename('pr')
        tmax_raw = img_processada.select('maximum_temperature_2m_above_ground').rename('Tmax')
        tmin_raw = img_processada.select('minimum_temperature_2m_above_ground').rename('Tmin')
        rs_raw = img_processada.select('downward_shortwave_radiation_flux').multiply(0.0864).max(0).rename('Rs')
        rh_raw = img_processada.select('relative_humidity_2m_above_ground').clamp(0, 100).rename('RH')
        u2_raw = img_processada.select('wind_speed_10m_above_ground').multiply(0.748).rename('u2')

        cache_gfs = ee.ImageCollection(ASSET_DESTINO_MATRIZ_GFS).filter(ee.Filter.eq('system:index', ee.String('Matriz_GFS_').cat(mes_str))).first()

        def calibrar_gfs_estado(img_raw, banda):
            m_sicsb_banda = ee.String(banda).cat('_m_sicsb')
            m_sab_banda = ee.String(banda).cat('_m_sab')
            m_alvo = ee.Image(ee.Algorithms.If(
                cache_gfs.bandNames().contains(m_sicsb_banda),
                cache_gfs.select(m_sicsb_banda),
                cache_gfs.select(m_sab_banda)
            ))
            gfs_sicsb_banda = ee.String(banda).cat('_m_gfs')
            m_gfs = cache_gfs.select(gfs_sicsb_banda)
            m_alvo = m_alvo.unmask(m_alvo.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
            m_gfs = m_gfs.unmask(m_gfs.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
            return img_raw.add(m_alvo.subtract(m_gfs))

        def calibrar_gfs_fluxo(img_raw, banda):
            m_sicsb_banda = ee.String(banda).cat('_m_sicsb')
            m_sab_banda = ee.String(banda).cat('_m_sab')
            m_alvo = ee.Image(ee.Algorithms.If(
                cache_gfs.bandNames().contains(m_sicsb_banda),
                cache_gfs.select(m_sicsb_banda),
                cache_gfs.select(m_sab_banda)
            ))
            gfs_sicsb_banda = ee.String(banda).cat('_m_gfs')
            m_gfs = cache_gfs.select(gfs_sicsb_banda)
            m_alvo = m_alvo.unmask(m_alvo.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
            m_gfs = m_gfs.unmask(m_gfs.reproject(crs=crsNativo, crsTransform=transformNativo).focalMean(1, 'square', 'pixels'))
            fator = m_alvo.divide(m_gfs.max(1e-3))
            return img_raw.multiply(fator)

        pr_calib = calibrar_gfs_fluxo(pr_raw, 'pr').max(0).rename('pr_mm').toFloat()
        tmax_calib = calibrar_gfs_estado(tmax_raw, 'Tmax').rename('tmax_C').toFloat()
        tmin_calib = calibrar_gfs_estado(tmin_raw, 'Tmin').rename('tmin_C').toFloat()
        rh_calib = calibrar_gfs_estado(rh_raw, 'RH').clamp(0, 100).rename('RH').toFloat()
        u2_calib = calibrar_gfs_fluxo(u2_raw, 'u2').max(0).rename('u2').toFloat()
        rs_calib = calibrar_gfs_fluxo(rs_raw, 'Rs').max(0).rename('rs').toFloat()

        tmedia = tmax_calib.add(tmin_calib).divide(2)
        es_tmax = tmax_calib.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': tmax_calib})
        es_tmin = tmin_calib.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': tmin_calib})
        es = es_tmax.add(es_tmin).divide(2)
        ea = es.multiply(rh_calib).divide(100)
        vpd = es.subtract(ea).max(0).rename('vpd').toFloat()

        J = ee.Number(data_atual.getRelative('day', 'year')).add(1)
        dr = ee.Number(J).multiply(2.0 * math.pi / 365.0).cos().multiply(0.033).add(1.0)
        delta_sol = ee.Number(J).multiply(2.0 * math.pi / 365.0).subtract(1.39).sin().multiply(0.409)
        ws = lat_rad.tan().multiply(ee.Number(delta_sol).tan()).multiply(-1.0).clamp(-1.0, 1.0).acos()

        termo1 = ws.multiply(lat_rad.sin()).multiply(ee.Number(delta_sol).sin())
        termo2 = lat_rad.cos().multiply(ee.Number(delta_sol).cos()).multiply(ws.sin())
        Ra = termo1.add(termo2).multiply(dr).multiply((24.0 * 60.0 / math.pi) * 0.0820)

        Rso = elevacao_br.multiply(0.00002).add(0.75).multiply(Ra)
        Rs_Rso = rs_calib.divide(Rso).clamp(0.0, 1.0)
        Rns = rs_calib.multiply(0.77)

        tmax_k = tmax_calib.add(273.16)
        tmin_k = tmin_calib.add(273.16)
        stefan_boltzmann = 4.903e-9

        rad_term = tmax_k.pow(4).add(tmin_k.pow(4)).divide(2.0).multiply(stefan_boltzmann)
        umid_term = ea.sqrt().multiply(0.14).multiply(-1.0).add(0.34)
        nuvem_term = Rs_Rso.multiply(1.35).subtract(0.35)

        Rnl = rad_term.multiply(umid_term).multiply(nuvem_term).max(0)
        Rn = Rns.subtract(Rnl)

        delta_press = tmedia.expression('4283.58 * (0.6108 * exp(17.625 * T / (T + 243.04))) / ((T + 243.04) ** 2)', {'T': tmedia})

        num_1 = delta_press.multiply(Rn).multiply(0.408)
        num_2 = gamma_dinamico.multiply(ee.Image(900).divide(tmedia.add(273))).multiply(u2_calib).multiply(vpd)
        den = delta_press.add(gamma_dinamico.multiply(ee.Image(1).add(u2_calib.multiply(0.34))))
        et_potencial = num_1.add(num_2).divide(den).max(0).rename('et_potencial').toFloat()

        sw_100_mm = estado_anterior.select('sw_100')
        sw_5_mm = estado_anterior.select('sw_5')

        saturacao = sw_100_mm.divide(400)
        cn_dinamico = ee.Image.constant(60).add(saturacao.multiply(35))
        s_gfs = ee.Image.constant(25400).divide(cn_dinamico).subtract(254)
        ia_gfs = s_gfs.multiply(0.2)
        p_minus_ia = pr_calib.subtract(ia_gfs).max(0)

        runoff_sup = p_minus_ia.pow(2).divide(p_minus_ia.add(s_gfs)).rename('runoff_sup_mm').toFloat()
        infiltracao = pr_calib.subtract(runoff_sup).max(0)

        kcb = vpd.multiply(-0.15).add(1.10).clamp(0.15, 1.05)
        tew = ee.Image.constant(20)
        rew = ee.Image.constant(8)
        kc_max = ee.Image.constant(1.2)

        d_e = tew.subtract(sw_5_mm).max(0)
        k_r = tew.subtract(d_e).divide(tew.subtract(rew)).clamp(0, 1)
        k_e = k_r.multiply(kc_max.subtract(kcb)).max(0)
        ks = sw_100_mm.subtract(100).divide(100).clamp(0.1, 1.0)

        evaporacao = k_e.multiply(et_potencial)
        transpiracao = kcb.multiply(ks).multiply(et_potencial)
        et_real = evaporacao.add(transpiracao).min(et_potencial).rename('et_real').toFloat()
        transpiracao_banda = transpiracao.min(et_real).rename('transpiracao_mm').toFloat()

        sw_100_temp = sw_100_mm.add(infiltracao).subtract(et_real)
        excesso_sat = sw_100_temp.subtract(400).max(0)
        sw_rebaixado = sw_100_temp.min(400)
        drenagem_lenta = sw_rebaixado.subtract(330).max(0).multiply(0.04)
        runoff_sub = excesso_sat.add(drenagem_lenta).rename('runoff_sub_mm').toFloat()

        novo_sw_100_mm = sw_100_temp.subtract(runoff_sub).clamp(0, 400).rename('sw_100')
        novo_sw_5_mm = sw_5_mm.add(infiltracao).subtract(evaporacao).clamp(0, 25).rename('sw_5')

        sw_100_m3m3 = novo_sw_100_mm.divide(1000).rename('soil_moisture_0_100cm_m3_m3').toFloat()
        sw_5_m3m3 = novo_sw_5_mm.divide(50).rename('soil_moisture_0_5cm_m3_m3').toFloat()

        tsolo = tmedia.rename('tsolo_C').toFloat()
        tfolha = tmin_calib.rename('tfolha_C').toFloat()

        img_gfs_raw = ee.Image.cat([
            pr_calib, tmax_calib, tmin_calib, rh_calib, et_potencial, et_real, vpd,
            rs_calib, u2_calib, tsolo, tfolha, transpiracao_banda,
            runoff_sup, runoff_sub, sw_5_m3m3, sw_100_m3m3,
            novo_sw_100_mm, novo_sw_5_mm
        ]).resample('bicubic').reproject(crs=crsNativo, crsTransform=transformNativo)

        borda_gfs = img_gfs_raw.focalMean(1, 'square', 'pixels')
        final_img_gfs_raw = img_gfs_raw.unmask(borda_gfs)

        et_pot_gfs = final_img_gfs_raw.select('et_potencial')
        et_real_gfs = final_img_gfs_raw.select('et_real')
        transp_gfs = final_img_gfs_raw.select('transpiracao_mm')

        et_pot_segura_gfs = et_pot_gfs.unmask(et_real_gfs)
        et_real_limitada_gfs = et_real_gfs.min(et_pot_segura_gfs).rename('et_real')
        transp_limitada_gfs = transp_gfs.min(et_real_limitada_gfs).rename('transpiracao_mm')

        bandas_consertadas_gfs = ee.Image.cat([et_real_limitada_gfs, transp_limitada_gfs])
        final_img = final_img_gfs_raw.addBands(bandas_consertadas_gfs, overwrite=True).clip(poligonoBrasil)

        return final_img.set({
            'system:time_start': data_atual.millis(),
            'versao': flag_versao_gfs,
            'Rodada_Utilizada_NOAA': ee.Date(creation_time).format('YYYY-MM-dd HH:mm:ss'),
            'Registro_Servidor_GEE': registro_gee,
            'Momento_Extracao_Local': data_extracao_local,
            'Imagens_Validas_GFS': qtd_imagens
        })

    def computar_cenario_falha():
        # Extrai estritamente as bandas repassadas pelo código isolado
        fallback_mm = estado_anterior.select(['sw_100', 'sw_5'])

        # Recria as variáveis volumétricas a partir do balanço congelado
        sw_100_m3m3 = fallback_mm.select('sw_100').divide(1000).rename('soil_moisture_0_100cm_m3_m3').toFloat()
        sw_5_m3m3 = fallback_mm.select('sw_5').divide(50).rename('soil_moisture_0_5cm_m3_m3').toFloat()

        fallback_completo = ee.Image.cat([fallback_mm, sw_5_m3m3, sw_100_m3m3])

        dummy_ausente = ee.Image.constant([0]*14).rename([
            'pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd',
            'rs', 'u2', 'tsolo_C', 'tfolha_C', 'transpiracao_mm',
            'runoff_sup_mm', 'runoff_sub_mm'
        ]).toFloat().updateMask(0)

        return ee.Image.cat([fallback_completo, dummy_ausente]).set({
            'system:time_start': data_atual.millis(),
            'versao': 'falha_latencia_gfs',
            'Rodada_Utilizada_NOAA': 'N/A',
            'Registro_Servidor_GEE': 'N/A',
            'Momento_Extracao_Local': data_extracao_local,
            'Imagens_Validas_GFS': 0
        })

    resultado_dia = ee.Image(ee.Algorithms.If(
        dados_parciais_aceitaveis,
        computar_dinamica_completa(),
        computar_cenario_falha()
    ))

    return resultado_dia.select(resultado_dia.bandNames().remove('sw_100').remove('sw_5'))

# =========================================================================
# 3. PAINEL DE CONTROLE DE EXECUÇÃO
# =========================================================================
print("==========================================================")
print(f"🕹️ CENTRO OPERACIONAL SAB V1 - TASK MANAGER {PROJECT_ID_ATIVO}")
print("==========================================================")

data_hoje_dt = datetime.now(timezone.utc)
data_fim_processo = (data_hoje_dt + timedelta(days=16)).strftime('%Y-%m-%d')
LIMITE_TAREFAS_MAX = 3000

def checar_tarefas_ativas():
    ativas = set()
    try:
        lista_tarefas = ee.data.getTaskList()
        for task_info in lista_tarefas:
            if task_info.get('state') in ['RUNNING', 'READY', 'SUBMITTED', 'PENDING']:
                desc = task_info.get('description', '')
                if desc.startswith('SAB_M_'):
                    ativas.add(desc)
    except Exception:
        pass
    return ativas

tarefas_ativas = checar_tarefas_ativas()
capacidade_disponivel = max(0, LIMITE_TAREFAS_MAX - len(tarefas_ativas))
print(f"📊 LIMITE DO TASK MANAGER: {LIMITE_TAREFAS_MAX:,} tarefas max | {len(tarefas_ativas):,} ativas na nuvem | {capacidade_disponivel:,} vagas disponíveis.\n")

print(f"🔍 Mapeando inventário da Conta {PROJECT_ID_ATIVO}...")
banco_def, banco_era, banco_gfs, banco_gfs_inc = mapear_colecao(ASSET_DESTINO)

def mapear_status(d_str, nome_imagem_id):
    ja_ex = (nome_imagem_id in banco_def) or (nome_imagem_id in banco_era) or (nome_imagem_id in banco_gfs) or (nome_imagem_id in banco_gfs_inc)
    if ja_ex:
        if nome_imagem_id in banco_gfs_inc:
            return 'precisa_upgrade'
        elif d_str <= ultima_data_brd and ((nome_imagem_id in banco_era) or (nome_imagem_id in banco_gfs)) and d_str > LIMITE_HISTORICO:
            return 'precisa_upgrade'
        elif d_str <= ultima_data_era5 and (nome_imagem_id in banco_gfs):
            return 'precisa_upgrade'
        else:
            return 'gravado'
    return 'ausente'

def executar_esteira_por_anos(anos_lista, rotulo_prioridade):
    global capacidade_disponivel
    print(f"🔎 {rotulo_prioridade}: Verificando integridade ano a ano...")
    anos_pendentes_existentes = False

    for ano in anos_lista:
        inicio_ano = f"{ano}-01-01"
        fim_ano = f"{ano}-12-31" if str(ano) != '2026' else data_fim_processo
        if inicio_ano > data_fim_processo: break

        datas_ano = pd.date_range(start=inicio_ano, end=fim_ano).strftime('%Y-%m-%d').tolist()

        gravados = 0
        na_fila = 0
        pendentes = []

        for d_str in datas_ano:
            partes = d_str.split('-')
            nome_imagem_id = f"SAB_{partes[0]}_{partes[1]}_{partes[2]}"
            desc_tarefa = f"SAB_M_{partes[0]}_{partes[1]}_{partes[2]}_{SUFIXO_TASK}"

            if desc_tarefa in tarefas_ativas:
                na_fila += 1
                continue

            status = mapear_status(d_str, nome_imagem_id)

            if status == 'gravado':
                gravados += 1
            else:
                pendentes.append((d_str, nome_imagem_id, desc_tarefa, status))

        total_dias_ano = len(datas_ano)

        if len(pendentes) == 0:
            print(f"  📅 [ANO {ano}] Concluído -> {gravados:,} gravados no asset | {na_fila:,} na fila (Total: {total_dias_ano} dias).")
        else:
            anos_pendentes_existentes = True
            qtd_tarefas_para_enviar = len(pendentes)

            if capacidade_disponivel < qtd_tarefas_para_enviar:
                print(f"  ⚠️ [ANO {ano}] INTERROMPIDO -> Requer {qtd_tarefas_para_enviar} vagas, mas restam apenas {capacidade_disponivel} (Limite {LIMITE_TAREFAS_MAX:,}).")
                return True

            pendentes_historico = [p for p in pendentes if p[0] <= ultima_data_era5]
            pendentes_previsao = [p for p in pendentes if p[0] > ultima_data_era5]

            # 1. Despacho assíncrono para os dados históricos consolidados (BR-DWGD e ERA5)
            enviados_hoje = 0
            for d_str, nome_img, desc_tarefa, st_atual in pendentes_historico:
                caminho_completo = f'{ASSET_DESTINO}/{nome_img}'

                if st_atual == 'precisa_upgrade':
                    try:
                        ee.data.deleteAsset(caminho_completo)
                        banco_era.discard(nome_img)
                        banco_gfs.discard(nome_img)
                        banco_gfs_inc.discard(nome_img)
                    except Exception: pass

                if d_str <= ultima_data_brd:
                    img_export = processarDia_Definitivo(d_str)
                else:
                    img_export = processarDia_Rota1(d_str)

                task = ee.batch.Export.image.toAsset(
                    image=img_export,
                    description=desc_tarefa,
                    assetId=caminho_completo,
                    region=limitesRegiao,
                    crs=crsNativo,
                    crsTransform=transformNativo,
                    maxPixels=1e13
                )
                task.start()
                tarefas_ativas.add(desc_tarefa)
                enviados_hoje += 1
                capacidade_disponivel -= 1

            # 2. Despacho bloqueante sequencial para as projeções futuras (GFS)
            if pendentes_previsao:
                print(f"  ⚙ [ANO {ano}] Iniciando roteamento GFS sequencial para {len(pendentes_previsao)} dias preditivos.")
                for d_str, nome_img, desc_tarefa, st_atual in pendentes_previsao:
                    caminho_completo = f'{ASSET_DESTINO}/{nome_img}'

                    if st_atual == 'precisa_upgrade':
                        try:
                            ee.data.deleteAsset(caminho_completo)
                            banco_gfs_inc.discard(nome_img)
                        except Exception: pass

                    data_atual_dt = datetime.strptime(d_str, '%Y-%m-%d')
                    data_ant_str = (data_atual_dt - timedelta(days=1)).strftime('%Y-%m-%d')
                    partes_ant = data_ant_str.split('-')
                    asset_ant = f'{ASSET_DESTINO}/SAB_{partes_ant[0]}_{partes_ant[1]}_{partes_ant[2]}'

                    print(f"    ⏳ {d_str}: Aguardando consolidação física do dia base ({data_ant_str}) na nuvem...")
                    while not verificar_se_asset_existe(asset_ant):
                        time.sleep(30)

                    ultimo_est_sat = ee.Image(asset_ant)
                    estado_solo_inicial = ee.Image.cat([
                        ultimo_est_sat.select('soil_moisture_0_100cm_m3_m3').multiply(1000).rename('sw_100'),
                        ultimo_est_sat.select('soil_moisture_0_5cm_m3_m3').multiply(50).rename('sw_5')
                    ])

                    img_export = processarDia_GFS_Isolado(d_str, estado_solo_inicial)

                    task = ee.batch.Export.image.toAsset(
                        image=img_export,
                        description=desc_tarefa,
                        assetId=caminho_completo,
                        region=limitesRegiao,
                        crs=crsNativo,
                        crsTransform=transformNativo,
                        maxPixels=1e13
                    )
                    task.start()
                    tarefas_ativas.add(desc_tarefa)
                    enviados_hoje += 1
                    capacidade_disponivel -= 1

                    while True:
                        state = task.status().get('state')
                        if state in ['COMPLETED', 'FAILED', 'CANCELLED']:
                            if state != 'COMPLETED':
                                raise RuntimeError(f"Falha na esteira sequencial. Tarefa {desc_tarefa} abortada com status: {state}")
                            print(f"    ✔️️ {d_str}: Exportação validada com sucesso.")
                            break
                        time.sleep(30)

            print(f"  📅 [ANO {ano}] Concluído -> {gravados:,} gravados no asset | {na_fila + enviados_hoje:,} na fila do Task Manager.")

    return anos_pendentes_existentes

anos_p1 = list(range(1991, 2027))
p1_tem_pendencias = executar_esteira_por_anos(anos_p1, "📌 PRIORIDADE PRINCIPAL (1991-2026+)")

if not p1_tem_pendencias:
    print("\n✔️ PRIORIDADE PRINCIPAL (1991-2026+) 100% CONSOLIDADA!")
    anos_p2 = list(range(1961, 1991))
    executar_esteira_por_anos(anos_p2, "🔍 PRIORIDADE SECUNDÁRIA (1961-1990)")
