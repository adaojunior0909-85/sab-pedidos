# -*- coding: utf-8 -*-
"""[V4] Testes offline (Python puro, sem Earth Engine) do 03_matriz_gfs_v2_1.py.

As funções e constantes puras são lidas do PRÓPRIO 03 com ast (não há cópia do código aqui):
horas_da_faixa, horas_chuva, inicio_dia_previsto, maximos_por_mes, abaixo_do_limiar,
decisao_mes, FAIXAS, N_ESPERADO, nomes de banda e o dicionário de propriedades.
Também confere a coerência com o motor (contagem_esperada, faixa_prazo e nomes de banda),
lendo o 05a sem executá-lo, e compara os máximos com testes/maximos_pares_v16.py.

Uso: python3 teste_03.py
"""
import ast
import glob
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.dirname(AQUI)
ARQ_03 = os.path.join(V4, '03_matriz_gfs_v2_1.py')

FALHAS = []
N_OK = 0


def confere(cond, msg):
    global N_OK
    if cond:
        N_OK += 1
    else:
        FALHAS.append(msg)
        print('   FALHOU:', msg)


def extrair(arquivo, nomes, extra_ns=None):
    """Executa, na ordem do arquivo, só as definições (def/atribuições) com os nomes pedidos."""
    with open(arquivo, encoding='utf-8') as f:
        arvore = ast.parse(f.read(), filename=arquivo)
    ns = {'date': date, 'datetime': datetime, 'timedelta': timedelta, 'timezone': timezone, 'math': math}
    ns.update(extra_ns or {})
    achados = set()
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef) and no.name in nomes:
            alvo = no.name
        elif isinstance(no, ast.Assign) and len(no.targets) == 1 and isinstance(no.targets[0], ast.Name) \
                and no.targets[0].id in nomes:
            alvo = no.targets[0].id
        else:
            continue
        exec(compile(ast.Module(body=[no], type_ignores=[]), arquivo, 'exec'), ns)
        achados.add(alvo)
    faltam = set(nomes) - achados
    return ns, faltam, arvore


def ms(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)


# ---------------------------------------------------------------------------------------------
print('== 0. Leitura do 03 ==')
NOMES_03 = ['VERSAO_MATRIZ', 'MODELO_GFS', 'INICIO_RODADAS', 'FIM_DIAS', 'DATA_FIM', 'FAIXAS',
            'LIMIAR_ALERTA', 'ESTADOS_ATIVOS', 'VARS', 'horas_da_faixa', 'horas_chuva',
            'inicio_dia_previsto', 'maximos_por_mes', 'abaixo_do_limiar', 'decisao_mes',
            'N_ESPERADO', 'BANDAS_DIA', 'NOMES_MEDIA', 'NOMES_DP', 'NOMES_N']
g, faltam, arvore_03 = extrair(ARQ_03, NOMES_03)
confere(not faltam, f'definições ausentes no 03: {sorted(faltam)}')
FAIXAS = g['FAIXAS']
FX = [fx for fx, _ in FAIXAS]
print('   FAIXAS =', FAIXAS)

# ---------------------------------------------------------------------------------------------
print('== 1. Período v16 e faixas ==')
confere(g['INICIO_RODADAS'] == '2021-03-23', 'INICIO_RODADAS deve ser 2021-03-23')
confere(g['FIM_DIAS'] == '2025-12-31', 'FIM_DIAS deve ser 2025-12-31')
confere(g['DATA_FIM'] == '2026-01-01', 'DATA_FIM (exclusivo) deve ser 2026-01-01')
confere(g['VERSAO_MATRIZ'] == 'V2.1' and g['MODELO_GFS'] == 'GFS v16', 'versão/modelo')
confere(FAIXAS == [('L1', [1]), ('L2a5', [2, 3, 4, 5]), ('L6a10', [6, 7, 8, 9, 10]),
                   ('L11a15', [11, 12, 13, 14, 15])], 'faixas do contrato (todos os dias)')
todos = [L for _, p in FAIXAS for L in p]
confere(todos == list(range(1, 16)), 'prazos 1..15, cada um em uma só faixa')

# ---------------------------------------------------------------------------------------------
print('== 2. Data da rodada por prazo (rodada 00Z de D-(L-1); corte pela criação) ==')
ini = date(2021, 3, 23)
for L in range(1, 16):
    esperado = (ini + timedelta(days=L - 1)).isoformat()
    confere(g['inicio_dia_previsto'](L) == esperado, f'inicio_dia_previsto({L}) = {esperado}')
    d0 = date.fromisoformat(g['inicio_dia_previsto'](L))
    confere(d0 - timedelta(days=L - 1) == ini, f'prazo {L}: 1º dia previsto usa a rodada de 2021-03-23')
    # mesma conta do 03 (servidor): criacao = data_ms - (L-1)*86400000
    for D in (d0, date(2023, 7, 15), date(2025, 12, 31)):
        criacao = ms(D) - (L - 1) * 86400000
        confere(criacao == ms(D - timedelta(days=L - 1)), f'criacao em ms, L={L}, D={D}')
        confere(criacao % 86400000 == 0, f'rodada 00Z, L={L}, D={D}')
        confere(criacao >= ms(ini), f'rodada >= 2021-03-23 para D >= inicio_dia_previsto, L={L}')
    # o dia anterior ao 1º dia previsto usaria uma rodada de 22/03/2021 (antes do v16): fica de fora
    confere(ms(d0 - timedelta(days=1)) - (L - 1) * 86400000 < ms(ini), f'dia anterior excluído, L={L}')
confere(g['inicio_dia_previsto'](15) == '2021-04-06', 'prazo 15 começa em 2021-04-06')

# ---------------------------------------------------------------------------------------------
print('== 3. Horas esperadas e blocos de chuva ==')
NE = g['N_ESPERADO']
confere(sorted(NE) == list(range(1, 16)), 'N_ESPERADO cobre os prazos 1..15')
for L in range(1, 16):
    h = g['horas_da_faixa'](L)
    h0 = 24 * (L - 1)
    confere(all(h0 < x <= h0 + 24 for x in h), f'horas do prazo {L} dentro de (24(L-1), 24L]')
    confere(NE[L] == (24 if L <= 5 else 8), f'prazo {L}: {NE[L]} horas esperadas')
    confere(all(x % 3 == 0 for x in h if x > 120), f'prazo {L}: de 3 em 3 h depois de 120 h')
    hc = g['horas_chuva'](L)
    confere(hc == [h0 + 6, h0 + 12, h0 + 18, h0 + 24], f'blocos de chuva do prazo {L}')
    confere(hc == [x for x in h if x % 6 == 0], f'blocos de chuva = horas múltiplas de 6 do prazo {L}')
    confere(set(hc) <= set(h), f'blocos de chuva entre as horas esperadas, prazo {L}')
# Estrutura v16 (F2: 209 imagens = f000 + 120 horárias + 88 de 3 em 3 h até 384 h)
v16 = [0] + list(range(1, 121)) + list(range(123, 385, 3))
confere(len(v16) == 209, 'rodada v16 com 209 imagens')
confere(sum(NE.values()) + 8 == 208, 'prazos 1..15 + 16º dia (8) = 208 saídas sem o f000')


def completa(horas_rodada, L):
    """Regra do 03 no servidor: size() == N_ESPERADO[L] e os 4 blocos de chuva presentes."""
    h0 = 24 * (L - 1)
    janela = [x for x in horas_rodada if h0 < x <= h0 + 24]
    chuva = [x for x in janela if x in g['horas_chuva'](L)]
    return len(janela) == NE[L] and len(chuva) == 4


for L in range(1, 16):
    confere(completa(v16, L), f'rodada v16 completa no prazo {L}')
    falta = [x for x in v16 if x != 24 * L]          # sem a última hora do dia (bloco de chuva)
    confere(not completa(falta, L), f'sem a hora {24 * L}: prazo {L} incompleto')
    falta2 = [x for x in v16 if x != 24 * (L - 1) + 3]   # sem uma hora que não é bloco de chuva
    confere(not completa(falta2, L), f'sem a hora {24 * (L - 1) + 3}: prazo {L} incompleto')
    dup = v16 + [24 * L]                              # imagem duplicada: size() != N_ESPERADO
    confere(not completa(dup, L), f'imagem duplicada: prazo {L} descartado')
# rodada antiga (antes de 13/06/2019): de 12 em 12 h depois de 240 h -> prazos 11+ incompletos
antiga = [0] + list(range(1, 121)) + list(range(123, 241, 3)) + list(range(252, 385, 12))
confere(completa(antiga, 10) and not completa(antiga, 11), 'estrutura antiga reprova a partir do prazo 11')

# ---------------------------------------------------------------------------------------------
print('== 4. Coerência com o motor (05a, só leitura) ==')
motores = sorted(glob.glob(os.path.join(V4, '05a_motor_sab_v1_*_SIMULACAO.py')))
if not motores:
    print('   PULADO: 05a não encontrado em', V4)
else:
    arq_motor = motores[-1]
    print('   motor:', os.path.basename(arq_motor))
    obrigatorias = ['contagem_esperada', 'FAIXAS_GFS', 'faixa_prazo']
    opcionais = ['MS_DIA', 'prazo_L', 'VERSAO_MATRIZ_GFS', 'VARS_MATRIZ_GFS', 'BANDAS_MEDIA_GFS']
    try:
        gm, faltam_m, _ = extrair(arq_motor, obrigatorias + opcionais)
        faltam_m = faltam_m & set(obrigatorias)
    except SyntaxError as e:
        gm, faltam_m = None, {'(erro de sintaxe)'}
        print('   PULADO: o motor não compila agora (edição em andamento?):', e)
    if gm is not None:
        confere(not faltam_m, f'funções do motor ausentes: {sorted(faltam_m)}')
        if 'VERSAO_MATRIZ_GFS' in gm:
            confere(gm['VERSAO_MATRIZ_GFS'] == g['VERSAO_MATRIZ'], 'motor exige a mesma versao_matriz que o 03 grava')
        if 'BANDAS_MEDIA_GFS' in gm:
            confere(list(gm['BANDAS_MEDIA_GFS']) == g['NOMES_MEDIA'], 'motor: BANDAS_MEDIA_GFS = 48 médias do 03, na mesma ordem')
    if gm is not None and not faltam_m:
        fx_de = {L: fx for fx, p in FAIXAS for L in p}
        for L in range(1, 16):
            for c in (date(2021, 3, 23), date(2024, 2, 20), date(2025, 12, 17)):
                dia = c + timedelta(days=L - 1)
                n, hc = gm['contagem_esperada'](ms(dia), ms(c))
                confere(n == NE[L], f'motor: {n} horas esperadas no prazo {L} (03: {NE[L]})')
                confere([float(x) for x in g['horas_chuva'](L)] == hc, f'motor: blocos de chuva do prazo {L}')
                confere(gm['faixa_prazo'](ms(dia), ms(c)) == fx_de[L], f'motor: faixa do prazo {L} = {fx_de[L]}')
        confere(tuple(gm['FAIXAS_GFS']) == tuple(FX), 'motor: FAIXAS_GFS igual às faixas do 03')
        # 16º dia: o motor usa a faixa L11a15 (extrapolação documentada no 03)
        c = date(2025, 1, 1)
        confere(gm['faixa_prazo'](ms(c + timedelta(days=15)), ms(c)) == 'L11a15', 'motor: 16º dia usa L11a15')
        # Bandas que o motor seleciona: {var}_m_sicsb_{faixa} e {var}_m_gfs_{faixa}
        for fx in gm['FAIXAS_GFS']:
            for v in g['VARS']:
                for b in (f'{v}_m_sicsb_{fx}', f'{v}_m_gfs_{fx}'):
                    confere(b in g['NOMES_MEDIA'], f'banda do motor ausente na matriz: {b}')

# ---------------------------------------------------------------------------------------------
print('== 5. Nomes e ordem das 100 bandas ==')
NM, ND, NN = g['NOMES_MEDIA'], g['NOMES_DP'], g['NOMES_N']
confere(len(NM) == 48 and len(ND) == 48 and len(NN) == 4, 'quantidade de bandas 48 + 48 + 4')
confere(len(set(NM + ND + NN)) == 100, '100 nomes distintos')
confere(NN == ['n_L1', 'n_L2a5', 'n_L6a10', 'n_L11a15'], 'bandas n_ do contrato')
# Concatenação por faixa (como em gerar_matriz_gfs_mes) reproduz a ordem da V2
med, dp = [], []
for fx in FX:
    bandas = [f'{v}__{fonte}_{fx}' for fonte in ('sicsb', 'gfs') for v in g['VARS']]
    med += [b.replace('__', '_m_') for b in bandas]
    dp += [b.replace('__', '_s_') for b in bandas]
    confere(f'Tmax__gfs_{fx}' in bandas, f'banda usada na contagem existe na faixa {fx}')
confere(med == NM, 'ordem das médias igual à da V2 (faixa, fonte, variável)')
confere(dp == ND, 'ordem dos desvios igual à da V2')
ordem_v2 = [f'{v}_{t}_{fonte}_{fx}' for t in ('m', 's') for fx in FX for fonte in ('sicsb', 'gfs') for v in g['VARS']]
confere(NM + ND == ordem_v2, 'as 96 bandas na mesma ordem da V2; n_ no fim')

# ---------------------------------------------------------------------------------------------
print('== 6. Propriedades do contrato ==')
func = [n for n in arvore_03.body if isinstance(n, ast.FunctionDef) and n.name == 'gerar_matriz_gfs_mes']
confere(len(func) == 1, 'gerar_matriz_gfs_mes encontrada')
if func:
    stmts = [s for s in func[0].body
             if (isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name) and s.targets[0].id == 'props')
             or (isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
                 and isinstance(s.value.func, ast.Attribute) and s.value.func.attr == 'update'
                 and isinstance(s.value.func.value, ast.Name) and s.value.func.value.id == 'props')]
    ns = dict(g)
    ns.update({'mes': 7, 'n_pares': {fx: f'<servidor {fx}>' for fx in FX}, 'GERADO_EM': '2026-10-20T00:00:00Z'})
    exec(compile(ast.Module(body=stmts, type_ignores=[]), ARQ_03, 'exec'), ns)
    props = ns['props']
    contrato = {
        'versao_matriz': 'V2.1', 'modelo_gfs': 'GFS v16', 'inicio_rodadas': '2021-03-23',
        'fim_dias': '2025-12-31', 'mes_referencia': 7,
        'leads_L1': '1', 'leads_L2a5': '2,3,4,5', 'leads_L6a10': '6,7,8,9,10', 'leads_L11a15': '11,12,13,14,15',
        'metodo_pr': 'soma_blocos_6h', 'metodo_rs': 'media_blocos_6h',
        'janela': '(00Z,24Z] UTC do dia previsto; rodada 00Z de D-(L-1)',
        'gerado_em': '2026-10-20T00:00:00Z',
    }
    for k, v in contrato.items():
        confere(props.get(k) == v, f'propriedade {k} = {v!r} (03: {props.get(k)!r})')
    for fx in FX:
        confere(props.get(f'n_pares_{fx}') == f'<servidor {fx}>', f'n_pares_{fx} vem do servidor')
    confere(isinstance(props['mes_referencia'], int), 'mes_referencia é int')
    print('   propriedades:', sorted(props))
# GERADO_EM em ISO (UTC)
with open(ARQ_03, encoding='utf-8') as f:
    fonte_03 = f.read()
confere("GERADO_EM = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')" in fonte_03, 'gerado_em ISO UTC')
confere("pares.aggregate_sum('valido')" in fonte_03 and '.getInfo()' not in fonte_03.split('def gerar_matriz_gfs_mes')[1].split('# 3. DISPARADOR')[0],
        'n_pares calculado no servidor, sem getInfo dentro de gerar_matriz_gfs_mes')
confere("sharedInputs=True" in fonte_03 and 'ee.Reducer.count()' in fonte_03, 'redutor combinado mean + stdDev + count')
confere('region=poligonoBrasil.bounds()' in fonte_03, 'exportação pelo retângulo do Brasil')
# [V4 revisão] composto_seguro (M03-11) e bandas n_ em Float32
confere(fonte_03.count('composto_seguro(') == 7, 'composto_seguro: 6 composições + a definição')
confere('n = n.updateMask(n.gt(0)).toFloat()' in fonte_03 and 'toInt16' not in fonte_03.split('def gerar_matriz_gfs_mes')[1],
        'bandas n_ em Float32')
confere("updateMask(ee.Image.constant(0))" in fonte_03.split('def composto_seguro')[1][:600], 'composto_seguro usa imagem totalmente mascarada')
confere("description=f'GERAR_MATRIZ_GFS_V2_{str_mes}'" in fonte_03, 'descrição das tarefas mantida')
for msg in ('Mês {str_mes}: dias válidos por faixa', '✔️ Tarefa enviada: matriz GFS V2, mês {str_mes}.', '🎉 Tarefas enviadas'):
    confere(msg in fonte_03, f'mensagem do roteiro presente: {msg}')
confere('except Exception:\n    pass' not in fonte_03, 'nenhuma exceção engolida com pass')

# ---------------------------------------------------------------------------------------------
print('== 7. Máximos de pares por mês e faixa ==')
maximos = g['maximos_por_mes']()
sys.path.insert(0, AQUI)
import maximos_pares_v16 as mp  # noqa: E402  (conferência independente: enumera rodadas)
ref = mp.maximos_por_rodada()
confere(maximos == ref, 'maximos_por_mes() do 03 = enumeração por rodadas (maximos_pares_v16.py)')
confere(sum(maximos[m]['L1'] for m in maximos) == 1745, 'L1: 1745 dias de 2021-03-23 a 2025-12-31')
confere(maximos[1] == {'L1': 124, 'L2a5': 496, 'L6a10': 620, 'L11a15': 620}, 'janeiro: 4 anos (2022-2025)')
confere(maximos[2]['L1'] == 28 + 28 + 29 + 28, 'fevereiro com 2024 bissexto')
confere(maximos[3] == {'L1': 9 + 124, 'L2a5': (8 + 7 + 6 + 5) + 496, 'L6a10': (4 + 3 + 2 + 1) + 620, 'L11a15': 620},
        'março: deslocamento por prazo em 2021')
confere(maximos[4]['L11a15'] == (29 + 28 + 27 + 26 + 25) + 600, 'abril L11a15: prazo 15 só a partir de 06/04/2021')
confere(all(maximos[m][fx] > 0 for m in maximos for fx in FX), 'todos os máximos > 0 (sem divisão por zero)')

# ---------------------------------------------------------------------------------------------
print('== 8. Alerta de 85% ==')
ab = g['abaixo_do_limiar']
confere(g['LIMIAR_ALERTA'] == 0.85, 'limiar 85%')
confere(not ab(124, 124) and not ab(106, 124) and ab(105, 124), 'limiar em janeiro L1 (106 é o mínimo sem ⚠️)')
confere(not ab(527, 620) and ab(526, 620), 'limiar em janeiro L6a10')
confere(not ab(0, 0), 'máximo 0 não gera alerta')
for m in maximos:
    for fx in FX:
        confere(mp.minimo_aceitavel(maximos[m][fx]) == min(k for k in range(maximos[m][fx] + 1) if not ab(k, maximos[m][fx])),
                f'mínimo sem ⚠️ da tabela = regra do 03 ({m}, {fx})')

# ---------------------------------------------------------------------------------------------
print('== 9. Reexecução segura ==')
dm = g['decisao_mes']
confere(dm(None, False) == 'enviar', 'sem asset e sem tarefa: envia')
confere(dm(None, True) == 'tarefa_ativa', 'tarefa na fila: pula')
confere(dm('V2.1', False) == 'pular' and dm('V2.1', True) == 'pular', 'asset V2.1: pula')
confere(dm('', False) == 'conflito', 'asset sem versão: para com ❌')
confere(dm('V2', False) == 'conflito' and dm('V2.0', True) == 'conflito', 'asset de outra versão: para com ❌')
confere(set(('READY', 'RUNNING')) <= set(g['ESTADOS_ATIVOS']), 'READY e RUNNING contam como tarefa ativa')

# ---------------------------------------------------------------------------------------------
print()
if FALHAS:
    print(f'❌ {len(FALHAS)} falha(s) em {N_OK + len(FALHAS)} verificações.')
    sys.exit(1)
print(f'✅ teste_03: {N_OK} verificações OK.')
