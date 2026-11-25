# ⛔⛔⛔ NÃO EXECUTAR: SCRIPT ORIGINAL GUARDADO SÓ COMO REGISTRO DO MÉTODO (metodologia da tese) ⛔⛔⛔
# Gerou: projects/clima-492922/assets/Baselines (48 imagens B1.1: normais e limiares 1961–1990 e 1991–2020)
# Hoje: Em uso, só leitura. É o "Código baselines.txt": NUNCA rodar. A conferência é pelo 07a/07b (mesmo cálculo, travado).
# Substituído por: 07a/07b_normais_CONFERIR (só conferem)
# Por que não rodar: ele RECRIARIA o asset acima; o banco, as calibrações e as validações (K8 a K16, 07a/07b,
#   08) foram aprovados com o asset que já existe. Rodar de novo exigiria refazer e validar tudo.
# Recebido do responsável em 03/11/2026 (scripts_originais_recebidos.txt, linhas 1803 a 3089). Abaixo da linha ORIGINAL, o texto está sem nenhuma
#   mudança. SHA-256 do trecho original: e2eeb998b96e7210e398619eb6ede662bd4ac97c0a7449ff046a8ce0aa2cca36
# A linha raise SystemExit abaixo faz a célula parar antes de qualquer import ou gravação.
raise SystemExit('⛔ Script original guardado só como registro. NÃO EXECUTAR (veja o cabeçalho).')
# ================================================ ORIGINAL ================================================
# =========================================================================================
# TÍTULO: NORMAIS CLIMATOLÓGICAS SAB (BASELINES 1961-1990 E 1991-2020) - VERSÃO B1.1
# RESUMO DA FUNÇÃO: gera, a partir do banco SAB_V1, as normais mensais e os limiares de
# extremos que o Painel SAB usa para anomalias, categorias de chuva, SPI, SPEI, eventos e o
# diagnóstico agrícola. Roda no Colab, como o motor.
#
# ATUALIZAÇÃO B1.1 (diagnóstico agrícola; as normais ainda não tinham sido exportadas)
#   - Variáveis novas com normal própria: temperatura média, graus-dia (base 10 °C, teto 30 °C,
#     como o painel), balanço hídrico climático (chuva menos ETo), dias com chuva de 1, 10 e
#     20 mm ou mais, dias de geada (Tmin até 2 °C), dias com Tmin abaixo de 0 °C, maior chuva
#     diária do mês (Rx1day), maior Tmax (TXx) e menor Tmin (TNn) do mês
#   - SPI de 1, 3 e 6 meses e SPEI de 1 e 3 meses. O SPEI usa a log-logística de 3 parâmetros
#     (Vicente-Serrano et al. 2010) na forma logística generalizada de Hosking, ajustada por
#     momentos-L não viciados, que é como o pacote SPEI do R calcula hoje (pelglo e cdfglo).
#     Na forma original o ajuste falha onde a assimetria da série é negativa ou nula
#   - Percentis 95 e 99 da chuva nos dias com chuva (limiar de chuva intensa do mês)
#   - Limiares diários também do P10 da Tmax (dias frescos) e do P90 da Tmin (noites quentes)
#   - Conferência revista (07/10/2026): a série diária dos pontos é lida BRUTA do banco e a
#     leitura do painel (correção V1.0 de solo e escoamento, ET real <= ETo, bandas derivadas)
#     é refeita aqui em pandas. Pedir os dias já corrigidos ao Earth Engine estourava a memória
#     ("User memory limit exceeded"), porque a correção usa reproject e focalMean em cada dia.
#     Se ainda assim o Earth Engine recusar, a leitura é feita em blocos menores de período e
#     de pontos. As normais e os limiares exportados não mudam
#
# O QUE MUDOU EM RELAÇÃO AO SCRIPT ANTERIOR DAS BASELINES
#   - Origem: SAB_V1 (o banco que o motor grava e o painel lê), e não SICSB
#   - Cada dia é lido exatamente como o painel lê: nomes antigos de banda tratados, correção de
#     umidade do solo e escoamento nos dias V1.0 (corrigirSoloEscoamentoV10), ET real limitada
#     à ETo e transpiração limitada à ET real. Sem isso a normal de solo e escoamento sairia dos
#     valores impossíveis do acervo V1.0 e a anomalia teria viés
#   - Regra dos 80% aplicada sobre ANOS, como manda a OMM (WMO-No. 1203, 2017):
#       * total mensal (chuva, ETo, ET real, escoamento, contagens): só com o mês completo
#       * média mensal (temperaturas, UR, vento, radiação, umidade do solo): no máximo 4 dias
#         faltando, o que garante a regra da OMM (menos de 11 faltas e menos de 5 seguidas)
#       * normal: só onde há pelo menos 24 dos 30 anos válidos
#     O script anterior contava DIAS (count() da coleção diária), então a máscara de 24
#     nunca cortava nada
#   - Desvio-padrão ENTRE ANOS (dos totais e médias de cada mês), amostral (n-1). O anterior
#     misturava a variação de um dia para o outro com a de um ano para o outro
#   - Chuva: quintis e tercis interanuais pelo método da OMM (posto 1 + k(n-1)/q, interpolação
#     linear) e parâmetros da distribuição gama para o SPI de 1 e de 3 meses
#   - Calor e frio: limiar diário por percentil com janela de 5 dias centrada em cada dia do
#     calendário (TX90 e TN10, padrão ETCCDI), no lugar de média + desvio
#   - Grade idêntica à do banco (mesma crsTransform de 0,1°), sem reamostragem
#   - Uma imagem por mês em coleções próprias (12 tarefas leves em vez de uma com 576 bandas)
#   - Modo simulação: inventário do banco e conferência dos números do Earth Engine contra um
#     cálculo independente feito aqui, em pontos de referência, antes de exportar
#
# SAÍDAS (pasta projects/clima-492922/assets/Baselines)
#   Normais_Operacional_1991_2020 / Normais_Historico_1961_1990 (12 imagens, propriedade 'mes')
#     {var}_media, {var}_dp, {var}_n para 33 variáveis (16 do banco, 6 derivadas, 8 contagens
#     de dias e 3 extremos do mês), pr_mm_q20..q80, pr_mm_t33/t67, pr_mm_mediana,
#     tmax/tmin_C_t33/t67, spi1/3/6_* (alfa, beta, q0, n), spei1/3_* (xi, alfa, kappa, n),
#     pr_p95_umido, pr_p99_umido, n_dias_umidos
#   Limiares_Operacional_1991_2020 / Limiares_Historico_1961_1990 (12 imagens)
#     tx90_dDD, tx10_dDD (P90 e P10 da Tmax), tn90_dDD, tn10_dDD (P90 e P10 da Tmin) para cada
#     dia DD do mês (fevereiro vai até o dia 28; o painel usa o dia 28 para 29/02)
#
# COMO RODAR
#   1. SIMULAR = True (padrão): nada é criado. Mostra o inventário, as tarefas que seriam
#      enviadas e a conferência numérica. Só siga se todos os critérios saírem ✅
#   2. SIMULAR = False com PILOTO = True: cria a pasta e as coleções e envia só o mês 01 de
#      normais e de limiares; no fim mostra minutos e EECU-horas de cada tarefa e a projeção
#      para as 48. Rode depois que as tarefas do motor (SAB_M_...) terminarem: a fila é a mesma
#   3. PILOTO = False: envia o restante (o que já existe é pulado)
#   4. Quando as tarefas terminarem, rode de novo com SIMULAR = True: a conferência passa a
#      comparar também os assets gravados
#   5. Na aba Assets, compartilhe as quatro coleções como o SAB_V1 (leitura pública), senão
#      quem abre o painel publicado não enxerga as normais
#
# LIMITAÇÕES CONHECIDAS (registradas para a nota técnica)
#   - Década de 1960: a menos confiável do BR-DWGD (menos estações); pesa só na 1961-1990
#   - Solo, escoamento e ET real do histórico vêm do ERA5-Land calibrado; a chuva vem do
#     BR-DWGD. O balanço hídrico do banco não fecha (resíduo de cerca de 400 mm/ano)
#   - Limiares de extremos sem o bootstrap do ETCCDI: a frequência de dias acima do P90 fica um
#     pouco diferente dentro e fora da normal (Zhang et al., 2005), o que cria um pequeno degrau
#     em séries que atravessam o início ou o fim do período da normal
#   - O percentil diário usa o cálculo direto do Earth Engine sobre os ~150 valores da janela;
#     a conferência mostra a diferença para o tipo 8 do climdex (fração de grau)
#   - Normais não usam 2026; a troca dos provisórios para a V1.3 não as afeta
# =========================================================================================

import calendar
import math
import time
from datetime import date, datetime, timedelta, timezone

import ee
import numpy as np
import pandas as pd

# =========================================================================
# 1. CONFIGURAÇÃO
# =========================================================================
PROJETO = 'clima-492922'
ASSET_ORIGEM = f'projects/{PROJETO}/assets/SAB_V1'
PASTA_DESTINO = f'projects/{PROJETO}/assets/Baselines'
ASSET_SOLO = f'projects/{PROJETO}/assets/SICSB_SOLO_2015_2025'   # mesma matriz do painel

VERSAO_BASELINE = 'B1.1'
# True: só lê e confere; nada é criado, apagado ou exportado. Rode assim primeiro.
SIMULAR = False
VERIFICAR = True                 # conferência numérica (só no modo simulação)
MESES_VERIFICACAO = (1,)         # janeiro testa a virada de ano do SPI-3 e da janela dos limiares
DIAS_VERIFICACAO = (1, 15)       # dias dos limiares conferidos
PERIODO_VERIFICACAO = '1991_2020'
PERIODOS_A_GERAR = ['1991_2020', '1961_1990']   # o painel usa 1991-2020 por padrão
MESES_A_GERAR = list(range(1, 13))
GERAR_LIMIARES = True
# True (recomendado na primeira execução real): envia só o mês 01 de normais e de limiares,
# acompanha as duas tarefas e mostra tempo e consumo de EECU, com a projeção para o restante.
# Desde abril de 2026 os projetos não comerciais têm cota mensal de EECU-horas (lote e
# interativo somados); passar dela deixa motor, painel e tarefas mais lentos até o dia 1º.
PILOTO = False
SOBRESCREVER = False             # True: regrava meses já exportados
ESPERAR_MOTOR = True             # não envia nada enquanto houver tarefas do motor na fila
ACOMPANHAR = True                # acompanha as tarefas depois de enviar (pode interromper)
INTERVALO_ACOMPANHAMENTO_S = 120

PERIODOS = {
    '1961_1990': {'anos': (1961, 1990), 'nome': 'Historico'},
    '1991_2020': {'anos': (1991, 2020), 'nome': 'Operacional'},
}

# Pontos de referência da conferência (o centro do pixel do banco é usado)
PONTOS_REFERENCIA = [
    ('Pato Branco-PR', -26.23, -52.67),
    ('Porto Alegre-RS', -30.03, -51.23),
    ('Brasilia-DF', -15.79, -47.88),
    ('Petrolina-PE', -9.39, -40.50),
    ('Manaus-AM', -3.10, -60.02),
]

# =========================================================================
# 2. REGRAS E CONSTANTES
# =========================================================================
ANOS_MINIMOS = 24                # OMM: pelo menos 80% dos 30 anos
FALTAS_MAX_MEDIA = 4             # média e extremos mensais válidos com até 4 dias faltando
LIMIAR_ZERO_CHUVA_MM = 0.1       # total abaixo disso conta como zero no SPI (igual no painel)
MIN_ANOS_COM_CHUVA_SPI = 10      # menos anos com chuva que isso: gama não é ajustada
MIN_DIAS_UMIDOS = 20             # menos dias com chuva nos 30 anos: P95/P99 não são calculados
JANELA_LIMIARES = 2              # ±2 dias: janela de 5 dias do ETCCDI
FRACAO_MIN_JANELA = 0.8          # limiar só com pelo menos 80% dos dias da janela
# Limiares fixos, os mesmos do painel (CFG): dia seco/chuvoso, frio, geada, calor, graus-dia
LIMIAR_DIA_SECO = 1.0            # seco: chuva < 1 mm; chuvoso: >= 1 mm (elemento da OMM)
LIMIAR_CHUVA_10 = 10.0           # ETCCDI R10mm
LIMIAR_CHUVA_20 = 20.0           # ETCCDI R20mm
LIMIAR_FRIO = 4.0
LIMIAR_GEADA = 2.0               # Tmin do abrigo até 2 °C: risco de geada na superfície
LIMIAR_TMIN_0 = 0.0              # ETCCDI FD (Tmin < 0 °C)
LIMIAR_CALOR = 35.0
TBASE_GD = 10.0                  # graus-dia: temperatura-base inferior
TSUP_GD = 30.0                   # graus-dia: temperatura-base superior
# Correção de leitura da V1.0 (mesmos valores do motor V1.3 e do painel)
FATOR_MAX = 5.0
UMIDADE_MAX_FISICA = 0.9
SIGMAS_TETO_UMIDADE = 3.0
SENTINELA = 1e30                 # valor posto no lugar dos anos inválidos antes de ordenar

BANDAS_SAB = [
    'pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd',
    'rs', 'u2', 'tsolo_C', 'tfolha_C', 'transpiracao_mm',
    'runoff_sup_mm', 'runoff_sub_mm',
    'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3',
]
NOMES_ANTIGOS = [
    'precipitation_mm', 'temp_max_C', 'temp_min_C', 'relative_humidity_pct',
    'et_potential_mm', 'et_actual_mm', 'vpd_kpa', 'solar_radiation_mj_m2',
    'wind_speed_m_s', 'soil_temperature_C', 'skin_temperature_C',
    'transpiration_mm', 'surface_runoff_mm', 'subsurface_runoff_mm',
    'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3',
]
# Mesmos grupos do CSV mensal do painel (bandasSoma e bandasMedia), mais derivadas e contagens
VARS_SOMA = ['pr_mm', 'chuva_efetiva', 'runoff_sup_mm', 'runoff_sub_mm', 'et_potencial', 'et_real',
             'transpiracao_mm', 'deficit_diario', 'balanco_hidrico', 'graus_dia']
VARS_CONTAGEM = ['dias_chuva_1mm', 'dias_secos', 'dias_chuva_10mm', 'dias_chuva_20mm',
                 'dias_frios', 'dias_geada', 'dias_tmin_0', 'dias_calor']
VARS_MEDIA = ['tmax_C', 'tmin_C', 'tmed_C', 'RH', 'rs', 'u2', 'tsolo_C', 'tfolha_C', 'vpd',
              'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3', 'amplitude_diaria']
# Extremos do mês: (nome, banda diária de origem, redutor)
VARS_EXTREMO = [('rx1day', 'pr_mm', 'max'), ('txx', 'tmax_C', 'max'), ('tnn', 'tmin_C', 'min')]
VARS_TOTAL = VARS_SOMA + VARS_CONTAGEM          # regra do mês completo
VARS_DIA = VARS_TOTAL + VARS_MEDIA              # bandas de cada dia depois da leitura
VARS_MES = VARS_DIA + [v for v, _, _ in VARS_EXTREMO]   # 33 variáveis, nesta ordem em todo o script

# Quantis interanuais (tipo 7 de Hyndman e Fan = método da OMM para quintis)
QUANTIS_CHUVA = [(0.2, 'pr_mm_q20'), (0.4, 'pr_mm_q40'), (0.6, 'pr_mm_q60'), (0.8, 'pr_mm_q80'),
                 (1 / 3, 'pr_mm_t33'), (2 / 3, 'pr_mm_t67'), (0.5, 'pr_mm_mediana')]
TERCIS_TEMP = [(1 / 3, 't33'), (2 / 3, 't67')]
ESCALAS_SPI = (1, 3, 6)          # meses acumulados do SPI (chuva)
ESCALAS_SPEI = (1, 3)            # meses acumulados do SPEI (chuva menos ETo)
KAPPA_MINIMO = 1e-4              # |kappa| menor que isso vira 1e-4: evita 0/0 nas fórmulas da logística

CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]

agora_brt = datetime.now(timezone(timedelta(hours=-3))).strftime('%Y-%m-%d %H:%M')

# =========================================================================
# 3. CONEXÃO E OBJETOS GLOBAIS
# =========================================================================
print(f"🔄 Normais SAB {VERSAO_BASELINE} | projeto {PROJETO} | {agora_brt} (BRT)")
try:
    ee.Initialize(project=PROJETO)
except Exception:
    print("🔗 Autorização do Earth Engine necessária: siga o link que vai aparecer.")
    ee.Authenticate()
    ee.Initialize(project=PROJETO)

_gaul_br = ee.FeatureCollection('FAO/GAUL/2015/level0').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
limitesRegiao = _gaul_br.geometry().bounds()     # mesma região de exportação do motor


def asset_colecao(tipo, p):
    prefixo = 'Normais' if tipo == 'normais' else 'Limiares'
    return f"{PASTA_DESTINO}/{prefixo}_{PERIODOS[p]['nome']}_{p}"


def nome_imagem(tipo, p, mes):
    prefixo = 'Normais' if tipo == 'normais' else 'Limiares'
    return f'{prefixo}_{p}_M{mes:02d}'


def descricao_tarefa(tipo, p, mes):
    return f"SAB_{'NORMAIS' if tipo == 'normais' else 'LIMIARES'}_{p}_M{mes:02d}"


def dias_medios_mes(a0, a1, mes):
    return sum(calendar.monthrange(a, mes)[1] for a in range(a0, a1 + 1)) / (a1 - a0 + 1)


# =========================================================================
# 4. LEITURA DE CADA DIA EXATAMENTE COMO O PAINEL
# =========================================================================
def expandir_borda(img):
    return img.unmask(img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMean(1, 'square', 'pixels'))


def montar_correcao_mes(mes):
    """Igual a montarCorrecaoMes do painel (e à regra de aplicarPatch_Solo do motor)."""
    solo = ee.Image(f'{ASSET_SOLO}/Matriz_Solo_{mes:02d}')

    def fator(p):
        f = expandir_borda(solo.select(f'{p}_m_smap')).divide(
            expandir_borda(solo.select(f'{p}_m_era5')).max(1e-3))
        return (ee.Image.constant(1)
                .where(f.gt(FATOR_MAX).unmask(0), ee.Image.constant(FATOR_MAX).divide(f))
                .unmask(1))

    def teto(p):
        return (expandir_borda(solo.select(f'{p}_m_smap'))
                .add(expandir_borda(solo.select(f'{p}_s_smap')).multiply(SIGMAS_TETO_UMIDADE))
                .min(UMIDADE_MAX_FISICA).unmask(UMIDADE_MAX_FISICA))

    return ee.Image.cat([
        fator('rsup').rename('c_rsup'), fator('rsub').rename('c_rsub'),
        fator('ssur').rename('c_ssur'), fator('swat').rename('c_swat'),
        teto('ssur').rename('teto_ssur'), teto('swat').rename('teto_swat'),
    ])


def padronizar_nomes(img):
    """Como getSABCollection: aceita imagens com os nomes antigos de banda."""
    return ee.Image(ee.Algorithms.If(
        img.bandNames().contains('precipitation_mm'),
        img.select(NOMES_ANTIGOS, BANDAS_SAB),
        img.select(BANDAS_SAB)))


def preparar_dia(img, corr):
    """getSABCollection + corrigirSoloEscoamentoV10 + grampo termodinâmico do painel, mais as
    bandas derivadas que o painel calcula (amplitude, déficit, chuva efetiva, contagens)."""
    base = padronizar_nomes(img)
    alg = ee.String(ee.Algorithms.If(img.propertyNames().contains('versao_algoritmo'),
                                     img.get('versao_algoritmo'), 'V1.0'))
    corrigidas = ee.Image.cat([
        base.select('runoff_sup_mm').multiply(corr.select('c_rsup')).rename('runoff_sup_mm'),
        base.select('runoff_sub_mm').multiply(corr.select('c_rsub')).rename('runoff_sub_mm'),
        base.select('soil_moisture_0_5cm_m3_m3').multiply(corr.select('c_ssur'))
            .min(corr.select('teto_ssur')).rename('soil_moisture_0_5cm_m3_m3'),
        base.select('soil_moisture_0_100cm_m3_m3').multiply(corr.select('c_swat'))
            .min(corr.select('teto_swat')).rename('soil_moisture_0_100cm_m3_m3'),
    ]).toFloat()
    # Só os dias da V1.0 recebem a correção (dias V1.2, V1.3 e patch já vêm corrigidos)
    base = ee.Image(ee.Algorithms.If(alg.equals('V1.0'), base.addBands(corrigidas, None, True), base))

    et_pot = base.select('et_potencial')
    et_real = base.select('et_real').min(et_pot).rename('et_real')
    transp = base.select('transpiracao_mm').min(et_real).rename('transpiracao_mm')
    base = base.addBands(ee.Image.cat([et_real, transp]), None, True)

    tmax, tmin, pr = base.select('tmax_C'), base.select('tmin_C'), base.select('pr_mm')
    # Graus-dia (McMaster e Wilhelm, 1997, método 2): Tmax e Tmin limitadas a [TBASE, TSUP]
    gd = (tmax.max(TBASE_GD).min(TSUP_GD).add(tmin.max(TBASE_GD).min(TSUP_GD))
          .divide(2).subtract(TBASE_GD))
    derivadas = ee.Image.cat([
        tmax.add(tmin).divide(2).rename('tmed_C'),
        tmax.subtract(tmin).rename('amplitude_diaria'),
        et_pot.subtract(et_real).max(0).rename('deficit_diario'),
        pr.subtract(base.select('runoff_sup_mm')).max(0).rename('chuva_efetiva'),
        pr.subtract(et_pot).rename('balanco_hidrico'),
        gd.rename('graus_dia'),
        pr.gte(LIMIAR_DIA_SECO).rename('dias_chuva_1mm'),
        pr.lt(LIMIAR_DIA_SECO).rename('dias_secos'),
        pr.gte(LIMIAR_CHUVA_10).rename('dias_chuva_10mm'),
        pr.gte(LIMIAR_CHUVA_20).rename('dias_chuva_20mm'),
        tmin.lte(LIMIAR_FRIO).rename('dias_frios'),
        tmin.lte(LIMIAR_GEADA).rename('dias_geada'),
        tmin.lt(LIMIAR_TMIN_0).rename('dias_tmin_0'),
        tmax.gte(LIMIAR_CALOR).rename('dias_calor'),
    ]).toFloat()
    return base.addBands(derivadas).select(VARS_DIA).toFloat()


# Imagens vazias (todo pixel mascarado) somadas a cada mês: um mês sem nenhum dia no banco
# vira "mês inválido" em vez de imagem sem bandas, que quebraria o cálculo
VAZIO_DIA = ee.Image.constant([0] * len(VARS_DIA)).rename(VARS_DIA).toFloat().updateMask(ee.Image.constant(0))
VAZIO_PR_ETO = (ee.Image.constant([0, 0]).rename(['pr_mm', 'et_potencial']).toFloat()
                .updateMask(ee.Image.constant(0)))


# =========================================================================
# 5. VALORES MENSAIS DE CADA ANO (REGRA DA OMM)
# =========================================================================
def agregar_ano_mes(ano, mes, corr):
    """Totais, médias e extremos de um mês de um ano, mascarados onde o mês não é válido."""
    ini = ee.Date.fromYMD(ano, mes, 1)
    fim = ini.advance(1, 'month')
    n_dias = ee.Image.constant(fim.difference(ini, 'day'))
    col = (ee.ImageCollection(ASSET_ORIGEM).filterDate(ini, fim)
           .map(lambda i: preparar_dia(i, corr))
           .merge(ee.ImageCollection([VAZIO_DIA])))
    totais = col.select(VARS_TOTAL).sum()
    medias = col.select(VARS_MEDIA).mean()
    extremos = ee.Image.cat([
        (col.select([orig]).max() if red == 'max' else col.select([orig]).min()).rename(nome)
        for nome, orig, red in VARS_EXTREMO])
    cont = col.select(VARS_DIA).count()
    cont_ext = ee.Image.cat([cont.select([orig]).rename(nome) for nome, orig, _ in VARS_EXTREMO])
    valido = ee.Image.cat([
        cont.select(VARS_TOTAL).eq(n_dias),                                # mês completo
        cont.select(VARS_MEDIA).gte(n_dias.subtract(FALTAS_MAX_MEDIA)),    # até 4 faltas
        cont_ext.gte(n_dias.subtract(FALTAS_MAX_MEDIA)),
    ])
    return ee.Image.cat([totais, medias, extremos]).updateMask(valido).set('ano', ano)


def total_mes_chuva_eto(ini):
    """Totais de chuva e de ETo de um mês; cada um só existe com o mês completo."""
    fim = ini.advance(1, 'month')
    n_dias = ee.Image.constant(fim.difference(ini, 'day'))
    col = (ee.ImageCollection(ASSET_ORIGEM).filterDate(ini, fim)
           .map(lambda i: padronizar_nomes(i).select(['pr_mm', 'et_potencial']))
           .merge(ee.ImageCollection([VAZIO_PR_ETO])))
    return col.sum().updateMask(col.count().eq(n_dias))


def totais_indices(ano, mes):
    """Chuva acumulada em 1, 3 e 6 meses (SPI) e chuva menos ETo em 1 e 3 meses (SPEI),
    terminando no mês dado; o acumulado só existe se todos os meses estiverem completos."""
    ini = ee.Date.fromYMD(ano, mes, 1)
    meses = [total_mes_chuva_eto(ini.advance(-k, 'month')) for k in range(max(ESCALAS_SPI + ESCALAS_SPEI))]
    pr = [t.select('pr_mm') for t in meses]
    d = [t.select('pr_mm').subtract(t.select('et_potencial')) for t in meses]

    def soma(lista):
        tot = lista[0]
        for x in lista[1:]:
            tot = tot.add(x)
        return tot

    return ee.Image.cat([soma(pr[:k]).rename(f'pr_{k}m') for k in ESCALAS_SPI] +
                        [soma(d[:k]).rename(f'd_{k}m') for k in ESCALAS_SPEI]).set('ano', ano)


# =========================================================================
# 6. ESTATÍSTICAS ENTRE ANOS
# =========================================================================
def quantis_por_posto(col, banda, probs_nomes, n_min):
    """Quantis exatos pelo tipo 7 (posto (n-1)p, interpolação linear), o método que a OMM
    recomenda para quintis. Anos inválidos viram SENTINELA e ficam no fim da ordenação."""
    serie = col.select([banda])
    n = serie.count().toFloat()
    ordenado = serie.map(lambda i: i.unmask(SENTINELA)).toBands().toArray().arraySort()
    ultimo = n.subtract(1).max(0)
    saidas = []
    for p, nome in probs_nomes:
        h = n.subtract(1).multiply(p).max(0).min(ultimo)
        lo = h.floor()
        hi = lo.add(1).min(ultimo)
        frac = h.subtract(lo)
        v_lo = ordenado.arrayGet(lo.toInt())
        v_hi = ordenado.arrayGet(hi.toInt())
        saidas.append(v_lo.add(v_hi.subtract(v_lo).multiply(frac))
                      .updateMask(n.gte(n_min)).rename(nome))
    return ee.Image.cat(saidas)


def parametros_gama(col, banda, prefixo):
    """Gama para o SPI (McKee et al., 1993) pela aproximação de máxima verossimilhança de Thom:
    A = ln(média) - média(ln), alfa = (1 + raiz(1 + 4A/3)) / 4A, beta = média / alfa,
    ajustada só aos anos com chuva; q0 = fração de anos sem chuva."""
    serie = col.select([banda])
    n = serie.count().toFloat()
    positivos = serie.map(lambda i: i.updateMask(i.gte(LIMIAR_ZERO_CHUVA_MM)))
    n_pos = positivos.count().toFloat()
    media_pos = positivos.mean()
    media_ln = positivos.map(lambda i: i.log()).mean()
    A = media_pos.log().subtract(media_ln)
    alfa = A.multiply(4.0 / 3.0).add(1).sqrt().add(1).divide(A.multiply(4))
    beta = media_pos.divide(alfa)
    q0 = n.subtract(n_pos).divide(n)
    valido = n.gte(ANOS_MINIMOS).And(n_pos.gte(MIN_ANOS_COM_CHUVA_SPI)).And(A.gt(1e-6))
    return ee.Image.cat([
        alfa.updateMask(valido).rename(f'{prefixo}_alfa'),
        beta.updateMask(valido).rename(f'{prefixo}_beta'),
        q0.updateMask(valido).rename(f'{prefixo}_q0'),
        n.rename(f'{prefixo}_n'),
    ])


def parametros_glo(col, banda, prefixo, n_anos):
    """SPEI: log-logística de 3 parâmetros (Vicente-Serrano et al., 2010) escrita como logística
    generalizada de Hosking, a forma do pacote SPEI do R (lmom::pelglo e cdfglo). Momentos-L
    amostrais pelos estimadores não viciados a_s = (1/n) soma C(n-i, s)/C(n-1, s) x_(i):
    l1 = a0, l2 = a0 - 2a1, l3 = a0 - 6a1 + 6a2. Parâmetros (Hosking e Wallis, 1997):
    kappa = -l3/l2, alfa = l2 sen(kappa pi)/(kappa pi), xi = l1 - alfa (1/kappa - pi/sen(kappa pi)).
    Com assimetria positiva é a mesma curva de Vicente-Serrano (beta = -1/kappa); com assimetria
    negativa ou nula, onde a forma original não tem solução, a curva continua definida.
    Cada valor ordenado vira uma banda e os pesos dependem só de n (anos válidos do pixel)."""
    serie = col.select([banda])
    n = serie.count().toDouble()
    nomes = [f'v{i:02d}' for i in range(1, n_anos + 1)]
    ordenado = (serie.map(lambda i: i.toDouble().unmask(SENTINELA)).toBands().toArray().arraySort()
                .arrayFlatten([nomes]))
    a0 = serie.map(lambda i: i.toDouble()).mean()
    a1 = ee.Image.constant(0).toDouble()
    a2 = ee.Image.constant(0).toDouble()
    for i in range(1, n_anos + 1):
        x = ordenado.select(nomes[i - 1])
        dentro = n.gte(i)                                  # posições além de n são SENTINELA: peso 0
        c1 = n.subtract(i).divide(n.subtract(1)).multiply(dentro)
        c2 = (n.subtract(i).multiply(n.subtract(i + 1))
              .divide(n.subtract(1).multiply(n.subtract(2))).multiply(dentro))
        a1 = a1.add(x.multiply(c1))
        a2 = a2.add(x.multiply(c2))
    a1 = a1.divide(n)
    a2 = a2.divide(n)
    l1 = a0
    l2 = a0.subtract(a1.multiply(2))
    l3 = a0.subtract(a1.multiply(6)).add(a2.multiply(6))
    kappa = l3.divide(l2).multiply(-1)
    kappa = kappa.where(kappa.abs().lt(KAPPA_MINIMO), KAPPA_MINIMO)
    kpi = kappa.multiply(math.pi)
    alfa = l2.multiply(kpi.sin()).divide(kpi)
    xi = l1.subtract(alfa.multiply(ee.Image.constant(1).divide(kappa).subtract(
        ee.Image.constant(math.pi).divide(kpi.sin()))))
    valido = n.gte(ANOS_MINIMOS).And(l2.gt(0)).And(kappa.abs().lt(1)).And(alfa.gt(0))
    return ee.Image.cat([
        xi.updateMask(valido).rename(f'{prefixo}_xi'),
        alfa.updateMask(valido).rename(f'{prefixo}_alfa'),
        kappa.updateMask(valido).rename(f'{prefixo}_kappa'),
        n.rename(f'{prefixo}_n'),
    ])


def percentis_chuva_umida(p, mes):
    """P95 e P99 da chuva diária nos dias com chuva (>= 1 mm) do mês, nos 30 anos juntos
    (limiar de chuva intensa do mês, no espírito do R95p do ETCCDI)."""
    a0, a1 = PERIODOS[p]['anos']
    col = (ee.ImageCollection(ASSET_ORIGEM).filter(ee.Filter.calendarRange(mes, mes, 'month'))
           .filterDate(f'{a0}-01-01', f'{a1 + 1}-01-01')
           .map(lambda i: padronizar_nomes(i).select(['pr_mm']))
           .map(lambda i: i.updateMask(i.gte(LIMIAR_DIA_SECO))))
    n = col.count()
    pct = (col.reduce(ee.Reducer.percentile(percentiles=[95, 99], maxRaw=1000))
           .rename(['pr_p95_umido', 'pr_p99_umido']).updateMask(n.gte(MIN_DIAS_UMIDOS)))
    return ee.Image.cat([pct, n.rename('n_dias_umidos')])


def nomes_bandas_normais():
    return ([f'{v}_media' for v in VARS_MES] + [f'{v}_dp' for v in VARS_MES] +
            [f'{v}_n' for v in VARS_MES] + [nome for _, nome in QUANTIS_CHUVA] +
            [f'{v}_{s}' for v in ('tmax_C', 'tmin_C') for _, s in TERCIS_TEMP] +
            [f'spi{k}_{c}' for k in ESCALAS_SPI for c in ('alfa', 'beta', 'q0', 'n')] +
            [f'spei{k}_{c}' for k in ESCALAS_SPEI for c in ('xi', 'alfa', 'kappa', 'n')] +
            ['pr_p95_umido', 'pr_p99_umido', 'n_dias_umidos'])


def imagem_normais(p, mes):
    a0, a1 = PERIODOS[p]['anos']
    corr = montar_correcao_mes(mes)
    anos = ee.List.sequence(a0, a1)
    anual = ee.ImageCollection.fromImages(anos.map(lambda a: agregar_ano_mes(ee.Number(a), mes, corr)))
    n = anual.count()                                   # 33 bandas, na ordem de VARS_MES
    ok = n.gte(ANOS_MINIMOS)
    media = anual.mean().updateMask(ok).rename([f'{v}_media' for v in VARS_MES])
    dp = anual.reduce(ee.Reducer.sampleStdDev()).updateMask(ok).rename([f'{v}_dp' for v in VARS_MES])
    contagem = n.rename([f'{v}_n' for v in VARS_MES])
    quantis = quantis_por_posto(anual, 'pr_mm', QUANTIS_CHUVA, ANOS_MINIMOS)
    tercis = ee.Image.cat([
        quantis_por_posto(anual, v, [(q, f'{v}_{s}') for q, s in TERCIS_TEMP], ANOS_MINIMOS)
        for v in ('tmax_C', 'tmin_C')])
    acumulados = ee.ImageCollection.fromImages(anos.map(lambda a: totais_indices(ee.Number(a), mes)))
    spi = ee.Image.cat([parametros_gama(acumulados, f'pr_{k}m', f'spi{k}') for k in ESCALAS_SPI])
    spei = ee.Image.cat([parametros_glo(acumulados, f'd_{k}m', f'spei{k}', a1 - a0 + 1)
                         for k in ESCALAS_SPEI])
    # select com a lista fixa: ordem garantida e erro imediato se faltar alguma banda que o painel lê
    img = ee.Image.cat([media, dp, contagem, quantis, tercis, spi, spei,
                        percentis_chuva_umida(p, mes)]).select(nomes_bandas_normais()).toFloat()
    return img.set({
        'mes': mes, 'periodo': p, 'ano_inicio': a0, 'ano_fim': a1,
        'dias_medios_mes': dias_medios_mes(a0, a1, mes),
        'anos_minimos': ANOS_MINIMOS, 'faltas_max_media': FALTAS_MAX_MEDIA,
        'limiar_zero_chuva_mm': LIMIAR_ZERO_CHUVA_MM, 'min_anos_com_chuva_spi': MIN_ANOS_COM_CHUVA_SPI,
        'limiar_dia_seco_mm': LIMIAR_DIA_SECO, 'limiar_chuva_10_mm': LIMIAR_CHUVA_10,
        'limiar_chuva_20_mm': LIMIAR_CHUVA_20, 'limiar_frio_C': LIMIAR_FRIO, 'limiar_geada_C': LIMIAR_GEADA,
        'limiar_tmin_0_C': LIMIAR_TMIN_0, 'limiar_calor_C': LIMIAR_CALOR,
        'tbase_graus_dia_C': TBASE_GD, 'tsup_graus_dia_C': TSUP_GD, 'min_dias_umidos': MIN_DIAS_UMIDOS,
        'kappa_minimo_spei': KAPPA_MINIMO,
        'versao_baseline': VERSAO_BASELINE, 'origem': ASSET_ORIGEM, 'gerado_em': agora_brt,
        'metodo': ('OMM WMO-No.1203: total so com mes completo; media e extremos com ate 4 faltas; normal '
                   'com >=24 anos; dp amostral entre anos; quantis tipo 7; SPI gama (Thom); SPEI '
                   'logistica generalizada de Hosking (momentos-L nao viciados, pelglo/cdfglo do pacote '
                   'SPEI); leitura igual ao Painel SAB (correcao V1.0 de solo/escoamento e ET real <= ETo)'),
    })


def imagem_limiares(p, mes, dias=None):
    """P90 e P10 da Tmax e da Tmin de cada dia do calendário, com janela de 5 dias (±2) em todos
    os anos da normal (ETCCDI: TX90p, TX10p, TN90p, TN10p). Dias da janela fora da normal ficam
    de fora."""
    a0, a1 = PERIODOS[p]['anos']
    lim_ini, lim_fim = date(a0, 1, 1), date(a1, 12, 31)
    base = ee.ImageCollection(ASSET_ORIGEM).filterDate(f'{a0}-01-01', f'{a1 + 1}-01-01')
    n_dias_mes = 28 if mes == 2 else calendar.monthrange(2001, mes)[1]
    dias = list(dias) if dias else list(range(1, n_dias_mes + 1))
    n_min = math.ceil(FRACAO_MIN_JANELA * (2 * JANELA_LIMIARES + 1) * (a1 - a0 + 1))
    reducer = ee.Reducer.percentile(percentiles=[10, 90], maxRaw=1000)   # cálculo direto (<= 150 valores)
    grupos = {'tx90': [], 'tx10': [], 'tn90': [], 'tn10': []}
    for d in dias:
        filtros = []
        for a in range(a0, a1 + 1):
            centro = date(a, mes, d)
            ini = max(centro - timedelta(days=JANELA_LIMIARES), lim_ini)
            fim = min(centro + timedelta(days=JANELA_LIMIARES), lim_fim)
            filtros.append(ee.Filter.date(ini.isoformat(), (fim + timedelta(days=1)).isoformat()))
        janela = base.filter(ee.Filter.Or(*filtros)).map(
            lambda i: padronizar_nomes(i).select(['tmax_C', 'tmin_C']))
        for var, pref in (('tmax_C', 'tx'), ('tmin_C', 'tn')):
            serie = janela.select([var])
            ok = serie.count().gte(n_min)
            pct = serie.reduce(reducer).rename([f'{pref}10', f'{pref}90']).updateMask(ok)
            grupos[f'{pref}90'].append(pct.select(f'{pref}90').rename(f'{pref}90_d{d:02d}'))
            grupos[f'{pref}10'].append(pct.select(f'{pref}10').rename(f'{pref}10_d{d:02d}'))
    return ee.Image.cat(grupos['tx90'] + grupos['tx10'] + grupos['tn90'] + grupos['tn10']).toFloat().set({
        'mes': mes, 'periodo': p, 'ano_inicio': a0, 'ano_fim': a1, 'dias_no_mes': n_dias_mes,
        'janela_dias': 2 * JANELA_LIMIARES + 1, 'percentis': '10 e 90', 'minimo_dias_janela': n_min,
        'versao_baseline': VERSAO_BASELINE, 'origem': ASSET_ORIGEM, 'gerado_em': agora_brt,
        'metodo': 'ETCCDI: percentil do dia do calendario com janela de 5 dias, sem bootstrap',
    })


# =========================================================================
# 7. INVENTÁRIO DO BANCO NO PERÍODO
# =========================================================================
DATAS_NAO_V10 = {}               # período -> datas gravadas por outra versão do motor (sem correção)

def maior_sequencia(dias_faltando):
    maior, atual, anterior = 0, 0, None
    for d in sorted(dias_faltando):
        atual = atual + 1 if anterior is not None and (d - anterior).days == 1 else 1
        maior = max(maior, atual)
        anterior = d
    return maior


def inventario(p):
    a0, a1 = PERIODOS[p]['anos']
    col = ee.ImageCollection(ASSET_ORIGEM).filterDate(f'{a0}-01-01', f'{a1 + 1}-01-01')

    def para_feature(img):
        d = img.toDictionary()
        return ee.Feature(None, {
            't': img.get('system:time_start'),
            'versao': d.get('versao', 'definitiva'),
            'alg': d.get('versao_algoritmo', 'V1.0'),
            'antigo': img.bandNames().contains('precipitation_mm'),
        })

    t, versao, alg, antigo = col.map(para_feature).reduceColumns(
        ee.Reducer.toList().repeat(4), ['t', 'versao', 'alg', 'antigo']).get('list').getInfo()
    datas = pd.to_datetime(pd.Series(t, dtype='float64'), unit='ms', utc=True).dt.tz_localize(None).dt.normalize()
    esperadas = pd.date_range(f'{a0}-01-01', f'{a1}-12-31')
    presentes = set(datas)
    faltando = sorted(set(esperadas) - presentes)
    duplicadas = sorted(set(datas[datas.duplicated()]))

    linhas = []
    for a in range(a0, a1 + 1):
        for m in range(1, 13):
            f = [d for d in faltando if d.year == a and d.month == m]
            linhas.append({'ano': a, 'mes': m, 'faltas': len(f), 'seguidas': maior_sequencia(f),
                           'duplicadas': sum(1 for d in duplicadas if d.year == a and d.month == m)})
    meses = pd.DataFrame(linhas)
    meses['total_ok'] = (meses.faltas == 0) & (meses.duplicadas == 0)
    meses['media_ok_omm'] = (meses.faltas <= 10) & (meses.seguidas <= 4)
    meses['media_ok_script'] = meses.faltas <= FALTAS_MAX_MEDIA
    anos_validos = meses.groupby('mes')[['total_ok', 'media_ok_omm', 'media_ok_script']].sum()

    print(f"\n📋 INVENTÁRIO {p.replace('_', '-')}: {len(datas)} imagens | esperadas {len(esperadas)} | "
          f"faltando {len(faltando)} | datas duplicadas {len(duplicadas)}")
    print(f"   versão: {pd.Series(versao).value_counts().to_dict()} | algoritmo: "
          f"{pd.Series(alg).value_counts().to_dict()} | com nomes antigos de banda: {int(sum(bool(x) for x in antigo))}")
    if faltando:
        print(f"   primeiros dias faltando: {[d.strftime('%Y-%m-%d') for d in faltando[:10]]}")
    if duplicadas:
        print(f"   ⚠️ datas duplicadas (somariam duas vezes): {[d.strftime('%Y-%m-%d') for d in duplicadas[:10]]}")
    if (anos_validos < 30).any().any():
        print("   Anos válidos por mês (de 30):")
        print(anos_validos.to_string())
    DATAS_NAO_V10[p] = {d for d, a in zip(datas, alg) if a != 'V1.0'}
    nao_def = sum(1 for v in versao if v != 'definitiva')
    if nao_def:
        print(f"   ⚠️ {nao_def} dia(s) não definitivos dentro da normal")
    min_anos = int(anos_validos.min().min())
    # Faltas isoladas são tratadas pela regra da OMM; duplicatas indicam banco inconsistente
    ok = (not duplicadas and nao_def == 0 and min_anos >= ANOS_MINIMOS)
    return {'ok': ok, 'faltando': len(faltando), 'duplicadas': len(duplicadas),
            'min_anos': min_anos, 'nao_definitivos': nao_def}


# =========================================================================
# 8. CONFERÊNCIA: EARTH ENGINE x CÁLCULO INDEPENDENTE NOS PONTOS DE REFERÊNCIA
# =========================================================================
def centro_pixel(lat, lon):
    dx, x0 = TRANSFORM[0], TRANSFORM[2]
    dy, y0 = -TRANSFORM[4], TRANSFORM[5]
    return (y0 - (math.floor((y0 - lat) / dy) + 0.5) * dy,
            x0 + (math.floor((lon - x0) / dx) + 0.5) * dx)


def pontos_conferencia():
    return [{'nome': n, 'lat': centro_pixel(la, lo)[0], 'lon': centro_pixel(la, lo)[1]}
            for n, la, lo in PONTOS_REFERENCIA]


def amostrar(img, pontos):
    """Valor de cada banda no pixel de cada ponto; se o Earth Engine recusar o pedido conjunto
    (tempo ou memória), pede um ponto por vez."""
    def ler(lista):
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([q['lon'], q['lat']]), {'nome': q['nome']})
                                   for q in lista])
        feats = img.reduceRegions(collection=fc, reducer=ee.Reducer.first(), crs=CRS,
                                  crsTransform=TRANSFORM).getInfo()['features']
        return {f['properties']['nome']: f['properties'] for f in feats}
    try:
        return ler(pontos)
    except Exception as e:
        print(f"   ↪️ pedido conjunto recusado ({str(e)[:80]}); um ponto por vez")
        res = {}
        for q in pontos:
            res.update(ler([q]))
        return res


ERROS_DE_LIMITE = ('memory', 'timed out', 'Too many', 'too large', 'exceeded', 'Computation')


def serie_pontos(col, bandas, pontos, ini, fim):
    """Série diária de cada ponto (getRegion na grade do banco) entre as datas ini e fim.
    Se o Earth Engine recusar o pedido (memória ou tempo), divide o período ao meio até blocos
    de cerca de um ano e, se ainda for preciso, lê um ponto por vez."""
    avisado = []

    def ler(lista, a, b):
        geom = ee.Geometry.MultiPoint([[q['lon'], q['lat']] for q in lista])
        linhas = (col.filterDate(a.isoformat(), b.isoformat()).select(bandas)
                  .getRegion(geom, None, CRS, TRANSFORM).getInfo())
        return pd.DataFrame(linhas[1:], columns=linhas[0])

    def ler_adaptativo(lista, a, b):
        try:
            return ler(lista, a, b)
        except ee.EEException as e:
            if not any(m in str(e) for m in ERROS_DE_LIMITE):
                raise
            if not avisado:
                print(f"   ↪️ leitura recusada pelo Earth Engine ({str(e)[:60]}); lendo em blocos menores")
                avisado.append(1)
            dias = (b - a).days
            if dias > 400:
                meio = a + timedelta(days=dias // 2)
                return pd.concat([ler_adaptativo(lista, a, meio), ler_adaptativo(lista, meio, b)], ignore_index=True)
            if len(lista) > 1:
                return pd.concat([ler_adaptativo([q], a, b) for q in lista], ignore_index=True)
            raise

    df = ler_adaptativo(list(pontos), ini, fim)
    lat = df['latitude'].astype(float).to_numpy()
    lon = df['longitude'].astype(float).to_numpy()
    dist = np.stack([np.hypot(lat - q['lat'], lon - q['lon']) for q in pontos])
    df['nome'] = [pontos[i]['nome'] for i in dist.argmin(axis=0)] if len(df) else []
    df['data'] = pd.to_datetime(df['time'].astype('float64'), unit='ms', utc=True).dt.tz_localize(None).dt.normalize()
    for b in bandas:
        df[b] = pd.to_numeric(df[b], errors='coerce')
    return df[['nome', 'data'] + bandas].sort_values(['nome', 'data'], ignore_index=True)


def preparar_local(bruta, corr_pts, datas_nao_v10):
    """A leitura de cada dia do painel (preparar_dia) refeita em pandas a partir das bandas
    brutas: correção V1.0 de escoamento e umidade do solo com os fatores do mês amostrados no
    pixel, ET real limitada à ETo, transpiração limitada à ET real e as bandas derivadas.
    Valor ausente continua ausente, como a máscara do Earth Engine."""
    s = bruta.copy()
    v10 = ~s['data'].isin(datas_nao_v10)
    def campo(c):
        return s['nome'].map(lambda n: float(corr_pts[n][c]))
    for banda, fator, teto in (('runoff_sup_mm', 'c_rsup', None), ('runoff_sub_mm', 'c_rsub', None),
                               ('soil_moisture_0_5cm_m3_m3', 'c_ssur', 'teto_ssur'),
                               ('soil_moisture_0_100cm_m3_m3', 'c_swat', 'teto_swat')):
        novo = s[banda] * campo(fator)
        if teto:
            novo = np.minimum(novo, campo(teto))
        s[banda] = novo.where(v10, s[banda])
    s['et_real'] = np.minimum(s['et_real'], s['et_potencial'])
    s['transpiracao_mm'] = np.minimum(s['transpiracao_mm'], s['et_real'])
    pr, tx, tn, eto = s['pr_mm'], s['tmax_C'], s['tmin_C'], s['et_potencial']
    s['tmed_C'] = (tx + tn) / 2
    s['amplitude_diaria'] = tx - tn
    s['deficit_diario'] = np.maximum(eto - s['et_real'], 0)
    s['chuva_efetiva'] = np.maximum(pr - s['runoff_sup_mm'], 0)
    s['balanco_hidrico'] = pr - eto
    s['graus_dia'] = (tx.clip(TBASE_GD, TSUP_GD) + tn.clip(TBASE_GD, TSUP_GD)) / 2 - TBASE_GD
    def marca(base, cond):
        return cond.astype(float).where(base.notna())
    s['dias_chuva_1mm'] = marca(pr, pr >= LIMIAR_DIA_SECO)
    s['dias_secos'] = marca(pr, pr < LIMIAR_DIA_SECO)
    s['dias_chuva_10mm'] = marca(pr, pr >= LIMIAR_CHUVA_10)
    s['dias_chuva_20mm'] = marca(pr, pr >= LIMIAR_CHUVA_20)
    s['dias_frios'] = marca(tn, tn <= LIMIAR_FRIO)
    s['dias_geada'] = marca(tn, tn <= LIMIAR_GEADA)
    s['dias_tmin_0'] = marca(tn, tn < LIMIAR_TMIN_0)
    s['dias_calor'] = marca(tx, tx >= LIMIAR_CALOR)
    return s[['nome', 'data'] + VARS_DIA]


def quantil_local(valores, p, tipo):
    x = np.sort(np.asarray(valores, dtype=float))
    n = len(x)
    if n == 0:
        return np.nan
    h = (n - 1) * p if tipo == 7 else (n + 1 / 3) * p + 1 / 3 - 1
    h = min(max(h, 0.0), n - 1.0)
    lo = int(math.floor(h))
    hi = min(lo + 1, n - 1)
    return x[lo] + (h - lo) * (x[hi] - x[lo])


def gama_local(totais):
    v = np.asarray([t for t in totais if np.isfinite(t)], dtype=float)
    n = len(v)
    pos = v[v >= LIMIAR_ZERO_CHUVA_MM]
    res = {'alfa': np.nan, 'beta': np.nan, 'q0': np.nan, 'n': float(n)}
    if n < ANOS_MINIMOS or len(pos) < MIN_ANOS_COM_CHUVA_SPI:
        return res
    A = math.log(pos.mean()) - np.log(pos).mean()
    if A <= 1e-6:
        return res
    alfa = (1 + math.sqrt(1 + 4 * A / 3)) / (4 * A)
    res.update(alfa=alfa, beta=pos.mean() / alfa, q0=(n - len(pos)) / n)
    return res


def glo_local(valores):
    """Mesmo ajuste do Earth Engine (momentos-L não viciados e logística generalizada), feito
    aqui de forma independente."""
    v = np.sort(np.asarray([t for t in valores if np.isfinite(t)], dtype=float))
    n = len(v)
    res = {'xi': np.nan, 'alfa': np.nan, 'kappa': np.nan, 'n': float(n)}
    if n < ANOS_MINIMOS:
        return res
    i = np.arange(1, n + 1)
    a0 = v.mean()
    a1 = np.sum((n - i) / (n - 1) * v) / n
    a2 = np.sum((n - i) * (n - i - 1) / ((n - 1) * (n - 2)) * v) / n
    l1, l2, l3 = a0, a0 - 2 * a1, a0 - 6 * a1 + 6 * a2
    if not l2 > 0:
        return res
    k = -l3 / l2
    if abs(k) < KAPPA_MINIMO:
        k = KAPPA_MINIMO
    if not abs(k) < 1:
        return res
    alfa = l2 * math.sin(k * math.pi) / (k * math.pi)
    if not alfa > 0:
        return res
    res.update(xi=l1 - alfa * (1 / k - math.pi / math.sin(k * math.pi)), alfa=alfa, kappa=k)
    return res


def valores_mensais_locais(serie, a0, a1, mes):
    """Totais, médias e extremos de cada ano pela mesma regra do Earth Engine (NaN = mês inválido)."""
    linhas = []
    for a in range(a0, a1 + 1):
        n_dias = calendar.monthrange(a, mes)[1]
        g = serie[(serie.data.dt.year == a) & (serie.data.dt.month == mes)]
        lin = {'ano': a}
        for v in VARS_DIA:
            s = g[v].dropna()
            if v in VARS_TOTAL:
                lin[v] = s.sum() if len(s) == n_dias else np.nan
            else:
                lin[v] = s.mean() if len(s) >= n_dias - FALTAS_MAX_MEDIA else np.nan
        for nome_e, orig, red in VARS_EXTREMO:
            s = g[orig].dropna()
            ok = len(s) > 0 and len(s) >= n_dias - FALTAS_MAX_MEDIA
            lin[nome_e] = (s.max() if red == 'max' else s.min()) if ok else np.nan
        linhas.append(lin)
    return pd.DataFrame(linhas)


def totais_indices_locais(serie, a0, a1, mes):
    """Acumulados de chuva (SPI) e de chuva menos ETo (SPEI) terminados no mês, por ano."""
    def total(a, m, banda):
        while m < 1:
            a, m = a - 1, m + 12
        n_dias = calendar.monthrange(a, m)[1]
        s = serie[(serie.data.dt.year == a) & (serie.data.dt.month == m)][banda].dropna()
        return s.sum() if len(s) == n_dias else np.nan
    res = {f'pr_{k}m': [] for k in ESCALAS_SPI}
    res.update({f'd_{k}m': [] for k in ESCALAS_SPEI})
    kmax = max(ESCALAS_SPI + ESCALAS_SPEI)
    for a in range(a0, a1 + 1):
        pr = [total(a, mes - k, 'pr_mm') for k in range(kmax)]
        et = [total(a, mes - k, 'et_potencial') for k in range(kmax)]
        for k in ESCALAS_SPI:
            res[f'pr_{k}m'].append(sum(pr[:k]))
        for k in ESCALAS_SPEI:
            res[f'd_{k}m'].append(sum(x - y for x, y in zip(pr[:k], et[:k])))
    return res


def normais_locais(serie_prep, serie_base, a0, a1, mes):
    res = {}
    for nome in serie_prep.nome.unique():
        anual = valores_mensais_locais(serie_prep[serie_prep.nome == nome], a0, a1, mes)
        r = {}
        for v in VARS_MES:
            x = anual[v].dropna().to_numpy()
            n = len(x)
            r[f'{v}_n'] = float(n)
            r[f'{v}_media'] = x.mean() if n >= ANOS_MINIMOS else np.nan
            r[f'{v}_dp'] = x.std(ddof=1) if n >= ANOS_MINIMOS else np.nan
        pr = anual['pr_mm'].dropna().to_numpy()
        for p, nome_q in QUANTIS_CHUVA:
            r[nome_q] = quantil_local(pr, p, 7) if len(pr) >= ANOS_MINIMOS else np.nan
        for v in ('tmax_C', 'tmin_C'):
            x = anual[v].dropna().to_numpy()
            for q, s in TERCIS_TEMP:
                r[f'{v}_{s}'] = quantil_local(x, q, 7) if len(x) >= ANOS_MINIMOS else np.nan
        acum = totais_indices_locais(serie_base[serie_base.nome == nome], a0, a1, mes)
        for k in ESCALAS_SPI:
            g = gama_local(acum[f'pr_{k}m'])
            for c in ('alfa', 'beta', 'q0', 'n'):
                r[f'spi{k}_{c}'] = g[c]
        for k in ESCALAS_SPEI:
            g = glo_local(acum[f'd_{k}m'])
            for c in ('xi', 'alfa', 'kappa', 'n'):
                r[f'spei{k}_{c}'] = g[c]
        res[nome] = r
    return res


def chuva_umida_local(serie_base, a0, a1, mes):
    """Chuva dos dias com chuva do mês nos anos da normal (para conferir P95 e P99)."""
    res = {}
    for nome in serie_base.nome.unique():
        s = serie_base[(serie_base.nome == nome) & (serie_base.data.dt.month == mes) &
                       (serie_base.data.dt.year >= a0) & (serie_base.data.dt.year <= a1)]
        x = np.sort(s['pr_mm'].dropna().to_numpy())
        x = x[x >= LIMIAR_DIA_SECO]
        res[nome] = {'pr_p95_umido': x, 'pr_p99_umido': x}
    return res


def limiares_locais(serie_temp, a0, a1, mes, dias):
    """Valores da janela de cada dia, para conferir os percentis do Earth Engine."""
    lim_ini, lim_fim = pd.Timestamp(a0, 1, 1), pd.Timestamp(a1, 12, 31)
    res = {}
    for nome in serie_temp.nome.unique():
        s = serie_temp[serie_temp.nome == nome]
        r = {}
        for d in dias:
            sel = np.zeros(len(s), dtype=bool)
            for a in range(a0, a1 + 1):
                c = pd.Timestamp(a, mes, d)
                ini = max(c - pd.Timedelta(days=JANELA_LIMIARES), lim_ini)
                fim = min(c + pd.Timedelta(days=JANELA_LIMIARES), lim_fim)
                sel |= ((s.data >= ini) & (s.data <= fim)).to_numpy()
            tx = np.sort(s.loc[sel, 'tmax_C'].dropna().to_numpy())
            tn = np.sort(s.loc[sel, 'tmin_C'].dropna().to_numpy())
            r[f'tx90_d{d:02d}'], r[f'tx10_d{d:02d}'] = tx, tx
            r[f'tn90_d{d:02d}'], r[f'tn10_d{d:02d}'] = tn, tn
        res[nome] = r
    return res


def comparar(ee_vals, loc_vals, rtol=5e-4, atol=1e-4):
    linhas = []
    for nome, loc in loc_vals.items():
        e = ee_vals.get(nome, {})
        for banda, ref in loc.items():
            v = e.get(banda)
            v = np.nan if v is None else float(v)
            ambos_nan = not np.isfinite(v) and not np.isfinite(ref)
            ok = ambos_nan or (np.isfinite(v) and np.isfinite(ref) and abs(v - ref) <= atol + rtol * abs(ref))
            linhas.append({'ponto': nome, 'banda': banda, 'ee': v, 'local': ref, 'ok': ok,
                           'dif': abs(v - ref) if np.isfinite(v) and np.isfinite(ref) else np.nan})
    return pd.DataFrame(linhas)


def percentil_da_banda(banda):
    for marca, p in (('p95', 0.95), ('p99', 0.99), ('90_', 0.90), ('10_', 0.10)):
        if marca in banda:
            return p
    raise ValueError(banda)


def comparar_percentis(ee_vals, amostras, n_min):
    """O percentil do Earth Engine (cálculo direto sobre os valores) tem de cair entre as
    estatísticas de ordem vizinhas da posição do percentil; também diz qual definição bate."""
    linhas = []
    for nome, jan in amostras.items():
        for banda, x in jan.items():
            p = percentil_da_banda(banda)
            v = ee_vals.get(nome, {}).get(banda)
            v = np.nan if v is None else float(v)
            n = len(x)
            if n < n_min:
                linhas.append({'ponto': nome, 'banda': banda, 'n': n, 'ee': v, 'ok': not np.isfinite(v),
                               'tipo7': np.nan, 'tipo8': np.nan, 'faixa': ''})
                continue
            h8 = (n + 1 / 3) * p + 1 / 3 - 1
            lo, hi = max(int(math.floor(h8)) - 1, 0), min(int(math.ceil(h8)) + 1, n - 1)
            t7, t8 = quantil_local(x, p, 7), quantil_local(x, p, 8)
            ok = np.isfinite(v) and x[lo] - 1e-4 <= v <= x[hi] + 1e-4
            linhas.append({'ponto': nome, 'banda': banda, 'n': n, 'ee': v, 'ok': ok,
                           'tipo7': t7, 'tipo8': t8, 'faixa': f'{x[lo]:.2f} a {x[hi]:.2f}'})
    return pd.DataFrame(linhas)


def grupo_banda(b):
    if b.startswith('spei'):
        return 'SPEI ' + b[4]
    if b.startswith('spi'):
        return 'SPI ' + b[3]
    if b.startswith('pr_mm_q') or b.startswith('pr_mm_t') or b == 'pr_mm_mediana':
        return 'quantis da chuva'
    if b.endswith('_t33') or b.endswith('_t67'):
        return 'tercis de temperatura'
    if b == 'n_dias_umidos':
        return 'dias úmidos (P95)'
    for suf, rot in (('_media', 'médias'), ('_dp', 'desvios'), ('_n', 'anos válidos')):
        if b.endswith(suf):
            return rot
    return 'outras'


def verificar(p, mes):
    a0, a1 = PERIODOS[p]['anos']
    pontos = pontos_conferencia()
    t0 = time.time()
    print(f"\n🔬 CONFERÊNCIA {p.replace('_', '-')}, mês {mes:02d}, em {len(pontos)} pontos")

    print("   ⏳ normais e limiares calculados pelo Earth Engine...")
    ee_n = amostrar(imagem_normais(p, mes), pontos)
    ee_l = amostrar(imagem_limiares(p, mes, DIAS_VERIFICACAO), pontos)

    print("   ⏳ séries diárias brutas dos mesmos pixels (a leitura do painel é refeita aqui)...")
    corr_pts = amostrar(montar_correcao_mes(mes), pontos)
    if p not in DATAS_NAO_V10:
        inventario(p)
    col_mes = (ee.ImageCollection(ASSET_ORIGEM).filter(ee.Filter.calendarRange(mes, mes, 'month'))
               .map(padronizar_nomes))
    serie_bruta = serie_pontos(col_mes, BANDAS_SAB, pontos, date(a0, 1, 1), date(a1 + 1, 1, 1))
    serie_prep = preparar_local(serie_bruta, corr_pts, DATAS_NAO_V10[p])
    kmax = max(ESCALAS_SPI + ESCALAS_SPEI)
    meses_base = {((mes - k - 1) % 12) + 1 for k in range(kmax)}
    if any(d + JANELA_LIMIARES > 28 for d in DIAS_VERIFICACAO):      # janela entra no mês seguinte
        meses_base.add(mes % 12 + 1)
    filtro_meses = ee.Filter.Or(*[ee.Filter.calendarRange(m, m, 'month') for m in sorted(meses_base)])
    bandas_base = ['pr_mm', 'et_potencial', 'tmax_C', 'tmin_C']
    col_base = (ee.ImageCollection(ASSET_ORIGEM).filter(filtro_meses)
                .map(lambda i: padronizar_nomes(i).select(bandas_base)))
    serie_base = serie_pontos(col_base, bandas_base, pontos, date(a0 - 1, 7, 1), date(a1 + 1, 1, 1))

    loc_n = normais_locais(serie_prep, serie_base, a0, a1, mes)
    umidos = chuva_umida_local(serie_base, a0, a1, mes)
    for nome, r in loc_n.items():
        r['n_dias_umidos'] = float(len(umidos.get(nome, {}).get('pr_p95_umido', [])))
    janelas = limiares_locais(serie_base, a0, a1, mes, DIAS_VERIFICACAO)
    n_min = math.ceil(FRACAO_MIN_JANELA * (2 * JANELA_LIMIARES + 1) * (a1 - a0 + 1))

    comp = comparar(ee_n, loc_n)
    comp['grupo'] = comp.banda.map(grupo_banda)
    resumo = comp.groupby('grupo').agg(comparacoes=('ok', 'size'), iguais=('ok', 'sum'),
                                       maior_diferenca=('dif', 'max'))
    comp_l = pd.concat([comparar_percentis(ee_l, janelas, n_min),
                        comparar_percentis(ee_n, umidos, MIN_DIAS_UMIDOS)], ignore_index=True)
    print(f"\n   EARTH ENGINE x CÁLCULO LOCAL (tolerância relativa 5e-4) | {time.time() - t0:.0f} s")
    print(resumo.to_string())
    print(f"   percentis diários (limiares dos dias {DIAS_VERIFICACAO} e P95/P99 da chuva): "
          f"{int(comp_l.ok.sum())} de {len(comp_l)} dentro da faixa das estatísticas de ordem vizinhas")
    temp = comp_l[comp_l.banda.str.startswith('t') & comp_l.ok]
    if len(temp):
        d7 = (temp.ee - temp.tipo7).abs().max()
        d8 = (temp.ee - temp.tipo8).abs().max()
        print(f"   percentil do Earth Engine nos limiares: maior diferença {d7:.3f} °C para o tipo 7 "
              f"e {d8:.3f} °C para o tipo 8")
    erros = comp[~comp.ok]
    if len(erros):
        print("   ❌ divergências (até 15):")
        print(erros.head(15).to_string(index=False))
    if (~comp_l.ok).any():
        print(comp_l[~comp_l.ok].to_string(index=False))

    # Coerência física e da regra dos 80%
    dm = dias_medios_mes(a0, a1, mes)
    problemas = []
    for nome, r in loc_n.items():
        e = {k: (np.nan if v is None else v) for k, v in ee_n.get(nome, {}).items() if k != 'nome'}
        g = lambda k: float(e.get(k, np.nan))  # noqa: E731
        if min(g(f'{v}_n') for v in VARS_MES) < ANOS_MINIMOS:
            problemas.append(f"{nome}: alguma variável com menos de {ANOS_MINIMOS} anos válidos")
        if not g('txx_media') >= g('tmax_C_media') > g('tmed_C_media') > g('tmin_C_media') >= g('tnn_media'):
            problemas.append(f"{nome}: ordem TXx >= Tmax > Tmed > Tmin >= TNn não vale nas normais")
        if not g('rx1day_media') <= g('pr_mm_media') + 1e-6:
            problemas.append(f"{nome}: maior chuva diária normal acima do total normal")
        if not abs(g('dias_chuva_1mm_media') + g('dias_secos_media') - dm) < 0.1:
            problemas.append(f"{nome}: dias com chuva + dias secos não somam os dias do mês")
        if not g('graus_dia_media') >= 0:
            problemas.append(f"{nome}: graus-dia normal negativo")
        qs = [g(n_) for _, n_ in QUANTIS_CHUVA[:4]]
        if not all(np.isfinite(qs)) or any(b < a - 1e-6 for a, b in zip(qs, qs[1:])):
            problemas.append(f"{nome}: quintis da chuva fora de ordem ou ausentes")
        if not g('pr_mm_t33') <= g('pr_mm_t67'):
            problemas.append(f"{nome}: tercis da chuva fora de ordem")
        if g('soil_moisture_0_100cm_m3_m3_media') > UMIDADE_MAX_FISICA + 1e-4:
            problemas.append(f"{nome}: umidade 0-100 cm normal acima de {UMIDADE_MAX_FISICA}")
        if g('et_real_media') > g('et_potencial_media') + 1e-3:
            problemas.append(f"{nome}: ET real normal maior que ETo normal")
        for k in ESCALAS_SPEI:
            if g(f'spei{k}_n') >= ANOS_MINIMOS and not np.isfinite(g(f'spei{k}_alfa')):
                problemas.append(f"{nome}: SPEI-{k} sem ajuste apesar de {g(f'spei{k}_n'):.0f} anos válidos")
        q0 = g('spi1_q0')
        if np.isfinite(q0) and not 0 <= q0 <= 1:
            problemas.append(f"{nome}: q0 do SPI fora de 0 a 1")
        if np.isfinite(g('pr_p95_umido')) and not g('pr_p99_umido') >= g('pr_p95_umido'):
            problemas.append(f"{nome}: P99 da chuva menor que o P95")
        lim = {k: v for k, v in ee_l.get(nome, {}).items() if k != 'nome'}
        if 15 in DIAS_VERIFICACAO:
            v15 = [lim.get(f'{b}_d15') for b in ('tx90', 'tx10', 'tn90', 'tn10')]
            if None in v15 or not (v15[0] > v15[1] and v15[2] > v15[3] and v15[0] > v15[3]):
                problemas.append(f"{nome}: limiares do dia 15 fora de ordem (TX90 > TX10, TN90 > TN10)")

    tabela = []
    for q in pontos:
        e = ee_n.get(q['nome'], {})
        lim = ee_l.get(q['nome'], {})
        f = lambda k, nd=1: (round(float(e[k]), nd) if e.get(k) is not None else None)  # noqa: E731
        fl = lambda k: (round(float(lim[k]), 1) if lim.get(k) is not None else None)  # noqa: E731
        tabela.append({
            'ponto': q['nome'], 'chuva': f('pr_mm_media'), 'dp': f('pr_mm_dp'), 'q20': f('pr_mm_q20'),
            'q80': f('pr_mm_q80'), 'dias_chuva': f('dias_chuva_1mm_media'), 'rx1day': f('rx1day_media'),
            'P95_dia': f('pr_p95_umido'), 'Tmax': f('tmax_C_media'), 'Tmin': f('tmin_C_media'),
            'ETo': f('et_potencial_media'), 'GD': f('graus_dia_media', 0),
            'umid100': f('soil_moisture_0_100cm_m3_m3_media', 3), 'anos': f('pr_mm_n', 0),
            'spi3_alfa': f('spi3_alfa', 2), 'spei3_kappa': f('spei3_kappa', 3),
            'TX90_d15': fl('tx90_d15'), 'TN10_d15': fl('tn10_d15'),
        })
    print(f"\n   NORMAIS DO MÊS {mes:02d} NOS PONTOS ({p.replace('_', '-')}; chuva e ETo em mm/mês)")
    print(pd.DataFrame(tabela).to_string(index=False))

    # Assets já gravados entram na conferência quando existirem
    gravados_ok = None
    caminho = f"{asset_colecao('normais', p)}/{nome_imagem('normais', p, mes)}"
    if asset_existe(caminho):
        comp_g = comparar(amostrar(ee.Image(caminho), pontos), loc_n)
        gravados_ok = bool(comp_g.ok.all())
        print(f"   asset gravado {caminho.split('/')[-1]}: {int(comp_g.ok.sum())} de {len(comp_g)} valores iguais ao cálculo local")

    return {'numeros_ok': bool(comp.ok.all()), 'limiares_ok': bool(comp_l.ok.all()),
            'problemas': problemas, 'gravados_ok': gravados_ok}


# =========================================================================
# 9. ASSETS E TAREFAS
# =========================================================================
def asset_existe(caminho):
    try:
        ee.data.getAsset(caminho)
        return True
    except ee.EEException:
        return False


def listar_nomes(pai):
    nomes, token = [], None
    while True:
        params = {'parent': pai, 'pageSize': 1000}
        if token:
            params['pageToken'] = token
        resp = ee.data.listAssets(params)
        for a in resp.get('assets', []):
            nomes.append((a.get('id') or a.get('name')).split('/')[-1])
        token = resp.get('nextPageToken')
        if not token:
            return nomes


def tarefas_ativas():
    return {t.get('description', ''): t.get('state') for t in ee.data.getTaskList()
            if t.get('state') in ('READY', 'RUNNING', 'SUBMITTED', 'PENDING')}


def garantir_asset(caminho, tipo):
    if asset_existe(caminho):
        return
    if SIMULAR:
        print(f"🧪 [SIMULAÇÃO] Criaria {tipo.lower()}: {caminho}")
        return
    ee.data.createAsset({'type': tipo}, caminho)
    print(f"📁 Criado: {caminho}")


def plano_de_exportacao():
    ativas = tarefas_ativas()
    plano = []
    for p in PERIODOS_A_GERAR:
        for tipo in ('normais', 'limiares'):
            if tipo == 'limiares' and not GERAR_LIMIARES:
                continue
            col = asset_colecao(tipo, p)
            existentes = set(listar_nomes(col)) if asset_existe(col) else set()
            for mes in MESES_A_GERAR:
                nome, desc = nome_imagem(tipo, p, mes), descricao_tarefa(tipo, p, mes)
                if desc in ativas:
                    situacao = 'na fila'
                elif nome in existentes and not SOBRESCREVER:
                    situacao = 'já existe'
                else:
                    situacao = 'enviar'
                plano.append({'periodo': p, 'tipo': tipo, 'mes': mes, 'colecao': col, 'nome': nome,
                              'descricao': desc, 'situacao': situacao})
    return pd.DataFrame(plano), ativas


def avisar_assets_antigos():
    for nome in ('Baseline_Historico_1961_1990', 'Baseline_Operacional_1991_2020'):
        caminho = f'{PASTA_DESTINO}/{nome}'
        if asset_existe(caminho):
            print(f"⚠️ {nome} existe e foi gerado pelo script anterior (SICSB e estatística sobre dias). "
                  f"O painel não o usa; apague-o pela aba Assets quando quiser.")


def acompanhar(descricoes):
    """Mostra o andamento e, no fim, o tempo e o consumo de EECU de cada tarefa."""
    if not descricoes:
        return {}
    print(f"\n⏳ Acompanhando {len(descricoes)} tarefa(s) a cada {INTERVALO_ACOMPANHAMENTO_S} s. "
          f"Pode interromper a célula: as tarefas continuam no Earth Engine.")
    alvo = set(descricoes)
    try:
        while True:
            info = {}
            for t in ee.data.getTaskList():
                d = t.get('description', '')
                if d in alvo and d not in info:         # a lista vem da mais nova para a mais antiga
                    info[d] = t
            estados = {d: t.get('state') for d, t in info.items()}
            cont = pd.Series(list(estados.values()), dtype='object').value_counts().to_dict()
            print(f"   {datetime.now(timezone(timedelta(hours=-3))).strftime('%H:%M')} {cont}")
            if info and not any(s in ('READY', 'RUNNING', 'SUBMITTED', 'PENDING') for s in estados.values()):
                falhas = [d for d, s in estados.items() if s != 'COMPLETED']
                consumo = {}
                for d, t in info.items():
                    eecu = t.get('batch_eecu_usage_seconds')
                    ini, fim = t.get('start_timestamp_ms'), t.get('update_timestamp_ms')
                    minutos = (fim - ini) / 60000 if ini and fim else float('nan')
                    consumo[d] = {'eecu_h': (eecu or 0) / 3600 if eecu is not None else float('nan'), 'min': minutos}
                    print(f"   {d}: {estados[d]} | {minutos:.0f} min | "
                          f"{consumo[d]['eecu_h']:.2f} EECU-hora(s)" + (f" | {t.get('error_message')}" if t.get('error_message') else ''))
                print("✅ Todas concluídas." if not falhas else f"❌ Não concluídas: {falhas}. Rode o script de novo para reenviar só essas.")
                return consumo
            time.sleep(INTERVALO_ACOMPANHAMENTO_S)
    except KeyboardInterrupt:
        print("⏸️ Acompanhamento interrompido; as tarefas seguem na fila.")
        return {}


# =========================================================================
# 10. EXECUÇÃO
# =========================================================================
def main():
    print(f"\n{'🧪 MODO SIMULAÇÃO: nada será criado ou exportado' if SIMULAR else '🚀 MODO REAL'}")
    print("Critérios para seguir: inventário sem duplicatas e com anos suficientes, números do Earth Engine "
          "iguais ao cálculo local, limiares dentro da faixa e nenhuma incoerência física.")

    resultados_inv = {p: inventario(p) for p in sorted(set(PERIODOS_A_GERAR) | {PERIODO_VERIFICACAO})}
    avisar_assets_antigos()
    plano, ativas = plano_de_exportacao()
    a_enviar = plano[plano.situacao == 'enviar']
    print(f"\n📦 PLANO: {len(plano)} imagens | enviar {len(a_enviar)} | já existem "
          f"{int((plano.situacao == 'já existe').sum())} | na fila {int((plano.situacao == 'na fila').sum())}")
    if len(a_enviar):
        print(a_enviar.groupby(['periodo', 'tipo']).mes.apply(lambda s: f"meses {s.min():02d} a {s.max():02d}").to_string())

    if SIMULAR:
        criterios = {f"inventário {p.replace('_', '-')} (sem datas duplicadas, só dias definitivos, "
                     f"pelo menos {ANOS_MINIMOS} anos válidos em todo mês)": r['ok']
                     for p, r in resultados_inv.items()}
        if VERIFICAR:
            for mes in MESES_VERIFICACAO:
                try:
                    r = verificar(PERIODO_VERIFICACAO, mes)
                except ee.EEException as e:
                    print(f"\n❌ Conferência do mês {mes:02d} não terminou: {str(e)[:200]}")
                    criterios[f"conferência numérica concluída (mês {mes:02d})"] = False
                    continue
                criterios[f"números EE = local (mês {mes:02d})"] = r['numeros_ok']
                criterios[f"limiares na faixa (mês {mes:02d})"] = r['limiares_ok']
                criterios[f"coerência física (mês {mes:02d})"] = not r['problemas']
                for pr in r['problemas']:
                    print(f"   ⚠️ {pr}")
                if r['gravados_ok'] is not None:
                    criterios[f"assets gravados = local (mês {mes:02d})"] = r['gravados_ok']
        print("\n=== CRITÉRIOS ===")
        for k, v in criterios.items():
            print(f"{'✅' if v else '❌'} {k}")
        if all(criterios.values()):
            print("\n✅ Tudo conferido. Para gerar de verdade, mude SIMULAR para False e rode de novo "
                  "depois que as tarefas do motor terminarem (com PILOTO = True vai só o mês 01 primeiro).")
        else:
            print("\n❌ Há critério não atendido. Não exporte antes de entender o motivo; mande esta saída.")
        return

    motor = [d for d in ativas if d.startswith('SAB_M_')]
    if motor and ESPERAR_MOTOR:
        print(f"\n⏸️ {len(motor)} tarefa(s) do motor ainda na fila (ex.: {motor[0]}). A fila do Earth Engine "
              f"é a mesma; enviar as normais agora atrasaria a previsão. Rode de novo quando terminarem "
              f"(ou mude ESPERAR_MOTOR para False).")
        return

    if PILOTO:
        a_enviar = a_enviar.groupby('tipo', sort=False).head(1)
        print(f"\n🧭 PILOTO: só {', '.join(a_enviar.descricao)}. Mede tempo e EECU antes de enviar o resto.")
    garantir_asset(PASTA_DESTINO, 'FOLDER')
    for col in sorted(set(a_enviar.colecao)):
        garantir_asset(col, 'IMAGE_COLLECTION')
    enviadas = []
    for _, lin in a_enviar.iterrows():
        img = (imagem_normais(lin.periodo, lin.mes) if lin.tipo == 'normais'
               else imagem_limiares(lin.periodo, lin.mes))
        extra = {'overwrite': True} if SOBRESCREVER else {}
        tarefa = ee.batch.Export.image.toAsset(
            image=img, description=lin.descricao, assetId=f'{lin.colecao}/{lin.nome}',
            region=limitesRegiao, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e13, **extra)
        tarefa.start()
        enviadas.append(lin.descricao)
        print(f"🚀 {lin.descricao}")
    print(f"\n✔️ {len(enviadas)} tarefa(s) enviada(s). Acompanhe em https://code.earthengine.google.com/tasks")
    if ACOMPANHAR or PILOTO:
        consumo = acompanhar(enviadas)
        if PILOTO and consumo:
            todas = plano[plano.situacao == 'enviar']
            proj = 0.0
            for tipo, n in todas.groupby('tipo').size().items():
                medido = [v['eecu_h'] for d, v in consumo.items()
                          if d.startswith('SAB_NORMAIS_' if tipo == 'normais' else 'SAB_LIMIARES_') and v['eecu_h'] == v['eecu_h']]
                proj += (medido[0] if medido else float('nan')) * n
            print(f"\n📈 Projeção para as {len(todas)} imagens do plano: cerca de {proj:.0f} EECU-horas "
                  f"(cotas mensais não comerciais: Community 150, Contributor 1.000; veja a do projeto no Console do Google Cloud). "
                  f"Se couber, mude PILOTO para False e rode de novo; os meses prontos são pulados.")


main()
