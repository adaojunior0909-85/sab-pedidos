# O histórico do SAB (1961-2025), década por década, contra referências de fora. SÓ LEITURA no Earth Engine.
#   TerraClimate (Abatzoglou et al., 2018; IDAHO_EPSCOR/TERRACLIMATE, mensal, ~4 km, 1958-): chuva, Tmax, Tmin, VPD,
#     radiação, vento, ETo (Penman-Monteith), ET real, água no solo e escoamento. Vem do WorldClim + CRU TS + JRA-55:
#     parte das estações do CRU são as mesmas do INMET, então é uma referência SEMI-independente do BR-DWGD.
#   CHIRPS (Funk et al., 2015; UCSB-CHG/CHIRPS/PENTAD, 1981-): chuva por satélite + estações.
# Para cada mês de 1961 a 2025, a média (ou o total) do mês por região, nos pixels entregues. Por década e região:
#   viés (somas: % do total; médias: diferença) e correlação das anomalias mensais (ciclo do ano retirado).
# REGRA FIXADA ANTES DE RODAR (25/11/2026), para achar DEGRAU no tempo (não o nível, que é de cada fonte):
#   uma década é SUSPEITA numa variável/região se (a) o viés dela se afasta da mediana dos vieses das 7 décadas por
#   mais que a tolerância (a mesma do validar_metodo_2026) ou (b) a correlação das anomalias dela fica abaixo de 0,5
#   quando a mediana das décadas é 0,7 ou mais.
#     python pesquisa/validar_historico.py      (retomável; TEMPO_MAX_MIN limita: sai com código 3 se faltar ano)
import glob
import os
import sys
import time
from datetime import date, timedelta

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ee  # noqa: E402
import validar_metodo_2026 as vm  # noqa: E402  (inicia o Earth Engine; regiões, coleção entregue e tolerâncias)

v, sp = vm.v, vm.sp
SAIDA = os.path.join(AQUI, 'resultados_historico')
TC = ee.ImageCollection('IDAHO_EPSCOR/TERRACLIMATE')
CHIRPS = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD').select('precipitation')
# variável do SAB: (banda do TerraClimate, escala para a unidade do SAB por dia ou por mês, soma no mês?)
PARES = {
    'pr_mm': ('pr', 'ppt', 1.0, True),
    'tmax_C': ('tmax_C', 'tmmx', 0.1, False),
    'tmin_C': ('tmin_C', 'tmmn', 0.1, False),
    'vpd': ('vpd', 'vpd', 0.01, False),
    'rs': ('rs', 'srad', 0.1 * 0.0864, False),             # W/m² -> MJ/m²/dia
    'u2': ('u2', 'vs', 0.01 * 0.748, False),               # 10 m -> 2 m (FAO-56)
    'et_potencial': ('et_potencial', 'pet', 0.1, True),
    'et_real': ('et_real', 'aet', 0.1, True),
    'agua_solo': ('soil_moisture_0_100cm_m3_m3', 'soil', 0.1, False),   # mm x m³/m³: só a correlação vale
    'escoamento': ('runoff', 'ro', 1.0, True),
}
SOMA = {k for k, p in PARES.items() if p[3]}
TOL = {**{k: 5.0 for k in SOMA}, 'tmax_C': 0.5, 'tmin_C': 0.5, 'vpd': 0.1, 'rs': 0.5, 'u2': 0.2, 'agua_solo': None}
DECADAS = [(1961, 1970), (1971, 1980), (1981, 1990), (1991, 2000), (2001, 2010), (2011, 2020), (2021, 2025)]
NOME = {'pr_mm': 'Chuva (TerraClimate)', 'pr_chirps': 'Chuva (CHIRPS, desde 1981)', 'tmax_C': 'Tmax', 'tmin_C': 'Tmin',
        'vpd': 'VPD', 'rs': 'Radiação', 'u2': 'Vento', 'et_potencial': 'ETo', 'et_real': 'ET real',
        'agua_solo': 'Umidade do solo 0-100 cm', 'escoamento': 'Escoamento total'}


def imagens_mes(ano, mes):
    d0 = date(ano, mes, 1)
    d1 = (d0 + timedelta(days=32)).replace(day=1)
    ini, fim = d0.isoformat(), d1.isoformat()
    col = sp.colecao(vm.BRASIL, ini, fim).map(
        lambda i: i.addBands(i.select('runoff_sup_mm').add(i.select('runoff_sub_mm')).rename('runoff')))
    soma = col.select(['pr_mm', 'et_potencial', 'et_real', 'runoff']).sum()
    media = col.select(['tmax_C', 'tmin_C', 'vpd', 'rs', 'u2', 'soil_moisture_0_100cm_m3_m3']).mean()
    sab = ee.Image.cat([soma, media])
    tc = ee.Image(TC.filterDate(ini, fim).first())
    bandas = []
    for k, (b_sab, b_tc, esc, _) in PARES.items():
        bandas += [sab.select(b_sab).rename(f's_{k}'), tc.select(b_tc).multiply(esc).rename(f'r_{k}')]
    if ano >= 1981:
        bandas.append(CHIRPS.filterDate(ini, fim).sum().rename('r_pr_chirps'))
    return ee.Image.cat(bandas).toFloat()


def main():
    regs = v.regioes()
    pasta = os.path.join(SAIDA, 'anos')
    os.makedirs(pasta, exist_ok=True)
    ultimo_tc = int(v.ultimo(TC)[:4])
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)
    for ano in range(1961, 2026):
        arq = os.path.join(pasta, f'{ano}.csv')
        if os.path.exists(arq):
            continue
        if time.time() > limite:
            print('Tempo desta vez acabou; a próxima retoma daqui.')
            raise SystemExit(3)
        t0, linhas = time.time(), []
        for mes in range(1, 13):
            img = imagens_mes(ano, mes) if ano <= ultimo_tc else None
            if img is None:
                continue
            for tentativa in range(4):
                try:
                    res = vm.reduzir(img, regs, img.bandNames().getInfo())
                    break
                except Exception as e:  # noqa: BLE001
                    print(f'   ⚠️ {ano}-{mes:02d}: {str(e)[:150]}', flush=True)
                    time.sleep(20 * (tentativa + 1))
            else:
                raise RuntimeError(f'{ano}-{mes:02d}: não deu depois de 4 tentativas')
            for reg, p in res.items():
                for k in list(PARES) + ['pr_chirps']:
                    s = p.get('s_pr_mm' if k == 'pr_chirps' else f's_{k}')
                    linhas.append({'regiao': reg, 'ano': ano, 'mes': mes, 'variavel': k, 'sab': s,
                                   'referencia': p.get(f'r_{k}')})
        if not linhas:
            continue                       # o TerraClimate ainda não tem esse ano
        pd.DataFrame(linhas).to_csv(arq, index=False)
        print(f'   {ano} pronto em {time.time() - t0:.0f} s', flush=True)
    resumo(pasta)


def resumo(pasta):
    df = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(pasta, '*.csv')))).dropna()
    for k in ('sab', 'referencia'):
        df[f'a_{k}'] = df[k] - df.groupby(['regiao', 'variavel', 'mes'])[k].transform('mean')
    regioes = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil']
    L = ['# O histórico do SAB década por década (1961–2025) contra TerraClimate e CHIRPS', '',
         'Em cada célula: viés da década (somas: % do total; médias: diferença na unidade) / correlação das anomalias '
         'mensais. ⚠️ = degrau (regra fixada antes de rodar, no cabeçalho do `pesquisa/validar_historico.py`). A '
         'umidade do solo do TerraClimate é em mm: só a correlação vale.', '']
    suspeitas = []
    for k in ['pr_mm', 'pr_chirps', 'tmax_C', 'tmin_C', 'vpd', 'rs', 'u2', 'et_potencial', 'et_real', 'agua_solo', 'escoamento']:
        L += [f'## {NOME[k]}', '', '| Década | ' + ' | '.join(regioes) + ' |', '|---|' + '---|' * len(regioes)]
        cel = {}
        for reg in regioes:
            g = df[(df.variavel == k) & (df.regiao == reg)]
            linhas = []
            for a, z in DECADAS:
                x = g[g.ano.between(a, z)]
                if len(x) < 24:
                    linhas.append(None)
                    continue
                vies = (100 * (x.sab.sum() / x.referencia.sum() - 1) if (k in SOMA or k == 'pr_chirps')
                        else (x.sab - x.referencia).mean())
                linhas.append((vies, x.a_sab.corr(x.a_referencia)))
            vs = pd.Series([x[0] for x in linhas if x]).median()
            rs = pd.Series([x[1] for x in linhas if x]).median()
            tol = TOL.get('pr_mm' if k == 'pr_chirps' else k)
            for (a, z), x in zip(DECADAS, linhas):
                if x is None:
                    cel.setdefault((a, z), []).append('-')
                    continue
                degrau = (tol is not None and abs(x[0] - vs) > tol) or (rs >= 0.7 and x[1] < 0.5)
                if degrau:
                    suspeitas.append(f'{NOME[k]}, {reg}, {a}-{z}')
                cel.setdefault((a, z), []).append(f'{"⚠️ " if degrau else ""}{x[0]:+.1f} / {x[1]:.2f}')
        for (a, z) in DECADAS:
            L.append(f'| {a}-{z} | ' + ' | '.join(cel[(a, z)]) + ' |')
        L.append('')
    L += ['## Degraus encontrados', '', '; '.join(suspeitas) if suspeitas else 'Nenhum.']
    with open(os.path.join(SAIDA, 'RESULTADOS.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
