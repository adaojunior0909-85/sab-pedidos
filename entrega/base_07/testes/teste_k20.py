# Teste offline da K20 (sem Earth Engine): regras V1 a V5 com casos conhecidos e a execução completa com um Earth
# Engine falso, que também roda a rotina sab_pedido.py 2026.11.03 (corrigir_pixels_b, area_tem_pixels_bc, colecao).
# Rodar: python3 testes/teste_k20.py
import os
import re
import sys
import tempfile
import time
import types

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(AQUI, '..', 'validacoes', 'K20_validacao_correcao_pixels_b.py'), encoding='utf-8').read()
ns = {'__name__': 'teste_k20'}
exec(compile(SRC, 'K20', 'exec'), ns)
ORDEM, NUCLEO = ns['ORDEM'], ns['NUCLEO']
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


def linha(classe, data, **mud):
    r = {'classe': classe, 'data': data, 'rso': 30.0}
    for b in ORDEM:
        r[f's_{b}'] = 10.0
        r[f'c_{b}'] = 10.0
    for b in NUCLEO:
        r[f'b_{b}'] = 10.0
    r['s_et_real'] = r['c_et_real'] = 3.0
    r['s_transpiracao_mm'] = r['c_transpiracao_mm'] = 2.0
    r.update(mud)
    return r


print('[marcador de vazio (v2)]')
d = ns['limpar_ausentes'](pd.DataFrame({'classe': [3, 1], 'data': ['2000-01-15', '2026-01-15'], 'b_pr_mm': [-99999.0, 5.0],
                                        'c_rs': [20.0, -99999.0], 'pid': [1, 2]}))
confere(pd.isna(d.loc[0, 'b_pr_mm']) and d.loc[1, 'b_pr_mm'] == 5.0 and pd.isna(d.loc[1, 'c_rs']) and d.loc[0, 'pid'] == 1,
        'AUSENTE vira vazio só nas bandas (pixel C sem BR-DWGD continua na tabela)')
confere(".unmask(AUSENTE)" in SRC, 'a imagem amostrada vai com o marcador no lugar do vazio')
print('[regras V1 a V5]')
bom = [linha(2, '2000-01-15', s_pr_mm=4.0, c_pr_mm=10.0), linha(1, '2000-01-15'), linha(3, '2000-01-15', s_rs=35.0, c_rs=30.0),
       linha(1, '2026-01-15'), linha(2, '2026-01-15')]
res, med = ns['avaliar'](pd.DataFrame(bom))
confere(all(res[v][0] == 'OK' for v in ('V1', 'V2', 'V3', 'V4', 'V5')), f'correção certa: tudo OK ({ {k: v[0] for k, v in res.items()} })')
confere('1 com a radiação limitada' in res['V3'][1], 'V3 conta a radiação limitada no pixel C')
confere(abs(med.set_index('banda').loc['pr_mm', 'mudanca_media'] - 6.0) < 1e-9, 'mudança da chuva no pixel B medida (6 mm)')
r, _ = ns['avaliar'](pd.DataFrame([linha(2, '2000-01-15', c_pr_mm=7.0), linha(1, '2000-01-15'), linha(3, '2000-01-15'),
                                   linha(1, '2026-01-15')]))
confere(r['V1'][0] == 'FALHA' and 'pr_mm' in r['V1'][1], 'B diferente do BR-DWGD: V1 FALHA')
r, _ = ns['avaliar'](pd.DataFrame(bom + [linha(1, '2001-01-15', c_tmax_C=11.0)]))
confere(r['V2'][0] == 'FALHA' and 'tmax_C' in r['V2'][1], 'pixel A mudou: V2 FALHA')
r, _ = ns['avaliar'](pd.DataFrame(bom + [linha(3, '2001-01-15', s_rs=40.0, c_rs=40.0)]))
confere(r['V3'][0] == 'FALHA' and '1 acima' in r['V3'][1], 'pixel C acima do céu claro: V3 FALHA')
r, _ = ns['avaliar'](pd.DataFrame(bom + [linha(2, '2001-01-15', c_et_real=12.0)]))
confere(r['V4'][0] == 'FALHA', 'B com ET real > ETo: V4 FALHA')
r, _ = ns['avaliar'](pd.DataFrame(bom + [linha(1, '2026-03-15', c_u2=9.0)]))
confere(r['V5'][0] == 'FALHA', '2026 mudou: V5 FALHA')
confere(ns['veredito']([{'parte': v, 'status': 'OK'} for v in ('V1', 'V2', 'V3', 'V4', 'V5', 'V6')])[0], 'tudo OK: aprovada')
confere(not ns['veredito']([{'parte': v, 'status': 'OK'} for v in ('V1', 'V2', 'V3', 'V4', 'V5')])[0], 'sem V6: não aprova')


# ---------------------------------------------------------------- Earth Engine falso
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
        if self._n.endswith('Feature') and len(a) > 1 and isinstance(a[1], dict):
            novo._props = dict(a[1])
        if self._n.endswith('FeatureCollection') and a and isinstance(a[0], list):
            novo._feats = [x._props for x in a[0] if isinstance(x, S)]
        if self._n.endswith('.sampleRegions'):
            novo._feats = k['collection']._feats
        return novo

    def __getitem__(self, k):
        return S(self._n + '[]')

    def _op(self, *a):
        return S(self._n + '·')
    __add__ = __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = __truediv__ = __rtruediv__ = __neg__ = __pow__ = _op

    def _responder(self):
        n = self._n
        if n.endswith('.reduceRegion().get()'):                 # V6: histograma de classes do polígono A6
            return {'1': 3, '2': 6}
        if '.stratifiedSample()' in n:
            return {'features': [{'properties': {'classe': [1, 2, 3][i % 3]},
                                  'geometry': {'coordinates': [-51.2 - 0.1 * i, -31.0]}} for i in range(9)]}
        if n.endswith('.sampleRegions()'):
            out = []
            for p in self._feats:
                q = dict(p)
                for b in ORDEM:
                    q[f's_{b}'] = q[f'c_{b}'] = 10.0
                q['s_et_real'] = q['c_et_real'] = 3.0
                q['s_transpiracao_mm'] = q['c_transpiracao_mm'] = 2.0
                for b in NUCLEO:
                    q[f'b_{b}'] = 10.0
                q['rso'] = 30.0
                out.append({'properties': q})
            return {'features': out}
        raise RuntimeError(f'sem resposta: {n[-60:]}')


raiz = S()
ee = types.ModuleType('ee')
for a in ('Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Filter', 'Reducer', 'Projection', 'Date', 'Geometry',
          'Number', 'List', 'Dictionary', 'Algorithms', 'String'):
    setattr(ee, a, getattr(raiz, a))
ee.Initialize = lambda *a, **k: None
gravou = []
ee.data = types.SimpleNamespace(deleteAsset=lambda *a: gravou.append('d'), startProcessing=lambda *a: gravou.append('e'))
ee.batch = types.SimpleNamespace(Task=type('Task', (), {'start': lambda self: gravou.append('s')}))
sys.modules['ee'] = ee

print('[execução completa com Earth Engine falso]')
tmp = tempfile.mkdtemp()
ns['PASTA'] = os.path.join(tmp, 'validacao_K20_teste')
ns['LOG'] = os.path.join(ns['PASTA'], 'LOG_K20.txt')
_s = time.sleep
time.sleep = lambda *a: None
ns['principal']()
time.sleep = _s
log = open(ns['LOG'], encoding='utf-8').read()
st = {a['parte']: a['status'] for a in ns['ACHADOS']}
print('   ', st)
VERSAO_ATUAL = re.search(r"VERSAO_ROTINA = '([^']+)'", ns['ROTINA_SRC']).group(1)   # a montar_k20 embute a rotina atual
confere(f'rotina {VERSAO_ATUAL} carregada' in log, f'rotina {VERSAO_ATUAL} embutida e carregada')
confere(all(st.get(v) == 'OK' for v in ('V1', 'V2', 'V3', 'V4', 'V5', 'V6')), 'V1 a V6 calculadas e OK nos dados simulados')
confere('não calculado' not in log, 'os 14 dias montados sem erro (corrigir_pixels_b, area_tem_pixels_bc, colecao)')
confere('CORREÇÃO APROVADA' in log and os.path.exists(ns['PASTA'] + '.zip'), 'veredito e zip')
for n_ in ('deleteAsset', 'startProcessing'):
    try:
        getattr(ee.data, n_)()
        confere(False, f'trava: {n_} liberado')
    except RuntimeError:
        confere(True, f'trava: {n_} bloqueado')
confere(not gravou, 'nada gravado')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
