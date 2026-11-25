# ⛔⛔⛔ NÃO EXECUTAR: SCRIPT ORIGINAL GUARDADO SÓ COMO REGISTRO DO MÉTODO (metodologia da tese) ⛔⛔⛔
# Gerou: projects/clima-492922/assets/SAB_V1 (dias provisórios e previsão de 2026, até a troca pela V1.5) e SAB_V1_TMP. NÃO gravou o histórico 1961–2025: esse é da V1.0 (O0_motor_mestre_V1_0_SAB_V1_historico.py); conferido no Earth Engine em 03/11/2026 (23.741 dias só com versao = definitiva, sem versao_algoritmo)
# Hoje: Histórico 1961–2025 travado (PROTEGER_HISTORICO, DATA_LIMITE_PROTECAO = 2025-12-31).
# Substituído por: 05a/05b_motor_sab_v1_5 (V1.5) para 2026 em diante; o histórico não é mais regravado
# Por que não rodar: ele RECRIARIA o asset acima; o banco, as calibrações e as validações (K8 a K16, 07a/07b,
#   08) foram aprovados com o asset que já existe. Rodar de novo exigiria refazer e validar tudo.
# Recebido do responsável em 03/11/2026 (scripts_originais_recebidos.txt, linhas 1 a 1331). Abaixo da linha ORIGINAL, o texto está sem nenhuma
#   mudança. SHA-256 do trecho original: 7ad5798dec67f5673a26913535d719b2e57d5eef6c7e3948a8b68684276b809b
# A linha raise SystemExit abaixo faz a célula parar antes de qualquer import ou gravação.
raise SystemExit('⛔ Script original guardado só como registro. NÃO EXECUTAR (veja o cabeçalho).')
# ================================================ ORIGINAL ================================================
# =========================================================================================
# TÍTULO: MOTOR MESTRE OPERACIONAL SAB V1.3 - SCRIPT 1 (CONTA CLIMA)
# RESUMO DA FUNÇÃO: Autenticação, processamento e tarefas isoladas para clima-492922
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

VERSAO_ALGORITMO = 'V1.3'
VERSAO_PATCH = 'V1.0-P12'        # dia da V1.0 com umidade do solo e escoamento corrigidos
# True: modo simulação. Lê o acervo e informa o que seria feito, sem exportar,
# apagar, renomear ou criar nenhum asset. Rode assim antes da primeira execução real.
SIMULAR = False
# True (só vale com SIMULAR = True): calcula, sem gravar nada, uma prévia que compara o que o
# painel mostra hoje nos dias provisórios com o que a V1.3 gravaria, e diz se o resultado
# atende aos critérios de aprovação da seção 7.
PREVIA = True
PREVIA_DIAS_DO_MES = (15,)       # dias de cada mês provisório usados na prévia, ex.: (5, 15, 25)
# Algoritmos aceitos nos dias definitivos: esses dias nunca são recalculados por mudança de versão
ALGORITMOS_DEFINITIVOS_VALIDOS = ('V1.0', VERSAO_PATCH, 'V1.2', 'V1.3')
# False (decisão atual): o histórico V1.0 NÃO é regravado; a correção de umidade do solo e
# escoamento desses dias é feita na leitura, pelo Painel SAB (corrigirSoloEscoamentoV10).
# True: aplica o patch no próprio banco (várias execuções, respeitando a fila).
APLICAR_PATCH_SOLO = False
# True: recalcula do zero os dias de versões anteriores (não necessário; mantenha False).
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

# Calibração multiplicativa: fator = alvo / max(modelo, 1e-3) (fórmula da V1.0), limitado
# a FATOR_MAX. Só os pixels cujo fator original passava do teto mudam.
FATOR_MAX = 5.0
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
poligonoBrasil = _gaul_br.geometry()   # polígono exato, igual à V1.0 (garante bordas idênticas)
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

def fator_v10(m_alvo, m_modelo):
    """Fator exatamente como na V1.0 (sem teto)."""
    return expandir_borda(m_alvo).divide(expandir_borda(m_modelo).max(1e-3))

def calib_multiplicativa(img, m_alvo, m_modelo):
    # Onde o fator da V1.0 já era <= FATOR_MAX, min() devolve o mesmo valor: resultado idêntico
    return img.multiply(fator_v10(m_alvo, m_modelo).min(FATOR_MAX))

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
    horas_chuva = [float(h) for h in horas if h % 6 == 0]
    return len(horas), horas_chuva

def processarDia_GFS(data_str, estado_anterior, ref, creation_ms, n_img_esperado, horas_chuva):
    data_atual = ee.Date(data_str)
    t0 = data_atual.millis()
    t1 = data_atual.advance(1, 'day').millis()
    mes = data_str[5:7]

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
            # Mesma variável usada na matriz SICSB_MATRIZ_GFS (temperatura horária instantânea)
            gfs_dia.select('temperature_2m_above_ground').max().rename('maximum_temperature_2m_above_ground'),
            gfs_dia.select('temperature_2m_above_ground').min().rename('minimum_temperature_2m_above_ground'),
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

    pr = calib_multiplicativa(pr_raw, *medias('pr')).max(0).rename('pr_mm')
    tmax_c = calib_aditiva(tmax_raw, *medias('Tmax'))
    tmin_c = calib_aditiva(tmin_raw, *medias('Tmin'))
    # Amplitude mínima: preserva a média e só altera pixels com amplitude < AMPLITUDE_MIN_C
    t_med = tmax_c.add(tmin_c).divide(2)
    meia_amp = tmax_c.subtract(tmin_c).max(AMPLITUDE_MIN_C).divide(2)
    tmax = t_med.add(meia_amp).rename('tmax_C')
    tmin = t_med.subtract(meia_amp).rename('tmin_C')
    rh = calib_aditiva(rh_raw, *medias('RH')).clamp(0, 100).rename('RH')
    u2 = calib_multiplicativa(u2_raw, *medias('u2')).max(0).rename('u2')
    rs = calib_multiplicativa(rs_raw, *medias('Rs')).max(0).rename('rs')

    vpd, _ = vpd_e_ea(tmax, tmin, rh)
    # Penman-Monteith FAO-56: a mesma função usada pela rota provisória (ERA5) a partir da V1.3
    et_potencial = eto_penman_monteith(tmax, tmin, rh, u2, rs, data_str)

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
    p_ia = pr.subtract(s_ret.multiply(0.2)).max(0)
    runoff_sup = p_ia.pow(2).divide(p_ia.add(s_ret)).rename('runoff_sup_mm')
    infiltracao = pr.subtract(runoff_sup).max(0)

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
    v, alg = info['versao'], info['alg']
    if v in VERSOES_GFS:
        return 'precisa_upgrade' if d_str <= ultima_data_era5 else 'gravado'
    if v == 'provisoria_era5':
        if d_str <= ultima_data_brd:
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
            img = processarDia_Definitivo(d) if d <= ultima_data_brd else processarDia_Rota1(d)
        exportar(img, d, usar_tmp=(status != 'ausente'))
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

def executar_cadeia_gfs(enviados_operacionais):
    dias = intervalo_datas(somar_dias(ultima_data_era5, 1), data_fim_processo)
    if not dias:
        return
    print(f"\n⚙ Cadeia GFS sequencial: {dias[0]} a {dias[-1]} ({len(dias)} dias).")
    rodadas, referencia = descobrir_rodadas_gfs()

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
        img = processarDia_GFS(d, estado, ref, rodada, n_img, horas_chuva)
        usar_tmp = info is not None
        exportar(img, d, usar_tmp)
        estado_final = aguardar_tarefa(desc)
        if estado_final != 'COMPLETED':
            raise RuntimeError(f"Falha na cadeia GFS: {desc} terminou com {estado_final}.")
        if usar_tmp:
            promover_tmp(nome)
        print(f"    ✔️ {d}: exportado ({n_img} imagens esperadas, {len(horas_chuva)} blocos de chuva).")

# =========================================================================
# 7. PRÉVIA DA V1.3 (só no modo simulação; nada é gravado)
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
# O que a V1.3 faz com cada banda dos dias provisórios, pelo código (V1.0 x V1.3):
BANDAS_MUDAM = ('et_potencial', 'et_real', 'transpiracao_mm')   # ETo nova; ET real e transpiração
#                 têm teto (ET real <= ETo, transpiração <= ET real), então acompanham a ETo nova
BANDAS_FATOR = ('pr_mm', 'u2', 'rs')   # calibração multiplicativa: só mudam onde o teto FATOR_MAX atua
BANDAS_SOLO = ('soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3',
               'runoff_sup_mm', 'runoff_sub_mm')   # o painel já corrige os dias da V1.0 na leitura
BANDAS_IGUAIS = ('tmax_C', 'tmin_C', 'RH', 'vpd', 'tsolo_C', 'tfolha_C')   # mesma conta, mesmos dados
assert sorted(BANDAS_MUDAM + BANDAS_FATOR + BANDAS_SOLO + BANDAS_IGUAIS) == sorted(BANDAS_PREVIA)
GRUPO_BANDA = {**{b: 'muda na V1.3' for b in BANDAS_MUDAM}, **{b: 'teto do fator' for b in BANDAS_FATOR},
               **{b: 'solo/escoamento' for b in BANDAS_SOLO}, **{b: 'deve ficar igual' for b in BANDAS_IGUAIS}}
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
# Bandas somadas pela prévia, na ordem do redutor: a_ = como o painel mostra hoje, n_ = V1.3,
# d_ = |V1.3 - hoje|, f_ = 1 se o pixel mudou mais que a tolerância. n_pix vale 1 em cada pixel
# válido: a soma dele é a contagem de pixels, e média = soma da banda / soma de n_pix.
NOMES_SOMA = ([f'{p}_{b}' for p in ('a', 'n', 'd', 'f') for b in BANDAS_PREVIA]
              + ['a_deficit', 'n_deficit', 'clim_eto', 'f_solo']
              + [f'{p}_{c}' for p in ('a', 'n') for c in COERENCIA] + ['n_pix'])
# Tentativas de cálculo de cada dia: (n, tileScale) = retângulo do Brasil cortado em n x n partes.
# Se o Earth Engine recusar por memória ou tempo, passa para a tentativa seguinte, com partes
# menores; as somas das partes fecham exatamente com a do retângulo inteiro.
NIVEIS_PREVIA = ((1, 4), (2, 16), (4, 16))

# Critérios de aprovação, definidos antes de rodar. No teste E4 (953 pontos, 2016-2025), a ETo
# atual ficou entre +6,5% e +10,2% acima do BR-DWGD e a de Penman-Monteith entre +1,8% e +3,5%;
# a troca deve, portanto, reduzir a ETo nacional em algo como 4% a 7%. As bandas fora de
# BANDAS_MUDAM não deveriam mudar, a não ser nos poucos pixels em que o teto do fator de
# calibração (FATOR_MAX, da V1.2) atua.
CRIT_ETO_BRASIL = (-12.0, -1.0)      # variação aceitável da ETo nacional (%)
CRIT_ETO_REGIAO = (-20.0, 5.0)       # variação aceitável da ETo de cada região (%)
CRIT_MAX_PIXELS_FATOR = 2.0          # % máxima de pixels alterados em chuva, vento e radiação
CRIT_MAX_PIXELS_SOLO = 1.0           # % máxima de pixels com umidade ou escoamento alterados
CRIT_MAX_PIXELS_IGUAIS = 0.5         # % máxima de pixels alterados nas bandas que devem ficar iguais
CRIT_MAX_INCOERENCIA = 0.01          # % máxima de pixels incoerentes na V1.3 (pelo código, deve ser 0)
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
    """As 16 bandas do dia como estão hoje (a_*) e como a V1.3 gravaria (n_*), a diferença (d_*),
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
    # Uma só máscara para todas as bandas: hoje e V1.3 são comparados exatamente nos mesmos pixels.
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
    """Médias regionais do dia como está hoje (a_*) e como a V1.3 gravaria (n_*). Se o Earth Engine
    recusar por memória ou tempo, refaz o mesmo cálculo em partes menores (NIVEIS_PREVIA)."""
    pilha = _pilha_previa(d, rotulo)
    for k, (n, tile_scale) in enumerate(NIVEIS_PREVIA):
        try:
            resultado = _medias_previa(_somas_regiao(pilha, _retangulos_previa(limites, n), tile_scale))
            if 'Brasil' not in resultado:
                raise RuntimeError("nenhum pixel válido em comum entre o dia gravado e a V1.3")
            return resultado
        except _PedidoGrande as e:
            if k == len(NIVEIS_PREVIA) - 1:
                raise RuntimeError(f"{e} Recusado mesmo em {n * n} partes.") from None
            prox = NIVEIS_PREVIA[k + 1][0] ** 2
            print(f"   {d}: o Earth Engine recusou por memória ou tempo; refazendo em {prox} partes...")

def _resumir_previa(df, motivos_simulacao, dias_previstos=None):
    """Monta as tabelas da prévia e aplica os critérios. Não usa o Earth Engine."""
    ordem = [r for r in ['Brasil', *UFS_REGIAO] if r in set(df['regiao'])]
    br = df[df['regiao'] == 'Brasil'].set_index('data').sort_index()
    por_data = pd.DataFrame({
        'ETo hoje': br['a_et_potencial'], 'ETo V1.3': br['n_et_potencial'],
        'ΔETo %': 100 * (br['n_et_potencial'] / br['a_et_potencial'] - 1),
        'ETo clima do mês': br['clim_eto'],
        'ET real hoje': br['a_et_real'], 'ET real V1.3': br['n_et_real'],
        'Déficit hoje': br['a_deficit'], 'Déficit V1.3': br['n_deficit'],
    }).astype(float).round(2)

    g = df.groupby('regiao')
    soma = lambda col: g[col].sum()
    variacao = lambda a, n: 100 * (soma(n) / soma(a) - 1)
    por_regiao = pd.DataFrame({
        'ΔETo %': variacao('a_et_potencial', 'n_et_potencial'),
        'ΔET real %': variacao('a_et_real', 'n_et_real'),
        'ΔDéficit %': variacao('a_deficit', 'n_deficit'),
        'ETo hoje x clima %': 100 * (soma('a_et_potencial') / soma('clim_eto') - 1),
        'ETo V1.3 x clima %': 100 * (soma('n_et_potencial') / soma('clim_eto') - 1),
        'ΔChuva %': variacao('a_pr_mm', 'n_pr_mm'),
        '% pixels chuva alterada': 100 * g['f_pr_mm'].mean(),
        '% pixels solo alterado': 100 * g['f_solo'].mean(),
    }).reindex(ordem).astype(float).round(2)

    # As 16 bandas no Brasil: média dos dias amostrados, hoje x V1.3
    hoje = pd.Series({b: br[f'a_{b}'].mean() for b in BANDAS_PREVIA}, dtype=float)
    v13 = pd.Series({b: br[f'n_{b}'].mean() for b in BANDAS_PREVIA}, dtype=float)
    n_alterados = pd.Series({b: br[f'f_{b}'].sum() for b in BANDAS_PREVIA}, dtype=float)
    todas = pd.DataFrame({
        'grupo': [GRUPO_BANDA[b] for b in BANDAS_PREVIA],
        'unid.': [UNIDADE_BANDA[b] for b in BANDAS_PREVIA],
        'hoje': hoje, 'V1.3': v13, 'Δ': v13 - hoje,
        'Δ %': 100 * (v13 / hoje.where(hoje.abs() > 1e-9) - 1),
        '% pixels alterados': pd.Series({b: 100 * br[f'f_{b}'].mean() for b in BANDAS_PREVIA}, dtype=float),
        '|Δ| onde mudou': pd.Series({b: br[f'd_{b}'].sum() / n_alterados[b] if n_alterados[b] > 0 else 0.0
                                     for b in BANDAS_PREVIA}, dtype=float),
    }, index=pd.Index(BANDAS_PREVIA, name='banda'))
    num = todas.columns[2:]
    todas[num] = todas[num].astype(float).round(3)

    coerencia = pd.DataFrame({
        'hoje (% pixels)': [100 * br[f'a_{c}'].mean() for c in COERENCIA],
        'V1.3 (% pixels)': [100 * br[f'n_{c}'].mean() for c in COERENCIA],
    }, index=pd.Index(list(COERENCIA.values()), name='verificação')).astype(float).round(3)

    falhas = []
    definitivos = [m for m in motivos_simulacao
                   if m.startswith('recalcular definitiva') or m.startswith('patch')]
    if definitivos:
        falhas.append(f"a execução mexeria em dias definitivos: {definitivos}")
    if 'Brasil' in por_regiao.index:
        b = por_regiao.loc['Brasil']
        if not CRIT_ETO_BRASIL[0] <= b['ΔETo %'] <= CRIT_ETO_BRASIL[1]:
            falhas.append(f"ETo nacional variou {b['ΔETo %']:+.1f}% "
                          f"(esperado entre {CRIT_ETO_BRASIL[0]:+.0f}% e {CRIT_ETO_BRASIL[1]:+.0f}%)")
        for banda in BANDAS_FATOR:
            p = todas.loc[banda, '% pixels alterados']
            if p > CRIT_MAX_PIXELS_FATOR:
                falhas.append(f"{banda} alterada em {p:.2f}% dos pixels (limite {CRIT_MAX_PIXELS_FATOR:.0f}%)")
        if b['% pixels solo alterado'] > CRIT_MAX_PIXELS_SOLO:
            falhas.append(f"umidade ou escoamento alterados em {b['% pixels solo alterado']:.2f}% "
                          f"dos pixels (limite {CRIT_MAX_PIXELS_SOLO:.0f}%)")
        for banda in BANDAS_IGUAIS:
            p = todas.loc[banda, '% pixels alterados']
            if p > CRIT_MAX_PIXELS_IGUAIS:
                falhas.append(f"{banda} mudou em {p:.2f}% dos pixels, mas a conta é a mesma da versão "
                              f"atual (limite {CRIT_MAX_PIXELS_IGUAIS}%)")
        for chave, texto in COERENCIA.items():
            agora, novo = coerencia.loc[texto, 'hoje (% pixels)'], coerencia.loc[texto, 'V1.3 (% pixels)']
            # Tmax < Tmin vem da calibração aditiva, igual nas duas versões: a V1.3 só não pode piorar
            limite = agora + CRIT_MAX_INCOERENCIA if chave == 'tmax_abaixo_tmin' else CRIT_MAX_INCOERENCIA
            if novo > limite:
                falhas.append(f"V1.3 com {texto} em {novo:.3f}% dos pixels (limite {limite:.3f}%)")
    else:
        falhas.append("a prévia não conseguiu calcular a média do Brasil")
    for r in UFS_REGIAO:
        if r not in por_regiao.index:
            falhas.append(f"a prévia não conseguiu calcular a região {r}")
            continue
        v = por_regiao.loc[r, 'ΔETo %']
        if not CRIT_ETO_REGIAO[0] <= v <= CRIT_ETO_REGIAO[1]:
            falhas.append(f"ETo do {r} variou {v:+.1f}% "
                          f"(esperado entre {CRIT_ETO_REGIAO[0]:+.0f}% e {CRIT_ETO_REGIAO[1]:+.0f}%)")
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

def executar_previa():
    meses = sorted({d[:7] for d in intervalo_datas(somar_dias(ultima_data_brd, 1), ultima_data_era5)})
    datas = [f'{m}-{dia:02d}' for m in meses for dia in PREVIA_DIAS_DO_MES]
    datas = [d for d in datas if d <= ultima_data_era5
             and (inventario.get(id_dia(d)) or {}).get('versao') == 'provisoria_era5']
    if not datas:
        print("\n🔎 Prévia: não há dias provisórios gravados para comparar.")
        return
    print(f"\n🔎 PRÉVIA V1.3: {len(datas)} dias provisórios, do jeito que o painel mostra hoje x como a "
          f"V1.3 gravaria. Nada é gravado; conte de 1 a 3 minutos por dia.")
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
        pd.DataFrame(linhas).to_csv('previa_v13.csv', index=False, sep=';', decimal=',')
        br = resultado.get('Brasil')
        resumo = ''
        if br:
            resumo = (f" | ETo Brasil {br['a_et_potencial']:.2f} -> {br['n_et_potencial']:.2f} mm/dia "
                      f"({100 * (br['n_et_potencial'] / br['a_et_potencial'] - 1):+.1f}%)")
        print(f"   {d}: ok em {(time.time() - inicio) / 60:.1f} min{resumo}")
    if not linhas:
        print("   Nenhum dia calculado; a prévia não pode ser avaliada.")
        return

    df = pd.DataFrame(linhas)
    por_data, por_regiao, todas, coerencia, falhas = _resumir_previa(df, list(relatorio_sim), len(datas))
    print(f"\n   Dias calculados: {df['data'].nunique()} de {len(datas)}.")
    pd.set_option('display.width', 220)
    pd.set_option('display.max_columns', 20)
    print("\n=== PRÉVIA 1. BRASIL, DIA A DIA (mm/dia; ETo clima = média do mês no BR-DWGD, 1986-2025) ===")
    print(por_data)
    print("\n=== PRÉVIA 2. MÉDIA DOS DIAS AMOSTRADOS, POR REGIÃO (variações da V1.3 sobre o painel atual) ===")
    print(por_regiao)
    print("A comparação com o clima é só referência: um ano específico pode ser mais quente ou seco.")
    print("\n=== PRÉVIA 3. AS 16 VARIÁVEIS NO BRASIL (média dos dias; Δ = V1.3 - hoje; "
          "|Δ| onde mudou = mudança média nos pixels alterados) ===")
    print(todas)
    print("\n=== PRÉVIA 4. COERÊNCIA FÍSICA (% dos pixels com o problema) ===")
    print(coerencia)
    print("\n=== PRÉVIA 5. CRITÉRIOS DE APROVAÇÃO ===")
    if falhas:
        print("⚠️ NÃO EXECUTE AINDA. Pontos fora do esperado:")
        for f in falhas:
            print(f"   - {f}")
    else:
        print("✅ Todos os critérios atendidos. Para gravar, mude SIMULAR = False e rode de novo.")
    df.to_csv('previa_v13.csv', index=False, sep=';', decimal=',')
    print("💾 Valores completos da prévia em previa_v13.csv (formato do Excel em português).")

# --- Execução ---
relatorio_sim = {}
if SIMULAR:
    print("🧪 MODO SIMULAÇÃO ATIVO: nenhum asset será criado, apagado ou exportado.\n")
# Todos os dias provisórios (desde o dia seguinte ao último BR-DWGD) entram na janela operacional,
# para que um recálculo de versão tenha prioridade sobre o passivo histórico.
inicio_janela = min(somar_dias(data_hoje_str, -JANELA_OPERACIONAL_DIAS),
                    somar_dias(ultima_data_brd, 1), ultima_data_era5)

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
print(f"\n✅ Execução encerrada. Vagas restantes na fila: {capacidade:,}.")
