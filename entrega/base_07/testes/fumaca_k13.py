# Fumaça da K13: roda o script inteiro (etapas E1 a E7 e o resultado) com Earth Engine e downloads simulados.
# Rodar de uma pasta vazia: python3 /caminho/testes/fumaca_k13.py
import os
import sys
import time
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(AQUI, '..', 'validacoes', 'K13_simulacao_organizacao_downloads.py'), encoding='utf-8').read()


class D:
    """Objeto do Earth Engine falso: aceita qualquer encadeamento; size()/getInfo() devolvem números."""
    def __init__(self, tag=''):
        self.tag = tag

    def __getattr__(self, n):
        if n == 'size':
            return lambda *a, **k: D('size')
        if n == 'aggregate_array':
            return lambda *a, **k: D('lista')
        if n == 'getInfo':
            return lambda *a, **k: (['Pato Branco', 'Clevelandia', 'Coronel Vivida'] if self.tag == 'lista'
                                    else 40 if self.tag == 'size' else {})
        if n == 'getDownloadURL':
            return lambda filetype=None, selectors=None, filename='': 'fake://' + filename
        return lambda *a, **k: D(self.tag if n in ('distinct', 'sort') else '')

    def __call__(self, *a, **k):
        return D()


ee = types.ModuleType('ee')
for nome in ('Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Geometry', 'Filter', 'Reducer', 'Date',
             'Algorithms', 'Number', 'List', 'Dictionary', 'String', 'Projection', 'Join'):
    setattr(ee, nome, D())
ee.Initialize = lambda **k: None
ee.Authenticate = lambda: None
sys.modules['ee'] = ee

ESPERADOS = {}
FALHAR = ('E1_2_anos', 'E1_18_meses_t2', 'E5_44_anos', 'E7_1_link')
VEZES_429 = {}


class Resp:
    def __init__(self, status, texto):
        self.status_code = status
        self.text = texto
        self.content = texto.encode()


def get(url, timeout=None):
    rot = url.replace('fake://', '')
    if any(rot.startswith(f) for f in FALHAR):
        return Resp(503, '{"error": {"code": 503, "message": "Please try again."}}')
    if rot.startswith('E6_3_de_cada_vez') and VEZES_429.get(rot, 0) == 0:
        VEZES_429[rot] = 1
        return Resp(429, 'Too many concurrent aggregations')
    n, colunas = ESPERADOS[rot]
    linhas = [','.join(colunas)]
    for i in range(n):
        val = {c: '' for c in colunas}
        val['N_Ponto'] = f'Ponto_{i % 40:05d}'
        val['Data_Completa'] = f'D{i // 40:06d}'
        linhas.append(','.join(val[c] for c in colunas))
    return Resp(200, '\n'.join(linhas) + '\n')


requests = types.ModuleType('requests')
requests.get = get
requests.exceptions = types.SimpleNamespace(Timeout=TimeoutError)
sys.modules['requests'] = requests
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
ns['ARQ_TESTES'] = os.path.join(ns['PASTA'], os.path.basename(ns['ARQ_TESTES']))
original = ns['baixar']


def baixar(rotulo, fc, colunas, esperado):
    ESPERADOS[rotulo] = (esperado, colunas)
    return original(rotulo, fc, colunas, esperado)


ns['baixar'] = baixar
exec('if True:' + parte2, ns)

# conferências da fumaça
import pandas as pd  # noqa: E402
pasta = ns['PASTA']
t = pd.read_csv(os.path.join(pasta, 'K13_testes.csv'), sep=';', decimal=',')
dec = pd.read_csv(os.path.join(pasta, 'K13_DECISOES.csv'), sep=';').set_index('decisao')['resultado'].to_dict()
plano = pd.read_csv(os.path.join(pasta, 'K13_PLANO.csv'), sep=';')
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


print('\n[fumaça K13]')
confere(set(t['etapa']) == {'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7'}, 'as 7 etapas rodaram')
confere(not t[t['teste'].str.startswith('E1_3_anos')].shape[0], 'E1 parou depois do degrau que falhou 2 vezes')
confere(str(dec['R6 links ao mesmo tempo']) in ('1', '2'), 'R6: 3 de cada vez com 429 não é escolhido')
confere(dec['R7 ano grande demais: dividir por'] == 'periodo', 'R7: período quando os dois abrem com tempo parecido')
confere(len(plano) >= 5, 'plano com os pedidos de exemplo')
confere(os.path.exists(pasta + '.zip'), 'zip gerado')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'FUMAÇA OK'))
sys.exit(1 if falhas else 0)
