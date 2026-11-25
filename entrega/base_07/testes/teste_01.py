# Testes offline (sem Earth Engine) da lógica pura do 01a/01b_mascara_qualidade (v4).
# As funções e constantes são extraídas do próprio arquivo pela AST; nada do Earth Engine é executado.
# Rodar: python3 testes/teste_01.py  (a partir da pasta do pacote)
import ast
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(AQUI, '..', '01a_mascara_qualidade_SIMULACAO.py')
ARQ_B = os.path.join(AQUI, '..', '01b_mascara_qualidade_GRAVACAO.py')
FUNCOES = ['comparar_j1', 'referencias_c', 'resumo_conferencia', 'pixels_b_raros', 'grade_nativa', 'contar_discordancias', 'escolher_metodo']
CONSTANTES = ['J1_CONTAGENS', 'K1D_CENTRO_NO_BRASIL', 'C_FORA_APROX', 'TOL_J1', 'TOL_INFO_C', 'METODOS_CENTRO', 'SIMULAR',
              'VERSAO_MASCARA', 'DIA_REFERENCIA', 'DIAS_CLASSES', 'TRANSFORM', 'ASSET_MASCARA', 'RAIZ', 'PROJETO']
FALHAS = []


def confere(cond, msg):
    print(('  ok   ' if cond else '  FALHA ') + msg)
    if not cond:
        FALHAS.append(msg)


fonte = open(ARQ, encoding='utf-8').read()
arvore = ast.parse(fonte)
nos, achados = [], set()
for no in arvore.body:
    if isinstance(no, ast.Assign) and any(isinstance(t, ast.Name) and t.id in CONSTANTES for t in no.targets):
        nos.append(no)
        achados |= {t.id for t in no.targets if isinstance(t, ast.Name)}
    elif isinstance(no, ast.FunctionDef) and no.name in FUNCOES:
        nos.append(no)
        achados.add(no.name)
assert not set(FUNCOES + CONSTANTES) - achados, set(FUNCOES + CONSTANTES) - achados
M = {}
exec(compile(ast.Module(body=nos, type_ignores=[]), ARQ, 'exec'), M)

print('\n[contrato]')
confere(M['SIMULAR'] is True, 'SIMULAR = True por padrão')
confere(M['ASSET_MASCARA'] == 'projects/clima-492922/assets/SAB_MASCARA_QUALIDADE', 'asset do contrato')
confere(M['VERSAO_MASCARA'] == 'Q1' and M['DIA_REFERENCIA'] == '2001-01-15', "versao_mascara 'Q1', dia 2001-01-15")
confere(M['DIAS_CLASSES'][0] == M['DIA_REFERENCIA'] and len(set(M['DIAS_CLASSES'])) == 5,
        '5 dias distintos na união de B, o 1º é o de referência (V4.1 K1a)')
confere(any(d[5:7] in ('06', '07', '08') for d in M['DIAS_CLASSES']), 'há dia de inverno na união (coincidências da K1a)')
confere(M['TRANSFORM'] == [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432],
        'crsTransform nativo do BR-DWGD')
for trecho in ("'classe'", 'toUint8()', 'pyramidingPolicy', "'versao_mascara'", "'dia_referencia'", "'gerado_em'",
               "n_classe_{k}", 'ee.Reducer.sum().unweighted()', "ADM0_NAME', 'Brazil'"):
    confere(trecho in fonte, f'código contém {trecho}')

print('\n[01a x 01b]')
la = fonte.splitlines()
lb = open(ARQ_B, encoding='utf-8').read().splitlines()
dif = [i + 1 for i, (x, y) in enumerate(zip(la, lb)) if x != y]
confere(len(la) == len(lb) and len(dif) == 2 and dif[0] == 1, f'01a e 01b diferem só em 2 linhas, a 1ª é o rótulo ({dif})')
confere(len(dif) == 2 and lb[dif[1] - 1].startswith('SIMULAR = False') and la[dif[1] - 1].startswith('SIMULAR = True'),
        '01a com SIMULAR = True e 01b com SIMULAR = False')
confere('SIMULAÇÃO' in la[0] and 'GRAVANDO' in lb[0], 'rótulos da linha 1')
confere("'Sem ⚠️: rode o 01b para gravar.'" in fonte, 'mensagem final da simulação manda rodar o 01b')

print('\n[comparação com a J1]')
linhas = M['comparar_j1']({1: 70364, 2: 204, 3: 229, 4: 880})
confere(all(x['ok'] for x in linhas) and [x['calculado'] for x in linhas] == [70364, 204, 1109], 'J1 exata: tudo ok')
linhas = M['comparar_j1']({1: 70364 + 700, 2: 204, 3: 229, 4: 880})
confere([x['ok'] for x in linhas] == [True, True, True], 'A +700 (0,99%): dentro de 1%')
linhas = M['comparar_j1']({1: 70364 + 710, 2: 204, 3: 229, 4: 880})
confere([x['ok'] for x in linhas] == [False, True, True], 'A +710 (1,01%): ⚠️')
linhas = M['comparar_j1']({1: 70364, 2: 207, 3: 229, 4: 880})
confere([x['ok'] for x in linhas] == [True, False, True], 'B 207 (1,5%): ⚠️')
linhas = M['comparar_j1']({1: 70364, 2: 204, 3: 300, 4: 820})
confere(linhas[2]['calculado'] == 1120 and linhas[2]['ok'], 'C = 3 + 4 (1.120, 0,99%)')
confere(M['referencias_c'](48, 1060) == [] and M['referencias_c'](58, 1250) == [], 'classe 3 ~48 e 4 ~1.060: sem ℹ️ (V4.1 K1d)')
confere(len(M['referencias_c'](229, 700)) == 2, 'classe 3 = 229 e classe 4 = 700: 2 linhas ℹ️')
confere(len(M['referencias_c'](48, 700)) == 1, 'só a classe 4 fora: 1 linha ℹ️')
print('\n[conferência entre dias (V4.1 K1a)]')
linhas = [{'dia': '2001-01-15', 'estrutura_diferente': 0, 'B_iguais_no_dia': 0},
          {'dia': '1981-07-01', 'estrutura_diferente': 0, 'B_iguais_no_dia': 7}]
confere(M['resumo_conferencia'](linhas) == (True, 7), 'coincidências B -> A não reprovam: (True, 7)')
confere(M['resumo_conferencia'](linhas + [{'dia': 'x', 'estrutura_diferente': 1, 'B_iguais_no_dia': 0}])[0] is False,
        'um pixel com estrutura diferente reprova')
confere("avisos.append(f'classe 4" not in fonte and 'referencias_c(cont[3], cont[4])' in fonte,
        'classes 3 e 4 só geram ℹ️')
confere('classes_estaveis(ref, b_u)' in fonte and 'classes_estaveis(clj[DIA_REFERENCIA], uniao_b(clj))' in fonte,
        'máscara e receita J1 usam a união dos dias')
confere("'dias_classes': ','.join(DIAS_CLASSES)" in fonte, 'propriedade dias_classes gravada')
confere(M['pixels_b_raros']({5: 296, 4: 5}) == 0 and M['pixels_b_raros']({5: 296, 2: 1, 1: 2}) == 3,
        'pixels B em só 1 ou 2 dias contados (V41-06)')
confere(M['pixels_b_raros']({'5': 296, '1.0': 1}) == 1, 'chaves do histograma em texto')
confere('completo=False' in fonte and "'contagem como na J1'" in fonte and 'geom=UF_BR.geometry().bounds()' in fonte,
        'comparação com a J1 refaz a receita da J1 (B-04)')

print('\n[grade gravada (B-01)]')
T = M['TRANSFORM']
confere(M['grade_nativa'](T), 'transform do BR-DWGD: mesma grade')
confere(M['grade_nativa']([T[0], 0, T[2] - 12 * T[0], 0, T[4], T[5] - 12 * T[4]]),
        'origem da região de exportação (-75,1 / 6,6): mesma grade')
confere(not M['grade_nativa']([T[0], 0, T[2] + 0.3 * T[0], 0, T[4], T[5]]), 'fração de pixel: outra grade')
confere(not M['grade_nativa']([0.1, 0, -75.1, 0, -0.1, 6.6]), 'escala diferente: outra grade')
confere('not grade_nativa(proj.get' in fonte, 'conferência pós-gravação usa grade_nativa')

print('\n[centro do pixel: validação da rasterização contra o teste vetorial]')
dentro = {0, 2}
confere(M['contar_discordancias'](4, dentro, {0: 1, 1: 0, 2: 1, 3: 0}) == 0, 'raster igual ao vetor: 0')
confere(M['contar_discordancias'](4, dentro, {0: 1.0, 1: 0.0, 2: 1.0, 3: 0.0}) == 0, 'valores float 1.0/0.0')
confere(M['contar_discordancias'](4, dentro, {0: 1, 1: 1, 2: 1, 3: 0}) == 1, 'pixel com centro fora pintado: 1')
confere(M['contar_discordancias'](4, dentro, {0: 1, 1: 0, 2: 1}) == 1, 'ponto sem valor conta como discordância')
confere(M['escolher_metodo']({'paint': 3, 'reduceToImage': 0, 'pontos': 0}) == 'reduceToImage', 'primeiro com 0')
confere(M['escolher_metodo']({'paint': 0}) == 'paint', 'paint aceito quando concorda')
confere(M['escolher_metodo']({'paint': 2, 'reduceToImage': 5}) is None, 'nenhum concorda: None (o script para com ❌)')
confere(M['METODOS_CENTRO'] == ('paint', 'reduceToImage', 'pontos'), 'ordem de tentativa')

print(f'\n{"TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S)"}')
sys.exit(1 if FALHAS else 0)
