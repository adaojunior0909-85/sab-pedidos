// Testes offline (Node) da ordem das colunas dos CSVs do painel 2026.10.4 (revisão B-05) e de trechos das
// revisões B-08 a B-10. Rodar: node testes/teste_06_colunas.js  (a partir da pasta do pacote)
var fs = require('fs');
var path = require('path');
var src = fs.readFileSync(path.join(__dirname, '..', '06_painel_sab_2026_11_5.js'), 'utf8');
var falhas = 0;

function confere(cond, msg) {
  console.log((cond ? '  ok   ' : '  FALHA ') + msg);
  if (!cond) { falhas++; }
}

function pegarFuncao(nome) {
  var i = src.indexOf('function ' + nome + '(');
  var j = src.indexOf('\n}\n', i);
  return src.slice(i, j + 2);
}

function pegarVar(nome) {
  var i = src.indexOf('var ' + nome + ' =');
  var j = src.indexOf(';', i);
  return src.slice(i, j + 1);
}

/* eslint-disable no-eval */
eval(pegarVar('COLUNAS_NOVAS_DIARIA'));
eval(pegarVar('COLUNAS_NOVAS_MENSAL'));
eval(pegarFuncao('getColunasClimaBase'));
eval(pegarFuncao('getColunasClimaDiaria'));
eval(pegarFuncao('getColunasClimaMensal'));

var b = getColunasClimaBase();
var d = getColunasClimaDiaria();
var m = getColunasClimaMensal();

console.log('\n[B-05] colunas novas no fim; antigas nas mesmas posições');
confere(b.length === 30, 'base com as 30 colunas da 2026.10.3a (' + b.length + ')');
confere(JSON.stringify(d.slice(0, 30)) === JSON.stringify(b), 'diário: 30 primeiras = base, mesma ordem');
confere(JSON.stringify(d.slice(30)) === JSON.stringify(['Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo']),
        'diário: Qualidade_Pixel, Janela_Chuva_UTC e Confianca_Prazo no fim');
confere(JSON.stringify(m.slice(0, 30)) === JSON.stringify(b), 'mensal: 30 primeiras = base, mesma ordem');
confere(JSON.stringify(m.slice(30)) === JSON.stringify(['N_Dias', 'Dias_no_Mes', 'Mes_Completo']),
        'mensal: N_Dias, Dias_no_Mes e Mes_Completo no fim');
confere(m.indexOf('Qualidade_Pixel') === -1, 'Qualidade_Pixel só no diário (contrato do SPEC)');
var chamadas = getColunasClimaBase();
chamadas.push('x');
confere(getColunasClimaBase().length === 30, 'getColunasClimaBase devolve lista nova a cada chamada');

console.log('\n[B-08 a B-10] trechos');
confere(src.indexOf("V1.5: so rodadas GFS 00Z completas") > 0, 'B-08: dicionário descreve a V1.5');
confere(src.indexOf('var imgCobertura = ee.Image.pixelLonLat();') > 0 &&
        src.indexOf('imgCobertura.sample({') > 0, 'B-09: camada de cobertura amostra a grade com a máscara');
confere((src.match(/compartilhe SAB_MASCARA_QUALIDADE \(Anyone can read\)/g) || []).length === 2,
        'B-10: alerta e Console citam o compartilhamento');

console.log('\n' + (falhas ? falhas + ' FALHA(S)' : 'TODOS OS TESTES PASSARAM'));
process.exit(falhas ? 1 : 0);
