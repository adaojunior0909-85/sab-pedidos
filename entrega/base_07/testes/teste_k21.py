# Teste offline da K21 (validação fora da amostra do motor V1.6): funções puras, a avaliação com dados sintéticos de
# resposta conhecida e a execução completa com um Earth Engine falso. Rodar: python3 testes/teste_k21.py
import ast
import math
import os
import sys
import tempfile
import time
import types
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, '..')
SRC = open(os.path.join(RAIZ, 'validacoes', 'K21_validacao_v16_fora_da_amostra.py'), encoding='utf-8').read()
MOTOR = open(os.path.join(RAIZ, '05a_motor_sab_v1_6_SIMULACAO.py'), encoding='utf-8').read()
M09 = open(os.path.join(RAIZ, '09a_matriz_eqm_SIMULACAO.py'), encoding='utf-8').read()
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


ns = {'__name__': 'teste_k21'}
exec(compile(SRC, 'K21', 'exec'), ns)
BRT = timezone(timedelta(hours=-3))

print('[janelas do motor]')
mj = ns['minutos_ate_janela']
confere(all(mj(datetime(2026, 11, 5, h, m, tzinfo=BRT)) == 0 for h, m in ((22, 50), (23, 30), (0, 10), (0, 59))),
        'v4: dentro da janela única (22h50 à 01h00): 0')
confere(mj(datetime(2026, 11, 5, 21, 20, tzinfo=BRT)) == 90 and mj(datetime(2026, 11, 5, 16, 33, tzinfo=BRT)) == 377
        and mj(datetime(2026, 11, 5, 1, 0, tzinfo=BRT)) == 1310 and mj(datetime(2026, 11, 5, 6, 30, tzinfo=BRT)) == 980,
        'v4: 21h20 = 90 min até 22h50; 16h33 = 377 min; 01h00 já fora; manhã e tarde livres')
confere(mj(datetime(2026, 11, 5, 21, 21, tzinfo=BRT)) < ns['DURACAO_ESTIMADA_MIN'] <= mj(datetime(2026, 11, 5, 21, 20, tzinfo=BRT)),
        'v4: começa até as 21h20; às 21h21 recusa')

print('[EQM igual ao do motor]')


class Img:
    def __init__(self, v): self.v = np.asarray(v, float)
    def _o(self, x): return x.v if isinstance(x, Img) else x
    def add(self, x): return Img(self.v + self._o(x))
    def subtract(self, x): return Img(self.v - self._o(x))
    def multiply(self, x): return Img(self.v * self._o(x))
    def divide(self, x): return Img(self.v / self._o(x))
    def max(self, x): return Img(np.maximum(self.v, self._o(x)))
    def gte(self, x): return Img((self.v >= self._o(x)).astype(float))
    def gt(self, x): return Img((self.v > self._o(x)).astype(float))
    def where(self, c, x): return Img(np.where(self._o(c) == 1, self._o(x) * np.ones_like(self.v), self.v))


arv = ast.parse(MOTOR)
fn = [n for n in arv.body if isinstance(n, ast.FunctionDef) and n.name == 'aplicar_eqm'][0]
nm = {}
exec(compile(ast.Module(body=[fn], type_ignores=[]), 'motor', 'exec'), nm)
rng = np.random.default_rng(3)
iguais = 0
for caso in range(200):
    qm = np.sort(rng.gamma(2, 1.2, 21))
    qo = np.sort(rng.gamma(2, 1.0, 21))
    if caso % 4 == 0:
        qm[:5] = qm[0]
    x = rng.gamma(2, 1.5, 40)
    a = ns['eqm'](x, qm, qo)
    b = nm['aplicar_eqm'](Img(x), [Img(np.full(40, q)) for q in qm], [Img(np.full(40, q)) for q in qo]).v
    iguais += bool(np.allclose(a, b, atol=1e-9))
confere(iguais == 200, f'eqm da K21 = aplicar_eqm do motor V1.6 em 200 casos ({iguais})')

print('[mesmo preparo de dados do 09 e do motor]')


def corpo(fonte, nome):
    t = fonte.split(f'def {nome}(img):', 1)[1]
    linhas = []
    for l in t.split('\n')[1:]:
        if l.strip() and not l.startswith(' '):
            break
        if l.strip().startswith('def '):
            break
        linhas.append(l.strip())
    return '\n'.join(x for x in linhas if x)


for nome in ('era_prep', 'br_prep'):
    confere(corpo(SRC, nome) == corpo(M09, nome), f'{nome} igual na K21 e no 09')
for trecho in ("'100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))'",
               ".multiply(0.748).resample('bilinear')", "multiply(0.39370079).add(-0.393701)",
               "multiply(0.05905512).add(-0.059055)"):
    confere(trecho in MOTOR and trecho in M09 and trecho in SRC, f'mesma conversão no motor, no 09 e na K21: {trecho[:40]}')

print('[ETo FAO-56: exemplo 18 da FAO (Bangkok, abril) e o mesmo código do motor]')
# FAO-56, exemplo 17/18: Tmax 34,8, Tmin 25,6, ea 2,85 kPa, u2 2,0, Rs 22,65 MJ, lat 13°44'N, z 2 m, 15 de abril
es_m = (ns['es'](34.8) + ns['es'](25.6)) / 2
rh = 100 * 2.85 / es_m
eto = float(ns['eto_pm'](34.8, 25.6, rh, 2.0, 22.65, 13 + 44 / 60, 105, 2)[0] if np.ndim(ns['eto_pm'](34.8, 25.6, rh, 2.0, 22.65, 13 + 44 / 60, 105, 2)) else ns['eto_pm'](34.8, 25.6, rh, 2.0, 22.65, 13 + 44 / 60, 105, 2))
confere(abs(eto - 5.72) < 0.15, f'ETo do exemplo 18 da FAO-56: {eto:.2f} mm (FAO: 5,72; o motor usa Rso com 2e-5 z)')
ra, rso = ns['ra_rso'](-20.0, 246, 0)
confere(abs(float(ra) - 32.2) < 0.2 and abs(float(rso) - 0.75 * float(ra)) < 1e-9,
        f'Ra em 20°S em 3 de setembro = 32,2 MJ (FAO-56, exemplo 8): {float(ra):.2f}; Rso = 0,75 Ra no nível do mar')

print('[v3: quantis do treino calculados em Python]')
rng0 = np.random.default_rng(1)
dd = pd.DataFrame({'pid': 0, 'data': [f'1990-01-{d:02d}' for d in range(1, 31)] * 3,
                   'era_rh': rng0.uniform(30, 90, 90), 'br_rh': rng0.uniform(40, 100, 90), 'era_u2': rng0.gamma(2, 1, 90),
                   'br_u2': rng0.gamma(2, 0.8, 90), 'br_pr': rng0.gamma(0.5, 10, 90)})
qt = ns['quantis_treino'](dd)
confere(len(qt) == 1 and abs(qt['RH_br_p050'][0] - np.median(dd['br_rh'])) < 1e-9 and
        abs(qt['u2_era_p100'][0] - dd['era_u2'].max()) < 1e-9 and abs(qt['pr_max_br'][0] - dd['br_pr'].max()) < 1e-9,
        'mediana, máximo e maior dia de chuva certos; mesmas bandas da matriz do 09')
confere(ns['quantis_treino'](dd.head(50))['RH_era_p050'].isna().all(), 'menos de 60 dias no pixel-mês: sem quantis (fica a V1.5)')
print('[regras de decisão]')
a = {'mae': 8.0, 'razao_desvio': 1.24, 'vies': -0.5}
confere(ns['decidir_u'](a, {'mae': 6.2, 'razao_desvio': 1.03, 'vies': 0.3}, 'RH')[0], 'U: melhora de 22% aprovada')
confere(not ns['decidir_u'](a, {'mae': 7.9, 'razao_desvio': 1.03, 'vies': 0.3}, 'RH')[0], 'U: melhora de 1% não basta')
confere(not ns['decidir_u'](a, {'mae': 6.0, 'razao_desvio': 1.40, 'vies': 0.3}, 'RH')[0], 'U: desvio pior reprova')
confere(not ns['decidir_u'](a, {'mae': 6.0, 'razao_desvio': 1.0, 'vies': 1.5}, 'RH')[0], 'U: viés maior que 1 % reprova')
confere(ns['decidir_r'](3.10, 3.05, 0) and not ns['decidir_r'](3.10, 3.20, 0) and not ns['decidir_r'](3.1, 3.0, 2),
        'R: MAE não piora e nada acima de Rso')
confere(ns['decidir_c'](0.0005, 20.0, 20.1) and not ns['decidir_c'](0.002, 20, 20) and not ns['decidir_c'](0.0, 20, 20.5),
        'C: até 0,1% dos dias e erro mensal até +1%')
tab = ns['latencia_gfs']([(1762300800000 + k * 86400000, 209, (1762300800000 + k * 86400000 + (6 + 0.1 * k) * 3.6e6) * 1000)
                         for k in range(10)] + [(1762300800000 - 86400000, 150, 1762300800000 * 1000)])
ok, p90, segura = ns['decidir_g'](tab)
confere(ok and 6.5 < p90 < 7.0 and segura == 8 and int(tab['completa'].sum()) == 10,
        f'G: p90 {p90:.2f} h, aprovado para 09h UTC, cron seguro às {segura}h UTC; rodada incompleta fora')
tab2 = ns['latencia_gfs']([(1762300800000 + k * 86400000, 209, (1762300800000 + k * 86400000 + 10.5 * 3.6e6) * 1000)
                          for k in range(10)])
confere(not ns['decidir_g'](tab2)[0] and ns['decidir_g'](tab2)[2] == 11, 'G: chegando às 10h30 UTC reprova e sugere 11h')

print('[avaliação com dados sintéticos: resposta conhecida]')
rng = np.random.default_rng(11)
N, ANOS = 6, range(2016, 2026)
linhas, treino, medias = [], [], []
pontos = pd.DataFrame({'pid': range(N), 'lat': np.linspace(-5, -30, N), 'z': np.linspace(10, 900, N)})
for pid in range(N):
    for mes in range(1, 13):
        # observado: UR ~ N(75, 8); ERA5: viés -6 e desvio 1,5x (o que a K19b viu); vento: obs gama, ERA5 1,7x a anomalia
        obs_rh = np.clip(rng.normal(75, 8, 3000), 5, 100)
        era_rh = np.clip(69 + (obs_rh - 75) * 1.5 + rng.normal(0, 2, 3000), 1, 100)
        obs_u2 = rng.gamma(4, 0.5, 3000)
        era_u2 = np.maximum(2.0 + (obs_u2 - 2.0) * 1.7, 0.05)
        q = np.array(ns['NIVEIS_EQM']) / 100
        tr = {'pid': pid, 'mes': mes, 'pr_max_br': 120.0}
        for p, a_, b_ in zip(ns['NIVEIS_EQM'], np.quantile(era_rh, q), np.quantile(obs_rh, q)):
            tr[f'RH_era_p{p:03d}'], tr[f'RH_br_p{p:03d}'] = a_, b_
        for p, a_, b_ in zip(ns['NIVEIS_EQM'], np.quantile(era_u2, q), np.quantile(obs_u2, q)):
            tr[f'u2_era_p{p:03d}'], tr[f'u2_br_p{p:03d}'] = a_, b_
        treino.append(tr)
        medias.append({'pid': pid, 'mes': mes, 'pr_m_br': 4.0, 'pr_m_era': 2.0, 'Tmax_m_br': 30.0, 'Tmax_m_era': 29.0,
                       'Tmin_m_br': 19.0, 'Tmin_m_era': 18.0, 'RH_m_br': 75.0, 'RH_m_era': 69.0, 'Rs_m_br': 19.0,
                       'Rs_m_era': 17.0, 'u2_m_br': 2.0, 'u2_m_era': 2.0})
    for ano in ANOS:
        for d in pd.date_range(f'{ano}-01-01', f'{ano}-12-31', freq='3D'):
            obs_rh = float(np.clip(rng.normal(75, 8), 5, 100))
            obs_u2 = float(rng.gamma(4, 0.5))
            br_pr = float(rng.gamma(0.5, 8))
            linhas.append({'pid': pid, 'data': d.strftime('%Y-%m-%d'),
                           'era_pr': br_pr / 2 + (300 if (pid == 0 and d.strftime('%m-%d') == '03-01' and ano == 2020) else 0),
                           'era_tmax': 29.0, 'era_tmin': 18.0,
                           'era_rh': float(np.clip(69 + (obs_rh - 75) * 1.5 + rng.normal(0, 2), 1, 100)),
                           'era_u2': max(2.0 + (obs_u2 - 2.0) * 1.7, 0.05), 'era_rs': 26.0 if d.month == 6 else 17.0,
                           'br_pr': br_pr, 'br_tmax': 30.0, 'br_tmin': 19.0, 'br_rh': obs_rh, 'br_u2': obs_u2,
                           'br_rs': 19.0, 'br_et': 4.0})
tmp = tempfile.mkdtemp()
ns['PASTA'] = os.path.join(tmp, 'validacao_K21_sintetico')
ns['LOG'] = os.path.join(ns['PASTA'], 'LOG_K21.txt')
ns['RESULTADOS'].clear()
ns['avaliar'](pd.DataFrame(linhas), pd.DataFrame(treino), pd.DataFrame(medias), pontos)
res = {(r['item'], r['titulo'].split(':')[0]): r for r in ns['RESULTADOS']}
confere(res[('U', 'UR')]['status'] == 'APROVADO', 'UR com desvio 1,5x: o EQM é aprovado (' + res[('U', 'UR')]['texto'][:70] + ')')
rv = [r for r in ns['RESULTADOS'] if r['item'] == 'V'][0]
confere(rv['status'] == 'INFO' and 'passaria' in rv['titulo'], 'v4: vento com desvio 1,7x: o EQM passaria, mas é só informação')
confere(not [r for r in ns['RESULTADOS'] if r['item'] == 'U' and r['titulo'].startswith('vento')], 'v4: o vento não é mais item U')
rt = pd.read_csv(os.path.join(ns['PASTA'], 'K21_metricas_teste.csv'), sep=';', decimal=',')
v15 = rt[(rt.variavel == 'vento') & (rt.versao == 'V1.5')]
confere(len(rt) == 9 and not (rt.versao == 'V1.6').loc[rt.variavel == 'vento'].any() and len(v15) == 1,
        'v4: 9 linhas; o vento da V1.6 é o da V1.5 (só aparece a V1.5 e o EQM como informação)')
re_ = [r for r in ns['RESULTADOS'] if r['item'] == 'E'][0]
confere('vento da V1.5' in re_['titulo'] and 'com o EQM também no vento seria' in re_['texto'], 'v4: E avalia a V1.6 revista')
confere(res[('R', 'radiação limitada ao céu claro')]['status'] == 'APROVADO' and '-> 0' in
        res[('R', 'radiação limitada ao céu claro')]['texto'], 'R: radiação de junho acima de Rso cortada, MAE menor')
rc = [r for r in ns['RESULTADOS'] if r['item'] == 'C'][0]
confere('o teto pegou 1 pixel-dias' in rc['texto'] and rc['status'] == 'APROVADO',
        'C: o dia inflado artificialmente (300 mm x2) é o único pego pelo teto: ' + rc['texto'][:60])
confere([r for r in ns['RESULTADOS'] if r['item'] == 'E'][0]['status'] in ('APROVADO', 'REPROVADO'), 'E avaliado')
for f in ('K21_metricas_teste.csv', 'K21_metricas_chuva.csv', 'K21_C_dias_com_teto.csv'):
    confere(os.path.exists(os.path.join(ns['PASTA'], f)), f'{f} gerado')


# ---------------------------------------------------------------- execução completa com Earth Engine falso
class S:
    contagem = {}

    def __init__(self, nome='ee'):
        self._n = nome

    def __getattr__(self, a):
        if a.startswith('__'):
            raise AttributeError(a)
        if a == 'getInfo':
            return self._responder
        if a == 'start':
            raise AssertionError('start')
        return S(f'{self._n}.{a}')

    def __call__(self, *a, **k):
        if self._n.endswith('.copyProperties'):
            return Elem()                        # [v3a] como no Earth Engine: copyProperties devolve um Element
        return S(self._n + '()')

    def __getitem__(self, k):
        return S(self._n + '[]')

    def _responder(self):
        n = self._n
        if n.endswith('stratifiedSample()'):
            return {'features': [{'geometry': {'coordinates': [-60 + 0.1 * k + 0.05, -10 - 0.1 * k - 0.05]}}
                                 for k in range(ns['N_PONTOS'])]}
        if n.endswith('sampleRegions()'):
            S.contagem['sr'] = S.contagem.get('sr', 0) + 1
            c = S.contagem['sr']
            if c == 1:
                return {'features': [{'properties': {'pid': k, 'z': 300}} for k in range(ns['N_PONTOS'])]}
            if c == 2:
                raise Exception('User memory limit exceeded.')   # 1º pedido da matriz recusado: divide os pontos ao meio
            if c <= 0:                                       # [v3] o treino não usa mais sampleRegions
                feats = []
                for k in range(ns['N_PONTOS']):
                    p = {'pid': k, 'pr_max_br': 150.0}
                    for v, (a, b) in (('RH', (40, 98)), ('u2', (0.3, 5))):
                        for i, q in enumerate(ns['NIVEIS_EQM']):
                            p[f'{v}_era_p{q:03d}'] = a + (b - a) * i / 20
                            p[f'{v}_br_p{q:03d}'] = a + 3 + (b - a) * 0.8 * i / 20
                    feats.append({'properties': p})
                return {'features': feats}
            props = []
            for k in range(ns['N_PONTOS']):
                p = {'pid': k}
                for m in range(1, 13):
                    for b, v in (('pr', 3.0), ('Tmax', 30.0), ('Tmin', 19.0), ('RH', 75.0), ('Rs', 18.0), ('u2', 2.0)):
                        p[f'{b}_m_br__{m}'] = v
                        p[f'{b}_m_era__{m}'] = v * 0.95
                props.append({'properties': p})
            return {'features': props}
        if n.endswith('getRegion()'):
            S.contagem['gr'] = S.contagem.get('gr', 0) + 1
            k = S.contagem['gr'] - 1
            ano, mes = 1986 + k // 12, k % 12 + 1
            cab = ['id', 'longitude', 'latitude', 'time', 'era_pr', 'era_tmax', 'era_tmin', 'era_rh', 'era_u2', 'era_rs',
                   'br_pr', 'br_tmax', 'br_tmin', 'br_rh', 'br_u2', 'br_rs', 'br_et']
            linhas = [cab]
            r = np.random.default_rng(k)
            for dia in range(1, 29, 3):                      # 10 dias por mês: 300 no treino por pixel-mês
                t = int(datetime(ano, mes, dia, tzinfo=timezone.utc).timestamp() * 1000)
                for p in range(ns['N_PONTOS']):
                    o = float(r.normal(75, 8))
                    linhas.append(['x', -60 + 0.1 * p + 0.05, -10 - 0.1 * p - 0.05, t, 2.0, 29.0, 18.0,
                                   69 + (o - 75) * 1.5, 2.2, 17.0, 3.0, 30.0, 19.0, o, 2.0, 18.0, 4.0])
            return linhas
        if n.endswith('limit()'):
            return {'features': []}
        if n.endswith('ee.List()'):
            base = int(datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
            return [[base - j * 86400000, 209, (base - j * 86400000 + 7 * 3.6e6) * 1000] for j in range(1, 21)]
        raise RuntimeError('sem resposta para ' + n)


class Elem:
    """[v3a] ee.Element do cliente Python: sem select, rename etc. (só vira imagem com ee.Image(...))."""
    def __getattr__(self, a):
        if a.startswith('__') or a in ('select', 'rename', 'updateMask', 'addBands', 'multiply', 'add'):
            raise AttributeError(f"'Element' object has no attribute '{a}'")
        return S(f'elem.{a}')


raiz = S()
ee = types.ModuleType('ee')
for a in ('Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Filter', 'Reducer', 'Date', 'Geometry', 'Join',
          'Projection', 'List'):
    setattr(ee, a, getattr(raiz, a))
ee.Initialize = lambda *a, **k: None
gravou = []
ee.data = types.SimpleNamespace(deleteAsset=lambda *a: gravou.append('d'), startProcessing=lambda *a: gravou.append('e'))
ee.batch = types.SimpleNamespace(Task=type('Task', (), {'start': lambda self: gravou.append('s')}))
sys.modules['ee'] = ee
ns['RESULTADOS'].clear()
ns['PASTA'] = os.path.join(tmp, 'validacao_K21_teste')
ns['LOG'] = os.path.join(ns['PASTA'], 'LOG_K21.txt')
ns['minutos_ate_janela'] = lambda agora: 999
_s = time.sleep
time.sleep = lambda *a: None
ns['principal']()
time.sleep = _s
print('\n[execução completa]')
log = open(ns['LOG'], encoding='utf-8').read()
confere('RESULTADO K21' in log and '[dias]' in log and '[X]' in log and '[G]' in log, 'as partes rodaram até o fim')
confere('matriz V1.5: pesado, dividindo os pontos (150 -> 75 + 75)' in log, 'memória recusada: divide os pontos e segue')
confere('combinações pixel-mês com quantis' in log and '1986: ' in log and '2025: ' in log, 'v3: treino (1986-2015) lido dia a dia e quantis em Python; teste até 2025')
confere("ℹ️ X INFO: nenhum pixel A de 2026" in log, 'X sem pixels extremos: informação')
confere('ℹ️ G INFO' in log and 'rodada única das 23h07' in log, 'v4: G é só informação (motor às 23h07)')
confere('V1.6 REVISTA APROVADA FORA DA AMOSTRA' in log or 'NÃO aprovada' in log, 'v4: decisão final escrita')
confere(os.path.exists(os.path.join(ns['PASTA'], 'K21_RESUMO.csv')), 'resumo gravado')
for n_ in ('deleteAsset', 'startProcessing'):
    try:
        getattr(ee.data, n_)()
        confere(False, f'trava: {n_} liberado')
    except RuntimeError:
        confere(True, f'trava: {n_} bloqueado')
confere(not gravou, 'nada gravado')
ns['minutos_ate_janela'] = lambda agora: 30
ns['RESULTADOS'].clear()
ns['PASTA'] = os.path.join(tmp, 'validacao_K21_janela')
ns['LOG'] = os.path.join(ns['PASTA'], 'LOG_K21.txt')
ns['principal']()
confere('Não comecei' in open(ns['LOG'], encoding='utf-8').read(), 'não começa a 30 min de uma janela do motor')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
