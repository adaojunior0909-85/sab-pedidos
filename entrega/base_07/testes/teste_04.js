// [V4] Teste offline do 04_conferencia_matriz_gfs.js (Node, sem Earth Engine).
// Roda o script inteiro num contexto com um `ee` simulado (Proxy encadeável), guarda cada
// .evaluate() e responde com resultados sintéticos, como o servidor faria. Confere:
//   - nenhuma exceção ao montar as expressões e ao interpretar os resultados;
//   - no máximo 4 pedidos simultâneos; relatório impresso uma única vez, no fim;
//   - cenário "tudo certo": nenhum ⚠️/❌ e o total esperado de ✅;
//   - cenário com defeitos: cada defeito vira o ❌/⚠️ certo;
//   - tabela MAXIMO_PARES do 04 = testes/maximos_pares_v16.py.
// Uso: node teste_04.js
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { execFileSync } = require('child_process');

const ARQ = path.join(__dirname, '..', '04_conferencia_matriz_gfs.js');
const CODIGO = fs.readFileSync(ARQ, 'utf8');
let falhas = 0;
let oks = 0;
function confere(cond, msg) {
  if (cond) { oks += 1; } else { falhas += 1; console.log('   FALHOU: ' + msg); }
}

// ---------- ee simulado ----------
function coletaInfo(x, acc, prof) {
  if (prof > 4 || x === null || x === undefined) return;
  if (typeof x === 'string') {
    if (x.indexOf('Matriz_GFS_') >= 0 && !acc.asset) acc.asset = x;
    return;
  }
  if (typeof x !== 'object' && typeof x !== 'function') return;
  if (x.__ehProxy) {
    const i = x.__info;
    if (i && i.asset && !acc.asset) acc.asset = i.asset;
    return;
  }
  if (Array.isArray(x)) { x.forEach(y => coletaInfo(y, acc, prof + 1)); return; }
  if (typeof x === 'object') Object.keys(x).forEach(k => coletaInfo(x[k], acc, prof + 1));
}

function criaAmbiente() {
  const amb = { chamadas: [], impressos: [], maxPendentes: 0 };
  function mk(trilha, info) {
    const alvo = function () {};
    return new Proxy(alvo, {
      get(t, k) {
        if (k === '__ehProxy') return true;
        if (k === '__info') return info;
        if (k === '__trilha') return trilha;
        if (typeof k === 'symbol') return undefined;
        if (k === 'evaluate') {
          return function (cb) {
            amb.chamadas.push({ trilha, info, cb });
            amb.maxPendentes = Math.max(amb.maxPendentes, amb.chamadas.length);
          };
        }
        return mk(trilha.concat([k]), info);
      },
      apply(t, ctx, args) {
        const novo = Object.assign({}, info || {});
        coletaInfo(args, novo, 0);
        const ultimo = trilha[trilha.length - 1];
        if (ultimo === 'Dictionary' && args[0] && typeof args[0] === 'object' && !args[0].__ehProxy) {
          novo.chaves = Object.keys(args[0]);
        }
        return mk(trilha.concat(['()']), novo);
      }
    });
  }
  const contexto = {
    ee: mk(['ee'], {}),
    print: function () { amb.impressos.push(Array.prototype.slice.call(arguments).join(' ')); },
    Map: { setCenter: function () {}, addLayer: function () {} },
    JSON, Math, Number, Object, isNaN, parseInt
  };
  vm.createContext(contexto);
  vm.runInContext(CODIGO, contexto, { filename: ARQ });
  amb.ctx = contexto;
  return amb;
}

function mesDe(info) {
  const m = /Matriz_GFS_(\d\d)/.exec((info && info.asset) || '');
  return m ? m[1] : null;
}

// Resultado sintético de cada pedido; `defeitos` muda o cenário
function responde(amb, ch, defeitos) {
  const ctx = amb.ctx;
  const trilha = ch.trilha;
  const chaves = (ch.info && ch.info.chaves) || [];
  const mm = mesDe(ch.info);
  if (trilha.indexOf('aggregate_array') >= 0) {
    return [ctx.MESES.filter(m => defeitos.ausente !== m).map(m => 'Matriz_GFS_' + m), null];
  }
  if (chaves.indexOf('bandas') >= 0) {
    const props = Object.assign({}, ctx.CONTRATO, { mes_referencia: parseInt(mm, 10), gerado_em: '2026-10-21T10:00:00Z' });
    ctx.FAIXAS.forEach((fx, i) => { props['n_pares_' + fx] = ctx.MAXIMO_PARES[mm][i] - 2; });
    let bandas = ctx.ESPERADAS.slice();
    if (defeitos.versao === mm) { props.versao_matriz = 'V2'; props.n_pares_L1 = 0; }
    if (defeitos.semBanda === mm) bandas = bandas.filter(b => b !== 'Rs_m_gfs_L6a10');
    if (defeitos.ordem === mm) bandas = bandas.slice(1).concat([bandas[0]]);
    if (defeitos.poucosPares === mm) props.n_pares_L2a5 = Math.floor(0.5 * ctx.MAXIMO_PARES[mm][1]);
    return [{ bandas, props }, null];
  }
  if (chaves.indexOf('n_amostra') >= 0) {
    if (defeitos.erroEstat === mm) return [null, 'Computation timed out.'];
    const n = {};
    ctx.FAIXAS.forEach((fx, i) => { n[fx] = ctx.MAXIMO_PARES[mm][i] - 2; });
    const percentis = {};
    ctx.FAIXAS.forEach(fx => {
      percentis['dif_Tmax_' + fx] = { p5: -1.5, p50: defeitos.viesTmax === mm ? 6.2 : 0.8, p95: 3.1 };
      percentis['dif_Tmin_' + fx] = { p5: -2.0, p50: -0.4, p95: 1.9 };
      percentis['dif_RH_' + fx] = { p5: -12, p50: 3.5, p95: 15 };
      percentis['fat_pr_' + fx] = { p5: 0.4, p50: 1.1, p95: 2.5 };
      percentis['fat_u2_' + fx] = { p5: 0.5, p50: 0.8, p95: 1.3 };
      percentis['fat_Rs_' + fx] = { p5: 0.88, p50: 0.97, p95: 1.06 };
      percentis['n_' + fx] = { p5: n[fx], p50: n[fx], p95: n[fx] };
    });
    const contagem = {};
    ctx.ESPERADAS.forEach(b => { contagem[b] = 70412; });
    if (defeitos.pegada === mm) contagem['pr_m_gfs_L1'] = 71500;
    const fracoes = {};
    ctx.FAIXAS.forEach(fx => ['pr', 'u2', 'Rs'].forEach(v => {
      fracoes['acima5_' + v + '_' + fx] = (defeitos.fatorPr === mm && v === 'pr') ? 0.18 : 0.001;
      fracoes['abaixo02_' + v + '_' + fx] = 0.0;
    }));
    const nMin = {};
    ctx.FAIXAS.forEach(fx => { nMin['n_' + fx] = n[fx]; });
    const somas = {};
    ctx.FAIXAS.forEach(fx => { somas['pr_m_gfs_' + fx] = 3.9e5; somas['pr_m_sicsb_' + fx] = defeitos.chuva === mm ? 1.5e5 : 3.5e5; });
    const r = { n_amostra: 4930, percentis, contagem, fracoes, n_min: nMin, somas_pr: somas };
    if (chaves.indexOf('gradientes') >= 0) {
      r.gradientes = {};
      ctx.FAIXAS.forEach(fx => {
        r.gradientes['g_br_' + fx] = 0.010;
        r.gradientes['g_gfs_' + fx] = defeitos.grad === mm ? 0.0021 : 0.0045;
      });
    }
    return [r, null];
  }
  if (trilha.indexOf('bandNames') >= 0) {
    if (defeitos.semV1) return [null, "Image.load: Image asset 'SICSB_MATRIZ_GFS/Matriz_GFS_01' not found."];
    return [['pr_m_sicsb', 'Tmax_m_sicsb', 'Rs_m_sicsb', 'Rs_m_gfs', 'Rs_s_gfs'], null];
  }
  if (trilha.indexOf('reduceRegion') >= 0) {
    return [{ g2: 1.00e6 * (defeitos.rs === mm ? 1.05 : 0.93), b2: 1.0e6, g1: 1.0e6, b1: 1.0e6 }, null];
  }
  throw new Error('pedido não reconhecido: ' + trilha.join('.'));
}

function roda(defeitos) {
  const amb = criaAmbiente();
  let passos = 0;
  while (amb.chamadas.length > 0 && passos < 1000) {
    const ch = amb.chamadas.shift();
    const [r, erro] = responde(amb, ch, defeitos);
    ch.cb(r, erro || undefined);
    passos += 1;
  }
  amb.passos = passos;
  amb.texto = amb.impressos.join('\n');
  return amb;
}

function conta(texto, marca) { return texto.split(marca).length - 1; }

// ---------- 1. Tabela embutida ----------
console.log('== 1. MAXIMO_PARES do 04 = maximos_pares_v16.py ==');
const tabela = JSON.parse(execFileSync('python3', [path.join(__dirname, 'maximos_pares_v16.py'), '--json']).toString());
const amb0 = criaAmbiente();
confere(JSON.stringify(amb0.ctx.MAXIMO_PARES) === JSON.stringify(tabela), 'tabela MAXIMO_PARES igual à do Python');
confere(amb0.ctx.ESPERADAS.length === 100 && new Set(amb0.ctx.ESPERADAS).size === 100, '100 bandas esperadas distintas');
confere(amb0.ctx.ESPERADAS[0] === 'pr_m_sicsb_L1' && amb0.ctx.ESPERADAS[48] === 'pr_s_sicsb_L1' &&
        amb0.ctx.ESPERADAS[99] === 'n_L11a15', 'ordem das bandas igual à do 03');

// ---------- 2. Cenário sem defeitos ----------
console.log('== 2. Cenário sem defeitos ==');
const a = roda({});
const relA = a.impressos.filter(t => t.indexOf('RESUMO') >= 0);
confere(relA.length === 1, 'relatório impresso uma vez');
confere(a.maxPendentes <= 4, 'no máximo 4 pedidos simultâneos (houve ' + a.maxPendentes + ')');
confere(a.passos === 1 + 12 + 12 + 1 + 12, 'pedidos: lista + 12 estrutura + 12 estatísticas + V1 + 12 Rs (houve ' + a.passos + ')');
// ✅ esperados: bloco 1 = 1 + 12*3; bloco 2 = 12 + 48; bloco 3 = 48; bloco 4 = 8; bloco 5 = 12
confere(/RESUMO: 165 ✅ \| 0 ⚠️ \| 0 ❌/.test(a.texto), 'RESUMO 165 ✅, 0 ⚠️, 0 ❌');
confere(a.texto.indexOf('pode seguir para o motor') >= 0, 'mensagem final de aprovação');
confere(a.texto.indexOf('Mês 07 L11a15: Tmax +0.8 [-1.5; +3.1]') >= 0, 'linha de viés formatada');
confere(a.texto.indexOf('Mês 01 L1: 2.143') < 0 && a.texto.indexOf('Mês 01 L1: 0.450') >= 0, 'razão de gradientes 0,450');
confere(a.texto.indexOf('Mês 03: n_pares / máximo possível: L1 131/133 (98.5%)') >= 0, 'n_pares contra o máximo');
confere(a.texto.indexOf('razão 0.930') >= 0, 'razão Rs V2.1/V1');
if (process.argv.indexOf('-v') >= 0) console.log(a.texto);

// ---------- 3. Cenário com defeitos ----------
console.log('== 3. Cenário com defeitos ==');
const b = roda({ ausente: '05', versao: '03', semBanda: '04', ordem: '06', poucosPares: '09', viesTmax: '07',
                 grad: '01', pegada: '08', fatorPr: '10', chuva: '11', erroEstat: '12', rs: '02' });
confere(b.impressos.filter(t => t.indexOf('RESUMO') >= 0).length === 1, 'relatório impresso uma vez (com defeitos)');
confere(b.maxPendentes <= 4, 'no máximo 4 pedidos simultâneos (com defeitos)');
const T = b.texto;
const espera = [
  ['❌ Número de matrizes (esperado 12): 11', 'matriz ausente na contagem'],
  ['❌ Mês 05: Matriz_GFS_05 não existe.', 'mês 05 ausente'],
  ["❌ Mês 03: propriedades com problema: versao_matriz = \"V2\"", 'versão errada'],
  ['❌ Mês 03: n_pares / máximo possível: L1 0/133', 'n_pares 0'],
  ['❌ Mês 04: 99 bandas (esperado 100); faltam 1 ["Rs_m_gfs_L6a10"]', 'banda faltando'],
  ['❌ Mês 04: estatísticas não calculadas (faltam bandas).', 'sem estatísticas quando falta banda'],
  ['⚠️ Mês 06: 100 bandas, mas fora da ordem', 'ordem das bandas'],
  ['⚠️ Mês 09: n_pares / máximo possível:', 'n_pares abaixo de 85%'],
  ['❌ Mês 07 L1: Tmax +6.2', 'viés de Tmax acima de 5 °C'],
  ['❌ Mês 01 L1: 0.210', 'gradiente abaixo da V1'],
  ['❌ Mês 08: contagem de pixels difere entre as bandas (mín 70412, máx 71500', 'pegada diferente'],
  ['⚠️ Mês 10 L1:', 'fator de chuva > 5 em 18% dos pixels'],
  ['❌ Mês 11 L1:', 'razão das somas de chuva fora de 0,5-2'],
  ['❌ Mês 12: estatísticas não calculadas (Computation timed out.)', 'erro do servidor no mês 12'],
  ['⚠️ Mês 02: GFS/BR-DWGD V2.1 L1 1.050, V1 1.000, razão 1.050', 'Rs fora de 0,85-1,0'],
  ['❌ Há itens reprovados: pare', 'mensagem final de reprovação']
];
espera.forEach(([trecho, msg]) => confere(T.indexOf(trecho) >= 0, msg + ' -> "' + trecho + '"'));
confere(T.indexOf('Mês 05: GFS/BR-DWGD') < 0, 'mês ausente fora da comparação com a V1');
confere(T.indexOf('Mês 07 L1: 0.') >= 0 && T.indexOf('❌ Mês 07 L1: 0.') < 0, 'gradiente de julho aprovado');
if (process.argv.indexOf('-v') >= 0) console.log(T);

// ---------- 4. V1 ausente ----------
console.log('== 4. V1 ausente ==');
const c = roda({ semV1: true });
confere(c.texto.indexOf('⚠️ Matriz V1 (projects/clima-492922/assets/SICSB_MATRIZ_GFS) ilegível') >= 0, 'V1 ausente vira ⚠️');
confere(/RESUMO: 153 ✅ \| 1 ⚠️ \| 0 ❌/.test(c.texto), 'sem a V1: 153 ✅ e 1 ⚠️');
confere(c.passos === 1 + 12 + 12 + 1, 'sem a V1 não há pedidos de Rs');

console.log();
if (falhas) {
  console.log('❌ ' + falhas + ' falha(s) em ' + (falhas + oks) + ' verificações.');
  process.exit(1);
}
console.log('✅ teste_04: ' + oks + ' verificações OK.');
