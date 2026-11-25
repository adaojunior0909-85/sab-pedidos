# >>> AUDITORIA K23 v2 (09/11/2026): o salto da Tmax na emenda ERA5 -> GFS é real ou defeito? Somente leitura. Cole inteiro, sem editar. <<<
# =========================================================================================
# K23 - AUDITORIA DA EMENDA ERA5 -> GFS DA TMAX (o aviso da PRÉVIA 5 do 05a V1.6, 08/11/2026)
#
# O AVISO
#   A PRÉVIA 5 do 05a V1.6 (08/11, 20h22) parou em um critério só: a Tmax máxima nacional foi de 41,4 °C no último dia
#   ERA5 (01/11) para 44,3 °C no 1º dia GFS (02/11): +2,8 °C, limite ±2 °C. A PRÉVIA 6 mostrou o 02/11 da V1.6 IGUAL
#   ao gravado pela V1.5 (44,28 °C), e o mesmo nos dias 09, 15 e 18/11.
#
# PARTE A (feita fora do Colab, no código, em 08/11; resultado no LOG): a rota GFS da Tmax e da Tmin é a MESMA na V1.5
#   e na V1.6. Das 41 funções e constantes da rota GFS, só processarDia_GFS mudou, e só na chuva (teto), na radiação
#   (limite do céu claro) e nas propriedades novas. Do lado ERA5 da emenda, a Tmax também não muda (PRÉVIA 3: 0% dos
#   pixels). Conclusão da parte A: a V1.6 não cria nem muda o salto.
#
# PARTES B a E (aqui, só leitura, ~15 a 30 min): o salto é variação natural do tempo ou efeito da calibração do GFS?
#   B  Contexto: Tmax do SAB_V1 de 18/10 a 23/11/2026 (máximo, percentil 99 e média do Brasil, e onde fica o máximo).
#   C  Emenda pixel a pixel: Tmax(1º dia GFS) - Tmax(último dia ERA5) em todos os pixels (média, desvio, p99 de |Δ|,
#      % com |Δ| > 5 °C), comparada com a variação natural de um dia para o outro: os pares de dias ERA5 seguidos de
#      2026 (até 10) e os pares de 29/10 a 03/11 do BR-DWGD de 2011 a 2025 (75 pares).
#   D  Máximo nacional: com que frequência a Tmax máxima do Brasil muda tanto quanto o salto, de um dia para o outro,
#      no BR-DWGD (15/10 a 30/11, 1991 a 2025).
#   E  O pixel do máximo do 1º dia GFS: o recorde e o percentil 99 da Tmax nesse pixel no BR-DWGD (out-nov, 1991-2025).
#
# REGRAS (fixadas antes de rodar)
#   C OK: a média, o desvio e o p99 de |Δ| da emenda ficam dentro do percentil 95 dos mesmos números nos pares
#        naturais (BR-DWGD + ERA5 de 2026).
#   D OK: um salto do tamanho do observado (ou maior) acontece em pelo menos 5% dos pares de dias do BR-DWGD.
#   E OK: o máximo do 1º dia GFS fica até 1,0 °C acima do recorde out-nov do próprio pixel no BR-DWGD.
#   Veredito: A (neutra) já decide a V1.6. Com C, D e E OK, o aviso é falso positivo do critério do máximo nacional
#   (um pixel só): segue o E2-5 com a exceção registrada. Se C ou E falhar, a rota GFS (no ar desde a V1.5) tem um
#   problema real na emenda: a V1.6 continua neutra, mas abre-se uma correção separada da calibração do GFS.
#
# v2 (09/11/2026): a v1 parou na parte B com o erro 429 do Earth Engine (muitos cálculos ao mesmo tempo): ela pedia
#   as estatísticas dos 37 dias num pedido só (74 reduções do Brasil inteiro em paralelo), e às 01h34 o motor da
#   noite ainda podia estar exportando. Agora: B um dia por pedido, C um par por pedido, D em blocos de 10 dias, e
#   espera longa e crescente quando o servidor devolve 429 (até ~15 min no total). Contas, dados e regras iguais.
#
# COMO RODAR NO COLAB (fora da janela do motor, 22h50-01h00: comece até as 22h05 ou depois da 01h00)
#   Ambiente de execução -> Reiniciar sessão -> cole inteiro -> Ctrl+Enter. No fim, baixa auditoria_K23_<data>.zip.
#   Me envie. Nada é gravado no Earth Engine (trava de somente leitura).
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
BR_DWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
REGIAO_COORDS = [-75.0, -35.0, -28.0, 6.5]
BANDA = 'tmax_C'
CONTEXTO = ('2026-10-18', '2026-11-23')
ANOS_PARES = (2011, 2025)
DIAS_PARES = ['10-29', '10-30', '10-31', '11-01', '11-02', '11-03']     # 5 pares por ano
ANOS_MAXIMO = (1991, 2025)
PERIODO_MAXIMO = ('10-15', '11-30')
MESES_RECORDE = (10, 11)
SALTO_OBSERVADO_PREVIA = 2.8        # °C, PRÉVIA 5 de 08/11 (41,4 -> 44,3)
PCT_NATURAL = 95                    # regra C
FREQ_MIN_D = 0.05                   # regra D
FOLGA_RECORDE_E = 1.0               # regra E, °C
JANELAS_MOTOR = [((22, 50), (24, 0)), ((0, 0), (1, 0))]
DURACAO_ESTIMADA_MIN = 45

BRT = timezone(timedelta(hours=-3))
AGORA = datetime.now(BRT)
PASTA = (f'/content/auditoria_K23_{AGORA:%Y%m%d_%H%M%S}' if os.path.isdir('/content')
         else f'auditoria_K23_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K23.txt')
RESULTADOS = []


def log(*partes):
    texto = ' '.join(str(p) for p in partes)
    print(texto)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(texto + '\n')


def resultado(item, status, titulo, texto):
    RESULTADOS.append({'item': item, 'status': status, 'titulo': titulo, 'texto': texto})
    simb = {'OK': '✅', 'ATENÇÃO': '⚠️', 'INFO': 'ℹ️', 'FALHOU': '❌'}.get(status, '•')
    log(f'{simb} {item} {status}: {titulo}\n   {texto}')


def salvar_csv(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=False)


# =========================================================================================
# FUNÇÕES PURAS (testadas offline em testes/teste_k23.py)
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


def emenda_do_inventario(linhas):
    """linhas: [{'data': 'AAAA-MM-DD', 'versao': ...}] dos dias de 2026. Devolve (último dia ERA5, 1º dia GFS depois
    dele) ou (None, None)."""
    era = sorted(l['data'] for l in linhas if l['versao'] == 'provisoria_era5')
    if not era:
        return None, None
    gfs = sorted(l['data'] for l in linhas if l['versao'] in ('provisoria_gfs', 'provisoria_gfs_incompleta')
                 and l['data'] > era[-1])
    return era[-1], (gfs[0] if gfs else None)


def stats_par(r):
    """r: dicionário do reduceRegion da diferença (bandas d, a, g5). Devolve as métricas da regra C."""
    return {'media': r.get('d_mean'), 'abs_media': None if r.get('d_mean') is None else abs(r['d_mean']),
            'desvio': r.get('d_stdDev'), 'p99_abs': r.get('a_p99'), 'pct_acima_5': None if r.get('g5_mean') is None
            else 100 * r['g5_mean'], 'p01': r.get('d_p1'), 'p99': r.get('d_p99')}


def decidir_c(emenda, naturais, pct=PCT_NATURAL):
    """emenda: stats_par da emenda; naturais: lista de stats_par. OK se abs_media, desvio e p99_abs da emenda <= o
    percentil pct dos naturais. Devolve (ok, {métrica: (valor, limite, ok)})."""
    nat = pd.DataFrame([n for n in naturais if n.get('desvio') is not None])
    det = {}
    for k in ('abs_media', 'desvio', 'p99_abs'):
        lim = float(np.percentile(nat[k].astype(float), pct)) if len(nat) else float('nan')
        v = emenda.get(k)
        det[k] = (v, lim, v is not None and lim == lim and v <= lim)
    return all(x[2] for x in det.values()) and len(nat) >= 10, det


def saltos_maximo(serie):
    """serie: DataFrame com 'data' (AAAA-MM-DD) e 'max'. Devolve os |Δ| entre dias seguidos (só pares de 1 dia)."""
    s = serie.dropna().copy()
    s['dt'] = pd.to_datetime(s['data'])
    s = s.sort_values('dt')
    seguido = s['dt'].diff().dt.days.eq(1)
    return (s['max'].diff().abs())[seguido].astype(float).values


def decidir_d(saltos, salto_obs, freq_min=FREQ_MIN_D):
    saltos = np.asarray(saltos, float)
    if len(saltos) < 100:
        return False, float('nan'), float('nan')
    freq = float((saltos >= abs(salto_obs) - 1e-9).mean())
    return freq >= freq_min, freq, float(np.percentile(saltos, 95))


def decidir_e(tmax_gfs, recorde_pixel, folga=FOLGA_RECORDE_E):
    if tmax_gfs is None or recorde_pixel is None or recorde_pixel != recorde_pixel:
        return False
    return tmax_gfs <= recorde_pixel + folga


# =========================================================================================
def principal():
    import ee
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log('=' * 100)
    log(f'K23 v2: AUDITORIA DA EMENDA ERA5 -> GFS DA TMAX (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log('=' * 100)
    falta = minutos_ate_janela(AGORA)
    if falta < DURACAO_ESTIMADA_MIN:
        log(f'⛔ Não comecei: a janela do motor começa em {falta} min. Comece até as 22h05 ou depois da 01h00.')
        return
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K23 é somente leitura: escrita bloqueada')
    for n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
              'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable', 'startIngestion',
              'cancelTask'):
        if hasattr(ee.data, n):
            setattr(ee.data, n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa.\n')
    resultado('A', 'OK', 'a V1.6 não mexe na Tmax da emenda (conferência do código, 08/11)',
              'rota GFS da Tmax/Tmin igual na V1.5 e na V1.6 (40 de 41 itens idênticos; processarDia_GFS muda só chuva, '
              'radiação e propriedades); Tmax do ERA5 sem mudança (PRÉVIA 3: 0% dos pixels); PRÉVIA 6: 02, 09, 15 e '
              '18/11 da V1.6 iguais ao gravado pela V1.5')

    REGIAO = ee.Geometry.Rectangle(REGIAO_COORDS, None, False)
    TRANS = ('Too many concurrent', 'Internal error', 'Service Unavailable', '503', '429', 'deadline', 'Deadline',
             'Connection', 'temporarily')

    ESPERAS = [30, 60, 90, 120, 180, 240, 240]                # [v2] 429: espera crescente (~16 min no total)

    def gi(obj, rotulo, tentativas=len(ESPERAS) + 1):
        for t in range(tentativas):
            try:
                return obj.getInfo()
            except Exception as e:
                s = str(e)
                if t < tentativas - 1 and any(k in s for k in TRANS):
                    log(f'   ↻ {rotulo}: servidor ocupado ({s[:60]}); nova tentativa em {ESPERAS[t]} s')
                    time.sleep(ESPERAS[t])
                    continue
                raise

    def rr(img, reducer, rotulo=None):
        return img.reduceRegion(reducer=reducer, geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10,
                                tileScale=4)

    def br_tmax(img):
        m = img.select('Tmax').gt(-32768)
        return ee.Image(img.select('Tmax').updateMask(m).multiply(0.00106815).add(15.0).rename(BANDA)
                        .copyProperties(img, ['system:time_start']))

    SAB = ee.ImageCollection(ASSET_SAB)
    BR = ee.ImageCollection(BR_DWGD)

    def sab_dia(d):
        return ee.Image(SAB.filterDate(d, ee.Date(d).advance(1, 'day')).first()).select(BANDA)

    RED_C = (ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True)
             .combine(ee.Reducer.percentile([1, 99]), sharedInputs=True))

    def dif_img(a, b):
        d = b.subtract(a).rename('d')
        return d.addBands(d.abs().rename('a')).addBands(d.abs().gt(5).rename('g5'))

    # ------------------------------------------------------------------ B: contexto 2026
    log(f'[B] Tmax do SAB_V1 de {CONTEXTO[0]} a {CONTEXTO[1]} (Brasil)')
    col = SAB.filterDate(CONTEXTO[0], ee.Date(CONTEXTO[1]).advance(1, 'day'))
    inv = gi(ee.List([col.aggregate_array('system:time_start'), col.aggregate_array('versao'),
                      col.aggregate_array('versao_algoritmo')]), 'inventário 2026')
    RED_B = (ee.Reducer.max().combine(ee.Reducer.mean(), sharedInputs=True)
             .combine(ee.Reducer.percentile([99]), sharedInputs=True))
    linhas = []
    for t_ms, versao, alg in zip(*inv):                      # [v2] um dia por pedido
        d = datetime.fromtimestamp(t_ms / 1000, timezone.utc).strftime('%Y-%m-%d')
        t = sab_dia(d)
        r = gi(ee.Dictionary({'est': rr(t, RED_B), 'onde': rr(t.addBands(ee.Image.pixelLonLat()), ee.Reducer.max(3))}),
               f'contexto {d}')
        est, onde = r.get('est') or {}, r.get('onde') or {}
        linhas.append({'data': d, 'versao': versao, 'alg': alg, 'max': est.get(f'{BANDA}_max'),
                       'p99': est.get(f'{BANDA}_p99'), 'media': est.get(f'{BANDA}_mean'),
                       'lon_max': onde.get('max1'), 'lat_max': onde.get('max2')})
    log(f'   {len(linhas)} dias lidos')
    ctx = pd.DataFrame(linhas).sort_values('data')
    salvar_csv(ctx.round(4), 'K23_B_contexto_2026.csv')
    log(ctx.round(2).to_string(index=False))
    ult_era, pri_gfs = emenda_do_inventario(linhas)
    if not pri_gfs:
        resultado('B', 'FALHOU', 'emenda não encontrada', f'último ERA5 {ult_era}; nenhum dia GFS depois dele')
        fechar(T0)
        return
    e1, g1 = ctx.set_index('data').loc[ult_era], ctx.set_index('data').loc[pri_gfs]
    salto_nac = float(g1['max'] - e1['max'])
    resultado('B', 'INFO', f'emenda atual: {ult_era} (ERA5) -> {pri_gfs} (GFS)',
              f'máximo nacional {e1["max"]:.1f} -> {g1["max"]:.1f} °C ({salto_nac:+.1f}); p99 {e1["p99"]:.1f} -> '
              f'{g1["p99"]:.1f}; média {e1["media"]:.2f} -> {g1["media"]:.2f}; máximo do GFS em '
              f'({g1["lon_max"]:.2f}; {g1["lat_max"]:.2f})')

    # ------------------------------------------------------------------ C: emenda pixel a pixel x natural
    log('\n[C] emenda pixel a pixel x variação natural de um dia para o outro')
    em = stats_par(gi(rr(dif_img(sab_dia(ult_era), sab_dia(pri_gfs)), RED_C), 'emenda'))
    nat = []
    eras = sorted(ctx.loc[ctx['versao'] == 'provisoria_era5', 'data'])[-11:]
    pares_era = [(a, b) for a, b in zip(eras[:-1], eras[1:])
                 if (datetime.strptime(b, '%Y-%m-%d') - datetime.strptime(a, '%Y-%m-%d')).days == 1]
    for a, b in pares_era:                                   # [v2] um par por pedido
        x = gi(rr(dif_img(sab_dia(a), sab_dia(b)), RED_C), f'par ERA5 {a}')
        nat.append({'fonte': 'SAB ERA5 2026', 'par': f'{a}->{b}', **stats_par(x)})
    gfss = sorted(ctx.loc[ctx['versao'] == 'provisoria_gfs', 'data'])[:6]
    pares_gfs = [(a, b) for a, b in zip(gfss[:-1], gfss[1:])]
    ref_gfs = []
    for a, b in pares_gfs:
        x = gi(rr(dif_img(sab_dia(a), sab_dia(b)), RED_C), f'par GFS {a}')
        ref_gfs.append({'fonte': 'SAB GFS 2026 (só referência)', 'par': f'{a}->{b}', **stats_par(x)})
    for ano in range(ANOS_PARES[0], ANOS_PARES[1] + 1):
        dias = [f'{ano}-{d}' for d in DIAS_PARES]
        imgs = [br_tmax(ee.Image(BR.filterDate(d, ee.Date(d).advance(1, 'day')).first())) for d in dias]
        for (a, b), (ia, ib) in zip(zip(dias[:-1], dias[1:]), zip(imgs[:-1], imgs[1:])):
            x = gi(rr(dif_img(ia, ib), RED_C), f'par BR-DWGD {a}')
            nat.append({'fonte': 'BR-DWGD', 'par': f'{a}->{b}', **stats_par(x)})
        log(f'   BR-DWGD {ano}: {len(dias) - 1} pares')
    tab_c = pd.DataFrame([{'fonte': 'EMENDA', 'par': f'{ult_era}->{pri_gfs}', **em}] + nat + ref_gfs)
    salvar_csv(tab_c.round(4), 'K23_C_emenda_x_natural.csv')
    ok_c, det = decidir_c(em, nat)
    log(tab_c.groupby('fonte')[['abs_media', 'desvio', 'p99_abs', 'pct_acima_5']].median().round(3).to_string())
    resultado('C', 'OK' if ok_c else 'ATENÇÃO', 'emenda pixel a pixel dentro da variação natural de um dia para o outro',
              '; '.join(f'{k} {v:.2f} (p{PCT_NATURAL} natural {lim:.2f}) {"ok" if b else "ACIMA"}'
                        for k, (v, lim, b) in det.items() if v is not None)
              + f'; {em["pct_acima_5"]:.2f}% dos pixels com |Δ| > 5 °C; {len(nat)} pares naturais')

    # ------------------------------------------------------------------ D: saltos do máximo nacional no BR-DWGD
    log(f'\n[D] máximo nacional da Tmax por dia no BR-DWGD, {PERIODO_MAXIMO[0]} a {PERIODO_MAXIMO[1]}, '
        f'{ANOS_MAXIMO[0]}-{ANOS_MAXIMO[1]}')
    saltos, series = [], []
    for ano in range(ANOS_MAXIMO[0], ANOS_MAXIMO[1] + 1):
        ini = datetime.strptime(f'{ano}-{PERIODO_MAXIMO[0]}', '%Y-%m-%d')
        fim = datetime.strptime(f'{ano}-{PERIODO_MAXIMO[1]}', '%Y-%m-%d')
        dias_d = [(ini + timedelta(days=k)).strftime('%Y-%m-%d') for k in range((fim - ini).days + 1)]
        reg_d = []
        for k in range(0, len(dias_d), 10):                  # [v2] blocos de 10 dias
            bloco = dias_d[k:k + 10]
            vals = gi(ee.List([rr(br_tmax(ee.Image(BR.filterDate(d, ee.Date(d).advance(1, 'day')).first())),
                                  ee.Reducer.max()).get(BANDA) for d in bloco]), f'máximos {bloco[0]}')
            reg_d += [{'data': d, 'max': m} for d, m in zip(bloco, vals)]
        s = pd.DataFrame(reg_d)
        series.append(s)
        saltos += list(saltos_maximo(s))
    salvar_csv(pd.concat(series, ignore_index=True), 'K23_D_maximo_nacional_brdwgd.csv')
    s_obs = salto_nac
    ok_d, freq, p95 = decidir_d(saltos, s_obs)
    ok_d_prev, freq_prev, _ = decidir_d(saltos, SALTO_OBSERVADO_PREVIA)
    resultado('D', 'OK' if ok_d else 'ATENÇÃO', 'saltos do máximo nacional de um dia para o outro no BR-DWGD',
              f'{len(saltos)} pares; |Δ| >= {abs(s_obs):.1f} °C (emenda atual) em {100 * freq:.1f}% dos pares; '
              f'|Δ| >= {SALTO_OBSERVADO_PREVIA} °C (PRÉVIA de 08/11) em {100 * freq_prev:.1f}%; p95 dos saltos '
              f'{p95:.1f} °C; o limite da PRÉVIA é 2 °C (|Δ| > 2 em '
              f'{100 * float((np.asarray(saltos) > 2).mean()):.1f}% dos pares)')

    # ------------------------------------------------------------------ E: o pixel do máximo
    log(f'   {len(saltos)} pares de dias lidos')
    log('\n[E] o pixel do máximo do 1º dia GFS x o recorde do pixel no BR-DWGD')
    lon, lat = float(g1['lon_max']), float(g1['lat_max'])
    pt = ee.Geometry.Point([lon, lat])
    hist = BR.filter(ee.Filter.calendarRange(ANOS_MAXIMO[0], ANOS_MAXIMO[1], 'year')) \
        .filter(ee.Filter.calendarRange(MESES_RECORDE[0], MESES_RECORDE[1], 'month')).map(br_tmax)
    reg = gi(hist.getRegion(pt, None, CRS, TRANSFORM), 'série do pixel')
    v = pd.DataFrame(reg[1:], columns=reg[0])[BANDA].astype(float).dropna()
    rec, p99 = (float(v.max()), float(np.percentile(v, 99))) if len(v) else (float('nan'), float('nan'))
    reg2 = gi(col.getRegion(pt, None, CRS, TRANSFORM), 'SAB 2026 no pixel')
    s26 = pd.DataFrame(reg2[1:], columns=reg2[0])
    s26['data'] = pd.to_datetime(s26['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
    s26 = s26[['data', BANDA]].sort_values('data')
    salvar_csv(s26.round(3), 'K23_E_pixel_do_maximo_2026.csv')
    log(s26.round(2).to_string(index=False))
    ok_e = decidir_e(float(g1['max']), rec)
    resultado('E', 'OK' if ok_e else 'ATENÇÃO', 'máximo do 1º dia GFS x recorde do próprio pixel (BR-DWGD out-nov)',
              f'pixel ({lon:.2f}; {lat:.2f}): GFS {g1["max"]:.1f} °C; recorde do pixel {rec:.1f} °C e p99 {p99:.1f} °C '
              f'({len(v)} dias, {ANOS_MAXIMO[0]}-{ANOS_MAXIMO[1]}); folga da regra {FOLGA_RECORDE_E} °C')

    fechar(T0, ok_c, ok_d, ok_e)


def fechar(T0, ok_c=None, ok_d=None, ok_e=None):
    log('\n' + '=' * 100)
    log('RESULTADO K23')
    log('=' * 100)
    for r in RESULTADOS:
        log(f'   {r["item"]:<3} {r["status"]:<9} {r["titulo"]}')
    salvar_csv(pd.DataFrame(RESULTADOS), 'K23_RESUMO.csv')
    if ok_c is None:
        log('\n   ⛔ Auditoria incompleta: me envie o zip.')
    elif ok_c and ok_e:
        log('\n   ✅ A V1.6 é neutra na emenda (A) e o salto está dentro da variação natural (C e E)'
            + ('' if ok_d else '; o salto do máximo nacional é raro no BR-DWGD (D), mas pixel a pixel a emenda é normal')
            + '. O aviso da PRÉVIA 5 é falso positivo do critério do máximo nacional: pode seguir para o E2-5.')
    else:
        log('\n   ⚠️ A V1.6 é neutra na emenda (A), mas a emenda da rota GFS (no ar desde a V1.5) tem sinal de defeito '
            '(C ou E). Não siga sozinho: me envie o zip para decidirmos juntos.')
    log(f'\nTempo: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine (trava de somente leitura).')


if __name__ == '__main__' or __name__ == 'k23':
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
