# >>> ARQUIVO PRONTO: máscara de qualidade em SIMULAÇÃO (não grava nada). Cole inteiro, sem editar nada. <<<
# =========================================================================================
# 01 - MÁSCARA DE QUALIDADE DOS PIXELS DO SAB (versão Q1) - 20/10/2026
#
# MUDANÇAS V4 (20/10/2026)
#   [V4 Q1] Script novo do pacote SAB v4. Grava projects/clima-492922/assets/SAB_MASCARA_QUALIDADE,
#           lida pelo painel 2026.10.4 (06), pelas normais (07) e pela auditoria 08 (seção Q1).
#   [V4 revisão B-01] A conferência da grade gravada aceita a origem própria do asset (deslocada por um
#           número inteiro de pixels); antes, uma gravação correta terminaria com ❌.
#   [V4 revisão B-04] A comparação com a J1 refaz a receita da J1 (soma padrão nos limites dos estados);
#           a classe 4 perto de ~880 vira só informação (o ~880 vem de soma ponderada por área).
#   Arquivos: 01a (SIMULAR = True) e 01b (SIMULAR = False) são o mesmo código; só mudam a linha 1 e o SIMULAR.
#
# MUDANÇAS V4.1 (20/10/2026), depois das auditorias K e K1d corrigida
#   [V4.1 K1a] A classe B é a UNIÃO dos pixels "BR-DWGD existe e o SAB difere" em 5 dias (DIAS_CLASSES).
#           A K1a mostrou que, em 17 de 65 datas de julho, até 7,5 pixels B ficam iguais ao BR-DWGD por
#           coincidência (dia sem chuva e ETo baixa nas lagoas do RS). Com um dia só, a conferência daria ❌
#           falso, e o dia de referência podia classificar um pixel B como A.
#           A conferência entre os dias passa a exigir só a ESTRUTURA (A+B, C e D iguais pixel a pixel); as
#           coincidências viram ℹ️.
#   [V4.1 K1d] Referências da K1d corrigida (pixels com o centro no Brasil): A 70.524, B 241, C 48. A classe 3
#           deve sair perto de 48 e a classe 4 perto de 1.060 (só informação; o antigo ~880 era estimativa).
#           A propriedade nova 'dias_classes' registra os dias usados.
#   [V4.1 revisão] Depois da revisão independente da v4.1: o 01b para se o asset existente não tiver
#           'dias_classes' (gravado antes da v4.1); o log mostra em quantos dias cada pixel da união esteve
#           em B (ℹ️ se algum esteve em só 1 ou 2) e o B da receita J1 só no dia de referência x na união.
#
# OBJETIVO
#   Classificar cada pixel do SAB pela origem do dado no histórico (auditoria J, item J1):
#     1 = A: SAB igual ao BR-DWGD (ETo e chuva com diferença de até 0,01)
#     2 = B: o BR-DWGD existe, mas o SAB difere (ERA5-Land mascarado; lagoas e estuários)
#     3 = C dentro: sem BR-DWGD, com o centro do pixel no Brasil
#     4 = C fora: sem BR-DWGD, com o centro do pixel fora do Brasil (borda)
#   Fora do SAB a banda fica mascarada. A trava do histórico NÃO é aberta: a máscara vale na leitura.
#
# COMO FUNCIONA
#   1. Classes em 5 dias (DIAS_CLASSES), com a mesma lógica da J1. A, C e D vêm do dia de referência
#      2001-01-15; B é a união dos 5 dias ([V4.1 K1a]).
#   2. Confere que a estrutura (A+B, C e D) é idêntica pixel a pixel nos 5 dias; senão, para com ❌.
#      Pixels B iguais ao BR-DWGD num dia (coincidência) só aparecem com ℹ️.
#   3. Separa C em 3 e 4 pelo centro do pixel. O centro de cada pixel C é testado como PONTO contra o
#      polígono do Brasil (GAUL level0); a imagem rasterizada só é aceita se concordar com esse teste em
#      TODOS os pixels C (ver centro_no_brasil). A regra de rasterização do Earth Engine (centro do pixel
#      ou qualquer interseção) fica A CONFIRMAR: o log mostra qual método passou.
#   4. Refaz a contagem com a receita da J1 e compara (A 70.364, B 204, C 1.109). As classes 3 e 4 são
#      comparadas com a K1d (perto de 48 e de 1.060), só como informação.
#   5. Com SIMULAR = False: exporta (uint8, banda 'classe', grade nativa do BR-DWGD), espera a tarefa e
#      confere o asset gravado. Se o asset já existir com versao_mascara = 'Q1', não faz nada.
#
# COMO RODAR NO COLAB
#   1. Cole o 01a inteiro numa célula e rode como está (SIMULAR = True). Nada é gravado: as funções de
#      escrita do Earth Engine ficam bloqueadas. Tempo típico: 2 a 5 minutos.
#   2. Sem ❌ e sem ⚠️, cole o 01b (SIMULAR = False) numa célula nova e rode: grava uma vez só (mais 5 a 15 min).
#   3. Depois de gravar, se o App estiver publicado, compartilhe o asset para leitura como o SAB_V1.
#   4. No fim, o Colab baixa mascara_qualidade_<data>.zip com o log e as tabelas.
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
SIMULAR = True                     # True: calcula e confere tudo sem gravar. False: exporta o asset (uma vez só)

RAIZ = f'projects/{PROJETO}/assets'
SAB = f'{RAIZ}/SAB_V1'
ASSET_MASCARA = f'{RAIZ}/SAB_MASCARA_QUALIDADE'
BR_DWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
VERSAO_MASCARA = 'Q1'
DIA_REFERENCIA = '2001-01-15'
# [V4.1 K1a] Dias cuja união define a classe B (o 1º é o de referência). Inclui dias de inverno, quando as
# coincidências da K1a acontecem; um pixel B só escaparia se coincidisse nos 5 dias.
DIAS_CLASSES = ('2001-01-15', '1961-01-15', '1981-07-01', '2017-07-15', '2025-01-15')

CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
# Retângulo folgado em volta do Brasil (ilhas oceânicas incluídas). As contagens 'unweighted' incluem o pixel
# pelo centro; o retângulo envolvente exato do GAUL poderia deixar de fora pixels de borda com o centro além dele.
REGIAO_AMPLA_COORDS = [-75.0, -35.0, -28.0, 6.5]

# Referência: auditoria J de 20/10/2026 (J1, 7 dias de 1961 a 2025, classes iguais em todos)
J1_CONTAGENS = {'A': 70364, 'B': 204, 'C': 1109}
TOL_J1 = 0.01                      # ⚠️ se a contagem A, B ou C (receita da J1) diferir da J1 em mais de 1%
# [V4.1 K1d] K1d corrigida (20/10/2026 15:05): pixels com o centro no polígono do Brasil, em 2001-07-01
K1D_CENTRO_NO_BRASIL = {'A': 70524, 'B': 241, 'C': 48}
C_FORA_APROX = 1060                # C total (~1.106 a 1.109) menos os 48 com centro no Brasil
TOL_INFO_C = 0.25                  # ℹ️ se a classe 3 ou a 4 se afastar da referência mais que isso
# Ordem de tentativa da rasterização do "centro no Brasil"; vale a primeira que concordar com o teste vetorial
METODOS_CENTRO = ('paint', 'reduceToImage', 'pontos')
TIMEOUT_TAREFA_MIN = 60
INTERVALO_POLL_S = 20

# Escala e offset do BR-DWGD (os mesmos do motor e da auditoria J)
ESCALA_BR = {'pr': (0.00686666, 225.0, 'pr_mm'), 'ET': (0.05118110, -0.0511811, 'et_potencial')}
BANDAS_SAB = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2', 'tsolo_C', 'tfolha_C',
              'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm', 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
NOMES_ANTIGOS = ['precipitation_mm', 'temp_max_C', 'temp_min_C', 'relative_humidity_pct', 'et_potential_mm',
                 'et_actual_mm', 'vpd_kpa', 'solar_radiation_mj_m2', 'wind_speed_m_s', 'soil_temperature_C',
                 'skin_temperature_C', 'transpiration_mm', 'surface_runoff_mm', 'subsurface_runoff_mm',
                 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
NOMES_CLASSE = {1: 'A (igual ao BR-DWGD)', 2: 'B (BR-DWGD descartado)', 3: 'C dentro (centro no Brasil)',
                4: 'C fora (centro fora do Brasil)'}

# =========================================================================
# 1. LOG E REGRAS PURAS (sem Earth Engine; testadas em testes/teste_01.py)
# =========================================================================
AGORA = datetime.now(timezone(timedelta(hours=-3)))
PASTA = (f'/content/mascara_qualidade_{AGORA:%Y%m%d_%H%M%S}' if os.path.isdir('/content')
         else f'mascara_qualidade_{AGORA:%Y%m%d_%H%M%S}')
os.makedirs(PASTA, exist_ok=True)
LOG = os.path.join(PASTA, 'LOG_01.txt')
open(LOG, 'w', encoding='utf-8').close()          # log novo a cada execução (não acumula execuções)


def log(*partes):
    texto = ' '.join(str(p) for p in partes)
    print(texto)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(texto + '\n')


def tabela(df, titulo):
    log(f'\n   {titulo}')
    with pd.option_context('display.width', 250, 'display.max_columns', 40):
        for linha in df.to_string().splitlines():
            log('   ' + linha)


def parar(msg):
    log(f'\n❌ {msg}')
    raise RuntimeError(msg)


def comparar_j1(contagens):
    """Contagens por classe (dict 1..4) contra a J1: A = 1, B = 2, C = 3 + 4. Devolve uma linha por classe."""
    calc = {'A': contagens.get(1, 0), 'B': contagens.get(2, 0), 'C': contagens.get(3, 0) + contagens.get(4, 0)}
    linhas = []
    for k, ref in J1_CONTAGENS.items():
        dif = abs(calc[k] - ref) / ref
        linhas.append({'classe': k, 'calculado': calc[k], 'J1': ref, 'dif_rel_pct': round(100 * dif, 3),
                       'ok': dif <= TOL_J1})
    return linhas


def referencias_c(n3, n4):
    """[V4.1 K1d] Só informação: classe 3 perto de 48 e classe 4 perto de ~1.060. Devolve as frases ℹ️ (lista
    vazia se as duas estiverem dentro de TOL_INFO_C)."""
    msgs = []
    ref3 = K1D_CENTRO_NO_BRASIL['C']
    if abs(n3 - ref3) > TOL_INFO_C * ref3:
        msgs.append(f'classe 3 = {n3} (K1d: {ref3} pixels C com o centro no Brasil)')
    if abs(n4 - C_FORA_APROX) > TOL_INFO_C * C_FORA_APROX:
        msgs.append(f'classe 4 = {n4} (referência ~{C_FORA_APROX}: C total menos os {ref3} com centro no Brasil)')
    return msgs


def pixels_b_raros(hist, max_dias=2):
    """[V4.1 revisão V41-06] hist: {número de dias em B: pixels} da união B. Devolve quantos pixels estiveram em B
    em no máximo max_dias dias (esperado 0: a coincidência da K1a tira B de um dia, não acrescenta)."""
    return int(sum(n for k, n in hist.items() if 0 < int(float(k)) <= max_dias))


def resumo_conferencia(linhas):
    """[V4.1 K1a] linhas: dicts com 'dia', 'estrutura_diferente' (pixels em que A+B, C ou D mudam em relação ao
    dia de referência) e 'B_iguais_no_dia' (pixels da união B que estão iguais ao BR-DWGD nesse dia).
    Devolve (estrutura_ok, total_de_coincidências)."""
    ok = all(int(x['estrutura_diferente']) == 0 for x in linhas)
    return ok, int(sum(int(x['B_iguais_no_dia']) for x in linhas))


def grade_nativa(t, tol=1e-6):
    """[V4 revisão B-01] Mesma grade do BR-DWGD: escala igual e origem deslocada por um número inteiro de pixels.
    O asset exportado guarda a origem da própria região de exportação (alinhada à grade), não a do BR-DWGD."""
    t = list(t or [])
    if len(t) != 6 or any(abs(t[i] - TRANSFORM[i]) > 1e-12 for i in (0, 1, 3, 4)):
        return False
    fx = (t[2] - TRANSFORM[2]) / TRANSFORM[0]
    fy = (t[5] - TRANSFORM[5]) / TRANSFORM[4]
    return abs(fx - round(fx)) < tol and abs(fy - round(fy)) < tol


def contar_discordancias(n_pontos, dentro, valores):
    """Pixels C cujo valor rasterizado (1 = centro no Brasil) difere do teste vetorial do centro.
    dentro: índices dos centros dentro do polígono; valores: {índice: valor rasterizado}.
    Ponto sem valor conta como discordância."""
    n = 0
    for i in range(n_pontos):
        v = valores.get(i)
        if v is None or int(round(float(v))) != (1 if i in dentro else 0):
            n += 1
    return n


def escolher_metodo(discordancias):
    """Primeiro método (na ordem de tentativa) sem nenhuma discordância; None se nenhum serviu."""
    for metodo, n in discordancias.items():
        if n == 0:
            return metodo
    return None


# =========================================================================
# 2. CONEXÃO (E TRAVA DE ESCRITA NA SIMULAÇÃO)
# =========================================================================
import ee

log('=' * 100)
log(f'01 - MÁSCARA DE QUALIDADE DO SAB ({VERSAO_MASCARA}) | {AGORA:%Y-%m-%d %H:%M:%S} (BRT) | '
    f'{"SIMULAÇÃO: nada é gravado" if SIMULAR else "GRAVAÇÃO"}')
log(f'Saídas em: {PASTA}')
log('=' * 100)
try:
    ee.Initialize(project=PROJETO)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJETO)
log(f'Earth Engine conectado ao projeto {PROJETO} (biblioteca ee {ee.__version__})')

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

if not SIMULAR and _escrita_bloqueada_na_sessao():
    parar(MSG_SESSAO_TRAVADA)


def _bloqueado(*a, **k):
    raise RuntimeError('SIMULAÇÃO: escrita bloqueada (use o 01b para gravar)')


if SIMULAR:
    for _nome in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
                  'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable',
                  'startIngestion', 'cancelTask'):
        if hasattr(ee.data, _nome):
            setattr(ee.data, _nome, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 SIMULAR = True: criar, apagar, exportar e cancelar estão bloqueados.\n')

GAUL0_BR = ee.FeatureCollection('FAO/GAUL/2015/level0').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
GEOM_BR = GAUL0_BR.geometry()
UF_BR = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
REGIAO_AMPLA = ee.Geometry.Rectangle(REGIAO_AMPLA_COORDS, None, False)

TRANSITORIOS = ('Too many concurrent', 'Internal error', 'Service Unavailable', '503', '429',
                'deadline', 'Deadline', 'Connection', 'temporarily')


def gi(obj, rotulo='', tentativas=4):
    """getInfo com novas tentativas para erros transitórios do servidor."""
    for t in range(tentativas):
        try:
            return obj.getInfo()
        except Exception as e:
            if t < tentativas - 1 and any(k in str(e) for k in TRANSITORIOS):
                log(f'   ↻ {rotulo}: erro transitório; nova tentativa em {10 * (t + 1)} s')
                time.sleep(10 * (t + 1))
                continue
            raise


def rr(img, reducer, rotulo, geom=None):
    """reduceRegion na grade nativa, na região ampla."""
    return gi(img.reduceRegion(reducer=reducer, geometry=geom or REGIAO_AMPLA, crs=CRS, crsTransform=TRANSFORM,
                               maxPixels=1e10, tileScale=4), rotulo)


def dia(col, d):
    return ee.Image(ee.ImageCollection(col).filterDate(d, ee.Date(d).advance(1, 'day')).first())


def padronizar(img):
    return ee.Image(ee.Algorithms.If(img.bandNames().contains('precipitation_mm'),
                                     img.select(NOMES_ANTIGOS, BANDAS_SAB), img.select(BANDAS_SAB)))


def br_fis(img):
    b = [img.select(k).multiply(e).add(o).rename(n) for k, (e, o, n) in ESCALA_BR.items()]
    out = ee.Image.cat(b)
    return out.addBands(out.select('pr_mm').max(0), None, True)


def classes_pixel(d, completo=True):
    """Classes do dia d com a lógica da J1. Com completo=True (padrão da máscara), a ausência do BR-DWGD fora da
    área coberta pela imagem dele também conta como 'sem BR-DWGD' (unmask(0)), para que todo pixel do SAB receba
    uma classe; com completo=False a conta é exatamente a da J1 (o log mostra a diferença, esperada 0 ou poucos)."""
    sab = padronizar(dia(SAB, d))
    br = br_fis(dia(BR_DWGD, d))
    sab_ok = sab.select('et_potencial').mask().gt(0)
    br_ok = br.select('et_potencial').mask().gt(0)
    if completo:
        br_ok = br_ok.unmask(0)
    igual = (sab.select('et_potencial').subtract(br.select('et_potencial')).abs().lte(0.01)
             .And(sab.select('pr_mm').subtract(br.select('pr_mm')).abs().lte(0.01))).unmask(0)
    return {'A': sab_ok.And(br_ok).And(igual), 'B': sab_ok.And(br_ok).And(igual.Not()),
            'C': sab_ok.And(br_ok.Not()), 'D': sab_ok.Not().And(br_ok)}


def codigo_abc(cl):
    """0 = sem SAB; 1 = A; 2 = B; 3 = C (dentro ou fora do Brasil)."""
    return ee.Image(0).where(cl['A'], 1).where(cl['B'], 2).where(cl['C'], 3).rename('abc')


def estrutura(cl):
    """[V4.1 K1a] O que não muda de um dia para outro: 0 = sem SAB nem BR-DWGD; 1 = SAB com BR-DWGD (A ou B);
    3 = C (SAB sem BR-DWGD); 5 = D (BR-DWGD sem SAB)."""
    return (ee.Image(0).where(cl['A'].Or(cl['B']), 1).where(cl['C'], 3).where(cl['D'], 5)
            .rename('estrutura'))


def uniao_b(cls):
    """[V4.1 K1a] União dos pixels B dos dias de cls ({dia: classes})."""
    imgs = [cl['B'] for cl in cls.values()]
    u = imgs[0]
    for i in imgs[1:]:
        u = u.Or(i)
    return u.rename('B_uniao')


def classes_estaveis(ref, b_u):
    """[V4.1 K1a] Classes da máscara: A+B, C e D do dia de referência; B = a união b_u (dentro de A+B)."""
    ab = ref['A'].Or(ref['B'])
    return {'A': ab.And(b_u.Not()), 'B': ab.And(b_u), 'C': ref['C'], 'D': ref['D']}


def contar_classes(classe, rotulo):
    ind = ee.Image.cat([classe.eq(k).rename(f'n_classe_{k}') for k in (1, 2, 3, 4)])
    r = rr(ind, ee.Reducer.sum().unweighted(), rotulo)
    return {k: int(round(r.get(f'n_classe_{k}') or 0)) for k in (1, 2, 3, 4)}


def rasterizar_centro(metodo, pts, dentro):
    """Imagem 0/1 na grade nativa: 1 = centro do pixel no Brasil.
    A CONFIRMAR qual regra o Earth Engine usa em paint/reduceToImage (centro do pixel ou qualquer interseção);
    por isso cada método só é aceito depois de concordar com o teste vetorial em todos os pixels C.
    'pontos' rasteriza os próprios centros dos pixels C que caíram dentro do polígono (um ponto no centro
    exato do pixel só toca aquele pixel)."""
    if metodo == 'paint':
        img = ee.Image(0).paint(GAUL0_BR, 1)
    elif metodo == 'reduceToImage':
        img = GAUL0_BR.map(lambda f: f.set('um', 1)).reduceToImage(['um'], ee.Reducer.first()).unmask(0)
    else:
        img = (pts.filter(ee.Filter.inList('i', sorted(dentro))).map(lambda f: f.set('um', 1))
               .reduceToImage(['um'], ee.Reducer.first()).unmask(0))
    return img.rename('centro_br').reproject(crs=CRS, crsTransform=TRANSFORM)


def valores_nos_pontos(img, pts, rotulo):
    fc = gi(img.reduceRegions(collection=pts, reducer=ee.Reducer.first(), crs=CRS, crsTransform=TRANSFORM,
                              tileScale=4).select(['i', 'first'], None, False), rotulo)
    return {int(f['properties']['i']): f['properties'].get('first') for f in fc['features']}


def centro_no_brasil(abc):
    """Separa a classe C pelo centro do pixel. Devolve (imagem 0/1, método, tabela dos centros C)."""
    cent = rr(ee.Image.pixelLonLat().updateMask(abc.eq(3)), ee.Reducer.toList(), 'centros dos pixels C')
    lons, lats = cent.get('longitude') or [], cent.get('latitude') or []
    if not lons or len(lons) != len(lats):
        parar(f'Centros dos pixels C não lidos ({len(lons)} longitudes, {len(lats)} latitudes).')
    log(f'   {len(lons)} pixels C; centro de cada um testado como ponto contra o polígono GAUL level0 do Brasil')
    pts = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([float(lo), float(la)]), {'i': i})
                                for i, (lo, la) in enumerate(zip(lons, lats))])
    dentro = {int(x) for x in gi(pts.filterBounds(GEOM_BR).aggregate_array('i'), 'centros dentro do Brasil')}
    log(f'   teste vetorial: {len(dentro)} centros dentro do Brasil, {len(lons) - len(dentro)} fora')
    discord, valores = {}, {}
    for metodo in METODOS_CENTRO:
        try:
            img = rasterizar_centro(metodo, pts, dentro)
            valores[metodo] = valores_nos_pontos(img, pts, f'rasterização {metodo}')
            discord[metodo] = contar_discordancias(len(lons), dentro, valores[metodo])
        except Exception as e:
            log(f'   rasterização {metodo}: falhou ({type(e).__name__}: {str(e)[:150]})')
            continue
        log(f'   rasterização {metodo}: {discord[metodo]} pixel(s) C em desacordo com o teste vetorial')
        if discord[metodo] == 0:
            break
    metodo = escolher_metodo(discord)
    if metodo is None:
        parar(f'Nenhuma rasterização concordou com o teste vetorial do centro do pixel: {discord}.')
    log(f'   ✅ método aceito: {metodo} (concorda com o teste do centro em todos os {len(lons)} pixels C)')
    tab = pd.DataFrame({'longitude': lons, 'latitude': lats})
    tab['centro_no_brasil'] = [i in dentro for i in range(len(lons))]
    tab[f'raster_{metodo}'] = [valores[metodo].get(i) for i in range(len(lons))]
    return rasterizar_centro(metodo, pts, dentro), metodo, tab


def aguardar(task):
    t0 = time.time()
    estado = None
    try:
        while True:
            st = task.status()
            if st.get('state') != estado:
                estado = st.get('state')
                log(f'   {datetime.now(timezone(timedelta(hours=-3))):%H:%M:%S} tarefa: {estado}')
            if estado not in ('READY', 'RUNNING', 'SUBMITTED', 'PENDING', 'UNSUBMITTED'):
                return st
            if time.time() - t0 > TIMEOUT_TAREFA_MIN * 60:
                parar(f'A tarefa passou de {TIMEOUT_TAREFA_MIN} min (estado {estado}). Ela segue no Earth Engine; '
                      f'confira o asset depois com a auditoria 08 (seção Q1).')
            time.sleep(INTERVALO_POLL_S)
    except KeyboardInterrupt:
        log('⏸️ Acompanhamento interrompido: a tarefa segue no Earth Engine. Confira depois com a 08 (seção Q1).')
        return None


# =========================================================================
# 3. EXECUÇÃO
# =========================================================================
def main():
    # 3.1 Asset existente
    try:
        meta = ee.data.getAsset(ASSET_MASCARA)
    except Exception:
        meta = None
    if meta:
        props = meta.get('properties') or {}
        versao = props.get('versao_mascara')
        log(f'   asset já existe: versao_mascara = {versao!r}; propriedades {props}')
        if versao != VERSAO_MASCARA:
            parar(f'{ASSET_MASCARA} existe com versao_mascara = {versao!r} (esperado {VERSAO_MASCARA!r}). '
                  'Não sobrescrevo: confira o asset antes de decidir.')
        antigo = props.get('dias_classes') != ','.join(DIAS_CLASSES)          # [V4.1 revisão V41-04]
        if not SIMULAR:
            if antigo:
                parar(f'{ASSET_MASCARA} foi gravado antes da v4.1 (dias_classes = {props.get("dias_classes")!r}, '
                      f'esperado {",".join(DIAS_CLASSES)!r}). Rode o 01a: se ele mostrar pixels diferentes do '
                      'cálculo atual, apague o asset na aba Assets e rode o 01b de novo.')
            log(f'✅ {ASSET_MASCARA} já existe com versao_mascara = {VERSAO_MASCARA}: nada a fazer.')
            return
        if antigo:
            log('ℹ️ o asset gravado é anterior à v4.1 (sem dias_classes); compare os pixels diferentes no fim.')
        log('   (simulação: recalculo e comparo com o asset gravado no fim)')

    # 3.2 [V4.1 K1a] Classes em DIAS_CLASSES: estrutura igual em todos; B = união dos dias
    log(f'\n⏳ Classes em {len(DIAS_CLASSES)} dias ({", ".join(DIAS_CLASSES)}); referência {DIA_REFERENCIA}...')
    cls = {d: classes_pixel(d) for d in DIAS_CLASSES}
    ref = cls[DIA_REFERENCIA]
    b_u = uniao_b(cls)
    abc_ref = codigo_abc(classes_estaveis(ref, b_u))
    r = rr(ee.Image.cat([ref['C'].rename('C_mascara'),
                         classes_pixel(DIA_REFERENCIA, completo=False)['C'].rename('C_logica_J1')]),
           ee.Reducer.sum().unweighted(), 'C completo x C da J1')
    log(f'   pixels C: {int(round(r.get("C_mascara") or 0))} na máscara; {int(round(r.get("C_logica_J1") or 0))} pela '
        f'conta exata da J1 (a diferença são pixels do SAB fora da área coberta pela imagem do BR-DWGD)')
    est_ref = estrutura(ref)
    conf = []
    for d in DIAS_CLASSES:
        img = ee.Image.cat([estrutura(cls[d]).neq(est_ref).rename('estrutura_diferente'),
                            b_u.And(cls[d]['A']).rename('B_iguais_no_dia')])
        r = rr(img, ee.Reducer.sum().unweighted(), f'conferência {d}')
        conf.append({'dia': d, 'estrutura_diferente': int(round(r.get('estrutura_diferente') or 0)),
                     'B_iguais_no_dia': int(round(r.get('B_iguais_no_dia') or 0))})
        log(f'   {d}: {conf[-1]["estrutura_diferente"]} pixel(s) com estrutura (A+B, C, D) diferente da referência; '
            f'{conf[-1]["B_iguais_no_dia"]} pixel(s) B iguais ao BR-DWGD neste dia (coincidência)')
    pd.DataFrame(conf).to_csv(os.path.join(PASTA, 'Q1_conferencia_dias.csv'), sep=';', index=False)
    est_ok, n_coinc = resumo_conferencia(conf)
    if not est_ok:
        parar(f'A estrutura dos pixels (A+B, C, D) muda entre os dias conferidos: {conf}. A máscara única não vale; '
              'não exporto.')
    log(f'   ✅ estrutura (A+B, C e D) idêntica pixel a pixel nos {len(DIAS_CLASSES)} dias')
    # [V4.1 revisão V41-06] Em quantos dos 5 dias cada pixel da união B esteve em B. O normal é 5 (ou 4 com uma
    # coincidência de inverno); um pixel B em só 1 ou 2 dias seria um pixel A que diferiu do BR-DWGD num dia.
    # [Correção 20/10/2026, 23h] O frequencyHistogram devolvia a chave 'null' e a conversão para número parava o
    # script. [Correção 23h30] A 1ª versão da correção somava os dias com unmask(0), que mantém a pegada (footprint)
    # da imagem de cada dia: um pixel sem classe num dia (SAB ou BR-DWGD sem dado ali) contava como "não B", e o
    # histograma saía espalhado ({0: 19, 1: 20, 2: 46, ...}) mesmo com a conferência por dia limpa. Agora, para cada
    # dia, cada pixel da união é contado como B, A ou sem classe (unmask(0, False), sem pegada), e o histograma de
    # dias em B considera só os pixels com classe nos 5 dias. Os pixels com algum dia sem classe aparecem à parte.
    nd = len(DIAS_CLASSES)
    b_u1 = b_u.unmask(0, False).eq(1)
    bandas_d, n_b, n_a = [b_u1.rename('U')], None, None
    for i, d in enumerate(DIAS_CLASSES):
        b_d = cls[d]['B'].unmask(0, False).eq(1).And(b_u1)
        a_d = cls[d]['A'].unmask(0, False).eq(1).And(b_u1)
        bandas_d += [b_d.rename(f'B_{i}'), a_d.rename(f'A_{i}')]
        n_b = b_d if n_b is None else n_b.add(b_d)
        n_a = a_d if n_a is None else n_a.add(a_d)
    com_classe = n_b.add(n_a).eq(nd).And(b_u1)
    bandas_d += [n_b.eq(k).And(com_classe).rename(f'dias_{k}') for k in range(nd + 1)]
    bandas_d += [b_u1.And(com_classe.Not()).rename('algum_dia_sem_classe')]
    r_n = rr(ee.Image.cat(bandas_d), ee.Reducer.sum().unweighted(), 'dias em B por pixel da união')
    n_u = int(round(r_n.get('U') or 0))
    diag = []
    for i, d in enumerate(DIAS_CLASSES):
        nb, na = int(round(r_n.get(f'B_{i}') or 0)), int(round(r_n.get(f'A_{i}') or 0))
        diag.append({'dia': d, 'uniao_B': n_u, 'B': nb, 'A': na, 'sem_classe': n_u - nb - na})
        log(f'   {d}: dos {n_u} pixels da união B, {nb} em B, {na} em A, {n_u - nb - na} sem classe neste dia')
    pd.DataFrame(diag).to_csv(os.path.join(PASTA, 'Q1_uniao_B_por_dia.csv'), sep=';', index=False)
    hist = {k: int(round(r_n.get(f'dias_{k}') or 0)) for k in range(nd + 1)}
    hist = {k: n for k, n in hist.items() if n}
    n_sem = int(round(r_n.get('algum_dia_sem_classe') or 0))
    if n_sem:
        log(f'ℹ️ {n_sem} pixel(s) da união B sem classe em algum dos {nd} dias (SAB ou BR-DWGD sem dado no pixel '
            'naquele dia; ver a tabela por dia acima). Ficam fora do histograma abaixo; a classe deles vem do dia '
            f'de referência {DIA_REFERENCIA} e da união dos dias em que têm dado.')
    log(f'   pixels da união B com classe nos {nd} dias, por número de dias em B: {dict(sorted(hist.items()))}')
    poucos = pixels_b_raros(hist)
    if poucos:
        log(f'ℹ️ {poucos} pixel(s) B em só 1 ou 2 dos {len(DIAS_CLASSES)} dias: não é a coincidência da K1a '
            '(que tira B de um dia). Não impede a gravação, mas me envie a saída.')
    if n_coinc:
        log(f'ℹ️ {n_coinc} caso(s) de pixel B igual ao BR-DWGD num dos dias (coincidência de dia seco e ETo baixa, como '
            'na K1a); a união dos dias mantém esses pixels na classe B.')

    # 3.3 Centro do pixel no Brasil (separa C em 3 e 4)
    log('\n⏳ Separando C pelo centro do pixel...')
    centro_br, metodo, tab_c = centro_no_brasil(abc_ref)
    tab_c.to_csv(os.path.join(PASTA, 'Q1_centros_classe_C.csv'), sep=';', decimal=',', index=False)

    # 3.4 Imagem de classes e contagens
    classe = (abc_ref.where(abc_ref.eq(3).And(centro_br.eq(0)), 4)
              .updateMask(abc_ref.gt(0)).rename('classe').toUint8())
    cont = contar_classes(classe, 'contagem por classe')
    tab = pd.DataFrame([{'valor': k, 'classe': NOMES_CLASSE[k], 'pixels': n} for k, n in cont.items()]).set_index('valor')
    tabela(tab, f'Pixels por classe (unweighted, grade nativa; total {sum(cont.values())}):')
    tab.to_csv(os.path.join(PASTA, 'Q1_contagens.csv'), sep=';')
    # [V4 revisão B-04] A comparação com a J1 usa a mesma receita da J1 (completo=False, soma padrão nos limites
    # dos estados); as contagens da máscara (completo, região ampla, sem ponderar) podem diferir um pouco dela.
    avisos = []
    clj = {d: classes_pixel(d, completo=False) for d in DIAS_CLASSES}          # [V4.1 K1a] mesma união de dias
    cj = classes_estaveis(clj[DIA_REFERENCIA], uniao_b(clj))
    rj = rr(ee.Image.cat([cj[k].rename(k) for k in ('A', 'B', 'C')]
                         + [clj[DIA_REFERENCIA]['B'].rename('B_ref')]),          # [V4.1 revisão V41-10]
            ee.Reducer.sum(), 'contagem como na J1', geom=UF_BR.geometry().bounds())
    cont_j = {1: int(round(rj.get('A') or 0)), 2: int(round(rj.get('B') or 0)), 3: int(round(rj.get('C') or 0)), 4: 0}
    log(f'   B pela receita da J1: só {DIA_REFERENCIA} = {rj.get("B_ref")}; união dos {len(DIAS_CLASSES)} dias = '
        f'{rj.get("B")} (iguais, ou a união um pouco maior)')
    cmp_j1 = pd.DataFrame(comparar_j1(cont_j)).set_index('classe')
    tabela(cmp_j1, f'Receita da J1 refeita agora x J1 de 20/10/2026 (tolerância {100 * TOL_J1:.0f}%):')
    for k, lin in cmp_j1.iterrows():
        if not lin['ok']:
            avisos.append(f'classe {k}: {lin["calculado"]} x J1 {lin["J1"]} ({lin["dif_rel_pct"]}%)')
    log(f'   máscara (sem ponderar, região ampla): A {cont[1]}, B {cont[2]}, C {cont[3] + cont[4]} '
        f'(C dentro {cont[3]}, C fora {cont[4]}); receita J1: A {cont_j[1]}, B {cont_j[2]}, C {cont_j[3]}')
    for m in referencias_c(cont[3], cont[4]):                                  # [V4.1 K1d] só informação
        log(f'ℹ️ {m}. A separação 3/4 já foi validada pelo teste vetorial do centro.')
    for a in avisos:
        log(f'⚠️ {a}')
    if not avisos:
        log(f'✅ receita da J1 reproduzida dentro da tolerância; classe 3 = {cont[3]} (K1d: '
            f'{K1D_CENTRO_NO_BRASIL["C"]}); classe 4 = {cont[4]} (referência ~{C_FORA_APROX})')

    # 3.5 Resumo por estado (centro do pixel dentro do estado, como a J1, mas sem ponderar)
    ind = ee.Image.cat([classe.eq(k).rename(f'n_classe_{k}') for k in (1, 2, 3, 4)]).unmask(0)
    fc = gi(ind.reduceRegions(collection=UF_BR, reducer=ee.Reducer.sum().unweighted(), crs=CRS,
                              crsTransform=TRANSFORM, tileScale=4)
            .select(['ADM1_NAME'] + [f'n_classe_{k}' for k in (1, 2, 3, 4)], None, False), 'por estado')
    nomes_uf = {'n_classe_1': 'A', 'n_classe_2': 'B', 'n_classe_3': 'C_dentro', 'n_classe_4': 'C_fora'}
    uf = (pd.DataFrame([f['properties'] for f in fc['features']]).set_index('ADM1_NAME')[list(nomes_uf)]
          .rename(columns=nomes_uf).fillna(0).round(0).astype(int))
    fora = {c: cont[k] - int(uf[c].sum()) for k, c in zip((1, 2, 3, 4), nomes_uf.values())}
    total = uf.sum(axis=1).replace(0, float('nan'))
    uf['pct_nao_A'] = (100 * (uf['B'] + uf['C_dentro'] + uf['C_fora']) / total).round(2)
    uf = uf.sort_values('pct_nao_A', ascending=False)
    tabela(uf, 'Por estado (GAUL level1; pixel no estado pelo centro):')
    log(f'   fora de todos os estados (diferença para o total): {fora}')
    uf.to_csv(os.path.join(PASTA, 'Q1_por_estado.csv'), sep=';', decimal=',')

    # 3.6 Simulação: compara com o asset gravado, se existir, e termina
    if SIMULAR:
        if meta:
            gravada = ee.Image(ASSET_MASCARA).select('classe')
            cont_g = contar_classes(gravada, 'contagem do asset gravado')
            r = rr(classe.unmask(0).neq(gravada.unmask(0)).rename('dif'), ee.Reducer.sum().unweighted(),
                   'gravado x calculado')
            log(f'   asset gravado: {cont_g} | pixels diferentes do cálculo atual: {int(round(r.get("dif") or 0))}')
        log('\nℹ️ SIMULAR = True: nada foi gravado. ' +
            ('Sem ⚠️: rode o 01b para gravar.' if not avisos else
             'Há ⚠️: entenda o motivo antes de gravar.'))
        return

    # 3.7 Gravação
    if avisos:
        parar(f'Há avisos ({avisos}); não gravo. Rode o 01a e confira.')
    props = {'versao_mascara': VERSAO_MASCARA, 'dia_referencia': DIA_REFERENCIA,
             'dias_classes': ','.join(DIAS_CLASSES),                                # [V4.1 K1a]
             'gerado_em': datetime.now(timezone.utc).isoformat(timespec='seconds'),
             'metodo_centro': metodo, **{f'n_classe_{k}': int(n) for k, n in cont.items()}}
    log(f'\n🚀 Exportando {ASSET_MASCARA} com {props}')
    task = ee.batch.Export.image.toAsset(
        image=classe.set(props), description='SAB_MASCARA_QUALIDADE_Q1', assetId=ASSET_MASCARA,
        region=REGIAO_AMPLA, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10,
        pyramidingPolicy={'classe': 'mode'})       # classe é categórica: pirâmides pela moda, não pela média
    task.start()
    st = aguardar(task)
    if st is None:
        return
    if st.get('state') != 'COMPLETED':
        parar(f'Exportação não concluída: {st}')

    # 3.8 Conferência do asset gravado
    meta = ee.data.getAsset(ASSET_MASCARA)
    props_g = meta.get('properties') or {}
    gravada = ee.Image(ASSET_MASCARA).select('classe')
    cont_g = contar_classes(gravada, 'contagem do asset gravado')
    r = rr(classe.unmask(0).neq(gravada.unmask(0)).rename('dif'), ee.Reducer.sum().unweighted(), 'gravado x calculado')
    n_dif = int(round(r.get('dif') or 0))
    proj = gi(gravada.projection(), 'projeção gravada')
    problemas = []
    if cont_g != cont:
        problemas.append(f'contagens gravadas {cont_g} x calculadas {cont}')
    if n_dif:
        problemas.append(f'{n_dif} pixel(s) diferentes entre o gravado e o calculado')
    for k, v in props.items():
        if k != 'gerado_em' and props_g.get(k) != v:
            problemas.append(f'propriedade {k}: gravada {props_g.get(k)!r}, esperada {v!r}')
    if proj.get('crs') != CRS or not grade_nativa(proj.get('transform')):
        problemas.append(f'projeção gravada {proj} diferente da grade nativa')
    if problemas:
        parar('Asset gravado não confere: ' + '; '.join(problemas))
    log(f'✅ {ASSET_MASCARA} gravado e conferido: {cont_g}, grade nativa, propriedades do contrato.')
    log('   Se o App estiver publicado, compartilhe este asset para leitura como o SAB_V1.')


try:
    main()
except Exception:
    log(traceback.format_exc())
    raise
finally:
    z = shutil.make_archive(PASTA, 'zip', PASTA)
    log(f'📦 {z}')
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        log('   (baixe pelo painel Arquivos do Colab)')
