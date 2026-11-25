# Teste offline do 09 (matriz EQM do motor V1.6): regras puras, o contrato com o motor e 09a x 09b.
# Rodar: python3 testes/teste_09.py
import ast
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, '..')
A = open(os.path.join(RAIZ, '09a_matriz_eqm_SIMULACAO.py'), encoding='utf-8').read()
B = open(os.path.join(RAIZ, '09b_matriz_eqm_GRAVACAO.py'), encoding='utf-8').read()
MOTOR = open(os.path.join(RAIZ, '05a_motor_sab_v1_6_SIMULACAO.py'), encoding='utf-8').read()
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


def carregar(fonte, consts, funcs):
    arv = ast.parse(fonte)
    def nomes(alvo):
        return [alvo.id] if isinstance(alvo, ast.Name) else [e.id for e in getattr(alvo, 'elts', []) if isinstance(e, ast.Name)]
    nos = [n for n in arv.body if (isinstance(n, ast.Assign) and len(n.targets) == 1
           and set(nomes(n.targets[0])) & consts)
           or (isinstance(n, ast.FunctionDef) and n.name in funcs)]
    import pandas as pd
    ns = {'pd': pd}
    exec(compile(ast.Module(body=nos, type_ignores=[]), '09', 'exec'), ns)
    return ns


C = carregar(A, {'NIVEIS_EQM', 'VARS_EQM', 'LIMITES', 'VERSAO_MATRIZ_EQM', 'ASSET_EQM', 'RAIZ', 'PROJETO', 'ANO_INI',
                 'ANO_FIM', 'SIMULAR', 'TOL_GRAVADO', 'TRANSFORM'},
             {'bandas_eqm', 'bandas_matriz', 'nomes_percentil', 'conferir_amostra', 'comparar_gravado', 'meses_faltando',
              'quantis_pontos', 'pid_de'})
M = carregar(MOTOR, {'NIVEIS_EQM', 'VARS_EQM', 'VERSAO_MATRIZ_EQM', 'ASSET_EQM'}, {'bandas_eqm', 'bandas_matriz_eqm'})

print('[contrato com o motor V1.6]')
confere(C['bandas_matriz']() == M['bandas_matriz_eqm'](), '85 bandas com os mesmos nomes e a mesma ordem do motor')
confere(C['VERSAO_MATRIZ_EQM'] == M['VERSAO_MATRIZ_EQM'] == 'E1', 'versão E1 nos dois')
confere(C['ASSET_EQM'] == M['ASSET_EQM'], 'mesmo asset')
confere((C['ANO_INI'], C['ANO_FIM']) == (1986, 2025), 'período 1986-2025 (o da climatologia SICSB_1986_2025)')
confere(C['nomes_percentil']('RH')[:3] == ['RH_p0', 'RH_p5', 'RH_p10'] and len(C['nomes_percentil']('u2')) == 21,
        'nomes do ee.Reducer.percentile na ordem dos níveis')
confere("'Matriz_EQM_{mm}'" in MOTOR.replace("f'{ASSET_EQM}/Matriz_EQM_{mm}'", "'Matriz_EQM_{mm}'") and
        "f'Matriz_EQM_{m:02d}'" in A, 'mesmo nome das imagens (Matriz_EQM_01 ... _12)')
confere("'versao_matriz_eqm': VERSAO_MATRIZ_EQM" in A and "get('versao_matriz_eqm') != VERSAO_MATRIZ_EQM" in MOTOR,
        'o 09 grava e o motor exige a propriedade versao_matriz_eqm')

print('[conferência da amostra]')


def linha(rh_era=None, desordem=False, pm=150.0):
    r = {'pr_max_br': pm}
    for v, (a, b) in (('RH', (30.0, 99.0)), ('u2', (0.2, 6.0))):
        for f in ('era', 'br'):
            q = [a + (b - a) * i / 20 for i in range(21)]
            if desordem and v == 'u2' and f == 'era':
                q[5], q[6] = q[6], q[5]
            for p, x in zip(C['NIVEIS_EQM'], q):
                r[f'{v}_{f}_p{p:03d}'] = x
    if rh_era is not None:
        r['RH_era_p100'] = rh_era
    return r


confere(C['conferir_amostra']([linha() for _ in range(10)]) == [], 'amostra boa: sem problemas')
confere(any('fora de ordem' in p for p in C['conferir_amostra']([linha(desordem=True)])), 'quantis fora de ordem acusados')
confere(any('RH_era' in p for p in C['conferir_amostra']([linha(rh_era=104.0)])), 'UR acima de 100 acusada')
confere(any('pr_max_br' in p for p in C['conferir_amostra']([linha(pm=1200.0)])), 'chuva máxima absurda acusada')
r = linha()
del r['u2_br_p050']
confere(any('faltam' in p for p in C['conferir_amostra']([r])), 'banda ausente acusada')
confere(C['conferir_amostra']([]) == ['nenhum ponto amostrado'], 'amostra vazia acusada')

print('[gravado x calculado e meses que faltam]')
calc = {'a': linha(), 'b': linha()}
grav = {'a': dict(linha(), RH_br_p050=linha()['RH_br_p050'] + 1.5), 'b': dict(linha(), RH_br_p050=10.0, u2_era_p100=7.0)}
confere(C['comparar_gravado'](calc, grav) == (2, 2), 'v3: UR 1,5 dentro da tolerância de 2; UR e vento longe acusados')
import numpy as np
rng = np.random.default_rng(2)
import pandas as pd
dfq = pd.DataFrame({'pid': ['p1'] * 100 + ['p2'] * 40, 'RH_era': rng.uniform(30, 90, 140), 'u2_era': rng.gamma(2, 1, 140),
                    'RH_br': rng.uniform(40, 99, 140), 'u2_br': rng.gamma(2, 0.8, 140), 'pr_br': rng.gamma(0.5, 9, 140)})
qp = C['quantis_pontos'](dfq)
confere(abs(qp['p1']['RH_br_p050'] - np.median(dfq['RH_br'][:100])) < 1e-9 and qp['p2']['RH_era_p050'] is None
        and C['conferir_amostra']([qp['p1']]) == [], 'v3: quantis dos dias em Python; pixel com menos de 60 dias fica vazio')
confere(C['pid_de'](-51.65, -26.15) == C['pid_de'](-51.6499, -26.1501), 'v3: mesmo pixel, mesmo identificador')
confere(C['meses_faltando']([], {}) == list(range(1, 13)), 'coleção vazia: os 12 meses')
nomes = [f'Matriz_EQM_{m:02d}' for m in range(1, 13)]
v = {n: 'E1' for n in nomes}
v['Matriz_EQM_03'] = 'E0'
confere(C['meses_faltando'](nomes[:-1], v) == [3, 12], 'mês de versão antiga e mês ausente são refeitos')

print('[09a x 09b]')
la, lb = A.splitlines(), B.splitlines()
dif = [i for i, (x, y) in enumerate(zip(la, lb)) if x != y]
confere(len(la) == len(lb) and len(dif) == 2 and dif[0] == 0, f'só a linha 1 e o SIMULAR mudam ({dif})')
confere('SIMULAR = True' in la[dif[1]] and 'SIMULAR = False' in lb[dif[1]], 'SIMULAR True no 09a e False no 09b')
codigo_09 = '\n'.join(l for l in A.splitlines() if not l.lstrip().startswith('#'))
confere('SAB_V1' not in codigo_09, 'o código do 09 nem cita o banco SAB_V1 (só o comentário diz que não o altera)')
confere("ee.Reducer.percentile(list(NIVEIS_EQM), None, None, None, MAX_RAW)" in A and 'MAX_RAW = 2000' in A,
        'percentil exato até 2.000 valores por pixel (40 anos x 31 dias)')
confere("return ee.Image(ee.Image.cat([rh, u2]).copyProperties(" in A and
        "return ee.Image(ee.Image.cat([rh, u2, pr]).updateMask(valido).copyProperties(" in A,
        'v3a: era_prep e br_prep devolvem ee.Image (copyProperties devolve Element no Python)')
confere('shardSize=32' in A and 'tileScale=16' in A and 'raise Pesado' in A,
        'v2: exportação em blocos de 32 px e amostra com tileScale 16, dividindo os pontos se faltar memória')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
