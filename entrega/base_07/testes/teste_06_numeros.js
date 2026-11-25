// Testes offline (Node) do painel (22/10/2026, 18h30): números com ponto, 1 arquivo por ano e linha do CSV mais leve.
// Rodar: node testes/teste_06_numeros.js  (a partir da pasta do pacote)
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var src = fs.readFileSync(path.join(__dirname, '..', '06_painel_sab_2026_11_5.js'), 'utf8');
var falhas = 0;

function confere(cond, msg) {
  console.log((cond ? '  ok   ' : '  FALHA ') + msg);
  if (!cond) { falhas++; }
}

function pegarFuncao(nome) {
  var i = src.indexOf('function ' + nome + '(');
  var j = src.indexOf('\n}\n', i);
  if (i < 0) throw new Error('função não encontrada: ' + nome);
  return src.slice(i, j + 2);
}

console.log('\n[código]');
var fmt = pegarFuncao('formatarExportacaoClima');
confere(fmt.indexOf(".replace('\\\\.', ',')") === -1 && fmt.indexOf('val.format(formatoCadeia)') > 0 &&
        fmt.indexOf('.round()') === -1, 'CSV de clima: ponto decimal com format (1 operação por valor), sem vírgula nem arredondamento numérico');
confere(fmt.indexOf('propertyNames') === -1 && fmt.indexOf("fDict.get(col, '')") > 0 && fmt.indexOf("fDict.get('Tipo_Dado', 'Agregado')") > 0,
        'linha do CSV sem listar as propriedades (mais leve que a 2026.10.2)');
confere(/'RONI_Trimestre_C': ee\.Algorithms\.If\(tem, roni\.format\('%\.1f'\), '-'\)/.test(src),
        'RONI_Trimestre_C com ponto decimal');
confere(src.indexOf(".replace('\\\\.', ',')") === -1, 'nenhuma troca de ponto por vírgula sobrou no servidor');
confere(src.indexOf("'Variavel': '(formato dos numeros)'") > 0, 'dicionário explica o ponto decimal');
var d = pegarFuncao('exportarSerieDiaria'), m = pegarFuncao('exportarSerieMensal');
confere(d.indexOf('anosComDados.forEach(function(anoAtual)') > 0 && d.indexOf("'Diaria_' + nomeSeguro + '_' + anoAtual + sufixoArquivoEnso(cenarioEnso)") > 0 &&
        d.indexOf('planejarPeriodos') === -1, 'diário: 1 arquivo por ano, como antes (sem divisão em partes)');
confere(m.indexOf("'Mensal_' + nomeSeguro + '_' + anoAtual + sufixoArquivoEnso(cenarioEnso)") > 0 && m.indexOf('planejarMeses') === -1,
        'mensal: 1 arquivo por ano, como antes');

// ---------------------------------------------------------------- formatação numérica com ee falso
console.log('\n[formatarExportacaoClima com ee falso]');
function Num(v) { this.v = v; }
function Bool(b) { this.b = b; }
Bool.prototype.or = function(o) { return new Bool(this.b || o.b); };
Num.prototype.eq = function(o) { return new Bool(this.v === o); };
Num.prototype.multiply = function(k) { return new Num(this.v * k); };
Num.prototype.round = function() { return new Num(Math.round(this.v)); };
Num.prototype.divide = function(k) { return new Num(this.v / k); };
Num.prototype.format = function(f) { return this.v.toFixed(parseInt(f.replace(/[^0-9]/g, ''), 10)); };
Num.prototype.subtract = function(o) { return new Num(this.v - (o instanceof Num ? o.v : o)); };
Num.prototype.max = function(o) { return new Num(Math.max(this.v, o)); };
var eeFalso = {
  Number: function(v) { return v instanceof Num ? v : new Num(v); },
  String: function(s) { return { split: function() { return { cat: function() { return { get: function(i) { return s.split('-')[i]; } }; } }; } }; },
  List: function(l) { return l; },
  Algorithms: { If: function(c, a, b) { return (c instanceof Bool ? c.b : c) ? a : b; } },
  Feature: function(g, p) { return p; }
};
var props = { Data: '2025-01-01', tmax_C: 18.4049, tmin_C: -9999, Latitude: -25.949521, pr_mm: 0.125, ID_Ponto: 'Ponto_00001' };
var featFalsa = {
  get: function(k) { return props[k]; },
  toDictionary: function() { return { get: function(k, padrao) { return k in props ? props[k] : padrao; }, contains: function(k) { return k in props; } }; },
  propertyNames: function() { return { contains: function(k) { return k in props; } }; }
};
var ctx2 = { ee: eeFalso };
vm.createContext(ctx2);
vm.runInContext(pegarFuncao('formatarExportacaoClima') + '\nthis.f = formatarExportacaoClima;', ctx2);
var linha = null;
ctx2.f({ map: function(fn) { linha = fn(featFalsa); return null; } }, []);
confere(linha.Temperatura_Maxima_C === '18.40', 'Tmax 18,4049 -> 18.40 (2 casas, ponto)');
confere(linha.Latitude === '-25.94952', 'Latitude com 5 casas, como antes');
confere(linha.Temperatura_Minima_C === null, 'sem dado (-9999) continua vazio');
confere(linha.Tipo_Dado === 'Agregado' && linha.Versao_Algoritmo === '', 'sem Tipo_Dado/Versao_Algoritmo na feição: os mesmos valores padrão de antes');

console.log('\n' + (falhas ? falhas + ' FALHA(S)' : 'TODOS OS TESTES PASSARAM'));
process.exit(falhas ? 1 : 0);
