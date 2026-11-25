# -*- coding: utf-8 -*-
"""[V4 M03-10] Máximo de pares dia x prazo por mês e por faixa na matriz GFS V2.1 (só GFS v16).

Python puro (sem Earth Engine). Enumera as RODADAS (e não os dias, como o 03 faz), para servir de
conferência independente da função maximos_por_mes() do 03:
  - rodadas 00Z criadas de 2021-03-23 a 2025-12-31;
  - cada rodada c gera o par do prazo L (1 a 15) para o dia previsto D = c + (L-1);
  - o par só conta se D <= 2025-12-31 (último dia do BR-DWGD);
  - o mês do par é o mês de D (a matriz é por mês do dia previsto).
O máximo supõe todas as rodadas presentes e completas. Na prática há poucas falhas no período
(auditoria F3: 1 rodada ausente em 2022-04; 1 rodada sem a hora 192 em 2022-08 e em 2022-09),
então a contagem do 03 deve ficar alguns pares abaixo do máximo nesses meses.

Uso: python3 maximos_pares_v16.py            (imprime a tabela em texto e em Markdown)
"""
from datetime import date, timedelta

INICIO_RODADAS = date(2021, 3, 23)
FIM_DIAS = date(2025, 12, 31)
FAIXAS = [('L1', [1]), ('L2a5', [2, 3, 4, 5]), ('L6a10', [6, 7, 8, 9, 10]), ('L11a15', [11, 12, 13, 14, 15])]
LIMIAR = 0.85
MESES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


def faixa_do_prazo(L):
    for fx, prazos in FAIXAS:
        if L in prazos:
            return fx
    return None


def maximos_por_rodada():
    """{mes: {faixa: n}} enumerando rodadas x prazos."""
    tab = {m: {fx: 0 for fx, _ in FAIXAS} for m in range(1, 13)}
    c = INICIO_RODADAS
    while c <= FIM_DIAS:
        for L in range(1, 16):
            d = c + timedelta(days=L - 1)
            if d <= FIM_DIAS:
                tab[d.month][faixa_do_prazo(L)] += 1
        c += timedelta(days=1)
    return tab


def minimo_aceitavel(n):
    """Menor contagem sem ⚠️ no 03 (n >= 85% do máximo)."""
    k = int(LIMIAR * n)
    while k < LIMIAR * n:
        k += 1
    return k


def main():
    tab = maximos_por_rodada()
    print("Máximo de pares dia x prazo por mês (GFS v16: rodadas 00Z de 2021-03-23 a 2025-12-31; "
          "dias previstos até 2025-12-31)\n")
    cab = f"{'Mês':<4}" + ''.join(f"{fx:>9}" for fx, _ in FAIXAS) + f"{'Total':>9}"
    print(cab)
    tot = {fx: 0 for fx, _ in FAIXAS}
    for m in range(1, 13):
        linha = f"{MESES[m - 1]:<4}" + ''.join(f"{tab[m][fx]:>9}" for fx, _ in FAIXAS)
        print(linha + f"{sum(tab[m].values()):>9}")
        for fx, _ in FAIXAS:
            tot[fx] += tab[m][fx]
    print(f"{'Ano':<4}" + ''.join(f"{tot[fx]:>9}" for fx, _ in FAIXAS) + f"{sum(tot.values()):>9}")

    print("\nTabela para o roteiro (máximo; entre parênteses, o mínimo sem ⚠️ = 85% do máximo):\n")
    print("| Mês | " + " | ".join(fx for fx, _ in FAIXAS) + " |")
    print("|---|" + "---|" * len(FAIXAS))
    for m in range(1, 13):
        print(f"| {MESES[m - 1]} | " + " | ".join(f"{tab[m][fx]} ({minimo_aceitavel(tab[m][fx])})" for fx, _ in FAIXAS) + " |")
    return tab


if __name__ == '__main__':
    import sys
    if '--json' in sys.argv:   # usado por teste_04.js para conferir a tabela embutida no 04
        import json
        t = maximos_por_rodada()
        print(json.dumps({f'{m:02d}': [t[m][fx] for fx, _ in FAIXAS] for m in range(1, 13)}))
    else:
        main()
