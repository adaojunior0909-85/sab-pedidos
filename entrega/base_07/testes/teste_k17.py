# Teste offline da K17 (sem Earth Engine): carga segura dos códigos embutidos, rotas montadas sem erro de nome
# com um Earth Engine simulado, e as funções puras de decisão. Rodar: python3 testes/teste_k17.py
import math
import os
import sys
import types

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(AQUI, '..', 'validacoes', 'K17_validacao_final_SAB.py'), encoding='utf-8').read()
ns = {'__name__': 'teste_k17'}
exec(compile(SRC, 'K17', 'exec'), ns)
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


# ---------------------------------------------------------------- Earth Engine simulado (aceita qualquer chamada)
class S:
    chamadas = []

    def __init__(self, nome='ee'):
        self._n = nome

    def __getattr__(self, a):
        if a.startswith('__'):
            raise AttributeError(a)
        if a == 'getInfo':
            raise AssertionError('getInfo chamado durante a carga ou a montagem da rota')
        if a in ('start',):
            raise AssertionError('start chamado: escrita')
        return S(f'{self._n}.{a}')

    def __call__(self, *a, **k):
        S.chamadas.append(self._n)
        return S(self._n + '()')

    def __getitem__(self, k):
        return S(self._n + '[]')

    def _op(self, *a):
        return S(self._n + '·')
    __add__ = __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = __truediv__ = __rtruediv__ = __neg__ = _op


ee_falso = S()
print('[carga segura dos códigos embutidos]')
fontes = {'v10': ns['FONTE_V10'], 'v13': ns['FONTE_V13'], 'v15': ns['FONTE_V15'], 'clima': ns['FONTE_CLIMA'],
          'solo': ns['FONTE_SOLO']}
precisa = {'v10': ['processarDia_Definitivo'], 'v13': ['processarDia_Definitivo', 'aplicarPatch_Solo'],
           'v15': ['processarDia_Definitivo', 'processarDia_Rota1', 'aplicarPatch_Solo'],
           'clima': ['gerar_matriz_do_mes'], 'solo': ['gerar_matriz_solo_mes']}
cargas = {}
for nome, fonte in fontes.items():
    trechos = ns['trechos_carregaveis'](fonte)
    nao_func = [seg for tipo, seg in trechos if tipo != 'FunctionDef']
    proibidos = [p for seg in nao_func for p in ns['PROIBIDO_NA_CARGA'] if p in seg]
    confere(not proibidos, f'{nome}: nenhuma chamada ao servidor ou escrita fora das funções ({len(trechos)} trechos)')
    fluxo = [seg.splitlines()[0] for tipo, seg in trechos if tipo == 'Assign' and
             any(x in seg for x in ('despachar_assincrono(', 'executar_esteira', 'mapear_colecao(', 'listar_tarefas'))]
    confere(not fluxo, f'{nome}: fluxo principal do motor fora da carga {fluxo[:2]}')
    S.chamadas.clear()
    carga, pulados = ns['carregar_codigo'](nome, fonte, precisa[nome], ee_falso)
    cargas[nome] = carga
    confere(all(callable(carga[f]) for f in precisa[nome]), f'{nome}: funções {precisa[nome]} carregadas')
    confere(not any('Export' in c or c.endswith('.start') for c in S.chamadas), f'{nome}: nenhuma exportação na carga')

print('[rotas montadas sem erro de nome (Earth Engine simulado)]')
for nome, chamada in (('v10', lambda c: c['processarDia_Definitivo']('2020-01-15')),
                      ('v13', lambda c: c['processarDia_Definitivo']('2020-01-15')),
                      ('v15', lambda c: c['processarDia_Definitivo']('2020-01-15')),
                      ('v15', lambda c: c['processarDia_Rota1']('2026-10-20')),
                      ('v15', lambda c: c['aplicarPatch_Solo']('1961-01-15')),
                      ('v13', lambda c: c['aplicarPatch_Solo']('1961-01-15')),
                      ('clima', lambda c: c['gerar_matriz_do_mes'](7)),
                      ('solo', lambda c: c['gerar_matriz_solo_mes'](1))):
    try:
        r = chamada(cargas[nome])
        confere(isinstance(r, S), f'{nome}: rota montada ({r._n[:40]}...)')
    except Exception as e:
        confere(False, f'{nome}: {type(e).__name__}: {e}')
confere(cargas['v15']['VERSAO_ALGORITMO'] == 'V1.5' and cargas['v13']['VERSAO_ALGORITMO'] == 'V1.3',
        'constantes de versão carregadas (V1.3 e V1.5)')
confere(cargas['v15']['PROTEGER_HISTORICO'] is True, 'trava do histórico presente no V1.5 carregado')

print('[inventário]')
datas = pd.date_range('1961-01-01', '2026-11-18', freq='D')
df = pd.DataFrame({'id': ['SAB_' + d.strftime('%Y_%m_%d') for d in datas]})
df['versao'] = ['definitiva' if d <= pd.Timestamp('2025-12-31') else
                ('provisoria_era5' if d <= pd.Timestamp('2026-10-28') else 'provisoria_gfs') for d in datas]
df['alg'] = ['V1.0' if d <= pd.Timestamp('2025-12-31') else 'V1.5' for d in datas]
df['t_ms'] = 0
prob, resumo, tab = ns['analisar_inventario'](df, pd.Timestamp('2026-11-03').date(), '2026-10-28')
confere(not prob and '23741' in resumo.replace('.', '') or 'histórico 23741' in resumo, f'acervo certo: sem problemas ({resumo})')
ruim = df.drop(index=[100, 200]).copy()
ruim.loc[ruim['id'] == 'SAB_1999_05_05', 'alg'] = 'V1.2'
prob, _, _ = ns['analisar_inventario'](ruim, pd.Timestamp('2026-11-03').date(), '2026-10-28')
confere(any('faltando' in p for p in prob) and any('V1.0' in p for p in prob), 'dias faltando e versão estranha acusados')
curto = df[df['id'] <= 'SAB_2026_11_05']
prob, _, _ = ns['analisar_inventario'](curto, pd.Timestamp('2026-11-03').date(), '2026-10-28')
confere(any('previsão termina' in p for p in prob), 'previsão curta acusada')

print('[comparação e reprodução]')
base = pd.DataFrame({'s_pr_mm': [1.0, 2.0, None, 4.0], 'a_pr_mm': [1.0, 2.0004, None, 4.0],
                     's_tmax_C': [30.0, 31.0, 32.0, 33.0], 'a_tmax_C': [30.0, 31.5, 32.0, 33.0], 'data': ['d1'] * 4})
t = ns['comparar_bandas'](base, 's_', 'a_', ['pr_mm', 'tmax_C'], grupo='data')
confere(t.set_index('banda').loc['pr_mm', 'frac_iguais'] == 1.0, 'ausente nos dois e diferença de 0,0004 contam como iguais')
confere(t.set_index('banda').loc['tmax_C', 'n_diferentes'] == 1, 'diferença de 0,5 °C acusada')
st, det = ns['status_reproducao'](t)
confere(st == 'ATENÇÃO' and 'tmax_C' in det, f'reprodução com diferença vira ATENÇÃO ({det[:60]})')
confere(ns['status_reproducao'](t[t['banda'] == 'pr_mm'])[0] == 'OK', 'reprodução idêntica vira OK')

print('[CHIRPS]')
import random
random.seed(1)
linhas = []
for i in range(300):
    c = random.uniform(0, 300)
    linhas.append({'periodo': 'histórico', 'chirps': c, 'sab': c * 1.05 + random.uniform(-15, 15)})
    linhas.append({'periodo': '2026 provisório', 'chirps': c, 'sab': c * 1.6 + random.uniform(-80, 80)})
tab = ns['estatisticas_chirps'](pd.DataFrame(linhas))
st, det = ns['status_chirps'](tab)
confere(st == 'ATENÇÃO' and '2026 provisório' in det.split('fora do esperado')[1], f'viés de +60% em 2026 acusado')
confere(tab.set_index('periodo').loc['histórico', 'r'] > 0.95, 'correlação do histórico calculada')

print('[RONI]')
cpc = pd.DataFrame({'SEAS': ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ'], 'YR': [2025] * 5,
                    'ANOM': [-1.07, -0.83, -0.45, -0.52, 0.48]})
asset = pd.DataFrame({'ano': [2025] * 5, 'Trimestre': ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ'],
                      'RONI': [-1.1, -0.8, -0.4, -0.5, 0.5]})
st, det, _ = ns['avaliar_roni'](asset, cpc)
confere(st == 'OK' and 'empate' in det, f'iguais, com empate de arredondamento aceito ({det})')
asset2 = asset.copy()
asset2.loc[0, 'RONI'] = -0.9
confere(ns['avaliar_roni'](asset2, cpc)[0] == 'FALHA', 'estação antiga diferente: FALHA')
asset3 = asset.copy()
asset3.loc[4, 'RONI'] = 0.3
confere(ns['avaliar_roni'](asset3, cpc)[0] == 'ATENÇÃO', 'estação recente diferente (revisão do CPC): ATENÇÃO')
confere(ns['avaliar_roni'](asset.iloc[:4], cpc)[0] == 'ATENÇÃO', 'estação nova do CPC fora do asset: ATENÇÃO')
confere(ns['arredondar_cpc'](-0.45) == -0.5 and ns['arredondar_cpc'](0.45) == 0.5 and ns['arredondar_cpc'](1.04) == 1.0,
        'arredondamento do CPC (metade para longe do zero)')

print('[máscara, coerência e veredito]')
grav = {1: 70632, 2: 301, 3: 47, 4: 1060}
confere(ns['avaliar_mascara'](dict(grav), grav)[0] == 'OK', 'máscara igual à que o 01b gravou: OK')
confere(ns['avaliar_mascara']({1: 70632, 2: 300, 3: 48, 4: 1060}, grav)[0] == 'FALHA', 'máscara mudou depois da gravação: FALHA')
confere(ns['avaliar_mascara'](dict(grav))[0] == 'OK', 'sem propriedades: dentro das faixas do roteiro (B ~300)')
confere(ns['avaliar_mascara']({1: 70524, 2: 241, 3: 48, 4: 1060})[0] == 'ATENÇÃO',
        'sem propriedades: B 241 (conta da K1d) fora da faixa da máscara inteira')
print('[P2: diagnóstico por banda e classe (v4)]')
import numpy as np
linhas = []
for d, mexe in (('2013-07-15', []), ('2020-01-15', ['et_real', 'pr_mm']), ('2004-01-15', ['tmax_C'])):
    for k in range(40):
        c = 1 if k < 20 else 2
        r = {'data': d, 'classe': c}
        for b in ns['ORDEM']:
            r[f's_{b}'] = 1.0
            r[f'a_{b}'] = 1.5 if (b in mexe and not (b == 'pr_mm' and c == 1)) else 1.0
        linhas.append(r)
amos = pd.DataFrame(linhas)
ok, txt = ns['assinatura_p2'](amos[amos['data'] != '2004-01-15'])
confere(ok and len(txt) == 1 and 'só variáveis acumuladas' in txt[0], f'só ERA5 acumulado: diagnosticado ({txt})')
ok2, txt2 = ns['assinatura_p2'](amos)
confere(ok2 is False and any('fora das acumuladas' in t for t in txt2), 'Tmax diferente: fora da assinatura')
pr_a = amos.copy()
pr_a.loc[(pr_a['data'] == '2020-01-15') & (pr_a['classe'] == 1), 'a_pr_mm'] = 1.5
confere(ns['assinatura_p2'](pr_a[pr_a['data'] != '2004-01-15'])[0] is False, 'chuva diferente nos pixels A (BR-DWGD): fora da assinatura')
print('[P4: tabela agrupada]')
g = {'groups': [{'pid': 3, 'mean': [1.0, 2.0]}, {'pid': 7, 'mean': [3.0, 4.0]}]}
tg = ns['tabela_agrupada'](g, ['pr_m_br', 'Tmax_m_br'], 'r_')
confere(list(tg.columns) == ['pid', 'r_pr_m_br', 'r_Tmax_m_br'] and tg.loc[1, 'r_Tmax_m_br'] == 4.0, 'grupos viram colunas')
confere(ns['tabela_agrupada']({'groups': [{'pid': 1, 'stdDev': 0.5}]}, ['x_s_br'], 'r_').loc[0, 'r_x_s_br'] == 0.5,
        'redutor com uma saída só')
coer = pd.DataFrame({'data': ['1961-01-15', '2026-11-10'], 'etr_acima_eto': [0.0, 0.0], 'transp_acima_etr': [0, 0],
                     'tmax_abaixo_tmin': [0, 0], 'ur_fora': [0, 0], 'chuva_negativa': [0, 0], 'tmax_acima_45': [0, 0],
                     'tmin_abaixo_m10': [0, 0], 'solo_acima_09_bruto': [0.02, 0], 'solo_acima_09_lido': [0, None]})
st, det = ns['status_coerencia'](coer)
confere(st == 'OK' and 'corrigido na leitura' in det, 'solo bruto acima de 0,9 (corrigido na leitura) não reprova')
coer.loc[1, 'etr_acima_eto'] = 0.01
confere(ns['status_coerencia'](coer)[0] == 'FALHA', 'ET real acima da ETo: FALHA')
ok = [{'parte': p, 'status': 'OK'} for p in ('P1', 'P2', 'P4', 'P5', 'P6', 'P8', 'P9')] + \
     [{'parte': 'P3', 'status': 'INFO'}, {'parte': 'P7', 'status': 'ATENÇÃO'}]
confere(ns['veredito'](ok)[0] is True, 'tudo OK (P3/P7 só medidas): aprovada')
ok[1]['status'] = 'ATENÇÃO'
confere(ns['veredito'](ok)[0] is False and 'P2' in ns['veredito'](ok)[1], 'P2 em ATENÇÃO: pendente')
confere(ns['SHAS']['V1.5 (05b)'].startswith('f35d5966'), 'V1.5 embutido = o mesmo motor do GitHub (SHA f35d5966...)')

print('[orquestração: principal() com Earth Engine simulado sem resposta]')
import tempfile, time as _time
_sleep = _time.sleep
_time.sleep = lambda *a: None
mod_ee = types.ModuleType('ee')
for _a in ('Initialize', 'Authenticate', 'Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Filter',
           'Reducer', 'Projection', 'Dictionary', 'Date', 'Algorithms', 'List', 'Number', 'String', 'Geometry'):
    setattr(mod_ee, _a, getattr(ee_falso, _a))
mod_ee.Initialize = lambda *a, **k: None
mod_ee.data = types.SimpleNamespace(deleteAsset=lambda *a: 'apagou', createAsset=lambda *a: 'criou',
                                    startProcessing=lambda *a: 'exportou')
mod_ee.batch = types.SimpleNamespace(Task=type('Task', (), {'start': lambda self: 'iniciou'}))
mod_req = types.ModuleType('requests')
mod_req.get = lambda *a, **k: (_ for _ in ()).throw(ConnectionError('sem rede no teste'))
sys.modules['ee'], sys.modules['requests'] = mod_ee, mod_req
tmp = tempfile.mkdtemp()
ns['PASTA'] = os.path.join(tmp, 'validacao_K17_teste')
ns['LOG'] = os.path.join(ns['PASTA'], 'LOG_K17.txt')
ns['ACHADOS'].clear()
try:
    ns['principal']()
    rodou = True
except Exception as e:
    rodou = False
    print('   ', type(e).__name__, e)
_time.sleep = _sleep
confere(rodou, 'principal() vai até o fim mesmo com todas as partes falhando')
for _n in ('deleteAsset', 'createAsset', 'startProcessing'):
    try:
        getattr(mod_ee.data, _n)()
        confere(False, f'trava: ee.data.{_n} continuou liberado')
    except RuntimeError:
        confere(True, f'trava: ee.data.{_n} bloqueado')
try:
    mod_ee.batch.Task().start()
    confere(False, 'trava: Task.start continuou liberado')
except RuntimeError:
    confere(True, 'trava: Task.start bloqueado')
partes = [a['parte'] for a in ns['ACHADOS']]
confere(partes == ['P1', 'P2', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'] and
        all(a['status'] == 'NÃO EXECUTADO' for a in ns['ACHADOS']), f'cada parte registrada como NÃO EXECUTADO {partes}')
confere(os.path.exists(ns['PASTA'] + '.zip') and os.path.exists(os.path.join(ns['PASTA'], 'K17_RESUMO.csv')),
        'zip e K17_RESUMO.csv gerados')
log_txt = open(ns['LOG'], encoding='utf-8').read()
confere('VALIDAÇÃO FINAL PENDENTE' in log_txt and 'APROVADA' not in log_txt.split('RESULTADO FINAL')[1],
        'sem dados não há aprovação')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
