# -*- coding: utf-8 -*-
"""Testes offline (Python puro, sem Earth Engine) da lógica nova do motor SAB V1.5 (05a/05b).

As funções e constantes são extraídas do PRÓPRIO 05a com ast (nada é copiado à mão), então o teste
falha se o código do motor mudar de comportamento. Rodar:  python3 testes/teste_05.py
"""
import ast
import math
import os
import re
import sys
from datetime import datetime, timezone, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.dirname(AQUI)
ARQ_A = os.path.join(PASTA, '05a_motor_sab_v1_5_SIMULACAO.py')
ARQ_B = os.path.join(PASTA, '05b_motor_sab_v1_5_GRAVACAO.py')

CONSTANTES = {
    'MS_DIA', 'PRAZO_MAX_GFS', 'HORAS_RODADA_COMPLETA', 'N_SAIDAS_RODADA', 'HORIZONTE_DIAS',
    'VERSAO_ALGORITMO', 'VERSAO_PATCH', 'ALGORITMOS_DEFINITIVOS_VALIDOS', 'VERSOES_GFS',
    'DATA_LIMITE_PROTECAO', 'CONVERTER_EM_DEFINITIVO', 'REPROCESSAR_VERSAO_ANTIGA', 'APLICAR_PATCH_SOLO',
    'PROTEGER_HISTORICO', 'BANDAS_MASCARADAS_INCOMPLETO', 'FAIXAS_GFS', 'VARS_MATRIZ_GFS',
    'BANDAS_MEDIA_GFS', 'FONTE_GFS', 'FONTE_ERA5', 'FONTE_DEFINITIVA', 'JANELA_CHUVA_00_24',
    'JANELA_CHUVA_12_12', 'VERSAO_MATRIZ_GFS', 'MATRIZ_GFS_ROTULO', 'CRIT_SOLO_BRASIL', 'K_CHUVA_MM',
    'FATOR_MAX', 'FATOR_MIN_UV_RS', 'FATOR_MAX_UV_RS', 'TMAX_RECORDE_BR', 'SALTO_MAX_TMAX',
    'ARQUIVO_PREVIA', 'DIA_MASCARA_CANONICA', '_NOME_DIA', 'ORDEM_BANDAS', 'SIMULAR',
    'METODO_TEMP_GFS', 'RAZAO_DESVIO_MIN', 'RAZAO_DESVIO_MAX', 'BANDAS_DESVIO_TEMP',
    'METODO_UR_RS_GFS', 'BANDAS_DESVIO_UR_RS', 'RAZAO_DESVIO_MAX_LONGO', 'FAIXAS_LONGAS',
}
FUNCOES = {
    'ms_para_data', 'data_para_ms', 'somar_dias', 'id_dia', 'limite_definitivo', 'dias_aguardando_decisao',
    'eh_rodada_00z', 'selecionar_rodadas', 'prazo_L', 'faixa_prazo', 'confianca_prazo', 'fim_horizonte',
    'rodada_para_dia', 'precisa_refazer_gfs', 'contagem_esperada', 'status_dia', 'dias_previa_gfs',
    'versao_tmp_aceita', 'data_de_nome', 'dia_protegido', 'decisao_tmax',
    'expandir_borda', 'razao_desvios', 'calib_variancia', 'calib_aditiva',
    'fator_v10', 'calib_limitada_gfs', 'info_de_propriedades', 'intervalo_datas', 'ultimo_dia_continuo',
    'teto_razao_temp',
}


def carregar(caminho):
    """Executa só as constantes e funções puras listadas, na ordem do arquivo."""
    with open(caminho, encoding='utf-8') as f:
        fonte = f.read()
    arvore = ast.parse(fonte)
    nos = []
    for no in arvore.body:
        if isinstance(no, ast.Assign) and len(no.targets) == 1 and isinstance(no.targets[0], ast.Name) \
                and no.targets[0].id in CONSTANTES:
            nos.append(no)
        elif isinstance(no, ast.FunctionDef) and no.name in FUNCOES:
            nos.append(no)
        elif isinstance(no, ast.Assert):
            seg = ast.get_source_segment(fonte, no)
            if 'N_SAIDAS_RODADA' in seg or 'ALGORITMOS_DEFINITIVOS_VALIDOS' in seg or 'METODO_TEMP_GFS' in seg \
                    or 'METODO_UR_RS_GFS' in seg:
                nos.append(no)
    modulo = ast.Module(body=nos, type_ignores=[])
    import pandas as pd
    ns = {'math': math, 're': re, 'datetime': datetime, 'timezone': timezone, 'timedelta': timedelta, 'pd': pd,
          'crsNativo': 'EPSG:4326', 'transformNativo': [0.1, 0, 0, 0, -0.1, 0]}
    exec(compile(modulo, caminho, 'exec'), ns)
    faltam = (CONSTANTES | FUNCOES) - set(ns)
    assert not faltam, f"não encontrei no 05a: {sorted(faltam)}"
    return ns, fonte


M, FONTE = carregar(ARQ_A)
ms = M['data_para_ms']
H = 3600000
N_OK = 0


def ok(cond, msg):
    global N_OK
    if not cond:
        raise AssertionError(msg)
    N_OK += 1


def eq(obtido, esperado, msg):
    ok(obtido == esperado, f"{msg}: obtido {obtido!r}, esperado {esperado!r}")


def z(d, hora=0):
    """creation_time (ms) da rodada do dia d às 'hora' Z."""
    return ms(d) + hora * H


# ---------------------------------------------------------------- 1. horas de uma rodada completa
def teste_horas_rodada():
    horas = M['HORAS_RODADA_COMPLETA']
    eq(M['N_SAIDAS_RODADA'], 208, "rodada completa = 208 saídas")
    eq(len([h for h in horas if 1 <= h <= 120]), 120, "120 saídas horárias (1-120 h)")
    eq(len([h for h in horas if 120 < h <= 240]), 40, "40 saídas de 3 h até 240 h")
    eq(len([h for h in horas if 240 < h <= 384]), 48, "48 saídas de 3 h até 384 h")
    ok(0 not in horas, "a hora 0 não conta")
    ok(121 not in horas and 122 not in horas and 123 in horas, "depois de 120 h só múltiplos de 3")
    eq(max(horas), 384, "última saída = 384 h")
    eq(len(set(horas)), len(horas), "sem repetição")
    # [V4 A-02] inteiros no inList('forecast_hours', ...), como na auditoria J
    ok(all(type(h) is int for h in horas), "HORAS_RODADA_COMPLETA só com int (A-02)")
    fonte = open(ARQ_A, encoding='utf-8').read()
    ok('horas_chuva = [h for h in horas if h % 6 == 0]' in fonte, "horas de chuva filtradas como int (A-02)")


# ---------------------------------------------------------------- 2. horas e blocos por prazo L1..L16
def teste_contagem_por_prazo():
    rodada = z('2026-10-20')
    uniao = []
    for L in range(1, 17):
        dia = M['somar_dias']('2026-10-20', L - 1)
        n, blocos = M['contagem_esperada'](ms(dia), rodada)
        h0 = 24 * (L - 1)
        horas = [h for h in range(h0 + 1, h0 + 25) if h <= 120 or h % 3 == 0]
        uniao += horas
        esperado_n = 24 if L <= 5 else 8
        eq(n, esperado_n, f"L{L}: imagens esperadas")
        eq(blocos, [float(h0 + 6), float(h0 + 12), float(h0 + 18), float(h0 + 24)], f"L{L}: blocos de chuva")
        eq(M['prazo_L'](ms(dia), rodada), L, f"L{L}: prazo_L")
    eq(sorted(uniao), M['HORAS_RODADA_COMPLETA'], "L1..L16 somam exatamente as 208 saídas")
    # prazo 5 termina na hora 120 (horária); prazo 6 é o primeiro depois da troca de passo (121-144 h)
    n5, _ = M['contagem_esperada'](ms('2026-10-24'), rodada)
    n6, b6 = M['contagem_esperada'](ms('2026-10-25'), rodada)
    eq((n5, n6), (24, 8), "troca de passo em 120 h: L5 = 24 saídas, L6 = 8 (123, 126, ..., 144)")
    eq(b6, [126.0, 132.0, 138.0, 144.0], "L6: 4 blocos de 6 h")
    # além de 384 h não há nada
    n17, b17 = M['contagem_esperada'](ms('2026-11-05'), rodada)
    eq((n17, b17), (0, []), "L17 (além de 384 h): nenhuma saída")
    # por que só 00Z: com rodada 12Z, o 1º dia tem 12 saídas e 2 blocos
    n12, b12 = M['contagem_esperada'](ms('2026-10-20'), z('2026-10-20', 12))
    eq((n12, len(b12)), (12, 2), "rodada 12Z: 1º dia incompleto (motivo do B1)")
    # rodada 12Z, dia que atravessa 120 h: mistura saídas horárias e de 3 h
    n_mix, _ = M['contagem_esperada'](ms('2026-10-25'), z('2026-10-20', 12))
    eq(n_mix, 12 + 4, "rodada 12Z, horas 109-132: 12 horárias + 4 de 3 h (mistura evitada pelo 00Z)")


# ---------------------------------------------------------------- 3. faixa e confiança por prazo
def teste_faixa_confianca():
    rodada = z('2026-10-20')
    faixas = {}
    for L in range(1, 17):
        dia = M['somar_dias']('2026-10-20', L - 1)
        faixas.setdefault(M['faixa_prazo'](ms(dia), rodada), []).append(L)
    eq(faixas, {'L1': [1], 'L2a5': [2, 3, 4, 5], 'L6a10': [6, 7, 8, 9, 10],
                'L11a15': [11, 12, 13, 14, 15, 16]}, "faixas (o prazo 16 usa L11a15)")
    conf = {L: M['confianca_prazo'](L) for L in range(1, 17)}
    eq({L for L, c in conf.items() if c == 'alta'}, set(range(1, 6)), "alta = prazos 1 a 5")
    eq({L for L, c in conf.items() if c == 'media'}, set(range(6, 11)), "media = prazos 6 a 10")
    eq({L for L, c in conf.items() if c == 'baixa'}, set(range(11, 17)), "baixa = prazos 11 em diante")


# ---------------------------------------------------------------- 4. seleção de rodadas 00Z completas
def _janela(contagem_especial):
    """Rodadas de 4 ciclos por dia de 2026-10-08 a 2026-10-20 (com 06/12/18Z de 10-20), com
    contagens 208 salvo as indicadas. creation_time às vezes vem como float ou texto."""
    rodadas, contagens = [], []
    d = '2026-10-08'
    while d <= '2026-10-20':
        for hora in (0, 6, 12, 18):
            r = z(d, hora)
            rodadas.append(float(r) if hora == 6 else (str(r) if hora == 12 else r))
            contagens.append(contagem_especial.get((d, hora), 208))
        d = M['somar_dias'](d, 1)
    return rodadas, contagens


def teste_selecao_rodadas():
    sel = M['selecionar_rodadas']
    rodadas, contagens = _janela({('2026-10-20', 0): 95, ('2026-10-14', 0): 207})
    r00, completas, ref = sel(rodadas, contagens)
    ok(all(r % M['MS_DIA'] == 0 for r in r00), "só rodadas 00Z")
    eq(len(r00), 13, "13 rodadas 00Z de 08/10 a 20/10")
    ok(z('2026-10-20', 18) not in completas, "a 18Z completa e mais recente é ignorada")
    ok(z('2026-10-14') not in completas, "207/208: incompleta")
    ok(z('2026-10-20') not in completas, "95/208 (ainda chegando): incompleta")
    eq(ref, z('2026-10-19'), "referência = 00Z completa mais recente")
    eq(completas, sorted(completas), "completas em ordem")
    # duplicatas no acervo não inflam a contagem (o motor conta horas distintas; aqui, a mesma rodada
    # repetida na lista fica uma só)
    r00b, _, _ = sel(rodadas + [z('2026-10-19')], contagens + [208])
    eq(r00b, r00, "rodada repetida na lista conta uma vez")
    # nenhuma 00Z completa (mesmo com 06/12/18Z completas): referência None
    tudo_incompleto = {(M['somar_dias']('2026-10-08', k), 0): 200 for k in range(13)}
    _, comp2, ref2 = sel(*_janela(tudo_incompleto))
    eq((comp2, ref2), ([], None), "sem 00Z completa: nenhum dia GFS nesta execução")
    eq(sel([], []), ([], [], None), "janela vazia")
    ok(M['eh_rodada_00z'](z('2026-10-20')) and not M['eh_rodada_00z'](z('2026-10-20', 6))
       and not M['eh_rodada_00z'](z('2026-10-20', 12)) and not M['eh_rodada_00z'](z('2026-10-20', 18)),
       "eh_rodada_00z")


# ---------------------------------------------------------------- 5. rodada de cada dia e horizonte
def teste_rodada_para_dia_e_horizonte():
    rodadas, contagens = _janela({('2026-10-20', 0): 95, ('2026-10-14', 0): 207})
    _, completas, ref = M['selecionar_rodadas'](rodadas, contagens)
    rpd = M['rodada_para_dia']
    pL = M['prazo_L']
    eq(rpd('2026-10-19', completas, ref), ref, "dia da referência: a referência (L1)")
    eq(pL(ms('2026-10-20'), rpd('2026-10-20', completas, ref)), 2, "hoje com a 00Z de hoje incompleta: L2")
    eq(rpd('2026-10-15', completas, ref), z('2026-10-15'), "dia passado: a 00Z do próprio dia")
    eq(rpd('2026-10-14', completas, ref), z('2026-10-13'),
       "dia passado com a própria 00Z incompleta: a 00Z completa anterior (L2)")
    eq(rpd('2026-10-07', completas, ref), None, "nenhuma rodada completa cobre o dia: None")
    # o fallback não passa do prazo 16
    so_uma = [z('2026-10-01')]
    eq(rpd('2026-10-16', so_uma, z('2026-10-20')), z('2026-10-01'), "prazo 16: ainda coberto")
    eq(rpd('2026-10-17', so_uma, z('2026-10-20')), None, "prazo 17: não coberto")
    # horizonte
    fh = M['fim_horizonte']
    eq(fh('2026-10-20', z('2026-10-19')), '2026-11-03', "ref = ontem: fim = ontem + 15 (L16)")
    eq(fh('2026-10-20', z('2026-10-20')), '2026-11-04', "ref = hoje: fim = hoje + 15 (L16)")
    eq(fh('2026-10-20', z('2026-10-12')), '2026-10-27', "ref antiga: o fim encolhe junto")
    for hoje, r in (('2026-10-20', z('2026-10-19')), ('2026-10-20', z('2026-10-20'))):
        fim = fh(hoje, r)
        eq(pL(ms(fim), r), 16, f"o último dia é o prazo 16 ({hoje}, ref {M['ms_para_data'](r)})")
        n, blocos = M['contagem_esperada'](ms(fim), r)
        eq((n, len(blocos)), (8, 4), "prazo 16 completo: 8 saídas e 4 blocos (M05-28)")
    eq(M['HORIZONTE_DIAS'], 15, "HORIZONTE_DIAS")


# ---------------------------------------------------------------- 6. conversão em definitivo e status
def teste_conversao_definitivo():
    lim = M['limite_definitivo']
    eq(lim('2026-06-30', False, '2025-12-31'), '2025-12-31', "sem conversão: nada depois de 2025")
    eq(lim('2026-06-30', True, '2025-12-31'), '2026-06-30', "com conversão: até o fim do BR-DWGD")
    eq(lim('2025-12-31', False, '2025-12-31'), '2025-12-31', "hoje (BR-DWGD até 2025-12-31)")
    eq(lim('2025-11-30', False, '2025-12-31'), '2025-11-30', "BR-DWGD atrás do limite")
    eq(M['CONVERTER_EM_DEFINITIVO'], False, "padrão CONVERTER_EM_DEFINITIVO = False")
    eq(M['dias_aguardando_decisao']('2026-06-30', '2025-12-31'), 181, "jan-jun/2026 = 181 dias")
    eq(M['dias_aguardando_decisao']('2025-12-31', '2025-12-31'), 0, "nenhum dia aguardando")

    st = M['status_dia']
    M['ultima_data_era5'] = '2026-10-14'
    for converter, esperado in ((False, 'gravado'), (True, 'precisa_upgrade')):
        M['limite_def'] = lim('2026-06-30', converter, '2025-12-31')
        eq(st('2026-03-01', {'versao': 'provisoria_era5', 'alg': 'V1.5', 'rodada': 0}), esperado,
           f"provisório V1.5 coberto pelo BR-DWGD, converter={converter}")
    M['limite_def'] = lim('2026-06-30', False, '2025-12-31')
    eq(st('2026-03-01', {'versao': 'provisoria_era5', 'alg': 'V1.3', 'rodada': 0}), 'precisa_upgrade',
       "provisório V1.3 -> recalculado (como provisório, pois 2026-03-01 > limite_def)")
    ok('2026-03-01' > M['limite_def'], "rota do recálculo: provisoria_era5")
    eq(st('2026-03-01', {'versao': 'provisoria_era5', 'alg': 'V1.4', 'rodada': 0}), 'precisa_upgrade',
       "provisório V1.4 -> recalculado para V1.5")
    eq(st('2026-10-10', {'versao': 'provisoria_gfs', 'alg': 'V1.3', 'rodada': 1}), 'precisa_upgrade',
       "dia GFS já coberto pelo ERA5 -> rota ERA5")
    eq(st('2026-10-20', {'versao': 'provisoria_gfs', 'alg': 'V1.3', 'rodada': 1}), 'gravado',
       "dia GFS futuro: a cadeia GFS decide")
    eq(st('2025-06-01', {'versao': 'definitiva', 'alg': 'V1.0', 'rodada': 0}), 'gravado',
       "definitivo V1.0 (histórico) fica")
    eq(st('2026-01-10', {'versao': 'definitiva', 'alg': 'V1.5', 'rodada': 0}), 'gravado',
       "definitivo V1.5 não é reexportado (M05-22)")
    ok('V1.5' in M['ALGORITMOS_DEFINITIVOS_VALIDOS'] and M['VERSAO_ALGORITMO'] == 'V1.5', "versão V1.5")
    # trava do histórico
    ok(M['dia_protegido']('SAB_2025_12_31') and not M['dia_protegido']('SAB_2026_01_01')
       and M['dia_protegido']('SAB_2026_01_01_x'), "dia_protegido")
    ok(M['PROTEGER_HISTORICO'] and M['DATA_LIMITE_PROTECAO'] == '2025-12-31', "trava ligada até 2025-12-31")
    ok(M['DIA_MASCARA_CANONICA'] <= M['DATA_LIMITE_PROTECAO'], "a máscara canônica vem de um dia protegido")


# ---------------------------------------------------------------- 7. refazer dias GFS (M05-09)
def teste_precisa_refazer():
    f = M['precisa_refazer_gfs']
    r = z('2026-10-19')
    em_uso = M['METODO_TEMP_GFS']
    outro = 'aditivo' if em_uso == 'variancia' else 'variancia'
    ur_uso = M['METODO_UR_RS_GFS']
    ur_outro = 'original' if ur_uso == 'variancia' else 'variancia'
    base = {'versao': 'provisoria_gfs', 'alg': 'V1.5', 'rodada': r, 'metodo': em_uso, 'metodo_ur_rs': ur_uso}
    eq(f(None, r, False, 4), True, "dia ausente")
    eq(f(base, r, True, 4), True, "forçado pelo estado do solo")
    eq(f(base, r, False, 4), False, "completo, mesma rodada e versão: fica")
    eq(f(dict(base, versao='provisoria_gfs_incompleta'), r, False, 4), True, "incompleto: refaz (M05-09)")
    eq(f(dict(base, versao='falha_latencia_gfs'), r, False, 4), True, "falha: refaz (M05-09)")
    eq(f(dict(base, versao='provisoria_gfs_incompleta'), r, False, 2), False, "sem 4 blocos esperados: não insiste")
    eq(f(dict(base, alg='V1.3'), r, False, 4), True, "versão antiga: refaz")
    eq(f(dict(base, rodada=z('2026-10-18')), r, False, 4), True, "rodada diferente: refaz")
    eq(f(dict(base, metodo=outro), r, False, 4), True, "método da Tmax diferente do em uso: refaz (V41-08)")
    eq(f(dict(base, metodo=em_uso), r, False, 4), False, "mesmo método: fica")
    sem = {k: v for k, v in base.items() if k != 'metodo'}
    eq(f(sem, r, False, 4), em_uso != 'aditivo', "dia sem a propriedade conta como aditivo (gravado antes da V4.1)")
    eq(f(dict(base, metodo_ur_rs=ur_outro), r, False, 4), True, "método da UR/radiação diferente do em uso: refaz (K9A)")
    sem = {k: v for k, v in base.items() if k != 'metodo_ur_rs'}
    eq(f(sem, r, False, 4), ur_uso != 'original', "dia sem metodo_ur_rs conta como 'original' (gravado antes da K9A)")
    p = M['info_de_propriedades']({'versao': 'provisoria_gfs', 'versao_algoritmo': 'V1.5', 'rodada_gfs_ms': r})
    eq((p['metodo'], p['metodo_ur_rs']), ('aditivo', 'original'), "propriedades ausentes: métodos antigos")
    p = M['info_de_propriedades']({'metodo_temp_gfs': 'variancia', 'metodo_ur_rs_gfs': 'variancia'})
    eq((p['metodo'], p['metodo_ur_rs']), ('variancia', 'variancia'), "propriedades lidas do asset")


# ---------------------------------------------------------------- 8. dias da PRÉVIA 6
def teste_dias_previa_gfs():
    f = M['dias_previa_gfs']
    eq(f('2026-10-15', z('2026-10-19'), '2026-11-03'), ['2026-10-15', '2026-10-20', '2026-10-26', '2026-10-29'],
       "1º dia GFS e prazos L2, L8 (V4.1 V41-09) e L11 da referência")
    eq(f('2026-10-20', z('2026-10-19'), '2026-11-03'), ['2026-10-20', '2026-10-26', '2026-10-29'], "sem repetir")
    eq(f('2026-10-15', z('2026-10-19'), '2026-10-25'), ['2026-10-15', '2026-10-20'], "dentro do horizonte")


# ---------------------------------------------------------------- 9. contrato e constantes
def teste_contrato():
    eq(M['FONTE_GFS'], 'NOAA/GFS0P25 (rodada 00Z)', "fonte GFS")
    eq(M['FONTE_ERA5'], 'ECMWF/ERA5_LAND/DAILY_AGGR', "fonte ERA5")
    eq(M['FONTE_DEFINITIVA'], 'BR-DWGD (ERA5 só onde falta)', "fonte definitiva")
    eq(M['JANELA_CHUVA_00_24'], '00-24', "janela 00-24")
    eq(M['JANELA_CHUVA_12_12'], '12-12 (12 UTC D-1 a 12 UTC D)', "janela 12-12")
    eq(M['MATRIZ_GFS_ROTULO'], 'SICSB_MATRIZ_GFS_V2 V2.1', "matriz_gfs")
    eq(M['VERSAO_MATRIZ_GFS'], 'V2.1', "versao_matriz exigida")
    bandas = M['BANDAS_MEDIA_GFS']
    eq(len(bandas), 48, "48 bandas de média")
    ok('pr_m_sicsb_L1' in bandas and 'Rs_m_gfs_L11a15' in bandas and 'Tmax_m_gfs_L6a10' in bandas,
       "nomes {v}_m_{sicsb|gfs}_{fx}")
    ok(not any('_s_' in b for b in bandas), "o motor não exige as bandas _s_")
    eq(set(M['BANDAS_MASCARADAS_INCOMPLETO']), {'pr_mm', 'rs', 'et_potencial', 'et_real', 'transpiracao_mm'},
       "bandas mascaradas no dia incompleto")
    ok(set(M['BANDAS_MASCARADAS_INCOMPLETO']) <= set(M['ORDEM_BANDAS']), "bandas existem")
    eq(M['CRIT_SOLO_BRASIL'], 2.0, "CRIT_SOLO_BRASIL = 2.0")
    eq((M['K_CHUVA_MM'], M['FATOR_MAX'], M['FATOR_MIN_UV_RS'], M['FATOR_MAX_UV_RS']), (0.1, 5.0, 0.5, 2.0),
       "constantes da calibração GFS")
    eq((M['TMAX_RECORDE_BR'], M['SALTO_MAX_TMAX']), (44.8, 2.0), "critérios da PRÉVIA 6")
    eq(M['ARQUIVO_PREVIA'], 'previa_v15.csv', "arquivo da prévia")
    ok(M['versao_tmp_aceita']('V1.5') and M['versao_tmp_aceita']('V1.0-P12')
       and not M['versao_tmp_aceita']('V1.4') and not M['versao_tmp_aceita'](None), "versões promovíveis do TMP")


# ---------------------------------------------------------------- 10. mensagens citadas pelo roteiro
def teste_mensagens():
    for msg in ('MODO SIMULAÇÃO ATIVO', 'TRAVA DO HISTÓRICO LIGADA', 'RESUMO DA SIMULAÇÃO', 'PRÉVIA 2',
                'PRÉVIA 3', 'PRÉVIA 5', 'PRÉVIA 6', 'Todos os critérios atendidos', 'PROTEGIDOS: nenhum dia',
                'Vagas restantes na fila', 'não tem os meses', 'Execução encerrada', 'deve ficar igual',
                'criar (GFS)', '-> GFS', 'Rodada GFS de referência', 'aguardam decisão',
                'ΔUmid 0-5 %', 'ΔUmid 0-100 %'):
        ok(msg in FONTE, f"mensagem ausente: {msg!r}")
    ok("'previa_v15.csv'" in FONTE, "previa_v15.csv")
    # nenhuma rota escolhida por ultima_data_brd (agora é limite_def)
    ok(not re.search(r'd(_str)?\s*<=\s*ultima_data_brd', FONTE), "rota/status ainda usam ultima_data_brd")
    corpo_finalizar = FONTE.split('def finalizar', 1)[1].split('def _componentes_era5', 1)[0]
    codigo_finalizar = '\n'.join(l.split('#', 1)[0] for l in corpo_finalizar.splitlines())
    ok('.clip(' not in codigo_finalizar and '.updateMask(MASCARA_SAB)' in codigo_finalizar,
       "finalizar sem clip e com a máscara canônica")
    ok('stats[\'n\'] >= 198' not in FONTE, "contagem antiga de rodada removida")
    ok("downward_shortwave_radiation_flux').mean()))" not in FONTE, "média simples da radiação removida")


# ---------------------------------------------------------------- 11. 05a x 05b
def teste_05a_05b():
    if not os.path.exists(ARQ_B):
        raise AssertionError(f"falta {ARQ_B}")
    with open(ARQ_A, encoding='utf-8') as fa, open(ARQ_B, encoding='utf-8') as fb:
        a, b = fa.read().splitlines(), fb.read().splitlines()
    eq(len(a), len(b), "mesmo número de linhas")
    dif = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    ok(len(dif) == 2 and dif[0] == 0, f"05a e 05b só diferem na linha 1 e em SIMULAR (diferem em {dif})")
    eq((a[dif[1]].strip(), b[dif[1]].strip()), ('SIMULAR = True', 'SIMULAR = False'), "linha SIMULAR")
    ok('V1.5 em SIMULAÇÃO' in a[0] and 'V1.5 GRAVANDO' in b[0], "linha 1 de cada arquivo")
    eq(M['SIMULAR'], True, "05a em simulação")


# ---------------------------------------------------------------- 12. [V4.1 K7] Tmax: aditivo x escala de variância
class Num:
    """Imagem falsa de um pixel: só as operações usadas por expandir_borda e pelas calibrações."""
    def __init__(self, v):
        self.v = float(v)

    def _o(self, x):
        return x.v if isinstance(x, Num) else float(x)

    def add(self, x):
        return Num(self.v + self._o(x))

    def subtract(self, x):
        return Num(self.v - self._o(x))

    def multiply(self, x):
        return Num(self.v * self._o(x))

    def divide(self, x):
        return Num(self.v / self._o(x))

    def max(self, x):
        return Num(max(self.v, self._o(x)))

    def clamp(self, a, b):
        return Num(min(max(self.v, a), b))

    def unmask(self, *a, **k):
        return self

    def reproject(self, *a, **k):
        return self

    def focalMean(self, *a, **k):
        return self


def teste_tmax_variancia():
    eq(M['METODO_TEMP_GFS'], 'variancia', "padrão: escala de variância (validada pela auditoria K8)")
    eq((M['RAZAO_DESVIO_MIN'], M['RAZAO_DESVIO_MAX']), (0.5, 2.0), "razão dos desvios limitada a [0,5; 2]")
    eq(len(M['BANDAS_DESVIO_TEMP']), 16, "16 bandas de desvio (Tmax e Tmin, BR-DWGD e GFS, 4 faixas)")
    ok('Tmax_s_sicsb_L1' in M['BANDAS_DESVIO_TEMP'] and 'Tmin_s_gfs_L11a15' in M['BANDAS_DESVIO_TEMP'], "nomes do contrato V2.1")
    cv, ca = M['calib_variancia'], M['calib_aditiva']
    x, ma, mm = Num(40), Num(30), Num(31)
    eq(ca(x, ma, mm).v, 39.0, "aditivo: 40 + (30 - 31) = 39")
    eq(cv(x, ma, mm, Num(2), Num(4)).v, 34.5, "variância: 30 + (40 - 31) x 0,5 = 34,5")
    eq(cv(x, ma, mm, Num(1), Num(4)).v, 34.5, "razão 0,25 limitada a 0,5")
    eq(cv(x, ma, mm, Num(3), Num(0)).v, 48.0, "desvio do GFS zero: razão limitada a 2 (30 + 9 x 2)")
    eq(cv(Num(31), ma, mm, Num(2), Num(4)).v, 30.0, "no valor médio do GFS, as duas dão a média do BR-DWGD")
    eq(cv(x, ma, mm, Num(3), Num(3)).v, ca(x, ma, mm).v, "desvios iguais: igual ao aditivo")
    d = M['decisao_tmax']
    ok(d('aditivo', 'variancia', {'aditivo': True, 'variancia': False}).startswith('✅'), "método em uso passa: ✅")
    ok("troque METODO_TEMP_GFS = 'aditivo' por 'variancia'" in d('aditivo', 'variancia', {'aditivo': False, 'variancia': True}),
       "só o outro passa: diz exatamente o que trocar")
    ok('nenhum dos dois' in d('aditivo', 'variancia', {'aditivo': False, 'variancia': False}), "nenhum passa: decisão do usuário")
    ok(d('aditivo', 'variancia', {'aditivo': True, 'variancia': True}, {'aditivo': False, 'variancia': False}).startswith('⚠️'),
       "emenda não testada: não decide (V41-03)")
    ok('nenhum dos dois' in d('aditivo', 'variancia', {'aditivo': False, 'variancia': True},
                              {'aditivo': True, 'variancia': False}),
       "o outro passou no recorde mas sem emenda testada: não é recomendado (V41-03)")
    eq(sum(l.startswith("METODO_TEMP_GFS = ") for l in FONTE.splitlines()), 1, "uma única linha da constante (V41-01)")
    eq(sum("METODO_TEMP_GFS = 'variancia'" in l for l in FONTE.splitlines()), 1,
       "a busca acha só a constante, não o comentário (V41-01)")
    eq(sum("METODO_TEMP_GFS = 'aditivo'" in l for l in FONTE.splitlines()), 0, "nenhuma linha com o método antigo")
    r = d('variancia', 'aditivo', {'variancia': False, 'aditivo': True})
    ok(r.startswith('⚠️') and 'NÃO troque' in r and 'troque METODO_TEMP_GFS' not in r,
       "variância em uso e só o aditivo passa: não manda voltar ao aditivo (revisão 20/10)")
    ok(d('variancia', 'aditivo', {'variancia': True, 'aditivo': False}).startswith('✅'), "variância em uso passa: ✅")
    ok('nenhum dos dois' in d('variancia', 'aditivo', {'variancia': False, 'aditivo': False}), "nenhum passa (variância em uso)")
    ok("partes + partes_info" in FONTE and "_nacional_gfs(partes, extras_req)" in FONTE,
       "o informativo não derruba o critério obrigatório (V41-02)")
    ok("'metodo_temp_gfs': metodo" in FONTE and "metodo_temp=alt" in FONTE, "propriedade nova e PRÉVIA com o outro método")
    ok("BANDAS_MEDIA_GFS + BANDAS_DESVIO_TEMP" in FONTE, "o motor confere também as bandas de desvio na matriz")


# ---------------------------------------------------------------- 13. [K9A] UR e radiação pela escala de variância
def teste_ur_rs_variancia():
    eq(M['METODO_UR_RS_GFS'], 'variancia', "padrão: escala de variância na UR e na radiação (validada pela K9A)")
    b = M['BANDAS_DESVIO_UR_RS']
    eq(len(b), 16, "16 bandas de desvio (UR e radiação, BR-DWGD e GFS, 4 faixas)")
    ok('RH_s_sicsb_L1' in b and 'Rs_s_gfs_L11a15' in b, "nomes do contrato V2.1 (os mesmos que o 03 grava)")
    ok(not set(b) & set(M['BANDAS_DESVIO_TEMP']), "sem repetir as bandas da temperatura")
    eq(sum(l.startswith("METODO_UR_RS_GFS = ") for l in FONTE.splitlines()), 1, "uma única linha da constante")
    for trecho, msg in (
            ("rh = calib_variancia(rh_raw, *medias('RH'), *desvios('RH')).clamp(0, 100).rename('RH')", "UR pela variância, limitada a [0, 100]"),
            ("rs = calib_variancia(rs_raw, *medias('Rs'), *desvios('Rs')).max(0).rename('rs')", "radiação pela variância, >= 0"),
            ("u2 = calib_limitada_gfs(u2_raw, *medias('u2')).max(0).rename('u2')", "vento continua com o fator [0,5; 2]"),
            ("'metodo_ur_rs_gfs': METODO_UR_RS_GFS", "propriedade nova nos dias GFS"),
            ("BANDAS_MEDIA_GFS + BANDAS_DESVIO_TEMP + BANDAS_DESVIO_UR_RS", "o motor confere as 16 bandas novas na matriz"),
            ("repeat(7)", "inventário lê as propriedades novas (K9A e K11)"),
            ("'metodo_ur_rs': d.get('metodo_ur_rs_gfs', 'original')", "inventário: padrão 'original'")):
        ok(trecho in FONTE, msg)
    # Mesma conta da K9A (calibrar, 'escala de variância'): mo + (g - mg) x clip(so / max(sg, 1e-3), 0,5; 2)
    import random
    rnd = random.Random(7)
    cv, cl = M['calib_variancia'], M['calib_limitada_gfs']
    for _ in range(500):
        g, mo, mg = rnd.uniform(5, 100), rnd.uniform(20, 95), rnd.uniform(20, 95)
        so, sg = rnd.uniform(0, 15), rnd.uniform(0, 15)
        k9a = min(max(mo + (g - mg) * min(max(so / max(sg, 1e-3), 0.5), 2.0), 0), 100)
        motor = cv(Num(g), Num(mo), Num(mg), Num(so), Num(sg)).clamp(0, 100).v
        ok(abs(motor - k9a) < 1e-9, f"UR: motor {motor} x K9A {k9a}")
        gr, mor, mgr = rnd.uniform(0, 32), rnd.uniform(5, 28), rnd.uniform(5, 28)
        k9a = max(mor + (gr - mgr) * min(max(so / max(sg, 1e-3), 0.5), 2.0), 0)
        motor = cv(Num(gr), Num(mor), Num(mgr), Num(so), Num(sg)).max(0).v
        ok(abs(motor - k9a) < 1e-9, f"radiação: motor {motor} x K9A {k9a}")
        k9a = gr * min(max(mor / max(mgr, 1e-3), 0.5), 2.0)
        ok(abs(cl(Num(gr), Num(mor), Num(mgr)).v - k9a) < 1e-9, "radiação 'original': fator [0,5; 2] como a K9A")


# ---------------------------------------------------------------- 14. [correção 21/10 18h] ERA5 com lacuna
def teste_era5_continuo():
    f = M['ultimo_dia_continuo']
    dias = {f'2026-10-{d:02d}' for d in range(1, 12)}
    eq(f(dias), ('2026-10-11', []), "sem lacuna: o último publicado")
    eq(f(dias - {'2026-10-09', '2026-10-10'}), ('2026-10-08', ['2026-10-09', '2026-10-10']),
       "caso real de 21/10/2026: 11 publicado sem 09 e 10 -> ERA5 só até 08")
    eq(f({'2026-10-05'}), ('2026-10-05', []), "um dia só")
    ok("ultima_data_era5, dias_faltando_era5 = ultimo_dia_continuo(" in FONTE, "o motor usa o último dia contínuo")
    ok("aggregate_max('system:time_start').getInfo()\nif _ms_era5" not in FONTE, "a data máxima não decide mais a rota")


# ---------------------------------------------------------------- K11 (22/10/2026)
def teste_teto_razao_k11():
    eq(M['RAZAO_DESVIO_MAX_LONGO'], 1.0, "teto 1 nos prazos de 6 dias em diante (validação K11)")
    eq(M['RAZAO_DESVIO_MAX'], 2.0, "teto 2 nos prazos 1 a 5 (inalterado)")
    t = M['teto_razao_temp']
    eq([t(f) for f in M['FAIXAS_GFS']], [2.0, 2.0, 1.0, 1.0], "L1 e L2a5: 2; L6a10 e L11a15: 1")
    # faixa de cada prazo (o dia 16 entra em L11a15)
    fx = M['faixa_prazo']
    r = z('2026-10-21')
    eq([t(fx(z(d), r)) for d in ('2026-10-21', '2026-10-25', '2026-10-26', '2026-10-30', '2026-10-31', '2026-11-05')],
       [2.0, 2.0, 1.0, 1.0, 1.0, 1.0], "prazos 1, 5, 6, 10, 11 e 16")
    # Casa Nova-BA, 26/10/2026 (K10): GFS 35,41; m_sicsb 34,89; m_gfs 30,18; s_sicsb 1,93; s_gfs 0,97
    cv = M['calib_variancia']
    antes = cv(Num(35.41), Num(34.89), Num(30.18), Num(1.93), Num(0.97)).v
    depois = cv(Num(35.41), Num(34.89), Num(30.18), Num(1.93), Num(0.97), teto=t('L6a10')).v
    ok(abs(antes - 45.3) < 0.1, f"Casa Nova com o teto 2 reproduz o caso de 22/10 ({antes:.2f} °C)")
    ok(abs(depois - 40.12) < 0.01, f"Casa Nova com o teto 1: {depois:.2f} °C (abaixo do máximo histórico do pixel, 40,76)")
    # razão abaixo de 1: o teto não muda nada
    eq(cv(Num(30), Num(28), Num(27), Num(1), Num(2)).v, cv(Num(30), Num(28), Num(27), Num(1), Num(2), teto=1.0).v,
       "razão < 1: mesmo valor com qualquer teto")
    # refazer: dia sem a propriedade conta como 2.0
    f = M['precisa_refazer_gfs']
    base = {'versao': 'provisoria_gfs', 'alg': 'V1.5', 'rodada': r, 'metodo': M['METODO_TEMP_GFS'],
            'metodo_ur_rs': M['METODO_UR_RS_GFS']}
    eq(f(base, r, False, 4, 'L6a10'), True, "prazo 6+ gravado sem o teto novo: refaz")
    eq(f(base, r, False, 4, 'L2a5'), False, "prazo 2-5 gravado antes da K11 (teto 2): fica")
    eq(f(dict(base, teto_razao=1.0), r, False, 4, 'L11a15'), False, "prazo 11+ com teto 1: fica")
    eq(f(dict(base, teto_razao=1.0), r, False, 4, 'L1'), True, "prazo 1 com teto 1 (não deveria): refaz")
    eq(f(base, r, False, 4), False, "sem a faixa (chamada antiga): o teto não é conferido")
    p = M['info_de_propriedades']({'versao': 'provisoria_gfs'})
    eq(p['teto_razao'], 2.0, "propriedade ausente: 2.0")
    eq(M['info_de_propriedades']({'teto_razao_temp_gfs': 1.0})['teto_razao'], 1.0, "propriedade lida do asset")
    for trecho, msg in (
            ("tmax_c = calib_variancia(tmax_raw, *medias('Tmax'), *desvios('Tmax'), teto=teto_temp)", "Tmax com o teto da faixa"),
            ("tmin_c = calib_variancia(tmin_raw, *medias('Tmin'), *desvios('Tmin'), teto=teto_temp)", "Tmin com o teto da faixa"),
            ("rh = calib_variancia(rh_raw, *medias('RH'), *desvios('RH')).clamp(0, 100).rename('RH')", "UR sem o teto novo"),
            ("rs = calib_variancia(rs_raw, *medias('Rs'), *desvios('Rs')).max(0).rename('rs')", "radiação sem o teto novo"),
            ("'teto_razao_temp_gfs': float(teto_razao_temp(faixa))", "propriedade nova nos dias GFS"),
            ("precisa_refazer_gfs(info, rodada, forcar, len(horas_chuva), faixa)", "a cadeia passa a faixa")):
        ok(trecho in FONTE, msg)


if __name__ == '__main__':
    testes = [v for k, v in sorted(globals().items()) if k.startswith('teste_') and callable(v)]
    falhas = 0
    for t in testes:
        try:
            t()
            print(f"OK    {t.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"FALHA {t.__name__}: {e}")
    print(f"\n{N_OK} verificações; {len(testes) - falhas} de {len(testes)} testes OK.")
    sys.exit(1 if falhas else 0)
