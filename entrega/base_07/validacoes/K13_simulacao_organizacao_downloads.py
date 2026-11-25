# >>> SIMULAÇÃO K13 (29/10/2026): a melhor forma de dividir e baixar os CSV do painel. SÓ LEITURA. Cole inteiro, sem editar. <<<
# =========================================================================================
# POR QUE EXISTE
#   Hoje o painel 06 gera 1 dicionário + 1 link POR LOCAL E POR ANO, sem olhar o tamanho. Isso dá dezenas de
#   links minúsculos em áreas pequenas (Pato Branco 1961-2026 = 66 links) e links grandes demais em estados
#   grandes (Minas Gerais, 1 ano, ~1,8 milhão de linhas, tende a 503). Antes de mudar o painel, esta simulação
#   mede TODAS as opções que mudam o resultado, com o mesmo cálculo do painel 2026.10.4 (revisão 18h30), e
#   escolhe a melhor por uma regra escrita AQUI, antes de rodar.
#
# O QUE É TESTADO (um link por vez, salvo na E6; cada link é baixado inteiro e conferido)
#   E1  Tamanho: quantas linhas diárias um link aguenta. Escada no Paraná (histórico): 3 meses, 6 meses,
#       1 ano, 18 meses, 2 anos e 3 anos, 2 tentativas por degrau. Para depois de um degrau que falhar 2 vezes.
#   E2  Forma: o mesmo número de linhas com muitos dias e poucos pontos (Pato Branco, 1961-2025) contra poucos
#       dias e muitos pontos (Paraná, 6 meses). Diz se o limite depende só de linhas ou também de dias.
#   E3  Formatação dos números: a do painel (ponto, "18.40"), a antiga (vírgula, "18,40") e sem formatação
#       (número cru). Paraná, 3 meses, 2 tentativas de cada, alternadas.
#   E4  Juntar locais: 5 municípios em 1 arquivo (coluna Municipio) contra 5 arquivos separados.
#   E5  Mensal: escada no Paraná (10, 22, 44 e 65 anos num link) e Pato Branco 1961-2025 num link.
#   E6  Links ao mesmo tempo: 3 links médios com 1, 2 e 3 de cada vez (quantos dão 429 ou 503).
#   E7  Estado grande (Minas Gerais, 2025): 1 link; 3 links por período (quadrimestres); 3 links por pontos.
#
# REGRA DE DECISÃO (fixada antes de rodar; o script aplica sozinho no fim)
#   R1  Limite de linhas diárias por link, pela E1. Aprovado = abriu completo nas 2 tentativas (linhas = pontos
#       x dias, nenhum par ponto-dia repetido, colunas na ordem do painel). Se nenhum degrau falhar, o limite é
#       o maior aprovado. Se algum falhar, o limite é o volume que caberia em 70% do tempo em que o pedido
#       falhou (pela velocidade do maior aprovado), nunca abaixo do maior aprovado nem acima de 90% do degrau
#       que falhou.
#   R2  Forma: se a série longa (E2) gastar mais de 30% a mais por linha que a larga, os arquivos com mais de
#       1 ano contam as linhas multiplicadas por essa razão (fator de forma). Senão, fator 1.
#   R3  Formatação: a do painel (ponto) continua, a menos que o número cru seja pelo menos 25% mais rápido
#       nas 2 tentativas. A vírgula só volta se for pelo menos 25% mais rápida que o ponto.
#   R4  Juntar locais: sim, se o arquivo junto abrir nas 2 tentativas e levar no máximo 1,2 vez a soma dos
#       separados.
#   R5  Mensal: a mesma regra do R1, com a escada da E5 (em linhas mensais).
#   R6  Links ao mesmo tempo: o maior número sem nenhum 429 ou 503 e pelo menos 10% mais rápido que um por
#       vez. Senão, 1 (baixar um de cada vez).
#   R7  Ano grande demais para 1 link: dividir por PERÍODO (cada arquivo com todos os pontos), se abrir tudo
#       e levar no máximo 1,1 vez o tempo da divisão por pontos; senão, por PONTOS.
#   Anos inteiros nunca são partidos, a menos que 1 ano sozinho passe do limite (R7).
#
# NADA é criado, apagado ou exportado no Earth Engine; a sessão não fica travada.
# TEMPO: de 2 a 3 horas. Deixe a aba aberta. Se a célula parar, rode de novo: o que já foi medido é lido do
#   arquivo de progresso (no Google Drive, com USAR_DRIVE = True) e não é repetido.
# NO FIM: o Colab baixa simulacao_K13_<data>.zip (LOG_K13.txt, K13_testes.csv, K13_DECISOES.csv,
#   K13_PLANO.csv). Me envie o zip.
# =========================================================================================
import io
import json
import math
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import ee
import pandas as pd
import requests

# ------------------------------------------------------------------ parâmetros (não precisa mudar)
PROJETO = 'clima-492922'
SAB = f'projects/{PROJETO}/assets/SAB_V1'
MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
SOLO = f'projects/{PROJETO}/assets/SICSB_SOLO_2015_2025'
ETAPAS = ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7']   # para repetir só algumas, deixe só elas na lista
USAR_DRIVE = True                         # guarda o progresso no Drive (retoma se a célula parar)
ESCALA_AREA = 11132                       # CFG.escalaArea do painel
LIMITE_PONTOS_GRADE = 25000               # CFG.limitePontosGrade do painel
TIMEOUT_S = 1200                          # espera máxima por link
ESPERA_429_S = 60                         # fila cheia: espera e repete o mesmo link
TENTATIVAS_429 = 6
ESPERA_FALHA_S = 120                      # antes da 2ª tentativa de um link que falhou (503 ou sem resposta)
MARGEM_TEMPO = 0.70                       # R1 e R5: fração do tempo em que o pedido falhou
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]

PARANA = ['Parana', 'Paraná']
MINAS = ['Minas Gerais']
MUNICIPIOS = [['Pato Branco'], ['Francisco Beltrao', 'Francisco Beltrão'], ['Clevelandia', 'Clevelândia'],
              ['Coronel Vivida'], ['Mariopolis', 'Mariópolis']]

# Degraus da E1 (Paraná, diário, só histórico BR-DWGD): rótulo, início, fim (fim exclusivo)
ESCADA_DIARIA = [('3_meses', '2025-01-01', '2025-04-01'), ('6_meses', '2025-01-01', '2025-07-01'),
                 ('1_ano', '2025-01-01', '2026-01-01'), ('18_meses', '2024-07-01', '2026-01-01'),
                 ('2_anos', '2024-01-01', '2026-01-01'), ('3_anos', '2023-01-01', '2026-01-01')]
# Degraus da E5 (Paraná, mensal): rótulo, ano inicial, ano final
ESCADA_MENSAL = [('10_anos', 2016, 2025), ('22_anos', 2004, 2025), ('44_anos', 1982, 2025), ('65_anos', 1961, 2025)]

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
PASTA = os.path.join(BASE, f'simulacao_K13_{AGORA:%Y%m%d_%H%M}')
LOG = os.path.join(PASTA, 'LOG_K13.txt')
ARQ_TESTES = os.path.join(PASTA, 'K13_testes.csv')


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
# FUNÇÕES PURAS (sem Earth Engine; testadas offline em testes/teste_k13.py)
# =========================================================================================
def media(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def aprovado(tentativas):
    """Degrau aprovado: 2 tentativas, as 2 abriram completas."""
    return len(tentativas) >= 2 and all(t['ok'] for t in tentativas[:2])


def limite_da_escada(degraus, margem_tempo=MARGEM_TEMPO):
    """R1/R5. degraus: lista ordenada de (rótulo, linhas, [tentativas com 'ok' e 'segundos']).
    Devolve (maior degrau aprovado, limite de linhas por link).
    - Aprovado = abriu completo nas 2 tentativas. Um degrau que falhou nas 2 encerra a escada (sem buraco).
    - Sem nenhuma falha acima do maior aprovado: limite = maior aprovado (o que foi comprovado).
    - Com falha: estima as linhas que caberiam em 70% do tempo em que o pedido falhou, pela velocidade do
      maior aprovado; o limite fica entre o maior aprovado e 90% do degrau que falhou."""
    maior, seg_maior, falha_linhas, t_falha = None, None, None, None
    for _, linhas, tent in degraus:
        if not tent:
            break
        if aprovado(tent):
            maior, seg_maior = linhas, media([t['segundos'] for t in tent[:2]])
            continue
        if falha_linhas is None:
            falha_linhas = linhas
            t_falha = max((t.get('segundos') or 0) for t in tent if not t['ok']) or None
        if not any(t['ok'] for t in tent):
            break
    if maior is None:
        return None, None
    if falha_linhas is None or falha_linhas <= maior:
        return maior, maior
    lim = maior
    if t_falha and seg_maior:
        lim = margem_tempo * t_falha / (seg_maior / maior)
    lim = min(max(lim, maior), 0.9 * falha_linhas)
    return maior, int(lim // 1000 * 1000)


def fator_de_forma(seg_mil_longa, seg_mil_larga, limiar=1.3):
    """R2: razão de segundos por mil linhas (série longa / larga); 1 se não passar do limiar."""
    if not seg_mil_longa or not seg_mil_larga:
        return 1.0
    r = seg_mil_longa / seg_mil_larga
    return round(r, 2) if r > limiar else 1.0


def escolher_formato(tempos, ganho=0.25):
    """R3: tempos = {'ponto': [t, t], 'cru': [...], 'virgula': [...]} (None = falhou)."""
    def ok2(m):
        v = tempos.get(m) or []
        return len(v) >= 2 and all(x is not None for x in v[:2])
    if not ok2('ponto'):
        return 'ponto', 'o formato do painel não abriu nas 2 tentativas: nada a comparar'
    tp = media(tempos['ponto'])
    if ok2('cru') and media(tempos['cru']) <= (1 - ganho) * tp:
        return 'cru', f"número cru {media(tempos['cru']):.0f} s x ponto {tp:.0f} s (ganho de 25% ou mais)"
    if ok2('virgula') and media(tempos['virgula']) <= (1 - ganho) * tp:
        return 'virgula', f"vírgula {media(tempos['virgula']):.0f} s x ponto {tp:.0f} s (ganho de 25% ou mais)"
    return 'ponto', 'nenhuma alternativa ganhou 25% ou mais: mantém o ponto do painel'


def decidir_juntar(t_junto, ok_junto, t_separados, limiar=1.2):
    """R4: t_junto = tempos do arquivo junto (2 tentativas); t_separados = tempo de cada arquivo separado."""
    if not ok_junto or not t_separados or any(t is None for t in t_separados):
        return False
    return media(t_junto) <= limiar * sum(t_separados)


def escolher_simultaneos(rodadas, ganho=0.10):
    """R6: rodadas = {n: {'falhas': int, 'tempo_total': s}}; n = links ao mesmo tempo (1 = um por vez)."""
    base = rodadas.get(1)
    if not base or base['falhas']:
        return 1
    melhor = 1
    for n in sorted(k for k in rodadas if k > 1):
        r = rodadas[n]
        if r['falhas'] == 0 and r['tempo_total'] <= (1 - ganho) * base['tempo_total']:
            melhor = n
    return melhor


def escolher_divisao(periodo, pontos, limiar=1.1):
    """R7: periodo/pontos = {'ok': bool, 'tempo_total': s}. Devolve 'periodo', 'pontos' ou 'nenhuma'."""
    if periodo['ok'] and (not pontos['ok'] or periodo['tempo_total'] <= limiar * pontos['tempo_total']):
        return 'periodo'
    if pontos['ok']:
        return 'pontos'
    return 'nenhuma'


def dias_do_ano(ano):
    return (date(ano + 1, 1, 1) - date(ano, 1, 1)).days


MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']


def planejar_arquivos(n_pontos, anos, limite, fator=1.0, por_ano=None):
    """Plano de arquivos do painel: junta ANOS INTEIROS seguidos enquanto pontos x unidades (x fator, se o
    arquivo passar de 1 ano) couber no limite. Um ano só é dividido (em blocos de meses) se sozinho passar.
    anos: lista de (ano, unidades no ano) em ordem (dias no diário, meses no mensal).
    Devolve lista de (rótulo, linhas)."""
    plano, grupo, linhas_grupo = [], [], 0

    def fechar():
        nonlocal grupo, linhas_grupo
        if grupo:
            rot = str(grupo[0]) if len(grupo) == 1 else f'{grupo[0]}-{grupo[-1]}'
            plano.append((rot, linhas_grupo))
        grupo, linhas_grupo = [], 0

    for ano, unidades in anos:
        linhas = n_pontos * unidades
        if linhas > limite:                       # R7: o ano sozinho não cabe
            fechar()
            k = math.ceil(linhas / limite)
            k = next(d for d in (2, 3, 4, 6, 12) if d >= k) if k <= 12 else 12
            passo = 12 // k
            for i in range(k):
                m0, m1 = i * passo, (i + 1) * passo - 1
                plano.append((f'{ano} ({MESES[m0]}-{MESES[m1]})', math.ceil(linhas / k)))
            continue
        novo = linhas_grupo + linhas
        custo = novo * (fator if len(grupo) >= 1 else 1.0)
        if grupo and custo > limite:
            fechar()
        grupo.append(ano)
        linhas_grupo += linhas
    fechar()
    return plano


def links_hoje(n_locais, n_anos):
    """Painel atual: 1 dicionário + 1 link por local e por ano."""
    return 1 + n_locais * n_anos


# =========================================================================================
# EARTH ENGINE: o mesmo cálculo do painel
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


SAL = [0]


def baixar(rotulo, fc, colunas, esperado):
    """Gera o link como o painel (getDownloadURL), baixa e confere. Devolve um dicionário."""
    r0 = {'teste': rotulo, 'linhas_esperadas': esperado, 'resposta': '', 'segundos': None, 'MB': 0,
          'linhas': 0, 'repetidos': 0, 'esperas_429': 0, 'ok': False, 'detalhe': ''}
    try:
        url = fc.getDownloadURL(filetype='csv', selectors=colunas, filename=rotulo)
    except Exception as e:
        return dict(r0, resposta='erro ao gerar o link', detalhe=str(e)[:200])
    t1 = time.time()
    try:
        r = requests.get(url, timeout=TIMEOUT_S)
        esperas = 0
        while r.status_code == 429 and esperas < TENTATIVAS_429:
            esperas += 1
            time.sleep(ESPERA_429_S)
            t1 = time.time()
            r = requests.get(url, timeout=TIMEOUT_S)
        seg = round(time.time() - t1, 1)
        res = dict(r0, resposta=r.status_code, segundos=seg, MB=round(len(r.content) / 1e6, 2), esperas_429=esperas)
        if r.status_code != 200:
            return dict(res, detalhe=r.text.replace('\n', ' ')[:200])
        df = pd.read_csv(io.BytesIO(r.content), usecols=['N_Ponto', 'Data_Completa'], dtype=str)
        cab = r.content[:2000].split(b'\n', 1)[0].decode('utf-8', 'replace').strip().split(',')
        rep = int(df.duplicated().sum())
        completo = (len(df) == esperado) and rep == 0 and cab == colunas
        det = '' if completo else (f'linhas {len(df):,} de {esperado:,}; repetidos {rep}; '
                                   f'colunas {"ok" if cab == colunas else "fora de ordem"}')
        return dict(res, linhas=len(df), repetidos=rep, ok=completo, detalhe=det)
    except requests.exceptions.Timeout:
        return dict(r0, resposta=f'sem resposta em {TIMEOUT_S} s', segundos=TIMEOUT_S)
    except Exception as e:
        return dict(r0, resposta='erro na conexão', segundos=round(time.time() - t1, 1), detalhe=str(e)[:200])


# =========================================================================================
# EXECUÇÃO
# =========================================================================================
if __name__ == '__main__':
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log(f'🔎 K13: a melhor forma de dividir e baixar os CSV do painel | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log('   Só leitura: nada é criado, apagado ou exportado no Earth Engine. Um link por vez (salvo na E6).')
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    # ---------------------------------------------------------------- progresso (retomada)
    ARQ_PROG = os.path.join(BASE, 'K13_progresso.json')
    if USAR_DRIVE:
        try:
            from google.colab import drive
            drive.mount('/content/drive')
            os.makedirs('/content/drive/MyDrive/K13', exist_ok=True)
            ARQ_PROG = '/content/drive/MyDrive/K13/K13_progresso.json'
        except Exception as e:
            log(f'   ⚠️ Drive indisponível ({str(e)[:80]}); o progresso fica só nesta sessão.')
    feitos = {}
    if os.path.exists(ARQ_PROG):
        with open(ARQ_PROG, encoding='utf-8') as f:
            feitos = json.load(f)
        log(f'   ♻️ {len(feitos)} teste(s) já medidos lidos de {ARQ_PROG}: não serão repetidos.')

    todos = []
    TRAVA = threading.Lock()   # a E6 mede links em paralelo

    def medir(rotulo, fc_fn, colunas, esperado, etapa):
        """Mede um link (ou reaproveita o resultado guardado). fc_fn() monta o pedido."""
        if rotulo in feitos:
            res = feitos[rotulo]
            origem = '(guardado)'
        else:
            with TRAVA:
                SAL[0] += 1
                sal = SAL[0] + int(T0)
            res = baixar(rotulo, fc_fn(sal), colunas, esperado)
            res['quando'] = datetime.now(timezone(timedelta(hours=-3))).strftime('%H:%M')
            origem = ''
        with TRAVA:
            if not origem:
                feitos[rotulo] = res
                with open(ARQ_PROG, 'w', encoding='utf-8') as f:
                    json.dump(feitos, f, ensure_ascii=False)
            res = dict(res, etapa=etapa)
            todos.append(res)
            pd.DataFrame(todos).to_csv(ARQ_TESTES, sep=';', decimal=',', encoding='utf-8-sig', index=False)
        simb = '✅' if res['ok'] else '❌'
        seg = f"{res['segundos']} s" if res['segundos'] is not None else '-'
        log(f"   {simb} {rotulo}: resposta {res['resposta']} | {seg} | {res['MB']} MB | {res['linhas']:,} de "
            f"{esperado:,} linhas{(' | ' + res['detalhe']) if res['detalhe'] else ''}"
            f"{(' | ' + str(res['esperas_429']) + 'x 429') if res['esperas_429'] else ''} {origem}")
        return res

    def duas_tentativas(rotulo, fc_fn, colunas, esperado, etapa):
        """Tentativa 1 e 2 (a 2ª só depois de esperar, se a 1ª falhou). Devolve as duas."""
        t1 = medir(rotulo + '_t1', fc_fn, colunas, esperado, etapa)
        if not t1['ok'] and (rotulo + '_t2') not in feitos:
            time.sleep(ESPERA_FALHA_S)
        t2 = medir(rotulo + '_t2', fc_fn, colunas, esperado, etapa)
        return [t1, t2]

    def seg_mil(tent):
        v = [t['segundos'] / (t['linhas'] / 1000) for t in tent if t['ok'] and t['linhas']]
        return media(v)

    # ---------------------------------------------------------------- grades e contagens
    log('\n0) Grades (como o painel) e dias de cada período')
    pr_pol = poligonos_estado(PARANA, 'Parana')
    pr_grade = montar_grade(pr_pol)
    n_pr = pr_grade.size().getInfo()
    mun_pol = poligonos_municipios(PARANA, MUNICIPIOS)
    nomes_mun = mun_pol.aggregate_array('Nome_Local_Export').distinct().getInfo()
    mun_grade = montar_grade(mun_pol)
    n_mun = mun_grade.size().getInfo()
    pb_pol = mun_pol.filter(ee.Filter.eq('Nome_Local_Export', 'Pato Branco'))
    pb_grade = montar_grade(pb_pol)
    n_pb = pb_grade.size().getInfo()
    log(f'   Paraná: {n_pr} pontos | Pato Branco: {n_pb} pontos | {len(nomes_mun)} municípios {nomes_mun}: {n_mun} pontos')
    if not n_pr or not n_pb:
        log('   ❌ Paraná ou Pato Branco sem pontos (nome não achado no GAUL): me envie o LOG.')
        raise SystemExit(1)
    if len(nomes_mun) < 3:
        log('   ⚠️ Menos de 3 municípios achados no GAUL: a E4 fica com os que foram achados.')
    geom_pr = pr_pol.geometry()

    cache_dias = {}

    def n_dias(geom, ini, fim, chave):
        if chave not in cache_dias:
            cache_dias[chave] = colecao(geom, ini, fim).size().getInfo()
        return cache_dias[chave]

    def pedido_diario(grade, geom, ini, fim, modo='ponto'):
        return lambda sal: formatar(linhas_diarias(colecao(geom, ini, fim), grade), modo, EXTRAS_DIARIA, sal)

    def pedido_mensal(grade, geom, a0, a1):
        return lambda sal: formatar(linhas_mensais(colecao(geom, f'{a0}-01-01', f'{a1 + 1}-01-01'), grade, a0, a1),
                                    'ponto', EXTRAS_MENSAL, sal)

    # ---------------------------------------------------------------- E1
    escada_d = []
    if 'E1' in ETAPAS:
        log('\n1) E1: quantas linhas diárias um link aguenta (Paraná, histórico, formato do painel)')
        parar = False
        for rot, ini, fim in ESCADA_DIARIA:
            nd = n_dias(geom_pr, ini, fim, f'pr_{ini}_{fim}')
            esperado = n_pr * nd
            if parar:
                escada_d.append((rot, esperado, []))
                continue
            tent = duas_tentativas(f'E1_{rot}', pedido_diario(pr_grade, geom_pr, ini, fim), COLUNAS_DIARIA,
                                   esperado, 'E1')
            escada_d.append((rot, esperado, tent))
            if not any(t['ok'] for t in tent):
                log('   ➜ degrau falhou nas 2 tentativas: os maiores não são testados.')
                parar = True
    maior_d, limite_d = limite_da_escada(escada_d)

    # ---------------------------------------------------------------- E2
    fator = 1.0
    if 'E2' in ETAPAS:
        log('\n2) E2: o mesmo volume em forma longa (muitos dias) e larga (muitos pontos)')
        nd_pb = n_dias(geom_pr, '1961-01-01', '2026-01-01', 'pb_1961_2025')
        longa = duas_tentativas('E2_longa_PatoBranco_1961_2025', pedido_diario(pb_grade, pb_pol.geometry(),
                                '1961-01-01', '2026-01-01'), COLUNAS_DIARIA, n_pb * nd_pb, 'E2')
        larga = next((t for r, _, t in escada_d if r == '6_meses' and t), None)
        if larga is None:
            nd6 = n_dias(geom_pr, '2025-01-01', '2025-07-01', 'pr_2025-01-01_2025-07-01')
            larga = duas_tentativas('E1_6_meses', pedido_diario(pr_grade, geom_pr, '2025-01-01', '2025-07-01'),
                                    COLUNAS_DIARIA, n_pr * nd6, 'E2')
        sl, sw = seg_mil(longa), seg_mil(larga)
        fator = fator_de_forma(sl, sw)
        log(f"   segundos por mil linhas: longa {sl if sl is None else round(sl, 3)} x larga "
            f"{sw if sw is None else round(sw, 3)} ➜ fator de forma {fator}")

    # ---------------------------------------------------------------- E3
    formato, motivo_formato = 'ponto', 'E3 não rodada'
    if 'E3' in ETAPAS:
        log('\n3) E3: formatação dos números (Paraná, 3 meses; tentativas alternadas)')
        nd3 = n_dias(geom_pr, '2025-01-01', '2025-04-01', 'pr_2025-01-01_2025-04-01')
        tempos = {'ponto': [], 'virgula': [], 'cru': []}
        for k in (1, 2):
            for modo in ('ponto', 'virgula', 'cru'):
                r = medir(f'E3_{modo}_t{k}', pedido_diario(pr_grade, geom_pr, '2025-01-01', '2025-04-01', modo),
                          COLUNAS_DIARIA, n_pr * nd3, 'E3')
                tempos[modo].append(r['segundos'] if r['ok'] else None)
        formato, motivo_formato = escolher_formato(tempos)
        log(f'   ➜ formato: {formato} ({motivo_formato})')

    # ---------------------------------------------------------------- E4
    juntar = None
    if 'E4' in ETAPAS:
        log(f'\n4) E4: {len(nomes_mun)} municípios num arquivo x um arquivo por município (2016-2025, diário)')
        nd10 = n_dias(geom_pr, '2016-01-01', '2026-01-01', 'pr_2016_2025')
        junto = duas_tentativas('E4_juntos', pedido_diario(mun_grade, mun_pol.geometry(), '2016-01-01', '2026-01-01'),
                                COLUNAS_DIARIA, n_mun * nd10, 'E4')
        separados = []
        for nome in nomes_mun:
            pol = mun_pol.filter(ee.Filter.eq('Nome_Local_Export', nome))
            g = montar_grade(pol)
            n_g = g.size().getInfo()
            r = medir(f'E4_separado_{nome.replace(" ", "_")}', pedido_diario(g, pol.geometry(), '2016-01-01',
                      '2026-01-01'), COLUNAS_DIARIA, n_g * nd10, 'E4')
            separados.append(r['segundos'] if r['ok'] else None)
        juntar = decidir_juntar([t['segundos'] for t in junto if t['ok']], aprovado(junto), separados)
        log(f"   junto {media([t['segundos'] for t in junto if t['ok']])} s x soma dos separados "
            f"{sum(x for x in separados if x) if all(separados) else 'algum falhou'} s ➜ juntar: {'sim' if juntar else 'não'}")

    # ---------------------------------------------------------------- E5
    escada_m = []
    if 'E5' in ETAPAS:
        log('\n5) E5: mensal (Paraná, escada de anos num link; Pato Branco 1961-2025 num link)')
        parar = False
        for rot, a0, a1 in ESCADA_MENSAL:
            esperado = n_pr * (a1 - a0 + 1) * 12
            if parar:
                escada_m.append((rot, esperado, []))
                continue
            tent = duas_tentativas(f'E5_{rot}', pedido_mensal(pr_grade, geom_pr, a0, a1), COLUNAS_MENSAL, esperado, 'E5')
            escada_m.append((rot, esperado, tent))
            if not any(t['ok'] for t in tent):
                log('   ➜ degrau falhou nas 2 tentativas: os maiores não são testados.')
                parar = True
        duas_tentativas('E5_PatoBranco_1961_2025', pedido_mensal(pb_grade, pb_pol.geometry(), 1961, 2025),
                        COLUNAS_MENSAL, n_pb * 65 * 12, 'E5')
    maior_m, limite_m = limite_da_escada(escada_m)

    # ---------------------------------------------------------------- E6
    simult = 1
    if 'E6' in ETAPAS:
        log('\n6) E6: links ao mesmo tempo (3 links de 3 meses do Paraná; 1, 2 e 3 de cada vez)')
        trimestres = [('2024-01-01', '2024-04-01'), ('2024-04-01', '2024-07-01'), ('2024-07-01', '2024-10-01')]
        rodadas = {}
        for n in (1, 2, 3):
            pend = []
            for j, (ini, fim) in enumerate(trimestres):
                nd = n_dias(geom_pr, ini, fim, f'pr_{ini}_{fim}')
                pend.append((f'E6_{n}_de_cada_vez_link{j + 1}', pedido_diario(pr_grade, geom_pr, ini, fim), n_pr * nd))
            ja = all(rot in feitos for rot, _, _ in pend)
            t_ini = time.time()
            with ThreadPoolExecutor(max_workers=n) as ex:
                res = list(ex.map(lambda p: medir(p[0], p[1], COLUNAS_DIARIA, p[2], 'E6'), pend))
            parede = round(time.time() - t_ini, 1)
            chave_tempo = f'E6_{n}_tempo_total'
            if ja and chave_tempo in feitos:
                parede = feitos[chave_tempo]
            else:
                feitos[chave_tempo] = parede
                with open(ARQ_PROG, 'w', encoding='utf-8') as f:
                    json.dump(feitos, f, ensure_ascii=False)
            falhas = sum(1 for r in res if not r['ok']) + sum(r['esperas_429'] for r in res)
            rodadas[n] = {'falhas': falhas, 'tempo_total': parede}
            log(f'   {n} de cada vez: tempo total {parede} s | falhas ou 429: {falhas}')
        simult = escolher_simultaneos(rodadas)
        log(f'   ➜ links ao mesmo tempo: {simult}')

    # ---------------------------------------------------------------- E7
    divisao, n_mg = None, None
    if 'E7' in ETAPAS:
        log('\n7) E7: estado grande (Minas Gerais, 2025, diário)')
        mg_pol = poligonos_estado(MINAS, 'Minas_Gerais')
        mg_grade = montar_grade(mg_pol)
        n_mg = mg_grade.size().getInfo()
        geom_mg = mg_pol.geometry()
        nd_mg = n_dias(geom_mg, '2025-01-01', '2026-01-01', 'mg_2025')
        log(f'   Minas Gerais: {n_mg} pontos x {nd_mg} dias = {n_mg * nd_mg:,} linhas')
        medir('E7_1_link', pedido_diario(mg_grade, geom_mg, '2025-01-01', '2026-01-01'), COLUNAS_DIARIA,
              n_mg * nd_mg, 'E7')
        quad = [('2025-01-01', '2025-05-01'), ('2025-05-01', '2025-09-01'), ('2025-09-01', '2026-01-01')]
        rp = [medir(f'E7_periodo_{k + 1}de3', pedido_diario(mg_grade, geom_mg, a, b), COLUNAS_DIARIA,
                    n_mg * n_dias(geom_mg, a, b, f'mg_{a}_{b}'), 'E7') for k, (a, b) in enumerate(quad)]
        lista_mg = mg_grade.toList(LIMITE_PONTOS_GRADE)
        cortes = [0, n_mg // 3, 2 * n_mg // 3, n_mg]
        rq = []
        for k in range(3):
            sub = ee.FeatureCollection(lista_mg.slice(cortes[k], cortes[k + 1]))
            rq.append(medir(f'E7_pontos_{k + 1}de3', pedido_diario(sub, geom_mg, '2025-01-01', '2026-01-01'),
                            COLUNAS_DIARIA, (cortes[k + 1] - cortes[k]) * nd_mg, 'E7'))
        per = {'ok': all(r['ok'] for r in rp), 'tempo_total': sum(r['segundos'] or 0 for r in rp)}
        pts = {'ok': all(r['ok'] for r in rq), 'tempo_total': sum(r['segundos'] or 0 for r in rq)}
        divisao = escolher_divisao(per, pts)
        log(f"   período: {'abriu tudo' if per['ok'] else 'falhou'} em {per['tempo_total']:.0f} s | pontos: "
            f"{'abriu tudo' if pts['ok'] else 'falhou'} em {pts['tempo_total']:.0f} s ➜ dividir por: {divisao}")

    # ---------------------------------------------------------------- resultado
    log('\n' + '=' * 100)
    log('RESULTADO FINAL K13: A MELHOR CONFIGURAÇÃO PELA REGRA FIXADA ANTES DE RODAR')
    log('=' * 100)
    dec = [
        ('R1 limite de linhas diárias por link', f'{limite_d:,}' if limite_d else 'não definido',
         f'maior degrau aprovado: {maior_d:,} linhas' if maior_d else 'nenhum degrau aprovado nas 2 tentativas'),
        ('R2 fator de forma (arquivos com mais de 1 ano)', fator, 'razão de segundos por mil linhas, longa / larga'),
        ('R3 formato dos números', formato, motivo_formato),
        ('R4 juntar municípios num arquivo', {True: 'sim', False: 'não', None: 'E4 não rodada'}[juntar], ''),
        ('R5 limite de linhas mensais por link', f'{limite_m:,}' if limite_m else 'não definido',
         f'maior degrau aprovado: {maior_m:,} linhas' if maior_m else 'nenhum degrau aprovado'),
        ('R6 links ao mesmo tempo', simult, '1 = baixar um de cada vez'),
        ('R7 ano grande demais: dividir por', divisao or 'E7 não rodada', 'período = cada arquivo com todos os pontos'),
    ]
    tdec = pd.DataFrame(dec, columns=['decisao', 'resultado', 'base'])
    tdec.to_csv(os.path.join(PASTA, 'K13_DECISOES.csv'), sep=';', encoding='utf-8-sig', index=False)
    tabela(tdec.set_index('decisao'), 'Decisões:')

    plano = []
    if limite_d:
        anos_hist = [(a, dias_do_ano(a)) for a in range(1961, 2026)] + [(2026, (date(2026, 11, 15) - date(2026, 1, 1)).days)]
        casos = [('Pato Branco, diário, 1961-2026', n_pb, anos_hist, 1, limite_d),
                 (f'{len(nomes_mun)} municípios, diário, 2016-2025', n_mun if juntar else round(n_mun / max(1, len(nomes_mun))),
                  [(a, dias_do_ano(a)) for a in range(2016, 2026)], 1 if juntar else len(nomes_mun), limite_d),
                 ('Paraná, diário, 2024-2026', n_pr, [(2024, 366), (2025, 365), anos_hist[-1]], 1, limite_d)]
        if n_mg:
            casos.append(('Minas Gerais, diário, 2025', n_mg, [(2025, 365)], 1, limite_d))
        if limite_m:
            casos += [('Pato Branco, mensal, 1961-2026', n_pb, [(a, 12) for a in range(1961, 2027)], 1, limite_m),
                      ('Paraná, mensal, 1961-2026', n_pr, [(a, 12) for a in range(1961, 2027)], 1, limite_m)]
        for nome, npts, anos, n_arq_locais, lim in casos:
            p = planejar_arquivos(npts, anos, lim, fator if 'diário' in nome else 1.0)
            locais_hoje = len(nomes_mun) if 'municípios' in nome else 1
            plano.append({'pedido': nome, 'links_hoje': links_hoje(locais_hoje, len(anos)),
                          'links_proposta': 1 + len(p) * n_arq_locais,
                          'arquivos': ' | '.join(f'{r} ({l:,} linhas)' for r, l in p)})
        tplano = pd.DataFrame(plano)
        tplano.to_csv(os.path.join(PASTA, 'K13_PLANO.csv'), sep=';', encoding='utf-8-sig', index=False)
        tabela(tplano.set_index('pedido')[['links_hoje', 'links_proposta']], 'Links por pedido (contando o dicionário):')
        for r in plano:
            log(f"   {r['pedido']}: {r['arquivos']}")
    else:
        log('   ❌ Sem limite diário definido (E1 não aprovou nenhum degrau): me envie o zip.')

    log(f'\nTempo total: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine.')
    z = shutil.make_archive(PASTA, 'zip', PASTA)
    log(f'📦 {z}')
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        log('   (baixe pelo painel Arquivos do Colab)')
