# Verificação COM Earth Engine da regra 2026.11.22 (radiação abaixo de 3% de Ra sai vazia). Só lê (getInfo).
# Rodar: no GitHub Actions (workflow "Verificar radiacao impossivel") ou no Colab, na pasta do repositório:
#     python testes/verificar_rs_impossivel_ee.py
#
# Compara a leitura NOVA (sab_pedido.colecao) com a ANTIGA (a mesma, sem vazio_rs_impossivel):
#   1. num pixel B do litoral do RS (Lagoa Mirim), em 10/03/2026 (Rs gravado = 0 pela K26): a antiga entrega Rs 0, a
#      nova deixa vazio, e as outras 15 bandas ficam iguais; em 01/03/2026 (fora da janela) as duas são iguais;
#   2. no Brasil inteiro, em dias com e sem o problema: os pixels que mudam são EXATAMENTE os que tinham Rs < 3% de Ra
#      na leitura antiga, nenhum Rs abaixo do limite sobra na nova, e nenhuma outra banda muda em pixel nenhum.
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import ee  # noqa: E402
import sab_pedido as sp  # noqa: E402

ee.Initialize(project=sp.PROJETO)
NOVA = sp.vazio_rs_impossivel
BANDAS = list(sp.BANDAS_SAB)
OUTRAS = [b for b in BANDAS if b != 'rs']
BRASIL = ee.Geometry.Rectangle([-74.0, -34.0, -34.0, 5.5], None, False)
falhas = 0


def confere(cond, msg):
    global falhas
    print(('  ok   ' if cond else '  FALHA ') + msg, flush=True)
    falhas += 0 if cond else 1


def leitura(geom, dia, nova):
    """A imagem do dia como o pedido por e-mail entrega, com a regra nova ou sem ela."""
    sp.vazio_rs_impossivel = NOVA if nova else (lambda img: img)
    try:
        fim = str(ee.Date(dia).advance(1, 'day').format('YYYY-MM-dd').getInfo())
        col = sp.colecao(geom, dia, fim)
        return ee.Image(col.first()).select(BANDAS + ['amplitude_diaria', 'deficit_diario', 'chuva_efetiva'])
    finally:
        sp.vazio_rs_impossivel = NOVA


print('1) Pixel B do litoral do RS (Lagoa Mirim)')
lat, lon = sp.centro_do_pixel(-32.65, -52.85)
pt = ee.Geometry.Point([lon, lat])
for dia, rs_zero in (('2026-03-10', True), ('2026-03-01', False)):
    v = {}
    for nome, nova in (('antiga', False), ('nova', True)):
        v[nome] = leitura(pt, dia, nova).reduceRegion(ee.Reducer.first(), pt, crs=sp.CRS,
                                                      crsTransform=sp.TRANSFORM).getInfo()
    ra = sp._radiacao_topo(ee.Date(dia)).reduceRegion(ee.Reducer.first(), pt, crs=sp.CRS,
                                                       crsTransform=sp.TRANSFORM).getInfo()['ra']
    a, n = v['antiga'].get('rs'), v['nova'].get('rs')
    print(f'   {dia} ({lat:.5f}, {lon:.5f}): Rs antiga {a} | nova {n} | Ra {ra:.2f} | ETo {v["nova"].get("et_potencial")}')
    if rs_zero:
        confere(a is not None and a < 0.03 * ra and n is None, f'{dia}: Rs {a} (abaixo de 3% de Ra) agora sai vazio')
    else:
        confere(a is not None and a >= 0.03 * ra and n == a, f'{dia}: Rs normal ({a}) continua igual')
    outras = [b for b in v['antiga'] if b != 'rs' and v['antiga'][b] != v['nova'].get(b)]
    confere(not outras, f'{dia}: as outras bandas ficam iguais ({len(v["antiga"]) - 1} conferidas)')

print('\n2) Brasil inteiro: só os pixels com Rs < 3% de Ra mudam, e só na radiação')
for dia in ('2026-03-10', '2026-10-01', '2026-11-16', '2025-06-15', '1965-01-15'):
    velha, nova = leitura(BRASIL, dia, False), leitura(BRASIL, dia, True)
    ra = sp._radiacao_topo(ee.Date(dia))
    rs_v, rs_n = velha.select('rs'), nova.select('rs')
    abaixo = rs_v.lt(ra.multiply(0.03)).And(rs_v.mask().gt(0))
    sumiu = rs_v.mask().gt(0).And(rs_n.mask().eq(0))
    mudou_rs = rs_n.mask().gt(0).And(rs_n.neq(rs_v))
    outras_dif = ee.Image.cat([velha.select(b).unmask(-9999).neq(nova.select(b).unmask(-9999)).rename(b)
                               for b in OUTRAS + ['amplitude_diaria', 'deficit_diario', 'chuva_efetiva']])
    sobra = rs_n.lt(ra.multiply(0.03)).And(rs_n.mask().gt(0))
    pilha = ee.Image.cat([abaixo.rename('abaixo'), sumiu.rename('sumiu'), abaixo.neq(sumiu).rename('fora_da_regra'),
                          mudou_rs.unmask(0).rename('rs_mudou_valor'), sobra.unmask(0).rename('sobra'),
                          outras_dif.reduce(ee.Reducer.max()).rename('outras_mudaram'),
                          rs_v.mask().gt(0).rename('com_rs')]).unmask(0)
    r = pilha.reduceRegion(ee.Reducer.sum(), BRASIL, crs=sp.CRS, crsTransform=sp.TRANSFORM, maxPixels=1e10,
                           tileScale=4).getInfo()
    r = {k: int(round(x or 0)) for k, x in r.items()}
    print(f"   {dia}: pixels com Rs {r['com_rs']:,} | abaixo de 3% de Ra (antiga) {r['abaixo']} | vazios na nova "
          f"{r['sumiu']} | fora da regra {r['fora_da_regra']} | Rs com valor mudado {r['rs_mudou_valor']} | "
          f"abaixo do limite na nova {r['sobra']} | outras bandas mudaram {r['outras_mudaram']}")
    confere(r['fora_da_regra'] == 0 and r['abaixo'] == r['sumiu'] and r['rs_mudou_valor'] == 0 and r['sobra'] == 0
            and r['outras_mudaram'] == 0 and r['com_rs'] > 60000,
            f'{dia}: só os {r["abaixo"]} pixel(s) abaixo do limite ficam vazios, e só no Rs')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'VERIFICAÇÃO OK'))
sys.exit(1 if falhas else 0)
