# Fumaça da K14: roda o script inteiro com Earth Engine, tarefas, Drive e link simulados.
# Rodar de uma pasta vazia: python3 /caminho/testes/fumaca_k14.py [falhar]
import os
import sys
import tempfile
import time
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(AQUI, '..', 'validacoes', 'K14_simulacao_exportacao_lote.py'), encoding='utf-8').read()
FALHAR_C3 = len(sys.argv) > 1 and sys.argv[1] == 'falhar'
DRIVE_FALSO = tempfile.mkdtemp(prefix='drive_k14_')


class D:
    def __init__(self, tag=''):
        self.tag = tag

    def __getattr__(self, n):
        if n == 'size':
            return lambda *a, **k: D('size')
        if n == 'format':
            return lambda *a, **k: D('texto')
        if n == 'getInfo':
            return lambda *a, **k: 40 if self.tag == 'size' else '2026-11-13' if self.tag == 'texto' else {}
        if n == 'getDownloadURL':
            return lambda filetype=None, selectors=None, filename='': 'fake://' + filename
        return lambda *a, **k: D()

    def __call__(self, *a, **k):
        return D()


def csv_falso(n, colunas):
    linhas = [','.join(colunas)]
    for i in range(n):
        v = {c: '' for c in colunas}
        v['N_Ponto'] = f'Ponto_{i % 40:05d}'
        v['Data_Completa'] = f'D{i // 40:06d}'
        v['Latitude'] = '-26.34952'
        linhas.append(','.join(v[c] for c in colunas))
    return '\n'.join(linhas) + '\n'


TAREFAS = {}


class Tarefa:
    def __init__(self, description, folder, fileNamePrefix, selectors, **k):
        self.id = 'ID' + description
        self.desc, self.folder, self.prefixo, self.colunas = description, folder, fileNamePrefix, selectors

    def start(self):
        n = 40 * 65 * 12 if 'mensal' in self.desc else 40 * 40
        falha = FALHAR_C3 and '_C3_' in self.desc
        if not falha:
            pasta = os.path.join(DRIVE_FALSO, self.folder)
            os.makedirs(pasta, exist_ok=True)
            with open(os.path.join(pasta, self.prefixo + '.csv'), 'w', encoding='utf-8') as f:
                f.write(csv_falso(n, self.colunas))
        TAREFAS[self.id] = {'id': self.id, 'state': 'FAILED' if falha else 'COMPLETED',
                            'creation_timestamp_ms': 1_000_000, 'start_timestamp_ms': 1_120_000,
                            'update_timestamp_ms': 1_720_000, 'batch_eecu_usage_seconds': 3600,
                            'error_message': 'Computation timed out.' if falha else ''}


ee = types.ModuleType('ee')
for nome in ('Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Geometry', 'Filter', 'Reducer', 'Date',
             'Algorithms', 'Number', 'List', 'Dictionary', 'String', 'Projection', 'Join'):
    setattr(ee, nome, D())
ee.Initialize = lambda **k: None
ee.Authenticate = lambda: None
ee.batch = types.SimpleNamespace(Export=types.SimpleNamespace(table=types.SimpleNamespace(toDrive=lambda **k: Tarefa(**k))))
ee.data = types.SimpleNamespace(getTaskStatus=lambda ids: [TAREFAS[i] for i in ids])
sys.modules['ee'] = ee


class Resp:
    def __init__(self, status, texto):
        self.status_code, self.text = status, texto


requests = types.ModuleType('requests')
requests.get = lambda url, timeout=None: Resp(200, csv_falso(1600, k14_colunas[0]))
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
k14_colunas = [ns['COLUNAS_DIARIA']]
exec('if True:' + parte2, ns)

import pandas as pd  # noqa: E402
tab = pd.read_csv(os.path.join(ns['PASTA'], 'K14_casos.csv'), sep=';', decimal=',')
log = open(ns['LOG'], encoding='utf-8').read()
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


print('\n[fumaça K14]')
confere(len(tab) == 7, '7 casos conferidos')
if FALHAR_C3:
    confere(not tab.set_index('caso').loc['C3', 'ok'] and 'Computation timed out.' in log, 'C3 com falha registrada')
    confere('❌ Algum caso' in log, 'veredito: não viável')
else:
    confere(tab['ok'].all(), 'todos completos')
    confere('idêntico ao link do painel' in log, 'C0 comparado com o link')
    confere('ENVIO POR E-MAIL VIÁVEL' in log, 'veredito: viável')
confere(os.path.exists(ns['PASTA'] + '.zip'), 'zip gerado')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'FUMAÇA OK'))
sys.exit(1 if falhas else 0)
