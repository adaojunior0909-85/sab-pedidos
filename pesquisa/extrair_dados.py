# PESQUISA: previsão estendida (além dos 16 dias do GFS) de chuva e temperatura. FASE 1: extração dos dados.
# Só LÊ o Earth Engine (getInfo); não exporta nada, não grava nenhum asset. Roda no GitHub Actions
# (workflow pesquisa_extrair.yml) e grava os CSV em pesquisa/dados/, que o próprio workflow sobe para a branch.
# Pode ser interrompido e rodado de novo: os anos já extraídos são pulados.
#
# O QUE EXTRAI
#   1. pontos.csv: pixels de 0,1° da classe A (BR-DWGD) numa malha de 1° no Brasil, numa malha de 0,25° no Paraná
#      e o pixel de Cascavel-PR, com a UF (GAUL 2015).
#   2. brdwgd/AAAA.csv.gz: por ponto e QUINZENA (dias 1-15 e 16-fim de cada mês) do BR-DWGD, decodificado como no
#      motor: chuva total (mm), média da Tmax e da Tmin (°C) e nº de dias válidos.
#   3. sst_mensal.csv: médias mensais da temperatura da superfície do mar (OISST v2.1), ponderadas pela área, em
#      caixas que influenciam o clima do Brasil: Niño 3.4, Niño 1+2, faixa tropical 20S-20N (para o Niño 3.4
#      relativo, como o RONI), Atlântico Norte tropical (TNA), Atlântico Sul tropical (TSA), Atlântico Sudoeste
#      (ATSW, frente ao Sul/Sudeste) e os dois polos do Dipolo do Índico (IOD).
#   4. roni_cpc.csv: a série oficial do RONI (asset RONI_CPC_v6), para conferência.
import csv
import gzip
import os
import sys
import time
from datetime import date

import ee

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import sab_pedido as sp  # noqa: E402

DADOS = os.path.join(AQUI, 'dados')
BRDWGD = sp.BRDWGD
ANO_INI_BR = 1981            # 1981 só como histórico das anomalias recentes (persistência) das previsões de 1982
ANO_INI_SST = 1982           # primeiro ano completo do OISST v2.1
LOTE_PONTOS = 250
CAIXAS = {                   # [oeste, sul, leste, norte]
    'nino34': [-170, -5, -120, 5], 'nino12': [-90, -10, -80, 0], 'tropical': [-180, -20, 180, 20],
    'tna': [-57.5, 5.5, -15, 23.5], 'tsa': [-30, -20, 10, 0], 'atsw': [-60, -40, -30, -20],
    'iod_w': [50, -10, 70, 10], 'iod_e': [90, -10, 110, 0]}


def com_retentativa(func, *a, tentativas=4):
    for i in range(tentativas):
        try:
            return func(*a)
        except Exception as e:  # noqa: BLE001
            if i == tentativas - 1:
                raise
            print(f'   ⚠️ {str(e)[:150]} | nova tentativa em {20 * (i + 1)} s')
            time.sleep(20 * (i + 1))


def quinzenas(ano):
    for q in range(24):
        m = q // 2 + 1
        d0 = date(ano, m, 1 if q % 2 == 0 else 16)
        d1 = date(ano, m, 16) if q % 2 == 0 else (date(ano + 1, 1, 1) if m == 12 else date(ano, m + 1, 1))
        yield q, d0, d1


# ---------------------------------------------------------------------------------------------------------- pontos
def pontos():
    caminho = os.path.join(DADOS, 'pontos.csv')
    if os.path.exists(caminho):
        with open(caminho, encoding='utf-8') as f:
            return list(csv.DictReader(f))
    cand = {}

    def add(lat, lon, grupo):
        la, lo = sp.centro_do_pixel(lat, lon)
        chave = (round(la, 5), round(lo, 5))
        cand.setdefault(chave, set()).add(grupo)
    for i in range(39):
        for j in range(40):
            add(4.5 - i, -73.5 + j, 'BR_1grau')
    for i in range(18):
        for j in range(27):
            add(-22.5 - 0.25 * i, -54.6 + 0.25 * j, 'PR_025grau')
    add(-25.34953, -53.45031, 'Cascavel')
    feats = [ee.Feature(ee.Geometry.Point([lo, la]), {'k': k, 'lat': la, 'lon': lo, 'grupo': '+'.join(sorted(g))})
             for k, ((la, lo), g) in enumerate(sorted(cand.items()))]
    fc = ee.FeatureCollection(feats)
    classe = ee.Image(sp.MASCARA).select('classe').unmask(0, False)
    fc = classe.reduceRegions(collection=fc, reducer=ee.Reducer.first().setOutputs(['classe']),
                              crs=sp.CRS, crsTransform=sp.TRANSFORM)
    fc = fc.filter(ee.Filter.eq('classe', 1))
    ufs = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
    fc = ee.Join.saveFirst(matchKey='uf', outer=True).apply(fc, ufs, ee.Filter.intersects(leftField='.geo', rightField='.geo'))
    fc = ee.FeatureCollection(fc).map(lambda f: ee.Feature(None, {
        'k': f.get('k'), 'lat': f.get('lat'), 'lon': f.get('lon'), 'grupo': f.get('grupo'),
        'uf': ee.Algorithms.If(f.get('uf'), ee.Feature(f.get('uf')).get('ADM1_NAME'), '')}))
    info = com_retentativa(lambda: fc.getInfo()['features'])
    linhas = []
    for f in sorted(info, key=lambda x: x['properties']['k']):
        p = f['properties']
        grupo = p['grupo']
        if 'PR_025grau' in grupo and p['uf'] != 'Parana':      # malha fina só dentro do Paraná
            grupo = '+'.join(g for g in grupo.split('+') if g != 'PR_025grau')
            if not grupo:
                continue
        linhas.append({'id': f'P{len(linhas) + 1:04d}', 'lat': f"{p['lat']:.5f}", 'lon': f"{p['lon']:.5f}",
                       'uf': p['uf'], 'grupo': grupo})
    with open(caminho, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'lat', 'lon', 'uf', 'grupo'])
        w.writeheader()
        w.writerows(linhas)
    print(f'📍 {len(linhas)} pontos da classe A ({sum("Parana" == l["uf"] for l in linhas)} no Paraná).')
    return linhas


# --------------------------------------------------------------------------------------------------------- BR-DWGD
def decodificar(img):
    ok = img.select('pr').gt(-32768)
    return ee.Image.cat([
        img.select('pr').multiply(0.00686666).add(225.0).max(0).rename('pr'),
        img.select('Tmax').multiply(0.00106815).add(15.0).rename('tx'),
        img.select('Tmin').multiply(0.00106815).add(15.0).rename('tn')]).updateMask(ok).toFloat()


def brdwgd(lista):
    pasta = os.path.join(DADOS, 'brdwgd')
    os.makedirs(pasta, exist_ok=True)
    col = ee.ImageCollection(BRDWGD)
    ultimo = date.fromisoformat(com_retentativa(
        lambda: ee.Date(col.aggregate_max('system:time_start')).format('YYYY-MM-dd').getInfo()))
    print(f'🗓️ BR-DWGD até {ultimo}.')
    fcs = [ee.FeatureCollection([ee.Feature(ee.Geometry.Point([float(p['lon']), float(p['lat'])]), {'id': p['id']})
                                 for p in lista[i:i + LOTE_PONTOS]]) for i in range(0, len(lista), LOTE_PONTOS)]
    for ano in range(ANO_INI_BR, ultimo.year + 1):
        arq = os.path.join(pasta, f'{ano}.csv.gz')
        if os.path.exists(arq):
            continue
        t0 = time.time()
        bandas, nomes = [], []
        for q, d0, d1 in quinzenas(ano):
            if d0 > ultimo:
                break
            c = col.filterDate(str(d0), str(d1)).map(decodificar)
            vazio = ee.Image.constant(0).toFloat().updateMask(0)

            def ou_vazio(red, c=c, vazio=vazio):   # quinzena sem nenhuma imagem: banda mascarada, não erro
                return ee.Image(ee.Algorithms.If(c.size().gt(0), red, vazio))
            bandas += [ou_vazio(c.select('pr').sum()), ou_vazio(c.select('tx').mean()),
                       ou_vazio(c.select('tn').mean()), ou_vazio(c.select('pr').count().toFloat())]
            nomes += [f'pr_{q:02d}', f'tx_{q:02d}', f'tn_{q:02d}', f'n_{q:02d}']
        img = ee.Image.cat(bandas).rename(nomes)
        linhas = []
        for fc in fcs:
            r = com_retentativa(lambda: img.reduceRegions(collection=fc, reducer=ee.Reducer.first(),
                                                           crs=sp.CRS, crsTransform=sp.TRANSFORM).getInfo())
            for f in r['features']:
                p = f['properties']
                linha = {'id': p['id'], 'ano': ano}
                for n in nomes:
                    v = p.get(n)
                    linha[n] = '' if v is None else (str(int(v)) if n.startswith('n_') else f'{v:.2f}')
                linhas.append(linha)
        with gzip.open(arq + '.tmp', 'wt', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=['id', 'ano'] + nomes)
            w.writeheader()
            w.writerows(sorted(linhas, key=lambda x: x['id']))
        os.replace(arq + '.tmp', arq)
        print(f'   BR-DWGD {ano}: {len(linhas)} pontos x {len(nomes) // 4} quinzenas em {time.time() - t0:.0f} s')


# ----------------------------------------------------------------------------------------------------------- OISST
def sst():
    arq = os.path.join(DADOS, 'sst_mensal.csv')
    feitos = {}
    if os.path.exists(arq):
        with open(arq, encoding='utf-8') as f:
            for l in csv.DictReader(f):
                feitos[(int(l['ano']), int(l['mes']))] = l
    col = ee.ImageCollection('NOAA/CDR/OISST/V2_1').select('sst')
    proj = col.first().projection()
    area = ee.Image.pixelArea()
    caixas = ee.FeatureCollection([ee.Feature(ee.Geometry.Rectangle(r, None, False), {'caixa': k})
                                   for k, r in CAIXAS.items()])
    hoje = date.today()
    for ano in range(ANO_INI_SST, hoje.year + 1):
        meses = [m for m in range(1, 13) if date(ano, m, 1) < date(hoje.year, hoje.month, 1)]
        meses = [m for m in meses if (ano, m) not in feitos or int(feitos[(ano, m)]['n_dias']) < 28]
        if not meses:
            continue
        bandas, nomes, contagens = [], [], {}
        for m in meses:
            d0 = date(ano, m, 1)
            d1 = date(ano + 1, 1, 1) if m == 12 else date(ano, m + 1, 1)
            cm = ee.ImageCollection(col.filterDate(str(d0), str(d1)).distinct('system:time_start'))
            media = cm.mean().multiply(0.01)
            bandas += [media.multiply(area).rename(f's{m:02d}'), media.mask().multiply(area).rename(f'a{m:02d}')]
            nomes += [f's{m:02d}', f'a{m:02d}']
            contagens[f'n{m:02d}'] = cm.size()
        img = ee.Image.cat(bandas)
        r = com_retentativa(lambda: ee.Dictionary({
            'cx': img.reduceRegions(collection=caixas, reducer=ee.Reducer.sum(), crs=proj, tileScale=4)
                     .toList(20).map(lambda f: ee.Feature(f).toDictionary()),
            'n': ee.Dictionary(contagens)}).getInfo())
        for m in meses:
            l = {'ano': ano, 'mes': m, 'n_dias': r['n'][f'n{m:02d}']}
            for c in r['cx']:
                s, a = c.get(f's{m:02d}'), c.get(f'a{m:02d}')
                l[c['caixa']] = f'{s / a:.4f}' if s is not None and a else ''
            feitos[(ano, m)] = l
        print(f'   OISST {ano}: {len(meses)} mes(es)')
    with open(arq, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['ano', 'mes', 'n_dias'] + list(CAIXAS))
        w.writeheader()
        w.writerows(feitos[k] for k in sorted(feitos))


def roni_cpc():
    info = com_retentativa(lambda: ee.FeatureCollection(sp.RONI_ASSET).toList(5000)
                           .map(lambda f: ee.Feature(f).toDictionary()).getInfo())
    with open(os.path.join(DADOS, 'roni_cpc.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ano', 'mes', 'RONI', 'Trimestre'])
        for x in sorted(info, key=lambda x: (int(x['ano']), int(x['mes']))):
            w.writerow([int(x['ano']), int(x['mes']), x['RONI'], x.get('Trimestre', '')])


if __name__ == '__main__':
    os.makedirs(DADOS, exist_ok=True)
    ee.Initialize(project=sp.PROJETO)
    t = time.time()
    roni_cpc()
    print('✅ RONI do CPC')
    sst()
    print('✅ OISST mensal')
    brdwgd(pontos())
    print(f'✅ Extração terminada em {(time.time() - t) / 60:.0f} min.')
