# Teste offline das funções puras da simulação K13 (sem Earth Engine). Rodar: python3 testes/teste_k13.py
import importlib.util
import os
import sys
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.modules.setdefault('ee', types.ModuleType('ee'))          # o script só usa o ee dentro do __main__
sys.modules.setdefault('requests', types.ModuleType('requests'))
spec = importlib.util.spec_from_file_location(
    'k13', os.path.join(AQUI, '..', 'validacoes', 'K13_simulacao_organizacao_downloads.py'))
k13 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k13)

falhas = 0


def confere(cond, msg):
    global falhas
    print(('  ok   ' if cond else '  FALHA ') + msg)
    falhas += 0 if cond else 1


def T(ok, seg):
    return {'ok': ok, 'segundos': seg}


OK, NAO = {'ok': True, 'segundos': 100}, {'ok': False, 'segundos': 100}

print('[aprovado e limite_da_escada]')
confere(k13.aprovado([OK, OK]) and not k13.aprovado([OK, NAO]) and not k13.aprovado([OK]), 'aprovado = 2 de 2')
esc = [('3m', 170000, [T(True, 40), T(True, 42)]), ('1a', 690000, [T(True, 150), T(True, 160)]),
       ('18m', 1030000, [T(True, 300), T(False, 600)]), ('2a', 1380000, [T(False, 620), T(False, 610)]), ('3a', 2070000, [])]
confere(k13.limite_da_escada(esc) == (690000, 927000),
        'falha em 18 meses: limite = 90% do degrau que falhou (927 mil), pois 70% do tempo da falha caberia mais')
esc_rapida = [('1a', 690000, [T(True, 150), T(True, 160)]), ('18m', 1030000, [T(False, 5), T(False, 4)])]
confere(k13.limite_da_escada(esc_rapida) == (690000, 690000), '503 rápido (carga): limite não cai abaixo do comprovado')
esc_meio = [('1a', 690000, [T(True, 150), T(True, 160)]), ('18m', 1030000, [T(False, 240), T(False, 250)])]
confere(k13.limite_da_escada(esc_meio) == (690000, 779000),
        'limite pela regra dos 70% do tempo da falha (779 mil, entre o comprovado e 90% da falha)')
esc_lenta = [('1a', 690000, [T(True, 300), T(True, 320)]), ('18m', 1030000, [T(False, 400), T(False, 420)])]
confere(k13.limite_da_escada(esc_lenta) == (690000, 690000), 'falha logo acima do tempo do comprovado: fica o comprovado')
esc_ok = [('3m', 170000, [OK, OK]), ('1a', 690000, [OK, OK]), ('3a', 2070000, [OK, OK])]
confere(k13.limite_da_escada(esc_ok) == (2070000, 2070000), 'nenhuma falha: limite = maior aprovado')
esc3 = [('3m', 170000, [OK, OK]), ('6m', 342000, [NAO, NAO]), ('1a', 690000, [OK, OK])]
confere(k13.limite_da_escada(esc3)[0] == 170000, 'degrau que falhou 2 vezes encerra a escada (sem buraco)')
confere(k13.limite_da_escada([('3m', 170000, [NAO, NAO])]) == (None, None), 'nada aprovado: sem limite')

print('[fator_de_forma]')
confere(k13.fator_de_forma(0.5, 0.45) == 1.0, 'diferença de 11%: fator 1')
confere(k13.fator_de_forma(0.8, 0.4) == 2.0, 'série longa 2x mais lenta: fator 2')
confere(k13.fator_de_forma(None, 0.4) == 1.0, 'sem medida: fator 1')

print('[escolher_formato]')
confere(k13.escolher_formato({'ponto': [100, 110], 'cru': [70, 75], 'virgula': [100, 100]})[0] == 'cru', 'cru 30% mais rápido: cru')
confere(k13.escolher_formato({'ponto': [100, 110], 'cru': [90, 95], 'virgula': [100, 100]})[0] == 'ponto', 'cru 12% mais rápido: ponto')
confere(k13.escolher_formato({'ponto': [100, 110], 'cru': [60, None], 'virgula': [100, 100]})[0] == 'ponto', 'cru falhou numa tentativa: ponto')
confere(k13.escolher_formato({'ponto': [100, None], 'cru': [60, 60]})[0] == 'ponto', 'ponto sem 2 tentativas: fica o ponto')
confere(k13.escolher_formato({'ponto': [100, 100], 'cru': [99, 99], 'virgula': [70, 70]})[0] == 'virgula', 'vírgula 30% mais rápida: vírgula')

print('[decidir_juntar]')
confere(k13.decidir_juntar([100, 110], True, [30, 30, 30, 20, 20]), 'junto 105 s <= 1,2 x 130 s: juntar')
confere(not k13.decidir_juntar([200, 210], True, [30, 30, 30, 20, 20]), 'junto 205 s > 156 s: não juntar')
confere(not k13.decidir_juntar([100, 110], False, [30, 30]), 'junto não aprovado: não juntar')
confere(not k13.decidir_juntar([100, 110], True, [30, None]), 'separado falhou: não juntar')

print('[escolher_simultaneos]')
r = {1: {'falhas': 0, 'tempo_total': 300}, 2: {'falhas': 0, 'tempo_total': 200}, 3: {'falhas': 2, 'tempo_total': 150}}
confere(k13.escolher_simultaneos(r) == 2, '2 sem falha e mais rápido; 3 com 429: 2')
r = {1: {'falhas': 0, 'tempo_total': 300}, 2: {'falhas': 0, 'tempo_total': 290}, 3: {'falhas': 0, 'tempo_total': 280}}
confere(k13.escolher_simultaneos(r) == 1, 'ganho menor que 10%: 1')
confere(k13.escolher_simultaneos({1: {'falhas': 1, 'tempo_total': 300}}) == 1, 'falha até sozinho: 1')

print('[escolher_divisao]')
confere(k13.escolher_divisao({'ok': True, 'tempo_total': 500}, {'ok': True, 'tempo_total': 480}) == 'periodo', 'empate (até 10%): período')
confere(k13.escolher_divisao({'ok': True, 'tempo_total': 700}, {'ok': True, 'tempo_total': 480}) == 'pontos', 'período 46% mais lento: pontos')
confere(k13.escolher_divisao({'ok': False, 'tempo_total': 0}, {'ok': True, 'tempo_total': 480}) == 'pontos', 'período falhou: pontos')
confere(k13.escolher_divisao({'ok': False, 'tempo_total': 0}, {'ok': False, 'tempo_total': 0}) == 'nenhuma', 'nada abriu: nenhuma')

print('[planejar_arquivos]')
anos = [(a, k13.dias_do_ano(a)) for a in range(1961, 2026)]
p = k13.planejar_arquivos(15, anos, 586000)
confere(len(p) == 1 and p[0][0] == '1961-2025' and p[0][1] == 15 * 23741, 'Pato Branco 1961-2025: 1 arquivo de 356.115 linhas')
p = k13.planejar_arquivos(15, anos, 586000, fator=2.0)
confere(len(p) == 2 and sum(l for _, l in p) == 15 * 23741, 'com fator de forma 2: 2 arquivos, sem perder linhas')
p = k13.planejar_arquivos(1889, [(2024, 366), (2025, 365), (2026, 319)], 586000)
confere([r for r, _ in p] == ['2024 (jan-jun)', '2024 (jul-dez)', '2025 (jan-jun)', '2025 (jul-dez)', '2026 (jan-jun)', '2026 (jul-dez)'],
        'Paraná com limite 586 mil: cada ano em 2 semestres')
p = k13.planejar_arquivos(1889, [(2024, 366), (2025, 365)], 1170000)
confere([r for r, _ in p] == ['2024', '2025'], 'Paraná com limite 1,17 milhão: 1 ano por arquivo (2 anos não cabem)')
p = k13.planejar_arquivos(1889, [(2024, 366), (2025, 365)], 1500000)
confere([r for r, _ in p] == ['2024-2025'], 'Paraná com limite 1,5 milhão: 2 anos num arquivo')
p = k13.planejar_arquivos(5200, [(2025, 365)], 586000)
confere([r for r, _ in p] == ['2025 (jan-mar)', '2025 (abr-jun)', '2025 (jul-set)', '2025 (out-dez)'], 'Minas 1 ano: 4 trimestres')
p = k13.planejar_arquivos(1889, [(a, 12) for a in range(1961, 2027)], 586000)
confere(sum(l for _, l in p) == 1889 * 66 * 12 and all(l <= 586000 for _, l in p) and len(p) == 3,
        'Paraná mensal 1961-2026: 3 arquivos de anos inteiros, sem perder linhas')
anos_nomes = ' '.join(r for r, _ in p)
confere('-' in anos_nomes and '(' not in anos_nomes, 'mensal: nenhum ano partido')

print('[links_hoje]')
confere(k13.links_hoje(1, 66) == 67 and k13.links_hoje(5, 10) == 51, 'hoje: 1 dicionário + locais x anos')

print('[colunas do painel]')
confere(len(k13.COLUNAS_DIARIA) == 33 and k13.COLUNAS_DIARIA[-3:] == ['Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo'],
        'diário: 33 colunas, como o painel 2026.10.4')
confere(len(k13.COLUNAS_MENSAL) == 33 and k13.COLUNAS_MENSAL[-3:] == ['N_Dias', 'Dias_no_Mes', 'Mes_Completo'],
        'mensal: 33 colunas, como o painel 2026.10.4')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
