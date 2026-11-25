// Testa a montagem do código a partir das respostas (montarCodigo_) e a montagem do formulário (montarFormulario)
// com um FormApp simulado. Rodar: node teste_formulario_gs.js
const fs = require('fs');
const vm = require('vm');
const path = require('path');

function formatDate(d, tz, fmt) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', {timeZone: tz, year: 'numeric', month: '2-digit',
    day: '2-digit', hour: '2-digit', hour12: false}).formatToParts(d).map((x) => [x.type, x.value]));
  if (fmt === 'yyyy-MM-dd') return p.year + '-' + p.month + '-' + p.day;
  if (fmt === 'H') return String(Number(p.hour));
  if (fmt === 'yyyy') return p.year;
  return p.day + '/' + p.month + '/' + p.year;
}

// ---------------- FormApp simulado
const TIPOS = {TEXT: 'TEXT', PARAGRAPH_TEXT: 'PARAGRAPH_TEXT', MULTIPLE_CHOICE: 'MULTIPLE_CHOICE', CHECKBOX: 'CHECKBOX',
               DATE: 'DATE', PAGE_BREAK: 'PAGE_BREAK'};
let itens = [];
const contagem = {listas: 0, movidos: 0, titulos: 0};
function novoItem(tipo, titulo) {
  const it = {tipo, titulo: titulo || '', escolhas: [], obrig: false, ajuda: '', vaiPara: null};
  const self = {
    _d: it, getTitle: () => { contagem.titulos++; if (it.apagado) throw new Error('Item ausente (talvez tenha sido excluído)'); return it.titulo; },
    getType: () => tipo, getIndex: () => itens.indexOf(self),
    setTitle: (t) => { it.titulo = t; return self; }, setRequired: (b) => { it.obrig = b; return self; },
    setHelpText: (t) => { it.ajuda = t; return self; },
    setChoices: (l) => { it.escolhas = l; return self; },
    setChoiceValues: (l) => { contagem.listas++; it.escolhas = l.map((v) => ({valor: v})); return self; },
    getChoices: () => it.escolhas.map((c) => ({getValue: () => c.valor})), getHelpText: () => it.ajuda,
    createChoice: (v, pag) => ({valor: v, pag}), setGoToPage: (p) => { it.vaiPara = p; return self; },
    createResponse: (v) => ({titulo: it.titulo, v}),
    asTextItem: () => self, asParagraphTextItem: () => self, asMultipleChoiceItem: () => self,
    asCheckboxItem: () => self, asDateItem: () => self, asPageBreakItem: () => self
  };
  itens.push(self);
  return self;
}
const form = {
  getItems: () => itens.slice(),
  addPageBreakItem: () => novoItem(TIPOS.PAGE_BREAK), addMultipleChoiceItem: () => novoItem(TIPOS.MULTIPLE_CHOICE),
  addCheckboxItem: () => novoItem(TIPOS.CHECKBOX), addParagraphTextItem: () => novoItem(TIPOS.PARAGRAPH_TEXT),
  addDateItem: () => novoItem(TIPOS.DATE),
  deleteItem: (it) => { it._d.apagado = true; itens.splice(itens.indexOf(it), 1); },   // como no Forms: apagado não lê
  moveItem: (de, para) => { contagem.movidos++; const [x] = itens.splice(de, 1); itens.splice(para, 0, x); },
  setProgressBar: () => form, setDescription: () => form, getPublishedUrl: () => 'https://forms/publicado',
  createResponse: () => { const r = {lista: [], withItemResponse: (x) => { r.lista.push(x); return r; },
    toPrefilledUrl: () => 'https://forms/pre?' + r.lista.map((x) => x.titulo + '=' + x.v).join('&')}; return r; }
};
// formulário como o usuário criou (passo 6 do guia)
[['TEXT', 'Código do pedido'], ['PARAGRAPH_TEXT', 'Resumo do pedido'], ['TEXT', 'Nome completo'],
 ['TEXT', 'E-mail para receber o link'], ['TEXT', 'Instituição'], ['MULTIPLE_CHOICE', 'Finalidade do uso dos dados'],
 ['CHECKBOX', 'Consentimento']].forEach(([t, n]) => novoItem(t, n));
const originais = itens.slice();

// lista de municípios do GAUL (workflow "Lista de municípios"), com nomes de estado sem acento, como no GAUL
const UFS = ['Acre', 'Alagoas', 'Amapa', 'Amazonas', 'Bahia', 'Ceara', 'Distrito Federal', 'Espirito Santo', 'Goias',
  'Maranhao', 'Mato Grosso', 'Mato Grosso do Sul', 'Minas Gerais', 'Para', 'Paraiba', 'Parana', 'Pernambuco', 'Piaui',
  'Rio de Janeiro', 'Rio Grande do Norte', 'Rio Grande do Sul', 'Rondonia', 'Roraima', 'Santa Catarina', 'Sao Paulo',
  'Sergipe', 'Tocantins'];
let CSV_MUN = 'Estado,Municipio\n' + UFS.map((u) => u + ',Capital de ' + u).join('\n') +
  '\nParana,Pato Branco\nParana,Clevelândia\nParana,Pato Branco\nSanta Catarina,Chapecó\nLagoa dos Patos,Lagoa\n';
let temArquivo = true;
const PROPS = {};
function parseCsv(txt) { return txt.trim().split('\n').map((l) => l.split(',')); }
const logs = [];
const ctx = {Date, Math, JSON, Number, String, Object, Array, Error, isNaN, console,
  Logger: {log: (m) => logs.push(String(m))}, Utilities: {formatDate, parseCsv},
  PropertiesService: {getScriptProperties: () => ({getProperty: (k) => PROPS[k] || null, setProperty: (k, v) => { PROPS[k] = v; }})},
  DriveApp: {getFilesByName: () => { let ok = temArquivo; return {hasNext: () => ok, next: () => { ok = false;
    return {isTrashed: () => false, getLastUpdated: () => new Date(), getBlob: () => ({getDataAsString: () => CSV_MUN})}; }}; }},
  SpreadsheetApp: {getActive: () => ({getFormUrl: () => 'https://forms/edit'})},
  FormApp: {openByUrl: () => form, ItemType: TIPOS, PageNavigationType: {CONTINUE: 'CONTINUE'}}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, 'Codigo.gs'), 'utf8'), ctx);

let falhas = 0;
function confere(c, m) { console.log((c ? '  ok   ' : '  FALHA ') + m); if (!c) falhas++; }
const AGORA = new Date('2026-10-30T10:00:00-03:00');
const base = {codigo: '', resumo: '', origem: '', resolucao: 'Diária', previsao: 'Não',
              dataIni: new Date('2025-01-01T00:00:00-03:00'), dataFim: new Date('2025-12-31T00:00:00-03:00'),
              variaveis: 'Todas as variáveis', estados: '', estadosSel: '', estadoMun: '', munPorEstado: {},
              municipios: '', munOutros: '', pontos: '', vertices: '', formato: ''};
const M = (extra) => ctx.montarCodigo_(Object.assign({}, base, extra), AGORA);
const erro = (extra, trecho) => { try { M(extra); return false; } catch (e) { return e.message.indexOf(trecho) !== -1 || e.message; } };
const E1 = {local: 'Estados', estadosSel: 'Paraná'};

console.log('[montarCodigo_: local]');
confere(erro({local: 'Brasil inteiro'}, 'Brasil inteiro foi desativado') === true, 'Brasil inteiro (formulário antigo) recusado');
confere(erro({codigo: 'v=1;res=D;tipo=BR;ini=1961-01-01;fim=2026-11-15;var=todas'}, 'Brasil inteiro foi desativado') === true,
        'Brasil inteiro (painel antigo) recusado');
confere(M({local: 'Estados', estadosSel: 'Paraná, Santa Catarina, Bahia'}).codigo ===
        'v=1;res=D;tipo=E;uf=Paraná,Santa Catarina,Bahia;sep=1;ini=2025-01-01;fim=2025-12-31;var=todas',
        'estados de duas regiões: um arquivo por estado');
confere(erro({local: 'Estados', estadosSel: 'Acre, Amapá, Amazonas, Pará, Rondônia, Roraima, Tocantins'}, 'No máximo 6') === true,
        'sete estados recusados');
confere(erro({local: 'Estados'}, 'pelo menos um estado') === true, 'nenhum estado marcado');
let r = M({local: 'Municípios', estadoMun: 'Paraná', munPorEstado: {'Paraná': 'Pato Branco, Clevelândia'},
           munOutros: 'Chapecó - SC\nXique-Xique BA\nPato Branco (PR)'});
confere(r.codigo === 'v=1;res=D;tipo=M;uf=Paraná,Santa Catarina,Bahia;mun=Pato Branco,Clevelândia,Chapecó,Xique-Xique;' +
        'ini=2025-01-01;fim=2025-12-31;var=todas', 'municípios marcados na lista + digitados de outros estados: ' + r.codigo);
confere(M({local: 'Municípios', municipios: 'Pato Branco - PR'}).codigo.indexOf('mun=Pato Branco;') !== -1,
        'resposta antiga (municípios digitados) ainda funciona');
confere(erro({local: 'Municípios', estadoMun: 'Paraná', munOutros: 'Pato Branco'}, 'sigla do estado') === true, 'digitado sem UF');
confere(erro({local: 'Municípios', estadoMun: 'Paraná', munOutros: 'Vila Rica'}, 'sigla do estado') === true,
        'nome que termina em 2 letras sem separador não vira UF');
confere(erro({local: 'Municípios', munOutros: 'Pato Branco - XX'}, 'não é uma UF') === true, 'UF inexistente');
confere(erro({local: 'Municípios', estadoMun: 'Paraná'}, 'pelo menos um município') === true, 'nenhum município marcado');
r = M({local: 'Pontos (coordenadas)', pontos: 'Fazenda A; -26.2285; -52.6712\nSítio B; -26,15; -52,70\n' +
  'Área C; 26°13\'42"S; 52°40\'16"W\n-25.4284, -49.2733\n25 25 48 S 49 16 24 W\nSem sinal; -26.1; 52.6'});
confere(r.codigo.indexOf('tipo=C;pts=-26.228500 -52.671200 Fazenda A|-26.150000 -52.700000 Sítio B|' +
        '-26.228333 -52.671111 Área C|-25.428400 -49.273300 Ponto 4|-25.430000 -49.273333 Ponto 5|' +
        '-26.100000 -52.600000 Sem sinal;') !== -1, 'pontos em decimal, vírgula, graus, sem nome e longitude sem sinal');
confere(erro({local: 'Pontos (coordenadas)', pontos: 'A; 26.2; -52.6'}, 'fora do Brasil') === true, 'latitude sem o sinal do sul');
confere(erro({local: 'Pontos (coordenadas)', pontos: 'A; 26°13\'42"; 52°40\'16"W'}, 'N ou S') === true, 'graus sem hemisfério');
confere(erro({local: 'Pontos (coordenadas)', pontos: 'A, -26,2, -52,6'}, 'ponto e vírgula') === true, 'vírgula ambígua');
r = M({local: 'Área desenhada (polígono)', vertices: '-26.2; -52.7\n-26.2; -52.6\n-26.3; -52.6\n-26.3; -52.7\n\n' +
  '25°S; 51°W\n25°S; 50°54\'W\n25°06\'S; 50°54\'W\n25°06\'S; 51°W'});
confere(r.codigo.indexOf('tipo=P;pol=-26.200000 -52.700000,-26.200000 -52.600000,-26.300000 -52.600000,' +
        '-26.300000 -52.700000|-25.000000 -51.000000,-25.000000 -50.900000,-25.100000 -50.900000,-25.100000 -51.000000;') !== -1,
        'duas áreas, decimal e graus');
confere(erro({local: 'Área desenhada (polígono)', vertices: '-26.2; -52.7\n-26.2; -52.6\n-26.3; -52.6'}, 'pelo menos 4') === true,
        'área com 3 vértices');

console.log('[montarCodigo_: período, variáveis, formato e painel]');
r = M(Object.assign({}, E1, {resolucao: 'Mensal', variaveis: 'Precipitação (mm), Temperatura máxima (°C), Déficit hídrico (mm)'}));
confere(/res=M;.*var=pr,tmax,def$/.test(r.codigo), 'mensal com 3 variáveis');
r = M(Object.assign({}, E1, {previsao: 'Sim', dataIni: new Date('2026-10-01T00:00:00-03:00')}));
confere(/fim=2026-11-14/.test(r.codigo) && /previsão até 14\/11\/2026/.test(r.resumo), 'previsão: data final = hoje + 15');
r = M(Object.assign({}, E1, {dataFim: '31/12/2027'}));
confere(/fim=2026-11-14/.test(r.codigo) && /ajustada/.test(r.resumo), 'data final depois da previsão: ajustada');
confere(erro(Object.assign({}, E1, {dataIni: '01/01/1960'}), '1961') === true, 'antes de 1961');
confere(erro(Object.assign({}, E1, {dataIni: '01/02/2025', dataFim: '01/01/2025'}), 'anterior à inicial') === true, 'fim antes do início');
confere(erro({local: ''}, 'Escolha o local') === true, 'sem local');
r = M(Object.assign({}, E1, {formato: 'Excel (.xlsx) com os números prontos para usar'}));
confere(/;fmt=xlsx$/.test(r.codigo) && /em Excel/.test(r.resumo), 'formato Excel: fmt=xlsx');
r = M(Object.assign({}, E1, {formato: 'CSV e Excel (.xlsx)', enso: 'La Niña fraca (−0,5 a −0,9 °C)'}));
confere(/;enso=La_Nina_Fraca;fmt=ambos$/.test(r.codigo), 'formato ambos com ENSO');
confere(!/fmt=/.test(M(Object.assign({}, E1, {formato: 'CSV (abre em qualquer programa; no Excel siga as instruções do e-mail)'})).codigo),
        'CSV: sem fmt no código (padrão)');
const painel = 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=todas;fmt=ambos';
r = M({codigo: painel, resumo: 'do painel', origem: 'Já escolhi no painel SAB (código preenchido)'});
confere(r.codigo === painel && !r.gerado, 'pedido do painel passa sem mudança');
confere(ctx.formatoDoCodigo_(painel) === 'ambos' && ctx.formatoDoCodigo_('v=1;res=D') === 'csv', 'formato lido do código');
confere(erro({origem: 'Já escolhi no painel SAB (código preenchido)'}, 'código do pedido está vazio') === true, 'painel sem código');
confere(erro({codigo: 'qualquer coisa'}, 'formato do painel') === true, 'código alterado');
confere(M(E1).resumo === 'Paraná, diário, 01/01/2025 a 31/12/2025, todas as variáveis', 'resumo legível');

console.log('[montarFormulario]');
// formulário como estava na versão 2026.10.30f (lista única de estados e municípios digitados)
const velhaOrigem = novoItem('MULTIPLE_CHOICE', 'Como você quer fazer o pedido?');
const velhaPagina = novoItem('PAGE_BREAK', 'Local do pedido');
const velhosEstados = novoItem('CHECKBOX', 'Estados');
const velhosMun = novoItem('PARAGRAPH_TEXT', 'Municípios');
temArquivo = false;
try { ctx.montarFormulario(); confere(false, 'sem a lista de municípios deveria parar'); }
catch (e) { confere(/Lista de municípios > Run workflow/.test(e.message), 'sem a lista: manda rodar o workflow do GitHub'); }
temArquivo = true;
logs.length = 0;
ctx.montarFormulario(0);                          // tempo esgotado logo no começo das listas
confere(logs.some((l) => /⏸️ Parte do formulário montada/.test(l) && /Rode montarFormulario de novo/.test(l)) &&
        !logs.some((l) => /✅ Formulário montado/.test(l)), 'perto dos 6 minutos: para e pede para rodar de novo');
ctx.montarFormulario();
const titulos = itens.map((i) => i.getTitle());
const REG = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'];
const ordemUF = ['Acre', 'Amapá', 'Amazonas', 'Pará', 'Rondônia', 'Roraima', 'Tocantins', 'Alagoas', 'Bahia', 'Ceará',
  'Maranhão', 'Paraíba', 'Pernambuco', 'Piauí', 'Rio Grande do Norte', 'Sergipe', 'Distrito Federal', 'Goiás',
  'Mato Grosso', 'Mato Grosso do Sul', 'Espírito Santo', 'Minas Gerais', 'Rio de Janeiro', 'São Paulo', 'Paraná',
  'Rio Grande do Sul', 'Santa Catarina'];
const esperado = ['Local', 'Estados'].concat(REG.map((r) => 'Estados - ' + r))
  .concat(['Municípios', 'Municípios de outros estados (opcional)', 'Estado dos municípios'])
  .concat([].concat(...ordemUF.map((e) => ['Municípios: ' + e, 'Municípios - ' + e])))
  .concat(['Pontos', 'Pontos (coordenadas)', 'Área desenhada', 'Área (vértices do polígono)', 'Período e variáveis',
    'Data inicial', 'Incluir a previsão dos próximos 15 dias?', 'Data final', 'Filtrar por fenômeno El Niño / La Niña',
    'Resolução', 'Formato dos arquivos', 'Variáveis', 'Pedido do painel', 'Código do pedido', 'Resumo do pedido',
    'Seus dados', 'Nome completo', 'E-mail para receber o link', 'Instituição', 'Finalidade do uso dos dados', 'Consentimento']);
confere(titulos.join(' | ') === esperado.join(' | '), 'ordem: Local; estados por região; um estado e sua lista de municípios ' +
        'por página; Período com formato; seção interna do painel' + (titulos.join(' | ') === esperado.join(' | ') ? '' :
        '\n' + titulos.join(' | ')));
confere([velhaOrigem, velhaPagina, velhosEstados, velhosMun].every((x) => itens.indexOf(x) === -1),
        'perguntas antigas removidas (origem, página antiga, estados numa lista só, municípios digitados)');
const item = (t, tipo) => itens.filter((i) => i.getTitle() === t && (!tipo || i.getType() === tipo))[0]._d;
const pag = (t) => itens.filter((i) => i.getTitle() === t && i.getType() === 'PAGE_BREAK')[0];
confere(item('Local').escolhas.map((c) => c.valor + '>' + c.pag.getTitle()).join() ===
        'Estados>Estados,Municípios>Municípios,Pontos (coordenadas)>Pontos,Área desenhada (polígono)>Área desenhada',
        'local: sem Brasil inteiro; cada escolha vai para a sua seção');
confere(REG.every((r, k) => item('Estados - ' + r).escolhas.length === [7, 9, 4, 4, 3][k]) &&
        REG.every((r) => item('Estados - ' + r).obrig === false), 'estados por região (7+9+4+4+3), nenhuma lista obrigatória');
const em = item('Estado dos municípios');
confere(em.obrig && em.escolhas.length === 27 && em.escolhas.every((c) => c.pag.getTitle() === 'Municípios: ' + c.valor),
        'estado dos municípios: cada estado leva à página dos seus municípios');
confere(em.escolhas.map((c) => c.valor).join() === em.escolhas.map((c) => c.valor).slice().sort((a, b) => a.localeCompare(b, 'pt')).join() &&
        em.escolhas[0].valor === 'Acre' && em.escolhas[26].valor === 'Tocantins' && em.escolhas[25].valor === 'Sergipe',
        'estado dos municípios em ordem alfabética (Acre ... São Paulo, Sergipe, Tocantins)');
confere(item('Municípios - Paraná').escolhas.map((c) => c.valor).join() === 'Capital de Parana,Clevelândia,Pato Branco' &&
        item('Municípios - Paraná').obrig, 'Paraná: nomes do GAUL, sem repetir, em ordem alfabética');
confere(item('Municípios - Santa Catarina').escolhas.map((c) => c.valor).join() === 'Capital de Santa Catarina,Chapecó',
        'Santa Catarina');
confere(logs.some((l) => /Lagoa dos Patos/.test(l)), 'unidade do GAUL fora dos estados: ignorada com aviso');
confere(ordemUF.every((e, k) => (k + 1 < ordemUF.length ? pag('Municípios: ' + ordemUF[k + 1]) : pag('Pontos'))._d.vaiPara
          .getTitle() === 'Período e variáveis'), 'depois de cada página de estado, pula para Período');
confere(pag('Municípios')._d.vaiPara.getTitle() === 'Período e variáveis' && pag('Área desenhada')._d.vaiPara.getTitle() ===
        'Período e variáveis' && pag('Período e variáveis')._d.vaiPara === 'CONTINUE', 'Estados e Pontos pulam para Período');
confere(pag('Pedido do painel')._d.vaiPara.getTitle() === 'Seus dados', 'ninguém passa pela seção interna');
confere(item('Data final').obrig === false && item('Data inicial').obrig === true && /Deixe em branco/.test(item('Data final').ajuda),
        'data final não obrigatória (com previsão fica em branco)');
confere(/fim=2026-11-14/.test(M(Object.assign({}, E1, {previsao: 'Sim', dataFim: '', dataIni: new Date('2026-10-01T00:00:00-03:00')})).codigo),
        'previsão Sim com a data final em branco: aceito, fim = último dia da previsão');
confere(erro(Object.assign({}, E1, {previsao: 'Não', dataFim: ''}), 'marque "Sim" na previsão') === true,
        'previsão Não sem a data final: recusa explicada');
confere(item('Formato dos arquivos').escolhas.length === 3 && item('Formato dos arquivos').obrig, 'formato: CSV, Excel ou os dois');
confere(item('Filtrar por fenômeno El Niño / La Niña').escolhas.length === 10 &&
        /6 colunas/.test(item('Filtrar por fenômeno El Niño / La Niña').ajuda), 'ENSO: sem filtro + 9 cenários; explica as 6 colunas');
const aviso = item('Seus dados', 'PAGE_BREAK').ajuda;
confere(/Google Drive/.test(aviso) && /não exige conta Google/.test(aviso) && /SPAM/.test(aviso), 'aviso de entrega e de spam');
confere(item('Variáveis').escolhas.length === 20 && item('Variáveis').escolhas.every((c) => c.valor.indexOf(',') === -1),
        '19 variáveis + todas, sem vírgula nos rótulos');
confere(vm.runInContext('Object.keys(CONFIG.UF).every(function (k) { return CONFIG.UF[k].indexOf(",") === -1; })', ctx), 'nomes sem vírgula');
confere(item('Código do pedido').obrig === false, 'código do pedido não obrigatório');
confere(originais.every((o) => itens.indexOf(o) !== -1), 'perguntas originais reaproveitadas (sem colunas repetidas)');
const n = itens.length;
contagem.listas = 0; contagem.movidos = 0; contagem.titulos = 0;
ctx.montarFormulario();
confere(itens.length === n && itens.map((i) => i.getTitle()).join() === titulos.join(), 'rodar de novo não duplica nada');
confere(contagem.movidos === 0 && contagem.listas <= 10,
        'rodar de novo pula o que já está pronto (' + contagem.movidos + ' movidas, ' + contagem.listas + ' listas regravadas)');
confere(contagem.titulos <= 2 * n, 'cada título é lido uma vez só (' + contagem.titulos + ' leituras para ' + n + ' perguntas; ' +
        'antes eram dezenas de milhares)');
confere(Object.keys(JSON.parse(PROPS.SAB_FORM_LISTAS)).length === 27, 'as 27 listas marcadas como prontas');

console.log('\n' + (falhas ? falhas + ' FALHA(S)' : 'FORMULÁRIO OK'));
process.exit(falhas ? 1 : 0);
