# >>> <<NOME>>: AUDITORIA PROFUNDA DO SAB (03/11/2026). SOMENTE LEITURA. Cole inteiro numa célula do Colab, sem editar. <<<
# =========================================================================================
# v4 / K19b (03/11, 20h30): na rodada das 19h29, D2, D3, D4 e D6 terminaram; a D5 (um ano inteiro de pontos num
#   pedido) e a D1 (V1.0 no Brasil inteiro por dia) passaram da memória do Earth Engine. Agora a D5 pede um MÊS por vez
#   (e divide os pontos se ainda for pesado) e a D1 compara nos pixels sorteados (A 200, B 100, C todos, borda 50),
#   cada versão sozinha, em lotes que caem pela metade, como na K17. A K19b roda só D5 e D1.
# v3 (03/11, 19h15): a D5 passa a medir também UR, radiação e vento (corrigidos só na média em 2026, como a chuva
#   e as temperaturas) e a D3 também a ETo (máxima anual isolada).
# v2 (03/11, 19h): a v1 pedia 3 anos por vez no D2 e o servidor respondeu 429 (pedidos simultâneos demais;
#   não é a cota mensal, que estava em 0,05%). Agora vai um ano por pedido e o 429 espera 1, 2 e 3 min.
# POR QUE EXISTE
#   A K17 e a K18 provaram que os códigos reproduzem os dados e acharam duas divergências (revisão do ERA5-Land
#   desde 2017; pixels B da V1.0). A K19 procura QUALQUER outra divergência ou limitação que a literatura clássica e
#   moderna saiba corrigir, em todo o período (1961 até a previsão), numa execução só, em sequência.
#
# PARTES (cada uma é independente; o resultado é salvo e um zip parcial é feito ao fim de cada parte)
#   D2  Controle de qualidade físico em TODOS os dias do SAB_V1 (1961 até a previsão), por ano e por classe de pixel:
#       Tmax < Tmin, chuva < 0, UR fora de 0-100, ET real > ETo, transpiração > ET real, radiação acima da de céu
#       claro (Rs > 1,1 Rso, FAO-56), limites de temperatura, vento, VPD, umidade do solo, escoamento.
#       Referências: WMO-No. 1269 (2021, controle de qualidade); testes do ETCCDI; Allen et al. (1998, FAO-56).
#   D3  Consistência espacial dos extremos de cada ano (máxima da Tmax, mínima da Tmin, máximas da chuva e da ETo): pixel que
#       foge demais da mediana dos 8 vizinhos (teste espacial clássico, como Hubbard & You 2005), com o local.
#   D4  Coerência entre variáveis: a ETo gravada x a ETo FAO-56 Penman-Monteith refeita com a função do próprio motor
#       V1.5 a partir de Tmax, Tmin, UR, vento e radiação gravados; o VPD gravado x o recalculado. Mostra a costura
#       entre a ETo do BR-DWGD (até 2025) e a do motor (2026).
#   D5  A emenda 2025 -> 2026 (chuva, Tmax, Tmin, UR, radiação e vento): em 2026 o dado vem do ERA5-Land corrigido
#       só na média (escala linear, V1.5). Em 150
#       pixels A, com o BR-DWGD como verdade, mede em 2024-2025 o ERA5 bruto, o método atual e o mapeamento de
#       quantis empírico (base do QDM), treinado em 2014-2023: viés, frequência de dias com chuva, percentis 95 e 99,
#       erro diário e mensal. Referências: Teutschbein & Seibert (2012); Cannon et al. (2015, QDM).
#   D6  Homogeneidade relativa das séries (jan-set de cada ano, 1961-2026, por estado, só pixels A): SAB menos
#       ERA5-Land bruto (e SAB / CHIRPS na chuva, 1981+), com os testes de Pettitt (1979) e SNHT (Alexandersson
#       1986); e a costura de 2026 (2026 x 1996-2025, escore z). Ref.: Peterson et al. (1998, homogeneização relativa).
#   D1  Reprodução das 16 bandas pelo código: um dia por ano de 1961 a 2025 (V1.0) e o dia 15 de cada mês de 2026
#       (V1.5), no Brasil inteiro, por classe de pixel. É a mais demorada; roda por último.
#
# REGRA: a K19 não aprova nem reprova o banco. Ela lista as divergências e as CANDIDATAS A CORREÇÃO (fim do log e
#   K19_CANDIDATAS.csv), cada uma com o tipo de correção permitido: na leitura (histórico travado) ou no motor
#   (2026 em diante). Nada é corrigido aqui.
# O QUE GRAVA: NADA no Earth Engine (trava de somente leitura). Só os resultados no Colab (validacao_K19_<data>.zip).
# ANTES DE RODAR: Ambiente de execução -> Reiniciar sessão. Sem K16/K17/K18 rodando. A K19 se recusa a começar se for
#   invadir a janela do motor (14h50-16h00 e 22h50-24h00) e pausa sozinha se uma parte cair numa janela.
# TEMPO: de 1h30 a 3h (o D2 confere os 24 mil dias inteiros; o D1 refaz 75 dias no Brasil todo). Pode deixar rodando.
# =========================================================================================
import ast
import hashlib
import math
import os
import shutil
import time
import traceback
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

PROJETO = 'clima-492922'
ASSET_SAB = f'projects/{PROJETO}/assets/SAB_V1'
ASSET_MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
ASSET_CLIMA = f'projects/{PROJETO}/assets/SICSB_1986_2025'
BRDWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
CHIRPS = 'UCSB-CHG/CHIRPS/DAILY'
GAUL1 = 'FAO/GAUL/2015/level1'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
X0, Y0, DX = -73.9000015258789, 5.400000095367432, 0.09999847412109375
REGIAO_AMPLA = [-75.0, -35.0, -28.0, 6.5]
ORDEM = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2', 'tsolo_C', 'tfolha_C',
         'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm', 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
CLASSES = {1: 'A', 2: 'B', 3: 'C', 4: 'borda'}
TOL_ABS, TOL_REL, MIN_IGUAIS = 1e-3, 1e-4, 0.99
FIM_HISTORICO = '2025-12-31'
ANO_FIM = 2026
SEMENTE = 17
# [04/11/2026] o GitHub começa o motor uns 40 min depois do agendado (15h07 → ~15h47, 21 min; 23h07 → ~23h49): janelas
#   até 16h30 e 00h30
JANELAS_MOTOR = [((5, 50), (8, 30)), ((14, 50), (16, 30)), ((22, 50), (24, 0)), ((0, 0), (0, 30))]   # [04/11] + manhã (V1.6)
DURACAO_ESTIMADA_MIN = <<DURACAO>>
PARTES = <<PARTES>>              # partes desta execução (a K19b roda só D5 e D1)
# D2: testes de controle de qualidade (nome, descrição, tipo) -> 'duro' = fisicamente impossível
QC = [('tmax_lt_tmin', 'Tmax < Tmin', 'duro'), ('pr_neg', 'chuva < 0', 'duro'), ('rh_fora', 'UR fora de 0-100%', 'duro'),
      ('etr_gt_eto', 'ET real > ETo', 'duro'), ('tr_gt_etr', 'transpiração > ET real', 'duro'),
      ('etr_neg', 'ET real < 0', 'duro'), ('runoff_neg', 'escoamento < 0', 'duro'), ('vpd_neg', 'VPD < 0', 'duro'),
      ('u2_neg', 'vento < 0', 'duro'), ('rs_neg', 'radiação < 0', 'duro'),
      ('rs_gt_rso', 'radiação > 1,1 x céu claro (FAO-56)', 'suspeito'), ('tmax_gt_45', 'Tmax > 45 °C', 'suspeito'),
      ('tmin_lt_m10', 'Tmin < -10 °C', 'suspeito'), ('pr_gt_400', 'chuva > 400 mm/dia', 'suspeito'),
      ('u2_gt_15', 'vento > 15 m/s', 'suspeito'), ('tsolo_fora', 'T solo fora de -10 a 60 °C', 'suspeito'),
      ('tfolha_fora', 'T folha fora de -20 a 70 °C', 'suspeito'),
      ('solo_gt_09', 'umidade do solo bruta > 0,9 (V1.0; corrigida na leitura)', 'conhecido')]
LOTE_ANOS_D2 = 1                         # v2: um ano por pedido (3 anos juntos geravam 429)
# D3: limites do teste espacial (diferença para a mediana dos 8 vizinhos)
D3_TMAX, D3_TMIN, D3_PR_FATOR, D3_PR_MIN, D3_ETO = 4.0, 4.0, 3.0, 100.0, 3.0
# D5
N_PONTOS_D5 = 150
ANOS_TREINO_D5 = list(range(2014, 2024))
ANOS_TESTE_D5 = [2024, 2025]
VARS_D5 = ['pr', 'tmax', 'tmin', 'rh', 'rs', 'u2']
BANDAS_MATRIZ_D5 = ['pr', 'Tmax', 'Tmin', 'RH', 'Rs', 'u2']
CHUVA_DIA = 1.0                          # mm: dia com chuva (ETCCDI)
FATOR_MAX = 5.0                          # o mesmo teto do motor V1.5
# D6
MES_FIM_D6 = 9                           # janela jan-set (2026 provisório está completo até set)
ANOS_D6 = list(range(1961, ANO_FIM + 1))
P_LIMITE = 0.01
N_PERMUTACOES = 999
LOTE_ANOS_D6 = 1
# D1
PONTOS_D1 = {1: 200, 2: 100, 3: 100, 4: 50}     # v4: D1 nos pixels sorteados (C entra inteira)
LOTE_D1, LOTE_MINIMO_D1 = 200, 25
DIAS_D1 = [f'{a}-{(a % 12) + 1:02d}-15' for a in range(1961, 2026)]          # todos os meses aparecem ~5 vezes
SOMA_ERA5_A = {'et_real', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm'}
SOMA_ERA5_OUTRAS = SOMA_ERA5_A | {'pr_mm', 'et_potencial', 'rs'}

AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'validacao_K19_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K19.txt')
ACHADOS, CANDIDATAS = [], []

# ------------------------------------------------------------------ códigos embutidos, sem mudança
FONTE_V10 = r'''<<V10>>'''
FONTE_V15 = r'''<<V15>>'''
SHAS = {n: hashlib.sha256(s.encode('utf-8')).hexdigest() for n, s in (('V1.0 (O0)', FONTE_V10), ('V1.5 (05b)', FONTE_V15))}

<<CARGA>>


def log(*p):
    t = ' '.join(str(x) for x in p)
    print(t, flush=True)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(t + '\n')


def achado(parte, status, titulo, detalhe):
    icone = {'OK': '✅', 'ATENÇÃO': '⚠️', 'FALHA': '❌', 'INFO': 'ℹ️', 'NÃO EXECUTADO': '⏭️'}[status]
    ACHADOS.append({'parte': parte, 'status': status, 'titulo': titulo, 'detalhe': detalhe})
    log(f'{icone} {parte} {status}: {titulo}\n   {detalhe}')


def candidata(parte, o_que, onde_corrigir, tamanho, referencia):
    CANDIDATAS.append({'parte': parte, 'divergencia': o_que, 'correcao_permitida': onde_corrigir,
                       'tamanho': tamanho, 'referencia': referencia})


def salvar_csv(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=False, encoding='utf-8-sig')


# =========================================================================================
# FUNÇÕES PURAS (testadas offline em testes/teste_k19.py)
# =========================================================================================
def minutos_ate_janela(agora):
    """Minutos até o início da próxima janela do motor (0 se já está dentro de uma)."""
    m = agora.hour * 60 + agora.minute
    melhor = None
    for (h1, m1), (h2, m2) in JANELAS_MOTOR:
        ini, fim = h1 * 60 + m1, h2 * 60 + m2
        if ini <= m < fim:
            return 0
        falta = (ini - m) % (24 * 60)
        melhor = falta if melhor is None else min(melhor, falta)
    return melhor


def iguais_np(a, b):
    a, b = pd.to_numeric(a, errors='coerce'), pd.to_numeric(b, errors='coerce')
    d = (a - b).abs()
    return (a.isna() & b.isna()) | (d <= TOL_ABS) | (d <= TOL_REL * b.abs())


def classificar_d1(linhas, min_iguais=MIN_IGUAIS):
    """linhas: [{'data', 'classe', 'frac_<banda>'...}] (fração de pixels iguais por banda e classe).
    Devolve (tabela por dia, contagem: {'idênticos', 'só ERA5 acumulado', 'outra diferença'}, dias com outra)."""
    df = pd.DataFrame(linhas)
    saida, cont, outros = [], {'idênticos': 0, 'só ERA5 acumulado': 0, 'outra diferença': 0}, []
    for d, sub in df.groupby('data'):
        dif = {}
        for _, r in sub.iterrows():
            ruins = [b for b in ORDEM if pd.notna(r.get(f'frac_{b}')) and r.get(f'frac_{b}') < min_iguais]
            if ruins:
                dif[r['classe']] = ruins
        if not dif:
            tipo = 'idênticos'
        # [v4.1] de 2026 em diante a chuva, a ETo e a radiação dos pixels A também vêm do ERA5 (não há BR-DWGD)
        elif all(set(v) <= (SOMA_ERA5_A if (c == 'A' and d <= FIM_HISTORICO) else SOMA_ERA5_OUTRAS)
                 for c, v in dif.items()):
            tipo = 'só ERA5 acumulado'
        else:
            tipo = 'outra diferença'
            outros.append(d)
        cont[tipo] += 1
        saida.append({'data': d, 'tipo': tipo, 'bandas_diferentes': '; '.join(f'{c}: {",".join(v)}' for c, v in dif.items())})
    return pd.DataFrame(saida), cont, outros


def resumo_qc(df):
    """df: uma linha por ano e classe, colunas n (pixel-dias válidos) e uma por teste do QC (contagem).
    Devolve (status, detalhe, tabela por teste e classe com contagem e fração)."""
    linhas = []
    for nome, desc, tipo in QC:
        for cl, sub in df.groupby('classe'):
            n, k = float(sub['n'].sum()), float(sub[nome].sum()) if nome in sub else 0.0
            anos = sub[sub.get(nome, 0) > 0]['ano'].astype(int).tolist() if nome in sub else []
            linhas.append({'teste': nome, 'descricao': desc, 'tipo': tipo, 'classe': cl, 'pixel_dias': int(n),
                           'ocorrencias': int(k), 'fracao': k / n if n else 0.0,
                           'anos': (f'{min(anos)}-{max(anos)} ({len(anos)} anos)' if anos else '-')})
    tab = pd.DataFrame(linhas)
    duros = tab[(tab['tipo'] == 'duro') & (tab['ocorrencias'] > 0)]
    susp = tab[(tab['tipo'] == 'suspeito') & (tab['ocorrencias'] > 0)]
    det = (f'{int(df.groupby("ano")["n"].sum().size)} anos; '
           f'{int(tab[tab["teste"] == QC[0][0]]["pixel_dias"].sum()):,} pixel-dias conferidos'.replace(',', '.'))
    if len(duros):
        det += ' | IMPOSSÍVEIS: ' + '; '.join(f'{r.descricao} ({r.classe}): {r.ocorrencias} em {r.anos}'
                                              for r in duros.itertuples())
    if len(susp):
        det += ' | suspeitos: ' + '; '.join(f'{r.descricao} ({r.classe}): {r.ocorrencias}' for r in susp.itertuples())
    st = 'FALHA' if len(duros) else ('ATENÇÃO' if len(susp) else 'OK')
    return st, det, tab


def pettitt(x):
    """Teste de Pettitt (1979). Devolve (índice da quebra: 1º ponto do 2º trecho, K, p aproximado)."""
    x = np.asarray(x, float)
    n = len(x)
    s = np.sign(x[None, :] - x[:, None])                      # s[i, j] = sign(x_j - x_i)
    u = np.array([s[:k + 1, k + 1:].sum() for k in range(n - 1)])
    k = int(np.argmax(np.abs(u)))
    K = float(abs(u[k]))
    p = min(1.0, 2 * math.exp(-6 * K ** 2 / (n ** 3 + n ** 2)))
    return k + 1, K, p


def snht(x, n_perm=N_PERMUTACOES, semente=SEMENTE, borda=3):
    """SNHT de Alexandersson (1986) para uma quebra na média, com p por permutação (sem tabela).
    Devolve (índice da quebra: 1º ponto do 2º trecho, T0, p)."""
    x = np.asarray(x, float)
    n = len(x)

    def estat(v):
        z = (v - v.mean()) / (v.std(ddof=1) or 1.0)
        c = np.cumsum(z)
        k = np.arange(1, n)
        t = k * (c[:-1] / k) ** 2 + (n - k) * ((c[-1] - c[:-1]) / (n - k)) ** 2
        t[:borda - 1] = -1
        t[n - borda:] = -1
        return int(np.argmax(t)) + 1, float(t.max())
    k, t0 = estat(x)
    rng = np.random.default_rng(semente)
    maior = sum(estat(rng.permutation(x))[1] >= t0 for _ in range(n_perm))
    return k, t0, (maior + 1) / (n_perm + 1)


def homogeneidade(series, anos, p_lim=P_LIMITE, ano_costura=ANO_FIM, base=(1996, 2025)):
    """series: DataFrame (uf, variavel, ano, d) com d = diferença (ou razão) SAB x referência. Para cada uf e variável:
    Pettitt e SNHT na série 1961-2025 e escore z do último ano (costura) contra a base. Devolve tabela."""
    linhas = []
    for (uf, var), sub in series.groupby(['uf', 'variavel']):
        sub = sub.dropna(subset=['d']).sort_values('ano')
        hist = sub[sub['ano'] < ano_costura]
        if len(hist) < 20:
            continue
        x = hist['d'].to_numpy()
        kp, K, pp = pettitt(x)
        ks, t0, ps = snht(x)
        ref = hist[(hist['ano'] >= base[0]) & (hist['ano'] <= base[1])]['d']
        ult = sub[sub['ano'] == ano_costura]['d']
        z = float((ult.iloc[0] - ref.mean()) / (ref.std(ddof=1) or np.nan)) if len(ult) and len(ref) > 5 else np.nan
        ano_q = int(hist['ano'].iloc[ks]) if ks < len(hist) else None
        linhas.append({'uf': uf, 'variavel': var, 'n': len(x), 'pettitt_ano': int(hist['ano'].iloc[kp]), 'pettitt_p': pp,
                       'snht_ano': ano_q, 'snht_T0': t0, 'snht_p': ps,
                       'salto_snht': float(x[ks:].mean() - x[:ks].mean()),
                       'quebra': bool(pp < p_lim and ps < p_lim), f'z_{ano_costura}': z})
    return pd.DataFrame(linhas)


def agrupar_quebras(tab, janela=2, minimo=5):
    """Quebras (Pettitt e SNHT significativos) que se repetem no mesmo ano (± janela) em pelo menos 'minimo' estados."""
    q = tab[tab['quebra']]
    saida = []
    for var, sub in q.groupby('variavel'):
        anos = sub['snht_ano'].dropna().astype(int).tolist()
        for a in sorted(set(anos)):
            perto = [x for x in anos if abs(x - a) <= janela]
            if len(perto) >= minimo:
                saida.append({'variavel': var, 'ano_central': a, 'estados': len(perto),
                              'salto_medio': float(sub[sub['snht_ano'].between(a - janela, a + janela)]['salto_snht'].mean())})
    df = pd.DataFrame(saida)
    if df.empty:
        return df
    df = df.sort_values(['variavel', 'estados'], ascending=[True, False])
    return df.drop_duplicates('variavel', keep='first')


def eqm_ajustar(treino_mod, treino_obs, niveis=101):
    """Mapeamento de quantis empírico (EQM): quantis do modelo e da observação no treino."""
    q = np.linspace(0, 1, niveis)
    return np.quantile(np.asarray(treino_mod, float), q), np.quantile(np.asarray(treino_obs, float), q)


def eqm_aplicar(x, qm, qo, chuva=False):
    """Aplica o EQM; fora da faixa do treino usa a correção do quantil extremo (multiplicativa na chuva)."""
    x = np.asarray(x, float)
    y = np.interp(x, qm, qo)
    if chuva:
        alto = x > qm[-1]
        y[alto] = x[alto] * (qo[-1] / qm[-1] if qm[-1] > 0 else 1.0)
        y = np.maximum(y, 0)
    else:
        y[x > qm[-1]] = x[x > qm[-1]] + (qo[-1] - qm[-1])
        y[x < qm[0]] = x[x < qm[0]] + (qo[0] - qm[0])
    return y


def metricas_chuva(sim, obs, chave_mes):
    """Viés (%), frequência de dias com chuva (pontos percentuais), P95 e P99 (razão), erro diário, correlação e erro
    do total mensal (chave_mes agrupa ponto e mês)."""
    sim, obs = np.asarray(sim, float), np.asarray(obs, float)
    ok = ~(np.isnan(sim) | np.isnan(obs))
    sim, obs, chave = sim[ok], obs[ok], np.asarray(chave_mes)[ok]
    mens = pd.DataFrame({'k': chave, 's': sim, 'o': obs}).groupby('k').sum()
    return {'vies_pct': 100 * (sim.sum() - obs.sum()) / obs.sum(),
            'freq_chuva_sim': 100 * (sim >= CHUVA_DIA).mean(), 'freq_chuva_obs': 100 * (obs >= CHUVA_DIA).mean(),
            'erro_freq_pp': 100 * ((sim >= CHUVA_DIA).mean() - (obs >= CHUVA_DIA).mean()),
            'razao_p95': np.percentile(sim, 95) / np.percentile(obs, 95),
            'razao_p99': np.percentile(sim, 99) / np.percentile(obs, 99),
            'erro_diario_mm': float(np.abs(sim - obs).mean()), 'correlacao': float(np.corrcoef(sim, obs)[0, 1]),
            'erro_mensal_mm': float((mens['s'] - mens['o']).abs().mean())}


def metricas_continua(sim, obs, grupo):
    """Viés, razão dos desvios das anomalias (no grupo ponto-mês), P99 e P1 (diferença) e erro diário."""
    df = pd.DataFrame({'s': np.asarray(sim, float), 'o': np.asarray(obs, float), 'g': np.asarray(grupo)}).dropna()
    an_s = df['s'] - df.groupby('g')['s'].transform('mean')
    an_o = df['o'] - df.groupby('g')['o'].transform('mean')
    return {'vies': float((df['s'] - df['o']).mean()), 'razao_desvio': float(an_s.std() / an_o.std()),
            'dif_p99': float(np.percentile(df['s'], 99) - np.percentile(df['o'], 99)),
            'dif_p01': float(np.percentile(df['s'], 1) - np.percentile(df['o'], 1)),
            'erro_diario': float((df['s'] - df['o']).abs().mean()), 'correlacao': float(df['s'].corr(df['o']))}


def avaliar_d5(dados, meses_matriz):
    """dados: DataFrame pid, data (YYYY-MM-DD), era_<v> e br_<v> para v em VARS_D5 (pr, tmax, tmin, rh, rs, u2).
    meses_matriz: DataFrame pid, mes e as médias da matriz (<B>_m_br, <B>_m_era) de BANDAS_MATRIZ_D5.
    Compara, no teste (ANOS_TESTE_D5), ERA5 bruto x método atual (escala na média, V1.5) x EQM treinado em
    ANOS_TREINO_D5. Devolve (tabela de métricas, texto, é_candidata)."""
    d = dados.copy()
    d['ano'] = d['data'].str[:4].astype(int)
    d['mes'] = d['data'].str[5:7].astype(int)
    d = d.merge(meses_matriz, on=['pid', 'mes'], how='left')
    fator = (d['pr_m_br'] / d['pr_m_era'].clip(lower=1e-3)).clip(upper=FATOR_MAX)
    d['atual_pr'] = (d['era_pr'] * fator).clip(lower=0)
    # o mesmo método do motor V1.5 (_componentes_era5): aditivo em Tmax, Tmin e UR; multiplicativo (teto 5) em
    # chuva, radiação e vento
    d['atual_tmax'] = d['era_tmax'] + (d['Tmax_m_br'] - d['Tmax_m_era'])
    d['atual_tmin'] = d['era_tmin'] + (d['Tmin_m_br'] - d['Tmin_m_era'])
    d['atual_rh'] = (d['era_rh'] + (d['RH_m_br'] - d['RH_m_era'])).clip(0, 100)
    for v, b in (('rs', 'Rs'), ('u2', 'u2')):
        d[f'atual_{v}'] = (d[f'era_{v}'] * (d[f'{b}_m_br'] / d[f'{b}_m_era'].clip(lower=1e-3)).clip(upper=FATOR_MAX)).clip(lower=0)
    treino, teste = d[d['ano'].isin(ANOS_TREINO_D5)], d[d['ano'].isin(ANOS_TESTE_D5)].copy()
    for v in VARS_D5:
        teste[f'qm_{v}'] = np.nan
    for (pid, mes), sub in teste.groupby(['pid', 'mes']):
        tr = treino[(treino['pid'] == pid) & (treino['mes'] == mes)]
        if len(tr) < 60:
            continue
        for v in VARS_D5:
            t2 = tr[[f'era_{v}', f'br_{v}']].dropna()
            if len(t2) < 60:
                continue
            qm, qo = eqm_ajustar(t2[f'era_{v}'], t2[f'br_{v}'])
            teste.loc[sub.index, f'qm_{v}'] = eqm_aplicar(sub[f'era_{v}'], qm, qo, chuva=(v == 'pr'))
    chave = teste['pid'].astype(str) + '_' + teste['data'].str[:7]
    linhas = []
    for metodo, pref in (('ERA5 bruto', 'era'), ('atual (média, V1.5)', 'atual'), ('quantis (EQM)', 'qm')):
        mc = metricas_chuva(teste[f'{pref}_pr'], teste['br_pr'], chave)
        linhas.append({'variavel': 'chuva', 'metodo': metodo, **mc})
        for v in VARS_D5[1:]:
            mt = metricas_continua(teste[f'{pref}_{v}'], teste[f'br_{v}'], chave)
            linhas.append({'variavel': v, 'metodo': metodo, **mt})
    tab = pd.DataFrame(linhas)
    c = tab[tab['variavel'] == 'chuva'].set_index('metodo')
    a, q = c.loc['atual (média, V1.5)'], c.loc['quantis (EQM)']
    melhora_freq = abs(q['erro_freq_pp']) <= 0.5 * abs(a['erro_freq_pp'])
    melhora_ext = abs(q['razao_p99'] - 1) <= 0.5 * abs(a['razao_p99'] - 1)
    nao_piora = q['erro_mensal_mm'] <= 1.05 * a['erro_mensal_mm']
    cand = bool((melhora_freq or melhora_ext) and nao_piora)
    texto = (f'chuva no teste {ANOS_TESTE_D5[0]}-{ANOS_TESTE_D5[-1]} ({teste["pid"].nunique()} pixels A): dias com chuva '
             f'BR-DWGD {a["freq_chuva_obs"]:.1f}% | atual {a["freq_chuva_sim"]:.1f}% (P99 x{a["razao_p99"]:.2f}, viés '
             f'{a["vies_pct"]:+.1f}%, erro mensal {a["erro_mensal_mm"]:.1f} mm) | EQM {q["freq_chuva_sim"]:.1f}% (P99 '
             f'x{q["razao_p99"]:.2f}, viés {q["vies_pct"]:+.1f}%, erro mensal {q["erro_mensal_mm"]:.1f} mm)')
    return tab, texto, cand


# =========================================================================================
def principal():
    import ee

    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log('=' * 100)
    log(f'<<NOME>>: AUDITORIA PROFUNDA DO SAB (somente leitura), partes {", ".join(PARTES)} | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    for n, s in SHAS.items():
        log(f'   código embutido {n}: SHA-256 {s}')
    log('=' * 100)
    falta = minutos_ate_janela(AGORA)
    if falta < DURACAO_ESTIMADA_MIN:
        log(f'⛔ Não comecei: a próxima janela do motor começa em {falta} min e a K19 pode levar até '
            f'{DURACAO_ESTIMADA_MIN} min. Comece entre 16h00 e 19h50 ou entre 00h00 e 11h50.')
        return
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K19 SOMENTE LEITURA: tentativa de escrita bloqueada')

    for _n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
               'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable', 'exportVideo',
               'exportMap', 'startIngestion', 'startTableIngestion', 'cancelTask', 'cancelOperation'):
        if hasattr(ee.data, _n):
            setattr(ee.data, _n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa (criar, apagar, renomear, exportar e cancelar bloqueados).\n')

    PROJ = ee.Projection(CRS, TRANSFORM)
    REGIAO = ee.Geometry.Rectangle(REGIAO_AMPLA, None, False)
    CLASSE = ee.Image(ASSET_MASCARA).select('classe').unmask(0).toInt().rename('classe')
    COL = ee.ImageCollection(ASSET_SAB)
    BRCOL = ee.ImageCollection(BRDWGD)
    ERACOL = ee.ImageCollection(ERA5)
    LONLAT = ee.Image.pixelLonLat()
    ELEV = ee.Image('USGS/SRTMGL1_003')
    UFS = ee.FeatureCollection(GAUL1).filter(ee.Filter.eq('ADM0_NAME', 'Brazil')).select(['ADM1_NAME'])
    estado = {}

    class Pesado(RuntimeError):
        pass

    def gi(obj, rotulo, tentativas=4):
        for k in range(tentativas):
            try:
                return obj.getInfo()
            except Exception as e:
                msg = str(e)
                if any(x in msg.lower() for x in ('memory limit', 'timed out', 'too large')):
                    raise Pesado(f'{rotulo}: {msg[:300]}')
                if k == tentativas - 1:
                    raise RuntimeError(f'{rotulo}: {msg[:300]}')
                # [v2] 429 = pedidos simultâneos demais (não é cota): espera mais antes de tentar de novo
                limite = '429' in msg or 'too many' in msg.lower()
                if limite:
                    log(f'   ↻ {rotulo}: servidor ocupado (429); nova tentativa em {60 * (k + 1)} s')
                time.sleep(60 * (k + 1) if limite else 20)

    def em_lotes(itens, montar, rotulo, lote):
        """montar(item) -> ee.Feature. Pede 'lote' itens por vez; lote recusado vai um por um."""
        linhas, sem = [], []
        for k in range(0, len(itens), lote):
            parte = itens[k:k + lote]
            try:
                linhas += [f['properties'] for f in gi(ee.FeatureCollection([montar(i) for i in parte]),
                                                       f'{rotulo} {parte[0]}', tentativas=2)['features']]
            except Exception:
                for i in parte:
                    try:
                        linhas += [f['properties'] for f in gi(ee.FeatureCollection([montar(i)]), f'{rotulo} {i}')['features']]
                    except Exception as e:
                        sem.append(i)
                        log(f'   {rotulo} {i}: não calculado ({str(e)[:150]})')
            log(f'   {rotulo}: {parte[0]} a {parte[-1]} ok')
        return linhas, sem

    def zip_parcial():
        try:
            pd.DataFrame(ACHADOS).to_csv(os.path.join(PASTA, 'K19_RESUMO.csv'), sep=';', index=False, encoding='utf-8-sig')
            pd.DataFrame(CANDIDATAS).to_csv(os.path.join(PASTA, 'K19_CANDIDATAS.csv'), sep=';', index=False,
                                            encoding='utf-8-sig')
            shutil.make_archive(PASTA, 'zip', PASTA)
        except Exception as e:
            log(f'   (zip parcial não feito: {e})')

    def parte(nome):
        def deco(fn):
            def rodar():
                while minutos_ate_janela(datetime.now(timezone(timedelta(hours=-3)))) == 0:
                    log('   ⏸️ janela do motor: pausa de 5 min')
                    time.sleep(300)
                log(f'\n{"-" * 100}\n{nome}\n{"-" * 100}')
                t = time.time()
                try:
                    fn()
                except Exception as e:
                    achado(nome.split()[0], 'NÃO EXECUTADO', nome, f'{type(e).__name__}: {str(e)[:400]}')
                    log(traceback.format_exc()[-1500:])
                log(f'   ({(time.time() - t) / 60:.1f} min)')
                zip_parcial()
            return rodar
        return deco

    carga = {}
    for nome, fonte, precisa in (('v10', FONTE_V10, ['processarDia_Definitivo']),
                                 ('v15', FONTE_V15, ['processarDia_Rota1', 'eto_penman_monteith', 'vpd_e_ea'])):
        carga[nome], pulados = carregar_codigo(nome, fonte, precisa, ee)
        log(f'   código {nome}: carregado ({len(pulados)} trecho(s) do fluxo principal ignorados)')

    def ra_mj(img_data):
        """Radiação no topo da atmosfera do dia (FAO-56, eq. 21), MJ/m²/dia, por pixel."""
        J = ee.Number(ee.Date(img_data).getRelative('day', 'year')).add(1)
        lat = LONLAT.select('latitude').multiply(math.pi / 180)
        dr = J.multiply(2 * math.pi / 365).cos().multiply(0.033).add(1)
        dec = J.multiply(2 * math.pi / 365).subtract(1.39).sin().multiply(0.409)
        ws = lat.tan().multiply(dec.tan()).multiply(-1).clamp(-1, 1).acos()
        return (ws.multiply(lat.sin()).multiply(dec.sin()).add(lat.cos().multiply(dec.cos()).multiply(ws.sin()))
                .multiply(dr).multiply(24 * 60 / math.pi * 0.0820))

    # ---------------------------------------------------------------------------------- D2 + D3
    @parte('D2 Controle de qualidade físico em todos os dias (por ano e classe) e D3 consistência espacial dos extremos')
    def d2_d3():
        nomes = [q[0] for q in QC]

        def bandeiras(img):
            g = img.select
            rso = ra_mj(img.get('system:time_start')).multiply(ELEV.multiply(2e-5).add(0.75))
            b = {
                'tmax_lt_tmin': g('tmax_C').lt(g('tmin_C')), 'pr_neg': g('pr_mm').lt(0),
                'rh_fora': g('RH').lt(0).Or(g('RH').gt(100.001)),
                'etr_gt_eto': g('et_real').gt(g('et_potencial').add(0.001)),
                'tr_gt_etr': g('transpiracao_mm').gt(g('et_real').add(0.001)), 'etr_neg': g('et_real').lt(0),
                'runoff_neg': g('runoff_sup_mm').lt(0).Or(g('runoff_sub_mm').lt(0)), 'vpd_neg': g('vpd').lt(0),
                'u2_neg': g('u2').lt(0), 'rs_neg': g('rs').lt(0), 'rs_gt_rso': g('rs').gt(rso.multiply(1.1)),
                'tmax_gt_45': g('tmax_C').gt(45), 'tmin_lt_m10': g('tmin_C').lt(-10), 'pr_gt_400': g('pr_mm').gt(400),
                'u2_gt_15': g('u2').gt(15), 'tsolo_fora': g('tsolo_C').lt(-10).Or(g('tsolo_C').gt(60)),
                'tfolha_fora': g('tfolha_C').lt(-20).Or(g('tfolha_C').gt(70)),
                'solo_gt_09': g('soil_moisture_0_5cm_m3_m3').gt(0.9001).Or(g('soil_moisture_0_100cm_m3_m3').gt(0.9001)),
            }
            validos = g('tmax_C').mask().rename('n')
            return ee.Image.cat([b[n].rename(n) for n in nomes] + [validos]).unmask(0).toInt()

        def montar(ano):
            col = COL.filterDate(f'{ano}-01-01', f'{ano + 1}-01-01')
            soma = col.map(bandeiras).sum()
            red = ee.Reducer.sum().unweighted().repeat(len(nomes) + 1).group(groupField=len(nomes) + 1, groupName='classe')
            qc = soma.addBands(CLASSE).reduceRegion(reducer=red, geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM,
                                                    maxPixels=1e10, tileScale=4)
            dentro = CLASSE.gte(1).And(CLASSE.lte(3))
            tmax = col.select('tmax_C').max()
            tmin = col.select('tmin_C').min()
            pr = col.select('pr_mm').max()
            eto = col.select('et_potencial').max()

            def ext(img, red_):
                return ee.Image.cat([img, LONLAT]).updateMask(dentro).reduceRegion(
                    reducer=red_, geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4)

            def mediana(img):
                return img.reproject(crs=CRS, crsTransform=TRANSFORM).focalMedian(1, 'square', 'pixels')
            out_tmax = tmax.subtract(mediana(tmax)).gt(D3_TMAX)
            out_tmin = mediana(tmin).subtract(tmin).gt(D3_TMIN)
            med_pr = mediana(pr)
            out_pr = pr.gt(med_pr.multiply(D3_PR_FATOR)).And(pr.subtract(med_pr).gt(D3_PR_MIN))
            out_eto = eto.subtract(mediana(eto)).gt(D3_ETO)
            red3 = ee.Reducer.sum().unweighted().repeat(4).group(groupField=4, groupName='classe')
            d3 = (ee.Image.cat([out_tmax, out_tmin, out_pr, out_eto]).unmask(0).toInt().addBands(CLASSE)
                  .reduceRegion(reducer=red3, geometry=REGIAO, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e10,
                                tileScale=4))
            return ee.Feature(None, {
                'ano': ano, 'n_dias': col.size(), 'qc': qc.get('groups'), 'd3': d3.get('groups'),
                'tmax_max': ext(tmax, ee.Reducer.max(3)), 'tmin_min': ext(tmin, ee.Reducer.min(3)),
                'pr_max': ext(pr, ee.Reducer.max(3)), 'eto_max': ext(eto, ee.Reducer.max(3)),
                'tmax_dif_max': ext(tmax.subtract(mediana(tmax)), ee.Reducer.max(3)),
                'pr_dif_max': ext(pr.subtract(med_pr), ee.Reducer.max(3))})

        linhas, sem = em_lotes(list(range(1961, ANO_FIM + 1)), montar, 'D2', LOTE_ANOS_D2)
        qc_linhas, d3_linhas, ext_linhas = [], [], []
        for p in linhas:
            for g in p.get('qc') or []:
                vals = g.get('sum', [])
                qc_linhas.append({'ano': p['ano'], 'classe': CLASSES.get(int(g['classe']), 'sem classe'),
                                  **dict(zip(nomes + ['n'], vals))})
            for g in p.get('d3') or []:
                v = list(g.get('sum', [])) + [0, 0, 0, 0]
                d3_linhas.append({'ano': p['ano'], 'classe': CLASSES.get(int(g['classe']), 'sem classe'),
                                  'tmax_isolada': v[0], 'tmin_isolada': v[1], 'chuva_isolada': v[2], 'eto_isolada': v[3]})
            e = {'ano': p['ano'], 'n_dias': p.get('n_dias')}
            for chave, pref in (('tmax_max', 'max'), ('tmin_min', 'min'), ('pr_max', 'max'), ('eto_max', 'max'),
                                ('tmax_dif_max', 'max'),
                                ('pr_dif_max', 'max')):
                dct = p.get(chave) or {}
                e[chave], e[f'{chave}_lon'], e[f'{chave}_lat'] = dct.get(pref), dct.get(f'{pref}1'), dct.get(f'{pref}2')
            ext_linhas.append(e)
        qc = pd.DataFrame(qc_linhas)
        qc = qc[qc['classe'] != 'sem classe']
        salvar_csv(qc, 'D2_qc_por_ano_e_classe.csv')
        ext = pd.DataFrame(ext_linhas).sort_values('ano')
        salvar_csv(ext, 'D3_extremos_por_ano.csv')
        d3 = pd.DataFrame(d3_linhas)
        salvar_csv(d3, 'D3_pixels_isolados_por_ano.csv')
        st, det, tab = resumo_qc(qc[qc['classe'] != 'borda'])
        salvar_csv(tab, 'D2_qc_resumo.csv')
        log(tab[tab['ocorrencias'] > 0].to_string(index=False) if (tab['ocorrencias'] > 0).any() else '   nenhuma ocorrência')
        achado('D2', st, 'Controle de qualidade físico (todos os dias; classes A, B e C)',
               det + (f' | anos não calculados: {sem}' if sem else ''))
        for r in tab[(tab['ocorrencias'] > 0) & (tab['tipo'] != 'conhecido')].itertuples():
            candidata('D2', f'{r.descricao} nos pixels {r.classe}: {r.ocorrencias} pixel-dias ({r.anos})',
                      'na leitura (histórico) ou no motor (2026+), conforme o ano' if r.tipo == 'duro'
                      else 'conferir o local e decidir (pode ser real)', f'{100 * r.fracao:.4f}% dos pixel-dias',
                      'WMO-No. 1269; FAO-56' if 'radiação' in r.descricao else 'WMO-No. 1269; ETCCDI')
        # D3
        log(ext[['ano', 'tmax_max', 'tmin_min', 'pr_max', 'eto_max', 'tmax_dif_max', 'pr_dif_max']].to_string(index=False))
        iso = (d3[d3['classe'] == 'A'][['tmax_isolada', 'tmin_isolada', 'chuva_isolada', 'eto_isolada']].sum()
               if len(d3) else None)
        det3 = (f'Tmax máxima do acervo {ext["tmax_max"].max():.1f} °C, Tmin mínima {ext["tmin_min"].min():.1f} °C, '
                f'chuva máxima {ext["pr_max"].max():.0f} mm/dia, ETo máxima {ext["eto_max"].max():.1f} mm/dia')
        if iso is not None:
            det3 += (f' | máximos anuais isolados nos pixels A (foge da mediana dos vizinhos): Tmax {int(iso["tmax_isolada"])}, '
                     f'Tmin {int(iso["tmin_isolada"])}, chuva {int(iso["chuva_isolada"])}, ETo {int(iso["eto_isolada"])} '
                     f'pixel-anos')
        st3 = 'ATENÇÃO' if iso is not None and iso.sum() > 0 else 'OK'
        achado('D3', st3, 'Consistência espacial dos extremos anuais', det3)
        if iso is not None and iso.sum() > 0:
            pior = ext.sort_values('tmax_dif_max', ascending=False).iloc[0]
            candidata('D3', f'máximos anuais isolados nos pixels A (Tmax {int(iso["tmax_isolada"])}, Tmin '
                      f'{int(iso["tmin_isolada"])}, chuva {int(iso["chuva_isolada"])}, ETo {int(iso["eto_isolada"])}); '
                      f'maior Tmax isolada em '
                      f'{int(pior["ano"])} ({pior["tmax_dif_max_lon"]:.2f}, {pior["tmax_dif_max_lat"]:.2f})',
                      'conferir caso a caso (pode ser real); se erro, na leitura', 'ver D3_*.csv',
                      'teste espacial (Hubbard & You 2005); WMO-No. 1269')

    # ---------------------------------------------------------------------------------- D4
    @parte('D4 Coerência: ETo gravada x FAO-56 Penman-Monteith do motor; VPD gravado x recalculado')
    def d4():
        dias = DIAS_D1 + [f'2026-{m:02d}-15' for m in range(1, 11)]
        A = CLASSE.eq(1)

        def montar(d):
            s = ee.Image(f'{ASSET_SAB}/SAB_{d.replace("-", "_")}')
            g = s.select
            eto = ee.Image(carga['v15']['eto_penman_monteith'](g('tmax_C'), g('tmin_C'), g('RH'), g('u2'), g('rs'), d))
            vpd = ee.Image(carga['v15']['vpd_e_ea'](g('tmax_C'), g('tmin_C'), g('RH'))[0])
            img = ee.Image.cat([eto.subtract(g('et_potencial')).rename('dif_eto'),
                                eto.subtract(g('et_potencial')).abs().rename('abs_eto'),
                                g('et_potencial').rename('eto_sab'), eto.rename('eto_pm'),
                                vpd.subtract(g('vpd')).abs().rename('abs_vpd')]).updateMask(A)
            return ee.Feature(None, img.reduceRegion(reducer=ee.Reducer.mean(), geometry=REGIAO, crs=CRS,
                                                     crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4)).set('data', d)

        linhas, sem = em_lotes(dias, montar, 'D4', 8)
        df = pd.DataFrame(linhas).sort_values('data')
        df['periodo'] = np.where(df['data'] <= FIM_HISTORICO, 'histórico (ETo do BR-DWGD)', '2026 (ETo do motor)')
        df['dif_pct'] = 100 * df['dif_eto'] / df['eto_sab']
        salvar_csv(df, 'D4_eto_vpd_por_dia.csv')
        res = df.groupby('periodo').agg(dias=('data', 'size'), eto_sab=('eto_sab', 'mean'), eto_pm=('eto_pm', 'mean'),
                                        dif_media=('dif_eto', 'mean'), dif_pct=('dif_pct', 'mean'),
                                        abs_media=('abs_eto', 'mean'), vpd_abs=('abs_vpd', 'mean')).reset_index()
        df['decada'] = df['data'].str[:3] + '0s'
        dec = df[df['data'] <= FIM_HISTORICO].groupby('decada').agg(dif_pct=('dif_pct', 'mean'),
                                                                     abs_media=('abs_eto', 'mean')).reset_index()
        salvar_csv(res, 'D4_resumo.csv')
        salvar_csv(dec, 'D4_por_decada.csv')
        log(res.to_string(index=False))
        log(dec.to_string(index=False))
        h = res[res['periodo'].str.startswith('histórico')].iloc[0]
        n26 = res[res['periodo'].str.startswith('2026')]
        det = (f'histórico (pixels A): ETo BR-DWGD {h.eto_sab:.2f} x FAO-56 do motor {h.eto_pm:.2f} mm/dia '
               f'({h.dif_pct:+.1f}%, erro médio {h.abs_media:.2f} mm/dia); VPD recalculado difere {h.vpd_abs:.4f} kPa')
        if len(n26):
            det += f' | 2026: diferença {n26.iloc[0].abs_media:.4f} mm/dia (o motor grava esta mesma conta)'
        salto = abs(h.dif_pct)
        st = 'ATENÇÃO' if salto > 3 or h.vpd_abs > 0.01 else 'OK'
        achado('D4', st, 'ETo e VPD coerentes com as outras variáveis', det + (f' | não calculados: {sem}' if sem else ''))
        if salto > 3:
            candidata('D4', f'a ETo do motor (2026, FAO-56 com a meteorologia) difere {h.dif_pct:+.1f}% da ETo do BR-DWGD '
                      f'para as mesmas variáveis: degrau na emenda 2025/2026',
                      'no motor (2026+): calibrar a ETo do motor contra a do BR-DWGD (matriz mensal) ou usar a mesma '
                      'formulação do BR-DWGD', f'{h.dif_pct:+.1f}%', 'Allen et al. 1998 (FAO-56); Xavier et al. 2022')

    # ---------------------------------------------------------------------------------- D5
    @parte('D5 Emenda 2025 -> 2026: ERA5 bruto x método atual x mapeamento de quantis, com o BR-DWGD como verdade')
    def d5():
        sorteio = (ee.Image.pixelLonLat().addBands(CLASSE)
                   .stratifiedSample(numPoints=0, classBand='classe', region=REGIAO, projection=PROJ, seed=SEMENTE,
                                     classValues=[1], classPoints=[N_PONTOS_D5], geometries=True, tileScale=4))
        pts = [{'pid': k, 'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1]}
               for k, f in enumerate(gi(sorteio, 'pontos D5')['features'])]
        chave = {(int(math.floor((p['lon'] - X0) / DX + 1e-6)), int(math.floor((Y0 - p['lat']) / DX + 1e-6))): p['pid']
                 for p in pts}
        salvar_csv(pd.DataFrame(pts), 'D5_pontos.csv')
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']}) for p in pts])
        mp = ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in pts])
        # médias mensais da matriz que o motor usa (SICSB_1986_2025)
        bandas = [f'{b}_m_{f}' for b in BANDAS_MATRIZ_D5 for f in ('br', 'era')]
        mats = ee.Image.cat([ee.Image(f'{ASSET_CLIMA}/Matriz_Clima_{m:02d}').select(bandas)
                             .rename([f'{b}__{m}' for b in bandas]) for m in range(1, 13)])
        am = gi(mats.sampleRegions(collection=fc, properties=['pid'], projection=PROJ, geometries=False), 'matriz D5')
        mm = []
        for f in am['features']:
            p = f['properties']
            for m in range(1, 13):
                mm.append({'pid': p['pid'], 'mes': m, **{b: p.get(f'{b}__{m}') for b in bandas}})
        meses_matriz = pd.DataFrame(mm)

        def era_prep(img):
            # as mesmas conversões do motor V1.5 (_componentes_era5), antes da calibração
            t2 = img.select('temperature_2m').subtract(273.15).resample('bilinear')
            td = img.select('dewpoint_temperature_2m').subtract(273.15).resample('bilinear')
            rh = t2.expression('100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))',
                               {'T': t2, 'Td': td})
            return ee.Image.cat([img.select('total_precipitation_sum').multiply(1000).max(0).rename('era_pr'),
                                 img.select('temperature_2m_max').subtract(273.15).resample('bilinear').rename('era_tmax'),
                                 img.select('temperature_2m_min').subtract(273.15).resample('bilinear').rename('era_tmin'),
                                 rh.rename('era_rh'),
                                 img.select('surface_solar_radiation_downwards_sum').divide(1e6).resample('bilinear')
                                 .rename('era_rs'),
                                 img.select('u_component_of_wind_10m').hypot(img.select('v_component_of_wind_10m'))
                                 .multiply(0.748).resample('bilinear').rename('era_u2')]
                                ).copyProperties(img, ['system:time_start'])

        def br_prep(img):
            # decodificação do BR-DWGD como na V1.0
            m = img.select('pr').gt(-32768)
            dec = lambda b, e, a: img.select(b).updateMask(m).multiply(e).add(a)
            return ee.Image.cat([dec('pr', 0.00686666, 225.0).max(0).rename('br_pr'),
                                 dec('Tmax', 0.00106815, 15.0).rename('br_tmax'),
                                 dec('Tmin', 0.00106815, 15.0).rename('br_tmin'),
                                 dec('RH', 0.39370079, -0.393701).clamp(0, 100).rename('br_rh'),
                                 dec('Rs', 0.15708661, -0.057087).rename('br_rs'),
                                 dec('u2', 0.05905512, -0.059055).rename('br_u2')]
                                ).copyProperties(img, ['system:time_start'])

        def regiao(ini, fim, lista, rotulo):
            """[v4] getRegion de UM mês; se pesado, divide os pontos ao meio (até 10 por pedido)."""
            par = ee.Join.inner().apply(ERACOL.filterDate(ini, fim).map(lambda i: ee.Image(era_prep(i))),
                                        BRCOL.filterDate(ini, fim).map(lambda i: ee.Image(br_prep(i))),
                                        ee.Filter.maxDifference(difference=12 * 3600 * 1000, leftField='system:time_start',
                                                                rightField='system:time_start'))
            junto = ee.ImageCollection(par.map(lambda f: ee.Image.cat([ee.Image(f.get('primary')),
                                                                       ee.Image(f.get('secondary'))])
                                               .set('system:time_start', ee.Image(f.get('primary')).get('system:time_start'))))
            try:
                reg = gi(junto.getRegion(ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in lista]), None, CRS,
                                         TRANSFORM), rotulo)
                return [reg[0]] + reg[1:]
            except Pesado:
                if len(lista) <= 10:
                    raise
                meio = len(lista) // 2
                log(f'   {rotulo}: pesado, dividindo os pontos ({len(lista)} -> {meio} + {len(lista) - meio})')
                a, b = regiao(ini, fim, lista[:meio], rotulo), regiao(ini, fim, lista[meio:], rotulo)
                return a + b[1:]

        quadros = []
        for ano in ANOS_TREINO_D5 + ANOS_TESTE_D5:
            linhas_ano, cab = [], None
            for mes in range(1, 13):
                ini = f'{ano}-{mes:02d}-01'
                fim = f'{ano + 1}-01-01' if mes == 12 else f'{ano}-{mes + 1:02d}-01'
                reg = regiao(ini, fim, pts, f'D5 {ano}-{mes:02d}')
                cab = reg[0]
                linhas_ano += reg[1:]
            df = pd.DataFrame(linhas_ano, columns=cab)
            ix = np.floor((df['longitude'].astype(float) - X0) / DX + 1e-6).astype(int)
            iy = np.floor((Y0 - df['latitude'].astype(float)) / DX + 1e-6).astype(int)
            df['pid'] = [chave.get((a, b)) for a, b in zip(ix, iy)]
            df['data'] = pd.to_datetime(df['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
            df = df.dropna(subset=['pid'])
            quadros.append(df[['pid', 'data'] + [f'era_{v}' for v in VARS_D5] + [f'br_{v}' for v in VARS_D5]])
            log(f'   D5 {ano}: {len(df)} pixel-dias')
        dados = pd.concat(quadros, ignore_index=True)
        dados['pid'] = dados['pid'].astype(int)
        tab, texto, cand = avaliar_d5(dados, meses_matriz)
        salvar_csv(tab, 'D5_metricas_teste_2024_2025.csv')
        log(tab.to_string(index=False))
        achado('D5', 'ATENÇÃO' if cand else 'INFO',
               'Emenda 2025/2026 (chuva, Tmax, Tmin, UR, radiação, vento): correção só na média x mapeamento de quantis', texto)
        if cand:
            candidata('D5', 'nos dias de 2026 (ERA5 corrigido só na média) a frequência de dias com chuva e/ou os extremos '
                      'ficam longe do BR-DWGD; o mapeamento de quantis reduz o erro sem piorar o total mensal',
                      'no motor, só 2026 em diante (V1.6), com simulação e validação fora da amostra antes',
                      texto.split('|', 1)[1].strip() if '|' in texto else texto,
                      'Teutschbein & Seibert 2012; Cannon et al. 2015 (QDM)')
        t = tab[tab['variavel'] != 'chuva'].set_index(['variavel', 'metodo'])
        nomes_v = {'tmax': 'Tmax', 'tmin': 'Tmin', 'rh': 'UR', 'rs': 'radiação', 'u2': 'vento'}
        for v in VARS_D5[1:]:
            a, q = t.loc[(v, 'atual (média, V1.5)')], t.loc[(v, 'quantis (EQM)')]
            log(f'   {nomes_v[v]}: atual viés {a["vies"]:+.2f}, desvios x{a["razao_desvio"]:.2f}, erro diário '
                f'{a["erro_diario"]:.2f} | EQM viés {q["vies"]:+.2f}, desvios x{q["razao_desvio"]:.2f}, erro diário '
                f'{q["erro_diario"]:.2f}')
            if abs(a['razao_desvio'] - 1) > 0.15:
                candidata('D5', f'{nomes_v[v]} de 2026: a amplitude das anomalias diárias é {a["razao_desvio"]:.2f}x a do '
                          f'BR-DWGD (a correção só na média não ajusta a variância)',
                          'no motor, só 2026 em diante (escala de variância, como na previsão GFS desde a K8, ou EQM)',
                          f'razão dos desvios {a["razao_desvio"]:.2f} (EQM: {q["razao_desvio"]:.2f})',
                          'Teutschbein & Seibert 2012; K8')
            if abs(a['vies']) > {'tmax': 0.5, 'tmin': 0.5, 'rh': 3.0, 'rs': 1.0, 'u2': 0.3}[v]:
                candidata('D5', f'{nomes_v[v]} de 2026: viés de {a["vies"]:+.2f} contra o BR-DWGD em 2024-2025, mesmo com '
                          f'a correção na média', 'no motor, só 2026 em diante', f'viés {a["vies"]:+.2f}',
                          'Teutschbein & Seibert 2012')

    # ---------------------------------------------------------------------------------- D6
    @parte('D6 Homogeneidade relativa (SAB x ERA5-Land e x CHIRPS, por estado, jan-set de 1961 a 2026) e costura de 2026')
    def d6():
        A = CLASSE.eq(1)
        vars_s = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'rs', 'u2', 'et_real']
        soma = {'pr_mm', 'et_real'}

        def era_dia(img):
            t2 = img.select('temperature_2m').subtract(273.15)
            td = img.select('dewpoint_temperature_2m').subtract(273.15)
            rh = t2.expression('100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))',
                               {'T': t2, 'Td': td})
            return ee.Image.cat([
                img.select('total_precipitation_sum').multiply(1000).max(0).rename('pr_mm'),
                img.select('temperature_2m_max').subtract(273.15).rename('tmax_C'),
                img.select('temperature_2m_min').subtract(273.15).rename('tmin_C'), rh.rename('RH'),
                img.select('surface_solar_radiation_downwards_sum').divide(1e6).rename('rs'),
                img.select('u_component_of_wind_10m').hypot(img.select('v_component_of_wind_10m')).multiply(0.748).rename('u2'),
                img.select('total_evaporation_sum').multiply(-1000).max(0).rename('et_real')])

        def agrega(col):
            return ee.Image.cat([col.select(v).sum() if v in soma else col.select(v).mean() for v in vars_s])

        def montar(ano):
            ini, fim = ee.Date.fromYMD(ano, 1, 1), ee.Date.fromYMD(ano, MES_FIM_D6 + 1, 1)
            s = agrega(COL.filterDate(ini, fim).select(vars_s)).rename([f's_{v}' for v in vars_s])
            r = agrega(ERACOL.filterDate(ini, fim).map(era_dia)).rename([f'r_{v}' for v in vars_s])
            fc = ee.Image.cat([s, r]).updateMask(A).reduceRegions(collection=UFS, reducer=ee.Reducer.mean(), crs=CRS,
                                                                   crsTransform=TRANSFORM, tileScale=4)
            if ano >= 1981:
                ch = ee.ImageCollection(CHIRPS).filterDate(ini, fim).select('precipitation').sum().rename('c_pr')
                fc = ch.updateMask(A).reduceRegions(collection=fc, reducer=ee.Reducer.mean().setOutputs(['c_pr']),
                                                    scale=5566, tileScale=4)
            return ee.Feature(None, {'ano': ano, 'ufs': fc.toList(40).map(lambda f: ee.Feature(f).toDictionary())})

        linhas, sem = em_lotes(ANOS_D6, montar, 'D6', LOTE_ANOS_D6)
        reg = []
        for p in linhas:
            for u in p.get('ufs') or []:
                reg.append({'ano': p['ano'], 'uf': u.get('ADM1_NAME'), **{k: v for k, v in u.items() if k != 'ADM1_NAME'}})
        bruto = pd.DataFrame(reg)
        salvar_csv(bruto, 'D6_series_por_estado.csv')
        series = []
        for v in vars_s:
            if f's_{v}' not in bruto:
                continue
            if v in soma:
                d = bruto[f's_{v}'] / bruto[f'r_{v}'].replace(0, np.nan)
            else:
                d = bruto[f's_{v}'] - bruto[f'r_{v}']
            series.append(pd.DataFrame({'uf': bruto['uf'], 'ano': bruto['ano'], 'variavel': f'{v} (SAB x ERA5)', 'd': d}))
        if 'c_pr' in bruto:
            series.append(pd.DataFrame({'uf': bruto['uf'], 'ano': bruto['ano'], 'variavel': 'pr_mm (SAB / CHIRPS)',
                                        'd': bruto['s_pr_mm'] / bruto['c_pr'].replace(0, np.nan)}))
        series = pd.concat(series, ignore_index=True)
        tab = homogeneidade(series, ANOS_D6)
        salvar_csv(tab, 'D6_homogeneidade_por_estado.csv')
        grupos = agrupar_quebras(tab)
        salvar_csv(grupos, 'D6_quebras_em_varios_estados.csv')
        zc = f'z_{ANO_FIM}'
        cost = tab[tab[zc].abs() > 3]
        cost_v = cost.groupby('variavel').size().to_dict()
        log(grupos.to_string(index=False) if len(grupos) else '   nenhuma quebra repetida em 5 ou mais estados')
        det = (f'{len(tab)} séries (estado x variável); {int(tab["quebra"].sum())} com quebra (Pettitt e SNHT, p < {P_LIMITE}) | '
               + ('quebras repetidas: ' + '; '.join(f'{r.variavel} ~{r.ano_central} em {r.estados} estados (salto '
                                                    f'{r.salto_medio:+.3f})' for r in grupos.itertuples())
                  if len(grupos) else 'nenhuma quebra repetida em 5+ estados')
               + f' | costura {ANO_FIM} (|z| > 3): ' + (', '.join(f'{k}: {v} estados' for k, v in cost_v.items())
                                                      if cost_v else 'nenhuma'))
        st = 'ATENÇÃO' if len(grupos) or cost_v else 'OK'
        achado('D6', st, 'Homogeneidade das séries e costura de 2026', det + (f' | anos não calculados: {sem}' if sem else ''))
        for r in grupos.itertuples():
            candidata('D6', f'quebra em {r.variavel} por volta de {r.ano_central} em {r.estados} estados (salto médio '
                      f'{r.salto_medio:+.3f})',
                      'só documentar se vier da referência (ERA5 antes de 1979, por exemplo) ou da rede de estações do '
                      'BR-DWGD; homogeneizar só com referência independente concordando', 'ver D6_*.csv',
                      'Pettitt 1979; Alexandersson 1986; Peterson et al. 1998')
        for v, k in cost_v.items():
            candidata('D6', f'{v}: 2026 fora do intervalo de 1996-2025 (|z| > 3) em {k} estados',
                      'no motor (2026+): é a emenda entre o BR-DWGD e o ERA5 calibrado', 'ver D6_homogeneidade',
                      'Peterson et al. 1998')

    # ---------------------------------------------------------------------------------- D1
    @parte('D1 Reprodução das 16 bandas pelo código: 1 dia por ano (1961-2025, V1.0) e 2026 (V1.5), pixels sorteados')
    def d1():
        dias = [(d, 'v10') for d in DIAS_D1] + [(f'2026-{m:02d}-15', 'v15') for m in range(1, 11)]
        cls = sorted(PONTOS_D1)
        sorteio = (ee.Image.pixelLonLat().addBands(CLASSE)
                   .stratifiedSample(numPoints=0, classBand='classe', region=REGIAO, projection=PROJ, seed=SEMENTE,
                                     classValues=cls, classPoints=[PONTOS_D1[c] for c in cls], geometries=True,
                                     tileScale=4))
        pts = [{'pid': k, 'classe': int(f['properties']['classe']), 'lon': f['geometry']['coordinates'][0],
                'lat': f['geometry']['coordinates'][1]} for k, f in enumerate(gi(sorteio, 'pontos D1')['features'])]
        salvar_csv(pd.DataFrame(pts), 'D1_pontos.csv')
        log(f'   D1: {len(pts)} pixels (' + ', '.join(f'{CLASSES[c]} {sum(p["classe"] == c for p in pts)}' for c in cls) + ')')
        lote = {'s': LOTE_D1, 'r': LOTE_D1}

        def amostra(img, chave, rotulo):
            """Uma imagem por vez, em lotes; se pesado, o lote cai pela metade e fica lembrado."""
            linhas, i = [], 0
            while i < len(pts):
                sub = pts[i:i + lote[chave]]
                fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']})
                                           for p in sub])
                try:
                    res = gi(img.sampleRegions(collection=fc, properties=['pid'], projection=PROJ, tileScale=16,
                                               geometries=False), rotulo)
                    linhas += [f['properties'] for f in res['features']]
                    i += len(sub)
                except Pesado:
                    if lote[chave] <= LOTE_MINIMO_D1:
                        raise
                    lote[chave] = max(LOTE_MINIMO_D1, lote[chave] // 2)
                    log(f'   {rotulo}: pesado, lote reduzido para {lote[chave]} pixels')
            return pd.DataFrame(linhas)

        base = pd.DataFrame(pts)[['pid', 'classe']]
        linhas, sem = [], []
        for d, rota in dias:
            try:
                s_ = ee.Image(f'{ASSET_SAB}/SAB_{d.replace("-", "_")}').select(ORDEM).rename([f's_{b}' for b in ORDEM])
                r_ = ee.Image(carga['v10']['processarDia_Definitivo'](d) if rota == 'v10'
                              else carga['v15']['processarDia_Rota1'](d)).select(ORDEM).toFloat() \
                    .rename([f'r_{b}' for b in ORDEM])
                df = base.copy()
                for img, chave in ((s_, 's'), (r_, 'r')):
                    parte_df = amostra(img, chave, f'D1 {d} {chave}')
                    if 'pid' in parte_df:
                        df = df.merge(parte_df, on='pid', how='left')
                for pref in ('s_', 'r_'):
                    for b in ORDEM:
                        if f'{pref}{b}' not in df:
                            df[f'{pref}{b}'] = np.nan
                for c, sub in df.groupby('classe'):
                    if c not in CLASSES:
                        continue
                    r = {'data': d, 'rota': rota, 'classe': CLASSES[c], 'n': len(sub)}
                    for b in ORDEM:
                        r[f'frac_{b}'] = float(iguais_np(sub[f's_{b}'], sub[f'r_{b}']).mean())
                        r[f'abs_{b}'] = float((sub[f's_{b}'] - sub[f'r_{b}']).abs().mean())
                    linhas.append(r)
                log(f'   D1 {d} ({rota}): ok')
            except Exception as e:
                sem.append(d)
                log(f'   D1 {d}: não calculado ({str(e)[:150]})')
        df = pd.DataFrame(linhas)
        salvar_csv(df, 'D1_reproducao_por_dia_e_classe.csv')
        tipos, cont, outros = classificar_d1(linhas)
        salvar_csv(tipos, 'D1_tipo_por_dia.csv')
        log(tipos[tipos['tipo'] != 'idênticos'].to_string(index=False) if (tipos['tipo'] != 'idênticos').any()
            else '   todos os dias idênticos')
        hist = tipos[tipos['data'] <= FIM_HISTORICO]
        prim = hist[hist['tipo'] != 'idênticos']['data'].min() if (hist['tipo'] != 'idênticos').any() else None
        det = (f'{len(tipos)} dias: idênticos {cont["idênticos"]}, só ERA5 acumulado {cont["só ERA5 acumulado"]}, '
               f'outra diferença {cont["outra diferença"]}' + (f' (dias: {outros[:8]})' if outros else '') +
               (f' | primeiro dia do histórico com diferença: {prim}' if prim else '') +
               (f' | não calculados: {sem}' if sem else ''))
        st = 'FALHA' if outros else ('ATENÇÃO' if cont['só ERA5 acumulado'] else 'OK')
        achado('D1', st, 'Reprodução das 16 bandas pelo código (pixels sorteados de todas as classes)', det)
        if outros:
            candidata('D1', f'diferença fora das variáveis acumuladas do ERA5 em {len(outros)} dia(s): {outros[:8]}',
                      'investigar antes de qualquer correção (D1_*.csv mostra banda e classe)', 'ver D1_*.csv', '-')

    for nome_p, fn in (('D2', d2_d3), ('D4', d4), ('D5', d5), ('D6', d6), ('D1', d1)):
        if nome_p in PARTES:
            fn()

    # ---------------------------------------------------------------------------------- resultado
    log('\n' + '=' * 100 + '\nRESULTADO K19 (auditoria profunda; nada é aprovado ou reprovado aqui)\n' + '=' * 100)
    for a in ACHADOS:
        log(f"   {a['parte']:3} {a['status']:13} {a['titulo']}")
    log('\nCANDIDATAS A CORREÇÃO (decidir juntos; nada foi corrigido):')
    if CANDIDATAS:
        for i, c in enumerate(CANDIDATAS, 1):
            log(f"   {i}. [{c['parte']}] {c['divergencia']}\n      correção permitida: {c['correcao_permitida']} | "
                f"tamanho: {c['tamanho']} | referência: {c['referencia']}")
    else:
        log('   nenhuma além das já conhecidas (revisão do ERA5 desde 2017; pixels B)')
    log(f'\nTempo: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine (trava de somente leitura).')
    zip_parcial()
    log(f'📦 {PASTA}.zip  <- me envie este zip')
    try:
        from google.colab import files
        files.download(PASTA + '.zip')
    except Exception:
        pass


if __name__ == '__main__':
    principal()
