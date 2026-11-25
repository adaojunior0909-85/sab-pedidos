# >>> K19b: AUDITORIA PROFUNDA DO SAB (03/11/2026). SOMENTE LEITURA. Cole inteiro numa célula do Colab, sem editar. <<<
# =========================================================================================
# v4 / K19b (03/11, 20h30): na rodada das 19h29, D2, D3, D4 e D6 terminaram; a D5 (um ano inteiro de pontos num
#   pedido) e a D1 (V1.0 no Brasil inteiro por dia) passaram da memória do Earth Engine. Agora a D5 pede um MÊS por vez
#   (e divide os pontos se ainda for pesado) e a D1 compara nos pixels sorteados (A 200, B 100, C todos, borda 50),
#   cada versão sozinha, em lotes que caem pela metade, como na K17. A K19b roda só D5 e D1.
# v3 (03/11, 19h15): a D5 passa a medir também UR, radiação e vento (corrigidos só na média em 2026, como a chuva
#   e as temperaturas) e a D3 também a ETo (máxima anual isolada).
# v2 (03/11, 19h): a v1 pedia 3 anos por vez no D2 e o servidor respondeu 429 (pedidos simultâneos demais;
#   não é a cota mensal, que estava em 0,05%). Agora vai um ano por pedido e o 429 espera 1, 2 e 3 min.
# POR QUE EXISTE
#   A K17 e a K18 provaram que os códigos reproduzem os dados e acharam duas divergências (revisão do ERA5-Land
#   desde 2017; pixels B da V1.0). A K19 procura QUALQUER outra divergência ou limitação que a literatura clássica e
#   moderna saiba corrigir, em todo o período (1961 até a previsão), numa execução só, em sequência.
#
# PARTES (cada uma é independente; o resultado é salvo e um zip parcial é feito ao fim de cada parte)
#   D2  Controle de qualidade físico em TODOS os dias do SAB_V1 (1961 até a previsão), por ano e por classe de pixel:
#       Tmax < Tmin, chuva < 0, UR fora de 0-100, ET real > ETo, transpiração > ET real, radiação acima da de céu
#       claro (Rs > 1,1 Rso, FAO-56), limites de temperatura, vento, VPD, umidade do solo, escoamento.
#       Referências: WMO-No. 1269 (2021, controle de qualidade); testes do ETCCDI; Allen et al. (1998, FAO-56).
#   D3  Consistência espacial dos extremos de cada ano (máxima da Tmax, mínima da Tmin, máximas da chuva e da ETo): pixel que
#       foge demais da mediana dos 8 vizinhos (teste espacial clássico, como Hubbard & You 2005), com o local.
#   D4  Coerência entre variáveis: a ETo gravada x a ETo FAO-56 Penman-Monteith refeita com a função do próprio motor
#       V1.5 a partir de Tmax, Tmin, UR, vento e radiação gravados; o VPD gravado x o recalculado. Mostra a costura
#       entre a ETo do BR-DWGD (até 2025) e a do motor (2026).
#   D5  A emenda 2025 -> 2026 (chuva, Tmax, Tmin, UR, radiação e vento): em 2026 o dado vem do ERA5-Land corrigido
#       só na média (escala linear, V1.5). Em 150
#       pixels A, com o BR-DWGD como verdade, mede em 2024-2025 o ERA5 bruto, o método atual e o mapeamento de
#       quantis empírico (base do QDM), treinado em 2014-2023: viés, frequência de dias com chuva, percentis 95 e 99,
#       erro diário e mensal. Referências: Teutschbein & Seibert (2012); Cannon et al. (2015, QDM).
#   D6  Homogeneidade relativa das séries (jan-set de cada ano, 1961-2026, por estado, só pixels A): SAB menos
#       ERA5-Land bruto (e SAB / CHIRPS na chuva, 1981+), com os testes de Pettitt (1979) e SNHT (Alexandersson
#       1986); e a costura de 2026 (2026 x 1996-2025, escore z). Ref.: Peterson et al. (1998, homogeneização relativa).
#   D1  Reprodução das 16 bandas pelo código: um dia por ano de 1961 a 2025 (V1.0) e o dia 15 de cada mês de 2026
#       (V1.5), no Brasil inteiro, por classe de pixel. É a mais demorada; roda por último.
#
# REGRA: a K19 não aprova nem reprova o banco. Ela lista as divergências e as CANDIDATAS A CORREÇÃO (fim do log e
#   K19_CANDIDATAS.csv), cada uma com o tipo de correção permitido: na leitura (histórico travado) ou no motor
#   (2026 em diante). Nada é corrigido aqui.
# O QUE GRAVA: NADA no Earth Engine (trava de somente leitura). Só os resultados no Colab (validacao_K19_<data>.zip).
# ANTES DE RODAR: Ambiente de execução -> Reiniciar sessão. Sem K16/K17/K18 rodando. A K19 se recusa a começar se for
#   invadir a janela do motor (14h50-16h00 e 22h50-24h00) e pausa sozinha se uma parte cair numa janela.
# TEMPO: de 1h30 a 3h (o D2 confere os 24 mil dias inteiros; o D1 refaz 75 dias no Brasil todo). Pode deixar rodando.
# =========================================================================================
import ast
import hashlib
import math
import os
import shutil
import time
import traceback
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

PROJETO = 'clima-492922'
ASSET_SAB = f'projects/{PROJETO}/assets/SAB_V1'
ASSET_MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
ASSET_CLIMA = f'projects/{PROJETO}/assets/SICSB_1986_2025'
BRDWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
CHIRPS = 'UCSB-CHG/CHIRPS/DAILY'
GAUL1 = 'FAO/GAUL/2015/level1'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
X0, Y0, DX = -73.9000015258789, 5.400000095367432, 0.09999847412109375
REGIAO_AMPLA = [-75.0, -35.0, -28.0, 6.5]
ORDEM = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2', 'tsolo_C', 'tfolha_C',
         'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm', 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
CLASSES = {1: 'A', 2: 'B', 3: 'C', 4: 'borda'}
TOL_ABS, TOL_REL, MIN_IGUAIS = 1e-3, 1e-4, 0.99
FIM_HISTORICO = '2025-12-31'
ANO_FIM = 2026
SEMENTE = 17
# [04/11/2026] o GitHub começa o motor uns 40 min depois do agendado (15h07 → ~15h47, 21 min; 23h07 → ~23h49): janelas
#   até 16h30 e 00h30
JANELAS_MOTOR = [((5, 50), (8, 30)), ((14, 50), (16, 30)), ((22, 50), (24, 0)), ((0, 0), (0, 30))]   # [04/11] + manhã (V1.6)
DURACAO_ESTIMADA_MIN = 90
PARTES = ('D5', 'D1')              # partes desta execução (a K19b roda só D5 e D1)
# D2: testes de controle de qualidade (nome, descrição, tipo) -> 'duro' = fisicamente impossível
QC = [('tmax_lt_tmin', 'Tmax < Tmin', 'duro'), ('pr_neg', 'chuva < 0', 'duro'), ('rh_fora', 'UR fora de 0-100%', 'duro'),
      ('etr_gt_eto', 'ET real > ETo', 'duro'), ('tr_gt_etr', 'transpiração > ET real', 'duro'),
      ('etr_neg', 'ET real < 0', 'duro'), ('runoff_neg', 'escoamento < 0', 'duro'), ('vpd_neg', 'VPD < 0', 'duro'),
      ('u2_neg', 'vento < 0', 'duro'), ('rs_neg', 'radiação < 0', 'duro'),
      ('rs_gt_rso', 'radiação > 1,1 x céu claro (FAO-56)', 'suspeito'), ('tmax_gt_45', 'Tmax > 45 °C', 'suspeito'),
      ('tmin_lt_m10', 'Tmin < -10 °C', 'suspeito'), ('pr_gt_400', 'chuva > 400 mm/dia', 'suspeito'),
      ('u2_gt_15', 'vento > 15 m/s', 'suspeito'), ('tsolo_fora', 'T solo fora de -10 a 60 °C', 'suspeito'),
      ('tfolha_fora', 'T folha fora de -20 a 70 °C', 'suspeito'),
      ('solo_gt_09', 'umidade do solo bruta > 0,9 (V1.0; corrigida na leitura)', 'conhecido')]
LOTE_ANOS_D2 = 1                         # v2: um ano por pedido (3 anos juntos geravam 429)
# D3: limites do teste espacial (diferença para a mediana dos 8 vizinhos)
D3_TMAX, D3_TMIN, D3_PR_FATOR, D3_PR_MIN, D3_ETO = 4.0, 4.0, 3.0, 100.0, 3.0
# D5
N_PONTOS_D5 = 150
ANOS_TREINO_D5 = list(range(2014, 2024))
ANOS_TESTE_D5 = [2024, 2025]
VARS_D5 = ['pr', 'tmax', 'tmin', 'rh', 'rs', 'u2']
BANDAS_MATRIZ_D5 = ['pr', 'Tmax', 'Tmin', 'RH', 'Rs', 'u2']
CHUVA_DIA = 1.0                          # mm: dia com chuva (ETCCDI)
FATOR_MAX = 5.0                          # o mesmo teto do motor V1.5
# D6
MES_FIM_D6 = 9                           # janela jan-set (2026 provisório está completo até set)
ANOS_D6 = list(range(1961, ANO_FIM + 1))
P_LIMITE = 0.01
N_PERMUTACOES = 999
LOTE_ANOS_D6 = 1
# D1
PONTOS_D1 = {1: 200, 2: 100, 3: 100, 4: 50}     # v4: D1 nos pixels sorteados (C entra inteira)
LOTE_D1, LOTE_MINIMO_D1 = 200, 25
DIAS_D1 = [f'{a}-{(a % 12) + 1:02d}-15' for a in range(1961, 2026)]          # todos os meses aparecem ~5 vezes
SOMA_ERA5_A = {'et_real', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm'}
SOMA_ERA5_OUTRAS = SOMA_ERA5_A | {'pr_mm', 'et_potencial', 'rs'}

AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'validacao_K19_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K19.txt')
ACHADOS, CANDIDATAS = [], []

# ------------------------------------------------------------------ códigos embutidos, sem mudança
FONTE_V10 = r'''# =========================================================================================
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
'''
FONTE_V15 = r'''# >>> ARQUIVO PRONTO: motor V1.5 GRAVANDO (uso diário depois da etapa 5a aprovada). Cole inteiro, sem editar nada. <<<
# =========================================================================================
# TÍTULO: MOTOR MESTRE OPERACIONAL SAB V1.5 - SCRIPT 1 (CONTA CLIMA)
# RESUMO DA FUNÇÃO: Autenticação, processamento e tarefas isoladas para clima-492922
# MUDANÇAS V4 (20/10/2026) - motor V1.5 (sobre a V1.4). Trechos marcados com [V4 <item>]:
#   - [V4 B1/M05-08] Rodadas GFS: só 00Z (creation_time múltiplo de 86.400.000 ms). Completa =
#     as 208 saídas de 1 a 384 h (120 horárias + 40 de 3 h até 240 h + 48 de 3 h até 384 h), sem a
#     hora 0, contadas numa só consulta para todas as rodadas da janela. Referência = a 00Z completa
#     mais recente; sem nenhuma completa, os dias GFS não são processados nesta execução. Dias
#     passados usam a rodada 00Z do próprio dia (ou, se ela estiver incompleta, a 00Z completa
#     anterior mais recente, M05-09).
#   - [V4 B1-horizonte/M05-28] Fim da cadeia = min(hoje + 15, dia da referência + 15). O último
#     dia é o prazo 16 (horas 361-384), completo com a rodada 00Z e calibrado com a faixa L11a15.
#   - [V4 B6/M05-10/M05-11] Dia incompleto: chuva, radiação, ETo, ET real e transpiração mascaradas;
#     o balde usa a chuva escalada por 4/n blocos (0 sem blocos); fim da média simples da radiação;
#     saídas duplicadas descartadas (distinct) e contagem exata (eq). [V4 M05-09] dias incompletos
#     ou com falha são refeitos quando a rodada certa está completa.
#   - [V4 B3/M05-07] Matriz GFS: um só getInfo confere as 48 bandas de média e versao_matriz = 'V2.1'.
#   - [V4 B4/M05-05] CRIT_SOLO_BRASIL = 2.0 (±2%, como o roteiro e o D13).
#   - [V4 B5/M05-04] CONVERTER_EM_DEFINITIVO = False: dias depois de DATA_LIMITE_PROTECAO não viram
#     'definitiva' sozinhos quando o BR-DWGD passar a cobri-los; aviso no início.
#   - [V4 C1/M05-01/M05-02] Rota definitiva: BR-DWGD primeiro e ERA5 só onde ele falta; máscara que
#     exclui -32768 e o dummy -99999; ETo, radiação e vento do BR-DWGD limitados a >= 0.
#   - [V4 C2/M05-03] Máscara canônica: todos os dias novos com a cobertura de SAB_2025_12_31 (pr_mm),
#     por updateMask em finalizar(), no lugar do .clip(poligonoBrasil) (a máscara já contém o recorte).
#   - [V4 C4/M03-15] Calibração só da rota GFS: chuva (m_sicsb + 0,1)/(m_gfs + 0,1) com teto FATOR_MAX;
#     vento com fator entre 0,5 e 2,0 (a radiação também, até a revisão K9A; ver abaixo). A rota ERA5 não muda.
#   - [V4 B8/M05-17] Propriedades novas: Confianca_Prazo, fonte, janela_chuva_utc, matriz_gfs.
#   - [V4 M05-22] VERSAO_ALGORITMO = 'V1.5' e aceita nos definitivos; aviso de opções inertes com a trava.
#   - [V4 B2/M05-06] PRÉVIA 6: rota GFS calculada em memória no modo simulação (sem exportar nada).
#   - [V4.1 K7] Tmax e Tmin dos dias GFS: constante METODO_TEMP_GFS ('variancia', o padrão desde a revisão de
#     20/10/2026 validada pela auditoria K8, ou 'aditivo'; escala de variância com os desvios da matriz V2.1). A PRÉVIA 6 calcula os dois e diz qual passa no recorde
#     do INMET e na emenda com o ERA5; o motor confere também as 16 bandas de desvio da Tmax e da Tmin.
#     Propriedade nova nos dias GFS: metodo_temp_gfs.
#   - [V4.1 revisão] A PRÉVIA 6 inclui o dia de prazo 8 (faixa L6a10); o cálculo do outro método não derruba
#     o critério obrigatório; sem a emenda testada, a decisão manda rodar de novo; um dia gravado com outro
#     método é refeito na próxima execução (precisa_refazer_gfs lê metodo_temp_gfs).
#   - [K9A, 20/10/2026] Umidade relativa e radiação dos dias GFS pela escala de variância (constante
#     METODO_UR_RS_GFS = 'variancia'; 'original' volta à UR aditiva e à radiação com fator [0,5; 2]).
#     Validação K9A (GFS v16, treino 2021-2024, teste em 2025 inteiro, 300 pontos, 438 mil previsões; IC 95%
#     por bootstrap de dias): MAE da UR 6,65 -> 4,98 (-25%), da radiação 3,51 -> 3,03 MJ/m²/dia (-14%) e da
#     ETo 0,704 -> 0,611 mm/dia (-13%); a variância também ganhou em cada um dos 5 anos do v16 (cada ano
#     testado com o treino nos outros). O motor confere as 16 bandas de desvio da UR e da radiação na
#     matriz; propriedade nova nos dias GFS: metodo_ur_rs_gfs; um dia gravado com outro método é refeito.
#   - [K11, 22/10/2026] Teto da razão dos desvios da Tmax e da Tmin nos prazos de 6 dias em diante
#     (faixas L6a10 e L11a15): RAZAO_DESVIO_MAX_LONGO = 1.0 (nos prazos 1 a 5 continua RAZAO_DESVIO_MAX = 2.0;
#     a UR e a radiação não mudam). Motivo: em 22/10 a previsão de 26/10 em Casa Nova-BA (prazo 6) saiu
#     com Tmax 45,24 °C (GFS bruto 35,41 °C; razão 1,98). Validação K11 (GFS v16, teste 2025 e cada ano de
#     2021 a 2025; regra fixada antes de rodar): nos prazos 8 e 13, MAE da Tmax 1,891 -> 1,879 (-0,6%) e da
#     Tmin 1,272 -> 1,205 (-5,3%), menos previsões além do limite físico do ponto (Tmax 0,171% -> 0,163%;
#     Tmin 0,303% -> 0,151%) e geada prevista mais perto da observada (0,131% -> 0,088%; obs 0,108%); ganhou
#     nos 5 anos. Propriedade nova nos dias GFS: teto_razao_temp_gfs (dia sem ela conta como 2.0); um dia
#     gravado com outro teto é refeito.
#   - [V4 M05-19] Promoção do TMP só se a versão do algoritmo for a atual; trava também em exportar().
#   - Prévia gravada em previa_v15.csv (antes previa_v14.csv).
#   - Fora do escopo V1.5 (não feitos): interpolação mensal (M05-12), janela 12-12 UTC (M05-16/V3),
#     ERA5 horário, constantes FAO-56 na equação de Magnus (M05-23) e qualquer outra mudança na rota ERA5.
# ATUALIZAÇÃO V1.4 (sobre a V1.3):
#   - Umidade do solo do ERA5 (0-7 cm e 0-100 cm) com reamostragem bilinear, igual à matriz
#     SICSB_SOLO_2015_2025 que calcula o fator SMAP/ERA5. Antes o dia usava vizinho mais
#     próximo e a matriz usava bilinear: o fator era aplicado sobre um campo diferente do que
#     o gerou. Dias definitivos (até 2025) não mudam; a partir dos provisórios há uma pequena
#     descontinuidade conhecida nas duas bandas de umidade.
#   - GFS: reamostragem bilinear em cada imagem ANTES de compor. O .resample() sobre a
#     composição (V1.3) não vale para composições no Earth Engine. Reprojeção final sem resample.
#   - GFS calibrado pela matriz SICSB_MATRIZ_GFS_V2, com faixas de prazo (1, 2-5, 6-10 e
#     11-15 dias de antecedência). Antes a calibração do 1º dia valia para os 15 dias.
#   - Prévia ajustada à V1.4: nos dias provisórios, só as duas bandas de umidade devem mudar.
#   - Radiação do GFS pela média dos blocos de 6 h (horas múltiplas de 6), como a chuva. Auditoria
#     de 20/10/2026 (item F4): o fluxo de onda curta do GFS é a média acumulada desde o início do
#     bloco de 6 h, e a média simples das saídas superestimava a radiação diária em 3% a 11%.
# ATUALIZAÇÃO V1.3 (sobre a V1.2):
#   - ETo dos dias provisórios (rota ERA5) calculada por Penman-Monteith FAO-56 com a
#     meteorologia calibrada, pela mesma função que a rota GFS já usava. Antes era a evaporação
#     potencial do ECMWF calibrada, que no teste E4 (953 pontos, 2016-2025) errou 12,7% ao ano
#     contra 4,0% do Penman-Monteith. O BR-DWGD, base dos dias definitivos, também é FAO-56.
#   - Dias provisórios gravados por versões anteriores do algoritmo são recalculados
#   - A janela operacional cobre todos os dias provisórios (desde o dia seguinte ao último BR-DWGD).
#     Como a fila do Earth Engine atende por ordem de envio, só os 15 dias ERA5 que servem de base
#     à previsão entram antes da cadeia GFS; os demais provisórios são enviados depois dela
#   - Modo simulação com prévia: compara as 16 bandas e a coerência física (ET real <= ETo etc.)
#     do que o painel mostra hoje com o que a V1.3 gravaria, por região, e avalia o resultado
#     contra critérios definidos antes de rodar. As médias
#     regionais saem de uma só passada sobre a grade (estados pintados, sem unir polígonos) e,
#     se o Earth Engine recusar por memória ou tempo, o Brasil é dividido em 4 e depois 16 partes
#   - Dias definitivos (até o último dia do BR-DWGD) não são alterados
# ATUALIZAÇÃO V1.2 (sobre a V1.1):
#   - Calibração multiplicativa volta à fórmula da V1.0 (alvo / max(modelo, 1e-3)), agora com
#     teto no fator: onde o fator original já era menor que o teto, o resultado é idêntico à V1.0
#   - Umidade do solo limitada ao teto físico (média SMAP + 3 desvios, no máximo 0.9 m³/m³)
#   - Patch do acervo V1.0: corrige SÓ umidade do solo e escoamento; demais bandas são copiadas
#     do asset existente, sem recálculo
#   - GFS: Tmax/Tmin pela temperatura horária (mesma variável da matriz GFS), amplitude térmica
#     mínima, ET real ancorada no comportamento ERA5 recente de cada pixel, balde com capacidade
#     por pixel
#   - Recorte volta ao polígono exato do GAUL (igual à V1.0)
# ATUALIZAÇÃO V1.1:
#   - Janela diária do GFS corrigida para (00Z, 24Z] (acumulados terminam no forecast_time)
#   - Rodada GFS escolhida no cliente, gravada no asset e usada para decidir atualização
#   - Banda de transpiração mantida (troca conhecida de bandas do ERA5-Land documentada)
#   - Calibração multiplicativa com piso físico e fator limitado
#   - Escrita atômica (exporta em coleção temporária e promove após conclusão)
#   - Janela operacional (recente + previsão) processada antes do passivo histórico
#   - Sem ano fixo no código; falhas de inventário interrompem a execução
#   - Ordem de bandas canônica em todas as rotas
# =========================================================================================

import ee
import math
import re
import time
from datetime import datetime, timezone, timedelta

import pandas as pd

# =========================================================================
# 1. CONFIGURAÇÃO
# =========================================================================
PROJECT_ID_ATIVO = 'clima-492922'
ASSET_DESTINO = f'projects/{PROJECT_ID_ATIVO}/assets/SAB_V1'
ASSET_TEMP = f'projects/{PROJECT_ID_ATIVO}/assets/SAB_V1_TMP'
SUFIXO_TASK = 'C1'

ASSET_CLIMATOLOGIA = 'projects/clima-492922/assets/SICSB_1986_2025'
ASSET_DESTINO_MATRIZ_GFS = 'projects/clima-492922/assets/SICSB_MATRIZ_GFS_V2'
ASSET_SOLO = 'projects/clima-492922/assets/SICSB_SOLO_2015_2025'

VERSAO_ALGORITMO = 'V1.5'        # [V4] antes 'V1.4'
VERSAO_PATCH = 'V1.0-P12'        # dia da V1.0 com umidade do solo e escoamento corrigidos
# True: modo simulação. Lê o acervo e informa o que seria feito, sem exportar,
# apagar, renomear ou criar nenhum asset. Rode assim antes da primeira execução real.
SIMULAR = False
# True (só vale no modo simulação): calcula, sem gravar nada, uma prévia que compara o que o
# painel mostra hoje nos dias provisórios com o que a V1.5 gravaria, e diz se o resultado
# atende aos critérios de aprovação da seção 7. [V4 B2] Inclui a PRÉVIA 6 (rota GFS em memória).
PREVIA = True
PREVIA_DIAS_DO_MES = (15,)       # dias de cada mês provisório usados na prévia, ex.: (5, 15, 25)
# True: umidade do solo do ERA5 com reamostragem bilinear, igual à matriz SICSB_SOLO_2015_2025.
# False: vizinho mais próximo, como todo o histórico 1961-2025 foi gravado. Decida pela prévia.
SOLO_BILINEAR = True
# Algoritmos aceitos nos dias definitivos: esses dias nunca são recalculados por mudança de versão
ALGORITMOS_DEFINITIVOS_VALIDOS = ('V1.0', VERSAO_PATCH, 'V1.2', 'V1.3', 'V1.4', 'V1.5')   # [V4 M05-22]
# [V4 M05-22] Sem a versão atual na tupla, os definitivos dela seriam reexportados a cada execução.
assert VERSAO_ALGORITMO in ALGORITMOS_DEFINITIVOS_VALIDOS, "Inclua VERSAO_ALGORITMO em ALGORITMOS_DEFINITIVOS_VALIDOS."
# False (decisão atual): o histórico V1.0 NÃO é regravado; a correção de umidade do solo e
# escoamento desses dias é feita na leitura, pelo Painel SAB (corrigirSoloEscoamentoV10).
# True: aplica o patch no próprio banco (várias execuções, respeitando a fila).
APLICAR_PATCH_SOLO = False
# True: recalcula do zero os dias de versões anteriores (não necessário; mantenha False).
REPROCESSAR_VERSAO_ANTIGA = False
# TRAVA DO HISTÓRICO. True: nenhum dia até DATA_LIMITE_PROTECAO é exportado, recalculado, criado
# ou substituído, em nenhuma hipótese (nem por versão antiga, nem por dia ausente, nem por sobra
# na coleção temporária). Dias históricos que precisariam de alguma ação são apenas listados no
# relatório "PROTEGIDOS". Só mude para False por decisão explícita de reprocessar o histórico.
PROTEGER_HISTORICO = True
DATA_LIMITE_PROTECAO = '2025-12-31'
# [V4 B5/M05-04] False (decisão atual): quando o BR-DWGD passar a cobrir dias depois de
# DATA_LIMITE_PROTECAO, esses dias continuam provisórios (rota ERA5) e NUNCA viram 'definitiva'
# sozinhos; o início da execução avisa quantos aguardam decisão. True: converte pela rota definitiva.
CONVERTER_EM_DEFINITIVO = False

# [V4 M05-28] Hoje + 15 dias = prazo 16 (horas 361-384 da rodada 00Z de hoje). Com rodada 00Z esse
# dia fica completo (8 saídas e 4 blocos de chuva). A matriz GFS não tem faixa para o prazo 16:
# ele usa a calibração da faixa L11a15 (extrapolação). O fim efetivo da cadeia é
# min(hoje + 15, dia da rodada de referência + 15): ver fim_horizonte().
HORIZONTE_DIAS = 15
JANELA_OPERACIONAL_DIAS = 90     # dias recentes processados com prioridade
DIAS_BUSCA_RODADAS = 12          # quantos dias de rodadas GFS considerar
# [V4 B1] Rodada GFS completa: todas as saídas de 1 a 384 h (a hora 0 não conta): 120 horárias
# (1-120 h), 40 de 3 em 3 h (123-240 h) e 48 de 3 em 3 h (243-384 h) = 208. Com a hora 0, o acervo
# tem 209 imagens por rodada (auditoria F2). A V1.4 aceitava >= 198 imagens contando a hora 0.
MS_DIA = 86400000
PRAZO_MAX_GFS = 16               # 384 h / 24
HORAS_RODADA_COMPLETA = [h for h in range(1, 24 * PRAZO_MAX_GFS + 1) if h <= 120 or h % 3 == 0]
N_SAIDAS_RODADA = len(HORAS_RODADA_COMPLETA)
assert N_SAIDAS_RODADA == 208
LIMITE_TAREFAS_MAX = 3000
RESERVA_OPERACIONAL = 100        # vagas que o histórico nunca consome
INTERVALO_POLL_S = 30
TIMEOUT_TAREFA_MIN = 120

DATA_INICIO_P1 = '1991-01-01'
DATA_INICIO_P2 = '1961-01-01'
DATA_FIM_P2 = '1990-12-31'

# Calibração multiplicativa: fator = alvo / max(modelo, 1e-3) (fórmula da V1.0), limitado
# a FATOR_MAX. Só os pixels cujo fator original passava do teto mudam.
FATOR_MAX = 5.0
# [V4 C4/M03-15] Calibração SÓ da rota GFS (a rota ERA5 continua com calib_multiplicativa acima).
# Chuva: fator = (m_sicsb + K_CHUVA_MM)/(m_gfs + K_CHUVA_MM), com teto FATOR_MAX. Na seca a média do
# GFS fica perto de zero e o fator explodia: na matriz GFS V1, julho, p95 = 13,3 e p99 = 59,2
# (auditoria J4). Vento e radiação: fator limitado a [FATOR_MIN_UV_RS, FATOR_MAX_UV_RS]
# (fator 5 é fisicamente impossível nessas variáveis). Muda só os dias GFS.
K_CHUVA_MM = 0.1                 # mm/dia
FATOR_MIN_UV_RS = 0.5
FATOR_MAX_UV_RS = 2.0
# [V4.1 K7] Correção da Tmax e da Tmin SÓ nos dias GFS:
#   'aditivo'   (V1.5 original): x + (m_sicsb - m_gfs), a mesma correção de média da V1.0.
#   'variancia' (escala de variância; PADRÃO desde a revisão de 20/10/2026, auditoria K8): m_sicsb +
#               (x - m_gfs) x (s_sicsb / s_gfs), com a razão dos desvios limitada a [RAZAO_DESVIO_MIN,
#               RAZAO_DESVIO_MAX]. Corrige a média e também a amplitude das anomalias.
#   K7 (set-nov/2025): a correção aditiva deixa o máximo diário nacional de 2,6 a 3,5 °C acima do BR-DWGD.
#   K8 (validação fora da amostra: treino 2021-2024, teste 2025, 300 pontos, 146.400 previsões), refeita na
#   revisão final com as estatísticas de treino mês a mês, como a matriz V2.1 calcula:
#     Tmax: MAE 1,58 °C (variância) x 1,99 °C (aditiva), diferença -0,41 °C (IC 95% -0,45 a -0,37; 122 dias);
#           dias acima de 35 °C 12,4% x 17,8% (observado 11,6%); acima de 40 °C 0,08% x 0,28% (observado 0,10%).
#     Tmin: empate prático, MAE 1,085 x 1,070 °C (+0,015 °C); noites abaixo do P10 9,2% x 9,1% (observado 9,3%).
# A PRÉVIA 6 continua mostrando os dois métodos lado a lado (só informação).
METODO_TEMP_GFS = 'variancia'
RAZAO_DESVIO_MIN = 0.5
RAZAO_DESVIO_MAX = 2.0
# [K11, 22/10/2026] Nos prazos de 6 dias em diante a Tmax e a Tmin usam a razão dos desvios limitada a
# [RAZAO_DESVIO_MIN, RAZAO_DESVIO_MAX_LONGO]: o GFS varia pouco de um dia para outro nesses prazos porque perde
# habilidade, e inflar a anomalia criava extremos (Casa Nova-BA, 26/10/2026: 45,24 °C com o GFS em 35,41 °C).
# Validação K11 aprovada na Tmax e na Tmin (ver o cabeçalho). Só a Tmax e a Tmin; UR e radiação não mudam.
RAZAO_DESVIO_MAX_LONGO = 1.0
FAIXAS_LONGAS = ('L6a10', 'L11a15')
assert METODO_TEMP_GFS in ('aditivo', 'variancia'), "METODO_TEMP_GFS deve ser 'aditivo' ou 'variancia'"
# [K9A] Correção da umidade relativa e da radiação SÓ nos dias GFS:
#   'original'  (V1.5 até a revisão K9A): UR aditiva, x + (m_sicsb - m_gfs), limitada a [0, 100]; radiação com
#               o fator m_sicsb / m_gfs limitado a [FATOR_MIN_UV_RS, FATOR_MAX_UV_RS].
#   'variancia' (PADRÃO desde a revisão K9A, 20/10/2026): m_sicsb + (x - m_gfs) x (s_sicsb / s_gfs), com a
#               razão dos desvios limitada a [RAZAO_DESVIO_MIN, RAZAO_DESVIO_MAX]; UR limitada a [0, 100] e
#               radiação >= 0. Usa as bandas de desvio que a matriz V2.1 já tem (contrato de 100 bandas).
#   K9A (2025, fora do treino): MAE da UR 6,65 -> 4,98 (-25%), da radiação 3,51 -> 3,03 (-14%), da ETo
#   0,704 -> 0,611 mm/dia (-13%). Limitação registrada: a variância prevê menos dias muito secos (UR < 30%:
#   0,09% x 0,18% observado) e menos dias de ETo > 6 mm (3,3% x 4,3% observado). O vento continua com o fator.
METODO_UR_RS_GFS = 'variancia'
assert METODO_UR_RS_GFS in ('original', 'variancia'), "METODO_UR_RS_GFS deve ser 'original' ou 'variancia'"
# Teto físico da umidade do solo: média SMAP + SIGMAS desvios do mês, nunca acima de 0.9
UMIDADE_MAX_FISICA = 0.9
SIGMAS_TETO_UMIDADE = 3.0

# Balde de solo do GFS. A capacidade efetiva de cada pixel é o maior valor entre estas
# constantes e a umidade do último dia ERA5 (evita corte artificial na transição).
SW100_MAX_MM = 400.0
SW100_CC_MM = 330.0
SW5_MAX_MM = 25.0
DIAS_REF_ET = 15          # dias ERA5 usados para ancorar ET real e transpiração no GFS
AMPLITUDE_MIN_C = 1.0     # amplitude térmica mínima nos dias GFS

ORDEM_BANDAS = [
    'pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd',
    'rs', 'u2', 'tsolo_C', 'tfolha_C', 'transpiracao_mm',
    'runoff_sup_mm', 'runoff_sub_mm',
    'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3',
]
VERSOES_GFS = ('provisoria_gfs', 'provisoria_gfs_incompleta', 'falha_latencia_gfs')
# [V4 B6/M05-10] Bandas mascaradas no dia 'provisoria_gfs_incompleta' (dependem da chuva ou da radiação)
BANDAS_MASCARADAS_INCOMPLETO = ['pr_mm', 'rs', 'et_potencial', 'et_real', 'transpiracao_mm']
# [V4 B3/M05-07] Matriz GFS exigida pelo motor (contrato SPEC_V4)
VERSAO_MATRIZ_GFS = 'V2.1'
VARS_MATRIZ_GFS = ('pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs')
# [V4 B8/M05-17] Propriedades gravadas (contrato SPEC_V4)
FONTE_GFS = 'NOAA/GFS0P25 (rodada 00Z)'
FONTE_ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
FONTE_DEFINITIVA = 'BR-DWGD (ERA5 só onde falta)'
JANELA_CHUVA_00_24 = '00-24'
JANELA_CHUVA_12_12 = '12-12 (12 UTC D-1 a 12 UTC D)'
MATRIZ_GFS_ROTULO = f'SICSB_MATRIZ_GFS_V2 {VERSAO_MATRIZ_GFS}'
# [V4 C2/M05-03] Dia do histórico cuja máscara (banda pr_mm) é a cobertura canônica de todos os dias novos
DIA_MASCARA_CANONICA = '2025-12-31'
ARQUIVO_PREVIA = 'previa_v15.csv'   # [V4] antes previa_v14.csv
ESTADOS_ATIVOS = ('READY', 'RUNNING', 'SUBMITTED', 'PENDING')
ESTADOS_FINAIS = ('COMPLETED', 'FAILED', 'CANCELLED')

fuso_br = timezone(timedelta(hours=-3))
data_extracao_local = datetime.now(fuso_br).strftime('%Y-%m-%d %H:%M:%S')
data_hoje_dt = datetime.now(timezone.utc)
data_hoje_str = data_hoje_dt.strftime('%Y-%m-%d')
data_fim_processo = (data_hoje_dt + timedelta(days=HORIZONTE_DIAS)).strftime('%Y-%m-%d')
# [V4 B1-horizonte] executar_cadeia_gfs() reduz data_fim_processo para min(hoje + 15, referência + 15)

print(f"🔄 Iniciando SAB {VERSAO_ALGORITMO} no projeto: {PROJECT_ID_ATIVO}...")
print(f"🕒 Timestamp de Operação (Local/BRT): {data_extracao_local}\n")

try:
    ee.Initialize(project=PROJECT_ID_ATIVO)
except Exception:
    print("🔗 Autenticação necessária:")
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID_ATIVO)

# [Correção 20/10/2026, 23h30] Trava de somente leitura herdada de outro script na MESMA sessão do Colab: os scripts
# de simulação e de auditoria (01a, 07, 08 e as validações) bloqueiam as funções de escrita do Earth Engine, e o
# bloqueio continua valendo nas células seguintes da sessão. Um script que grava precisa de uma sessão nova.
def _escrita_bloqueada_na_sessao():
    _funcs = [getattr(ee.batch.Task, 'start', None)] + [getattr(ee.data, _n, None) for _n in (
        'createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'setAssetAcl', 'startProcessing', 'exportImage')]
    return any(getattr(_f, '__name__', '') in ('_bloqueado', '_bloq') for _f in _funcs)


MSG_SESSAO_TRAVADA = ('Esta sessão do Colab ainda tem a trava de somente leitura de um script rodado antes nela '
                      '(por exemplo, o 01a, o 07 ou o 08). Nada foi gravado. No menu do Colab, clique em '
                      '"Ambiente de execução" e depois em "Reiniciar sessão" (confirme), e rode este arquivo de novo.')

if not SIMULAR and _escrita_bloqueada_na_sessao():
    raise RuntimeError('❌ ' + MSG_SESSAO_TRAVADA)

# =========================================================================
# 2. OBJETOS GLOBAIS
# =========================================================================
_gaul_br = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
limitesRegiao = _gaul_br.geometry().bounds()
poligonoBrasil = _gaul_br.geometry()   # polígono exato, igual à V1.0 (garante bordas idênticas)
# [V4 C2/M05-03] finalizar() não recorta mais por poligonoBrasil: usa MASCARA_SAB, que já contém esse
# recorte (o dia de referência foi gravado com .clip(poligonoBrasil)). A variável fica para consulta.
crsNativo = 'EPSG:4326'
transformNativo = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
elevacao_br = ee.Image('USGS/SRTMGL1_003').clip(limitesRegiao)
colChuvaGeral = ee.ImageCollection('projects/ee-alexandrexavier/assets/BR-DWGD')
colecao_era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
COL_GFS = 'NOAA/GFS0P25'

def ms_para_data(ms):
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime('%Y-%m-%d')

def data_para_ms(d_str):
    return int(datetime.strptime(d_str, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp() * 1000)

def somar_dias(d_str, n):
    return (datetime.strptime(d_str, '%Y-%m-%d') + timedelta(days=n)).strftime('%Y-%m-%d')

def intervalo_datas(ini, fim):
    if ini > fim:
        return []
    return pd.date_range(start=ini, end=fim).strftime('%Y-%m-%d').tolist()

def id_dia(d_str):
    return 'SAB_' + d_str.replace('-', '_')

def desc_dia(d_str):
    return 'SAB_M_' + d_str.replace('-', '_') + '_' + SUFIXO_TASK

def desc_de_nome(nome):
    return nome.replace('SAB_', 'SAB_M_', 1) + '_' + SUFIXO_TASK

# [V4 C2/M05-03] Máscara canônica, lida uma vez: a cobertura da banda pr_mm do último dia do histórico.
# Todas as rotas passam a gravar exatamente essa cobertura (D10). A existência do asset é conferida
# no início da orquestração.
MASCARA_SAB = ee.Image(f'{ASSET_DESTINO}/{id_dia(DIA_MASCARA_CANONICA)}').select('pr_mm').mask()

def ultimo_dia_continuo(datas):
    """[Correção 21/10/2026, 18h] datas: conjunto de dias 'AAAA-MM-DD' com imagem ERA5-Land. Devolve (último dia
    sem lacuna desde o primeiro dia do conjunto, lista dos dias que faltam entre o primeiro e o último publicado)."""
    ordenadas = sorted(datas)
    faltando = [x for x in intervalo_datas(ordenadas[0], ordenadas[-1]) if x not in datas]
    if not faltando:
        return ordenadas[-1], []
    return somar_dias(faltando[0], -1), faltando

def limite_definitivo(ultima_brd, converter, data_limite):
    """[V4 B5/M05-04] Último dia que pode ser gravado (ou convertido) como 'definitiva'.
    Com converter=False, nenhum dia depois de data_limite vira definitivo, mesmo coberto pelo BR-DWGD."""
    return ultima_brd if converter else min(ultima_brd, data_limite)

def dias_aguardando_decisao(ultima_brd, data_limite):
    """[V4 B5/M05-04] Quantos dias depois de data_limite o BR-DWGD já cobre."""
    if ultima_brd <= data_limite:
        return 0
    return (datetime.strptime(ultima_brd, '%Y-%m-%d') - datetime.strptime(data_limite, '%Y-%m-%d')).days

# Últimas datas disponíveis (falha aqui interrompe: decidir rota sem essa informação é inseguro)
_ini_busca = ee.Date(data_hoje_dt.strftime('%Y-%m-%d')).advance(-150, 'day')
# [Correção 21/10/2026, 18h] O ERA5-Land DAILY_AGGR do Earth Engine pode publicar um dia antes dos anteriores
# (em 21/10/2026 havia 2026-10-11 sem 2026-10-09 e 2026-10-10). Com a data MÁXIMA, os dias da lacuna iam para a
# rota ERA5 sem imagem e a tarefa falhava ("Image.select: Parameter 'input' is required and may not be null").
# Agora a rota ERA5 vai só até o último dia CONTÍNUO (sem lacuna); da lacuna em diante, os dias seguem pela
# previsão GFS (rodada 00Z do próprio dia) até o ERA5 preencher a lacuna, quando a execução seguinte os refaz
# como ERA5 (o mesmo caminho que já transforma dias de previsão em dias ERA5).
_lista_era5 = colecao_era5.filterDate(_ini_busca, ee.Date(data_hoje_str).advance(1, 'day')) \
    .aggregate_array('system:time_start').getInfo()
if not _lista_era5:
    raise RuntimeError("Não foi possível determinar a última data do ERA5-Land.")
ultima_data_era5_publicada = ms_para_data(max(_lista_era5))
ultima_data_era5, dias_faltando_era5 = ultimo_dia_continuo({ms_para_data(t) for t in _lista_era5})
if dias_faltando_era5:
    print(f"⚠️ ERA5-Land sem {len(dias_faltando_era5)} dia(s) no Earth Engine antes do último publicado "
          f"({ultima_data_era5_publicada}): {dias_faltando_era5[:10]}. Os dias ERA5 vão até {ultima_data_era5} "
          f"(último sem lacuna); os seguintes seguem pela previsão GFS até a lacuna ser preenchida.")

_ms_brd = colChuvaGeral.aggregate_max('system:time_start').getInfo()
if _ms_brd is None:
    raise RuntimeError("Não foi possível determinar a última data do BR-DWGD.")
ultima_data_brd = ms_para_data(_ms_brd)

print(f"📡 Última data ERA5-Land: {ultima_data_era5}"
      + (f" (contínua; publicada até {ultima_data_era5_publicada})" if dias_faltando_era5 else "")
      + f" | Última data BR-DWGD: {ultima_data_brd}")

# [V4 B5/M05-04] Limite da rota definitiva, usado em status_dia(), na escolha da rota e na janela
limite_def = limite_definitivo(ultima_data_brd, CONVERTER_EM_DEFINITIVO, DATA_LIMITE_PROTECAO)
_n_aguardando = dias_aguardando_decisao(ultima_data_brd, DATA_LIMITE_PROTECAO)
if _n_aguardando and not CONVERTER_EM_DEFINITIVO:
    print(f"⏸️ BR-DWGD já cobre até {ultima_data_brd}: {_n_aguardando} dias aguardam decisão "
          f"(CONVERTER_EM_DEFINITIVO = False: seguem provisórios, rota ERA5).")
elif _n_aguardando:
    print(f"🔁 CONVERTER_EM_DEFINITIVO = True: {_n_aguardando} dias depois de {DATA_LIMITE_PROTECAO} "
          f"serão gravados como definitivos (BR-DWGD até {ultima_data_brd}).")

# =========================================================================
# 3. UTILITÁRIOS DE ASSET E TAREFA
# =========================================================================
def asset_existe(path):
    try:
        ee.data.getAsset(path)
        return True
    except ee.EEException:
        return False

def propriedades_asset(path):
    try:
        return ee.data.getAsset(path).get('properties', {}) or {}
    except ee.EEException:
        return None

def info_de_propriedades(p):
    if p is None:
        return None
    rodada = p.get('rodada_gfs_ms', 0)
    return {
        'versao': p.get('versao', 'definitiva'),
        'alg': p.get('versao_algoritmo', 'V1.0'),
        'rodada': int(float(rodada)) if rodada is not None else 0,
        'metodo': p.get('metodo_temp_gfs', 'aditivo'),          # [V4.1 revisão V41-08]
        'metodo_ur_rs': p.get('metodo_ur_rs_gfs', 'original'),  # [K9A]
        'teto_razao': float(p.get('teto_razao_temp_gfs', 2.0)),  # [K11] dia sem a propriedade: 2.0
    }

def garantir_colecao(path):
    if not asset_existe(path):
        if SIMULAR:
            print(f"🧪 [SIMULAÇÃO] Criaria a coleção: {path}")
            return
        ee.data.createAsset({'type': 'IMAGE_COLLECTION'}, path)
        print(f"📁 Coleção criada: {path}")

def listar_nomes(parent):
    nomes, token = [], None
    while True:
        params = {'parent': parent, 'pageSize': 1000}
        if token:
            params['pageToken'] = token
        resp = ee.data.listAssets(params)
        for a in resp.get('assets', []):
            caminho = a.get('id') or a.get('name')
            nomes.append(caminho.split('/')[-1])
        token = resp.get('nextPageToken')
        if not token:
            break
    return nomes

def listar_tarefas_ativas():
    """Retorna {descricao: id} de TODAS as tarefas ativas (a fila de 3000 é por usuário)."""
    ativas = {}
    for t in ee.data.getTaskList():
        if t.get('state') in ESTADOS_ATIVOS:
            ativas[t.get('description', '')] = t.get('id')
    return ativas

def versao_tmp_aceita(alg):
    """[V4 M05-19] Versões que podem ser promovidas da coleção temporária: a atual e a do patch."""
    return alg in (VERSAO_ALGORITMO, VERSAO_PATCH)

def promover_tmp(nome):
    """Substitui o asset definitivo pelo temporário já concluído.
    [V4 M05-19] Não é atômico (apaga e renomeia). Antes de promover: respeita a trava do histórico e
    confere a versão do algoritmo do TMP; uma sobra de versão antiga é apagada e o dia é refeito
    pelo fluxo normal (o asset final continua com a versão antiga ou ausente)."""
    tmp = f'{ASSET_TEMP}/{nome}'
    final = f'{ASSET_DESTINO}/{nome}'
    if dia_protegido(nome):                                    # [V4 M05-19]
        return False
    p = propriedades_asset(tmp)                                # [V4 M05-19] None = não existe
    if p is None:
        return False
    if not versao_tmp_aceita(p.get('versao_algoritmo')):       # [V4 M05-19]
        print(f"🧹 {nome}: sobra na coleção temporária com versão {p.get('versao_algoritmo')} "
              f"(atual {VERSAO_ALGORITMO}); apagada sem promover, o dia será refeito.")
        ee.data.deleteAsset(tmp)
        return False
    if asset_existe(final):
        ee.data.deleteAsset(final)
    ee.data.renameAsset(tmp, final)
    return True

_NOME_DIA = re.compile(r'^SAB_\d{4}_\d{2}_\d{2}$')

def data_de_nome(nome):
    """'SAB_2026_01_05' -> '2026-01-05'."""
    return nome[4:].replace('_', '-')

def dia_protegido(nome):
    """Com a trava ligada, protege todo dia até DATA_LIMITE_PROTECAO e todo nome fora do padrão."""
    if not PROTEGER_HISTORICO:
        return False
    return not (_NOME_DIA.match(nome) and data_de_nome(nome) > DATA_LIMITE_PROTECAO)

def finalizar_trocas_pendentes(tarefas_ativas):
    if not asset_existe(ASSET_TEMP):
        return
    promovidos, bloqueados, seriam, seriam_apagados = 0, [], [], []   # [V4 M05-19]
    for nome in listar_nomes(ASSET_TEMP):
        if desc_de_nome(nome) in tarefas_ativas:
            continue
        if dia_protegido(nome):
            bloqueados.append(nome)
            continue
        if SIMULAR:
            # [V4 M05-19] na simulação, separa as sobras de versão antiga (seriam apagadas, não promovidas)
            p = propriedades_asset(f'{ASSET_TEMP}/{nome}') or {}
            (seriam if versao_tmp_aceita(p.get('versao_algoritmo')) else seriam_apagados).append(nome)
            continue
        if promover_tmp(nome):
            promovidos += 1
    if bloqueados:
        print(f"🛡️ {len(bloqueados)} item(ns) na coleção temporária NÃO foram promovidos (trava do histórico): "
              f"{bloqueados[:10]}{' ...' if len(bloqueados) > 10 else ''}")
    if seriam:
        print(f"🧪 [SIMULAÇÃO] Seriam promovidos da coleção temporária: {len(seriam)} dia(s), "
              f"de {min(seriam)} a {max(seriam)}.")
    if seriam_apagados:   # [V4 M05-19]
        print(f"🧪 [SIMULAÇÃO] Seriam apagados da coleção temporária (versão diferente de {VERSAO_ALGORITMO}): "
              f"{len(seriam_apagados)} dia(s), de {min(seriam_apagados)} a {max(seriam_apagados)}.")
    if promovidos:
        print(f"🔁 {promovidos} dia(s) promovido(s) da coleção temporária para {ASSET_DESTINO}.")

def mapear_colecao():
    if not asset_existe(ASSET_DESTINO):
        return {}
    col = ee.ImageCollection(ASSET_DESTINO)

    def para_feature(img):
        d = img.toDictionary()
        return ee.Feature(None, {
            'id': img.get('system:index'),
            'versao': d.get('versao', 'definitiva'),
            'alg': d.get('versao_algoritmo', 'V1.0'),
            'rodada': d.get('rodada_gfs_ms', 0),
            'metodo': d.get('metodo_temp_gfs', 'aditivo'),          # [V4.1 revisão V41-08]
            'metodo_ur_rs': d.get('metodo_ur_rs_gfs', 'original'),  # [K9A]
            'teto_razao': d.get('teto_razao_temp_gfs', 2.0),          # [K11]
        })

    try:
        lista = col.map(para_feature) \
            .reduceColumns(ee.Reducer.toList().repeat(7), ['id', 'versao', 'alg', 'rodada', 'metodo',
                                                          'metodo_ur_rs', 'teto_razao']) \
            .get('list').getInfo()
    except Exception as e:
        raise RuntimeError(f"Falha ao inventariar {ASSET_DESTINO}; execução interrompida para evitar reenvio em massa. Detalhe: {e}")

    inventario = {}
    for idx, versao, alg, rodada, metodo, metodo_ur_rs, teto_razao in zip(*lista):
        inventario[str(idx).split('/')[-1]] = {
            'versao': versao, 'alg': alg,
            'rodada': int(float(rodada)) if rodada is not None else 0,
            'metodo': metodo,
            'metodo_ur_rs': metodo_ur_rs,                           # [K9A]
            'teto_razao': float(teto_razao) if teto_razao is not None else 2.0,   # [K11]
        }
    return inventario

# =========================================================================
# 4. FUNÇÕES DE CALIBRAÇÃO E MONTAGEM
# =========================================================================
def expandir_borda(img):
    return img.unmask(img.reproject(crs=crsNativo, crsTransform=transformNativo)
                      .focalMean(1, 'square', 'pixels'))

def calib_aditiva(img, m_alvo, m_modelo):
    return img.add(expandir_borda(m_alvo).subtract(expandir_borda(m_modelo)))

def fator_v10(m_alvo, m_modelo):
    """Fator exatamente como na V1.0 (sem teto)."""
    return expandir_borda(m_alvo).divide(expandir_borda(m_modelo).max(1e-3))

def calib_multiplicativa(img, m_alvo, m_modelo):
    # Onde o fator da V1.0 já era <= FATOR_MAX, min() devolve o mesmo valor: resultado idêntico
    return img.multiply(fator_v10(m_alvo, m_modelo).min(FATOR_MAX))

def calib_chuva_gfs(img, m_alvo, m_modelo):
    """[V4 C4/M03-15] Só rota GFS: fator = (m_sicsb + K)/(m_gfs + K), K = K_CHUVA_MM, teto FATOR_MAX.
    A constante K estabiliza o fator nos pixels e meses secos (médias perto de zero)."""
    fator = expandir_borda(m_alvo).add(K_CHUVA_MM).divide(expandir_borda(m_modelo).add(K_CHUVA_MM))
    return img.multiply(fator.min(FATOR_MAX))

def calib_limitada_gfs(img, m_alvo, m_modelo):
    """[V4 C4/M03-15] Só rota GFS (vento e radiação): fator da V1.0 limitado a [0,5; 2,0]."""
    return img.multiply(fator_v10(m_alvo, m_modelo).clamp(FATOR_MIN_UV_RS, FATOR_MAX_UV_RS))

def razao_desvios(s_alvo, s_modelo, teto=None):
    """[V4.1 K7] s_sicsb / s_gfs limitada a [RAZAO_DESVIO_MIN, teto]; teto padrão RAZAO_DESVIO_MAX.
    [K11] A Tmax e a Tmin dos prazos de 6 dias em diante usam teto = RAZAO_DESVIO_MAX_LONGO."""
    teto = RAZAO_DESVIO_MAX if teto is None else teto
    return (expandir_borda(s_alvo).divide(expandir_borda(s_modelo).max(1e-3))
            .clamp(RAZAO_DESVIO_MIN, teto))

def teto_razao_temp(faixa):
    """[K11] Teto da razão dos desvios da Tmax e da Tmin na faixa de prazo do dia."""
    return RAZAO_DESVIO_MAX_LONGO if faixa in FAIXAS_LONGAS else RAZAO_DESVIO_MAX

def calib_variancia(img, m_alvo, m_modelo, s_alvo, s_modelo, teto=None):
    """[V4.1 K7] Escala de variância (só rota GFS): m_alvo + (x - m_modelo) x razão dos desvios."""
    return expandir_borda(m_alvo).add(img.subtract(expandir_borda(m_modelo))
                                      .multiply(razao_desvios(s_alvo, s_modelo, teto)))

def teto_umidade(solo, camada):
    m = expandir_borda(solo.select(f'{camada}_m_smap'))
    s = expandir_borda(solo.select(f'{camada}_s_smap'))
    return m.add(s.multiply(SIGMAS_TETO_UMIDADE)).min(UMIDADE_MAX_FISICA).unmask(UMIDADE_MAX_FISICA)

def es_de(T):
    return T.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': T})

def vpd_e_ea(tmax, tmin, rh):
    es = es_de(tmax).add(es_de(tmin)).divide(2)
    ea = es.multiply(rh).divide(100)
    return es.subtract(ea).max(0).rename('vpd'), ea

def eto_penman_monteith(tmax, tmin, rh, u2, rs, data_str):
    """ETo diária FAO-56 Penman-Monteith (mm/dia), a mesma conta que a rota GFS faz desde a V1.0.
    Entradas por pixel: Tmax e Tmin (°C), UR (%), vento a 2 m (m/s) e radiação solar (MJ/m²/dia).
    Usada pelas rotas GFS e provisória (ERA5); nos dias definitivos a ETo vem do BR-DWGD."""
    data_atual = ee.Date(data_str)
    lat_rad = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180.0)
    pressao_atm = elevacao_br.multiply(-0.0065).add(293.0).divide(293.0).pow(5.26).multiply(101.3)
    gamma_dinamico = pressao_atm.multiply(0.000665)
    tmedia = tmax.add(tmin).divide(2)
    vpd, ea = vpd_e_ea(tmax, tmin, rh)
    J = ee.Number(data_atual.getRelative('day', 'year')).add(1)
    dr = J.multiply(2.0 * math.pi / 365.0).cos().multiply(0.033).add(1.0)
    delta_sol = J.multiply(2.0 * math.pi / 365.0).subtract(1.39).sin().multiply(0.409)
    ws = lat_rad.tan().multiply(delta_sol.tan()).multiply(-1.0).clamp(-1.0, 1.0).acos()
    termo1 = ws.multiply(lat_rad.sin()).multiply(delta_sol.sin())
    termo2 = lat_rad.cos().multiply(delta_sol.cos()).multiply(ws.sin())
    Ra = termo1.add(termo2).multiply(dr).multiply((24.0 * 60.0 / math.pi) * 0.0820)
    Rso = elevacao_br.multiply(0.00002).add(0.75).multiply(Ra)
    Rs_Rso = rs.divide(Rso).clamp(0.0, 1.0)
    Rns = rs.multiply(0.77)
    tmax_k = tmax.add(273.16)
    tmin_k = tmin.add(273.16)
    rad_term = tmax_k.pow(4).add(tmin_k.pow(4)).divide(2.0).multiply(4.903e-9)
    umid_term = ea.sqrt().multiply(-0.14).add(0.34)
    nuvem_term = Rs_Rso.multiply(1.35).subtract(0.35)
    Rn = Rns.subtract(rad_term.multiply(umid_term).multiply(nuvem_term).max(0))
    delta_press = tmedia.expression(
        '4283.58 * (0.6108 * exp(17.625 * T / (T + 243.04))) / ((T + 243.04) ** 2)', {'T': tmedia})
    num_1 = delta_press.multiply(Rn).multiply(0.408)
    num_2 = gamma_dinamico.multiply(ee.Image(900).divide(tmedia.add(273))).multiply(u2).multiply(vpd)
    den = delta_press.add(gamma_dinamico.multiply(ee.Image(1).add(u2.multiply(0.34))))
    return num_1.add(num_2).divide(den).max(0).rename('et_potencial')

def finalizar(img, propriedades):
    et_pot = img.select('et_potencial')
    et_real = img.select('et_real')
    transp = img.select('transpiracao_mm')
    et_real_l = et_real.min(et_pot.unmask(et_real)).rename('et_real')
    transp_l = transp.min(et_real_l).rename('transpiracao_mm')
    # [V4 C2/M05-03] Máscara canônica no lugar do .clip(poligonoBrasil): todas as rotas gravam a
    # cobertura do histórico (SAB_2025_12_31, banda pr_mm), que já traz o recorte pelo polígono GAUL.
    # O clip não é necessário para a pegada: a exportação usa region=limitesRegiao, e fora da máscara
    # tudo fica mascarado. Manter os dois poderia aplicar duas vezes a fração de borda (A CONFIRMAR:
    # como updateMask combina máscaras fracionárias; com a máscara própria da imagem = 1, o resultado é
    # a máscara de referência em qualquer regra). Efeito: os dias GFS perdem os ~4 pixels extras do
    # D10; as bandas de solo do GFS deixam de crescer 1 pixel por dia; a cobertura dos dias ERA5 e
    # definitivos fica a mesma de hoje. [V4 A-03] O updateMask só RESTRINGE: nos dias GFS a cobertura
    # fica CONTIDA na canônica (a calibração vem da pegada do BR-DWGD dilatada 2 pixels), e pixels
    # isolados preenchidos pelo ERA5 no histórico (ilhas, por exemplo) podem ficar sem valor. O D10
    # da auditoria 08 v4 confere isso separando os dias GFS dos dias ERA5.
    saida = (img.addBands(ee.Image.cat([et_real_l, transp_l]), overwrite=True)
             .select(ORDEM_BANDAS).toFloat().updateMask(MASCARA_SAB))
    return saida.set(propriedades)

def _componentes_era5(data_str):
    dStart = ee.Date(data_str)
    dEnd = dStart.advance(1, 'day')
    mes = data_str[5:7]
    clima = ee.Image(f'{ASSET_CLIMATOLOGIA}/Matriz_Clima_{mes}')
    solo = ee.Image(f'{ASSET_SOLO}/Matriz_Solo_{mes}')
    era = ee.Image(colecao_era5.filterDate(dStart, dEnd).first())

    def mc(p):
        return clima.select(f'{p}_m_br'), clima.select(f'{p}_m_era')

    def ms(p):
        return solo.select(f'{p}_m_smap'), solo.select(f'{p}_m_era5')

    pr_raw = era.select('total_precipitation_sum').multiply(1000).max(0)
    tmax_raw = era.select('temperature_2m_max').subtract(273.15).resample('bilinear')
    tmin_raw = era.select('temperature_2m_min').subtract(273.15).resample('bilinear')
    # Limitação conhecida: o DAILY_AGGR só traz componentes médias; a velocidade derivada
    # delas subestima o vento em dias de direção variável. Corrigir exige ERA5_LAND/HOURLY.
    u2_raw = era.select('u_component_of_wind_10m').hypot(era.select('v_component_of_wind_10m')) \
        .multiply(0.748).resample('bilinear')
    rs_raw = era.select('surface_solar_radiation_downwards_sum').divide(1e6).resample('bilinear')
    t2m = era.select('temperature_2m').subtract(273.15).resample('bilinear')
    tdew = era.select('dewpoint_temperature_2m').subtract(273.15).resample('bilinear')
    rh_raw = t2m.expression(
        '100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))',
        {'T': t2m, 'Td': tdew})
    # V1.3: a evaporação potencial do ECMWF (potential_evaporation_sum) deixou de ser usada;
    # a ETo é calculada por Penman-Monteith logo abaixo, com a meteorologia já calibrada.

    c = {}
    c['pr_mm'] = calib_multiplicativa(pr_raw, *mc('pr')).max(0).rename('pr_mm')
    c['u2'] = calib_multiplicativa(u2_raw, *mc('u2')).max(0).rename('u2')
    c['rs'] = calib_multiplicativa(rs_raw, *mc('Rs')).max(0).rename('rs')
    c['tmax_C'] = calib_aditiva(tmax_raw, *mc('Tmax')).rename('tmax_C')
    c['tmin_C'] = calib_aditiva(tmin_raw, *mc('Tmin')).rename('tmin_C')
    c['RH'] = calib_aditiva(rh_raw, *mc('RH')).clamp(0, 100).rename('RH')
    c['et_potencial'] = eto_penman_monteith(c['tmax_C'], c['tmin_C'], c['RH'], c['u2'], c['rs'], data_str)
    c['vpd'], _ = vpd_e_ea(c['tmax_C'], c['tmin_C'], c['RH'])

    c['et_real'] = era.select('total_evaporation_sum').multiply(-1000).max(0) \
        .rename('et_real').resample('bilinear')
    # ATENÇÃO: problema conhecido do ERA5-Land (ver catálogo GEE). As bandas estão trocadas:
    # evaporation_from_bare_soil_sum CONTÉM os valores de transpiração da vegetação.
    # evaporation_from_vegetation_transpiration_sum contém evaporação de águas abertas. Não trocar.
    c['transpiracao_mm'] = era.select('evaporation_from_bare_soil_sum').multiply(-1000).max(0) \
        .rename('transpiracao_mm').resample('bilinear')
    c['tsolo_C'] = era.select('soil_temperature_level_1').subtract(273.15).rename('tsolo_C').resample('bilinear')
    c['tfolha_C'] = era.select('skin_temperature').subtract(273.15).rename('tfolha_C').resample('bilinear')

    ssur_era = era.select('volumetric_soil_water_layer_1')
    swat_era = era.expression('(l1*7 + l2*21 + l3*72) / 100', {
        'l1': era.select('volumetric_soil_water_layer_1'),
        'l2': era.select('volumetric_soil_water_layer_2'),
        'l3': era.select('volumetric_soil_water_layer_3'),
    })
    if SOLO_BILINEAR:   # V1.4: igual à matriz SICSB_SOLO_2015_2025 (que gera o fator SMAP/ERA5)
        ssur_era = ssur_era.resample('bilinear')
        swat_era = swat_era.resample('bilinear')
    rsup_era = era.select('surface_runoff_sum').multiply(1000).max(0)
    rsub_era = era.select('sub_surface_runoff_sum').multiply(1000).max(0)

    c['soil_moisture_0_5cm_m3_m3'] = calib_multiplicativa(ssur_era, *ms('ssur')).max(0) \
        .min(teto_umidade(solo, 'ssur')).rename('soil_moisture_0_5cm_m3_m3')
    c['soil_moisture_0_100cm_m3_m3'] = calib_multiplicativa(swat_era, *ms('swat')).max(0) \
        .min(teto_umidade(solo, 'swat')).rename('soil_moisture_0_100cm_m3_m3')
    c['runoff_sup_mm'] = calib_multiplicativa(rsup_era, *ms('rsup')).max(0).rename('runoff_sup_mm')
    c['runoff_sub_mm'] = calib_multiplicativa(rsub_era, *ms('rsub')).max(0).rename('runoff_sub_mm')
    return c

# =========================================================================
# 5. ROTAS DE PROCESSAMENTO
# =========================================================================
def processarDia_Definitivo(data_str):
    c = _componentes_era5(data_str)
    dStart = ee.Date(data_str)
    dEnd = dStart.advance(1, 'day')

    dummyBR = ee.Image.constant([-99999] * 7).rename(['pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs', 'ET'])
    imgBR = ee.Image(colChuvaGeral.filterDate(dStart, dEnd).merge(ee.ImageCollection([dummyBR])).first())
    # [V4 C1/M05-02] Pixel válido do BR-DWGD: exclui o valor de ausência -32768 (viraria Tmax/Tmin
    # = -20 °C e chuva 0) e o dummy -99999 (dia sem BR-DWGD), em pr, Tmax e Tmin, como no 03.
    valido_br = (imgBR.select('pr').gt(-32768)
                 .And(imgBR.select('Tmax').gt(-32768))
                 .And(imgBR.select('Tmin').gt(-32768)))

    tmax_br = imgBR.select('Tmax').multiply(0.00106815).add(15.0)
    tmin_br = imgBR.select('Tmin').multiply(0.00106815).add(15.0)
    rh_br = imgBR.select('RH').multiply(0.39370079).add(-0.393701).clamp(0, 100)
    vpd_br, _ = vpd_e_ea(tmax_br, tmin_br, rh_br)

    br = {
        'pr_mm': imgBR.select('pr').multiply(0.00686666).add(225.0).max(0),
        'tmax_C': tmax_br,
        'tmin_C': tmin_br,
        'RH': rh_br,
        'vpd': vpd_br,
        # [V4 C1/M05-02] .max(0): o bruto 0 viraria ETo -0,051 mm, radiação -0,057 MJ e vento -0,059 m/s
        'et_potencial': imgBR.select('ET').multiply(0.05118110).add(-0.0511811).max(0),
        'rs': imgBR.select('Rs').multiply(0.15708661).add(-0.057087).max(0),
        'u2': imgBR.select('u2').multiply(0.05905512).add(-0.059055).max(0),
    }

    # [V4 C1/M05-01] BR-DWGD primeiro e ERA5 só onde ele falta. Na V1.0-V1.4 era
    # c[b].where(has_real_br, br[b]) seguido de unmask(fallback): onde o ERA5 calibrado é máscara
    # (litoral, lagoas, estuários), o where não faz nada e o valor do BR-DWGD era descartado, ficando
    # a média focal do ERA5. O histórico V1.0 tem 204 pixels assim (classe B da auditoria J1, valor
    # que não vem do BR-DWGD). O histórico NÃO é regravado (trava): esse defeito é tratado na leitura
    # pela máscara de qualidade SAB_MASCARA_QUALIDADE (classe 2). Só os definitivos novos mudam.
    # sameFootprint=False: a pegada da saída é a união das duas. Com o padrão (True) ficaria só a
    # pegada do BR-DWGD (grade a partir de -73,9°, sem as ilhas oceânicas), e pixels de borda que hoje
    # vêm do ERA5 sumiriam dos definitivos novos.
    era_cheia = expandir_borda(ee.Image.cat([c[b] for b in ORDEM_BANDAS]).toFloat())
    img = ee.Image.cat([
        (br[b].updateMask(valido_br).unmask(era_cheia.select(b), sameFootprint=False) if b in br
         else era_cheia.select(b)).rename(b)
        for b in ORDEM_BANDAS
    ]).toFloat()

    return finalizar(img, {
        'system:time_start': dStart.millis(),
        'versao': 'definitiva',
        'versao_algoritmo': VERSAO_ALGORITMO,
        'fonte': FONTE_DEFINITIVA,                    # [V4 B8/M05-17]
        'janela_chuva_utc': JANELA_CHUVA_12_12,       # [V4 B8/M05-17]
    })

def processarDia_Rota1(data_str):
    c = _componentes_era5(data_str)
    img = expandir_borda(ee.Image.cat([c[b] for b in ORDEM_BANDAS]).toFloat())
    return finalizar(img, {
        'system:time_start': ee.Date(data_str).millis(),
        'versao': 'provisoria_era5',
        'versao_algoritmo': VERSAO_ALGORITMO,
        'fonte': FONTE_ERA5,                          # [V4 B8/M05-17]
        'janela_chuva_utc': JANELA_CHUVA_00_24,       # [V4 B8/M05-17]
    })

def aplicarPatch_Solo(data_str):
    """Corrige SÓ umidade do solo e escoamento de um dia gravado pela V1.0.
    As outras 12 bandas e todas as propriedades são copiadas do asset existente.
    Valor V1.0 = bruto x fator_v10, então o valor com teto = valor V1.0 x (FATOR_MAX / fator_v10)
    nos pixels onde fator_v10 > FATOR_MAX; nos demais, o valor não muda."""
    solo = ee.Image(f'{ASSET_SOLO}/Matriz_Solo_{data_str[5:7]}')
    antigo = ee.Image(f'{ASSET_DESTINO}/{id_dia(data_str)}')

    def correcao(p):
        f = fator_v10(solo.select(f'{p}_m_smap'), solo.select(f'{p}_m_era5'))
        acima = f.gt(FATOR_MAX).unmask(0)
        return ee.Image.constant(1).where(acima, ee.Image.constant(FATOR_MAX).divide(f))

    novas = []
    for banda, p in [('runoff_sup_mm', 'rsup'), ('runoff_sub_mm', 'rsub'),
                     ('soil_moisture_0_5cm_m3_m3', 'ssur'), ('soil_moisture_0_100cm_m3_m3', 'swat')]:
        b = antigo.select(banda).multiply(correcao(p))
        if p in ('ssur', 'swat'):
            b = b.min(teto_umidade(solo, p))
        novas.append(b.toFloat().rename(banda))

    return (antigo.addBands(ee.Image.cat(novas), overwrite=True)
            .select(ORDEM_BANDAS)
            .set('versao_algoritmo', VERSAO_PATCH))

_cache_bandas_gfs = {}

def bandas_matriz_gfs(mes):
    if mes not in _cache_bandas_gfs:
        _cache_bandas_gfs[mes] = ee.Image(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{mes}').bandNames().getInfo()
    return _cache_bandas_gfs[mes]

def colecao_gfs_rodada(creation_ms):
    # Pressupõe system:time_start == creation_time no NOAA/GFS0P25 (filtro indexado, rápido).
    return (ee.ImageCollection(COL_GFS)
            .filterDate(creation_ms, creation_ms + 3600 * 1000)
            .filter(ee.Filter.eq('creation_time', creation_ms)))

def contagem_esperada(dia_ms, creation_ms):
    """Horas de previsão esperadas na janela (início, fim] do dia, e blocos de chuva de 6 h."""
    h0 = int(round((dia_ms - creation_ms) / 3600000.0))
    horas = [h for h in range(h0 + 1, h0 + 25) if 0 < h <= 384 and (h <= 120 or h % 3 == 0)]
    # [V4 A-02] Horas inteiras, como o 03 e o F3 da auditoria (inList com inteiros comprovado no acervo).
    horas_chuva = [h for h in horas if h % 6 == 0]
    return len(horas), horas_chuva

FAIXAS_GFS = ('L1', 'L2a5', 'L6a10', 'L11a15')
# [V4 B3/M05-07] As 48 bandas de média que o motor usa: {v}_m_{sicsb|gfs}_{faixa}
BANDAS_MEDIA_GFS = [f'{v}_m_{fonte}_{fx}' for fx in FAIXAS_GFS for fonte in ('sicsb', 'gfs')
                    for v in VARS_MATRIZ_GFS]
# [V4.1 K7] As 16 bandas de desvio da Tmax e da Tmin, usadas pela escala de variância (contrato V2.1: 100 bandas)
BANDAS_DESVIO_TEMP = [f'{v}_s_{fonte}_{fx}' for fx in FAIXAS_GFS for fonte in ('sicsb', 'gfs')
                      for v in ('Tmax', 'Tmin')]
# [K9A] As 16 bandas de desvio da UR e da radiação, usadas pela escala de variância (METODO_UR_RS_GFS)
BANDAS_DESVIO_UR_RS = [f'{v}_s_{fonte}_{fx}' for fx in FAIXAS_GFS for fonte in ('sicsb', 'gfs')
                       for v in ('RH', 'Rs')]

def colecao_gfs_dia(data_str, creation_ms):
    """[V4] Saídas da rodada válidas na janela (00Z, 24Z] do dia, cada uma reamostrada (bilinear).
    Extraída de processarDia_GFS para a PRÉVIA 6 usar a mesma seleção (GFS bruto)."""
    data_atual = ee.Date(data_str)
    t0 = data_atual.millis()
    t1 = data_atual.advance(1, 'day').millis()
    # CORRIGIDO: janela (00Z, 24Z]. Acumulados e extremos do GFS referem-se ao período
    # que TERMINA no forecast_time.
    saidas = (colecao_gfs_rodada(creation_ms)
              .filter(ee.Filter.gt('forecast_time', t0))
              .filter(ee.Filter.lte('forecast_time', t1))
              .filter(ee.Filter.gt('forecast_hours', 0)))
    # [V4 M05-11] Uma imagem por hora de previsão: uma duplicata no acervo dobraria o bloco de chuva.
    # Collection.distinct devolve, no cliente Python, um FeatureCollection; o ee.ImageCollection()
    # só refaz o tipo para o map com resample (os elementos continuam imagens no servidor).
    saidas = ee.ImageCollection(saidas.distinct('forecast_hours'))
    # V1.4: bilinear em cada imagem antes de compor (resample não vale em composições)
    return saidas.map(lambda i: i.resample('bilinear'))

def eh_rodada_00z(creation_ms):
    """[V4 B1] Rodada das 00Z: creation_time múltiplo de 86.400.000 ms."""
    return int(creation_ms) % MS_DIA == 0

def selecionar_rodadas(rodadas_ms, contagens):
    """[V4 B1/M05-08] rodadas_ms: creation_time de cada rodada; contagens: nº de horas distintas de
    HORAS_RODADA_COMPLETA presentes em cada uma (mesma ordem). Devolve (rodadas_00z, completas,
    referencia): só rodadas 00Z, completas = com as 208 saídas, referência = a completa mais recente
    (None se nenhuma estiver completa)."""
    contagem = {}
    for r, n in zip(rodadas_ms, contagens):
        contagem[int(float(r))] = int(n or 0)
    rodadas_00z = sorted(r for r in contagem if eh_rodada_00z(r))
    completas = [r for r in rodadas_00z if contagem[r] >= N_SAIDAS_RODADA]
    return rodadas_00z, completas, (completas[-1] if completas else None)

def prazo_L(dia_ms, creation_ms):
    """[V4] Prazo do dia em relação à rodada: o dia L termina 24*L horas depois da criação."""
    horas_fim = (dia_ms + MS_DIA - creation_ms) / 3600000.0
    return math.ceil(horas_fim / 24.0 - 1e-9)

def faixa_prazo(dia_ms, creation_ms):
    """Faixa de antecedência do dia em relação à rodada: L1 (1º dia), L2a5, L6a10, L11a15.
    O dia L termina 24*L horas depois da criação da rodada.
    [V4 M05-28] O prazo 16 (horas 361-384) entra em L11a15: calibração extrapolada."""
    L = prazo_L(dia_ms, creation_ms)
    if L <= 1:
        return 'L1'
    if L <= 5:
        return 'L2a5'
    if L <= 10:
        return 'L6a10'
    return 'L11a15'

def confianca_prazo(L):
    """[V4 B8] Confianca_Prazo: 'alta' (prazo 1 a 5), 'media' (6 a 10), 'baixa' (11 em diante)."""
    if L <= 5:
        return 'alta'
    if L <= 10:
        return 'media'
    return 'baixa'

def fim_horizonte(hoje_str, referencia_ms):
    """[V4 B1-horizonte] Último dia da cadeia GFS: min(hoje + 15, dia da referência + 15).
    O dia da referência + 15 é o prazo 16 (horas 361-384), o último que a rodada 00Z cobre."""
    return min(somar_dias(hoje_str, HORIZONTE_DIAS),
               somar_dias(ms_para_data(referencia_ms), HORIZONTE_DIAS))

def rodada_para_dia(d_str, completas, referencia):
    """[V4 B1/M05-09] Rodada 00Z usada no dia. Dias a partir do dia da referência: a referência.
    Dias passados: a rodada 00Z do próprio dia, se completa; se não, a 00Z completa anterior mais
    recente que ainda cubra o dia (prazo <= 16). None se nenhuma rodada completa cobrir o dia."""
    t0 = data_para_ms(d_str)
    if t0 >= referencia:
        return referencia
    candidatas = [r for r in completas if r <= t0 and prazo_L(t0, r) <= PRAZO_MAX_GFS]
    return max(candidatas) if candidatas else None

def precisa_refazer_gfs(info, rodada, forcar, n_blocos, faixa=None):
    """Decide se um dia da cadeia GFS precisa ser (re)calculado.
    [V4 M05-09] Também refaz dias gravados como incompletos ou com falha quando a rodada do dia
    tem os 4 blocos de chuva (antes, com a mesma rodada, nunca eram refeitos)."""
    if forcar or info is None:
        return True
    if info['rodada'] != rodada or info['alg'] != VERSAO_ALGORITMO:
        return True
    if info.get('metodo', 'aditivo') != METODO_TEMP_GFS:     # [V4.1 revisão V41-08] troca de método refaz o dia
        return True
    if info.get('metodo_ur_rs', 'original') != METODO_UR_RS_GFS:   # [K9A] troca de método da UR/radiação refaz o dia
        return True
    if faixa is not None and abs(float(info.get('teto_razao', 2.0)) - teto_razao_temp(faixa)) > 1e-9:
        return True                                               # [K11] gravado com outro teto da razão
    return info['versao'] != 'provisoria_gfs' and n_blocos >= 4

def processarDia_GFS(data_str, estado_anterior, ref, creation_ms, n_img_esperado, horas_chuva, faixa,
                     prazo, metodo_temp=None):   # [V4 B8] prazo L do dia; [V4.1 K7] metodo_temp (PRÉVIA 6)
    data_atual = ee.Date(data_str)
    mes = data_str[5:7]

    # Janela (00Z, 24Z] do dia; [V4 M05-11] sem saídas duplicadas (ver colecao_gfs_dia)
    gfs_dia = colecao_gfs_dia(data_str, creation_ms)
    chuva_blocos = gfs_dia.filter(ee.Filter.inList('forecast_hours', horas_chuva))

    qtd_img = gfs_dia.size()
    qtd_chuva = chuva_blocos.size()

    if len(horas_chuva) >= 4:
        # [V4 M05-11] contagem exata (eq), como no 03: todas as saídas esperadas e os 4 blocos
        completo = qtd_img.eq(n_img_esperado).And(qtd_chuva.eq(len(horas_chuva)))
    else:
        completo = ee.Number(0)                   # dia além do horizonte da rodada
    versao_ok = ee.Algorithms.If(completo, 'provisoria_gfs', 'provisoria_gfs_incompleta')

    nomes = ['total_precipitation_surface', 'maximum_temperature_2m_above_ground',
             'minimum_temperature_2m_above_ground', 'downward_shortwave_radiation_flux',
             'relative_humidity_2m_above_ground', 'wind_speed_10m_above_ground']

    def vel_vento(img):
        return img.select('u_component_of_wind_10m_above_ground') \
            .hypot(img.select('v_component_of_wind_10m_above_ground')) \
            .rename('wind_speed_10m_above_ground')

    img_chuva = ee.Image(ee.Algorithms.If(
        qtd_chuva.gt(0),
        chuva_blocos.select('total_precipitation_surface').sum(),
        ee.Image.constant(0).rename('total_precipitation_surface')))
    # [V4 B6/M05-10] Chuva do balde de solo: a soma dos n blocos escalada por 4/n, ou seja, a média
    # dos blocos x 4 (0 sem blocos). Em dia completo o balde usa a própria chuva do dia (abaixo).
    img_chuva_balde = ee.Image(ee.Algorithms.If(
        qtd_chuva.gt(0),
        chuva_blocos.select('total_precipitation_surface').mean().multiply(4),
        ee.Image.constant(0).rename('total_precipitation_surface')))

    # V1.4: o fluxo de onda curta do GFS é a média desde o início do bloco de 6 h (auditoria F4).
    # Nas horas múltiplas de 6 ele vale a média do bloco inteiro; a média desses blocos é a média
    # do dia. [V4 B6/M05-10] Sem nenhum bloco no dia, a radiação fica mascarada (acabou a média
    # simples das saídas, que o F4 condenou); o balde usa a radiação média do BR-DWGD (abaixo).
    img_rad = ee.Image(ee.Algorithms.If(
        qtd_chuva.gt(0),
        chuva_blocos.select('downward_shortwave_radiation_flux').mean(),
        ee.Image.constant(0).rename('downward_shortwave_radiation_flux').updateMask(0)))
    img_dia = ee.Image(ee.Algorithms.If(
        qtd_img.gt(0),
        ee.Image.cat([
            img_chuva,
            # Mesma variável usada na matriz SICSB_MATRIZ_GFS (temperatura horária instantânea)
            gfs_dia.select('temperature_2m_above_ground').max().rename('maximum_temperature_2m_above_ground'),
            gfs_dia.select('temperature_2m_above_ground').min().rename('minimum_temperature_2m_above_ground'),
            img_rad.rename('downward_shortwave_radiation_flux'),
            gfs_dia.select('relative_humidity_2m_above_ground').mean(),
            gfs_dia.map(vel_vento).mean(),
        ]),
        ee.Image.constant([0] * 6).rename(nomes)))

    pr_raw = img_dia.select('total_precipitation_surface').max(0)
    tmax_raw = img_dia.select('maximum_temperature_2m_above_ground')
    tmin_raw = img_dia.select('minimum_temperature_2m_above_ground')
    rs_raw = img_dia.select('downward_shortwave_radiation_flux').multiply(0.0864).max(0)
    rh_raw = img_dia.select('relative_humidity_2m_above_ground').clamp(0, 100)
    u2_raw = img_dia.select('wind_speed_10m_above_ground').multiply(0.748)

    cache_gfs = ee.Image(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{mes}')
    bandas_cache = bandas_matriz_gfs(mes)

    def medias(banda):
        # V1.4: média do GFS da mesma faixa de prazo do dia (matriz V2)
        alvo, modelo = f'{banda}_m_sicsb_{faixa}', f'{banda}_m_gfs_{faixa}'
        faltam = [b for b in (alvo, modelo) if b not in bandas_cache]
        if faltam:
            raise RuntimeError(f"Matriz GFS do mês {mes} sem as bandas {faltam}; gere a SICSB_MATRIZ_GFS_V2.")
        return cache_gfs.select(alvo), cache_gfs.select(modelo)

    def desvios(banda):
        # [V4.1 K7] desvios-padrão diários do BR-DWGD e do GFS na mesma faixa (bandas s da matriz V2.1);
        # [K9A] usados na Tmax, na Tmin e, com METODO_UR_RS_GFS = 'variancia', na UR e na radiação
        alvo, modelo = f'{banda}_s_sicsb_{faixa}', f'{banda}_s_gfs_{faixa}'
        faltam = [b for b in (alvo, modelo) if b not in bandas_cache]
        if faltam:
            raise RuntimeError(f"Matriz GFS do mês {mes} sem as bandas {faltam}; gere a SICSB_MATRIZ_GFS_V2 (V2.1).")
        return cache_gfs.select(alvo), cache_gfs.select(modelo)

    # [V4 C4/M03-15] chuva com fator suavizado (K_CHUVA_MM); vento com fator em [0,5; 2,0];
    # [K9A] UR e radiação pela escala de variância (METODO_UR_RS_GFS)
    pr = calib_chuva_gfs(pr_raw, *medias('pr')).max(0).rename('pr_mm')
    metodo = metodo_temp or METODO_TEMP_GFS                                   # [V4.1 K7]
    if metodo == 'variancia':
        teto_temp = teto_razao_temp(faixa)                                            # [K11]
        tmax_c = calib_variancia(tmax_raw, *medias('Tmax'), *desvios('Tmax'), teto=teto_temp)
        tmin_c = calib_variancia(tmin_raw, *medias('Tmin'), *desvios('Tmin'), teto=teto_temp)
    else:
        tmax_c = calib_aditiva(tmax_raw, *medias('Tmax'))
        tmin_c = calib_aditiva(tmin_raw, *medias('Tmin'))
    # Amplitude mínima: preserva a média e só altera pixels com amplitude < AMPLITUDE_MIN_C
    t_med = tmax_c.add(tmin_c).divide(2)
    meia_amp = tmax_c.subtract(tmin_c).max(AMPLITUDE_MIN_C).divide(2)
    tmax = t_med.add(meia_amp).rename('tmax_C')
    tmin = t_med.subtract(meia_amp).rename('tmin_C')
    u2 = calib_limitada_gfs(u2_raw, *medias('u2')).max(0).rename('u2')            # [V4 C4]
    if METODO_UR_RS_GFS == 'variancia':                                           # [K9A]
        rh = calib_variancia(rh_raw, *medias('RH'), *desvios('RH')).clamp(0, 100).rename('RH')
        rs = calib_variancia(rs_raw, *medias('Rs'), *desvios('Rs')).max(0).rename('rs')
    else:
        rh = calib_aditiva(rh_raw, *medias('RH')).clamp(0, 100).rename('RH')
        rs = calib_limitada_gfs(rs_raw, *medias('Rs')).max(0).rename('rs')        # [V4 C4]

    # [V4 B6/M05-10] Entradas do balde. Em dia completo são a própria chuva e a própria radiação do
    # dia. Em dia incompleto: chuva escalada para 4 blocos e radiação dos blocos disponíveis; sem
    # nenhum bloco, a radiação média do BR-DWGD (Rs_m_sicsb da faixa) só para a ETo do balde.
    # Nesses dias, a saída grava chuva, radiação, ETo, ET real e transpiração mascaradas.
    pr_balde = ee.Image(ee.Algorithms.If(
        completo, pr,
        calib_chuva_gfs(img_chuva_balde.max(0), *medias('pr')).max(0).rename('pr_mm')))
    rs_balde = ee.Image(ee.Algorithms.If(
        qtd_chuva.gt(0), rs, expandir_borda(medias('Rs')[0]).rename('rs')))

    vpd, _ = vpd_e_ea(tmax, tmin, rh)
    # Penman-Monteith FAO-56: a mesma função usada pela rota provisória (ERA5) a partir da V1.3
    # [V4 B6] com rs_balde (= rs nos dias completos)
    et_potencial = eto_penman_monteith(tmax, tmin, rh, u2, rs_balde, data_str)

    # Balde de solo ancorado no último período ERA5 de cada pixel (ref):
    #  - capacidade e início da drenagem nunca abaixo da umidade do último dia ERA5
    #  - ET real = ETp x razão ET real/ETp do ERA5 recente x variação relativa da umidade
    #  - transpiração = mesma fração da ET real observada no ERA5 recente
    k_et = ref.select('k_et')
    f_transp = ref.select('f_transp')
    sw_ref = ref.select('sw_ref_100')
    cap100 = sw_ref.max(SW100_MAX_MM)
    cc100 = sw_ref.max(SW100_CC_MM).min(cap100)
    cap5 = ref.select('sw_ref_5').max(SW5_MAX_MM)

    sw100 = estado_anterior.select('sw_100').min(cap100)
    sw5 = estado_anterior.select('sw_5').min(cap5)
    saturacao = sw100.divide(cap100)
    cn = ee.Image.constant(60).add(saturacao.multiply(35))
    s_ret = ee.Image.constant(25400).divide(cn).subtract(254)
    p_ia = pr_balde.subtract(s_ret.multiply(0.2)).max(0)                     # [V4 B6] pr_balde
    runoff_sup = p_ia.pow(2).divide(p_ia.add(s_ret)).rename('runoff_sup_mm')
    infiltracao = pr_balde.subtract(runoff_sup).max(0)                       # [V4 B6] pr_balde

    g_umidade = sw100.divide(sw_ref.max(1.0)).clamp(0.5, 1.5)
    et_real = et_potencial.multiply(k_et).multiply(g_umidade).min(et_potencial).rename('et_real')
    transp_b = et_real.multiply(f_transp).rename('transpiracao_mm')
    evaporacao = et_real.subtract(transp_b)

    sw100_tmp = sw100.add(infiltracao).subtract(et_real)
    excesso = sw100_tmp.subtract(cap100).max(0)
    drenagem = sw100_tmp.min(cap100).subtract(cc100).max(0).multiply(0.04)
    runoff_sub = excesso.add(drenagem).rename('runoff_sub_mm')
    # clamp() só aceita números; com limite por pixel (imagem) usa-se max/min
    novo_sw100 = sw100_tmp.subtract(runoff_sub).max(0).min(cap100)
    novo_sw5 = sw5.add(infiltracao).subtract(evaporacao).max(0).min(cap5)

    # tsolo/tfolha mascarados: o GFS não tem equivalente direto às bandas do ERA5,
    # e usar Tmédia/Tmin criava degrau artificial na transição ERA5 -> GFS.
    mascarado = ee.Image.constant(0).updateMask(0)

    bandas_ok = {
        'pr_mm': pr, 'tmax_C': tmax, 'tmin_C': tmin, 'RH': rh,
        'et_potencial': et_potencial, 'et_real': et_real, 'vpd': vpd,
        'rs': rs, 'u2': u2,
        'tsolo_C': mascarado.rename('tsolo_C'), 'tfolha_C': mascarado.rename('tfolha_C'),
        'transpiracao_mm': transp_b, 'runoff_sup_mm': runoff_sup, 'runoff_sub_mm': runoff_sub,
        'soil_moisture_0_5cm_m3_m3': novo_sw5.divide(50).rename('soil_moisture_0_5cm_m3_m3'),
        'soil_moisture_0_100cm_m3_m3': novo_sw100.divide(1000).rename('soil_moisture_0_100cm_m3_m3'),
    }
    img_ok = ee.Image.cat([bandas_ok[b] for b in ORDEM_BANDAS]).toFloat() \
        .reproject(crs=crsNativo, crsTransform=transformNativo)   # V1.4: sem resample na composição
    img_ok = expandir_borda(img_ok)
    # [V4 B6/M05-10] Dia incompleto: chuva, radiação, ETo, ET real e transpiração mascaradas (o painel
    # mostra "Parcial"); temperatura, UR, vento, VPD, escoamento e umidade do solo continuam gravados.
    img_ok = ee.Image(ee.Algorithms.If(
        completo, img_ok,
        img_ok.addBands(img_ok.select(BANDAS_MASCARADAS_INCOMPLETO).updateMask(0), overwrite=True)))

    bandas_falha = {b: mascarado.rename(b) for b in ORDEM_BANDAS}
    bandas_falha['soil_moisture_0_5cm_m3_m3'] = sw5.divide(50).rename('soil_moisture_0_5cm_m3_m3')
    bandas_falha['soil_moisture_0_100cm_m3_m3'] = sw100.divide(1000).rename('soil_moisture_0_100cm_m3_m3')
    img_falha = ee.Image.cat([bandas_falha[b] for b in ORDEM_BANDAS]).toFloat()

    registro_gee = ee.Algorithms.If(
        qtd_img.gt(0),
        ee.Date(ee.Number(gfs_dia.aggregate_max('system:version')).divide(1000)).format('YYYY-MM-dd HH:mm:ss'),
        'N/A')

    comuns = {
        'system:time_start': data_atual.millis(),
        'versao_algoritmo': VERSAO_ALGORITMO,
        'rodada_gfs_ms': creation_ms,
        'Rodada_Utilizada_NOAA': datetime.fromtimestamp(creation_ms / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'Imagens_Esperadas_GFS': n_img_esperado,
        'Faixa_Prazo_GFS': faixa,
        'Momento_Extracao_Local': data_extracao_local,
        'Confianca_Prazo': confianca_prazo(prazo),    # [V4 B8/M05-17]
        'fonte': FONTE_GFS,                           # [V4 B8/M05-17]
        'janela_chuva_utc': JANELA_CHUVA_00_24,       # [V4 B8/M05-17]
        'matriz_gfs': MATRIZ_GFS_ROTULO,              # [V4 B8/M05-17]
        'metodo_temp_gfs': metodo,                    # [V4.1 K7] 'aditivo' ou 'variancia'
        'metodo_ur_rs_gfs': METODO_UR_RS_GFS,         # [K9A] 'original' ou 'variancia'
        'teto_razao_temp_gfs': float(teto_razao_temp(faixa)),   # [K11] 2.0 nos prazos 1-5; 1.0 do 6 em diante
    }
    final_ok = finalizar(img_ok, dict(comuns, versao=versao_ok, Imagens_Validas_GFS=qtd_img,
                                      Registro_Servidor_GEE=registro_gee))
    final_falha = finalizar(img_falha, dict(comuns, versao='falha_latencia_gfs', Imagens_Validas_GFS=0,
                                            Registro_Servidor_GEE='N/A'))
    return ee.Image(ee.Algorithms.If(qtd_img.gt(0), final_ok, final_falha))

# =========================================================================
# 6. ORQUESTRAÇÃO
# =========================================================================
print("==========================================================")
print(f"🕹️ CENTRO OPERACIONAL SAB {VERSAO_ALGORITMO} - TASK MANAGER {PROJECT_ID_ATIVO}")
print("==========================================================")

faltam_matriz = [m for m in range(1, 13)
                 if not asset_existe(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{m:02d}')]
if faltam_matriz:
    raise RuntimeError(f"❌ A matriz {ASSET_DESTINO_MATRIZ_GFS} não tem os meses {faltam_matriz}. "
                       "Rode o script da matriz GFS V2 e espere as 12 tarefas terminarem.")

# [V4 B3/M05-07] Um só getInfo com bandas e propriedades dos 12 meses. Exige as 48 bandas de média
# {v}_m_{sicsb|gfs}_{faixa} e versao_matriz = 'V2.1'. Uma matriz deixada por um 03 antigo seria usada
# sem aviso (o pacote v1 tinha a radiação antiga). As bandas ficam no cache de bandas_matriz_gfs().
_meses_matriz = [f'{m:02d}' for m in range(1, 13)]
_info_matriz = ee.List([
    ee.List([ee.Image(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{mm}').bandNames(),
             ee.Image(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{mm}').toDictionary()])
    for mm in _meses_matriz]).getInfo()
_problemas_matriz = []
for _mm, (_bandas, _props) in zip(_meses_matriz, _info_matriz):
    _cache_bandas_gfs[_mm] = _bandas
    _exigidas = BANDAS_MEDIA_GFS + BANDAS_DESVIO_TEMP + BANDAS_DESVIO_UR_RS             # [V4.1 K7] + [K9A] desvios
    _faltam = [b for b in _exigidas if b not in _bandas]
    if _faltam:
        _problemas_matriz.append(f"mês {_mm} sem {len(_faltam)} das {len(_exigidas)} "
                                 f"bandas de média e de desvio (ex.: {_faltam[:3]})")
    if (_props or {}).get('versao_matriz') != VERSAO_MATRIZ_GFS:
        _problemas_matriz.append(f"mês {_mm} com versao_matriz = {(_props or {}).get('versao_matriz')!r} "
                                 f"(esperado '{VERSAO_MATRIZ_GFS}')")
if _problemas_matriz:
    raise RuntimeError(f"❌ A matriz {ASSET_DESTINO_MATRIZ_GFS} não é a {VERSAO_MATRIZ_GFS} que o motor "
                       f"{VERSAO_ALGORITMO} exige: " + '; '.join(_problemas_matriz)
                       + ". Apague os meses antigos, rode o 03 (matriz V2.1) e espere as 12 tarefas terminarem.")
_p01 = _info_matriz[0][1] or {}
print(f"✅ Matriz GFS {VERSAO_MATRIZ_GFS}: 12 meses com as {len(BANDAS_MEDIA_GFS)} bandas de média e as "
      f"{len(BANDAS_DESVIO_TEMP) + len(BANDAS_DESVIO_UR_RS)} de desvio da Tmax, da Tmin, da UR e da radiação "
      f"(modelo {_p01.get('modelo_gfs', '?')}, rodadas desde {_p01.get('inicio_rodadas', '?')}, "
      f"dias até {_p01.get('fim_dias', '?')}).")
print(f"   Correção da Tmax/Tmin nos dias GFS: {METODO_TEMP_GFS} (METODO_TEMP_GFS; a PRÉVIA 6 compara com a outra).")
print(f"   Correção da UR e da radiação nos dias GFS: {METODO_UR_RS_GFS} (METODO_UR_RS_GFS; auditoria K9A).")
print(f"   Teto da razão dos desvios da Tmax/Tmin: {RAZAO_DESVIO_MAX} nos prazos 1 a 5 e {RAZAO_DESVIO_MAX_LONGO} "
      f"do 6 em diante (RAZAO_DESVIO_MAX_LONGO; validação K11).")

# [V4 C2/M05-03] A máscara canônica vem de um dia do histórico; sem ele, toda exportação falharia.
if not asset_existe(f'{ASSET_DESTINO}/{id_dia(DIA_MASCARA_CANONICA)}'):
    raise RuntimeError(f"❌ Não encontrei {ASSET_DESTINO}/{id_dia(DIA_MASCARA_CANONICA)}, de onde vem a máscara "
                       "canônica (cobertura do histórico) aplicada a todos os dias novos.")

garantir_colecao(ASSET_DESTINO)
garantir_colecao(ASSET_TEMP)

tarefas = listar_tarefas_ativas()
finalizar_trocas_pendentes(tarefas)

print(f"🔍 Mapeando inventário de {ASSET_DESTINO}...")
inventario = mapear_colecao()
capacidade = max(0, LIMITE_TAREFAS_MAX - len(tarefas))
print(f"📊 Fila: {len(tarefas):,} tarefas ativas | {capacidade:,} vagas | {len(inventario):,} dias no acervo.\n")

def status_dia(d_str, info):
    if info is None:
        return 'ausente'
    v, alg = info['versao'], info['alg']
    if v in VERSOES_GFS:
        return 'precisa_upgrade' if d_str <= ultima_data_era5 else 'gravado'
    if v == 'provisoria_era5':
        # [V4 B5/M05-04] limite_def, não ultima_data_brd: sem CONVERTER_EM_DEFINITIVO, um dia depois
        # de DATA_LIMITE_PROTECAO nunca vira definitivo, mesmo que o BR-DWGD já o cubra
        if d_str <= limite_def:
            return 'precisa_upgrade'      # o BR-DWGD já cobre o dia: vira definitivo
        if alg != VERSAO_ALGORITMO:
            return 'precisa_upgrade'      # provisórios acompanham sempre a versão atual
        return 'gravado'
    # Dias definitivos: só mudam por decisão explícita (REPROCESSAR_VERSAO_ANTIGA ou patch)
    if REPROCESSAR_VERSAO_ANTIGA and alg != VERSAO_ALGORITMO:
        return 'precisa_upgrade'
    if alg not in ALGORITMOS_DEFINITIVOS_VALIDOS:
        return 'precisa_upgrade'          # dias da V1.1 (fórmula de calibração diferente)
    if alg == 'V1.0' and APLICAR_PATCH_SOLO:
        return 'precisa_patch'
    return 'gravado'

def exportar(img, d_str, usar_tmp):
    global capacidade
    nome = id_dia(d_str)
    desc = desc_dia(d_str)
    if dia_protegido(nome):   # [V4 M05-19] última barreira: os chamadores já conferem a trava
        raise RuntimeError(f"❌ Trava do histórico: exportação de {nome} bloqueada (dia até "
                           f"{DATA_LIMITE_PROTECAO} ou nome fora do padrão).")
    destino = f'{ASSET_TEMP if usar_tmp else ASSET_DESTINO}/{nome}'
    task = ee.batch.Export.image.toAsset(
        image=img, description=desc, assetId=destino,
        region=limitesRegiao, crs=crsNativo, crsTransform=transformNativo, maxPixels=1e13)
    task.start()
    tarefas[desc] = task.id
    capacidade -= 1
    return task

def aguardar_tarefa(desc):
    global capacidade
    task_id = tarefas.get(desc)
    if task_id is None:
        return 'COMPLETED'
    limite = time.time() + TIMEOUT_TAREFA_MIN * 60
    while True:
        estado = ee.data.getTaskStatus(task_id)[0].get('state')
        if estado in ESTADOS_FINAIS:
            tarefas.pop(desc, None)
            capacidade += 1
            return estado
        if time.time() > limite:
            raise TimeoutError(f"Tarefa {desc} excedeu {TIMEOUT_TAREFA_MIN} min (estado: {estado}).")
        time.sleep(INTERVALO_POLL_S)

def aguardar_dia_pronto(d_str):
    nome, desc = id_dia(d_str), desc_dia(d_str)
    if desc in tarefas:
        print(f"    ⏳ Aguardando tarefa do dia base {d_str}...")
        estado = aguardar_tarefa(desc)
        if estado != 'COMPLETED':
            raise RuntimeError(f"Dia base {d_str} terminou com estado {estado}; cadeia GFS interrompida.")
    promover_tmp(nome)
    if not asset_existe(f'{ASSET_DESTINO}/{nome}'):
        raise RuntimeError(f"Dia base {d_str} não existe no acervo e não há tarefa ativa para ele.")

def despachar_assincrono(datas, rotulo, reserva):
    global capacidade
    print(f"🔎 {rotulo}: {len(datas):,} dias avaliados.")
    enviados, por_ano = [], {}
    for d in datas:
        st_ano = por_ano.setdefault(d[:4], {'gravado': 0, 'fila': 0, 'enviado': 0, 'adiado': 0, 'protegido': 0})
        nome, desc = id_dia(d), desc_dia(d)
        if desc in tarefas:
            st_ano['fila'] += 1
            continue
        status = status_dia(d, inventario.get(nome))
        if status == 'gravado':
            st_ano['gravado'] += 1
            continue
        if PROTEGER_HISTORICO and d <= DATA_LIMITE_PROTECAO:
            st_ano['protegido'] += 1
            info = inventario.get(nome)
            situacao = 'ausente no SAB_V1' if info is None else f"{info['versao']} {info['alg']}"
            motivo = f"{status} ({situacao})"
            relatorio_protegidos[motivo] = relatorio_protegidos.get(motivo, 0) + 1
            continue
        if capacidade <= reserva:
            st_ano['adiado'] += 1
            continue
        if SIMULAR:
            info = inventario.get(nome)
            rota = 'definitiva' if d <= limite_def else 'provisoria_era5'   # [V4 B5/M05-04]
            if status == 'precisa_patch':
                motivo = f"patch solo/escoamento ({info['versao']}, V1.0 -> {VERSAO_PATCH})"
            elif info is None:
                motivo = f"criar ({rota})"
            else:
                motivo = f"recalcular {info['versao']} {info['alg']} -> {rota} {VERSAO_ALGORITMO}"
            relatorio_sim[motivo] = relatorio_sim.get(motivo, 0) + 1
            capacidade -= 1
            st_ano['enviado'] += 1
            enviados.append(d)
            continue
        if status == 'precisa_patch':
            img = aplicarPatch_Solo(d)
        else:
            img = processarDia_Definitivo(d) if d <= limite_def else processarDia_Rota1(d)   # [V4 B5/M05-04]
        exportar(img, d, usar_tmp=(status != 'ausente'))
        st_ano['enviado'] += 1
        enviados.append(d)
    for ano, s in sorted(por_ano.items()):
        if s['enviado'] or s['adiado'] or s['fila'] or s['protegido']:
            print(f"  📅 [{ano}] gravados {s['gravado']:,} | na fila {s['fila']:,} | "
                  f"enviados {s['enviado']:,} | adiados por capacidade {s['adiado']:,} | "
                  f"protegidos {s['protegido']:,}")
    return enviados

def descobrir_rodadas_gfs():
    # A busca precisa cobrir todo o intervalo sem ERA5, senão dias passados ficam sem rodada
    lacuna = (data_hoje_dt.date() - datetime.strptime(ultima_data_era5, '%Y-%m-%d').date()).days
    dias_busca = max(DIAS_BUSCA_RODADAS, lacuna + 3)
    ini = (data_hoje_dt - timedelta(days=dias_busca)).strftime('%Y-%m-%d')
    fim = (data_hoje_dt + timedelta(days=1)).strftime('%Y-%m-%d')
    col = ee.ImageCollection(COL_GFS).filterDate(ini, fim)
    rodadas = col.aggregate_array('creation_time').distinct().getInfo()
    # [V4 B1/M05-08] Só rodadas 00Z, como na matriz (03). A V1.4 aceitava 06/12/18Z: com 12Z, o 1º dia
    # previsto tinha 12 h e 2 blocos, e o prazo não batia com as faixas da matriz.
    rodadas_00z = sorted({int(float(r)) for r in (rodadas or []) if eh_rodada_00z(int(float(r)))})
    if not rodadas_00z:
        print("  ⚠️ Nenhuma rodada GFS 00Z no período de busca: os dias GFS não serão processados "
              "nesta execução (os existentes ficam como estão).")
        return [], [], None

    # [V4 B1/M05-08] Uma só consulta conta, em cada rodada 00Z, as horas distintas de 1 a 384 h
    # esperadas (HORAS_RODADA_COMPLETA, 208). A V1.4 contava as imagens com a hora 0 e aceitava >= 198,
    # olhando só as 4 últimas rodadas (um getInfo por rodada). Padrões: filtro inList com horas
    # inteiras (como o 03) e aggregate_array(...).distinct().
    # [V4 A-02] Horas inteiras (inList com inteiros comprovado no 03 e no F3 da auditoria).
    col_saidas = col.filter(ee.Filter.inList('forecast_hours', HORAS_RODADA_COMPLETA))
    contagens = ee.List(rodadas_00z).map(
        lambda r: col_saidas.filter(ee.Filter.eq('creation_time', r))
        .aggregate_array('forecast_hours').distinct().size()).getInfo()
    rodadas_00z, completas, referencia = selecionar_rodadas(rodadas_00z, contagens)

    incompletas = [f"{ms_para_data(r)} ({n}/{N_SAIDAS_RODADA})"
                   for r, n in zip(rodadas_00z, contagens) if r not in completas]
    print(f"  🛰️ Rodadas 00Z na janela ({ini} a {fim}): {len(rodadas_00z)} | completas "
          f"({N_SAIDAS_RODADA} saídas de 1 a 384 h): {len(completas)}"
          + (f" | incompletas: {', '.join(incompletas)}" if incompletas else ""))
    if referencia is None:
        print("  ⚠️ Nenhuma rodada 00Z completa na janela: os dias GFS não serão processados nesta "
              "execução (os existentes ficam como estão). Rode de novo mais tarde.")
        return rodadas_00z, completas, None
    print(f"  🛰️ Rodada GFS de referência: "
          f"{datetime.fromtimestamp(referencia / 1000, tz=timezone.utc).strftime('%Y-%m-%d %HZ')}")
    return rodadas_00z, completas, referencia

def referencia_balde(ultima_era5):
    """Razões ET real/ETp e transpiração/ET real dos últimos DIAS_REF_ET dias ERA5,
    e a umidade do último dia ERA5, por pixel."""
    ini = somar_dias(ultima_era5, -(DIAS_REF_ET - 1))
    col = ee.ImageCollection(ASSET_DESTINO).filterDate(ini, somar_dias(ultima_era5, 1))
    et_r = col.select('et_real').mean()
    et_p = col.select('et_potencial').mean()
    tr = col.select('transpiracao_mm').mean()
    base = ee.Image(f'{ASSET_DESTINO}/{id_dia(ultima_era5)}')
    return ee.Image.cat([
        et_r.divide(et_p.max(0.1)).clamp(0.05, 1.0).rename('k_et'),
        tr.divide(et_r.max(0.05)).clamp(0.0, 1.0).rename('f_transp'),
        base.select('soil_moisture_0_100cm_m3_m3').multiply(1000).rename('sw_ref_100'),
        base.select('soil_moisture_0_5cm_m3_m3').multiply(50).rename('sw_ref_5'),
    ])

# [V4 B2] Rodadas completas, referência e fim do horizonte da cadeia, guardados para a PRÉVIA 6
contexto_gfs = {}

def executar_cadeia_gfs(enviados_operacionais):
    global data_fim_processo
    dias = intervalo_datas(somar_dias(ultima_data_era5, 1), data_fim_processo)
    if not dias:
        return
    print("\n⚙ Cadeia GFS sequencial (só rodadas 00Z completas):")
    _, completas, referencia = descobrir_rodadas_gfs()
    if referencia is None:   # [V4 B1] sem rodada 00Z completa: nenhum dia GFS nesta execução
        contexto_gfs.update(completas=completas, referencia=None, fim=None)
        if SIMULAR:
            motivo = 'GFS não processado (nenhuma rodada 00Z completa)'
            relatorio_sim[motivo] = relatorio_sim.get(motivo, 0) + 1
        return
    # [V4 B1-horizonte] fim = min(hoje + 15, dia da referência + 15): o prazo 16 da referência
    data_fim_processo = fim_horizonte(data_hoje_str, referencia)
    dias = intervalo_datas(somar_dias(ultima_data_era5, 1), data_fim_processo)
    contexto_gfs.update(completas=completas, referencia=referencia, fim=data_fim_processo)
    if not dias:
        return
    print(f"  📆 Dias GFS: {dias[0]} a {dias[-1]} ({len(dias)} dias; o último é o prazo "
          f"L{prazo_L(data_para_ms(dias[-1]), referencia)} da referência).")

    dias_ref = intervalo_datas(somar_dias(ultima_data_era5, -(DIAS_REF_ET - 1)), ultima_data_era5)
    ref = None
    if not SIMULAR:
        for d_ref in dias_ref:            # a referência precisa estar com as versões finais
            aguardar_dia_pronto(d_ref)
        ref = referencia_balde(ultima_data_era5)
    forcar = any(d_ref in enviados_operacionais for d_ref in dias_ref)

    for d in dias:
        nome, desc = id_dia(d), desc_dia(d)
        caminho = f'{ASSET_DESTINO}/{nome}'
        if desc in tarefas and not SIMULAR:
            aguardar_tarefa(desc)
            promover_tmp(nome)

        rodada = rodada_para_dia(d, completas, referencia)          # [V4 B1/M05-09]
        if rodada is None:
            # [V4 B1] Nenhuma rodada 00Z completa cobre o dia: a cadeia do balde não pode pular um dia
            print(f"    ⚠️ {d}: nenhuma rodada 00Z completa cobre o dia; cadeia GFS interrompida aqui "
                  f"(os dias seguintes ficam como estão).")
            if SIMULAR:
                motivo = 'GFS interrompido (dia sem rodada 00Z completa)'
                relatorio_sim[motivo] = relatorio_sim.get(motivo, 0) + 1
            break
        dia_ms = data_para_ms(d)
        n_img, horas_chuva = contagem_esperada(dia_ms, rodada)
        prazo = prazo_L(dia_ms, rodada)
        faixa = faixa_prazo(dia_ms, rodada)
        info = info_de_propriedades(propriedades_asset(caminho))
        precisa = precisa_refazer_gfs(info, rodada, forcar, len(horas_chuva), faixa)   # [V4 M05-09] [K11]
        if not precisa:
            print(f"    ✔️ {d}: atualizado com a rodada esperada.")
            continue
        forcar = True   # estado do solo mudou: todos os dias seguintes precisam ser refeitos
        if SIMULAR:
            motivo = 'criar (GFS)' if info is None else f"refazer {info['versao']} -> GFS"
            relatorio_sim[motivo] = relatorio_sim.get(motivo, 0) + 1
            continue

        d_ant = somar_dias(d, -1)
        aguardar_dia_pronto(d_ant)
        base = ee.Image(f'{ASSET_DESTINO}/{id_dia(d_ant)}')
        estado = ee.Image.cat([
            base.select('soil_moisture_0_100cm_m3_m3').multiply(1000).rename('sw_100'),
            base.select('soil_moisture_0_5cm_m3_m3').multiply(50).rename('sw_5'),
        ])

        img = processarDia_GFS(d, estado, ref, rodada, n_img, horas_chuva, faixa, prazo)   # [V4 B8] prazo
        usar_tmp = info is not None
        exportar(img, d, usar_tmp)
        estado_final = aguardar_tarefa(desc)
        if estado_final != 'COMPLETED':
            raise RuntimeError(f"Falha na cadeia GFS: {desc} terminou com {estado_final}.")
        if usar_tmp:
            promover_tmp(nome)
        print(f"    ✔️ {d}: exportado (rodada {ms_para_data(rodada)} 00Z, prazo L{prazo}, faixa {faixa}, "
              f"confiança {confianca_prazo(prazo)}, {n_img} imagens esperadas, {len(horas_chuva)} blocos de chuva).")

# =========================================================================
# 7. PRÉVIA DA V1.5 (só no modo simulação; nada é gravado)
# [V4] Nos dias provisórios ERA5, a V1.5 grava o mesmo que a V1.4 (só a umidade muda em relação aos
# dias V1.3 do acervo); os rótulos passam a usar VERSAO_ALGORITMO. [V4 B2] PRÉVIA 6: rota GFS.
# =========================================================================
# Estados de cada região com os nomes usados pelo FAO/GAUL 2015 (sem acentos)
UFS_REGIAO = {
    'Norte': ['Acre', 'Amapa', 'Amazonas', 'Para', 'Rondonia', 'Roraima', 'Tocantins'],
    'Nordeste': ['Alagoas', 'Bahia', 'Ceara', 'Maranhao', 'Paraiba', 'Pernambuco', 'Piaui',
                 'Rio Grande Do Norte', 'Sergipe'],
    'Centro-Oeste': ['Distrito Federal', 'Goias', 'Mato Grosso', 'Mato Grosso Do Sul'],
    'Sudeste': ['Espirito Santo', 'Minas Gerais', 'Rio De Janeiro', 'Sao Paulo'],
    'Sul': ['Parana', 'Rio Grande Do Sul', 'Santa Catarina'],
}
CODIGO_REGIAO = {reg: k for k, reg in enumerate(UFS_REGIAO, start=1)}   # 0 = pixel fora das UFs listadas
BANDAS_PREVIA = list(ORDEM_BANDAS)   # as 16 bandas do SAB
# O que a V1.4 faz com cada banda dos dias provisórios gravados pela V1.4:
BANDAS_MUDAM = ('soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3')   # ERA5 agora bilinear
BANDAS_SOLO = BANDAS_MUDAM   # usadas na marca f_solo (pixel com umidade alterada)
BANDAS_IGUAIS = tuple(b for b in BANDAS_PREVIA if b not in BANDAS_MUDAM)       # mesma conta, mesmos dados
assert sorted(BANDAS_MUDAM + BANDAS_IGUAIS) == sorted(BANDAS_PREVIA)
GRUPO_BANDA = {**{b: f'muda na {VERSAO_ALGORITMO}' for b in BANDAS_MUDAM},   # [V4] rótulo da versão
               **{b: 'deve ficar igual' for b in BANDAS_IGUAIS}}
UNIDADE_BANDA = {'pr_mm': 'mm', 'tmax_C': '°C', 'tmin_C': '°C', 'RH': '%', 'et_potencial': 'mm',
                 'et_real': 'mm', 'vpd': 'kPa', 'rs': 'MJ/m²', 'u2': 'm/s', 'tsolo_C': '°C',
                 'tfolha_C': '°C', 'transpiracao_mm': 'mm', 'runoff_sup_mm': 'mm', 'runoff_sub_mm': 'mm',
                 'soil_moisture_0_5cm_m3_m3': 'm³/m³', 'soil_moisture_0_100cm_m3_m3': 'm³/m³'}
# Diferença mínima, na unidade da banda, para um pixel contar como alterado
TOLERANCIA_PREVIA = {b: 0.01 for b in BANDAS_PREVIA}
TOLERANCIA_PREVIA.update({'RH': 0.1, 'vpd': 0.001, 'soil_moisture_0_5cm_m3_m3': 0.001,
                          'soil_moisture_0_100cm_m3_m3': 0.001})
# Coerência física de cada imagem (fração de pixels com o problema)
COERENCIA = {
    'etr_acima_eto': 'ET real acima da ETo',
    'transp_acima_etr': 'transpiração acima da ET real',
    'tmax_abaixo_tmin': 'Tmax abaixo da Tmin',
    'ur_fora': 'UR fora de 0 a 100%',
    'umid_acima_teto': f'umidade do solo acima de {UMIDADE_MAX_FISICA}',
}
# Bandas somadas pela prévia, na ordem do redutor: a_ = como o painel mostra hoje, n_ = V1.4,
# d_ = |V1.4 - hoje|, f_ = 1 se o pixel mudou mais que a tolerância. n_pix vale 1 em cada pixel
# válido: a soma dele é a contagem de pixels, e média = soma da banda / soma de n_pix.
NOMES_SOMA = ([f'{p}_{b}' for p in ('a', 'n', 'd', 'f') for b in BANDAS_PREVIA]
              + ['a_deficit', 'n_deficit', 'clim_eto', 'f_solo']
              + [f'{p}_{c}' for p in ('a', 'n') for c in COERENCIA] + ['n_pix'])
# Tentativas de cálculo de cada dia: (n, tileScale) = retângulo do Brasil cortado em n x n partes.
# Se o Earth Engine recusar por memória ou tempo, passa para a tentativa seguinte, com partes
# menores; as somas das partes fecham exatamente com a do retângulo inteiro.
NIVEIS_PREVIA = ((1, 4), (2, 16), (4, 16))

# Critérios de aprovação, definidos antes de rodar. A V1.4 só troca a reamostragem da umidade
# do solo (vizinho mais próximo -> bilinear) no mesmo campo do ERA5: a média regional quase não
# deve mudar; mudança grande indica erro. As outras 14 bandas devem sair idênticas.
CRIT_SOLO_BRASIL = 2.0               # |variação| máxima da umidade média do Brasil (%) [V4 B4/M05-05: era 5.0]
CRIT_SOLO_REGIAO = 10.0              # |variação| máxima da umidade média de cada região (%)
CRIT_MAX_PIXELS_IGUAIS = 0.5         # % máxima de pixels alterados nas bandas que devem ficar iguais
CRIT_MAX_INCOERENCIA = 0.01          # % máxima de pixels incoerentes na V1.4 (pelo código, deve ser 0)
CRIT_MIN_DIAS = 2 / 3                # fração mínima dos dias amostrados que precisa ser calculada
CRIT_MIN_COBERTURA = 0.95            # as cinco regiões juntas precisam ter 95% dos pixels do Brasil

def _imagem_como_no_painel(d):
    """O dia gravado como o painel o mostra hoje: nos dias da V1.0 o painel aplica, na leitura,
    a correção de umidade e escoamento, que é a mesma do aplicarPatch_Solo."""
    info = inventario.get(id_dia(d))
    if info is not None and info['alg'] == 'V1.0':
        return aplicarPatch_Solo(d)
    return ee.Image(f'{ASSET_DESTINO}/{id_dia(d)}')

def _rotulo_regioes():
    """Imagem com o código da região de cada pixel (1 a 5, na ordem de UFS_REGIAO; 0 = pixel fora
    das UFs listadas). Os estados são pintados na grade, sem unir polígonos: a união
    (FeatureCollection.geometry) é a operação que o Earth Engine desaconselha por consumir muita
    memória, e era feita a cada dia na versão anterior da prévia. Usa a versão do GAUL 2015
    simplificada a 500 m (mesmos nomes e atributos), mais leve e suficiente para pixels de 11 km;
    o recorte do Brasil continua vindo das próprias imagens do SAB."""
    estados = (ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level1')
               .filter(ee.Filter.eq('ADM0_NAME', 'Brazil')))
    nomes_gaul = set(estados.aggregate_array('ADM1_NAME').getInfo())
    rotulo = ee.Image.constant(0).toByte()
    for reg, ufs in UFS_REGIAO.items():
        faltam = [u for u in ufs if u not in nomes_gaul]
        if faltam:
            print(f"   ⚠️ {reg}: estados não encontrados no GAUL, fora da prévia: {faltam}")
        rotulo = rotulo.paint(estados.filter(ee.Filter.inList('ADM1_NAME', ufs)), CODIGO_REGIAO[reg])
    return rotulo.rename('cod_regiao')

def _retangulos_previa(limites, n):
    """Retângulo do Brasil cortado em n x n partes, com os cortes sobre as linhas da grade de 0,1°
    do SAB: cada pixel cai em uma única parte. limites = (oeste, sul, leste, norte), em graus."""
    oeste, sul, leste, norte = limites
    dx, x0 = transformNativo[0], transformNativo[2]
    dy, y0 = -transformNativo[4], transformNativo[5]
    c0, c1 = math.floor((oeste - x0) / dx), math.ceil((leste - x0) / dx)
    l0, l1 = math.floor((y0 - norte) / dy), math.ceil((y0 - sul) / dy)
    cols = [c0 + round(i * (c1 - c0) / n) for i in range(n + 1)]
    lins = [l0 + round(i * (l1 - l0) / n) for i in range(n + 1)]
    return [[x0 + ca * dx, y0 - lb * dy, x0 + cb * dx, y0 - la * dy]
            for la, lb in zip(lins, lins[1:]) for ca, cb in zip(cols, cols[1:])]

def _coerencia(img):
    """Marca, pixel a pixel, os problemas físicos listados em COERENCIA (1 = problema)."""
    teto = UMIDADE_MAX_FISICA + 1e-4
    return ee.Image.cat([
        img.select('et_real').gt(img.select('et_potencial').add(0.001)),
        img.select('transpiracao_mm').gt(img.select('et_real').add(0.001)),
        img.select('tmax_C').lt(img.select('tmin_C')),
        img.select('RH').lt(0).Or(img.select('RH').gt(100)),
        img.select('soil_moisture_0_100cm_m3_m3').gt(teto).Or(img.select('soil_moisture_0_5cm_m3_m3').gt(teto)),
    ]).rename(list(COERENCIA))

def _pilha_previa(d, rotulo):
    """As 16 bandas do dia como estão hoje (a_*) e como a V1.4 gravaria (n_*), a diferença (d_*),
    a marca de pixel alterado (f_*), déficits, ETo climatológica do mês, coerência física, n_pix e,
    por último, o código da região."""
    antigo = _imagem_como_no_painel(d).select(BANDAS_PREVIA)
    novo = processarDia_Rota1(d).select(BANDAS_PREVIA)
    clima_eto = expandir_borda(ee.Image(f'{ASSET_CLIMATOLOGIA}/Matriz_Clima_{d[5:7]}').select('ET_m_br'))

    def deficit(img):
        return img.select('et_potencial').subtract(img.select('et_real'))

    dif = novo.subtract(antigo).abs().rename(BANDAS_PREVIA)      # banda a banda, na mesma ordem
    mudou = dif.gt(ee.Image.constant([TOLERANCIA_PREVIA[b] for b in BANDAS_PREVIA])).rename(BANDAS_PREVIA)

    pilha = ee.Image.cat([
        antigo.rename([f'a_{b}' for b in BANDAS_PREVIA]),
        novo.rename([f'n_{b}' for b in BANDAS_PREVIA]),
        dif.rename([f'd_{b}' for b in BANDAS_PREVIA]),
        mudou.rename([f'f_{b}' for b in BANDAS_PREVIA]),
        deficit(antigo).rename('a_deficit'),
        deficit(novo).rename('n_deficit'),
        clima_eto.rename('clim_eto'),
        mudou.select(list(BANDAS_SOLO)).reduce(ee.Reducer.max()).rename('f_solo'),
        _coerencia(antigo).rename([f'a_{c}' for c in COERENCIA]),
        _coerencia(novo).rename([f'n_{c}' for c in COERENCIA]),
        ee.Image.constant(1).rename('n_pix'),
        rotulo,
    ]).select(NOMES_SOMA + ['cod_regiao'])
    # Uma só máscara para todas as bandas: hoje e V1.4 são comparados exatamente nos mesmos pixels.
    # Fora do Brasil as imagens do SAB são mascaradas, então o retângulo não soma oceano nem vizinhos.
    return pilha.updateMask(pilha.mask().reduce(ee.Reducer.min()))

class _PedidoGrande(Exception):
    """O Earth Engine recusou o pedido por memória ou por tempo."""

def _pedido_grande_demais(erro):
    msg = str(erro).lower()
    return 'memory' in msg or 'timed out' in msg

def _somas_regiao(pilha, retangulos, tile_scale):
    """Soma de cada banda de NOMES_SOMA por código de região, parte por parte (um pedido por parte)."""
    n = len(NOMES_SOMA)
    redutor = ee.Reducer.sum().repeat(n).group(groupField=n, groupName='cod_regiao')
    total = {}
    for ret in retangulos:
        geometria = ee.Geometry.Rectangle(ret, proj=crsNativo, geodesic=False)
        for tentativa in range(3):
            try:
                r = pilha.reduceRegion(reducer=redutor, geometry=geometria, crs=crsNativo,
                                       crsTransform=transformNativo, tileScale=tile_scale,
                                       maxPixels=1e10).getInfo()
                break
            except Exception as e:
                if _pedido_grande_demais(e):
                    raise _PedidoGrande(str(e)) from None
                if tentativa == 2:
                    raise
                time.sleep(15)   # falha passageira do servidor (ex.: 503 ou excesso de pedidos)
        for grupo in r.get('groups', []):
            cod = int(grupo['cod_regiao'])
            anterior = total.get(cod, [0.0] * n)
            total[cod] = [a + (s or 0.0) for a, s in zip(anterior, grupo['sum'])]
    return total

def _medias_previa(somas):
    """Converte as somas por código em médias por região; o Brasil soma todos os códigos, inclusive
    o 0. Região sem pixel nenhum fica de fora (e o resumo acusa a ausência)."""
    i_pix = NOMES_SOMA.index('n_pix')
    nome = {k: reg for reg, k in CODIGO_REGIAO.items()}

    def medias(v):
        saida = {b: v[i] / v[i_pix] for i, b in enumerate(NOMES_SOMA) if b != 'n_pix'}
        saida['n_pix'] = v[i_pix]
        return saida

    resultado = {nome[k]: medias(v) for k, v in somas.items() if k in nome and v[i_pix] > 0}
    brasil = [sum(col) for col in zip(*somas.values())]
    if brasil and brasil[i_pix] > 0:
        resultado['Brasil'] = medias(brasil)
    return resultado

def _previa_dia(d, rotulo, limites):
    """Médias regionais do dia como está hoje (a_*) e como a V1.5 gravaria (n_*). Se o Earth Engine
    recusar por memória ou tempo, refaz o mesmo cálculo em partes menores (NIVEIS_PREVIA)."""
    pilha = _pilha_previa(d, rotulo)
    for k, (n, tile_scale) in enumerate(NIVEIS_PREVIA):
        try:
            resultado = _medias_previa(_somas_regiao(pilha, _retangulos_previa(limites, n), tile_scale))
            if 'Brasil' not in resultado:
                raise RuntimeError(f"nenhum pixel válido em comum entre o dia gravado e a {VERSAO_ALGORITMO}")   # [V4]
            return resultado
        except _PedidoGrande as e:
            if k == len(NIVEIS_PREVIA) - 1:
                raise RuntimeError(f"{e} Recusado mesmo em {n * n} partes.") from None
            prox = NIVEIS_PREVIA[k + 1][0] ** 2
            print(f"   {d}: o Earth Engine recusou por memória ou tempo; refazendo em {prox} partes...")

def _resumir_previa(df, motivos_simulacao, dias_previstos=None):
    """Monta as tabelas da prévia e aplica os critérios da V1.5. Não usa o Earth Engine."""
    nv = VERSAO_ALGORITMO   # [V4] rótulo da versão nova nas tabelas (antes 'V1.4' fixo)
    ordem = [r for r in ['Brasil', *UFS_REGIAO] if r in set(df['regiao'])]
    br = df[df['regiao'] == 'Brasil'].set_index('data').sort_index()
    u5, u100 = 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3'
    por_data = pd.DataFrame({
        'Umid 0-5 hoje': br[f'a_{u5}'], f'Umid 0-5 {nv}': br[f'n_{u5}'],
        'ΔUmid 0-5 %': 100 * (br[f'n_{u5}'] / br[f'a_{u5}'] - 1),
        'Umid 0-100 hoje': br[f'a_{u100}'], f'Umid 0-100 {nv}': br[f'n_{u100}'],
        'ΔUmid 0-100 %': 100 * (br[f'n_{u100}'] / br[f'a_{u100}'] - 1),
        'ETo hoje': br['a_et_potencial'], f'ETo {nv}': br['n_et_potencial'],
    }).astype(float).round(4)

    g = df.groupby('regiao')
    soma = lambda col: g[col].sum()
    variacao = lambda a, n: 100 * (soma(n) / soma(a) - 1)
    por_regiao = pd.DataFrame({
        'ΔUmid 0-5 %': variacao(f'a_{u5}', f'n_{u5}'),
        'ΔUmid 0-100 %': variacao(f'a_{u100}', f'n_{u100}'),
        '% pixels solo alterado': 100 * g['f_solo'].mean(),
        'ΔETo %': variacao('a_et_potencial', 'n_et_potencial'),
        'ΔChuva %': variacao('a_pr_mm', 'n_pr_mm'),
    }).reindex(ordem).astype(float).round(3)

    # As 16 bandas no Brasil: média dos dias amostrados, hoje x versão nova
    hoje = pd.Series({b: br[f'a_{b}'].mean() for b in BANDAS_PREVIA}, dtype=float)
    v14 = pd.Series({b: br[f'n_{b}'].mean() for b in BANDAS_PREVIA}, dtype=float)
    n_alterados = pd.Series({b: br[f'f_{b}'].sum() for b in BANDAS_PREVIA}, dtype=float)
    todas = pd.DataFrame({
        'grupo': [GRUPO_BANDA[b] for b in BANDAS_PREVIA],
        'unid.': [UNIDADE_BANDA[b] for b in BANDAS_PREVIA],
        'hoje': hoje, nv: v14, 'Δ': v14 - hoje,                                  # [V4] rótulo nv
        'Δ %': 100 * (v14 / hoje.where(hoje.abs() > 1e-9) - 1),
        '% pixels alterados': pd.Series({b: 100 * br[f'f_{b}'].mean() for b in BANDAS_PREVIA}, dtype=float),
        '|Δ| onde mudou': pd.Series({b: br[f'd_{b}'].sum() / n_alterados[b] if n_alterados[b] > 0 else 0.0
                                     for b in BANDAS_PREVIA}, dtype=float),
    }, index=pd.Index(BANDAS_PREVIA, name='banda'))
    num = todas.columns[2:]
    todas[num] = todas[num].astype(float).round(4)

    coerencia = pd.DataFrame({
        'hoje (% pixels)': [100 * br[f'a_{c}'].mean() for c in COERENCIA],
        f'{nv} (% pixels)': [100 * br[f'n_{c}'].mean() for c in COERENCIA],   # [V4] rótulo nv
    }, index=pd.Index(list(COERENCIA.values()), name='verificação')).astype(float).round(3)

    falhas = []
    definitivos = [m for m in motivos_simulacao
                   if m.startswith('recalcular definitiva') or m.startswith('patch')]
    if definitivos:
        falhas.append(f"a execução mexeria em dias definitivos: {definitivos}")
    if 'Brasil' in por_regiao.index:
        b = por_regiao.loc['Brasil']
        for col in ('ΔUmid 0-5 %', 'ΔUmid 0-100 %'):
            if abs(b[col]) > CRIT_SOLO_BRASIL:
                falhas.append(f"{col} no Brasil = {b[col]:+.2f}% (limite ±{CRIT_SOLO_BRASIL:.0f}%)")
        for banda in BANDAS_IGUAIS:
            p = todas.loc[banda, '% pixels alterados']
            if p > CRIT_MAX_PIXELS_IGUAIS:
                falhas.append(f"{banda} mudou em {p:.2f}% dos pixels, mas a conta é a mesma da {nv} "
                              f"(limite {CRIT_MAX_PIXELS_IGUAIS}%)")                    # [V4] rótulo nv
        for chave, texto in COERENCIA.items():
            agora, novo = coerencia.loc[texto, 'hoje (% pixels)'], coerencia.loc[texto, f'{nv} (% pixels)']
            # Tmax < Tmin vem da calibração aditiva, igual nas duas versões: a nova só não pode piorar
            limite = agora + CRIT_MAX_INCOERENCIA if chave == 'tmax_abaixo_tmin' else CRIT_MAX_INCOERENCIA
            if novo > limite:
                falhas.append(f"{nv} com {texto} em {novo:.3f}% dos pixels (limite {limite:.3f}%)")   # [V4]
    else:
        falhas.append("a prévia não conseguiu calcular a média do Brasil")
    for r in UFS_REGIAO:
        if r not in por_regiao.index:
            falhas.append(f"a prévia não conseguiu calcular a região {r}")
            continue
        for col in ('ΔUmid 0-5 %', 'ΔUmid 0-100 %'):
            v = por_regiao.loc[r, col]
            if abs(v) > CRIT_SOLO_REGIAO:
                falhas.append(f"{col} no {r} = {v:+.2f}% (limite ±{CRIT_SOLO_REGIAO:.0f}%)")
    # Controles da própria prévia: dias suficientes e regiões cobrindo o país
    n_dias = df['data'].nunique()
    if dias_previstos and n_dias < math.ceil(CRIT_MIN_DIAS * dias_previstos):
        falhas.append(f"só {n_dias} de {dias_previstos} dias foram calculados "
                      f"(mínimo {math.ceil(CRIT_MIN_DIAS * dias_previstos)})")
    if 'n_pix' in df.columns and 'Brasil' in set(df['regiao']):
        pix = df.pivot_table(index='data', columns='regiao', values='n_pix', aggfunc='sum')
        regs = [r for r in UFS_REGIAO if r in pix.columns]
        cobertura = (pix[regs].sum(axis=1) / pix['Brasil']).min() if regs else 0.0
        if cobertura < CRIT_MIN_COBERTURA:
            falhas.append(f"as regiões cobrem só {100 * cobertura:.0f}% dos pixels do Brasil "
                          f"(mínimo {100 * CRIT_MIN_COBERTURA:.0f}%)")
    return por_data, por_regiao, todas, coerencia, falhas

# [V4 B2/M05-06] PRÉVIA 6: a rota GFS calculada em memória (nada é exportado). Até a V1.4, a simulação
# saía da cadeia GFS antes de chamar processarDia_GFS, e a etapa 5a nunca exercitava a matriz, os
# blocos de 6 h nem a calibração do GFS.
TMAX_RECORDE_BR = 44.8      # °C: recorde nacional de temperatura máxima do INMET
SALTO_MAX_TMAX = 2.0        # °C: |Tmax máx nacional do 1º dia GFS - a do último dia ERA5| (J5: +2,4)
BANDAS_PREVIA_GFS = ('tmax_C', 'pr_mm', 'rs', 'et_potencial')
COLUNAS_PREVIA_GFS = {('tmax_C', 'mean'): 'Tmax média °C', ('tmax_C', 'max'): 'Tmax máx °C',
                      ('pr_mm', 'mean'): 'Chuva média mm', ('rs', 'mean'): 'Rs média MJ/m²',
                      ('et_potencial', 'mean'): 'ETo média mm'}

def dias_previa_gfs(primeiro_dia, referencia_ms, fim):
    """1º dia GFS e os dias de prazo L2, L8 e L11 da rodada de referência, sem repetir, dentro da cadeia.
    [V4.1 revisão V41-09] O L8 cobre a faixa L6a10, onde a K7 mediu o máximo +2,9 °C acima do BR-DWGD."""
    ref_dia = ms_para_data(referencia_ms)
    saida = []
    for d in (primeiro_dia, somar_dias(ref_dia, 1), somar_dias(ref_dia, 7), somar_dias(ref_dia, 10)):
        if primeiro_dia <= d <= fim and d not in saida:
            saida.append(d)
    return saida

def _estado_previa_gfs(base):
    """Estado do solo e referência do balde montados em memória a partir do último dia ERA5. Encadear
    o balde por 10 dias em memória seria pesado; chuva, Tmax, radiação e ETo, que a PRÉVIA 6 compara,
    não dependem do balde, então todos os dias da prévia partem deste mesmo estado."""
    estado = ee.Image.cat([
        base.select('soil_moisture_0_100cm_m3_m3').multiply(1000).rename('sw_100'),
        base.select('soil_moisture_0_5cm_m3_m3').multiply(50).rename('sw_5'),
    ])
    ref = ee.Image.cat([
        ee.Image.constant(0.5).rename('k_et'), ee.Image.constant(0.5).rename('f_transp'),
        estado.select('sw_100').rename('sw_ref_100'), estado.select('sw_5').rename('sw_ref_5'),
    ])
    return estado, ref

def _nacional_gfs(partes, extras):
    """Média e máximo nacionais de cada banda de cada parte (prefixo, imagem, bandas) num só pedido.
    Cada banda reduz com a sua própria máscara. extras: valores do servidor lidos no mesmo pedido."""
    pilha = ee.Image.cat([img.select(list(bandas)).rename([f'{p}__{b}' for b in bandas])
                          for p, img, bandas in partes])
    redutor = ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True)
    for tile_scale in (4, 16):
        try:
            r = ee.Dictionary(dict(extras, est=pilha.reduceRegion(
                reducer=redutor, geometry=limitesRegiao, crs=crsNativo, crsTransform=transformNativo,
                tileScale=tile_scale, maxPixels=1e10))).getInfo()
            break
        except Exception as e:
            if tile_scale == 16 or not _pedido_grande_demais(e):
                raise
            print("   o Earth Engine recusou por memória ou tempo; refazendo com tileScale 16...")
    est = r.pop('est', None) or {}
    valores = {}
    for p, _, bandas in partes:
        for b in bandas:
            for estat in ('mean', 'max'):
                valores[(p, b, estat)] = est.get(f'{p}__{b}_{estat}')
    return valores, r

def executar_previa_gfs():
    """[V4 B2/M05-06] Calcula em memória o 1º dia GFS e os dias de prazo L2, L8 e L11 da referência.
    Devolve {'tabela', 'linhas', 'falhas'}: as falhas entram no veredito da PRÉVIA 5."""
    nv = VERSAO_ALGORITMO
    res = {'tabela': None, 'linhas': [], 'falhas': []}

    def criterio(ok, texto):
        res['linhas'].append(f"{'✅' if ok else '⚠️'} {texto}")
        if not ok:
            res['falhas'].append(texto)

    def problema(obrigatorio, texto):
        # o 1º dia é obrigatório (entra no veredito); os outros são tolerados, como na prévia ERA5
        if obrigatorio:
            criterio(False, texto)
        else:
            res['linhas'].append(f"⚠️ {texto} (dia opcional; não entra no veredito)")

    if not contexto_gfs:
        res['linhas'].append("ℹ️ Nenhum dia GFS nesta execução: a rota GFS não foi testada.")
        return res
    referencia = contexto_gfs.get('referencia')
    if referencia is None:
        criterio(False, "nenhuma rodada 00Z completa: a rota GFS não pôde ser testada (rode de novo mais tarde)")
        return res
    dias = dias_previa_gfs(somar_dias(ultima_data_era5, 1), referencia, contexto_gfs['fim'])
    if not dias:
        res['linhas'].append("ℹ️ Nenhum dia GFS dentro do horizonte: a rota GFS não foi testada.")
        return res
    # [V4.1 K7] O outro método da Tmax/Tmin, calculado em memória ao lado do escolhido (só informação)
    alt = 'variancia' if METODO_TEMP_GFS == 'aditivo' else 'aditivo'
    tmax_ok = {METODO_TEMP_GFS: True, alt: True}
    emenda_testada = {METODO_TEMP_GFS: False, alt: False}                              # [V4.1 revisão V41-03]
    n_calculados = 0
    print(f"\n🔎 PRÉVIA GFS {nv}: {len(dias)} dia(s) calculado(s) em memória ({', '.join(dias)}), "
          f"sem exportar nada; conte de 1 a 3 minutos por dia.")
    base = processarDia_Rota1(ultima_data_era5)
    estado, ref_balde = _estado_previa_gfs(base)
    tabela = {}

    def linha_tabela(rotulo, valores, prefixo):
        tabela[rotulo] = {col: valores.get((prefixo, b, estat)) for (b, estat), col in COLUNAS_PREVIA_GFS.items()}

    for i, d in enumerate(dias):
        rodada = rodada_para_dia(d, contexto_gfs['completas'], referencia)
        if rodada is None:
            problema(i == 0, f"{d}: nenhuma rodada 00Z completa cobre o dia")
            continue
        dia_ms = data_para_ms(d)
        n_img, horas_chuva = contagem_esperada(dia_ms, rodada)
        prazo, faixa = prazo_L(dia_ms, rodada), faixa_prazo(dia_ms, rodada)
        novo = processarDia_GFS(d, estado, ref_balde, rodada, n_img, horas_chuva, faixa, prazo)
        novo_alt = processarDia_GFS(d, estado, ref_balde, rodada, n_img, horas_chuva, faixa, prazo,
                                    metodo_temp=alt)                                  # [V4.1 K7]
        partes = [('novo', novo, BANDAS_PREVIA_GFS)]
        # [V4.1 K7] Partes só informativas (o outro método e a razão dos desvios): se o pedido com elas falhar,
        # o dia é refeito sem elas, para o informativo nunca derrubar o critério obrigatório (revisão V41-02)
        partes_info = [('alt', novo_alt, ('tmax_C',))]
        if i == 0:
            mat = ee.Image(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{d[5:7]}')
            razao = razao_desvios(mat.select(f'Tmax_s_sicsb_{faixa}'), mat.select(f'Tmax_s_gfs_{faixa}'))
            partes_info.append(('razao', ee.Image.cat([razao.rename('razao_tmax'),
                                                       razao.lt(1).rename('frac_menor_1')]).updateMask(MASCARA_SAB),
                                ('razao_tmax', 'frac_menor_1')))
        info = inventario.get(id_dia(d))
        if info is not None:
            partes.append(('gravado', ee.Image(f'{ASSET_DESTINO}/{id_dia(d)}'), BANDAS_PREVIA_GFS))
        if i == 0:
            partes.append(('era5', base, BANDAS_PREVIA_GFS))
            # J6: Tmax do GFS BRUTO (antes da calibração), para separar viés do modelo de efeito da calibração
            bruto = (colecao_gfs_dia(d, rodada).select('temperature_2m_above_ground').max()
                     .rename('tmax_C').updateMask(MASCARA_SAB))
            partes.append(('bruto', bruto, ('tmax_C',)))
        inicio = time.time()
        extras_req = {'versao': novo.get('versao'), 'n_img': novo.get('Imagens_Validas_GFS')}
        try:
            try:
                v, extras = _nacional_gfs(partes + partes_info, extras_req)
            except Exception as e_info:                                                # [V4.1 revisão V41-02]
                res['linhas'].append(f"ℹ️ {d}: Tmax pelo outro método ({alt}) não calculada "
                                     f"({str(e_info)[:120]}); refeito só o método em uso")
                tmax_ok[alt] = False
                v, extras = _nacional_gfs(partes, extras_req)
        except Exception as e:
            print(f"   ⚠️ {d} (prazo L{prazo}): prévia GFS não calculada ({e})")
            problema(i == 0, f"{d} (prazo L{prazo}): prévia GFS não calculada")
            continue
        n_calculados += 1                                                                 # [V4.1 K7]
        print(f"   {d}: ok em {(time.time() - inicio) / 60:.1f} min (rodada {ms_para_data(rodada)} 00Z, "
              f"prazo L{prazo}, faixa {faixa})")
        if i == 0:
            linha_tabela(f"{ultima_data_era5} último ERA5 ({nv})", v, 'era5')
        linha_tabela(f"{d} L{prazo} {nv} ({extras.get('versao')})", v, 'novo')
        if info is not None:
            linha_tabela(f"{d} gravado ({info['versao']} {info['alg']})", v, 'gravado')
        linha_tabela(f"{d} L{prazo} Tmax pelo outro método ({alt})", v, 'alt')     # [V4.1 K7]
        if i == 0:
            linha_tabela(f"{d} GFS bruto (sem calibração)", v, 'bruto')

        criterio(extras.get('versao') == 'provisoria_gfs',
                 f"{d} (L{prazo}): {extras.get('versao')}, {extras.get('n_img')} de {n_img} saídas "
                 f"(esperado provisoria_gfs, dia completo)")
        tmax_max = v.get(('novo', 'tmax_C', 'max'))
        tmax_alt = v.get(('alt', 'tmax_C', 'max'))                                       # [V4.1 K7]
        criterio(tmax_max is not None and tmax_max <= TMAX_RECORDE_BR,
                 f"{d} (L{prazo}): Tmax máxima nacional "
                 f"{'não calculada' if tmax_max is None else f'{tmax_max:.1f} °C'} "
                 f"(recorde do INMET {TMAX_RECORDE_BR} °C; método {METODO_TEMP_GFS})")
        tmax_ok[METODO_TEMP_GFS] &= tmax_max is not None and tmax_max <= TMAX_RECORDE_BR
        tmax_ok[alt] &= tmax_alt is not None and tmax_alt <= TMAX_RECORDE_BR
        res['linhas'].append(
            f"ℹ️ {d} (L{prazo}): Tmax máxima nacional {METODO_TEMP_GFS} "
            f"{'?' if tmax_max is None else f'{tmax_max:.1f}'} °C x {alt} "
            f"{'?' if tmax_alt is None else f'{tmax_alt:.1f}'} °C (recorde {TMAX_RECORDE_BR} °C)")
        if i == 0:
            tmax_era5, tmax_bruto = v.get(('era5', 'tmax_C', 'max')), v.get(('bruto', 'tmax_C', 'max'))
            if tmax_max is not None and tmax_era5 is not None:
                salto = tmax_max - tmax_era5
                criterio(abs(salto) <= SALTO_MAX_TMAX,
                         f"salto da Tmax máxima nacional na emenda ERA5 -> GFS ({ultima_data_era5} -> {d}): "
                         f"{tmax_era5:.1f} -> {tmax_max:.1f} °C ({salto:+.1f} °C; limite ±{SALTO_MAX_TMAX:.0f} °C)")
                tmax_ok[METODO_TEMP_GFS] &= abs(salto) <= SALTO_MAX_TMAX
                emenda_testada[METODO_TEMP_GFS] = True
            if tmax_alt is not None and tmax_era5 is not None:
                tmax_ok[alt] &= abs(tmax_alt - tmax_era5) <= SALTO_MAX_TMAX
                emenda_testada[alt] = True
                res['linhas'].append(f"ℹ️ salto na emenda pelo outro método ({alt}): "
                                     f"{tmax_alt - tmax_era5:+.1f} °C (limite ±{SALTO_MAX_TMAX:.0f} °C)")
            rz, fr = v.get(('razao', 'razao_tmax', 'mean')), v.get(('razao', 'frac_menor_1', 'mean'))
            if rz is not None and fr is not None:
                res['linhas'].append(
                    f"ℹ️ razão dos desvios da Tmax BR-DWGD/GFS (mês {d[5:7]}, faixa {faixa}): média {rz:.2f}; "
                    f"{100 * fr:.0f}% dos pixels abaixo de 1 (abaixo de 1, a escala de variância encolhe as "
                    f"anomalias do GFS e reduz os extremos)")
            if tmax_bruto is not None and tmax_max is not None and tmax_era5 is not None:
                res['linhas'].append(
                    f"ℹ️ {d}: Tmax máxima nacional do GFS bruto {tmax_bruto:.1f} °C -> calibrado {tmax_max:.1f} °C "
                    f"(efeito da calibração {tmax_max - tmax_bruto:+.1f} °C; bruto - último ERA5 "
                    f"{tmax_bruto - tmax_era5:+.1f} °C). Bruto já acima do recorde = viés do modelo; "
                    f"só o calibrado acima = efeito da calibração.")
        rs_novo, rs_grav = v.get(('novo', 'rs', 'mean')), v.get(('gravado', 'rs', 'mean'))
        if rs_novo is not None and rs_grav:
            res['linhas'].append(f"ℹ️ {d}: razão da radiação média {nv}/gravado ({info['alg']}) = "
                                 f"{rs_novo / rs_grav:.3f} (informativa)")
    if tabela:
        res['tabela'] = pd.DataFrame.from_dict(tabela, orient='index').astype(float).round(2)
    if n_calculados:
        res['linhas'].append(decisao_tmax(METODO_TEMP_GFS, alt, tmax_ok, emenda_testada))   # [V4.1 K7]
    return res

def decisao_tmax(metodo, alt, ok, emenda=None):
    """[V4.1 K7] Frase da decisão da Tmax: ok = {método: passou no recorde e na emenda em todos os dias};
    emenda = {método: a emenda ERA5 -> GFS foi testada} (revisão V41-03; None = as duas testadas)."""
    emenda = emenda if emenda is not None else {metodo: True, alt: True}
    if not emenda.get(metodo):
        return ("⚠️ Tmax: a emenda ERA5 -> GFS não foi testada nesta execução (1º dia GFS não calculado); "
                "não decida o método agora: rode o 05a de novo mais tarde.")
    if not emenda.get(alt):
        ok = dict(ok, **{alt: False})
    if ok.get(metodo):
        return (f"✅ Tmax: o método em uso ({metodo}) passa no recorde e na emenda; o outro ({alt}) "
                f"{'também passa' if ok.get(alt) else 'não passaria'}. Não é preciso mudar nada.")
    if ok.get(alt) and metodo == 'variancia':
        # [Revisão 20/10/2026] A variância foi validada fora da amostra (K8, cerca de 146 mil previsões); poucos
        # dias da PRÉVIA não bastam para voltar ao aditivo
        return (f"⚠️ Tmax: nesta execução '{alt}' passou no recorde e na emenda e '{metodo}' não. NÃO troque o "
                f"método por conta disso (a auditoria K8 validou '{metodo}' em 2025 inteiro): mande esta saída.")
    if ok.get(alt):
        return (f"➜ DECISÃO (roteiro, etapa 5a): com '{alt}' a Tmax passaria no recorde e na emenda. Para adotar, "
                f"troque METODO_TEMP_GFS = '{metodo}' por '{alt}' no 05a e no 05b e rode o 05a de novo.")
    return ("➜ DECISÃO (roteiro, etapa 5a): nenhum dos dois métodos tira a Tmax de cima do recorde ou do limite da "
            "emenda. Veja a linha do GFS bruto: se ele já passa do recorde, a cauda vem do próprio GFS.")

def _imprimir_previa_gfs(gfs):
    print("\n=== PRÉVIA 6. ROTA GFS EM MEMÓRIA (Brasil: médias e máximos nacionais; nada é gravado) ===")
    if gfs['tabela'] is not None:
        print(gfs['tabela'])
    for linha in gfs['linhas']:
        print(f"   {linha}")

def _previa_gfs_sozinha():
    """[V4 B2] Sem a prévia ERA5 (nenhum dia V1.3 para comparar), a PRÉVIA 6 roda com veredito próprio."""
    gfs = executar_previa_gfs()
    _imprimir_previa_gfs(gfs)
    if gfs['falhas']:
        print("⚠️ NÃO EXECUTE AINDA. Pontos fora do esperado na rota GFS:")
        for f in gfs['falhas']:
            print(f"   - {f}")
    else:
        print("✅ Critérios da rota GFS (PRÉVIA 6) atendidos.")

def executar_previa():
    # [V4 B5/M05-04] provisórios começam depois de limite_def (não de ultima_data_brd)
    meses = sorted({d[:7] for d in intervalo_datas(somar_dias(limite_def, 1), ultima_data_era5)})
    datas = [f'{m}-{dia:02d}' for m in meses for dia in PREVIA_DIAS_DO_MES]
    # Só dias provisórios já gravados pela V1.3: a comparação isola o que a V1.5 muda nos dias ERA5
    datas = [d for d in datas if d <= ultima_data_era5
             and (inventario.get(id_dia(d)) or {}).get('versao') == 'provisoria_era5'
             and (inventario.get(id_dia(d)) or {}).get('alg') == 'V1.3']
    if not datas:
        print("\n🔎 Prévia: não há dias provisórios gravados pela V1.3 para comparar.")
        _previa_gfs_sozinha()   # [V4 B2]
        return
    print(f"\n🔎 PRÉVIA {VERSAO_ALGORITMO}: {len(datas)} dias provisórios, do jeito que o painel mostra hoje x "
          f"como a {VERSAO_ALGORITMO} gravaria. Nada é gravado; conte de 1 a 3 minutos por dia.")   # [V4]
    rotulo = _rotulo_regioes()
    anel = limitesRegiao.coordinates().getInfo()[0]       # retângulo envolvente do Brasil
    xs, ys = [p[0] for p in anel], [p[1] for p in anel]
    limites = (min(xs), min(ys), max(xs), max(ys))
    linhas, falhas_seguidas = [], 0
    for d in datas:
        inicio = time.time()
        try:
            resultado = _previa_dia(d, rotulo, limites)
        except Exception as e:
            print(f"   ⚠️ {d}: prévia não calculada ({e})")
            falhas_seguidas += 1
            if falhas_seguidas == 3:
                print("   Três dias seguidos falharam; a prévia parou aqui para não gastar mais tempo.")
                break
            continue
        falhas_seguidas = 0
        for reg, props in resultado.items():
            linhas.append(dict(props, data=d, regiao=reg))
        # Grava a cada dia: se a execução for interrompida, os dias já calculados ficam no arquivo
        pd.DataFrame(linhas).to_csv(ARQUIVO_PREVIA, index=False, sep=';', decimal=',')   # [V4] previa_v15.csv
        br = resultado.get('Brasil')
        resumo = ''
        if br:
            u = 'soil_moisture_0_100cm_m3_m3'
            resumo = (f" | Umidade 0-100 cm Brasil {br['a_' + u]:.4f} -> {br['n_' + u]:.4f} m³/m³ "
                      f"({100 * (br['n_' + u] / br['a_' + u] - 1):+.2f}%)")
        print(f"   {d}: ok em {(time.time() - inicio) / 60:.1f} min{resumo}")
    if not linhas:
        print("   Nenhum dia calculado; a prévia não pode ser avaliada.")
        _previa_gfs_sozinha()   # [V4 B2]
        return

    df = pd.DataFrame(linhas)
    por_data, por_regiao, todas, coerencia, falhas = _resumir_previa(df, list(relatorio_sim), len(datas))
    print(f"\n   Dias calculados: {df['data'].nunique()} de {len(datas)}.")
    # [V4 B2/M05-06] Rota GFS em memória; os critérios dela entram no veredito da PRÉVIA 5
    gfs = executar_previa_gfs()
    falhas = falhas + [f"rota GFS (PRÉVIA 6): {f}" for f in gfs['falhas']]
    pd.set_option('display.width', 220)
    pd.set_option('display.max_columns', 20)
    print("\n=== PRÉVIA 1. BRASIL, DIA A DIA (umidade em m³/m³; ETo em mm/dia) ===")
    print(por_data)
    print(f"\n=== PRÉVIA 2. MÉDIA DOS DIAS AMOSTRADOS, POR REGIÃO (variações da {VERSAO_ALGORITMO} "
          f"sobre o painel atual) ===")   # [V4] rótulo da versão
    print(por_regiao)
    print(f"\n=== PRÉVIA 3. AS 16 VARIÁVEIS NO BRASIL (média dos dias; Δ = {VERSAO_ALGORITMO} - hoje; "
          "|Δ| onde mudou = mudança média nos pixels alterados) ===")   # [V4] rótulo da versão
    print(todas)
    print("\n=== PRÉVIA 4. COERÊNCIA FÍSICA (% dos pixels com o problema) ===")
    print(coerencia)
    print("\n=== PRÉVIA 5. CRITÉRIOS DE APROVAÇÃO ===")
    print("   (inclui os critérios da rota GFS, detalhados na PRÉVIA 6, logo abaixo)")   # [V4 B2]
    if falhas:
        print("⚠️ NÃO EXECUTE AINDA. Pontos fora do esperado:")
        for f in falhas:
            print(f"   - {f}")
    else:
        print("✅ Todos os critérios atendidos. Para gravar, mude SIMULAR = False e rode de novo.")
    _imprimir_previa_gfs(gfs)   # [V4 B2]
    df.to_csv(ARQUIVO_PREVIA, index=False, sep=';', decimal=',')   # [V4] previa_v15.csv
    print(f"💾 Valores completos da prévia em {ARQUIVO_PREVIA} (formato do Excel em português).")

# --- Execução ---
relatorio_sim = {}
relatorio_protegidos = {}
if PROTEGER_HISTORICO:
    print(f"🛡️ TRAVA DO HISTÓRICO LIGADA: nenhum dia até {DATA_LIMITE_PROTECAO} será alterado.\n")
    # [V4 M05-22] Com a trava, estas opções não têm efeito nos dias até DATA_LIMITE_PROTECAO
    if APLICAR_PATCH_SOLO:
        print(f"⚠️ APLICAR_PATCH_SOLO = True não tem efeito com a trava ligada: os dias V1.0 vão até "
              f"{DATA_LIMITE_PROTECAO} e só aparecem no relatório PROTEGIDOS.\n")
    if REPROCESSAR_VERSAO_ANTIGA:
        print(f"⚠️ REPROCESSAR_VERSAO_ANTIGA = True com a trava ligada: os dias até {DATA_LIMITE_PROTECAO} "
              f"não são recalculados e só aparecem no relatório PROTEGIDOS.\n")
if SIMULAR:
    print("🧪 MODO SIMULAÇÃO ATIVO: nenhum asset será criado, apagado ou exportado.\n")
# Todos os dias provisórios (desde o dia seguinte ao último dia definitivo) entram na janela
# operacional, para que um recálculo de versão tenha prioridade sobre o passivo histórico.
# [V4 B5/M05-04] limite_def no lugar de ultima_data_brd: sem conversão, os dias que o BR-DWGD já
# cobre depois de DATA_LIMITE_PROTECAO continuam provisórios e continuam na janela.
inicio_janela = min(somar_dias(data_hoje_str, -JANELA_OPERACIONAL_DIAS),
                    somar_dias(limite_def, 1), ultima_data_era5)

# A fila do Earth Engine atende por ordem de envio (com a mesma prioridade, quem chega primeiro
# roda primeiro) e roda poucas tarefas ao mesmo tempo. A cadeia GFS espera cada dia terminar,
# então antes dela só entram os dias ERA5 que ela usa como base. Se os ~270 provisórios entrassem
# antes, cada dia de previsão esperaria a fila inteira e poderia estourar TIMEOUT_TAREFA_MIN.
dias_janela = intervalo_datas(inicio_janela, ultima_data_era5)[::-1]   # do mais recente ao mais antigo

# 1) Base da previsão: os últimos DIAS_REF_ET dias do ERA5, sem reserva
enviados_op = despachar_assincrono(
    dias_janela[:DIAS_REF_ET], "📌 JANELA OPERACIONAL (base da previsão)", reserva=0)

# 2) Previsão GFS encadeada
executar_cadeia_gfs(enviados_op)

# 3) Resto da janela operacional (demais provisórios e dias recentes), sem reserva. As tarefas
#    seguem rodando no Earth Engine depois que a execução termina; a execução seguinte as promove.
despachar_assincrono(dias_janela[DIAS_REF_ET:], "📌 JANELA OPERACIONAL (restante)", reserva=0)

# 4) Passivo histórico, respeitando a reserva para as próximas execuções
despachar_assincrono(
    intervalo_datas(DATA_INICIO_P1, somar_dias(inicio_janela, -1)),
    f"📚 HISTÓRICO PRINCIPAL ({DATA_INICIO_P1[:4]} até a janela)", reserva=RESERVA_OPERACIONAL)
despachar_assincrono(
    intervalo_datas(DATA_INICIO_P2, DATA_FIM_P2),
    f"🔍 HISTÓRICO SECUNDÁRIO ({DATA_INICIO_P2[:4]}-{DATA_FIM_P2[:4]})", reserva=RESERVA_OPERACIONAL)

# 5) Promove o que já terminou
finalizar_trocas_pendentes(listar_tarefas_ativas())

if SIMULAR:
    print("\n🧪 RESUMO DA SIMULAÇÃO (dias por ação):")
    for motivo, n in sorted(relatorio_sim.items()):
        print(f"   {motivo}: {n:,}")
    print("   Demais dias do acervo: mantidos sem alteração.")
    if PREVIA:
        executar_previa()
if relatorio_protegidos:
    print("\n🛡️ PROTEGIDOS: dias históricos que precisariam de ação e NÃO foram tocados (trava ligada):")
    for motivo, n in sorted(relatorio_protegidos.items()):
        print(f"   {motivo}: {n:,}")
else:
    print("\n🛡️ PROTEGIDOS: nenhum dia histórico precisaria de ação.")
print(f"\n✅ Execução encerrada. Vagas restantes na fila: {capacidade:,}.")

'''
SHAS = {n: hashlib.sha256(s.encode('utf-8')).hexdigest() for n, s in (('V1.0 (O0)', FONTE_V10), ('V1.5 (05b)', FONTE_V15))}

PROIBIDO_NA_CARGA = ('getInfo', 'getTaskList', 'Initialize', 'Authenticate', 'Export', '.start(', 'deleteAsset',
                     'renameAsset', 'createAsset', 'copyAsset', 'listAssets', 'getAsset(', 'setAssetAcl')
GLOBAIS_PERMITIDOS = {'limitesRegiao', 'poligonoBrasil', 'crsNativo', 'transformNativo', 'elevacao_br', 'colChuvaGeral',
                      'colecao_era5', '_gaul_br', 'fcBrasil', 'fuso_br', 'data_extracao_local', 'data_hoje_dt',
                      'data_hoje_str', 'data_fim_processo'}


def trechos_carregaveis(fonte):
    """Divide o código de um motor em instruções do nível de cima e devolve só as seguras para carregar: imports,
    definições de função e atribuições de constantes (NOMES_EM_MAIÚSCULAS) ou de objetos permitidos, sem nenhuma
    chamada ao servidor nem escrita. Nada do fluxo principal do motor (que exporta) é executado."""
    fonte = fonte.lstrip('﻿')
    arvore = ast.parse(fonte)
    saida = []
    for no in arvore.body:
        seg = ast.get_source_segment(fonte, no) or ''
        if isinstance(no, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            if isinstance(no, ast.FunctionDef) or not any(p in seg for p in PROIBIDO_NA_CARGA):
                saida.append((type(no).__name__, seg))
        elif isinstance(no, ast.Assign) and all(isinstance(t, ast.Name) and (t.id.isupper() or t.id in GLOBAIS_PERMITIDOS)
                                                for t in no.targets):
            if not any(p in seg for p in PROIBIDO_NA_CARGA):
                saida.append(('Assign', seg))
    return saida


def carregar_codigo(nome, fonte, precisa, ee_mod):
    """Carrega o motor num espaço próprio e confere que as funções pedidas existem."""
    ns = {'__name__': f'k17_{nome}', '__builtins__': __builtins__, 'ee': ee_mod}
    pulados = []
    for tipo, seg in trechos_carregaveis(fonte):
        try:
            exec(compile(seg, f'<{nome}>', 'exec'), ns)
        except Exception as e:          # ex.: constante que depende de algo do fluxo principal
            pulados.append(f'{tipo}: {seg.splitlines()[0][:60]} ({type(e).__name__})')
    faltam = [f for f in precisa if not callable(ns.get(f))]
    if faltam:
        raise RuntimeError(f'{nome}: funções não encontradas: {faltam}')
    return ns, pulados



def log(*p):
    t = ' '.join(str(x) for x in p)
    print(t, flush=True)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(t + '\n')


def achado(parte, status, titulo, detalhe):
    icone = {'OK': '✅', 'ATENÇÃO': '⚠️', 'FALHA': '❌', 'INFO': 'ℹ️', 'NÃO EXECUTADO': '⏭️'}[status]
    ACHADOS.append({'parte': parte, 'status': status, 'titulo': titulo, 'detalhe': detalhe})
    log(f'{icone} {parte} {status}: {titulo}\n   {detalhe}')


def candidata(parte, o_que, onde_corrigir, tamanho, referencia):
    CANDIDATAS.append({'parte': parte, 'divergencia': o_que, 'correcao_permitida': onde_corrigir,
                       'tamanho': tamanho, 'referencia': referencia})


def salvar_csv(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=False, encoding='utf-8-sig')


# =========================================================================================
# FUNÇÕES PURAS (testadas offline em testes/teste_k19.py)
# =========================================================================================
def minutos_ate_janela(agora):
    """Minutos até o início da próxima janela do motor (0 se já está dentro de uma)."""
    m = agora.hour * 60 + agora.minute
    melhor = None
    for (h1, m1), (h2, m2) in JANELAS_MOTOR:
        ini, fim = h1 * 60 + m1, h2 * 60 + m2
        if ini <= m < fim:
            return 0
        falta = (ini - m) % (24 * 60)
        melhor = falta if melhor is None else min(melhor, falta)
    return melhor


def iguais_np(a, b):
    a, b = pd.to_numeric(a, errors='coerce'), pd.to_numeric(b, errors='coerce')
    d = (a - b).abs()
    return (a.isna() & b.isna()) | (d <= TOL_ABS) | (d <= TOL_REL * b.abs())


def classificar_d1(linhas, min_iguais=MIN_IGUAIS):
    """linhas: [{'data', 'classe', 'frac_<banda>'...}] (fração de pixels iguais por banda e classe).
    Devolve (tabela por dia, contagem: {'idênticos', 'só ERA5 acumulado', 'outra diferença'}, dias com outra)."""
    df = pd.DataFrame(linhas)
    saida, cont, outros = [], {'idênticos': 0, 'só ERA5 acumulado': 0, 'outra diferença': 0}, []
    for d, sub in df.groupby('data'):
        dif = {}
        for _, r in sub.iterrows():
            ruins = [b for b in ORDEM if pd.notna(r.get(f'frac_{b}')) and r.get(f'frac_{b}') < min_iguais]
            if ruins:
                dif[r['classe']] = ruins
        if not dif:
            tipo = 'idênticos'
        # [v4.1] de 2026 em diante a chuva, a ETo e a radiação dos pixels A também vêm do ERA5 (não há BR-DWGD)
        elif all(set(v) <= (SOMA_ERA5_A if (c == 'A' and d <= FIM_HISTORICO) else SOMA_ERA5_OUTRAS)
                 for c, v in dif.items()):
            tipo = 'só ERA5 acumulado'
        else:
            tipo = 'outra diferença'
            outros.append(d)
        cont[tipo] += 1
        saida.append({'data': d, 'tipo': tipo, 'bandas_diferentes': '; '.join(f'{c}: {",".join(v)}' for c, v in dif.items())})
    return pd.DataFrame(saida), cont, outros


def resumo_qc(df):
    """df: uma linha por ano e classe, colunas n (pixel-dias válidos) e uma por teste do QC (contagem).
    Devolve (status, detalhe, tabela por teste e classe com contagem e fração)."""
    linhas = []
    for nome, desc, tipo in QC:
        for cl, sub in df.groupby('classe'):
            n, k = float(sub['n'].sum()), float(sub[nome].sum()) if nome in sub else 0.0
            anos = sub[sub.get(nome, 0) > 0]['ano'].astype(int).tolist() if nome in sub else []
            linhas.append({'teste': nome, 'descricao': desc, 'tipo': tipo, 'classe': cl, 'pixel_dias': int(n),
                           'ocorrencias': int(k), 'fracao': k / n if n else 0.0,
                           'anos': (f'{min(anos)}-{max(anos)} ({len(anos)} anos)' if anos else '-')})
    tab = pd.DataFrame(linhas)
    duros = tab[(tab['tipo'] == 'duro') & (tab['ocorrencias'] > 0)]
    susp = tab[(tab['tipo'] == 'suspeito') & (tab['ocorrencias'] > 0)]
    det = (f'{int(df.groupby("ano")["n"].sum().size)} anos; '
           f'{int(tab[tab["teste"] == QC[0][0]]["pixel_dias"].sum()):,} pixel-dias conferidos'.replace(',', '.'))
    if len(duros):
        det += ' | IMPOSSÍVEIS: ' + '; '.join(f'{r.descricao} ({r.classe}): {r.ocorrencias} em {r.anos}'
                                              for r in duros.itertuples())
    if len(susp):
        det += ' | suspeitos: ' + '; '.join(f'{r.descricao} ({r.classe}): {r.ocorrencias}' for r in susp.itertuples())
    st = 'FALHA' if len(duros) else ('ATENÇÃO' if len(susp) else 'OK')
    return st, det, tab


def pettitt(x):
    """Teste de Pettitt (1979). Devolve (índice da quebra: 1º ponto do 2º trecho, K, p aproximado)."""
    x = np.asarray(x, float)
    n = len(x)
    s = np.sign(x[None, :] - x[:, None])                      # s[i, j] = sign(x_j - x_i)
    u = np.array([s[:k + 1, k + 1:].sum() for k in range(n - 1)])
    k = int(np.argmax(np.abs(u)))
    K = float(abs(u[k]))
    p = min(1.0, 2 * math.exp(-6 * K ** 2 / (n ** 3 + n ** 2)))
    return k + 1, K, p


def snht(x, n_perm=N_PERMUTACOES, semente=SEMENTE, borda=3):
    """SNHT de Alexandersson (1986) para uma quebra na média, com p por permutação (sem tabela).
    Devolve (índice da quebra: 1º ponto do 2º trecho, T0, p)."""
    x = np.asarray(x, float)
    n = len(x)

    def estat(v):
        z = (v - v.mean()) / (v.std(ddof=1) or 1.0)
        c = np.cumsum(z)
        k = np.arange(1, n)
        t = k * (c[:-1] / k) ** 2 + (n - k) * ((c[-1] - c[:-1]) / (n - k)) ** 2
        t[:borda - 1] = -1
        t[n - borda:] = -1
        return int(np.argmax(t)) + 1, float(t.max())
    k, t0 = estat(x)
    rng = np.random.default_rng(semente)
    maior = sum(estat(rng.permutation(x))[1] >= t0 for _ in range(n_perm))
    return k, t0, (maior + 1) / (n_perm + 1)


def homogeneidade(series, anos, p_lim=P_LIMITE, ano_costura=ANO_FIM, base=(1996, 2025)):
    """series: DataFrame (uf, variavel, ano, d) com d = diferença (ou razão) SAB x referência. Para cada uf e variável:
    Pettitt e SNHT na série 1961-2025 e escore z do último ano (costura) contra a base. Devolve tabela."""
    linhas = []
    for (uf, var), sub in series.groupby(['uf', 'variavel']):
        sub = sub.dropna(subset=['d']).sort_values('ano')
        hist = sub[sub['ano'] < ano_costura]
        if len(hist) < 20:
            continue
        x = hist['d'].to_numpy()
        kp, K, pp = pettitt(x)
        ks, t0, ps = snht(x)
        ref = hist[(hist['ano'] >= base[0]) & (hist['ano'] <= base[1])]['d']
        ult = sub[sub['ano'] == ano_costura]['d']
        z = float((ult.iloc[0] - ref.mean()) / (ref.std(ddof=1) or np.nan)) if len(ult) and len(ref) > 5 else np.nan
        ano_q = int(hist['ano'].iloc[ks]) if ks < len(hist) else None
        linhas.append({'uf': uf, 'variavel': var, 'n': len(x), 'pettitt_ano': int(hist['ano'].iloc[kp]), 'pettitt_p': pp,
                       'snht_ano': ano_q, 'snht_T0': t0, 'snht_p': ps,
                       'salto_snht': float(x[ks:].mean() - x[:ks].mean()),
                       'quebra': bool(pp < p_lim and ps < p_lim), f'z_{ano_costura}': z})
    return pd.DataFrame(linhas)


def agrupar_quebras(tab, janela=2, minimo=5):
    """Quebras (Pettitt e SNHT significativos) que se repetem no mesmo ano (± janela) em pelo menos 'minimo' estados."""
    q = tab[tab['quebra']]
    saida = []
    for var, sub in q.groupby('variavel'):
        anos = sub['snht_ano'].dropna().astype(int).tolist()
        for a in sorted(set(anos)):
            perto = [x for x in anos if abs(x - a) <= janela]
            if len(perto) >= minimo:
                saida.append({'variavel': var, 'ano_central': a, 'estados': len(perto),
                              'salto_medio': float(sub[sub['snht_ano'].between(a - janela, a + janela)]['salto_snht'].mean())})
    df = pd.DataFrame(saida)
    if df.empty:
        return df
    df = df.sort_values(['variavel', 'estados'], ascending=[True, False])
    return df.drop_duplicates('variavel', keep='first')


def eqm_ajustar(treino_mod, treino_obs, niveis=101):
    """Mapeamento de quantis empírico (EQM): quantis do modelo e da observação no treino."""
    q = np.linspace(0, 1, niveis)
    return np.quantile(np.asarray(treino_mod, float), q), np.quantile(np.asarray(treino_obs, float), q)


def eqm_aplicar(x, qm, qo, chuva=False):
    """Aplica o EQM; fora da faixa do treino usa a correção do quantil extremo (multiplicativa na chuva)."""
    x = np.asarray(x, float)
    y = np.interp(x, qm, qo)
    if chuva:
        alto = x > qm[-1]
        y[alto] = x[alto] * (qo[-1] / qm[-1] if qm[-1] > 0 else 1.0)
        y = np.maximum(y, 0)
    else:
        y[x > qm[-1]] = x[x > qm[-1]] + (qo[-1] - qm[-1])
        y[x < qm[0]] = x[x < qm[0]] + (qo[0] - qm[0])
    return y


def metricas_chuva(sim, obs, chave_mes):
    """Viés (%), frequência de dias com chuva (pontos percentuais), P95 e P99 (razão), erro diário, correlação e erro
    do total mensal (chave_mes agrupa ponto e mês)."""
    sim, obs = np.asarray(sim, float), np.asarray(obs, float)
    ok = ~(np.isnan(sim) | np.isnan(obs))
    sim, obs, chave = sim[ok], obs[ok], np.asarray(chave_mes)[ok]
    mens = pd.DataFrame({'k': chave, 's': sim, 'o': obs}).groupby('k').sum()
    return {'vies_pct': 100 * (sim.sum() - obs.sum()) / obs.sum(),
            'freq_chuva_sim': 100 * (sim >= CHUVA_DIA).mean(), 'freq_chuva_obs': 100 * (obs >= CHUVA_DIA).mean(),
            'erro_freq_pp': 100 * ((sim >= CHUVA_DIA).mean() - (obs >= CHUVA_DIA).mean()),
            'razao_p95': np.percentile(sim, 95) / np.percentile(obs, 95),
            'razao_p99': np.percentile(sim, 99) / np.percentile(obs, 99),
            'erro_diario_mm': float(np.abs(sim - obs).mean()), 'correlacao': float(np.corrcoef(sim, obs)[0, 1]),
            'erro_mensal_mm': float((mens['s'] - mens['o']).abs().mean())}


def metricas_continua(sim, obs, grupo):
    """Viés, razão dos desvios das anomalias (no grupo ponto-mês), P99 e P1 (diferença) e erro diário."""
    df = pd.DataFrame({'s': np.asarray(sim, float), 'o': np.asarray(obs, float), 'g': np.asarray(grupo)}).dropna()
    an_s = df['s'] - df.groupby('g')['s'].transform('mean')
    an_o = df['o'] - df.groupby('g')['o'].transform('mean')
    return {'vies': float((df['s'] - df['o']).mean()), 'razao_desvio': float(an_s.std() / an_o.std()),
            'dif_p99': float(np.percentile(df['s'], 99) - np.percentile(df['o'], 99)),
            'dif_p01': float(np.percentile(df['s'], 1) - np.percentile(df['o'], 1)),
            'erro_diario': float((df['s'] - df['o']).abs().mean()), 'correlacao': float(df['s'].corr(df['o']))}


def avaliar_d5(dados, meses_matriz):
    """dados: DataFrame pid, data (YYYY-MM-DD), era_<v> e br_<v> para v em VARS_D5 (pr, tmax, tmin, rh, rs, u2).
    meses_matriz: DataFrame pid, mes e as médias da matriz (<B>_m_br, <B>_m_era) de BANDAS_MATRIZ_D5.
    Compara, no teste (ANOS_TESTE_D5), ERA5 bruto x método atual (escala na média, V1.5) x EQM treinado em
    ANOS_TREINO_D5. Devolve (tabela de métricas, texto, é_candidata)."""
    d = dados.copy()
    d['ano'] = d['data'].str[:4].astype(int)
    d['mes'] = d['data'].str[5:7].astype(int)
    d = d.merge(meses_matriz, on=['pid', 'mes'], how='left')
    fator = (d['pr_m_br'] / d['pr_m_era'].clip(lower=1e-3)).clip(upper=FATOR_MAX)
    d['atual_pr'] = (d['era_pr'] * fator).clip(lower=0)
    # o mesmo método do motor V1.5 (_componentes_era5): aditivo em Tmax, Tmin e UR; multiplicativo (teto 5) em
    # chuva, radiação e vento
    d['atual_tmax'] = d['era_tmax'] + (d['Tmax_m_br'] - d['Tmax_m_era'])
    d['atual_tmin'] = d['era_tmin'] + (d['Tmin_m_br'] - d['Tmin_m_era'])
    d['atual_rh'] = (d['era_rh'] + (d['RH_m_br'] - d['RH_m_era'])).clip(0, 100)
    for v, b in (('rs', 'Rs'), ('u2', 'u2')):
        d[f'atual_{v}'] = (d[f'era_{v}'] * (d[f'{b}_m_br'] / d[f'{b}_m_era'].clip(lower=1e-3)).clip(upper=FATOR_MAX)).clip(lower=0)
    treino, teste = d[d['ano'].isin(ANOS_TREINO_D5)], d[d['ano'].isin(ANOS_TESTE_D5)].copy()
    for v in VARS_D5:
        teste[f'qm_{v}'] = np.nan
    for (pid, mes), sub in teste.groupby(['pid', 'mes']):
        tr = treino[(treino['pid'] == pid) & (treino['mes'] == mes)]
        if len(tr) < 60:
            continue
        for v in VARS_D5:
            t2 = tr[[f'era_{v}', f'br_{v}']].dropna()
            if len(t2) < 60:
                continue
            qm, qo = eqm_ajustar(t2[f'era_{v}'], t2[f'br_{v}'])
            teste.loc[sub.index, f'qm_{v}'] = eqm_aplicar(sub[f'era_{v}'], qm, qo, chuva=(v == 'pr'))
    chave = teste['pid'].astype(str) + '_' + teste['data'].str[:7]
    linhas = []
    for metodo, pref in (('ERA5 bruto', 'era'), ('atual (média, V1.5)', 'atual'), ('quantis (EQM)', 'qm')):
        mc = metricas_chuva(teste[f'{pref}_pr'], teste['br_pr'], chave)
        linhas.append({'variavel': 'chuva', 'metodo': metodo, **mc})
        for v in VARS_D5[1:]:
            mt = metricas_continua(teste[f'{pref}_{v}'], teste[f'br_{v}'], chave)
            linhas.append({'variavel': v, 'metodo': metodo, **mt})
    tab = pd.DataFrame(linhas)
    c = tab[tab['variavel'] == 'chuva'].set_index('metodo')
    a, q = c.loc['atual (média, V1.5)'], c.loc['quantis (EQM)']
    melhora_freq = abs(q['erro_freq_pp']) <= 0.5 * abs(a['erro_freq_pp'])
    melhora_ext = abs(q['razao_p99'] - 1) <= 0.5 * abs(a['razao_p99'] - 1)
    nao_piora = q['erro_mensal_mm'] <= 1.05 * a['erro_mensal_mm']
    cand = bool((melhora_freq or melhora_ext) and nao_piora)
    texto = (f'chuva no teste {ANOS_TESTE_D5[0]}-{ANOS_TESTE_D5[-1]} ({teste["pid"].nunique()} pixels A): dias com chuva '
             f'BR-DWGD {a["freq_chuva_obs"]:.1f}% | atual {a["freq_chuva_sim"]:.1f}% (P99 x{a["razao_p99"]:.2f}, viés '
             f'{a["vies_pct"]:+.1f}%, erro mensal {a["erro_mensal_mm"]:.1f} mm) | EQM {q["freq_chuva_sim"]:.1f}% (P99 '
             f'x{q["razao_p99"]:.2f}, viés {q["vies_pct"]:+.1f}%, erro mensal {q["erro_mensal_mm"]:.1f} mm)')
    return tab, texto, cand


# =========================================================================================
def principal():
    import ee

    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log('=' * 100)
    log(f'K19b: AUDITORIA PROFUNDA DO SAB (somente leitura), partes {", ".join(PARTES)} | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    for n, s in SHAS.items():
        log(f'   código embutido {n}: SHA-256 {s}')
    log('=' * 100)
    falta = minutos_ate_janela(AGORA)
    if falta < DURACAO_ESTIMADA_MIN:
        log(f'⛔ Não comecei: a próxima janela do motor começa em {falta} min e a K19 pode levar até '
            f'{DURACAO_ESTIMADA_MIN} min. Comece entre 16h00 e 19h50 ou entre 00h00 e 11h50.')
        return
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K19 SOMENTE LEITURA: tentativa de escrita bloqueada')

    for _n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
               'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable', 'exportVideo',
               'exportMap', 'startIngestion', 'startTableIngestion', 'cancelTask', 'cancelOperation'):
        if hasattr(ee.data, _n):
            setattr(ee.data, _n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa (criar, apagar, renomear, exportar e cancelar bloqueados).\n')

    PROJ = ee.Projection(CRS, TRANSFORM)
    REGIAO = ee.Geometry.Rectangle(REGIAO_AMPLA, None, False)
    CLASSE = ee.Image(ASSET_MASCARA).select('classe').unmask(0).toInt().rename('classe')
    COL = ee.ImageCollection(ASSET_SAB)
    BRCOL = ee.ImageCollection(BRDWGD)
    ERACOL = ee.ImageCollection(ERA5)
    LONLAT = ee.Image.pixelLonLat()
    ELEV = ee.Image('USGS/SRTMGL1_003')
    UFS = ee.FeatureCollection(GAUL1).filter(ee.Filter.eq('ADM0_NAME', 'Brazil')).select(['ADM1_NAME'])
    estado = {}

    class Pesado(RuntimeError):
        pass

    def gi(obj, rotulo, tentativas=4):
        for k in range(tentativas):
            try:
                return obj.getInfo()
            except Exception as e:
                msg = str(e)
                if any(x in msg.lower() for x in ('memory limit', 'timed out', 'too large')):
                    raise Pesado(f'{rotulo}: {msg[:300]}')
                if k == tentativas - 1:
                    raise RuntimeError(f'{rotulo}: {msg[:300]}')
                # [v2] 429 = pedidos simultâneos demais (não é cota): espera mais antes de tentar de novo
                limite = '429' in msg or 'too many' in msg.lower()
                if limite:
                    log(f'   ↻ {rotulo}: servidor ocupado (429); nova tentativa em {60 * (k + 1)} s')
                time.sleep(60 * (k + 1) if limite else 20)

    def em_lotes(itens, montar, rotulo, lote):
        """montar(item) -> ee.Feature. Pede 'lote' itens por vez; lote recusado vai um por um."""
        linhas, sem = [], []
        for k in range(0, len(itens), lote):
            parte = itens[k:k + lote]
            try:
                linhas += [f['properties'] for f in gi(ee.FeatureCollection([montar(i) for i in parte]),
                                                       f'{rotulo} {parte[0]}', tentativas=2)['features']]
            except Exception:
                for i in parte:
                    try:
                        linhas += [f['properties'] for f in gi(ee.FeatureCollection([montar(i)]), f'{rotulo} {i}')['features']]
                    except Exception as e:
                        sem.append(i)
                        log(f'   {rotulo} {i}: não calculado ({str(e)[:150]})')
            log(f'   {rotulo}: {parte[0]} a {parte[-1]} ok')
        return linhas, sem

    def zip_parcial():
        try:
            pd.DataFrame(ACHADOS).to_csv(os.path.join(PASTA, 'K19_RESUMO.csv'), sep=';', index=False, encoding='utf-8-sig')
            pd.DataFrame(CANDIDATAS).to_csv(os.path.join(PASTA, 'K19_CANDIDATAS.csv'), sep=';', index=False,
                                            encoding='utf-8-sig')
            shutil.make_archive(PASTA, 'zip', PASTA)
        except Exception as e:
            log(f'   (zip parcial não feito: {e})')

    def parte(nome):
        def deco(fn):
            def rodar():
                while minutos_ate_janela(datetime.now(timezone(timedelta(hours=-3)))) == 0:
                    log('   ⏸️ janela do motor: pausa de 5 min')
                    time.sleep(300)
                log(f'\n{"-" * 100}\n{nome}\n{"-" * 100}')
                t = time.time()
                try:
                    fn()
                except Exception as e:
                    achado(nome.split()[0], 'NÃO EXECUTADO', nome, f'{type(e).__name__}: {str(e)[:400]}')
                    log(traceback.format_exc()[-1500:])
                log(f'   ({(time.time() - t) / 60:.1f} min)')
                zip_parcial()
            return rodar
        return deco

    carga = {}
    for nome, fonte, precisa in (('v10', FONTE_V10, ['processarDia_Definitivo']),
                                 ('v15', FONTE_V15, ['processarDia_Rota1', 'eto_penman_monteith', 'vpd_e_ea'])):
        carga[nome], pulados = carregar_codigo(nome, fonte, precisa, ee)
        log(f'   código {nome}: carregado ({len(pulados)} trecho(s) do fluxo principal ignorados)')

    def ra_mj(img_data):
        """Radiação no topo da atmosfera do dia (FAO-56, eq. 21), MJ/m²/dia, por pixel."""
        J = ee.Number(ee.Date(img_data).getRelative('day', 'year')).add(1)
        lat = LONLAT.select('latitude').multiply(math.pi / 180)
        dr = J.multiply(2 * math.pi / 365).cos().multiply(0.033).add(1)
        dec = J.multiply(2 * math.pi / 365).subtract(1.39).sin().multiply(0.409)
        ws = lat.tan().multiply(dec.tan()).multiply(-1).clamp(-1, 1).acos()
        return (ws.multiply(lat.sin()).multiply(dec.sin()).add(lat.cos().multiply(dec.cos()).multiply(ws.sin()))
                .multiply(dr).multiply(24 * 60 / math.pi * 0.0820))

    # ---------------------------------------------------------------------------------- D2 + D3
    @parte('D2 Controle de qualidade físico em todos os dias (por ano e classe) e D3 consistência espacial dos extremos')
    def d2_d3():
        nomes = [q[0] for q in QC]

        def bandeiras(img):
            g = img.select
            rso = ra_mj(img.get('system:time_start')).multiply(ELEV.multiply(2e-5).add(0.75))
            b = {
                'tmax_lt_tmin': g('tmax_C').lt(g('tmin_C')), 'pr_neg': g('pr_mm').lt(0),
                'rh_fora': g('RH').lt(0).Or(g('RH').gt(100.001)),
                'etr_gt_eto': g('et_real').gt(g('et_potencial').add(0.001)),
                'tr_gt_etr': g('transpiracao_mm').gt(g('et_real').add(0.001)), 'etr_neg': g('et_real').lt(0),
                'runoff_neg': g('runoff_sup_mm').lt(0).Or(g('runoff_sub_mm').lt(0)), 'vpd_neg': g('vpd').lt(0),
                'u2_neg': g('u2').lt(0), 'rs_neg': g('rs').lt(0), 'rs_gt_rso': g('rs').gt(rso.multiply(1.1)),
                'tmax_gt_45': g('tmax_C').gt(45), 'tmin_lt_m10': g('tmin_C').lt(-10), 'pr_gt_400': g('pr_mm').gt(400),
                'u2_gt_15': g('u2').gt(15), 'tsolo_fora': g('tsolo_C').lt(-10).Or(g('tsolo_C').gt(60)),
                'tfolha_fora': g('tfolha_C').lt(-20).Or(g('tfolha_C').gt(70)),
                'solo_gt_09': g('soil_moisture_0_5cm_m3_m3').gt(0.9001).Or(g('soil_moisture_0_100cm_m3_m3').gt(0.9001)),
            }
            validos = g('tmax_C').mask().rename('n')
            return ee.Image.cat([b[n].rename(n) for n in nomes] + [validos]).unmask(0).toInt()

        def montar(ano):
            col = COL.filterDate(f'{ano}-01-01', f'{ano + 1}-01-01')
            soma = col.map(bandeiras).sum()
            red = ee.Reducer.sum().unweighted().repeat(len(nomes) + 1).group(groupField=len(nomes) + 1, groupName='classe')
            qc = soma.addBands(CLASSE).reduceRegion(reducer=red, geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM,
                                                    maxPixels=1e10, tileScale=4)
            dentro = CLASSE.gte(1).And(CLASSE.lte(3))
            tmax = col.select('tmax_C').max()
            tmin = col.select('tmin_C').min()
            pr = col.select('pr_mm').max()
            eto = col.select('et_potencial').max()

            def ext(img, red_):
                return ee.Image.cat([img, LONLAT]).updateMask(dentro).reduceRegion(
                    reducer=red_, geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4)

            def mediana(img):
                return img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMedian(1, 'square', 'pixels')
            out_tmax = tmax.subtract(mediana(tmax)).gt(D3_TMAX)
            out_tmin = mediana(tmin).subtract(tmin).gt(D3_TMIN)
            med_pr = mediana(pr)
            out_pr = pr.gt(med_pr.multiply(D3_PR_FATOR)).And(pr.subtract(med_pr).gt(D3_PR_MIN))
            out_eto = eto.subtract(mediana(eto)).gt(D3_ETO)
            red3 = ee.Reducer.sum().unweighted().repeat(4).group(groupField=4, groupName='classe')
            d3 = (ee.Image.cat([out_tmax, out_tmin, out_pr, out_eto]).unmask(0).toInt().addBands(CLASSE)
                  .reduceRegion(reducer=red3, geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10,
                                tileScale=4))
            return ee.Feature(None, {
                'ano': ano, 'n_dias': col.size(), 'qc': qc.get('groups'), 'd3': d3.get('groups'),
                'tmax_max': ext(tmax, ee.Reducer.max(3)), 'tmin_min': ext(tmin, ee.Reducer.min(3)),
                'pr_max': ext(pr, ee.Reducer.max(3)), 'eto_max': ext(eto, ee.Reducer.max(3)),
                'tmax_dif_max': ext(tmax.subtract(mediana(tmax)), ee.Reducer.max(3)),
                'pr_dif_max': ext(pr.subtract(med_pr), ee.Reducer.max(3))})

        linhas, sem = em_lotes(list(range(1961, ANO_FIM + 1)), montar, 'D2', LOTE_ANOS_D2)
        qc_linhas, d3_linhas, ext_linhas = [], [], []
        for p in linhas:
            for g in p.get('qc') or []:
                vals = g.get('sum', [])
                qc_linhas.append({'ano': p['ano'], 'classe': CLASSES.get(int(g['classe']), 'sem classe'),
                                  **dict(zip(nomes + ['n'], vals))})
            for g in p.get('d3') or []:
                v = list(g.get('sum', [])) + [0, 0, 0, 0]
                d3_linhas.append({'ano': p['ano'], 'classe': CLASSES.get(int(g['classe']), 'sem classe'),
                                  'tmax_isolada': v[0], 'tmin_isolada': v[1], 'chuva_isolada': v[2], 'eto_isolada': v[3]})
            e = {'ano': p['ano'], 'n_dias': p.get('n_dias')}
            for chave, pref in (('tmax_max', 'max'), ('tmin_min', 'min'), ('pr_max', 'max'), ('eto_max', 'max'),
                                ('tmax_dif_max', 'max'),
                                ('pr_dif_max', 'max')):
                dct = p.get(chave) or {}
                e[chave], e[f'{chave}_lon'], e[f'{chave}_lat'] = dct.get(pref), dct.get(f'{pref}1'), dct.get(f'{pref}2')
            ext_linhas.append(e)
        qc = pd.DataFrame(qc_linhas)
        qc = qc[qc['classe'] != 'sem classe']
        salvar_csv(qc, 'D2_qc_por_ano_e_classe.csv')
        ext = pd.DataFrame(ext_linhas).sort_values('ano')
        salvar_csv(ext, 'D3_extremos_por_ano.csv')
        d3 = pd.DataFrame(d3_linhas)
        salvar_csv(d3, 'D3_pixels_isolados_por_ano.csv')
        st, det, tab = resumo_qc(qc[qc['classe'] != 'borda'])
        salvar_csv(tab, 'D2_qc_resumo.csv')
        log(tab[tab['ocorrencias'] > 0].to_string(index=False) if (tab['ocorrencias'] > 0).any() else '   nenhuma ocorrência')
        achado('D2', st, 'Controle de qualidade físico (todos os dias; classes A, B e C)',
               det + (f' | anos não calculados: {sem}' if sem else ''))
        for r in tab[(tab['ocorrencias'] > 0) & (tab['tipo'] != 'conhecido')].itertuples():
            candidata('D2', f'{r.descricao} nos pixels {r.classe}: {r.ocorrencias} pixel-dias ({r.anos})',
                      'na leitura (histórico) ou no motor (2026+), conforme o ano' if r.tipo == 'duro'
                      else 'conferir o local e decidir (pode ser real)', f'{100 * r.fracao:.4f}% dos pixel-dias',
                      'WMO-No. 1269; FAO-56' if 'radiação' in r.descricao else 'WMO-No. 1269; ETCCDI')
        # D3
        log(ext[['ano', 'tmax_max', 'tmin_min', 'pr_max', 'eto_max', 'tmax_dif_max', 'pr_dif_max']].to_string(index=False))
        iso = (d3[d3['classe'] == 'A'][['tmax_isolada', 'tmin_isolada', 'chuva_isolada', 'eto_isolada']].sum()
               if len(d3) else None)
        det3 = (f'Tmax máxima do acervo {ext["tmax_max"].max():.1f} °C, Tmin mínima {ext["tmin_min"].min():.1f} °C, '
                f'chuva máxima {ext["pr_max"].max():.0f} mm/dia, ETo máxima {ext["eto_max"].max():.1f} mm/dia')
        if iso is not None:
            det3 += (f' | máximos anuais isolados nos pixels A (foge da mediana dos vizinhos): Tmax {int(iso["tmax_isolada"])}, '
                     f'Tmin {int(iso["tmin_isolada"])}, chuva {int(iso["chuva_isolada"])}, ETo {int(iso["eto_isolada"])} '
                     f'pixel-anos')
        st3 = 'ATENÇÃO' if iso is not None and iso.sum() > 0 else 'OK'
        achado('D3', st3, 'Consistência espacial dos extremos anuais', det3)
        if iso is not None and iso.sum() > 0:
            pior = ext.sort_values('tmax_dif_max', ascending=False).iloc[0]
            candidata('D3', f'máximos anuais isolados nos pixels A (Tmax {int(iso["tmax_isolada"])}, Tmin '
                      f'{int(iso["tmin_isolada"])}, chuva {int(iso["chuva_isolada"])}, ETo {int(iso["eto_isolada"])}); '
                      f'maior Tmax isolada em '
                      f'{int(pior["ano"])} ({pior["tmax_dif_max_lon"]:.2f}, {pior["tmax_dif_max_lat"]:.2f})',
                      'conferir caso a caso (pode ser real); se erro, na leitura', 'ver D3_*.csv',
                      'teste espacial (Hubbard & You 2005); WMO-No. 1269')

    # ---------------------------------------------------------------------------------- D4
    @parte('D4 Coerência: ETo gravada x FAO-56 Penman-Monteith do motor; VPD gravado x recalculado')
    def d4():
        dias = DIAS_D1 + [f'2026-{m:02d}-15' for m in range(1, 11)]
        A = CLASSE.eq(1)

        def montar(d):
            s = ee.Image(f'{ASSET_SAB}/SAB_{d.replace("-", "_")}')
            g = s.select
            eto = ee.Image(carga['v15']['eto_penman_monteith'](g('tmax_C'), g('tmin_C'), g('RH'), g('u2'), g('rs'), d))
            vpd = ee.Image(carga['v15']['vpd_e_ea'](g('tmax_C'), g('tmin_C'), g('RH'))[0])
            img = ee.Image.cat([eto.subtract(g('et_potencial')).rename('dif_eto'),
                                eto.subtract(g('et_potencial')).abs().rename('abs_eto'),
                                g('et_potencial').rename('eto_sab'), eto.rename('eto_pm'),
                                vpd.subtract(g('vpd')).abs().rename('abs_vpd')]).updateMask(A)
            return ee.Feature(None, img.reduceRegion(reducer=ee.Reducer.mean(), geometry=REGIAO, crs=CRS,
                                                     crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4)).set('data', d)

        linhas, sem = em_lotes(dias, montar, 'D4', 8)
        df = pd.DataFrame(linhas).sort_values('data')
        df['periodo'] = np.where(df['data'] <= FIM_HISTORICO, 'histórico (ETo do BR-DWGD)', '2026 (ETo do motor)')
        df['dif_pct'] = 100 * df['dif_eto'] / df['eto_sab']
        salvar_csv(df, 'D4_eto_vpd_por_dia.csv')
        res = df.groupby('periodo').agg(dias=('data', 'size'), eto_sab=('eto_sab', 'mean'), eto_pm=('eto_pm', 'mean'),
                                        dif_media=('dif_eto', 'mean'), dif_pct=('dif_pct', 'mean'),
                                        abs_media=('abs_eto', 'mean'), vpd_abs=('abs_vpd', 'mean')).reset_index()
        df['decada'] = df['data'].str[:3] + '0s'
        dec = df[df['data'] <= FIM_HISTORICO].groupby('decada').agg(dif_pct=('dif_pct', 'mean'),
                                                                     abs_media=('abs_eto', 'mean')).reset_index()
        salvar_csv(res, 'D4_resumo.csv')
        salvar_csv(dec, 'D4_por_decada.csv')
        log(res.to_string(index=False))
        log(dec.to_string(index=False))
        h = res[res['periodo'].str.startswith('histórico')].iloc[0]
        n26 = res[res['periodo'].str.startswith('2026')]
        det = (f'histórico (pixels A): ETo BR-DWGD {h.eto_sab:.2f} x FAO-56 do motor {h.eto_pm:.2f} mm/dia '
               f'({h.dif_pct:+.1f}%, erro médio {h.abs_media:.2f} mm/dia); VPD recalculado difere {h.vpd_abs:.4f} kPa')
        if len(n26):
            det += f' | 2026: diferença {n26.iloc[0].abs_media:.4f} mm/dia (o motor grava esta mesma conta)'
        salto = abs(h.dif_pct)
        st = 'ATENÇÃO' if salto > 3 or h.vpd_abs > 0.01 else 'OK'
        achado('D4', st, 'ETo e VPD coerentes com as outras variáveis', det + (f' | não calculados: {sem}' if sem else ''))
        if salto > 3:
            candidata('D4', f'a ETo do motor (2026, FAO-56 com a meteorologia) difere {h.dif_pct:+.1f}% da ETo do BR-DWGD '
                      f'para as mesmas variáveis: degrau na emenda 2025/2026',
                      'no motor (2026+): calibrar a ETo do motor contra a do BR-DWGD (matriz mensal) ou usar a mesma '
                      'formulação do BR-DWGD', f'{h.dif_pct:+.1f}%', 'Allen et al. 1998 (FAO-56); Xavier et al. 2022')

    # ---------------------------------------------------------------------------------- D5
    @parte('D5 Emenda 2025 -> 2026: ERA5 bruto x método atual x mapeamento de quantis, com o BR-DWGD como verdade')
    def d5():
        sorteio = (ee.Image.pixelLonLat().addBands(CLASSE)
                   .stratifiedSample(numPoints=0, classBand='classe', region=REGIAO, projection=PROJ, seed=SEMENTE,
                                     classValues=[1], classPoints=[N_PONTOS_D5], geometries=True, tileScale=4))
        pts = [{'pid': k, 'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1]}
               for k, f in enumerate(gi(sorteio, 'pontos D5')['features'])]
        chave = {(int(math.floor((p['lon'] - X0) / DX + 1e-6)), int(math.floor((Y0 - p['lat']) / DX + 1e-6))): p['pid']
                 for p in pts}
        salvar_csv(pd.DataFrame(pts), 'D5_pontos.csv')
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']}) for p in pts])
        mp = ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in pts])
        # médias mensais da matriz que o motor usa (SICSB_1986_2025)
        bandas = [f'{b}_m_{f}' for b in BANDAS_MATRIZ_D5 for f in ('br', 'era')]
        mats = ee.Image.cat([ee.Image(f'{ASSET_CLIMA}/Matriz_Clima_{m:02d}').select(bandas)
                             .rename([f'{b}__{m}' for b in bandas]) for m in range(1, 13)])
        am = gi(mats.sampleRegions(collection=fc, properties=['pid'], projection=PROJ, geometries=False), 'matriz D5')
        mm = []
        for f in am['features']:
            p = f['properties']
            for m in range(1, 13):
                mm.append({'pid': p['pid'], 'mes': m, **{b: p.get(f'{b}__{m}') for b in bandas}})
        meses_matriz = pd.DataFrame(mm)

        def era_prep(img):
            # as mesmas conversões do motor V1.5 (_componentes_era5), antes da calibração
            t2 = img.select('temperature_2m').subtract(273.15).resample('bilinear')
            td = img.select('dewpoint_temperature_2m').subtract(273.15).resample('bilinear')
            rh = t2.expression('100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))',
                               {'T': t2, 'Td': td})
            return ee.Image.cat([img.select('total_precipitation_sum').multiply(1000).max(0).rename('era_pr'),
                                 img.select('temperature_2m_max').subtract(273.15).resample('bilinear').rename('era_tmax'),
                                 img.select('temperature_2m_min').subtract(273.15).resample('bilinear').rename('era_tmin'),
                                 rh.rename('era_rh'),
                                 img.select('surface_solar_radiation_downwards_sum').divide(1e6).resample('bilinear')
                                 .rename('era_rs'),
                                 img.select('u_component_of_wind_10m').hypot(img.select('v_component_of_wind_10m'))
                                 .multiply(0.748).resample('bilinear').rename('era_u2')]
                                ).copyProperties(img, ['system:time_start'])

        def br_prep(img):
            # decodificação do BR-DWGD como na V1.0
            m = img.select('pr').gt(-32768)
            dec = lambda b, e, a: img.select(b).updateMask(m).multiply(e).add(a)
            return ee.Image.cat([dec('pr', 0.00686666, 225.0).max(0).rename('br_pr'),
                                 dec('Tmax', 0.00106815, 15.0).rename('br_tmax'),
                                 dec('Tmin', 0.00106815, 15.0).rename('br_tmin'),
                                 dec('RH', 0.39370079, -0.393701).clamp(0, 100).rename('br_rh'),
                                 dec('Rs', 0.15708661, -0.057087).rename('br_rs'),
                                 dec('u2', 0.05905512, -0.059055).rename('br_u2')]
                                ).copyProperties(img, ['system:time_start'])

        def regiao(ini, fim, lista, rotulo):
            """[v4] getRegion de UM mês; se pesado, divide os pontos ao meio (até 10 por pedido)."""
            par = ee.Join.inner().apply(ERACOL.filterDate(ini, fim).map(lambda i: ee.Image(era_prep(i))),
                                        BRCOL.filterDate(ini, fim).map(lambda i: ee.Image(br_prep(i))),
                                        ee.Filter.maxDifference(difference=12 * 3600 * 1000, leftField='system:time_start',
                                                                rightField='system:time_start'))
            junto = ee.ImageCollection(par.map(lambda f: ee.Image.cat([ee.Image(f.get('primary')),
                                                                       ee.Image(f.get('secondary'))])
                                               .set('system:time_start', ee.Image(f.get('primary')).get('system:time_start'))))
            try:
                reg = gi(junto.getRegion(ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in lista]), None, CRS,
                                         TRANSFORM), rotulo)
                return [reg[0]] + reg[1:]
            except Pesado:
                if len(lista) <= 10:
                    raise
                meio = len(lista) // 2
                log(f'   {rotulo}: pesado, dividindo os pontos ({len(lista)} -> {meio} + {len(lista) - meio})')
                a, b = regiao(ini, fim, lista[:meio], rotulo), regiao(ini, fim, lista[meio:], rotulo)
                return a + b[1:]

        quadros = []
        for ano in ANOS_TREINO_D5 + ANOS_TESTE_D5:
            linhas_ano, cab = [], None
            for mes in range(1, 13):
                ini = f'{ano}-{mes:02d}-01'
                fim = f'{ano + 1}-01-01' if mes == 12 else f'{ano}-{mes + 1:02d}-01'
                reg = regiao(ini, fim, pts, f'D5 {ano}-{mes:02d}')
                cab = reg[0]
                linhas_ano += reg[1:]
            df = pd.DataFrame(linhas_ano, columns=cab)
            ix = np.floor((df['longitude'].astype(float) - X0) / DX + 1e-6).astype(int)
            iy = np.floor((Y0 - df['latitude'].astype(float)) / DX + 1e-6).astype(int)
            df['pid'] = [chave.get((a, b)) for a, b in zip(ix, iy)]
            df['data'] = pd.to_datetime(df['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
            df = df.dropna(subset=['pid'])
            quadros.append(df[['pid', 'data'] + [f'era_{v}' for v in VARS_D5] + [f'br_{v}' for v in VARS_D5]])
            log(f'   D5 {ano}: {len(df)} pixel-dias')
        dados = pd.concat(quadros, ignore_index=True)
        dados['pid'] = dados['pid'].astype(int)
        tab, texto, cand = avaliar_d5(dados, meses_matriz)
        salvar_csv(tab, 'D5_metricas_teste_2024_2025.csv')
        log(tab.to_string(index=False))
        achado('D5', 'ATENÇÃO' if cand else 'INFO',
               'Emenda 2025/2026 (chuva, Tmax, Tmin, UR, radiação, vento): correção só na média x mapeamento de quantis', texto)
        if cand:
            candidata('D5', 'nos dias de 2026 (ERA5 corrigido só na média) a frequência de dias com chuva e/ou os extremos '
                      'ficam longe do BR-DWGD; o mapeamento de quantis reduz o erro sem piorar o total mensal',
                      'no motor, só 2026 em diante (V1.6), com simulação e validação fora da amostra antes',
                      texto.split('|', 1)[1].strip() if '|' in texto else texto,
                      'Teutschbein & Seibert 2012; Cannon et al. 2015 (QDM)')
        t = tab[tab['variavel'] != 'chuva'].set_index(['variavel', 'metodo'])
        nomes_v = {'tmax': 'Tmax', 'tmin': 'Tmin', 'rh': 'UR', 'rs': 'radiação', 'u2': 'vento'}
        for v in VARS_D5[1:]:
            a, q = t.loc[(v, 'atual (média, V1.5)')], t.loc[(v, 'quantis (EQM)')]
            log(f'   {nomes_v[v]}: atual viés {a["vies"]:+.2f}, desvios x{a["razao_desvio"]:.2f}, erro diário '
                f'{a["erro_diario"]:.2f} | EQM viés {q["vies"]:+.2f}, desvios x{q["razao_desvio"]:.2f}, erro diário '
                f'{q["erro_diario"]:.2f}')
            if abs(a['razao_desvio'] - 1) > 0.15:
                candidata('D5', f'{nomes_v[v]} de 2026: a amplitude das anomalias diárias é {a["razao_desvio"]:.2f}x a do '
                          f'BR-DWGD (a correção só na média não ajusta a variância)',
                          'no motor, só 2026 em diante (escala de variância, como na previsão GFS desde a K8, ou EQM)',
                          f'razão dos desvios {a["razao_desvio"]:.2f} (EQM: {q["razao_desvio"]:.2f})',
                          'Teutschbein & Seibert 2012; K8')
            if abs(a['vies']) > {'tmax': 0.5, 'tmin': 0.5, 'rh': 3.0, 'rs': 1.0, 'u2': 0.3}[v]:
                candidata('D5', f'{nomes_v[v]} de 2026: viés de {a["vies"]:+.2f} contra o BR-DWGD em 2024-2025, mesmo com '
                          f'a correção na média', 'no motor, só 2026 em diante', f'viés {a["vies"]:+.2f}',
                          'Teutschbein & Seibert 2012')

    # ---------------------------------------------------------------------------------- D6
    @parte('D6 Homogeneidade relativa (SAB x ERA5-Land e x CHIRPS, por estado, jan-set de 1961 a 2026) e costura de 2026')
    def d6():
        A = CLASSE.eq(1)
        vars_s = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'rs', 'u2', 'et_real']
        soma = {'pr_mm', 'et_real'}

        def era_dia(img):
            t2 = img.select('temperature_2m').subtract(273.15)
            td = img.select('dewpoint_temperature_2m').subtract(273.15)
            rh = t2.expression('100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))',
                               {'T': t2, 'Td': td})
            return ee.Image.cat([
                img.select('total_precipitation_sum').multiply(1000).max(0).rename('pr_mm'),
                img.select('temperature_2m_max').subtract(273.15).rename('tmax_C'),
                img.select('temperature_2m_min').subtract(273.15).rename('tmin_C'), rh.rename('RH'),
                img.select('surface_solar_radiation_downwards_sum').divide(1e6).rename('rs'),
                img.select('u_component_of_wind_10m').hypot(img.select('v_component_of_wind_10m')).multiply(0.748).rename('u2'),
                img.select('total_evaporation_sum').multiply(-1000).max(0).rename('et_real')])

        def agrega(col):
            return ee.Image.cat([col.select(v).sum() if v in soma else col.select(v).mean() for v in vars_s])

        def montar(ano):
            ini, fim = ee.Date.fromYMD(ano, 1, 1), ee.Date.fromYMD(ano, MES_FIM_D6 + 1, 1)
            s = agrega(COL.filterDate(ini, fim).select(vars_s)).rename([f's_{v}' for v in vars_s])
            r = agrega(ERACOL.filterDate(ini, fim).map(era_dia)).rename([f'r_{v}' for v in vars_s])
            fc = ee.Image.cat([s, r]).updateMask(A).reduceRegions(collection=UFS, reducer=ee.Reducer.mean(), crs=CRS,
                                                                   crsTransform=TRANSFORM, tileScale=4)
            if ano >= 1981:
                ch = ee.ImageCollection(CHIRPS).filterDate(ini, fim).select('precipitation').sum().rename('c_pr')
                fc = ch.updateMask(A).reduceRegions(collection=fc, reducer=ee.Reducer.mean().setOutputs(['c_pr']),
                                                    scale=5566, tileScale=4)
            return ee.Feature(None, {'ano': ano, 'ufs': fc.toList(40).map(lambda f: ee.Feature(f).toDictionary())})

        linhas, sem = em_lotes(ANOS_D6, montar, 'D6', LOTE_ANOS_D6)
        reg = []
        for p in linhas:
            for u in p.get('ufs') or []:
                reg.append({'ano': p['ano'], 'uf': u.get('ADM1_NAME'), **{k: v for k, v in u.items() if k != 'ADM1_NAME'}})
        bruto = pd.DataFrame(reg)
        salvar_csv(bruto, 'D6_series_por_estado.csv')
        series = []
        for v in vars_s:
            if f's_{v}' not in bruto:
                continue
            if v in soma:
                d = bruto[f's_{v}'] / bruto[f'r_{v}'].replace(0, np.nan)
            else:
                d = bruto[f's_{v}'] - bruto[f'r_{v}']
            series.append(pd.DataFrame({'uf': bruto['uf'], 'ano': bruto['ano'], 'variavel': f'{v} (SAB x ERA5)', 'd': d}))
        if 'c_pr' in bruto:
            series.append(pd.DataFrame({'uf': bruto['uf'], 'ano': bruto['ano'], 'variavel': 'pr_mm (SAB / CHIRPS)',
                                        'd': bruto['s_pr_mm'] / bruto['c_pr'].replace(0, np.nan)}))
        series = pd.concat(series, ignore_index=True)
        tab = homogeneidade(series, ANOS_D6)
        salvar_csv(tab, 'D6_homogeneidade_por_estado.csv')
        grupos = agrupar_quebras(tab)
        salvar_csv(grupos, 'D6_quebras_em_varios_estados.csv')
        zc = f'z_{ANO_FIM}'
        cost = tab[tab[zc].abs() > 3]
        cost_v = cost.groupby('variavel').size().to_dict()
        log(grupos.to_string(index=False) if len(grupos) else '   nenhuma quebra repetida em 5 ou mais estados')
        det = (f'{len(tab)} séries (estado x variável); {int(tab["quebra"].sum())} com quebra (Pettitt e SNHT, p < {P_LIMITE}) | '
               + ('quebras repetidas: ' + '; '.join(f'{r.variavel} ~{r.ano_central} em {r.estados} estados (salto '
                                                    f'{r.salto_medio:+.3f})' for r in grupos.itertuples())
                  if len(grupos) else 'nenhuma quebra repetida em 5+ estados')
               + f' | costura {ANO_FIM} (|z| > 3): ' + (', '.join(f'{k}: {v} estados' for k, v in cost_v.items())
                                                      if cost_v else 'nenhuma'))
        st = 'ATENÇÃO' if len(grupos) or cost_v else 'OK'
        achado('D6', st, 'Homogeneidade das séries e costura de 2026', det + (f' | anos não calculados: {sem}' if sem else ''))
        for r in grupos.itertuples():
            candidata('D6', f'quebra em {r.variavel} por volta de {r.ano_central} em {r.estados} estados (salto médio '
                      f'{r.salto_medio:+.3f})',
                      'só documentar se vier da referência (ERA5 antes de 1979, por exemplo) ou da rede de estações do '
                      'BR-DWGD; homogeneizar só com referência independente concordando', 'ver D6_*.csv',
                      'Pettitt 1979; Alexandersson 1986; Peterson et al. 1998')
        for v, k in cost_v.items():
            candidata('D6', f'{v}: 2026 fora do intervalo de 1996-2025 (|z| > 3) em {k} estados',
                      'no motor (2026+): é a emenda entre o BR-DWGD e o ERA5 calibrado', 'ver D6_homogeneidade',
                      'Peterson et al. 1998')

    # ---------------------------------------------------------------------------------- D1
    @parte('D1 Reprodução das 16 bandas pelo código: 1 dia por ano (1961-2025, V1.0) e 2026 (V1.5), pixels sorteados')
    def d1():
        dias = [(d, 'v10') for d in DIAS_D1] + [(f'2026-{m:02d}-15', 'v15') for m in range(1, 11)]
        cls = sorted(PONTOS_D1)
        sorteio = (ee.Image.pixelLonLat().addBands(CLASSE)
                   .stratifiedSample(numPoints=0, classBand='classe', region=REGIAO, projection=PROJ, seed=SEMENTE,
                                     classValues=cls, classPoints=[PONTOS_D1[c] for c in cls], geometries=True,
                                     tileScale=4))
        pts = [{'pid': k, 'classe': int(f['properties']['classe']), 'lon': f['geometry']['coordinates'][0],
                'lat': f['geometry']['coordinates'][1]} for k, f in enumerate(gi(sorteio, 'pontos D1')['features'])]
        salvar_csv(pd.DataFrame(pts), 'D1_pontos.csv')
        log(f'   D1: {len(pts)} pixels (' + ', '.join(f'{CLASSES[c]} {sum(p["classe"] == c for p in pts)}' for c in cls) + ')')
        lote = {'s': LOTE_D1, 'r': LOTE_D1}

        def amostra(img, chave, rotulo):
            """Uma imagem por vez, em lotes; se pesado, o lote cai pela metade e fica lembrado."""
            linhas, i = [], 0
            while i < len(pts):
                sub = pts[i:i + lote[chave]]
                fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']})
                                           for p in sub])
                try:
                    res = gi(img.sampleRegions(collection=fc, properties=['pid'], projection=PROJ, tileScale=16,
                                               geometries=False), rotulo)
                    linhas += [f['properties'] for f in res['features']]
                    i += len(sub)
                except Pesado:
                    if lote[chave] <= LOTE_MINIMO_D1:
                        raise
                    lote[chave] = max(LOTE_MINIMO_D1, lote[chave] // 2)
                    log(f'   {rotulo}: pesado, lote reduzido para {lote[chave]} pixels')
            return pd.DataFrame(linhas)

        base = pd.DataFrame(pts)[['pid', 'classe']]
        linhas, sem = [], []
        for d, rota in dias:
            try:
                s_ = ee.Image(f'{ASSET_SAB}/SAB_{d.replace("-", "_")}').select(ORDEM).rename([f's_{b}' for b in ORDEM])
                r_ = ee.Image(carga['v10']['processarDia_Definitivo'](d) if rota == 'v10'
                              else carga['v15']['processarDia_Rota1'](d)).select(ORDEM).toFloat() \
                    .rename([f'r_{b}' for b in ORDEM])
                df = base.copy()
                for img, chave in ((s_, 's'), (r_, 'r')):
                    parte_df = amostra(img, chave, f'D1 {d} {chave}')
                    if 'pid' in parte_df:
                        df = df.merge(parte_df, on='pid', how='left')
                for pref in ('s_', 'r_'):
                    for b in ORDEM:
                        if f'{pref}{b}' not in df:
                            df[f'{pref}{b}'] = np.nan
                for c, sub in df.groupby('classe'):
                    if c not in CLASSES:
                        continue
                    r = {'data': d, 'rota': rota, 'classe': CLASSES[c], 'n': len(sub)}
                    for b in ORDEM:
                        r[f'frac_{b}'] = float(iguais_np(sub[f's_{b}'], sub[f'r_{b}']).mean())
                        r[f'abs_{b}'] = float((sub[f's_{b}'] - sub[f'r_{b}']).abs().mean())
                    linhas.append(r)
                log(f'   D1 {d} ({rota}): ok')
            except Exception as e:
                sem.append(d)
                log(f'   D1 {d}: não calculado ({str(e)[:150]})')
        df = pd.DataFrame(linhas)
        salvar_csv(df, 'D1_reproducao_por_dia_e_classe.csv')
        tipos, cont, outros = classificar_d1(linhas)
        salvar_csv(tipos, 'D1_tipo_por_dia.csv')
        log(tipos[tipos['tipo'] != 'idênticos'].to_string(index=False) if (tipos['tipo'] != 'idênticos').any()
            else '   todos os dias idênticos')
        hist = tipos[tipos['data'] <= FIM_HISTORICO]
        prim = hist[hist['tipo'] != 'idênticos']['data'].min() if (hist['tipo'] != 'idênticos').any() else None
        det = (f'{len(tipos)} dias: idênticos {cont["idênticos"]}, só ERA5 acumulado {cont["só ERA5 acumulado"]}, '
               f'outra diferença {cont["outra diferença"]}' + (f' (dias: {outros[:8]})' if outros else '') +
               (f' | primeiro dia do histórico com diferença: {prim}' if prim else '') +
               (f' | não calculados: {sem}' if sem else ''))
        st = 'FALHA' if outros else ('ATENÇÃO' if cont['só ERA5 acumulado'] else 'OK')
        achado('D1', st, 'Reprodução das 16 bandas pelo código (pixels sorteados de todas as classes)', det)
        if outros:
            candidata('D1', f'diferença fora das variáveis acumuladas do ERA5 em {len(outros)} dia(s): {outros[:8]}',
                      'investigar antes de qualquer correção (D1_*.csv mostra banda e classe)', 'ver D1_*.csv', '-')

    for nome_p, fn in (('D2', d2_d3), ('D4', d4), ('D5', d5), ('D6', d6), ('D1', d1)):
        if nome_p in PARTES:
            fn()

    # ---------------------------------------------------------------------------------- resultado
    log('\n' + '=' * 100 + '\nRESULTADO K19 (auditoria profunda; nada é aprovado ou reprovado aqui)\n' + '=' * 100)
    for a in ACHADOS:
        log(f"   {a['parte']:3} {a['status']:13} {a['titulo']}")
    log('\nCANDIDATAS A CORREÇÃO (decidir juntos; nada foi corrigido):')
    if CANDIDATAS:
        for i, c in enumerate(CANDIDATAS, 1):
            log(f"   {i}. [{c['parte']}] {c['divergencia']}\n      correção permitida: {c['correcao_permitida']} | "
                f"tamanho: {c['tamanho']} | referência: {c['referencia']}")
    else:
        log('   nenhuma além das já conhecidas (revisão do ERA5 desde 2017; pixels B)')
    log(f'\nTempo: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine (trava de somente leitura).')
    zip_parcial()
    log(f'📦 {PASTA}.zip  <- me envie este zip')
    try:
        from google.colab import files
        files.download(PASTA + '.zip')
    except Exception:
        pass


if __name__ == '__main__':
    principal()
