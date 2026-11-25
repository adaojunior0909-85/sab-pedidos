# As 16 variáveis de 2026 (ERA5-Land calibrado pelo motor) estão certas? Dois testes, SÓ LEITURA no Earth Engine.
#
# PARTE A, O MÉTODO NUM ANO CONHECIDO: aplica a mesma rota ERA5 do motor V1.7 (processarDia_Rota1, a que fez os dias
#   de 2026) aos anos 2021-2025, que já têm o BR-DWGD, e compara mês a mês, por região, com o que o banco entrega
#   nesses anos. Nas 8 variáveis do BR-DWGD (chuva, Tmax, Tmin, UR, VPD, ETo, radiação, vento) mede o erro do método
#   contra a observação; nas outras 8 (ET real, transpiração, temperaturas do solo e da folha, umidade do solo e
#   escoamento, que vêm do ERA5 nos dois períodos) mede se 2026 continua o histórico sem degrau.
#   Mostra o erro de cada ano: se o "erro" de 2026 cair fora da faixa dos anos conhecidos, 2026 é atípico.
#   Obs.: as matrizes de calibração usam 1986-2025 (os anos do teste estão no treino); a K21 já mediu fora da amostra
#   (treino 1986-2015, teste 2016-2025) para UR e vento.
#
# PARTE B, 2026 CONTRA UMA REFERÊNCIA INDEPENDENTE PARA TODAS AS VARIÁVEIS: GLDAS-2.1 (NASA, modelo de superfície Noah
#   forçado por GDAS/NOAA, chuva GPCP e radiação AGRMET; nada do ECMWF). O GLDAS tem os seus próprios erros, então o
#   que conta é a MUDANÇA: a diferença SAB - GLDAS nos meses de 2026 contra a mesma diferença nos mesmos meses de
#   2022, 2023 e 2024 (a régua, quando o SAB é o BR-DWGD).
#   REGRA FIXADA ANTES DE RODAR (25/11/2026): uma variável/região é SUSPEITA em 2026 se a diferença de 2026 sair da
#   faixa [mínimo, máximo] dos três anos da régua por mais que a tolerância (TOL abaixo).
#
#     python pesquisa/validar_metodo_2026.py A     (retomável; TEMPO_MAX_MIN limita: sai com código 3 se faltar ano)
#     python pesquisa/validar_metodo_2026.py B
import glob
import hashlib
import os
import sys
import time
from datetime import date, timedelta

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ee  # noqa: E402
import validar_2026_independente as v  # noqa: E402  (inicia o Earth Engine; regiões e máscara de entrega)

sp = v.sp
SAIDA = os.path.join(AQUI, 'resultados_metodo_2026')
MOTOR = os.path.join(AQUI, 'motor', '05a_motor_sab_v1_7_SIMULACAO.py')
SHA_MOTOR = 'e84ebb1f480e18fd321340f9de7db3cf8a93edcd8cfca76c44912b205119cafb'
ANOS_A = range(2021, 2026)
REGUA_B = (2022, 2023, 2024)
SOMA = ['pr_mm', 'et_potencial', 'et_real', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm']
MEDIA = ['tmax_C', 'tmin_C', 'RH', 'vpd', 'rs', 'u2', 'tsolo_C', 'tfolha_C', 'soil_moisture_0_5cm_m3_m3',
         'soil_moisture_0_100cm_m3_m3']
VARS = SOMA + MEDIA
DO_BRDWGD = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'vpd', 'et_potencial', 'rs', 'u2']
NOME = {'pr_mm': 'Chuva', 'tmax_C': 'Tmax', 'tmin_C': 'Tmin', 'RH': 'Umidade relativa', 'vpd': 'Déficit de pressão de vapor',
        'et_potencial': 'ETo', 'rs': 'Radiação solar', 'u2': 'Vento', 'et_real': 'ET real', 'transpiracao_mm': 'Transpiração',
        'runoff_sup_mm': 'Escoamento superficial', 'runoff_sub_mm': 'Escoamento subsuperficial', 'tsolo_C': 'Temperatura do solo',
        'tfolha_C': 'Temperatura da folha', 'soil_moisture_0_5cm_m3_m3': 'Umidade do solo 0-5 cm',
        'soil_moisture_0_100cm_m3_m3': 'Umidade do solo 0-100 cm'}
# tolerância da regra da parte B: % nas somas; unidade da variável nas médias
TOL = {**{b: 5.0 for b in SOMA}, 'tmax_C': 0.5, 'tmin_C': 0.5, 'RH': 3.0, 'vpd': 0.1, 'rs': 0.5, 'u2': 0.2,
       'tsolo_C': 0.5, 'tfolha_C': 0.5, 'soil_moisture_0_5cm_m3_m3': 0.02, 'soil_moisture_0_100cm_m3_m3': 0.02}
UNID = {**{b: '%' for b in SOMA}, 'tmax_C': '°C', 'tmin_C': '°C', 'RH': 'p.p.', 'vpd': 'kPa', 'rs': 'MJ/m²/dia',
        'u2': 'm/s', 'tsolo_C': '°C', 'tfolha_C': '°C', 'soil_moisture_0_5cm_m3_m3': 'm³/m³',
        'soil_moisture_0_100cm_m3_m3': 'm³/m³'}
BRASIL = ee.Geometry.Rectangle([-74.0, -34.0, -34.0, 5.5], None, False)


def carregar_motor():
    """As seções 1 a 5 do motor V1.7 (configuração e funções), sem a orquestração. Nada é gravado."""
    texto = open(MOTOR, encoding='utf-8').read()
    sha = hashlib.sha256(texto.encode('utf-8')).hexdigest()
    if sha != SHA_MOTOR:
        raise SystemExit(f'A cópia do motor mudou (SHA {sha[:12]}); confira pesquisa/motor/LEIA.md')
    corte = texto.index('# 6. ORQUESTRAÇÃO')
    def _bloqueado(*a, **k):
        raise RuntimeError('teste só de leitura: escrita no Earth Engine bloqueada')
    ee.batch.Task.start = _bloqueado
    for nome in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'setAssetAcl', 'startProcessing', 'exportImage'):
        if hasattr(ee.data, nome):
            setattr(ee.data, nome, _bloqueado)
    ns = {'__name__': 'motor_v17'}
    exec(compile(texto[:texto.rindex('\n# ====', 0, corte)], MOTOR, 'exec'), ns)   # noqa: S102
    assert ns['SIMULAR'] is True
    return ns


def mensal(col, ini, fim):
    """Total (somas) ou média (o resto) do mês, nas 16 variáveis."""
    return ee.Image.cat([col.select(SOMA).sum(), col.select(MEDIA).mean()])


def reduzir(img, regs, bandas):
    r = img.select(bandas).updateMask(v.ENTREGUE).reduceRegions(
        collection=regs, reducer=ee.Reducer.mean(), crs=sp.CRS, crsTransform=sp.TRANSFORM, tileScale=16).getInfo()
    return {f['properties']['regiao']: f['properties'] for f in r['features']}


# ------------------------------------------------------------------ parte A
def parte_a():
    m = carregar_motor()
    regs = v.regioes()
    pasta = os.path.join(SAIDA, 'parte_a')
    os.makedirs(pasta, exist_ok=True)
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)
    for ano in ANOS_A:
        arq = os.path.join(pasta, f'{ano}.csv')
        if os.path.exists(arq):
            continue
        linhas = []
        for mes in range(1, 13):
            if time.time() > limite:
                print('Tempo desta vez acabou; a próxima retoma daqui.')
                raise SystemExit(3)
            d0 = date(ano, mes, 1)
            d1 = (d0 + timedelta(days=32)).replace(day=1)
            ini, fim = d0.isoformat(), d1.isoformat()
            dias = [(d0 + timedelta(days=k)).isoformat() for k in range((d1 - d0).days)]
            metodo = mensal(ee.ImageCollection([m['processarDia_Rota1'](d) for d in dias]), ini, fim)
            entregue = mensal(sp.colecao(BRASIL, ini, fim), ini, fim)
            par = ee.Image.cat([metodo.rename([f'm_{b}' for b in VARS]), entregue.rename([f'e_{b}' for b in VARS])])
            res = {}
            for tentativa, grupos in enumerate((1, 4, 8, 16)):
                try:
                    n = -(-len(VARS) // grupos)
                    for i in range(0, len(VARS), n):
                        bs = VARS[i:i + n]
                        for reg, p in reduzir(par, regs, [f'{x}_{b}' for b in bs for x in 'me']).items():
                            res.setdefault(reg, {}).update(p)
                    break
                except Exception as e:  # noqa: BLE001
                    print(f'   ⚠️ {ini}: {str(e)[:150]} | de novo em pedidos menores', flush=True)
                    time.sleep(20 * (tentativa + 1))
            else:
                raise RuntimeError(f'{ini}: não deu depois de 4 tentativas')
            for reg, p in res.items():
                for b in VARS:
                    linhas.append({'regiao': reg, 'ano': ano, 'mes': mes, 'variavel': b,
                                   'metodo_2026': p.get(f'm_{b}'), 'entregue': p.get(f'e_{b}')})
            print(f'   {ini} pronto', flush=True)
        pd.DataFrame(linhas).to_csv(arq, index=False)
    resumo_a(pasta)


def erro(g, b):
    if b in SOMA:
        return 100 * (g.metodo_2026.sum() / g.entregue.sum() - 1) if g.entregue.sum() else float('nan')
    return (g.metodo_2026 - g.entregue).mean()


def resumo_a(pasta):
    df = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(pasta, '*.csv'))))
    regioes = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil']
    L = ['# Parte A: o método de 2026 aplicado a 2021–2025 (anos com BR-DWGD)', '',
         'Erro do método = rota ERA5 do motor V1.7 menos o que o banco entrega no mesmo mês (somas: % do total; '
         'médias: diferença na unidade). Em cada célula: o erro dos 5 anos juntos e, entre colchetes, o menor e o maior '
         'erro de um ano só. **Nas 8 primeiras linhas a referência é a observação (BR-DWGD)**; nas outras, o próprio '
         'ERA5 do histórico (mede só a emenda).', '',
         '| Variável | Unid. | ' + ' | '.join(regioes) + ' |', '|---|---|' + '---|' * len(regioes)]
    for b in DO_BRDWGD + [x for x in VARS if x not in DO_BRDWGD]:
        cel = []
        for reg in regioes:
            g = df[(df.variavel == b) & (df.regiao == reg)].dropna()
            anos = [erro(x, b) for _, x in g.groupby('ano')]
            cel.append(f'{erro(g, b):+.2f} [{min(anos):+.1f} a {max(anos):+.1f}]' if anos else '-')
        L.append(f'| {NOME[b]} | {UNID[b]} | ' + ' | '.join(cel) + ' |')
    with open(os.path.join(SAIDA, 'RESULTADOS_A.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


# ------------------------------------------------------------------ parte B
GLDAS = ee.ImageCollection('NASA/GLDAS/V021/NOAH/G025/T3H')


def gldas_mes(ini, fim):
    g = GLDAS.filterDate(ini, fim)
    ndias = ee.Date(fim).difference(ee.Date(ini), 'day')
    s_mes = ndias.multiply(86400)

    def umid(i):
        t = i.select('Tair_f_inst').subtract(273.15)
        q, p = i.select('Qair_f_inst'), i.select('Psurf_f_inst')
        e = q.multiply(p).divide(q.multiply(0.378).add(0.622))
        es = t.multiply(17.67).divide(t.add(243.5)).exp().multiply(611.2)
        return ee.Image.cat([e.divide(es).multiply(100).min(100).rename('RH'), es.subtract(e).max(0).divide(1000).rename('vpd')])

    def dia(k):
        d = ee.Date(ini).advance(k, 'day')
        t = g.filterDate(d, d.advance(1, 'day')).select('Tair_f_inst')
        return ee.Image.cat([t.max().rename('tmax_C'), t.min().rename('tmin_C')]).subtract(273.15)

    tt = ee.ImageCollection(ee.List.sequence(0, ndias.subtract(1)).map(dia)).mean()
    w = 0.0864 / 2.45                                     # W/m² -> mm/dia
    return ee.Image.cat([
        g.select('Rainf_f_tavg').mean().multiply(s_mes).rename('pr_mm'),
        g.select('PotEvap_tavg').mean().multiply(w).multiply(ndias).rename('et_potencial'),
        g.select('Evap_tavg').mean().multiply(s_mes).rename('et_real'),
        g.select('Tveg_tavg').mean().multiply(w).multiply(ndias).rename('transpiracao_mm'),
        g.select('Qs_acc').sum().rename('runoff_sup_mm'),
        g.select('Qsb_acc').sum().rename('runoff_sub_mm'),
        tt.select('tmax_C'), tt.select('tmin_C'),
        g.map(umid).mean(),
        g.select('SWdown_f_tavg').mean().multiply(0.0864).rename('rs'),
        g.select('Wind_f_inst').mean().multiply(0.748).rename('u2'),
        g.select('SoilTMP0_10cm_inst').mean().subtract(273.15).rename('tsolo_C'),
        g.select('AvgSurfT_inst').mean().subtract(273.15).rename('tfolha_C'),
        g.select('SoilMoi0_10cm_inst').mean().divide(100).rename('soil_moisture_0_5cm_m3_m3'),
        g.select(['SoilMoi0_10cm_inst', 'SoilMoi10_40cm_inst', 'SoilMoi40_100cm_inst']).mean()
         .reduce(ee.Reducer.sum()).divide(1000).rename('soil_moisture_0_100cm_m3_m3'),
    ]).select(VARS)


def parte_b():
    os.makedirs(SAIDA, exist_ok=True)
    regs = v.regioes()
    fim_g = v.ultimo(GLDAS.filterDate('2026-01-01', '2027-01-01'))
    inv = ee.ImageCollection(sp.SAB).filterDate('2026-01-01', '2027-01-01')
    vers = dict(zip(inv.aggregate_array('system:index').getInfo(), inv.aggregate_array('versao').getInfo()))
    ult_era5 = max(k for k, x in vers.items() if x == 'provisoria_era5')[4:].replace('_', '-')
    meses = [mm for mm in range(1, 13) if (date(2026, mm, 1) + timedelta(days=32)).replace(day=1)
             <= min(date.fromisoformat(fim_g[:10]), date.fromisoformat(ult_era5)) + timedelta(days=1)]
    print(f'GLDAS até {fim_g}; SAB ERA5 até {ult_era5}; meses de 2026 comparados: {meses}', flush=True)
    linhas = []
    for ano in (2026, *REGUA_B):
        for mm in meses:
            ini = date(ano, mm, 1).isoformat()
            fim = (date(ano, mm, 1) + timedelta(days=32)).replace(day=1).isoformat()
            par = ee.Image.cat([mensal(sp.colecao(BRASIL, ini, fim), ini, fim).rename([f's_{b}' for b in VARS]),
                                gldas_mes(ini, fim).rename([f'g_{b}' for b in VARS])])
            res = {}
            for i in range(0, len(VARS), 4):
                for reg, p in reduzir(par, regs, [f'{x}_{b}' for b in VARS[i:i + 4] for x in 'sg']).items():
                    res.setdefault(reg, {}).update(p)
            for reg, p in res.items():
                for b in VARS:
                    linhas.append({'regiao': reg, 'ano': ano, 'mes': mm, 'variavel': b, 'sab': p.get(f's_{b}'),
                                   'gldas': p.get(f'g_{b}')})
            print(f'   {ini} pronto', flush=True)
    df = pd.DataFrame(linhas)
    df.to_csv(os.path.join(SAIDA, 'parte_b_gldas.csv'), index=False)
    resumo_b(df, meses, fim_g, ult_era5)


def resumo_b(df, meses, fim_g, ult_era5):
    regioes = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil']

    def dif(g, b):
        if b in SOMA:
            return 100 * (g.sab.sum() / g.gldas.sum() - 1) if g.gldas.sum() else float('nan')
        return (g.sab - g.gldas).mean()

    L = ['# Parte B: 2026 contra o GLDAS-2.1 (NASA), com 2022–2024 como régua', '',
         f'Meses {meses[0]} a {meses[-1]} de cada ano (GLDAS até {fim_g[:10]}; SAB ERA5 até {ult_era5}). Em cada célula: '
         'a diferença SAB − GLDAS em 2026 e, entre colchetes, a faixa da mesma diferença em 2022–2024 (quando o SAB '
         'é o BR-DWGD). ⚠️ = 2026 fora da faixa por mais que a tolerância (regra fixada antes de rodar).', '',
         '| Variável | Unid. | Tol. | ' + ' | '.join(regioes) + ' |', '|---|---|---|' + '---|' * len(regioes)]
    suspeitas = []
    for b in DO_BRDWGD + [x for x in VARS if x not in DO_BRDWGD]:
        cel = []
        for reg in regioes:
            g = df[(df.variavel == b) & (df.regiao == reg)].dropna()
            d26 = dif(g[g.ano == 2026], b)
            regua = [dif(g[g.ano == a], b) for a in REGUA_B]
            fora = d26 < min(regua) - TOL[b] or d26 > max(regua) + TOL[b]
            if fora:
                suspeitas.append(f'{NOME[b]} no {reg}')
            cel.append(f'{"⚠️ " if fora else ""}{d26:+.2f} [{min(regua):+.1f} a {max(regua):+.1f}]')
        L.append(f'| {NOME[b]} | {UNID[b]} | {TOL[b]} | ' + ' | '.join(cel) + ' |')
    L += ['', '**Suspeitas em 2026:** ' + ('; '.join(suspeitas) if suspeitas else 'nenhuma.')]
    with open(os.path.join(SAIDA, 'RESULTADOS_B.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    {'A': parte_a, 'B': parte_b}[(sys.argv[1:] or ['A'])[0].upper()]()
