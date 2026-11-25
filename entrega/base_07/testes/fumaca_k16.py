# Fumaça da K16: roda o script inteiro com Earth Engine, Drive, tarefas e link simulados.
# Rodar de uma pasta vazia: python3 /caminho/testes/fumaca_k16.py
import os
import sys
import tempfile
import time
import types
from datetime import date, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(AQUI, '..', 'validacoes', 'K16_validacao_identidade_email.py'), encoding='utf-8').read()
DRIVE = tempfile.mkdtemp(prefix='drive_k16_')
ESTRAGAR = os.environ.get('ESTRAGAR', '')     # nome de um arquivo do painel para alterar (teste da reprovação)


class D:
    def __getattr__(self, n):
        if n == 'getDownloadURL':
            return lambda filetype=None, selectors=None, filename='': 'fake://' + filename
        return lambda *a, **k: D()

    def __call__(self, *a, **k):
        return D()


ee = types.ModuleType('ee')
for nome in ('Image', 'ImageCollection', 'FeatureCollection', 'Feature', 'Geometry', 'Filter', 'Reducer', 'Date',
             'Algorithms', 'Number', 'List', 'Dictionary', 'String', 'Projection', 'Join'):
    setattr(ee, nome, D())
ee.Initialize = lambda **k: None
ee.Authenticate = lambda: None
TAREFAS = {}


def csv(colunas, n, mexer=False, a7=False):
    linhas = [','.join(colunas)]
    for i in range(n):
        v = {c: '' for c in colunas}
        v.update(N_Ponto=f'Ponto_{i % 7:05d}', Data_Completa=f'D{i // 7:04d}', Variavel=f'V{i:02d}',
                 Tipo_Dado='Previsao_GFS' if i % 2 else 'Provisorio_ERA5', Filtro_ENSO='Sem filtro', Fase_ENSO='Neutro',
                 Fonte_ENSO='Persistencia')
        v = {c: v.get(c, '') for c in colunas}
        for c in colunas:
            if c.startswith(('Temperatura', 'Precip')):
                v[c] = '18.41' if (mexer and i == 3) else '18.40'
        if a7:   # [v7] Lagoa Mirim: 1 linha em 7 com radiação, ETo e déficit vazios (dentro de 04-20/03)
            vz = i % 7 == 0
            v.update({'Data_Completa': f'2026-03-{4 + i // 7:02d}', 'Evapotranspiracao_Potencial_mm': '' if vz else '3.10',
                      'Deficit_Hidrico_mm': '' if vz else '1.00', 'Evapotranspiracao_Real_mm': '2.10',
                      'Radiacao_Solar_MJ_m2': '' if vz else '18.40'})
            v = {c: v.get(c, '') for c in colunas}
        linhas.append(','.join(v[c] for c in colunas))
    return '\n'.join(linhas) + '\n'


class Tarefa:
    def __init__(self, **k):
        self.k, self.id = k, 'ID%02d' % (len(TAREFAS) + 1)

    def start(self):
        pasta = os.path.join(DRIVE, self.k['folder'])
        if 'Dicionario' in self.k['fileNamePrefix']:   # [v7.1] o Drive criou uma 2ª pasta com o mesmo nome
            pasta += ' (1)'
        os.makedirs(pasta, exist_ok=True)
        n = 35 if 'Dicionario' in self.k['fileNamePrefix'] else 70
        open(os.path.join(pasta, self.k['fileNamePrefix'] + '.csv'), 'w').write(
            csv(self.k['selectors'], n, a7='A7__' in self.k['fileNamePrefix']))
        TAREFAS[self.id] = {'id': self.id, 'state': 'COMPLETED'}


ee.batch = types.SimpleNamespace(Export=types.SimpleNamespace(table=types.SimpleNamespace(toDrive=lambda **k: Tarefa(**k))))
ee.data = types.SimpleNamespace(getTaskStatus=lambda ids: [TAREFAS[i] for i in ids])
sys.modules['ee'] = ee


class Resp:
    status_code = 200

    def __init__(self, txt):
        self.text, self.content = txt, txt.encode()


requests = types.ModuleType('requests')
# Cada link "demora" 10 s num relógio simulado: o tempo medido não depende da carga da máquina (antes, o tempo
# real de montar o CSV falso às vezes dava razão < 0,7 entre 3 e 19 variáveis e o teste falhava por acaso).
_RELOGIO = [0.0]
_TEMPO_REAL = time.time
time.time = lambda: _TEMPO_REAL() + _RELOGIO[0]


def _get(url, timeout=None):
    r = Resp(csv(['N_Ponto', 'Data_Completa'], 1889 * 90))
    _RELOGIO[0] += 10.0
    return r


requests.get = _get
sys.modules['requests'] = requests
colab = types.ModuleType('google.colab')
colab.drive = types.SimpleNamespace(mount=lambda p: None)
colab.files = types.SimpleNamespace(download=lambda z: None)
sys.modules['google'] = types.ModuleType('google')
sys.modules['google.colab'] = colab
time.sleep = lambda s: None

parte1, parte2 = SRC.rsplit("if __name__ == '__main__':", 1)   # o último: o da K16 (a rotina embutida tem o seu)
ns = {'__name__': 'fumaca'}
exec(parte1, ns)
# Pasta de saída própria desta execução (a do script tem só o minuto no nome: duas execuções no mesmo minuto
# escreviam no mesmo LOG e a contagem de linhas do teste dobrava)
import tempfile as _tf  # noqa: E402
_SAIDA = _tf.mkdtemp(prefix='saida_fumaca_')
ns['PASTA'] = os.path.join(_SAIDA, os.path.basename(ns['PASTA']))
ns['LOG'] = os.path.join(ns['PASTA'], os.path.basename(ns['LOG']))
ns['DRIVE'] = DRIVE
sp = ns['sp']
ANO = [date(2025, 1, 1) + timedelta(days=i) for i in range(10)]   # 10 dias: 7 pontos x 10 = 70 linhas


def avaliar_falso(ped):
    if ped['tipo'] == 'E':
        return None, D(), D(), 1889, [('Paraná', 1889)], [], [date(2025, 1, 1) + timedelta(days=i) for i in range(90)]
    if ped['tipo'] == 'P':
        return None, D(), D(), 7, [('Poligono_1', 7)], [], ANO
    locais = [('Clevelandia', 7), ('Pato Branco', 7)] if len(ped['municipios']) == 2 else [('Pato Branco', 7)]
    return None, D(), D(), 7 * len(locais), locais, [], ANO


sp.avaliar = avaliar_falso
sp.resolver_municipios = lambda ped: ped            # nomes já do GAUL nos casos da K16
sp.aplicar_enso = lambda ctx, ped: dict(ctx, enso={'ascii': (ped['enso'] or {}).get('ascii', 'Sem filtro'),
                                                   'filtro': bool(ped['enso']), 'meses_ok': ['2025_01'], 'dic': {}})
# CSV do "painel" no Drive, iguais ao que a rotina exporta (com o caso ESTRAGAR alterado)
COL_D, COL_M = sp.colunas_do_pedido('D', sp.CODIGOS, enso=False), sp.colunas_do_pedido('M', sp.CODIGOS, enso=False)
for caso, nomes, cols in [('A1', ['Diaria_Pato_Branco_2025'], COL_D),
                          ('A2', ['Diaria_Pato_Branco_2025', 'Diaria_Clevelandia_2025'], COL_D),
                          ('A3', ['Mensal_Pato_Branco_2025'], COL_M), ('A4', ['Diaria_Poligono_1_2025'], COL_D),
                          ('A5', ['Diaria_Pato_Branco_2025_El_Nino_Forte'], COL_D + sp.COLUNAS_ENSO_PAINEL),
                          ('A6', ['Diaria_Poligono_1_2025'], COL_D),    # o avaliar falso usa 2025
                          ('A7', ['Diaria_Poligono_1_2025'], COL_D)]:
    os.makedirs(os.path.join(DRIVE, ns['PASTA_PAINEL'], caso), exist_ok=True)
    for n in nomes:
        open(os.path.join(DRIVE, ns['PASTA_PAINEL'], caso, n + '.csv'), 'w').write(
            csv(cols, 70, mexer=(f'{caso}/{n}' == ESTRAGAR), a7=(caso == 'A7')))
open(os.path.join(DRIVE, ns['PASTA_PAINEL'], 'A1', '00_Dicionario_Variaveis_SAB.csv'), 'w').write(
    csv(['Variavel', 'Descricao', 'Unidade'], 35))
ns['RODAR_PARTE_C'] = True          # [v7] a fumaça continua exercitando a parte C (no Colab ela vem desligada)
exec('if True:' + parte2, ns)

log = open(ns['LOG'], encoding='utf-8').read()
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


print('\n[fumaça K16]' + (f' com {ESTRAGAR} alterado' if ESTRAGAR else ''))
confere(sp.VERSAO_ROTINA == '2026.11.22' and 'SHA-256' in log, 'rotina embutida carregada e impressão digital no LOG')
if ESTRAGAR:
    confere('IDENTIDADE NÃO APROVADA' in log and '18.41' in log, 'uma célula diferente reprova e aparece no LOG')
else:
    confere(log.count('✅ A') + log.count('✅ B') >= 6, 'todos os arquivos A e B conferidos iguais')
    confere('IDENTIDADE APROVADA' in log, 'identidade aprovada')
    confere('coluna(s) ENSO só na rotina' in log and '✅ E1' in log, 'colunas ENSO a mais aceitas e E1 conferido')
    confere('✅ A7' in log and '✅ R7' in log, '[v7] A7 igual ao painel e R7 (radiação vazia) conferido')
    confere('achado em outra pasta do Drive' in log and '✅ A1 dicionário' in log,
            '[v7.1] dicionário exportado para uma 2ª pasta com o mesmo nome: achado e conferido')
    confere(log.count('E1 colunas ENSO') == 1 and 'R7 radiação' not in log.split('E1 colunas ENSO')[1].split('\n')[0],
            '[v7.1] a linha do E1 traz o texto do E1')
    confere('NÃO aceleram' in log, 'links com o mesmo tempo: não acelera')
confere(os.path.exists(ns['PASTA'] + '.zip'), 'zip gerado')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'FUMAÇA OK'))
sys.exit(1 if falhas else 0)
