# =========================================================================================
# K9A - VALIDAÇÃO AMPLIADA DE TODAS AS VARIÁVEIS DA PREVISÃO GFS (SOMENTE LEITURA)
# [Versão do pacote, depois da revisão K9A] O "motor" comparado aqui é o motor V1.5 ATUAL: Tmax, Tmin, UR e
# radiação pela escala de variância; chuva com o fator (m+0,1)/(m+0,1) e teto 5; vento com o fator [0,5; 2].
# Os métodos anteriores à revisão K9A (UR aditiva e radiação com fator) entram como alternativas. A execução
# de 20/10/2026 (zip validacao_K9A_20261020_1846) foi feita com a versão anterior deste arquivo, em que o
# "motor" ainda tinha a UR aditiva e a radiação com fator; as contas e os números são os mesmos, só os rótulos
# mudam. Use esta versão para refazer a validação (por exemplo, no período do GFS v17: ajuste BLOCOS).
# Amplia a K9 ao máximo que o acervo permite:
#   - TODOS os dias (a K9 usava 1 a cada 3), de 01/07/2015 (início do NOAA/GFS0P25 no Earth Engine) a
#     31/12/2025 (fim do BR-DWGD no SAB); prazos 1, 3, 8 e 13 dias (um de cada faixa); os 300 pontos da K8/K9
#   - O GFS mudou de versão 3 vezes nesse período, e cada versão erra diferente (auditoria K2). Por isso
#     nada é treinado misturando versões: cada bloco é treinado e testado só com ele mesmo
#       GFS v13 (rodadas de 01/07/2015 a 18/07/2017) | GFS v14 (20/07/2017 a 11/06/2019)
#       GFS v15 (13/06/2019 a 21/03/2021)           | GFS v16 (23/03/2021 a 31/12/2025; o do motor)
#     As rodadas dos dias de troca de versão ficam de fora
#   - Três testes:
#     A. OFICIAL (decide): GFS v16, treino até 31/12/2024, teste em 2025 inteiro, todos os métodos
#     B. CADA ANO DE FORA (decide junto com o A): em cada bloco, cada ano é testado com o treino nos outros
#        anos do mesmo bloco. No v16 são 5 testes (2021 a 2025)
#     C. VERSÕES ANTIGAS (só informação): o mesmo B nos blocos v13, v14 e v15. Mostra se a escolha do
#        método vale também para outro modelo e outros anos; não muda o motor, que só usa o v16
#   - Estatísticas de treino por ponto, prazo e MÊS, como a matriz V2.1. Com todos os dias, o treino tem
#     cerca de 120 dias por ponto, prazo e mês no v16 (perto do que a matriz usa)
#   - Variáveis: chuva, Tmax, Tmin, umidade relativa, vento, radiação e ETo (Penman do motor)
# REGRA DA INDICAÇÃO (definida antes de rodar): um método só substitui o do motor se
#   (1) no teste A errar pelo menos 3% menos (MAE), com o IC 95% (bootstrap de dias) inteiro abaixo de zero,
#       sem piorar a razão de volume em mais de 0,05, nem o ETS da chuva (1 mm) em mais de 0,01, nem o erro
#       do total mensal (chuva e ETo) em mais de 1 ponto percentual; e
#   (2) errar menos que o motor em TODOS os anos do teste B no v16 (o mapeamento de quantis entra no B só no v16).
#   O "GFS sem correção" também é candidato (na K9 ele ficou de fora da regra).
# Nada é gravado no Earth Engine. RODE SOZINHA: nenhum outro script do projeto rodando ao mesmo tempo.
# COMO RODAR: cole inteiro numa célula do Colab e rode. Leva de 2 a 3 horas. Deixe a aba aberta.
#   Com USAR_DRIVE = True (padrão), os lotes baixados ficam no seu Google Drive: se o Colab desconectar,
#   rode de novo e ele continua de onde parou (na 1ª vez, autorize o acesso ao Drive).
#   No final baixa um zip pequeno com os resultados (os dados brutos ficam no Drive, em parquet).
# =========================================================================================
import os, shutil, time, pickle, hashlib, warnings
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# ------------------------------- CONFIGURAÇÃO -------------------------------------------
PROJETO = 'clima-492922'
N_PONTOS = 300
PASSO_DIAS = 1
LEADS = [1, 3, 8, 13]
INICIO, FIM = '2015-07-01', '2025-12-31'
FIM_TREINO_OFICIAL = '2024-12-31'
BLOCOS = [('GFS v16', '2021-03-23', '2025-12-31'), ('GFS v15', '2019-06-13', '2021-03-21'),
          ('GFS v14', '2017-07-20', '2019-06-11'), ('GFS v13', '2015-07-01', '2017-07-18')]   # datas da RODADA
PERCENTIS = [5, 10, 25, 50, 75, 90, 95]
USAR_DRIVE = True
N_BOOT = 1000
MIN_TREINO = 20
MIN_TESTE_ANO = 20000      # ano com menos pares que isso (anos parciais pequenos) não vira teste no B
# Constantes do motor V1.5 (05b)
K_CHUVA_MM, FATOR_MAX = 0.1, 5.0
FATOR_MIN_UV_RS, FATOR_MAX_UV_RS = 0.5, 2.0
RAZAO_DESVIO_MIN, RAZAO_DESVIO_MAX = 0.5, 2.0
AMPLITUDE_MIN_C = 1.0
GANHO_MIN = 0.03
# -----------------------------------------------------------------------------------------

BR_DWGD, GFS = 'projects/ee-alexandrexavier/assets/BR-DWGD', 'NOAA/GFS0P25'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
DIA_MS = 86400000
VARS = ['pr', 'tmax', 'tmin', 'rh', 'u2', 'rs']
NOMES = {'pr': 'Chuva (mm/dia)', 'tmax': 'Tmax (°C)', 'tmin': 'Tmin (°C)', 'rh': 'Umidade relativa (%)',
         'u2': 'Vento a 2 m (m/s)', 'rs': 'Radiação solar (MJ/m²/dia)', 'eto': 'ETo (mm/dia)'}
MOTOR = {'pr': 'motor V1.5: fator (m+0,1)/(m+0,1), teto 5', 'tmax': 'motor V1.5: escala de variância',
         'tmin': 'motor V1.5: escala de variância', 'rh': 'motor V1.5: escala de variância',
         'u2': 'motor V1.5: fator limitado a [0,5; 2]', 'rs': 'motor V1.5: escala de variância',
         'eto': 'motor V1.5'}
ANTES_K9A = {'rh': 'aditiva (motor antes da K9A)', 'rs': 'fator limitado a [0,5; 2] (motor antes da K9A)'}

AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'validacao_K9A_{AGORA:%Y%m%d_%H%M}')
CACHE = os.path.join(BASE, 'cache_validacao_K9A')
LOCAL = os.environ.get('K9_DADOS_LOCAIS')       # só para o teste offline (sem Earth Engine)
if USAR_DRIVE and not LOCAL:
    try:
        from google.colab import drive
        drive.mount('/content/drive')
        CACHE = '/content/drive/MyDrive/cache_validacao_K9A'
    except Exception as e:
        print(f'⚠️ Drive indisponível ({e}); o cache fica em {CACHE} e se perde se o Colab desconectar.')
os.makedirs(PASTA, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)
LOG = os.path.join(PASTA, 'LOG_K9A.txt')


def log(*p):
    t = ' '.join(str(x) for x in p)
    print(t, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(t + '\n')


def tabela(df, titulo):
    log(f'\n   {titulo}')
    with pd.option_context('display.width', 250, 'display.max_columns', 40, 'display.max_rows', 400):
        for linha in df.to_string().splitlines():
            log('   ' + linha)


def salvar(df, nome, index=True):
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', encoding='utf-8-sig', index=index)


def bloco_da_rodada(rodada_str):
    for nome, ini, fim in BLOCOS:
        if ini <= rodada_str <= fim:
            return nome
    return None


# =========================================================================================
# PARTE 1. DOWNLOAD (Earth Engine)
# =========================================================================================
TRANSITORIOS = ('Too many concurrent', 'Internal error', '503', '429', 'deadline', 'Connection', 'temporarily',
                'Remote end closed')
PESADOS = ('Computation timed out', 'memory limit', 'User memory', 'capacity exceeded', 'aborted after accumulating',
           'Request payload size', 'too large')


def gi(obj, rot='', n=6):
    for t in range(n):
        try:
            return obj.getInfo()
        except Exception as e:
            if 'Too many concurrent' in str(e) and t >= 1:
                raise
            if t < n - 1 and any(k in str(e) for k in TRANSITORIOS) and not any(k in str(e) for k in PESADOS):
                espera = min(30 * (t + 1), 180)
                log(f'   ↻ {rot}: servidor ocupado ({str(e)[:40]}); nova tentativa em {espera} s')
                time.sleep(espera)
                continue
            raise


def buscar(lote, construir, rot, insistencias=3):
    try:
        fc = gi(construir(lote), rot)
        return [f['properties'] for f in fc['features']]
    except Exception as e:
        recusa = any(k in str(e) for k in PESADOS + ('Too many concurrent',))
        if recusa and len(lote) > 1:
            meio = len(lote) // 2
            log(f'   ↘ {rot}: pedido recusado ({str(e)[:40]}); dividindo o lote')
            return buscar(lote[:meio], construir, rot + 'a') + buscar(lote[meio:], construir, rot + 'b')
        if recusa and insistencias > 0:
            log(f'   ⏸️ {rot}: Earth Engine ocupado; esperando 5 min antes de tentar de novo '
                '(outro script do projeto rodando ao mesmo tempo atrasa esta etapa)')
            time.sleep(300)
            return buscar(lote, construir, rot, insistencias - 1)
        raise


def em_lotes(nome, itens, construir, tam):
    chave = hashlib.md5(f'{nome}|{N_PONTOS}|{len(itens)}|{itens[:1]}|{itens[-1:]}'.encode()).hexdigest()[:8]
    lotes = [itens[i:i + tam] for i in range(0, len(itens), tam)]
    partes, t0, feitos = [], time.time(), 0
    log(f'   {nome}: {len(itens)} itens em {len(lotes)} lotes (cache em {CACHE})')
    for k, lote in enumerate(lotes):
        arq = os.path.join(CACHE, f'{nome}_{chave}_{k:05d}.pkl')
        if os.path.exists(arq):
            with open(arq, 'rb') as f:
                partes.append(pickle.load(f))
            continue
        df = pd.DataFrame(buscar(lote, construir, f'{nome} lote {k + 1}/{len(lotes)}'))
        num = [c for c in df.columns if c.startswith(('o_', 'g_')) or c == 'elev']
        if len(df):
            df[num] = df[num].apply(pd.to_numeric, errors='coerce').astype('float32')
        with open(arq, 'wb') as f:
            pickle.dump(df, f)
        partes.append(df)
        feitos += 1
        if feitos in (1, 3) or feitos % 25 == 0 or k + 1 == len(lotes):
            dec = time.time() - t0
            log(f'   … lote {k + 1}/{len(lotes)} | {dec / 60:.1f} min | faltam ~{dec / feitos * (len(lotes) - k - 1) / 60:.0f} min')
    partes = [p for p in partes if len(p)]
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def baixar():
    import ee
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloq(*a, **k):
        raise RuntimeError('SOMENTE LEITURA: escrita bloqueada')

    for _n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
               'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable',
               'startIngestion', 'cancelTask'):
        if hasattr(ee.data, _n):
            setattr(ee.data, _n, _bloq)
    ee.batch.Task.start = _bloq
    log('🔒 Trava de somente leitura ativa.\n')

    UF_BR = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
    LIMITES = UF_BR.geometry().bounds()
    MASC_BR = ee.Image.constant(1).clipToCollection(UF_BR).mask()
    PROJ_SAB = ee.Projection(CRS, TRANSFORM)
    ELEV = ee.Image('USGS/SRTMGL1_003').rename('elev').toFloat()

    def dia(col, d):
        return ee.Image(ee.ImageCollection(col).filterDate(d, ee.Date(d).advance(1, 'day')).first())

    def ms(d):
        return int(pd.Timestamp(d).value // 10 ** 6)

    def br_dia(d):
        img = dia(BR_DWGD, d)
        valido = img.select('pr').gt(-32768)
        return ee.Image.cat([
            img.select('pr').multiply(0.00686666).add(225.0).max(0).rename('o_pr'),
            img.select('Tmax').multiply(0.00106815).add(15.0).rename('o_tmax'),
            img.select('Tmin').multiply(0.00106815).add(15.0).rename('o_tmin'),
            img.select('RH').multiply(0.39370079).add(-0.393701).clamp(0, 100).rename('o_rh'),
            img.select('u2').multiply(0.05905512).add(-0.059055).rename('o_u2'),
            img.select('Rs').multiply(0.15708661).add(-0.057087).rename('o_rs'),
            img.select('ET').multiply(0.05118110).add(-0.0511811).max(0).rename('o_eto'),
        ]).toFloat().updateMask(valido)

    def u2_de(img):
        return img.select('u_component_of_wind_10m_above_ground') \
            .hypot(img.select('v_component_of_wind_10m_above_ground')).multiply(0.748).rename('u2')

    def seguro(col, banda, redutor):
        vazia = ee.Image.constant(0).rename(banda).toFloat().updateMask(ee.Image.constant(0))
        return col.select(banda).map(lambda i: i.toFloat()).merge(ee.ImageCollection([vazia])) \
            .reduce(redutor).rename(banda)

    def gfs_dia(d, L):
        criacao = ms(d) - (L - 1) * DIA_MS
        h0 = 24 * (L - 1)
        horas = [h for h in range(h0 + 1, h0 + 25) if h <= 120 or h % 3 == 0]
        horas_chuva = [h for h in horas if h % 6 == 0]
        dt = ee.Date(criacao)
        bruta = (ee.ImageCollection(GFS).filterDate(dt, dt.advance(1, 'hour'))
                 .filter(ee.Filter.eq('creation_time', criacao))
                 .filter(ee.Filter.gt('forecast_hours', h0)).filter(ee.Filter.lte('forecast_hours', h0 + 24)))
        bruta = ee.ImageCollection(bruta.distinct('forecast_hours'))
        chuva_b = bruta.filter(ee.Filter.inList('forecast_hours', horas_chuva))
        ok = bruta.size().eq(len(horas)).And(chuva_b.size().eq(len(horas_chuva)))
        rod = bruta.map(lambda i: i.resample('bilinear'))
        ch = chuva_b.map(lambda i: i.resample('bilinear'))
        cheia = ee.Image.cat([
            seguro(ch, 'total_precipitation_surface', ee.Reducer.sum()).max(0).rename('g_pr'),
            seguro(rod, 'temperature_2m_above_ground', ee.Reducer.max()).rename('g_tmax'),
            seguro(rod, 'temperature_2m_above_ground', ee.Reducer.min()).rename('g_tmin'),
            seguro(rod, 'relative_humidity_2m_above_ground', ee.Reducer.mean()).clamp(0, 100).rename('g_rh'),
            seguro(rod.map(u2_de), 'u2', ee.Reducer.mean()).rename('g_u2'),
            seguro(ch, 'downward_shortwave_radiation_flux', ee.Reducer.mean()).multiply(0.0864).max(0).rename('g_rs'),
        ]).toFloat()
        nomes = ['g_' + v for v in VARS]
        vazia = ee.Image.constant([0] * 6).rename(nomes).toFloat().updateMask(ee.Image.constant(0))
        return ee.Image(ee.Algorithms.If(ok, cheia, vazia)), ok

    arq_pts = os.path.join(CACHE, f'pontos_v2_{N_PONTOS}.pkl')
    candidatos = [arq_pts, os.path.join(BASE, 'cache_validacao_K9', f'pontos_v2_{N_PONTOS}.pkl'),
                  os.path.join(BASE, 'cache_validacao_K8', f'pontos_v2_{N_PONTOS}.pkl')]
    achou = next((c for c in candidatos if os.path.exists(c)), None)
    if achou:
        with open(achou, 'rb') as f:
            coords = pickle.load(f)
    else:
        validos = dia(BR_DWGD, '2001-01-15').select('pr').gt(-32768).unmask(0).gt(0)
        fc = gi(ee.Image.constant(1).updateMask(validos).updateMask(MASC_BR).sample(
            region=LIMITES, projection=PROJ_SAB, numPixels=int(N_PONTOS * 4), seed=23, geometries=True, tileScale=4),
            'sorteio dos pontos')
        coords = [f['geometry']['coordinates'] for f in fc['features']][:N_PONTOS]
    with open(arq_pts, 'wb') as f:
        pickle.dump(coords, f)
    PONTOS = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(c), {'pid': i}) for i, c in enumerate(coords)])
    log(f'   {len(coords)} pontos fixos entre os pixels com BR-DWGD (os mesmos da K8 e da K9)')

    def construir(lote):
        fcs = []
        for d, L in lote:
            g, ok = gfs_dia(d, L)
            img = ee.Image.cat([br_dia(d), g, ELEV])
            fcs.append(img.reduceRegions(collection=PONTOS, reducer=ee.Reducer.first(), crs=CRS,
                                         crsTransform=TRANSFORM, tileScale=4)
                       .map(lambda f: ee.Feature(None, f.toDictionary()).set({'dia': d, 'L': L, 'ok': ok})))
        return ee.FeatureCollection(fcs).flatten()

    itens = []
    for x in pd.date_range(INICIO, FIM, freq=f'{PASSO_DIAS}D'):
        for L in LEADS:
            rodada = (x - pd.Timedelta(days=L - 1)).strftime('%Y-%m-%d')
            if bloco_da_rodada(rodada):
                itens.append((x.strftime('%Y-%m-%d'), L))
    t0 = time.time()
    df = em_lotes('K9A', itens, construir, 6)
    log(f'   download: {(time.time() - t0) / 60:.1f} min')
    lat = {i: c[1] for i, c in enumerate(coords)}
    try:
        arq = os.path.join(CACHE, 'K9A_dados_brutos.parquet')
        df.to_parquet(arq, index=False)
        log(f'   dados brutos guardados em {arq}')
    except Exception as e:
        log(f'   (dados brutos não guardados em parquet: {str(e)[:80]})')
    return df, lat


# =========================================================================================
# PARTE 2. CONTAS (pandas; as mesmas fórmulas do motor V1.5)
# =========================================================================================
def es_de(T):
    return 0.6108 * np.exp(17.625 * T / (T + 243.04))


def eto_pm(tmax, tmin, rh, u2, rs, elev, lat_graus, doy):
    """Cópia da eto_penman_monteith do motor V1.5 (FAO-56), em numpy."""
    lat = np.radians(lat_graus)
    p = 101.3 * ((293.0 - 0.0065 * elev) / 293.0) ** 5.26
    gamma = 0.000665 * p
    tmed = (tmax + tmin) / 2
    es = (es_de(tmax) + es_de(tmin)) / 2
    ea = es * rh / 100
    vpd = np.maximum(es - ea, 0)
    dr = 1 + 0.033 * np.cos(2 * np.pi / 365 * doy)
    dec = 0.409 * np.sin(2 * np.pi / 365 * doy - 1.39)
    ws = np.arccos(np.clip(-np.tan(lat) * np.tan(dec), -1, 1))
    ra = (24 * 60 / np.pi) * 0.0820 * dr * (ws * np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.sin(ws))
    rso = (0.75 + 2e-5 * elev) * ra
    rs_rso = np.clip(rs / rso, 0, 1)
    rns = 0.77 * rs
    rnl = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * rs_rso - 0.35)
    rn = rns - np.maximum(rnl, 0)
    delta = 4283.58 * es_de(tmed) / (tmed + 243.04) ** 2
    num = 0.408 * delta * rn + gamma * (900 / (tmed + 273)) * u2 * vpd
    den = delta + gamma * (1 + 0.34 * u2)
    return np.maximum(num / den, 0)


def amplitude_minima(tmax, tmin):
    tmed = (tmax + tmin) / 2
    meia = np.maximum(tmax - tmin, AMPLITUDE_MIN_C) / 2
    return tmed + meia, tmed - meia


def qm(x, qg, qo):
    qg = np.maximum.accumulate(qg) + np.arange(len(qg)) * 1e-6
    return x + np.interp(x, qg, qo - qg, left=(qo - qg)[0], right=(qo - qg)[-1])


def estatisticas_treino(tr):
    g = tr.groupby(['pid', 'L', 'mes'])
    st = g.size().rename('n_treino').to_frame()
    for v in VARS:
        for f in ('o', 'g'):
            st[f'm{f}_{v}'] = g[f'{f}_{v}'].mean()
            st[f's{f}_{v}'] = g[f'{f}_{v}'].std()
    return st.reset_index()


def calibrar(x, v):
    """{método: série} para a variável v (x: linhas já unidas às estatísticas de treino)."""
    g, mo, mg = x[f'g_{v}'], x[f'mo_{v}'], x[f'mg_{v}']
    so, sg = x[f'so_{v}'], x[f'sg_{v}']
    razao_s = (so / sg.clip(lower=1e-3)).clip(RAZAO_DESVIO_MIN, RAZAO_DESVIO_MAX)
    out = {'GFS sem correção': g}
    if v == 'pr':
        out[MOTOR['pr']] = g * ((mo + K_CHUVA_MM) / (mg + K_CHUVA_MM)).clip(upper=FATOR_MAX)
        out['fator V1.0 (sem o +0,1), teto 5'] = g * (mo / mg.clip(lower=1e-3)).clip(upper=FATOR_MAX)
        out['fator limitado a [0,5; 2]'] = g * ((mo + K_CHUVA_MM) / (mg + K_CHUVA_MM)).clip(0.5, 2.0)
    elif v in ('tmax', 'tmin'):
        out['aditiva'] = g + (mo - mg)
        out[MOTOR[v]] = mo + (g - mg) * razao_s
    elif v == 'rh':
        out[ANTES_K9A['rh']] = (g + (mo - mg)).clip(0, 100)
        out[MOTOR['rh']] = (mo + (g - mg) * razao_s).clip(0, 100)
        out['fator multiplicativo [0,5; 2]'] = (g * (mo / mg.clip(lower=1e-3)).clip(0.5, 2.0)).clip(0, 100)
    elif v == 'u2':
        out[MOTOR['u2']] = g * (mo / mg.clip(lower=1e-3)).clip(FATOR_MIN_UV_RS, FATOR_MAX_UV_RS)
        out['aditiva'] = (g + (mo - mg)).clip(lower=0)
        out['escala de variância'] = (mo + (g - mg) * razao_s).clip(lower=0)
    else:   # rs
        out[ANTES_K9A['rs']] = g * (mo / mg.clip(lower=1e-3)).clip(FATOR_MIN_UV_RS, FATOR_MAX_UV_RS)
        out['aditiva'] = (g + (mo - mg)).clip(lower=0)
        out[MOTOR['rs']] = (mo + (g - mg) * razao_s).clip(lower=0)
    return out


def quantis_por_grupo(tr, te, v):
    saida = pd.Series(np.nan, index=te.index)
    trg = {k: g[[f'g_{v}', f'o_{v}']].to_numpy() for k, g in tr.groupby(['pid', 'L', 'mes'])}
    for k, g in te.groupby(['pid', 'L', 'mes']):
        t = trg.get(k)
        if t is None or len(t) < MIN_TREINO:
            continue
        y = qm(g[f'g_{v}'].values, np.percentile(t[:, 0], PERCENTIS), np.percentile(t[:, 1], PERCENTIS))
        if v == 'pr':
            y = np.where(g[f'g_{v}'].values <= 0, 0.0, y)
        lim = {'pr': (0, None), 'rh': (0, 100), 'u2': (0, None), 'rs': (0, None)}.get(v)
        saida.loc[g.index] = np.clip(y, lim[0], lim[1]) if lim else y
    return saida


def ets(prev, obs, limiar):
    a = ((prev >= limiar) & (obs >= limiar)).sum()
    b = ((prev >= limiar) & (obs < limiar)).sum()
    c = ((prev < limiar) & (obs >= limiar)).sum()
    n = len(obs)
    ar = (a + b) * (a + c) / n if n else 0
    den = a + b + c - ar
    return (a - ar) / den if den else np.nan


def metricas(x, o, v):
    e = x - o
    lin = {'n': int(len(o)), 'vies': e.mean(), 'MAE': e.abs().mean(), 'RMSE': np.sqrt((e ** 2).mean()),
           'corr': np.corrcoef(x, o)[0, 1] if len(o) > 2 else np.nan}
    if v in ('pr', 'eto', 'rs', 'u2'):
        lin['razao_volume'] = x.sum() / o.sum() if o.sum() else np.nan
    if v == 'pr':
        for lim in (1, 10, 30):
            lin[f'pct_{lim}mm_prev'] = 100 * (x >= lim).mean()
            lin[f'pct_{lim}mm_obs'] = 100 * (o >= lim).mean()
        lin['ETS_1mm'] = ets(x, o, 1.0)
        lin['ETS_10mm'] = ets(x, o, 10.0)
    elif v == 'tmax':
        lin['pct35_prev'], lin['pct35_obs'] = 100 * (x > 35).mean(), 100 * (o > 35).mean()
    elif v == 'tmin':
        lin['pct_geada2_prev'], lin['pct_geada2_obs'] = 100 * (x <= 2).mean(), 100 * (o <= 2).mean()
    elif v == 'rh':
        lin['pct_UR30_prev'], lin['pct_UR30_obs'] = 100 * (x < 30).mean(), 100 * (o < 30).mean()
    elif v == 'u2':
        lin['pct_4ms_prev'], lin['pct_4ms_obs'] = 100 * (x > 4).mean(), 100 * (o > 4).mean()
    elif v == 'eto':
        lin['pct_6mm_prev'], lin['pct_6mm_obs'] = 100 * (x > 6).mean(), 100 * (o > 6).mean()
    return lin


def ic_dif_mae(a, b, o, dias, n_boot=N_BOOT, semente=9):
    """Diferença de MAE (a - b) e IC 95% por bootstrap de dias. Negativo: a erra menos que b."""
    d = ((a - o).abs() - (b - o).abs()).groupby(np.asarray(dias)).agg(['sum', 'count'])
    s, c = d['sum'].values, d['count'].values
    rng = np.random.default_rng(semente)
    idx = rng.integers(0, len(s), size=(n_boot, len(s)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return s.sum() / c.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def preparar(df, lat):
    df = df.copy()
    for c in ['L', 'pid', 'ok', 'elev'] + [f'{f}_{v}' for f in ('o', 'g') for v in VARS] + ['o_eto']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    n0 = len(df)
    df = df[df['ok'] > 0].dropna(subset=[f'{f}_{v}' for f in ('o', 'g') for v in VARS] + ['o_eto', 'elev'])
    df['pid'], df['L'] = df['pid'].astype(int), df['L'].astype(int)
    df['data'] = pd.to_datetime(df['dia'])
    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month
    df['doy'] = df['data'].dt.dayofyear
    df['lat'] = df['pid'].map(lat).astype(float)
    df['rodada'] = (df['data'] - pd.to_timedelta(df['L'] - 1, unit='D')).dt.strftime('%Y-%m-%d')
    df['bloco'] = df['rodada'].map(bloco_da_rodada)
    df = df[df['bloco'].notna()]
    df['estacao'] = np.where(df['mes'].isin([6, 7, 8, 9]), 'seca (jun-set)', 'demais meses')
    log(f'   {len(df):,} pares ponto-dia-prazo válidos de {n0:,} baixados')
    cob = df.groupby(['bloco', 'ano', 'L']).size().unstack('L')
    tabela(cob, 'Pares válidos por bloco (versão do GFS), ano e prazo:')
    salvar(cob, 'K9A_cobertura.csv')
    return df.reset_index(drop=True)


def prever(tr, te, com_qm=False, com_fator_eto=False):
    """Previsões corrigidas do teste com o treino dado. Devolve (r, P, E): r = linhas do teste com
    treino suficiente; P[var][método]; E[combinação] = ETo."""
    st = estatisticas_treino(tr)
    st = st[st['n_treino'] >= MIN_TREINO]
    r = te.merge(st, on=['pid', 'L', 'mes'], how='inner')
    P = {v: calibrar(r, v) for v in VARS}
    if com_qm:
        for v in VARS:
            P[v]['mapeamento de quantis'] = quantis_por_grupo(tr, r, v)
    for nome in ('aditiva', MOTOR['tmax']):           # Tmax/Tmin gravadas com a amplitude mínima
        P['tmax'][nome], P['tmin'][nome] = amplitude_minima(P['tmax'][nome], P['tmin'][nome])

    def eto(tx, tn, rh, u2, rs):
        return pd.Series(eto_pm(np.asarray(tx), np.asarray(tn), np.asarray(rh), np.asarray(u2), np.asarray(rs),
                                r['elev'].values, r['lat'].values, r['doy'].values), index=r.index)

    tx, tn = P['tmax'][MOTOR['tmax']], P['tmin'][MOTOR['tmin']]
    rh_m, rh_a = P['rh'][MOTOR['rh']], P['rh'][ANTES_K9A['rh']]
    u2_m = P['u2'][MOTOR['u2']]
    rs_m, rs_a = P['rs'][MOTOR['rs']], P['rs'][ANTES_K9A['rs']]
    gx, gn = amplitude_minima(r['g_tmax'], r['g_tmin'])
    E = {'GFS sem correção': eto(gx, gn, r['g_rh'], r['g_u2'], r['g_rs']),
         'motor V1.5': eto(tx, tn, rh_m, u2_m, rs_m),
         'motor com a UR de antes da K9A': eto(tx, tn, rh_a, u2_m, rs_m),
         'motor com a radiação de antes da K9A': eto(tx, tn, rh_m, u2_m, rs_a),
         'motor antes da K9A (UR e radiação)': eto(tx, tn, rh_a, u2_m, rs_a),
         'motor com Tmax/Tmin aditivas': eto(P['tmax']['aditiva'], P['tmin']['aditiva'], rh_m, u2_m, rs_m)}
    if com_fator_eto:
        trs = tr.merge(st, on=['pid', 'L', 'mes'], how='inner')
        Pt = {v: calibrar(trs, v) for v in VARS}
        txt, tnt = amplitude_minima(Pt['tmax'][MOTOR['tmax']], Pt['tmin'][MOTOR['tmin']])
        e_tr = eto_pm(np.asarray(txt), np.asarray(tnt), Pt['rh'][MOTOR['rh']].values, Pt['u2'][MOTOR['u2']].values,
                      Pt['rs'][MOTOR['rs']].values, trs['elev'].values, trs['lat'].values, trs['doy'].values)
        f = (pd.DataFrame({'pid': trs['pid'], 'L': trs['L'], 'mes': trs['mes'], 'o': trs['o_eto'], 'm': e_tr})
             .groupby(['pid', 'L', 'mes']).sum())
        f = (f['o'] / f['m'].clip(lower=1e-3)).clip(0.5, 2.0).rename('f').reset_index()
        fr = r[['pid', 'L', 'mes']].merge(f, on=['pid', 'L', 'mes'], how='left')['f'].fillna(1.0).values
        E['motor + fator direto na ETo [0,5; 2]'] = E['motor V1.5'] * fr
    P['eto'] = E
    return r, P


def observado(r, v):
    return r['o_eto'] if v == 'eto' else r[f'o_{v}']


def erro_total_mensal(x, o, r):
    """Erro do total mensal por ponto e prazo, em % do total observado (o que pesa nas séries mensais)."""
    m = pd.DataFrame({'pid': r['pid'], 'L': r['L'], 'ano': r['ano'], 'mes': r['mes'], 'x': x, 'o': o}) \
        .groupby(['pid', 'L', 'ano', 'mes']).sum()
    return 100 * (m['x'] - m['o']).abs().sum() / m['o'].sum()


# ------------------------------------- TESTE A -----------------------------------------
def teste_oficial(df):
    log('\n' + '=' * 100)
    log('TESTE A (OFICIAL): GFS v16, treino até 31/12/2024, teste em 2025 inteiro')
    log('=' * 100)
    b = df[df['bloco'] == 'GFS v16']
    tr, te = b[b['data'] <= pd.Timestamp(FIM_TREINO_OFICIAL)], b[b['data'] > pd.Timestamp(FIM_TREINO_OFICIAL)]
    r, P = prever(tr, te, com_qm=True, com_fator_eto=True)
    st = estatisticas_treino(tr)
    log(f'   {len(r):,} previsões no teste; treino mediano de {int(st["n_treino"].median())} dias por ponto, prazo e mês')
    todas, comp = [], []
    for v in VARS + ['eto']:
        o = observado(r, v)
        linhas = []
        for nome, x in P[v].items():
            ok = x.notna()
            grupos = [('todos', ok)] + [(L, ok & (r['L'] == L)) for L in LEADS] + \
                     [(e, ok & (r['estacao'] == e)) for e in ('seca (jun-set)', 'demais meses')]
            for rot, idx in grupos:
                lin = {'var': v, 'prazo': rot, 'metodo': nome, **metricas(x[idx], o[idx], v)}
                if v in ('pr', 'eto'):
                    lin['erro_total_mensal_pct'] = erro_total_mensal(x[idx], o[idx], r[idx])
                linhas.append(lin)
        t = pd.DataFrame(linhas)
        todas.append(t)
        tabela(t.set_index(['prazo', 'metodo']).drop(columns='var').round(3),
               f'A - {NOMES[v]}: viés, MAE e RMSE na unidade da variável; frequências em % dos ponto-dias:')
        # comparações com o motor (mesmas linhas para todos os métodos)
        comum = pd.concat([x.notna() for x in P[v].values()], axis=1).all(axis=1)
        nm = MOTOR[v]
        xm, oo, dd = P[v][nm][comum], o[comum], r.loc[comum, 'dia']
        mm = metricas(xm, oo, v)
        for nome, x in P[v].items():
            if nome == nm or nome.startswith('controle'):
                continue
            xa = x[comum]
            d, lo, hi = ic_dif_mae(xa, xm, oo, dd)
            ma = metricas(xa, oo, v)
            piora_vol = 'razao_volume' in ma and abs(ma['razao_volume'] - 1) > abs(mm['razao_volume'] - 1) + 0.05
            piora_ets = v == 'pr' and ma['ETS_1mm'] < mm['ETS_1mm'] - 0.01
            if v in ('pr', 'eto'):
                em_m, em_a = erro_total_mensal(xm, oo, r[comum]), erro_total_mensal(xa, oo, r[comum])
                piora_mensal = em_a > em_m + 1.0
            else:
                em_m = em_a = np.nan
                piora_mensal = False
            comp.append({'var': v, 'metodo': nome, 'MAE_motor': mm['MAE'], 'MAE_metodo': ma['MAE'],
                         'dif': d, 'dif_pct': 100 * d / mm['MAE'], 'IC95_inf': lo, 'IC95_sup': hi,
                         'vol_motor': mm.get('razao_volume'), 'vol_metodo': ma.get('razao_volume'),
                         'ETS1_motor': mm.get('ETS_1mm'), 'ETS1_metodo': ma.get('ETS_1mm'),
                         'erro_mensal_motor': em_m, 'erro_mensal_metodo': em_a,
                         'passa_A': bool(d <= -GANHO_MIN * mm['MAE'] and hi < 0 and not piora_vol and not piora_ets
                                         and not piora_mensal)})
    salvar(pd.concat(todas, ignore_index=True), 'K9A_A_metricas.csv', index=False)
    comp = pd.DataFrame(comp)
    salvar(comp, 'K9A_A_comparacoes.csv', index=False)
    tabela(comp.set_index(['var', 'metodo']).round(3), 'A - cada método contra o do motor (dif < 0: erra menos que o motor):')

    # ETo: controle da fórmula e peso das entradas
    rr = r
    ctl = eto_pm(rr['o_tmax'].values, rr['o_tmin'].values, rr['o_rh'].values, rr['o_u2'].values, rr['o_rs'].values,
                 rr['elev'].values, rr['lat'].values, rr['doy'].values)
    m_ctl = metricas(pd.Series(ctl, index=rr.index), rr['o_eto'], 'eto')
    log(f"\n   CONTROLE DA ETo (Penman do motor com as entradas do BR-DWGD x ETo do BR-DWGD): viés {m_ctl['vies']:+.3f}, "
        f"MAE {m_ctl['MAE']:.3f} mm/dia, volume {m_ctl['razao_volume']:.3f}, correlação {m_ctl['corr']:.3f}")
    return comp


# ------------------------------------- TESTES B e C ------------------------------------
def cada_ano_de_fora(df):
    log('\n' + '=' * 100)
    log('TESTES B (v16) e C (versões antigas): cada ano testado com o treino nos outros anos do mesmo bloco')
    log('=' * 100)
    linhas = []
    for bloco, _, _ in BLOCOS:
        b = df[df['bloco'] == bloco]
        anos = [a for a, n in b.groupby('ano').size().items() if n >= MIN_TESTE_ANO]
        if len(anos) < 2:
            log(f'   {bloco}: menos de 2 anos com dados suficientes; fica de fora')
            continue
        for a in anos:
            t0 = time.time()
            # o mapeamento de quantis entra no v16 (que decide); nas versões antigas fica de fora para poupar tempo
            r, P = prever(b[b['ano'] != a], b[b['ano'] == a], com_qm=(bloco == 'GFS v16'))
            if not len(r):
                continue
            for v in VARS + ['eto']:
                o = observado(r, v)
                for nome, x in P[v].items():
                    m = metricas(x, o, v)
                    lin = {'bloco': bloco, 'ano': a, 'var': v, 'metodo': nome, 'n': m['n'], 'MAE': m['MAE'],
                           'vies': m['vies'], 'vol': m.get('razao_volume'), 'ETS1': m.get('ETS_1mm'),
                           'ETS10': m.get('ETS_10mm')}
                    if v in ('pr', 'eto'):
                        lin['erro_total_mensal_pct'] = erro_total_mensal(x, o, r)
                    linhas.append(lin)
            log(f'   {bloco} {a}: {len(r):,} previsões ({time.time() - t0:.0f} s)')
    cv = pd.DataFrame(linhas)
    salvar(cv, 'K9A_BC_cada_ano.csv', index=False)
    for v in VARS + ['eto']:
        t = cv[cv['var'] == v].pivot_table(index=['bloco', 'metodo'], columns='ano', values='MAE').round(3)
        tabela(t, f'B/C - {NOMES[v]}: MAE de cada ano testado (treino nos outros anos do bloco):')
        if v in ('pr', 'eto', 'rs', 'u2'):
            t = cv[cv['var'] == v].pivot_table(index=['bloco', 'metodo'], columns='ano', values='vol').round(3)
            tabela(t, f'B/C - {NOMES[v]}: razão de volume de cada ano:')
    # vitórias contra o motor
    rob = []
    for (bloco, v, a), g in cv.groupby(['bloco', 'var', 'ano']):
        mae_m = g.loc[g['metodo'] == MOTOR[v], 'MAE']
        if mae_m.empty:
            continue
        for _, x in g.iterrows():
            if x['metodo'] != MOTOR[v]:
                rob.append({'bloco': bloco, 'var': v, 'metodo': x['metodo'], 'ano': a,
                            'vence_motor': bool(x['MAE'] < mae_m.iloc[0]),
                            'dif_pct': 100 * (x['MAE'] - mae_m.iloc[0]) / mae_m.iloc[0]})
    rob = pd.DataFrame(rob)
    res = rob.groupby(['var', 'metodo', 'bloco']).agg(anos=('ano', 'size'), vence=('vence_motor', 'sum'),
                                                      dif_media_pct=('dif_pct', 'mean'),
                                                      dif_pior_ano_pct=('dif_pct', 'max')).reset_index()
    salvar(res, 'K9A_BC_vitorias.csv', index=False)
    tabela(res.set_index(['var', 'metodo', 'bloco']).round(2),
           'B/C - em quantos anos cada método errou menos que o do motor (dif < 0: erra menos):')
    return cv, res


def decidir(comp, res):
    log('\n' + '=' * 100)
    log('RESULTADO FINAL K9A (regra definida antes de rodar)')
    log('=' * 100)
    final = []
    for v in VARS + ['eto']:
        c = comp[comp['var'] == v]
        log(f'\n{NOMES[v]}  [motor: {MOTOR[v]}]')
        indicados = []
        for _, x in c.sort_values('dif').iterrows():
            rb = res[(res['var'] == v) & (res['metodo'] == x['metodo'])]
            v16 = rb[rb['bloco'] == 'GFS v16']
            antigos = rb[rb['bloco'] != 'GFS v16']
            todos_v16 = bool(len(v16) and v16['vence'].iloc[0] == v16['anos'].iloc[0])
            txt_v16 = f"{int(v16['vence'].iloc[0])} de {int(v16['anos'].iloc[0])} anos" if len(v16) else 'n/d'
            txt_ant = (f"{int(antigos['vence'].sum())} de {int(antigos['anos'].sum())} anos" if len(antigos) else 'n/d')
            passa = bool(x['passa_A']) and todos_v16
            if passa:
                indicados.append(x['metodo'])
            vol = (f"; volume {x['vol_motor']:.3f} -> {x['vol_metodo']:.3f}" if pd.notna(x['vol_metodo']) else '')
            if pd.notna(x['erro_mensal_metodo']):
                vol += f"; erro do total mensal {x['erro_mensal_motor']:.1f}% -> {x['erro_mensal_metodo']:.1f}%"
            if pd.notna(x['ETS1_metodo']):
                vol += f"; ETS 1 mm {x['ETS1_motor']:.3f} -> {x['ETS1_metodo']:.3f}"
            log(f"   {x['metodo']}: MAE {x['MAE_metodo']:.3f} x motor {x['MAE_motor']:.3f} ({x['dif_pct']:+.1f}%, IC "
                f"{x['IC95_inf']:+.3f} a {x['IC95_sup']:+.3f}){vol} | teste A: {'passa' if x['passa_A'] else 'não passa'} | "
                f"vence o motor no v16 em {txt_v16}; nas versões antigas em {txt_ant}{'  ✅ INDICADO' if passa else ''}")
            final.append({'var': NOMES[v], 'metodo_motor': MOTOR[v], 'metodo': x['metodo'], 'dif_pct_A': x['dif_pct'],
                          'IC95_inf': x['IC95_inf'], 'IC95_sup': x['IC95_sup'], 'passa_A': x['passa_A'],
                          'vence_v16': txt_v16, 'vence_antigas': txt_ant, 'indicado': passa})
        if indicados:
            melhor = c[c['metodo'].isin(indicados)].sort_values('dif').iloc[0]['metodo']
            log(f'   ➜ TROCAR por: {melhor}')
        else:
            log('   ➜ MANTER o método do motor')
    f = pd.DataFrame(final)
    salvar(f, 'K9A_RESULTADO_FINAL.csv', index=False)
    log('\n   Chuva: o dia do BR-DWGD vai das 12 às 12 UTC e o do GFS das 00 às 24 UTC (Parte A, nota 10); essa defasagem '
        'pesa em todos os métodos. O MAE diário favorece previsões mais secas: leia junto o volume, o ETS e o erro do '
        'total mensal (tabelas A e B).')
    return f


# =========================================================================================
# EXECUÇÃO
# =========================================================================================
log('=' * 100)
log(f'K9A - VALIDAÇÃO AMPLIADA, TODAS AS VARIÁVEIS (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
log('=' * 100)
if LOCAL:
    with open(LOCAL, 'rb') as f:
        DF, LAT = pickle.load(f)
    log('   (teste offline com dados locais)')
else:
    DF, LAT = baixar()
DF = preparar(DF, LAT)
COMP = teste_oficial(DF)
CV, RES = cada_ano_de_fora(DF)
FINAL = decidir(COMP, RES)
log('\nNada foi gravado no Earth Engine.')
z = shutil.make_archive(PASTA, 'zip', PASTA)
log(f'📦 {z}')
if not LOCAL:
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        log('   (baixe pelo painel Arquivos do Colab)')
