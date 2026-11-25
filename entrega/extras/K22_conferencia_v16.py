# >>> CONFERÊNCIA K22 v2 (08/11/2026): o motor V1.6 gravou certo os dias de 2026? Somente leitura. Cole inteiro. <<<
# =========================================================================================
# K22 - CONFERÊNCIA DEPOIS DE IMPLANTAR O MOTOR V1.6 (etapa 2, passo E2-6)
#
# Rode depois de pelo menos DUAS rodadas automáticas do motor V1.6 no GitHub (ele refaz os dias de 2026 aos poucos).
#   1  INVENTÁRIO: todos os dias provisórios (ERA5) e de previsão (GFS) de 2026 gravados pela V1.6; os definitivos
#      (1961-2025) intocados (nenhum dia até 2025-12-31 com versão nova).
#   2  COERÊNCIA FÍSICA em 12 dias ERA5 (um por mês, dia 15) e 3 dias GFS: radiação <= céu claro (FAO-56), UR entre 0 e
#      100, ET real <= ETo, transpiração <= ET real, e chuva <= máx(ERA5 bruto, 1,5 x maior dia do BR-DWGD) nos dias ERA5.
#   3  EMENDA 2025 -> 2026 da UR em 150 pixels A: o desvio das anomalias diárias de 2026 dividido pelo do BR-DWGD
#      2016-2025 no mesmo pixel e mês. Antes da V1.6 a K19b mediu 1,24; agora deve ficar entre 0,85 e 1,15. O vento é
#      só informação: depois da K21 v3a (08/11) o motor V1.6 corrige o vento só na média, como a V1.5 (a razão continua
#      perto de 1,6 a 1,7). O viés das médias mensais é só informação.
#   v2 (08/11/2026): o item 1 confere também o método gravado nos dias da V1.6 ('UR eqm; vento media'); o item 3 exige
#      só a UR na faixa; janela única do motor (23h07): 22h50 à 01h00.
#   APROVADA com 1, 2 e 3 OK. Se o 1 não estiver completo, o motor ainda está refazendo os dias: rode de novo amanhã.
#
# COMO RODAR NO COLAB (fora da janela do motor, 22h50-01h00: comece até as 22h10 ou depois da 01h00)
#   Ambiente de execução -> Reiniciar sessão -> cole inteiro -> Ctrl+Enter. Tempo: de 15 a 40 min. Somente leitura.
#   No fim, baixa validacao_K22_<data>.zip. Me envie.
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
ASSET_SAB = f'projects/{PROJETO}/assets/SAB_V1'
ASSET_MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
ASSET_EQM = f'projects/{PROJETO}/assets/SICSB_EQM_1986_2025'
BR_DWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
X0, Y0, DX = TRANSFORM[2], TRANSFORM[5], TRANSFORM[0]
REGIAO_COORDS = [-75.0, -35.0, -28.0, 6.5]
VERSAO_NOVA = 'V1.6'
FATOR_TETO_CHUVA = 1.5
N_PONTOS = 150
SEMENTE = 22
FAIXA_DESVIO = (0.85, 1.15)
ANTES_K19B = {'RH': 1.24, 'u2': 1.71}
JANELAS_MOTOR = [((22, 50), (24, 0)), ((0, 0), (1, 0))]     # [v2] motor 1x por dia às 23h07 (GitHub ~23h47)
METODO_ESPERADO = 'UR eqm; vento media'                     # [v2] propriedade metodo_ur_vento_era5 da V1.6
DURACAO_ESTIMADA_MIN = 40

BRT = timezone(timedelta(hours=-3))
AGORA = datetime.now(BRT)
PASTA = (f'/content/validacao_K22_{AGORA:%Y%m%d_%H%M%S}' if os.path.isdir('/content')
         else f'validacao_K22_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K22.txt')
RESULTADOS = []


def log(*partes):
    texto = ' '.join(str(p) for p in partes)
    print(texto)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(texto + '\n')


def resultado(item, status, titulo, texto):
    RESULTADOS.append({'item': item, 'status': status, 'titulo': titulo, 'texto': texto})
    simb = {'OK': '✅', 'FALHA': '❌', 'ESPERAR': '⏳', 'INFO': 'ℹ️'}.get(status, '•')
    log(f'{simb} {item} {status}: {titulo}\n   {texto}')


def salvar_csv(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=False)


# =========================================================================================
# FUNÇÕES PURAS (testadas offline em testes/teste_k22.py)
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


def resumir_inventario(linhas):
    """linhas: [{'data', 'versao', 'alg'}] dos dias de 2026 em diante. Devolve (status, tabela, texto)."""
    df = pd.DataFrame(linhas)
    if df.empty:
        return 'FALHA', df, 'nenhum dia de 2026 no banco'
    df['alg'] = df['alg'].fillna('V1.0')
    tab = df.groupby(['versao', 'alg']).size().rename('dias').reset_index()
    novos = df[df['versao'].isin(['provisoria_era5', 'provisoria_gfs', 'provisoria_gfs_incompleta'])]
    velhos = novos[novos['alg'] != VERSAO_NOVA]
    if len(velhos):
        return ('ESPERAR', tab, f'{len(velhos)} de {len(novos)} dias provisórios ainda na versão antiga (ex.: '
                f'{sorted(velhos["data"])[:3]}): o motor refaz aos poucos; rode a K22 de novo depois da próxima rodada')
    return 'OK', tab, f'os {len(novos)} dias provisórios e de previsão de 2026 estão na {VERSAO_NOVA}'


def resumir_coerencia(linhas):
    """linhas: [{'data', 'tipo', 'n_pix', 'rs_acima', 'ur_fora', 'etr_acima', 'transp_acima', 'chuva_acima'}]."""
    df = pd.DataFrame(linhas)
    cols = ['rs_acima', 'ur_fora', 'etr_acima', 'transp_acima', 'chuva_acima']
    tot = {c: int(df[c].fillna(0).sum()) for c in cols if c in df}
    ruim = {c: n for c, n in tot.items() if n > 0}
    texto = f'{len(df)} dias, {int(df["n_pix"].sum()):,} pixel-dias: ' + ', '.join(f'{c} {n}' for c, n in tot.items())
    return ('FALHA' if ruim else 'OK'), texto


def razao_desvios(sab, br_sd):
    """sab: DataFrame pid, data, RH, u2 (2026); br_sd: DataFrame pid, mes, RH_sd, u2_sd, RH_m, u2_m (BR-DWGD 2016-2025,
    desvio dentro do mês, médio entre os anos, e média). Devolve {var: (razão, viés)}."""
    d = sab.copy()
    d['mes'] = d['data'].str[5:7].astype(int)
    d['am'] = d['data'].str[:7]
    saida = {}
    for v in ('RH', 'u2'):
        g = d.dropna(subset=[v]).groupby(['pid', 'am'])
        sd = g[v].std().rename('sd').reset_index()
        sd = sd[g[v].size().values >= 10]
        sd['mes'] = sd['am'].str[5:7].astype(int)
        m = sd.merge(br_sd[['pid', 'mes', f'{v}_sd']], on=['pid', 'mes']).dropna()
        razao = float(np.sqrt((m['sd'] ** 2).mean()) / np.sqrt((m[f'{v}_sd'] ** 2).mean())) if len(m) else float('nan')
        med = d.groupby(['pid', 'mes'])[v].mean().rename('m').reset_index().merge(br_sd[['pid', 'mes', f'{v}_m']],
                                                                                  on=['pid', 'mes']).dropna()
        vies = float((med['m'] - med[f'{v}_m']).mean()) if len(med) else float('nan')
        saida[v] = (razao, vies)
    return saida


def decidir_emenda(r):
    """[v2] Só a UR precisa ficar na faixa (o vento da V1.6 continua com a correção na média: só informação)."""
    return FAIXA_DESVIO[0] <= r['RH'][0] <= FAIXA_DESVIO[1]


# =========================================================================================
def principal():
    import ee
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log('=' * 100)
    log(f'K22: CONFERÊNCIA DO MOTOR {VERSAO_NOVA} NOS DIAS DE 2026 (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log('=' * 100)
    falta = minutos_ate_janela(AGORA)
    if falta < DURACAO_ESTIMADA_MIN:
        log(f'⛔ Não comecei: a próxima janela do motor começa em {falta} min e a K22 pode levar até '
            f'{DURACAO_ESTIMADA_MIN} min. Comece até as 22h10 ou depois da 01h00.')
        return
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K22 é somente leitura: escrita bloqueada')
    for n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
              'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable', 'startIngestion',
              'cancelTask'):
        if hasattr(ee.data, n):
            setattr(ee.data, n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa.\n')

    PROJ = ee.Projection(CRS, TRANSFORM)
    REGIAO = ee.Geometry.Rectangle(REGIAO_COORDS, None, False)
    CLASSE = ee.Image(ASSET_MASCARA).select('classe')
    ELEV = ee.Image('USGS/SRTMGL1_003')

    def gi(obj, rotulo, tentativas=6):
        for t in range(tentativas):
            try:
                return obj.getInfo()
            except Exception as e:
                if t < tentativas - 1 and any(k in str(e) for k in ('Too many concurrent', 'Internal error', '503', '429',
                                                                     'deadline', 'Deadline', 'temporarily')):
                    log(f'   ↻ {rotulo}: erro transitório; nova tentativa em {20 * (t + 1)} s')
                    time.sleep(20 * (t + 1))
                    continue
                raise

    def rso(d):
        """A mesma conta do radiacao_ceu_claro do motor V1.6."""
        data = ee.Date(d)
        lat = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180.0)
        J = ee.Number(data.getRelative('day', 'year')).add(1)
        dr = J.multiply(2.0 * math.pi / 365.0).cos().multiply(0.033).add(1.0)
        de = J.multiply(2.0 * math.pi / 365.0).subtract(1.39).sin().multiply(0.409)
        ws = lat.tan().multiply(de.tan()).multiply(-1.0).clamp(-1.0, 1.0).acos()
        ra = (ws.multiply(lat.sin()).multiply(de.sin()).add(lat.cos().multiply(de.cos()).multiply(ws.sin()))
              .multiply(dr).multiply((24.0 * 60.0 / math.pi) * 0.0820))
        return ELEV.multiply(0.00002).add(0.75).multiply(ra)

    # ------------------------------------------------------------------ 1 inventário
    col26 = ee.ImageCollection(ASSET_SAB).filterDate('2026-01-01', '2028-01-01')
    inv = gi(ee.List([col26.aggregate_array('system:time_start'), col26.aggregate_array('versao'),
                      col26.aggregate_array('versao_algoritmo')]), 'inventário 2026')
    # aggregate_array pula as imagens sem a propriedade: reconstrói por imagem quando os tamanhos diferem
    if not (len(inv[0]) == len(inv[1]) == len(inv[2])):
        feats = gi(col26.map(lambda i: ee.Feature(None, {
            't': i.get('system:time_start'), 'v': i.get('versao'),
            'a': ee.Algorithms.If(i.propertyNames().contains('versao_algoritmo'), i.get('versao_algoritmo'), 'V1.0')})),
            'inventário por imagem')['features']
        inv = [[f['properties']['t'] for f in feats], [f['properties']['v'] for f in feats],
               [f['properties']['a'] for f in feats]]
    linhas = [{'data': datetime.fromtimestamp(t / 1000, timezone.utc).strftime('%Y-%m-%d'), 'versao': v, 'alg': a}
              for t, v, a in zip(*inv)]
    st, tab, texto = resumir_inventario(linhas)
    salvar_csv(pd.DataFrame(linhas), 'K22_inventario_2026.csv')
    log(tab.to_string(index=False))
    antigos = gi(ee.ImageCollection(ASSET_SAB).filterDate('1961-01-01', '2026-01-01')
                 .filter(ee.Filter.eq('versao_algoritmo', VERSAO_NOVA)).size(), 'histórico com a versão nova')
    if antigos:
        st, texto = 'FALHA', f'{antigos} dia(s) até 2025 com a {VERSAO_NOVA}: a trava do histórico falhou. ' + texto
    metodos = gi(col26.filter(ee.Filter.eq('versao_algoritmo', VERSAO_NOVA)).aggregate_array('metodo_ur_vento_era5')
                 .distinct(), 'método gravado')                                               # [v2]
    if metodos and sorted(metodos) != [METODO_ESPERADO]:
        st, texto = 'FALHA', f'método gravado {metodos} (esperado {METODO_ESPERADO!r}): o motor no GitHub não é o do pacote. ' + texto
    texto += f' | método gravado: {metodos or "nenhum dia ainda"}'
    resultado('1', st, 'inventário de 2026 e histórico intocado', texto + f' | histórico com a {VERSAO_NOVA}: {antigos}')

    # ------------------------------------------------------------------ 2 coerência
    log('\n[2] coerência física')
    datas = sorted({l['data'] for l in linhas})
    era_dias = [l['data'] for l in linhas if l['versao'] == 'provisoria_era5' and l['alg'] == VERSAO_NOVA]
    gfs_dias = [l['data'] for l in linhas if l['versao'] == 'provisoria_gfs' and l['alg'] == VERSAO_NOVA]
    amostra = sorted({min((d for d in era_dias if d[:7] == m), key=lambda d: abs(int(d[8:]) - 15))
                      for m in {d[:7] for d in era_dias}}) + gfs_dias[:1] + gfs_dias[len(gfs_dias) // 2:][:1] + gfs_dias[-1:]
    coer = []
    for d in amostra:
        img = ee.Image(col26.filterDate(d, ee.Date(d).advance(1, 'day')).first())
        eh_era = d in era_dias
        flags = [ee.Image.constant(1).updateMask(img.select('pr_mm').mask()).rename('n_pix'),
                 img.select('rs').gt(rso(d).multiply(1.001)).rename('rs_acima'),
                 img.select('RH').lt(0).Or(img.select('RH').gt(100)).rename('ur_fora'),
                 img.select('et_real').gt(img.select('et_potencial').add(0.001)).rename('etr_acima'),
                 img.select('transpiracao_mm').gt(img.select('et_real').add(0.001)).rename('transp_acima')]
        if eh_era:
            era = ee.Image(ee.ImageCollection(ERA5).filterDate(d, ee.Date(d).advance(1, 'day')).first())
            bruto = era.select('total_precipitation_sum').multiply(1000).max(0)
            teto = ee.Image(f'{ASSET_EQM}/Matriz_EQM_{d[5:7]}').select('pr_max_br').multiply(FATOR_TETO_CHUVA)
            flags.append(img.select('pr_mm').gt(bruto.max(teto).add(0.01)).unmask(0).rename('chuva_acima'))
        r = gi(ee.Image.cat(flags).unmask(0).updateMask(img.select('pr_mm').mask().Or(img.select('RH').mask()))
               .reduceRegion(reducer=ee.Reducer.sum(), geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM,
                             maxPixels=1e10, tileScale=4), f'coerência {d}')
        coer.append({'data': d, 'tipo': 'ERA5' if eh_era else 'GFS', **{k: int(round(v or 0)) for k, v in r.items()}})
        log(f'   {d} ({"ERA5" if eh_era else "GFS"}): {coer[-1]}')
    salvar_csv(pd.DataFrame(coer), 'K22_coerencia.csv')
    st, texto = resumir_coerencia(coer) if coer else ('ESPERAR', 'nenhum dia V1.6 ainda')
    resultado('2', st, 'coerência física dos dias V1.6', texto)

    # ------------------------------------------------------------------ 3 emenda
    log(f'\n[3] emenda 2025 -> 2026: desvio das anomalias diárias da UR e do vento ({N_PONTOS} pixels A)')
    if not era_dias:
        resultado('3', 'ESPERAR', 'emenda da UR e do vento', 'nenhum dia ERA5 da V1.6 ainda')
        return fechar(T0)
    sorteio = (ee.Image.pixelLonLat().addBands(CLASSE)
               .stratifiedSample(numPoints=0, classBand='classe', region=REGIAO, projection=PROJ, seed=SEMENTE,
                                 classValues=[1], classPoints=[N_PONTOS], geometries=True, tileScale=4))
    pts = [{'pid': k, 'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1]}
           for k, f in enumerate(gi(sorteio, 'pontos')['features'])]
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']}) for p in pts])
    chave = {(int(math.floor((p['lon'] - X0) / DX + 1e-6)), int(math.floor((Y0 - p['lat']) / DX + 1e-6))): p['pid']
             for p in pts}

    def br_prep(img):
        m = img.select('pr').gt(-32768).And(img.select('Tmax').gt(-32768)).And(img.select('Tmin').gt(-32768))
        return ee.Image.cat([img.select('RH').updateMask(m).multiply(0.39370079).add(-0.393701).clamp(0, 100).rename('RH'),
                             img.select('u2').updateMask(m).multiply(0.05905512).add(-0.059055).max(0).rename('u2')])

    br_sd = []
    for mes in range(1, 13):
        anos = ee.List.sequence(2016, 2025)
        col = ee.ImageCollection(BR_DWGD)
        sd = ee.ImageCollection(anos.map(lambda a: col.filter(ee.Filter.calendarRange(a, a, 'year'))
                                         .filter(ee.Filter.calendarRange(mes, mes, 'month')).map(br_prep)
                                         .reduce(ee.Reducer.stdDev()).rename(['RH_sd', 'u2_sd']))).mean()
        me = (col.filter(ee.Filter.calendarRange(2016, 2025, 'year')).filter(ee.Filter.calendarRange(mes, mes, 'month'))
              .map(br_prep).mean().rename(['RH_m', 'u2_m']))
        r = gi(sd.addBands(me).sampleRegions(collection=fc, properties=['pid'], projection=PROJ, geometries=False,
                                             tileScale=16), f'BR-DWGD mês {mes:02d}')
        br_sd += [dict(f['properties'], mes=mes) for f in r['features']]
    br_sd = pd.DataFrame(br_sd)
    fim = max(era_dias)
    sab = []
    for m in sorted({d[:7] for d in era_dias}):
        ini = f'{m}-01'
        prox = (datetime.strptime(ini, '%Y-%m-%d') + timedelta(days=32)).strftime('%Y-%m-01')
        reg = gi(col26.filterDate(ini, min(prox, (datetime.strptime(fim, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')))
                 .filter(ee.Filter.eq('versao', 'provisoria_era5')).select(['RH', 'u2'])
                 .getRegion(ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in pts]), None, CRS, TRANSFORM), f'SAB {m}')
        df = pd.DataFrame(reg[1:], columns=reg[0])
        ix = np.floor((df['longitude'].astype(float) - X0) / DX + 1e-6).astype(int)
        iy = np.floor((Y0 - df['latitude'].astype(float)) / DX + 1e-6).astype(int)
        df['pid'] = [chave.get((a, b)) for a, b in zip(ix, iy)]
        df['data'] = pd.to_datetime(df['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
        sab.append(df.dropna(subset=['pid'])[['pid', 'data', 'RH', 'u2']])
    sab = pd.concat(sab, ignore_index=True)
    for c in ('RH', 'u2'):
        sab[c] = pd.to_numeric(sab[c], errors='coerce')
    sab['pid'] = sab['pid'].astype(int)
    r = razao_desvios(sab, br_sd)
    salvar_csv(pd.DataFrame([{'variavel': v, 'razao_desvio': r[v][0], 'vies_medio': r[v][1],
                              'antes_K19b': ANTES_K19B[v]} for v in r]), 'K22_emenda.csv')
    resultado('3', 'OK' if decidir_emenda(r) else 'FALHA', 'emenda 2025 -> 2026 da UR (vento só informação)',
              f'desvio das anomalias diárias / BR-DWGD 2016-2025: UR {ANTES_K19B["RH"]:.2f} (antes) -> {r["RH"][0]:.2f} '
              f'(faixa {FAIXA_DESVIO[0]}-{FAIXA_DESVIO[1]}); vento {ANTES_K19B["u2"]:.2f} -> {r["u2"][0]:.2f} (correção na '
              f'média, como a V1.5: informação) | viés médio '
              f'UR {r["RH"][1]:+.2f} %, vento {r["u2"][1]:+.2f} m/s (informação: 2026 não é a média de 2016-2025)')
    fechar(T0)


def fechar(T0):
    log('\n' + '=' * 100)
    log('RESULTADO K22')
    log('=' * 100)
    for r in RESULTADOS:
        log(f'   {r["item"]:<3} {r["status"]:<8} {r["titulo"]}')
    salvar_csv(pd.DataFrame(RESULTADOS), 'K22_RESUMO.csv')
    st = {r['item']: r['status'] for r in RESULTADOS}
    if all(st.get(k) == 'OK' for k in ('1', '2', '3')):
        log(f'\n   ✅ MOTOR {VERSAO_NOVA} CONFERIDO: etapa 2 concluída.')
    elif any(v == 'FALHA' for v in st.values()):
        log('\n   ❌ Há falha: me envie o zip (o histórico não é afetado; dá para voltar o motor para a V1.5).')
    else:
        log('\n   ⏳ O motor ainda está refazendo dias: rode a K22 de novo depois da próxima rodada.')
    log(f'\nTempo: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine (trava de somente leitura).')


if __name__ == '__main__':
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
