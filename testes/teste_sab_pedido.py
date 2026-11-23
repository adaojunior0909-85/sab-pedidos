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

print('[Brasil inteiro desativado, estados e pontos]')
confere(recusa('v=1;res=M;tipo=BR;ini=2015-01-01;fim=2024-12-31;var=pr', 'Brasil inteiro foi desativado'),
        'tipo=BR recusado com explicação (estouro de memória de 31/10)')
confere(recusa('v=1;res=D;tipo=E;uf=' + ','.join(sp.LISTA_ESTADOS[:7]) + ';sep=1;ini=2025-01-01;fim=2025-01-31',
               'No máximo 6 estados'), 'sete estados: recusado (todos os estados = Brasil inteiro)')
confere(not recusa('v=1;res=D;tipo=E;uf=' + ','.join(sp.LISTA_ESTADOS[:6]) + ';sep=1;ini=2025-01-01;fim=2025-01-31',
                   'x'), 'seis estados: aceito')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=C;pts=-26.2285 -52.6712 Fazenda São João|-25.4 -49.27;'
                             'ini=2024-01-01;fim=2024-12-31'), HOJE)
confere([x['nome'] for x in p['pontos']] == ['Fazenda São João', 'Ponto 2'] and p['pontos'][0]['lat'] == -26.2285,
        'pontos com e sem nome')
confere(recusa('v=1;res=D;tipo=C;pts=-26.2 abc;ini=2024-01-01;fim=2024-12-31', 'inválido'), 'ponto ilegível')
confere(recusa('v=1;res=D;tipo=C;pts=10.0 -52.0;ini=2024-01-01;fim=2024-12-31', 'fora do Brasil'), 'ponto fora do Brasil')
confere(recusa('v=1;res=D;tipo=C;pts=' + '|'.join('-26.2 -52.6' for _ in range(201)) + ';ini=2024-01-01;fim=2024-12-31',
               'máximo'), 'mais de 200 pontos')
lat, lon = sp.centro_do_pixel(-26.30, -52.66)
confere(f'{lat:.5f}' == '-26.34952' and abs(lon - (-52.65033)) < 1e-4, 'centro do pixel igual ao da grade do painel (-26.34952)')
confere(sp.centro_do_pixel(*sp.centro_do_pixel(-26.30, -52.66)) == sp.centro_do_pixel(-26.30, -52.66), 'centro do centro é ele mesmo')
ach, falt = sp.casar_municipios(['clevelandia', 'PATO BRANCO', 'sao joao d oeste', 'Patoo Branco'],
                                ['Clevelândia', 'Pato Branco', "São João d'Oeste"])
confere(ach == ['Clevelândia', 'Pato Branco', "São João d'Oeste"], 'municípios sem acento, maiúsculas e apóstrofo')
confere(falt == ['Patoo Branco (talvez: Pato Branco)'], 'município errado com sugestão')

p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=E;uf=Paraná,Santa Catarina;sep=1;ini=2025-01-01;fim=2025-12-31'), HOJE)
confere(p['separar'] and 'um arquivo por estado' in sp.texto_local(p), 'estados separados (formulário)')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=E;uf=Paraná,Santa Catarina;ini=2025-01-01;fim=2025-12-31'), HOJE)
confere(not p['separar'], 'estados sem sep = Grupo_Estados, como o painel')

print('[ENSO, como o painel]')
serie = [{'ano': 2000, 'mes': m, 'RONI': r, 'Trimestre': sp.TRIMESTRES[m - 1]}
         for m, r in zip(range(1, 13), [0.1, 0.6, 0.7, 0.9, 1.2, 0.8, 0.2, 0.0, -0.6, -0.7, -0.5, -0.8])]
c = sp.classificar_enso(serie)
confere([x['FaseENSO'] for x in c] == ['Neutro'] + ['El Nino'] * 5 + ['Neutro'] * 2 + ['Indefinida'] * 4,
        '5 estações acima de +0,5 = El Niño; sinal que continua até o fim sem fechar 5 = Indefinida')
c2 = sp.classificar_enso(serie + [{'ano': 2001, 'mes': 1, 'RONI': -0.9, 'Trimestre': 'DJF'}])
confere([x['FaseENSO'] for x in c2[8:]] == ['La Nina'] * 5, 'com a 5ª estação, a La Niña se confirma')
confere(sp.no_cenario({'FaseENSO': 'El Nino', 'RONI': 1.2}, 'El Niño Moderado (1.0 a 1.4°C)') and
        not sp.no_cenario({'FaseENSO': 'El Nino', 'RONI': 1.5}, 'El Niño Moderado (1.0 a 1.4°C)') and
        sp.no_cenario({'FaseENSO': 'El Nino', 'RONI': 1.5}, 'El Niño Forte (1.5 a 1.9°C)') and
        sp.no_cenario({'FaseENSO': 'La Nina', 'RONI': -2.0}, 'Super La Niña (≤ -2.0°C)') and
        sp.no_cenario({'FaseENSO': 'Neutro', 'RONI': 0.6}, 'Anos Neutros') and
        not sp.no_cenario({'FaseENSO': 'Indefinida', 'RONI': 0.6}, 'El Niño Fraco (0.5 a 0.9°C)'),
        'limites dos cenários iguais ao filtroCenario do painel')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=E;uf=Paraná;ini=2015-01-01;fim=2016-12-31;enso=El_Nino_Muito_Forte'), HOJE)
confere(p['enso']['valor'] == 'Super El Niño (≥ 2.0°C)' and 'filtro ENSO' in sp.texto_periodo(p), 'código com enso')
confere(recusa('v=1;res=D;tipo=E;uf=Paraná;ini=2015-01-01;fim=2016-12-31;enso=Chuvoso', 'ENSO'), 'cenário desconhecido')
a = sp.planejar('D', [('Pato Branco', 14)], [date(2015, 10, 1), date(2016, 1, 1)], sufixo='_El_Nino_Muito_Forte')
confere([x['nome'] for x in a] == ['Diaria_Pato_Branco_2015_El_Nino_Muito_Forte', 'Diaria_Pato_Branco_2016_El_Nino_Muito_Forte'],
        'nomes com o sufixo do painel')
confere(sp.colunas_do_pedido('D', sp.CODIGOS)[-6:] == sp.COLUNAS_ENSO and sp.COLUNAS_ENSO[:5] == sp.COLUNAS_ENSO_PAINEL
        and sp.COLUNAS_ENSO[5] == 'Fonte_ENSO', 'e-mail: 6 colunas ENSO no fim, sempre (5 do painel + Fonte_ENSO)')
for chave in ('', ';enso=sem filtro', ';enso=Todos'):
    p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=E;uf=Paraná;ini=2015-01-01;fim=2016-12-31' + chave), HOJE)
    confere(p['enso'] is None and 'ENSO' not in sp.texto_periodo(p), f'sem filtro ENSO ({chave or "sem enso"})')

print('[ENSO: série do painel + extensão até a previsão]')
of = [{'ano': 2026, 'mes': m, 'RONI': r, 'Trimestre': sp.TRIMESTRES[m - 1], 'Fonte': 'CPC'}
      for m, r in zip(range(1, 8), [-0.6, -0.5, -0.3, 0.0, 0.2, 0.4, 0.5])]
est = [{'ano': 2026, 'mes': 6, 'RONI': 0.4, 'n_meses': 3}, {'ano': 2026, 'mes': 8, 'RONI': 0.6, 'n_meses': 3},
       {'ano': 2026, 'mes': 9, 'RONI': 0.8, 'n_meses': 2}, {'ano': 1991, 'mes': 1, 'RONI': 0.1, 'n_meses': 2}]
serie, parc = sp.juntar_roni(of, est)
confere([(x['mes'], x['Fonte']) for x in serie[-2:]] == [(7, 'CPC'), (8, 'Estimativa_OISST')] and len(serie) == 8,
        'série do painel: CPC + OISST completo só depois da última estação oficial')
confere([(x['mes'], x['Fonte'], x['Trimestre']) for x in parc] == [(9, 'Estimativa_OISST_parcial', 'ASO')],
        'parcial: só o trimestre de 2 meses depois do fim da série')
ext = sp.estender_enso(sp.classificar_enso(serie), parc, date(2026, 11, 20))
confere([(x['mes'], x['Fonte']) for x in ext[-3:]] == [(9, 'Estimativa_OISST_parcial'), (10, 'Persistencia'),
                                                       (11, 'Persistencia')], 'extensão: parcial e depois persistência')
confere(ext[-1]['RONI'] == 0.8 and ext[-1]['Trimestre'] == 'ASO' and ext[-1]['FaseENSO'] == 'Indefinida',
        'persistência copia o último valor e o trimestre; sinal de El Niño sem 5 trimestres = Indefinida')
dic = sp.dicionario_enso(ext)
confere(dic['2026_11'] == ['Indefinida', 0.8, 'ASO', 'Persistencia'] and dic['2026_01'][3] == 'CPC', 'dicionário AAAA_MM')
c3 = sp.classificar_enso([{'ano': 2015, 'mes': m, 'RONI': 1.6, 'Trimestre': sp.TRIMESTRES[m - 1], 'Fonte': 'CPC'}
                          for m in range(1, 13)])
e3 = sp.estender_enso(c3, [], date(2016, 2, 1))
confere([x['FaseENSO'] for x in e3[-2:]] == ['El Nino', 'El Nino'], 'persistência mantém um El Niño confirmado')
confere(sp.estender_enso([], [], date(2026, 1, 1)) == [], 'série vazia não quebra')
confere(not sp.no_cenario({'FaseENSO': 'Indefinida', 'RONI': 0.8}, 'El Niño Fraco (0.5 a 0.9°C)'),
        'meses estendidos (Indefinida) fora dos filtros')

print('[formato e estimativa de tamanho antes do Earth Engine]')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;fmt=xlsx'), HOJE)
confere(p['formato'] == 'xlsx' and 'Excel' in sp.texto_periodo(p), 'fmt=xlsx')
confere(sp.validar(sp.ler_codigo('v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31'),
                   HOJE)['formato'] == 'csv', 'sem fmt = csv')
confere(recusa('v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;fmt=pdf', 'Formato'),
        'formato desconhecido')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-12-31'), HOJE)
lin, px = sp.estimar_linhas(p)
confere(1700 <= px <= 2100 and abs(lin / 365 - px) < 1, f'Paraná: ~{px} pixels estimados (grade real 1.889)')
confere(sp.conferir_estimativa(p) == lin, 'Paraná 2025: estimativa aceita')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=E;uf=Paraná;ini=1961-01-01;fim=2026-11-15'), HOJE)
try:
    sp.conferir_estimativa(p)
    confere(False, 'Paraná 1961-2026 diário deveria ser recusado na hora')
except sp.PedidoInvalido as e:
    confere('Divida' in str(e), 'Paraná 1961-2026 diário (~45 milhões): recusado sem Earth Engine')
p = sp.validar(sp.ler_codigo('v=1;res=M;tipo=E;uf=Paraná;ini=1961-01-01;fim=2026-10-31'), HOJE)
confere(sp.conferir_estimativa(p) > 0, 'Paraná 1961-2026 mensal (~1,5 milhão): aceito')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=P;pol=-26.2 -52.7,-26.2 -52.6,-26.3 -52.6,-26.3 -52.7;'
                             'ini=2025-01-01;fim=2025-03-31'), HOJE)
confere(sp.estimar_linhas(p)[1] <= 12, 'polígono de 0,1° x 0,1°: poucos pixels')
confere(sp.e_pedido_grande(RuntimeError('User memory limit exceeded.')) and
        not sp.e_pedido_grande(RuntimeError('Too many concurrent aggregations')), 'erro de memória vira recusa explicada')

print('[colunas, como o painel 2026.10.4]')
PAINEL_BASE = ['Tipo_Dado', 'Versao_Algoritmo', 'Data_Completa', 'Ano', 'Mes', 'Dia', 'N_Ponto', 'Latitude',
               'Longitude', 'Estado', 'Municipio', 'Precipitacao_mm', 'Chuva_Efetiva_mm', 'Runoff_Superficial_mm',
               'Runoff_Subsuperficial_mm', 'Temperatura_Maxima_C', 'Temperatura_Minima_C', 'Amplitude_Termica_C',
               'Temperatura_Solo_C', 'Temperatura_Folha_C', 'Umidade_Relativa_Porc', 'Vento_ms',
               'Radiacao_Solar_MJ_m2', 'Evapotranspiracao_Potencial_mm', 'Evapotranspiracao_Real_mm',
               'Transpiracao_Planta_mm', 'Deficit_Hidrico_mm', 'Deficit_Pressao_Vapor_kPa',
               'Umidade_Volumetrica_Solo_0_5cm_m3_m3', 'Umidade_Volumetrica_Solo_0_100cm_m3_m3']
confere(sp.colunas_do_pedido('D', sp.CODIGOS, enso=False) == PAINEL_BASE + ['Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo'],
        'diária com todas = 33 colunas do painel, na ordem')
confere(sp.colunas_do_pedido('M', sp.CODIGOS, enso=False) == PAINEL_BASE + ['N_Dias', 'Dias_no_Mes', 'Mes_Completo'],
        'mensal com todas = colunas do painel')
confere(sp.colunas_do_pedido('M', sp.CODIGOS) == PAINEL_BASE + ['N_Dias', 'Dias_no_Mes', 'Mes_Completo'] + sp.COLUNAS_ENSO,
        'e-mail: colunas do painel + 6 ENSO')
confere(sp.colunas_do_pedido('D', ['pr', 'tmax'], enso=False) == PAINEL_BASE[:11] + ['Precipitacao_mm', 'Temperatura_Maxima_C',
                                                                          'Qualidade_Pixel', 'Janela_Chuva_UTC',
                                                                          'Confianca_Prazo'], 'subconjunto')
confere(sp.bandas_do_pedido(['amp', 'def']) == ['amplitude_diaria', 'deficit_diario'], 'bandas derivadas')
confere(set(sp.BANDAS_SOMA) | set(sp.BANDAS_MEDIA) == {v[2] for v in sp.VARIAVEIS}, 'soma + média = 19 bandas')
confere(len(sp.DICIONARIO) == 36 and sp.DICIONARIO[0][0] == 'Tipo_Dado' and
        any(v == 'Fonte_ENSO' for v, _, _ in sp.DICIONARIO), 'dicionário: 35 do painel + Fonte_ENSO')
confere(all(',' not in u for _, _, u in sp.DICIONARIO) and 'UTF-8' in dict((v, d) for v, d, _ in sp.DICIONARIO)[
    '(formato dos numeros)'], 'dicionário explica a importação no Excel (UTF-8, não detectar tipos)')

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
mil = [{'nome': f'f{i}', 'linhas': 1} for i in range(401)]
confere('401 arquivos' in limite(10, [('X', 10)], mil), 'arquivos demais')

print('[manifesto e nomes das tarefas]')
p = sp.validar(sp.ler_codigo('v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=pr'), HOJE)
arqs = sp.planejar('D', [('Pato Branco', 14)], ano)
m = sp.linhas_manifesto('P1', 'aceito', '', p, arqs)
confere(len(m) == 3 and m[0]['Arquivo'] == '' and m[1]['Arquivo'] == 'Diaria_Pato_Branco_2025.csv' and
        m[2]['Arquivo'] == '00_Dicionario_Variaveis_SAB.csv' and m[0]['Linhas_Esperadas'] == str(14 * 365),
        'manifesto: resumo + arquivos + dicionário')
confere(all(set(l) == set(sp.COLUNAS_MANIFESTO) for l in m) and m[0]['Formato'] == 'csv', 'manifesto com as colunas fixas')
r = sp.linhas_manifesto('P1', 'recusado', 'motivo', None)
confere(len(r) == 1 and r[0]['Status'] == 'recusado' and r[0]['Local'] == '', 'manifesto de recusa (pedido ilegível)')
confere(sp.descricao_tarefa('P20261029', 7) == 'SABPED_P20261029_007' and sp.pasta_do_pedido('P1') == 'SAB_pedido_P1',
        'nomes de tarefa e de pasta')
confere(sp.descricao_tarefa('SAB2026-00001', 0) == 'SABPED_SAB2026-00001_000', 'ID sequencial do Apps Script')

print('[2026.11.18: pedido de uma variável só (coluna vazia)]')


class _RedutorFalso:
    """Imita ee.Reducer.mean(): guarda o nome da saída que o Earth Engine daria à média."""
    def __init__(self, saidas=None):
        self.saidas = saidas

    def setOutputs(self, saidas):
        return _RedutorFalso(list(saidas))


_ee_original = sp._ee
sp._ee = lambda: type('EEFalso', (), {'Reducer': type('R', (), {'mean': staticmethod(_RedutorFalso)})})
try:
    for cod in sp.CODIGOS:                      # cada uma das 19 variáveis pedida sozinha
        bandas = sp.bandas_do_pedido([cod])
        r = sp._redutor_media(bandas)
        confere(len(bandas) == 1 and r.saidas == bandas, f'só {cod}: a média sai com o nome da banda {bandas}')
    confere(sp._redutor_media(sp.bandas_do_pedido(['pr', 'tmax'])).saidas is None,
            '2 variáveis: redutor sem mudança (nomes das bandas pelo próprio Earth Engine, K16 igual)')
    confere(sp._redutor_media(sp.bandas_do_pedido(sp.CODIGOS)).saidas is None, 'todas: redutor sem mudança')
finally:
    sp._ee = _ee_original

print('[2026.11.22: radiação abaixo de 3% de Ra sai vazia, com a ETo e o déficit do dia]')


class _ImgFalsa:
    """Imagem de UM pixel: {banda: (valor, máscara)}; só as operações que vazio_rs_impossivel usa."""
    def __init__(self, bandas):
        self.b = bandas

    def select(self, nomes):
        return _ImgFalsa({n: self.b[n] for n in ([nomes] if isinstance(nomes, str) else nomes)})

    def date(self):
        return None

    def gte(self, ra):
        (v, m), = self.b.values()
        return _ImgFalsa({'ok': (1 if v >= ra.valor else 0, 1)})

    def updateMask(self, ok):
        return _ImgFalsa({n: (v, m * ok.b['ok'][0]) for n, (v, m) in self.b.items()})

    def addBands(self, outra, nomes, sobrescrever):
        assert nomes is None and sobrescrever is True
        return _ImgFalsa({**self.b, **outra.b})


class _Ra:
    def __init__(self, v):
        self.valor = v

    def multiply(self, k):
        return _Ra(self.valor * k)


_ra_original = sp._radiacao_topo
sp._radiacao_topo = lambda data: _Ra(30.0)                  # Ra = 30 MJ/m²: o limite é 0,9 MJ/m²
try:
    for rs, vazio in ((0.0, True), (0.89, True), (0.9, False), (18.4, False)):
        img = _ImgFalsa({'rs': (rs, 1), 'et_potencial': (2.3, 1), 'deficit_diario': (1.0, 1), 'et_real': (1.3, 1),
                         'pr_mm': (0.0, 1), 'tmax_C': (29.0, 1)})
        s_ = sp.vazio_rs_impossivel(img).b
        m = 0 if vazio else 1
        confere(s_['rs'] == (rs, m) and s_['et_potencial'] == (2.3, m) and s_['deficit_diario'] == (1.0, m) and
                s_['et_real'] == (1.3, 1) and s_['pr_mm'] == (0.0, 1) and s_['tmax_C'] == (29.0, 1),
                f'Rs {rs} com Ra 30: Rs, ETo e déficit {"vazios" if vazio else "ficam"}; ET real, chuva e Tmax iguais')
finally:
    sp._radiacao_topo = _ra_original
confere(sp.BANDAS_RS_IMPOSSIVEL == ['rs', 'et_potencial', 'deficit_diario'], 'as 3 bandas que a regra esvazia')
fonte = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sab_pedido.py'), encoding='utf-8').read()
corpo = fonte[fonte.index('def colecao('):fonte.index('def props_enso(')]
confere(corpo.index('corrigir_pixels_b(im)') < corpo.index("im.select('et_real').min(etp)") <
        corpo.index('return vazio_rs_impossivel(im.addBands('),
        'colecao: a regra vem depois da correção B e do grampo (a ET real não muda), nos dois caminhos')
desc = {v: d for v, d, u in sp.DICIONARIO}['Radiacao_Solar_MJ_m2']
confere('3% da radiacao no topo da atmosfera' in desc and 'Evapotranspiracao_Potencial_mm' in desc and 'K26' in desc,
        'dicionário explica a célula vazia da radiação, da ETo e do déficit')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
