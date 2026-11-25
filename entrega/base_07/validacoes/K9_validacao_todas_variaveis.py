# =========================================================================================
# K9 - VALIDAÇÃO FORA DA AMOSTRA DE TODAS AS VARIÁVEIS DA PREVISÃO GFS (SOMENTE LEITURA)
# [Registro] Versão executada em 20/10/2026 (zip validacao_K9_20261020_1758). O "motor V1.5" comparado aqui é o de
# antes da revisão K9A (UR aditiva e radiação com fator). Substituída pela K9A (validacoes/K9A_validacao_ampliada.py),
# que usa todos os dias de 2015 a 2025 e já compara com o motor atual. Guardada só para rastreabilidade.
# Pergunta: as correções que o motor V1.5 aplica nos dias de previsão melhoram o GFS, em dados que o
# treino não viu? Existe outra correção claramente melhor?
#   - Variáveis: chuva, Tmax, Tmin, umidade relativa, vento a 2 m, radiação solar e ETo (Penman-Monteith
#     calculado com as entradas corrigidas, comparado com a ETo do BR-DWGD)
#   - GFS v16 composto exatamente como a matriz V2.1 e o motor V1.5: rodada 00Z, uma saída por hora de
#     previsão, reamostragem bilinear por imagem, janela (00Z, 24Z] do dia; Tmax/Tmin pela temperatura
#     horária; UR e vento pela média das saídas; chuva e radiação pelos 4 blocos de 6 h
#   - Prazos 1, 3, 8 e 13 dias (um de cada faixa), 1 dia a cada 3, de 08/04/2021 a 31/12/2025
#   - Os mesmos 300 pontos da K8 (mesmo sorteio, semente 23)
#   - TREINO: 08/04/2021 a 31/12/2024, estatísticas por ponto, prazo e MÊS (como a matriz V2.1).
#     TESTE: 2025 inteiro, que o treino não viu
#   - Métodos por variável: GFS bruto | o que o motor V1.5 faz | alternativas (aditiva, fator,
#     escala de variância, mapeamento de quantis, conforme a variável)
#   - ETo: GFS bruto | motor V1.5 | motor com Tmax/Tmin aditivas | motor + fator direto na ETo |
#     controle: Penman com as entradas do próprio BR-DWGD (mede a diferença de fórmula)
#   - Incerteza: IC 95% por bootstrap de dias (os 300 pontos de um mesmo dia não são independentes)
# Nada é gravado no Earth Engine. RODE SOZINHA: nenhum outro script do projeto pode estar rodando ao
# mesmo tempo (o Earth Engine recusa pedidos por excesso de cálculos simultâneos, erro 429).
# COMO RODAR: cole inteiro numa célula do Colab e rode. Leva de 15 a 40 min. O log mostra o tempo
# restante; se parar, rode de novo (os lotes já baixados ficam no cache). No final baixa um zip.
# =========================================================================================
import os, shutil, time, pickle, hashlib, warnings
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# ------------------------------- CONFIGURAÇÃO -------------------------------------------
PROJETO = 'clima-492922'
N_PONTOS = 300
PASSO_DIAS = 3
LEADS = [1, 3, 8, 13]
INICIO, FIM_TREINO, FIM = '2021-04-08', '2024-12-31', '2025-12-31'
PERCENTIS = [5, 10, 25, 50, 75, 90, 95]
USAR_DRIVE = False
N_BOOT = 1000
MIN_TREINO = 20            # mínimo de dias de treino por ponto, prazo e mês
# Constantes do motor V1.5 (05b), copiadas para reproduzir as mesmas contas
K_CHUVA_MM, FATOR_MAX = 0.1, 5.0
FATOR_MIN_UV_RS, FATOR_MAX_UV_RS = 0.5, 2.0
RAZAO_DESVIO_MIN, RAZAO_DESVIO_MAX = 0.5, 2.0
AMPLITUDE_MIN_C = 1.0
# Regra da indicação: uma alternativa só é indicada se reduzir o MAE do motor em 3% ou mais, com o
# IC 95% inteiro abaixo de zero, sem piorar o volume (razão) em mais de 0,05 nem o ETS da chuva em mais de 0,01
GANHO_MIN = 0.03
# -----------------------------------------------------------------------------------------

BR_DWGD, GFS = 'projects/ee-alexandrexavier/assets/BR-DWGD', 'NOAA/GFS0P25'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
DIA_MS = 86400000
VARS = ['pr', 'tmax', 'tmin', 'rh', 'u2', 'rs']
NOMES = {'pr': 'Chuva (mm/dia)', 'tmax': 'Tmax (°C)', 'tmin': 'Tmin (°C)', 'rh': 'Umidade relativa (%)',
         'u2': 'Vento a 2 m (m/s)', 'rs': 'Radiação solar (MJ/m²/dia)', 'eto': 'ETo (mm/dia)'}

AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'validacao_K9_{AGORA:%Y%m%d_%H%M}')
CACHE = os.path.join(BASE, 'cache_validacao_K9')
LOCAL = os.environ.get('K9_DADOS_LOCAIS')       # só para o teste offline (sem Earth Engine)
if USAR_DRIVE and not LOCAL:
    from google.colab import drive
    drive.mount('/content/drive')
    CACHE = '/content/drive/MyDrive/cache_validacao_K9'
os.makedirs(PASTA, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)
LOG = os.path.join(PASTA, 'LOG_K9.txt')


def log(*p):
    t = ' '.join(str(x) for x in p)
    print(t, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(t + '\n')


def tabela(df, titulo):
    log(f'\n   {titulo}')
    with pd.option_context('display.width', 250, 'display.max_columns', 40, 'display.max_rows', 300):
        for linha in df.to_string().splitlines():
            log('   ' + linha)


def salvar(df, nome, index=True):
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', encoding='utf-8-sig', index=index)


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
    """Pede um lote. Se o Earth Engine recusar por peso ou por excesso de cálculos simultâneos,
    divide o lote; um item sozinho espera 5 min e tenta de novo."""
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
    log(f'   {nome}: {len(itens)} itens em {len(lotes)} lotes')
    for k, lote in enumerate(lotes):
        arq = os.path.join(CACHE, f'{nome}_{chave}_{k:04d}.pkl')
        if os.path.exists(arq):
            with open(arq, 'rb') as f:
                partes.append(pickle.load(f))
            continue
        df = pd.DataFrame(buscar(lote, construir, f'{nome} lote {k + 1}/{len(lotes)}'))
        with open(arq, 'wb') as f:
            pickle.dump(df, f)
        partes.append(df)
        feitos += 1
        if feitos in (1, 3) or feitos % 10 == 0 or k + 1 == len(lotes):
            dec = time.time() - t0
            log(f'   … lote {k + 1}/{len(lotes)} | {dec / 60:.1f} min | faltam ~{dec / feitos * (len(lotes) - k - 1) / 60:.0f} min')
    partes = [p for p in partes if len(p)]
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def baixar():
    """Devolve (df, lat_por_ponto). df: uma linha por ponto, dia e prazo, com o BR-DWGD (o_*) e o GFS (g_*)."""
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
    ELEV = ee.Image('USGS/SRTMGL1_003').rename('elev').toFloat()     # a mesma elevação do Penman do motor

    def dia(col, d):
        return ee.Image(ee.ImageCollection(col).filterDate(d, ee.Date(d).advance(1, 'day')).first())

    def ms(d):
        return int(pd.Timestamp(d).value // 10 ** 6)

    def br_dia(d):
        """BR-DWGD com escala e offset oficiais (os mesmos do 03, do motor e do 01)."""
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
        """Composição que não falha com a coleção vazia (a mesma ideia do composto_seguro do 03): uma imagem
        totalmente mascarada entra na coleção e não muda a soma, a média, o máximo nem o mínimo."""
        vazia = ee.Image.constant(0).rename(banda).toFloat().updateMask(ee.Image.constant(0))
        return col.select(banda).map(lambda i: i.toFloat()).merge(ee.ImageCollection([vazia])) \
            .reduce(redutor).rename(banda)

    def gfs_dia(d, L):
        """Previsão do dia d feita L dias antes (rodada 00Z de d-(L-1)), com as contas da matriz V2.1 e do motor."""
        criacao = ms(d) - (L - 1) * DIA_MS
        h0 = 24 * (L - 1)
        horas = [h for h in range(h0 + 1, h0 + 25) if h <= 120 or h % 3 == 0]
        horas_chuva = [h for h in horas if h % 6 == 0]
        dt = ee.Date(criacao)
        bruta = (ee.ImageCollection(GFS).filterDate(dt, dt.advance(1, 'hour'))
                 .filter(ee.Filter.eq('creation_time', criacao))
                 .filter(ee.Filter.gt('forecast_hours', h0)).filter(ee.Filter.lte('forecast_hours', h0 + 24)))
        bruta = ee.ImageCollection(bruta.distinct('forecast_hours'))      # uma saída por hora, como o motor
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

    # Pontos: o mesmo sorteio da K8 (semente 23)
    arq_pts = os.path.join(CACHE, f'pontos_v2_{N_PONTOS}.pkl')
    arq_k8 = os.path.join(BASE, 'cache_validacao_K8', f'pontos_v2_{N_PONTOS}.pkl')
    if os.path.exists(arq_pts):
        with open(arq_pts, 'rb') as f:
            coords = pickle.load(f)
    elif os.path.exists(arq_k8):
        with open(arq_k8, 'rb') as f:
            coords = pickle.load(f)
        log('   pontos lidos do cache da K8')
    else:
        validos = dia(BR_DWGD, '2001-01-15').select('pr').gt(-32768).unmask(0).gt(0)
        fc = gi(ee.Image.constant(1).updateMask(validos).updateMask(MASC_BR).sample(
            region=LIMITES, projection=PROJ_SAB, numPixels=int(N_PONTOS * 4), seed=23, geometries=True, tileScale=4),
            'sorteio dos pontos')
        coords = [f['geometry']['coordinates'] for f in fc['features']][:N_PONTOS]
    with open(arq_pts, 'wb') as f:
        pickle.dump(coords, f)
    PONTOS = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(c), {'pid': i}) for i, c in enumerate(coords)])
    log(f'   {len(coords)} pontos fixos entre os pixels com BR-DWGD')

    def construir(lote):
        fcs = []
        for d, L in lote:
            g, ok = gfs_dia(d, L)
            img = ee.Image.cat([br_dia(d), g, ELEV])
            fcs.append(img.reduceRegions(collection=PONTOS, reducer=ee.Reducer.first(), crs=CRS,
                                         crsTransform=TRANSFORM, tileScale=4)
                       .map(lambda f: ee.Feature(None, f.toDictionary()).set({'dia': d, 'L': L, 'ok': ok})))
        return ee.FeatureCollection(fcs).flatten()

    dias = [x.strftime('%Y-%m-%d') for x in pd.date_range(INICIO, FIM, freq=f'{PASSO_DIAS}D')]
    itens = [(d, L) for d in dias for L in LEADS]
    t0 = time.time()
    df = em_lotes('K9', itens, construir, 6)
    log(f'   download: {(time.time() - t0) / 60:.1f} min')
    lat = {i: c[1] for i, c in enumerate(coords)}
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
    """Regra do motor: preserva a média e garante Tmax - Tmin >= AMPLITUDE_MIN_C."""
    tmed = (tmax + tmin) / 2
    meia = np.maximum(tmax - tmin, AMPLITUDE_MIN_C) / 2
    return tmed + meia, tmed - meia


def qm(x, qg, qo):
    """Mapeamento de quantis linear por partes (o mesmo da K8)."""
    qg = np.maximum.accumulate(qg) + np.arange(len(qg)) * 1e-6
    return x + np.interp(x, qg, qo - qg, left=(qo - qg)[0], right=(qo - qg)[-1])


def estatisticas_treino(tr):
    """Média, desvio e percentis por ponto, prazo e mês, para o BR-DWGD (o_) e o GFS (g_)."""
    g = tr.groupby(['pid', 'L', 'mes'])
    st = g.size().rename('n_treino').to_frame()
    for v in VARS:
        for f in ('o', 'g'):
            st[f'm{f}_{v}'] = g[f'{f}_{v}'].mean()
            st[f's{f}_{v}'] = g[f'{f}_{v}'].std()
    return st.reset_index()


def calibrar(x, st, v):
    """Devolve {método: série} para a variável v. x: DataFrame com g_{v}, já unido às estatísticas."""
    g, mo, mg = x[f'g_{v}'], x[f'mo_{v}'], x[f'mg_{v}']
    so, sg = x[f'so_{v}'], x[f'sg_{v}']
    razao_s = (so / sg.clip(lower=1e-3)).clip(RAZAO_DESVIO_MIN, RAZAO_DESVIO_MAX)
    out = {'GFS bruto': g}
    if v == 'pr':
        out['motor V1.5: fator (m+0,1)/(m+0,1), teto 5'] = g * ((mo + K_CHUVA_MM) / (mg + K_CHUVA_MM)).clip(upper=FATOR_MAX)
        out['fator V1.0 (sem o +0,1), teto 5'] = g * (mo / mg.clip(lower=1e-3)).clip(upper=FATOR_MAX)
        out['fator limitado a [0,5; 2]'] = g * ((mo + K_CHUVA_MM) / (mg + K_CHUVA_MM)).clip(0.5, 2.0)
    elif v in ('tmax', 'tmin'):
        out['aditiva'] = g + (mo - mg)
        out['motor V1.5: escala de variância'] = mo + (g - mg) * razao_s
    elif v == 'rh':
        out['motor V1.5: aditiva'] = (g + (mo - mg)).clip(0, 100)
        out['escala de variância'] = (mo + (g - mg) * razao_s).clip(0, 100)
        out['fator multiplicativo [0,5; 2]'] = (g * (mo / mg.clip(lower=1e-3)).clip(0.5, 2.0)).clip(0, 100)
    else:   # u2, rs
        out['motor V1.5: fator limitado a [0,5; 2]'] = g * (mo / mg.clip(lower=1e-3)).clip(FATOR_MIN_UV_RS, FATOR_MAX_UV_RS)
        out['aditiva'] = (g + (mo - mg)).clip(lower=0)
        out['escala de variância'] = (mo + (g - mg) * razao_s).clip(lower=0)
    return out


def metodo_motor(v):
    return {'pr': 'motor V1.5: fator (m+0,1)/(m+0,1), teto 5', 'tmax': 'motor V1.5: escala de variância',
            'tmin': 'motor V1.5: escala de variância', 'rh': 'motor V1.5: aditiva',
            'u2': 'motor V1.5: fator limitado a [0,5; 2]', 'rs': 'motor V1.5: fator limitado a [0,5; 2]',
            'eto': 'motor V1.5'}[v]


def quantis_por_grupo(tr, te, v):
    """Mapeamento de quantis por ponto, prazo e mês (alternativa; não é usado pelo motor)."""
    saida = pd.Series(np.nan, index=te.index)
    trg = {k: g for k, g in tr.groupby(['pid', 'L', 'mes'])}
    for k, g in te.groupby(['pid', 'L', 'mes']):
        t = trg.get(k)
        if t is None or len(t) < MIN_TREINO:
            continue
        qg = np.percentile(t[f'g_{v}'], PERCENTIS)
        qo = np.percentile(t[f'o_{v}'], PERCENTIS)
        y = qm(g[f'g_{v}'].values, qg, qo)
        if v == 'pr':
            y = np.where(g[f'g_{v}'].values <= 0, 0.0, y)      # chuva zero continua zero
        lim = {'pr': (0, None), 'rh': (0, 100), 'u2': (0, None), 'rs': (0, None)}.get(v, (None, None))
        saida.loc[g.index] = np.clip(y, lim[0], lim[1]) if lim != (None, None) else y
    return saida


def ets(prev, obs, limiar):
    a = ((prev >= limiar) & (obs >= limiar)).sum()
    b = ((prev >= limiar) & (obs < limiar)).sum()
    c = ((prev < limiar) & (obs >= limiar)).sum()
    n = len(obs)
    ar = (a + b) * (a + c) / n if n else 0
    den = a + b + c - ar
    return (a - ar) / den if den else np.nan


def metricas(x, o, v, limites=None):
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
    """Diferença de MAE (a - b), com IC 95% por bootstrap de dias. Negativo: a erra menos que b."""
    d = ((a - o).abs() - (b - o).abs()).groupby(dias.values).agg(['sum', 'count'])
    s, c = d['sum'].values, d['count'].values
    rng = np.random.default_rng(semente)
    idx = rng.integers(0, len(s), size=(n_boot, len(s)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return s.sum() / c.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def analisar(df, lat):
    df = df.copy()
    for c in ['L', 'pid'] + [f'{f}_{v}' for f in ('o', 'g') for v in VARS] + ['o_eto', 'elev', 'ok']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df[df['ok'] > 0].dropna(subset=[f'{f}_{v}' for f in ('o', 'g') for v in VARS] + ['o_eto', 'elev'])
    df['pid'], df['L'] = df['pid'].astype(int), df['L'].astype(int)
    df['data'] = pd.to_datetime(df['dia'])
    df['mes'] = df['data'].dt.month
    df['doy'] = df['data'].dt.dayofyear
    df['lat'] = df['pid'].map(lat)
    df['teste'] = df['data'] > pd.Timestamp(FIM_TREINO)
    df['estacao'] = np.where(df['mes'].isin([6, 7, 8, 9]), 'seca (jun-set)', 'demais meses')
    df = df.reset_index(drop=True)
    log(f'   {len(df):,} pares ponto-dia-prazo válidos ({int(df["teste"].sum()):,} no teste de 2025)')
    salvar(df.drop(columns=['data']).round(4), 'K9_dados_pontos.csv', index=False)

    tr, te = df[~df['teste']], df[df['teste']]
    st = estatisticas_treino(tr)
    st = st[st['n_treino'] >= MIN_TREINO]
    r = te.merge(st, on=['pid', 'L', 'mes'], how='inner')
    trs = tr.merge(st, on=['pid', 'L', 'mes'], how='inner')
    log(f'   {len(r):,} previsões no teste com treino suficiente (treino mediano de {int(st["n_treino"].median())} '
        f'dias por ponto, prazo e mês)')

    # --- corrigidas, no teste e no treino (o treino serve ao fator direto da ETo)
    prev, prev_tr = {}, {}
    for v in VARS:
        prev[v] = calibrar(r, st, v)
        prev_tr[v] = calibrar(trs, st, v)
        if v in ('rh', 'u2', 'rs', 'tmax', 'tmin'):
            prev[v]['mapeamento de quantis'] = quantis_por_grupo(tr, r, v)
    if 'pr' in prev:
        prev['pr']['mapeamento de quantis'] = quantis_por_grupo(tr, r, 'pr')

    # Tmax/Tmin com a regra da amplitude mínima, como o motor grava
    def temps(p, mt):
        return amplitude_minima(p['tmax'][mt], p['tmin'][mt])

    tx_m, tn_m = temps(prev, 'motor V1.5: escala de variância')
    tx_a, tn_a = temps(prev, 'aditiva')
    prev['tmax']['motor V1.5: escala de variância'], prev['tmin']['motor V1.5: escala de variância'] = tx_m, tn_m
    prev['tmax']['aditiva'], prev['tmin']['aditiva'] = tx_a, tn_a

    # --- ETo
    def eto(dfx, tx, tn, rh, u2, rs):
        return eto_pm(tx.values, tn.values, rh.values, u2.values, rs.values, dfx['elev'].values,
                      dfx['lat'].values, dfx['doy'].values)

    mot = lambda p, v: p[v][metodo_motor(v)]
    eto_mot = eto(r, tx_m, tn_m, mot(prev, 'rh'), mot(prev, 'u2'), mot(prev, 'rs'))
    tx_tr, tn_tr = amplitude_minima(prev_tr['tmax']['motor V1.5: escala de variância'],
                                    prev_tr['tmin']['motor V1.5: escala de variância'])
    eto_mot_tr = eto(trs, tx_tr, tn_tr, mot(prev_tr, 'rh'), mot(prev_tr, 'u2'), mot(prev_tr, 'rs'))
    fator_eto = (pd.DataFrame({'pid': trs['pid'], 'L': trs['L'], 'mes': trs['mes'], 'o': trs['o_eto'], 'm': eto_mot_tr})
                 .groupby(['pid', 'L', 'mes']).sum())
    fator_eto = (fator_eto['o'] / fator_eto['m'].clip(lower=1e-3)).clip(0.5, 2.0).rename('f_eto').reset_index()
    f_r = r[['pid', 'L', 'mes']].merge(fator_eto, on=['pid', 'L', 'mes'], how='left')['f_eto'].fillna(1.0).values
    gx, gn = amplitude_minima(r['g_tmax'], r['g_tmin'])
    prev['eto'] = {
        'GFS bruto': pd.Series(eto(r, gx, gn, r['g_rh'], r['g_u2'], r['g_rs']), index=r.index),
        'motor V1.5': pd.Series(eto_mot, index=r.index),
        'motor com Tmax/Tmin aditivas': pd.Series(eto(r, tx_a, tn_a, mot(prev, 'rh'), mot(prev, 'u2'), mot(prev, 'rs')), index=r.index),
        'motor + fator direto na ETo [0,5; 2]': pd.Series(eto_mot * f_r, index=r.index),
        'controle: Penman com entradas do BR-DWGD': pd.Series(eto(r, r['o_tmax'], r['o_tmin'], r['o_rh'], r['o_u2'], r['o_rs']), index=r.index),
    }

    # previsões do teste (observado, GFS bruto e o que o motor gravaria), para reanálise
    prev_teste = r[['pid', 'L', 'mes', 'dia'] + [f'o_{v}' for v in VARS] + ['o_eto'] + [f'g_{v}' for v in VARS]].copy()
    for v in VARS + ['eto']:
        prev_teste[f'motor_{v}'] = prev[v][metodo_motor(v)]
    salvar(prev_teste.round(4), 'K9_previsoes_teste_2025.csv', index=False)

    # --- tabelas por variável
    resumo, todas = [], []
    for v in VARS + ['eto']:
        o = r['o_eto'] if v == 'eto' else r[f'o_{v}']
        linhas = []
        for nome, x in prev[v].items():
            ok = x.notna()
            for L, idx in [('todos', ok)] + [(L, ok & (r['L'] == L)) for L in LEADS]:
                linhas.append({'var': v, 'prazo': L, 'metodo': nome, **metricas(x[idx], o[idx], v)})
            for est in ('seca (jun-set)', 'demais meses'):
                idx = ok & (r['estacao'] == est)
                linhas.append({'var': v, 'prazo': est, 'metodo': nome, **metricas(x[idx], o[idx], v)})
        t = pd.DataFrame(linhas)
        todas.append(t)
        tv = t.set_index(['prazo', 'metodo']).drop(columns='var').round(3)
        tabela(tv, f'K9 - {NOMES[v]} no TESTE (2025, fora do treino); viés, MAE e RMSE na unidade da variável; '
                   f'frequências em % dos ponto-dias:')

        # comparação: motor x bruto, e melhor alternativa x motor (mesmos casos: onde todas existem)
        nm = metodo_motor(v)
        comum = pd.concat([x.notna() for x in prev[v].values()], axis=1).all(axis=1)
        if v == 'eto':
            alternativas = [k for k in prev[v] if k not in ('GFS bruto', nm) and not k.startswith('controle')]
        else:
            alternativas = [k for k in prev[v] if k not in ('GFS bruto', nm)]
        xm, xb, oo, dd = prev[v][nm][comum], prev[v]['GFS bruto'][comum], o[comum], r.loc[comum, 'dia']
        d_mb, lo_mb, hi_mb = ic_dif_mae(xm, xb, oo, dd)
        mae_m = (xm - oo).abs().mean()
        melhor, info_alt = None, None
        for a in alternativas:
            xa = prev[v][a][comum]
            d, lo, hi = ic_dif_mae(xa, xm, oo, dd)
            if info_alt is None or d < info_alt[1]:
                melhor, info_alt = a, (xa, d, lo, hi)
        xa, d_am, lo_am, hi_am = info_alt
        m_a, m_m = metricas(xa, oo, v), metricas(xm, oo, v)
        piora_vol = ('razao_volume' in m_a and abs(m_a['razao_volume'] - 1) > abs(m_m['razao_volume'] - 1) + 0.05)
        piora_ets = (v == 'pr' and m_a['ETS_1mm'] < m_m['ETS_1mm'] - 0.01)
        indicada = (d_am <= -GANHO_MIN * mae_m) and (hi_am < 0) and not piora_vol and not piora_ets
        if hi_mb < 0:
            sit = 'o motor MELHORA o GFS'
        elif lo_mb > 0:
            sit = 'o motor PIORA o GFS'
        else:
            sit = 'o motor não muda o erro de forma detectável'
        if 'razao_volume' in m_m:
            sit += f" (volume: bruto {metricas(xb, oo, v)['razao_volume']:.3f} -> motor {m_m['razao_volume']:.3f})"
        resumo.append({
            'variavel': NOMES[v], 'metodo_motor': nm, 'n': int(comum.sum()),
            'MAE_bruto': (xb - oo).abs().mean(), 'MAE_motor': mae_m,
            'motor_menos_bruto': d_mb, 'IC95_inf': lo_mb, 'IC95_sup': hi_mb, 'situacao_motor': sit,
            'melhor_alternativa': melhor, 'MAE_alternativa': (xa - oo).abs().mean(),
            'alternativa_menos_motor': d_am, 'IC95_inf_alt': lo_am, 'IC95_sup_alt': hi_am,
            'indicacao': ('AVALIAR TROCA: a alternativa erra menos, com folga e sem piorar volume' if indicada
                          else 'manter o motor')})
    salvar(pd.concat(todas, ignore_index=True), 'K9_metricas_todas.csv', index=False)
    res = pd.DataFrame(resumo)
    salvar(res, 'K9_RESUMO.csv', index=False)

    # controle da fórmula da ETo
    ctl = prev['eto']['controle: Penman com entradas do BR-DWGD']
    m_ctl = metricas(ctl, r['o_eto'], 'eto')
    log('\n' + '=' * 100)
    log('CONTROLE DA ETo: Penman do motor alimentado com as variáveis do próprio BR-DWGD x ETo do BR-DWGD')
    log(f"   viés {m_ctl['vies']:+.3f} mm/dia | MAE {m_ctl['MAE']:.3f} | razão de volume {m_ctl['razao_volume']:.3f} | "
        f"correlação {m_ctl['corr']:.3f}")
    log('   (perto de zero: a fórmula do motor é a mesma do BR-DWGD, e o erro da ETo da previsão vem das entradas;'
        ' longe de zero: parte do erro da ETo é diferença de fórmula, não do GFS)')

    # rodada a rodada: qual entrada pesa mais no erro da ETo (troca uma entrada corrigida pela observada)
    base = (pd.Series(eto_mot, index=r.index) - r['o_eto']).abs().mean()
    contrib = []
    entradas = {'tmax/tmin': None, 'rh': 'o_rh', 'u2': 'o_u2', 'rs': 'o_rs'}
    for nome, col in entradas.items():
        tx, tn = (r['o_tmax'], r['o_tmin']) if nome == 'tmax/tmin' else (tx_m, tn_m)
        rh = r['o_rh'] if col == 'o_rh' else mot(prev, 'rh')
        u2 = r['o_u2'] if col == 'o_u2' else mot(prev, 'u2')
        rs = r['o_rs'] if col == 'o_rs' else mot(prev, 'rs')
        e = (pd.Series(eto(r, tx, tn, rh, u2, rs), index=r.index) - r['o_eto']).abs().mean()
        contrib.append({'entrada trocada pela observada': nome, 'MAE_ETo': e, 'reducao_do_MAE': base - e,
                        'reducao_pct': 100 * (base - e) / base})
    tabela(pd.DataFrame(contrib).set_index('entrada trocada pela observada').round(3),
           f'Peso de cada entrada no erro da ETo do motor (MAE do motor = {base:.3f} mm/dia): quanto o MAE cai se só '
           f'aquela entrada fosse perfeita')
    salvar(pd.DataFrame(contrib), 'K9_ETo_peso_das_entradas.csv', index=False)

    log('\n' + '=' * 100)
    log('RESUMO K9 (2025, fora do treino; IC 95% por bootstrap de dias; diferença negativa = erra menos)')
    log('=' * 100)
    for _, x in res.iterrows():
        log(f"\n{x['variavel']}  [motor: {x['metodo_motor']}]  n = {x['n']:,}")
        log(f"   MAE bruto {x['MAE_bruto']:.3f} -> motor {x['MAE_motor']:.3f}; motor - bruto {x['motor_menos_bruto']:+.3f} "
            f"(IC {x['IC95_inf']:+.3f} a {x['IC95_sup']:+.3f}): {x['situacao_motor']}")
        log(f"   melhor alternativa: {x['melhor_alternativa']}, MAE {x['MAE_alternativa']:.3f}; alternativa - motor "
            f"{x['alternativa_menos_motor']:+.3f} (IC {x['IC95_inf_alt']:+.3f} a {x['IC95_sup_alt']:+.3f})")
        log(f"   ➜ {x['indicacao']}")
    log('\n   Regra da indicação: a alternativa precisa reduzir o MAE do motor em 3% ou mais, com o IC 95% inteiro abaixo '
        'de zero, sem piorar a razão de volume em mais de 0,05 (chuva, vento, radiação, ETo) nem o ETS da chuva em mais de 0,01.')
    log('   Chuva: o dia do BR-DWGD vai das 12 UTC da véspera às 12 UTC, o do GFS das 00 às 24 UTC (Parte A, nota 10). '
        'Nenhuma correção de média resolve essa defasagem; ela aparece no MAE e no ETS de todos os métodos.')
    return res


# =========================================================================================
# EXECUÇÃO
# =========================================================================================
log('=' * 100)
log(f'K9 - VALIDAÇÃO DE TODAS AS VARIÁVEIS DA PREVISÃO (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
log('=' * 100)
if LOCAL:
    with open(LOCAL, 'rb') as f:
        DF, LAT = pickle.load(f)
    log('   (teste offline com dados locais)')
else:
    DF, LAT = baixar()
RES = analisar(DF, LAT)
log('\nNada foi gravado no Earth Engine.')
z = shutil.make_archive(PASTA, 'zip', PASTA)
log(f'📦 {z}')
if not LOCAL:
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        log('   (baixe pelo painel Arquivos do Colab)')
