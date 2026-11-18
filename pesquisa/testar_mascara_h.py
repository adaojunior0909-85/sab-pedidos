# Item H da K26: a falta de pixels nas bandas do ERA5-Land nos pixels ENTREGUES é valor ausente ou máscara
# fracionária (pixel de costa com máscara entre 0 e 1, que tem valor mas pesa menos na soma)? Só LÊ o Earth Engine.
# Dia 15 de jan, abr, jul e out de 1985, leitura dos pedidos, pixels A, B e C_interior.
import os
import sys

import ee

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import sab_pedido as sp  # noqa: E402

BANDAS = ('pr_mm', 'tmax_C', 'et_real', 'tsolo_C', 'runoff_sup_mm', 'soil_moisture_0_5cm_m3_m3')


def main():
    ee.Initialize(project=sp.PROJETO)
    geom = ee.Geometry.Rectangle([-74.0, -34.0, -34.0, 5.5], None, False)
    classe = ee.Image(sp.MASCARA).select('classe').unmask(0, False)
    ent = classe.gte(1).And(classe.lte(3))
    print(f"{'dia':<11} {'banda':<28} {'K26 (máscara fracionária)':>26} {'tem valor (binário)':>20} {'pixels com 0<máscara<1':>24}")
    for d in ('1985-01-15', '1985-04-15', '1985-07-15', '1985-10-15'):
        img = ee.Image(sp.colecao(geom, d, str(ee.Date(d).advance(1, 'day').format('YYYY-MM-dd').getInfo()))
                       .first())
        bs = []
        for b in BANDAS:
            m = img.select(b).mask()
            bs += [ee.Image.constant(1).updateMask(m).unmask(0).rename(f'{b}__k26'),
                   m.gt(0).rename(f'{b}__bin'), m.gt(0).And(m.lt(1)).rename(f'{b}__frac')]
        r = ee.Image.cat(bs).updateMask(ent).reduceRegion(reducer=ee.Reducer.sum(), geometry=geom, crs=sp.CRS,
                                                          crsTransform=sp.TRANSFORM, maxPixels=1e10,
                                                          tileScale=4).getInfo()
        for b in BANDAS:
            print(f"{d:<11} {b:<28} {r[b + '__k26']:>26,.1f} {r[b + '__bin']:>20,.0f} {r[b + '__frac']:>24,.0f}")


if __name__ == '__main__':
    main()
