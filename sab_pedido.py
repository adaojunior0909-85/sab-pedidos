# >>> SAB: ATENDIMENTO AUTOMÁTICO DOS PEDIDOS POR E-MAIL (rotina do GitHub Actions). Versão 2026.11.18 <<<
# =========================================================================================
# O QUE FAZ
#   Recebe UM pedido (painel SAB ou formulário -> Apps Script -> GitHub) e manda o Earth Engine exportar os
#   CSV para uma pasta própria do pedido no Google Drive do dono do projeto:
#       SAB_pedido_<ID>/00_Pedido_<ID>.csv              manifesto: o que foi pedido e a lista de arquivos
#       SAB_pedido_<ID>/00_Dicionario_Variaveis_SAB.csv o dicionário das colunas
#       SAB_pedido_<ID>/Diaria_<Local>_<Ano>.csv        um arquivo por local e por ano, como o painel
#   Termina em 1 a 3 minutos: só ENVIA as exportações. O Earth Engine as processa na fila dele, e o
#   Apps Script entrega o link quando todos os arquivos do manifesto estiverem na pasta. Quem pediu Excel
#   recebe também os .xlsx, feitos depois pela rotina sab_xlsx.py.
#
# [2026.11.18] PEDIDO DE UMA VARIÁVEL SÓ SAÍA COM A COLUNA VAZIA. Com uma banda só, o reduceRegions do Earth Engine
#   grava a média na propriedade 'mean' (nome do redutor), e não 'pr_mm' (nome da banda); o formatar() procurava
#   'pr_mm', não achava e deixava a célula vazia em todas as linhas (diário e mensal; qualquer variável sozinha).
#   Agora o redutor recebe o nome da banda (_redutor_media). Pedidos de 2 ou mais variáveis não mudam (K16 igual).
# [2026.11.03] MESMO CÁLCULO DO PAINEL 2026.11.1: correção de leitura dos pixels B (núcleo do BR-DWGD) e da radiação dos
#   pixels C (limitada à de céu claro, FAO-56), só nos dias de 1961 a 2025 e só quando a área tem pixel B ou C
#   (função corrigir_pixels_b). K16 com o caso A6 (Lagoa dos Patos). O banco não muda.
# MESMO CÁLCULO DO PAINEL 2026.10.4 (revisão 18h30 de 22/10)
#   Grade, coleção, correções V1.0, grampo termodinâmico, linhas e formatação são os da K14, que saiu
#   idêntica ao link do painel (caso C0). As colunas do painel saem iguais (K16); as diferenças de propósito são:
#     - um ano com mais de 1.000.000 de linhas (limite do Excel) é dividido em blocos de meses;
#     - [2026.11.01] as colunas ENSO vão SEMPRE no fim do CSV (com ou sem filtro), mais a coluna Fonte_ENSO;
#       os meses depois do último trimestre calculável e os dias de previsão recebem a estimativa mais recente
#       (Estimativa_OISST_parcial ou Persistencia), marcada em Fonte_ENSO. O painel continua como estava;
#     - [2026.11.01] o Brasil inteiro (tipo=BR) saiu: estourou a memória do Earth Engine em 31/10/2026.
#   Filtro ENSO (enso=<cenário>): a mesma série e regra do painel (RONI oficial do CPC + estimativa OISST depois
#     da última estação oficial; episódio de 5 estações). Só meses com Fonte CPC ou Estimativa_OISST entram nos
#     filtros, como no painel; os dias de previsão entram sempre.
#   Toda mudança no cálculo do painel exige mudar este arquivo e repetir a K16 (identidade).
#
# CÓDIGO DO PEDIDO (gerado pelo painel ou pelo formulário; campos separados por ";")
#   v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-12-31;var=todas
#   v=1;res=M;tipo=M;uf=Paraná;mun=Pato Branco,Clevelândia;ini=1991-01-01;fim=2020-12-31;var=pr,tmax,tmin;fmt=xlsx
#   v=1;res=D;tipo=P;pol=-26.1 -52.7,-26.1 -52.6,-26.2 -52.6,-26.2 -52.7;ini=2025-01-01;fim=2025-03-31;var=todas
#   v=1;res=D;tipo=C;pts=-26.2285 -52.6712 Fazenda A|-25.4 -49.27 Curitiba;ini=2024-01-01;fim=2024-12-31;var=todas
#     res: D diária, M mensal | tipo: E estados, M municípios, P polígonos ("lat lon", vértices separados por ","
#     e polígonos por "|"), C pontos ("lat lon nome", separados por "|"; cada ponto vira o pixel de 0,1° que o
#     contém) | var: "todas" ou os códigos de VARIAVEIS abaixo | fmt: csv (padrão), xlsx ou ambos (só a entrega
#     muda; o cálculo é o mesmo) | enso: sufixo de ENSO_CENARIOS (sem enso = sem filtro).
#   Estados com sep=1 (pedidos do formulário): uma grade e um arquivo por estado (sem sep, vários estados formam
#   uma grade só, Grupo_Estados, como no painel). No máximo LIMITE_ESTADOS estados por pedido.
#   Municípios: o nome é procurado no GAUL sem ligar para acento, maiúscula ou hífen ("clevelandia" acha
#   "Clevelândia"); se não achar, a recusa sugere nomes parecidos.
#   Antes de qualquer cálculo no Earth Engine, o tamanho é estimado pela área (estimar_linhas): um pedido muito
#   acima do limite é recusado na hora, sem gastar memória do Earth Engine.
#
# EXECUÇÃO: pelo GitHub Actions (.github/workflows/pedido_sab.yml), com as variáveis de ambiente
#   PEDIDO_ID, CODIGO e SIMULAR (1 = só confere e mostra o plano, sem exportar nada).
#   No computador ou no Colab: PEDIDO_ID=TESTE01 CODIGO='v=1;...' SIMULAR=1 python sab_pedido.py
# NÃO GRAVA NADA NO EARTH ENGINE: só CSV no Drive. Não toca no SAB_V1 nem em asset algum.
# =========================================================================================
import difflib
import math
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone

VERSAO_ROTINA = '2026.11.18'
VERSAO_PAINEL = '2026.10.4 (revisao 18h30 de 22/10/2026)'

# ------------------------------------------------------------------ parâmetros
PROJETO = 'clima-492922'
SAB = f'projects/{PROJETO}/assets/SAB_V1'
MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
SOLO = f'projects/{PROJETO}/assets/SICSB_SOLO_2015_2025'
BRDWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'           # [2026.11.03] CORR_B do painel 2026.11.1
ELEVACAO = 'USGS/SRTMGL1_003'
FIM_HISTORICO_CORRECAO = '2026-01-01'                           # exclusivo: só os dias até 31/12/2025
NUCLEO_B = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'rs', 'u2', 'vpd']
ESCALA_AREA = 11132          # CFG.escalaArea do painel (Estados / Municípios e grade)
ESCALA_PONTO = 1000          # CFG.escalaPonto do painel (Coordenadas)
LIMITE_PONTOS_GRADE = 25000  # CFG.limitePontosGrade do painel (pares pixel x polígono)
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
DATA_MINIMA = date(1961, 1, 1)
LIMITE_LINHAS_ARQUIVO = 1_000_000    # o Excel abre até 1.048.576 linhas
LIMITE_LINHAS_PEDIDO = 10_000_000    # ~2,3 GB de CSV com todas as variáveis (protege o Drive de 15 GB)
LIMITE_ARQUIVOS = 400
LIMITE_ESTADOS = 6                   # [2026.11.01] o Brasil inteiro estourou a memória do Earth Engine (31/10)
FOLGA_ESTIMATIVA = 1.5               # recusa na hora se a estimativa pela área passar de 1,5 x o limite de linhas
LIMITE_PONTOS = 200
LIMITE_MUNICIPIOS = 30
LIMITE_POLIGONOS = 10
LIMITE_VERTICES = 150
BRT = timezone(timedelta(hours=-3))

ESTADOS = {  # dicionario_regioes do painel
    'Norte': ['Acre', 'Amapá', 'Amazonas', 'Pará', 'Rondônia', 'Roraima', 'Tocantins'],
    'Nordeste': ['Alagoas', 'Bahia', 'Ceará', 'Maranhão', 'Paraíba', 'Pernambuco', 'Piauí', 'Rio Grande do Norte',
                 'Sergipe'],
    'Centro-Oeste': ['Distrito Federal', 'Goiás', 'Mato Grosso', 'Mato Grosso do Sul'],
    'Sudeste': ['Espírito Santo', 'Minas Gerais', 'Rio de Janeiro', 'São Paulo'],
    'Sul': ['Paraná', 'Rio Grande do Sul', 'Santa Catarina']}
LISTA_ESTADOS = [e for lista in ESTADOS.values() for e in lista]
# [2026.11.01] Área (km², IBGE) e latitude do centro de cada estado: só para estimar o número de pixels de 0,1° antes
# de chamar o Earth Engine (pixel de 0,1° ~ 123,9 km² x cos(latitude)). A grade real conta ~5 a 10% a mais (borda).
AREA_LAT_ESTADO = {
    'Acre': (164124, -9.0), 'Alagoas': (27830, -9.6), 'Amapá': (142471, 1.4), 'Amazonas': (1559256, -4.0),
    'Bahia': (564760, -12.5), 'Ceará': (148894, -5.2), 'Distrito Federal': (5760, -15.8),
    'Espírito Santo': (46074, -19.6), 'Goiás': (340203, -16.0), 'Maranhão': (329642, -5.0),
    'Mato Grosso': (903207, -13.0), 'Mato Grosso do Sul': (357146, -20.5), 'Minas Gerais': (586514, -18.5),
    'Pará': (1245870, -4.0), 'Paraíba': (56467, -7.2), 'Paraná': (199298, -24.6), 'Pernambuco': (98068, -8.4),
    'Piauí': (251756, -7.5), 'Rio de Janeiro': (43750, -22.3), 'Rio Grande do Norte': (52810, -5.8),
    'Rio Grande do Sul': (281707, -30.0), 'Rondônia': (237765, -10.9), 'Roraima': (223644, 2.0),
    'Santa Catarina': (95731, -27.3), 'São Paulo': (248219, -22.2), 'Sergipe': (21926, -10.6),
    'Tocantins': (277467, -10.2)}
FORMATOS = {'csv': 'CSV', 'xlsx': 'Excel (.xlsx)', 'ambos': 'CSV e Excel (.xlsx)'}

# código -> (coluna do CSV, banda, casas decimais, grupo), na ORDEM das colunas do painel
VARIAVEIS = [
    ('pr', 'Precipitacao_mm', 'pr_mm', 2, 'Chuva e escoamento'),
    ('ce', 'Chuva_Efetiva_mm', 'chuva_efetiva', 2, 'Chuva e escoamento'),
    ('rsup', 'Runoff_Superficial_mm', 'runoff_sup_mm', 2, 'Chuva e escoamento'),
    ('rsub', 'Runoff_Subsuperficial_mm', 'runoff_sub_mm', 2, 'Chuva e escoamento'),
    ('tmax', 'Temperatura_Maxima_C', 'tmax_C', 2, 'Temperatura'),
    ('tmin', 'Temperatura_Minima_C', 'tmin_C', 2, 'Temperatura'),
    ('amp', 'Amplitude_Termica_C', 'amplitude_diaria', 2, 'Temperatura'),
    ('tsolo', 'Temperatura_Solo_C', 'tsolo_C', 2, 'Temperatura'),
    ('tfolha', 'Temperatura_Folha_C', 'tfolha_C', 2, 'Temperatura'),
    ('ur', 'Umidade_Relativa_Porc', 'RH', 2, 'Ar e radiação'),
    ('vento', 'Vento_ms', 'u2', 2, 'Ar e radiação'),
    ('rad', 'Radiacao_Solar_MJ_m2', 'rs', 2, 'Ar e radiação'),
    ('etp', 'Evapotranspiracao_Potencial_mm', 'et_potencial', 2, 'Balanço hídrico'),
    ('etr', 'Evapotranspiracao_Real_mm', 'et_real', 2, 'Balanço hídrico'),
    ('transp', 'Transpiracao_Planta_mm', 'transpiracao_mm', 2, 'Balanço hídrico'),
    ('def', 'Deficit_Hidrico_mm', 'deficit_diario', 2, 'Balanço hídrico'),
    ('dpv', 'Deficit_Pressao_Vapor_kPa', 'vpd', 2, 'Ar e radiação'),
    ('us5', 'Umidade_Volumetrica_Solo_0_5cm_m3_m3', 'soil_moisture_0_5cm_m3_m3', 3, 'Umidade do solo'),
    ('us100', 'Umidade_Volumetrica_Solo_0_100cm_m3_m3', 'soil_moisture_0_100cm_m3_m3', 3, 'Umidade do solo')]
CODIGOS = [v[0] for v in VARIAVEIS]
COLUNAS_ID = ['Tipo_Dado', 'Versao_Algoritmo', 'Data_Completa', 'Ano', 'Mes', 'Dia', 'N_Ponto', 'Latitude',
              'Longitude', 'Estado', 'Municipio']
EXTRAS_DIARIA = ['Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo']
EXTRAS_MENSAL = ['N_Dias', 'Dias_no_Mes', 'Mes_Completo']
BANDAS_SAB = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2', 'tsolo_C',
              'tfolha_C', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm',
              'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
BANDAS_ANTIGAS = ['precipitation_mm', 'temp_max_C', 'temp_min_C', 'relative_humidity_pct', 'et_potential_mm',
                  'et_actual_mm', 'vpd_kpa', 'solar_radiation_mj_m2', 'wind_speed_m_s', 'soil_temperature_C',
                  'skin_temperature_C', 'transpiration_mm', 'surface_runoff_mm', 'subsurface_runoff_mm',
                  'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
BANDAS_SOMA = ['pr_mm', 'chuva_efetiva', 'runoff_sup_mm', 'runoff_sub_mm', 'et_potencial', 'et_real',
               'transpiracao_mm', 'deficit_diario']
BANDAS_MEDIA = ['tmax_C', 'tmin_C', 'RH', 'rs', 'u2', 'tsolo_C', 'tfolha_C', 'vpd', 'soil_moisture_0_5cm_m3_m3',
                'soil_moisture_0_100cm_m3_m3', 'amplitude_diaria']
# [ENSO] Os mesmos cenários do painel (CENARIOS_ENSO): valor interno, texto da coluna Filtro_ENSO, sufixo do arquivo
ENSO_CENARIOS = [
    ('Super El Niño (≥ 2.0°C)', 'El Nino muito forte (Super)', 'El_Nino_Muito_Forte'),
    ('El Niño Forte (1.5 a 1.9°C)', 'El Nino forte', 'El_Nino_Forte'),
    ('El Niño Moderado (1.0 a 1.4°C)', 'El Nino moderado', 'El_Nino_Moderado'),
    ('El Niño Fraco (0.5 a 0.9°C)', 'El Nino fraco', 'El_Nino_Fraco'),
    ('Anos Neutros', 'Neutro', 'Neutro'),
    ('La Niña Fraca (-0.5 a -0.9°C)', 'La Nina fraca', 'La_Nina_Fraca'),
    ('La Niña Moderada (-1.0 a -1.4°C)', 'La Nina moderada', 'La_Nina_Moderada'),
    ('La Niña Forte (-1.5 a -1.9°C)', 'La Nina forte', 'La_Nina_Forte'),
    ('Super La Niña (≤ -2.0°C)', 'La Nina muito forte (Super)', 'La_Nina_Muito_Forte')]
COLUNAS_ENSO_PAINEL = ['Filtro_ENSO', 'Fase_ENSO', 'Intensidade_ENSO', 'RONI_Trimestre_C', 'Trimestre_CPC']
COLUNAS_ENSO = COLUNAS_ENSO_PAINEL + ['Fonte_ENSO']     # [2026.11.01] sempre no CSV do e-mail
# Fontes do RONI de cada mês: as duas primeiras são as do painel e as únicas que entram nos filtros
FONTES_FILTRO = ('CPC', 'Estimativa_OISST')
TRIMESTRES = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']
VERSOES_PREVISAO = ['provisoria_gfs', 'provisoria_gfs_incompleta', 'falha_latencia_gfs']
RONI_ASSET = f'projects/{PROJETO}/assets/RONI_CPC_v6'
COLUNAS_MANIFESTO = ['Pedido', 'Status', 'Motivo', 'Arquivo', 'Linhas_Esperadas', 'Local', 'Periodo', 'Resolucao',
                     'Variaveis', 'Formato', 'Gerado_em', 'Versao_Rotina', 'Versao_Painel']

# Dicionário de variáveis: as 35 linhas de exportarDicionarioAutomatizado do painel. [2026.11.01] Mudaram de propósito
# (a K16 aceita só estas diferenças): Filtro_ENSO, Fase_ENSO, Intensidade_ENSO, RONI_Trimestre_C, Trimestre_CPC e
# (formato dos numeros); entrou Fonte_ENSO.
DICIONARIO = [
    ('Tipo_Dado',
     'Origem do dia: Historico_Observado (BR-DWGD), Provisorio_ERA5 (reanalise calibrada), Previsao_GFS (previsao calibrada), Previsao_GFS_Parcial (dia com rodada GFS incompleta: chuva, radiacao solar, ETo e as colunas que dependem delas ficam vazias), Sem_Dado, Desconhecido (valor de versao que o painel nao reconhece).',
     '-'),
    ('Versao_Algoritmo',
     'Versao do motor que gravou o dia. V1.0: historico (umidade do solo e escoamento corrigidos pelo painel na leitura). V1.3: ETo por Penman-Monteith nos dias provisorios e na previsao. V1.4: umidade do solo do ERA5 com reamostragem bilinear e previsao GFS calibrada por faixa de prazo. V1.5: so rodadas GFS 00Z completas, matriz GFS V2.1, mascara de 2025-12-31 e Confianca_Prazo nos dias GFS. No arquivo mensal, as versoes presentes no mes.',
     '-'),
    ('Janela_Chuva_UTC',
     'CSV diario. Janela de acumulo da chuva do dia, em UTC. 12-12 UTC (D-1 a D): BR-DWGD (historico), de 12 UTC do dia anterior a 12 UTC do dia (9 h a 9 h de Brasilia). 00-24 UTC: ERA5 e GFS, dia civil em UTC (21 h do dia anterior a 21 h do dia em Brasilia). Os valores nao sao ajustados entre as janelas.',
     '-'),
    ('Filtro_ENSO',
     'Fenomeno escolhido no filtro ENSO do pedido, ou Sem filtro. Com filtro, o arquivo traz so os meses do passado em que ele ocorreu (meses com Fonte_ENSO CPC ou Estimativa_OISST); os dias de previsao entram sempre. As colunas ENSO vem em todo pedido por e-mail.',
     '-'),
    ('Fase_ENSO',
     'Fase do trimestre centrado no mes do dia: El Nino, La Nina ou Neutro (episodio = 5 trimestres seguidos acima de +0,5 ou abaixo de -0,5 C); Indefinida = fim da serie, sinal de El Nino ou La Nina que ainda nao completou 5 trimestres; Sem_Dado = mes sem RONI. Nos meses estimados e nos dias de previsao, a fase do ultimo trimestre calculado (ver Fonte_ENSO).',
     '-'),
    ('Intensidade_ENSO',
     'Intensidade pelo RONI do trimestre: Fraco (0,5 a 0,9), Moderado (1,0 a 1,4), Forte (1,5 a 1,9) ou Muito forte/Super (2,0 ou mais), em modulo; - no Neutro, na fase Indefinida e sem dado.',
     '-'),
    ('RONI_Trimestre_C',
     'Indice RONI do trimestre centrado no mes (anomalia relativa da temperatura do mar no Nino 3.4, ja descontado o aquecimento medio dos oceanos tropicais). A origem do valor esta em Fonte_ENSO.',
     'C'),
    ('Trimestre_CPC',
     'Sigla do trimestre do CPC centrado no mes (ex.: OND = outubro a dezembro, usado nos dias de novembro). Nos meses por persistencia, o trimestre de onde o valor foi copiado.',
     '-'),
    ('Fonte_ENSO',
     'Origem do RONI do mes. CPC: valor oficial do CPC/NOAA (ERSSTv6). Estimativa_OISST: trimestre completo calculado pelo SAB com o satelite OISST, enquanto o CPC nao publica. Estimativa_OISST_parcial: so 2 dos 3 meses do trimestre ja existem (estimativa provisoria). Persistencia: mes atual e dias de previsao, com o ultimo valor calculado (o ENSO muda devagar, em meses; em ate 15 dias a persistencia e a melhor estimativa simples). Os dois ultimos tipos nao entram nos filtros.',
     '-'),
    ('Confianca_Prazo',
     'CSV diario. Confianca da previsao GFS pelo prazo, gravada pelo motor a partir da V1.5: alta (prazo de 1 a 5 dias), media (6 a 10), baixa (11 em diante). Vazia nos demais dias e nos dias gravados pelas versoes V1.3 e V1.4.',
     '-'),
    ('N_Dias',
     'CSV mensal. Numero de imagens diarias usadas no mes (dentro do periodo pedido e do filtro ENSO).',
     'dias'),
    ('Dias_no_Mes',
     'CSV mensal. Numero de dias do mes no calendario.',
     'dias'),
    ('Mes_Completo',
     'CSV mensal. sim quando N_Dias = Dias_no_Mes; nao em mes parcial (inicio ou fim do periodo, filtro ENSO, dias faltando). Somas de mes parcial nao sao totais mensais.',
     '-'),
    ('Latitude',
     'Latitude do centro do pixel da grade de 0,1 grau (nao e a sede do municipio).',
     'graus'),
    ('Longitude',
     'Longitude do centro do pixel da grade de 0,1 grau (nao e a sede do municipio).',
     'graus'),
    ('Qualidade_Pixel',
     'CSV diario. Classe do pixel na mascara de qualidade: A = SAB igual ao BR-DWGD; B = lagoas e estuarios onde o motor V1.0 descartou o BR-DWGD (desde o painel 2026.11.1 os dias de 1961 a 2025 saem com o BR-DWGD em chuva, temperaturas, UR, VPD, ETo, radiacao e vento, corrigidos na leitura); C = sem BR-DWGD, preenchido com ERA5, centro do pixel no Brasil (desde 2026.11.1 a radiacao dos dias de 1961 a 2025 e limitada a de ceu claro, FAO-56). Com a mascara, os pixels sem BR-DWGD com centro fora do Brasil (borda) ficam fora do CSV. Vazia se o pixel nao tem classe ou se a mascara ainda nao existe.',
     '-'),
    ('Precipitacao_mm',
     'Volume total de chuva no periodo. A janela de acumulo de cada dia esta na coluna Janela_Chuva_UTC.',
     'mm'),
    ('(formato dos numeros)',
     'CSV em UTF-8, separado por virgula, com PONTO decimal (ex.: 18.40); celula vazia = sem dado. No Excel em portugues, NAO abra com duplo clique: Dados > Obter Dados > De Texto/CSV; Origem do arquivo 65001: Unicode (UTF-8); Delimitador Virgula; Deteccao de tipo de dados: Nao detectar tipos de dados; Transformar Dados; selecione as colunas numericas > botao direito > Alterar Tipo > Usando a Localidade > Numero Decimal, Ingles (Estados Unidos); Fechar e Carregar. Ou peca o formato Excel (.xlsx), que ja vem com os numeros prontos.',
     '-'),
    ('Chuva_Efetiva_mm',
     'INDICE NAO VALIDADO: chuva menos o escoamento superficial (minimo zero). Herda a incerteza do escoamento (auditoria E3: fator do SMAP acima de 5 em ate 60% dos pixels na seca). Nao e medida da chuva que infiltrou.',
     'mm'),
    ('Runoff_Superficial_mm',
     'INDICE NAO VALIDADO de escoamento superficial (enxurrada). Auditoria E3: fator do SMAP acima de 5 em ate 60% dos pixels na seca.',
     'mm'),
    ('Runoff_Subsuperficial_mm',
     'INDICE NAO VALIDADO de escoamento por dentro do solo (fluxo subsuperficial). Mesma ressalva do escoamento superficial (auditoria E3).',
     'mm'),
    ('Temperatura_Maxima_C',
     'Temperatura maxima do ar a 2 metros de altura.',
     'Celsius (C)'),
    ('Temperatura_Minima_C',
     'Temperatura minima do ar a 2 metros de altura.',
     'Celsius (C)'),
    ('Amplitude_Termica_C',
     'Diferenca entre a temperatura maxima e minima do dia.',
     'Celsius (C)'),
    ('Temperatura_Solo_C',
     'Temperatura media da camada de 0 a 7 cm do solo (ERA5-Land). Vazia nos dias de previsao GFS.',
     'Celsius (C)'),
    ('Temperatura_Folha_C',
     'Temperatura de superficie (skin temperature do ERA5-Land): temperatura teorica que fecha o balanco de energia da superficie. Nao e medida direta da folha. Vazia nos dias de previsao GFS.',
     'Celsius (C)'),
    ('Umidade_Relativa_Porc',
     'Umidade relativa do ar. Nos dias provisorios, calculada das medias diarias de temperatura e ponto de orvalho do ERA5-Land e calibrada pelo BR-DWGD.',
     '%'),
    ('Vento_ms',
     'Velocidade media do vento a 2 metros de altura (convertida de 10 m pelo fator FAO-56).',
     'm/s'),
    ('Radiacao_Solar_MJ_m2',
     'Radiacao solar global incidente na superficie.',
     'MJ/m2'),
    ('Evapotranspiracao_Potencial_mm',
     'Evapotranspiracao de Referencia FAO-56 Penman-Monteith (demanda da atmosfera). No historico vem do BR-DWGD; nos dias provisorios e na previsao e calculada com a meteorologia calibrada.',
     'mm'),
    ('Evapotranspiracao_Real_mm',
     'Evapotranspiracao Real (ERA5-Land no historico e nos dias provisorios; balanco de agua no solo na previsao), nunca maior que a potencial.',
     'mm'),
    ('Transpiracao_Planta_mm',
     'Vem da banda de evaporacao do solo do ERA5-Land (evaporation_from_bare_soil_sum), que o motor usa como transpiracao por causa da troca de bandas apontada no catalogo do GEE; limitada a ET real. Nos dias GFS vem do balanco de agua do motor. Nao e medida da transpiracao da cultura.',
     'mm'),
    ('Deficit_Hidrico_mm',
     'Estresse hidrico (Evapotranspiracao Potencial - Evapotranspiracao Real).',
     'mm'),
    ('Deficit_Pressao_Vapor_kPa',
     'Deficit de Pressao de Vapor (VPD) medindo a secura do ar.',
     'kPa'),
    ('Umidade_Volumetrica_Solo_0_5cm_m3_m3',
     'Umidade volumetrica da camada superficial: camada de 0 a 7 cm do ERA5-Land calibrada pela media mensal do SMAP L4 (0 a 5 cm).',
     'm3/m3'),
    ('Umidade_Volumetrica_Solo_0_100cm_m3_m3',
     'Umidade volumétrica de água armazenada na zona radicular completa de 0 a 100 cm.',
     'm3/m3'),
]


class PedidoInvalido(Exception):
    """Pedido recusado: a mensagem vai para o manifesto e para o e-mail do solicitante."""


# =========================================================================================
# FUNÇÕES PURAS (sem Earth Engine; testadas em testes/teste_sab_pedido.py)
# =========================================================================================
_COM = 'ÁÀÃÂÄÉÈÊËÍÌÎÏÓÒÕÔÖÚÙÛÜÇÑáàãâäéèêëíìîïóòõôöúùûüçñ'
_SEM = 'AAAAAEEEEIIIIOOOOOUUUUCNaaaaaeeeeiiiiooooouuuucn'


def remover_acentos(texto):
    """removerAcentos do painel, letra a letra."""
    if not texto:
        return ''
    return ''.join(_SEM[_COM.index(c)] if c in _COM else c for c in str(texto))


def limpar_nome_arquivo(nome):
    """limparNomeArquivo do painel."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', remover_acentos(str(nome)))


def variacoes_busca(lista):
    """listaVariacoesBusca do painel (formatarTextoBusca de cada item, sem repetir, na mesma ordem)."""
    saida = []
    for item in lista or []:
        if not item:
            continue
        bruto = str(item).strip()
        sem = remover_acentos(bruto)
        titulo = ' '.join((w[0].upper() + w[1:]) if w else '' for w in sem.lower().split(' ')).strip()
        for v in (bruto, sem, titulo, bruto.upper(), sem.upper(), titulo.upper()):
            if v not in saida:
                saida.append(v)
    return saida


def ler_codigo(codigo):
    """'k=v;k=v' -> dicionário. Chaves em minúsculas, valores sem espaços nas pontas."""
    if not codigo or not str(codigo).strip():
        raise PedidoInvalido('O código do pedido veio vazio. Gere o pedido de novo pelo painel.')
    if len(codigo) > 6000:
        raise PedidoInvalido('O código do pedido é longo demais.')
    campos = {}
    for parte in str(codigo).strip().strip(';').split(';'):
        if not parte.strip():
            continue
        if '=' not in parte:
            raise PedidoInvalido(f'Trecho sem "=" no código do pedido: "{parte[:40]}".')
        k, v = parte.split('=', 1)
        campos[k.strip().lower()] = v.strip()
    return campos


def _data(txt, nome):
    try:
        return datetime.strptime(txt, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        raise PedidoInvalido(f'Data {nome} inválida: "{txt}" (use AAAA-MM-DD).')


def _estado_canonico(nome):
    alvo = remover_acentos(nome).strip().lower()
    for e in LISTA_ESTADOS:
        if remover_acentos(e).lower() == alvo:
            return e
    raise PedidoInvalido(f'Estado não reconhecido: "{nome}".')


def sinal_enso(roni):
    return 1 if roni >= 0.5 else (-1 if roni <= -0.5 else 0)


def classificar_enso(serie):
    """[ENSO] indiceONI_FC do painel: serie = [{'ano', 'mes', 'RONI', 'Trimestre'}] em ordem e contínua.
    Fase por episódio: El Niño/La Niña quando o limiar de ±0,5 se mantém por 5 estações seguidas (janelas de 5
    que contêm o mês); no fim da série, sinal não nulo que se repete até a última estação sem completar 5 vira
    'Indefinida'; o resto é 'Neutro'. Devolve a mesma lista com 'FaseENSO'."""
    sinais = [sinal_enso(x['RONI']) for x in serie]
    n = len(sinais)
    saida = []
    for i, x in enumerate(serie):
        janelas = []
        for off in (-4, -3, -2, -1, 0):
            ini, fim = i + off, i + off + 4
            janelas.append(sum(sinais[ini:fim + 1]) if ini >= 0 and fim < n else 0)
        ate_fim = n - i
        indefinida = abs(sinais[i]) == 1 and ate_fim <= 4 and sum(sinais[i:]) == sinais[i] * ate_fim
        fase = 'El Nino' if 5 in janelas else ('La Nina' if -5 in janelas else ('Indefinida' if indefinida else 'Neutro'))
        saida.append(dict(x, FaseENSO=fase))
    return saida


def no_cenario(item, valor):
    """[ENSO] filtroCenario do painel para um mês classificado."""
    f, r = item['FaseENSO'], item['RONI']
    if f not in ('El Nino', 'La Nina', 'Neutro'):
        return False
    regras = {
        'Super El Niño (≥ 2.0°C)': f == 'El Nino' and r >= 2.0,
        'El Niño Forte (1.5 a 1.9°C)': f == 'El Nino' and 1.5 <= r < 2.0,
        'El Niño Moderado (1.0 a 1.4°C)': f == 'El Nino' and 1.0 <= r < 1.5,
        'El Niño Fraco (0.5 a 0.9°C)': f == 'El Nino' and 0.5 <= r < 1.0,
        'Anos Neutros': f == 'Neutro',
        'La Niña Fraca (-0.5 a -0.9°C)': f == 'La Nina' and -1.0 < r <= -0.5,
        'La Niña Moderada (-1.0 a -1.4°C)': f == 'La Nina' and -1.5 < r <= -1.0,
        'La Niña Forte (-1.5 a -1.9°C)': f == 'La Nina' and -2.0 < r <= -1.5,
        'Super La Niña (≤ -2.0°C)': f == 'La Nina' and r <= -2.0}
    return bool(regras.get(valor))


def chave_mes(d):
    return f'{d.year:04d}_{d.month:02d}'


def juntar_roni(oficial, estimativas):
    """[ENSO] oficial: série do CPC em ordem; estimativas: dicionários do OISST {'ano', 'mes', 'RONI', 'n_meses'}.
    Devolve (serie, parciais): serie = oficial + trimestres OISST completos (n_meses 3) depois da última estação
    oficial (a série do painel); parciais = trimestres OISST com 2 meses depois do fim da série."""
    ultima = (oficial[-1]['ano'], oficial[-1]['mes']) if oficial else (0, 0)
    depois = sorted((x for x in estimativas if (int(x['ano']), int(x['mes'])) > ultima),
                    key=lambda x: (int(x['ano']), int(x['mes'])))
    est = [{'ano': int(x['ano']), 'mes': int(x['mes']), 'RONI': float(x['RONI']),
            'Trimestre': TRIMESTRES[int(x['mes']) - 1], 'Fonte': 'Estimativa_OISST'}
           for x in depois if int(x.get('n_meses', 3)) == 3]
    serie = list(oficial) + est
    fim = (serie[-1]['ano'], serie[-1]['mes']) if serie else ultima
    parciais = [{'ano': int(x['ano']), 'mes': int(x['mes']), 'RONI': float(x['RONI']),
                 'Trimestre': TRIMESTRES[int(x['mes']) - 1], 'Fonte': 'Estimativa_OISST_parcial'}
                for x in depois if int(x.get('n_meses', 3)) == 2 and (int(x['ano']), int(x['mes'])) > fim]
    return serie, parciais


def _mes_seguinte(ano, mes):
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def estender_enso(classif, parciais, ate):
    """[2026.11.01] Completa a série classificada até o mês de `ate` (date: fim do pedido ou da previsão).
    1) parciais (trimestre OISST com 2 de 3 meses), em sequência ao fim da série; 2) depois, PERSISTÊNCIA do
    último valor (mesmo RONI e trimestre de origem). Fase dos meses estendidos: a do último mês classificado se
    for El Niño/La Niña e o sinal se mantiver; senão 'Indefinida' (sinal de ±0,5 ainda sem os 5 trimestres) ou
    'Neutro'. Esses meses nunca entram nos filtros (só CPC e Estimativa_OISST entram)."""
    saida = [dict(x, Fonte=x.get('Fonte', 'CPC')) for x in classif]
    if not saida:
        return saida
    ult = saida[-1]
    fase_ult = ult['FaseENSO']

    def fase_de(r):
        s_ = sinal_enso(r)
        if fase_ult == 'El Nino' and s_ == 1 or fase_ult == 'La Nina' and s_ == -1:
            return fase_ult
        return 'Indefinida' if s_ else 'Neutro'

    ano, mes = ult['ano'], ult['mes']
    for p in parciais:
        if (p['ano'], p['mes']) != _mes_seguinte(ano, mes):
            break
        saida.append(dict(p, FaseENSO=fase_de(p['RONI'])))
        ano, mes = p['ano'], p['mes']
    base = saida[-1]
    while (ano, mes) < (ate.year, ate.month):
        ano, mes = _mes_seguinte(ano, mes)
        saida.append({'ano': ano, 'mes': mes, 'RONI': base['RONI'], 'Trimestre': base['Trimestre'],
                      'Fonte': 'Persistencia', 'FaseENSO': fase_de(base['RONI'])})
    return saida


def dicionario_enso(serie):
    """'AAAA_MM' -> [fase, RONI, trimestre, fonte], o dicionário que props_enso consulta no Earth Engine."""
    return {f"{x['ano']:04d}_{x['mes']:02d}": [x['FaseENSO'], x['RONI'], x['Trimestre'], x.get('Fonte', 'CPC')]
            for x in serie}


def ler_pontos(txt):
    """'lat lon nome|lat lon nome' -> [{'lat', 'lon', 'nome'}]. Coordenadas decimais com ponto."""
    pontos = []
    for i, bloco in enumerate(x.strip() for x in str(txt).split('|') if x.strip()):
        partes = bloco.split(None, 2)
        try:
            lat, lon = float(partes[0]), float(partes[1])
        except (IndexError, ValueError):
            raise PedidoInvalido(f'Ponto {i + 1} inválido: "{bloco[:40]}" (esperado: latitude longitude nome).')
        if not (-34.0 <= lat <= 6.0 and -74.0 <= lon <= -34.0):
            raise PedidoInvalido(f'Ponto {i + 1} fora do Brasil: {lat}, {lon}.')
        nome = re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿ0-9 ._()\-]', ' ', partes[2] if len(partes) > 2 else f'Ponto {i + 1}')
        pontos.append({'lat': lat, 'lon': lon, 'nome': re.sub(r'\s+', ' ', nome).strip()[:40] or f'Ponto {i + 1}'})
    if not pontos:
        raise PedidoInvalido('Nenhum ponto no pedido.')
    if len(pontos) > LIMITE_PONTOS:
        raise PedidoInvalido(f'No máximo {LIMITE_PONTOS} pontos por pedido.')
    return pontos


def centro_do_pixel(lat, lon):
    """Centro do pixel de 0,1° da grade do SAB (TRANSFORM) que contém o ponto: o mesmo que a grade do painel usa."""
    dx, x0, dy, y0 = TRANSFORM[0], TRANSFORM[2], TRANSFORM[4], TRANSFORM[5]
    col = int((lon - x0) // dx)
    lin = int((lat - y0) // dy)
    return y0 + (lin + 0.5) * dy, x0 + (col + 0.5) * dx


def normalizar_nome(t):
    return re.sub(r'\s+', ' ', remover_acentos(str(t)).lower().replace('-', ' ').replace("'", ' ')).strip()


def casar_municipios(pedidos, nomes_gaul):
    """Acha cada município pedido entre os nomes do GAUL, sem ligar para acento, maiúscula, hífen ou apóstrofo.
    Devolve (nomes do GAUL achados, mensagens dos que faltam, com sugestões)."""
    por_norma = {}
    for n in nomes_gaul or []:
        por_norma.setdefault(normalizar_nome(n), [])
        if n not in por_norma[normalizar_nome(n)]:
            por_norma[normalizar_nome(n)].append(n)
    achados, faltam = [], []
    for p in pedidos:
        iguais = por_norma.get(normalizar_nome(p))
        if iguais:
            achados.extend(x for x in iguais if x not in achados)
        else:
            perto = difflib.get_close_matches(normalizar_nome(p), list(por_norma), n=3, cutoff=0.75)
            dica = ' (talvez: ' + ', '.join(por_norma[x][0] for x in perto) + ')' if perto else ''
            faltam.append(p + dica)
    return achados, faltam


_RE_MUN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ0-9' .\-()]{2,60}$")


def validar(campos, hoje):
    """Confere o pedido e devolve a forma normalizada. hoje: date (para o limite da data final)."""
    if campos.get('v') != '1':
        raise PedidoInvalido('Versão do código do pedido não reconhecida (esperado v=1).')
    res = campos.get('res', '').upper()
    if res not in ('D', 'M'):
        raise PedidoInvalido('Resolução inválida (res=D diária ou res=M mensal).')
    tipo = campos.get('tipo', '').upper()
    if tipo == 'BR':   # [2026.11.01] estourou a memória do Earth Engine (pedido P20261031213150mffz, 31/10/2026)
        raise PedidoInvalido('O pedido do Brasil inteiro foi desativado: é grande demais para o Earth Engine. '
                             f'Peça por estados (até {LIMITE_ESTADOS} por pedido), de preferência com a resolução '
                             'mensal para períodos longos.')
    if tipo not in ('E', 'M', 'P', 'C'):
        raise PedidoInvalido('Tipo de local inválido (tipo=E estados, M municípios, P polígonos ou C pontos).')
    ini, fim = _data(campos.get('ini'), 'inicial'), _data(campos.get('fim'), 'final')
    if ini < DATA_MINIMA:
        raise PedidoInvalido('O banco SAB começa em 01/01/1961.')
    if fim < ini:
        raise PedidoInvalido('A data final é anterior à inicial.')
    if fim > hoje + timedelta(days=20):
        raise PedidoInvalido('A data final passa do fim da previsão do banco.')
    ped = {'res': res, 'tipo': tipo, 'ini': ini, 'fim': fim, 'estados': [], 'municipios': [], 'poligonos': [],
           'pontos': []}
    if tipo == 'C':
        ped['pontos'] = ler_pontos(campos.get('pts', ''))
    ped['separar'] = campos.get('sep') == '1'   # uma grade e um arquivo por estado
    fmt = campos.get('fmt', 'csv').strip().lower() or 'csv'
    if fmt not in FORMATOS:
        raise PedidoInvalido(f'Formato não reconhecido: "{fmt}" (use csv, xlsx ou ambos).')
    ped['formato'] = fmt
    ped['enso'] = None          # sem filtro (as colunas ENSO saem do mesmo jeito)
    chave_enso = campos.get('enso', '').strip()
    if chave_enso.lower() in ('sem filtro', 'sem_filtro', 'todos', 'nenhum'):
        chave_enso = ''
    if chave_enso:
        achado = [c for c in ENSO_CENARIOS if c[2].lower() == chave_enso.lower()]
        if not achado:
            raise PedidoInvalido(f'Filtro ENSO não reconhecido: "{chave_enso}".')
        ped['enso'] = {'valor': achado[0][0], 'ascii': achado[0][1], 'arquivo': achado[0][2]}

    if tipo in ('E', 'M'):
        ufs = [u for u in (x.strip() for x in campos.get('uf', '').split(',')) if u]
        if not ufs:
            raise PedidoInvalido('Nenhum estado no pedido.')
        estados = []
        for u in ufs:
            e = _estado_canonico(u)
            if e not in estados:
                estados.append(e)
        if tipo == 'E' and len(estados) > LIMITE_ESTADOS:
            raise PedidoInvalido(f'No máximo {LIMITE_ESTADOS} estados por pedido (foram {len(estados)}). '
                                 'Divida em pedidos menores.')
        ped['estados'] = estados
    if tipo == 'M':
        muns = [m for m in (x.strip() for x in campos.get('mun', '').split(',')) if m]
        if not muns:
            raise PedidoInvalido('Nenhum município no pedido.')
        if len(muns) > LIMITE_MUNICIPIOS:
            raise PedidoInvalido(f'No máximo {LIMITE_MUNICIPIOS} municípios por pedido.')
        for m in muns:
            if not _RE_MUN.match(m):
                raise PedidoInvalido(f'Nome de município inválido: "{m[:60]}".')
        ped['municipios'] = list(dict.fromkeys(muns))
    if tipo == 'P':
        polis, total = [], 0
        for i, bloco in enumerate(x for x in campos.get('pol', '').split('|') if x.strip()):
            verts = []
            for par in (p for p in bloco.split(',') if p.strip()):
                nums = par.split()
                if len(nums) != 2:
                    raise PedidoInvalido(f'Vértice inválido no polígono {i + 1}: "{par.strip()[:30]}".')
                try:
                    lat, lon = float(nums[0]), float(nums[1])
                except ValueError:
                    raise PedidoInvalido(f'Vértice inválido no polígono {i + 1}: "{par.strip()[:30]}".')
                if not (-34.0 <= lat <= 6.0 and -74.0 <= lon <= -34.0):
                    raise PedidoInvalido(f'Vértice fora do Brasil no polígono {i + 1}: {lat}, {lon}.')
                verts.append([lon, lat])     # [lon, lat], como o painel monta o ee.Geometry.Polygon
            if len(verts) < 4:
                raise PedidoInvalido(f'O polígono {i + 1} tem menos de 4 vértices.')
            total += len(verts)
            polis.append(verts)
        if not polis:
            raise PedidoInvalido('Nenhum polígono no pedido.')
        if len(polis) > LIMITE_POLIGONOS or total > LIMITE_VERTICES:
            raise PedidoInvalido(f'No máximo {LIMITE_POLIGONOS} polígonos e {LIMITE_VERTICES} vértices por pedido.')
        ped['poligonos'] = polis

    txt = campos.get('var', 'todas').strip().lower()
    if txt in ('', 'todas', 'all'):
        cods = list(CODIGOS)
    else:
        pedidos = [c.strip() for c in txt.split(',') if c.strip()]
        desconhecidos = [c for c in pedidos if c not in CODIGOS]
        if desconhecidos:
            raise PedidoInvalido(f'Variável não reconhecida: {", ".join(desconhecidos)}.')
        cods = [c for c in CODIGOS if c in pedidos]     # ordem do painel
    if not cods:
        raise PedidoInvalido('Escolha pelo menos uma variável.')
    ped['variaveis'] = cods
    return ped


def nome_local_unico(ped):
    """nome_local do painel (só para o texto do manifesto)."""
    if ped['tipo'] == 'C':
        return 'Pontos'
    if ped['tipo'] == 'E':
        return ped['estados'][0] if len(ped['estados']) == 1 else 'Grupo_Estados'
    if ped['tipo'] == 'M':
        return ped['municipios'][0] if len(ped['municipios']) == 1 else 'Grupo_Municipios'
    return 'Poligono_Usuario' if len(ped['poligonos']) == 1 else 'Multiplos_Poligonos'


def colunas_do_pedido(res, cods, enso=True):
    """Selectors do CSV: identificação + variáveis pedidas (ordem do painel) + colunas de qualidade + as 6 colunas
    ENSO no fim. [2026.11.01] enso=True é o padrão do e-mail (sempre); enso=False dá as colunas do painel sem filtro
    (usado pela K16 para comparar)."""
    numericas = [col for c, col, _, _, _ in VARIAVEIS if c in cods]
    return COLUNAS_ID + numericas + (EXTRAS_DIARIA if res == 'D' else EXTRAS_MENSAL) + (COLUNAS_ENSO if enso else [])


def _pixels_poligono(verts):
    """Pixels de 0,1° dentro de um polígono [[lon, lat], ...] (fórmula do laço, em graus; ~ estimativa)."""
    a = 0.0
    for (x1, y1), (x2, y2) in zip(verts, verts[1:] + verts[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2 / (TRANSFORM[0] ** 2) + 2 * len(verts)


def estimar_linhas(ped):
    """[2026.11.01] Linhas do pedido estimadas SEM Earth Engine (área dos estados, polígonos, pontos), para recusar na
    hora um pedido muito grande em vez de estourar a memória do Earth Engine. Devolve (linhas, pixels)."""
    if ped['tipo'] == 'E':
        px = sum(AREA_LAT_ESTADO[e][0] / (123.9 * math.cos(math.radians(AREA_LAT_ESTADO[e][1]))) * 1.08
                 for e in ped['estados'])
    elif ped['tipo'] == 'M':
        px = 40 * len(ped['municipios'])       # município médio: ~1.500 km², ~12 pixels; folga para os grandes
    elif ped['tipo'] == 'P':
        px = sum(_pixels_poligono(v) for v in ped['poligonos'])
    else:
        px = len(ped['pontos'])
    dias = (ped['fim'] - ped['ini']).days + 1
    tempos = dias if ped['res'] == 'D' else (ped['fim'].year - ped['ini'].year) * 12 + ped['fim'].month - ped['ini'].month + 1
    return int(px * tempos), int(px)


def conferir_estimativa(ped):
    linhas, px = estimar_linhas(ped)
    if linhas > FOLGA_ESTIMATIVA * LIMITE_LINHAS_PEDIDO:
        raise PedidoInvalido(f'O pedido teria cerca de {milhar(linhas)} linhas ({milhar(px)} pixels de 0,1° x '
                             f'{"dias" if ped["res"] == "D" else "meses"}), acima do limite de '
                             f'{milhar(LIMITE_LINHAS_PEDIDO)} por pedido. Divida em pedidos menores: menos anos, '
                             'menos estados ou a resolução mensal.')
    return linhas


def bandas_do_pedido(cods):
    return [banda for c, _, banda, _, _ in VARIAVEIS if c in cods]


def _blocos_de_meses(dias_por_mes, n_pontos, limite):
    """Menor divisão do ano (1, 2, 3, 4, 6 ou 12 blocos de meses) em que nenhum bloco passa do limite."""
    for k in (1, 2, 3, 4, 6, 12):
        tam = 12 // k
        blocos = [(i * tam + 1, (i + 1) * tam) for i in range(k)]
        if all(n_pontos * sum(dias_por_mes.get(m, 0) for m in range(a, b + 1)) <= limite for a, b in blocos):
            return blocos
    return [(m, m) for m in range(1, 13)]


def planejar(res, locais, datas, limite=LIMITE_LINHAS_ARQUIVO, sufixo=''):
    """locais: lista de (Nome_Local_Export, n_pontos), na ordem do painel; datas: datas (date) das imagens
    do período. Devolve a lista de arquivos: nome, local, ini e fim (fim exclusivo) e linhas esperadas.
    Um arquivo por local e por ano com dados (como o painel); um ano diário acima do limite vira blocos."""
    por_ano = {}
    for d in datas:
        por_ano.setdefault(d.year, {}).setdefault(d.month, 0)
        por_ano[d.year][d.month] += 1
    arquivos = []
    for nome, n in locais:
        base = limpar_nome_arquivo(nome)
        for ano in sorted(por_ano):
            meses = por_ano[ano]
            if res == 'M':
                arquivos.append({'nome': f'Mensal_{base}_{ano}{sufixo}', 'local': nome, 'ano': ano,
                                 'ini': date(ano, 1, 1), 'fim': date(ano + 1, 1, 1), 'linhas': n * len(meses)})
                continue
            blocos = _blocos_de_meses(meses, n, limite)
            for i, (a, b) in enumerate(blocos):
                linhas = n * sum(meses.get(m, 0) for m in range(a, b + 1))
                if not linhas:
                    continue
                parte = '' if len(blocos) == 1 else f'_parte{i + 1}de{len(blocos)}'
                fim = date(ano + 1, 1, 1) if b == 12 else date(ano, b + 1, 1)
                arquivos.append({'nome': f'Diaria_{base}_{ano}{sufixo}{parte}', 'local': nome, 'ano': ano,
                                 'ini': date(ano, a, 1), 'fim': fim, 'linhas': linhas})
    return arquivos


def milhar(n):
    return f'{n:,}'.replace(',', '.')


def conferir_limites(n_pares, locais, arquivos):
    """Os mesmos limites do painel (pares) e os do envio por e-mail (linhas e arquivos)."""
    if n_pares > LIMITE_PONTOS_GRADE:
        raise PedidoInvalido(f'Área grande demais: {milhar(n_pares)} pares pixel x polígono (limite '
                             f'{milhar(LIMITE_PONTOS_GRADE)}, o mesmo do painel). Reduza a área.')
    if not locais or not any(n for _, n in locais):
        raise PedidoInvalido('Nenhum ponto da grade no local pedido.')
    if not arquivos:
        raise PedidoInvalido('Não há dados do banco SAB no período pedido.')
    total = sum(a['linhas'] for a in arquivos)
    if total > LIMITE_LINHAS_PEDIDO:
        raise PedidoInvalido(f'O pedido tem {milhar(total)} linhas, acima do limite de {milhar(LIMITE_LINHAS_PEDIDO)} '
                             'por pedido. Divida em pedidos menores, com menos anos ou menos área (menos variáveis '
                             'deixam o arquivo menor, mas não diminuem as linhas).')
    if len(arquivos) > LIMITE_ARQUIVOS:
        raise PedidoInvalido(f'O pedido geraria {len(arquivos)} arquivos (limite {LIMITE_ARQUIVOS}). '
                             'Divida em pedidos menores.')
    return total


def contar_pontos(nomes_dos_pontos):
    """[(Nome_Local_Export, n_pontos)] na ordem de aparição (a do distinct do painel)."""
    contagem = {}
    for nome in nomes_dos_pontos:
        contagem[nome] = contagem.get(nome, 0) + 1
    return list(contagem.items())


def faltando(pedidos, encontrados):
    """Nomes pedidos que nenhuma variação de busca (acentos, maiúsculas) encontrou no GAUL."""
    achados = set(encontrados or [])
    return [p for p in pedidos if not any(v in achados for v in variacoes_busca([p]))]


def pasta_do_pedido(pedido_id):
    return f'SAB_pedido_{pedido_id}'


def descricao_tarefa(pedido_id, k):
    return f'SABPED_{pedido_id}_{k:03d}'


def texto_periodo(ped):
    return f"{ped['ini']:%d/%m/%Y} a {ped['fim']:%d/%m/%Y}" + \
        (f" | filtro ENSO: {ped['enso']['ascii']} (a previsão entra sempre)" if ped.get('enso') else '') + \
        (f" | formato: {FORMATOS[ped.get('formato', 'csv')]}" if ped.get('formato', 'csv') != 'csv' else '')


def texto_local(ped):
    if ped['tipo'] == 'C':
        return f"{len(ped['pontos'])} ponto(s): " + ', '.join(p['nome'] for p in ped['pontos'][:10]) + \
            ('...' if len(ped['pontos']) > 10 else '')
    if ped['tipo'] == 'E':
        return 'Estado(s): ' + ', '.join(ped['estados']) + (' (um arquivo por estado)' if ped.get('separar') else '')
    if ped['tipo'] == 'M':
        return 'Município(s): ' + ', '.join(ped['municipios']) + ' (' + ', '.join(ped['estados']) + ')'
    return f"{len(ped['poligonos'])} polígono(s) desenhado(s)"


def linhas_manifesto(pedido_id, status, motivo, ped=None, arquivos=None, agora=None):
    agora = agora or datetime.now(BRT)
    comum = {'Pedido': pedido_id, 'Status': status, 'Motivo': motivo, 'Arquivo': '', 'Linhas_Esperadas': '',
             'Local': texto_local(ped) if ped else '', 'Periodo': texto_periodo(ped) if ped else '',
             'Resolucao': ('Diária' if ped['res'] == 'D' else 'Mensal') if ped else '',
             'Variaveis': ', '.join(ped['variaveis']) if ped else '',
             'Formato': ped.get('formato', 'csv') if ped else '', 'Gerado_em': f'{agora:%Y-%m-%d %H:%M} (BRT)',
             'Versao_Rotina': VERSAO_ROTINA, 'Versao_Painel': VERSAO_PAINEL}
    if not arquivos:
        return [comum]
    resumo = dict(comum, Linhas_Esperadas=str(sum(a['linhas'] for a in arquivos)))
    return ([resumo] + [dict(comum, Arquivo=a['nome'] + '.csv', Linhas_Esperadas=str(a['linhas'])) for a in arquivos]
            + [dict(comum, Arquivo='00_Dicionario_Variaveis_SAB.csv', Linhas_Esperadas=str(len(DICIONARIO)))])


# =========================================================================================
# EARTH ENGINE: o mesmo cálculo do painel (copiado da K14; mudanças marcadas com [E-MAIL])
# =========================================================================================
def _ee():
    import ee
    return ee


def poligonos_do_pedido(ped):
    """construirRegiaoSelecionada do painel: polígonos com Nome_Local_Export, Estado e Municipio."""
    ee = _ee()
    estados = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
    municipios = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
    if ped['tipo'] == 'P':
        feats = [ee.Feature(ee.Geometry.Polygon([v]), {'Nome_Local_Export': f'Poligono_{i + 1}', 'Estado': 'Customizado',
                                                      'Municipio': 'Area_Desenhada'})
                 for i, v in enumerate(ped['poligonos'])]
        return ee.FeatureCollection(feats)
    var_uf = variacoes_busca(ped['estados'])
    if ped['tipo'] == 'M':
        var_mun = variacoes_busca(ped['municipios'])
        return municipios.filter(ee.Filter.And(ee.Filter.inList('ADM1_NAME', var_uf),
                                               ee.Filter.inList('ADM2_NAME', var_mun))).map(
            lambda f: f.set({'Nome_Local_Export': f.get('ADM2_NAME'), 'Municipio': f.get('ADM2_NAME'),
                             'Estado': f.get('ADM1_NAME')}))
    nome_exp = ped['estados'][0] if len(ped['estados']) == 1 else 'Grupo_Estados'
    return estados.filter(ee.Filter.inList('ADM1_NAME', var_uf)).map(
        lambda f: f.set({'Nome_Local_Export': nome_exp, 'Municipio': 'Estado_Completo', 'Estado': f.get('ADM1_NAME')}))


def montar_grade(poligonos):
    """Grade do painel (K14). [E-MAIL] devolve também o número de pares antes do limite (n_pares)."""
    ee = _ee()
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

    pares = junta.map(por_poligono).flatten().map(chave).sort('ChaveOrdenacao')
    lista = pares.toList(LIMITE_PONTOS_GRADE)

    def ponto(i):
        f = ee.Feature(lista.get(i))
        cq = ee.Number(f.get('Classe_Q'))
        return ee.Feature(ee.Geometry.Point([f.get('Lon'), f.get('Lat')]), {
            'Nome_Local_Export': f.get('Local_Ext'), 'Estado': f.get('Estado_Ext'), 'Municipio': f.get('Muni_Ext'),
            'ID_Ponto': ee.String('Ponto_').cat(ee.Number(i).add(1).format('%05d')),
            'Latitude': f.get('Lat'), 'Longitude': f.get('Lon'),
            'Qualidade_Pixel': ee.Algorithms.If(cq.eq(1), 'A', ee.Algorithms.If(cq.eq(2), 'B',
                                                ee.Algorithms.If(cq.eq(3), 'C', '')))})

    return ee.FeatureCollection(ee.List.sequence(0, lista.size().subtract(1)).map(ponto)), pares.size()


def _expandir(img):
    return img.unmask(img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMean(1, 'square', 'pixels'))


def _correcao_mes(mes):
    """montarCorrecaoMes do painel (correção de leitura do solo e do escoamento dos dias V1.0)."""
    ee = _ee()
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


def _brdwgd_do_dia(data):
    """brdwgdDoDia do painel 2026.11.1: o BR-DWGD do dia decodificado como na V1.0, nas 8 bandas do núcleo."""
    ee = _ee()
    vazio = ee.Image.constant([-32768] * 7).rename(['pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs', 'ET'])
    br = ee.Image(ee.ImageCollection(BRDWGD).filterDate(data, data.advance(1, 'day'))
                  .merge(ee.ImageCollection([vazio])).first())
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


def _radiacao_ceu_claro(data):
    """radiacaoCeuClaro do painel: Rso = (0,75 + 2e-5 z) Ra (FAO-56, eq. 21 e 37)."""
    ee = _ee()
    J = ee.Number(data.getRelative('day', 'year')).add(1)
    lat = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180)
    dr = J.multiply(2 * math.pi / 365).cos().multiply(0.033).add(1)
    dec = J.multiply(2 * math.pi / 365).subtract(1.39).sin().multiply(0.409)
    ws = lat.tan().multiply(dec.tan()).multiply(-1).clamp(-1, 1).acos()
    ra = (ws.multiply(lat.sin()).multiply(dec.sin()).add(lat.cos().multiply(dec.cos()).multiply(ws.sin()))
          .multiply(dr).multiply(24 * 60 / math.pi * 0.0820))
    return ra.multiply(ee.Image(ELEVACAO).unmask(0).multiply(2e-5).add(0.75)).rename('rso')


def corrigir_pixels_b(img):
    """[2026.11.03] corrigirPixelsB do painel 2026.11.1: pixels B com o núcleo do BR-DWGD e radiação dos pixels C
    limitada à de céu claro, só nos dias de 1961 a 2025 (o banco não muda)."""
    ee = _ee()
    data = img.date()
    classe = ee.Image(MASCARA).select('classe').unmask(0, False)
    br = _brdwgd_do_dia(data)
    usar_b = classe.eq(2).And(br.select('pr_mm').mask().unmask(0))
    nucleo = [img.select(b).where(usar_b, br.select(b)).rename(b) for b in NUCLEO_B]
    rso = _radiacao_ceu_claro(data)
    rs = ee.Image(nucleo[5])
    nucleo[5] = rs.where(classe.eq(3).And(rs.gt(rso)), rso).rename('rs')
    corrigida = img.addBands(ee.Image.cat(nucleo).toFloat(), None, True)
    return ee.Image(ee.Algorithms.If(data.millis().lt(ee.Date(FIM_HISTORICO_CORRECAO).millis()), corrigida, img))


def area_tem_pixels_bc(geom):
    """areaTemPixelsBC do painel: 1 se a área (retângulo envolvente) tem algum pixel B ou C."""
    ee = _ee()
    classe = ee.Image(MASCARA).select('classe').unmask(0, False)
    r = classe.eq(2).Or(classe.eq(3)).selfMask().reduceRegion(
        reducer=ee.Reducer.anyNonZero(), geometry=geom.bounds(), crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10)
    return ee.Number(ee.Algorithms.If(r.get('classe'), 1, 0))


def colecao(geom, ini, fim):
    """getSABCollectionCorrigida + corrigirSoloEscoamentoV10 + [2026.11.03] corrigirPixelsB + grampo termodinâmico
    do painel (K14). fim exclusivo."""
    ee = _ee()
    corr_mes = ee.List([_correcao_mes(m) for m in range(1, 13)])
    col = ee.ImageCollection(SAB).filterBounds(geom.bounds()).filterDate(ini, fim)

    def preparar(img, com_b):
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
        if com_b:                                           # [2026.11.03] antes do grampo, como no painel
            im = corrigir_pixels_b(im)
        etp = im.select('et_potencial')
        etr = im.select('et_real').min(etp).rename('et_real')
        tr = im.select('transpiracao_mm').min(etr).rename('transpiracao_mm')
        im = im.addBands(ee.Image.cat([etr, tr]), None, True)
        amp = im.select('tmax_C').subtract(im.select('tmin_C')).rename('amplitude_diaria').toFloat()
        dfc = etp.subtract(etr).max(0).rename('deficit_diario').toFloat()
        ce = im.select('pr_mm').subtract(im.select('runoff_sup_mm')).max(0).rename('chuva_efetiva').toFloat()
        return im.addBands(ee.Image.cat([amp, dfc, ce]))

    com, sem = col.map(lambda i: preparar(i, True)), col.map(lambda i: preparar(i, False))
    return ee.ImageCollection(ee.Algorithms.If(area_tem_pixels_bc(geom), com, sem)).sort('system:time_start')


def props_enso(img, enso):
    """[ENSO] As 6 colunas ENSO de um dia (ou do 1º dia do mês, no mensal), pelo mês da imagem no dicionário
    enso['dic'] ('AAAA_MM' -> [fase, RONI, trimestre, fonte]). [2026.11.01] Os dias de previsão usam o mesmo
    dicionário (estimativa por persistência, marcada em Fonte_ENSO); antes saíam 'Previsao (sem classificacao)'.
    Nos meses com fonte CPC ou Estimativa_OISST, as 5 primeiras colunas são as do painel (K16, caso A5)."""
    ee = _ee()
    info = ee.List(ee.Dictionary(enso['dic']).get(img.date().format('YYYY_MM'), ['Sem_Dado', -99, 'N/A', 'Sem_Dado']))
    fase = ee.String(info.get(0))
    roni = ee.Number(info.get(1))
    sem = ee.String(info.get(3)).equals('Sem_Dado')
    nino, nina = fase.equals('El Nino'), fase.equals('La Nina')
    intens = ee.Algorithms.If(nino,
        ee.Algorithms.If(roni.gte(2.0), 'Muito forte (Super)', ee.Algorithms.If(roni.gte(1.5), 'Forte',
            ee.Algorithms.If(roni.gte(1.0), 'Moderado', 'Fraco'))),
        ee.Algorithms.If(nina,
            ee.Algorithms.If(roni.lte(-2.0), 'Muito forte (Super)', ee.Algorithms.If(roni.lte(-1.5), 'Forte',
                ee.Algorithms.If(roni.lte(-1.0), 'Moderada', 'Fraca'))),
            '-'))
    return {'Filtro_ENSO': enso['ascii'], 'Fase_ENSO': fase, 'Intensidade_ENSO': intens,
            'RONI_Trimestre_C': ee.Algorithms.If(sem, '-', roni.format('%.1f')),
            'Trimestre_CPC': info.get(2), 'Fonte_ENSO': info.get(3)}


def filtrar_enso(ic, enso):
    """[ENSO] Recorte do painel: passado só nos meses do cenário; dias de previsão entram todos."""
    ee = _ee()

    def marcar(img):
        versao = ee.String(ee.Algorithms.If(img.propertyNames().contains('versao'), img.get('versao'), 'definitiva'))
        return img.set({'prev_enso': ee.Number(ee.Algorithms.If(ee.List(VERSOES_PREVISAO).contains(versao), 1, 0)),
                        'chave_enso': img.date().format('YYYY_MM')})
    return ic.map(marcar).filter(ee.Filter.Or(ee.Filter.eq('prev_enso', 1),
                                              ee.Filter.inList('chave_enso', ee.List(enso['meses_ok'])))) \
        .sort('system:time_start')


def _redutor_media(bandas):
    """[2026.11.18] Redutor da média do reduceRegions. Com 2 ou mais bandas o Earth Engine já grava cada média com o
    nome da banda; com UMA banda só, grava na propriedade 'mean' (nome do redutor) e o formatar(), que procura o nome
    da banda, deixava a coluna inteira vazia. setOutputs dá à saída o nome da banda nesse caso."""
    ee = _ee()
    bandas = list(bandas)
    return ee.Reducer.mean().setOutputs(bandas) if len(bandas) == 1 else ee.Reducer.mean()


def linhas_diarias(ic, grade, bandas, escala, enso=None):
    """exportarSerieDiaria do painel. [E-MAIL] só as bandas pedidas entram no reduceRegions. [ENSO] colunas ENSO."""
    ee = _ee()

    def por_dia(img):
        versao = ee.String(ee.Algorithms.If(img.propertyNames().contains('versao'), img.get('versao'), 'definitiva'))
        tipo = ee.Dictionary({'definitiva': 'Historico_Observado', 'provisoria_era5': 'Provisorio_ERA5',
                              'provisoria_gfs': 'Previsao_GFS', 'provisoria_gfs_incompleta': 'Previsao_GFS_Parcial',
                              'falha_latencia_gfs': 'Sem_Dado'}).get(versao, 'Desconhecido')
        alg = ee.Algorithms.If(img.propertyNames().contains('versao_algoritmo'), img.get('versao_algoritmo'), 'V1.0')
        janela = ee.Algorithms.If(versao.equals('definitiva'), '12-12 UTC (D-1 a D)', '00-24 UTC')
        conf = ee.Algorithms.If(img.propertyNames().contains('Confianca_Prazo'), img.get('Confianca_Prazo'), '')
        data = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
        extra = props_enso(img, enso) if enso else {}
        return img.select(bandas).reduceRegions(collection=grade, reducer=_redutor_media(bandas), scale=escala).map(
            lambda f: f.set({'Data': data, 'Tipo_Dado': tipo, 'Versao_Algoritmo': alg,
                             'Janela_Chuva_UTC': janela, 'Confianca_Prazo': conf}).set(extra))
    return ic.map(por_dia).flatten()


def linhas_mensais(ic, grade, ano, bandas, escala, enso=None):
    """exportarSerieMensal do painel, um ano. [E-MAIL] só as bandas pedidas. [ENSO] colunas do 1º dia do mês."""
    ee = _ee()
    inicio = ee.Date.fromYMD(ano, 1, 1)
    soma = [b for b in BANDAS_SOMA if b in bandas]
    media = [b for b in BANDAS_MEDIA if b in bandas]

    def mes(m):
        d0 = inicio.advance(m, 'month')
        d1 = d0.advance(1, 'month')
        icm = ic.filterDate(d0, d1)
        partes = ([icm.select(soma).sum()] if soma else []) + ([icm.select(media).mean()] if media else [])
        img = partes[0] if len(partes) == 1 else partes[0].addBands(partes[1])
        versoes = icm.map(lambda im: im.set('alg_tmp', ee.Algorithms.If(
            im.propertyNames().contains('versao_algoritmo'), im.get('versao_algoritmo'), 'V1.0'))
        ).aggregate_array('alg_tmp').distinct().sort()
        dias_mes = d1.advance(-1, 'day').get('day')
        if enso:
            primeira = ee.Image(ee.Algorithms.If(icm.size().gt(0), icm.first(),
                                                 ee.Image(0).set('system:time_start', d0.millis())))
            img = img.set(props_enso(primeira, enso))
        return img.set('Data', d0.format('YYYY-MM-dd'), 'n_imgs', icm.size(),
                       'Versao_Algoritmo', ee.List(versoes).join('+'), 'Dias_no_Mes', dias_mes,
                       'Mes_Completo', ee.Algorithms.If(icm.size().eq(dias_mes), 'sim', 'nao'))

    icm = ee.ImageCollection.fromImages(ee.List.sequence(0, 11).map(mes)).filter(ee.Filter.gt('n_imgs', 0))

    def reduzir(img):
        extra = {c: img.get(c) for c in COLUNAS_ENSO} if enso else {}
        return img.reduceRegions(collection=grade, reducer=_redutor_media(soma + media), scale=escala).map(
            lambda f: f.set({'Data': img.get('Data'), 'Tipo_Dado': 'Agregado_Mensal',
                             'Versao_Algoritmo': img.get('Versao_Algoritmo'), 'N_Dias': img.get('n_imgs'),
                             'Dias_no_Mes': img.get('Dias_no_Mes'), 'Mes_Completo': img.get('Mes_Completo')}).set(extra))
    return icm.map(reduzir).flatten()


def formatar(fc, cods, extras):
    """formatarExportacaoClima do painel (números com ponto, "18.40"). [E-MAIL] só as colunas pedidas."""
    ee = _ee()
    numericas = [('Latitude', 'Latitude', 5), ('Longitude', 'Longitude', 5)] + \
                [(col, banda, casas) for c, col, banda, casas, _ in VARIAVEIS if c in cods]

    def linha(f):
        data = ee.String(f.get('Data'))
        partes = data.split('-').cat(ee.List(['', '', '']))
        d = f.toDictionary()

        def valor(banda, casas):
            v = ee.Number(d.get(banda, -9999))
            return ee.Algorithms.If(v.eq(-9999), None, v.format('%.' + str(casas) + 'f'))

        props = {'Tipo_Dado': d.get('Tipo_Dado', 'Agregado'), 'Versao_Algoritmo': d.get('Versao_Algoritmo', ''),
                 'Data_Completa': data, 'Ano': partes.get(0), 'Mes': partes.get(1), 'Dia': partes.get(2),
                 'N_Ponto': f.get('ID_Ponto'), 'Estado': f.get('Estado'), 'Municipio': f.get('Municipio')}
        for col, banda, casas in numericas:
            props[col] = valor(banda, casas)
        for col in extras:
            props[col] = d.get(col, '')
        return ee.Feature(None, props)
    return fc.map(linha)


def tabela_ee(linhas, colunas):
    ee = _ee()
    return ee.FeatureCollection([ee.Feature(None, {c: str(l.get(c, '')) for c in colunas}) for l in linhas])


def dicionario_ee():
    ee = _ee()
    return ee.FeatureCollection([ee.Feature(None, {'Variavel': v, 'Descricao': d, 'Unidade': u})
                                 for v, d, u in DICIONARIO])


def fc_do_arquivo(ped, arq, grade, geom, escala, enso=None):
    """O CSV de um arquivo do plano: o mesmo pedido que o painel faz para aquele local e ano.
    enso: ctx['enso'] (sempre, no e-mail); o recorte por fenômeno só com enso['filtro']."""
    ee = _ee()
    pontos = grade.filter(ee.Filter.eq('Nome_Local_Export', arq['local']))
    ini_ped, fim_ped = ped['ini'], ped['fim'] + timedelta(days=1)
    ic = colecao(geom, str(ped['ini']), str(fim_ped))
    a, b = max(arq['ini'], ini_ped), min(arq['fim'], fim_ped)
    if enso and enso.get('filtro'):
        ic = filtrar_enso(ic, enso)
    ic = ic.filterDate(str(a), str(b))
    bandas = bandas_do_pedido(ped['variaveis'])
    extra = COLUNAS_ENSO if enso else []
    if ped['res'] == 'D':
        return formatar(linhas_diarias(ic, pontos, bandas, escala, enso), ped['variaveis'], EXTRAS_DIARIA + extra)
    return formatar(linhas_mensais(ic, pontos, arq['ano'], bandas, escala, enso), ped['variaveis'], EXTRAS_MENSAL + extra)


def avaliar(ped):
    """Uma ida ao servidor: pontos por local, pares, nomes encontrados e datas das imagens do período."""
    ee = _ee()
    poligonos = poligonos_do_pedido(ped)
    grade, n_pares = montar_grade(poligonos)
    geom = poligonos.geometry()
    fim = ped['fim'] + timedelta(days=1)
    datas = ee.ImageCollection(SAB).filterBounds(geom.bounds()).filterDate(str(ped['ini']), str(fim)) \
        .aggregate_array('system:time_start')
    info = ee.Dictionary({'pares': n_pares, 'nomes': poligonos.aggregate_array('Nome_Local_Export'),
                          'estados': poligonos.aggregate_array('Estado'),
                          'pontos': grade.aggregate_array('Nome_Local_Export'), 'datas': datas}).getInfo()
    if ped['tipo'] == 'M':
        faltam = faltando(ped['municipios'], info['nomes'])
        if faltam:
            raise PedidoInvalido('Município não encontrado nos estados pedidos: ' + ', '.join(faltam) + '.')
    if ped['tipo'] == 'E':
        faltam = faltando(ped['estados'], info['estados'])
        if faltam:
            raise PedidoInvalido('Estado não encontrado no mapa de limites (GAUL): ' + ', '.join(faltam) + '.')
    locais = contar_pontos(info['pontos'])
    sem_pontos = [n for n in dict.fromkeys(info['nomes']) if n not in dict(locais)]
    # uma data por imagem (com repetições, se houver): o CSV tem uma linha por ponto e por imagem
    dias = sorted(datetime.fromtimestamp(t / 1000, timezone.utc).date() for t in info['datas'])
    return poligonos, grade, geom, int(info['pares']), locais, sem_pontos, dias


def _datas_do_periodo(ee, geom, ped):
    fim = ped['fim'] + timedelta(days=1)
    return ee.ImageCollection(SAB).filterBounds(geom.bounds()).filterDate(str(ped['ini']), str(fim)) \
        .aggregate_array('system:time_start')


def _dias(lista_ms):
    return sorted(datetime.fromtimestamp(t / 1000, timezone.utc).date() for t in lista_ms)


def resolver_municipios(ped):
    """[E-MAIL] Troca os nomes digitados pelos nomes do GAUL (sem ligar para acento, maiúscula ou hífen). Pedidos do
    painel já vêm com o nome do GAUL e ficam iguais."""
    ee = _ee()
    nomes = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM0_NAME', 'Brazil')) \
        .filter(ee.Filter.inList('ADM1_NAME', variacoes_busca(ped['estados']))).aggregate_array('ADM2_NAME').getInfo()
    achados, faltam = casar_municipios(ped['municipios'], nomes)
    if faltam:
        raise PedidoInvalido('Município não encontrado nos estados pedidos: ' + '; '.join(faltam) + '.')
    ped['municipios'] = achados
    return ped


def avaliar_pedido(ped):
    """Contexto do pedido. [2026.11.01] O ENSO é sempre calculado (colunas em todo CSV); o recorte dos dias só com
    filtro. Antes de qualquer conta no Earth Engine, o tamanho é estimado pela área (conferir_estimativa)."""
    conferir_estimativa(ped)
    ctx = _avaliar_locais(ped)
    return aplicar_enso(ctx, ped)


def _roni_oisst(ee):
    """[ENSO] indiceRONI_Sat do painel: RONI estimado pelo OISST (climatologia e fator de variância de 1991-2020,
    média móvel de 3 meses centrada, arredondado em 0,1). Só os meses depois da última estação oficial são usados."""
    col = ee.ImageCollection('NOAA/CDR/OISST/V2_1')
    proj = col.first().projection()
    area_px = ee.Image.pixelArea()
    sst = col.select('sst').map(lambda img: img.multiply(0.01).copyProperties(img, ['system:time_start', 'status']))
    hoje = ee.Date(int(time.time() * 1000))
    limite = ee.Date.fromYMD(hoje.get('year'), hoje.get('month'), 1)
    inicio = ee.Date('1991-01-01')
    total = limite.difference(inicio, 'month').round()

    def mes(off):
        d0 = inicio.advance(off, 'month')
        d1 = d0.advance(1, 'month')
        cm = sst.filterDate(d0, d1)
        n = cm.aggregate_array('system:time_start').distinct().size()
        completo = n.eq(d1.difference(d0, 'day').round())
        im = ee.Image(ee.Algorithms.If(completo, cm.mean(), ee.Image.constant(-999).toFloat().rename('sst')))
        nome = ee.String('Y').cat(d0.get('year').format('%04d')).cat('M').cat(d0.get('month').format('%02d'))
        return im.rename([nome]).set('system:time_start', d0.millis())
    pilha = ee.ImageCollection(ee.List.sequence(0, total.subtract(1)).map(mes)).toBands()

    def media(geom):
        def somar(img):
            return img.reduceRegion(reducer=ee.Reducer.sum(), geometry=geom, crs=proj, maxPixels=1e10, tileScale=4)
        num = somar(pilha.multiply(area_px))
        den = somar(pilha.mask().multiply(area_px))
        nomes = pilha.bandNames()
        return ee.Dictionary.fromLists(nomes, nomes.map(lambda b: ee.Number(num.get(b)).divide(ee.Number(den.get(b)))))
    nino34 = media(ee.Geometry.Rectangle([-170, -5, -120, 5], None, False))
    trop = media(ee.Geometry.Rectangle([-180, -20, 180, 20], None, False))

    def linha(nome):
        st = ee.String(nome)
        i = st.rindex('Y')
        ano = ee.Number.parse(st.slice(i.add(1), i.add(5)))
        m = ee.Number.parse(st.slice(i.add(6), i.add(8)))
        return ee.Feature(None, {'ano': ano, 'mes': m, 'sst_nino34': nino34.get(nome), 'sst_tropical': trop.get(nome),
                                 'system:time_start': ee.Date.fromYMD(ano, m, 1).millis()})
    mensal = ee.FeatureCollection(pilha.bandNames().map(linha)).filter(ee.Filter.gt('sst_nino34', -900))
    clima = ee.FeatureCollection(ee.List.sequence(1, 12).map(lambda m: ee.Feature(None, {
        'mes': m,
        'clima_nino34': mensal.filter(ee.Filter.eq('mes', m)).filter(ee.Filter.gte('ano', 1991))
                              .filter(ee.Filter.lte('ano', 2020)).aggregate_mean('sst_nino34'),
        'clima_tropical': mensal.filter(ee.Filter.eq('mes', m)).filter(ee.Filter.gte('ano', 1991))
                                .filter(ee.Filter.lte('ano', 2020)).aggregate_mean('sst_tropical')})))
    com_clima = ee.FeatureCollection(ee.Join.saveFirst('climatologia').apply(
        mensal, clima, ee.Filter.equals(leftField='mes', rightField='mes')))

    def anomalia(f):
        c = ee.Feature(f.get('climatologia'))
        a_n = ee.Number(f.get('sst_nino34')).subtract(ee.Number(c.get('clima_nino34')))
        a_t = ee.Number(f.get('sst_tropical')).subtract(ee.Number(c.get('clima_tropical')))
        return f.set({'anom_nino34': a_n, 'anom_tropical': a_t, 'anom_relativa': a_n.subtract(a_t)})
    anom = com_clima.map(anomalia)
    base = anom.filter(ee.Filter.And(ee.Filter.gte('ano', 1991), ee.Filter.lte('ano', 2020)))
    fator = ee.Number(base.reduceColumns(ee.Reducer.stdDev(), ['anom_nino34']).get('stdDev')).divide(
        ee.Number(base.reduceColumns(ee.Reducer.stdDev(), ['anom_relativa']).get('stdDev')))
    ajust = anom.map(lambda f: f.set('anom_ajustada', ee.Number(f.get('anom_relativa')).multiply(fator))) \
        .sort('system:time_start')
    janela = ee.Filter.maxDifference(difference=1000 * 60 * 60 * 24 * 40, leftField='system:time_start',
                                     rightField='system:time_start')
    brutos = ee.Join.saveAll('trimestre').apply(ajust, ajust, janela)

    def roni(f):
        valores = ee.List(f.get('trimestre')).map(lambda x: ee.Feature(x).get('anom_ajustada'))
        r = ee.Number(valores.reduce(ee.Reducer.mean()))
        return ee.Feature(None, {'ano': f.get('ano'), 'mes': f.get('mes'), 'RONI': r.multiply(10).round().divide(10),
                                 'n_meses': valores.size()})
    # [2026.11.01] também os trimestres com 2 dos 3 meses (só o último, ainda sem o mês seguinte, é usado: parcial)
    return ee.FeatureCollection(brutos).map(roni).filter(ee.Filter.gte('n_meses', 2))


def serie_roni():
    """[ENSO] colecaoCompleta do painel: a série oficial do CPC (asset RONI_CPC_v6) + a estimativa OISST (trimestre
    completo) só depois da última estação oficial, em ordem. Devolve (serie, parciais): serie =
    [{'ano', 'mes', 'RONI', 'Trimestre', 'Fonte'}], a mesma do painel; parciais = trimestres OISST com 2 dos 3
    meses depois do fim da série (em geral só o último mês completo do OISST), para estender_enso."""
    ee = _ee()
    oficial = ee.FeatureCollection(RONI_ASSET).map(lambda f: ee.Feature(None, {
        'ano': f.get('ano'), 'mes': f.get('mes'), 'RONI': f.get('RONI'),
        'Trimestre': ee.Algorithms.If(f.propertyNames().contains('Trimestre'), f.get('Trimestre'), '')}))
    info = ee.Dictionary({'of': oficial.toList(5000).map(lambda f: ee.Feature(f).toDictionary()),
                          'est': _roni_oisst(ee).toList(5000).map(lambda f: ee.Feature(f).toDictionary())}).getInfo()
    of = sorted(({'ano': int(x['ano']), 'mes': int(x['mes']), 'RONI': float(x['RONI']),
                  'Trimestre': x.get('Trimestre', ''), 'Fonte': 'CPC'} for x in info['of']),
                key=lambda x: (x['ano'], x['mes']))
    return juntar_roni(of, info['est'])


def aplicar_enso(ctx, ped):
    """[ENSO] Classifica os meses (como o painel), estende a série até o fim da previsão e, com filtro, deixa nos
    dias só os meses do cenário (fonte CPC ou Estimativa_OISST) e os dias de previsão. Sem filtro, uma falha na
    série RONI não derruba o pedido: as colunas ENSO saem Sem_Dado e o manifesto avisa."""
    ee = _ee()
    filtro = bool(ped.get('enso'))
    hoje = datetime.now(BRT).date()
    try:
        serie, parciais = serie_roni()
        classif = classificar_enso(serie)
        dic = dicionario_enso(estender_enso(classif, parciais, max(ped['fim'], hoje + timedelta(days=20))))
        aviso = ''
    except Exception as e:
        if filtro:
            raise
        print(f'   ⚠️ série RONI indisponível ({str(e)[:150]}); colunas ENSO vazias neste pedido.')
        classif, dic = [], {}
        aviso = 'Série RONI indisponível no momento: as colunas ENSO saíram como Sem_Dado.'
    ascii_ = ped['enso']['ascii'] if filtro else 'Sem filtro'
    if not filtro:
        ctx = dict(ctx, enso={'ascii': ascii_, 'filtro': False, 'meses_ok': [], 'dic': dic})
        if aviso:
            ctx['avisos'] = (ctx['avisos'] + ' ' if ctx['avisos'] else '') + aviso
        return ctx
    meses_ok = sorted(f"{x['ano']:04d}_{x['mes']:02d}" for x in classif if no_cenario(x, ped['enso']['valor']))
    fim = ped['fim'] + timedelta(days=1)
    col = ee.ImageCollection(SAB).filterBounds(ctx['area'].bounds()).filterDate(str(ped['ini']), str(fim)).map(
        lambda img: img.set('v_enso', ee.Algorithms.If(img.propertyNames().contains('versao'), img.get('versao'),
                                                         'definitiva')))
    info = ee.Dictionary({'t': col.aggregate_array('system:time_start'), 'v': col.aggregate_array('v_enso')}).getInfo()
    dias = sorted(datetime.fromtimestamp(t / 1000, timezone.utc).date() for t, v in zip(info['t'], info['v'])
                  if v in VERSOES_PREVISAO or chave_mes(datetime.fromtimestamp(t / 1000, timezone.utc)) in meses_ok)
    if not dias:
        raise PedidoInvalido(f"Nenhum mês do período teve o fenômeno \"{ped['enso']['ascii']}\". "
                             'Amplie o período ou escolha outro fenômeno.')
    ctx = dict(ctx, dias=dias, enso={'ascii': ascii_, 'filtro': True, 'meses_ok': meses_ok, 'dic': dic})
    no_periodo = [m for m in meses_ok if str(ped['ini'])[:7].replace('-', '_') <= m <= str(ped['fim'])[:7].replace('-', '_')]
    ctx['avisos'] = (ctx['avisos'] + ' ' if ctx['avisos'] else '') + \
        f"Filtro ENSO {ped['enso']['ascii']}: {len(no_periodo)} mês(es) do passado no período (a previsão entra sempre)."
    return ctx


def _avaliar_locais(ped):
    """Contexto do pedido: locais (nome, pontos), grade e área de cada local, escala, pares, dias e avisos.
    Estados, municípios e polígonos usam avaliar() (o caminho conferido pela K16); estados separados e pontos são do
    e-mail."""
    ee = _ee()
    if ped['tipo'] in ('E', 'M', 'P') and not ped.get('separar'):
        if ped['tipo'] == 'M':
            resolver_municipios(ped)
        _, grade, geom, n_pares, locais, sem_pontos, dias = avaliar(ped)
        return {'locais': locais, 'por_local': {n: (grade, geom) for n, _ in locais}, 'n_pares': n_pares,
                'dias': dias, 'avisos': ('Sem pontos da grade (nenhum arquivo): ' + ', '.join(sem_pontos) + '.')
                if sem_pontos else '', 'escala': ESCALA_PONTO if ped['tipo'] == 'P' else ESCALA_AREA, 'area': geom}

    if ped['tipo'] == 'E':
        # uma grade por estado (sep=1, formulário), um arquivo por estado; no máximo LIMITE_ESTADOS estados
        grades = {}
        for e in ped['estados']:
            pol = poligonos_do_pedido({'tipo': 'E', 'estados': [e]})
            grade, pares = montar_grade(pol)
            grades[e] = (grade, pol.geometry(), pares)
        area = poligonos_do_pedido({'tipo': 'E', 'estados': ped['estados']}).geometry()
        info = ee.Dictionary({'n': ee.Dictionary({e: g[0].size() for e, g in grades.items()}),
                              'pares': ee.Dictionary({e: g[2] for e, g in grades.items()}),
                              'datas': _datas_do_periodo(ee, area, ped)}).getInfo()
        locais = [(e, int(info['n'][e])) for e in ped['estados'] if int(info['n'][e]) > 0]
        return {'locais': locais, 'por_local': {e: (grades[e][0], grades[e][1]) for e, _ in locais},
                'n_pares': max(int(v) for v in info['pares'].values()), 'dias': _dias(info['datas']), 'avisos': '',
                'escala': ESCALA_AREA, 'area': area}

    # pontos: o pixel de 0,1° que contém cada ponto, com a classe da máscara de qualidade
    centros = [centro_do_pixel(p['lat'], p['lon']) for p in ped['pontos']]
    pts = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([lon, lat]), {'i': i}) for i, (lat, lon) in enumerate(centros)])
    classes = ee.Image(MASCARA).select('classe').unmask(0, False).reduceRegions(
        collection=pts, reducer=ee.Reducer.first(), crs=CRS, crsTransform=TRANSFORM)
    geom = pts.geometry()
    info = ee.Dictionary({'classes': classes.aggregate_array('first'), 'idx': classes.aggregate_array('i'),
                          'datas': _datas_do_periodo(ee, geom, ped)}).getInfo()
    classe = dict(zip(info['idx'], info['classes']))
    letra = {1: 'A', 2: 'B', 3: 'C'}
    feats, fora, n = [], [], 0
    for i, (p, (lat, lon)) in enumerate(zip(ped['pontos'], centros)):
        c = int(classe.get(i) or 0)
        if c == 4:     # como na grade do painel: pixel sem BR-DWGD com centro fora do Brasil fica de fora
            fora.append(p['nome'])
            continue
        n += 1
        feats.append(ee.Feature(ee.Geometry.Point([lon, lat]), {
            'Nome_Local_Export': 'Pontos', 'Estado': 'Coordenada',
            'Municipio': f"{p['nome']} ({p['lat']:.5f}, {p['lon']:.5f})", 'ID_Ponto': f'Ponto_{n:05d}',
            'Latitude': lat, 'Longitude': lon, 'Qualidade_Pixel': letra.get(c, '')}))
    if not feats:
        raise PedidoInvalido('Todos os pontos caem em pixels de borda, fora da grade do banco.')
    grade = ee.FeatureCollection(feats)
    return {'locais': [('Pontos', n)], 'por_local': {'Pontos': (grade, geom)}, 'n_pares': n, 'dias': _dias(info['datas']),
            'avisos': ('Pontos fora da grade (pixel de borda, sem arquivo): ' + ', '.join(fora) + '.') if fora else '',
            'escala': ESCALA_PONTO, 'area': geom}


MSG_GRANDE = ('O pedido é grande demais para o Earth Engine calcular de uma vez (limite de memória ou de tempo). '
              'Divida em pedidos menores: menos anos, menos estados ou a resolução mensal.')


def e_pedido_grande(erro):
    t = str(erro).lower()
    return any(x in t for x in ('memory limit', 'computation timed out', 'limite de memória'))


def tarefas_existentes(prefixo):
    """Descrições das tarefas deste pedido já enviadas e não falhas (para não enviar duas vezes)."""
    ee = _ee()
    try:
        ops = ee.data.listOperations()
    except Exception as e:
        print(f'   ⚠️ não consegui listar as tarefas ({str(e)[:120]}); sigo sem a conferência de repetidas.')
        return set()
    saida = set()
    for op in ops or []:
        md = op.get('metadata', {})
        if str(md.get('description', '')).startswith(prefixo) and md.get('state') not in ('FAILED', 'CANCELLED'):
            saida.add(md['description'])
    return saida


def exportar(fc, descricao, pasta, nome, colunas, ja_enviadas):
    ee = _ee()
    if descricao in ja_enviadas:
        print(f'   ♻️ {nome}: já enviada antes ({descricao})')
        return None
    t = ee.batch.Export.table.toDrive(collection=fc, description=descricao, folder=pasta, fileNamePrefix=nome,
                                      fileFormat='CSV', selectors=colunas)
    t.start()
    print(f'   🚀 {nome}: tarefa {t.id}')
    return t.id


def esperar_tarefa(id_tarefa, limite_s=300, intervalo_s=5):
    """Espera a tarefa terminar (até limite_s). Duas exportações que começam juntas para uma pasta que ainda não
    existe podem criar DUAS pastas com o mesmo nome no Drive; com o manifesto pronto antes, as outras usam a dele."""
    ee = _ee()
    t0 = time.time()
    while time.time() - t0 < limite_s:
        try:
            estado = ee.data.getTaskStatus([id_tarefa])[0].get('state', '')
        except Exception as e:
            print(f'   ⚠️ não consegui ler o estado do manifesto ({str(e)[:100]}); sigo.')
            return None
        if estado in ('COMPLETED', 'SUCCEEDED', 'FAILED', 'CANCELLED'):
            print(f'   manifesto: {estado} em {time.time() - t0:.0f} s')
            return estado
        time.sleep(intervalo_s)
    print(f'   ⚠️ manifesto ainda na fila depois de {limite_s} s; sigo (o Apps Script junta pastas repetidas).')
    return None


def recusar(pedido_id, status, motivo, ped, simular):
    """Grava só o manifesto, com status 'recusado' (pedido fora das regras) ou 'falha' (erro do servidor)."""
    print(f'❌ PEDIDO {status.upper()}: {motivo}')
    if simular:
        return
    exportar(tabela_ee(linhas_manifesto(pedido_id, status, motivo, ped), COLUNAS_MANIFESTO),
             descricao_tarefa(pedido_id, 0), pasta_do_pedido(pedido_id), f'00_Pedido_{pedido_id}', COLUNAS_MANIFESTO,
             tarefas_existentes(descricao_tarefa(pedido_id, 0)))


def atender(pedido_id, codigo, simular, hoje=None):
    ee = _ee()
    t0 = time.time()
    print(f'🔎 SAB, pedido {pedido_id} | rotina {VERSAO_ROTINA} | painel {VERSAO_PAINEL} | '
          f'earthengine-api {getattr(ee, "__version__", "?")} | {"SIMULAÇÃO (não exporta)" if simular else "EXPORTAÇÃO"}')
    print(f'   código: {codigo}')
    if not re.match(r'^[A-Za-z0-9_-]{4,40}$', pedido_id or ''):
        print('❌ ID do pedido inválido (só letras, números, _ e -, de 4 a 40).')
        return 2
    ee.Initialize(project=PROJETO)
    hoje = hoje or datetime.now(BRT).date()
    ped = None
    try:
        ped = validar(ler_codigo(codigo), hoje)
        print(f"   pedido: {texto_local(ped)} | {texto_periodo(ped)} | "
              f"{'diária' if ped['res'] == 'D' else 'mensal'} | variáveis: {', '.join(ped['variaveis'])}")
        ctx = avaliar_pedido(ped)
        locais, dias = ctx['locais'], ctx['dias']
        print(f"   grade: {ctx['n_pares']} pares | " + ' | '.join(f'{n}: {k} pontos' for n, k in locais) +
              (f" | {ctx['avisos']}" if ctx['avisos'] else '') +
              f' | {len(dias)} imagens' + (f' ({dias[0]} a {dias[-1]})' if dias else ''))
        arquivos = planejar(ped['res'], locais, dias, sufixo=('_' + ped['enso']['arquivo']) if ped.get('enso') else '')
        total = conferir_limites(ctx['n_pares'], locais, arquivos)
    except PedidoInvalido as e:
        recusar(pedido_id, 'recusado', str(e), ped, simular)
        return 0
    except Exception as e:                      # erro do servidor: avisa pelo manifesto e marca a execução
        if e_pedido_grande(e):                  # [2026.11.01] memória ou tempo do Earth Engine: recusa explicada
            recusar(pedido_id, 'recusado', MSG_GRANDE + f' (Earth Engine: {str(e)[:120]})', ped, simular)
            return 0
        recusar(pedido_id, 'falha', 'Erro no servidor do Earth Engine: ' + str(e)[:300], ped, simular)
        raise
    nota = ctx['avisos']
    print(f'   plano: {len(arquivos)} arquivo(s) de dados, {milhar(total)} linhas')
    for a in arquivos:
        print(f"      {a['nome']}.csv  {milhar(a['linhas'])} linhas")
    if simular:
        print(f'✅ SIMULAÇÃO OK em {time.time() - t0:.0f} s: nada foi exportado.')
        return 0

    pasta = pasta_do_pedido(pedido_id)
    ja = tarefas_existentes(f'SABPED_{pedido_id}_')
    escala = ctx['escala']
    colunas = colunas_do_pedido(ped['res'], ped['variaveis'])
    print(f'\n   Exportando para a pasta {pasta} do Drive (manifesto, dicionário e {len(arquivos)} arquivo(s)):')
    id_man = exportar(tabela_ee(linhas_manifesto(pedido_id, 'aceito', nota, ped, arquivos), COLUNAS_MANIFESTO),
                      descricao_tarefa(pedido_id, 0), pasta, f'00_Pedido_{pedido_id}', COLUNAS_MANIFESTO, ja)
    if id_man:
        esperar_tarefa(id_man)   # a pasta passa a existir antes das outras exportações (evita pasta repetida)
    exportar(dicionario_ee(), descricao_tarefa(pedido_id, 1), pasta, '00_Dicionario_Variaveis_SAB',
             ['Variavel', 'Descricao', 'Unidade'], ja)
    for k, a in enumerate(arquivos, start=2):
        grade, geom = ctx['por_local'][a['local']]
        exportar(fc_do_arquivo(ped, a, grade, geom, escala, ctx['enso']), descricao_tarefa(pedido_id, k), pasta, a['nome'],
                 colunas, ja)
    print(f'\n✅ {len(arquivos) + 2} exportação(ões) na fila do Earth Engine em {time.time() - t0:.0f} s. '
          'O Apps Script entrega o link quando todas terminarem.')
    return 0


if __name__ == '__main__':
    sys.exit(atender(os.environ.get('PEDIDO_ID', '').strip(), os.environ.get('CODIGO', ''),
                     os.environ.get('SIMULAR', '0').strip() in ('1', 'true', 'True')))
