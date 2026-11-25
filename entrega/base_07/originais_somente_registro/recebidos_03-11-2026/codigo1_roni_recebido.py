# =========================================================================
# AUDITORIA CIENTÍFICA + COMPARAÇÃO TRIPLA DO RONI (1950-2026)
# ASSET ANTIGO (1950-1980) VS GABARITO NOAA VS MOTOR SAB (OISST)
# =========================================================================

import ee
import pandas as pd
import numpy as np
import io
import time

# 1. AUTENTICAÇÃO E INICIALIZAÇÃO
print("⏳ PASSO 1: Autenticando no Earth Engine...")
PROJECT_ID = 'clima-492922'
try:
    ee.Initialize(project=PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)
print("✅ Autenticado com sucesso!\n")

# 2. EXTRAÇÃO DOS DADOS OISST DO PACÍFICO (1981-2026)
print("⏳ PASSO 2: Extraindo dados do Oceano Pacífico via OISST (1981-2026)...")
nino34 = ee.Geometry.Rectangle([-170, -5, -120, 5])
tropics = ee.Geometry.Rectangle([-179.99, -20, 179.99, 20])
oisst = ee.ImageCollection('NOAA/CDR/OISST/V2_1').select('sst')

registros = []
for ano in range(1981, 2027):
    meses = ee.List.sequence(1, 12)
    def calc_mes(m):
        d = ee.Date.fromYMD(ano, m, 1)
        col = oisst.filterDate(d, d.advance(1, 'month'))
        tem_imagem = col.size().gt(0)

        img = ee.Image(ee.Algorithms.If(tem_imagem, col.mean().multiply(0.01), ee.Image.constant(-999).rename('sst')))
        nino = ee.Algorithms.If(tem_imagem, img.reduceRegion(ee.Reducer.mean(), nino34, 25000).get('sst'), -999)
        trop = ee.Algorithms.If(tem_imagem, img.reduceRegion(ee.Reducer.mean(), tropics, 25000).get('sst'), -999)

        return ee.Feature(None, {'ano': ano, 'mes': m, 'sst_nino34': nino, 'sst_tropical': trop})

    fc = ee.FeatureCollection(meses.map(calc_mes))
    try:
        dados_ano = fc.getInfo()['features']
        for feat in dados_ano:
            props = feat['properties']
            if props['sst_nino34'] is not None and props['sst_nino34'] != -999:
                registros.append(props)
    except Exception:
        pass
    time.sleep(0.2)

df = pd.DataFrame(registros)
df['data'] = pd.to_datetime(df['ano'].astype(str) + '-' + df['mes'].astype(str) + '-01')
df = df.sort_values('data').reset_index(drop=True)
print(f"✅ {len(df)} meses OISST extraídos com sucesso.\n")

# 3. CÁLCULO DO RONI SAB (CLIMATOLOGIA 1991-2020)
print("⏳ PASSO 3: Aplicando o pipeline matemático do Motor SAB...")
df_base = df[(df['data'] >= '1991-01-01') & (df['data'] <= '2020-12-01')]
clima = df_base.groupby('mes')[['sst_nino34', 'sst_tropical']].mean().reset_index()
clima.columns = ['mes', 'clima_nino34', 'clima_tropical']

df = df.merge(clima, on='mes', how='left')
df['anom_nino34'] = df['sst_nino34'] - df['clima_nino34']
df['anom_tropical'] = df['sst_tropical'] - df['clima_tropical']
df['anom_relativa'] = df['anom_nino34'] - df['anom_tropical']

df_base_anom = df[(df['data'] >= '1991-01-01') & (df['data'] <= '2020-12-01')]
fator_ajuste = df_base_anom['anom_nino34'].std() / df_base_anom['anom_relativa'].std()

df['anom_ajustada'] = df['anom_relativa'] * fator_ajuste
df['RONI_SAB_Bruto'] = df['anom_ajustada'].rolling(window=3).mean()
df['RONI_SAB'] = (df['RONI_SAB_Bruto'] * 10).round() / 10

# Preparação das colunas de identificação para a Matriz
df['Ano_Visualizacao'] = df['data'].dt.year
df.loc[df['data'].dt.month == 1, 'Ano_Visualizacao'] -= 1
trimestres_nomes = {2: 'DJF', 3: 'JFM', 4: 'FMA', 5: 'MAM', 6: 'AMJ', 7: 'MJJ',
                    8: 'JJA', 9: 'JAS', 10: 'ASO', 11: 'SON', 12: 'OND', 1: 'NDJ'}
df['Trimestre'] = df['data'].dt.month.map(trimestres_nomes)
ordem_colunas = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']

matriz_sab = df.pivot(index='Ano_Visualizacao', columns='Trimestre', values='RONI_SAB')
matriz_sab = matriz_sab.reindex(columns=ordem_colunas)

# 4. GABARITO OFICIAL NOAA (NOVO)
print("⏳ PASSO 4: Estruturando o Gabarito Oficial da NOAA...")
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

df_noaa_matriz = pd.read_csv(io.StringIO(noaa_data), sep=r'\s+')
matriz_noaa = df_noaa_matriz.set_index('Year')
matriz_noaa = matriz_noaa.reindex(columns=ordem_colunas)

# 5. EXTRAÇÃO DO ASSET ANTIGO (1950-1980)
print("⏳ PASSO 5: Extraindo o Asset Antigo do Earth Engine...")
try:
    asset_antigo = ee.FeatureCollection('projects/clima-492922/assets/RONI_Calibrado_Sazonal_1950_1980')
    features_antigas = asset_antigo.getInfo()['features']
    lista_antiga = []
    for feat in features_antigas:
        p = feat['properties']
        lista_antiga.append({'Year': p.get('ano'), 'Trimestre': p.get('Trimestre'), 'RONI_ASSET': p.get('ONI')})

    df_asset = pd.DataFrame(lista_antiga)
    matriz_asset = df_asset.pivot(index='Year', columns='Trimestre', values='RONI_ASSET')
    matriz_asset = matriz_asset.reindex(columns=ordem_colunas)
    print("✅ Asset Antigo carregado com sucesso.\n")
except Exception as e:
    print(f"⚠️ Aviso: Não foi possível carregar o asset antigo. Erro: {e}\n")
    matriz_asset = pd.DataFrame(columns=ordem_colunas)

# 6. LOG VISUAL: COMPARAÇÃO TRIPLA
print("=========================================================================================")
print("📋 LOG ORGANIZADO: COMPARAÇÃO TRIPLA (ASSET ANTIGO vs NOAA ERSST vs MOTOR SAB)")
print("=========================================================================================\n")

cabecalho = " ".join([f"{col:>5}" for col in ordem_colunas])

for ano_vis in range(1950, 2027):
    row_asset = matriz_asset.loc[ano_vis] if ano_vis in matriz_asset.index else pd.Series([np.nan]*12, index=ordem_colunas)
    row_noaa  = matriz_noaa.loc[ano_vis] if ano_vis in matriz_noaa.index else pd.Series([np.nan]*12, index=ordem_colunas)
    row_sab   = matriz_sab.loc[ano_vis] if ano_vis in matriz_sab.index else pd.Series([np.nan]*12, index=ordem_colunas)

    # Imprime apenas anos que possuem dado em ao menos uma das três tabelas
    if row_asset.notna().any() or row_noaa.notna().any() or row_sab.notna().any():
        print(f"🗓️  ANO {ano_vis}:")
        print(f"{'':>17}{cabecalho}")

        str_asset = " ".join([f"{x:5.1f}" if pd.notna(x) else "  N/A" for x in row_asset])
        str_noaa  = " ".join([f"{x:5.1f}" if pd.notna(x) else "  N/A" for x in row_noaa])
        str_sab   = " ".join([f"{x:5.1f}" if pd.notna(x) else "  N/A" for x in row_sab])

        print("   ASSET (Antigo):" + str_asset)
        print("   NOAA (Oficial):" + str_noaa)
        print("   SAB (OISST):   " + str_sab)
        print("   -----------------------------------------------------------------------------------")

# 7. ESTATÍSTICA APLICADA (SAB VS NOAA NO PERÍODO ORBITAL)
s1 = matriz_sab.stack()
s2 = matriz_noaa.stack()
df_stats = pd.DataFrame({'SAB': s1, 'NOAA': s2}).dropna()

mse = ((df_stats['SAB'] - df_stats['NOAA'])**2).mean()
rmse = np.sqrt(mse)
mae = (df_stats['SAB'] - df_stats['NOAA']).abs().mean()
correlacao = df_stats['SAB'].corr(df_stats['NOAA'])

print("\n=================================================================")
print("📊 RESUMO DOS RESULTADOS ESTATÍSTICOS (SAB vs NOAA | 1981 - 2026)")
print("=================================================================")
print(f"Total de trimestres analisados em conjunto: {len(df_stats)} meses.")
print(f"🔹 MSE (Erro Quadrático Médio): {round(mse, 4)}")
print(f"🔹 RMSE (Raiz do Erro Quadrático Médio): {round(rmse, 4)} °C")
print(f"🔹 MAE (Erro Absoluto Médio): {round(mae, 4)} °C")
print(f"🔹 Correlação de Pearson (R): {round(correlacao, 4)}")

# =========================================================================
# 8. GERADOR DO ARQUIVO COMPLETO DE RECONSTRUÇÃO (1950 - 2026) PARA O ASSET GEE
# =========================================================================
print("\n=================================================================")
print("🛠️ GERANDO TABELA DE RECONSTRUÇÃO COMPLETA (1950-2026)")
print("=================================================================")

matriz_sab_export = matriz_sab.copy()
matriz_sab_export.index.name = 'Year'

matriz_noaa_export = matriz_noaa.copy()
matriz_noaa_export.index.name = 'Year'

# Prioriza dados do SAB e preenche os vazios do passado (1950 a 1981) com o NOAA ERSST
df_export_final = matriz_sab_export.combine_first(matriz_noaa_export).reset_index()
df_export_final = df_export_final.sort_values('Year').reset_index(drop=True)

nome_arquivo_csv = "RONI_Calibrado_Sazonal_1950_2026.csv"
df_export_final.to_csv(nome_arquivo_csv, index=False)

print(f"✅ Arquivo compilado com sucesso: '{nome_arquivo_csv}'")
print("   - Tabela unificada e pronta para upload no Google Earth Engine substituindo o Asset antigo.")
