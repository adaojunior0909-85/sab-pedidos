# Testa a hipótese das janelas (pesquisa/ESCOAMENTO.md) no que os pedidos entregam. Só LÊ o Earth Engine.
# Dia 15 de cada mês de 1981-1990 (dias definitivos, como a K26) e de jan-out/2026 (provisórios, só o 'atual').
# Saída: pesquisa/resultados_k26/teste_escoamento.csv e o resumo com a regra de aceite no log.
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
VARIANTES = ('atual', 'alinhado', 'alinhado_teto')
METRICAS = ('soma_rsup', 'gt_pr', 'gt_pr_10', 'gt_200', 'ce0_chuva5')


def com_retentativa(func, tentativas=5):
    for i in range(tentativas):
        try:
            return func()
        except Exception as e:  # noqa: BLE001
            if i == tentativas - 1:
                raise
            print(f'   ⚠️ {str(e)[:120]} | nova tentativa em {15 * (i + 1)} s')
            time.sleep(15 * (i + 1))


def contar(img_ant, img, classe, geom):
    pr = img.select('pr_mm')
    r0, r1 = img_ant.select('runoff_sup_mm'), img.select('runoff_sup_mm')
    al = r0.add(r1).multiply(0.5)
    var = {'atual': r1, 'alinhado': al, 'alinhado_teto': al.min(pr)}
    ok = pr.mask().And(r1.mask()).And(r0.mask()).And(classe.gte(1)).And(classe.lte(3))
    bandas = [ok.rename('n'), pr.rename('soma_pr')]
    for v, rs in var.items():
        ce = pr.subtract(rs).max(0)
        bandas += [rs.rename(f'{v}__soma_rsup'), rs.gt(pr).rename(f'{v}__gt_pr'),
                   rs.gt(pr.add(10)).rename(f'{v}__gt_pr_10'), rs.gt(200).rename(f'{v}__gt_200'),
                   pr.gte(5).And(ce.eq(0)).rename(f'{v}__ce0_chuva5')]
    pilha = ee.Image.cat([b.unmask(0).toFloat() for b in bandas]).updateMask(ok)
    return pilha.reduceRegion(reducer=ee.Reducer.sum(), geometry=geom, crs=sp.CRS, crsTransform=sp.TRANSFORM,
                              maxPixels=1e10, tileScale=4)


def main():
    ee.Initialize(project=sp.PROJETO)
    os.makedirs(SAIDA, exist_ok=True)
    geom = ee.Geometry.Rectangle([-74.0, -34.0, -34.0, 5.5], None, False)
    classe = ee.Image(sp.MASCARA).select('classe').unmask(0, False)
    dias = [date(a, m, 15) for a in range(1981, 1991) for m in range(1, 13)] + [date(2026, m, 15) for m in range(1, 11)]
    linhas = []
    for d in dias:
        col = sp.colecao(geom, str(d - timedelta(days=1)), str(d + timedelta(days=1))).toList(2)
        r = com_retentativa(lambda: contar(ee.Image(col.get(0)), ee.Image(col.get(1)), classe, geom).getInfo())
        linhas.append({'data': str(d), **{k: round(v or 0, 2) for k, v in r.items()}})
        if d.month == 12 or d.year == 2026 and d.month == 10:
            print(f'   {d.year} pronto')
    cols = ['data', 'n', 'soma_pr'] + [f'{v}__{m}' for v in VARIANTES for m in METRICAS]
    with open(os.path.join(SAIDA, 'teste_escoamento.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(linhas)
    for rotulo, sel in (('DEFINITIVOS 1981-1990', [l for l in linhas if l['data'] < '2026']),
                        ('PROVISÓRIOS 2026 (mesma janela; só o atual vale)', [l for l in linhas if l['data'] >= '2026'])):
        n = sum(l['n'] for l in sel)
        print(f'\n{rotulo}: {len(sel)} dias, {n:,.0f} pixel-dias')
        tot = {v: {m: sum(l[f'{v}__{m}'] for l in sel) for m in METRICAS} for v in VARIANTES}
        for v in VARIANTES:
            t = tot[v]
            print(f"  {v:<14} escoamento total {t['soma_rsup']:,.0f} | > chuva {100 * t['gt_pr'] / n:.3f}% | "
                  f"> chuva+10 {100 * t['gt_pr_10'] / n:.3f}% | > 200 mm {100 * t['gt_200'] / n:.4f}% | "
                  f"chuva efetiva 0 com chuva >= 5 mm {100 * t['ce0_chuva5'] / n:.3f}%")
        if rotulo.startswith('DEF'):
            a, al, tt = tot['atual'], tot['alinhado'], tot['alinhado_teto']
            c1 = al['ce0_chuva5'] <= 0.5 * a['ce0_chuva5']
            c2 = al['gt_pr_10'] <= 0.5 * a['gt_pr_10']
            c3 = abs(al['soma_rsup'] / a['soma_rsup'] - 1) < 0.02
            c4 = (al['soma_rsup'] - tt['soma_rsup']) / al['soma_rsup'] < 0.02
            print(f"\n  REGRA: chuva efetiva zerada cai >= 50%: {'SIM' if c1 else 'NÃO'} "
                  f"({100 * (al['ce0_chuva5'] / a['ce0_chuva5'] - 1):+.0f}%) | > chuva+10 cai >= 50%: {'SIM' if c2 else 'NÃO'} "
                  f"({100 * (al['gt_pr_10'] / a['gt_pr_10'] - 1):+.0f}%) | soma do escoamento muda < 2%: {'SIM' if c3 else 'NÃO'} "
                  f"({100 * (al['soma_rsup'] / a['soma_rsup'] - 1):+.2f}%)")
            print(f"  ALINHAMENTO {'ADOTADO' if c1 and c2 and c3 else 'NÃO ADOTADO'}; teto tira "
                  f"{100 * (al['soma_rsup'] - tt['soma_rsup']) / al['soma_rsup']:.2f}% da soma -> teto "
                  f"{'ADOTADO junto' if c1 and c2 and c3 and c4 else 'não adotado'}")


if __name__ == '__main__':
    main()
