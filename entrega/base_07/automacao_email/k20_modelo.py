# >>> K20 v2: VALIDAÇÃO DA CORREÇÃO DE LEITURA DOS PIXELS B E DA RADIAÇÃO (03/11/2026). SOMENTE LEITURA. Cole inteiro. <<<
# =========================================================================================
# v2 (03/11/2026, 22h30): na v1 o sampleRegions descartava o ponto inteiro quando faltava o BR-DWGD (pixels C, que não
#   têm BR-DWGD, e dias de 2026, que ainda não têm): V3 e V5 ficaram com 0 pixel-dias. Agora todas as bandas vão com
#   o marcador AUSENTE no lugar do vazio, que vira vazio de novo no Colab (função limpar_ausentes).
# POR QUE EXISTE
#   O painel 2026.11.1 e a rotina do e-mail sab_pedido.py 2026.11.03 corrigem NA LEITURA (o banco não muda):
#     - pixels B (lagoas e estuários), dias de 1961 a 2025: chuva, Tmax, Tmin, UR, VPD, ETo, radiação e vento do BR-DWGD;
#     - pixels C, dias de 1961 a 2025: radiação limitada à de céu claro, Rso = (0,75 + 2e-5 z) Ra (FAO-56).
#   Antes de trocar o painel e a rotina, a K20 roda a PRÓPRIA rotina 2026.11.03 (embutida abaixo, sem mudança) no
#   Earth Engine de verdade e prova, em pixels sorteados de cada classe e em 14 dias de 1961 a 2026:
#     V1  pixels B: as 8 bandas do núcleo = BR-DWGD do dia (decodificado direto, como a V1.0 faz nos pixels A);
#     V2  pixels A: as 16 bandas iguais às da leitura sem a correção (nada muda fora de B e C);
#     V3  pixels C: radiação <= céu claro; as outras 15 bandas iguais às da leitura sem a correção;
#     V4  depois da correção, ET real <= ETo e transpiração <= ET real nos pixels B;
#     V5  dias de 2026: nada muda (sem BR-DWGD; a correção é só do histórico);
#     V6  o polígono do caso A6 da K16 (Lagoa dos Patos) tem pixels B (senão a K16 não testaria a correção).
#   E mede, só para informação, quanto a chuva e a ETo dos pixels B mudam.
#
# REGRA (fixada antes de rodar): APROVADA com V1 a V6 ✅. Só então: trocar o sab_pedido.py, o painel no app teste1,
#   rodar a K16 v4 e, aprovada, o app oficial (passo a passo no guia, "Etapa 1").
# O QUE GRAVA: NADA no Earth Engine (trava de somente leitura). Só os resultados no Colab (validacao_K20_<data>.zip).
# ANTES DE RODAR: Ambiente de execução -> Reiniciar sessão. Fora das janelas do motor (14h50-16h00 e 22h50-24h00).
# TEMPO: de 10 a 25 minutos.
# =========================================================================================
import hashlib
import os
import shutil
import time
import traceback
import types
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

PROJETO = 'clima-492922'
ASSET_SAB = f'projects/{PROJETO}/assets/SAB_V1'
ASSET_MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
REGIAO_AMPLA = [-75.0, -35.0, -28.0, 6.5]
ORDEM = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2', 'tsolo_C', 'tfolha_C',
         'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm', 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
NUCLEO = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'rs', 'u2', 'vpd']
CLASSES = {1: 'A', 2: 'B', 3: 'C'}
PONTOS = {1: 100, 2: 150, 3: 100}             # C entra inteira (48 pixels)
SEMENTE = 17
DIAS = ['1961-01-15', '1966-07-15', '1971-01-15', '1976-07-15', '1981-01-15', '1986-07-15', '1991-01-15', '1996-07-15',
        '2001-01-15', '2010-07-15', '2018-01-15', '2025-12-15', '2026-01-15', '2026-07-15']
FIM_HISTORICO = '2025-12-31'
POLIGONO_A6 = [[-51.4, -30.9], [-51.1, -30.9], [-51.1, -31.2], [-51.4, -31.2], [-51.4, -30.9]]   # lon, lat
TOL_ABS, TOL_REL, MIN_IGUAIS = 1e-3, 1e-4, 0.99
LOTE = 120
AUSENTE = -99999.0          # v2: marcador de valor vazio (o sampleRegions descarta o ponto com qualquer banda vazia)

AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'validacao_K20_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K20.txt')
ACHADOS = []

# ------------------------------------------------------------------ a rotina do e-mail 2026.11.03, sem mudança
ROTINA_SRC = r'''<<ROTINA>>'''
SHA_ROTINA = hashlib.sha256(ROTINA_SRC.encode('utf-8')).hexdigest()


def log(*p):
    t = ' '.join(str(x) for x in p)
    print(t, flush=True)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(t + '\n')


def achado(parte, status, titulo, detalhe):
    icone = {'OK': '✅', 'FALHA': '❌', 'INFO': 'ℹ️', 'NÃO EXECUTADO': '⏭️'}[status]
    ACHADOS.append({'parte': parte, 'status': status, 'titulo': titulo, 'detalhe': detalhe})
    log(f'{icone} {parte} {status}: {titulo}\n   {detalhe}')


def salvar_csv(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=False, encoding='utf-8-sig')


# =========================================================================================
# FUNÇÕES PURAS (testadas offline em testes/teste_k20.py)
# =========================================================================================
def iguais(a, b):
    a, b = pd.to_numeric(a, errors='coerce'), pd.to_numeric(b, errors='coerce')
    d = (a - b).abs()
    return (a.isna() & b.isna()) | (d <= TOL_ABS) | (d <= TOL_REL * b.abs())


def limpar_ausentes(df):
    """v2: o marcador AUSENTE volta a ser vazio (NaN) em todas as bandas."""
    df = df.copy()
    for c in df.columns:
        if c.startswith(('c_', 's_', 'b_')) or c == 'rso':
            v = pd.to_numeric(df[c], errors='coerce')
            df[c] = v.where(v > AUSENTE / 2)
    return df


def avaliar(df):
    """df: uma linha por pixel e dia com classe, data, c_<banda> (com a correção), s_<banda> (sem a correção),
    b_<banda> (BR-DWGD do dia, núcleo) e rso. Devolve {V1..V5: (status, detalhe)} e a tabela de medidas."""
    hist = df[df['data'] <= FIM_HISTORICO]
    novo = df[df['data'] > FIM_HISTORICO]
    B, A, C = hist[hist['classe'] == 2], hist[hist['classe'] == 1], hist[hist['classe'] == 3]
    res = {}
    # V1: B = BR-DWGD onde o BR-DWGD tem valor
    ruins = []
    for b in NUCLEO:
        sub = B[B[f'b_{b}'].notna()]
        f = float(iguais(sub[f'c_{b}'], sub[f'b_{b}']).mean()) if len(sub) else 0.0
        if f < MIN_IGUAIS:
            ruins.append(f'{b} {100 * f:.1f}%')
    nb = int(B[B['b_pr_mm'].notna()].shape[0])
    res['V1'] = ('FALHA' if ruins or nb == 0 else 'OK',
                 f'{nb} pixel-dias B com BR-DWGD; núcleo = BR-DWGD' + (f' | diferentes: {ruins}' if ruins else
                                                                      ' nas 8 bandas' if nb else ' | nenhum pixel B'))
    # V2: A intocado
    difA = [b for b in ORDEM if len(A) and iguais(A[f'c_{b}'], A[f's_{b}']).mean() < 1.0]
    res['V2'] = ('FALHA' if difA or not len(A) else 'OK',
                 f'{len(A)} pixel-dias A; 16 bandas iguais à leitura sem a correção' + (f' | mudaram: {difA}' if difA else ''))
    # V3: C com radiação <= Rso e o resto intocado
    acima = int((C['c_rs'] > C['rso'] * (1 + 1e-4) + 1e-3).sum()) if len(C) else 0
    lim = int((~iguais(C['c_rs'], C['s_rs'])).sum()) if len(C) else 0
    difC = [b for b in ORDEM if b != 'rs' and len(C) and iguais(C[f'c_{b}'], C[f's_{b}']).mean() < 1.0]
    res['V3'] = ('FALHA' if acima or difC or not len(C) else 'OK',
                 f'{len(C)} pixel-dias C; {lim} com a radiação limitada ao céu claro; {acima} acima do céu claro depois'
                 + (f' | outras bandas mudaram: {difC}' if difC else ''))
    # V4: grampo nos B
    etr = int((B['c_et_real'] > B['c_et_potencial'] + 1e-3).sum())
    tr = int((B['c_transpiracao_mm'] > B['c_et_real'] + 1e-3).sum())
    res['V4'] = ('FALHA' if etr or tr else 'OK', f'pixels B: ET real > ETo em {etr}; transpiração > ET real em {tr}')
    # V5: 2026 intocado
    dif26 = [b for b in ORDEM if len(novo) and iguais(novo[f'c_{b}'], novo[f's_{b}']).mean() < 1.0]
    res['V5'] = ('FALHA' if dif26 or not len(novo) else 'OK',
                 f'{len(novo)} pixel-dias de 2026; nada muda' + (f' | mudaram: {dif26}' if dif26 else ''))
    # medidas (informação)
    med = []
    for b in NUCLEO:
        if len(B):
            d = (B[f'c_{b}'] - B[f's_{b}']).abs()
            med.append({'banda': b, 'pixel_dias_B': len(B), 'mudanca_media': float(d.mean()),
                        'mudanca_p95': float(d.quantile(0.95)), 'antes_media': float(B[f's_{b}'].mean()),
                        'depois_media': float(B[f'c_{b}'].mean())})
    return res, pd.DataFrame(med)


def veredito(achados):
    st = {a['parte']: a['status'] for a in achados}
    falta = [p for p in ('V1', 'V2', 'V3', 'V4', 'V5', 'V6') if st.get(p) != 'OK']
    return not falta, falta


# =========================================================================================
def principal():
    import ee

    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log('=' * 100)
    log(f'K20 v2: VALIDAÇÃO DA CORREÇÃO DE LEITURA DOS PIXELS B E DA RADIAÇÃO (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log(f'   rotina sab_pedido.py embutida: SHA-256 {SHA_ROTINA}')
    log('=' * 100)
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K20 SOMENTE LEITURA: tentativa de escrita bloqueada')

    for _n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
               'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable', 'exportVideo',
               'exportMap', 'startIngestion', 'startTableIngestion', 'cancelTask', 'cancelOperation'):
        if hasattr(ee.data, _n):
            setattr(ee.data, _n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa (criar, apagar, renomear, exportar e cancelar bloqueados).\n')

    sp = types.ModuleType('sab_pedido')
    exec(compile(ROTINA_SRC, 'sab_pedido.py', 'exec'), sp.__dict__)
    sp._ee = lambda: ee
    log(f'   rotina {sp.VERSAO_ROTINA} carregada (corrigir_pixels_b, area_tem_pixels_bc, colecao)')
    PROJ = ee.Projection(CRS, TRANSFORM)
    REGIAO = ee.Geometry.Rectangle(REGIAO_AMPLA, None, False)
    CLASSE = ee.Image(ASSET_MASCARA).select('classe').unmask(0).toInt().rename('classe')

    def gi(obj, rotulo, tentativas=4):
        for k in range(tentativas):
            try:
                return obj.getInfo()
            except Exception as e:
                msg = str(e)
                if k == tentativas - 1:
                    raise RuntimeError(f'{rotulo}: {msg[:300]}')
                time.sleep(60 * (k + 1) if ('429' in msg or 'too many' in msg.lower()) else 15)

    # V6: o polígono do caso A6 tem pixels B?
    try:
        pol = ee.Geometry.Polygon([POLIGONO_A6], None, False)
        h = gi(CLASSE.reduceRegion(reducer=ee.Reducer.frequencyHistogram(), geometry=pol, crs=CRS,
                                   crsTransform=TRANSFORM, maxPixels=1e8).get('classe'), 'polígono A6')
        cont = {CLASSES.get(int(float(k)), 'outra'): int(v) for k, v in (h or {}).items()}
        achado('V6', 'OK' if cont.get('B', 0) > 0 else 'FALHA', 'O polígono do caso A6 da K16 tem pixels B',
               f'classes no polígono (Lagoa dos Patos): {cont}')
    except Exception as e:
        achado('V6', 'NÃO EXECUTADO', 'O polígono do caso A6 da K16 tem pixels B', f'{type(e).__name__}: {str(e)[:300]}')

    # pixels sorteados por classe
    cls = sorted(PONTOS)
    sorteio = (ee.Image.pixelLonLat().addBands(CLASSE)
               .stratifiedSample(numPoints=0, classBand='classe', region=REGIAO, projection=PROJ, seed=SEMENTE,
                                 classValues=cls, classPoints=[PONTOS[c] for c in cls], geometries=True, tileScale=4))
    pts = [{'pid': k, 'classe': int(f['properties']['classe']), 'lon': f['geometry']['coordinates'][0],
            'lat': f['geometry']['coordinates'][1]} for k, f in enumerate(gi(sorteio, 'pontos')['features'])]
    log('   pixels: ' + ', '.join(f'{CLASSES[c]} {sum(p["classe"] == c for p in pts)}' for c in cls))
    salvar_csv(pd.DataFrame(pts), 'pontos.csv')
    geom_todos = ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in pts])

    original = sp.area_tem_pixels_bc
    linhas, sem_dia = [], []
    for d in DIAS:
        try:
            ini = d
            fim = (pd.Timestamp(d) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            com = ee.Image(sp.colecao(geom_todos, ini, fim).first())             # o que a rotina entrega
            sp.area_tem_pixels_bc = lambda g: ee.Number(0)                       # a mesma leitura, sem a correção
            sem = ee.Image(sp.colecao(geom_todos, ini, fim).first())
            sp.area_tem_pixels_bc = original
            br = sp._brdwgd_do_dia(ee.Date(d))
            rso = sp._radiacao_ceu_claro(ee.Date(d))
            img = ee.Image.cat([com.select(ORDEM).rename([f'c_{b}' for b in ORDEM]),
                                sem.select(ORDEM).rename([f's_{b}' for b in ORDEM]),
                                br.select(NUCLEO).rename([f'b_{b}' for b in NUCLEO]), rso]).unmask(AUSENTE)
            for k in range(0, len(pts), LOTE):
                sub = pts[k:k + LOTE]
                fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]),
                                                      {'pid': p['pid'], 'classe': p['classe']}) for p in sub])
                r = gi(img.sampleRegions(collection=fc, properties=['pid', 'classe'], projection=PROJ, tileScale=8,
                                         geometries=False), f'K20 {d}')
                for f in r['features']:
                    linhas.append(dict(f['properties'], data=d))
            log(f'   {d}: ok')
        except Exception as e:
            sp.area_tem_pixels_bc = original
            sem_dia.append(d)
            log(f'   {d}: não calculado ({str(e)[:200]})')
    df = limpar_ausentes(pd.DataFrame(linhas))
    for pref, bs in (('c_', ORDEM), ('s_', ORDEM), ('b_', NUCLEO)):
        for b in bs:
            if f'{pref}{b}' not in df:
                df[f'{pref}{b}'] = np.nan
    if 'rso' not in df:
        df['rso'] = np.nan
    salvar_csv(df, 'K20_amostra.csv')
    if len(df):
        res, med = avaliar(df)
        salvar_csv(med, 'K20_mudanca_pixels_B.csv')
        nomes = {'V1': 'Pixels B: núcleo = BR-DWGD', 'V2': 'Pixels A: nada muda',
                 'V3': 'Pixels C: radiação <= céu claro; o resto não muda', 'V4': 'Pixels B: ET real <= ETo',
                 'V5': 'Dias de 2026: nada muda'}
        for v in ('V1', 'V2', 'V3', 'V4', 'V5'):
            st, det = res[v]
            achado(v, st, nomes[v], det + (f' | dias não calculados: {sem_dia}' if sem_dia else ''))
        if len(med):
            log(med.round(3).to_string(index=False))
            m = med.set_index('banda')
            achado('INFO', 'INFO', 'Quanto os pixels B mudam (dias de 1961 a 2025)',
                   f'chuva: {m.loc["pr_mm", "mudanca_media"]:.2f} mm/dia em média (p95 {m.loc["pr_mm", "mudanca_p95"]:.1f}); '
                   f'ETo: {m.loc["et_potencial", "mudanca_media"]:.2f} mm/dia; Tmax: {m.loc["tmax_C", "mudanca_media"]:.2f} °C')
    else:
        for v in ('V1', 'V2', 'V3', 'V4', 'V5'):
            achado(v, 'NÃO EXECUTADO', v, f'nenhum dia calculado: {sem_dia}')

    salvar_csv(pd.DataFrame(ACHADOS), 'K20_RESUMO.csv')
    ok, falta = veredito(ACHADOS)
    log('\n' + '=' * 100 + '\nRESULTADO K20\n' + '=' * 100)
    for a in ACHADOS:
        log(f"   {a['parte']:4} {a['status']:13} {a['titulo']}")
    log('\n   ✅ CORREÇÃO APROVADA: pode trocar o sab_pedido.py e o painel (guia, "Etapa 1").' if ok else
        f'\n   ❌ CORREÇÃO NÃO APROVADA ({", ".join(falta)}): NÃO troque nada; me envie o zip.')
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
