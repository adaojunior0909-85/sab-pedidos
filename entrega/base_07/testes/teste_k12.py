# Teste offline das funções puras da simulação K12 (sem Earth Engine). Rodar: python3 testes/teste_k12.py
import importlib.util
import os
import sys
import types

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.modules.setdefault('ee', types.ModuleType('ee'))          # o script só usa o ee dentro do __main__
sys.modules.setdefault('requests', types.ModuleType('requests'))
spec = importlib.util.spec_from_file_location('k12', os.path.join(AQUI, '..', 'validacoes', 'K12_simulacao_download_estadual.py'))
k12 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k12)

falhas = 0


def confere(cond, msg):
    global falhas
    print(('  ok   ' if cond else '  FALHA ') + msg)
    falhas += 0 if cond else 1


print('[planejar_partes]')
p = k12.planejar_partes(2000, 31, 15000)
confere(len(p) == 5 and p[0] == (0, 483) and p[-1][1] == 2000, 'Paraná, 1 mês: 5 partes de até 483 pontos')
confere(all(b > a for a, b in p) and all(p[i][1] == p[i + 1][0] for i in range(len(p) - 1)), 'partes contíguas, sem repetir nem pular')
confere(all((b - a) * 31 <= 15000 for a, b in p), 'nenhuma parte passa de 15.000 linhas')
confere(k12.planejar_partes(15, 365, 15000) == [(0, 15)], 'Pato Branco, ano inteiro: 1 parte')
confere(len(k12.planejar_partes(3, 20000, 15000)) == 3, 'mais dias que o limite: 1 ponto por parte')
confere(k12.planejar_partes(0, 31, 15000) == [], 'sem pontos: nenhuma parte')

print('[ler_csv_texto]')
cab = ','.join(k12.COLUNAS)
vazio = {c: '' for c in k12.COLUNAS}
lin_v = dict(vazio, N_Ponto='Ponto_00001', Data_Completa='2026-10-01', Temperatura_Maxima_C='18,40',
             Latitude='-25,94952', Precipitacao_mm='')
lin_n = dict(vazio, N_Ponto='Ponto_00001', Data_Completa='2026-10-01', Temperatura_Maxima_C='18.4',
             Latitude='-25.94952', Precipitacao_mm='')


def csv(lin):
    return cab + '\n' + ','.join('"' + lin[c] + '"' if ',' in lin[c] else lin[c] for c in k12.COLUNAS) + '\n'


dv = k12.ler_csv_texto(csv(lin_v), virgula=True)
dn = k12.ler_csv_texto(csv(lin_n), virgula=False)
confere(dv['Temperatura_Maxima_C'].iloc[0] == 18.4 and dn['Temperatura_Maxima_C'].iloc[0] == 18.4, '"18,40" e 18.4 viram o mesmo número')
confere(pd.isna(dv['Precipitacao_mm'].iloc[0]) and pd.isna(dn['Precipitacao_mm'].iloc[0]), 'célula vazia continua vazia')
confere(list(dn.columns) == k12.COLUNAS, 'colunas na ordem do painel')
confere(len(k12.COLUNAS) == 33 and k12.COLUNAS[-3:] == ['Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo'],
        '33 colunas, como o CSV diário do painel 2026.10.4')

print('[diferenca_so_arredondamento]')
base = pd.DataFrame({c: [1.0] for c, _, _ in k12.NUMERICAS})
um_centesimo = base.copy(); um_centesimo['Temperatura_Maxima_C'] = 1.01
dois_centesimos = base.copy(); dois_centesimos['Temperatura_Maxima_C'] = 1.02
confere(k12.diferenca_so_arredondamento(base, um_centesimo), 'diferença de 1 unidade da 2ª casa (empate): aceita')
confere(not k12.diferenca_so_arredondamento(base, dois_centesimos), 'diferença de 2 unidades: acusa')

print('[dias_do_ano, dividir_bloco, conferir_ano]')
confere(k12.dias_do_ano(2025) == 365 and k12.dias_do_ano(2024) == 366, '2025: 365 dias; 2024: 366')
anual = k12.planejar_partes(2000, 365, 15000)
confere(len(anual) == 49 and anual[0] == (0, 41), 'Paraná, ano inteiro: 49 partes de até 41 pontos (14.965 linhas)')
menores = k12.dividir_bloco(41, 82, 365, 15000)
confere(menores[0][0] == 41 and menores[-1][1] == 82 and all(b - a <= 20 for a, b in menores),
        'parte que falhou vira blocos com a metade do limite, cobrindo os mesmos pontos')
pares = pd.DataFrame({'N_Ponto': [f'P{i}' for i in range(3) for _ in range(2)],
                      'Data_Completa': ['2025-01-01', '2025-01-02'] * 3})
r = dict(k12.conferir_ano([(k12.COLUNAS, pares)], 3, 2))
confere(all(r.values()), 'ano completo: todas as conferências passam')
r2 = dict(k12.conferir_ano([(k12.COLUNAS, pares), (k12.COLUNAS, pares.iloc[:1])], 3, 2))
confere(not r2['nenhum par (ponto, dia) repetido'] and not r2['linhas = pontos x dias (6)'], 'parte repetida: acusa')
r3 = dict(k12.conferir_ano([(k12.COLUNAS, pares.iloc[:4])], 3, 2))
confere(not r3['todos os 3 pontos presentes'], 'ponto faltando: acusa')
r4 = dict(k12.conferir_ano([(list(reversed(k12.COLUNAS)), pares)], 3, 2))
confere(not r4['colunas na ordem do painel em todas as partes'], 'colunas fora de ordem: acusa')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
