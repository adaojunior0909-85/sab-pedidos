# A7 do protocolo da auditoria profunda: a cadeia (2026 e a previsão) herdou o degrau de 2020–2025? Sem Earth Engine.
# 1. Quais anos entram em cada calibração (lido no código; as linhas citadas estão na tabela do relatório).
# 2. Climatologia SICSB_1986_2025 (fator BR-DWGD/ERA5 dos dias ERA5 desde 2026; e base do EQM): quanto o fator mudaria
#    refeito sem 2020–2025, por região e mês, com as médias regionais mensais do banco (= BR-DWGD no núcleo) e do
#    ERA5-Land bruto que já subiram (resultados_multifonte/era5). Aproximação regional (o fator real é por pixel).
# 3. Calibrações feitas SÓ com anos do trecho suspeito (matriz do GFS V2.1: 2021–2025; razões da V1.8: 2021–2025): não
#    há como refazer sem esses anos; a herança é medida pelo tamanho do degrau do A1 nesses anos (mediana das famílias).
# Regra (protocolo, A7): mudança > tolerância do A1 em ≥ 2 regiões = a cadeia herdou o degrau.
import glob
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import auditoria_a1_a2 as A  # noqa: E402

SAIDA = os.path.join(AQUI, 'resultados_auditoria')
REG5 = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
CALIBRACOES = [
    ('Fator de clima dos dias ERA5 (2026 em diante, V1.7/V1.8)', 'SICSB_1986_2025', '1986–2025 (6 de 40 anos no trecho)',
     'sab-motor 05a_motor_sab_v1_8_SIMULACAO.py, ASSET_CLIMATOLOGIA (l. 179)'),
    ('UR por quantis (EQM) dos dias ERA5', 'SICSB_EQM_1986_2025', '1986–2025 (6 de 40)', '05a v1_8, ASSET_EQM (l. 183)'),
    ('Razões da chuva da V1.8 (C3)', 'RAZAO_CHUVA_C3', '2021–2025 (todos no trecho)', '05a v1_8, cabeçalho (l. 12–14)'),
    ('Previsão GFS 1–15 dias (matriz V2.1)', 'SICSB_MATRIZ_GFS_V2', 'rodadas de 23/03/2021 a 31/12/2025 (todos no trecho)',
     'entrega/base_07/03_matriz_gfs_v2_1.py, INICIO_RODADAS/FIM_DIAS (l. 97–98)'),
    ('Umidade do solo (fator SMAP/ERA5)', 'SICSB_SOLO_2015_2025', '2015–2025 (não usa o BR-DWGD: fora do degrau)',
     '05a v1_8, ASSET_SOLO (l. 181)'),
    ('Normais 1991–2020 (painel)', '07a_normais_CONFERIR_1991_2020.py', '1991–2020 (1 de 30)', 'entrega/base_07/07a'),
]


def climatologia():
    d = A.carregar()
    e = d[d.base == 'era5'][['regiao', 'ano', 'mes', 'variavel', 'sab', 'referencia']]
    if e.empty or e.ano.max() < 2025:
        return None, (int(e.ano.max()) if len(e) else None)
    linhas = []
    for (reg, var, mes), g in e[e.regiao.isin(REG5 + ['Brasil'])].groupby(['regiao', 'variavel', 'mes']):
        tudo = g[g.ano.between(1986, 2025)]
        sem = g[g.ano.between(1986, 2019)]
        if var in A.MULT:
            f_tudo = tudo.sab.mean() / tudo.referencia.mean()
            f_sem = sem.sab.mean() / sem.referencia.mean()
            mud = 100 * (f_sem / f_tudo - 1)
        else:
            mud = (sem.sab.mean() - sem.referencia.mean()) - (tudo.sab.mean() - tudo.referencia.mean())
        linhas.append({'regiao': reg, 'variavel': var, 'mes': mes, 'mudanca_sem_2020_2025': mud})
    return pd.DataFrame(linhas), 2025


def main():
    L = ['# A7. A cadeia (2026 e a previsão) herdou o degrau de 2020–2025?', '',
         'Protocolo `pesquisa/PROTOCOLO_AUDITORIA_PROFUNDA.md`, A7. Regra: mudança > tolerância do A1 em ≥ 2 regiões = '
         'a cadeia herdou o degrau.', '', '## Quais anos entram em cada calibração', '',
         '| Calibração | Asset / objeto | Anos | Onde está no código |', '|---|---|---|---|']
    L += [f'| {a} | `{b}` | {c} | {d} |' for a, b, c, d in CALIBRACOES]
    L.append('')
    # 2. climatologia
    c, ate = climatologia()
    L += ['## Fator de clima (SICSB_1986_2025) refeito sem 2020–2025', '']
    if c is None:
        L += [f'Aguardando o ERA5-Land bruto até 2025 no `resultados_multifonte/era5` (hoje até {ate}).', '']
    else:
        c.to_csv(os.path.join(SAIDA, 'A7_climatologia.csv'), index=False)
        L += ['Mudança média do fator nos 12 meses (maior mês entre parênteses); + = o fator sem 2020–2025 seria maior.', '',
              '| Variável | ' + ' | '.join(REG5) + ' | regiões acima da tolerância |', '|---|' + '---|' * 6]
        for var, g in c.groupby('variavel'):
            if var not in A.TOL:
                continue
            cel, n = [], 0
            for reg in REG5:
                s = g[g.regiao == reg].mudanca_sem_2020_2025
                if s.empty:
                    cel.append('-')
                    continue
                tol = A.TOL[var] if var != 'rs' else 3.0
                n += abs(s.mean()) > tol
                cel.append(f'{A.fmt(s.mean(), var)} ({A.fmt(s.loc[s.abs().idxmax()], var)})')
            L.append(f'| {A.NOME.get(var, var)} | ' + ' | '.join(cel) + f' | {n} {"→ herdou" if n >= 2 else ""} |')
        L.append('')
    # 3. calibrações feitas só com o trecho suspeito
    arq = os.path.join(SAIDA, 'A1_por_familia_ano.csv')
    if os.path.exists(arq):
        t = pd.read_csv(arq)
        t = t[t.ano.between(2021, 2025)]
        pers = pd.read_csv(os.path.join(SAIDA, 'A1_persistencia.csv'))
        pers = {(r.regiao, r.variavel) for r in pers.itertuples() if r.persistente}
        L += ['## Matriz do GFS e razões da V1.8 (feitas só com 2021–2025)', '',
              'Não há como refazê-las sem esses anos (o GFS v16 começa em 2021). A herança é o degrau do A1 em 2021–2025: '
              'mediana das famílias, média dos anos, **só onde o A1 confirmou degrau persistente** (célula com "·" = sem degrau '
              'confirmado no A1: o valor de uma família só é relato e não conta para a regra).', '',
              '| Variável | ' + ' | '.join(REG5) + ' | regiões acima da tolerância |', '|---|' + '---|' * 6]
        for var in A.VARS:
            g = t[t.variavel == var]
            if g.empty:
                continue
            cel, n = [], 0
            for reg in REG5:
                s = g[g.regiao == reg].groupby('ano').v.median()
                if s.empty:
                    cel.append('-')
                    continue
                tol = g[g.regiao == reg].tol.median()
                if (reg, var) not in pers:
                    cel.append(f'· {A.fmt(s.mean(), var)}')
                    continue
                n += abs(s.mean()) > tol
                cel.append(f'**{A.fmt(s.mean(), var)}**')
            L.append(f'| {A.NOME[var]} | ' + ' | '.join(cel) + f' | {n} {"→ herdou" if n >= 2 else ""} |')
        L.append('')
    with open(os.path.join(SAIDA, 'RESULTADOS_A7.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
