# >>> VALIDAÇÃO K16 v7.1 (23/11/2026): o envio por e-mail entrega o MESMO arquivo do painel? Cole inteiro, sem editar. <<<
# [v7.1, 23/11/2026] três consertos da própria K16, depois da corrida de 22/11 21h54 (todos os casos A, B e o A7 já
#   saíram idênticos ao painel 2026.11.5): (1) o R7 contava também as linhas SEM DADO nenhum (pixels do polígono sem
#   valor em nenhuma variável, 3 x 31 dias); agora só as linhas com dado entram; (2) a linha do E1 no log saía com o
#   texto do R7 (o resultado do E1 estava certo: E1=True); (3) o Drive pode criar duas pastas com o mesmo nome quando
#   várias exportações começam juntas para uma pasta nova; agora a K16 procura o arquivo exportado também nas outras
#   pastas do Meu Drive (foi o que deixou o dicionário do A1 "ausente"). Rodar de novo reaproveita tudo: as exportações,
#   os CSV do painel e o progresso ficam no Drive, e só a comparação é refeita (poucos minutos).
# [v7, 22/11/2026] rotina sab_pedido.py 2026.11.22 e painel 2026.11.5: Rs abaixo de 3% da radiação no topo da atmosfera
#   (impossível de dia; ex.: 0, achado da K26) sai como célula VAZIA, nos dois, com a ETo e o déficit do dia (calculados
#   com ela). Caso novo A7: polígono na Lagoa Mirim (RS), março de 2026, onde a K26 achou Rs gravado = 0 de 04 a 20/03 em
#   pixels B. Conferência nova R7, na planilha do e-mail do A7: a radiação sai vazia em algum dia, só em 04-20/03, nunca
#   com valor abaixo de 0,5 MJ/m²; nas linhas com a radiação vazia, ETo e déficit também vazios, e a ET real preenchida. A parte C (tempo do link) não muda com a regra e fica desligada (RODAR_PARTE_C;
#   medida na v6: o limite do link é o mesmo para qualquer escolha). Pastas do Drive com as versões novas.
# [v6, 18/11/2026] rotina sab_pedido.py 2026.11.19 e painel 2026.11.4. A rotina 2026.11.18 corrigiu o pedido de UMA
#   variável só, que saía com a coluna vazia (com uma banda, o reduceRegions grava a média como 'mean'); a 2026.11.19 e
#   o painel 2026.11.4 levam o mesmo aviso do escoamento no dicionário (K26). Caso novo B2: o A1 só com a chuva
#   (var=pr), que tem de ser igual à coluna Precipitacao_mm do A1 do painel (com a rotina antiga, ela saía vazia).
#   As pastas do Drive levam as versões novas: nada da rodada anterior é reaproveitado.
# [v5, 04/11/2026] painel 2026.11.3, o publicado no app adao-alves-rodrigues-junior-sab (a 2026.11.3 só muda a autoria e o
#   botão do e-mail; os cálculos são os da 2026.11.1, aprovada pela K16 v4 em 03/11, 22h35).
# [v4, 03/11/2026, 22h] painel 2026.11.1 e rotina 2026.11.03 (correção de leitura dos pixels B e da radiação dos pixels
#   C). Caso novo A6: polígono na Lagoa dos Patos (RS), jan-mar/2024, com pixels B. As pastas do Drive levam a versão
#   (K16_painel_2026.11.1, K16_teste_2026.11.03, K16_2026.11.03): nada da rodada anterior é reaproveitado.
# =========================================================================================
# POR QUE EXISTE
#   O envio por e-mail usa a rotina sab_pedido.py (GitHub Actions), escrita em Python a partir do cálculo
#   do painel 2026.10.4 (JavaScript). Antes de ligar o envio para o público, é preciso provar que os CSV da
#   rotina são IGUAIS, célula a célula e com os mesmos nomes de arquivo, aos que o próprio painel gera.
#   A K14 comparou a exportação com o link do MESMO código Python; aqui a comparação é com o painel.
#   Também mede se escolher menos variáveis deixa o link na hora mais rápido.
#
# [v3] OS CSV DO PAINEL AGORA SÃO GERADOS AQUI MESMO (parte P): a K16 roda o PRÓPRIO código do painel
#   (06_painel_sab_2026_11_5.js, embutido abaixo sem mudança, com a impressão digital SHA-256) no Node.js do Colab,
#   com o Earth Engine de verdade (@google/earthengine, a mesma biblioteca do Code Editor). Só a tela é simulada:
#   uma "pessoa" preenche os campos de cada caso, clica em PROCESSAR e baixa os links, que são os MESMOS
#   getDownloadURL do botão de download do painel. Os CSV vão para MeuDrive/K16_painel/<caso>/.
#   Se você já tiver posto CSV baixados à mão numa pasta K16_painel/<caso>/, esse caso usa os seus.
#   Para fazer à mão (GERAR_PAINEL = False), os casos são (no painel publicado, sem a caixa de previsão e sem o
#   filtro ENSO, exceto no A5), com os CSV em MeuDrive/K16_painel/<caso>/:
#   A1  Município Pato Branco (PR), Diária, 01/01/2025 a 31/12/2025
#       -> K16_painel/A1/Diaria_Pato_Branco_2025.csv e K16_painel/A1/00_Dicionario_Variaveis_SAB.csv
#   A2  Municípios Pato Branco + Clevelândia (PR), Diária, 01/01/2025 a 31/12/2025
#       -> K16_painel/A2/Diaria_Pato_Branco_2025.csv e K16_painel/A2/Diaria_Clevelandia_2025.csv
#   A3  Município Pato Branco (PR), Mensal, 01/01/2025 a 31/12/2025  -> K16_painel/A3/Mensal_Pato_Branco_2025.csv
#   A4  Coordenadas, formato Decimal, 4 pontos na ordem: -26.2/-52.7, -26.2/-52.6, -26.3/-52.6, -26.3/-52.7;
#       Diária, 01/01/2025 a 31/03/2025  -> K16_painel/A4/Diaria_Poligono_1_2025.csv
#   A5  Município Pato Branco (PR), Diária, 01/01/2015 a 31/12/2016, com o filtro do item B ligado
#       ("Filtrar os dados do passado por fenômeno" = El Niño forte (+1,5 a +1,9 °C))
#       -> K16_painel/A5/ todos os CSV que o painel gerar (ex.: Diaria_Pato_Branco_2015_El_Nino_Forte.csv)
#   (Se faltar algum caso, o script compara os que existirem e diz quais ficaram sem conferência.)
#
# MUDANÇA DA v3 (03/11/2026): parte P (CSV do painel gerados pelo próprio painel, no Node). O resto é a v2.
# MUDANÇA DA v2 (rotina 2026.11.01): o CSV do e-mail traz SEMPRE as colunas ENSO no fim (6: as 5 do painel +
#   Fonte_ENSO) e o dicionário tem textos novos nas linhas ENSO e no formato dos números. A identidade agora é:
#   as colunas do PAINEL saem idênticas, na mesma ordem, célula a célula; a rotina só pode ter A MAIS as colunas ENSO
#   (as 6 sem filtro; só Fonte_ENSO no A5, que já tem as 5 do painel); no dicionário, só as linhas mudadas de
#   propósito (lista DICIONARIO_MUDADO) e a nova Fonte_ENSO podem diferir. O caso E1 (novo) confere as colunas ENSO
#   dos dias recentes e da previsão, que o painel não classifica.
#
# O QUE FAZ
#   A  Para cada caso, a rotina sab_pedido.py (embutida abaixo, com a impressão digital SHA-256) monta o
#      pedido como o e-mail faria e exporta os CSV para a pasta K16_teste do Drive. Confere: os nomes dos
#      arquivos iguais aos do painel e cada CSV IDÊNTICO ao do painel (todas as células, como texto).
#   B  O caso A1 só com chuva e temperaturas (var=pr,tmax,tmin): deve ser igual às mesmas colunas do A1.
#      [v6] B2: o A1 só com a chuva (var=pr, UMA variável): igual à coluna Precipitacao_mm do A1.
#   C  Link na hora (getDownloadURL, como o painel) do Paraná, 01/01 a 31/03/2025 (~170 mil linhas), com
#      as 19 variáveis e com 3 (pr, tmax, tmin), alternados: 19, 3, 19, 3.
#   A7 [v7] Lagoa Mirim (RS), polígono -32,5/-53,0 a -32,8/-52,7, diária, 01/03 a 31/03/2026 (pixels B com o Rs gravado
#      = 0 em 04-20/03): identidade com o painel, como os outros A, e a conferência R7 da radiação vazia.
#   E1 Pato Branco, diária, de 01/09/2026 até o fim da previsão (sem filtro): nenhuma linha Sem_Dado em Fonte_ENSO,
#      os dias de previsão com Fonte_ENSO Persistencia (ou Estimativa_OISST_parcial) e Filtro_ENSO = Sem filtro.
#   D  (opcional) PASTA_PEDIDO: nome de uma pasta SAB_pedido_<ID> feita pelo GitHub para o pedido do A1;
#      os arquivos dela também são comparados com o painel (prova do caminho completo).
#
# REGRA DE DECISÃO (fixada antes de rodar)
#   IDENTIDADE: aprovado para ligar o envio por e-mail só se TODOS os casos A conferidos tiverem os mesmos
#     nomes de arquivo e as colunas do painel idênticas (só as colunas ENSO a mais), o B for igual às colunas do A1,
#     o E1 passar e os casos A tiverem o CSV do painel no Drive. [v7] E o R7 passar (radiação impossível vazia no A7). Qualquer diferença: não ligar; me envie o zip.
#   VARIÁVEIS: menos variáveis "aceleram o link" se o link com 3 variáveis levar no máximo 70% do tempo do
#     link com 19 nos DOIS pares. Se sim, o limite do link na hora no painel pode crescer com menos
#     variáveis (proporção medida); se não, o limite é o mesmo para qualquer escolha.
#
# O QUE GRAVA: só CSV na pasta K16_teste do seu Drive. Nada no Earth Engine; nenhum asset.
# ANTES DE RODAR: Ambiente de execução -> Reiniciar sessão. Não rode junto com o 05b.
# TEMPO: de 30 a 60 minutos. Se a célula parar, rode de novo: retoma pelo progresso no Drive.
# NO FIM: o Colab baixa validacao_K16_<data>.zip (LOG_K16.txt e K16_resultados.csv). Me envie o zip.
# =========================================================================================
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import types
from datetime import datetime, timedelta, timezone

import ee
import pandas as pd
import requests

PASTA_PEDIDO = ''          # opcional (parte D): ex. 'SAB_pedido_P20261103140000abcd'
GERAR_PAINEL = True        # [v3] gera os CSV do painel que faltarem rodando o próprio painel (parte P)
RODAR_PARTE_C = False      # [v7] o tempo do link (parte C) foi medido na v6 e a regra da radiação não o muda
PROJETO = 'clima-492922'
PASTA_DRIVE = 'K16_teste'
INTERVALO_S = 30
ESPERA_MAX_H = 3
ESPERA_ARQUIVO_S = 900
TIMEOUT_LINK_S = 1200
MARGEM_VARIAVEIS = 0.70
CASOS = [
    ('A1', 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=todas'),
    ('A2', 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco,Clevelândia;ini=2025-01-01;fim=2025-12-31;var=todas'),
    ('A3', 'v=1;res=M;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=todas'),
    ('A4', 'v=1;res=D;tipo=P;pol=-26.2 -52.7,-26.2 -52.6,-26.3 -52.6,-26.3 -52.7;ini=2025-01-01;fim=2025-03-31;var=todas'),
    ('A5', 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2015-01-01;fim=2016-12-31;var=todas;enso=El_Nino_Forte'),
    # [2026.11.03] Lagoa dos Patos (RS): pixels B, para provar a correção de leitura dos pixels B do painel 2026.11.1
    ('A6', 'v=1;res=D;tipo=P;pol=-30.9 -51.4,-30.9 -51.1,-31.2 -51.1,-31.2 -51.4;ini=2024-01-01;fim=2024-03-31;var=todas'),
    ('B1', 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=pr,tmax,tmin'),
    # [v6] UMA variável só: com a rotina antiga a coluna saía vazia
    ('B2', 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=pr'),
    # [v7] Lagoa Mirim (RS), março de 2026: pixels B com Rs gravado = 0 de 04 a 20/03 (K26): a radiação sai vazia
    ('A7', 'v=1;res=D;tipo=P;pol=-32.5 -53.0,-32.5 -52.7,-32.8 -52.7,-32.8 -53.0;ini=2026-03-01;fim=2026-03-31;var=todas')]
CASO_E1 = 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2026-09-01;fim=<FIM>;var=pr,tmax'
# linhas do dicionário cujo texto mudou de propósito na rotina 2026.11.01 (as demais têm de ser idênticas às do painel)
DICIONARIO_MUDADO = ('Filtro_ENSO', 'Fase_ENSO', 'Intensidade_ENSO', 'RONI_Trimestre_C', 'Trimestre_CPC',
                     '(formato dos numeros)')
# [v3] o que a "pessoa simulada" preenche no painel em cada caso (mesmos pedidos de CASOS)
TELA_PAINEL = {
    'A1': {'res': 'Diária', 'local': {'tipo': 'M', 'uf': ['Paraná'], 'mun': ['Pato Branco']},
           'ini': '01/01/2025', 'fim': '31/12/2025', 'enso': None},
    'A2': {'res': 'Diária', 'local': {'tipo': 'M', 'uf': ['Paraná'], 'mun': ['Pato Branco', 'Clevelândia']},
           'ini': '01/01/2025', 'fim': '31/12/2025', 'enso': None},
    'A3': {'res': 'Mensal', 'local': {'tipo': 'M', 'uf': ['Paraná'], 'mun': ['Pato Branco']},
           'ini': '01/01/2025', 'fim': '31/12/2025', 'enso': None},
    'A4': {'res': 'Diária', 'local': {'tipo': 'P', 'pontos': [[-26.2, -52.7], [-26.2, -52.6], [-26.3, -52.6], [-26.3, -52.7]]},
           'ini': '01/01/2025', 'fim': '31/03/2025', 'enso': None},
    'A5': {'res': 'Diária', 'local': {'tipo': 'M', 'uf': ['Paraná'], 'mun': ['Pato Branco']},
           'ini': '01/01/2015', 'fim': '31/12/2016', 'enso': 'El Niño Forte (1.5 a 1.9°C)'},
    'A6': {'res': 'Diária', 'local': {'tipo': 'P', 'pontos': [[-30.9, -51.4], [-30.9, -51.1], [-31.2, -51.1], [-31.2, -51.4]]},
           'ini': '01/01/2024', 'fim': '31/03/2024', 'enso': None},
    'A7': {'res': 'Diária', 'local': {'tipo': 'P', 'pontos': [[-32.5, -53.0], [-32.5, -52.7], [-32.8, -52.7], [-32.8, -53.0]]},
           'ini': '01/03/2026', 'fim': '31/03/2026', 'enso': None}}
# [v7] R7: a janela em que a K26 achou o Rs gravado = 0 nos pixels B da Lagoa Mirim
JANELA_R7 = ('2026-03-04', '2026-03-20')
CODIGO_C = {'19': 'v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-03-31;var=todas',
            '3': 'v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-03-31;var=pr,tmax,tmin'}

# ------------------------------------------------------------------ a rotina do e-mail, sem mudança
ROTINA_SRC = r'''<<ROTINA>>'''
sp = types.ModuleType('sab_pedido')
exec(compile(ROTINA_SRC, 'sab_pedido.py', 'exec'), sp.__dict__)
SHA_ROTINA = hashlib.sha256(ROTINA_SRC.encode('utf-8')).hexdigest()

# ------------------------------------------------------------------ [v3] o painel, sem mudança, e quem o opera no Node
PAINEL_SRC = r'''<<PAINEL>>'''
NODE_SRC = r'''<<NODE>>'''
SHA_PAINEL = hashlib.sha256(PAINEL_SRC.encode('utf-8')).hexdigest()
VERSAO_PAINEL_JS = (re.search(r"versao: '([^']+)'", PAINEL_SRC) or [None, '?'])[1]
# [2026.11.03] pastas do Drive com a versão: uma rodada com painel ou rotina novos nunca reaproveita CSV, exportações
# ou tempos de uma versão anterior (as pastas antigas ficam como estão, para registro)
PASTA_DRIVE = f'K16_teste_{sp.VERSAO_ROTINA}'
PASTA_PAINEL = f'K16_painel_{VERSAO_PAINEL_JS}'
PASTA_PROGRESSO = f'K16_{sp.VERSAO_ROTINA}'

AGORA = datetime.now(timezone(timedelta(hours=-3)))
BASE = '/content' if os.path.isdir('/content') else '.'
PASTA = os.path.join(BASE, f'validacao_K16_{AGORA:%Y%m%d_%H%M}')
LOG = os.path.join(PASTA, 'LOG_K16.txt')
DRIVE = '/content/drive/MyDrive'
TERMINAIS = ('COMPLETED', 'FAILED', 'CANCELLED', 'SUCCEEDED')


def log(*p):
    t = ' '.join(str(x) for x in p)
    print(t, flush=True)
    os.makedirs(PASTA, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(t + '\n')


# =========================================================================================
# FUNÇÕES PURAS (testadas offline em testes/teste_k16.py)
# =========================================================================================
def ler_csv(caminho):
    return pd.read_csv(caminho, dtype=str, keep_default_na=False)


def comparar(df_a, df_b, chave=('N_Ponto', 'Data_Completa')):
    """(igual, detalhe). Mesmas colunas na mesma ordem e as mesmas células (texto), na ordem da chave."""
    if list(df_a.columns) != list(df_b.columns):
        return False, f'colunas diferentes: {list(df_a.columns)[:5]}... x {list(df_b.columns)[:5]}...'
    if len(df_a) != len(df_b):
        return False, f'linhas: {len(df_a)} x {len(df_b)}'
    k = [c for c in chave if c in df_a.columns]
    a = df_a.sort_values(k).reset_index(drop=True)
    b = df_b.sort_values(k).reset_index(drop=True)
    if a.equals(b):
        return True, f'{len(a)} linhas idênticas'
    dif = (a != b)
    cols = [c for c in a.columns if dif[c].any()]
    i = int(dif.any(axis=1).idxmax())
    c = cols[0]
    return False, (f'{int(dif.any(axis=1).sum())} linha(s) diferentes, colunas {cols[:6]}; ex.: {a.loc[i, k].tolist()} '
                   f'{c}: rotina "{a.loc[i, c]}" x painel "{b.loc[i, c]}"')


def comparar_painel(df_rot, df_pai, extras):
    """[v2] (igual, detalhe). As colunas do painel saem na rotina na mesma ordem e as extras da rotina (no fim) são
    exatamente `extras`; as células das colunas do painel são idênticas."""
    cols_pai = list(df_pai.columns)
    cols_rot = list(df_rot.columns)
    if cols_rot[:len(cols_pai)] != cols_pai or cols_rot[len(cols_pai):] != list(extras):
        return False, f'colunas: rotina {cols_rot[-8:]} x painel {cols_pai[-8:]} + extras esperadas {list(extras)}'
    igual, det = comparar(df_rot[cols_pai], df_pai)
    return igual, det + (f' (+ {len(extras)} coluna(s) ENSO só na rotina)' if igual and extras else '')


def extras_esperadas(colunas_painel):
    """Colunas que só a rotina tem: as 6 ENSO (painel sem filtro) ou só Fonte_ENSO (painel com filtro)."""
    return [c for c in sp.COLUNAS_ENSO if c not in colunas_painel]


def comparar_dicionario(df_rot, df_pai):
    """[v2] Cada variável do painel existe na rotina; fora de DICIONARIO_MUDADO, texto e unidade idênticos; a rotina
    só pode ter a mais a Fonte_ENSO."""
    r = {x.Variavel: (x.Descricao, x.Unidade) for x in df_rot.itertuples()}
    p = {x.Variavel: (x.Descricao, x.Unidade) for x in df_pai.itertuples()}
    faltam = [v for v in p if v not in r]
    sobram = [v for v in r if v not in p and v != 'Fonte_ENSO']
    difs = [v for v in p if v in r and v not in DICIONARIO_MUDADO and r[v] != p[v]]
    if faltam or sobram or difs:
        return False, f'faltam {faltam}, sobram {sobram}, textos diferentes {difs}'
    return True, (f'{len(p)} variáveis do painel; {len(p) - len(DICIONARIO_MUDADO)} idênticas, '
                  f'{len(DICIONARIO_MUDADO)} com texto novo de propósito, + Fonte_ENSO')


def conferir_e1(df):
    """[v2] Colunas ENSO dos dias recentes e da previsão (o painel não as tem): (ok, detalhe)."""
    if 'Fonte_ENSO' not in df.columns or not len(df):
        return False, 'sem a coluna Fonte_ENSO ou sem linhas'
    prev = df[df['Tipo_Dado'].str.startswith('Previsao')]
    sem = int((df['Fonte_ENSO'] == 'Sem_Dado').sum())
    fontes_prev = sorted(prev['Fonte_ENSO'].unique())
    ok = bool(sem == 0 and len(prev) > 0 and set(fontes_prev) <= {'Persistencia', 'Estimativa_OISST_parcial'}) and \
        set(df['Filtro_ENSO'].unique()) == {'Sem filtro'} and bool((df['Fase_ENSO'] != '').all())
    return ok, (f'{len(df)} linhas, {len(prev)} de previsão; Fonte_ENSO na previsão {fontes_prev}; Sem_Dado {sem}; '
                f'fontes no período {sorted(df["Fonte_ENSO"].unique())}')


def conferir_r7(df):
    """[v7] Planilha do e-mail do A7 (Lagoa Mirim, março de 2026): (ok, detalhe). A radiação sai vazia em algum dia,
    só dentro de JANELA_R7, nunca com valor abaixo de 0,5 MJ/m² (3% de Ra em março ali é ~1 MJ/m²); nas linhas com a
    radiação vazia, a ETo e o déficit também vazios (calculados com ela) e a ET real preenchida (vem antes da regra)."""
    rs, eto, dfc, etr, tx = ('Radiacao_Solar_MJ_m2', 'Evapotranspiracao_Potencial_mm', 'Deficit_Hidrico_mm',
                             'Evapotranspiracao_Real_mm', 'Temperatura_Maxima_C')
    if not len(df) or any(c not in df.columns for c in (rs, eto, dfc, etr, tx)):
        return False, 'sem linhas ou sem as colunas da radiação, da ETo, do déficit, da ET real e da Tmax'
    # [v7.1] só as linhas com dado: um pixel do polígono sem valor em nenhuma variável não é a regra da radiação
    sem_dado = int((df[tx] == '').sum())
    df = df[df[tx] != '']
    if not len(df):
        return False, f'nenhuma linha com dado ({sem_dado} sem dado)'
    vazio = df[rs] == ''
    datas = sorted(df.loc[vazio, 'Data_Completa'].unique())
    fora = [d for d in datas if not JANELA_R7[0] <= d <= JANELA_R7[1]]
    baixos = int((pd.to_numeric(df.loc[~vazio, rs], errors='coerce') < 0.5).sum())
    juntas = int(((df.loc[vazio, eto] != '') | (df.loc[vazio, dfc] != '')).sum())
    etr_vazia = int((df.loc[vazio, etr] == '').sum())
    eto_sumiu = int((df.loc[~vazio, eto] == '').sum())
    ok = bool(vazio.any()) and not fora and baixos == 0 and juntas == 0 and etr_vazia == 0 and eto_sumiu == 0
    return ok, (f'{len(df)} linhas com dado ({sem_dado} sem dado nenhum, fora da conta); '
                f'{int(vazio.sum())} célula(s) de radiação vazias em {len(datas)} dia(s) '
                f'({datas[0] if datas else "-"} a {datas[-1] if datas else "-"}); fora da janela {fora[:3]}; '
                f'radiação abaixo de 0,5 MJ/m² {baixos}; nessas linhas ETo ou déficit preenchidos {juntas}, ET real '
                f'vazia {etr_vazia}; ETo vazia com a radiação preenchida {eto_sumiu}')


def decidir_k16(identidade, tempos):
    """identidade: {caso: True/False/None (sem CSV do painel)}; tempos: {'19': [s, s], '3': [s, s]}."""
    aprovado = bool(identidade) and all(v is True for v in identidade.values()) and \
        all(identidade.get(c) is True for c in ('A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'B1', 'B2', 'E1', 'R7'))
    t19, t3 = tempos.get('19', []), tempos.get('3', [])
    razoes = [round(b / a, 2) for a, b in zip(t19, t3) if a and b]
    acelera = len(razoes) == 2 and all(r <= MARGEM_VARIAVEIS for r in razoes)
    return {'aprovado': aprovado, 'razoes': razoes, 'acelera': acelera}


# ------------------------------------------------------------------ [v3] parte P: CSV do painel pelo próprio painel
def casos_sem_painel(drive):
    """Casos A1-A5 sem nenhum CSV de dados em K16_painel/<caso>/ (os que você já pôs à mão são mantidos)."""
    faltam = []
    for caso in TELA_PAINEL:
        pasta = os.path.join(drive, PASTA_PAINEL, caso)
        dados = [x for x in glob.glob(os.path.join(pasta, '*.csv')) if not os.path.basename(x).startswith('00_')]
        if not dados or (caso == 'A1' and not os.path.exists(os.path.join(pasta, '00_Dicionario_Variaveis_SAB.csv'))):
            faltam.append(caso)
    return faltam


def token_ee():
    """Token de acesso da MESMA conta que iniciou o Earth Engine aqui (vale 1 hora; não é gravado em lugar nenhum)."""
    import google.auth
    import google.auth.transport.requests
    cred = None
    for pegar in (lambda: ee.data._get_state().credentials, lambda: ee.data._credentials,
                  lambda: ee.data.get_persistent_credentials(),
                  lambda: google.auth.default(scopes=['https://www.googleapis.com/auth/earthengine',
                                                      'https://www.googleapis.com/auth/cloud-platform'])[0]):
        try:
            cred = pegar()
        except Exception:
            cred = None
        if cred is not None:
            break
    if cred is None:
        raise RuntimeError('não achei a credencial do Earth Engine nesta sessão')
    if getattr(cred, 'refresh', None):
        cred.refresh(google.auth.transport.requests.Request())
    tok = getattr(cred, 'token', None)
    if not tok:
        raise RuntimeError('a credencial do Earth Engine não deu um token de acesso')
    return tok


def preparar_node(pasta):
    """Node.js 18+ e a biblioteca @google/earthengine em <pasta>. Devolve o caminho do node."""
    def versao(cmd):
        try:
            return int(subprocess.run([cmd, '--version'], capture_output=True, text=True, timeout=30).stdout.strip()
                       .lstrip('v').split('.')[0])
        except Exception:
            return 0
    node = shutil.which('node')
    if not node or versao(node) < 18:
        log('   instalando o Node.js (pacote nodejs-wheel-binaries do pip)...')
        subprocess.run(['pip', 'install', '-q', 'nodejs-wheel-binaries'], check=True, timeout=600)
        node = shutil.which('node')
    if not node or versao(node) < 18:
        raise RuntimeError('Node.js 18 ou mais novo não disponível no Colab')
    npm = shutil.which('npm')
    os.makedirs(pasta, exist_ok=True)
    if not os.path.isdir(os.path.join(pasta, 'node_modules', '@google', 'earthengine')):
        log('   instalando a biblioteca JavaScript do Earth Engine (@google/earthengine, a do Code Editor)...')
        r = subprocess.run([npm, 'install', '--no-audit', '--no-fund', '--loglevel=error', '@google/earthengine@1'],
                           cwd=pasta, capture_output=True, text=True, timeout=900)
        if r.returncode != 0:
            raise RuntimeError('npm install falhou: ' + (r.stderr or r.stdout)[-300:])
    return node


def gerar_csv_painel(drive, planos):
    """Parte P. Roda o painel no Node para os casos sem CSV do painel. Devolve {caso: resultado do Node}."""
    faltam = casos_sem_painel(drive)
    if not faltam:
        log('   todos os casos já têm CSV do painel em K16_painel: nada a gerar')
        return {}
    pasta = os.path.join(BASE, 'k16_node')
    node = preparar_node(pasta)
    open(os.path.join(pasta, 'painel.js'), 'w', encoding='utf-8').write(PAINEL_SRC)
    open(os.path.join(pasta, 'k16_painel_node.js'), 'w', encoding='utf-8').write(NODE_SRC)
    casos = []
    for caso in faltam:
        c = dict(TELA_PAINEL[caso], caso=caso)
        c['esperados'] = list(planos.get(caso, [])) + (['00_Dicionario_Variaveis_SAB'] if caso == 'A1' else [])
        casos.append(c)
    json.dump(casos, open(os.path.join(pasta, 'casos.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    env = dict(os.environ, EE_TOKEN=token_ee())
    log(f"   rodando o painel {VERSAO_PAINEL_JS} para {', '.join(faltam)} (de 2 a 20 min por caso)...")
    proc = subprocess.Popen([node, 'k16_painel_node.js', 'painel.js', os.path.join(drive, PASTA_PAINEL), 'casos.json',
                             PROJETO], cwd=pasta, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    res = {}
    try:
        for linha in proc.stdout:
            linha = linha.rstrip()
            if linha.startswith('K16P_RESULTADO '):
                r = json.loads(linha[len('K16P_RESULTADO '):])
                res[r['caso']] = r
                ok = not r['faltando'] and not r['erros']
                log(f"   {'✅' if ok else '⚠️'} painel {r['caso']}: {len(r['arquivos'])} arquivo(s) em {r['segundos']} s"
                    + (f" | faltando {r['faltando']}" if r['faltando'] else '')
                    + (f" | erros {r['erros']}" if r['erros'] else '')
                    + (f" | avisos do painel {r['alertas']}" if r['alertas'] and not ok else ''))
            elif linha.startswith('K16P_ERRO') or linha.startswith('K16P '):
                log('   ' + linha.replace('K16P_ERRO', '❌ painel no Node:').replace('K16P ', ''))
        proc.wait(timeout=3600)
    finally:
        if proc.poll() is None:
            proc.kill()
    return res


def status_de(ids):
    try:
        return {s['id']: s for s in ee.data.getTaskStatus(ids)}
    except Exception as e:
        return {i: {'state': 'DESCONHECIDO', 'error_message': str(e)[:150]} for i in ids}


# =========================================================================================
# EXECUÇÃO
# =========================================================================================
if __name__ == '__main__':
    os.makedirs(PASTA, exist_ok=True)
    T0 = time.time()
    log(f'🔎 K16: identidade do envio por e-mail com o painel | {AGORA:%Y-%m-%d %H:%M} (BRT)')
    log(f'   rotina sab_pedido.py {sp.VERSAO_ROTINA} | SHA-256 {SHA_ROTINA}')
    log(f'   painel de referência: {sp.VERSAO_PAINEL}')
    log(f'   [v3] painel que gera os CSV de comparação: {VERSAO_PAINEL_JS} | SHA-256 {SHA_PAINEL}')
    try:
        ee.Initialize(project=PROJETO)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJETO)
    from google.colab import drive
    drive.mount('/content/drive')
    os.makedirs(os.path.join(DRIVE, PASTA_PROGRESSO), exist_ok=True)
    ARQ_PROG = os.path.join(DRIVE, PASTA_PROGRESSO, 'K16_progresso.json')
    prog = json.load(open(ARQ_PROG, encoding='utf-8')) if os.path.exists(ARQ_PROG) else {}
    carimbo = prog.setdefault('carimbo', f'{AGORA:%Y%m%d_%H%M}')
    prog.setdefault('tarefas', {})

    def salvar():
        with open(ARQ_PROG, 'w', encoding='utf-8') as f:
            json.dump(prog, f, ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- A e B: exportações pela rotina
    log('\nA/B) Pedidos montados pela rotina do e-mail e exportados para a pasta ' + PASTA_DRIVE)
    hoje = datetime.now(timezone(timedelta(hours=-3))).date()
    planos = {}
    for caso, codigo in CASOS:
        ped = sp.validar(sp.ler_codigo(codigo), hoje)
        try:
            ctx = sp.avaliar_pedido(ped)          # o mesmo caminho do GitHub (com o filtro ENSO, se houver)
            sufixo = ('_' + ped['enso']['arquivo']) if ped.get('enso') else ''
            arquivos = sp.planejar(ped['res'], ctx['locais'], ctx['dias'], sufixo=sufixo)
            sp.conferir_limites(ctx['n_pares'], ctx['locais'], arquivos)
        except sp.PedidoInvalido as e:
            log(f'   ❌ {caso}: a rotina recusou o pedido: {e}')
            planos[caso] = []
            continue
        colunas = sp.colunas_do_pedido(ped['res'], ped['variaveis'])          # [v2] sempre com as 6 colunas ENSO
        planos[caso] = [a['nome'] for a in arquivos]
        log(f"   {caso}: {sp.texto_local(ped)} | {', '.join(f'{n}: {k} pontos' for n, k in ctx['locais'])} | "
            f"{len(arquivos)} arquivo(s): {', '.join(planos[caso])}" + (f" | {ctx['avisos']}" if ctx['avisos'] else ''))
        itens = [(a['nome'], lambda a=a: sp.fc_do_arquivo(ped, a, ctx['por_local'][a['local']][0],
                                                          ctx['por_local'][a['local']][1], ctx['escala'], ctx['enso']),
                  colunas) for a in arquivos]
        if caso == 'A1':
            itens.append(('00_Dicionario_Variaveis_SAB', sp.dicionario_ee, ['Variavel', 'Descricao', 'Unidade']))
        for nome, fc_fn, cols in itens:
            chave = f'{caso}__{nome}'
            if chave in prog['tarefas']:
                continue
            prefixo = f'K16_{carimbo}_{chave}'
            t = ee.batch.Export.table.toDrive(collection=fc_fn(), description=f'K16_{chave}'[:100], folder=PASTA_DRIVE,
                                              fileNamePrefix=prefixo, fileFormat='CSV', selectors=cols)
            t.start()
            prog['tarefas'][chave] = {'id': t.id, 'prefixo': prefixo, 'caso': caso, 'nome': nome}
            salvar()
            log(f'      🚀 {nome}: tarefa {t.id}')

    # ---------------------------------------------------------------- E1: colunas ENSO da previsão (v2)
    fim_e1 = str(hoje + timedelta(days=15))
    ped_e1 = sp.validar(sp.ler_codigo(CASO_E1.replace('<FIM>', fim_e1)), hoje)
    ctx_e1 = sp.avaliar_pedido(ped_e1)
    arq_e1 = sp.planejar('D', ctx_e1['locais'], ctx_e1['dias'])
    log(f"\nE1) Pato Branco, 01/09/2026 a {fim_e1}: {len(arq_e1)} arquivo(s), {sum(a['linhas'] for a in arq_e1)} linhas")
    for a in arq_e1:
        chave = f"E1__{a['nome']}"
        if chave in prog['tarefas']:
            continue
        prefixo = f'K16_{carimbo}_{chave}'
        t = ee.batch.Export.table.toDrive(collection=sp.fc_do_arquivo(ped_e1, a, ctx_e1['por_local'][a['local']][0],
                                                                      ctx_e1['por_local'][a['local']][1], ctx_e1['escala'],
                                                                      ctx_e1['enso']),
                                          description=f'K16_{chave}'[:100], folder=PASTA_DRIVE, fileNamePrefix=prefixo,
                                          fileFormat='CSV', selectors=sp.colunas_do_pedido('D', ped_e1['variaveis']))
        t.start()
        prog['tarefas'][chave] = {'id': t.id, 'prefixo': prefixo, 'caso': 'E1', 'nome': a['nome']}
        salvar()
        log(f"      🚀 {a['nome']}: tarefa {t.id}")

    # ---------------------------------------------------------------- P: CSV do painel pelo próprio painel (v3)
    log('\nP) CSV do painel, gerados pelo próprio painel (Node.js + Earth Engine), em MeuDrive/K16_painel/<caso>/')
    if GERAR_PAINEL:
        try:
            gerar_csv_painel(DRIVE, planos)
        except Exception as e:
            log(f'   ❌ não foi possível gerar os CSV do painel aqui: {str(e)[:300]}')
            log('      Os casos sem CSV ficam "não conferidos". Alternativa: baixe-os à mão no painel (casos no topo).')
    else:
        log('   GERAR_PAINEL = False: usa só os CSV que você pôs à mão')

    # ---------------------------------------------------------------- C: link na hora, 19 x 3 variáveis
    log('\nC) Link na hora do Paraná, 01/01 a 31/03/2025: 19 variáveis x 3 (pr, tmax, tmin), alternados')
    prog.setdefault('links', {'19': [], '3': []})
    fc_c = {}
    if not RODAR_PARTE_C:
        log('   RODAR_PARTE_C = False: não medido nesta versão (a regra da radiação não muda o tempo do link; v6: o '
            'limite é o mesmo para qualquer escolha)')
    for k, codigo in (CODIGO_C.items() if RODAR_PARTE_C else ()):
        ped = sp.validar(sp.ler_codigo(codigo), hoje)
        ctx = sp.avaliar_pedido(ped)
        arq = sp.planejar(ped['res'], ctx['locais'], ctx['dias'])[0]
        grade, geom = ctx['por_local'][arq['local']]
        fc_c[k] = (sp.fc_do_arquivo(ped, arq, grade, geom, ctx['escala']),
                   sp.colunas_do_pedido('D', ped['variaveis'], enso=False), arq['linhas'])
    for rodada in (range(2) if RODAR_PARTE_C else ()):
        for k in ('19', '3'):
            if len(prog['links'][k]) > rodada:
                continue
            fc, cols, esperado = fc_c[k]
            t1 = time.time()
            seg = None
            try:
                url = fc.getDownloadURL(filetype='csv', selectors=cols, filename=f'K16_C_{k}_{rodada}')
                r = requests.get(url, timeout=TIMEOUT_LINK_S)
                n = len(r.text.splitlines()) - 1 if r.status_code == 200 else -1
                if r.status_code == 200 and n == esperado:
                    seg = round(time.time() - t1, 1)
                    log(f'   ✅ {k} variáveis, rodada {rodada + 1}: {seg} s, {n} linhas, {len(r.content) / 1e6:.1f} MB')
                else:
                    log(f'   ❌ {k} variáveis, rodada {rodada + 1}: HTTP {r.status_code}, {n} de {esperado} linhas '
                        f'{r.text[:120] if r.status_code != 200 else ""}')
            except Exception as e:
                log(f'   ❌ {k} variáveis, rodada {rodada + 1}: {str(e)[:150]}')
            prog['links'][k].append(seg)
            salvar()

    # ---------------------------------------------------------------- acompanhamento das exportações
    log(f'\n   Acompanhando as exportações a cada {INTERVALO_S} s (até {ESPERA_MAX_H} h)')
    ids = {c: v['id'] for c, v in prog['tarefas'].items()}
    limite = time.time() + ESPERA_MAX_H * 3600
    while True:
        st = status_de(list(ids.values()))
        if all(st.get(i, {}).get('state') in TERMINAIS for i in ids.values()) or time.time() > limite:
            break
        time.sleep(INTERVALO_S)
    for c, i in ids.items():
        e = st.get(i, {}).get('state', '?')
        if e not in ('COMPLETED', 'SUCCEEDED'):
            log(f"   ❌ {c}: {e} {st.get(i, {}).get('error_message', '')}")

    def arquivo_exportado(chave):
        v = prog['tarefas'][chave]
        nome = v['prefixo'] + '.csv'          # o prefixo tem o carimbo desta rodada: não confunde com outro arquivo

        def achar():
            alvo = os.path.join(DRIVE, PASTA_DRIVE, nome)
            if os.path.exists(alvo):
                return alvo
            # [v7.1] o Drive pode criar duas pastas com o mesmo nome (exportações simultâneas para uma pasta nova)
            outros = sorted(glob.glob(os.path.join(DRIVE, '*', nome)))
            if outros:
                log(f'   (achado em outra pasta do Drive: {os.path.relpath(outros[0], DRIVE)})')
            return outros[0] if outros else None
        t_esp = time.time() + ESPERA_ARQUIVO_S
        achado = achar()
        while achado is None and time.time() < t_esp:
            time.sleep(20)
            achado = achar()
        return achado

    # ---------------------------------------------------------------- comparação com o painel
    log('\nComparação com os CSV do painel (MeuDrive/K16_painel/<caso>/)')
    linhas, identidade = [], {}
    for caso, _ in CASOS:
        pasta_painel = os.path.join(DRIVE, PASTA_PAINEL, 'A1' if caso in ('B1', 'B2') else caso)
        painel = sorted(os.path.basename(x)[:-4] for x in glob.glob(os.path.join(pasta_painel, '*.csv'))
                        if not os.path.basename(x).startswith('00_'))
        if not painel:
            log(f'   ⚠️ {caso}: sem CSV do painel em {pasta_painel}: caso NÃO conferido')
            identidade[caso] = None
            linhas.append({'caso': caso, 'arquivo': '', 'igual': None, 'detalhe': 'sem CSV do painel'})
            continue
        ok_caso = True
        if caso not in ('B1', 'B2') and sorted(planos[caso]) != painel:
            ok_caso = False
            log(f'   ❌ {caso}: nomes diferentes. rotina {sorted(planos[caso])} x painel {painel}')
        for nome in planos[caso]:
            exp = arquivo_exportado(f'{caso}__{nome}')
            ref = os.path.join(pasta_painel, nome + '.csv')
            if not exp or not os.path.exists(ref):
                igual, det = False, 'arquivo da rotina não apareceu' if not exp else 'painel sem este arquivo'
            else:
                a, b = ler_csv(exp), ler_csv(ref)
                if caso in ('B1', 'B2'):   # B1 (3 variáveis) e B2 (1): as colunas do painel A1 que existem nele, na ordem do A1
                    b = b[[c for c in b.columns if c in set(a.columns)]]
                igual, det = comparar_painel(a, b, extras_esperadas(list(b.columns)))
            ok_caso = ok_caso and igual
            log(f"   {'✅' if igual else '❌'} {caso} {nome}: {det}")
            linhas.append({'caso': caso, 'arquivo': nome, 'igual': igual, 'detalhe': det})
        if caso == 'A1':
            exp = arquivo_exportado('A1__00_Dicionario_Variaveis_SAB')
            ref = os.path.join(pasta_painel, '00_Dicionario_Variaveis_SAB.csv')
            if exp and os.path.exists(ref):
                igual, det = comparar_dicionario(ler_csv(exp), ler_csv(ref))
            else:      # [v7.1] diz qual dos dois falta
                igual, det = False, ('dicionário da rotina não apareceu no Drive' if not exp else '') + \
                    (' e ' if not exp and not os.path.exists(ref) else '') + \
                    ('dicionário do painel ausente em ' + ref if not os.path.exists(ref) else '')
            ok_caso = ok_caso and igual
            log(f"   {'✅' if igual else '❌'} A1 dicionário: {det}")
            linhas.append({'caso': 'A1', 'arquivo': '00_Dicionario_Variaveis_SAB', 'igual': igual, 'detalhe': det})
        identidade[caso] = ok_caso

    e1 = [k for k in prog['tarefas'] if k.startswith('E1__')]
    dfs = [ler_csv(x) for x in (arquivo_exportado(k) for k in e1) if x]
    if len(dfs) == len(e1) and dfs:
        igual, det = conferir_e1(pd.concat(dfs, ignore_index=True))
    else:
        igual, det = False, 'arquivo do E1 não apareceu'
    identidade['E1'] = igual

    log(f"   {'✅' if igual else '❌'} E1 colunas ENSO na previsão: {det}")
    linhas.append({'caso': 'E1', 'arquivo': ', '.join(e1), 'igual': igual, 'detalhe': det})

    # [v7] R7: a radiação impossível sai vazia na planilha do e-mail do A7 (o painel tem de ser igual: caso A7)
    r7 = [k for k in prog['tarefas'] if k.startswith('A7__')]
    dfs = [ler_csv(x) for x in (arquivo_exportado(k) for k in r7) if x]
    if len(dfs) == len(r7) and dfs:
        igual, det = conferir_r7(pd.concat(dfs, ignore_index=True))
    else:
        igual, det = False, 'arquivo do A7 não apareceu'
    identidade['R7'] = igual
    log(f"   {'✅' if igual else '❌'} R7 radiação impossível vazia (A7, Lagoa Mirim, 03/2026): {det}")
    linhas.append({'caso': 'R7', 'arquivo': ', '.join(r7), 'igual': igual, 'detalhe': det})

    if PASTA_PEDIDO:
        log(f'\nD) Pasta do pedido feito pelo GitHub: {PASTA_PEDIDO} x painel A1')
        for nome in planos['A1']:
            exp = os.path.join(DRIVE, PASTA_PEDIDO, nome + '.csv')
            ref = os.path.join(DRIVE, PASTA_PAINEL, 'A1', nome + '.csv')
            if os.path.exists(exp) and os.path.exists(ref):
                b = ler_csv(ref)
                igual, det = comparar_painel(ler_csv(exp), b, extras_esperadas(list(b.columns)))
            else:
                igual, det = False, 'arquivo ausente na pasta do pedido ou no painel'
            identidade['D'] = identidade.get('D', True) and igual
            log(f"   {'✅' if igual else '❌'} D {nome}: {det}")
            linhas.append({'caso': 'D', 'arquivo': nome, 'igual': igual, 'detalhe': det})

    pd.DataFrame(linhas).to_csv(os.path.join(PASTA, 'K16_resultados.csv'), index=False, encoding='utf-8-sig')
    d = decidir_k16(identidade, prog['links'])
    log('\n' + '=' * 100)
    log('RESULTADO FINAL K16')
    log('=' * 100)
    if d['aprovado']:
        log('   ✅ IDENTIDADE APROVADA: a rotina do e-mail gera os mesmos arquivos do painel (nomes e células das colunas '
            'do painel) e as colunas ENSO da previsão estão completas (E1).')
        log('      ➜ Pode seguir para o teste de ponta a ponta (formulário -> GitHub -> e-mail).')
    else:
        log('   ❌ IDENTIDADE NÃO APROVADA: ' + ', '.join(f'{c}={v}' for c, v in identidade.items()) +
            '. NÃO ligue o envio por e-mail; me envie o zip.')
    log(f"   Links (s): 19 variáveis {prog['links']['19']} | 3 variáveis {prog['links']['3']} | razões {d['razoes']}")
    if not RODAR_PARTE_C:
        log('   ➖ Parte C não rodada nesta versão (RODAR_PARTE_C = False); vale a medida da v6.')
    else:
        log('   ' + ('✅ Menos variáveis ACELERAM o link (≤ 70% do tempo nos 2 pares): o limite do link pode crescer '
                     'com menos variáveis.' if d['acelera'] else
                     '➖ Menos variáveis NÃO aceleram o link o suficiente: o limite do link é o mesmo para qualquer '
                     'escolha (a escolha ainda deixa o arquivo menor).'))
    log(f'\nTempo desta execução: {(time.time() - T0) / 60:.0f} min. Nada foi gravado no Earth Engine.')
    log(f'Os CSV estão em {PASTA_DRIVE} e {PASTA_PAINEL} no seu Drive; pode apagá-las depois de me enviar o zip.')
    z = shutil.make_archive(PASTA, 'zip', PASTA)
    log(f'📦 {z}')
    try:
        from google.colab import files
        files.download(z)
    except Exception:
        log('   (baixe pelo painel Arquivos do Colab)')
