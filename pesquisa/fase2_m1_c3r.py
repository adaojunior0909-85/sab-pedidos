# Fase 2, módulo M1-C3R: a razão do C3 só onde o viés é consistente (pesquisa/PROTOCOLO_CORRECAO_FASE2.md, congelado no
# commit 9a12309 antes de rodar). Sem Earth Engine: usa os dados da fase 1 (pesquisa/resultados_correcao_era5/).
#   C3R na região e no mês do ano-alvo Y: a razão do C3 se, nos 5 anos anteriores, |razão - 1| >= 0,05 E a razão de cada
#   ano estiver do mesmo lado de 1 em pelo menos 4 dos 5; senão, razão 1. Como a razão é uma constante da região e do
#   mês, o C3R da região é EXATAMENTE a linha do C3 (razão aplicada) ou a do C0 (razão 1): chuva, dias de chuva, Rx1day.
#   Brasil: a média das 5 regiões pesada pela área entregue (pesos pelo ajuste de mínimos quadrados Brasil = soma pesos x
#   região, nos 120 meses do C0; conferido contra o próprio Brasil do C3).
#   Regra (contra o C3, a V1.8): ver o protocolo, M1.
#     python pesquisa/fase2_m1_c3r.py
import glob
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import validar_correcao_era5 as t  # noqa: E402

FASE1 = os.path.join(AQUI, 'resultados_correcao_era5')
SAIDA = os.path.join(AQUI, 'resultados_fase2')
LIMIAR_RAZAO, ANOS_MESMO_LADO = 0.05, 4
PIORA_MEDIANA, QUEDA_FRACAO, MELHORA_PIOR = 0.5, 0.20, 2.0
QUEDA_R, CRESCE_EXT = 0.02, 0.05


def consistente(razoes_ano, razao):
    """A razão do C3 é aplicada? |razão-1| >= 0,05 e >= 4 dos 5 anos do mesmo lado de 1."""
    if abs(razao - 1) < LIMIAR_RAZAO:
        return False
    lado = np.sign(razao - 1)
    return sum(1 for r in razoes_ano if np.isfinite(r) and np.sign(r - 1) == lado) >= ANOS_MESMO_LADO


def pesos_area(alvo):
    """Pesos das 5 regiões no Brasil (mínimos quadrados nos totais mensais do C0, normalizados para somar 1)."""
    p = alvo[(alvo.metodo == 'C0') & (alvo.variavel == 'pr')].pivot_table(index=['ano', 'mes'], columns='regiao',
                                                                          values='valor')
    w, *_ = np.linalg.lstsq(p[t.REGIOES5].values, p['Brasil'].values, rcond=None)
    return dict(zip(t.REGIOES5, w / w.sum()))


def decisoes(df):
    """{(Y, mes, regiao): True se a razão é aplicada}, com as razões por ano dos 5 anos anteriores."""
    out = {}
    lb = df[(df.variavel == 'pr') & (df.ano < df.ano_alvo)]
    for (Y, mes, r), g in lb.groupby(['ano_alvo', 'mes', 'regiao']):
        if r not in t.REGIOES5:
            continue
        br = g[g.metodo == 'BR'].set_index('ano').valor
        c0 = g[g.metodo == 'C0'].set_index('ano').valor
        anos = br.index.intersection(c0.index)
        razoes_ano = [br[a] / c0[a] if c0[a] > 0 else np.nan for a in anos]
        out[(Y, mes, r)] = consistente(razoes_ano, t.razao_c3(br.loc[anos], c0.loc[anos]))
    return out


def montar_c3r(alvo, dec, w):
    """Linhas do C3R: em cada região e mês, a linha do C3 ou a do C0; o Brasil pela média pesada das regiões."""
    vs = ['pr', 'wet', 'rx', 'drx']
    base = alvo[alvo.variavel.isin(vs) & alvo.metodo.isin(['C0', 'C3']) & alvo.regiao.isin(t.REGIOES5)]
    linhas = []
    for (Y, mes, r), g in base.groupby(['ano_alvo', 'mes', 'regiao']):
        fonte = 'C3' if dec.get((Y, mes, r), False) else 'C0'
        for _, x in g[g.metodo == fonte].iterrows():
            linhas.append(dict(x, metodo='C3R'))
    c3r = pd.DataFrame(linhas)
    br = []
    for (Y, mes, v), g in c3r.groupby(['ano_alvo', 'mes', 'variavel']):
        val = sum(w[r] * g[g.regiao == r].valor.iloc[0] for r in t.REGIOES5 if (g.regiao == r).any())
        br.append({'ano_alvo': Y, 'ano': Y, 'mes': mes, 'regiao': 'Brasil', 'metodo': 'C3R', 'variavel': v, 'valor': val})
    return pd.concat([c3r, pd.DataFrame(br)], ignore_index=True)


def main():
    os.makedirs(SAIDA, exist_ok=True)
    df = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(FASE1, 'regional', '*.csv'))))
    alvo = df[df.ano == df.ano_alvo]
    w = pesos_area(alvo)
    # conferência dos pesos: o Brasil do C3 reconstruído das regiões
    p3 = alvo[(alvo.metodo == 'C3') & (alvo.variavel == 'pr')].pivot_table(index=['ano', 'mes'], columns='regiao',
                                                                           values='valor')
    erro_pesos = float(np.max(np.abs(p3[t.REGIOES5].values @ np.array([w[r] for r in t.REGIOES5]) / p3['Brasil'] - 1)))
    dec = decisoes(df)
    alvo2 = pd.concat([alvo, montar_c3r(alvo, dec, w)], ignore_index=True)
    ks = ['C0', 'C3', 'C3R']
    t.METODOS = ks                                   # as funções de métrica percorrem estes métodos
    mc, mx = t.metricas_chuva(alvo2), t.metricas_extremos(alvo2)
    # p99 nos 1.500 pixels: C3R = C0 x (razão se aplicada, senão 1)
    pix = os.path.join(FASE1, 'pixels')
    pontos = pd.read_csv(os.path.join(pix, 'pontos.csv'))
    dias = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(pix, 'dias_*.csv.gz'))))
    ag = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(pix, 'agregados_*.csv.gz'))))
    razoes = {}
    lb = df[(df.variavel == 'pr') & (df.ano < df.ano_alvo)]
    for (Y, mes, r), g in lb.groupby(['ano_alvo', 'mes', 'regiao']):
        if r in t.REGIOES5:
            razoes[(Y, mes, r)] = t.razao_c3(g[g.metodo == 'BR'].valor, g[g.metodo == 'C0'].valor)
    px = t.chuva_pixels(ag, dias, pontos, razoes)
    pm = pontos.set_index('pid')
    reg = np.array([pm.loc[p, 'regiao'] for p in px.pid])
    anos = (px.dia // 10000).values
    meses = px.mes.values
    aplica = np.array([dec.get((Y, m, r), False) for Y, m, r in zip(anos, meses, reg)])
    px['C3R'] = np.where(aplica, px.C3.values, px.C0.values)
    mp = t.metricas_pixels(px, ks)
    # regra
    c3 = mc['C3']
    k = mc['C3R']
    c1 = k['mediana5'] - c3['mediana5'] <= PIORA_MEDIANA + t.EPS
    soma = lambda m: sum(abs(mx[m][r]['fracao'] - mx['BR'][r]['fracao']) for r in t.REGIOES5)
    queda_fr = 1 - soma('C3R') / soma('C3') if soma('C3') else 0.0
    pior3 = max(c3['mediana_regiao'][r] for r in t.REGIOES5)
    regiao_pior = max(t.REGIOES5, key=lambda r: c3['mediana_regiao'][r])
    melhora_pior = c3['mediana_regiao'][regiao_pior] - k['mediana_regiao'][regiao_pior]
    c2 = queda_fr >= QUEDA_FRACAO - t.EPS or melhora_pior >= MELHORA_PIOR - t.EPS
    quedas_r = {r: c3['r_anom'][r] - k['r_anom'][r] for r in t.REGIOES5}
    c3_ = all(np.isfinite(q) and q <= QUEDA_R + t.EPS for q in quedas_r.values())
    rx_ok = all(mx['C3R'][r]['erro_rx'] <= (1 + CRESCE_EXT) * mx['C3'][r]['erro_rx'] + t.EPS for r in t.REGIOES5)
    p99_ok = mp['C3R']['erro_p99'] <= (1 + CRESCE_EXT) * mp['C3']['erro_p99'] + t.EPS
    passa = c1 and c2 and c3_ and rx_ok and p99_ok
    # relato 2026 x CHIRPS: razões por ano 2021-2025 da Parte A
    pa = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(AQUI, 'resultados_metodo_2026', 'parte_a', '*.csv'))))
    pa = pa[(pa.variavel == 'pr_mm') & pa.regiao.isin(t.REGIOES5)]
    dec26 = {}
    for (mes, r), g in pa.groupby(['mes', 'regiao']):
        ra = [e / m if m > 0 else np.nan for e, m in zip(g.entregue, g.metodo_2026)]
        dec26[(mes, r)] = consistente(ra, t.razao_c3(g.entregue, g.metodo_2026))
    ch = pd.read_csv(os.path.join(FASE1, 'chirps_2026.csv'))
    s = {s_: ch[(ch.ano == 2026) & (ch.serie == s_)] for s_ in ('C0', 'C3', 'CHIRPS')}
    tot = {}
    for r in t.REGIOES5:
        c3r_r = sum((s['C3'] if dec26.get((m, r)) else s['C0']).query('regiao == @r and mes == @m').valor.sum()
                    for m in sorted(s['C0'].mes.unique()))
        tot[r] = 100 * (c3r_r / s['CHIRPS'].query('regiao == @r').valor.sum() - 1)
    def vies26(serie, r):
        return 100 * (ch[(ch.ano == 2026) & (ch.regiao == r) & (ch.serie == serie)].valor.sum()
                      / ch[(ch.ano == 2026) & (ch.regiao == r) & (ch.serie == 'CHIRPS')].valor.sum() - 1)
    def regua(r):
        return 100 * (ch[(ch.ano == 2024) & (ch.regiao == r) & (ch.serie == 'BR-DWGD')].valor.sum()
                      / ch[(ch.ano == 2024) & (ch.regiao == r) & (ch.serie == 'CHIRPS')].valor.sum() - 1)
    aplicadas = sum(dec.values())
    L = ['# Fase 2, M1-C3R: a razão do C3 só onde o viés é consistente', '',
         'Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (congelado no commit 9a12309 antes de rodar). Sem Earth Engine: '
         'os dados da fase 1. Base de comparação: o C3 (a V1.8).', '',
         f'Razão aplicada em {aplicadas} de {len(dec)} combinações ano-alvo × mês × região '
         f'({100 * aplicadas / len(dec):.0f}%). Pesos do Brasil (área): ' +
         ', '.join(f'{r} {w[r]:.3f}' for r in t.REGIOES5) + f' (conferência no C3: erro máx. {100 * erro_pesos:.2f}%).', '',
         '| Método | ' + ' | '.join(t.REGIOES5) + ' | Mediana das 5 |', '|---|' + '---|' * 6]
    for m in ks:
        L.append(f'| {m} | ' + ' | '.join(f"{mc[m]['mediana_regiao'][r]:.1f}% (r {mc[m]['r_anom'][r]:.2f})"
                                           for r in t.REGIOES5) + f" | {mc[m]['mediana5']:.2f}% |")
    L += ['', '| Método | Dias de chuva: afastamento somado (p.p.) | p99 (1.500 pixels) |', '|---|---|---|']
    for m in ks:
        L.append(f"| {m} | {100 * soma(m):.2f} | {100 * mp[m]['erro_p99']:.1f}% |")
    s_ = {True: '✅', False: '❌'}
    L += ['', '## Regra (contra o C3)', '',
          f"1. mediana não piora > 0,5 p.p.: {s_[c1]} ({k['mediana5'] - c3['mediana5']:+.2f} p.p.)",
          f"2. dias de chuva −20% ({100 * queda_fr:+.1f}%) ou pior região ({regiao_pior}) −2 p.p. "
          f"({melhora_pior:+.2f} p.p.): {s_[c2]}",
          f"3. r_anomalias não cai > 0,02: {s_[c3_]} (maior queda {max(quedas_r.values()):+.3f})",
          f"4. Rx1day e p99 não crescem > 5%: {s_[rx_ok and p99_ok]}", '',
          f"**M1-C3R: {'PASSA — substitui o C3 (gravação só com autorização)' if passa else 'não passa; o C3 (V1.8) fica'}.**",
          '', '## Só relato: 2026 × CHIRPS (jan–set, viés do total, %)', '',
          '| Região | 2024 (régua) | 2026 C0 (V1.7) | 2026 C3 (V1.8) | 2026 C3R |', '|---|---|---|---|---|']
    for r in t.REGIOES5:
        L.append(f'| {r} | {regua(r):+.1f} | {vies26("C0", r):+.1f} | {vies26("C3", r):+.1f} | {tot[r]:+.1f} |')
    with open(os.path.join(SAIDA, 'RESULTADOS_M1_C3R.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
