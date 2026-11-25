# Fumaça da K15: roda o script inteiro com Earth Engine, asset, tarefas, Drive e link simulados.
# Rodar de uma pasta vazia: python3 /caminho/testes/fumaca_k15.py
import os
import sys
import tempfile
import time
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(AQUI, '..', 'validacoes', 'K15_simulacao_grade_asset.py'), encoding='utf-8').read()
DRIVE_FALSO = tempfile.mkdtemp(prefix='drive_k15_')
ASSETS = set()
APAGADOS = []


class D:
    def __init__(self, tag=''):
        self.tag = tag

    def __getattr__(self, n):
        if n == 'size':
            return lambda *a, **k: D('size')
        if n == 'reduceColumns':
            return lambda *a, **k: D('cols')
        if n == 'get':
            return lambda *a, **k: D(self.tag)
        if n == 'getInfo':
            return lambda *a, **k: (40 if self.tag == 'size' else
                                    [['Ponto_00001', -26.3, -52.6, 'A', 'Estado_Completo', 'Parana', 'Parana']]
                                    if self.tag == 'cols' else {})
        if n == 'getDownloadURL':
            return lambda filetype=None, selectors=None, filename='': 'fake://' + filename
        return lambda *a, **k: D()

    def __call__(self, *a, **k):
        return D()


def csv_falso(n, colunas, formato):
    linhas = [','.join(colunas)]
    for i in range(n):
        v = {c: '' for c in colunas}
        v['N_Ponto'] = f'Ponto_{i % 40:05d}'
        v['Data_Completa'] = f'D{i // 40:06d}'
        v['Temperatura_Maxima_C'] = '18.399999618530273' if formato == 'cru' else '18.40'
        linhas.append(','.join(v[c] for c in colunas))
    return '\n'.join(linhas) + '\n'


TAREFAS = {}
MINUTOS = {'V0a': 60, 'V1a': 15, 'V3': 55, 'V2': 14, 'V0b': 58, 'V1b': 16, 'grade': 1}


class Tarefa:
    def __init__(self, description, **k):
        self.id = 'ID_' + description
        self.desc, self.k = description, k

    def start(self):
        if 'assetId' in self.k:
            ASSETS.add(self.k['assetId'])
            minutos = 1
        else:
            v = self.desc.split('_')[1]
            minutos = MINUTOS[v]
            fmt = 'cru' if self.desc.endswith('_cru') else 'ponto'
            pasta = os.path.join(DRIVE_FALSO, self.k['folder'])
            os.makedirs(pasta, exist_ok=True)
            with open(os.path.join(pasta, self.k['fileNamePrefix'] + '.csv'), 'w', encoding='utf-8') as f:
                f.write(csv_falso(1600, self.k['selectors'], fmt))
        TAREFAS[self.id] = {'id': self.id, 'state': 'COMPLETED', 'creation_timestamp_ms': 0,
                            'start_timestamp_ms': 60000, 'update_timestamp_ms': 60000 + minutos * 60000,
                            'batch_eecu_usage_seconds': 100, 'error_message': ''}


def get_asset(a):
    if a not in ASSETS:
        raise Exception('not found')
    return {}


ee = types.ModuleType('ee')
for nome in ('Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Geometry', 'Filter', 'Reducer', 'Date',
             'Algorithms', 'Number', 'List', 'Dictionary', 'String', 'Projection', 'Join'):
    setattr(ee, nome, D())
ee.Initialize = lambda **k: None
ee.Authenticate = lambda: None
ee.batch = types.SimpleNamespace(Export=types.SimpleNamespace(table=types.SimpleNamespace(
    toDrive=lambda **k: Tarefa(**k), toAsset=lambda **k: Tarefa(**k))))
ee.data = types.SimpleNamespace(getTaskStatus=lambda ids: [TAREFAS[i] for i in ids], getAsset=get_asset,
                                deleteAsset=lambda a: APAGADOS.append(a))
sys.modules['ee'] = ee


class Resp:
    def __init__(self, status, conteudo):
        self.status_code, self.content, self.text = status, conteudo.encode(), conteudo


requests = types.ModuleType('requests')
requests.get = lambda url, timeout=None: Resp(200, csv_falso(1600, ['N_Ponto', 'Data_Completa'], 'ponto'))
requests.exceptions = types.SimpleNamespace(Timeout=TimeoutError)
sys.modules['requests'] = requests
colab = types.ModuleType('google.colab')
colab.drive = types.SimpleNamespace(mount=lambda p: None)
colab.files = types.SimpleNamespace(download=lambda z: None)
sys.modules['google'] = types.ModuleType('google')
sys.modules['google.colab'] = colab
time.sleep = lambda s: None

parte1, parte2 = SRC.split("if __name__ == '__main__':", 1)
ns = {'__name__': 'fumaca'}
exec(parte1, ns)
# Pasta de saída própria desta execução (a do script tem só o minuto no nome: duas execuções no mesmo minuto
# escreviam no mesmo LOG e a contagem de linhas do teste dobrava)
import tempfile as _tf  # noqa: E402
_SAIDA = _tf.mkdtemp(prefix='saida_fumaca_')
ns['PASTA'] = os.path.join(_SAIDA, os.path.basename(ns['PASTA']))
ns['LOG'] = os.path.join(ns['PASTA'], os.path.basename(ns['LOG']))
ns['DRIVE'] = DRIVE_FALSO
exec('if True:' + parte2, ns)

log = open(ns['LOG'], encoding='utf-8').read()
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


print('\n[fumaça K15]')
confere(log.count('✅ V') == 6, 'as 6 exportações conferidas completas')
confere('idêntico a V0a' in log and 'igual a V0a a menos do arredondamento' in log, 'comparações de conteúdo feitas')
confere('Grade em asset: ADOTAR' in log, 'G: asset 4x mais rápido nos 2 pares -> adotar')
confere('manter o formato do painel' in log, 'F: cru sem ganho de 25% -> manter')
confere(APAGADOS == [ns['ASSET_GRADE']], 'asset de teste apagado no fim')
confere(os.path.exists(ns['PASTA'] + '.zip'), 'zip gerado')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'FUMAÇA OK'))
sys.exit(1 if falhas else 0)
