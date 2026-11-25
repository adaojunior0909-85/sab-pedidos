# Teste de fumaça (sem Earth Engine) da 08 v4 e do 01: executa as seções novas e alteradas com um módulo `ee`
# FALSO (objetos encadeáveis que não calculam nada) e respostas fixas do getInfo por rótulo, montadas com os números
# reais da auditoria (LOG_COMPLETO, auditoria J). Pega erros de Python/pandas no código que roda no Colab
# (nomes, colunas, formatos, fluxo de status); NÃO valida as chamadas do Earth Engine em si.
# Rodar: python3 testes/fumaca_08_01.py  (a partir da pasta do pacote)
import os
import re
import sys
import tempfile
import types

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(AQUI, '..')
J5_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dados', 'J5_tmax_2026.csv')   # cópia da auditoria J
FALHAS = []


def confere(cond, msg):
    print(('  ok   ' if cond else '  FALHA ') + msg)
    if not cond:
        FALHAS.append(msg)


class Fake:
    """Objeto do Earth Engine falso: todo método existe e devolve outro Fake."""
    def __init__(self, nome='ee'):
        self._nome = nome

    def __getattr__(self, k):
        if k.startswith('__'):
            raise AttributeError(k)
        return Fake(f'{self._nome}.{k}')

    def __call__(self, *a, **k):
        return Fake(self._nome + '()')

    def getInfo(self):
        raise RuntimeError(f'getInfo sem resposta preparada: {self._nome}')


EXISTENTES = set()
PROPS_ASSET = {}
T_NATIVO = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
T_EXPORTADO = [T_NATIVO[0], 0, T_NATIVO[2] - 12 * T_NATIVO[0], 0, T_NATIVO[4], T_NATIVO[5] - 12 * T_NATIVO[4]]


def fazer_ee():
    ee = types.ModuleType('ee')
    ee.__version__ = 'falso'

    class Data:
        def getAsset(self, caminho):
            if caminho.split('/')[-1] in EXISTENTES or caminho in EXISTENTES:
                return {'type': 'IMAGE', 'properties': PROPS_ASSET.get(caminho.split('/')[-1], {})}
            raise Exception(f'Asset not found: {caminho}')

        def getTaskList(self):
            return []

    ee.data = Data()
    ee.batch = types.SimpleNamespace(Task=type('Task', (), {}), Export=Fake('ee.batch.Export'))
    ee.Initialize = lambda **k: None
    ee.Authenticate = lambda **k: None
    ee.__getattr__ = lambda nome: Fake(f'ee.{nome}')
    return ee


sys.modules['ee'] = fazer_ee()

# -------------------------------------------------------------------------------------------------
# Respostas preparadas (por rótulo do gi)
# -------------------------------------------------------------------------------------------------
R172 = list(range(1, 121)) + list(range(123, 241, 3)) + list(range(252, 385, 12))
R209 = [0] + list(range(1, 121)) + list(range(123, 241, 3)) + list(range(243, 385, 3))


def ms(d):
    return int(pd.Timestamp(d, tz='UTC').timestamp() * 1000)


def horas_rodada(dia):
    if dia < '2016-07-24':
        return list(range(3, 37, 3))
    if dia < '2019-06-13':
        return ([0] if dia < '2017-02-08' else []) + R172
    return R209


def resp_horas_bloco(ini):
    c, h = [], []
    for d in pd.date_range(ini, periods=10):
        for hora_rodada in (0, 6, 12, 18):
            cm = ms(d.strftime('%Y-%m-%d')) + hora_rodada * 3600000
            for x in horas_rodada(d.strftime('%Y-%m-%d')):
                c.append(cm)
                h.append(x)
    return {'list': [c, h]}


j5 = pd.read_csv(J5_CSV, sep=';', decimal=',', encoding='utf-8-sig', index_col='dia')
DIAS_26 = [d.strftime('%Y-%m-%d') for d in pd.date_range('2026-01-01', '2026-11-01')]
ERA5_EXTRA = []   # dias publicados depois de uma lacuna (caso da correção 21/10 18h)
VERS_26 = {d: ('provisoria_era5' if d <= '2026-10-06' else 'provisoria_gfs') for d in DIAS_26}
ALG_26 = 'V1.3'
ORD = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']
CPC = pd.DataFrame([{'ano': a, 'Trimestre': t, 'RONI_2c': round(0.37 * ((a * 12 + i) % 7) - 1.0, 2)}
                    for a in range(1950, 1953) for i, t in enumerate(ORD)])


def resposta(rotulo):
    if rotulo == 'inventário 2026':
        rod = ms('2026-10-07')
        cols = [[ms(d) for d in DIAS_26], [VERS_26[d] for d in DIAS_26], [ALG_26] * len(DIAS_26),
                [rod if VERS_26[d] != 'provisoria_era5' else -1 for d in DIAS_26], [''] * len(DIAS_26),
                [''] * len(DIAS_26), [''] * len(DIAS_26), [''] * len(DIAS_26)]
        return {'list': cols}
    if rotulo == 'ERA5 datas':
        # [21/10 18h] D14 lê a lista de datas do ERA5 e usa o último dia contínuo
        dias = [d.strftime('%Y-%m-%d') for d in pd.date_range('2026-09-01', '2026-10-06')] + ERA5_EXTRA
        return [ms(d) for d in dias]
    if rotulo.startswith('horas GFS '):
        return resp_horas_bloco(rotulo.split()[-1])
    if rotulo == 'metadados da matriz V2.1':
        feats = []
        for m in range(1, 13):
            bandas = [{'id': f'{v}_{e}_{f}_{fx}', 'data_type': {'precision': 'float'}}
                      for v in ('pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs') for e in 'ms' for f in ('sicsb', 'gfs')
                      for fx in ('L1', 'L2a5', 'L6a10', 'L11a15')]
            bandas += [{'id': f'n_{fx}', 'data_type': {'type': 'PixelType', 'precision': 'float'}}
                       for fx in ('L1', 'L2a5', 'L6a10', 'L11a15')]
            props = {'versao_matriz': 'V2.1', 'modelo_gfs': 'GFS v16', 'inicio_rodadas': '2021-03-23',
                     'fim_dias': '2025-12-31', 'mes_referencia': m, 'leads_L1': '1', 'leads_L2a5': '2,3,4,5',
                     'leads_L6a10': '6,7,8,9,10', 'leads_L11a15': '11,12,13,14,15', 'metodo_pr': 'soma_blocos_6h',
                     'metodo_rs': 'media_blocos_6h', 'janela': '(00Z,24Z] UTC do dia previsto; rodada 00Z de D-(L-1)',
                     'gerado_em': '2026-10-21T00:00:00+00:00', 'n_pares_L1': 1500, 'n_pares_L2a5': 6000,
                     'n_pares_L6a10': 7400, 'n_pares_L11a15': 7300}
            feats.append({'id': f'projects/clima-492922/assets/SICSB_MATRIZ_GFS_V2/Matriz_GFS_{m:02d}',
                          'bands': bandas, 'properties': props})
        return {'type': 'ImageCollection', 'features': feats}
    if rotulo.startswith('contagens n_* '):
        out = {}
        for fx, (a, b) in zip(('L1', 'L2a5', 'L6a10', 'L11a15'), ((60, 140), (240, 560), (300, 700), (300, 700))):
            out.update({f'frac_{fx}_max': 0.0, f'frac_{fx}_min': 0.0, f'n_{fx}_min': a, f'n_{fx}_max': b})
        return out
    if rotulo.startswith('gradientes V2.1 x V1'):
        return {'g2_gfs': 0.0042, 'g2_br': 0.010, 'g1_gfs': 0.0023, 'g1_br': 0.010}
    if rotulo.startswith('radiação V2.1 x V1'):
        return {'rs2_gfs': 21.0, 'rs2_br': 20.0, 'rs1_gfs': 22.6, 'rs1_br': 20.0}
    if rotulo == 'RONI_CPC_v6':
        f = []
        for _, r in CPC.iterrows():
            mes = ORD.index(r['Trimestre']) + 1
            f.append({'properties': {'ano': float(r['ano']), 'mes': mes, 'Trimestre': r['Trimestre'],
                                     'RONI': round(r['RONI_2c'], 1), 'RONI_2c': r['RONI_2c'], 'Fonte': 'CPC_ERSSTv6',
                                     'data_ms': ms(f'{int(r["ano"])}-{mes:02d}-01'),
                                     't_ms': ms(f'{int(r["ano"])}-{mes:02d}-01')}})
        return {'features': f}
    if rotulo == 'chave do painel':
        return {'features': [{'properties': {'ano': 1950, 'mes': m, 'chave_painel': f'1950_{m:02d}'}} for m in (1, 2, 3)]}
    if rotulo == 'projeção da máscara':     # [revisão B-02] origem própria do asset: 12 pixels a oeste e ao norte
        return {'type': 'Projection', 'crs': 'EPSG:4326', 'transform': T_EXPORTADO}
    if rotulo == 'contagem da máscara':
        return {'n_classe_1': 70364, 'n_classe_2': 204, 'n_classe_3': 229, 'n_classe_4': 880}
    if rotulo.startswith('máscara x classes'):       # [V4.1 K1a] 3 pixels B iguais ao BR-DWGD no dia: ignorados
        return {'dif': 0, 'coinc': 3}
    if rotulo.startswith('BR-DWGD '):
        return 1
    if rotulo.startswith('classes '):
        return {'A': 70364.0, 'B': 204.0, 'C': 1109.0, 'D': 73.0}
    if rotulo == 'nomes UF':
        return ['Acre', 'Amazonas', 'Para', 'Distrito Federal', 'Name Unknown', 'Name Unknown']
    if rotulo == 'homônimos':
        return {'list': [['Amazonas', 'Amazonas', 'Amazonas', 'Para', 'Distrito Federal', 'Amazonas'],
                         ['Colombia', 'Peru', 'Venezuela', 'Suriname', 'Mexico', 'Peru']]}
    if rotulo.startswith('Tmax 20'):          # a J5 vai até hoje + 40 dias: de 22/11 em diante chega a 2027 (mês sem dias = vazio)
        mes = rotulo.split()[-1]
        f = []
        for d in [x for x in DIAS_26 if x.startswith(mes)]:
            p = {'t': ms(d), 'versao': VERS_26[d], 'alg': ALG_26}
            if d in j5.index:
                p.update({'tmax_C_max': j5.loc[d, 'tmax_max'], 'tmax_C_mean': j5.loc[d, 'tmax_media'],
                          'acima40_mean': j5.loc[d, 'pct_acima40'] / 100, 'acima42_mean': j5.loc[d, 'pct_acima42'] / 100})
            elif d != '2026-03-03':      # um dia sem estatísticas (como um dia todo mascarado)
                p.update({'tmax_C_max': 40.0, 'tmax_C_mean': 32.0, 'acima40_mean': 0.0, 'acima42_mean': 0.0})
            f.append({'type': 'Feature', 'properties': p})
        return {'type': 'FeatureCollection', 'features': f}
    if rotulo.endswith(' contagem'):
        return {b: 70907 for b in BANDAS_ATUAIS}
    if rotulo.endswith(' amostra'):
        rng = np.random.default_rng(7)
        return {'features': [{'properties': {b: float(x) for b, x in zip(BANDAS_ATUAIS, rng.lognormal(0, 0.5, len(BANDAS_ATUAIS)))}}
                             for _ in range(2498)]}
    if rotulo.startswith('coerência '):
        d = rotulo.split()[-1]
        base = {k: 0 for k in ('UR_fora_0_100', 'chuva_negativa', 'ETo_negativa', 'vento_negativo', 'radiacao_negativa',
                               'Tmax_menor_Tmin', 'ETreal_maior_ETo', 'transp_maior_ETreal', 'umid100_acima_0_9',
                               'umid5_acima_0_9', 'Tmax_igual_-20')}
        base['pixels'] = 70459 if d >= '2026-10-07' else 70455
        return base
    if rotulo.startswith('faixas '):
        return {'pr_mm_min': 0, 'pr_mm_max': 100}
    if rotulo.startswith('máscara '):
        d = rotulo.split()[-1]
        return {'so_dia': 4 if d >= '2026-10-07' else 0, 'so_ref': 0, 'fracao': 1 if d == '2026-10-06' else 0}
    if rotulo.startswith('locais '):
        if rotulo.endswith('2026-10-06'):
            return {'longitude': [-50.05], 'latitude': [-30.05], 'so_dia': [0], 'fracao': [1]}
        return {'longitude': [-48.05, -48.15, -35.05, -35.15], 'latitude': [-25.55, -25.55, -8.95, -9.05],
                'so_dia': [1, 1, 1, 1], 'fracao': [0, 0, 0, 0]}
    raise RuntimeError(f'sem resposta preparada para o rótulo {rotulo!r}')


BANDAS_ATUAIS = []
ROTULOS = []


def gi_falso(obj, rotulo='', tentativas=4):
    ROTULOS.append(rotulo)
    return resposta(rotulo)


# -------------------------------------------------------------------------------------------------
# Carrega a 08 até o laço de execução (sem rodar as seções) e troca o gi
# -------------------------------------------------------------------------------------------------
fonte = open(os.path.join(V4, '08_auditoria_completa_SAB.py'), encoding='utf-8').read()
corte = fonte.index('\ninicio_total = time.time()')
dir_tmp = tempfile.mkdtemp()
os.chdir(dir_tmp)
ns = {'__name__': 'auditoria08'}
exec(compile(fonte[:corte], '08_auditoria_completa_SAB.py', 'exec'), ns)
ns['gi'] = gi_falso
ns['inicio_total'] = 0.0
print(f'\n08 carregada (pasta de saída {ns["PASTA"]})')
confere(re.search(r'auditoria_SAB_\d{8}_\d{6}$', ns['PASTA']) is not None, '[M08-01] pasta com segundos')
confere(os.path.getsize(ns['ARQ_LOG']) > 0, '[M08-01] log criado e escrito')


def roda(nome, fn, *a):
    n0 = len(ns['ACHADOS'])
    try:
        fn(*a)
    except Exception as e:
        import traceback
        traceback.print_exc()
        confere(False, f'{nome} levantou {type(e).__name__}: {e}')
        return []
    novos = ns['ACHADOS'][n0:]
    confere(bool(novos), f'{nome} rodou: ' + '; '.join(f'{x["codigo"]}={x["status"]}' for x in novos))
    return novos


def status(achados, cod):
    return next((x['status'] for x in achados if x['codigo'] == cod), None)


print('\n[D14] antes da etapa 5b (dias V1.3)')
a = roda('secao_d14', ns['secao_d14'])
confere(status(a, 'D14') == 'INFO' and 'aguardando motor V1.5' in a[0]['resultado'], 'D14 INFO aguardando motor V1.5')
# mesmo cenário, mas com o ERA5 publicando 2026-10-09 depois de uma lacuna em 10-07 e 10-08: resultado igual
ERA5_EXTRA[:] = ['2026-10-09']
a = roda('secao_d14 (ERA5 com lacuna)', ns['secao_d14'])
confere(status(a, 'D14') == 'INFO' and 'aguardando motor V1.5' in a[0]['resultado'],
        'D14 com lacuna no ERA5: usa o último dia contínuo (10-06), resultado igual')
ERA5_EXTRA[:] = []

print('\n[E6] sem a matriz e com a matriz V2.1 conforme')
a = roda('secao_e6 (sem matriz)', ns['secao_e6'])
confere(status(a, 'E6') == 'ATENÇÃO' and 'Rode o 03' in a[0]['acao_sugerida'], 'E6 ATENÇÃO rode o 03')
EXISTENTES.add('SICSB_MATRIZ_GFS_V2')
a = roda('secao_e6', ns['secao_e6'])
confere(status(a, 'E6-estrutura') == 'OK' and status(a, 'E6-detalhe') == 'OK' and status(a, 'E6-Rs') == 'OK',
        'E6 estrutura/detalhe/Rs OK (razão 0,42 x 0,23; Rs 1,05/1,13 = 0,93)')

print('\n[H5] sem o asset e com o asset igual ao CPC')
a = roda('secao_h5 (sem asset)', ns['secao_h5'])
confere(status(a, 'H5') == 'ATENÇÃO', 'H5 ATENÇÃO rode o 02')
EXISTENTES.add('RONI_CPC_v6')
_read_csv = pd.read_csv
ns['pd'].read_csv = lambda url, *a, **k: CPC.copy() if str(url).startswith('https://') else _read_csv(url, *a, **k)
a = roda('secao_h5', ns['secao_h5'])
ns['pd'].read_csv = _read_csv
confere(status(a, 'H5') == 'OK', 'H5 OK')

print('\n[Q1] sem o asset e com a máscara conforme')
a = roda('secao_q1 (sem asset)', ns['secao_q1'])
confere(status(a, 'Q1') == 'ATENÇÃO' and 'Rode o 01' in a[0]['acao_sugerida'], 'Q1 ATENÇÃO rode o 01')
EXISTENTES.add('SAB_MASCARA_QUALIDADE')
PROPS_ASSET['SAB_MASCARA_QUALIDADE'] = {'versao_mascara': 'Q1', 'dia_referencia': '2001-01-15', 'n_classe_1': 70364,
                                        'dias_classes': '2001-01-15,1961-01-15,1981-07-01,2017-07-15,2025-01-15',
                                        'n_classe_2': 204, 'n_classe_3': 229, 'n_classe_4': 880, 'gerado_em': 'x'}
a = roda('secao_q1', ns['secao_q1'])
confere(status(a, 'Q1') == 'OK', 'Q1 OK')
confere('(coincidência, ignorados): 3' in open(ns['ARQ_LOG'], encoding='utf-8').read(),
        'Q1: 3 coincidências B -> A mostradas e ignoradas (V4.1 K1a)')

print('\n[J1, J3, J5]')
a = roda('secao_j1', ns['secao_j1'])
confere(status(a, 'J1') == 'INFO' and status(a, 'J1-2026') is None, 'J1 INFO (B 204, C 1.109); sem definitivas de 2026')
a = roda('secao_j3', ns['secao_j3'])
confere(status(a, 'J3') == 'INFO' and 'Name Unknown' not in a[0]['resultado'], 'J3 INFO sem "Name Unknown"')
a = roda('secao_j5', ns['secao_j5'])
confere(status(a, 'J5a') == 'ATENÇÃO' and status(a, 'J5b') == 'ATENÇÃO' and status(a, 'J5c') == 'INFO',
        'J5a (4 dias > 44,8) e J5b (+2,40 °C) ATENÇÃO; J5c INFO sem CSV anterior')
csv_novo = os.path.join(ns['PASTA'], 'J5_tmax_2026.csv')
t = pd.read_csv(csv_novo, sep=';', decimal=',', encoding='utf-8-sig', index_col='dia')
confere(list(t.columns[:2]) == ['versao', 'alg'] and len(t) == len(DIAS_26) and t.loc['2026-10-07', 'tmax_max'] == 44.12,
        'J5_tmax_2026.csv no formato da J (lido de volta)')
confere(np.isnan(t.loc['2026-03-03', 'tmax_max']), 'dia sem estatísticas fica NaN, sem quebrar')
# segunda execução: os dias 07-10/10 viraram ERA5; o CSV desta execução vira o "anterior"
ns['J5_CSV_ANTERIOR'] = csv_novo
for d in ('2026-10-07', '2026-10-08', '2026-10-09', '2026-10-10'):
    VERS_26[d] = 'provisoria_era5'
j5.loc[['2026-10-07', '2026-10-08', '2026-10-09', '2026-10-10'], 'tmax_max'] = 41.6
a = roda('secao_j5 (com CSV anterior)', ns['secao_j5'])
confere(status(a, 'J5c') == 'ATENÇÃO' and '4 dia(s)' in next(x['resultado'] for x in a if x['codigo'] == 'J5c'),
        'J5c compara 4 datas GFS x ERA5 e acusa viés > 2 °C')
for d in ('2026-10-07', '2026-10-08', '2026-10-09', '2026-10-10'):
    VERS_26[d] = 'provisoria_gfs'

print('\n[F5] transições dia a dia (blocos de 10 dias, só metadados)')
a = roda('transicoes_gfs', ns['transicoes_gfs'])
confere(status(a, 'F5') == 'OK' and 'desde 2016-07-24' in a[0]['resultado'] and 'desde 2019-06-13' in a[0]['resultado'],
        f'F5 OK: 384 h desde 2016-07-24 e 3 h desde 2019-06-13 ({a[0]["resultado"][:120]})')
n_horas = sum(1 for r in ROTULOS if r.startswith('horas GFS '))
confere(n_horas <= 40, f'F5 usa {n_horas} consultas de metadados (a versão antiga fazia uma por dia)')

print('\n[E] percentis por amostragem')
BANDAS_ATUAIS[:] = ['fator_pr', 'fator_u2', 'fator_Rs', 'dif_Tmax', 'dif_Tmin', 'dif_RH']
p = ns['percentis'](Fake('img'), 'clima 01')
confere(all(f'{b}_p{q}' in p for b in BANDAS_ATUAIS for q in (1, 5, 50, 95, 99)), 'chaves _p1.._p99 como antes')
confere(p['fator_pr_count'] == 70907 and p['fator_pr_n_amostra'] == 2498, 'contagem total e tamanho da amostra')
confere(p['fator_pr_p1'] < p['fator_pr_p50'] < p['fator_pr_p99'], 'percentis exatos crescentes (não colapsam)')

print('\n[D10] máscara x SAB_2025_12_31 nos dias amostrados')
inv = pd.DataFrame({'dia': pd.to_datetime(['2025-12-31', '2026-10-06', '2026-10-07', '2026-10-10']),
                    'par': ['definitiva | V1.0', 'provisoria_era5 | V1.3', 'provisoria_gfs | V1.3', 'provisoria_gfs | V1.3'],
                    'alg': ['V1.0', 'V1.3', 'V1.3', 'V1.3']})
ns['CONTEXTO']['inv'] = inv
ns['DIAS_AMOSTRA_HIST'] = ['1961-01-01', '2025-12-31']
a = roda('coerencia_fisica', ns['coerencia_fisica'])
confere(status(a, 'D10') == 'INFO', 'D10 INFO: só dias V1.3 diferem (4 pixels a mais nos GFS; 1 de fração no ERA5)')
coords = pd.read_csv(os.path.join(ns['PASTA'], 'D_mascara_coordenadas.csv'), sep=';', decimal=',', encoding='utf-8-sig')
confere(len(coords) == 9 and (coords['tipo'] == 'fração de máscara diferente').sum() == 1,
        f'coordenadas listadas ({len(coords)}: 4 por dia GFS e 1 de fração, até 50)')
confere(status(a, 'D11-UR_fora_0_100') == 'OK', 'D11 continua funcionando com contagens unweighted')

print('\n[M08-08 / M08-01] ACEITOS no resumo e resumo gravado')
ns['achado']('H2', 'ATENÇÃO', 'Retângulo tropical', '9,692 km²')
ns['CONTEXTO']['versoes_baselines'] = {'B1.1'}
ns['achado']('I1', 'ATENÇÃO', 'Baselines', '12 imagens B1.1')
ns['gravar_resumo']('J5')
res = pd.read_csv(os.path.join(ns['PASTA'], 'RESUMO_ACHADOS.csv'), sep=';', encoding='utf-8-sig')
confere(res.loc[res['codigo'] == 'H2', 'status'].iloc[0] == 'INFO' and
        res.loc[res['codigo'] == 'H2', 'status_original'].iloc[0] == 'ATENÇÃO', 'H2 INFO no resumo, original ATENÇÃO')
confere(res.loc[res['codigo'] == 'I1', 'status'].iloc[0] == 'INFO', 'I1 INFO (só B1.1)')
log_txt = open(ns['ARQ_LOG'], encoding='utf-8').read()
confere('EXECUÇÃO INTERROMPIDA NA SEÇÃO J5' in log_txt, 'resumo registra a seção interrompida')
confere(os.path.isfile(ns['PASTA'] + '.zip'), '.zip gravado')
confere(log_txt.count('AUDITORIA COMPLETA DO SISTEMA SAB') == 1, 'um cabeçalho só no log')

# -------------------------------------------------------------------------------------------------
# 01: carrega até a execução, troca gi/rr e roda o main() em simulação
# -------------------------------------------------------------------------------------------------
print('\n[01] simulação com ee falso')
EXISTENTES.clear()
fonte01 = open(os.path.join(V4, '01a_mascara_qualidade_SIMULACAO.py'), encoding='utf-8').read()
corte01 = fonte01.index('\ntry:\n    main()')
n1 = {'__name__': 'mascara01'}
exec(compile(fonte01[:corte01], '01a_mascara_qualidade_SIMULACAO.py', 'exec'), n1)
confere(re.search(r'mascara_qualidade_\d{8}_\d{6}$', n1['PASTA']) is not None, 'pasta com segundos')
LONS = [-73.95 + 0.1 * i for i in range(1109)]
T_GRAVADO = [T_EXPORTADO]


def resposta01(rotulo):
    if rotulo == 'C completo x C da J1':
        return {'C_mascara': 1109, 'C_logica_J1': 1109}
    if rotulo.startswith('conferência '):        # [V4.1 K1a] coincidências num dia de inverno não reprovam
        return {'estrutura_diferente': 0, 'B_iguais_no_dia': 7 if '1981-07-01' in rotulo else 0}
    if rotulo == 'centros dos pixels C':
        return {'longitude': LONS, 'latitude': [-10.0] * 1109}
    if rotulo == 'centros dentro do Brasil':
        return list(range(48))                   # [V4.1 K1d] 48 centros C no Brasil
    if rotulo.startswith('rasterização '):
        metodo = rotulo.split()[-1]
        val = (lambda i: 1 if i < 49 else 0) if metodo == 'paint' else (lambda i: 1 if i < 48 else 0)
        return {'features': [{'properties': {'i': i, 'first': val(i)}} for i in range(1109)]}
    if rotulo == 'contagem como na J1':
        return {'A': 70364.0, 'B': 204.0, 'C': 1109.0, 'B_ref': 204.0}
    if rotulo == 'dias em B por pixel da união':     # [V4.1 revisão V41-06]; [correção 20/10 23h] indicadores dias_k
        return {'U': 301, 'B_0': 301, 'A_0': 0, 'B_1': 301, 'A_1': 0, 'B_2': 296, 'A_2': 5, 'B_3': 301, 'A_3': 0,
                'B_4': 301, 'A_4': 0, 'dias_0': 0, 'dias_1': 0, 'dias_2': 0, 'dias_3': 0, 'dias_4': 5, 'dias_5': 296,
                'algum_dia_sem_classe': 0}
    if rotulo in ('contagem por classe', 'contagem do asset gravado'):
        return {'n_classe_1': 70900, 'n_classe_2': 301, 'n_classe_3': 48, 'n_classe_4': 1060}
    if rotulo == 'gravado x calculado':
        return {'dif': 0}
    if rotulo == 'projeção gravada':
        return {'type': 'Projection', 'crs': 'EPSG:4326', 'transform': T_GRAVADO[0]}
    if rotulo == 'por estado':
        return {'features': [{'properties': {'ADM1_NAME': n, 'n_classe_4': 0, 'n_classe_1': a, 'n_classe_2': b,
                                             'n_classe_3': c}}
                             for n, a, b, c in (('Para', 10004, 77, 15), ('Amazonas', 12766, 0, 35),
                                                ('Name Unknown', 0, 0, 0))]}
    raise RuntimeError(f'01: sem resposta para {rotulo!r}')


n1['gi'] = lambda obj, rotulo='', tentativas=4: resposta01(rotulo)
try:
    n1['main']()
    ok01 = True
except Exception:
    import traceback
    traceback.print_exc()
    ok01 = False
confere(ok01, '01 main() em simulação termina sem erro')
log01 = open(n1['LOG'], encoding='utf-8').read()
confere('rasterização paint: 1 pixel(s) C em desacordo' in log01 and 'método aceito: reduceToImage' in log01,
        'paint discordante é recusado; reduceToImage aceito')
confere('receita da J1 reproduzida dentro da tolerância' in log01 and 'SIMULAR = True: nada foi gravado' in log01,
        'contagens = J1 e nada gravado')
confere('ℹ️ 7 caso(s) de pixel B igual ao BR-DWGD' in log01 and 'estrutura (A+B, C e D) idêntica' in log01,
        'coincidências da K1a viram ℹ️ e não reprovam (V4.1)')
confere('ℹ️ classe 3' not in log01 and 'ℹ️ classe 4' not in log01, 'classes 3 = 48 e 4 = 1.060: sem ℹ️ (V4.1 K1d)')
confere('por número de dias em B: {4: 5, 5: 296}' in log01 and 'em só 1 ou 2' not in log01
        and '1981-07-01: dos 301 pixels da união B, 296 em B, 5 em A, 0 sem classe neste dia' in log01
        and 'sem classe em algum' not in log01,
        'histograma de dias em B por pixel, sem pixel raro (V41-06)')
confere('só 2001-01-15 = 204.0; união dos 5 dias = 204.0' in log01, 'B da receita J1: dia de referência x união (V41-10)')
confere('Sem ⚠️: rode o 01b para gravar.' in log01, 'mensagem final manda rodar o 01b')
uf = pd.read_csv(os.path.join(n1['PASTA'], 'Q1_por_estado.csv'), sep=';', decimal=',', index_col='ADM1_NAME')
confere(list(uf.columns) == ['A', 'B', 'C_dentro', 'C_fora', 'pct_nao_A'], 'Q1_por_estado.csv com as colunas certas')
confere('fora de todos os estados' in log01, 'linha "fora de todos os estados"')

# asset já existe com outra versão: para com ❌
EXISTENTES.add('SAB_MASCARA_QUALIDADE')
PROPS_ASSET['SAB_MASCARA_QUALIDADE'] = {'versao_mascara': 'Q0'}
try:
    n1['main']()
    parou = False
except RuntimeError as e:
    parou = 'Q0' in str(e)
confere(parou, 'asset existente com outra versão: para com ❌')
# asset Q1 gravado antes da v4.1 (sem dias_classes) e gravação: para com ❌ [V4.1 revisão V41-04]
PROPS_ASSET['SAB_MASCARA_QUALIDADE'] = {'versao_mascara': 'Q1'}
n1['SIMULAR'] = False
try:
    n1['main']()
    parou = False
except RuntimeError as e:
    parou = 'antes da v4.1' in str(e)
confere(parou, 'asset Q1 sem dias_classes e SIMULAR = False: para com ❌ (V41-04)')
# asset Q1 da v4.1 e gravação: não faz nada
PROPS_ASSET['SAB_MASCARA_QUALIDADE'] = {'versao_mascara': 'Q1',
                                        'dias_classes': '2001-01-15,1961-01-15,1981-07-01,2017-07-15,2025-01-15'}
n1['main']()
confere('já existe com versao_mascara = Q1: nada a fazer' in open(n1['LOG'], encoding='utf-8').read(),
        'asset Q1 da v4.1 existente e SIMULAR = False: nada a fazer')
# classes diferentes entre dias: para com ❌
EXISTENTES.clear()
n1['SIMULAR'] = True
n1['gi'] = lambda obj, rotulo='', tentativas=4: ({'estrutura_diferente': 3, 'B_iguais_no_dia': 0}
                                                if rotulo.startswith('conferência 1961') else resposta01(rotulo))
try:
    n1['main']()
    parou = False
except RuntimeError as e:
    parou = 'estrutura dos pixels' in str(e)
confere(parou, 'classes diferentes em 1961-01-15: para com ❌')


# [revisão B-04] classe 4 longe de ~880 (soma ponderada da J1) não bloqueia: só ℹ️
n1['gi'] = lambda obj, rotulo='', tentativas=4: (
    {'n_classe_1': 70900, 'n_classe_2': 301, 'n_classe_3': 48, 'n_classe_4': 700} if rotulo == 'contagem por classe'
    else {'U': 297, 'B_0': 297, 'A_0': 0, 'B_1': 296, 'A_1': 1, 'B_2': 296, 'A_2': 1, 'B_3': 296, 'A_3': 1,
          'B_4': 296, 'A_4': 1, 'dias_1': 1, 'dias_5': 296, 'algum_dia_sem_classe': 0}
    if rotulo == 'dias em B por pixel da união'
    else resposta01(rotulo))
n1['main']()
log01 = open(n1['LOG'], encoding='utf-8').read()
confere('ℹ️ classe 4 = 700' in log01 and 'Sem ⚠️: rode o 01b para gravar.' in log01,
        'classe 4 = 700: só ℹ️, gravação liberada (B-04/V4.1 K1d)')
confere('ℹ️ 1 pixel(s) B em só 1 ou 2 dos 5 dias' in log01, 'pixel B em 1 dia só: ℹ️ pedindo a saída (V41-06)')

# [correção 20/10 23h30] pixels da união sem classe num dia: ℹ️ à parte, fora do histograma, sem impedir a gravação
n1['gi'] = lambda obj, rotulo='', tentativas=4: (
    {'U': 301, 'B_0': 301, 'A_0': 0, 'B_1': 282, 'A_1': 0, 'B_2': 301, 'A_2': 0, 'B_3': 301, 'A_3': 0,
     'B_4': 301, 'A_4': 0, 'dias_5': 282, 'algum_dia_sem_classe': 19}
    if rotulo == 'dias em B por pixel da união' else resposta01(rotulo))
n1['main']()
log01 = open(n1['LOG'], encoding='utf-8').read()
confere('1961-01-15: dos 301 pixels da união B, 282 em B, 0 em A, 19 sem classe neste dia' in log01
        and 'ℹ️ 19 pixel(s) da união B sem classe em algum dos 5 dias' in log01 and '{5: 282}' in log01
        and 'Sem ⚠️: rode o 01b para gravar.' in log01, 'pixels sem classe num dia: ℹ️ à parte (correção 23h30)')

# [revisão B-01] gravação: asset com a origem própria (12 pixels inteiros) é aceito; meio pixel, não
PROPS_Q1 = {'versao_mascara': 'Q1', 'dia_referencia': '2001-01-15', 'metodo_centro': 'reduceToImage',
            'dias_classes': '2001-01-15,1961-01-15,1981-07-01,2017-07-15,2025-01-15',
            'n_classe_1': 70900, 'n_classe_2': 301, 'n_classe_3': 48, 'n_classe_4': 1060}


def aguardar_falso(task):
    EXISTENTES.add('SAB_MASCARA_QUALIDADE')
    PROPS_ASSET['SAB_MASCARA_QUALIDADE'] = dict(PROPS_Q1, gerado_em='x')
    return {'state': 'COMPLETED'}


n1['gi'] = lambda obj, rotulo='', tentativas=4: resposta01(rotulo)
n1['aguardar'] = aguardar_falso
for t_g, aceito, rot in ((T_EXPORTADO, True, 'origem própria do asset (12 pixels inteiros): gravado e conferido'),
                         ([T_NATIVO[0], 0, T_NATIVO[2] - 0.5 * T_NATIVO[0], 0, T_NATIVO[4], T_NATIVO[5]], False,
                          'meio pixel de deslocamento: para com ❌')):
    EXISTENTES.clear()
    PROPS_ASSET.pop('SAB_MASCARA_QUALIDADE', None)
    T_GRAVADO[0] = t_g
    n1['SIMULAR'] = False
    try:
        n1['main']()
        res = 'gravado e conferido' in open(n1['LOG'], encoding='utf-8').read()
    except RuntimeError as e:
        res = False if 'diferente da grade nativa' in str(e) else f'outro erro: {e}'
    confere(res is aceito, f'B-01 {rot}')
EXISTENTES.clear()
n1['SIMULAR'] = True

print(f'\n{"FUMAÇA OK" if not FALHAS else f"{len(FALHAS)} FALHA(S)"}')
sys.exit(1 if FALHAS else 0)
