# O banco contra VÁRIAS referências independentes, mês a mês, 1961–2025 (fase 2, emenda 1 do M5; protocolo
# pesquisa/PROTOCOLO_CORRECAO_FASE2.md, congelado ANTES de rodar). SÓ LEITURA no Earth Engine.
# Cada fonte roda à parte (retomável, um CSV por ano) e o resumo junta todas, com o TerraClimate e o CHIRPS do
# pesquisa/validar_historico.py:
#   era5      ERA5-Land bruto (ECMWF/ERA5_LAND/DAILY_AGGR), 1961–2025: chuva, Tmax, Tmin, UR, VPD, radiação, vento
#             (independente só para as variáveis do BR-DWGD; as do modelo vêm dele e ficam de fora)
#   gldas20   GLDAS-2.0 Noah 3 h (NASA/GLDAS/V20/NOAH/G025/T3H), 1961–2014: as 16 variáveis (a conta da Parte B)
#   gldas21   GLDAS-2.1 Noah 3 h (NASA/GLDAS/V021/NOAH/G025/T3H), 2000–2025: idem
#   chuva     PERSIANN-CDR (NOAA/PERSIANN-CDR, diário, 1983–) e IMERG mensal (NASA/GPM_L3/IMERG_MONTHLY_V07, 2000–)
#   mod16     MOD16A2 (MODIS/061/MOD16A2, 8 dias, 2001–): ET real (e a PET contra a ETo, só correlação)
# Regiões: as 5, o Brasil e os 27 estados (FAO GAUL 2015), pixels entregues (classes 1–3), grade do SAB.
# REGRA (fixada antes, a mesma do validar_historico.py): numa fonte, a década é DEGRAU se o viés dela se afasta da
#   mediana das décadas por mais que a tolerância, ou se a correlação das anomalias fica < 0,5 quando a mediana é >= 0,7;
#   década com < 24 meses fica de fora; a fonte precisa ter >= 3 décadas. CONFIRMADO = degrau em >= 2 referências
#   independentes (GLDAS-2.0 e 2.1 contam como uma; ERA5-Land não conta para as variáveis do modelo).
#     python pesquisa/validar_multifonte.py <fonte>     (TEMPO_MAX_MIN limita: sai com código 3 se faltar ano)
#     python pesquisa/validar_multifonte.py resumo
import glob
import os
import sys
import time
from datetime import date, timedelta

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
SAIDA = os.path.join(AQUI, 'resultados_multifonte')
HIST = os.path.join(AQUI, 'resultados_historico', 'anos')
FONTES = {'era5': (1961, 2025), 'gldas20': (1961, 2014), 'gldas21': (2000, 2025), 'chuva': (1983, 2025),
          'mod16': (2001, 2025)}
DECADAS = [(1961, 1970), (1971, 1980), (1981, 1990), (1991, 2000), (2001, 2010), (2011, 2020), (2021, 2025)]
SOMA = {'pr_mm', 'et_potencial', 'et_real', 'transpiracao_mm', 'runoff', 'runoff_sup_mm', 'runoff_sub_mm'}
TOL = {**{k: 5.0 for k in SOMA}, 'tmax_C': 0.5, 'tmin_C': 0.5, 'RH': 3.0, 'vpd': 0.1, 'rs': 0.5, 'u2': 0.2,
       'tsolo_C': 0.5, 'tfolha_C': 0.5, 'soil_moisture_0_5cm_m3_m3': 0.02, 'soil_moisture_0_100cm_m3_m3': None}
NOME = {'pr_mm': 'Chuva', 'tmax_C': 'Tmax', 'tmin_C': 'Tmin', 'RH': 'Umidade relativa', 'vpd': 'VPD',
        'rs': 'Radiação', 'u2': 'Vento', 'et_potencial': 'ETo', 'et_real': 'ET real', 'transpiracao_mm': 'Transpiração',
        'tsolo_C': 'Temperatura do solo', 'tfolha_C': 'Temperatura da folha',
        'soil_moisture_0_5cm_m3_m3': 'Umidade do solo 0-5 cm', 'soil_moisture_0_100cm_m3_m3': 'Umidade do solo 0-100 cm',
        'runoff': 'Escoamento total'}
DO_BRDWGD = {'pr_mm', 'tmax_C', 'tmin_C', 'RH', 'vpd', 'rs', 'u2', 'et_potencial'}
# nome da fonte -> grupo independente (para a confirmação)
GRUPO = {'terraclimate': 'TerraClimate', 'chirps': 'CHIRPS', 'persiann': 'PERSIANN', 'imerg': 'IMERG',
         'gldas20': 'GLDAS', 'gldas21': 'GLDAS', 'era5': 'ERA5-Land', 'mod16': 'MOD16'}
REGIOES = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil']


# ============================================================ contas puras
def decadas(g, var):
    """[(década, viés, r) ou None] de uma série mensal (colunas ano, mes, sab, referencia) já com anomalias."""
    out = []
    for a, z in DECADAS:
        x = g[g.ano.between(a, z)].dropna(subset=['sab', 'referencia'])
        if len(x) < 24:
            out.append(None)
            continue
        vies = (100 * (x.sab.sum() / x.referencia.sum() - 1) if var in SOMA and x.referencia.sum()
                else (x.sab - x.referencia).mean())
        out.append(((a, z), vies, x.a_sab.corr(x.a_referencia)))
    return out


def degraus(linhas, var):
    """{década: True/False} pela regra; {} se a fonte tem < 3 décadas."""
    ok = [x for x in linhas if x]
    if len(ok) < 3:
        return {}
    vs = pd.Series([x[1] for x in ok]).median()
    rs = pd.Series([x[2] for x in ok]).median()
    tol = TOL.get(var)
    return {x[0]: bool((tol is not None and abs(x[1] - vs) > tol) or (rs >= 0.7 and x[2] < 0.5)) for x in ok}


def conta_independente(fontes_com_degrau, var):
    """Quantos grupos independentes marcam o degrau (ERA5-Land não conta para as variáveis do modelo)."""
    g = {GRUPO[f] for f in fontes_com_degrau if not (f == 'era5' and var not in DO_BRDWGD)}
    return len(g), sorted(g)


# ============================================================ Earth Engine
def _ee():
    import validar_metodo_2026 as vm      # inicia o Earth Engine e bloqueia escrita? (só leitura: nada aqui grava)
    return vm


def sab_mes(vm, ini, fim):
    col = vm.sp.colecao(vm.BRASIL, ini, fim)
    img = vm.mensal(col, ini, fim)
    return img.addBands(img.select('runoff_sup_mm').add(img.select('runoff_sub_mm')).rename('runoff'))


def ref_era5(vm, ini, fim):
    ee = vm.ee
    col = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').filterDate(ini, fim)

    def dia(i):
        tx = i.select('temperature_2m_max').subtract(273.15)
        tn = i.select('temperature_2m_min').subtract(273.15)
        t = i.select('temperature_2m').subtract(273.15)
        td = i.select('dewpoint_temperature_2m').subtract(273.15)
        es = lambda x: x.expression('0.6108 * exp(17.27 * T / (T + 237.3))', {'T': x})
        rh = td.expression('100 * exp(17.625 * Td / (243.04 + Td)) / exp(17.625 * T / (243.04 + T))', {'Td': td, 'T': t})
        vpd = es(tx).add(es(tn)).divide(2).subtract(es(td)).max(0)
        return ee.Image.cat([
            i.select('total_precipitation_sum').multiply(1000).max(0).rename('pr_mm'), tx.rename('tmax_C'),
            tn.rename('tmin_C'), rh.min(100).rename('RH'), vpd.rename('vpd'),
            i.select('surface_solar_radiation_downwards_sum').divide(1e6).rename('rs'),
            i.select('u_component_of_wind_10m').hypot(i.select('v_component_of_wind_10m')).multiply(0.748).rename('u2')])
    d = col.map(dia)
    return ee.Image.cat([d.select('pr_mm').sum(), d.select(['tmax_C', 'tmin_C', 'RH', 'vpd', 'rs', 'u2']).mean()])


def ref_gldas(vm, ini, fim, colecao):
    vm.GLDAS = vm.ee.ImageCollection(colecao)              # a conta da Parte B, com a coleção pedida
    g = vm.gldas_mes(ini, fim)
    return g.addBands(g.select('runoff_sup_mm').add(g.select('runoff_sub_mm')).rename('runoff'))


def ref_chuva(vm, ano, ini, fim, d0, d1):
    ee = vm.ee
    b = []
    if ano >= 1983:
        b.append(ee.ImageCollection('NOAA/PERSIANN-CDR').filterDate(ini, fim).select('precipitation').sum()
                 .rename('persiann'))
    if ano >= 2000:
        horas = (d1 - d0).days * 24
        im = ee.ImageCollection('NASA/GPM_L3/IMERG_MONTHLY_V07').filterDate(ini, fim).select('precipitation')
        b.append(ee.Image(ee.Algorithms.If(im.size().gt(0), im.first().multiply(horas),
                                           ee.Image.constant(0).updateMask(ee.Image.constant(0)))).rename('imerg'))
    return ee.Image.cat(b) if b else None


def ref_mod16(vm, ini, fim):
    ee = vm.ee
    # MOD16A2GF (061, com falhas preenchidas, 2001-): a mesma do validar_solo_folha.py; o MOD16A2 061 só começa em 2021
    c = ee.ImageCollection('MODIS/061/MOD16A2GF').filterDate(ini, fim)
    vazio = ee.Image.constant([0, 0]).rename(['et_real', 'et_potencial']).updateMask(ee.Image.constant(0)).toFloat()
    cheio = ee.Image.cat([
        c.select('ET').map(lambda i: i.updateMask(i.lt(32700)).multiply(0.1)).sum().rename('et_real'),
        c.select('PET').map(lambda i: i.updateMask(i.lt(32700)).multiply(0.1)).sum().rename('et_potencial')]).toFloat()
    return ee.Image(ee.Algorithms.If(c.size().gt(0), cheio, vazio))


VARS_FONTE = {
    'era5': ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'vpd', 'rs', 'u2'],
    'gldas20': ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'vpd', 'rs', 'u2', 'et_potencial', 'et_real', 'transpiracao_mm',
                'tsolo_C', 'tfolha_C', 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3', 'runoff'],
    'mod16': ['et_real', 'et_potencial'],
}
VARS_FONTE['gldas21'] = VARS_FONTE['gldas20']


def rodar(fonte):
    vm = _ee()
    ee = vm.ee
    regs = vm.v.regioes(com_ufs=True)
    pasta = os.path.join(SAIDA, fonte)
    os.makedirs(pasta, exist_ok=True)
    a0, a1 = FONTES[fonte]
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)
    for ano in range(a0, a1 + 1):
        arq = os.path.join(pasta, f'{ano}.csv')
        if os.path.exists(arq):
            continue
        if time.time() > limite:
            print('Tempo desta vez acabou; a próxima retoma daqui.', flush=True)
            raise SystemExit(3)
        t0, linhas = time.time(), []
        for mes in range(1, 13):
            d0 = date(ano, mes, 1)
            d1 = (d0 + timedelta(days=32)).replace(day=1)
            ini, fim = d0.isoformat(), d1.isoformat()
            sab = sab_mes(vm, ini, fim)
            if fonte == 'chuva':
                ref = ref_chuva(vm, ano, ini, fim, d0, d1)
                if ref is None:
                    continue
                pares = [(n, 'pr_mm', n) for n in ref.bandNames().getInfo()]
            else:
                ref = (ref_era5(vm, ini, fim) if fonte == 'era5' else ref_mod16(vm, ini, fim) if fonte == 'mod16'
                       else ref_gldas(vm, ini, fim, 'NASA/GLDAS/V20/NOAH/G025/T3H' if fonte == 'gldas20'
                                      else 'NASA/GLDAS/V021/NOAH/G025/T3H'))
                pares = [(v, v, v) for v in VARS_FONTE[fonte]]
            img = ee.Image.cat([sab.select(s).rename(f's_{k}') for k, s, _ in pares] +
                               [ref.select(r).rename(f'r_{k}') for k, _, r in pares]).toFloat()
            bandas = img.bandNames().getInfo()
            for tentativa in range(4):
                try:
                    res = vm.reduzir(img, regs, bandas)
                    break
                except Exception as e:  # noqa: BLE001
                    print(f'   ⚠️ {fonte} {ano}-{mes:02d}: {str(e)[:150]}', flush=True)
                    time.sleep(20 * (tentativa + 1))
            else:
                raise RuntimeError(f'{fonte} {ano}-{mes:02d}: não deu depois de 4 tentativas')
            for reg, p in res.items():
                for k, s, _ in pares:
                    linhas.append({'regiao': reg, 'ano': ano, 'mes': mes, 'variavel': s,
                                   'fonte': k if fonte == 'chuva' else fonte,
                                   'sab': p.get(f's_{k}'), 'referencia': p.get(f'r_{k}')})
        if linhas:
            pd.DataFrame(linhas).to_csv(arq, index=False)
        print(f'   {fonte} {ano} pronto em {time.time() - t0:.0f} s', flush=True)
    resumo()


# ============================================================ resumo
HIST_VAR = {'pr_mm': ('pr_mm', 'terraclimate'), 'pr_chirps': ('pr_mm', 'chirps'), 'tmax_C': ('tmax_C', 'terraclimate'),
            'tmin_C': ('tmin_C', 'terraclimate'), 'vpd': ('vpd', 'terraclimate'), 'rs': ('rs', 'terraclimate'),
            'u2': ('u2', 'terraclimate'), 'et_potencial': ('et_potencial', 'terraclimate'),
            'et_real': ('et_real', 'terraclimate'), 'agua_solo': ('soil_moisture_0_100cm_m3_m3', 'terraclimate'),
            'escoamento': ('runoff', 'terraclimate')}


def carregar():
    partes = []
    for a in sorted(glob.glob(os.path.join(HIST, '*.csv'))):
        h = pd.read_csv(a)
        h['fonte'] = h.variavel.map(lambda v: HIST_VAR.get(v, (v, 'terraclimate'))[1])
        h['variavel'] = h.variavel.map(lambda v: HIST_VAR.get(v, (v, ''))[0])
        partes.append(h)
    for a in sorted(glob.glob(os.path.join(SAIDA, '*', '*.csv'))):
        partes.append(pd.read_csv(a))
    df = pd.concat(partes, ignore_index=True)
    df = df.dropna(subset=['sab', 'referencia'])
    for k in ('sab', 'referencia'):
        df[f'a_{k}'] = df[k] - df.groupby(['fonte', 'regiao', 'variavel', 'mes'])[k].transform('mean')
    return df


def resumo():
    df = carregar()
    if df.empty:
        return
    os.makedirs(SAIDA, exist_ok=True)
    flags, tabela = {}, []
    for (fonte, var, reg), g in df.groupby(['fonte', 'variavel', 'regiao']):
        linhas = decadas(g, var)
        dg = degraus(linhas, var)
        for x in linhas:
            if x:
                tabela.append({'fonte': fonte, 'variavel': var, 'regiao': reg, 'decada': f'{x[0][0]}-{x[0][1]}',
                               'vies': round(x[1], 3), 'r_anom': round(x[2], 3), 'degrau': dg.get(x[0], False)})
                if dg.get(x[0]):
                    flags.setdefault((var, reg, x[0]), []).append(fonte)
    tab = pd.DataFrame(tabela)
    tab.to_csv(os.path.join(SAIDA, 'TODAS_AS_COMPARACOES.csv'), index=False)
    L = ['# O banco contra várias referências (1961–2025)', '',
         'Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md`, emenda 1 (antes de rodar). Viés da década / correlação das '
         'anomalias mensais, por fonte. ⚠️ = degrau naquela fonte. **Confirmado** = degrau em ≥ 2 referências '
         'independentes (GLDAS-2.0 e 2.1 = uma; ERA5-Land não conta para as variáveis do modelo). Todas as comparações '
         '(também os 27 estados) em `TODAS_AS_COMPARACOES.csv`.', '',
         '## Fontes já comparadas', '', '| Fonte | Variáveis | Anos com dado |', '|---|---|---|']
    for f, g in df.groupby('fonte'):
        L.append(f"| {f} | {', '.join(sorted(NOME.get(v, v) for v in g.variavel.unique()))} | {g.ano.min()}–{g.ano.max()} |")
    L += ['', '## Degraus confirmados (≥ 2 referências independentes)', '',
          '| Variável | Região | Década | Fontes que marcam |', '|---|---|---|---|']
    conf = []
    for (var, reg, dec), fs in sorted(flags.items()):
        n, gr = conta_independente(fs, var)
        if n >= 2 and reg in REGIOES:
            conf.append((var, reg, dec))
            L.append(f'| {NOME.get(var, var)} | {reg} | {dec[0]}-{dec[1]} | {", ".join(gr)} |')
    if not conf:
        L.append('| — | — | — | nenhum até agora |')
    for var in [v for v in NOME if v in set(tab.variavel)]:
        L += ['', f'## {NOME[var]}', '', '| Década | Região | ' + ' | '.join(
            sorted(tab[tab.variavel == var].fonte.unique())) + ' |']
        fontes = sorted(tab[tab.variavel == var].fonte.unique())
        L.append('|---|---|' + '---|' * len(fontes))
        for a, z in DECADAS:
            for reg in REGIOES:
                cel = []
                for f in fontes:
                    x = tab[(tab.variavel == var) & (tab.regiao == reg) & (tab.fonte == f) & (tab.decada == f'{a}-{z}')]
                    cel.append('-' if x.empty else f"{'⚠️ ' if x.degrau.iloc[0] else ''}{x.vies.iloc[0]:+.1f} / {x.r_anom.iloc[0]:.2f}")
                if any(c != '-' for c in cel):
                    L.append(f'| {a}-{z} | {reg} | ' + ' | '.join(cel) + ' |')
    with open(os.path.join(SAIDA, 'RESULTADOS.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L[:40]))


if __name__ == '__main__':
    arg = (sys.argv[1:] or ['resumo'])[0]
    resumo() if arg == 'resumo' else rodar(arg)
