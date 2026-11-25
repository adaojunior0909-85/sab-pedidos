# Teste offline das funções puras da validação K16 (sem Earth Engine). Rodar: python3 testes/teste_k16.py
import importlib.util
import os
import sys
import types

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
for m in ('ee', 'requests'):
    sys.modules.setdefault(m, types.ModuleType(m))
spec = importlib.util.spec_from_file_location('k16', os.path.join(AQUI, '..', 'validacoes', 'K16_validacao_identidade_email.py'))
k16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k16)
rotina = open(os.path.join(AQUI, '..', 'automacao_email', 'sab_pedidos', 'sab_pedido.py'), encoding='utf-8').read()
falhas = 0


def confere(cond, msg):
    global falhas
    print(('  ok   ' if cond else '  FALHA ') + msg)
    falhas += 0 if cond else 1


print('[rotina embutida]')
confere(k16.ROTINA_SRC == rotina, 'a K16 embute a rotina sab_pedido.py sem mudança')
confere(k16.sp.VERSAO_ROTINA == '2026.11.22' and len(k16.sp.DICIONARIO) == 36, 'rotina carregada como módulo')

print('[comparar]')
a = pd.DataFrame({'N_Ponto': ['P1', 'P2'], 'Data_Completa': ['d1', 'd1'], 'Tmax': ['18.40', '']})
b = a.iloc[::-1].reset_index(drop=True)
confere(k16.comparar(a, b)[0], 'mesmas células em outra ordem: igual')
c = b.copy()
c.loc[0, 'Tmax'] = '18.41'
ok, det = k16.comparar(a, c)
confere(not ok and 'Tmax' in det and '18.41' in det, 'uma célula diferente: acusa e mostra')
confere(not k16.comparar(a, b[['Data_Completa', 'N_Ponto', 'Tmax']])[0], 'colunas em outra ordem: diferente')
confere(not k16.comparar(a, a.iloc[:1])[0], 'linha a menos: diferente')
c = b.copy()
c.loc[1, 'Tmax'] = '0'
confere(not k16.comparar(a, c)[0], 'vazio x 0: diferente')
d1 = pd.DataFrame({'Variavel': ['B', 'A'], 'Descricao': ['y', 'x']})
confere(k16.comparar(d1, d1.iloc[::-1], chave=('Variavel',))[0], 'dicionário pela chave Variavel')

print('[v2: colunas do painel + só as ENSO a mais]')
pai = pd.DataFrame({'N_Ponto': ['P1'], 'Data_Completa': ['d1'], 'Tmax': ['18.40']})
rot = pai.assign(**{c: ['x'] for c in k16.sp.COLUNAS_ENSO})
confere(k16.extras_esperadas(list(pai.columns)) == k16.sp.COLUNAS_ENSO, 'painel sem filtro: 6 colunas ENSO a mais')
confere(k16.comparar_painel(rot, pai, k16.extras_esperadas(list(pai.columns)))[0], 'rotina = painel + 6 ENSO: igual')
pai5 = pai.assign(**{c: ['y'] for c in k16.sp.COLUNAS_ENSO_PAINEL})
rot5 = pai5.assign(Fonte_ENSO=['CPC'])
confere(k16.extras_esperadas(list(pai5.columns)) == ['Fonte_ENSO'] and
        k16.comparar_painel(rot5, pai5, ['Fonte_ENSO'])[0], 'A5 (com filtro): só Fonte_ENSO a mais')
rot5.loc[0, 'Fase_ENSO'] = 'outra'
confere(not k16.comparar_painel(rot5, pai5, ['Fonte_ENSO'])[0], 'A5: coluna ENSO do painel diferente acusa')
confere(not k16.comparar_painel(rot.assign(Extra=['z']), pai, k16.sp.COLUNAS_ENSO)[0], 'coluna estranha a mais: diferente')
confere(not k16.comparar_painel(rot[[c for c in rot.columns if c != 'Tmax']], pai, k16.sp.COLUNAS_ENSO)[0],
        'coluna do painel faltando: diferente')
dp = pd.DataFrame({'Variavel': ['Tipo_Dado', 'Fase_ENSO'], 'Descricao': ['a', 'velho'], 'Unidade': ['-', '-']})
dr = pd.DataFrame({'Variavel': ['Tipo_Dado', 'Fase_ENSO', 'Fonte_ENSO'], 'Descricao': ['a', 'novo', 'f'], 'Unidade': ['-'] * 3})
confere(k16.comparar_dicionario(dr, dp)[0], 'dicionário: texto ENSO novo de propósito + Fonte_ENSO: aceito')
dr2 = dr.copy()
dr2.loc[0, 'Descricao'] = 'mudou'
confere(not k16.comparar_dicionario(dr2, dp)[0], 'dicionário: linha fora da lista mudou: acusa')
e1 = pd.DataFrame({'Tipo_Dado': ['Provisorio_ERA5', 'Previsao_GFS'], 'Filtro_ENSO': ['Sem filtro'] * 2,
                   'Fase_ENSO': ['Neutro', 'Neutro'], 'Fonte_ENSO': ['Estimativa_OISST_parcial', 'Persistencia']})
confere(k16.conferir_e1(e1)[0], 'E1: previsão por persistência, sem Sem_Dado')
confere(not k16.conferir_e1(e1.assign(Fonte_ENSO=['Sem_Dado', 'Persistencia']))[0], 'E1: Sem_Dado acusa')
confere(not k16.conferir_e1(e1.iloc[:1])[0], 'E1: sem dias de previsão acusa')

print('[decidir_k16]')
todos = {c: True for c in ('A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'B1', 'B2', 'E1', 'R7')}
d = k16.decidir_k16(todos, {'19': [300, 320], '3': [150, 200]})
confere(d['aprovado'] and d['acelera'] and d['razoes'] == [0.5, 0.62], 'tudo idêntico e link 38-50% mais rápido')
confere(not k16.decidir_k16(dict(todos, A4=None), {})['aprovado'], 'caso sem CSV do painel: não aprova')
confere(not k16.decidir_k16({c: v for c, v in todos.items() if c != 'A5'}, {})['aprovado'], 'sem o caso ENSO (A5): não aprova')
confere(not k16.decidir_k16({c: v for c, v in todos.items() if c != 'A6'}, {})['aprovado'], 'sem o caso dos pixels B (A6): não aprova')
confere(not k16.decidir_k16({c: v for c, v in todos.items() if c not in ('A7', 'R7')}, {})['aprovado'],
        '[v7] sem o caso da Lagoa Mirim (A7 e R7): não aprova')
confere(not k16.decidir_k16(dict(todos, R7=False), {})['aprovado'], '[v7] radiação impossível não vazia (R7): não aprova')
confere(k16.PASTA_PAINEL == 'K16_painel_2026.11.5' and k16.PASTA_DRIVE == 'K16_teste_2026.11.22', 'pastas do Drive com a versão')
confere(not k16.decidir_k16(dict(todos, E1=False), {})['aprovado'], 'E1 com Sem_Dado: não aprova')
confere(not k16.decidir_k16(dict(todos, A2=False), {})['aprovado'], 'um caso diferente: não aprova')
confere(not k16.decidir_k16(dict(todos, D=False), {})['aprovado'], 'pasta do GitHub diferente: não aprova')
confere(k16.decidir_k16(dict(todos, D=True), {})['aprovado'], 'pasta do GitHub igual: aprova')
confere(not k16.decidir_k16(todos, {'19': [300, 320], '3': [150, 300]})['acelera'], 'ganho só num par: não acelera')
confere(not k16.decidir_k16(todos, {'19': [300, None], '3': [150, 100]})['acelera'], 'link falhou: sem conclusão')

print('[v7: R7, radiação impossível vazia no A7]')
R, E, F, T = 'Radiacao_Solar_MJ_m2', 'Evapotranspiracao_Potencial_mm', 'Deficit_Hidrico_mm', 'Evapotranspiracao_Real_mm'
base = pd.DataFrame({'Data_Completa': ['2026-03-01', '2026-03-10', '2026-03-10', '2026-03-21'],
                     R: ['27.47', '', '19.02', '22.10'], E: ['5.22', '', '3.10', '4.00'], F: ['2.0', '', '1.0', '1.5'],
                     T: ['3.2', '1.3', '2.1', '2.5']})
base['Temperatura_Maxima_C'] = ['30.1', '28.4', '29.0', '27.7']
ok, det = k16.conferir_r7(base)
confere(ok and '1 célula(s)' in det, 'um dia vazio em 04-20/03, ETo e déficit vazios junto, ET real preenchida: passa (' + det + ')')
confere(not k16.conferir_r7(base.assign(**{R: ['27.47', '0.00', '19.02', '22.10']}))[0], 'Rs 0.00 no lugar do vazio: reprova')
confere(not k16.conferir_r7(base.assign(**{R: ['27.47', '19.0', '19.02', '22.10']}))[0], 'nenhum vazio (regra não aplicada): reprova')
confere(not k16.conferir_r7(base.assign(**{R: ['27.47', '', '19.02', '']}))[0], 'vazio fora da janela 04-20/03: reprova')
confere(not k16.conferir_r7(base.assign(**{E: ['5.22', '2.27', '3.10', '4.00']}))[0], 'ETo preenchida com o Rs vazio: reprova')
confere(not k16.conferir_r7(base.assign(**{F: ['2.0', '0.9', '1.0', '1.5']}))[0], 'déficit preenchido com o Rs vazio: reprova')
confere(not k16.conferir_r7(base.assign(**{T: ['3.2', '', '2.1', '2.5']}))[0], 'ET real vazia junto: reprova (a regra não a toca)')
confere(not k16.conferir_r7(base.assign(**{E: ['', '', '3.10', '4.00']}))[0], 'ETo vazia num dia com radiação: reprova')
confere(not k16.conferir_r7(base.iloc[:0])[0], 'planilha vazia: reprova')
# [v7.1] pixels do polígono sem dado nenhum (todas as colunas vazias) ficam fora da conta, em qualquer dia
sem = pd.DataFrame({'Data_Completa': ['2026-03-01', '2026-03-25'], R: ['', ''], E: ['', ''], F: ['', ''], T: ['', ''],
                    'Temperatura_Maxima_C': ['', '']})
com = base.assign(Temperatura_Maxima_C=['30.1', '28.4', '29.0', '27.7'])
ok, det = k16.conferir_r7(pd.concat([com, sem], ignore_index=True))
confere(ok and '2 sem dado' in det, '[v7.1] linhas sem dado nenhum fora da janela: não contam (' + det + ')')
confere(not k16.conferir_r7(sem)[0], '[v7.1] só linhas sem dado: reprova')
confere(not k16.conferir_r7(pd.concat([com.assign(**{R: ['', '', '19.02', '22.10'], E: ['', '', '3.10', '4.00'],
                                                  F: ['', '', '1.0', '1.5']}), sem], ignore_index=True))[0],
        '[v7.1] linha COM dado e radiação vazia fora da janela (01/03): continua reprovando')
confere([c for c, _ in k16.CASOS][-1] == 'A7' and 'A7' in k16.TELA_PAINEL and
        k16.TELA_PAINEL['A7']['ini'] == '01/03/2026' and 'ini=2026-03-01;fim=2026-03-31' in dict(k16.CASOS)['A7'],
        'A7 igual no e-mail e na tela do painel (Lagoa Mirim, março de 2026)')
confere(k16.RODAR_PARTE_C is False, 'parte C desligada na v7 (medida na v6)')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
