# Fase 2, leva 1 (protocolo pesquisa/PROTOCOLO_CORRECAO_FASE2.md, congelado no commit 9a12309 ANTES de rodar). SÓ LEITURA
# no Earth Engine (escrita bloqueada pelo carregar_motor). Métodos desta leva:
#   M1 chuva:   C3 (a V1.8, a base), C3G (garoa + C3), C3RG (garoa + C3 só onde o viés é consistente)
#   M2 radiação: R1 (razão multiplicativa regional dos 5 anos anteriores, limitada a [0,85; 1,15], depois céu claro);
#               a ETo recalculada (FAO-56) com a radiação corrigida. Base: a V1.7 (C0).
#   M3 Tmax, Tmin, UR, vento: T2 (ajuste regional dos 5 anos anteriores: aditivo na Tmax, Tmin e UR; no vento,
#               multiplicativo limitado a [0,9; 1,1]); VPD e ETo recalculadas. Base: a V1.7.
#   Ficam para a leva 2 (precisam da radiação e das temperaturas diárias dos 1.500 pixels): R2 (quantis da radiação) e
#   T1 (janela de 10 anos). Detalhe fixado aqui ANTES de rodar: a UR usa o EQM (quantis da SICSB_EQM), então o T1 não se
#   aplica a ela; a UR entra só no T2.
# Garoa (C3G, C3RG): o limiar de cada região, mês e ano-alvo Y vem dos 1.500 pixels (dias de Y-5 a Y-1; o ERA5 calibrado
#   com a climatologia de 1986 a Y-1): o menor t >= 1 mm com fração de dias >= t do ERA5 = fração de dias >= 1 mm do
#   BR-DWGD (se o ERA5 já não passa do BR-DWGD, t = 1). Dia abaixo de t vira 0; fora das 5 regiões, sem corte. A razão do
#   C3 é refeita com o ERA5 já sem a garoa. C3RG: essa razão só onde é consistente (|razão-1| >= 0,05 e >= 4 dos 5 anos do
#   mesmo lado de 1), como o C3R do M1.
# Regras: as do protocolo (M1, M2, M3), aplicadas no resumo.
#     python pesquisa/validar_fase2.py          (retomável; TEMPO_MAX_MIN limita: sai com código 3 se faltar)
#     python pesquisa/validar_fase2.py resumo
import glob
import os
import sys
import time
from datetime import date

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import validar_correcao_era5 as t  # noqa: E402

FASE1 = os.path.join(AQUI, 'resultados_correcao_era5')
SAIDA = os.path.join(AQUI, 'resultados_fase2')
ANOS_DIAS_EXTRA = list(range(2011, 2016))          # dias dos pixels que faltam para os limiares de 2016-2020
LIMITES_RS = (0.85, 1.15)
LIMITES_VENTO = (0.9, 1.1)
VARS_T = ['tmax_C', 'tmin_C', 'RH', 'u2']
# regras do protocolo
PIORA_MEDIANA, QUEDA_FRACAO, MELHORA_PIOR, QUEDA_R, CRESCE_EXT = 0.5, 0.20, 2.0, 0.02, 0.05
QUEDA_RS_MJ, QUEDA_ETO_PP, PIORA_RS_MJ, PIORA_ETO_PP = 0.2, 1.0, 0.1, 0.5
LIMIAR_M3 = {'tmax_C': 0.1, 'tmin_C': 0.1, 'RH': 0.5, 'vpd': 0.02, 'u2': 0.05}


# ============================================================ contas puras
def limiar_garoa(c0, br, chuva_dia=t.CHUVA_DIA):
    """Menor t >= 1 mm com fração(c0 >= t) = fração(br >= 1 mm); t = 1 se o c0 já não chove mais vezes."""
    c0, br = np.asarray(c0, float), np.asarray(br, float)
    ok = np.isfinite(c0) & np.isfinite(br)
    c0, br = c0[ok], br[ok]
    if len(c0) == 0:
        return chuva_dia
    f_br = (br >= chuva_dia).mean()
    if (c0 >= chuva_dia).mean() <= f_br:
        return chuva_dia
    pos = np.sort(c0[c0 >= chuva_dia])[::-1]
    k = int(round(f_br * len(c0)))
    return float(pos[k - 1]) if k > 0 else float(pos[0]) + 1e-6


def consistente(razoes_ano, razao, limiar=0.05, minimo=4):
    if abs(razao - 1) < limiar:
        return False
    lado = np.sign(razao - 1)
    return sum(1 for r in razoes_ano if np.isfinite(r) and np.sign(r - 1) == lado) >= minimo


def limiares(agregados, dias, pontos):
    """{(Y, mes, regiao): limiar da garoa}, nos 1.500 pixels, com os dias de Y-5 a Y-1 calibrados pela climatologia
    de 1986 a Y-1 (o C0 do ano-alvo Y)."""
    pm = pontos.set_index('pid')
    d = dias.copy()
    d['ano'], d['mes'] = d.dia // 10000, d.dia // 100 % 100
    d['regiao'] = d.pid.map(pm['regiao'])
    teto = pm[[f'prmax_{m:02d}' for m in range(1, 13)]].to_numpy(float)
    pos = pd.Index(pm.index).get_indexer(d.pid)
    prmax = teto[pos, d.mes.to_numpy() - 1]
    out = {}
    for Y in t.ANOS_TESTE:
        sel = (d.ano >= Y - t.ANOS_C3) & (d.ano < Y)
        x = d[sel]
        cc = t.clima_pixels(agregados, *t.janela('C0', Y)).reindex(list(zip(x.pid, x.mes)))
        c0 = t.chuva_corrigida(x.era.values, t.fator(cc.m_br.values, cc.m_era.values), prmax[sel.values])
        x = x.assign(c0=c0)
        for (mes, r), g in x.groupby(['mes', 'regiao']):
            out[(Y, int(mes), r)] = limiar_garoa(g.c0.values, g.br.values)
    return out


# ============================================================ Earth Engine
def imagem(valores, padrao):
    return t.imagem_regional({r: float(valores.get(r, padrao)) for r in t.REGIOES5}, padrao)


def dia(d, cl, eqm, lim_img=None, aj=None, so_lookback=False):
    """Um dia: chuva (C0, sem garoa), radiação, temperaturas, UR, vento da V1.7, e os métodos da leva 1."""
    E = t.iniciar()
    ee, m = E['ee'], E['m']
    c = m['_componentes_era5'](d)
    era = ee.Image(m['colecao_era5'].filterDate(ee.Date(d), ee.Date(d).advance(1, 'day')).first())
    pr_raw = era.select('total_precipitation_sum').multiply(1000).max(0)
    rs_cru = era.select('surface_solar_radiation_downwards_sum').divide(1e6)
    rs_raw = rs_cru.updateMask(rs_cru.gt(0)).resample('bilinear')
    pr0 = m['teto_chuva'](m['calib_multiplicativa'](pr_raw, cl.select('pr_m_br'), cl.select('pr_m_era')).max(0), pr_raw, eqm)
    rs0 = m['limitar_rs'](m['calib_multiplicativa'](rs_raw, cl.select('Rs_m_br'), cl.select('Rs_m_era')).max(0), d)
    prg = pr0.where(pr0.lt(lim_img), 0)
    b = [pr0.rename('C0_pr'), prg.rename('G_pr'), rs0.rename('C0_rs')] + [c[v].rename(f'C0_{v}') for v in VARS_T]
    if not so_lookback:
        def eto(tx, tn, rh, u, rs):
            return m['eto_penman_monteith'](tx, tn, rh, u, rs, d)
        b.append(eto(c['tmax_C'], c['tmin_C'], c['RH'], c['u2'], rs0).rename('C0_eto'))
        b.append(c['vpd'].rename('C0_vpd'))
        b += [pr0.multiply(aj['r_c3']).rename('C3_pr'), prg.multiply(aj['r_g']).rename('C3G_pr'),
              prg.multiply(aj['r_rg']).rename('C3RG_pr')]
        rs1 = m['limitar_rs'](rs0.multiply(aj['f_rs']), d)
        b += [rs1.rename('R1_rs'), eto(c['tmax_C'], c['tmin_C'], c['RH'], c['u2'], rs1).rename('R1_eto')]
        tx2, tn2 = c['tmax_C'].add(aj['d_tmax_C']), c['tmin_C'].add(aj['d_tmin_C'])
        rh2, u22 = c['RH'].add(aj['d_RH']).clamp(0, 100), c['u2'].multiply(aj['f_u2'])
        vpd2, _ = m['vpd_e_ea'](tx2, tn2, rh2)
        b += [tx2.rename('T2_tmax_C'), tn2.rename('T2_tmin_C'), rh2.rename('T2_RH'), u22.rename('T2_u2'),
              vpd2.rename('T2_vpd'), eto(tx2, tn2, rh2, u22, rs0).rename('T2_eto')]
    return ee.Image.cat(b).updateMask(m['MASCARA_SAB'])


SOMA = ('pr', 'eto')


def mes_img(ano, mes, cl, lim_img, aj=None, so_lookback=False):
    E = t.iniciar()
    ee = E['ee']
    dias = [date(ano, mes, k).isoformat() for k in range(1, t.dias_no_mes(ano, mes) + 1)]
    col = ee.ImageCollection([dia(d, cl, t.E_eqm(mes), lim_img, aj, so_lookback) for d in dias])
    nomes = col.first().bandNames().getInfo()
    soma = [n for n in nomes if n.endswith('_pr') or n.endswith('_eto')]
    media = [n for n in nomes if n not in soma]
    im = [col.select(soma).sum(), col.select(media).mean()]
    if not so_lookback:
        prs = [n for n in soma if n.endswith('_pr')]
        im.append(col.select(prs).map(lambda i: ee.Image(i).gte(t.CHUVA_DIA)).sum()
                  .rename([n.replace('_pr', '_wet') for n in prs]))
        im.append(col.select(prs).max().rename([n.replace('_pr', '_rx') for n in prs]))
    return ee.Image.cat(im)


def entregue(ano, mes, extremos):
    E = t.iniciar()
    ee = E['ee']
    ini = date(ano, mes, 1).isoformat()
    fim = date(ano + (mes == 12), mes % 12 + 1, 1).isoformat()
    col = E['sp'].colecao(E['vm'].BRASIL, ini, fim)
    pr = col.select('pr_mm')
    im = [pr.sum().rename('BR_pr'), col.select('rs').mean().rename('BR_rs')] + \
         [col.select(v).mean().rename(f'BR_{v}') for v in VARS_T]
    if extremos:
        im += [col.select('et_potencial').sum().rename('BR_eto'), col.select('vpd').mean().rename('BR_vpd'),
               pr.map(lambda i: ee.Image(i).gte(t.CHUVA_DIA)).sum().rename('BR_wet'), pr.count().rename('BR_n'),
               pr.max().rename('BR_rx')]
    return ee.Image.cat(im)


def ajustes(lin_l, lim):
    """Razões e diferenças regionais dos 5 anos anteriores (a partir das linhas do pedido L)."""
    d = pd.DataFrame(lin_l)
    aj = {k: {} for k in ('r_c3', 'r_g', 'r_rg', 'f_rs', 'd_tmax_C', 'd_tmin_C', 'd_RH', 'f_u2')}
    for r in t.REGIOES5:
        g = d[d.regiao == r]
        s = lambda met, var: g[(g.metodo == met) & (g.variavel == var)].set_index('ano').valor
        br_pr, c0_pr, g_pr = s('BR', 'pr'), s('C0', 'pr'), s('G', 'pr')
        aj['r_c3'][r] = t.razao_c3(br_pr, c0_pr)
        rg = t.razao_c3(br_pr, g_pr)
        aj['r_g'][r] = rg
        anos = br_pr.index.intersection(g_pr.index)
        aj['r_rg'][r] = rg if consistente([br_pr[a] / g_pr[a] if g_pr[a] > 0 else np.nan for a in anos], rg) else 1.0
        i = s('BR', 'rs').index.intersection(s('C0', 'rs').index)
        f = float(s('BR', 'rs').loc[i].mean() / s('C0', 'rs').loc[i].mean()) if len(i) else 1.0
        aj['f_rs'][r] = min(max(f, LIMITES_RS[0]), LIMITES_RS[1])
        for v in ('tmax_C', 'tmin_C', 'RH'):
            i = s('BR', v).index.intersection(s('C0', v).index)
            aj[f'd_{v}'][r] = float((s('BR', v).loc[i] - s('C0', v).loc[i]).mean()) if len(i) else 0.0
        i = s('BR', 'u2').index.intersection(s('C0', 'u2').index)
        fu = float(s('BR', 'u2').loc[i].mean() / s('C0', 'u2').loc[i].mean()) if len(i) else 1.0
        aj['f_u2'][r] = min(max(fu, LIMITES_VENTO[0]), LIMITES_VENTO[1])
    return aj


def regional_mes(Y, mes, lim):
    E = t.iniciar()
    ee = E['ee']
    cl = t.climatologias(mes, Y, metodos=('C0',))['C0']
    lim_img = imagem({r: lim[(Y, mes, r)] for r in t.REGIOES5}, 0.0)
    imgs, bandas = [], []
    for a in range(Y - t.ANOS_C3, Y):
        par = ee.Image.cat([mes_img(a, mes, cl, lim_img, so_lookback=True), entregue(a, mes, extremos=False)])
        nomes = par.bandNames().getInfo()
        imgs.append(par.rename([f'a{a}_{n}' for n in nomes]))
        bandas += [f'a{a}_{n}' for n in nomes]
    lin_l = t.linhas_de(t.reduzir(ee.Image.cat(imgs), bandas, f'{Y}-{mes:02d} (anos anteriores)'), Y, None, mes,
                        prefixo_ano=True)
    aj = ajustes(lin_l, lim)
    padrao = {'r_c3': 1.0, 'r_g': 1.0, 'r_rg': 1.0, 'f_rs': 1.0, 'd_tmax_C': 0.0, 'd_tmin_C': 0.0, 'd_RH': 0.0, 'f_u2': 1.0}
    aj_img = {k: imagem(v, padrao[k]) for k, v in aj.items()}
    mm = mes_img(Y, mes, cl, lim_img, aj_img)
    en = entregue(Y, mes, extremos=True)
    ks = ['C0', 'C3', 'C3G', 'C3RG']
    drx = [mm.select(f'{k}_rx').subtract(en.select('BR_rx')).abs().rename(f'{k}_drx') for k in ks]
    par = ee.Image.cat([mm, en] + drx)
    nomes = par.bandNames().getInfo()
    lin_t = t.linhas_de(t.reduzir(par, nomes, f'{Y}-{mes:02d} (ano-alvo)'), Y, Y, mes)
    return lin_l + lin_t, aj


def linhas_de(res, Y, ano, mes, prefixo_ano=False):
    """Como t.linhas_de, mas a variável é tudo depois do método (tmax_C, ...)."""
    out = []
    for reg, p in res.items():
        for chave, valor in p.items():
            if chave == 'regiao' or valor is None:
                continue
            partes = chave.split('_')
            if prefixo_ano:
                if not partes[0].startswith('a'):
                    continue
                ano_l, partes = int(partes[0][1:]), partes[1:]
            else:
                ano_l = ano
            out.append({'ano_alvo': Y, 'ano': ano_l, 'mes': mes, 'regiao': reg, 'metodo': partes[0],
                        'variavel': '_'.join(partes[1:]), 'valor': valor})
    return out


t.linhas_de = linhas_de          # a variável completa (tmax_C, tmin_C) nas linhas


# ============================================================ resumo
def resumo():
    arqs = sorted(glob.glob(os.path.join(SAIDA, 'regional', '*.csv')))
    if not arqs:
        print('Nada baixado ainda.')
        return
    df = pd.concat(pd.read_csv(a) for a in arqs)
    alvo = df[df.ano == df.ano_alvo]
    completos = sorted(Y for Y, g in alvo.groupby('ano_alvo') if g.mes.nunique() == 12)
    alvo = alvo[alvo.ano_alvo.isin(completos)]
    s_ = {True: '✅', False: '❌'}
    L = ['# Fase 2, leva 1: M1 (garoa), M2-R1 (radiação) e M3-T2 (temperaturas, UR, vento)', '',
         'Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (congelado no commit 9a12309 antes de rodar). Só leitura no '
         'Earth Engine. Nada é gravado: um método que passa vai ao responsável, que autoriza (ou não) a gravação.', '']
    if len(completos) < len(t.ANOS_TESTE):
        L += [f'**Parcial:** {len(completos)} de {len(t.ANOS_TESTE)} anos de teste ({completos}). A decisão só sai com os 10.', '']
    if not completos:
        open(os.path.join(SAIDA, 'RESULTADOS_LEVA1.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        return
    t.METODOS = ['C0', 'C3', 'C3G', 'C3RG']
    mc, mx = t.metricas_chuva(alvo), t.metricas_extremos(alvo)
    soma = lambda m: sum(abs(mx[m][r]['fracao'] - mx['BR'][r]['fracao']) for r in t.REGIOES5)
    L += ['## M1. Chuva (base: C3, a V1.8)', '',
          '| Método | Mediana do |viés anual| (5 regiões) | Pior região | Dias de chuva: afastamento somado (p.p.) | r_anom mínimo |',
          '|---|---|---|---|---|']
    for k in t.METODOS:
        pior = max(t.REGIOES5, key=lambda r: mc[k]['mediana_regiao'][r])
        L.append(f"| {k} | {mc[k]['mediana5']:.2f}% | {pior} {mc[k]['mediana_regiao'][pior]:.1f}% | "
                 f"{100 * soma(k):.2f} | {min(mc[k]['r_anom'][r] for r in t.REGIOES5):.3f} |")
    passam = []
    final = len(completos) == len(t.ANOS_TESTE)
    pix_ok = all(os.path.exists(os.path.join(FASE1, 'pixels', f'dias_{a}.csv.gz')) for a in t.ANOS_TESTE)
    mp = None
    if final and pix_ok:
        mp = p99_pixels(df)
    for k in ('C3G', 'C3RG'):
        c3, mk = mc['C3'], mc[k]
        c1 = mk['mediana5'] - c3['mediana5'] <= PIORA_MEDIANA + t.EPS
        queda = 1 - soma(k) / soma('C3') if soma('C3') else 0.0
        rp = max(t.REGIOES5, key=lambda r: c3['mediana_regiao'][r])
        c2 = queda >= QUEDA_FRACAO - t.EPS or c3['mediana_regiao'][rp] - mk['mediana_regiao'][rp] >= MELHORA_PIOR - t.EPS
        c3_ = all(c3['r_anom'][r] - mk['r_anom'][r] <= QUEDA_R + t.EPS for r in t.REGIOES5)
        rx = all(mx[k][r]['erro_rx'] <= (1 + CRESCE_EXT) * mx['C3'][r]['erro_rx'] + t.EPS for r in t.REGIOES5)
        p99 = mp is not None and mp[k]['erro_p99'] <= (1 + CRESCE_EXT) * mp['C3']['erro_p99'] + t.EPS
        ok = c1 and c2 and c3_ and rx and p99
        if ok:
            passam.append(k)
        txt_p99 = f"{100 * mp[k]['erro_p99']:.1f}% (C3 {100 * mp['C3']['erro_p99']:.1f}%)" if mp else 'pendente'
        L.append(f"\n- **{k}**: 1 {s_[c1]} ({mk['mediana5'] - c3['mediana5']:+.2f} p.p.) · 2 {s_[c2]} (dias de chuva "
                 f"{100 * queda:+.1f}%) · 3 {s_[c3_]} · 4 Rx1day {s_[rx]}, p99 {txt_p99} → {s_[ok]}")
    venc = None
    if passam:
        melhor = min(passam, key=soma)
        venc = [k for k in ('C3G', 'C3RG') if k in passam and soma(k) <= soma(melhor) * 1.05 + t.EPS][0]
    L += ['', f"**M1: {('troca para ' + venc + ' (gravação só com autorização)') if venc else 'nenhum passou; o C3 (V1.8) fica'}"
          f"{'' if final else ' (parcial)'}.**", '']
    # M2
    t.METODOS = ['C0', 'R1']
    m2 = {}
    for k in ('C0', 'R1'):
        m2[k] = {}
        for r in t.REGIOES:
            def sr(met, var):
                return t.serie(alvo, met, var, r)
            i = sr(k, 'rs').index.intersection(sr('BR', 'rs').index)
            j = sr(k, 'eto').index.intersection(sr('BR', 'eto').index)
            m2[k][r] = {'rs': float((sr(k, 'rs').loc[i] - sr('BR', 'rs').loc[i]).mean()),
                        'eto': t.vies_pct(sr(k, 'eto').loc[j], sr('BR', 'eto').loc[j]),
                        'r': t.r_anomalias(pd.DataFrame({'metodo': sr(k, 'rs').loc[i], 'ref': sr('BR', 'rs').loc[i]}).reset_index())}
    qrs = abs(m2['C0']['Brasil']['rs']) - abs(m2['R1']['Brasil']['rs'])
    qet = abs(m2['C0']['Brasil']['eto']) - abs(m2['R1']['Brasil']['eto'])
    pr_ = max(abs(m2['R1'][r]['rs']) - abs(m2['C0'][r]['rs']) for r in t.REGIOES5)
    pe_ = max(abs(m2['R1'][r]['eto']) - abs(m2['C0'][r]['eto']) for r in t.REGIOES5)
    qr = max(m2['C0'][r]['r'] - m2['R1'][r]['r'] for r in t.REGIOES5)
    ok2 = qrs >= QUEDA_RS_MJ - t.EPS and qet >= QUEDA_ETO_PP - t.EPS and pr_ <= PIORA_RS_MJ + t.EPS \
        and pe_ <= PIORA_ETO_PP + t.EPS and qr <= QUEDA_R + t.EPS
    L += ['## M2. Radiação e ETo (base: V1.7)', '', '| Método | ' + ' | '.join(t.REGIOES) + ' |', '|---|' + '---|' * 6]
    for k in ('C0', 'R1'):
        L.append(f'| {k} | ' + ' | '.join(f"{m2[k][r]['rs']:+.2f} MJ / {m2[k][r]['eto']:+.1f}%" for r in t.REGIOES) + ' |')
    L += ['', f"R1: radiação no Brasil {qrs:+.2f} MJ (precisa ≥ 0,2) · ETo {qet:+.2f} p.p. (≥ 1) · pior região "
          f"{pr_:+.2f} MJ / {pe_:+.2f} p.p. · r_anom {qr:+.3f} → **{'PASSA (gravação só com autorização)' if ok2 else 'não passa; a V1.7 fica'}"
          f"{'' if final else ' (parcial)'}**", '']
    # M3
    L += ['## M3. Tmax, Tmin, UR, VPD e vento (base: V1.7)', '', '| Variável | Base: viés Brasil | T2: viés Brasil | Pior região (piora) | r_anom (maior queda) | Passa? |',
          '|---|---|---|---|---|---|']
    for v in ('tmax_C', 'tmin_C', 'RH', 'vpd', 'u2'):
        b, n = {}, {}
        for r in t.REGIOES:
            i = t.serie(alvo, 'C0', v, r).index.intersection(t.serie(alvo, 'BR', v, r).index)
            b[r] = float((t.serie(alvo, 'C0', v, r).loc[i] - t.serie(alvo, 'BR', v, r).loc[i]).mean())
            j = t.serie(alvo, 'T2', v, r).index.intersection(t.serie(alvo, 'BR', v, r).index)
            n[r] = float((t.serie(alvo, 'T2', v, r).loc[j] - t.serie(alvo, 'BR', v, r).loc[j]).mean())
        qb = abs(b['Brasil']) - abs(n['Brasil'])
        piora = max(abs(n[r]) - abs(b[r]) for r in t.REGIOES5)
        quedas = []
        for r in t.REGIOES5:
            br_s = t.serie(alvo, 'BR', v, r)
            rb = t.r_anomalias(pd.DataFrame({'metodo': t.serie(alvo, 'C0', v, r), 'ref': br_s}).reset_index())
            rn = t.r_anomalias(pd.DataFrame({'metodo': t.serie(alvo, 'T2', v, r), 'ref': br_s}).reset_index())
            quedas.append(rb - rn)
        ok3 = qb >= LIMIAR_M3[v] - t.EPS and piora <= LIMIAR_M3[v] + t.EPS and max(quedas) <= QUEDA_R + t.EPS
        L.append(f"| {v} | {b['Brasil']:+.3f} | {n['Brasil']:+.3f} | {piora:+.3f} | {max(quedas):+.3f} | {s_[ok3]} |")
    L.append('' if final else '\n(parcial)')
    open(os.path.join(SAIDA, 'RESULTADOS_LEVA1.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L))


def p99_pixels(df):
    """p99 nos 1.500 pixels: C3 (fase 1), C3G e C3RG (limiar e razões regionais desta leva)."""
    pix = os.path.join(FASE1, 'pixels')
    pontos = pd.read_csv(os.path.join(pix, 'pontos.csv'))
    dias = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(pix, 'dias_*.csv.gz')))
                     if int(a[-11:-7]) in t.ANOS_TESTE)
    ag = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(pix, 'agregados_*.csv.gz'))))
    lim = pd.read_csv(os.path.join(SAIDA, 'limiares_garoa.csv'))
    lim = {(r.ano_alvo, r.mes, r.regiao): r.limiar for r in lim.itertuples()}
    aj = pd.read_csv(os.path.join(SAIDA, 'ajustes.csv'))
    razoes = {(r.ano_alvo, r.mes, r.regiao): r.r_c3 for r in aj.itertuples()}
    px = t.chuva_pixels(ag, dias, pontos, razoes)
    pm = pontos.set_index('pid')
    reg = [pm.loc[p, 'regiao'] for p in px.pid]
    Y = (px.dia // 10000).values
    lims = np.array([lim.get((y, m, r), 0.0) for y, m, r in zip(Y, px.mes, reg)])
    g = np.where(px.C0.values < lims, 0.0, px.C0.values)
    ajd = {(r.ano_alvo, r.mes, r.regiao): r for r in aj.itertuples()}
    px['C3G'] = g * np.array([ajd[(y, m, r)].r_g if (y, m, r) in ajd else 1.0 for y, m, r in zip(Y, px.mes, reg)])
    px['C3RG'] = g * np.array([ajd[(y, m, r)].r_rg if (y, m, r) in ajd else 1.0 for y, m, r in zip(Y, px.mes, reg)])
    return t.metricas_pixels(px, ['C3', 'C3G', 'C3RG'])


# ============================================================ orquestração
def main():
    os.makedirs(os.path.join(SAIDA, 'regional'), exist_ok=True)
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)
    pix = os.path.join(FASE1, 'pixels')
    pontos = pd.read_csv(os.path.join(pix, 'pontos.csv'))
    for ano in ANOS_DIAS_EXTRA:                       # dias dos pixels de 2011-2015 (limiares de 2016-2020)
        arq = os.path.join(pix, f'dias_{ano}.csv.gz')
        if not os.path.exists(arq):
            if time.time() > limite:
                raise SystemExit(3)
            t.dias_pixels(ano, pontos).round(3).to_csv(arq, index=False)
            print(f'   pixels dias {ano} prontos', flush=True)
    arq_lim = os.path.join(SAIDA, 'limiares_garoa.csv')
    if not os.path.exists(arq_lim):
        dias = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(pix, 'dias_*.csv.gz'))))
        ag = pd.concat(pd.read_csv(a) for a in sorted(glob.glob(os.path.join(pix, 'agregados_*.csv.gz'))))
        lim = limiares(ag, dias, pontos)
        pd.DataFrame([{'ano_alvo': k[0], 'mes': k[1], 'regiao': k[2], 'limiar': v} for k, v in lim.items()]) \
            .to_csv(arq_lim, index=False)
    lim = pd.read_csv(arq_lim)
    lim = {(r.ano_alvo, r.mes, r.regiao): r.limiar for r in lim.itertuples()}
    print('Limiares da garoa (mm, mediana por região): ' + ', '.join(
        f"{r} {np.median([v for k, v in lim.items() if k[2] == r]):.2f}" for r in t.REGIOES5), flush=True)
    arq_aj = os.path.join(SAIDA, 'ajustes.csv')
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
            linhas, aj = regional_mes(Y, mes, lim)
            pd.DataFrame(linhas).to_csv(arq, index=False)
            linha_aj = pd.DataFrame([{'ano_alvo': Y, 'mes': mes, 'regiao': r, **{k: aj[k][r] for k in aj}}
                                     for r in t.REGIOES5])
            linha_aj.to_csv(arq_aj, mode='a', header=not os.path.exists(arq_aj), index=False)
            print(f'   {Y}-{mes:02d} pronto em {(time.time() - t0) / 60:.1f} min', flush=True)
    resumo()


if __name__ == '__main__':
    resumo() if (sys.argv[1:] or [''])[0] == 'resumo' else main()
