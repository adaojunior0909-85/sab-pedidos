# ⛔⛔⛔ NÃO EXECUTAR: SCRIPT ORIGINAL GUARDADO SÓ COMO REGISTRO DO MÉTODO (metodologia da tese) ⛔⛔⛔
# Gerou: projects/clima-492922/assets/SICSB_1986_2025 (12 imagens Matriz_Clima_MM)
# Hoje: Em uso, só leitura: calibração BR-DWGD × ERA5-Land dos dias provisórios (motor V1.5).
# Substituído por: não substituído
# Por que não rodar: ele RECRIARIA o asset acima; o banco, as calibrações e as validações (K8 a K16, 07a/07b,
#   08) foram aprovados com o asset que já existe. Rodar de novo exigiria refazer e validar tudo.
# Recebido do responsável em 03/11/2026 (scripts_originais_recebidos.txt, linhas 1333 a 1469). Abaixo da linha ORIGINAL, o texto está sem nenhuma
#   mudança. SHA-256 do trecho original: 26c19e51394a4dd1e78c9b7f483ee611565ed8a2783be6a482810190168e781f
# A linha raise SystemExit abaixo faz a célula parar antes de qualquer import ou gravação.
raise SystemExit('⛔ Script original guardado só como registro. NÃO EXECUTAR (veja o cabeçalho).')
# ================================================ ORIGINAL ================================================
# =========================================================================================
# TÍTULO: Motor Gerador da Base Climatológica Histórica (Cérebro do Sistema: 1986 a 2025)
#
# RESUMO DETALHADO DA FUNÇÃO:
# Este código empilha 40 anos de dados (1986 a 2025) do satélite ERA5 e da base
# terrestre (BR-DWGD) e comprime tudo em 12 imagens mensais (Média e Desvio Padrão).
# ATUALIZAÇÃO 1: Correção de OOM delegando clip geométrico e reprojeção para o nó de exportação.
# ATUALIZAÇÃO 2: Ajuste de reamostragem híbrida (Bilinear para contínuas e Nearest Neighbor para chuva).
# =========================================================================================

import ee
import time
import sys

# =========================================================================
# 1. AUTENTICAÇÃO E INICIALIZAÇÃO
# =========================================================================
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
ASSET_DESTINO_CLIMA = 'projects/clima-492922/assets/SICSB_1986_2025'

limitesRegiao = (ee.FeatureCollection("FAO/GAUL/2015/level0")
                 .filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
                 .geometry().bounds())

poligonoBrasil = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_NAME', 'Brazil')).geometry()

colChuvaGeral = ee.ImageCollection('projects/ee-alexandrexavier/assets/BR-DWGD')

crsNativo = 'EPSG:4326'
transformNativo = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]

def verificar_se_asset_existe(asset_path):
    try:
        ee.data.getAsset(asset_path)
        return True
    except Exception:
        return False

# =========================================================================
# 3. MOTOR DE CÁLCULO ESTATÍSTICO MENSAL (40 ANOS: 1986 - 2025)
# =========================================================================
print("\n⏳ Preparando as equações de Média e Desvio Padrão (Base Histórica de 40 Anos)...")

def gerar_matriz_do_mes(mes):
    br_hist = colChuvaGeral.filter(ee.Filter.calendarRange(mes, mes, 'month')).filterDate('1986-01-01', '2026-01-01')
    era_hist = (ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR')
                .filter(ee.Filter.calendarRange(mes, mes, 'month'))
                .filterDate('1986-01-01', '2026-01-01')
                .filterBounds(limitesRegiao))

    def preparar_era(img):
        pr = img.select('total_precipitation_sum').multiply(1000).max(0).rename('pr')
        tmax = img.select('temperature_2m_max').subtract(273.15).resample('bilinear').rename('Tmax')
        tmin = img.select('temperature_2m_min').subtract(273.15).resample('bilinear').rename('Tmin')
        et = img.select('potential_evaporation_sum').multiply(-1000).max(0).resample('bilinear').rename('ET')
        rs = img.select('surface_solar_radiation_downwards_sum').divide(1000000).resample('bilinear').rename('Rs')
        u2 = img.select('u_component_of_wind_10m').hypot(img.select('v_component_of_wind_10m')).multiply(0.748).resample('bilinear').rename('u2')

        t2m = img.select('temperature_2m').subtract(273.15).resample('bilinear')
        tdew = img.select('dewpoint_temperature_2m').subtract(273.15).resample('bilinear')
        rh = t2m.expression('100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))', {'T': t2m, 'Td': tdew}).rename('RH')

        return ee.Image.cat([pr, tmax, tmin, et, rs, u2, rh])

    def limpar_br(img):
        mask = img.select('pr').gt(-32768)
        return ee.Image.cat([
            img.select('pr').updateMask(mask).multiply(0.00686666).add(225.0).max(0).rename('pr'),
            img.select('Tmax').updateMask(mask).multiply(0.00106815).add(15.0).rename('Tmax'),
            img.select('Tmin').updateMask(mask).multiply(0.00106815).add(15.0).rename('Tmin'),
            img.select('RH').updateMask(mask).multiply(0.39370079).add(-0.393701).rename('RH'),
            img.select('u2').updateMask(mask).multiply(0.05905512).add(-0.059055).rename('u2'),
            img.select('Rs').updateMask(mask).multiply(0.15708661).add(-0.057087).rename('Rs'),
            img.select('ET').updateMask(mask).multiply(0.05118110).add(-0.0511811).rename('ET')
        ])

    br_limpo = br_hist.map(limpar_br)
    era_limpo = era_hist.map(preparar_era)

    img_mean_br = br_limpo.mean().rename(['pr_m_br', 'Tmax_m_br', 'Tmin_m_br', 'RH_m_br', 'u2_m_br', 'Rs_m_br', 'ET_m_br'])
    img_std_br = br_limpo.reduce(ee.Reducer.stdDev()).rename(['pr_s_br', 'Tmax_s_br', 'Tmin_s_br', 'RH_s_br', 'u2_s_br', 'Rs_s_br', 'ET_s_br'])

    img_mean_era = era_limpo.mean().rename(['pr_m_era', 'Tmax_m_era', 'Tmin_m_era', 'ET_m_era', 'Rs_m_era', 'u2_m_era', 'RH_m_era'])
    img_std_era = era_limpo.reduce(ee.Reducer.stdDev()).rename(['pr_s_era', 'Tmax_s_era', 'Tmin_s_era', 'ET_s_era', 'Rs_s_era', 'u2_s_era', 'RH_s_era'])

    # Correção: Remoção total do reproject e clip desta etapa intermédia.
    return (ee.Image.cat([img_mean_br, img_std_br, img_mean_era, img_std_era])
            .toFloat()
            .set('mes_referencia', mes))

# =========================================================================
# 4. DISPARADOR DAS 12 TAREFAS COM PROTEÇÃO CONTRA DUPLICIDADE
# =========================================================================
print("\n🚀 Gerando as 12 matrizes-mestre na nuvem (modo seguro ativado)...")
tasks_enviadas = []

for mes in range(1, 13):
    str_mes = str(mes).zfill(2)
    nome_asset = f'{ASSET_DESTINO_CLIMA}/Matriz_Clima_{str_mes}'

    if verificar_se_asset_existe(nome_asset):
        print(f"⏩ Matriz do mês {str_mes} já existe no servidor. Pulando para evitar recálculo.")
        continue

    img_mes = gerar_matriz_do_mes(mes)

    task = ee.batch.Export.image.toAsset(
        image=img_mes,
        description=f'GERAR_MATRIZ_CLIMA_40A_{str_mes}',
        assetId=nome_asset,
        region=poligonoBrasil, # Correção: Polígono exato definido apenas no momento da exportação.
        crs=crsNativo,
        crsTransform=transformNativo,
        maxPixels=1e13
    )
    task.start()
    tasks_enviadas.append((str_mes, task.id))
    print(f"✔️ Nova tarefa com recorte exato para o mês {str_mes} enviada com sucesso!")

# =========================================================================
# 5. MONITORAMENTO
# =========================================================================
if tasks_enviadas:
    print("\n⏳ Aguardando o Google Earth Engine compilar os 40 anos de histórico com o recorte da fronteira...")
    print("⚠️ (Você pode fechar esta aba/terminal e acompanhar o andamento pela aba 'Tasks' no Earth Engine Code Editor na web).")
else:
    print("\n🎉 Processo concluído. Todas as matrizes já estavam salvas e foram preservadas.")
