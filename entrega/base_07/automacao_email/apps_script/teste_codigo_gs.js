// Simulação do Apps Script (Codigo.gs) com planilha, Drive, Gmail e GitHub falsos. Rodar: node teste_codigo_gs.js
// Não faz parte do que vai para o Apps Script; serve só para conferir a lógica antes de colar.
const fs = require('fs');
const crypto = require('crypto');
const vm = require('vm');
const path = require('path');

let AGORA = new Date('2026-11-03T14:00:00-03:00').getTime();
const RealDate = Date;
class FakeDate extends RealDate {
  constructor(...a) { if (a.length === 0) super(AGORA); else super(...a); }
  static now() { return AGORA; }
}

// ---------------- planilha
// títulos com espaço no fim e acento decomposto (NFD), como o Forms às vezes grava
const CAB = ['Carimbo de data/hora', 'Código do pedido '.normalize('NFD'), 'Resumo do pedido', 'Nome completo  ', 'E-mail para receber o link',
             'Instituição', 'Finalidade do uso dos dados'];
let grade = [CAB.slice()];      // aba de respostas do Forms
// [2026.11.04] planilha com várias abas: a do Forms (grade) e as de registro criadas pelo script (Pedidos, Pedidos_Teste)
function fakeAba(nome, g) {
  const cel = (l, c) => (g[l - 1] || [])[c - 1];
  const a = {
    _g: g, congeladas: 0,
    getName: () => nome,
    getLastRow: () => g.length,
    getMaxRows: () => g.length + 50,
    getLastColumn: () => Math.max(1, ...g.map((r) => r.length)),
    appendRow: (l) => { g.push(l.slice()); },
    insertRowsAfter: () => {},
    deleteRows: (l, n) => { if (l + n - 1 >= a.getMaxRows()) throw new Error('não pode apagar todas as linhas'); g.splice(l - 1, n); },
    deleteColumn: (c) => { g.forEach((r) => r.splice(c - 1, 1)); },
    setFrozenRows: (n) => { a.congeladas = n; },
    getRange: (l, c, nl, nc) => {
      const rg = {
        getValues: () => {
          const out = [];
          for (let i = 0; i < (nl || 1); i++) {
            const r = [];
            for (let j = 0; j < (nc || 1); j++) { const v = cel(l + i, c + j); r.push(v === undefined ? '' : v); }
            out.push(r);
          }
          return out;
        },
        setValue: (v) => { while (g.length < l) g.push([]); g[l - 1][c - 1] = v; return rg; },
        setValues: (vs) => { vs.forEach((r, i) => r.forEach((v, j) => { while (g.length < l + i) g.push([]); g[l + i - 1][c + j - 1] = v; })); return rg; },
        setFontWeight: () => rg, setNumberFormat: () => rg
      };
      return rg;
    }
  };
  return a;
}
const aba = fakeAba('Respostas ao formulário 1', grade);
const abasReg = {};
let respostasForms = 0, formApagado = 0;
const planilha = () => ({
  getSheets: () => [aba].concat(Object.values(abasReg)),
  getSheetByName: (n) => abasReg[n] || (n === aba.getName() ? aba : null),
  insertSheet: (n) => { abasReg[n] = fakeAba(n, []); return abasReg[n]; },
  getFormUrl: () => 'https://docs.google.com/forms/d/x/edit'
});
function responder(codigo, email, nome) {
  AGORA += 1000;            // respostas do Forms têm carimbo com segundos
  respostasForms++;
  grade.push([new FakeDate(), codigo, 'Pato Branco, diário, 2025, todas as variáveis', nome || 'Fulana', email,
              'UTFPR', 'Pesquisa acadêmica']);
  return {range: {getSheet: () => aba, getRow: () => grade.length}};
}
const R = () => abasReg.Pedidos._g, RT = () => abasReg.Pedidos_Teste._g;
const obj = (g, l) => { const o = {}; g[0].forEach((h, i) => { o[h] = (g[l - 1] || [])[i]; }); return o; };
const P = (l) => obj(R(), l), PT = (l) => obj(RT(), l);
const ultimo = () => P(R().length);
const comEmail = (e) => R().slice(1).map((r, i) => P(i + 2)).filter((o) => o['E-mail'] === e);

// ---------------- Drive
let pastas = [];           // lista: o Earth Engine pode criar duas pastas com o mesmo nome
let usoDrive = 0.1, bloquearLink = false;
function novaPasta(nome) {
  const criada = AGORA;
  const p = {id: 'ID_' + nome + '_' + pastas.length, nome, arquivos: {}, compart: null, leitores: [], apagada: false,
    getName: () => nome, getDateCreated: () => new RealDate(criada),
    getId: () => p.id, getUrl: () => 'https://drive.google.com/drive/folders/' + p.id, isTrashed: () => p.apagada,
    setSharing: (a, b) => { if (bloquearLink) throw new Error('Acesso negado pela política do domínio'); p.compart = [a, b]; },
    addViewer: (e) => { p.leitores.push(e); },
    setTrashed: () => { p.apagada = true; },
    getFilesByName: (n) => { let ok = !!p.arquivos[n]; return {hasNext: () => ok, next: () => { ok = false; return p.arquivos[n]; }}; },
    getFiles: () => { const l = Object.values(p.arquivos); let i = 0; return {hasNext: () => i < l.length, next: () => l[i++]}; }};
  pastas.push(p);
  return p;
}
function arquivo(pasta, nome, conteudo, mb) {
  const f = {getName: () => nome, getSize: () => (mb || 1) * 1e6, setSharing: () => {},
             getBlob: () => ({getDataAsString: () => conteudo, tamanho: (mb || 1) * 1e6}),
             moveTo: (destino) => { delete pasta.arquivos[nome]; destino.arquivos[nome] = f; pasta = destino; }};
  pasta.arquivos[nome] = f;
}
function manifesto(id, status, motivo, arquivos) {
  const cols = 'Pedido,Status,Motivo,Arquivo,Linhas_Esperadas';
  const linhas = [cols, [id, status, motivo, '', ''].join(',')].concat(arquivos.map((a) => [id, status, '', a, '10'].join(',')));
  return linhas.join('\n') + '\n';
}

// ---------------- e-mail, GitHub, propriedades
// GitHub App: par de chaves RSA no formato que o GitHub entrega (PKCS#1, "BEGIN RSA PRIVATE KEY")
const PAR = crypto.generateKeyPairSync('rsa', {modulusLength: 2048, publicKeyEncoding: {type: 'spki', format: 'pem'},
  privateKeyEncoding: {type: 'pkcs1', format: 'pem'}});
let jwts = [], tokensGerados = 0, cache = {}, appInstalado = true;
const assinados = (buf) => Array.from(buf).map((b) => (b > 127 ? b - 256 : b));
const paraBuffer = (x) => (typeof x === 'string' ? Buffer.from(x, 'utf8') : Buffer.from(x.map((b) => b & 255)));
let emails = [], acion = [], respostaGitHub = 204, motorRodando = 0, consultas = [], props = {GITHUB_TOKEN: 'tok', GITHUB_REPO: 'u/sab-pedidos',
  EMAIL_RESPONSAVEL: 'dono@gmail.com'}, gatilhos = [], rapidos = [];
const rapidoAtivo = () => rapidos.filter((t) => !t.apagado);   // [2026.11.08a] acionadores verificarRapido vivos

function parseCsv(txt) {
  return txt.trim().split('\n').map((l) => {
    const out = []; let cur = '', q = false;
    for (const ch of l) { if (ch === '"') q = !q; else if (ch === ',' && !q) { out.push(cur); cur = ''; } else cur += ch; }
    out.push(cur); return out;
  });
}
function formatDate(d, tz, fmt) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', {timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false}).formatToParts(new RealDate(d.getTime())).map((x) => [x.type, x.value]));
  if (fmt === 'H') return String(Number(p.hour));
  if (fmt === 'HH:mm') return p.hour + ':' + p.minute;
  if (fmt === 'yyyy') return p.year;
  if (fmt === 'dd/MM/yyyy') return p.day + '/' + p.month + '/' + p.year;
  if (fmt === 'yyyy-MM-dd') return p.year + '-' + p.month + '-' + p.day;
  return p.year + p.month + p.day + p.hour + p.minute + p.second;
}

let travaLivre = true;   // [2026.11.03] false = outra rotina está com a trava do script
const ctx = {
  Date: FakeDate, Math, JSON, Number, String, Object, Array, Error, console,
  Logger: {log: (m) => { ctx._log.push(String(m)); }}, _log: [],
  Session: {getEffectiveUser: () => ({getEmail: () => 'dono@gmail.com'})},
  SpreadsheetApp: {getActive: planilha},
  FormApp: {openByUrl: () => ({getResponses: () => new Array(respostasForms), deleteAllResponses: () => { formApagado++; respostasForms = 0; }})},
  DriveApp: {searchFolders: () => { const l = pastas.filter((p) => !p.apagada); let i = 0;
               return {hasNext: () => i < l.length, next: () => l[i++]}; },
             getFoldersByName: (n) => { const l = pastas.filter((p) => p.nome === n); let i = 0;
                                        return {hasNext: () => i < l.length, next: () => l[i++]}; },
             getStorageUsed: () => usoDrive * 15e9, getStorageLimit: () => 15e9,
             Access: {ANYONE_WITH_LINK: 'ANYONE_WITH_LINK'}, Permission: {VIEW: 'VIEW'}},
  Drive: {Files: {remove: (id) => { pastas.forEach((p) => { if (p.id === id) p.apagada = true; }); }}},
  MailApp: {getRemainingDailyQuota: () => 100, sendEmail: (o) => emails.push(o)},
  UrlFetchApp: {fetch: (url, o) => {
    if (/\/installation$/.test(url)) {
      jwts.push(o.headers.Authorization.replace('Bearer ', ''));
      return {getResponseCode: () => (appInstalado ? 200 : 404), getContentText: () => JSON.stringify({id: 777})};
    }
    if (/\/app\/installations\/777\/access_tokens$/.test(url)) {
      jwts.push(o.headers.Authorization.replace('Bearer ', ''));
      tokensGerados++;
      return {getResponseCode: () => 201, getContentText: () => JSON.stringify({token: 'ghs_teste' + tokensGerados,
        expires_at: '2026-11-03T15:00:00Z', permissions: {contents: 'write', actions: 'read', metadata: 'read'}})};
    }
    if (/\/repos\/[^/]+\/[^/]+$/.test(url)) {
      consultas.push(url + ' ' + (o.headers.Authorization || ''));
      return {getResponseCode: () => 200, getContentText: () => '{}'};
    }
    if (o.method !== 'post') {                 // consulta das execuções do motor (API do GitHub)
      consultas.push(url + ' ' + ((o.headers || {}).Authorization || ''));
      const n = /in_progress/.test(url) ? motorRodando : 0;
      return {getResponseCode: () => 200, getContentText: () => JSON.stringify({total_count: n})};
    }
    acion.push({url, corpo: JSON.parse(o.payload), aut: o.headers.Authorization});
    return {getResponseCode: () => respostaGitHub, getContentText: () => 'msg'}; }},
  LockService: {getScriptLock: () => ({waitLock: () => { if (!travaLivre) throw new Error('Tempo limite do bloqueio'); },
                                       tryLock: () => travaLivre, releaseLock: () => {}})},
  PropertiesService: {getScriptProperties: () => ({getProperty: (k) => props[k] || null, setProperty: (k, v) => { props[k] = v; },
                                                   deleteProperty: (k) => { delete props[k]; },
                                                   getProperties: () => props})},
  CacheService: {getScriptCache: () => ({get: (k) => cache[k] || null, put: (k, v) => { cache[k] = v; },
                                         remove: (k) => { delete cache[k]; }})},
  Utilities: {formatDate, parseCsv,
              base64Decode: (t) => assinados(Buffer.from(t, 'base64')),
              base64Encode: (x) => paraBuffer(x).toString('base64'),
              base64EncodeWebSafe: (x) => paraBuffer(x).toString('base64').replace(/\+/g, '-').replace(/\//g, '_'),
              computeRsaSha256Signature: (txt, chave) => {
                if (!/^-----BEGIN PRIVATE KEY-----\n/.test(chave)) throw new Error('Invalid argument: key (só PKCS#8)');
                return assinados(crypto.sign('sha256', Buffer.from(txt, 'utf8'), crypto.createPrivateKey(chave)));
              },
              zip: (blobs, nome) => { const b = blobs.reduce((s, x) => s + x.tamanho, 0) * 0.15;
                                      return {getName: () => nome, getBytes: () => ({length: b})}; }},
  HtmlService: {createHtmlOutput: (h) => ({html: h, setTitle: function () { return this; }})},
  ScriptApp: {getProjectTriggers: () => gatilhos.concat(rapidos).filter((t) => !t.apagado).map((t) => ({getHandlerFunction: () => t.f, _t: t})),
              deleteTrigger: (x) => { x._t.apagado = true; },
              newTrigger: (f) => { const t = {f}; const enc = {forSpreadsheet: () => enc, onFormSubmit: () => enc, timeBased: () => enc,
                                    everyMinutes: (m) => { t.min = m; return enc; }, after: (ms) => { t.after = ms; return enc; },
                                    create: () => (f === 'verificarRapido' ? rapidos : gatilhos).push(t)}; return enc; }}
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, 'Codigo.gs'), 'utf8'), ctx);

let falhas = 0;
function confere(c, m) { console.log((c ? '  ok   ' : '  FALHA ') + m); if (!c) falhas++; }
const COD = 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=todas';
const horas = (h) => { AGORA += h * 3.6e6; };

console.log('[aba errada]');
const abaVazia = {getName: () => 'Página1', getLastRow: () => 1, getLastColumn: () => 2,
  getRange: () => ({getValues: () => [['Coluna A', 'Coluna B']]})};
ctx.SpreadsheetApp.getActive = () => ({getSheets: () => [abaVazia], getSheetByName: () => null, insertSheet: planilha().insertSheet});
try { ctx.configurar(); confere(false, 'deveria acusar a aba sem o formulário'); }
catch (e) { confere(/Página1/.test(e.message) && /Extensões/.test(e.message), 'erro mostra as abas e onde abrir o script'); }
ctx.SpreadsheetApp.getActive = () => Object.assign(planilha(), {getSheets: () => [abaVazia, aba].concat(Object.values(abasReg))});
console.log('[configurar]');
ctx.configurar();
confere(gatilhos.length === 2 && gatilhos[1].min === 10, 'acionadores: resposta do formulário e a cada 10 min');
confere(R()[0].join() === vm.runInContext('CONFIG', ctx).CABECALHO.join() && RT()[0].join() === vm.runInContext('CONFIG', ctx).CABECALHO.join() &&
        R()[0][0] === 'ID_Pedido' && abasReg.Pedidos.congeladas === 1, 'abas Pedidos e Pedidos_Teste criadas, ID na 1ª coluna');
confere(grade[0].indexOf('ID_Pedido') === -1 && grade[0].length === CAB.length, 'a aba do Forms não ganha colunas de controle');

console.log('[pedido normal, do formulário à entrega]');
ctx.aoEnviarFormulario(responder(COD, 'Fulana@UTFPR.edu.br'));
let L = P(2);
confere(L.ID_Pedido === 'SAB-0001' && R().length === 2, 'ID sequencial na aba Pedidos: ' + L.ID_Pedido);
confere(L.Origem === 'Formulário' && L['E-mail'] === 'fulana@utfpr.edu.br' && L['Resposta_formulario'] &&
        grade[1].length === CAB.length, 'registro com a origem; a resposta do Forms fica intacta');
confere(L.Status === 'enviado' && acion.length === 1, 'acionou o GitHub na hora (fila vazia)');
confere(rapidoAtivo().length === 1 && rapidoAtivo()[0].after === 60000, '[2026.11.08a] pedido acionado: próxima volta em 1 min');
confere(acion[0].corpo.event_type === 'pedido_sab' && acion[0].corpo.client_payload.codigo === COD &&
        !('simular' in acion[0].corpo.client_payload) && acion[0].aut === 'Bearer tok', 'GitHub recebe só ID e código');
confere(JSON.stringify(acion[0].corpo).indexOf('Fulana') === -1 && JSON.stringify(acion[0].corpo).indexOf('utfpr') === -1,
        'nome e e-mail NÃO vão para o GitHub');
confere(emails.length === 1 && emails[0].to === 'fulana@utfpr.edu.br' && /Recebemos/.test(emails[0].subject),
        'e-mail de confirmação');
confere(/SPAM/.test(emails[0].body) && /Lixo eletrônico/.test(emails[0].body), 'confirmação avisa para olhar o spam');
const ID = L.ID_Pedido;
horas(0.2); ctx.verificarRapido();
confere(P(2).Status === 'enviado', 'sem pasta ainda: continua enviado');
confere(rapidoAtivo().length === 1 && rapidoAtivo()[0].after === 60000 && rapidos.length === 2,
        '[2026.11.08a] continua ativo: um acionador só (o anterior foi apagado), de novo em 1 min');
confere(/\|1$/.test(props.SAB_RAPIDO_DIA), '[2026.11.08a] volta rápida contada no dia');
const pasta = novaPasta('SAB_pedido_' + ID);
arquivo(pasta, '00_Pedido_' + ID + '.csv', manifesto(ID, 'aceito', '', ['Diaria_Pato_Branco_2025.csv', '00_Dicionario_Variaveis_SAB.csv']));
arquivo(pasta, '00_Dicionario_Variaveis_SAB.csv', 'x');
horas(0.2); ctx.verificarPedidos();
confere(P(2).Status === 'em_preparo' && P(2).Detalhe === '1 de 2 arquivos prontos', 'em preparo: 1 de 2');
arquivo(pasta, 'Diaria_Pato_Branco_2025.csv', 'x', 1.2);
horas(0.2); ctx.verificarPedidos();
L = P(2);
confere(L.Status === 'entregue' && L.Link === pasta.getUrl(), 'entregue, com o link da pasta');
confere(rapidoAtivo().length === 0, '[2026.11.08a] entregue e fila vazia: sem volta rápida (fica o acionador de 10 min)');
confere(pasta.compart && pasta.compart[0] === 'ANYONE_WITH_LINK' && pasta.compart[1] === 'VIEW', 'pasta compartilhada só para leitura');
const ent = emails[emails.length - 1];
confere(/prontos/.test(ent.subject) && ent.body.indexOf(pasta.getUrl()) !== -1 && /Diaria_Pato_Branco_2025.csv/.test(ent.body),
        'e-mail de entrega com o link e a lista');
confere(ent.replyTo === 'dono@gmail.com', 'resposta vai para o responsável');
confere(ent.attachments && ent.attachments.length === 1 && ent.attachments[0].getName() === 'SAB_' + ID + '.zip' &&
        /anexados a este e-mail/.test(ent.body) && /não exige conta Google/.test(ent.body), 'pedido pequeno: zip anexado e aviso sem conta Google');
confere(/65001: Unicode \(UTF-8\)/.test(ent.body) && /Não detectar tipos de dados/.test(ent.body) && /Vírgula/.test(ent.body) &&
        /Inglês \(Estados Unidos\)/.test(ent.body), 'CSV: instruções do Excel (UTF-8, vírgula, não detectar tipos, localidade)');
confere(/O QUE VOCÊ ACHOU/.test(ent.body) && /\(46\) 99907-5852/.test(ent.body) && /gratuitos/.test(ent.body) &&
        /voluntária/.test(ent.body), 'entrega pede opinião e traz o PIX com o aviso das limitações gratuitas');
confere(/Fase_ENSO/.test(ent.body) && /Fonte_ENSO/.test(ent.body), 'entrega explica as colunas ENSO');
horas(24 * 6); ctx.verificarPedidos();
confere(P(2).Status === 'entregue' && !pasta.apagada, 'com 6 dias a pasta continua');
horas(24 * 1.1); ctx.verificarPedidos();
confere(P(2).Status === 'expirado' && pasta.apagada, 'depois de 7 dias a pasta é apagada');

console.log('[fila: um pedido por vez]');
AGORA = new Date('2026-11-12T14:00:00-03:00').getTime();
acion = []; emails = [];
ctx.aoEnviarFormulario(responder(COD, 'a@x.com'));
ctx.aoEnviarFormulario(responder(COD, 'b@x.com'));
confere(P(3).Status === 'enviado' && P(4).Status === 'na_fila' && acion.length === 1, 'o segundo espera na fila');
const ID3 = P(3).ID_Pedido;
const p3 = novaPasta('SAB_pedido_' + ID3);
arquivo(p3, '00_Pedido_' + ID3 + '.csv', manifesto(ID3, 'recusado', 'O pedido tem 11.031.760 linhas', []));
ctx.verificarPedidos();
confere(P(3).Status === 'recusado' && /11.031.760/.test(emails.filter((e) => e.to === 'a@x.com').pop().body),
        'recusa do servidor chega ao solicitante com o motivo');
confere(P(4).Status === 'enviado' && acion.length === 2, 'vaga liberada: o segundo é acionado');

console.log('[limites e erros]');
ctx.aoEnviarFormulario(responder('qualquer coisa', 'c@x.com'));
confere(P(5).Status === 'recusado' && acion.length === 2, 'código alterado: recusado sem acionar o GitHub');
ctx.aoEnviarFormulario(responder(COD, 'sem-arroba'));
confere(P(6).Status === 'recusado', 'e-mail inválido');
['d@x.com', 'd@x.com', 'd@x.com', 'd@x.com'].forEach((e) => ctx.aoEnviarFormulario(responder(COD, e)));
confere(P(10).Status === 'recusado' && P(10).Detalhe === 'Limite diário por e-mail', '4º pedido do dia recusado');
const ID4 = P(4).ID_Pedido;
horas(7); ctx.verificarPedidos();
confere(P(4).Status === 'falha' && emails.some((e) => e.to === 'dono@gmail.com' && /Falha/.test(e.subject)),
        'sem manifesto em 6 h: falha e aviso ao responsável');
const p4f = novaPasta('SAB_pedido_' + ID4);
confere(emails.some((e) => e.to === 'b@x.com' && /problema/.test(e.subject)), 'solicitante avisado da falha');

console.log('[GitHub recusando, Drive cheio, motor rodando, nova tentativa]');
const fila = [7, 8, 9].map((l) => P(l).Status);
confere(fila.join() === 'enviado,na_fila,na_fila', 'pedidos de d@x.com: 1 acionado, 2 na fila');
const ID7 = P(7).ID_Pedido;
const p7 = novaPasta('SAB_pedido_' + ID7);
arquivo(p7, '00_Pedido_' + ID7 + '.csv', manifesto(ID7, 'falha', 'Erro no servidor do Earth Engine: timed out', []));
respostaGitHub = 401;
const antes = acion.length;
ctx.verificarPedidos();
confere(P(7).Status === 'falha' && !p7.apagada, 'manifesto de falha: pasta mantida para conferência');
confere(P(8).Status === 'na_fila' && /401/.test(P(8).Detalhe) && acion.length === antes + 1, 'GitHub 401: continua na fila');
confere(emails.some((e) => e.to === 'dono@gmail.com' && /GitHub recusou/.test(e.subject)), 'responsável avisado do token');
respostaGitHub = 204; usoDrive = 0.9;
ctx.verificarPedidos();
confere(P(8).Status === 'na_fila' && /espaço/.test(P(8).Detalhe), 'Drive acima de 85%: espera');
usoDrive = 0.1;
AGORA = new Date('2026-11-13T23:30:00-03:00').getTime();
ctx.verificarPedidos();
confere(P(8).Status === 'na_fila' && /horário do motor SAB \(22:50 às 24:00\)/.test(P(8).Detalhe),
        'das 22h50 à meia-noite (motor das 23h07, que começa ~23h47) não começa pedido novo');
AGORA = new Date('2026-11-14T00:40:00-03:00').getTime();
ctx.verificarPedidos();
confere(P(8).Status === 'na_fila' && /00:00 às 01:00/.test(P(8).Detalhe), 'da meia-noite à 01h00 (folga do atraso do GitHub) também não');
AGORA = new Date('2026-11-14T06:40:00-03:00').getTime();
confere(ctx.motorOcupado_(false) === '', 'às 06h40 não há janela (a rodada da manhã nunca foi implantada)');
AGORA = new Date('2026-11-14T15:30:00-03:00').getTime();
confere(ctx.motorOcupado_(false) === '', 'às 15h30 também não (a rodada das 15h07 saiu)');
AGORA = new Date('2026-11-14T22:49:00-03:00').getTime();
confere(ctx.motorOcupado_(false) === '', 'às 22h49 ainda pode começar pedido');
AGORA = new Date('2026-11-14T01:00:00-03:00').getTime();
confere(ctx.motorOcupado_(false) === '', 'à 01h00 a janela já fechou');
AGORA = new Date('2026-11-14T10:05:00-03:00').getTime();
props.MOTOR_REPO = 'u/sab-motor'; motorRodando = 1;
ctx.verificarPedidos();
confere(P(8).Status === 'na_fila' && /motor SAB rodando no GitHub/.test(P(8).Detalhe) &&
        consultas.some((u) => /repos\/u\/sab-motor\/actions\/runs/.test(u)), 'motor rodando (API do GitHub): a fila espera');
motorRodando = 0;
ctx.verificarPedidos();
confere(P(8).Status === 'enviado', 'motor parado e fora das janelas: é acionado');
R()[3][R()[0].indexOf('ID_Pedido')] = '';
R()[3][R()[0].indexOf('Status')] = 'na_fila';
const ID8 = P(8).ID_Pedido;
confere(!p4f.apagada, 'pasta da falha guardada para conferência');
const p8 = novaPasta('SAB_pedido_' + ID8);
arquivo(p8, '00_Pedido_' + ID8 + '.csv', manifesto(ID8, 'recusado', 'x', []));
ctx.verificarPedidos();
confere(P(4).ID_Pedido && P(4).ID_Pedido !== ID4 && P(4).Status === 'enviado',
        'responsável devolve à fila sem ID: ganha ID novo e é acionado');

console.log('[2026.11.08a: em sequência, sem esperar 10 min]');
{
  const iSt = R()[0].indexOf('Status'), iEnv = R()[0].indexOf('Enviado_em'), iConv = R()[0].indexOf('Conversao_em');
  const salvo = R().map((r) => r.slice());
  R().slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'convertendo', 'na_fila'].indexOf(r[iSt]) !== -1) r[iSt] = 'expirado'; });
  ctx.verificarPedidos();
  confere(rapidoAtivo().length === 0, 'sem pedido ativo: nenhuma volta rápida');
  R()[2][iSt] = 'convertendo'; R()[2][iConv] = new FakeDate(AGORA - 5 * 60000);
  confere(ctx.intervaloAcompanhamento_() === 1, 'convertendo há 5 min: volta em 1 min');
  R()[2][iConv] = new FakeDate(AGORA - 50 * 60000);
  confere(ctx.intervaloAcompanhamento_() === 5, 'na mesma etapa há 50 min (pedido grande): volta em 5 min');
  R()[2][iSt] = 'em_preparo'; R()[2][iEnv] = new FakeDate(AGORA - 2 * 60000);
  confere(ctx.intervaloAcompanhamento_() === 1, 'em preparo há 2 min: volta em 1 min');
  props.SAB_RAPIDO_DIA = vm.runInContext("Utilities.formatDate(new Date(), FUSO, 'yyyy-MM-dd')", ctx) + '|600';
  confere(ctx.intervaloAcompanhamento_() === 5, 'passou de 600 voltas rápidas no dia: 5 min (cota do Apps Script)');
  props.SAB_RAPIDO_DIA = '2000-01-01|900';
  confere(ctx.intervaloAcompanhamento_() === 1, 'dia novo: a contagem recomeça');
  R()[2][iSt] = 'expirado';
  travaLivre = false;
  ctx.aoEnviarFormulario(responder(COD, 'ocupado@x.com'));
  confere(rapidoAtivo().length === 1 && rapidoAtivo()[0].after === 60000 && cache.SAB_PENDENTE === '1',
          'sistema ocupado: pendente marcado e volta em 1 min (antes, até 10 min)');
  travaLivre = true;
  confere(ctx.intervaloAcompanhamento_() === 1, 'com pendente marcado, a volta seguinte continua rápida');
  ctx.verificarPedidos();
  confere(!cache.SAB_PENDENTE, 'a volta seguinte atende o pendente e limpa o aviso');
  // devolve a planilha como estava
  grade.splice(grade.length - 1, 1);
  salvo.forEach((r, i) => { R()[i] = r; }); R().length = salvo.length;
  rapidos.forEach((t) => { t.apagado = true; });
}

console.log('[diagnóstico]');
ctx._log.length = 0; ctx.diagnosticar();
confere(ctx._log.some((l) => /dono@gmail.com/.test(l)) && ctx._log.some((l) => /📁 SAB_pedido_/.test(l)), 'diagnosticar mostra a conta e as pastas');
confere(/ainda não está no Drive de dono@gmail.com|Pasta achada|arquivos prontos|Cálculo iniciado|entregue|recusado/.test(String(P(4).Detalhe)), 'Detalhe explica a espera');
horas(24 * 8); ctx.verificarPedidos();
confere(p7.apagada && R().slice(1).some((r) => r[R()[0].indexOf('Status')] === 'falha_expirada'),
        'falha: a pasta é apagada depois de 7 dias (falha_expirada)');
confere(p4f.apagada, 'pasta órfã (pedido devolvido à fila com ID novo) apagada depois de 7 dias');
console.log('[pedido grande: sem anexo]');
R().slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'na_fila'].indexOf(r[R()[0].indexOf('Status')]) !== -1) r[R()[0].indexOf('Status')] = 'expirado'; });
AGORA = new Date('2026-11-18T14:00:00-03:00').getTime();
emails = [];
ctx.aoEnviarFormulario(responder(COD, 'grande@x.com'));
const IDG = ultimo().ID_Pedido;
const pg1 = novaPasta('SAB_pedido_' + IDG);
arquivo(pg1, '00_Pedido_' + IDG + '.csv', manifesto(IDG, 'aceito', '', ['Diaria_Parana_2025.csv', '00_Dicionario_Variaveis_SAB.csv']));
arquivo(pg1, 'Diaria_Parana_2025.csv', 'x', 160);
arquivo(pg1, '00_Dicionario_Variaveis_SAB.csv', 'x', 0.01);
ctx.verificarPedidos();
const entG = emails.filter((e) => e.to === 'grande@x.com').pop();
confere(ultimo().Status === 'entregue' && !entG.attachments && !/anexados/.test(entG.body),
        '160 MB: só o link, sem anexo');

console.log('[pasta repetida pelo Earth Engine e conta institucional]');
AGORA = new Date('2026-11-20T14:00:00-03:00').getTime();
emails = [];
const iS = R()[0].indexOf('Status');
R().slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'na_fila'].indexOf(r[iS]) !== -1) r[iS] = 'expirado'; });  // fila livre
ctx.aoEnviarFormulario(responder(COD, 'e@x.com'));
const L11 = R().length, ID11 = P(L11).ID_Pedido;
confere(P(L11).Status === 'enviado', 'pedido novo acionado');
const pa = novaPasta('SAB_pedido_' + ID11), pb = novaPasta('SAB_pedido_' + ID11);
arquivo(pa, '00_Pedido_' + ID11 + '.csv', manifesto(ID11, 'aceito', '', ['Mensal_Pato_Branco_2020.csv', '00_Dicionario_Variaveis_SAB.csv']));
arquivo(pa, 'Mensal_Pato_Branco_2020.csv', 'x');
arquivo(pb, '00_Dicionario_Variaveis_SAB.csv', 'x');
bloquearLink = true;
ctx.verificarPedidos();
const LP = P(L11);
confere(LP.Status === 'entregue', 'duas pastas com o mesmo nome: entregue (antes ficava parado)');
confere(Object.keys(pa.arquivos).length === 3 && pb.apagada && LP.Link === pa.getUrl(), 'arquivos juntados na pasta do manifesto e a repetida apagada');
confere(pa.leitores.indexOf('e@x.com') !== -1 && /acesso só para o e-mail/.test(LP.Detalhe), 'link público bloqueado: acesso liberado para o e-mail de quem pediu');
confere(/abra o link com a conta Google e@x.com/.test(emails.filter((e) => e.to === 'e@x.com').pop().body), 'e-mail explica o acesso');
bloquearLink = false;
console.log('[pedido escolhido no formulário, sem o painel]');
['Como você quer fazer o pedido?', 'Local', 'Estados', 'Municípios', 'Pontos (coordenadas)', 'Área (vértices do polígono)',
 'Data inicial', 'Data final', 'Incluir a previsão dos próximos 15 dias?', 'Resolução', 'Variáveis']
  .forEach((h) => grade[0].push(h));     // colunas novas que o Forms acrescenta depois do montarFormulario
R().slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'na_fila'].indexOf(r[iS]) !== -1) r[iS] = 'expirado'; });
const valores = {'Carimbo de data/hora': new FakeDate(), 'Nome completo  ': 'Beltrano', 'E-mail para receber o link': 'f@x.com',
  'Como você quer fazer o pedido?': 'Vou escolher agora o local, o período e as variáveis', 'Local': 'Municípios',
  'Municípios': 'Pato Branco - PR\nChapecó - SC', 'Data inicial': new Date('2024-01-01T00:00:00-03:00'),
  'Data final': new Date('2024-12-31T00:00:00-03:00'), 'Incluir a previsão dos próximos 15 dias?': 'Não',
  'Resolução': 'Mensal', 'Variáveis': 'Precipitação (mm), Temperatura mínima (°C)'};
AGORA += 1000; grade.push(grade[0].map((h) => valores[h] !== undefined ? valores[h] : ''));
acion = [];
ctx.aoEnviarFormulario({range: {getSheet: () => aba, getRow: () => grade.length}});
const LF = ultimo();
const esperado = 'v=1;res=M;tipo=M;uf=Paraná,Santa Catarina;mun=Pato Branco,Chapecó;ini=2024-01-01;fim=2024-12-31;var=pr,tmin';
confere(LF.Status === 'enviado' && acion.length === 1 && acion[0].corpo.client_payload.codigo === esperado,
        'código montado das respostas e enviado ao GitHub');
confere(LF['Código do pedido'] === esperado && /2 municípios/.test(LF['Resumo do pedido']),
        'código e resumo gravados na aba Pedidos');
AGORA += 1000; grade.push(grade[0].map((h) => Object.assign({}, valores, {'Municípios': 'Pato Branco', 'Carimbo de data/hora': new FakeDate()})[h] || ''));
ctx.aoEnviarFormulario({range: {getSheet: () => aba, getRow: () => grade.length}});
confere(ultimo().Status === 'recusado' && /Pato Branco - PR/.test(emails[emails.length - 1].body),
        'resposta com erro: recusada e o e-mail explica como corrigir');

console.log('[pedido direto do painel, sem formulário (App da Web)]');
R().slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'na_fila'].indexOf(r[iS]) !== -1) r[iS] = 'expirado'; });
acion = []; emails = [];
const COD_P = 'v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-12-31;var=pr,tmax';
let pg = ctx.doGet({parameter: {codigo: COD_P, resumo: 'Paraná, diário, 2025', nome: 'Ciclana', email: 'G@X.com',
                                 inst: 'UTFPR', fin: 'Ensino', aceite: '1'}});
const LG = ultimo();
confere(/Pedido recebido/.test(pg.html) && /SAB-\d{4}/.test(pg.html), 'página confirma o pedido com o ID');
confere(LG['Código do pedido'] === COD_P && LG['Nome completo'] === 'Ciclana' && LG['Instituição'] === 'UTFPR' &&
        LG.Origem === 'Painel SAB' && grade.every((r) => r[3] !== 'Ciclana'), 'pedido do painel só na aba Pedidos (o Forms não é tocado)');
confere(LG.Status === 'enviado' && acion.length === 1 && acion[0].corpo.client_payload.codigo === COD_P,
        'pedido entra na fila e aciona o GitHub');
confere(emails.some((e) => e.to === 'g@x.com' && /Recebemos/.test(e.subject)), 'e-mail de confirmação');
pg = ctx.doGet({parameter: {codigo: COD_P, nome: 'X', email: 'h@x.com'}});
confere(/LGPD/.test(pg.html) && ultimo()['Nome completo'] !== 'X', 'sem aceite: não grava nada');
pg = ctx.doGet({parameter: {codigo: 'v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-12-31', nome: 'Y', email: 'sem-arroba', aceite: '1'}});
confere(/não é válido/.test(pg.html), 'e-mail inválido explicado na página');
pg = ctx.doGet({parameter: {}});
confere(/recebe os pedidos/.test(pg.html), 'sem pedido: página explica para que serve');
pg = ctx.doGet({parameter: {codigo: COD_P, nome: '<script>', email: 'z@x.com', aceite: '1', resumo: '<b>x</b>'}});
confere(pg.html.indexOf('<script>') === -1 && pg.html.indexOf('<b>x</b>') === -1, 'texto da pessoa escapado na página');

pg = ctx.doGet({parameter: {codigo: 'v=1;res=D;tipo=BR;ini=1961-01-01;fim=2026-11-15;var=todas', nome: 'W', email: 'w@x.com',
                             aceite: '1'}});
confere(/Brasil inteiro foi desativado/.test(pg.html) && ultimo().Status === 'recusado',
        'Brasil inteiro (painel antigo): recusado na hora, sem acionar o GitHub');

console.log('[2026.11.03: trava ocupada não perde o pedido; página recarregada não duplica]');
R().slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'na_fila'].indexOf(r[iS]) !== -1) r[iS] = 'expirado'; });
acion = []; emails = [];
const COD_T = 'v=1;res=D;tipo=E;uf=Paraná;ini=2024-01-01;fim=2024-12-31;var=pr';
travaLivre = false;
let nAntes = R().length;
pg = ctx.doGet({parameter: {codigo: COD_T, resumo: 'Paraná 2024', nome: 'Ocupada', email: 'oc@x.com', aceite: '1'}});
let LT = ultimo();
confere(/Pedido recebido/.test(pg.html) && /1 a\s+2 minutos/.test(pg.html) && !/Tempo limite/.test(pg.html),
        'painel com a trava ocupada: página "recebido", sem o erro do bloqueio');
confere(rapidoAtivo().length === 1 && rapidoAtivo()[0].after === 60000 && cache.SAB_PENDENTE === '1',
        '[2026.11.08a] painel com a trava ocupada: volta rápida em 1 min registra o pedido');
confere(R().length === nAntes + 1 && !LT.ID_Pedido && !LT.Status && /Aguardando registro/.test(LT.Detalhe) && acion.length === 0 && emails.length === 0,
        'linha gravada sem ID, sem e-mail e sem acionar o GitHub');
pg = ctx.doGet({parameter: {codigo: COD_T, resumo: 'Paraná 2024', nome: 'Ocupada', email: 'oc@x.com', aceite: '1'}});
confere(/já foi recebido/.test(pg.html) && R().length === nAntes + 1, 'recarregar a página não grava de novo');
pg = ctx.doGet({parameter: {codigo: COD_T, nome: 'Z', email: 'sem-arroba', aceite: '1'}});
confere(/não é válido/.test(pg.html) && R().length === nAntes + 1, 'trava ocupada e e-mail inválido: avisa e não grava');
AGORA += 1000;
grade.push(grade[0].map((h) => ({'Carimbo de data/hora': new FakeDate(), 'Nome completo  ': 'Form Ocupado',
  'E-mail para receber o link': 'fo@x.com', ['Código do pedido '.normalize('NFD')]: COD,
  'Como você quer fazer o pedido?': 'Já escolhi no painel SAB (código preenchido)'})[h] || ''));
const linhaForm = grade.length;
ctx._log.length = 0;
ctx.aoEnviarFormulario({range: {getSheet: () => aba, getRow: () => linhaForm}});
confere(!comEmail('fo@x.com').length && ctx._log.some((l) => /registrada pelo verificarPedidos/.test(l)),
        'formulário com a trava ocupada: a execução termina sem erro e a resposta espera');
const velha = grade[0].map((h) => ({'Carimbo de data/hora': new FakeDate(AGORA - 3 * 864e5), 'Nome completo  ': 'Antiga',
  'E-mail para receber o link': 'antiga@x.com', ['Código do pedido '.normalize('NFD')]: COD})[h] || '');
grade.push(velha); const linhaVelha = grade.length;
travaLivre = true;
horas(0.1); ctx.verificarPedidos();
LT = P(nAntes + 1);
confere(/^SAB-\d{4}$/.test(LT.ID_Pedido) && ['na_fila', 'enviado'].indexOf(LT.Status) !== -1 &&
        emails.some((e) => e.to === 'oc@x.com' && /Recebemos/.test(e.subject)), 'verificarPedidos registra o pedido do painel e manda a confirmação');
confere(comEmail('fo@x.com').length === 1 && /^SAB-\d{4}$/.test(comEmail('fo@x.com')[0].ID_Pedido) && emails.some((e) => e.to === 'fo@x.com' && /Recebemos/.test(e.subject)),
        'verificarPedidos registra a resposta do formulário');
confere(!comEmail('antiga@x.com').length && !emails.some((e) => e.to === 'antiga@x.com'),
        'linha antiga (mais de 24 h) sem ID não é tocada');
pg = ctx.doGet({parameter: {codigo: COD_T, resumo: 'Paraná 2024', nome: 'Ocupada', email: 'oc@x.com', aceite: '1'}});
confere(new RegExp('registrado como ' + LT.ID_Pedido).test(pg.html), 'página recarregada depois: mostra o ID já registrado');
const idsAntes = R().slice(1).map((r) => r[0]).filter((x) => x).length;
horas(0.1); ctx.verificarPedidos();
confere(R().slice(1).map((r) => r[0]).filter((x) => x).length === idsAntes, 'segunda passada não registra nada de novo');

console.log('[formato Excel: conversão no GitHub antes da entrega]');
R().slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'na_fila'].indexOf(r[iS]) !== -1) r[iS] = 'expirado'; });
AGORA = new Date('2026-11-25T10:00:00-03:00').getTime();
acion = []; emails = [];
ctx.aoEnviarFormulario(responder(COD + ';fmt=ambos', 'x1@x.com'));
const LX = R().length, IDX = P(LX).ID_Pedido;
const px = novaPasta('SAB_pedido_' + IDX);
arquivo(px, '00_Pedido_' + IDX + '.csv', manifesto(IDX, 'aceito', '', ['Diaria_Pato_Branco_2025.csv', '00_Dicionario_Variaveis_SAB.csv']));
arquivo(px, 'Diaria_Pato_Branco_2025.csv', 'x');
arquivo(px, '00_Dicionario_Variaveis_SAB.csv', 'x');
ctx.verificarPedidos();
const conv = acion.filter((a) => a.corpo.event_type === 'converter_xlsx').pop();
confere(P(LX).Status === 'convertendo' && conv && conv.corpo.client_payload.pasta_id === px.getId() &&
        conv.corpo.client_payload.modo === 'ambos' && conv.corpo.client_payload.pedido_id === IDX,
        'CSV prontos: aciona a conversão com o ID da pasta e o modo');
ctx.aoEnviarFormulario(responder(COD, 'x2@x.com'));
confere(ultimo().Status === 'enviado', 'enquanto converte, o próximo pedido já pode calcular');
horas(0.3); ctx.verificarPedidos();
confere(P(LX).Status === 'convertendo', 'sem o marcador: continua convertendo');
arquivo(px, 'Diaria_Pato_Branco_2025.xlsx', 'x'); arquivo(px, '00_Dicionario_Variaveis_SAB.xlsx', 'x');
arquivo(px, '00_Conversao_' + IDX + '.csv', 'Pedido,Arquivo,Status,Linhas,Detalhe\n' + IDX + ',Diaria_Pato_Branco_2025.xlsx,ok,10,\n' +
        IDX + ',00_Dicionario_Variaveis_SAB.xlsx,ok,36,\n');
horas(0.2); ctx.verificarPedidos();
const entX = emails.filter((e) => e.to === 'x1@x.com').pop();
confere(P(LX).Status === 'entregue' && /com Excel/.test(P(LX).Detalhe) && /\.xlsx/.test(entX.body) &&
        /duplo clique/.test(entX.body) && !/00_Conversao_/.test(entX.body), 'marcador chegou: entrega com os .xlsx');
const LX2 = R().length;
ctx.aoEnviarFormulario(responder(COD + ';fmt=xlsx', 'x3@x.com'));
const IDX3 = ultimo().ID_Pedido;
const LX3 = R().length;
const IDX2 = P(LX2).ID_Pedido;
const px2 = novaPasta('SAB_pedido_' + IDX2);
arquivo(px2, '00_Pedido_' + IDX2 + '.csv', manifesto(IDX2, 'recusado', 'x', []));
ctx.verificarPedidos();
const px3 = novaPasta('SAB_pedido_' + IDX3);
arquivo(px3, '00_Pedido_' + IDX3 + '.csv', manifesto(IDX3, 'aceito', '', ['Diaria_Pato_Branco_2025.csv']));
arquivo(px3, 'Diaria_Pato_Branco_2025.csv', 'x');
ctx.verificarPedidos();
confere(P(LX3).Status === 'convertendo', 'formato xlsx: convertendo');
horas(7); ctx.verificarPedidos();
const entX3 = emails.filter((e) => e.to === 'x3@x.com').pop();
confere(P(LX3).Status === 'entregue' && /conversão incompleta/.test(P(LX3).Detalhe) &&
        /não foi possível/.test(entX3.body) && /65001/.test(entX3.body), 'conversão sem resposta em 6 h: entrega o CSV com aviso');
R().slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'na_fila'].indexOf(r[iS]) !== -1) r[iS] = 'expirado'; });
acion = [];
ctx.aoEnviarFormulario(responder(COD + ';fmt=xlsx', 'x4@x.com'));
const IDX4 = ultimo().ID_Pedido, LX4 = R().length;
const px4 = novaPasta('SAB_pedido_' + IDX4);
arquivo(px4, '00_Pedido_' + IDX4 + '.csv', ['Pedido,Status,Motivo,Arquivo,Linhas_Esperadas,Formato',
  [IDX4, 'aceito', '', '', '5000000', 'xlsx'].join(','), [IDX4, 'aceito', '', 'Diaria_Parana_2025.csv', '5000000', 'xlsx'].join(',')].join('\n'));
arquivo(px4, 'Diaria_Parana_2025.csv', 'x');
ctx.verificarPedidos();
confere(P(LX4).Status === 'entregue' && !acion.some((a) => a.corpo.event_type === 'converter_xlsx') &&
        /acima do limite/.test(emails.filter((e) => e.to === 'x4@x.com').pop().body), 'acima de 3 milhões de linhas: só CSV, com aviso');

console.log('[formulário novo: estados por região e municípios por estado, colunas da planilha]');
['Estados - Sul', 'Estados - Nordeste', 'Estado dos municípios', 'Municípios - Paraná', 'Municípios - Santa Catarina',
 'Municípios de outros estados (opcional)', 'Formato dos arquivos', 'Filtrar por fenômeno El Niño / La Niña']
  .forEach((h) => grade[0].push(h));
R().slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'na_fila', 'convertendo'].indexOf(r[iS]) !== -1) r[iS] = 'expirado'; });
const base2 = {'Carimbo de data/hora': new FakeDate(), 'Nome completo  ': 'Novo', 'E-mail para receber o link': 'n@x.com',
  'Data inicial': new Date('2024-01-01T00:00:00-03:00'), 'Data final': new Date('2024-12-31T00:00:00-03:00'),
  'Incluir a previsão dos próximos 15 dias?': 'Não', 'Resolução': 'Diária', 'Variáveis': 'Precipitação (mm)',
  'Filtrar por fenômeno El Niño / La Niña': 'Sem filtro (todos os meses)'};
acion = [];
AGORA += 1000; grade.push(grade[0].map((h) => Object.assign({}, base2, {'Carimbo de data/hora': new FakeDate(), 'Local': 'Estados', 'Estados - Sul': 'Paraná, Santa Catarina',
  'Estados - Nordeste': 'Bahia', 'Formato dos arquivos': 'Excel (.xlsx) com os números prontos para usar'})[h] || ''));
ctx.aoEnviarFormulario({range: {getSheet: () => aba, getRow: () => grade.length}});
confere(acion.length === 1 && acion[0].corpo.client_payload.codigo ===
        'v=1;res=D;tipo=E;uf=Bahia,Paraná,Santa Catarina;sep=1;ini=2024-01-01;fim=2024-12-31;var=pr;fmt=xlsx',
        'estados marcados em duas regiões (na ordem das regiões) + Excel: código certo');
R().slice(1).forEach((r) => { if (['enviado'].indexOf(r[iS]) !== -1) r[iS] = 'expirado'; });
AGORA += 1000; grade.push(grade[0].map((h) => Object.assign({}, base2, {'Carimbo de data/hora': new FakeDate(), 'Local': 'Municípios', 'Estado dos municípios': 'Paraná',
  'Municípios - Paraná': 'Pato Branco, Clevelândia', 'Municípios de outros estados (opcional)': 'Chapecó - SC'})[h] || ''));
ctx.aoEnviarFormulario({range: {getSheet: () => aba, getRow: () => grade.length}});
confere(acion.length === 2 && acion[1].corpo.client_payload.codigo ===
        'v=1;res=D;tipo=M;uf=Paraná,Santa Catarina;mun=Pato Branco,Clevelândia,Chapecó;ini=2024-01-01;fim=2024-12-31;var=pr',
        'municípios marcados na lista do estado + outro estado digitado: ' + (acion[1] || {corpo: {client_payload: {}}}).corpo.client_payload.codigo);

console.log('[GitHub App: token de 1 hora gerado sozinho, sem troca anual]');
delete props.GITHUB_TOKEN; delete props.MOTOR_TOKEN;
props.GITHUB_APP_ID = ' 123456 ';
props.GITHUB_APP_CHAVE = PAR.privateKey.replace(/\n/g, ' ');     // colado na propriedade: as quebras viram espaço
ctx._log.length = 0;
ctx.testarApp();
confere(ctx._log.some((l) => /✅ Chave do App aceita/.test(l)) && ctx._log.some((l) => /✅ u\/sab-pedidos: o App tem acesso/.test(l)) &&
        ctx._log.some((l) => /✅ u\/sab-motor: o App tem acesso/.test(l)) && !ctx._log.some((l) => /❌/.test(l)),
        'testarApp: chave PKCS#1 do GitHub convertida, token gerado e os dois repositórios acessíveis');
const [c64, p64, s64] = jwts[0].split('.');
const carga = JSON.parse(Buffer.from(p64, 'base64').toString());
confere(crypto.verify('sha256', Buffer.from(c64 + '.' + p64), PAR.publicKey, Buffer.from(s64, 'base64')),
        'JWT assinado com RS256 e conferido com a chave pública do App');
confere(carga.iss === 123456 && carga.exp - carga.iat === 600 && !/=/.test(jwts[0]), 'JWT: iss = App ID, 10 min, sem "="');
confere(props.GITHUB_APP_INSTALACAO === '777', 'instalação descoberta sozinha e guardada');
const semQuebras = ctx.chavePkcs8_(PAR.privateKey.replace(/\n/g, ''));
confere(crypto.verify('sha256', Buffer.from('x'), PAR.publicKey, crypto.sign('sha256', Buffer.from('x'),
        crypto.createPrivateKey(semQuebras))), 'chave colada sem nenhuma quebra de linha também funciona');
acion = []; tokensGerados = 0; cache = {};
ctx.testarGitHub(); ctx.testarGitHub();
confere(acion.length === 2 && acion.every((a) => a.aut === 'Bearer ghs_teste1') && tokensGerados === 1,
        'pedidos acionados com o token do App, reaproveitado do cache (um token por hora)');
AGORA = new Date('2026-12-01T10:00:00-03:00').getTime();
props.MOTOR_REPO = 'u/sab-motor'; consultas.length = 0;
ctx.testarMotor();
confere(consultas.some((c) => /actions\/runs.*Bearer ghs_teste/.test(c)), 'consulta do motor também usa o token do App');
cache = {}; respostaGitHub = 204;
const salvo = props.GITHUB_APP_CHAVE;
props.GITHUB_APP_CHAVE = 'colei errado';
const rr = ctx.acionarGitHub_('X1', COD, true);
confere(!rr.ok && rr.codigo === 'App' && /arquivo .pem inteiro/.test(rr.texto), 'chave errada: o acionamento falha com a explicação');
props.GITHUB_APP_CHAVE = salvo; delete props.GITHUB_APP_INSTALACAO; appInstalado = false; cache = {};
ctx._log.length = 0; ctx.testarApp();
confere(ctx._log.some((l) => /não está instalado em u\/sab-pedidos/.test(l)), 'App não instalado: testarApp diz o que fazer');
appInstalado = true;

console.log('[simulação pelo GitHub]');
ctx.testarGitHub();
const ult = acion[acion.length - 1].corpo.client_payload;
confere(ult.simular === '1' && ult.pedido_id === 'TESTE_GITHUB', 'testarGitHub manda simular=1');

console.log('[2026.11.04: pedidos de teste separados, ordem de chegada e zerar]');
AGORA = new Date('2026-12-02T10:00:00-03:00').getTime();
R().slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'na_fila', 'convertendo'].indexOf(r[iS]) !== -1) r[iS] = 'expirado'; });
acion = []; emails = [];
const nUsu = R().length;
['dono@gmail.com', 'dono@gmail.com', 'dono@gmail.com', 'DONO@gmail.com'].forEach((e) => ctx.aoEnviarFormulario(responder(COD, e)));
confere(RT().length === 5 && R().length === nUsu, 'pedidos do responsável vão para Pedidos_Teste, não para Pedidos');
confere(PT(2).ID_Pedido === 'TESTE-0001' && PT(5).ID_Pedido === 'TESTE-0004' && PT(5).Status !== 'recusado',
        'numeração própria (TESTE-0001...) e sem o limite de 3 por dia');
confere(PT(2).Status === 'enviado' && PT(3).Status === 'na_fila' && acion.length === 1, 'teste e usuários dividem a mesma fila');
props.EMAILS_TESTE = 'colega@ufpr.br, outra@x.com';
ctx.doGet({parameter: {codigo: COD, resumo: 'x', nome: 'Colega', email: 'Colega@UFPR.br', aceite: '1'}});
confere(PT(RT().length)['E-mail'] === 'colega@ufpr.br' && PT(RT().length).Origem === 'Painel SAB', 'EMAILS_TESTE também vão para Pedidos_Teste');
ctx.aoEnviarFormulario(responder(COD, 'usuaria@x.com'));
const IDu = ultimo().ID_Pedido;
confere(/^SAB-\d{4}$/.test(IDu) && ultimo().Status === 'na_fila', 'usuário chega depois e espera a vez dos testes: ' + IDu);
const quando = R().slice(1).map((r) => new Date(r[1]).getTime());
confere(quando.every((q, i) => i === 0 || q >= quando[i - 1]), 'aba Pedidos em ordem de chegada');
const idsNum = R().slice(1).map((r) => parseInt(String(r[0]).replace('SAB-', ''), 10)).filter((n) => !isNaN(n));
confere(new Set(idsNum).size === idsNum.length, 'nenhum ID repetido');
props.EMAIL_RESPONSAVEL = 'Adao@Alunos.utfpr.edu.br, dono@gmail.com';
ctx.doGet({parameter: {codigo: COD, resumo: 'x', nome: 'Inst', email: 'adao@alunos.utfpr.edu.br', aceite: '1'}});
confere(PT(RT().length)['E-mail'] === 'adao@alunos.utfpr.edu.br', '2026.11.04a: EMAIL_RESPONSAVEL com dois e-mails: o segundo também é teste');
confere(emails.filter((e) => e.to === 'adao@alunos.utfpr.edu.br').every((e) => e.replyTo === 'Adao@Alunos.utfpr.edu.br'),
        'resposta dos e-mails vai só para o primeiro (replyTo com um endereço)');
console.log('[zerarPedidos]');
const ativo = PT(2).ID_Pedido;
try { ctx.zerarPedidos(); confere(false, 'deveria recusar com pedido em cálculo'); }
catch (e) { confere(new RegExp(ativo).test(e.message) && R().length > 1, 'com pedido em cálculo: recusa e não apaga nada'); }
[R(), RT()].forEach((g) => g.slice(1).forEach((r) => { if (['enviado', 'em_preparo', 'convertendo', 'na_fila'].indexOf(r[iS]) !== -1) r[iS] = 'expirado'; }));
grade[0].push('ID_Pedido', 'Status');          // colunas que o sistema antigo criava na aba do Forms
const pastaVelha = novaPasta('SAB_pedido_SAB2026-00021');
ctx._log.length = 0;
ctx.zerarPedidos();
confere(R().length === 1 && RT().length === 1 && grade.length === 1, 'linhas de Pedidos, Pedidos_Teste e do Forms apagadas (cabeçalhos ficam)');
confere(grade[0].indexOf('ID_Pedido') === -1 && grade[0].indexOf('Status') === -1 && grade[0].indexOf('Local') !== -1,
        'colunas de controle antigas tiradas da aba do Forms (as perguntas ficam)');
confere(formApagado === 1 && pastaVelha.apagada && pastas.every((p) => p.apagada || p.nome.indexOf('SAB_pedido_') !== 0),
        'respostas do Forms e todas as pastas SAB_pedido_ apagadas');
confere(ctx._log.some((l) => /Pedidos zerados/.test(l) && /SAB-0001/.test(l)), 'log confirma');
ctx.aoEnviarFormulario(responder(COD, 'nova@x.com'));
ctx.aoEnviarFormulario(responder(COD, 'dono@gmail.com'));
confere(P(2).ID_Pedido === 'SAB-0001' && PT(2).ID_Pedido === 'TESTE-0001', 'numeração recomeça em SAB-0001 e TESTE-0001');

console.log('\n' + (falhas ? falhas + ' FALHA(S)' : 'SIMULAÇÃO DO APPS SCRIPT OK'));
process.exit(falhas ? 1 : 0);
