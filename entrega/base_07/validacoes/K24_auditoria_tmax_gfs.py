# >>> AUDITORIA K24 v1 (09/11/2026): a Tmax da previsão GFS passa do recorde do pixel? Somente leitura. Cole inteiro, sem editar. <<<
# =========================================================================================
# K24 - AUDITORIA DO PONTO QUENTE DA TMAX NA PREVISÃO GFS (base da futura V1.7)
#
# O QUE JÁ SABEMOS (K23 v2, 09/11, 01h39)
#   A emenda ERA5 -> GFS é normal no Brasil todo (pixel a pixel, mais suave que a troca natural de um dia para o
#   outro). O salto da máxima nacional (41,4 -> 44,3 °C) vem de UM pixel em Roraima (-60,65; 2,85): nos dias GFS ele
#   foi a máxima do Brasil em 16 de 22 dias, entre 43 e 44 °C, acima do recorde dele em out-nov de 1991-2025
#   (42,6 °C); nos dias ERA5 ficou entre 37 e 41 °C. Vem da rota GFS da V1.5 (a V1.6 não mexe nela).
#
# PERGUNTAS DA K24 (só leitura, ~20 a 40 min)
#   B  Quanto da previsão passa do recorde do próprio pixel (BR-DWGD, mesmo mês, 1991-2025)? Por dia GFS: % de pixels
#      acima do recorde, do recorde + 1 °C e + 2 °C, e o maior excesso. A mesma conta nos últimos 30 dias ERA5 é a
#      referência (o ano de 2026 é quente: El Niño muito forte; um pouco acima do recorde também acontece no ERA5).
#   C  Onde: os pixels que passam do recorde + 1 °C em 5 dias GFS ou mais ("pontos quentes"), com o excesso.
#   D  Por quê: nos 10 piores pontos quentes, a Tmax do GFS bruto de cada dia, recuperada da gravada pela própria conta
#      do motor (calibrada = m_sicsb + (bruto - m_gfs) x razão dos desvios, matriz V2.1 do mês e da faixa de prazo):
#      bruto = m_gfs + (calibrada - m_sicsb) / razão. Mostra quanto é viés do modelo e quanto é da calibração.
#   E  Um teto resolveria? Para folgas de 0, 1 e 2 °C acima do recorde do pixel: a máxima nacional de cada dia GFS com
#      o teto, o salto na emenda com o teto e quantos pixel-dias o teto pegaria.
#
# REGRAS (fixadas antes de rodar)
#   P1 excesso sistemático: % de pixel-dias GFS acima do recorde + 1 °C >= 3 x o dos dias ERA5 E >= 0,05%.
#   P2 pontos quentes: pixels acima do recorde + 1 °C em 5 dias GFS ou mais (só contagem e lista).
#   P3 origem: nos pontos quentes, efeito médio da calibração (calibrada - bruta) > +0,5 °C = a calibração aumenta o
#      calor; senão, o excesso vem do próprio GFS.
#   Folga sugerida para a V1.7: a menor (0, 1 ou 2 °C) com a máxima nacional de todos os dias GFS <= 44,8 °C (recorde
#   do INMET) e o salto na emenda <= 2 °C, pegando no máximo 0,5% dos pixel-dias GFS.
#   Veredito: com P1, a V1.7 (teto da Tmax da previsão no recorde do pixel + folga) é justificada; sem P1, o ponto
#   quente é isolado e basta registrar. Nada é decidido sozinho: me envie o zip.
#
# COMO RODAR NO COLAB (fora da janela do motor, 22h50-01h00: comece até as 21h50 ou depois da 01h00; de preferência
#   depois das 08h, quando as tarefas da noite já terminaram)
#   Ambiente de execução -> Reiniciar sessão -> cole inteiro -> Ctrl+Enter. No fim, baixa auditoria_K24_<data>.zip.
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
ASSET_MATRIZ_GFS = f'projects/{PROJETO}/assets/SICSB_MATRIZ_GFS_V2'
BR_DWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
BLOCOS = [(-75.0, -5.0, -28.0, 6.5), (-75.0, -14.0, -28.0, -5.0), (-75.0, -23.0, -28.0, -14.0),
          (-75.0, -35.0, -28.0, -23.0)]                        # faixas de latitude (lon_min, lat_min, lon_max, lat_max)
BANDA = 'tmax_C'
ANOS_RECORDE = (1991, 2025)
DIAS_ERA5_REF = 30
FOLGAS = (0, 1, 2)
TMAX_RECORDE_BR = 44.8              # INMET (Araçuaí, 19/11/2023), o mesmo do motor
SALTO_MAX = 2.0                     # °C, o mesmo critério da PRÉVIA 6 do motor
P1_RAZAO, P1_MIN_PCT = 3.0, 0.05    # regra P1
DIAS_PONTO_QUENTE = 5               # regra P2
EFEITO_CALIB_MIN = 0.5              # regra P3, °C
MAX_PCT_TETO = 0.5                  # folga sugerida: o teto pega no máximo 0,5% dos pixel-dias GFS
N_PIORES = 10
RAZAO_MIN, RAZAO_MAX, RAZAO_MAX_LONGO = 0.5, 2.0, 1.0      # iguais ao motor (K7/K11)
FAIXAS_LONGAS = ('L6a10', 'L11a15')
DIAS_POR_PEDIDO = 8
JANELAS_MOTOR = [((22, 50), (24, 0)), ((0, 0), (1, 0))]
DURACAO_ESTIMADA_MIN = 60

BRT = timezone(timedelta(hours=-3))
AGORA = datetime.now(BRT)
PASTA = (f'/content/auditoria_K24_{AGORA:%Y%m%d_%H%M%S}' if os.path.isdir('/content')
         else f'auditoria_K24_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K24.txt')
RESULTADOS = []


def log(*partes):
    texto = ' '.join(str(p) for p in partes)
    print(texto)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(texto + '\n')


def resultado(item, status, titulo, texto):
    RESULTADOS.append({'item': item, 'status': status, 'titulo': titulo, 'texto': texto})
    simb = {'SIM': '⚠️', 'NÃO': '✅', 'INFO': 'ℹ️', 'FALHOU': '❌'}.get(status, '•')
    log(f'{simb} {item} {status}: {titulo}\n   {texto}')


def salvar_csv(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=False)


# =========================================================================================
# FUNÇÕES PURAS (testadas offline em testes/teste_k24.py)
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


def chave(d):
    return d.replace('-', '')


def agregar_blocos(partes, dias, com_teto):
    """partes: lista (um por bloco) de dicionários do servidor: {'max': {e_AAAAMMDD: ...}, 'g': {gK_AAAAMMDD_mean,
    gK_AAAAMMDD_count}, 'c': {cF_AAAAMMDD: ...}}. Devolve um DataFrame por dia: máximo nacional, % de pixels acima
    do recorde + 0/1/2 °C, maior excesso e (com_teto) a máxima nacional com o teto de cada folga."""
    linhas = []
    for d in dias:
        k = chave(d)
        lin = {'data': d, 'n_pix': 0}
        exc = [p['max'].get(f'e_{k}') for p in partes if p.get('max')]
        tmx = [p['max'].get(f't_{k}') for p in partes if p.get('max')]
        exc, tmx = [x for x in exc if x is not None], [x for x in tmx if x is not None]
        lin['tmax_max'] = max(tmx) if tmx else np.nan
        lin['excesso_max'] = max(exc) if exc else np.nan
        for g in FOLGAS:
            num = den = 0.0
            for p in partes:
                m, n = p['g'].get(f'g{g}_{k}_mean'), p['g'].get(f'g{g}_{k}_count')
                if m is not None and n:
                    num += m * n
                    den += n
            lin[f'pct_acima_{g}'] = 100 * num / den if den else np.nan
            if g == 0:
                lin['n_pix'] = int(den)
        if com_teto:
            for f in FOLGAS:
                v = [p['c'].get(f'c{f}_{k}') for p in partes if p.get('c')]
                v = [x for x in v if x is not None]
                lin[f'tmax_max_teto_{f}'] = max(v) if v else np.nan
        linhas.append(lin)
    return pd.DataFrame(linhas)


def pct_pixel_dias(tab, g):
    """% de pixel-dias acima do recorde + g (média ponderada pelos pixels de cada dia)."""
    t = tab.dropna(subset=[f'pct_acima_{g}'])
    return float((t[f'pct_acima_{g}'] * t['n_pix']).sum() / t['n_pix'].sum()) if t['n_pix'].sum() else float('nan')


def decidir_p1(pct_gfs, pct_era):
    return pct_gfs >= P1_MIN_PCT and pct_gfs >= P1_RAZAO * max(pct_era, 1e-9)


def razao_desvios(s_alvo, s_modelo, faixa):
    teto = RAZAO_MAX_LONGO if faixa in FAIXAS_LONGAS else RAZAO_MAX
    return float(np.clip(s_alvo / max(s_modelo, 1e-3), RAZAO_MIN, teto))


def bruto_de_calibrado(y, m_s, m_g, s_s, s_g, faixa):
    """Inverte a escala de variância do motor: y = m_s + (x - m_g) * r  ->  x = m_g + (y - m_s) / r."""
    r = razao_desvios(s_s, s_g, faixa)
    return m_g + (y - m_s) / r, r


def escolher_folga(tab_gfs, tmax_ultimo_era5, pct_teto):
    """tab_gfs: agregar_blocos dos dias GFS (com teto), em ordem de data; pct_teto: {folga: % de pixel-dias pegos}.
    Devolve (folga ou None, {folga: (máx nacional com teto, salto na emenda com teto, % pego, ok)})."""
    det = {}
    for f in FOLGAS:
        col = tab_gfs[f'tmax_max_teto_{f}']
        mx = float(col.max())
        salto = float(col.iloc[0] - tmax_ultimo_era5)
        pct = pct_teto.get(f, float('nan'))
        det[f] = (mx, salto, pct, mx <= TMAX_RECORDE_BR and abs(salto) <= SALTO_MAX and pct <= MAX_PCT_TETO)
    boas = [f for f in FOLGAS if det[f][3]]
    return (min(boas) if boas else None), det


# =========================================================================================
def principal():
    import ee
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log('=' * 100)
    log(f'K24 v1: AUDITORIA DO PONTO QUENTE DA TMAX NA PREVISÃO GFS (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log('=' * 100)
    falta = minutos_ate_janela(AGORA)
    if falta < DURACAO_ESTIMADA_MIN:
        log(f'⛔ Não comecei: a janela do motor começa em {falta} min. Comece até as 21h50 ou depois da 01h00.')
        return
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K24 é somente leitura: escrita bloqueada')
    for n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
              'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable', 'startIngestion',
              'cancelTask'):
        if hasattr(ee.data, n):
            setattr(ee.data, n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa.\n')

    TRANS = ('Too many concurrent', 'Internal error', 'Service Unavailable', '503', '429', 'deadline', 'Deadline',
             'Connection', 'temporarily')
    ESPERAS = [30, 60, 90, 120, 180, 240, 240]

    class Pesado(Exception):
        pass

    def gi(obj, rotulo, tentativas=len(ESPERAS) + 1):
        for t in range(tentativas):
            try:
                return obj.getInfo()
            except Exception as e:
                s = str(e)
                if 'memory' in s.lower() or 'timed out' in s.lower() or 'computation timed out' in s.lower():
                    raise Pesado(s)
                if t < tentativas - 1 and any(k in s for k in TRANS):
                    log(f'   ↻ {rotulo}: servidor ocupado ({s[:60]}); nova tentativa em {ESPERAS[t]} s')
                    time.sleep(ESPERAS[t])
                    continue
                raise

    def geom(b):
        return ee.Geometry.Rectangle(list(b), None, False)

    def rr(img, reducer, g):
        return img.reduceRegion(reducer=reducer, geometry=g, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10,
                                tileScale=16)

    def br_tmax(img):
        m = img.select('Tmax').gt(-32768)
        return ee.Image(img.select('Tmax').updateMask(m).multiply(0.00106815).add(15.0).rename(BANDA)
                        .copyProperties(img, ['system:time_start']))

    SAB = ee.ImageCollection(ASSET_SAB)
    BR = ee.ImageCollection(BR_DWGD)

    def sab_dia(d):
        return ee.Image(SAB.filterDate(d, ee.Date(d).advance(1, 'day')).first()).select(BANDA)

    _rec = {}

    def recorde(mes):
        if mes not in _rec:
            _rec[mes] = (BR.filter(ee.Filter.calendarRange(ANOS_RECORDE[0], ANOS_RECORDE[1], 'year'))
                         .filter(ee.Filter.calendarRange(mes, mes, 'month')).map(br_tmax).max().rename('rec'))
        return _rec[mes]

    # ------------------------------------------------------------------ A: inventário
    hoje = AGORA.strftime('%Y-%m-%d')
    col = SAB.filterDate((AGORA - timedelta(days=60)).strftime('%Y-%m-%d'), '2027-01-01')
    inv = gi(ee.List([col.aggregate_array('system:time_start'), col.aggregate_array('versao'),
                      col.aggregate_array('Faixa_Prazo_GFS'), col.aggregate_array('versao_algoritmo')]), 'inventário')
    if len(set(len(x) for x in inv)) > 1:   # aggregate_array pula imagens sem a propriedade: refaz por imagem
        inv2 = gi(col.toList(500).map(lambda i: ee.List([ee.Image(i).get('system:time_start'), ee.Image(i).get('versao'),
                                                         ee.Image(i).get('Faixa_Prazo_GFS'),
                                                         ee.Image(i).get('versao_algoritmo')])), 'inventário por imagem')
        inv = [list(x) for x in zip(*inv2)]
    dias = pd.DataFrame({'data': [datetime.fromtimestamp(t / 1000, timezone.utc).strftime('%Y-%m-%d') for t in inv[0]],
                         'versao': inv[1], 'faixa': inv[2], 'alg': inv[3]}).sort_values('data')
    era = list(dias.loc[dias['versao'] == 'provisoria_era5', 'data'])[-DIAS_ERA5_REF:]
    gfs = list(dias.loc[dias['versao'].isin(['provisoria_gfs', 'provisoria_gfs_incompleta']) &
                        (dias['data'] > (era[-1] if era else '')), 'data'])
    salvar_csv(dias, 'K24_A_inventario.csv')
    if not era or not gfs:
        resultado('A', 'FALHOU', 'dias ERA5 ou GFS não encontrados', f'{len(era)} ERA5, {len(gfs)} GFS')
        fechar(T0)
        return
    resultado('A', 'INFO', 'dias auditados', f'ERA5 (referência): {era[0]} a {era[-1]} ({len(era)} dias); GFS: {gfs[0]} '
              f'a {gfs[-1]} ({len(gfs)} dias); versões gravadas: {dict(dias["alg"].value_counts())}')

    # ------------------------------------------------------------------ B: excesso sobre o recorde do pixel
    def imagem_dias(lista, com_teto):
        e, g, c = [], [], []
        for d in lista:
            k = chave(d)
            t = sab_dia(d)
            rec = recorde(int(d[5:7]))
            exc = t.subtract(rec)
            e += [exc.rename(f'e_{k}'), t.rename(f't_{k}')]
            g += [exc.gt(x).rename(f'g{x}_{k}') for x in FOLGAS]
            if com_teto:
                c += [t.min(rec.add(f)).rename(f'c{f}_{k}') for f in FOLGAS]
        return ee.Image.cat(e), ee.Image.cat(g), (ee.Image.cat(c) if c else None)

    def pedir_bloco(lista, com_teto, b, rotulo, nivel=0):
        E, G, C = imagem_dias(lista, com_teto)
        g = geom(b)
        dic = {'max': rr(E, ee.Reducer.max(), g),
               'g': rr(G, ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True), g)}
        if C is not None:
            dic['c'] = rr(C, ee.Reducer.max(), g)
        try:
            return [gi(ee.Dictionary(dic), rotulo)]
        except Pesado:
            if nivel >= 2:
                raise
            lon0, lat0, lon1, lat1 = b
            meio = (lat0 + lat1) / 2
            log(f'   {rotulo}: pesado, dividindo o bloco')
            return (pedir_bloco(lista, com_teto, (lon0, lat0, lon1, meio), rotulo, nivel + 1)
                    + pedir_bloco(lista, com_teto, (lon0, meio, lon1, lat1), rotulo, nivel + 1))

    def auditar(lista, com_teto, nome):
        partes_por_lote = []
        for i in range(0, len(lista), DIAS_POR_PEDIDO):
            lote = lista[i:i + DIAS_POR_PEDIDO]
            partes = []
            for j, b in enumerate(BLOCOS):
                partes += pedir_bloco(lote, com_teto, b, f'{nome} {lote[0]} bloco {j + 1}')
            partes_por_lote.append(agregar_blocos(partes, lote, com_teto))
            log(f'   {nome}: {lote[0]} a {lote[-1]} lidos')
        return pd.concat(partes_por_lote, ignore_index=True)

    log(f'[B] Tmax acima do recorde do próprio pixel (BR-DWGD, mesmo mês, {ANOS_RECORDE[0]}-{ANOS_RECORDE[1]})')
    tab_era = auditar(era, False, 'ERA5')
    tab_gfs = auditar(gfs, True, 'GFS')
    tab_gfs['faixa'] = tab_gfs['data'].map(dict(zip(dias['data'], dias['faixa'])))
    salvar_csv(tab_era.round(4), 'K24_B_era5_por_dia.csv')
    salvar_csv(tab_gfs.round(4), 'K24_B_gfs_por_dia.csv')
    log('\nERA5 (referência):\n' + tab_era.round(3).to_string(index=False))
    log('\nGFS:\n' + tab_gfs.round(3).to_string(index=False))
    pct = {fonte: {g: pct_pixel_dias(t, g) for g in FOLGAS} for fonte, t in (('ERA5', tab_era), ('GFS', tab_gfs))}
    p1 = decidir_p1(pct['GFS'][1], pct['ERA5'][1])
    resultado('P1', 'SIM' if p1 else 'NÃO', 'excesso sistemático da Tmax do GFS sobre o recorde do pixel',
              ' | '.join(f'acima do recorde + {g} °C: GFS {pct["GFS"][g]:.3f}% x ERA5 {pct["ERA5"][g]:.3f}% dos pixel-dias'
                         for g in FOLGAS) + f' | maior excesso GFS {tab_gfs["excesso_max"].max():+.1f} °C, ERA5 '
              f'{tab_era["excesso_max"].max():+.1f} °C')

    # ------------------------------------------------------------------ C: pontos quentes
    log(f'\n[C] pontos quentes: acima do recorde + 1 °C em {DIAS_PONTO_QUENTE} dias GFS ou mais')
    excs = ee.ImageCollection([sab_dia(d).subtract(recorde(int(d[5:7]))) for d in gfs])
    H = excs.map(lambda x: x.gt(1)).sum().rename('dias_acima')
    M = excs.max().rename('excesso_max')
    T = ee.ImageCollection([sab_dia(d) for d in gfs]).mean().rename('tmax_gfs_media')
    Te = ee.ImageCollection([sab_dia(d) for d in era[-10:]]).mean().rename('tmax_era5_media_10d')
    R = recorde(int(gfs[0][5:7])).rename('recorde_mes')
    alvo = H.addBands([M, T, Te, R]).updateMask(H.gte(DIAS_PONTO_QUENTE))
    quentes = []
    for j, b in enumerate(BLOCOS):
        fs = gi(alvo.sample(region=geom(b), projection=ee.Projection(CRS, TRANSFORM), geometries=True,
                            numPixels=1e6, tileScale=16).limit(2000), f'pontos quentes bloco {j + 1}')['features']
        for f in fs:
            p = f['properties']
            quentes.append({'lon': round(f['geometry']['coordinates'][0], 3), 'lat': round(f['geometry']['coordinates'][1], 3),
                            **{k: p.get(k) for k in ('dias_acima', 'excesso_max', 'tmax_gfs_media',
                                                     'tmax_era5_media_10d', 'recorde_mes')}})
    tq = pd.DataFrame(quentes, columns=['lon', 'lat', 'dias_acima', 'excesso_max', 'tmax_gfs_media',
                                        'tmax_era5_media_10d', 'recorde_mes'])
    tq = tq.drop_duplicates(['lon', 'lat']).sort_values(['dias_acima', 'excesso_max'], ascending=False)
    salvar_csv(tq.round(3), 'K24_C_pontos_quentes.csv')
    if len(tq):
        log(tq.head(20).round(2).to_string(index=False))
    resultado('P2', 'INFO', f'pontos quentes (acima do recorde + 1 °C em {DIAS_PONTO_QUENTE} dias GFS ou mais)',
              f'{len(tq)} pixels' + (f'; o pior em ({tq.iloc[0]["lon"]:.2f}; {tq.iloc[0]["lat"]:.2f}): '
                                     f'{tq.iloc[0]["dias_acima"]:.0f} dias, excesso até {tq.iloc[0]["excesso_max"]:+.1f} °C, '
                                     f'GFS {tq.iloc[0]["tmax_gfs_media"]:.1f} x ERA5 {tq.iloc[0]["tmax_era5_media_10d"]:.1f} °C '
                                     f'(médias)' if len(tq) else ''))

    # ------------------------------------------------------------------ D: bruto x calibração nos piores
    log(f'\n[D] nos {N_PIORES} piores pontos quentes: GFS bruto (recuperado pela conta do motor) x calibrado')
    p3, efeito_medio = None, float('nan')
    if len(tq):
        pior = tq.head(N_PIORES).reset_index(drop=True)
        pts = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {'i': i}) for i, r in pior.iterrows()])
        mp = ee.Geometry.MultiPoint([[r.lon, r.lat] for r in pior.itertuples()])
        reg = gi(ee.ImageCollection([sab_dia(d).set('system:time_start', ee.Date(d).millis()) for d in gfs])
                 .getRegion(mp, None, CRS, TRANSFORM), 'GFS nos pontos')
        dfp = pd.DataFrame(reg[1:], columns=reg[0])
        dfp['data'] = pd.to_datetime(dfp['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
        meses = sorted({int(d[5:7]) for d in gfs})
        faixas = sorted({f for f in tab_gfs['faixa'].dropna()})
        bandas = [f'Tmax_{t}_{fonte}_{fx}' for t in ('m', 's') for fonte in ('sicsb', 'gfs') for fx in faixas]
        mat = {}
        for m in meses:
            fs = gi(ee.Image(f'{ASSET_MATRIZ_GFS}/Matriz_GFS_{m:02d}').select(bandas)
                    .sampleRegions(collection=pts, properties=['i'], scale=11132, geometries=False), f'matriz {m:02d}')
            for f in fs['features']:
                mat[(m, f['properties']['i'])] = f['properties']
        linhas = []
        for i, r in pior.iterrows():
            sub = dfp[(dfp['longitude'].astype(float).sub(r.lon).abs() < 0.06) &
                      (dfp['latitude'].astype(float).sub(r.lat).abs() < 0.06)]
            for _, s in sub.iterrows():
                y = s[BANDA]
                fx = dict(zip(tab_gfs['data'], tab_gfs['faixa'])).get(s['data'])
                mm = mat.get((int(s['data'][5:7]), i), {})
                ok = y is not None and fx and all(mm.get(f'Tmax_{t}_{fo}_{fx}') is not None
                                                  for t in ('m', 's') for fo in ('sicsb', 'gfs'))
                if not ok:
                    continue
                x, rz = bruto_de_calibrado(float(y), mm[f'Tmax_m_sicsb_{fx}'], mm[f'Tmax_m_gfs_{fx}'],
                                           mm[f'Tmax_s_sicsb_{fx}'], mm[f'Tmax_s_gfs_{fx}'], fx)
                linhas.append({'ponto': i, 'lon': r.lon, 'lat': r.lat, 'data': s['data'], 'faixa': fx,
                               'tmax_calibrada': float(y), 'tmax_bruta': x, 'efeito_calibracao': float(y) - x,
                               'm_sicsb': mm[f'Tmax_m_sicsb_{fx}'], 'm_gfs': mm[f'Tmax_m_gfs_{fx}'], 'razao': rz,
                               'recorde_mes': r.recorde_mes})
        td = pd.DataFrame(linhas)
        salvar_csv(td.round(3), 'K24_D_bruto_x_calibrado.csv')
        if len(td):
            res = td.groupby(['ponto', 'lon', 'lat']).agg(dias=('data', 'size'), bruta=('tmax_bruta', 'mean'),
                                                          calibrada=('tmax_calibrada', 'mean'),
                                                          efeito=('efeito_calibracao', 'mean'),
                                                          offset_medias=('m_sicsb', 'mean'), razao=('razao', 'mean'),
                                                          recorde=('recorde_mes', 'first')).reset_index()
            res['offset_medias'] = (td.groupby('ponto')['m_sicsb'].mean() - td.groupby('ponto')['m_gfs'].mean()).values
            log(res.round(2).to_string(index=False))
            efeito_medio = float(td['efeito_calibracao'].mean())
            p3 = efeito_medio > EFEITO_CALIB_MIN
            resultado('P3', 'SIM' if p3 else 'NÃO', 'a calibração aumenta o calor nos pontos quentes',
                      f'efeito médio da calibração {efeito_medio:+.2f} °C (limite {EFEITO_CALIB_MIN:+.1f}); GFS bruto '
                      f'médio {td["tmax_bruta"].mean():.1f} °C, calibrado {td["tmax_calibrada"].mean():.1f} °C, '
                      f'recorde do mês {pior["recorde_mes"].mean():.1f} °C')
        else:
            resultado('P3', 'FALHOU', 'decomposição bruto x calibrado', 'sem dados da matriz nos pontos')

    # ------------------------------------------------------------------ E: efeito de um teto
    log('\n[E] um teto da Tmax da previsão no recorde do pixel + folga')
    t_ult = float(tab_era['tmax_max'].iloc[-1])
    pct_teto = {f: pct['GFS'][f] for f in FOLGAS}
    folga, det = escolher_folga(tab_gfs, t_ult, pct_teto)
    for f in FOLGAS:
        mx, salto, pc, ok = det[f]
        log(f'   folga {f} °C: máxima nacional dos dias GFS até {mx:.1f} °C; emenda {t_ult:.1f} -> '
            f'{tab_gfs[f"tmax_max_teto_{f}"].iloc[0]:.1f} °C ({salto:+.1f}); pega {pc:.3f}% dos pixel-dias '
            f'{"✅" if ok else "—"}')
    resultado('E', 'INFO', 'folga sugerida para o teto da V1.7',
              (f'{folga} °C acima do recorde do pixel no mês' if folga is not None else
               'nenhuma folga de 0 a 2 °C atende às três condições: o teto sozinho não basta')
              + f' (condições: máxima nacional <= {TMAX_RECORDE_BR} °C, emenda <= {SALTO_MAX:.0f} °C, '
                f'pega <= {MAX_PCT_TETO}% dos pixel-dias)')

    fechar(T0, p1, p3, folga)


def fechar(T0, p1=None, p3=None, folga=None):
    log('\n' + '=' * 100)
    log('RESULTADO K24')
    log('=' * 100)
    for r in RESULTADOS:
        log(f'   {r["item"]:<3} {r["status"]:<7} {r["titulo"]}')
    salvar_csv(pd.DataFrame(RESULTADOS), 'K24_RESUMO.csv')
    if p1 is None:
        log('\n   ⛔ Auditoria incompleta: me envie o zip.')
    elif p1:
        log('\n   ⚠️ Excesso sistemático da Tmax do GFS sobre o recorde do pixel: a V1.7 (teto da Tmax da previsão'
            + (f' no recorde do pixel + {folga} °C' if folga is not None else '') + ') é justificada'
            + ('; a calibração aumenta o calor' if p3 else '; o excesso vem do próprio GFS' if p3 is not None else '')
            + '. Me envie o zip: preparo a V1.7 e a validação fora da amostra.')
    else:
        log('\n   ✅ Sem excesso sistemático: o ponto quente é isolado. Me envie o zip para registrarmos.')
    log(f'\nTempo: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine (trava de somente leitura).')


if __name__ == '__main__' or __name__ == 'k24':
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
