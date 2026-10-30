# Testes das funções puras da rotina de pedidos (sem Earth Engine). Rodar: python testes/teste_sab_pedido.py
# O GitHub Actions roda este arquivo antes de cada pedido: se algum teste falhar, nada é exportado.
import os
import sys
from datetime import date, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import sab_pedido as sp  # noqa: E402

falhas = 0


def confere(cond, msg):
    global falhas
    print(('  ok   ' if cond else '  FALHA ') + msg)
    falhas += 0 if cond else 1


def recusa(codigo, trecho, hoje=date(2026, 10, 29)):
    try:
        sp.validar(sp.ler_codigo(codigo), hoje)
    except sp.PedidoInvalido as e:
        return trecho.lower() in str(e).lower()
    return False


HOJE = date(2026, 10, 29)
print('[nomes, como o painel]')
confere(sp.remover_acentos('Paraná') == 'Parana' and sp.remover_acentos('São João') == 'Sao Joao', 'removerAcentos')
confere(sp.limpar_nome_arquivo('São Paulo') == 'Sao_Paulo' and sp.limpar_nome_arquivo("Pérola d'Oeste") == 'Perola_d_Oeste',
        'limparNomeArquivo')
confere(sp.variacoes_busca(['Pato Branco']) == ['Pato Branco', 'PATO BRANCO'], 'variações sem acento')
confere(sp.variacoes_busca(['Clevelândia']) == ['Clevelândia', 'Clevelandia', 'CLEVELÂNDIA', 'CLEVELANDIA'],
        'variações com acento')
confere(sp.variacoes_busca(['mato grosso do sul']) == ['mato grosso do sul', 'Mato Grosso Do Sul', 'MATO GROSSO DO SUL'],
        'título palavra a palavra, sem repetir')
confere(sp.faltando(['Clevelândia', 'Xyz'], ['Clevelandia', 'Pato Branco']) == ['Xyz'], 'município não achado')
confere(sp.contar_pontos(['B', 'B', 'A', 'B']) == [('B', 3), ('A', 1)], 'contagem na ordem de aparição')

print('[código do pedido]')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=E;uf=parana;ini=2025-01-01;fim=2025-12-31;var=todas'), HOJE)
confere(p['estados'] == ['Paraná'] and p['variaveis'] == sp.CODIGOS and p['res'] == 'D', 'estado sem acento -> Paraná')
p = sp.validar(sp.ler_codigo(' v=1 ; res=m ; tipo=M ; uf=Paraná,Santa Catarina ; mun=Pato Branco, Clevelândia ;'
                             'ini=1991-01-01;fim=2020-12-31;var=tmin,pr; '), HOJE)
confere(p['municipios'] == ['Pato Branco', 'Clevelândia'] and p['estados'] == ['Paraná', 'Santa Catarina'],
        'municípios e estados com espaços')
confere(p['variaveis'] == ['pr', 'tmin'] and p['res'] == 'M', 'variáveis na ordem do painel')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=P;pol=-26.1 -52.7,-26.1 -52.6,-26.2 -52.6,-26.2 -52.7|'
                             '-25.0 -51.0,-25.0 -50.9,-25.1 -50.9,-25.1 -51.0;ini=2025-01-01;fim=2025-03-31'), HOJE)
confere(len(p['poligonos']) == 2 and p['poligonos'][0][0] == [-52.7, -26.1], 'polígonos em [lon, lat]')
confere(sp.nome_local_unico(p) == 'Multiplos_Poligonos', 'nome local de vários polígonos')
confere(recusa('', 'vazio'), 'código vazio')
confere(recusa('v=2;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-01-31', 'versão'), 'versão errada')
confere(recusa('v=1;res=X;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-01-31', 'resolução'), 'resolução errada')
confere(recusa('v=1;res=D;tipo=E;uf=Paraná;ini=1960-12-31;fim=2025-01-31', '1961'), 'antes de 1961')
confere(recusa('v=1;res=D;tipo=E;uf=Paraná;ini=2025-02-01;fim=2025-01-31', 'anterior'), 'fim antes do início')
confere(recusa('v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2026-12-31', 'previsão'), 'fim depois da previsão')
confere(recusa('v=1;res=D;tipo=E;uf=Paraná;ini=2025-13-01;fim=2025-12-31', 'inválida'), 'data inexistente')
confere(recusa('v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-01-31;var=pr,chuva', 'chuva'), 'variável desconhecida')
confere(recusa('v=1;res=D;tipo=E;uf=Atlântida;ini=2025-01-01;fim=2025-01-31', 'Atlântida'), 'estado desconhecido')
confere(recusa('v=1;res=D;tipo=M;uf=Paraná;ini=2025-01-01;fim=2025-01-31', 'município'), 'municípios faltando')
confere(recusa('v=1;res=D;tipo=M;uf=Paraná;mun=' + ','.join(f'M{i:02d}' for i in range(31)) +
               ';ini=2025-01-01;fim=2025-01-31', 'máximo'), 'municípios demais')
confere(recusa('v=1;res=D;tipo=M;uf=Paraná;mun=Pato<script>;ini=2025-01-01;fim=2025-01-31', 'inválido'),
        'nome de município com símbolo')
confere(recusa('v=1;res=D;tipo=P;pol=-26.1 -52.7,-26.1 -52.6,-26.2 -52.6;ini=2025-01-01;fim=2025-01-31', '4 vértices'),
        'polígono com 3 vértices')
confere(recusa('v=1;res=D;tipo=P;pol=40.1 -52.7,-26.1 -52.6,-26.2 -52.6,-26.2 -52.7;ini=2025-01-01;fim=2025-01-31',
               'fora do Brasil'), 'vértice fora do Brasil')
confere(recusa('v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-01-31;var=', 'x') is False,
        'var vazio = todas (aceito)')

print('[colunas, como o painel 2026.10.4]')
PAINEL_BASE = ['Tipo_Dado', 'Versao_Algoritmo', 'Data_Completa', 'Ano', 'Mes', 'Dia', 'N_Ponto', 'Latitude',
               'Longitude', 'Estado', 'Municipio', 'Precipitacao_mm', 'Chuva_Efetiva_mm', 'Runoff_Superficial_mm',
               'Runoff_Subsuperficial_mm', 'Temperatura_Maxima_C', 'Temperatura_Minima_C', 'Amplitude_Termica_C',
               'Temperatura_Solo_C', 'Temperatura_Folha_C', 'Umidade_Relativa_Porc', 'Vento_ms',
               'Radiacao_Solar_MJ_m2', 'Evapotranspiracao_Potencial_mm', 'Evapotranspiracao_Real_mm',
               'Transpiracao_Planta_mm', 'Deficit_Hidrico_mm', 'Deficit_Pressao_Vapor_kPa',
               'Umidade_Volumetrica_Solo_0_5cm_m3_m3', 'Umidade_Volumetrica_Solo_0_100cm_m3_m3']
confere(sp.colunas_do_pedido('D', sp.CODIGOS) == PAINEL_BASE + ['Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo'],
        'diária com todas = 33 colunas do painel, na ordem')
confere(sp.colunas_do_pedido('M', sp.CODIGOS) == PAINEL_BASE + ['N_Dias', 'Dias_no_Mes', 'Mes_Completo'],
        'mensal com todas = colunas do painel')
confere(sp.colunas_do_pedido('D', ['pr', 'tmax']) == PAINEL_BASE[:11] + ['Precipitacao_mm', 'Temperatura_Maxima_C',
                                                                          'Qualidade_Pixel', 'Janela_Chuva_UTC',
                                                                          'Confianca_Prazo'], 'subconjunto')
confere(sp.bandas_do_pedido(['amp', 'def']) == ['amplitude_diaria', 'deficit_diario'], 'bandas derivadas')
confere(set(sp.BANDAS_SOMA) | set(sp.BANDAS_MEDIA) == {v[2] for v in sp.VARIAVEIS}, 'soma + média = 19 bandas')
confere(len(sp.DICIONARIO) == 35 and sp.DICIONARIO[0][0] == 'Tipo_Dado', 'dicionário do painel (35 linhas)')

print('[plano de arquivos]')
ano = [date(2025, 1, 1) + timedelta(days=i) for i in range(365)]
a = sp.planejar('D', [('Paraná', 1889)], ano)
confere(len(a) == 1 and a[0]['nome'] == 'Diaria_Parana_2025' and a[0]['linhas'] == 1889 * 365, 'Paraná 2025: 1 arquivo')
a = sp.planejar('D', [('Minas Gerais', 5000)], ano)
confere([x['nome'] for x in a] == ['Diaria_Minas_Gerais_2025_parte1de2', 'Diaria_Minas_Gerais_2025_parte2de2'] and
        a[0]['fim'] == date(2025, 7, 1) and a[1]['ini'] == date(2025, 7, 1) and a[1]['fim'] == date(2026, 1, 1),
        'ano acima de 1 milhão: 2 blocos de 6 meses')
confere(all(x['linhas'] <= sp.LIMITE_LINHAS_ARQUIVO for x in a) and sum(x['linhas'] for x in a) == 5000 * 365,
        'blocos sem perder linhas')
a = sp.planejar('D', [('Grupo_Estados', 24000)], ano)
confere(len(a) == 12 and sum(x['linhas'] for x in a) == 24000 * 365, '24 mil pontos: 12 blocos mensais')
a = sp.planejar('D', [('Pato Branco', 7), ('Clevelândia', 5)], [date(2024, 12, 30), date(2024, 12, 31), date(2025, 1, 1)])
confere([(x['nome'], x['linhas']) for x in a] == [('Diaria_Pato_Branco_2024', 14), ('Diaria_Pato_Branco_2025', 7),
                                                  ('Diaria_Clevelandia_2024', 10), ('Diaria_Clevelandia_2025', 5)],
        'um arquivo por local e por ano')
a = sp.planejar('M', [('Paraná', 1889)], ano + [date(2026, 1, 1)])
confere([(x['nome'], x['linhas']) for x in a] == [('Mensal_Parana_2025', 1889 * 12), ('Mensal_Parana_2026', 1889)],
        'mensal: meses com dados')
a = sp.planejar('D', [('X', 2)], [date(2025, 1, 1), date(2025, 1, 1)])
confere(a[0]['linhas'] == 4, 'imagem repetida conta duas vezes (como no CSV)')

print('[limites]')


def limite(*args):
    try:
        sp.conferir_limites(*args)
    except sp.PedidoInvalido as e:
        return str(e)
    return ''


ok = sp.planejar('D', [('Paraná', 1889)], ano)
confere(limite(1889, [('Paraná', 1889)], ok) == '', 'Paraná 2025 aceito')
confere('25.000' in limite(25001, [('X', 25000)], ok), 'mais pares que o painel aceita')
confere('Nenhum ponto' in limite(0, [], []), 'sem pontos')
confere('período' in limite(10, [('X', 10)], []), 'sem dados no período')
muitos = sp.planejar('D', [('Paraná', 1889)], [date(2000 + i // 365, 1, 1) + timedelta(days=i % 365) for i in range(365 * 8)])
confere(limite(1889, [('Paraná', 1889)], muitos) == '', '8 anos do Paraná (5,5 milhões): aceito')
muitos = sp.planejar('D', [('Paraná', 1889)], [date(2000, 1, 1) + timedelta(days=i) for i in range(365 * 16)])
confere('10.000.000' in limite(1889, [('Paraná', 1889)], muitos), '16 anos do Paraná (11 milhões): recusado')
mil = [{'nome': f'f{i}', 'linhas': 1} for i in range(201)]
confere('201 arquivos' in limite(10, [('X', 10)], mil), 'arquivos demais')

print('[manifesto e nomes das tarefas]')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=pr'), HOJE)
arqs = sp.planejar('D', [('Pato Branco', 14)], ano)
m = sp.linhas_manifesto('P1', 'aceito', '', p, arqs)
confere(len(m) == 3 and m[0]['Arquivo'] == '' and m[1]['Arquivo'] == 'Diaria_Pato_Branco_2025.csv' and
        m[2]['Arquivo'] == '00_Dicionario_Variaveis_SAB.csv' and m[0]['Linhas_Esperadas'] == str(14 * 365),
        'manifesto: resumo + arquivos + dicionário')
confere(all(set(l) == set(sp.COLUNAS_MANIFESTO) for l in m), 'manifesto com as colunas fixas')
r = sp.linhas_manifesto('P1', 'recusado', 'motivo', None)
confere(len(r) == 1 and r[0]['Status'] == 'recusado' and r[0]['Local'] == '', 'manifesto de recusa (pedido ilegível)')
confere(sp.descricao_tarefa('P20261029', 7) == 'SABPED_P20261029_007' and sp.pasta_do_pedido('P1') == 'SAB_pedido_P1',
        'nomes de tarefa e de pasta')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
