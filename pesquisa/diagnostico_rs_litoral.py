# Diagnóstico (só leitura) do Rs gravado = 0 nos pixels do litoral em 04-20/03 e 23/09-08/10/2026 (K26, 22/11/2026).
# A ETo gravada nesses dias é coerente com um Rs normal, mas o motor V1.6 calcula a ETo com o MESMO Rs que grava
# (_componentes_era5 -> processarDia_Rota1). Este script separa as duas explicações possíveis:
#   (a) o código de hoje dá Rs = 0 ali (então o defeito está na conta; ver os passos da conta abaixo);
#   (b) o código de hoje dá um Rs normal (então o Rs = 0 veio de outra gravação: ver as datas de atualização dos assets).
# Rodar: GitHub Actions (workflow "Diagnostico Rs litoral") ou Colab, na pasta do repositório:
#     python pesquisa/diagnostico_rs_litoral.py
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
ELEV = ee.Image('USGS/SRTMGL1_003')
FATOR_MAX = 5.0
PIXELS = {'Lagoa Mirim (B)': (-32.65, -52.85), 'costa do Amapá (B)': (0.05, -50.95), 'Maranhão (B)': (-1.45, -44.85)}
DIAS = ['2026-03-01', '2026-03-03', '2026-03-04', '2026-03-10', '2026-03-20', '2026-03-21',
        '2026-09-22', '2026-09-23', '2026-10-08', '2026-10-09']


def expandir_borda(img):              # o mesmo do motor V1.6
    return img.unmask(img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMean(1, 'square', 'pixels'))


def rso(data):                        # radiacao_ceu_claro do motor V1.6 (elevação SRTM com máscara)
    return sp._radiacao_topo(ee.Date(data)).multiply(ELEV.multiply(0.00002).add(0.75)).rename('rso')


def no_pixel(img, lat, lon):
    pt = ee.Geometry.Point([lon, lat])
    return img.reduceRegion(ee.Reducer.first(), pt, crs=CRS, crsTransform=TRANSFORM)


print('1) Quando cada dia foi gravado (updateTime do asset) e com que propriedades')
for d in DIAS + ['2026-11-15', '2026-11-16', '2026-11-17']:
    nome = f"{sp.SAB}/SAB_{d.replace('-', '_')}"
    try:
        a = ee.data.getAsset(nome)
        p = a.get('properties', {})
        print(f"   {d}: atualizado {a.get('updateTime', '?')} | versao {p.get('versao')} | alg {p.get('versao_algoritmo')} | "
              f"fonte {p.get('fonte')} | rs_limitado_rso {p.get('rs_limitado_rso')} | metodo {p.get('metodo_ur_vento_era5')}")
    except Exception as e:  # noqa: BLE001
        print(f'   {d}: {str(e)[:120]}')

print('\n2) A conta do Rs do motor V1.6, passo a passo, no pixel (e o que está gravado)')
for rotulo, (la, lo) in PIXELS.items():
    lat, lon = sp.centro_do_pixel(la, lo)
    print(f'\n   {rotulo} ({lat:.5f}, {lon:.5f})')
    for d in DIAS:
        d1 = str(ee.Date(d).advance(1, 'day').format('YYYY-MM-dd').getInfo())
        era = ee.Image(ERA5.filterDate(d, d1).first())
        clima = ee.Image(f'{CLIMA}/Matriz_Clima_{d[5:7]}')
        rs_cru = era.select('surface_solar_radiation_downwards_sum').divide(1e6)
        rs_bil = rs_cru.resample('bilinear')
        fator = expandir_borda(clima.select('Rs_m_br')).divide(expandir_borda(clima.select('Rs_m_era')).max(1e-3))
        calib = rs_bil.multiply(fator.min(FATOR_MAX)).max(0)
        limit = calib.min(rso(d))
        cheio = expandir_borda(limit)
        grav = ee.Image(f"{sp.SAB}/SAB_{d.replace('-', '_')}")
        pilha = ee.Image.cat([
            rs_cru.rename('era5_cru'), rs_cru.mask().rename('era5_mascara'), rs_bil.rename('era5_bilinear'),
            clima.select('Rs_m_br').rename('clima_br'), clima.select('Rs_m_era').rename('clima_era'),
            fator.rename('fator'), calib.rename('calibrado'), rso(d).rename('rso'), ELEV.rename('srtm'),
            ELEV.mask().rename('srtm_mascara'), limit.rename('limitado'), cheio.rename('com_borda'),
            grav.select('rs').rename('gravado_rs'), grav.select('et_potencial').rename('gravado_eto'),
            grav.select('rs').mask().rename('gravado_mascara')])
        try:
            v = no_pixel(pilha, lat, lon).getInfo()
            f = lambda k: 'vazio' if v.get(k) is None else f'{v[k]:.3f}'   # noqa: E731
            print(f"      {d}: ERA5 cru {f('era5_cru')} (máscara {f('era5_mascara')}), bilinear {f('era5_bilinear')} | "
                  f"clima br {f('clima_br')} era {f('clima_era')} fator {f('fator')} | calibrado {f('calibrado')} | "
                  f"Rso {f('rso')} (SRTM {f('srtm')}, máscara {f('srtm_mascara')}) | limitado {f('limitado')} | "
                  f"com a borda {f('com_borda')} || GRAVADO Rs {f('gravado_rs')} ETo {f('gravado_eto')} "
                  f"(máscara {f('gravado_mascara')})")
        except Exception as e:  # noqa: BLE001
            print(f'      {d}: {str(e)[:200]}')

print('\nLeitura: se "com a borda" for normal e o GRAVADO for 0, a conta de hoje não reproduz o 0 (explicação b).')
print('Se "com a borda" também for 0, o passo em que ele vira 0 é o primeiro com 0 na linha (explicação a).')
