# >>> K18: AUDITORIA DO ERA5-LAND E DOS PIXELS B (03/11/2026). SOMENTE LEITURA. Cole inteiro numa célula do Colab. <<<
# =========================================================================================
# POR QUE EXISTE
#   A K17 (03/11/2026) mostrou que o código V1.0 reproduz o histórico gravado, menos as variáveis ACUMULADAS do
#   ERA5-Land (ET real, transpiração, escoamento...) em 15/01/2020 e 31/12/2025: a fonte foi revista no Earth Engine
#   depois da gravação. Também confirmou o defeito conhecido da V1.0 nos pixels B (lagoas e estuários): ali o BR-DWGD
#   existe, mas foi descartado. Antes de decidir qualquer correção, a K18 mede as duas coisas com números.
#
# O QUE FAZ (nada é gravado no Earth Engine)
#   Q1  A partir de quando o ERA5-Land mudou? Um dia por mês de 2014 a 2025 (dia 15) e 6 dias de controle de 1961
#       a 2013. Em todos os pixels A do Brasil, refaz a ET real e a transpiração exatamente como a V1.0
#       (ERA5 de hoje, limitado pela ETo e pela ET real GRAVADAS, que nos pixels A vêm do BR-DWGD) e compara com o
#       gravado. Controle interno: a temperatura do solo (variável instantânea do mesmo ERA5) tem de sair 100% igual
#       em todos os dias, e os dias de controle de 1961 a 2013 também; senão a conta não é fiel e o Q1 não vale.
#   Q2  De quanto seria a correção dos pixels B? Janeiro e julho de cada ano, de 1961 a 2025: o gravado nos pixels B
#       x o BR-DWGD dos mesmos pixels e dias (mesma decodificação da V1.0). Chuva (total do mês), Tmax, Tmin, UR,
#       ETo, radiação e vento: diferença do mês e diferença diária média. Controle: nos pixels A, gravado = BR-DWGD.
#
# O QUE GRAVA: NADA no Earth Engine (trava de somente leitura). Só os resultados no Colab, que viram
#   validacao_K18_<data>.zip (baixado sozinho).
# ANTES DE RODAR: Ambiente de execução -> Reiniciar sessão. Fora das 15h07 e 23h07 (motor). Sem K16/K17 rodando.
# TEMPO: de 10 a 30 minutos.
# =========================================================================================
import os
import shutil
import time
import traceback
from datetime import datetime, timedelta, timezone

import pandas as pd

PROJETO = 'clima-492922'
ASSET_SAB = f'projects/{PROJETO}/assets/SAB_V1'
ASSET_MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
BRDWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
REGIAO_AMPLA = [-75.0, -35.0, -28.0, 6.5]
TOL_ABS, TOL_REL = 1e-3, 1e-4
MIN_IGUAIS = 0.99
DIAS_CONTROLE = ['1961-01-15', '1980-07-15', '2000-01-15', '2005-07-15', '2010-01-15', '2013-07-15']
DIAS_Q1 = DIAS_CONTROLE + [f'{a}-{m:02d}-15' for a in range(2014, 2026) for m in range(1, 13)]
MESES_Q2 = [(a, m) for a in range(1961, 2026) for m in (1, 7)]
MESES_CONTROLE_A = [(1961, 1), (1990, 7), (2020, 1)]
LOTE = 8
# Decodificação do BR-DWGD exatamente como na V1.0 (O0, processarDia_Definitivo)
DECODIFICA = {'pr': ('pr_mm', 0.00686666, 225.0), 'Tmax': ('tmax_C', 0.00106815, 15.0),
              'Tmin': ('tmin_C', 0.00106815, 15.0), 'RH': ('RH', 0.39370079, -0.393701),
              'ET': ('et_potencial', 0.05118110, -0.0511811), 'Rs': ('rs', 0.15708661, -0.057087),
              'u2': ('u2', 0.05905512, -0.059055)}
SOMA_NO_MES = {'pr_mm', 'et_potencial'}          # total do mês; as outras, média do mês
BANDAS_Q2 = [v[0] for v in DECODIFICA.values()]

AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'validacao_K18_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K18.txt')


def log(*p):
    t = ' '.join(str(x) for x in p)
    print(t, flush=True)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(t + '\n')


def salvar_csv(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=False, encoding='utf-8-sig')


# =========================================================================================
# FUNÇÕES PURAS (testadas offline em testes/teste_k18.py)
# =========================================================================================
def resumo_q1(df, min_iguais=MIN_IGUAIS):
    """df: uma linha por dia (data, frac_tsolo, frac_etr, frac_tr, dif_etr, absdif_etr, ...). Devolve
    (fiel: bool, texto, tabela por ano). fiel = tsolo >= min_iguais em TODOS os dias e ET real/transpiração
    >= min_iguais em todos os dias de controle (até 2013)."""
    df = df.sort_values('data').reset_index(drop=True)
    controle = df[df['data'] <= '2013-12-31']
    fiel = bool((df['frac_tsolo'] >= min_iguais).all() and (controle['frac_etr'] >= min_iguais).all()
                and (controle['frac_tr'] >= min_iguais).all()) and len(df) > 0
    df['mudou'] = (df['frac_etr'] < min_iguais) | (df['frac_tr'] < min_iguais)
    pos = df[df['data'] >= '2014-01-01']
    mud = pos[pos['mudou']]
    tab = (pos.assign(ano=pos['data'].str[:4])
           .groupby('ano').agg(dias=('data', 'size'), dias_mudados=('mudou', 'sum'),
                               frac_etr_min=('frac_etr', 'min'), absdif_etr_media=('absdif_etr', 'mean'),
                               dif_etr_media=('dif_etr', 'mean')).reset_index())
    if not fiel:
        texto = ('a conta da K18 NÃO reproduziu os dias de controle (ou a temperatura do solo): o resultado do Q1 '
                 'não é confiável; me envie o zip')
    elif mud.empty:
        texto = 'nenhum dia de 2014 a 2025 com ET real ou transpiração diferente do gravado'
    else:
        primeiro, ultimo_igual = mud['data'].iloc[0], pos[~pos['mudou'] & (pos['data'] < mud['data'].iloc[0])]
        antes = ultimo_igual['data'].iloc[-1] if len(ultimo_igual) else 'nenhum'
        depois_iguais = pos[(pos['data'] > primeiro) & ~pos['mudou']]
        texto = (f'primeiro dia mudado: {primeiro} (último igual antes dele: {antes}); {len(mud)} de {len(pos)} dias '
                 f'de 2014 a 2025 mudados' + (f'; {len(depois_iguais)} dia(s) iguais depois do primeiro mudado '
                                              f'(mudança não contínua): {list(depois_iguais["data"])[:6]}'
                                              if len(depois_iguais) else '; contínua até 2025'))
    return fiel, texto, tab


def resumo_q2(df):
    """df: uma linha por mês e classe (ano, mes, classe, n_dias, <b>_sab, <b>_br, <b>_abs_mes, <b>_abs_dia).
    Devolve (controle_ok, tabela por variável, texto). controle_ok: nos pixels A, |gravado - BR-DWGD| ~ 0."""
    a = df[df['classe'] == 'A']
    controle_ok = bool(len(a)) and all(float(a[f'{b}_abs_dia'].max()) <= 0.01 for b in BANDAS_Q2)
    b = df[df['classe'] == 'B']
    linhas = []
    for v in BANDAS_Q2:
        sab, br = b[f'{v}_sab'].astype(float), b[f'{v}_br'].astype(float)
        linhas.append({'variavel': v, 'agregado_mes': 'total' if v in SOMA_NO_MES else 'média',
                       'gravado_medio': sab.mean(), 'brdwgd_medio': br.mean(), 'dif_media': (sab - br).mean(),
                       'dif_pct': 100 * (sab - br).mean() / br.mean() if br.mean() else float('nan'),
                       'abs_mes_media': b[f'{v}_abs_mes'].astype(float).mean(),
                       'abs_dia_media': b[f'{v}_abs_dia'].astype(float).mean(),
                       'abs_dia_max_mes': b[f'{v}_abs_dia'].astype(float).max()})
    tab = pd.DataFrame(linhas)
    pr = tab.set_index('variavel').loc['pr_mm']
    texto = (f'{len(b)} meses nos pixels B; chuva do mês: gravado {pr.gravado_medio:.1f} x BR-DWGD {pr.brdwgd_medio:.1f} mm '
             f'({pr.dif_pct:+.1f}%), diferença média por pixel {pr.abs_mes_media:.1f} mm/mês e {pr.abs_dia_media:.2f} '
             f'mm/dia | controle nos pixels A: {"gravado = BR-DWGD" if controle_ok else "DIFERENTE (decodificação a conferir)"}')
    return controle_ok, tab, texto


# =========================================================================================
def principal():
    import ee

    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log('=' * 100)
    log(f'K18: AUDITORIA DO ERA5-LAND E DOS PIXELS B (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log('=' * 100)
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K18 SOMENTE LEITURA: tentativa de escrita bloqueada')

    for _n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
               'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable', 'exportVideo',
               'exportMap', 'startIngestion', 'startTableIngestion', 'cancelTask', 'cancelOperation'):
        if hasattr(ee.data, _n):
            setattr(ee.data, _n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa (criar, apagar, renomear, exportar e cancelar bloqueados).\n')

    REGIAO = ee.Geometry.Rectangle(REGIAO_AMPLA, None, False)
    CLASSE = ee.Image(ASSET_MASCARA).select('classe')
    COL = ee.ImageCollection(ASSET_SAB)
    BRCOL = ee.ImageCollection(BRDWGD)
    resultados = {}

    def gi(obj, rotulo, tentativas=3):
        for k in range(tentativas):
            try:
                return obj.getInfo()
            except Exception as e:
                if k == tentativas - 1 or 'memory' in str(e).lower() or 'timed out' in str(e).lower():
                    raise RuntimeError(f'{rotulo}: {str(e)[:300]}')
                time.sleep(20)

    def reduzir(img, rotulo):
        return img.reduceRegion(reducer=ee.Reducer.mean(), geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM,
                                maxPixels=1e10, tileScale=4)

    def em_lotes(itens, montar, rotulo):
        """montar(item) -> ee.Feature. Pede LOTE itens por vez; se um lote falhar, um por um."""
        linhas, sem = [], []
        for k in range(0, len(itens), LOTE):
            lote = itens[k:k + LOTE]
            try:
                linhas += [f['properties'] for f in gi(ee.FeatureCollection([montar(i) for i in lote]),
                                                       f'{rotulo} {lote[0]}', tentativas=1)['features']]
            except Exception:
                for i in lote:
                    try:
                        linhas += [f['properties'] for f in gi(ee.FeatureCollection([montar(i)]), f'{rotulo} {i}')['features']]
                    except Exception as e:
                        sem.append(i)
                        log(f'   {i}: não calculado ({str(e)[:150]})')
            log(f'   {rotulo}: {lote[0]} a {lote[-1]} ok')
        return pd.DataFrame(linhas), sem

    def decodificar(img):
        """BR-DWGD -> unidades do SAB, como a V1.0 (chuva >= 0, UR de 0 a 100)."""
        mask = img.select('pr').gt(-32768)
        bandas = []
        for b, (nome, esc, desl) in DECODIFICA.items():
            x = img.select(b).updateMask(mask).multiply(esc).add(desl)
            x = x.max(0) if b == 'pr' else (x.clamp(0, 100) if b == 'RH' else x)
            bandas.append(x.rename(nome))
        return ee.Image(ee.Image.cat(bandas).copyProperties(img, ['system:time_start']))

    # ---------------------------------------------------------------------------------- Q1
    def q1():
        log(f'\n{"-" * 100}\nQ1 A partir de quando o ERA5-Land mudou (ET real e transpiração nos pixels A)\n{"-" * 100}')
        a = CLASSE.eq(1)

        def igual(x, y):
            d = x.subtract(y).abs()
            return d.lte(TOL_ABS).Or(d.lte(y.abs().multiply(TOL_REL)))

        def montar(d):
            ini = ee.Date(d)
            s = ee.Image(f'{ASSET_SAB}/SAB_{d.replace("-", "_")}')
            era = ee.ImageCollection(ERA5).filterDate(ini, ini.advance(1, 'day')).first()
            # V1.0: et_real = min(ERA5 total_evaporation_sum, ETo); transpiração = min(bare_soil_sum, ET real)
            evap = era.select('total_evaporation_sum').multiply(-1000).max(0).resample('bilinear')
            tr_raw = era.select('evaporation_from_bare_soil_sum').multiply(-1000).max(0).resample('bilinear')
            etr = evap.min(s.select('et_potencial')).toFloat()
            tr = tr_raw.min(etr).toFloat()
            tsolo = era.select('soil_temperature_level_1').subtract(273.15).resample('bilinear').toFloat()
            img = ee.Image.cat([
                igual(s.select('tsolo_C'), tsolo).rename('frac_tsolo'),
                igual(s.select('et_real'), etr).rename('frac_etr'),
                igual(s.select('transpiracao_mm'), tr).rename('frac_tr'),
                etr.subtract(s.select('et_real')).rename('dif_etr'),
                etr.subtract(s.select('et_real')).abs().rename('absdif_etr'),
                tr.subtract(s.select('transpiracao_mm')).abs().rename('absdif_tr'),
            ]).updateMask(a).updateMask(s.select('et_real').mask())
            return ee.Feature(None, reduzir(img, d)).set('data', d)

        df, sem = em_lotes(DIAS_Q1, montar, 'Q1')
        salvar_csv(df, 'Q1_por_dia.csv')
        fiel, texto, tab = resumo_q1(df)
        salvar_csv(tab, 'Q1_por_ano.csv')
        log(tab.to_string(index=False))
        resultados['Q1'] = ('OK' if fiel else 'FALHA', texto + (f' | não calculados: {sem}' if sem else ''))
        log(f'{"ℹ️" if fiel else "❌"} Q1: {resultados["Q1"][1]}')

    # ---------------------------------------------------------------------------------- Q2
    def q2():
        log(f'\n{"-" * 100}\nQ2 Correção dos pixels B: gravado x BR-DWGD (janeiro e julho de 1961 a 2025)\n{"-" * 100}')
        ult = gi(BRCOL.aggregate_max('system:time_start'), 'fim do BR-DWGD')
        log(f'   último dia do BR-DWGD: {datetime.fromtimestamp(ult / 1000, tz=timezone.utc):%Y-%m-%d}')
        itens = [(a, m, 'B') for a, m in MESES_Q2] + [(a, m, 'A') for a, m in MESES_CONTROLE_A]

        def montar(item):
            ano, mes, cl = item
            ini = ee.Date.fromYMD(ano, mes, 1)
            fim = ini.advance(1, 'month')
            sab = COL.filterDate(ini, fim).select(BANDAS_Q2)
            br = BRCOL.filterDate(ini, fim).map(decodificar)
            par = ee.Join.inner().apply(sab, br, ee.Filter.maxDifference(
                difference=12 * 3600 * 1000, leftField='system:time_start', rightField='system:time_start'))
            dif_dia = ee.ImageCollection(par.map(
                lambda f: ee.Image(f.get('primary')).subtract(ee.Image(f.get('secondary'))).abs()))
            agrega = lambda c: ee.Image.cat([c.select(b).sum() if b in SOMA_NO_MES else c.select(b).mean()
                                             for b in BANDAS_Q2])
            s_m, b_m = agrega(sab), agrega(br)
            img = ee.Image.cat([s_m.rename([f'{b}_sab' for b in BANDAS_Q2]),
                                b_m.rename([f'{b}_br' for b in BANDAS_Q2]),
                                s_m.subtract(b_m).abs().rename([f'{b}_abs_mes' for b in BANDAS_Q2]),
                                dif_dia.mean().rename([f'{b}_abs_dia' for b in BANDAS_Q2])])
            img = img.updateMask(CLASSE.eq(2 if cl == 'B' else 1))
            return ee.Feature(None, reduzir(img, f'{ano}-{mes}')).set(
                {'ano': ano, 'mes': mes, 'classe': cl, 'n_dias': par.size(), 'n_dias_sab': sab.size(),
                 'n_dias_br': br.size()})

        df, sem = em_lotes(itens, montar, 'Q2')
        salvar_csv(df, 'Q2_por_mes.csv')
        ok, tab, texto = resumo_q2(df)
        salvar_csv(tab, 'Q2_por_variavel.csv')
        log(tab.to_string(index=False))
        b = df[df['classe'] == 'B'].copy()
        if len(b):
            b['decada'] = (b['ano'].astype(int) // 10 * 10).astype(str) + 's'
            dec = b.groupby('decada').agg(meses=('ano', 'size'), pr_gravado=('pr_mm_sab', 'mean'),
                                          pr_brdwgd=('pr_mm_br', 'mean'), pr_abs_mes=('pr_mm_abs_mes', 'mean'),
                                          tmax_abs_dia=('tmax_C_abs_dia', 'mean')).reset_index()
            salvar_csv(dec, 'Q2_pixels_B_por_decada.csv')
            log(dec.to_string(index=False))
            incompletos = b[b['n_dias'].astype(int) < b['n_dias_sab'].astype(int)]
            if len(incompletos):
                texto += f' | {len(incompletos)} mês(es) sem BR-DWGD em algum dia: {incompletos[["ano", "mes"]].values.tolist()[:5]}'
        resultados['Q2'] = ('OK' if ok else 'FALHA', texto + (f' | não calculados: {sem}' if sem else ''))
        log(f'{"ℹ️" if ok else "❌"} Q2: {resultados["Q2"][1]}')

    for fn in (q1, q2):
        t = time.time()
        try:
            fn()
        except Exception as e:
            nome = fn.__name__.upper()
            resultados[nome] = ('NÃO EXECUTADO', f'{type(e).__name__}: {str(e)[:400]}')
            log(f'⏭️ {nome} NÃO EXECUTADO: {resultados[nome][1]}')
            log(traceback.format_exc()[-1500:])
        log(f'   ({(time.time() - t) / 60:.1f} min)')

    salvar_csv(pd.DataFrame([{'parte': k, 'status': v[0], 'detalhe': v[1]} for k, v in resultados.items()]),
               'K18_RESUMO.csv')
    log('\n' + '=' * 100 + '\nRESULTADO K18 (só medidas; nada é aprovado ou reprovado aqui)\n' + '=' * 100)
    for k, (st, det) in resultados.items():
        log(f'   {k} {st}: {det}')
    log(f'\nTempo: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine (trava de somente leitura).')
    z = shutil.make_archive(PASTA, 'zip', PASTA)
    log(f'📦 {z}  <- me envie este zip')
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        pass


if __name__ == '__main__':
    principal()
