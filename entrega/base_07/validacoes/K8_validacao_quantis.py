# =========================================================================================
# 01 - VALIDAÇÃO K8 (SOMENTE LEITURA): Tmax/Tmin da previsão GFS - QUANTIS x ADITIVA
# Pergunta: corrigir a temperatura do GFS por mapeamento de quantis (decisão 8a) é melhor do que a
# correção aditiva pela média, FORA da amostra de treino?
#   - GFS v16 composto exatamente como o motor V1.4 (rodada 00Z, reamostragem bilinear por imagem,
#     Tmax/Tmin pela temperatura horária na janela 00-24 UTC do dia)
#   - Prazos 1, 3, 8 e 13 dias (um de cada faixa), em 1 dia a cada 3, de 08/04/2021 a 31/12/2025
#   - Pontos fixos sorteados entre os pixels com BR-DWGD
#   - TREINO: 08/04/2021 a 31/12/2024 (mês do dia e os dois vizinhos, para ter amostra parecida com a
#     da matriz, que usa todos os dias da faixa). TESTE: 2025 inteiro, que o treino não viu.
#   - Métodos: GFS bruto | aditiva (média) | quantis (percentis 5,10,25,50,75,90,95, como a matriz V2)
#   - Métricas no teste: viés, MAE, RMSE e frequência de extremos (dias quentes acima do p90 do
#     ponto, Tmax > 35 e > 40 °C; noites frias abaixo do p10, Tmin < 10 °C) prevista x observada
# Nada é gravado no Earth Engine. RODE SOZINHA: com outro script do projeto rodando ao mesmo tempo
# (etapas 2 ou 3), o Earth Engine recusa pedidos por excesso de cálculos simultâneos.
# (Versão 2, 20/10/2026 15h50: lotes de 6 previsões, espera e divisão automática quando o servidor recusa.)
# COMO RODAR: cole inteiro numa célula do Colab e rode. O log mostra o tempo restante; se parar,
# rode de novo (os lotes já baixados ficam no cache). No final baixa um zip com o resultado.
# =========================================================================================
import os, shutil, time, traceback, pickle, hashlib, warnings
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import ee

warnings.filterwarnings('ignore')

# ------------------------------- CONFIGURAÇÃO -------------------------------------------
PROJETO = 'clima-492922'
N_PONTOS = 300
PASSO_DIAS = 3
LEADS = [1, 3, 8, 13]
INICIO, FIM_TREINO, FIM = '2021-04-08', '2024-12-31', '2025-12-31'
PERCENTIS = [5, 10, 25, 50, 75, 90, 95]
USAR_DRIVE = False
# -----------------------------------------------------------------------------------------

BR_DWGD, GFS = 'projects/ee-alexandrexavier/assets/BR-DWGD', 'NOAA/GFS0P25'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
DIA_MS = 86400000

AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'validacao_K8_{AGORA:%Y%m%d_%H%M}')
CACHE = os.path.join(BASE, 'cache_validacao_K8')
if USAR_DRIVE:
    from google.colab import drive
    drive.mount('/content/drive')
    CACHE = '/content/drive/MyDrive/cache_validacao_K8'
os.makedirs(PASTA, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)
LOG = os.path.join(PASTA, 'LOG_K8.txt')


def log(*p):
    t = ' '.join(str(x) for x in p)
    print(t, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(t + '\n')


def tabela(df, titulo):
    log(f'\n   {titulo}')
    with pd.option_context('display.width', 250, 'display.max_columns', 40, 'display.max_rows', 200):
        for linha in df.to_string().splitlines():
            log('   ' + linha)


TRANSITORIOS = ('Too many concurrent', 'Internal error', '503', '429', 'deadline', 'Connection', 'temporarily',
                'Remote end closed')
PESADOS = ('Computation timed out', 'memory limit', 'User memory', 'capacity exceeded', 'aborted after accumulating',
           'Request payload size', 'too large')


def gi(obj, rot='', n=6):
    for t in range(n):
        try:
            return obj.getInfo()
        except Exception as e:
            # Excesso de cálculos simultâneos: uma nova tentativa só; depois o lote é dividido (buscar)
            if 'Too many concurrent' in str(e) and t >= 1:
                raise
            if t < n - 1 and any(k in str(e) for k in TRANSITORIOS) and not any(k in str(e) for k in PESADOS):
                espera = min(30 * (t + 1), 180)
                log(f'   ↻ {rot}: servidor ocupado ({str(e)[:40]}); nova tentativa em {espera} s')
                time.sleep(espera)
                continue
            raise


def buscar(lote, construir, rot, insistencias=3):
    """Pede um lote. Se o Earth Engine recusar por peso ou por excesso de cálculos simultâneos
    ('Too many concurrent aggregations'), divide o lote; um item sozinho espera 5 min e tenta de novo."""
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


log('=' * 100)
log(f'01 - VALIDAÇÃO K8: QUANTIS x ADITIVA (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
log('=' * 100)
try:
    ee.Initialize(project=PROJETO)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJETO)


def _bloq(*a, **k):
    raise RuntimeError('SOMENTE LEITURA: escrita bloqueada')


for _n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl', 'setAssetProperties',
           'createFolder', 'startProcessing', 'exportImage', 'exportTable', 'startIngestion', 'cancelTask'):
    if hasattr(ee.data, _n):
        setattr(ee.data, _n, _bloq)
ee.batch.Task.start = _bloq
log('🔒 Trava de somente leitura ativa.\n')

UF_BR = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
LIMITES = UF_BR.geometry().bounds()
MASC_BR = ee.Image.constant(1).clipToCollection(UF_BR).mask()
PROJ_SAB = ee.Projection(CRS, TRANSFORM)


def dia(col, d):
    return ee.Image(ee.ImageCollection(col).filterDate(d, ee.Date(d).advance(1, 'day')).first())


def ms(d):
    return int(pd.Timestamp(d).value // 10 ** 6)


def br_t(d):
    img = dia(BR_DWGD, d)
    valido = img.select('pr').gt(-32768)
    return ee.Image.cat([img.select('Tmax').multiply(0.00106815).add(15.0).rename('o_tmax'),
                         img.select('Tmin').multiply(0.00106815).add(15.0).rename('o_tmin')]).updateMask(valido)


def gfs_t(d, L):
    """Tmax/Tmin do GFS para o dia d, previsto L dias antes (00Z), igual ao motor V1.4."""
    criacao = ms(d) - (L - 1) * DIA_MS
    h0 = 24 * (L - 1)
    horas = [h for h in range(h0 + 1, h0 + 25) if h <= 120 or h % 3 == 0]
    dt = ee.Date(criacao)
    col = (ee.ImageCollection(GFS).filterDate(dt, dt.advance(1, 'hour'))
           .filter(ee.Filter.eq('creation_time', criacao))
           .filter(ee.Filter.gt('forecast_hours', h0)).filter(ee.Filter.lte('forecast_hours', h0 + 24))
           .map(lambda i: i.resample('bilinear')))
    ok = col.size().eq(len(horas))
    t = col.select('temperature_2m_above_ground')
    cheia = ee.Image.cat([t.max().rename('g_tmax'), t.min().rename('g_tmin')]).toFloat()
    vazia = ee.Image.constant([0, 0]).rename(['g_tmax', 'g_tmin']).toFloat().updateMask(ee.Image.constant(0))
    return ee.Image(ee.Algorithms.If(ok, cheia, vazia)), ok


arq_pts = os.path.join(CACHE, f'pontos_v2_{N_PONTOS}.pkl')
if os.path.exists(arq_pts):
    with open(arq_pts, 'rb') as f:
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
log(f'   {len(coords)} pontos fixos entre os pixels com BR-DWGD')


def construir(lote):
    fcs = []
    for d, L in lote:
        g, ok = gfs_t(d, L)
        img = ee.Image.cat([br_t(d), g])
        fcs.append(img.reduceRegions(collection=PONTOS, reducer=ee.Reducer.first(), crs=CRS, crsTransform=TRANSFORM,
                                     tileScale=4)
                   .map(lambda f: ee.Feature(None, f.toDictionary()).set({'dia': d, 'L': L, 'ok': ok})))
    return ee.FeatureCollection(fcs).flatten()


dias = [x.strftime('%Y-%m-%d') for x in pd.date_range(INICIO, FIM, freq=f'{PASSO_DIAS}D')]
itens = [(d, L) for d in dias for L in LEADS]
t0 = time.time()
# 6 previsões por pedido: lotes maiores esbarravam no limite de cálculos simultâneos do Earth Engine
df = em_lotes('K8', itens, construir, 6)
log(f'   download: {(time.time() - t0) / 60:.1f} min')
df = df[df['ok'].astype(float) > 0].dropna(subset=['o_tmax', 'o_tmin', 'g_tmax', 'g_tmin'])
df['data'] = pd.to_datetime(df['dia'])
df['mes'] = df['data'].dt.month
df['teste'] = df['data'] > pd.Timestamp(FIM_TREINO)
log(f'   {len(df):,} pares ponto-dia-prazo válidos ({df["teste"].sum():,} no teste de 2025)')
df.to_csv(os.path.join(PASTA, 'K8_dados_pontos.csv'), sep=';', decimal=',', index=False)


def qm(x, qg, qo):
    """Mapeamento de quantis linear por partes, com extrapolação constante da diferença nas pontas
    (a mesma conta que o motor V1.4 faz com a matriz V2)."""
    qg = np.maximum.accumulate(qg) + np.arange(len(qg)) * 1e-6
    return x + np.interp(x, qg, qo - qg, left=(qo - qg)[0], right=(qo - qg)[-1])


VIZ = {m: [((m - 2) % 12) + 1, m, (m % 12) + 1] for m in range(1, 13)}
linhas = []
treino_all = df[~df['teste']]
teste_all = df[df['teste']]
for (pid, L), te in teste_all.groupby(['pid', 'L']):
    tr_pl = treino_all[(treino_all['pid'] == pid) & (treino_all['L'] == L)]
    for m, te_m in te.groupby('mes'):
        tr = tr_pl[tr_pl['mes'].isin(VIZ[m])]
        if len(tr) < 30:
            continue
        out = te_m[['pid', 'L', 'mes', 'dia', 'o_tmax', 'o_tmin', 'g_tmax', 'g_tmin']].copy()
        for v in ('tmax', 'tmin'):
            o, g = tr[f'o_{v}'].values, tr[f'g_{v}'].values
            out[f'adi_{v}'] = te_m[f'g_{v}'] + (o.mean() - g.mean())
            out[f'qm_{v}'] = qm(te_m[f'g_{v}'].values, np.percentile(g, PERCENTIS), np.percentile(o, PERCENTIS))
            out[f'p90_{v}'] = np.percentile(o, 90)
            out[f'p10_{v}'] = np.percentile(o, 10)
        out['n_treino'] = len(tr)
        linhas.append(out)
r = pd.concat(linhas, ignore_index=True)
r.to_csv(os.path.join(PASTA, 'K8_previsoes_teste_2025.csv'), sep=';', decimal=',', index=False)
log(f'   {len(r):,} previsões avaliadas no teste; treino mediano de {int(r["n_treino"].median())} dias por ponto-prazo-mês')

res = []
for L, g in list(r.groupby('L')) + [('todos', r)]:
    for v in ('tmax', 'tmin'):
        o = g[f'o_{v}']
        for nome, col in (('GFS bruto', f'g_{v}'), ('aditiva', f'adi_{v}'), ('quantis', f'qm_{v}')):
            x = g[col]
            lin = {'prazo': L, 'var': v, 'metodo': nome, 'vies': (x - o).mean(), 'MAE': (x - o).abs().mean(),
                   'RMSE': np.sqrt(((x - o) ** 2).mean())}
            if v == 'tmax':
                lin.update({'freq_quente_prev': 100 * (x > g['p90_tmax']).mean(), 'freq_quente_obs': 100 * (o > g['p90_tmax']).mean(),
                            'pct35_prev': 100 * (x > 35).mean(), 'pct35_obs': 100 * (o > 35).mean(),
                            'pct40_prev': 100 * (x > 40).mean(), 'pct40_obs': 100 * (o > 40).mean()})
            else:
                lin.update({'freq_fria_prev': 100 * (x < g['p10_tmin']).mean(), 'freq_fria_obs': 100 * (o < g['p10_tmin']).mean(),
                            'pct10_prev': 100 * (x < 10).mean(), 'pct10_obs': 100 * (o < 10).mean()})
            res.append(lin)
t = pd.DataFrame(res)
for v in ('tmax', 'tmin'):
    tv = t[t['var'] == v].dropna(axis=1, how='all').set_index(['prazo', 'metodo']).drop(columns='var').round(3)
    tabela(tv, f'K8 - {v.upper()} no TESTE (2025, fora do treino): viés, MAE e RMSE em °C; frequências em % dos ponto-dias:')
    tv.to_csv(os.path.join(PASTA, f'K8_resultado_{v}.csv'), sep=';', decimal=',', encoding='utf-8-sig')

# Indicação: quantis só se reduzir bem o erro de frequência dos extremos sem piorar o MAE além de 0,10 °C
tt = t[t['prazo'] == 'todos'].set_index(['var', 'metodo'])
e_q = abs(tt.loc[('tmax', 'quantis'), 'freq_quente_prev'] - tt.loc[('tmax', 'quantis'), 'freq_quente_obs']) + \
      abs(tt.loc[('tmin', 'quantis'), 'freq_fria_prev'] - tt.loc[('tmin', 'quantis'), 'freq_fria_obs'])
e_a = abs(tt.loc[('tmax', 'aditiva'), 'freq_quente_prev'] - tt.loc[('tmax', 'aditiva'), 'freq_quente_obs']) + \
      abs(tt.loc[('tmin', 'aditiva'), 'freq_fria_prev'] - tt.loc[('tmin', 'aditiva'), 'freq_fria_obs'])
d_mae = max(tt.loc[('tmax', 'quantis'), 'MAE'] - tt.loc[('tmax', 'aditiva'), 'MAE'],
            tt.loc[('tmin', 'quantis'), 'MAE'] - tt.loc[('tmin', 'aditiva'), 'MAE'])
usar_q = (e_q <= 0.7 * e_a) and (d_mae <= 0.10)
log('\n' + '=' * 100)
log(f'RESULTADO: erro na frequência de extremos (quente + frio, pontos percentuais) quantis {e_q:.2f} x aditiva {e_a:.2f}; '
    f'MAE quantis - aditiva: {d_mae:+.3f} °C')
metodo = 'quantis' if usar_q else 'aditiva'
log(f'INDICAÇÃO: no motor (etapas 5a e 5b) use  METODO_TEMPERATURA = "{metodo}"')
log('   (regra: quantis só se reduzir o erro dos extremos em 30% ou mais e não piorar o MAE em mais de 0,10 °C)')
log('=' * 100)
pd.DataFrame([{'erro_extremos_quantis': e_q, 'erro_extremos_aditiva': e_a, 'dif_MAE': d_mae,
               'METODO_TEMPERATURA': metodo}]).to_csv(
    os.path.join(PASTA, 'K8_INDICACAO.csv'), sep=';', decimal=',', index=False)
log('Nada foi gravado no Earth Engine.')
z = shutil.make_archive(PASTA, 'zip', PASTA)
log(f'📦 {z}')
try:
    from google.colab import files
    files.download(z)
except Exception:
    log('   (baixe pelo painel Arquivos do Colab)')
