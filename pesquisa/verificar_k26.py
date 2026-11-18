# Confere os achados da K26 (rodada 7, 1981-1990) no que o USUÁRIO recebe. Só LÊ o Earth Engine.
# A K26 leu o SAB_V1 bruto; o painel e os pedidos corrigem na leitura (escoamento e solo dos dias V1.0 com o fator do
# SMAP limitado a 5; pixels B com o núcleo do BR-DWGD; radiação dos C_interior limitada à de céu claro) e deixam a
# borda (C_borda, classe 4) fora das planilhas. Aqui, no dia 15 de cada mês de 1981-1990, as mesmas contagens da K26
# no banco BRUTO e no ENTREGUE (sab_pedido.colecao), separando os pixels entregues (classes A, B, C_interior) da
# borda. Saída: pesquisa/resultados_k26/verificacao_k26.csv e o resumo no log.
import csv
import os
import sys

import ee

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import sab_pedido as sp  # noqa: E402

SAIDA = os.path.join(AQUI, 'resultados_k26')
CONTAGENS = ('n', 'rsup_gt_pr', 'rsup_gt_pr_10', 'rsup_gt_pr_50', 'rsup_gt_200', 'rs_gt_rso', 'ce_zero_com_chuva5')


def bruto(img):
    return ee.Image(ee.Algorithms.If(img.bandNames().contains('precipitation_mm'),
                                     img.select(sp.BANDAS_ANTIGAS, sp.BANDAS_SAB), img.select(sp.BANDAS_SAB)))


def contar(img, classe, geom, rotulo):
    data = img.date()
    rso = sp._radiacao_ceu_claro(data)
    pr, rsup, rs = img.select('pr_mm'), img.select('runoff_sup_mm'), img.select('rs')
    ok = pr.mask().And(rsup.mask())
    ce = pr.subtract(rsup).max(0)
    um = {
        'n': ok,
        'rsup_gt_pr': ok.And(rsup.gt(pr)),
        'rsup_gt_pr_10': ok.And(rsup.gt(pr.add(10))),
        'rsup_gt_pr_50': ok.And(rsup.gt(pr.add(50))),
        'rsup_gt_200': ok.And(rsup.gt(200)),
        'rs_gt_rso': rs.mask().And(rs.gt(rso)),
        'ce_zero_com_chuva5': ok.And(pr.gte(5)).And(ce.eq(0))}
    for b in sp.BANDAS_SAB:
        um[f'cob_{b}'] = img.select(b).mask().gt(0)
    pilha = ee.Image.cat([ee.Image(v).unmask(0).rename(k) for k, v in um.items()])
    out = {}
    for grupo, m in (('entregue', classe.gte(1).And(classe.lte(3))), ('borda', classe.eq(4))):
        r = pilha.updateMask(m).reduceRegion(reducer=ee.Reducer.sum(), geometry=geom, crs=sp.CRS,
                                             crsTransform=sp.TRANSFORM, maxPixels=1e10, tileScale=4)
        out[grupo] = r
    return ee.Feature(None, {'data': data.format('YYYY-MM-dd'), 'leitura': rotulo,
                             'entregue': out['entregue'], 'borda': out['borda']})


def main():
    ee.Initialize(project=sp.PROJETO)
    os.makedirs(SAIDA, exist_ok=True)
    geom = ee.Geometry.Rectangle([-74.0, -34.0, -34.0, 5.5], None, False)
    classe = ee.Image(sp.MASCARA).select('classe').unmask(0, False)
    linhas = []
    for ano in range(1981, 1991):
        dias = [f'{ano}-{m:02d}-15' for m in range(1, 13)]
        col_b = ee.ImageCollection(sp.SAB).filter(ee.Filter.inList('system:index', [sp_id(d) for d in dias]))
        col_e = sp.colecao(geom, f'{ano}-01-01', f'{ano + 1}-01-01').filter(
            ee.Filter.inList('system:index', [sp_id(d) for d in dias]))
        fc = ee.FeatureCollection(col_b.map(lambda i: contar(bruto(i), classe, geom, 'bruto'))).merge(
            ee.FeatureCollection(col_e.map(lambda i: contar(i, classe, geom, 'entregue'))))
        info = fc.getInfo()['features']
        for f in info:
            p = f['properties']
            for grupo in ('entregue', 'borda'):
                linhas.append({'data': p['data'], 'leitura': p['leitura'], 'pixels': grupo,
                               **{k: int(round(v or 0)) for k, v in p[grupo].items()}})
        print(f'   {ano}: {len(info)} dia-leituras')
    cols = ['data', 'leitura', 'pixels'] + list(CONTAGENS) + [f'cob_{b}' for b in sp.BANDAS_SAB]
    with open(os.path.join(SAIDA, 'verificacao_k26.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(sorted(linhas, key=lambda x: (x['data'], x['leitura'], x['pixels'])))
    # resumo
    print('\nRESUMO (soma dos 120 dias; % sobre os pixels com chuva e escoamento):')
    for leitura in ('bruto', 'entregue'):
        for grupo in ('entregue', 'borda'):
            sel = [l for l in linhas if l['leitura'] == leitura and l['pixels'] == grupo]
            n = sum(l['n'] for l in sel) or 1
            txt = ' | '.join(f"{k} {sum(l[k] for l in sel):,} ({100 * sum(l[k] for l in sel) / n:.3f}%)"
                             for k in CONTAGENS[1:])
            print(f'  leitura {leitura:<8} pixels {grupo:<8} n {n:,} | {txt}')
        sel = [l for l in linhas if l['leitura'] == leitura and l['pixels'] == 'entregue']
        cob = {b: sum(l[f'cob_{b}'] for l in sel) for b in sp.BANDAS_SAB}
        mx = max(cob.values())
        print(f'  leitura {leitura:<8} cobertura nos pixels entregues (pixels a menos que a banda mais completa, '
              f'soma dos 120 dias): ' + ', '.join(f'{b} {mx - c:,}' for b, c in cob.items() if mx - c))


def sp_id(d):
    return 'SAB_' + d.replace('-', '_')


if __name__ == '__main__':
    main()
