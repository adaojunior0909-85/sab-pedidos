# Fumaça da K17 v2: principal() com um Earth Engine falso que (1) sorteia os 1.000 pixels, (2) responde às amostras
# e (3) RECUSA com "User memory limit exceeded" qualquer amostra com mais de 250 pixels, como o servidor fez no P2
# da v1 em 03/11/2026. Confere que o lote cai pela metade sozinho, que P2, P3 e P4 terminam com todos os pixels
# e que nada é gravado. Rodar: python3 testes/fumaca_k17.py
import os
import sys
import tempfile
import time
import types

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(AQUI, '..', 'validacoes', 'K17_validacao_final_SAB.py'), encoding='utf-8').read()
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


LIMITE = 250
PEDIDOS = {'amostra': [], 'recusadas': 0}
BANDAS_MATRIZ = ['a_m_br', 'b_m_br', 'a_s_br', 'b_s_br', 'a_m_era', 'b_m_era', 'a_s_era', 'b_s_era']
LIMITE_TABELA = 20               # P4: pedido de tabela acima disso é recusado por memória
MASCARA = {'n_classe_1': 70632, 'n_classe_2': 301, 'n_classe_3': 47, 'n_classe_4': 1060}


class S:
    def __init__(self, nome='ee', bandas=None, feats=None, props=None):
        self._n, self._bandas, self._feats, self._props = nome, bandas, feats, props

    def __getattr__(self, a):
        if a.startswith('__'):
            raise AttributeError(a)
        if a == 'getInfo':
            return self._responder
        if a == 'start':
            raise AssertionError('start chamado')
        return S(f'{self._n}.{a}', self._bandas, self._feats)

    def __call__(self, *a, **k):
        novo = S(self._n + '()', self._bandas, self._feats)
        if self._n.endswith('.rename') and a and isinstance(a[0], list):
            novo._bandas = a[0]
        if self._n.endswith('Feature') and len(a) > 1:
            novo._props = a[1]
        if self._n.endswith('FeatureCollection') and a and isinstance(a[0], list):
            novo._feats = [x._props for x in a[0]]
        if self._n.endswith('.sampleRegions') or self._n.endswith('.reduceRegions'):
            novo._feats = k['collection']._feats
        if self._n.endswith('List') and a and isinstance(a[0], list):
            novo._nlist = len(a[0])
        return novo

    def __getitem__(self, k):
        return S(self._n + '[]')

    def _op(self, *a):
        return S(self._n + '·', self._bandas, self._feats)
    __add__ = __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = __truediv__ = __rtruediv__ = __neg__ = _op

    def _responder(self):
        n = self._n
        if '.stratifiedSample()' in n:                       # sorteio estratificado dos pixels fixos
            return {'features': [{'properties': {'classe': [1, 1, 1, 2, 3, 4][i % 6], 'longitude': 0, 'latitude': 0},
                                  'geometry': {'type': 'Point', 'coordinates': [-50 + i * 0.01, -10]}}
                                 for i in range(1000)]}
        if n.endswith('.sampleRegions()'):
            if len(self._feats) > LIMITE:
                PEDIDOS['recusadas'] += 1
                raise Exception('User memory limit exceeded.')
            PEDIDOS['amostra'].append(len(self._feats))
            return {'features': [{'properties': {**p, **{b: 1.5 for b in self._bandas}}} for p in self._feats]}
        if n.endswith('.bandNames()'):
            return list(BANDAS_MATRIZ)
        if n.endswith('List()'):                             # bandas de cada coleção capturada no P4
            return [['x1', 'x2']] * self._nlist
        if n.endswith('.reduceRegion()'):                    # P9: contagem da máscara
            return dict(MASCARA)
        if n.endswith('.toDictionary()'):                    # P9: propriedades gravadas pelo 01b
            return dict(MASCARA, metodo_centro='teste')
        raise RuntimeError('sem resposta neste teste')


class IC(S):
    """ImageCollection falsa como CLASSE (a K17 v3 troca mean/reduce na classe para saber que coleções o
    código original usa). Lê a tabela dos pontos (reduceRegions dentro do map) e responde a reduceColumns."""
    capturas = []

    def __init__(self, *a, nome='IC', feats=None, sel=None):
        S.__init__(self, nome, None, feats)
        self._sel = sel

    def __getattr__(self, a):
        if a.startswith('__'):
            raise AttributeError(a)
        if a == 'getInfo':
            return self._responder_ic
        if a == 'first':
            return lambda *x: S(self._n + '.first()')
        if a == 'map':
            def mapear(f, *x, **k):
                r = f(S('img'))
                return IC(nome=self._n + '.map()', feats=getattr(r, '_feats', None) or self._feats)
            return mapear
        if a == 'reduceColumns':
            return lambda red, sel, *x, **k: IC(nome=self._n + '.reduceColumns()', feats=self._feats, sel=sel)
        return lambda *x, **k: IC(nome=self._n + '.' + a + '()', feats=self._feats, sel=self._sel)

    def mean(self, *a, **k):
        IC.capturas.append('mean')
        return S(self._n + '.mean()')

    def reduce(self, *a, **k):
        IC.capturas.append('reduce')
        return S(self._n + '.reduce()')

    def _responder_ic(self):
        if self._n.endswith('.reduceColumns()') and self._feats:
            if len(self._feats) > LIMITE_TABELA:
                PEDIDOS['recusadas_p4'] += 1
                raise Exception('User memory limit exceeded.')
            nb = len(self._sel) - 1
            return {'groups': [{'pid': p['pid'], 'mean': [1.5] * nb} for p in self._feats]}
        raise RuntimeError('sem resposta neste teste')


PEDIDOS['recusadas_p4'] = 0
raiz = S()
ee = types.ModuleType('ee')
for a in ('Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Filter', 'Reducer', 'Projection', 'Dictionary',
          'Date', 'Algorithms', 'List', 'Number', 'String', 'Geometry', 'Kernel', 'Terrain'):
    setattr(ee, a, getattr(raiz, a))
ee.ImageCollection = IC
ee.Initialize = lambda *a, **k: None
ee.Authenticate = lambda *a, **k: None
gravou = []
DATAS = {'SAB': '2026-09-13T10:00:00Z', 'ERA5': '2026-10-02T00:00:00Z'}
ee.data = types.SimpleNamespace(deleteAsset=lambda *a: gravou.append('delete'),
                                startProcessing=lambda *a: gravou.append('export'),
                                getAsset=lambda c: {'updateTime': DATAS['ERA5'] if 'ERA5' in c else DATAS['SAB']})
ee.batch = types.SimpleNamespace(Task=type('Task', (), {'start': lambda self: gravou.append('start')}))
req = types.ModuleType('requests')
req.get = lambda *a, **k: (_ for _ in ()).throw(ConnectionError('sem rede no teste'))
sys.modules['ee'], sys.modules['requests'] = ee, req

ns = {'__name__': 'fumaca_k17'}
exec(compile(SRC, 'K17', 'exec'), ns)
tmp = tempfile.mkdtemp()
ns['PASTA'] = os.path.join(tmp, 'validacao_K17_fumaca')
ns['LOG'] = os.path.join(ns['PASTA'], 'LOG_K17.txt')
_sleep = time.sleep
time.sleep = lambda *a: None
ns['principal']()
time.sleep = _sleep

log = open(ns['LOG'], encoding='utf-8').read()
st = {a['parte']: a['status'] for a in ns['ACHADOS']}
print('\n[resultado]')
confere('amostra fixa: 1000 pixels' in log, 'pixels sorteados uma vez e guardados no Colab')
confere(st.get('P9') == 'OK', f'P9: máscara = o que o 01b gravou ({st.get("P9")})')
confere(IC.capturas.count('mean') == 4 and IC.capturas.count('reduce') == 4,
        f'P4: o código original O2 e O4 chamou 2 médias e 2 desvios cada ({IC.capturas})')
confere(PEDIDOS['recusadas_p4'] > 0 and 'lote reduzido para 20' in log, 'P4: tabela pesada vira lote menor')
confere(os.path.exists(os.path.join(ns['PASTA'], 'P2_proveniencia_datas.csv')), 'P2: datas de atualização gravadas')
confere(PEDIDOS['recusadas'] > 0 and 'lote reduzido para 250' in log, f'recusa por memória vira lote menor '
        f'({PEDIDOS["recusadas"]} recusas)')
confere(max(PEDIDOS['amostra']) <= LIMITE, 'nenhuma amostra aceita acima do limite')
confere(st.get('P2') == 'OK', f'P2 terminou: {st.get("P2")}')
confere(st.get('P3') == 'INFO', f'P3 terminou: {st.get("P3")}')
confere(st.get('P4') == 'OK', f'P4 terminou: {st.get("P4")}')
for d in ns['DIAS_P2']:
    arq = os.path.join(ns['PASTA'], f'P2_P3_amostra_{d}.csv')
    df = pd.read_csv(arq, sep=';', decimal=',') if os.path.exists(arq) else pd.DataFrame()
    ok = len(df) == 1000 and all(df[f'{p}pr_mm'].notna().all() for p in ('s_', 'a_', 'b_', 'c_', 'l_'))
    confere(ok, f'{d}: 1000 pixels nas 5 versões')
t2 = pd.read_csv(os.path.join(ns['PASTA'], 'P2_V10_recalculada_x_gravado.csv'), sep=';', decimal=',')
confere(len(t2) == 16 * 8 and (t2['n'] == 1000).all(), 'P2: 16 bandas × 8 dias, 1000 pixels cada')
confere(st.get('P1') == 'NÃO EXECUTADO' and st.get('P5') == 'NÃO EXECUTADO', 'partes sem resposta no teste não param as outras')
confere(not gravou, 'nada gravado')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'FUMAÇA K17 OK'))
sys.exit(1 if falhas else 0)
