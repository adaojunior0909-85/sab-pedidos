# >>> SIMULAÇÃO K12 v2 (22/10/2026, 15h): download do CSV DIÁRIO DE UM ANO de um estado inteiro. SÓ LEITURA. Cole inteiro, sem editar. <<<
# =========================================================================================
# POR QUE EXISTE
#   No painel 06, o CSV diário do Paraná inteiro gerou o link, mas ao abrir voltou
#   {"error": {"code": 503, "message": "The service is currently unavailable."}}.
#   O objetivo é baixar UM ANO INTEIRO do estado (cerca de 2.000 pontos x 365 dias = 730 mil linhas).
#   Antes de mudar o painel, esta simulação mede, com os mesmos dados e o mesmo cálculo do painel:
#     - quantas linhas um link aguenta (60.000, 30.000, 15.000 ou 8.000);
#     - quanto pesa converter os números em TEXTO COM VÍRGULA (como hoje) em vez de NÚMEROS com ponto;
#     - se o ANO INTEIRO sai completo em partes, sem perder nem repetir ponto ou dia.
#
# O QUE FAZ (nada é criado, apagado ou exportado no Earth Engine; não trava a sessão)
#   1. Monta a grade do estado como o painel (pixels de 0,1°, sem a classe 4 da máscara de qualidade).
#   2. Monta o CSV diário do ano como o painel: mesmas 33 colunas, na mesma ordem; correção de leitura do
#      solo e do escoamento nos dias V1.0; ET real, transpiração, amplitude, déficit e chuva efetiva iguais.
#   3. Etapa 1: com o 1º bloco de pontos, testa links de 60.000, 30.000, 15.000 e 8.000 linhas e escolhe o
#      maior que abre. No bloco de 15.000, compara texto com vírgula x número com ponto (tempo e valores).
#   3b. Etapa 1b (v2): repete o pedido que deu 503 no painel (Paraná, outubro de 2026, 1 link, texto com
#      vírgula, grade refeita no link) e troca uma coisa de cada vez: grade pronta; depois números com ponto.
#   4. Etapa 2: baixa o ANO INTEIRO em partes do tamanho escolhido, UM LINK POR VEZ (como quem clica nos
#      links do painel). Resposta 429 ("Too many concurrent aggregations") é fila cheia, não tamanho: espera
#      1 minuto e tenta o mesmo link de novo. Só resposta 503 ou falta de resposta divide a parte.
# v2: a 1ª execução (14h31) mostrou link de 60.000 linhas abrindo em 2 min, mas com 3 links ao mesmo tempo o
#     Earth Engine recusou 13 pedidos com 429, e a v1 tratava o 429 como parte grande demais.
#   5. Etapa 3: confere o ano: linhas = pontos x dias, nenhum par (ponto, dia) repetido, todos os pontos e
#      todos os dias presentes, colunas na ordem do painel.
#   6. Resume: tamanho de parte para o painel, número de links por ano e tempo total.
#
# TEMPO: cerca de 1 hora (um link por vez, de 2 a 4 minutos cada). Deixe a aba aberta.
# NO FIM: o Colab baixa simulacao_K12_<data>.zip (LOG_K12.txt, K12_links.csv). Me envie o zip.
# =========================================================================================
import io
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone

import ee
import pandas as pd
import requests

# ------------------------------------------------------------------ parâmetros (não precisa mudar)
PROJETO = 'clima-492922'
SAB = f'projects/{PROJETO}/assets/SAB_V1'
MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
SOLO = f'projects/{PROJETO}/assets/SICSB_SOLO_2015_2025'
ESTADO_GAUL = ['Parana', 'Paraná']        # como o painel procura o nome (com e sem acento)
NOME_EXPORT = 'Parana'
ANO = 2025                                # ano completo do histórico (BR-DWGD, dias V1.0 com a correção de leitura)
ESCALA_AREA = 11132                       # CFG.escalaArea do painel
TAMANHOS = (60000, 30000, 15000, 8000)    # linhas por link testadas na etapa 1, do maior para o menor
LINKS_SIMULTANEOS = 1                     # um link por vez (com 3 ao mesmo tempo o Earth Engine devolveu 429)
ESPERA_429_S = 60                         # espera antes de repetir um link recusado com 429
TENTATIVAS_429 = 6
MES_503 = ('2026-10-01', '2026-11-01')    # o pedido que deu 503 no painel (outubro de 2026)
TIMEOUT_S = 900                           # espera máxima por link
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
BANDAS_SAB = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2', 'tsolo_C',
              'tfolha_C', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm',
              'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
BANDAS_ANTIGAS = ['precipitation_mm', 'temp_max_C', 'temp_min_C', 'relative_humidity_pct', 'et_potential_mm',
                  'et_actual_mm', 'vpd_kpa', 'solar_radiation_mj_m2', 'wind_speed_m_s', 'soil_temperature_C',
                  'skin_temperature_C', 'transpiration_mm', 'surface_runoff_mm', 'subsurface_runoff_mm',
                  'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
# Colunas do CSV diário do painel 2026.10.4, na mesma ordem (getColunasClimaDiaria)
COLUNAS = ['Tipo_Dado', 'Versao_Algoritmo', 'Data_Completa', 'Ano', 'Mes', 'Dia', 'N_Ponto', 'Latitude', 'Longitude',
           'Estado', 'Municipio', 'Precipitacao_mm', 'Chuva_Efetiva_mm', 'Runoff_Superficial_mm',
           'Runoff_Subsuperficial_mm', 'Temperatura_Maxima_C', 'Temperatura_Minima_C', 'Amplitude_Termica_C',
           'Temperatura_Solo_C', 'Temperatura_Folha_C', 'Umidade_Relativa_Porc', 'Vento_ms', 'Radiacao_Solar_MJ_m2',
           'Evapotranspiracao_Potencial_mm', 'Evapotranspiracao_Real_mm', 'Transpiracao_Planta_mm',
           'Deficit_Hidrico_mm', 'Deficit_Pressao_Vapor_kPa', 'Umidade_Volumetrica_Solo_0_5cm_m3_m3',
           'Umidade_Volumetrica_Solo_0_100cm_m3_m3', 'Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo']
# coluna do CSV -> (banda, casas decimais), como formatarExportacaoClima do painel
NUMERICAS = [('Latitude', 'Latitude', 5), ('Longitude', 'Longitude', 5), ('Precipitacao_mm', 'pr_mm', 2),
             ('Chuva_Efetiva_mm', 'chuva_efetiva', 2), ('Runoff_Superficial_mm', 'runoff_sup_mm', 2),
             ('Runoff_Subsuperficial_mm', 'runoff_sub_mm', 2), ('Temperatura_Maxima_C', 'tmax_C', 2),
             ('Temperatura_Minima_C', 'tmin_C', 2), ('Amplitude_Termica_C', 'amplitude_diaria', 2),
             ('Temperatura_Solo_C', 'tsolo_C', 2), ('Temperatura_Folha_C', 'tfolha_C', 2),
             ('Umidade_Relativa_Porc', 'RH', 2), ('Vento_ms', 'u2', 2), ('Radiacao_Solar_MJ_m2', 'rs', 2),
             ('Evapotranspiracao_Potencial_mm', 'et_potencial', 2), ('Evapotranspiracao_Real_mm', 'et_real', 2),
             ('Transpiracao_Planta_mm', 'transpiracao_mm', 2), ('Deficit_Hidrico_mm', 'deficit_diario', 2),
             ('Deficit_Pressao_Vapor_kPa', 'vpd', 2), ('Umidade_Volumetrica_Solo_0_5cm_m3_m3', 'soil_moisture_0_5cm_m3_m3', 3),
             ('Umidade_Volumetrica_Solo_0_100cm_m3_m3', 'soil_moisture_0_100cm_m3_m3', 3)]

AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'simulacao_K12_{AGORA:%Y%m%d_%H%M}')
LOG = os.path.join(PASTA, 'LOG_K12.txt')


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


# ------------------------------------------------------------------ funções puras (testadas offline)
def planejar_partes(n_pontos, n_unidades, max_linhas):
    """Blocos [início, fim) de pontos com no máximo max_linhas (pontos x dias) cada; um ponto nunca é dividido."""
    por_parte = max(1, max_linhas // max(1, n_unidades))
    return [(i, min(n_pontos, i + por_parte)) for i in range(0, n_pontos, por_parte)]


def dividir_bloco(i0, i1, n_unidades, max_linhas):
    """Refaz um bloco que falhou em blocos menores (metade do limite)."""
    return [(i0 + a, i0 + b) for a, b in planejar_partes(i1 - i0, n_unidades, max(1, max_linhas // 2))]


def dias_do_ano(ano):
    return (date(ano + 1, 1, 1) - date(ano, 1, 1)).days


def ler_csv_texto(texto, virgula):
    """Lê um CSV do Earth Engine (separador vírgula). Com virgula=True, os números vêm como "18,40"."""
    df = pd.read_csv(io.StringIO(texto), dtype=str, keep_default_na=False)
    if virgula:
        for col, _, _ in NUMERICAS:
            if col in df:
                df[col] = df[col].str.replace(',', '.', regex=False)
    for col, _, _ in NUMERICAS:
        if col in df:
            df[col] = pd.to_numeric(df[col].replace('', None), errors='coerce')
    return df


def diferenca_so_arredondamento(dv, dn):
    """True se, em cada coluna numérica, os dois formatos diferem no máximo 1 unidade da última casa
    (o texto do painel arredonda empate de um jeito e o número de outro, por exemplo 0,125 -> 0,13 ou 0,12)."""
    for col, _, casas in NUMERICAS:
        dif = (dv[col] - dn[col]).abs().max()
        if pd.notna(dif) and float(dif) > 10 ** -casas + 1e-9:
            return False
    return True


def conferir_ano(resumos, n_pontos, n_dias):
    """resumos: lista de (colunas, DataFrame com N_Ponto e Data_Completa) de cada parte. Devolve [(texto, ok)]."""
    colunas_ok = all(c == COLUNAS for c, _ in resumos)
    pares = pd.concat([d for _, d in resumos], ignore_index=True) if resumos else pd.DataFrame(columns=['N_Ponto', 'Data_Completa'])
    return [('colunas na ordem do painel em todas as partes', colunas_ok),
            (f'linhas = pontos x dias ({n_pontos * n_dias:,})', len(pares) == n_pontos * n_dias),
            ('nenhum par (ponto, dia) repetido', not pares.duplicated().any()),
            (f'todos os {n_pontos} pontos presentes', pares['N_Ponto'].nunique() == n_pontos),
            (f'todos os {n_dias} dias presentes', pares['Data_Completa'].nunique() == n_dias)]


# ------------------------------------------------------------------ Earth Engine: como o painel
def montar_grade(estado_fc):
    """Grade do painel (construirRegiaoSelecionada, estado inteiro): pixel de 0,1° cuja caixa toca o estado."""
    proj = ee.Projection(CRS, TRANSFORM)
    classe = ee.Image(MASCARA).select('classe').unmask(0, False).rename('classe_q')
    img = ee.Image.pixelLonLat().addBands(classe).updateMask(classe.neq(4))
    amostra = img.sample(region=estado_fc.geometry().buffer(ESCALA_AREA, 1000), projection=proj,
                         geometries=True, dropNulls=True)

    def caixa(f):
        c = f.geometry().coordinates()
        return f.setGeometry(f.geometry().buffer(ESCALA_AREA / 2, 100).bounds()).set({'Lon': c.get(0), 'Lat': c.get(1)})

    junta = ee.Join.saveAll('munis_intersecao').apply(
        amostra.map(caixa), estado_fc, ee.Filter.intersects(leftField='.geo', rightField='.geo', maxError=10))

    def chave(f):
        lat = ee.Number(f.get('Lat')).add(100).format('%.4f')
        lon = ee.Number(f.get('Lon')).add(100).format('%.4f')
        return f.set('ChaveOrdenacao', ee.String('Estado_Completo_').cat(lat).cat('_').cat(lon))

    lista = ee.FeatureCollection(junta).map(chave).sort('ChaveOrdenacao').toList(25000)
    estado_nome = ee.String(estado_fc.first().get('ADM1_NAME'))

    def ponto(i):
        f = ee.Feature(lista.get(i))
        cq = ee.Number(f.get('classe_q'))
        return ee.Feature(ee.Geometry.Point([f.get('Lon'), f.get('Lat')]), {
            'Nome_Local_Export': NOME_EXPORT, 'Estado': estado_nome, 'Municipio': 'Estado_Completo',
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


def colecao_ano(geom, ini=None, fim=None):
    corr_mes = ee.List([_correcao_mes(m) for m in range(1, 13)])
    ini, fim = ini or f'{ANO}-01-01', fim or f'{ANO + 1}-01-01'
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


def linhas_diarias(ic, pontos):
    def por_dia(img):
        versao = ee.String(ee.Algorithms.If(img.propertyNames().contains('versao'), img.get('versao'), 'definitiva'))
        tipo = ee.Dictionary({'definitiva': 'Historico_Observado', 'provisoria_era5': 'Provisorio_ERA5',
                              'provisoria_gfs': 'Previsao_GFS', 'provisoria_gfs_incompleta': 'Previsao_GFS_Parcial',
                              'falha_latencia_gfs': 'Sem_Dado'}).get(versao, 'Desconhecido')
        alg = ee.Algorithms.If(img.propertyNames().contains('versao_algoritmo'), img.get('versao_algoritmo'), 'V1.0')
        janela = ee.Algorithms.If(versao.equals('definitiva'), '12-12 UTC (D-1 a D)', '00-24 UTC')
        conf = ee.Algorithms.If(img.propertyNames().contains('Confianca_Prazo'), img.get('Confianca_Prazo'), '')
        data = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
        return img.reduceRegions(collection=pontos, reducer=ee.Reducer.mean(), scale=ESCALA_AREA).map(
            lambda f: f.set({'Data': data, 'Tipo_Dado': tipo, 'Versao_Algoritmo': alg,
                             'Janela_Chuva_UTC': janela, 'Confianca_Prazo': conf}))
    return ic.map(por_dia).flatten()


def formatar(fc, modo):
    """modo='texto_virgula': igual ao painel de hoje ("18,40"). modo='numero': número arredondado (18.4)."""
    def linha(f):
        data = ee.String(f.get('Data'))
        partes = data.split('-').cat(ee.List(['', '', '']))
        d = f.toDictionary()

        def valor(banda, casas):
            v = ee.Number(d.get(banda, -9999))
            if modo == 'texto_virgula':
                saida = v.format('%.' + str(casas) + 'f').replace('\\.', ',')
            else:
                fator = 10 ** casas
                saida = v.multiply(fator).round().divide(fator)
            return ee.Algorithms.If(v.eq(-9999), None, saida)

        props = {'Tipo_Dado': f.get('Tipo_Dado'), 'Versao_Algoritmo': f.get('Versao_Algoritmo'),
                 'Data_Completa': data, 'Ano': partes.get(0), 'Mes': partes.get(1), 'Dia': partes.get(2),
                 'N_Ponto': f.get('ID_Ponto'), 'Estado': f.get('Estado'), 'Municipio': f.get('Municipio'),
                 'Qualidade_Pixel': f.get('Qualidade_Pixel'), 'Janela_Chuva_UTC': f.get('Janela_Chuva_UTC'),
                 'Confianca_Prazo': f.get('Confianca_Prazo')}
        for col, banda, casas in NUMERICAS:
            props[col] = valor(banda, casas)
        return ee.Feature(None, props)
    return fc.map(linha)


def baixar(rotulo, fc):
    """Gera o link como o painel (getDownloadURL) e baixa. Devolve (resultado, texto do CSV ou None)."""
    t0 = time.time()
    try:
        url = fc.getDownloadURL(filetype='csv', selectors=COLUNAS, filename=rotulo)
    except Exception as e:
        return {'link': rotulo, 'resposta': 'erro ao gerar o link', 'segundos': round(time.time() - t0, 1),
                'MB': 0, 'linhas': 0, 'detalhe': str(e)[:160]}, None
    t1 = time.time()
    try:
        r = requests.get(url, timeout=TIMEOUT_S)
        esperas = 0
        while r.status_code == 429 and esperas < TENTATIVAS_429:   # fila cheia: espera e repete o mesmo link
            esperas += 1
            time.sleep(ESPERA_429_S)
            r = requests.get(url, timeout=TIMEOUT_S)
        texto = r.text if r.status_code == 200 else None
        linhas = max(0, texto.count('\n') - 1) if texto else 0
        det = '' if r.status_code == 200 else r.text.replace('\n', ' ')[:160]
        if esperas:
            det = (det + f' (repetido {esperas}x depois de 429)').strip()
        return {'link': rotulo, 'resposta': r.status_code, 'segundos': round(time.time() - t1, 1),
                'MB': round(len(r.content) / 1e6, 2), 'linhas': linhas, 'detalhe': det}, texto
    except requests.exceptions.Timeout:
        return {'link': rotulo, 'resposta': f'sem resposta em {TIMEOUT_S} s', 'segundos': TIMEOUT_S,
                'MB': 0, 'linhas': 0, 'detalhe': ''}, None
    except Exception as e:
        return {'link': rotulo, 'resposta': 'erro na conexão', 'segundos': round(time.time() - t1, 1),
                'MB': 0, 'linhas': 0, 'detalhe': str(e)[:160]}, None


def ok(res):
    return res['resposta'] == 200


# ------------------------------------------------------------------ execução
if __name__ == '__main__':
    os.makedirs(PASTA, exist_ok=True)
    T_INICIO = time.time()
    log(f'🔎 K12: simulação do download de um ano do estado | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log(f'   Estado: {NOME_EXPORT} | ano {ANO} | CSV diário | nada é gravado no Earth Engine')
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    estado = (ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
              .filter(ee.Filter.inList('ADM1_NAME', ESTADO_GAUL)))
    ic = colecao_ano(estado.geometry())

    log('\n1) Grade e período')
    t0 = time.time()
    feats = montar_grade(estado).getInfo()['features']
    n_pontos = len(feats)
    n_dias = ic.size().getInfo()
    log(f'   {n_pontos} pontos (como o painel) | {n_dias} dias no SAB_V1 em {ANO} (esperado {dias_do_ano(ANO)}) | '
        f'{n_pontos * n_dias:,} linhas no ano | grade em {time.time() - t0:.0f} s')
    pontos = [ee.Feature(ee.Geometry.Point(f['geometry']['coordinates']), f['properties']) for f in feats]

    def csv_do_bloco(i0, i1, modo='numero'):
        return formatar(linhas_diarias(ic, ee.FeatureCollection(pontos[i0:i1])), modo)

    resultados = []

    def registrar(etapa, res):
        res = dict(res, etapa=etapa)
        resultados.append(res)
        simb = '✅' if ok(res) else '❌'
        log(f"   {simb} {res['link']}: resposta {res['resposta']} | {res['segundos']} s | {res['MB']} MB | "
            f"{res['linhas']:,} linhas {('| ' + res['detalhe']) if res['detalhe'] else ''}")
        return res

    # ---------------------------------------------------------------- etapa 1
    log('\n2) Etapa 1: quantas linhas um link aguenta (1º bloco de pontos, números com ponto)')
    tamanho = None
    for lim in TAMANHOS:
        i0, i1 = planejar_partes(n_pontos, n_dias, lim)[0]
        res, _ = baixar(f'E1_{lim}_linhas', csv_do_bloco(i0, i1))
        registrar('1', res)
        if ok(res):
            tamanho = lim
            break
    if tamanho is None:
        log('   ❌ nem 8.000 linhas abriram: há outro gargalo além do tamanho. Me envie o zip.')

    log('\n2b) Etapa 1b: o pedido que deu 503 no painel (Paraná, out/2026, 1 link) mudando uma coisa por vez')
    ic_mes = colecao_ano(estado.geometry(), *MES_503)
    grade_refeita = montar_grade(estado)
    grade_pronta = ee.FeatureCollection(pontos)
    for rot, grade, modo in (('E1b_como_hoje_texto_grade_refeita', grade_refeita, 'texto_virgula'),
                             ('E1b_texto_grade_pronta', grade_pronta, 'texto_virgula'),
                             ('E1b_numero_grade_pronta', grade_pronta, 'numero')):
        registrar('1b', baixar(rot, formatar(linhas_diarias(ic_mes, grade), modo))[0])

    comp = None
    if tamanho:
        log('\n3) Peso do texto com vírgula: o mesmo bloco de 15.000 linhas nos dois formatos')
        i0, i1 = planejar_partes(n_pontos, n_dias, 15000)[0]
        rn, tn = baixar('E1c_15000_numero', csv_do_bloco(i0, i1, 'numero'))
        rv, tv = baixar('E1c_15000_texto_virgula', csv_do_bloco(i0, i1, 'texto_virgula'))
        registrar('1c', rn)
        registrar('1c', rv)
        if tn and tv:
            dn = ler_csv_texto(tn, virgula=False).set_index(['N_Ponto', 'Data_Completa'])
            dv = ler_csv_texto(tv, virgula=True).set_index(['N_Ponto', 'Data_Completa'])
            comuns = dv.index.intersection(dn.index)
            cols = [c for c, _, _ in NUMERICAS]
            comp = [('mesmos pares (ponto, dia) nos dois formatos', len(comuns) == len(dn) == len(dv)),
                    ('números com ponto = texto com vírgula (só arredondamento)',
                     diferenca_so_arredondamento(dv.loc[comuns], dn.loc[comuns])),
                    ('mesmas células vazias nos dois formatos',
                     int(dv.loc[comuns, cols].isna().sum().sum()) == int(dn.loc[comuns, cols].isna().sum().sum()))]
            for txt, cond in comp:
                log(f"   {'✅' if cond else '❌'} {txt}")
            log(f"   tempo: número com ponto {rn['segundos']} s x texto com vírgula {rv['segundos']} s | "
                f"tamanho: {rn['MB']} MB x {rv['MB']} MB")

    # ---------------------------------------------------------------- etapa 2
    resumos, falhas_finais = [], []
    if tamanho:
        blocos = planejar_partes(n_pontos, n_dias, tamanho)
        log(f'\n4) Etapa 2: o ano inteiro em {len(blocos)} partes de até {tamanho:,} linhas '
            f'({LINKS_SIMULTANEOS} links por vez)')

        def tarefa(k, i0, i1, rot):
            res, texto = baixar(rot, csv_do_bloco(i0, i1))
            resumo = None
            if texto:
                df = pd.read_csv(io.StringIO(texto), dtype=str, keep_default_na=False)
                resumo = (list(df.columns), df[['N_Ponto', 'Data_Completa']].copy())
            return k, i0, i1, res, resumo

        pendentes = [(k, a, b, f'E2_parte{k + 1:03d}de{len(blocos):03d}') for k, (a, b) in enumerate(blocos)]
        for tentativa in (1, 2, 3):
            if not pendentes:
                break
            if tentativa > 1:
                log(f'   Tentativa {tentativa}: {len(pendentes)} parte(s) que falharam')
            falharam = []
            with ThreadPoolExecutor(max_workers=LINKS_SIMULTANEOS) as ex:
                futuros = [ex.submit(tarefa, *p) for p in pendentes]
                for fu in as_completed(futuros):
                    k, a, b, res, resumo = fu.result()
                    registrar(f'2.{tentativa}', res)
                    if resumo:
                        resumos.append(resumo)
                    else:
                        falharam.append((k, a, b))
            if tentativa == 1:   # 429 já foi repetido dentro de baixar(); aqui é uma 2ª chance para o resto
                pendentes = [(k, a, b, f'E2_parte{k + 1:03d}_de_novo') for k, a, b in falharam]
            else:   # na 3ª tentativa, a parte que falhou duas vezes é refeita em blocos menores
                pendentes = []
                for k, a, b in falharam:
                    for j, (c, d) in enumerate(dividir_bloco(a, b, n_dias, tamanho)):
                        pendentes.append((k, c, d, f'E2_parte{k + 1:03d}_menor{j + 1}'))
                if tentativa == 3:
                    falhas_finais = falharam

    # ---------------------------------------------------------------- etapa 3
    log('\n5) Etapa 3: o ano está completo?')
    chec = conferir_ano(resumos, n_pontos, n_dias) if tamanho else []
    for txt, cond in chec:
        log(f"   {'✅' if cond else '❌'} {txt}")

    tab = pd.DataFrame(resultados)[['etapa', 'link', 'resposta', 'segundos', 'MB', 'linhas', 'detalhe']]
    tab.to_csv(os.path.join(PASTA, 'K12_links.csv'), sep=';', decimal=',', encoding='utf-8-sig', index=False)
    e2 = tab[tab['etapa'].str.startswith('2')]
    if len(e2):
        tabela(e2.groupby('resposta').agg(links=('link', 'count'), segundos_medio=('segundos', 'mean'),
                                          MB_total=('MB', 'sum')).round(1), 'Etapa 2, por resposta:')

    log('\n' + '=' * 90)
    log('RESULTADO FINAL K12')
    log('=' * 90)
    minutos = (time.time() - T_INICIO) / 60
    e1b = {r['link']: ok(r) for r in resultados if r['etapa'] == '1b'}
    if e1b:
        txt = {True: 'abriu', False: 'falhou'}
        log(f"   Pedido do painel (out/2026, 1 link): como hoje {txt[e1b.get('E1b_como_hoje_texto_grade_refeita', False)]} | "
            f"grade pronta {txt[e1b.get('E1b_texto_grade_pronta', False)]} | "
            f"grade pronta + números {txt[e1b.get('E1b_numero_grade_pronta', False)]}")
        if not e1b.get('E1b_como_hoje_texto_grade_refeita', True) and e1b.get('E1b_texto_grade_pronta', False):
            log('   ➜ A causa do 503 é a grade refeita dentro de cada link.')
        elif all(e1b.values()):
            log('   ➜ O pedido de hoje abriu: o 503 do painel foi carga momentânea do Earth Engine ou links clicados juntos.')
    if tamanho and chec and all(c for _, c in chec) and (comp is None or all(c for _, c in comp)):
        n_links = len(planejar_partes(n_pontos, n_dias, tamanho))
        log(f'   ✅ O ano {ANO} do {NOME_EXPORT} saiu completo em {n_links} links de até {tamanho:,} linhas.')
        log(f'   ➜ PAINEL: números com ponto, grade calculada uma vez e partes de até {tamanho:,} linhas por link.')
        log(f'   Tempo total da simulação: {minutos:.0f} min.')
    elif tamanho and chec and all(c for _, c in chec):
        log('   ⚠️ O ano saiu completo, mas a comparação texto x número acusou diferença: me envie o zip.')
    elif tamanho:
        log(f'   ❌ O ano não saiu completo ({len(falhas_finais)} parte(s) falharam mesmo menores): me envie o zip.')
    else:
        log('   ❌ Nenhum tamanho de link abriu: me envie o zip.')

    log('\nNada foi gravado no Earth Engine.')
    z = shutil.make_archive(PASTA, 'zip', PASTA)
    log(f'📦 {z}')
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        log('   (baixe pelo painel Arquivos do Colab)')
