# >>> K26 v1.10 (18/11/2026 19h50): AUDITORIA FINAL. Somente leitura. Cole inteiro; mude SÓ a linha RODADA. <<<
# =========================================================================================
# K26 - AUDITORIA FINAL ANTES DA ÚLTIMA VERSÃO DO BANCO
#
# VERSÕES (a 1ª linha do log repete a versão: confira que é a última antes de rodar)
#   v1.10 18/11 19h50 só configuração: rodada nova 12 = 2001-2025 de uma vez (modo rápido, ~4 h; RODADA = 12).
#                     2026 continua separado (rodada 1): com 2026 na faixa o modo rápido desliga para tudo.
#   v1.9 18/11 19h40  RODADA = 8 (1991-2000). Veredito de B, C e H separado por grupo de pixels: ENTREGUES
#                     (A, B, C_interior: vão às planilhas) x C_borda (fica fora; vira INFO). A2 escreve
#                     'V1.0 (sem propriedade)' em vez de vazio. LEITURA = 'gravado' volta a valer no modo
#                     rápido (a condição tinha ido parar dentro de um comentário). C anota a causa do
#                     escoamento > chuva nos dias definitivos (chuva observada x escoamento do modelo).
#                     H conta 'tem valor' (máscara > 0): a v1.8 somava a máscara FRACIONÁRIA dos pixels de costa
#                     e acusava 'pixels a menos' onde o valor existe (conferido em 4 dias de 1985: os 70.982
#                     pixels entregues têm valor nas bandas). Grava K26_H_mascara_v19.csv (não mistura com
#                     as contagens antigas).
#   v1.8 17/11 14h15  só configuração: RODADA = 7 (1981-1990); código igual à v1.6 (a rodada 6 levou 96 min)
#   v1.7 17/11 06h15  só configuração: RODADA = 6 (1971-1980); código igual à v1.6 (a rodada 5 levou 73 min)
#   v1.6 17/11 04h30  MODO RÁPIDO no histórico (rodadas 5 a 11): o servidor agrega o período inteiro;
#                     B = 3 pedidos por ano (sem histograma), C e H = 1 pedido por mês. A v1.5 fazia
#                     ~18 mil pedidos por década (~10 h); a v1.6 faz ~250. C diz o mês, não o dia.
#   v1.5 16/11 10h00  só configuração: RODADA = 5 (primeira década, 1961-1970); código igual à v1.4
#   v1.4 16/11 07h00  parte S (umidade do solo x SMAP, 5 correções) na nova rodada 4; décadas viram 5 a 11
#   v1.3 16/11 06h00  vento (V): imagens convertidas para Float antes da média (o servidor recusou o
#                     tipo com faixa do BR-DWGD); parte que quebra deixa o resumo "INCOMPLETO"
#   v1.2 15/11 22h30  parte Q (ERA5 cru nos pixels do Rs = 0) e teste rs_zero na parte C; rodada 2 = Q + R
#   v1.1 15/11 21h20  folga antes da janela do motor por rodada (45 min na rodada 1)
#   v1   15/11 20h40  primeira versão
#
# POR QUE ESTE ARQUIVO EXISTE
#   A K25 (15/11/2026, 14h01) varreu 2026 e deixou quatro coisas em aberto:
#     1. ESCOAMENTO: 116.412 pixel-dias ERA5 com escoamento superficial acima da chuva do dia e máximo
#        diário de 1.099 mm (fev/2026). Causa: runoff do ERA5-Land x fator SMAP/ERA5 das MÉDIAS mensais,
#        com teto 5. O histórico usa a mesma conta (o painel e o sab_pedido.py limitam a 5 na leitura).
#     2. VENTO: na emenda, o vento ERA5 de 2026 varia 1,67x o do BR-DWGD (parte F da K25).
#     3. ETo: os mesmos 20 pixels B/C_borda divergem 2,3-3,5 mm em 04-20/03 e 23/09-08/10/2026.
#     4. NADA varreu 1961-2025 com as 16 variáveis.
#   A K26 testa as correções candidatas FORA DA AMOSTRA (partes R e V), diagnostica os 20 pixels
#   (parte P) e varre o histórico inteiro, década a década, no valor que o USUÁRIO RECEBE (LEITURA).
#
# O QUE MUDOU EM RELAÇÃO À K25 (defeitos da própria K25 que a corrida de 14h01 mostrou)
#   - B: o veredito usava só o histograma, que perde o que passa do topo da faixa (o 1.099 mm de
#     fevereiro não foi marcado). Agora usa também o mínimo e o máximo absolutos de cada mês.
#   - C: o escoamento acima da chuva ganhou degraus (> chuva + 10 mm, + 50 mm e > 200 mm absolutos),
#     para separar arredondamento de valor absurdo.
#   - G: dia definitivo (ETo do BR-DWGD) não entra no veredito; ele é só informação.
#   - H: tsolo_C e tfolha_C vazias nos dias GFS são do motor (linha 1234: o GFS não tem equivalente);
#     não é vazamento de máscara.
#   - dias antigos com nomes de banda antigos (precipitation_mm, ...) são lidos pelos nomes novos,
#     como no sab_pedido.py; a K25 quebraria neles.
#
# AS PARTES
#   A  inventário, proveniência e contagem por classe (igual à K25)
#   B  perfil das 16 variáveis por classe e mês, com extremos absolutos no veredito
#   C  invariantes físicas e limites de Xavier et al. (2022), todos os dias, por classe e rota
#   G  ETo e VPD recalculados das primárias (só dias ERA5 e GFS no veredito)
#   H  máscara banda a banda
#   Q  o ERA5-Land cru nos pixels do Rs gravado = 0 (achado da rodada 1)
#   P  os pixels da ETo divergente e do Rs acima do céu claro: valores de entrada, elevação e a ETo
#      refeita de três jeitos, dia a dia em volta de cada bloco, para achar a causa
#   R  ESCOAMENTO: fator SMAP/ERA5 atual contra 11 alternativas, treino 2015-2020 e teste 2021-2025,
#      em pontos de classe A, contra o SMAP L4 diário. Escoamento superficial E subsuperficial.
#   V  VENTO: correção na média (atual) contra escala de variância, com o vento da média diária das
#      componentes (atual) e com a média da velocidade horária; treino 2016-2020, teste 2021-2025,
#      contra o BR-DWGD diário, com a regra de aprovação da K21 (viés <= 0,10 m/s)
#   S  UMIDADE DO SOLO: correção atual (fator SMAP/ERA5 com teto) contra cru, aditivo, variância e
#      mapeamento de quantis, nas duas camadas, contra o SMAP L4 diário (mesmos pontos e anos da R)
#   Z  estatística sobre os CSV (bootstrap de blocos, permutação, Mann-Whitney)
#
# LEITURA = 'entregue' (padrão): cada dia passa pela mesma correção de leitura do painel e do
#   sab_pedido.py 2026.11.03 (solo e escoamento dos dias V1.0, pixels B pelo BR-DWGD, Rs dos pixels C
#   no céu claro até 31/12/2025, ET real <= ETo e transpiração <= ET real). É o dado que o usuário
#   baixa. LEITURA = 'gravado' audita o asset cru. A parte P lê sempre o gravado (diagnóstico do motor).
#
# AS RODADAS (mude só RODADA; cada uma grava o zip; suba os CSV do zip anterior em
#   /content/K26_acumulado/ antes da seguinte, para o checkpoint por mês continuar de onde parou)
#   1  2026: A B C G H P Z ............. conferência das correções da K26 em 2026 + diagnóstico P (~30 min)
#   2  Q R  ERA5 cru nos pixels do Rs = 0 (Q) + escoamento (R) ......... (rodou em 37 min, 16/11)
#   3  V  vento ........................................................... (rodou em 11 min, 16/11)
#   4  S  umidade do solo ......................................................... (rodou em 26 min, 16/11)
#   5  1961-1970: A B C H Z
#   6  1971-1980   7  1981-1990   8  1991-2000   9  2001-2010   10  2011-2020   11  2021-2025
#   12 2001-2025 de uma vez (= 9 + 10 + 11; ~4 h; deixe a aba do Colab aberta até o fim)
#      (modo rápido: 1961-1970 levou 73 min em 17/11)
#
# COMO RODAR NO COLAB
#   1. Ambiente de execução -> Reiniciar sessão.
#   2. Mude RODADA logo abaixo. Nada mais.
#   3. Cole o arquivo inteiro numa célula e Ctrl+Enter. Fora da janela do motor (22h50-01h00).
#   4. No fim baixa K26_<data>.zip. Me envie.
#
# MEMÓRIA: igual à K25 (4 faixas de latitude que se dividem sozinhas, lotes de dias que caem pela
#   metade, checkpoint por mês). R e V leem pontos (getRegion), um mês por pedido, e também têm
#   checkpoint por mês.
# =========================================================================================
import json
import math
import os
import shutil
import time
import traceback
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- o que rodar
RODADA = 12
RODADAS = {
    1: (2026, 2026, ('A', 'B', 'C', 'G', 'H', 'P', 'Z')),
    2: (2026, 2026, ('Q', 'R', 'Z')),
    3: (2026, 2026, ('V', 'Z')),
    4: (2026, 2026, ('S', 'Z')),
    5: (1961, 1970, ('A', 'B', 'C', 'H', 'Z')),
    6: (1971, 1980, ('A', 'B', 'C', 'H', 'Z')),
    7: (1981, 1990, ('A', 'B', 'C', 'H', 'Z')),
    8: (1991, 2000, ('A', 'B', 'C', 'H', 'Z')),
    9: (2001, 2010, ('A', 'B', 'C', 'H', 'Z')),
    10: (2011, 2020, ('A', 'B', 'C', 'H', 'Z')),
    11: (2021, 2025, ('A', 'B', 'C', 'H', 'Z')),
    12: (2001, 2025, ('A', 'B', 'C', 'H', 'Z')),     # [v1.10] as rodadas 9, 10 e 11 de uma vez (~4 h)
}
ANO_INI, ANO_FIM, PARTES = RODADAS[RODADA]
LEITURA = 'entregue'             # 'entregue' (o que o usuário baixa) ou 'gravado' (o asset cru)
SIMULACAO_PERMITIDA = False      # só o simular_K26.py liga isto. Deixe False SEMPRE.
VERSAO = 'K26 v1.10 (18/11/2026 19h50)'   # muda a CADA alteração do código, junto com a 1ª linha e a lista VERSÕES

PROJETO = 'clima-492922'
ASSET_SAB = f'projects/{PROJETO}/assets/SAB_V1'
ASSET_MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
ASSET_EQM = f'projects/{PROJETO}/assets/SICSB_EQM_1986_2025'
BR_DWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ASSET_SOLO = f'projects/{PROJETO}/assets/SICSB_SOLO_2015_2025'
SMAP_L4 = 'NASA/SMAP/SPL4SMGP/008'
ERA5_DIA = 'ECMWF/ERA5_LAND/DAILY_AGGR'
ERA5_HORA = 'ECMWF/ERA5_LAND/HOURLY'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
X0, Y0, DX = TRANSFORM[2], TRANSFORM[5], TRANSFORM[0]

BANDAS = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2',
          'tsolo_C', 'tfolha_C', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm',
          'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
# dias antigos do SAB_V1 têm estes nomes (mesma ordem); o sab_pedido.py 2026.11.03 lê assim
BANDAS_ANTIGAS = ['precipitation_mm', 'temp_max_C', 'temp_min_C', 'relative_humidity_pct', 'et_potential_mm',
                  'et_actual_mm', 'vpd_kpa', 'solar_radiation_mj_m2', 'wind_speed_m_s', 'soil_temperature_C',
                  'skin_temperature_C', 'transpiration_mm', 'surface_runoff_mm', 'subsurface_runoff_mm',
                  'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
# ---- correção de leitura do painel / sab_pedido.py 2026.11.03 (se ela mudar, mude aqui também) ----
FIM_HISTORICO_CORRECAO = '2026-01-01'      # exclusivo: pixels B e Rs dos C corrigidos só até 31/12/2025
NUCLEO_B = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'rs', 'u2', 'vpd']
TETO_FATOR_LEITURA = 5.0                   # fator SMAP/ERA5 dos dias V1.0 limitado a 5 na leitura
# bandas que o motor deixa vazias de propósito numa rota (não é vazamento de máscara)
VAZIAS_POR_DESENHO = {'GFS': ('tsolo_C', 'tfolha_C')}
# motor V1.6, BANDAS_MASCARADAS_INCOMPLETO: dia GFS sem todos os blocos de chuva/radiação
VAZIAS_POR_VERSAO = {'provisoria_gfs_incompleta': ('pr_mm', 'rs', 'et_potencial', 'et_real', 'transpiracao_mm')}

# ---- parte R: escoamento contra o SMAP L4 ------------------------------------------------
R_INICIO, R_FIM = '2015-04-01', '2026-01-01'   # o SMAP L4 começa em 31/03/2015
R_ANOS_TREINO = (2015, 2020)
R_ANOS_TESTE = (2021, 2025)
N_PONTOS_R = 300
# candidatos: (nome, K, teto). fator = (m_smap + K) / (m_era5 + K), limitado a teto; K = 0 e teto
# None = sem limite. 'sem_fator' é o ERA5-Land cru. O primeiro é a conta de hoje.
CANDIDATOS_R = [('atual_teto5', 0.0, 5.0), ('sem_fator', None, None), ('teto2', 0.0, 2.0), ('teto3', 0.0, 3.0)] + \
               [(f'K{k:g}_teto{t:g}', k, t) for k in (0.1, 0.5, 1.0) for t in (2.0, 3.0, 5.0)]
# regra de escolha, fixada ANTES de ver o resultado:
#   aprovado = |viés do total| <= 15% E razão do p99 dos dias com escoamento em [0,67; 1,5]
#              E escoamento superficial > chuva do ERA5-Land (mesma janela 00-24 UTC) em no máximo
#              0,1% dos ponto-dias (só para o superficial: o subsuperficial é drenagem e passa da chuva);
#   entre os aprovados, o menor erro absoluto médio diário.
#   O SMAP L4 é modelo (Catchment), não observação: "mais perto do SMAP" quer dizer mais perto da
#   referência que a V1.0 escolheu, não da verdade.
R_MAX_VIES_PCT = 15.0
R_FAIXA_P99 = (0.67, 1.5)
R_MAX_PCT_GT_PR = 0.1

# ---- parte V: vento contra o BR-DWGD ------------------------------------------------------
V_ANOS_TREINO = (2016, 2020)
V_ANOS_TESTE = (2021, 2025)
N_PONTOS_V = 150
V_RAZAO_DESVIO = (0.5, 2.0)      # limite da razão s_br / s_era na escala de variância (como no GFS)
V_MAX_VIES = 0.10                # m/s, a regra da K21
CONV_U10_U2 = 0.748              # FAO-56 eq. 47 para 10 m, como no motor

# ---- parte S: umidade do solo contra o SMAP L4 (mesmos pontos, anos e treino/teste da parte R) ----
# camadas: superficial = ERA5-Land camada 1 (0-7 cm) x SMAP sm_surface (0-5 cm);
#          0-100 cm   = (7 l1 + 21 l2 + 72 l3) / 100, como o motor, x SMAP sm_rootzone (0-100 cm)
# candidatos: atual (x * min(m_smap/m_era, 5), teto min(m_smap + 3 s_smap, 0,9)), cru, aditivo (desloca a
#   média), variancia (média e desvio do SMAP, razão limitada a [0,5; 2]) e eqm (mapeamento de quantis,
#   21 quantis por pixel e mês: o método padrão para umidade do solo). Todos limitados a [0; 0,9].
# regra de escolha, fixada ANTES de ver o resultado: aprovado = |viés| <= 0,02 m³/m³ E razão dos desvios
#   em [0,8; 1,25]; entre os aprovados, o menor erro absoluto médio diário.
S_MAX_VIES = 0.02
S_FAIXA_RAZAO = (0.8, 1.25)
S_QUANTIS = np.linspace(0, 1, 21)

# ---- parte P: pixels da ETo e do Rs ----------------------------------------------------
# datas de dentro dos blocos que a K25 achou; a janela de cada uma vai de -10 a +10 dias
P_DATAS = ['2026-03-10', '2026-03-27', '2026-09-05', '2026-09-28']
P_JANELA_DIAS = 10
P_TOL_ETO = 0.5                  # mm: divergência que conta como "o pixel do bloco"
P_MAX_PIXELS = 60

# ---- parte Q: o ERA5-Land cru nos pixels do Rs = 0 (achados da rodada 1, 15/11/2026 21h16) ----
Q_PIXELS = [(-50.75035, 0.15008),     # B, foz do Amazonas
            (-48.45039, -0.74991),    # C_borda, Pará
            (-45.15044, -1.34990),    # C_borda, Maranhão (Rs 4,7 e não 0 em 10/03: caso parcial)
            (-46.35042, -24.04955),   # C_borda, litoral de SP
            (-48.45039, -26.24952)]   # C_borda, litoral de SC
Q_JANELAS = [('2026-02-28', '2026-03-23'), ('2026-09-19', '2026-10-11')]

# Faixa declarada de cada banda, para o histograma normalizado e para a contagem de fora-da-faixa.
# NÃO é um limite físico: é o intervalo em que o valor tem de cair para ser plausível no Brasil.
FAIXA = {'pr_mm': (0, 500), 'tmax_C': (-10, 50), 'tmin_C': (-15, 40), 'RH': (0, 100),
         'et_potencial': (0, 15), 'et_real': (0, 15), 'vpd': (0, 10), 'rs': (0, 45), 'u2': (0, 30),
         'tsolo_C': (-10, 50), 'tfolha_C': (-10, 60), 'transpiracao_mm': (0, 15),
         'runoff_sup_mm': (0, 500), 'runoff_sub_mm': (0, 500),
         'soil_moisture_0_5cm_m3_m3': (0, 0.95), 'soil_moisture_0_100cm_m3_m3': (0, 0.95)}

CLASSES = {1: 'A', 2: 'B', 3: 'C_interior', 4: 'C_borda'}
# [v1.9] grupos do veredito: as classes ENTREGUES vão às planilhas do painel e dos pedidos; a C_borda (pixel sem
# BR-DWGD com centro fora do Brasil) fica fora delas, então o que só acontece nela é informação, não falha.
GRUPO_ENTREGUE = (1, 2, 3)
GRUPO_BORDA = (4,)
NOMES_ENTREGUE = tuple(CLASSES[k] for k in GRUPO_ENTREGUE)
NOTA_ESCOAMENTO = ('Nos dias definitivos (até 2025) a chuva é a OBSERVADA (BR-DWGD, 12-12 UTC) e o escoamento é do '
                   'ERA5-Land (00-24 UTC), que responde à chuva do próprio modelo: dia a dia eles não batem, embora '
                   'no total o escoamento seja ~21% da chuva. Teste do alinhamento das janelas rejeitado; correção '
                   'proposta (coeficiente do ERA5 x chuva observada) em pesquisa/ESCOAMENTO.md do sab-pedidos.')
BLOCOS = [(-75.0, -5.0, -28.0, 6.5), (-75.0, -14.0, -28.0, -5.0),
          (-75.0, -23.0, -28.0, -14.0), (-75.0, -35.0, -28.0, -23.0)]

# ---- constantes copiadas do motor V1.6 (se o motor mudar, mude aqui também) -------------
UMIDADE_MAX_FISICA = 0.9
FATOR_TETO_CHUVA = 1.5
SW5_MAX_MM, SW100_MAX_MM = 25.0, 400.0
TOL_RSO_MOTOR = 0.001            # o motor marca rs > 1,001 x Rso
TOL_RSO_AUDIT = 0.02             # a T5 marcou rs > 1,02 x Rso; os dois contam, para comparar
# Xavier et al. (2022): limites aplicados às observações que entram no BR-DWGD
LIM_PR = (0.0, 450.0)            # 0 < pr < 450 mm
LIM_RS_FRAC = (0.03, 1.0)        # 0,03 Ra <= Rs < Ra
LIM_U2 = (0.0, 100.0)
LIM_T = (-30.0, 50.0)
ANOS_RECORDE = (1991, 2025)
# Se um campo passa do recorde de 35 anos em mais do que isto, o problema quase certamente é a
# REFERÊNCIA (decodificação do BR-DWGD), não o dado: um campo bem calibrado fica na ordem de 0,1%.
MAX_PCT_REFERENCIA_SUSPEITA = 20.0
# Como medir "acima do recorde do pixel": aditivo em graus para temperatura, multiplicativo para o
# resto (somar 1 mm ao recorde de chuva não quer dizer nada; multiplicar por 1,1 quer).
LIMIARES_REC = {'tmax_C': ('mais', (0.0, 1.0, 2.0), '°C'), 'tmin_C': ('mais', (0.0, 1.0, 2.0), '°C'),
                'pr_mm': ('vezes', (1.0, 1.1, 1.5), 'x'), 'rs': ('vezes', (1.0, 1.05, 1.1), 'x'),
                'u2': ('vezes', (1.0, 1.1, 1.5), 'x')}
ANOS_REF_EMENDA = (2016, 2025)
N_PONTOS_EMENDA = 150
SEMENTE = 25
TOL_ETO = 0.01                   # mm/dia: divergência aceitável no recálculo da ETo
TOL_VPD = 0.005                  # kPa
BINS = 512
PERCENTIS = (1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9)
ALFA = 0.05
N_BOOT = 1000
N_PERM = 10000
MAX_PIXELS_LISTA = 3000          # no máximo tantos pixels violadores listados por teste

DIAS_POR_PEDIDO = 4
JANELAS_MOTOR = [((22, 50), (24, 0)), ((0, 0), (1, 0))]
# folga exigida antes da janela do motor, por rodada (a 1 é a K25 sem E e F, que levou 32 min com elas)
DURACAO_ESTIMADA_MIN = {1: 45, 2: 60, 3: 30, 4: 60, 12: 240}.get(RODADA, 90)

BRT = timezone(timedelta(hours=-3))
AGORA = datetime.now(BRT)
RAIZ = '/content' if os.path.isdir('/content') else '.'
ACUMULADO = os.path.join(RAIZ, 'K26_acumulado')          # CSV de sessões anteriores entram aqui
PASTA = os.path.join(RAIZ, f'K26_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K26.txt')
RESULTADOS = []


def log(*partes):
    texto = ' '.join(str(p) for p in partes)
    print(texto, flush=True)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(texto + '\n')


def resultado(item, status, titulo, texto):
    RESULTADOS.append({'item': item, 'status': status, 'titulo': titulo, 'texto': texto})
    simb = {'OK': '✅', 'FALHA': '❌', 'ATENCAO': '⚠️', 'INFO': 'ℹ️', 'ESPERAR': '⏳'}.get(status, '•')
    log(f'{simb} {item} {status}: {titulo}\n   {texto}')


def caminho(nome):
    return os.path.join(PASTA, nome)


def falhou_parte(nome, e, detalhe=''):
    """Uma parte que quebra NÃO derruba a corrida: fica registrada e o resto segue."""
    msg = f'{type(e).__name__}: {str(e)[:260]}'
    log(f'   ⚠️ parte {nome} interrompida -> {msg}')
    log('   ' + traceback.format_exc(limit=4).replace(chr(10), chr(10) + '   '))
    resultado(nome, 'FALHOU', f'parte {nome} interrompida (as outras seguiram)',
              msg + (f' | {detalhe}' if detalhe else '') +
              ' | o CSV do que já tinha sido lido está no zip; rode esta parte sozinha depois')


def ler_acumulado(nome):
    """CSV de sessões anteriores (para o checkpoint por mês). Devolve DataFrame vazio se não houver."""
    for base in (PASTA, ACUMULADO):
        p = os.path.join(base, nome)
        if os.path.exists(p):
            try:
                return pd.read_csv(p, sep=';', decimal=',')
            except Exception:
                pass
    return pd.DataFrame()


def gravar(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(caminho(nome), sep=';', decimal=',', index=False)
    return caminho(nome)


def acrescentar(df, nome):
    """Junta com o que já existe (checkpoint) e grava."""
    velho = ler_acumulado(nome)
    novo = pd.concat([velho, df], ignore_index=True) if len(velho) else df
    return gravar(novo, nome)


# =========================================================================================
# FUNÇÕES PURAS — testadas offline em 03_testes_offline/teste_K25.py (nenhuma fala com o servidor)
# =========================================================================================
def minutos_ate_janela(agora):
    m = agora.hour * 60 + agora.minute
    melhor = None
    for (h1, m1), (h2, m2) in JANELAS_MOTOR:
        ini, fim = h1 * 60 + m1, h2 * 60 + m2
        if ini <= m < fim:
            return 0
        falta = (ini - m) % (24 * 60)
        melhor = falta if melhor is None else min(melhor, falta)
    return melhor


def meses_do_intervalo(ano_ini, ano_fim):
    return [f'{a}-{m:02d}' for a in range(ano_ini, ano_fim + 1) for m in range(1, 13)]


def meses_a_fazer(todos, feitos):
    return [m for m in todos if m not in set(feitos)]


def dividir(b):
    """Divide um bloco de latitude em dois. Devolve os dois blocos."""
    lon0, lat0, lon1, lat1 = b
    meio = (lat0 + lat1) / 2.0
    return (lon0, lat0, lon1, meio), (lon0, meio, lon1, lat1)


def lotes(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]


def classificar_rota(versao):
    """Rota de cada dia a partir da propriedade 'versao' gravada."""
    if versao is None:
        return 'desconhecida'
    v = str(versao)
    if v.startswith('provisoria_gfs') or v.startswith('falha_latencia_gfs'):
        return 'GFS'
    if v.startswith('provisoria'):
        return 'ERA5'
    return 'BR-DWGD'


def ler_grupos(bruto, nomes, chave_soma='sum'):
    """Resposta de um reducer agrupado -> {classe: {nome: valor}}.
    bruto: {'groups': [{'classe': 1, 'sum': [v1, v2, ...]}, ...]} ou com valor escalar."""
    saida = {}
    for g in (bruto or {}).get('groups', []):
        k = int(g['classe'])
        v = g.get(chave_soma)
        if isinstance(v, list):
            saida[k] = {n: (v[i] if i < len(v) else None) for i, n in enumerate(nomes)}
        else:
            saida[k] = {nomes[0]: v}
    return saida


def somar_grupos(partes, nomes):
    """Soma, classe a classe, os dicionários de vários blocos."""
    total = {}
    for p in partes:
        for k, d in p.items():
            alvo = total.setdefault(k, {n: 0.0 for n in nomes})
            for n in nomes:
                x = d.get(n)
                if x is not None:
                    alvo[n] += float(x)
    return total


def juntar_hist(partes):
    """Soma histogramas de vários blocos. partes: lista de arrays (n_bandas, BINS)."""
    acc = None
    for h in partes:
        a = np.asarray(h, dtype=float)
        acc = a if acc is None else acc + a
    return acc


def percentis_de_hist(hist, lo, hi, percentis=PERCENTIS):
    """Percentis exatos até a largura do bin, a partir de um histograma de BINS bins em [lo, hi]."""
    h = np.asarray(hist, dtype=float)
    n = h.sum()
    if n <= 0:
        return {f'p{p:g}': float('nan') for p in percentis}
    bordas = np.linspace(lo, hi, len(h) + 1)
    acum = np.cumsum(h) / n
    saida = {}
    for p in percentis:
        i = int(np.searchsorted(acum, p / 100.0, side='left'))
        i = min(i, len(h) - 1)
        saida[f'p{p:g}'] = float((bordas[i] + bordas[i + 1]) / 2.0)
    return saida


def degrau_quantizacao(hist, lo, hi):
    """Se os valores vierem de inteiro com escala, os bins ocupados ficam espaçados de forma regular.
    Devolve (n_bins_ocupados, degrau_mediano_em_unidades) ou (n, nan) se não houver padrão."""
    h = np.asarray(hist, dtype=float)
    ocup = np.flatnonzero(h > 0)
    if len(ocup) < 3:
        return int(len(ocup)), float('nan')
    larg = (hi - lo) / len(h)
    d = np.diff(ocup)
    if len(d) == 0 or np.median(d) <= 1:
        return int(len(ocup)), float('nan')
    return int(len(ocup)), float(np.median(d) * larg)


def fracao_fora(hist, lo, hi, faixa):
    """Fração do histograma INTEIRAMENTE fora de faixa. Conta um bin como abaixo só se a sua borda
    direita já estiver abaixo do mínimo, e como acima só se a borda esquerda já estiver acima do
    máximo. Comparar pelo centro, como a v2 fazia, acusava o bin que contém o próprio limite: um
    valor exatamente 0 ou exatamente 100 aparecia como fora da faixa."""
    h = np.asarray(hist, dtype=float)
    n = h.sum()
    if n <= 0:
        return float('nan'), float('nan')
    bordas = np.linspace(lo, hi, len(h) + 1)
    esq, dir_ = bordas[:-1], bordas[1:]
    return float(h[dir_ <= faixa[0]].sum() / n), float(h[esq >= faixa[1]].sum() / n)


def razao_e_vies(sab, ref, variavel):
    """Razão dos desvios dentro do mês (2026 / BR-DWGD 2016-2025) e viés das médias, nos mesmos pixels.
    sab: pid, data, <variavel>. ref: pid, mes, <variavel>_sd, <variavel>_m."""
    d = sab.dropna(subset=[variavel]).copy()
    if not len(d):
        return float('nan'), float('nan'), 0
    d['am'] = d['data'].str[:7]
    d['mes'] = d['data'].str[5:7].astype(int)
    g = d.groupby(['pid', 'am'])[variavel]
    sd = pd.DataFrame({'sd': g.std(), 'n': g.size()}).reset_index()
    sd = sd[sd['n'] >= 10]
    sd['mes'] = sd['am'].str[5:7].astype(int)
    m = sd.merge(ref[['pid', 'mes', f'{variavel}_sd']], on=['pid', 'mes']).dropna()
    razao = (float(np.sqrt((m['sd'] ** 2).mean()) / np.sqrt((m[f'{variavel}_sd'] ** 2).mean()))
             if len(m) and np.sqrt((m[f'{variavel}_sd'] ** 2).mean()) > 0 else float('nan'))
    md = (d.groupby(['pid', 'mes'])[variavel].mean().rename('m').reset_index()
          .merge(ref[['pid', 'mes', f'{variavel}_m']], on=['pid', 'mes']).dropna())
    vies = float((md['m'] - md[f'{variavel}_m']).mean()) if len(md) else float('nan')
    return razao, vies, int(len(m))


def bootstrap_blocos(x, n_rep=N_BOOT, tamanho=5, semente=SEMENTE):
    """IC 95% da média por bootstrap de blocos consecutivos (respeita a autocorrelação diária)."""
    x = np.asarray([v for v in x if np.isfinite(v)], dtype=float)
    if len(x) < tamanho * 2:
        return float('nan'), float('nan')
    rng = np.random.default_rng(semente)
    n_blocos = int(np.ceil(len(x) / tamanho))
    inicios = np.arange(len(x) - tamanho + 1)
    medias = np.empty(n_rep)
    for i in range(n_rep):
        esc = rng.choice(inicios, n_blocos, replace=True)
        amostra = np.concatenate([x[s:s + tamanho] for s in esc])[:len(x)]
        medias[i] = amostra.mean()
    return float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))


def permutacao(a, b, n_rep=N_PERM, semente=SEMENTE):
    """p exato (bilateral) da diferença de médias por permutação. Devolve (dif, p, n_a, n_b)."""
    a = np.asarray([v for v in a if np.isfinite(v)], dtype=float)
    b = np.asarray([v for v in b if np.isfinite(v)], dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float('nan'), float('nan'), len(a), len(b)
    obs = a.mean() - b.mean()
    junto = np.concatenate([a, b])
    rng = np.random.default_rng(semente)
    conta = 0
    for _ in range(n_rep):
        rng.shuffle(junto)
        if abs(junto[:len(a)].mean() - junto[len(a):].mean()) >= abs(obs) - 1e-12:
            conta += 1
    return float(obs), float((conta + 1) / (n_rep + 1)), len(a), len(b)


def outliers_tukey(x):
    """Regra de Tukey (1,5 e 3,0 IQR). Devolve (n_moderados, n_extremos, limites)."""
    x = np.asarray([v for v in x if np.isfinite(v)], dtype=float)
    if len(x) < 4:
        return 0, 0, (float('nan'), float('nan'))
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    mod = int(((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)).sum())
    ext = int(((x < q1 - 3.0 * iqr) | (x > q3 + 3.0 * iqr)).sum())
    return mod, ext, (float(q1 - 1.5 * iqr), float(q3 + 1.5 * iqr))


def eto_fao56_numpy(tmax, tmin, rh, u2, rs, ra, z):
    """A MESMA conta do eto_penman_monteith do motor, em numpy, para o teste offline da parte G."""
    p = 101.3 * ((293.0 - 0.0065 * z) / 293.0) ** 5.26
    gamma = 0.000665 * p
    tm = (tmax + tmin) / 2.0
    es = (0.6108 * np.exp(17.625 * tmax / (tmax + 243.04)) +
          0.6108 * np.exp(17.625 * tmin / (tmin + 243.04))) / 2.0
    ea = es * rh / 100.0
    vpd = np.maximum(es - ea, 0.0)
    rso = (0.75 + 2e-5 * z) * ra
    rs_rso = np.clip(rs / rso, 0.0, 1.0)
    rns = 0.77 * rs
    rad = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2.0
    rn = rns - np.maximum(rad * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * rs_rso - 0.35), 0.0)
    delta = 4283.58 * (0.6108 * np.exp(17.625 * tm / (tm + 243.04))) / (tm + 243.04) ** 2
    num = 0.408 * delta * rn + gamma * (900.0 / (tm + 273.0)) * u2 * vpd
    return np.maximum(num / (delta + gamma * (1.0 + 0.34 * u2)), 0.0), vpd


def decidir_invariantes(total):
    """total: {classe: {flag: n}}. Devolve (status, texto)."""
    soma = {}
    for d in total.values():
        for k, v in d.items():
            if k != 'n_pix':
                soma[k] = soma.get(k, 0.0) + float(v or 0)
    ruins = {k: int(v) for k, v in soma.items() if v > 0 and not k.startswith('i_')}
    infos = {k: int(v) for k, v in soma.items() if v > 0 and k.startswith('i_')}
    n = sum(float(d.get('n_pix') or 0) for d in total.values())
    extra = ('; informativos, não são violação: '
             + ', '.join(f'{k} {v:,}' for k, v in sorted(infos.items()))) if infos else ''
    if not ruins:
        return 'OK', f'{int(n):,} pixel-dias, nenhuma violação' + extra
    return ('FALHA', f'{int(n):,} pixel-dias; violações: '
            + ', '.join(f'{k} {v:,}' for k, v in sorted(ruins.items())) + extra)


def folga_seam(a, b):
    """Descontinuidade relativa entre dois valores (último dia de uma rota, primeiro da outra)."""
    if a is None or b is None or not np.isfinite(a) or not np.isfinite(b) or a == 0:
        return float('nan')
    return float(b / a)


def fator_candidato(m_alvo, m_modelo, K, teto):
    """Fator de um candidato da parte R. K None = sem fator (1). K = 0 é a conta da V1.0
    (m_alvo / max(m_modelo, 1e-3)); K > 0 estabiliza os meses secos, como a chuva do GFS."""
    m_alvo = np.asarray(m_alvo, dtype=float)
    m_modelo = np.asarray(m_modelo, dtype=float)
    if K is None:
        return np.ones_like(m_alvo)
    if K == 0:
        f = m_alvo / np.maximum(m_modelo, 1e-3)
    else:
        f = (m_alvo + K) / (np.maximum(m_modelo, 0.0) + K)
    return np.minimum(f, teto) if teto is not None else f


def _anos(serie_data, intervalo):
    a = serie_data.str[:4].astype(int)
    return (a >= intervalo[0]) & (a <= intervalo[1])


def avaliar_fatores(df, alvo, modelo, candidatos, treino, teste, pr=None):
    """Parte R, offline. df: pid, data (AAAA-MM-DD), <alvo> (SMAP), <modelo> (ERA5-Land cru) e,
    se pr, a chuva do ERA5-Land. As médias mensais por pixel saem SÓ dos anos de treino e o erro é
    medido SÓ nos anos de teste: a matriz SICSB_SOLO usa 2015-2025 inteiro, e testar nela mesma
    seria medir o ajuste, não a previsão. Devolve uma linha por candidato."""
    d = df.dropna(subset=[alvo, modelo]).copy()
    d['mes'] = d['data'].str[5:7].astype(int)
    tr = d[_anos(d['data'], treino)]
    te = d[_anos(d['data'], teste)].copy()
    medias = tr.groupby(['pid', 'mes']).agg(m_alvo=(alvo, 'mean'), m_modelo=(modelo, 'mean')).reset_index()
    te = te.merge(medias, on=['pid', 'mes'], how='inner')
    linhas = []
    if not len(te):
        return pd.DataFrame(linhas)
    obs = te[alvo].to_numpy()
    molhado_obs = obs[obs > 0.1]
    p99_obs = float(np.percentile(molhado_obs, 99)) if len(molhado_obs) else float('nan')
    te['am'] = te['data'].str[:7]
    for nome, K, teto in candidatos:
        prev = te[modelo].to_numpy() * fator_candidato(te['m_alvo'], te['m_modelo'], K, teto)
        molhado = prev[prev > 0.1]
        p99 = float(np.percentile(molhado, 99)) if len(molhado) else float('nan')
        mens = (te.assign(prev=prev).groupby(['pid', 'am'])[['prev', alvo]].sum())
        linha = {'candidato': nome, 'K': K, 'teto': teto, 'n_ponto_dias': int(len(te)),
                 'vies_total_pct': float(100.0 * (prev.sum() / obs.sum() - 1.0)) if obs.sum() > 0 else float('nan'),
                 'mae_diario': float(np.mean(np.abs(prev - obs))),
                 'rmse_diario': float(np.sqrt(np.mean((prev - obs) ** 2))),
                 'mae_mensal': float(np.mean(np.abs(mens['prev'] - mens[alvo]))),
                 'p99_prev': p99, 'p99_ref': p99_obs,
                 'razao_p99': p99 / p99_obs if p99_obs and np.isfinite(p99_obs) and p99_obs > 0 else float('nan'),
                 'max_prev': float(prev.max()), 'max_ref': float(obs.max()),
                 'corr_diaria': float(np.corrcoef(prev, obs)[0, 1]) if prev.std() > 0 and obs.std() > 0 else float('nan')}
        if pr is not None and pr in te:
            chuva = te[pr].to_numpy()
            ok = np.isfinite(chuva)
            linha['pct_acima_chuva'] = float(100.0 * np.mean(prev[ok] > chuva[ok] + 0.01)) if ok.any() else float('nan')
            linha['pct_acima_chuva_10mm'] = float(100.0 * np.mean(prev[ok] > chuva[ok] + 10.0)) if ok.any() else float('nan')
        linhas.append(linha)
    return pd.DataFrame(linhas)


def escolher_fator(tab, com_chuva):
    """Aplica a regra fixada em CANDIDATOS_R. Devolve (tabela com 'aprovado', nome escolhido ou None)."""
    t = tab.copy()
    if not len(t):
        return t, None
    ok = (t['vies_total_pct'].abs() <= R_MAX_VIES_PCT) & t['razao_p99'].between(*R_FAIXA_P99)
    if com_chuva and 'pct_acima_chuva' in t:
        ok &= t['pct_acima_chuva'] <= R_MAX_PCT_GT_PR
    t['aprovado'] = ok.fillna(False)
    aprov = t[t['aprovado']]
    return t, (aprov.sort_values('mae_diario').iloc[0]['candidato'] if len(aprov) else None)


def razao_desvio_mensal(d, prev, ref):
    """Razão dos desvios dentro do pixel-mês (como a parte F), com no mínimo 10 dias por pixel-mês."""
    g = d.assign(_p=prev, _r=ref).groupby(['pid', 'am'])
    sd = pd.DataFrame({'sp': g['_p'].std(), 'sr': g['_r'].std(), 'n': g.size()})
    sd = sd[sd['n'] >= 10].dropna()
    if not len(sd) or (sd['sr'] ** 2).mean() <= 0:
        return float('nan')
    return float(np.sqrt((sd['sp'] ** 2).mean() / (sd['sr'] ** 2).mean()))


def avaliar_vento(df, treino, teste, fontes=('era_dia', 'era_hora'), ref='br_u2'):
    """Parte V, offline. df: pid, data, br_u2, era_dia, era_hora (ERA5-Land a 2 m, sem correção).
    Médias e desvios por pixel e mês SÓ do treino; erro SÓ no teste. Dois métodos:
      media      x * min(m_br / m_era, 5)                           (o da V1.6 nos dias ERA5)
      variancia  m_br + (x - m_era) * clip(s_br / s_era, 0,5, 2,0)  (o da rota GFS desde a K9A)"""
    linhas = []
    for fonte in fontes:
        if fonte not in df:
            continue
        d = df.dropna(subset=[ref, fonte]).copy()
        d['mes'] = d['data'].str[5:7].astype(int)
        d['am'] = d['data'].str[:7]
        tr = d[_anos(d['data'], treino)]
        te = d[_anos(d['data'], teste)]
        est = tr.groupby(['pid', 'mes']).agg(m_br=(ref, 'mean'), s_br=(ref, 'std'),
                                             m_e=(fonte, 'mean'), s_e=(fonte, 'std')).reset_index()
        te = te.merge(est, on=['pid', 'mes'], how='inner')
        if not len(te):
            continue
        x, obs = te[fonte].to_numpy(), te[ref].to_numpy()
        metodos = {
            'cru': x,
            'media': x * np.minimum(te['m_br'] / np.maximum(te['m_e'], 1e-3), 5.0),
            'variancia': np.maximum(te['m_br'] + (x - te['m_e']) *
                                    np.clip(te['s_br'] / np.maximum(te['s_e'], 1e-6), *V_RAZAO_DESVIO), 0.0),
        }
        for metodo, prev in metodos.items():
            prev = np.asarray(prev, dtype=float)
            razao = razao_desvio_mensal(te, prev, obs)
            vies = float(np.mean(prev - obs))
            linhas.append({'fonte': fonte, 'metodo': metodo, 'n_ponto_dias': int(len(te)),
                           'vies_m_s': vies, 'mae_m_s': float(np.mean(np.abs(prev - obs))),
                           'erro_rel_pct': float(100 * np.mean(np.abs(prev - obs)) / np.mean(obs)),
                           'razao_desvio': razao,
                           'corr_diaria': float(np.corrcoef(prev, obs)[0, 1]) if prev.std() > 0 else float('nan'),
                           'aprovado': bool(abs(vies) <= V_MAX_VIES and np.isfinite(razao)
                                            and 0.85 <= razao <= 1.15)})
    return pd.DataFrame(linhas)


def _eqm(te, tr, alvo, modelo, quantis):
    """Mapeamento de quantis por pixel e mês: os quantis do ERA5 no treino viram os do SMAP no treino.
    Fora da faixa do treino, desloca pela diferença da ponta (não extrapola a inclinação)."""
    saida = np.full(len(te), np.nan)
    grupos_tr = {k: g for k, g in tr.groupby(['pid', 'mes'])}
    for k, idx in te.groupby(['pid', 'mes']).groups.items():
        g = grupos_tr.get(k)
        if g is None or len(g) < 10:
            continue
        qm = np.quantile(g[modelo], quantis)
        qa = np.quantile(g[alvo], quantis)
        x = te.loc[idx, modelo].to_numpy()
        y = np.interp(x, qm, qa)
        y = np.where(x < qm[0], qa[0] + (x - qm[0]), y)
        y = np.where(x > qm[-1], qa[-1] + (x - qm[-1]), y)
        saida[te.index.get_indexer(idx)] = y
    return saida


def avaliar_umidade(df, alvo, modelo, treino, teste, quantis=None):
    """Parte S, offline. df: pid, data, <alvo> (SMAP), <modelo> (ERA5-Land cru), em m³/m³.
    Estatísticas por pixel e mês SÓ do treino; erro SÓ no teste. Devolve uma linha por candidato."""
    quantis = S_QUANTIS if quantis is None else quantis
    d = df.dropna(subset=[alvo, modelo]).copy()
    d['mes'] = d['data'].str[5:7].astype(int)
    d['am'] = d['data'].str[:7]
    tr = d[_anos(d['data'], treino)]
    te = d[_anos(d['data'], teste)]
    est = tr.groupby(['pid', 'mes']).agg(m_a=(alvo, 'mean'), s_a=(alvo, 'std'),
                                         m_m=(modelo, 'mean'), s_m=(modelo, 'std')).reset_index()
    te = te.merge(est, on=['pid', 'mes'], how='inner').reset_index(drop=True)
    if not len(te):
        return pd.DataFrame()
    x, obs = te[modelo].to_numpy(), te[alvo].to_numpy()
    teto = np.minimum(te['m_a'] + 3.0 * te['s_a'], UMIDADE_MAX_FISICA)
    cands = {
        'atual': np.minimum(x * np.minimum(te['m_a'] / np.maximum(te['m_m'], 1e-3), 5.0), teto),
        'cru': x,
        'aditivo': x + (te['m_a'] - te['m_m']),
        'variancia': te['m_a'] + (x - te['m_m']) * np.clip(te['s_a'] / np.maximum(te['s_m'], 1e-6), 0.5, 2.0),
        'eqm': _eqm(te, tr, alvo, modelo, quantis),
    }
    linhas = []
    for nome, prev in cands.items():
        prev = np.clip(np.asarray(prev, dtype=float), 0.0, UMIDADE_MAX_FISICA)
        ok = np.isfinite(prev)
        p, o = prev[ok], obs[ok]
        if not len(p):
            continue
        vies = float(np.mean(p - o))
        razao = razao_desvio_mensal(te[ok], p, o)
        linhas.append({'candidato': nome, 'n_ponto_dias': int(ok.sum()), 'vies': vies,
                       'mae_diario': float(np.mean(np.abs(p - o))),
                       'ubrmse': float(np.sqrt(np.mean(((p - p.mean()) - (o - o.mean())) ** 2))),
                       'corr_diaria': float(np.corrcoef(p, o)[0, 1]) if p.std() > 0 and o.std() > 0 else float('nan'),
                       'razao_desvio': razao,
                       'aprovado': bool(abs(vies) <= S_MAX_VIES and np.isfinite(razao)
                                        and S_FAIXA_RAZAO[0] <= razao <= S_FAIXA_RAZAO[1])})
    return pd.DataFrame(linhas)


def extremos_fora_da_faixa(mom, faixa=None):
    """Parte B: linhas (mês, classe, variável) cujo mínimo ou máximo ABSOLUTO sai da faixa declarada.
    O histograma não serve para isto: o que passa do topo cai fora dos bins e some."""
    faixa = faixa or FAIXA
    if not len(mom):
        return pd.DataFrame()
    m = mom.copy()
    m['lo'] = m['variavel'].map(lambda v: faixa.get(v, (-np.inf, np.inf))[0])
    m['hi'] = m['variavel'].map(lambda v: faixa.get(v, (-np.inf, np.inf))[1])
    fora = m[(m['maximo_absoluto'] > m['hi']) | (m['minimo_absoluto'] < m['lo'])]
    return fora[['mes', 'nome_classe', 'variavel', 'minimo_absoluto', 'maximo_absoluto', 'lo', 'hi']]


def ajustar_vazias_por_desenho(por_dia, bandas, vazias=None, coluna='rota'):
    """Parte H: nas rotas (ou versões) em que o motor deixa uma banda vazia de propósito, ela não
    conta como vazamento de máscara. por_dia: data, <coluna>, <bandas>, maximo."""
    vazias = VAZIAS_POR_DESENHO if vazias is None else vazias
    p = por_dia.copy()
    if coluna not in p:
        return p
    for rota, bs in vazias.items():
        sel = p[coluna] == rota
        for b in bs:
            if b in bandas and b in p:
                p.loc[sel, b] = p.loc[sel, 'maximo']
    return p


def datas_da_janela(d, n):
    base = datetime.strptime(d, '%Y-%m-%d')
    return [(base + timedelta(days=k)).strftime('%Y-%m-%d') for k in range(-n, n + 1)]


def meses_entre(ini, fim_exclusivo):
    """'2015-04-01', '2026-01-01' -> ['2015-04', ..., '2025-12']"""
    a, m = int(ini[:4]), int(ini[5:7])
    fa, fm = int(fim_exclusivo[:4]), int(fim_exclusivo[5:7])
    saida = []
    while (a, m) < (fa, fm):
        saida.append(f'{a}-{m:02d}')
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return saida


def dias_do_mes_calendario(am):
    a, m = int(am[:4]), int(am[5:7])
    d = datetime(a, m, 1)
    saida = []
    while d.month == m:
        saida.append(d.strftime('%Y-%m-%d'))
        d += timedelta(days=1)
    return saida


def regiao_para_pid(reg, chave):
    """Resposta do getRegion -> DataFrame com pid e data (o pixel volta pelo índice da grade)."""
    df = pd.DataFrame(reg[1:], columns=reg[0])
    if not len(df):
        return df
    ix = np.floor((df['longitude'].astype(float) - X0) / DX + 1e-6).astype(int)
    iy = np.floor((Y0 - df['latitude'].astype(float)) / DX + 1e-6).astype(int)
    df['pid'] = [chave.get((a, b)) for a, b in zip(ix, iy)]
    df['data'] = pd.to_datetime(df['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
    return df.dropna(subset=['pid'])


# =========================================================================================
def ee_e_de_verdade(ee):
    """True se o módulo `ee` importado é o Earth Engine mesmo. Dois sinais independentes:
    o pacote de verdade é um arquivo em disco (tem __file__) e o simulador se declara."""
    return getattr(ee, '__file__', None) is not None and not bool(getattr(ee, 'SIMULADO', False))


def principal():
    global PASTA, LOG
    import ee
    # TRAVA DE PROCEDÊNCIA. Um verificador que relata números sintéticos como se fossem dados é pior
    # do que um que para. Isto aconteceu em 15/11/2026: o simular_K26.py foi colado numa célula do
    # Colab, instalou um `ee` falso na sessão, e a célula seguinte com o K25 mediu o simulador — 40
    # dias, 4.000 células por classe, tudo em 0 min — sem nada avisar.
    if not ee_e_de_verdade(ee):
        if not SIMULACAO_PERMITIDA:
            raise RuntimeError(
                'O módulo `ee` desta sessão NÃO é o Earth Engine: é o simulador offline.\n'
                'Causa: o simular_K26.py foi executado nesta sessão (colado numa célula). Ele troca o\n'
                '`ee` por um falso e o falso fica na sessão inteira.\n'
                'Conserto: Ambiente de execução -> Reiniciar sessão, e cole SÓ o K26.\n'
                'Para usar o simulador, rode-o como processo separado: !python3 simular_K26.py')
        PASTA = os.path.join(os.path.dirname(PASTA) or '.', 'SIMULACAO_' + os.path.basename(PASTA))
        LOG = os.path.join(PASTA, 'LOG_K26.txt')
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    if not ee_e_de_verdade(ee):
        for _ in range(3):
            log('⚠️  SIMULAÇÃO — OS NÚMEROS ABAIXO SÃO SINTÉTICOS E NÃO DESCREVEM O SAB  ⚠️')
        log('')
    log('=' * 104)
    log(f'{VERSAO}: AUDITORIA FINAL (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log(f'   rodada {RODADA} | anos {ANO_INI}-{ANO_FIM} | partes {PARTES} | leitura {LEITURA} | alfa = {ALFA}')
    log('=' * 104)
    falta = minutos_ate_janela(AGORA)
    if falta < DURACAO_ESTIMADA_MIN:
        log(f'⛔ Não comecei: a janela do motor começa em {falta} min e a K26 pode levar {DURACAO_ESTIMADA_MIN} min. '
            f'Comece bem antes das 22h50 ou depois da 01h00.')
        return
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K26 é somente leitura: escrita bloqueada')
    for n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
              'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable',
              'startIngestion', 'cancelTask'):
        if hasattr(ee.data, n):
            setattr(ee.data, n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa.\n')

    # ---------------------------------------------------------------- infraestrutura
    # Três classes de erro, porque a reação a cada uma é diferente:
    #   TRANS  servidor ocupado        -> esperar e repetir
    #   Pesado memória / tempo / volume -> dividir o bloco e reduzir o lote
    #   Forma  pedido mal montado      -> dividir NÃO resolve; cai para outra implementação
    TRANS = ('Too many concurrent', 'Internal error', 'Service Unavailable', '503', '429', 'deadline',
             'Deadline', 'Connection', 'temporarily', 'Bad Gateway', '502', 'Quota')
    PESADO = ('memory', 'timed out', 'too many values', 'aggregation', 'too many pixels',
              'user memory limit', 'exceeded', 'output of this computation is too large',
              'request payload size')
    FORMA = ('must be a number', 'reducer input', 'no band named', 'does not contain',
             'cannot be cast', 'expected a', 'invalid argument', 'unable to cast',
             'parameter', 'array', 'dictionary', 'band names', 'must have the same',
             'not a defined', 'image.select', 'number of bands')
    ESPERAS = [30, 60, 90, 120, 180, 240]

    class Pesado(Exception):
        pass

    class Forma(Exception):
        pass

    def classificar(e):
        t = str(e).lower()
        if any(k in t for k in PESADO):
            return 'pesado'
        if any(k in t for k in FORMA):
            return 'forma'
        if any(k.lower() in t for k in TRANS):
            return 'trans'
        return 'outro'

    def gi(obj, rotulo):
        for t in range(len(ESPERAS) + 1):
            try:
                return obj.getInfo()
            except Exception as e:
                tipo = classificar(e)
                if tipo == 'pesado':
                    raise Pesado(str(e))
                if tipo == 'forma':
                    raise Forma(str(e))
                if tipo == 'trans' and t < len(ESPERAS):
                    log(f'   ↻ {rotulo}: servidor ocupado; nova tentativa em {ESPERAS[t]} s')
                    time.sleep(ESPERAS[t])
                    continue
                if tipo == 'outro' and t < 2:
                    log(f'   ↻ {rotulo}: erro não classificado ({str(e)[:70]}); repito em 30 s')
                    time.sleep(30)
                    continue
                raise

    def geom(b):
        return ee.Geometry.Rectangle(list(b), None, False)

    def por_blocos(fabrica, rotulo, blocos=None, nivel=0):
        """Chama fabrica(bloco) em cada faixa de latitude; divide a faixa se o servidor reclamar.
        Erro de FORMA sobe inteiro: dividir não conserta pedido mal montado."""
        saida = []
        for j, b in enumerate(blocos or BLOCOS):
            try:
                saida.append(gi(fabrica(b), f'{rotulo} bloco {j + 1}'))
            except Pesado as e:
                if nivel >= 3:
                    log(f'   {rotulo} bloco {j + 1}: pesado no 3º nível; desisti deste pedaço')
                    continue
                log(f'   {rotulo} bloco {j + 1}: pesado ({str(e)[:50]}), dividindo')
                saida += por_blocos(fabrica, rotulo, list(dividir(b)), nivel + 1)
        return saida

    SONDA = (-60.0, -12.0, -59.0, -11.0)        # 1 grau no meio do Brasil: barato
    _sondas = {}                                 # a forma de um pedido só é sondada UMA vez

    def sondar(fabrica, rotulo, chave):
        """Testa a FORMA do pedido num quadrado de 1 grau antes de rodar o país inteiro.
        O resultado fica em cache por `chave`: a forma de um pedido não muda de um mês para o outro,
        então sondar por mês e por variável gastaria centenas de chamadas sem necessidade."""
        if chave in _sondas:
            return _sondas[chave]
        try:
            gi(fabrica(SONDA), f'sonda {rotulo}')
            ok = True
        except Forma as e:
            log(f'   ⚠️ sonda {chave}: forma recusada pelo servidor ({str(e)[:90]})')
            ok = False
        except Pesado:
            ok = True                            # pesado na sonda é improvável; a forma está ok
        except Exception as e:
            log(f'   ⚠️ sonda {chave}: {str(e)[:90]}')
            ok = False
        _sondas[chave] = ok
        return ok

    def tentar(opcoes, rotulo):
        """Escada de implementações: devolve o resultado da primeira cuja FORMA o servidor aceita e
        que completa. opcoes: [(nome, fabrica, leitor)] ou [(nome, fabrica, leitor, chave_sonda)].
        Devolve (nome, dados) ou (None, None)."""
        for op in opcoes:
            nome, fabrica, leitor = op[0], op[1], op[2]
            chave = op[3] if len(op) > 3 else f'{rotulo}/{nome}'
            if not sondar(fabrica, f'{rotulo}/{nome}', chave):
                continue
            try:
                partes = por_blocos(fabrica, f'{rotulo}/{nome}')
                if not partes:
                    log(f'   {rotulo}: {nome} não devolveu nada; tento a próxima')
                    continue
                return nome, leitor(partes)
            except (Pesado, Forma) as e:
                log(f'   {rotulo}: {nome} falhou ({str(e)[:70]}); tento a próxima')
                continue
        log(f'   ⚠️ {rotulo}: nenhuma implementação completou')
        return None, None

    PROJ = ee.Projection(CRS, TRANSFORM)
    CLASSE = ee.Image(ASSET_MASCARA).select('classe').rename('classe')
    ELEV = ee.Image('USGS/SRTMGL1_003')
    SAB = ee.ImageCollection(ASSET_SAB)
    BR = ee.ImageCollection(BR_DWGD)

    def rr(img, reducer, b):
        return img.reduceRegion(reducer=reducer, geometry=geom(b), crs=CRS, crsTransform=TRANSFORM,
                                maxPixels=1e10, tileScale=16)

    def agrupado(reducer, n):
        return reducer.repeat(n).group(groupField=n, groupName='classe')

    def ra_fao56(d):
        data = ee.Date(d)
        lat = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180.0)
        J = ee.Number(data.getRelative('day', 'year')).add(1)
        dr = J.multiply(2.0 * math.pi / 365.0).cos().multiply(0.033).add(1.0)
        de = J.multiply(2.0 * math.pi / 365.0).subtract(1.39).sin().multiply(0.409)
        ws = lat.tan().multiply(de.tan()).multiply(-1.0).clamp(-1.0, 1.0).acos()
        return (ws.multiply(lat.sin()).multiply(de.sin())
                .add(lat.cos().multiply(de.cos()).multiply(ws.sin()))
                .multiply(dr).multiply((24.0 * 60.0 / math.pi) * 0.0820).rename('ra'))

    def rso_fao56(d):
        return ELEV.multiply(0.00002).add(0.75).multiply(ra_fao56(d)).rename('rso')

    def dia_gravado(d):
        """O dia como está no asset, sempre com os nomes de banda novos (dias antigos têm outros)."""
        img = ee.Image(SAB.filterDate(d, ee.Date(d).advance(1, 'day')).first())
        return ee.Image(ee.Algorithms.If(img.bandNames().contains('precipitation_mm'),
                                         img.select(BANDAS_ANTIGAS, BANDAS), img.select(BANDAS)))

    # ---- correção de leitura: cópia do sab_pedido.py 2026.11.03 (colecao/preparar, com_b=True) ----
    def _expandir(img):
        return img.unmask(img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMean(1, 'square', 'pixels'))

    _corr = {}

    def correcao_mes(mes):
        if mes not in _corr:
            solo = ee.Image(f'{ASSET_SOLO}/Matriz_Solo_{mes:02d}')

            def fator(p):
                f = _expandir(solo.select(p + '_m_smap')).divide(_expandir(solo.select(p + '_m_era5')).max(1e-3))
                return (ee.Image.constant(1).where(f.gt(TETO_FATOR_LEITURA).unmask(0),
                                                   ee.Image.constant(TETO_FATOR_LEITURA).divide(f)).unmask(1))

            def teto(p):
                return (_expandir(solo.select(p + '_m_smap')).add(_expandir(solo.select(p + '_s_smap')).multiply(3.0))
                        .min(0.9).unmask(0.9))
            _corr[mes] = ee.Image.cat([fator('rsup').rename('c_rsup'), fator('rsub').rename('c_rsub'),
                                       fator('ssur').rename('c_ssur'), fator('swat').rename('c_swat'),
                                       teto('ssur').rename('teto_ssur'), teto('swat').rename('teto_swat')])
        return _corr[mes]

    def brdwgd_do_dia(d):
        vazio = ee.Image.constant([-32768] * 7).rename(['pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs', 'ET'])
        br = ee.Image(BR.filterDate(d, ee.Date(d).advance(1, 'day')).merge(ee.ImageCollection([vazio])).first())
        ok = br.select('pr').gt(-32768)

        def dec(b, e, a):
            return br.select(b).updateMask(ok).multiply(e).add(a)

        def es(t):
            return t.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': t})
        tmax, tmin = dec('Tmax', 0.00106815, 15.0), dec('Tmin', 0.00106815, 15.0)
        rh = dec('RH', 0.39370079, -0.393701).clamp(0, 100)
        e = es(tmax).add(es(tmin)).divide(2)
        vpd = e.subtract(e.multiply(rh).divide(100)).max(0)
        return ee.Image.cat([
            dec('pr', 0.00686666, 225.0).max(0).rename('pr_mm'), tmax.rename('tmax_C'), tmin.rename('tmin_C'),
            rh.rename('RH'), dec('ET', 0.05118110, -0.0511811).rename('et_potencial'),
            dec('Rs', 0.15708661, -0.057087).rename('rs'), dec('u2', 0.05905512, -0.059055).rename('u2'),
            vpd.rename('vpd')]).toFloat()

    def entregue(img, d):
        alg = ee.String(ee.Algorithms.If(img.propertyNames().contains('versao_algoritmo'),
                                         img.get('versao_algoritmo'), 'V1.0'))
        c = correcao_mes(int(d[5:7]))
        corrigidas = ee.Image.cat([
            img.select('runoff_sup_mm').multiply(c.select('c_rsup')).rename('runoff_sup_mm'),
            img.select('runoff_sub_mm').multiply(c.select('c_rsub')).rename('runoff_sub_mm'),
            img.select('soil_moisture_0_5cm_m3_m3').multiply(c.select('c_ssur')).min(c.select('teto_ssur'))
              .rename('soil_moisture_0_5cm_m3_m3'),
            img.select('soil_moisture_0_100cm_m3_m3').multiply(c.select('c_swat')).min(c.select('teto_swat'))
              .rename('soil_moisture_0_100cm_m3_m3')]).toFloat()
        im = ee.Image(ee.Algorithms.If(alg.equals('V1.0'), img.addBands(corrigidas, None, True), img))
        if d < FIM_HISTORICO_CORRECAO:                 # corrigirPixelsB: só 1961-2025 (decidido no cliente)
            classe = CLASSE.unmask(0, False)
            br = brdwgd_do_dia(d)
            usar_b = classe.eq(2).And(br.select('pr_mm').mask().unmask(0))
            nucleo = [im.select(b).where(usar_b, br.select(b)).rename(b) for b in NUCLEO_B]
            rso = ra_fao56(d).multiply(ELEV.unmask(0).multiply(2e-5).add(0.75)).rename('rso')
            rs = ee.Image(nucleo[5])
            nucleo[5] = rs.where(classe.eq(3).And(rs.gt(rso)), rso).rename('rs')
            im = im.addBands(ee.Image.cat(nucleo).toFloat(), None, True)
        etp = im.select('et_potencial')
        etr = im.select('et_real').min(etp).rename('et_real')
        tr = im.select('transpiracao_mm').min(etr).rename('transpiracao_mm')
        return ee.Image(im.addBands(ee.Image.cat([etr, tr]), None, True).select(BANDAS).copyProperties(img))

    _dias = {}

    def dia(d):
        if d not in _dias:
            g = dia_gravado(d)
            _dias[d] = entregue(g, d) if LEITURA == 'entregue' else g
        return _dias[d]

    def sortear_pontos(n, semente, rotulo):
        sorteio = (ee.Image.pixelLonLat().addBands(CLASSE)
                   .stratifiedSample(numPoints=0, classBand='classe', region=geom((-75.0, -35.0, -28.0, 6.5)),
                                     projection=PROJ, seed=semente, classValues=[1],
                                     classPoints=[n], geometries=True, tileScale=16))
        pts = [{'pid': k, 'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1]}
               for k, f in enumerate(gi(sorteio, rotulo)['features'])]
        chave = {(int(math.floor((p['lon'] - X0) / DX + 1e-6)),
                  int(math.floor((Y0 - p['lat']) / DX + 1e-6))): p['pid'] for p in pts}
        return pts, chave, ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in pts])

    def media_ou_vazio(col, nomes):
        """A média do dia (as 8 saídas de 3 h do SMAP; a imagem única do ERA5 e do BR-DWGD), ou bandas
        mascaradas se a coleção vier vazia (dia sem SMAP). Sem isto, .mean() de coleção vazia não tem
        bandas e o cat cai. A imagem vazia é mascarada, então não entra na média quando há dado."""
        vazio = ee.Image.constant([0] * len(nomes)).rename(nomes).toFloat().updateMask(0)
        # toFloat em cada imagem: o servidor exige o mesmo tipo de banda na coleção, e o BR-DWGD
        # decodificado tem tipo com faixa (Float<-0,059; 15>) — foi o erro da rodada 3 de 16/11, 05h07
        return (col.select(nomes).map(lambda i: ee.Image(i).toFloat())
                .merge(ee.ImageCollection([vazio])).mean().rename(nomes))

    def ler_pontos_mes(am, fabrica_dia, regiao, chave, rotulo):
        """Uma coleção de um mês (uma imagem por dia) lida nos pontos por getRegion. Se o servidor
        reclamar do tamanho, lê o mês em duas metades."""
        dd = dias_do_mes_calendario(am)
        for partes in (1, 2, 4):
            try:
                saida = []
                for lote in lotes(dd, int(math.ceil(len(dd) / partes))):
                    col = ee.ImageCollection([fabrica_dia(d).set('system:time_start', ee.Date(d).millis())
                                              for d in lote])
                    saida.append(regiao_para_pid(gi(col.getRegion(regiao, None, CRS, TRANSFORM),
                                                    f'{rotulo} {lote[0]}'), chave))
                return pd.concat(saida, ignore_index=True)
            except Pesado:
                log(f'   {rotulo} {am}: pesado; leio em {partes * 2} pedaços')
        raise Pesado(f'{rotulo} {am}: pesado mesmo em 4 pedaços')

    # decodificação do BR-DWGD (escala e offset por variável, como nas auditorias anteriores)
    # Escala e deslocamento de cada variável do BR-DWGD.
    # O deslocamento da Tmin era 5,0 na v2 e v3 e estava ERRADO em exatamente 10 graus. A prova veio
    # da parte F da corrida de 12h55: o viés da Tmin contra o BR-DWGD deu +10,364 na rota ERA5 e
    # +10,603 na GFS, contra +0,540 e +0,696 da Tmax. Tirando os 10, a Tmin fica em +0,364 e +0,603,
    # da mesma ordem da Tmax — que é o que se espera de duas variáveis corrigidas pelo mesmo caminho.
    # Com 5,0 a parte E acusava 97% dos pixel-dias acima do recorde, que era defeito inventado.
    # Confirme contra as propriedades do asset antes de publicar qualquer número que dependa disto.
    DECODE_BR = {'Tmax': (0.00106815, 15.0), 'Tmin': (0.00106815, 15.0), 'pr': (0.00686666, 225.0),
                 'RH': (0.39370079, -0.393701), 'u2': (0.05905512, -0.059055), 'Rs': (0.15708661, -0.057087)}
    DECODE_CONFERIDO = {'Tmax': True, 'pr': True, 'RH': True, 'u2': True, 'Rs': True, 'Tmin': True}

    def br_var(img, v):
        esc, off = DECODE_BR[v]
        m = img.select('pr').gt(-32768).And(img.select('Tmax').gt(-32768))
        return img.select(v).updateMask(m).multiply(esc).add(off).rename(v)

    _rec = {}

    def recorde(v, mes):
        if (v, mes) not in _rec:
            _rec[(v, mes)] = (BR.filter(ee.Filter.calendarRange(*ANOS_RECORDE, 'year'))
                              .filter(ee.Filter.calendarRange(mes, mes, 'month'))
                              .map(lambda i: br_var(i, v)).max().rename('rec'))
        return _rec[(v, mes)]

    # ---------------------------------------------------------------- R escoamento x SMAP
    if 'R' in PARTES:
        try:
            log(f'\n[R] escoamento: {len(CANDIDATOS_R)} fatores contra o SMAP L4, treino {R_ANOS_TREINO}, '
                f'teste {R_ANOS_TESTE}, {N_PONTOS_R} pontos de classe A')
            pts, chave, regiao = sortear_pontos(N_PONTOS_R, SEMENTE + 1, 'pontos da parte R')
            gravar(pd.DataFrame(pts), 'K26_R_pontos_sorteados.csv')
            NOMES_SMAP = ['overland_runoff_flux', 'baseflow_flux']
            NOMES_ERA = ['surface_runoff_sum', 'sub_surface_runoff_sum', 'total_precipitation_sum']

            def dia_R(d):
                fim = ee.Date(d).advance(1, 'day')
                smap = (media_ou_vazio(ee.ImageCollection(SMAP_L4).filterDate(d, fim), NOMES_SMAP)
                        .multiply(86400).rename(['smap_rsup', 'smap_rsub']))           # kg/m²/s -> mm/dia
                era = (media_ou_vazio(ee.ImageCollection(ERA5_DIA).filterDate(d, fim), NOMES_ERA)
                       .multiply(1000).max(0).rename(['era_rsup', 'era_rsub', 'era_pr']))
                return smap.addBands(era).addBands(dia_gravado(d).select(['pr_mm'], ['sab_pr'])).toFloat()

            feito = ler_acumulado('K26_R_serie.csv')
            meses = meses_entre(R_INICIO, R_FIM)
            pendentes = meses_a_fazer(meses, feito['data'].str[:7].unique() if len(feito) else [])
            log(f'   meses a ler: {len(pendentes)} de {len(meses)}')
            for am in pendentes:
                df = ler_pontos_mes(am, dia_R, regiao, chave, 'R')
                cols = ['pid', 'data', 'smap_rsup', 'smap_rsub', 'era_rsup', 'era_rsub', 'era_pr', 'sab_pr']
                df = df[[c for c in cols if c in df.columns]]
                for c in cols[2:]:
                    if c in df:
                        df[c] = pd.to_numeric(df[c], errors='coerce')
                acrescentar(df, 'K26_R_serie.csv')
                log(f'   R: {am} lido ({len(df)} ponto-dias)')
            serie = ler_acumulado('K26_R_serie.csv')
            serie['pid'] = serie['pid'].astype(int)
            tabelas, escolhas = [], {}
            for var, alvo, modelo, pr in (('runoff_sup_mm', 'smap_rsup', 'era_rsup', 'era_pr'),
                                          ('runoff_sub_mm', 'smap_rsub', 'era_rsub', None)):
                t = avaliar_fatores(serie, alvo, modelo, CANDIDATOS_R, R_ANOS_TREINO, R_ANOS_TESTE, pr=pr)
                if pr is not None and len(t):
                    # o mesmo número para o SAB: chuva do SAB (BR-DWGD 12-12 UTC no histórico), só informação
                    t2 = avaliar_fatores(serie, alvo, modelo, CANDIDATOS_R, R_ANOS_TREINO, R_ANOS_TESTE, pr='sab_pr')
                    t['i_pct_acima_chuva_sab'] = t2['pct_acima_chuva'].values
                t, esc = escolher_fator(t, com_chuva=pr is not None)
                t.insert(0, 'variavel', var)
                tabelas.append(t)
                escolhas[var] = esc
            R = pd.concat(tabelas, ignore_index=True)
            if not len(R) or 'candidato' not in R:
                raise RuntimeError('sem ponto-dias nos anos de teste: confira R_INICIO/R_FIM e o checkpoint')
            gravar(R.round(5), 'K26_R_fatores.csv')
            log('\n' + R[['variavel', 'candidato', 'vies_total_pct', 'mae_diario', 'mae_mensal', 'razao_p99',
                          'max_prev', 'max_ref'] + [c for c in ('pct_acima_chuva', 'pct_acima_chuva_10mm')
                                                    if c in R] + ['aprovado']].round(4).to_string(index=False))
            atual = R[R['candidato'] == 'atual_teto5'].set_index('variavel')
            txt = []
            for var, esc in escolhas.items():
                a = atual.loc[var] if var in atual.index else None
                base = (f'{var}: hoje viés {a["vies_total_pct"]:+.1f}%, p99 x{a["razao_p99"]:.2f}, '
                        f'máx {a["max_prev"]:.0f} mm (SMAP {a["max_ref"]:.0f})') if a is not None else var
                txt.append(base + (f' -> melhor aprovado: {esc}' if esc else ' -> NENHUM candidato aprovado'))
            resultado('R', 'ATENCAO' if any(e != 'atual_teto5' for e in escolhas.values()) else 'OK',
                      'escoamento: fator SMAP/ERA5 fora da amostra', ' | '.join(txt))
        except Exception as _e:
            falhou_parte('R', _e)

    # ---------------------------------------------------------------- V vento x BR-DWGD
    if 'V' in PARTES:
        try:
            log(f'\n[V] vento: média x variância, componentes diárias x velocidade horária, treino '
                f'{V_ANOS_TREINO}, teste {V_ANOS_TESTE}, {N_PONTOS_V} pontos de classe A')
            pts, chave, regiao = sortear_pontos(N_PONTOS_V, SEMENTE, 'pontos da parte V')
            gravar(pd.DataFrame(pts), 'K26_V_pontos_sorteados.csv')

            def velocidade(img):
                return (img.select('u_component_of_wind_10m').hypot(img.select('v_component_of_wind_10m'))
                        .rename('w'))

            def dia_V(d):
                fim = ee.Date(d).advance(1, 'day')
                br = media_ou_vazio(BR.filterDate(d, fim).map(lambda i: br_var(i, 'u2')), ['u2']).rename('br_u2')
                comp = media_ou_vazio(ee.ImageCollection(ERA5_DIA).filterDate(d, fim),
                                      ['u_component_of_wind_10m', 'v_component_of_wind_10m'])
                era_dia = velocidade(comp).multiply(CONV_U10_U2).resample('bilinear').rename('era_dia')
                era_hora = (media_ou_vazio(ee.ImageCollection(ERA5_HORA).filterDate(d, fim).map(velocidade), ['w'])
                            .multiply(CONV_U10_U2).resample('bilinear').rename('era_hora'))
                return br.addBands(era_dia).addBands(era_hora).toFloat()

            feito = ler_acumulado('K26_V_serie.csv')
            meses = meses_entre(f'{V_ANOS_TREINO[0]}-01-01', f'{V_ANOS_TESTE[1] + 1}-01-01')
            pendentes = meses_a_fazer(meses, feito['data'].str[:7].unique() if len(feito) else [])
            log(f'   meses a ler: {len(pendentes)} de {len(meses)}')
            for am in pendentes:
                df = ler_pontos_mes(am, dia_V, regiao, chave, 'V')
                cols = ['pid', 'data', 'br_u2', 'era_dia', 'era_hora']
                df = df[[c for c in cols if c in df.columns]]
                for c in cols[2:]:
                    if c in df:
                        df[c] = pd.to_numeric(df[c], errors='coerce')
                acrescentar(df, 'K26_V_serie.csv')
                log(f'   V: {am} lido ({len(df)} ponto-dias)')
            serie = ler_acumulado('K26_V_serie.csv')
            serie['pid'] = serie['pid'].astype(int)
            V = avaliar_vento(serie, V_ANOS_TREINO, V_ANOS_TESTE)
            if not len(V):
                raise RuntimeError('sem ponto-dias nos anos de teste: confira V_ANOS_* e o checkpoint')
            gravar(V.round(5), 'K26_V_vento.csv')
            log('\n' + V.round(4).to_string(index=False))
            atual = V[(V['fonte'] == 'era_dia') & (V['metodo'] == 'media')]
            aprov = V[V['aprovado'] & (V['metodo'] != 'cru')].sort_values('mae_m_s')
            a = atual.iloc[0] if len(atual) else None
            resultado('V', 'OK' if a is not None and bool(a['aprovado']) else 'ATENCAO',
                      'vento: correção dos dias ERA5 fora da amostra',
                      (f'hoje (componentes diárias, média): viés {a["vies_m_s"]:+.3f} m/s, erro {a["erro_rel_pct"]:.1f}%, '
                       f'razão dos desvios {a["razao_desvio"]:.2f}' if a is not None else 'atual não medido')
                      + (f' | melhor aprovado: {aprov.iloc[0]["fonte"]}/{aprov.iloc[0]["metodo"]} '
                         f'(viés {aprov.iloc[0]["vies_m_s"]:+.3f}, erro {aprov.iloc[0]["erro_rel_pct"]:.1f}%, '
                         f'razão {aprov.iloc[0]["razao_desvio"]:.2f})' if len(aprov)
                         else ' | nenhum candidato passa viés <= 0,10 m/s e razão em [0,85; 1,15]'))
        except Exception as _e:
            falhou_parte('V', _e)

    # ---------------------------------------------------------------- S umidade do solo x SMAP
    if 'S' in PARTES:
        try:
            log(f'\n[S] umidade do solo: 5 correções contra o SMAP L4, treino {R_ANOS_TREINO}, '
                f'teste {R_ANOS_TESTE}, {N_PONTOS_R} pontos de classe A (os mesmos da parte R)')
            pts, chave, regiao = sortear_pontos(N_PONTOS_R, SEMENTE + 1, 'pontos da parte S')
            NOMES_SM = ['sm_surface', 'sm_rootzone']
            NOMES_L = ['volumetric_soil_water_layer_1', 'volumetric_soil_water_layer_2',
                       'volumetric_soil_water_layer_3']

            def dia_S(d):
                fim = ee.Date(d).advance(1, 'day')
                smap = (media_ou_vazio(ee.ImageCollection(SMAP_L4).filterDate(d, fim), NOMES_SM)
                        .rename(['smap_ssur', 'smap_swat']))
                era = media_ou_vazio(ee.ImageCollection(ERA5_DIA).filterDate(d, fim), NOMES_L)
                ssur = era.select(NOMES_L[0]).resample('bilinear').rename('era_ssur')     # SOLO_BILINEAR do motor
                swat = (era.expression('(l1*7 + l2*21 + l3*72) / 100', {
                    'l1': era.select(NOMES_L[0]), 'l2': era.select(NOMES_L[1]), 'l3': era.select(NOMES_L[2])})
                        .resample('bilinear').rename('era_swat'))
                return smap.addBands(ssur).addBands(swat).toFloat()

            feito = ler_acumulado('K26_S_serie.csv')
            meses = meses_entre(R_INICIO, R_FIM)
            pendentes = meses_a_fazer(meses, feito['data'].str[:7].unique() if len(feito) else [])
            log(f'   meses a ler: {len(pendentes)} de {len(meses)}')
            for am in pendentes:
                df = ler_pontos_mes(am, dia_S, regiao, chave, 'S')
                cols = ['pid', 'data', 'smap_ssur', 'smap_swat', 'era_ssur', 'era_swat']
                df = df[[c for c in cols if c in df.columns]]
                for c in cols[2:]:
                    if c in df:
                        df[c] = pd.to_numeric(df[c], errors='coerce')
                acrescentar(df, 'K26_S_serie.csv')
                log(f'   S: {am} lido ({len(df)} ponto-dias)')
            serie = ler_acumulado('K26_S_serie.csv')
            serie['pid'] = serie['pid'].astype(int)
            tabelas, txt = [], []
            for var, alvo, modelo in (('soil_moisture_0_5cm_m3_m3', 'smap_ssur', 'era_ssur'),
                                      ('soil_moisture_0_100cm_m3_m3', 'smap_swat', 'era_swat')):
                t = avaliar_umidade(serie, alvo, modelo, R_ANOS_TREINO, R_ANOS_TESTE)
                if not len(t):
                    continue
                t.insert(0, 'variavel', var)
                tabelas.append(t)
                a = t.set_index('candidato').loc['atual'] if 'atual' in set(t['candidato']) else None
                aprov = t[t['aprovado']].sort_values('mae_diario')
                txt.append(f'{var}: hoje viés {a["vies"]:+.3f}, erro {a["mae_diario"]:.3f} m³/m³, razão {a["razao_desvio"]:.2f}'
                           + (f' -> melhor aprovado: {aprov.iloc[0]["candidato"]} (erro {aprov.iloc[0]["mae_diario"]:.3f})'
                              if len(aprov) else ' -> NENHUM candidato aprovado'))
            if not tabelas:
                raise RuntimeError('sem ponto-dias nos anos de teste: confira R_INICIO/R_FIM e o checkpoint')
            S = pd.concat(tabelas, ignore_index=True)
            gravar(S.round(5), 'K26_S_umidade.csv')
            log('\n' + S.round(4).to_string(index=False))
            muda = any('melhor aprovado: atual' not in x for x in txt)
            resultado('S', 'ATENCAO' if muda else 'OK', 'umidade do solo: correção fora da amostra', ' | '.join(txt))
        except Exception as _e:
            falhou_parte('S', _e)

    # ---------------------------------------------------------------- P pixels da ETo e do Rs
    if 'P' in PARTES:
        try:
            log('\n[P] pixels com ETo divergente ou Rs acima do céu claro: entradas, elevação e ETo refeita')

            def variantes(d):
                img = dia_gravado(d)
                return (img.select(['et_potencial', 'rs', 'u2', 'RH', 'tmax_C', 'tmin_C', 'vpd', 'pr_mm'])
                        .addBands(eto_ee(img, d).rename('eto_srtm'))
                        .addBands(eto_ee(img, d, ELEV.unmask(0)).rename('eto_srtm_0'))
                        .addBands(ELEV.rename('elev')).addBands(ELEV.mask().rename('elev_tem_valor'))
                        .addBands(rso_fao56(d)).addBands(ra_fao56(d)).addBands(CLASSE).toFloat())

            achados = []
            for d in P_DATAS:
                v = variantes(d)
                ruim = (v.select('et_potencial').subtract(v.select('eto_srtm')).abs().gt(P_TOL_ETO)
                        .Or(v.select('rs').gt(v.select('rso').multiply(1.0 + TOL_RSO_MOTOR)))
                        .Or(v.select('eto_srtm').mask().Not().And(v.select('et_potencial').mask())))
                for b in BLOCOS:
                    try:
                        fs = gi(ee.Image.pixelLonLat().updateMask(ruim.unmask(0))
                                .sample(region=geom(b), projection=PROJ, factor=1, seed=SEMENTE,
                                        geometries=True, dropNulls=True, tileScale=16).limit(P_MAX_PIXELS),
                                f'P pixels {d}')['features']
                    except Pesado:
                        continue
                    achados += [(d, f['geometry']['coordinates'][0], f['geometry']['coordinates'][1]) for f in fs]
            log(f'   {len(achados)} pixel-data(s) achados nas {len(P_DATAS)} datas')
            if achados:
                linhas = []
                for d in P_DATAS:
                    coords = sorted({(round(x, 5), round(y, 5)) for dd_, x, y in achados if dd_ == d})[:P_MAX_PIXELS]
                    if not coords:
                        continue
                    ch = {(int(math.floor((x - X0) / DX + 1e-6)), int(math.floor((Y0 - y) / DX + 1e-6))): k
                          for k, (x, y) in enumerate(coords)}
                    reg = gi(ee.ImageCollection([variantes(j).set('system:time_start', ee.Date(j).millis())
                                                 for j in datas_da_janela(d, P_JANELA_DIAS)])
                             .getRegion(ee.Geometry.MultiPoint([list(c) for c in coords]), None, CRS, TRANSFORM),
                             f'P série {d}')
                    df = regiao_para_pid(reg, ch)
                    df['data_alvo'] = d
                    linhas.append(df)
                P = pd.concat(linhas, ignore_index=True)
                for c in ('et_potencial', 'eto_srtm', 'eto_srtm_0', 'rs', 'rso'):
                    P[c] = pd.to_numeric(P[c], errors='coerce')
                P['dif_srtm'] = P['et_potencial'] - P['eto_srtm']
                P['dif_srtm_0'] = P['et_potencial'] - P['eto_srtm_0']
                P['rs_sobre_rso'] = P['rs'] / P['rso']
                gravar(P.drop(columns=['id'], errors='ignore').round(5), 'K26_P_pixels.csv')
                div = P[P['dif_srtm'].abs() > P_TOL_ETO]
                explica_0 = int((div['dif_srtm_0'].abs() <= TOL_ETO).sum())
                resultado('P', 'INFO', 'pixels da ETo divergente e do Rs acima do céu claro',
                          f'{P["pid"].nunique()} pixel(s) por data, {len(div)} pixel-dias divergentes > {P_TOL_ETO} mm '
                          f'na janela de ±{P_JANELA_DIAS} dias; destes, {explica_0} batem com a ETo refeita com a '
                          f'elevação sem máscara (SRTM vazio = 0 m). Série dia a dia em K26_P_pixels.csv.')
            else:
                resultado('P', 'INFO', 'pixels da ETo divergente e do Rs acima do céu claro',
                          'nenhum pixel com divergência nas datas pedidas')
        except Exception as _e:
            falhou_parte('P', _e)

    # ---------------------------------------------------------------- Q ERA5 cru nos pixels do Rs = 0
    if 'Q' in PARTES:
        try:
            log('\n[Q] ERA5-Land CRU nos pixels em que a rodada 1 achou Rs gravado = 0')
            NOMES_Q = ['surface_solar_radiation_downwards_sum', 'u_component_of_wind_10m',
                       'v_component_of_wind_10m', 'temperature_2m', 'dewpoint_temperature_2m',
                       'total_precipitation_sum']

            def dia_Q(d):
                era = media_ou_vazio(ee.ImageCollection(ERA5_DIA).filterDate(d, ee.Date(d).advance(1, 'day')),
                                     NOMES_Q)
                return (era.addBands(era.select([NOMES_Q[0]], ['ssrd_bilinear']).resample('bilinear'))
                        .addBands(dia_gravado(d).select(['rs', 'et_potencial', 'u2', 'RH', 'tmax_C', 'tmin_C'],
                                                        ['sab_rs', 'sab_eto', 'sab_u2', 'sab_RH', 'sab_tmax', 'sab_tmin']))
                        .addBands(CLASSE).toFloat())

            ch = {(int(math.floor((x - X0) / DX + 1e-6)), int(math.floor((Y0 - y) / DX + 1e-6))): k
                  for k, (x, y) in enumerate(Q_PIXELS)}
            regiao = ee.Geometry.MultiPoint([list(c) for c in Q_PIXELS])
            linhas = []
            for d0, d1 in Q_JANELAS:
                datas = pd.date_range(d0, d1).strftime('%Y-%m-%d').tolist()
                col = ee.ImageCollection([dia_Q(d).set('system:time_start', ee.Date(d).millis()) for d in datas])
                linhas.append(regiao_para_pid(gi(col.getRegion(regiao, None, CRS, TRANSFORM), f'Q {d0}'), ch))
            Q = pd.concat(linhas, ignore_index=True).drop(columns=['id'], errors='ignore')
            for c in Q.columns:
                if c not in ('data', 'pid'):
                    Q[c] = pd.to_numeric(Q[c], errors='coerce')
            Q['ssrd_MJ'] = Q['surface_solar_radiation_downwards_sum'] / 1e6
            Q['ssrd_bilinear_MJ'] = Q['ssrd_bilinear'] / 1e6
            gravar(Q.round(5), 'K26_Q_era5_cru.csv')
            zeros = Q[Q['sab_rs'] <= 0]
            log(Q[['data', 'pid', 'classe', 'ssrd_MJ', 'ssrd_bilinear_MJ', 'sab_rs', 'sab_eto']].round(3)
                .to_string(index=False))
            sem = int(zeros['ssrd_MJ'].isna().sum())
            zero_cru = int((zeros['ssrd_MJ'] <= 0).sum())
            resultado('Q', 'INFO', 'ERA5-Land cru nos pixels do Rs = 0',
                      f'{len(zeros)} pixel-dias com Rs gravado = 0 nos {len(Q_PIXELS)} pixels; no ERA5-Land cru de hoje: '
                      f'{sem} sem valor (máscara), {zero_cru} com radiação 0, '
                      f'{len(zeros) - sem - zero_cru} com radiação > 0 (o ERA5 foi revisto depois da gravação ou o '
                      f'motor perdeu o valor). Detalhe em K26_Q_era5_cru.csv.')
        except Exception as _e:
            falhou_parte('Q', _e)

    # ---------------------------------------------------------------- A inventário
    PRECISAM_INVENTARIO = set('BCDEFGH')
    inventario = ler_acumulado('K26_A_inventario.csv')
    if 'A' in PARTES or (not len(inventario) and PRECISAM_INVENTARIO & set(PARTES)):
        try:
            log('[A] inventário, proveniência e contagem por classe')
            col = SAB.filterDate(f'{ANO_INI}-01-01', f'{ANO_FIM + 1}-01-01')
            campos = ['system:time_start', 'versao', 'versao_algoritmo', 'Faixa_Prazo_GFS',
                      'metodo_ur_vento_era5', 'rs_limitado_rso', 'teto_chuva_fator']
            try:
                bruto = gi(col.map(lambda i: ee.Feature(None, ee.Dictionary.fromLists(
                    campos, [ee.Algorithms.If(ee.Image(i).propertyNames().contains(c), ee.Image(i).get(c), '')
                             for c in campos]))), 'inventário')['features']
                linhas = [f['properties'] for f in bruto]
            except Pesado:
                linhas = []
                for a in range(ANO_INI, ANO_FIM + 1):
                    sub = SAB.filterDate(f'{a}-01-01', f'{a + 1}-01-01')
                    bruto = gi(sub.map(lambda i: ee.Feature(None, ee.Dictionary.fromLists(
                        campos, [ee.Algorithms.If(ee.Image(i).propertyNames().contains(c), ee.Image(i).get(c), '')
                                 for c in campos]))), f'inventário {a}')['features']
                    linhas += [f['properties'] for f in bruto]
            inventario = pd.DataFrame(linhas)
            if 'system:time_start' not in inventario.columns:
                raise RuntimeError('o servidor não devolveu system:time_start; colunas: '
                                   f'{list(inventario.columns)}')
            def _data(t):
                try:
                    return datetime.fromtimestamp(int(t) / 1000, timezone.utc).strftime('%Y-%m-%d')
                except Exception:
                    return None
            inventario['data'] = [_data(t) for t in inventario['system:time_start']]
            inventario = inventario.dropna(subset=['data'])
            for c in ('versao', 'versao_algoritmo', 'Faixa_Prazo_GFS', 'metodo_ur_vento_era5'):
                if c not in inventario.columns:
                    inventario[c] = None
            inventario['versao'] = inventario['versao'].replace('', None)
            for c in ('versao_algoritmo', 'metodo_ur_vento_era5'):        # [v1.9] '' = propriedade ausente
                inventario[c] = inventario[c].replace('', None)
            inventario['rota'] = inventario['versao'].map(classificar_rota)
            inventario = inventario.drop(columns=['system:time_start']).sort_values('data').reset_index(drop=True)
            gravar(inventario, 'K26_A_inventario.csv')
            dias_rota_pre = dict(zip(inventario['data'], inventario['rota']))
            esperado = pd.date_range(inventario['data'].min(), inventario['data'].max())
            buracos = sorted(set(esperado.strftime('%Y-%m-%d')) - set(inventario['data']))
            dups = inventario['data'].duplicated().sum()
            resultado('A1', 'OK' if not buracos and not dups else 'FALHA', 'dias gravados, sem buraco e sem repetição',
                      f'{len(inventario)} dias de {inventario["data"].min()} a {inventario["data"].max()}; '
                      f'esperados {len(esperado)}; buracos {len(buracos)}'
                      + (f' (ex.: {buracos[:5]})' if buracos else '') + f'; datas repetidas {int(dups)}')
            resultado('A2', 'INFO', 'proveniência e versão do algoritmo',
                      ' | '.join(f'{r} {n}' for r, n in inventario['rota'].value_counts().items())
                      + ' || versões: ' + ', '.join(f'{k}={v}' for k, v in
                                                    inventario['versao_algoritmo'].fillna('V1.0 (sem propriedade)').value_counts().items())
                      + ' || métodos: ' + ', '.join(sorted(set(inventario['metodo_ur_vento_era5'].dropna().astype(str))) or ['nenhum']))

            # contagem por classe: a conta que resolve o total de células sobre terra
            cont = somar_grupos([ler_grupos(p, ['n'], 'sum') for p in por_blocos(
                lambda b: rr(ee.Image.constant(1).rename('n').addBands(CLASSE).updateMask(CLASSE.mask()),
                             agrupado(ee.Reducer.sum(), 1), b), 'classes')], ['n'])
            tab = pd.DataFrame([{'classe': k, 'nome': CLASSES.get(k, f'?{k}'), 'celulas': int(round(v['n']))}
                                for k, v in sorted(cont.items())])
            tab.loc[len(tab)] = {'classe': 0, 'nome': 'TOTAL', 'celulas': int(tab['celulas'].sum())}
            gravar(tab, 'K26_A_classes.csv')
            log(tab.to_string(index=False))
            # A contagem pela máscara de UM dia do SAB NÃO é a mesma coisa que a contagem da máscara de
            # qualidade, e na primeira corrida as duas discordaram em 1.247 células. Então aqui elas são
            # CONFRONTADAS, em vários dias, em vez de uma ser apresentada como a resposta.
            n_mascara = int(tab.loc[tab.classe == 0, 'celulas'].iloc[0])
            datas_ord = sorted(inventario['data'])
            amostra_dias = []
            for cand in (datas_ord[0], datas_ord[len(datas_ord) // 2], datas_ord[-1]):
                if cand not in amostra_dias:
                    amostra_dias.append(cand)
            linhas_sab = []
            for d in amostra_dias:
                m_sab = dia_gravado(d).select('pr_mm').mask()
                # (i) total de células com valor, SEM cruzar com a máscara de qualidade
                tot = sum(float((p or {}).get('n') or 0) for p in por_blocos(
                    lambda b: rr(ee.Image.constant(1).rename('n').updateMask(m_sab), ee.Reducer.sum(), b),
                    f'total com valor {d}'))
                # (ii) o mesmo, agrupado por classe (quem tem valor E tem classe)
                cont2 = somar_grupos([ler_grupos(p, ['n'], 'sum') for p in por_blocos(
                    lambda b: rr(ee.Image.constant(1).rename('n').updateMask(m_sab).addBands(CLASSE),
                                 agrupado(ee.Reducer.sum(), 1), b), f'classes com valor {d}')], ['n'])
                linha = {'data': d, 'rota': dias_rota_pre.get(d), 'com_valor_total': int(round(tot))}
                for k in (1, 2, 3, 4):
                    linha[CLASSES[k]] = int(round((cont2.get(k) or {}).get('n') or 0))
                linha['com_valor_e_classe'] = sum(linha[CLASSES[k]] for k in (1, 2, 3, 4))
                linha['com_valor_sem_classe'] = linha['com_valor_total'] - linha['com_valor_e_classe']
                linha['classe_sem_valor'] = n_mascara - linha['com_valor_e_classe']
                linhas_sab.append(linha)
                log(f'   {d}: {linha["com_valor_total"]:,} com valor; {linha["com_valor_e_classe"]:,} '
                    f'também com classe; {linha["com_valor_sem_classe"]:,} com valor e sem classe; '
                    f'{linha["classe_sem_valor"]:,} com classe e sem valor')
            tab2 = pd.DataFrame(linhas_sab)
            gravar(tab2, 'K26_A_classes_no_SAB.csv')
            log('\nconfronto das contagens:')
            log(tab2.to_string(index=False))
            pior = int(tab2['classe_sem_valor'].abs().max())
            concorda = pior == 0
            resultado('A3', 'INFO' if concorda else 'ATENCAO', 'contagem por classe e confronto com a máscara do dia',
                      f'MÁSCARA DE QUALIDADE (é esta que vai ao artigo): '
                      + ' | '.join(f'{r.nome} {r.celulas:,}' for r in tab.itertuples() if r.classe)
                      + f' || total {n_mascara:,}. '
                      + (f'A máscara de qualidade e as células com valor coincidem nos {len(amostra_dias)} dias '
                         f'conferidos.' if concorda else
                         f'DISCORDÂNCIA: em {amostra_dias[0]}..{amostra_dias[-1]} há até {pior:,} células '
                         f'classificadas sem valor no dia (e até '
                         f'{int(tab2["com_valor_sem_classe"].abs().max()):,} com valor e sem classe). '
                         f'As duas contagens medem coisas diferentes: a máscara é estática e o dia é um dia. '
                         f'Para o artigo use a máscara ({n_mascara:,}); cite o número do dia só se disser qual dia.'))
        except Exception as _e:
            falhou_parte('A', _e)

    # A parte A pode ter falhado. Sem um inventário com a coluna 'data' nenhuma outra parte tem o que
    # varrer, então aqui a corrida termina com relatório em vez de estourar na primeira indexação.
    if not PRECISAM_INVENTARIO & set(PARTES):
        return fechar(T0)
    if not isinstance(inventario, pd.DataFrame) or inventario.empty or 'data' not in inventario.columns:
        resultado('A', 'FALHA', 'inventário indisponível',
                  'sem a lista de dias gravados não há o que varrer. Causas prováveis: ANO_INI/ANO_FIM '
                  'fora do que existe no asset, ou a parte A falhou (veja o item A acima). As partes '
                  'B a H precisam do inventário e foram puladas.')
        return fechar(T0)
    for _c in ('versao', 'rota', 'Faixa_Prazo_GFS'):
        if _c not in inventario.columns:
            inventario[_c] = None
    if inventario['rota'].isna().all():
        inventario['rota'] = inventario['versao'].map(classificar_rota)
    inventario['mes'] = inventario['data'].astype(str).str[:7]
    dias_rota = dict(zip(inventario['data'], inventario['rota']))
    dias_versao = dict(zip(inventario['data'], inventario['versao']))
    dias_faixa = dict(zip(inventario['data'], inventario.get('Faixa_Prazo_GFS', pd.Series(dtype=object))))
    todos_meses = sorted(inventario['mes'].unique())

    def dias_do_mes(m):
        return sorted(inventario.loc[inventario['mes'] == m, 'data'])

    # ---- [v1.6] MODO RÁPIDO para o histórico ------------------------------------------------
    # A rodada 5 (1961-1970, 17/11 02h36) levou 1h30 para 24 meses só na parte B: ~150 pedidos por mês,
    # um atrás do outro (lote de 4 dias x 4 faixas x 6 famílias + 16 histogramas). Uma década inteira
    # seriam ~18 mil pedidos, ~10 h. No modo rápido o SERVIDOR agrega o período inteiro numa coleção
    # mapeada (como o sab_pedido.py faz) e cada pedido cobre o Brasil todo (divide sozinho se pesar):
    # B = 3 pedidos por ANO (sem histograma; os extremos absolutos ficam), C e H = 1 pedido por MÊS.
    # Perde-se só o detalhe por dia (o C diz o mês, não o dia, de cada violação).
    MODO_RAPIDO = ANO_FIM < 2026
    BRASIL = [(-75.0, -35.0, -28.0, 6.5)]
    _corr_lista = []

    def entregue_srv(img):
        """O mesmo que entregue(img, d), com a data lida no servidor (para coleção mapeada).
        Só para o histórico: a correção dos pixels B e do Rs dos C vale para todo dia até 31/12/2025."""
        if not _corr_lista:
            _corr_lista.append(ee.List([correcao_mes(m) for m in range(1, 13)]))
        data = img.date()
        alg = ee.String(ee.Algorithms.If(img.propertyNames().contains('versao_algoritmo'),
                                         img.get('versao_algoritmo'), 'V1.0'))
        c = ee.Image(_corr_lista[0].get(data.get('month').subtract(1)))
        corrigidas = ee.Image.cat([
            img.select('runoff_sup_mm').multiply(c.select('c_rsup')).rename('runoff_sup_mm'),
            img.select('runoff_sub_mm').multiply(c.select('c_rsub')).rename('runoff_sub_mm'),
            img.select('soil_moisture_0_5cm_m3_m3').multiply(c.select('c_ssur')).min(c.select('teto_ssur'))
              .rename('soil_moisture_0_5cm_m3_m3'),
            img.select('soil_moisture_0_100cm_m3_m3').multiply(c.select('c_swat')).min(c.select('teto_swat'))
              .rename('soil_moisture_0_100cm_m3_m3')]).toFloat()
        im = ee.Image(ee.Algorithms.If(alg.equals('V1.0'), img.addBands(corrigidas, None, True), img))
        classe = CLASSE.unmask(0, False)
        br = brdwgd_do_dia(data)
        usar_b = classe.eq(2).And(br.select('pr_mm').mask().unmask(0))
        nucleo = [im.select(b).where(usar_b, br.select(b)).rename(b) for b in NUCLEO_B]
        rso = ra_fao56(data).multiply(ELEV.unmask(0).multiply(2e-5).add(0.75)).rename('rso')
        rs = ee.Image(nucleo[5])
        nucleo[5] = rs.where(classe.eq(3).And(rs.gt(rso)), rso).rename('rs')
        im = im.addBands(ee.Image.cat(nucleo).toFloat(), None, True)
        etp = im.select('et_potencial')
        etr = im.select('et_real').min(etp).rename('et_real')
        tr = im.select('transpiracao_mm').min(etr).rename('transpiracao_mm')
        return ee.Image(im.addBands(ee.Image.cat([etr, tr]), None, True).select(BANDAS).copyProperties(img))

    def preparar_srv(img0):
        img0 = ee.Image(img0)
        img = ee.Image(ee.Algorithms.If(img0.bandNames().contains('precipitation_mm'),
                                        img0.select(BANDAS_ANTIGAS, BANDAS), img0.select(BANDAS)))
        # select guarda as propriedades (data e versão do algoritmo). [v1.9] a condição estava dentro do comentário:
        # LEITURA = 'gravado' não valia no modo rápido
        return entregue_srv(img) if LEITURA == 'entregue' else img

    def colecao(ini, fim):
        return SAB.filterDate(ini, fim).map(preparar_srv)

    def fim_do_mes(am):
        a, m = int(am[:4]), int(am[5:7])
        return f'{a + 1}-01-01' if m == 12 else f'{a}-{m + 1:02d}-01'

    # ---------------------------------------------------------------- B perfil
    if 'B' in PARTES:
        try:
            log('\n[B] perfil das 16 variáveis: momentos por classe e percentis exatos por histograma')
            feito = ler_acumulado('K26_B_momentos.csv')
            pendentes = meses_a_fazer(todos_meses, feito['mes'].unique() if len(feito) else [])
            log(f'   meses a fazer: {len(pendentes)} de {len(todos_meses)}')
            mom_novos, hist_novos = [], []
            # Cada família: (nome declarado, reducer no TEMPO por pixel, reducer no ESPAÇO por classe, chave)
            FAMILIAS = [('soma_das_medias_temporais', ee.Reducer.mean(), ee.Reducer.sum(), 'sum'),
                        ('soma_dos_desvios_temporais', ee.Reducer.stdDev(), ee.Reducer.sum(), 'sum'),
                        ('pixels_com_dado', None, ee.Reducer.sum(), 'sum'),
                        ('minimo_absoluto', ee.Reducer.min(), ee.Reducer.min(), 'min'),
                        ('maximo_absoluto', ee.Reducer.max(), ee.Reducer.max(), 'max'),
                        ('pixel_dias', ee.Reducer.count(), ee.Reducer.sum(), 'sum')]
            if MODO_RAPIDO:
                # [v1.6] um período = um ANO; 3 pedidos (somas, mínimos, máximos) para as 16 bandas
                anos = sorted({m[:4] for m in todos_meses})
                feitos = set(feito['mes'].astype(str)) if len(feito) else set()
                pend_anos = [a for a in anos if a not in feitos]
                log(f'   modo rápido: anos a fazer {len(pend_anos)} de {len(anos)} (sem histograma por mês)')
                SOMAS = [('soma_das_medias_temporais', 'm'), ('soma_dos_desvios_temporais', 's'),
                         ('pixels_com_dado', 'p'), ('pixel_dias', 'n')]
                for ano in pend_anos:
                    col = colecao(f'{ano}-01-01', f'{int(ano) + 1}-01-01')

                    def img_somas(b, col=col):
                        bs = []
                        for bb in BANDAS:
                            c = col.select(bb)
                            n = c.reduce(ee.Reducer.count()).unmask(0)
                            bs += [c.reduce(ee.Reducer.mean()).rename(f'{bb}__m'),
                                   c.reduce(ee.Reducer.stdDev()).rename(f'{bb}__s'),
                                   n.gt(0).rename(f'{bb}__p'), n.rename(f'{bb}__n')]
                        return ee.Image.cat(bs).toFloat().addBands(CLASSE)

                    def img_ext(b, col=col, red=None):
                        return ee.Image.cat([col.select(bb).reduce(red).rename(bb) for bb in BANDAS]).addBands(CLASSE)
                    nomes_s = [f'{bb}__{k}' for bb in BANDAS for _, k in SOMAS]
                    try:
                        ps = por_blocos(lambda b: rr(img_somas(b), agrupado(ee.Reducer.sum(), len(nomes_s)), b),
                                        f'B {ano} somas', BRASIL)
                        pmin = por_blocos(lambda b: rr(img_ext(b, red=ee.Reducer.min()),
                                                       agrupado(ee.Reducer.min(), len(BANDAS)), b), f'B {ano} min', BRASIL)
                        pmax = por_blocos(lambda b: rr(img_ext(b, red=ee.Reducer.max()),
                                                       agrupado(ee.Reducer.max(), len(BANDAS)), b), f'B {ano} max', BRASIL)
                    except Pesado:
                        log(f'   B {ano}: pesado mesmo dividido; pulei')
                        continue
                    gs = somar_grupos([ler_grupos(p, nomes_s, 'sum') for p in ps], nomes_s)
                    gmin = [ler_grupos(p, BANDAS, 'min') for p in pmin]
                    gmax = [ler_grupos(p, BANDAS, 'max') for p in pmax]
                    for cl, v in gs.items():
                        for bb in BANDAS:
                            mins = [g[cl][bb] for g in gmin if cl in g and g[cl].get(bb) is not None]
                            maxs = [g[cl][bb] for g in gmax if cl in g and g[cl].get(bb) is not None]
                            linha = {'mes': ano, 'classe': cl, 'nome_classe': CLASSES.get(cl, f'?{cl}'), 'variavel': bb,
                                     **{nome: v.get(f'{bb}__{k}') for nome, k in SOMAS},
                                     'minimo_absoluto': float(np.min(mins)) if mins else np.nan,
                                     'maximo_absoluto': float(np.max(maxs)) if maxs else np.nan}
                            n = linha.get('pixels_com_dado') or 0
                            linha['media'] = linha['soma_das_medias_temporais'] / n if n else np.nan
                            linha['desvio_temporal_medio'] = linha['soma_dos_desvios_temporais'] / n if n else np.nan
                            mom_novos.append(linha)
                    acrescentar(pd.DataFrame(mom_novos), 'K26_B_momentos.csv')    # checkpoint por ano
                    mom_novos = []
                    log(f'   B: {ano} pronto')
            for m in ([] if MODO_RAPIDO else pendentes):
                dd = dias_do_mes(m)
                col_mes = {bb: ee.ImageCollection([dia(d).select([bb]) for d in dd]) for bb in BANDAS}
                bruto_fam = {}
                for nome_fam, red_t, red_e, chave_k in FAMILIAS:
                    def pilha(b, red_t=red_t):
                        if red_t is None:     # contagem de pixels que têm dado em pelo menos um dia
                            bandas = [ee.Image.constant(1).updateMask(col_mes[bb].max().mask()).rename(bb)
                                      for bb in BANDAS]
                        else:
                            bandas = [col_mes[bb].reduce(red_t).rename(bb) for bb in BANDAS]
                        return ee.Image.cat(bandas).addBands(CLASSE)
                    try:
                        partes = por_blocos(lambda b: rr(pilha(b), agrupado(red_e, len(BANDAS)), b),
                                            f'B {m} {nome_fam}')
                    except Pesado:
                        log(f'   B {m} {nome_fam}: pesado mesmo dividido; pulei')
                        continue
                    bruto_fam[nome_fam] = [ler_grupos(p, BANDAS, chave_k) for p in partes]
                # junta os blocos: soma para as somas, min/max para os extremos
                classes_vistas = sorted({k for v in bruto_fam.values() for p in v for k in p})
                for cl in classes_vistas:
                    for bb in BANDAS:
                        linha = {'mes': m, 'classe': cl, 'nome_classe': CLASSES.get(cl, f'?{cl}'), 'variavel': bb}
                        for nome_fam, _, _, _ in FAMILIAS:
                            xs = [p[cl][bb] for p in bruto_fam.get(nome_fam, [])
                                  if cl in p and p[cl].get(bb) is not None]
                            if not xs:
                                linha[nome_fam] = np.nan
                            elif nome_fam == 'minimo_absoluto':
                                linha[nome_fam] = float(np.min(xs))
                            elif nome_fam == 'maximo_absoluto':
                                linha[nome_fam] = float(np.max(xs))
                            else:
                                linha[nome_fam] = float(np.sum(xs))
                        n = linha.get('pixels_com_dado') or 0
                        # média e desvio exatos: soma dividida pelo número de pixels (não média de blocos)
                        linha['media'] = linha['soma_das_medias_temporais'] / n if n else np.nan
                        linha['desvio_temporal_medio'] = linha['soma_dos_desvios_temporais'] / n if n else np.nan
                        mom_novos.append(linha)
                # HISTOGRAMA, uma variável por pedido. O fixedHistogram vive DENTRO do reduceRegion:
                # dentro do Image.reduce ele devolveria array por pixel, e o servidor recusa somar array
                # ('Reducer input must be a number' — foi o erro da v1). Com os dias como bandas, o
                # servidor devolve um histograma por dia e a soma entre dias e blocos é feita aqui.
                for bb in BANDAS:
                    lo, hi = FAIXA[bb]
                    lo2, hi2 = lo - 0.02 * (hi - lo), hi + 0.02 * (hi - lo)

                    def faz(b, bb=bb, lo2=lo2, hi2=hi2, bins=BINS):
                        img = col_mes[bb].toBands().subtract(lo2).divide(hi2 - lo2).clamp(0, 1)
                        return rr(img, ee.Reducer.fixedHistogram(0, 1, bins), b)

                    def le(partes, bins=BINS):
                        acc = np.zeros(bins)
                        for p in partes:
                            for v in (p or {}).values():
                                if v is None:
                                    continue
                                a = np.asarray(v, dtype=float)
                                if a.ndim == 2 and a.shape[1] >= 2 and a.shape[0] == bins:
                                    acc += a[:, 1]
                        return acc

                    opcoes = [(f'{bins} bins', (lambda b, bins=bins: faz(b, bins=bins)),
                               (lambda partes, bins=bins: le(partes, bins=bins)), f'B2/{bins}bins')
                              for bins in (BINS, BINS // 2, BINS // 4)]
                    nome_usado, h = tentar(opcoes, f'B2 {m} {bb}')
                    if h is None or not h.sum():
                        log(f'   B2 {m} {bb}: sem histograma; segui')
                        continue
                    bins_usados = len(h)
                    pc = percentis_de_hist(h, lo2, hi2)
                    nb, degrau = degrau_quantizacao(h, lo2, hi2)
                    f_lo, f_hi = fracao_fora(h, lo2, hi2, FAIXA[bb])
                    hist_novos.append({'mes': m, 'variavel': bb, 'n': float(h.sum()), **pc,
                                       'bins': bins_usados,
                                       'largura_bin': (hi2 - lo2) / max(bins_usados, 1),
                                       'bins_ocupados': nb,
                                       'degrau_estimado': degrau, 'frac_abaixo_faixa': f_lo,
                                       'frac_acima_faixa': f_hi, 'faixa_declarada': f'[{lo}; {hi}]'})
                log(f'   B: {m} pronto')
            if mom_novos:
                acrescentar(pd.DataFrame(mom_novos), 'K26_B_momentos.csv')
            if hist_novos:
                acrescentar(pd.DataFrame(hist_novos), 'K26_B_percentis.csv')
            hp = ler_acumulado('K26_B_percentis.csv')
            mom = ler_acumulado('K26_B_momentos.csv')
            if len(hp) or len(mom):
                fora = pd.DataFrame(columns=['variavel', 'mes'])
                if len(hp):
                    log('\npercentis exatos (histograma de ' + str(BINS) + ' bins), último mês varrido:')
                    ult = hp[hp['mes'] == hp['mes'].max()]
                    log(ult[['variavel', 'n', 'p1', 'p50', 'p99', 'p99.9', 'degrau_estimado',
                             'frac_acima_faixa']].round(4).to_string(index=False))
                    fora = hp[(hp['frac_acima_faixa'] > 0) | (hp['frac_abaixo_faixa'] > 0)]
                # [K26] o histograma perde o que passa do topo; os extremos absolutos não perdem
                ext = extremos_fora_da_faixa(mom)
                hp = hp if len(hp) else mom
                if len(ext):
                    gravar(ext.round(4), 'K26_B_extremos_fora_da_faixa.csv')
                    piores = (ext.assign(excesso=ext['maximo_absoluto'] - ext['hi'])
                              .sort_values('excesso', ascending=False).drop_duplicates('variavel'))
                    log('\nextremos absolutos fora da faixa declarada (pior mês de cada variável):\n'
                        + piores.round(3).to_string(index=False))
                # [v1.9] o veredito olha só os pixels entregues; a C_borda vira informação
                ext_e = ext[ext['nome_classe'].isin(NOMES_ENTREGUE)] if len(ext) else ext
                ext_b = ext[~ext['nome_classe'].isin(NOMES_ENTREGUE)] if len(ext) else ext
                vars_fora = sorted(set(fora['variavel']) | set(ext_e['variavel'] if len(ext_e) else []))
                resultado('B', 'ATENCAO' if vars_fora else 'OK', 'perfil das variáveis nos pixels entregues (A, B, C_interior)',
                          f'{hp["variavel"].nunique()} variáveis x {hp["mes"].nunique()} meses; '
                          + (f'fora da faixa declarada: {", ".join(vars_fora)} '
                             f'({len(fora)} variável-mês pelo histograma, {len(ext_e)} mês-classe pelos extremos '
                             f'absolutos; detalhe em K26_B_extremos_fora_da_faixa.csv)' if vars_fora
                             else 'nenhum valor fora da faixa declarada'))
                if len(ext_b):
                    resultado('B_borda', 'INFO', 'perfil: fora da faixa só na C_borda (não vai às planilhas)',
                              f'{", ".join(sorted(set(ext_b["variavel"])))} ({len(ext_b)} mês-classe)')
        except Exception as _e:
            falhou_parte('B', _e)

    # ---------------------------------------------------------------- C/D invariantes e limites
    if 'C' in PARTES or 'D' in PARTES:
        try:
            log('\n[C+D] invariantes físicas e limites de Xavier et al. (2022), todos os dias, por classe')
            # prefixo 'i_' = INFORMAÇÃO (assimetria entre rotas), não violação: fica fora do veredito.
            NOMES = ['n_pix',
                     'rs_gt_rso_motor', 'rs_gt_rso_audit', 'etr_gt_eto', 'transp_gt_etr', 'tmax_lt_tmin',
                     'rh_fora', 'solo_gt_max',
                     'runoff_sup_gt_pr', 'i_runoff_total_gt_pr', 'negativo', 'eto_zero_com_rs',
                     'vpd_incoerente', 'i_sm5_muito_acima_sm100',
                     'pr_ge_450', 'rs_ge_ra', 'rs_lt_003ra', 'u2_fora', 't_fora',
                     # [K26] degraus do escoamento: separa arredondamento de valor absurdo
                     'runoff_sup_gt_pr_10', 'runoff_sup_gt_pr_50', 'runoff_sup_gt_200',
                     # [K26 r1] Rs = 0 de dia: a rodada 1 achou Rs gravado = 0 no litoral em 33 dias de 2026,
                     # e o rs_lt_003ra não pega zero (ele exige rs > 0)
                     'rs_zero']
            def lista_flags(img, rso, ra):
                """As bandas de NOMES, na mesma ordem, para um dia (usada pelo modo normal e pelo rápido)."""
                pr = img.select('pr_mm')
                rs = img.select('rs')
                eto = img.select('et_potencial')
                etr = img.select('et_real')
                sm5 = img.select('soil_moisture_0_5cm_m3_m3')
                sm100 = img.select('soil_moisture_0_100cm_m3_m3')
                teto = UMIDADE_MAX_FISICA + 1e-4
                # Só o escoamento SUPERFICIAL é limitado pela chuva do dia. O subsuperficial
                # é drenagem do armazenamento (escoamento de base) e passa da chuva do dia
                # sem nenhuma anomalia: testar a SOMA deu 2.000.165 falsos positivos (8,5%
                # do acervo) na corrida de 09h31. A soma vira informação, não invariante.
                runoff = img.select('runoff_sup_mm')
                neg = (pr.lt(-1e-6).Or(rs.lt(-1e-6)).Or(img.select('u2').lt(-1e-6))
                       .Or(eto.lt(-1e-6)).Or(img.select('vpd').lt(-1e-6))
                       .Or(etr.lt(-1e-6)).Or(img.select('transpiracao_mm').lt(-1e-6)))
                return [
                    ee.Image.constant(1).updateMask(pr.mask()).rename('n_pix'),
                    rs.gt(rso.multiply(1.0 + TOL_RSO_MOTOR)).rename('rs_gt_rso_motor'),
                    rs.gt(rso.multiply(1.0 + TOL_RSO_AUDIT)).rename('rs_gt_rso_audit'),
                    etr.gt(eto.add(0.001)).rename('etr_gt_eto'),
                    img.select('transpiracao_mm').gt(etr.add(0.001)).rename('transp_gt_etr'),
                    img.select('tmax_C').lt(img.select('tmin_C')).rename('tmax_lt_tmin'),
                    img.select('RH').lt(0).Or(img.select('RH').gt(100)).rename('rh_fora'),
                    sm100.gt(teto).Or(sm5.gt(teto)).rename('solo_gt_max'),
                    # ---- seis que o motor NÃO testa
                    runoff.gt(pr.add(0.01)).rename('runoff_sup_gt_pr'),
                    img.select('runoff_sup_mm').add(img.select('runoff_sub_mm'))
                    .gt(pr.add(0.01)).rename('i_runoff_total_gt_pr'),
                    neg.rename('negativo'),
                    eto.lt(1e-6).And(rs.gt(1.0)).rename('eto_zero_com_rs'),
                    img.select('vpd').gt(es_sat(img)).rename('vpd_incoerente'),
                    # Não é violação: na rota GFS a camada rasa é um balde de 50 mm que satura
                # antes da profunda. Assimetria entre rotas, logo informação.
                    sm5.gt(sm100.add(0.3)).rename('i_sm5_muito_acima_sm100'),
                    # ---- limites absolutos de Xavier et al. (2022)
                    pr.gte(LIM_PR[1]).rename('pr_ge_450'),
                    rs.gte(ra).rename('rs_ge_ra'),
                    rs.lt(ra.multiply(LIM_RS_FRAC[0])).And(rs.gt(0)).rename('rs_lt_003ra'),
                    img.select('u2').lt(LIM_U2[0]).Or(img.select('u2').gt(LIM_U2[1])).rename('u2_fora'),
                    (img.select('tmax_C').gte(LIM_T[1]).Or(img.select('tmin_C').lte(LIM_T[0]))
                     ).rename('t_fora'),
                    runoff.gt(pr.add(10.0)).rename('runoff_sup_gt_pr_10'),
                    runoff.gt(pr.add(50.0)).rename('runoff_sup_gt_pr_50'),
                    runoff.gt(200.0).rename('runoff_sup_gt_200'),
                    rs.lte(0).rename('rs_zero'),
                ]

            feito = ler_acumulado('K26_CD_invariantes.csv')
            pendentes = meses_a_fazer(todos_meses, feito['mes'].unique() if len(feito) else [])
            novos = []
            if MODO_RAPIDO:
                # [v1.6] um pedido por MÊS: o servidor soma as bandas de cada dia no tempo e depois por classe
                log(f'   modo rápido: meses a fazer {len(pendentes)} de {len(todos_meses)} (contagem por mês)')

                def flags_srv(img):
                    img = ee.Image(img)
                    data = img.date()
                    return ee.Image.cat(lista_flags(img, rso_fao56(data), ra_fao56(data))).unmask(0).toFloat()
                for m in pendentes:
                    soma = colecao(f'{m}-01', fim_do_mes(m)).map(flags_srv).sum().rename(NOMES).addBands(CLASSE)
                    try:
                        partes = por_blocos(lambda b, soma=soma: rr(soma, agrupado(ee.Reducer.sum(), len(NOMES)), b),
                                            f'CD {m}', BRASIL)
                    except Pesado:
                        log(f'   CD {m}: pesado mesmo dividido; pulei')
                        continue
                    g = somar_grupos([ler_grupos(p, NOMES, 'sum') for p in partes], NOMES)
                    rota_m = dias_rota.get(f'{m}-01')
                    linhas_m = [{'mes': m, 'data': m, 'rota': rota_m, 'classe': cl, 'nome_classe': CLASSES.get(cl, f'?{cl}'),
                                 **{nm: int(round(v.get(nm) or 0)) for nm in NOMES}} for cl, v in g.items()]
                    acrescentar(pd.DataFrame(linhas_m), 'K26_CD_invariantes.csv')     # checkpoint por mês
                    log(f'   CD: {m} lido')
            for m in ([] if MODO_RAPIDO else pendentes):
                dd = dias_do_mes(m)
                tam = DIAS_POR_PEDIDO
                i = 0
                while i < len(dd):
                    lote = dd[i:i + tam]

                    def flags(b, lote=lote):
                        saida = []
                        for d in lote:
                            img = dia(d)
                            rso = rso_fao56(d)
                            ra = ra_fao56(d)
                            saida += lista_flags(img, rso, ra)
                        n = len(NOMES)
                        return ee.Image.cat([ee.Image.cat(saida[k * n:(k + 1) * n]).unmask(0)
                                             for k in range(len(lote))]).addBands(CLASSE)

                    try:
                        partes = por_blocos(lambda b: rr(flags(b), agrupado(ee.Reducer.sum(), len(NOMES) * len(lote)), b),
                                            f'CD {lote[0]}')
                    except Pesado:
                        if tam > 1:
                            tam = max(1, tam // 2)
                            log(f'   CD {lote[0]}: pesado; lote cai para {tam} dia(s)')
                            continue
                        raise
                    nomes_lote = [f'{nm}__{k}' for k in range(len(lote)) for nm in NOMES]
                    g = somar_grupos([ler_grupos(p, nomes_lote, 'sum') for p in partes], nomes_lote)
                    for k, d in enumerate(lote):
                        for cl, vals in g.items():
                            novos.append({'mes': m, 'data': d, 'rota': dias_rota.get(d), 'classe': cl,
                                          'nome_classe': CLASSES.get(cl, f'?{cl}'),
                                          **{nm: int(round(vals.get(f'{nm}__{k}') or 0)) for nm in NOMES}})
                    log(f'   CD: {lote[0]} a {lote[-1]} lidos')
                    i += len(lote)
                if novos:
                    acrescentar(pd.DataFrame(novos), 'K26_CD_invariantes.csv')
                    novos = []
            cd = ler_acumulado('K26_CD_invariantes.csv')
            if len(cd):
                tot = {cl: {c: cd.loc[cd['classe'] == cl, c].sum() for c in NOMES}
                       for cl in sorted(cd['classe'].unique())}
                # [v1.9] veredito só nos pixels entregues; a C_borda vira informação
                tot_e = {cl: v for cl, v in tot.items() if int(cl) in GRUPO_ENTREGUE}
                tot_b = {cl: v for cl, v in tot.items() if int(cl) in GRUPO_BORDA}
                st, texto = decidir_invariantes(tot_e)
                esc_def = cd[cd['classe'].isin(GRUPO_ENTREGUE) & (cd['rota'] == 'BR-DWGD')]['runoff_sup_gt_pr'].sum()
                if esc_def > 0:
                    texto += ' || ' + NOTA_ESCOAMENTO
                resultado('C', st, 'invariantes físicas e limites absolutos nos pixels entregues (A, B, C_interior)', texto)
                if tot_b:
                    st_b, texto_b = decidir_invariantes(tot_b)
                    resultado('C_borda', 'INFO', 'invariantes na C_borda (fora das planilhas; só informação)',
                              f'{st_b}: {texto_b}')
                porclasse = cd.groupby('nome_classe')[NOMES].sum()
                log('\nviolações por classe:\n' + porclasse.loc[:, (porclasse.sum() > 0) | (porclasse.columns == 'n_pix')].to_string())
                porrota = cd.groupby('rota')[NOMES].sum()
                log('\nviolações por rota:\n' + porrota.loc[:, (porrota.sum() > 0) | (porrota.columns == 'n_pix')].to_string())
                gravar(porclasse.reset_index(), 'K26_CD_por_classe.csv')
                gravar(porrota.reset_index(), 'K26_CD_por_rota.csv')

                # localiza cada pixel violador dos dias com violação (sample factor=1: varre TODOS os pixels)
                alvos = cd[cd[[c for c in NOMES if c != 'n_pix']].sum(axis=1) > 0]['data'].unique().tolist()
                if alvos and MODO_RAPIDO:
                    log(f'\n   modo rápido: {len(alvos)} mês(es) com violação; os pixels não são localizados aqui '
                        f'(a contagem é por mês). Para localizar, rode o mês com ANO_FIM >= 2026 ou peça uma parte nova.')
                if alvos and not MODO_RAPIDO:
                    log(f'\n   localizando os pixels violadores em {len(alvos)} dia(s)')
                    achados = []
                    for d in alvos[:40]:
                        img = dia(d)
                        rso, ra = rso_fao56(d), ra_fao56(d)
                        ruim = (img.select('rs').gt(rso.multiply(1.0 + TOL_RSO_MOTOR))
                                .Or(img.select('rs').gte(ra))
                                .Or(img.select('et_real').gt(img.select('et_potencial').add(0.001)))
                                .Or(img.select('tmax_C').lt(img.select('tmin_C')))
                                .Or(img.select('RH').lt(0).Or(img.select('RH').gt(100))))
                        alvo = (img.select(['rs', 'pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real'])
                                .addBands([rso, ra, ELEV.rename('elev'), CLASSE]).updateMask(ruim))
                        for b in BLOCOS:
                            try:
                                fs = gi(alvo.sample(region=geom(b), projection=PROJ, factor=1, seed=SEMENTE,
                                                    geometries=True, dropNulls=True, tileScale=16)
                                        .limit(MAX_PIXELS_LISTA), f'violadores {d}')['features']
                            except Pesado:
                                continue
                            for f in fs:
                                p = f['properties']
                                achados.append({'data': d, 'lon': round(f['geometry']['coordinates'][0], 4),
                                                'lat': round(f['geometry']['coordinates'][1], 4),
                                                'classe': p.get('classe'), **{k: p.get(k) for k in
                                                ('rs', 'rso', 'ra', 'elev', 'pr_mm', 'tmax_C', 'tmin_C', 'RH',
                                                 'et_potencial', 'et_real')}})
                    if achados:
                        av = pd.DataFrame(achados)
                        av['rs_sobre_rso'] = av['rs'] / av['rso']
                        av['rs_sobre_ra'] = av['rs'] / av['ra']
                        gravar(av.round(4), 'K26_D_pixels_violadores.csv')
                        log(av.head(20).round(3).to_string(index=False))
                        resultado('D', 'ATENCAO', 'pixels violadores localizados',
                                  f'{len(av)} pixel-dias listados em K26_D_pixels_violadores.csv; '
                                  f'classes {sorted(set(av["classe"].dropna()))}; '
                                  f'maior rs/Rso {av["rs_sobre_rso"].max():.4f}, maior rs/Ra {av["rs_sobre_ra"].max():.4f}')
        except Exception as _e:
            falhou_parte('C+D', _e)

    # ---------------------------------------------------------------- E recorde do pixel
    if 'E' in PARTES:
        try:
            log('\n[E] excesso sobre o recorde do próprio pixel, por rota E POR MÊS')
            VARS_REC = [('tmax_C', 'Tmax'), ('tmin_C', 'Tmin'), ('pr_mm', 'pr'), ('rs', 'Rs'), ('u2', 'u2')]
            feito = ler_acumulado('K26_E_recorde.csv')
            pendentes = meses_a_fazer(todos_meses, feito['mes'].unique() if len(feito) else [])
            novos = []
            for m in pendentes:
                dd = dias_do_mes(m)
                mes_num = int(m[5:7])
                for sab_b, br_b in VARS_REC:
                    modo, limiares, unidade = LIMIARES_REC[sab_b]

                    # DUAS imagens: indicadores (unmask 0, somados) e excesso (mascarado, para o máximo).
                    # Misturar as duas numa só contamina a soma onde o pixel é mascarado.
                    def ind(b, dd=dd, sab_b=sab_b, br_b=br_b, mes_num=mes_num, modo=modo, limiares=limiares):
                        rec = recorde(br_b, mes_num)
                        saida = []
                        for d in dd:
                            x = dia(d).select(sab_b)
                            saida.append(ee.Image.constant(1).updateMask(x.mask().And(rec.mask())).rename('n'))
                            for j, t in enumerate(limiares):
                                alvo = rec.add(t) if modo == 'mais' else rec.multiply(t)
                                saida.append(x.gt(alvo).updateMask(x.mask().And(rec.mask())).rename(f'g{j}'))
                        return ee.Image.cat([t.unmask(0) for t in saida]).addBands(CLASSE)

                    def exc(b, dd=dd, sab_b=sab_b, br_b=br_b, mes_num=mes_num):
                        rec = recorde(br_b, mes_num)
                        return ee.Image.cat([dia(d).select(sab_b).subtract(rec).rename('exc')
                                             for d in dd]).addBands(CLASSE)
                    n_ind = 1 + len(limiares)
                    try:
                        partes_s = por_blocos(lambda b: rr(ind(b), agrupado(ee.Reducer.sum(), n_ind * len(dd)), b),
                                              f'E {m} {sab_b}')
                        partes_x = por_blocos(lambda b: rr(exc(b), agrupado(ee.Reducer.max(), len(dd)), b),
                                              f'E {m} {sab_b} max')
                    except Pesado:
                        log(f'   E {m} {sab_b}: pesado; pulei')
                        continue
                    nomes = [f'{n}__{k}' for k in range(len(dd))
                             for n in ['n'] + [f'g{j}' for j in range(len(limiares))]]
                    nomes_x = [f'exc__{k}' for k in range(len(dd))]
                    gs = somar_grupos([ler_grupos(p, nomes, 'sum') for p in partes_s], nomes)
                    gx = [ler_grupos(p, nomes_x, 'max') for p in partes_x]
                    for k, d in enumerate(dd):
                        for cl, v in gs.items():
                            # as somas vêm de bandas com unmask(-9999): só 'n' e 'g*' são indicadores limpos
                            n = max(0.0, (v.get(f'n__{k}') or 0))
                            linha = {'mes': m, 'data': d, 'rota': dias_rota.get(d), 'faixa': dias_faixa.get(d),
                                     'classe': cl, 'nome_classe': CLASSES.get(cl, f'?{cl}'), 'variavel': sab_b,
                                     'modo': modo, 'n': int(n)}
                            for j, t in enumerate(limiares):
                                bruto = v.get(f'g{j}__{k}')
                                linha[f'limiar_{j}'] = t
                                linha[f'pct_acima_{j}'] = (100.0 * bruto / n) if (n and bruto is not None) else np.nan
                            linha['excesso_max'] = max([x[cl][f'exc__{k}'] for x in gx
                                                        if cl in x and x[cl].get(f'exc__{k}') is not None]
                                                       or [np.nan])
                            novos.append(linha)
                log(f'   E: {m} pronto')
                if novos:
                    acrescentar(pd.DataFrame(novos), 'K26_E_recorde.csv')
                    novos = []
            E = ler_acumulado('K26_E_recorde.csv')
            if len(E):
                # ERA5 x GFS DENTRO DO MESMO MÊS: o que a K24 não fez (ela comparou outubro com novembro)
                comp = []
                for (m, v, cl), g in E.groupby(['mes', 'variavel', 'nome_classe']):
                    a = g.loc[g['rota'] == 'ERA5'].groupby('data')['pct_acima_1'].mean().dropna()
                    b = g.loc[g['rota'] == 'GFS'].groupby('data')['pct_acima_1'].mean().dropna()
                    if len(a) >= 2 and len(b) >= 2:
                        dif, p, na, nb = permutacao(a.values, b.values)
                        comp.append({'mes': m, 'variavel': v, 'classe': cl, 'media_ERA5': float(a.mean()),
                                     'media_GFS': float(b.mean()), 'diferenca': dif, 'p_permutacao': p,
                                     'n_dias_ERA5': na, 'n_dias_GFS': nb,
                                     'significativo_alfa_005': bool(np.isfinite(p) and p < ALFA)})
                if comp:
                    cp = pd.DataFrame(comp)
                    gravar(cp.round(6), 'K26_E_rotas_mesmo_mes.csv')
                    log('\nERA5 x GFS no MESMO mês e na MESMA classe (% de pixel-dias acima do limiar 1):')
                    log(cp.round(4).to_string(index=False))
                linhas_res = []
                for (v, rota), t in E.groupby(['variavel', 'rota'], dropna=False):
                    peso = t['n'].clip(lower=1)
                    linhas_res.append({'variavel': v, 'rota': rota, 'dias': t['data'].nunique(),
                                       'pixel_dias': int(t['n'].sum()),
                                       **{f'pct_acima_{j}': float(np.average(t[f'pct_acima_{j}'].fillna(0), weights=peso))
                                          for j in (0, 1, 2) if f'pct_acima_{j}' in t},
                                       'excesso_max': float(t['excesso_max'].max())})
                resumo = pd.DataFrame(linhas_res)
                # Antes de concluir qualquer coisa: a REFERÊNCIA é confiável? O recorde sai de uma
                # decodificação do BR-DWGD que é suposição. Se um campo passa do recorde de 35 anos em
                # mais de MAX_PCT_REFERENCIA_SUSPEITA, a explicação mais provável é a referência errada,
                # e reportar o número como achado seria inventar um defeito. Então a variável é
                # suprimida do veredito e o motivo vai escrito.
                de_para = {'tmax_C': 'Tmax', 'tmin_C': 'Tmin', 'pr_mm': 'pr', 'rs': 'Rs', 'u2': 'u2'}
                resumo['decodificacao_conferida'] = [DECODE_CONFERIDO.get(de_para.get(v), False)
                                                     for v in resumo['variavel']]
                resumo['referencia_suspeita'] = ((resumo['pct_acima_0'] > MAX_PCT_REFERENCIA_SUSPEITA)
                                                 | (~resumo['decodificacao_conferida']))
                gravar(resumo.round(5), 'K26_E_resumo.csv')
                log('\n' + resumo.round(4).to_string(index=False))
                suspeitas = sorted(set(resumo.loc[resumo['referencia_suspeita'], 'variavel']))
                bom = resumo[~resumo['referencia_suspeita']]
                if suspeitas:
                    log('\n   REFERÊNCIA SUSPEITA e por isso SUPRIMIDA do veredito: '
                        + ', '.join(suspeitas))
                    for v in suspeitas:
                        pc = resumo.loc[resumo['variavel'] == v, 'pct_acima_0'].max()
                        log(f'      {v}: {pc:.2f}% dos pixel-dias acima do recorde. Um campo plausível '
                            f'fica na ordem de 0,1%; isto é assinatura de recorde mal decodificado '
                            f'(confira escala e deslocamento de {de_para.get(v, v)} em DECODE_BR).')
                if len(bom):
                    pior = bom.sort_values('pct_acima_1', ascending=False).iloc[0]
                    resultado('E', 'ATENCAO' if pior['pct_acima_1'] > 1.0 else 'INFO',
                              'excesso sobre o recorde do pixel por variável e rota',
                              f'pior caso entre as variáveis com referência confiável: {pior["variavel"]} na '
                              f'rota {pior["rota"]}, {pior["pct_acima_1"]:.3f}% dos pixel-dias acima do '
                              f'limiar 1 (maior excesso {pior["excesso_max"]:+.2f}). Para um campo bem '
                              f'calibrado contra um recorde de {ANOS_RECORDE[1] - ANOS_RECORDE[0] + 1} anos a '
                              f'expectativa é da ordem de 0,1%: acima de 1% é desacordo distribucional, não '
                              f'clima.'
                              + (f' SUPRIMIDAS por referência suspeita: {", ".join(suspeitas)}.'
                                 if suspeitas else ''))
                else:
                    resultado('E', 'FALHOU', 'excesso sobre o recorde do pixel',
                              'nenhuma variável tem referência confiável: a decodificação do BR-DWGD em '
                              'DECODE_BR precisa ser conferida antes deste teste valer.')
        except Exception as _e:
            falhou_parte('E', _e)

    # ---------------------------------------------------------------- F emenda por variável
    if 'F' in PARTES:
        try:
            log(f'\n[F] emenda: razão dos desvios por variável em {N_PONTOS_EMENDA} pixels de classe A')
            sorteio = (ee.Image.pixelLonLat().addBands(CLASSE)
                       .stratifiedSample(numPoints=0, classBand='classe', region=geom((-75.0, -35.0, -28.0, 6.5)),
                                         projection=PROJ, seed=SEMENTE, classValues=[1],
                                         classPoints=[N_PONTOS_EMENDA], geometries=True, tileScale=16))
            pts = [{'pid': k, 'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1]}
                   for k, f in enumerate(gi(sorteio, 'pontos da emenda')['features'])]
            fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']})
                                       for p in pts])
            chave = {(int(math.floor((p['lon'] - X0) / DX + 1e-6)),
                      int(math.floor((Y0 - p['lat']) / DX + 1e-6))): p['pid'] for p in pts}
            PARES = [('pr_mm', 'pr'), ('tmax_C', 'Tmax'), ('tmin_C', 'Tmin'), ('RH', 'RH'), ('rs', 'Rs'), ('u2', 'u2')]
            ref = []
            for mes in range(1, 13):
                if not any(int(m[5:7]) == mes for m in todos_meses):
                    continue
                # O Earth Engine exige que a função passada a List.map e a ImageCollection.map receba
                # EXATAMENTE um argumento. Um parâmetro com valor padrão já conta como segundo, e o servidor
                # recusa com 'List.map: A mapped algorithm must take one argument.' — foi o erro desta parte
                # na corrida de 09h31. Por isso a variável é fechada numa fábrica, sem argumento padrão.
                def fab_br_var(nome_br):
                    def f(img):
                        return br_var(img, nome_br)
                    return f

                def fab_por_ano(mes_alvo):
                    def por_ano(a):
                        sub = (BR.filter(ee.Filter.calendarRange(a, a, 'year'))
                               .filter(ee.Filter.calendarRange(mes_alvo, mes_alvo, 'month')))
                        return ee.Image.cat([sub.map(fab_br_var(v)).reduce(ee.Reducer.stdDev())
                                             .rename(f'{s}_sd') for s, v in PARES])
                    return por_ano

                anos = ee.List.sequence(*ANOS_REF_EMENDA)
                sd = ee.ImageCollection(anos.map(fab_por_ano(mes))).mean()
                me = ee.Image.cat([(BR.filter(ee.Filter.calendarRange(*ANOS_REF_EMENDA, 'year'))
                                    .filter(ee.Filter.calendarRange(mes, mes, 'month'))
                                    .map(fab_br_var(v)).mean().rename(f'{s}_m')) for s, v in PARES])
                r = gi(sd.addBands(me).sampleRegions(collection=fc, properties=['pid'], projection=PROJ,
                                                     geometries=False, tileScale=16), f'BR-DWGD mês {mes:02d}')
                ref += [dict(f['properties'], mes=mes) for f in r['features']]
            ref = pd.DataFrame(ref)
            if not len(ref) or 'pid' not in ref:
                resultado('F', 'FALHA', 'razão dos desvios na emenda',
                          'o BR-DWGD não devolveu referência nos pixels sorteados: confira o asset e a decodificação')
                ref = pd.DataFrame(columns=['pid', 'mes'])
            linhas = []
            for rota in ('ERA5', 'GFS'):
                datas = [d for d, r in dias_rota.items() if r == rota and d[:7] in set(todos_meses)]
                if len(datas) < 10:
                    continue
                sab = []
                for m in sorted({d[:7] for d in datas}):
                    dm = sorted(d for d in datas if d[:7] == m)
                    reg = gi(ee.ImageCollection([dia(d).select([s for s, _ in PARES]) for d in dm])
                             .getRegion(ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in pts]), None,
                                        CRS, TRANSFORM), f'SAB {rota} {m}')
                    df = pd.DataFrame(reg[1:], columns=reg[0])
                    ix = np.floor((df['longitude'].astype(float) - X0) / DX + 1e-6).astype(int)
                    iy = np.floor((Y0 - df['latitude'].astype(float)) / DX + 1e-6).astype(int)
                    df['pid'] = [chave.get((a, b)) for a, b in zip(ix, iy)]
                    df['data'] = pd.to_datetime(df['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
                    sab.append(df.dropna(subset=['pid'])[['pid', 'data'] + [s for s, _ in PARES]])
                if not sab:
                    continue
                sab = pd.concat(sab, ignore_index=True)
                sab['pid'] = sab['pid'].astype(int)
                for s, _ in PARES:
                    sab[s] = pd.to_numeric(sab[s], errors='coerce')
                for s, _ in PARES:
                    if f'{s}_sd' not in ref.columns:
                        continue
                    razao, vies, n = razao_e_vies(sab, ref, s)
                    linhas.append({'rota': rota, 'variavel': s, 'razao_desvio': razao, 'vies_medio': vies,
                                   'n_pixel_mes': n, 'dentro_085_115': bool(0.85 <= razao <= 1.15)
                                   if np.isfinite(razao) else None})
            if not linhas:
                resultado('F', 'FALHOU', 'razão dos desvios na emenda',
                          'nenhuma variável pôde ser medida. Causas prováveis: o BR-DWGD não devolveu '
                          'desvio nos pixels sorteados (confira a decodificação em DECODE_BR), menos de '
                          '10 dias por pixel-mês no intervalo pedido, ou nenhuma rota com 10 dias ou mais. '
                          'Rode a parte F sozinha com um intervalo de pelo menos um mês cheio por rota.')
            if linhas:
                F = pd.DataFrame(linhas)
                gravar(F.round(5), 'K26_F_emenda.csv')
                log('\n' + F.round(3).to_string(index=False))
                fora = F[F['dentro_085_115'] == False]
                resultado('F', 'FALHA' if len(fora) else 'OK', 'razão dos desvios na emenda, por variável e rota',
                          (', '.join(f'{r.rota}/{r.variavel} {r.razao_desvio:.2f}' for r in fora.itertuples())
                           + ' fora de [0,85; 1,15]' if len(fora) else 'todas as variáveis dentro de [0,85; 1,15]')
                          + ' | a K22 mede isto só para a UR')
        except Exception as _e:
            falhou_parte('F', _e)

    # ---------------------------------------------------------------- G derivadas
    if 'G' in PARTES:
        try:
            log('\n[G] coerência das derivadas: ETo e VPD recalculados das primárias gravadas')
            feito = ler_acumulado('K26_G_derivadas.csv')
            pendentes = meses_a_fazer(todos_meses, feito['mes'].unique() if len(feito) else [])
            novos = []
            for m in pendentes:
                dd = dias_do_mes(m)
                for lote in lotes(dd, DIAS_POR_PEDIDO):
                    def flags(b, lote=lote):
                        saida = []
                        for d in lote:
                            img = dia(d)
                            eto_calc = eto_ee(img, d)
                            vpd_calc = vpd_ee(img)
                            de = img.select('et_potencial').subtract(eto_calc).abs()
                            dv = img.select('vpd').subtract(vpd_calc).abs()
                            saida += [ee.Image.constant(1).updateMask(img.select('et_potencial').mask()).rename('n'),
                                      de.gt(TOL_ETO).rename('eto_difere'),
                                      dv.gt(TOL_VPD).rename('vpd_difere'),
                                      de.rename('eto_dif_abs'), dv.rename('vpd_dif_abs')]
                        return ee.Image.cat([s.unmask(0) for s in saida]).addBands(CLASSE)
                    def difs(b, lote=lote):
                        saida = []
                        for d in lote:
                            img = dia(d)
                            saida += [img.select('et_potencial').subtract(eto_ee(img, d)).abs().rename('eto_dif_abs'),
                                      img.select('vpd').subtract(vpd_ee(img)).abs().rename('vpd_dif_abs')]
                        return ee.Image.cat(saida).addBands(CLASSE)
                    try:
                        partes_s = por_blocos(lambda b: rr(flags(b), agrupado(ee.Reducer.sum(), 5 * len(lote)), b),
                                              f'G {lote[0]}')
                        partes_x = por_blocos(lambda b: rr(difs(b), agrupado(ee.Reducer.max(), 2 * len(lote)), b),
                                              f'G max {lote[0]}')
                    except Pesado:
                        log(f'   G {lote[0]}: pesado; pulei o lote')
                        continue
                    nomes = [f'{n}__{k}' for k in range(len(lote))
                             for n in ('n', 'eto_difere', 'vpd_difere', 'eto_dif_abs', 'vpd_dif_abs')]
                    nomes_x = [f'{n}__{k}' for k in range(len(lote)) for n in ('eto_dif_abs', 'vpd_dif_abs')]
                    gs = somar_grupos([ler_grupos(p, nomes, 'sum') for p in partes_s], nomes)
                    gx = [ler_grupos(p, nomes_x, 'max') for p in partes_x]
                    for k, d in enumerate(lote):
                        for cl, v in gs.items():
                            n = v.get(f'n__{k}') or 0
                            mx_eto = max([x[cl][f'eto_dif_abs__{k}'] for x in gx
                                          if cl in x and x[cl].get(f'eto_dif_abs__{k}') is not None] or [np.nan])
                            mx_vpd = max([x[cl][f'vpd_dif_abs__{k}'] for x in gx
                                          if cl in x and x[cl].get(f'vpd_dif_abs__{k}') is not None] or [np.nan])
                            novos.append({'mes': m, 'data': d, 'rota': dias_rota.get(d), 'classe': cl,
                                          'nome_classe': CLASSES.get(cl, f'?{cl}'), 'n': int(n),
                                          'eto_difere': int(v.get(f'eto_difere__{k}') or 0),
                                          'vpd_difere': int(v.get(f'vpd_difere__{k}') or 0),
                                          'eto_dif_media': (v.get(f'eto_dif_abs__{k}') or 0) / n if n else np.nan,
                                          'vpd_dif_media': (v.get(f'vpd_dif_abs__{k}') or 0) / n if n else np.nan,
                                          'eto_dif_max': mx_eto, 'vpd_dif_max': mx_vpd})
                    log(f'   G: {lote[0]} a {lote[-1]} lidos')
                if novos:
                    acrescentar(pd.DataFrame(novos), 'K26_G_derivadas.csv')
                    novos = []
            G = ler_acumulado('K26_G_derivadas.csv')
            if len(G):
                por = G.groupby('rota').agg(dias=('data', 'nunique'), n=('n', 'sum'),
                                            eto_difere=('eto_difere', 'sum'), vpd_difere=('vpd_difere', 'sum'),
                                            eto_dif_max=('eto_dif_max', 'max'), vpd_dif_max=('vpd_dif_max', 'max'))
                log('\n' + por.to_string())
                gravar(por.reset_index(), 'K26_G_resumo.csv')
                # [K26] nos dias definitivos a ETo vem do BR-DWGD: divergir é esperado e não entra no veredito
                calc = por.drop(index=[r for r in por.index if r == 'BR-DWGD'])
                ruim = int(calc['eto_difere'].sum() + calc['vpd_difere'].sum()) if len(calc) else 0
                grande = G[(G['rota'] != 'BR-DWGD') & (G['eto_dif_max'] > 1.0)]
                resultado('G', 'FALHA' if ruim else 'OK', 'ETo e VPD gravados conferem com as primárias (dias ERA5 e GFS)',
                          (f'{ruim:,} pixel-dias divergem (tolerância ETo {TOL_ETO} mm, VPD {TOL_VPD} kPa); '
                           f'maior divergência ETo {calc["eto_dif_max"].max():.4f} mm, VPD {calc["vpd_dif_max"].max():.4f} kPa; '
                           f'{grande["data"].nunique()} dia(s) com algum pixel acima de 1 mm (classes '
                           f'{", ".join(sorted(set(grande["nome_classe"].astype(str))))}): a parte P procura a causa.'
                           if len(calc) else 'nenhum dia ERA5 ou GFS no intervalo')
                          + (' Dias definitivos (ETo do BR-DWGD) ficam só em K26_G_resumo.csv.'
                             if 'BR-DWGD' in por.index else ''))
        except Exception as _e:
            falhou_parte('G', _e)

    # ---------------------------------------------------------------- H máscara e balanço
    if 'H' in PARTES:
        try:
            log('\n[H] máscara banda a banda e balanço hídrico')
            feito = ler_acumulado('K26_H_mascara_v19.csv')
            pendentes = meses_a_fazer(todos_meses, feito['mes'].unique() if len(feito) else [])
            novos = []
            if MODO_RAPIDO:
                # [v1.6] um pedido por MÊS: pixel-dias com valor em cada banda, por classe
                log(f'   modo rápido: meses a fazer {len(pendentes)} de {len(todos_meses)} (pixel-dias por mês)')

                def tem_valor(img):
                    img = ee.Image(img)
                    return ee.Image.cat([img.select(bb).mask().gt(0).rename(bb)
                                         for bb in BANDAS]).unmask(0).toFloat()
                for m in pendentes:
                    soma = colecao(f'{m}-01', fim_do_mes(m)).map(tem_valor).sum().rename(BANDAS).addBands(CLASSE)
                    try:
                        partes = por_blocos(lambda b, soma=soma: rr(soma, agrupado(ee.Reducer.sum(), len(BANDAS)), b),
                                            f'H {m}', BRASIL)
                    except Pesado:
                        log(f'   H {m}: pesado mesmo dividido; pulei')
                        continue
                    g = somar_grupos([ler_grupos(p, BANDAS, 'sum') for p in partes], BANDAS)
                    rota_m = dias_rota.get(f'{m}-01')
                    linhas_m = [{'mes': m, 'data': m, 'rota': rota_m, 'classe': cl, 'nome_classe': CLASSES.get(cl, f'?{cl}'),
                                 **{bb: int(round(v.get(bb) or 0)) for bb in BANDAS}} for cl, v in g.items()]
                    acrescentar(pd.DataFrame(linhas_m), 'K26_H_mascara_v19.csv')     # checkpoint por mês
                    log(f'   H: {m} lido')
            for m in ([] if MODO_RAPIDO else pendentes):
                dd = dias_do_mes(m)
                for lote in lotes(dd, DIAS_POR_PEDIDO):
                    def conta(b, lote=lote):
                        saida = []
                        for d in lote:
                            img = dia(d)
                            saida += [img.select(bb).mask().gt(0).rename(bb)
                                      for bb in BANDAS]
                        return ee.Image.cat([s.unmask(0) for s in saida]).addBands(CLASSE)
                    try:
                        partes = por_blocos(lambda b: rr(conta(b), agrupado(ee.Reducer.sum(), len(BANDAS) * len(lote)), b),
                                            f'H {lote[0]}')
                    except Pesado:
                        log(f'   H {lote[0]}: pesado; pulei o lote')
                        continue
                    nomes = [f'{bb}__{k}' for k in range(len(lote)) for bb in BANDAS]
                    g = somar_grupos([ler_grupos(p, nomes, 'sum') for p in partes], nomes)
                    for k, d in enumerate(lote):
                        for cl, v in g.items():
                            linha = {'mes': m, 'data': d, 'rota': dias_rota.get(d), 'classe': cl,
                                     'nome_classe': CLASSES.get(cl, f'?{cl}')}
                            linha.update({bb: int(round(v.get(f'{bb}__{k}') or 0)) for bb in BANDAS})
                            novos.append(linha)
                    log(f'   H: {lote[0]} a {lote[-1]} lidos')
                if novos:
                    acrescentar(pd.DataFrame(novos), 'K26_H_mascara_v19.csv')
                    novos = []
            H = ler_acumulado('K26_H_mascara_v19.csv')
            if len(H):
                def faltas(Hs):
                    if not len(Hs):
                        return []
                    por_dia = Hs.groupby(['data', 'rota'], dropna=False)[BANDAS].sum().reset_index()
                    por_dia['maximo'] = por_dia[BANDAS].max(axis=1)
                    # [K26] bandas que o motor deixa vazias de propósito não são vazamento
                    por_dia['versao'] = por_dia['data'].map(dias_versao)
                    por_dia = ajustar_vazias_por_desenho(por_dia, BANDAS)
                    por_dia = ajustar_vazias_por_desenho(por_dia, BANDAS, VAZIAS_POR_VERSAO, coluna='versao')
                    saida = []
                    for bb in BANDAS:
                        d = (por_dia['maximo'] - por_dia[bb])
                        if d.max() > 0:
                            saida.append({'variavel': bb, 'dias_com_falta': int((d > 0).sum()),
                                          'pior_dia': por_dia.loc[d.idxmax(), 'data'],
                                          'rota_pior': por_dia.loc[d.idxmax(), 'rota'],
                                          'pixels_a_menos': int(d.max()),
                                          'pct_a_menos': float(100 * d.max() / por_dia.loc[d.idxmax(), 'maximo'])})
                    return saida
                # [v1.9] separado por grupo: só a falta nos pixels entregues é vazamento que chega ao usuário
                falta = faltas(H[H['classe'].isin(GRUPO_ENTREGUE)])
                falta_b = faltas(H[H['classe'].isin(GRUPO_BORDA)])
                if falta or falta_b:
                    fv = pd.concat([pd.DataFrame(falta).assign(grupo='entregue'),
                                    pd.DataFrame(falta_b).assign(grupo='C_borda')], ignore_index=True)
                    fv = fv.sort_values(['grupo', 'pixels_a_menos'], ascending=[False, False])
                    gravar(fv, 'K26_H_vazamento_mascara.csv')
                    log('\nbandas com menos pixels que a banda mais completa do mesmo dia, por grupo:\n'
                        + fv.to_string(index=False))
                resultado('H', 'ATENCAO' if falta else 'OK', 'máscara igual nas 16 bandas nos pixels entregues (A, B, C_interior)',
                          (f'{len(falta)} banda(s) com pixels a menos: '
                           + ', '.join(f'{r["variavel"]} (até {r["pixels_a_menos"]:,} px, {r["pct_a_menos"]:.3f}%)'
                                       for _, r in pd.DataFrame(falta).iterrows())
                           + '. Uma banda com menos pixels que as outras é vazamento de máscara: o valor foi '
                             'descartado em vez de preservado.') if falta
                          else 'as 16 bandas têm o mesmo número de pixels em todos os dias varridos')
                if falta_b:
                    resultado('H_borda', 'INFO', 'máscara na C_borda (fora das planilhas; só informação)',
                              ', '.join(f'{r["variavel"]} (até {r["pixels_a_menos"]:,} px)' for r in falta_b))
        except Exception as _e:
            falhou_parte('H', _e)

    fechar(T0)


def es_sat(img):
    """es médio do dia a partir da Tmax e da Tmin gravadas (para checar o VPD)."""
    import ee
    def es(T):
        return T.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': T})
    return es(img.select('tmax_C')).add(es(img.select('tmin_C'))).divide(2).rename('es')


def vpd_ee(img):
    return es_sat(img).multiply(ee_const(1).subtract(img.select('RH').divide(100))).max(0).rename('vpd_calc')


def ee_const(v):
    import ee
    return ee.Image.constant(v)


def eto_ee(img, d, elev=None):
    """ETo FAO-56 exatamente como o eto_penman_monteith do motor V1.6, a partir das bandas GRAVADAS.
    elev: a elevação a usar (padrão: o SRTM como o motor, mascarado onde o SRTM não tem valor)."""
    import ee
    ELEV = elev if elev is not None else ee.Image('USGS/SRTMGL1_003')
    tmax, tmin = img.select('tmax_C'), img.select('tmin_C')
    rh, u2, rs = img.select('RH'), img.select('u2'), img.select('rs')
    lat = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180.0)
    p = ELEV.multiply(-0.0065).add(293.0).divide(293.0).pow(5.26).multiply(101.3)
    gamma = p.multiply(0.000665)
    tm = tmax.add(tmin).divide(2)

    def es(T):
        return T.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': T})
    esm = es(tmax).add(es(tmin)).divide(2)
    ea = esm.multiply(rh).divide(100)
    vpd = esm.subtract(ea).max(0)
    J = ee.Number(ee.Date(d).getRelative('day', 'year')).add(1)
    dr = J.multiply(2.0 * math.pi / 365.0).cos().multiply(0.033).add(1.0)
    de = J.multiply(2.0 * math.pi / 365.0).subtract(1.39).sin().multiply(0.409)
    ws = lat.tan().multiply(de.tan()).multiply(-1.0).clamp(-1.0, 1.0).acos()
    Ra = (ws.multiply(lat.sin()).multiply(de.sin())
          .add(lat.cos().multiply(de.cos()).multiply(ws.sin()))
          .multiply(dr).multiply((24.0 * 60.0 / math.pi) * 0.0820))
    Rso = ELEV.multiply(0.00002).add(0.75).multiply(Ra)
    rs_rso = rs.divide(Rso).clamp(0.0, 1.0)
    rad = tmax.add(273.16).pow(4).add(tmin.add(273.16).pow(4)).divide(2.0).multiply(4.903e-9)
    Rn = rs.multiply(0.77).subtract(
        rad.multiply(ea.sqrt().multiply(-0.14).add(0.34)).multiply(rs_rso.multiply(1.35).subtract(0.35)).max(0))
    delta = tm.expression('4283.58 * (0.6108 * exp(17.625 * T / (T + 243.04))) / ((T + 243.04) ** 2)', {'T': tm})
    num = delta.multiply(Rn).multiply(0.408).add(
        gamma.multiply(ee.Image(900).divide(tm.add(273))).multiply(u2).multiply(vpd))
    den = delta.add(gamma.multiply(ee.Image(1).add(u2.multiply(0.34))))
    return num.divide(den).max(0).rename('eto_calc')


# =========================================================================================
# Z — estatística sobre os CSV (roda sem Earth Engine; pode rodar no seu computador)
# =========================================================================================
def parte_Z():
    log('\n[Z] estatística: descritivo, outliers, bootstrap de blocos e teste de permutação')
    log(f'   nível de significância declarado: alfa = {ALFA}; {N_BOOT} réplicas de bootstrap, '
        f'{N_PERM} permutações; unidade de reamostragem: bloco de 5 dias consecutivos')
    linhas = []
    E = ler_acumulado('K26_E_recorde.csv')
    if len(E):
        for (v, cl), g in E.groupby(['variavel', 'nome_classe']):
            for rota, gr in g.groupby('rota', dropna=False):
                x = gr.groupby('data')['pct_acima_1'].mean().sort_index().values
                lo, hi = bootstrap_blocos(x)
                mod, ext, lim = outliers_tukey(x)
                linhas.append({'tabela': 'E', 'metrica': 'pct_acima_1', 'variavel': v, 'classe': cl,
                               'grupo': rota, 'n_dias': int(np.isfinite(x).sum()),
                               'media': float(np.nanmean(x)) if len(x) else np.nan,
                               'mediana': float(np.nanmedian(x)) if len(x) else np.nan,
                               'desvio': float(np.nanstd(x, ddof=1)) if len(x) > 1 else np.nan,
                               'ic95_inf': lo, 'ic95_sup': hi, 'outliers_15iqr': mod, 'outliers_30iqr': ext,
                               'limite_inf_tukey': lim[0], 'limite_sup_tukey': lim[1]})
    CD = ler_acumulado('K26_CD_invariantes.csv')
    if len(CD):
        flags = [c for c in CD.columns if c not in ('mes', 'data', 'rota', 'classe', 'nome_classe', 'n_pix')]
        for f in flags:
            if CD[f].sum() == 0:
                continue
            for rota, gr in CD.groupby('rota', dropna=False):
                x = (gr.groupby('data')[f].sum() / gr.groupby('data')['n_pix'].sum().clip(lower=1) * 100).values
                lo, hi = bootstrap_blocos(x)
                mod, ext, lim = outliers_tukey(x)
                linhas.append({'tabela': 'CD', 'metrica': f'pct_{f}', 'variavel': f, 'classe': 'todas',
                               'grupo': rota, 'n_dias': int(np.isfinite(x).sum()),
                               'media': float(np.nanmean(x)) if len(x) else np.nan,
                               'mediana': float(np.nanmedian(x)) if len(x) else np.nan,
                               'desvio': float(np.nanstd(x, ddof=1)) if len(x) > 1 else np.nan,
                               'ic95_inf': lo, 'ic95_sup': hi, 'outliers_15iqr': mod, 'outliers_30iqr': ext,
                               'limite_inf_tukey': lim[0], 'limite_sup_tukey': lim[1]})
    if linhas:
        Z = pd.DataFrame(linhas)
        gravar(Z.round(6), 'K26_Z_estatistica.csv')
        log('\n' + Z.round(4).to_string(index=False))
    # Mann-Whitney, com a ressalva
    try:
        from scipy import stats
        if len(E):
            mw = []
            for (v, cl), g in E.groupby(['variavel', 'nome_classe']):
                a = g.loc[g['rota'] == 'ERA5'].groupby('data')['pct_acima_1'].mean().dropna().values
                b = g.loc[g['rota'] == 'GFS'].groupby('data')['pct_acima_1'].mean().dropna().values
                if len(a) >= 3 and len(b) >= 3:
                    u, p = stats.mannwhitneyu(a, b, alternative='two-sided')
                    dif, pp, na, nb = permutacao(a, b)
                    mw.append({'variavel': v, 'classe': cl, 'n_ERA5': len(a), 'n_GFS': len(b),
                               'U': float(u), 'gl_aprox': len(a) + len(b) - 2, 'p_mannwhitney': float(p),
                               'p_permutacao': pp, 'diferenca_medias': dif,
                               'significativo_alfa_005': bool(p < ALFA)})
            if mw:
                M = pd.DataFrame(mw)
                gravar(M.round(6), 'K26_Z_testes.csv')
                log('\nERA5 x GFS (pct acima do recorde + 1). Mann-Whitney bilateral e permutação exata:')
                log(M.round(5).to_string(index=False))
                log('   RESSALVA: dias consecutivos são autocorrelacionados, logo o n efetivo é menor que o '
                    'n de dias. O p do Mann-Whitney é otimista; o IC do bootstrap de blocos é a referência.')
    except Exception as e:
        log(f'   scipy indisponível ({e}); fica o bootstrap e a permutação.')


def fechar(T0):
    if 'Z' in PARTES:
        try:
            parte_Z()
        except Exception:
            log('   parte Z falhou:\n' + traceback.format_exc())
    log('\n' + '=' * 104)
    log('RESULTADO K26')
    log('=' * 104)
    for r in RESULTADOS:
        log(f'   {r["item"]:<4} {r["status"]:<8} {r["titulo"]}')
    if RESULTADOS:
        gravar(pd.DataFrame(RESULTADOS), 'K26_RESUMO.csv')
    falhas = [r for r in RESULTADOS if r['status'] == 'FALHA']
    atencao = [r for r in RESULTADOS if r['status'] == 'ATENCAO']
    quebradas = [r for r in RESULTADOS if r['status'] == 'FALHOU']
    if quebradas:      # parte que não terminou não pode virar "tudo dentro dos critérios"
        log(f'\n   ⛔ {len(quebradas)} parte(s) não terminaram ({", ".join(r["item"] for r in quebradas)}): '
            f'o resultado está INCOMPLETO. Me envie o zip.')
    elif falhas:
        log(f'\n   ❌ {len(falhas)} falha(s) e {len(atencao)} ponto(s) de atenção. Me envie o zip.')
    elif atencao:
        log(f'\n   ⚠️ Nenhuma falha, {len(atencao)} ponto(s) de atenção. Me envie o zip.')
    else:
        log('\n   ✅ Tudo dentro dos critérios declarados nos dias varridos.')
    log(f'\nTempo: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine (trava de somente leitura).')
    if PASTA and 'SIMULACAO_' in os.path.basename(PASTA):
        log('')
        for _ in range(3):
            log('⚠️  ISTO FOI UMA SIMULAÇÃO. NENHUM NÚMERO ACIMA DESCREVE O SAB.  ⚠️')


if __name__ == '__main__':          # importar o arquivo NÃO roda nada (é assim que o teste offline o lê)
    try:
        principal()
    except Exception:
        log(traceback.format_exc())
        raise
    finally:
        # só empacota se houver CSV: um zip vazio anunciado como entrega é pior que nenhum zip
        tem_csv = os.path.isdir(PASTA) and any(f.endswith('.csv') for f in os.listdir(PASTA))
        if tem_csv:
            z = shutil.make_archive(PASTA, 'zip', PASTA)
            log(f'📦 {z}  <- me envie este zip')
            log('   Para continuar outro mês/ano: suba os CSV deste zip para /content/K26_acumulado/ '
                'antes de rodar de novo.')
            try:
                from google.colab import files
                files.download(z)
            except Exception:
                pass
        elif os.path.isdir(PASTA):
            log('Nenhum CSV foi produzido, então não há zip para enviar. Resolva o erro acima e rode '
                'de novo.')
