// A 2026.11.3 troca o botão "Gerar o pedido" + link por UM botão de envio. Confere que o endereço do pedido é
// exatamente o que a 2026.11.2 montava (mesmos campos, mesma ordem, mesmo código), que os avisos de campo faltando
// aparecem e que, fora da caixa do e-mail, o painel é o mesmo da 2026.11.2. Rodar: node testes/teste_06_2026_11_3.js
const fs = require('fs');
const path = require('path');
const ler = (n) => fs.readFileSync(path.join(__dirname, '..', n), 'utf8');
const novo = ler('06_painel_sab_2026_11_3.js'), velho = ler('06_painel_sab_2026_11_2.js');
let falhas = 0;
const confere = (c, m) => { console.log((c ? '  ok   ' : '  FALHA ') + m); if (!c) falhas++; };

function bloco(src, inicio) {                   // texto de inicio até a chave que fecha o primeiro "{"
  const i = src.indexOf(inicio);
  if (i < 0) throw new Error('não achado: ' + inicio);
  let n = 0;
  for (let k = src.indexOf('{', i); k < src.length; k++) {
    if (src[k] === '{') n++;
    if (src[k] === '}') { n--; if (n === 0) return src.slice(i, k + 1); }
  }
}
const lista = (src, nome) => { const i = src.indexOf('var ' + nome + ' = ['); return src.slice(i, src.indexOf('];', i) + 2); };
const CFG = { urlPedidoEmail: 'https://script.google.com/macros/s/X/exec' };

// --- 2026.11.3: função pura
const N = {};
new Function('CFG', 'N', lista(novo, 'FORMATOS_EMAIL') + '\n' + bloco(novo, 'function pedidoComFormato(') + '\n' +
  bloco(novo, 'function montarUrlPedidoEmail(') + '\nN.f = montarUrlPedidoEmail;')(CFG, N);

// --- 2026.11.2: o onClick antigo, com controles simulados
function urlVelha(p, c) {
  const val = (v) => ({ getValue: () => v });
  const saida = {};
  const lbl = (k) => ({ setValue: (v) => { saida[k] = v; }, setUrl: (u) => { saida.url = u; }, style: () => ({ set() {} }) });
  const env = { APP: { pedidoEmail: p }, CFG, box_email_nome: val(c.nome), box_email_endereco: val(c.email),
    box_email_inst: val(c.inst), select_email_fin: val(c.fin), select_email_formato: val(c.formato),
    check_email_lgpd: val(c.lgpd), label_email_link: lbl('link'), label_email_aviso: lbl('aviso'), logInfo() {} };
  const corpo = bloco(velho, 'btn_email_gerar.onClick(function()').replace('btn_email_gerar.onClick(function()', 'function clicar()');
  new Function(...Object.keys(env), lista(velho, 'FORMATOS_EMAIL') + '\n' + bloco(velho, 'function pedidoComFormato(') +
    '\n' + corpo + '\nclicar();')(...Object.values(env));
  return saida;
}

const pedido = { codigo: 'v=1;res=D;tipo=P;pol=-30.9 -51.4,-30.9 -51.1,-31.2 -51.1,-31.2 -51.4;ini=2024-01-01;fim=2024-03-31;var=todas',
                 resumo: '1 área(s) desenhada(s), diário, 01/01/2024 a 31/03/2024, todas as variáveis' };
const completo = { nome: '  Maria da Silva ', email: 'maria@ufpr.br', inst: 'UFPR & cia', fin: 'Pesquisa acadêmica',
                   formato: 'CSV e Excel (.xlsx)', lgpd: true };
for (const formato of ['CSV', 'Excel (.xlsx), números prontos', 'CSV e Excel (.xlsx)']) {
  const c = Object.assign({}, completo, { formato });
  const r = N.f(pedido, c), v = urlVelha(pedido, c);
  confere(r.url && r.url === v.url, `endereço igual ao da 2026.11.2 (${formato})`);
}
const r0 = N.f(pedido, { nome: 'Ma', email: 'x', fin: '', lgpd: false });
confere(r0.erro && ['nome completo', 'e-mail válido', 'finalidade', 'LGPD'].every((s) => r0.erro.includes(s)),
        'campos faltando listados juntos: ' + r0.erro);
confere(N.f(null, completo).erro === 'Processe os dados primeiro.', 'sem processar: aviso');
const sete = { codigo: 'v=1;res=M;tipo=E;uf=Paraná,Bahia,Goiás,Pará,Piauí,Ceará,Acre;ini=2025-01-01;fim=2025-12-31;var=todas', resumo: 'x' };
confere(/6 estados/.test(N.f(sete, completo).erro), 'mais de 6 estados: aviso');
confere(!N.f(Object.assign({}, pedido), Object.assign({}, completo, { lgpd: false })).url, 'sem o aceite: sem botão');

// --- fora da caixa do e-mail, nada muda
const corta = (s) => s.slice(0, s.indexOf('var label_email_formato')) + s.slice(s.indexOf('// [2026.10.6] Acrescenta ;fmt=xlsx'));
const semCabecalho = (s) => corta(s).split('\n').filter((l) => !/^\/\/ |^\/\/   |versao: '2026\.11\./.test(l)).join('\n');
confere(semCabecalho(novo) === semCabecalho(velho), 'resto do painel idêntico ao da 2026.11.2');
confere(!/btn_email_gerar/.test(novo) && /w\.onChange\(atualizarEnvioEmail\)/.test(novo), 'botão antigo removido; campos ligados ao botão novo');
console.log('\n' + (falhas ? falhas + ' FALHA(S)' : 'TODOS OS TESTES PASSARAM'));
process.exit(falhas ? 1 : 0);
