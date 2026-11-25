# Teste offline das funções puras da simulação K15 (sem Earth Engine). Rodar: python3 testes/teste_k15.py
import importlib.util
import os
import sys
import types

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.modules.setdefault('ee', types.ModuleType('ee'))
sys.modules.setdefault('requests', types.ModuleType('requests'))
spec = importlib.util.spec_from_file_location('k15', os.path.join(AQUI, '..', 'validacoes', 'K15_simulacao_grade_asset.py'))
k15 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k15)

falhas = 0


def confere(cond, msg):
    global falhas
    print(('  ok   ' if cond else '  FALHA ') + msg)
    falhas += 0 if cond else 1


print('[comparar_arredondado]')
ponto = pd.DataFrame({'N_Ponto': ['P1', 'P2'], 'Data_Completa': ['d1', 'd1'], 'Temperatura_Maxima_C': ['18.40', ''],
                      'Latitude': ['-26.34952', '-26.44952'], 'Municipio': ['Pato Branco', 'Pato Branco']})
cru = pd.DataFrame({'N_Ponto': ['P2', 'P1'], 'Data_Completa': ['d1', 'd1'], 'Temperatura_Maxima_C': ['', '18.399999618530273'],
                    'Latitude': ['-26.449520000000003', '-26.34952'], 'Municipio': ['Pato Branco', 'Pato Branco']})
confere(k15.comparar_arredondado(ponto, cru), 'cru igual ao formatado a menos do arredondamento (outra ordem de linhas)')
cru2 = cru.copy()
cru2.loc[1, 'Temperatura_Maxima_C'] = '18.41'
confere(not k15.comparar_arredondado(ponto, cru2), 'diferença de 0,01 na 2ª casa: acusa')
cru3 = cru.copy()
cru3.loc[0, 'Temperatura_Maxima_C'] = '0'
confere(not k15.comparar_arredondado(ponto, cru3), 'vazio x 0: acusa')
cru4 = cru.copy()
cru4.loc[1, 'Municipio'] = 'Outro'
confere(not k15.comparar_arredondado(ponto, cru4), 'texto diferente: acusa')

print('[decidir_k15]')
proc = {'V0a': 60, 'V1a': 20, 'V0b': 50, 'V1b': 25, 'V2': 18, 'V3': 55}
d = k15.decidir_k15(proc, True, {'montada': [500, 520], 'asset': [100, 120]})
confere(d['grade_asset'] and d['razoes_grade'] == [0.33, 0.5], 'asset 50-67% mais rápido nos 2 pares: adotar')
confere(not d['formato_cru'] and d['razao_formato_asset'] == 0.8, 'cru só 20% mais rápido: manter o formato')
confere(d['link_mais_rapido'] and d['razao_link'] == 0.22, 'link com asset 78% mais rápido (110 s x 510 s)')
confere(not k15.decidir_k15(proc, False, {})['grade_asset'], 'V1 diferente de V0: não adotar, por mais rápido que seja')
confere(not k15.decidir_k15(dict(proc, V1b=40), True, {})['grade_asset'], 'ganho só num par (40/50 = 0,8): não adotar')
confere(not k15.decidir_k15(dict(proc, V1b=None), True, {})['grade_asset'], 'um par falhou: não adotar')
d = k15.decidir_k15(dict(proc, V2=10, V3=30), True, {})
confere(d['formato_cru'], 'cru 55% e 45% mais rápido com as 2 grades: ganho suficiente')
d = k15.decidir_k15(dict(proc, V2=10, V3=50), True, {})
confere(not d['formato_cru'], 'cru rápido só com uma grade: manter o formato')
confere(k15.decidir_k15(proc, True, {'montada': [None, None], 'asset': [100]})['razao_link'] is None, 'link montado falhou: sem razão')

print('[ordem de envio]')
confere([v for v, _, _ in k15.VERSOES] == ['V0a', 'V1a', 'V3', 'V2', 'V0b', 'V1b'], 'pares (V0, V1), (V3, V2), (V0, V1)')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
