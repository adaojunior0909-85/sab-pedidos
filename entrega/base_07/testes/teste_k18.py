# Teste offline da K18: funções de resumo e a execução completa com um Earth Engine falso (que responde com números
# inventados, mas no formato real). Confere a trava de somente leitura, as duas partes e o zip. Rodar:
#   python3 testes/teste_k18.py
import os
import sys
import tempfile
import time
import types

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(AQUI, '..', 'validacoes', 'K18_auditoria_era5_e_pixels_b.py'), encoding='utf-8').read()
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


ns = {'__name__': 'teste_k18'}
exec(compile(SRC, 'K18', 'exec'), ns)

print('[Q1: início da mudança do ERA5]')


def q1(mudados, tsolo=1.0, controle=1.0):
    linhas = []
    for d in ns['DIAS_Q1']:
        f = controle if d < '2014' else (0.3 if d in mudados else 1.0)
        linhas.append({'data': d, 'frac_tsolo': tsolo, 'frac_etr': f, 'frac_tr': f, 'dif_etr': 0.0,
                       'absdif_etr': 0.0 if f == 1.0 else 0.01, 'absdif_tr': 0.0})
    return pd.DataFrame(linhas)


mud = [d for d in ns['DIAS_Q1'] if d >= '2019-03-01']
fiel, txt, tab = ns['resumo_q1'](q1(mud))
confere(fiel and 'primeiro dia mudado: 2019-03-15' in txt and 'último igual antes dele: 2019-02-15' in txt
        and 'contínua' in txt, f'início achado ({txt})')
confere(int(tab.set_index('ano').loc['2019', 'dias_mudados']) == 10, 'contagem por ano')
fiel, txt, _ = ns['resumo_q1'](q1(mud + [], tsolo=0.5))
confere(not fiel and 'NÃO reproduziu' in txt, 'temperatura do solo diferente: conta não é fiel')
fiel, txt, _ = ns['resumo_q1'](q1(mud, controle=0.8))
confere(not fiel, 'dia de controle (até 2013) diferente: conta não é fiel')
fiel, txt, _ = ns['resumo_q1'](q1(['2016-05-15', '2020-01-15']))
confere(fiel and 'não contínua' in txt, 'mudança salteada acusada')
confere(ns['resumo_q1'](q1([]))[1].startswith('nenhum dia'), 'nada mudado')

print('[Q2: tamanho da correção dos pixels B]')
linhas = []
for a, m in ns['MESES_Q2']:
    r = {'ano': a, 'mes': m, 'classe': 'B', 'n_dias': 31, 'n_dias_sab': 31, 'n_dias_br': 31}
    for b in ns['BANDAS_Q2']:
        r.update({f'{b}_sab': 110.0, f'{b}_br': 100.0, f'{b}_abs_mes': 15.0, f'{b}_abs_dia': 2.0})
    linhas.append(r)
for a, m in ns['MESES_CONTROLE_A']:
    r = {'ano': a, 'mes': m, 'classe': 'A', 'n_dias': 31, 'n_dias_sab': 31, 'n_dias_br': 31}
    for b in ns['BANDAS_Q2']:
        r.update({f'{b}_sab': 100.0, f'{b}_br': 100.0, f'{b}_abs_mes': 0.0, f'{b}_abs_dia': 0.0})
    linhas.append(r)
df2 = pd.DataFrame(linhas)
ok, tab2, txt2 = ns['resumo_q2'](df2)
confere(ok and '+10.0%' in txt2 and 'gravado = BR-DWGD' in txt2, f'diferença de 10% medida ({txt2[:90]}...)')
confere(len(tab2) == 7 and tab2.set_index('variavel').loc['pr_mm', 'agregado_mes'] == 'total', '7 variáveis; chuva em total')
df3 = df2.copy()
df3.loc[df3['classe'] == 'A', 'tmax_C_abs_dia'] = 0.5
confere(ns['resumo_q2'](df3)[0] is False, 'controle A diferente: decodificação a conferir')


# ---------------------------------------------------------------- execução completa com Earth Engine falso
class S:
    def __init__(self, nome='ee', props=None, feats=None):
        self._n, self._props, self._feats = nome, props, feats

    def __getattr__(self, a):
        if a.startswith('__'):
            raise AttributeError(a)
        if a == 'getInfo':
            return self._responder
        if a == 'start':
            raise AssertionError('start')
        return S(f'{self._n}.{a}', self._props, self._feats)

    def __call__(self, *a, **k):
        novo = S(self._n + '()', dict(self._props or {}), self._feats)
        if self._n.endswith('.set') and a:
            novo._props.update(a[0] if isinstance(a[0], dict) else {a[0]: a[1]})
        if self._n.endswith('FeatureCollection') and a and isinstance(a[0], list):
            novo._feats = [x._props for x in a[0]]
        return novo

    def __getitem__(self, k):
        return S(self._n + '[]')

    def _op(self, *a):
        return S(self._n + '·')
    __add__ = __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = __truediv__ = __rtruediv__ = __neg__ = _op

    def _responder(self):
        if self._n.endswith('aggregate_max()'):
            return 1767139200000
        if self._feats is not None:
            out = []
            for p in self._feats:
                if 'data' in p:
                    f = 1.0 if p['data'] < '2019-03-01' else 0.4
                    q = {'data': p['data'], 'frac_tsolo': 1.0, 'frac_etr': f, 'frac_tr': f, 'dif_etr': 0.0,
                         'absdif_etr': 0.0 if f == 1 else 0.01, 'absdif_tr': 0.0}
                else:
                    cl = p['classe']
                    q = {'ano': p['ano'], 'mes': p['mes'], 'classe': cl, 'n_dias': 31, 'n_dias_sab': 31, 'n_dias_br': 31}
                    for b in ns['BANDAS_Q2']:
                        q.update({f'{b}_sab': 120.0 if cl == 'B' else 100.0, f'{b}_br': 100.0,
                                  f'{b}_abs_mes': 20.0 if cl == 'B' else 0.0, f'{b}_abs_dia': 3.0 if cl == 'B' else 0.0})
                out.append({'properties': q})
            return {'features': out}
        raise RuntimeError('sem resposta')


raiz = S()
ee = types.ModuleType('ee')
for a in ('Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Filter', 'Reducer', 'Date', 'Geometry', 'Join'):
    setattr(ee, a, getattr(raiz, a))
ee.Initialize = lambda *a, **k: None
gravou = []
ee.data = types.SimpleNamespace(deleteAsset=lambda *a: gravou.append('d'), startProcessing=lambda *a: gravou.append('e'))
ee.batch = types.SimpleNamespace(Task=type('Task', (), {'start': lambda self: gravou.append('s')}))
sys.modules['ee'] = ee
tmp = tempfile.mkdtemp()
ns['PASTA'] = os.path.join(tmp, 'validacao_K18_teste')
ns['LOG'] = os.path.join(ns['PASTA'], 'LOG_K18.txt')
_s = time.sleep
time.sleep = lambda *a: None
ns['principal']()
time.sleep = _s
print('\n[execução completa]')
log = open(ns['LOG'], encoding='utf-8').read()
confere('ℹ️ Q1: primeiro dia mudado: 2019-03-15' in log, 'Q1 achou o início simulado (2019-03-15)')
confere('ℹ️ Q2:' in log and '+20.0%' in log, 'Q2 mediu a diferença simulada dos pixels B (+20%)')
confere(os.path.exists(ns['PASTA'] + '.zip'), 'zip gerado')
for f in ('Q1_por_dia.csv', 'Q1_por_ano.csv', 'Q2_por_mes.csv', 'Q2_por_variavel.csv', 'Q2_pixels_B_por_decada.csv',
          'K18_RESUMO.csv'):
    confere(os.path.exists(os.path.join(ns['PASTA'], f)), f'{f} gerado')
d1 = pd.read_csv(os.path.join(ns['PASTA'], 'Q1_por_dia.csv'), sep=';', decimal=',')
d2 = pd.read_csv(os.path.join(ns['PASTA'], 'Q2_por_mes.csv'), sep=';', decimal=',')
confere(len(d1) == len(ns['DIAS_Q1']) == 150, f'Q1: {len(d1)} dias (6 de controle + 144 meses)')
confere(len(d2) == 133, f'Q2: {len(d2)} meses (130 nos pixels B + 3 de controle nos A)')
for n in ('deleteAsset', 'startProcessing'):
    try:
        getattr(ee.data, n)()
        confere(False, f'trava: {n} liberado')
    except RuntimeError:
        confere(True, f'trava: {n} bloqueado')
confere(not gravou, 'nada gravado')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
