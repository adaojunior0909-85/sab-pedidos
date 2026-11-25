// SAB: teste dos limites de pedidos do Codigo.gs (por e-mail e teto geral). Roda fora do Google, com uma planilha falsa.
// Uso (na pasta 05_Apps_Script):  node testes/teste_limite.js
const fs = require('fs'), path = require('path'), vm = require('vm');
const props = {};
let avisos = 0;
const ctx = {console, Date,
  PropertiesService: {getScriptProperties: () => ({getProperty: k => props[k] ?? null, setProperty: (k, v) => { props[k] = v; }})},
  Utilities: {formatDate: d => d.toISOString().slice(0, 10)}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'Codigo.gs'), 'utf8'), ctx);
ctx.avisarResponsavel_ = () => { avisos++; };

const col = {email: 1, Recebido_em: 2, Status: 3, ID_Pedido: 4};
const agora = new Date(), velho = new Date(Date.now() - 2 * 864e5);
const planilha = linhas => ({getLastRow: () => linhas.length + 1, getLastColumn: () => 4,
                             getRange: () => ({getValues: () => linhas})});
let falhas = 0;
const confere = (ok, msg) => { console.log((ok ? 'ok    ' : 'FALHOU ') + msg); if (!ok) falhas++; };
const f = ctx.pedidosRecentes_;

const aba = planilha([['a@x.com', agora, 'na_fila', 'SAB-0001'], ['a@x.com', agora, 'recusado', 'SAB-0002'],
  ['b@x.com', agora, 'entregue', 'SAB-0003'], ['c@x.com', velho, 'entregue', 'SAB-0004'],
  ['d@x.com', '', 'na_fila', 'SAB-0005'], ['e@x.com', agora, '', '']]);
confere(f(aba, col, 'a@x.com', 99) === 1, 'por e-mail: não conta recusado');
confere(f(aba, col, null, 99) === 3, 'geral: conta registrados das últimas 24 h, recusados inclusive');
confere(f(aba, col, null, 2) === 2, 'geral: não conta a própria linha');

// 25 registrados + 6 que chegaram com o sistema ocupado (sem ID): com teto 30, só o 6º pode ser barrado
const leva = Array.from({length: 25}, (_, i) => ['u' + i + '@x.com', agora, 'na_fila', 'SAB-' + i])
  .concat(Array.from({length: 6}, (_, i) => ['p' + i + '@x.com', agora, '', '']));
const teto = vm.runInContext('CONFIG.MAX_PEDIDOS_DIA', ctx);
let aceitos = 0;
for (let i = 25; i < 31; i++) {
  if (f(planilha(leva), col, null, i + 2) < teto) { leva[i][3] = 'SAB-P' + i; aceitos++; }
}
confere(teto === 30 && aceitos === 5, 'leva sem ID: aceita 5 até o teto de 30 (antes recusava os 6)');

ctx.avisarLimiteGeral_();
ctx.avisarLimiteGeral_();
confere(avisos === 1, 'aviso ao responsável só uma vez por dia');
process.exitCode = falhas ? 1 : 0;
