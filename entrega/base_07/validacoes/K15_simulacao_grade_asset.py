# >>> SIMULAÇÃO K15 (29/10/2026): por que a exportação é lenta? Grade em asset x grade montada; formatação. Cole inteiro. <<<
# =========================================================================================
# POR QUE EXISTE
#   Na K14 (29/10), o Paraná 2025 levou 102 minutos para exportar usando só 82 segundos de processamento (EECU):
#   o Earth Engine passou quase todo o tempo esperando uma etapa feita em série, não calculando. O suspeito é a
#   GRADE DE PONTOS, que o painel monta a cada pedido (amostra os pixels, cruza com o polígono, ordena e numera
#   com toList + List.sequence, o que costuma rodar numa máquina só). O segundo suspeito é a FORMATAÇÃO de cada
#   número da linha como texto ("18.40").
#
# O QUE FAZ
#   1. Monta a grade do Paraná exatamente como o painel (1.889 pontos) e grava UMA VEZ num asset de TESTE:
#      projects/clima-492922/assets/TESTE_K15_grade_PR (só a grade; o asset é APAGADO no fim).
#   2. Exporta para o Drive (pasta K15_teste) o MESMO pedido, Paraná de 01/01 a 31/03/2025 (170.010 linhas,
#      CSV diário com as 33 colunas do painel), em 4 versões, 2 x 2:
#        V0 grade montada (como o painel hoje) + números formatados ("18.40", como o painel hoje)
#        V1 grade do asset                     + números formatados
#        V2 grade do asset                     + números sem formatação (número cru)
#        V3 grade montada                      + números sem formatação
#      V0 e V1 vão 2 vezes. Ordem de envio: V0, V1, V3, V2, V0, V1. O Earth Engine roda 2 tarefas por vez, na
#      ordem de envio, então cada par roda junto, nas mesmas condições: (V0, V1), (V3, V2), (V0, V1).
#   3. Mede o link na hora (getDownloadURL, como o painel) do mesmo pedido com a grade montada e com a do asset,
#      alternados, 2 vezes cada.
#   4. Confere: cada CSV completo (linhas, sem repetição, colunas do painel); V1 IDÊNTICO a V0 célula a célula;
#      V2 e V3 iguais a V0 a menos do arredondamento.
#
# REGRA DE DECISÃO (fixada antes de rodar)
#   G  Grade em asset: adotar se V1 for IDÊNTICO a V0 e levar no máximo 70% do tempo de processamento de V0 nos
#      DOIS pares (ganho de 30% ou mais nos dois).
#   F  Formatação: trocar para número cru só se V2 levar no máximo 75% de V1 E V3 no máximo 75% de V0 (ganho de
#      25% ou mais com as duas grades). Mesmo assim, a troca muda a aparência do CSV e depende da sua aprovação.
#   L  Link na hora: informa a razão de tempo grade do asset / grade montada (mesma regra de 30%).
#
# O QUE GRAVA: 1 asset de teste pequeno (TESTE_K15_grade_PR, apagado no fim; APAGAR_ASSET_NO_FIM = True) e
#   CSV na pasta K15_teste do seu Drive. NADA no SAB_V1 nem em outro asset do sistema.
# ANTES DE RODAR: Ambiente de execução -> Reiniciar sessão (este script grava um asset). Não rode junto com o 05b.
# TEMPO: de 1 a 2 horas. Se a célula parar, rode de novo: retoma pelo progresso no Drive, sem reenviar.
# NO FIM: o Colab baixa simulacao_K15_<data>.zip (LOG_K15.txt e K15_resultados.csv). Me envie o zip.
# =========================================================================================
import glob
import io
import json
import os
import shutil
import time
from datetime import datetime, timedelta, timezone

import ee
import pandas as pd
import requests

# ------------------------------------------------------------------ parâmetros (não precisa mudar)
PROJETO = 'clima-492922'
SAB = f'projects/{PROJETO}/assets/SAB_V1'
MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
SOLO = f'projects/{PROJETO}/assets/SICSB_SOLO_2015_2025'
ASSET_GRADE = f'projects/{PROJETO}/assets/TESTE_K15_grade_PR'
APAGAR_ASSET_NO_FIM = True
PASTA_DRIVE = 'K15_teste'
PERIODO = ('2025-01-01', '2025-04-01')    # fim exclusivo: 1º trimestre de 2025 (só histórico)
ESCALA_AREA = 11132
LIMITE_PONTOS_GRADE = 25000
INTERVALO_S = 30
ESPERA_MAX_H = 4
ESPERA_ARQUIVO_S = 900
TIMEOUT_LINK_S = 1200
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
PARANA = ['Parana', 'Paraná']
# versão: (grade, formato); ordem de envio = ordem da lista
VERSOES = [('V0a', 'montada', 'ponto'), ('V1a', 'asset', 'ponto'), ('V3', 'montada', 'cru'),
           ('V2', 'asset', 'cru'), ('V0b', 'montada', 'ponto'), ('V1b', 'asset', 'ponto')]

BANDAS_SAB = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2', 'tsolo_C',
              'tfolha_C', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm',
              'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
BANDAS_ANTIGAS = ['precipitation_mm', 'temp_max_C', 'temp_min_C', 'relative_humidity_pct', 'et_potential_mm',
                  'et_actual_mm', 'vpd_kpa', 'solar_radiation_mj_m2', 'wind_speed_m_s', 'soil_temperature_C',
                  'skin_temperature_C', 'transpiration_mm', 'surface_runoff_mm', 'subsurface_runoff_mm',
                  'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
# Colunas do painel 2026.10.4 (getColunasClimaDiaria e getColunasClimaMensal), na mesma ordem
COLUNAS_BASE = ['Tipo_Dado', 'Versao_Algoritmo', 'Data_Completa', 'Ano', 'Mes', 'Dia', 'N_Ponto', 'Latitude',
                'Longitude', 'Estado', 'Municipio', 'Precipitacao_mm', 'Chuva_Efetiva_mm', 'Runoff_Superficial_mm',
                'Runoff_Subsuperficial_mm', 'Temperatura_Maxima_C', 'Temperatura_Minima_C', 'Amplitude_Termica_C',
                'Temperatura_Solo_C', 'Temperatura_Folha_C', 'Umidade_Relativa_Porc', 'Vento_ms',
                'Radiacao_Solar_MJ_m2', 'Evapotranspiracao_Potencial_mm', 'Evapotranspiracao_Real_mm',
                'Transpiracao_Planta_mm', 'Deficit_Hidrico_mm', 'Deficit_Pressao_Vapor_kPa',
                'Umidade_Volumetrica_Solo_0_5cm_m3_m3', 'Umidade_Volumetrica_Solo_0_100cm_m3_m3']
EXTRAS_DIARIA = ['Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo']
EXTRAS_MENSAL = ['N_Dias', 'Dias_no_Mes', 'Mes_Completo']
COLUNAS_DIARIA = COLUNAS_BASE + EXTRAS_DIARIA
COLUNAS_MENSAL = COLUNAS_BASE + EXTRAS_MENSAL
# coluna do CSV -> (banda, casas decimais), como formatarExportacaoClima do painel
NUMERICAS = [('Latitude', 'Latitude', 5), ('Longitude', 'Longitude', 5), ('Precipitacao_mm', 'pr_mm', 2),
             ('Chuva_Efetiva_mm', 'chuva_efetiva', 2), ('Runoff_Superficial_mm', 'runoff_sup_mm', 2),
             ('Runoff_Subsuperficial_mm', 'runoff_sub_mm', 2), ('Temperatura_Maxima_C', 'tmax_C', 2),
             ('Temperatura_Minima_C', 'tmin_C', 2), ('Amplitude_Termica_C', 'amplitude_diaria', 2),
             ('Temperatura_Solo_C', 'tsolo_C', 2), ('Temperatura_Folha_C', 'tfolha_C', 2),
             ('Umidade_Relativa_Porc', 'RH', 2), ('Vento_ms', 'u2', 2), ('Radiacao_Solar_MJ_m2', 'rs', 2),
             ('Evapotranspiracao_Potencial_mm', 'et_potencial', 2), ('Evapotranspiracao_Real_mm', 'et_real', 2),
             ('Transpiracao_Planta_mm', 'transpiracao_mm', 2), ('Deficit_Hidrico_mm', 'deficit_diario', 2),
             ('Deficit_Pressao_Vapor_kPa', 'vpd', 2),
             ('Umidade_Volumetrica_Solo_0_5cm_m3_m3', 'soil_moisture_0_5cm_m3_m3', 3),
             ('Umidade_Volumetrica_Solo_0_100cm_m3_m3', 'soil_moisture_0_100cm_m3_m3', 3)]


AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'simulacao_K15_{AGORA:%Y%m%d_%H%M}')
LOG = os.path.join(PASTA, 'LOG_K15.txt')
DRIVE = '/content/drive/MyDrive'


def log(*p):
    t = ' '.join(str(x) for x in p)
    print(t, flush=True)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(t + '\n')


def tabela(df, titulo):
    log(f'\n   {titulo}')
    with pd.option_context('display.width', 250, 'display.max_columns', 40, 'display.max_rows', 400):
        for linha in df.to_string().splitlines():
            log('   ' + linha)


# =========================================================================================
# FUNÇÕES PURAS (sem Earth Engine; testadas offline em testes/teste_k15.py)
# =========================================================================================
TERMINAIS = ('COMPLETED', 'FAILED', 'CANCELLED')
_DE_OPERACAO = {'SUCCEEDED': 'COMPLETED', 'FAILED': 'FAILED', 'CANCELLED': 'CANCELLED', 'CANCELLING': 'CANCEL_REQUESTED',
                'RUNNING': 'RUNNING', 'PENDING': 'READY'}


def _ms_de_iso(txt):
    if not txt:
        return None
    return int(datetime.fromisoformat(txt.replace('Z', '+00:00')).timestamp() * 1000)


def normalizar_status(st):
    """Aceita o formato de ee.data.getTaskStatus (state, *_timestamp_ms) ou o de uma operação
    (metadata.state, createTime...). Devolve um dicionário no formato do getTaskStatus."""
    if 'metadata' in st:
        md = st['metadata']
        return {'state': _DE_OPERACAO.get(md.get('state', ''), md.get('state', '')),
                'creation_timestamp_ms': _ms_de_iso(md.get('createTime')),
                'start_timestamp_ms': _ms_de_iso(md.get('startTime')),
                'update_timestamp_ms': _ms_de_iso(md.get('updateTime') or md.get('endTime')),
                'batch_eecu_usage_seconds': md.get('batchEecuUsageSeconds'),
                'error_message': (st.get('error') or {}).get('message', '')}
    return st


def resumo_tarefa(st):
    """Tempos em minutos: fila (criação -> início), processamento (início -> fim) e total; EECU em horas."""
    st = normalizar_status(st)
    c, s, u = st.get('creation_timestamp_ms'), st.get('start_timestamp_ms'), st.get('update_timestamp_ms')
    terminal = st.get('state') in TERMINAIS

    def minutos(a, b):
        return round((b - a) / 60000, 1) if a is not None and b is not None and b >= a else None
    eecu = st.get('batch_eecu_usage_seconds')
    return {'estado': st.get('state', ''),
            'fila_min': minutos(c, s),
            'processamento_min': minutos(s, u) if terminal else None,
            'total_min': minutos(c, u) if terminal else None,
            'EECU_h': round(float(eecu) / 3600, 3) if eecu not in (None, '') else None,
            'erro': st.get('error_message', '') or ''}


def conferir_csv(cabecalho, pares, colunas, esperado):
    """cabecalho: lista de colunas lidas; pares: DataFrame com N_Ponto e Data_Completa (todas as partes)."""
    rep = int(pares.duplicated().sum())
    ok = cabecalho == colunas and len(pares) == esperado and rep == 0
    det = '' if ok else (f'linhas {len(pares):,} de {esperado:,}; repetidos {rep}; '
                         f'colunas {"ok" if cabecalho == colunas else "fora de ordem"}')
    return ok, det


def comparar_identicos(df_a, df_b):
    """True se os dois CSV têm as mesmas colunas e as mesmas células (como texto), na ordem de ponto e dia."""
    if list(df_a.columns) != list(df_b.columns) or len(df_a) != len(df_b):
        return False
    chave = ['N_Ponto', 'Data_Completa']
    a = df_a.fillna('').astype(str).sort_values(chave).reset_index(drop=True)
    b = df_b.fillna('').astype(str).sort_values(chave).reset_index(drop=True)
    return a.equals(b)


CASAS = {col: casas for col, _, casas in NUMERICAS}


def comparar_arredondado(df_ponto, df_cru):
    """True se os dois CSV têm as mesmas linhas e colunas, os textos iguais e cada número do cru, arredondado nas
    casas do painel, igual ao formatado (diferença de no máximo meia unidade da última casa)."""
    if list(df_ponto.columns) != list(df_cru.columns) or len(df_ponto) != len(df_cru):
        return False
    chave = ['N_Ponto', 'Data_Completa']
    a = df_ponto.fillna('').astype(str).sort_values(chave).reset_index(drop=True)
    b = df_cru.fillna('').astype(str).sort_values(chave).reset_index(drop=True)
    for col in a.columns:
        if col in CASAS:
            va = pd.to_numeric(a[col].replace('', None), errors='coerce')
            vb = pd.to_numeric(b[col].replace('', None), errors='coerce')
            if not (va.isna() == vb.isna()).all():
                return False
            dif = (va - vb).abs().max()
            if pd.notna(dif) and float(dif) > 0.5 * 10 ** -CASAS[col] + 1e-6:
                return False
        elif not a[col].equals(b[col]):
            return False
    return True


def decidir_k15(proc, identico_v1, links, ganho_grade=0.30, ganho_formato=0.25):
    """proc: minutos de processamento por versão ('V0a', 'V1a', 'V0b', 'V1b', 'V2', 'V3'; None = falhou).
    links: {'montada': [s, ...], 'asset': [s, ...]} (None = falhou). Regras G, F e L do cabeçalho."""
    def ok(*vs):
        return all(proc.get(v) is not None for v in vs)

    g_pares = []
    for a, b in (('V0a', 'V1a'), ('V0b', 'V1b')):
        if ok(a, b) and proc[a] > 0:
            g_pares.append(proc[b] / proc[a])
    grade = bool(identico_v1) and len(g_pares) == 2 and all(r <= 1 - ganho_grade for r in g_pares)

    def med(*vs):
        x = [proc[v] for v in vs if proc.get(v) is not None]
        return sum(x) / len(x) if x else None
    v0, v1 = med('V0a', 'V0b'), med('V1a', 'V1b')
    f_asset = proc['V2'] / v1 if ok('V2') and v1 else None
    f_montada = proc['V3'] / v0 if ok('V3') and v0 else None
    formato = (f_asset is not None and f_montada is not None and
               f_asset <= 1 - ganho_formato and f_montada <= 1 - ganho_formato)

    lm = [x for x in links.get('montada', []) if x is not None]
    la = [x for x in links.get('asset', []) if x is not None]
    r_link = (sum(la) / len(la)) / (sum(lm) / len(lm)) if lm and la and sum(lm) > 0 else None
    return {'grade_asset': grade, 'razoes_grade': [round(r, 2) for r in g_pares],
            'formato_cru': formato, 'razao_formato_asset': None if f_asset is None else round(f_asset, 2),
            'razao_formato_montada': None if f_montada is None else round(f_montada, 2),
            'razao_link': None if r_link is None else round(r_link, 2),
            'link_mais_rapido': r_link is not None and r_link <= 1 - ganho_grade}


# =========================================================================================
# EARTH ENGINE: o mesmo cálculo do painel (copiado da K13, sem mudança)
# =========================================================================================
def poligonos_estado(nomes, nome_export):
    est = (ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
           .filter(ee.Filter.inList('ADM1_NAME', nomes)))
    return est.map(lambda f: f.set({'Nome_Local_Export': nome_export, 'Municipio': 'Estado_Completo',
                                     'Estado': f.get('ADM1_NAME')}))


def poligonos_municipios(nomes_estado, listas_nomes):
    variantes = [n for lista in listas_nomes for n in lista]
    mun = (ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
           .filter(ee.Filter.inList('ADM1_NAME', nomes_estado)).filter(ee.Filter.inList('ADM2_NAME', variantes)))
    return mun.map(lambda f: f.set({'Nome_Local_Export': f.get('ADM2_NAME'), 'Municipio': f.get('ADM2_NAME'),
                                     'Estado': f.get('ADM1_NAME')}))


def montar_grade(poligonos):
    """construirRegiaoSelecionada do painel: pixel de 0,1° cuja caixa toca o polígono, sem a classe 4."""
    proj = ee.Projection(CRS, TRANSFORM)
    classe = ee.Image(MASCARA).select('classe').unmask(0, False).rename('classe_q')
    img = ee.Image.pixelLonLat().addBands(classe).updateMask(classe.neq(4))
    amostra = img.sample(region=poligonos.geometry().buffer(ESCALA_AREA, 1000), projection=proj,
                         geometries=True, dropNulls=True)

    def caixa(f):
        c = f.geometry().coordinates()
        return f.setGeometry(f.geometry().buffer(ESCALA_AREA / 2, 100).bounds()).set({'Lon': c.get(0), 'Lat': c.get(1)})

    junta = ee.FeatureCollection(ee.Join.saveAll('munis_intersecao').apply(
        amostra.map(caixa), poligonos, ee.Filter.intersects(leftField='.geo', rightField='.geo', maxError=10)))

    def por_poligono(px):
        def um(p):
            return (ee.Feature(px.geometry()).set('polyInfo', p).set('Lat', px.get('Lat')).set('Lon', px.get('Lon'))
                    .set('Classe_Q', px.get('classe_q')))
        return ee.FeatureCollection(ee.List(px.get('munis_intersecao')).map(um))

    def chave(f):
        poly = ee.Feature(f.get('polyInfo'))
        lat = ee.Number(f.get('Lat')).add(100).format('%.4f')
        lon = ee.Number(f.get('Lon')).add(100).format('%.4f')
        return f.set({'ChaveOrdenacao': ee.String(poly.get('Municipio')).cat('_').cat(lat).cat('_').cat(lon),
                      'Estado_Ext': poly.get('Estado'), 'Muni_Ext': poly.get('Municipio'),
                      'Local_Ext': poly.get('Nome_Local_Export')})

    lista = junta.map(por_poligono).flatten().map(chave).sort('ChaveOrdenacao').toList(LIMITE_PONTOS_GRADE)

    def ponto(i):
        f = ee.Feature(lista.get(i))
        cq = ee.Number(f.get('Classe_Q'))
        return ee.Feature(ee.Geometry.Point([f.get('Lon'), f.get('Lat')]), {
            'Nome_Local_Export': f.get('Local_Ext'), 'Estado': f.get('Estado_Ext'), 'Municipio': f.get('Muni_Ext'),
            'ID_Ponto': ee.String('Ponto_').cat(ee.Number(i).add(1).format('%05d')),
            'Latitude': f.get('Lat'), 'Longitude': f.get('Lon'),
            'Qualidade_Pixel': ee.Algorithms.If(cq.eq(1), 'A', ee.Algorithms.If(cq.eq(2), 'B',
                                                ee.Algorithms.If(cq.eq(3), 'C', '')))})

    return ee.FeatureCollection(ee.List.sequence(0, lista.size().subtract(1)).map(ponto))


def _expandir(img):
    return img.unmask(img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMean(1, 'square', 'pixels'))


def _correcao_mes(mes):
    """Correção de leitura do solo e do escoamento dos dias V1.0 (montarCorrecaoMes do painel)."""
    solo = ee.Image(f'{SOLO}/Matriz_Solo_{mes:02d}')

    def fator(p):
        f = _expandir(solo.select(p + '_m_smap')).divide(_expandir(solo.select(p + '_m_era5')).max(1e-3))
        return ee.Image.constant(1).where(f.gt(5.0).unmask(0), ee.Image.constant(5.0).divide(f)).unmask(1)

    def teto(p):
        return (_expandir(solo.select(p + '_m_smap')).add(_expandir(solo.select(p + '_s_smap')).multiply(3.0))
                .min(0.9).unmask(0.9))

    return ee.Image.cat([fator('rsup').rename('c_rsup'), fator('rsub').rename('c_rsub'),
                         fator('ssur').rename('c_ssur'), fator('swat').rename('c_swat'),
                         teto('ssur').rename('teto_ssur'), teto('swat').rename('teto_swat')])


def colecao(geom, ini, fim):
    corr_mes = ee.List([_correcao_mes(m) for m in range(1, 13)])
    col = ee.ImageCollection(SAB).filterBounds(geom.bounds()).filterDate(ini, fim)

    def preparar(img):
        im = ee.Image(ee.Algorithms.If(img.bandNames().contains('precipitation_mm'),
                                       img.select(BANDAS_ANTIGAS, BANDAS_SAB), img.select(BANDAS_SAB)))
        alg = ee.String(ee.Algorithms.If(img.propertyNames().contains('versao_algoritmo'),
                                         img.get('versao_algoritmo'), 'V1.0'))
        c = ee.Image(corr_mes.get(img.date().get('month').subtract(1)))
        corrigidas = ee.Image.cat([
            im.select('runoff_sup_mm').multiply(c.select('c_rsup')).rename('runoff_sup_mm'),
            im.select('runoff_sub_mm').multiply(c.select('c_rsub')).rename('runoff_sub_mm'),
            im.select('soil_moisture_0_5cm_m3_m3').multiply(c.select('c_ssur')).min(c.select('teto_ssur'))
              .rename('soil_moisture_0_5cm_m3_m3'),
            im.select('soil_moisture_0_100cm_m3_m3').multiply(c.select('c_swat')).min(c.select('teto_swat'))
              .rename('soil_moisture_0_100cm_m3_m3')]).toFloat()
        im = ee.Image(ee.Algorithms.If(alg.equals('V1.0'), im.addBands(corrigidas, None, True), im))
        etp = im.select('et_potencial')
        etr = im.select('et_real').min(etp).rename('et_real')
        tr = im.select('transpiracao_mm').min(etr).rename('transpiracao_mm')
        im = im.addBands(ee.Image.cat([etr, tr]), None, True)
        amp = im.select('tmax_C').subtract(im.select('tmin_C')).rename('amplitude_diaria').toFloat()
        dfc = etp.subtract(etr).max(0).rename('deficit_diario').toFloat()
        ce = im.select('pr_mm').subtract(im.select('runoff_sup_mm')).max(0).rename('chuva_efetiva').toFloat()
        return im.addBands(ee.Image.cat([amp, dfc, ce]))

    return col.map(preparar).sort('system:time_start')


def linhas_diarias(ic, grade):
    def por_dia(img):
        versao = ee.String(ee.Algorithms.If(img.propertyNames().contains('versao'), img.get('versao'), 'definitiva'))
        tipo = ee.Dictionary({'definitiva': 'Historico_Observado', 'provisoria_era5': 'Provisorio_ERA5',
                              'provisoria_gfs': 'Previsao_GFS', 'provisoria_gfs_incompleta': 'Previsao_GFS_Parcial',
                              'falha_latencia_gfs': 'Sem_Dado'}).get(versao, 'Desconhecido')
        alg = ee.Algorithms.If(img.propertyNames().contains('versao_algoritmo'), img.get('versao_algoritmo'), 'V1.0')
        janela = ee.Algorithms.If(versao.equals('definitiva'), '12-12 UTC (D-1 a D)', '00-24 UTC')
        conf = ee.Algorithms.If(img.propertyNames().contains('Confianca_Prazo'), img.get('Confianca_Prazo'), '')
        data = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
        return img.reduceRegions(collection=grade, reducer=ee.Reducer.mean(), scale=ESCALA_AREA).map(
            lambda f: f.set({'Data': data, 'Tipo_Dado': tipo, 'Versao_Algoritmo': alg,
                             'Janela_Chuva_UTC': janela, 'Confianca_Prazo': conf}))
    return ic.map(por_dia).flatten()


BANDAS_SOMA = ['pr_mm', 'chuva_efetiva', 'runoff_sup_mm', 'runoff_sub_mm', 'et_potencial', 'et_real',
               'transpiracao_mm', 'deficit_diario']
BANDAS_MEDIA = ['tmax_C', 'tmin_C', 'RH', 'rs', 'u2', 'tsolo_C', 'tfolha_C', 'vpd', 'soil_moisture_0_5cm_m3_m3',
                'soil_moisture_0_100cm_m3_m3', 'amplitude_diaria']


def linhas_mensais(ic, grade, ano_ini, ano_fim):
    """exportarSerieMensal do painel, para vários anos num arquivo só."""
    inicio = ee.Date.fromYMD(ano_ini, 1, 1)
    n_meses = (ano_fim - ano_ini + 1) * 12

    def mes(m):
        d0 = inicio.advance(m, 'month')
        d1 = d0.advance(1, 'month')
        icm = ic.filterDate(d0, d1)
        img = icm.select(BANDAS_SOMA).sum().addBands(icm.select(BANDAS_MEDIA).mean())
        versoes = icm.map(lambda im: im.set('alg_tmp', ee.Algorithms.If(
            im.propertyNames().contains('versao_algoritmo'), im.get('versao_algoritmo'), 'V1.0'))
        ).aggregate_array('alg_tmp').distinct().sort()
        dias_mes = d1.advance(-1, 'day').get('day')
        return img.set('Data', d0.format('YYYY-MM-dd'), 'n_imgs', icm.size(),
                       'Versao_Algoritmo', ee.List(versoes).join('+'), 'Dias_no_Mes', dias_mes,
                       'Mes_Completo', ee.Algorithms.If(icm.size().eq(dias_mes), 'sim', 'nao'))

    icm = ee.ImageCollection.fromImages(ee.List.sequence(0, n_meses - 1).map(mes)).filter(ee.Filter.gt('n_imgs', 0))

    def reduzir(img):
        return img.reduceRegions(collection=grade, reducer=ee.Reducer.mean(), scale=ESCALA_AREA).map(
            lambda f: f.set({'Data': img.get('Data'), 'Tipo_Dado': 'Agregado_Mensal',
                             'Versao_Algoritmo': img.get('Versao_Algoritmo'), 'N_Dias': img.get('n_imgs'),
                             'Dias_no_Mes': img.get('Dias_no_Mes'), 'Mes_Completo': img.get('Mes_Completo')}))
    return icm.map(reduzir).flatten()


def formatar(fc, modo, extras, sal):
    """formatarExportacaoClima do painel (revisão 18h30). modo: 'ponto' (painel atual, "18.40"),
    'virgula' (painel 2026.10.2, "18,40") ou 'cru' (número sem formatação). 'sal' muda só uma propriedade que
    não vai para o CSV: cada link é um pedido novo e o Earth Engine não reaproveita o cálculo de outro."""
    def linha(f):
        data = ee.String(f.get('Data'))
        partes = data.split('-').cat(ee.List(['', '', '']))
        d = f.toDictionary()

        def valor(banda, casas):
            v = ee.Number(d.get(banda, -9999))
            if modo == 'cru':
                saida = v
            elif modo == 'virgula':
                saida = v.format('%.' + str(casas) + 'f').replace('\\.', ',')
            else:
                saida = v.format('%.' + str(casas) + 'f')
            return ee.Algorithms.If(v.eq(-9999), None, saida)

        props = {'Tipo_Dado': d.get('Tipo_Dado', 'Agregado'), 'Versao_Algoritmo': d.get('Versao_Algoritmo', ''),
                 'Data_Completa': data, 'Ano': partes.get(0), 'Mes': partes.get(1), 'Dia': partes.get(2),
                 'N_Ponto': f.get('ID_Ponto'), 'Estado': f.get('Estado'), 'Municipio': f.get('Municipio'),
                 'Sal_K13': sal}
        for col, banda, casas in NUMERICAS:
            props[col] = valor(banda, casas)
        for col in extras:
            props[col] = d.get(col, '')
        return ee.Feature(None, props)
    return fc.map(linha)


def status_de(ids):
    """Estado das tarefas pelo número (funciona também depois de reiniciar a célula)."""
    try:
        lista = ee.data.getTaskStatus(ids)
        return {s['id']: normalizar_status(s) for s in lista}
    except Exception:
        saida = {}
        for i in ids:
            try:
                saida[i] = normalizar_status(ee.data.getOperation(f'projects/{PROJETO}/operations/{i}'))
            except Exception as e:
                saida[i] = {'state': 'DESCONHECIDO', 'error_message': str(e)[:150]}
        return saida


def arquivos_do_caso(prefixo):
    return sorted(glob.glob(os.path.join(DRIVE, PASTA_DRIVE, prefixo + '*.csv')))


def link_na_hora(rotulo, fc, esperado):
    """Gera o link como o painel e baixa. Devolve (segundos ou None, texto do resultado)."""
    try:
        url = fc.getDownloadURL(filetype='csv', selectors=COLUNAS_DIARIA, filename=rotulo)
    except Exception as e:
        return None, f'erro ao gerar o link: {str(e)[:150]}'
    t1 = time.time()
    try:
        r = requests.get(url, timeout=TIMEOUT_LINK_S)
        esperas = 0
        while r.status_code == 429 and esperas < 6:
            esperas += 1
            time.sleep(60)
            t1 = time.time()
            r = requests.get(url, timeout=TIMEOUT_LINK_S)
        seg = round(time.time() - t1, 1)
        if r.status_code != 200:
            return None, f'resposta {r.status_code} em {seg} s: {r.text[:150]}'
        pares = pd.read_csv(io.BytesIO(r.content), usecols=['N_Ponto', 'Data_Completa'], dtype=str)
        if len(pares) != esperado or pares.duplicated().any():
            return None, f'incompleto: {len(pares):,} de {esperado:,} linhas'
        return seg, f'{seg} s | {len(r.content) / 1e6:.1f} MB'
    except requests.exceptions.Timeout:
        return None, f'sem resposta em {TIMEOUT_LINK_S} s'
    except Exception as e:
        return None, f'erro: {str(e)[:150]}'


# =========================================================================================
# EXECUÇÃO
# =========================================================================================
if __name__ == '__main__':
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log(f'🔎 K15: grade em asset x grade montada; formatação dos números | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log(f'   Grava só o asset de teste {ASSET_GRADE} (apagado no fim) e CSV na pasta {PASTA_DRIVE} do Drive.')
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)
    from google.colab import drive
    drive.mount('/content/drive')
    os.makedirs(os.path.join(DRIVE, 'K15'), exist_ok=True)
    ARQ_PROG = os.path.join(DRIVE, 'K15', 'K15_progresso.json')
    prog = {}
    if os.path.exists(ARQ_PROG):
        with open(ARQ_PROG, encoding='utf-8') as f:
            prog = json.load(f)
        log(f"   ♻️ Retomando (carimbo {prog.get('carimbo')}).")
    carimbo = prog.get('carimbo') or f'{AGORA:%Y%m%d_%H%M}'
    prog['carimbo'] = carimbo
    prog.setdefault('tarefas', {})
    prog.setdefault('links', {})

    def salvar():
        with open(ARQ_PROG, 'w', encoding='utf-8') as f:
            json.dump(prog, f, ensure_ascii=False, indent=1)

    def acompanhar(ids, rotulo):
        ultimo, limite = {}, time.time() + ESPERA_MAX_H * 3600
        while True:
            st = status_de(list(ids.values()))
            for k, i in ids.items():
                e = st.get(i, {}).get('state', '?')
                if ultimo.get(k) != e:
                    ultimo[k] = e
                    log(f"   {datetime.now(timezone(timedelta(hours=-3))):%H:%M} {rotulo} {k}: {e}")
            if all(st.get(i, {}).get('state') in TERMINAIS for i in ids.values()) or time.time() > limite:
                return st
            time.sleep(INTERVALO_S)

    # ---------------------------------------------------------------- grade
    log('\n0) Grade do Paraná como o painel')
    pr_pol = poligonos_estado(PARANA, 'Parana')
    geom = pr_pol.geometry()
    grade_montada = montar_grade(pr_pol)
    n = grade_montada.size().getInfo()
    ic = colecao(geom, *PERIODO)
    n_dias = ic.size().getInfo()
    esperado = n * n_dias
    log(f'   {n} pontos x {n_dias} dias = {esperado:,} linhas')

    log(f'\n1) Asset de teste com a grade ({ASSET_GRADE})')
    try:
        ee.data.getAsset(ASSET_GRADE)
        existe = True
    except Exception:
        existe = False
    if not existe:
        t = ee.batch.Export.table.toAsset(collection=grade_montada, description='K15_grade_PR', assetId=ASSET_GRADE)
        t.start()
        log(f'   🚀 gravando a grade (tarefa {t.id})')
        st = acompanhar({'grade': t.id}, 'asset')
        if st.get(t.id, {}).get('state') != 'COMPLETED':
            log(f"   ❌ a gravação da grade falhou: {st.get(t.id, {}).get('error_message', '')}. Me envie o LOG.")
            raise SystemExit(1)
    else:
        log('   ♻️ o asset de teste já existe (execução anterior)')
    grade_asset = ee.FeatureCollection(ASSET_GRADE)
    props = ['ID_Ponto', 'Latitude', 'Longitude', 'Qualidade_Pixel', 'Municipio', 'Estado', 'Nome_Local_Export']

    def tabela_grade(fc):
        lst = fc.reduceColumns(ee.Reducer.toList(len(props)), props).get('list').getInfo()
        return sorted(tuple(str(x) for x in linha) for linha in lst)
    igual_grade = tabela_grade(grade_montada) == tabela_grade(grade_asset)
    log(f"   {'✅' if igual_grade else '❌'} grade do asset igual à montada (ID, latitude, longitude, qualidade, "
        f"município, estado, local): {'sim' if igual_grade else 'NÃO'}")
    if not igual_grade:
        log('   ❌ Sem grade igual, a comparação não vale. Me envie o LOG.')
        raise SystemExit(1)
    grades = {'montada': grade_montada, 'asset': grade_asset}

    def pedido(qual, formato):
        return formatar(linhas_diarias(colecao(geom, *PERIODO), grades[qual]), formato, EXTRAS_DIARIA, 0)

    # ---------------------------------------------------------------- exportações
    log('\n2) Exportações (2 por vez, na ordem de envio)')
    for v, qual, formato in VERSOES:
        if v in prog['tarefas']:
            log(f"   ♻️ {v}: já enviada (tarefa {prog['tarefas'][v]['id']})")
            continue
        prefixo = f'K15_{v}_{qual}_{formato}_{carimbo}'
        t = ee.batch.Export.table.toDrive(collection=pedido(qual, formato), description=f'K15_{v}_{qual}_{formato}',
                                          folder=PASTA_DRIVE, fileNamePrefix=prefixo, fileFormat='CSV',
                                          selectors=COLUNAS_DIARIA)
        t.start()
        prog['tarefas'][v] = {'id': t.id, 'grade': qual, 'formato': formato, 'prefixo': prefixo}
        salvar()
        log(f'   🚀 {v} (grade {qual}, números {formato}): tarefa {t.id}')
    st = acompanhar({v: d['id'] for v, d in prog['tarefas'].items()}, 'exportação')

    # ---------------------------------------------------------------- conferência
    log('\n3) Conferência dos CSV')
    dfs, linhas, proc = {}, [], {}
    for v, d in prog['tarefas'].items():
        r = resumo_tarefa(st.get(d['id'], {}))
        reg = {'versao': v, 'grade': d['grade'], 'formato': d['formato'], **r, 'MB': None, 'ok': False,
               'detalhe': r['erro']}
        if r['estado'] == 'COMPLETED':
            t_esp = time.time() + ESPERA_ARQUIVO_S
            arqs = arquivos_do_caso(d['prefixo'])
            while not arqs and time.time() < t_esp:
                time.sleep(30)
                arqs = arquivos_do_caso(d['prefixo'])
            if arqs:
                df = pd.concat([pd.read_csv(a, dtype=str, keep_default_na=False) for a in arqs], ignore_index=True)
                ok, det = conferir_csv(list(df.columns), df[['N_Ponto', 'Data_Completa']], COLUNAS_DIARIA, esperado)
                reg.update(MB=round(sum(os.path.getsize(a) for a in arqs) / 1e6, 1), ok=ok, detalhe=det)
                dfs[v] = df
            else:
                reg['detalhe'] = f'arquivo não apareceu em {PASTA_DRIVE}'
        proc[v] = reg['processamento_min'] if reg['ok'] else None
        linhas.append(reg)
    identico = 'V0a' in dfs and all(v in dfs and comparar_identicos(dfs['V0a'], dfs[v]) for v in ('V1a', 'V1b', 'V0b'))
    arred = {v: ('V0a' in dfs and v in dfs and comparar_arredondado(dfs['V0a'], dfs[v])) for v in ('V2', 'V3')}
    for reg in linhas:
        v = reg['versao']
        if v in ('V1a', 'V1b', 'V0b'):
            reg['detalhe'] = (reg['detalhe'] + ' ' if reg['detalhe'] else '') + \
                ('idêntico a V0a' if identico else 'DIFERENTE de V0a (alguma das versões)')
        if v in arred:
            reg['detalhe'] = (reg['detalhe'] + ' ' if reg['detalhe'] else '') + \
                ('igual a V0a a menos do arredondamento' if arred[v] else 'DIFERENTE de V0a além do arredondamento')
        log(f"   {'✅' if reg['ok'] else '❌'} {v} (grade {reg['grade']}, números {reg['formato']}): {reg['estado']} | "
            f"fila {reg['fila_min']} min | processamento {reg['processamento_min']} min | EECU {reg['EECU_h']} h | "
            f"{reg['MB']} MB{(' | ' + reg['detalhe']) if reg['detalhe'] else ''}")

    # ---------------------------------------------------------------- links
    log('\n4) Link na hora (como o painel), grade montada x asset, alternados')
    for k, qual in enumerate(('montada', 'asset', 'montada', 'asset')):
        rot = f'K15_link_{qual}_{k // 2 + 1}'
        if rot not in prog['links']:
            seg, txt = link_na_hora(rot, pedido(qual, 'ponto'), esperado)
            prog['links'][rot] = {'grade': qual, 'segundos': seg, 'texto': txt}
            salvar()
        r = prog['links'][rot]
        log(f"   {'✅' if r['segundos'] is not None else '❌'} {rot}: {r['texto']}")
    links = {'montada': [], 'asset': []}
    for r in prog['links'].values():
        links[r['grade']].append(r['segundos'])

    # ---------------------------------------------------------------- resultado
    tab = pd.DataFrame(linhas)
    tab.to_csv(os.path.join(PASTA, 'K15_resultados.csv'), sep=';', decimal=',', encoding='utf-8-sig', index=False)
    dec = decidir_k15(proc, identico, links)
    log('\n' + '=' * 100)
    log('RESULTADO FINAL K15')
    log('=' * 100)
    tabela(tab.set_index('versao')[['grade', 'formato', 'processamento_min', 'EECU_h', 'MB', 'ok']], 'Exportações:')
    log(f"\n   G  Grade em asset: {'ADOTAR' if dec['grade_asset'] else 'não adotar'} | tempo V1/V0 nos 2 pares: "
        f"{dec['razoes_grade']} (adotar se as 2 razões <= 0,70 e V1 idêntico a V0: {'sim' if identico else 'não'})")
    log(f"   F  Números sem formatação: {'ganho suficiente (decidir com você)' if dec['formato_cru'] else 'manter o formato do painel'}"
        f" | V2/V1 {dec['razao_formato_asset']} e V3/V0 {dec['razao_formato_montada']} (trocar se as 2 <= 0,75)")
    log(f"   L  Link na hora: tempo asset/montada {dec['razao_link']} "
        f"({'mais rápido com o asset' if dec['link_mais_rapido'] else 'sem ganho de 30%'})")
    pd.DataFrame([dec]).to_csv(os.path.join(PASTA, 'K15_DECISOES.csv'), sep=';', encoding='utf-8-sig', index=False)

    if APAGAR_ASSET_NO_FIM:
        try:
            ee.data.deleteAsset(ASSET_GRADE)
            log(f'\n   🧹 asset de teste apagado: {ASSET_GRADE}')
        except Exception as e:
            log(f'\n   ⚠️ não consegui apagar {ASSET_GRADE} ({str(e)[:100]}); apague à mão na aba Assets.')
    log(f'\nTempo desta execução: {(time.time() - T0) / 60:.0f} min. Nenhum asset do sistema foi tocado.')
    log(f'Os CSV estão na pasta {PASTA_DRIVE} do seu Drive; pode apagá-la depois de me enviar o zip.')
    z = shutil.make_archive(PASTA, 'zip', PASTA)
    log(f'📦 {z}')
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        log('   (baixe pelo painel Arquivos do Colab)')
