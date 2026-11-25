# Correção da chuva, da radiação e da ETo nos dias ERA5: teste fora da amostra com origem móvel. SÓ LEITURA no
# Earth Engine (as funções de escrita ficam bloqueadas). Protocolo APROVADO e congelado ANTES de rodar:
# pesquisa/PROTOCOLO_CORRECAO_ERA5_2026.md (commit 1de7696 do validacoes-2, 25/11/2026) + EMENDA 1 (25/11/2026,
# também antes de rodar, pedida pelo responsável: os extremos em todos os pixels). Nada aqui muda a regra.
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
#   pixels entregues (classes 1-3), nas 5 regiões e no Brasil. Tudo é calculado pixel a pixel e dia a dia no Earth
#   Engine; as médias regionais pesam cada pixel pela fração dele dentro da região.
#
# REGRA DE DECISÃO (do protocolo, com a emenda 1 na condição 4; fixada antes):
#   CHUVA: um método substitui o C0 só se cumprir AS QUATRO:
#     1. a mediana, entre as 5 regiões, do |viés anual| (a mediana dos 10 anos de cada região) cai >= 3 p.p.;
#     2. no Brasil, o |viés anual| melhora em >= 7 dos 10 anos;
#     3. o r_anomalias mensal (ciclo anual retirado) não cai mais de 0,02 em nenhuma das 5 regiões;
#     4. extremos e dias de chuva (EMENDA 1: os três itens precisam passar):
#        4a. TODOS os pixels entregues: em cada uma das 5 regiões, a fração de dias com chuva (>= 1 mm) não se afasta
#            do BR-DWGD mais 2 p.p. do que o C0 já se afasta;
#        4b. TODOS os pixels entregues: em cada uma das 5 regiões, o erro da maior chuva diária do mês (Rx1day) não
#            cresce mais de 5% em relação ao do C0;
#        4c. 1.500 pixels A (300 por região, sorteio fixo, semente 21; antes eram os 150 da K21): o erro do percentil
#            99 diário não cresce mais de 5% em relação ao do C0.
#     Mais de um passa: vence o de menor mediana do |viés|; diferença < 0,5 p.p.: o mais simples (C1, C2, C3).
#   RADIAÇÃO E ETo (juntas): substitui o C0 se o |viés| da radiação no Brasil cair >= 0,2 MJ/m²/dia, o da ETo cair
#     >= 1 p.p., e nenhuma região piorar mais de 0,1 MJ ou 0,5 p.p.
#   SÓ RELATADO (fora da regra): os quatro métodos aplicados a 2026 x CHIRPS, com a régua de 2024.
#
# COMO AS CONTAS FORAM FIXADAS (escrito aqui ANTES de rodar):
#   - viés anual da chuva = 100 x (total do ano do método / total do BR-DWGD - 1), na média da região;
#   - r_anomalias = correlação de Pearson dos 120 totais mensais (2016-2025) de cada região, cada um menos a média do
#     mesmo mês do ano nos 10 anos (método e BR-DWGD, cada um com a sua média);
#   - 4a: fração = soma, nos 120 meses, da média regional dos dias >= 1 mm / soma dos dias (no BR-DWGD, dos dias com
#     dado); 4b: erro = soma, nos 120 meses, da média regional de |Rx1day do método - Rx1day do BR-DWGD| (pixel a
#     pixel) / soma da média regional do Rx1day do BR-DWGD; 4c: erro = média, nos pixels, de |p99 do método / p99 do
#     BR-DWGD - 1|, com os dias de 2016-2025 juntos. "Não cresce mais de 5%" = erro <= 1,05 x o do C0 (relativo);
#   - C3 da chuva: C0 x a razão da região do pixel (fora das 5 regiões, razão 1), dia a dia, sem refazer o teto;
#   - radiação: viés = média dos 120 meses de (método - BR-DWGD), em MJ/m²/dia; ETo: 100 x (total/total - 1) nos 120
#     meses. "Melhorar" e "piorar" comparam os |viés| com os do C0. Se mais de um método passar na radiação, vence o
#     de menor |viés| da radiação no Brasil; diferença < 0,05 MJ: o mais simples (C1, C2, C3), como na chuva.
#
# MEMÓRIA (técnico, 25/11, 2ª versão): a 1ª tentativa estourou a memória do Earth Engine ao somar ~1.240 dias do
#   ERA5-Land por mês. A média do ERA5 agora vem do ERA5-Land MENSAL (soma do mês / dias, a mesma conta, linear); o
#   BR-DWGD continua diário, com chuva e radiação em pedidos separados; sem a reprojeção explícita; e, se ainda faltar
#   memória, o pedido é feito região por região. A conferência da receita abaixo prova que o resultado é o do asset.
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
PONTOS_POR_REGIAO, SEMENTE = 300, 21            # emenda 1: 1.500 pixels A (antes, os 150 da K21)
REGIAO_SORTEIO = [-75.0, -35.0, -28.0, 6.5]
FATOR_MAX = 5.0                                 # do motor (conferido contra a cópia carregada)
FATOR_TETO_CHUVA = 1.5
TOL_RECEITA = 0.02
EPS = 1e-9                                      # só arredondamento: um empate exato não reprova
# regra (protocolo + emenda 1)
QUEDA_MEDIANA_PP = 3.0
ANOS_MELHORA_MIN = 7
QUEDA_R_MAX = 0.02
AFASTA_FRACAO_PP = 2.0
CRESCE_EXTREMO = 0.05
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


def dias_no_mes(ano, mes):
    d0 = date(ano, mes, 1)
    return ((d0 + timedelta(days=32)).replace(day=1) - d0).days


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


def serie(alvo, metodo, variavel, regiao):
    s = alvo[(alvo.metodo == metodo) & (alvo.variavel == variavel) & (alvo.regiao == regiao)]
    return s.groupby(['ano', 'mes']).valor.first()


def metricas_chuva(alvo):
    """alvo: as linhas do ano-alvo (ano == ano_alvo). Viés anual por região e ano, a mediana, o r_anomalias."""
    out = {}
    for k in METODOS:
        vies, med_reg, r_an = {}, {}, {}
        for r in REGIOES:
            mk, br = serie(alvo, k, 'pr', r), serie(alvo, 'BR', 'pr', r)
            i = mk.index.intersection(br.index)
            for a in ANOS_TESTE:
                ia = [x for x in i if x[0] == a]
                if len(ia) == 12:
                    vies[(r, a)] = vies_pct(mk.loc[ia], br.loc[ia])
            med_reg[r] = float(np.nanmedian([abs(vies[(r, a)]) for a in ANOS_TESTE if (r, a) in vies] or [np.nan]))
            m = pd.DataFrame({'metodo': mk.loc[i], 'ref': br.loc[i]}).reset_index()
            r_an[r] = r_anomalias(m)
        out[k] = {'vies': vies, 'mediana_regiao': med_reg,
                  'mediana5': float(np.median([med_reg[r] for r in REGIOES5])), 'r_anom': r_an}
    return out


def metricas_extremos(alvo):
    """4a e 4b em todos os pixels entregues, por região."""
    out = {'BR': {}}
    for r in REGIOES:
        wet, n = serie(alvo, 'BR', 'wet', r), serie(alvo, 'BR', 'n', r)
        out['BR'][r] = {'fracao': float(wet.sum() / n.sum()) if n.sum() else float('nan')}
    for k in METODOS:
        out[k] = {}
        for r in REGIOES:
            wet = serie(alvo, k, 'wet', r)
            dias = sum(dias_no_mes(a, m) for a, m in wet.index)
            drx, rx_br = serie(alvo, k, 'drx', r), serie(alvo, 'BR', 'rx', r)
            i = drx.index.intersection(rx_br.index)
            out[k][r] = {'fracao': float(wet.sum() / dias) if dias else float('nan'),
                         'erro_rx': float(drx.loc[i].sum() / rx_br.loc[i].sum()) if rx_br.loc[i].sum() else float('nan')}
    return out


def metricas_pixels(dias, ks=METODOS):
    """4c. dias: DataFrame pid, br, C0..C3 (chuva diária nos pixels, anos de teste, só dias com BR-DWGD)."""
    d = dias.dropna(subset=['br'])
    out = {'fracao_br': float((d.br >= CHUVA_DIA).mean()), 'n_pixels': int(d.pid.nunique()), 'n_dias': len(d)}
    p99_br = d.groupby('pid').br.quantile(0.99)
    ok = p99_br[p99_br > 0].index
    for k in ks:
        p99 = d.groupby('pid')[k].quantile(0.99)
        out[k] = {'fracao': float((d[k] >= CHUVA_DIA).mean()),
                  'erro_p99': float(np.mean(np.abs(p99.loc[ok] / p99_br.loc[ok] - 1)))}
    return out


def decidir_chuva(mc, mx, mp):
    """As 4 condições para C1..C3 contra o C0. Devolve (vencedor ou None, detalhes por método)."""
    c0 = mc['C0']
    det, passam = {}, []
    for k in SIMPLICIDADE:
        mk = mc[k]
        cond1 = c0['mediana5'] - mk['mediana5'] >= QUEDA_MEDIANA_PP - EPS
        melhores = sum(1 for a in ANOS_TESTE if ('Brasil', a) in mk['vies'] and ('Brasil', a) in c0['vies']
                       and abs(mk['vies'][('Brasil', a)]) < abs(c0['vies'][('Brasil', a)]))
        cond2 = melhores >= ANOS_MELHORA_MIN
        quedas = {r: c0['r_anom'][r] - mk['r_anom'][r] for r in REGIOES5}
        cond3 = all(np.isfinite(q) and q <= QUEDA_R_MAX + EPS for q in quedas.values())
        piora_fr = {r: abs(mx[k][r]['fracao'] - mx['BR'][r]['fracao']) - abs(mx['C0'][r]['fracao'] - mx['BR'][r]['fracao'])
                    for r in REGIOES5}
        cresc_rx = {r: mx[k][r]['erro_rx'] / mx['C0'][r]['erro_rx'] - 1 if mx['C0'][r]['erro_rx'] else 0.0
                    for r in REGIOES5}
        c4a = all(np.isfinite(p) and p <= AFASTA_FRACAO_PP / 100 + EPS for p in piora_fr.values())
        c4b = all(mx[k][r]['erro_rx'] <= (1 + CRESCE_EXTREMO) * mx['C0'][r]['erro_rx'] + EPS for r in REGIOES5)
        c4c = mp[k]['erro_p99'] <= (1 + CRESCE_EXTREMO) * mp['C0']['erro_p99'] + EPS
        det[k] = {'cond1': cond1, 'queda_mediana_pp': c0['mediana5'] - mk['mediana5'], 'cond2': cond2,
                  'anos_melhores': melhores, 'cond3': cond3, 'maior_queda_r': max(quedas.values()),
                  'c4a': c4a, 'pior_afastamento_pp': 100 * max(piora_fr.values()),
                  'c4b': c4b, 'pior_crescimento_rx': max(cresc_rx.values()),
                  'c4c': c4c, 'erro_p99': mp[k]['erro_p99'], 'erro_p99_c0': mp['C0']['erro_p99']}
        det[k]['cond4'] = c4a and c4b and c4c
        det[k]['passa'] = cond1 and cond2 and cond3 and det[k]['cond4']
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


def metricas_rad(alvo):
    """Viés dos 120 meses por região: radiação (média das diferenças) e ETo (%)."""
    out = {}
    for k in METODOS:
        out[k] = {}
        for r in REGIOES:
            rs_k, rs_b = serie(alvo, k, 'rs', r), serie(alvo, 'BR', 'rs', r)
            et_k, et_b = serie(alvo, k, 'eto', r), serie(alvo, 'BR', 'eto', r)
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
        ok_reg = all(p[0] <= PIORA_RS_MJ + EPS and p[1] <= PIORA_ETO_PP + EPS for p in piora.values())
        det[k] = {'queda_rs': queda_rs, 'queda_eto_pp': queda_et, 'pior_regiao_rs': max(p[0] for p in piora.values()),
                  'pior_regiao_eto_pp': max(p[1] for p in piora.values()),
                  'passa': queda_rs >= QUEDA_RS_MJ - EPS and queda_et >= QUEDA_ETO_PP - EPS and ok_reg}
        if det[k]['passa']:
            passam.append(k)
    return escolher(passam, {k: abs(mr[k]['Brasil']['vies_rs']) for k in passam}, DESEMPATE_RS_MJ), det


def deltas_c3(linhas_l):
    """Razão da chuva e diferença da radiação (BR - C0) por região, a partir das linhas de Y-5..Y-1 de um mês."""
    d = pd.DataFrame(linhas_l)
    razao, delta = {}, {}
    for r in REGIOES5:
        g = d[d.regiao == r] if len(d) else d
        if not len(g):
            razao[r], delta[r] = 1.0, 0.0
            continue
        pr_br, pr_c0 = g[(g.metodo == 'BR') & (g.variavel == 'pr')], g[(g.metodo == 'C0') & (g.variavel == 'pr')]
        rs_br = g[(g.metodo == 'BR') & (g.variavel == 'rs')].set_index('ano').valor
        rs_c0 = g[(g.metodo == 'C0') & (g.variavel == 'rs')].set_index('ano').valor
        razao[r] = razao_c3(pr_br.valor, pr_c0.valor)
        i = rs_br.index.intersection(rs_c0.index)
        delta[r] = float((rs_br.loc[i] - rs_c0.loc[i]).mean()) if len(i) else 0.0
    return razao, delta


def clima_pixels(agregados, a0, a1):
    """Média diária por pixel e mês na janela [a0, a1], a partir das somas mensais (pid, ano, mes, s_era, n_era, s_br, n_br)."""
    h = agregados[(agregados.ano >= a0) & (agregados.ano <= a1)]
    g = h.groupby(['pid', 'mes'])[['s_era', 'n_era', 's_br', 'n_br']].sum()
    return pd.DataFrame({'m_era': g.s_era / g.n_era.replace(0, np.nan), 'm_br': g.s_br / g.n_br.replace(0, np.nan)})


def agregar_dias(dias):
    """Somas mensais por pixel a partir dos dias (para os anos de teste entrarem nas janelas seguintes)."""
    d = dias.copy()
    d['ano'] = d.dia // 10000
    d['mes'] = d.dia // 100 % 100
    return d.groupby(['pid', 'ano', 'mes']).agg(s_era=('era', 'sum'), n_era=('era', 'count'),
                                                s_br=('br', 'sum'), n_br=('br', 'count')).reset_index()


def chuva_pixels(agregados, dias_teste, pontos, razoes):
    """Chuva diária dos 4 métodos nos pixels, nos anos de teste.
    agregados: somas mensais de 1986-2025; dias_teste: pid, dia (AAAAMMDD), era, br; pontos: pid, regiao,
    prmax_01..12; razoes: {(Y, mes, regiao): razão C3}."""
    pm = pontos.set_index('pid')
    saida = []
    for Y in ANOS_TESTE:
        x = dias_teste[dias_teste.dia // 10000 == Y].copy()
        x['mes'] = x.dia // 100 % 100
        prmax = np.array([pm.loc[p, f'prmax_{m:02d}'] for p, m in zip(x.pid, x.mes)], float)
        for k in ('C0', 'C1', 'C2'):
            cc = clima_pixels(agregados, *janela(k, Y)).reindex(list(zip(x.pid, x.mes)))
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
    # 1) todas as regiões juntas; 2) em 3 grupos de bandas; 3) região por região; 4) região por região, banda a banda
    for tentativa, (grupos, separar) in enumerate(((1, False), (3, False), (1, True), (len(bandas), True))):
        try:
            res = {}
            n = -(-len(bandas) // grupos)
            colecoes = ([E['regs'].filter(ee.Filter.eq('regiao', r)) for r in REGIOES] if separar else [E['regs']])
            for col in colecoes:
                for i in range(0, len(bandas), n):
                    fc = img.select(bandas[i:i + n]).updateMask(v.ENTREGUE).reduceRegions(
                        collection=col, reducer=ee.Reducer.mean(), crs=sp.CRS, crsTransform=sp.TRANSFORM, tileScale=16)
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


ERA5_MENSAL = 'ECMWF/ERA5_LAND/MONTHLY_AGGR'


def era_mensal_soma(img):
    """Um mês do ERA5-Land mensal como somas e contagens diárias: chuva (mm) e radiação (MJ/m², bilinear), e o número
    de dias. A média dos dias do O2 = soma do mês / dias (as duas contas são lineares; a conferência da receita prova)."""
    ee = iniciar()['ee']
    d0 = ee.Date(img.get('system:time_start'))
    n = ee.Image.constant(d0.advance(1, 'month').difference(d0, 'day')).toFloat()
    return ee.Image.cat([img.select('total_precipitation_sum').multiply(1000).max(0).rename('pr_sum'),
                         img.select('surface_solar_radiation_downwards_sum').divide(1e6).resample('bilinear')
                         .rename('Rs_sum'), n.rename('pr_count'), n.rename('Rs_count')])


def soma_conta_era(mes, a0, a1):
    ee = iniciar()['ee']
    return (ee.ImageCollection(ERA5_MENSAL).filter(ee.Filter.calendarRange(mes, mes, 'month'))
            .filterDate(f'{a0}-01-01', f'{a1 + 1}-01-01').map(era_mensal_soma).sum())


def soma_conta_br(mes, a0, a1, var):
    """BR-DWGD diário: soma e contagem dos dias válidos de uma variável (separadas, para o pedido ficar leve)."""
    E = iniciar()
    ee = E['ee']
    c = (E['m']['colChuvaGeral'].filter(ee.Filter.calendarRange(mes, mes, 'month'))
         .filterDate(f'{a0}-01-01', f'{a1 + 1}-01-01').map(lambda i: br_limpo(i).select(var)))
    return c.reduce(ee.Reducer.sum().combine(ee.Reducer.count(), sharedInputs=True))   # <var>_sum, <var>_count


def climatologias(mes, Y, metodos=('C0', 'C1', 'C2')):
    """{metodo: imagem com pr_m_br, pr_m_era, Rs_m_br, Rs_m_era} na grade do SAB (como a exportação do O2)."""
    E = iniciar()
    ee, m, sp = E['ee'], E['m'], E['sp']
    blocos = {}
    for b, (a0, a1) in pedacos(Y).items():
        if a1 >= a0 and any(b in BLOCOS[k] for k in metodos):
            blocos[b] = ({v_: soma_conta_br(mes, a0, a1, v_) for v_ in ('pr', 'Rs')}, soma_conta_era(mes, a0, a1))
    out = {}
    for k in metodos:
        bs = [b for b in BLOCOS[k] if b in blocos]
        im = []
        for fonte, i in (('br', 0), ('era', 1)):
            for var in ('pr', 'Rs'):
                fontes = [blocos[b][i][var] if fonte == 'br' else blocos[b][i] for b in bs]
                s = ee.Image.cat([x.select(f'{var}_sum') for x in fontes]).reduce(ee.Reducer.sum())
                n = ee.Image.cat([x.select(f'{var}_count') for x in fontes]).reduce(ee.Reducer.sum())
                im.append(s.divide(n).rename(f'{var}_m_{fonte}'))
        out[k] = ee.Image.cat(im).toFloat()       # a grade do SAB vem do pedido (e do expandir_borda do motor)
    return out


def imagem_regional(valores, padrao):
    """Pinta um valor por região (as 5) numa imagem; fora delas, o padrão."""
    E = iniciar()
    ee = E['ee']
    fc = E['regs5'].map(lambda f: f.set('v', ee.Dictionary(valores).get(f.get('regiao'))))
    return ee.Image.constant(padrao).toFloat().paint(fc, 'v')


def E_eqm(mes):
    E = iniciar()
    return E['ee'].Image(f"{E['m']['ASSET_EQM']}/Matriz_EQM_{mes:02d}")


def dia_metodos(d, climas, eqm, razao_img=None, delta_img=None, com_eto=True):
    """Chuva, radiação e ETo de um dia pela rota ERA5 do motor V1.7, trocando só a climatologia da chuva e da
    radiação. razao_img / delta_img: os ajustes regionais do C3 (chuva / radiação)."""
    E = iniciar()
    ee, m = E['ee'], E['m']
    c = m['_componentes_era5'](d)
    era = ee.Image(m['colecao_era5'].filterDate(ee.Date(d), ee.Date(d).advance(1, 'day')).first())
    pr_raw = era.select('total_precipitation_sum').multiply(1000).max(0)
    rs_cru = era.select('surface_solar_radiation_downwards_sum').divide(1e6)
    rs_raw = rs_cru.updateMask(rs_cru.gt(0)).resample('bilinear')
    bandas, pr0, rs0 = [], None, None

    def eto(rs):
        return m['eto_penman_monteith'](c['tmax_C'], c['tmin_C'], c['RH'], c['u2'], rs, d)

    for k, cl in climas.items():
        pr = m['teto_chuva'](m['calib_multiplicativa'](pr_raw, cl.select('pr_m_br'), cl.select('pr_m_era')).max(0),
                             pr_raw, eqm)
        rs = m['limitar_rs'](m['calib_multiplicativa'](rs_raw, cl.select('Rs_m_br'), cl.select('Rs_m_era')).max(0), d)
        if k == 'C0':
            pr0, rs0 = pr, rs
        bandas += [pr.rename(f'{k}_pr'), rs.rename(f'{k}_rs')] + ([eto(rs).rename(f'{k}_eto')] if com_eto else [])
    if razao_img is not None:
        bandas.append(pr0.multiply(razao_img).rename('C3_pr'))
    if delta_img is not None:
        rs3 = m['limitar_rs'](rs0.add(delta_img).max(0), d)
        bandas += [rs3.rename('C3_rs')] + ([eto(rs3).rename('C3_eto')] if com_eto else [])
    return ee.Image.cat(bandas).updateMask(m['MASCARA_SAB'])


def agregar_mes(col, ks, extremos=True, com_eto=True, com_rs=True):
    """Do dia para o mês: chuva (total, dias >= 1 mm, maior dia), radiação (média), ETo (total)."""
    ee = iniciar()['ee']
    pr = [f'{k}_pr' for k in ks]
    im = [col.select(pr).sum()]
    if extremos:
        im.append(col.select(pr).map(lambda i: ee.Image(i).gte(CHUVA_DIA)).sum().rename([f'{k}_wet' for k in ks]))
        im.append(col.select(pr).max().rename([f'{k}_rx' for k in ks]))
    if com_rs:
        im.append(col.select([f'{k}_rs' for k in ks]).mean())
    if com_eto:
        im.append(col.select([f'{k}_eto' for k in ks]).sum())
    return ee.Image.cat(im)


def mensal_metodos(ano, mes, climas, razao_img=None, delta_img=None, com_eto=True, extremos=True, com_rs=True):
    ee = iniciar()['ee']
    dias = [date(ano, mes, k).isoformat() for k in range(1, dias_no_mes(ano, mes) + 1)]
    col = ee.ImageCollection([dia_metodos(d, climas, E_eqm(mes), razao_img, delta_img, com_eto) for d in dias])
    ks = list(climas) + (['C3'] if razao_img is not None else [])
    return agregar_mes(col, ks, extremos=extremos, com_eto=com_eto, com_rs=com_rs)


def entregue_mensal(ano, mes, extremos=True, com_eto=True):
    E = iniciar()
    ini = date(ano, mes, 1)
    fim = (ini + timedelta(days=32)).replace(day=1)
    col = E['sp'].colecao(E['vm'].BRASIL, ini.isoformat(), fim.isoformat())
    pr = col.select('pr_mm')
    im = [pr.sum().rename('BR_pr'), col.select('rs').mean().rename('BR_rs')]
    if extremos:
        ee = E['ee']
        im += [pr.map(lambda i: ee.Image(i).gte(CHUVA_DIA)).sum().rename('BR_wet'), pr.count().rename('BR_n'),
               pr.max().rename('BR_rx')]
    if com_eto:
        im.append(col.select('et_potencial').sum().rename('BR_eto'))
    return E['ee'].Image.cat(im)


def linhas_de(res, Y, ano, mes, prefixo_ano=False):
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
                        'variavel': partes[1], 'valor': valor})
    return out


def regional_mes(Y, mes):
    """Os dois pedidos de um ano-alvo e mês: (L) o C0 e o BR-DWGD nos 5 anos anteriores, para o C3; (T) o ano-alvo."""
    E = iniciar()
    ee = E['ee']
    cl = climatologias(mes, Y)
    imgs, bandas = [], []
    for a in range(Y - ANOS_C3, Y):
        mm = mensal_metodos(a, mes, {'C0': cl['C0']}, com_eto=False, extremos=False)
        en = entregue_mensal(a, mes, extremos=False, com_eto=False)
        nomes = ['C0_pr', 'C0_rs', 'BR_pr', 'BR_rs']
        imgs.append(ee.Image.cat([mm, en]).select(nomes, [f'a{a}_{x}' for x in nomes]))
        bandas += [f'a{a}_{x}' for x in nomes]
    res_l = reduzir(ee.Image.cat(imgs), bandas, f'{Y}-{mes:02d} (anos anteriores)')
    lin_l = linhas_de(res_l, Y, None, mes, prefixo_ano=True)
    razao, delta = deltas_c3(lin_l)
    mm = mensal_metodos(Y, mes, cl, razao_img=imagem_regional(razao, 1.0), delta_img=imagem_regional(delta, 0.0))
    en = entregue_mensal(Y, mes)
    ks = METODOS
    drx = [mm.select(f'{k}_rx').subtract(en.select('BR_rx')).abs().rename(f'{k}_drx') for k in ks]
    par = ee.Image.cat([mm, en] + drx)
    nomes = ([f'{k}_{x}' for k in ks for x in ('pr', 'wet', 'rx', 'drx', 'rs', 'eto')]
             + ['BR_pr', 'BR_wet', 'BR_n', 'BR_rx', 'BR_rs', 'BR_eto'])
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


def pontos_sorteio():
    """1.500 pixels A, 300 por região (sorteio fixo), e o maior dia do BR-DWGD por mês em cada um."""
    arq = os.path.join(SAIDA, 'pixels', 'pontos.csv')
    if os.path.exists(arq):
        return pd.read_csv(arq)
    E = iniciar()
    ee, sp = E['ee'], E['sp']
    proj = ee.Projection(sp.CRS, sp.TRANSFORM)
    classe = ee.Image(sp.MASCARA).select('classe')
    idx = E['regs5'].map(lambda f: f.set('idx', ee.Number(ee.List(REGIOES5).indexOf(f.get('regiao'))).add(1)))
    estrato = ee.Image.constant(0).paint(idx, 'idx').toInt().rename('estrato')      # o sorteio exige inteiro
    estrato = estrato.updateMask(classe.eq(1).And(estrato.gt(0))).toInt()
    sorteio = (ee.Image.pixelLonLat().addBands(estrato)
               .stratifiedSample(numPoints=0, classBand='estrato', region=ee.Geometry.Rectangle(REGIAO_SORTEIO, None, False),
                                 projection=proj, seed=SEMENTE, classValues=[1, 2, 3, 4, 5],
                                 classPoints=[PONTOS_POR_REGIAO] * 5, geometries=True, tileScale=4))
    pts = [{'pid': k, 'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1],
            'regiao': REGIOES5[int(f['properties']['estrato']) - 1]}
           for k, f in enumerate(gi(sorteio, 'pontos')['features'])]
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']}) for p in pts])
    img = ee.Image.cat([E_eqm(mm).select('pr_max_br').rename(f'prmax_{mm:02d}') for mm in range(1, 13)])
    amostra = gi(img.sampleRegions(collection=fc, properties=['pid'], projection=proj, geometries=False, tileScale=16),
                 'pontos: teto da chuva')
    por = {f['properties']['pid']: f['properties'] for f in amostra['features']}
    for p in pts:
        for mm in range(1, 13):
            p[f'prmax_{mm:02d}'] = por.get(p['pid'], {}).get(f'prmax_{mm:02d}')
    df = pd.DataFrame(pts)
    os.makedirs(os.path.dirname(arq), exist_ok=True)
    df.to_csv(arq, index=False)
    print(f'   {len(df)} pixels sorteados; por região: {df.regiao.value_counts().to_dict()}', flush=True)
    return df


def _feats(pontos):
    ee = iniciar()['ee']
    return [ee.Feature(ee.Geometry.Point([lo, la]), {'pid': int(p)}) for p, lo, la in zip(pontos.pid, pontos.lon, pontos.lat)]


def agregados_pixels(ano, pontos):
    """Somas e contagens mensais da chuva do ERA5 (mensal, como a climatologia regional) e do BR-DWGD nos pixels."""
    E = iniciar()
    ee, sp, m = E['ee'], E['sp'], E['m']
    proj = ee.Projection(sp.CRS, sp.TRANSFORM)
    feats = _feats(pontos)
    linhas = []
    for meses in ([list(range(1, 13))] + [[x] for x in range(1, 13)]):
        try:
            ims = []
            for mes in meses:
                ini, fim = f'{ano}-{mes:02d}-01', (date(ano, mes, 1) + timedelta(days=32)).replace(day=1).isoformat()
                era = ee.ImageCollection(ERA5_MENSAL).filterDate(ini, fim).map(era_mensal_soma).sum()
                br = m['colChuvaGeral'].filterDate(ini, fim).map(lambda i: br_limpo(i).select('pr').rename('b'))
                ims += [era.select('pr_sum').rename(f's_era_{mes}'), era.select('pr_count').rename(f'n_era_{mes}'),
                        br.sum().rename(f's_br_{mes}'), br.count().rename(f'n_br_{mes}')]
            r = gi(ee.Image.cat(ims).sampleRegions(collection=ee.FeatureCollection(feats), properties=['pid'],
                                                   projection=proj, geometries=False, tileScale=16),
                   f'agregados {ano} {meses[0]:02d}')
            for f in r['features']:
                q = f['properties']
                for mes in meses:
                    linhas.append({'pid': q['pid'], 'ano': ano, 'mes': mes, 's_era': q.get(f's_era_{mes}'),
                                   'n_era': q.get(f'n_era_{mes}'), 's_br': q.get(f's_br_{mes}'),
                                   'n_br': q.get(f'n_br_{mes}')})
            if len(meses) == 12:
                break
        except Exception as e:  # noqa: BLE001
            if len(meses) == 12:
                print(f'   ⚠️ agregados {ano}: {str(e)[:150]} | de novo mês a mês', flush=True)
                linhas = []
                continue
            raise
    return pd.DataFrame(linhas)


def dias_pixels(ano, pontos, lote=500):
    """Anos de teste: chuva diária bruta do ERA5 e do BR-DWGD nos pixels (um pedido por mês e lote de pontos)."""
    E = iniciar()
    ee, sp, m = E['ee'], E['sp'], E['m']
    x0, y0, dx = sp.TRANSFORM[2], sp.TRANSFORM[5], sp.TRANSFORM[0]
    chave = {(int(math.floor((lo - x0) / dx + 1e-6)), int(math.floor((y0 - la) / dx + 1e-6))): int(p)
             for p, lo, la in zip(pontos.pid, pontos.lon, pontos.lat)}
    partes = {'era': [], 'br': []}
    for mes in range(1, 13):
        ini, fim = f'{ano}-{mes:02d}-01', (date(ano, mes, 1) + timedelta(days=32)).replace(day=1).isoformat()
        # ee.Image(...): no Python, copyProperties devolve um Element (o erro da K21 v3)
        cols = {'era': m['colecao_era5'].filterDate(ini, fim).map(
                    lambda i: ee.Image(i.select('total_precipitation_sum').multiply(1000).max(0).rename('v')
                                       .copyProperties(i, ['system:time_start']))),
                'br': m['colChuvaGeral'].filterDate(ini, fim).map(
                    lambda i: ee.Image(br_limpo(i).select('pr').rename('v').copyProperties(i, ['system:time_start'])))}
        for i in range(0, len(pontos), lote):
            sub = pontos.iloc[i:i + lote]
            geo = ee.Geometry.MultiPoint([[lo, la] for lo, la in zip(sub.lon, sub.lat)])
            for nome, col in cols.items():
                r = gi(ee.ImageCollection(col).getRegion(geo, None, sp.CRS, sp.TRANSFORM),
                       f'pixels {nome} {ano}-{mes:02d} lote {i // lote + 1}')
                d = pd.DataFrame(r[1:], columns=r[0])
                ix = np.floor((d.longitude.astype(float) - x0) / dx + 1e-6).astype(int)
                iy = np.floor((y0 - d.latitude.astype(float)) / dx + 1e-6).astype(int)
                d['pid'] = [chave.get((a, b)) for a, b in zip(ix, iy)]
                d['dia'] = pd.to_datetime(d['time'], unit='ms', utc=True).dt.strftime('%Y%m%d').astype(int)
                partes[nome].append(d.dropna(subset=['pid'])[['pid', 'dia', 'v']].rename(columns={'v': nome}))
    era, br = pd.concat(partes['era']), pd.concat(partes['br'])
    era['pid'], br['pid'] = era.pid.astype(int), br.pid.astype(int)
    return era.merge(br, on=['pid', 'dia'], how='left').drop_duplicates(['pid', 'dia'])


def razoes_parte_a():
    """C3 de 2026: a razão BR-DWGD / método de 2026 (= C0 com 1986-2025) em 2021-2025, da Parte A."""
    arqs = sorted(glob.glob(os.path.join(AQUI, 'resultados_metodo_2026', 'parte_a', '*.csv')))
    df = pd.concat(pd.read_csv(a) for a in arqs)
    df = df[(df.variavel == 'pr_mm') & df.ano.between(2021, 2025)]
    return {(mes, r): razao_c3(g.entregue, g.metodo_2026) for (mes, r), g in df.groupby(['mes', 'regiao'])}


def chirps_2026():
    """Só relato: a chuva de 2026 pelos quatro métodos (janelas até 2025) x CHIRPS, mesmos meses e máscara da
    validação de 2026; a régua (2024) e o 2026 gravado vêm de pesquisa/resultados_2026/validacao_2026_independente.csv."""
    arq = os.path.join(SAIDA, 'chirps_2026.csv')
    if os.path.exists(arq):
        return pd.read_csv(arq)
    E = iniciar()
    ee, v = E['ee'], E['v']
    razoes = razoes_parte_a()
    ref = pd.read_csv(os.path.join(AQUI, 'resultados_2026', 'validacao_2026_independente.csv'))
    meses = sorted(int(m) for m in ref[(ref.variavel == 'chuva_mm_mes') & (ref.ano == 2026)].mes.unique())   # int do Python (o Earth Engine recusa o do numpy)
    linhas = []
    for mes in meses:
        cl = climatologias(mes, 2026)
        ini = date(2026, mes, 1)
        fim = (ini + timedelta(days=32)).replace(day=1)
        rz = imagem_regional({r: razoes.get((mes, r), 1.0) for r in REGIOES5}, 1.0)
        mm = mensal_metodos(2026, mes, cl, razao_img=rz, com_eto=False, extremos=False, com_rs=False)
        par = ee.Image.cat([mm, v.CHIRPS.filterDate(ini.isoformat(), fim.isoformat()).sum().rename('CHIRPS_pr')])
        bandas = [f'{k}_pr' for k in METODOS] + ['CHIRPS_pr']
        res = reduzir(par.select(bandas), bandas, f'2026-{mes:02d} x CHIRPS')
        for reg, p in res.items():
            for k in METODOS + ['CHIRPS']:
                linhas.append({'ano': 2026, 'mes': mes, 'regiao': reg, 'serie': k, 'valor': p.get(f'{k}_pr')})
        print(f'   2026-{mes:02d} x CHIRPS pronto', flush=True)
    for r in ref[(ref.variavel == 'chuva_mm_mes') & ref.mes.isin(meses)].itertuples():
        linhas.append({'ano': r.ano, 'mes': r.mes, 'regiao': r.regiao,
                       'serie': 'gravado' if r.ano == 2026 else 'BR-DWGD', 'valor': r.sab})
        if r.ano == 2024:
            linhas.append({'ano': 2024, 'mes': r.mes, 'regiao': r.regiao, 'serie': 'CHIRPS', 'valor': r.referencia})
    df = pd.DataFrame(linhas)
    df.to_csv(arq, index=False)
    return df


# ============================================================ resumo
def fmt(x, nd=1, sinal=True):
    return '-' if x is None or not np.isfinite(x) else (f'{x:+.{nd}f}' if sinal else f'{x:.{nd}f}')


def pixels_prontos():
    pix = os.path.join(SAIDA, 'pixels')
    ag = [os.path.join(pix, f'agregados_{a}.csv.gz') for a in range(ANO_INICIO_CLIMA, ANOS_TESTE[-1] + 1)]
    di = [os.path.join(pix, f'dias_{a}.csv.gz') for a in ANOS_TESTE]
    return all(os.path.exists(a) for a in ag + di + [os.path.join(pix, 'pontos.csv')]), ag, di


def resumo():
    arqs = sorted(glob.glob(os.path.join(SAIDA, 'regional', '*.csv')))
    if not arqs:
        print('Nada baixado ainda.')
        return
    df = pd.concat(pd.read_csv(a) for a in arqs)
    alvo = df[df.ano == df.ano_alvo]
    completos = sorted(Y for Y, g in alvo.groupby('ano_alvo') if g.mes.nunique() == 12)
    alvo = alvo[alvo.ano_alvo.isin(completos)]
    L = ['# Correção da chuva, da radiação e da ETo nos dias ERA5: teste fora da amostra', '',
         'Protocolo aprovado e congelado antes de rodar (`pesquisa/PROTOCOLO_CORRECAO_ERA5_2026.md`, com a emenda 1: '
         'extremos em todos os pixels). Cada ano de teste é calibrado só com os anos anteriores. Referência: o que o '
         'banco entrega (BR-DWGD no núcleo), pixels entregues. Só leitura: nada foi gravado no Earth Engine.', '']
    rec = os.path.join(SAIDA, 'receita.csv')
    if os.path.exists(rec):
        r = pd.read_csv(rec)
        L += [f'Conferência da receita (média 1986-2025 recalculada × `SICSB_1986_2025`, janeiro e julho, 6 regiões, '
              f'chuva e radiação): maior diferença {100 * r.dif_rel.max():.2f}% (limite {100 * TOL_RECEITA:.0f}%).', '']
    if len(completos) < len(ANOS_TESTE):
        L += [f'**Parcial:** {len(completos)} de {len(ANOS_TESTE)} anos de teste completos ({completos}). '
              'A decisão só sai com os 10.', '']
    mc = mx = mr = mp = None
    if completos:
        mc, mx, mr = metricas_chuva(alvo), metricas_extremos(alvo), metricas_rad(alvo)
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
        L += ['', '## Dias de chuva e maior chuva do mês, em todos os pixels entregues', '',
              'Em cada célula: fração de dias com chuva (%) / erro do Rx1day (%). BR-DWGD: só a fração.', '',
              '| Método | ' + ' | '.join(REGIOES) + ' |', '|---|' + '---|' * len(REGIOES),
              '| BR-DWGD | ' + ' | '.join(f"{fmt(100 * mx['BR'][r]['fracao'], 1, False)}" for r in REGIOES) + ' |']
        for k in METODOS:
            L.append(f'| {k} | ' + ' | '.join(f"{fmt(100 * mx[k][r]['fracao'], 1, False)} / "
                                               f"{fmt(100 * mx[k][r]['erro_rx'], 1, False)}" for r in REGIOES) + ' |')
        L += ['', '## Radiação e ETo: viés nos meses de teste', '',
              '| Método | ' + ' | '.join(REGIOES) + ' |', '|---|' + '---|' * len(REGIOES)]
        for k in METODOS:
            L.append(f'| {k} | ' + ' | '.join(f"{fmt(mr[k][r]['vies_rs'], 2)} MJ / {fmt(mr[k][r]['vies_eto'])}%"
                                               for r in REGIOES) + ' |')
        L.append('')
    prontos, ag, di = pixels_prontos()
    if len(completos) == len(ANOS_TESTE) and prontos:
        pontos = pd.read_csv(os.path.join(SAIDA, 'pixels', 'pontos.csv'))
        razoes = {}
        for (Y, mes), g in df[(df.variavel == 'pr') & (df.ano < df.ano_alvo)].groupby(['ano_alvo', 'mes']):
            for r in REGIOES5:
                gr = g[g.regiao == r]
                razoes[(Y, mes, r)] = razao_c3(gr[gr.metodo == 'BR'].valor, gr[gr.metodo == 'C0'].valor)
        dias = pd.concat(pd.read_csv(a) for a in di)
        agregados = pd.concat([pd.read_csv(a) for a in ag], ignore_index=True)
        mp = metricas_pixels(chuva_pixels(agregados, dias, pontos, razoes))
        L += [f"## Percentil 99 diário em {mp['n_pixels']} pixels A ({mp['n_dias']:,} pixel-dias de 2016-2025)".replace(',', '.'),
              '', f"Fração de dias com chuva no BR-DWGD nesses pixels: {100 * mp['fracao_br']:.1f}%.", '',
              '| Método | Fração de dias com chuva (%) | Erro do percentil 99 |', '|---|---|---|']
        for k in METODOS:
            L.append(f"| {k} | {100 * mp[k]['fracao']:.1f} | {100 * mp[k]['erro_p99']:.1f}% |")
        L.append('')
        venc_c, det_c = decidir_chuva(mc, mx, mp)
        venc_r, det_r = decidir_rad(mr)
        s = {True: '✅', False: '❌'}
        L += ['## Decisão (regra fixada antes)', '', '### Chuva', '',
              '| Método | 1. mediana cai >= 3 p.p. | 2. Brasil melhora em >= 7 de 10 anos | 3. r_anom não cai > 0,02 | '
              '4a. dias de chuva (todas as regiões) | 4b. Rx1day (todas as regiões) | 4c. p99 | Passa? |',
              '|---|---|---|---|---|---|---|---|']
        for k in SIMPLICIDADE:
            d = det_c[k]
            L.append(f"| {k} | {s[d['cond1']]} {d['queda_mediana_pp']:+.2f} p.p. | {s[d['cond2']]} {d['anos_melhores']} | "
                     f"{s[d['cond3']]} maior queda {d['maior_queda_r']:+.3f} | {s[d['c4a']]} pior região "
                     f"{d['pior_afastamento_pp']:+.2f} p.p. além do C0 | {s[d['c4b']]} pior região "
                     f"{100 * d['pior_crescimento_rx']:+.1f}% | {s[d['c4c']]} {100 * d['erro_p99']:.1f}% "
                     f"(C0 {100 * d['erro_p99_c0']:.1f}%) | {s[d['passa']]} |")
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
        def v(ano, serie_):
            a = c[(c.ano == ano) & (c.regiao == r) & (c.serie == serie_)].valor.sum()
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
    # pixels primeiro (mais leves): o sorteio, as somas dos anos de climatologia e os dias dos anos de teste
    pontos = pontos_sorteio()
    tarefas = [('agregados', a) for a in range(ANO_INICIO_CLIMA, 2026)] + [('dias', a) for a in ANOS_TESTE]
    for tipo, ano in tarefas:
        arq = os.path.join(SAIDA, 'pixels', f'{tipo}_{ano}.csv.gz')
        if os.path.exists(arq):
            continue
        tempo()
        t0 = time.time()
        d = dias_pixels(ano, pontos) if tipo == 'dias' else agregados_pixels(ano, pontos)
        d.round(3).to_csv(arq, index=False)
        print(f'   pixels {tipo} {ano}: {len(d)} linhas em {(time.time() - t0) / 60:.1f} min', flush=True)
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
    tempo()
    chirps_2026()
    resumo()


if __name__ == '__main__':
    if (sys.argv[1:] or [''])[0] == 'resumo':
        resumo()
    else:
        main()
