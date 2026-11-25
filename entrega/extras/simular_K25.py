# Simulador do Earth Engine para rodar o K25 INTEIRO offline, sem servidor e sem credencial.
#
# POR QUE ISTO EXISTE
#   O teste_K25.py cobre as funções puras, mas o erro que derrubou a v1 no Colab
#   ("Reducer input must be a number") estava no lado SERVIDOR: o fixedHistogram devolve array por
#   pixel e eu pedi Reducer.sum() sobre array. Nenhum teste de função pura pega isso.
#   Este arquivo finge ser o módulo `ee` e é DELIBERADAMENTE ESTRITO nas regras que importam:
#     - reducer escalar (sum/mean/min/max/count) sobre banda de ARRAY  -> recusa, como o servidor
#     - repeat(n).group(groupField=n) com número de bandas diferente de n+1 -> recusa
#     - select de banda que não existe -> recusa
#   Tudo o mais devolve número sintético plausível, só para o código correr até o fim.
#
# COMO RODAR:  python3 -I simular_K25.py
# Esperado: todas as partes chegam ao fim, nenhum FALHOU, e os CSV aparecem numa pasta temporária.
import importlib.util
import math
import os
import shutil
import sys
import tempfile

import numpy as np

N_PIX = 1000                      # pixels fictícios por bloco
CLASSES_SIM = (1, 2, 3, 4)


class EEException(Exception):
    pass


ESCALAR = {'sum', 'mean', 'stdDev', 'min', 'max', 'count', 'minMax', 'percentile'}


class Reducer:
    def __init__(self, nome, n=1, grupo=None, args=None):
        self.nome, self.n, self.grupo, self.args = nome, n, grupo, args or {}

    def repeat(self, n):
        return Reducer(self.nome, n, self.grupo, self.args)

    def group(self, groupField=None, groupName='group'):
        return Reducer(self.nome, self.n, (groupField, groupName), self.args)

    def combine(self, outro, sharedInputs=False):
        return Reducer(self.nome + '+' + outro.nome, self.n, self.grupo, self.args)

    @property
    def chave(self):
        return {'minMax': 'min', 'stdDev': 'stdDev'}.get(self.nome, self.nome)


class _Reducers:
    def sum(self): return Reducer('sum')
    def mean(self): return Reducer('mean')
    def stdDev(self): return Reducer('stdDev')
    def min(self): return Reducer('min')
    def max(self): return Reducer('max')
    def count(self): return Reducer('count')
    def minMax(self): return Reducer('minMax')
    def percentile(self, ps): return Reducer('percentile', args={'ps': ps})
    def fixedHistogram(self, lo, hi, steps): return Reducer('fixedHistogram', args={'lo': lo, 'hi': hi, 'n': steps})


class Image:
    """bands: lista de (nome, tipo) com tipo 'num' ou 'array'."""

    def __init__(self, bands=None, src=None):
        if isinstance(bands, (int, float)):
            bands = [('constant', 'num')]
        self.bands = list(bands) if bands else [('b', 'num')]

    # ---- estrutura
    def bandNames(self):
        return List([b for b, _ in self.bands])

    def select(self, *a):
        sel = a[0] if len(a) == 1 else list(a)
        nomes = [b for b, _ in self.bands]
        if isinstance(sel, str):
            sel = [sel]
        if isinstance(sel, (list, tuple)):
            saida = []
            for x in sel:
                if isinstance(x, int):
                    saida.append(self.bands[x])
                    continue
                achou = [t for t in self.bands if t[0] == x]
                if not achou:
                    raise EEException(f'Image.select: no band named {x!r}. Bands: {nomes}')
                saida.append(achou[0])
            return Image(saida)
        return Image(self.bands[:1])

    def rename(self, *a):
        novo = a[0] if len(a) == 1 else list(a)
        if isinstance(novo, List):
            novo = novo.v
        if isinstance(novo, str):
            novo = [novo]
        if len(novo) != len(self.bands):
            raise EEException(f'Image.rename: {len(novo)} names for {len(self.bands)} bands')
        return Image([(n, t) for n, (_, t) in zip(novo, self.bands)])

    def addBands(self, outra):
        outras = outra.bands if isinstance(outra, Image) else []
        if isinstance(outra, list):
            outras = [b for im in outra for b in im.bands]
        return Image(self.bands + outras)

    # ---- aritmética e máscara: preservam a forma
    def _mesmo(self, *a, **k):
        return Image(self.bands)

    for _m in ('add subtract multiply divide pow min max abs sqrt exp log cos sin tan acos atan '
               'clamp gt gte lt lte eq neq And Or Not unmask updateMask mask resample reproject '
               'focalMean int float toFloat copyProperties set clip arrayFlatten').split():
        locals()[_m] = _mesmo
    del _m

    def expression(self, *a, **k):
        return Image([(self.bands[0][0], 'num')])

    # ---- reduções
    def reduce(self, reducer):
        """Image.reduce reduz ENTRE BANDAS por pixel. fixedHistogram devolve ARRAY por pixel."""
        tipo = 'array' if reducer.nome in ('fixedHistogram', 'percentile') else 'num'
        nome = {'sum': 'sum', 'mean': 'mean', 'stdDev': 'stdDev', 'min': 'min', 'max': 'max',
                'count': 'count'}.get(reducer.nome, reducer.nome)
        return Image([(nome, tipo)])

    def reduceRegion(self, reducer=None, geometry=None, crs=None, crsTransform=None,
                     maxPixels=None, tileScale=None, scale=None, **k):
        r = reducer
        arrays = [n for n, t in self.bands if t == 'array']
        if r.nome in ESCALAR and arrays:
            raise EEException('Reducer input must be a number.')
        if r.grupo is not None:
            campo, nome_grupo = r.grupo
            if campo != len(self.bands) - 1:
                raise EEException(
                    f'Reducer.group: groupField {campo} but the image has {len(self.bands)} bands; '
                    f'the group band must be the last one (groupField = n_bands - 1 = '
                    f'{len(self.bands) - 1})')
            if r.n != len(self.bands) - 1:
                raise EEException(
                    f'Reducer.repeat({r.n}) with {len(self.bands) - 1} value bands: must be equal')
            rng = np.random.default_rng(abs(hash(tuple(n for n, _ in self.bands))) % 2**31)
            grupos = []
            for c in CLASSES_SIM:
                vals = []
                for i, (n, _) in enumerate(self.bands[:-1]):
                    if n.startswith('n_pix') or n.startswith('n__') or n == 'n' or n.startswith('n__'):
                        vals.append(float(N_PIX))
                    elif r.nome in ('min',):
                        vals.append(float(rng.uniform(-5, 0)))
                    elif r.nome in ('max',):
                        vals.append(float(rng.uniform(20, 45)))
                    else:
                        vals.append(float(rng.integers(0, 3)))
                grupos.append({nome_grupo: c, r.chave: vals})
            return Dictionary({'groups': grupos})
        # sem grupo
        rng = np.random.default_rng(abs(hash(tuple(n for n, _ in self.bands))) % 2**31)
        saida = {}
        for n, t in self.bands:
            if r.nome == 'fixedHistogram':
                if t == 'array':
                    raise EEException('Reducer input must be a number.')
                nb = int(r.args['n'])
                h = rng.multinomial(N_PIX, np.full(nb, 1.0 / nb)).astype(float)
                bordas = np.linspace(r.args['lo'], r.args['hi'], nb + 1)
                saida[n] = [[float(bordas[i]), float(h[i])] for i in range(nb)]
            elif r.nome == 'percentile':
                for p in r.args['ps']:
                    saida[f'{n}_p{p}'] = float(rng.uniform(0, 30))
            elif n == 'n' or n.startswith('n_pix') or n.startswith('n__'):
                saida[n] = float(N_PIX)
            else:
                saida[n] = float(rng.integers(0, 3))
        return Dictionary(saida)

    def sample(self, region=None, projection=None, factor=None, seed=None, geometries=None,
               dropNulls=None, tileScale=None, numPixels=None, **k):
        return FeatureCollection([Feature(None, {n: 1.0 for n, _ in self.bands}) for _ in range(3)])

    def sampleRegions(self, collection=None, properties=None, projection=None, geometries=None,
                      tileScale=None, scale=None, **k):
        props = {}
        for n, _ in self.bands:
            props[n] = 1.0
        props['pid'] = 0
        props['i'] = 0
        return FeatureCollection([Feature(None, dict(props, pid=k)) for k in range(5)])

    def stratifiedSample(self, numPoints=None, classBand=None, region=None, projection=None,
                         seed=None, classValues=None, classPoints=None, geometries=None,
                         tileScale=None, **k):
        n = (classPoints or [5])[0]
        return FeatureCollection([Feature({'coordinates': [-60.0 + 0.1 * i, -12.0 - 0.1 * i]},
                                          {'pid': i}) for i in range(min(n, 8))])

    def pixelLonLat(self):
        return Image([('longitude', 'num'), ('latitude', 'num')])

    def getInfo(self):
        return {n: 1.0 for n, _ in self.bands}

    def propertyNames(self):
        return List(['system:time_start', 'versao', 'versao_algoritmo'])

    def get(self, k):
        return k


def _img_ctor(x=None):
    if isinstance(x, Image):
        return x
    if isinstance(x, (int, float)):
        return Image([('constant', 'num')])
    if isinstance(x, str):
        # asset: devolve as bandas que o K25 pede desses assets
        if 'MASCARA' in x:
            return Image([('classe', 'num')])
        if 'SRTM' in x:
            return Image([('elevation', 'num')])
        if 'Matriz_EQM' in x:
            return Image([('pr_max_br', 'num')])
        if 'Matriz_GFS' in x:
            return Image([(f'Tmax_{t}_{f}_{fx}', 'num') for t in 'ms' for f in ('sicsb', 'gfs')
                          for fx in ('L1', 'L2a5', 'L6a10', 'L11a15')])
        return Image(BANDAS_SAB)
    return Image(BANDAS_SAB)


class _ImageNS:
    def __call__(self, x=None):
        return _img_ctor(x)

    def constant(self, v):
        if isinstance(v, (list, tuple)):
            return Image([(f'constant_{i}', 'num') for i in range(len(v))])
        return Image([('constant', 'num')])

    def cat(self, lista):
        if isinstance(lista, Image):
            return lista
        bands = []
        for im in lista:
            bands += im.bands
        return Image(bands)

    def pixelLonLat(self):
        return Image([('longitude', 'num'), ('latitude', 'num')])


BANDAS_SAB = [(b, 'num') for b in
              ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2',
               'tsolo_C', 'tfolha_C', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm',
               'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']]


BANDAS_BR = [(b, 'num') for b in ('pr', 'Tmax', 'Tmin', 'RH', 'Rs', 'u2', 'ETo')]
BANDAS_ERA5 = [(b, 'num') for b in ('total_precipitation_sum', 'total_evaporation_sum',
                                    'surface_runoff_sum', 'sub_surface_runoff_sum',
                                    'volumetric_soil_water_layer_1', 'volumetric_soil_water_layer_2',
                                    'volumetric_soil_water_layer_3')]


def _bandas_de(origem):
    o = str(origem or '')
    if 'BR-DWGD' in o or 'alexandrexavier' in o:
        return BANDAS_BR
    if 'ERA5' in o:
        return BANDAS_ERA5
    return BANDAS_SAB


class ImageCollection:
    def __init__(self, x=None):
        self.origem = x if isinstance(x, str) else None
        if isinstance(x, list) and x and isinstance(x[0], Image):
            self.imgs = x
        elif isinstance(x, List):
            if x.v and isinstance(x.v[0], Image):
                self.imgs = list(x.v)                 # ee.ImageCollection(ee.List([Image, ...]))
            else:
                self.imgs = [Image(_bandas_de(None)) for _ in range(max(1, len(x.v)))]
        else:
            self.imgs = [Image(_bandas_de(x)) for _ in range(40)]

    def filterDate(self, *a): return self
    def filter(self, *a): return self

    def map(self, fn):
        saida = [fn(i) for i in self.imgs]      # SEM try/except: erro de forma tem de aparecer
        if saida and isinstance(saida[0], Image):
            nova = ImageCollection(saida)
            nova.origem = self.origem
            return nova
        return FeatureCollection([f if isinstance(f, Feature) else Feature(None, {}) for f in saida])
    def select(self, *a): return ImageCollection([i.select(*a) for i in self.imgs])
    def first(self): return self.imgs[0]
    def size(self): return Number(0)
    def reduce(self, reducer): return self.imgs[0].reduce(reducer)
    def mean(self): return Image([(n, t) for n, t in self.imgs[0].bands])
    def max(self): return Image([(n, t) for n, t in self.imgs[0].bands])
    def sum(self): return Image([(n, t) for n, t in self.imgs[0].bands])
    def toBands(self):
        bands = []
        for k, im in enumerate(self.imgs):
            bands += [(f'{k}_{n}', t) for n, t in im.bands]
        return Image(bands)
    def aggregate_array(self, p): return List([])
    def toList(self, n): return List(self.imgs)
    def getRegion(self, *a, **k):
        cab = ['id', 'longitude', 'latitude', 'time'] + [n for n, _ in self.imgs[0].bands]
        linhas = [cab]
        for d in range(6):
            for p in range(5):
                linhas.append(['x', -60.0 + 0.1 * p, -12.0 - 0.1 * p,
                               1767225600000 + d * 86400000] + [20.0] * (len(cab) - 4))
        return List(linhas)


class List:
    def __init__(self, v): self.v = list(v) if not isinstance(v, List) else v.v
    def map(self, fn): return List([fn(x) for x in self.v])
    def getInfo(self): return self.v
    def distinct(self): return self
    def contains(self, x): return True
    def __len__(self): return len(self.v)

    @staticmethod
    def sequence(a, b): return List(list(range(int(a), int(b) + 1)))


class Dictionary:
    def __init__(self, d): self.d = d
    def getInfo(self): return self.d

    @staticmethod
    def fromLists(a, b):
        ks = a.v if isinstance(a, List) else list(a)
        vs = b.v if isinstance(b, List) else list(b)
        return Dictionary({k: (vs[i] if i < len(vs) else None) for i, k in enumerate(ks)})


class Number:
    def __init__(self, v=0.0):
        self.v = float(v.v) if isinstance(v, Number) else float(v)   # ee.Number(ee.Number(x)) é legal

    def _o(self, x): return x.v if isinstance(x, Number) else float(x)
    def add(self, x): return Number(self.v + self._o(x))
    def subtract(self, x): return Number(self.v - self._o(x))
    def multiply(self, x): return Number(self.v * self._o(x))
    def divide(self, x): return Number(self.v / (self._o(x) or 1.0))
    def pow(self, x): return Number(self.v ** self._o(x))
    def max(self, x): return Number(max(self.v, self._o(x)))
    def min(self, x): return Number(min(self.v, self._o(x)))
    def clamp(self, a, b): return Number(min(max(self.v, self._o(a)), self._o(b)))
    def sqrt(self): return Number(math.sqrt(abs(self.v)))
    def cos(self): return Number(math.cos(self.v))
    def sin(self): return Number(math.sin(self.v))
    def tan(self): return Number(math.tan(self.v))
    def acos(self): return Number(math.acos(max(-1.0, min(1.0, self.v))))
    def exp(self): return Number(math.exp(min(self.v, 700)))
    def getInfo(self): return self.v


class Date:
    def __init__(self, d): self.d = d
    def advance(self, n, u): return self
    def getRelative(self, a, b): return Number(100)
    def millis(self): return Number(1767225600000)


class Geometry:
    @staticmethod
    def Rectangle(c, p=None, g=None): return Geometry()
    @staticmethod
    def Point(c): return Geometry()
    @staticmethod
    def MultiPoint(c): return Geometry()


class Projection:
    def __init__(self, *a): pass


BASE_MS = 1767225600000          # 2026-01-01T00:00:00Z


class Feature:
    def __init__(self, geom=None, props=None):
        self.geometry_ = geom or {'coordinates': [-60.0, -12.0]}
        if isinstance(props, Dictionary):
            props = dict(props.d)
        self.properties = dict(props or {})
    def getInfo(self): return {'geometry': self.geometry_, 'properties': dict(self.properties)}


class FeatureCollection:
    def __init__(self, feats): self.feats = feats
    def limit(self, n): return FeatureCollection(self.feats[:n])

    def getInfo(self):
        saida = []
        for k, f in enumerate(self.feats):
            d = f.getInfo()
            p = d['properties']
            if 'system:time_start' in p:          # inventário: preenche dias plausíveis
                p['system:time_start'] = BASE_MS + k * 86400000
                p['versao'] = 'provisoria_era5' if k < len(self.feats) - 6 else 'provisoria_gfs'
                p['versao_algoritmo'] = 'V1.6'
                p['Faixa_Prazo_GFS'] = 'L1' if k >= len(self.feats) - 6 else ''
                p['metodo_ur_vento_era5'] = 'UR eqm; vento media'
                p['rs_limitado_rso'] = 'true'
                p['teto_chuva_fator'] = 1.5
            saida.append(d)
        return {'features': saida}


class _Filter:
    def eq(self, *a): return self
    def calendarRange(self, *a): return self


class _Algorithms:
    def If(self, c, a, b): return a


class _Data:
    pass


class _Task:
    @staticmethod
    def start(*a, **k): pass


class _Batch:
    Task = _Task


def _initialize(**k): pass
def _authenticate(**k): pass


# =========================================================================================
# A PARTIR DAQUI: achar o K25 PRIMEIRO, depois instalar o `ee` falso, e SEMPRE devolvê-lo.
# Em 15/11/2026 este arquivo foi colado numa célula do Colab. Ele instalava o `ee` falso e só depois
# procurava o K25; não achou, levantou SystemExit — e deixou o `ee` falso na sessão. A célula
# seguinte, com o K25 de verdade, mediu o simulador sem avisar. Nunca mais: nada é trocado antes de
# haver o que rodar, e a troca é desfeita no finally, inclusive em SystemExit.
# =========================================================================================
try:
    AQUI = os.path.dirname(os.path.abspath(__file__))
except NameError:
    AQUI = os.getcwd()

ALVO = None
for cand in (os.path.join(AQUI, '..', '02_Colab_testes', 'K25_varredura_total.py'),
             os.path.join(AQUI, 'K25_varredura_total.py'),
             os.path.join(os.getcwd(), 'K25_varredura_total.py'),
             '/content/K25_varredura_total.py'):
    if os.path.exists(cand):
        ALVO = os.path.abspath(cand)
        break

EM_NOTEBOOK = 'IPython' in sys.modules or os.path.isdir('/content')
FORCAR = os.environ.get('K25_SIMULAR_AQUI') == '1'

if ALVO is None:
    print('=' * 78)
    print('NÃO ACHEI o K25_varredura_total.py — e por isso NÃO mexi em nada.')
    print('Nenhum `ee` falso foi instalado nesta sessão: o K25 pode rodar normalmente.')
    print()
    print('Ponha os dois arquivos no mesmo lugar e rode o simulador como PROCESSO SEPARADO:')
    print('   !python3 -I simular_K25.py')
    print('No Colab, suba os dois com o botão de arquivos ou:')
    print("   from google.colab import files; files.upload()")
    print('=' * 78)
    sys.exit(2)

if EM_NOTEBOOK and not FORCAR:
    print('=' * 78)
    print('NÃO rode o simulador colando-o numa célula. NÃO mexi em nada.')
    print()
    print('Motivo: para simular, este arquivo precisa trocar o módulo `ee` por um falso. Numa célula,')
    print('essa troca vale para a sessão inteira, e o K25 colado depois mediria o simulador em vez do')
    print('SAB. Foi o que aconteceu em 15/11/2026.')
    print()
    print('Rode assim, numa célula, com o ponto de exclamação (processo separado, sessão intacta):')
    print('   !python3 -I simular_K25.py')
    print('=' * 78)
    sys.exit(2)

# monta o módulo falso
mod = type(sys)('ee')
mod.SIMULADO = True               # o K25 procura exatamente isto antes de medir qualquer coisa
mod.Image = _ImageNS()
mod.ImageCollection = ImageCollection
mod.Reducer = _Reducers()
mod.List = List
mod.Dictionary = Dictionary
mod.Number = Number
mod.Date = Date
mod.Geometry = Geometry
mod.Projection = Projection
mod.Feature = Feature
mod.FeatureCollection = FeatureCollection
mod.Filter = _Filter()
mod.Algorithms = _Algorithms()
mod.data = _Data()
mod.batch = _Batch
mod.Initialize = _initialize
mod.Authenticate = _authenticate
mod.ee_exception = type(sys)('ee.ee_exception')
mod.ee_exception.EEException = EEException
for n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
          'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable',
          'startIngestion', 'cancelTask'):
    setattr(mod.data, n, lambda *a, **k: None)

_ee_antes = sys.modules.get('ee', '<ausente>')
_cwd_antes = os.getcwd()
TMP = tempfile.mkdtemp(prefix='sim_k25_')
codigo = 0
try:
    sys.modules['ee'] = mod
    os.chdir(TMP)
    spec = importlib.util.spec_from_file_location('k25_sim', ALVO)
    K = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(K)

    from datetime import datetime, timedelta, timezone
    K.SIMULACAO_PERMITIDA = True          # sem isto o K25 se recusa a rodar, e é assim que deve ser
    K.AGORA = datetime(2026, 11, 15, 9, 0, tzinfo=timezone(timedelta(hours=-3)))   # fora da janela
    K.PASTA = os.path.join(TMP, 'saida')
    K.ACUMULADO = os.path.join(TMP, 'acumulado')
    K.LOG = os.path.join(K.PASTA, 'LOG.txt')
    K.N_BOOT, K.N_PERM = 50, 200          # a estatística é a mesma; só mais rápida
    K.BINS = 64

    print('=' * 78)
    print('SIMULAÇÃO DO K25 — módulo `ee` falso, estrito nas regras que importam.')
    print('Os números são sintéticos: o que se verifica aqui é se o PEDIDO se monta, não o dado.')
    print('=' * 78)
    K.principal()

    res = K.RESULTADOS
    falhou = [r for r in res if r['status'] == 'FALHOU']
    print('\n' + '=' * 78)
    for r in res:
        print(f'   {r["item"]:<4} {r["status"]:<8} {r["titulo"]}')
    pasta_saida = K.PASTA
    csvs = sorted(f for f in os.listdir(pasta_saida) if f.endswith('.csv')) if os.path.isdir(pasta_saida) else []
    print(f'\nCSV gerados: {len(csvs)}')
    for c in csvs:
        print('   ' + c)
    print('=' * 78)
    if falhou:
        print(f'❌ {len(falhou)} parte(s) com FALHOU — o servidor recusaria o mesmo pedido:')
        for r in falhou:
            print(f'   {r["item"]}: {r["texto"][:200]}')
        print('\n(o traceback de cada uma está acima, no log da simulação)')
        codigo = 1
    else:
        print('✅ Todas as partes chegaram ao fim sem erro de forma.')
    print('=' * 78)
finally:
    # devolve a sessão exatamente como estava, aconteça o que acontecer
    if _ee_antes == '<ausente>':
        sys.modules.pop('ee', None)
    else:
        sys.modules['ee'] = _ee_antes
    try:
        os.chdir(_cwd_antes)
    except Exception:
        pass
    shutil.rmtree(TMP, ignore_errors=True)
    print('(o módulo `ee` desta sessão foi restaurado; o K25 pode rodar normalmente)')
sys.exit(codigo)
