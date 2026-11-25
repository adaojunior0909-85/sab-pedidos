# >>> K17 v4: VALIDAÇÃO FINAL DO SAB (03/11/2026). SOMENTE LEITURA. Cole inteiro numa célula do Colab, sem editar. <<<
# v4 (03/11/2026, 12h30), depois da v3 (P1, P2, P5, P6, P8, P9 ✅; P4 ⚠️): a regra da v3 que dava P2 ✅ pela data de
#   atualização do catálogo foi RETIRADA (todas as imagens do ERA5-Land mostravam a mesma data, a da própria execução;
#   ela não prova revisão). P2 volta a ⚠️ quando há diferença, com um diagnóstico por banda e classe (assinatura_p2).
#   Resultado da v3 (zip de 03/11, 11h44): 1961 a 2013 idênticos nas 16 bandas e 4 classes; em 2020-01-15 e
#   2025-12-31 só as variáveis acumuladas do ERA5-Land diferem (|dif| média 0,01 mm de ET real nos A).
# v3 (03/11/2026, 12h), depois da v2 (P1, P5, P6 e P8 ✅; P2 ⚠️; P4 sem memória; P9 ❌):
#   - P9: a v2 comparava a contagem da máscara (pixel inteiro, B ~300) com a da K1d (só o centro no Brasil, B 241).
#     Erro da K17, não da máscara. Agora a contagem é a mesma receita do 01b e o alvo é o que o 01b gravou no
#     próprio asset (propriedades n_classe_1 a n_classe_4); a K1d fica só como informação.
#   - P4: a matriz é média de ~1.240 imagens diárias por pixel; amostrar a imagem estoura a memória até com 50
#     pixels. Agora as coleções montadas pelo código original (O2/O4, sem mudança) são lidas ponto a ponto e a
#     média e o desvio são feitos como tabela (mesmo redutor do código). 40 pixels, um mês por matriz.
#   - P2: a v2 achou diferença só em 2020-01-15 e 2025-12-31, só nas bandas que vêm direto do ERA5-Land (ET real,
#     transpiração, escoamento). A v3 lê a data de atualização de cada imagem de origem no catálogo e a de gravação
#     do dia no SAB: diferença só em banda do ERA5 com o ERA5 atualizado DEPOIS da gravação = revisão da fonte
#     (explicada), não erro de código. Sem essa prova, continua ⚠️.
#   - Amostra estratificada por classe (A 700, B até 400, C todos, borda 150): a v2 tinha só 4 B e 1 C.
#   - P3: 'o que o usuário vê' passa a ser comparado com o GRAVADO (efeito só da correção de leitura).
# v2 (03/11/2026, 11h): a v1 parou no P2 com "User memory limit exceeded" (5 versões do dia numa consulta só).
#   Agora cada versão é amostrada sozinha, em lotes de 500 pixels que caem pela metade se o servidor recusar.
#   Os cálculos e a regra de decisão não mudaram.
# =========================================================================================
# POR QUE EXISTE
#   É a auditoria mestre para a validação final dos dados, do histórico (1961–2025) até a previsão (2026 em
#   diante). As auditorias anteriores (08, 07a/07b, K8 a K16) olharam cada peça. A K17 junta a pergunta que
#   faltava: os dados gravados são EXATAMENTE o que os códigos dizem, e o que muda entre as versões do motor?
#   Para isso ela traz embutidos, sem mudança, os códigos que gravaram os dados (V1.0, V1.3, V1.5 e as duas
#   matrizes de calibração), recalcula com eles numa amostra fixa de pixels e compara com o que está gravado.
#
# O QUE FAZ (cada parte termina com ✅ OK, ⚠️ ATENÇÃO, ❌ FALHA ou ℹ️ INFO)
#   P1  Inventário do SAB_V1 inteiro: dias seguidos de 01/01/1961 até o fim da previsão, sem buraco; versão de
#       cada período (histórico = V1.0 definitiva; 2026 = V1.5 provisória; futuro = previsão GFS V1.5);
#       16 bandas na ordem certa; a previsão chega a hoje + 15 dias.
#   P2  Origem do histórico: recalcula com a V1.0 (O0) dias de 1961 a 2025 em 1.000 pixels e compara com o
#       gravado. Iguais = prova numérica de que o histórico é a V1.0 e não mudou desde a gravação.
#   P3  Diferença entre versões: nos mesmos dias e pixels, calcula a rota "definitiva" da V1.3 e da V1.5 e mede,
#       banda por banda e por classe de pixel (A, B, C, borda), onde e quanto elas diferem da V1.0. Mede também
#       "o que o usuário vê" (V1.0 + a correção de solo/escoamento que o painel e o e-mail fazem na leitura).
#   P4  Origem das calibrações: recalcula as matrizes SICSB_1986_2025 (O2) e SICSB_SOLO_2015_2025 (O4) em janeiro
#       e julho, em 500 pixels, e compara com os assets gravados.
#   P5  2026: recalcula com a V1.5 os últimos dias provisórios (ERA5) e compara com o gravado; confere as
#       propriedades dos dias de previsão (rodada, versão, Confianca_Prazo).
#   P6  Coerência física do acervo inteiro (um dia por ano de 1961 a 2025, o dia 15 de cada mês de 2026 e todos os
#       dias de previsão), no Brasil todo: ET real <= ETo, transpiração <= ET real, Tmax >= Tmin, UR de 0 a 100%,
#       chuva >= 0, Tmax <= 45 °C, Tmin >= -10 °C, umidade do solo <= 0,9 (bruta e depois da correção de leitura).
#   P7  Validação independente da chuva: totais mensais do SAB x CHIRPS (satélite + estações, UCSB), no histórico e
#       nos meses provisórios de 2026: correlação e viés. Só informação (o CHIRPS também tem erro).
#   P8  RONI_CPC_v6 x arquivo oficial do CPC/NOAA (RONI.ascii.txt), estação por estação.
#   P9  Máscara de qualidade: contagem de pixels por classe (receita do 01b) x a contagem que o 01b gravou no asset.
#
# REGRA DE DECISÃO (fixada antes de rodar)
#   VALIDAÇÃO FINAL APROVADA quando P1, P2, P4, P5, P8 e P9 saem ✅ e P6 não tem ❌. P3 e P7 são medidas (ℹ️/⚠️)
#   para a tese: dizem onde as versões diferem e quão perto o SAB está de uma fonte independente.
#   Diferença em P2/P4/P5 vira ⚠️ (não ❌) porque pode vir de revisão dos dados de origem (BR-DWGD, ERA5-Land,
#   SMAP) depois da gravação; o detalhe por banda diz qual. Me envie o zip em qualquer caso.
#
# O QUE GRAVA: NADA no Earth Engine (trava de somente leitura: criar, apagar, renomear e exportar bloqueados).
#   Só os arquivos de resultado no Colab, que no fim viram validacao_K17_<data>.zip (baixado sozinho).
# ANTES DE RODAR: Ambiente de execução -> Reiniciar sessão. Fora das 15h07 e 23h07 (motor). Sem K16 rodando.
# TEMPO: de 40 a 80 minutos. Cada parte é independente: se uma falhar, as outras continuam.
# =========================================================================================
import ast
import hashlib
import io
import math
import os
import re
import shutil
import time
import traceback
from datetime import date, datetime, timedelta, timezone

import pandas as pd

PROJETO = 'clima-492922'
ASSET_SAB = f'projects/{PROJETO}/assets/SAB_V1'
ASSET_MASCARA = f'projects/{PROJETO}/assets/SAB_MASCARA_QUALIDADE'
ASSET_RONI = f'projects/{PROJETO}/assets/RONI_CPC_v6'
ASSET_CLIMA = f'projects/{PROJETO}/assets/SICSB_1986_2025'
ASSET_SOLO = f'projects/{PROJETO}/assets/SICSB_SOLO_2015_2025'
URL_RONI_CPC = 'https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt'
CHIRPS = 'UCSB-CHG/CHIRPS/DAILY'
CRS = 'EPSG:4326'
TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
ORDEM = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 'rs', 'u2', 'tsolo_C', 'tfolha_C',
         'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm', 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
NUCLEO = ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'vpd', 'et_potencial', 'rs', 'u2']        # vêm do BR-DWGD no histórico
SOLO = ['runoff_sup_mm', 'runoff_sub_mm', 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
CLASSES = {0: 'sem classe', 1: 'A', 2: 'B', 3: 'C', 4: 'borda'}
REF_MASCARA = {1: 70524, 2: 241, 3: 48}       # K1d corrigida (pixels com o centro no Brasil)
REF_BORDA = 1060
FIM_HISTORICO = '2025-12-31'
N_PONTOS = 1000                     # (v2) pixels da amostra; na v3 a amostra é estratificada (abaixo)
PONTOS_POR_CLASSE = {1: 700, 2: 400, 3: 100, 4: 150}   # v3: classe com menos pixels entra inteira (B ~300, C ~48)
REGIAO_AMPLA = [-75.0, -35.0, -28.0, 6.5]                # a mesma do 01b (inclui a borda)
N_PONTOS_P4 = 40                    # v3: pixels A por matriz no P4
MATRIZES_P4 = (('clima', 'gerar_matriz_do_mes', 'SICSB_1986_2025', 'Matriz_Clima', 1),
               ('solo', 'gerar_matriz_solo_mes', 'SICSB_SOLO_2015_2025', 'Matriz_Solo', 7))
# bandas que a V1.0 tira direto do ERA5-Land (sem BR-DWGD): diferença nelas é explicada por revisão do ERA5
BANDAS_ERA5_V10 = ['et_real',  # (v3; mantida só como registro)
                   'transpiracao_mm', 'tsolo_C', 'tfolha_C', 'runoff_sup_mm', 'runoff_sub_mm',
                   'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3']
N_PONTOS_MATRIZ = 500               # pixels da amostra das matrizes e do CHIRPS (P4, P7)
SEMENTE = 17                        # a mesma amostra a cada execução
DIAS_P2 = ['1961-01-15', '1972-07-15', '1983-01-15', '1994-07-15', '2004-01-15', '2013-07-15', '2020-01-15',
           '2025-12-31']
MESES_P4 = (1, 7)
TOL_ABS = 1e-3                      # diferença tolerada (float32 + arredondamento do Earth Engine)
TOL_REL = 1e-4
MIN_IGUAIS = 0.99                   # fração mínima de pixels iguais por banda para P2/P4/P5 saírem ✅
TMAX_LIMITE, TMIN_LIMITE, UMIDADE_LIMITE = 45.0, -10.0, 0.9
MESES_CHIRPS_HIST = ['1985-01', '1985-07', '1995-01', '1995-07', '2005-01', '2005-07', '2015-01', '2015-07',
                     '2020-01', '2020-07', '2024-01', '2024-07']
LOTE_P6 = 8                         # dias por pedido no P6 (para não passar do tempo do Earth Engine)
LOTE_AMOSTRA = 500                  # pixels por consulta de amostra (v2); cai pela metade se o servidor recusar
LOTE_MINIMO = 50

AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'validacao_K17_{AGORA:%Y%m%d_%H%M%S}')
LOG = os.path.join(PASTA, 'LOG_K17.txt')
ACHADOS = []

# ------------------------------------------------------------------ códigos embutidos, sem mudança
FONTE_V10 = r'''<<V10>>'''
FONTE_V13 = r'''<<V13>>'''
FONTE_V15 = r'''<<V15>>'''
FONTE_CLIMA = r'''<<CLIMA>>'''
FONTE_SOLO = r'''<<SOLO>>'''
SHAS = {n: hashlib.sha256(s.encode('utf-8')).hexdigest() for n, s in
        (('V1.0 (O0)', FONTE_V10), ('V1.3 (O1)', FONTE_V13), ('V1.5 (05b)', FONTE_V15),
         ('SICSB_1986_2025 (O2)', FONTE_CLIMA), ('SICSB_SOLO_2015_2025 (O4)', FONTE_SOLO))}


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


def salvar_csv(df, nome):
    os.makedirs(PASTA, exist_ok=True)
    df.to_csv(os.path.join(PASTA, nome), sep=';', decimal=',', index=False, encoding='utf-8-sig')


# =========================================================================================
# FUNÇÕES PURAS (testadas offline em testes/teste_k17.py)
# =========================================================================================
PROIBIDO_NA_CARGA = ('getInfo', 'getTaskList', 'Initialize', 'Authenticate', 'Export', '.start(', 'deleteAsset',
                     'renameAsset', 'createAsset', 'copyAsset', 'listAssets', 'getAsset(', 'setAssetAcl')
GLOBAIS_PERMITIDOS = {'limitesRegiao', 'poligonoBrasil', 'crsNativo', 'transformNativo', 'elevacao_br', 'colChuvaGeral',
                      'colecao_era5', '_gaul_br', 'fcBrasil', 'fuso_br', 'data_extracao_local', 'data_hoje_dt',
                      'data_hoje_str', 'data_fim_processo'}


def trechos_carregaveis(fonte):
    """Divide o código de um motor em instruções do nível de cima e devolve só as seguras para carregar: imports,
    definições de função e atribuições de constantes (NOMES_EM_MAIÚSCULAS) ou de objetos permitidos, sem nenhuma
    chamada ao servidor nem escrita. Nada do fluxo principal do motor (que exporta) é executado."""
    fonte = fonte.lstrip('﻿')
    arvore = ast.parse(fonte)
    saida = []
    for no in arvore.body:
        seg = ast.get_source_segment(fonte, no) or ''
        if isinstance(no, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            if isinstance(no, ast.FunctionDef) or not any(p in seg for p in PROIBIDO_NA_CARGA):
                saida.append((type(no).__name__, seg))
        elif isinstance(no, ast.Assign) and all(isinstance(t, ast.Name) and (t.id.isupper() or t.id in GLOBAIS_PERMITIDOS)
                                                for t in no.targets):
            if not any(p in seg for p in PROIBIDO_NA_CARGA):
                saida.append(('Assign', seg))
    return saida


def carregar_codigo(nome, fonte, precisa, ee_mod):
    """Carrega o motor num espaço próprio e confere que as funções pedidas existem."""
    ns = {'__name__': f'k17_{nome}', '__builtins__': __builtins__, 'ee': ee_mod}
    pulados = []
    for tipo, seg in trechos_carregaveis(fonte):
        try:
            exec(compile(seg, f'<{nome}>', 'exec'), ns)
        except Exception as e:          # ex.: constante que depende de algo do fluxo principal
            pulados.append(f'{tipo}: {seg.splitlines()[0][:60]} ({type(e).__name__})')
    faltam = [f for f in precisa if not callable(ns.get(f))]
    if faltam:
        raise RuntimeError(f'{nome}: funções não encontradas: {faltam}')
    return ns, pulados


def iguais(a, b, tol_abs=TOL_ABS, tol_rel=TOL_REL):
    """Série booleana: os dois valores são iguais (os dois ausentes também contam como iguais)."""
    a = pd.to_numeric(a, errors='coerce')
    b = pd.to_numeric(b, errors='coerce')
    ambos_nan = a.isna() & b.isna()
    dif = (a - b).abs()
    return ambos_nan | (dif <= tol_abs) | (dif <= tol_rel * b.abs())


def comparar_bandas(df, pa, pb, bandas, grupo=None):
    """Tabela por banda (e por grupo, se pedido): pixels comparados, fração igual, diferença média e máxima."""
    linhas = []
    grupos = [(None, df)] if grupo is None else list(df.groupby(grupo))
    for g, sub in grupos:
        for b in bandas:
            ca, cb = f'{pa}{b}', f'{pb}{b}'
            if ca not in sub.columns or cb not in sub.columns:
                continue
            a = pd.to_numeric(sub[ca], errors='coerce')
            bb = pd.to_numeric(sub[cb], errors='coerce')
            ok = iguais(a, bb)
            dif = (a - bb).abs()
            linhas.append({'grupo': g, 'banda': b, 'n': int(len(sub)), 'frac_iguais': float(ok.mean()) if len(sub) else 1.0,
                           'n_diferentes': int((~ok).sum()), 'dif_media': float(dif[~ok].mean()) if (~ok).any() else 0.0,
                           'dif_max': float(dif.max()) if dif.notna().any() else 0.0,
                           'so_um_ausente': int((a.isna() ^ bb.isna()).sum())})
    return pd.DataFrame(linhas)


def status_reproducao(tab, min_iguais=MIN_IGUAIS):
    """OK se todas as bandas tiverem pelo menos min_iguais dos pixels iguais; senão ATENÇÃO, com as bandas."""
    if tab.empty:
        return 'FALHA', 'nenhum pixel comparado'
    ruins = tab[tab['frac_iguais'] < min_iguais]
    if ruins.empty:
        return 'OK', f'{len(tab)} comparações banda×dia, todas com ≥ {100 * min_iguais:.0f}% dos pixels iguais'
    lista = ', '.join(f"{r.banda}{'' if r.grupo is None else ' ' + str(r.grupo)} ({100 * r.frac_iguais:.1f}%)"
                      for r in ruins.head(8).itertuples())
    return 'ATENÇÃO', f'{len(ruins)} de {len(tab)} comparações abaixo de {100 * min_iguais:.0f}%: {lista}'


def analisar_inventario(df, hoje, ultima_era5, horizonte=15):
    """df: id, versao, alg, t_ms. Devolve (problemas, resumo, tabela por período)."""
    problemas = []
    d = df.copy()
    d['data'] = pd.to_datetime(d['id'].str.replace('SAB_', '', regex=False), format='%Y_%m_%d', errors='coerce')
    ruins = d[d['data'].isna()]
    if len(ruins):
        problemas.append(f'{len(ruins)} imagem(ns) com nome fora do padrão SAB_AAAA_MM_DD: {list(ruins["id"][:5])}')
    d = d.dropna(subset=['data']).sort_values('data')
    if d['data'].duplicated().any():
        problemas.append(f'datas repetidas: {list(d.loc[d["data"].duplicated(), "id"][:5])}')
    inicio, fim = d['data'].min(), d['data'].max()
    esperado = pd.date_range('1961-01-01', fim, freq='D')
    faltam = esperado.difference(pd.DatetimeIndex(d['data']))
    if len(faltam):
        problemas.append(f'{len(faltam)} dia(s) faltando entre 1961-01-01 e {fim:%Y-%m-%d}: '
                         f'{[x.strftime("%Y-%m-%d") for x in faltam[:8]]}')
    if inicio != pd.Timestamp('1961-01-01'):
        problemas.append(f'o acervo começa em {inicio:%Y-%m-%d}, não em 1961-01-01')
    lim_hist = pd.Timestamp(FIM_HISTORICO)
    lim_era5 = pd.Timestamp(ultima_era5)
    d['periodo'] = 'previsão'
    d.loc[d['data'] <= lim_era5, 'periodo'] = '2026 provisório'
    d.loc[d['data'] <= lim_hist, 'periodo'] = 'histórico'
    hist = d[d['periodo'] == 'histórico']
    fora = hist[(hist['versao'] != 'definitiva') | (hist['alg'] != 'V1.0')]
    if len(fora):
        problemas.append(f'histórico com versão diferente de definitiva/V1.0 em {len(fora)} dia(s): '
                         f'{fora.groupby(["versao", "alg"]).size().to_dict()}')
    prov = d[d['periodo'] == '2026 provisório']
    fora = prov[(prov['versao'] != 'provisoria_era5') | (prov['alg'] != 'V1.5')]
    if len(fora):
        problemas.append(f'{len(fora)} dia(s) de 2026 até o último ERA5 ({ultima_era5}) que não são provisoria_era5 V1.5: '
                         f'{fora.groupby(["versao", "alg"]).size().to_dict()}')
    prev = d[d['periodo'] == 'previsão']
    fora = prev[~prev['versao'].isin(['provisoria_gfs', 'provisoria_gfs_incompleta', 'falha_latencia_gfs'])
                | (prev['alg'] != 'V1.5')]
    if len(fora):
        problemas.append(f'{len(fora)} dia(s) depois do último ERA5 que não são previsão GFS V1.5: '
                         f'{fora.groupby(["versao", "alg"]).size().to_dict()}')
    alvo = pd.Timestamp(hoje) + pd.Timedelta(days=horizonte)
    if abs((fim - alvo).days) > 2:
        problemas.append(f'a previsão termina em {fim:%Y-%m-%d}; o esperado é perto de {alvo:%Y-%m-%d} (hoje + {horizonte})')
    falhas_lat = prev[prev['versao'] == 'falha_latencia_gfs']
    if len(falhas_lat):
        problemas.append(f'{len(falhas_lat)} dia(s) de previsão com falha_latencia_gfs (sem dado GFS)')
    tab = d.groupby(['periodo', 'versao', 'alg']).agg(dias=('id', 'size'), de=('data', 'min'), ate=('data', 'max')) \
        .reset_index()
    tab['de'] = tab['de'].dt.strftime('%Y-%m-%d')
    tab['ate'] = tab['ate'].dt.strftime('%Y-%m-%d')
    resumo = (f'{len(d)} dias de {inicio:%Y-%m-%d} a {fim:%Y-%m-%d}; histórico {len(hist)}, 2026 provisório {len(prov)}, '
              f'previsão {len(prev)}')
    return problemas, resumo, tab


def estatisticas_chirps(df):
    """df: periodo, sab, chirps (totais mensais por pixel). Correlação, viés relativo e erro médio por período."""
    linhas = []
    for per, sub in df.groupby('periodo'):
        s = pd.to_numeric(sub['sab'], errors='coerce')
        c = pd.to_numeric(sub['chirps'], errors='coerce')
        ok = s.notna() & c.notna()
        s, c = s[ok], c[ok]
        if len(s) < 30:
            continue
        linhas.append({'periodo': per, 'n': int(len(s)), 'r': float(s.corr(c)),
                       'vies_pct': float(100 * (s.sum() / c.sum() - 1)) if c.sum() > 0 else float('nan'),
                       'erro_medio_mm': float((s - c).abs().mean()), 'media_sab_mm': float(s.mean()),
                       'media_chirps_mm': float(c.mean())})
    return pd.DataFrame(linhas)


def status_chirps(tab):
    if tab.empty:
        return 'NÃO EXECUTADO', 'sem meses comparáveis'
    falhas = []
    for r in tab.itertuples():
        r_min, vies_max = (0.75, 20.0) if r.periodo == 'histórico' else (0.6, 30.0)
        if r.r < r_min or abs(r.vies_pct) > vies_max:
            falhas.append(f'{r.periodo}: r = {r.r:.2f} (mín. {r_min}), viés {r.vies_pct:+.1f}% (máx. ±{vies_max:.0f}%)')
    texto = '; '.join(f'{r.periodo}: r = {r.r:.2f}, viés {r.vies_pct:+.1f}%, erro médio {r.erro_medio_mm:.1f} mm/mês '
                      f'({r.n} pixel-meses)' for r in tab.itertuples())
    return ('ATENÇÃO', texto + ' | fora do esperado: ' + '; '.join(falhas)) if falhas else ('OK', texto)


def arredondar_cpc(x):
    """Arredondamento do RONI do CPC para 1 casa: metade para longe do zero (como a tabela oficial)."""
    return math.copysign(math.floor(abs(x) * 10 + 0.5 + 1e-9) / 10, x)


def avaliar_roni(asset, cpc):
    """asset: ano, Trimestre, RONI; cpc: SEAS, YR, ANOM (2 casas). Devolve (status, detalhe, tabela)."""
    c = cpc.rename(columns={'SEAS': 'Trimestre', 'YR': 'ano', 'ANOM': 'cpc_2c'}).copy()
    c['cpc'] = c['cpc_2c'].astype(float).map(arredondar_cpc)
    a = asset[['ano', 'Trimestre', 'RONI']].copy()
    a['ano'] = a['ano'].astype(int)
    c['ano'] = c['ano'].astype(int)
    c['_ordem'] = range(len(c))                      # o arquivo do CPC vem em ordem cronológica
    m = c.merge(a, on=['ano', 'Trimestre'], how='left')
    m['igual'] = (m['RONI'].astype(float) - m['cpc']).abs() <= 0.051
    falta = m[m['RONI'].isna()]
    dif = m[m['RONI'].notna() & ~m['igual']]
    # empate na 2ª casa (ex.: 0,45): o 02 pede a decisão à mão; diferença de 0,1 aí não é erro
    empate = dif[(dif['cpc_2c'].astype(float).abs() * 100).round().astype(int) % 10 == 5]
    dif_real = dif.drop(empate.index)
    # o CPC revisa as estações mais novas no mês seguinte: diferença nas 3 últimas pede só rodar o 02
    recentes = dif_real[dif_real['_ordem'] >= len(c) - 3]
    dif_real = dif_real.drop(recentes.index)
    det = f'{len(c)} estações no CPC; {int(m["igual"].sum())} iguais no asset'
    if len(recentes) and not len(dif_real):
        return 'ATENÇÃO', det + f'; o CPC revisou {len(recentes)} estação(ões) recente(s): rode o 02', m
    if len(dif_real):
        return 'FALHA', det + f'; {len(dif_real)} diferentes: ' + str(dif_real[['ano', 'Trimestre', 'RONI', 'cpc']].head(5)
                                                                     .to_dict('records')), m
    if len(falta):
        ult = falta.iloc[-1]
        return 'ATENÇÃO', det + f'; {len(falta)} estação(ões) do CPC ainda fora do asset (até {ult.Trimestre} {ult.ano}): rode o 02', m
    return 'OK', det + (f'; {len(empate)} em empate de arredondamento (valor escolhido no 02)' if len(empate) else ''), m


def avaliar_mascara(hist, gravado=None):
    """hist: {classe: pixels} contados agora com a receita do 01b (pixel inteiro, região ampla, sem ponderar).
    gravado: {classe: pixels} que o 01b gravou no asset (n_classe_1 a 4). Igual = OK; diferente = FALHA.
    Sem as propriedades: confere as faixas esperadas pelo roteiro (B ~300, C dentro ~48, borda ~1.060): ATENÇÃO.
    [v3] A K1d (A 70.524, B 241, C 48) conta só os pixels com o CENTRO no Brasil: é outra conta, só informação."""
    fmt = lambda h: f'A {h.get(1, 0):,}, B {h.get(2, 0):,}, C {h.get(3, 0):,}, borda {h.get(4, 0):,}'.replace(',', '.')
    det = f'agora: {fmt(hist)}'
    if gravado:
        det += f' | gravado pelo 01b: {fmt(gravado)}'
        dif = {k: (hist.get(k, 0), gravado.get(k, 0)) for k in (1, 2, 3, 4) if hist.get(k, 0) != gravado.get(k, 0)}
        det += ' | K1d (centro no Brasil, outra conta): A 70.524, B 241, C 48'
        return ('FALHA', det + f' | diferentes: {dif}') if dif else ('OK', det)
    faixas = {2: (270, 330), 3: (40, 56), 4: (1000, 1120)}
    fora = {k: hist.get(k, 0) for k, (a, b) in faixas.items() if not a <= hist.get(k, 0) <= b}
    if fora:
        return 'ATENÇÃO', det + f' | asset sem n_classe_*; fora da faixa do roteiro: {fora}'
    return 'OK', det + ' | asset sem n_classe_*; dentro das faixas do roteiro (B ~300, C ~48, borda ~1.060)'


# [v4] Bandas que, em cada classe, a V1.0 tira de uma variável ACUMULADA do dia no ERA5-Land (sufixo _sum no
# DAILY_AGGR). No pixel A o núcleo vem do BR-DWGD; nos B, C e borda, chuva, ETo e radiação também vêm do ERA5.
SOMA_ERA5_A = {'et_real', 'transpiracao_mm', 'runoff_sup_mm', 'runoff_sub_mm'}
SOMA_ERA5_OUTRAS = SOMA_ERA5_A | {'pr_mm', 'et_potencial', 'rs'}


def assinatura_p2(df, min_iguais=MIN_IGUAIS):
    """[v4] df: amostra bruta do P2 (colunas data, classe, s_<banda>, a_<banda>). Para cada dia com diferença, diz
    quais bandas diferem nos pixels A e nos demais, e se TODAS são de variáveis acumuladas do ERA5-Land (assinatura
    de revisão dessa fonte; o BR-DWGD e as variáveis instantâneas do ERA5 iguais). Só DIAGNÓSTICO: não muda o status.
    [v3 retirada] A v3 usava a data 'updateTime' do catálogo como prova de revisão; na execução de 03/11/2026 todas
    as imagens do ERA5-Land tinham a mesma data (o próprio dia da execução): essa data não diz quando o dado mudou.
    Devolve (só_soma_era5: bool, textos)."""
    textos, todas = [], True
    for d, sub in df.groupby('data'):
        dif = {}
        for grupo, cond in (('A', sub['classe'] == 1), ('outras', sub['classe'] != 1)):
            s2 = sub[cond]
            ruins = [b for b in ORDEM if f's_{b}' in s2 and len(s2) and iguais(s2[f's_{b}'], s2[f'a_{b}']).mean() < min_iguais]
            dif[grupo] = ruins
        if not dif['A'] and not dif['outras']:
            continue
        ok = set(dif['A']) <= SOMA_ERA5_A and set(dif['outras']) <= SOMA_ERA5_OUTRAS
        todas &= ok
        textos.append(f'{d}: diferem nos pixels A {dif["A"] or "-"}; nos B/C/borda {dif["outras"] or "-"} -> ' +
                      ('só variáveis acumuladas do ERA5-Land (BR-DWGD e variáveis instantâneas iguais)' if ok else
                       'ATENÇÃO: há banda fora das acumuladas do ERA5-Land'))
    return todas, textos


def tabela_agrupada(grupos, nomes, pref):
    """grupos: saída de reduceColumns(...group(groupName='pid')) {'groups': [{'pid': .., '<saida>': [..]}]}.
    Devolve DataFrame pid + pref+nome (uma coluna por banda, na ordem de nomes)."""
    linhas = []
    for g in grupos.get('groups', []):
        chave = [k for k in g if k != 'pid'][0]
        val = g[chave] if isinstance(g[chave], list) else [g[chave]]
        linhas.append({'pid': int(g['pid']), **{f'{pref}{n}': v for n, v in zip(nomes, val)}})
    return pd.DataFrame(linhas, columns=['pid'] + [f'{pref}{n}' for n in nomes])


def status_coerencia(tab):
    """tab: uma linha por dia com as frações de pixels com cada problema. FALHA só em problema que não pode existir."""
    duros = ['etr_acima_eto', 'transp_acima_etr', 'ur_fora', 'chuva_negativa']
    falhas = {c: float(tab[c].max()) for c in duros if c in tab and tab[c].max() > 1e-4}
    avisos = {c: float(tab[c].max()) for c in ['tmax_abaixo_tmin', 'tmax_acima_45', 'tmin_abaixo_m10', 'solo_acima_09_lido']
              if c in tab and tab[c].max() > 1e-3}
    info = {c: float(tab[c].max()) for c in ['solo_acima_09_bruto'] if c in tab and tab[c].max() > 0}
    fmt = lambda dic: ', '.join(f'{k} até {100 * v:.3f}% dos pixels' for k, v in dic.items())
    det = f'{len(tab)} dias conferidos'
    if info:
        det += f' | bruto do acervo (corrigido na leitura): {fmt(info)}'
    if falhas:
        return 'FALHA', det + f' | impossível fisicamente: {fmt(falhas)}'
    if avisos:
        return 'ATENÇÃO', det + f' | a olhar: {fmt(avisos)}'
    return 'OK', det + ' | nenhuma incoerência'


def veredito(achados):
    criticas = ['P1', 'P2', 'P4', 'P5', 'P8', 'P9']
    st = {a['parte']: a['status'] for a in achados}
    falta = [p for p in criticas if st.get(p) != 'OK']
    p6 = st.get('P6')
    aprovado = not falta and p6 in ('OK', 'ATENÇÃO')
    return aprovado, falta, p6


# =========================================================================================
# EXECUÇÃO NO EARTH ENGINE
# =========================================================================================
def principal():
    import ee
    import requests

    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log('=' * 100)
    log(f'K17 v4: VALIDAÇÃO FINAL DO SAB (somente leitura) | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    for n, s in SHAS.items():
        log(f'   código embutido {n}: SHA-256 {s}')
    log('=' * 100)
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)

    def _bloqueado(*a, **k):
        raise RuntimeError('K17 SOMENTE LEITURA: tentativa de escrita bloqueada')

    for _n in ('createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'updateAsset', 'setAssetAcl',
               'setAssetProperties', 'createFolder', 'startProcessing', 'exportImage', 'exportTable', 'exportVideo',
               'exportMap', 'startIngestion', 'startTableIngestion', 'cancelTask', 'cancelOperation'):
        if hasattr(ee.data, _n):
            setattr(ee.data, _n, _bloqueado)
    ee.batch.Task.start = _bloqueado
    log('🔒 Trava de somente leitura ativa (criar, apagar, renomear, exportar e cancelar bloqueados).\n')

    PROJ = ee.Projection(CRS, TRANSFORM)
    BR = ee.FeatureCollection('FAO/GAUL/2015/level0').filter(ee.Filter.eq('ADM0_NAME', 'Brazil')).geometry()
    COL = ee.ImageCollection(ASSET_SAB)
    CLASSE = ee.Image(ASSET_MASCARA).select('classe').unmask(0).rename('classe')
    hoje = AGORA.date()

    class Pesado(RuntimeError):
        """O Earth Engine recusou por memória ou tempo: repetir igual não adianta, é preciso dividir o pedido."""

    def gi(obj, rotulo, tentativas=3):
        for k in range(tentativas):
            try:
                return obj.getInfo()
            except Exception as e:
                msg = str(e)
                if any(x in msg.lower() for x in ('memory limit', 'timed out', 'computation timed', 'too large')):
                    raise Pesado(f'{rotulo}: {msg[:300]}')
                if k == tentativas - 1:
                    raise RuntimeError(f'{rotulo}: {msg[:300]}')
                time.sleep(20)

    # [K17 v2, 03/11/2026] A v1 pedia numa consulta só as 5 versões do dia (gravado, V1.0, V1.3, V1.5 e a
    # leitura do painel) nos 1.000 pixels e o Earth Engine respondeu "User memory limit exceeded" no P2. Agora:
    # os pontos ficam fixos do lado do Colab (lista), cada imagem é amostrada sozinha, em lotes de LOTE_AMOSTRA
    # pixels; se o servidor recusar por memória ou tempo, o lote cai pela metade (até LOTE_MINIMO). O resultado
    # é o mesmo: as tabelas são juntadas pelo número do pixel (pid).
    def fc_de(lista):
        return ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p['lon'], p['lat']]),
                                                {'pid': p['pid'], 'classe': p['classe']}) for p in lista])

    lote_atual = {}                       # tamanho de lote que funcionou, por tipo de imagem (lembrado entre dias)

    def amostra(img, lista, rotulo='amostra', chave=None):
        linhas, i, n = [], 0, lote_atual.get(chave, LOTE_AMOSTRA)
        while i < len(lista):
            sub = lista[i:i + n]
            fc = img.sampleRegions(collection=fc_de(sub), properties=['pid', 'classe'], projection=PROJ,
                                   tileScale=16, geometries=False)
            try:
                linhas += [f['properties'] for f in gi(fc, rotulo)['features']]
                i += len(sub)
            except Pesado:
                if n <= LOTE_MINIMO:
                    raise
                n = max(LOTE_MINIMO, n // 2)
                lote_atual[chave] = n
                log(f'   {rotulo}: pedido pesado, lote reduzido para {n} pixels')
        return pd.DataFrame(linhas)

    def amostra_varias(imagens, bandas, lista, rotulo):
        """imagens: [(prefixo, ee.Image com as bandas)]. Renomeia para prefixo+banda, faz uma consulta por imagem e
        por lote e junta tudo pelo pid. Pixel sem valor numa versão fica vazio nela (aparece na comparação)."""
        df = pd.DataFrame([{'pid': p['pid'], 'classe': p['classe']} for p in lista])
        for pref, img in imagens:
            img = ee.Image(img).select(bandas).rename([f'{pref}{b}' for b in bandas])
            parte_df = amostra(img, lista, f'{rotulo} {pref}', chave=pref)
            parte_df = parte_df.drop(columns=['classe'], errors='ignore')
            if 'pid' not in parte_df.columns:
                parte_df = pd.DataFrame({'pid': []})
            df = df.merge(parte_df, on='pid', how='left')
            for b in bandas:
                if f'{pref}{b}' not in df.columns:
                    df[f'{pref}{b}'] = float('nan')
        return df

    def parte(nome):
        def deco(fn):
            def rodar():
                log(f'\n{"-" * 100}\n{nome}\n{"-" * 100}')
                t = time.time()
                try:
                    fn()
                except Exception as e:
                    achado(nome.split()[0], 'NÃO EXECUTADO', nome, f'{type(e).__name__}: {str(e)[:400]}')
                    log(traceback.format_exc()[-1500:])
                log(f'   ({(time.time() - t) / 60:.1f} min)')
            return rodar
        return deco

    # pontos fixos na grade nativa (centro dos pixels), com a classe da máscara
    # [v3] estratificada: cada classe com a sua cota (B e C quase inteiras), na região ampla do 01b (inclui a borda)
    classes_s = sorted(PONTOS_POR_CLASSE)
    sorteio = (ee.Image.pixelLonLat().addBands(CLASSE.toInt())
               .stratifiedSample(numPoints=0, classBand='classe', region=ee.Geometry.Rectangle(REGIAO_AMPLA, None, False),
                                 projection=PROJ, seed=SEMENTE, classValues=classes_s,
                                 classPoints=[PONTOS_POR_CLASSE[c] for c in classes_s], geometries=True, tileScale=4))
    try:
        pontos = [{'pid': k, 'classe': int(f['properties']['classe']), 'lon': f['geometry']['coordinates'][0],
                   'lat': f['geometry']['coordinates'][1]} for k, f in enumerate(gi(sorteio, 'pontos')['features'])]
    except Exception as e:                # sem amostra, P2 a P7 saem sem pixels; P1, P8 e P9 rodam igual
        pontos = []
        log(f'   ⚠️ amostra fixa de pixels não sorteada: {str(e)[:300]}')
    pontos_m = [p for p in pontos if p['classe'] == 1][:400] + [p for p in pontos if p['classe'] in (2, 3)]   # P7
    pontos_p4 = [p for p in pontos if p['classe'] == 1][:N_PONTOS_P4]
    log(f'   amostra fixa: {len(pontos)} pixels (' +
        ', '.join(f'{CLASSES[c]} {sum(p["classe"] == c for p in pontos)}' for c in sorted(CLASSES)) + ')')
    salvar_csv(pd.DataFrame(pontos), 'pontos_amostra.csv')

    # códigos dos motores e das matrizes
    carga = {}
    for nome, fonte, precisa in (('v10', FONTE_V10, ['processarDia_Definitivo']),
                                 ('v13', FONTE_V13, ['processarDia_Definitivo', 'aplicarPatch_Solo']),
                                 ('v15', FONTE_V15, ['processarDia_Definitivo', 'processarDia_Rota1', 'aplicarPatch_Solo']),
                                 ('clima', FONTE_CLIMA, ['gerar_matriz_do_mes']),
                                 ('solo', FONTE_SOLO, ['gerar_matriz_solo_mes'])):
        carga[nome], pulados = carregar_codigo(nome, fonte, precisa, ee)
        log(f'   código {nome}: carregado ({len(pulados)} trecho(s) do fluxo principal ignorados)')

    def lido_pelo_painel(d, img_gravado):
        """O que o painel e o e-mail entregam: dias V1.0 com a correção de solo e escoamento feita na leitura."""
        return ee.Image(carga['v15']['aplicarPatch_Solo'](d)).select(ORDEM)

    estado = {}

    # ---------------------------------------------------------------------------------- P1
    @parte('P1 Inventário do SAB_V1 (todos os dias)')
    def p1():
        def props(img):
            dic = img.toDictionary()
            return ee.Feature(None, {'id': img.get('system:index'), 'versao': dic.get('versao', 'definitiva'),
                                     'alg': dic.get('versao_algoritmo', 'V1.0'), 't': img.get('system:time_start')})
        lista = gi(COL.map(props).reduceColumns(ee.Reducer.toList().repeat(4), ['id', 'versao', 'alg', 't']).get('list'),
                   'inventário')
        df = pd.DataFrame({'id': lista[0], 'versao': lista[1], 'alg': lista[2], 't_ms': lista[3]})
        df['id'] = df['id'].astype(str).str.split('/').str[-1]
        ms = gi(ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').filterDate(str(hoje - timedelta(days=150)),
                                                                             str(hoje + timedelta(days=1)))
                .aggregate_max('system:time_start'), 'último ERA5')
        ult_era5 = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
        ult_gravado_era5 = df[df['versao'] == 'provisoria_era5']['id'].max()
        estado['ult_era5'] = ult_gravado_era5.replace('SAB_', '').replace('_', '-') if isinstance(ult_gravado_era5, str) else ult_era5
        problemas, resumo, tab = analisar_inventario(df, hoje, estado['ult_era5'])
        salvar_csv(tab, 'P1_inventario_por_periodo.csv')
        log(tab.to_string(index=False))
        log(f'   último ERA5-Land disponível: {ult_era5} | último dia provisório gravado: {estado["ult_era5"]}')
        # bandas: 1º dia de cada ano e os 20 últimos dias
        ids = sorted({f'SAB_{a}_01_01' for a in range(1961, hoje.year + 1)} | set(df.sort_values('id')['id'].tail(20)))
        bandas = gi(COL.filter(ee.Filter.inList('system:index', ids))
                    .map(lambda i: ee.Feature(None, {'id': i.get('system:index'), 'b': i.bandNames()})), 'bandas')
        ruins = [f['properties']['id'] for f in bandas['features'] if f['properties']['b'] != ORDEM]
        if ruins:
            problemas.append(f'{len(ruins)} dia(s) sem as 16 bandas na ordem canônica: {ruins[:5]}')
        estado['df'] = df
        achado('P1', 'FALHA' if problemas else 'OK', 'Inventário do SAB_V1',
               resumo + ('' if not problemas else ' | ' + ' | '.join(problemas)) +
               f' | bandas conferidas em {len(bandas["features"])} dias')

    # ---------------------------------------------------------------------------------- P2 e P3
    @parte('P2 Origem do histórico (V1.0 recalculada x gravado) e P3 diferença entre versões')
    def p2_p3():
        quadros, sem = [], []
        for d in DIAS_P2:
            gravado = ee.Image(f'{ASSET_SAB}/SAB_{d.replace("-", "_")}')
            try:
                df = amostra_varias([('s_', gravado),
                                     ('a_', carga['v10']['processarDia_Definitivo'](d)),
                                     ('b_', carga['v13']['processarDia_Definitivo'](d)),
                                     ('c_', carga['v15']['processarDia_Definitivo'](d)),
                                     ('l_', lido_pelo_painel(d, gravado))], ORDEM, pontos, d)
            except Exception as e:
                sem.append(d)
                log(f'   {d}: não calculado ({str(e)[:200]})')
                continue
            df['data'] = d
            quadros.append(df)
            salvar_csv(df, f'P2_P3_amostra_{d}.csv')
            log(f'   {d}: {int(df["s_pr_mm"].notna().sum())} pixels com valor gravado, '
                f'{int(df["a_pr_mm"].notna().sum())} com a V1.0 recalculada')
        if not quadros:
            raise RuntimeError(f'nenhum dia calculado: {sem}')
        df = pd.concat(quadros, ignore_index=True)
        df['classe_nome'] = df['classe'].map(lambda c: CLASSES.get(int(c), str(c)))
        salvar_csv(df, 'P2_P3_amostra_bruta.csv')
        # P2
        t2 = comparar_bandas(df, 's_', 'a_', ORDEM, grupo='data')
        salvar_csv(t2, 'P2_V10_recalculada_x_gravado.csv')
        st, det = status_reproducao(t2)
        # [v3] proveniência: quando cada imagem de origem foi atualizada no catálogo x quando o dia foi gravado no SAB
        prov = {}
        for d in DIAS_P2:
            p = {}
            for chave, caminho in (('sab', f'{ASSET_SAB}/SAB_{d.replace("-", "_")}'),
                                   ('era5', f'ECMWF/ERA5_LAND/DAILY_AGGR/{d.replace("-", "")}')):
                try:
                    p[chave] = ee.data.getAsset(caminho).get('updateTime')
                except Exception as e:
                    p[chave] = None
                    log(f'   {caminho}: data de atualização não lida ({str(e)[:100]})')
            try:
                idx = gi(ee.ImageCollection('projects/ee-alexandrexavier/assets/BR-DWGD')
                         .filterDate(d, (pd.Timestamp(d) + pd.Timedelta(days=1)).strftime('%Y-%m-%d'))
                         .first().get('system:index'), 'BR-DWGD id', tentativas=1)
                p['brdwgd'] = ee.data.getAsset(f'projects/ee-alexandrexavier/assets/BR-DWGD/{idx}').get('updateTime')
            except Exception:
                p['brdwgd'] = None
            prov[d] = p
        salvar_csv(pd.DataFrame([{'data': d, **v} for d, v in prov.items()]), 'P2_proveniencia_datas.csv')
        log(pd.DataFrame([{'data': d, **v} for d, v in prov.items()]).to_string(index=False))
        log('   (datas do catálogo só como registro: elas mudam quando o catálogo é republicado, sem o dado mudar)')
        so_era5, textos = assinatura_p2(df)
        for t_ in textos:
            log(f'   {t_}')
        if textos:
            det += (' | diagnóstico: ' + ('todas as diferenças são de variáveis acumuladas do ERA5-Land (revisão da '
                    'fonte depois da gravação; o código reproduz o resto)' if so_era5 else
                    'há diferença fora das variáveis acumuladas do ERA5-Land'))
        if sem and st == 'OK':
            st = 'ATENÇÃO'
        achado('P2', st, 'Histórico gravado = V1.0 recalculada hoje',
               det + f' | {len(quadros)} de {len(DIAS_P2)} dias de 1961 a 2025 × {len(pontos)} pixels' +
               (f' | não calculados: {sem}' if sem else ''))
        # P3
        resumo = []
        for rot, pa, pref in (('V1.0 x V1.3', 'a_', 'b_'), ('V1.0 x V1.5', 'a_', 'c_'),
                              ('gravado x o que o usuário vê (correção de leitura)', 's_', 'l_')):
            t = comparar_bandas(df, pa, pref, ORDEM, grupo='classe_nome')
            t.insert(0, 'comparacao', rot)
            resumo.append(t)
        t3 = pd.concat(resumo, ignore_index=True)
        salvar_csv(t3, 'P3_diferencas_entre_versoes.csv')
        nuc = t3[(t3['comparacao'] == 'V1.0 x V1.5') & (t3['grupo'] == 'A') & t3['banda'].isin(NUCLEO)]
        solo = t3[(t3['comparacao'] == 'V1.0 x V1.5') & t3['banda'].isin(SOLO)]
        log(t3[t3['frac_iguais'] < 0.999].to_string(index=False) if (t3['frac_iguais'] < 0.999).any()
            else '   nenhuma diferença entre as versões na amostra')
        achado('P3', 'INFO', 'Onde a V1.0 difere da V1.3/V1.5 (rota definitiva)',
               f'núcleo (chuva, temperaturas, UR, VPD, ETo, radiação, vento) nos pixels A: '
               f'{100 * nuc["frac_iguais"].min():.2f}% a {100 * nuc["frac_iguais"].max():.2f}% iguais | '
               f'solo e escoamento (todas as classes): {100 * solo["frac_iguais"].min():.1f}% a '
               f'{100 * solo["frac_iguais"].max():.1f}% iguais | tabela completa em P3_diferencas_entre_versoes.csv')

    # ---------------------------------------------------------------------------------- P4
    @parte('P4 Origem das calibrações (SICSB_1986_2025 e SICSB_SOLO_2015_2025 recalculadas x gravadas)')
    def p4():
        # [v3] O código original (O2/O4) é chamado sem mudança; durante a chamada, mean() e reduce() da coleção
        # anotam QUAL coleção e QUAL redutor ele usou (e seguem fazendo o mesmo cálculo). Depois cada imagem
        # dessas coleções é lida nos pixels (reduceRegions, grade nativa) e a média/desvio vira conta de tabela,
        # com o mesmo redutor: mesmo resultado, sem montar 1.240 imagens na memória de uma vez.
        def capturar(fn, mes):
            anot, dentro = [], [False]
            orig_mean, orig_reduce = ee.ImageCollection.mean, ee.ImageCollection.reduce

            def mean(self, *a, **k):
                if not dentro[0]:
                    anot.append((self, ee.Reducer.mean(), '_m_'))
                dentro[0] = True
                try:
                    return orig_mean(self, *a, **k)
                finally:
                    dentro[0] = False

            def reduce(self, reducer, *a, **k):
                if not dentro[0]:
                    anot.append((self, reducer, '_s_'))
                dentro[0] = True
                try:
                    return orig_reduce(self, reducer, *a, **k)
                finally:
                    dentro[0] = False
            ee.ImageCollection.mean, ee.ImageCollection.reduce = mean, reduce
            try:
                img = ee.Image(fn(mes))
            finally:
                ee.ImageCollection.mean, ee.ImageCollection.reduce = orig_mean, orig_reduce
            return img, anot

        def ler_colecao(col, redutor, bandas_col, nomes, lista, rotulo):
            linhas, i, n = [], 0, len(lista)
            while i < len(lista):
                sub = lista[i:i + n]
                pts = fc_de(sub)
                tab = (col.map(lambda im: im.reduceRegions(collection=pts, reducer=ee.Reducer.first(), crs=CRS,
                                                           crsTransform=TRANSFORM, tileScale=4))
                       .flatten().filter(ee.Filter.notNull(bandas_col)))
                red = redutor.repeat(len(bandas_col)).group(groupField=len(bandas_col), groupName='pid')
                try:
                    res = gi(tab.reduceColumns(red, bandas_col + ['pid']), rotulo)
                    linhas.append(tabela_agrupada(res, nomes, 'r_'))
                    i += len(sub)
                except Pesado:
                    if n <= 5:
                        raise
                    n = max(5, n // 2)
                    log(f'   {rotulo}: pedido pesado, lote reduzido para {n} pixels')
            return pd.concat(linhas, ignore_index=True) if linhas else pd.DataFrame(columns=['pid'])

        tabelas = []
        for nome, fn, asset_nome, prefixo, mes in MATRIZES_P4:
            rot = f'{prefixo}_{mes:02d}'
            gravada = ee.Image(f'projects/{PROJETO}/assets/{asset_nome}/{rot}')
            nomes_g = gi(gravada.bandNames(), 'bandas da matriz')
            refeita, anot = capturar(carga[nome][fn], mes)
            nomes_r = gi(refeita.bandNames(), 'bandas recalculadas')
            bandas_cols = gi(ee.List([c.first().bandNames() for c, _, _ in anot]), 'bandas das coleções')
            if sorted(nomes_r) != sorted(nomes_g) or sum(len(b) for b in bandas_cols) != len(nomes_r):
                raise RuntimeError(f'{rot}: bandas não batem (gravada {len(nomes_g)}, recalculada {len(nomes_r)}, '
                                   f'coleções {[len(b) for b in bandas_cols]})')
            df = amostra_varias([('s_', gravada)], nomes_g, pontos_p4, rot)
            k = 0
            for (col, redutor, marca), bcol in zip(anot, bandas_cols):
                nomes = nomes_r[k:k + len(bcol)]
                k += len(bcol)
                if not all(marca in n for n in nomes):      # média -> bandas _m_, desvio -> _s_ (ordem do código)
                    raise RuntimeError(f'{rot}: ordem das bandas inesperada {nomes} para {marca}')
                parte_df = ler_colecao(col, redutor, bcol, nomes, pontos_p4, f'{rot} {nomes[0][:12]}…')
                df = df.merge(parte_df, on='pid', how='left')
                log(f'   {rot}: {len(nomes)} bandas de {nomes[0]} a {nomes[-1]} lidas em {len(parte_df)} pixels')
            fora = df[[f's_{b}' for b in nomes_g]].isna().all(axis=1)
            df = df[~fora]                                  # pixels fora da região exportada (sem valor gravado)
            salvar_csv(df, f'P4_amostra_{rot}.csv')
            t = comparar_bandas(df, 's_', 'r_', nomes_g)
            t.insert(0, 'matriz', rot)
            tabelas.append(t)
            log(f'   {rot}: {len(df)} pixels ({int(fora.sum())} fora da região exportada), {len(nomes_g)} bandas, '
                f'{100 * t["frac_iguais"].min():.1f}% a {100 * t["frac_iguais"].max():.1f}% iguais')
        t4 = pd.concat(tabelas, ignore_index=True)
        salvar_csv(t4, 'P4_matrizes_recalculadas_x_gravadas.csv')
        t4['grupo'] = t4['matriz']
        st, det = status_reproducao(t4)
        achado('P4', st, 'Matrizes de calibração gravadas = códigos originais (O2 e O4)',
               det + f' | {", ".join(m[3] + f"_{m[4]:02d}" for m in MATRIZES_P4)}, {len(pontos_p4)} pixels A')

    # ---------------------------------------------------------------------------------- P5
    @parte('P5 2026: provisórios recalculados com a V1.5 e propriedades da previsão')
    def p5():
        df_inv = estado.get('df')
        if df_inv is None:
            raise RuntimeError('o P1 não rodou')
        prov = sorted(df_inv[df_inv['versao'] == 'provisoria_era5']['id'])[-3:]
        quadros = []
        for nome in prov:
            d = nome.replace('SAB_', '').replace('_', '-')
            df = amostra_varias([('s_', ee.Image(f'{ASSET_SAB}/{nome}')), ('c_', carga['v15']['processarDia_Rota1'](d))],
                                ORDEM, pontos, d)
            df['data'] = d
            quadros.append(df)
        df = pd.concat(quadros, ignore_index=True)
        t5 = comparar_bandas(df, 's_', 'c_', ORDEM, grupo='data')
        salvar_csv(t5, 'P5_provisorios_V15_x_gravado.csv')
        st, det = status_reproducao(t5)
        # previsão: propriedades
        prev = df_inv[df_inv['versao'].isin(['provisoria_gfs', 'provisoria_gfs_incompleta', 'falha_latencia_gfs'])]
        info = gi(COL.filter(ee.Filter.inList('system:index', list(prev['id'])))
                  .map(lambda i: ee.Feature(None, {'id': i.get('system:index'), 'p': i.toDictionary()})), 'previsão')
        sem = [f['properties']['id'] for f in info['features']
               if not {'rodada_gfs_ms', 'versao_algoritmo'} <= set(f['properties']['p'])]
        conf = sorted({str(f['properties']['p'].get('Confianca_Prazo', f['properties']['p'].get('confianca_prazo', '-')))
                       for f in info['features']})
        det += f' | previsão: {len(prev)} dias, Confianca_Prazo {conf}' + (f'; sem rodada/versão: {sem[:5]}' if sem else '')
        if sem and st == 'OK':
            st = 'ATENÇÃO'
        achado('P5', st, f'Provisórios de 2026 = V1.5 ({", ".join(prov)}) e previsão com propriedades', det)

    # ---------------------------------------------------------------------------------- P6
    @parte('P6 Coerência física do acervo (um dia por ano, 2026 e toda a previsão)')
    def p6():
        df_inv = estado.get('df')
        if df_inv is None:
            raise RuntimeError('o P1 não rodou')
        datas = [f'{a}-{"07" if a % 2 else "01"}-15' for a in range(1961, 2026)]
        datas += [f'2026-{m:02d}-15' for m in range(1, 13) if f'2026-{m:02d}-15' <= estado['ult_era5']]
        datas += [i.replace('SAB_', '').replace('_', '-') for i in
                  df_inv[df_inv['versao'] != 'definitiva']['id'] if i.replace('SAB_', '').replace('_', '-') > estado['ult_era5']]

        def bandeiras(d):
            img = ee.Image(f'{ASSET_SAB}/SAB_{d.replace("-", "_")}')
            g = lambda b: img.select(b)
            band = [g('et_real').gt(g('et_potencial').add(0.001)).rename('etr_acima_eto'),
                    g('transpiracao_mm').gt(g('et_real').add(0.001)).rename('transp_acima_etr'),
                    g('tmax_C').lt(g('tmin_C')).rename('tmax_abaixo_tmin'),
                    g('RH').lt(0).Or(g('RH').gt(100)).rename('ur_fora'),
                    g('pr_mm').lt(0).rename('chuva_negativa'),
                    g('tmax_C').gt(TMAX_LIMITE).rename('tmax_acima_45'),
                    g('tmin_C').lt(TMIN_LIMITE).rename('tmin_abaixo_m10'),
                    g('soil_moisture_0_5cm_m3_m3').gt(UMIDADE_LIMITE + 1e-4)
                    .Or(g('soil_moisture_0_100cm_m3_m3').gt(UMIDADE_LIMITE + 1e-4)).rename('solo_acima_09_bruto')]
            if d <= FIM_HISTORICO:
                lido = lido_pelo_painel(d, img)
                band.append(lido.select('soil_moisture_0_5cm_m3_m3').gt(UMIDADE_LIMITE + 1e-4)
                            .Or(lido.select('soil_moisture_0_100cm_m3_m3').gt(UMIDADE_LIMITE + 1e-4))
                            .rename('solo_acima_09_lido'))
            fr = ee.Image.cat(band).unmask(0).updateMask(g('tmax_C').mask()).reduceRegion(
                reducer=ee.Reducer.mean(), geometry=BR, crs=CRS, crsTransform=TRANSFORM, maxPixels=1e9, tileScale=4)
            return ee.Feature(None, fr).set('data', d)

        linhas, sem = [], []
        for k in range(0, len(datas), LOTE_P6):
            lote = datas[k:k + LOTE_P6]
            try:
                res = gi(ee.FeatureCollection([bandeiras(d) for d in lote]), f'coerência {lote[0]}', tentativas=1)
                linhas += [f['properties'] for f in res['features']]
            except Exception:                 # lote pesado demais: um dia por pedido
                for d in lote:
                    try:
                        linhas += [f['properties'] for f in gi(ee.FeatureCollection([bandeiras(d)]), d)['features']]
                    except Exception as e:
                        sem.append(d)
                        log(f'   {d}: não calculado ({str(e)[:120]})')
            log(f'   {lote[0]} a {lote[-1]}: ok')
        tab = pd.DataFrame(linhas)
        salvar_csv(tab, 'P6_coerencia_fisica.csv')
        st, det = status_coerencia(tab)
        if sem:
            det += f' | {len(sem)} dia(s) não calculados: {sem[:5]}'
            st = 'ATENÇÃO' if st == 'OK' else st
        achado('P6', st, 'Coerência física (fração de pixels com cada problema)', det)

    # ---------------------------------------------------------------------------------- P7
    @parte('P7 Validação independente da chuva: SAB x CHIRPS (totais mensais)')
    def p7():
        chirps = ee.ImageCollection(CHIRPS).select('precipitation')
        proj_ch = ee.Image(chirps.first()).projection()
        meses = [(m, 'histórico') for m in MESES_CHIRPS_HIST]
        meses += [(f'2026-{m:02d}', '2026 provisório') for m in range(1, 13)
                  if f'2026-{m:02d}-01' <= estado.get('ult_era5', '2026-01-01')]
        linhas = []
        for m, per in meses:
            ini = ee.Date(m + '-01')
            fim = ini.advance(1, 'month')
            n_dias = gi(ee.Dictionary({'sab': COL.filterDate(ini, fim).size(), 'ch': chirps.filterDate(ini, fim).size(),
                                       'dias': fim.difference(ini, 'day')}), f'contagem {m}')
            if n_dias['sab'] < n_dias['dias'] or n_dias['ch'] < n_dias['dias']:
                log(f'   {m}: mês incompleto (SAB {n_dias["sab"]}, CHIRPS {n_dias["ch"]} de {n_dias["dias"]} dias): fora')
                continue
            sab = COL.filterDate(ini, fim).select('pr_mm').sum().rename('sab')
            ch = (chirps.filterDate(ini, fim).sum().setDefaultProjection(proj_ch)
                  .reduceResolution(ee.Reducer.mean(), maxPixels=64).reproject(PROJ).rename('chirps'))
            df = amostra_varias([('', ee.Image.cat([sab, ch]))], ['sab', 'chirps'], pontos_m, m)
            df = df[df['classe'].isin([1, 2, 3])].dropna(subset=['sab', 'chirps'])
            df['periodo'], df['mes'] = per, m
            linhas.append(df)
            log(f'   {m}: {len(df)} pixels')
        df = pd.concat(linhas, ignore_index=True) if linhas else pd.DataFrame(columns=['periodo', 'sab', 'chirps'])
        salvar_csv(df, 'P7_sab_x_chirps_mensal.csv')
        tab = estatisticas_chirps(df)
        salvar_csv(tab, 'P7_resumo.csv')
        st, det = status_chirps(tab)
        achado('P7', 'INFO' if st == 'OK' else st, 'Chuva do SAB x CHIRPS (fonte independente)', det)

    # ---------------------------------------------------------------------------------- P8
    @parte('P8 RONI_CPC_v6 x arquivo oficial do CPC/NOAA')
    def p8():
        r = requests.get(URL_RONI_CPC, timeout=60)
        r.raise_for_status()
        cpc = pd.read_csv(io.StringIO(r.text), sep=r'\s+')
        fc = gi(ee.FeatureCollection(ASSET_RONI), 'RONI_CPC_v6')
        asset = pd.DataFrame([f['properties'] for f in fc['features']])
        st, det, m = avaliar_roni(asset, cpc)
        salvar_csv(m, 'P8_roni_asset_x_cpc.csv')
        achado('P8', st, 'RONI do asset = tabela oficial do CPC', det)

    # ---------------------------------------------------------------------------------- P9
    @parte('P9 Máscara de qualidade (contagem por classe)')
    def p9():
        # [v3] mesma receita do 01b (contar_classes): soma sem ponderar de classe == k, na região ampla, grade nativa
        masc = ee.Image(ASSET_MASCARA)
        classe = masc.select('classe')
        ind = ee.Image.cat([classe.eq(k).rename(f'n_classe_{k}') for k in (1, 2, 3, 4)])
        r = gi(ind.reduceRegion(reducer=ee.Reducer.sum().unweighted(),
                                geometry=ee.Geometry.Rectangle(REGIAO_AMPLA, None, False), crs=CRS,
                                crsTransform=TRANSFORM, maxPixels=1e10, tileScale=4), 'máscara')
        hist = {k: int(round(r.get(f'n_classe_{k}') or 0)) for k in (1, 2, 3, 4)}
        props = gi(masc.toDictionary(), 'propriedades da máscara')
        gravado = ({k: int(props[f'n_classe_{k}']) for k in (1, 2, 3, 4)}
                   if all(f'n_classe_{k}' in props for k in (1, 2, 3, 4)) else None)
        log(f'   propriedades do asset: ' + ', '.join(f'{k}={props[k]}' for k in sorted(props) if not str(k).startswith('system')))
        st, det = avaliar_mascara(hist, gravado)
        achado('P9', st, 'Máscara de qualidade = a que o 01b gravou', det)

    for fn in (p1, p2_p3, p4, p5, p6, p7, p8, p9):
        fn()

    # ---------------------------------------------------------------------------------- resultado
    tab = pd.DataFrame(ACHADOS)
    salvar_csv(tab, 'K17_RESUMO.csv')
    aprovado, falta, p6 = veredito(ACHADOS)
    log('\n' + '=' * 100 + '\nRESULTADO FINAL K17\n' + '=' * 100)
    for a in ACHADOS:
        log(f"   {a['parte']:3} {a['status']:13} {a['titulo']}")
    if aprovado:
        log('\n   ✅ VALIDAÇÃO FINAL APROVADA: os dados gravados, do histórico à previsão, são o que os códigos dizem, '
            'sem incoerência física, com o RONI oficial e a máscara de referência.')
    else:
        log(f'\n   ⚠️ VALIDAÇÃO FINAL PENDENTE: {", ".join(falta) or "-"} não saíram ✅' +
            (f'; P6 = {p6}' if p6 not in ('OK', 'ATENÇÃO') else '') + '. Me envie o zip: o detalhe diz o motivo.')
    log(f'\nTempo: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine (trava de somente leitura).')
    z = shutil.make_archive(PASTA, 'zip', PASTA)
    log(f'📦 {z}')
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        pass


if __name__ == '__main__':
    principal()
