# Correção da chuva, da radiação e da ETo nos dias ERA5: teste fora da amostra com origem móvel. SÓ LEITURA no
# Earth Engine (as funções de escrita ficam bloqueadas). Protocolo APROVADO e congelado ANTES de rodar:
# pesquisa/PROTOCOLO_CORRECAO_ERA5_2026.md (commit 1de7696 do validacoes-2, 25/11/2026). Nada aqui muda a regra.
#
# PERGUNTA: uma calibração que pesa os anos recentes reduz o erro da chuva (e da radiação e da ETo) em anos que ela
#   não viu, sem piorar a variação de mês a mês nem os extremos?
#
# DESENHO (do protocolo): anos de teste 2016-2025; cada ano-alvo Y é calibrado SÓ com anos anteriores a Y.
#   C0  atual: fator pixel x mês com a média de 1986 a Y-1 (a receita da SICSB_1986_2025, o script O2)
#   C1  a mesma conta com a média de Y-10 a Y-1;   C2  idem, Y-15 a Y-1
#   C3  C0 x razão (BR-DWGD / C0) da região e do mês em Y-5..Y-1, limitada a [0,8; 1,5] (chuva);
#       C0 + diferença (BR-DWGD - C0) da região e do mês em Y-5..Y-1 (radiação)
#   Em todos: o teto da chuva diária (motor V1.6), a radiação <= céu claro, o 0 de radiação como vazio (V1.7) e a ETo
#   FAO-56 recalculada com a radiação corrigida. As outras entradas da ETo (Tmax, Tmin, UR, vento) são as do motor V1.7
#   (iguais nos quatro métodos). A referência é o que o banco entrega (BR-DWGD no núcleo; sab_pedido.colecao), nos
#   pixels entregues (classes 1-3), nas 5 regiões e no Brasil.
#
# REGRA DE DECISÃO (copiada do protocolo; fixada antes):
#   CHUVA: um método substitui o C0 só se cumprir AS QUATRO:
#     1. a mediana, entre as 5 regiões, do |viés anual| (a mediana dos 10 anos de cada região) cai >= 3 p.p.;
#     2. no Brasil, o |viés anual| melhora em >= 7 dos 10 anos;
#     3. o r_anomalias mensal (ciclo anual retirado) não cai mais de 0,02 em nenhuma das 5 regiões;
#     4. nos 150 pixels da K21: a fração de dias com chuva (>= 1 mm) não se afasta do BR-DWGD mais 2 p.p. do que o C0
#        já se afasta, e o erro do percentil 99 diário não cresce mais de 5%.
#     Mais de um passa: vence o de menor mediana do |viés|; diferença < 0,5 p.p.: o mais simples (C1, C2, C3).
#   RADIAÇÃO E ETo (juntas): substitui o C0 se o |viés| da radiação no Brasil cair >= 0,2 MJ/m²/dia, o da ETo cair
#     >= 1 p.p., e nenhuma região piorar mais de 0,1 MJ ou 0,5 p.p.
#   SÓ RELATADO (fora da regra): o método vencedor (e os outros) aplicados a 2026 x CHIRPS, com a régua de 2024.
#
# COMO AS CONTAS FORAM FIXADAS (o protocolo não descia a esse detalhe; escrito aqui ANTES de rodar):
#   - viés anual da chuva = 100 x (total do ano do método / total do BR-DWGD - 1), na média da região;
#   - r_anomalias = correlação de Pearson dos 120 totais mensais (2016-2025) de cada região, cada um menos a média do
#     mesmo mês do ano nos 10 anos (método e BR-DWGD, cada um com a sua média);
#   - condição 4: fração de dias com chuva = pixel-dias >= 1 mm / pixel-dias com BR-DWGD, os 150 pixels e os 10 anos
#     juntos; erro do percentil 99 = média, nos pixels, de |p99 do método / p99 do BR-DWGD - 1|, e "não cresce mais de
#     5%" = erro do método <= 1,05 x erro do C0 (o crescimento relativo, a leitura mais rígida);
#   - C3 no pixel: o C0 do pixel x a razão da região dele (no Brasil, a média das 5 regiões pesada pela área entregue
#     de cada uma, que é o que a média do Brasil faz);
#   - radiação: viés = média dos 120 meses de (método - BR-DWGD), em MJ/m²/dia; ETo: 100 x (total/total - 1) nos 120
#     meses. "Melhorar" e "piorar" comparam os |viés| com os do C0. Se mais de um método passar na radiação, vence o
#     de menor |viés| da radiação no Brasil; diferença < 0,05 MJ: o mais simples (C1, C2, C3), como na chuva.
#
# CONFERÊNCIA DA RECEITA (antes de tudo, técnica, não é regra): a média recalculada aqui para 1986-2025 tem de bater
#   com o asset SICSB_1986_2025 (chuva e radiação, BR-DWGD e ERA5, médias regionais de janeiro e julho) a 2%; se não
#   bater, o script para (código 1) sem rodar o resto.
#
#     python pesquisa/validar_correcao_era5.py          (retomável; TEMPO_MAX_MIN limita: sai com código 3 se faltar)
#     python pesquisa/validar_correcao_era5.py resumo   (só refaz o RESULTADOS.md com o que já foi baixado)
# Saída: pesquisa/resultados_correcao_era5/ (CSV brutos por ano-alvo e mês, pixels, CHIRPS e RESULTADOS.md).
import glob
import math
import os
import sys
import time
from datetime import date, timedelta

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, 'resultados_correcao_era5')
ANOS_TESTE = list(range(2016, 2026))
ANO_INICIO_CLIMA = 1986
METODOS = ['C0', 'C1', 'C2', 'C3']
SIMPLICIDADE = ['C1', 'C2', 'C3']               # desempate "o mais simples"
REGIOES5 = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
REGIOES = REGIOES5 + ['Brasil']
RAZAO_C3 = (0.8, 1.5)
ANOS_C3 = 5
CHUVA_DIA = 1.0                                 # mm (como a K21)
N_PONTOS, SEMENTE = 150, 21                     # os pixels da K21
REGIAO_K21 = [-75.0, -35.0, -28.0, 6.5]
FATOR_MAX = 5.0                                 # do motor (conferido contra a cópia carregada)
FATOR_TETO_CHUVA = 1.5
TOL_RECEITA = 0.02
# regra (protocolo)
QUEDA_MEDIANA_PP = 3.0
ANOS_MELHORA_MIN = 7
QUEDA_R_MAX = 0.02
AFASTA_FRACAO_PP = 2.0
CRESCE_P99 = 0.05
DESEMPATE_PP = 0.5
QUEDA_RS_MJ, QUEDA_ETO_PP = 0.2, 1.0
PIORA_RS_MJ, PIORA_ETO_PP = 0.1, 0.5
DESEMPATE_RS_MJ = 0.05


def janela(metodo, Y):
    """Anos (início, fim) da média de cada método para o ano-alvo Y (C3 usa a do C0)."""
    return {'C0': (ANO_INICIO_CLIMA, Y - 1), 'C1': (Y - 10, Y - 1), 'C2': (Y - 15, Y - 1),
            'C3': (ANO_INICIO_CLIMA, Y - 1)}[metodo]


def pedacos(Y):
    """Três blocos de anos que somados dão as janelas C2 (b+c), C1 (c) e C0 (a+b+c): cada bloco é lido uma vez."""
    return {'a': (ANO_INICIO_CLIMA, Y - 16), 'b': (Y - 15, Y - 11), 'c': (Y - 10, Y - 1)}


BLOCOS = {'C0': 'abc', 'C1': 'c', 'C2': 'bc'}


# ============================================================ contas puras (testadas em teste_correcao_era5.py)
def fator(m_br, m_era):
    """Fator da V1.0 com o teto do motor: m_br / max(m_era, 1e-3), no máximo FATOR_MAX."""
    return np.minimum(np.asarray(m_br, float) / np.maximum(np.asarray(m_era, float), 1e-3), FATOR_MAX)


def chuva_corrigida(bruta, f, pr_max_br):
    """Motor V1.6/V1.7 no pixel: min(max(bruta x f, 0), max(bruta, 1,5 x maior dia do BR-DWGD no pixel e mês))."""
    bruta = np.asarray(bruta, float)
    pr = np.maximum(bruta * f, 0)
    teto = np.asarray(np.nan if pr_max_br is None else pr_max_br, float)
    limite = np.where(np.isfinite(teto), np.maximum(bruta, FATOR_TETO_CHUVA * np.nan_to_num(teto)), np.inf)
    return np.minimum(pr, limite)            # sem matriz no pixel, nada muda (como o unmask do motor)


def razao_c3(br_totais, c0_totais):
    """Razão (BR-DWGD / C0) dos totais de Y-5..Y-1, limitada; sem chuva no C0: 1."""
    s_br, s_c0 = float(np.nansum(br_totais)), float(np.nansum(c0_totais))
    if s_c0 <= 0:
        return 1.0
    return float(min(max(s_br / s_c0, RAZAO_C3[0]), RAZAO_C3[1]))


def vies_pct(metodo, ref):
    s = float(np.nansum(ref))
    return 100.0 * (float(np.nansum(metodo)) / s - 1.0) if s else float('nan')


def r_anomalias(mensal):
    """mensal: DataFrame com ano, mes, metodo, ref. Correlação das anomalias (cada série menos a média do mês)."""
    d = mensal.dropna(subset=['metodo', 'ref']).copy()
    if len(d) < 3:
        return float('nan')
    d['am'] = d.metodo - d.groupby('mes').metodo.transform('mean')
    d['ar'] = d.ref - d.groupby('mes').ref.transform('mean')
    if d.am.std() == 0 or d.ar.std() == 0:
        return float('nan')
    return float(np.corrcoef(d.am, d.ar)[0, 1])


def metricas_chuva(reg):
    """reg: DataFrame regiao, ano, mes, metodo (C0..C3 ou BR), valor (total mensal de chuva).
    Devolve {metodo: {...}} com o viés anual por região e ano, a mediana, os anos melhores e o r_anomalias."""
    br = reg[reg.metodo == 'BR'].set_index(['regiao', 'ano', 'mes']).valor
    out = {}
    for k in METODOS:
        mk = reg[reg.metodo == k].set_index(['regiao', 'ano', 'mes']).valor
        vies = {(r, a): vies_pct(mk.loc[r, a], br.loc[r, a]) for r in REGIOES for a in ANOS_TESTE
                if (r, a) in mk.index.droplevel(2) and (r, a) in br.index.droplevel(2)}
        med_reg = {r: float(np.nanmedian([abs(vies[(r, a)]) for a in ANOS_TESTE if (r, a) in vies])) for r in REGIOES}
        r_an = {}
        for r in REGIOES:
            m = pd.DataFrame({'metodo': mk.loc[r], 'ref': br.loc[r]}).reset_index()
            r_an[r] = r_anomalias(m)
        out[k] = {'vies': vies, 'mediana_regiao': med_reg,
                  'mediana5': float(np.median([med_reg[r] for r in REGIOES5])), 'r_anom': r_an}
    return out


def metricas_pixels(dias, ks=METODOS):
    """dias: DataFrame pid, data, br, C0..C3 (chuva diária nos pixels, anos de teste, só dias com BR-DWGD)."""
    d = dias.dropna(subset=['br'])
    out = {'fracao_br': float((d.br >= CHUVA_DIA).mean())}
    p99_br = d.groupby('pid').br.quantile(0.99)
    ok = p99_br[p99_br > 0].index
    for k in ks:
        p99 = d.groupby('pid')[k].quantile(0.99)
        out[k] = {'fracao': float((d[k] >= CHUVA_DIA).mean()),
                  'erro_p99': float(np.mean(np.abs(p99.loc[ok] / p99_br.loc[ok] - 1)))}
    return out


def decidir_chuva(mc, mp):
    """As 4 condições para C1..C3 contra o C0. Devolve (vencedor ou None, detalhes por método)."""
    c0 = mc['C0']
    afast0 = abs(mp['C0']['fracao'] - mp['fracao_br'])
    det, passam = {}, []
    for k in SIMPLICIDADE:
        mk = mc[k]
        cond1 = c0['mediana5'] - mk['mediana5'] >= QUEDA_MEDIANA_PP
        melhores = sum(1 for a in ANOS_TESTE if ('Brasil', a) in mk['vies'] and ('Brasil', a) in c0['vies']
                       and abs(mk['vies'][('Brasil', a)]) < abs(c0['vies'][('Brasil', a)]))
        cond2 = melhores >= ANOS_MELHORA_MIN
        quedas = {r: c0['r_anom'][r] - mk['r_anom'][r] for r in REGIOES5}
        cond3 = all(np.isfinite(q) and q <= QUEDA_R_MAX for q in quedas.values())
        afast = abs(mp[k]['fracao'] - mp['fracao_br'])
        eps = 1e-9                                   # só arredondamento: um empate exato não reprova
        cond4 = (afast <= afast0 + AFASTA_FRACAO_PP / 100.0 + eps) and \
            (mp[k]['erro_p99'] <= (1 + CRESCE_P99) * mp['C0']['erro_p99'] + eps)
        det[k] = {'cond1': cond1, 'queda_mediana_pp': c0['mediana5'] - mk['mediana5'], 'cond2': cond2,
                  'anos_melhores': melhores, 'cond3': cond3, 'maior_queda_r': max(quedas.values()),
                  'cond4': cond4, 'afastamento_fracao_pp': 100 * afast, 'afastamento_fracao_c0_pp': 100 * afast0,
                  'erro_p99': mp[k]['erro_p99'], 'erro_p99_c0': mp['C0']['erro_p99']}
        det[k]['passa'] = cond1 and cond2 and cond3 and cond4
        if det[k]['passa']:
            passam.append(k)
    return escolher(passam, {k: mc[k]['mediana5'] for k in passam}, DESEMPATE_PP), det


def escolher(passam, nota, desempate):
    """Menor nota; quem estiver a menos de `desempate` da melhor empata e vence o mais simples (ordem SIMPLICIDADE)."""
    if not passam:
        return None
    melhor = min(nota[k] for k in passam)
    empatados = [k for k in SIMPLICIDADE if k in passam and nota[k] - melhor < desempate]
    return empatados[0]


def metricas_rad(reg):
    """reg: regiao, ano, mes, metodo, variavel (rs/eto), valor. Viés pooled dos 120 meses por região."""
    out = {}
    for k in METODOS:
        out[k] = {}
        for r in REGIOES:
            def serie(met, var):
                s = reg[(reg.metodo == met) & (reg.variavel == var) & (reg.regiao == r)]
                return s.set_index(['ano', 'mes']).valor
            rs_k, rs_b = serie(k, 'rs'), serie('BR', 'rs')
            et_k, et_b = serie(k, 'eto'), serie('BR', 'eto')
            i_rs, i_et = rs_k.index.intersection(rs_b.index), et_k.index.intersection(et_b.index)
            out[k][r] = {'vies_rs': float((rs_k.loc[i_rs] - rs_b.loc[i_rs]).mean()),
                         'vies_eto': vies_pct(et_k.loc[i_et], et_b.loc[i_et])}
    return out


def decidir_rad(mr):
    c0, det, passam = mr['C0'], {}, []
    for k in SIMPLICIDADE:
        mk = mr[k]
        queda_rs = abs(c0['Brasil']['vies_rs']) - abs(mk['Brasil']['vies_rs'])
        queda_et = abs(c0['Brasil']['vies_eto']) - abs(mk['Brasil']['vies_eto'])
        piora = {r: (abs(mk[r]['vies_rs']) - abs(c0[r]['vies_rs']), abs(mk[r]['vies_eto']) - abs(c0[r]['vies_eto']))
                 for r in REGIOES5}
        ok_reg = all(p[0] <= PIORA_RS_MJ and p[1] <= PIORA_ETO_PP for p in piora.values())
        det[k] = {'queda_rs': queda_rs, 'queda_eto_pp': queda_et, 'pior_regiao_rs': max(p[0] for p in piora.values()),
                  'pior_regiao_eto_pp': max(p[1] for p in piora.values()),
                  'passa': queda_rs >= QUEDA_RS_MJ and queda_et >= QUEDA_ETO_PP and ok_reg}
        if det[k]['passa']:
            passam.append(k)
    return escolher(passam, {k: abs(mr[k]['Brasil']['vies_rs']) for k in passam}, DESEMPATE_RS_MJ), det


def brasil_ponderado(valores, pesos):
    """Média do Brasil a partir das 5 regiões, pesada pela área entregue de cada uma."""
    num = sum(valores[r] * pesos[r] for r in REGIOES5 if r in valores and np.isfinite(valores[r]))
    den = sum(pesos[r] for r in REGIOES5 if r in valores and np.isfinite(valores[r]))
    return num / den if den else float('nan')


def c3_chuva_regional(df, pesos):
    """Acrescenta as linhas do C3 da chuva (C0 x razão da região), ano-alvo a ano-alvo e mês a mês.
    df: as linhas brutas (ano_alvo, ano, mes, regiao, metodo, variavel, valor)."""
    novas = []
    for (Y, mes), g in df[df.variavel == 'pr'].groupby(['ano_alvo', 'mes']):
        anos_l = range(Y - ANOS_C3, Y)
        vals = {}
        for r in REGIOES5:
            br = g[(g.regiao == r) & (g.metodo == 'BR') & g.ano.isin(anos_l)].valor
            c0 = g[(g.regiao == r) & (g.metodo == 'C0') & g.ano.isin(anos_l)].valor
            c0y = g[(g.regiao == r) & (g.metodo == 'C0') & (g.ano == Y)].valor
            if len(c0y) and len(br) == ANOS_C3 and len(c0) == ANOS_C3:
                vals[r] = razao_c3(br, c0) * float(c0y.iloc[0])
        if len(vals) == len(REGIOES5):
            vals['Brasil'] = brasil_ponderado(vals, pesos)
        novas += [{'ano_alvo': Y, 'ano': Y, 'mes': mes, 'regiao': r, 'metodo': 'C3', 'variavel': 'pr', 'valor': v}
                  for r, v in vals.items()]
    return pd.concat([df, pd.DataFrame(novas)], ignore_index=True)


def deltas_c3(linhas_l, Y):
    """Razão da chuva e diferença da radiação (BR - C0) por região, a partir das linhas de Y-5..Y-1 de um mês."""
    d = pd.DataFrame(linhas_l)
    razao, delta = {}, {}
    for r in REGIOES5:
        g = d[d.regiao == r]
        pr_br, pr_c0 = g[(g.metodo == 'BR') & (g.variavel == 'pr')], g[(g.metodo == 'C0') & (g.variavel == 'pr')]
        rs_br = g[(g.metodo == 'BR') & (g.variavel == 'rs')].set_index('ano').valor
        rs_c0 = g[(g.metodo == 'C0') & (g.variavel == 'rs')].set_index('ano').valor
        razao[r] = razao_c3(pr_br.valor, pr_c0.valor)
        i = rs_br.index.intersection(rs_c0.index)
        delta[r] = float((rs_br.loc[i] - rs_c0.loc[i]).mean()) if len(i) else 0.0
    return razao, delta


def chuva_pixels(dados, pontos, razoes):
    """Chuva diária dos 4 métodos nos pixels, para os anos de teste, a partir dos dias brutos de 1986-2025.
    dados: pid, data, era, br (diários). pontos: pid, regiao, prmax_01..12. razoes: {(Y, mes, regiao): razão C3}."""
    d = dados.copy()
    d['ano'] = d.data.str[:4].astype(int)
    d['mes'] = d.data.str[5:7].astype(int)
    pm = pontos.set_index('pid')
    saida = []
    for Y in ANOS_TESTE:
        alvo = d[d.ano == Y]
        clim = {}
        for k in ('C0', 'C1', 'C2'):
            a0, a1 = janela(k, Y)
            h = d[(d.ano >= a0) & (d.ano <= a1)]
            clim[k] = h.groupby(['pid', 'mes']).agg(m_era=('era', 'mean'), m_br=('br', 'mean'))
        x = alvo.copy()
        prmax = np.array([pm.loc[p, f'prmax_{m:02d}'] for p, m in zip(x.pid, x.mes)], float)
        for k, c in clim.items():
            cc = c.reindex(list(zip(x.pid, x.mes)))
            x[k] = chuva_corrigida(x.era.values, fator(cc.m_br.values, cc.m_era.values), prmax)
        reg = [pm.loc[p, 'regiao'] for p in x.pid]
        x['C3'] = x.C0.values * np.array([razoes.get((Y, m, r), 1.0) for m, r in zip(x.mes, reg)])
        saida.append(x)
    return pd.concat(saida, ignore_index=True)


# ============================================================ Earth Engine
_E = {}


def iniciar():
    if _E:
        return _E
    sys.path.insert(0, AQUI)
    import ee
    import validar_metodo_2026 as vm                 # inicia o Earth Engine; carrega o motor V1.7 (SHA conferido)
    m = vm.carregar_motor()                          # e bloqueia toda escrita
    assert m['FATOR_MAX'] == FATOR_MAX and m['FATOR_TETO_CHUVA'] == FATOR_TETO_CHUVA, 'constantes do motor mudaram'
    _E.update(ee=ee, vm=vm, v=vm.v, sp=vm.sp, m=m, regs=vm.v.regioes())
    _E['regs5'] = _E['regs'].filter(ee.Filter.inList('regiao', REGIOES5))
    return _E


def gi(obj, rotulo, tentativas=5):
    for t in range(tentativas):
        try:
            return obj.getInfo()
        except Exception as e:  # noqa: BLE001
            if t == tentativas - 1:
                raise
            print(f'   ⚠️ {rotulo}: {str(e)[:160]} | de novo em {30 * (t + 1)} s', flush=True)
            time.sleep(30 * (t + 1))


def reduzir(img, bandas, rotulo):
    """Média regional (pixels entregues), em grupos de bandas cada vez menores se o servidor recusar."""
    E = iniciar()
    ee, v, sp = E['ee'], E['v'], E['sp']
    for tentativa, grupos in enumerate((1, 2, 4, len(bandas))):
        try:
            res = {}
            n = -(-len(bandas) // grupos)
            for i in range(0, len(bandas), n):
                fc = img.select(bandas[i:i + n]).updateMask(v.ENTREGUE).reduceRegions(
                    collection=E['regs'], reducer=ee.Reducer.mean(), crs=sp.CRS, crsTransform=sp.TRANSFORM, tileScale=16)
                for f in fc.getInfo()['features']:
                    res.setdefault(f['properties']['regiao'], {}).update(f['properties'])
            return res
        except Exception as e:  # noqa: BLE001
            print(f'   ⚠️ {rotulo}: {str(e)[:160]} | de novo em pedidos menores', flush=True)
            time.sleep(20 * (tentativa + 1))
    raise RuntimeError(f'{rotulo}: não deu depois de 4 tentativas')


def br_limpo(img):
    """O2: pixel válido = pr > -32768; chuva e radiação decodificadas."""
    ee = iniciar()['ee']
    mask = img.select('pr').gt(-32768)
    return ee.Image.cat([img.select('pr').updateMask(mask).multiply(0.00686666).add(225.0).max(0).rename('pr'),
                         img.select('Rs').updateMask(mask).multiply(0.15708661).add(-0.057087).rename('Rs')])


def era_limpo(img):
    """O2: chuva sem reamostrar, radiação bilinear (sem tirar o 0: a matriz original não tirava)."""
    ee = iniciar()['ee']
    return ee.Image.cat([img.select('total_precipitation_sum').multiply(1000).max(0).rename('pr'),
                         img.select('surface_solar_radiation_downwards_sum').divide(1e6).resample('bilinear').rename('Rs')])


def soma_conta(col, mes, a0, a1, prep):
    ee = iniciar()['ee']
    c = col.filter(ee.Filter.calendarRange(mes, mes, 'month')).filterDate(f'{a0}-01-01', f'{a1 + 1}-01-01').map(prep)
    return c.reduce(ee.Reducer.sum().combine(ee.Reducer.count(), sharedInputs=True))   # pr_sum, pr_count, Rs_sum, Rs_count


def climatologias(mes, Y, metodos=('C0', 'C1', 'C2')):
    """{metodo: imagem com pr_m_br, pr_m_era, Rs_m_br, Rs_m_era} na grade do SAB (como a exportação do O2)."""
    E = iniciar()
    ee, m, sp = E['ee'], E['m'], E['sp']
    blocos = {}
    for b, (a0, a1) in pedacos(Y).items():
        if a1 >= a0 and any(b in BLOCOS[k] for k in metodos):
            blocos[b] = (soma_conta(m['colChuvaGeral'], mes, a0, a1, br_limpo),
                         soma_conta(m['colecao_era5'], mes, a0, a1, era_limpo))
    out = {}
    for k in metodos:
        bs = [b for b in BLOCOS[k] if b in blocos]
        im = []
        for fonte, i in (('br', 0), ('era', 1)):
            for var in ('pr', 'Rs'):
                s = ee.Image.cat([blocos[b][i].select(f'{var}_sum') for b in bs]).reduce(ee.Reducer.sum())
                n = ee.Image.cat([blocos[b][i].select(f'{var}_count') for b in bs]).reduce(ee.Reducer.sum())
                im.append(s.divide(n).rename(f'{var}_m_{fonte}'))
        out[k] = ee.Image.cat(im).toFloat().reproject(crs=sp.CRS, crsTransform=sp.TRANSFORM)
    return out


def dia_metodos(d, climas, eqm, delta_img=None, com_eto=True):
    """Chuva, radiação e ETo de um dia pela rota ERA5 do motor V1.7, trocando só a climatologia da chuva e da
    radiação. delta_img: a diferença regional do C3 (radiação)."""
    E = iniciar()
    ee, m = E['ee'], E['m']
    c = m['_componentes_era5'](d)
    era = ee.Image(m['colecao_era5'].filterDate(ee.Date(d), ee.Date(d).advance(1, 'day')).first())
    pr_raw = era.select('total_precipitation_sum').multiply(1000).max(0)
    rs_cru = era.select('surface_solar_radiation_downwards_sum').divide(1e6)
    rs_raw = rs_cru.updateMask(rs_cru.gt(0)).resample('bilinear')
    bandas = []
    rs0 = None
    for k, cl in climas.items():
        pr = m['teto_chuva'](m['calib_multiplicativa'](pr_raw, cl.select('pr_m_br'), cl.select('pr_m_era')).max(0),
                             pr_raw, eqm)
        rs = m['limitar_rs'](m['calib_multiplicativa'](rs_raw, cl.select('Rs_m_br'), cl.select('Rs_m_era')).max(0), d)
        rs0 = rs if k == 'C0' else rs0
        bandas += [pr.rename(f'{k}_pr'), rs.rename(f'{k}_rs')]
        if com_eto:
            bandas.append(m['eto_penman_monteith'](c['tmax_C'], c['tmin_C'], c['RH'], c['u2'], rs, d).rename(f'{k}_eto'))
    if delta_img is not None:
        rs3 = m['limitar_rs'](rs0.add(delta_img).max(0), d)
        bandas += [rs3.rename('C3_rs'),
                   m['eto_penman_monteith'](c['tmax_C'], c['tmin_C'], c['RH'], c['u2'], rs3, d).rename('C3_eto')]
    return ee.Image.cat(bandas).updateMask(m['MASCARA_SAB'])


def mensal_metodos(ano, mes, climas, delta_img=None, com_eto=True):
    ee = iniciar()['ee']
    d0 = date(ano, mes, 1)
    d1 = (d0 + timedelta(days=32)).replace(day=1)
    dias = [(d0 + timedelta(days=k)).isoformat() for k in range((d1 - d0).days)]
    col = ee.ImageCollection([dia_metodos(d, climas, E_eqm(mes), delta_img, com_eto) for d in dias])
    nomes = col.first().bandNames()
    soma = col.select('.*_(pr|eto)').sum()
    media = col.select('.*_rs').mean()
    return ee.Image.cat([soma, media]).select(nomes)


def E_eqm(mes):
    E = iniciar()
    return E['ee'].Image(f"{E['m']['ASSET_EQM']}/Matriz_EQM_{mes:02d}")


def entregue_mensal(ano, mes, com_eto=True):
    E = iniciar()
    ini = date(ano, mes, 1)
    fim = (ini + timedelta(days=32)).replace(day=1)
    col = E['sp'].colecao(E['vm'].BRASIL, ini.isoformat(), fim.isoformat())
    im = [col.select('pr_mm').sum().rename('BR_pr'), col.select('rs').mean().rename('BR_rs')]
    if com_eto:
        im.append(col.select('et_potencial').sum().rename('BR_eto'))
    return E['ee'].Image.cat(im)


def linhas_de(res, Y, ano, mes, prefixo_ano=None):
    out = []
    for reg, p in res.items():
        for chave, valor in p.items():
            if chave == 'regiao' or valor is None:
                continue
            partes = chave.split('_')
            if prefixo_ano is not None:
                if not partes[0].startswith('a'):
                    continue
                ano_l, partes = int(partes[0][1:]), partes[1:]
            else:
                ano_l = ano
            out.append({'ano_alvo': Y, 'ano': ano_l, 'mes': mes, 'regiao': reg, 'metodo': partes[0],
                        'variavel': partes[1], 'valor': valor})
    return out


def regional_mes(Y, mes):
    """Os dois pedidos de um ano-alvo e mês: (L) o C0 e o BR-DWGD nos 5 anos anteriores, para o C3; (T) o ano-alvo."""
    E = iniciar()
    ee = E['ee']
    cl = climatologias(mes, Y)
    # L: anos Y-5..Y-1, C0 (com a climatologia de 1986..Y-1) e o que o banco entrega
    imgs, bandas = [], []
    for a in range(Y - ANOS_C3, Y):
        mm = mensal_metodos(a, mes, {'C0': cl['C0']}, com_eto=False)
        en = entregue_mensal(a, mes, com_eto=False)
        par = ee.Image.cat([mm, en])
        nomes = ['C0_pr', 'C0_rs', 'BR_pr', 'BR_rs']
        imgs.append(par.select(nomes, [f'a{a}_{x}' for x in nomes]))
        bandas += [f'a{a}_{x}' for x in nomes]
    res_l = reduzir(ee.Image.cat(imgs), bandas, f'{Y}-{mes:02d} (anos anteriores)')
    lin_l = linhas_de(res_l, Y, None, mes, prefixo_ano=True)
    razao, delta = deltas_c3(lin_l, Y)
    fc = E['regs5'].map(lambda f: f.set('delta', ee.Dictionary(delta).get(f.get('regiao'))))
    delta_img = ee.Image.constant(0).toFloat().paint(fc, 'delta')
    # T: o ano-alvo, C0/C1/C2 (chuva, radiação, ETo), C3 (radiação, ETo) e o que o banco entrega
    mm = mensal_metodos(Y, mes, cl, delta_img=delta_img)
    en = entregue_mensal(Y, mes)
    par = ee.Image.cat([mm, en])
    nomes = [f'{k}_{x}' for k in ('C0', 'C1', 'C2') for x in ('pr', 'rs', 'eto')] + ['C3_rs', 'C3_eto',
                                                                                     'BR_pr', 'BR_rs', 'BR_eto']
    res_t = reduzir(par.select(nomes), nomes, f'{Y}-{mes:02d} (ano-alvo)')
    return lin_l + linhas_de(res_t, Y, Y, mes), razao, delta


def conferir_receita():
    """A média recalculada para 1986-2025 x o asset SICSB_1986_2025 (janeiro e julho, médias regionais)."""
    E = iniciar()
    ee, m = E['ee'], E['m']
    arq = os.path.join(SAIDA, 'receita.csv')
    if os.path.exists(arq):
        return pd.read_csv(arq)
    linhas = []
    for mes in (1, 7):
        cl = climatologias(mes, 2026, metodos=('C0',))['C0']       # C0 do ano-alvo 2026 = 1986..2025
        ast = ee.Image(f"{m['ASSET_CLIMATOLOGIA']}/Matriz_Clima_{mes:02d}")
        bs = ['pr_m_br', 'pr_m_era', 'Rs_m_br', 'Rs_m_era']
        par = ee.Image.cat([cl.select(bs, [f'novo_{b}' for b in bs]), ast.select(bs, [f'asset_{b}' for b in bs])])
        res = reduzir(par, [f'{x}_{b}' for b in bs for x in ('novo', 'asset')], f'receita mês {mes:02d}')
        for reg, p in res.items():
            for b in bs:
                linhas.append({'mes': mes, 'regiao': reg, 'banda': b, 'recalculada': p.get(f'novo_{b}'),
                               'asset': p.get(f'asset_{b}')})
        print(f'   receita {mes:02d} conferida', flush=True)
    df = pd.DataFrame(linhas)
    df['dif_rel'] = (df.recalculada / df.asset - 1).abs()
    df.to_csv(arq, index=False)
    return df


def pesos_regioes():
    arq = os.path.join(SAIDA, 'pesos_regioes.csv')
    if os.path.exists(arq):
        p = pd.read_csv(arq)
        return dict(zip(p.regiao, p.peso))
    E = iniciar()
    ee, v, sp = E['ee'], E['v'], E['sp']
    fc = ee.Image.constant(1).rename('peso').updateMask(v.ENTREGUE).reduceRegions(
        collection=E['regs'], reducer=ee.Reducer.sum(), crs=sp.CRS, crsTransform=sp.TRANSFORM, tileScale=8)
    p = {f['properties']['regiao']: f['properties']['sum'] for f in gi(fc, 'pesos')['features']}
    pd.DataFrame({'regiao': list(p), 'peso': list(p.values())}).to_csv(arq, index=False)
    return p


def pontos_k21():
    """Os 150 pixels A da K21 (mesmo sorteio e semente), a região de cada um e o maior dia do BR-DWGD por mês."""
    arq = os.path.join(SAIDA, 'pixels', 'pontos.csv')
    if os.path.exists(arq):
        return pd.read_csv(arq)
    E = iniciar()
    ee, sp, m = E['ee'], E['sp'], E['m']
    proj = ee.Projection(sp.CRS, sp.TRANSFORM)
    classe = ee.Image(sp.MASCARA).select('classe')
    sorteio = (ee.Image.pixelLonLat().addBands(classe)
               .stratifiedSample(numPoints=0, classBand='classe', region=ee.Geometry.Rectangle(REGIAO_K21, None, False),
                                 projection=proj, seed=SEMENTE, classValues=[1], classPoints=[N_PONTOS],
                                 geometries=True, tileScale=4))
    pts = [{'pid': k, 'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1]}
           for k, f in enumerate(gi(sorteio, 'pontos')['features'])]
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']}) for p in pts])
    idx = E['regs5'].map(lambda f: f.set('idx', ee.Number(ee.List(REGIOES5).indexOf(f.get('regiao'))).add(1)))
    img = ee.Image.cat([ee.Image.constant(0).toInt().paint(idx, 'idx').rename('regiao_idx')] +
                       [E_eqm(mm).select('pr_max_br').rename(f'prmax_{mm:02d}') for mm in range(1, 13)])
    amostra = gi(img.sampleRegions(collection=fc, properties=['pid'], projection=proj, geometries=False, tileScale=16),
                 'pontos: região e teto')
    por = {f['properties']['pid']: f['properties'] for f in amostra['features']}
    for p in pts:
        q = por.get(p['pid'], {})
        i = int(q.get('regiao_idx') or 0)
        p['regiao'] = REGIOES5[i - 1] if i else 'fora'
        for mm in range(1, 13):
            p[f'prmax_{mm:02d}'] = q.get(f'prmax_{mm:02d}')
    df = pd.DataFrame(pts)
    os.makedirs(os.path.dirname(arq), exist_ok=True)
    df.to_csv(arq, index=False)
    print(f'   {len(df)} pixels da K21; por região: {df.regiao.value_counts().to_dict()}', flush=True)
    return df


def dias_pixels(ano, pontos):
    """Chuva diária bruta do ERA5 e do BR-DWGD nos pixels (um pedido por mês, como a K21)."""
    E = iniciar()
    ee, sp, m = E['ee'], E['sp'], E['m']
    x0, y0, dx = sp.TRANSFORM[2], sp.TRANSFORM[5], sp.TRANSFORM[0]
    chave = {(int(math.floor((lo - x0) / dx + 1e-6)), int(math.floor((y0 - la) / dx + 1e-6))): p
             for p, lo, la in zip(pontos.pid, pontos.lon, pontos.lat)}
    geo = ee.Geometry.MultiPoint([[lo, la] for lo, la in zip(pontos.lon, pontos.lat)])
    quadros = []
    for mes in range(1, 13):
        ini = date(ano, mes, 1)
        fim = (ini + timedelta(days=32)).replace(day=1)
        # ee.Image(...): no Python, copyProperties devolve um Element (o erro da K21 v3)
        era = m['colecao_era5'].filterDate(ini.isoformat(), fim.isoformat()).map(
            lambda i: ee.Image(i.select('total_precipitation_sum').multiply(1000).max(0).rename('era')
                               .copyProperties(i, ['system:time_start'])))
        br = m['colChuvaGeral'].filterDate(ini.isoformat(), fim.isoformat()).map(
            lambda i: ee.Image(br_limpo(i).select('pr').rename('br').copyProperties(i, ['system:time_start'])))
        for nome, col in (('era', era), ('br', br)):
            r = gi(ee.ImageCollection(col).getRegion(geo, None, sp.CRS, sp.TRANSFORM), f'pixels {nome} {ano}-{mes:02d}')
            d = pd.DataFrame(r[1:], columns=r[0])
            ix = np.floor((d.longitude.astype(float) - x0) / dx + 1e-6).astype(int)
            iy = np.floor((y0 - d.latitude.astype(float)) / dx + 1e-6).astype(int)
            d['pid'] = [chave.get((a, b)) for a, b in zip(ix, iy)]
            d['data'] = pd.to_datetime(d['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
            quadros.append(d.dropna(subset=['pid'])[['pid', 'data', nome]].assign(fonte=nome))
    era = pd.concat([q for q in quadros if len(q) and q.fonte.iloc[0] == 'era'])[['pid', 'data', 'era']]
    br = pd.concat([q for q in quadros if len(q) and q.fonte.iloc[0] == 'br'])[['pid', 'data', 'br']]
    era['pid'], br['pid'] = era.pid.astype(int), br.pid.astype(int)
    return era.merge(br, on=['pid', 'data'], how='left')


def chirps_2026(razoes_2026, pesos):
    """Só relato: a chuva de 2026 pelos quatro métodos (janelas até 2025) x CHIRPS, mesmos meses e máscara da
    validação de 2026; a régua (2024) e o 2026 gravado vêm de pesquisa/resultados_2026/validacao_2026_independente.csv."""
    arq = os.path.join(SAIDA, 'chirps_2026.csv')
    if os.path.exists(arq):
        return pd.read_csv(arq)
    E = iniciar()
    ee, v = E['ee'], E['v']
    ref = pd.read_csv(os.path.join(AQUI, 'resultados_2026', 'validacao_2026_independente.csv'))
    meses = sorted(ref[(ref.variavel == 'chuva_mm_mes') & (ref.ano == 2026)].mes.unique())
    linhas = []
    for mes in meses:
        cl = climatologias(mes, 2026)
        ini = date(2026, mes, 1)
        fim = (ini + timedelta(days=32)).replace(day=1)
        mm = mensal_metodos(2026, mes, cl, com_eto=False).select(['C0_pr', 'C1_pr', 'C2_pr'])
        par = ee.Image.cat([mm, v.CHIRPS.filterDate(ini.isoformat(), fim.isoformat()).sum().rename('CHIRPS_pr')])
        res = reduzir(par, ['C0_pr', 'C1_pr', 'C2_pr', 'CHIRPS_pr'], f'2026-{mes:02d} x CHIRPS')
        vals = {r: res[r]['C0_pr'] * razoes_2026.get((mes, r), 1.0) for r in REGIOES5
                if res.get(r, {}).get('C0_pr') is not None}
        vals['Brasil'] = brasil_ponderado(vals, pesos)
        for reg, p in res.items():
            for k in ('C0', 'C1', 'C2', 'CHIRPS'):
                linhas.append({'ano': 2026, 'mes': mes, 'regiao': reg, 'serie': k, 'valor': p.get(f'{k}_pr')})
            linhas.append({'ano': 2026, 'mes': mes, 'regiao': reg, 'serie': 'C3', 'valor': vals.get(reg)})
        print(f'   2026-{mes:02d} x CHIRPS pronto', flush=True)
    for r in ref[(ref.variavel == 'chuva_mm_mes') & ref.mes.isin(meses)].itertuples():
        serie = 'gravado' if r.ano == 2026 else 'BR-DWGD'
        linhas.append({'ano': r.ano, 'mes': r.mes, 'regiao': r.regiao, 'serie': serie, 'valor': r.sab})
        if r.ano == 2024:
            linhas.append({'ano': 2024, 'mes': r.mes, 'regiao': r.regiao, 'serie': 'CHIRPS', 'valor': r.referencia})
    df = pd.DataFrame(linhas)
    df.to_csv(arq, index=False)
    return df


def razoes_parte_a():
    """C3 de 2026: a razão BR-DWGD / método de 2026 (= C0 com 1986-2025) em 2021-2025, da Parte A."""
    arqs = sorted(glob.glob(os.path.join(AQUI, 'resultados_metodo_2026', 'parte_a', '*.csv')))
    df = pd.concat(pd.read_csv(a) for a in arqs)
    df = df[(df.variavel == 'pr_mm') & df.ano.between(2021, 2025)]
    return {(mes, r): razao_c3(g.entregue, g.metodo_2026) for (mes, r), g in df.groupby(['mes', 'regiao'])}


# ============================================================ resumo
def fmt(x, nd=1, sinal=True):
    return '-' if x is None or not np.isfinite(x) else (f'{x:+.{nd}f}' if sinal else f'{x:.{nd}f}')


def resumo():
    arqs = sorted(glob.glob(os.path.join(SAIDA, 'regional', '*.csv')))
    if not arqs:
        print('Nada baixado ainda.')
        return
    pesos = pesos_regioes()
    bruto = pd.concat(pd.read_csv(a) for a in arqs)
    df = c3_chuva_regional(bruto, pesos)
    alvo = df[df.ano == df.ano_alvo].copy()
    completos = sorted(Y for Y, g in alvo.groupby('ano_alvo') if g.mes.nunique() == 12)
    L = ['# Correção da chuva, da radiação e da ETo nos dias ERA5: teste fora da amostra', '',
         'Protocolo aprovado e congelado antes de rodar: `pesquisa/PROTOCOLO_CORRECAO_ERA5_2026.md`. Cada ano de teste '
         'é calibrado só com os anos anteriores. Referência: o que o banco entrega (BR-DWGD no núcleo), pixels '
         'entregues. Só leitura: nada foi gravado no Earth Engine.', '']
    rec = os.path.join(SAIDA, 'receita.csv')
    if os.path.exists(rec):
        r = pd.read_csv(rec)
        L += [f'Conferência da receita (média 1986-2025 recalculada × `SICSB_1986_2025`, janeiro e julho, 6 regiões, '
              f'chuva e radiação): maior diferença {100 * r.dif_rel.max():.2f}% (limite {100 * TOL_RECEITA:.0f}%).', '']
    if len(completos) < len(ANOS_TESTE):
        L += [f'**Parcial:** {len(completos)} de {len(ANOS_TESTE)} anos de teste completos ({completos}). '
              'A decisão só sai com os 10.', '']
    chuva = alvo[(alvo.variavel == 'pr') & alvo.ano_alvo.isin(completos)][['regiao', 'ano', 'mes', 'metodo', 'valor']]
    if completos:
        mc = metricas_chuva(chuva)
        L += ['## Chuva: |viés anual| (mediana dos anos de teste) e r_anomalias', '',
              '| Método | ' + ' | '.join(REGIOES) + ' | Mediana das 5 |', '|---|' + '---|' * (len(REGIOES) + 1)]
        for k in METODOS:
            L.append(f'| {k} | ' + ' | '.join(f"{fmt(mc[k]['mediana_regiao'][r], 1, False)}% "
                                               f"(r {fmt(mc[k]['r_anom'][r], 2, False)})" for r in REGIOES)
                     + f" | {fmt(mc[k]['mediana5'], 2, False)}% |")
        L += ['', '### Viés anual da chuva no Brasil (%)', '', '| Ano | ' + ' | '.join(METODOS) + ' |',
              '|---|' + '---|' * len(METODOS)]
        for a in completos:
            L.append(f'| {a} | ' + ' | '.join(fmt(mc[k]['vies'].get(('Brasil', a))) for k in METODOS) + ' |')
        L.append('')
    pix = os.path.join(SAIDA, 'pixels')
    anos_px = sorted(glob.glob(os.path.join(pix, 'dias_*.csv.gz')))
    mp = None
    if completos and len(completos) == len(ANOS_TESTE) and len(anos_px) == 2025 - ANO_INICIO_CLIMA + 1:
        pontos = pd.read_csv(os.path.join(pix, 'pontos.csv'))
        razoes = {}
        for Y in ANOS_TESTE:
            for mes in range(1, 13):
                g = df[(df.ano_alvo == Y) & (df.mes == mes) & (df.variavel == 'pr') & df.ano.between(Y - ANOS_C3, Y - 1)]
                for r in REGIOES5:
                    gr = g[g.regiao == r]
                    razoes[(Y, mes, r)] = razao_c3(gr[gr.metodo == 'BR'].valor, gr[gr.metodo == 'C0'].valor)
        dados = pd.concat(pd.read_csv(a) for a in anos_px)
        dias = chuva_pixels(dados, pontos, razoes)
        mp = metricas_pixels(dias)
        L += ['## Extremos nos 150 pixels da K21 (dias de 2016-2025)', '',
              f"Fração de dias com chuva (>= {CHUVA_DIA:.0f} mm) no BR-DWGD: {100 * mp['fracao_br']:.1f}%.", '',
              '| Método | Fração de dias com chuva (%) | Erro do percentil 99 |', '|---|---|---|']
        for k in METODOS:
            L.append(f"| {k} | {100 * mp[k]['fracao']:.1f} | {100 * mp[k]['erro_p99']:.1f}% |")
        L.append('')
    rad = alvo[alvo.variavel.isin(['rs', 'eto']) & alvo.ano_alvo.isin(completos)]
    if completos:
        mr = metricas_rad(rad)
        L += ['## Radiação e ETo: viés nos meses de teste', '',
              '| Método | ' + ' | '.join(REGIOES) + ' |', '|---|' + '---|' * len(REGIOES)]
        for k in METODOS:
            L.append(f'| {k} | ' + ' | '.join(f"{fmt(mr[k][r]['vies_rs'], 2)} MJ / {fmt(mr[k][r]['vies_eto'])}%"
                                               for r in REGIOES) + ' |')
        L.append('')
    if mp is not None:
        venc_c, det_c = decidir_chuva(mc, mp)
        venc_r, det_r = decidir_rad(mr)
        L += ['## Decisão (regra fixada antes)', '', '### Chuva', '',
              '| Método | 1. mediana cai >= 3 p.p. | 2. Brasil melhora em >= 7 de 10 anos | 3. r_anom não cai > 0,02 | '
              '4. dias de chuva e p99 | Passa? |', '|---|---|---|---|---|---|']
        s = {True: '✅', False: '❌'}
        for k in SIMPLICIDADE:
            d = det_c[k]
            L.append(f"| {k} | {s[d['cond1']]} {d['queda_mediana_pp']:+.2f} p.p. | {s[d['cond2']]} {d['anos_melhores']} | "
                     f"{s[d['cond3']]} maior queda {d['maior_queda_r']:+.3f} | {s[d['cond4']]} afastamento "
                     f"{d['afastamento_fracao_pp']:.2f} p.p. (C0 {d['afastamento_fracao_c0_pp']:.2f}); p99 "
                     f"{100 * d['erro_p99']:.1f}% (C0 {100 * d['erro_p99_c0']:.1f}%) | {s[d['passa']]} |")
        L += ['', f"**Chuva: {'troca para ' + venc_c if venc_c else 'nenhum método passou; o C0 (atual) fica'}.**", '',
              '### Radiação e ETo', '',
              '| Método | |viés| da radiação no Brasil cai (MJ) | |viés| da ETo no Brasil cai (p.p.) | pior região '
              '(MJ / p.p.) | Passa? |', '|---|---|---|---|---|']
        for k in SIMPLICIDADE:
            d = det_r[k]
            L.append(f"| {k} | {d['queda_rs']:+.2f} | {d['queda_eto_pp']:+.2f} | {d['pior_regiao_rs']:+.2f} / "
                     f"{d['pior_regiao_eto_pp']:+.2f} | {s[d['passa']]} |")
        L += ['', f"**Radiação e ETo: {'troca para ' + venc_r if venc_r else 'nenhum método passou; o C0 (atual) fica'}.**",
              '', 'Nada é gravado por este teste. Se algum método passou, o próximo passo (com aprovação) é o motor '
              'em simulação (05a), a prévia de 2026 e a K16; uma janela de anos exige um asset novo (escrita, '
              'aprovação separada).', '']
        L += relato_chirps(venc_c)
    with open(os.path.join(SAIDA, 'RESULTADOS.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


def relato_chirps(venc):
    arq = os.path.join(SAIDA, 'chirps_2026.csv')
    if not os.path.exists(arq):
        return []
    c = pd.read_csv(arq)
    L = ['## Só relatado (fora da regra): 2026 × CHIRPS', '',
         f"Meses {c.mes.min()} a {c.mes.max()}; viés do total do período contra o CHIRPS (%). Régua: 2024, quando o "
         f"SAB é o BR-DWGD. Método vencedor na chuva: {venc or 'nenhum (C0)'}.", '',
         '| Região | 2024 (régua) | 2026 gravado | 2026 C0 | 2026 C1 | 2026 C2 | 2026 C3 |', '|---|---|---|---|---|---|---|']
    for r in REGIOES:
        def v(ano, serie):
            a = c[(c.ano == ano) & (c.regiao == r) & (c.serie == serie)].valor.sum()
            b = c[(c.ano == ano) & (c.regiao == r) & (c.serie == 'CHIRPS')].valor.sum()
            return 100 * (a / b - 1) if b else float('nan')
        L.append(f"| {r} | {fmt(v(2024, 'BR-DWGD'))} | {fmt(v(2026, 'gravado'))} | " +
                 ' | '.join(fmt(v(2026, k)) for k in METODOS) + ' |')
    return L + ['']


# ============================================================ orquestração
def main():
    os.makedirs(os.path.join(SAIDA, 'regional'), exist_ok=True)
    os.makedirs(os.path.join(SAIDA, 'pixels'), exist_ok=True)
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)

    def tempo():
        if time.time() > limite:
            print('Tempo desta vez acabou; a próxima retoma daqui.', flush=True)
            resumo()
            raise SystemExit(3)

    rec = conferir_receita()
    pior = rec.dif_rel.max()
    print(f'Receita: maior diferença {100 * pior:.2f}% contra o asset SICSB_1986_2025', flush=True)
    if not pior <= TOL_RECEITA:
        print(rec.sort_values('dif_rel', ascending=False).head(10).to_string())
        raise SystemExit(f'A média recalculada não bate com o asset (>{100 * TOL_RECEITA:.0f}%): o teste não roda.')
    pesos = pesos_regioes()
    for Y in ANOS_TESTE:
        for mes in range(1, 13):
            arq = os.path.join(SAIDA, 'regional', f'{Y}_{mes:02d}.csv')
            if os.path.exists(arq):
                continue
            tempo()
            t0 = time.time()
            linhas, razao, delta = regional_mes(Y, mes)
            pd.DataFrame(linhas).to_csv(arq, index=False)
            print(f'   {Y}-{mes:02d} pronto em {(time.time() - t0) / 60:.1f} min | razão C3 '
                  + ', '.join(f'{r[:2]} {razao[r]:.2f}' for r in REGIOES5)
                  + ' | Δ Rs ' + ', '.join(f'{r[:2]} {delta[r]:+.2f}' for r in REGIOES5), flush=True)
    pontos = pontos_k21()
    for ano in range(ANO_INICIO_CLIMA, 2026):
        arq = os.path.join(SAIDA, 'pixels', f'dias_{ano}.csv.gz')
        if os.path.exists(arq):
            continue
        tempo()
        d = dias_pixels(ano, pontos)
        d.round(3).to_csv(arq, index=False)
        print(f'   pixels {ano}: {len(d)} pixel-dias', flush=True)
    tempo()
    chirps_2026(razoes_parte_a(), pesos)
    resumo()


if __name__ == '__main__':
    if (sys.argv[1:] or [''])[0] == 'resumo':
        resumo()
    else:
        main()
