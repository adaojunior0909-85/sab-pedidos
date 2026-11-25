# =========================================================================================
# AUDITORIA COMPLETA DO SISTEMA SAB (SOMENTE LEITURA) - versão A3 (20/10/2026)
# A3: teste da radiação sem a hora 0 da previsão (que não tem a banda); F3 ignora o mês corrente;
#     F5 localiza as datas exatas em que o GFS passou a ter 384 h e saídas de 3 em 3 h após 240 h
# A2: nomes de banda do teste da convenção do dia sem '+' (o Earth Engine recusava 'era5tx_D+1');
#     opção SECOES_A_RODAR para repetir só algumas seções
#
# OBJETIVO
#   Medir, nos dados reais do Earth Engine, tudo o que até agora foi deduzido só pelo código,
#   antes de decidir qualquer mudança. Nada é criado, apagado, renomeado ou exportado: todas
#   as funções de escrita do Earth Engine são bloqueadas logo depois da conexão.
#
# O QUE É AUDITADO (cada item vira uma linha no resumo final)
#   A  Ambiente: conexão, tarefas na fila, falhas recentes e consumo de EECU do mês
#   B  Assets do projeto: o que existe, tipo, quantidade de imagens
#   C  BR-DWGD: datas, horário, lacunas, tipos de pixel, valores brutos (-32768 e zero),
#      faixas físicas depois da escala, e a CONVENÇÃO DO DIA DE CHUVA (teste com IMERG e ERA5)
#   D  SAB_V1: inventário 1961-hoje, versões por ano, coleção temporária, fidelidade dos dias
#      definitivos ao BR-DWGD, coerência física, 2026 x climatologia, e o efeito da reamostragem
#      bilinear na umidade do solo (antecipa o critério de ±2% da etapa 5a)
#   E  Matrizes: SICSB_1986_2025, SICSB_SOLO_2015_2025, SICSB_MATRIZ_GFS (fatores, cortes no
#      teto de 5, cobertura) e resolução efetiva da matriz GFS V1
#   F  GFS: time_start x creation_time, horas de previsão por época (datas usadas no script 03),
#      disponibilidade das rodadas 00Z mês a mês e natureza da radiação (instantânea ou média)
#   G  ERA5-Land: última data e alinhamento da grade com o SAB
#   H  OISST e RONI: últimos dias, status, retângulos geodésicos x planos, asset RONI antigo x CPC
#   I  Baselines: imagens e versões nas 4 coleções
#
# COMO RODAR NO COLAB
#   1. Cole este arquivo inteiro numa célula e rode (Ctrl+Enter). Tempo típico: cerca de 10 minutos.
#   2. Não precisa editar nada. Para uma rodada mais curta, mude RAPIDO para True (seção 0).
#   3. No fim, o Colab baixa auditoria_SAB_<data>.zip com o log completo, o resumo e as tabelas.
#      Se o download não abrir, use o painel Arquivos (ícone de pasta, à esquerda).
#   4. Envie o .zip (ou o arquivo LOG_COMPLETO.txt) para a análise.
# =========================================================================================

import calendar
import io
import json
import math
import os
import shutil
import time
import traceback
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

# =========================================================================
# 0. CONFIGURAÇÃO (não precisa mudar nada)
# =========================================================================
PROJETO = 'clima-492922'
RAPIDO = False                     # True: amostras menores (cerca de 1/3 do tempo)
# Seções a rodar. Vazio = todas. Exemplo para repetir só o que faltou: SECOES_A_RODAR = ['C', 'E', 'F', 'G', 'H', 'I']
# (a seção D é necessária para D-dependentes; C, E, F, G, H e I são independentes)
SECOES_A_RODAR = []

RAIZ = f'projects/{PROJETO}/assets'
SAB = f'{RAIZ}/SAB_V1'
SAB_TMP = f'{RAIZ}/SAB_V1_TMP'
CLIMA = f'{RAIZ}/SICSB_1986_2025'
SOLO = f'{RAIZ}/SICSB_SOLO_2015_2025'
GFS_V1 = f'{RAIZ}/SICSB_MATRIZ_GFS'
GFS_V2 = f'{RAIZ}/SICSB_MATRIZ_GFS_V2'
RONI_ANTIGO = f'{RAIZ}/RONI_Calibrado_Sazonal_1950_1980'
RONI_NOVO = f'{RAIZ}/RONI_CPC_v6'
BASELINES = f'{RAIZ}/Baselines'
BR_DWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
GFS = 'NOAA/GFS0P25'
OISST = 'NOAA/CDR/OISST/V2_1'
IMERG_OPCOES = ['NASA/GPM_L3/IMERG_V07', 'NASA/GPM_L3/IMERG_V06']
URL_RONI_CPC = 'https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt'

CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
DIAS_HISTORICO = 23741             # 01/01/1961 a 31/12/2025
FATOR_MAX = 5.0
UMIDADE_MAX = 0.9

# Escala e offset do BR-DWGD (metadados do asset; os mesmos do motor)
ESCALA_BR = {'pr': (0.00686666, 225.0), 'Tmax': (0.00106815, 15.0), 'Tmin': (0.00106815, 15.0),
             'RH': (0.39370079, -0.393701), 'u2': (0.05905512, -0.059055),
             'Rs': (0.15708661, -0.057087), 'ET': (0.05118110, -0.0511811)}
BR_PARA_SAB = {'pr': 'pr_mm', 'Tmax': 'tmax_C', 'Tmin': 'tmin_C', 'RH': 'RH', 'u2': 'u2',
               'Rs': 'rs', 'ET': 'et_potencial'}

BANDAS_SAB = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2',
              'tsolo_C', 'tfolha_C', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm',
              'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
NOMES_ANTIGOS = ['precipitation_mm', 'temp_max_C', 'temp_min_C', 'relative_humidity_pct',
                 'et_potential_mm', 'et_actual_mm', 'vpd_kpa', 'solar_radiation_mj_m2',
                 'wind_speed_m_s', 'soil_temperature_C', 'skin_temperature_C', 'transpiration_mm',
                 'surface_runoff_mm', 'subsurface_runoff_mm', 'soil_moisture_0_5cm_m3_m3',
                 'soil_moisture_0_100cm_m3_m3']

PONTOS = [
    ('Pato Branco-PR', -26.23, -52.67), ('Curitiba-PR', -25.43, -49.27), ('Londrina-PR', -23.31, -51.16),
    ('Porto Alegre-RS', -30.03, -51.23), ('Passo Fundo-RS', -28.26, -52.41), ('Chapeco-SC', -27.10, -52.62),
    ('Campo Grande-MS', -20.47, -54.62), ('Rio Verde-GO', -17.80, -50.93), ('Sorriso-MT', -12.55, -55.71),
    ('Brasilia-DF', -15.79, -47.88), ('Uberaba-MG', -19.75, -47.93), ('Barreiras-BA', -12.15, -45.00),
    ('Petrolina-PE', -9.39, -40.50), ('Quixada-CE', -4.97, -39.02), ('Paragominas-PA', -3.00, -47.35),
    ('Manaus-AM', -3.10, -60.02), ('Porto Velho-RO', -8.76, -63.90), ('Balsas-MA', -7.53, -46.04),
]

# Amostras de dias
PASSO_ANOS = 8 if RAPIDO else 4
DIAS_AMOSTRA_HIST = sorted({f'{a}-{m:02d}-15' for a in range(1961, 2026, PASSO_ANOS) for m in (1, 7)}
                           | {'1961-01-01', '1990-12-31', '2025-12-31'})
PERIODOS_CHUVA = ([('2019-01-01', '2019-03-31')] if RAPIDO else
                  [('2019-01-01', '2019-03-31'), ('2019-10-01', '2019-12-31')])
MAX_PONTOS_CHUVA = 30 if RAPIDO else 60
MESES_SOLO_2025 = (1, 7) if RAPIDO else (1, 3, 5, 7, 9, 11)

# =========================================================================
# 1. LOG, ACHADOS E UTILITÁRIOS
# =========================================================================
AGORA = datetime.now(timezone(timedelta(hours=-3)))
PASTA = f'/content/auditoria_SAB_{AGORA:%Y%m%d_%H%M}' if os.path.isdir('/content') else \
        f'auditoria_SAB_{AGORA:%Y%m%d_%H%M}'
os.makedirs(PASTA, exist_ok=True)
ARQ_LOG = os.path.join(PASTA, 'LOG_COMPLETO.txt')
ACHADOS = []
ORDEM_STATUS = {'ERRO': 0, 'ATENÇÃO': 1, 'NÃO EXECUTADO': 2, 'INFO': 3, 'OK': 4}


def log(*partes):
    texto = ' '.join(str(p) for p in partes)
    print(texto)
    with open(ARQ_LOG, 'a', encoding='utf-8') as f:
        f.write(texto + '\n')


def log_tabela(df, titulo=None, max_linhas=200):
    if titulo:
        log(f'\n   {titulo}')
    if df is None or len(df) == 0:
        log('   (vazio)')
        return
    with pd.option_context('display.width', 250, 'display.max_columns', 60, 'display.max_colwidth', 60):
        texto = df.head(max_linhas).to_string()
    for linha in texto.splitlines():
        log('   ' + linha)
    if len(df) > max_linhas:
        log(f'   ... ({len(df) - max_linhas} linhas a mais no CSV)')


def salvar_csv(df, nome):
    if df is not None and len(df):
        df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=True, encoding='utf-8-sig')


def achado(codigo, status, titulo, resultado, significado='', acao=''):
    ACHADOS.append({'codigo': codigo, 'status': status, 'titulo': titulo, 'resultado': resultado,
                    'significado': significado, 'acao_sugerida': acao})
    simbolo = {'OK': '✅', 'ATENÇÃO': '⚠️', 'ERRO': '❌', 'INFO': 'ℹ️', 'NÃO EXECUTADO': '⏭️'}[status]
    log(f'{simbolo} [{codigo}] {titulo}: {resultado}')
    if significado:
        log(f'      significado: {significado}')
    if acao:
        log(f'      ação sugerida: {acao}')


def ms_para_txt(ms, horas=True):
    if ms is None:
        return 'N/A'
    d = datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc)
    return d.strftime('%Y-%m-%d %H:%M UTC' if horas else '%Y-%m-%d')


def data_ms(d):
    return int(datetime.strptime(d, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp() * 1000)


def centro_pixel(lat, lon):
    dx, x0 = TRANSFORM[0], TRANSFORM[2]
    dy, y0 = -TRANSFORM[4], TRANSFORM[5]
    return (y0 - (math.floor((y0 - lat) / dy) + 0.5) * dy,
            x0 + (math.floor((lon - x0) / dx) + 0.5) * dx)


PONTOS_CP = [(n, *centro_pixel(la, lo)) for n, la, lo in PONTOS]

TRANSITORIOS = ('Too many concurrent', 'Internal error', 'Service Unavailable', '503', '429',
                'deadline', 'Deadline', 'Connection', 'temporarily')


def gi(obj, rotulo='', tentativas=4):
    """getInfo com novas tentativas para erros transitórios do servidor."""
    for t in range(tentativas):
        try:
            return obj.getInfo()
        except Exception as e:
            msg = str(e)
            if t < tentativas - 1 and any(k in msg for k in TRANSITORIOS):
                espera = 10 * (t + 1)
                log(f'   ↻ {rotulo}: erro transitório ({msg[:80]}); nova tentativa em {espera} s')
                time.sleep(espera)
                continue
            raise


# =========================================================================
# 2. CONEXÃO E TRAVA DE SOMENTE LEITURA
# =========================================================================
import ee

log('=' * 100)
log(f'AUDITORIA COMPLETA DO SISTEMA SAB (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT) | '
    f'modo {"RÁPIDO" if RAPIDO else "COMPLETO"}')
log(f'Saídas em: {PASTA}')
log('=' * 100)
try:
    ee.Initialize(project=PROJETO)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJETO)
log(f'Earth Engine conectado ao projeto {PROJETO} (biblioteca ee {ee.__version__})')


def _bloqueado(*a, **k):
    raise RuntimeError('AUDITORIA SOMENTE LEITURA: tentativa de escrita bloqueada')


for _nome in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset',
              'setAssetAcl', 'setAssetProperties', 'createFolder', 'startProcessing',
              'exportImage', 'exportTable', 'exportVideo', 'exportMap', 'startIngestion',
              'startTableIngestion', 'cancelTask', 'cancelOperation'):
    if hasattr(ee.data, _nome):
        setattr(ee.data, _nome, _bloqueado)
ee.batch.Task.start = _bloqueado
log('🔒 Trava de somente leitura ativa: criar, apagar, renomear, exportar e cancelar estão bloqueados.\n')

GAUL_BR = ee.FeatureCollection('FAO/GAUL/2015/level0').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
LIMITES = GAUL_BR.geometry().bounds()
MASCARA_BR = ee.Image.constant(1).clipToCollection(GAUL_BR).mask()


def rr(img, reducer, rotulo, geom=None, crs=CRS, transform=TRANSFORM, escala=None):
    """reduceRegion na grade do SAB (ou na escala dada), com novas tentativas."""
    args = dict(reducer=reducer, geometry=geom or LIMITES, maxPixels=1e10, tileScale=4)
    if escala:
        args.update(scale=escala)
    else:
        args.update(crs=crs, crsTransform=transform)
    return gi(img.reduceRegion(**args), rotulo)


def regiao_pontos(col, bandas, pontos, rotulo, crs=CRS, transform=TRANSFORM, escala=None):
    """getRegion nos pontos; devolve DataFrame com nome do ponto, data e bandas."""
    geom = ee.Geometry.MultiPoint([[lo, la] for _, la, lo in pontos])
    if escala:
        linhas = gi(col.select(bandas).getRegion(geom, escala), rotulo)
    else:
        linhas = gi(col.select(bandas).getRegion(geom, None, crs, transform), rotulo)
    df = pd.DataFrame(linhas[1:], columns=linhas[0])
    if not len(df):
        return df
    la = df['latitude'].astype(float).to_numpy()
    lo = df['longitude'].astype(float).to_numpy()
    dist = np.stack([np.hypot(la - p[1], lo - p[2]) for p in pontos])
    df['ponto'] = [pontos[i][0] for i in dist.argmin(axis=0)]
    df['data'] = pd.to_datetime(df['time'].astype('float64'), unit='ms', utc=True).dt.tz_localize(None)
    for b in bandas:
        df[b] = pd.to_numeric(df[b], errors='coerce')
    return df[['ponto', 'data'] + bandas]


def padronizar_sab(img):
    return ee.Image(ee.Algorithms.If(img.bandNames().contains('precipitation_mm'),
                                     img.select(NOMES_ANTIGOS, BANDAS_SAB), img.select(BANDAS_SAB)))


def br_fisico(img):
    """BR-DWGD em unidades físicas, exatamente como o motor grava (UR limitada a 0-100, chuva >= 0)."""
    b = {k: img.select(k).multiply(e).add(o) for k, (e, o) in ESCALA_BR.items()}
    b['pr'] = b['pr'].max(0)
    b['RH'] = b['RH'].clamp(0, 100)
    return ee.Image(ee.Image.cat([b[k].rename(BR_PARA_SAB[k]) for k in ESCALA_BR])
                    .copyProperties(img, ['system:time_start']))


def listar_assets(pai):
    nomes, token = [], None
    while True:
        params = {'parent': pai, 'pageSize': 1000}
        if token:
            params['pageToken'] = token
        resp = ee.data.listAssets(params)
        for a in resp.get('assets', []):
            nomes.append({'nome': (a.get('id') or a.get('name')).split('/')[-1],
                          'caminho': a.get('id') or a.get('name'), 'tipo': a.get('type')})
        token = resp.get('nextPageToken')
        if not token:
            return nomes


def existe(caminho):
    try:
        ee.data.getAsset(caminho)
        return True
    except Exception:
        return False


SECOES = []


def secao(codigo, titulo):
    def deco(fn):
        SECOES.append((codigo, titulo, fn))
        return fn
    return deco


CONTEXTO = {}   # resultados que uma seção passa para outra


# =========================================================================
# A. AMBIENTE E FILA DE TAREFAS
# =========================================================================
@secao('A', 'Ambiente e fila de tarefas')
def secao_a():
    tarefas = ee.data.getTaskList()
    ativas = [t for t in tarefas if t.get('state') in ('READY', 'RUNNING', 'SUBMITTED', 'PENDING')]
    inicio_mes = datetime(AGORA.year, AGORA.month, 1, tzinfo=timezone.utc).timestamp() * 1000
    recentes = [t for t in tarefas if (t.get('creation_timestamp_ms') or 0) >= inicio_mes - 30 * 864e5]
    falhas = [t for t in recentes if t.get('state') == 'FAILED']
    eecu_mes = sum((t.get('batch_eecu_usage_seconds') or 0) for t in tarefas
                   if (t.get('start_timestamp_ms') or 0) >= inicio_mes) / 3600
    por_prefixo = pd.Series([t.get('description', '')[:6] for t in ativas]).value_counts()
    log(f'   tarefas ativas: {len(ativas)} | por prefixo: {por_prefixo.to_dict()}')
    achado('A1', 'INFO', 'Tarefas ativas na fila', f'{len(ativas)} tarefa(s)',
           'Motor, normais e matrizes dividem a mesma fila de 3.000 tarefas do projeto.')
    if falhas:
        tab = pd.DataFrame([{'descricao': t.get('description'), 'criada': ms_para_txt(t.get('creation_timestamp_ms')),
                             'erro': (t.get('error_message') or '')[:120]} for t in falhas[:50]])
        log_tabela(tab, 'Falhas nos últimos ~30 dias (até 50):')
        salvar_csv(tab, 'A_tarefas_falhas.csv')
        erros_cota = sum('quota' in (t.get('error_message') or '').lower() for t in falhas)
        achado('A2', 'ATENÇÃO', 'Tarefas que falharam nos últimos ~30 dias',
               f'{len(falhas)} falha(s), {erros_cota} por cota', 'Ver A_tarefas_falhas.csv.',
               'Ler as mensagens de erro antes das próximas exportações.')
    else:
        achado('A2', 'OK', 'Tarefas que falharam nos últimos ~30 dias', 'nenhuma')
    achado('A3', 'INFO', 'Consumo de EECU das tarefas em lote neste mês (soma das tarefas listadas)',
           f'{eecu_mes:.1f} EECU-horas',
           'Só conta tarefas em lote ainda listadas; o uso interativo (painel, Colab) não entra. '
           'Cota mensal não comercial: Community 150, Contributor 1.000 EECU-horas.')


# =========================================================================
# B. ASSETS DO PROJETO
# =========================================================================
@secao('B', 'Assets do projeto')
def secao_b():
    raiz = listar_assets(RAIZ)
    linhas = []
    for a in raiz:
        n = None
        if a['tipo'] == 'IMAGE_COLLECTION':
            n = gi(ee.ImageCollection(a['caminho']).size(), f"tamanho {a['nome']}")
        elif a['tipo'] == 'TABLE':
            n = gi(ee.FeatureCollection(a['caminho']).size(), f"tamanho {a['nome']}")
        elif a['tipo'] == 'FOLDER':
            n = len(listar_assets(a['caminho']))
        linhas.append({'asset': a['nome'], 'tipo': a['tipo'], 'itens': n})
    tab = pd.DataFrame(linhas).set_index('asset')
    log_tabela(tab, 'Assets na raiz do projeto:')
    salvar_csv(tab, 'B_assets.csv')
    esperados = ['SAB_V1', 'SAB_V1_TMP', 'SICSB_1986_2025', 'SICSB_SOLO_2015_2025', 'SICSB_MATRIZ_GFS',
                 'RONI_Calibrado_Sazonal_1950_1980', 'Baselines']
    faltam = [e for e in esperados if e not in tab.index]
    achado('B1', 'ERRO' if faltam else 'OK', 'Assets esperados presentes',
           f'faltam {faltam}' if faltam else 'todos os 7 presentes',
           'Sem eles o motor e o painel não funcionam.' if faltam else '')
    novos = [n for n in ('RONI_CPC_v6', 'SICSB_MATRIZ_GFS_V2') if n in tab.index]
    achado('B2', 'INFO', 'Assets novos do pacote de correções', f'já existem: {novos or "nenhum"}',
           'Antes das etapas 2 e 3 é esperado que não existam.')
    for nome, esperado in (('SICSB_1986_2025', 12), ('SICSB_SOLO_2015_2025', 12), ('SICSB_MATRIZ_GFS', 12)):
        if nome in tab.index:
            n = tab.loc[nome, 'itens']
            achado(f'B3-{nome}', 'OK' if n == esperado else 'ATENÇÃO', f'{nome}: número de matrizes',
                   f'{n} (esperado {esperado})')


# =========================================================================
# C. BR-DWGD
# =========================================================================
@secao('C', 'BR-DWGD: metadados, datas, valores brutos e convenção do dia')
def secao_c():
    col = ee.ImageCollection(BR_DWGD)
    meta = ee.data.getAsset(BR_DWGD)
    log(f'   asset: tipo {meta.get("type")} | atualizado {meta.get("updateTime")} | '
        f'propriedades: {list((meta.get("properties") or {}).keys())[:20]}')
    tempos = gi(col.aggregate_array('system:time_start'), 'datas BR-DWGD')
    datas = pd.to_datetime(pd.Series(tempos, dtype='float64'), unit='ms', utc=True)
    horas = datas.dt.strftime('%H:%M').value_counts()
    dias = datas.dt.tz_localize(None).dt.normalize()
    esperado = pd.date_range(dias.min(), dias.max())
    faltando = sorted(set(esperado) - set(dias))
    duplicados = sorted(set(dias[dias.duplicated()]))
    log(f'   imagens: {len(tempos)} | de {dias.min():%Y-%m-%d} a {dias.max():%Y-%m-%d} | horários: {horas.to_dict()}')
    ok_n = len(tempos) == DIAS_HISTORICO and not faltando and not duplicados
    achado('C1', 'OK' if ok_n else 'ERRO', 'BR-DWGD: um dia por imagem, sem lacunas',
           f'{len(tempos)} imagens, {len(faltando)} dias faltando, {len(duplicados)} duplicados '
           f'(primeiros faltando: {[d.strftime("%Y-%m-%d") for d in faltando[:5]]})')
    so_meia_noite = list(horas.index) == ['00:00']
    achado('C2', 'OK' if so_meia_noite else 'ERRO', 'BR-DWGD: horário de system:time_start',
           f'{horas.to_dict()}',
           'A matriz GFS V2 (script 03) pareia cada dia com a rodada GFS criada à meia-noite UTC '
           'desse dia; com outro horário nenhuma rodada é encontrada.',
           '' if so_meia_noite else 'Não rode o script 03 antes de ajustar o pareamento.')

    primeira = ee.Image(col.first())
    tipos = gi(primeira.bandTypes(), 'tipos BR-DWGD')
    tab_tipos = pd.DataFrame({b: {'precisao': v.get('precision'), 'min': v.get('min'), 'max': v.get('max')}
                              for b, v in tipos.items()}).T
    log_tabela(tab_tipos, 'Tipos de pixel das bandas (valor bruto):')
    CONTEXTO['tipos_br'] = tipos

    # Valores brutos e físicos nos dias de amostra
    linhas = []
    for d in DIAS_AMOSTRA_HIST:
        img = ee.Image(col.filterDate(d, ee.Date(d).advance(1, 'day')).first())
        bruto = img.select(list(ESCALA_BR))
        ind = ee.Image.cat([
            bruto.select(['pr', 'Tmax', 'Tmin']).eq(-32768).rename(['s32768_pr', 's32768_Tmax', 's32768_Tmin']),
            bruto.select(['RH', 'u2', 'Rs', 'ET']).eq(0).rename(['zero_RH', 'zero_u2', 'zero_Rs', 'zero_ET']),
        ])
        fis = ee.Image.cat([bruto.select(k).multiply(e).add(o).rename(f'f_{k}') for k, (e, o) in ESCALA_BR.items()])
        red = ee.Reducer.minMax().combine(ee.Reducer.count(), sharedInputs=True)
        s1 = rr(ee.Image.cat([bruto, fis]), red, f'BR {d}', transform=TRANSFORM)
        s2 = rr(ind, ee.Reducer.sum(), f'BR indicadores {d}', transform=TRANSFORM)
        lin = {'dia': d}
        lin.update({k: s1.get(k) for k in s1})
        lin.update({k: s2.get(k) for k in s2})
        linhas.append(lin)
        log(f'   {d}: pr bruto {s1.get("pr_min")}..{s1.get("pr_max")} | Tmax bruto {s1.get("Tmax_min")}..'
            f'{s1.get("Tmax_max")} | RH bruto {s1.get("RH_min")}..{s1.get("RH_max")} | pixels pr {s1.get("pr_count")} '
            f'| -32768: {s2.get("s32768_pr")}/{s2.get("s32768_Tmax")}/{s2.get("s32768_Tmin")} | zeros RH/u2/Rs/ET: '
            f'{s2.get("zero_RH")}/{s2.get("zero_u2")}/{s2.get("zero_Rs")}/{s2.get("zero_ET")}')
    tab = pd.DataFrame(linhas).set_index('dia')
    salvar_csv(tab, 'C_br_dwgd_valores_por_dia.csv')
    sentinela = int(tab[['s32768_pr', 's32768_Tmax', 's32768_Tmin']].fillna(0).sum().sum())
    achado('C3', 'OK' if sentinela == 0 else 'ERRO', 'BR-DWGD: valor de ausência -32768 sem máscara',
           f'{sentinela} pixel(s) em {len(tab)} dias de amostra',
           'Se existir, a rota definitiva do motor grava Tmax/Tmin = -20 °C e chuva = 0 nesses pixels.',
           '' if sentinela == 0 else 'Mascarar -32768 no motor e verificar o histórico gravado.')
    zeros = tab[['zero_RH', 'zero_u2', 'zero_Rs', 'zero_ET']].fillna(0).sum()
    achado('C4', 'OK' if zeros.sum() == 0 else 'ATENÇÃO', 'BR-DWGD: valor bruto 0 nas bandas de 8 bits',
           f'{zeros.astype(int).to_dict()}',
           'Com o offset, bruto 0 vira valor levemente negativo (ETo -0,051 mm, vento -0,059 m/s, '
           'radiação -0,057 MJ/m²); o motor não limita ETo, vento e radiação a zero.',
           '' if zeros.sum() == 0 else 'Verificar se bruto 0 é ausência ou zero real e limitar a 0.')
    faixas = {'f_pr': (0, 450.01), 'f_Tmax': (-20.01, 50.01), 'f_Tmin': (-20.01, 50.01), 'f_RH': (-0.5, 100.01),
              'f_u2': (-0.1, 15.01), 'f_Rs': (-0.1, 40.01), 'f_ET': (-0.1, 13.01)}
    fora = {k: (tab[f'{k}_min'].min(), tab[f'{k}_max'].max()) for k in faixas
            if tab[f'{k}_min'].min() < faixas[k][0] or tab[f'{k}_max'].max() > faixas[k][1]}
    achado('C5', 'OK' if not fora else 'ERRO', 'BR-DWGD: valores físicos dentro da faixa da codificação',
           'todos dentro' if not fora else f'fora: {fora}',
           'Confirma escala e offset: UR até 100,000% só com o offset documentado no asset.')
    rh_max = tab['f_RH_max'].max()
    achado('C6', 'OK' if rh_max <= 100.01 else 'ERRO', 'BR-DWGD: UR máxima com o offset atual',
           f'{rh_max:.3f}%', 'Sem o offset, a UR máxima seria 100,394%.')
    teste_convencao_dia()


def teste_convencao_dia():
    """Convenção do dia de chuva: compara a chuva do BR-DWGD do dia D com três janelas do IMERG
    (00-24 UTC de D; 12 UTC de D-1 a 12 UTC de D; 12 UTC de D a 12 UTC de D+1) e com o ERA5-Land
    nos dias D-1, D e D+1. A janela com maior correlação indica a convenção."""
    imerg_id = None
    for cand in IMERG_OPCOES:
        try:
            n = gi(ee.ImageCollection(cand).filterDate('2019-01-01', '2019-01-02').size(), cand)
            if n:
                imerg_id = cand
                break
        except Exception:
            continue
    if not imerg_id:
        achado('C7', 'NÃO EXECUTADO', 'Convenção do dia de chuva (IMERG)', 'nenhuma coleção IMERG acessível')
    else:
        log(f'   teste da convenção do dia com {imerg_id}')
    br = ee.ImageCollection(BR_DWGD)
    # Pontos: grade de 3° sobre o Brasil, só onde o BR-DWGD tem dado
    cand = [(f'g{la:+.0f}{lo:+.0f}', *centro_pixel(la, lo)) for la in np.arange(-32, 5, 3)
            for lo in np.arange(-72, -34, 3)]
    teste = regiao_pontos(br.filterDate('2019-01-15', '2019-01-16').map(br_fisico), ['pr_mm'], cand, 'pontos grade')
    validos = set(teste.dropna(subset=['pr_mm'])['ponto'])
    pontos = [p for p in cand if p[0] in validos]
    if len(pontos) > MAX_PONTOS_CHUVA:          # distribuição uniforme no país, não só os primeiros
        pontos = [pontos[i] for i in np.linspace(0, len(pontos) - 1, MAX_PONTOS_CHUVA).round().astype(int)]
    log(f'   pontos com BR-DWGD válido: {len(pontos)}')

    def janelas(d):
        d = ee.Date(d)
        bandas = []
        if imerg_id:
            banda_imerg = 'precipitation' if imerg_id.endswith('V07') else 'precipitationCal'
            im = ee.ImageCollection(imerg_id).select(banda_imerg)
            def soma(a, b):
                return im.filterDate(a, b).sum().multiply(0.5)
            bandas += [soma(d, d.advance(1, 'day')).rename('imerg_00_24'),
                       soma(d.advance(-12, 'hour'), d.advance(12, 'hour')).rename('imerg_12ant_12'),
                       soma(d.advance(12, 'hour'), d.advance(36, 'hour')).rename('imerg_12_12seg')]
        era = ee.ImageCollection(ERA5)
        for k, nome in ((-1, 'era5_Dm1'), (0, 'era5_D0'), (1, 'era5_Dp1')):
            dk = d.advance(k, 'day')
            bandas.append(ee.Image(era.filterDate(dk, dk.advance(1, 'day')).first())
                          .select('total_precipitation_sum').multiply(1000).rename(nome))
        for k, nome in ((-1, 'era5tx_Dm1'), (0, 'era5tx_D0'), (1, 'era5tx_Dp1')):
            dk = d.advance(k, 'day')
            bandas.append(ee.Image(era.filterDate(dk, dk.advance(1, 'day')).first())
                          .select('temperature_2m_max').subtract(273.15).rename(nome))
        return ee.Image.cat(bandas).set('system:time_start', d.millis())

    nomes_ref = (['imerg_00_24', 'imerg_12ant_12', 'imerg_12_12seg'] if imerg_id else []) + \
                ['era5_Dm1', 'era5_D0', 'era5_Dp1', 'era5tx_Dm1', 'era5tx_D0', 'era5tx_Dp1']
    partes = []
    for ini, fim in PERIODOS_CHUVA:
        blocos = pd.date_range(ini, fim, freq='15D')
        for b0 in blocos:
            b1 = min(b0 + timedelta(days=15), pd.Timestamp(fim) + timedelta(days=1))
            dias_b = [x.strftime('%Y-%m-%d') for x in pd.date_range(b0, b1 - timedelta(days=1))]
            ref = ee.ImageCollection.fromImages([janelas(x) for x in dias_b])
            df_ref = regiao_pontos(ref, nomes_ref, pontos, f'referências {dias_b[0]}', escala=11132)
            df_br = regiao_pontos(br.filterDate(dias_b[0], b1.strftime('%Y-%m-%d')).map(br_fisico),
                                  ['pr_mm', 'tmax_C'], pontos, f'BR {dias_b[0]}')
            df_ref['dia'] = df_ref['data'].dt.normalize()
            df_br['dia'] = df_br['data'].dt.normalize()
            partes.append(df_br.drop(columns='data').merge(df_ref.drop(columns='data'), on=['ponto', 'dia']))
            log(f'   bloco {dias_b[0]} a {dias_b[-1]}: {len(partes[-1])} pares')
    dados = pd.concat(partes, ignore_index=True).dropna()
    salvar_csv(dados, 'C_convencao_dia_pares.csv')
    linhas = []
    for ref in nomes_ref:
        alvo = 'tmax_C' if 'tx' in ref else 'pr_mm'
        x, y = dados[alvo], dados[ref]
        lin = {'referencia': ref, 'variavel_BR': alvo, 'pares': len(x),
               'pearson': x.corr(y), 'spearman': x.corr(y, method='spearman')}
        if alvo == 'pr_mm':
            lin['acerto_dia_chuvoso'] = ((x >= 1) == (y >= 1)).mean()
        linhas.append(lin)
    tab = pd.DataFrame(linhas).set_index('referencia')
    log_tabela(tab.round(3), 'Correlação BR-DWGD do dia D x referências:')
    salvar_csv(tab, 'C_convencao_dia_resumo.csv')
    era_pr = tab.loc[['era5_Dm1', 'era5_D0', 'era5_Dp1'], 'spearman']
    era_tx = tab.loc[['era5tx_Dm1', 'era5tx_D0', 'era5tx_Dp1'], 'spearman']
    achado('C8', 'INFO' if era_pr.idxmax() == 'era5_D0' else 'ATENÇÃO',
           'Convenção do dia (ERA5-Land, defasagem de -1 a +1 dia)',
           f'chuva: melhor {era_pr.idxmax()} ({era_pr.round(3).to_dict()}); '
           f'Tmax: melhor {era_tx.idxmax()} ({era_tx.round(3).to_dict()})',
           'Dm1 = ERA5 do dia anterior, D0 = mesmo dia, Dp1 = dia seguinte. Se a melhor correlação da chuva for '
           'com Dm1, a chuva do BR-DWGD do dia D caiu, em boa parte, no dia civil anterior (leitura da manhã).')
    if imerg_id:
        im = tab.loc[['imerg_00_24', 'imerg_12ant_12', 'imerg_12_12seg']]
        melhor = im['spearman'].idxmax()
        margem = im['spearman'].max() - im['spearman'].drop(melhor).max()
        # voto por ponto
        votos = {}
        for p, g in dados.groupby('ponto'):
            c = {r: g['pr_mm'].corr(g[r], method='spearman') for r in im.index}
            c = {r: v for r, v in c.items() if pd.notna(v)}
            if c:
                votos[max(c, key=c.get)] = votos.get(max(c, key=c.get), 0) + 1
        texto = {'imerg_00_24': 'dia civil 00-24 UTC (mesma convenção do ERA5 e do GFS)',
                 'imerg_12ant_12': 'chuva das 12 UTC de D-1 às 12 UTC de D (leitura da manhã de D, '
                                   'atribuída a D)',
                 'imerg_12_12seg': 'chuva das 12 UTC de D às 12 UTC de D+1 (leitura da manhã de D+1, '
                                   'atribuída a D)'}[melhor]
        conclusivo = margem >= 0.05 and votos.get(melhor, 0) >= 0.6 * sum(votos.values())
        CONTEXTO['convencao_dia'] = melhor
        achado('C7', 'INFO' if melhor == 'imerg_00_24' else 'ATENÇÃO',
               'Convenção do dia de chuva do BR-DWGD (IMERG)',
               f'melhor janela: {melhor} (Spearman {im.loc[melhor, "spearman"]:.3f}, margem {margem:.3f}; '
               f'votos por ponto {votos}); {"conclusivo" if conclusivo else "NÃO conclusivo"}',
               f'O dia D do BR-DWGD corresponde a: {texto}.',
               '' if melhor == 'imerg_00_24' else
               'Os pareamentos diários com ERA5 e GFS (00-24 UTC) ficam deslocados meio dia; médias mensais '
               'quase não mudam. Avaliar ajuste na matriz GFS e na transição 2025/2026.')


# =========================================================================
# D. SAB_V1
# =========================================================================
@secao('D', 'SAB_V1: inventário, fidelidade, coerência e umidade do solo')
def secao_d():
    col = ee.ImageCollection(SAB)

    def props(img):
        d = img.toDictionary()
        return ee.Feature(None, {'t': img.get('system:time_start'), 'id': img.get('system:index'),
                                 'versao': d.get('versao', 'definitiva'), 'alg': d.get('versao_algoritmo', 'V1.0'),
                                 'antigo': img.bandNames().contains('precipitation_mm'),
                                 'nb': img.bandNames().size()})

    partes = []
    hoje = datetime.now(timezone.utc)
    for a0 in list(range(1961, hoje.year + 1, 5)):
        a1 = a0 + 5
        sub = col.filterDate(f'{a0}-01-01', f'{a1}-01-01')
        if a1 > hoje.year:
            sub = col.filterDate(f'{a0}-01-01', (hoje + timedelta(days=40)).strftime('%Y-%m-%d'))
        res = gi(sub.map(props).reduceColumns(ee.Reducer.toList().repeat(6),
                                              ['t', 'id', 'versao', 'alg', 'antigo', 'nb']), f'inventário {a0}')
        partes.append(pd.DataFrame(dict(zip(['t', 'id', 'versao', 'alg', 'antigo', 'nb'], res['list']))))
        log(f'   inventário {a0}-{a1 - 1}: {len(partes[-1])} imagens')
    inv = pd.concat(partes, ignore_index=True)
    inv['data_hora'] = pd.to_datetime(inv['t'].astype('float64'), unit='ms', utc=True).dt.tz_localize(None)
    inv['dia'] = inv['data_hora'].dt.normalize()
    inv['hora'] = inv['data_hora'].dt.strftime('%H:%M')
    inv['ano'] = inv['dia'].dt.year
    inv['id_esperado'] = 'SAB_' + inv['dia'].dt.strftime('%Y_%m_%d')
    inv['par'] = inv['versao'] + ' | ' + inv['alg']
    salvar_csv(inv.drop(columns=['t']), 'D_inventario_SAB_V1.csv')
    CONTEXTO['inv'] = inv

    hist = inv[inv['dia'] <= '2025-12-31']
    faltando = sorted(set(pd.date_range('1961-01-01', '2025-12-31')) - set(hist['dia']))
    duplic = sorted(set(inv['dia'][inv['dia'].duplicated()]))
    achado('D1', 'OK' if (len(hist) == DIAS_HISTORICO and not faltando and not duplic) else 'ERRO',
           'SAB_V1 1961-2025: um dia por imagem', f'{len(hist)} imagens (esperado {DIAS_HISTORICO}), '
           f'{len(faltando)} faltando, {len(duplic)} datas duplicadas; primeiros faltando '
           f'{[d.strftime("%Y-%m-%d") for d in faltando[:5]]}')
    errados = inv[inv['id'] != inv['id_esperado']]
    achado('D2', 'OK' if errados.empty else 'ERRO', 'SAB_V1: nome da imagem bate com a data',
           f'{len(errados)} divergência(s) {errados[["id", "id_esperado"]].head(5).values.tolist()}')
    achado('D3', 'OK' if set(inv['hora']) == {'00:00'} else 'ATENÇÃO', 'SAB_V1: horário de system:time_start',
           f'{inv["hora"].value_counts().to_dict()}')
    por_ano = pd.crosstab(inv['ano'], inv['par'])
    log_tabela(por_ano, 'Imagens por ano e (versão | algoritmo):', max_linhas=80)
    salvar_csv(por_ano, 'D_versoes_por_ano.csv')
    validos_hist = {'definitiva | V1.0', 'definitiva | V1.0-P12', 'definitiva | V1.2', 'definitiva | V1.3',
                    'definitiva | V1.4'}
    estranhos = hist[~hist['par'].isin(validos_hist)]['par'].value_counts().to_dict()
    achado('D4', 'OK' if not estranhos else 'ATENÇÃO', 'SAB_V1 1961-2025: só versões definitivas reconhecidas',
           f'fora do esperado: {estranhos}' if estranhos else 'todas reconhecidas',
           'A trava do motor V1.4 impede alterar esses dias; aqui só se mede.')
    nb = inv['nb'].value_counts().to_dict()
    achado('D5', 'OK' if set(nb) == {16} else 'ATENÇÃO', 'SAB_V1: número de bandas por imagem', f'{nb}')
    achado('D6', 'INFO', 'SAB_V1: imagens com nomes antigos de banda', f'{int(inv["antigo"].astype(bool).sum())}',
           'O painel e as normais tratam os nomes antigos.')
    v26 = inv[inv['dia'] >= '2026-01-01']['par'].value_counts().to_dict()
    achado('D7', 'INFO', 'SAB_V1 2026 em diante: tipos e versões', f'{v26}',
           'A prévia da etapa 5a precisa de dias "provisoria_era5 | V1.3".')

    # Coleção temporária
    if existe(SAB_TMP):
        tmp = listar_assets(SAB_TMP)
        nomes = sorted(t['nome'] for t in tmp)
        hist_tmp = [n for n in nomes if n[4:8].isdigit() and n[4:8] <= '2025']
        achado('D8', 'OK' if not hist_tmp else 'ATENÇÃO', 'SAB_V1_TMP: sobras', f'{len(nomes)} item(ns); '
               f'históricos (até 2025): {len(hist_tmp)} {hist_tmp[:10]}',
               'O motor V1.3 promoveria essas sobras por cima do SAB_V1; a V1.4 com trava não promove.')
    else:
        achado('D8', 'OK', 'SAB_V1_TMP: sobras', 'coleção não existe')

    fidelidade_br()
    coerencia_fisica()
    ano_2026_x_clima()
    umidade_nn_x_bilinear()


def fidelidade_br():
    """Os dias definitivos guardam exatamente o BR-DWGD (com escala e offset)?"""
    col_sab = ee.ImageCollection(SAB)
    col_br = ee.ImageCollection(BR_DWGD)
    filtro = ee.Filter.Or(*[ee.Filter.date(d, (pd.Timestamp(d) + timedelta(days=1)).strftime('%Y-%m-%d'))
                            for d in DIAS_AMOSTRA_HIST])
    bandas = list(BR_PARA_SAB.values())
    sab = regiao_pontos(col_sab.filter(filtro).map(padronizar_sab), bandas, PONTOS_CP, 'SAB nos pontos')
    br = regiao_pontos(col_br.filter(filtro).map(br_fisico), bandas, PONTOS_CP, 'BR nos pontos')
    sab['dia'] = sab['data'].dt.normalize()
    br['dia'] = br['data'].dt.normalize()
    m = sab.drop(columns='data').merge(br.drop(columns='data'), on=['ponto', 'dia'], suffixes=('_sab', '_br'))
    inv = CONTEXTO['inv'].drop_duplicates('dia').set_index('dia')
    m['alg'] = m['dia'].map(inv['alg'])
    linhas = []
    for b in bandas:
        dif = (m[f'{b}_sab'] - m[f'{b}_br']).abs()
        linhas.append({'banda': b, 'pares': int(dif.notna().sum()), 'max_dif': dif.max(),
                       'pares_com_dif>0.01': int((dif > 0.01).sum())})
    tab = pd.DataFrame(linhas).set_index('banda')
    log_tabela(tab, 'SAB definitivo x BR-DWGD (mesmo pixel, mesmos dias):')
    salvar_csv(m, 'D_fidelidade_SAB_x_BR.csv')
    divergentes = tab[tab['pares_com_dif>0.01'] > 0]
    detalhe = ''
    if len(divergentes):
        b = divergentes.index[0]
        sub = m[(m[f'{b}_sab'] - m[f'{b}_br']).abs() > 0.01]
        detalhe = f' | versões com divergência: {sub["alg"].value_counts().to_dict()}'
    achado('D9', 'OK' if divergentes.empty else 'ATENÇÃO', 'Dias definitivos do SAB = BR-DWGD',
           f'{len(divergentes)} banda(s) com diferença > 0,01: {divergentes.index.tolist()}{detalhe}',
           'Confirma que o histórico gravado usa a mesma escala/offset do motor atual.')


def coerencia_fisica():
    inv = CONTEXTO['inv']
    mapa_par = inv.drop_duplicates('dia').set_index('dia')['par']
    dias = list(DIAS_AMOSTRA_HIST)
    d26 = inv[inv['dia'] >= '2026-01-01'].sort_values('dia')
    for par, g in d26.groupby('par'):
        idx = np.linspace(0, len(g) - 1, min(len(g), 4 if RAPIDO else 8)).astype(int)
        dias += [g.iloc[i]['dia'].strftime('%Y-%m-%d') for i in idx]
    linhas = []
    for d in sorted(set(dias)):
        img = ee.Image(ee.ImageCollection(SAB).filterDate(d, (pd.Timestamp(d) + timedelta(days=1)).strftime('%Y-%m-%d')).first())
        s = padronizar_sab(img)
        ind = ee.Image.cat([
            s.select('RH').lt(0).Or(s.select('RH').gt(100)).rename('UR_fora_0_100'),
            s.select('pr_mm').lt(0).rename('chuva_negativa'),
            s.select('et_potencial').lt(0).rename('ETo_negativa'),
            s.select('u2').lt(0).rename('vento_negativo'),
            s.select('rs').lt(0).rename('radiacao_negativa'),
            s.select('tmax_C').lt(s.select('tmin_C')).rename('Tmax_menor_Tmin'),
            s.select('et_real').gt(s.select('et_potencial').add(1e-4)).rename('ETreal_maior_ETo'),
            s.select('transpiracao_mm').gt(s.select('et_real').add(1e-4)).rename('transp_maior_ETreal'),
            s.select('soil_moisture_0_100cm_m3_m3').gt(UMIDADE_MAX).rename('umid100_acima_0_9'),
            s.select('soil_moisture_0_5cm_m3_m3').gt(UMIDADE_MAX).rename('umid5_acima_0_9'),
            s.select('tmax_C').lte(-20.0005).rename('Tmax_igual_-20'),
            s.select('pr_mm').mask().rename('pixels'),
        ]).updateMask(MASCARA_BR)
        r = rr(ind, ee.Reducer.sum(), f'coerência {d}')
        mm = rr(s.select(['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'soil_moisture_0_100cm_m3_m3'])
                .updateMask(MASCARA_BR), ee.Reducer.minMax(), f'faixas {d}')
        lin = {'dia': d, 'par': mapa_par.get(pd.Timestamp(d), '?')}
        lin.update({k: r.get(k) for k in r})
        lin.update({k: mm.get(k) for k in mm})
        linhas.append(lin)
        log(f'   {d} ({lin["par"]}): pixels {r.get("pixels"):.0f} | UR fora {r.get("UR_fora_0_100")} | '
            f'Tmax<Tmin {r.get("Tmax_menor_Tmin")} | ETreal>ETo {r.get("ETreal_maior_ETo")} | '
            f'umid100>0,9 {r.get("umid100_acima_0_9")} | ETo<0 {r.get("ETo_negativa")}')
    tab = pd.DataFrame(linhas).set_index('dia')
    salvar_csv(tab, 'D_coerencia_fisica_por_dia.csv')
    CONTEXTO['coerencia'] = tab
    cols = ['UR_fora_0_100', 'chuva_negativa', 'ETo_negativa', 'vento_negativo', 'radiacao_negativa',
            'Tmax_menor_Tmin', 'ETreal_maior_ETo', 'transp_maior_ETreal', 'umid100_acima_0_9',
            'umid5_acima_0_9', 'Tmax_igual_-20']
    resumo = tab.groupby('par')[cols + ['pixels']].sum()
    pct = resumo[cols].div(resumo['pixels'], axis=0) * 100
    log_tabela(pct.round(4).T, 'Coerência física (% dos pixels do Brasil nos dias de amostra, por versão):')
    salvar_csv(pct, 'D_coerencia_fisica_pct.csv')
    pixels = tab['pixels'].astype(float)
    achado('D10', 'OK' if pixels.std() / pixels.mean() < 0.01 else 'ATENÇÃO', 'SAB_V1: cobertura de pixels por dia',
           f'média {pixels.mean():.0f}, mínimo {pixels.min():.0f}, máximo {pixels.max():.0f}',
           'Todos os dias devem cobrir o mesmo conjunto de pixels.')
    for c in cols:
        total = pct[c].max()
        status = 'OK' if total == 0 else ('INFO' if c in ('umid100_acima_0_9', 'umid5_acima_0_9', 'ETreal_maior_ETo',
                                                          'transp_maior_ETreal') else 'ATENÇÃO')
        piores = pct[c][pct[c] > 0].round(4).to_dict()
        achado(f'D11-{c}', status, f'SAB_V1: {c}', 'zero em todas as versões' if total == 0 else f'% por versão: {piores}',
               'Nos dias V1.0, umidade acima de 0,9 e ET real > ETo são corrigidos na leitura do painel.'
               if status == 'INFO' else '')


def ano_2026_x_clima():
    """Meses completos de 2026 (provisório ERA5 calibrado) x climatologia 1986-2025 do BR-DWGD."""
    inv = CONTEXTO['inv']
    hoje = datetime.now(timezone.utc)
    meses = [m for m in range(1, hoje.month) if
             len(inv[(inv['dia'].dt.year == 2026) & (inv['dia'].dt.month == m)]) == calendar.monthrange(2026, m)[1]]
    if not meses:
        achado('D12', 'NÃO EXECUTADO', '2026 x climatologia', 'nenhum mês completo de 2026')
        return
    linhas = []
    for m in meses:
        ini = f'2026-{m:02d}-01'
        fim = (pd.Timestamp(ini) + pd.offsets.MonthBegin(1)).strftime('%Y-%m-%d')
        sab = ee.ImageCollection(SAB).filterDate(ini, fim).map(padronizar_sab)
        nd = calendar.monthrange(2026, m)[1]
        mes_img = ee.Image.cat([sab.select('pr_mm').sum().rename('pr_mes'),
                                sab.select(['tmax_C', 'tmin_C', 'RH', 'et_potencial', 'rs', 'u2']).mean()])
        clima = ee.Image(f'{CLIMA}/Matriz_Clima_{m:02d}')
        ref = ee.Image.cat([clima.select('pr_m_br').multiply(nd).rename('c_pr_mes'),
                            clima.select(['Tmax_m_br', 'Tmin_m_br', 'RH_m_br', 'ET_m_br', 'Rs_m_br', 'u2_m_br'])])
        img = ee.Image.cat([mes_img, ref]).set('system:time_start', ee.Date(ini).millis())
        df = regiao_pontos(ee.ImageCollection([img]), ['pr_mes', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'rs', 'u2',
                                                       'c_pr_mes', 'Tmax_m_br', 'Tmin_m_br', 'RH_m_br', 'ET_m_br',
                                                       'Rs_m_br', 'u2_m_br'], PONTOS_CP, f'2026-{m:02d}')
        df['mes'] = m
        linhas.append(df)
    t = pd.concat(linhas, ignore_index=True)
    t['razao_chuva'] = t['pr_mes'] / t['c_pr_mes']
    t['dif_Tmax'] = t['tmax_C'] - t['Tmax_m_br']
    t['dif_Tmin'] = t['tmin_C'] - t['Tmin_m_br']
    t['dif_UR'] = t['RH'] - t['RH_m_br']
    t['razao_ETo'] = t['et_potencial'] / t['ET_m_br']
    t['razao_Rs'] = t['rs'] / t['Rs_m_br']
    t['razao_vento'] = t['u2'] / t['u2_m_br']
    cols = ['razao_chuva', 'dif_Tmax', 'dif_Tmin', 'dif_UR', 'razao_ETo', 'razao_Rs', 'razao_vento']
    resumo = t.groupby('mes')[cols].median()
    log_tabela(resumo.round(2), '2026 (provisório) x climatologia 1986-2025, mediana dos 18 pontos:')
    salvar_csv(t.set_index(['mes', 'ponto']), 'D_2026_x_climatologia.csv')
    implaus = t[(t['dif_Tmax'].abs() > 5) | (t['dif_Tmin'].abs() > 5) | (t['dif_UR'].abs() > 25) |
                (t['razao_ETo'] > 1.6) | (t['razao_ETo'] < 0.6) | (t['razao_vento'] > 2.5) | (t['razao_Rs'] > 1.5)]
    achado('D12', 'OK' if implaus.empty else 'ATENÇÃO', '2026 provisório x climatologia (plausibilidade)',
           f'{len(implaus)} mês-ponto com desvio fisicamente improvável (|ΔT|>5 °C, |ΔUR|>25, ETo fora de 0,6-1,6x, '
           f'vento > 2,5x, radiação > 1,5x); viés mediano Tmax {resumo["dif_Tmax"].median():+.2f} °C, '
           f'UR {resumo["dif_UR"].median():+.1f}, ETo {resumo["razao_ETo"].median():.2f}x',
           'Chuva diferente do normal é esperada (El Niño); desvios grandes de temperatura, UR, ETo, vento '
           'ou radiação apontam problema na rota provisória.')


def umidade_nn_x_bilinear():
    """Quanto a umidade calibrada muda ao trocar vizinho mais próximo por bilinear (antecipa a etapa 5a)."""
    def expandir(img):
        return img.unmask(img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMean(1, 'square', 'pixels'))

    linhas = []
    for m in MESES_SOLO_2025:
        d = f'2025-{m:02d}-15'
        era = ee.Image(ee.ImageCollection(ERA5).filterDate(d, (pd.Timestamp(d) + timedelta(days=1)).strftime('%Y-%m-%d')).first())
        solo = ee.Image(f'{SOLO}/Matriz_Solo_{m:02d}')
        res = {}
        for nome, p, bruto in (('umid5', 'ssur', era.select('volumetric_soil_water_layer_1')),
                               ('umid100', 'swat', era.expression('(l1*7 + l2*21 + l3*72) / 100', {
                                   'l1': era.select('volumetric_soil_water_layer_1'),
                                   'l2': era.select('volumetric_soil_water_layer_2'),
                                   'l3': era.select('volumetric_soil_water_layer_3')}))):
            fator = expandir(solo.select(f'{p}_m_smap')).divide(expandir(solo.select(f'{p}_m_era5')).max(1e-3)).min(FATOR_MAX)
            teto = expandir(solo.select(f'{p}_m_smap')).add(expandir(solo.select(f'{p}_s_smap')).multiply(3)) \
                .min(UMIDADE_MAX).unmask(UMIDADE_MAX)
            nn = bruto.multiply(fator).max(0).min(teto)
            bil = bruto.resample('bilinear').multiply(fator).max(0).min(teto)
            dif = bil.subtract(nn)
            img = ee.Image.cat([nn.rename('nn'), bil.rename('bil'), dif.abs().rename('absdif'),
                                dif.abs().gt(0.001).rename('alterado')]).updateMask(MASCARA_BR)
            r = rr(img, ee.Reducer.mean(), f'solo {nome} {d}')
            res[nome] = r
        lin = {'dia': d}
        for nome, r in res.items():
            lin[f'{nome}_nn'] = r['nn']
            lin[f'{nome}_bil'] = r['bil']
            lin[f'{nome}_delta_pct'] = 100 * (r['bil'] / r['nn'] - 1)
            lin[f'{nome}_absdif_medio'] = r['absdif']
            lin[f'{nome}_pct_pixels_alterados'] = 100 * r['alterado']
        linhas.append(lin)
        log(f'   {d}: Δ umid 0-5 {lin["umid5_delta_pct"]:+.2f}% | Δ umid 0-100 {lin["umid100_delta_pct"]:+.2f}% | '
            f'pixels alterados {lin["umid5_pct_pixels_alterados"]:.1f}% / {lin["umid100_pct_pixels_alterados"]:.1f}%')
    tab = pd.DataFrame(linhas).set_index('dia')
    salvar_csv(tab, 'D_umidade_nn_x_bilinear.csv')
    pior = max(tab['umid5_delta_pct'].abs().max(), tab['umid100_delta_pct'].abs().max())
    achado('D13', 'OK' if pior <= 2 else 'ATENÇÃO', 'Umidade do solo: vizinho mais próximo x bilinear (Brasil)',
           f'maior |Δ| nacional {pior:.2f}% (critério da etapa 5a: ±2%); |Δ| médio por pixel '
           f'{tab["umid5_absdif_medio"].mean():.4f} / {tab["umid100_absdif_medio"].mean():.4f} m³/m³',
           'Mede, em dias de 2025, o efeito da mudança SOLO_BILINEAR da V1.4. Dentro de ±2%: a descontinuidade '
           'com o histórico é desprezível na média nacional.',
           '' if pior <= 2 else 'Decidir antes da etapa 5b: manter vizinho mais próximo ou reprocessar o solo do histórico.')


# =========================================================================
# E. MATRIZES DE CALIBRAÇÃO
# =========================================================================
def percentis(img, rotulo):
    red = ee.Reducer.percentile([1, 5, 50, 95, 99]).combine(ee.Reducer.count(), sharedInputs=True)
    return rr(img.updateMask(MASCARA_BR), red, rotulo)


@secao('E', 'Matrizes de calibração')
def secao_e():
    # E1 clima
    linhas = []
    for m in range(1, 13):
        c = ee.Image(f'{CLIMA}/Matriz_Clima_{m:02d}')
        if m == 1:
            log(f'   bandas SICSB_1986_2025: {gi(c.bandNames(), "bandas clima")}')
        fat = ee.Image.cat([c.select(f'{p}_m_br').divide(c.select(f'{p}_m_era').max(1e-3)).rename(f'fator_{p}')
                            for p in ('pr', 'u2', 'Rs')])
        adi = ee.Image.cat([c.select(f'{p}_m_br').subtract(c.select(f'{p}_m_era')).rename(f'dif_{p}')
                            for p in ('Tmax', 'Tmin', 'RH')])
        acima = fat.gt(FATOR_MAX).rename([f'acima5_{p}' for p in ('pr', 'u2', 'Rs')])
        r = percentis(ee.Image.cat([fat, adi]), f'clima {m:02d}')
        a = rr(acima.updateMask(MASCARA_BR), ee.Reducer.mean(), f'clima acima {m:02d}')
        lin = {'mes': m}
        lin.update(r)
        lin.update({k: 100 * v for k, v in a.items()})
        linhas.append(lin)
    tab = pd.DataFrame(linhas).set_index('mes')
    salvar_csv(tab, 'E_clima_fatores.csv')
    cols_show = [c for c in tab.columns if c.endswith(('_p1', '_p50', '_p99')) or c.startswith('acima5')]
    log_tabela(tab[cols_show].round(3), 'SICSB_1986_2025: fatores BR/ERA5 e diferenças (percentis no Brasil); % acima de 5:')
    pct5 = tab[[c for c in tab.columns if c.startswith('acima5')]].max().max()
    achado('E1', 'OK' if pct5 < 1 else 'ATENÇÃO', 'Matriz clima: pixels com fator acima do teto de 5',
           f'máximo {pct5:.2f}% dos pixels em algum mês/variável',
           'Onde o fator passa de 5 o motor limita; muitos pixels indicam ERA5 com média quase zero.')
    achado('E2', 'INFO', 'Matriz clima: correção aditiva de temperatura e UR (mediana nacional)',
           f'Tmax {tab["dif_Tmax_p50"].median():+.2f} °C, Tmin {tab["dif_Tmin_p50"].median():+.2f} °C, '
           f'UR {tab["dif_RH_p50"].median():+.1f} pontos; extremos Tmax {tab["dif_Tmax_p1"].min():+.1f} a '
           f'{tab["dif_Tmax_p99"].max():+.1f} °C')

    # E3 solo
    linhas = []
    for m in range(1, 13):
        s = ee.Image(f'{SOLO}/Matriz_Solo_{m:02d}')
        if m == 1:
            log(f'   bandas SICSB_SOLO_2015_2025: {gi(s.bandNames(), "bandas solo")}')
        fat = ee.Image.cat([s.select(f'{p}_m_smap').divide(s.select(f'{p}_m_era5').max(1e-3)).rename(f'fator_{p}')
                            for p in ('ssur', 'swat', 'rsup', 'rsub')])
        r = percentis(fat, f'solo {m:02d}')
        a = rr(fat.gt(FATOR_MAX).updateMask(MASCARA_BR), ee.Reducer.mean(), f'solo acima {m:02d}')
        lin = {'mes': m}
        lin.update(r)
        lin.update({f'acima5_{k}': 100 * v for k, v in a.items()})
        linhas.append(lin)
    tab = pd.DataFrame(linhas).set_index('mes')
    salvar_csv(tab, 'E_solo_fatores.csv')
    cols_show = [c for c in tab.columns if c.endswith(('_p5', '_p50', '_p95')) or c.startswith('acima5')]
    log_tabela(tab[cols_show].round(3), 'SICSB_SOLO_2015_2025: fatores SMAP/ERA5 (percentis no Brasil); % acima de 5:')
    for p in ('ssur', 'swat', 'rsup', 'rsub'):
        v = tab[f'acima5_fator_{p}'].max()
        achado(f'E3-{p}', 'OK' if v < 1 else 'ATENÇÃO', f'Matriz solo: fator {p} acima de 5',
               f'máximo {v:.2f}% dos pixels; mediana nacional {tab[f"fator_{p}_p50"].median():.2f}')

    # E4 GFS V1: resolução efetiva (gradiente médio GFS x BR-DWGD na Serra do Mar)
    caixa = ee.Geometry.Rectangle([-48.5, -24.8, -43.5, -21.5], None, False)
    g = ee.Image(f'{GFS_V1}/Matriz_GFS_01')
    bandas = gi(g.bandNames(), 'bandas GFS V1')
    log(f'   bandas SICSB_MATRIZ_GFS (V1): {bandas}')
    alvo = 'Tmax_m_sicsb' if 'Tmax_m_sicsb' in bandas else [b for b in bandas if b.startswith('Tmax_m_') and 'gfs' not in b][0]

    def grad(img):
        gr = img.gradient()
        return gr.select('x').hypot(gr.select('y'))

    r = rr(ee.Image.cat([grad(g.select('Tmax_m_gfs')).rename('g_gfs'), grad(g.select(alvo)).rename('g_br')]),
           ee.Reducer.mean(), 'gradientes GFS V1', geom=caixa)
    razao = r['g_gfs'] / r['g_br'] if r.get('g_br') else float('nan')
    achado('E4', 'ATENÇÃO' if razao < 0.25 else 'INFO', 'Matriz GFS V1: detalhe espacial (gradiente GFS / BR-DWGD, Serra do Mar)',
           f'{razao:.3f}',
           'Um GFS de 0,25° reamostrado corretamente guarda parte do relevo (razão tipicamente 0,3-0,7); '
           'razão muito baixa indica campo calculado em ~1° (efeito do .resample() na composição, corrigido na V2).')
    for nome, caminho in (('SICSB_MATRIZ_GFS_V2', GFS_V2), ('RONI_CPC_v6', RONI_NOVO)):
        achado(f'E5-{nome}', 'INFO', f'{nome} existe?', 'sim' if existe(caminho) else 'não (esperado antes das etapas 2 e 3)')


# =========================================================================
# F. GFS
# =========================================================================
@secao('F', 'GFS: tempos, horas de previsão por época, rodadas e radiação')
def secao_f():
    col = ee.ImageCollection(GFS)
    # F1 time_start x creation_time
    amostra = col.filterDate('2024-03-01', '2024-03-02').limit(50)
    pares = gi(amostra.reduceColumns(ee.Reducer.toList().repeat(4),
                                     ['system:time_start', 'creation_time', 'forecast_time', 'forecast_hours']), 'tempos GFS')['list']
    t = pd.DataFrame(dict(zip(['time_start', 'creation_time', 'forecast_time', 'forecast_hours'], pares))).astype(float)
    igual = (t['time_start'] == t['creation_time']).all()
    coerente = ((t['forecast_time'] - t['creation_time']) / 3.6e6 == t['forecast_hours']).all()
    achado('F1', 'OK' if igual else 'ERRO', 'GFS: system:time_start igual a creation_time',
           f'{"sim" if igual else "NÃO"} em {len(t)} imagens; forecast_time = creation + horas: {"sim" if coerente else "NÃO"}',
           'O motor e o script 03 filtram a rodada por filterDate em creation_time.')

    # F2 horas de previsão por época
    datas = sorted({f'{a}-{m:02d}-10' for a in range(2015, 2027) for m in ((1, 7) if not RAPIDO else (7,))
                    if f'{a}-{m:02d}-10' <= AGORA.strftime('%Y-%m-%d') and f'{a}-{m:02d}-10' >= '2015-07-10'}
                   | {'2017-07-08', '2017-07-10', '2017-07-12', '2019-06-11', '2019-06-13', '2021-03-21',
                      '2021-03-23', '2021-06-10', '2021-06-12', '2021-06-14'})
    linhas = []
    for d in datas:
        c = data_ms(d)
        horas = gi(col.filterDate(c, c + 3600 * 1000).filter(ee.Filter.eq('creation_time', c))
                   .aggregate_array('forecast_hours'), f'horas {d}')
        h = sorted(int(x) for x in horas)
        def passo(a, b):
            seg = [x for x in h if a < x <= b]
            return (int(np.median(np.diff(seg))) if len(seg) > 1 else None), len(seg)
        p1, n1 = passo(0, 120)
        p2, n2 = passo(120, 240)
        p3, n3 = passo(240, 384)
        linhas.append({'rodada_00Z': d, 'imagens': len(h), 'hora_max': max(h) if h else None,
                       'passo_1_120': p1, 'n_1_120': n1, 'passo_121_240': p2, 'n_121_240': n2,
                       'passo_241_384': p3, 'n_241_384': n3})
    tab = pd.DataFrame(linhas).set_index('rodada_00Z')
    log_tabela(tab, 'Horas de previsão da rodada 00Z por data:')
    salvar_csv(tab, 'F_gfs_horas_por_epoca.csv')
    # Premissas do script 03 / motor: a partir de 2017-07-10 hora a hora até 120 e de 3 em 3 até 240;
    # a partir de 2021-06-12, de 3 em 3 até 384
    def esperado(d):
        if d >= '2021-06-12':
            return (1, 120, 3, 40, 3, 48)
        if d >= '2017-07-10':
            return (1, 120, 3, 40, None, None)
        return None
    falhas = []
    for d, lin in tab.iterrows():
        e = esperado(d)
        if not e:
            continue
        obs = (lin['passo_1_120'], lin['n_1_120'], lin['passo_121_240'], lin['n_121_240'])
        if obs != e[:4] or (e[4] and (lin['passo_241_384'], lin['n_241_384']) != (e[4], e[5])):
            falhas.append(d)
    achado('F2', 'OK' if not falhas else 'ATENÇÃO', 'GFS: horas de previsão conferem com as épocas do script 03',
           f'divergências em {falhas}' if falhas else f'todas as {len(tab)} rodadas conferem',
           'Datas divergentes perdem amostra na matriz V2 (rodada incompleta é descartada), sem enviesar.')

    # F3 disponibilidade mês a mês das rodadas 00Z com as horas-chave
    chave = [6, 24, 120, 192, 312]
    meses = pd.date_range('2015-07-01', AGORA.strftime('%Y-%m-01'), freq='MS')
    if RAPIDO:
        meses = [m for m in meses if m.month in (1, 7)]
    linhas = []
    for m0 in meses:
        m1 = m0 + pd.offsets.MonthBegin(1)
        sub = col.filterDate(m0.strftime('%Y-%m-%d'), m1.strftime('%Y-%m-%d')).filter(ee.Filter.inList('forecast_hours', chave))
        res = gi(sub.reduceColumns(ee.Reducer.toList().repeat(2), ['creation_time', 'forecast_hours']), f'rodadas {m0:%Y-%m}')['list']
        df = pd.DataFrame({'c': res[0], 'h': res[1]}).astype(float)
        df = df[(df['c'] % 86400000) == 0]                    # só rodadas 00Z
        nd = calendar.monthrange(m0.year, m0.month)[1]
        lin = {'mes': m0.strftime('%Y-%m'), 'dias_no_mes': nd}
        for h in chave:
            lin[f'dias_com_h{h}'] = df[df['h'] == h]['c'].nunique()
        linhas.append(lin)
    tab = pd.DataFrame(linhas).set_index('mes')
    salvar_csv(tab, 'F_gfs_rodadas_00Z_por_mes.csv')
    log_tabela(tab, 'Dias do mês com rodada 00Z contendo cada hora-chave (6 e 24 = 1º dia; 120 = dia 5; 192 = dia 8; 312 = dia 13):', 150)
    pos = tab[(tab.index >= '2017-08') & (tab.index < AGORA.strftime('%Y-%m'))]   # mês corrente ainda incompleto
    falhos = pos[pos['dias_com_h24'] < 0.8 * pos['dias_no_mes']].index.tolist()
    achado('F3', 'OK' if not falhos else 'ATENÇÃO', 'GFS: meses com menos de 80% das rodadas 00Z (desde 2017-08)',
           f'{falhos}' if falhos else 'nenhum', 'Meses com poucas rodadas pesam menos na matriz V2.')

    transicoes_gfs()
    radiacao_gfs()


def transicoes_gfs():
    """Primeira rodada 00Z com previsão até 384 h e primeira com saídas de 3 em 3 h após 240 h."""
    col = ee.ImageCollection(GFS)

    def horas(d):
        c = data_ms(d)
        h = gi(col.filterDate(c, c + 3600 * 1000).filter(ee.Filter.eq('creation_time', c))
               .aggregate_array('forecast_hours'), f'transição {d}')
        return sorted(int(x) for x in h)

    def primeira(dias, teste):
        for d in dias:
            h = horas(d)
            if h and teste(h):
                return d
        return None

    tem_384 = lambda h: max(h) >= 384 and sum(1 for x in h if x <= 120) == 120
    tres_apos_240 = lambda h: sum(1 for x in h if 240 < x <= 384) == 48
    meses = [m.strftime('%Y-%m-%d') for m in pd.date_range('2016-07-01', '2017-08-01', freq='MS')]
    m1 = primeira(meses, tem_384)
    d384 = None
    if m1:
        ini = (pd.Timestamp(m1) - pd.offsets.MonthBegin(1)).strftime('%Y-%m-%d')
        d384 = primeira([x.strftime('%Y-%m-%d') for x in pd.date_range(ini, m1)], tem_384)
    d3h = primeira([x.strftime('%Y-%m-%d') for x in pd.date_range('2019-06-05', '2019-06-20')], tres_apos_240)
    CONTEXTO['gfs_384_desde'] = d384
    CONTEXTO['gfs_3h_apos_240_desde'] = d3h
    achado('F5', 'ATENÇÃO' if (d384 and d384 < '2017-07-10') or (d3h and d3h < '2021-06-12') else 'OK',
           'GFS: datas reais das mudanças de saídas (rodadas 00Z)',
           f'384 h com saída horária até 120 h desde {d384}; saídas de 3 em 3 h entre 241 e 384 h desde {d3h}',
           'O script 03 usa 10/07/2017 e 12/06/2021 (datas do catálogo). Datas reais mais antigas permitem '
           'mais anos na matriz V2; rodadas incompletas continuam descartadas pelo teste de completude.')


def radiacao_gfs():
    """Radiação do GFS: instantânea ou média do intervalo? Usa um ponto em Brasília numa rodada de inverno."""
    col = ee.ImageCollection(GFS)
    linhas = []
    for d in ('2025-07-15', '2025-01-15'):
        c = data_ms(d)
        run = col.filterDate(c, c + 3600 * 1000).filter(ee.Filter.eq('creation_time', c)) \
            .filter(ee.Filter.gt('forecast_hours', 0)).filter(ee.Filter.lte('forecast_hours', 48)) \
            .map(lambda i: i.set('system:time_start', i.get('forecast_time')))
        df = regiao_pontos(run, ['downward_shortwave_radiation_flux', 'temperature_2m_above_ground'],
                           [('Brasilia', -15.79, -47.88)], f'radiação {d}', escala=27830)
        df['hora_UTC'] = df['data'].dt.hour
        df['rodada'] = d
        linhas.append(df)
    t = pd.concat(linhas, ignore_index=True).sort_values(['rodada', 'data'])
    salvar_csv(t, 'F_gfs_radiacao_brasilia.csv')
    log_tabela(t[['rodada', 'data', 'hora_UTC', 'downward_shortwave_radiation_flux',
                  'temperature_2m_above_ground']].reset_index(drop=True), 'Radiação de onda curta em Brasília (W/m²):', 100)
    # Em Brasília (UTC-3) o sol se põe por volta das 21-21:30 UTC; às 23 e 00 UTC é noite.
    noite = t[t['hora_UTC'].isin([23, 0])]['downward_shortwave_radiation_flux']
    media = noite.mean()
    instant = media < 5
    achado('F4', 'INFO' if instant else 'ATENÇÃO', 'GFS: natureza da radiação de onda curta',
           f'valor médio às 23 e 00 UTC (noite em Brasília): {media:.1f} W/m² -> '
           f'{"instantânea" if instant else "MÉDIA ACUMULADA DO BLOCO (não instantânea)"}',
           'Se for média do bloco de 6 h, a média simples das saídas horárias superestima a radiação diária; '
           'o certo seria usar só as horas múltiplas de 6 (como na chuva).',
           '' if instant else 'Ajustar o cálculo da radiação no motor e na matriz GFS V2 antes de gerá-la.')
    CONTEXTO['radiacao_gfs_instantanea'] = instant


# =========================================================================
# G. ERA5-LAND
# =========================================================================
@secao('G', 'ERA5-Land: última data e grade')
def secao_g():
    col = ee.ImageCollection(ERA5)
    hoje = ee.Date(AGORA.strftime('%Y-%m-%d'))
    ult = gi(col.filterDate(hoje.advance(-150, 'day'), hoje.advance(1, 'day')).aggregate_max('system:time_start'), 'ERA5 último')
    atraso = (AGORA.date() - datetime.fromtimestamp(ult / 1000, tz=timezone.utc).date()).days
    achado('G1', 'OK' if atraso <= 12 else 'ATENÇÃO', 'ERA5-Land: último dia disponível',
           f'{ms_para_txt(ult)} ({atraso} dias atrás)')
    p_era = gi(ee.Image(col.first()).select('total_precipitation_sum').projection(), 'proj ERA5')
    p_br = gi(ee.Image(ee.ImageCollection(BR_DWGD).first()).select('pr').projection(), 'proj BR')
    log(f'   ERA5-Land: {p_era}\n   BR-DWGD:   {p_br}')
    t_e, t_b = p_era.get('transform'), p_br.get('transform')
    if t_e and t_b:
        off_x = ((t_e[2] + t_e[0] / 2) - (t_b[2] + t_b[0] / 2)) / t_b[0] % 1
        off_y = ((t_e[5] + t_e[4] / 2) - (t_b[5] + t_b[4] / 2)) / abs(t_b[4]) % 1
        meio = 0.4 < off_x < 0.6 or 0.4 < off_y < 0.6
        achado('G2', 'INFO', 'Grade ERA5-Land x grade SAB (BR-DWGD)',
               f'deslocamento dos centros em fração de pixel: x {off_x:.2f}, y {off_y:.2f} '
               f'({"meio pixel" if meio else "alinhadas"})',
               'Com meio pixel, vizinho mais próximo e bilinear diferem mais (ver D13).')
    else:
        achado('G2', 'NÃO EXECUTADO', 'Grade ERA5-Land x grade SAB', 'projeção sem transform')


# =========================================================================
# H. OISST E RONI
# =========================================================================
@secao('H', 'OISST e RONI')
def secao_h():
    col = ee.ImageCollection(OISST)
    hoje = ee.Date(AGORA.strftime('%Y-%m-%d'))
    rec = col.filterDate(hoje.advance(-60, 'day'), hoje.advance(1, 'day'))
    ult = gi(rec.aggregate_max('system:time_start'), 'OISST último')
    st = gi(rec.aggregate_histogram('status'), 'OISST status')
    achado('H1', 'INFO', 'OISST: último dia e status dos últimos 60 dias', f'{ms_para_txt(ult)} | {st}')

    geo = ee.Geometry.Rectangle([-179.99, -20, 179.99, 20])
    plano = ee.Geometry.Rectangle([-180, -20, 180, 20], None, False)
    a_geo = gi(geo.area(maxError=1), 'área geodésica') / 1e6
    a_pl = gi(plano.area(maxError=1), 'área plana') / 1e6
    achado('H2', 'ATENÇÃO' if a_geo < 1.5e8 else 'OK', 'Retângulo tropical do Código 1 e do painel antigos',
           f'área com a definição antiga {a_geo:,.0f} km² x plana {a_pl:,.0f} km² (esperado ~174 milhões)',
           'Área muito menor que a plana confirma que a média tropical antiga era calculada numa tira na linha '
           'de data.' if a_geo < 1.5e8 else 'A definição antiga já cobria a faixa tropical inteira: a correção '
           'das geometrias no RONI é só preventiva.')

    # RONI antigo x CPC
    try:
        cpc = pd.read_csv(URL_RONI_CPC, sep=r'\s+').rename(columns={'SEAS': 'Trimestre', 'YR': 'ano', 'ANOM': 'RONI_2c'})
    except Exception as e:
        achado('H3', 'NÃO EXECUTADO', 'RONI antigo x CPC', f'não foi possível baixar o arquivo do CPC ({e})')
        return
    ult_cpc = cpc.iloc[-1]
    achado('H3', 'INFO', 'Arquivo oficial do CPC (RONI.ascii.txt)', f'{len(cpc)} estações; última {ult_cpc["Trimestre"]} '
           f'{int(ult_cpc["ano"])} = {ult_cpc["RONI_2c"]}', 'A tabela do script 02 deve terminar na mesma estação.')
    props = [f['properties'] for f in gi(ee.FeatureCollection(RONI_ANTIGO), 'RONI antigo')['features']]
    log(f'   propriedades do asset RONI antigo: {sorted(props[0])}')
    ordem = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']
    if 'Year' in props[0]:
        antigo = pd.DataFrame(props).set_index('Year')[ordem].apply(pd.to_numeric, errors='coerce').stack().reset_index()
        antigo.columns = ['ano', 'Trimestre', 'valor']
        formato = 'largo (Year, DJF...)'
    else:
        col_v = 'ONI' if 'ONI' in props[0] else ('RONI' if 'RONI' in props[0] else None)
        antigo = pd.DataFrame(props).rename(columns={col_v: 'valor'})[['ano', 'Trimestre', 'valor']]
        formato = f'longo (ano, Trimestre, {col_v})'
    antigo['ano'] = antigo['ano'].astype(int)
    m = antigo.merge(cpc, on=['ano', 'Trimestre'], how='left')
    m['dif'] = (m['valor'] - m['RONI_2c']).abs()
    salvar_csv(m, 'H_roni_antigo_x_cpc.csv')
    n_dif = int((m['dif'] > 0.051).sum())
    achado('H4', 'OK' if n_dif == 0 else 'ATENÇÃO', 'Asset RONI antigo x RONI oficial do CPC (ERSSTv6)',
           f'formato {formato}; {len(m)} estações ({m["ano"].min()}-{m["ano"].max()}); {n_dif} diferem mais que o '
           f'arredondamento (maior diferença {m["dif"].max():.2f})',
           'Diferenças mostram que o asset antigo não é a série oficial atual; o painel novo usa RONI_CPC_v6.')


# =========================================================================
# I. BASELINES
# =========================================================================
@secao('I', 'Pasta Baselines')
def secao_i():
    if not existe(BASELINES):
        achado('I1', 'INFO', 'Pasta Baselines', 'não existe')
        return
    itens = listar_assets(BASELINES)
    linhas = []
    for a in itens:
        n, versoes = None, None
        if a['tipo'] == 'IMAGE_COLLECTION':
            c = ee.ImageCollection(a['caminho']).map(lambda i: i.set('v', ee.Algorithms.If(
                i.propertyNames().contains('versao_baseline'), i.get('versao_baseline'), 'SEM_VERSAO')))
            n = gi(c.size(), f"tamanho {a['nome']}")
            versoes = gi(c.aggregate_histogram('v'), f"versões {a['nome']}") if n else {}
        linhas.append({'item': a['nome'], 'tipo': a['tipo'], 'imagens': n, 'versoes': versoes})
    tab = pd.DataFrame(linhas).set_index('item')
    log_tabela(tab, 'Conteúdo da pasta Baselines:')
    salvar_csv(tab, 'I_baselines.csv')
    com_imagens = tab[tab['imagens'].fillna(0) > 0]
    achado('I1', 'OK' if com_imagens.empty else 'ATENÇÃO', 'Baselines: coleções já com imagens',
           'todas vazias' if com_imagens.empty else f'{com_imagens["imagens"].to_dict()} versões '
           f'{com_imagens["versoes"].to_dict()}',
           'Os scripts de normais pulam imagens existentes; imagens de versão antiga ficariam misturadas com a B1.1b.')


# =========================================================================
# EXECUÇÃO E RESUMO
# =========================================================================
inicio_total = time.time()
for codigo, titulo, fn in SECOES:
    if SECOES_A_RODAR and codigo not in SECOES_A_RODAR:
        continue
    log('\n' + '=' * 100)
    log(f'SEÇÃO {codigo}: {titulo}')
    log('=' * 100)
    t0 = time.time()
    try:
        fn()
    except Exception as e:
        achado(codigo, 'NÃO EXECUTADO', f'Seção {codigo} interrompida', f'{type(e).__name__}: {str(e)[:300]}',
               'As demais seções continuam. Ver o traceback no log.')
        log(traceback.format_exc())
    log(f'   ⏱️ seção {codigo}: {(time.time() - t0) / 60:.1f} min')

resumo = pd.DataFrame(ACHADOS)
resumo['ordem'] = resumo['status'].map(ORDEM_STATUS)
resumo = resumo.sort_values(['ordem', 'codigo']).drop(columns='ordem').reset_index(drop=True)
resumo.to_csv(os.path.join(PASTA, 'RESUMO_ACHADOS.csv'), sep=';', index=False, encoding='utf-8-sig')
with open(os.path.join(PASTA, 'RESUMO_ACHADOS.json'), 'w', encoding='utf-8') as f:
    json.dump(ACHADOS, f, ensure_ascii=False, indent=1, default=str)

log('\n' + '=' * 100)
log(f'RESUMO DA AUDITORIA | {len(resumo)} itens | {(time.time() - inicio_total) / 60:.0f} min')
log('=' * 100)
log(f'contagem por status: {resumo["status"].value_counts().to_dict()}')
for _, r in resumo.iterrows():
    simbolo = {'OK': '✅', 'ATENÇÃO': '⚠️', 'ERRO': '❌', 'INFO': 'ℹ️', 'NÃO EXECUTADO': '⏭️'}[r['status']]
    log(f'{simbolo} [{r["codigo"]}] {r["titulo"]}: {r["resultado"]}')
log('\nNada foi gravado no Earth Engine (trava de somente leitura ativa durante toda a execução).')

arq_zip = shutil.make_archive(PASTA, 'zip', PASTA)
log(f'📦 Pacote com log, resumo e tabelas: {arq_zip}')
try:
    from google.colab import files
    files.download(arq_zip)
except Exception:
    log('   (download automático indisponível; baixe pelo painel Arquivos do Colab)')
