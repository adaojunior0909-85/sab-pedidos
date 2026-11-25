# =========================================================================================
# TÍTULO: Script 3 V2.1 - Motor Gerador da Base de Calibração Preditiva (GFS v16 x BR-DWGD)
# RESUMO: [V4 M03-14] Para cada dia do BR-DWGD, compara o que o GFS previu para aquele dia com
# cada prazo de 1 a 15 dias de antecedência e junta os prazos em quatro faixas: L1 = {1},
# L2a5 = {2,3,4,5}, L6a10 = {6,...,10} e L11a15 = {11,...,15}. Exporta 12 matrizes mensais com
# média, desvio-padrão e número de pares por pixel. O Motor SAB V1.5 usa as médias (bandas _m_) para
# calibrar a previsão e, na escala de variância, também os desvios (_s_) da Tmax e da Tmin (V4.1, K8) e da
# umidade relativa e da radiação (revisão K9A); as contagens (n_) servem para conferência.
# [Revisão K9A] Só este comentário mudou: o cálculo e as 100 bandas da matriz são os mesmos.
# [V4 D1] Período: só o GFS v16 (decisão do usuário em 20/10/2026). O v16 entrou em 22/03/2021 às
# 12 UTC, então entram as rodadas 00Z criadas de 23/03/2021 a 31/12/2025, e o dia previsto vai
# até 31/12/2025 (último dia do BR-DWGD). O corte é pela data de CRIAÇÃO da rodada: o prazo L
# só tem dia previsto a partir de 23/03/2021 + (L-1) dias. Cerca de 4,8 anos.
# [V4 M03-03] Para cada prazo L, o par é o dia D do BR-DWGD com a rodada 00Z de D-(L-1), nas horas
# de previsão (24(L-1), 24L]. Os pares de todos os prazos de uma faixa entram na mesma média, e
# o BR-DWGD de cada faixa é calculado exatamente nos mesmos pares (e pixels) que o GFS.
#
# MUDANÇAS V4 (20/10/2026) - versão da matriz V2.1
#   [V4 D1]     Só GFS v16: rodadas 00Z criadas de 2021-03-23 a 2025-12-31; dia previsto até 2025-12-31.
#   [V4 M03-04] O corte é pela data de criação da rodada, não pelo dia previsto.
#   [V4 M03-03] Todos os dias de cada faixa (a V2 usava só os dias 1, 3, 8 e 13).
#   [V4 M03-08] GFS de cada par mascarado pela máscara diária do BR-DWGD (mesma pegada nas 12 bandas).
#   [V4 M03-06] Uma redução por faixa (média + desvio + contagem) e 4 bandas n_{faixa}: 100 bandas.
#   [V4 M03-05] Propriedades do contrato (versao_matriz 'V2.1', n_pares_{faixa} calculado no servidor
#               etc.); reexecução segura: pula só o mês já gerado na V2.1, e um asset de outra
#               versão (ou sem versão) para o script com ❌ antes de enviar qualquer tarefa.
#   [V4 M03-09] Pula o mês cuja tarefa GERAR_MATRIZ_GFS_V2_MM esteja na fila (READY/RUNNING);
#               nenhum erro é engolido.
#   [V4 M03-10] Contagem impressa contra o máximo possível (⚠️ abaixo de 85%); exportação pelo
#               retângulo do Brasil (poligonoBrasil.bounds()) com o crsTransform nativo.
#   [V4 M03-14] Cabeçalho e comentários corrigidos (datas, épocas, faixas, uso das bandas).
#   [V4 M03-11] Composições do GFS seguras para coleção vazia (composto_seguro): uma rodada ausente
#               não derruba a tarefa no ramo não escolhido do ee.Algorithms.If.
#   [V4 revisão] Bandas n_{faixa} gravadas em Float32 (valores inteiros), como as outras 96.
#
# [V4 M03-14] SOBRE AS DATAS DA V2: a V2 começava em 08/02/2017 (L1, L2a5, L6a10) e em 13/06/2019
# (L11a15), datas do teste F5 da auditoria de 20/10/2026. O F5 estava errado: contava a hora 0
# (f000) entre as 120 saídas horárias, e toda rodada com f000 reprovava (M08-01). A rodada de
# 10/01/2017 já tinha 384 h com saída horária até 120 h, e há rodadas de 384 h desde 24/07/2016
# (passo até 120 h em ago-dez/2016 A CONFIRMAR). A V2.1 não depende dessas datas: usa só o GFS
# v16, com saídas de 1 em 1 h até 120 h e de 3 em 3 h de 120 a 384 h em todas as rodadas.
#
# CORREÇÕES DA V2 EM RELAÇÃO À V1 (mantidas na V2.1)
#   - Reamostragem bilinear aplicada a cada imagem do GFS ANTES de compor. O .resample()
#     sobre a composição (V1) não vale para composições no Earth Engine.
#   - Radiação pela média dos 4 blocos de 6 h (horas múltiplas de 6), como a chuva. A auditoria
#     de 20/10/2026 (item F4) mostrou que o fluxo de onda curta do GFS é a média acumulada desde
#     o início do bloco de 6 h; a média simples das saídas superestimava a radiação em 3% a 11%.
#   - Faixas de prazo: a V1 só usava o 1º dia de previsão e o motor aplicava a mesma
#     calibração até o 15º dia.
#   - Rodada só entra se estiver completa (todas as horas esperadas e os 4 blocos de chuva).
#   - BR-DWGD e GFS pareados no mesmo conjunto de dias, faixa a faixa.
#   - Valor de ausência -32768 do BR-DWGD mascarado (igual à matriz climatológica).
#   - ET de Hargreaves removida: não era usada pelo motor e faltava o fator 0,408.
#
# NÃO SOBRESCREVE a matriz V1: grava em SICSB_MATRIZ_GFS_V2.
# =========================================================================================

import ee
import time
from datetime import date, datetime, timedelta, timezone   # [V4 M03-05/M03-10] máximos e gerado_em

print("🔄 Conectando à infraestrutura do Google Earth Engine...")
try:
    ee.Initialize(project='clima-492922')
    print("✔️ Google Earth Engine inicializado com sucesso!")
except Exception:
    ee.Authenticate()
    ee.Initialize(project='clima-492922')

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

if _escrita_bloqueada_na_sessao():
    raise RuntimeError('❌ ' + MSG_SESSAO_TRAVADA)

# =========================================================================
# 1. CONFIGURAÇÕES
# =========================================================================
ASSET_SICSB_REAL = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ASSET_DESTINO_MATRIZ_GFS = 'projects/clima-492922/assets/SICSB_MATRIZ_GFS_V2'
COL_GFS = 'NOAA/GFS0P25'

# [V4 D1/M03-04] Só GFS v16. O corte é pela data de CRIAÇÃO da rodada 00Z, não pelo dia previsto.
VERSAO_MATRIZ = 'V2.1'
MODELO_GFS = 'GFS v16'
INICIO_RODADAS = '2021-03-23'   # 1ª rodada 00Z do GFS v16 (o v16 entrou em 22/03/2021 às 12 UTC)
FIM_DIAS = '2025-12-31'         # último dia previsto (último dia do BR-DWGD)
DATA_FIM = '2026-01-01'         # exclusivo: inclui 31/12/2025, último dia do BR-DWGD

# [V4 M03-03] Faixa de prazo -> TODOS os prazos (dias de antecedência) que entram na matriz.
# O motor aplica a faixa L11a15 também ao 16º dia (extrapolação).
FAIXAS = [('L1', [1]), ('L2a5', [2, 3, 4, 5]), ('L6a10', [6, 7, 8, 9, 10]), ('L11a15', [11, 12, 13, 14, 15])]

LIMIAR_ALERTA = 0.85   # [V4 M03-10] ⚠️ quando os pares válidos ficam abaixo de 85% do máximo possível
ESTADOS_ATIVOS = ('READY', 'RUNNING', 'SUBMITTED', 'PENDING')   # [V4 M03-09] tarefas na fila (igual ao motor)
GERADO_EM = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')   # [V4 M03-05]

VARS = ['pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs']

poligonoBrasil = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_NAME', 'Brazil')).geometry()

crsNativo = 'EPSG:4326'
transformNativo = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]


def horas_da_faixa(L):
    """Horas de previsão do dia L (24(L-1), 24L] que existem no GFS atual."""
    return [h for h in range(24 * (L - 1) + 1, 24 * L + 1) if h <= 120 or h % 3 == 0]


def horas_chuva(L):
    """[V4 M03-03] Horas dos 4 blocos de 6 h do dia L (blocos que terminam às 06, 12, 18 e 24 UTC
    numa rodada 00Z). Chuva = soma dos 4 blocos; radiação = média dos 4 blocos."""
    h0 = 24 * (L - 1)
    return [h0 + 6, h0 + 12, h0 + 18, h0 + 24]


def inicio_dia_previsto(L):
    """[V4 M03-04] 1º dia previsto do prazo L: a rodada 00Z de D-(L-1) não pode ser anterior a
    INICIO_RODADAS, então D >= INICIO_RODADAS + (L-1) dias."""
    return (date.fromisoformat(INICIO_RODADAS) + timedelta(days=L - 1)).isoformat()


def maximos_por_mes():
    """[V4 M03-10] Máximo de pares dia x prazo por mês do calendário e por faixa, se todas as
    rodadas 00Z do período existissem completas: o prazo L conta os dias de
    inicio_dia_previsto(L) a FIM_DIAS. Testado em testes/teste_03.py."""
    fim = date.fromisoformat(FIM_DIAS)
    maximos = {mes: {fx: 0 for fx, _ in FAIXAS} for mes in range(1, 13)}
    for fx, prazos in FAIXAS:
        for L in prazos:
            d = date.fromisoformat(inicio_dia_previsto(L))
            while d <= fim:
                maximos[d.month][fx] += 1
                d += timedelta(days=1)
    return maximos


def abaixo_do_limiar(n, maximo):
    """[V4 M03-10] True quando a contagem fica abaixo de LIMIAR_ALERTA do máximo possível."""
    return maximo > 0 and n < LIMIAR_ALERTA * maximo


def decisao_mes(versao_existente, tarefa_ativa):
    """[V4 M03-05/M03-09] O que fazer com um mês. versao_existente: None se o asset não existe;
    '' se existe sem versao_matriz; senão o valor gravado.
    Devolve 'pular' (já gerado na V2.1), 'conflito' (asset de outra versão ou sem versão: o
    script para), 'tarefa_ativa' (tarefa na fila: pula) ou 'enviar'."""
    if versao_existente is not None:
        return 'pular' if versao_existente == VERSAO_MATRIZ else 'conflito'
    return 'tarefa_ativa' if tarefa_ativa else 'enviar'


# [V4 M03-03] Horas esperadas por prazo (1 a 15): 24 nos dias 1 a 5 (saída horária até 120 h)
# e 8 nos dias 6 a 15 (de 3 em 3 h). As mesmas do motor (contagem_esperada) numa rodada 00Z.
N_ESPERADO = {L: len(horas_da_faixa(L)) for _, prazos in FAIXAS for L in prazos}
print("Imagens esperadas por dia em cada faixa:", {fx: sorted({N_ESPERADO[L] for L in prazos}) for fx, prazos in FAIXAS})

BANDAS_DIA = [f'{v}__{fonte}_{fx}' for fx, _ in FAIXAS for fonte in ('sicsb', 'gfs') for v in VARS]
INICIO_RODADAS_MS = ee.Date(INICIO_RODADAS).millis()   # [V4 M03-04]
NOMES_MEDIA = [b.replace('__', '_m_') for b in BANDAS_DIA]
NOMES_DP = [b.replace('__', '_s_') for b in BANDAS_DIA]
NOMES_N = [f'n_{fx}' for fx, _ in FAIXAS]   # [V4 M03-06] pares válidos por pixel (Float32, valores inteiros)

# [V4 M03-06] Média, desvio (o mesmo ee.Reducer.stdDev da V2) e contagem numa só passada
REDUTOR = (ee.Reducer.mean()
           .combine(ee.Reducer.stdDev(), sharedInputs=True)
           .combine(ee.Reducer.count(), sharedInputs=True))

# [V4 M03-09] Cria a coleção só se ela não existir; um erro na criação para o script.
try:
    ee.data.getAsset(ASSET_DESTINO_MATRIZ_GFS)
except ee.EEException:
    ee.data.createAsset({'type': 'ImageCollection'}, ASSET_DESTINO_MATRIZ_GFS)
    print("✔️ Pasta de destino criada.")


def versoes_existentes():
    """[V4 M03-05] {nome: versao_matriz} das imagens já gravadas na coleção ('' sem versão)."""
    versoes = {}
    for a in ee.data.listAssets({'parent': ASSET_DESTINO_MATRIZ_GFS}).get('assets', []):
        caminho = a.get('id') or a.get('name')
        v = ee.Image(caminho).get('versao_matriz').getInfo()
        versoes[caminho.split('/')[-1]] = '' if v is None else str(v)
    return versoes


def descricoes_tarefas_ativas():
    """[V4 M03-09] Descrições das tarefas do usuário que ainda estão na fila ou rodando."""
    return {t.get('description', '') for t in ee.data.getTaskList() if t.get('state') in ESTADOS_ATIVOS}


# =========================================================================
# 2. FUNÇÕES DE PROCESSAMENTO
# =========================================================================
def extrair_sicsb(img):
    """BR-DWGD com escala e offset oficiais; -32768 tratado como ausência."""
    mask = img.select('pr').gt(-32768)
    return ee.Image.cat([
        img.select('pr').multiply(0.00686666).add(225.0).max(0),
        img.select('Tmax').multiply(0.00106815).add(15.0),
        img.select('Tmin').multiply(0.00106815).add(15.0),
        img.select('RH').multiply(0.39370079).add(-0.393701).clamp(0, 100),
        img.select('u2').multiply(0.05905512).add(-0.059055),
        img.select('Rs').multiply(0.15708661).add(-0.057087),
    ]).updateMask(mask).rename([f'{v}__sicsb' for v in VARS])


def preparar_br(img):
    """[V4 M03-08] BR-DWGD do dia convertido uma vez (a mesma imagem serve aos 15 prazos), com a
    mesma pegada nas 6 bandas: o pixel só entra se todas as variáveis existirem no dia.
    O system:time_start do BR-DWGD é 00:00 UTC em todos os dias (auditoria C2)."""
    br = extrair_sicsb(img)
    pegada = br.mask().reduce(ee.Reducer.min())
    return br.updateMask(pegada).set('system:time_start', img.get('system:time_start'))


def velocidade_u2(img):
    return img.select('u_component_of_wind_10m_above_ground') \
        .hypot(img.select('v_component_of_wind_10m_above_ground')) \
        .multiply(0.748).rename('u2')


def gfs_faixa(data_ms, L, fx):
    """Previsão do GFS para o dia data_ms feita L dias antes (rodada 00Z de D-(L-1)).
    Mesmas contas do motor: [V4 M03-14] Tmax/Tmin pela temperatura instantânea das saídas do dia
    (24 horárias nos dias 1 a 5; 8 de 3 em 3 h do dia 6 em diante), chuva e radiação pelos 4
    blocos de 6 h (horas múltiplas de 6), UR e vento pela média das saídas do dia.
    [V4 M03-04] Devolve também a data de criação da rodada (ms) para o corte do v16."""
    criacao = ee.Number(data_ms).subtract((L - 1) * 86400000)
    h0 = 24 * (L - 1)
    # [V4 M03-03] Completude contada na coleção sem o .map (só metadados); a reamostragem
    # bilinear continua sendo feita em cada imagem antes de compor.
    bruta = (ee.ImageCollection(COL_GFS)
             .filterDate(ee.Date(criacao), ee.Date(criacao).advance(1, 'hour'))
             .filter(ee.Filter.eq('creation_time', criacao))
             .filter(ee.Filter.gt('forecast_hours', h0))
             .filter(ee.Filter.lte('forecast_hours', h0 + 24)))
    chuva_bruta = bruta.filter(ee.Filter.inList('forecast_hours', horas_chuva(L)))
    completa = bruta.size().eq(N_ESPERADO[L]).And(chuva_bruta.size().eq(4))
    rodada = bruta.map(lambda i: i.resample('bilinear'))
    chuva = chuva_bruta.map(lambda i: i.resample('bilinear'))   # filtrada antes do .map

    # [V4 M03-11] Composições seguras para coleção vazia (rodada ausente): cada uma recebe uma
    # imagem totalmente mascarada com a banda certa, que não muda nada quando há saídas (pixel
    # mascarado não entra na soma, média, máximo ou mínimo) e garante 1 banda quando não há.
    # Assim o ramo não escolhido do ee.Algorithms.If em par_faixa nunca falha no rename.
    img = ee.Image.cat([
        composto_seguro(chuva, 'total_precipitation_surface', ee.Reducer.sum()).max(0),
        composto_seguro(rodada, 'temperature_2m_above_ground', ee.Reducer.max()),
        composto_seguro(rodada, 'temperature_2m_above_ground', ee.Reducer.min()),
        composto_seguro(rodada, 'relative_humidity_2m_above_ground', ee.Reducer.mean()).clamp(0, 100),
        composto_seguro(rodada.map(velocidade_u2), 'u2', ee.Reducer.mean()),
        composto_seguro(chuva, 'downward_shortwave_radiation_flux', ee.Reducer.mean())
        .multiply(0.0864).max(0),   # média dos 4 blocos de 6 h
    ]).rename([f'{v}__gfs_{fx}' for v in VARS])
    return img, completa, criacao   # [V4 M03-04]


def composto_seguro(col, banda, redutor):
    """[V4 M03-11] Composição de uma banda que não falha com a coleção vazia (ver gfs_faixa)."""
    vazia = ee.Image.constant(0).rename(banda).toFloat().updateMask(ee.Image.constant(0))
    return col.select(banda).map(lambda i: i.toFloat()).merge(ee.ImageCollection([vazia])) \
        .reduce(redutor).rename(banda)


def par_faixa(img_br, fx, L):
    """[V4 M03-03] Par do prazo L da faixa fx: dia D do BR-DWGD (já convertido por preparar_br)
    com a rodada 00Z de D-(L-1). Se a rodada estiver incompleta ou for anterior ao v16, as 12
    bandas ficam mascaradas juntas (o par sai inteiro da média) e 'valido' = 0."""
    data_ms = img_br.date().millis()
    img_gfs, completa, criacao = gfs_faixa(data_ms, L, fx)
    br = img_br.rename([f'{v}__sicsb_{fx}' for v in VARS])
    img_gfs = img_gfs.updateMask(br.select(f'pr__sicsb_{fx}').mask())   # [V4 M03-08] mesma pegada
    valido = completa.And(criacao.gte(INICIO_RODADAS_MS))               # [V4 M03-04] corte pela criação
    nomes = [f'{v}__sicsb_{fx}' for v in VARS] + [f'{v}__gfs_{fx}' for v in VARS]
    cheia = ee.Image.cat([br, img_gfs]).toFloat()
    vazia = (ee.Image.constant([0] * len(nomes)).rename(nomes).toFloat()
             .updateMask(ee.Image.constant(0)))
    return ee.Image(ee.Algorithms.If(valido, cheia, vazia)).set(
        {'system:time_start': data_ms, 'valido': valido, 'prazo': L})


def funcao_par(fx, L):
    """[V4 M03-03] Função do .map de um prazo (fixa fx e L)."""
    return lambda img_br: par_faixa(img_br, fx, L)


def pares_da_faixa(br_mes, fx, prazos):
    """[V4 M03-03] Todos os pares dia x prazo da faixa numa só coleção, com os mesmos nomes de
    banda. Cada prazo L usa os dias do mês a partir de inicio_dia_previsto(L)."""
    pares = None
    for L in prazos:
        col = br_mes.filterDate(inicio_dia_previsto(L), DATA_FIM).map(funcao_par(fx, L))
        pares = col if pares is None else pares.merge(col)
    return pares


def gerar_matriz_gfs_mes(mes):
    # [V4 M03-08] BR-DWGD do mês filtrado e convertido uma vez, reaproveitado pelos 15 prazos
    br_mes = (ee.ImageCollection(ASSET_SICSB_REAL)
              .filterDate(INICIO_RODADAS, DATA_FIM)
              .filter(ee.Filter.calendarRange(mes, mes, 'month'))
              .map(preparar_br))

    # [V4 M03-03/M03-06] Uma redução por faixa (o número de pares por dia difere entre as
    # faixas) com o redutor combinado; as faixas são concatenadas na ordem das bandas da V2.
    medias, dps, ns, n_pares = [], [], [], {}
    for fx, prazos in FAIXAS:
        pares = pares_da_faixa(br_mes, fx, prazos)
        red = pares.reduce(REDUTOR)
        bandas = [f'{v}__{fonte}_{fx}' for fonte in ('sicsb', 'gfs') for v in VARS]
        medias.append(red.select([f'{b}_mean' for b in bandas]))
        dps.append(red.select([f'{b}_stdDev' for b in bandas]))
        ns.append(red.select(f'Tmax__gfs_{fx}_count'))
        n_pares[fx] = pares.aggregate_sum('valido')   # [V4 M03-05] calculado no servidor

    media = ee.Image.cat(medias).rename(NOMES_MEDIA)
    dp = ee.Image.cat(dps).rename(NOMES_DP)
    n = ee.Image.cat(ns).rename(NOMES_N)
    # [V4 M03-06] mesma pegada das médias. Gravado como Float32 (valores inteiros), como as outras
    # 96 bandas: evita o risco de a exportação recusar tipos diferentes no mesmo asset.
    n = n.updateMask(n.gt(0)).toFloat()
    matriz = ee.Image.cat([ee.Image.cat([media, dp]).toFloat(), n])

    # [V4 M03-05] Propriedades do contrato V2.1 (n_pares_* são calculados dentro da tarefa)
    props = {
        'versao_matriz': VERSAO_MATRIZ,
        'modelo_gfs': MODELO_GFS,
        'inicio_rodadas': INICIO_RODADAS,
        'fim_dias': FIM_DIAS,
        'mes_referencia': mes,
        'metodo_pr': 'soma_blocos_6h',
        'metodo_rs': 'media_blocos_6h',
        'janela': '(00Z,24Z] UTC do dia previsto; rodada 00Z de D-(L-1)',
        'gerado_em': GERADO_EM,
        'periodo': f'rodadas 00Z de {INICIO_RODADAS} a {FIM_DIAS}; dias previstos até {FIM_DIAS}',
        'faixas': ';'.join(f'{fx}=' + ','.join(str(L) for L in prazos) for fx, prazos in FAIXAS),
    }
    props.update({f'leads_{fx}': ','.join(str(L) for L in prazos) for fx, prazos in FAIXAS})
    props.update({f'n_pares_{fx}': n_pares[fx] for fx, _ in FAIXAS})

    mascara_brasil = ee.Image.constant(1).clipToCollection(ee.FeatureCollection([ee.Feature(poligonoBrasil)])).mask()
    return matriz.updateMask(mascara_brasil).set(props), n_pares


# =========================================================================
# 3. DISPARADOR DAS 12 TAREFAS MENSAIS
# =========================================================================
# [V4 D1] Mensagem inicial com a versão e o período
print(f"\n🚀 Empacotando e exportando as 12 matrizes preditivas V2 (versão {VERSAO_MATRIZ}: só {MODELO_GFS}, "
      f"rodadas 00Z de {INICIO_RODADAS} a {FIM_DIAS})...")

# [V4 M03-05/M03-09] Plano dos 12 meses ANTES de enviar qualquer tarefa
versoes = versoes_existentes()
ativas = descricoes_tarefas_ativas()
plano = {mes: decisao_mes(versoes.get(f'Matriz_GFS_{mes:02d}'), f'GERAR_MATRIZ_GFS_V2_{mes:02d}' in ativas)
         for mes in range(1, 13)}

conflitos = [mes for mes in range(1, 13) if plano[mes] == 'conflito']
if conflitos:
    for mes in conflitos:
        v = versoes[f'Matriz_GFS_{mes:02d}']
        print(f"❌ {ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{mes:02d} já existe com "
              f"{'versao_matriz = ' + repr(v) if v else 'nenhuma versao_matriz'} (esta é a {VERSAO_MATRIZ}).")
    print("   O que fazer: apague À MÃO esses assets antigos (Code Editor, aba Assets, ou "
          "ee.data.deleteAsset('<caminho>') no Colab) e rode este script de novo.")
    print("   Nenhuma tarefa foi enviada.")
    raise RuntimeError(f"Matriz GFS de outra versão nos meses {[f'{m:02d}' for m in conflitos]}; "
                       "apague os assets antigos à mão e rode de novo.")

MAXIMOS = maximos_por_mes()   # [V4 M03-10]
enviadas = []

for mes in range(1, 13):
    str_mes = str(mes).zfill(2)
    nome_asset = f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{str_mes}'

    if plano[mes] == 'pular':   # [V4 M03-05/M03-09] pula só a V2.1 e as tarefas na fila
        print(f"⏩ Matriz do mês {str_mes} já existe na versão {VERSAO_MATRIZ}. Pulando.")
        continue
    if plano[mes] == 'tarefa_ativa':
        print(f"⏳ A tarefa GERAR_MATRIZ_GFS_V2_{str_mes} ainda está na fila (READY/RUNNING). Pulando o mês {str_mes}. "
              "Se ela for de uma versão anterior do 03, cancele-a na aba Tasks e rode este script de novo.")
        continue

    # [V4 M03-10] Contagem (a mesma expressão gravada em n_pares_*) contra o máximo possível
    img_mes, n_pares = gerar_matriz_gfs_mes(mes)
    maximo = MAXIMOS[mes]
    try:
        bruto = ee.Dictionary(n_pares).getInfo()
        contagem = {fx: int(bruto[fx]) for fx, _ in FAIXAS}
        print(f"   Mês {str_mes}: dias válidos por faixa {contagem}")
        print(f"      (pares dia x prazo; máximo possível {maximo}; "
              + ', '.join(f'{fx} {100.0 * contagem[fx] / maximo[fx]:.1f}%' for fx, _ in FAIXAS) + ")")
        for fx, _ in FAIXAS:
            if abaixo_do_limiar(contagem[fx], maximo[fx]):
                print(f"   ⚠️ Faixa {fx} do mês {str_mes}: {contagem[fx]} pares, abaixo de "
                      f"{LIMIAR_ALERTA:.0%} do máximo ({maximo[fx]}); confira o catálogo do GFS.")
    except Exception as e:
        print(f"   ⚠️ Contagem de pares válidos do mês {str_mes} não calculada no Colab ({e}); "
              "a exportação segue e grava n_pares_* no asset (confira no 04).")

    task = ee.batch.Export.image.toAsset(
        image=img_mes,
        description=f'GERAR_MATRIZ_GFS_V2_{str_mes}',
        assetId=nome_asset,
        region=poligonoBrasil.bounds(),   # [V4 M03-10] retângulo; a máscara do Brasil já está na imagem
        crs=crsNativo,
        crsTransform=transformNativo,
        maxPixels=1e13
    )
    try:
        task.start()
    except Exception as e:   # [V4 M03-09] o erro aparece; rodar de novo é seguro (meses enviados são pulados)
        print(f"❌ Falha ao enviar a tarefa do mês {str_mes}: {e}")
        raise
    enviadas.append(str_mes)   # [V4]
    print(f"✔️ Tarefa enviada: matriz GFS V2, mês {str_mes}.")
    time.sleep(2)

# [V4] Resumo do envio; o motor agora é a V1.5
print(f"\n🎉 Tarefas enviadas: {len(enviadas)} ({', '.join(enviadas) if enviadas else 'nenhuma'}). "
      "Acompanhe na aba Tasks; o motor V1.5 só deve rodar com as 12 concluídas (confira antes com o 04).")
