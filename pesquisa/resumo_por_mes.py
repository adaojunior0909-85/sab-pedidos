# Os resultados das validações abertos POR MÊS DO ANO (jan a dez), para ver se o erro muda com a estação (chuvosa x
# seca, verão x inverno), o que o resumo do período inteiro esconde. Não fala com o Earth Engine: lê os CSV que os
# testes já gravaram e escreve pesquisa/RESULTADOS_POR_MES.md. Cada parte só entra se o CSV dela existir.
#   A. o método de 2026 em 2021-2025 (resultados_metodo_2026/parte_a/*.csv): erro por mês do ano
#   B. 2026 x GLDAS (resultados_metodo_2026/parte_b_gldas.csv): diferença de 2026 e a faixa de 2022-2024, por mês
#   C. o histórico x TerraClimate/CHIRPS (resultados_historico/anos/*.csv): viés por mês do ano e a correlação entre
#      os anos naquele mês (o mesmo mês de 1961 a 2025: acompanha os anos secos e chuvosos?)
#   D. o solo, a folha e a ET real x satélites (resultados_solo_folha/series_mensais.csv): viés por mês do ano
#     python pesquisa/resumo_por_mes.py
import glob
import os
import sys

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
REGIOES = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil']
SOMAS = {'pr_mm', 'pr_chirps', 'et_potencial', 'et_real', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm', 'escoamento'}
REGUA = (2022, 2023, 2024)


def vies(g, a, b, k):
    if k in SOMAS:
        return 100 * (g[a].sum() / g[b].sum() - 1) if g[b].sum() else float('nan')
    return (g[a] - g[b]).mean()


def tabela(df, a, b, titulo, unid, extra=None):
    """Linhas = mês do ano, colunas = regiões. extra(g) acrescenta texto à célula."""
    L = [f'### {titulo} ({unid})', '', '| Mês | ' + ' | '.join(REGIOES) + ' |', '|---|' + '---|' * len(REGIOES)]
    for m in range(1, 13):
        cel = []
        for reg in REGIOES:
            g = df[(df.mes == m) & (df.regiao == reg)].dropna(subset=[a, b])
            cel.append('-' if g.empty else f(vies(g, a, b, titulo_var(df)), titulo_var(df)) + (extra(g) if extra else ''))
        L.append(f'| {MESES[m - 1]} | ' + ' | '.join(cel) + ' |')
    return L + ['']


def f(x, k):
    return f'{x:+.3f}' if ('soil' in k or 'umidade' in k) else (f'{x:+.1f}' if k in SOMAS else f'{x:+.2f}')


def titulo_var(df):
    return df.variavel.iloc[0]


def unidade(k):
    return '%' if k in SOMAS else 'diferença na unidade da variável'


def main():
    L = ['# Validações abertas por mês do ano', '',
         'Gerado por `pesquisa/resumo_por_mes.py` a partir dos CSV das validações. Somas (chuva, ET, escoamento) em % '
         'do total do mês; o resto em diferença (SAB − referência) na unidade da variável.', '']
    pa = sorted(glob.glob(os.path.join(AQUI, 'resultados_metodo_2026', 'parte_a', '*.csv')))
    if pa:
        df = pd.concat(pd.read_csv(x) for x in pa)
        L += ['## A. O método de 2026 aplicado a 2021–2025 (erro do método, por mês do ano)', '']
        for k, g in df.groupby('variavel', sort=False):
            L += tabela(g, 'metodo_2026', 'entregue', k, unidade(k))
    pb = os.path.join(AQUI, 'resultados_metodo_2026', 'parte_b_gldas.csv')
    if os.path.exists(pb):
        df = pd.read_csv(pb)
        L += ['## B. 2026 contra o GLDAS-2.1, mês a mês (2026 e, entre colchetes, a faixa de 2022–2024)', '']
        for k, g in df.groupby('variavel', sort=False):
            L += [f'### {k} ({unidade(k)})', '', '| Mês | ' + ' | '.join(REGIOES) + ' |', '|---|' + '---|' * len(REGIOES)]
            for m in sorted(g.mes.unique()):
                cel = []
                for reg in REGIOES:
                    x = g[(g.mes == m) & (g.regiao == reg)].dropna()
                    d26 = vies(x[x.ano == 2026], 'sab', 'gldas', k)
                    rg = [vies(x[x.ano == a], 'sab', 'gldas', k) for a in REGUA]
                    cel.append(f'{f(d26, k)} [{f(min(rg), k)} a {f(max(rg), k)}]')
                L.append(f'| {MESES[m - 1]} | ' + ' | '.join(cel) + ' |')
            L.append('')
    ph = sorted(glob.glob(os.path.join(AQUI, 'resultados_historico', 'anos', '*.csv')))
    if ph:
        df = pd.concat(pd.read_csv(x) for x in ph)
        L += ['## C. O histórico contra TerraClimate e CHIRPS, por mês do ano',
              '', 'Viés no mês / correlação entre os anos naquele mês (o SAB acompanha os anos secos e chuvosos?).', '']
        for k, g in df.groupby('variavel', sort=False):
            L += tabela(g, 'sab', 'referencia', k, unidade(k),
                        extra=lambda x: f' / {x.sab.corr(x.referencia):.2f}' if len(x) > 5 else '')
    ps = os.path.join(AQUI, 'resultados_solo_folha', 'series_mensais.csv')
    if os.path.exists(ps):
        df = pd.read_csv(ps)
        L += ['## D. Solo, folha e ET real contra satélites (2016–2021), por mês do ano', '']
        for k, g in df.groupby('variavel', sort=False):
            L += tabela(g, 'sab', 'referencia', k, unidade(k))
    with open(os.path.join(AQUI, 'RESULTADOS_POR_MES.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print(f'{len(L)} linhas escritas em pesquisa/RESULTADOS_POR_MES.md')


if __name__ == '__main__':
    sys.exit(main())
