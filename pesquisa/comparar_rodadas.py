# PESQUISA: critério de aceite da rodada 2 (PROTOCOLO.md, seção "Rodada 2"). Só anos de TREINO decidem:
# a rodada 2 substitui a 1, por variável, se a soma dos erros dos métodos escolhidos (5 regiões x 4 estações x
# 3 alvos) cair nas duas medidas de treino: "ano de fora" 1982-2010 e validação para frente 2000-2010.
# O teste 2011-2025 é mostrado só como informação (exploratório).
#     python pesquisa/comparar_rodadas.py [resultados] [resultados_rodada2]
import os
import sys

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
REGIOES = ('Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul')
NOME = {'pr': 'Chuva', 'tx': 'Tmax', 'tn': 'Tmin'}


def ler(pasta):
    e = pd.read_csv(os.path.join(pasta, 'metodo_escolhido_por_celula.csv'))
    return e[e['regiao'].isin(REGIOES)]


def main():
    r1 = ler(sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, 'resultados'))
    r2 = ler(sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, 'resultados_rodada2'))
    L = ['# Rodada 1 x rodada 2 (critério de aceite: só anos de treino)', '',
         '| Variável | Erro "ano de fora" 1982-2010 (r1 → r2) | Erro validação 2000-2010 (r1 → r2) | Aceita a rodada 2? | '
         'Teste 2011- (exploratório): células aprovadas r1 → r2 | MSESS médio das escolhidas r1 → r2 |',
         '|---|---|---|---|---|---|']
    aceite = {}
    for v in ('pr', 'tx', 'tn'):
        a, b = r1[r1['variavel'] == v], r2[r2['variavel'] == v]
        tl1, tl2 = a['EQM_treino_loo'].sum(), b['EQM_treino_loo'].sum()
        va1, va2 = a['EQM_validacao'].sum(), b['EQM_validacao'].sum()
        ok = tl2 < tl1 and va2 < va1
        aceite[v] = ok
        ap1 = (a['produto'] != 'sem sinal: média histórica').sum()
        ap2 = (b['produto'] != 'sem sinal: média histórica').sum()
        L.append(f'| {NOME[v]} | {tl1:.1f} → {tl2:.1f} ({100 * (tl2 / tl1 - 1):+.1f}%) | '
                 f'{va1:.1f} → {va2:.1f} ({100 * (va2 / va1 - 1):+.1f}%) | {"**sim**" if ok else "não (fica a rodada 1)"} | '
                 f'{ap1} → {ap2} de {len(a)} | {a["MSESS"].mean():+.3f} → {b["MSESS"].mean():+.3f} |')
    texto = '\n'.join(L) + '\n'
    print(texto)
    with open(os.path.join(AQUI, 'COMPARACAO_RODADAS.md'), 'w', encoding='utf-8') as f:
        f.write(texto)
    return aceite


if __name__ == '__main__':
    main()
