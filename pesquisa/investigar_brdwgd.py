# Investigação do BR-DWGD bruto (projects/ee-alexandrexavier/assets/BR-DWGD), 1961–2025. SÓ LEITURA no Earth Engine.
# Motivo (26/11/2026): a chuva do banco sobe de repente em 2020 contra GLDAS-2.1, IMERG, PERSIANN e TerraClimate
# (+10 a +18% sobre 2001–2015; até 2019, ±3%), e o CHIRPS sobe bem menos; a radiação cai ~0,7 MJ contra o TerraClimate.
# Este script mostra o que mudou na fonte:
#   A. metadados de cada ano: número de imagens, bandas, propriedades da 1ª imagem do ano;
#   B. por ano e região (5 + Brasil, pixels entregues): a chuva do BR-DWGD bruto decomposta em total, dias >= 1 mm,
#      intensidade (total / dias), maior dia e pixel-dias válidos (cobertura); o mesmo para o CHIRPS diário
#      (UCSB-CHG/CHIRPS/DAILY, 1981–) e o ERA5-Land diário bruto; e o banco (sab_pedido.colecao) para conferir se ele é
#      o BR-DWGD bruto.
#     python pesquisa/investigar_brdwgd.py         (retomável; TEMPO_MAX_MIN)
#     python pesquisa/investigar_brdwgd.py resumo
import glob
import os
import sys
import time

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
SAIDA = os.path.join(AQUI, 'resultados_brdwgd')
BRDWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
REG = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil']


def metadados(vm):
    ee = vm.ee
    arq = os.path.join(SAIDA, 'metadados.csv')
    if os.path.exists(arq):
        return
    col = ee.ImageCollection(BRDWGD)
    linhas = []
    for ano in range(1961, 2026):
        c = col.filterDate(f'{ano}-01-01', f'{ano + 1}-01-01')
        info = ee.Dictionary({'n': c.size(), 'bandas': c.first().bandNames(),
                              'props': c.first().toDictionary(), 'nomes': c.first().propertyNames(),
                              'id': c.first().get('system:index')}).getInfo()
        linhas.append({'ano': ano, 'imagens': info['n'], 'bandas': ' '.join(info['bandas']),
                       'id_1a_imagem': info.get('id'), 'propriedades': ' '.join(sorted(info['nomes'])),
                       'valores': '; '.join(f'{k}={v}' for k, v in sorted(info['props'].items()))})
        print(f'   metadados {ano}: {info["n"]} imagens', flush=True)
    pd.DataFrame(linhas).to_csv(arq, index=False)


def ano_img(vm, ano):
    ee = vm.ee
    ini, fim = f'{ano}-01-01', f'{ano + 1}-01-01'

    def br(i):
        ok = i.select('pr').gt(-32768)
        return i.select('pr').updateMask(ok).multiply(0.00686666).add(225.0).max(0).rename('p')
    fontes = {
        'br': ee.ImageCollection(BRDWGD).filterDate(ini, fim).map(br),
        'sab': vm.sp.colecao(vm.BRASIL, ini, fim).select(['pr_mm'], ['p']),
        'era5': ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').filterDate(ini, fim)
        .map(lambda i: i.select('total_precipitation_sum').multiply(1000).max(0).rename('p')),
    }
    if ano >= 1981:
        fontes['chirps'] = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').filterDate(ini, fim).select(['precipitation'], ['p'])
    b = []
    for k, c in fontes.items():
        b += [c.sum().rename(f'{k}_total'), c.map(lambda i: ee.Image(i).gte(1)).sum().rename(f'{k}_dias'),
              c.max().rename(f'{k}_max'), c.count().rename(f'{k}_n')]
    return ee.Image.cat(b).toFloat()


def rodar():
    import validar_metodo_2026 as vm
    os.makedirs(os.path.join(SAIDA, 'anos'), exist_ok=True)
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)
    metadados(vm)
    regs = vm.v.regioes()
    # do mais recente para o mais antigo: o que interessa (2010–2025) sai primeiro
    for ano in list(range(2025, 2009, -1)) + list(range(2009, 1960, -1)):
        arq = os.path.join(SAIDA, 'anos', f'{ano}.csv')
        if os.path.exists(arq):
            continue
        if time.time() > limite:
            resumo()
            raise SystemExit(3)
        t0 = time.time()
        img = ano_img(vm, ano)
        res = vm.reduzir(img, regs, img.bandNames().getInfo())
        linhas = [{'regiao': r, 'ano': ano, **{k: v for k, v in p.items() if k != 'regiao'}} for r, p in res.items()]
        pd.DataFrame(linhas).to_csv(arq, index=False)
        print(f'   {ano} pronto em {time.time() - t0:.0f} s', flush=True)
    resumo()


def resumo():
    arqs = sorted(glob.glob(os.path.join(SAIDA, 'anos', '*.csv')))
    if not arqs:
        return
    d = pd.concat(pd.read_csv(a) for a in arqs).sort_values('ano')
    for k in ('br', 'sab', 'era5', 'chirps'):
        if f'{k}_total' in d:
            d[f'{k}_int'] = d[f'{k}_total'] / d[f'{k}_dias']
    L = ['# O BR-DWGD bruto, ano a ano (1961–2025)', '',
         'Médias regionais nos pixels entregues. total = chuva do ano (mm); dias = dias com ≥ 1 mm; int = total / dias '
         '(mm por dia de chuva); n = pixel-dias válidos no ano (cobertura). BR = BR-DWGD bruto; SAB = o que o banco entrega; '
         'CHIRPS diário e ERA5-Land bruto como comparação. Razões em relação à média de 2001–2015.', '']
    meta = os.path.join(SAIDA, 'metadados.csv')
    if os.path.exists(meta):
        m = pd.read_csv(meta)
        L += ['## Metadados (1ª imagem de cada ano)', '', '| Ano | Imagens | Bandas | Propriedades |', '|---|---|---|---|']
        ant = None
        for r in m.itertuples():
            marca = '' if ant is None or (r.bandas, r.propriedades) == ant else ' ⚠️ mudou'
            L.append(f'| {r.ano} | {r.imagens} | {r.bandas} | {r.propriedades}{marca} |')
            ant = (r.bandas, r.propriedades)
        L.append('')
    for reg in REG:
        g = d[d.regiao == reg].set_index('ano')
        if g.empty:
            continue
        base = g.loc[2001:2015]
        L += [f'## {reg}', '', '| Ano | BR total | SAB/BR | BR/CHIRPS (total) | BR/CHIRPS (dias) | BR/CHIRPS (intens.) | '
              'BR/ERA5 (total) | BR/ERA5 (dias) | cobertura BR (n) |', '|---|---|---|---|---|---|---|---|---|']
        for a, r in g.iterrows():
            def rel(num, den):
                if den not in g or num not in g:
                    return '-'
                b = (base[num] / base[den]).median()
                v = r[num] / r[den]
                return f'{100 * (v / b - 1):+.1f}%' if pd.notna(v) and b else '-'
            L.append(f"| {a} | {r['br_total']:.0f} | {r['sab_total'] / r['br_total']:.3f} | {rel('br_total', 'chirps_total')} | "
                     f"{rel('br_dias', 'chirps_dias')} | {rel('br_int', 'chirps_int')} | {rel('br_total', 'era5_total')} | "
                     f"{rel('br_dias', 'era5_dias')} | {r['br_n']:.0f} |")
        L.append('')
    with open(os.path.join(SAIDA, 'RESULTADOS.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L[:60]))


if __name__ == '__main__':
    resumo() if (sys.argv[1:] or [''])[0] == 'resumo' else rodar()
