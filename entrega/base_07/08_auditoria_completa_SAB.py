# =========================================================================================
# AUDITORIA COMPLETA DO SISTEMA SAB (SOMENTE LEITURA) - versão A3 (20/10/2026), REVISÃO FINAL DE 22/10/2026
#   (seção F corrigida e critério teto_razao_K11 na D14; CHANGELOG_REVISAO_K9A.md, seções 10 e 12)
#
# MUDANÇAS V4 (20/10/2026) - pacote SAB v4; cada trecho alterado ou novo leva "# [V4 <ID>]"
#   [V4 M08-01] Log: pasta com segundos; LOG_COMPLETO.txt aberto com 'w'; resumo gravado sempre (try/finally),
#               mesmo se a execução for interrompida, com a seção em curso
#   [V4 M08-02/M08-03] F2, F3 e F5 com as datas do 03 v4 (só GFS v16: rodadas 00Z desde 2021-03-23 em todas as
#               faixas). O F5 conta só as horas 0 < x <= 120, acha a transição dia a dia (só metadados) e relata
#               as datas reais; OK quando o 03 começa depois delas
#   [V4 M08-04/M08-05] D10/D11: contagens unweighted; o D10 exige a máscara do SAB_2025_12_31 (presença e fração)
#               em todos os dias amostrados (até 50 coordenadas diferentes); dias V1.3/V1.4 diferentes = INFO,
#               outras versões = ATENÇÃO
#   [V4 M08-06] Seção E: percentis exatos por amostragem (sorteio de 6.000 pontos, como a J4); acima5 igual
#   [V4 M08-08] ACEITOS: C7, E4, H2, H4 e I1 passam de ATENÇÃO para INFO, com o motivo no log
#   [V4 NOVO]   Seções novas, somente leitura: D14 (dias de 2026 e motor V1.5; M08-11), E6 (matriz GFS V2.1;
#               M08-10), H5 (RONI_CPC_v6 x CPC; M08-09), Q1 (máscara de qualidade), J1 (classes de pixel),
#               J3 (homônimos no GAUL) e J5 (Tmax nacional de 2026). Constantes RODAR_* desligam as mais demoradas
#   [V4]        SECOES_A_RODAR aceita a letra ('D' roda D e D14) ou o código ('D14')
#   [V4 revisão] Depois das auditorias independentes A e B (20/10/2026):
#               - D10 (A-03): dias GFS V1.5 com cobertura CONTIDA na canônica (só faltam pixels) = INFO
#               - Q1 (B-02): a grade gravada aceita a origem própria do asset (deslocada por pixels inteiros)
#               - H5 (B-06): sem system:time_start em nenhuma estação = ATENÇÃO (o painel recalcula a data);
#                 a chave do painel ordena por data_ms
#               - B2 lista também SAB_MASCARA_QUALIDADE; J5_CSV_ANTERIOR = /content/J5_previsao_anterior.csv
#   [V4.1] Depois das auditorias K e K1d corrigida (20/10/2026):
#               - Q1 (K1a): pixel B da máscara igual ao BR-DWGD no dia conferido é coincidência e não conta como
#                 diferença (é mostrado à parte); referências da K1d: classe 3 perto de 48, classe 4 perto de 1.060
#               - J1 (K1a): histórico INFO com C = 1.109, A + B = 70.568 e B entre 194 e 205 (antes exigia B = 204)
#               - Q1 (revisão V41): confere também dias_classes e acusa mais de 20 coincidências B -> A no dia
#
# A3: teste da radiação sem a hora 0 da previsão (que não tem a banda); F3 ignora o mês corrente;
#     F5 localiza as datas exatas em que o GFS passou a ter 384 h e saídas de 3 em 3 h após 240 h
# A2: nomes de banda do teste da convenção do dia sem '+' (o Earth Engine recusava 'era5tx_D+1');
#     opção SECOES_A_RODAR para repetir só algumas seções
#
# OBJETIVO
#   Medir, nos dados reais do Earth Engine, tudo o que até agora foi deduzido só pelo código,
#   antes de decidir qualquer mudança. Nada é criado, apagado, renomeado ou exportado: todas
#   as funções de escrita do Earth Engine são bloqueadas logo depois da conexão.
#
# O QUE É AUDITADO (cada item vira uma linha no resumo final)
#   A  Ambiente: conexão, tarefas na fila, falhas recentes e consumo de EECU do mês
#   B  Assets do projeto: o que existe, tipo, quantidade de imagens
#   C  BR-DWGD: datas, horário, lacunas, tipos de pixel, valores brutos (-32768 e zero),
#      faixas físicas depois da escala, e a CONVENÇÃO DO DIA DE CHUVA (teste com IMERG e ERA5)
#   D  SAB_V1: inventário 1961-hoje, versões por ano, coleção temporária, fidelidade dos dias
#      definitivos ao BR-DWGD, coerência física, 2026 x climatologia, e o efeito da reamostragem
#      bilinear na umidade do solo (antecipa o critério de ±2% da etapa 5a)
#   E  Matrizes: SICSB_1986_2025, SICSB_SOLO_2015_2025, SICSB_MATRIZ_GFS (fatores, cortes no
#      teto de 5, cobertura) e resolução efetiva da matriz GFS V1
#   F  GFS: time_start x creation_time, horas de previsão por época (datas usadas no script 03),
#      disponibilidade das rodadas 00Z mês a mês e natureza da radiação (instantânea ou média)
#   G  ERA5-Land: última data e alinhamento da grade com o SAB
#   H  OISST e RONI: últimos dias, status, retângulos geodésicos x planos, asset RONI antigo x CPC
#   I  Baselines: imagens e versões nas 4 coleções
#   [V4] D14 dias de 2026 (V1.5, contíguos, rodada 00Z, Confianca_Prazo, emenda ERA5 -> GFS);
#        E6 matriz GFS V2.1; H5 RONI_CPC_v6 x CPC; Q1 máscara de qualidade; J1 classes de pixel do histórico;
#        J3 nomes de estados repetidos no GAUL; J5 Tmax nacional dos dias de 2026 (recorde e emenda)
#
# COMO RODAR NO COLAB
#   1. Cole este arquivo inteiro numa célula e rode (Ctrl+Enter). Tempo típico: cerca de 15 minutos.
#   2. Não precisa editar nada. Para uma rodada mais curta, mude RAPIDO para True (seção 0).
#   3. No fim, o Colab baixa auditoria_SAB_<data>.zip com o log completo, o resumo e as tabelas.
#      Se o download não abrir, use o painel Arquivos (ícone de pasta, à esquerda).
#   4. Envie o .zip (ou o arquivo LOG_COMPLETO.txt) para a análise.
# =========================================================================================

import calendar
import io
import json
import math
import os
import re                          # [V4 M08-09] formato da chave do painel no H5
import shutil
import time
import traceback
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

# =========================================================================
# 0. CONFIGURAÇÃO (não precisa mudar nada)
# =========================================================================
PROJETO = 'clima-492922'
RAPIDO = False                     # True: amostras menores (cerca de 1/3 do tempo)
# Seções a rodar. Vazio = todas. Exemplo para repetir só o que faltou: SECOES_A_RODAR = ['C', 'E', 'F', 'G', 'H', 'I']
# (a seção D é necessária para D-dependentes; C, E, F, G, H e I são independentes)
SECOES_A_RODAR = []
# [V4] Seções novas (somente leitura). As mais demoradas podem ser desligadas aqui.
RODAR_D14 = True                   # dias de 2026 e motor V1.5 (cerca de 0,5 min)
RODAR_E6 = True                    # matriz GFS V2.1 (cerca de 1 min)
RODAR_Q1 = True                    # máscara de qualidade (cerca de 0,5 min)
RODAR_J1 = True                    # classes de pixel em 3 dias do histórico (cerca de 0,5 min)
RODAR_J5 = True                    # Tmax nacional dos dias de 2026, uma consulta por mês (cerca de 2 a 4 min)
# [V4 J5] Opcional: J5_tmax_2026.csv de uma execução anterior (desta auditoria ou da J), para comparar a previsão
# GFS com o ERA5 nas datas que já viraram ERA5. O roteiro (Parte 4) manda enviar esse CSV ao Colab com o nome
# abaixo; se o arquivo não existir, a comparação é só pulada (INFO).
J5_CSV_ANTERIOR = '/content/J5_previsao_anterior.csv'

RAIZ = f'projects/{PROJETO}/assets'
SAB = f'{RAIZ}/SAB_V1'
SAB_TMP = f'{RAIZ}/SAB_V1_TMP'
CLIMA = f'{RAIZ}/SICSB_1986_2025'
SOLO = f'{RAIZ}/SICSB_SOLO_2015_2025'
GFS_V1 = f'{RAIZ}/SICSB_MATRIZ_GFS'
GFS_V2 = f'{RAIZ}/SICSB_MATRIZ_GFS_V2'
RONI_ANTIGO = f'{RAIZ}/RONI_Calibrado_Sazonal_1950_1980'
RONI_NOVO = f'{RAIZ}/RONI_CPC_v6'
BASELINES = f'{RAIZ}/Baselines'
ASSET_MASCARA = f'{RAIZ}/SAB_MASCARA_QUALIDADE'          # [V4 Q1] gerado pelo 01
BR_DWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
GFS = 'NOAA/GFS0P25'
OISST = 'NOAA/CDR/OISST/V2_1'
IMERG_OPCOES = ['NASA/GPM_L3/IMERG_V07', 'NASA/GPM_L3/IMERG_V06']
URL_RONI_CPC = 'https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt'

CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
DIAS_HISTORICO = 23741             # 01/01/1961 a 31/12/2025
FATOR_MAX = 5.0
UMIDADE_MAX = 0.9

# Escala e offset do BR-DWGD (metadados do asset; os mesmos do motor)
ESCALA_BR = {'pr': (0.00686666, 225.0), 'Tmax': (0.00106815, 15.0), 'Tmin': (0.00106815, 15.0),
             'RH': (0.39370079, -0.393701), 'u2': (0.05905512, -0.059055),
             'Rs': (0.15708661, -0.057087), 'ET': (0.05118110, -0.0511811)}
BR_PARA_SAB = {'pr': 'pr_mm', 'Tmax': 'tmax_C', 'Tmin': 'tmin_C', 'RH': 'RH', 'u2': 'u2',
               'Rs': 'rs', 'ET': 'et_potencial'}

BANDAS_SAB = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2',
              'tsolo_C', 'tfolha_C', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm',
              'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
NOMES_ANTIGOS = ['precipitation_mm', 'temp_max_C', 'temp_min_C', 'relative_humidity_pct',
                 'et_potential_mm', 'et_actual_mm', 'vpd_kpa', 'solar_radiation_mj_m2',
                 'wind_speed_m_s', 'soil_temperature_C', 'skin_temperature_C', 'transpiration_mm',
                 'surface_runoff_mm', 'subsurface_runoff_mm', 'soil_moisture_0_5cm_m3_m3',
                 'soil_moisture_0_100cm_m3_m3']

PONTOS = [
    ('Pato Branco-PR', -26.23, -52.67), ('Curitiba-PR', -25.43, -49.27), ('Londrina-PR', -23.31, -51.16),
    ('Porto Alegre-RS', -30.03, -51.23), ('Passo Fundo-RS', -28.26, -52.41), ('Chapeco-SC', -27.10, -52.62),
    ('Campo Grande-MS', -20.47, -54.62), ('Rio Verde-GO', -17.80, -50.93), ('Sorriso-MT', -12.55, -55.71),
    ('Brasilia-DF', -15.79, -47.88), ('Uberaba-MG', -19.75, -47.93), ('Barreiras-BA', -12.15, -45.00),
    ('Petrolina-PE', -9.39, -40.50), ('Quixada-CE', -4.97, -39.02), ('Paragominas-PA', -3.00, -47.35),
    ('Manaus-AM', -3.10, -60.02), ('Porto Velho-RO', -8.76, -63.90), ('Balsas-MA', -7.53, -46.04),
]

# Amostras de dias
PASSO_ANOS = 8 if RAPIDO else 4
DIAS_AMOSTRA_HIST = sorted({f'{a}-{m:02d}-15' for a in range(1961, 2026, PASSO_ANOS) for m in (1, 7)}
                           | {'1961-01-01', '1990-12-31', '2025-12-31'})
PERIODOS_CHUVA = ([('2019-01-01', '2019-03-31')] if RAPIDO else
                  [('2019-01-01', '2019-03-31'), ('2019-10-01', '2019-12-31')])
MAX_PONTOS_CHUVA = 30 if RAPIDO else 60
MESES_SOLO_2025 = (1, 7) if RAPIDO else (1, 3, 5, 7, 9, 11)

# [V4] Contrato do pacote v4 (SPEC_V4.md) e limiares das seções novas
INICIO_RODADAS_03 = '2021-03-23'   # [V4 M08-03] 03 v4: só GFS v16 (entrou em 22/03/2021 12 UTC), todas as faixas
AMOSTRA_PERCENTIS = 6000           # [V4 M08-06] pontos sorteados por mês (cerca de 2.500 caem no Brasil, como na J4)
REGIAO_AMPLA_COORDS = [-75.0, -35.0, -28.0, 6.5]   # [V4] retângulo folgado: contagem unweighted vai pelo centro
RECORDE_TMAX_BR = 44.8             # [V4 J5] recorde do INMET: Araçuaí-MG, 19/11/2023
SALTO_EMENDA_MAX_C = 2.0           # [V4 J5] salto máximo aceito na Tmax máxima nacional entre o último ERA5 e o 1º GFS
Q1_DIA = '2013-07-15'              # [V4 Q1] dia do histórico usado para recalcular as classes
J1_DIAS = ('1961-01-15', '1990-12-31', '2025-12-31')   # [V4 J1]
J1_ESPERADO = {'B': 204, 'C': 1109, 'AB': 70568}      # [V4 J1] auditoria J; [V4.1 K1a] A + B constante (K1a, 65 anos)
J1_TOL_B = 10                      # [V4.1 K1a] B pode cair até ~7,5 pixels num dia por coincidência (lagoas do RS)
J1_C_FORA_APROX = 1060             # [V4.1 K1d] classe 4: C total menos os 48 com centro no Brasil (antes ~880)
K1D_C_DENTRO = 48                  # [V4.1 K1d] classe 3: pixels C com o centro no polígono do Brasil
DIAS_CLASSES_Q1 = '2001-01-15,1961-01-15,1981-07-01,2017-07-15,2025-01-15'   # [V4.1] propriedade dias_classes do 01
Q1_MAX_COINC = 20                  # [V4.1 revisão V41-07] a K1a mediu até ~8 coincidências B -> A num dia
ORDEM_TRIMESTRES = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']
VERSOES_GFS_SAB = ('provisoria_gfs', 'provisoria_gfs_incompleta', 'falha_latencia_gfs')
FAIXAS_V21 = ('L1', 'L2a5', 'L6a10', 'L11a15')
VARS_V21 = ('pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs')
CONTRATO_V21 = {'versao_matriz': 'V2.1', 'modelo_gfs': 'GFS v16', 'inicio_rodadas': '2021-03-23',
                'fim_dias': '2025-12-31', 'leads_L1': '1', 'leads_L2a5': '2,3,4,5', 'leads_L6a10': '6,7,8,9,10',
                'leads_L11a15': '11,12,13,14,15', 'metodo_pr': 'soma_blocos_6h', 'metodo_rs': 'media_blocos_6h',
                'janela': '(00Z,24Z] UTC do dia previsto; rodada 00Z de D-(L-1)'}
# [Revisão 20/10/2026] Método da Tmax/Tmin dos dias GFS: tem de ser o mesmo METODO_TEMP_GFS do 05b
METODO_TEMP_GFS_ESPERADO = 'variancia'
# [Revisão K9A] Método da UR e da radiação dos dias GFS: tem de ser o mesmo METODO_UR_RS_GFS do 05b
METODO_UR_RS_GFS_ESPERADO = 'variancia'
# [K11, 22/10/2026] Teto da razão dos desvios da Tmax/Tmin dos dias GFS: 2.0 nos prazos 1 a 5 e 1.0 do 6 em
# diante (RAZAO_DESVIO_MAX e RAZAO_DESVIO_MAX_LONGO do 05b). Dia sem a propriedade conta como 2.0 (antes da K11).
TETO_RAZAO_CURTO_ESPERADO = 2.0
TETO_RAZAO_LONGO_ESPERADO = 1.0
CONTRATO_V15 = {
    'gfs': {'janela_chuva_utc': '00-24', 'fonte': 'NOAA/GFS0P25 (rodada 00Z)', 'matriz_gfs': 'SICSB_MATRIZ_GFS_V2 V2.1',
            'metodo_temp_gfs': METODO_TEMP_GFS_ESPERADO, 'metodo_ur_rs_gfs': METODO_UR_RS_GFS_ESPERADO},
    'era5': {'janela_chuva_utc': '00-24', 'fonte': 'ECMWF/ERA5_LAND/DAILY_AGGR'},
    'definitiva': {'janela_chuva_utc': '12-12 (12 UTC D-1 a 12 UTC D)', 'fonte': 'BR-DWGD (ERA5 só onde falta)'},
}
# [V4 M08-08] ATENÇÕES já registradas e aceitas: viram INFO, com o motivo no log e no resumo
ACEITOS = {
    'C7': 'convenção do dia de chuva do BR-DWGD (12 UTC de D-1 a 12 UTC de D) registrada na tese',
    'E4': 'mede a matriz GFS V1, substituída pela V2.1 (ver E6)',
    'H2': 'testa a geometria do RONI antigo; o painel usa o RONI_CPC_v6 (ver H5)',
    'H4': 'asset RONI antigo, substituído pelo RONI_CPC_v6 (ver H5)',
    'I1': 'normais e limiares B1.1 gravados são o estado esperado',
}

# =========================================================================
# 1. LOG, ACHADOS E UTILITÁRIOS
# =========================================================================
AGORA = datetime.now(timezone(timedelta(hours=-3)))
PASTA = f'/content/auditoria_SAB_{AGORA:%Y%m%d_%H%M%S}' if os.path.isdir('/content') else \
        f'auditoria_SAB_{AGORA:%Y%m%d_%H%M%S}'          # [V4 M08-01] com segundos: duas execuções não se misturam
os.makedirs(PASTA, exist_ok=True)
ARQ_LOG = os.path.join(PASTA, 'LOG_COMPLETO.txt')
open(ARQ_LOG, 'w', encoding='utf-8').close()          # [V4 M08-01] log novo a cada execução
ACHADOS = []
ORDEM_STATUS = {'ERRO': 0, 'ATENÇÃO': 1, 'NÃO EXECUTADO': 2, 'INFO': 3, 'OK': 4}


def log(*partes):
    texto = ' '.join(str(p) for p in partes)
    print(texto)
    with open(ARQ_LOG, 'a', encoding='utf-8') as f:
        f.write(texto + '\n')


def log_tabela(df, titulo=None, max_linhas=200):
    if titulo:
        log(f'\n   {titulo}')
    if df is None or len(df) == 0:
        log('   (vazio)')
        return
    with pd.option_context('display.width', 250, 'display.max_columns', 60, 'display.max_colwidth', 60):
        texto = df.head(max_linhas).to_string()
    for linha in texto.splitlines():
        log('   ' + linha)
    if len(df) > max_linhas:
        log(f'   ... ({len(df) - max_linhas} linhas a mais no CSV)')


def salvar_csv(df, nome):
    if df is not None and len(df):
        df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=True, encoding='utf-8-sig')


def achado(codigo, status, titulo, resultado, significado='', acao=''):
    status_original = status
    status, motivo = rebaixar_aceito(codigo, status, CONTEXTO)          # [V4 M08-08]
    if motivo:
        significado = f'{significado} [ATENÇÃO aceita: {motivo}]'.strip()
    ACHADOS.append({'codigo': codigo, 'status': status, 'titulo': titulo, 'resultado': resultado,
                    'significado': significado, 'acao_sugerida': acao, 'status_original': status_original})
    simbolo = {'OK': '✅', 'ATENÇÃO': '⚠️', 'ERRO': '❌', 'INFO': 'ℹ️', 'NÃO EXECUTADO': '⏭️'}[status]
    log(f'{simbolo} [{codigo}] {titulo}: {resultado}')
    if significado:
        log(f'      significado: {significado}')
    if acao:
        log(f'      ação sugerida: {acao}')


def ms_para_txt(ms, horas=True):
    if ms is None:
        return 'N/A'
    d = datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc)
    return d.strftime('%Y-%m-%d %H:%M UTC' if horas else '%Y-%m-%d')


def data_ms(d):
    return int(datetime.strptime(d, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp() * 1000)


def centro_pixel(lat, lon):
    dx, x0 = TRANSFORM[0], TRANSFORM[2]
    dy, y0 = -TRANSFORM[4], TRANSFORM[5]
    return (y0 - (math.floor((y0 - lat) / dy) + 0.5) * dy,
            x0 + (math.floor((lon - x0) / dx) + 0.5) * dx)


PONTOS_CP = [(n, *centro_pixel(la, lo)) for n, la, lo in PONTOS]

TRANSITORIOS = ('Too many concurrent', 'Internal error', 'Service Unavailable', '503', '429',
                'deadline', 'Deadline', 'Connection', 'temporarily')


def gi(obj, rotulo='', tentativas=4):
    """getInfo com novas tentativas para erros transitórios do servidor."""
    for t in range(tentativas):
        try:
            return obj.getInfo()
        except Exception as e:
            msg = str(e)
            if t < tentativas - 1 and any(k in msg for k in TRANSITORIOS):
                espera = 10 * (t + 1)
                log(f'   ↻ {rotulo}: erro transitório ({msg[:80]}); nova tentativa em {espera} s')
                time.sleep(espera)
                continue
            raise


# =========================================================================
# 1b. [V4] REGRAS PURAS DAS MUDANÇAS V4 (sem Earth Engine; testadas em testes/teste_08.py)
# =========================================================================
def tem_384(h):
    """[V4 M08-02] Rodada com 384 h e saída horária de 1 a 120 h. Só contam as horas 0 < x <= 120: algumas
    rodadas têm a hora 0 e outras não (o teste antigo contava a hora 0 e falhava nas rodadas com ela)."""
    return bool(h) and max(h) >= 384 and set(range(1, 121)) <= set(h)


def tres_apos_240(h):
    """[V4 M08-02] Rodada com saídas de 3 em 3 h de 243 a 384 h."""
    return bool(h) and set(range(243, 385, 3)) <= set(h)


def detectar_transicao(dias, ok, janela=30, fracao=0.9):
    """[V4 M08-02] Primeiro dia em que o teste passa a valer de vez: vale no dia, não valia no dia anterior e vale
    em pelo menos `fracao` dos `janela` dias a partir dele. Dia sem rodada 00Z conta como 'não vale'.
    Devolve (dia ou None, nota)."""
    ok = [bool(x) for x in ok]
    if not ok:
        return None, 'nenhum dia consultado'
    if ok[0] and np.mean(ok[:janela]) >= fracao:
        return None, f'já valia no primeiro dia da janela ({dias[0]})'
    for i in range(1, len(ok)):
        if ok[i] and not ok[i - 1] and np.mean(ok[i:i + janela]) >= fracao:
            return dias[i], ''
    return None, 'transição não encontrada na janela'


def status_f5(d384, d3h, inicio_03):
    """[V4 M08-03] OK se o 03 começa depois das duas mudanças de estrutura (o período v16 é decisão do usuário);
    ATENÇÃO se começa antes de alguma; INFO se alguma data não foi localizada."""
    if not d384 or not d3h:
        return 'INFO'
    return 'OK' if max(d384, d3h) <= inicio_03 else 'ATENÇÃO'


def rebaixar_aceito(codigo, status, contexto=None):
    """[V4 M08-08] ATENÇÃO de item listado em ACEITOS vira INFO; devolve (status, motivo). ERRO nunca é rebaixado.
    O I1 só é aceito se as coleções das Baselines tiverem apenas a versão B1.1."""
    if status != 'ATENÇÃO' or codigo not in ACEITOS:
        return status, ''
    if codigo == 'I1' and not set((contexto or {}).get('versoes_baselines') or ()) <= {'B1.1'}:
        return status, ''
    return 'INFO', ACEITOS[codigo]


def status_d10(linhas):
    """[V4 M08-04; revisão A-03] linhas: dicts com 'alg', 'versao', 'n_dif', 'so_no_dia', 'so_no_SAB_2025_12_31' e
    'fracao_de_mascara_diferente' (pixels com máscara diferente da do SAB_2025_12_31). OK sem diferença.
    INFO: (a) dias V1.3/V1.4 (motor anterior à V1.5: cerca de 4 pixels a mais nos dias GFS); (b) dias V1.5 de
    previsão GFS cuja cobertura está CONTIDA na canônica (só faltam pixels: a calibração vem da pegada do BR-DWGD
    dilatada 2 pixels e ilhas preenchidas pelo ERA5 podem ficar sem valor). ATENÇÃO: qualquer outra diferença
    (pixel fora da canônica, fração de máscara diferente, dia histórico, ERA5 ou definitivo V1.5)."""
    status = 'OK'
    for x in linhas:
        if not (x.get('n_dif') or 0):
            continue
        alg = str(x.get('alg'))
        contida = not (x.get('so_no_dia') or 0) and not (x.get('fracao_de_mascara_diferente') or 0)
        if alg in ('V1.3', 'V1.4') or (alg == 'V1.5' and x.get('versao') in VERSOES_GFS_SAB and contida):
            status = 'INFO'
        else:
            return 'ATENÇÃO'
    return status


def dias_acima_recorde(t, limite=None):
    """[V4 J5] Dias com Tmax máxima nacional acima do recorde do INMET: lista de (dia, valor)."""
    limite = RECORDE_TMAX_BR if limite is None else limite
    s = pd.to_numeric(t['tmax_max'], errors='coerce')
    return [(d, round(float(v), 2)) for d, v in s[s > limite].sort_index().items()]


def salto_emenda(t):
    """[V4 J5] Salto da Tmax máxima nacional entre o último dia provisoria_era5 e o primeiro dia GFS depois dele.
    t: DataFrame indexado pelo dia (AAAA-MM-DD), com 'versao' e 'tmax_max'. None se não houver emenda."""
    t = t.sort_index()
    era = t[t['versao'] == 'provisoria_era5']
    gfs = t[t['versao'].isin(VERSOES_GFS_SAB)]
    if era.empty or gfs.empty:
        return None
    d_era = era.index.max()
    depois = gfs[gfs.index > d_era]
    if depois.empty:
        return None
    d_gfs = depois.index.min()
    a, b = float(t.loc[d_era, 'tmax_max']), float(t.loc[d_gfs, 'tmax_max'])
    return {'dia_era5': d_era, 'dia_gfs': d_gfs, 'tmax_era5': a, 'tmax_gfs': b, 'salto': round(b - a, 2),
            'dias_entre': (pd.Timestamp(d_gfs) - pd.Timestamp(d_era)).days,
            'atencao': abs(b - a) > SALTO_EMENDA_MAX_C}


def comparar_gfs_x_era5(anterior, atual):
    """[V4 J5] Datas que eram previsão GFS numa execução anterior e hoje são ERA5 (ou definitivas): valores das
    duas fontes e a diferença GFS - ERA5 por dia. anterior e atual: DataFrames indexados pelo dia."""
    a = anterior[anterior['versao'].isin(VERSOES_GFS_SAB)]
    b = atual[atual['versao'].isin(('provisoria_era5', 'definitiva'))]
    comuns = sorted(set(a.index) & set(b.index))
    out = pd.DataFrame(index=pd.Index(comuns, name='dia'))
    for c in ('tmax_max', 'tmax_media', 'pct_acima40', 'pct_acima42'):
        if c in a.columns and c in b.columns:
            out[f'{c}_gfs'] = pd.to_numeric(a.loc[comuns, c], errors='coerce').values
            out[f'{c}_era5'] = pd.to_numeric(b.loc[comuns, c], errors='coerce').values
            out[f'dif_{c}'] = (out[f'{c}_gfs'] - out[f'{c}_era5']).round(2)
    return out


def confianca_esperada(dia_ms, rodada_ms):
    """[V4 D14] Confianca_Prazo do contrato V1.5: prazo L de 1 a 5 'alta', de 6 a 10 'media', 11 em diante 'baixa'.
    O dia L termina 24*L h depois da criação da rodada (a mesma conta da faixa_prazo do motor)."""
    L = math.ceil((dia_ms + 86400000 - rodada_ms) / 86400000.0 - 1e-9)
    return 'alta' if L <= 5 else ('media' if L <= 10 else 'baixa')


def teto_razao_esperado(dia_ms, rodada_ms):
    """[K11] Teto da razão dos desvios da Tmax/Tmin do dia GFS: 2.0 nos prazos 1 a 5 e 1.0 do 6 em diante
    (a mesma conta de prazo da confianca_esperada)."""
    L = math.ceil((dia_ms + 86400000 - rodada_ms) / 86400000.0 - 1e-9)
    return TETO_RAZAO_LONGO_ESPERADO if L >= 6 else TETO_RAZAO_CURTO_ESPERADO


def ultimo_dia_continuo_era5(datas):
    """[Correção 21/10/2026, 18h] A mesma regra do motor V1.5 (ultimo_dia_continuo): datas = conjunto de dias
    'AAAA-MM-DD' com imagem ERA5-Land; devolve (último dia sem lacuna, dias que faltam até o último publicado)."""
    ordenadas = sorted(datas)
    todos = [x.strftime('%Y-%m-%d') for x in pd.date_range(ordenadas[0], ordenadas[-1])]
    faltando = [x for x in todos if x not in datas]
    if not faltando:
        return ordenadas[-1], []
    return (pd.Timestamp(faltando[0]) - pd.Timedelta(days=1)).strftime('%Y-%m-%d'), faltando


def checar_d14(inv, ultimo_era5):
    """[V4 M08-11] Critérios dos dias de 2026. inv: DataFrame com dia (AAAA-MM-DD), versao, alg, rodada (ms; <= 0
    sem rodada), Confianca_Prazo, fonte, janela_chuva_utc, matriz_gfs, metodo_temp_gfs e metodo_ur_rs_gfs. ultimo_era5: último dia do ERA5-Land (G1).
    Devolve {critério: (ok, detalhe)}; ok None quando o critério não se aplica."""
    t = inv.sort_values('dia').reset_index(drop=True)
    res = {'todos_V1.5': (set(t['alg']) == {'V1.5'}, f'{t["alg"].value_counts().to_dict()}')}
    dias = pd.to_datetime(t['dia'])
    faltam = sorted(set(pd.date_range('2026-01-01', dias.max())) - set(dias))
    dup = sorted(set(t['dia'][t['dia'].duplicated()]))
    res['datas_contiguas'] = (not faltam and not dup and t['dia'].min() == '2026-01-01',
                              f'de {t["dia"].min()} a {t["dia"].max()}; {len(faltam)} faltando '
                              f'{[d.strftime("%Y-%m-%d") for d in faltam[:5]]}; {len(dup)} duplicado(s) {dup[:5]}')
    gfs = t[t['versao'].isin(VERSOES_GFS_SAB)]
    rod = gfs['rodada'].astype('int64')
    fora = gfs[(rod <= 0) | (rod % 86400000 != 0)]
    res['rodada_00Z'] = (len(gfs) > 0 and fora.empty,
                         f'{len(gfs)} dia(s) GFS; rodada(s) {sorted(ms_para_txt(r) for r in set(rod) if r > 0)[:3]}; '
                         f'sem rodada 00Z: {fora["dia"].tolist()[:5]}')
    alvo = gfs[(gfs['alg'] == 'V1.5') & (gfs['versao'] != 'falha_latencia_gfs')]
    errados = [(d, c, confianca_esperada(data_ms(d), int(r)) if r > 0 else None)
               for d, c, r in zip(alvo['dia'], alvo['Confianca_Prazo'], alvo['rodada'])]
    errados = [x for x in errados if x[1] != x[2]]
    res['Confianca_Prazo'] = ((not errados) if len(alvo) else None,
                              f'{len(alvo)} dia(s) GFS V1.5; divergentes (dia, gravado, esperado): {errados[:5]}')
    # [K11] teto da razão dos desvios da Tmax/Tmin conforme o prazo (dia sem a propriedade conta como 2.0)
    def _teto(x):
        try:
            v = float(x)
        except (TypeError, ValueError):
            return TETO_RAZAO_CURTO_ESPERADO
        return TETO_RAZAO_CURTO_ESPERADO if math.isnan(v) else v
    gravados = alvo['teto_razao_temp_gfs'] if 'teto_razao_temp_gfs' in alvo else pd.Series(2.0, index=alvo.index)
    errados_t = [(d, _teto(g), teto_razao_esperado(data_ms(d), int(r)) if r > 0 else None)
                 for d, g, r in zip(alvo['dia'], gravados, alvo['rodada'])]
    errados_t = [x for x in errados_t if x[2] is None or abs(x[1] - x[2]) > 1e-9]
    res['teto_razao_K11'] = ((not errados_t) if len(alvo) else None,
                             f'{len(alvo)} dia(s) GFS V1.5; teto da razão Tmax/Tmin divergente (dia, gravado, '
                             f'esperado: 2.0 nos prazos 1-5, 1.0 do 6 em diante): {errados_t[:5]}')
    ultimo = t['dia'].max()
    ruins = t[t['versao'].isin(('provisoria_gfs_incompleta', 'falha_latencia_gfs')) & (t['dia'] < ultimo)]
    res['incompleta_so_no_ultimo_dia'] = (ruins.empty, f'antes de {ultimo}: {ruins[["dia", "versao"]].values.tolist()[:5]}')
    era = t[t['versao'] == 'provisoria_era5']
    ult_era = era['dia'].max() if len(era) else None
    prim_gfs = gfs['dia'].min() if len(gfs) else None
    seguinte = bool(ult_era and prim_gfs and (pd.Timestamp(prim_gfs) - pd.Timestamp(ult_era)).days == 1)
    res['emenda_ERA5_GFS'] = (seguinte and ult_era == ultimo_era5,
                              f'último dia ERA5 no SAB {ult_era}; último dia do ERA5-Land (G1) {ultimo_era5}; '
                              f'primeiro dia GFS {prim_gfs}')
    rota = t['versao'].map(lambda v: 2 if v in VERSOES_GFS_SAB else (1 if v == 'provisoria_era5' else 0))
    res['ordem_das_rotas'] = (bool(rota.is_monotonic_increasing), 'definitiva -> provisoria_era5 -> GFS, sem mistura')
    v15 = t[t['alg'] == 'V1.5']
    prob = []
    for _, r in v15.iterrows():
        tipo = 'gfs' if r['versao'] in VERSOES_GFS_SAB else ('era5' if r['versao'] == 'provisoria_era5' else 'definitiva')
        prob += [f'{r["dia"]} {k}={r.get(k)!r}' for k, v in CONTRATO_V15[tipo].items() if r.get(k) != v]
    res['propriedades_contrato_V1.5'] = ((not prob) if len(v15) else None, f'{len(prob)} divergência(s) {prob[:5]}')
    return res


def status_d14(res, inv):
    """[V4 M08-11] INFO antes da etapa 5b (nenhum dia V1.5: 'aguardando motor V1.5'); depois, OK só com todos os
    critérios atendidos."""
    if 'V1.5' not in set(inv['alg']):
        return 'INFO'
    return 'OK' if all(v[0] is not False for v in res.values()) else 'ATENÇÃO'


def avaliar_roni(novo, cpc, chaves=(), n_recentes=3):
    """[V4 M08-09] RONI_CPC_v6 (novo: ano, mes, Trimestre, RONI, RONI_2c, t_ms e, se gravados, data_ms e chave_join)
    x RONI.ascii.txt do CPC (cpc: ano, Trimestre, RONI_2c). chaves: [(ano, mes, chave montada no servidor como o
    painel)]. Revisão do CPC nas
    `n_recentes` estações mais novas é ATENÇÃO ('rode o 02'); nas antigas, ERRO. Devolve (status, problemas)."""
    erros, atencoes = [], []
    idx = {t: i for i, t in enumerate(ORDEM_TRIMESTRES)}
    n = novo.copy()
    c = cpc[['ano', 'Trimestre', 'RONI_2c']].rename(columns={'RONI_2c': 'RONI_2c_cpc'}).copy()
    n['ano'] = pd.to_numeric(n['ano']).round().astype(int)
    n['mes'] = pd.to_numeric(n['mes']).round().astype(int)
    c['ano'] = pd.to_numeric(c['ano']).round().astype(int)

    def ordem(df):
        return df['ano'] * 12 + df['Trimestre'].map(idx)

    dup = n[n.duplicated(['ano', 'Trimestre'], keep=False)]
    if len(dup):
        erros.append(f'{len(dup)} linha(s) duplicada(s) no asset: {dup[["ano", "Trimestre"]].values.tolist()[:5]}')
    m = n.merge(c, on=['ano', 'Trimestre'], how='outer', indicator=True)
    so_asset = m[m['_merge'] == 'left_only']
    if len(so_asset):
        erros.append(f'{len(so_asset)} estação(ões) só no asset: {so_asset[["ano", "Trimestre"]].values.tolist()[:5]}')
    so_cpc = m[m['_merge'] == 'right_only']
    if len(so_cpc):
        ult = ordem(n).max()
        novas, buracos = so_cpc[ordem(so_cpc) > ult], so_cpc[ordem(so_cpc) <= ult]
        if len(novas):
            atencoes.append(f'o CPC já publicou {len(novas)} estação(ões) que o asset não tem '
                            f'{novas[["ano", "Trimestre"]].values.tolist()[:5]}: rode o 02')
        if len(buracos):
            erros.append(f'{len(buracos)} estação(ões) do CPC faltando no meio do asset '
                         f'{buracos[["ano", "Trimestre"]].values.tolist()[:5]}')
    amb = m[m['_merge'] == 'both'].copy()
    amb['ord'] = ordem(amb)
    recente = amb['ord'].nlargest(n_recentes).min() if len(amb) else 0
    for col, tol, nome in (('RONI', 0.05 + 1e-9, 'RONI x RONI_2c do CPC (> 0,05)'),
                           ('RONI_2c', 1e-6, 'RONI_2c gravado x CPC')):
        if col not in amb.columns:
            continue
        dif = (pd.to_numeric(amb[col], errors='coerce') - amb['RONI_2c_cpc']).abs()
        ruins = amb[dif.isna() | (dif > tol)]
        antigas, recentes = ruins[ruins['ord'] < recente], ruins[ruins['ord'] >= recente]
        if len(antigas):
            erros.append(f'{nome}: {len(antigas)} estação(ões) {antigas[["ano", "Trimestre"]].values.tolist()[:5]}')
        if len(recentes):
            atencoes.append(f'{nome}: o CPC revisou {recentes[["ano", "Trimestre"]].values.tolist()}: rode o 02')
    errado = n[n['mes'] != n['Trimestre'].map(idx) + 1]
    if len(errado):
        erros.append(f'mês central errado em {len(errado)} estação(ões) {errado[["ano", "Trimestre", "mes"]].values.tolist()[:5]}')
    t_esp = np.array([data_ms(f'{a:04d}-{mm:02d}-01') for a, mm in zip(n['ano'], n['mes'])], dtype=float)
    t_gr = pd.to_numeric(n['t_ms'], errors='coerce').to_numpy(dtype=float) if 't_ms' in n else np.full(len(n), np.nan)
    if np.isnan(t_gr).all():   # [V4 revisão B-06] a exportação de tabela pode não guardar a propriedade (A CONFIRMAR)
        atencoes.append('system:time_start não veio em nenhuma estação (o painel recalcula a data por ano e mês; '
                        'data_ms conferido)' if 'data_ms' in n else
                        'nem system:time_start nem data_ms vieram no asset: rode o 02 v4')
    else:
        errado = n[~(t_gr == t_esp)]
        if len(errado):
            erros.append(f'system:time_start diferente do 1º dia do mês central em {len(errado)} estação(ões) '
                         f'{errado[["ano", "mes"]].values.tolist()[:5]}')
    if 'data_ms' in n:          # o 02 grava data_ms igual ao system:time_start
        errado = n[~(pd.to_numeric(n['data_ms'], errors='coerce').to_numpy(dtype=float) == t_esp)]
        if len(errado):
            erros.append(f'data_ms diferente do 1º dia do mês central em {len(errado)} estação(ões)')
    if 'chave_join' in n:       # o 02 v4 grava a chave do painel em texto (M02-03)
        esp = [f'{a:04d}_{mm:02d}' for a, mm in zip(n['ano'], n['mes'])]
        errado = n[n['chave_join'].astype(str).to_numpy() != np.array(esp)]
        if len(errado):
            erros.append(f'chave_join gravada errada em {len(errado)} estação(ões) '
                         f'{errado[["ano", "mes", "chave_join"]].values.tolist()[:5]}')
    k = sorted(set(n['ano'] * 12 + n['mes'] - 1))
    lacunas = [(a // 12, a % 12 + 1) for a, b in zip(k, k[1:]) if b - a != 1]
    if lacunas:
        erros.append(f'série com {len(lacunas)} lacuna(s), depois de (ano, mês) {lacunas[:5]}')
    if not chaves:
        erros.append('chave do painel não calculada')
    for a, mm, ch in chaves:
        esperado = f'{int(a):04d}_{int(mm):02d}' if a is not None and mm is not None else None
        if not isinstance(ch, str) or not re.fullmatch(r'\d{4}_\d{2}', ch) or ch != esperado:
            erros.append(f'chave do painel {ch!r} (esperado {esperado!r})')
    return ('ERRO' if erros else ('ATENÇÃO' if atencoes else 'OK')), erros + atencoes


def bandas_v21():
    """[V4 M08-10] As 100 bandas do contrato da matriz V2.1: 96 médias/desvios e 4 contagens n_<faixa>."""
    b = {f'{v}_{e}_{f}_{fx}' for v in VARS_V21 for e in ('m', 's') for f in ('sicsb', 'gfs') for fx in FAIXAS_V21}
    return b | {f'n_{fx}' for fx in FAIXAS_V21}


def checar_matriz_v21(meta):
    """[V4 M08-10] meta: {nome da imagem: {'bandas': {banda: data_type}, 'props': {...}}}. Lista de problemas
    (vazia = estrutura e propriedades conforme o contrato)."""
    prob = []
    esperadas = {f'Matriz_GFS_{m:02d}' for m in range(1, 13)}
    if set(meta) != esperadas:
        prob.append(f'imagens: faltam {sorted(esperadas - set(meta))}, sobram {sorted(set(meta) - esperadas)}')
    alvo = bandas_v21()
    for nome in sorted(set(meta) & esperadas):
        mes = int(nome[-2:])
        bandas, props = meta[nome].get('bandas') or {}, meta[nome].get('props') or {}
        if set(bandas) != alvo:
            prob.append(f'{nome}: {len(bandas)} bandas (esperado {len(alvo)}); faltam {sorted(alvo - set(bandas))[:4]}, '
                        f'sobram {sorted(set(bandas) - alvo)[:4]}')
        for fx in FAIXAS_V21:       # contrato revisado: Float32 com valores inteiros (os inteiros são vistos no E6)
            tipo = bandas.get(f'n_{fx}')
            if tipo is not None and tipo.get('precision') != 'float':
                prob.append(f'{nome}: n_{fx} não é Float32 ({tipo})')
        for k, v in CONTRATO_V21.items():
            if props.get(k) != v:
                prob.append(f'{nome}: {k} = {props.get(k)!r} (esperado {v!r})')
        mr = props.get('mes_referencia')
        if isinstance(mr, bool) or not isinstance(mr, (int, float)) or mr != mes:
            prob.append(f'{nome}: mes_referencia = {mr!r} (esperado {mes})')
        for fx in FAIXAS_V21:
            npar = props.get(f'n_pares_{fx}')
            if isinstance(npar, bool) or not isinstance(npar, (int, float)) or not npar > 0:
                prob.append(f'{nome}: n_pares_{fx} = {npar!r} (esperado > 0)')
        if not props.get('gerado_em'):
            prob.append(f'{nome}: sem gerado_em')
    return prob


def criterio_detalhe(r_v21, r_v1):
    """[V4 M08-10] Detalhe espacial do L1 (gradiente GFS / BR-DWGD na Serra do Mar) melhor que o da V1:
    pelo menos 1,2 vez a razão da V1 e pelo menos 0,3."""
    return r_v21 is not None and r_v1 is not None and bool(r_v21 >= max(1.2 * r_v1, 0.3))


def criterio_rs(q):
    """[V4 M08-10] q = (Rs GFS / Rs BR-DWGD na V2.1, L1) / (a mesma razão na V1). Pelo F4, a média dos blocos de 6 h
    deve baixar a radiação do GFS de 3% a 11%; aceita de 1% a 15% (limiar heurístico, calibrar na 1ª execução)."""
    return q is not None and bool(0.85 <= q <= 0.99)


def grade_nativa(t, tol=1e-6):
    """[V4 revisão B-02] Mesma grade do BR-DWGD: escala igual e origem deslocada por um número inteiro de pixels
    (o asset exportado guarda a origem da própria região de exportação). Igual à função do 01."""
    t = list(t or [])
    if len(t) != 6 or any(abs(t[i] - TRANSFORM[i]) > 1e-12 for i in (0, 1, 3, 4)):
        return False
    fx = (t[2] - TRANSFORM[2]) / TRANSFORM[0]
    fy = (t[5] - TRANSFORM[5]) / TRANSFORM[4]
    return abs(fx - round(fx)) < tol and abs(fy - round(fy)) < tol


def checar_q1(props, contagens, transform, n_dif, n_coinc=0):
    """[V4 Q1] Problemas da máscara de qualidade gravada. contagens: {1..4: pixels, unweighted}; transform:
    crsTransform gravado; n_dif: pixels cuja classe difere da recalculada no dia Q1_DIA."""
    prob = []
    for k, v in (('versao_mascara', 'Q1'), ('dia_referencia', '2001-01-15'), ('dias_classes', DIAS_CLASSES_Q1)):
        if props.get(k) != v:
            prob.append(f'{k} = {props.get(k)!r} (esperado {v!r})')
    for k in (1, 2, 3, 4):
        p = props.get(f'n_classe_{k}')
        if p is None or int(round(float(p))) != contagens.get(k):
            prob.append(f'n_classe_{k}: propriedade {p!r} x contagem {contagens.get(k)}')
    t = list(transform or [])
    if not grade_nativa(t):          # [V4 revisão B-02] origem do asset deslocada por pixels inteiros é a mesma grade
        prob.append(f'grade {t} diferente da nativa')
    if n_dif:
        prob.append(f'{n_dif} pixel(s) com classe diferente da recalculada em {Q1_DIA}')
    if n_coinc > Q1_MAX_COINC:                                  # [V4.1 revisão V41-07]
        prob.append(f'{n_coinc} pixels B iguais ao BR-DWGD em {Q1_DIA} (a K1a mediu até ~8; B inflado?)')
    return prob


def avaliar_j1(linhas):
    """[V4 J1] linhas: dicts com 'tipo' ('historico' ou 'definitiva_2026') e as contagens A, B, C e D.
    Histórico: INFO se, em todos os dias, C = J1_ESPERADO['C'], A + B = J1_ESPERADO['AB'] (±1, arredondamento) e
    B entre J1_ESPERADO['B'] - J1_TOL_B e J1_ESPERADO['B'] + 1 ([V4.1 K1a]: um pixel B pode ficar igual ao BR-DWGD
    num dia por coincidência, e ele passa para A sem mudar A + B); senão ATENÇÃO.
    Dias definitivos de 2026: OK se B = 0 em todos; senão ATENÇÃO; None se não houver nenhum."""
    hist = [x for x in linhas if x['tipo'] == 'historico']
    d26 = [x for x in linhas if x['tipo'] == 'definitiva_2026']
    ok_h = bool(hist) and all(
        x['C'] == J1_ESPERADO['C'] and abs(x['A'] + x['B'] - J1_ESPERADO['AB']) <= 1
        and J1_ESPERADO['B'] - J1_TOL_B <= x['B'] <= J1_ESPERADO['B'] + 1 for x in hist)
    st_26 = None if not d26 else ('OK' if all(x['B'] == 0 for x in d26) else 'ATENÇÃO')
    return ('INFO' if ok_h else 'ATENÇÃO'), st_26


# =========================================================================
# 2. CONEXÃO E TRAVA DE SOMENTE LEITURA
# =========================================================================
import ee

log('=' * 100)
log(f'AUDITORIA COMPLETA DO SISTEMA SAB (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT) | '
    f'modo {"RÁPIDO" if RAPIDO else "COMPLETO"}')
log(f'Saídas em: {PASTA}')
log('=' * 100)
try:
    ee.Initialize(project=PROJETO)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJETO)
log(f'Earth Engine conectado ao projeto {PROJETO} (biblioteca ee {ee.__version__})')


def _bloqueado(*a, **k):
    raise RuntimeError('AUDITORIA SOMENTE LEITURA: tentativa de escrita bloqueada')


for _nome in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset',
              'setAssetAcl', 'setAssetProperties', 'createFolder', 'startProcessing',
              'exportImage', 'exportTable', 'exportVideo', 'exportMap', 'startIngestion',
              'startTableIngestion', 'cancelTask', 'cancelOperation'):
    if hasattr(ee.data, _nome):
        setattr(ee.data, _nome, _bloqueado)
ee.batch.Task.start = _bloqueado
log('🔒 Trava de somente leitura ativa: criar, apagar, renomear, exportar e cancelar estão bloqueados.\n')

GAUL_BR = ee.FeatureCollection('FAO/GAUL/2015/level0').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
LIMITES = GAUL_BR.geometry().bounds()
MASCARA_BR = ee.Image.constant(1).clipToCollection(GAUL_BR).mask()
REGIAO_AMPLA = ee.Geometry.Rectangle(REGIAO_AMPLA_COORDS, None, False)       # [V4] contagens unweighted
GAUL1 = ee.FeatureCollection('FAO/GAUL/2015/level1')                        # [V4 J3]
UF_BR = GAUL1.filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))                    # [V4 J3]


def rr(img, reducer, rotulo, geom=None, crs=CRS, transform=TRANSFORM, escala=None):
    """reduceRegion na grade do SAB (ou na escala dada), com novas tentativas."""
    args = dict(reducer=reducer, geometry=geom or LIMITES, maxPixels=1e10, tileScale=4)
    if escala:
        args.update(scale=escala)
    else:
        args.update(crs=crs, crsTransform=transform)
    return gi(img.reduceRegion(**args), rotulo)


def regiao_pontos(col, bandas, pontos, rotulo, crs=CRS, transform=TRANSFORM, escala=None):
    """getRegion nos pontos; devolve DataFrame com nome do ponto, data e bandas."""
    geom = ee.Geometry.MultiPoint([[lo, la] for _, la, lo in pontos])
    if escala:
        linhas = gi(col.select(bandas).getRegion(geom, escala), rotulo)
    else:
        linhas = gi(col.select(bandas).getRegion(geom, None, crs, transform), rotulo)
    df = pd.DataFrame(linhas[1:], columns=linhas[0])
    if not len(df):
        return df
    la = df['latitude'].astype(float).to_numpy()
    lo = df['longitude'].astype(float).to_numpy()
    dist = np.stack([np.hypot(la - p[1], lo - p[2]) for p in pontos])
    df['ponto'] = [pontos[i][0] for i in dist.argmin(axis=0)]
    df['data'] = pd.to_datetime(df['time'].astype('float64'), unit='ms', utc=True).dt.tz_localize(None)
    for b in bandas:
        df[b] = pd.to_numeric(df[b], errors='coerce')
    return df[['ponto', 'data'] + bandas]


def padronizar_sab(img):
    return ee.Image(ee.Algorithms.If(img.bandNames().contains('precipitation_mm'),
                                     img.select(NOMES_ANTIGOS, BANDAS_SAB), img.select(BANDAS_SAB)))


def br_fisico(img):
    """BR-DWGD em unidades físicas, exatamente como o motor grava (UR limitada a 0-100, chuva >= 0)."""
    b = {k: img.select(k).multiply(e).add(o) for k, (e, o) in ESCALA_BR.items()}
    b['pr'] = b['pr'].max(0)
    b['RH'] = b['RH'].clamp(0, 100)
    return ee.Image(ee.Image.cat([b[k].rename(BR_PARA_SAB[k]) for k in ESCALA_BR])
                    .copyProperties(img, ['system:time_start']))


def listar_assets(pai):
    nomes, token = [], None
    while True:
        params = {'parent': pai, 'pageSize': 1000}
        if token:
            params['pageToken'] = token
        resp = ee.data.listAssets(params)
        for a in resp.get('assets', []):
            nomes.append({'nome': (a.get('id') or a.get('name')).split('/')[-1],
                          'caminho': a.get('id') or a.get('name'), 'tipo': a.get('type')})
        token = resp.get('nextPageToken')
        if not token:
            return nomes


def existe(caminho):
    try:
        ee.data.getAsset(caminho)
        return True
    except Exception:
        return False


# [V4] Utilitários das seções novas (Q1, J1, J5, D14)
def dia_img(col, d):
    return ee.Image(ee.ImageCollection(col).filterDate(d, ee.Date(d).advance(1, 'day')).first())


def classes_pixel(d, completo=True):
    """[V4 J1/Q1] Classes de pixel do dia d com a lógica da auditoria J (J1): A = SAB igual ao BR-DWGD (ETo e chuva
    com diferença até 0,01); B = BR-DWGD existe e o SAB difere; C = SAB sem BR-DWGD; D = BR-DWGD sem SAB.
    completo=True é a regra do 01: a ausência do BR-DWGD fora da área da imagem dele também conta como C.
    completo=False reproduz exatamente a conta da J1."""
    sab = padronizar_sab(dia_img(SAB, d))
    br = br_fisico(dia_img(BR_DWGD, d))
    sab_ok = sab.select('et_potencial').mask().gt(0)
    br_ok = br.select('et_potencial').mask().gt(0)
    if completo:
        br_ok = br_ok.unmask(0)
    igual = (sab.select('et_potencial').subtract(br.select('et_potencial')).abs().lte(0.01)
             .And(sab.select('pr_mm').subtract(br.select('pr_mm')).abs().lte(0.01))).unmask(0)
    return {'A': sab_ok.And(br_ok).And(igual), 'B': sab_ok.And(br_ok).And(igual.Not()),
            'C': sab_ok.And(br_ok.Not()), 'D': sab_ok.Not().And(br_ok)}


def codigo_abc(cl):
    """[V4 Q1] 0 = sem SAB; 1 = A; 2 = B; 3 = C (dentro ou fora do Brasil). Mesma conta do 01."""
    return ee.Image(0).where(cl['A'], 1).where(cl['B'], 2).where(cl['C'], 3).rename('abc')


def inventario_2026():
    """[V4 D14/J1/J5] Propriedades dos dias de 2026 em diante, numa consulta só (guardada no CONTEXTO).
    Propriedade ausente vira valor padrão, para as listas do reduceColumns ficarem alinhadas."""
    if 'inv26' in CONTEXTO:
        return CONTEXTO['inv26']
    campos = ['t', 'versao', 'alg', 'rodada', 'Confianca_Prazo', 'fonte', 'janela_chuva_utc', 'matriz_gfs',
              'metodo_temp_gfs', 'metodo_ur_rs_gfs', 'teto_razao_temp_gfs']

    def props26(img):
        d = img.toDictionary()
        return ee.Feature(None, {'t': img.get('system:time_start'), 'versao': d.get('versao', 'definitiva'),
                                 'alg': d.get('versao_algoritmo', 'V1.0'), 'rodada': d.get('rodada_gfs_ms', -1),
                                 'Confianca_Prazo': d.get('Confianca_Prazo', ''), 'fonte': d.get('fonte', ''),
                                 'janela_chuva_utc': d.get('janela_chuva_utc', ''),
                                 'matriz_gfs': d.get('matriz_gfs', ''),
                                 'metodo_temp_gfs': d.get('metodo_temp_gfs', ''),
                                 'metodo_ur_rs_gfs': d.get('metodo_ur_rs_gfs', ''),
                                 'teto_razao_temp_gfs': d.get('teto_razao_temp_gfs', 2.0)})   # [K11]

    fim = (datetime.now(timezone.utc) + timedelta(days=40)).strftime('%Y-%m-%d')
    res = gi(ee.ImageCollection(SAB).filterDate('2026-01-01', fim).map(props26)
             .reduceColumns(ee.Reducer.toList().repeat(len(campos)), campos), 'inventário 2026')
    df = pd.DataFrame(dict(zip(campos, res['list'])))
    if len(df):
        df['dia'] = pd.to_datetime(df['t'].astype('float64'), unit='ms', utc=True).dt.strftime('%Y-%m-%d')
        df['rodada'] = pd.to_numeric(df['rodada'], errors='coerce').fillna(-1).astype('int64')
        df = df.drop(columns='t').sort_values('dia').reset_index(drop=True)
    else:
        df = pd.DataFrame(columns=['dia'] + campos[1:])
    CONTEXTO['inv26'] = df
    return df


SECOES = []


def secao(codigo, titulo):
    def deco(fn):
        SECOES.append((codigo, titulo, fn))
        return fn
    return deco


CONTEXTO = {}   # resultados que uma seção passa para outra


# =========================================================================
# A. AMBIENTE E FILA DE TAREFAS
# =========================================================================
@secao('A', 'Ambiente e fila de tarefas')
def secao_a():
    tarefas = ee.data.getTaskList()
    ativas = [t for t in tarefas if t.get('state') in ('READY', 'RUNNING', 'SUBMITTED', 'PENDING')]
    inicio_mes = datetime(AGORA.year, AGORA.month, 1, tzinfo=timezone.utc).timestamp() * 1000
    recentes = [t for t in tarefas if (t.get('creation_timestamp_ms') or 0) >= inicio_mes - 30 * 864e5]
    falhas = [t for t in recentes if t.get('state') == 'FAILED']
    eecu_mes = sum((t.get('batch_eecu_usage_seconds') or 0) for t in tarefas
                   if (t.get('start_timestamp_ms') or 0) >= inicio_mes) / 3600
    por_prefixo = pd.Series([t.get('description', '')[:6] for t in ativas]).value_counts()
    log(f'   tarefas ativas: {len(ativas)} | por prefixo: {por_prefixo.to_dict()}')
    achado('A1', 'INFO', 'Tarefas ativas na fila', f'{len(ativas)} tarefa(s)',
           'Motor, normais e matrizes dividem a mesma fila de 3.000 tarefas do projeto.')
    if falhas:
        tab = pd.DataFrame([{'descricao': t.get('description'), 'criada': ms_para_txt(t.get('creation_timestamp_ms')),
                             'erro': (t.get('error_message') or '')[:120]} for t in falhas[:50]])
        log_tabela(tab, 'Falhas nos últimos ~30 dias (até 50):')
        salvar_csv(tab, 'A_tarefas_falhas.csv')
        erros_cota = sum('quota' in (t.get('error_message') or '').lower() for t in falhas)
        achado('A2', 'ATENÇÃO', 'Tarefas que falharam nos últimos ~30 dias',
               f'{len(falhas)} falha(s), {erros_cota} por cota', 'Ver A_tarefas_falhas.csv.',
               'Ler as mensagens de erro antes das próximas exportações.')
    else:
        achado('A2', 'OK', 'Tarefas que falharam nos últimos ~30 dias', 'nenhuma')
    achado('A3', 'INFO', 'Consumo de EECU das tarefas em lote neste mês (soma das tarefas listadas)',
           f'{eecu_mes:.1f} EECU-horas',
           'Só conta tarefas em lote ainda listadas; o uso interativo (painel, Colab) não entra. '
           'Cota mensal não comercial: Community 150, Contributor 1.000 EECU-horas.')


# =========================================================================
# B. ASSETS DO PROJETO
# =========================================================================
@secao('B', 'Assets do projeto')
def secao_b():
    raiz = listar_assets(RAIZ)
    linhas = []
    for a in raiz:
        n = None
        if a['tipo'] == 'IMAGE_COLLECTION':
            n = gi(ee.ImageCollection(a['caminho']).size(), f"tamanho {a['nome']}")
        elif a['tipo'] == 'TABLE':
            n = gi(ee.FeatureCollection(a['caminho']).size(), f"tamanho {a['nome']}")
        elif a['tipo'] == 'FOLDER':
            n = len(listar_assets(a['caminho']))
        linhas.append({'asset': a['nome'], 'tipo': a['tipo'], 'itens': n})
    tab = pd.DataFrame(linhas).set_index('asset')
    log_tabela(tab, 'Assets na raiz do projeto:')
    salvar_csv(tab, 'B_assets.csv')
    esperados = ['SAB_V1', 'SAB_V1_TMP', 'SICSB_1986_2025', 'SICSB_SOLO_2015_2025', 'SICSB_MATRIZ_GFS',
                 'RONI_Calibrado_Sazonal_1950_1980', 'Baselines']
    faltam = [e for e in esperados if e not in tab.index]
    achado('B1', 'ERRO' if faltam else 'OK', 'Assets esperados presentes',
           f'faltam {faltam}' if faltam else 'todos os 7 presentes',
           'Sem eles o motor e o painel não funcionam.' if faltam else '')
    novos = [n for n in ('RONI_CPC_v6', 'SICSB_MATRIZ_GFS_V2', 'SAB_MASCARA_QUALIDADE') if n in tab.index]
    achado('B2', 'INFO', 'Assets novos do pacote de correções', f'já existem: {novos or "nenhum"}',
           'Antes das etapas 2 e 3 é esperado que não existam.')
    for nome, esperado in (('SICSB_1986_2025', 12), ('SICSB_SOLO_2015_2025', 12), ('SICSB_MATRIZ_GFS', 12)):
        if nome in tab.index:
            n = tab.loc[nome, 'itens']
            achado(f'B3-{nome}', 'OK' if n == esperado else 'ATENÇÃO', f'{nome}: número de matrizes',
                   f'{n} (esperado {esperado})')


# =========================================================================
# C. BR-DWGD
# =========================================================================
@secao('C', 'BR-DWGD: metadados, datas, valores brutos e convenção do dia')
def secao_c():
    col = ee.ImageCollection(BR_DWGD)
    meta = ee.data.getAsset(BR_DWGD)
    log(f'   asset: tipo {meta.get("type")} | atualizado {meta.get("updateTime")} | '
        f'propriedades: {list((meta.get("properties") or {}).keys())[:20]}')
    tempos = gi(col.aggregate_array('system:time_start'), 'datas BR-DWGD')
    datas = pd.to_datetime(pd.Series(tempos, dtype='float64'), unit='ms', utc=True)
    horas = datas.dt.strftime('%H:%M').value_counts()
    dias = datas.dt.tz_localize(None).dt.normalize()
    esperado = pd.date_range(dias.min(), dias.max())
    faltando = sorted(set(esperado) - set(dias))
    duplicados = sorted(set(dias[dias.duplicated()]))
    log(f'   imagens: {len(tempos)} | de {dias.min():%Y-%m-%d} a {dias.max():%Y-%m-%d} | horários: {horas.to_dict()}')
    ok_n = len(tempos) == DIAS_HISTORICO and not faltando and not duplicados
    achado('C1', 'OK' if ok_n else 'ERRO', 'BR-DWGD: um dia por imagem, sem lacunas',
           f'{len(tempos)} imagens, {len(faltando)} dias faltando, {len(duplicados)} duplicados '
           f'(primeiros faltando: {[d.strftime("%Y-%m-%d") for d in faltando[:5]]})')
    so_meia_noite = list(horas.index) == ['00:00']
    achado('C2', 'OK' if so_meia_noite else 'ERRO', 'BR-DWGD: horário de system:time_start',
           f'{horas.to_dict()}',
           'A matriz GFS V2 (script 03) pareia cada dia com a rodada GFS criada à meia-noite UTC '
           'desse dia; com outro horário nenhuma rodada é encontrada.',
           '' if so_meia_noite else 'Não rode o script 03 antes de ajustar o pareamento.')

    primeira = ee.Image(col.first())
    tipos = gi(primeira.bandTypes(), 'tipos BR-DWGD')
    tab_tipos = pd.DataFrame({b: {'precisao': v.get('precision'), 'min': v.get('min'), 'max': v.get('max')}
                              for b, v in tipos.items()}).T
    log_tabela(tab_tipos, 'Tipos de pixel das bandas (valor bruto):')
    CONTEXTO['tipos_br'] = tipos

    # Valores brutos e físicos nos dias de amostra
    linhas = []
    for d in DIAS_AMOSTRA_HIST:
        img = ee.Image(col.filterDate(d, ee.Date(d).advance(1, 'day')).first())
        bruto = img.select(list(ESCALA_BR))
        ind = ee.Image.cat([
            bruto.select(['pr', 'Tmax', 'Tmin']).eq(-32768).rename(['s32768_pr', 's32768_Tmax', 's32768_Tmin']),
            bruto.select(['RH', 'u2', 'Rs', 'ET']).eq(0).rename(['zero_RH', 'zero_u2', 'zero_Rs', 'zero_ET']),
        ])
        fis = ee.Image.cat([bruto.select(k).multiply(e).add(o).rename(f'f_{k}') for k, (e, o) in ESCALA_BR.items()])
        red = ee.Reducer.minMax().combine(ee.Reducer.count(), sharedInputs=True)
        s1 = rr(ee.Image.cat([bruto, fis]), red, f'BR {d}', transform=TRANSFORM)
        s2 = rr(ind, ee.Reducer.sum(), f'BR indicadores {d}', transform=TRANSFORM)
        lin = {'dia': d}
        lin.update({k: s1.get(k) for k in s1})
        lin.update({k: s2.get(k) for k in s2})
        linhas.append(lin)
        log(f'   {d}: pr bruto {s1.get("pr_min")}..{s1.get("pr_max")} | Tmax bruto {s1.get("Tmax_min")}..'
            f'{s1.get("Tmax_max")} | RH bruto {s1.get("RH_min")}..{s1.get("RH_max")} | pixels pr {s1.get("pr_count")} '
            f'| -32768: {s2.get("s32768_pr")}/{s2.get("s32768_Tmax")}/{s2.get("s32768_Tmin")} | zeros RH/u2/Rs/ET: '
            f'{s2.get("zero_RH")}/{s2.get("zero_u2")}/{s2.get("zero_Rs")}/{s2.get("zero_ET")}')
    tab = pd.DataFrame(linhas).set_index('dia')
    salvar_csv(tab, 'C_br_dwgd_valores_por_dia.csv')
    sentinela = int(tab[['s32768_pr', 's32768_Tmax', 's32768_Tmin']].fillna(0).sum().sum())
    achado('C3', 'OK' if sentinela == 0 else 'ERRO', 'BR-DWGD: valor de ausência -32768 sem máscara',
           f'{sentinela} pixel(s) em {len(tab)} dias de amostra',
           'Se existir, a rota definitiva do motor grava Tmax/Tmin = -20 °C e chuva = 0 nesses pixels.',
           '' if sentinela == 0 else 'Mascarar -32768 no motor e verificar o histórico gravado.')
    zeros = tab[['zero_RH', 'zero_u2', 'zero_Rs', 'zero_ET']].fillna(0).sum()
    achado('C4', 'OK' if zeros.sum() == 0 else 'ATENÇÃO', 'BR-DWGD: valor bruto 0 nas bandas de 8 bits',
           f'{zeros.astype(int).to_dict()}',
           'Com o offset, bruto 0 vira valor levemente negativo (ETo -0,051 mm, vento -0,059 m/s, '
           'radiação -0,057 MJ/m²); o motor não limita ETo, vento e radiação a zero.',
           '' if zeros.sum() == 0 else 'Verificar se bruto 0 é ausência ou zero real e limitar a 0.')
    faixas = {'f_pr': (0, 450.01), 'f_Tmax': (-20.01, 50.01), 'f_Tmin': (-20.01, 50.01), 'f_RH': (-0.5, 100.01),
              'f_u2': (-0.1, 15.01), 'f_Rs': (-0.1, 40.01), 'f_ET': (-0.1, 13.01)}
    fora = {k: (tab[f'{k}_min'].min(), tab[f'{k}_max'].max()) for k in faixas
            if tab[f'{k}_min'].min() < faixas[k][0] or tab[f'{k}_max'].max() > faixas[k][1]}
    achado('C5', 'OK' if not fora else 'ERRO', 'BR-DWGD: valores físicos dentro da faixa da codificação',
           'todos dentro' if not fora else f'fora: {fora}',
           'Confirma escala e offset: UR até 100,000% só com o offset documentado no asset.')
    rh_max = tab['f_RH_max'].max()
    achado('C6', 'OK' if rh_max <= 100.01 else 'ERRO', 'BR-DWGD: UR máxima com o offset atual',
           f'{rh_max:.3f}%', 'Sem o offset, a UR máxima seria 100,394%.')
    teste_convencao_dia()


def teste_convencao_dia():
    """Convenção do dia de chuva: compara a chuva do BR-DWGD do dia D com três janelas do IMERG
    (00-24 UTC de D; 12 UTC de D-1 a 12 UTC de D; 12 UTC de D a 12 UTC de D+1) e com o ERA5-Land
    nos dias D-1, D e D+1. A janela com maior correlação indica a convenção."""
    imerg_id = None
    for cand in IMERG_OPCOES:
        try:
            n = gi(ee.ImageCollection(cand).filterDate('2019-01-01', '2019-01-02').size(), cand)
            if n:
                imerg_id = cand
                break
        except Exception:
            continue
    if not imerg_id:
        achado('C7', 'NÃO EXECUTADO', 'Convenção do dia de chuva (IMERG)', 'nenhuma coleção IMERG acessível')
    else:
        log(f'   teste da convenção do dia com {imerg_id}')
    br = ee.ImageCollection(BR_DWGD)
    # Pontos: grade de 3° sobre o Brasil, só onde o BR-DWGD tem dado
    cand = [(f'g{la:+.0f}{lo:+.0f}', *centro_pixel(la, lo)) for la in np.arange(-32, 5, 3)
            for lo in np.arange(-72, -34, 3)]
    teste = regiao_pontos(br.filterDate('2019-01-15', '2019-01-16').map(br_fisico), ['pr_mm'], cand, 'pontos grade')
    validos = set(teste.dropna(subset=['pr_mm'])['ponto'])
    pontos = [p for p in cand if p[0] in validos]
    if len(pontos) > MAX_PONTOS_CHUVA:          # distribuição uniforme no país, não só os primeiros
        pontos = [pontos[i] for i in np.linspace(0, len(pontos) - 1, MAX_PONTOS_CHUVA).round().astype(int)]
    log(f'   pontos com BR-DWGD válido: {len(pontos)}')

    def janelas(d):
        d = ee.Date(d)
        bandas = []
        if imerg_id:
            banda_imerg = 'precipitation' if imerg_id.endswith('V07') else 'precipitationCal'
            im = ee.ImageCollection(imerg_id).select(banda_imerg)
            def soma(a, b):
                return im.filterDate(a, b).sum().multiply(0.5)
            bandas += [soma(d, d.advance(1, 'day')).rename('imerg_00_24'),
                       soma(d.advance(-12, 'hour'), d.advance(12, 'hour')).rename('imerg_12ant_12'),
                       soma(d.advance(12, 'hour'), d.advance(36, 'hour')).rename('imerg_12_12seg')]
        era = ee.ImageCollection(ERA5)
        for k, nome in ((-1, 'era5_Dm1'), (0, 'era5_D0'), (1, 'era5_Dp1')):
            dk = d.advance(k, 'day')
            bandas.append(ee.Image(era.filterDate(dk, dk.advance(1, 'day')).first())
                          .select('total_precipitation_sum').multiply(1000).rename(nome))
        for k, nome in ((-1, 'era5tx_Dm1'), (0, 'era5tx_D0'), (1, 'era5tx_Dp1')):
            dk = d.advance(k, 'day')
            bandas.append(ee.Image(era.filterDate(dk, dk.advance(1, 'day')).first())
                          .select('temperature_2m_max').subtract(273.15).rename(nome))
        return ee.Image.cat(bandas).set('system:time_start', d.millis())

    nomes_ref = (['imerg_00_24', 'imerg_12ant_12', 'imerg_12_12seg'] if imerg_id else []) + \
                ['era5_Dm1', 'era5_D0', 'era5_Dp1', 'era5tx_Dm1', 'era5tx_D0', 'era5tx_Dp1']
    partes = []
    for ini, fim in PERIODOS_CHUVA:
        blocos = pd.date_range(ini, fim, freq='15D')
        for b0 in blocos:
            b1 = min(b0 + timedelta(days=15), pd.Timestamp(fim) + timedelta(days=1))
            dias_b = [x.strftime('%Y-%m-%d') for x in pd.date_range(b0, b1 - timedelta(days=1))]
            ref = ee.ImageCollection.fromImages([janelas(x) for x in dias_b])
            df_ref = regiao_pontos(ref, nomes_ref, pontos, f'referências {dias_b[0]}', escala=11132)
            df_br = regiao_pontos(br.filterDate(dias_b[0], b1.strftime('%Y-%m-%d')).map(br_fisico),
                                  ['pr_mm', 'tmax_C'], pontos, f'BR {dias_b[0]}')
            df_ref['dia'] = df_ref['data'].dt.normalize()
            df_br['dia'] = df_br['data'].dt.normalize()
            partes.append(df_br.drop(columns='data').merge(df_ref.drop(columns='data'), on=['ponto', 'dia']))
            log(f'   bloco {dias_b[0]} a {dias_b[-1]}: {len(partes[-1])} pares')
    dados = pd.concat(partes, ignore_index=True).dropna()
    salvar_csv(dados, 'C_convencao_dia_pares.csv')
    linhas = []
    for ref in nomes_ref:
        alvo = 'tmax_C' if 'tx' in ref else 'pr_mm'
        x, y = dados[alvo], dados[ref]
        lin = {'referencia': ref, 'variavel_BR': alvo, 'pares': len(x),
               'pearson': x.corr(y), 'spearman': x.corr(y, method='spearman')}
        if alvo == 'pr_mm':
            lin['acerto_dia_chuvoso'] = ((x >= 1) == (y >= 1)).mean()
        linhas.append(lin)
    tab = pd.DataFrame(linhas).set_index('referencia')
    log_tabela(tab.round(3), 'Correlação BR-DWGD do dia D x referências:')
    salvar_csv(tab, 'C_convencao_dia_resumo.csv')
    era_pr = tab.loc[['era5_Dm1', 'era5_D0', 'era5_Dp1'], 'spearman']
    era_tx = tab.loc[['era5tx_Dm1', 'era5tx_D0', 'era5tx_Dp1'], 'spearman']
    achado('C8', 'INFO' if era_pr.idxmax() == 'era5_D0' else 'ATENÇÃO',
           'Convenção do dia (ERA5-Land, defasagem de -1 a +1 dia)',
           f'chuva: melhor {era_pr.idxmax()} ({era_pr.round(3).to_dict()}); '
           f'Tmax: melhor {era_tx.idxmax()} ({era_tx.round(3).to_dict()})',
           'Dm1 = ERA5 do dia anterior, D0 = mesmo dia, Dp1 = dia seguinte. Se a melhor correlação da chuva for '
           'com Dm1, a chuva do BR-DWGD do dia D caiu, em boa parte, no dia civil anterior (leitura da manhã).')
    if imerg_id:
        im = tab.loc[['imerg_00_24', 'imerg_12ant_12', 'imerg_12_12seg']]
        melhor = im['spearman'].idxmax()
        margem = im['spearman'].max() - im['spearman'].drop(melhor).max()
        # voto por ponto
        votos = {}
        for p, g in dados.groupby('ponto'):
            c = {r: g['pr_mm'].corr(g[r], method='spearman') for r in im.index}
            c = {r: v for r, v in c.items() if pd.notna(v)}
            if c:
                votos[max(c, key=c.get)] = votos.get(max(c, key=c.get), 0) + 1
        texto = {'imerg_00_24': 'dia civil 00-24 UTC (mesma convenção do ERA5 e do GFS)',
                 'imerg_12ant_12': 'chuva das 12 UTC de D-1 às 12 UTC de D (leitura da manhã de D, '
                                   'atribuída a D)',
                 'imerg_12_12seg': 'chuva das 12 UTC de D às 12 UTC de D+1 (leitura da manhã de D+1, '
                                   'atribuída a D)'}[melhor]
        conclusivo = margem >= 0.05 and votos.get(melhor, 0) >= 0.6 * sum(votos.values())
        CONTEXTO['convencao_dia'] = melhor
        achado('C7', 'INFO' if melhor == 'imerg_00_24' else 'ATENÇÃO',
               'Convenção do dia de chuva do BR-DWGD (IMERG)',
               f'melhor janela: {melhor} (Spearman {im.loc[melhor, "spearman"]:.3f}, margem {margem:.3f}; '
               f'votos por ponto {votos}); {"conclusivo" if conclusivo else "NÃO conclusivo"}',
               f'O dia D do BR-DWGD corresponde a: {texto}.',
               '' if melhor == 'imerg_00_24' else
               'Os pareamentos diários com ERA5 e GFS (00-24 UTC) ficam deslocados meio dia; médias mensais '
               'quase não mudam. Avaliar ajuste na matriz GFS e na transição 2025/2026.')


# =========================================================================
# D. SAB_V1
# =========================================================================
@secao('D', 'SAB_V1: inventário, fidelidade, coerência e umidade do solo')
def secao_d():
    col = ee.ImageCollection(SAB)

    def props(img):
        d = img.toDictionary()
        return ee.Feature(None, {'t': img.get('system:time_start'), 'id': img.get('system:index'),
                                 'versao': d.get('versao', 'definitiva'), 'alg': d.get('versao_algoritmo', 'V1.0'),
                                 'antigo': img.bandNames().contains('precipitation_mm'),
                                 'nb': img.bandNames().size()})

    partes = []
    hoje = datetime.now(timezone.utc)
    for a0 in list(range(1961, hoje.year + 1, 5)):
        a1 = a0 + 5
        sub = col.filterDate(f'{a0}-01-01', f'{a1}-01-01')
        if a1 > hoje.year:
            sub = col.filterDate(f'{a0}-01-01', (hoje + timedelta(days=40)).strftime('%Y-%m-%d'))
        res = gi(sub.map(props).reduceColumns(ee.Reducer.toList().repeat(6),
                                              ['t', 'id', 'versao', 'alg', 'antigo', 'nb']), f'inventário {a0}')
        partes.append(pd.DataFrame(dict(zip(['t', 'id', 'versao', 'alg', 'antigo', 'nb'], res['list']))))
        log(f'   inventário {a0}-{a1 - 1}: {len(partes[-1])} imagens')
    inv = pd.concat(partes, ignore_index=True)
    inv['data_hora'] = pd.to_datetime(inv['t'].astype('float64'), unit='ms', utc=True).dt.tz_localize(None)
    inv['dia'] = inv['data_hora'].dt.normalize()
    inv['hora'] = inv['data_hora'].dt.strftime('%H:%M')
    inv['ano'] = inv['dia'].dt.year
    inv['id_esperado'] = 'SAB_' + inv['dia'].dt.strftime('%Y_%m_%d')
    inv['par'] = inv['versao'] + ' | ' + inv['alg']
    salvar_csv(inv.drop(columns=['t']), 'D_inventario_SAB_V1.csv')
    CONTEXTO['inv'] = inv

    hist = inv[inv['dia'] <= '2025-12-31']
    faltando = sorted(set(pd.date_range('1961-01-01', '2025-12-31')) - set(hist['dia']))
    duplic = sorted(set(inv['dia'][inv['dia'].duplicated()]))
    achado('D1', 'OK' if (len(hist) == DIAS_HISTORICO and not faltando and not duplic) else 'ERRO',
           'SAB_V1 1961-2025: um dia por imagem', f'{len(hist)} imagens (esperado {DIAS_HISTORICO}), '
           f'{len(faltando)} faltando, {len(duplic)} datas duplicadas; primeiros faltando '
           f'{[d.strftime("%Y-%m-%d") for d in faltando[:5]]}')
    errados = inv[inv['id'] != inv['id_esperado']]
    achado('D2', 'OK' if errados.empty else 'ERRO', 'SAB_V1: nome da imagem bate com a data',
           f'{len(errados)} divergência(s) {errados[["id", "id_esperado"]].head(5).values.tolist()}')
    achado('D3', 'OK' if set(inv['hora']) == {'00:00'} else 'ATENÇÃO', 'SAB_V1: horário de system:time_start',
           f'{inv["hora"].value_counts().to_dict()}')
    por_ano = pd.crosstab(inv['ano'], inv['par'])
    log_tabela(por_ano, 'Imagens por ano e (versão | algoritmo):', max_linhas=80)
    salvar_csv(por_ano, 'D_versoes_por_ano.csv')
    validos_hist = {'definitiva | V1.0', 'definitiva | V1.0-P12', 'definitiva | V1.2', 'definitiva | V1.3',
                    'definitiva | V1.4'}
    estranhos = hist[~hist['par'].isin(validos_hist)]['par'].value_counts().to_dict()
    achado('D4', 'OK' if not estranhos else 'ATENÇÃO', 'SAB_V1 1961-2025: só versões definitivas reconhecidas',
           f'fora do esperado: {estranhos}' if estranhos else 'todas reconhecidas',
           'A trava do motor V1.4 impede alterar esses dias; aqui só se mede.')
    nb = inv['nb'].value_counts().to_dict()
    achado('D5', 'OK' if set(nb) == {16} else 'ATENÇÃO', 'SAB_V1: número de bandas por imagem', f'{nb}')
    achado('D6', 'INFO', 'SAB_V1: imagens com nomes antigos de banda', f'{int(inv["antigo"].astype(bool).sum())}',
           'O painel e as normais tratam os nomes antigos.')
    v26 = inv[inv['dia'] >= '2026-01-01']['par'].value_counts().to_dict()
    achado('D7', 'INFO', 'SAB_V1 2026 em diante: tipos e versões', f'{v26}',
           'A prévia da etapa 5a precisa de dias "provisoria_era5 | V1.3".')

    # Coleção temporária
    if existe(SAB_TMP):
        tmp = listar_assets(SAB_TMP)
        nomes = sorted(t['nome'] for t in tmp)
        hist_tmp = [n for n in nomes if n[4:8].isdigit() and n[4:8] <= '2025']
        achado('D8', 'OK' if not hist_tmp else 'ATENÇÃO', 'SAB_V1_TMP: sobras', f'{len(nomes)} item(ns); '
               f'históricos (até 2025): {len(hist_tmp)} {hist_tmp[:10]}',
               'O motor V1.3 promoveria essas sobras por cima do SAB_V1; a V1.4 com trava não promove.')
    else:
        achado('D8', 'OK', 'SAB_V1_TMP: sobras', 'coleção não existe')

    fidelidade_br()
    coerencia_fisica()
    ano_2026_x_clima()
    umidade_nn_x_bilinear()


def fidelidade_br():
    """Os dias definitivos guardam exatamente o BR-DWGD (com escala e offset)?"""
    col_sab = ee.ImageCollection(SAB)
    col_br = ee.ImageCollection(BR_DWGD)
    filtro = ee.Filter.Or(*[ee.Filter.date(d, (pd.Timestamp(d) + timedelta(days=1)).strftime('%Y-%m-%d'))
                            for d in DIAS_AMOSTRA_HIST])
    bandas = list(BR_PARA_SAB.values())
    sab = regiao_pontos(col_sab.filter(filtro).map(padronizar_sab), bandas, PONTOS_CP, 'SAB nos pontos')
    br = regiao_pontos(col_br.filter(filtro).map(br_fisico), bandas, PONTOS_CP, 'BR nos pontos')
    sab['dia'] = sab['data'].dt.normalize()
    br['dia'] = br['data'].dt.normalize()
    m = sab.drop(columns='data').merge(br.drop(columns='data'), on=['ponto', 'dia'], suffixes=('_sab', '_br'))
    inv = CONTEXTO['inv'].drop_duplicates('dia').set_index('dia')
    m['alg'] = m['dia'].map(inv['alg'])
    linhas = []
    for b in bandas:
        dif = (m[f'{b}_sab'] - m[f'{b}_br']).abs()
        linhas.append({'banda': b, 'pares': int(dif.notna().sum()), 'max_dif': dif.max(),
                       'pares_com_dif>0.01': int((dif > 0.01).sum())})
    tab = pd.DataFrame(linhas).set_index('banda')
    log_tabela(tab, 'SAB definitivo x BR-DWGD (mesmo pixel, mesmos dias):')
    salvar_csv(m, 'D_fidelidade_SAB_x_BR.csv')
    divergentes = tab[tab['pares_com_dif>0.01'] > 0]
    detalhe = ''
    if len(divergentes):
        b = divergentes.index[0]
        sub = m[(m[f'{b}_sab'] - m[f'{b}_br']).abs() > 0.01]
        detalhe = f' | versões com divergência: {sub["alg"].value_counts().to_dict()}'
    achado('D9', 'OK' if divergentes.empty else 'ATENÇÃO', 'Dias definitivos do SAB = BR-DWGD',
           f'{len(divergentes)} banda(s) com diferença > 0,01: {divergentes.index.tolist()}{detalhe}',
           'Confirma que o histórico gravado usa a mesma escala/offset do motor atual.')


def coerencia_fisica():
    inv = CONTEXTO['inv']
    mapa_par = inv.drop_duplicates('dia').set_index('dia')['par']
    mapa_alg = inv.drop_duplicates('dia').set_index('dia')['alg']           # [V4 M08-04]
    dias = list(DIAS_AMOSTRA_HIST)
    d26 = inv[inv['dia'] >= '2026-01-01'].sort_values('dia')
    for par, g in d26.groupby('par'):
        idx = np.linspace(0, len(g) - 1, min(len(g), 4 if RAPIDO else 8)).astype(int)
        dias += [g.iloc[i]['dia'].strftime('%Y-%m-%d') for i in idx]
    # [V4 M08-04] Máscara de referência: SAB_2025_12_31 (último dia do histórico e máscara canônica do motor V1.5),
    # sem MASCARA_BR. Compara presença do pixel e também o valor da máscara (pode ser fracionário, k/255).
    ref_val = padronizar_sab(ee.Image(f'{SAB}/SAB_2025_12_31')).select('pr_mm').mask()
    ref_masc = ref_val.gt(0)
    linhas, mascaras, coords = [], [], []
    for d in sorted(set(dias)):
        img = ee.Image(ee.ImageCollection(SAB).filterDate(d, (pd.Timestamp(d) + timedelta(days=1)).strftime('%Y-%m-%d')).first())
        s = padronizar_sab(img)
        ind = ee.Image.cat([
            s.select('RH').lt(0).Or(s.select('RH').gt(100)).rename('UR_fora_0_100'),
            s.select('pr_mm').lt(0).rename('chuva_negativa'),
            s.select('et_potencial').lt(0).rename('ETo_negativa'),
            s.select('u2').lt(0).rename('vento_negativo'),
            s.select('rs').lt(0).rename('radiacao_negativa'),
            s.select('tmax_C').lt(s.select('tmin_C')).rename('Tmax_menor_Tmin'),
            s.select('et_real').gt(s.select('et_potencial').add(1e-4)).rename('ETreal_maior_ETo'),
            s.select('transpiracao_mm').gt(s.select('et_real').add(1e-4)).rename('transp_maior_ETreal'),
            s.select('soil_moisture_0_100cm_m3_m3').gt(UMIDADE_MAX).rename('umid100_acima_0_9'),
            s.select('soil_moisture_0_5cm_m3_m3').gt(UMIDADE_MAX).rename('umid5_acima_0_9'),
            s.select('tmax_C').lte(-20.0005).rename('Tmax_igual_-20'),
            s.select('pr_mm').mask().gt(0).rename('pixels'),          # [V4 M08-05] 0/1, sem fração de máscara
        ]).updateMask(MASCARA_BR)
        r = rr(ind, ee.Reducer.sum().unweighted(), f'coerência {d}')   # [V4 M08-05] contagens inteiras
        mm = rr(s.select(['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'soil_moisture_0_100cm_m3_m3'])
                .updateMask(MASCARA_BR), ee.Reducer.minMax(), f'faixas {d}')
        lin = {'dia': d, 'par': mapa_par.get(pd.Timestamp(d), '?')}
        lin.update({k: r.get(k) for k in r})
        lin.update({k: mm.get(k) for k in mm})
        linhas.append(lin)
        log(f'   {d} ({lin["par"]}): pixels {r.get("pixels"):.0f} | UR fora {r.get("UR_fora_0_100")} | '
            f'Tmax<Tmin {r.get("Tmax_menor_Tmin")} | ETreal>ETo {r.get("ETreal_maior_ETo")} | '
            f'umid100>0,9 {r.get("umid100_acima_0_9")} | ETo<0 {r.get("ETo_negativa")}')
        # [V4 M08-04] máscara do dia x máscara do SAB_2025_12_31 (pixel a pixel, região ampla, unweighted)
        m_val = s.select('pr_mm').mask()
        m = m_val.gt(0)
        dif = ee.Image.cat([m.And(ref_masc.Not()).rename('so_dia'), ref_masc.And(m.Not()).rename('so_ref'),
                            m.And(ref_masc).And(m_val.neq(ref_val)).rename('fracao')])
        rd = rr(dif, ee.Reducer.sum().unweighted(), f'máscara {d}', geom=REGIAO_AMPLA)
        so_dia, so_ref, fracao = (int(round(rd.get(k) or 0)) for k in ('so_dia', 'so_ref', 'fracao'))
        mascaras.append({'dia': d, 'par': lin['par'], 'alg': mapa_alg.get(pd.Timestamp(d), '?'),
                         'versao': str(lin['par']).split(' | ')[0],                       # [V4 revisão A-03]
                         'so_no_dia': so_dia, 'so_no_SAB_2025_12_31': so_ref, 'fracao_de_mascara_diferente': fracao,
                         'n_dif': so_dia + so_ref + fracao})
        if mascaras[-1]['n_dif']:
            log(f'      máscara diferente da do SAB_2025_12_31: {so_dia} pixel(s) só no dia, {so_ref} só na referência, '
                f'{fracao} com fração de máscara diferente')
            if len(coords) < 50 and mascaras[-1]['n_dif'] <= 2000:
                loc = rr(ee.Image.pixelLonLat().addBands(dif.select(['so_dia', 'fracao']))
                         .updateMask(dif.reduce(ee.Reducer.max())), ee.Reducer.toList(), f'locais {d}',
                         geom=REGIAO_AMPLA)
                for la, lo, sd, fr in zip(loc.get('latitude') or [], loc.get('longitude') or [],
                                          loc.get('so_dia') or [], loc.get('fracao') or []):
                    if len(coords) < 50:
                        coords.append({'dia': d, 'alg': mascaras[-1]['alg'], 'latitude': round(la, 4),
                                       'longitude': round(lo, 4),
                                       'tipo': 'fração de máscara diferente' if fr else
                                       ('só no dia' if sd else 'só no SAB_2025_12_31')})
    tab = pd.DataFrame(linhas).set_index('dia')
    salvar_csv(tab, 'D_coerencia_fisica_por_dia.csv')
    CONTEXTO['coerencia'] = tab
    cols = ['UR_fora_0_100', 'chuva_negativa', 'ETo_negativa', 'vento_negativo', 'radiacao_negativa',
            'Tmax_menor_Tmin', 'ETreal_maior_ETo', 'transp_maior_ETreal', 'umid100_acima_0_9',
            'umid5_acima_0_9', 'Tmax_igual_-20']
    resumo = tab.groupby('par')[cols + ['pixels']].sum()
    pct = resumo[cols].div(resumo['pixels'], axis=0) * 100
    log_tabela(pct.round(4).T, 'Coerência física (% dos pixels do Brasil nos dias de amostra, por versão):')
    salvar_csv(pct, 'D_coerencia_fisica_pct.csv')
    pixels = tab['pixels'].astype(float)
    # [V4 M08-04] D10 exige a mesma máscara em todos os dias amostrados (antes tolerava 1% de diferença)
    tab_m = pd.DataFrame(mascaras).set_index('dia')
    salvar_csv(tab_m, 'D_mascara_x_SAB_2025_12_31.csv')
    if coords:
        tab_c = pd.DataFrame(coords)
        log_tabela(tab_c, 'Pixels com máscara diferente da do SAB_2025_12_31 (até 50):', 50)
        salvar_csv(tab_c, 'D_mascara_coordenadas.csv')
    difs = tab_m[tab_m['n_dif'] > 0]
    gfs15 = difs[(difs['alg'] == 'V1.5') & difs['versao'].isin(VERSOES_GFS_SAB)]
    achado('D10', status_d10(mascaras), 'SAB_V1: cobertura de pixels por dia',
           f'máscara igual à do SAB_2025_12_31 em {len(tab_m) - len(difs)} de {len(tab_m)} dias; diferem: '
           f'{difs.groupby("par")["n_dif"].agg(["count", "max"]).to_dict("index") if len(difs) else "nenhum"} '
           f'(dias, máx. pixels); dias GFS V1.5: até {int(gfs15["so_no_SAB_2025_12_31"].max()) if len(gfs15) else 0} '
           f'pixel(s) faltando e até {int(gfs15["so_no_dia"].max()) if len(gfs15) else 0} fora da canônica; '
           f'pixels no Brasil: média {pixels.mean():.0f}, mínimo {pixels.min():.0f}, máximo {pixels.max():.0f}',
           'Os dias históricos, ERA5 e definitivos devem ter a mesma máscara do SAB_2025_12_31 (presença e fração). '
           'Ficam INFO: dias V1.3/V1.4 (motor anterior; cerca de 4 pixels a mais nos dias GFS) e dias GFS V1.5 com '
           'cobertura CONTIDA na canônica (só faltam pixels). Qualquer outra diferença é ATENÇÃO. Ver '
           'D_mascara_x_SAB_2025_12_31.csv e D_mascara_coordenadas.csv.')
    for c in cols:
        total = pct[c].max()
        status = 'OK' if total == 0 else ('INFO' if c in ('umid100_acima_0_9', 'umid5_acima_0_9', 'ETreal_maior_ETo',
                                                          'transp_maior_ETreal') else 'ATENÇÃO')
        piores = pct[c][pct[c] > 0].round(4).to_dict()
        achado(f'D11-{c}', status, f'SAB_V1: {c}', 'zero em todas as versões' if total == 0 else f'% por versão: {piores}',
               'Nos dias V1.0, umidade acima de 0,9 e ET real > ETo são corrigidos na leitura do painel.'
               if status == 'INFO' else '')


def ano_2026_x_clima():
    """Meses completos de 2026 (provisório ERA5 calibrado) x climatologia 1986-2025 do BR-DWGD."""
    inv = CONTEXTO['inv']
    hoje = datetime.now(timezone.utc)
    meses = [m for m in range(1, hoje.month) if
             len(inv[(inv['dia'].dt.year == 2026) & (inv['dia'].dt.month == m)]) == calendar.monthrange(2026, m)[1]]
    if not meses:
        achado('D12', 'NÃO EXECUTADO', '2026 x climatologia', 'nenhum mês completo de 2026')
        return
    linhas = []
    for m in meses:
        ini = f'2026-{m:02d}-01'
        fim = (pd.Timestamp(ini) + pd.offsets.MonthBegin(1)).strftime('%Y-%m-%d')
        sab = ee.ImageCollection(SAB).filterDate(ini, fim).map(padronizar_sab)
        nd = calendar.monthrange(2026, m)[1]
        mes_img = ee.Image.cat([sab.select('pr_mm').sum().rename('pr_mes'),
                                sab.select(['tmax_C', 'tmin_C', 'RH', 'et_potencial', 'rs', 'u2']).mean()])
        clima = ee.Image(f'{CLIMA}/Matriz_Clima_{m:02d}')
        ref = ee.Image.cat([clima.select('pr_m_br').multiply(nd).rename('c_pr_mes'),
                            clima.select(['Tmax_m_br', 'Tmin_m_br', 'RH_m_br', 'ET_m_br', 'Rs_m_br', 'u2_m_br'])])
        img = ee.Image.cat([mes_img, ref]).set('system:time_start', ee.Date(ini).millis())
        df = regiao_pontos(ee.ImageCollection([img]), ['pr_mes', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'rs', 'u2',
                                                       'c_pr_mes', 'Tmax_m_br', 'Tmin_m_br', 'RH_m_br', 'ET_m_br',
                                                       'Rs_m_br', 'u2_m_br'], PONTOS_CP, f'2026-{m:02d}')
        df['mes'] = m
        linhas.append(df)
    t = pd.concat(linhas, ignore_index=True)
    t['razao_chuva'] = t['pr_mes'] / t['c_pr_mes']
    t['dif_Tmax'] = t['tmax_C'] - t['Tmax_m_br']
    t['dif_Tmin'] = t['tmin_C'] - t['Tmin_m_br']
    t['dif_UR'] = t['RH'] - t['RH_m_br']
    t['razao_ETo'] = t['et_potencial'] / t['ET_m_br']
    t['razao_Rs'] = t['rs'] / t['Rs_m_br']
    t['razao_vento'] = t['u2'] / t['u2_m_br']
    cols = ['razao_chuva', 'dif_Tmax', 'dif_Tmin', 'dif_UR', 'razao_ETo', 'razao_Rs', 'razao_vento']
    resumo = t.groupby('mes')[cols].median()
    log_tabela(resumo.round(2), '2026 (provisório) x climatologia 1986-2025, mediana dos 18 pontos:')
    salvar_csv(t.set_index(['mes', 'ponto']), 'D_2026_x_climatologia.csv')
    implaus = t[(t['dif_Tmax'].abs() > 5) | (t['dif_Tmin'].abs() > 5) | (t['dif_UR'].abs() > 25) |
                (t['razao_ETo'] > 1.6) | (t['razao_ETo'] < 0.6) | (t['razao_vento'] > 2.5) | (t['razao_Rs'] > 1.5)]
    achado('D12', 'OK' if implaus.empty else 'ATENÇÃO', '2026 provisório x climatologia (plausibilidade)',
           f'{len(implaus)} mês-ponto com desvio fisicamente improvável (|ΔT|>5 °C, |ΔUR|>25, ETo fora de 0,6-1,6x, '
           f'vento > 2,5x, radiação > 1,5x); viés mediano Tmax {resumo["dif_Tmax"].median():+.2f} °C, '
           f'UR {resumo["dif_UR"].median():+.1f}, ETo {resumo["razao_ETo"].median():.2f}x',
           'Chuva diferente do normal é esperada (El Niño); desvios grandes de temperatura, UR, ETo, vento '
           'ou radiação apontam problema na rota provisória.')


def umidade_nn_x_bilinear():
    """Quanto a umidade calibrada muda ao trocar vizinho mais próximo por bilinear (antecipa a etapa 5a)."""
    def expandir(img):
        return img.unmask(img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMean(1, 'square', 'pixels'))

    linhas = []
    for m in MESES_SOLO_2025:
        d = f'2025-{m:02d}-15'
        era = ee.Image(ee.ImageCollection(ERA5).filterDate(d, (pd.Timestamp(d) + timedelta(days=1)).strftime('%Y-%m-%d')).first())
        solo = ee.Image(f'{SOLO}/Matriz_Solo_{m:02d}')
        res = {}
        for nome, p, bruto in (('umid5', 'ssur', era.select('volumetric_soil_water_layer_1')),
                               ('umid100', 'swat', era.expression('(l1*7 + l2*21 + l3*72) / 100', {
                                   'l1': era.select('volumetric_soil_water_layer_1'),
                                   'l2': era.select('volumetric_soil_water_layer_2'),
                                   'l3': era.select('volumetric_soil_water_layer_3')}))):
            fator = expandir(solo.select(f'{p}_m_smap')).divide(expandir(solo.select(f'{p}_m_era5')).max(1e-3)).min(FATOR_MAX)
            teto = expandir(solo.select(f'{p}_m_smap')).add(expandir(solo.select(f'{p}_s_smap')).multiply(3)) \
                .min(UMIDADE_MAX).unmask(UMIDADE_MAX)
            nn = bruto.multiply(fator).max(0).min(teto)
            bil = bruto.resample('bilinear').multiply(fator).max(0).min(teto)
            dif = bil.subtract(nn)
            img = ee.Image.cat([nn.rename('nn'), bil.rename('bil'), dif.abs().rename('absdif'),
                                dif.abs().gt(0.001).rename('alterado')]).updateMask(MASCARA_BR)
            r = rr(img, ee.Reducer.mean(), f'solo {nome} {d}')
            res[nome] = r
        lin = {'dia': d}
        for nome, r in res.items():
            lin[f'{nome}_nn'] = r['nn']
            lin[f'{nome}_bil'] = r['bil']
            lin[f'{nome}_delta_pct'] = 100 * (r['bil'] / r['nn'] - 1)
            lin[f'{nome}_absdif_medio'] = r['absdif']
            lin[f'{nome}_pct_pixels_alterados'] = 100 * r['alterado']
        linhas.append(lin)
        log(f'   {d}: Δ umid 0-5 {lin["umid5_delta_pct"]:+.2f}% | Δ umid 0-100 {lin["umid100_delta_pct"]:+.2f}% | '
            f'pixels alterados {lin["umid5_pct_pixels_alterados"]:.1f}% / {lin["umid100_pct_pixels_alterados"]:.1f}%')
    tab = pd.DataFrame(linhas).set_index('dia')
    salvar_csv(tab, 'D_umidade_nn_x_bilinear.csv')
    pior = max(tab['umid5_delta_pct'].abs().max(), tab['umid100_delta_pct'].abs().max())
    achado('D13', 'OK' if pior <= 2 else 'ATENÇÃO', 'Umidade do solo: vizinho mais próximo x bilinear (Brasil)',
           f'maior |Δ| nacional {pior:.2f}% (critério da etapa 5a: ±2%); |Δ| médio por pixel '
           f'{tab["umid5_absdif_medio"].mean():.4f} / {tab["umid100_absdif_medio"].mean():.4f} m³/m³',
           'Mede, em dias de 2025, o efeito da mudança SOLO_BILINEAR da V1.4. Dentro de ±2%: a descontinuidade '
           'com o histórico é desprezível na média nacional.',
           '' if pior <= 2 else 'Decidir antes da etapa 5b: manter vizinho mais próximo ou reprocessar o solo do histórico.')


# =========================================================================
# D14. [V4 M08-11] DIAS DE 2026: MOTOR V1.5 (seção própria, roda junto com 'D')
# =========================================================================
@secao('D14', 'Dias de 2026: motor V1.5, datas, rodada 00Z, confiança e emenda ERA5 -> GFS')
def secao_d14():
    titulo = 'SAB_V1 2026: dias do motor V1.5 (contíguos, rodada 00Z, Confianca_Prazo, emenda ERA5 -> GFS)'
    if not RODAR_D14:
        achado('D14', 'NÃO EXECUTADO', titulo, 'desligada (RODAR_D14 = False)')
        return
    inv = inventario_2026()
    if inv.empty:
        achado('D14', 'INFO', titulo, 'nenhum dia de 2026 no SAB_V1')
        return
    hoje = ee.Date(AGORA.strftime('%Y-%m-%d'))
    lista = gi(ee.ImageCollection(ERA5).filterDate(hoje.advance(-150, 'day'), hoje.advance(1, 'day'))
               .aggregate_array('system:time_start'), 'ERA5 datas')
    # [Correção 21/10/2026, 18h] O motor usa o último dia ERA5 CONTÍNUO (sem lacuna); a emenda é conferida contra ele
    ultimo_era5, faltando = ultimo_dia_continuo_era5({ms_para_txt(x, horas=False) for x in lista})
    if faltando:
        log(f'   ℹ️ ERA5-Land sem {len(faltando)} dia(s) antes do último publicado: {faltando[:10]}; '
            f'o motor usa o ERA5 até {ultimo_era5} e a previsão GFS depois dele.')
    res = checar_d14(inv, ultimo_era5)
    tab = pd.DataFrame([{'criterio': k, 'ok': v[0], 'detalhe': v[1]} for k, v in res.items()]).set_index('criterio')
    log_tabela(tab, f'Critérios dos {len(inv)} dias de 2026 (ok vazio = não se aplica):')
    log_tabela(pd.crosstab(inv['versao'], inv['alg']), 'Dias de 2026 por versão e algoritmo:')
    salvar_csv(inv.set_index('dia'), 'D14_dias_2026.csv')
    status = status_d14(res, inv)
    falhos = [k for k, v in res.items() if v[0] is False]
    achado('D14', status, titulo,
           ('aguardando motor V1.5 (etapa 5b); ' if status == 'INFO' else '') +
           (f'critérios não atendidos: {falhos}' if falhos else 'todos os critérios atendidos'),
           'Depois da etapa 5b: todos os dias V1.5, datas contíguas, dias GFS da rodada 00Z com Confianca_Prazo, '
           'incompleta só no último dia e emenda no dia seguinte ao último dia do ERA5-Land (G1).',
           '' if status != 'ATENÇÃO' else 'Ver D14_dias_2026.csv. Se só a emenda falhar porque o ERA5-Land andou, '
           'rode o motor.')


# =========================================================================
# E. MATRIZES DE CALIBRAÇÃO
# =========================================================================
def percentis(img, rotulo):
    # [V4 M08-06] Percentis exatos (pandas) sobre uma amostra de pixels do Brasil, como a J4. O percentil do Earth
    # Engine usa histograma e colapsava (p1 = p99) nos fatores com valores extremos. A contagem continua total.
    cont = rr(img.updateMask(MASCARA_BR), ee.Reducer.count(), f'{rotulo} contagem')
    fc = gi(img.updateMask(MASCARA_BR).sample(region=LIMITES, projection=ee.Projection(CRS).atScale(11132),
                                              numPixels=AMOSTRA_PERCENTIS, seed=7, tileScale=4), f'{rotulo} amostra')
    df = pd.DataFrame([f['properties'] for f in fc['features']])
    out = {}
    for b in cont:
        v = pd.to_numeric(df[b], errors='coerce').dropna() if b in df else pd.Series(dtype=float)
        q = v.quantile([0.01, 0.05, 0.5, 0.95, 0.99]) if len(v) else pd.Series([np.nan] * 5)
        out.update({f'{b}_p{p}': float(x) for p, x in zip((1, 5, 50, 95, 99), q.values)})
        out[f'{b}_count'] = cont[b]
        out[f'{b}_n_amostra'] = len(v)
    return out


@secao('E', 'Matrizes de calibração')
def secao_e():
    # E1 clima
    linhas = []
    for m in range(1, 13):
        c = ee.Image(f'{CLIMA}/Matriz_Clima_{m:02d}')
        if m == 1:
            log(f'   bandas SICSB_1986_2025: {gi(c.bandNames(), "bandas clima")}')
        fat = ee.Image.cat([c.select(f'{p}_m_br').divide(c.select(f'{p}_m_era').max(1e-3)).rename(f'fator_{p}')
                            for p in ('pr', 'u2', 'Rs')])
        adi = ee.Image.cat([c.select(f'{p}_m_br').subtract(c.select(f'{p}_m_era')).rename(f'dif_{p}')
                            for p in ('Tmax', 'Tmin', 'RH')])
        acima = fat.gt(FATOR_MAX).rename([f'acima5_{p}' for p in ('pr', 'u2', 'Rs')])
        r = percentis(ee.Image.cat([fat, adi]), f'clima {m:02d}')
        a = rr(acima.updateMask(MASCARA_BR), ee.Reducer.mean(), f'clima acima {m:02d}')
        lin = {'mes': m}
        lin.update(r)
        lin.update({k: 100 * v for k, v in a.items()})
        linhas.append(lin)
    tab = pd.DataFrame(linhas).set_index('mes')
    salvar_csv(tab, 'E_clima_fatores.csv')
    cols_show = [c for c in tab.columns if c.endswith(('_p1', '_p50', '_p99')) or c.startswith('acima5')]
    log_tabela(tab[cols_show].round(3), 'SICSB_1986_2025: fatores BR/ERA5 e diferenças (percentis no Brasil); % acima de 5:')
    pct5 = tab[[c for c in tab.columns if c.startswith('acima5')]].max().max()
    achado('E1', 'OK' if pct5 < 1 else 'ATENÇÃO', 'Matriz clima: pixels com fator acima do teto de 5',
           f'máximo {pct5:.2f}% dos pixels em algum mês/variável',
           'Onde o fator passa de 5 o motor limita; muitos pixels indicam ERA5 com média quase zero.')
    achado('E2', 'INFO', 'Matriz clima: correção aditiva de temperatura e UR (mediana nacional)',
           f'Tmax {tab["dif_Tmax_p50"].median():+.2f} °C, Tmin {tab["dif_Tmin_p50"].median():+.2f} °C, '
           f'UR {tab["dif_RH_p50"].median():+.1f} pontos; extremos Tmax {tab["dif_Tmax_p1"].min():+.1f} a '
           f'{tab["dif_Tmax_p99"].max():+.1f} °C')

    # E3 solo
    linhas = []
    for m in range(1, 13):
        s = ee.Image(f'{SOLO}/Matriz_Solo_{m:02d}')
        if m == 1:
            log(f'   bandas SICSB_SOLO_2015_2025: {gi(s.bandNames(), "bandas solo")}')
        fat = ee.Image.cat([s.select(f'{p}_m_smap').divide(s.select(f'{p}_m_era5').max(1e-3)).rename(f'fator_{p}')
                            for p in ('ssur', 'swat', 'rsup', 'rsub')])
        r = percentis(fat, f'solo {m:02d}')
        a = rr(fat.gt(FATOR_MAX).updateMask(MASCARA_BR), ee.Reducer.mean(), f'solo acima {m:02d}')
        lin = {'mes': m}
        lin.update(r)
        lin.update({f'acima5_{k}': 100 * v for k, v in a.items()})
        linhas.append(lin)
    tab = pd.DataFrame(linhas).set_index('mes')
    salvar_csv(tab, 'E_solo_fatores.csv')
    cols_show = [c for c in tab.columns if c.endswith(('_p5', '_p50', '_p95')) or c.startswith('acima5')]
    log_tabela(tab[cols_show].round(3), 'SICSB_SOLO_2015_2025: fatores SMAP/ERA5 (percentis no Brasil); % acima de 5:')
    for p in ('ssur', 'swat', 'rsup', 'rsub'):
        v = tab[f'acima5_fator_{p}'].max()
        achado(f'E3-{p}', 'OK' if v < 1 else 'ATENÇÃO', f'Matriz solo: fator {p} acima de 5',
               f'máximo {v:.2f}% dos pixels; mediana nacional {tab[f"fator_{p}_p50"].median():.2f}')

    # E4 GFS V1: resolução efetiva (gradiente médio GFS x BR-DWGD na Serra do Mar)
    caixa = ee.Geometry.Rectangle([-48.5, -24.8, -43.5, -21.5], None, False)
    g = ee.Image(f'{GFS_V1}/Matriz_GFS_01')
    bandas = gi(g.bandNames(), 'bandas GFS V1')
    log(f'   bandas SICSB_MATRIZ_GFS (V1): {bandas}')
    alvo = 'Tmax_m_sicsb' if 'Tmax_m_sicsb' in bandas else [b for b in bandas if b.startswith('Tmax_m_') and 'gfs' not in b][0]

    def grad(img):
        gr = img.gradient()
        return gr.select('x').hypot(gr.select('y'))

    r = rr(ee.Image.cat([grad(g.select('Tmax_m_gfs')).rename('g_gfs'), grad(g.select(alvo)).rename('g_br')]),
           ee.Reducer.mean(), 'gradientes GFS V1', geom=caixa)
    razao = r['g_gfs'] / r['g_br'] if r.get('g_br') else float('nan')
    achado('E4', 'ATENÇÃO' if razao < 0.25 else 'INFO', 'Matriz GFS V1: detalhe espacial (gradiente GFS / BR-DWGD, Serra do Mar)',
           f'{razao:.3f}',
           'Um GFS de 0,25° reamostrado corretamente guarda parte do relevo (razão tipicamente 0,3-0,7); '
           'razão muito baixa indica campo calculado em ~1° (efeito do .resample() na composição, corrigido na V2).')
    for nome, caminho in (('SICSB_MATRIZ_GFS_V2', GFS_V2), ('RONI_CPC_v6', RONI_NOVO)):
        achado(f'E5-{nome}', 'INFO', f'{nome} existe?', 'sim' if existe(caminho) else 'não (esperado antes das etapas 2 e 3)')


# =========================================================================
# E6. [V4 M08-10] MATRIZ GFS V2.1 (seção própria, roda junto com 'E')
# =========================================================================
CAIXA_SERRA_MAR = [-48.5, -24.8, -43.5, -21.5]       # a mesma caixa do E4


def gradiente(img):
    gr = img.gradient()
    return gr.select('x').hypot(gr.select('y'))


@secao('E6', 'Matriz GFS V2.1: estrutura, propriedades, detalhe espacial e radiação')
def secao_e6():
    if not RODAR_E6:
        achado('E6', 'NÃO EXECUTADO', 'Matriz GFS V2.1', 'desligada (RODAR_E6 = False)')
        return
    if not existe(GFS_V2):
        achado('E6', 'ATENÇÃO', 'Matriz GFS V2.1', 'SICSB_MATRIZ_GFS_V2 não existe',
               'O motor V1.5 calibra a previsão por faixa de prazo com essa matriz.', 'Rode o 03.')
        return
    info = gi(ee.ImageCollection(GFS_V2), 'metadados da matriz V2.1')
    meta = {f['id'].split('/')[-1]: {'bandas': {b['id']: b.get('data_type') or {} for b in f.get('bands', [])},
                                     'props': f.get('properties') or {}} for f in info.get('features', [])}
    tab = pd.DataFrame({n: {k: m['props'].get(k) for k in ['versao_matriz', 'mes_referencia', 'inicio_rodadas',
                                                           'fim_dias'] + [f'n_pares_{fx}' for fx in FAIXAS_V21]}
                        for n, m in meta.items()}).T.sort_index()
    log_tabela(tab, 'SICSB_MATRIZ_GFS_V2: propriedades por imagem:')
    salvar_csv(tab, 'E6_matriz_v21_propriedades.csv')
    prob = checar_matriz_v21(meta)
    for m in (1, 7):      # contagens n_<faixa>: Float32 com valores inteiros e pelo menos 1 par onde não há máscara
        nome = f'Matriz_GFS_{m:02d}'
        if nome in meta and {f'n_{fx}' for fx in FAIXAS_V21} <= set(meta[nome]['bandas']):
            g2 = ee.Image(f'{GFS_V2}/{nome}')
            r = rr(ee.Image.cat([g2.select(f'n_{fx}').subtract(g2.select(f'n_{fx}').round()).abs().rename(f'frac_{fx}')
                                 for fx in FAIXAS_V21] + [g2.select(f'n_{fx}').rename(f'n_{fx}') for fx in FAIXAS_V21]),
                   ee.Reducer.max().combine(ee.Reducer.min(), sharedInputs=True), f'contagens n_* {m:02d}')
            for fx in FAIXAS_V21:
                if (r.get(f'frac_{fx}_max') or 0) > 0 or (r.get(f'n_{fx}_min') is not None and r.get(f'n_{fx}_min') < 1):
                    prob.append(f'{nome}: n_{fx} com valor não inteiro ou < 1 (min {r.get(f"n_{fx}_min")}, '
                                f'max {r.get(f"n_{fx}_max")}, maior parte fracionária {r.get(f"frac_{fx}_max")})')
            log(f'   {nome}: pares por pixel (min-max) ' +
                ', '.join(f'{fx} {r.get(f"n_{fx}_min")}-{r.get(f"n_{fx}_max")}' for fx in FAIXAS_V21))
    for p in prob[:30]:
        log(f'   problema: {p}')
    achado('E6-estrutura', 'OK' if not prob else 'ATENÇÃO', 'Matriz GFS V2.1: imagens, 100 bandas e propriedades do contrato',
           f'{len(meta)} imagens; ' + ('tudo conforme o contrato' if not prob else f'{len(prob)} problema(s): {prob[:3]}'),
           'Contrato v4: versao_matriz V2.1, GFS v16 desde 2021-03-23, 96 bandas de média/desvio, 4 contagens n_<faixa> '
           '(Float32 com valores inteiros) e n_pares_<faixa> > 0.',
           '' if not prob else 'Rode o 03 v4 de novo para os meses com problema.')

    caixa = ee.Geometry.Rectangle(CAIXA_SERRA_MAR, None, False)
    linhas = []
    for m in (1, 7):
        nome = f'Matriz_GFS_{m:02d}'
        if nome not in meta or not {'Tmax_m_gfs_L1', 'Tmax_m_sicsb_L1', 'Rs_m_gfs_L1', 'Rs_m_sicsb_L1'} <= set(meta[nome]['bandas']):
            continue
        g2, g1 = ee.Image(f'{GFS_V2}/{nome}'), ee.Image(f'{GFS_V1}/{nome}')
        r = rr(ee.Image.cat([gradiente(g2.select('Tmax_m_gfs_L1')).rename('g2_gfs'),
                             gradiente(g2.select('Tmax_m_sicsb_L1')).rename('g2_br'),
                             gradiente(g1.select('Tmax_m_gfs')).rename('g1_gfs'),
                             gradiente(g1.select('Tmax_m_sicsb')).rename('g1_br')]),
               ee.Reducer.mean(), f'gradientes V2.1 x V1 {m:02d}', geom=caixa)
        s = rr(ee.Image.cat([g2.select('Rs_m_gfs_L1').rename('rs2_gfs'), g2.select('Rs_m_sicsb_L1').rename('rs2_br'),
                             g1.select('Rs_m_gfs').rename('rs1_gfs'), g1.select('Rs_m_sicsb').rename('rs1_br')])
               .updateMask(MASCARA_BR), ee.Reducer.mean(), f'radiação V2.1 x V1 {m:02d}')
        div = lambda a, b: a / b if a is not None and b else None
        lin = {'mes': m, 'razao_grad_V21_L1': div(r.get('g2_gfs'), r.get('g2_br')),
               'razao_grad_V1': div(r.get('g1_gfs'), r.get('g1_br')),
               'Rs_gfs_sobre_br_V21_L1': div(s.get('rs2_gfs'), s.get('rs2_br')),
               'Rs_gfs_sobre_br_V1': div(s.get('rs1_gfs'), s.get('rs1_br'))}
        lin['Rs_V21_sobre_V1'] = div(lin['Rs_gfs_sobre_br_V21_L1'], lin['Rs_gfs_sobre_br_V1'])
        lin['detalhe_ok'] = criterio_detalhe(lin['razao_grad_V21_L1'], lin['razao_grad_V1'])
        lin['Rs_ok'] = criterio_rs(lin['Rs_V21_sobre_V1'])
        linhas.append(lin)
    if not linhas:
        achado('E6-detalhe', 'NÃO EXECUTADO', 'Matriz GFS V2.1: detalhe espacial e radiação do L1',
               'janeiro e julho sem as bandas Tmax/Rs do L1')
        return
    t = pd.DataFrame(linhas).set_index('mes')
    log_tabela(t.round(3), 'Matriz V2.1 x V1 (L1): razão de gradientes na Serra do Mar e radiação GFS/BR-DWGD no Brasil:')
    salvar_csv(t, 'E6_matriz_v21_x_v1.csv')
    achado('E6-detalhe', 'OK' if t['detalhe_ok'].all() else 'ATENÇÃO',
           'Matriz GFS V2.1: detalhe espacial do L1 (gradiente GFS / BR-DWGD, Serra do Mar) x V1',
           f'V2.1 {t["razao_grad_V21_L1"].round(3).to_dict()} x V1 {t["razao_grad_V1"].round(3).to_dict()} (por mês)',
           'Critério: V2.1 >= 1,2 vez a V1 e >= 0,3. Razão baixa indica campo GFS suavizado (problema do E4 na V1).')
    achado('E6-Rs', 'OK' if t['Rs_ok'].all() else 'ATENÇÃO', 'Matriz GFS V2.1: radiação do GFS (L1) x V1',
           f'(Rs GFS/BR na V2.1) / (na V1): {t["Rs_V21_sobre_V1"].round(3).to_dict()} (por mês)',
           'Com a média dos blocos de 6 h (F4), a radiação do GFS deve cair de 3% a 11% em relação à V1; aceita de '
           '0,85 a 0,99 (limiar heurístico, calibrar na 1ª execução).')


# =========================================================================
# F. GFS
# =========================================================================
@secao('F', 'GFS: tempos, horas de previsão por época, rodadas e radiação')
def secao_f():
    col = ee.ImageCollection(GFS)
    # F1 time_start x creation_time
    amostra = col.filterDate('2024-03-01', '2024-03-02').limit(50)
    pares = gi(amostra.reduceColumns(ee.Reducer.toList().repeat(4),
                                     ['system:time_start', 'creation_time', 'forecast_time', 'forecast_hours']), 'tempos GFS')['list']
    t = pd.DataFrame(dict(zip(['time_start', 'creation_time', 'forecast_time', 'forecast_hours'], pares))).astype(float)
    igual = (t['time_start'] == t['creation_time']).all()
    coerente = ((t['forecast_time'] - t['creation_time']) / 3.6e6 == t['forecast_hours']).all()
    achado('F1', 'OK' if igual else 'ERRO', 'GFS: system:time_start igual a creation_time',
           f'{"sim" if igual else "NÃO"} em {len(t)} imagens; forecast_time = creation + horas: {"sim" if coerente else "NÃO"}',
           'O motor e o script 03 filtram a rodada por filterDate em creation_time.')

    # F2 horas de previsão por época
    datas = sorted({f'{a}-{m:02d}-10' for a in range(2015, 2027) for m in ((1, 7) if not RAPIDO else (7,))
                    if f'{a}-{m:02d}-10' <= AGORA.strftime('%Y-%m-%d') and f'{a}-{m:02d}-10' >= '2015-07-10'}
                   | {'2017-07-08', '2017-07-10', '2017-07-12', '2019-06-11', '2019-06-13', '2021-03-21',
                      '2021-03-22',            # [V4 M08-03] última rodada 00Z do GFS v15
                      '2021-03-23', '2021-06-10', '2021-06-12', '2021-06-14'})
    linhas = []
    for d in datas:
        c = data_ms(d)
        horas = gi(col.filterDate(c, c + 3600 * 1000).filter(ee.Filter.eq('creation_time', c))
                   .aggregate_array('forecast_hours'), f'horas {d}')
        h = sorted(int(x) for x in horas)
        def passo(a, b):
            seg = [x for x in h if a < x <= b]
            return (int(np.median(np.diff(seg))) if len(seg) > 1 else None), len(seg)
        p1, n1 = passo(0, 120)
        p2, n2 = passo(120, 240)
        p3, n3 = passo(240, 384)
        linhas.append({'rodada_00Z': d, 'imagens': len(h), 'hora_max': max(h) if h else None,
                       'passo_1_120': p1, 'n_1_120': n1, 'passo_121_240': p2, 'n_121_240': n2,
                       'passo_241_384': p3, 'n_241_384': n3})
    tab = pd.DataFrame(linhas).set_index('rodada_00Z')
    log_tabela(tab, 'Horas de previsão da rodada 00Z por data:')
    salvar_csv(tab, 'F_gfs_horas_por_epoca.csv')
    # [V4 M08-03] Premissa do 03 v4: só GFS v16, rodadas 00Z desde INICIO_RODADAS_03 em todas as faixas, com saída
    # hora a hora até 120 h e de 3 em 3 h de 120 a 384 h. As rodadas anteriores só aparecem na tabela.
    def esperado(d):
        if d >= INICIO_RODADAS_03:
            return (1, 120, 3, 40, 3, 48)
        return None
    falhas = []
    n_conferidas = 0                                                        # [V4 M08-03]
    for d, lin in tab.iterrows():
        e = esperado(d)
        if not e:
            continue
        n_conferidas += 1
        obs = (lin['passo_1_120'], lin['n_1_120'], lin['passo_121_240'], lin['n_121_240'])
        if obs != e[:4] or (e[4] and (lin['passo_241_384'], lin['n_241_384']) != (e[4], e[5])):
            falhas.append(d)
    achado('F2', 'OK' if not falhas else 'ATENÇÃO', 'GFS: horas de previsão conferem com as épocas do script 03',
           f'divergências em {falhas}' if falhas else
           f'todas as {n_conferidas} rodadas desde {INICIO_RODADAS_03} conferem (1 h até 120 h; 3 h até 384 h)',
           'Datas divergentes perdem amostra na matriz V2 (rodada incompleta é descartada), sem enviesar.')

    # F3 disponibilidade mês a mês das rodadas 00Z com as horas-chave
    chave = [6, 24, 120, 192, 312]
    meses = pd.date_range('2015-07-01', AGORA.strftime('%Y-%m-01'), freq='MS')
    if RAPIDO:
        meses = [m for m in meses if m.month in (1, 7)]
    linhas = []
    for m0 in meses:
        m1 = m0 + pd.offsets.MonthBegin(1)
        sub = col.filterDate(m0.strftime('%Y-%m-%d'), m1.strftime('%Y-%m-%d')).filter(ee.Filter.inList('forecast_hours', chave))
        res = gi(sub.filter(ee.Filter.notNull(['creation_time', 'forecast_hours']))     # [22/10] ver horas_00z
                 .reduceColumns(ee.Reducer.toList().repeat(2), ['creation_time', 'forecast_hours']), f'rodadas {m0:%Y-%m}')['list']
        df = pd.DataFrame({'c': res[0], 'h': res[1]}).astype(float)
        df = df[(df['c'] % 86400000) == 0]                    # só rodadas 00Z
        nd = calendar.monthrange(m0.year, m0.month)[1]
        lin = {'mes': m0.strftime('%Y-%m'), 'dias_no_mes': nd}
        for h in chave:
            lin[f'dias_com_h{h}'] = df[df['h'] == h]['c'].nunique()
        linhas.append(lin)
    tab = pd.DataFrame(linhas).set_index('mes')
    salvar_csv(tab, 'F_gfs_rodadas_00Z_por_mes.csv')
    log_tabela(tab, 'Dias do mês com rodada 00Z contendo cada hora-chave (6 e 24 = 1º dia; 120 = dia 5; 192 = dia 8; 312 = dia 13):', 150)
    # [V4 M08-03] desde o início do 03 v4 e em todas as faixas (h24 = L1, h120 = L5, h192 = L8, h312 = L13)
    pos = tab[(tab.index >= INICIO_RODADAS_03[:7]) & (tab.index < AGORA.strftime('%Y-%m'))]   # mês corrente incompleto
    horas_faixas = ['dias_com_h24', 'dias_com_h120', 'dias_com_h192', 'dias_com_h312']
    falhos = pos[pos[horas_faixas].min(axis=1) < 0.8 * pos['dias_no_mes']].index.tolist()
    achado('F3', 'OK' if not falhos else 'ATENÇÃO',
           f'GFS: meses com menos de 80% das rodadas 00Z (desde {INICIO_RODADAS_03[:7]}, horas 24/120/192/312)',
           f'{falhos}' if falhos else 'nenhum', 'Meses com poucas rodadas pesam menos na matriz V2.')

    transicoes_gfs()
    radiacao_gfs()


def transicoes_gfs():
    """Datas reais das mudanças de estrutura das rodadas 00Z: 384 h com saída horária até 120 h, e saídas de
    3 em 3 h depois de 240 h. [V4 M08-02] Dia a dia, só com metadados (creation_time e forecast_hours lidos em
    blocos de 10 dias); a hora 0 não entra no teste (tem_384, tres_apos_240 e detectar_transicao na seção 1b)."""
    col = ee.ImageCollection(GFS)

    def horas_00z(ini, fim, bloco=10):
        """{dia: horas de previsão da rodada 00Z do dia}, de ini a fim (inclusive)."""
        out = {}
        for b0 in pd.date_range(ini, fim, freq=f'{bloco}D'):
            b1 = min(b0 + timedelta(days=bloco), pd.Timestamp(fim) + timedelta(days=1))
            # [Correção 22/10/2026] toList().repeat(2) descarta os nulos de cada coluna em separado: com uma
            # imagem sem creation_time ou forecast_hours (acervo GFS de 2016), as listas saem com tamanhos
            # diferentes e o DataFrame quebrava ("All arrays must be of the same length", seção F de 22/10).
            # Só entram imagens com as duas propriedades; se ainda assim divergirem, para com mensagem clara.
            res = gi(col.filterDate(b0.strftime('%Y-%m-%d'), b1.strftime('%Y-%m-%d'))
                     .filter(ee.Filter.notNull(['creation_time', 'forecast_hours']))
                     .reduceColumns(ee.Reducer.toList().repeat(2), ['creation_time', 'forecast_hours']),
                     f'horas GFS {b0:%Y-%m-%d}')['list']
            if len(res[0]) != len(res[1]):
                raise RuntimeError(f'GFS {b0:%Y-%m-%d}: {len(res[0])} creation_time x {len(res[1])} forecast_hours')
            df = pd.DataFrame({'c': res[0], 'h': res[1]}).astype(float)
            df = df[(df['c'] % 86400000) == 0]                    # só rodadas 00Z
            for c, g in df.groupby('c'):
                out[ms_para_txt(c, horas=False)] = sorted({int(x) for x in g['h']})
        return out

    linhas, achadas = [], {}
    for nome, (ini, fim), teste in (('384h_1h_ate_120', ('2016-07-01', '2017-03-01'), tem_384),
                                     ('3h_de_243_a_384', ('2019-05-15', '2019-07-15'), tres_apos_240)):
        hs = horas_00z(ini, fim)
        dias = [x.strftime('%Y-%m-%d') for x in pd.date_range(ini, fim)]
        ok = [bool(hs.get(d)) and teste(hs[d]) for d in dias]
        achadas[nome] = detectar_transicao(dias, ok)
        linhas += [{'teste': nome, 'dia': d, 'imagens': len(hs.get(d) or []), 'hora_max': max(hs[d]) if hs.get(d) else None,
                    'tem_hora_0': 0 in (hs.get(d) or []), 'n_1_120': sum(1 for x in hs.get(d) or [] if 0 < x <= 120),
                    'n_243_384_3h': sum(1 for x in hs.get(d) or [] if 240 < x <= 384 and x % 3 == 0), 'passa': o}
                   for d, o in zip(dias, ok)]
        log(f'   {nome}: {sum(ok)} de {len(dias)} rodadas 00Z passam; transição em {achadas[nome][0]} '
            f'{achadas[nome][1]}'.rstrip())
    salvar_csv(pd.DataFrame(linhas).set_index(['teste', 'dia']), 'F_gfs_transicoes_dia_a_dia.csv')
    d384, d3h = achadas['384h_1h_ate_120'][0], achadas['3h_de_243_a_384'][0]
    CONTEXTO['gfs_384_desde'] = d384
    CONTEXTO['gfs_3h_apos_240_desde'] = d3h
    achado('F5', status_f5(d384, d3h, INICIO_RODADAS_03), 'GFS: datas reais das mudanças de saídas (rodadas 00Z)',
           f'384 h com saída horária até 120 h desde {d384}; saídas de 3 em 3 h entre 241 e 384 h desde {d3h}; '
           f'o 03 v4 usa rodadas desde {INICIO_RODADAS_03} (só GFS v16, decisão do usuário)',
           'Datas reais registradas como informação (ver F_gfs_transicoes_dia_a_dia.csv). OK quando o 03 começa depois '
           'das duas mudanças; antes do GFS v16 havia mais anos com a mesma estrutura de saídas, mas outro modelo.')


def radiacao_gfs():
    """Radiação do GFS: instantânea ou média do intervalo? Usa um ponto em Brasília numa rodada de inverno."""
    col = ee.ImageCollection(GFS)
    linhas = []
    for d in ('2025-07-15', '2025-01-15'):
        c = data_ms(d)
        run = col.filterDate(c, c + 3600 * 1000).filter(ee.Filter.eq('creation_time', c)) \
            .filter(ee.Filter.gt('forecast_hours', 0)).filter(ee.Filter.lte('forecast_hours', 48)) \
            .map(lambda i: i.set('system:time_start', i.get('forecast_time')))
        df = regiao_pontos(run, ['downward_shortwave_radiation_flux', 'temperature_2m_above_ground'],
                           [('Brasilia', -15.79, -47.88)], f'radiação {d}', escala=27830)
        df['hora_UTC'] = df['data'].dt.hour
        df['rodada'] = d
        linhas.append(df)
    t = pd.concat(linhas, ignore_index=True).sort_values(['rodada', 'data'])
    salvar_csv(t, 'F_gfs_radiacao_brasilia.csv')
    log_tabela(t[['rodada', 'data', 'hora_UTC', 'downward_shortwave_radiation_flux',
                  'temperature_2m_above_ground']].reset_index(drop=True), 'Radiação de onda curta em Brasília (W/m²):', 100)
    # Em Brasília (UTC-3) o sol se põe por volta das 21-21:30 UTC; às 23 e 00 UTC é noite.
    noite = t[t['hora_UTC'].isin([23, 0])]['downward_shortwave_radiation_flux']
    media = noite.mean()
    instant = media < 5
    # [22/10/2026] Desde a V1.4 o motor (05) e a matriz V2/V2.1 (03) já usam a média dos 4 blocos de 6 h
    # (horas múltiplas de 6): com radiação de bloco, F4 é a confirmação do tratamento, não um problema.
    achado('F4', 'INFO', 'GFS: natureza da radiação de onda curta',
           f'valor médio às 23 e 00 UTC (noite em Brasília): {media:.1f} W/m² -> '
           f'{"instantânea" if instant else "média acumulada do bloco de 6 h (não instantânea)"}',
           'O motor V1.4+ e a matriz GFS V2.1 já calculam a radiação pela média dos blocos de 6 h (horas '
           'múltiplas de 6), como a chuva; esta linha só confirma a natureza do dado.' if not instant else
           'Radiação instantânea: a média das saídas horárias seria a média do dia.',
           '' if not instant else 'Se o GFS mudar para radiação instantânea, revisar o 03 e o 05 (hoje usam blocos de 6 h).')
    CONTEXTO['radiacao_gfs_instantanea'] = instant


# =========================================================================
# G. ERA5-LAND
# =========================================================================
@secao('G', 'ERA5-Land: última data e grade')
def secao_g():
    col = ee.ImageCollection(ERA5)
    hoje = ee.Date(AGORA.strftime('%Y-%m-%d'))
    ult = gi(col.filterDate(hoje.advance(-150, 'day'), hoje.advance(1, 'day')).aggregate_max('system:time_start'), 'ERA5 último')
    atraso = (AGORA.date() - datetime.fromtimestamp(ult / 1000, tz=timezone.utc).date()).days
    achado('G1', 'OK' if atraso <= 12 else 'ATENÇÃO', 'ERA5-Land: último dia disponível',
           f'{ms_para_txt(ult)} ({atraso} dias atrás)')
    p_era = gi(ee.Image(col.first()).select('total_precipitation_sum').projection(), 'proj ERA5')
    p_br = gi(ee.Image(ee.ImageCollection(BR_DWGD).first()).select('pr').projection(), 'proj BR')
    log(f'   ERA5-Land: {p_era}\n   BR-DWGD:   {p_br}')
    t_e, t_b = p_era.get('transform'), p_br.get('transform')
    if t_e and t_b:
        off_x = ((t_e[2] + t_e[0] / 2) - (t_b[2] + t_b[0] / 2)) / t_b[0] % 1
        off_y = ((t_e[5] + t_e[4] / 2) - (t_b[5] + t_b[4] / 2)) / abs(t_b[4]) % 1
        meio = 0.4 < off_x < 0.6 or 0.4 < off_y < 0.6
        achado('G2', 'INFO', 'Grade ERA5-Land x grade SAB (BR-DWGD)',
               f'deslocamento dos centros em fração de pixel: x {off_x:.2f}, y {off_y:.2f} '
               f'({"meio pixel" if meio else "alinhadas"})',
               'Com meio pixel, vizinho mais próximo e bilinear diferem mais (ver D13).')
    else:
        achado('G2', 'NÃO EXECUTADO', 'Grade ERA5-Land x grade SAB', 'projeção sem transform')


# =========================================================================
# H. OISST E RONI
# =========================================================================
@secao('H', 'OISST e RONI')
def secao_h():
    col = ee.ImageCollection(OISST)
    hoje = ee.Date(AGORA.strftime('%Y-%m-%d'))
    rec = col.filterDate(hoje.advance(-60, 'day'), hoje.advance(1, 'day'))
    ult = gi(rec.aggregate_max('system:time_start'), 'OISST último')
    st = gi(rec.aggregate_histogram('status'), 'OISST status')
    achado('H1', 'INFO', 'OISST: último dia e status dos últimos 60 dias', f'{ms_para_txt(ult)} | {st}')

    geo = ee.Geometry.Rectangle([-179.99, -20, 179.99, 20])
    plano = ee.Geometry.Rectangle([-180, -20, 180, 20], None, False)
    a_geo = gi(geo.area(maxError=1), 'área geodésica') / 1e6
    a_pl = gi(plano.area(maxError=1), 'área plana') / 1e6
    achado('H2', 'ATENÇÃO' if a_geo < 1.5e8 else 'OK', 'Retângulo tropical do Código 1 e do painel antigos',
           f'área com a definição antiga {a_geo:,.0f} km² x plana {a_pl:,.0f} km² (esperado ~174 milhões)',
           'Área muito menor que a plana confirma que a média tropical antiga era calculada numa tira na linha '
           'de data.' if a_geo < 1.5e8 else 'A definição antiga já cobria a faixa tropical inteira: a correção '
           'das geometrias no RONI é só preventiva.')

    # RONI antigo x CPC
    try:
        cpc = pd.read_csv(URL_RONI_CPC, sep=r'\s+').rename(columns={'SEAS': 'Trimestre', 'YR': 'ano', 'ANOM': 'RONI_2c'})
    except Exception as e:
        achado('H3', 'NÃO EXECUTADO', 'RONI antigo x CPC', f'não foi possível baixar o arquivo do CPC ({e})')
        return
    ult_cpc = cpc.iloc[-1]
    achado('H3', 'INFO', 'Arquivo oficial do CPC (RONI.ascii.txt)', f'{len(cpc)} estações; última {ult_cpc["Trimestre"]} '
           f'{int(ult_cpc["ano"])} = {ult_cpc["RONI_2c"]}', 'A tabela do script 02 deve terminar na mesma estação.')
    props = [f['properties'] for f in gi(ee.FeatureCollection(RONI_ANTIGO), 'RONI antigo')['features']]
    log(f'   propriedades do asset RONI antigo: {sorted(props[0])}')
    ordem = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']
    if 'Year' in props[0]:
        antigo = pd.DataFrame(props).set_index('Year')[ordem].apply(pd.to_numeric, errors='coerce').stack().reset_index()
        antigo.columns = ['ano', 'Trimestre', 'valor']
        formato = 'largo (Year, DJF...)'
    else:
        col_v = 'ONI' if 'ONI' in props[0] else ('RONI' if 'RONI' in props[0] else None)
        antigo = pd.DataFrame(props).rename(columns={col_v: 'valor'})[['ano', 'Trimestre', 'valor']]
        formato = f'longo (ano, Trimestre, {col_v})'
    antigo['ano'] = antigo['ano'].astype(int)
    m = antigo.merge(cpc, on=['ano', 'Trimestre'], how='left')
    m['dif'] = (m['valor'] - m['RONI_2c']).abs()
    salvar_csv(m, 'H_roni_antigo_x_cpc.csv')
    n_dif = int((m['dif'] > 0.051).sum())
    achado('H4', 'OK' if n_dif == 0 else 'ATENÇÃO', 'Asset RONI antigo x RONI oficial do CPC (ERSSTv6)',
           f'formato {formato}; {len(m)} estações ({m["ano"].min()}-{m["ano"].max()}); {n_dif} diferem mais que o '
           f'arredondamento (maior diferença {m["dif"].max():.2f})',
           'Diferenças mostram que o asset antigo não é a série oficial atual; o painel novo usa RONI_CPC_v6.')


# =========================================================================
# H5. [V4 M08-09] RONI_CPC_v6 x CPC (seção própria, roda junto com 'H')
# =========================================================================
@secao('H5', 'RONI_CPC_v6 x arquivo oficial do CPC')
def secao_h5():
    titulo = 'RONI_CPC_v6 x RONI.ascii.txt do CPC (valores, mês central, time_start, continuidade, chave do painel)'
    if not existe(RONI_NOVO):
        achado('H5', 'ATENÇÃO', titulo, 'asset RONI_CPC_v6 não existe', 'O painel 2026.10.4 lê o RONI_CPC_v6.',
               'Rode o 02.')
        return
    try:
        cpc = pd.read_csv(URL_RONI_CPC, sep=r'\s+').rename(columns={'SEAS': 'Trimestre', 'YR': 'ano', 'ANOM': 'RONI_2c'})
    except Exception as e:
        achado('H5', 'NÃO EXECUTADO', titulo, f'não foi possível baixar o arquivo do CPC ({e})')
        return
    fc = ee.FeatureCollection(RONI_NOVO).map(lambda f: f.set('t_ms', f.get('system:time_start')))
    novo = pd.DataFrame([f['properties'] for f in gi(fc, 'RONI_CPC_v6')['features']])
    log(f'   RONI_CPC_v6: {len(novo)} estações; propriedades {sorted(novo.columns)}')
    try:   # a mesma conta da chave_join do painel (06), nas 3 primeiras estações
        amostra = ee.FeatureCollection(RONI_NOVO).sort('data_ms').limit(3).map(   # [V4 revisão B-06]
            
            lambda f: f.set('chave_painel', ee.Number(f.get('ano')).format('%04d').cat('_')
                            .cat(ee.Number(f.get('mes')).format('%02d'))))
        chaves = [(p.get('ano'), p.get('mes'), p.get('chave_painel'))
                  for p in (f['properties'] for f in gi(amostra, 'chave do painel')['features'])]
        log(f'   chave do painel nas 3 primeiras estações: {[c[2] for c in chaves]}')
    except Exception as e:
        log(f'   chave do painel não calculada: {type(e).__name__}: {str(e)[:200]}')
        chaves = []
    status, problemas = avaliar_roni(novo, cpc, chaves)
    for p in problemas:
        log(f'   problema: {p}')
    ult = novo.sort_values(['ano', 'mes']).iloc[-1] if len(novo) else None
    achado('H5', status, titulo,
           f'{len(novo)} estações no asset x {len(cpc)} no CPC; última no asset '
           f'{ult["Trimestre"] if ult is not None else "?"} {int(ult["ano"]) if ult is not None else "?"}; ' +
           ('tudo confere' if not problemas else f'{len(problemas)} problema(s): {problemas[:3]}'),
           'O painel monta a série ENSO e o filtro histórico com este asset.',
           '' if status == 'OK' else 'Rode o 02 (e confira o compartilhamento do asset se o App estiver publicado).')


# =========================================================================
# I. BASELINES
# =========================================================================
@secao('I', 'Pasta Baselines')
def secao_i():
    if not existe(BASELINES):
        achado('I1', 'INFO', 'Pasta Baselines', 'não existe')
        return
    itens = listar_assets(BASELINES)
    linhas = []
    for a in itens:
        n, versoes = None, None
        if a['tipo'] == 'IMAGE_COLLECTION':
            c = ee.ImageCollection(a['caminho']).map(lambda i: i.set('v', ee.Algorithms.If(
                i.propertyNames().contains('versao_baseline'), i.get('versao_baseline'), 'SEM_VERSAO')))
            n = gi(c.size(), f"tamanho {a['nome']}")
            versoes = gi(c.aggregate_histogram('v'), f"versões {a['nome']}") if n else {}
        linhas.append({'item': a['nome'], 'tipo': a['tipo'], 'imagens': n, 'versoes': versoes})
    tab = pd.DataFrame(linhas).set_index('item')
    log_tabela(tab, 'Conteúdo da pasta Baselines:')
    salvar_csv(tab, 'I_baselines.csv')
    com_imagens = tab[tab['imagens'].fillna(0) > 0]
    CONTEXTO['versoes_baselines'] = {v for d in com_imagens['versoes'] for v in (d or {})}   # [V4 M08-08]
    achado('I1', 'OK' if com_imagens.empty else 'ATENÇÃO', 'Baselines: coleções já com imagens',
           'todas vazias' if com_imagens.empty else f'{com_imagens["imagens"].to_dict()} versões '
           f'{com_imagens["versoes"].to_dict()}',
           'Os scripts de normais pulam imagens existentes; imagens de versão antiga ficariam misturadas com a B1.1b.')


# =========================================================================
# Q1. [V4 Q1] MÁSCARA DE QUALIDADE (gerada pelo 01)
# =========================================================================
@secao('Q1', 'Máscara de qualidade dos pixels (SAB_MASCARA_QUALIDADE)')
def secao_q1():
    titulo = 'Máscara de qualidade: classes 1-4, propriedades, grade e igualdade com as classes recalculadas'
    if not RODAR_Q1:
        achado('Q1', 'NÃO EXECUTADO', titulo, 'desligada (RODAR_Q1 = False)')
        return
    if not existe(ASSET_MASCARA):
        achado('Q1', 'ATENÇÃO', titulo, 'SAB_MASCARA_QUALIDADE não existe',
               'O painel 2026.10.4 exclui os pixels de classe 4 e informa a classe no CSV a partir desta máscara.',
               'Rode o 01.')
        return
    props = ee.data.getAsset(ASSET_MASCARA).get('properties') or {}
    img = ee.Image(ASSET_MASCARA).select('classe')
    proj = gi(img.projection(), 'projeção da máscara')
    r = rr(ee.Image.cat([img.eq(k).rename(f'n_classe_{k}') for k in (1, 2, 3, 4)]), ee.Reducer.sum().unweighted(),
           'contagem da máscara', geom=REGIAO_AMPLA)
    cont = {k: int(round(r.get(f'n_classe_{k}') or 0)) for k in (1, 2, 3, 4)}
    abc = codigo_abc(classes_pixel(Q1_DIA))
    m3 = img.where(img.eq(4), 3).unmask(0)
    # [V4.1 K1a] Pixel B da máscara que está igual ao BR-DWGD neste dia é coincidência (dia seco, ETo baixa), não erro
    coinc = m3.eq(2).And(abc.eq(1))
    rd = rr(ee.Image.cat([abc.neq(m3).And(coinc.Not()).rename('dif'), coinc.rename('coinc')]),
            ee.Reducer.sum().unweighted(), f'máscara x classes de {Q1_DIA}', geom=REGIAO_AMPLA)
    n_dif = int(round(rd.get('dif') or 0))
    n_coinc = int(round(rd.get('coinc') or 0))
    log(f'   propriedades: {props}')
    log(f'   pixels por classe (unweighted): {cont}; referência K1d: classe 3 perto de {K1D_C_DENTRO} e classe 4 perto '
        f'de {J1_C_FORA_APROX}; pixels com classe diferente da recalculada em {Q1_DIA}: {n_dif}; pixels B iguais ao '
        f'BR-DWGD neste dia (coincidência, ignorados): {n_coinc}')
    prob = checar_q1(props, cont, proj.get('transform'), n_dif, n_coinc)
    achado('Q1', 'OK' if not prob else 'ATENÇÃO', titulo,
           f'A {cont[1]}, B {cont[2]}, C dentro {cont[3]}, C fora {cont[4]}; ' +
           ('confere' if not prob else f'{len(prob)} problema(s): {prob[:3]}'),
           'A máscara vale para todo o histórico (as classes da J1 são iguais em todos os dias).',
           '' if not prob else 'Confira o asset; se for preciso refazer, apague-o e rode o 01.')


# =========================================================================
# J. [V4] ITENS PERMANENTES DA AUDITORIA COMPLEMENTAR J
# =========================================================================
@secao('J1', 'Classes de pixel do histórico (J1 permanente)')
def secao_j1():
    titulo = 'Histórico: classes de pixel A/B/C/D (B = BR-DWGD descartado; C = sem BR-DWGD)'
    if not RODAR_J1:
        achado('J1', 'NÃO EXECUTADO', titulo, 'desligada (RODAR_J1 = False)')
        return
    dias = [('historico', d) for d in J1_DIAS]
    inv = inventario_2026()
    defin = inv[inv['versao'] == 'definitiva']['dia'].tolist() if len(inv) else []
    if defin:
        idx = np.linspace(0, len(defin) - 1, min(len(defin), 3)).round().astype(int)
        dias += [('definitiva_2026', defin[i]) for i in sorted(set(idx))]
    linhas = []
    for tipo, d in dias:
        if not gi(ee.ImageCollection(BR_DWGD).filterDate(d, ee.Date(d).advance(1, 'day')).size(), f'BR-DWGD {d}'):
            log(f'   {d}: sem BR-DWGD neste dia; pulado')
            continue
        cl = classes_pixel(d, completo=False)     # conta exata da J1: soma padrão nos limites dos estados, como na J
        s = rr(ee.Image.cat([v.rename(k) for k, v in cl.items()]), ee.Reducer.sum(), f'classes {d}',
               geom=UF_BR.geometry().bounds())
        linhas.append({'tipo': tipo, 'dia': d, **{k: int(round(s.get(k) or 0)) for k in cl}})
        log(f'   {d} ({tipo}): A {linhas[-1]["A"]} | B {linhas[-1]["B"]} | C {linhas[-1]["C"]} | D {linhas[-1]["D"]}')
    if not linhas:
        achado('J1', 'NÃO EXECUTADO', titulo, f'nenhum dos dias {J1_DIAS} tem BR-DWGD')
        return
    t = pd.DataFrame(linhas).set_index('dia')
    salvar_csv(t, 'J1_classes_por_dia.csv')
    st_h, st_26 = avaliar_j1(linhas)
    hist = t[t['tipo'] == 'historico']
    achado('J1', st_h, titulo,
           f'{len(hist)} dias: B {sorted(set(hist["B"]))}, C {sorted(set(hist["C"]))}, A {sorted(set(hist["A"]))}, '
           f'D {sorted(set(hist["D"]))} (esperado C {J1_ESPERADO["C"]} e A + B {J1_ESPERADO["AB"]} constantes; '
           f'B de {J1_ESPERADO["B"] - J1_TOL_B} a {J1_ESPERADO["B"] + 1})',
           'Pixels B e C são tratados pela máscara de qualidade (Q1); a trava do histórico não é aberta. B um pouco '
           'abaixo de 204 num dia é coincidência (K1a); C ou A + B diferentes indicam que o histórico ou o BR-DWGD mudou.')
    if st_26:
        d26 = t[t['tipo'] == 'definitiva_2026']
        achado('J1-2026', st_26, 'Dias definitivos de 2026: pixels B (BR-DWGD descartado)',
               f'B {d26["B"].to_dict()} (esperado 0 com o motor V1.5)',
               'Na rota definitiva V1.5, onde o BR-DWGD existe o SAB deve ser igual a ele.')


@secao('J3', 'Nomes de estados do Brasil repetidos em outros países no GAUL')
def secao_j3():
    nomes = [n for n in gi(UF_BR.aggregate_array('ADM1_NAME'), 'nomes UF') if n != 'Name Unknown']
    estr = GAUL1.filter(ee.Filter.inList('ADM1_NAME', nomes)).filter(ee.Filter.neq('ADM0_NAME', 'Brazil'))
    lst = gi(estr.reduceColumns(ee.Reducer.toList().repeat(2), ['ADM1_NAME', 'ADM0_NAME']), 'homônimos')['list']
    t = pd.DataFrame({'estado_BR': lst[0], 'pais': lst[1]}).drop_duplicates()
    if len(t):
        log_tabela(t.set_index('estado_BR'), 'Estados do Brasil com o mesmo nome em outro país (GAUL level1):')
        salvar_csv(t.set_index('estado_BR'), 'J3_homonimos_GAUL.csv')
    achado('J3', 'INFO', 'GAUL: nomes de estados do Brasil repetidos em outros países',
           f'{t.values.tolist()}' if len(t) else 'nenhum',
           'O painel 2026.10.4 filtra estados e municípios também pelo país (ADM0_NAME = Brazil); nas versões '
           'anteriores esses polígonos estrangeiros entravam na seleção. "Name Unknown" não conta como homônimo.')


@secao('J5', 'Tmax nacional dos dias de 2026 (recorde, emenda ERA5 -> GFS e GFS x ERA5)')
def secao_j5():
    if not RODAR_J5:
        achado('J5', 'NÃO EXECUTADO', 'Tmax nacional dos dias de 2026', 'desligada (RODAR_J5 = False)')
        return

    def tmax_dia(img):
        s = padronizar_sab(img).select('tmax_C')
        r = (ee.Image.cat([s, s.gt(40).rename('acima40'), s.gt(42).rename('acima42')]).updateMask(MASCARA_BR)
             .reduceRegion(reducer=ee.Reducer.max().combine(ee.Reducer.mean(), sharedInputs=True), geometry=LIMITES,
                           crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4))
        d = img.toDictionary()
        return ee.Feature(None, r).set({'t': img.get('system:time_start'), 'versao': d.get('versao', 'definitiva'),
                                        'alg': d.get('versao_algoritmo', 'V1.0')})

    fim = (datetime.now(timezone.utc) + timedelta(days=40)).strftime('%Y-%m-%d')
    props = []
    for m0 in pd.date_range('2026-01-01', fim, freq='MS'):      # uma consulta por mês, calculada no servidor
        m1 = (m0 + pd.offsets.MonthBegin(1)).strftime('%Y-%m-%d')
        fc = ee.FeatureCollection(ee.ImageCollection(SAB).filterDate(m0.strftime('%Y-%m-%d'), m1).map(tmax_dia))
        props += [f['properties'] for f in gi(fc, f'Tmax {m0:%Y-%m}')['features']]
    if not props:
        achado('J5', 'INFO', 'Tmax nacional dos dias de 2026', 'nenhum dia de 2026 no SAB_V1')
        return
    df = pd.DataFrame(props).reindex(columns=['t', 'versao', 'alg', 'tmax_C_max', 'tmax_C_mean', 'acima40_mean',
                                              'acima42_mean'])        # dia todo mascarado volta sem as estatísticas
    num = df[['tmax_C_max', 'tmax_C_mean', 'acima40_mean', 'acima42_mean']].apply(pd.to_numeric, errors='coerce')
    t = pd.DataFrame({'versao': df['versao'].values, 'alg': df['alg'].values,
                      'tmax_max': num['tmax_C_max'].values, 'tmax_media': num['tmax_C_mean'].values,
                      'pct_acima40': 100 * num['acima40_mean'].values, 'pct_acima42': 100 * num['acima42_mean'].values},
                     index=pd.Index(pd.to_datetime(df['t'].astype('float64'), unit='ms', utc=True)
                                    .dt.strftime('%Y-%m-%d').values, name='dia')).sort_index().round(2)
    ant = None                                # lido antes de gravar o CSV desta execução (pode ser o mesmo caminho)
    if J5_CSV_ANTERIOR and os.path.isfile(J5_CSV_ANTERIOR):
        ant = pd.read_csv(J5_CSV_ANTERIOR, sep=';', decimal=',', encoding='utf-8-sig', index_col='dia')
    salvar_csv(t, 'J5_tmax_2026.csv')         # mesmo formato da J: serve de J5_CSV_ANTERIOR numa execução futura
    log_tabela(t[t['versao'] != 'provisoria_era5'], 'Tmax no Brasil nos dias de 2026 que não são ERA5 (todos no CSV):', 60)
    g = t.groupby(['versao', 'alg'])[['tmax_max', 'tmax_media', 'pct_acima40', 'pct_acima42']].mean().round(2)
    g['dias'] = t.groupby(['versao', 'alg']).size()
    log_tabela(g, 'Médias por versão e algoritmo:')
    acima = dias_acima_recorde(t)
    achado('J5a', 'ATENÇÃO' if acima else 'OK', f'Tmax máxima nacional acima do recorde do INMET ({RECORDE_TMAX_BR} °C)',
           f'{len(acima)} dia(s): {[(d, v, t.loc[d, "versao"]) for d, v in acima][:10]}' if acima else
           f'nenhum dia; maior {t["tmax_max"].max()} °C em '
           f'{t["tmax_max"].dropna().idxmax() if t["tmax_max"].notna().any() else "?"}',
           'Recorde nacional: 44,8 °C em Araçuaí-MG, 19/11/2023. Valores acima dele, em pixels de 0,1°, indicam viés '
           'da calibração (na V1, a previsão GFS ficou cerca de 3 °C acima dos dias ERA5).')
    e = salto_emenda(t)
    if e is None:
        achado('J5b', 'INFO', 'Emenda ERA5 -> GFS: salto da Tmax máxima nacional', 'sem dias ERA5 seguidos de dias GFS')
    else:
        achado('J5b', 'ATENÇÃO' if e['atencao'] else 'OK', 'Emenda ERA5 -> GFS: salto da Tmax máxima nacional',
               f'{e["dia_era5"]} (ERA5) {e["tmax_era5"]:.2f} °C -> {e["dia_gfs"]} (GFS) {e["tmax_gfs"]:.2f} °C: salto '
               f'{e["salto"]:+.2f} °C (limite {SALTO_EMENDA_MAX_C} °C); dias entre os dois: {e["dias_entre"]}',
               'Salto grande na troca de fonte é degrau artificial na série que o painel mostra.')
    if ant is not None:
        cmp = comparar_gfs_x_era5(ant, t)
        if len(cmp):
            log_tabela(cmp, f'Mesmas datas: previsão GFS ({os.path.basename(J5_CSV_ANTERIOR)}) x ERA5 de hoje:')
            salvar_csv(cmp, 'J5_gfs_x_era5_mesmas_datas.csv')
            vies = cmp['dif_tmax_max'].mean()
            achado('J5c', 'ATENÇÃO' if abs(vies) > SALTO_EMENDA_MAX_C else 'INFO',
                   'Tmax máxima nacional: previsão GFS x ERA5 nas mesmas datas',
                   f'{len(cmp)} dia(s); viés médio GFS - ERA5 {vies:+.2f} °C na máxima, '
                   f'{cmp["dif_tmax_media"].mean():+.2f} °C na média nacional',
                   f'Viés médio acima de {SALTO_EMENDA_MAX_C} °C na máxima repete o problema da calibração GFS V1.')
        else:
            achado('J5c', 'INFO', 'Tmax máxima nacional: previsão GFS x ERA5 nas mesmas datas',
                   'nenhuma data que era GFS no CSV anterior já virou ERA5')
    else:
        achado('J5c', 'INFO', 'Tmax máxima nacional: previsão GFS x ERA5 nas mesmas datas',
               'sem CSV anterior' + (f' (não achei {J5_CSV_ANTERIOR})' if J5_CSV_ANTERIOR else ''),
               'Para comparar, envie ao Colab o J5_tmax_2026.csv de uma execução anterior com o nome '
               'J5_previsao_anterior.csv (pasta /content): os dias GFS são substituídos pelo ERA5 quando ele chega.')


# =========================================================================
# EXECUÇÃO E RESUMO
# =========================================================================
def gravar_resumo(interrompida=None):
    """[V4 M08-01] Resumo, JSON e .zip; chamado sempre (finally), mesmo se a execução for interrompida."""
    resumo = pd.DataFrame(ACHADOS, columns=['codigo', 'status', 'titulo', 'resultado', 'significado', 'acao_sugerida',
                                            'status_original'])
    resumo['ordem'] = resumo['status'].map(ORDEM_STATUS)
    resumo = resumo.sort_values(['ordem', 'codigo']).drop(columns='ordem').reset_index(drop=True)
    resumo.to_csv(os.path.join(PASTA, 'RESUMO_ACHADOS.csv'), sep=';', index=False, encoding='utf-8-sig')
    with open(os.path.join(PASTA, 'RESUMO_ACHADOS.json'), 'w', encoding='utf-8') as f:
        json.dump(ACHADOS, f, ensure_ascii=False, indent=1, default=str)

    log('\n' + '=' * 100)
    log(f'RESUMO DA AUDITORIA | {len(resumo)} itens | {(time.time() - inicio_total) / 60:.0f} min')
    log('=' * 100)
    if interrompida:
        log(f'⏸️ EXECUÇÃO INTERROMPIDA NA SEÇÃO {interrompida}: o resumo cobre só o que rodou até ali.')
    log(f'contagem por status: {resumo["status"].value_counts().to_dict()}')
    for _, r in resumo.iterrows():
        simbolo = {'OK': '✅', 'ATENÇÃO': '⚠️', 'ERRO': '❌', 'INFO': 'ℹ️', 'NÃO EXECUTADO': '⏭️'}[r['status']]
        log(f'{simbolo} [{r["codigo"]}] {r["titulo"]}: {r["resultado"]}')
    log('\nNada foi gravado no Earth Engine (trava de somente leitura ativa durante toda a execução).')

    arq_zip = shutil.make_archive(PASTA, 'zip', PASTA)
    log(f'📦 Pacote com log, resumo e tabelas: {arq_zip}')
    try:
        from google.colab import files
        files.download(arq_zip)
    except Exception:
        log('   (download automático indisponível; baixe pelo painel Arquivos do Colab)')


inicio_total = time.time()
secao_em_curso = None                                  # [V4 M08-01]
try:
    for codigo, titulo, fn in SECOES:
        # [V4] a letra roda a seção e as novas dela ('D' roda D e D14); o código roda só aquela ('D14')
        if SECOES_A_RODAR and codigo not in SECOES_A_RODAR and codigo[0] not in SECOES_A_RODAR:
            continue
        secao_em_curso = codigo
        log('\n' + '=' * 100)
        log(f'SEÇÃO {codigo}: {titulo}')
        log('=' * 100)
        t0 = time.time()
        try:
            fn()
        except Exception as e:
            achado(codigo, 'NÃO EXECUTADO', f'Seção {codigo} interrompida', f'{type(e).__name__}: {str(e)[:300]}',
                   'As demais seções continuam. Ver o traceback no log.')
            log(traceback.format_exc())
        log(f'   ⏱️ seção {codigo}: {(time.time() - t0) / 60:.1f} min')
    secao_em_curso = None
except KeyboardInterrupt:                              # [V4 M08-01] interrupção pelo usuário (botão parar)
    log(f'\n⏸️ Execução interrompida pelo usuário na seção {secao_em_curso}.')
    achado(secao_em_curso or '-', 'NÃO EXECUTADO', 'Execução interrompida pelo usuário',
           f'interrompida na seção {secao_em_curso}; as seções seguintes não rodaram')
finally:
    gravar_resumo(secao_em_curso)
