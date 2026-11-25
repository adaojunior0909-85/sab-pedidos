// Teste offline do k16_painel_node.js: roda o painel 2026.10.7 inteiro com um Earth Engine SIMULADO (qualquer
// chamada vira um objeto que guarda o caminho; evaluate e getDownloadURL respondem pelo conteúdo do caminho) e
// confere que a "pessoa simulada" preenche a tela certo e baixa os links de cada caso da K16.
// Uso: node testes/teste_k16_painel_node.js
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const DIR = path.resolve(__dirname, '..');
const H = require(path.join(DIR, 'automacao_email', 'k16_painel_node.js'));
const painelSrc = fs.readFileSync(path.join(DIR, '06_painel_sab_2026_11_5.js'), 'utf8');

let falhas = 0;
const confere = (c, m) => { console.log((c ? '  ok   ' : '  FALHA ') + m); if (!c) falhas++; };

// ---------------------------------------------------------------- Earth Engine simulado
const pedidos = [];      // o que o painel pediu ao servidor (para conferir o que a tela montou)
function stub(caminho) {
  const f = function () {};
  return new Proxy(f, {
    get(t, p) {
      if (p === 'evaluate') {
        return function (cb) {
          const c = caminho.join('');
          pedidos.push(c);
          setTimeout(() => cb(responder(c), undefined), 5);
        };
      }
      if (p === 'getDownloadURL') {
        return function (fmt, cols, nome, cb) {
          pedidos.push('URL:' + nome + ':' + caminho.join(''));
          setTimeout(() => cb('https://teste/' + nome, undefined), 5);
        };
      }
      if (p === '__caminho') return caminho.join('');
      if (p === 'getInfo') return () => null;
      if (p === Symbol.toPrimitive || p === 'toString' || p === 'valueOf') return () => '[ee]';
      if (p === 'then') return undefined;
      return stub(caminho.concat(['.' + String(p)]));
    },
    apply(t, este, args) {
      return stub(caminho.concat(['(' + args.map(ser).join(',') + ')']));
    },
    construct(t, args) { return stub(caminho.concat(['new(' + args.length + ')'])); }
  });
}
// argumentos no caminho (objetos do servidor pelo próprio caminho), para o responder saber o que foi pedido
function ser(a, prof) {
  prof = prof || 0;
  if (prof > 6) return '…';
  if (typeof a === 'function') return a.__caminho ? a.__caminho.slice(0, 4000) : 'fn';
  if (typeof a === 'string') return JSON.stringify(a);
  if (a === null || typeof a !== 'object') return String(a);
  if (Array.isArray(a)) return '[' + a.map((x) => ser(x, prof + 1)).join(',') + ']';
  return '{' + Object.keys(a).map((k) => k + ':' + ser(a[k], prof + 1)).join(',') + '}';
}
const MUNIS = ['Abatia', 'Clevelandia', 'Pato Branco', 'Palmas'];
let anosEnso = [2015, 2016];
function responder(c) {
  if (/^ee\.Dictionary\(\{Indefinida:/.test(c)) return {Indefinida: [], Sem_Dado: []};
  if (/^ee\.Dictionary\(\{n:.*nPares:/.test(c)) return {n: 15, nPares: 15};
  if (/^ee\.Dictionary\(\{qtd_periodo:/.test(c)) return {qtd_periodo: 365};
  if (/bandNames\(\)$/.test(c)) return ['classe'];
  if (/aggregate_array\("ADM2_NAME"\)/.test(c)) return MUNIS.concat(['Pato Branco']);
  if (/\{n:.*nPares:/.test(c)) return {n: 15, nPares: 15};
  if (/\{qtd_periodo:/.test(c)) return {qtd_periodo: 365};
  const fim = c.slice(-80);
  if (/aggregate_array\("system:time_start"\)/.test(fim)) return anosEnso;
  if (/aggregate_array\("Nome_Local_Export"\)/.test(fim)) {
    const nomes = [];
    if (/"Pato Branco"/.test(c)) nomes.push('Pato Branco');
    if (/"Clevelandia"/.test(c)) nomes.push('Clevelandia');
    if (/Poligono_|Polygon/.test(c) && !nomes.length) nomes.push('Poligono_1');
    return nomes.length ? nomes : ['Poligono_1'];
  }
  if (/aggregate_array\("system:time_start"\)/.test(c)) return anosEnso;
  if (/reduceRegion/.test(c)) return new Proxy({}, {get: (t, k) => (typeof k === 'string' ? 1 : undefined)});   // camadas do mapa
  return null;
}
const ee = stub(['ee']);

// ---------------------------------------------------------------- casos da K16
const casos = [
  {caso: 'A1', res: 'Diária', local: {tipo: 'M', uf: ['Paraná'], mun: ['Pato Branco']}, ini: '01/01/2025', fim: '31/12/2025',
   enso: null, esperados: ['Diaria_Pato_Branco_2025', '00_Dicionario_Variaveis_SAB']},
  {caso: 'A2', res: 'Diária', local: {tipo: 'M', uf: ['Paraná'], mun: ['Pato Branco', 'Clevelândia']}, ini: '01/01/2025',
   fim: '31/12/2025', enso: null, esperados: ['Diaria_Clevelandia_2025', 'Diaria_Pato_Branco_2025']},
  {caso: 'A3', res: 'Mensal', local: {tipo: 'M', uf: ['Paraná'], mun: ['Pato Branco']}, ini: '01/01/2025', fim: '31/12/2025',
   enso: null, esperados: ['Mensal_Pato_Branco_2025']},
  {caso: 'A4', res: 'Diária', local: {tipo: 'P', pontos: [[-26.2, -52.7], [-26.2, -52.6], [-26.3, -52.6], [-26.3, -52.7]]},
   ini: '01/01/2025', fim: '31/03/2025', enso: null, esperados: ['Diaria_Poligono_1_2025']},
  {caso: 'A5', res: 'Diária', local: {tipo: 'M', uf: ['Paraná'], mun: ['Pato Branco']}, ini: '01/01/2015', fim: '31/12/2016',
   enso: 'El Niño Forte (1.5 a 1.9°C)', esperados: ['Diaria_Pato_Branco_2015_El_Nino_Forte', 'Diaria_Pato_Branco_2016_El_Nino_Forte']}
];
const saida = fs.mkdtempSync(path.join(os.tmpdir(), 'k16p_'));
const baixados = [];
const baixar = async (url) => { baixados.push(url); return Buffer.from('Tipo_Dado,Data\nX,' + url + '\n'); };

(async function () {
  const t0 = Date.now();
  // espera "parado" de 90 s não pode acontecer aqui: todos os esperados chegam
  const r = await H.principal(ee, painelSrc, saida, casos, 'clima-492922', baixar);
  const por = {}; r.resultados.forEach((x) => { por[x.caso] = x; });
  console.log('[resultado por caso]');
  r.resultados.forEach((x) => console.log('   ' + x.caso + ': ' + x.arquivos.join(', ') + (x.faltando.length ? ' | faltando ' + x.faltando : '')));
  confere(Date.now() - t0 < 60000, 'termina rápido quando todos os links esperados ficam prontos');
  confere(por.A1.arquivos.join() === '00_Dicionario_Variaveis_SAB,Diaria_Pato_Branco_2025' && !por.A1.faltando.length, 'A1: CSV diário e dicionário');
  confere(['Diaria_Clevelandia_2025', 'Diaria_Pato_Branco_2025'].every((n) => por.A2.arquivos.indexOf(n) !== -1), 'A2: os dois municípios (aceitou o aviso de vários municípios)');
  confere(por.A3.arquivos.indexOf('Mensal_Pato_Branco_2025') !== -1, 'A3: mensal');
  confere(por.A4.arquivos.indexOf('Diaria_Poligono_1_2025') !== -1, 'A4: polígono das coordenadas');
  confere(por.A5.arquivos.indexOf('Diaria_Pato_Branco_2015_El_Nino_Forte') !== -1 &&
          por.A5.arquivos.indexOf('Diaria_Pato_Branco_2016_El_Nino_Forte') !== -1, 'A5: arquivos com o sufixo do filtro');
  confere(fs.existsSync(path.join(saida, 'A1', 'Diaria_Pato_Branco_2025.csv')) &&
          fs.readFileSync(path.join(saida, 'A1', 'Diaria_Pato_Branco_2025.csv'), 'utf8').indexOf('https://teste/Diaria_Pato_Branco_2025') !== -1,
          'arquivo gravado com o conteúdo do link do painel');
  // o que a tela pediu ao servidor
  const urlA2 = pedidos.filter((p) => /^URL:Diaria_Clevelandia_2025/.test(p))[0] || '';
  confere(/"Clevelandia"/.test(urlA2) && /"Pato Branco"/.test(urlA2), 'A2: filtro do GAUL com os dois municípios');
  const urlA4 = pedidos.filter((p) => /^URL:Diaria_Poligono_1_2025/.test(p))[0] || '';
  confere(/"2025-01-01"/.test(urlA4) && /"2025-03-31"/.test(urlA4), 'A4: período 01/01 a 31/03/2025 levado ao servidor');
  confere(urlA4.indexOf('ee.Geometry.Polygon([[[-52.7,-26.2],[-52.6,-26.2],[-52.6,-26.3],[-52.7,-26.3]]])') !== -1,
          'A4: os 4 vértices na ordem, como lon/lat');
  confere(/FaseENSO/.test(pedidos.filter((p) => /^URL:Diaria_Pato_Branco_2016_El_Nino_Forte/.test(p))[0] || '') &&
          !/FaseENSO/.test(pedidos.filter((p) => /^URL:Diaria_Pato_Branco_2025:/.test(p))[0] || 'FaseENSO'), 'filtro ENSO só no A5');
  const urlA1 = pedidos.filter((p) => /^URL:Diaria_Pato_Branco_2025:/.test(p))[0] || '';
  confere(/"2025-12-31"/.test(urlA1) && !/advance\(15/.test(urlA1), 'A1: sem a previsão (data final não estendida)');
  const urlA5 = pedidos.filter((p) => /^URL:Diaria_Pato_Branco_2015_El_Nino_Forte/.test(p))[0] || '';
  confere(/"2015-01-01"/.test(urlA5) && /"2016-12-31"/.test(urlA5), 'A5: período 2015-2016');
  confere(baixados.length === r.resultados.reduce((s, x) => s + x.arquivos.length, 0), 'cada arquivo baixado uma vez');
  fs.rmSync(saida, {recursive: true, force: true});
  console.log('\n' + (falhas ? falhas + ' FALHA(S)' : 'K16 v3 (PAINEL NO NODE) OK'));
  process.exit(falhas ? 1 : 0);
})().catch((e) => { console.log('ERRO ' + (e.stack || e)); process.exit(1); });
