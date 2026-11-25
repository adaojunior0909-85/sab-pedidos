# ⛔⛔⛔ NÃO EXECUTAR: SCRIPT ORIGINAL GUARDADO SÓ COMO REGISTRO DO MÉTODO (metodologia da tese) ⛔⛔⛔
# Gerou: projects/clima-492922/assets/SICSB_SOLO_2015_2025 (12 imagens Matriz_Solo_MM)
# Hoje: Em uso, só leitura: fator SMAP/ERA5 da umidade do solo (motor V1.5 e correção de leitura do painel).
# Substituído por: não substituído
# Por que não rodar: ele RECRIARIA o asset acima; o banco, as calibrações e as validações (K8 a K16, 07a/07b,
#   08) foram aprovados com o asset que já existe. Rodar de novo exigiria refazer e validar tudo.
# Recebido do responsável em 03/11/2026 (scripts_originais_recebidos.txt, linhas 1664 a 1801). Abaixo da linha ORIGINAL, o texto está sem nenhuma
#   mudança. SHA-256 do trecho original: 404c8bd65a48f727fbec0e7b8a9f1a6435b6c18613eaf563dea794c16cc353f8
# A linha raise SystemExit abaixo faz a célula parar antes de qualquer import ou gravação.
raise SystemExit('⛔ Script original guardado só como registro. NÃO EXECUTAR (veja o cabeçalho).')
# ================================================ ORIGINAL ================================================
# =========================================================================================
# TÍTULO: Motor Gerador da Base Climatológica de Solo (Calibração ERA5-Land vs SMAP L4)
# RESUMO: Processa a sobreposição temporal (2015 a 2025) entre as duas bases de solo
# para gerar as 12 matrizes mensais de Média e Desvio Padrão (Z-Score).
# UNIDADES: Umidade do Solo em Fração Volumétrica (m³/m³) | Runoff em milímetros (mm).
# =========================================================================================

import ee

print("🔄 Conectando ao Google Earth Engine...")
try:
    ee.Initialize(project='clima-492922')
    print("✔️ Conectado com sucesso!")
except Exception:
    ee.Authenticate()
    ee.Initialize(project='clima-492922')

# =========================================================================
# 2. CONFIGURAÇÕES GEOGRÁFICAS E DIRETÓRIO
# =========================================================================
ASSET_DESTINO_SOLO = 'projects/clima-492922/assets/SICSB_SOLO_2015_2025'

fcBrasil = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
limitesRegiao = fcBrasil.geometry().bounds()

crsNativo = 'EPSG:4326'
transformNativo = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]

def verificar_se_asset_existe(asset_path):
    try:
        ee.data.getAsset(asset_path)
        return True
    except Exception:
        return False

# =========================================================================
# 3. MOTOR DE CÁLCULO ESTATÍSTICO MENSAL (SOBREPOSIÇÃO: 2015 a 2025)
# =========================================================================
print("\n⏳ Preparando as equações de Média e Desvio Padrão para a Umidade do Solo (m³/m³)...")

def gerar_matriz_solo_mes(mes):
    data_inicio = '2015-04-01'
    data_fim = '2026-01-01'

    # COLEÇÃO 1: SMAP L4 (A "Verdade Absoluta" do Presente)
    smap_hist = (ee.ImageCollection("NASA/SMAP/SPL4SMGP/008")
                 .filter(ee.Filter.calendarRange(mes, mes, 'month'))
                 .filterDate(data_inicio, data_fim)
                 .filterBounds(limitesRegiao))

    # COLEÇÃO 2: ERA5-LAND (A base histórica que precisa ser calibrada)
    era5_hist = (ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
                 .filter(ee.Filter.calendarRange(mes, mes, 'month'))
                 .filterDate(data_inicio, data_fim)
                 .filterBounds(limitesRegiao))

    def preparar_smap(img):
        # RUNOFF: Está em kg/m2/s. Multiplica-se por 86400 (segundos do dia) para virar mm/dia.
        rsup = img.select('overland_runoff_flux').multiply(86400).rename('runoff_sup')
        rsub = img.select('baseflow_flux').multiply(86400).rename('runoff_sub')

        # UMIDADE: O SMAP já entrega Fração Volumétrica (m3/m3) de fábrica. (NÃO MULTIPLICAMOS MAIS)
        swat = img.select('sm_rootzone').resample('bilinear').rename('soil_water')
        ssur = img.select('sm_surface').resample('bilinear').rename('soil_surface')

        return ee.Image.cat([rsup, rsub, swat, ssur])

    def preparar_era5(img):
        # RUNOFF: O ERA5 entrega em metros. Multiplica-se por 1000 para virar milímetros (mm).
        rsup = img.select('surface_runoff_sum').multiply(1000).max(0).rename('runoff_sup')
        rsub = img.select('sub_surface_runoff_sum').multiply(1000).max(0).rename('runoff_sub')

        # UMIDADE (0 a 5 cm): Usamos a Layer 1 do ERA5 (0-7cm) como proxy, já em Fração Volumétrica.
        ssur = img.select('volumetric_soil_water_layer_1').resample('bilinear').rename('soil_surface')

        # UMIDADE (0 a 100 cm): Média Ponderada das 3 primeiras camadas do ERA5
        # Layer 1 = 7%, Layer 2 = 21%, Layer 3 = 72% (Total = 100% de 1 metro)
        L1 = img.select('volumetric_soil_water_layer_1').multiply(0.07)
        L2 = img.select('volumetric_soil_water_layer_2').multiply(0.21)
        L3 = img.select('volumetric_soil_water_layer_3').multiply(0.72)
        swat = L1.add(L2).add(L3).resample('bilinear').rename('soil_water')

        return ee.Image.cat([rsup, rsub, swat, ssur])

    # Aplica as regras de padronização nas duas coleções
    smap_limpo = smap_hist.map(preparar_smap)
    era5_limpo = era5_hist.map(preparar_era5)

    # Calcula Média e Desvio Padrão do SMAP (Sufixo: _smap)
    img_mean_smap = smap_limpo.mean().rename(['rsup_m_smap', 'rsub_m_smap', 'swat_m_smap', 'ssur_m_smap'])
    img_std_smap = smap_limpo.reduce(ee.Reducer.stdDev()).rename(['rsup_s_smap', 'rsub_s_smap', 'swat_s_smap', 'ssur_s_smap'])

    # Calcula Média e Desvio Padrão do ERA5 (Sufixo novo: _era5)
    img_mean_era5 = era5_limpo.mean().rename(['rsup_m_era5', 'rsub_m_era5', 'swat_m_era5', 'ssur_m_era5'])
    img_std_era5 = era5_limpo.reduce(ee.Reducer.stdDev()).rename(['rsup_s_era5', 'rsub_s_era5', 'swat_s_era5', 'ssur_s_era5'])

    # Empacota as 16 matrizes estatísticas em uma única imagem final
    img_final = ee.Image.cat([img_mean_smap, img_std_smap, img_mean_era5, img_std_era5]).toFloat()

    # Rasteriza o limite territorial do GAUL para criar uma máscara de pixels eficiente
    mascara_brasil = ee.Image.constant(1).clipToCollection(fcBrasil).mask()

    # Aplica a máscara e configura o mês de referência
    return img_final.updateMask(mascara_brasil).set('mes_referencia', mes)

# =========================================================================
# 4. DISPARADOR DAS 12 TAREFAS DE SOLO
# =========================================================================
print("\n🚀 Gerando as 12 matrizes-mestre de solo na nuvem...")
tasks_enviadas = []

for mes in range(1, 13):
    str_mes = str(mes).zfill(2)
    nome_asset = f'{ASSET_DESTINO_SOLO}/Matriz_Solo_{str_mes}'

    if verificar_se_asset_existe(nome_asset):
        print(f"⏩ Matriz de solo do mês {str_mes} já existe no servidor. Pulando.")
        continue

    img_mes = gerar_matriz_solo_mes(mes)

    task = ee.batch.Export.image.toAsset(
        image=img_mes,
        description=f'GERAR_MATRIZ_SOLO_{str_mes}',
        assetId=nome_asset,
        region=limitesRegiao,
        crs=crsNativo,
        crsTransform=transformNativo,
        maxPixels=1e13
    )
    task.start()
    tasks_enviadas.append((str_mes, task.id))
    print(f"✔️ Tarefa de calibração de solo para o mês {str_mes} despachada!")

if tasks_enviadas:
    print("\n⏳ Aguardando processamento das 12 imagens mensais pela infraestrutura do Google.")
else:
    print("\n🎉 Todas as matrizes de solo já foram geradas com sucesso.")
