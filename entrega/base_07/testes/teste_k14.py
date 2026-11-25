# Teste offline das funções puras da simulação K14 (sem Earth Engine). Rodar: python3 testes/teste_k14.py
import importlib.util
import os
import sys
import types

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.modules.setdefault('ee', types.ModuleType('ee'))
sys.modules.setdefault('requests', types.ModuleType('requests'))
spec = importlib.util.spec_from_file_location('k14', os.path.join(AQUI, '..', 'validacoes', 'K14_simulacao_exportacao_lote.py'))
k14 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k14)

falhas = 0


def confere(cond, msg):
    global falhas
    print(('  ok   ' if cond else '  FALHA ') + msg)
    falhas += 0 if cond else 1


print('[normalizar_status e resumo_tarefa]')
st = {'state': 'COMPLETED', 'creation_timestamp_ms': 0, 'start_timestamp_ms': 120000, 'update_timestamp_ms': 720000,
      'batch_eecu_usage_seconds': 7200}
r = k14.resumo_tarefa(st)
confere(r == {'estado': 'COMPLETED', 'fila_min': 2.0, 'processamento_min': 10.0, 'total_min': 12.0, 'EECU_h': 2.0, 'erro': ''},
        'formato getTaskStatus: fila 2, processamento 10, total 12 min; 2 EECU-hora')
op = {'metadata': {'state': 'SUCCEEDED', 'createTime': '2026-10-29T15:00:00Z', 'startTime': '2026-10-29T15:03:00Z',
                   'updateTime': '2026-10-29T15:33:00Z', 'batchEecuUsageSeconds': 1800}}
r = k14.resumo_tarefa(op)
confere(r['estado'] == 'COMPLETED' and r['fila_min'] == 3.0 and r['total_min'] == 33.0 and r['EECU_h'] == 0.5,
        'formato de operação: SUCCEEDED vira COMPLETED, tempos e EECU certos')
r = k14.resumo_tarefa({'state': 'RUNNING', 'creation_timestamp_ms': 0, 'start_timestamp_ms': 60000, 'update_timestamp_ms': 90000})
confere(r['processamento_min'] is None and r['total_min'] is None, 'tarefa ainda rodando: sem tempo total')
r = k14.resumo_tarefa({'metadata': {'state': 'FAILED'}, 'error': {'message': 'Computation timed out.'}})
confere(r['estado'] == 'FAILED' and r['erro'] == 'Computation timed out.', 'falha: estado e mensagem')

print('[conferir_csv]')
pares = pd.DataFrame({'N_Ponto': ['P1', 'P1', 'P2', 'P2'], 'Data_Completa': ['d1', 'd2', 'd1', 'd2']})
confere(k14.conferir_csv(['a', 'b'], pares, ['a', 'b'], 4) == (True, ''), 'completo')
confere(not k14.conferir_csv(['a', 'b'], pares.iloc[:3], ['a', 'b'], 4)[0], 'linha faltando')
confere(not k14.conferir_csv(['a', 'b'], pd.concat([pares, pares.iloc[:1]]), ['a', 'b'], 5)[0], 'par repetido')
confere(not k14.conferir_csv(['b', 'a'], pares, ['a', 'b'], 4)[0], 'colunas fora de ordem')

print('[comparar_identicos]')
a = pd.DataFrame({'N_Ponto': ['P2', 'P1'], 'Data_Completa': ['d1', 'd1'], 'x': ['1.00', '']})
b = pd.DataFrame({'N_Ponto': ['P1', 'P2'], 'Data_Completa': ['d1', 'd1'], 'x': ['', '1.00']})
confere(k14.comparar_identicos(a, b), 'mesmas células em outra ordem de linhas: idênticos')
c = b.copy()
c.loc[1, 'x'] = '1.0'
confere(not k14.comparar_identicos(a, c), '"1.00" x "1.0": diferentes (compara como texto)')
confere(not k14.comparar_identicos(a, b[['Data_Completa', 'N_Ponto', 'x']]), 'colunas em outra ordem: diferentes')

print('[veredito]')
ok = [{'caso': 'C0', 'ok': True, 'total_min': 3}] + [{'caso': f'C{i}', 'ok': True, 'total_min': t}
                                                      for i, t in zip(range(1, 7), [10, 40, 35, 25, 8, 60])]
confere(k14.veredito(ok) == (True, 60, 35), 'todos completos: viável; maior 60 min, mediana 35 min')
confere(not k14.veredito(ok[:3] + [{'caso': 'C3', 'ok': False, 'total_min': None}] + ok[4:])[0], 'um grande falhou: não viável')
confere(not k14.veredito([{'caso': 'C0', 'ok': False, 'total_min': 3}] + ok[1:])[0], 'C0 diferente do link: não viável')

print('[colunas]')
confere(k14.COLUNAS_DIARIA[-3:] == ['Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo'] and len(k14.COLUNAS_DIARIA) == 33,
        'diário: 33 colunas do painel')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
