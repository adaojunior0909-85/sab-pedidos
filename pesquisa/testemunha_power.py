# Testemunha NASA POWER (família F4 do protocolo da auditoria profunda; a chuva conta como F1 – ver abaixo).
# Só leitura: API mensal regional oficial (https://power.larc.nasa.gov/docs/services/api/temporal/monthly/), blocos de
# 10° × 10°, 1981 até o ano anterior. Parâmetros (conferidos em 26/11/2026 contra a API diária num ponto):
#   PRECTOTCORR (mm/dia, média do mês → × dias do mês), T2M_MAX_AVG e T2M_MIN_AVG (média das máximas/mínimas diárias;
#   o T2M_MAX mensal é a máxima ABSOLUTA do mês e não serve), RH2M (%), WS2M (m/s), ALLSKY_SFC_SW_DWN (MJ/m²/dia; GEWEX
#   1984–2000, CERES 2001–), T2MDEW (°C, para a VPD = média de es(Tmax) e es(Tmin) − es(Tdew), a conta do ERA5 no
#   validar_multifonte.py). Sem ETo no POWER.
# Média regional igual à do SAB: o peso de cada célula do POWER (0,5° × 0,625°) é o número de pixels ENTREGUES do SAB
# (grade 0,1°) que caem nela e na região (Earth Engine, uma vez, só leitura). A média do SAB já está nos pares que subiram
# (historico/multifonte; idêntica entre as fontes, conferido em 26/11).
# Chuva: a página oficial diz só "observationally corrected" (Reichle et al. 2017), sem nomear a rede; pela regra do
# protocolo (seção 2), sem confirmação de rede distinta do GPCC ela entra na F1.
#     python pesquisa/testemunha_power.py          (retomável)
import glob
import json
import os
import sys
import time
import urllib.request
from calendar import monthrange

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
SAIDA = os.path.join(AQUI, 'resultados_power')
BRUTO = os.path.join(SAIDA, 'bruto_regional')      # médias regionais do POWER (o bruto por célula não sobe: é grande)
API = 'https://power.larc.nasa.gov/api/temporal/monthly/regional'
PARAM = ['PRECTOTCORR', 'T2M_MAX_AVG', 'T2M_MIN_AVG', 'RH2M', 'WS2M', 'ALLSKY_SFC_SW_DWN', 'T2MDEW']
LATS = [(-34, -24), (-24, -14), (-14, -4), (-4, 6)]
LONS = [(-74, -64), (-64, -54), (-54, -44), (-44, -34)]
ANO_FIM = int(os.environ.get('POWER_ANO_FIM') or 2025)


def idx(lat, lon):
    return int(np.floor((lat + 90 + 0.25) / 0.5)), int(np.floor((lon + 180 + 0.3125) / 0.625))


def pesos():
    arq = os.path.join(SAIDA, 'pesos_celulas.csv')
    if os.path.exists(arq):
        return pd.read_csv(arq)
    import validar_metodo_2026 as vm
    ee, v, sp = vm.ee, vm.v, vm.sp
    ll = ee.Image.pixelLonLat()
    i = ll.select('latitude').add(90.25).divide(0.5).floor()
    j = ll.select('longitude').add(180.3125).divide(0.625).floor()
    cel = i.multiply(1000).add(j).toInt().rename('cel').updateMask(v.ENTREGUE)
    linhas = []
    regs = v.regioes(com_ufs=True)
    for f in regs.getInfo()['features']:
        nome = f['properties']['regiao']
        geo = regs.filter(ee.Filter.eq('regiao', nome)).geometry()
        h = cel.reduceRegion(ee.Reducer.frequencyHistogram(), geo, crs=sp.CRS, crsTransform=sp.TRANSFORM,
                             maxPixels=1e10, tileScale=8).get('cel').getInfo() or {}
        for k, n in h.items():
            k = int(float(k))
            linhas.append({'regiao': nome, 'i': k // 1000, 'j': k % 1000, 'pixels': n})
        print(f'   pesos {nome}: {len(h)} células', flush=True)
    d = pd.DataFrame(linhas)
    os.makedirs(SAIDA, exist_ok=True)
    d.to_csv(arq, index=False)
    return d


def baixar(param, la, lo):
    url = (f'{API}?latitude-min={la[0]}&latitude-max={la[1]}&longitude-min={lo[0]}&longitude-max={lo[1]}'
           f'&parameters={param}&community=AG&start=1981&end={ANO_FIM}&format=JSON')
    for t in range(5):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            print(f'   ⚠️ {param} {la} {lo}: {str(e)[:120]}', flush=True)
            time.sleep(30 * (t + 1))
    raise RuntimeError(f'POWER {param} {la} {lo}: falhou 5 vezes')


def celulas(param):
    """{(i, j): {(ano, mes): valor}} de todo o Brasil para um parâmetro (os blocos se sobrepõem na borda: 1 por célula)."""
    out, versao = {}, None
    for la in LATS:
        for lo in LONS:
            js = baixar(param, la, lo)
            versao = js.get('header', {}).get('api', {}).get('version', versao)
            fill = js.get('header', {}).get('fill_value', -999.0)
            for f in js.get('features', []):
                lon, lat = f['geometry']['coordinates'][:2]
                serie = f['properties']['parameter'][param]
                out[idx(lat, lon)] = {(int(k[:4]), int(k[4:])): (np.nan if v == fill or v is None else float(v))
                                      for k, v in serie.items() if int(k[4:]) <= 12}
    return out, versao


def main():
    os.makedirs(BRUTO, exist_ok=True)
    w = pesos()
    versoes = {}
    for p in PARAM:
        arq = os.path.join(BRUTO, f'{p}.csv')
        if os.path.exists(arq):
            continue
        t0 = time.time()
        cel, versoes[p] = celulas(p)
        linhas = []
        for reg, g in w.groupby('regiao'):
            chaves = [(int(a), int(b)) for a, b in zip(g.i, g.j)]
            pw = g.pixels.to_numpy(float)
            faltam = sum(k not in cel for k in chaves)
            tempos = sorted({t for k in chaves if k in cel for t in cel[k]})
            for (ano, mes) in tempos:
                vals = np.array([cel.get(k, {}).get((ano, mes), np.nan) for k in chaves])
                ok = ~np.isnan(vals)
                if ok.sum() == 0 or pw[ok].sum() < 0.9 * pw.sum():     # menos de 90% do peso com dado: mês vazio
                    continue
                linhas.append({'regiao': reg, 'ano': ano, 'mes': mes, 'valor': float((vals[ok] * pw[ok]).sum() / pw[ok].sum()),
                               'celulas': int(ok.sum()), 'celulas_sem_dado_na_api': faltam})
        pd.DataFrame(linhas).to_csv(arq, index=False)
        print(f'   {p}: {len(linhas)} região-mês em {time.time() - t0:.0f} s (API {versoes[p]})', flush=True)
    with open(os.path.join(SAIDA, 'FONTE.md'), 'w', encoding='utf-8') as f:
        f.write('# NASA POWER: de onde vieram os números\n\n'
                f'- API mensal regional, {API}, comunidade AG, 1981–{ANO_FIM}; acesso em {time.strftime("%d/%m/%Y")}; '
                f'versões da API: {sorted(set(v for v in versoes.values() if v)) or "ver execuções anteriores"}.\n'
                '- Média regional ponderada pelo número de pixels entregues do SAB em cada célula (pesos_celulas.csv).\n'
                '- Mês com menos de 90% do peso com dado fica de fora.\n')
    parear()


def parear():
    """Escreve resultados_power/power/<ano>.csv no formato dos outros pares (regiao, ano, mes, variavel, fonte, sab,
    referencia), com a média do SAB tirada dos pares que já subiram."""
    sab = []
    for pasta in ('resultados_historico/anos', 'resultados_multifonte/*'):
        for x in glob.glob(os.path.join(AQUI, pasta, '*.csv')):
            sab.append(pd.read_csv(x, usecols=['regiao', 'ano', 'mes', 'variavel', 'sab']))
    sab = pd.concat(sab).dropna().drop_duplicates(['regiao', 'ano', 'mes', 'variavel'])
    b = {p: pd.read_csv(os.path.join(BRUTO, f'{p}.csv')).set_index(['regiao', 'ano', 'mes']).valor for p in PARAM}
    ref = pd.DataFrame(b)
    dias = np.array([monthrange(a, m)[1] for a, m in zip(ref.index.get_level_values(1), ref.index.get_level_values(2))])

    def es(t):
        return 0.6108 * np.exp(17.27 * t / (t + 237.3))
    r = pd.DataFrame({'pr_mm': ref.PRECTOTCORR * dias, 'tmax_C': ref.T2M_MAX_AVG, 'tmin_C': ref.T2M_MIN_AVG,
                      'RH': ref.RH2M, 'u2': ref.WS2M, 'rs': ref.ALLSKY_SFC_SW_DWN,
                      'vpd': ((es(ref.T2M_MAX_AVG) + es(ref.T2M_MIN_AVG)) / 2 - es(ref.T2MDEW)).clip(lower=0)})
    r = r.stack().rename('referencia').reset_index().rename(columns={'level_3': 'variavel'})
    p = r.merge(sab, on=['regiao', 'ano', 'mes', 'variavel'], how='inner')
    p['fonte'] = 'power'
    pasta = os.path.join(SAIDA, 'power')
    os.makedirs(pasta, exist_ok=True)
    for ano, g in p.groupby('ano'):
        g[['regiao', 'ano', 'mes', 'variavel', 'fonte', 'sab', 'referencia']].to_csv(os.path.join(pasta, f'{ano}.csv'), index=False)
    print(f'   pares: {len(p)} linhas, {p.ano.min()}–{p.ano.max()}', flush=True)


if __name__ == '__main__':
    parear() if (sys.argv[1:] or [''])[0] == 'parear' else main()
