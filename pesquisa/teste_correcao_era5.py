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
confere(np.allclose(t.chuva_corrigida([10.0, 100.0, 0.0], 2.0, 40.0), [20.0, 100.0, 0.0]), 'teto da chuva')
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
confere(t.pedacos(2016) == {'a': (1986, 2000), 'b': (2001, 2005), 'c': (2006, 2015)}, 'pedaços')
m = pd.DataFrame({'ano': [1, 1, 2, 2], 'mes': [1, 2, 1, 2], 'metodo': [1, 5, 3, 7], 'ref': [2, 6, 4, 8]})
confere(abs(t.r_anomalias(m) - 1) < 1e-12, 'r_anomalias perfeito')
ag = pd.DataFrame({'pid': [0, 0], 'ano': [2000, 2001], 'mes': [1, 1], 's_era': [31.0, 62.0], 'n_era': [31, 31],
                   's_br': [62.0, 62.0], 'n_br': [31, 31]})
c = t.clima_pixels(ag, 2000, 2001)
confere(abs(c.loc[(0, 1), 'm_era'] - 1.5) < 1e-12 and abs(c.loc[(0, 1), 'm_br'] - 2) < 1e-12, 'clima dos pixels')
d = pd.DataFrame({'pid': [0, 0], 'dia': [20160101, 20160102], 'era': [1.0, 3.0], 'br': [2.0, np.nan]})
a = t.agregar_dias(d)
confere(a.s_era.iloc[0] == 4 and a.n_br.iloc[0] == 1 and a.ano.iloc[0] == 2016, 'agregar os dias')
r, dl = t.deltas_c3([{'regiao': 'Norte', 'ano': y, 'metodo': mt, 'variavel': v, 'valor': val}
                     for y in (2011, 2012) for mt, v, val in (('BR', 'pr', 110), ('C0', 'pr', 100),
                                                              ('BR', 'rs', 18), ('C0', 'rs', 18.5))])
confere(abs(r['Norte'] - 1.1) < 1e-12 and abs(dl['Norte'] + 0.5) < 1e-12 and r['Sul'] == 1.0, 'razão e Δ do C3')

# --- ponta a ponta sintético
# chuva: o C0 chove 0,90 x o BR-DWGD, o C1 acerta, o C2 chove 0,95 x, o C3 = 0,90 x 1/0,9 (acerta)
# extremos regionais: o C3 erra muito o Rx1day (reprova 4b); radiação: o C3 acerta, o C1 quase
rng = np.random.default_rng(1)
pasta = tempfile.mkdtemp()
t.SAIDA = pasta
os.makedirs(os.path.join(pasta, 'regional'))
os.makedirs(os.path.join(pasta, 'pixels'))
f_pr = {'C0': 0.90, 'C1': 1.00, 'C2': 0.95, 'C3': 1.00}
f_wet = {'C0': 0.40, 'C1': 0.41, 'C2': 0.405, 'C3': 0.40}
e_rx = {'C0': 0.20, 'C1': 0.19, 'C2': 0.20, 'C3': 0.30}
rad = {'C0': (0.6, 1.035), 'C1': (0.1, 1.005), 'C2': (0.3, 1.02), 'C3': (0.0, 1.0)}
for Y in t.ANOS_TESTE:
    for mes in range(1, 13):
        L = []
        dias = t.dias_no_mes(Y, mes)
        for r in t.REGIOES:
            def add(ano, met, var, val):
                L.append(dict(ano_alvo=Y, ano=ano, mes=mes, regiao=r, metodo=met, variavel=var, valor=val))
            for a in range(Y - 5, Y):
                br = 100 + 50 * np.sin(mes) + rng.normal(0, 10)
                add(a, 'BR', 'pr', br)
                add(a, 'C0', 'pr', 0.9 * br)
                add(a, 'BR', 'rs', 18.0)
                add(a, 'C0', 'rs', 18.6)
            br = 100 + 50 * np.sin(mes) + rng.normal(0, 10)
            ruido = rng.normal(0, 1)
            add(Y, 'BR', 'pr', br)
            add(Y, 'BR', 'wet', 0.40 * dias)
            add(Y, 'BR', 'n', dias)
            add(Y, 'BR', 'rx', 40.0)
            rs, eto = 18 + rng.normal(0, 0.5), 120 + rng.normal(0, 3)
            add(Y, 'BR', 'rs', rs)
            add(Y, 'BR', 'eto', eto)
            for k in t.METODOS:
                add(Y, k, 'pr', f_pr[k] * br + ruido)
                add(Y, k, 'wet', f_wet[k] * dias)
                add(Y, k, 'rx', 40.0)
                add(Y, k, 'drx', e_rx[k] * 40.0)
                add(Y, k, 'rs', rs + rad[k][0])
                add(Y, k, 'eto', eto * rad[k][1])
        pd.DataFrame(L).to_csv(os.path.join(pasta, 'regional', f'{Y}_{mes:02d}.csv'), index=False)
# pixels: o ERA5 bruto chove 0,8 x o BR-DWGD em todos os anos (C0 = C1 = C2 nos pixels; C3 = C0 x 1/0,9)
pts = pd.DataFrame({'pid': range(10), 'lon': 0.0, 'lat': 0.0, 'regiao': t.REGIOES5 * 2,
                    **{f'prmax_{mm:02d}': 80.0 for mm in range(1, 13)}})
pts.to_csv(os.path.join(pasta, 'pixels', 'pontos.csv'), index=False)
for ano in range(1986, 2026):
    ds = pd.date_range(f'{ano}-01-01', f'{ano}-12-31').strftime('%Y%m%d').astype(int)
    br = np.where(rng.random((10, len(ds))) < 0.4, rng.gamma(0.8, 12, (10, len(ds))), 0.0)
    df = pd.DataFrame({'pid': np.repeat(range(10), len(ds)), 'dia': np.tile(ds, 10), 'era': 0.8 * br.ravel(),
                       'br': br.ravel()})
    if ano in t.ANOS_TESTE:
        df.to_csv(os.path.join(pasta, 'pixels', f'dias_{ano}.csv.gz'), index=False)
    else:
        t.agregar_dias(df).to_csv(os.path.join(pasta, 'pixels', f'agregados_{ano}.csv.gz'), index=False)
t.resumo()
txt = open(os.path.join(pasta, 'RESULTADOS.md'), encoding='utf-8').read()
confere('**Chuva: troca para C1.**' in txt, 'a regra escolhe o C1 na chuva (o C3 reprova no Rx1day)')
confere('**Radiação e ETo: troca para C3.**' in txt, 'a regra escolhe o C3 na radiação (0,1 MJ melhor que o C1)')
confere('| C3 |' in txt and '❌' in txt.split('**Chuva:')[0].split('| C3 |')[-1], 'C3 reprovado na chuva')
alvo = pd.concat(pd.read_csv(a) for a in sorted(__import__('glob').glob(os.path.join(pasta, 'regional', '*.csv'))))
alvo = alvo[alvo.ano == alvo.ano_alvo]
mc = t.metricas_chuva(alvo)
confere(abs(mc['C0']['mediana5'] - 10) < 1.5 and mc['C1']['mediana5'] < 1.5, 'viés sintético recuperado')
mx = t.metricas_extremos(alvo)
confere(abs(mx['C1']['Norte']['fracao'] - 0.41) < 1e-9 and abs(mx['C3']['Sul']['erro_rx'] - 0.30) < 1e-9,
        'extremos regionais')
# o C1 se afasta 1 p.p. a mais na fração de dias com chuva (< 2 p.p.): passa; com 3 p.p. reprovaria
mx2 = {k: {r: dict(v) for r, v in d.items()} for k, d in mx.items()}
for r in t.REGIOES:
    mx2['C1'][r]['fracao'] = 0.43
venc, det = t.decidir_chuva(mc, mx2, {'C0': {'erro_p99': 0.1}, 'C1': {'erro_p99': 0.1}, 'C2': {'erro_p99': 0.1},
                                      'C3': {'erro_p99': 0.1}, 'fracao_br': 0.4})
confere(not det['C1']['c4a'] and venc == 'C2', f'4a reprova o C1 com 3 p.p.; vence o C2 ({venc})')
print(f'{ok} conferências ok')
