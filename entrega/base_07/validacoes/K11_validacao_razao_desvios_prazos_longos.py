# =========================================================================================
# K11 - ESCALA DE VARIÂNCIA DA TMAX E DA TMIN NOS PRAZOS LONGOS (SOMENTE LEITURA)
# 22/10/2026. Cole inteiro numa célula do Colab e rode. Nada é gravado no Earth Engine.
#
# POR QUE EXISTE
#   A auditoria 08 de 22/10 (J5a) e o diagnóstico K10 acharam a previsão de 26/10/2026 em Casa Nova-BA
#   (rodada 21/10 00Z, prazo 6) com Tmax de 45,24 °C, acima do recorde do INMET (44,8 °C), quando o GFS
#   bruto dava 35,41 °C. Causa: a escala de variância do motor V1.5,
#       Tmax = m_sicsb + (GFS - m_gfs) x clip(s_sicsb / s_gfs, 0,5, 2)
#   com razão 1,98 (s_gfs 0,97 °C). Nos prazos longos o GFS varia pouco de um dia para outro porque a
#   previsão perde habilidade e se aproxima da climatologia do modelo; a escala interpreta isso como
#   variância baixa demais e multiplica a anomalia por até 2. A K9A já mostrava o sinal no frio: no prazo
#   13, a Tmin pela variância previa geada (<= 2 °C) em 0,154% dos ponto-dias contra 0,108% observados.
#
# O QUE COMPARA (Tmax e Tmin; os mesmos 300 pontos, prazos 1, 3, 8 e 13 e anos da K9A)
#   M0  motor atual: razão limitada a [0,5; 2] em todos os prazos
#   M1  PROPOSTA: razão limitada a [0,5; 1] nos prazos de 6 dias em diante (faixas L6a10 e L11a15);
#       nos prazos 1 a 5 continua [0,5; 2] (nos prazos 1 e 3 é idêntico ao M0)
#   M2  razão limitada a [0,5; 1,5] em todos os prazos
#   M3  razão limitada a [0,5; 1] em todos os prazos (só informação)
#   M4  M0 + teto físico: Tmax no máximo o maior valor observado do ponto naquele mês no treino + 1 °C
#       (Tmin no mínimo o menor observado - 1 °C) (só informação: cortaria um recorde verdadeiro)
#   aditiva (método anterior à K8, só referência)
#   As Tmax e Tmin de cada método passam pela amplitude mínima de 1 °C, como no motor.
#
# DADOS
#   Usa os dados brutos da K9A guardados no seu Google Drive (cache_validacao_K9A/K9A_dados_brutos.parquet,
#   gravado em 20/10/2026). Se não achar, junta os lotes .pkl do mesmo cache; se também não achar, baixa de
#   novo só o GFS v16 (2021-2025, de 1 a 2 horas).
#
# TESTES
#   A. OFICIAL (decide): GFS v16, treino até 31/12/2024, teste em 2025 inteiro
#   B. CADA ANO DE FORA (decide junto): no v16, cada ano de 2021 a 2025 testado com o treino nos outros
#   C. GFS v15 (só informação): o mesmo B no bloco v15 (2019-2021)
#
# REGRA DA DECISÃO (fixada antes de rodar; vale para a Tmax e para a Tmin, cada uma por si)
#   O M1 substitui o M0 se, nos prazos 8 e 13 juntos (os de 6 dias em diante):
#     (1) teste A: não piora o erro: limite superior do IC 95% (bootstrap de dias) da diferença de MAE
#         (M1 - M0) abaixo de +0,5% do MAE do M0;
#     (2) teste A: a taxa de excedência física não aumenta: Tmax acima do maior valor observado do ponto
#         no mês (no treino) + 1 °C; Tmin abaixo do menor observado - 1 °C. Na Tmax, também não pode haver
#         mais previsões acima do recorde do INMET (44,8 °C) que no M0;
#     (3) teste A: a frequência do evento extremo não se afasta da observada mais que 0,5 ponto
#         percentual além do M0 (Tmax > 35 °C; Tmin <= 2 °C);
#     (4) teste B: em TODOS os anos de 2021 a 2025, MAE do M1 <= MAE do M0 x 1,005.
#   Se o M1 não passar, o M2 é avaliado pela mesma regra, mas em TODOS os prazos (ele muda também os
#   prazos 1 e 3). Se nenhum passar: manter o M0 e registrar.
#   Se o M1 passar, a mudança no motor (05a e 05b) é uma constante: RAZAO_DESVIO_MAX_LONGO = 1.0 para as
#   faixas L6a10 e L11a15 na Tmax e na Tmin. Nada muda nos prazos 1 a 5 nem na UR e na radiação (a K11
#   não testa essas duas; se o M1 passar, a UR e a radiação podem ser vistas depois numa K11b).
#
# LIMITAÇÃO: as estatísticas de treino são por ponto, prazo e mês (como na K9A); a matriz V2.1 usa a
# faixa de prazo inteira. O prazo 8 representa a faixa L6a10 e o 13 a L11a15; os prazos 6 e 16, onde
# apareceram os casos de 22/10, não estão nos dados da K9A.
# =========================================================================================
import os, glob, shutil, time, pickle, hashlib, warnings
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# ------------------------------- CONFIGURAÇÃO -------------------------------------------
PROJETO = 'clima-492922'
USAR_DRIVE = True
CACHE_K9A = '/content/drive/MyDrive/cache_validacao_K9A'
N_PONTOS = 300
LEADS = [1, 3, 8, 13]
LEADS_LONGOS = [8, 13]               # prazos de 6 dias em diante presentes nos dados
LIMIAR_LONGO = 6                     # M1 muda a razão a partir deste prazo
FIM_TREINO_OFICIAL = '2024-12-31'
BLOCOS = [('GFS v16', '2021-03-23', '2025-12-31'), ('GFS v15', '2019-06-13', '2021-03-21')]   # datas da RODADA
N_BOOT = 1000
MIN_TREINO = 20
MIN_TESTE_ANO = 20000
RAZAO_MIN, RAZAO_MAX = 0.5, 2.0      # motor V1.5 atual
AMPLITUDE_MIN_C = 1.0
RECORDE_TMAX = 44.8
MARGEM_FISICA = 1.0                  # °C além do máximo (mínimo) observado do ponto no mês
TOL_MAE = 0.005                      # +0,5% do MAE do M0
TOL_FREQ = 0.5                       # pontos percentuais
# -----------------------------------------------------------------------------------------

BR_DWGD, GFS = 'projects/ee-alexandrexavier/assets/BR-DWGD', 'NOAA/GFS0P25'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
DIA_MS = 86400000
VARS = ['tmax', 'tmin']
NOMES = {'tmax': 'Tmax (°C)', 'tmin': 'Tmin (°C)'}
M0 = 'M0 motor atual: razão [0,5; 2] em todos os prazos'
M1 = 'M1 proposta: razão [0,5; 1] nos prazos 6+'
M2 = 'M2 razão [0,5; 1,5] em todos os prazos'
M3 = 'M3 razão [0,5; 1] em todos os prazos'
M4 = 'M4 M0 + teto físico (máx./mín. do ponto no mês ± 1 °C)'
ADITIVA = 'aditiva (antes da K8)'
GFS_BRUTO = 'GFS sem correção'

AGORA = datetime.now(timezone(timedelta(hours=-3)))
LOCAL = os.environ.get('K11_DADOS_LOCAIS')       # só para o teste offline (sem Earth Engine e sem Drive)
BASE = '.' if LOCAL else ('/content' if os.path.isdir('/content') else '.')
PASTA = os.path.join(BASE, f'validacao_K11_{AGORA:%Y%m%d_%H%M}')
CACHE = os.path.join(BASE, 'cache_validacao_K11') if LOCAL else CACHE_K9A
if USAR_DRIVE and not LOCAL:
    try:
        from google.colab import drive
        drive.mount('/content/drive')
    except Exception as e:
        print(f'⚠️ Drive indisponível ({e}); sem os dados da K9A o script baixa de novo (de 1 a 2 horas).')
        CACHE = os.path.join(BASE, 'cache_validacao_K11')
os.makedirs(PASTA, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)
LOG = os.path.join(PASTA, 'LOG_K11.txt')


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
# PARTE 1. DADOS (reaproveita a K9A; só baixa se não achar)
# =========================================================================================
def carregar():
    arq = os.path.join(CACHE_K9A, 'K9A_dados_brutos.parquet')
    if os.path.exists(arq):
        log(f'   dados da K9A: {arq}')
        df = pd.read_parquet(arq)
    else:
        lotes = sorted(glob.glob(os.path.join(CACHE_K9A, 'K9A_*_*.pkl')))
        if lotes:
            log(f'   parquet da K9A não encontrado; juntando {len(lotes)} lotes .pkl de {CACHE_K9A}')
            partes = []
            for a in lotes:
                with open(a, 'rb') as f:
                    partes.append(pickle.load(f))
            df = pd.concat([p for p in partes if len(p)], ignore_index=True)
        else:
            log('   ⚠️ dados da K9A não encontrados no Drive: baixando de novo só o GFS v16 (de 1 a 2 horas)')
            df = baixar_v16()
    pts = None
    for c in (os.path.join(CACHE_K9A, f'pontos_v2_{N_PONTOS}.pkl'), os.path.join(CACHE, f'pontos_v2_{N_PONTOS}.pkl')):
        if os.path.exists(c):
            with open(c, 'rb') as f:
                pts = pickle.load(f)
            break
    lat = {i: c[1] for i, c in enumerate(pts)} if pts else {}
    return df, lat


TRANSITORIOS = ('Too many concurrent', 'Internal error', '503', '429', 'deadline', 'Connection', 'temporarily',
                'Remote end closed')
PESADOS = ('Computation timed out', 'memory limit', 'User memory', 'capacity exceeded', 'aborted after accumulating',
           'Request payload size', 'too large')


def baixar_v16():
    """Mesma extração da K9A (BR-DWGD e GFS bilinear na grade do SAB), só Tmax e Tmin e só o GFS v16."""
    import ee
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def gi(obj, rot='', n=6):
        for t in range(n):
            try:
                return obj.getInfo()
            except Exception as e:
                if t < n - 1 and any(k in str(e) for k in TRANSITORIOS) and not any(k in str(e) for k in PESADOS):
                    time.sleep(min(30 * (t + 1), 180))
                    continue
                raise

    def buscar(lote, construir, rot):
        try:
            return [f['properties'] for f in gi(construir(lote), rot)['features']]
        except Exception as e:
            if any(k in str(e) for k in PESADOS + ('Too many concurrent',)) and len(lote) > 1:
                meio = len(lote) // 2
                return buscar(lote[:meio], construir, rot + 'a') + buscar(lote[meio:], construir, rot + 'b')
            raise

    UF_BR = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
    LIMITES = UF_BR.geometry().bounds()
    MASC_BR = ee.Image.constant(1).clipToCollection(UF_BR).mask()
    PROJ_SAB = ee.Projection(CRS, TRANSFORM)

    def dia(col, d):
        return ee.Image(ee.ImageCollection(col).filterDate(d, ee.Date(d).advance(1, 'day')).first())

    def br_dia(d):
        img = dia(BR_DWGD, d)
        valido = img.select('pr').gt(-32768)
        return ee.Image.cat([img.select('Tmax').multiply(0.00106815).add(15.0).rename('o_tmax'),
                             img.select('Tmin').multiply(0.00106815).add(15.0).rename('o_tmin')]).toFloat().updateMask(valido)

    def gfs_dia(d, L):
        criacao = int(pd.Timestamp(d).value // 10 ** 6) - (L - 1) * DIA_MS
        h0 = 24 * (L - 1)
        horas = [h for h in range(h0 + 1, h0 + 25) if h <= 120 or h % 3 == 0]
        horas_chuva = [h for h in horas if h % 6 == 0]
        dt = ee.Date(criacao)
        bruta = (ee.ImageCollection(GFS).filterDate(dt, dt.advance(1, 'hour'))
                 .filter(ee.Filter.eq('creation_time', criacao))
                 .filter(ee.Filter.gt('forecast_hours', h0)).filter(ee.Filter.lte('forecast_hours', h0 + 24)))
        bruta = ee.ImageCollection(bruta.distinct('forecast_hours'))
        ok = bruta.size().eq(len(horas)).And(bruta.filter(ee.Filter.inList('forecast_hours', horas_chuva)).size()
                                             .eq(len(horas_chuva)))
        rod = bruta.map(lambda i: i.resample('bilinear')).select('temperature_2m_above_ground')
        vazia = ee.Image.constant(0).rename('temperature_2m_above_ground').toFloat().updateMask(ee.Image.constant(0))
        rod = rod.merge(ee.ImageCollection([vazia]))
        cheia = ee.Image.cat([rod.max().rename('g_tmax'), rod.min().rename('g_tmin')]).toFloat()
        return cheia, ok

    arq_pts = os.path.join(CACHE, f'pontos_v2_{N_PONTOS}.pkl')
    if os.path.exists(arq_pts):
        with open(arq_pts, 'rb') as f:
            coords = pickle.load(f)
    else:
        validos = dia(BR_DWGD, '2001-01-15').select('pr').gt(-32768).unmask(0).gt(0)
        fc = gi(ee.Image.constant(1).updateMask(validos).updateMask(MASC_BR).sample(
            region=LIMITES, projection=PROJ_SAB, numPixels=int(N_PONTOS * 4), seed=23, geometries=True, tileScale=4))
        coords = [f['geometry']['coordinates'] for f in fc['features']][:N_PONTOS]
        with open(arq_pts, 'wb') as f:
            pickle.dump(coords, f)
    PONTOS = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(c), {'pid': i}) for i, c in enumerate(coords)])

    def construir(lote):
        fcs = []
        for d, L in lote:
            g, ok = gfs_dia(d, L)
            fcs.append(ee.Image.cat([br_dia(d), g]).reduceRegions(collection=PONTOS, reducer=ee.Reducer.first(),
                                                                   crs=CRS, crsTransform=TRANSFORM, tileScale=4)
                       .map(lambda f: ee.Feature(None, f.toDictionary()).set({'dia': d, 'L': L, 'ok': ok})))
        return ee.FeatureCollection(fcs).flatten()

    itens = [(x.strftime('%Y-%m-%d'), L) for x in pd.date_range('2021-03-24', '2025-12-31') for L in LEADS
             if bloco_da_rodada((x - pd.Timedelta(days=L - 1)).strftime('%Y-%m-%d')) == 'GFS v16']
    chave = hashlib.md5(f'K11|{len(itens)}'.encode()).hexdigest()[:8]
    partes = []
    lotes = [itens[i:i + 8] for i in range(0, len(itens), 8)]
    t0 = time.time()
    for k, lote in enumerate(lotes):
        arq = os.path.join(CACHE, f'K11_{chave}_{k:05d}.pkl')
        if os.path.exists(arq):
            with open(arq, 'rb') as f:
                partes.append(pickle.load(f))
            continue
        df = pd.DataFrame(buscar(lote, construir, f'lote {k + 1}/{len(lotes)}'))
        with open(arq, 'wb') as f:
            pickle.dump(df, f)
        partes.append(df)
        if (k + 1) % 50 == 0:
            log(f'   … lote {k + 1}/{len(lotes)} | {(time.time() - t0) / 60:.0f} min')
    return pd.concat([p for p in partes if len(p)], ignore_index=True)


def preparar(df):
    df = df.copy()
    for c in ['L', 'pid', 'ok', 'o_tmax', 'o_tmin', 'g_tmax', 'g_tmin']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    n0 = len(df)
    df = df[df['ok'] > 0].dropna(subset=['o_tmax', 'o_tmin', 'g_tmax', 'g_tmin'])
    df['pid'], df['L'] = df['pid'].astype(int), df['L'].astype(int)
    df['data'] = pd.to_datetime(df['dia'])
    df['ano'], df['mes'] = df['data'].dt.year, df['data'].dt.month
    df['rodada'] = (df['data'] - pd.to_timedelta(df['L'] - 1, unit='D')).dt.strftime('%Y-%m-%d')
    df['bloco'] = df['rodada'].map(bloco_da_rodada)
    df = df[df['bloco'].notna() & df['L'].isin(LEADS)]
    log(f'   {len(df):,} pares ponto-dia-prazo válidos (de {n0:,}) nos blocos {sorted(df["bloco"].unique())}')
    tabela(df.groupby(['bloco', 'ano', 'L']).size().unstack('L'), 'Pares válidos por bloco, ano e prazo:')
    return df[['pid', 'L', 'dia', 'data', 'ano', 'mes', 'bloco', 'o_tmax', 'o_tmin', 'g_tmax', 'g_tmin']].reset_index(drop=True)


# =========================================================================================
# PARTE 2. MÉTODOS (as fórmulas do motor V1.5) E MÉTRICAS
# =========================================================================================
def amplitude_minima(tmax, tmin):
    tmed = (tmax + tmin) / 2
    meia = np.maximum(tmax - tmin, AMPLITUDE_MIN_C) / 2
    return tmed + meia, tmed - meia


def estatisticas_treino(tr):
    g = tr.groupby(['pid', 'L', 'mes'])
    st = g.size().rename('n_treino').to_frame()
    for v in VARS:
        st[f'mo_{v}'], st[f'so_{v}'] = g[f'o_{v}'].mean(), g[f'o_{v}'].std()
        st[f'mg_{v}'], st[f'sg_{v}'] = g[f'g_{v}'].mean(), g[f'g_{v}'].std()
    # limites físicos do ponto no mês (observado, todos os prazos do treino juntos)
    lim = tr.groupby(['pid', 'mes']).agg(omax_tmax=('o_tmax', 'max'), omin_tmin=('o_tmin', 'min')).reset_index()
    return st.reset_index().merge(lim, on=['pid', 'mes'], how='left')


def razoes(x, v):
    """Razão bruta s_obs/s_gfs (antes de limitar) e as limitadas de cada método."""
    bruta = x[f'so_{v}'] / x[f'sg_{v}'].clip(lower=1e-3)
    longo = x['L'] >= LIMIAR_LONGO
    return {
        M0: bruta.clip(RAZAO_MIN, RAZAO_MAX),
        M1: bruta.clip(RAZAO_MIN, RAZAO_MAX).where(~longo, bruta.clip(RAZAO_MIN, 1.0)),
        M2: bruta.clip(RAZAO_MIN, 1.5),
        M3: bruta.clip(RAZAO_MIN, 1.0),
    }


def prever(tr, te):
    st = estatisticas_treino(tr)
    st = st[st['n_treino'] >= MIN_TREINO]
    r = te.merge(st, on=['pid', 'L', 'mes'], how='inner')
    P = {v: {} for v in VARS}
    rz = {v: razoes(r, v) for v in VARS}
    for v in VARS:
        g, mo, mg = r[f'g_{v}'], r[f'mo_{v}'], r[f'mg_{v}']
        P[v][GFS_BRUTO] = g
        P[v][ADITIVA] = g + (mo - mg)
        for nome, rzv in rz[v].items():
            P[v][nome] = mo + (g - mg) * rzv
    for nome in [ADITIVA, M0, M1, M2, M3]:                 # amplitude mínima como no motor
        P['tmax'][nome], P['tmin'][nome] = amplitude_minima(P['tmax'][nome], P['tmin'][nome])
    gx, gn = amplitude_minima(P['tmax'][GFS_BRUTO], P['tmin'][GFS_BRUTO])
    P['tmax'][GFS_BRUTO], P['tmin'][GFS_BRUTO] = gx, gn
    tx4 = P['tmax'][M0].clip(upper=r['omax_tmax'] + MARGEM_FISICA)
    tn4 = P['tmin'][M0].clip(lower=r['omin_tmin'] - MARGEM_FISICA)
    P['tmax'][M4], P['tmin'][M4] = amplitude_minima(tx4, tn4)
    r = r.assign(rz_bruta_tmax=r['so_tmax'] / r['sg_tmax'].clip(lower=1e-3),
                 rz_bruta_tmin=r['so_tmin'] / r['sg_tmin'].clip(lower=1e-3))
    return r, P


def metricas(x, o, r, v):
    e = x - o
    lin = {'n': int(len(o)), 'vies': e.mean(), 'MAE': e.abs().mean(), 'RMSE': np.sqrt((e ** 2).mean()),
           'corr': np.corrcoef(x, o)[0, 1] if len(o) > 2 else np.nan}
    if v == 'tmax':
        lin['P99_prev'], lin['P99_obs'] = np.percentile(x, 99), np.percentile(o, 99)
        lin['max_prev'], lin['max_obs'] = x.max(), o.max()
        lin['pct_35_prev'], lin['pct_35_obs'] = 100 * (x > 35).mean(), 100 * (o > 35).mean()
        lin['n_acima_recorde'] = int((x > RECORDE_TMAX).sum())
        lin['pct_excede_fisico'] = 100 * (x > r['omax_tmax'] + MARGEM_FISICA).mean()
        lin['pct_obs_excede_fisico'] = 100 * (o > r['omax_tmax'] + MARGEM_FISICA).mean()
    else:
        lin['P1_prev'], lin['P1_obs'] = np.percentile(x, 1), np.percentile(o, 1)
        lin['min_prev'], lin['min_obs'] = x.min(), o.min()
        lin['pct_geada2_prev'], lin['pct_geada2_obs'] = 100 * (x <= 2).mean(), 100 * (o <= 2).mean()
        lin['n_acima_recorde'] = 0
        lin['pct_excede_fisico'] = 100 * (x < r['omin_tmin'] - MARGEM_FISICA).mean()
        lin['pct_obs_excede_fisico'] = 100 * (o < r['omin_tmin'] - MARGEM_FISICA).mean()
    return lin


def freq_extremo(m, v):
    return (m['pct_35_prev'], m['pct_35_obs']) if v == 'tmax' else (m['pct_geada2_prev'], m['pct_geada2_obs'])


def ic_dif_mae(a, b, o, dias, n_boot=N_BOOT, semente=11):
    d = ((a - o).abs() - (b - o).abs()).groupby(np.asarray(dias)).agg(['sum', 'count'])
    s, c = d['sum'].values, d['count'].values
    rng = np.random.default_rng(semente)
    idx = rng.integers(0, len(s), size=(n_boot, len(s)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return s.sum() / c.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


# =========================================================================================
# PARTE 3. TESTES
# =========================================================================================
def teste_a(df):
    log('\n' + '=' * 100)
    log('TESTE A (OFICIAL): GFS v16, treino até 31/12/2024, teste em 2025')
    log('=' * 100)
    b = df[df['bloco'] == 'GFS v16']
    tr, te = b[b['data'] <= pd.Timestamp(FIM_TREINO_OFICIAL)], b[b['data'] > pd.Timestamp(FIM_TREINO_OFICIAL)]
    r, P = prever(tr, te)
    log(f'   {len(r):,} previsões no teste')
    # quanto a razão bruta passa de 1 e de 2 (por prazo): o tamanho do problema
    rz = r.groupby('L').agg(**{f'{k}_{v}': (f'rz_bruta_{v}', f) for v in VARS for k, f in
                              (('mediana', 'median'), ('pct_acima_1', lambda s: 100 * (s > 1).mean()),
                               ('pct_acima_2', lambda s: 100 * (s > 2).mean()))})
    tabela(rz.round(2), 'Razão s_BR-DWGD / s_GFS por prazo (antes de limitar): mediana e % de ponto-dias acima de 1 e de 2:')
    salvar(rz, 'K11_razao_por_prazo.csv')
    linhas, comp = [], []
    grupos = [('todos', r.index == r.index)] + [(f'prazo {L}', r['L'] == L) for L in LEADS] + \
             [('prazos 8 e 13', r['L'].isin(LEADS_LONGOS))]
    for v in VARS:
        o = r[f'o_{v}']
        for nome, x in P[v].items():
            for rot, idx in grupos:
                linhas.append({'var': v, 'grupo': rot, 'metodo': nome, **metricas(x[idx], o[idx], r[idx], v)})
        for alvo, gr in ((M1, 'prazos 8 e 13'), (M2, 'todos'), (M3, 'todos'), (M4, 'prazos 8 e 13')):
            idx = r['L'].isin(LEADS_LONGOS) if gr == 'prazos 8 e 13' else (r.index == r.index)
            x0, x1, oo = P[v][M0][idx], P[v][alvo][idx], o[idx]
            d, lo, hi = ic_dif_mae(x1, x0, oo, r.loc[idx, 'dia'])
            m0, m1 = metricas(x0, oo, r[idx], v), metricas(x1, oo, r[idx], v)
            f0p, f0o = freq_extremo(m0, v)
            f1p, f1o = freq_extremo(m1, v)
            c1 = hi < TOL_MAE * m0['MAE']
            c2 = (m1['pct_excede_fisico'] <= m0['pct_excede_fisico'] + 1e-9 and
                  m1['n_acima_recorde'] <= m0['n_acima_recorde'])
            c3 = abs(f1p - f1o) <= abs(f0p - f0o) + TOL_FREQ
            comp.append({'var': v, 'metodo': alvo, 'grupo': gr, 'MAE_M0': m0['MAE'], 'MAE_metodo': m1['MAE'],
                         'dif': d, 'dif_pct': 100 * d / m0['MAE'], 'IC95_inf': lo, 'IC95_sup': hi,
                         'excede_fisico_M0_pct': m0['pct_excede_fisico'], 'excede_fisico_metodo_pct': m1['pct_excede_fisico'],
                         'acima_recorde_M0': m0['n_acima_recorde'], 'acima_recorde_metodo': m1['n_acima_recorde'],
                         'freq_extremo_obs': f0o, 'freq_extremo_M0': f0p, 'freq_extremo_metodo': f1p,
                         'c1_MAE': c1, 'c2_fisico': c2, 'c3_extremo': c3, 'passa_A': bool(c1 and c2 and c3)})
    met = pd.DataFrame(linhas)
    salvar(met, 'K11_A_metricas.csv', index=False)
    for v in VARS:
        cols = ['n', 'vies', 'MAE', 'RMSE', 'corr'] + (
            ['P99_prev', 'P99_obs', 'max_prev', 'max_obs', 'pct_35_prev', 'pct_35_obs', 'n_acima_recorde',
             'pct_excede_fisico', 'pct_obs_excede_fisico'] if v == 'tmax' else
            ['P1_prev', 'P1_obs', 'min_prev', 'min_obs', 'pct_geada2_prev', 'pct_geada2_obs', 'pct_excede_fisico',
             'pct_obs_excede_fisico'])
        tabela(met[met['var'] == v].set_index(['grupo', 'metodo'])[cols].round(3),
               f'A - {NOMES[v]}: erro e extremos (excede_fisico = % além do máx./mín. observado do ponto no mês ± 1 °C):')
    comp = pd.DataFrame(comp)
    salvar(comp, 'K11_A_comparacoes.csv', index=False)
    tabela(comp.set_index(['var', 'metodo', 'grupo']).round(4), 'A - cada método contra o M0 (dif < 0: erra menos):')
    return comp


def teste_bc(df):
    log('\n' + '=' * 100)
    log('TESTES B (v16, decide) e C (v15, informação): cada ano testado com o treino nos outros anos do bloco')
    log('=' * 100)
    linhas = []
    for bloco, _, _ in BLOCOS:
        b = df[df['bloco'] == bloco]
        anos = [a for a, n in b.groupby('ano').size().items() if n >= MIN_TESTE_ANO]
        if len(anos) < 2:
            log(f'   {bloco}: menos de 2 anos com dados suficientes; fica de fora')
            continue
        for a in anos:
            r, P = prever(b[b['ano'] != a], b[b['ano'] == a])
            if not len(r):
                continue
            for v in VARS:
                o = r[f'o_{v}']
                for grupo, idx in (('prazos 8 e 13', r['L'].isin(LEADS_LONGOS)), ('todos', r.index == r.index)):
                    for nome in (M0, M1, M2, M3, M4, ADITIVA):
                        m = metricas(P[v][nome][idx], o[idx], r[idx], v)
                        linhas.append({'bloco': bloco, 'ano': a, 'var': v, 'grupo': grupo, 'metodo': nome,
                                       'MAE': m['MAE'], 'vies': m['vies'], 'excede_fisico_pct': m['pct_excede_fisico'],
                                       'acima_recorde': m['n_acima_recorde']})
            log(f'   {bloco} {a}: {len(r):,} previsões')
    cv = pd.DataFrame(linhas)
    salvar(cv, 'K11_BC_cada_ano.csv', index=False)
    for v in VARS:
        for grupo in ('prazos 8 e 13', 'todos'):
            t = cv[(cv['var'] == v) & (cv['grupo'] == grupo)].pivot_table(index=['bloco', 'metodo'], columns='ano',
                                                                         values='MAE').round(3)
            tabela(t, f'B/C - {NOMES[v]} ({grupo}): MAE de cada ano testado:')
        t = cv[(cv['var'] == v) & (cv['grupo'] == 'prazos 8 e 13')].pivot_table(
            index=['bloco', 'metodo'], columns='ano', values='excede_fisico_pct').round(3)
        tabela(t, f'B/C - {NOMES[v]} (prazos 8 e 13): % de previsões além do limite físico do ponto:')
    return cv


def passa_b(cv, v, metodo, grupo):
    b = cv[(cv['bloco'] == 'GFS v16') & (cv['var'] == v) & (cv['grupo'] == grupo)]
    if b.empty:
        return False, 'n/d'
    t = b.pivot_table(index='ano', columns='metodo', values='MAE')
    ok = (t[metodo] <= t[M0] * (1 + TOL_MAE))
    return bool(ok.all()), f'{int(ok.sum())} de {len(ok)} anos'


def decidir(comp, cv):
    log('\n' + '=' * 100)
    log('RESULTADO FINAL K11 (regra fixada antes de rodar)')
    log('=' * 100)
    final = []
    for v in VARS:
        log(f'\n{NOMES[v]}')
        escolhido = None
        for alvo, grupo in ((M1, 'prazos 8 e 13'), (M2, 'todos')):
            x = comp[(comp['var'] == v) & (comp['metodo'] == alvo) & (comp['grupo'] == grupo)].iloc[0]
            ok_b, txt_b = passa_b(cv, v, alvo, grupo)
            passa = bool(x['passa_A']) and ok_b
            log(f"   {alvo} ({grupo}): MAE {x['MAE_metodo']:.3f} x M0 {x['MAE_M0']:.3f} ({x['dif_pct']:+.2f}%, IC "
                f"{x['IC95_inf']:+.4f} a {x['IC95_sup']:+.4f}) [{'ok' if x['c1_MAE'] else 'NÃO'}] | além do limite físico "
                f"{x['excede_fisico_M0_pct']:.3f}% -> {x['excede_fisico_metodo_pct']:.3f}%"
                f"{'; acima de 44,8 °C ' + str(int(x['acima_recorde_M0'])) + ' -> ' + str(int(x['acima_recorde_metodo'])) if v == 'tmax' else ''}"
                f" [{'ok' if x['c2_fisico'] else 'NÃO'}] | evento extremo prev/obs {x['freq_extremo_M0']:.3f}% -> "
                f"{x['freq_extremo_metodo']:.3f}% (obs {x['freq_extremo_obs']:.3f}%) [{'ok' if x['c3_extremo'] else 'NÃO'}] | "
                f"teste B: {txt_b} [{'ok' if ok_b else 'NÃO'}]{'  ✅ PASSA' if passa else ''}")
            final.append({'var': NOMES[v], 'metodo': alvo, 'grupo': grupo, 'dif_pct_A': x['dif_pct'],
                          'IC95_inf': x['IC95_inf'], 'IC95_sup': x['IC95_sup'], 'c1_MAE': x['c1_MAE'],
                          'c2_fisico': x['c2_fisico'], 'c3_extremo': x['c3_extremo'], 'teste_B': txt_b,
                          'passa': passa})
            if passa:
                escolhido = alvo
                break
        if escolhido == M1:
            log('   ➜ TROCAR: limitar a razão dos desvios a 1 nos prazos de 6 dias em diante (faixas L6a10 e L11a15).')
        elif escolhido == M2:
            log('   ➜ TROCAR: limitar a razão dos desvios a 1,5 em todos os prazos.')
        else:
            log('   ➜ MANTER o M0 (o motor atual); o M4 (teto físico) fica registrado como alternativa a discutir.')
        final.append({'var': NOMES[v], 'metodo': 'DECISÃO', 'grupo': '', 'passa': escolhido or 'manter M0'})
    f = pd.DataFrame(final)
    salvar(f, 'K11_RESULTADO_FINAL.csv', index=False)
    return f


# =========================================================================================
# EXECUÇÃO
# =========================================================================================
log('=' * 100)
log(f'K11 - RAZÃO DOS DESVIOS DA TMAX/TMIN NOS PRAZOS LONGOS (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
log('=' * 100)
if LOCAL:
    with open(LOCAL, 'rb') as f:
        DF0, LAT = pickle.load(f)
    log('   (teste offline com dados locais)')
else:
    DF0, LAT = carregar()
DF = preparar(DF0)
COMP = teste_a(DF)
CV = teste_bc(DF)
FINAL = decidir(COMP, CV)
log('\nNada foi gravado no Earth Engine.')
z = shutil.make_archive(PASTA, 'zip', PASTA)
log(f'📦 {z}')
if not LOCAL:
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        log('   (baixe pelo painel Arquivos do Colab)')
