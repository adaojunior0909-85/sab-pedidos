# Teste offline da K19 (sem Earth Engine): funções estatísticas e de decisão com casos conhecidos, carga segura dos
# motores embutidos e a execução completa com um Earth Engine falso que responde no formato real de cada parte.
# Rodar: python3 testes/teste_k19.py
import os
import sys
import tempfile
import time
import types
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(AQUI, '..', 'validacoes', 'K19_auditoria_profunda_SAB.py'), encoding='utf-8').read()
ns = {'__name__': 'teste_k19'}
exec(compile(SRC, 'K19', 'exec'), ns)
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


BRT = timezone(timedelta(hours=-3))
print('[janela do motor]')
mj = ns['minutos_ate_janela']
confere(mj(datetime(2026, 11, 3, 18, 45, tzinfo=BRT)) == 245, '18h45: 245 min até 22h50')
confere(all(mj(datetime(2026, 11, 3, h, m, tzinfo=BRT)) == 0 for h, m in ((15, 0), (16, 20), (23, 30), (0, 20))),
        'dentro das janelas (15h00, 16h20, 23h30, 00h20): 0')
confere(mj(datetime(2026, 11, 3, 13, 0, tzinfo=BRT)) == 110, '13h00: 110 min até 14h50')
confere(mj(datetime(2026, 11, 4, 0, 40, tzinfo=BRT)) == 310, '00h40: 310 min até 05h50 (janela da manhã, motor V1.6)')

print('[Pettitt e SNHT]')
rng = np.random.default_rng(3)
x = np.r_[rng.normal(0, 1, 30), rng.normal(2, 1, 35)]
kp, K, pp = ns['pettitt'](x)
ks, t0, ps = ns['snht'](x)
confere(abs(kp - 30) <= 2 and pp < 0.01, f'Pettitt acha a quebra em 30 ({kp}, p={pp:.1e})')
confere(abs(ks - 30) <= 2 and ps < 0.01, f'SNHT acha a quebra em 30 ({ks}, T0={t0:.1f}, p={ps:.3f})')
y = rng.normal(0, 1, 65)
confere(ns['pettitt'](y)[2] > 0.01 and ns['snht'](y)[2] > 0.01, 'série sem quebra: não significativa')

print('[homogeneidade por estado]')
lin = []
for u in range(27):
    for a in range(1961, 2027):
        base = rng.normal(0, 0.1)
        salto = 0.8 if (u < 8 and a >= 1979) else 0.0
        lin.append({'uf': f'UF{u}', 'ano': a, 'variavel': 'tmax_C (SAB x ERA5)', 'd': base + salto})
        lin.append({'uf': f'UF{u}', 'ano': a, 'variavel': 'RH (SAB x ERA5)', 'd': rng.normal(0, 0.1) + (1.0 if a == 2026 else 0)})
tab = ns['homogeneidade'](pd.DataFrame(lin), list(range(1961, 2027)))
g = ns['agrupar_quebras'](tab)
confere(len(g) == 1 and g.iloc[0]['variavel'].startswith('tmax') and abs(g.iloc[0]['ano_central'] - 1979) <= 1
        and g.iloc[0]['estados'] >= 7, f'quebra em 8 estados por volta de 1979 agrupada ({g.to_dict("records")})')
confere((tab[tab['variavel'].str.startswith('RH')]['z_2026'].abs() > 3).sum() >= 20, 'costura de 2026 (z > 3) acusada')
confere(not tab[tab['variavel'].str.startswith('RH')]['quebra'].any(), 'RH sem quebra no histórico')

print('[mapeamento de quantis e D5]')
qm, qo = ns['eqm_ajustar'](np.arange(100.0), np.arange(100.0) * 2)
confere(np.allclose(ns['eqm_aplicar']([10, 50, 200], qm, qo, chuva=True)[:2], [20, 100]) and
        ns['eqm_aplicar']([200], qm, qo, chuva=True)[0] > 300, 'EQM interpola e extrapola a cauda')
pts, linhas = 15, []
for pid in range(pts):
    for d in pd.date_range('2014-01-01', '2025-12-31', freq='D'):
        molhado = rng.random() < 0.35
        br = rng.gamma(0.8, 14) if molhado else 0.0
        era = (0.7 * br + rng.gamma(0.5, 1.5)) if (molhado or rng.random() < 0.45) else 0.0   # garoa e extremos amortecidos
        tb = 26 + 4 * np.sin(d.dayofyear / 58) + rng.normal(0, 3)
        rh, rs, u2 = 75 + rng.normal(0, 8), 18 + rng.normal(0, 4), 2 + abs(rng.normal(0, 0.8))
        linhas.append({'pid': pid, 'data': d.strftime('%Y-%m-%d'), 'era_pr': era, 'br_pr': br,
                       'era_tmax': 0.6 * tb + 11, 'br_tmax': tb, 'era_tmin': 0.6 * (tb - 10) + 7, 'br_tmin': tb - 10,
                       'era_rh': rh - 4, 'br_rh': rh, 'era_rs': rs * 1.05, 'br_rs': rs,
                       'era_u2': 0.4 * u2 + 0.5, 'br_u2': u2})
dados = pd.DataFrame(linhas)
dados['mes'] = dados['data'].str[5:7].astype(int)
mm = dados.groupby(['pid', 'mes']).agg(pr_m_br=('br_pr', 'mean'), pr_m_era=('era_pr', 'mean'),
                                       Tmax_m_br=('br_tmax', 'mean'), Tmax_m_era=('era_tmax', 'mean'),
                                       Tmin_m_br=('br_tmin', 'mean'), Tmin_m_era=('era_tmin', 'mean'),
                                       RH_m_br=('br_rh', 'mean'), RH_m_era=('era_rh', 'mean'),
                                       Rs_m_br=('br_rs', 'mean'), Rs_m_era=('era_rs', 'mean'),
                                       u2_m_br=('br_u2', 'mean'), u2_m_era=('era_u2', 'mean')).reset_index()
tab5, txt5, cand5 = ns['avaliar_d5'](dados.drop(columns='mes'), mm)
c = tab5[tab5['variavel'] == 'chuva'].set_index('metodo')
confere(cand5 and abs(c.loc['quantis (EQM)', 'erro_freq_pp']) < abs(c.loc['atual (média, V1.5)', 'erro_freq_pp']),
        f'garoa do ERA5: o EQM corrige a frequência de dias com chuva ({txt5[:120]}...)')
t = tab5[tab5['variavel'] == 'tmax'].set_index('metodo')
confere(abs(t.loc['atual (média, V1.5)', 'razao_desvio'] - 0.6) < 0.08 and abs(t.loc['quantis (EQM)', 'razao_desvio'] - 1) < 0.1,
        'Tmax: a correção na média mantém a variância amortecida (0,6); o EQM corrige')
u = tab5[tab5['variavel'] == 'u2'].set_index('metodo')
ua, uq = u.loc['atual (média, V1.5)'], u.loc['quantis (EQM)']
confere(abs(ua['vies']) < 0.05 and 0.6 < ua['razao_desvio'] < 0.8 and abs(uq['razao_desvio'] - 1) < 0.15,
        f'vento (ERA5 = 0,4 x obs + 0,5): o fator multiplicativo acerta a média e deixa a variância em ~0,68; o EQM '
        f'corrige ({ua["vies"]:+.3f}, x{ua["razao_desvio"]:.2f}; EQM x{uq["razao_desvio"]:.2f})')
confere(set(tab5['variavel']) == {'chuva', 'tmax', 'tmin', 'rh', 'rs', 'u2'}, 'D5 mede as 6 variáveis do núcleo')

print('[controle de qualidade e reprodução]')
qc = pd.DataFrame([{'ano': 2000, 'classe': 'A', 'n': 1000, **{q[0]: 0 for q in ns['QC']}},
                   {'ano': 2001, 'classe': 'A', 'n': 1000, **{q[0]: 0 for q in ns['QC']}}])
confere(ns['resumo_qc'](qc)[0] == 'OK', 'sem ocorrência: OK')
qc.loc[1, 'tmax_gt_45'] = 3
confere(ns['resumo_qc'](qc)[0] == 'ATENÇÃO', 'só suspeito (Tmax > 45): ATENÇÃO')
qc.loc[0, 'tmax_lt_tmin'] = 2
st, det, _ = ns['resumo_qc'](qc)
confere(st == 'FALHA' and 'Tmax < Tmin (A): 2 em 2000-2000' in det, f'impossível (Tmax < Tmin): FALHA ({det[:90]})')
qc2 = qc.copy()
qc2[[q[0] for q in ns['QC']]] = 0
qc2.loc[0, 'solo_gt_09'] = 50
confere(ns['resumo_qc'](qc2)[0] == 'OK', 'umidade bruta > 0,9 (conhecido, corrigido na leitura) não pesa')
ORD = ns['ORDEM']
lin1 = [{'data': '1990-03-15', 'classe': 'A', **{f'frac_{b}': 1.0 for b in ORD}},
        {'data': '2020-09-15', 'classe': 'A', **{f'frac_{b}': (0.4 if b == 'et_real' else 1.0) for b in ORD}},
        {'data': '2020-09-15', 'classe': 'B', **{f'frac_{b}': (0.5 if b == 'pr_mm' else 1.0) for b in ORD}},
        {'data': '2005-05-15', 'classe': 'A', **{f'frac_{b}': (0.9 if b == 'tmax_C' else 1.0) for b in ORD}}]
lin1.append({'data': '2026-03-15', 'classe': 'A', **{f'frac_{b}': (0.5 if b in ('pr_mm', 'et_real') else 1.0) for b in ORD}})
tipos, cont, outros = ns['classificar_d1'](lin1)
confere(tipos.set_index('data').loc['2026-03-15', 'tipo'] == 'só ERA5 acumulado',
        '2026: chuva dos pixels A vem do ERA5 (não do BR-DWGD): mesma assinatura')
cont['só ERA5 acumulado'] -= 1
confere(cont == {'idênticos': 1, 'só ERA5 acumulado': 1, 'outra diferença': 1} and outros == ['2005-05-15'],
        f'reprodução classificada ({cont})')


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
        if self._n.endswith('Feature') and len(a) > 1:
            novo._props = dict(a[1]) if isinstance(a[1], dict) else {'__base__': a[1]}
        if self._n.endswith('.set') and a:
            novo._props.update(a[0] if isinstance(a[0], dict) else {a[0]: a[1]})
        if self._n.endswith('FeatureCollection') and a and isinstance(a[0], list):
            novo._feats = [x._props for x in a[0] if isinstance(x, S)]
        return novo

    def __getitem__(self, k):
        return S(self._n + '[]')

    def _op(self, *a):
        return S(self._n + '·')
    __add__ = __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = __truediv__ = __rtruediv__ = __neg__ = __pow__ = _op

    def _responder(self):
        return responder(self)


N5 = 12
CHAMADAS = {'getRegion': 0}
ANOS5 = ns['ANOS_TREINO_D5'] + ns['ANOS_TESTE_D5']
NOMES_QC = [q[0] for q in ns['QC']]


def responder(o):
    n = o._n
    if '.stratifiedSample()' in n:
        X0, Y0, DX = ns['X0'], ns['Y0'], ns['DX']
        return {'features': [{'properties': {'classe': [1, 1, 2, 3, 4][i % 5]},
                              'geometry': {'coordinates': [X0 + (100 + 3 * i + 0.5) * DX, Y0 - (150 + 2 * i + 0.5) * DX]}}
                             for i in range(N5)]}
    if n.endswith('.sampleRegions()'):
        out = []
        pids = [f.get('pid', i) for i, f in enumerate(o._feats)] if o._feats else list(range(N5))
        for i in pids:
            p = {'pid': i, **{f'{pr}{b}': 1.0 for pr in ('s_', 'r_') for b in ns['ORDEM']}}
            for m in range(1, 13):
                p.update({f'pr_m_br__{m}': 5.0, f'pr_m_era__{m}': 6.0, f'Tmax_m_br__{m}': 30.0, f'Tmax_m_era__{m}': 29.0,
                          f'Tmin_m_br__{m}': 19.0, f'Tmin_m_era__{m}': 18.5, f'RH_m_br__{m}': 75.0, f'RH_m_era__{m}': 72.0,
                          f'Rs_m_br__{m}': 18.0, f'Rs_m_era__{m}': 19.0, f'u2_m_br__{m}': 2.0, f'u2_m_era__{m}': 1.2})
            out.append({'properties': p})
        return {'features': out}
    if n.endswith('.getRegion()'):
        k = CHAMADAS['getRegion']
        ano, mes = ANOS5[k // 12], k % 12 + 1
        CHAMADAS['getRegion'] += 1
        X0, Y0, DX = ns['X0'], ns['Y0'], ns['DX']
        cab = ['id', 'longitude', 'latitude', 'time', 'era_pr', 'era_tmax', 'era_tmin', 'era_rh', 'era_rs', 'era_u2',
               'br_pr', 'br_tmax', 'br_tmin', 'br_rh', 'br_rs', 'br_u2']
        linhas = [cab]
        r = np.random.default_rng(ano)
        r = np.random.default_rng(ano * 100 + mes)
        for d in pd.date_range(f'{ano}-{mes:02d}-01', periods=31):
            if d.month != mes:
                break
            ms = int(d.tz_localize('UTC').timestamp() * 1000)
            for i in range(N5):
                br = r.gamma(0.8, 14) if r.random() < 0.35 else 0.0
                era = 0.7 * br + (r.gamma(0.5, 1.5) if r.random() < 0.5 else 0)
                tb = 28 + r.normal(0, 3)
                linhas.append(['x', X0 + (100 + 3 * i) * DX, Y0 - (150 + 2 * i) * DX, ms, era, 0.6 * tb + 11,
                               0.6 * tb + 1, 72 + r.normal(0, 5), 19 + r.normal(0, 3), 1.2 + abs(r.normal(0, 0.3)),
                               br, tb, tb - 10, 75 + r.normal(0, 8), 18 + r.normal(0, 4), 2 + abs(r.normal(0, 0.8))])
        return linhas
    if 'reduceRegion' in n and n.endswith('.get()'):                       # D1: grupos por classe
        return [{'classe': c, 'mean': [1.0] * 16 + [0.0] * 16} for c in range(0, 5)]
    if o._feats is not None:                                               # FeatureCollection de resultados
        out = []
        for p in o._feats:
            if 'qc' in p:                                                  # D2/D3
                q = {'ano': p['ano'], 'n_dias': 365,
                     'qc': [{'classe': c, 'sum': [0] * len(NOMES_QC) + [50000]} for c in range(5)],
                     'd3': [{'classe': c, 'sum': [0, 0, 0, 0]} for c in range(5)],
                     'eto_max': {'max': 9.5, 'max1': -50.0, 'max2': -10.0},
                     'tmax_max': {'max': 41.0, 'max1': -50.0, 'max2': -10.0},
                     'tmin_min': {'min': -3.0, 'min1': -51.0, 'min2': -28.0},
                     'pr_max': {'max': 280.0, 'max1': -48.0, 'max2': -23.0},
                     'tmax_dif_max': {'max': 1.5, 'max1': -50.0, 'max2': -10.0},
                     'pr_dif_max': {'max': 60.0, 'max1': -48.0, 'max2': -23.0}}
                q['qc'][1]['sum'][NOMES_QC.index('solo_gt_09')] = 7
            elif 'ufs' in p:                                               # D6
                ufs = []
                for u in range(27):
                    v = {'ADM1_NAME': f'UF{u}', 's_tmax_C': 30.0 + 0.01 * u, 'r_tmax_C': 29.0, 's_tmin_C': 19.0,
                         'r_tmin_C': 18.0, 's_RH': 75.0, 'r_RH': 72.0, 's_rs': 18.0, 'r_rs': 19.0, 's_u2': 2.0, 'r_u2': 2.5,
                         's_pr_mm': 900.0, 'r_pr_mm': 1000.0, 's_et_real': 700.0, 'r_et_real': 690.0}
                    v = {k: (x + np.random.default_rng(p['ano'] * 100 + u).normal(0, 0.05) if isinstance(x, float) else x)
                         for k, x in v.items()}
                    if p['ano'] >= 1981:
                        v['c_pr'] = 950.0
                    ufs.append(v)
                q = {'ano': p['ano'], 'ufs': ufs}
            elif 'data' in p:                                              # D4
                q = {'data': p['data'], 'dif_eto': 0.1, 'abs_eto': 0.2, 'eto_sab': 4.0, 'eto_pm': 4.1, 'abs_vpd': 0.0}
            else:
                raise RuntimeError('feature desconhecida no teste')
            out.append({'properties': q})
        return {'features': out}
    raise RuntimeError(f'sem resposta neste teste: {n[-80:]}')


raiz = S()
ee = types.ModuleType('ee')
for a in ('Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Filter', 'Reducer', 'Projection', 'Date', 'Geometry',
          'Join', 'Number', 'List', 'Dictionary', 'Algorithms', 'String', 'Kernel', 'Terrain'):
    setattr(ee, a, getattr(raiz, a))
ee.Initialize = lambda *a, **k: None
gravou = []
ee.data = types.SimpleNamespace(deleteAsset=lambda *a: gravou.append('d'), startProcessing=lambda *a: gravou.append('e'))
ee.batch = types.SimpleNamespace(Task=type('Task', (), {'start': lambda self: gravou.append('s')}))
sys.modules['ee'] = ee

print('[carga segura dos motores embutidos]')
for nome, fonte, precisa in (('v10', ns['FONTE_V10'], ['processarDia_Definitivo']),
                             ('v15', ns['FONTE_V15'], ['processarDia_Rota1', 'eto_penman_monteith', 'vpd_e_ea'])):
    carga, pulados = ns['carregar_codigo'](nome, fonte, precisa, ee)
    confere(all(callable(carga[f]) for f in precisa), f'{nome}: {precisa} carregadas')
    if nome == 'v15':
        r = carga['eto_penman_monteith'](S('t'), S('t'), S('t'), S('t'), S('t'), '2026-01-15')
        confere(isinstance(r, S), 'v15: ETo FAO-56 montada sem erro de nome')

print('[execução completa]')
tmp = tempfile.mkdtemp()
ns['PASTA'] = os.path.join(tmp, 'validacao_K19_teste')
ns['LOG'] = os.path.join(ns['PASTA'], 'LOG_K19.txt')
ns['N_PONTOS_D5'] = N5
ns['minutos_ate_janela'] = lambda agora: 999                   # o teste não depende da hora em que roda
_s = time.sleep
time.sleep = lambda *a: None
ns['principal']()
time.sleep = _s
log = open(ns['LOG'], encoding='utf-8').read()
st = {a['parte']: a['status'] for a in ns['ACHADOS']}
print('   ', st)
confere(set(st) == {'D1', 'D2', 'D3', 'D4', 'D5', 'D6'} and 'NÃO EXECUTADO' not in st.values(),
        'as 6 partes rodaram até o fim')
confere(st['D2'] == 'OK' and st['D3'] == 'OK', 'D2/D3: sem ocorrência (umidade > 0,9 é conhecida)')
confere(st['D1'] == 'OK' and '75 dias: idênticos 75' in log and 'D1: 12 pixels' in log,
        'D1 nos pixels sorteados: 75 dias (65 do histórico + 10 de 2026) idênticos')
confere(st['D4'] == 'OK', 'D4: ETo dentro de 3%')
confere(st['D5'] in ('ATENÇÃO', 'INFO') and os.path.exists(os.path.join(ns['PASTA'], 'D5_metricas_teste_2024_2025.csv')),
        f'D5 calculada ({st["D5"]})')
h6 = pd.read_csv(os.path.join(ns['PASTA'], 'D6_homogeneidade_por_estado.csv'), sep=';', decimal=',')
confere(st['D6'] == 'OK' and 'costura 2026' in log and len(h6) == 27 * 8,
        f'D6: 27 estados x 8 séries (7 x ERA5 + chuva x CHIRPS), sem quebra nos dados simulados ({len(h6)})')
confere(os.path.exists(ns['PASTA'] + '.zip') and os.path.exists(os.path.join(ns['PASTA'], 'K19_CANDIDATAS.csv')),
        'zip e lista de candidatas gerados')
confere(CHAMADAS['getRegion'] == 12 * len(ANOS5), f'D5 leu os {len(ANOS5)} anos mês a mês ({CHAMADAS["getRegion"]} pedidos)')
for n_ in ('deleteAsset', 'startProcessing'):
    try:
        getattr(ee.data, n_)()
        confere(False, f'trava: {n_} liberado')
    except RuntimeError:
        confere(True, f'trava: {n_} bloqueado')
confere(not gravou, 'nada gravado')

print('[recusa perto da janela do motor]')
ns['minutos_ate_janela'] = lambda agora: 30
ns['PASTA'] = os.path.join(tmp, 'validacao_K19_janela')
ns['LOG'] = os.path.join(ns['PASTA'], 'LOG_K19.txt')
ns['ACHADOS'].clear()
ns['principal']()
confere('Não comecei' in open(ns['LOG'], encoding='utf-8').read() and not ns['ACHADOS'], 'não começa a 30 min da janela')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)

