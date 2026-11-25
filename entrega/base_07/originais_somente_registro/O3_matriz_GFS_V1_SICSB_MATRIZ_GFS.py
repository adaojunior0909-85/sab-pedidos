# ⛔⛔⛔ NÃO EXECUTAR: SCRIPT ORIGINAL GUARDADO SÓ COMO REGISTRO DO MÉTODO (metodologia da tese) ⛔⛔⛔
# Gerou: projects/clima-492922/assets/SICSB_MATRIZ_GFS (V1)
# Hoje: Sem uso: referência da 04 e da 08 (comparação com a V2.1).
# Substituído por: 03_matriz_gfs_v2_1.py (SICSB_MATRIZ_GFS_V2)
# Por que não rodar: ele RECRIARIA o asset acima; o banco, as calibrações e as validações (K8 a K16, 07a/07b,
#   08) foram aprovados com o asset que já existe. Rodar de novo exigiria refazer e validar tudo.
# Recebido do responsável em 03/11/2026 (scripts_originais_recebidos.txt, linhas 1471 a 1662). Abaixo da linha ORIGINAL, o texto está sem nenhuma
#   mudança. SHA-256 do trecho original: 8c3bf73ddbe50555f82985431eb2907d28826a1889094a1f5d54a0996ca38099
# A linha raise SystemExit abaixo faz a célula parar antes de qualquer import ou gravação.
raise SystemExit('⛔ Script original guardado só como registro. NÃO EXECUTAR (veja o cabeçalho).')
# ================================================ ORIGINAL ================================================
# =========================================================================================
# TÍTULO: Script 3 - Motor Gerador da Base de Calibração Preditiva (GFS x SICSB)
# RESUMO: Processa 10 anos de rodadas diárias do GFS (2015-2025), desacumula
# variáveis de fluxo, ajusta parâmetros pela FAO-56 e exporta a matriz Z-Score com 14
# bandas mensais para a calibração operacional do futuro SICSB.
# =========================================================================================

import ee
import time
import math

print("🔄 Conectando à infraestrutura do Google Earth Engine...")
try:
    ee.Initialize(project='clima-492922')
    print("✔️ Google Earth Engine inicializado com sucesso!")
except Exception:
    ee.Authenticate()
    ee.Initialize(project='clima-492922')

# =========================================================================
# 1. CONFIGURAÇÕES ESPACIAIS E DE DIRETÓRIO
# =========================================================================
ASSET_SICSB_REAL = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ASSET_DESTINO_MATRIZ_GFS = 'projects/clima-492922/assets/SICSB_MATRIZ_GFS'

poligonoBrasil = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_NAME', 'Brazil')).geometry()
limitesRegiao = poligonoBrasil.bounds()

crsNativo = 'EPSG:4326'
transformNativo = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]

try:
    ee.data.createAsset({'type': 'ImageCollection'}, ASSET_DESTINO_MATRIZ_GFS)
    print("✔️ Pasta de destino criada.")
except Exception:
    pass

def verificar_se_asset_existe(asset_path):
    try:
        ee.data.getAsset(asset_path)
        return True
    except Exception:
        return False

# =========================================================================
# 2. MOTOR DE REDUÇÃO MENSAL ESTATÍSTICA (GFS VS SICSB)
# =========================================================================
print("\n⏳ Preparando equações paramétricas para janela 2015-2025...")

def gerar_matriz_gfs_mes(mes):
    data_inicio = '2015-08-01'
    data_fim = '2025-12-31'

    mes_filtro = ee.Filter.calendarRange(mes, mes, 'month')

    # A) BASE GABARITO (Verdade Histórica)
    sicsb_hist = ee.ImageCollection(ASSET_SICSB_REAL) \
        .filterDate(data_inicio, data_fim) \
        .filter(mes_filtro)

    def extrair_sicsb(img):
        # Seleciona as bandas corretas da base BR-DWGD e aplica os fatores de escala e offset
        pr = img.select('pr').multiply(0.00686666).add(225.0)
        tmax = img.select('Tmax').multiply(0.00106815).add(15.0)
        tmin = img.select('Tmin').multiply(0.00106815).add(15.0)
        rh = img.select('RH').multiply(0.39370079).add(-0.393701)
        u2 = img.select('u2').multiply(0.05905512).add(-0.059055)
        rs = img.select('Rs').multiply(0.15708661).add(-0.057087)
        et = img.select('ET').multiply(0.05118110).add(-0.0511811)

        return ee.Image.cat([pr, tmax, tmin, rh, u2, rs, et]) \
            .rename(['pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs', 'ET']) \
            .set('system:time_start', img.get('system:time_start'))

    sicsb_limpo = sicsb_hist.map(extrair_sicsb)

    # B) BASE PREDITIVA BRUTA (Modelo GFS Histórico)
    gfs_raw = ee.ImageCollection('NOAA/GFS0P25') \
        .filterBounds(limitesRegiao) \
        .filterDate(data_inicio, data_fim)

    # Função de emparelhamento estrutural com blindagem contra falhas do catálogo NOAA
    def processar_gfs_emparelhado(img_sicsb):
        data_ms = img_sicsb.date().millis()

        # Isola a rodada gerada exatamente à meia-noite do dia correspondente
        rodada = gfs_raw.filter(ee.Filter.eq('creation_time', data_ms)) \
                        .filter(ee.Filter.gt('forecast_hours', 0)) \
                        .filter(ee.Filter.lte('forecast_hours', 24))

        # Trava de segurança: conta as imagens da rodada para prevenir colapso estatístico
        tamanho_rodada = rodada.size()

        def rodada_valida():
            # 1. Temperatura: Extração de máximas e mínimas sobre a pilha de 24h
            t_base = rodada.select('temperature_2m_above_ground')
            tmax_gfs = t_base.max().rename('Tmax')
            tmin_gfs = t_base.min().rename('Tmin')

            # 2. Precipitação: Soma estrita dos blocos cumulativos para fechar 24h sem dupla contagem
            chuva_blocos = rodada.filter(ee.Filter.inList('forecast_hours', [6, 12, 18, 24]))
            pr_gfs = chuva_blocos.select('total_precipitation_surface').sum().max(0).rename('pr')

            # 3. Umidade e Radiação Solar incidente
            rh_gfs = rodada.select('relative_humidity_2m_above_ground').mean().clamp(0, 100).rename('RH')
            rs_gfs = rodada.select('downward_shortwave_radiation_flux').mean().multiply(0.0864).max(0).rename('Rs')

            # 4. Vento com ajuste logarítmico FAO-56
            def calc_u2(img):
                u = img.select('u_component_of_wind_10m_above_ground')
                v = img.select('v_component_of_wind_10m_above_ground')
                u2 = u.hypot(v).multiply(0.748).rename('u2')
                return img.addBands(u2)

            u2_gfs = rodada.map(calc_u2).select('u2').mean()

            # 5. Evapotranspiração FAO-56 Hargreaves (Cálculo Astronômico de Ra)
            J = img_sicsb.date().getRelative('day', 'year').add(1).toDouble()
            lat = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180.0)

            dr = J.multiply(2 * math.pi / 365).cos().multiply(0.033).add(1)
            delta = J.multiply(2 * math.pi / 365).subtract(1.39).sin().multiply(0.409)

            ws_arg = lat.tan().multiply(-1).multiply(delta.tan()).clamp(-1.0, 1.0)
            ws = ws_arg.acos()

            term1 = ws.multiply(lat.sin()).multiply(delta.sin())
            term2 = lat.cos().multiply(delta.cos()).multiply(ws.sin())

            # Inversão da ordem de multiplicação para respeitar a tipagem (Image x Number)
            Ra = term1.add(term2).multiply(dr).multiply((24 * 60 / math.pi) * 0.0820)

            tmedia = tmax_gfs.add(tmin_gfs).divide(2)
            et_gfs = tmedia.add(17.8).multiply(tmax_gfs.subtract(tmin_gfs).max(0).sqrt()).multiply(0.0023).multiply(Ra).rename('ET')

            return ee.Image.cat([pr_gfs, tmax_gfs, tmin_gfs, rh_gfs, u2_gfs, rs_gfs, et_gfs]) \
                .set('system:time_start', data_ms) \
                .resample('bicubic')

        def rodada_vazia():
            # Injeta imagem vazia perfeitamente nomeada e mascarada para o GEE ignorar no cálculo de média
            vazio = ee.Image.constant([0, 0, 0, 0, 0, 0, 0]) \
                .rename(['pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs', 'ET']) \
                .updateMask(ee.Image.constant(0)) \
                .set('system:time_start', data_ms)
            return vazio

        return ee.Image(ee.Algorithms.If(tamanho_rodada.gt(0), rodada_valida(), rodada_vazia()))

    gfs_limpo = sicsb_hist.map(processar_gfs_emparelhado)

    # C) CÁLCULO ESTATÍSTICO Z-SCORE
    sicsb_mean = sicsb_limpo.mean().rename(['pr_m_sicsb', 'Tmax_m_sicsb', 'Tmin_m_sicsb', 'RH_m_sicsb', 'u2_m_sicsb', 'Rs_m_sicsb', 'ET_m_sicsb'])
    sicsb_std = sicsb_limpo.reduce(ee.Reducer.stdDev()).rename(['pr_s_sicsb', 'Tmax_s_sicsb', 'Tmin_s_sicsb', 'RH_s_sicsb', 'u2_s_sicsb', 'Rs_s_sicsb', 'ET_s_sicsb'])

    gfs_mean = gfs_limpo.mean().rename(['pr_m_gfs', 'Tmax_m_gfs', 'Tmin_m_gfs', 'RH_m_gfs', 'u2_m_gfs', 'Rs_m_gfs', 'ET_m_gfs'])
    gfs_std = gfs_limpo.reduce(ee.Reducer.stdDev()).rename(['pr_s_gfs', 'Tmax_s_gfs', 'Tmin_s_gfs', 'RH_s_gfs', 'u2_s_gfs', 'Rs_s_gfs', 'ET_s_gfs'])

    matriz_final = ee.Image.cat([sicsb_mean, sicsb_std, gfs_mean, gfs_std]).toFloat()

    mascara_brasil = ee.Image.constant(1).clipToCollection(ee.FeatureCollection([poligonoBrasil])).mask()
    return matriz_final.updateMask(mascara_brasil).set('mes_referencia', mes)

# =========================================================================
# 3. DISPARADOR DAS 12 TAREFAS MENSAIS
# =========================================================================
print("\n🚀 Empacotando e exportando as 12 matrizes preditivas...")

for mes in range(1, 13):
    str_mes = str(mes).zfill(2)
    nome_asset = f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{str_mes}'

    if verificar_se_asset_existe(nome_asset):
        print(f"⏩ Matriz do mês {str_mes} já identificada no Google. Pulando.")
        continue

    img_mes = gerar_matriz_gfs_mes(mes)

    task = ee.batch.Export.image.toAsset(
        image=img_mes,
        description=f'GERAR_MATRIZ_GFS_{str_mes}',
        assetId=nome_asset,
        region=poligonoBrasil,
        crs=crsNativo,
        crsTransform=transformNativo,
        maxPixels=1e13
    )
    task.start()
    print(f"✔️ Missão enviada para a nuvem: Calibração GFS Mês {str_mes}.")
    time.sleep(2)

print("\n🎉 Todas as rodadas de construção da arquitetura foram acionadas.")
