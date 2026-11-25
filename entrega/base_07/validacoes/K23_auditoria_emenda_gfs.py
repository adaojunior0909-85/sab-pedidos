# >>> AUDITORIA K23 (08/11/2026): o aviso da emenda ERA5 -> GFS (Tmax) indica defeito? Somente leitura. Cole inteiro, sem editar. <<<
# =========================================================================================
# K23 - AUDITORIA FINAL DA EMENDA ERA5 -> GFS DA TEMPERATURA MÁXIMA (antes do passo E2-5)
#
# POR QUE EXISTE
#   A simulação do motor V1.6 (05a, 08/11/2026, 20h22) aprovou tudo o que a V1.6 muda, mas terminou com "NÃO EXECUTE
#   AINDA" por um critério da rota GFS: a Tmax máxima nacional foi de 41,4 °C (01/11, último dia ERA5) para 44,3 °C
#   (02/11, 1º dia GFS), +2,8 °C, limite +-2 °C. Os dias GFS da V1.6 saíram IGUAIS aos gravados pela V1.5 (que está no ar).
#
# O QUE JÁ ESTÁ PROVADO SEM RODAR NADA (conferência do código, 08/11/2026)
#   Entre o 05a V1.5 e o 05a V1.6, 73 funções são idênticas. Na processarDia_GFS mudam só: o teto da chuva, o limite da
#   radiação (céu claro) e as propriedades gravadas. As linhas da Tmax e da Tmin dos dias GFS (calib_variancia,
#   calib_limitada_gfs, matriz V2.1) são as mesmas. Logo, a V1.6 não cria nem muda esse salto.
#
# O QUE A K23 MEDE (só leitura; regras fixadas ANTES de rodar)
#   S  SALTO NA EMENDA, refeito com o banco de hoje: Tmax máxima nacional (todos os pixels e só os pixels A) e o
#      percentil 99 nacional do último dia ERA5 e do 1º dia GFS. Só informação (confere a PRÉVIA 6).
#   N  VARIAÇÃO NATURAL: nos dias ERA5 de 2026 (mesma fonte, sem emenda), a distribuição do |salto| da Tmax máxima
#      nacional entre dias seguidos. APROVADO se pelo menos 1% dos pares de dias seguidos tiver |salto| >= o salto da
#      emenda (o salto da emenda não é raro demais para ser só tempo). Referência extra (informação): BR-DWGD de
#      outubro a dezembro, 1991-2025.
#   R  CAUDA QUENTE: % dos pixels A com Tmax acima do recorde do próprio pixel no mês (maior valor de 1991-2025 no
#      banco), nos 14 últimos dias ERA5 e nos 5 primeiros dias GFS (prazos L1 a L5). APROVADO se a média dos dias GFS
#      for <= máx(2 x a média dos dias ERA5; média ERA5 + 0,5 ponto percentual): a calibração do GFS não infla a cauda.
#   P  PIXEL MAIS QUENTE do 1º dia GFS: onde fica, a classe, o recorde do pixel no mês e a série dos últimos dias no
#      mesmo pixel. Só informação.
#   V  VERIFICAÇÃO DEPOIS DO FATO: quando o banco tiver o ERA5 de 02/11/2026 (o motor troca o GFS pelo ERA5 sozinho), a
#      K23 compara a Tmax máxima nacional prevista (44,3 °C, PRÉVIA 6) com a medida. Antes disso: ESPERAR.
#   CONCLUSÃO: com N e R aprovados, o aviso da emenda não indica defeito (variação do tempo, sem inflar a cauda): seguir
#   com o E2-5, com a exceção registrada. Com R reprovado: a calibração da Tmax do GFS infla a cauda quente; isso já
#   está no ar com a V1.5 e a V1.6 não muda, mas vira uma correção própria (rota GFS) antes de fechar a etapa 2.
#
# COMO RODAR NO COLAB (fora da janela do motor, 22h50-01h00: comece até as 22h10 ou depois da 01h00)
#   Ambiente de execução -> Reiniciar sessão -> cole inteiro -> Ctrl+Enter. Tempo: 10 a 40 min. Somente leitura:
#   criar, apagar, exportar e cancelar ficam bloqueados. No fim, baixa validacao_K23_<data>.zip. Me envie.
# =========================================================================================
import math
import os
import shutil
import time
import traceback
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

PROJETO = 'clima-492922'
ASSET_SAB = f'projects/{PROJETO}/assets/SAB_V1'
ASSET_MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
REGIAO_COORDS = [-75.0, -35.0, -28.0, 6.5]
ANO_ATUAL = 2026
ANOS_RECORDE = (1991, 2025)
ANOS_NATURAL_BR = (1991, 2025)
MESES_NATURAL_BR = (10, 11, 12)
DIAS_ERA5_R = 14
DIAS_GFS_R = 5
FRACAO_MIN_N = 0.01              # N: pelo menos 1% dos pares de dias seguidos com |salto| >= o da emenda
FATOR_R, FOLGA_R = 2.0, 0.5      # R: GFS <= máx(2 x ERA5, ERA5 + 0,5 ponto percentual)
SNAPSHOT_PREVIA6 = {'2026-11-02': 44.28, '2026-11-09': 43.80, '2026-11-15': 41.37, '2026-11-18': 42.10}
SALTO_PREVIA6 = (41.43, 44.28)   # último ERA5 (01/11) -> 1º GFS (02/11), PRÉVIA 6 do 05a V1.6
VERSOES_GFS = ('provisoria_gfs', 'provisoria_gfs_incompleta', 'falha_latencia_gfs')
JANELAS_MOTOR = [((22, 50), (24, 0)), ((0, 0), (1, 0))]     # motor 1x por dia às 23h07 (GitHub ~23h47)
DURACAO_ESTIMADA_MIN = 40

BRT = timezone(timedelta(hours=-3))
AGORA = datetime.now(BRT)
PASTA = (f'/content/validacao_K23_{AGORA:%Y%m%d_%H%M%S}' if os.path.isdir('/content')
         else f'validacao_K23_{AGORA:%Y%m%d_%H%M%S}')
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
    simb = {'APROVADO': '✅', 'REPROVADO': '❌', 'INFO': 'ℹ️', 'FALHOU': '⚠️', 'ESPERAR': '⏳'}.get(status, '•')
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


def saltos_seguidos(df, col='max'):
    """df: colunas data (AAAA-MM-DD) e col. Devolve os saltos (dia - véspera) só entre dias de calendário seguidos."""
    d = df[['data', col]].dropna().copy()
    d['dt'] = pd.to_datetime(d['data'])
    d = d.sort_values('dt').drop_duplicates('dt')
    dif = d[col].diff()
    seguido = d['dt'].diff() == pd.Timedelta(days=1)
    return dif[seguido].astype(float).values


def resumo_saltos(saltos, salto_emenda):
    a = np.abs(np.asarray(saltos, float))
    if not len(a):
        return {'n': 0, 'frac_acima_2': float('nan'), 'p95': float('nan'), 'p99': float('nan'), 'max': float('nan'),
                'frac_ge_emenda': float('nan')}
    return {'n': int(len(a)), 'frac_acima_2': float((a > 2.0).mean()), 'p95': float(np.percentile(a, 95)),
            'p99': float(np.percentile(a, 99)), 'max': float(a.max()),
            'frac_ge_emenda': float((a >= abs(salto_emenda) - 1e-9).mean())}


def decidir_n(resumo):
    return resumo['n'] >= 30 and resumo['frac_ge_emenda'] >= FRACAO_MIN_N


def decidir_r(media_gfs, media_era):
    return media_gfs <= max(FATOR_R * media_era, media_era + FOLGA_R)


def conclusao(st):
    """st: {'N': status, 'R': status}. Devolve (código, frase)."""
    n, r = st.get('N'), st.get('R')
    if n == 'APROVADO' and r == 'APROVADO':
        return 'seguir', ('✅ O AVISO DA EMENDA NÃO INDICA DEFEITO: o salto está dentro da variação natural do tempo e a '
                          'calibração do GFS não infla a cauda quente. Pode seguir com o E2-5 (exceção registrada).')
    if r == 'REPROVADO':
        return 'corrigir_gfs', ('⚠️ A CALIBRAÇÃO DA TMAX DO GFS INFLA A CAUDA QUENTE. Isso já está no ar com a V1.5 e a '
                                'V1.6 não muda (a rota da Tmax é a mesma): me envie o zip para decidirmos a correção da '
                                'rota GFS antes de fechar a etapa 2.')
    if n == 'REPROVADO' and r == 'APROVADO':
        return 'acompanhar', ('ℹ️ Salto raro para um dia só, mas sem inflar a cauda: provável evento real. Me envie o zip; '
                              'a confirmação vem pela parte V quando o ERA5 de 02/11 chegar.')
    return 'incompleto', '⏳ Partes sem resultado: me envie o zip (o log diz o que faltou).'


# =========================================================================================
def principal():
    import ee
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log('=' * 100)
    log(f'K23: AUDITORIA DA EMENDA ERA5 -> GFS DA TMAX (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log('=' * 100)
    falta = minutos_ate_janela(AGORA)
    if falta < DURACAO_ESTIMADA_MIN:
        log(f'⛔ Não comecei: a janela do motor começa em {falta} min e a K23 pode levar até {DURACAO_ESTIMADA_MIN} '
            'min. Comece até as 22h10 ou depois da 01h00.')
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
    log('🔒 Trava de somente leitura ativa (criar, apagar, exportar e cancelar bloqueados).')
    log('ℹ️ Já provado pelo código (08/11): a V1.6 não muda a Tmax nem a Tmin dos dias GFS (73 funções iguais; na '
        'processarDia_GFS só mudam chuva, radiação e propriedades).\n')

    REGIAO = ee.Geometry.Rectangle(REGIAO_COORDS, None, False)
    A = ee.Image(ASSET_MASCARA).select('classe').eq(1)
    COL = ee.ImageCollection(ASSET_SAB)
    RED = ee.Reducer.max().combine(ee.Reducer.percentile([99]), sharedInputs=True)
    TRANS = ('Too many concurrent', 'Internal error', 'Service Unavailable', '503', '429', 'deadline', 'Deadline',
             'Connection', 'temporarily')

    def gi(obj, rotulo, tentativas=6):
        for t in range(tentativas):
            try:
                return obj.getInfo()
            except Exception as e:
                if t < tentativas - 1 and any(k in str(e) for k in TRANS):
                    log(f'   ↻ {rotulo}: erro transitório; nova tentativa em {20 * (t + 1)} s')
                    time.sleep(20 * (t + 1))
                    continue
                raise

    def reduzir(img, mascara=None, tile=4):
        t = img.select('tmax_C')
        if mascara is not None:
            t = t.updateMask(mascara)
        return t.reduceRegion(reducer=RED, geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10,
                              tileScale=tile)

    def estat(img):
        r, ra = reduzir(img), reduzir(img, A)
        return ee.Feature(None, {'t': img.get('system:time_start'), 'versao': img.get('versao'),
                                 'max': r.get('tmax_C_max'), 'p99': r.get('tmax_C_p99'),
                                 'maxA': ra.get('tmax_C_max'), 'p99A': ra.get('tmax_C_p99')})

    def tabela(ini, fim, rotulo):
        """Estatísticas nacionais diárias da Tmax entre ini e fim (fim exclusivo), um pedido; divide se pesado."""
        try:
            fs = gi(COL.filterDate(ini, fim).map(estat), rotulo)['features']
        except Exception as e:
            s = str(e).lower()
            d0, d1 = date.fromisoformat(ini), date.fromisoformat(fim)
            if ('memory' in s or 'timed out' in s or 'too many' in s) and (d1 - d0).days > 3:
                meio = (d0 + (d1 - d0) / 2).isoformat()
                log(f'   {rotulo}: pesado, dividindo ({ini} a {meio} e {meio} a {fim})')
                return pd.concat([tabela(ini, meio, rotulo), tabela(meio, fim, rotulo)], ignore_index=True)
            raise
        linhas = [{'data': datetime.fromtimestamp(f['properties']['t'] / 1000, timezone.utc).strftime('%Y-%m-%d'),
                   **{k: f['properties'].get(k) for k in ('versao', 'max', 'p99', 'maxA', 'p99A')}} for f in fs]
        return pd.DataFrame(linhas, columns=['data', 'versao', 'max', 'p99', 'maxA', 'p99A'])

    # ------------------------------------------------------------------ 2026 inteiro (ERA5 provisório e GFS)
    log(f'[2026] Tmax máxima e percentil 99 nacionais de cada dia de {ANO_ATUAL} (um pedido por mês)')
    partes = []
    for m in range(1, 13):
        ini = f'{ANO_ATUAL}-{m:02d}-01'
        fim = f'{ANO_ATUAL + 1}-01-01' if m == 12 else f'{ANO_ATUAL}-{m + 1:02d}-01'
        tb = tabela(ini, fim, f'{ANO_ATUAL}-{m:02d}')
        if len(tb):
            log(f'   {ANO_ATUAL}-{m:02d}: {len(tb)} dias ({", ".join(f"{v} {n}" for v, n in tb["versao"].value_counts().items())})')
        partes.append(tb)
    d26 = pd.concat(partes, ignore_index=True).sort_values('data').reset_index(drop=True)
    for c in ('max', 'p99', 'maxA', 'p99A'):
        d26[c] = pd.to_numeric(d26[c], errors='coerce')
    salvar_csv(d26.round(3), 'K23_2026_tmax_nacional.csv')
    era = d26[d26['versao'] == 'provisoria_era5']
    gfs = d26[d26['versao'].isin(VERSOES_GFS)]
    if not len(era) or not len(gfs):
        resultado('S', 'FALHOU', 'emenda ERA5 -> GFS', f'dias ERA5: {len(era)}; dias GFS: {len(gfs)}')
        fechar(T0)
        return
    ue, pg = era.iloc[-1], gfs[gfs['data'] > era['data'].max()].iloc[0]
    salto = float(pg['max'] - ue['max'])
    resultado('S', 'INFO', f'emenda {ue["data"]} (ERA5) -> {pg["data"]} (GFS), banco de hoje',
              f'Tmax máx. nacional {ue["max"]:.2f} -> {pg["max"]:.2f} °C ({salto:+.2f}); só pixels A {ue["maxA"]:.2f} -> '
              f'{pg["maxA"]:.2f} ({pg["maxA"] - ue["maxA"]:+.2f}); percentil 99 {ue["p99"]:.2f} -> {pg["p99"]:.2f} '
              f'({pg["p99"] - ue["p99"]:+.2f}) | PRÉVIA 6: {SALTO_PREVIA6[0]} -> {SALTO_PREVIA6[1]}')
    snap = gfs[['data', 'versao', 'max', 'maxA', 'p99']].copy()
    salvar_csv(snap.round(3), 'K23_snapshot_dias_gfs.csv')       # para a parte V, depois

    # ------------------------------------------------------------------ N: variação natural
    log('\n[N] variação natural da Tmax máxima nacional entre dias seguidos')
    try:
        s26 = saltos_seguidos(era, 'max')
        r26 = resumo_saltos(s26, salto)
        s26a = resumo_saltos(saltos_seguidos(era, 'maxA'), pg['maxA'] - ue['maxA'])
        s26p = resumo_saltos(saltos_seguidos(era, 'p99'), pg['p99'] - ue['p99'])
        hist = []
        for ano in range(ANOS_NATURAL_BR[0], ANOS_NATURAL_BR[1] + 1):
            tb = tabela(f'{ano}-{MESES_NATURAL_BR[0]:02d}-01', f'{ano + 1}-01-01', f'BR-DWGD {ano}')
            hist.append(tb[tb['versao'] == 'definitiva'])
        dh = pd.concat(hist, ignore_index=True)
        for c in ('max', 'p99', 'maxA', 'p99A'):
            dh[c] = pd.to_numeric(dh[c], errors='coerce')
        salvar_csv(dh.round(3), 'K23_historico_out_dez_tmax_nacional.csv')
        rh = resumo_saltos(saltos_seguidos(dh, 'max'), salto)
        tab = pd.DataFrame([{'fonte': f'ERA5 {ANO_ATUAL} (Tmax máx.)', **r26}, {'fonte': f'ERA5 {ANO_ATUAL} (só pixels A)', **s26a},
                            {'fonte': f'ERA5 {ANO_ATUAL} (percentil 99)', **s26p},
                            {'fonte': f'BR-DWGD out-dez {ANOS_NATURAL_BR[0]}-{ANOS_NATURAL_BR[1]} (Tmax máx.)', **rh}])
        salvar_csv(tab.round(4), 'K23_N_saltos_naturais.csv')
        log(tab.round(3).to_string(index=False))
        resultado('N', 'APROVADO' if decidir_n(r26) else 'REPROVADO',
                  f'salto da emenda ({salto:+.2f} °C) x variação natural dos dias ERA5 de {ANO_ATUAL}',
                  f'{r26["n"]} pares de dias seguidos; |salto| >= {abs(salto):.2f} °C em {100 * r26["frac_ge_emenda"]:.1f}% '
                  f'(mínimo {100 * FRACAO_MIN_N:.0f}%); acima de 2 °C em {100 * r26["frac_acima_2"]:.1f}%; p95 '
                  f'{r26["p95"]:.2f}, p99 {r26["p99"]:.2f}, maior {r26["max"]:.2f} °C | BR-DWGD out-dez: acima de 2 °C em '
                  f'{100 * rh["frac_acima_2"]:.1f}%, |salto| >= o da emenda em {100 * rh["frac_ge_emenda"]:.1f}%')
    except Exception as e:
        resultado('N', 'FALHOU', 'variação natural', str(e)[:300])

    # ------------------------------------------------------------------ R: cauda quente x recorde do pixel
    log(f'\n[R] pixels A acima do recorde do próprio pixel no mês ({ANOS_RECORDE[0]}-{ANOS_RECORDE[1]})')
    try:
        def recorde(m):
            return (COL.filter(ee.Filter.calendarRange(ANOS_RECORDE[0], ANOS_RECORDE[1], 'year'))
                    .filter(ee.Filter.calendarRange(m, m, 'month')).filter(ee.Filter.eq('versao', 'definitiva'))
                    .select('tmax_C').max())
        recs = {}
        dias_e = list(era['data'].iloc[-DIAS_ERA5_R:])
        dias_g = list(gfs[gfs['data'] > era['data'].max()]['data'].iloc[:DIAS_GFS_R])
        linhas = []
        for d in dias_e + dias_g:
            m = int(d[5:7])
            recs.setdefault(m, recorde(m))
            img = ee.Image(COL.filterDate(d, ee.Date(d).advance(1, 'day')).first()).select('tmax_C').updateMask(A)
            acima = img.gt(recs[m]).rename('acima')
            acima1 = img.gt(recs[m].add(1)).rename('acima1')
            r = gi(ee.Image.cat([acima, acima1, img.mask().rename('n')]).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4),
                f'recorde {d}')
            n = r.get('n') or 0
            linhas.append({'data': d, 'fonte': 'GFS' if d in dias_g else 'ERA5', 'pixels_A': n,
                           'pct_acima_recorde': 100 * (r.get('acima') or 0) / n if n else float('nan'),
                           'pct_acima_recorde_mais_1C': 100 * (r.get('acima1') or 0) / n if n else float('nan')})
            log(f'   {d} {linhas[-1]["fonte"]}: {linhas[-1]["pct_acima_recorde"]:.3f}% acima do recorde '
                f'({linhas[-1]["pct_acima_recorde_mais_1C"]:.3f}% acima do recorde + 1 °C)')
        tr = pd.DataFrame(linhas)
        salvar_csv(tr.round(4), 'K23_R_acima_do_recorde.csv')
        me = float(tr.loc[tr['fonte'] == 'ERA5', 'pct_acima_recorde'].mean())
        mg = float(tr.loc[tr['fonte'] == 'GFS', 'pct_acima_recorde'].mean())
        resultado('R', 'APROVADO' if decidir_r(mg, me) else 'REPROVADO',
                  'cauda quente: pixels A acima do recorde do pixel no mês',
                  f'média dos {len(dias_e)} últimos dias ERA5 {me:.3f}% x {len(dias_g)} primeiros dias GFS {mg:.3f}% '
                  f'(limite: até {max(FATOR_R * me, me + FOLGA_R):.3f}%)')
    except Exception as e:
        resultado('R', 'FALHOU', 'cauda quente', str(e)[:300])

    # ------------------------------------------------------------------ P: pixel mais quente do 1º dia GFS
    log(f'\n[P] pixel mais quente do 1º dia GFS ({pg["data"]})')
    try:
        img = ee.Image(COL.filterDate(pg['data'], ee.Date(pg['data']).advance(1, 'day')).first()).select('tmax_C')
        r = gi(img.addBands(ee.Image.pixelLonLat()).reduceRegion(
            reducer=ee.Reducer.max(3), geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4),
            'pixel mais quente')
        tmax, lon, lat = r.get('max'), r.get('max1'), r.get('max2')
        ponto = ee.Geometry.Point([lon, lat])
        m = int(pg['data'][5:7])
        info = gi(ee.Image.cat([ee.Image(ASSET_MASCARA).select('classe'),
                                (COL.filter(ee.Filter.calendarRange(ANOS_RECORDE[0], ANOS_RECORDE[1], 'year'))
                                 .filter(ee.Filter.calendarRange(m, m, 'month')).filter(ee.Filter.eq('versao', 'definitiva'))
                                 .select('tmax_C').max().rename('recorde'))])
                  .reduceRegion(ee.Reducer.first(), ponto, crs=CRS, crsTransform=TRANSFORM), 'classe e recorde')
        ini = (date.fromisoformat(pg['data']) - timedelta(days=14)).isoformat()
        fim = (date.fromisoformat(pg['data']) + timedelta(days=8)).isoformat()
        reg = gi(COL.filterDate(ini, fim).select('tmax_C').getRegion(ponto, None, CRS, TRANSFORM), 'série do pixel')
        serie = pd.DataFrame(reg[1:], columns=reg[0])
        serie['data'] = pd.to_datetime(serie['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
        serie = serie.merge(d26[['data', 'versao']], on='data', how='left')[['data', 'versao', 'tmax_C']]
        salvar_csv(serie, 'K23_P_serie_pixel_mais_quente.csv')
        log(serie.to_string(index=False))
        cls = {1: 'A', 2: 'B', 3: 'C'}.get(info.get('classe'), str(info.get('classe')))
        rec = info.get('recorde')
        resultado('P', 'INFO', f'pixel mais quente de {pg["data"]}: {tmax:.2f} °C em ({lon:.2f}; {lat:.2f}), classe {cls}',
                  f'recorde do pixel em {m:02d} ({ANOS_RECORDE[0]}-{ANOS_RECORDE[1]}): '
                  f'{"?" if rec is None else f"{rec:.2f} °C"}; '
                  f'{"" if rec is None else f"diferença {tmax - rec:+.2f} °C; "}série no arquivo K23_P_serie_pixel_mais_quente.csv')
    except Exception as e:
        resultado('P', 'FALHOU', 'pixel mais quente', str(e)[:300])

    # ------------------------------------------------------------------ V: depois do fato
    log('\n[V] verificação depois do fato (previsto pelo GFS x medido pelo ERA5)')
    medidos = d26[(d26['data'].isin(SNAPSHOT_PREVIA6)) & (d26['versao'] == 'provisoria_era5')]
    if not len(medidos):
        resultado('V', 'ESPERAR', 'Tmax máxima nacional prevista x medida',
                  f'o banco ainda não tem o ERA5 de {min(SNAPSHOT_PREVIA6)} (último ERA5: {era["data"].max()}); rode a K23 '
                  'de novo daqui a alguns dias para fechar esta parte')
    else:
        txt = '; '.join(f'{r.data}: previsto {SNAPSHOT_PREVIA6[r.data]:.2f}, medido {r.max:.2f} °C '
                        f'({r.max - SNAPSHOT_PREVIA6[r.data]:+.2f})' for r in medidos.itertuples())
        resultado('V', 'INFO', 'Tmax máxima nacional prevista (GFS, PRÉVIA 6) x medida (ERA5)', txt)

    fechar(T0)


def fechar(T0):
    log('\n' + '=' * 100)
    log('RESULTADO K23')
    log('=' * 100)
    for r in RESULTADOS:
        log(f'   {r["item"]:<3} {r["status"]:<10} {r["titulo"]}')
    salvar_csv(pd.DataFrame(RESULTADOS), 'K23_RESUMO.csv')
    st = {r['item']: r['status'] for r in RESULTADOS}
    log('\n   ' + conclusao(st)[1])
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
