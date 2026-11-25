# >>> ARQUIVO PRONTO: matriz EQM em SIMULAÇÃO (não grava nada). Cole inteiro, sem editar nada. <<<
# =========================================================================================
# 09 - MATRIZ EQM DO MOTOR V1.6 (versão E1) - 04/11/2026, etapa 2
# [08/11/2026] Conta e matriz SEM mudança (a versão continua E1). A K21 v3a reprovou o EQM do VENTO (viés acima do
#   limite): o motor V1.6 usa da matriz só os quantis da UR e o maior dia de chuva; os quantis do vento ficam gravados,
#   sem uso, para estudo futuro. Motor uma vez por dia às 23h07: a única janela é 22h50-01h00.
# v3 (04/11, 18h50): a K21 v2 mostrou que o servidor não aguenta o percentil de décadas num pedido INTERATIVO (nem com
#   2 pontos). A exportação (09b) é em lote, com mais memória e blocos de 32 px, e continua calculando no servidor. Mas
#   a amostra de conferência agora lê os valores diários do mês de simulação de 1986 a 2025 (getRegion, um ano por
#   pedido) e calcula os quantis em Python; o 09b compara o gravado com eles, com tolerância (o percentil do Earth
#   Engine e o do NumPy diferem um pouco entre dois valores vizinhos).
# v2 (04/11, 18h40): a K21 v1 parou com "User memory limit exceeded" ao calcular percentis de décadas em pontos. Aqui:
#   a amostra pede o ERA5 e o BR-DWGD separados, com tileScale 16, e divide os pontos ao meio se o servidor recusar;
#   a exportação calcula a matriz em blocos de 32 x 32 pixels (shardSize = 32; o padrão é 256). Contas sem mudança.
#
# O QUE FAZ
#   Calcula, para cada pixel do SAB e cada mês, os quantis 0, 5, 10, ..., 100% da umidade relativa e do vento a 2 m
#   do ERA5-Land (preparados exatamente como o motor faz antes de calibrar) e do BR-DWGD, de 1986 a 2025, e o maior
#   dia de chuva do BR-DWGD no pixel e mês. O motor V1.6 usa os quantis da UR para corrigir os dias de 2026 em diante
#   pelo mapeamento empírico de quantis (EQM) e o maior dia para o teto da chuva (os do vento ficam sem uso: K21 v3a).
#   Grava (só o 09b) a coleção NOVA projects/clima-492922/assets/SICSB_EQM_1986_2025, com 12 imagens Matriz_EQM_01 a
#   Matriz_EQM_12, 85 bandas cada (RH_era_p000 ... RH_br_p100, u2_era_p000 ... u2_br_p100, pr_max_br). O banco SAB_V1
#   não é lido para gravar nem alterado.
#
#   Arquivos: 09a (SIMULAR = True) e 09b (SIMULAR = False) são o mesmo código; só mudam a linha 1 e o SIMULAR.
#
# COMO FUNCIONA
#   1. 09a: calcula a matriz de um mês (MES_SIMULACAO) só em PONTOS_SIMULACAO pixels A, em memória, e confere:
#      as 85 bandas; os quantis em ordem crescente; UR entre 0 e 100; vento entre 0 e 20 m/s; chuva máxima entre 0 e
#      800 mm. Nada é gravado (funções de escrita bloqueadas).
#   2. 09b: se a coleção já tiver os 12 meses da versão E1, não faz nada e só confere. Senão, cria a coleção, exporta
#      os meses que faltam (12 tarefas) e acompanha. Pode fechar o Colab: as tarefas seguem no Earth Engine; rode o
#      09b de novo depois para conferir (ele não exporta duas vezes).
#   3. Conferência do gravado: 12 meses, 85 bandas, propriedades, grade nativa, quantis em ordem e o mês de
#      simulação gravado igual ao calculado em memória nos mesmos pontos.
#
# COMO RODAR NO COLAB (fora da janela do motor: 22h50-01h00)
#   1. Colab -> Ambiente de execução -> Reiniciar sessão. Cole o 09a numa célula e rode. Tempo: 5 a 15 min.
#   2. Sem ❌: nova sessão, cole o 09b e rode. Exportação: de 30 min a 3 h (as 12 tarefas aparecem em
#      code.earthengine.google.com/tasks como SAB_EQM_01 ... SAB_EQM_12).
#   3. No fim, o Colab baixa matriz_eqm_<data>.zip com o log. Me envie.
# =========================================================================================

import os
import shutil
import time
import traceback
from datetime import datetime, timedelta, timezone

import pandas as pd

# =========================================================================
# 0. CONFIGURAÇÃO
# =========================================================================
PROJETO = 'clima-492922'
SIMULAR = True                    # True: calcula e confere sem gravar. False: exporta a coleção (uma vez só)

RAIZ = f'projects/{PROJETO}/assets'
ASSET_EQM = f'{RAIZ}/SICSB_EQM_1986_2025'
ASSET_MASCARA = f'{RAIZ}/SAB_MASCARA_QUALIDADE'
BR_DWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
VERSAO_MATRIZ_EQM = 'E1'
ANO_INI, ANO_FIM = 1986, 2025               # mesmo período da climatologia SICSB_1986_2025 que o motor já usa
NIVEIS_EQM = tuple(range(0, 101, 5))        # 21 quantis
VARS_EQM = ('RH', 'u2')
MES_SIMULACAO = 7                           # mês calculado em memória no 09a e conferido no 09b
PONTOS_SIMULACAO = 150
SEMENTE = 42
MAX_RAW = 2000                              # até 2.000 valores por pixel o percentil é exato (40 anos x 31 dias = 1.240)

CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
REGIAO_AMPLA_COORDS = [-75.0, -35.0, -28.0, 6.5]
TIMEOUT_TAREFAS_MIN = 240
INTERVALO_POLL_S = 60
LIMITES = {'RH': (0.0, 100.0), 'u2': (0.0, 20.0), 'pr_max_br': (0.0, 800.0)}

# =========================================================================
# 1. LOG E REGRAS PURAS (sem Earth Engine; testadas em testes/teste_09.py)
# =========================================================================
AGORA = datetime.now(timezone(timedelta(hours=-3)))
PASTA = (f'/content/matriz_eqm_{AGORA:%Y%m%d_%H%M%S}' if os.path.isdir('/content')
         else f'matriz_eqm_{AGORA:%Y%m%d_%H%M%S}')
os.makedirs(PASTA, exist_ok=True)
LOG = os.path.join(PASTA, 'LOG_09.txt')
open(LOG, 'w', encoding='utf-8').close()


def log(*partes):
    texto = ' '.join(str(p) for p in partes)
    print(texto)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(texto + '\n')


def parar(msg):
    log('❌ ' + msg)
    raise SystemExit(msg)


def bandas_eqm(var, fonte):
    """Nomes das bandas de quantis (iguais aos do motor V1.6): RH_era_p000 ... u2_br_p100."""
    return [f'{var}_{fonte}_p{p:03d}' for p in NIVEIS_EQM]


def bandas_matriz():
    return [b for v in VARS_EQM for f in ('era', 'br') for b in bandas_eqm(v, f)] + ['pr_max_br']


def nomes_percentil(var):
    """Nomes que o ee.Reducer.percentile dá às bandas (RH_p0, RH_p5, ...), na ordem de NIVEIS_EQM."""
    return [f'{var}_p{p}' for p in NIVEIS_EQM]


def conferir_amostra(linhas):
    """linhas: lista de dicionários (um por ponto) com as 85 bandas. Devolve a lista de problemas (vazia = ok):
    banda ausente, quantis fora de ordem, valores fora dos limites físicos."""
    problemas = []
    if not linhas:
        return ['nenhum ponto amostrado']
    faltam = [b for b in bandas_matriz() if b not in linhas[0]]
    if faltam:
        return [f'faltam {len(faltam)} bandas (ex.: {faltam[:3]})']
    fora_ordem, fora_limite, vazios = 0, {}, 0
    for r in linhas:
        for v in VARS_EQM:
            for f in ('era', 'br'):
                q = [r[b] for b in bandas_eqm(v, f)]
                if any(x is None for x in q):
                    vazios += 1
                    continue
                if any(b < a - 1e-6 for a, b in zip(q, q[1:])):
                    fora_ordem += 1
                lo, hi = LIMITES[v]
                if q[0] < lo - 1e-6 or q[-1] > hi + 1e-6:
                    fora_limite[f'{v}_{f}'] = fora_limite.get(f'{v}_{f}', 0) + 1
        pm = r.get('pr_max_br')
        if pm is not None and not (LIMITES['pr_max_br'][0] <= pm <= LIMITES['pr_max_br'][1]):
            fora_limite['pr_max_br'] = fora_limite.get('pr_max_br', 0) + 1
    if fora_ordem:
        problemas.append(f'{fora_ordem} séries de quantis fora de ordem')
    for k, n in fora_limite.items():
        problemas.append(f'{n} pontos com {k} fora de {LIMITES[k.split("_")[0] if k != "pr_max_br" else k]}')
    if vazios > len(linhas) * len(VARS_EQM) * 2 * 0.05:
        problemas.append(f'{vazios} séries vazias em {len(linhas)} pontos (mais de 5%)')
    return problemas


TOL_GRAVADO = {'RH': 2.0, 'u2': 0.2, 'pr_max_br': 0.5}   # [v3] % de UR, m/s, mm


def comparar_gravado(calc, grav, tol=None):
    """calc (quantis do NumPy) e grav (asset): {pid: {banda: valor}}. Devolve (pontos comparados, valores diferentes
    além da tolerância da variável). [v3] Tolerância por variável (TOL_GRAVADO)."""
    n, dif = 0, 0
    for pid, a in calc.items():
        b = grav.get(pid)
        if not b:
            continue
        n += 1
        for k in bandas_matriz():
            x, y = a.get(k), b.get(k)
            if x is None and y is None:
                continue
            lim = TOL_GRAVADO['pr_max_br' if k == 'pr_max_br' else k.split('_')[0]] if tol is None else tol
            if x is None or y is None or abs(x - y) > lim:
                dif += 1
    return n, dif


def quantis_pontos(df):
    """[v3] df: pid, RH_era, u2_era, RH_br, u2_br, pr_br (dias do mês). Devolve {pid: {85 bandas}}, com os mesmos
    nomes da matriz. Pixel com menos de 60 dias válidos fica sem quantis (None)."""
    import numpy as np
    q = np.array(NIVEIS_EQM) / 100.0
    saida = {}
    for pid, g in df.groupby('pid'):
        r = {'pid': pid}
        for v in VARS_EQM:
            for f in ('era', 'br'):
                x = pd.to_numeric(g[f'{v}_{f}'], errors='coerce').dropna().values
                vals = np.quantile(x, q) if len(x) >= 60 else [None] * len(q)
                for b, val in zip(bandas_eqm(v, f), vals):
                    r[b] = None if val is None else float(val)
        pr = pd.to_numeric(g['pr_br'], errors='coerce').dropna()
        r['pr_max_br'] = float(pr.max()) if len(pr) else None
        saida[pid] = r
    return saida


def meses_faltando(existentes, versoes):
    """existentes: nomes das imagens na coleção; versoes: {nome: versao_matriz_eqm}. Meses (1-12) a exportar."""
    return [m for m in range(1, 13)
            if f'Matriz_EQM_{m:02d}' not in existentes or versoes.get(f'Matriz_EQM_{m:02d}') != VERSAO_MATRIZ_EQM]


# =========================================================================
# 2. EARTH ENGINE
# =========================================================================
log('=' * 100)
log(f'09 MATRIZ EQM {VERSAO_MATRIZ_EQM} | {AGORA:%Y-%m-%d %H:%M} (BRT) | '
    f'{"SIMULAÇÃO: nada é gravado" if SIMULAR else "GRAVAÇÃO"} | {ASSET_EQM}')
log('=' * 100)

import ee  # noqa: E402

try:
    ee.Initialize(project=PROJETO)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJETO)


def _escrita_bloqueada_na_sessao():
    _funcs = [getattr(ee.batch.Task, 'start', None)] + [getattr(ee.data, _n, None) for _n in (
        'createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'setAssetAcl', 'startProcessing', 'exportImage')]
    return any(getattr(_f, '__name__', '') in ('_bloqueado', '_bloq') for _f in _funcs)


MSG_SESSAO_TRAVADA = ('Esta sessão do Colab ainda tem a trava de somente leitura de um script rodado antes nela '
                      '(por exemplo, o 09a ou uma validação). Nada foi gravado. No menu do Colab, clique em '
                      '"Ambiente de execução" e depois em "Reiniciar sessão" (confirme), e rode este arquivo de novo.')

if not SIMULAR and _escrita_bloqueada_na_sessao():
    parar(MSG_SESSAO_TRAVADA)


def _bloqueado(*a, **k):
    raise RuntimeError('SIMULAÇÃO: escrita bloqueada (use o 09b para gravar)')


if SIMULAR:
    for _nome in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
                  'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable',
                  'startIngestion', 'cancelTask'):
        if hasattr(ee.data, _nome):
            setattr(ee.data, _nome, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 SIMULAR = True: criar, apagar, exportar e cancelar estão bloqueados.\n')

REGIAO_AMPLA = ee.Geometry.Rectangle(REGIAO_AMPLA_COORDS, None, False)
PROJ = ee.Projection(CRS, TRANSFORM)
TRANSITORIOS = ('Too many concurrent', 'Internal error', 'Service Unavailable', '503', '429',
                'deadline', 'Deadline', 'Connection', 'temporarily')


class Pesado(Exception):
    """O Earth Engine recusou o pedido por memória ou tempo."""


def gi(obj, rotulo='', tentativas=5):
    for t in range(tentativas):
        try:
            return obj.getInfo()
        except Exception as e:
            if any(k in str(e).lower() for k in ('memory', 'timed out', 'too many pixels')):
                raise Pesado(str(e))
            if t < tentativas - 1 and any(k in str(e) for k in TRANSITORIOS):
                log(f'   ↻ {rotulo}: erro transitório; nova tentativa em {15 * (t + 1)} s')
                time.sleep(15 * (t + 1))
                continue
            raise


# --- preparo dos dados: o MESMO do motor V1.6 (_componentes_era5 e processarDia_Definitivo), antes de calibrar
def era_prep(img):
    t2m = img.select('temperature_2m').subtract(273.15).resample('bilinear')
    tdew = img.select('dewpoint_temperature_2m').subtract(273.15).resample('bilinear')
    rh = t2m.expression('100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))',
                        {'T': t2m, 'Td': tdew}).rename('RH')
    u2 = img.select('u_component_of_wind_10m').hypot(img.select('v_component_of_wind_10m')) \
        .multiply(0.748).resample('bilinear').rename('u2')
    return ee.Image(ee.Image.cat([rh, u2]).copyProperties(img, ['system:time_start']))   # ee.Image: copyProperties devolve Element


def br_prep(img):
    valido = (img.select('pr').gt(-32768).And(img.select('Tmax').gt(-32768)).And(img.select('Tmin').gt(-32768)))
    rh = img.select('RH').updateMask(img.select('RH').gt(-32768)).multiply(0.39370079).add(-0.393701) \
        .clamp(0, 100).rename('RH')
    u2 = img.select('u2').updateMask(img.select('u2').gt(-32768)).multiply(0.05905512).add(-0.059055) \
        .max(0).rename('u2')
    pr = img.select('pr').multiply(0.00686666).add(225.0).max(0).rename('pr')
    return ee.Image(ee.Image.cat([rh, u2, pr]).updateMask(valido).copyProperties(img, ['system:time_start']))


def do_mes(col, mes):
    return (ee.ImageCollection(col).filter(ee.Filter.calendarRange(ANO_INI, ANO_FIM, 'year'))
            .filter(ee.Filter.calendarRange(mes, mes, 'month')))


def matriz_mes(mes, parte=None):
    """As 85 bandas do mês (em memória). [v2] parte='era' só os quantis do ERA5; parte='br' os do BR-DWGD e o maior dia."""
    pct = ee.Reducer.percentile(list(NIVEIS_EQM), None, None, None, MAX_RAW)
    era = do_mes(ERA5, mes).map(era_prep)
    br = do_mes(BR_DWGD, mes).map(br_prep)
    q_era = era.select(list(VARS_EQM)).reduce(pct)
    q_br = br.select(list(VARS_EQM)).reduce(pct)
    partes = []
    for v in VARS_EQM:
        partes.append(q_era.select(nomes_percentil(v), bandas_eqm(v, 'era')))
        partes.append(q_br.select(nomes_percentil(v), bandas_eqm(v, 'br')))
    partes.append(br.select('pr').max().rename('pr_max_br'))
    if parte == 'era':
        return ee.Image.cat([q_era.select(nomes_percentil(v), bandas_eqm(v, 'era')) for v in VARS_EQM])
    if parte == 'br':
        return ee.Image.cat([q_br.select(nomes_percentil(v), bandas_eqm(v, 'br')) for v in VARS_EQM]
                            + [br.select('pr').max().rename('pr_max_br')])
    return ee.Image.cat(partes).toFloat().set({
        'versao_matriz_eqm': VERSAO_MATRIZ_EQM, 'mes': mes, 'anos': f'{ANO_INI}-{ANO_FIM}',
        'niveis': ','.join(str(p) for p in NIVEIS_EQM), 'fonte_modelo': ERA5, 'fonte_obs': 'BR-DWGD (Xavier et al. 2022)',
        'gerado_em': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'script': '09b'})


def pontos_a():
    classe = ee.Image(ASSET_MASCARA).select('classe')
    s = classe.stratifiedSample(numPoints=0, classBand='classe', region=REGIAO_AMPLA, projection=PROJ,
                                seed=SEMENTE, classValues=[1], classPoints=[PONTOS_SIMULACAO], geometries=True,
                                tileScale=4)
    feats = gi(s, 'sorteio dos pontos')['features']
    return [ee.Feature(ee.Geometry.Point(f['geometry']['coordinates']), {'pid': pid_de(*f['geometry']['coordinates'])})
            for f in feats]


def pid_de(lon, lat):
    """[v3] Identificador do pixel pela coluna e linha da grade nativa (igual no sorteio e no getRegion)."""
    return f'{int((lon - TRANSFORM[2]) // TRANSFORM[0])}_{int((TRANSFORM[5] - lat) // TRANSFORM[0])}'


def amostrar(img, pts, rotulo):
    """[v2] sampleRegions com tileScale 16; se o servidor recusar por memória, divide os pontos ao meio."""
    try:
        fc = gi(img.sampleRegions(collection=ee.FeatureCollection(pts), properties=['pid'], projection=PROJ,
                                  geometries=False, tileScale=16), rotulo)
        return {f['properties']['pid']: f['properties'] for f in fc['features']}
    except Pesado:
        if len(pts) <= 2:
            raise
        meio = len(pts) // 2
        log(f'   {rotulo}: pesado, dividindo os pontos ({len(pts)} -> {meio} + {len(pts) - meio})')
        saida = amostrar(img, pts[:meio], rotulo)
        saida.update(amostrar(img, pts[meio:], rotulo))
        return saida


def dias_mes(mes, pts):
    """[v3] Valores diários do mês (todos os anos de ANO_INI a ANO_FIM) nos pontos, um ano por pedido (getRegion), com
    o mesmo preparo do motor. Se o servidor recusar, divide os pontos ao meio."""
    coords = [f.geometry().coordinates() for f in pts]
    lista = gi(ee.List(coords), 'coordenadas')
    quadros = []

    def regiao(ano, cs):
        ini = ee.Date.fromYMD(ano, mes, 1)
        par = ee.Join.inner().apply(
            ee.ImageCollection(ERA5).filterDate(ini, ini.advance(1, 'month')).map(
                lambda i: era_prep(i).rename(['RH_era', 'u2_era'])),
            ee.ImageCollection(BR_DWGD).filterDate(ini, ini.advance(1, 'month')).map(
                lambda i: br_prep(i).rename(['RH_br', 'u2_br', 'pr_br'])),
            ee.Filter.maxDifference(difference=12 * 3600 * 1000, leftField='system:time_start',
                                    rightField='system:time_start'))
        junto = ee.ImageCollection(par.map(lambda f: ee.Image.cat([ee.Image(f.get('primary')),
                                                                   ee.Image(f.get('secondary'))])))
        try:
            return gi(junto.getRegion(ee.Geometry.MultiPoint(cs), None, CRS, TRANSFORM), f'dias {ano}-{mes:02d}')
        except Pesado:
            if len(cs) <= 10:
                raise
            meio = len(cs) // 2
            log(f'   dias {ano}-{mes:02d}: pesado, dividindo os pontos ({len(cs)} -> {meio} + {len(cs) - meio})')
            a, b = regiao(ano, cs[:meio]), regiao(ano, cs[meio:])
            return a + b[1:]

    for ano in range(ANO_INI, ANO_FIM + 1):
        reg = regiao(ano, lista)
        df = pd.DataFrame(reg[1:], columns=reg[0])
        df['pid'] = [pid_de(float(x), float(y)) for x, y in zip(df['longitude'], df['latitude'])]
        quadros.append(df)
        if ano % 10 == 5:
            log(f'   {ano}: {len(df)} pixel-dias')
    return pd.concat(quadros, ignore_index=True)


def amostrar_mes(mes, pts):
    """[v2] A matriz do mês nos pontos, pedindo o ERA5 e o BR-DWGD separados."""
    saida = {}
    for parte, nome in (('era', 'ERA5'), ('br', 'BR-DWGD')):
        for pid, props in amostrar(matriz_mes(mes, parte), pts, f'matriz do mês {mes:02d} ({nome})').items():
            saida.setdefault(pid, {}).update(props)
    return saida


def aguardar(tarefas):
    """tarefas: {descrição: task}. Espera todas terminarem; devolve {descrição: estado}."""
    t0, estados = time.time(), {}
    try:
        while True:
            mudou = False
            for d, t in tarefas.items():
                st = t.status().get('state')
                if st != estados.get(d):
                    estados[d] = st
                    mudou = True
            if mudou:
                cont = pd.Series(estados).value_counts().to_dict()
                log(f'   {datetime.now(timezone(timedelta(hours=-3))):%H:%M} tarefas: {cont}')
            if all(s not in ('READY', 'RUNNING', 'SUBMITTED', 'PENDING', 'UNSUBMITTED') for s in estados.values()):
                return estados
            if time.time() - t0 > TIMEOUT_TAREFAS_MIN * 60:
                log(f'⏸️ Passou de {TIMEOUT_TAREFAS_MIN} min. As tarefas seguem no Earth Engine; rode o 09b de novo '
                    'depois para conferir (ele não exporta de novo).')
                return None
            time.sleep(INTERVALO_POLL_S)
    except KeyboardInterrupt:
        log('⏸️ Acompanhamento interrompido: as tarefas seguem. Rode o 09b de novo depois para conferir.')
        return None


def inventario():
    try:
        itens = ee.data.listAssets({'parent': ASSET_EQM}).get('assets', [])
    except Exception:
        return None, {}
    nomes = [a['name'].split('/')[-1] for a in itens]
    versoes = {}
    for a in itens:
        nome = a['name'].split('/')[-1]
        try:
            versoes[nome] = (ee.data.getAsset(a['name']).get('properties') or {}).get('versao_matriz_eqm')
        except Exception:
            versoes[nome] = None
    return nomes, versoes


# =========================================================================
# 3. EXECUÇÃO
# =========================================================================
def main():
    T0 = time.time()
    pts = pontos_a()
    log(f'1) Mês {MES_SIMULACAO:02d}, {ANO_INI}-{ANO_FIM}, em {PONTOS_SIMULACAO} pixels A: valores diários e quantis em '
        f'Python ({ANO_FIM - ANO_INI + 1} pedidos, de 3 a 10 min)...')
    calc = quantis_pontos(dias_mes(MES_SIMULACAO, pts))           # [v3] sem percentil no servidor
    problemas = conferir_amostra(list(calc.values()))
    tab = pd.DataFrame(list(calc.values()))
    resumo = pd.DataFrame({v: {'ERA5 p05': tab[f'{v}_era_p005'].mean(), 'ERA5 p50': tab[f'{v}_era_p050'].mean(),
                               'ERA5 p95': tab[f'{v}_era_p095'].mean(), 'BR p05': tab[f'{v}_br_p005'].mean(),
                               'BR p50': tab[f'{v}_br_p050'].mean(), 'BR p95': tab[f'{v}_br_p095'].mean()}
                           for v in VARS_EQM}).round(2)
    log(f'   {len(calc)} pontos | médias dos quantis (UR em %, vento em m/s):\n{resumo.to_string()}')
    log(f'   maior dia de chuva do BR-DWGD (média dos pontos): {tab["pr_max_br"].mean():.1f} mm '
        f'(máx. {tab["pr_max_br"].max():.1f} mm)')
    tab.to_csv(os.path.join(PASTA, f'amostra_mes_{MES_SIMULACAO:02d}.csv'), sep=';', decimal=',', index=False)
    if problemas:
        parar('Amostra com problemas: ' + '; '.join(problemas))
    log('✅ Amostra conferida: 85 bandas, quantis em ordem, valores dentro dos limites físicos.')

    nomes, versoes = inventario()
    faltam = meses_faltando(nomes or [], versoes)
    log(f'\n2) Coleção {ASSET_EQM}: ' + ('não existe' if nomes is None else
                                        f'{len(nomes)} imagem(ns); faltam os meses {faltam or "nenhum"}'))
    if SIMULAR:
        log(f'\nℹ️ SIMULAR = True: nada foi gravado ({(time.time() - T0) / 60:.0f} min). Sem ❌: rode o 09b.')
        return

    if faltam:
        if nomes is None:
            ee.data.createAsset({'type': 'IMAGE_COLLECTION'}, ASSET_EQM)
            log(f'   coleção criada: {ASSET_EQM}')
        tarefas = {}
        for m in faltam:
            nome = f'Matriz_EQM_{m:02d}'
            if nomes and nome in nomes:
                ee.data.deleteAsset(f'{ASSET_EQM}/{nome}')          # sobra de versão antiga
                log(f'   apagada a versão antiga de {nome}')
            t = ee.batch.Export.image.toAsset(image=matriz_mes(m), description=f'SAB_EQM_{m:02d}',
                                              assetId=f'{ASSET_EQM}/{nome}', region=REGIAO_AMPLA, crs=CRS,
                                              crsTransform=TRANSFORM, maxPixels=1e10, shardSize=32)
            t.start()
            tarefas[f'SAB_EQM_{m:02d}'] = t
        log(f'🚀 {len(tarefas)} exportações iniciadas (code.earthengine.google.com/tasks). Acompanhando a cada '
            f'{INTERVALO_POLL_S} s, até {TIMEOUT_TAREFAS_MIN} min...')
        estados = aguardar(tarefas)
        if estados is None:
            return
        falhas = {d: s for d, s in estados.items() if s != 'COMPLETED'}
        if falhas:
            parar(f'Exportações sem sucesso: {falhas}. Rode o 09b de novo: ele refaz só os meses que faltam.')

    log('\n3) Conferência do gravado')
    nomes, versoes = inventario()
    faltam = meses_faltando(nomes or [], versoes)
    if faltam:
        parar(f'A coleção ainda não tem os meses {faltam} da versão {VERSAO_MATRIZ_EQM}.')
    info = gi(ee.List([ee.List([ee.Image(f'{ASSET_EQM}/Matriz_EQM_{m:02d}').bandNames(),
                                ee.Image(f'{ASSET_EQM}/Matriz_EQM_{m:02d}').projection()]) for m in range(1, 13)]),
              'bandas e projeção dos 12 meses')
    prob = []
    for m, (bandas, proj) in zip(range(1, 13), info):
        if sorted(bandas) != sorted(bandas_matriz()):
            prob.append(f'mês {m:02d} com {len(bandas)} bandas')
        if proj.get('crs') != CRS:
            prob.append(f'mês {m:02d} com crs {proj.get("crs")}')
    grav = amostrar(ee.Image(f'{ASSET_EQM}/Matriz_EQM_{MES_SIMULACAO:02d}'), pts, 'gravado do mês de simulação')
    n, dif = comparar_gravado(calc, grav)
    log(f'   mês {MES_SIMULACAO:02d}: {n} pontos comparados, {dif} de {n * 85} valores fora da tolerância {TOL_GRAVADO} '
        f'em relação aos quantis do NumPy')
    if n == 0 or dif > n * 85 * 0.05:
        prob.append(f'{dif} valores do mês {MES_SIMULACAO:02d} longe dos quantis calculados dos dias (mais de 5%)')
    prob += [f'gravado: {p}' for p in conferir_amostra(list(grav.values()))]
    if prob:
        parar('Matriz gravada não confere: ' + '; '.join(prob))
    log(f'✅ {ASSET_EQM}: 12 meses da versão {VERSAO_MATRIZ_EQM}, 85 bandas, grade nativa, quantis em ordem e o mês '
        f'{MES_SIMULACAO:02d} igual ao calculado. Próximo passo: o 05a V1.6 (simulação do motor).')


try:
    main()
except SystemExit:
    pass
except Exception:
    log(traceback.format_exc())
    raise
finally:
    z = shutil.make_archive(PASTA, 'zip', PASTA)
    log(f'📦 {z}  <- me envie este zip')
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        log('   (baixe pelo painel Arquivos do Colab)')
