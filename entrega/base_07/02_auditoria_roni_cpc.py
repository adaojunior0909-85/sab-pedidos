# =========================================================================
# AUDITORIA CIENTÍFICA DO RONI + GERAÇÃO DO ASSET OFICIAL (1950 até hoje)
# ASSET ANTIGO x TABELA OFICIAL CPC (ERSSTv6) x RÉPLICA SAB (OISST)
#
# MUDANÇAS V4 (20/10/2026)
#   [V4 M02-01] Gravação sem janela e sem perder o compartilhamento: o asset atual vira
#               RONI_CPC_v6_ANTERIOR, o _TMP é promovido e a ACL anterior (sem 'owners') é
#               reaplicada e impressa. Se não der, um aviso ⚠️ pede o compartilhamento à mão
#   [V4 M02-02] Estações novas do arquivo do CPC entram sozinhas, arredondadas do arquivo, fora
#               dos empates (2ª casa decimal 5). Num empate a execução para e diz qual valor
#               digitar. Revisão do CPC nas 3 últimas estações da tabela vale com aviso ⚠️. No
#               fim sai a linha do ano já atualizada, no formato da tabela, para quem quiser colar
#   [V4 M02-03] O asset gravado é lido de volta e comparado com a série oficial (estações, RONI,
#               Trimestre, mês central, system:time_start, chave_join). Se bater, o _ANTERIOR é
#               apagado; se não, ele volta para o lugar e a execução para com ❌. Propriedade
#               nova em texto: chave_join = 'AAAA_MM'
#   [V4 revisão B-03] Se sobrou RONI_CPC_v6_ANTERIOR sem o asset principal (restauração anterior que
#               falhou), ele volta ao lugar antes da troca; antes era apagado e o RONI podia sumir
#   [V4 revisão B-10] A contagem do asset gravado fica dentro da conferência; se a restauração falhar,
#               a mensagem manda apagar o asset ruim antes de renomear o _ANTERIOR
#
# O QUE ESTE CÓDIGO FAZ
#   1. Confere a tabela oficial do RONI digitada abaixo contra o arquivo do CPC
#      (RONI.ascii.txt, 2 casas decimais). [V4 M02-02] Estações que o CPC já publicou e a
#      tabela ainda não tem entram sozinhas; só um empate na 2ª casa decimal ou um erro de
#      digitação faz a execução parar e dizer o que corrigir.
#   2. Recalcula o RONI com o OISST (réplica SAB) só para auditoria.
#   3. Compara asset antigo, tabela oficial e réplica SAB, ano a ano.
#   4. Grava o asset RONI_CPC_v6, só com a série OFICIAL, que o Painel SAB usa.
#
# CORREÇÕES EM RELAÇÃO À VERSÃO ANTERIOR
#   - Retângulos planos (geodesic=False): o retângulo tropical geodésico de
#     -179,99 a 179,99 virava uma tira na linha de data
#   - Média de TSM ponderada pela área do pixel, na grade nativa do OISST
#   - Só meses completos entram; dias provisórios do OISST ficam marcados
#   - Falha de extração interrompe a execução (antes um ano sumia em silêncio)
#   - Série mensal contínua (lacuna vira vazio, nunca junta meses distantes)
#   - Média móvel centrada e rótulo pelo mês central (DJF = janeiro), igual ao painel
#   - Arredondamento "meio para longe do zero", igual ao Earth Engine
#   - Estatísticas com viés, concordância de sinal e de fase (episódios)
#   - O asset gravado contém só a série oficial do CPC (antes o OISST substituía
#     45 anos de valores oficiais)
#
# ROTINA MENSAL [V4 M02-02]: depois do dia 5 de cada mês, rode de novo, sem editar. As
# estações novas do arquivo do CPC entram sozinhas. A execução só para num empate (2ª casa
# decimal 5 no arquivo): aí digite na tabela abaixo o valor da tabela ERSSTv6 de
# https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/ e rode de novo. Revisões
# do CPC nas 3 últimas estações da tabela são aceitas com aviso ⚠️ (o CPC pode alterá-las).
# =========================================================================

import ee
import io
import json
import time
from datetime import datetime

import numpy as np
import pandas as pd

# =========================================================================
# 0. CONFIGURAÇÃO
# =========================================================================
PROJECT_ID = 'clima-492922'
ASSET_ANTIGO = 'projects/clima-492922/assets/RONI_Calibrado_Sazonal_1950_1980'
ASSET_RONI = 'projects/clima-492922/assets/RONI_CPC_v6'
URL_ASCII = 'https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt'
GRAVAR_ASSET = True      # False: só audita, não grava nada no Earth Engine
URL_TABELA_CPC = 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/'   # [V4 M02-02]
AUTO_ESTACOES_NOVAS = True   # [V4 M02-02] False: volta a parar diante de qualquer estação nova do CPC
ESTACOES_REVISAVEIS = 3      # [V4 M02-02] últimas estações da tabela que o CPC ainda pode revisar
ORDEM = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']

# Tabela oficial do CPC (ERSSTv6), uma casa decimal. É a referência para classificar fases.
noaa_data = """Year DJF JFM FMA MAM AMJ MJJ JJA JAS ASO SON OND NDJ
1950 -1.2 -1.1 -1.0 -1.0 -1.0 -0.7 -0.4 -0.3 -0.3 -0.4 -0.4 -0.5
1951 -0.3 0.1 0.5 0.6 0.6 0.7 0.8 1.0 1.0 1.0 0.9 0.7
1952 0.7 0.3 0.5 0.2 0.0 -0.4 -0.4 -0.1 0.1 0.0 -0.1 0.1
1953 0.4 0.7 0.7 0.7 0.9 0.8 0.7 0.7 0.7 0.8 0.6 0.7
1954 0.6 0.6 0.3 0.0 -0.2 -0.2 -0.4 -0.6 -0.5 -0.3 -0.1 -0.2
1955 -0.1 -0.1 -0.1 -0.4 -0.4 -0.5 -0.4 -0.7 -0.9 -1.3 -1.4 -1.3
1956 -0.8 -0.4 -0.1 -0.1 0.0 0.0 -0.1 -0.2 -0.1 -0.1 -0.1 -0.2
1957 0.0 0.2 0.5 0.8 0.9 0.9 1.0 1.1 1.1 1.2 1.5 1.8
1958 1.9 1.8 1.3 1.0 0.7 0.6 0.5 0.3 0.2 0.2 0.4 0.6
1959 0.8 0.8 0.6 0.5 0.3 0.1 -0.1 -0.2 -0.1 0.0 0.2 0.2
1960 0.2 0.2 0.2 0.3 0.2 0.1 0.1 0.2 0.3 0.1 -0.1 -0.1
1961 0.0 0.1 0.0 0.1 0.2 0.3 0.2 -0.1 -0.2 -0.2 -0.1 0.0
1962 0.0 0.0 0.0 -0.2 -0.2 -0.1 0.0 -0.1 -0.1 -0.3 -0.3 -0.4
1963 -0.3 -0.1 0.0 0.1 0.0 0.4 0.7 1.1 1.1 1.1 1.1 1.1
1964 1.0 0.6 0.1 -0.4 -0.7 -0.7 -0.6 -0.5 -0.5 -0.6 -0.6 -0.5
1965 -0.2 0.1 0.2 0.4 0.6 1.0 1.3 1.5 1.8 1.9 2.0 1.8
1966 1.5 1.3 1.0 0.6 0.3 0.2 0.3 0.2 0.0 0.0 -0.1 -0.2
1967 -0.3 -0.2 -0.3 -0.3 -0.1 0.2 0.2 0.0 -0.1 -0.1 0.0 0.0
1968 -0.2 -0.4 -0.3 -0.3 0.1 0.3 0.6 0.5 0.4 0.6 0.7 1.0
1969 1.1 1.0 0.7 0.4 0.4 0.3 0.3 0.3 0.6 0.7 0.8 0.7
1970 0.5 0.2 0.2 0.2 0.1 -0.2 -0.5 -0.6 -0.5 -0.6 -0.5 -0.8
1971 -0.9 -1.0 -0.8 -0.6 -0.5 -0.4 -0.3 -0.2 -0.3 -0.4 -0.4 -0.4
1972 -0.2 0.0 0.3 0.5 0.7 0.9 1.1 1.4 1.6 1.8 2.0 1.9
1973 1.7 1.3 0.6 -0.2 -0.7 -1.0 -1.1 -1.2 -1.3 -1.6 -1.9 -1.9
1974 -1.6 -1.3 -1.0 -0.8 -0.6 -0.5 -0.3 -0.2 -0.2 -0.4 -0.6 -0.3
1975 -0.1 -0.1 -0.3 -0.4 -0.6 -0.7 -0.9 -0.9 -1.0 -0.9 -1.0 -1.1
1976 -1.0 -0.6 -0.3 -0.1 0.0 0.3 0.5 0.7 0.9 1.0 1.1 1.1
1977 1.0 0.9 0.5 0.3 0.3 0.5 0.5 0.5 0.6 0.9 1.1 1.1
1978 1.0 0.7 0.3 -0.1 -0.3 -0.2 -0.3 -0.3 -0.3 -0.1 0.2 0.3
1979 0.3 0.3 0.3 0.2 0.1 0.0 0.0 0.3 0.4 0.5 0.5 0.6
1980 0.7 0.5 0.3 0.1 0.3 0.3 0.1 -0.1 -0.2 -0.1 0.1 0.1
1981 0.0 -0.2 -0.3 -0.2 -0.3 -0.3 -0.2 -0.2 0.0 -0.2 -0.2 -0.1
1982 0.1 0.2 0.2 0.5 0.7 0.8 0.9 1.1 1.6 2.0 2.2 2.4
1983 2.4 2.2 1.7 1.3 0.9 0.5 0.0 -0.2 -0.6 -0.9 -1.1 -1.0
1984 -0.6 -0.5 -0.5 -0.6 -0.6 -0.5 -0.3 -0.2 -0.3 -0.6 -0.9 -0.9
1985 -0.8 -0.7 -0.7 -0.8 -0.8 -0.5 -0.3 -0.2 -0.2 -0.2 -0.1 -0.2
1986 -0.3 -0.3 -0.2 -0.1 -0.1 0.0 0.3 0.6 0.8 1.0 1.2 1.4
1987 1.5 1.4 1.1 0.9 0.8 0.9 1.1 1.3 1.3 1.2 1.0 0.8
1988 0.5 0.1 -0.4 -0.9 -1.5 -1.7 -1.6 -1.4 -1.4 -1.7 -1.9 -1.9
1989 -1.6 -1.4 -1.1 -0.9 -0.6 -0.4 -0.4 -0.4 -0.3 -0.2 -0.1 0.1
1990 0.3 0.3 0.3 0.3 0.2 0.2 0.2 0.3 0.3 0.3 0.3 0.4
1991 0.6 0.5 0.4 0.4 0.6 0.7 0.9 0.8 1.0 1.2 1.7 2.0
1992 2.1 2.1 1.9 1.8 1.4 0.9 0.5 0.3 0.1 0.1 0.1 0.4
1993 0.6 0.7 0.9 1.1 1.0 0.8 0.5 0.5 0.5 0.5 0.4 0.4
1994 0.3 0.2 0.2 0.3 0.4 0.4 0.5 0.6 0.8 1.0 1.2 1.3
1995 1.2 0.9 0.6 0.2 -0.1 -0.2 -0.4 -0.6 -0.8 -0.9 -1.0 -1.0
1996 -0.9 -0.7 -0.6 -0.4 -0.2 -0.2 -0.2 -0.2 -0.2 -0.2 -0.3 -0.3
1997 -0.2 0.0 0.2 0.5 0.8 1.2 1.5 1.8 2.1 2.2 2.3 2.3
1998 2.1 1.8 1.2 0.8 0.1 -0.5 -1.0 -1.1 -1.2 -1.3 -1.5 -1.6
1999 -1.6 -1.3 -1.0 -0.9 -0.8 -0.8 -0.8 -0.9 -0.9 -1.1 -1.3 -1.6
2000 -1.5 -1.3 -1.1 -0.9 -0.7 -0.5 -0.3 -0.3 -0.4 -0.5 -0.8 -0.8
2001 -0.8 -0.6 -0.5 -0.4 -0.3 -0.1 0.0 0.0 0.0 -0.2 -0.3 -0.3
2002 -0.2 0.0 0.0 0.1 0.2 0.4 0.6 0.8 1.0 1.2 1.3 1.1
2003 0.9 0.5 0.2 -0.2 -0.3 -0.2 0.0 0.1 0.2 0.2 0.3 0.2
2004 0.2 0.1 0.1 0.1 0.2 0.4 0.5 0.7 0.7 0.7 0.7 0.7
2005 0.5 0.4 0.3 0.3 0.2 0.1 -0.1 -0.1 0.0 -0.2 -0.5 -0.8
2006 -0.9 -0.9 -0.7 -0.5 -0.2 0.0 0.1 0.4 0.6 0.7 0.9 0.9
2007 0.6 0.2 -0.1 -0.3 -0.4 -0.4 -0.5 -0.8 -1.0 -1.3 -1.5 -1.6
2008 -1.7 -1.6 -1.4 -1.0 -0.8 -0.5 -0.2 -0.2 -0.3 -0.4 -0.6 -0.9
2009 -1.0 -0.9 -0.7 -0.4 0.0 0.2 0.4 0.4 0.5 0.9 1.3 1.5
2010 1.4 1.1 0.7 0.1 -0.5 -1.0 -1.2 -1.4 -1.5 -1.6 -1.6 -1.5
2011 -1.4 -1.2 -1.0 -0.8 -0.5 -0.3 -0.3 -0.4 -0.7 -0.9 -1.0 -1.0
2012 -0.8 -0.6 -0.5 -0.4 -0.3 0.0 0.3 0.4 0.4 0.2 0.0 -0.3
2013 -0.5 -0.6 -0.5 -0.4 -0.5 -0.5 -0.5 -0.4 -0.4 -0.2 -0.2 -0.3
2014 -0.4 -0.4 -0.1 0.1 0.2 0.0 -0.1 -0.1 0.1 0.4 0.5 0.6
2015 0.5 0.5 0.6 0.7 0.9 1.0 1.3 1.5 1.8 2.0 2.2 2.3
2016 2.1 1.8 1.3 0.7 0.1 -0.4 -0.7 -0.8 -0.9 -1.0 -1.0 -0.9
2017 -0.6 -0.4 -0.2 -0.1 0.0 0.0 -0.2 -0.5 -0.6 -0.8 -1.0 -1.1
2018 -1.1 -1.0 -0.9 -0.7 -0.3 0.0 0.1 0.2 0.4 0.6 0.8 0.8
2019 0.7 0.6 0.6 0.5 0.4 0.2 0.0 -0.1 0.0 0.2 0.3 0.2
2020 0.1 0.1 0.0 -0.3 -0.5 -0.7 -0.8 -0.8 -1.2 -1.4 -1.5 -1.4
2021 -1.3 -1.2 -1.1 -0.9 -0.7 -0.6 -0.6 -0.8 -0.9 -1.1 -1.2 -1.2
2022 -1.2 -1.1 -1.2 -1.3 -1.2 -0.9 -0.9 -0.9 -1.1 -1.1 -1.1 -1.0
2023 -0.9 -0.7 -0.5 -0.3 0.0 0.3 0.5 0.8 1.0 1.3 1.4 1.4
2024 1.1 0.8 0.4 0.0 -0.3 -0.4 -0.5 -0.6 -0.7 -0.8 -0.9 -1.0
2025 -1.1 -0.8 -0.7 -0.5 -0.5 -0.4 -0.4 -0.6 -0.8 -0.9 -1.0 -1.0
2026 -0.9 -0.8 -0.4 0.0 0.5 1.0 1.4 1.7 NaN NaN NaN NaN"""

# =========================================================================
# 1. AUTENTICAÇÃO
# =========================================================================
print("⏳ PASSO 1: Autenticando no Earth Engine...")
try:
    ee.Initialize(project=PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)
print("✅ Autenticado com sucesso!\n")

# [Correção 20/10/2026, 23h30] Trava de somente leitura herdada de outro script na MESMA sessão do Colab: os scripts
# de simulação e de auditoria (01a, 07, 08 e as validações) bloqueiam as funções de escrita do Earth Engine, e o
# bloqueio continua valendo nas células seguintes da sessão. Um script que grava precisa de uma sessão nova.
def _escrita_bloqueada_na_sessao():
    _funcs = [getattr(ee.batch.Task, 'start', None)] + [getattr(ee.data, _n, None) for _n in (
        'createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'setAssetAcl', 'startProcessing', 'exportImage')]
    return any(getattr(_f, '__name__', '') in ('_bloqueado', '_bloq') for _f in _funcs)


MSG_SESSAO_TRAVADA = ('Esta sessão do Colab ainda tem a trava de somente leitura de um script rodado antes nela '
                      '(por exemplo, o 01a, o 07 ou o 08). Nada foi gravado. No menu do Colab, clique em '
                      '"Ambiente de execução" e depois em "Reiniciar sessão" (confirme), e rode este arquivo de novo.')

if GRAVAR_ASSET and _escrita_bloqueada_na_sessao():
    raise RuntimeError('❌ ' + MSG_SESSAO_TRAVADA)

# =========================================================================
# 2. GEOMETRIAS (PLANAS) E TESTE DE ÁREA
# =========================================================================
nino34 = ee.Geometry.Rectangle([-170, -5, -120, 5], proj=None, geodesic=False)
tropics = ee.Geometry.Rectangle([-180, -20, 180, 20], proj=None, geodesic=False)

area_n34 = nino34.area(maxError=1).getInfo() / 1e6
area_trop = tropics.area(maxError=1).getInfo() / 1e6
print(f"📐 Área Niño 3.4: {area_n34:,.0f} km² (esperado ~6,17 milhões)")
print(f"📐 Área trópicos 20S-20N: {area_trop:,.0f} km² (esperado ~174 milhões)")
if not (5.5e6 < area_n34 < 6.9e6 and 1.6e8 < area_trop < 1.9e8):
    raise RuntimeError("Área das geometrias fora do esperado; confira os retângulos antes de continuar.")
print()

# =========================================================================
# 3. EXTRAÇÃO MENSAL DO OISST (SÓ MESES COMPLETOS, MÉDIA PONDERADA POR ÁREA)
# =========================================================================
print("⏳ PASSO 3: Extraindo TSM mensal do OISST (1981 até o último mês completo)...")
oisst = ee.ImageCollection('NOAA/CDR/OISST/V2_1').select('sst')
proj_oisst = ee.ImageCollection('NOAA/CDR/OISST/V2_1').first().projection()
area_px = ee.Image.pixelArea()
print(f"   Grade nativa do OISST: {proj_oisst.nominalScale().getInfo():,.0f} m")


def media_area(img, geom):
    """Média de TSM ponderada pela área real de cada pixel, na grade nativa do OISST."""
    num = img.multiply(area_px).rename('num')
    den = img.mask().multiply(area_px).rename('den')   # só a área de oceano
    r = ee.Image.cat([num, den]).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=geom, crs=proj_oisst, maxPixels=1e10, tileScale=4)
    return ee.Number(r.get('num')).divide(r.get('den'))


def fazer_calc_mes(ano):
    def calc_mes(m):
        d = ee.Date.fromYMD(ano, m, 1)
        col = oisst.filterDate(d, d.advance(1, 'month'))
        n_dias = col.aggregate_array('system:time_start').distinct().size()
        ok = n_dias.gt(0)
        img = col.mean().multiply(0.01)   # fator de escala 0,01 da banda sst
        return ee.Feature(None, {
            'ano': ano, 'mes': m,
            'n_imgs': col.size(),
            'n_dias': n_dias,
            'n_perm': col.filter(ee.Filter.eq('status', 'permanent')).size(),
            'dias_mes': d.advance(1, 'month').difference(d, 'day').round(),
            'sst_nino34': ee.Algorithms.If(ok, media_area(img, nino34), -999),
            'sst_tropical': ee.Algorithms.If(ok, media_area(img, tropics), -999),
        })
    return calc_mes


registros = []
for ano in range(1981, datetime.now().year + 1):
    fc = ee.FeatureCollection(ee.List.sequence(1, 12).map(fazer_calc_mes(ano)))
    for tentativa in range(3):
        try:
            feats = fc.getInfo()['features']
            break
        except Exception as e:
            if tentativa == 2:
                raise RuntimeError(f"Falha ao extrair o ano {ano} após 3 tentativas: {e}")
            print(f"   ⚠️ {ano}: falha temporária, tentando de novo em 15 s...")
            time.sleep(15)
    registros += [f['properties'] for f in feats]
    print(f"   {ano}: ok")

df = pd.DataFrame(registros)
duplicados = df[df['n_imgs'] > df['n_dias']]
if len(duplicados):
    print("⚠️ Meses com mais de uma imagem por dia (verifique):", duplicados[['ano', 'mes']].values.tolist())
df = df[(df['sst_nino34'] != -999) & (df['n_dias'] == df['dias_mes'])].copy()
df['provisorio'] = df['n_perm'] < df['n_dias']
df['data'] = pd.to_datetime(dict(year=df['ano'], month=df['mes'], day=1))
df = df.set_index('data').sort_index().asfreq('MS')
df['ano'], df['mes'] = df.index.year, df.index.month
lacunas = df[df['sst_nino34'].isna()]
if len(lacunas):
    print("⚠️ Meses ausentes (os trimestres vizinhos ficam vazios):", list(lacunas.index.strftime('%Y-%m')))
n_prov = int(df['provisorio'].fillna(False).astype(bool).sum())
print(f"✅ {df['sst_nino34'].notna().sum()} meses completos extraídos "
      f"({df.index.min():%Y-%m} a {df.index.max():%Y-%m}); {n_prov} com dias provisórios.\n")

# =========================================================================
# 4. RONI SAB (RÉPLICA OISST, BASE 1991-2020)
# =========================================================================
print("⏳ PASSO 4: Calculando o RONI da réplica SAB...")
base = df.loc['1991-01-01':'2020-12-01']
clima = base.groupby('mes')[['sst_nino34', 'sst_tropical']].mean()
df['anom_nino34'] = df['sst_nino34'] - df['mes'].map(clima['sst_nino34'])
df['anom_tropical'] = df['sst_tropical'] - df['mes'].map(clima['sst_tropical'])
df['anom_relativa'] = df['anom_nino34'] - df['anom_tropical']

b = df.loc['1991-01-01':'2020-12-01']
fator_ajuste = b['anom_nino34'].std() / b['anom_relativa'].std()
print(f"   Fator de ajuste de variância (1991-2020): {fator_ajuste:.4f}  <- compare com o painel")
df['anom_ajustada'] = df['anom_relativa'] * fator_ajuste


def arred1(x):
    """Arredonda para 1 casa, meio para longe do zero (igual ao Earth Engine)."""
    return np.sign(x) * np.floor(np.abs(x) * 10 + 0.5 + 1e-9) / 10


# Média móvel centrada: o valor fica no mês central (DJF = janeiro, NDJ = dezembro)
df['RONI_SAB_2c'] = df['anom_ajustada'].rolling(3, center=True).mean()
df['RONI_SAB'] = arred1(df['RONI_SAB_2c'])
df['provisorio_tri'] = df['provisorio'].astype(float).rolling(3, center=True).max() > 0
df['Trimestre'] = [ORDEM[m - 1] for m in df['mes']]
sab = df.reset_index()
matriz_sab = sab.pivot(index='ano', columns='Trimestre', values='RONI_SAB').reindex(columns=ORDEM)
print("✅ RONI SAB calculado.\n")

# =========================================================================
# 5. SÉRIE OFICIAL DO CPC (TABELA DIGITADA x ARQUIVO DE 2 CASAS)
# =========================================================================
print("⏳ PASSO 5: Conferindo a tabela oficial contra o arquivo do CPC...")


# [V4 M02-02] Lógica pura (sem rede e sem Earth Engine), testada em testes/teste_02.py
def empate_2c(x):
    """True onde a 2ª casa decimal é 5 (empate): o arquivo de 2 casas não diz para que lado o CPC
    arredondou (ele parte de mais casas). Usa o valor absoluto, então vale para negativos
    (-0,45 e -1,05 são empates)."""
    c = np.round(np.abs(np.asarray(x, dtype=float)) * 100)
    return np.isfinite(c) & (np.abs(c % 10 - 5) < 1e-6)


def arred_sem_empate(x):
    """Uma casa decimal. Fora dos empates todas as regras de arredondamento dão o mesmo valor
    (conferido nas 912 estações de 1950 a 2025: nenhuma divergência). O + 0.0 troca -0.0 por 0.0."""
    return np.round(np.asarray(x, dtype=float), 1) + 0.0


def ler_tabela(tabela_txt):
    tab = (pd.read_csv(io.StringIO(tabela_txt), sep=r'\s+').set_index('Year')[ORDEM]
             .stack().dropna().reset_index())
    tab.columns = ['ano', 'Trimestre', 'RONI']
    tab['ano'] = tab['ano'].astype(int)
    return tab


def conciliar_oficial(tab, asc, auto_novas=True, n_revisaveis=3):
    """Junta a tabela digitada (1 casa) e o arquivo do CPC (2 casas) e devolve a série oficial e um
    relatório {'acrescentadas': [[ano, trimestre, RONI_2c, RONI], ...], 'revisadas': [[ano,
    trimestre, valor da tabela, RONI_2c, RONI], ...]}. Regras:
      - estação digitada que o arquivo não tem: erro;
      - estação do arquivo que a tabela não tem: entra com o valor do arquivo arredondado, se a
        2ª casa não for 5; num empate, erro pedindo o valor da tabela ERSSTv6 do site;
      - diferença acima de 0,05 (meio arredondamento): nas n_revisaveis últimas estações da
        tabela é revisão do CPC e vale o arquivo; antes delas, erro (digitação ou revisão antiga)."""
    faltam = {'ano', 'Trimestre', 'RONI_2c'} - set(asc.columns)
    if faltam:
        raise ValueError(f"O arquivo do CPC não tem as colunas {sorted(faltam)}; colunas lidas: {list(asc.columns)}")
    tab = tab[['ano', 'Trimestre', 'RONI']].copy()
    asc = asc[['ano', 'Trimestre', 'RONI_2c']].copy()
    tab['ano'] = tab['ano'].astype(int)
    asc['ano'] = asc['ano'].astype(int)
    asc['RONI_2c'] = pd.to_numeric(asc['RONI_2c'], errors='coerce')
    ruins = asc[~asc['Trimestre'].isin(ORDEM) | ~np.isfinite(asc['RONI_2c']) | (asc['RONI_2c'].abs() > 9)
                | asc.duplicated(['ano', 'Trimestre'], keep=False)]
    if len(ruins):
        raise ValueError("Linhas inesperadas no arquivo do CPC (trimestre desconhecido, valor ausente ou "
                         f"estação repetida):\n{ruins}")
    of = tab.merge(asc, on=['ano', 'Trimestre'], how='outer', indicator=True)
    of['_ordem'] = of['ano'] * 12 + of['Trimestre'].map({t: i for i, t in enumerate(ORDEM)})
    so_tabela = of[of['_merge'] == 'left_only']
    if len(so_tabela):
        raise ValueError("Estações digitadas na tabela que o arquivo do CPC não tem "
                         "(confira se alguma foi digitada a mais):\n"
                         f"{so_tabela[['ano', 'Trimestre', 'RONI']]}")
    rel = {'acrescentadas': [], 'revisadas': []}
    novas = of[of['_merge'] == 'right_only']
    if len(novas):
        if not auto_novas:
            raise ValueError("A tabela digitada e o arquivo do CPC cobrem estações diferentes. "
                             "Acrescente na tabela as estações novas (ou confira se alguma foi digitada a mais):\n"
                             f"{novas[['ano', 'Trimestre', 'RONI', 'RONI_2c', '_merge']]}")
        emp = empate_2c(novas['RONI_2c'])
        if emp.any():
            raise ValueError("Estação nova no arquivo do CPC com a 2ª casa decimal 5 (empate): o arquivo de "
                             "2 casas não diz para que lado o CPC arredondou. Abra " + URL_TABELA_CPC +
                             " , leia o valor na tabela ERSSTv6 e digite-o na tabela noaa_data deste "
                             "arquivo (linha do ano, coluna do trimestre, no lugar do NaN); depois rode de novo:\n"
                             f"{novas.loc[emp, ['ano', 'Trimestre', 'RONI_2c']].to_string(index=False)}")
        of.loc[novas.index, 'RONI'] = arred_sem_empate(novas['RONI_2c'])
        rel['acrescentadas'] = [[int(a), t, float(x), float(v)] for a, t, x, v in
                                of.loc[novas.index].sort_values('_ordem')[['ano', 'Trimestre', 'RONI_2c', 'RONI']]
                                .itertuples(index=False)]
    ultimas = set(of.loc[of['_merge'] == 'both', '_ordem'].nlargest(n_revisaveis))
    dif = (of['RONI'] - of['RONI_2c']).abs()
    diverg = (of['_merge'] == 'both') & (dif > 0.05 + 1e-9)
    recente = of['_ordem'].isin(ultimas)
    if (diverg & ~recente).any():
        raise ValueError("Divergência acima do arredondamento entre a tabela e o arquivo do CPC "
                         f"(provável erro de digitação ou revisão do CPC):\n"
                         f"{of.loc[diverg & ~recente, ['ano', 'Trimestre', 'RONI', 'RONI_2c']]}")
    rev = diverg & recente
    if rev.any():
        emp = empate_2c(of.loc[rev, 'RONI_2c'])
        if emp.any():
            raise ValueError(f"O CPC revisou uma das {n_revisaveis} últimas estações da tabela e o valor novo "
                             "tem a 2ª casa decimal 5 (empate). Abra " + URL_TABELA_CPC + " , leia o valor "
                             "na tabela ERSSTv6 e corrija-o na tabela noaa_data; depois rode de novo:\n"
                             f"{of.loc[rev, ['ano', 'Trimestre', 'RONI', 'RONI_2c']][emp].to_string(index=False)}")
        antes = of.loc[rev, 'RONI'].to_numpy()
        of.loc[rev, 'RONI'] = arred_sem_empate(of.loc[rev, 'RONI_2c'])
        rel['revisadas'] = [[int(a), t, float(v0), float(x), float(v)] for (a, t, x, v), v0 in
                            zip(of.loc[rev, ['ano', 'Trimestre', 'RONI_2c', 'RONI']].itertuples(index=False), antes)]
    of['mes'] = of['Trimestre'].map({t: i + 1 for i, t in enumerate(ORDEM)})
    of['Fonte'] = 'CPC_ERSSTv6'
    return of.drop(columns=['_merge', '_ordem']).sort_values(['ano', 'mes']).reset_index(drop=True), rel


def linhas_tabela(of, anos):
    """Linhas no formato da tabela noaa_data (uma casa, NaN onde ainda não há estação)."""
    m = of.pivot(index='ano', columns='Trimestre', values='RONI').reindex(columns=ORDEM)
    saida = []
    for a in anos:
        vals = m.loc[a] if a in m.index else [np.nan] * 12
        saida.append(f"{a} " + " ".join(f"{v + 0.0:.1f}" if pd.notna(v) else "NaN" for v in vals))
    return saida


def carregar_oficial(tabela_txt):
    asc = (pd.read_csv(URL_ASCII, sep=r'\s+')
             .rename(columns={'SEAS': 'Trimestre', 'YR': 'ano', 'ANOM': 'RONI_2c'}))
    of, rel = conciliar_oficial(ler_tabela(tabela_txt), asc, AUTO_ESTACOES_NOVAS, ESTACOES_REVISAVEIS)
    if rel['acrescentadas']:
        print("   Estações acrescentadas do arquivo do CPC:", rel['acrescentadas'])
    for a, t, v0, x, v in rel['revisadas']:
        print(f"   ⚠️ Revisão do CPC em {t} {a}: tabela {v0:+.1f}, arquivo {x:+.2f}; vale {v:+.1f}. Cole na tabela "
              f"a linha do fim do log: sem isso, a diferença volta a parar a execução quando essa estação deixar "
              f"de estar entre as {ESTACOES_REVISAVEIS} últimas digitadas.")
    return of, rel


oficial, rel_cpc = carregar_oficial(noaa_data)   # [V4 M02-02]
matriz_noaa = oficial.pivot(index='ano', columns='Trimestre', values='RONI').reindex(columns=ORDEM)
ult = oficial.iloc[-1]
print(f"✅ {len(oficial)} estações oficiais conferidas (última: {ult['Trimestre']} {ult['ano']} = {ult['RONI']:+.1f}).\n")

# =========================================================================
# 6. ASSET ANTIGO (DETECTA O FORMATO)
# =========================================================================
print("⏳ PASSO 6: Lendo o asset antigo...")
matriz_asset = pd.DataFrame(columns=ORDEM, dtype=float)
try:
    props = [f['properties'] for f in ee.FeatureCollection(ASSET_ANTIGO).getInfo()['features']]
    print(f"   Propriedades do asset antigo: {sorted(props[0])}")
    if 'Year' in props[0]:
        matriz_asset = (pd.DataFrame(props).set_index('Year')[ORDEM]
                          .apply(pd.to_numeric, errors='coerce'))
        print("   Formato: largo (uma linha por ano)")
    else:
        col_valor = 'ONI' if 'ONI' in props[0] else 'RONI'
        matriz_asset = (pd.DataFrame(props).pivot(index='ano', columns='Trimestre', values=col_valor)
                          .reindex(columns=ORDEM).apply(pd.to_numeric, errors='coerce'))
        print(f"   Formato: longo (uma linha por estação, valor em '{col_valor}')")
    matriz_asset.index = matriz_asset.index.astype(int)
    print("✅ Asset antigo carregado.\n")
except Exception as e:
    print(f"⚠️ Não foi possível ler o asset antigo: {e}\n")

# =========================================================================
# 7. LOG: COMPARAÇÃO TRIPLA
# =========================================================================
print("=========================================================================================")
print("📋 COMPARAÇÃO TRIPLA (ASSET ANTIGO x CPC ERSSTv6 OFICIAL x RÉPLICA SAB OISST)")
print("=========================================================================================\n")
cabecalho = " ".join([f"{c:>5}" for c in ORDEM])
vazio = pd.Series([np.nan] * 12, index=ORDEM)


def linha(m, ano):
    return m.loc[ano].reindex(ORDEM) if ano in m.index else vazio


divergencias_asset = 0
for ano in range(1950, datetime.now().year + 1):
    ra, rn, rs = linha(matriz_asset, ano), linha(matriz_noaa, ano), linha(matriz_sab, ano)
    if not (ra.notna().any() or rn.notna().any() or rs.notna().any()):
        continue
    fmt = lambda s: " ".join([f"{x:5.1f}" if pd.notna(x) else "  N/A" for x in s])
    marca = ""
    if ra.notna().any() and rn.notna().any():
        dif = (ra - rn).abs().max()
        if dif > 0.01:
            divergencias_asset += 1
            marca = f"   ⚠️ asset difere do oficial (até {dif:.1f})"
    print(f"🗓️  ANO {ano}:{marca}")
    print(f"{'':>17}{cabecalho}")
    print("   ASSET (Antigo):" + fmt(ra))
    print("   CPC (Oficial): " + fmt(rn))
    print("   SAB (OISST):   " + fmt(rs))
    print("   -----------------------------------------------------------------------------------")
print(f"\nAnos em que o asset antigo difere da tabela oficial: {divergencias_asset}")

# =========================================================================
# 8. ESTATÍSTICA: RÉPLICA SAB x CPC
# =========================================================================


def sinal(v):
    v = np.asarray(v, dtype=float)
    return np.where(v >= 0.5, 1, np.where(v <= -0.5, -1, 0))


def fases_episodio(v):
    """Fase por episódio: limiar de ±0,5 mantido por pelo menos 5 estações seguidas."""
    s = sinal(v)
    f = np.zeros(len(s), int)
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i] and s[i] != 0:
            j += 1
        if s[i] != 0 and j - i >= 5:
            f[i:j] = s[i]
        i = max(j, i + 1)
    return f


comp = (sab[['ano', 'mes', 'RONI_SAB', 'RONI_SAB_2c', 'provisorio_tri']]
          .merge(oficial[['ano', 'mes', 'RONI', 'RONI_2c']], on=['ano', 'mes'])
          .dropna(subset=['RONI_SAB_2c', 'RONI_2c']))
comp = comp[~comp['provisorio_tri']].sort_values(['ano', 'mes'])
erro = comp['RONI_SAB_2c'] - comp['RONI_2c']

print("\n=================================================================")
print("📊 RÉPLICA SAB (OISST) x CPC OFICIAL (ERSSTv6), SEM MESES PROVISÓRIOS")
print("=================================================================")
print(f"Trimestres comparados: {len(comp)} ({comp['ano'].min()} a {comp['ano'].max()})")
print(f"🔹 Viés médio (SAB - CPC): {erro.mean():+.3f} °C")
print(f"🔹 RMSE: {np.sqrt((erro ** 2).mean()):.3f} °C | MAE: {erro.abs().mean():.3f} °C")
print(f"🔹 Correlação de Pearson: {comp['RONI_SAB_2c'].corr(comp['RONI_2c']):.4f}")
print(f"🔹 Concordância de sinal (±0,5): {100 * (sinal(comp['RONI_SAB']) == sinal(comp['RONI'])).mean():.1f}%")
print(f"🔹 Concordância de fase (episódios): "
      f"{100 * (fases_episodio(comp['RONI_SAB']) == fases_episodio(comp['RONI'])).mean():.1f}%")

# =========================================================================
# 9. GRAVAÇÃO DO ASSET OFICIAL (TEMPORÁRIO -> PROMOÇÃO) E ARQUIVOS DE AUDITORIA
# =========================================================================
oficial['data_ms'] = ((pd.to_datetime(dict(year=oficial['ano'], month=oficial['mes'], day=1))
                       - pd.Timestamp('1970-01-01')) // pd.Timedelta('1ms')).astype('int64')
oficial['chave_join'] = [f'{a:04d}_{m:02d}' for a, m in zip(oficial['ano'], oficial['mes'])]   # [V4 M02-03]
cols = ['ano', 'mes', 'Trimestre', 'RONI', 'RONI_2c', 'Fonte', 'data_ms', 'chave_join']   # [V4 M02-03] + chave_join
oficial[cols].to_csv('RONI_CPC_v6.csv', index=False)
comp.to_csv('auditoria_RONI_SAB_x_CPC.csv', index=False, sep=';', decimal=',')
print("\n💾 Arquivos locais: RONI_CPC_v6.csv e auditoria_RONI_SAB_x_CPC.csv")


# [V4 M02-01] Compartilhamento (ACL) e troca de assets
def asset_existe(caminho):
    try:
        ee.data.getAsset(caminho)
        return True
    except ee.EEException:
        return False


def acl_sem_dono(acl):
    return {k: v for k, v in (acl or {}).items() if k != 'owners'}


def acl_resumo(acl):
    """ACL sem 'owners', sem entradas vazias e com listas ordenadas, para comparar antes e depois."""
    return {k: (sorted(v) if isinstance(v, list) else v) for k, v in acl_sem_dono(acl).items() if v}


def aplicar_acl(asset, acl):
    """Reaplica a ACL sem 'owners'. A CONFIRMAR o formato que ee.data.setAssetAcl aceita na versão
    do Colab (texto JSON nas antigas; texto ou dicionário nas novas): tenta os dois. Devolve None
    se deu certo, ou o texto dos erros."""
    atual = acl_sem_dono(acl)
    erros = []
    for formato, valor in (('texto JSON', json.dumps(atual)), ('dicionário', dict(atual))):
        try:
            ee.data.setAssetAcl(asset, valor)
            return None
        except Exception as e:
            erros.append(f"{formato}: {str(e)[:150]}")
    return ' | '.join(erros)


# [V4 M02-03] Leitura de volta do asset gravado
def ler_asset_roni(asset):
    """Propriedades de todas as feições; ts_lido = system:time_start (-1 se a feição não o tiver)."""
    fc = ee.FeatureCollection(asset).map(lambda f: f.set('ts_lido', ee.Algorithms.If(
        f.propertyNames().contains('system:time_start'), f.get('system:time_start'), -1)))
    for tentativa in range(3):
        try:
            return pd.DataFrame([f['properties'] for f in fc.getInfo()['features']])
        except Exception as e:
            if tentativa == 2:
                raise
            print(f"   ⚠️ leitura de volta: falha temporária ({str(e)[:80]}), tentando de novo em 15 s...")
            time.sleep(15)


def conferir_leitura(lido, of):
    """Compara o asset lido de volta com a série oficial. Devolve {'erros', 'avisos', 'itens'}.
    Lógica pura (sem Earth Engine), testada em testes/teste_02.py."""
    res = {'erros': [], 'avisos': [], 'itens': []}
    precisa = ['ano', 'mes', 'Trimestre', 'RONI', 'RONI_2c', 'data_ms', 'chave_join']
    faltam = [c for c in precisa if c not in lido.columns]
    if faltam:
        res['erros'].append(f"propriedades ausentes no asset: {faltam}")
        return res
    g = lido.copy()
    for c in ('ano', 'mes', 'RONI', 'RONI_2c', 'data_ms'):
        g[c] = pd.to_numeric(g[c], errors='coerce')
    if g[['ano', 'mes']].isna().any().any() or ((g['ano'] % 1 != 0) | (g['mes'] % 1 != 0)).any():
        res['erros'].append("ano ou mes ausente ou não inteiro em alguma feição")
        return res
    g['ano'], g['mes'] = g['ano'].astype('int64'), g['mes'].astype('int64')
    rep = g[g.duplicated(['ano', 'mes'], keep=False)]
    if len(rep):
        res['erros'].append(f"estações repetidas no asset: {rep[['ano', 'mes']].values.tolist()[:10]}")
    m = of[precisa].merge(g, on=['ano', 'mes'], how='outer', suffixes=('', '_lido'), indicator=True)
    fora = m[m['_merge'] != 'both']
    if len(fora):
        res['erros'].append(f"{len(fora)} estação(ões) só na série oficial (left_only) ou só no asset "
                            f"(right_only): {fora[['ano', 'mes', '_merge']].astype(str).values.tolist()[:10]}")
    b = m[m['_merge'] == 'both']

    def acusar(ruim, rotulo, cols_):
        if ruim.any():
            res['erros'].append(f"{rotulo} diverge em {int(ruim.sum())} estação(ões): "
                                f"{b.loc[ruim, ['ano', 'mes'] + cols_].values.tolist()[:10]}")

    acusar(~((b['RONI'] - b['RONI_lido']).abs() < 1e-6), 'RONI', ['RONI', 'RONI_lido'])
    acusar(~((b['RONI_2c'] - b['RONI_2c_lido']).abs() < 1e-6), 'RONI_2c', ['RONI_2c', 'RONI_2c_lido'])
    acusar(b['Trimestre'].astype(str) != b['Trimestre_lido'].astype(str), 'Trimestre', ['Trimestre', 'Trimestre_lido'])
    acusar(~((b['data_ms'] - b['data_ms_lido']).abs() < 0.5), 'data_ms', ['data_ms', 'data_ms_lido'])
    acusar(b['chave_join'].astype(str) != b['chave_join_lido'].astype(str), 'chave_join', ['chave_join', 'chave_join_lido'])
    res['itens'] += ['estações', 'RONI', 'RONI_2c', 'Trimestre', 'mês central', 'data_ms', 'chave_join']
    ts = pd.to_numeric(b['ts_lido'], errors='coerce') if 'ts_lido' in b.columns else pd.Series(np.nan, index=b.index)
    ts = ts.where(ts != -1)
    if 'system:time_start' in b.columns:
        ts = ts.fillna(pd.to_numeric(b['system:time_start'], errors='coerce'))
    if len(b) and ts.isna().all():
        res['avisos'].append("system:time_start não veio em nenhuma feição lida (A CONFIRMAR se a exportação de "
                             "tabela o preserva). O painel recalcula a data a partir de ano e mes, e data_ms foi conferido")
    else:
        b = b.assign(ts=ts)
        acusar(~((ts - b['data_ms']).abs() < 0.5), 'system:time_start', ['data_ms', 'ts'])
        res['itens'].append('system:time_start')
    return res


if not GRAVAR_ASSET:
    print("ℹ️ GRAVAR_ASSET = False: nada foi gravado no Earth Engine.")
else:
    print(f"\n⏳ Gravando {ASSET_RONI}...")
    TMP = ASSET_RONI + '_TMP'
    linhas = json.loads(oficial[cols].to_json(orient='records'))
    # [Correção 20/10/2026, 23h55] A exportação de tabela para asset recusa feições sem geometria ("Unable to
    # export features with null geometry"). Cada estação recebe um ponto fixo (0, 0), só para a exportação: o painel,
    # a auditoria 08 e a conferência abaixo leem apenas as propriedades.
    PONTO_FIXO = ee.Geometry.Point([0, 0])
    fc_roni = ee.FeatureCollection([
        ee.Feature(PONTO_FIXO, dict(r, **{'system:time_start': r['data_ms']})) for r in linhas])
    try:
        ee.data.deleteAsset(TMP)
    except ee.EEException:
        pass
    task = ee.batch.Export.table.toAsset(collection=fc_roni, description='RONI_CPC_v6', assetId=TMP)
    task.start()
    while task.status()['state'] in ('READY', 'RUNNING', 'SUBMITTED', 'PENDING'):
        time.sleep(15)
    if task.status()['state'] != 'COMPLETED':
        raise RuntimeError(f"Exportação falhou: {task.status()}")
    # [V4 M02-01] Troca sem janela: o atual vira _ANTERIOR (apagado só depois da conferência do
    # M02-03) e o _TMP é promovido; a ACL do atual é reaplicada no novo
    BKP = ASSET_RONI + '_ANTERIOR'
    existia = asset_existe(ASSET_RONI)
    if not existia and asset_existe(BKP):
        # [V4 revisão B-03] Sobra de uma restauração que falhou: o _ANTERIOR é a única cópia boa. Ele volta ao
        # lugar antes da troca (senão seria apagado logo abaixo e, se a conferência falhasse de novo, não
        # sobraria nenhum RONI).
        try:
            ee.data.renameAsset(BKP, ASSET_RONI)
        except ee.EEException as e:
            raise RuntimeError(f"❌ {BKP.split('/')[-1]} existe sem {ASSET_RONI.split('/')[-1]} e não consegui "
                               f"devolvê-lo ao lugar ({e}). Na aba Assets, renomeie {BKP} para {ASSET_RONI} e rode "
                               f"de novo. A versão nova ficou em {TMP}.")
        existia = True
        print(f"   {BKP.split('/')[-1]} sem o asset principal (sobra de uma restauração que falhou): "
              f"versão anterior devolvida ao lugar antes da troca.")
    acl_antiga = None
    if existia:
        try:
            acl_antiga = ee.data.getAssetAcl(ASSET_RONI)
            print(f"   ACL do asset atual: {acl_antiga}")
        except ee.EEException as e:
            print(f"   ⚠️ Não foi possível ler a ACL do asset atual ({e}); confira o compartilhamento no fim.")
    if asset_existe(BKP):
        ee.data.deleteAsset(BKP)
        print(f"   {BKP.split('/')[-1]} que tinha sobrado de uma execução anterior foi apagado.")
    if existia:
        try:
            ee.data.renameAsset(ASSET_RONI, BKP)
        except ee.EEException as e:
            raise RuntimeError(f"❌ Não foi possível renomear {ASSET_RONI} para {BKP} ({e}). Nada foi trocado; "
                               f"a versão nova ficou em {TMP}. Rode de novo.")
    try:
        ee.data.renameAsset(TMP, ASSET_RONI)
    except ee.EEException as e:
        if existia:
            try:
                ee.data.renameAsset(BKP, ASSET_RONI)
            except ee.EEException:
                raise RuntimeError(f"❌ Não foi possível promover {TMP} ({e}) nem devolver a versão anterior. "
                                   f"Na aba Assets, renomeie {BKP} para {ASSET_RONI}. Mande esta saída.")
        raise RuntimeError(f"❌ Não foi possível promover {TMP} ({e}). O asset anterior continua em {ASSET_RONI}.")
    erro_acl = None
    if acl_antiga is not None:
        erro_acl = aplicar_acl(ASSET_RONI, acl_antiga)
        if erro_acl:
            print(f"   ⚠️ Não foi possível reaplicar o compartilhamento ({erro_acl}). Compartilhe {ASSET_RONI} "
                  f"à mão (Anyone can read) se o painel for publicado como App (roteiro 2.7).")
    else:
        print(f"   ℹ️ Não havia ACL anterior para reaplicar: compartilhe {ASSET_RONI} à mão (Anyone can read) "
              f"se o painel for publicado como App (roteiro 2.7).")
    try:
        acl_final = ee.data.getAssetAcl(ASSET_RONI)
        print(f"   ACL final de {ASSET_RONI.split('/')[-1]}: {acl_final}")
        if acl_antiga is not None and not erro_acl and acl_resumo(acl_final) != acl_resumo(acl_antiga):
            print(f"   ⚠️ O compartilhamento final difere do anterior ({acl_resumo(acl_antiga)}). "
                  f"Compartilhe {ASSET_RONI} à mão (Anyone can read) se o painel for publicado como App.")
    except ee.EEException as e:
        print(f"   ⚠️ Não foi possível ler a ACL final ({e}); confira o compartilhamento na aba Assets.")
    # [V4 M02-03] Leitura de volta: só depois dela o _ANTERIOR é apagado
    try:
        n_gravado = ee.FeatureCollection(ASSET_RONI).size().getInfo()     # [V4 revisão B-10] dentro do try
        print(f"✅ {n_gravado} estações gravadas em {ASSET_RONI} (esperado {len(linhas)}).")
        lido = ler_asset_roni(ASSET_RONI)
    except Exception as e:
        raise RuntimeError(f"❌ Não foi possível ler {ASSET_RONI} de volta para conferir ({str(e)[:150]}). "
                           f"O asset novo ficou no lugar e a versão anterior foi mantida em {BKP}; rode de novo.")
    conf = conferir_leitura(lido, oficial)
    for a in conf['avisos']:
        print(f"   ⚠️ {a}")
    if conf['erros']:
        print("❌ O asset gravado não bate com a série oficial:")
        for e in conf['erros']:
            print(f"   - {e}")
        try:
            ee.data.deleteAsset(ASSET_RONI)
            if existia:
                ee.data.renameAsset(BKP, ASSET_RONI)
                if acl_antiga is not None and aplicar_acl(ASSET_RONI, acl_antiga):
                    print("   ⚠️ Compartilhamento não reaplicado na versão restaurada: compartilhe à mão (Anyone can read).")
        except ee.EEException as e:
            # [V4 revisão B-10] o delete pode ter falhado: o asset ruim ainda estaria no lugar
            raise RuntimeError(f"❌ Conferência falhou e a restauração também ({e}). Na aba Assets: se "
                               f"{ASSET_RONI.split('/')[-1]} ainda existir, apague-o" +
                               (f"; depois renomeie {BKP} para {ASSET_RONI}." if existia else ".") +
                               " Mande esta saída.")
        raise RuntimeError("❌ Conferência do asset gravado falhou; " +
                           (f"a versão anterior de {ASSET_RONI} foi restaurada." if existia else
                            "o asset novo foi apagado (não havia versão anterior).") + " Mande esta saída.")
    print(f"✅ {len(lido)} estações conferidas no asset ({', '.join(conf['itens'])}).")
    if asset_existe(BKP):
        try:
            ee.data.deleteAsset(BKP)
            print(f"   Versão anterior ({BKP.split('/')[-1]}) apagada.")
        except ee.EEException as e:
            print(f"   ⚠️ Não foi possível apagar {BKP} ({e}); a próxima execução apaga, ou apague na aba Assets.")

# [V4 M02-02] Linha do ano já atualizada, no formato da tabela (colar é opcional para estações novas,
# que o script acrescenta sozinho; recomendado depois de uma revisão do CPC)
anos_linha = sorted({int(oficial['ano'].iloc[-1])} |
                    {r[0] for r in rel_cpc['acrescentadas'] + rel_cpc['revisadas']})
print("\n📝 Tabela noaa_data com as estações de hoje, para colar no lugar da linha do mesmo ano "
      f"({'recomendado: houve revisão do CPC' if rel_cpc['revisadas'] else 'opcional'}):")
for lin in linhas_tabela(oficial, anos_linha):
    print(lin)
