# Fumaça: roda a rotina inteira (atender) com um Earth Engine simulado. Só para conferência local;
# o GitHub Actions não roda este arquivo. Rodar: python testes/fumaca_sab_pedido.py
import os
import sys
import types
from datetime import date, datetime, timedelta, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
EXPORTS, INFO, OPS = [], {}, []


class D:
    def __getattr__(self, n):
        if n == 'getInfo':                      # lista de municípios do GAUL (resolver_municipios)
            return lambda *a, **k: list(INFO.get('nomes', []))
        return lambda *a, **k: D()

    def __call__(self, *a, **k):
        return D()


class Dicionario(D):
    def __init__(self, *a, **k):
        pass

    def getInfo(self):
        if INFO.get('erro'):
            raise RuntimeError(INFO['erro'])
        return INFO


class Tarefa:
    def __init__(self, **k):
        self.k, self.id = k, 'T%03d' % (len(EXPORTS) + 1)

    def start(self):
        EXPORTS.append(self.k)


ee = types.ModuleType('ee')
for nome in ('Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Geometry', 'Filter', 'Reducer', 'Date',
             'Algorithms', 'Number', 'List', 'String', 'Projection', 'Join'):
    setattr(ee, nome, D())
ee.Dictionary = Dicionario
Dicionario.fromLists = staticmethod(lambda *a, **k: D())
ee.Initialize = lambda **k: None
ee.__version__ = 'falso'
ee.batch = types.SimpleNamespace(Export=types.SimpleNamespace(table=types.SimpleNamespace(toDrive=lambda **k: Tarefa(**k))))
ee.data = types.SimpleNamespace(listOperations=lambda: OPS, getTaskStatus=lambda ids: [{'id': i, 'state': 'COMPLETED'} for i in ids])
sys.modules['ee'] = ee

import sab_pedido as sp  # noqa: E402

MANIFESTOS = []
_tabela = sp.tabela_ee
sp.tabela_ee = lambda linhas, colunas: (MANIFESTOS.append(linhas), _tabela(linhas, colunas))[1]
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


def ms(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)


def rodar(pid, codigo, simular, info, ops=()):
    EXPORTS.clear(), MANIFESTOS.clear(), INFO.clear(), OPS.clear()
    INFO.update(info)
    OPS.extend(ops)
    return sp.atender(pid, codigo, simular, hoje=date(2026, 10, 29))


ANO = [ms(date(2025, 1, 1) + timedelta(days=i)) for i in range(365)]
PB = {'pares': 14, 'nomes': ['Pato Branco'], 'estados': ['Parana'], 'pontos': ['Pato Branco'] * 14, 'datas': ANO}
COD = 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=pr,tmax'

print('\n[1] simulação: confere e mostra o plano, sem exportar')
confere(rodar('TESTE01', COD, True, PB) == 0 and not EXPORTS, 'nada exportado')

print('\n[2] exportação: manifesto, dicionário e 1 arquivo por ano')
confere(rodar('P20261029A', COD, False, PB) == 0, 'terminou')
confere([e['fileNamePrefix'] for e in EXPORTS] == ['00_Pedido_P20261029A', '00_Dicionario_Variaveis_SAB',
                                                    'Diaria_Pato_Branco_2025'], 'ordem: manifesto, dicionário, dados')
confere(all(e['folder'] == 'SAB_pedido_P20261029A' for e in EXPORTS), 'pasta própria do pedido')
confere([e['description'] for e in EXPORTS] == ['SABPED_P20261029A_000', 'SABPED_P20261029A_001',
                                                'SABPED_P20261029A_002'], 'descrições das tarefas')
confere(EXPORTS[2]['selectors'] == sp.COLUNAS_ID + ['Precipitacao_mm', 'Temperatura_Maxima_C'] + sp.EXTRAS_DIARIA +
        sp.COLUNAS_ENSO, 'colunas pedidas + identificação + qualidade + 6 colunas ENSO (sempre)')
confere('Série RONI indisponível' in MANIFESTOS[0][0]['Motivo'],
        'sem a série RONI e sem filtro: o pedido segue, com aviso no manifesto')
m = MANIFESTOS[0]
confere(m[0]['Status'] == 'aceito' and m[1]['Arquivo'] == 'Diaria_Pato_Branco_2025.csv' and
        m[1]['Linhas_Esperadas'] == str(14 * 365), 'manifesto aceito com os arquivos e as linhas')

print('\n[3] rodar de novo o mesmo pedido não reenvia (idempotente)')
ops = [{'metadata': {'description': f'SABPED_P20261029A_00{i}', 'state': 'RUNNING'}} for i in range(3)]
rodar('P20261029A', COD, False, PB, ops)
confere(not EXPORTS, 'nenhuma tarefa repetida')
ops[2]['metadata']['state'] = 'FAILED'
rodar('P20261029A', COD, False, PB, ops)
confere([e['fileNamePrefix'] for e in EXPORTS] == ['Diaria_Pato_Branco_2025'], 'só a que falhou é reenviada')

print('\n[4] pedido fora das regras: só o manifesto de recusa')
rodar('P0002', COD.replace('mun=Pato Branco', 'mun=Pato Brancoo'), False,
      dict(PB, nomes=[]))
confere(len(EXPORTS) == 1 and MANIFESTOS[0][0]['Status'] == 'recusado' and 'Pato Brancoo' in MANIFESTOS[0][0]['Motivo'],
        'município inexistente recusado com o nome no motivo')
rodar('P0003', 'v=1;res=D;tipo=E;uf=Paraná;ini=1950-01-01;fim=2025-12-31', False, PB)
confere(len(EXPORTS) == 1 and '1961' in MANIFESTOS[0][0]['Motivo'], 'data antes de 1961 recusada')
grande = {'pares': 1889, 'nomes': ['Paraná'], 'estados': ['Parana'], 'pontos': ['Paraná'] * 1889,
          'datas': [ms(date(2000, 1, 1) + timedelta(days=i)) for i in range(365 * 16)]}
rodar('P0004', 'v=1;res=D;tipo=E;uf=Paraná;ini=2000-01-01;fim=2015-12-31', False, grande)
confere(len(EXPORTS) == 1 and 'limite' in MANIFESTOS[0][0]['Motivo'], '16 anos do Paraná: recusado pelo limite de linhas')

print('\n[5] erro do servidor: manifesto de falha e a execução é marcada')
try:
    rodar('P0005', COD, False, dict(PB, erro='Internal error'))
    confere(False, 'deveria ter levantado o erro')
except RuntimeError:
    confere(len(EXPORTS) == 1 and MANIFESTOS[0][0]['Status'] == 'falha' and 'Internal' in MANIFESTOS[0][0]['Motivo'],
            'manifesto de falha com a mensagem do servidor')
confere(rodar('P0005B', COD, False, dict(PB, erro='User memory limit exceeded.')) == 0 and
        MANIFESTOS[0][0]['Status'] == 'recusado' and 'Divida' in MANIFESTOS[0][0]['Motivo'],
        'estouro de memória (31/10): recusa explicada, sem falha')

print('\n[6] ID inválido não exporta nada')
confere(rodar('a b', COD, False, PB) == 2 and not EXPORTS, 'recusado antes de tudo')

print('\n[7] mensal, 2 municípios, todas as variáveis')
info = {'pares': 12, 'nomes': ['Pato Branco', 'Clevelandia'], 'estados': ['Parana', 'Parana'],
        'pontos': ['Clevelandia'] * 5 + ['Pato Branco'] * 7, 'datas': ANO}
rodar('P0007', 'v=1;res=M;tipo=M;uf=Paraná;mun=Pato Branco,Clevelândia;ini=2025-01-01;fim=2025-12-31', False, info)
confere([e['fileNamePrefix'] for e in EXPORTS[2:]] == ['Mensal_Clevelandia_2025', 'Mensal_Pato_Branco_2025'],
        'um arquivo mensal por município')
confere(EXPORTS[2]['selectors'] == sp.colunas_do_pedido('M', sp.CODIGOS), 'colunas mensais do painel')

print('\n[8] Brasil inteiro desativado; pedido gigante recusado antes do Earth Engine')
rodar('P0008', 'v=1;res=D;tipo=BR;ini=1961-01-01;fim=2026-11-15;var=todas', False, {'erro': 'não devia chamar o EE'})
confere(len(EXPORTS) == 1 and MANIFESTOS[0][0]['Status'] == 'recusado' and 'Brasil inteiro' in MANIFESTOS[0][0]['Motivo'],
        'o pedido de 31/10 (P20261031213150mffz) agora é recusado com explicação')
rodar('P0008B', 'v=1;res=D;tipo=E;uf=Amazonas,Pará;sep=1;ini=1961-01-01;fim=2026-11-15', False, {'erro': 'não devia chamar'})
confere(MANIFESTOS[0][0]['Status'] == 'recusado' and 'cerca de' in MANIFESTOS[0][0]['Motivo'],
        'Amazonas + Pará 1961-2026: recusado pela estimativa, sem tocar no Earth Engine')

print('\n[9] pontos: o de borda sai, com aviso')
pts = {'classes': [1, 4, 3], 'idx': [0, 1, 2], 'datas': ANO}
rodar('P0009', 'v=1;res=D;tipo=C;pts=-26.2285 -52.6712 Fazenda A|-33.7 -53.4 Chui|-25.4 -49.27 Curitiba;'
               'ini=2025-01-01;fim=2025-12-31;var=pr', False, pts)
confere([e['fileNamePrefix'] for e in EXPORTS[2:]] == ['Diaria_Pontos_2025'], 'um arquivo com os pontos')
confere(MANIFESTOS[0][1]['Linhas_Esperadas'] == str(2 * 365) and 'Chui' in MANIFESTOS[0][0]['Motivo'],
        '2 pontos no arquivo e o de borda no aviso')

print('\n[11] estados escolhidos no formulário: um arquivo por estado')
dois = {'n': {'Paraná': 1889, 'Santa Catarina': 1100}, 'pares': {'Paraná': 1889, 'Santa Catarina': 1100}, 'datas': ANO}
rodar('P0011', 'v=1;res=D;tipo=E;uf=Paraná,Santa Catarina;sep=1;ini=2025-01-01;fim=2025-12-31;var=pr', False, dois)
confere([e['fileNamePrefix'] for e in EXPORTS[2:]] == ['Diaria_Parana_2025', 'Diaria_Santa_Catarina_2025'],
        'Paraná e Santa Catarina em arquivos separados')

print('\n[12] filtro ENSO: só os meses do cenário, com as colunas ENSO')
of = [{'ano': 2024, 'mes': m, 'RONI': 0.0} for m in range(1, 10)] + \
     [{'ano': 2024, 'mes': m, 'RONI': -0.6} for m in range(10, 13)] + \
     [{'ano': 2025, 'mes': m, 'RONI': -0.6} for m in range(1, 5)] + [{'ano': 2025, 'mes': m, 'RONI': 0.0} for m in range(5, 10)]
enso = dict(PB, of=of, est=[], t=ANO, v=['definitiva'] * 365)
rodar('P0012', 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=pr;enso=La_Nina_Fraca', False, enso)
confere([e['fileNamePrefix'] for e in EXPORTS[2:]] == ['Diaria_Pato_Branco_2025_La_Nina_Fraca'], 'nome com o sufixo do cenário')
confere(MANIFESTOS[0][1]['Linhas_Esperadas'] == str(14 * 120), 'só janeiro a abril de 2025 (La Niña fraca): 14 x 120')
confere(EXPORTS[2]['selectors'][-6:] == sp.COLUNAS_ENSO, 'colunas ENSO no fim do CSV')
confere('indisponível' not in MANIFESTOS[0][0]['Motivo'], 'com a série RONI: sem aviso')
enso_prev = dict(enso, v=['definitiva'] * 300 + ['provisoria_gfs'] * 65)
rodar('P0013', 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=pr;enso=La_Nina_Fraca', False, enso_prev)
confere(MANIFESTOS[0][1]['Linhas_Esperadas'] == str(14 * (120 + 65)), 'dias de previsão entram sempre')
rodar('P0014', 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=pr;enso=Super_El_Nino', False, enso)
confere(MANIFESTOS and MANIFESTOS[0][0]['Status'] == 'recusado', 'cenário inexistente recusado')
rodar('P0015', 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=pr;enso=El_Nino_Forte', False, enso)
confere(MANIFESTOS[0][0]['Status'] == 'recusado' and 'Nenhum mês' in MANIFESTOS[0][0]['Motivo'], 'nenhum mês com o fenômeno')

print('\n[16] formato Excel vai para o manifesto')
rodar('P0016', COD + ';fmt=ambos', False, dict(PB, of=[{'ano': 2025, 'mes': 1, 'RONI': 0.0}], est=[]))
confere(MANIFESTOS[0][0]['Formato'] == 'ambos' and len(EXPORTS) == 3, 'Formato = ambos; o cálculo é o mesmo')

print('\n[10] município digitado sem acento acha o nome do GAUL')
rodar('P0010', 'v=1;res=D;tipo=M;uf=Paraná;mun=clevelandia;ini=2025-01-01;fim=2025-12-31;var=pr', False,
      {'pares': 5, 'nomes': ['Clevelândia'], 'estados': ['Parana'], 'pontos': ['Clevelândia'] * 5, 'datas': ANO})
confere([e['fileNamePrefix'] for e in EXPORTS[2:]] == ['Diaria_Clevelandia_2025'], 'clevelandia -> Clevelândia')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'FUMAÇA OK'))
sys.exit(1 if falhas else 0)
