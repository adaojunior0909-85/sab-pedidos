# Fase 2, leva 2 (protocolo pesquisa/PROTOCOLO_CORRECAO_FASE2.md, congelado no commit 9a12309, emenda 1 no 8b100c8; ANTES de
# rodar). SÓ LEITURA no Earth Engine. Métodos:
#   M2-R2 radiação por quantis regionais: os decis (10% a 90%) da radiação diária do ERA5 calibrado (a V1.7: fator da
#        média 1986..Y-1, teto 5, céu claro) e do BR-DWGD, por região e mês, nos 1.500 pixels, com os anos Y-5..Y-1; a
#        radiação do dia vai do decil do ERA5 ao do BR-DWGD (interpolação linear; fora dos decis extremos, desloca pela
#        diferença do extremo); depois, céu claro; ETo recalculada (FAO-56). Base: a V1.7.
#   M3-T1 janela de 10 anos: Tmax e Tmin (aditivo) e vento (multiplicativo, teto 5) calibrados com a média de Y-10..Y-1
#        no lugar da do asset (1986-2025); VPD e ETo recalculadas. A UR usa o EQM (quantis da SICSB_EQM): o T1 não se
#        aplica a ela (fixado no validar_fase2.py antes de rodar). Base: a V1.7.
# Regras: as do protocolo (M2: radiação no Brasil -0,2 MJ, ETo -1 p.p., nenhuma região piora > 0,1 MJ ou 0,5 p.p.,
#   r_anom da radiação não cai > 0,02; M3: por variável, |viés| no Brasil cai >= 0,1 °C / 0,02 kPa / 0,05 m/s, nenhuma
#   região piora mais que isso, r_anom não cai > 0,02).
#     python pesquisa/validar_fase2_leva2.py          (retomável; TEMPO_MAX_MIN)
#     python pesquisa/validar_fase2_leva2.py resumo
import glob
import math
import os
import sys
import time
from datetime import date, timedelta

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import validar_correcao_era5 as t  # noqa: E402
import validar_fase2 as f2  # noqa: E402  (linhas_de com a variável inteira; entregue; imagem regional)

FASE1 = os.path.join(AQUI, 'resultados_correcao_era5')
SAIDA = os.path.join(AQUI, 'resultados_fase2', 'leva2')
PIX = os.path.join(SAIDA, 'pixels_rs')
NIVEIS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
ANOS_PIX = range(2011, 2026)


# ============================================================ contas puras
def rso_fao(lat_graus, z, doy):
    """Radiação de céu claro (MJ/m²/dia), FAO-56 eq. 21 e 37 (a mesma conta do motor)."""
    lat = np.radians(np.asarray(lat_graus, float))
    J = np.asarray(doy, float)
    dr = 1 + 0.033 * np.cos(2 * np.pi * J / 365)
    d = 0.409 * np.sin(2 * np.pi * J / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(lat) * np.tan(d), -1, 1))
    ra = (24 * 60 / np.pi) * 0.0820 * dr * (ws * np.sin(lat) * np.sin(d) + np.cos(lat) * np.cos(d) * np.sin(ws))
    return (0.75 + 2e-5 * np.asarray(z, float)) * ra


def mapa_quantis(x, qx, qy):
    """Leva x dos quantis qx aos qy: linear entre eles; fora da faixa, desloca pela diferença do extremo."""
    x = np.asarray(x, float)
    xc = np.clip(x, qx[0], qx[-1])
    return np.interp(xc, qx, qy) + (x - xc)


def crescente(q):
    """Força os decis a crescer (empates viram degraus mínimos), como o interpolate do Earth Engine exige."""
    q = np.asarray(q, float).copy()
    for i in range(1, len(q)):
        if q[i] <= q[i - 1]:
            q[i] = q[i - 1] + 1e-4
    return q


# ============================================================ pixels (radiação)
def baixar_pixels(limite):
    """Radiação diária bruta do ERA5 (bilinear, 0 = vazio) e do BR-DWGD nos 1.500 pixels, 2011-2025; somas mensais
    (média de climatologia) de 1986-2025; altitude."""
    E = t.iniciar()
    ee, sp, m = E['ee'], E['sp'], E['m']
    os.makedirs(PIX, exist_ok=True)
    pontos = pd.read_csv(os.path.join(FASE1, 'pixels', 'pontos.csv'))
    proj = ee.Projection(sp.CRS, sp.TRANSFORM)
    feats = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([lo, la]), {'pid': int(p)})
                                  for p, lo, la in zip(pontos.pid, pontos.lon, pontos.lat)])
    arq_z = os.path.join(PIX, 'altitude.csv')
    if not os.path.exists(arq_z):
        r = t.gi(ee.Image('USGS/SRTMGL1_003').rename('z').sampleRegions(collection=feats, properties=['pid'],
                                                                          scale=90, geometries=False), 'altitude')
        pd.DataFrame([f['properties'] for f in r['features']]).to_csv(arq_z, index=False)
    for ano in range(t.ANO_INICIO_CLIMA, 2026):          # somas mensais (climatologia por janela)
        arq = os.path.join(PIX, f'somas_{ano}.csv.gz')
        if os.path.exists(arq):
            continue
        if time.time() > limite:
            raise SystemExit(3)
        ims = []
        for mes in range(1, 13):
            ini = date(ano, mes, 1).isoformat()
            fim = (date(ano, mes, 1) + timedelta(days=32)).replace(day=1).isoformat()
            era = ee.ImageCollection(t.ERA5_MENSAL).filterDate(ini, fim).map(t.era_mensal_soma).sum()
            br = m['colChuvaGeral'].filterDate(ini, fim).map(lambda i: t.br_limpo(i).select('Rs'))
            ims += [era.select('Rs_sum').rename(f's_era_{mes}'), era.select('Rs_count').rename(f'n_era_{mes}'),
                    br.sum().rename(f's_br_{mes}'), br.count().rename(f'n_br_{mes}')]
        r = t.gi(ee.Image.cat(ims).sampleRegions(collection=feats, properties=['pid'], projection=proj,
                                                 geometries=False, tileScale=16), f'somas Rs {ano}')
        linhas = [{'pid': q['pid'], 'ano': ano, 'mes': mes, 's_era': q.get(f's_era_{mes}'), 'n_era': q.get(f'n_era_{mes}'),
                   's_br': q.get(f's_br_{mes}'), 'n_br': q.get(f'n_br_{mes}')}
                  for q in (x['properties'] for x in r['features']) for mes in range(1, 13)]
        pd.DataFrame(linhas).to_csv(arq, index=False)
        print(f'   somas Rs {ano}', flush=True)
    for ano in ANOS_PIX:                                   # dias
        arq = os.path.join(PIX, f'dias_{ano}.csv.gz')
        if os.path.exists(arq):
            continue
        if time.time() > limite:
            raise SystemExit(3)
        partes = {'era': [], 'br': []}
        x0, y0, dx = sp.TRANSFORM[2], sp.TRANSFORM[5], sp.TRANSFORM[0]
        chave = {(int(math.floor((lo - x0) / dx + 1e-6)), int(math.floor((y0 - la) / dx + 1e-6))): int(p)
                 for p, lo, la in zip(pontos.pid, pontos.lon, pontos.lat)}
        for mes in range(1, 13):
            ini = date(ano, mes, 1).isoformat()
            fim = (date(ano, mes, 1) + timedelta(days=32)).replace(day=1).isoformat()
            cols = {'era': m['colecao_era5'].filterDate(ini, fim).map(lambda i: ee.Image(
                        i.select('surface_solar_radiation_downwards_sum').divide(1e6).rename('v')
                        .updateMask(i.select('surface_solar_radiation_downwards_sum').gt(0)).resample('bilinear')
                        .copyProperties(i, ['system:time_start']))),
                    'br': m['colChuvaGeral'].filterDate(ini, fim).map(lambda i: ee.Image(
                        t.br_limpo(i).select('Rs').rename('v').copyProperties(i, ['system:time_start'])))}
            for i in range(0, len(pontos), 500):
                sub = pontos.iloc[i:i + 500]
                geo = ee.Geometry.MultiPoint([[lo, la] for lo, la in zip(sub.lon, sub.lat)])
                for nome, col in cols.items():
                    r = t.gi(ee.ImageCollection(col).getRegion(geo, None, sp.CRS, sp.TRANSFORM), f'Rs {nome} {ano}-{mes:02d}')
                    d = pd.DataFrame(r[1:], columns=r[0])
                    ix = np.floor((d.longitude.astype(float) - x0) / dx + 1e-6).astype(int)
                    iy = np.floor((y0 - d.latitude.astype(float)) / dx + 1e-6).astype(int)
                    d['pid'] = [chave.get((a, b)) for a, b in zip(ix, iy)]
                    d['dia'] = pd.to_datetime(d['time'], unit='ms', utc=True).dt.strftime('%Y%m%d').astype(int)
                    partes[nome].append(d.dropna(subset=['pid'])[['pid', 'dia', 'v']].rename(columns={'v': nome}))
        era, br = pd.concat(partes['era']), pd.concat(partes['br'])
        era['pid'], br['pid'] = era.pid.astype(int), br.pid.astype(int)
        era.merge(br, on=['pid', 'dia'], how='outer').drop_duplicates(['pid', 'dia']).round(3).to_csv(arq, index=False)
        print(f'   Rs dias {ano}', flush=True)


def decis_rs():
    """{(Y, mes, regiao): (decis do ERA5 calibrado, decis do BR-DWGD)} com os anos Y-5..Y-1."""
    pontos = pd.read_csv(os.path.join(FASE1, 'pixels', 'pontos.csv')).set_index('pid')
    z = pd.read_csv(os.path.join(PIX, 'altitude.csv')).set_index('pid').z
    somas = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(PIX, 'somas_*.csv.gz'))))
    dias = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(PIX, 'dias_*.csv.gz'))))
    dias['ano'], dias['mes'] = dias.dia // 10000, dias.dia // 100 % 100
    doy = pd.to_datetime(dias.dia.astype(str), format='%Y%m%d').dt.dayofyear
    dias['rso'] = rso_fao(dias.pid.map(pontos.lat), dias.pid.map(z).fillna(0), doy)
    dias['regiao'] = dias.pid.map(pontos.regiao)
    out = {}
    for Y in t.ANOS_TESTE:
        cl = t.clima_pixels(somas, *t.janela('C0', Y))
        x = dias[(dias.ano >= Y - 5) & (dias.ano < Y)]
        cc = cl.reindex(list(zip(x.pid, x.mes)))
        c0 = np.minimum(np.maximum(x.era.values * t.fator(cc.m_br.values, cc.m_era.values), 0), x.rso.values)
        x = x.assign(c0=c0)
        for (mes, r), g in x.groupby(['mes', 'regiao']):
            a, b = g.c0.dropna().values, g.br.dropna().values
            if len(a) > 50 and len(b) > 50:
                out[(Y, int(mes), r)] = (crescente(np.quantile(a, NIVEIS)), crescente(np.quantile(b, NIVEIS)))
    return out


# ============================================================ Earth Engine
def mapa_ee(rs, decis, Y, mes):
    """R2 no Earth Engine: cada região com os seus decis; fora das 5 regiões, sem mudança."""
    E = t.iniciar()
    ee = E['ee']
    idx = E['regs5'].map(lambda f: f.set('idx', ee.Number(ee.List(t.REGIOES5).indexOf(f.get('regiao'))).add(1)))
    cod = ee.Image.constant(0).paint(idx, 'idx').toInt()
    out = rs
    for k, r in enumerate(t.REGIOES5, start=1):
        if (Y, mes, r) not in decis:
            continue
        qx, qy = decis[(Y, mes, r)]
        xc = rs.clamp(float(qx[0]), float(qx[-1]))
        img = xc.interpolate([float(v) for v in qx], [float(v) for v in qy], 'extrapolate').add(rs.subtract(xc))
        out = out.where(cod.eq(k), img)
    return out


def clima_temp(mes, Y):
    """Média de Y-10..Y-1 (mês do ano) da Tmax, Tmin e vento do BR-DWGD e do ERA5 bruto (receita do O2)."""
    E = t.iniciar()
    ee, m = E['ee'], E['m']
    f = ee.Filter.calendarRange(mes, mes, 'month')
    ini, fim = f'{Y - 10}-01-01', f'{Y}-01-01'

    def br(i):
        k = i.select('pr').gt(-32768)
        return ee.Image.cat([i.select('Tmax').updateMask(k).multiply(0.00106815).add(15.0).rename('Tmax'),
                             i.select('Tmin').updateMask(k).multiply(0.00106815).add(15.0).rename('Tmin'),
                             i.select('u2').updateMask(k).multiply(0.05905512).add(-0.059055).rename('u2')])

    def era(i):
        return ee.Image.cat([i.select('temperature_2m_max').subtract(273.15).resample('bilinear').rename('Tmax'),
                             i.select('temperature_2m_min').subtract(273.15).resample('bilinear').rename('Tmin'),
                             i.select('u_component_of_wind_10m').hypot(i.select('v_component_of_wind_10m'))
                             .multiply(0.748).resample('bilinear').rename('u2')])
    b = m['colChuvaGeral'].filter(f).filterDate(ini, fim).map(br).mean()
    e = m['colecao_era5'].filter(f).filterDate(ini, fim).map(era).mean()
    return b, e


def dia(d, cl, decis, Y, mes, ct):
    E = t.iniciar()
    ee, m = E['ee'], E['m']
    c = m['_componentes_era5'](d)
    era = ee.Image(m['colecao_era5'].filterDate(ee.Date(d), ee.Date(d).advance(1, 'day')).first())
    rs_cru = era.select('surface_solar_radiation_downwards_sum').divide(1e6)
    rs_raw = rs_cru.updateMask(rs_cru.gt(0)).resample('bilinear')
    rs0 = m['limitar_rs'](m['calib_multiplicativa'](rs_raw, cl.select('Rs_m_br'), cl.select('Rs_m_era')).max(0), d)
    rs2 = m['limitar_rs'](mapa_ee(rs0, decis, Y, mes).max(0), d)

    def eto(tx, tn, rh, u, rs):
        return m['eto_penman_monteith'](tx, tn, rh, u, rs, d)
    b_br, b_era = ct
    tx_raw = era.select('temperature_2m_max').subtract(273.15).resample('bilinear')
    tn_raw = era.select('temperature_2m_min').subtract(273.15).resample('bilinear')
    u_raw = era.select('u_component_of_wind_10m').hypot(era.select('v_component_of_wind_10m')).multiply(0.748).resample('bilinear')
    tx1 = m['calib_aditiva'](tx_raw, b_br.select('Tmax'), b_era.select('Tmax'))
    tn1 = m['calib_aditiva'](tn_raw, b_br.select('Tmin'), b_era.select('Tmin'))
    u1 = m['calib_multiplicativa'](u_raw, b_br.select('u2'), b_era.select('u2')).max(0)
    vpd1, _ = m['vpd_e_ea'](tx1, tn1, c['RH'])
    return ee.Image.cat([
        rs0.rename('C0_rs'), eto(c['tmax_C'], c['tmin_C'], c['RH'], c['u2'], rs0).rename('C0_eto'),
        rs2.rename('R2_rs'), eto(c['tmax_C'], c['tmin_C'], c['RH'], c['u2'], rs2).rename('R2_eto'),
        c['tmax_C'].rename('C0_tmax_C'), c['tmin_C'].rename('C0_tmin_C'), c['u2'].rename('C0_u2'), c['vpd'].rename('C0_vpd'),
        tx1.rename('T1_tmax_C'), tn1.rename('T1_tmin_C'), u1.rename('T1_u2'), vpd1.rename('T1_vpd'),
        eto(tx1, tn1, c['RH'], u1, rs0).rename('T1_eto')]).updateMask(m['MASCARA_SAB'])


def regional_mes(Y, mes, decis):
    E = t.iniciar()
    ee = E['ee']
    cl = t.climatologias(mes, Y, metodos=('C0',))['C0']
    ct = clima_temp(mes, Y)
    dias = [date(Y, mes, k).isoformat() for k in range(1, t.dias_no_mes(Y, mes) + 1)]
    col = ee.ImageCollection([dia(d, cl, decis, Y, mes, ct) for d in dias])
    soma = ['C0_eto', 'R2_eto', 'T1_eto']
    media = ['C0_rs', 'R2_rs', 'C0_tmax_C', 'C0_tmin_C', 'C0_u2', 'C0_vpd', 'T1_tmax_C', 'T1_tmin_C', 'T1_u2', 'T1_vpd']
    en = f2.entregue(Y, mes, extremos=True)
    par = ee.Image.cat([col.select(soma).sum(), col.select(media).mean(),
                        en.select(['BR_rs', 'BR_eto', 'BR_tmax_C', 'BR_tmin_C', 'BR_u2', 'BR_vpd'])])
    nomes = par.bandNames().getInfo()
    return f2.linhas_de(t.reduzir(par, nomes, f'leva 2 {Y}-{mes:02d}'), Y, Y, mes)


# ============================================================ resumo
def resumo():
    arqs = sorted(glob.glob(os.path.join(SAIDA, 'regional', '*.csv')))
    if not arqs:
        print('Nada baixado ainda.')
        return
    alvo = pd.concat(pd.read_csv(a) for a in arqs)
    completos = sorted(Y for Y, g in alvo.groupby('ano_alvo') if g.mes.nunique() == 12)
    alvo = alvo[alvo.ano_alvo.isin(completos)]
    final = len(completos) == len(t.ANOS_TESTE)
    s_ = {True: '✅', False: '❌'}
    L = ['# Fase 2, leva 2: M2-R2 (quantis da radiação) e M3-T1 (janela de 10 anos)', '',
         'Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (congelado antes de rodar). Só leitura. Nada é gravado sem '
         'autorização do responsável.', '']
    if not final:
        L += [f'**Parcial:** {len(completos)} de {len(t.ANOS_TESTE)} anos ({completos}).', '']
    if completos:
        def vies(k, v, r):
            a, b = t.serie(alvo, k, v, r), t.serie(alvo, 'BR', v, r)
            i = a.index.intersection(b.index)
            return t.vies_pct(a.loc[i], b.loc[i]) if v == 'eto' else float((a.loc[i] - b.loc[i]).mean())

        def r_an(k, v, r):
            return t.r_anomalias(pd.DataFrame({'metodo': t.serie(alvo, k, v, r), 'ref': t.serie(alvo, 'BR', v, r)}).reset_index())
        qrs = abs(vies('C0', 'rs', 'Brasil')) - abs(vies('R2', 'rs', 'Brasil'))
        qet = abs(vies('C0', 'eto', 'Brasil')) - abs(vies('R2', 'eto', 'Brasil'))
        prs = max(abs(vies('R2', 'rs', r)) - abs(vies('C0', 'rs', r)) for r in t.REGIOES5)
        pet = max(abs(vies('R2', 'eto', r)) - abs(vies('C0', 'eto', r)) for r in t.REGIOES5)
        qr = max(r_an('C0', 'rs', r) - r_an('R2', 'rs', r) for r in t.REGIOES5)
        ok = qrs >= 0.2 - t.EPS and qet >= 1.0 - t.EPS and prs <= 0.1 + t.EPS and pet <= 0.5 + t.EPS and qr <= 0.02 + t.EPS
        L += ['## M2-R2. Radiação e ETo', '', '| Região | V1.7: radiação / ETo | R2: radiação / ETo |', '|---|---|---|']
        for r in t.REGIOES:
            L.append(f"| {r} | {vies('C0', 'rs', r):+.2f} MJ / {vies('C0', 'eto', r):+.1f}% | "
                     f"{vies('R2', 'rs', r):+.2f} MJ / {vies('R2', 'eto', r):+.1f}% |")
        L += ['', f'R2: radiação no Brasil {qrs:+.2f} MJ (≥ 0,2) · ETo {qet:+.2f} p.p. (≥ 1) · pior região {prs:+.2f} MJ / '
              f'{pet:+.2f} p.p. · r_anom {qr:+.3f} → **{s_[ok]} {"PASSA (gravação só com autorização)" if ok else "não passa; a V1.7 fica"}'
              f'{"" if final else " (parcial)"}**', '',
              '## M3-T1. Tmax, Tmin, VPD e vento', '', '| Variável | V1.7: viés Brasil | T1: viés Brasil | Pior região (piora) | r_anom (maior queda) | Passa? |',
              '|---|---|---|---|---|---|']
        for v in ('tmax_C', 'tmin_C', 'vpd', 'u2'):
            qb = abs(vies('C0', v, 'Brasil')) - abs(vies('T1', v, 'Brasil'))
            piora = max(abs(vies('T1', v, r)) - abs(vies('C0', v, r)) for r in t.REGIOES5)
            quedas = max(r_an('C0', v, r) - r_an('T1', v, r) for r in t.REGIOES5)
            ok3 = qb >= f2.LIMIAR_M3[v] - t.EPS and piora <= f2.LIMIAR_M3[v] + t.EPS and quedas <= 0.02 + t.EPS
            L.append(f"| {v} | {vies('C0', v, 'Brasil'):+.3f} | {vies('T1', v, 'Brasil'):+.3f} | {piora:+.3f} | {quedas:+.3f} | {s_[ok3]} |")
    os.makedirs(os.path.dirname(os.path.join(SAIDA, 'x')), exist_ok=True)
    with open(os.path.join(AQUI, 'resultados_fase2', 'RESULTADOS_LEVA2.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


def main():
    os.makedirs(os.path.join(SAIDA, 'regional'), exist_ok=True)
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)
    baixar_pixels(limite)
    decis = decis_rs()
    pd.DataFrame([{'ano_alvo': k[0], 'mes': k[1], 'regiao': k[2], **{f'era_q{int(100 * n)}': a[i] for i, n in enumerate(NIVEIS)},
                   **{f'br_q{int(100 * n)}': b[i] for i, n in enumerate(NIVEIS)}} for k, (a, b) in decis.items()]) \
        .to_csv(os.path.join(SAIDA, 'decis_rs.csv'), index=False)
    for Y in t.ANOS_TESTE:
        for mes in range(1, 13):
            arq = os.path.join(SAIDA, 'regional', f'{Y}_{mes:02d}.csv')
            if os.path.exists(arq):
                continue
            if time.time() > limite:
                print('Tempo desta vez acabou; a próxima retoma daqui.', flush=True)
                resumo()
                raise SystemExit(3)
            t0 = time.time()
            pd.DataFrame(regional_mes(Y, mes, decis)).to_csv(arq, index=False)
            print(f'   leva 2 {Y}-{mes:02d} pronto em {(time.time() - t0) / 60:.1f} min', flush=True)
    resumo()


if __name__ == '__main__':
    resumo() if (sys.argv[1:] or [''])[0] == 'resumo' else main()
