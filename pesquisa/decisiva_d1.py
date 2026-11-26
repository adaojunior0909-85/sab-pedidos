# Análise decisiva, D1 (pesquisa/PROTOCOLO_ANALISE_DECISIVA.md): pluviômetros ESTÁVEIS da ANA (2010–2024) como verdade de
# chão. Só leitura (serviço público da ANA; Earth Engine). Etapas (retomável; TEMPO_MAX_MIN):
#   1. inventário: HidroInventario (tipo 2), candidatos com início ≤ 2009 e sem fim antes de 2025, só no Brasil;
#   2. séries: HidroSerieHistorica 2010–2024, total mensal (consistido > bruto); estável = ≥ 11 meses em cada ano e
#      nenhum total anual (dos meses com dado) fora de [0,3; 3] × a mediana do posto em 2010–2019; até 150 por estado;
#   3. Earth Engine: total mensal no pixel do posto para BR-DWGD bruto, CHIRPS, ERA5-Land, IMERG, PERSIANN, TerraClimate;
#   4. análise: q_X = X ÷ posto nos mesmos meses do ano; salto = média 2020–24 ÷ média 2010–19 − 1; S_X = mediana dos
#      postos (região e Brasil), IC 95% por reamostragem dos postos; regra do protocolo. Teste sintético antes; conta em
#      dobro; sensibilidade relatada.
#     python pesquisa/decisiva_d1.py              (tudo)
#     python pesquisa/decisiva_d1.py analise      (só a etapa 4)
import glob
import os
import re
import sys
import time
import urllib.request

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
SAIDA = os.path.join(AQUI, 'resultados_decisiva')
D1 = os.path.join(SAIDA, 'd1')
API = 'https://telemetriaws1.ana.gov.br/ServiceANA.asmx'
ANOS = list(range(2010, 2025))
MAX_UF = 150
REGIAO_UF = {
    'ACRE': 'Norte', 'AMAPÁ': 'Norte', 'AMAZONAS': 'Norte', 'PARÁ': 'Norte', 'RONDÔNIA': 'Norte', 'RORAIMA': 'Norte',
    'TOCANTINS': 'Norte', 'ALAGOAS': 'Nordeste', 'BAHIA': 'Nordeste', 'CEARÁ': 'Nordeste', 'MARANHÃO': 'Nordeste',
    'PARAÍBA': 'Nordeste', 'PERNAMBUCO': 'Nordeste', 'PIAUÍ': 'Nordeste', 'RIO GRANDE DO NORTE': 'Nordeste',
    'SERGIPE': 'Nordeste', 'DISTRITO FEDERAL': 'Centro-Oeste', 'GOIÁS': 'Centro-Oeste', 'MATO GROSSO': 'Centro-Oeste',
    'MATO GROSSO DO SUL': 'Centro-Oeste', 'ESPÍRITO SANTO': 'Sudeste', 'MINAS GERAIS': 'Sudeste',
    'RIO DE JANEIRO': 'Sudeste', 'SÃO PAULO': 'Sudeste', 'PARANÁ': 'Sul', 'RIO GRANDE DO SUL': 'Sul',
    'SANTA CATARINA': 'Sul'}
FONTES = ['br', 'chirps', 'era5', 'imerg', 'persiann', 'terraclimate']
FAMILIA = {'chirps': 'F3', 'era5': 'F5', 'imerg': 'F1', 'persiann': 'F1', 'terraclimate': 'F2'}


def baixar(url, tent=5):
    for t in range(tent):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return r.read().decode('utf-8', errors='replace')
        except Exception as e:  # noqa: BLE001
            print(f'   ⚠️ ANA: {str(e)[:100]}', flush=True)
            time.sleep(10 * (t + 1))
    raise RuntimeError(f'ANA falhou: {url[:120]}')


def campo(x, k):
    m = re.search(rf'<{k}>([^<]*)</{k}>', x)
    return m.group(1) if m else ''


def inventario():
    arq = os.path.join(D1, 'candidatos.csv')
    if os.path.exists(arq):
        return pd.read_csv(arq)
    s = baixar(f'{API}/HidroInventario?codEstDE=&codEstATE=&tpEst=2&nmEst=&nmRio=&codSubBacia=&codBacia=&nmMunicipio='
               '&nmEstado=&sgResp=&sgOper=&telemetrica=')
    linhas = []
    for x in re.findall(r'<Table[^>]*>(.*?)</Table>', s, re.S):
        uf = campo(x, 'nmEstado')
        ini, fim = campo(x, 'PeriodoPluviometroInicio')[:4], campo(x, 'PeriodoPluviometroFim')[:4]
        if uf not in REGIAO_UF or not ini or ini > '2009' or (fim and fim < '2025'):
            continue
        linhas.append({'codigo': int(campo(x, 'Codigo')), 'nome': campo(x, 'Nome'), 'uf': uf, 'regiao': REGIAO_UF[uf],
                       'lat': float(campo(x, 'Latitude')), 'lon': float(campo(x, 'Longitude')),
                       'operadora': campo(x, 'OperadoraSigla'), 'inicio': ini, 'fim': fim})
    d = pd.DataFrame(linhas).drop_duplicates('codigo').sort_values(['uf', 'codigo'])
    os.makedirs(D1, exist_ok=True)
    d.to_csv(arq, index=False)
    print(f'   inventário: {len(d)} candidatos', flush=True)
    return d


def serie(cod):
    s = baixar(f'{API}/HidroSerieHistorica?codEstacao={cod}&dataInicio=01/01/2010&dataFim=31/12/2024&tipoDados=2'
               '&nivelConsistencia=')
    m = {}
    for x in re.findall(r'<SerieHistorica[^>]*>(.*?)</SerieHistorica>', s, re.S):
        data, nivel, tot = campo(x, 'DataHora')[:7], campo(x, 'NivelConsistencia'), campo(x, 'Total')
        if not data or tot == '':
            continue
        a, mm = int(data[:4]), int(data[5:7])
        nivel = int(nivel or 1)
        if (a, mm) not in m or nivel > m[(a, mm)][0]:
            m[(a, mm)] = (nivel, float(tot))
    return pd.DataFrame([{'codigo': cod, 'ano': a, 'mes': mm, 'nivel': n, 'chuva': v} for (a, mm), (n, v) in m.items()])


def estavel(s):
    if s.empty:
        return False
    c = s.groupby('ano').mes.nunique().reindex(ANOS, fill_value=0)
    if (c < 11).any():
        return False
    tot = s.groupby('ano').chuva.sum()
    med = tot.loc[2010:2019].median()
    return bool(med > 0 and tot.between(0.3 * med, 3 * med).all())


def series(cand, limite):
    os.makedirs(os.path.join(D1, 'series'), exist_ok=True)
    feito = os.path.join(D1, 'consultados.csv')
    cons = pd.read_csv(feito) if os.path.exists(feito) else pd.DataFrame(columns=['codigo', 'estavel'])
    ja = set(cons.codigo)
    novos = []
    for uf, g in cand.groupby('uf'):
        n_ok = int(cons[cons.codigo.isin(g.codigo)].estavel.sum()) if len(cons) else 0
        for cod in g.codigo:
            if n_ok >= MAX_UF:
                break
            if cod in ja:
                continue
            if time.time() > limite:
                pd.concat([cons, pd.DataFrame(novos)]).to_csv(feito, index=False)
                raise SystemExit(3)
            s = serie(cod)
            ok = estavel(s)
            if ok:
                s.to_csv(os.path.join(D1, 'series', f'{cod}.csv'), index=False)
                n_ok += 1
            novos.append({'codigo': cod, 'estavel': ok})
        print(f'   {uf}: {n_ok} estáveis', flush=True)
        pd.concat([cons, pd.DataFrame(novos)]).to_csv(feito, index=False)
    return pd.concat([cons, pd.DataFrame(novos)])


def amostrar(limite):
    """Total mensal de cada base no pixel de cada posto estável (Earth Engine, só leitura)."""
    import validar_metodo_2026 as vm
    ee = vm.ee
    cand = pd.read_csv(os.path.join(D1, 'candidatos.csv')).set_index('codigo')
    cods = sorted(int(os.path.basename(x)[:-4]) for x in glob.glob(os.path.join(D1, 'series', '*.csv')))
    pts = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([cand.loc[c, 'lon'], cand.loc[c, 'lat']]), {'codigo': c})
                                for c in cods])
    os.makedirs(os.path.join(D1, 'grade'), exist_ok=True)
    br_col = ee.ImageCollection('projects/ee-alexandrexavier/assets/BR-DWGD')
    for ano in ANOS:
        arq = os.path.join(D1, 'grade', f'{ano}.csv')
        if os.path.exists(arq):
            continue
        if time.time() > limite:
            raise SystemExit(3)
        bandas = []
        for m in range(1, 13):
            ini = ee.Date.fromYMD(ano, m, 1)
            fim = ini.advance(1, 'month')
            horas = ee.Number(fim.difference(ini, 'hour'))
            br = br_col.filterDate(ini, fim).map(
                lambda i: i.select('pr').updateMask(i.select('pr').gt(-32768)).multiply(0.00686666).add(225.0).max(0))
            im = ee.ImageCollection('NASA/GPM_L3/IMERG_MONTHLY_V07').filterDate(ini, fim).select('precipitation')
            vazio = ee.Image.constant(0).updateMask(ee.Image.constant(0)).toFloat()
            bandas += [
                br.sum().rename(f'br_{m}'),
                ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD').filterDate(ini, fim).select('precipitation').sum()
                .rename(f'chirps_{m}'),
                ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY_AGGR').filterDate(ini, fim).first()
                .select('total_precipitation_sum').multiply(1000).rename(f'era5_{m}'),
                ee.Image(ee.Algorithms.If(im.size().gt(0), im.first().multiply(horas), vazio)).rename(f'imerg_{m}'),
                ee.ImageCollection('NOAA/PERSIANN-CDR').filterDate(ini, fim).select('precipitation').sum()
                .rename(f'persiann_{m}'),
                ee.ImageCollection('IDAHO_EPSCOR/TERRACLIMATE').filterDate(ini, fim).first().select('pr')
                .rename(f'terraclimate_{m}')]
        img = ee.Image.cat(bandas).toFloat()
        linhas = []
        for k in range(0, len(cods), 500):
            sub = ee.FeatureCollection(pts.toList(500, k))
            for t in range(4):
                try:
                    # cada base no próprio pixel: amostra com escala fina (o valor é o do pixel que contém o ponto)
                    r = img.reduceRegions(collection=sub, reducer=ee.Reducer.first(), scale=1000, tileScale=4).getInfo()
                    break
                except Exception as e:  # noqa: BLE001
                    print(f'   ⚠️ grade {ano}: {str(e)[:120]}', flush=True)
                    time.sleep(20 * (t + 1))
            else:
                raise RuntimeError(f'grade {ano}: 4 tentativas')
            for f in r['features']:
                p = f['properties']
                for m in range(1, 13):
                    linhas.append({'codigo': p['codigo'], 'ano': ano, 'mes': m,
                                   **{x: p.get(f'{x}_{m}') for x in FONTES}})
        pd.DataFrame(linhas).to_csv(arq, index=False)
        print(f'   grade {ano}: {len(cods)} postos', flush=True)


# ------------------------------------------------------------------ análise (etapa 4)
def saltos(pares, base=(2010, 2019), depois=(2020, 2024)):
    """Salto de cada posto e base: média de q_X em 2020–24 ÷ média em 2010–19 − 1 (q_X = X ÷ posto no ano, nos meses
    em que o posto tem dado)."""
    p = pares.dropna(subset=['chuva'])
    an = p.groupby(['codigo', 'ano'])[['chuva'] + FONTES].sum(min_count=1).reset_index()
    out = []
    for x in FONTES:
        a = an.dropna(subset=[x])
        a = a[a.chuva > 0]
        q = (a[x] / a.chuva).groupby([a.codigo, a.ano]).first().unstack()
        s = q.loc[:, depois[0]:depois[1]].mean(axis=1) / q.loc[:, base[0]:base[1]].mean(axis=1) - 1
        out.append(s.rename(x))
    return pd.concat(out, axis=1) * 100


def saltos_numpy(pares):
    """A mesma conta escrita de novo (conta em dobro)."""
    res = {}
    for x in FONTES:
        d = {}
        for r in pares[['codigo', 'ano', 'chuva', x]].itertuples(index=False):
            if r.chuva != r.chuva or r[3] != r[3]:
                continue
            k = (r.codigo, r.ano)
            g, v = d.get(k, (0.0, 0.0))
            d[k] = (g + r.chuva, v + r[3])
        por = {}
        for (c, a), (g, v) in d.items():
            if g > 0:
                por.setdefault(c, {})[a] = v / g
        for c, qs in por.items():
            b = [qs[a] for a in range(2010, 2020) if a in qs]
            dp = [qs[a] for a in range(2020, 2025) if a in qs]
            if b and dp:
                res[(c, x)] = 100 * (np.mean(dp) / np.mean(b) - 1)
    return res


def regra(S, ic):
    """S, ic: {fonte: valor}, {fonte: (lo, hi)} de uma região. Saída: DADOS, CLIMA ou inconclusivo."""
    fam = {}
    for x, f in FAMILIA.items():
        if x in S and pd.notna(S[x]):
            fam.setdefault(f, []).append(x)
    def famval(f):
        xs = fam[f]
        return np.median([S[x] for x in xs]), (min(ic[x][0] for x in xs), max(ic[x][1] for x in xs))
    fv = {f: famval(f) for f in fam}
    br, (blo, bhi) = S['br'], ic['br']
    perto = sum(abs(v) <= 3 for v, _ in fv.values())
    abaixo = sum(v <= -4 and hi < 0 for v, (lo, hi) in fv.values())
    if br >= 4 and blo > 0 and perto >= 2:
        return 'DADOS (a grade erra)'
    if abs(br) <= 3 and abaixo >= 2:
        return 'CLIMA (as referências erram)'
    return 'inconclusivo'


def bootstrap(v, n=2000, seed=0):
    v = np.asarray(v.dropna())
    if len(v) < 5:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    meds = np.median(rng.choice(v, (n, len(v)), replace=True), axis=1)
    return (float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5)))


def avaliar(sal, cand):
    sal = sal.join(cand.set_index('codigo')[['regiao']], how='left')
    linhas = []
    for reg in ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil']:
        g = sal if reg == 'Brasil' else sal[sal.regiao == reg]
        S = {x: float(g[x].median()) for x in FONTES if g[x].notna().sum() >= 5}
        ic = {x: bootstrap(g[x]) for x in S}
        n = int(g.br.notna().sum())
        dec = regra(S, ic) if n >= 30 and 'br' in S else 'inconclusivo (< 30 postos)'
        linhas.append({'regiao': reg, 'postos': n, **{f'S_{x}': S.get(x) for x in FONTES},
                       **{f'IC_{x}': ic.get(x) for x in FONTES}, 'decisao': dec})
    return pd.DataFrame(linhas)


def sintetico(pares, cand):
    """Postos inventados sobre as bases reais: (1) posto = TerraClimate × ruído (sem salto real) e BR = posto × 1,10
    desde 2020 → tem de sair DADOS; (2) posto com +10% real desde 2020, as referências sem salto, BR = posto → CLIMA."""
    rng = np.random.default_rng(3)
    res = {}
    for caso in ('dados', 'clima'):
        p = pares.copy()
        base = p.terraclimate * (1 + rng.normal(0, 0.05, len(p)))
        degrau = np.where(p.ano >= 2020, 1.10, 1.0)
        if caso == 'dados':
            p['chuva'] = base
            for x in ('chirps', 'era5', 'imerg', 'persiann'):
                p[x] = base * (1 + rng.normal(0, 0.05, len(p)))
            p['terraclimate'] = base * (1 + rng.normal(0, 0.05, len(p)))
            p['br'] = base * degrau
        else:
            p['chuva'] = base * degrau
            for x in ('chirps', 'era5', 'imerg', 'persiann', 'terraclimate'):
                p[x] = base * (1 + rng.normal(0, 0.05, len(p)))
            p['br'] = p.chuva
        res[caso] = avaliar(saltos(p), cand).set_index('regiao').loc['Brasil', 'decisao']
    ok = res['dados'].startswith('DADOS') and res['clima'].startswith('CLIMA')
    return ok, res


def analise():
    cand = pd.read_csv(os.path.join(D1, 'candidatos.csv'))
    se = pd.concat(pd.read_csv(x) for x in glob.glob(os.path.join(D1, 'series', '*.csv')))
    gr = pd.concat(pd.read_csv(x) for x in sorted(glob.glob(os.path.join(D1, 'grade', '*.csv'))))
    pares = se.merge(gr, on=['codigo', 'ano', 'mes'], how='inner')
    ok, res = sintetico(pares, cand)
    L = ['# D1. Pluviômetros estáveis da ANA (2010–2024) como verdade de chão', '',
         'Protocolo `pesquisa/PROTOCOLO_ANALISE_DECISIVA.md`. Salto = (base ÷ posto) em 2020–24 contra 2010–19, nos mesmos '
         'meses; S = mediana dos postos (IC 95% por reamostragem). **DADOS** = S_BR ≥ +4% (IC > 0) e ≥ 2 famílias com '
         '|S| ≤ 3%; **CLIMA** = |S_BR| ≤ 3% e ≥ 2 famílias com S ≤ −4% (IC < 0).', '',
         f'Teste sintético (antes dos dados reais): grade com salto inventado → {res["dados"]}; chuva real inventada → '
         f'{res["clima"]}. **{"PASSOU" if ok else "FALHOU: resultados reais não olhados"}**', '']
    if not ok:
        open(os.path.join(SAIDA, 'RESULTADOS_D1.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        raise SystemExit('sintético falhou')
    sal = saltos(pares)
    nump = saltos_numpy(pares)
    dif = max(abs(sal.loc[c, x] - v) for (c, x), v in nump.items() if c in sal.index and pd.notna(sal.loc[c, x]))
    L.append(f'Conta em dobro: {len(nump)} saltos posto × base refeitos por outra implementação; maior diferença {dif:.1e}. '
             f'**{"OK" if dif < 1e-6 else "DIFERENÇA"}**')
    L.append('')
    t = avaliar(sal, cand)
    sal.join(cand.set_index('codigo')[['uf', 'regiao', 'lat', 'lon', 'operadora']]).to_csv(os.path.join(SAIDA, 'D1_saltos_postos.csv'))
    t.to_csv(os.path.join(SAIDA, 'D1_decisao.csv'), index=False)
    L += ['## Resultado', '', '| Região | Postos | BR-DWGD | CHIRPS (F3) | ERA5-Land (F5) | IMERG (F1) | PERSIANN (F1) | '
          'TerraClimate (F2) | Decisão |', '|---|---|---|---|---|---|---|---|---|']
    for r in t.itertuples():
        def c(x):
            v, i = getattr(r, f'S_{x}'), getattr(r, f'IC_{x}')
            return '-' if v is None or pd.isna(v) else f'{v:+.1f}% [{i[0]:+.1f}; {i[1]:+.1f}]'
        L.append(f'| {r.regiao} | {r.postos} | ' + ' | '.join(c(x) for x in FONTES) + f' | **{r.decisao}** |')
    L += ['', '## Sensibilidade (relatada)', '']
    for nome, kw in [('base 2015–2019', {'base': (2015, 2019)})]:
        tt = avaliar(saltos(pares, **kw), cand)
        L.append(f'- {nome}: ' + '; '.join(f'{r.regiao} {r.decisao} (BR {r.S_br:+.1f}%)' for r in tt.itertuples()))
    cons = pares.groupby('codigo').nivel.min() >= 2
    tt = avaliar(saltos(pares[pares.codigo.isin(cons[cons].index)]), cand)
    L.append('- só postos com todos os meses consistidos: ' + '; '.join(f'{r.regiao} {r.decisao} ({r.postos} postos)'
                                                                    for r in tt.itertuples()))
    with open(os.path.join(SAIDA, 'RESULTADOS_D1.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


def main():
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)
    cand = inventario()
    series(cand, limite)
    amostrar(limite)
    analise()


if __name__ == '__main__':
    analise() if (sys.argv[1:] or [''])[0] == 'analise' else main()
