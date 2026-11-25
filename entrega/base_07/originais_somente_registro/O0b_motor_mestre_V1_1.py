# ⛔⛔⛔ NÃO EXECUTAR: SCRIPT ORIGINAL GUARDADO SÓ COMO REGISTRO DO MÉTODO (metodologia da tese) ⛔⛔⛔
# Gerou: projects/clima-492922/assets/nenhum dia do histórico (conferido: 0 dias com versao_algoritmo); pode ter gravado dias provisórios de 2026, já recalculados pelas versões seguintes
# Hoje: Sem efeito no banco hoje. Registro da evolução do motor.
# Substituído por: V1.2 e V1.3 (O1) e depois V1.5
# Por que não rodar: ele RECRIARIA o asset acima; o banco, as calibrações e as validações (K8 a K16, 07a/07b,
#   08) foram aprovados com o asset que já existe. Rodar de novo exigiria refazer e validar tudo.
# Recebido do responsável em 03/11/2026 (motores_V1_0_V1_1_e_utilitarios_recebidos.txt, linhas 923 a 1781). Abaixo da linha ORIGINAL, o texto está sem nenhuma
#   mudança. SHA-256 do trecho original: b6c31ed226384ecf708d410e040022377d4d4d65d3ad1d7dbb2b66bd60028273
# A linha raise SystemExit abaixo faz a célula parar antes de qualquer import ou gravação.
raise SystemExit('⛔ Script original guardado só como registro. NÃO EXECUTAR (veja o cabeçalho).')
# ================================================ ORIGINAL ================================================
# =========================================================================================
# TÍTULO: MOTOR MESTRE OPERACIONAL SAB V1.1 - SCRIPT 1 (CONTA CLIMA)
# RESUMO DA FUNÇÃO: Autenticação, processamento e tarefas isoladas para clima-492922
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
ASSET_DESTINO_MATRIZ_GFS = 'projects/clima-492922/assets/SICSB_MATRIZ_GFS'
ASSET_SOLO = 'projects/clima-492922/assets/SICSB_SOLO_2015_2025'

VERSAO_ALGORITMO = 'V1.1'
# True: modo simulação. Lê o acervo e informa o que seria feito, sem exportar,
# apagar, renomear ou criar nenhum asset. Rode assim antes da primeira execução real.
SIMULAR = True
# True: dias gravados com versão anterior do algoritmo são reprocessados ao longo de
# várias execuções. Ative só depois de medir o impacto da nova calibração (piso/limite
# do fator) no histórico; a transpiração da V1.0 já estava correta.
REPROCESSAR_VERSAO_ANTIGA = False

HORIZONTE_DIAS = 15              # GFS vai até 384 h; o 16º dia nunca fica completo
JANELA_OPERACIONAL_DIAS = 90     # dias recentes processados com prioridade
DIAS_BUSCA_RODADAS = 12          # quantos dias de rodadas GFS considerar
LIMITE_TAREFAS_MAX = 3000
RESERVA_OPERACIONAL = 100        # vagas que o histórico nunca consome
INTERVALO_POLL_S = 30
TIMEOUT_TAREFA_MIN = 120

DATA_INICIO_P1 = '1991-01-01'
DATA_INICIO_P2 = '1961-01-01'
DATA_FIM_P2 = '1990-12-31'

# Piso físico da calibração multiplicativa (unidade da variável, média diária mensal).
# Fator = (alvo + piso) / (modelo + piso), limitado a [FATOR_MIN, FATOR_MAX].
PISO_CALIB = {
    'pr': 0.1, 'u2': 0.1, 'Rs': 1.0, 'ET': 0.1,
    'ssur': 0.01, 'swat': 0.01, 'rsup': 0.05, 'rsub': 0.05,
}
FATOR_MIN, FATOR_MAX = 0.2, 5.0

# Balde de solo do GFS (valores da V1 mantidos; ajuste conforme o máximo do SMAP calibrado)
SW100_MAX_MM = 400.0
SW100_CC_MM = 330.0
SW5_MAX_MM = 25.0

ORDEM_BANDAS = [
    'pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd',
    'rs', 'u2', 'tsolo_C', 'tfolha_C', 'transpiracao_mm',
    'runoff_sup_mm', 'runoff_sub_mm',
    'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3',
]
VERSOES_GFS = ('provisoria_gfs', 'provisoria_gfs_incompleta', 'falha_latencia_gfs')
ESTADOS_ATIVOS = ('READY', 'RUNNING', 'SUBMITTED', 'PENDING')
ESTADOS_FINAIS = ('COMPLETED', 'FAILED', 'CANCELLED')

fuso_br = timezone(timedelta(hours=-3))
data_extracao_local = datetime.now(fuso_br).strftime('%Y-%m-%d %H:%M:%S')
data_hoje_dt = datetime.now(timezone.utc)
data_hoje_str = data_hoje_dt.strftime('%Y-%m-%d')
data_fim_processo = (data_hoje_dt + timedelta(days=HORIZONTE_DIAS)).strftime('%Y-%m-%d')

print(f"🔄 Iniciando SAB {VERSAO_ALGORITMO} no projeto: {PROJECT_ID_ATIVO}...")
print(f"🕒 Timestamp de Operação (Local/BRT): {data_extracao_local}\n")

try:
    ee.Initialize(project=PROJECT_ID_ATIVO)
except Exception:
    print("🔗 Autenticação necessária:")
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID_ATIVO)

# =========================================================================
# 2. OBJETOS GLOBAIS
# =========================================================================
_gaul_br = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
limitesRegiao = _gaul_br.geometry().bounds()
poligonoBrasil = _gaul_br.geometry().simplify(500)   # erro máx. 500 m, muito abaixo do pixel de ~11 km
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


# Últimas datas disponíveis (falha aqui interrompe: decidir rota sem essa informação é inseguro)
_ini_busca = ee.Date(data_hoje_dt.strftime('%Y-%m-%d')).advance(-150, 'day')
_ms_era5 = colecao_era5.filterDate(_ini_busca, ee.Date(data_hoje_str).advance(1, 'day')) \
    .aggregate_max('system:time_start').getInfo()
if _ms_era5 is None:
    raise RuntimeError("Não foi possível determinar a última data do ERA5-Land.")
ultima_data_era5 = ms_para_data(_ms_era5)

_ms_brd = colChuvaGeral.aggregate_max('system:time_start').getInfo()
if _ms_brd is None:
    raise RuntimeError("Não foi possível determinar a última data do BR-DWGD.")
ultima_data_brd = ms_para_data(_ms_brd)

print(f"📡 Última data ERA5-Land: {ultima_data_era5} | Última data BR-DWGD: {ultima_data_brd}")

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


def promover_tmp(nome):
    """Substitui o asset definitivo pelo temporário já concluído."""
    tmp = f'{ASSET_TEMP}/{nome}'
    final = f'{ASSET_DESTINO}/{nome}'
    if not asset_existe(tmp):
        return False
    if asset_existe(final):
        ee.data.deleteAsset(final)
    ee.data.renameAsset(tmp, final)
    return True


def finalizar_trocas_pendentes(tarefas_ativas):
    if SIMULAR or not asset_existe(ASSET_TEMP):
        return
    promovidos = 0
    for nome in listar_nomes(ASSET_TEMP):
        if desc_de_nome(nome) in tarefas_ativas:
            continue
        if promover_tmp(nome):
            promovidos += 1
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
        })

    try:
        lista = col.map(para_feature) \
            .reduceColumns(ee.Reducer.toList().repeat(4), ['id', 'versao', 'alg', 'rodada']) \
            .get('list').getInfo()
    except Exception as e:
        raise RuntimeError(f"Falha ao inventariar {ASSET_DESTINO}; execução interrompida para evitar reenvio em massa. Detalhe: {e}")

    inventario = {}
    for idx, versao, alg, rodada in zip(*lista):
        inventario[str(idx).split('/')[-1]] = {
            'versao': versao, 'alg': alg,
            'rodada': int(float(rodada)) if rodada is not None else 0,
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


def calib_multiplicativa(img, m_alvo, m_modelo, chave):
    piso = PISO_CALIB[chave]
    fator = (expandir_borda(m_alvo).max(0).add(piso)
             .divide(expandir_borda(m_modelo).max(0).add(piso))
             .clamp(FATOR_MIN, FATOR_MAX))
    return img.multiply(fator)


def es_de(T):
    return T.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': T})


def vpd_e_ea(tmax, tmin, rh):
    es = es_de(tmax).add(es_de(tmin)).divide(2)
    ea = es.multiply(rh).divide(100)
    return es.subtract(ea).max(0).rename('vpd'), ea


def finalizar(img, propriedades):
    et_pot = img.select('et_potencial')
    et_real = img.select('et_real')
    transp = img.select('transpiracao_mm')
    et_real_l = et_real.min(et_pot.unmask(et_real)).rename('et_real')
    transp_l = transp.min(et_real_l).rename('transpiracao_mm')
    saida = (img.addBands(ee.Image.cat([et_real_l, transp_l]), overwrite=True)
             .select(ORDEM_BANDAS).toFloat().clip(poligonoBrasil))
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
    et_pot_raw = era.select('potential_evaporation_sum').multiply(-1000).max(0)

    c = {}
    c['pr_mm'] = calib_multiplicativa(pr_raw, *mc('pr'), 'pr').max(0).rename('pr_mm')
    c['u2'] = calib_multiplicativa(u2_raw, *mc('u2'), 'u2').max(0).rename('u2')
    c['rs'] = calib_multiplicativa(rs_raw, *mc('Rs'), 'Rs').max(0).rename('rs')
    c['tmax_C'] = calib_aditiva(tmax_raw, *mc('Tmax')).rename('tmax_C')
    c['tmin_C'] = calib_aditiva(tmin_raw, *mc('Tmin')).rename('tmin_C')
    c['RH'] = calib_aditiva(rh_raw, *mc('RH')).clamp(0, 100).rename('RH')
    c['et_potencial'] = calib_multiplicativa(et_pot_raw, *mc('ET'), 'ET').max(0).rename('et_potencial')
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
    rsup_era = era.select('surface_runoff_sum').multiply(1000).max(0)
    rsub_era = era.select('sub_surface_runoff_sum').multiply(1000).max(0)

    c['soil_moisture_0_5cm_m3_m3'] = calib_multiplicativa(ssur_era, *ms('ssur'), 'ssur').max(0) \
        .rename('soil_moisture_0_5cm_m3_m3')
    c['soil_moisture_0_100cm_m3_m3'] = calib_multiplicativa(swat_era, *ms('swat'), 'swat').max(0) \
        .rename('soil_moisture_0_100cm_m3_m3')
    c['runoff_sup_mm'] = calib_multiplicativa(rsup_era, *ms('rsup'), 'rsup').max(0).rename('runoff_sup_mm')
    c['runoff_sub_mm'] = calib_multiplicativa(rsub_era, *ms('rsub'), 'rsub').max(0).rename('runoff_sub_mm')
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
    has_real_br = imgBR.select('pr').gt(-90000)

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
        'et_potencial': imgBR.select('ET').multiply(0.05118110).add(-0.0511811),
        'rs': imgBR.select('Rs').multiply(0.15708661).add(-0.057087),
        'u2': imgBR.select('u2').multiply(0.05905512).add(-0.059055),
    }

    interior = ee.Image.cat([
        c[b].where(has_real_br, br[b]).rename(b) if b in br else c[b]
        for b in ORDEM_BANDAS
    ]).toFloat()
    fallback = expandir_borda(ee.Image.cat([c[b] for b in ORDEM_BANDAS]).toFloat())
    img = interior.unmask(fallback)

    return finalizar(img, {
        'system:time_start': dStart.millis(),
        'versao': 'definitiva',
        'versao_algoritmo': VERSAO_ALGORITMO,
    })


def processarDia_Rota1(data_str):
    c = _componentes_era5(data_str)
    img = expandir_borda(ee.Image.cat([c[b] for b in ORDEM_BANDAS]).toFloat())
    return finalizar(img, {
        'system:time_start': ee.Date(data_str).millis(),
        'versao': 'provisoria_era5',
        'versao_algoritmo': VERSAO_ALGORITMO,
    })


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
    horas_chuva = [float(h) for h in horas if h % 6 == 0]
    return len(horas), horas_chuva


def processarDia_GFS(data_str, estado_anterior, creation_ms, n_img_esperado, horas_chuva):
    data_atual = ee.Date(data_str)
    t0 = data_atual.millis()
    t1 = data_atual.advance(1, 'day').millis()
    mes = data_str[5:7]

    lat_rad = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180.0)
    pressao_atm = elevacao_br.multiply(-0.0065).add(293.0).divide(293.0).pow(5.26).multiply(101.3)
    gamma_dinamico = pressao_atm.multiply(0.000665)

    # CORRIGIDO: janela (00Z, 24Z]. Acumulados e extremos do GFS referem-se ao período
    # que TERMINA no forecast_time.
    gfs_dia = (colecao_gfs_rodada(creation_ms)
               .filter(ee.Filter.gt('forecast_time', t0))
               .filter(ee.Filter.lte('forecast_time', t1))
               .filter(ee.Filter.gt('forecast_hours', 0)))
    chuva_blocos = gfs_dia.filter(ee.Filter.inList('forecast_hours', horas_chuva))

    qtd_img = gfs_dia.size()
    qtd_chuva = chuva_blocos.size()

    if len(horas_chuva) >= 4:
        completo = qtd_img.gte(n_img_esperado).And(qtd_chuva.gte(4))
        versao_ok = ee.Algorithms.If(completo, 'provisoria_gfs', 'provisoria_gfs_incompleta')
    else:
        versao_ok = 'provisoria_gfs_incompleta'   # dia além do horizonte da rodada

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

    # Nota: radiação e UR por média simples das saídas; se o fluxo de onda curta do GFS for
    # média por bucket (como a chuva), há um viés pequeno a verificar.
    img_dia = ee.Image(ee.Algorithms.If(
        qtd_img.gt(0),
        ee.Image.cat([
            img_chuva,
            gfs_dia.select('maximum_temperature_2m_above_ground').max(),
            gfs_dia.select('minimum_temperature_2m_above_ground').min(),
            gfs_dia.select(['downward_shortwave_radiation_flux', 'relative_humidity_2m_above_ground']).mean(),
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
        alvo = f'{banda}_m_sicsb' if f'{banda}_m_sicsb' in bandas_cache else f'{banda}_m_sab'
        return cache_gfs.select(alvo), cache_gfs.select(f'{banda}_m_gfs')

    pr = calib_multiplicativa(pr_raw, *medias('pr'), 'pr').max(0).rename('pr_mm')
    tmax = calib_aditiva(tmax_raw, *medias('Tmax')).rename('tmax_C')
    tmin = calib_aditiva(tmin_raw, *medias('Tmin')).rename('tmin_C')
    rh = calib_aditiva(rh_raw, *medias('RH')).clamp(0, 100).rename('RH')
    u2 = calib_multiplicativa(u2_raw, *medias('u2'), 'u2').max(0).rename('u2')
    rs = calib_multiplicativa(rs_raw, *medias('Rs'), 'Rs').max(0).rename('rs')

    tmedia = tmax.add(tmin).divide(2)
    vpd, ea = vpd_e_ea(tmax, tmin, rh)

    # Penman-Monteith FAO-56 (inalterado da V1, verificado)
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
    et_potencial = num_1.add(num_2).divide(den).max(0).rename('et_potencial')

    # Balde de solo (parâmetros em constantes no topo)
    sw100 = estado_anterior.select('sw_100')
    sw5 = estado_anterior.select('sw_5')
    saturacao = sw100.divide(SW100_MAX_MM)
    cn = ee.Image.constant(60).add(saturacao.multiply(35))
    s_ret = ee.Image.constant(25400).divide(cn).subtract(254)
    p_ia = pr.subtract(s_ret.multiply(0.2)).max(0)
    runoff_sup = p_ia.pow(2).divide(p_ia.add(s_ret)).rename('runoff_sup_mm')
    infiltracao = pr.subtract(runoff_sup).max(0)

    kcb = vpd.multiply(-0.15).add(1.10).clamp(0.15, 1.05)
    tew = ee.Image.constant(20)
    rew = ee.Image.constant(8)
    kc_max = ee.Image.constant(1.2)
    d_e = tew.subtract(sw5).max(0)
    k_r = tew.subtract(d_e).divide(tew.subtract(rew)).clamp(0, 1)
    k_e = k_r.multiply(kc_max.subtract(kcb)).max(0)
    ks = sw100.subtract(100).divide(100).clamp(0.1, 1.0)

    evaporacao = k_e.multiply(et_potencial)
    transpiracao = kcb.multiply(ks).multiply(et_potencial)
    et_real = evaporacao.add(transpiracao).min(et_potencial).rename('et_real')
    transp_b = transpiracao.min(et_real).rename('transpiracao_mm')

    sw100_tmp = sw100.add(infiltracao).subtract(et_real)
    excesso = sw100_tmp.subtract(SW100_MAX_MM).max(0)
    drenagem = sw100_tmp.min(SW100_MAX_MM).subtract(SW100_CC_MM).max(0).multiply(0.04)
    runoff_sub = excesso.add(drenagem).rename('runoff_sub_mm')
    novo_sw100 = sw100_tmp.subtract(runoff_sub).clamp(0, SW100_MAX_MM)
    novo_sw5 = sw5.add(infiltracao).subtract(evaporacao).clamp(0, SW5_MAX_MM)

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
        .resample('bilinear').reproject(crs=crsNativo, crsTransform=transformNativo)
    img_ok = expandir_borda(img_ok)

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
        'Momento_Extracao_Local': data_extracao_local,
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
    v = info['versao']
    if v in VERSOES_GFS:
        return 'precisa_upgrade' if d_str <= ultima_data_era5 else 'gravado'
    if REPROCESSAR_VERSAO_ANTIGA and info['alg'] != VERSAO_ALGORITMO:
        return 'precisa_upgrade'
    if v == 'provisoria_era5' and d_str <= ultima_data_brd:
        return 'precisa_upgrade'
    return 'gravado'


def exportar(img, d_str, usar_tmp):
    global capacidade
    nome = id_dia(d_str)
    desc = desc_dia(d_str)
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
        st_ano = por_ano.setdefault(d[:4], {'gravado': 0, 'fila': 0, 'enviado': 0, 'adiado': 0})
        nome, desc = id_dia(d), desc_dia(d)
        if desc in tarefas:
            st_ano['fila'] += 1
            continue
        status = status_dia(d, inventario.get(nome))
        if status == 'gravado':
            st_ano['gravado'] += 1
            continue
        if capacidade <= reserva:
            st_ano['adiado'] += 1
            continue
        if SIMULAR:
            info = inventario.get(nome)
            rota = 'definitiva' if d <= ultima_data_brd else 'provisoria_era5'
            motivo = f"criar ({rota})" if info is None else f"refazer {info['versao']} -> {rota}"
            relatorio_sim[motivo] = relatorio_sim.get(motivo, 0) + 1
            capacidade -= 1
            st_ano['enviado'] += 1
            enviados.append(d)
            continue
        img = processarDia_Definitivo(d) if d <= ultima_data_brd else processarDia_Rota1(d)
        exportar(img, d, usar_tmp=(status == 'precisa_upgrade'))
        st_ano['enviado'] += 1
        enviados.append(d)
    for ano, s in sorted(por_ano.items()):
        if s['enviado'] or s['adiado'] or s['fila']:
            print(f"  📅 [{ano}] gravados {s['gravado']:,} | na fila {s['fila']:,} | "
                  f"enviados {s['enviado']:,} | adiados por capacidade {s['adiado']:,}")
    return enviados


def descobrir_rodadas_gfs():
    # A busca precisa cobrir todo o intervalo sem ERA5, senão dias passados ficam sem rodada
    lacuna = (data_hoje_dt.date() - datetime.strptime(ultima_data_era5, '%Y-%m-%d').date()).days
    dias_busca = max(DIAS_BUSCA_RODADAS, lacuna + 3)
    ini = (data_hoje_dt - timedelta(days=dias_busca)).strftime('%Y-%m-%d')
    fim = (data_hoje_dt + timedelta(days=1)).strftime('%Y-%m-%d')
    rodadas = ee.ImageCollection(COL_GFS).filterDate(ini, fim) \
        .aggregate_array('creation_time').distinct().getInfo()
    rodadas = sorted(int(float(r)) for r in rodadas)
    if not rodadas:
        raise RuntimeError("Nenhuma rodada GFS encontrada no período de busca.")

    referencia = None
    for r in reversed(rodadas[-4:]):
        stats = ee.Dictionary({
            'n': colecao_gfs_rodada(r).size(),
            'max': colecao_gfs_rodada(r).aggregate_max('forecast_hours'),
        }).getInfo()
        if stats.get('max') is not None and stats['max'] >= 384 and stats['n'] >= 198:
            referencia = r
            break
    if referencia is None:
        referencia = rodadas[-1]
        print("  ⚠️ Nenhuma das últimas rodadas está completa; usando a mais recente.")
    print(f"  🛰️ Rodada GFS de referência: "
          f"{datetime.fromtimestamp(referencia / 1000, tz=timezone.utc).strftime('%Y-%m-%d %HZ')}")
    return rodadas, referencia


def rodada_para_dia(d_str, rodadas, referencia):
    t0 = data_para_ms(d_str)
    if t0 >= referencia:
        return referencia
    candidatas = [r for r in rodadas if t0 - 48 * 3600000 <= r <= t0 and r <= referencia]
    return max(candidatas) if candidatas else referencia


def executar_cadeia_gfs(enviados_operacionais):
    dias = intervalo_datas(somar_dias(ultima_data_era5, 1), data_fim_processo)
    if not dias:
        return
    print(f"\n⚙ Cadeia GFS sequencial: {dias[0]} a {dias[-1]} ({len(dias)} dias).")
    rodadas, referencia = descobrir_rodadas_gfs()

    if not SIMULAR:
        aguardar_dia_pronto(ultima_data_era5)
    forcar = ultima_data_era5 in enviados_operacionais

    for d in dias:
        nome, desc = id_dia(d), desc_dia(d)
        caminho = f'{ASSET_DESTINO}/{nome}'
        if desc in tarefas and not SIMULAR:
            aguardar_tarefa(desc)
            promover_tmp(nome)

        rodada = rodada_para_dia(d, rodadas, referencia)
        info = info_de_propriedades(propriedades_asset(caminho))
        precisa = (forcar or info is None or info['rodada'] != rodada
                   or info['alg'] != VERSAO_ALGORITMO)
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

        n_img, horas_chuva = contagem_esperada(data_para_ms(d), rodada)
        img = processarDia_GFS(d, estado, rodada, n_img, horas_chuva)
        usar_tmp = info is not None
        exportar(img, d, usar_tmp)
        estado_final = aguardar_tarefa(desc)
        if estado_final != 'COMPLETED':
            raise RuntimeError(f"Falha na cadeia GFS: {desc} terminou com {estado_final}.")
        if usar_tmp:
            promover_tmp(nome)
        print(f"    ✔️ {d}: exportado ({n_img} imagens esperadas, {len(horas_chuva)} blocos de chuva).")


# --- Execução ---
relatorio_sim = {}
if SIMULAR:
    print("🧪 MODO SIMULAÇÃO ATIVO: nenhum asset será criado, apagado ou exportado.\n")
inicio_janela = min(somar_dias(data_hoje_str, -JANELA_OPERACIONAL_DIAS), ultima_data_era5)

# 1) Janela operacional histórica (recente, ERA5 / BR-DWGD) sem reserva
enviados_op = despachar_assincrono(
    intervalo_datas(inicio_janela, ultima_data_era5), "📌 JANELA OPERACIONAL (recente)", reserva=0)

# 2) Previsão GFS encadeada
executar_cadeia_gfs(enviados_op)

# 3) Passivo histórico, respeitando a reserva para as próximas execuções
despachar_assincrono(
    intervalo_datas(DATA_INICIO_P1, somar_dias(inicio_janela, -1)),
    f"📚 HISTÓRICO PRINCIPAL ({DATA_INICIO_P1[:4]} até a janela)", reserva=RESERVA_OPERACIONAL)
despachar_assincrono(
    intervalo_datas(DATA_INICIO_P2, DATA_FIM_P2),
    f"🔍 HISTÓRICO SECUNDÁRIO ({DATA_INICIO_P2[:4]}-{DATA_FIM_P2[:4]})", reserva=RESERVA_OPERACIONAL)

# 4) Promove o que já terminou
finalizar_trocas_pendentes(listar_tarefas_ativas())

if SIMULAR:
    print("\n🧪 RESUMO DA SIMULAÇÃO (dias por ação):")
    for motivo, n in sorted(relatorio_sim.items()):
        print(f"   {motivo}: {n:,}")
    print("   Demais dias do acervo: mantidos sem alteração.")
print(f"\n✅ Execução encerrada. Vagas restantes na fila: {capacidade:,}.")
