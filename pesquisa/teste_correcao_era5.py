# Testes, SEM Earth Engine, das contas e da regra de decisão de pesquisa/validar_correcao_era5.py.
#     python pesquisa/teste_correcao_era5.py
import os
import sys
import tempfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validar_correcao_era5 as t  # noqa: E402

ok = 0


def confere(cond, msg):
    global ok
    assert cond, msg
    ok += 1


# --- contas do motor no pixel
confere(abs(t.fator(10, 5) - 2) < 1e-12, 'fator simples')
confere(t.fator(10, 0) == t.FATOR_MAX, 'fator com modelo seco vai ao teto')
pr = t.chuva_corrigida([10.0, 100.0, 0.0], 2.0, 40.0)            # teto = max(bruta, 60)
confere(np.allclose(pr, [20.0, 100.0, 0.0]), f'teto da chuva {pr}')
confere(np.allclose(t.chuva_corrigida([10.0, 100.0], 2.0, np.nan), [20.0, 200.0]), 'sem matriz, sem teto')
confere(np.allclose(t.chuva_corrigida([10.0, 100.0], 2.0, [np.nan, 40.0]), [20.0, 100.0]), 'teto por pixel')
confere(t.razao_c3([120, 120], [100, 100]) == 1.2, 'razão C3')
confere(t.razao_c3([300], [100]) == 1.5 and t.razao_c3([10], [100]) == 0.8, 'razão C3 limitada')
confere(t.razao_c3([10], [0]) == 1.0, 'razão C3 sem chuva')
confere(t.escolher(['C3', 'C1'], {'C1': 5.3, 'C3': 5.0}, 0.5) == 'C1', 'desempate pelo mais simples')
confere(t.escolher(['C3', 'C1'], {'C1': 5.6, 'C3': 5.0}, 0.5) == 'C3', 'sem empate vence o menor')
confere(t.escolher([], {}, 0.5) is None, 'ninguém passa')
confere(t.janela('C1', 2016) == (2006, 2015) and t.janela('C2', 2016) == (2001, 2015)
        and t.janela('C0', 2016) == (1986, 2015), 'janelas')
p = t.pedacos(2016)
confere(p == {'a': (1986, 2000), 'b': (2001, 2005), 'c': (2006, 2015)}, f'pedaços {p}')
confere(abs(t.brasil_ponderado({'Norte': 1, 'Nordeste': 3, 'Centro-Oeste': 0, 'Sudeste': 0, 'Sul': 0},
                               {'Norte': 1, 'Nordeste': 1, 'Centro-Oeste': 0, 'Sudeste': 0, 'Sul': 0}) - 2) < 1e-12,
        'Brasil ponderado')
m = pd.DataFrame({'ano': [1, 1, 2, 2], 'mes': [1, 2, 1, 2], 'metodo': [1, 5, 3, 7], 'ref': [2, 6, 4, 8]})
confere(abs(t.r_anomalias(m) - 1) < 1e-12, 'r_anomalias perfeito')

# --- ponta a ponta sintético: C1 corrige um viés de -10% que o C0 deixa; C2 corrige metade; C3 é o C0
rng = np.random.default_rng(1)
pasta = tempfile.mkdtemp()
t.SAIDA = pasta
os.makedirs(os.path.join(pasta, 'regional'))
os.makedirs(os.path.join(pasta, 'pixels'))
pesos = {r: 1.0 for t_ in [0] for r in t.REGIOES5}
pd.DataFrame({'regiao': list(pesos), 'peso': list(pesos.values())}).to_csv(os.path.join(pasta, 'pesos_regioes.csv'),
                                                                            index=False)
fator_metodo = {'C0': 0.90, 'C1': 1.00, 'C2': 0.95}
for Y in t.ANOS_TESTE:
    for mes in range(1, 13):
        linhas = []
        for r in t.REGIOES:
            for a in range(Y - 5, Y + 1):
                br = 100 + 50 * np.sin(mes) + rng.normal(0, 10)
                ruido = rng.normal(0, 1)
                linhas.append(dict(ano_alvo=Y, ano=a, mes=mes, regiao=r, metodo='BR', variavel='pr', valor=br))
                linhas.append(dict(ano_alvo=Y, ano=a, mes=mes, regiao=r, metodo='C0', variavel='pr',
                                   valor=0.90 * br + ruido))
                if a == Y:
                    for k in ('C1', 'C2'):
                        linhas.append(dict(ano_alvo=Y, ano=a, mes=mes, regiao=r, metodo=k, variavel='pr',
                                           valor=fator_metodo[k] * br + ruido))
                    rs = 18 + rng.normal(0, 0.5)
                    eto = 120 + rng.normal(0, 3)
                    linhas.append(dict(ano_alvo=Y, ano=a, mes=mes, regiao=r, metodo='BR', variavel='rs', valor=rs))
                    linhas.append(dict(ano_alvo=Y, ano=a, mes=mes, regiao=r, metodo='BR', variavel='eto', valor=eto))
                    for k, (drs, feto) in {'C0': (0.6, 1.035), 'C1': (0.1, 1.005), 'C2': (0.3, 1.02),
                                           'C3': (0.0, 1.0)}.items():
                        linhas.append(dict(ano_alvo=Y, ano=a, mes=mes, regiao=r, metodo=k, variavel='rs', valor=rs + drs))
                        linhas.append(dict(ano_alvo=Y, ano=a, mes=mes, regiao=r, metodo=k, variavel='eto',
                                           valor=eto * feto))
        pd.DataFrame(linhas).to_csv(os.path.join(pasta, 'regional', f'{Y}_{mes:02d}.csv'), index=False)
# pixels: o ERA5 bruto chove 0,8 x o BR-DWGD; as janelas têm o mesmo fator, então C0 = C1 = C2 nos pixels
pts = pd.DataFrame({'pid': range(6), 'lon': 0.0, 'lat': 0.0, 'regiao': t.REGIOES5 + ['Norte'],
                    **{f'prmax_{mm:02d}': 80.0 for mm in range(1, 13)}})
pts.to_csv(os.path.join(pasta, 'pixels', 'pontos.csv'), index=False)
datas = pd.date_range('1986-01-01', '2025-12-31').strftime('%Y-%m-%d')
for ano in range(1986, 2026):
    ds = [d for d in datas if d.startswith(str(ano))]
    br = np.where(rng.random((6, len(ds))) < 0.4, rng.gamma(0.8, 12, (6, len(ds))), 0.0)
    df = pd.DataFrame({'pid': np.repeat(range(6), len(ds)), 'data': np.tile(ds, 6), 'br': br.ravel(),
                       'era': 0.8 * br.ravel()})
    df.to_csv(os.path.join(pasta, 'pixels', f'dias_{ano}.csv.gz'), index=False)
t.resumo()
txt = open(os.path.join(pasta, 'RESULTADOS.md'), encoding='utf-8').read()
confere('**Chuva: troca para C1.**' in txt, 'a regra escolhe o C1 na chuva')
confere('**Radiação e ETo: troca para C3.**' in txt or '**Radiação e ETo: troca para C1.**' in txt,
        'a regra escolhe um método na radiação')
# C3 da radiação: |viés| 0 (C1 0,1); diferença 0,1 >= 0,05, então vence o menor, o C3
confere('**Radiação e ETo: troca para C3.**' in txt, 'desempate da radiação')
mc = t.metricas_chuva(t.c3_chuva_regional(pd.concat(pd.read_csv(a) for a in
                                                     sorted(__import__('glob').glob(os.path.join(pasta, 'regional', '*.csv')))),
                                          pesos).query('ano == ano_alvo and variavel == "pr"')[['regiao', 'ano', 'mes', 'metodo', 'valor']])
confere(abs(mc['C0']['mediana5'] - 10) < 1.5 and mc['C1']['mediana5'] < 1.5, 'viés sintético recuperado')
# C3 corrige o C0 pela razão dos 5 anos anteriores (~1/0,9): fica perto do BR-DWGD
confere(mc['C3']['mediana5'] < 2.0, f"C3 sintético {mc['C3']['mediana5']:.2f}")
print(f'{ok} conferências ok')
