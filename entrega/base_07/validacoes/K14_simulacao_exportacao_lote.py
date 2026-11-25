# >>> SIMULAÇÃO K14 (29/10/2026): exportação em LOTE para o Drive (base do envio por e-mail). Cole inteiro, sem editar. <<<
# =========================================================================================
# POR QUE EXISTE
#   A K13 (29/10, 10h56) mostrou que o link gerado na hora (getDownloadURL, o que o painel usa) tem um teto de
#   cerca de 10 minutos de cálculo: 3 meses do Paraná levaram de 276 a 540 s, e 6 meses, 1 ano e Pato Branco
#   1961-2025 falharam perto de 590 s ("timed out", "memory", 503, 500), conforme a carga do Earth Engine.
#   A proposta é mandar os recortes grandes por e-mail: o pedido dispara uma EXPORTAÇÃO EM LOTE
#   (Export.table.toDrive), que não tem esse teto, e o solicitante recebe o link do arquivo pronto.
#   Antes de montar o formulário e o Apps Script, esta simulação mede, com o MESMO cálculo e as MESMAS colunas
#   do painel 2026.10.4 (revisão 18h30):
#     - se cada pedido grande termina, e em quanto tempo (fila + processamento);
#     - quanto processamento (EECU) cada um gasta da cota do projeto;
#     - se o CSV sai completo (linhas = pontos x dias ou meses, sem repetir, colunas na ordem do painel);
#     - se o CSV da exportação é IDÊNTICO ao do link do painel (caso C0, Pato Branco 2025, pequeno).
#
# CASOS (enviados juntos, como se fossem pedidos de pessoas diferentes; a fila do Earth Engine organiza)
#   C0  Pato Branco, diário, 2025 (5 mil linhas): exportação x link do painel, comparados célula a célula
#   C1  Paraná, diário, 2025 (~690 mil linhas): falhou no link na K13
#   C2  Paraná, diário, 2024 até o último dia do banco (~2 milhões de linhas, com 2026 e a previsão)
#   C3  Minas Gerais, diário, 2025 (~1,8 milhão de linhas)
#   C4  Pato Branco, diário, 1961 até o último dia do banco (~360 mil linhas): falhou no link na K13
#   C5  5 municípios do Sudoeste do PR, diário, 2016-2025, num arquivo só (~270 mil linhas)
#   C6  Paraná, mensal, 1961-2025 (~1,5 milhão de linhas mensais)
#
# REGRA DE DECISÃO (fixada antes de rodar)
#   O envio por e-mail é VIÁVEL se todos os casos C1 a C6 terminarem (COMPLETED) com o CSV completo, e o C0
#   sair idêntico ao do link do painel. O tempo que o solicitante esperaria é o tempo total de cada caso
#   (fila + processamento + cópia no Drive); o script mostra o maior e a mediana.
#
# O QUE GRAVA: só arquivos CSV na pasta K14_teste do seu Google Drive (nada no Earth Engine; nenhum asset).
#   As tarefas aparecem em https://code.earthengine.google.com/tasks com o nome K14_...
#   Depois de me enviar o zip, pode apagar a pasta K14_teste do Drive.
# TEMPO: de 30 minutos a 2 horas, conforme a fila. Deixe a aba aberta. Se a célula parar, rode de novo: as
#   tarefas já enviadas são acompanhadas pelo número delas (progresso no Drive) e não são enviadas de novo.
# NÃO rode junto com o 05b (um script de cada vez).
# NO FIM: o Colab baixa simulacao_K14_<data>.zip (LOG_K14.txt e K14_casos.csv). Me envie o zip.
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
PASTA_DRIVE = 'K14_teste'                 # pasta criada pela exportação na raiz do seu Drive
ESCALA_AREA = 11132                       # CFG.escalaArea do painel
LIMITE_PONTOS_GRADE = 25000               # CFG.limitePontosGrade do painel
INTERVALO_S = 30                          # de quanto em quanto tempo olha as tarefas
ESPERA_MAX_H = 4                          # desiste de acompanhar depois de 4 horas
ESPERA_ARQUIVO_S = 900                    # espera o arquivo aparecer no Drive depois de COMPLETED
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
PARANA = ['Parana', 'Paraná']
MINAS = ['Minas Gerais']
MUNICIPIOS = [['Pato Branco'], ['Francisco Beltrao', 'Francisco Beltrão'], ['Clevelandia', 'Clevelândia'],
              ['Coronel Vivida'], ['Mariopolis', 'Mariópolis']]

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
PASTA = os.path.join(BASE, f'simulacao_K14_{AGORA:%Y%m%d_%H%M}')
LOG = os.path.join(PASTA, 'LOG_K14.txt')
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
# FUNÇÕES PURAS (sem Earth Engine; testadas offline em testes/teste_k14.py)
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


def veredito(casos):
    """casos: lista de dicionários com 'caso', 'ok' e 'total_min'. Regra fixada no cabeçalho."""
    grandes = [c for c in casos if c['caso'] != 'C0']
    c0 = next((c for c in casos if c['caso'] == 'C0'), None)
    viavel = bool(grandes) and all(c['ok'] for c in grandes) and bool(c0 and c0['ok'])
    tempos = sorted(c['total_min'] for c in grandes if c['ok'] and c['total_min'] is not None)
    mediana = tempos[len(tempos) // 2] if tempos else None
    return viavel, (max(tempos) if tempos else None), mediana


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


def ler_pares(arquivos):
    cab, partes, mb = None, [], 0.0
    for a in arquivos:
        mb += os.path.getsize(a) / 1e6
        with open(a, encoding='utf-8') as f:
            c = f.readline().strip().split(',')
        cab = cab or c
        partes.append(pd.read_csv(a, usecols=['N_Ponto', 'Data_Completa'], dtype=str))
    pares = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=['N_Ponto', 'Data_Completa'])
    return cab or [], pares, round(mb, 1)


# =========================================================================================
# EXECUÇÃO
# =========================================================================================
if __name__ == '__main__':
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log(f'🔎 K14: exportação em lote para o Drive (base do envio por e-mail) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log(f'   Grava só CSV na pasta {PASTA_DRIVE} do seu Drive. Nada é gravado no Earth Engine.')
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)
    from google.colab import drive
    drive.mount('/content/drive')
    os.makedirs(os.path.join(DRIVE, 'K14'), exist_ok=True)
    ARQ_PROG = os.path.join(DRIVE, 'K14', 'K14_progresso.json')
    prog = {}
    if os.path.exists(ARQ_PROG):
        with open(ARQ_PROG, encoding='utf-8') as f:
            prog = json.load(f)
        log(f"   ♻️ Retomando: {len(prog.get('tarefas', {}))} tarefa(s) já enviadas (carimbo {prog.get('carimbo')}).")
    carimbo = prog.get('carimbo') or f'{AGORA:%Y%m%d_%H%M}'
    prog['carimbo'] = carimbo
    prog.setdefault('tarefas', {})

    def salvar():
        with open(ARQ_PROG, 'w', encoding='utf-8') as f:
            json.dump(prog, f, ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- grades e casos
    log('\n0) Grades (como o painel) e casos')
    pr_pol = poligonos_estado(PARANA, 'Parana')
    pr_grade = montar_grade(pr_pol)
    mg_pol = poligonos_estado(MINAS, 'Minas_Gerais')
    mg_grade = montar_grade(mg_pol)
    mun_pol = poligonos_municipios(PARANA, MUNICIPIOS)
    mun_grade = montar_grade(mun_pol)
    pb_pol = mun_pol.filter(ee.Filter.eq('Nome_Local_Export', 'Pato Branco'))
    pb_grade = montar_grade(pb_pol)
    n = {'pr': pr_grade.size().getInfo(), 'mg': mg_grade.size().getInfo(), 'mun': mun_grade.size().getInfo(),
         'pb': pb_grade.size().getInfo()}
    ultimo = ee.Date(ee.ImageCollection(SAB).aggregate_max('system:time_start')).format('YYYY-MM-dd').getInfo()
    fim_banco = (datetime.strptime(ultimo, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    log(f"   pontos: Paraná {n['pr']} | Minas Gerais {n['mg']} | 5 municípios {n['mun']} | Pato Branco {n['pb']}"
        f" | último dia do banco: {ultimo}")
    if not n['pr'] or not n['pb'] or not n['mg']:
        log('   ❌ Algum local ficou sem pontos (nome não achado no GAUL): me envie o LOG.')
        raise SystemExit(1)
    geom = {'pr': pr_pol.geometry(), 'mg': mg_pol.geometry(), 'mun': mun_pol.geometry(), 'pb': pb_pol.geometry()}
    grade = {'pr': pr_grade, 'mg': mg_grade, 'mun': mun_grade, 'pb': pb_grade}

    def diario(loc, ini, fim):
        ic = colecao(geom[loc], ini, fim)
        return formatar(linhas_diarias(ic, grade[loc]), 'ponto', EXTRAS_DIARIA, 0), n[loc] * ic.size().getInfo()

    def mensal(loc, a0, a1):
        ic = colecao(geom[loc], f'{a0}-01-01', f'{a1 + 1}-01-01')
        return formatar(linhas_mensais(ic, grade[loc], a0, a1), 'ponto', EXTRAS_MENSAL, 0), n[loc] * (a1 - a0 + 1) * 12

    casos = [('C0', 'PatoBranco_diario_2025', COLUNAS_DIARIA, lambda: diario('pb', '2025-01-01', '2026-01-01')),
             ('C1', 'Parana_diario_2025', COLUNAS_DIARIA, lambda: diario('pr', '2025-01-01', '2026-01-01')),
             ('C2', 'Parana_diario_2024_ate_hoje', COLUNAS_DIARIA, lambda: diario('pr', '2024-01-01', fim_banco)),
             ('C3', 'MinasGerais_diario_2025', COLUNAS_DIARIA, lambda: diario('mg', '2025-01-01', '2026-01-01')),
             ('C4', 'PatoBranco_diario_1961_ate_hoje', COLUNAS_DIARIA, lambda: diario('pb', '1961-01-01', fim_banco)),
             ('C5', 'Municipios_diario_2016_2025', COLUNAS_DIARIA, lambda: diario('mun', '2016-01-01', '2026-01-01')),
             ('C6', 'Parana_mensal_1961_2025', COLUNAS_MENSAL, lambda: mensal('pr', 1961, 2025))]

    # ---------------------------------------------------------------- envio
    log('\n1) Envio das exportações (todas de uma vez, como pedidos de pessoas diferentes)')
    fc_c0 = None
    for caso, nome, colunas, montar in casos:
        fc, esperado = montar()
        if caso == 'C0':
            fc_c0 = fc
        if caso in prog['tarefas']:
            log(f"   ♻️ {caso} {nome}: já enviada (tarefa {prog['tarefas'][caso]['id']})")
            continue
        prefixo = f'K14_{caso}_{nome}_{carimbo}'
        t = ee.batch.Export.table.toDrive(collection=fc, description=f'K14_{caso}_{nome}', folder=PASTA_DRIVE,
                                          fileNamePrefix=prefixo, fileFormat='CSV', selectors=colunas)
        t.start()
        prog['tarefas'][caso] = {'id': t.id, 'nome': nome, 'prefixo': prefixo, 'esperado': esperado,
                                 'colunas': colunas, 'enviada': datetime.now(timezone(timedelta(hours=-3))).strftime('%H:%M')}
        salvar()
        log(f'   🚀 {caso} {nome}: tarefa {t.id} | {esperado:,} linhas esperadas')

    # ---------------------------------------------------------------- C0 pelo link do painel
    log('\n2) C0 pelo link do painel (getDownloadURL), para comparar com a exportação')
    txt_link = None
    try:
        url = fc_c0.getDownloadURL(filetype='csv', selectors=COLUNAS_DIARIA, filename='K14_C0_link')
        r = requests.get(url, timeout=900)
        if r.status_code == 200:
            txt_link = r.text
            log(f'   ✅ link do painel: {len(txt_link.splitlines()) - 1:,} linhas')
        else:
            log(f'   ⚠️ link do painel respondeu {r.status_code}: {r.text[:150]}')
    except Exception as e:
        log(f'   ⚠️ link do painel falhou: {str(e)[:150]}')

    # ---------------------------------------------------------------- acompanhamento
    log(f'\n3) Acompanhando as tarefas a cada {INTERVALO_S} s (até {ESPERA_MAX_H} h)')
    ids = {c: v['id'] for c, v in prog['tarefas'].items()}
    ultimo_estado = {}
    limite = time.time() + ESPERA_MAX_H * 3600
    while True:
        st = status_de(list(ids.values()))
        for caso, i in ids.items():
            e = st.get(i, {}).get('state', '?')
            if ultimo_estado.get(caso) != e:
                ultimo_estado[caso] = e
                log(f"   {datetime.now(timezone(timedelta(hours=-3))):%H:%M} {caso}: {e}")
        if all(st.get(i, {}).get('state') in TERMINAIS for i in ids.values()) or time.time() > limite:
            break
        time.sleep(INTERVALO_S)

    # ---------------------------------------------------------------- conferência
    log('\n4) Conferência dos arquivos no Drive')
    linhas = []
    for caso, v in prog['tarefas'].items():
        r = resumo_tarefa(st.get(v['id'], {}))
        reg = {'caso': caso, 'pedido': v['nome'], 'linhas_esperadas': v['esperado'], **r, 'MB': None,
               'arquivos': 0, 'ok': False, 'detalhe': r['erro']}
        if r['estado'] == 'COMPLETED':
            t_esp = time.time() + ESPERA_ARQUIVO_S
            arqs = arquivos_do_caso(v['prefixo'])
            while not arqs and time.time() < t_esp:
                time.sleep(30)
                arqs = arquivos_do_caso(v['prefixo'])
            if not arqs:
                reg['detalhe'] = f"arquivo não apareceu em {PASTA_DRIVE} no Drive montado (prefixo {v['prefixo']})"
            else:
                cab, pares, mb = ler_pares(arqs)
                ok, det = conferir_csv(cab, pares, v['colunas'], v['esperado'])
                reg.update(MB=mb, arquivos=len(arqs), ok=ok, detalhe=det)
                if caso == 'C0':
                    if txt_link is None:
                        reg.update(ok=False, detalhe='sem o CSV do link para comparar')
                    else:
                        df_exp = pd.concat([pd.read_csv(a, dtype=str, keep_default_na=False) for a in arqs],
                                           ignore_index=True)
                        df_lnk = pd.read_csv(io.StringIO(txt_link), dtype=str, keep_default_na=False)
                        igual = comparar_identicos(df_exp, df_lnk)
                        reg.update(ok=ok and igual, detalhe=(det + ' ' if det else '') +
                                   ('idêntico ao link do painel' if igual else 'DIFERENTE do link do painel'))
        simb = '✅' if reg['ok'] else '❌'
        log(f"   {simb} {caso} {v['nome']}: {reg['estado']} | fila {reg['fila_min']} min | processamento "
            f"{reg['processamento_min']} min | total {reg['total_min']} min | {reg['MB']} MB em {reg['arquivos']} "
            f"arquivo(s) | EECU {reg['EECU_h']} h{(' | ' + reg['detalhe']) if reg['detalhe'] else ''}")
        linhas.append(reg)

    tab = pd.DataFrame(linhas)
    tab.to_csv(os.path.join(PASTA, 'K14_casos.csv'), sep=';', decimal=',', encoding='utf-8-sig', index=False)

    log('\n' + '=' * 100)
    log('RESULTADO FINAL K14')
    log('=' * 100)
    viavel, maior, mediana = veredito(linhas)
    tabela(tab.set_index('caso')[['pedido', 'estado', 'total_min', 'MB', 'EECU_h', 'ok']], 'Casos:')
    eecu = tab['EECU_h'].dropna().sum()
    if viavel:
        log(f'   ✅ ENVIO POR E-MAIL VIÁVEL: todos os pedidos grandes terminaram completos e o C0 saiu idêntico ao '
            f'link do painel.')
        log(f'   Espera do solicitante: mediana {mediana} min, maior {maior} min (fila + processamento).')
        log(f'   Cota gasta nos 7 casos: {eecu:.2f} EECU-hora.')
        log('   ➜ Próximo passo: formulário + Apps Script (pedido, exportação, e-mail com o link, limpeza).')
    else:
        log('   ❌ Algum caso não terminou completo ou o C0 saiu diferente: me envie o zip.')
    log(f'\nTempo desta execução: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine.')
    log(f'Os CSV estão na pasta {PASTA_DRIVE} do seu Drive; pode apagá-la depois de me enviar o zip.')
    z = shutil.make_archive(PASTA, 'zip', PASTA)
    log(f'📦 {z}')
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        log('   (baixe pelo painel Arquivos do Colab)')
