// ============================================================
// CONFERÊNCIA DA MATRIZ GFS V2 (CODE EDITOR; SÓ LEITURA)
// Rode depois que as 12 tarefas GERAR_MATRIZ_GFS_V2_xx terminarem (COMPLETED).
// O que conferir no Console e no mapa está descrito em cada bloco.
//
// [V4] Esta versão confere a matriz V2.1 (03_matriz_gfs_v2_1.py). O relatório sai no Console
// de uma vez, em 1 a 3 minutos, em 5 blocos com ✅/⚠️/❌, seguido de um RESUMO. Nada é gravado.
//
// MUDANÇAS V4 (20/10/2026)
//   [V4 M04-04] Os 12 meses (antes só janeiro): 100 bandas na ordem do contrato, propriedades
//               V2.1 (versao_matriz, inicio_rodadas, n_pares_* > 0 etc.), mesma contagem de
//               pixels em todas as bandas, n_{faixa} mínimo e mediano por pixel.
//   [V4 M04-01] Por mês e faixa: mediana, p5 e p95 de (GFS − BR-DWGD) para Tmax, Tmin e UR;
//               fator que o motor V1.5 aplica nos dias GFS [V4 A-01]: chuva (BR+0,1)/(GFS+0,1)
//               com teto 5; vento e radiação BR/max(GFS, 1e-3) limitado a [0,5; 2] (mediana,
//               % no teto, % no piso); razão das somas de chuva na área.
//   [V4 M04-02] Detalhe espacial (razão de gradientes do E4) por faixa nos meses 01 e 07.
//   [V4 M04-03] Radiação: (Rs GFS/BR-DWGD) da V2.1 L1 contra a mesma razão da V1.
//   [V4 M04-05] Reduções na grade nativa (EPSG:4326 + crsTransform do BR-DWGD); percentis
//               exatos numa amostra de ~5.000 pixels por mês (maxRaw acima da amostra).
//   Tudo por evaluate (assíncrono, no máximo 4 pedidos ao mesmo tempo); nenhum getInfo.
//   As camadas do mapa da Serra do Mar continuam as mesmas.
// ============================================================
var COLECAO = 'projects/clima-492922/assets/SICSB_MATRIZ_GFS_V2';
var FAIXAS = ['L1', 'L2a5', 'L6a10', 'L11a15'];
var regiao = ee.Geometry.Rectangle([-74, -34, -34, 6], null, false);

// [V4] Configuração da conferência
var MATRIZ_V1 = 'projects/clima-492922/assets/SICSB_MATRIZ_GFS';
var VARS = ['pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs'];
var MESES = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
var CRS = 'EPSG:4326';   // [V4 M04-05] grade nativa do BR-DWGD (a mesma da matriz)
var TRANSFORM = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432];
var BRASIL = ee.FeatureCollection('FAO/GAUL/2015/level0').filter(ee.Filter.eq('ADM0_NAME', 'Brazil')).geometry();
var CAIXA_SERRA = ee.Geometry.Rectangle([-48.5, -24.8, -43.5, -21.5], null, false);   // a mesma do E4 (08)
var N_AMOSTRA = 5000;      // [V4 M04-05] pixels sorteados por mês para percentis e medianas
var MAX_RAW = 20000;       // maior que a amostra: o percentil usa os valores brutos (sem histograma)
var MAX_SIMULTANEOS = 4;   // pedidos ao servidor ao mesmo tempo

// [V4] Limiares. Os marcados como heurísticos devem ser recalibrados depois da 1ª execução.
var LIM = {
  viesT: 5,            // |mediana GFS − BR| de Tmax e Tmin (°C): ❌ acima (critério do roteiro v3)
  caudaT: 10,          // |p5| ou |p95| de Tmax e Tmin (°C): ⚠️ acima (heurístico)
  viesRH: 20,          // |mediana| de UR (pontos): ⚠️ acima (heurístico)
  fatorMed: [0.5, 2],  // mediana do fator BR/GFS fora desta faixa: ⚠️ (heurístico)
  fracPr: 0.10,        // [V4 A-01] fração de pixels com o fator de chuva do motor V1.5 no teto (5) ou < 0,2: ⚠️ acima (heurístico)
  fracU2Rs: 0.005,     // [V4 A-01] fração de pixels com fator de vento ou radiação fora de [0,5; 2] (limitado pelo motor): ⚠️ acima
  razaoPr: [0.5, 2],   // Σ chuva GFS / Σ chuva BR-DWGD na área: ❌ fora (critério do roteiro v3)
  nMin: 0.9,           // n_{faixa} mínimo por pixel abaixo de 90% de n_pares: ⚠️
  minPares: 0.85,      // n_pares abaixo de 85% do máximo possível: ⚠️ (o mesmo limiar do 03)
  gradV1: 0.230,       // razão de gradientes da V1 (auditoria E4)
  gradMin: 0.30,       // mínimo esperado para o GFS 0,25° reamostrado (M04-02)
  rsV1: [0.85, 1.0]    // (Rs GFS/BR V2.1 L1) / (Rs GFS/BR V1): faixa informativa (correção F4)
};

// [V4 M04-04] Máximo de pares dia x prazo por mês, [L1, L2a5, L6a10, L11a15]
// (testes/maximos_pares_v16.py; rodadas 00Z de 2021-03-23 a 2025-12-31)
var MAXIMO_PARES = {
  '01': [124, 496, 620, 620], '02': [113, 452, 565, 565], '03': [133, 522, 630, 620],
  '04': [150, 600, 750, 735], '05': [155, 620, 775, 775], '06': [150, 600, 750, 750],
  '07': [155, 620, 775, 775], '08': [155, 620, 775, 775], '09': [150, 600, 750, 750],
  '10': [155, 620, 775, 775], '11': [150, 600, 750, 750], '12': [155, 620, 775, 775]
};

// [V4 M04-04] Propriedades do contrato V2.1 (além de mes_referencia, n_pares_* e gerado_em)
var CONTRATO = {
  versao_matriz: 'V2.1', modelo_gfs: 'GFS v16', inicio_rodadas: '2021-03-23', fim_dias: '2025-12-31',
  leads_L1: '1', leads_L2a5: '2,3,4,5', leads_L6a10: '6,7,8,9,10', leads_L11a15: '11,12,13,14,15',
  metodo_pr: 'soma_blocos_6h', metodo_rs: 'media_blocos_6h',
  janela: '(00Z,24Z] UTC do dia previsto; rodada 00Z de D-(L-1)'
};

// [V4 M04-04] As 100 bandas na ordem do 03: médias, desvios (faixa, fonte, variável) e n_ no fim
var ESPERADAS = [];
['m', 's'].forEach(function(t) {
  FAIXAS.forEach(function(fx) {
    ['sicsb', 'gfs'].forEach(function(fonte) {
      VARS.forEach(function(v) { ESPERADAS.push(v + '_' + t + '_' + fonte + '_' + fx); });
    });
  });
});
var NOMES_N = FAIXAS.map(function(fx) { return 'n_' + fx; });
ESPERADAS = ESPERADAS.concat(NOMES_N);

// ------------------------------------------------------------
// [V4] Relatório: as linhas ficam guardadas por bloco e por mês e saem em ordem no fim
// ------------------------------------------------------------
var TITULOS = [
  '1. Estrutura e propriedades (esperado: 12 matrizes, 100 bandas, contrato V2.1, n_pares perto do máximo)',
  '2. Cobertura (mesma contagem de pixels nas 100 bandas) e pares por pixel (n_{faixa})',
  '3. Por mês e faixa. Tmax/Tmin/RH: mediana [p5; p95] de GFS − BR-DWGD (°C; pontos de UR). ' +
    'fator aplicado pelo motor V1.5: mediana (% de pixels no teto; % no piso). Chuva: (BR+0,1)/(GFS+0,1), ' +
    'teto 5, piso informativo 0,2. Vento e radiação: BR/GFS limitado a [0,5; 2]. ' +
    'Σchuva = soma GFS / soma BR-DWGD na área',
  '4. Detalhe espacial na Serra do Mar: razão de gradientes de Tmax GFS/BR-DWGD (E4; V1 = 0,230)',
  '5. Radiação: (Rs GFS/BR-DWGD) da V2.1 L1 dividido pelo mesmo da V1 (informativo; esperado 0,85 a 1,0)'
];
var saida = [{}, {}, {}, {}, {}];
var totais = {'✅': 0, '⚠️': 0, '❌': 0};
var alertas = [];
var npares = {};   // mês -> {faixa: n_pares gravado no asset}

function anota(secao, chave, nivel, texto) {
  var s = saida[secao - 1];
  if (!s[chave]) s[chave] = [];
  s[chave].push((nivel ? nivel + ' ' : '   ') + texto);
  if (nivel) {
    totais[nivel] += 1;
    if (nivel !== '✅') alertas.push(nivel + ' [' + secao + '] ' + texto);
  }
}
function vazio(x) { return x === null || x === undefined || isNaN(x); }
function pior(niveis) {
  if (niveis.indexOf('❌') >= 0) return '❌';
  if (niveis.indexOf('⚠️') >= 0) return '⚠️';
  return '✅';
}
function f(x, d) { return vazio(x) ? 'n/d' : Number(x).toFixed(d); }
function pct(x) { return vazio(x) ? 'n/d' : (100 * x).toFixed(1) + '%'; }
function sinal(x, d) { return vazio(x) ? 'n/d' : (x >= 0 ? '+' : '') + Number(x).toFixed(d); }
function fora(x, faixa) { return vazio(x) || x < faixa[0] || x > faixa[1]; }

// Reduções na grade nativa da matriz [V4 M04-05]
function reduzir(img, reducer, geom) {
  return img.reduceRegion({reducer: reducer, geometry: geom || regiao, crs: CRS, crsTransform: TRANSFORM,
                           maxPixels: 1e9, tileScale: 4});
}
function gradiente(banda) {   // o mesmo cálculo do E4 da auditoria 08
  var g = banda.gradient();
  return g.select('x').hypot(g.select('y'));
}

// Fila de pedidos: no máximo MAX_SIMULTANEOS ao mesmo tempo; relatório quando a fila esvazia
var fila = [];
var ativos = 0;
var relatorioImpresso = false;
function agenda(tarefa) { fila.push(tarefa); despacha(); }
function despacha() {
  while (ativos < MAX_SIMULTANEOS && fila.length > 0) {
    ativos += 1;
    executa(fila.shift());
  }
  if (ativos === 0 && fila.length === 0 && !relatorioImpresso) {
    relatorioImpresso = true;
    imprimeRelatorio();
  }
}
function executa(tarefa) {
  var terminou = false;
  function feito() {
    if (terminou) return;
    terminou = true;
    ativos -= 1;
    despacha();
  }
  try {
    tarefa(feito);
  } catch (e) {
    anota(1, 'zz', '❌', 'Erro no script de conferência: ' + e);
    feito();
  }
}
function protegido(secao, chave, rotulo, corpo, feito) {   // erro de interpretação não trava a fila
  try {
    corpo();
  } catch (e) {
    anota(secao, chave, '❌', rotulo + ': erro ao interpretar o resultado (' + e + ')');
  }
  feito();
}

// ------------------------------------------------------------
// 1. Estrutura e propriedades [V4 M04-04]
// ------------------------------------------------------------
function avaliarEstrutura(mm, r) {
  var bandas = r.bandas || [];
  var props = r.props || {};
  var faltam = ESPERADAS.filter(function(b) { return bandas.indexOf(b) < 0; });
  var sobram = bandas.filter(function(b) { return ESPERADAS.indexOf(b) < 0; });
  if (faltam.length || sobram.length) {
    anota(1, mm, '❌', 'Mês ' + mm + ': ' + bandas.length + ' bandas (esperado 100); faltam ' +
          faltam.length + ' ' + JSON.stringify(faltam.slice(0, 6)) + '; sobram ' + sobram.length + ' ' +
          JSON.stringify(sobram.slice(0, 6)));
  } else if (bandas.join(',') !== ESPERADAS.join(',')) {
    anota(1, mm, '⚠️', 'Mês ' + mm + ': 100 bandas, mas fora da ordem do contrato (o motor seleciona por nome).');
  } else {
    anota(1, mm, '✅', 'Mês ' + mm + ': 100 bandas na ordem do contrato.');
  }

  var erros = [];
  Object.keys(CONTRATO).forEach(function(k) {
    if (props[k] !== CONTRATO[k]) erros.push(k + ' = ' + JSON.stringify(props[k]) + ' (esperado ' + JSON.stringify(CONTRATO[k]) + ')');
  });
  if (Number(props.mes_referencia) !== parseInt(mm, 10)) erros.push('mes_referencia = ' + JSON.stringify(props.mes_referencia));
  if (!props.gerado_em) erros.push('gerado_em ausente');
  anota(1, mm, erros.length ? '❌' : '✅', 'Mês ' + mm + ': propriedades ' +
        (erros.length ? 'com problema: ' + erros.join('; ') : 'do contrato V2.1 conferem (gerado_em ' + props.gerado_em + ').'));

  var n = {};
  var partes = [];
  var niveis = [];
  FAIXAS.forEach(function(fx, i) {
    var v = props['n_pares_' + fx];
    var maximo = MAXIMO_PARES[mm][i];
    n[fx] = vazio(v) ? null : Number(v);
    niveis.push(n[fx] === null || !(n[fx] > 0) || n[fx] > maximo ? '❌' : (n[fx] < LIM.minPares * maximo ? '⚠️' : '✅'));
    partes.push(fx + ' ' + (n[fx] === null ? 'n/d' : n[fx]) + '/' + maximo +
                (n[fx] > 0 ? ' (' + (100 * n[fx] / maximo).toFixed(1) + '%)' : ''));
  });
  npares[mm] = n;
  anota(1, mm, pior(niveis), 'Mês ' + mm + ': n_pares / máximo possível: ' + partes.join(', '));
  return faltam.length === 0;
}

function tarefaEstrutura(mm) {
  return function(feito) {
    var img = ee.Image(COLECAO + '/Matriz_GFS_' + mm);
    ee.Dictionary({bandas: img.bandNames(), props: img.toDictionary()}).evaluate(function(r, erro) {
      protegido(1, mm, 'Mês ' + mm, function() {
        if (erro || !r) {
          anota(1, mm, '❌', 'Mês ' + mm + ': matriz ilegível (' + erro + ').');
        } else if (avaliarEstrutura(mm, r)) {
          agenda(tarefaEstatisticas(mm));
        } else {
          anota(2, mm, '❌', 'Mês ' + mm + ': estatísticas não calculadas (faltam bandas).');
        }
      }, feito);
    });
  };
}

// ------------------------------------------------------------
// 2 a 4. Cobertura, viés, fatores e detalhe espacial [V4 M04-01/M04-02/M04-04/M04-05]
// ------------------------------------------------------------
function tarefaEstatisticas(mm) {
  return function(feito) {
    var img = ee.Image(COLECAO + '/Matriz_GFS_' + mm);
    var derivadas = [];
    var indicadores = [];
    var colunas = [];
    var bandasPr = [];
    FAIXAS.forEach(function(fx) {
      ['Tmax', 'Tmin', 'RH'].forEach(function(v) {
        var nome = 'dif_' + v + '_' + fx;
        derivadas.push(img.select(v + '_m_gfs_' + fx).subtract(img.select(v + '_m_sicsb_' + fx)).rename(nome));
        colunas.push(nome);
      });
      ['pr', 'u2', 'Rs'].forEach(function(v) {
        var nome = 'fat_' + v + '_' + fx;
        var alvo = img.select(v + '_m_sicsb_' + fx);
        var modelo = img.select(v + '_m_gfs_' + fx);
        // [V4 A-01] O fator que o motor V1.5 aplica nos dias GFS, antes do limite: chuva
        // (m_sicsb + 0,1)/(m_gfs + 0,1) com teto 5 (calib_chuva_gfs); vento e radiação
        // m_sicsb/max(m_gfs, 1e-3) limitado a [0,5; 2] (calib_limitada_gfs). Os indicadores contam os
        // pixels em que o limite atua (teto) e, na chuva, os de fator muito baixo (< 0,2).
        var fator = v === 'pr' ? alvo.add(0.1).divide(modelo.add(0.1)) : alvo.divide(modelo.max(1e-3));
        var teto = v === 'pr' ? 5 : 2;
        var piso = v === 'pr' ? 0.2 : 0.5;
        derivadas.push(fator.rename(nome));
        colunas.push(nome);
        indicadores.push(fator.gt(teto).rename('acima5_' + v + '_' + fx));
        indicadores.push(fator.lt(piso).rename('abaixo02_' + v + '_' + fx));
      });
      bandasPr.push('pr_m_gfs_' + fx, 'pr_m_sicsb_' + fx);
    });
    colunas = colunas.concat(NOMES_N);

    // Percentis exatos numa amostra da grade nativa (sem histograma: maxRaw > N_AMOSTRA)
    var amostra = ee.Image.cat(derivadas).addBands(img.select(NOMES_N)).sample({
      region: BRASIL, projection: ee.Projection(CRS, TRANSFORM), numPixels: N_AMOSTRA, seed: 42, geometries: false});
    var redutorPct = ee.Reducer.percentile({percentiles: [5, 50, 95], maxRaw: MAX_RAW});
    var percentis = {};
    colunas.forEach(function(c) {
      percentis[c] = amostra.reduceColumns({reducer: redutorPct, selectors: [c]});
    });

    var dados = {
      n_amostra: amostra.size(),
      percentis: ee.Dictionary(percentis),
      contagem: reduzir(img, ee.Reducer.count()),
      fracoes: reduzir(ee.Image.cat(indicadores), ee.Reducer.mean().unweighted()),
      n_min: reduzir(img.select(NOMES_N), ee.Reducer.min()),
      somas_pr: reduzir(img.select(bandasPr), ee.Reducer.sum().unweighted())
    };
    if (mm === '01' || mm === '07') {
      var grads = [];
      FAIXAS.forEach(function(fx) {
        grads.push(gradiente(img.select('Tmax_m_gfs_' + fx)).rename('g_gfs_' + fx));
        grads.push(gradiente(img.select('Tmax_m_sicsb_' + fx)).rename('g_br_' + fx));
      });
      dados.gradientes = reduzir(ee.Image.cat(grads), ee.Reducer.mean(), CAIXA_SERRA);
    }
    ee.Dictionary(dados).evaluate(function(r, erro) {
      protegido(3, mm, 'Mês ' + mm, function() {
        if (erro || !r) {
          anota(3, mm, '❌', 'Mês ' + mm + ': estatísticas não calculadas (' + erro + ').');
        } else {
          avaliarEstatisticas(mm, r);
        }
      }, feito);
    });
  };
}

function avaliarEstatisticas(mm, r) {
  var p = r.percentis || {};
  var q0 = function(c) { return p[c] || {}; };

  // 2. Cobertura: a mesma contagem de pixels nas 100 bandas (M03-08)
  var cont = r.contagem || {};
  var valores = ESPERADAS.map(function(b) { return vazio(cont[b]) ? 0 : cont[b]; });
  var minC = Math.min.apply(null, valores);
  var maxC = Math.max.apply(null, valores);
  if (minC === maxC && maxC > 0) {
    anota(2, mm, '✅', 'Mês ' + mm + ': ' + maxC + ' pixels em todas as 100 bandas.');
  } else {
    var menores = ESPERADAS.filter(function(b, i) { return valores[i] !== maxC; });
    anota(2, mm, '❌', 'Mês ' + mm + ': contagem de pixels difere entre as bandas (mín ' + minC + ', máx ' + maxC +
          '; ' + menores.length + ' bandas abaixo do máximo, por exemplo ' + menores.slice(0, 4).join(', ') + ').');
  }
  // 2. n por pixel: com a máscara diária constante, mediana = n_pares
  FAIXAS.forEach(function(fx) {
    var np = (npares[mm] || {})[fx];
    var mn = (r.n_min || {})['n_' + fx];
    var md = q0('n_' + fx).p50;
    var nivel = vazio(mn) || vazio(md) || !(np > 0) ? '❌' : (md === np && mn >= LIM.nMin * np ? '✅' : '⚠️');
    anota(2, mm, nivel, 'Mês ' + mm + ' ' + fx + ': n por pixel mínimo ' + f(mn, 0) + ', mediana ' + f(md, 0) +
          ' (n_pares ' + (vazio(np) ? 'n/d' : np) + ').');
  });

  // 3. Viés e fatores por faixa
  if (vazio(r.n_amostra) || r.n_amostra < 0.8 * N_AMOSTRA) {
    anota(3, mm, '⚠️', 'Mês ' + mm + ': amostra de ' + f(r.n_amostra, 0) + ' pixels (esperado ~' + N_AMOSTRA + ').');
  }
  FAIXAS.forEach(function(fx) {
    var niveis = [];
    var txt = [];
    ['Tmax', 'Tmin', 'RH'].forEach(function(v) {
      var q = q0('dif_' + v + '_' + fx);
      txt.push(v + ' ' + sinal(q.p50, 1) + ' [' + sinal(q.p5, 1) + '; ' + sinal(q.p95, 1) + ']');
      if (v === 'RH') {
        niveis.push(fora(q.p50, [-LIM.viesRH, LIM.viesRH]) ? '⚠️' : '✅');
      } else {
        niveis.push(fora(q.p50, [-LIM.viesT, LIM.viesT]) ? '❌' : '✅');
        niveis.push(fora(q.p5, [-LIM.caudaT, LIM.caudaT]) || fora(q.p95, [-LIM.caudaT, LIM.caudaT]) ? '⚠️' : '✅');
      }
    });
    ['pr', 'u2', 'Rs'].forEach(function(v) {
      var q = q0('fat_' + v + '_' + fx);
      var a5 = (r.fracoes || {})['acima5_' + v + '_' + fx];
      var b02 = (r.fracoes || {})['abaixo02_' + v + '_' + fx];
      var limite = v === 'pr' ? LIM.fracPr : LIM.fracU2Rs;
      txt.push('fator ' + v + ' ' + f(q.p50, 2) + ' (' + pct(a5) + '; ' + pct(b02) + ')');
      niveis.push(fora(q.p50, LIM.fatorMed) ? '⚠️' : '✅');
      niveis.push(fora(a5, [0, limite]) || fora(b02, [0, limite]) ? '⚠️' : '✅');
    });
    var somaGfs = (r.somas_pr || {})['pr_m_gfs_' + fx];
    var somaBr = (r.somas_pr || {})['pr_m_sicsb_' + fx];
    var razao = somaBr > 0 ? somaGfs / somaBr : null;
    txt.push('Σchuva ' + f(razao, 2));
    niveis.push(fora(razao, LIM.razaoPr) ? '❌' : '✅');
    anota(3, mm, pior(niveis), 'Mês ' + mm + ' ' + fx + ': ' + txt.join(' | '));
  });

  // 4. Detalhe espacial (meses 01 e 07) [V4 M04-02]
  if (r.gradientes) {
    FAIXAS.forEach(function(fx) {
      var gGfs = r.gradientes['g_gfs_' + fx];
      var gBr = r.gradientes['g_br_' + fx];
      var razao = gBr > 0 ? gGfs / gBr : null;
      var nivel = vazio(razao) ? '❌' : (razao >= LIM.gradMin ? '✅' : (razao > LIM.gradV1 ? '⚠️' : '❌'));
      anota(4, mm, nivel, 'Mês ' + mm + ' ' + fx + ': ' + f(razao, 3) + ' (critério ≥ ' + LIM.gradMin.toFixed(2) +
            ' e acima de ' + LIM.gradV1.toFixed(3) + ', valor da V1)');
    });
  }
}

// ------------------------------------------------------------
// 5. Radiação: V2.1 L1 contra a V1 [V4 M04-03]
// ------------------------------------------------------------
function tarefaRsV1(presentes) {
  return function(feito) {
    ee.Image(MATRIZ_V1 + '/Matriz_GFS_01').bandNames().evaluate(function(bandas, erro) {
      protegido(5, '00', 'Bandas da V1', function() {
        if (erro || !bandas) {
          anota(5, '00', '⚠️', 'Matriz V1 (' + MATRIZ_V1 + ') ilegível; comparação não feita (' + erro + ').');
          return;
        }
        var gfs = bandas.indexOf('Rs_m_gfs') >= 0 ? 'Rs_m_gfs' : null;
        var alvo = null;
        ['Rs_m_sicsb', 'Rs_m_sab', 'Rs_m_br'].forEach(function(b) { if (!alvo && bandas.indexOf(b) >= 0) alvo = b; });
        bandas.forEach(function(b) { if (!alvo && b.indexOf('Rs_m_') === 0 && b.indexOf('gfs') < 0) alvo = b; });
        if (!gfs || !alvo) {
          anota(5, '00', '⚠️', 'Matriz V1 sem bandas de radiação reconhecidas (' + bandas.join(', ') + '); comparação não feita.');
          return;
        }
        anota(5, '00', null, 'Bandas da V1 usadas: ' + gfs + ' e ' + alvo + ' (somas nos pixels comuns às duas matrizes).');
        presentes.forEach(function(mm) { agenda(tarefaRsMes(mm, gfs, alvo)); });
      }, feito);
    });
  };
}

function tarefaRsMes(mm, gfs, alvo) {
  return function(feito) {
    var v2 = ee.Image(COLECAO + '/Matriz_GFS_' + mm);
    var v1 = ee.Image(MATRIZ_V1 + '/Matriz_GFS_' + mm);
    var img = ee.Image.cat([v2.select('Rs_m_gfs_L1').rename('g2'), v2.select('Rs_m_sicsb_L1').rename('b2'),
                            v1.select(gfs).rename('g1'), v1.select(alvo).rename('b1')]);
    var comum = img.mask().reduce(ee.Reducer.min());
    reduzir(img.updateMask(comum), ee.Reducer.sum().unweighted()).evaluate(function(s, erro) {
      protegido(5, mm, 'Mês ' + mm, function() {
        if (erro || !s) {
          anota(5, mm, '⚠️', 'Mês ' + mm + ': comparação com a V1 não calculada (' + erro + ').');
          return;
        }
        var r2 = s.b2 > 0 ? s.g2 / s.b2 : null;
        var r1 = s.b1 > 0 ? s.g1 / s.b1 : null;
        var rr = !vazio(r2) && r1 > 0 ? r2 / r1 : null;
        anota(5, mm, fora(rr, LIM.rsV1) ? '⚠️' : '✅', 'Mês ' + mm + ': GFS/BR-DWGD V2.1 L1 ' + f(r2, 3) +
              ', V1 ' + f(r1, 3) + ', razão ' + f(rr, 3));
      }, feito);
    });
  };
}

// ------------------------------------------------------------
// Relatório final e resumo
// ------------------------------------------------------------
function imprimeRelatorio() {
  print('==================== CONFERÊNCIA DA MATRIZ GFS V2.1 ====================');
  TITULOS.forEach(function(titulo, i) {
    var linhas = [];
    Object.keys(saida[i]).sort().forEach(function(k) {
      saida[i][k].forEach(function(l) { linhas.push('   ' + l); });
    });
    print(titulo + '\n' + (linhas.length ? linhas.join('\n') : '   (nada calculado)'));
  });
  var resumo = 'RESUMO: ' + totais['✅'] + ' ✅ | ' + totais['⚠️'] + ' ⚠️ | ' + totais['❌'] + ' ❌\n';
  if (totais['❌'] > 0) {
    resumo += '❌ Há itens reprovados: pare e me envie a saída inteira do Console.';
  } else if (totais['⚠️'] > 0) {
    resumo += '⚠️ Sem reprovações, mas há avisos (limiares heurísticos): me envie a saída antes de rodar o motor.';
  } else {
    resumo += '✅ Matriz GFS V2.1 conferida: pode seguir para o motor.';
  }
  if (alertas.length) resumo += '\nItens com ⚠️ ou ❌:\n   ' + alertas.join('\n   ');
  print(resumo);
}

// ------------------------------------------------------------
// Disparo [V4]
// ------------------------------------------------------------
print('⏳ Conferindo as 12 matrizes da ' + COLECAO + ' (1 a 3 min). O relatório sai de uma vez no fim.');
var col = ee.ImageCollection(COLECAO);
agenda(function(feito) {
  col.aggregate_array('system:index').evaluate(function(ids, erro) {
    protegido(1, '00', 'Lista de matrizes', function() {
      if (erro || !ids) {
        anota(1, '00', '❌', 'Coleção ' + COLECAO + ' ilegível (' + erro + ').');
        return;
      }
      anota(1, '00', ids.length === 12 ? '✅' : '❌', 'Número de matrizes (esperado 12): ' + ids.length);
      var presentes = MESES.filter(function(mm) { return ids.indexOf('Matriz_GFS_' + mm) >= 0; });
      MESES.forEach(function(mm) {
        if (presentes.indexOf(mm) < 0) anota(1, mm, '❌', 'Mês ' + mm + ': Matriz_GFS_' + mm + ' não existe.');
      });
      presentes.forEach(function(mm) { agenda(tarefaEstrutura(mm)); });
      agenda(tarefaRsV1(presentes));
    }, feito);
  });
});

// 6. Inspeção visual da resolução: Serra do Mar e Mantiqueira. [V4: era o bloco 3; a medida
//    numérica do mesmo efeito está no bloco 4 do relatório]
//    Esperado: a camada GFS mostra o relevo em escala de dezenas de km (grade do GFS de 0,25°
//    suavizada). Manchas lisas de ~100 km indicariam que a reamostragem não funcionou.
var m = ee.Image(COLECAO + '/Matriz_GFS_01');   // [V4] mesma matriz de janeiro de antes (só mudou de lugar)
var vis = {min: 20, max: 34, palette: ['#2c7bb6', '#abd9e9', '#ffffbf', '#fdae61', '#d7191c']};
Map.setCenter(-46.5, -23, 7);
Map.addLayer(m.select('Tmax_m_sicsb_L1'), vis, 'Tmax BR-DWGD (pares da faixa L1)');
Map.addLayer(m.select('Tmax_m_gfs_L1'), vis, 'Tmax GFS faixa L1');
Map.addLayer(m.select('Tmax_m_gfs_L11a15'), vis, 'Tmax GFS faixa L11a15', false);
