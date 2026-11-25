// >>> K16 v3: gera os CSV do PAINEL rodando o próprio código do painel (06_painel_sab_*.js) no Node. <<<
// Usado pela K16 no Colab (não rode sozinho). O painel roda SEM MUDANÇA: só a tela (ui.*) é simulada aqui; o Earth
// Engine é o de verdade (@google/earthengine, a mesma biblioteca do Code Editor) e os CSV vêm do MESMO
// getDownloadURL que o botão de download do painel usa. Para cada caso, o script faz o que uma pessoa faria na
// tela: escolhe o modo, a resolução, o local, as datas e o filtro, clica em PROCESSAR e baixa todos os links.
//
// Uso: EE_TOKEN=<token de acesso> node k16_painel_node.js <painel.js> <pasta de saída> <casos.json> [projeto]
//   casos.json: [{"caso": "A1", "res": "Diária", "local": {...}, "ini": "01/01/2025", "fim": "31/12/2025",
//                 "enso": null, "esperados": ["Diaria_Pato_Branco_2025", "00_Dicionario_Variaveis_SAB"]}, ...]
//   local: {"tipo": "M", "uf": ["Paraná"], "mun": ["Pato Branco"]} ou {"tipo": "P", "pontos": [[-26.2, -52.7], ...]}
// Saída: <pasta>/<caso>/<arquivo>.csv e uma linha "K16P_RESULTADO {json}" por caso no fim de cada caso.
'use strict';
const fs = require('fs');
const path = require('path');

// ------------------------------------------------------------------ tela simulada (ui.*)
function criarUi(registro) {
  function Estilo(inicial) {
    const v = Object.assign({}, inicial || {});
    return {
      set: function (k, x) { if (k && typeof k === 'object') Object.assign(v, k); else v[k] = x; return this; },
      get: function (k) { return k === 'shown' ? v.shown !== false : v[k]; }
    };
  }
  function Widget(tipo, op) {
    op = op || {};
    const w = {
      tipo: tipo, _valor: op.value, _rotulo: op.label, _itens: (op.items || []).slice(), _url: null,
      _estilo: Estilo(op.style), _clique: [], _muda: [], _desab: !!op.disabled, _filhos: [], _placeholder: op.placeholder
    };
    if (typeof op.onClick === 'function') w._clique.push(op.onClick);
    if (typeof op.onChange === 'function') w._muda.push(op.onChange);
    w.getValue = function () { return w._valor; };
    w.setValue = function (v, disparar) {
      const mudou = v !== w._valor;
      w._valor = v;
      if (tipo === 'Label') registro.label(w);
      if (mudou && disparar !== false) w._muda.forEach(function (f) { f(v, w); });
      return w;
    };
    w.getLabel = function () { return w._rotulo; };
    w.setLabel = function (r) { w._rotulo = r; return w; };
    w.items = function () {
      return {
        reset: function (l) { w._itens = (l || []).slice(); return this; },
        getJsArray: function () { return w._itens.slice(); },
        length: function () { return w._itens.length; },
        add: function (x) { w._itens.push(x); return this; }
      };
    };
    w.style = function () { return w._estilo; };
    w.onClick = function (f) { w._clique.push(f); return f; };
    w.onChange = function (f) { w._muda.push(f); return f; };
    w.clicar = function () { w._clique.forEach(function (f) { f(w); }); };
    w.setDisabled = function (d) { w._desab = !!d; return w; };
    w.getDisabled = function () { return w._desab; };
    w.setUrl = function (u) { w._url = u; registro.url(w); return w; };
    w.getUrl = function () { return w._url; };
    w.setPlaceholder = function (p) { w._placeholder = p; return w; };
    w.add = function (x) { w._filhos.push(x); return w; };
    w.insert = function (i, x) { w._filhos.splice(i, 0, x); return w; };
    w.remove = function (x) { const i = w._filhos.indexOf(x); if (i !== -1) w._filhos.splice(i, 1); return w; };
    w.clear = function () { w._filhos = []; return w; };
    w.widgets = function () {
      return { reset: function (l) { w._filhos = (l || []).slice(); return this; }, add: function (x) { w._filhos.push(x); return this; },
               length: function () { return w._filhos.length; }, get: function (i) { return w._filhos[i]; } };
    };
    w.layers = function () {
      return { add: function (x) { w._filhos.push(x); return this; }, remove: function (x) { w.remove(x); return this; },
               length: function () { return w._filhos.length; }, reset: function () { w._filhos = []; return this; } };
    };
    // mapa e camadas: não desenham nada aqui
    ['setCenter', 'centerObject', 'setOptions', 'setControlVisibility', 'setZoom', 'setShown', 'setEeObject',
     'setVisParams', 'setName', 'setOpacity', 'setLayout', 'drawingTools', 'unlisten'].forEach(function (m) {
      w[m] = function () { return w; };
    });
    return w;
  }
  const Label = function (valor, estilo) {
    const w = Widget('Label', {value: valor === undefined ? '' : valor, style: estilo});
    registro.label(w);
    return w;
  };
  const Panel = function (a, b, c) {
    let op = {};
    if (a && !Array.isArray(a) && typeof a === 'object' && (a.widgets || a.layout || a.style)) op = a;
    else op = {widgets: a, layout: b, style: c};
    const w = Widget('Panel', {style: op.style});
    (op.widgets || []).forEach(function (x) { w.add(x); });
    return w;
  };
  Panel.Layout = {flow: function () { return {}; }, absolute: function () { return {}; }};
  const ui = {
    Label: Label,
    Panel: Panel,
    Button: function (op) { return Widget('Button', typeof op === 'string' ? {label: op} : op); },
    Select: function (op) { return Widget('Select', op); },
    Checkbox: function (op) { return Widget('Checkbox', op); },
    Textbox: function (op) { return Widget('Textbox', op); },
    SplitPanel: function () { return Widget('SplitPanel', {}); },
    Map: function () { return Widget('Map', {}); },
    root: Widget('Root', {})
  };
  ui.Map.Layer = function () { return Widget('Layer', {}); };
  return ui;
}

// ------------------------------------------------------------------ utilidades
const esperar = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
async function ate(cond, maxMs, passoMs) {
  const t0 = Date.now();
  while (Date.now() - t0 < maxMs) {
    if (cond()) return true;
    await esperar(passoMs || 500);
  }
  return cond();
}
function semAcento(t) { return String(t).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim(); }

// ------------------------------------------------------------------ execução
async function principal(ee, painelSrc, saida, casos, projeto, baixar) {
  const avisos = [];
  const reg = {
    pendentes: {}, prontos: {}, erros: {}, ultimo: Date.now(), caso: null,
    label: function (w) {
      const v = String(w._valor || '');
      let m = v.match(/^⏳ Gerando: (.+)\.\.\.$/);
      if (m) { reg.pendentes[m[1]] = true; reg.ultimo = Date.now(); return; }
      m = v.match(/^❌ Erro \((.+?)\): (.*)$/);
      if (m) { delete reg.pendentes[m[1]]; reg.erros[m[1]] = m[2]; reg.ultimo = Date.now(); return; }
      if (/^⚠️|^❌/.test(v) && reg.caso) { avisos.push(reg.caso + ': ' + v.slice(0, 200)); }
    },
    url: function (w) {
      const m = String(w._valor || '').match(/^⬇️ Baixar (.+)\.csv$/);
      if (m) { delete reg.pendentes[m[1]]; reg.prontos[m[1]] = w._url; reg.ultimo = Date.now(); }
    }
  };
  const ui = criarUi(reg);
  const alertas = [];
  const print = function () {
    const t = Array.prototype.map.call(arguments, function (x) { return typeof x === 'string' ? x : ''; }).join(' ').trim();
    if (t) {
      if (/^❌|^⚠️/.test(t)) alertas.push(t.slice(0, 300));
      if (process.env.K16_VERBOSO) console.log('   [painel] ' + t);
    }
  };
  // O painel roda inteiro, sem mudança, dentro desta função; "__k16" devolve as variáveis dele pelo nome.
  const executar = new Function('ee', 'ui', 'print', '__k16', painelSrc +
    '\n;__k16.ler = function (n) { return eval(n); };\n');
  const k16 = {};
  executar(ee, ui, print, k16);
  const P = function (n) { return k16.ler(n); };

  P('select_modo_processamento').setValue('Dados Climáticos Locais');
  await ate(function () { return P('APP').mascaraQualidadeOk !== null; }, 120000);
  if (P('APP').mascaraQualidadeOk !== true) {
    throw new Error('o painel não achou a máscara de qualidade (SAB_MASCARA_QUALIDADE): os CSV sairiam diferentes');
  }

  const resultados = [];
  for (const c of casos) {
    reg.caso = c.caso; reg.pendentes = {}; reg.prontos = {}; reg.erros = {}; alertas.length = 0;
    const t0 = Date.now();
    console.log('K16P ' + c.caso + ': preenchendo a tela');
    // ---- limpa a tela, como os botões "Limpar"
    P('btn_limpar_estados').clicar();
    P('btn_limpar_coords').clicar();
    P('check_usar_enso').setValue(false);
    P('select_enso').setValue('Todos os Anos');
    P('check_todas_vars').setValue(true);
    P('select_resolucao').setValue(c.res);
    // ---- local
    if (c.local.tipo === 'P') {
      P('select_abrangencia').setValue('Coordenadas (Lat / Lon)');
      P('select_formato_coord').setValue('Decimal (ex: -23.5500)');
      for (const p of c.local.pontos) {
        P('box_lat').setValue(String(p[0]));
        P('box_lon').setValue(String(p[1]));
        P('btn_add_coord').clicar();
      }
    } else {
      P('select_abrangencia').setValue('Estados / Municípios');
      P('check_filtrar_munis').setValue(false);
      const regioes = P('dicionario_regioes');
      for (const uf of c.local.uf) {
        const regiao = Object.keys(regioes).filter(function (r) { return regioes[r].indexOf(uf) !== -1; })[0];
        P('select_macro').setValue(regiao);
        P('select_estado').setValue(uf);
        P('btn_add_estado').clicar();
      }
      if (c.local.mun && c.local.mun.length) {
        P('check_filtrar_munis').setValue(true);       // carrega a lista de municípios do GAUL (no servidor)
        const sc = P('select_cidade');
        const ok = await ate(function () {
          return !sc.getDisabled() && sc._itens.length > 1;
        }, 180000);
        if (!ok) throw new Error(c.caso + ': a lista de municípios não carregou');
        for (const nome of c.local.mun) {
          const item = sc._itens.filter(function (x) { return semAcento(x) === semAcento(nome); })[0];
          if (!item) throw new Error(c.caso + ': município "' + nome + '" não está na lista do painel');
          sc.setValue(item);
          P('btn_add_cidade').clicar();
        }
      }
    }
    // ---- período, previsão, filtro ENSO
    P('box_inicio').setValue(c.ini);
    P('box_fim').setValue(c.fim);
    P('check_previsao').setValue(false);
    if (c.enso) {
      P('check_usar_enso').setValue(true);
      P('select_enso').setValue(c.enso);
    }
    // ---- PROCESSAR (aceita o aviso de "múltiplos municípios", como "Sim, continuar")
    const mapa = P('meuMapa');
    const antes = mapa._filhos.length;
    P('btn_processar').clicar();
    const novos = mapa._filhos.slice(antes);
    novos.forEach(function (painelAviso) {
      (painelAviso._filhos || []).forEach(function (linha) {
        (linha._filhos || []).forEach(function (b) { if (b.tipo === 'Button' && b._rotulo === 'Sim, continuar') b.clicar(); });
      });
    });
    reg.ultimo = Date.now();
    console.log('K16P ' + c.caso + ': processando (esperando ' + (c.esperados || []).length + ' link(s))');
    // ---- espera: todos os links esperados prontos, ou o painel parado (sem links pendentes) por 90 s
    const esperados = c.esperados || [];
    await ate(function () {
      const todos = esperados.length && esperados.every(function (n) { return reg.prontos[n] || reg.erros[n]; });
      const parado = !P('APP').processando && !Object.keys(reg.pendentes).length && Date.now() - reg.ultimo > 90000;
      return todos || parado;
    }, 20 * 60000, 1000);
    // ---- baixa os links (os mesmos que a pessoa clicaria)
    const pasta = path.join(saida, c.caso);
    fs.mkdirSync(pasta, {recursive: true});
    const arquivos = [];
    for (const nome of Object.keys(reg.prontos).sort()) {
      const destino = path.join(pasta, nome + '.csv');
      try {
        const bytes = await baixar(reg.prontos[nome]);
        fs.writeFileSync(destino, bytes);
        arquivos.push(nome);
      } catch (e) {
        reg.erros[nome] = 'download: ' + String(e.message || e).slice(0, 150);
      }
    }
    const r = {caso: c.caso, arquivos: arquivos, erros: reg.erros, faltando: esperados.filter(function (n) { return arquivos.indexOf(n) === -1; }),
               alertas: alertas.slice(0, 5), segundos: Math.round((Date.now() - t0) / 1000)};
    console.log('K16P_RESULTADO ' + JSON.stringify(r));
    resultados.push(r);
  }
  return {resultados: resultados, avisos: avisos};
}

async function baixarHttp(url) {
  const r = await fetch(url, {redirect: 'follow'});
  if (r.status !== 200) throw new Error('HTTP ' + r.status + ' ' + (await r.text()).slice(0, 120));
  return Buffer.from(await r.arrayBuffer());
}

function iniciarEe(ee, token, projeto) {
  return new Promise(function (ok, falha) {
    let seguiu = false;
    const seguir = function () {
      if (seguiu) return;
      seguiu = true;
      try { if (ee.data.setProject) ee.data.setProject(projeto); } catch (e) { /* versões antigas */ }
      ee.initialize(null, null, ok, function (e) { falha(new Error('ee.initialize: ' + e)); }, null, projeto);
    };
    try {
      ee.data.setAuthToken('', 'Bearer', token, 3600, [], seguir, false);
    } catch (e) {
      falha(new Error('ee.data.setAuthToken: ' + e));
      return;
    }
    setTimeout(seguir, 5000);   // versões que não chamam o callback quando não atualizam a biblioteca de login
  });
}

module.exports = {principal: principal, criarUi: criarUi};

if (require.main === module) {
  (async function () {
    const [painelArq, saida, casosArq, projeto] = process.argv.slice(2);
    const token = process.env.EE_TOKEN;
    if (!token) throw new Error('falta EE_TOKEN');
    const ee = require('@google/earthengine');
    await iniciarEe(ee, token, projeto || 'clima-492922');
    console.log('K16P Earth Engine iniciado (biblioteca JavaScript ' + (ee.apiclient && ee.apiclient.VERSION || '') + ')');
    const casos = JSON.parse(fs.readFileSync(casosArq, 'utf8'));
    await principal(ee, fs.readFileSync(painelArq, 'utf8'), saida, casos, projeto, baixarHttp);
    console.log('K16P_FIM');
    process.exit(0);
  })().catch(function (e) {
    console.log('K16P_ERRO ' + String(e && e.stack || e).slice(0, 600));
    process.exit(1);
  });
}
