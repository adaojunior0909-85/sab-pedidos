# >>> VALIDAÇÃO K21 v4 (08/11/2026): a V1.6 revista (vento pela média) melhora os dias de 2026? Somente leitura. Cole inteiro, sem editar. <<<
# =========================================================================================
# K21 - VALIDAÇÃO FORA DA AMOSTRA DAS MUDANÇAS DO MOTOR V1.6 (etapa 2)
#
# PERGUNTA
#   As três mudanças do motor V1.6 nos dias de 2026 em diante deixam o dado mais perto do BR-DWGD, num período que a
#   calibração NÃO viu?
#     U  UR e vento pelo mapeamento empírico de quantis (EQM) x a correção só na média da V1.5
#     R  radiação limitada à de céu claro (FAO-56) x sem limite
#     C  teto da chuva (1,5 x o maior dia do BR-DWGD no pixel e mês) x sem teto
#     E  efeito na ETo (Penman-Monteith FAO-56, a mesma conta do motor) das três juntas
#   E ainda:
#     X  os dias de 2026 com mais de 400 mm (K19: até 546 mm): o que o teto faria com eles
#     G  a que horas a rodada 00Z do GFS fica completa no Earth Engine (para escolher o horário da rodada da manhã)
#
# v4 (08/11/2026): a v3a rodou (08/11, 16h33, 26 min) e reprovou SÓ o EQM do vento: erro diário -9,5% e desvios mais
#   perto, mas viés +0,085 -> +0,107 m/s, acima do limite de 0,10 m/s (o vento do BR-DWGD cai ao longo do tempo: 1,16 m/s
#   em 1986-2025 x 1,09 m/s em 2016-2025, e o treino do EQM é 1986-2015). UR, R, C, E e G passaram. O motor V1.6 foi
#   revisto: o vento dos dias ERA5 fica com a correção na média da V1.5 (METODO_VENTO_ERA5 = 'media'). Esta v4 avalia
#   ESSA versão com as MESMAS regras, dados, pontos e semente: U (só a UR), R, C e E (a ETo agora com o vento da V1.5).
#   O EQM do vento continua medido, só como informação (item V). Motor uma vez por dia às 23h07 (decisão de 08/11):
#   o item G vira informação (a rodada das 23h07 usa a 00Z do mesmo dia) e a única janela é 22h50-01h00.
#
# v2 (04/11, 18h40): a v1 parou no treino com "User memory limit exceeded": os percentis de 30 anos (930 imagens) dos
#   150 pontos e das duas fontes iam num pedido só, em blocos grandes. Agora cada mês pede o ERA5 e o BR-DWGD
#   separados, com tileScale 16 (blocos 16x menores), e, se o servidor ainda recusar, divide os pontos ao meio até
#   caber (como a K17 e a K19b). Contas, pontos e regras de aprovação sem mudança.
#
# v3a (04/11, 18h55): a v3 parou no primeiro pedido com "'Element' object has no attribute 'select'": no Python,
#   copyProperties devolve um Element, e o resultado do era_prep era usado como imagem. Agora toda função que copia
#   propriedades devolve ee.Image(...) (aqui e no 09). Só isso mudou.
# v3 (04/11, 18h50): a v2 também estourou a memória, mesmo com 2 pontos: o servidor não aguenta o percentil de 930
#   imagens num pedido interativo. Agora o treino NÃO usa percentil no servidor: lê os valores diários de 1986 a 2015
#   nos 150 pontos, um mês por pedido (o mesmo getRegion que a D5 da K19b usou sem problema), e calcula os quantis e o
#   maior dia em Python. Teste, pontos e regras de aprovação sem mudança.
#
# COMO (regra fixada ANTES de rodar)
#   150 pixels A (SAB igual ao BR-DWGD), sorteio fixo. Treino 1986-2015: quantis e maior dia de chuva calculados em
#   Python (v3) com a MESMA receita do 09 (era_prep e br_prep iguais aos do motor). Teste 2016-2025 (10 anos que o treino
#   não viu): ERA5 bruto do dia corrigido pela V1.5 e pela V1.6, comparado com o BR-DWGD do mesmo dia.
#   APROVADO por item (v4: a V1.6 revista = UR pelo EQM, vento pela média da V1.5, radiação <= Rso, teto da chuva):
#     U (UR): erro diário (MAE) do EQM <= 0,97 x o da V1.5 E desvio das anomalias mais perto do
#        BR-DWGD (|razão - 1| menor) E |viés| do EQM <= máx(|viés da V1.5|, 1,0 %).
#     V (vento pelo EQM): só informação na v4 (mesma conta da v3a, limite de viés 0,10 m/s).
#     R: MAE da radiação com o teto <= MAE sem o teto + 0,01 MJ/m² E nenhum pixel-dia acima de 1,001 Rso.
#     C: o teto pega no máximo 0,1% dos pixel-dias E o erro mensal da chuva não piora mais que 1%.
#     E: MAE da ETo da V1.6 revista (UR do EQM, vento da V1.5, radiação limitada) <= MAE da ETo da V1.5.
#   X e G são só informação (G: a que horas a rodada 00Z fica completa; a rodada única das 23h07 usa a do mesmo dia).
#   V1.6 APROVADA com U, R, C e E aprovados.
#
# COMO RODAR NO COLAB (fora da janela do motor, 22h50-01h00: comece até as 21h20 ou depois da 01h00)
#   Ambiente de execução -> Reiniciar sessão -> cole inteiro -> Ctrl+Enter. Tempo: ~30 min (a v3a levou 26 min). Somente leitura:
#   as funções de escrita do Earth Engine ficam bloqueadas. No fim, baixa validacao_K21_<data>.zip. Me envie.
# =========================================================================================
import math
import os
import shutil
import time
import traceback
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

PROJETO = 'clima-492922'
ASSET_MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
ASSET_CLIMA = f'projects/{PROJETO}/assets/SICSB_1986_2025'
ASSET_SAB = f'projects/{PROJETO}/assets/SAB_V1'
BR_DWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
GFS = 'NOAA/GFS0P25'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
X0, Y0, DX = TRANSFORM[2], TRANSFORM[5], TRANSFORM[0]
REGIAO_COORDS = [-75.0, -35.0, -28.0, 6.5]

N_PONTOS = 150
SEMENTE = 21
TREINO = (1986, 2015)
TESTE = (2016, 2025)
NIVEIS_EQM = tuple(range(0, 101, 5))
FATOR_MAX = 5.0                    # teto do fator da média na rota ERA5 (motor V1.2 em diante)
FATOR_TETO_CHUVA = 1.5             # motor V1.6
CHUVA_DIA = 1.0                    # mm: dia com chuva
LIMIAR_X = 400.0                   # mm: dias extremos de 2026 investigados (K19)
DIAS_GFS = 20                      # rodadas 00Z olhadas na parte G
HORA_UTC_MANHA = 9                 # 09h UTC = 06h de Brasília (cron '7 9 * * *')
JANELAS_MOTOR = [((22, 50), (24, 0)), ((0, 0), (1, 0))]     # [v4] motor 1x por dia às 23h07 (GitHub ~23h47)
DURACAO_ESTIMADA_MIN = 90                                    # [v4] a v3a levou 26 min

BRT = timezone(timedelta(hours=-3))
AGORA = datetime.now(BRT)
PASTA = (f'/content/validacao_K21_{AGORA:%Y%m%d_%H%M%S}' if os.path.isdir('/content')
         else f'validacao_K21_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K21.txt')
RESULTADOS = []


def log(*partes):
    texto = ' '.join(str(p) for p in partes)
    print(texto)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(texto + '\n')


def resultado(item, status, titulo, texto):
    RESULTADOS.append({'item': item, 'status': status, 'titulo': titulo, 'texto': texto})
    simb = {'APROVADO': '✅', 'REPROVADO': '❌', 'INFO': 'ℹ️', 'FALHOU': '⚠️'}.get(status, '•')
    log(f'{simb} {item} {status}: {titulo}\n   {texto}')


def salvar_csv(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=False)


# =========================================================================================
# FUNÇÕES PURAS (testadas offline em testes/teste_k21.py)
# =========================================================================================
def minutos_ate_janela(agora):
    m = agora.hour * 60 + agora.minute
    melhor = None
    for (h1, m1), (h2, m2) in JANELAS_MOTOR:
        ini, fim = h1 * 60 + m1, h2 * 60 + m2
        if ini <= m < fim:
            return 0
        falta = (ini - m) % (24 * 60)
        melhor = falta if melhor is None else min(melhor, falta)
    return melhor


def eqm(x, qm, qo):
    """O mesmo algoritmo do aplicar_eqm do motor V1.6, em NumPy: o último segmento cujo início é <= x; abaixo do 1º
    e acima do último quantil, desloca pela diferença do quantil extremo."""
    x = np.asarray(x, float)
    qm, qo = np.asarray(qm, float), np.asarray(qo, float)
    y = x + (qo[0] - qm[0])
    for k in range(len(qm) - 1):
        larg = max(qm[k + 1] - qm[k], 1e-6)
        seg = qo[k] + (x - qm[k]) * (qo[k + 1] - qo[k]) / larg
        y = np.where(x >= qm[k], seg, y)
    return np.where(x > qm[-1], x + (qo[-1] - qm[-1]), y)


def ra_rso(lat_graus, doy, z):
    """Ra e Rso (MJ/m²/dia), FAO-56 eq. 21 e 37, como o motor (dr, delta, ws com as mesmas constantes)."""
    lat = np.radians(np.asarray(lat_graus, float))
    J = np.asarray(doy, float)
    dr = 1 + 0.033 * np.cos(2 * math.pi / 365 * J)
    d = 0.409 * np.sin(2 * math.pi / 365 * J - 1.39)
    ws = np.arccos(np.clip(-np.tan(lat) * np.tan(d), -1, 1))
    ra = 24 * 60 / math.pi * 0.0820 * dr * (ws * np.sin(lat) * np.sin(d) + np.cos(lat) * np.cos(d) * np.sin(ws))
    return ra, (0.75 + 2e-5 * np.asarray(z, float)) * ra


def es(t):
    return 0.6108 * np.exp(17.625 * t / (t + 243.04))


def eto_pm(tmax, tmin, rh, u2, rs, lat, doy, z):
    """ETo FAO-56 Penman-Monteith com as mesmas fórmulas do eto_penman_monteith do motor."""
    tmax, tmin, rh, u2, rs = (np.asarray(v, float) for v in (tmax, tmin, rh, u2, rs))
    _, rso = ra_rso(lat, doy, z)
    p = 101.3 * ((293.0 - 0.0065 * np.asarray(z, float)) / 293.0) ** 5.26
    gama = 0.000665 * p
    tm = (tmax + tmin) / 2
    esat = (es(tmax) + es(tmin)) / 2
    ea = esat * rh / 100
    vpd = np.maximum(esat - ea, 0)
    rs_rso = np.clip(rs / rso, 0, 1)
    rnl = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * rs_rso - 0.35)
    rn = 0.77 * rs - np.maximum(rnl, 0)
    delta = 4283.58 * es(tm) / (tm + 243.04) ** 2
    num = 0.408 * delta * rn + gama * (900 / (tm + 273)) * u2 * vpd
    return np.maximum(num / (delta + gama * (1 + 0.34 * u2)), 0)


def metricas_continua(sim, obs, grupo):
    df = pd.DataFrame({'s': np.asarray(sim, float), 'o': np.asarray(obs, float), 'g': np.asarray(grupo)}).dropna()
    an_s = df['s'] - df.groupby('g')['s'].transform('mean')
    an_o = df['o'] - df.groupby('g')['o'].transform('mean')
    return {'n': int(len(df)), 'vies': float((df['s'] - df['o']).mean()), 'mae': float((df['s'] - df['o']).abs().mean()),
            'razao_desvio': float(an_s.std() / an_o.std()) if an_o.std() > 0 else float('nan'),
            'p01_dif': float(np.percentile(df['s'], 1) - np.percentile(df['o'], 1)),
            'p99_dif': float(np.percentile(df['s'], 99) - np.percentile(df['o'], 99)),
            'correlacao': float(df['s'].corr(df['o']))}


def metricas_chuva(sim, obs, chave_mes):
    sim, obs = np.asarray(sim, float), np.asarray(obs, float)
    ok = ~(np.isnan(sim) | np.isnan(obs))
    sim, obs, chave = sim[ok], obs[ok], np.asarray(chave_mes)[ok]
    mens = pd.DataFrame({'k': chave, 's': sim, 'o': obs}).groupby('k').sum()
    return {'n': int(len(sim)), 'vies_pct': float(100 * (sim.sum() - obs.sum()) / obs.sum()),
            'mae': float(np.abs(sim - obs).mean()), 'erro_mensal_mm': float((mens['s'] - mens['o']).abs().mean()),
            'max_sim': float(sim.max()), 'max_obs': float(obs.max()),
            'freq_chuva_sim': float(100 * (sim >= CHUVA_DIA).mean()), 'freq_chuva_obs': float(100 * (obs >= CHUVA_DIA).mean())}


def quantis_treino(dados):
    """[v3] Por pixel e mês: os 21 quantis (0, 5, ..., 100%) da UR e do vento do ERA5 bruto e do BR-DWGD, e o maior
    dia de chuva do BR-DWGD. Mesmas bandas que a matriz do 09 (RH_era_p000 ... u2_br_p100, pr_max_br)."""
    d = dados.copy()
    for c in ('era_rh', 'br_rh', 'era_u2', 'br_u2', 'br_pr'):
        d[c] = pd.to_numeric(d[c], errors='coerce')
    d['mes'] = d['data'].str[5:7].astype(int)
    q = np.array(NIVEIS_EQM) / 100.0
    linhas = []
    for (pid, mes), g in d.groupby(['pid', 'mes']):
        r = {'pid': pid, 'mes': mes}
        for v, col in (('RH', 'rh'), ('u2', 'u2')):
            for fonte in ('era', 'br'):
                x = g[f'{fonte}_{col}'].dropna().values
                vals = np.quantile(x, q) if len(x) >= 60 else [np.nan] * len(q)
                for p, val in zip(NIVEIS_EQM, vals):
                    r[f'{v}_{fonte}_p{p:03d}'] = float(val)
        pr = g['br_pr'].dropna()
        r['pr_max_br'] = float(pr.max()) if len(pr) else np.nan
        linhas.append(r)
    return pd.DataFrame(linhas)


def decidir_u(atual, novo, var):
    """Regra do item U para uma variável (dicionários de metricas_continua)."""
    lim_vies = {'RH': 1.0, 'u2': 0.10}[var]
    c1 = novo['mae'] <= 0.97 * atual['mae']
    c2 = abs(novo['razao_desvio'] - 1) < abs(atual['razao_desvio'] - 1)
    c3 = abs(novo['vies']) <= max(abs(atual['vies']), lim_vies)
    return c1 and c2 and c3, {'mae_97': c1, 'desvio_mais_perto': c2, 'vies_ok': c3}


def decidir_r(mae_sem, mae_com, n_acima_com):
    return mae_com <= mae_sem + 0.01 and n_acima_com == 0


def decidir_c(frac_teto, erro_mensal_sem, erro_mensal_com):
    return frac_teto <= 0.001 and erro_mensal_com <= 1.01 * erro_mensal_sem


def latencia_gfs(rodadas):
    """rodadas: lista de (creation_ms, n_imagens, max_system_version_us). Devolve DataFrame com a hora UTC em que cada
    rodada 00Z completa (208 saídas ou mais) terminou de chegar, em horas depois das 00Z."""
    linhas = []
    for cms, n, ver in rodadas:
        if not cms or not ver:
            continue
        linhas.append({'rodada': datetime.fromtimestamp(cms / 1000, timezone.utc).strftime('%Y-%m-%d'),
                       'n_imagens': int(n), 'completa': int(n) >= 208,
                       'horas_apos_00z': (ver / 1000 - cms) / 3.6e6})
    return pd.DataFrame(linhas)


def decidir_g(tab, hora_utc=HORA_UTC_MANHA):
    """Aprovado se em >= 90% das rodadas completas a última imagem chegou antes de hora_utc. Devolve
    (aprovado, p90 em horas, hora UTC segura sugerida)."""
    c = tab[tab['completa']] if len(tab) else tab
    if len(c) < 5:
        return False, float('nan'), None
    p90 = float(np.percentile(c['horas_apos_00z'], 90))
    segura = int(math.ceil(p90 + 0.5))
    return p90 <= hora_utc, p90, segura


# =========================================================================================
def principal():
    import ee
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log('=' * 100)
    log(f'K21 v4: VALIDAÇÃO FORA DA AMOSTRA DO MOTOR V1.6 REVISTO (vento pela média; somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log(f'   treino {TREINO[0]}-{TREINO[1]} | teste {TESTE[0]}-{TESTE[1]} | {N_PONTOS} pixels A | quantis {len(NIVEIS_EQM)}')
    log('=' * 100)
    falta = minutos_ate_janela(AGORA)
    if falta < DURACAO_ESTIMADA_MIN:
        log(f'⛔ Não comecei: a próxima janela do motor começa em {falta} min e a K21 pode levar até '
            f'{DURACAO_ESTIMADA_MIN} min. Comece até as 21h20 ou depois da 01h00.')
        return
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K21 é somente leitura: escrita bloqueada')
    for n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
              'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable', 'startIngestion',
              'cancelTask'):
        if hasattr(ee.data, n):
            setattr(ee.data, n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa (criar, apagar, exportar e cancelar bloqueados).\n')

    PROJ = ee.Projection(CRS, TRANSFORM)
    REGIAO = ee.Geometry.Rectangle(REGIAO_COORDS, None, False)
    CLASSE = ee.Image(ASSET_MASCARA).select('classe')
    TRANS = ('Too many concurrent', 'Internal error', 'Service Unavailable', '503', '429', 'deadline', 'Deadline',
             'Connection', 'temporarily')

    class Pesado(Exception):
        pass

    def gi(obj, rotulo, tentativas=6):
        for t in range(tentativas):
            try:
                return obj.getInfo()
            except Exception as e:
                s = str(e)
                if 'memory' in s.lower() or 'timed out' in s.lower() or 'too many pixels' in s.lower():
                    raise Pesado(s)
                if t < tentativas - 1 and any(k in s for k in TRANS):
                    log(f'   ↻ {rotulo}: erro transitório; nova tentativa em {20 * (t + 1)} s')
                    time.sleep(20 * (t + 1))
                    continue
                raise

    # --- preparo: o MESMO do 09 e do motor V1.6
    def era_prep(img):
        t2m = img.select('temperature_2m').subtract(273.15).resample('bilinear')
        tdew = img.select('dewpoint_temperature_2m').subtract(273.15).resample('bilinear')
        rh = t2m.expression('100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))',
                            {'T': t2m, 'Td': tdew}).rename('RH')
        u2 = img.select('u_component_of_wind_10m').hypot(img.select('v_component_of_wind_10m')) \
            .multiply(0.748).resample('bilinear').rename('u2')
        return ee.Image(ee.Image.cat([rh, u2]).copyProperties(img, ['system:time_start']))   # ee.Image: copyProperties devolve Element

    def br_prep(img):
        valido = (img.select('pr').gt(-32768).And(img.select('Tmax').gt(-32768)).And(img.select('Tmin').gt(-32768)))
        rh = img.select('RH').updateMask(img.select('RH').gt(-32768)).multiply(0.39370079).add(-0.393701) \
            .clamp(0, 100).rename('RH')
        u2 = img.select('u2').updateMask(img.select('u2').gt(-32768)).multiply(0.05905512).add(-0.059055) \
            .max(0).rename('u2')
        pr = img.select('pr').multiply(0.00686666).add(225.0).max(0).rename('pr')
        return ee.Image(ee.Image.cat([rh, u2, pr]).updateMask(valido).copyProperties(img, ['system:time_start']))

    def era_dia(img):
        """Bruto do ERA5 do dia, como o motor lê antes de calibrar (chuva, Tmax, Tmin, UR, vento e radiação)."""
        p = era_prep(img)
        return ee.Image(ee.Image.cat([
            img.select('total_precipitation_sum').multiply(1000).max(0).rename('era_pr'),
            img.select('temperature_2m_max').subtract(273.15).resample('bilinear').rename('era_tmax'),
            img.select('temperature_2m_min').subtract(273.15).resample('bilinear').rename('era_tmin'),
            p.select('RH').rename('era_rh'), p.select('u2').rename('era_u2'),
            img.select('surface_solar_radiation_downwards_sum').divide(1e6).resample('bilinear').rename('era_rs'),
        ]).copyProperties(img, ['system:time_start']))

    def br_dia(img):
        m = img.select('pr').gt(-32768).And(img.select('Tmax').gt(-32768)).And(img.select('Tmin').gt(-32768))
        dec = lambda b, e, a: img.select(b).updateMask(m).multiply(e).add(a)
        return ee.Image(ee.Image.cat([dec('pr', 0.00686666, 225.0).max(0).rename('br_pr'),
                             dec('Tmax', 0.00106815, 15.0).rename('br_tmax'),
                             dec('Tmin', 0.00106815, 15.0).rename('br_tmin'),
                             dec('RH', 0.39370079, -0.393701).clamp(0, 100).rename('br_rh'),
                             dec('u2', 0.05905512, -0.059055).max(0).rename('br_u2'),
                             dec('Rs', 0.15708661, -0.057087).max(0).rename('br_rs'),
                             dec('ET', 0.05118110, -0.0511811).max(0).rename('br_et')]
                            ).copyProperties(img, ['system:time_start']))

    # ------------------------------------------------------------------ pontos
    sorteio = (ee.Image.pixelLonLat().addBands(CLASSE)
               .stratifiedSample(numPoints=0, classBand='classe', region=REGIAO, projection=PROJ, seed=SEMENTE,
                                 classValues=[1], classPoints=[N_PONTOS], geometries=True, tileScale=4))
    pts = [{'pid': k, 'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1]}
           for k, f in enumerate(gi(sorteio, 'pontos')['features'])]
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']}) for p in pts])
    elev = gi(ee.Image('USGS/SRTMGL1_003').rename('z').sampleRegions(collection=fc, properties=['pid'], scale=11132,
                                                                      geometries=False), 'altitude')
    z = {f['properties']['pid']: f['properties'].get('z', 0) or 0 for f in elev['features']}
    for p in pts:
        p['z'] = z.get(p['pid'], 0)
    pontos = pd.DataFrame(pts)
    salvar_csv(pontos, 'K21_pontos.csv')
    chave = {(int(math.floor((p['lon'] - X0) / DX + 1e-6)), int(math.floor((Y0 - p['lat']) / DX + 1e-6))): p['pid']
             for p in pts}
    log(f'   {len(pts)} pixels A sorteados (semente {SEMENTE}); altitude média {pontos["z"].mean():.0f} m')

    # ------------------------------------------------------------------ treino: quantis e maior dia, por mês
    feats = [ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']}) for p in pts]

    def amostrar(img, lista, rotulo):
        """[v2] sampleRegions com tileScale 16; se o servidor recusar por memória, divide os pontos ao meio."""
        try:
            r = gi(img.sampleRegions(collection=ee.FeatureCollection(lista), properties=['pid'], projection=PROJ,
                                     geometries=False, tileScale=16), rotulo)
            return [f['properties'] for f in r['features']]
        except Pesado:
            if len(lista) <= 2:
                raise
            meio = len(lista) // 2
            log(f'   {rotulo}: pesado, dividindo os pontos ({len(lista)} -> {meio} + {len(lista) - meio})')
            return amostrar(img, lista[:meio], rotulo) + amostrar(img, lista[meio:], rotulo)

    # médias da matriz que a V1.5 usa
    bandas_m = [f'{b}_m_{f}' for b in ('pr', 'Tmax', 'Tmin', 'RH', 'Rs', 'u2') for f in ('br', 'era')]
    mats = ee.Image.cat([ee.Image(f'{ASSET_CLIMA}/Matriz_Clima_{m:02d}').select(bandas_m)
                         .rename([f'{b}__{m}' for b in bandas_m]) for m in range(1, 13)])
    mm = []
    for p in amostrar(mats, feats, 'matriz V1.5'):
        for m in range(1, 13):
            mm.append({'pid': p['pid'], 'mes': m, **{b: p.get(f'{b}__{m}') for b in bandas_m}})
    medias = pd.DataFrame(mm)

    # ------------------------------------------------------------------ teste: dias de 2016-2025
    log(f'\n[dias] ERA5 bruto e BR-DWGD por dia, {TREINO[0]}-{TESTE[1]} (480 pedidos, um por mês): treino '
        f'{TREINO[0]}-{TREINO[1]}, teste {TESTE[0]}-{TESTE[1]}')
    ERACOL, BRCOL = ee.ImageCollection(ERA5), ee.ImageCollection(BR_DWGD)

    def regiao(ini, fim, lista, rotulo):
        par = ee.Join.inner().apply(ERACOL.filterDate(ini, fim).map(lambda i: ee.Image(era_dia(i))),
                                    BRCOL.filterDate(ini, fim).map(lambda i: ee.Image(br_dia(i))),
                                    ee.Filter.maxDifference(difference=12 * 3600 * 1000, leftField='system:time_start',
                                                            rightField='system:time_start'))
        junto = ee.ImageCollection(par.map(lambda f: ee.Image.cat([ee.Image(f.get('primary')), ee.Image(f.get('secondary'))])
                                           .set('system:time_start', ee.Image(f.get('primary')).get('system:time_start'))))
        try:
            return gi(junto.getRegion(ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in lista]), None, CRS, TRANSFORM),
                      rotulo)
        except Pesado:
            if len(lista) <= 10:
                raise
            meio = len(lista) // 2
            log(f'   {rotulo}: pesado, dividindo os pontos ({len(lista)} -> {meio} + {len(lista) - meio})')
            a, b = regiao(ini, fim, lista[:meio], rotulo), regiao(ini, fim, lista[meio:], rotulo)
            return a + b[1:]

    quadros = []
    for ano in range(TREINO[0], TESTE[1] + 1):           # [v3] treino e teste lidos do mesmo jeito
        linhas, cab = [], None
        for mes in range(1, 13):
            ini = f'{ano}-{mes:02d}-01'
            fim = f'{ano + 1}-01-01' if mes == 12 else f'{ano}-{mes + 1:02d}-01'
            reg = regiao(ini, fim, pts, f'dias {ano}-{mes:02d}')
            cab = reg[0]
            linhas += reg[1:]
        df = pd.DataFrame(linhas, columns=cab)
        ix = np.floor((df['longitude'].astype(float) - X0) / DX + 1e-6).astype(int)
        iy = np.floor((Y0 - df['latitude'].astype(float)) / DX + 1e-6).astype(int)
        df['pid'] = [chave.get((a, b)) for a, b in zip(ix, iy)]
        df['data'] = pd.to_datetime(df['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
        df = df.dropna(subset=['pid'])
        quadros.append(df.drop(columns=['id', 'longitude', 'latitude', 'time'], errors='ignore'))
        log(f'   {ano}: {len(df)} pixel-dias')
    dados = pd.concat(quadros, ignore_index=True)
    dados['pid'] = dados['pid'].astype(int)
    ano_d = dados['data'].str[:4].astype(int)
    treino = quantis_treino(dados[ano_d <= TREINO[1]])                # [v3] quantis e maior dia em Python
    salvar_csv(treino, 'K21_treino_quantis.csv')
    log(f'   treino: {len(treino)} combinações pixel-mês com quantis')
    avaliar(dados[ano_d >= TESTE[0]].reset_index(drop=True), treino, medias, pontos)

    # ------------------------------------------------------------------ X: dias de 2026 acima de 400 mm
    log(f'\n[X] dias de 2026 com chuva acima de {LIMIAR_X:.0f} mm no SAB (pixels A)')
    try:
        sab26 = ee.ImageCollection(ASSET_SAB).filterDate('2026-01-01', '2027-01-01')
        mx = sab26.select('pr_mm').max().updateMask(CLASSE.eq(1))
        alvo = mx.updateMask(mx.gt(LIMIAR_X)).rename('pr_max_2026')
        cand = gi(alvo.sample(region=REGIAO, projection=PROJ, geometries=True, numPixels=1e6, tileScale=4).limit(40),
                  'pixels acima do limiar')
        lista = [{'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1]}
                 for f in cand['features']]
        if not lista:
            resultado('X', 'INFO', f'nenhum pixel A de 2026 acima de {LIMIAR_X:.0f} mm', 'nada a investigar')
        else:
            mp = ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in lista])
            maxbr = ee.Image.cat([ee.ImageCollection(BR_DWGD).filter(ee.Filter.calendarRange(1986, 2025, 'year'))
                                  .filter(ee.Filter.calendarRange(m, m, 'month')).map(br_prep).select('pr').max()
                                  .rename(f'max_{m:02d}') for m in range(1, 13)])
            rmax = gi(maxbr.reduceRegions(collection=ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]))
                                                                            for p in lista]),
                                          reducer=ee.Reducer.first(), crs=CRS, crsTransform=TRANSFORM), 'maior dia BR')
            par = ee.Join.inner().apply(
                sab26.select(['pr_mm'], ['sab_pr']),
                ee.ImageCollection(ERA5).filterDate('2026-01-01', '2027-01-01').map(
                    lambda i: ee.Image(i.select('total_precipitation_sum').multiply(1000).max(0).rename('era_pr')
                    .copyProperties(i, ['system:time_start']))),
                ee.Filter.maxDifference(difference=12 * 3600 * 1000, leftField='system:time_start',
                                        rightField='system:time_start'))
            junto = ee.ImageCollection(par.map(lambda f: ee.Image.cat([ee.Image(f.get('primary')), ee.Image(f.get('secondary'))])
                                               .set('system:time_start', ee.Image(f.get('primary')).get('system:time_start'))))
            reg = gi(junto.filter(ee.Filter.notNull(['system:time_start'])).getRegion(mp, None, CRS, TRANSFORM), 'dias 2026')
            df = pd.DataFrame(reg[1:], columns=reg[0])
            df = df[df['sab_pr'].astype(float) > LIMIAR_X].copy()
            df['data'] = pd.to_datetime(df['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
            mx_por_ponto = {}
            for f, p in zip(rmax['features'], lista):
                mx_por_ponto[(round(p['lon'], 4), round(p['lat'], 4))] = f['properties']
            linhas = []
            for _, r in df.iterrows():
                k = min(mx_por_ponto, key=lambda c: (c[0] - float(r['longitude'])) ** 2 + (c[1] - float(r['latitude'])) ** 2)
                mes = int(r['data'][5:7])
                mbr = mx_por_ponto[k].get(f'max_{mes:02d}')
                era = float(r['era_pr']) if r['era_pr'] is not None else float('nan')
                teto = max(era, FATOR_TETO_CHUVA * mbr) if mbr is not None else float('nan')
                linhas.append({'data': r['data'], 'lon': float(r['longitude']), 'lat': float(r['latitude']),
                               'sab_v15_mm': float(r['sab_pr']), 'era5_bruto_mm': era, 'maior_dia_br_mm': mbr,
                               'teto_v16_mm': teto, 'v16_mm': min(float(r['sab_pr']), teto) if teto == teto else float('nan')})
            tx = pd.DataFrame(linhas).sort_values('sab_v15_mm', ascending=False)
            salvar_csv(tx, 'K21_X_chuva_2026_acima_400mm.csv')
            if len(tx):
                log(tx.head(15).to_string(index=False))
                top = tx.iloc[0]
                resultado('X', 'INFO', f'{len(tx)} pixel-dias de 2026 acima de {LIMIAR_X:.0f} mm',
                          f'o maior: {top["sab_v15_mm"]:.0f} mm em {top["data"]} ({top["lon"]:.2f}; {top["lat"]:.2f}); '
                          f'ERA5 bruto {top["era5_bruto_mm"]:.0f} mm; maior dia do BR-DWGD no mês {top["maior_dia_br_mm"]:.0f} mm; '
                          f'com a V1.6: {top["v16_mm"]:.0f} mm')
            else:
                resultado('X', 'INFO', 'pixels acima do limiar sem dia correspondente', 'conferir à mão')
    except Exception as e:
        resultado('X', 'FALHOU', 'investigação dos dias extremos de 2026', str(e)[:300])

    # ------------------------------------------------------------------ G: latência do GFS 00Z
    log(f'\n[G] a que horas a rodada 00Z do GFS fica completa no Earth Engine (últimas {DIAS_GFS})')
    try:
        hoje = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cms = [int((hoje - timedelta(days=k)).timestamp() * 1000) for k in range(1, DIAS_GFS + 1)]
        col = ee.ImageCollection(GFS)
        info = gi(ee.List([ee.List([c, col.filter(ee.Filter.eq('creation_time', c)).size(),
                                    col.filter(ee.Filter.eq('creation_time', c)).aggregate_max('system:version')])
                           for c in cms]), 'rodadas GFS')
        tab = latencia_gfs(info)
        salvar_csv(tab, 'K21_G_latencia_gfs.csv')
        log(tab.to_string(index=False))
        ok, p90, segura = decidir_g(tab)
        texto = (f'p90: a rodada 00Z completa chega {p90:.1f} h depois das 00Z ({(p90 - 3) % 24:.1f} h de Brasília); '
                 f'a rodada única das 23h07 (02h07 UTC do dia seguinte) usa a 00Z do mesmo dia, completa ~'
                 f'{26.1 - p90:.0f} h antes') if p90 == p90 else 'poucas rodadas'
        resultado('G', 'INFO', 'horário da rodada 00Z do GFS (motor às 23h07)', texto)   # [v4] só informação
    except Exception as e:
        resultado('G', 'FALHOU', 'latência do GFS', str(e)[:300])

    fechar(T0)


def avaliar(dados, treino, medias, pontos):
    """Corrige o ERA5 do teste pela V1.5 e pela V1.6 e compara com o BR-DWGD (itens U, R, C e E)."""
    d = dados.copy()
    for c in d.columns:
        if c not in ('data',):
            d[c] = pd.to_numeric(d[c], errors='coerce')
    d['mes'] = d['data'].str[5:7].astype(int)
    d['doy'] = pd.to_datetime(d['data']).dt.dayofyear
    d = d.merge(medias, on=['pid', 'mes'], how='left').merge(treino, on=['pid', 'mes'], how='left') \
        .merge(pontos[['pid', 'lat', 'z']], on='pid', how='left')
    fat = lambda b: (d[f'{b}_m_br'] / d[f'{b}_m_era'].clip(lower=1e-3)).clip(upper=FATOR_MAX)
    # V1.5 (_componentes_era5)
    d['v15_pr'] = (d['era_pr'] * fat('pr')).clip(lower=0)
    d['v15_tmax'] = d['era_tmax'] + (d['Tmax_m_br'] - d['Tmax_m_era'])
    d['v15_tmin'] = d['era_tmin'] + (d['Tmin_m_br'] - d['Tmin_m_era'])
    d['v15_rh'] = (d['era_rh'] + (d['RH_m_br'] - d['RH_m_era'])).clip(0, 100)
    d['v15_u2'] = (d['era_u2'] * fat('u2')).clip(lower=0)
    d['v15_rs'] = (d['era_rs'] * fat('Rs')).clip(lower=0)
    # V1.6 revista [v4]: UR pelo EQM; vento da V1.5 (eqm_u2 = o EQM do vento, só informação)
    d['v16_rh'], d['eqm_u2'] = d['v15_rh'], d['v15_u2']
    for v, col, dest in (('RH', 'rh', 'v16_rh'), ('u2', 'u2', 'eqm_u2')):
        qm_c = [f'{v}_era_p{p:03d}' for p in NIVEIS_EQM]
        qo_c = [f'{v}_br_p{p:03d}' for p in NIVEIS_EQM]
        ok = d[qm_c + qo_c].notna().all(axis=1) & d[f'era_{col}'].notna()
        for _, idx in d[ok].groupby(['pid', 'mes']).groups.items():   # quantis iguais no grupo: uma chamada só
            linha = d.loc[idx[0]]
            d.loc[idx, dest] = eqm(d.loc[idx, f'era_{col}'].values, linha[qm_c].values.astype(float),
                                   linha[qo_c].values.astype(float))
    d['v16_rh'] = d['v16_rh'].clip(0, 100)
    d['eqm_u2'] = d['eqm_u2'].clip(lower=0)
    d['v16_u2'] = d['v15_u2']                              # [v4] METODO_VENTO_ERA5 = 'media' no motor
    _, rso = ra_rso(d['lat'], d['doy'], d['z'])
    d['rso'] = rso
    d['v16_rs'] = np.minimum(d['v15_rs'], d['rso'])
    teto = np.maximum(d['era_pr'], FATOR_TETO_CHUVA * d['pr_max_br'])
    d['v16_pr'] = np.where(d['pr_max_br'].notna(), np.minimum(d['v15_pr'], teto), d['v15_pr'])
    d['teto_pegou'] = d['v16_pr'] < d['v15_pr'] - 1e-9
    for v in ('15', '16'):
        d[f'v{v}_eto'] = eto_pm(d['v15_tmax'], d['v15_tmin'], d[f'v{v}_rh'], d[f'v{v}_u2'], d[f'v{v}_rs'], d['lat'],
                                d['doy'], d['z'])
    d['eqm_eto'] = eto_pm(d['v15_tmax'], d['v15_tmin'], d['v16_rh'], d['eqm_u2'], d['v16_rs'], d['lat'], d['doy'], d['z'])
    grupo = d['pid'].astype(str) + '_' + d['data'].str[:7]
    linhas = []
    rot = {'v15': 'V1.5', 'v16': 'V1.6', 'eqm': 'EQM no vento (info)'}
    for nome, a, b in (('UR', 'v15_rh', 'br_rh'), ('UR', 'v16_rh', 'br_rh'), ('vento', 'v15_u2', 'br_u2'),
                       ('vento', 'eqm_u2', 'br_u2'), ('radiação', 'v15_rs', 'br_rs'), ('radiação', 'v16_rs', 'br_rs'),
                       ('ETo', 'v15_eto', 'br_et'), ('ETo', 'v16_eto', 'br_et'), ('ETo', 'eqm_eto', 'br_et')):
        linhas.append({'variavel': nome, 'versao': rot[a[:3]], **metricas_continua(d[a], d[b], grupo)})
    tab = pd.DataFrame(linhas)
    chuva = pd.DataFrame([{'versao': v, **metricas_chuva(d[col], d['br_pr'], grupo)}
                          for v, col in (('V1.5', 'v15_pr'), ('V1.6', 'v16_pr'))])
    salvar_csv(tab.round(4), 'K21_metricas_teste.csv')
    salvar_csv(chuva.round(4), 'K21_metricas_chuva.csv')
    salvar_csv(d.sample(min(len(d), 20000), random_state=1).round(4), 'K21_amostra_dias.csv')
    log('\n' + tab.round(3).to_string(index=False))
    log('\n' + chuva.round(3).to_string(index=False))
    t = tab.set_index(['variavel', 'versao'])
    for item, nome, var, nova in (('U', 'UR', 'RH', 'V1.6'), ('V', 'vento', 'u2', 'EQM no vento (info)')):
        a, n = t.loc[(nome, 'V1.5')], t.loc[(nome, nova)]
        ok, c = decidir_u(a, n, var)
        c = {k: bool(v) for k, v in c.items()}
        texto = (f'erro diário {a["mae"]:.3f} -> {n["mae"]:.3f} ({100 * (n["mae"] / a["mae"] - 1):+.1f}%); desvios '
                 f'x{a["razao_desvio"]:.2f} -> x{n["razao_desvio"]:.2f} do BR-DWGD; viés {a["vies"]:+.2f} -> {n["vies"]:+.2f} '
                 f'| critérios {c}')
        if item == 'U':
            resultado('U', 'APROVADO' if ok else 'REPROVADO', f'{nome}: EQM x correção só na média', texto)
        else:                                               # [v4] o motor revisto não usa o EQM no vento
            resultado('V', 'INFO', f'{nome}: EQM ({"passaria" if ok else "não passa"} pela regra; o motor fica com a média)',
                      texto)
    a, n = t.loc[('radiação', 'V1.5')], t.loc[('radiação', 'V1.6')]
    acima15 = int((d['v15_rs'] > 1.001 * d['rso']).sum())
    acima16 = int((d['v16_rs'] > 1.001 * d['rso']).sum())
    resultado('R', 'APROVADO' if decidir_r(a['mae'], n['mae'], acima16) else 'REPROVADO', 'radiação limitada ao céu claro',
              f'erro diário {a["mae"]:.3f} -> {n["mae"]:.3f} MJ/m²; pixel-dias acima de Rso {acima15} '
              f'({100 * acima15 / len(d):.2f}%) -> {acima16}; BR-DWGD acima de Rso: '
              f'{int((d["br_rs"] > 1.001 * d["rso"]).sum())}')
    c15, c16 = chuva.set_index('versao').loc['V1.5'], chuva.set_index('versao').loc['V1.6']
    frac = float(d['teto_pegou'].mean())
    pegos = d[d['teto_pegou']]
    resultado('C', 'APROVADO' if decidir_c(frac, c15['erro_mensal_mm'], c16['erro_mensal_mm']) else 'REPROVADO',
              'teto da chuva (1,5 x o maior dia do BR-DWGD no pixel e mês, treino 1986-2015)',
              f'o teto pegou {len(pegos)} pixel-dias ({100 * frac:.3f}%); erro mensal {c15["erro_mensal_mm"]:.2f} -> '
              f'{c16["erro_mensal_mm"]:.2f} mm; maior dia {c15["max_sim"]:.0f} -> {c16["max_sim"]:.0f} mm (BR-DWGD '
              f'{c15["max_obs"]:.0f}); nos dias pegos, o BR-DWGD passou do teto em '
              f'{int((pegos["br_pr"] > pegos["v16_pr"]).sum()) if len(pegos) else 0}')
    if len(pegos):
        salvar_csv(pegos[['pid', 'data', 'era_pr', 'v15_pr', 'v16_pr', 'br_pr', 'pr_max_br']].round(2), 'K21_C_dias_com_teto.csv')
    a, n, q = t.loc[('ETo', 'V1.5')], t.loc[('ETo', 'V1.6')], t.loc[('ETo', 'EQM no vento (info)')]
    resultado('E', 'APROVADO' if n['mae'] <= a['mae'] else 'REPROVADO',
              'ETo (Penman-Monteith) da V1.6 revista (UR do EQM, vento da V1.5, radiação limitada)',
              f'erro diário {a["mae"]:.3f} -> {n["mae"]:.3f} mm ({100 * (n["mae"] / a["mae"] - 1):+.1f}%); viés '
              f'{a["vies"]:+.3f} -> {n["vies"]:+.3f} mm | com o EQM também no vento seria {q["mae"]:.3f} mm (informação)')


def fechar(T0):
    log('\n' + '=' * 100)
    log('RESULTADO K21')
    log('=' * 100)
    for r in RESULTADOS:
        log(f'   {r["item"]:<3} {r["status"]:<10} {r["titulo"]}')
    salvar_csv(pd.DataFrame(RESULTADOS), 'K21_RESUMO.csv')
    obrig = [r for r in RESULTADOS if r['item'] in ('U', 'R', 'C', 'E')]
    if obrig and all(r['status'] == 'APROVADO' for r in obrig) and len(obrig) == 4:      # [v4] U (UR), R, C, E
        log('\n   ✅ V1.6 REVISTA APROVADA FORA DA AMOSTRA: pode seguir para o 09a (guia, "Etapa 2", passo E2-2).')
    else:
        rep = [f"{r['item']} {r['titulo']}" for r in obrig if r['status'] != 'APROVADO']
        log(f'\n   ⛔ V1.6 NÃO aprovada como está ({rep or "itens faltando"}). Não siga: me envie o zip.')
    g = [r for r in RESULTADOS if r['item'] == 'G']
    if g:
        log(f'   GFS: {g[0]["texto"]}')
    log(f'\nTempo: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine (trava de somente leitura).')


if __name__ == '__main__' or __name__ == 'k21':
    try:
        principal()
    except Exception:
        log(traceback.format_exc())
        raise
    finally:
        if os.path.isdir(PASTA):
            z = shutil.make_archive(PASTA, 'zip', PASTA)
            log(f'📦 {z}  <- me envie este zip')
            try:
                from google.colab import files
                files.download(z)
            except Exception:
                pass
