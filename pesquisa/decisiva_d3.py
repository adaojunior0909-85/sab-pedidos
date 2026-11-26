# Análise decisiva, D3 (pesquisa/PROTOCOLO_ANALISE_DECISIVA.md): a rede do BR-DWGD. Só leitura.
# 1. Baixa da pasta pública do autor (Google Drive) o Controls_pr_Tmax_Tmin_NetCDF_Files.zip (v_3.2.4, 2,1 GB) e extrai
#    só o controle da chuva de 2001–2025 (número de pluviômetros usados e distância ao mais próximo, por pixel e dia).
# 2. Por célula de 1°: média do número de pluviômetros e da distância em 2015–2019 e em 2020–2024; rede ESTÁVEL = as duas
#    variam menos de 10%; o resto = rede MUDADA (células sem pixel com dado ficam fora).
# 3. Earth Engine: total anual da chuva do BR-DWGD bruto, do CHIRPS e do ERA5-Land em cada grupo (pixels entregues);
#    salto = (BR ÷ referência) em 2020–2024 contra 2010–2019.
# Regra: a causa é a rede se o salto nas células estáveis < metade do das mudadas e a diferença > 4 p.p.
#     python pesquisa/decisiva_d3.py
import glob
import os
import sys
import time
import zipfile

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
SAIDA = os.path.join(AQUI, 'resultados_decisiva')
TMP = os.environ.get('RUNNER_TEMP') or '/tmp'
ZIP_ID = '1xbBl-6E78OyIOvxZPzy3IR316wULhVt6'     # Controls_pr_Tmax_Tmin_NetCDF_Files.zip (pasta pública do autor)


def celulas():
    arq = os.path.join(SAIDA, 'D3_celulas.csv')
    if os.path.exists(arq):
        return pd.read_csv(arq)
    import gdown
    import xarray as xr
    z = os.path.join(TMP, 'controles.zip')
    if not os.path.exists(z):
        gdown.download(id=ZIP_ID, output=z, quiet=False)
    with zipfile.ZipFile(z) as f:
        nomes = f.namelist()
        print('   no zip:', nomes, flush=True)
        alvo = [n for n in nomes if 'pr' in os.path.basename(n).lower() and 'control' in n.lower() and '2001' in n]
        if not alvo:
            raise RuntimeError(f'controle da chuva 2001–2025 não encontrado no zip: {nomes}')
        f.extract(alvo[0], TMP)
    nc = os.path.join(TMP, alvo[0])
    ds = xr.open_dataset(nc, chunks={'time': 365})
    print('   variáveis:', {k: (v.dims, dict(v.attrs)) for k, v in ds.data_vars.items()}, flush=True)
    vs = list(ds.data_vars)
    dist = [v for v in vs if 'dist' in v.lower()]
    cont = [v for v in vs if v not in dist]
    if not dist or not cont:
        raise RuntimeError(f'não achei número e distância entre {vs}')
    tdim = [d for d in ds[dist[0]].dims if 'time' in d.lower()][0]
    lat = [d for d in ds[dist[0]].dims if 'lat' in d.lower()][0]
    lon = [d for d in ds[dist[0]].dims if 'lon' in d.lower()][0]
    out = {}
    for nome, v in (('n', cont[0]), ('dist', dist[0])):
        for per, (a, b) in (('antes', ('2015-01-01', '2019-12-31')), ('depois', ('2020-01-01', '2024-12-31'))):
            m = ds[v].sel({tdim: slice(a, b)}).mean(tdim).compute()
            m = m.assign_coords({lat: np.floor(m[lat]), lon: np.floor(m[lon])})
            out[f'{nome}_{per}'] = m.to_dataframe(name='v').groupby([lat, lon]).v.mean()
    d = pd.DataFrame(out).reset_index()
    d.columns = ['lat', 'lon'] + list(out)
    d = d.dropna()
    dn = (d.n_depois / d.n_antes - 1).abs()
    dd = (d.dist_depois / d.dist_antes - 1).abs()
    d['grupo'] = np.where((dn < 0.10) & (dd < 0.10), 'estavel', 'mudada')
    os.makedirs(SAIDA, exist_ok=True)
    d.to_csv(arq, index=False)
    print(f'   células: {d.grupo.value_counts().to_dict()}', flush=True)
    return d


def chuva_grupos(cel):
    arq = os.path.join(SAIDA, 'D3_chuva_grupos.csv')
    if os.path.exists(arq):
        return pd.read_csv(arq)
    import validar_metodo_2026 as vm
    ee, v, sp = vm.ee, vm.v, vm.sp
    feats = []
    for g, s in cel.groupby('grupo'):
        geo = ee.Geometry.MultiPolygon([[[[lo, la], [lo + 1, la], [lo + 1, la + 1], [lo, la + 1], [lo, la]]]
                                        for la, lo in zip(s.lat, s.lon)], None, False)
        feats.append(ee.Feature(geo, {'grupo': g}))
    fc = ee.FeatureCollection(feats)
    br_col = ee.ImageCollection('projects/ee-alexandrexavier/assets/BR-DWGD')
    linhas = []
    for ano in range(2010, 2025):
        ini, fim = f'{ano}-01-01', f'{ano + 1}-01-01'
        img = ee.Image.cat([
            br_col.filterDate(ini, fim).map(lambda i: i.select('pr').updateMask(i.select('pr').gt(-32768))
                                            .multiply(0.00686666).add(225.0).max(0)).sum().rename('br'),
            ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD').filterDate(ini, fim).select('precipitation').sum().rename('chirps'),
            ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY_AGGR').filterDate(ini, fim).select('total_precipitation_sum')
            .sum().multiply(1000).rename('era5')]).toFloat().updateMask(v.ENTREGUE)
        for t in range(4):
            try:
                r = img.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), crs=sp.CRS, crsTransform=sp.TRANSFORM,
                                      tileScale=8).getInfo()
                break
            except Exception as e:  # noqa: BLE001
                print(f'   ⚠️ {ano}: {str(e)[:120]}', flush=True)
                time.sleep(20 * (t + 1))
        else:
            raise RuntimeError(f'{ano}: 4 tentativas')
        for f in r['features']:
            p = f['properties']
            linhas.append({'ano': ano, 'grupo': p['grupo'], 'br': p.get('br'), 'chirps': p.get('chirps'),
                           'era5': p.get('era5')})
        print(f'   chuva {ano} pronta', flush=True)
    d = pd.DataFrame(linhas)
    d.to_csv(arq, index=False)
    return d


def main():
    cel = celulas()
    ch = chuva_grupos(cel)
    L = ['# D3. A rede do BR-DWGD: células de 1° com rede estável × rede mudada', '',
         'Protocolo `pesquisa/PROTOCOLO_ANALISE_DECISIVA.md`. Controle da chuva da v_3.2.4 (pasta pública do autor). '
         'Estável = número médio de pluviômetros e distância média ao mais próximo variando < 10% entre 2015–19 e 2020–24. '
         'Salto = (BR-DWGD ÷ referência) em 2020–24 contra 2010–19. Regra: causa = rede se salto(estável) < ½ salto(mudada) '
         'e a diferença > 4 p.p.', '',
         f'Células: {cel.grupo.value_counts().to_dict()}. Mediana da variação do número de pluviômetros nas mudadas: '
         f'{100 * (cel[cel.grupo == "mudada"].n_depois / cel[cel.grupo == "mudada"].n_antes - 1).median():+.1f}%.', '',
         '| Grupo | Salto × CHIRPS | Salto × ERA5-Land |', '|---|---|---|']
    s = {}
    for g, x in ch.groupby('grupo'):
        x = x.set_index('ano')
        for r in ('chirps', 'era5'):
            q = x.br / x[r]
            s[(g, r)] = 100 * (q.loc[2020:2024].mean() / q.loc[2010:2019].mean() - 1)
        L.append(f'| {g} | {s[(g, "chirps")]:+.1f}% | {s[(g, "era5")]:+.1f}% |')
    vere = []
    for r in ('chirps', 'era5'):
        e, m = s.get(('estavel', r)), s.get(('mudada', r))
        if e is None or m is None:
            vere.append(f'{r}: sem os dois grupos')
            continue
        rede = e < 0.5 * m and (m - e) > 4
        vere.append(f'{r}: {"a causa é a rede" if rede else "a rede não explica"} ({e:+.1f}% × {m:+.1f}%)')
    L += ['', '**Veredito:** ' + '; '.join(vere), '']
    with open(os.path.join(SAIDA, 'RESULTADOS_D3.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
