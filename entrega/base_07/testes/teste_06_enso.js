// =====================================================================================
// TESTE OFFLINE DO PAINEL 2026.10.7 (06): fase ENSO no fim da série, continuidade e IC
// Uso: node testes/teste_06_enso.js  (a partir da pasta do pacote)
//
// A classificação de fase do painel roda no servidor (ee.*). Aqui ela é replicada em
// JavaScript puro, passo a passo, com a mesma regra:
//   - checkWindow: 5 janelas de 5 estações (deslocamentos -4 a 0) com soma de sinais;
//     janela que sai da série vale 0; El Niño se alguma soma = 5, La Niña se = -5;
//   - [V4 F6/M06-06] Indefinida: sinal do mês não nulo, nAteFim = n - i <= 4 e soma dos
//     sinais de i até o fim = sinal * nAteFim (todas iguais até a última estação).
// A tabela do RONI vem da variável noaa_data do 02_auditoria_roni_cpc.py (lida do arquivo).
// A tabela do IC e a função textoIC95 são extraídas do próprio painel e executadas aqui.
// =====================================================================================
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var DIR = path.resolve(__dirname, '..');
var ARQ_02 = path.join(DIR, '02_auditoria_roni_cpc.py');
var ARQ_06 = path.join(DIR, '06_painel_sab_2026_11_5.js');
var ORDEM = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ'];

var falhas = 0, total = 0;
function confere(cond, msg) {
  total++;
  if (cond) { console.log('  OK   ' + msg); }
  else { falhas++; console.log('  FALHA ' + msg); }
}
function chave(e) { return e.ano + '_' + ('0' + e.mes).slice(-2); }

// ---------------------------------------------------------------- 1. série oficial
function lerSerieOficial() {
  var src = fs.readFileSync(ARQ_02, 'utf8');
  var m = src.match(/noaa_data\s*=\s*"""([\s\S]*?)"""/);
  if (!m) throw new Error('noaa_data não encontrada no 02');
  var linhas = m[1].trim().split('\n');
  var cab = linhas[0].trim().split(/\s+/);
  if (cab.slice(1).join(',') !== ORDEM.join(',')) throw new Error('cabeçalho inesperado: ' + cab);
  var serie = [];
  for (var l = 1; l < linhas.length; l++) {
    var p = linhas[l].trim().split(/\s+/);
    var ano = parseInt(p[0], 10);
    for (var j = 1; j <= 12; j++) {
      if (p[j] === 'NaN') continue;               // estação ainda não publicada
      serie.push({ ano: ano, mes: j, Trimestre: ORDEM[j - 1], RONI: parseFloat(p[j]) });
    }
  }
  serie.sort(function (a, b) { return (a.ano - b.ano) || (a.mes - b.mes); });
  return serie;
}

// sinal: igual ao painel (r.gte(0.5) -> 1; r.lte(-0.5) -> -1; senão 0)
function sinal(r) { return r >= 0.5 ? 1 : (r <= -0.5 ? -1 : 0); }

// ---------------------------------------------------------------- 2. réplica da fase
function classificar(serie, comRegraV4) {
  var s = serie.map(function (e) { return sinal(e.RONI); });
  var n = s.length;
  function checkWindow(i, offset) {
    var start = i + offset, end = start + 4;
    if (!(start >= 0 && end < n)) return 0;
    var soma = 0;
    for (var k = start; k <= end; k++) soma += s[k];
    return soma;
  }
  return serie.map(function (e, i) {
    var w = [-4, -3, -2, -1, 0].map(function (o) { return checkWindow(i, o); });
    var isElNino = w.indexOf(5) !== -1;
    var isLaNina = w.indexOf(-5) !== -1;
    var isIndefinida = false;
    if (comRegraV4) {
      var sinalI = s[i];
      var nAteFim = n - i;
      var somaAteFim = 0;
      if (nAteFim <= 4) { for (var k = i; k <= n - 1; k++) somaAteFim += s[k]; }
      isIndefinida = (Math.abs(sinalI) === 1) && (nAteFim <= 4) && (somaAteFim === sinalI * nAteFim);
    }
    var fase = isElNino ? 'El Nino' : (isLaNina ? 'La Nina' : (isIndefinida ? 'Indefinida' : 'Neutro'));
    return { ano: e.ano, mes: e.mes, RONI: e.RONI, FaseENSO: fase };
  });
}

// réplica de fases_episodio do 02 (sequências de mesmo sinal com pelo menos 5 estações)
function fasesEpisodio02(serie) {
  var s = serie.map(function (e) { return sinal(e.RONI); });
  var f = s.map(function () { return 0; });
  var i = 0;
  while (i < s.length) {
    var j = i;
    while (j < s.length && s[j] === s[i] && s[i] !== 0) j++;
    if (s[i] !== 0 && j - i >= 5) { for (var k = i; k < j; k++) f[k] = s[i]; }
    i = Math.max(j, i + 1);
  }
  return f;
}

// filtro de cenário do painel V4 (com a exclusão explícita de 'Indefinida'/'Sem_Dado')
var DEFINIDAS = ['El Nino', 'La Nina', 'Neutro'];
var CENARIOS = {
  'Super El Niño': function (e) { return e.FaseENSO === 'El Nino' && e.RONI >= 2.0; },
  'El Niño Forte': function (e) { return e.FaseENSO === 'El Nino' && e.RONI >= 1.5 && e.RONI < 2.0; },
  'El Niño Moderado': function (e) { return e.FaseENSO === 'El Nino' && e.RONI >= 1.0 && e.RONI < 1.5; },
  'El Niño Fraco': function (e) { return e.FaseENSO === 'El Nino' && e.RONI >= 0.5 && e.RONI < 1.0; },
  'Anos Neutros': function (e) { return e.FaseENSO === 'Neutro'; },
  'La Niña Fraca': function (e) { return e.FaseENSO === 'La Nina' && e.RONI <= -0.5 && e.RONI > -1.0; },
  'La Niña Moderada': function (e) { return e.FaseENSO === 'La Nina' && e.RONI <= -1.0 && e.RONI > -1.5; },
  'La Niña Forte': function (e) { return e.FaseENSO === 'La Nina' && e.RONI <= -1.5 && e.RONI > -2.0; },
  'Super La Niña': function (e) { return e.FaseENSO === 'La Nina' && e.RONI <= -2.0; }
};
function aplicarCenario(fases, nome, v4) {
  return fases.filter(function (e) {
    return CENARIOS[nome](e) && (!v4 || DEFINIDAS.indexOf(e.FaseENSO) !== -1);
  });
}

// ---------------------------------------------------------------- 3. testes da fase
console.log('\n=== 1. Série oficial do 02 (noaa_data) ===');
var serie = lerSerieOficial();
var ult = serie[serie.length - 1];
confere(serie.length === 920, 'série com 920 estações (lidas: ' + serie.length + ')');
confere(ult.ano === 2026 && ult.Trimestre === 'JAS' && ult.RONI === 1.7, 'última estação JAS 2026 = 1.7');

console.log('\n=== 2. Continuidade (réplica do teste do cliente, M06-15) ===');
function continuidade(sr) {
  var t0 = sr[0], t1 = sr[sr.length - 1];
  var mesesEsperados = (t1.ano - t0.ano) * 12 + (t1.mes - t0.mes) + 1;
  var distintos = {};
  sr.forEach(function (e) { distintos[chave(e)] = true; });
  var nChaves = Object.keys(distintos).length;
  return (sr.length === mesesEsperados) && (nChaves === sr.length);
}
confere(continuidade(serie) === true, 'série oficial contínua -> true');
var comLacuna = serie.slice(0, 500).concat(serie.slice(501));
confere(continuidade(comLacuna) === false, 'série com lacuna -> false');
var comRepeticao = serie.slice(0, 500).concat([serie[499]]).concat(serie.slice(501));
confere(continuidade(comRepeticao) === false, 'lacuna compensada por repetição (mesmo tamanho) -> false');

console.log('\n=== 3. Fim da série: mai a ago/2026 ===');
var v3 = classificar(serie, false);
var v4 = classificar(serie, true);
var fim = v4.slice(-6).map(function (e) { return chave(e) + '=' + e.RONI + ':' + e.FaseENSO; });
console.log('  V4 últimas 6: ' + fim.join(' | '));
var alvo = ['2026_05', '2026_06', '2026_07', '2026_08'];
alvo.forEach(function (c) {
  var e = v4.filter(function (x) { return chave(x) === c; })[0];
  confere(e && e.FaseENSO === 'Indefinida', c + ' (' + (e ? e.RONI : '?') + ') = Indefinida');
});
var e04 = v4.filter(function (x) { return chave(x) === '2026_04'; })[0];
confere(e04.FaseENSO === 'Neutro', '2026_04 (MAM = 0.0, sinal nulo) continua Neutro');
var indef = v4.filter(function (e) { return e.FaseENSO === 'Indefinida'; }).map(chave);
confere(indef.length === 4 && indef.join(',') === alvo.join(','),
        'exatamente 4 estações Indefinida na série: ' + indef.join(','));

console.log('\n=== 4. Só o fim muda (V3 x V4) ===');
var dif = [];
v3.forEach(function (e, i) { if (e.FaseENSO !== v4[i].FaseENSO) dif.push(chave(e) + ':' + e.FaseENSO + '->' + v4[i].FaseENSO); });
console.log('  diferenças: ' + dif.join(' | '));
confere(dif.length === 4 && dif.every(function (d) { return d.indexOf('Neutro->Indefinida') !== -1; }),
        'só as 4 estações finais mudam, todas de Neutro para Indefinida');

console.log('\n=== 5. Conferência com fases_episodio do 02 (fora das Indefinida) ===');
var ep = fasesEpisodio02(serie);
var mapaFase = { 'El Nino': 1, 'La Nina': -1, 'Neutro': 0 };
var divergentes = [];
v4.forEach(function (e, i) {
  if (e.FaseENSO === 'Indefinida') { if (ep[i] !== 0) divergentes.push(chave(e)); return; }
  if (mapaFase[e.FaseENSO] !== ep[i]) divergentes.push(chave(e));
});
confere(divergentes.length === 0, 'janelas do painel = sequências do 02 em todas as estações (' + divergentes.length + ' divergências)');

console.log('\n=== 6. Roteiro 6.5: El Niño Forte em 1972-73 ===');
function forte7273(fases, v4flag) {
  return aplicarCenario(fases, 'El Niño Forte', v4flag)
    .filter(function (e) { return e.ano === 1972 || e.ano === 1973; }).map(chave);
}
var esperado = ['1972_09', '1972_10', '1972_12', '1973_01'];
confere(forte7273(v3, false).join(',') === esperado.join(','), 'V3: ' + forte7273(v3, false).join(','));
confere(forte7273(v4, true).join(',') === esperado.join(','), 'V4: ' + forte7273(v4, true).join(','));
var nov72 = v4.filter(function (x) { return chave(x) === '1972_11'; })[0];
confere(nov72.FaseENSO === 'El Nino' && nov72.RONI === 2.0 &&
        aplicarCenario([nov72], 'Super El Niño', true).length === 1, 'nov/1972 (2.0) cai em Super El Niño');

console.log('\n=== 7. Nenhum cenário inclui Indefinida; Anos Neutros perde mai-ago/2026 ===');
Object.keys(CENARIOS).forEach(function (nome) {
  var sel = aplicarCenario(v4, nome, true);
  confere(sel.every(function (e) { return e.FaseENSO !== 'Indefinida'; }), nome + ': ' + sel.length + ' estações, nenhuma Indefinida');
});
var neutrosV3 = aplicarCenario(v3, 'Anos Neutros', false).map(chave);
var neutrosV4 = aplicarCenario(v4, 'Anos Neutros', true).map(chave);
confere(alvo.every(function (c) { return neutrosV3.indexOf(c) !== -1; }), 'V3: mai-ago/2026 estavam em Anos Neutros');
confere(alvo.every(function (c) { return neutrosV4.indexOf(c) === -1; }), 'V4: mai-ago/2026 saíram de Anos Neutros');
confere(neutrosV3.length - neutrosV4.length === 4, 'Anos Neutros: ' + neutrosV3.length + ' -> ' + neutrosV4.length + ' estações');

console.log('\n=== 8. Cenários hipotéticos do fim da série (estimativa OISST acrescentada) ===');
function comExtra(valores) {
  var s2 = serie.slice();
  var a = 2026, m = 8;
  valores.forEach(function (v) {
    m++; if (m > 12) { m = 1; a++; }
    s2.push({ ano: a, mes: m, Trimestre: ORDEM[m - 1], RONI: v });
  });
  return classificar(s2, true);
}
function fases(c, lista) {
  return lista.map(function (k) { return c.filter(function (x) { return chave(x) === k; })[0].FaseENSO; });
}
var c1 = comExtra([2.0]);   // ASO 2026 = 2.0: 5 estações seguidas >= 0.5
confere(fases(c1, alvo.concat(['2026_09'])).every(function (f) { return f === 'El Nino'; }),
        'ASO = 2.0: mai a set/2026 viram El Nino (episódio completo)');
var c2 = comExtra([0.3]);   // ASO 2026 = 0.3: a sequência de 4 fecha sem episódio
confere(fases(c2, alvo.concat(['2026_09'])).every(function (f) { return f === 'Neutro'; }),
        'ASO = 0.3: mai a ago/2026 Neutro (sequência fechada com 4) e set Neutro (sinal nulo)');
var c3 = comExtra([-0.6]);  // troca de sinal: a sequência positiva fecha, a negativa fica aberta
confere(fases(c3, alvo).every(function (f) { return f === 'Neutro'; }) && fases(c3, ['2026_09'])[0] === 'Indefinida',
        'ASO = -0.6: mai a ago/2026 Neutro e set/2026 Indefinida (La Niña em aberto)');
var c4 = comExtra([-0.6, -0.7, -0.8, -0.9]);  // 4 negativas no fim
confere(fases(c4, ['2026_09', '2026_10', '2026_11', '2026_12']).every(function (f) { return f === 'Indefinida'; }),
        '4 estações negativas no fim: todas Indefinida');
var c5 = comExtra([-0.6, -0.7, -0.8, -0.9, -1.0]);  // 5 negativas: episódio
confere(fases(c5, ['2026_09', '2026_10', '2026_11', '2026_12', '2027_01']).every(function (f) { return f === 'La Nina'; }),
        '5 estações negativas no fim: todas La Nina');

// ---------------------------------------------------------------- 4. IC Clopper-Pearson
console.log('\n=== 9. IC 95% (tabela e textoIC95 extraídas do painel) ===');
var src06 = fs.readFileSync(ARQ_06, 'utf8');
var mTab = src06.match(/var IC95_CLOPPER_PEARSON_N10 = \{[\s\S]*?\};/);
var mFun = src06.match(/function textoIC95\([\s\S]*?\n\}/);
confere(!!mTab && !!mFun, 'tabela e função encontradas no painel');
var ctx = {};
vm.createContext(ctx);
vm.runInContext(mTab[0] + '\n' + mFun[0] + '\nthis.T = IC95_CLOPPER_PEARSON_N10; this.f = textoIC95;', ctx);

// Clopper-Pearson exato por bissecção na binomial (n = 10)
function comb(n, k) { var r = 1; for (var i = 1; i <= k; i++) r = r * (n - k + i) / i; return r; }
function binomCdf(k, n, p) { var s = 0; for (var i = 0; i <= k; i++) s += comb(n, i) * Math.pow(p, i) * Math.pow(1 - p, n - i); return s; }
// limite inferior: P(X >= k | p) = 0,025 (cresce com p); superior: P(X <= k | p) = 0,025 (cai com p)
function clopperPearson(k, n) {
  var inf = 0, sup = 1;
  if (k > 0) { var lo = 0, hi = 1; for (var a = 0; a < 200; a++) { var mid = (lo + hi) / 2; if (1 - binomCdf(k - 1, n, mid) < 0.025) lo = mid; else hi = mid; } inf = (lo + hi) / 2; }
  if (k < n) { var lo2 = 0, hi2 = 1; for (var b = 0; b < 200; b++) { var mid2 = (lo2 + hi2) / 2; if (binomCdf(k, n, mid2) > 0.025) lo2 = mid2; else hi2 = mid2; } sup = (lo2 + hi2) / 2; }
  return [inf, sup];
}
for (var k = 0; k <= 10; k++) {
  var cp = clopperPearson(k, 10);
  var tab = ctx.T[k];
  var okInf = Math.abs(cp[0] * 100 - tab[0]) <= 0.05 + 1e-9;
  var okSup = Math.abs(cp[1] * 100 - tab[1]) <= 0.05 + 1e-9;
  confere(okInf && okSup, 'k=' + k + ': tabela [' + tab[0] + ', ' + tab[1] + '] x exato [' +
          (cp[0] * 100).toFixed(2) + ', ' + (cp[1] * 100).toFixed(2) + ']');
}
confere(ctx.f(100, 10) === '(IC 95%: 69.2–100.0%)', 'textoIC95(100, 10) = ' + ctx.f(100, 10));
confere(ctx.f(50, 10) === '(IC 95%: 18.7–81.3%)', 'textoIC95(50, 10) = ' + ctx.f(50, 10));
confere(ctx.f(0, 10) === '(IC 95%: 0.0–30.8%)', 'textoIC95(0, 10) = ' + ctx.f(0, 10));
confere(ctx.f(10, 10) === '(IC 95%: 0.3–44.5%)', 'textoIC95(10, 10) = ' + ctx.f(10, 10));
confere(ctx.f(100 / 9 * 3, 9) === '(IC indisponível)', 'com 9 análogos: ' + ctx.f(100 / 9 * 3, 9));
confere(ctx.f(0, 0) === '(IC indisponível)', 'sem análogos: ' + ctx.f(0, 0));
confere(ctx.f(undefined, 10) === '(IC indisponível)', 'probabilidade ausente: ' + ctx.f(undefined, 10));

// ---------------------------------------------------------------- 5. apresentação (V4.1, 22/10)
console.log('\n=== 10. Textos do resultado (montarTextosEnso extraída do painel) ===');
var mMont = src06.match(/function montarTextosEnso\(res\) \{[\s\S]*?\n\}/);
confere(!!mMont, 'montarTextosEnso encontrada no painel');
vm.runInContext(mMont[0] + '\nthis.montar = montarTextosEnso;', ctx);

// réplica do motor de análogos (mesma regra do executarMotorPreditivo) sobre a série oficial
function motor(sr, nAnalogos) {
  var n = sr.length, ia = n - 1, atual = sr[ia].RONI, tend = atual - sr[ia - 5].RONI, cand = [];
  for (var i = 5; i <= n - 13; i++) {
    if (sr[i].mes !== sr[ia].mes) continue;
    cand.push({ano: sr[i].ano, sim: Math.abs(sr[i].RONI - atual) + 0.5 * Math.abs((sr[i].RONI - sr[i - 5].RONI) - tend),
               fut: sr[i + 3].RONI, est: sr[i].RONI, traj: sr[i].RONI - sr[i - 5].RONI});
  }
  cand.sort(function (a, b) { return a.sim - b.sim; });
  var top = cand.slice(0, nAnalogos), nA = top.length;
  var conta = function (f) { return 100 * top.filter(f).length / nA; };
  return {
    roniAtual: atual, trimestreAtual: sr[ia].Trimestre, anoAtual: sr[ia].ano, mesAtual: sr[ia].mes,
    fonteAtual: 'CPC_ERSSTv6', horizonteMeses: 3, tendencia: tend, roniInicioTendencia: sr[ia - 5].RONI,
    variacaoTri: atual - sr[ia - 1].RONI, faseAtual: 'Indefinida', mesesIndefinida: alvo.slice(),
    amostrasUsadas: nA, anosAnalogos: top.map(function (x) { return x.ano; }),
    oniFuturoAnalogos: top.map(function (x) { return x.fut; }),
    roniEstacaoAnalogos: top.map(function (x) { return x.est; }), trajetoriaAnalogos: top.map(function (x) { return x.traj; }),
    similaridadeAnalogos: top.map(function (x) { return x.sim; }), pesoTendencia: 0.5,
    pElNino: conta(function (x) { return x.fut >= 0.5; }), pLaNina: conta(function (x) { return x.fut <= -0.5; }),
    pNeutro: conta(function (x) { return x.fut >= -0.49 && x.fut < 0.5; })
  };
}
var res = motor(serie, 10);
confere(res.anosAnalogos.join(',') === '1997,1965,2015,1972,1963,1982,2023,1957,1987,1951',
        'análogos (ordem de semelhança) iguais ao roteiro 6.4: ' + res.anosAnalogos.join(','));
var t = ctx.montar(res);
['titulo', 'situacao', 'variacao', 'tituloPrevisao', 'analogos', 'elnino', 'neutro', 'lanina', 'detalhes', 'nota'].forEach(function (k) {
  console.log('  ' + t[k].split('\n').join('\n  '));
});
// [2026.10.7] textos reorganizados: AGORA em tópicos, resposta curta primeiro, "Como ler" atrás de um botão
confere(t.titulo === '🌊 AGORA (julho a setembro de 2026)', 'título com os meses por extenso');
confere(t.situacao.indexOf('• Temperatura do mar: 1,7 °C acima do normal (índice RONI +1,7 °C).') !== -1, 'RONI atual em linguagem simples');
confere(t.situacao.indexOf('• Situação: já no nível de El Niño forte. A tabela histórica do CPC/NOAA só registra o episódio depois de 5 trimestres seguidos acima de +0,5 °C (até agora são 4), mas o CPC pode já ter declarado condições de El Niño no boletim do mês: confira o alerta no site do CPC.') === 0, 'correção 1: regra dos 5 trimestres = tabela histórica; CPC pode já ter declarado');
confere(t.situacao.indexOf('ainda não é oficial') === -1 && t.nota.indexOf('O episódio só é oficial') === -1, 'correção 1: nenhum "não é oficial" no texto');
confere(t.situacao.indexOf('• Últimos 5 meses: esquentou 2,1 °C (em fevereiro a abril de 2026 estava 0,4 °C abaixo do normal).') !== -1, 'trajetória de 5 meses');
confere(t.situacao.indexOf('• Fonte: CPC/NOAA (valor oficial).') !== -1, 'fonte');
confere(t.situacao.split('\n').length === 4, 'AGORA em 4 tópicos curtos');
confere(t.variacao === '• Último mês: subiu 0,3 °C, sem mudança brusca.' && t.corVariacao === '#0b5d1e', 'último mês');
confere(t.tituloPrevisao === '🔮 PRÓXIMOS 3 MESES (outubro a dezembro de 2026)', 'período previsto por extenso');
confere(t.analogos.split('\n')[0] === 'Resposta curta: El Niño muito provável (10 dos 10 anos mais parecidos com agora tiveram El Niño nesses meses).', 'resposta curta primeiro');
confere(t.detalhes.indexOf('📅 Anos parecidos: 1951, 1957, 1963, 1965, 1972, 1982, 1987, 1997, 2015 e 2023 (o mais parecido foi 1997).') === 0, 'análogos em ordem crescente');
confere(t.elnino.split('\n')[0] === '🔥 El Niño: 10 de 10 anos (100%)', 'linha principal do El Niño');
confere(t.elnino.indexOf('• muito forte (+2,0 °C ou mais): 1965, 1972, 1982, 1997 e 2015') !== -1, 'muito forte com os 5 anos');
confere(t.elnino.indexOf('• forte (+1,5 a +1,9 °C): 1957') !== -1, 'forte: 1957');
confere(t.elnino.indexOf('• moderado (+1,0 a +1,4 °C): 1963, 1987 e 2023') !== -1, 'moderado: 1963, 1987 e 2023');
confere(t.elnino.indexOf('• fraco (+0,5 a +0,9 °C): 1951') !== -1, 'fraco: 1951');
confere(t.neutro === '⚪ Neutro: 0 de 10 anos (0%)', 'neutro 0%');
confere(t.lanina === '❄️ La Niña: 0 de 10 anos (0%)', 'La Niña 0%');
confere(t.nota.indexOf('• Por que não é certeza, se deu 10 em 10? Porque 10 anos é pouco. Fazendo a conta da margem de erro (intervalo de confiança de 95%), a chance de El Niño fica entre 69% e 100%: muito provável, mas não garantido.') !== -1, 'confiança do resultado principal');
confere(t.nota.indexOf('nesta mesma época (julho a setembro), olhando o valor e a tendência dos últimos 5 meses. Depois vimos o que o oceano fez 3 meses depois (outubro a dezembro) naqueles anos.') !== -1, 'o que foi comparado (oceano, não efeitos), no "Como ler"');
confere(t.detalhes.indexOf('Use o item B, logo abaixo. Os dados de clima começam em 1961: 1951 e 1957 ficam de fora.') !== -1, 'remete ao item B e avisa dos anos parecidos antes de 1961');
confere(t.detalhes.split('\n').pop() === 'Não é a previsão oficial: compare com a do CPC/NOAA.', 'lembrete da previsão oficial sempre visível');
confere(t.nota.indexOf('• A força do fenômeno é bem mais incerta: "muito forte" apareceu em 5 dos 10 anos (50%), mas pela mesma conta pode ficar entre 19% e 81%.') !== -1, 'incerteza da intensidade');
confere(t.nota.indexOf('Ela não cobre o erro do próprio método') !== -1, 'limite da margem explicado');
confere(t.nota.indexOf('centro-leste do Pacífico equatorial com a média de todos os oceanos tropicais') !== -1, 'definição do RONI (CPC)');
confere(t.nota.indexOf('(JAS = julho a setembro de 2026; OND = outubro a dezembro de 2026)') !== -1, 'siglas explicadas');
confere(t.nota.indexOf('Clopper') === -1 && t.nota.indexOf('neutro até') === -1, 'sem a lista longa de intervalos');
confere(t.aviso === null, 'contagem do cliente = contagem do servidor (sem aviso)');
// contagem divergente: o painel avisa
var resErr = JSON.parse(JSON.stringify(res)); resErr.pElNino = 90;
confere(ctx.montar(resErr).aviso !== null, 'contagem divergente gera aviso');
// com 9 análogos: sem IC, texto coerente
var t9 = ctx.montar(motor(serie, 9));
confere(t9.nota.indexOf('só é calculada com exatamente 10 anos') !== -1 && t9.elnino.indexOf(' de 9 anos') !== -1, 'com 9 análogos: IC indisponível');
// virada de ano: estação NDJ + 3 = FMA do ano seguinte; fonte OISST; resfriamento rápido
var rV = JSON.parse(JSON.stringify(res));
rV.trimestreAtual = 'NDJ'; rV.fonteAtual = 'Estimativa_OISST'; rV.variacaoTri = -0.5; rV.faseAtual = 'El Nino';
var tV = ctx.montar(rV);
confere(tV.tituloPrevisao === '🔮 PRÓXIMOS 3 MESES (fevereiro a abril de 2027)', 'NDJ 2026 + 3 meses = FMA 2027');
confere(tV.titulo === '🌊 AGORA (novembro de 2026 a janeiro de 2027)', 'NDJ 2026 = nov/2026 a jan/2027');
confere(tV.situacao.indexOf('• Fonte: estimativa provisória por satélite (OISST); o CPC/NOAA ainda não publicou este trimestre.') !== -1, 'fonte OISST identificada');
confere(tV.variacao === '⚠️ Último mês: caiu 0,5 °C (resfriamento rápido).' && tV.corVariacao === '#1d70b8', 'resfriamento rápido em azul');
confere(tV.situacao.indexOf('• Situação: El Niño forte, episódio já confirmado.') === 0, 'episódio confirmado');
rV.trimestreAtual = 'SON';
confere(ctx.montar(rV).tituloPrevisao === '🔮 PRÓXIMOS 3 MESES (dezembro de 2026 a fevereiro de 2027)', 'SON 2026 + 3 meses = DJF 2027 (dez/2026 a fev/2027)');
var rN = JSON.parse(JSON.stringify(res)); rN.roniAtual = 0.2; rN.faseAtual = 'Neutro'; rN.variacaoTri = 0.5;
var tN = ctx.montar(rN);
confere(tN.situacao.indexOf('0,2 °C acima do normal') !== -1 && tN.situacao.indexOf('• Situação: neutro (nem El Niño, nem La Niña).') === 0, 'caso neutro');
confere(tN.variacao === '⚠️ Último mês: subiu 0,5 °C (aquecimento rápido).' && tN.corVariacao === '#d73027', 'aquecimento rápido em vermelho');
var rL = JSON.parse(JSON.stringify(res)); rL.roniAtual = -1.2; rL.faseAtual = 'La Nina'; rL.roniInicioTendencia = 0.3; rL.tendencia = -1.5;
var tL = ctx.montar(rL);
confere(tL.situacao.indexOf('• Temperatura do mar: 1,2 °C abaixo do normal (índice RONI −1,2 °C).') !== -1 && tL.situacao.indexOf('• Situação: La Niña moderada, episódio já confirmado.') === 0, 'caso La Niña: valor negativo e concordância');
var rL2 = JSON.parse(JSON.stringify(rL)); rL2.faseAtual = 'Indefinida'; rL2.mesesIndefinida = ['2026_07', '2026_08'];
confere(ctx.montar(rL2).situacao.indexOf('5 trimestres seguidos abaixo de −0,5 °C (até agora são 2), mas o CPC pode já ter declarado condições de La Niña') !== -1, 'La Niña ainda não registrada (correção 1)');
confere(tL.situacao.indexOf('esfriou 1,5 °C') !== -1, 'caso La Niña: esfriou');

var rM = JSON.parse(JSON.stringify(res));
rM.oniFuturoAnalogos = [2.3, 1.2, 0.8, 0.6, 0.2, 0.1, -0.1, 0.3, 0.7, 1.6]; rM.pElNino = 60; rM.pNeutro = 40; rM.pLaNina = 0;
var tM = ctx.montar(rM);
confere(tM.aviso === null && tM.nota.indexOf('• Quão certo é? El Niño apareceu em 6 dos 10 anos (60%), mas 10 anos é pouco. Fazendo a conta da margem de erro (intervalo de confiança de 95%), a chance de El Niño fica entre 26% e 88%.') !== -1, 'resultado misto: 6 de 10');
confere(tM.analogos.indexOf('Resposta curta: El Niño um pouco mais provável que as outras opções (6 dos 10') === 0, 'resposta curta do resultado misto');
confere(tM.neutro === '⚪ Neutro: 4 de 10 anos (40%)\n   • ' + tM.neutro.split('• ')[1], 'neutro com a lista de anos');
var rZ = JSON.parse(JSON.stringify(res));
rZ.oniFuturoAnalogos = [0.1, 0.2, -0.3, 0, 0.4, -0.2, 0.3, 0.1, -0.1, 0]; rZ.pElNino = 0; rZ.pNeutro = 100; rZ.pLaNina = 0;
var tZ = ctx.montar(rZ);
confere(tZ.nota.indexOf('a chance de neutralidade fica entre 69% e 100%: muito provável') !== -1 && tZ.nota.indexOf('força do fenômeno') === -1, 'neutro dominante: sem linha de intensidade');
confere(tZ.analogos.indexOf('Resposta curta: neutralidade muito provável') === 0 && tZ.avisoForca === null, 'neutro dominante: resposta curta e sem aviso de força');
var r7 = JSON.parse(JSON.stringify(res));
r7.oniFuturoAnalogos = [2.3, 1.2, 0.8, 0.6, 0.9, 1.1, 0.7, 0.3, 0.1, -0.6]; r7.pElNino = 70; r7.pNeutro = 20; r7.pLaNina = 10;
confere(ctx.montar(r7).analogos.indexOf('Resposta curta: El Niño provável (7 dos 10') === 0, '7 de 10 = provável');
var rE = JSON.parse(JSON.stringify(res));
rE.oniFuturoAnalogos = [2.3, 1.2, 0.8, 0.6, 0.9, 0.1, 0.2, 0.3, 0.1, -0.6]; rE.pElNino = 50; rE.pNeutro = 40; rE.pLaNina = 10;
confere(ctx.montar(rE).analogos.indexOf('Resposta curta: El Niño incerto') === 0, '5 de 10 = incerto (sem maioria)');
var rD = JSON.parse(JSON.stringify(res));
rD.oniFuturoAnalogos = [2.3, 1.2, 0.8, 0.6, 0.9, 0.1, 0.2, 0.3, 0.1, 0.4]; rD.pElNino = 50; rD.pNeutro = 50; rD.pLaNina = 0;
confere(ctx.montar(rD).analogos.indexOf('Resposta curta: resultado dividido. Nos anos parecidos, El Niño e neutralidade apareceram 5 vezes cada.') === 0, 'empate = resultado dividido');
['titulo', 'situacao', 'variacao', 'tituloPrevisao', 'analogos', 'elnino', 'neutro', 'lanina', 'detalhes', 'nota'].forEach(function (k) {
  confere(typeof t[k] === 'string' && t[k].length > 0, 'texto "' + k + '" preenchido');
});
confere(src06.indexOf("label_detalhes_enso.setValue(t.detalhes)") !== -1 && src06.indexOf("btn_como_ler_enso.onClick") !== -1 &&
        /label_nota_ic = ui\.Label\('', \{[^}]*shown: false/.test(src06), 'tela: detalhes visíveis e "Como ler" escondido atrás do botão');

console.log('\n=== 11. CSV da previsão por link direto (montarLinhasExportEnso extraída do painel) ===');
var mExp = src06.match(/function montarLinhasExportEnso\(res, dataExtracao\) \{[\s\S]*?\n\}/);
confere(!!mExp, 'montarLinhasExportEnso encontrada no painel');
vm.runInContext(mExp[0] + '\nthis.exp = montarLinhasExportEnso;', ctx);
var E = ctx.exp(res, '2026-10-22');
var R = E.resumo;
console.log('  ' + E.colsResumo.map(function (c) { return c + '=' + R[c]; }).join('\n  '));
E.analogos.forEach(function (x) { console.log('  ' + E.colsAnalogos.map(function (c) { return x[c]; }).join(' | ')); });
confere(R.Estacao_Atual === 'JAS 2026' && R.Estacao_Prevista === 'OND 2026', 'estação atual e prevista');
confere(R.Anos_Analogos === '1951;1957;1963;1965;1972;1982;1987;1997;2015;2023' && R.Analogo_Mais_Parecido === 1997, 'anos em ordem crescente e o mais parecido');
confere(R.Prob_El_Nino_pct === 100 && R.IC95_El_Nino_pct === '69.2 a 100.0' && R.IC95_Neutro_pct === '0.0 a 30.8', 'probabilidades e IC95');
confere(R.Prob_El_Nino_Muito_Forte_pct === 50 && R.Prob_El_Nino_Forte_pct === 10 && R.Prob_El_Nino_Moderado_pct === 30 &&
        R.Prob_El_Nino_Fraco_pct === 10, 'intensidades = tela (50/10/30/10)');
confere(R.Leitura_Ultimo_Mes === 'sem mudanca brusca' && R.Variacao_Ultimo_Mes_C === '0.3' && R.RONI_Atual_C === '1.7' && R.Tendencia_5_Meses_C === '2.1', 'variação do último mês e RONI com 1 casa');
confere(E.colsAnalogos.join(',') === 'Ano,Ordem_Semelhanca,RONI_JAS_C,Trajetoria_5_Meses_C,Distancia_Semelhanca,RONI_OND_C,Fase_OND,Intensidade_OND', 'colunas do CSV dos análogos');
var a97 = E.analogos.filter(function (x) { return x.Ano === 1997; })[0];
confere(a97.Ordem_Semelhanca === 1 && a97.RONI_JAS_C === '1.8' && a97.RONI_OND_C === '2.3' && a97.Distancia_Semelhanca === '0.35' && a97.Intensidade_OND === 'Muito forte (Super)', '1997: 1º, JAS 1.8, OND 2.3, distância 0.35, muito forte');
var a65 = E.analogos.filter(function (x) { return x.Ano === 1965; })[0];
confere(a65.RONI_OND_C === '2.0' && a65.Trajetoria_5_Meses_C === '1.3', 'correção 3: 1965 OND = "2.0" (uma casa decimal)');
var t4 = ctx.montar(res);
confere(t4.nota.indexOf('o RONI de outubro a dezembro foi no máximo +2,3 °C. Ele não consegue indicar um evento mais forte que esse') !== -1, 'correção 4: limite do método (máx. +2,3)');
confere(t4.detalhes.indexOf('⚠️ Atenção: o aquecimento de agora (+2,1 °C em 5 meses) é maior que o de todos os anos parecidos (no máximo +1,6 °C, em 1997). Por isso, a força real tende a ser maior que a indicada aqui.') !== -1 && t4.avisoForca !== null, 'correção 4: aquecimento atual acima de todos os análogos (visível, fora do "Como ler")');
var rLento = JSON.parse(JSON.stringify(res)); rLento.tendencia = 1.0;
confere(ctx.montar(rLento).detalhes.indexOf('Atenção:') === -1 && ctx.montar(rLento).avisoForca === null, 'correção 4: sem o aviso quando o aquecimento atual não é o maior');
var a51 = E.analogos.filter(function (x) { return x.Ano === 1951; })[0];
confere(a51.Ordem_Semelhanca === 10 && a51.Fase_OND === 'El Nino' && a51.Intensidade_OND === 'Fraco', '1951: 10º, El Niño fraco');
var semAcento = JSON.stringify(E).replace(/[–]/g, '');
confere(!/[^\x00-\x7F]/.test(semAcento), 'CSV sem acentos (Excel abre sem estragar)');
confere(src06.split('\n').filter(function (l) { return /Export\.(table|image)\./.test(l) && !/^\s*\/\//.test(l); }).length === 0,
        'nenhum download do painel depende da aba Tasks');
confere(E.sufixo === 'OND_2026', 'nome do arquivo: Previsao_ENSO_OND_2026_...');

console.log('\n=== 12. Lista de meses do filtro (montarListaMesesEnso extraída do painel) ===');
var mLista = src06.match(/function montarListaMesesEnso\(lista\) \{[\s\S]*?\n\}/);
confere(!!mLista, 'montarListaMesesEnso encontrada no painel');
vm.runInContext(mLista[0] + '\nthis.lista = montarListaMesesEnso;', ctx);
var superNino = aplicarCenario(v4, 'Super El Niño', true).map(function (e) {
  return {ano: e.ano, mes: e.mes, RONI: e.RONI, FaseENSO: e.FaseENSO, Fonte: 'CPC_ERSSTv6'};
});
var Lm = ctx.lista(superNino.slice().reverse());
Lm.forEach(function (x) { console.log('  ' + [x.Ano, x.Mes, x.Mes_Nome, x.Trimestre_CPC, x.Meses_do_Trimestre, x.RONI_C, x.Fase, x.Intensidade, x.Fonte_RONI].join(' | ')); });
var chaves = Lm.map(function (x) { return x.Ano + '_' + x.Mes; }).join(',');
confere(Lm[0].RONI_C === '2.0' && Lm[3].RONI_C === '2.2', 'correção 3: RONI da lista com uma casa (2.0)');
confere(chaves === '1965_11,1972_11,1982_10,1982_11,1982_12,1983_1,1983_2,1991_12,1992_1,1992_2,1997_9,1997_10,1997_11,1997_12,1998_1,2015_10,2015_11,2015_12,2016_1',
        'Super El Niño: os 19 meses da matriz que o usuário baixou, em ordem cronológica');
var dez82 = Lm.filter(function (x) { return x.Ano === 1983 && x.Mes === 1; })[0];
confere(dez82.Trimestre_CPC === 'DJF' && dez82.Meses_do_Trimestre === 'dez/1982 a fev/1983' && dez82.Mes_Nome === 'janeiro',
        'janeiro de 1983 = trimestre DJF (dez/1982 a fev/1983)');
var nd = Lm.filter(function (x) { return x.Ano === 1991 && x.Mes === 12; })[0];
confere(nd.Trimestre_CPC === 'NDJ' && nd.Meses_do_Trimestre === 'nov/1991 a jan/1992', 'dezembro de 1991 = NDJ (nov/1991 a jan/1992)');
confere(Lm.every(function (x) { return x.Intensidade === 'Muito forte (Super)' && x.Fase === 'El Nino'; }), 'fase e intensidade em todas as linhas');
confere(!/[^\x00-\x7F]/.test(JSON.stringify(Lm)), 'lista sem acentos');
var fracaNina = ctx.lista([{ano: 2000, mes: 3, RONI: -0.7, FaseENSO: 'La Nina', Fonte: 'Estimativa_OISST'}])[0];
confere(fracaNina.Intensidade === 'Fraca' && fracaNina.Mes_Nome === 'marco' && fracaNina.Fonte_RONI === 'Estimativa OISST (provisoria)', 'La Niña fraca, março sem acento, fonte OISST');
confere(src06.indexOf('RONI e força), sem dados de clima.') !== -1 && src06.indexOf('Só a lista de meses do fenômeno (sem dados de clima)') !== -1,
        'botão e nota: a lista não tem dados de clima');

console.log('\n=== 13. Colunas ENSO nos CSV de dados (só com o filtro do item B) ===');
function pega(nome) { var i = src06.indexOf('function ' + nome + '('); return src06.slice(i, src06.indexOf('\n}\n', i) + 2); }
var mCol = src06.match(/var COLUNAS_ENSO = \[[^\]]*\];/);
vm.runInContext(mCol[0] + '\n' + pega('sufixoArquivoEnso') + '\nthis.COL = COLUNAS_ENSO; this.suf = sufixoArquivoEnso;', ctx);
confere(ctx.COL.join(',') === 'Filtro_ENSO,Fase_ENSO,Intensidade_ENSO,RONI_Trimestre_C,Trimestre_CPC', 'colunas ENSO');
var mCen = src06.match(/var CENARIOS_ENSO = \[[\s\S]*?\n\];/);
vm.runInContext(mCen[0] + '\n' + pega('infoCenarioEnso') + '\n' + pega('sufixoArquivoEnso') + '\nthis.CEN = CENARIOS_ENSO; this.suf = sufixoArquivoEnso; this.info = infoCenarioEnso;', ctx);
confere(ctx.suf('Super El Niño (≥ 2.0°C)') === '_El_Nino_Muito_Forte' && ctx.suf('La Niña Forte (-1.5 a -1.9°C)') === '_La_Nina_Forte' &&
        ctx.suf('Anos Neutros') === '_Neutro' && ctx.suf(null) === '', 'sufixo do nome do arquivo');
// os valores internos da lista são exatamente as chaves do filtroCenario (nenhum cenário perdido)
var chavesFiltro = (src06.match(/function filtroCenario[\s\S]*?\n\}/)[0].match(/'[^']+':\s+ee\.Filter/g) || []).map(function (x) { return x.split("'")[1]; });
var valores = ctx.CEN.map(function (c) { return c.value; });
confere(chavesFiltro.length === 9 && chavesFiltro.every(function (k) { return valores.indexOf(k) !== -1; }) && valores[0] === 'Todos os Anos' && valores.length === 10,
        'valores da lista = chaves do filtroCenario (9 cenários + sem filtro)');
// mesmos nomes e faixas do item A (vírgula decimal, "muito forte", sinais)
var rotulos = ctx.CEN.map(function (c) { return c.label; });
console.log('  rótulos: ' + rotulos.join(' | '));
confere(rotulos.indexOf('El Niño muito forte, Super (+2,0 °C ou mais)') !== -1 && rotulos.indexOf('El Niño forte (+1,5 a +1,9 °C)') !== -1 &&
        rotulos.indexOf('La Niña fraca (−0,5 a −0,9 °C)') !== -1 && rotulos.indexOf('Neutro (entre −0,5 e +0,5 °C)') !== -1, 'rótulos com os nomes e faixas do item A');
confere(rotulos.every(function (r) { return !/\d\.\d/.test(r); }), 'nenhum rótulo com ponto decimal');
confere(ctx.CEN.every(function (c) { return !/[^\x00-\x7F]/.test(c.ascii + c.arquivo); }), 'Filtro_ENSO e nome do arquivo sem acentos');
var dia = pega('exportarSerieDiaria'), mes = pega('exportarSerieMensal');
confere(/getColunasClimaDiaria\(\)\.concat\(cenarioEnso \? COLUNAS_ENSO : \[\]\)/.test(dia) &&
        /getColunasClimaMensal\(\)\.concat\(cenarioEnso \? COLUNAS_ENSO : \[\]\)/.test(mes), 'colunas ENSO só com o filtro, no fim (diário e mensal)');
confere(dia.indexOf('comAnosComDados(') !== -1 && mes.indexOf('comAnosComDados(') !== -1, 'anos sem o fenômeno não geram arquivo');
confere(src06.indexOf("ee.Filter.inList('versao', VERSOES_PREVISAO)") !== -1 && src06.indexOf('ic_periodo.filterDate(datas.dataIni, hojeRef)') === -1, 'correção 2: passado e previsão separados pelo tipo de dado, não pela data');
var pE = pega('propsEnsoDaImagem');
confere(pE.indexOf("'Previsao (sem classificacao)'") !== -1 && /'RONI_Trimestre_C':[^\n]*'-'\)/.test(pE) && pE.indexOf('triData') !== -1, 'correção 2: previsão marcada (fase, "-" e trimestre pela data)');
confere(src06.indexOf("APP.filtroEnso = select_enso.getValue();") !== -1 && src06.indexOf('APP.filtroEnso = null;') !== -1, 'estado do filtro definido a cada processamento');
confere(src06.indexOf("'Variavel': 'Fase_ENSO'") !== -1 && src06.indexOf("'Variavel': 'RONI_Trimestre_C'") !== -1, 'colunas ENSO no dicionário');



console.log('\n' + (falhas === 0 ? '✅' : '❌') + ' ' + (total - falhas) + ' de ' + total + ' verificações OK');
process.exit(falhas === 0 ? 0 : 1);
