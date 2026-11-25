# >>> K25 v4 (15/11/2026): VARREDURA TOTAL DAS 16 VARIÁVEIS. Somente leitura. Cole inteiro, sem editar. <<<
# =========================================================================================
# K25 - TODOS OS TESTES POSSÍVEIS, TODAS AS VARIÁVEIS, ESTRATIFICADO POR CLASSE E POR ROTA
#
# POR QUE ESTE ARQUIVO EXISTE
#   A K22 confere 3 coisas em 11 dias de 334. A K24 confere 1 variável (Tmax) e, sem querer, exclui as
#   1.112 células de classe C (ela mascara pelo recorde do BR-DWGD, que não existe lá). O T5 varreu 2026.
#   Nada varreu 1961-2025, nada testou as 10 variáveis de superfície, e nada comparou as derivadas
#   (ETo, VPD) com as primárias gravadas. A K25 fecha isso.
#
# AS OITO PARTES (rode na ordem; cada uma grava o seu CSV e pode ser repetida sozinha)
#   A  inventário, proveniência e CONTAGEM POR CLASSE (resolve de vez o total de células sobre terra)
#   B  perfil das 16 variáveis: n, ausentes, min, máx, média, desvio, percentis exatos por histograma,
#      quantização (degrau da codificação) e caudas fora da faixa declarada — por classe e por mês
#   C  invariantes físicas: as 6 do motor + 6 que o motor NÃO testa — em TODOS os dias, por classe
#   D  limites absolutos de Xavier et al. (2022) aplicados ao produto final, nas DUAS tolerâncias de Rso
#      (1,001 do motor e 1,02 da T5), por classe, e a localização de cada pixel que violar
#   E  excesso sobre o recorde do próprio pixel (BR-DWGD, mesmo mês) para Tmax, Tmin, chuva, Rs e vento,
#      por rota E POR MÊS (a K24 comparou ERA5 de outubro com GFS de novembro: aqui não)
#   F  EMENDA, variável por variável: razão dos desvios 2026 / BR-DWGD 2016-2025 nos mesmos pixels.
#      A K22 mede isso só para a UR. É o teste que faltava para a Tmax.
#   G  COERÊNCIA DAS DERIVADAS: recalcula ETo e VPD a partir das primárias GRAVADAS e compara com as
#      gravadas. Se divergirem, o dia foi escrito por um código diferente do que o pacote declara.
#   H  máscara banda a banda (acha banda com menos pixels que as outras: vazamento de máscara) e
#      fechamento do balanço hídrico nos dias GFS
#   Z  ESTATÍSTICA, no seu computador ou no Colab, sobre os CSV: descritivo completo, outliers,
#      bootstrap por bloco de dias (1.000 réplicas, IC 95%), teste de permutação com p exato,
#      Mann-Whitney com a ressalva de autocorrelação. Nível declarado: alfa = 0,05.
#
# v4 (15/11/2026, depois da corrida de 12h55, a primeira com a parte F inteira): corrige o
#   deslocamento da Tmin na decodificação do BR-DWGD, de 5,0 para 15,0. A própria parte F deu a
#   prova: viés da Tmin +10,36 e +10,60 contra +0,54 e +0,70 da Tmax, e os 10 são exatamente a
#   diferença entre os dois deslocamentos. Com isso a Tmin volta ao teste da parte E.
#
# v3 (15/11/2026, depois da primeira corrida COMPLETA de verdade): conserta cinco defeitos MEUS que
#   a corrida de 09h31 expôs, e que produziam falso defeito no banco.
#   1. parte F caía com 'List.map: A mapped algorithm must take one argument.' — o Earth Engine exige
#      função de exatamente um argumento e eu usei parâmetro com valor padrão. Agora é fábrica.
#   2. `runoff_gt_pr` acusava 2.000.165 pixel-dias (8,5% do acervo). Era teste errado: eu somava o
#      escoamento SUBsuperficial, que é drenagem do armazenamento e passa da chuva do dia sem
#      anomalia nenhuma. Agora o invariante é só o superficial; a soma virou informação.
#   3. `tmin_C` aparecia com 97% dos pixel-dias acima do recorde. Era a REFERÊNCIA, não o dado: o
#      deslocamento de Tmin na decodificação do BR-DWGD não está conferido. A parte E agora detecta
#      referência implausível sozinha e SUPRIME a variável em vez de inventar um defeito.
#   4. `sm5_gt_sm100_sat` não é violação: na rota GFS a camada rasa é um balde de 50 mm que satura
#      antes da profunda. Passou a informação de assimetria entre rotas (prefixo i_, fora do veredito).
#   5. a parte B acusava valor "fora da faixa" comparando pelo CENTRO do bin, o que marcava o bin que
#      contém o próprio limite. Agora conta só o bin inteiramente fora, e grava a largura do bin.
#   E o simular_K25.py passou a exigir aridade 1 em List.map e Collection.map, que é o que faltava
#   para ele ter pegado o defeito 1 aqui em vez de no Colab.
#
# v2 (15/11/2026, mesmo dia): conserta o `Reducer input must be a number` da parte B2 — o
#   fixedHistogram devolve ARRAY por pixel, então ele tem de viver dentro do reduceRegion e não
#   dentro do Image.reduce. E blinda tudo: cada parte roda num try próprio (uma que falhe não
#   derruba as outras), erro estrutural cai para uma implementação alternativa em vez de tentar
#   dividir o bloco, erro de memória divide o bloco e reduz o lote, e a parte A agora CONFRONTA
#   as duas contagens de célula em vez de confiar numa só.
#
# MEMÓRIA (o Earth Engine não estoura: foi desenhado para isso)
#   - Nunca reduz o Brasil inteiro de uma vez: 4 faixas de latitude, e cada faixa se divide em duas
#     sozinha se o servidor reclamar de memória (até 2 níveis = 16 pedaços).
#   - Dias em lotes (DIAS_POR_PEDIDO), e o lote cai pela metade sozinho se pesar.
#   - As 16 bandas num único histograma: normalizadas para [0,1] pela faixa declarada de cada uma.
#     Uma chamada por faixa por mês dá os percentis exatos das 16 variáveis.
#   - Somas por classe com reducer agrupado (um pedido devolve as 4 classes).
#   - CHECKPOINT POR MÊS: cada parte grava o CSV e pula os meses que já estão nele. Pode rodar
#     1961-2025 em várias sessões: rode, baixe, suba o CSV de volta na próxima e continue.
#
# COMO RODAR NO COLAB
#   1. Ambiente de execução -> Reiniciar sessão.
#   2. Confira ANO_INI / ANO_FIM / PARTES logo abaixo. O padrão é 2026 e todas as partes.
#   3. Cole o arquivo inteiro numa célula e Ctrl+Enter. Fora da janela do motor (22h50-01h00).
#   4. No fim baixa K25_<data>.zip. Me envie.
#
#   Para varrer o histórico: ANO_INI = 1961, ANO_FIM = 1970, PARTES = ('C','D','H'), e repita por década.
#   Se já tiver CSV de uma sessão anterior, suba os arquivos para /content/K25_acumulado/ antes de rodar.
# =========================================================================================
import json
import math
import os
import shutil
import time
import traceback
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- o que rodar
ANO_INI, ANO_FIM = 2026, 2026
PARTES = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'Z')
SIMULACAO_PERMITIDA = False      # só o simular_K25.py liga isto. Deixe False SEMPRE.

PROJETO = 'clima-492922'
ASSET_SAB = f'projects/{PROJETO}/assets/SAB_V1'
ASSET_MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
ASSET_EQM = f'projects/{PROJETO}/assets/SICSB_EQM_1986_2025'
BR_DWGD = 'projects/ee-alexandrexavier/assets/BR-DWGD'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
X0, Y0, DX = TRANSFORM[2], TRANSFORM[5], TRANSFORM[0]

BANDAS = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2',
          'tsolo_C', 'tfolha_C', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm',
          'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']

# Faixa declarada de cada banda, para o histograma normalizado e para a contagem de fora-da-faixa.
# NÃO é um limite físico: é o intervalo em que o valor tem de cair para ser plausível no Brasil.
FAIXA = {'pr_mm': (0, 500), 'tmax_C': (-10, 50), 'tmin_C': (-15, 40), 'RH': (0, 100),
         'et_potencial': (0, 15), 'et_real': (0, 15), 'vpd': (0, 10), 'rs': (0, 45), 'u2': (0, 30),
         'tsolo_C': (-10, 50), 'tfolha_C': (-10, 60), 'transpiracao_mm': (0, 15),
         'runoff_sup_mm': (0, 500), 'runoff_sub_mm': (0, 500),
         'soil_moisture_0_5cm_m3_m3': (0, 0.95), 'soil_moisture_0_100cm_m3_m3': (0, 0.95)}

CLASSES = {1: 'A', 2: 'B', 3: 'C_interior', 4: 'C_borda'}
BLOCOS = [(-75.0, -5.0, -28.0, 6.5), (-75.0, -14.0, -28.0, -5.0),
          (-75.0, -23.0, -28.0, -14.0), (-75.0, -35.0, -28.0, -23.0)]

# ---- constantes copiadas do motor V1.6 (se o motor mudar, mude aqui também) -------------
UMIDADE_MAX_FISICA = 0.9
FATOR_TETO_CHUVA = 1.5
SW5_MAX_MM, SW100_MAX_MM = 25.0, 400.0
TOL_RSO_MOTOR = 0.001            # o motor marca rs > 1,001 x Rso
TOL_RSO_AUDIT = 0.02             # a T5 marcou rs > 1,02 x Rso; os dois contam, para comparar
# Xavier et al. (2022): limites aplicados às observações que entram no BR-DWGD
LIM_PR = (0.0, 450.0)            # 0 < pr < 450 mm
LIM_RS_FRAC = (0.03, 1.0)        # 0,03 Ra <= Rs < Ra
LIM_U2 = (0.0, 100.0)
LIM_T = (-30.0, 50.0)
ANOS_RECORDE = (1991, 2025)
# Se um campo passa do recorde de 35 anos em mais do que isto, o problema quase certamente é a
# REFERÊNCIA (decodificação do BR-DWGD), não o dado: um campo bem calibrado fica na ordem de 0,1%.
MAX_PCT_REFERENCIA_SUSPEITA = 20.0
# Como medir "acima do recorde do pixel": aditivo em graus para temperatura, multiplicativo para o
# resto (somar 1 mm ao recorde de chuva não quer dizer nada; multiplicar por 1,1 quer).
LIMIARES_REC = {'tmax_C': ('mais', (0.0, 1.0, 2.0), '°C'), 'tmin_C': ('mais', (0.0, 1.0, 2.0), '°C'),
                'pr_mm': ('vezes', (1.0, 1.1, 1.5), 'x'), 'rs': ('vezes', (1.0, 1.05, 1.1), 'x'),
                'u2': ('vezes', (1.0, 1.1, 1.5), 'x')}
ANOS_REF_EMENDA = (2016, 2025)
N_PONTOS_EMENDA = 150
SEMENTE = 25
TOL_ETO = 0.01                   # mm/dia: divergência aceitável no recálculo da ETo
TOL_VPD = 0.005                  # kPa
BINS = 512
PERCENTIS = (1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9)
ALFA = 0.05
N_BOOT = 1000
N_PERM = 10000
MAX_PIXELS_LISTA = 3000          # no máximo tantos pixels violadores listados por teste

DIAS_POR_PEDIDO = 4
JANELAS_MOTOR = [((22, 50), (24, 0)), ((0, 0), (1, 0))]
DURACAO_ESTIMADA_MIN = 90

BRT = timezone(timedelta(hours=-3))
AGORA = datetime.now(BRT)
RAIZ = '/content' if os.path.isdir('/content') else '.'
ACUMULADO = os.path.join(RAIZ, 'K25_acumulado')          # CSV de sessões anteriores entram aqui
PASTA = os.path.join(RAIZ, f'K25_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K25.txt')
RESULTADOS = []


def log(*partes):
    texto = ' '.join(str(p) for p in partes)
    print(texto, flush=True)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(texto + '\n')


def resultado(item, status, titulo, texto):
    RESULTADOS.append({'item': item, 'status': status, 'titulo': titulo, 'texto': texto})
    simb = {'OK': '✅', 'FALHA': '❌', 'ATENCAO': '⚠️', 'INFO': 'ℹ️', 'ESPERAR': '⏳'}.get(status, '•')
    log(f'{simb} {item} {status}: {titulo}\n   {texto}')


def caminho(nome):
    return os.path.join(PASTA, nome)


def falhou_parte(nome, e, detalhe=''):
    """Uma parte que quebra NÃO derruba a corrida: fica registrada e o resto segue."""
    msg = f'{type(e).__name__}: {str(e)[:260]}'
    log(f'   ⚠️ parte {nome} interrompida -> {msg}')
    log('   ' + traceback.format_exc(limit=4).replace(chr(10), chr(10) + '   '))
    resultado(nome, 'FALHOU', f'parte {nome} interrompida (as outras seguiram)',
              msg + (f' | {detalhe}' if detalhe else '') +
              ' | o CSV do que já tinha sido lido está no zip; rode esta parte sozinha depois')


def ler_acumulado(nome):
    """CSV de sessões anteriores (para o checkpoint por mês). Devolve DataFrame vazio se não houver."""
    for base in (PASTA, ACUMULADO):
        p = os.path.join(base, nome)
        if os.path.exists(p):
            try:
                return pd.read_csv(p, sep=';', decimal=',')
            except Exception:
                pass
    return pd.DataFrame()


def gravar(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(caminho(nome), sep=';', decimal=',', index=False)
    return caminho(nome)


def acrescentar(df, nome):
    """Junta com o que já existe (checkpoint) e grava."""
    velho = ler_acumulado(nome)
    novo = pd.concat([velho, df], ignore_index=True) if len(velho) else df
    return gravar(novo, nome)


# =========================================================================================
# FUNÇÕES PURAS — testadas offline em 03_testes_offline/teste_K25.py (nenhuma fala com o servidor)
# =========================================================================================
def minutos_ate_janela(agora):
    m = agora.hour * 60 + agora.minute
    melhor = None
    for (h1, m1), (h2, m2) in JANELAS_MOTOR:
        ini, fim = h1 * 60 + m1, h2 * 60 + m2
        if ini <= m < fim:
            return 0
        falta = (ini - m) % (24 * 60)
        melhor = falta if melhor is None else min(melhor, falta)
    return melhor


def meses_do_intervalo(ano_ini, ano_fim):
    return [f'{a}-{m:02d}' for a in range(ano_ini, ano_fim + 1) for m in range(1, 13)]


def meses_a_fazer(todos, feitos):
    return [m for m in todos if m not in set(feitos)]


def dividir(b):
    """Divide um bloco de latitude em dois. Devolve os dois blocos."""
    lon0, lat0, lon1, lat1 = b
    meio = (lat0 + lat1) / 2.0
    return (lon0, lat0, lon1, meio), (lon0, meio, lon1, lat1)


def lotes(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]


def classificar_rota(versao):
    """Rota de cada dia a partir da propriedade 'versao' gravada."""
    if versao is None:
        return 'desconhecida'
    v = str(versao)
    if v.startswith('provisoria_gfs') or v.startswith('falha_latencia_gfs'):
        return 'GFS'
    if v.startswith('provisoria'):
        return 'ERA5'
    return 'BR-DWGD'


def ler_grupos(bruto, nomes, chave_soma='sum'):
    """Resposta de um reducer agrupado -> {classe: {nome: valor}}.
    bruto: {'groups': [{'classe': 1, 'sum': [v1, v2, ...]}, ...]} ou com valor escalar."""
    saida = {}
    for g in (bruto or {}).get('groups', []):
        k = int(g['classe'])
        v = g.get(chave_soma)
        if isinstance(v, list):
            saida[k] = {n: (v[i] if i < len(v) else None) for i, n in enumerate(nomes)}
        else:
            saida[k] = {nomes[0]: v}
    return saida


def somar_grupos(partes, nomes):
    """Soma, classe a classe, os dicionários de vários blocos."""
    total = {}
    for p in partes:
        for k, d in p.items():
            alvo = total.setdefault(k, {n: 0.0 for n in nomes})
            for n in nomes:
                x = d.get(n)
                if x is not None:
                    alvo[n] += float(x)
    return total


def juntar_hist(partes):
    """Soma histogramas de vários blocos. partes: lista de arrays (n_bandas, BINS)."""
    acc = None
    for h in partes:
        a = np.asarray(h, dtype=float)
        acc = a if acc is None else acc + a
    return acc


def percentis_de_hist(hist, lo, hi, percentis=PERCENTIS):
    """Percentis exatos até a largura do bin, a partir de um histograma de BINS bins em [lo, hi]."""
    h = np.asarray(hist, dtype=float)
    n = h.sum()
    if n <= 0:
        return {f'p{p:g}': float('nan') for p in percentis}
    bordas = np.linspace(lo, hi, len(h) + 1)
    acum = np.cumsum(h) / n
    saida = {}
    for p in percentis:
        i = int(np.searchsorted(acum, p / 100.0, side='left'))
        i = min(i, len(h) - 1)
        saida[f'p{p:g}'] = float((bordas[i] + bordas[i + 1]) / 2.0)
    return saida


def degrau_quantizacao(hist, lo, hi):
    """Se os valores vierem de inteiro com escala, os bins ocupados ficam espaçados de forma regular.
    Devolve (n_bins_ocupados, degrau_mediano_em_unidades) ou (n, nan) se não houver padrão."""
    h = np.asarray(hist, dtype=float)
    ocup = np.flatnonzero(h > 0)
    if len(ocup) < 3:
        return int(len(ocup)), float('nan')
    larg = (hi - lo) / len(h)
    d = np.diff(ocup)
    if len(d) == 0 or np.median(d) <= 1:
        return int(len(ocup)), float('nan')
    return int(len(ocup)), float(np.median(d) * larg)


def fracao_fora(hist, lo, hi, faixa):
    """Fração do histograma INTEIRAMENTE fora de faixa. Conta um bin como abaixo só se a sua borda
    direita já estiver abaixo do mínimo, e como acima só se a borda esquerda já estiver acima do
    máximo. Comparar pelo centro, como a v2 fazia, acusava o bin que contém o próprio limite: um
    valor exatamente 0 ou exatamente 100 aparecia como fora da faixa."""
    h = np.asarray(hist, dtype=float)
    n = h.sum()
    if n <= 0:
        return float('nan'), float('nan')
    bordas = np.linspace(lo, hi, len(h) + 1)
    esq, dir_ = bordas[:-1], bordas[1:]
    return float(h[dir_ <= faixa[0]].sum() / n), float(h[esq >= faixa[1]].sum() / n)


def razao_e_vies(sab, ref, variavel):
    """Razão dos desvios dentro do mês (2026 / BR-DWGD 2016-2025) e viés das médias, nos mesmos pixels.
    sab: pid, data, <variavel>. ref: pid, mes, <variavel>_sd, <variavel>_m."""
    d = sab.dropna(subset=[variavel]).copy()
    if not len(d):
        return float('nan'), float('nan'), 0
    d['am'] = d['data'].str[:7]
    d['mes'] = d['data'].str[5:7].astype(int)
    g = d.groupby(['pid', 'am'])[variavel]
    sd = pd.DataFrame({'sd': g.std(), 'n': g.size()}).reset_index()
    sd = sd[sd['n'] >= 10]
    sd['mes'] = sd['am'].str[5:7].astype(int)
    m = sd.merge(ref[['pid', 'mes', f'{variavel}_sd']], on=['pid', 'mes']).dropna()
    razao = (float(np.sqrt((m['sd'] ** 2).mean()) / np.sqrt((m[f'{variavel}_sd'] ** 2).mean()))
             if len(m) and np.sqrt((m[f'{variavel}_sd'] ** 2).mean()) > 0 else float('nan'))
    md = (d.groupby(['pid', 'mes'])[variavel].mean().rename('m').reset_index()
          .merge(ref[['pid', 'mes', f'{variavel}_m']], on=['pid', 'mes']).dropna())
    vies = float((md['m'] - md[f'{variavel}_m']).mean()) if len(md) else float('nan')
    return razao, vies, int(len(m))


def bootstrap_blocos(x, n_rep=N_BOOT, tamanho=5, semente=SEMENTE):
    """IC 95% da média por bootstrap de blocos consecutivos (respeita a autocorrelação diária)."""
    x = np.asarray([v for v in x if np.isfinite(v)], dtype=float)
    if len(x) < tamanho * 2:
        return float('nan'), float('nan')
    rng = np.random.default_rng(semente)
    n_blocos = int(np.ceil(len(x) / tamanho))
    inicios = np.arange(len(x) - tamanho + 1)
    medias = np.empty(n_rep)
    for i in range(n_rep):
        esc = rng.choice(inicios, n_blocos, replace=True)
        amostra = np.concatenate([x[s:s + tamanho] for s in esc])[:len(x)]
        medias[i] = amostra.mean()
    return float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))


def permutacao(a, b, n_rep=N_PERM, semente=SEMENTE):
    """p exato (bilateral) da diferença de médias por permutação. Devolve (dif, p, n_a, n_b)."""
    a = np.asarray([v for v in a if np.isfinite(v)], dtype=float)
    b = np.asarray([v for v in b if np.isfinite(v)], dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float('nan'), float('nan'), len(a), len(b)
    obs = a.mean() - b.mean()
    junto = np.concatenate([a, b])
    rng = np.random.default_rng(semente)
    conta = 0
    for _ in range(n_rep):
        rng.shuffle(junto)
        if abs(junto[:len(a)].mean() - junto[len(a):].mean()) >= abs(obs) - 1e-12:
            conta += 1
    return float(obs), float((conta + 1) / (n_rep + 1)), len(a), len(b)


def outliers_tukey(x):
    """Regra de Tukey (1,5 e 3,0 IQR). Devolve (n_moderados, n_extremos, limites)."""
    x = np.asarray([v for v in x if np.isfinite(v)], dtype=float)
    if len(x) < 4:
        return 0, 0, (float('nan'), float('nan'))
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    mod = int(((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)).sum())
    ext = int(((x < q1 - 3.0 * iqr) | (x > q3 + 3.0 * iqr)).sum())
    return mod, ext, (float(q1 - 1.5 * iqr), float(q3 + 1.5 * iqr))


def eto_fao56_numpy(tmax, tmin, rh, u2, rs, ra, z):
    """A MESMA conta do eto_penman_monteith do motor, em numpy, para o teste offline da parte G."""
    p = 101.3 * ((293.0 - 0.0065 * z) / 293.0) ** 5.26
    gamma = 0.000665 * p
    tm = (tmax + tmin) / 2.0
    es = (0.6108 * np.exp(17.625 * tmax / (tmax + 243.04)) +
          0.6108 * np.exp(17.625 * tmin / (tmin + 243.04))) / 2.0
    ea = es * rh / 100.0
    vpd = np.maximum(es - ea, 0.0)
    rso = (0.75 + 2e-5 * z) * ra
    rs_rso = np.clip(rs / rso, 0.0, 1.0)
    rns = 0.77 * rs
    rad = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2.0
    rn = rns - np.maximum(rad * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * rs_rso - 0.35), 0.0)
    delta = 4283.58 * (0.6108 * np.exp(17.625 * tm / (tm + 243.04))) / (tm + 243.04) ** 2
    num = 0.408 * delta * rn + gamma * (900.0 / (tm + 273.0)) * u2 * vpd
    return np.maximum(num / (delta + gamma * (1.0 + 0.34 * u2)), 0.0), vpd


def decidir_invariantes(total):
    """total: {classe: {flag: n}}. Devolve (status, texto)."""
    soma = {}
    for d in total.values():
        for k, v in d.items():
            if k != 'n_pix':
                soma[k] = soma.get(k, 0.0) + float(v or 0)
    ruins = {k: int(v) for k, v in soma.items() if v > 0 and not k.startswith('i_')}
    infos = {k: int(v) for k, v in soma.items() if v > 0 and k.startswith('i_')}
    n = sum(float(d.get('n_pix') or 0) for d in total.values())
    extra = ('; informativos, não são violação: '
             + ', '.join(f'{k} {v:,}' for k, v in sorted(infos.items()))) if infos else ''
    if not ruins:
        return 'OK', f'{int(n):,} pixel-dias, nenhuma violação' + extra
    return ('FALHA', f'{int(n):,} pixel-dias; violações: '
            + ', '.join(f'{k} {v:,}' for k, v in sorted(ruins.items())) + extra)


def folga_seam(a, b):
    """Descontinuidade relativa entre dois valores (último dia de uma rota, primeiro da outra)."""
    if a is None or b is None or not np.isfinite(a) or not np.isfinite(b) or a == 0:
        return float('nan')
    return float(b / a)


# =========================================================================================
def ee_e_de_verdade(ee):
    """True se o módulo `ee` importado é o Earth Engine mesmo. Dois sinais independentes:
    o pacote de verdade é um arquivo em disco (tem __file__) e o simulador se declara."""
    return getattr(ee, '__file__', None) is not None and not bool(getattr(ee, 'SIMULADO', False))


def principal():
    global PASTA, LOG
    import ee
    # TRAVA DE PROCEDÊNCIA. Um verificador que relata números sintéticos como se fossem dados é pior
    # do que um que para. Isto aconteceu em 15/11/2026: o simular_K25.py foi colado numa célula do
    # Colab, instalou um `ee` falso na sessão, e a célula seguinte com o K25 mediu o simulador — 40
    # dias, 4.000 células por classe, tudo em 0 min — sem nada avisar.
    if not ee_e_de_verdade(ee):
        if not SIMULACAO_PERMITIDA:
            raise RuntimeError(
                'O módulo `ee` desta sessão NÃO é o Earth Engine: é o simulador offline.\n'
                'Causa: o simular_K25.py foi executado nesta sessão (colado numa célula). Ele troca o\n'
                '`ee` por um falso e o falso fica na sessão inteira.\n'
                'Conserto: Ambiente de execução -> Reiniciar sessão, e cole SÓ o K25.\n'
                'Para usar o simulador, rode-o como processo separado: !python3 simular_K25.py')
        PASTA = os.path.join(os.path.dirname(PASTA) or '.', 'SIMULACAO_' + os.path.basename(PASTA))
        LOG = os.path.join(PASTA, 'LOG_K25.txt')
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    if not ee_e_de_verdade(ee):
        for _ in range(3):
            log('⚠️  SIMULAÇÃO — OS NÚMEROS ABAIXO SÃO SINTÉTICOS E NÃO DESCREVEM O SAB  ⚠️')
        log('')
    log('=' * 104)
    log(f'K25 v4: VARREDURA TOTAL DAS 16 VARIÁVEIS (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log(f'   anos {ANO_INI}-{ANO_FIM} | partes {PARTES} | alfa = {ALFA}')
    log('=' * 104)
    falta = minutos_ate_janela(AGORA)
    if falta < DURACAO_ESTIMADA_MIN:
        log(f'⛔ Não comecei: a janela do motor começa em {falta} min e a K25 pode levar {DURACAO_ESTIMADA_MIN} min. '
            f'Comece bem antes das 22h50 ou depois da 01h00.')
        return
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K25 é somente leitura: escrita bloqueada')
    for n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
              'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable',
              'startIngestion', 'cancelTask'):
        if hasattr(ee.data, n):
            setattr(ee.data, n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa.\n')

    # ---------------------------------------------------------------- infraestrutura
    # Três classes de erro, porque a reação a cada uma é diferente:
    #   TRANS  servidor ocupado        -> esperar e repetir
    #   Pesado memória / tempo / volume -> dividir o bloco e reduzir o lote
    #   Forma  pedido mal montado      -> dividir NÃO resolve; cai para outra implementação
    TRANS = ('Too many concurrent', 'Internal error', 'Service Unavailable', '503', '429', 'deadline',
             'Deadline', 'Connection', 'temporarily', 'Bad Gateway', '502', 'Quota')
    PESADO = ('memory', 'timed out', 'too many values', 'aggregation', 'too many pixels',
              'user memory limit', 'exceeded', 'output of this computation is too large',
              'request payload size')
    FORMA = ('must be a number', 'reducer input', 'no band named', 'does not contain',
             'cannot be cast', 'expected a', 'invalid argument', 'unable to cast',
             'parameter', 'array', 'dictionary', 'band names', 'must have the same',
             'not a defined', 'image.select', 'number of bands')
    ESPERAS = [30, 60, 90, 120, 180, 240]

    class Pesado(Exception):
        pass

    class Forma(Exception):
        pass

    def classificar(e):
        t = str(e).lower()
        if any(k in t for k in PESADO):
            return 'pesado'
        if any(k in t for k in FORMA):
            return 'forma'
        if any(k.lower() in t for k in TRANS):
            return 'trans'
        return 'outro'

    def gi(obj, rotulo):
        for t in range(len(ESPERAS) + 1):
            try:
                return obj.getInfo()
            except Exception as e:
                tipo = classificar(e)
                if tipo == 'pesado':
                    raise Pesado(str(e))
                if tipo == 'forma':
                    raise Forma(str(e))
                if tipo == 'trans' and t < len(ESPERAS):
                    log(f'   ↻ {rotulo}: servidor ocupado; nova tentativa em {ESPERAS[t]} s')
                    time.sleep(ESPERAS[t])
                    continue
                if tipo == 'outro' and t < 2:
                    log(f'   ↻ {rotulo}: erro não classificado ({str(e)[:70]}); repito em 30 s')
                    time.sleep(30)
                    continue
                raise

    def geom(b):
        return ee.Geometry.Rectangle(list(b), None, False)

    def por_blocos(fabrica, rotulo, blocos=None, nivel=0):
        """Chama fabrica(bloco) em cada faixa de latitude; divide a faixa se o servidor reclamar.
        Erro de FORMA sobe inteiro: dividir não conserta pedido mal montado."""
        saida = []
        for j, b in enumerate(blocos or BLOCOS):
            try:
                saida.append(gi(fabrica(b), f'{rotulo} bloco {j + 1}'))
            except Pesado as e:
                if nivel >= 3:
                    log(f'   {rotulo} bloco {j + 1}: pesado no 3º nível; desisti deste pedaço')
                    continue
                log(f'   {rotulo} bloco {j + 1}: pesado ({str(e)[:50]}), dividindo')
                saida += por_blocos(fabrica, rotulo, list(dividir(b)), nivel + 1)
        return saida

    SONDA = (-60.0, -12.0, -59.0, -11.0)        # 1 grau no meio do Brasil: barato
    _sondas = {}                                 # a forma de um pedido só é sondada UMA vez

    def sondar(fabrica, rotulo, chave):
        """Testa a FORMA do pedido num quadrado de 1 grau antes de rodar o país inteiro.
        O resultado fica em cache por `chave`: a forma de um pedido não muda de um mês para o outro,
        então sondar por mês e por variável gastaria centenas de chamadas sem necessidade."""
        if chave in _sondas:
            return _sondas[chave]
        try:
            gi(fabrica(SONDA), f'sonda {rotulo}')
            ok = True
        except Forma as e:
            log(f'   ⚠️ sonda {chave}: forma recusada pelo servidor ({str(e)[:90]})')
            ok = False
        except Pesado:
            ok = True                            # pesado na sonda é improvável; a forma está ok
        except Exception as e:
            log(f'   ⚠️ sonda {chave}: {str(e)[:90]}')
            ok = False
        _sondas[chave] = ok
        return ok

    def tentar(opcoes, rotulo):
        """Escada de implementações: devolve o resultado da primeira cuja FORMA o servidor aceita e
        que completa. opcoes: [(nome, fabrica, leitor)] ou [(nome, fabrica, leitor, chave_sonda)].
        Devolve (nome, dados) ou (None, None)."""
        for op in opcoes:
            nome, fabrica, leitor = op[0], op[1], op[2]
            chave = op[3] if len(op) > 3 else f'{rotulo}/{nome}'
            if not sondar(fabrica, f'{rotulo}/{nome}', chave):
                continue
            try:
                partes = por_blocos(fabrica, f'{rotulo}/{nome}')
                if not partes:
                    log(f'   {rotulo}: {nome} não devolveu nada; tento a próxima')
                    continue
                return nome, leitor(partes)
            except (Pesado, Forma) as e:
                log(f'   {rotulo}: {nome} falhou ({str(e)[:70]}); tento a próxima')
                continue
        log(f'   ⚠️ {rotulo}: nenhuma implementação completou')
        return None, None

    PROJ = ee.Projection(CRS, TRANSFORM)
    CLASSE = ee.Image(ASSET_MASCARA).select('classe').rename('classe')
    ELEV = ee.Image('USGS/SRTMGL1_003')
    SAB = ee.ImageCollection(ASSET_SAB)
    BR = ee.ImageCollection(BR_DWGD)

    def rr(img, reducer, b):
        return img.reduceRegion(reducer=reducer, geometry=geom(b), crs=CRS, crsTransform=TRANSFORM,
                                maxPixels=1e10, tileScale=16)

    def agrupado(reducer, n):
        return reducer.repeat(n).group(groupField=n, groupName='classe')

    def ra_fao56(d):
        data = ee.Date(d)
        lat = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180.0)
        J = ee.Number(data.getRelative('day', 'year')).add(1)
        dr = J.multiply(2.0 * math.pi / 365.0).cos().multiply(0.033).add(1.0)
        de = J.multiply(2.0 * math.pi / 365.0).subtract(1.39).sin().multiply(0.409)
        ws = lat.tan().multiply(de.tan()).multiply(-1.0).clamp(-1.0, 1.0).acos()
        return (ws.multiply(lat.sin()).multiply(de.sin())
                .add(lat.cos().multiply(de.cos()).multiply(ws.sin()))
                .multiply(dr).multiply((24.0 * 60.0 / math.pi) * 0.0820).rename('ra'))

    def rso_fao56(d):
        return ELEV.multiply(0.00002).add(0.75).multiply(ra_fao56(d)).rename('rso')

    def dia(d):
        return ee.Image(SAB.filterDate(d, ee.Date(d).advance(1, 'day')).first())

    # decodificação do BR-DWGD (escala e offset por variável, como nas auditorias anteriores)
    # Escala e deslocamento de cada variável do BR-DWGD.
    # O deslocamento da Tmin era 5,0 na v2 e v3 e estava ERRADO em exatamente 10 graus. A prova veio
    # da parte F da corrida de 12h55: o viés da Tmin contra o BR-DWGD deu +10,364 na rota ERA5 e
    # +10,603 na GFS, contra +0,540 e +0,696 da Tmax. Tirando os 10, a Tmin fica em +0,364 e +0,603,
    # da mesma ordem da Tmax — que é o que se espera de duas variáveis corrigidas pelo mesmo caminho.
    # Com 5,0 a parte E acusava 97% dos pixel-dias acima do recorde, que era defeito inventado.
    # Confirme contra as propriedades do asset antes de publicar qualquer número que dependa disto.
    DECODE_BR = {'Tmax': (0.00106815, 15.0), 'Tmin': (0.00106815, 15.0), 'pr': (0.00686666, 225.0),
                 'RH': (0.39370079, -0.393701), 'u2': (0.05905512, -0.059055), 'Rs': (0.15708661, -0.057087)}
    DECODE_CONFERIDO = {'Tmax': True, 'pr': True, 'RH': True, 'u2': True, 'Rs': True, 'Tmin': True}

    def br_var(img, v):
        esc, off = DECODE_BR[v]
        m = img.select('pr').gt(-32768).And(img.select('Tmax').gt(-32768))
        return img.select(v).updateMask(m).multiply(esc).add(off).rename(v)

    _rec = {}

    def recorde(v, mes):
        if (v, mes) not in _rec:
            _rec[(v, mes)] = (BR.filter(ee.Filter.calendarRange(*ANOS_RECORDE, 'year'))
                              .filter(ee.Filter.calendarRange(mes, mes, 'month'))
                              .map(lambda i: br_var(i, v)).max().rename('rec'))
        return _rec[(v, mes)]

    # ---------------------------------------------------------------- A inventário
    inventario = ler_acumulado('K25_A_inventario.csv')
    if 'A' in PARTES or not len(inventario):
        try:
            log('[A] inventário, proveniência e contagem por classe')
            col = SAB.filterDate(f'{ANO_INI}-01-01', f'{ANO_FIM + 1}-01-01')
            campos = ['system:time_start', 'versao', 'versao_algoritmo', 'Faixa_Prazo_GFS',
                      'metodo_ur_vento_era5', 'rs_limitado_rso', 'teto_chuva_fator']
            try:
                bruto = gi(col.map(lambda i: ee.Feature(None, ee.Dictionary.fromLists(
                    campos, [ee.Algorithms.If(ee.Image(i).propertyNames().contains(c), ee.Image(i).get(c), '')
                             for c in campos]))), 'inventário')['features']
                linhas = [f['properties'] for f in bruto]
            except Pesado:
                linhas = []
                for a in range(ANO_INI, ANO_FIM + 1):
                    sub = SAB.filterDate(f'{a}-01-01', f'{a + 1}-01-01')
                    bruto = gi(sub.map(lambda i: ee.Feature(None, ee.Dictionary.fromLists(
                        campos, [ee.Algorithms.If(ee.Image(i).propertyNames().contains(c), ee.Image(i).get(c), '')
                                 for c in campos]))), f'inventário {a}')['features']
                    linhas += [f['properties'] for f in bruto]
            inventario = pd.DataFrame(linhas)
            if 'system:time_start' not in inventario.columns:
                raise RuntimeError('o servidor não devolveu system:time_start; colunas: '
                                   f'{list(inventario.columns)}')
            def _data(t):
                try:
                    return datetime.fromtimestamp(int(t) / 1000, timezone.utc).strftime('%Y-%m-%d')
                except Exception:
                    return None
            inventario['data'] = [_data(t) for t in inventario['system:time_start']]
            inventario = inventario.dropna(subset=['data'])
            for c in ('versao', 'versao_algoritmo', 'Faixa_Prazo_GFS', 'metodo_ur_vento_era5'):
                if c not in inventario.columns:
                    inventario[c] = None
            inventario['versao'] = inventario['versao'].replace('', None)
            inventario['rota'] = inventario['versao'].map(classificar_rota)
            inventario = inventario.drop(columns=['system:time_start']).sort_values('data').reset_index(drop=True)
            gravar(inventario, 'K25_A_inventario.csv')
            dias_rota_pre = dict(zip(inventario['data'], inventario['rota']))
            esperado = pd.date_range(inventario['data'].min(), inventario['data'].max())
            buracos = sorted(set(esperado.strftime('%Y-%m-%d')) - set(inventario['data']))
            dups = inventario['data'].duplicated().sum()
            resultado('A1', 'OK' if not buracos and not dups else 'FALHA', 'dias gravados, sem buraco e sem repetição',
                      f'{len(inventario)} dias de {inventario["data"].min()} a {inventario["data"].max()}; '
                      f'esperados {len(esperado)}; buracos {len(buracos)}'
                      + (f' (ex.: {buracos[:5]})' if buracos else '') + f'; datas repetidas {int(dups)}')
            resultado('A2', 'INFO', 'proveniência e versão do algoritmo',
                      ' | '.join(f'{r} {n}' for r, n in inventario['rota'].value_counts().items())
                      + ' || versões: ' + ', '.join(f'{k}={v}' for k, v in
                                                    inventario['versao_algoritmo'].fillna('sem propriedade').value_counts().items())
                      + ' || métodos: ' + ', '.join(sorted(set(inventario['metodo_ur_vento_era5'].dropna().astype(str))) or ['nenhum']))

            # contagem por classe: a conta que resolve o total de células sobre terra
            cont = somar_grupos([ler_grupos(p, ['n'], 'sum') for p in por_blocos(
                lambda b: rr(ee.Image.constant(1).rename('n').addBands(CLASSE).updateMask(CLASSE.mask()),
                             agrupado(ee.Reducer.sum(), 1), b), 'classes')], ['n'])
            tab = pd.DataFrame([{'classe': k, 'nome': CLASSES.get(k, f'?{k}'), 'celulas': int(round(v['n']))}
                                for k, v in sorted(cont.items())])
            tab.loc[len(tab)] = {'classe': 0, 'nome': 'TOTAL', 'celulas': int(tab['celulas'].sum())}
            gravar(tab, 'K25_A_classes.csv')
            log(tab.to_string(index=False))
            # A contagem pela máscara de UM dia do SAB NÃO é a mesma coisa que a contagem da máscara de
            # qualidade, e na primeira corrida as duas discordaram em 1.247 células. Então aqui elas são
            # CONFRONTADAS, em vários dias, em vez de uma ser apresentada como a resposta.
            n_mascara = int(tab.loc[tab.classe == 0, 'celulas'].iloc[0])
            datas_ord = sorted(inventario['data'])
            amostra_dias = []
            for cand in (datas_ord[0], datas_ord[len(datas_ord) // 2], datas_ord[-1]):
                if cand not in amostra_dias:
                    amostra_dias.append(cand)
            linhas_sab = []
            for d in amostra_dias:
                img_d = ee.Image(SAB.filterDate(d, ee.Date(d).advance(1, 'day')).first())
                m_sab = img_d.select('pr_mm').mask()
                # (i) total de células com valor, SEM cruzar com a máscara de qualidade
                tot = sum(float((p or {}).get('n') or 0) for p in por_blocos(
                    lambda b: rr(ee.Image.constant(1).rename('n').updateMask(m_sab), ee.Reducer.sum(), b),
                    f'total com valor {d}'))
                # (ii) o mesmo, agrupado por classe (quem tem valor E tem classe)
                cont2 = somar_grupos([ler_grupos(p, ['n'], 'sum') for p in por_blocos(
                    lambda b: rr(ee.Image.constant(1).rename('n').updateMask(m_sab).addBands(CLASSE),
                                 agrupado(ee.Reducer.sum(), 1), b), f'classes com valor {d}')], ['n'])
                linha = {'data': d, 'rota': dias_rota_pre.get(d), 'com_valor_total': int(round(tot))}
                for k in (1, 2, 3, 4):
                    linha[CLASSES[k]] = int(round((cont2.get(k) or {}).get('n') or 0))
                linha['com_valor_e_classe'] = sum(linha[CLASSES[k]] for k in (1, 2, 3, 4))
                linha['com_valor_sem_classe'] = linha['com_valor_total'] - linha['com_valor_e_classe']
                linha['classe_sem_valor'] = n_mascara - linha['com_valor_e_classe']
                linhas_sab.append(linha)
                log(f'   {d}: {linha["com_valor_total"]:,} com valor; {linha["com_valor_e_classe"]:,} '
                    f'também com classe; {linha["com_valor_sem_classe"]:,} com valor e sem classe; '
                    f'{linha["classe_sem_valor"]:,} com classe e sem valor')
            tab2 = pd.DataFrame(linhas_sab)
            gravar(tab2, 'K25_A_classes_no_SAB.csv')
            log('\nconfronto das contagens:')
            log(tab2.to_string(index=False))
            pior = int(tab2['classe_sem_valor'].abs().max())
            concorda = pior == 0
            resultado('A3', 'INFO' if concorda else 'ATENCAO', 'contagem por classe e confronto com a máscara do dia',
                      f'MÁSCARA DE QUALIDADE (é esta que vai ao artigo): '
                      + ' | '.join(f'{r.nome} {r.celulas:,}' for r in tab.itertuples() if r.classe)
                      + f' || total {n_mascara:,}. '
                      + (f'A máscara de qualidade e as células com valor coincidem nos {len(amostra_dias)} dias '
                         f'conferidos.' if concorda else
                         f'DISCORDÂNCIA: em {amostra_dias[0]}..{amostra_dias[-1]} há até {pior:,} células '
                         f'classificadas sem valor no dia (e até '
                         f'{int(tab2["com_valor_sem_classe"].abs().max()):,} com valor e sem classe). '
                         f'As duas contagens medem coisas diferentes: a máscara é estática e o dia é um dia. '
                         f'Para o artigo use a máscara ({n_mascara:,}); cite o número do dia só se disser qual dia.'))
        except Exception as _e:
            falhou_parte('A', _e)

    # A parte A pode ter falhado. Sem um inventário com a coluna 'data' nenhuma outra parte tem o que
    # varrer, então aqui a corrida termina com relatório em vez de estourar na primeira indexação.
    if not isinstance(inventario, pd.DataFrame) or inventario.empty or 'data' not in inventario.columns:
        resultado('A', 'FALHA', 'inventário indisponível',
                  'sem a lista de dias gravados não há o que varrer. Causas prováveis: ANO_INI/ANO_FIM '
                  'fora do que existe no asset, ou a parte A falhou (veja o item A acima). As partes '
                  'B a H precisam do inventário e foram puladas.')
        return fechar(T0)
    for _c in ('versao', 'rota', 'Faixa_Prazo_GFS'):
        if _c not in inventario.columns:
            inventario[_c] = None
    if inventario['rota'].isna().all():
        inventario['rota'] = inventario['versao'].map(classificar_rota)
    inventario['mes'] = inventario['data'].astype(str).str[:7]
    dias_rota = dict(zip(inventario['data'], inventario['rota']))
    dias_faixa = dict(zip(inventario['data'], inventario.get('Faixa_Prazo_GFS', pd.Series(dtype=object))))
    todos_meses = sorted(inventario['mes'].unique())

    def dias_do_mes(m):
        return sorted(inventario.loc[inventario['mes'] == m, 'data'])

    # ---------------------------------------------------------------- B perfil
    if 'B' in PARTES:
        try:
            log('\n[B] perfil das 16 variáveis: momentos por classe e percentis exatos por histograma')
            feito = ler_acumulado('K25_B_momentos.csv')
            pendentes = meses_a_fazer(todos_meses, feito['mes'].unique() if len(feito) else [])
            log(f'   meses a fazer: {len(pendentes)} de {len(todos_meses)}')
            mom_novos, hist_novos = [], []
            # Cada família: (nome declarado, reducer no TEMPO por pixel, reducer no ESPAÇO por classe, chave)
            FAMILIAS = [('soma_das_medias_temporais', ee.Reducer.mean(), ee.Reducer.sum(), 'sum'),
                        ('soma_dos_desvios_temporais', ee.Reducer.stdDev(), ee.Reducer.sum(), 'sum'),
                        ('pixels_com_dado', None, ee.Reducer.sum(), 'sum'),
                        ('minimo_absoluto', ee.Reducer.min(), ee.Reducer.min(), 'min'),
                        ('maximo_absoluto', ee.Reducer.max(), ee.Reducer.max(), 'max'),
                        ('pixel_dias', ee.Reducer.count(), ee.Reducer.sum(), 'sum')]
            for m in pendentes:
                dd = dias_do_mes(m)
                col_mes = {bb: ee.ImageCollection([dia(d).select([bb]) for d in dd]) for bb in BANDAS}
                bruto_fam = {}
                for nome_fam, red_t, red_e, chave_k in FAMILIAS:
                    def pilha(b, red_t=red_t):
                        if red_t is None:     # contagem de pixels que têm dado em pelo menos um dia
                            bandas = [ee.Image.constant(1).updateMask(col_mes[bb].max().mask()).rename(bb)
                                      for bb in BANDAS]
                        else:
                            bandas = [col_mes[bb].reduce(red_t).rename(bb) for bb in BANDAS]
                        return ee.Image.cat(bandas).addBands(CLASSE)
                    try:
                        partes = por_blocos(lambda b: rr(pilha(b), agrupado(red_e, len(BANDAS)), b),
                                            f'B {m} {nome_fam}')
                    except Pesado:
                        log(f'   B {m} {nome_fam}: pesado mesmo dividido; pulei')
                        continue
                    bruto_fam[nome_fam] = [ler_grupos(p, BANDAS, chave_k) for p in partes]
                # junta os blocos: soma para as somas, min/max para os extremos
                classes_vistas = sorted({k for v in bruto_fam.values() for p in v for k in p})
                for cl in classes_vistas:
                    for bb in BANDAS:
                        linha = {'mes': m, 'classe': cl, 'nome_classe': CLASSES.get(cl, f'?{cl}'), 'variavel': bb}
                        for nome_fam, _, _, _ in FAMILIAS:
                            xs = [p[cl][bb] for p in bruto_fam.get(nome_fam, [])
                                  if cl in p and p[cl].get(bb) is not None]
                            if not xs:
                                linha[nome_fam] = np.nan
                            elif nome_fam == 'minimo_absoluto':
                                linha[nome_fam] = float(np.min(xs))
                            elif nome_fam == 'maximo_absoluto':
                                linha[nome_fam] = float(np.max(xs))
                            else:
                                linha[nome_fam] = float(np.sum(xs))
                        n = linha.get('pixels_com_dado') or 0
                        # média e desvio exatos: soma dividida pelo número de pixels (não média de blocos)
                        linha['media'] = linha['soma_das_medias_temporais'] / n if n else np.nan
                        linha['desvio_temporal_medio'] = linha['soma_dos_desvios_temporais'] / n if n else np.nan
                        mom_novos.append(linha)
                # HISTOGRAMA, uma variável por pedido. O fixedHistogram vive DENTRO do reduceRegion:
                # dentro do Image.reduce ele devolveria array por pixel, e o servidor recusa somar array
                # ('Reducer input must be a number' — foi o erro da v1). Com os dias como bandas, o
                # servidor devolve um histograma por dia e a soma entre dias e blocos é feita aqui.
                for bb in BANDAS:
                    lo, hi = FAIXA[bb]
                    lo2, hi2 = lo - 0.02 * (hi - lo), hi + 0.02 * (hi - lo)

                    def faz(b, bb=bb, lo2=lo2, hi2=hi2, bins=BINS):
                        img = col_mes[bb].toBands().subtract(lo2).divide(hi2 - lo2).clamp(0, 1)
                        return rr(img, ee.Reducer.fixedHistogram(0, 1, bins), b)

                    def le(partes, bins=BINS):
                        acc = np.zeros(bins)
                        for p in partes:
                            for v in (p or {}).values():
                                if v is None:
                                    continue
                                a = np.asarray(v, dtype=float)
                                if a.ndim == 2 and a.shape[1] >= 2 and a.shape[0] == bins:
                                    acc += a[:, 1]
                        return acc

                    opcoes = [(f'{bins} bins', (lambda b, bins=bins: faz(b, bins=bins)),
                               (lambda partes, bins=bins: le(partes, bins=bins)), f'B2/{bins}bins')
                              for bins in (BINS, BINS // 2, BINS // 4)]
                    nome_usado, h = tentar(opcoes, f'B2 {m} {bb}')
                    if h is None or not h.sum():
                        log(f'   B2 {m} {bb}: sem histograma; segui')
                        continue
                    bins_usados = len(h)
                    pc = percentis_de_hist(h, lo2, hi2)
                    nb, degrau = degrau_quantizacao(h, lo2, hi2)
                    f_lo, f_hi = fracao_fora(h, lo2, hi2, FAIXA[bb])
                    hist_novos.append({'mes': m, 'variavel': bb, 'n': float(h.sum()), **pc,
                                       'bins': bins_usados,
                                       'largura_bin': (hi2 - lo2) / max(bins_usados, 1),
                                       'bins_ocupados': nb,
                                       'degrau_estimado': degrau, 'frac_abaixo_faixa': f_lo,
                                       'frac_acima_faixa': f_hi, 'faixa_declarada': f'[{lo}; {hi}]'})
                log(f'   B: {m} pronto')
            if mom_novos:
                acrescentar(pd.DataFrame(mom_novos), 'K25_B_momentos.csv')
            if hist_novos:
                acrescentar(pd.DataFrame(hist_novos), 'K25_B_percentis.csv')
            hp = ler_acumulado('K25_B_percentis.csv')
            if len(hp):
                log('\npercentis exatos (histograma de ' + str(BINS) + ' bins), último mês varrido:')
                ult = hp[hp['mes'] == hp['mes'].max()]
                log(ult[['variavel', 'n', 'p1', 'p50', 'p99', 'p99.9', 'degrau_estimado',
                         'frac_acima_faixa']].round(4).to_string(index=False))
                fora = hp[(hp['frac_acima_faixa'] > 0) | (hp['frac_abaixo_faixa'] > 0)]
                resultado('B', 'ATENCAO' if len(fora) else 'OK', 'perfil das variáveis',
                          f'{hp["variavel"].nunique()} variáveis x {hp["mes"].nunique()} meses; '
                          + (f'{len(fora)} combinações variável-mês com valor fora da faixa declarada: '
                             + ', '.join(sorted(set(fora['variavel']))) if len(fora)
                             else 'nenhum valor fora da faixa declarada'))
        except Exception as _e:
            falhou_parte('B', _e)

    # ---------------------------------------------------------------- C/D invariantes e limites
    if 'C' in PARTES or 'D' in PARTES:
        try:
            log('\n[C+D] invariantes físicas e limites de Xavier et al. (2022), todos os dias, por classe')
            # prefixo 'i_' = INFORMAÇÃO (assimetria entre rotas), não violação: fica fora do veredito.
            NOMES = ['n_pix',
                     'rs_gt_rso_motor', 'rs_gt_rso_audit', 'etr_gt_eto', 'transp_gt_etr', 'tmax_lt_tmin',
                     'rh_fora', 'solo_gt_max',
                     'runoff_sup_gt_pr', 'i_runoff_total_gt_pr', 'negativo', 'eto_zero_com_rs',
                     'vpd_incoerente', 'i_sm5_muito_acima_sm100',
                     'pr_ge_450', 'rs_ge_ra', 'rs_lt_003ra', 'u2_fora', 't_fora']
            feito = ler_acumulado('K25_CD_invariantes.csv')
            pendentes = meses_a_fazer(todos_meses, feito['mes'].unique() if len(feito) else [])
            novos = []
            for m in pendentes:
                dd = dias_do_mes(m)
                tam = DIAS_POR_PEDIDO
                i = 0
                while i < len(dd):
                    lote = dd[i:i + tam]

                    def flags(b, lote=lote):
                        saida = []
                        for d in lote:
                            img = dia(d)
                            rso = rso_fao56(d)
                            ra = ra_fao56(d)
                            pr = img.select('pr_mm')
                            rs = img.select('rs')
                            eto = img.select('et_potencial')
                            etr = img.select('et_real')
                            sm5 = img.select('soil_moisture_0_5cm_m3_m3')
                            sm100 = img.select('soil_moisture_0_100cm_m3_m3')
                            teto = UMIDADE_MAX_FISICA + 1e-4
                            # Só o escoamento SUPERFICIAL é limitado pela chuva do dia. O subsuperficial
                            # é drenagem do armazenamento (escoamento de base) e passa da chuva do dia
                            # sem nenhuma anomalia: testar a SOMA deu 2.000.165 falsos positivos (8,5%
                            # do acervo) na corrida de 09h31. A soma vira informação, não invariante.
                            runoff = img.select('runoff_sup_mm')
                            neg = (pr.lt(-1e-6).Or(rs.lt(-1e-6)).Or(img.select('u2').lt(-1e-6))
                                   .Or(eto.lt(-1e-6)).Or(img.select('vpd').lt(-1e-6))
                                   .Or(etr.lt(-1e-6)).Or(img.select('transpiracao_mm').lt(-1e-6)))
                            saida += [
                                ee.Image.constant(1).updateMask(pr.mask()).rename('n_pix'),
                                rs.gt(rso.multiply(1.0 + TOL_RSO_MOTOR)).rename('rs_gt_rso_motor'),
                                rs.gt(rso.multiply(1.0 + TOL_RSO_AUDIT)).rename('rs_gt_rso_audit'),
                                etr.gt(eto.add(0.001)).rename('etr_gt_eto'),
                                img.select('transpiracao_mm').gt(etr.add(0.001)).rename('transp_gt_etr'),
                                img.select('tmax_C').lt(img.select('tmin_C')).rename('tmax_lt_tmin'),
                                img.select('RH').lt(0).Or(img.select('RH').gt(100)).rename('rh_fora'),
                                sm100.gt(teto).Or(sm5.gt(teto)).rename('solo_gt_max'),
                                # ---- seis que o motor NÃO testa
                                runoff.gt(pr.add(0.01)).rename('runoff_sup_gt_pr'),
                                img.select('runoff_sup_mm').add(img.select('runoff_sub_mm'))
                                .gt(pr.add(0.01)).rename('i_runoff_total_gt_pr'),
                                neg.rename('negativo'),
                                eto.lt(1e-6).And(rs.gt(1.0)).rename('eto_zero_com_rs'),
                                img.select('vpd').gt(es_sat(img)).rename('vpd_incoerente'),
                                # Não é violação: na rota GFS a camada rasa é um balde de 50 mm que satura
                            # antes da profunda. Assimetria entre rotas, logo informação.
                                sm5.gt(sm100.add(0.3)).rename('i_sm5_muito_acima_sm100'),
                                # ---- limites absolutos de Xavier et al. (2022)
                                pr.gte(LIM_PR[1]).rename('pr_ge_450'),
                                rs.gte(ra).rename('rs_ge_ra'),
                                rs.lt(ra.multiply(LIM_RS_FRAC[0])).And(rs.gt(0)).rename('rs_lt_003ra'),
                                img.select('u2').lt(LIM_U2[0]).Or(img.select('u2').gt(LIM_U2[1])).rename('u2_fora'),
                                (img.select('tmax_C').gte(LIM_T[1]).Or(img.select('tmin_C').lte(LIM_T[0]))
                                 ).rename('t_fora'),
                            ]
                        n = len(NOMES)
                        return ee.Image.cat([ee.Image.cat(saida[k * n:(k + 1) * n]).unmask(0)
                                             for k in range(len(lote))]).addBands(CLASSE)

                    try:
                        partes = por_blocos(lambda b: rr(flags(b), agrupado(ee.Reducer.sum(), len(NOMES) * len(lote)), b),
                                            f'CD {lote[0]}')
                    except Pesado:
                        if tam > 1:
                            tam = max(1, tam // 2)
                            log(f'   CD {lote[0]}: pesado; lote cai para {tam} dia(s)')
                            continue
                        raise
                    nomes_lote = [f'{nm}__{k}' for k in range(len(lote)) for nm in NOMES]
                    g = somar_grupos([ler_grupos(p, nomes_lote, 'sum') for p in partes], nomes_lote)
                    for k, d in enumerate(lote):
                        for cl, vals in g.items():
                            novos.append({'mes': m, 'data': d, 'rota': dias_rota.get(d), 'classe': cl,
                                          'nome_classe': CLASSES.get(cl, f'?{cl}'),
                                          **{nm: int(round(vals.get(f'{nm}__{k}') or 0)) for nm in NOMES}})
                    log(f'   CD: {lote[0]} a {lote[-1]} lidos')
                    i += len(lote)
                if novos:
                    acrescentar(pd.DataFrame(novos), 'K25_CD_invariantes.csv')
                    novos = []
            cd = ler_acumulado('K25_CD_invariantes.csv')
            if len(cd):
                tot = {cl: {c: cd.loc[cd['classe'] == cl, c].sum() for c in NOMES}
                       for cl in sorted(cd['classe'].unique())}
                st, texto = decidir_invariantes(tot)
                resultado('C', st, 'invariantes físicas e limites absolutos, todos os dias varridos', texto)
                porclasse = cd.groupby('nome_classe')[NOMES].sum()
                log('\nviolações por classe:\n' + porclasse.loc[:, (porclasse.sum() > 0) | (porclasse.columns == 'n_pix')].to_string())
                porrota = cd.groupby('rota')[NOMES].sum()
                log('\nviolações por rota:\n' + porrota.loc[:, (porrota.sum() > 0) | (porrota.columns == 'n_pix')].to_string())
                gravar(porclasse.reset_index(), 'K25_CD_por_classe.csv')
                gravar(porrota.reset_index(), 'K25_CD_por_rota.csv')

                # localiza cada pixel violador dos dias com violação (sample factor=1: varre TODOS os pixels)
                alvos = cd[cd[[c for c in NOMES if c != 'n_pix']].sum(axis=1) > 0]['data'].unique().tolist()
                if alvos:
                    log(f'\n   localizando os pixels violadores em {len(alvos)} dia(s)')
                    achados = []
                    for d in alvos[:40]:
                        img = dia(d)
                        rso, ra = rso_fao56(d), ra_fao56(d)
                        ruim = (img.select('rs').gt(rso.multiply(1.0 + TOL_RSO_MOTOR))
                                .Or(img.select('rs').gte(ra))
                                .Or(img.select('et_real').gt(img.select('et_potencial').add(0.001)))
                                .Or(img.select('tmax_C').lt(img.select('tmin_C')))
                                .Or(img.select('RH').lt(0).Or(img.select('RH').gt(100))))
                        alvo = (img.select(['rs', 'pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real'])
                                .addBands([rso, ra, ELEV.rename('elev'), CLASSE]).updateMask(ruim))
                        for b in BLOCOS:
                            try:
                                fs = gi(alvo.sample(region=geom(b), projection=PROJ, factor=1, seed=SEMENTE,
                                                    geometries=True, dropNulls=True, tileScale=16)
                                        .limit(MAX_PIXELS_LISTA), f'violadores {d}')['features']
                            except Pesado:
                                continue
                            for f in fs:
                                p = f['properties']
                                achados.append({'data': d, 'lon': round(f['geometry']['coordinates'][0], 4),
                                                'lat': round(f['geometry']['coordinates'][1], 4),
                                                'classe': p.get('classe'), **{k: p.get(k) for k in
                                                ('rs', 'rso', 'ra', 'elev', 'pr_mm', 'tmax_C', 'tmin_C', 'RH',
                                                 'et_potencial', 'et_real')}})
                    if achados:
                        av = pd.DataFrame(achados)
                        av['rs_sobre_rso'] = av['rs'] / av['rso']
                        av['rs_sobre_ra'] = av['rs'] / av['ra']
                        gravar(av.round(4), 'K25_D_pixels_violadores.csv')
                        log(av.head(20).round(3).to_string(index=False))
                        resultado('D', 'ATENCAO', 'pixels violadores localizados',
                                  f'{len(av)} pixel-dias listados em K25_D_pixels_violadores.csv; '
                                  f'classes {sorted(set(av["classe"].dropna()))}; '
                                  f'maior rs/Rso {av["rs_sobre_rso"].max():.4f}, maior rs/Ra {av["rs_sobre_ra"].max():.4f}')
        except Exception as _e:
            falhou_parte('C+D', _e)

    # ---------------------------------------------------------------- E recorde do pixel
    if 'E' in PARTES:
        try:
            log('\n[E] excesso sobre o recorde do próprio pixel, por rota E POR MÊS')
            VARS_REC = [('tmax_C', 'Tmax'), ('tmin_C', 'Tmin'), ('pr_mm', 'pr'), ('rs', 'Rs'), ('u2', 'u2')]
            feito = ler_acumulado('K25_E_recorde.csv')
            pendentes = meses_a_fazer(todos_meses, feito['mes'].unique() if len(feito) else [])
            novos = []
            for m in pendentes:
                dd = dias_do_mes(m)
                mes_num = int(m[5:7])
                for sab_b, br_b in VARS_REC:
                    modo, limiares, unidade = LIMIARES_REC[sab_b]

                    # DUAS imagens: indicadores (unmask 0, somados) e excesso (mascarado, para o máximo).
                    # Misturar as duas numa só contamina a soma onde o pixel é mascarado.
                    def ind(b, dd=dd, sab_b=sab_b, br_b=br_b, mes_num=mes_num, modo=modo, limiares=limiares):
                        rec = recorde(br_b, mes_num)
                        saida = []
                        for d in dd:
                            x = dia(d).select(sab_b)
                            saida.append(ee.Image.constant(1).updateMask(x.mask().And(rec.mask())).rename('n'))
                            for j, t in enumerate(limiares):
                                alvo = rec.add(t) if modo == 'mais' else rec.multiply(t)
                                saida.append(x.gt(alvo).updateMask(x.mask().And(rec.mask())).rename(f'g{j}'))
                        return ee.Image.cat([t.unmask(0) for t in saida]).addBands(CLASSE)

                    def exc(b, dd=dd, sab_b=sab_b, br_b=br_b, mes_num=mes_num):
                        rec = recorde(br_b, mes_num)
                        return ee.Image.cat([dia(d).select(sab_b).subtract(rec).rename('exc')
                                             for d in dd]).addBands(CLASSE)
                    n_ind = 1 + len(limiares)
                    try:
                        partes_s = por_blocos(lambda b: rr(ind(b), agrupado(ee.Reducer.sum(), n_ind * len(dd)), b),
                                              f'E {m} {sab_b}')
                        partes_x = por_blocos(lambda b: rr(exc(b), agrupado(ee.Reducer.max(), len(dd)), b),
                                              f'E {m} {sab_b} max')
                    except Pesado:
                        log(f'   E {m} {sab_b}: pesado; pulei')
                        continue
                    nomes = [f'{n}__{k}' for k in range(len(dd))
                             for n in ['n'] + [f'g{j}' for j in range(len(limiares))]]
                    nomes_x = [f'exc__{k}' for k in range(len(dd))]
                    gs = somar_grupos([ler_grupos(p, nomes, 'sum') for p in partes_s], nomes)
                    gx = [ler_grupos(p, nomes_x, 'max') for p in partes_x]
                    for k, d in enumerate(dd):
                        for cl, v in gs.items():
                            # as somas vêm de bandas com unmask(-9999): só 'n' e 'g*' são indicadores limpos
                            n = max(0.0, (v.get(f'n__{k}') or 0))
                            linha = {'mes': m, 'data': d, 'rota': dias_rota.get(d), 'faixa': dias_faixa.get(d),
                                     'classe': cl, 'nome_classe': CLASSES.get(cl, f'?{cl}'), 'variavel': sab_b,
                                     'modo': modo, 'n': int(n)}
                            for j, t in enumerate(limiares):
                                bruto = v.get(f'g{j}__{k}')
                                linha[f'limiar_{j}'] = t
                                linha[f'pct_acima_{j}'] = (100.0 * bruto / n) if (n and bruto is not None) else np.nan
                            linha['excesso_max'] = max([x[cl][f'exc__{k}'] for x in gx
                                                        if cl in x and x[cl].get(f'exc__{k}') is not None]
                                                       or [np.nan])
                            novos.append(linha)
                log(f'   E: {m} pronto')
                if novos:
                    acrescentar(pd.DataFrame(novos), 'K25_E_recorde.csv')
                    novos = []
            E = ler_acumulado('K25_E_recorde.csv')
            if len(E):
                # ERA5 x GFS DENTRO DO MESMO MÊS: o que a K24 não fez (ela comparou outubro com novembro)
                comp = []
                for (m, v, cl), g in E.groupby(['mes', 'variavel', 'nome_classe']):
                    a = g.loc[g['rota'] == 'ERA5'].groupby('data')['pct_acima_1'].mean().dropna()
                    b = g.loc[g['rota'] == 'GFS'].groupby('data')['pct_acima_1'].mean().dropna()
                    if len(a) >= 2 and len(b) >= 2:
                        dif, p, na, nb = permutacao(a.values, b.values)
                        comp.append({'mes': m, 'variavel': v, 'classe': cl, 'media_ERA5': float(a.mean()),
                                     'media_GFS': float(b.mean()), 'diferenca': dif, 'p_permutacao': p,
                                     'n_dias_ERA5': na, 'n_dias_GFS': nb,
                                     'significativo_alfa_005': bool(np.isfinite(p) and p < ALFA)})
                if comp:
                    cp = pd.DataFrame(comp)
                    gravar(cp.round(6), 'K25_E_rotas_mesmo_mes.csv')
                    log('\nERA5 x GFS no MESMO mês e na MESMA classe (% de pixel-dias acima do limiar 1):')
                    log(cp.round(4).to_string(index=False))
                linhas_res = []
                for (v, rota), t in E.groupby(['variavel', 'rota'], dropna=False):
                    peso = t['n'].clip(lower=1)
                    linhas_res.append({'variavel': v, 'rota': rota, 'dias': t['data'].nunique(),
                                       'pixel_dias': int(t['n'].sum()),
                                       **{f'pct_acima_{j}': float(np.average(t[f'pct_acima_{j}'].fillna(0), weights=peso))
                                          for j in (0, 1, 2) if f'pct_acima_{j}' in t},
                                       'excesso_max': float(t['excesso_max'].max())})
                resumo = pd.DataFrame(linhas_res)
                # Antes de concluir qualquer coisa: a REFERÊNCIA é confiável? O recorde sai de uma
                # decodificação do BR-DWGD que é suposição. Se um campo passa do recorde de 35 anos em
                # mais de MAX_PCT_REFERENCIA_SUSPEITA, a explicação mais provável é a referência errada,
                # e reportar o número como achado seria inventar um defeito. Então a variável é
                # suprimida do veredito e o motivo vai escrito.
                de_para = {'tmax_C': 'Tmax', 'tmin_C': 'Tmin', 'pr_mm': 'pr', 'rs': 'Rs', 'u2': 'u2'}
                resumo['decodificacao_conferida'] = [DECODE_CONFERIDO.get(de_para.get(v), False)
                                                     for v in resumo['variavel']]
                resumo['referencia_suspeita'] = ((resumo['pct_acima_0'] > MAX_PCT_REFERENCIA_SUSPEITA)
                                                 | (~resumo['decodificacao_conferida']))
                gravar(resumo.round(5), 'K25_E_resumo.csv')
                log('\n' + resumo.round(4).to_string(index=False))
                suspeitas = sorted(set(resumo.loc[resumo['referencia_suspeita'], 'variavel']))
                bom = resumo[~resumo['referencia_suspeita']]
                if suspeitas:
                    log('\n   REFERÊNCIA SUSPEITA e por isso SUPRIMIDA do veredito: '
                        + ', '.join(suspeitas))
                    for v in suspeitas:
                        pc = resumo.loc[resumo['variavel'] == v, 'pct_acima_0'].max()
                        log(f'      {v}: {pc:.2f}% dos pixel-dias acima do recorde. Um campo plausível '
                            f'fica na ordem de 0,1%; isto é assinatura de recorde mal decodificado '
                            f'(confira escala e deslocamento de {de_para.get(v, v)} em DECODE_BR).')
                if len(bom):
                    pior = bom.sort_values('pct_acima_1', ascending=False).iloc[0]
                    resultado('E', 'ATENCAO' if pior['pct_acima_1'] > 1.0 else 'INFO',
                              'excesso sobre o recorde do pixel por variável e rota',
                              f'pior caso entre as variáveis com referência confiável: {pior["variavel"]} na '
                              f'rota {pior["rota"]}, {pior["pct_acima_1"]:.3f}% dos pixel-dias acima do '
                              f'limiar 1 (maior excesso {pior["excesso_max"]:+.2f}). Para um campo bem '
                              f'calibrado contra um recorde de {ANOS_RECORDE[1] - ANOS_RECORDE[0] + 1} anos a '
                              f'expectativa é da ordem de 0,1%: acima de 1% é desacordo distribucional, não '
                              f'clima.'
                              + (f' SUPRIMIDAS por referência suspeita: {", ".join(suspeitas)}.'
                                 if suspeitas else ''))
                else:
                    resultado('E', 'FALHOU', 'excesso sobre o recorde do pixel',
                              'nenhuma variável tem referência confiável: a decodificação do BR-DWGD em '
                              'DECODE_BR precisa ser conferida antes deste teste valer.')
        except Exception as _e:
            falhou_parte('E', _e)

    # ---------------------------------------------------------------- F emenda por variável
    if 'F' in PARTES:
        try:
            log(f'\n[F] emenda: razão dos desvios por variável em {N_PONTOS_EMENDA} pixels de classe A')
            sorteio = (ee.Image.pixelLonLat().addBands(CLASSE)
                       .stratifiedSample(numPoints=0, classBand='classe', region=geom((-75.0, -35.0, -28.0, 6.5)),
                                         projection=PROJ, seed=SEMENTE, classValues=[1],
                                         classPoints=[N_PONTOS_EMENDA], geometries=True, tileScale=16))
            pts = [{'pid': k, 'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1]}
                   for k, f in enumerate(gi(sorteio, 'pontos da emenda')['features'])]
            fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]), {'pid': p['pid']})
                                       for p in pts])
            chave = {(int(math.floor((p['lon'] - X0) / DX + 1e-6)),
                      int(math.floor((Y0 - p['lat']) / DX + 1e-6))): p['pid'] for p in pts}
            PARES = [('pr_mm', 'pr'), ('tmax_C', 'Tmax'), ('tmin_C', 'Tmin'), ('RH', 'RH'), ('rs', 'Rs'), ('u2', 'u2')]
            ref = []
            for mes in range(1, 13):
                if not any(int(m[5:7]) == mes for m in todos_meses):
                    continue
                # O Earth Engine exige que a função passada a List.map e a ImageCollection.map receba
                # EXATAMENTE um argumento. Um parâmetro com valor padrão já conta como segundo, e o servidor
                # recusa com 'List.map: A mapped algorithm must take one argument.' — foi o erro desta parte
                # na corrida de 09h31. Por isso a variável é fechada numa fábrica, sem argumento padrão.
                def fab_br_var(nome_br):
                    def f(img):
                        return br_var(img, nome_br)
                    return f
                
                def fab_por_ano(mes_alvo):
                    def por_ano(a):
                        sub = (BR.filter(ee.Filter.calendarRange(a, a, 'year'))
                               .filter(ee.Filter.calendarRange(mes_alvo, mes_alvo, 'month')))
                        return ee.Image.cat([sub.map(fab_br_var(v)).reduce(ee.Reducer.stdDev())
                                             .rename(f'{s}_sd') for s, v in PARES])
                    return por_ano
                
                anos = ee.List.sequence(*ANOS_REF_EMENDA)
                sd = ee.ImageCollection(anos.map(fab_por_ano(mes))).mean()
                me = ee.Image.cat([(BR.filter(ee.Filter.calendarRange(*ANOS_REF_EMENDA, 'year'))
                                    .filter(ee.Filter.calendarRange(mes, mes, 'month'))
                                    .map(fab_br_var(v)).mean().rename(f'{s}_m')) for s, v in PARES])
                r = gi(sd.addBands(me).sampleRegions(collection=fc, properties=['pid'], projection=PROJ,
                                                     geometries=False, tileScale=16), f'BR-DWGD mês {mes:02d}')
                ref += [dict(f['properties'], mes=mes) for f in r['features']]
            ref = pd.DataFrame(ref)
            if not len(ref) or 'pid' not in ref:
                resultado('F', 'FALHA', 'razão dos desvios na emenda',
                          'o BR-DWGD não devolveu referência nos pixels sorteados: confira o asset e a decodificação')
                ref = pd.DataFrame(columns=['pid', 'mes'])
            linhas = []
            for rota in ('ERA5', 'GFS'):
                datas = [d for d, r in dias_rota.items() if r == rota and d[:7] in set(todos_meses)]
                if len(datas) < 10:
                    continue
                sab = []
                for m in sorted({d[:7] for d in datas}):
                    dm = sorted(d for d in datas if d[:7] == m)
                    reg = gi(ee.ImageCollection([dia(d).select([s for s, _ in PARES]) for d in dm])
                             .getRegion(ee.Geometry.MultiPoint([[p['lon'], p['lat']] for p in pts]), None,
                                        CRS, TRANSFORM), f'SAB {rota} {m}')
                    df = pd.DataFrame(reg[1:], columns=reg[0])
                    ix = np.floor((df['longitude'].astype(float) - X0) / DX + 1e-6).astype(int)
                    iy = np.floor((Y0 - df['latitude'].astype(float)) / DX + 1e-6).astype(int)
                    df['pid'] = [chave.get((a, b)) for a, b in zip(ix, iy)]
                    df['data'] = pd.to_datetime(df['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d')
                    sab.append(df.dropna(subset=['pid'])[['pid', 'data'] + [s for s, _ in PARES]])
                if not sab:
                    continue
                sab = pd.concat(sab, ignore_index=True)
                sab['pid'] = sab['pid'].astype(int)
                for s, _ in PARES:
                    sab[s] = pd.to_numeric(sab[s], errors='coerce')
                for s, _ in PARES:
                    if f'{s}_sd' not in ref.columns:
                        continue
                    razao, vies, n = razao_e_vies(sab, ref, s)
                    linhas.append({'rota': rota, 'variavel': s, 'razao_desvio': razao, 'vies_medio': vies,
                                   'n_pixel_mes': n, 'dentro_085_115': bool(0.85 <= razao <= 1.15)
                                   if np.isfinite(razao) else None})
            if not linhas:
                resultado('F', 'FALHOU', 'razão dos desvios na emenda',
                          'nenhuma variável pôde ser medida. Causas prováveis: o BR-DWGD não devolveu '
                          'desvio nos pixels sorteados (confira a decodificação em DECODE_BR), menos de '
                          '10 dias por pixel-mês no intervalo pedido, ou nenhuma rota com 10 dias ou mais. '
                          'Rode a parte F sozinha com um intervalo de pelo menos um mês cheio por rota.')
            if linhas:
                F = pd.DataFrame(linhas)
                gravar(F.round(5), 'K25_F_emenda.csv')
                log('\n' + F.round(3).to_string(index=False))
                fora = F[F['dentro_085_115'] == False]
                resultado('F', 'FALHA' if len(fora) else 'OK', 'razão dos desvios na emenda, por variável e rota',
                          (', '.join(f'{r.rota}/{r.variavel} {r.razao_desvio:.2f}' for r in fora.itertuples())
                           + ' fora de [0,85; 1,15]' if len(fora) else 'todas as variáveis dentro de [0,85; 1,15]')
                          + ' | a K22 mede isto só para a UR')
        except Exception as _e:
            falhou_parte('F', _e)

    # ---------------------------------------------------------------- G derivadas
    if 'G' in PARTES:
        try:
            log('\n[G] coerência das derivadas: ETo e VPD recalculados das primárias gravadas')
            feito = ler_acumulado('K25_G_derivadas.csv')
            pendentes = meses_a_fazer(todos_meses, feito['mes'].unique() if len(feito) else [])
            novos = []
            for m in pendentes:
                dd = dias_do_mes(m)
                for lote in lotes(dd, DIAS_POR_PEDIDO):
                    def flags(b, lote=lote):
                        saida = []
                        for d in lote:
                            img = dia(d)
                            eto_calc = eto_ee(img, d)
                            vpd_calc = vpd_ee(img)
                            de = img.select('et_potencial').subtract(eto_calc).abs()
                            dv = img.select('vpd').subtract(vpd_calc).abs()
                            saida += [ee.Image.constant(1).updateMask(img.select('et_potencial').mask()).rename('n'),
                                      de.gt(TOL_ETO).rename('eto_difere'),
                                      dv.gt(TOL_VPD).rename('vpd_difere'),
                                      de.rename('eto_dif_abs'), dv.rename('vpd_dif_abs')]
                        return ee.Image.cat([s.unmask(0) for s in saida]).addBands(CLASSE)
                    def difs(b, lote=lote):
                        saida = []
                        for d in lote:
                            img = dia(d)
                            saida += [img.select('et_potencial').subtract(eto_ee(img, d)).abs().rename('eto_dif_abs'),
                                      img.select('vpd').subtract(vpd_ee(img)).abs().rename('vpd_dif_abs')]
                        return ee.Image.cat(saida).addBands(CLASSE)
                    try:
                        partes_s = por_blocos(lambda b: rr(flags(b), agrupado(ee.Reducer.sum(), 5 * len(lote)), b),
                                              f'G {lote[0]}')
                        partes_x = por_blocos(lambda b: rr(difs(b), agrupado(ee.Reducer.max(), 2 * len(lote)), b),
                                              f'G max {lote[0]}')
                    except Pesado:
                        log(f'   G {lote[0]}: pesado; pulei o lote')
                        continue
                    nomes = [f'{n}__{k}' for k in range(len(lote))
                             for n in ('n', 'eto_difere', 'vpd_difere', 'eto_dif_abs', 'vpd_dif_abs')]
                    nomes_x = [f'{n}__{k}' for k in range(len(lote)) for n in ('eto_dif_abs', 'vpd_dif_abs')]
                    gs = somar_grupos([ler_grupos(p, nomes, 'sum') for p in partes_s], nomes)
                    gx = [ler_grupos(p, nomes_x, 'max') for p in partes_x]
                    for k, d in enumerate(lote):
                        for cl, v in gs.items():
                            n = v.get(f'n__{k}') or 0
                            mx_eto = max([x[cl][f'eto_dif_abs__{k}'] for x in gx
                                          if cl in x and x[cl].get(f'eto_dif_abs__{k}') is not None] or [np.nan])
                            mx_vpd = max([x[cl][f'vpd_dif_abs__{k}'] for x in gx
                                          if cl in x and x[cl].get(f'vpd_dif_abs__{k}') is not None] or [np.nan])
                            novos.append({'mes': m, 'data': d, 'rota': dias_rota.get(d), 'classe': cl,
                                          'nome_classe': CLASSES.get(cl, f'?{cl}'), 'n': int(n),
                                          'eto_difere': int(v.get(f'eto_difere__{k}') or 0),
                                          'vpd_difere': int(v.get(f'vpd_difere__{k}') or 0),
                                          'eto_dif_media': (v.get(f'eto_dif_abs__{k}') or 0) / n if n else np.nan,
                                          'vpd_dif_media': (v.get(f'vpd_dif_abs__{k}') or 0) / n if n else np.nan,
                                          'eto_dif_max': mx_eto, 'vpd_dif_max': mx_vpd})
                    log(f'   G: {lote[0]} a {lote[-1]} lidos')
                if novos:
                    acrescentar(pd.DataFrame(novos), 'K25_G_derivadas.csv')
                    novos = []
            G = ler_acumulado('K25_G_derivadas.csv')
            if len(G):
                por = G.groupby('rota').agg(dias=('data', 'nunique'), n=('n', 'sum'),
                                            eto_difere=('eto_difere', 'sum'), vpd_difere=('vpd_difere', 'sum'),
                                            eto_dif_max=('eto_dif_max', 'max'), vpd_dif_max=('vpd_dif_max', 'max'))
                log('\n' + por.to_string())
                gravar(por.reset_index(), 'K25_G_resumo.csv')
                ruim = int(por['eto_difere'].sum() + por['vpd_difere'].sum())
                resultado('G', 'FALHA' if ruim else 'OK', 'ETo e VPD gravados conferem com as primárias gravadas',
                          f'{ruim:,} pixel-dias divergem (tolerância ETo {TOL_ETO} mm, VPD {TOL_VPD} kPa); '
                          f'maior divergência ETo {por["eto_dif_max"].max():.4f} mm, VPD {por["vpd_dif_max"].max():.4f} kPa. '
                          f'Nos dias definitivos a ETo vem do BR-DWGD e a divergência é esperada: olhe por rota.')
        except Exception as _e:
            falhou_parte('G', _e)

    # ---------------------------------------------------------------- H máscara e balanço
    if 'H' in PARTES:
        try:
            log('\n[H] máscara banda a banda e balanço hídrico')
            feito = ler_acumulado('K25_H_mascara.csv')
            pendentes = meses_a_fazer(todos_meses, feito['mes'].unique() if len(feito) else [])
            novos = []
            for m in pendentes:
                dd = dias_do_mes(m)
                for lote in lotes(dd, DIAS_POR_PEDIDO):
                    def conta(b, lote=lote):
                        saida = []
                        for d in lote:
                            img = dia(d)
                            saida += [ee.Image.constant(1).updateMask(img.select(bb).mask()).rename(bb)
                                      for bb in BANDAS]
                        return ee.Image.cat([s.unmask(0) for s in saida]).addBands(CLASSE)
                    try:
                        partes = por_blocos(lambda b: rr(conta(b), agrupado(ee.Reducer.sum(), len(BANDAS) * len(lote)), b),
                                            f'H {lote[0]}')
                    except Pesado:
                        log(f'   H {lote[0]}: pesado; pulei o lote')
                        continue
                    nomes = [f'{bb}__{k}' for k in range(len(lote)) for bb in BANDAS]
                    g = somar_grupos([ler_grupos(p, nomes, 'sum') for p in partes], nomes)
                    for k, d in enumerate(lote):
                        for cl, v in g.items():
                            linha = {'mes': m, 'data': d, 'rota': dias_rota.get(d), 'classe': cl,
                                     'nome_classe': CLASSES.get(cl, f'?{cl}')}
                            linha.update({bb: int(round(v.get(f'{bb}__{k}') or 0)) for bb in BANDAS})
                            novos.append(linha)
                    log(f'   H: {lote[0]} a {lote[-1]} lidos')
                if novos:
                    acrescentar(pd.DataFrame(novos), 'K25_H_mascara.csv')
                    novos = []
            H = ler_acumulado('K25_H_mascara.csv')
            if len(H):
                por_dia = H.groupby(['data', 'rota'], dropna=False)[BANDAS].sum().reset_index()
                por_dia['maximo'] = por_dia[BANDAS].max(axis=1)
                falta = []
                for bb in BANDAS:
                    d = (por_dia['maximo'] - por_dia[bb])
                    if d.max() > 0:
                        falta.append({'variavel': bb, 'dias_com_falta': int((d > 0).sum()),
                                      'pior_dia': por_dia.loc[d.idxmax(), 'data'],
                                      'rota_pior': por_dia.loc[d.idxmax(), 'rota'],
                                      'pixels_a_menos': int(d.max()),
                                      'pct_a_menos': float(100 * d.max() / por_dia.loc[d.idxmax(), 'maximo'])})
                if falta:
                    fv = pd.DataFrame(falta).sort_values('pixels_a_menos', ascending=False)
                    gravar(fv, 'K25_H_vazamento_mascara.csv')
                    log('\nbandas com menos pixels que a banda mais completa do mesmo dia:\n'
                        + fv.to_string(index=False))
                resultado('H', 'ATENCAO' if falta else 'OK', 'máscara igual nas 16 bandas',
                          (f'{len(falta)} banda(s) com pixels a menos: '
                           + ', '.join(f'{r["variavel"]} (até {r["pixels_a_menos"]:,} px, {r["pct_a_menos"]:.3f}%)'
                                       for _, r in pd.DataFrame(falta).iterrows())
                           + '. Uma banda com menos pixels que as outras é vazamento de máscara: o valor foi '
                             'descartado em vez de preservado.') if falta
                          else 'as 16 bandas têm o mesmo número de pixels em todos os dias varridos')
        except Exception as _e:
            falhou_parte('H', _e)

    fechar(T0)


def es_sat(img):
    """es médio do dia a partir da Tmax e da Tmin gravadas (para checar o VPD)."""
    import ee
    def es(T):
        return T.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': T})
    return es(img.select('tmax_C')).add(es(img.select('tmin_C'))).divide(2).rename('es')


def vpd_ee(img):
    return es_sat(img).multiply(ee_const(1).subtract(img.select('RH').divide(100))).max(0).rename('vpd_calc')


def ee_const(v):
    import ee
    return ee.Image.constant(v)


def eto_ee(img, d):
    """ETo FAO-56 exatamente como o eto_penman_monteith do motor V1.6, a partir das bandas GRAVADAS."""
    import ee
    ELEV = ee.Image('USGS/SRTMGL1_003')
    tmax, tmin = img.select('tmax_C'), img.select('tmin_C')
    rh, u2, rs = img.select('RH'), img.select('u2'), img.select('rs')
    lat = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180.0)
    p = ELEV.multiply(-0.0065).add(293.0).divide(293.0).pow(5.26).multiply(101.3)
    gamma = p.multiply(0.000665)
    tm = tmax.add(tmin).divide(2)

    def es(T):
        return T.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': T})
    esm = es(tmax).add(es(tmin)).divide(2)
    ea = esm.multiply(rh).divide(100)
    vpd = esm.subtract(ea).max(0)
    J = ee.Number(ee.Date(d).getRelative('day', 'year')).add(1)
    dr = J.multiply(2.0 * math.pi / 365.0).cos().multiply(0.033).add(1.0)
    de = J.multiply(2.0 * math.pi / 365.0).subtract(1.39).sin().multiply(0.409)
    ws = lat.tan().multiply(de.tan()).multiply(-1.0).clamp(-1.0, 1.0).acos()
    Ra = (ws.multiply(lat.sin()).multiply(de.sin())
          .add(lat.cos().multiply(de.cos()).multiply(ws.sin()))
          .multiply(dr).multiply((24.0 * 60.0 / math.pi) * 0.0820))
    Rso = ELEV.multiply(0.00002).add(0.75).multiply(Ra)
    rs_rso = rs.divide(Rso).clamp(0.0, 1.0)
    rad = tmax.add(273.16).pow(4).add(tmin.add(273.16).pow(4)).divide(2.0).multiply(4.903e-9)
    Rn = rs.multiply(0.77).subtract(
        rad.multiply(ea.sqrt().multiply(-0.14).add(0.34)).multiply(rs_rso.multiply(1.35).subtract(0.35)).max(0))
    delta = tm.expression('4283.58 * (0.6108 * exp(17.625 * T / (T + 243.04))) / ((T + 243.04) ** 2)', {'T': tm})
    num = delta.multiply(Rn).multiply(0.408).add(
        gamma.multiply(ee.Image(900).divide(tm.add(273))).multiply(u2).multiply(vpd))
    den = delta.add(gamma.multiply(ee.Image(1).add(u2.multiply(0.34))))
    return num.divide(den).max(0).rename('eto_calc')


# =========================================================================================
# Z — estatística sobre os CSV (roda sem Earth Engine; pode rodar no seu computador)
# =========================================================================================
def parte_Z():
    log('\n[Z] estatística: descritivo, outliers, bootstrap de blocos e teste de permutação')
    log(f'   nível de significância declarado: alfa = {ALFA}; {N_BOOT} réplicas de bootstrap, '
        f'{N_PERM} permutações; unidade de reamostragem: bloco de 5 dias consecutivos')
    linhas = []
    E = ler_acumulado('K25_E_recorde.csv')
    if len(E):
        for (v, cl), g in E.groupby(['variavel', 'nome_classe']):
            for rota, gr in g.groupby('rota', dropna=False):
                x = gr.groupby('data')['pct_acima_1'].mean().sort_index().values
                lo, hi = bootstrap_blocos(x)
                mod, ext, lim = outliers_tukey(x)
                linhas.append({'tabela': 'E', 'metrica': 'pct_acima_1', 'variavel': v, 'classe': cl,
                               'grupo': rota, 'n_dias': int(np.isfinite(x).sum()),
                               'media': float(np.nanmean(x)) if len(x) else np.nan,
                               'mediana': float(np.nanmedian(x)) if len(x) else np.nan,
                               'desvio': float(np.nanstd(x, ddof=1)) if len(x) > 1 else np.nan,
                               'ic95_inf': lo, 'ic95_sup': hi, 'outliers_15iqr': mod, 'outliers_30iqr': ext,
                               'limite_inf_tukey': lim[0], 'limite_sup_tukey': lim[1]})
    CD = ler_acumulado('K25_CD_invariantes.csv')
    if len(CD):
        flags = [c for c in CD.columns if c not in ('mes', 'data', 'rota', 'classe', 'nome_classe', 'n_pix')]
        for f in flags:
            if CD[f].sum() == 0:
                continue
            for rota, gr in CD.groupby('rota', dropna=False):
                x = (gr.groupby('data')[f].sum() / gr.groupby('data')['n_pix'].sum().clip(lower=1) * 100).values
                lo, hi = bootstrap_blocos(x)
                mod, ext, lim = outliers_tukey(x)
                linhas.append({'tabela': 'CD', 'metrica': f'pct_{f}', 'variavel': f, 'classe': 'todas',
                               'grupo': rota, 'n_dias': int(np.isfinite(x).sum()),
                               'media': float(np.nanmean(x)) if len(x) else np.nan,
                               'mediana': float(np.nanmedian(x)) if len(x) else np.nan,
                               'desvio': float(np.nanstd(x, ddof=1)) if len(x) > 1 else np.nan,
                               'ic95_inf': lo, 'ic95_sup': hi, 'outliers_15iqr': mod, 'outliers_30iqr': ext,
                               'limite_inf_tukey': lim[0], 'limite_sup_tukey': lim[1]})
    if linhas:
        Z = pd.DataFrame(linhas)
        gravar(Z.round(6), 'K25_Z_estatistica.csv')
        log('\n' + Z.round(4).to_string(index=False))
    # Mann-Whitney, com a ressalva
    try:
        from scipy import stats
        if len(E):
            mw = []
            for (v, cl), g in E.groupby(['variavel', 'nome_classe']):
                a = g.loc[g['rota'] == 'ERA5'].groupby('data')['pct_acima_1'].mean().dropna().values
                b = g.loc[g['rota'] == 'GFS'].groupby('data')['pct_acima_1'].mean().dropna().values
                if len(a) >= 3 and len(b) >= 3:
                    u, p = stats.mannwhitneyu(a, b, alternative='two-sided')
                    dif, pp, na, nb = permutacao(a, b)
                    mw.append({'variavel': v, 'classe': cl, 'n_ERA5': len(a), 'n_GFS': len(b),
                               'U': float(u), 'gl_aprox': len(a) + len(b) - 2, 'p_mannwhitney': float(p),
                               'p_permutacao': pp, 'diferenca_medias': dif,
                               'significativo_alfa_005': bool(p < ALFA)})
            if mw:
                M = pd.DataFrame(mw)
                gravar(M.round(6), 'K25_Z_testes.csv')
                log('\nERA5 x GFS (pct acima do recorde + 1). Mann-Whitney bilateral e permutação exata:')
                log(M.round(5).to_string(index=False))
                log('   RESSALVA: dias consecutivos são autocorrelacionados, logo o n efetivo é menor que o '
                    'n de dias. O p do Mann-Whitney é otimista; o IC do bootstrap de blocos é a referência.')
    except Exception as e:
        log(f'   scipy indisponível ({e}); fica o bootstrap e a permutação.')


def fechar(T0):
    if 'Z' in PARTES:
        try:
            parte_Z()
        except Exception:
            log('   parte Z falhou:\n' + traceback.format_exc())
    log('\n' + '=' * 104)
    log('RESULTADO K25')
    log('=' * 104)
    for r in RESULTADOS:
        log(f'   {r["item"]:<4} {r["status"]:<8} {r["titulo"]}')
    if RESULTADOS:
        gravar(pd.DataFrame(RESULTADOS), 'K25_RESUMO.csv')
    falhas = [r for r in RESULTADOS if r['status'] == 'FALHA']
    atencao = [r for r in RESULTADOS if r['status'] == 'ATENCAO']
    if falhas:
        log(f'\n   ❌ {len(falhas)} falha(s) e {len(atencao)} ponto(s) de atenção. Me envie o zip.')
    elif atencao:
        log(f'\n   ⚠️ Nenhuma falha, {len(atencao)} ponto(s) de atenção. Me envie o zip.')
    else:
        log('\n   ✅ Tudo dentro dos critérios declarados nos dias varridos.')
    log(f'\nTempo: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine (trava de somente leitura).')
    if PASTA and 'SIMULACAO_' in os.path.basename(PASTA):
        log('')
        for _ in range(3):
            log('⚠️  ISTO FOI UMA SIMULAÇÃO. NENHUM NÚMERO ACIMA DESCREVE O SAB.  ⚠️')


if __name__ == '__main__':          # importar o arquivo NÃO roda nada (é assim que o teste offline o lê)
    try:
        principal()
    except Exception:
        log(traceback.format_exc())
        raise
    finally:
        # só empacota se houver CSV: um zip vazio anunciado como entrega é pior que nenhum zip
        tem_csv = os.path.isdir(PASTA) and any(f.endswith('.csv') for f in os.listdir(PASTA))
        if tem_csv:
            z = shutil.make_archive(PASTA, 'zip', PASTA)
            log(f'📦 {z}  <- me envie este zip')
            log('   Para continuar outro mês/ano: suba os CSV deste zip para /content/K25_acumulado/ '
                'antes de rodar de novo.')
            try:
                from google.colab import files
                files.download(z)
            except Exception:
                pass
        elif os.path.isdir(PASTA):
            log('Nenhum CSV foi produzido, então não há zip para enviar. Resolva o erro acima e rode '
                'de novo.')
