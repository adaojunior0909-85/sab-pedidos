# Verificação COM Earth Engine da regra 2026.11.22 (radiação abaixo de 3% de Ra sai vazia, com a ETo e o déficit do dia,
# que foram calculados com ela). Só lê (getInfo).
# Rodar: no GitHub Actions (workflow "Verificar radiacao impossivel") ou no Colab, na pasta do repositório:
#     python testes/verificar_rs_impossivel_ee.py
#
# Compara a leitura NOVA (sab_pedido.colecao) com a ANTIGA (a mesma, sem vazio_rs_impossivel):
#   1. num pixel B do litoral do RS (Lagoa Mirim), em 10/03/2026 (Rs gravado = 0 pela K26): a antiga entrega Rs 0, a
#      nova deixa Rs, ETo e déficit vazios, e as outras bandas ficam iguais; em 01/03/2026 (fora da janela), tudo igual;
#   2. no Brasil inteiro, em dias com e sem o problema: os pixels que mudam são EXATAMENTE os que tinham Rs < 3% de Ra
#      na leitura antiga, neles a ETo e o déficit também ficam vazios, nenhum Rs abaixo do limite sobra na nova, e nenhuma
#      outra banda (nem a ETo e o déficit dos outros pixels) muda.
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import ee  # noqa: E402
import sab_pedido as sp  # noqa: E402

ee.Initialize(project=sp.PROJETO)
NOVA = sp.vazio_rs_impossivel
BANDAS = list(sp.BANDAS_SAB)
JUNTAS = ['et_potencial', 'deficit_diario']           # vazias junto com o Rs
OUTRAS = [b for b in BANDAS if b not in ['rs'] + JUNTAS] + ['amplitude_diaria', 'chuva_efetiva']
BRASIL = ee.Geometry.Rectangle([-74.0, -34.0, -34.0, 5.5], None, False)
CLASSE = ee.Image(sp.MASCARA).select('classe').unmask(0, False)
NOMES_CLASSE = {1: 'A', 2: 'B', 3: 'C_interior', 4: 'C_borda', 0: 'sem_classe'}
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
        confere(a is not None and a < 0.03 * ra and n is None and all(v['nova'].get(b) is None for b in JUNTAS)
                and all(v['antiga'].get(b) is not None for b in JUNTAS),
                f'{dia}: Rs {a} (abaixo de 3% de Ra) agora sai vazio, com a ETo ({v["antiga"].get("et_potencial")}) e o déficit')
    else:
        confere(a is not None and a >= 0.03 * ra and n == a and all(v['nova'].get(b) == v['antiga'].get(b) for b in JUNTAS),
                f'{dia}: Rs normal ({a}), ETo e déficit continuam iguais')
    outras = [b for b in v['antiga'] if b in OUTRAS and v['antiga'][b] != v['nova'].get(b)]
    confere(not outras, f'{dia}: as outras bandas ficam iguais ({len(v["antiga"]) - 1} conferidas)')

print('\n2) Brasil inteiro: só os pixels com Rs < 3% de Ra mudam, e só no Rs, na ETo e no déficit')
for dia in ('2026-03-10', '2026-10-01', '2026-11-16', '2025-06-15', '1965-01-15'):
    velha, nova = leitura(BRASIL, dia, False), leitura(BRASIL, dia, True)
    ra = sp._radiacao_topo(ee.Date(dia))
    rs_v, rs_n = velha.select('rs'), nova.select('rs')
    # contagens em PIXELS inteiros: o unmask tira a máscara fracionária da borda, que pesaria a soma
    tem_v, tem_n = rs_v.mask().gt(0), rs_n.mask().gt(0)
    abaixo = rs_v.unmask(9999).lt(ra.multiply(0.03)).And(tem_v)
    sumiu = tem_v.And(tem_n.Not())
    mudou_rs = tem_n.And(rs_n.unmask(0).neq(rs_v.unmask(0)))
    outras_dif = ee.Image.cat([velha.select(b).unmask(-9999).neq(nova.select(b).unmask(-9999)).rename(b) for b in OUTRAS])
    # ETo e déficit: vazios exatamente onde o Rs sumiu; iguais em todo o resto
    juntas_erro = ee.Image.cat([
        sumiu.And(nova.select(b).mask().gt(0)).Or(sumiu.Not().And(
            velha.select(b).unmask(-9999).neq(nova.select(b).unmask(-9999)))).rename(b) for b in JUNTAS])
    sobra = rs_n.unmask(9999).lt(ra.multiply(0.03)).And(tem_n)
    pilha = ee.Image.cat([abaixo.rename('abaixo'), sumiu.rename('sumiu'), abaixo.neq(sumiu).rename('fora_da_regra'),
                          mudou_rs.rename('rs_mudou_valor'), sobra.rename('sobra'),
                          outras_dif.reduce(ee.Reducer.max()).rename('outras_mudaram'),
                          juntas_erro.reduce(ee.Reducer.max()).rename('eto_deficit_fora'),
                          tem_v.rename('com_rs')] +
                         [sumiu.And(CLASSE.eq(k)).rename(f'vazio_{n}') for k, n in NOMES_CLASSE.items()]
                         ).unmask(0).updateMask(ee.Image(1))
    r = pilha.reduceRegion(ee.Reducer.sum(), BRASIL, crs=sp.CRS, crsTransform=sp.TRANSFORM, maxPixels=1e10,
                           tileScale=4).getInfo()
    r = {k: int(round(x or 0)) for k, x in r.items()}
    print(f"   {dia}: pixels com Rs {r['com_rs']:,} | abaixo de 3% de Ra (antiga) {r['abaixo']} | vazios na nova "
          f"{r['sumiu']} | fora da regra {r['fora_da_regra']} | Rs com valor mudado {r['rs_mudou_valor']} | "
          f"abaixo do limite na nova {r['sobra']} | outras bandas mudaram {r['outras_mudaram']} | "
          f"ETo/déficit fora da regra {r['eto_deficit_fora']}")
    print('      vazios por classe (pixels inteiros): ' + ', '.join(f"{n} {r[f'vazio_{n}']}" for n in NOMES_CLASSE.values()))
    confere(r['fora_da_regra'] == 0 and r['abaixo'] == r['sumiu'] and r['rs_mudou_valor'] == 0 and r['sobra'] == 0
            and r['outras_mudaram'] == 0 and r['eto_deficit_fora'] == 0 and r['com_rs'] > 60000,
            f'{dia}: só os {r["abaixo"]} pixel(s) abaixo do limite ficam vazios (Rs, ETo e déficit); o resto é igual')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'VERIFICAÇÃO OK'))
sys.exit(1 if falhas else 0)
