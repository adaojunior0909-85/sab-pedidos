# Teste 2 do escoamento (pesquisa/ESCOAMENTO.md): coeficiente do ERA5 aplicado à chuva observada. Só LÊ o Earth Engine.
# Dia 15 de cada mês de 1981-1990 e 2001-2010, pixels entregues (A, B, C_interior), na leitura dos pedidos.
# Saída: pesquisa/resultados_k26/teste_escoamento2.csv e o resumo com a regra de aceite no log.
import csv
import os
import sys
import time
from datetime import date, timedelta

import ee

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import sab_pedido as sp  # noqa: E402

SAIDA = os.path.join(AQUI, 'resultados_k26')
ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
METRICAS = ('soma_rsup', 'gt_pr', 'gt_pr_10', 'ce0_chuva5')


def com_retentativa(func, tentativas=5):
    for i in range(tentativas):
        try:
            return func()
        except Exception as e:  # noqa: BLE001
            if i == tentativas - 1:
                raise
            print(f'   ⚠️ {str(e)[:120]} | nova tentativa em {15 * (i + 1)} s')
            time.sleep(15 * (i + 1))


def contar(d, classe, geom):
    ini, fim = str(d - timedelta(days=2)), str(d + timedelta(days=3))
    sab = sp.colecao(geom, ini, fim)
    era = ee.ImageCollection(ERA5).filterDate(ini, fim)
    img = ee.Image(sab.filter(ee.Filter.eq('system:index', 'SAB_' + str(d).replace('-', '_'))).first())
    pr, r = img.select('pr_mm'), img.select('runoff_sup_mm')
    soma_r = sab.select('runoff_sup_mm').sum()
    soma_tp = era.select('total_precipitation_sum').sum().multiply(1000)
    k = soma_r.divide(soma_tp.max(0.1)).min(1).max(0)
    novo = k.multiply(pr)
    ok = pr.mask().And(r.mask()).And(soma_r.mask()).And(soma_tp.mask()).And(classe.gte(1)).And(classe.lte(3))
    bandas = [ok.rename('n'), pr.rename('soma_pr'), soma_tp.divide(5).rename('soma_tp_era5_dia')]
    for v, rs in (('atual', r), ('corrigido', novo)):
        ce = pr.subtract(rs).max(0)
        bandas += [rs.rename(f'{v}__soma_rsup'), rs.gt(pr).rename(f'{v}__gt_pr'),
                   rs.gt(pr.add(10)).rename(f'{v}__gt_pr_10'), pr.gte(5).And(ce.eq(0)).rename(f'{v}__ce0_chuva5')]
    pilha = ee.Image.cat([b.unmask(0).toFloat() for b in bandas]).updateMask(ok)
    return pilha.reduceRegion(reducer=ee.Reducer.sum(), geometry=geom, crs=sp.CRS, crsTransform=sp.TRANSFORM,
                              maxPixels=1e10, tileScale=4)


def main():
    ee.Initialize(project=sp.PROJETO)
    os.makedirs(SAIDA, exist_ok=True)
    geom = ee.Geometry.Rectangle([-74.0, -34.0, -34.0, 5.5], None, False)
    classe = ee.Image(sp.MASCARA).select('classe').unmask(0, False)
    dias = [date(a, m, 15) for dec in (1981, 2001) for a in range(dec, dec + 10) for m in range(1, 13)]
    linhas = []
    for d in dias:
        r = com_retentativa(lambda: contar(d, classe, geom).getInfo())
        linhas.append({'data': str(d), **{k: round(v or 0, 2) for k, v in r.items()}})
        if d.month == 12:
            print(f'   {d.year} pronto')
    cols = ['data', 'n', 'soma_pr', 'soma_tp_era5_dia'] + [f'{v}__{m}' for v in ('atual', 'corrigido') for m in METRICAS]
    with open(os.path.join(SAIDA, 'teste_escoamento2.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(linhas)
    aprovado = True
    for rotulo, a0 in (('1981-1990', '1981'), ('2001-2010', '2001')):
        sel = [l for l in linhas if l['data'][:4] >= a0 and l['data'][:4] < str(int(a0) + 10)]
        n = sum(l['n'] for l in sel)
        t = {v: {m: sum(l[f'{v}__{m}'] for l in sel) for m in METRICAS} for v in ('atual', 'corrigido')}
        print(f'\n{rotulo}: {len(sel)} dias, {n:,.0f} pixel-dias; chuva observada {sum(l["soma_pr"] for l in sel):,.0f} '
              f'| chuva ERA5 {sum(l["soma_tp_era5_dia"] for l in sel):,.0f}')
        for v in ('atual', 'corrigido'):
            x = t[v]
            print(f"  {v:<10} escoamento total {x['soma_rsup']:,.0f} | > chuva {100 * x['gt_pr'] / n:.3f}% | "
                  f"> chuva+10 {100 * x['gt_pr_10'] / n:.3f}% | chuva efetiva 0 com chuva >= 5 mm {100 * x['ce0_chuva5'] / n:.3f}%")
        a, c = t['atual'], t['corrigido']
        c1 = c['ce0_chuva5'] <= 0.5 * a['ce0_chuva5']
        c2 = c['gt_pr_10'] <= 0.1 * a['gt_pr_10']
        tot = c['soma_rsup'] / a['soma_rsup'] - 1
        meses = {}
        for l in sel:
            m = l['data'][5:7]
            meses.setdefault(m, [0, 0])
            meses[m][0] += l['atual__soma_rsup']
            meses[m][1] += l['corrigido__soma_rsup']
        var_mes = {m: v[1] / v[0] - 1 for m, v in meses.items() if v[0] > 0}
        c3 = abs(tot) <= 0.20 and all(abs(x) <= 0.30 for x in var_mes.values())
        aprovado = aprovado and c1 and c2 and c3
        print(f"  REGRA: chuva efetiva zerada cai >= 50%: {'SIM' if c1 else 'NÃO'} ({100 * (c['ce0_chuva5'] / a['ce0_chuva5'] - 1):+.0f}%)"
              f" | > chuva+10 cai >= 90%: {'SIM' if c2 else 'NÃO'} ({100 * (c['gt_pr_10'] / a['gt_pr_10'] - 1):+.0f}%)"
              f" | total ±20% e meses ±30%: {'SIM' if c3 else 'NÃO'} (total {100 * tot:+.1f}%; meses "
              + ', '.join(f'{m} {100 * x:+.0f}%' for m, x in sorted(var_mes.items())) + ')')
    print(f"\nCORREÇÃO {'RECOMENDADA (decisão do dono do projeto para aplicar)' if aprovado else 'NÃO RECOMENDADA'}")


if __name__ == '__main__':
    main()
