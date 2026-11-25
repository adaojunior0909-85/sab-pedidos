# Prepara os dados do CAMELS-BR para a comparação do escoamento (protocolo: ../PROTOCOLO_ESCOAMENTO_CAMELS.md).
# Entrada: a pasta com os zips 01 (atributos), 03 (vazão em mm) e 14 (contornos) do CAMELS-BR v1.1 já extraídos
# (https://zenodo.org/records/3964745, CC-BY-4.0). Saída em pesquisa/dados/camels/:
#   bacias.geojson      os contornos das bacias selecionadas, simplificados (tolerância 0,01°, 1/10 do pixel do SAB), com id, região e área
#   vazao_mensal.csv.gz a vazão observada mensal (mm/mês) de 1981 a 2018, só nos meses com >= 25 dias observados
#   bacias.csv          os atributos usados na seleção
#     python pesquisa/escoamento/preparar_camels.py /caminho/da/pasta/extraida
import glob
import json
import os
import sys

import pandas as pd
import shapefile
from shapely.geometry import mapping, shape

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, '..', 'dados', 'camels')
AREA_MIN, AREA_MAX, REGULACAO_MAX, USO_MAX = 500, 50000, 10, 10
MIN_DIAS_MES = 25
TOLERANCIA = 0.01


def main(pasta):
    os.makedirs(SAIDA, exist_ok=True)
    a = os.path.join(pasta, '01_CAMELS_BR_attributes')
    rd = lambda f: pd.read_csv(os.path.join(a, f), sep=r'\s+', dtype={'gauge_id': str})  # noqa: E731
    d = rd('camels_br_human_intervention.txt').merge(rd('camels_br_location.txt'), on='gauge_id')
    sel = d[d.area_gsim.between(AREA_MIN, AREA_MAX) & (d.regulation_degree < REGULACAO_MAX)
            & (d.consumptive_use_perc < USO_MAX)].copy()
    sel[['gauge_id', 'gauge_name', 'gauge_region', 'gauge_lat', 'gauge_lon', 'area_gsim', 'regulation_degree',
         'consumptive_use_perc']].to_csv(os.path.join(SAIDA, 'bacias.csv'), index=False)
    ids = set(sel.gauge_id)
    regiao = dict(zip(sel.gauge_id, sel.gauge_region))
    area = dict(zip(sel.gauge_id, sel.area_gsim))
    r = shapefile.Reader(os.path.join(pasta, '14_CAMELS_BR_catchment_boundaries', 'camels_br_catchments.shp'))
    feats = []
    for s in r.iterShapeRecords():
        gid = str(int(s.record['gauge_id']))
        if gid not in ids:
            continue
        g = shape(s.shape.__geo_interface__).buffer(0).simplify(TOLERANCIA, preserve_topology=True)
        feats.append({'type': 'Feature', 'geometry': mapping(g),
                      'properties': {'id': gid, 'regiao': regiao[gid], 'area_km2': area[gid]}})
    with open(os.path.join(SAIDA, 'bacias.geojson'), 'w') as f:
        json.dump({'type': 'FeatureCollection', 'features': feats}, f, separators=(',', ':'))
    linhas = []
    for arq in glob.glob(os.path.join(pasta, '03_CAMELS_BR_streamflow_mm_selected_catchments', '*_streamflow_mm.txt')):
        gid = os.path.basename(arq).split('_')[0]
        if gid not in ids:
            continue
        q = pd.read_csv(arq, sep=r'\s+')
        q = q[q.year.between(1981, 2018)]
        g = q.groupby(['year', 'month'])['streamflow_mm'].agg(['sum', 'count']).reset_index()
        g = g[g['count'] >= MIN_DIAS_MES]
        dias = pd.to_datetime(dict(year=g.year, month=g.month, day=1)).dt.days_in_month
        g['q_obs_mm'] = (g['sum'] / g['count'] * dias).round(3)       # média dos dias observados x dias do mês
        g.insert(0, 'id', gid)
        linhas.append(g[['id', 'year', 'month', 'q_obs_mm', 'count']].rename(columns={'year': 'ano', 'month': 'mes',
                                                                                     'count': 'dias_obs'}))
    v = pd.concat(linhas)
    v.to_csv(os.path.join(SAIDA, 'vazao_mensal.csv.gz'), index=False)
    print(f'{len(sel)} bacias selecionadas; {len(feats)} contornos; {v.id.nunique()} com vazão; {len(v)} bacia-meses')


if __name__ == '__main__':
    main(sys.argv[1])
