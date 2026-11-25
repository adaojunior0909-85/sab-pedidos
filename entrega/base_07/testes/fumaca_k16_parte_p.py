# Fumaça da parte P da K16 v3: o Python prepara a pasta, chama o Node com o painel embutido e lê o resultado.
# O Node é o de verdade; no lugar de @google/earthengine entra um Earth Engine simulado (sem rede): os links do
# painel viram URLs "data:" com um CSV pequeno, que o fetch do Node baixa como se fosse o servidor.
# Rodar: python3 testes/fumaca_k16_parte_p.py
import os
import shutil
import sys
import tempfile
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(AQUI, '..', 'validacoes', 'K16_validacao_identidade_email.py'), encoding='utf-8').read()
BASE = tempfile.mkdtemp(prefix='k16p_base_')
DRIVE = tempfile.mkdtemp(prefix='k16p_drive_')

for m in ('ee', 'pandas', 'requests'):
    if m not in sys.modules:
        try:
            __import__(m)
        except ImportError:
            sys.modules[m] = types.ModuleType(m)
parte1, _ = SRC.rsplit("if __name__ == '__main__':", 1)
ns = {'__name__': 'fumaca_p'}
exec(parte1, ns)
ns['BASE'] = BASE
ns['PASTA'] = os.path.join(BASE, 'saida')
ns['LOG'] = os.path.join(ns['PASTA'], 'LOG_K16.txt')

FAKE_EE = r"""
// Earth Engine simulado para a fumaça (mesmo esquema do testes/teste_k16_painel_node.js)
function ser(a, p) { p = p || 0; if (p > 6) return '…';
  if (typeof a === 'function') return a.__caminho ? a.__caminho.slice(0, 4000) : 'fn';
  if (typeof a === 'string') return JSON.stringify(a);
  if (a === null || typeof a !== 'object') return String(a);
  if (Array.isArray(a)) return '[' + a.map(function (x) { return ser(x, p + 1); }).join(',') + ']';
  return '{' + Object.keys(a).map(function (k) { return k + ':' + ser(a[k], p + 1); }).join(',') + '}'; }
function responder(c) {
  if (/^ee\.Dictionary\(\{Indefinida:/.test(c)) return {Indefinida: [], Sem_Dado: []};
  if (/^ee\.Dictionary\(\{n:.*nPares:/.test(c)) return {n: 15, nPares: 15};
  if (/^ee\.Dictionary\(\{qtd_periodo:/.test(c)) return {qtd_periodo: 365};
  if (/bandNames\(\)$/.test(c)) return ['classe'];
  if (/aggregate_array\("ADM2_NAME"\)$/.test(c)) return ['Clevelandia', 'Pato Branco'];
  var fim = c.slice(-80);
  if (/aggregate_array\("system:time_start"\)/.test(fim)) return [2015, 2016];
  if (/aggregate_array\("Nome_Local_Export"\)/.test(fim)) {
    var n = []; if (/"Pato Branco"/.test(c)) n.push('Pato Branco'); if (/"Clevelandia"/.test(c)) n.push('Clevelandia');
    return n.length ? n : ['Poligono_1']; }
  if (/reduceRegion/.test(c)) return new Proxy({}, {get: function (t, k) { return typeof k === 'string' ? 1 : undefined; }});
  return null; }
function stub(cam) {
  return new Proxy(function () {}, {
    get: function (t, p) {
      if (p === '__caminho') return cam.join('');
      if (p === 'evaluate') return function (cb) { var c = cam.join(''); setTimeout(function () { cb(responder(c)); }, 2); };
      if (p === 'getDownloadURL') return function (f, cols, nome, cb) {
        var csv = 'arquivo,colunas\n' + nome + ',' + cols.length + '\n';
        setTimeout(function () { cb('data:text/csv;base64,' + Buffer.from(csv).toString('base64')); }, 2); };
      if (p === 'then') return undefined;
      if (p === Symbol.toPrimitive || p === 'toString' || p === 'valueOf') return function () { return '[ee]'; };
      return stub(cam.concat(['.' + String(p)]));
    },
    apply: function (t, e, args) { return stub(cam.concat(['(' + args.map(function (a) { return ser(a); }).join(',') + ')'])); },
    construct: function () { return stub(cam.concat(['new'])); }
  });
}
var ee = stub(['ee']);
var falso = {
  data: {setAuthToken: function (a, b, tok, d, e, cb) { if (tok !== 'TOKEN_FALSO') throw new Error('token errado'); cb(); },
         setProject: function () {}},
  initialize: function (a, b, ok) { ok(); }
};
module.exports = new Proxy(falso, {get: function (t, p) { return p in t ? t[p] : ee[p]; }});
"""


def preparar_falso(pasta):
    mod = os.path.join(pasta, 'node_modules', '@google', 'earthengine')
    os.makedirs(mod, exist_ok=True)
    open(os.path.join(mod, 'index.js'), 'w', encoding='utf-8').write(FAKE_EE)
    open(os.path.join(mod, 'package.json'), 'w', encoding='utf-8').write('{"name":"@google/earthengine","main":"index.js"}')
    return shutil.which('node')


ns['preparar_node'] = preparar_falso
ns['token_ee'] = lambda: 'TOKEN_FALSO'
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


print('[fumaça K16 v3, parte P]')
# A3 já tem o CSV posto à mão: não pode ser refeito
os.makedirs(os.path.join(DRIVE, ns['PASTA_PAINEL'], 'A3'))
open(os.path.join(DRIVE, ns['PASTA_PAINEL'], 'A3', 'Mensal_Pato_Branco_2025.csv'), 'w').write('feito,a,mao\n')
planos = {'A1': ['Diaria_Pato_Branco_2025'], 'A2': ['Diaria_Clevelandia_2025', 'Diaria_Pato_Branco_2025'],
          'A3': ['Mensal_Pato_Branco_2025'], 'A4': ['Diaria_Poligono_1_2025'],
          'A5': ['Diaria_Pato_Branco_2015_El_Nino_Forte', 'Diaria_Pato_Branco_2016_El_Nino_Forte'],
          'A6': ['Diaria_Poligono_1_2024'], 'A7': ['Diaria_Poligono_1_2026']}
confere(ns['casos_sem_painel'](DRIVE) == ['A1', 'A2', 'A4', 'A5', 'A6', 'A7'], 'só os casos sem CSV vão para o Node')
res = ns['gerar_csv_painel'](DRIVE, planos)
confere(sorted(res) == ['A1', 'A2', 'A4', 'A5', 'A6', 'A7'], 'o Node devolveu um resultado por caso: ' + ', '.join(sorted(res)))
confere(all(not r['faltando'] and not r['erros'] for r in res.values()), 'nenhum arquivo faltando nem com erro')
for caso, nomes in planos.items():
    if caso == 'A3':
        continue
    for n in nomes:
        arq = os.path.join(DRIVE, ns['PASTA_PAINEL'], caso, n + '.csv')
        confere(os.path.exists(arq) and open(arq).read().startswith('arquivo,colunas\n' + n + ','), f'{caso}/{n}.csv gravado')
confere(os.path.exists(os.path.join(DRIVE, ns['PASTA_PAINEL'], 'A1', '00_Dicionario_Variaveis_SAB.csv')), 'A1: dicionário do painel')
confere(open(os.path.join(DRIVE, ns['PASTA_PAINEL'], 'A3', 'Mensal_Pato_Branco_2025.csv')).read() == 'feito,a,mao\n',
        'A3 feito à mão continua o mesmo')
confere(ns['casos_sem_painel'](DRIVE) == [], 'depois da parte P, nenhum caso sem CSV do painel')
log = open(ns['LOG'], encoding='utf-8').read()
confere('TOKEN_FALSO' not in log, 'o token não aparece no LOG')
confere(ns['VERSAO_PAINEL_JS'] == '2026.11.5', 'versão do painel embutido lida: ' + ns['VERSAO_PAINEL_JS'])
shutil.rmtree(BASE, ignore_errors=True)
shutil.rmtree(DRIVE, ignore_errors=True)
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'FUMAÇA PARTE P OK'))
sys.exit(1 if falhas else 0)
