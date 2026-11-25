// Teste das funções novas do painel 2026.10.7 (variáveis, pedido por e-mail e formato), sem Earth Engine.
// Extrai as funções do painel, roda com controles simulados e grava os códigos gerados em
// testes/dados/codigos_painel_2026_10_7.txt (a rotina Python os confere em teste_06_pedido_email.py).
// Rodar: node testes/teste_06_pedido_email.js
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', '06_painel_sab_2026_11_5.js'), 'utf8');

function funcao(nome) {                       // texto de "function nome(...) { ... }" com chaves balanceadas
  const i = src.indexOf('function ' + nome + '(');
  if (i < 0) throw new Error('função não achada: ' + nome);
  let j = src.indexOf('{', i), n = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') n++;
    if (src[k] === '}') { n--; if (n === 0) return src.slice(i, k + 1); }
  }
  throw new Error('chaves desbalanceadas em ' + nome);
}
const ini = src.indexOf('var VARIAVEIS_SAB = [');
const lista = src.slice(ini, src.indexOf('];', ini) + 2);
const iniF = src.indexOf('var FORMATOS_EMAIL = [');
const listaF = src.slice(iniF, src.indexOf('];', iniF) + 2);

// controles simulados
const ctl = (v) => ({ getValue: () => ctl.estado[v] });
ctl.estado = {};
const check_todas_vars = ctl('todas');
const select_resolucao = ctl('res');
const select_abrangencia = ctl('abr');
const check_filtrar_munis = ctl('munis');
let lista_estados_array = [], lista_cidades_array = [], lista_coords_array = [];
function infoCenarioEnso(v) { return v === 'El Niño Forte (1.5 a 1.9°C)' ?
  {value: v, label: 'El Niño forte (+1,5 a +1,9 °C)', arquivo: 'El_Nino_Forte'} : {value: v, label: v, arquivo: ''}; }
const CFG = { limiteLinhasLink: 100000, limiteArquivosLink: 20, urlPedidoEmail: 'https://script.google.com/x/exec' };
const APP = { filtroEnso: null };
let checks_vars = {};

eval(lista + '\n' + listaF + '\n' + ['variaveisEscolhidas', 'filtrarColunasPorVariaveis', 'montarCodigoPedido',
  'decidirEntrega', 'pedidoComFormato'].map(funcao).join('\n') + '\nglobalThis.F = {VARIAVEIS_SAB, FORMATOS_EMAIL, ' +
  'variaveisEscolhidas, filtrarColunasPorVariaveis, montarCodigoPedido, decidirEntrega, pedidoComFormato};');
F.VARIAVEIS_SAB.forEach((v) => { checks_vars[v[0]] = { getValue: () => (ctl.estado.vars || []).indexOf(v[0]) !== -1 }; });

let falhas = 0;
function confere(c, m) { console.log((c ? '  ok   ' : '  FALHA ') + m); if (!c) falhas++; }
const codigos = [];
const BASE = ['Tipo_Dado', 'Versao_Algoritmo', 'Data_Completa', 'Ano', 'Mes', 'Dia', 'N_Ponto', 'Latitude', 'Longitude',
              'Estado', 'Municipio'];
const NUM = F.VARIAVEIS_SAB.map((v) => v[1]);
const datas = { isoInicio: '2025-01-01', isoFim: '2025-12-31', totalDias: 365 };

console.log('[variáveis]');
ctl.estado = { todas: true };
const todasCols = BASE.concat(NUM, ['Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo']);
confere(F.filtrarColunasPorVariaveis(todasCols) === todasCols, 'todas: colunas sem mudança');
ctl.estado = { todas: false, vars: ['tmin', 'pr'] };
confere(F.filtrarColunasPorVariaveis(todasCols).join() ===
        BASE.concat(['Precipitacao_mm', 'Temperatura_Minima_C', 'Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo']).join(),
        'só chuva e mínima, na ordem do painel, com identificação e qualidade');
confere(F.variaveisEscolhidas().join() === 'pr,tmin', 'códigos na ordem da lista');
confere(F.VARIAVEIS_SAB.length === 19 && new Set(F.VARIAVEIS_SAB.map((v) => v[1])).size === 19, '19 variáveis sem repetir');

console.log('[código do pedido]');
ctl.estado = { todas: true, res: 'Diária', abr: 'Estados / Municípios', munis: false };
lista_estados_array = ['Paraná'];
let p = F.montarCodigoPedido(datas);
confere(p.codigo === 'v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-12-31;var=todas', 'estado: ' + p.codigo);
codigos.push(p.codigo);
lista_estados_array = ['Paraná', 'Santa Catarina'];
codigos.push(F.montarCodigoPedido(datas).codigo);
ctl.estado = { todas: false, vars: ['pr', 'tmax'], res: 'Mensal', abr: 'Estados / Municípios', munis: true };
lista_estados_array = ['Paraná']; lista_cidades_array = ['Pato Branco', 'Clevelândia'];
p = F.montarCodigoPedido(datas);
confere(p.codigo === 'v=1;res=M;tipo=M;uf=Paraná;mun=Pato Branco,Clevelândia;ini=2025-01-01;fim=2025-12-31;var=pr,tmax',
        'municípios, mensal, 2 variáveis');
confere(p.resumo === '2 municípios, mensal, 01/01/2025 a 31/12/2025, 2 variável(is)', 'resumo: ' + p.resumo);
codigos.push(p.codigo);
ctl.estado = { todas: true, res: 'Diária', abr: 'Coordenadas (Lat / Lon)' };
lista_coords_array = ['-26.2000, -52.7000', '-26.2000, -52.6000', '-26.3000, -52.6000', '-26.3000, -52.7000',
                      'NOVA_AREA_BREAK', '-25.123456, -51.000000', '-25.0, -50.9', '-25.1, -50.9', '-25.1, -51.0'];
p = F.montarCodigoPedido(datas);
confere(p.codigo === 'v=1;res=D;tipo=P;pol=-26.2000 -52.7000,-26.2000 -52.6000,-26.3000 -52.6000,-26.3000 -52.7000|' +
        '-25.123456 -51.000000,-25.0 -50.9,-25.1 -50.9,-25.1 -51.0;ini=2025-01-01;fim=2025-12-31;var=todas',
        'duas áreas desenhadas, com os números como estão na lista do painel');
codigos.push(p.codigo);

console.log('[link na hora ou e-mail]');
ctl.estado = { res: 'Diária' };
let d = F.decidirEntrega(15, 1, datas);
confere(d.link && !d.grande, 'Pato Branco 2025 (5.475 linhas): link na hora');
d = F.decidirEntrega(1889, 1, datas);
confere(!d.link && d.grande && /689\.485 linhas/.test(d.motivo), 'Paraná 2025 (689 mil linhas): e-mail');
d = F.decidirEntrega(1889, 1, { isoInicio: '2025-01-01', isoFim: '2025-01-31', totalDias: 31 });
confere(d.link, 'Paraná, 1 mês (58 mil linhas): link na hora');
d = F.decidirEntrega(15, 1, { isoInicio: '1991-01-01', isoFim: '2020-12-31', totalDias: 10958 });
confere(!d.link && /30 arquivo/.test(d.motivo), 'Pato Branco 30 anos: 30 arquivos, vai por e-mail');
ctl.estado = { res: 'Mensal' };
d = F.decidirEntrega(1889, 1, { isoInicio: '1961-01-01', isoFim: '1975-12-31', totalDias: 5479 });
confere(d.link && !d.grande, 'Paraná mensal 15 anos (15 arquivos de 22 mil linhas): link na hora');
APP.filtroEnso = 'El Niño Forte (1.5 a 1.9°C)';
ctl.estado = { res: 'Diária' };
d = F.decidirEntrega(1889, 1, datas);
confere(!d.link && d.grande && /Google Drive/.test(d.motivo), 'com filtro ENSO: grande vai por e-mail, com o aviso do Drive');
ctl.estado = { todas: true, res: 'Diária', abr: 'Estados / Municípios', munis: false };
lista_estados_array = ['Paraná'];
p = F.montarCodigoPedido(datas);
confere(/;enso=El_Nino_Forte$/.test(p.codigo) && /filtro El Niño forte/.test(p.resumo), 'código com o filtro ENSO: ' + p.codigo);
codigos.push(p.codigo);
APP.filtroEnso = null;
CFG.urlPedidoEmail = '';
d = F.decidirEntrega(1889, 1, datas);
confere(d.link, 'envio por e-mail não configurado: links como na 2026.10.4');

console.log('[formato da entrega por e-mail (2026.10.6)]');
const pp = {codigo: 'v=1;res=D;tipo=E;uf=Paraná;ini=2025-01-01;fim=2025-12-31;var=todas', resumo: 'Paraná'};
confere(F.pedidoComFormato(pp, 'CSV').codigo === pp.codigo, 'CSV: código sem fmt (padrão)');
let pf = F.pedidoComFormato(pp, 'Excel (.xlsx), números prontos');
confere(pf.codigo === pp.codigo + ';fmt=xlsx' && /Excel/.test(pf.resumo), 'Excel: ;fmt=xlsx');
codigos.push(pf.codigo);
pf = F.pedidoComFormato(pp, 'CSV e Excel (.xlsx)');
confere(pf.codigo === pp.codigo + ';fmt=ambos', 'os dois: ;fmt=ambos');
codigos.push(pf.codigo);
confere(F.FORMATOS_EMAIL.length === 3 && /spam/i.test(src.slice(src.indexOf('var label_email_spam'), src.indexOf('var check_email_lgpd'))),
        'caixa do e-mail com os 3 formatos e o aviso de spam');
confere(src.indexOf("'2026.11.5'") !== -1 && /máximo 6 estados/.test(src), 'versão 2026.11.5 e limite de 6 estados no e-mail');

fs.mkdirSync(path.join(__dirname, 'dados'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'dados', 'codigos_painel_2026_11_5.txt'), codigos.join('\n') + '\n');
console.log('\n' + (falhas ? falhas + ' FALHA(S)' : 'PAINEL: FUNÇÕES NOVAS OK'));
process.exit(falhas ? 1 : 0);
