# Verificação prévia (só leitura) da mudança do motor V1.7: radiação 0 do ERA5-Land tratada como vazia.
# Refaz SÓ a conta do Rs do motor (_componentes_era5 -> expandir_borda -> finalizar) do jeito da V1.6 e do jeito da
# V1.7, no Brasil inteiro, e confere:
#   1. a conta da V1.6 aqui reproduz o Rs GRAVADO (prova de que a réplica está certa);
#   2. nos dias normais, a V1.7 dá exatamente o mesmo Rs da V1.6;
#   3. nos dias das janelas (04-20/03 e 23/09-08/10/2026), os pixels com Rs ~0 ganham valor normal e nenhum fica
#      abaixo de 3% de Ra nem vazio;
#   4. [24/11, depois da 1ª execução] os OUTROS pixels que mudam nas janelas (~1.230, no litoral) eram contaminados
#      pelo 0 do mar na interpolação bilinear: na V1.6 o Rs deles fica abaixo do dos dias normais vizinhos (antes e
#      depois da janela) e na V1.7 volta para perto deles.
# A simulação completa do motor (05a da V1.7, com a prévia de todas as bandas) roda depois, no sab-motor.
#     python pesquisa/verificar_v17_rs.py
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import ee  # noqa: E402
import sab_pedido as sp  # noqa: E402

ee.Initialize(project=sp.PROJETO)
CRS, TRANSFORM = sp.CRS, sp.TRANSFORM
CLIMA = 'projects/clima-492922/assets/SICSB_1986_2025'
ERA5 = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR')
BRASIL = ee.Geometry.Rectangle([-74.0, -34.0, -34.0, 5.5], None, False)
ELEV = ee.Image('USGS/SRTMGL1_003').clip(BRASIL)
MASCARA_SAB = ee.Image(f'{sp.SAB}/SAB_2025_12_31').select('pr_mm').mask()
CLASSE = ee.Image(sp.MASCARA).select('classe').unmask(0, False)
FATOR_MAX = 5.0
DIAS = [('2026-03-10', 'janela'), ('2026-03-15', 'janela'), ('2026-10-01', 'janela'), ('2026-06-15', 'normal'),
        ('2026-11-10', 'normal')]
# dias normais logo antes e logo depois de cada janela: a referência do Rs "de verdade" daqueles pixels
VIZINHOS = {'03': ('2026-03-01', '2026-03-02', '2026-03-03', '2026-03-21', '2026-03-22', '2026-03-23'),
            '10': ('2026-09-20', '2026-09-21', '2026-09-22', '2026-10-09', '2026-10-10', '2026-10-11')}
falhas = 0


def confere(cond, msg):
    global falhas
    print(('  ok   ' if cond else '  FALHA ') + msg, flush=True)
    falhas += 0 if cond else 1


def expandir_borda(img):              # o mesmo do motor
    return img.unmask(img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMean(1, 'square', 'pixels'))


def rs_motor(dia, v17):
    d1 = ee.Date(dia).advance(1, 'day')
    era = ee.Image(ERA5.filterDate(dia, d1).first())
    clima = ee.Image(f'{CLIMA}/Matriz_Clima_{dia[5:7]}')
    cru = era.select('surface_solar_radiation_downwards_sum').divide(1e6)
    rs_raw = (cru.updateMask(cru.gt(0)) if v17 else cru).resample('bilinear')
    fator = expandir_borda(clima.select('Rs_m_br')).divide(expandir_borda(clima.select('Rs_m_era')).max(1e-3))
    calib = rs_raw.multiply(fator.min(FATOR_MAX)).max(0)
    ra = sp._radiacao_topo(ee.Date(dia))
    rso = ra.multiply(ELEV.multiply(0.00002).add(0.75))
    return expandir_borda(calib.min(rso)).updateMask(MASCARA_SAB).rename('rs'), ra


for dia, tipo in DIAS:
    v16, ra = rs_motor(dia, False)
    v17, _ = rs_motor(dia, True)
    grav = ee.Image(f"{sp.SAB}/SAB_{dia.replace('-', '_')}").select('rs')
    lim = ra.multiply(0.03)
    tem = grav.mask().gt(0)
    entregue = CLASSE.gte(1).And(CLASSE.lte(3))
    pilha = ee.Image.cat([
        tem.rename('pixels'),
        tem.And(v16.unmask(-1).subtract(grav.unmask(-1)).abs().gt(0.01)).rename('v16_difere_do_gravado'),
        tem.And(v17.unmask(-1).subtract(v16.unmask(-1)).abs().gt(0.01)).rename('v17_muda'),
        tem.And(grav.unmask(99).lt(lim)).rename('gravado_abaixo'),
        tem.And(v17.unmask(99).lt(lim)).rename('v17_abaixo'),
        tem.And(v17.mask().eq(0)).rename('v17_vazio'),
        tem.And(v17.unmask(-1).subtract(v16.unmask(-1)).abs().gt(0.01)).And(grav.unmask(99).gte(lim)).rename('muda_fora_da_regra'),
        tem.And(grav.unmask(99).lt(lim)).And(entregue).rename('abaixo_entregue')]).unmask(0).updateMask(ee.Image(1))
    r = {k: int(round(v or 0)) for k, v in pilha.reduceRegion(ee.Reducer.sum(), BRASIL, crs=CRS, crsTransform=TRANSFORM,
                                                                 maxPixels=1e10, tileScale=4).getInfo().items()}
    medias = ee.Image.cat([v16.rename('v16'), v17.rename('v17')]).updateMask(
        grav.unmask(99).lt(lim)).reduceRegion(ee.Reducer.mean(), BRASIL, crs=CRS, crsTransform=TRANSFORM,
                                              maxPixels=1e10, tileScale=4).getInfo()
    print(f"\n{dia} ({tipo}): {r['pixels']:,} pixels | V1.6 refeita ≠ gravado: {r['v16_difere_do_gravado']} | "
          f"V1.7 muda: {r['v17_muda']} | gravado abaixo de 3% de Ra: {r['gravado_abaixo']} (entregues "
          f"{r['abaixo_entregue']}) | V1.7 abaixo: {r['v17_abaixo']} | V1.7 vazio: {r['v17_vazio']} | "
          f"muda fora dos pixels abaixo: {r['muda_fora_da_regra']}", flush=True)
    if r['gravado_abaixo']:
        print(f"   nesses pixels, Rs médio: V1.6 {medias.get('v16') or 0:.2f} -> V1.7 {medias.get('v17') or 0:.2f} MJ/m²")
    confere(r['v16_difere_do_gravado'] <= max(3, r['pixels'] // 10000),
            f'{dia}: a réplica da conta da V1.6 reproduz o Rs gravado')
    if tipo == 'normal':
        confere(r['v17_muda'] == 0, f'{dia}: dia normal, a V1.7 não muda nada')
    else:
        confere(r['gravado_abaixo'] > 0 and r['v17_abaixo'] == 0 and r['v17_vazio'] == 0,
                f'{dia}: os {r["gravado_abaixo"]} pixel(s) com Rs ~0 ganham valor normal na V1.7, nenhum fica vazio')
        muda = tem.And(v17.unmask(-1).subtract(v16.unmask(-1)).abs().gt(0.01)).And(grav.unmask(99).gte(lim))
        ref = ee.ImageCollection([ee.Image(f"{sp.SAB}/SAB_{d.replace('-', '_')}").select('rs')
                                  for d in VIZINHOS[dia[5:7]]]).mean()
        # o Rs de um dia varia com as nuvens: compara a razão com a dos pixels que NÃO mudam (o tempo do dia)
        estat = ee.Image.cat([v16.rename('v16'), v17.rename('v17'), ref.rename('ref'),
                              v17.gt(v16).rename('sobe'), muda.And(entregue).rename('entregues')]).updateMask(muda)
        e = estat.reduceRegion(ee.Reducer.mean().combine(ee.Reducer.sum(), outputPrefix='', sharedInputs=True),
                               BRASIL, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4).getInfo()
        cont = ee.Image.cat([v16.rename('v16'), ref.rename('ref')]).updateMask(tem.And(muda.Not()).And(
            v16.mask())).reduceRegion(ee.Reducer.mean(), BRASIL, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10,
                                      tileScale=4).getInfo()
        dia_rel = (cont['v16'] or 0) / max(cont['ref'] or 1e-6, 1e-6)
        r16, r17 = (e['v16_mean'] or 0) / max(e['ref_mean'] or 1e-6, 1e-6), (e['v17_mean'] or 0) / max(e['ref_mean'] or 1e-6, 1e-6)
        print(f"   os outros {r['muda_fora_da_regra']} pixels que mudam ({int(e['entregues_sum'] or 0)} entregues): Rs médio "
              f"V1.6 {e['v16_mean'] or 0:.2f} -> V1.7 {e['v17_mean'] or 0:.2f} MJ/m²; dias normais vizinhos "
              f"{e['ref_mean'] or 0:.2f}; sobe em {100 * (e['sobe_mean'] or 0):.0f}% deles | razão dia/vizinhos: "
              f"V1.6 {r16:.2f}, V1.7 {r17:.2f}, resto do Brasil {dia_rel:.2f}")
        confere((e['sobe_mean'] or 0) >= 0.8 and abs(r17 - dia_rel) < abs(r16 - dia_rel),
                f'{dia}: nos outros pixels que mudam, a V1.6 estava rebaixada pelo 0 do mar e a V1.7 volta para perto '
                f'do esperado')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'VERIFICAÇÃO DA V1.7 OK'))
sys.exit(1 if falhas else 0)
