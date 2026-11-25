# Teste offline do 02_auditoria_roni_cpc.py (V4: M02-02 e M02-03). Sem Earth Engine e sem rede.
# As funções são tiradas do próprio script (ast), então o teste exercita o código que vai ao Colab.
# "Arquivo do CPC" simulado: RONI_2c real de 1950-2025 (auditoria/H_roni_antigo_x_cpc.csv, baixado
# pelo 08 em 20/10/2026) + 2026 simulado (JAS = 1,69, como no H3 do 08; os outros meses de 2026
# são valores de 2 casas compatíveis com a tabela, inventados só para o teste).
# Rodar: python3 testes/teste_02.py  (a partir da pasta do pacote)
import ast
import io
import sys

import numpy as np
import pandas as pd

import os
AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, '..', '02_auditoria_roni_cpc.py')
H4_CSV = os.path.join(AQUI, 'dados', 'H_roni_antigo_x_cpc.csv')   # saída real da 08 (seção H4)
NOMES = {'ORDEM', 'noaa_data', 'URL_TABELA_CPC', 'AUTO_ESTACOES_NOVAS', 'ESTACOES_REVISAVEIS',
         'empate_2c', 'arred_sem_empate', 'ler_tabela', 'conciliar_oficial', 'linhas_tabela',
         'conferir_leitura', 'acl_sem_dono', 'acl_resumo'}


def carregar():
    arvore = ast.parse(open(SCRIPT, encoding='utf-8').read())
    corpo = []
    for n in arvore.body:
        if isinstance(n, ast.FunctionDef) and n.name in NOMES:
            corpo.append(n)
        elif isinstance(n, ast.Assign) and any(getattr(t, 'id', None) in NOMES for t in n.targets):
            corpo.append(n)
    ns = {'np': np, 'pd': pd, 'io': io}
    exec(compile(ast.Module(body=corpo, type_ignores=[]), SCRIPT, 'exec'), ns)
    faltam = NOMES - set(ns)
    assert not faltam, f'não achei no script: {faltam}'
    return ns


S = carregar()
ORDEM = S['ORDEM']
FALHAS = []


def ok(cond, msg):
    print(('  ok   ' if cond else '  FALHA ') + msg)
    if not cond:
        FALHAS.append(msg)


def espera_erro(fn, *trechos, msg=''):
    try:
        fn()
    except ValueError as e:
        txt = str(e)
        ok(all(t in txt for t in trechos), f'{msg}: erro com {trechos}')
        return txt
    ok(False, f'{msg}: deveria parar com ValueError')


# ---------------------------------------------------------------- arquivo do CPC simulado
h = pd.read_csv(H4_CSV, sep=';', decimal=',')[['ano', 'Trimestre', 'RONI_2c']]
SIM_2026 = {'DJF': -0.92, 'JFM': -0.79, 'FMA': -0.38, 'MAM': 0.03, 'AMJ': 0.47, 'MJJ': 1.02,
            'JJA': 1.37, 'JAS': 1.69}
ASC_BASE = pd.concat([h, pd.DataFrame({'ano': 2026, 'Trimestre': list(SIM_2026),
                                       'RONI_2c': list(SIM_2026.values())})], ignore_index=True)


def arquivo_cpc(df):
    """Texto no formato do RONI.ascii.txt (SEAS YR ANOM) e leitura igual à do script."""
    txt = 'SEAS   YR   ANOM\n' + '\n'.join(f"{t:>4} {a:>5} {x:>6.2f}" for a, t, x in
                                           df[['ano', 'Trimestre', 'RONI_2c']].itertuples(index=False))
    return (pd.read_csv(io.StringIO(txt), sep=r'\s+')
              .rename(columns={'SEAS': 'Trimestre', 'YR': 'ano', 'ANOM': 'RONI_2c'}))


def com(*novas, base=ASC_BASE, trocar=None, tirar=None):
    df = base.copy()
    for a, t, x in (trocar or []):
        df.loc[(df.ano == a) & (df.Trimestre == t), 'RONI_2c'] = x
    for a, t in (tirar or []):
        df = df[~((df.ano == a) & (df.Trimestre == t))]
    if novas:
        df = pd.concat([df, pd.DataFrame(novas, columns=['ano', 'Trimestre', 'RONI_2c'])], ignore_index=True)
    return arquivo_cpc(df)


TAB = S['ler_tabela'](S['noaa_data'])
conc = S['conciliar_oficial']
linha_2026 = [l for l in S['noaa_data'].splitlines() if l.startswith('2026')][0].replace('"""', '')

print('1. Dados reais: a regra sem empate reproduz a tabela oficial')
m = TAB.merge(h, on=['ano', 'Trimestre'])
emp = S['empate_2c'](m['RONI_2c'])
ok(len(m) == 912, f'912 estações de 1950 a 2025 em comum (achei {len(m)})')
ok(int(emp.sum()) == 87, f'87 empates na 2ª casa, como na revisão (achei {int(emp.sum())})')
ok(int((emp & (m['RONI_2c'] < 0)).sum()) == 47, 'empates negativos detectados (47)')
dif = np.abs(S['arred_sem_empate'](m['RONI_2c'][~emp]) - m['RONI'][~emp].to_numpy())
ok(int((dif > 1e-9).sum()) == 0, 'round(RONI_2c, 1) = tabela em todas as 825 estações sem empate')

print('2. empate_2c e arred_sem_empate')
x = np.array([-0.45, -1.05, -0.05, 0.05, 0.15, 1.95, 2.25, -0.44, -0.46, 1.04, 0.0, -0.04, 1.69])
ok(S['empate_2c'](x).tolist() == [True] * 7 + [False] * 6, 'empate vale para positivos e negativos')
r = S['arred_sem_empate'](np.array([-0.44, -0.46, -0.04, 0.04, 1.69, -1.14, 2.36]))
ok(r.tolist() == [-0.4, -0.5, 0.0, 0.0, 1.7, -1.1, 2.4], f'arredondamento sem empate {r.tolist()}')
ok(str(r[2]) == '0.0', '-0,04 vira 0.0 (sem sinal negativo)')

print('3. Caso de hoje: tabela e arquivo iguais (920 estações)')
of, rel = conc(TAB, com(), True, 3)
ok(len(of) == 920 and rel == {'acrescentadas': [], 'revisadas': []}, f'{len(of)} estações, nada acrescentado')
ok(of[['ano', 'mes']].values.tolist() == sorted(of[['ano', 'mes']].values.tolist()), 'ordenado por ano e mês')
ok(of.iloc[-1][['ano', 'Trimestre', 'mes']].tolist() == [2026, 'JAS', 8], 'última estação JAS 2026, mes 8')
ok(set(of.columns) >= {'ano', 'Trimestre', 'RONI', 'RONI_2c', 'mes', 'Fonte'}, 'colunas da série oficial')
ok(S['linhas_tabela'](of, [2026]) == [linha_2026], f'linha 2026 idêntica à tabela: {S["linhas_tabela"](of, [2026])}')
ok(S['linhas_tabela'](of, [1950, 2025]) == [l for l in S['noaa_data'].splitlines() if l[:4] in ('1950', '2025')],
   'linhas 1950 e 2025 idênticas à tabela (formato)')

print('4. Estação nova sem empate entra sozinha')
of, rel = conc(TAB, com((2026, 'ASO', 1.93)), True, 3)
ok(len(of) == 921, '921 estações')
ok(rel['acrescentadas'] == [[2026, 'ASO', 1.93, 1.9]], f"acrescentadas {rel['acrescentadas']}")
ok(S['linhas_tabela'](of, [2026]) == ['2026 -0.9 -0.8 -0.4 0.0 0.5 1.0 1.4 1.7 1.9 NaN NaN NaN'], 'linha 2026 atualizada')
of, rel = conc(TAB, com((2026, 'ASO', -0.44), (2026, 'SON', -0.04), (2026, 'OND', -1.06)), True, 3)
ok([r_[3] for r_ in rel['acrescentadas']] == [-0.4, 0.0, -1.1], f"negativas sem empate {rel['acrescentadas']}")
ok(S['linhas_tabela'](of, [2026])[0].endswith('-0.4 0.0 -1.1 NaN'), S['linhas_tabela'](of, [2026])[0])
of, rel = conc(TAB, com((2026, 'ASO', 1.93), (2026, 'SON', 2.08), (2026, 'OND', 2.21), (2026, 'NDJ', 2.17),
                        (2027, 'DJF', 1.88)), True, 3)
ok(len(rel['acrescentadas']) == 5 and len(of) == 925, 'várias estações novas, virando o ano')
ok(S['linhas_tabela'](of, [2026, 2027]) == ['2026 -0.9 -0.8 -0.4 0.0 0.5 1.0 1.4 1.7 1.9 2.1 2.2 2.2',
                                            '2027 1.9 NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN'], 'linhas 2026 e 2027')
ok(of.iloc[-1][['ano', 'mes']].tolist() == [2027, 1], 'DJF 2027 = mês 1 de 2027')

print('5. Empate em estação nova: para e manda digitar')
for v in (1.95, -0.45, -1.05, 0.05, -0.05):
    espera_erro(lambda: conc(TAB, com((2026, 'ASO', v)), True, 3), 'ASO', '2026', 'ERSSTv6', 'empate',
                msg=f'empate {v:+.2f}')
espera_erro(lambda: conc(TAB, com((2026, 'ASO', 1.93), (2026, 'SON', -0.45)), True, 3), 'SON', '-0.45',
            msg='empate só na 2ª estação nova')
tab_digitada = TAB.copy()
tab_digitada.loc[len(tab_digitada)] = [2026, 'ASO', -0.4]          # usuário digitou o valor do site
of, rel = conc(tab_digitada, com((2026, 'ASO', -0.45)), True, 3)
ok(len(of) == 921 and rel['acrescentadas'] == [], 'depois de digitado, o empate passa (|dif| = 0,05)')

print('6. AUTO_ESTACOES_NOVAS = False mantém a parada antiga')
ok(S['AUTO_ESTACOES_NOVAS'] is True and S['ESTACOES_REVISAVEIS'] == 3, 'constantes no script')
espera_erro(lambda: conc(TAB, com((2026, 'ASO', 1.93)), False, 3), 'cobrem estações diferentes', msg='auto desligado')

print('7. Revisão do CPC: vale nas 3 últimas estações da tabela; antes, erro')
for t, x, novo in (('JAS', 1.82, 1.8), ('JJA', 1.52, 1.5), ('MJJ', 0.88, 0.9)):
    of, rel = conc(TAB, com(trocar=[(2026, t, x)]), True, 3)
    v = of.loc[(of.ano == 2026) & (of.Trimestre == t), 'RONI'].item()
    ok(abs(v - novo) < 1e-9 and len(rel['revisadas']) == 1 and rel['revisadas'][0][:2] == [2026, t],
       f'revisão {t} 2026 -> {novo} ({rel["revisadas"]})')
espera_erro(lambda: conc(TAB, com(trocar=[(2026, 'AMJ', 0.62)]), True, 3), 'Divergência', 'AMJ',
            msg='AMJ (4ª última) revisada')
espera_erro(lambda: conc(TAB, com(trocar=[(1998, 'JAS', -0.5)]), True, 3), 'Divergência', '1998',
            msg='erro antigo de digitação')
espera_erro(lambda: conc(TAB, com(trocar=[(2026, 'JAS', 1.85)]), True, 3), 'empate', 'JAS', msg='revisão com empate')
of, rel = conc(TAB, com(trocar=[(2026, 'JAS', 1.65)]), True, 3)
ok(rel['revisadas'] == [] and of.iloc[-1]['RONI'] == 1.7, 'diferença de 0,05 (empate) fica na tolerância')
of, rel = conc(TAB, com((2026, 'ASO', 1.93), trocar=[(2026, 'JAS', 1.82)]), True, 3)
ok(len(rel['revisadas']) == 1 and len(rel['acrescentadas']) == 1, 'revisão e estação nova juntas')
ok(S['linhas_tabela'](of, [2026]) == ['2026 -0.9 -0.8 -0.4 0.0 0.5 1.0 1.4 1.8 1.9 NaN NaN NaN'], 'linha com revisão')

print('8. Outras paradas e lacunas')
espera_erro(lambda: conc(TAB, com(tirar=[(2026, 'JAS')]), True, 3), 'que o arquivo do CPC não tem', 'JAS',
            msg='estação digitada a mais')
buraco = TAB[~((TAB.ano == 1990) & (TAB.Trimestre == 'MAM'))]
of, rel = conc(buraco, com(), True, 3)
ok(of.loc[(of.ano == 1990) & (of.Trimestre == 'MAM'), 'RONI'].item() == 0.3 and len(of) == 920,
   'lacuna no meio da tabela é preenchida pelo arquivo (valor oficial 0.3)')
dup = pd.concat([com(), com().iloc[[5]]], ignore_index=True)
espera_erro(lambda: conc(TAB, dup, True, 3), 'repetida', msg='estação repetida no arquivo')
ruim = com()
ruim.loc[3, 'RONI_2c'] = np.nan
espera_erro(lambda: conc(TAB, ruim, True, 3), 'valor ausente', msg='valor ausente no arquivo')
espera_erro(lambda: conc(TAB, com().rename(columns={'RONI_2c': 'ANOM2'}), True, 3), 'colunas', msg='coluna mudou')

print('9. Leitura de volta do asset (M02-03)')
of, _ = conc(TAB, com(), True, 3)
of['data_ms'] = ((pd.to_datetime(dict(year=of['ano'], month=of['mes'], day=1))
                  - pd.Timestamp('1970-01-01')) // pd.Timedelta('1ms')).astype('int64')   # igual ao script
of['chave_join'] = [f'{a:04d}_{m_:02d}' for a, m_ in zip(of['ano'], of['mes'])]            # igual ao script
ok(of['chave_join'].iloc[0] == '1950_01' and of['data_ms'].iloc[0] == -631152000000, 'chave 1950_01 e data_ms de 1950-01-01')
lido = of.copy()
lido['ano'] = lido['ano'].astype(float)                        # número volta como double
lido['RONI'] = lido['RONI'].astype(np.float32).astype(float)   # gravado em float32: |dif| < 1e-6
lido['ts_lido'] = lido['data_ms']
c = S['conferir_leitura'](lido.sample(frac=1, random_state=1), of)
ok(c['erros'] == [] and 'system:time_start' in c['itens'], f'asset igual: sem erros ({c})')
l2 = lido.copy()
l2['ts_lido'] = -1
c = S['conferir_leitura'](l2, of)
ok(c['erros'] == [] and c['avisos'] and 'system:time_start' not in c['itens'], 'time_start ausente em todas: só aviso')
l2 = lido.copy()
l2 = l2.drop(columns='ts_lido').assign(**{'system:time_start': l2['data_ms']})
ok(S['conferir_leitura'](l2, of)['erros'] == [], 'time_start lido direto das propriedades também vale')
for rot, mexe in (('RONI', lambda d: d.__setitem__('RONI', d['RONI'].where(d.index != 10, d['RONI'] + 0.1))),
                  ('Trimestre', lambda d: d.__setitem__('Trimestre', d['Trimestre'].where(d.index != 3, 'XXX'))),
                  ('system:time_start', lambda d: d.__setitem__('ts_lido', d['ts_lido'].where(d.index != 7, -2))),
                  ('chave_join', lambda d: d.__setitem__('chave_join', d['chave_join'].where(d.index != 0, '1950_1'))),
                  ('data_ms', lambda d: d.__setitem__('data_ms', d['data_ms'].where(d.index != 9, 0)))):
    l2 = lido.copy()
    mexe(l2)
    c = S['conferir_leitura'](l2, of)
    ok(any(e.startswith(rot) for e in c['erros']), f'acusa {rot}: {c["erros"]}')
c = S['conferir_leitura'](lido.iloc[:-1], of)
ok(any('left_only' in e for e in c['erros']), 'acusa estação faltando no asset')
c = S['conferir_leitura'](pd.concat([lido, lido.iloc[[0]]]), of)
ok(any('repetidas' in e for e in c['erros']), 'acusa estação repetida no asset')
c = S['conferir_leitura'](lido.drop(columns='chave_join'), of)
ok(c['erros'] and 'ausentes' in c['erros'][0], 'acusa propriedade ausente')

print('10. ACL (M02-01): comparação sem owners e sem entradas vazias')
a1 = {'owners': ['user:a@x'], 'readers': [], 'writers': ['user:b@x'], 'all_users_can_read': True}
a2 = {'owners': ['user:c@x'], 'writers': ['user:b@x'], 'all_users_can_read': True}
ok(S['acl_resumo'](a1) == S['acl_resumo'](a2), 'mesma ACL apesar de owners e lista vazia')
ok(S['acl_resumo'](a1) != S['acl_resumo']({'owners': ['user:a@x'], 'writers': ['user:b@x']}), 'perda da leitura pública é detectada')
ok('owners' not in S['acl_sem_dono'](a1), 'owners sai da ACL reaplicada')

print(f"\n{'TODOS OS TESTES PASSARAM' if not FALHAS else f'{len(FALHAS)} FALHA(S)'}")
sys.exit(1 if FALHAS else 0)
