# TESTE DE SENSIBILIDADE À RESOLUÇÃO: as comparações levam cada referência para a grade do SAB (0,1°) antes de tirar a
# média da região. Este teste refaz a média de CADA referência, em CADA variável e em CADA mês usado nas comparações,
# na RESOLUÇÃO NATIVA da própria fonte (a projeção e o pixel dela), nas mesmas regiões e com a mesma máscara de pixels
# entregues, e mede quanto o valor da referência muda. Como viés = SAB − referência, a mudança no viés é exatamente
# essa diferença. SÓ LEITURA no Earth Engine.
#   Fontes e períodos (os mesmos das comparações):
#     CHIRPS (0,05°)                chuva                           1981–2026
#     TerraClimate (1/24°)          as 10 variáveis                 1961–2025
#     MODIS Terra MOD11A2 (1 km)    LST de dia                      set e out de 2003–2026
#     MODIS Aqua MYD11A2 (1 km)     LST de dia e de noite           2016–2021
#     MODIS MOD16A2GF (500 m)       ET                              2016–2021
#     SMAP SPL3SMP_E (9 km)         umidade 0–5 cm                  2016–2021
#     GLDAS-2.1 (0,25°)             as 16 variáveis                 2022–2026 (meses da parte B)
# REGRA FIXADA ANTES DE RODAR (25/11/2026): a resolução é IRRELEVANTE para uma fonte/variável/região se o percentil 95
#   de |nativa − grade do SAB| nos meses for no máximo 1/5 da tolerância das comparações (somas: 1% do valor; Tmax/Tmin
#   e temperaturas: 0,1 °C; UR: 0,6 p.p.; VPD: 0,02 kPa; radiação: 0,1 MJ/m²/dia; vento: 0,04 m/s; umidade do solo:
#   0,004 m³/m³). Se passar disso, o resultado da comparação é refeito com a média nativa e as duas ficam registradas.
#     python pesquisa/sensibilidade_resolucao.py    (retomável; TEMPO_MAX_MIN limita: sai com código 3 se faltar)
import glob
import os
import sys
import time
from datetime import date, timedelta

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ee  # noqa: E402
import validar_historico as vh  # noqa: E402  (inicia o Earth Engine; TerraClimate e CHIRPS)

vm, v, sp = vh.vm, vh.v, vh.sp
SAIDA = os.path.join(AQUI, 'resultados_resolucao')


def tol(var):
    if var in vm.SOMA or var in vh.SOMA or var in ('pr_chirps', 'et_mod16'):
        return ('%', 1.0)
    return ('unid', {'tmax_C': 0.1, 'tmin_C': 0.1, 'tsolo_C': 0.1, 'tfolha_C': 0.1, 'lst_dia_C': 0.1, 'lst_noite_C': 0.1,
                     'RH': 0.6, 'vpd': 0.02, 'rs': 0.1, 'u2': 0.04, 'soil_moisture_0_5cm_m3_m3': 0.004,
                     'soil_moisture_0_100cm_m3_m3': 0.004, 'smap_0_5cm': 0.004, 'agua_solo': None}.get(var))


def duas_escalas(img, nativa, regs):
    """Média de cada região na grade do SAB e na projeção nativa da fonte, num pedido só."""
    m = img.updateMask(v.ENTREGUE)
    g = m.reduceRegions(collection=regs, reducer=ee.Reducer.mean(), crs=sp.CRS, crsTransform=sp.TRANSFORM, tileScale=16)
    n = m.reduceRegions(collection=regs, reducer=ee.Reducer.mean(), crs=nativa, tileScale=16)
    r = ee.Dictionary({'g': g, 'n': n}).getInfo()
    return ({f['properties']['regiao']: f['properties'] for f in r['g']['features']},
            {f['properties']['regiao']: f['properties'] for f in r['n']['features']})


def mes_fim(ano, mes):
    return ee.Date.fromYMD(ano, mes, 1), ee.Date.fromYMD(ano, mes, 1).advance(1, 'month')


def fontes():
    """(nome, projeção nativa, anos, meses, função ano,mes -> imagem com as bandas de cada variável)."""
    tc = vh.TC
    chirps = vh.CHIRPS
    mod11, myd11 = ee.ImageCollection('MODIS/061/MOD11A2'), ee.ImageCollection('MODIS/061/MYD11A2')
    mod16 = ee.ImageCollection('MODIS/061/MOD16A2GF').select('ET')
    smap = ee.ImageCollection('NASA/SMAP/SPL3SMP_E/006').select('soil_moisture_am')
    ult_tc = int(v.ultimo(tc)[:4])

    def f_tc(a, m):
        ini, fim = mes_fim(a, m)
        i = ee.Image(tc.filterDate(ini, fim).first())
        return ee.Image.cat([i.select(bt).multiply(esc).rename(k) for k, (_, bt, esc, _) in vh.PARES.items()])

    def f_chirps(a, m):
        ini, fim = mes_fim(a, m)
        return chirps.filterDate(ini, fim).sum().rename('pr_chirps')

    def f_terra(a, m):
        ini, fim = mes_fim(a, m)
        return mod11.filterDate(ini, fim).select('LST_Day_1km').mean().multiply(0.02).subtract(273.15).rename('lst_dia_C')

    def f_aqua(a, m):
        ini, fim = mes_fim(a, m)
        c = myd11.filterDate(ini, fim)
        return ee.Image.cat([c.select('LST_Day_1km').mean().multiply(0.02).subtract(273.15).rename('lst_dia_C'),
                             c.select('LST_Night_1km').mean().multiply(0.02).subtract(273.15).rename('lst_noite_C')])

    def f_mod16(a, m):
        ini, fim = mes_fim(a, m)
        return mod16.filterDate(ini, fim).sum().multiply(0.1).rename('et_mod16')

    def f_smap(a, m):
        ini, fim = mes_fim(a, m)
        return smap.filterDate(ini, fim).mean().rename('smap_0_5cm')

    def f_gldas(a, m):
        d0 = date(a, m, 1)
        return vm.gldas_mes(d0.isoformat(), (d0 + timedelta(days=32)).replace(day=1).isoformat())

    fim_g = date.fromisoformat(v.ultimo(vm.GLDAS.filterDate('2026-01-01', '2027-01-01'))[:10])
    meses_g = [m for m in range(1, 13) if (date(2026, m, 1) + timedelta(days=32)).replace(day=1) <= fim_g + timedelta(days=1)]
    proj = lambda col, b: ee.Image(col.first()).select(b).projection()   # noqa: E731
    return [
        ('chirps', proj(chirps, 'precipitation'), range(1981, 2027), range(1, 13), f_chirps),
        ('terraclimate', proj(tc, 'pr'), range(1961, ult_tc + 1), range(1, 13), f_tc),
        ('modis_terra_lst', proj(mod11, 'LST_Day_1km'), range(2003, 2027), (9, 10), f_terra),
        ('modis_aqua_lst', proj(myd11, 'LST_Day_1km'), range(2016, 2022), range(1, 13), f_aqua),
        ('modis_mod16_et', proj(mod16, 'ET'), range(2016, 2022), range(1, 13), f_mod16),
        ('smap', proj(smap, 'soil_moisture_am'), range(2016, 2022), range(1, 13), f_smap),
        ('gldas', proj(vm.GLDAS, 'Tair_f_inst'), range(2022, 2027), meses_g, f_gldas),
    ]


def main():
    regs = v.regioes(com_ufs=True)
    ult_chirps = v.ultimo(vh.CHIRPS.filterDate('2026-01-01', '2027-01-01'))
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)
    for nome, nativa, anos, meses, f in fontes():
        pasta = os.path.join(SAIDA, nome)
        os.makedirs(pasta, exist_ok=True)
        for ano in anos:
            arq = os.path.join(pasta, f'{ano}.csv')
            if os.path.exists(arq):
                continue
            if time.time() > limite:
                print('Tempo desta vez acabou; a próxima retoma daqui.')
                raise SystemExit(3)
            t0, linhas = time.time(), []
            for mes in meses:
                if nome == 'chirps' and f'{ano}-{mes:02d}-26' > ult_chirps:
                    continue                                    # CHIRPS ainda sem o mês inteiro
                img = f(ano, mes)
                for tentativa in range(4):
                    try:
                        g, n = duas_escalas(img, nativa, regs)
                        break
                    except Exception as e:  # noqa: BLE001
                        print(f'   ⚠️ {nome} {ano}-{mes:02d}: {str(e)[:150]}', flush=True)
                        time.sleep(20 * (tentativa + 1))
                else:
                    raise RuntimeError(f'{nome} {ano}-{mes:02d}: não deu depois de 4 tentativas')
                for reg in g:
                    for var, val in g[reg].items():
                        if var in ('regiao', 'system:index'):
                            continue
                        linhas.append({'fonte': nome, 'variavel': var, 'regiao': reg, 'ano': ano, 'mes': mes,
                                       'grade_sab': val, 'nativa': n.get(reg, {}).get(var)})
            if linhas:
                pd.DataFrame(linhas).to_csv(arq, index=False)
            print(f'   {nome} {ano} pronto em {time.time() - t0:.0f} s', flush=True)
    resumo()


def resumo():
    arqs = sorted(glob.glob(os.path.join(SAIDA, '*', '*.csv')))
    df = pd.concat(pd.read_csv(a) for a in arqs).dropna(subset=['grade_sab', 'nativa'])
    L = ['# Sensibilidade à resolução: cada referência na grade do SAB (0,1°) × na resolução nativa', '',
         'Diferença = nativa − grade do SAB, na média mensal de cada região (a mesma máscara de pixels entregues). '
         'Somas em % do valor; o resto na unidade da variável. Regra fixada antes de rodar: irrelevante se o '
         'percentil 95 de |diferença| ≤ 1/5 da tolerância das comparações (cabeçalho do script).', '',
         '| Fonte | Variável | Região | Meses | Mediana da diferença | P95 de \\|diferença\\| | Limite | Resultado |',
         '|---|---|---|---|---|---|---|---|']
    relevantes, ufs = [], []
    for (fonte, var, reg), g in df.groupby(['fonte', 'variavel', 'regiao']):
        tipo, lim = tol(var)
        d = (100 * (g.nativa / g.grade_sab - 1)).where(g.grade_sab.abs() > 1e-6) if tipo == '%' else g.nativa - g.grade_sab
        d = d.dropna()
        p95, med = d.abs().quantile(0.95), d.median()
        if lim is None:
            res = 'só correlação (unidade diferente)'
        elif p95 <= lim:
            res = '✅ irrelevante'
        else:
            res = '⚠️ relevante'
            relevantes.append(f'{fonte}/{var}/{reg}')
        un = '%' if tipo == '%' else ''
        if reg.startswith('UF '):
            ufs.append(res.startswith('✅'))
            continue
        L.append(f'| {fonte} | {var} | {reg} | {len(d)} | {med:+.3f}{un} | {p95:.3f}{un} | '
                 f'{"-" if lim is None else f"{lim}{un}"} | {res} |')
    L += ['', f'**Nos 27 estados** (fora da tabela; todos no CSV): {sum(ufs)} de {len(ufs)} combinações irrelevantes.']
    L += ['', '**Onde a resolução pesa:** ' + ('; '.join(relevantes) if relevantes else 'em nenhuma combinação.')]
    with open(os.path.join(SAIDA, 'RESULTADOS.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L[-3:]))


if __name__ == '__main__':
    main()
