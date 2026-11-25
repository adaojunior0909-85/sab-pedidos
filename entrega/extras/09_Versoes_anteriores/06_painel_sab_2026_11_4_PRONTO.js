// ============================================================
// PAINEL SAB (BRASIL / GLOBAL + PREVISÃO + ENSO)
// VERSÃO 2026.11.4 (18/11/2026): só o TEXTO de duas linhas do dicionário (Chuva_Efetiva_mm e Runoff_Superficial_mm):
//   o aviso de que, nos dias de 1961 a 2025, escoamento e chuva efetiva não batem dia a dia com a chuva (chuva
//   observada do BR-DWGD x escoamento do modelo ERA5-Land; auditoria K26). O mesmo texto do sab_pedido.py 2026.11.19.
//   Cálculos e CSV iguais aos da 2026.11.3 (K16 v6).
// VERSÃO 2026.11.3 (04/11/2026): só a caixa "Receber por e-mail" muda: o botão "Gerar o pedido" e o link de baixo viram
//   UM botão "ENVIAR O PEDIDO", que aparece quando os campos estão completos (o Earth Engine só envia por link clicado).
//   Mesmo endereço e mesmos campos do pedido; cálculos e CSV iguais aos da 2026.11.1 (K20 e K16 v4 valem).
// VERSÃO 2026.11.2 (04/11/2026): só a AUTORIA e o LINK OFICIAL no topo do painel (CFG.autoria e CFG.urlApp; app novo
//   adao-alves-rodrigues-junior-sab). Cálculos, CSV, e-mail e o link na hora são os da 2026.11.1 (K20 e K16 v4 valem).
// VERSÃO 2026.11.1 (03/11/2026): CORREÇÃO DE LEITURA (o banco não muda) decidida depois das auditorias K18 e K19:
//   nos pixels B (lagoas e estuários), os dias de 1961 a 2025 saem com o BR-DWGD no núcleo (chuva, Tmax, Tmin, UR,
//   VPD, ETo, radiação, vento); nos pixels C, a radiação desses dias fica limitada à de céu claro (FAO-56). O grampo
//   ET real <= ETo vem depois, como antes. Mesma conta no sab_pedido.py 2026.11.03 (K16 com o caso A6, Lagoa dos
//   Patos). Fora dos pixels B e C nada muda. CHANGELOG_06.md, seção 2026.11.1.
// VERSÃO 2026.10.7 (02/11/2026): só os TEXTOS do bloco El Niño/La Niña mudam (agora / próximos 3 meses / avisos;
//   explicação longa num botão "Como ler"). Cálculos, CSV e o link na hora são os mesmos (K16 continua valendo).
// VERSÃO 2026.10.6 (01/11/2026): só a caixa "Receber por e-mail" muda (formato CSV/Excel, aviso de spam, até 6
//   estados). O cálculo e os CSV do link na hora são os da 2026.10.4/2026.10.5 (K16). CHANGELOG_06.md, seção 2026.10.6.
// VERSÃO 2026.10.4 (20/10/2026), sobre a 2026.10.3a; REVISÃO FINAL DE 22/10/2026 (ENSO explicado para leigos,
//   downloads do ENSO por link, colunas ENSO nos CSVs do item B; CHANGELOG_REVISAO_K9A.md, seção 9)
// REVISÃO DE 22/10/2026, 18h30 (CHANGELOG_REVISAO_K9A.md, seção 17): números dos CSV de clima com PONTO
//   decimal (antes texto com vírgula), mesmas casas; 1 arquivo por ano; formatação de cada linha mais
//   leve que a da 2026.10.2 (o ano inteiro do Paraná deu 503 com o arredondamento das 17h).
// MUDANÇAS V4 (20/10/2026): cada trecho alterado ou novo está marcado com // [V4 <ID>]
//   - [V4 F1/M06-01] GAUL filtrado por ADM0_NAME == 'Brazil' (estados e municípios). Sem o filtro,
//     Amazonas trazia Colômbia, Peru e Venezuela; Distrito Federal, o México; e "Pará" (sem acento,
//     "Para") o Suriname (auditoria J3)
//   - [V4 F2/M06-03] a grade não é mais cortada em silêncio: o número de pares pixel × polígono
//     entra na avaliação inicial e, acima de 25.000, o processamento para com aviso na tela
//   - [V4 Q1] máscara de qualidade SAB_MASCARA_QUALIDADE: os pixels de classe 4 (sem BR-DWGD, centro
//     fora do Brasil) saem dos pontos, e a coluna diária Qualidade_Pixel traz A, B ou C. Sem o
//     asset (antes da etapa 1), o painel avisa e segue sem filtro, com a coluna vazia
//   - [V4 F4/M06-04] CSV mensal: colunas N_Dias, Dias_no_Mes e Mes_Completo
//   - [V4 F8/M06-05] CSV diário: coluna Janela_Chuva_UTC (12-12 UTC no BR-DWGD, 00-24 UTC no ERA5/GFS)
//   - [V4 Conf] CSV diário: coluna Confianca_Prazo (propriedade gravada pelo motor V1.5 nos dias GFS)
//   - [V4 F6/M06-06] ENSO: a sequência final de mesmo sinal com menos de 5 estações, cortada pelo fim
//     da série, vira 'Indefinida' (antes 'Neutro') e fica fora de todos os cenários; o Console
//     informa quantos meses ficaram 'Indefinida' ou 'Sem_Dado'
//   - [V4 M06-15] continuidade do RONI impressa como true/false; se false, a simulação não é mostrada
//   - [V4 IC] IC exato de 95% (Clopper–Pearson, k de 10) ao lado de cada probabilidade dos análogos
//   - [V4 M06-23] valor de 'versao' desconhecido vira 'Desconhecido' (antes 'Historico_Observado')
//   - [V4 F9/M06-11] dicionário de variáveis: ressalvas (escoamento, chuva efetiva, transpiração,
//     dias GFS, Lat/Lon) e colunas novas
//   - [V4 versão] CFG.versao = '2026.10.4'
//   - [V4 revisão B-05] colunas novas no FIM dos CSVs: as 30 colunas antigas mantêm as posições
//   - [V4 revisão B-08] dicionário: Versao_Algoritmo descreve a V1.5
//   - [V4 revisão B-09] camada 'Área de Cobertura' sem os pixels de classe 4, como os pontos de extração
//   - [V4 revisão B-10] alerta da máscara também cita o compartilhamento (App publicado)
// REVISÃO 2026.10.3a (19/10/2026), sobre a 2026.10.3, sem mudar nenhum cálculo:
//   - restaurada a chamada final atualizarVisibilidadeEspacial(...) que existia na 2026.10.2
//   - CSV: com a previsão ligada, a data final em texto também avança 15 dias (virada de ano)
//   - camada 'Pontos informados pelo usuário' volta a ser desenhada no modo Coordenadas
//   - CSV diário: umidade do solo com 3 casas decimais (antes 2)
// ÚLTIMA ATUALIZAÇÃO (2026.10.3): COMPATÍVEL COM O MOTOR V1.4 E COM O RONI OFICIAL DO CPC
//   - ENSO: série oficial do CPC (ERSSTv6) lida do asset RONI_CPC_v6; o OISST só estima as
//     estações que o CPC ainda não publicou (marcadas como Estimativa_OISST)
//   - ENSO/OISST: geometrias planas, terra mascarada (o fallback -999 contaminava a média
//     tropical), média ponderada por área na grade nativa, só meses completos, só trimestres
//     com 3 meses, fator de variância em 1991-2020
//   - ENSO: preditor por análogos da mesma estação com o valor 3 meses à frente (antes usava o
//     próprio valor do análogo); mostra estação atual, fonte e anos análogos
//   - ENSO: filtro histórico não descarta mais dias do SAB (join externo) e lê a propriedade RONI
//     também em 1950-1980; categorias de El Niño/La Niña exigem episódio
//   - Dicionário: temperatura de superfície (skin), camadas do solo e UR dos dias provisórios
// ATUALIZAÇÃO ANTERIOR (2026.10.2): COMPATÍVEL COM O MOTOR V1.3
//   - Coluna Versao_Algoritmo no CSV: versão do motor que gravou cada dia (V1.0 no histórico,
//     V1.3 em 2026 depois da troca); no mensal, as versões presentes no mês
//   - ENSO: subcategoria "El Niño Fraco" passa a usar o ONI futuro dos análogos, como as demais
//   - Dica de período e dicionário atualizados (2026 provisório; ETo por Penman-Monteith)
// ATUALIZAÇÃO ANTERIOR: CORREÇÃO DE LEITURA (SOLO/ESCOAMENTO V1.0) E PREVISÃO LIDA DO BANCO
//   - Umidade do solo e escoamento dos dias da V1.0 corrigidos na leitura (banco intacto)
//   - Previsão GFS lida do banco SAB (gerada pelo motor Python); previsão interna removida
//   - Coluna Tipo_Dado indica a origem real de cada dia
//   - Dicionário: vento a 2 m, escoamento subsuperficial e Tipo_Dado
// ============================================================

// ============================================================
// MODULO 1: INICIALIZACAO E ESTILO BASE DO MAPA
// ============================================================
ui.root.clear();
var meuMapa = ui.Map();

// Centraliza o mapa inicialmente no Brasil (Longitude, Latitude, Zoom)
meuMapa.setCenter(-51.9253, -14.2350, 4);

var estiloLimpo = [
  { featureType: 'all', elementType: 'labels', stylers: [{ visibility: 'off' }] },
  { featureType: 'road', stylers: [{ visibility: 'off' }] },
  { featureType: 'poi', stylers: [{ visibility: 'off' }] },
  { featureType: 'transit', stylers: [{ visibility: 'off' }] }
];

// ============================================================
// MODULO 2: PARAMETROS GLOBAIS E VARIAVEIS DE ESTADO (CFG E APP)
// ============================================================
var CFG = {
  versao: '2026.11.4', // [2026.11.4] aviso do escoamento no dicionário; [2026.11.3] envio por e-mail num clique; [2026.11.2] autoria e link oficial no topo; [2026.11.1] correção de leitura dos pixels B e da radiação dos pixels C ([2026.10.7] textos ENSO)
  // [2026.10.5] Envio por e-mail (validações K13 a K15): o link na hora aguenta ~100 mil linhas por arquivo; acima
  // disso, ou com arquivos demais, o painel mostra só a opção "Receber por e-mail".
  limiteLinhasLink: 100000,
  limiteArquivosLink: 20,
  // Endereço do App da Web do Apps Script dos pedidos (Implantar > Nova implantação > App da Web), terminado em /exec.
  // Vazio: o painel não oferece o envio por e-mail.
  urlPedidoEmail: 'https://script.google.com/macros/s/AKfycbzNDVBp7HJgZo1xzi6BlhNUNJuTG9EwW_eYfhxSpTBu7XaB__MF-btlSTytz2mphPVC/exec',
  // [2026.11.2] autoria e endereço oficial do app, mostrados no topo do painel
  autoria: 'Desenvolvido por Adão Alves Rodrigues Junior (UTFPR, Pato Branco)',
  urlApp: 'https://clima-492922.projects.earthengine.app/view/adao-alves-rodrigues-junior-sab',
  limitePontosGrade: 25000, // [V4 F2/M06-03] máximo de pares pixel × polígono (acima disso o processamento para)
  escalaPonto: 1000,
  escalaArea: 11132, 
  escalaExportacaoRaster: 11132, 
  bufferPontoMetros: 100,
  bufferInspectorMetros: 500,
  zoomPonto: 10,
  zoomArea: 7,
  limiarFrio: 4,
  limiarGeada: 2, 
  limiarCalor: 35,
  limiarDiaSeco: 1,
  tBaseInferiorPadrao: 10,
  tBaseSuperiorPadrao: 30,
  cloudCoverHLS: 40,
  anoMapBiomasMin: 1985,
  anoMapBiomasMax: 2024,
  periodoHistoricoInicio: '1961-01-01', 
  periodoHistoricoFim: '2025-12-31',    
  classesMapBiomasProdutivas: [9, 15, 20, 21, 35, 39, 40, 41, 46, 47, 48, 62],
  pastaDrive: 'SAB',
  assets: {
    estados: 'FAO/GAUL/2015/level1',
    municipios: 'FAO/GAUL/2015/level2',
    bancoDadosSAB: 'projects/clima-492922/assets/SAB_V1',
    era5Daily: 'ECMWF/ERA5_LAND/DAILY_AGGR',
    hlss30: 'NASA/HLS/HLSS30/v002',
    hlsl30: 'NASA/HLS/HLSL30/v002',
    mapbiomas: 'projects/mapbiomas-public/assets/brazil/lulc/v1',
    gfs: 'NOAA/GFS0P25',
    // [V4 Q1] máscara de qualidade (etapa 1), banda 'classe': 1 = A, 2 = B, 3 = C com centro no
    // Brasil, 4 = C com centro fora (borda, excluída dos pontos)
    mascaraQualidade: 'projects/clima-492922/assets/SAB_MASCARA_QUALIDADE',
    roniPassado: 'projects/clima-492922/assets/RONI_CPC_v6' // RONI oficial do CPC (ERSSTv6), gerado pelo script de auditoria
  },
  bandasSAB: [
    'pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd', 
    'rs', 'u2', 'tsolo_C', 'tfolha_C', 'transpiracao_mm', 
    'runoff_sup_mm', 'runoff_sub_mm', 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3'
  ],
  resolucoes: {
    sab: 11132,     
    hls: 30
  },
  paletas: {
    chuvaAnomalia: ['#8c510a', '#d8b365', '#f6e8c3', '#f5f5f5', '#c7eae5', '#5ab4ac', '#01665e'], 
    tempAnomalia: ['#313695', '#4575b4', '#74add1', '#e0f3f8', '#fee090', '#f46d43', '#d73027', '#a50026'], 
    chuvaTotal: ['#ffffd9', '#c7e9b4', '#41b6c4', '#1d91c0', '#225ea8', '#0c2c84'], 
    tminMedia: ['#081d58', '#253494', '#225ea8', '#1d91c0', '#41b6c4', '#c7e9b4'], 
    tmaxMedia: ['#fed976', '#feb24c', '#fd8d3c', '#f03b20', '#bd0026', '#800026'], 
    diasSecos: ['#ffffcc', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'], 
    diasFrios: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695', '#54278f'], 
    diasCalor: ['#ffffb2', '#fecc5c', '#fd8d3c', '#e31a1c', '#800026', '#4a1486'], 
    amplitudeTermica: ['#fee0d2', '#fc9272', '#de2d26', '#a50f15', '#67000d'], 
    gdd: ['#c2e699', '#78c679', '#31a354', '#006837', '#003e21'], 
    geada: ['#a6bddb', '#3690c0', '#0570b0', '#045a8d', '#023858'], 
    umidadeSolo: ['#d73027', '#f46d43', '#fdae61', '#abd9e9', '#74add1', '#4575b4'], 
    ndvi: ['#a50026', '#d73027', '#f46d43', '#d9f0a3', '#addd8e', '#41ab5d', '#006837'], 
    mascaraProdutiva: ['#2e7d32']
  }
};

var APP = {
  processando: false,
  startTime: null, 
  camadaInspectorAtual: null,
  layersByKey: {},
  layerOrder: [],
  regiaoGeom: null,
  regiaoFC: null,
  escalaAtual: CFG.escalaArea,
  abrangenciaAtual: null,
  colecaoClimaticaAtual: null,
  modoCaptura: false
};
// [V4 Q1] Disponibilidade da máscara de qualidade: null = verificação em andamento,
// true = asset com a banda 'classe', false = ausente (a verificação roda uma vez, ao abrir o painel)
APP.mascaraQualidadeOk = null;
// [2026.11.1] true = o BR-DWGD pode ser lido (correção dos pixels B ligada); false = segue sem a correção, com aviso
APP.brdwgdOk = null;

// ============================================================
// MODULO 3: FUNCOES UTILITARIAS DE LOG E ALERTA (UI/UX)
// ============================================================
function logInfo(msg, obj) { print('ℹ️ ' + msg, obj || ''); }
function logWarn(msg, obj) { print('⚠️ ' + msg, obj || ''); }
function logError(msg, obj) { print('❌ ' + msg, obj || ''); }
function logStep(msg) { print('➡️ ' + msg); }

function mostrarAlertaTela(mensagem) {
  var painelAlerta = ui.Panel({
    layout: ui.Panel.Layout.flow('vertical'),
    style: { position: 'top-center', padding: '15px', backgroundColor: '#ffffff', border: '3px solid #d32f2f', width: '320px' }
  });
  var titulo = ui.Label('⚠️ AVISO DO SISTEMA', { fontWeight: 'bold', color: '#d32f2f', fontSize: '14px', textAlign: 'center' });
  var texto = ui.Label(mensagem, { color: '#333333', fontSize: '13px', margin: '10px 0', textAlign: 'justify' });
  var btnFechar = ui.Button({
    label: 'OK, Entendi',
    onClick: function() { meuMapa.remove(painelAlerta); },
    style: { margin: '5px auto' }
  });
  
  painelAlerta.add(titulo); 
  painelAlerta.add(texto); 
  painelAlerta.add(btnFechar);
  
  meuMapa.add(painelAlerta);
}

function mostrarConfirmacaoTela(mensagem, callbackContinuar) {
  var painelAlerta = ui.Panel({
    layout: ui.Panel.Layout.flow('vertical'),
    style: { position: 'top-center', padding: '15px', backgroundColor: '#ffffff', border: '3px solid #f57c00', width: '350px' }
  });
  var titulo = ui.Label('⚠️ ALERTA DE PERFORMANCE', { fontWeight: 'bold', color: '#f57c00', fontSize: '14px', textAlign: 'center' });
  var texto = ui.Label(mensagem, { color: '#333333', fontSize: '13px', margin: '10px 0', textAlign: 'justify' });
  
  var painelBotoes = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal'), style: { margin: '5px auto' } });
  
  var btnContinuar = ui.Button({
    label: 'Sim, continuar',
    onClick: function() { 
      meuMapa.remove(painelAlerta); 
      callbackContinuar(); 
    },
    style: { color: '#d32f2f', margin: '0 10px' }
  });
  
  var btnCancelar = ui.Button({
    label: 'Não, vou reduzir',
    onClick: function() { 
      meuMapa.remove(painelAlerta); 
      liberarBotaoProcessamento();
    },
    style: { color: '#2e7d32', margin: '0 10px' }
  });
  
  painelBotoes.add(btnCancelar);
  painelBotoes.add(btnContinuar);
  
  painelAlerta.add(titulo); 
  painelAlerta.add(texto); 
  painelAlerta.add(painelBotoes);
  
  meuMapa.add(painelAlerta);
}

// ============================================================
// MODULO 4: DICIONARIOS DE REGIOES E CULTURAS
// ============================================================
var dicionario_regioes = {
  'Norte': ['Acre', 'Amapá', 'Amazonas', 'Pará', 'Rondônia', 'Roraima', 'Tocantins'],
  'Nordeste': ['Alagoas', 'Bahia', 'Ceará', 'Maranhão', 'Paraíba', 'Pernambuco', 'Piauí', 'Rio Grande do Norte', 'Sergipe'],
  'Centro-Oeste': ['Distrito Federal', 'Goiás', 'Mato Grosso', 'Mato Grosso do Sul'],
  'Sudeste': ['Espírito Santo', 'Minas Gerais', 'Rio de Janeiro', 'São Paulo'],
  'Sul': ['Paraná', 'Rio Grande do Sul', 'Santa Catarina']
};

// [V4 F1/M06-01] Só o Brasil: o GAUL é mundial e a busca é por nome sem acento (J3: Amazonas na
// Colômbia, no Peru e na Venezuela; Distrito Federal no México; "Para" no Suriname). Todas as
// seleções, a lista de municípios do passo 3, os contornos e o centerObject partem destas duas.
var estados = ee.FeatureCollection(CFG.assets.estados).filter(ee.Filter.eq('ADM0_NAME', 'Brazil'));
var municipios = ee.FeatureCollection(CFG.assets.municipios).filter(ee.Filter.eq('ADM0_NAME', 'Brazil'));

// ============================================================
// MODULO 5: PREPARACAO INICIAL E VISUAL DO MAPA
// ============================================================
function aplicarEstiloBaseMapa() {
  meuMapa.setOptions('HYBRID', { 'Mapa Limpo': estiloLimpo }, ['HYBRID', 'ROADMAP', 'SATELLITE', 'Mapa Limpo']);
}
aplicarEstiloBaseMapa();
meuMapa.setControlVisibility({ all: false, zoomControl: true, layerList: false, mapTypeControl: true, scaleControl: true });
meuMapa.style().set('cursor', 'hand');

// ============================================================
// MODULO 6: FUNCOES DE FORMATACAO E TRATAMENTO DE TEXTOS E DATAS
// ============================================================
function removerAcentos(texto) {
  if (!texto) return '';
  var comAcento = 'ÁÀÃÂÄÉÈÊËÍÌÎÏÓÒÕÔÖÚÙÛÜÇÑáàãâäéèêëíìîïóòõôöúùûüçñ';
  var semAcento = 'AAAAAEEEEIIIIOOOOOUUUUCNaaaaaeeeeiiiiooooouuuucn';
  var saida = '';
  texto = String(texto);
  for (var i = 0; i < texto.length; i++) {
    var idx = comAcento.indexOf(texto.charAt(i));
    saida += idx > -1 ? semAcento.charAt(idx) : texto.charAt(i);
  }
  return saida;
}

function formatarTextoBusca(str) {
  if (!str) return [];
  var bruto = String(str).trim();
  var sem = removerAcentos(bruto);
  var titulo = sem.toLowerCase().split(' ').map(function(w) {
    if (!w) return '';
    return w.charAt(0).toUpperCase() + w.slice(1);
  }).join(' ').trim();
  return [bruto, sem, titulo, bruto.toUpperCase(), sem.toUpperCase(), titulo.toUpperCase()];
}

function listaVariacoesBusca(lista) {
  var out = [];
  (lista || []).forEach(function(item) { out = out.concat(formatarTextoBusca(item)); });
  return out.filter(function(item, pos) { return out.indexOf(item) === pos; });
}

function numeroSeguro(valor, fallback) {
  var n = parseFloat(String(valor).replace(',', '.'));
  return isNaN(n) ? fallback : n;
}

function limitarValor(valor, min, max) {
  return Math.max(min, Math.min(max, valor));
}

function aplicarMascaraData(texto, widget) {
  var num = String(texto || '').replace(/\D/g, '');
  if (num.length > 8) num = num.substring(0, 8);
  var formatado = num;
  if (num.length >= 5) formatado = num.substring(0, 2) + '/' + num.substring(2, 4) + '/' + num.substring(4, 8);
  else if (num.length >= 3) formatado = num.substring(0, 2) + '/' + num.substring(2, 4);
  if (widget && texto !== formatado) widget.setValue(formatado);
  return formatado;
}

function converterDataParaISO(dataBR) {
  if (!dataBR) return null;
  var partes = String(dataBR).split('/');
  if (partes.length !== 3) return null;
  return partes[2] + '-' + partes[1] + '-' + partes[0];
}

function dataEhValida(dataBR) {
  if (!dataBR || dataBR.length !== 10) return false;
  var partes = dataBR.split('/');
  var dia = parseInt(partes[0], 10), mes = parseInt(partes[1], 10), ano = parseInt(partes[2], 10);
  var dataTeste = new Date(ano, mes - 1, dia); 
  return (dataTeste.getFullYear() === ano && dataTeste.getMonth() === (mes - 1) && dataTeste.getDate() === dia);
}

function escalaPorAbrangencia(tipo) { return (tipo && tipo.indexOf('Coordenadas') !== -1) ? CFG.escalaPonto : CFG.escalaArea; }
function zoomPorAbrangencia(tipo) { return (tipo && tipo.indexOf('Coordenadas') !== -1) ? CFG.zoomPonto : CFG.zoomArea; }

function converterDMSparaDecimal(str) {
  str = String(str).trim().toUpperCase().replace(',', '.');
  var match = str.match(/([+-]?\d+)[^\d]+(\d+)[^\d]+([\d.]+)[^A-Z]*([NSWE]?)/);
  if (!match) return null;
  var deg = Math.abs(parseFloat(match[1]));
  var min = parseFloat(match[2]);
  var sec = parseFloat(match[3]);
  var dir = match[4];
  var dec = deg + (min / 60) + (sec / 3600);
  if (dir === 'S' || dir === 'W' || str.indexOf('-') === 0) dec = -dec;
  return dec;
}

function verificarECorrigirCoordsTexto(txtLat, txtLon, formato) {
  if (!txtLat || !txtLon) return null;
  var lat, lon;
  if (formato.indexOf('Graus') !== -1) {
    lat = converterDMSparaDecimal(txtLat);
    lon = converterDMSparaDecimal(txtLon);
  } else {
    lat = numeroSeguro(txtLat, null);
    lon = numeroSeguro(txtLon, null);
  }

  if (lat === null || lon === null) return null;
  
  if (lat < -34.0 || (lon > -34.0 && lon < 6.0)) { 
    var temp = lat; lat = lon; lon = temp; 
  }
  
  var foraDoBrasil = (lat > 6.0 || lat < -35.0 || lon > -34.0 || lon < -75.0);
  
  if (foraDoBrasil) {
    mostrarAlertaTela('⚠️ LOCALIZAÇÃO INVÁLIDA: A Base Climática Oficial possui cálculos exclusivos para o território brasileiro. As coordenadas informadas estão fora do polígono de cobertura.');
    return null;
  }

  return { lat: lat, lon: lon };
}

// ============================================================
// MODULO 7: GERENCIAMENTO DE CAMADAS DO MAPA (REGISTRO E LIMPEZA)
// ============================================================
var painel_camadas_scroll = ui.Panel({ layout: ui.Panel.Layout.flow('vertical'), style: { height: '360px', stretch: 'vertical' } });
var painel_camadas = ui.Panel({ layout: ui.Panel.Layout.flow('vertical'), style: { width: '340px', position: 'top-right', padding: '8px', backgroundColor: 'rgba(255,255,255,0.96)' } });

function resetPainelCamadas() {
  painel_camadas.clear();
  painel_camadas.add(ui.Label('Camadas do Mapa', {fontWeight: 'bold', fontSize: '15px', color: '#1d70b8'}));
  painel_camadas.add(ui.Label('Ative apenas o que quiser visualizar.', {fontSize: '11px', color: '#555'}));
  painel_camadas_scroll.clear();
  painel_camadas.add(painel_camadas_scroll);
}

// ============================================================
// MODULO 7.1: LEGENDA FLUTUANTE EXPLICATIVA DE CORES
// ============================================================
var painel_legenda_cores = ui.Panel({
  style: {
    position: 'bottom-right',
    padding: '10px 15px',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    border: '1px solid #cccccc'
  }
});
painel_legenda_cores.add(ui.Label('🎨 Interpretação Visual', {fontWeight: 'bold', fontSize: '12px', margin: '0 0 6px 0', color: '#333333'}));
painel_legenda_cores.add(ui.Label('• Cores de base (branco, azul claro, etc.) indicam valor ZERO.', {fontSize: '11px', margin: '0 0 4px 0', color: '#555555'}));
painel_legenda_cores.add(ui.Label('• Mapas uniformes significam ausência do evento no período.', {fontSize: '11px', margin: '0', color: '#555555'}));

meuMapa.add(painel_camadas);
meuMapa.add(painel_legenda_cores);
resetPainelCamadas();

function limparMapaParaNovoProcessamento() {
  logStep('Limpando mapa para novo processamento...');
  meuMapa.clear();
  APP.layersByKey = {};
  APP.layerOrder = [];
  aplicarEstiloBaseMapa();
  meuMapa.setControlVisibility({ all: false, zoomControl: true, layerList: false, mapTypeControl: true, scaleControl: true });
  meuMapa.add(painel_camadas);
  meuMapa.add(painel_legenda_cores);
  resetPainelCamadas();
  
  if (typeof painel_downloads_app !== 'undefined') {
    painel_downloads_app.clear();
    painel_downloads_app.add(ui.Label('Arquivos Prontos para Download:', {fontWeight: 'bold', color: '#2e7d32', fontSize: '14px'}));
    painel_downloads_app.style().set('shown', false);
  }
  if (typeof painel_pedido_email !== 'undefined') {   // [2026.10.5]
    painel_pedido_email.style().set('shown', false);
    APP.pedidoEmail = null;
  }
}

function registrarCamada(chave, grupo, nome, objeto, visParams, visivel) {
  if (APP.layersByKey[chave]) {
    try { meuMapa.layers().remove(APP.layersByKey[chave].layer); } catch (e) {}
  }
  var layer = ui.Map.Layer(objeto, visParams || {}, nome, !!visivel);
  APP.layersByKey[chave] = { layer: layer, grupo: grupo, nome: nome, visivel: !!visivel };
  if (APP.layerOrder.indexOf(chave) === -1) APP.layerOrder.push(chave);
  meuMapa.layers().add(layer);
}

// ============================================================
// MODULO 8: INFRAESTRUTURA DE ESTACOES E MALHA AMOSTRAL
// ============================================================
function adicionarCamadasInfraestrutura(regiao_geom, escalaAnalise, pontosCoordsGeom) {
  if (pontosCoordsGeom) {
    registrarCamada(
      'pontos_selecionados', 'Infraestrutura e pontos', 'Pontos informados pelo usuário',
      ee.FeatureCollection(ee.Geometry.MultiPoint(pontosCoordsGeom).geometries().map(function(g) { return ee.Feature(ee.Geometry(g)); })).style({ color: '#d7301f', pointSize: 5, pointShape: 'circle', width: 1, fillColor: '#ff0000' }), {}, true
    );
  }

  if (APP.abrangenciaAtual && APP.abrangenciaAtual.indexOf('Coordenada') === -1) {
    var malha = ee.Image.pixelLonLat().sample({ region: regiao_geom, scale: escalaAnalise, geometries: true });
    registrarCamada('malha_grid', 'Infraestrutura e pontos', 'GRID de amostragem', ee.FeatureCollection(malha).style({ color: '#4d4d4d', pointSize: 2, pointShape: 'circle', width: 1, fillColor: '#b39ddb' }), {}, false);
  }
}

function obterGridAmostragem(regiao_geom, escala) {
  if (!regiao_geom) return ee.FeatureCollection([]);
  return ee.Image.pixelLonLat().sample({region: regiao_geom, scale: escala || CFG.escalaArea, geometries: true}).map(function(f) { return ee.Feature(f.geometry(), {'id_grid': 1}); });
}

function atualizarOverlaysIndependentes() {
  var regiao = APP.regiaoGeom || null;
  if (APP.layersByKey['malha_grid']) {
    if (regiao && APP.abrangenciaAtual && APP.abrangenciaAtual.indexOf('Coordenada') === -1) {
      var escalaGrid = APP.escalaAtual || CFG.escalaArea;
      var fcGrid = obterGridAmostragem(regiao, escalaGrid);
      APP.layersByKey['malha_grid'].layer.setEeObject(fcGrid.style({color: '#4d4d4d', pointSize: 2, pointShape: 'circle', width: 1, fillColor: '#b39ddb'}));
      APP.layersByKey['malha_grid'].placeholder = false;
      APP.layersByKey['malha_grid'].realDisponivel = true;
    } else {
      APP.layersByKey['malha_grid'].layer.setEeObject(ee.FeatureCollection([]).style({color: '#4d4d4d', pointSize: 2, pointShape: 'circle', width: 1, fillColor: '#b39ddb'}));
      APP.layersByKey['malha_grid'].placeholder = true;
      APP.layersByKey['malha_grid'].realDisponivel = false;
    }
  }
}

// ============================================================
// MODULO 9: LOGICA DO PAINEL DE CAMADAS (CHECKBOXES E GRUPOS)
// ============================================================
function garantirCamadasOpcionaisSempreVisiveisNoPainel(regiao_geom) {
  var geomBase = regiao_geom || ee.Geometry.Point([-53.5, -24.5]).buffer(1000);

  if (!APP.layersByKey['malha_grid']) {
    registrarCamada('malha_grid', 'Infraestrutura e pontos', 'GRID de amostragem', ee.FeatureCollection([]).style({color: '#4d4d4d', pointSize: 2, pointShape: 'circle', width: 1, fillColor: '#b39ddb'}), {}, false);
  }
  APP.layersByKey['malha_grid'].placeholder = regiao_geom ? false : true;
  APP.layersByKey['malha_grid'].realDisponivel = regiao_geom ? true : false;

  if (!APP.layersByKey['cobertura_pixels']) {
    registrarCamada('cobertura_pixels', 'Infraestrutura e pontos', 'Área de Cobertura', ee.FeatureCollection([]).style({color: 'FFA500', fillColor: 'FFA50044', width: 2}), {}, false);
  }
  APP.layersByKey['cobertura_pixels'].placeholder = regiao_geom ? false : true;
  APP.layersByKey['cobertura_pixels'].realDisponivel = regiao_geom ? true : false;

  atualizarOverlaysIndependentes();
}

function construirPainelCamadas() {
  resetPainelCamadas();
  var ordemGrupos = ['Referência', 'Infraestrutura e pontos', 'Clima', 'Extremos', 'Anomalias', 'Vegetação e solo'];
  
  var ordemItens = {
    'Referência': ['limites_estaduais', 'area_foco', 'area_expandida'],
    'Infraestrutura e pontos': ['malha_grid', 'pontos_selecionados', 'cobertura_pixels'], 
    'Clima': ['chuva_total', 'tmin_media', 'tmax_media', 'amp_termica', 'vento_media', 'rs_media', 'tsolo_media', 'tfolha_media', 'chuva_efetiva_total'],
    'Extremos': ['dias_secos', 'dias_frios', 'dias_calor', 'deficit_hidrico', 'vpd_media'],
    'Vegetação e solo': ['umidade_solo_5', 'umidade_solo_100', 'et_real_total', 'transpiracao_total']
  };

  var chavesUnicas = [];
  APP.layerOrder.forEach(function(k) { if (chavesUnicas.indexOf(k) === -1) chavesUnicas.push(k); });

  ordemGrupos.forEach(function(grupoNome) {
    var itensGrupo = chavesUnicas.filter(function(k) { return APP.layersByKey[k] && APP.layersByKey[k].grupo === grupoNome; });
    if (itensGrupo.length === 0) return;

    var ordem = ordemItens[grupoNome] || [];
    itensGrupo.sort(function(a, b) {
      var ia = ordem.indexOf(a); var ib = ordem.indexOf(b);
      ia = ia === -1 ? 999 : ia; ib = ib === -1 ? 999 : ib;
      return ia - ib;
    });

    painel_camadas_scroll.add(ui.Label(grupoNome, {fontWeight: 'bold', fontSize: '13px', margin: '10px 0 6px 0', color: '#1f1f1f'}));

    itensGrupo.forEach(function(k) {
      var item = APP.layersByKey[k];
      var valorInicial = item.visivel === true;
      if (['limites_estaduais'].indexOf(k) !== -1) valorInicial = true;

      var cb = ui.Checkbox({ label: item.nome, value: valorInicial, style: {margin: '0 0 4px 0', fontSize: '12px'} });
      cb.onChange(function(v) {
        item.layer.setShown(v);
        APP.layersByKey[k].visivel = v;
      });
      item.layer.setShown(valorInicial);
      APP.layersByKey[k].visivel = valorInicial;
      painel_camadas_scroll.add(cb);
    });
  });
}

// ============================================================
// MODULO 10: CONSTRUCAO DA INTERFACE DE USUARIO (PAINEL LATERAL)
// ============================================================
var painel = ui.Panel({ style: { width: '400px', padding: '15px' } });
painel.add(ui.Label('SAB Clima', {fontWeight: 'bold', fontSize: '20px', color: '#1d70b8'}));
// [2026.11.2] autoria e link oficial
painel.add(ui.Label(CFG.autoria, {fontSize: '11px', color: '#555555', margin: '0 8px 2px 8px'}));
painel.add(ui.Label('🔗 Link oficial do painel', {fontSize: '11px', color: '#1d70b8', margin: '0 8px 12px 8px'}, CFG.urlApp));

painel.add(ui.Label('Modo de Operação do Sistema:', {fontWeight: 'bold', color: '#b30000'}));

var select_modo_processamento = ui.Select({
  items: [
    '-- Selecione o Modo de Operação --',
    'Dados Climáticos Locais'
  ],
  value: '-- Selecione o Modo de Operação --',
  style: {width: '280px', color: '#b30000', fontWeight: 'bold'}
});
painel.add(select_modo_processamento);
var label_explicacao_modo = ui.Label('Selecione a extração rápida de dados locais.', {fontSize: '10px', color: '#555555', margin: '0 0 15px 8px'});
painel.add(label_explicacao_modo);

var bloco_resolucao = ui.Panel({ style: { shown: false } });
bloco_resolucao.add(ui.Label('Resolução Desejada:', {fontWeight: 'bold'}));
var select_resolucao = ui.Select({ items: ['Diária', 'Mensal'], value: 'Diária', style: {width: '280px'} });
bloco_resolucao.add(select_resolucao);
painel.add(bloco_resolucao);

var painel_fonte = ui.Panel({ style: { shown: false } });
painel_fonte.add(ui.Label('Banco de Dados:', {fontWeight: 'bold'}));
var select_fonte = ui.Select({ 
  items: ['Base Climática Oficial (Histórico + Previsão)'], 
  value: 'Base Climática Oficial (Histórico + Previsão)', 
  style: {width: '280px'} 
});
var label_dica_data = ui.Label('', {fontSize: '11px', color: '#d73027', margin: '0px 0px 10px 15px'});
painel_fonte.add(select_fonte);
painel_fonte.add(label_dica_data);
painel.add(painel_fonte);

var bloco_espacial = ui.Panel({ style: { shown: false } });
bloco_espacial.add(ui.Label('Seleção Espacial:', {fontWeight: 'bold'}));
var painel_espacial = ui.Panel({ style: { border: '1px solid #cccccc', padding: '8px', margin: '5px 0px' } });
bloco_espacial.add(painel_espacial);
painel.add(bloco_espacial);

painel_espacial.add(ui.Label('Nível de Análise:', {fontSize: '12px', margin: '0 0 4px 0'}));
var select_abrangencia = ui.Select({
  items: ['Estados / Municípios', 'Coordenadas (Lat / Lon)'],
  value: 'Estados / Municípios',
  style: {width: '260px', color: 'darkblue'}
});
painel_espacial.add(select_abrangencia);

var container_nomes = ui.Panel();
painel_espacial.add(container_nomes);
container_nomes.add(ui.Label('Passo 1: Região', {fontSize: '11px', color: '#555555'}));
var select_macro = ui.Select({ items: Object.keys(dicionario_regioes), value: 'Sul', style: {width: '260px'} });
container_nomes.add(select_macro);

container_nomes.add(ui.Label('Passo 2: Selecione os Estados', {fontSize: '11px', color: '#555555', margin: '10px 8px 0 8px'}));
var painel_add_estado = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal') });
var select_estado = ui.Select({ items: dicionario_regioes['Sul'], value: 'Paraná', style: {width: '150px'} });
var btn_add_estado = ui.Button({ label: '+ Adicionar', style: {color: 'green'} });
painel_add_estado.add(select_estado);
painel_add_estado.add(btn_add_estado);
container_nomes.add(painel_add_estado);

var painel_lista_estados = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal') });
var label_lista_estados = ui.Label('Estados: Nenhum', {fontSize: '11px', color: '#1d70b8', stretch: 'horizontal'});
var btn_limpar_estados = ui.Button({ label: 'Limpar', style: {color: 'red', margin: '0 8px'} });
var lista_estados_array = [];
painel_lista_estados.add(label_lista_estados);
painel_lista_estados.add(btn_limpar_estados);
container_nomes.add(painel_lista_estados);

var check_filtrar_munis = ui.Checkbox({ label: 'Deseja selecionar municípios específicos?', value: false, style: {margin: '15px 8px 5px 8px', fontWeight: 'bold', color: '#8c510a'} });
container_nomes.add(check_filtrar_munis);

var painel_municipios = ui.Panel({ style: {shown: false} });
container_nomes.add(painel_municipios);

var painel_add_muni = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal') });
var select_cidade = ui.Select({ placeholder: 'Aguardando estados...', style: {width: '150px'} });
var btn_add_cidade = ui.Button({ label: '+ Adicionar', style: {color: 'green'} });
painel_add_muni.add(select_cidade);
painel_add_muni.add(btn_add_cidade);
painel_municipios.add(painel_add_muni);

var painel_lista_cidades = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal') });
var label_lista_cidades = ui.Label('Municípios: Nenhum', {fontSize: '11px', color: '#1d70b8', stretch: 'horizontal'});
var btn_limpar_cidades = ui.Button({ label: 'Limpar', style: {color: 'red', margin: '0 8px'} });
var lista_cidades_array = [];
painel_lista_cidades.add(label_lista_cidades);
painel_lista_cidades.add(btn_limpar_cidades);
painel_municipios.add(painel_lista_cidades);

var container_coords = ui.Panel({ style: { shown: false, padding: '5px', border: '1px solid #d73027' } });
painel_espacial.add(container_coords);

var btn_desenhar_mapa = ui.Button({ label: '📍 Ativar Captura no Mapa', style: {color: '#1d70b8', margin: '10px 0'} });
container_coords.add(btn_desenhar_mapa);

container_coords.add(ui.Label('Ou insira os pontos manualmente:', {fontSize: '11px', color: '#555555'}));
var select_formato_coord = ui.Select({items: ['Graus/Min/Seg (ex: 23°33\'00"S)', 'Decimal (ex: -23.5500)'], value: 'Decimal (ex: -23.5500)', style: {width: '260px'}});
container_coords.add(select_formato_coord);

var painel_inputs_coords = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal') });
var box_lat = ui.Textbox({ placeholder: '-23.5500', style: {width: '110px'} });
var box_lon = ui.Textbox({ placeholder: '-46.6333', style: {width: '110px'} });

select_formato_coord.onChange(function(formato) {
  box_lat.setValue('');
  box_lon.setValue('');

  if (formato.indexOf('Graus') !== -1) {
    box_lat.setPlaceholder("23°33'00\"S");
    box_lon.setPlaceholder("46°37'59\"W");
  } else {
    box_lat.setPlaceholder("-23.5500");
    box_lon.setPlaceholder("-46.6333");
  }
});

painel_inputs_coords.add(ui.Label('Lat:')); painel_inputs_coords.add(box_lat);
painel_inputs_coords.add(ui.Label('Lon:')); painel_inputs_coords.add(box_lon);
container_coords.add(painel_inputs_coords);

container_coords.add(ui.Label('Cada área exige no mínimo 4 pontos. Use o separador abaixo se desejar traçar múltiplas fazendas.', {fontSize: '11px', color: '#d73027', fontWeight: 'bold'}));

var painel_botoes_coords = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal') });
var btn_add_coord = ui.Button({ label: '+ Adicionar Ponto', style: {color: 'green'} });
var btn_nova_area = ui.Button({ label: '✂️ Separar Polígonos', style: {color: '#f57c00'} });
var btn_limpar_coords = ui.Button({ label: 'Limpar Todos', style: {color: 'red'} });

painel_botoes_coords.add(btn_add_coord);
painel_botoes_coords.add(btn_nova_area);
painel_botoes_coords.add(btn_limpar_coords);
container_coords.add(painel_botoes_coords);

var painel_lista_coords = ui.Panel({ layout: ui.Panel.Layout.flow('vertical'), style: {margin: '5px 0'} });
container_coords.add(painel_lista_coords);
var lista_coords_array = [];

// =========================================================
// BLOCO ADICIONADO: INFLUÊNCIA GLOBAL ENSO (Conforme Imagem)
// =========================================================
var bloco_enso = ui.Panel({ style: { shown: false } });
bloco_enso.add(ui.Label('Influência Global (El Niño e La Niña):', {fontWeight: 'bold'}));
var painel_enso = ui.Panel({ style: { border: '1px solid #cccccc', padding: '12px', margin: '5px 0px 15px 0px', backgroundColor: '#fcfcfc' } });

// A. PREVISÃO DA PRÓXIMA ESTAÇÃO (Motor Preditivo)
painel_enso.add(ui.Label('A. El Niño / La Niña agora e nos próximos 3 meses', {fontWeight: 'bold', fontSize: '12px', color: '#d73027'}));   // [2026.10.7]
var desc_preditivo = ui.Label('Mostra a situação atual do Pacífico e uma estimativa para os 3 meses seguintes, feita com os anos do passado mais parecidos com agora. Não é a previsão oficial do CPC/NOAA.', {fontSize: '10px', color: '#666666', margin: '4px 0 12px 0'});
painel_enso.add(desc_preditivo);

var btn_calcular_enso = ui.Button({ label: '📊 Ver a situação e a estimativa', style: { stretch: 'horizontal', margin: '0 0 5px 0' } });
painel_enso.add(btn_calcular_enso);

var painel_resultados_enso = ui.Panel({ style: { shown: false, padding: '12px', backgroundColor: '#ffffff', border: '1px solid #e0e0e0', margin: '5px 0 0 0' } });
var label_status_enso = ui.Label('', {fontSize: '12px', color: '#333333', fontWeight: 'bold'});
var label_alerta_enso = ui.Label('', {fontSize: '11px', fontWeight: 'bold', margin: '8px 0'});
// [V4.1 22/10] apresentação do ENSO reorganizada: situação atual, previsão (com os anos análogos) e como ler
var label_situacao_enso = ui.Label('', {fontSize: '11px', color: '#333333', margin: '2px 0 0 0'});
var label_titulo_prev_enso = ui.Label('', {fontSize: '12px', color: '#333333', fontWeight: 'bold', margin: '12px 0 0 0'});
var label_analogos_enso = ui.Label('', {fontSize: '11px', color: '#333333', fontWeight: 'bold', margin: '4px 0 6px 0'});   // [2026.10.7] resposta curta
var label_prob_elnino = ui.Label('', {fontSize: '12px', color: '#d73027', fontWeight: 'bold', margin: '4px 0'});
var label_prob_lanina = ui.Label('', {fontSize: '12px', color: '#1d70b8', fontWeight: 'bold', margin: '4px 0'});
var label_prob_neutro = ui.Label('', {fontSize: '12px', color: '#888888', fontWeight: 'bold', margin: '4px 0'});
// [V4 IC] Nota sobre o significado das probabilidades e do intervalo
var label_nota_ic = ui.Label('', {fontSize: '10px', color: '#666666', margin: '8px 0 0 0', shown: false});
// [2026.10.7] anos parecidos e avisos logo abaixo das porcentagens; a explicação longa fica atrás do botão "Como ler"
var label_detalhes_enso = ui.Label('', {fontSize: '11px', color: '#333333', margin: '8px 0 0 0'});
var btn_como_ler_enso = ui.Button({ label: 'ℹ️ Como ler este resultado', style: { stretch: 'horizontal', margin: '8px 0 0 0', shown: false } });
btn_como_ler_enso.onClick(function() {
  var mostrar = !label_nota_ic.style().get('shown');
  label_nota_ic.style().set('shown', mostrar);
  btn_como_ler_enso.setLabel(mostrar ? 'ℹ️ Esconder a explicação' : 'ℹ️ Como ler este resultado');
});
var btn_exportar_enso = ui.Button({ label: '📥 Gerar link da previsão (CSV)', style: { stretch: 'horizontal', margin: '12px 0 0 0', shown: false } });
// [V4.1 22/10] Downloads do ENSO por link direto (getDownloadURL), como os dados climáticos; antes iam
// para a aba Tasks (Export.table.toDrive), que não existe para quem usa o App publicado.
var label_link_enso_resumo = ui.Label('', {fontSize: '12px', margin: '6px 0 0 0', shown: false});
var label_link_enso_analogos = ui.Label('', {fontSize: '12px', margin: '2px 0 0 0', shown: false});

painel_resultados_enso.add(label_status_enso);
painel_resultados_enso.add(label_situacao_enso);      // [V4.1 22/10]
painel_resultados_enso.add(label_alerta_enso);
painel_resultados_enso.add(label_titulo_prev_enso);   // [V4.1 22/10]
painel_resultados_enso.add(label_analogos_enso);      // [V4.1 22/10]
painel_resultados_enso.add(label_prob_elnino);
painel_resultados_enso.add(label_prob_neutro);        // [V4.1 22/10] ordem: El Niño, Neutro, La Niña
painel_resultados_enso.add(label_prob_lanina);
painel_resultados_enso.add(label_detalhes_enso);   // [2026.10.7]
painel_resultados_enso.add(btn_como_ler_enso);     // [2026.10.7]
painel_resultados_enso.add(label_nota_ic); // [V4 IC]
painel_resultados_enso.add(btn_exportar_enso);
painel_resultados_enso.add(label_link_enso_resumo);     // [V4.1 22/10]
painel_resultados_enso.add(label_link_enso_analogos);   // [V4.1 22/10]
painel_enso.add(painel_resultados_enso);

painel_enso.add(ui.Label('', {border: '0.5px solid #eeeeee', margin: '15px 0 15px 0', stretch: 'horizontal'}));

// B. AJUSTE DE CENÁRIO HISTÓRICO (Filtro Passado)
painel_enso.add(ui.Label('B. Clima do passado em meses de El Niño, La Niña ou neutro', {fontWeight: 'bold', fontSize: '12px', color: '#1d70b8'}));   // [2026.10.7]
var check_usar_enso = ui.Checkbox({ label: 'Filtrar os dados do passado por fenômeno', value: false, style: {fontSize: '12px', color: '#333333', fontWeight: 'bold'} });
painel_enso.add(check_usar_enso);
painel_enso.add(ui.Label('Baixa os dados da sua área só dos meses, desde 1961, em que houve o fenômeno escolhido (mesma classificação do item A).\n' +
  '1. Marque a caixa acima e escolha o fenômeno na lista.\n' +
  '2. Escolha a resolução e o período e clique em PROCESSAR DADOS CLIMÁTICOS, no fim do painel.\n' +
  '3. Baixe os arquivos em "Arquivos Prontos para Download". O nome termina com o fenômeno (ex.: Mensal_Pato_Branco_1982_El_Nino_Muito_Forte.csv); as últimas colunas dizem a fase e a força de cada mês. Os dias de previsão vêm todos, marcados "Previsao (sem classificacao)".',
  {fontSize: '10px', color: '#666666', margin: '0 0 10px 25px', whiteSpace: 'pre-wrap'}));   // [V4.1 22/10]

var painel_opcoes_historico = ui.Panel({ layout: ui.Panel.Layout.flow('vertical'), style: { shown: false, margin: '0 0 15px 25px' } });
// [V4.1 22/10] Uma tabela só para os nomes dos cenários: o rótulo da lista usa os mesmos nomes, faixas e
// vírgula decimal do item A ("muito forte", "+1,5 a +1,9 °C"); o valor interno continua o texto antigo
// (usado por filtroCenario); 'ascii' vai para a coluna Filtro_ENSO e 'arquivo' para o nome dos CSV.
var CENARIOS_ENSO = [
  {value: 'Todos os Anos', label: 'Sem filtro (todos os meses)', ascii: '', arquivo: ''},
  {value: 'Super El Niño (≥ 2.0°C)', label: 'El Niño muito forte, Super (+2,0 °C ou mais)', ascii: 'El Nino muito forte (Super)', arquivo: 'El_Nino_Muito_Forte'},
  {value: 'El Niño Forte (1.5 a 1.9°C)', label: 'El Niño forte (+1,5 a +1,9 °C)', ascii: 'El Nino forte', arquivo: 'El_Nino_Forte'},
  {value: 'El Niño Moderado (1.0 a 1.4°C)', label: 'El Niño moderado (+1,0 a +1,4 °C)', ascii: 'El Nino moderado', arquivo: 'El_Nino_Moderado'},
  {value: 'El Niño Fraco (0.5 a 0.9°C)', label: 'El Niño fraco (+0,5 a +0,9 °C)', ascii: 'El Nino fraco', arquivo: 'El_Nino_Fraco'},
  {value: 'Anos Neutros', label: 'Neutro (entre −0,5 e +0,5 °C)', ascii: 'Neutro', arquivo: 'Neutro'},
  {value: 'La Niña Fraca (-0.5 a -0.9°C)', label: 'La Niña fraca (−0,5 a −0,9 °C)', ascii: 'La Nina fraca', arquivo: 'La_Nina_Fraca'},
  {value: 'La Niña Moderada (-1.0 a -1.4°C)', label: 'La Niña moderada (−1,0 a −1,4 °C)', ascii: 'La Nina moderada', arquivo: 'La_Nina_Moderada'},
  {value: 'La Niña Forte (-1.5 a -1.9°C)', label: 'La Niña forte (−1,5 a −1,9 °C)', ascii: 'La Nina forte', arquivo: 'La_Nina_Forte'},
  {value: 'Super La Niña (≤ -2.0°C)', label: 'La Niña muito forte, Super (−2,0 °C ou menos)', ascii: 'La Nina muito forte (Super)', arquivo: 'La_Nina_Muito_Forte'}
];
function infoCenarioEnso(valor) {
  for (var i = 0; i < CENARIOS_ENSO.length; i++) { if (CENARIOS_ENSO[i].value === valor) return CENARIOS_ENSO[i]; }
  return {value: valor, label: valor, ascii: '', arquivo: ''};
}
var select_enso = ui.Select({
  items: CENARIOS_ENSO.map(function(c) { return {label: c.label, value: c.value}; }),
  value: 'Todos os Anos',
  style: {width: '290px', margin: '0 0 8px 0'}
});
var btn_exportar_historico_enso = ui.Button({ label: '📋 Só a lista de meses do fenômeno (sem dados de clima)', style: { stretch: 'horizontal', margin: '0' } });
// [V4.1 22/10] deixa claro que esta lista não traz dados de clima
var label_nota_lista_enso = ui.Label('Opcional: baixa só o calendário dos meses com o fenômeno (1961 até hoje: mês, trimestre, RONI e força), sem dados de clima.', {fontSize: '10px', color: '#666666', margin: '4px 0 0 0'});
var label_link_enso_hist = ui.Label('', {fontSize: '12px', margin: '6px 0 0 0', shown: false});   // [V4.1 22/10]

painel_opcoes_historico.add(select_enso);
painel_opcoes_historico.add(btn_exportar_historico_enso);
painel_opcoes_historico.add(label_nota_lista_enso);   // [V4.1 22/10]
painel_opcoes_historico.add(label_link_enso_hist);   // [V4.1 22/10]
painel_enso.add(painel_opcoes_historico);

bloco_enso.add(painel_enso);
painel.add(bloco_enso);
// =========================================================

var bloco_periodo = ui.Panel({ style: { shown: false } });
var label_periodo = ui.Label('Período (A partir de 1961):', {fontWeight: 'bold'});
bloco_periodo.add(label_periodo);

var dataHoje = new Date();
var dataInicio = new Date();
dataInicio.setDate(dataHoje.getDate() - 30); 

function formatarDataBR(dataObj) {
  var d = ('0' + dataObj.getDate()).slice(-2);
  var m = ('0' + (dataObj.getMonth() + 1)).slice(-2);
  var a = dataObj.getFullYear();
  return d + '/' + m + '/' + a;
}

var strHoje = formatarDataBR(dataHoje);
var strInicio = formatarDataBR(dataInicio);

var box_inicio = ui.Textbox({ value: strInicio, style: {width: '120px'} });
var box_fim = ui.Textbox({ value: strHoje, style: {width: '120px'} });
var label_ate = ui.Label(' até ', {margin: '8px 4px'});
var painel_data_fim = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal'), style: {margin: '0', padding: '0'} });
painel_data_fim.add(label_ate);
painel_data_fim.add(box_fim);

var painel_calendario = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal') });
painel_calendario.add(box_inicio);
painel_calendario.add(painel_data_fim);
bloco_periodo.add(painel_calendario);
painel.add(bloco_periodo);

// BLOCO 7: EXPORTAÇÃO CSV
var painel_exportacoes_gerais = ui.Panel({ style: { shown: false } });
var label_dicionario_aviso = ui.Label('💡 O dicionário será liberado na tela junto com as tabelas.', {fontSize: '10px', color: '#1d70b8', margin: '5px 8px'});
painel_exportacoes_gerais.add(label_dicionario_aviso);
painel.add(painel_exportacoes_gerais);

var painel_previsao = ui.Panel({ style: { shown: false } });
painel_previsao.add(ui.Label('Previsão do Tempo (GFS NOAA):', {fontWeight: 'bold', color: '#1d70b8'}));
var check_previsao = ui.Checkbox({ 
  label: 'Acoplar previsão para os próximos 15 dias', 
  value: true, 
  disabled: false, 
  style: {fontWeight: 'bold', color: '#0b5d1e'} 
});
var aviso_previsao = ui.Label('A previsão preencherá a lacuna de tempo real e o futuro.', {fontSize: '10px', color: '#555555', margin: '0 0 10px 15px'});
painel_previsao.add(check_previsao);
painel_previsao.add(aviso_previsao);
painel.add(painel_previsao);

// [2026.10.5] BLOCO 8: VARIÁVEIS DO ARQUIVO (valem para o link na hora e para o envio por e-mail)
// código do pedido, coluna do CSV, rótulo, grupo (na ordem dos grupos; o CSV segue a ordem de getColunasClimaBase)
var VARIAVEIS_SAB = [
  ['pr', 'Precipitacao_mm', 'Precipitação (mm)', 'Chuva e escoamento'],
  ['ce', 'Chuva_Efetiva_mm', 'Chuva efetiva (mm)', 'Chuva e escoamento'],
  ['rsup', 'Runoff_Superficial_mm', 'Escoamento superficial (mm)', 'Chuva e escoamento'],
  ['rsub', 'Runoff_Subsuperficial_mm', 'Escoamento subsuperficial (mm)', 'Chuva e escoamento'],
  ['tmax', 'Temperatura_Maxima_C', 'Temperatura máxima (°C)', 'Temperatura'],
  ['tmin', 'Temperatura_Minima_C', 'Temperatura mínima (°C)', 'Temperatura'],
  ['amp', 'Amplitude_Termica_C', 'Amplitude térmica (°C)', 'Temperatura'],
  ['tsolo', 'Temperatura_Solo_C', 'Temperatura do solo (°C)', 'Temperatura'],
  ['tfolha', 'Temperatura_Folha_C', 'Temperatura de superfície (°C)', 'Temperatura'],
  ['ur', 'Umidade_Relativa_Porc', 'Umidade relativa do ar (%)', 'Ar e radiação'],
  ['vento', 'Vento_ms', 'Vento a 2 m (m/s)', 'Ar e radiação'],
  ['rad', 'Radiacao_Solar_MJ_m2', 'Radiação solar (MJ/m²)', 'Ar e radiação'],
  ['dpv', 'Deficit_Pressao_Vapor_kPa', 'Déficit de pressão de vapor (kPa)', 'Ar e radiação'],
  ['etp', 'Evapotranspiracao_Potencial_mm', 'Evapotranspiração potencial (mm)', 'Balanço hídrico'],
  ['etr', 'Evapotranspiracao_Real_mm', 'Evapotranspiração real (mm)', 'Balanço hídrico'],
  ['transp', 'Transpiracao_Planta_mm', 'Transpiração (mm)', 'Balanço hídrico'],
  ['def', 'Deficit_Hidrico_mm', 'Déficit hídrico (mm)', 'Balanço hídrico'],
  ['us5', 'Umidade_Volumetrica_Solo_0_5cm_m3_m3', 'Umidade do solo de 0 a 5 cm (m³/m³)', 'Umidade do solo'],
  ['us100', 'Umidade_Volumetrica_Solo_0_100cm_m3_m3', 'Umidade do solo de 0 a 100 cm (m³/m³)', 'Umidade do solo']
];
var bloco_variaveis = ui.Panel({ style: { shown: false } });
bloco_variaveis.add(ui.Label('Variáveis do arquivo:', {fontWeight: 'bold'}));
var check_todas_vars = ui.Checkbox({ label: 'Todas as variáveis (19)', value: true, style: {fontWeight: 'bold'} });
var painel_vars = ui.Panel({ style: { shown: false, margin: '0 0 0 12px' } });
var checks_vars = {};
(function() {
  var grupoAtual = null;
  VARIAVEIS_SAB.forEach(function(v) {
    if (v[3] !== grupoAtual) {
      grupoAtual = v[3];
      painel_vars.add(ui.Label(grupoAtual, {fontSize: '11px', color: '#555555', margin: '6px 0 0 0', fontWeight: 'bold'}));
    }
    checks_vars[v[0]] = ui.Checkbox({ label: v[2], value: false, style: {fontSize: '12px', margin: '0 0 0 8px'} });
    painel_vars.add(checks_vars[v[0]]);
  });
})();
check_todas_vars.onChange(function(marcado) { painel_vars.style().set('shown', !marcado); });
bloco_variaveis.add(check_todas_vars);
bloco_variaveis.add(painel_vars);
bloco_variaveis.add(ui.Label('Ponto, data, coordenadas, município, estado e qualidade do pixel vão sempre. Menos variáveis deixam o arquivo menor.',
                             {fontSize: '10px', color: '#555555', margin: '0 0 10px 8px'}));
painel.add(bloco_variaveis);

// Códigos das variáveis marcadas; null = todas
function variaveisEscolhidas() {
  if (check_todas_vars.getValue()) return null;
  return VARIAVEIS_SAB.filter(function(v) { return checks_vars[v[0]].getValue(); }).map(function(v) { return v[0]; });
}

// Tira do CSV as colunas das variáveis não marcadas (as de identificação, qualidade e ENSO ficam sempre)
function filtrarColunasPorVariaveis(colunas) {
  var escolhidas = variaveisEscolhidas();
  if (!escolhidas) return colunas;
  var fora = VARIAVEIS_SAB.filter(function(v) { return escolhidas.indexOf(v[0]) === -1; })
                          .map(function(v) { return v[1]; });
  return colunas.filter(function(c) { return fora.indexOf(c) === -1; });
}

var btn_processar = ui.Button({ label: 'PROCESSAR DADOS CLIMÁTICOS', style: { stretch: 'horizontal', color: 'darkblue', fontWeight: 'bold', shown: false } });
painel.add(btn_processar);

// ============================================================
// PAINEL DE DOWNLOADS PARA EE_APP
// ============================================================
var painel_downloads_app = ui.Panel({
  layout: ui.Panel.Layout.flow('vertical'),
  style: { shown: false, border: '2px solid #4CAF50', padding: '10px', margin: '15px 0' }
});
painel_downloads_app.add(ui.Label('Arquivos Prontos para Download:', {fontWeight: 'bold', color: '#2e7d32', fontSize: '14px'}));
painel.add(painel_downloads_app);

// [2026.10.5] PEDIDO POR E-MAIL: o pedido vai direto para o App da Web do Apps Script (sem o formulário)
var painel_pedido_email = ui.Panel({
  layout: ui.Panel.Layout.flow('vertical'),
  style: { shown: false, border: '2px solid #1d70b8', padding: '10px', margin: '0 0 15px 0' }
});
var label_email_titulo = ui.Label('📧 Receber por e-mail', {fontWeight: 'bold', color: '#1d70b8', fontSize: '14px'});
var label_email_motivo = ui.Label('', {fontSize: '11px', color: '#333333'});
var box_email_nome = ui.Textbox({ placeholder: 'Nome completo', style: {width: '340px'} });
var box_email_endereco = ui.Textbox({ placeholder: 'E-mail para receber o link', style: {width: '340px'} });
var box_email_inst = ui.Textbox({ placeholder: 'Instituição', style: {width: '340px'} });
var select_email_fin = ui.Select({
  items: ['Pesquisa acadêmica', 'Ensino', 'Extensão ou assistência técnica', 'Produção agrícola', 'Outro'],
  placeholder: 'Finalidade do uso dos dados', style: {width: '340px'}
});
// [2026.10.6] formato da entrega por e-mail: o Excel vem com os números prontos (conversão no GitHub, sab_xlsx.py)
var FORMATOS_EMAIL = [['CSV', 'csv'], ['Excel (.xlsx), números prontos', 'xlsx'], ['CSV e Excel (.xlsx)', 'ambos']];
var select_email_formato = ui.Select({
  items: FORMATOS_EMAIL.map(function(f) { return f[0]; }), value: FORMATOS_EMAIL[0][0],
  placeholder: 'Formato dos arquivos', style: {width: '340px'}
});
var label_email_formato = ui.Label('Formato dos arquivos (o Excel abre com duplo clique, sem configurar nada):',
                                   {fontSize: '11px', color: '#333333', margin: '4px 8px 0 8px'});
var label_email_spam = ui.Label('⚠️ Os e-mails automáticos podem cair na caixa de SPAM, Lixo eletrônico ou Promoções: ' +
  'procure lá também e marque "Não é spam". Os arquivos do e-mail trazem, em cada dia, 6 colunas sobre o El Niño / La Niña.',
  {fontSize: '11px', color: '#8a5300', margin: '4px 8px'});
var check_email_lgpd = ui.Checkbox({
  label: 'Li e concordo: meu nome, e-mail, instituição e finalidade são usados só para enviar o link dos arquivos e ' +
         'para estatísticas de uso do SAB, sem compartilhamento (LGPD, Lei 13.709/2018). O link vale 7 dias.',
  value: false, style: {fontSize: '11px'}
});
// [2026.11.3] Um botão só: o painel do Earth Engine não pode chamar outro site sozinho, então o envio é um link. Ele
// aparece pronto (com o pedido montado) assim que os campos estão completos; antes disso, a linha de cima diz o que falta.
var label_email_falta = ui.Label('', {fontSize: '12px', color: '#8a5300', margin: '6px 8px'});
// O Earth Engine pinta todo link de azul: fundo claro e borda azul deixam o texto legível
var label_email_link = ui.Label('', {fontSize: '15px', fontWeight: 'bold', color: '#1d70b8', backgroundColor: '#e8f1fb',
                                     border: '2px solid #1d70b8', padding: '10px', margin: '8px 8px', textAlign: 'center',
                                     stretch: 'horizontal', shown: false});
[label_email_titulo, label_email_motivo, box_email_nome, box_email_endereco, box_email_inst, select_email_fin,
 label_email_formato, select_email_formato, label_email_spam,
 check_email_lgpd, label_email_falta, label_email_link].forEach(function(w) { painel_pedido_email.add(w); });
painel.add(painel_pedido_email);
APP.pedidoEmail = null;
APP.ultimoCodigoEmail = null;

function mostrarPedidoEmail(motivo, pedido) {
  APP.pedidoEmail = pedido;
  APP.ultimoCodigoEmail = null;
  label_email_motivo.setValue(motivo);
  painel_pedido_email.style().set('shown', true);
  atualizarEnvioEmail();
}

// [2026.11.3] Confere os campos e monta o endereço do pedido (função pura, testada no teste_06_2026_11_3.js).
// Devolve {erro: texto} ou {url: endereço, codigo: código do pedido}. Mesmo endereço e mesmas regras da 2026.10.6.
function montarUrlPedidoEmail(p, campos) {
  if (!p) return {erro: 'Processe os dados primeiro.'};
  if (!CFG.urlPedidoEmail) return {erro: 'O envio por e-mail ainda não foi configurado neste painel.'};
  var ufs = (p.codigo.match(/;uf=([^;]*)/) || ['', ''])[1];   // [2026.10.6] o e-mail aceita até 6 estados
  if (/;tipo=E;/.test(p.codigo) && ufs.split(',').length > 6) {
    return {erro: 'Pelo e-mail, no máximo 6 estados por pedido (o Brasil inteiro estoura a memória do Earth Engine). ' +
                  'Escolha menos estados e processe de novo.'};
  }
  var nome = String(campos.nome || '').trim();
  var email = String(campos.email || '').trim();
  var falta = [];
  if (nome.length < 3) falta.push('o seu nome completo');
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) falta.push('um e-mail válido');
  if (!campos.fin) falta.push('a finalidade do uso dos dados');
  if (!campos.lgpd) falta.push('marcar a caixa de concordância (LGPD)');
  if (falta.length) return {erro: 'Para liberar o botão de envio, falta: ' + falta.join('; ') + '.'};
  var q = function(k, v) { return k + '=' + encodeURIComponent(v); };
  var pf = pedidoComFormato(p, campos.formato);   // [2026.10.6]
  return {
    codigo: pf.codigo,
    url: CFG.urlPedidoEmail + '?' + [q('codigo', pf.codigo), q('resumo', pf.resumo), q('nome', nome), q('email', email),
         q('inst', String(campos.inst || '').trim()), q('fin', campos.fin), q('aceite', '1')].join('&')
  };
}

// Atualiza o botão a cada mudança de campo (as caixas de texto avisam ao sair delas ou com Enter)
function atualizarEnvioEmail() {
  var r = montarUrlPedidoEmail(APP.pedidoEmail, {
    nome: box_email_nome.getValue(), email: box_email_endereco.getValue(), inst: box_email_inst.getValue(),
    fin: select_email_fin.getValue(), formato: select_email_formato.getValue(), lgpd: check_email_lgpd.getValue()
  });
  if (r.erro) {
    label_email_link.style().set('shown', false);
    label_email_falta.setValue(r.erro);
    label_email_falta.style().set('shown', true);
    return;
  }
  label_email_falta.setValue('✅ Tudo preenchido. Clique no quadro azul abaixo: o pedido é enviado e abre uma aba com o número dele.');
  label_email_link.setValue('📨  Clique aqui para ENVIAR O PEDIDO');
  label_email_link.setUrl(r.url);
  label_email_link.style().set('shown', true);
  if (r.codigo !== APP.ultimoCodigoEmail) logInfo('Pedido por e-mail pronto para envio: ' + r.codigo);
  APP.ultimoCodigoEmail = r.codigo;
}
[box_email_nome, box_email_endereco, box_email_inst, select_email_fin, select_email_formato, check_email_lgpd]
  .forEach(function(w) { w.onChange(atualizarEnvioEmail); });

// [2026.10.6] Acrescenta ;fmt=xlsx ou ;fmt=ambos ao código (CSV é o padrão e não vai no código)
function pedidoComFormato(p, rotulo) {
  var fmt = 'csv';
  FORMATOS_EMAIL.forEach(function(f) { if (f[0] === rotulo) fmt = f[1]; });
  if (fmt === 'csv') return {codigo: p.codigo, resumo: p.resumo};
  return {codigo: p.codigo + ';fmt=' + fmt, resumo: p.resumo + (fmt === 'xlsx' ? ', em Excel (.xlsx)' : ', em CSV e Excel (.xlsx)')};
}

// Código do pedido (o mesmo formato que a rotina do e-mail e o formulário usam), a partir do que está na tela
function montarCodigoPedido(datas) {
  var res = select_resolucao.getValue() === 'Diária' ? 'D' : 'M';
  var partes = ['v=1', 'res=' + res];
  var descricao;
  if (select_abrangencia.getValue() === 'Coordenadas (Lat / Lon)') {
    var pols = [], atual = [];
    lista_coords_array.forEach(function(item) {
      if (item === 'NOVA_AREA_BREAK') { if (atual.length) pols.push(atual); atual = []; return; }
      var c = String(item).split(',');
      atual.push(String(c[0]).trim() + ' ' + String(c[1]).trim());
    });
    if (atual.length) pols.push(atual);
    partes.push('tipo=P', 'pol=' + pols.map(function(a) { return a.join(','); }).join('|'));
    descricao = pols.length + ' área(s) desenhada(s)';
  } else if (check_filtrar_munis.getValue()) {
    partes.push('tipo=M', 'uf=' + lista_estados_array.join(','), 'mun=' + lista_cidades_array.join(','));
    descricao = lista_cidades_array.length === 1 ? lista_cidades_array[0] : lista_cidades_array.length + ' municípios';
  } else {
    partes.push('tipo=E', 'uf=' + lista_estados_array.join(','));
    descricao = lista_estados_array.join(', ');
  }
  var vars = variaveisEscolhidas();
  partes.push('ini=' + datas.isoInicio, 'fim=' + datas.isoFim, 'var=' + (vars ? vars.join(',') : 'todas'));
  // filtro ENSO do item B: a rotina do e-mail aplica o mesmo recorte (meses do fenômeno + previsão)
  var enso = APP.filtroEnso ? infoCenarioEnso(APP.filtroEnso) : null;
  if (enso && enso.arquivo) partes.push('enso=' + enso.arquivo);
  var br = function(iso) { var x = iso.split('-'); return x[2] + '/' + x[1] + '/' + x[0]; };
  return {
    codigo: partes.join(';'),
    resumo: descricao + ', ' + (res === 'D' ? 'diário' : 'mensal') + ', ' + br(datas.isoInicio) + ' a ' +
            br(datas.isoFim) + ', ' + (vars ? vars.length + ' variável(is)' : 'todas as variáveis') +
            (enso && enso.arquivo ? ', filtro ' + enso.label : '')
  };
}

// Link na hora ou e-mail: linhas do maior arquivo (pontos x dias de um ano, teto) e número de arquivos
function decidirEntrega(nPontos, nLocais, datas) {
  var anos = parseInt(datas.isoFim.split('-')[0], 10) - parseInt(datas.isoInicio.split('-')[0], 10) + 1;
  var diaria = select_resolucao.getValue() === 'Diária';
  var linhasArquivo = nPontos * (diaria ? Math.min(datas.totalDias, 366) : 12);
  var linhasTotal = nPontos * (diaria ? datas.totalDias : anos * 12);
  var arquivos = nLocais * anos;
  var mil = function(x) { return String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); };
  var grande = linhasArquivo > CFG.limiteLinhasLink || arquivos > CFG.limiteArquivosLink;
  var resumo = 'cerca de ' + mil(linhasTotal) + ' linhas em ' + arquivos + ' arquivo(s)';
  // Com o filtro ENSO, as linhas acima são um teto (o filtro deixa só os meses do fenômeno)
  return {
    grande: grande,
    link: !grande || !CFG.urlPedidoEmail,   // sem o envio configurado: como na 2026.10.4
    linhas: linhasTotal,
    motivo: (grande ?
      'Pedido grande (' + resumo + ') para o link na hora. Preencha abaixo e receba os arquivos por e-mail, numa ' +
      'pasta com um arquivo por local e por ano (de minutos a algumas horas).' :
      'Prefere receber tudo por e-mail, numa pasta só? (' + resumo + ')') +
      ' Os arquivos chegam como link para uma pasta no Google Drive, que abre no navegador sem conta Google; ' +
      'pedidos pequenos vêm também anexados (.zip). Pode escolher CSV ou Excel. O Brasil inteiro não vai por e-mail: ' +
      'peça por estados (até 6).'
  };
}

var splitPanel = ui.SplitPanel({ firstPanel: painel, secondPanel: meuMapa, orientation: 'horizontal' });
ui.root.add(splitPanel);

// ============================================================
// MODULO 11: FUNCOES DE ATUALIZACAO E VISIBILIDADE DA UI
// ============================================================

function atualizarDicaData(val) {
  var anoIni = CFG.periodoHistoricoInicio.split('-')[0];
  var anoFim = CFG.periodoHistoricoFim.split('-')[0];
  var anoProvisorio = String(parseInt(anoFim, 10) + 1);
  label_dica_data.setValue('📅 Histórico ' + anoIni + ' a ' + anoFim + ' | ' + anoProvisorio +
                           ' provisório (ERA5 calibrado) | Previsão GFS: 15 dias');
  logInfo('Fonte de dados selecionada: ' + val);
}

function atualizarTextoListaMunis() {
  label_lista_cidades.setValue(lista_cidades_array.length === 0 ? 'Municípios: Nenhum' : 'Municípios: ' + lista_cidades_array.join(', '));
}

function atualizarTextoListaEstados() {
  label_lista_estados.setValue(lista_estados_array.length === 0 ? 'Estados: Nenhum' : 'Estados: ' + lista_estados_array.join(', '));
}

function desenharRascunhoPoligono() {
  if (APP.layersByKey['rascunho_poligono']) {
    try { meuMapa.layers().remove(APP.layersByKey['rascunho_poligono'].layer); } catch (e) {}
    delete APP.layersByKey['rascunho_poligono'];
  }
  
  if (lista_coords_array.length === 0) return;
  
  var subPoligonos = [];
  var coordsAtuais = [];
  
  lista_coords_array.forEach(function(c) {
    if (c === 'NOVA_AREA_BREAK') {
      if (coordsAtuais.length > 0) {
        subPoligonos.push(coordsAtuais);
        coordsAtuais = [];
      }
    } else {
      var parts = c.split(',');
      coordsAtuais.push([parseFloat(String(parts[1]).trim()), parseFloat(String(parts[0]).trim())]);
    }
  });
  
  if (coordsAtuais.length > 0) {
    subPoligonos.push(coordsAtuais);
  }
  
  var features = [];
  var todosPontos = [];
  
  subPoligonos.forEach(function(coords) {
    todosPontos = todosPontos.concat(coords);
    if (coords.length > 2) {
      features.push(ee.Feature(ee.Geometry.Polygon([coords])));
    } else if (coords.length === 2) {
      features.push(ee.Feature(ee.Geometry.LineString(coords)));
    }
  });
  
  if (todosPontos.length > 0) {
    features.push(ee.Feature(ee.Geometry.MultiPoint(todosPontos)));
  }
  
  if (features.length === 0) return;
  
  var fc = ee.FeatureCollection(features);
  var layer = ui.Map.Layer(fc.style({color: '#ff0000', fillColor: '#ff000044', pointSize: 5, pointShape: 'circle', width: 2}), {}, 'Rascunho Geometria', true);
  APP.layersByKey['rascunho_poligono'] = { layer: layer, grupo: 'Referência', nome: 'Rascunho Geometria', visivel: true };
  meuMapa.layers().add(layer);
  
  if (!APP.modoCaptura && todosPontos.length === 1) {
    meuMapa.setCenter(todosPontos[0][0], todosPontos[0][1], 15);
  } else if (!APP.modoCaptura) {
    meuMapa.centerObject(fc);
  }
}

function atualizarTextoListaCoords() {
  painel_lista_coords.clear();
  if (lista_coords_array.length === 0) {
    painel_lista_coords.add(ui.Label('Lista: Nenhuma coordenada adicionada.', {fontSize: '11px', color: '#555555'}));
    desenharRascunhoPoligono();
    return;
  }

  var contadorPonto = 1;
  lista_coords_array.forEach(function(item, index) {
    var linha = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal'), style: {margin: '2px 0'} });
    var lbl;
    
    if (item === 'NOVA_AREA_BREAK') {
      lbl = ui.Label('✂️ --- Quebra de Polígono ---', {fontSize: '12px', color: '#f57c00', fontWeight: 'bold', margin: '4px 0'});
      contadorPonto = 1;
    } else {
      lbl = ui.Label('Ponto ' + contadorPonto + ': ' + item, {fontSize: '12px', color: '#333333', margin: '4px 0'});
      contadorPonto++;
    }
    
    var btnRemover = ui.Button({
      label: 'Excluir',
      style: {margin: '0 0 0 10px', color: '#d32f2f'},
      onClick: function() {
        lista_coords_array.splice(index, 1);
        atualizarTextoListaCoords();
      }
    });
    linha.add(lbl);
    linha.add(btnRemover);
    painel_lista_coords.add(linha);
  });
  
  desenharRascunhoPoligono();
}

function atualizarListaCidades() {
  if (lista_estados_array.length === 0) {
    select_cidade.items().reset(['Adicione um estado primeiro']);
    select_cidade.setValue('Adicione um estado primeiro');
    select_cidade.setDisabled(true);
    return;
  }

  logStep('Atualizando lista de municípios disponíveis...');
  select_cidade.setPlaceholder('Carregando municípios...');
  select_cidade.setDisabled(true);

  var variacoesListaEstados = listaVariacoesBusca(lista_estados_array);
  var filtro = municipios.filter(ee.Filter.inList('ADM1_NAME', variacoesListaEstados));

  filtro.aggregate_array('ADM2_NAME').evaluate(function(lista, erro) {
    if (erro) {
      logError('Falha ao buscar municípios no servidor.', erro);
      select_cidade.items().reset(['Erro de conexão']);
      select_cidade.setValue('Erro de conexão');
      return;
    }
    if (!lista || lista.length === 0) {
      select_cidade.items().reset(['Nenhum município encontrado']);
      select_cidade.setValue('Nenhum município encontrado');
      return;
    }
    
    var lista_unica = lista.filter(function(item, pos) { return lista.indexOf(item) === pos; });
    lista_unica.sort();
    select_cidade.items().reset(lista_unica);
    select_cidade.setValue(lista_unica[0]);
    select_cidade.setDisabled(false);
    logInfo('Municípios carregados e prontos para seleção.');
  });
}

function verificarECorrigirCoords() {
  var formato = select_formato_coord.getValue();
  var fonte = select_fonte.getValue();
  
  var coords = verificarECorrigirCoordsTexto(box_lat.getValue(), box_lon.getValue(), formato, fonte);
  if (!coords) {
    if (formato.indexOf('Graus') !== -1) {
      mostrarAlertaTela('⚠️ Formato de Graus inválido. Tente digitar como: 25°30\'15"S ou similar.');
    }
    return null;
  }
  
  box_lat.setValue(coords.lat.toFixed(6));
  box_lon.setValue(coords.lon.toFixed(6));
  select_formato_coord.setValue('Decimal (ex: -23.5500)'); 
  return coords;
}

function atualizarVisibilidadeEspacial(val) {
  var is_admin = (val === 'Estados / Municípios');
  var is_coord = (val === 'Coordenadas (Lat / Lon)');

  container_nomes.style().set('shown', is_admin);
  container_coords.style().set('shown', is_coord);
  APP.abrangenciaAtual = val;
  logInfo('Abrangência espacial alterada para: ' + val);
}

// ============================================================
// MODULO 12: LISTENERS DE EVENTOS DA INTERFACE (ONCHANGE/ONCLICK)
// ============================================================
select_modo_processamento.onChange(function(val) {
  var isNenhum = val === '-- Selecione o Modo de Operação --';
  var isLocal = val.indexOf('Locais') !== -1;

  var temModoAtivo = !isNenhum;

  if (isLocal) {
      label_periodo.setValue('Período (A partir de 1961):');
  }

  bloco_resolucao.style().set('shown', temModoAtivo);
  painel_fonte.style().set('shown', temModoAtivo);
  bloco_espacial.style().set('shown', temModoAtivo);
  bloco_enso.style().set('shown', temModoAtivo); // Ativando Bloco ENSO
  bloco_periodo.style().set('shown', temModoAtivo);
  painel_data_fim.style().set('shown', true);
  
  painel_exportacoes_gerais.style().set('shown', temModoAtivo);
  painel_previsao.style().set('shown', temModoAtivo);
  btn_processar.style().set('shown', temModoAtivo);
  bloco_variaveis.style().set('shown', temModoAtivo);   // [2026.10.5]

  if (isNenhum) logInfo('Aguardando seleção do modo de operação...');
  if (isLocal) logInfo('Modo Extração Rápida: Interface simplificada para dados locais.');
});

check_usar_enso.onChange(function(checked) { 
  painel_opcoes_historico.style().set('shown', checked); 
});

function avaliarStatusPrevisao() {
  var dataInput = box_fim.getValue();
  var dataHojeAtual = formatarDataBR(new Date());
  
  if (dataInput === dataHojeAtual) {
      check_previsao.setDisabled(false);
      check_previsao.setValue(true);
  } else {
      check_previsao.setValue(false);
      check_previsao.setDisabled(true);
  }
}

box_inicio.onChange(function(texto) { aplicarMascaraData(texto, box_inicio); });
box_fim.onChange(function(texto) { 
  aplicarMascaraData(texto, box_fim); 
  avaliarStatusPrevisao(); 
});

avaliarStatusPrevisao();
select_fonte.onChange(function(val) { atualizarDicaData(val); });

select_macro.onChange(function(regiao) {
  var estados_da_regiao = dicionario_regioes[regiao];
  select_estado.items().reset(estados_da_regiao);
  if(estados_da_regiao.length > 0) select_estado.setValue(estados_da_regiao[0]);
});

check_filtrar_munis.onChange(function(checked) {
  painel_municipios.style().set('shown', checked);
  if (checked) atualizarListaCidades(); 
});

select_abrangencia.onChange(atualizarVisibilidadeEspacial);

select_resolucao.onChange(function(val) {
  logInfo('Resolução de processamento alterada para: ' + val);
});

btn_desenhar_mapa.onClick(function() {
  APP.modoCaptura = !APP.modoCaptura;
  if (APP.modoCaptura) {
    btn_desenhar_mapa.setLabel('🛑 Parar Captura de Pontos');
    btn_desenhar_mapa.style().set('color', '#d32f2f');
    meuMapa.style().set('cursor', 'crosshair');
    mostrarAlertaTela('Modo de captura ativado. Clique no mapa e os vértices serão adicionados um a um na sua lista, formando o desenho do polígono em tempo real.');
  } else {
    btn_desenhar_mapa.setLabel('📍 Ativar Captura no Mapa');
    btn_desenhar_mapa.style().set('color', '#1d70b8');
    meuMapa.style().set('cursor', 'hand');
  }
});

meuMapa.onClick(function(coords) {
  if (!APP.modoCaptura) return;
  var coord_str = coords.lat.toFixed(6) + ', ' + coords.lon.toFixed(6);
  if (lista_coords_array.indexOf(coord_str) === -1) {
    lista_coords_array.push(coord_str);
    atualizarTextoListaCoords();
  }
});

btn_add_estado.onClick(function() {
  var est = select_estado.getValue();
  if (est && lista_estados_array.indexOf(est) === -1) {
    lista_estados_array.push(est);
    atualizarTextoListaEstados();
    if (check_filtrar_munis.getValue()) atualizarListaCidades();
    logInfo('Estado adicionado ao escopo: ' + est);
  }
});

btn_limpar_estados.onClick(function() {
  lista_estados_array = [];
  lista_cidades_array = [];
  atualizarTextoListaEstados();
  atualizarTextoListaMunis();
  if (check_filtrar_munis.getValue()) atualizarListaCidades();
  logInfo('Lista de estados completamente limpa.');
});

btn_add_cidade.onClick(function() {
  var cid = select_cidade.getValue();
  if (cid && cid !== 'Adicione um estado primeiro' && cid !== 'Nenhum município encontrado' && lista_cidades_array.indexOf(cid) === -1) {
    lista_cidades_array.push(cid);
    atualizarTextoListaMunis();
    logInfo('Município adicionado ao escopo: ' + cid);
  }
});

btn_limpar_cidades.onClick(function() {
  lista_cidades_array = [];
  atualizarTextoListaMunis();
  logInfo('Lista de municípios limpa.');
});

btn_nova_area.onClick(function() {
  if (lista_coords_array.length === 0 || lista_coords_array[lista_coords_array.length - 1] === 'NOVA_AREA_BREAK') return;
  lista_coords_array.push('NOVA_AREA_BREAK');
  atualizarTextoListaCoords();
  logInfo('Quebra de geometria inserida. O próximo ponto iniciará um novo polígono.');
});

function mostrarConfirmacaoDuplicata(mensagem, callbackSim) {
  var painelAlerta = ui.Panel({ layout: ui.Panel.Layout.flow('vertical'), style: { position: 'top-center', padding: '15px', backgroundColor: '#ffffff', border: '3px solid #f57c00', width: '350px' } });
  var titulo = ui.Label('⚠️ COORDENADA REPETIDA', { fontWeight: 'bold', color: '#f57c00', fontSize: '14px', textAlign: 'center' });
  var texto = ui.Label(mensagem, { color: '#333333', fontSize: '13px', margin: '10px 0', textAlign: 'justify' });
  var painelBotoes = ui.Panel({ layout: ui.Panel.Layout.flow('horizontal'), style: { margin: '5px auto' } });
  var btnSim = ui.Button({ label: 'Sim, adicionar', onClick: function() { meuMapa.remove(painelAlerta); callbackSim(); }, style: { color: '#d32f2f', margin: '0 10px' } });
  var btnNao = ui.Button({ label: 'Não', onClick: function() { meuMapa.remove(painelAlerta); }, style: { color: '#2e7d32', margin: '0 10px' } });
  painelBotoes.add(btnNao);
  painelBotoes.add(btnSim);
  painelAlerta.add(titulo);
  painelAlerta.add(texto);
  painelAlerta.add(painelBotoes);
  meuMapa.add(painelAlerta);
}

btn_add_coord.onClick(function() {
  var validadas = verificarECorrigirCoords();
  if (validadas) {
    var coord_str = validadas.lat.toFixed(4) + ', ' + validadas.lon.toFixed(4);
    
    if (lista_coords_array.indexOf(coord_str) !== -1) {
      mostrarConfirmacaoDuplicata('O ponto exato [' + coord_str + '] já existe na sua lista. Repetir coordenadas cria um polígono inválido na maioria dos casos. Deseja registrar essa repetição mesmo assim?', function() {
        lista_coords_array.push(coord_str);
        atualizarTextoListaCoords();
        logInfo('Coordenada repetida forçada pelo usuário: ' + coord_str);
      });
    } else {
      lista_coords_array.push(coord_str);
      atualizarTextoListaCoords();
      logInfo('Coordenada adicionada: ' + coord_str);
    }
  }
});

btn_limpar_coords.onClick(function() {
  lista_coords_array = [];
  atualizarTextoListaCoords();
  logInfo('Lista de coordenadas limpa.');
});

select_modo_processamento.setValue('-- Selecione o Modo de Operação --');

// ============================================================
// MODULO 13: CONSTRUCAO DA GEOMETRIA (FRONTEIRA EXATA) E DATAS
// ============================================================
function obterDatasInterface() {
  var isoInicio = converterDataParaISO(box_inicio.getValue());
  var isoFim = converterDataParaISO(box_fim.getValue());
  if (!isoInicio || !isoFim) return null;

  var partesIni = isoInicio.split('-');
  var partesFim = isoFim.split('-');
  var dIni = new Date(partesIni[0], partesIni[1] - 1, partesIni[2]);
  var dFim = new Date(partesFim[0], partesFim[1] - 1, partesFim[2]);
  var totalDias = Math.floor((dFim.getTime() - dIni.getTime()) / (1000 * 3600 * 24)) + 1;

  var dataIni = ee.Date(isoInicio);
  var dataFim = ee.Date(isoFim);
  var dataFimGEE = dataFim.advance(1, 'day');

  return {
    isoInicio: isoInicio, isoFim: isoFim, 
    dataIni: dataIni, dataFim: dataFim, 
    dataFimGEE: dataFimGEE,
    mesIni: dataIni.get('month'), mesFim: dataFim.get('month'),
    totalDias: totalDias > 0 ? totalDias : 1 
  };
}

function construirRegiaoSelecionada() {
  var tipo = select_abrangencia.getValue();
  var regiao_fc = null, estados_contorno_fc = null, nome_local = null;
  var escala = escalaPorAbrangencia(tipo);
  
  var poligonos_base = null;
  var lista_coords_puras = [];
  var isEstadoGeral = (tipo === 'Estados / Municípios' && !check_filtrar_munis.getValue());

  if (tipo === 'Coordenadas (Lat / Lon)') {
    var subPoligonos = [];
    var coordsAtuais = [];
    
    lista_coords_array.forEach(function(item) {
      if (item === 'NOVA_AREA_BREAK') {
        if (coordsAtuais.length > 0) {
          subPoligonos.push(coordsAtuais);
          coordsAtuais = [];
        }
      } else {
        var parts = item.split(',');
        coordsAtuais.push([parseFloat(String(parts[1]).trim()), parseFloat(String(parts[0]).trim())]);
      }
    });
    
    if (coordsAtuais.length > 0) {
      subPoligonos.push(coordsAtuais);
    }

    var featuresPoly = [];
    
    for (var i = 0; i < subPoligonos.length; i++) {
      if (subPoligonos[i].length < 4) {
        mostrarAlertaTela('⚠️ LOCALIZAÇÃO INVÁLIDA: A Área ' + (i + 1) + ' na sua lista possui menos de 4 coordenadas (vértices) e não forma um polígono fechado. Adicione mais pontos ou exclua os sobressalentes.');
        return null;
      }
      
      var poligono_geom = ee.Geometry.Polygon([subPoligonos[i]]);
      
      featuresPoly.push(ee.Feature(poligono_geom, { 
        'Nome_Local_Export': 'Poligono_' + (i + 1), 
        'Estado': 'Customizado', 
        'Municipio': 'Area_Desenhada', 
        'ID_Ponto': 'Poligono_0' + (i + 1),
        'Longitude': subPoligonos[i][0][0], 
        'Latitude': subPoligonos[i][0][1]
      }));
      
      lista_coords_puras = lista_coords_puras.concat(subPoligonos[i]);
    }

    if (featuresPoly.length === 0) return null;

    poligonos_base = ee.FeatureCollection(featuresPoly);
    estados_contorno_fc = estados.filterBounds(poligonos_base.geometry());
    nome_local = featuresPoly.length > 1 ? 'Multiplos_Poligonos' : 'Poligono_Usuario';
    
  } else if (tipo === 'Estados / Municípios') {
    if (lista_estados_array.length === 0) {
      mostrarAlertaTela('⚠️ Por favor, adicione pelo menos um ESTADO à lista (Passo 2) antes de processar.');
      return null;
    }
    
    var variacoesListaEstados = listaVariacoesBusca(lista_estados_array);
    estados_contorno_fc = estados.filter(ee.Filter.inList('ADM1_NAME', variacoesListaEstados));
    
    if (check_filtrar_munis.getValue()) {
      if (lista_cidades_array.length === 0) {
        mostrarAlertaTela('⚠️ Você marcou a opção de Municípios (Passo 3), mas não adicionou nenhum à lista.');
        return null;
      }
      var variacoesListaCidades = listaVariacoesBusca(lista_cidades_array);
      poligonos_base = municipios.filter(ee.Filter.and(
        ee.Filter.inList('ADM1_NAME', variacoesListaEstados),
        ee.Filter.inList('ADM2_NAME', variacoesListaCidades)
      )).map(function(f) { 
        var coords = f.geometry().centroid().coordinates();
        return f.set('Nome_Local_Export', f.get('ADM2_NAME'))
                .set('Municipio', f.get('ADM2_NAME'))
                .set('Estado', f.get('ADM1_NAME'))
                .set('ID_Ponto', f.get('ADM2_NAME'))
                .set('Longitude', coords.get(0))
                .set('Latitude', coords.get(1));
      });
      
      nome_local = lista_cidades_array.length === 1 ? lista_cidades_array[0] : 'Grupo_Municipios';
    } else {
      poligonos_base = estados.filter(ee.Filter.inList('ADM1_NAME', variacoesListaEstados))
        .map(function(f) { 
          var nomeExp = lista_estados_array.length === 1 ? lista_estados_array[0] : 'Grupo_Estados';
          var coords = f.geometry().centroid().coordinates();
          return f.set('Nome_Local_Export', nomeExp)
                  .set('Municipio', 'Estado_Completo')
                  .set('Estado', f.get('ADM1_NAME'))
                  .set('ID_Ponto', f.get('ADM1_NAME'))
                  .set('Longitude', coords.get(0))
                  .set('Latitude', coords.get(1));
        });
      nome_local = lista_estados_array.length === 1 ? lista_estados_array[0] : 'Grupo_Estados';
    }
  }

  if (!poligonos_base) return null;

  var projNativa = ee.Projection('EPSG:4326', [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]);
  var areaAmostragem = poligonos_base.geometry().buffer(CFG.escalaArea, 1000);

  // [V4 Q1] Pixels de classe 4 (sem BR-DWGD, centro fora do Brasil) saem ANTES da amostragem, e a
  // classe de cada pixel (0 = sem classe) segue até a coluna Qualidade_Pixel. unmask(0, false):
  // pixel sem classe, inclusive fora do footprint do asset, fica com 0 e continua na grade como antes.
  var usarMascaraQ = (APP.mascaraQualidadeOk === true);
  var imgGrade = ee.Image.pixelLonLat();
  if (usarMascaraQ) {
    var classeQualidade = ee.Image(CFG.assets.mascaraQualidade).select('classe').unmask(0, false).rename('classe_q');
    imgGrade = imgGrade.addBands(classeQualidade).updateMask(classeQualidade.neq(4));
  } else {
    logWarn('Máscara de qualidade ausente: rode a etapa 1. Os pixels de borda (classe 4) não foram excluídos e a coluna Qualidade_Pixel sai vazia.');
  }
  
  var grid_pontos_quadrados = imgGrade.sample({
    region: areaAmostragem,
    projection: projNativa, 
    geometries: true,
    dropNulls: true
  }).map(function(f) {
    var coords = f.geometry().coordinates();
    var caixa_exata = f.geometry().buffer(CFG.escalaArea / 2, 100).bounds();
    return f.setGeometry(caixa_exata).set('Lon', coords.get(0), 'Lat', coords.get(1));
  });

  var spatialFilter = ee.Filter.intersects({ leftField: '.geo', rightField: '.geo', maxError: 10 });
  var join = ee.Join.saveAll('munis_intersecao');
  var gridJoin = ee.FeatureCollection(join.apply(grid_pontos_quadrados, poligonos_base, spatialFilter));
  
  var gridComNomes = ee.FeatureCollection(gridJoin.map(function(pixel) {
    var intersecoes = ee.List(pixel.get('munis_intersecao'));
    var listFeat = intersecoes.map(function(intersecao) {
      return ee.Feature(pixel.geometry()).set('polyInfo', intersecao)
               .set('Lat', pixel.get('Lat')).set('Lon', pixel.get('Lon'))
               .set('Classe_Q', usarMascaraQ ? pixel.get('classe_q') : 0); // [V4 Q1]
    });
    return ee.FeatureCollection(listFeat);
  })).flatten();

  gridComNomes = gridComNomes.map(function(f) {
    var poly = ee.Feature(f.get('polyInfo'));
    var muni = ee.String(poly.get('Municipio'));
    var latStr = ee.Number(f.get('Lat')).add(100).format('%.4f'); 
    var lonStr = ee.Number(f.get('Lon')).add(100).format('%.4f');
    var chaveOrdenacao = muni.cat('_').cat(latStr).cat('_').cat(lonStr);
    
    return f.set({
      'ChaveOrdenacao': chaveOrdenacao, 
      'Estado_Ext': poly.get('Estado'), 
      'Muni_Ext': poly.get('Municipio'), 
      'Local_Ext': poly.get('Nome_Local_Export')
    });
  }).sort('ChaveOrdenacao'); 

  // [V4 F2/M06-03] O limite continua (o ID_Ponto sequencial depende da lista), mas não corta mais
  // em silêncio: o número de pares (n_pares) é conferido na avaliação inicial e, acima do limite,
  // o processamento para com aviso.
  var listGrid = gridComNomes.toList(CFG.limitePontosGrade); 
  var indices = ee.List.sequence(0, listGrid.size().subtract(1));
  
  regiao_fc = ee.FeatureCollection(indices.map(function(i) {
    var f = ee.Feature(listGrid.get(i));
    var idxStr = ee.Number(i).add(1).format('%05d'); 
    var pontoCentro = ee.Geometry.Point([f.get('Lon'), f.get('Lat')]);
    var cq = ee.Number(f.get('Classe_Q')); // [V4 Q1] 0 = sem classe

    return ee.Feature(pontoCentro, { 
      'Nome_Local_Export': f.get('Local_Ext'), 
      'Estado': f.get('Estado_Ext'), 
      'Municipio': f.get('Muni_Ext'), 
      'ID_Ponto': ee.String('Ponto_').cat(idxStr), 
      'Latitude': f.get('Lat'), 
      'Longitude': f.get('Lon'),
      // [V4 Q1] classe da máscara de qualidade: 1 = A, 2 = B, 3 = C; vazio sem classe ou sem máscara
      'Qualidade_Pixel': ee.Algorithms.If(cq.eq(1), 'A', ee.Algorithms.If(cq.eq(2), 'B',
                           ee.Algorithms.If(cq.eq(3), 'C', '')))
    });
  }));

  var poligonosExpandidosAntigos = poligonos_base.map(function(f) {
    return f.setGeometry(f.geometry().buffer(CFG.escalaArea / 2, 1000)); 
  });

  return { 
    tipo: tipo, 
    regiao_fc: regiao_fc, 
    poligonos_fc: poligonos_base, 
    poligonos_expandidos_fc: poligonosExpandidosAntigos, 
    estados_contorno_fc: estados_contorno_fc, 
    nome_local: nome_local, 
    escala: escala,
    lista_coords_puras: lista_coords_puras,
    n_pares: gridComNomes.size() // [V4 F2/M06-03] pares pixel × polígono antes do limite (servidor)
  };
}

// [V4 Q1] Verificação única e assíncrona da máscara de qualidade. O painel pode ser aberto antes
// da etapa 1, quando o asset ainda não existe: nesse caso nada quebra, só não há filtro de borda
// e a coluna Qualidade_Pixel sai vazia. Usa o mesmo evaluate com callback do resto do painel e
// confere também a banda 'classe'.
function verificarMascaraQualidade() {
  APP.mascaraQualidadeOk = null;
  ee.Image(CFG.assets.mascaraQualidade).bandNames().evaluate(function(bandas, erro) {
    if (erro || !bandas || bandas.indexOf('classe') === -1) {
      APP.mascaraQualidadeOk = false;
      // [V4 revisão B-10] no App publicado, asset existente mas não compartilhado cai aqui também
      logWarn('Máscara de qualidade ausente ou sem permissão de leitura: rode a etapa 1 ou, com o App publicado, compartilhe SAB_MASCARA_QUALIDADE (Anyone can read). Sem ela, os pixels de borda (classe 4) não são excluídos e a coluna Qualidade_Pixel fica vazia. (' + CFG.assets.mascaraQualidade + ')', erro || '');
      mostrarAlertaTela('Máscara de qualidade ausente ou sem permissão de leitura: rode a etapa 1 ou, com o App publicado, compartilhe SAB_MASCARA_QUALIDADE (Anyone can read). Até lá, o painel funciona sem excluir os pixels de borda (sem BR-DWGD e com o centro fora do Brasil) e a coluna Qualidade_Pixel do CSV fica vazia.');
      return;
    }
    APP.mascaraQualidadeOk = true;
    logInfo('Máscara de qualidade encontrada: os pixels de classe 4 (borda) ficam fora dos pontos de extração.');
  });
}

// [2026.11.1] Verificação única do BR-DWGD (asset de outro usuário). Sem permissão de leitura, o painel segue sem
// a correção dos pixels B e da radiação (como na 2026.10.7) e avisa.
function verificarBRDWGD() {
  APP.brdwgdOk = null;
  ee.ImageCollection(CORR_B.assetBRDWGD).limit(1).size().evaluate(function(n, erro) {
    if (erro || !n) {
      APP.brdwgdOk = false;
      logWarn('BR-DWGD sem permissão de leitura: os pixels B e a radiação dos pixels C saem sem a correção de leitura da 2026.11.1. (' + CORR_B.assetBRDWGD + ')', erro || '');
      return;
    }
    APP.brdwgdOk = true;
    logInfo('BR-DWGD encontrado: correção de leitura dos pixels B e da radiação dos pixels C ligada (dias de 1961 a 2025).');
  });
}

// ============================================================
// MODULO 14: AQUISICAO DA BASE HISTORICA CALIBRADA (COM CORREÇÃO DE LEITURA)
// ============================================================

// Correção de leitura (o banco não é alterado): umidade do solo e escoamento dos dias
// gravados pela V1.0. Mesma regra dos motores Python V1.2 e V1.3:
//  - fator SMAP/ERA5 limitado a fatorMax (só onde o fator original passava disso)
//  - umidade limitada à média SMAP + 3 desvios do mês, no máximo 0.9 m3/m3
// Dias gravados pela V1.2, pela V1.3 ou com patch já vêm corrigidos e passam sem alteração.
var CORR = {
  assetSolo: 'projects/clima-492922/assets/SICSB_SOLO_2015_2025',
  fatorMax: 5.0,
  umidadeMax: 0.9,
  sigmas: 3.0,
  crs: 'EPSG:4326',
  transform: [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
};

function expandirBordaSAB(img) {
  return img.unmask(img.reproject({crs: CORR.crs, crsTransform: CORR.transform})
                       .focalMean(1, 'square', 'pixels'));
}

function montarCorrecaoMes(mes) {
  var solo = ee.Image(CORR.assetSolo + '/Matriz_Solo_' + (mes < 10 ? '0' + mes : String(mes)));

  var fatorCorrecao = function(p) {
    var fatorV10 = expandirBordaSAB(solo.select(p + '_m_smap'))
      .divide(expandirBordaSAB(solo.select(p + '_m_era5')).max(1e-3));
    return ee.Image.constant(1)
      .where(fatorV10.gt(CORR.fatorMax).unmask(0), ee.Image.constant(CORR.fatorMax).divide(fatorV10))
      .unmask(1);
  };

  var teto = function(p) {
    return expandirBordaSAB(solo.select(p + '_m_smap'))
      .add(expandirBordaSAB(solo.select(p + '_s_smap')).multiply(CORR.sigmas))
      .min(CORR.umidadeMax)
      .unmask(CORR.umidadeMax);
  };

  return ee.Image.cat([
    fatorCorrecao('rsup').rename('c_rsup'),
    fatorCorrecao('rsub').rename('c_rsub'),
    fatorCorrecao('ssur').rename('c_ssur'),
    fatorCorrecao('swat').rename('c_swat'),
    teto('ssur').rename('teto_ssur'),
    teto('swat').rename('teto_swat')
  ]);
}

// As 12 correções mensais são montadas uma vez só
var CORRECOES_SOLO_MES = ee.List([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(function(m) {
  return montarCorrecaoMes(m);
}));

function corrigirSoloEscoamentoV10(img) {
  var alg = ee.String(ee.Algorithms.If(
    img.propertyNames().contains('versao_algoritmo'), img.get('versao_algoritmo'), 'V1.0'));
  var corr = ee.Image(CORRECOES_SOLO_MES.get(img.date().get('month').subtract(1)));

  var corrigidas = ee.Image.cat([
    img.select('runoff_sup_mm').multiply(corr.select('c_rsup')).rename('runoff_sup_mm'),
    img.select('runoff_sub_mm').multiply(corr.select('c_rsub')).rename('runoff_sub_mm'),
    img.select('soil_moisture_0_5cm_m3_m3').multiply(corr.select('c_ssur'))
       .min(corr.select('teto_ssur')).rename('soil_moisture_0_5cm_m3_m3'),
    img.select('soil_moisture_0_100cm_m3_m3').multiply(corr.select('c_swat'))
       .min(corr.select('teto_swat')).rename('soil_moisture_0_100cm_m3_m3')
  ]).toFloat();

  // Só os dias da V1.0 recebem a correção; as outras 12 bandas nunca são tocadas
  return ee.Image(ee.Algorithms.If(alg.equals('V1.0'), img.addBands(corrigidas, null, true), img));
}

// ============================================================
// [2026.11.1] CORREÇÃO DE LEITURA DOS PIXELS B E DA RADIAÇÃO DOS PIXELS C (só dias de 1961 a 2025; o banco não muda)
// Auditorias K18 e K19 (03/11/2026): nos pixels B (lagoas e estuários) o motor V1.0 descartou o BR-DWGD e preencheu
// com o ERA5 dos vizinhos (chuva diária 4,8 mm diferente do BR-DWGD, ETo 20%). Aqui eles recebem o BR-DWGD do dia,
// decodificado exatamente como na V1.0 (o mesmo dos pixels A), nas 8 bandas do núcleo. Nos pixels C (sem BR-DWGD),
// a radiação do ERA5 calibrado passava da de céu claro em 18% dos dias: fica limitada a Rso = (0,75 + 2e-5 z) Ra
// (FAO-56, eq. 21 e 37; Allen 1996). A mesma conta está no sab_pedido.py (função corrigir_pixels_b).
// ============================================================
var CORR_B = {
  assetBRDWGD: 'projects/ee-alexandrexavier/assets/BR-DWGD',
  elevacao: 'USGS/SRTMGL1_003',
  fimHistorico: '2026-01-01',          // exclusivo: só os dias até 31/12/2025
  nucleo: ['pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'rs', 'u2', 'vpd']
};
// Dia sem BR-DWGD: imagem com -32768 (o valor ausente do BR-DWGD), que a máscara abaixo descarta
var BR_VAZIO = ee.Image.constant([-32768, -32768, -32768, -32768, -32768, -32768, -32768])
  .rename(['pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs', 'ET']);

function esMagnusB(t) {
  return t.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {T: t});
}

function brdwgdDoDia(data) {
  var br = ee.Image(ee.ImageCollection(CORR_B.assetBRDWGD).filterDate(data, data.advance(1, 'day'))
    .merge(ee.ImageCollection([BR_VAZIO])).first());
  var ok = br.select('pr').gt(-32768);
  var dec = function(b, e, a) { return br.select(b).updateMask(ok).multiply(e).add(a); };
  var tmax = dec('Tmax', 0.00106815, 15.0);
  var tmin = dec('Tmin', 0.00106815, 15.0);
  var rh = dec('RH', 0.39370079, -0.393701).clamp(0, 100);
  var es = esMagnusB(tmax).add(esMagnusB(tmin)).divide(2);
  var vpd = es.subtract(es.multiply(rh).divide(100)).max(0);
  return ee.Image.cat([
    dec('pr', 0.00686666, 225.0).max(0).rename('pr_mm'), tmax.rename('tmax_C'), tmin.rename('tmin_C'),
    rh.rename('RH'), dec('ET', 0.05118110, -0.0511811).rename('et_potencial'),
    dec('Rs', 0.15708661, -0.057087).rename('rs'), dec('u2', 0.05905512, -0.059055).rename('u2'),
    vpd.rename('vpd')
  ]).toFloat();
}

function radiacaoCeuClaro(data) {
  var J = ee.Number(data.getRelative('day', 'year')).add(1);
  var lat = ee.Image.pixelLonLat().select('latitude').multiply(Math.PI / 180);
  var dr = J.multiply(2 * Math.PI / 365).cos().multiply(0.033).add(1);
  var dec = J.multiply(2 * Math.PI / 365).subtract(1.39).sin().multiply(0.409);
  var ws = lat.tan().multiply(dec.tan()).multiply(-1).clamp(-1, 1).acos();
  var ra = ws.multiply(lat.sin()).multiply(dec.sin()).add(lat.cos().multiply(dec.cos()).multiply(ws.sin()))
    .multiply(dr).multiply(24 * 60 / Math.PI * 0.0820);
  return ra.multiply(ee.Image(CORR_B.elevacao).unmask(0).multiply(2e-5).add(0.75)).rename('rso');
}

function corrigirPixelsB(img) {
  var data = img.date();
  var classe = ee.Image(CFG.assets.mascaraQualidade).select('classe').unmask(0, false);
  var br = brdwgdDoDia(data);
  var usarB = classe.eq(2).and(br.select('pr_mm').mask().unmask(0));
  var nucleo = CORR_B.nucleo.map(function(b) {
    return img.select(b).where(usarB, br.select(b)).rename(b);
  });
  var rso = radiacaoCeuClaro(data);
  var rs = ee.Image(nucleo[5]);
  nucleo[5] = rs.where(classe.eq(3).and(rs.gt(rso)), rso).rename('rs');
  var corrigida = img.addBands(ee.Image.cat(nucleo).toFloat(), null, true);
  return ee.Image(ee.Algorithms.If(data.millis().lt(ee.Date(CORR_B.fimHistorico).millis()), corrigida, img));
}

// 1 se a área pedida tem algum pixel B ou C (a correção só entra aí); sem área, 1
function areaTemPixelsBC(geometry) {
  if (!geometry) return ee.Number(1);
  var classe = ee.Image(CFG.assets.mascaraQualidade).select('classe').unmask(0, false);
  var r = classe.eq(2).or(classe.eq(3)).selfMask().reduceRegion({
    reducer: ee.Reducer.anyNonZero(), geometry: geometry.bounds ? geometry.bounds() : geometry,
    crs: CORR.crs, crsTransform: CORR.transform, maxPixels: 1e10
  });
  return ee.Number(ee.Algorithms.If(r.get('classe'), 1, 0));
}

function getSABCollection(geometry, dataIni, dataFimGEE) {
  var col = ee.ImageCollection(CFG.assets.bancoDadosSAB);
  if (geometry) col = col.filterBounds(geometry.bounds ? geometry.bounds() : geometry);
  if (dataIni && dataFimGEE) col = col.filterDate(dataIni, dataFimGEE);

  return col.map(function(img) {
    var nomesAtuais = img.bandNames();

    var imagemPadronizada = ee.Algorithms.If(
      nomesAtuais.contains('precipitation_mm'),
      img.select(
        [
          'precipitation_mm', 'temp_max_C', 'temp_min_C', 'relative_humidity_pct',
          'et_potential_mm', 'et_actual_mm', 'vpd_kpa', 'solar_radiation_mj_m2',
          'wind_speed_m_s', 'soil_temperature_C', 'skin_temperature_C',
          'transpiration_mm', 'surface_runoff_mm', 'subsurface_runoff_mm',
          'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3'
        ],
        CFG.bandasSAB
      ),
      img.select(CFG.bandasSAB)
    );

    return corrigirSoloEscoamentoV10(ee.Image(imagemPadronizada));
  });
}

// [2026.11.1] A coleção que o painel usa: a de cima com a correção dos pixels B e da radiação dos pixels C (dias de
// 1961 a 2025), só quando a área tem pixel B ou C e o BR-DWGD e a máscara podem ser lidos.
function getSABCollectionCorrigida(geometry, dataIni, dataFimGEE) {
  var col = getSABCollection(geometry, dataIni, dataFimGEE);
  if (APP.brdwgdOk !== true || APP.mascaraQualidadeOk !== true) return col;
  return ee.ImageCollection(ee.Algorithms.If(areaTemPixelsBC(geometry), col.map(corrigirPixelsB), col));
}

function getClimateCollection(fonte, geometry, dataIni, dataFimGEE) {
  logStep('Acessando Banco de Dados Oficial (SAB)...');
  return getSABCollectionCorrigida(geometry, dataIni, dataFimGEE);   // [2026.11.1]
}

// ============================================================
// MODULO 14.1: FENOMENOS CLIMATICOS (ENSO / RONI)
// Série OFICIAL do CPC (ERSSTv6) no asset RONI_CPC_v6 (gerado e conferido pelo script de
// auditoria do RONI) + estimativa pelo OISST só para as estações que o CPC ainda não publicou.
// Cada estação é identificada pelo mês central (DJF = janeiro, NDJ = dezembro).
// ============================================================
logStep('Inicializando o módulo ENSO (RONI oficial do CPC + estimativa OISST)...');

var labelsNOAA = ee.List(['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']);

// Geometrias planas: com coordenadas numéricas o Rectangle é geodésico por padrão, e a aresta
// de -180 a 180 viraria uma tira estreita na linha de data.
var regiaoNino34 = ee.Geometry.Rectangle([-170, -5, -120, 5], null, false);
var regiaoTropical = ee.Geometry.Rectangle([-180, -20, 180, 20], null, false);

var colOISST = ee.ImageCollection('NOAA/CDR/OISST/V2_1');
var projOISST = colOISST.first().projection();
var areaPx = ee.Image.pixelArea();

var sstCol = colOISST.select('sst').map(function(img) {
  return img.multiply(0.01).copyProperties(img, ['system:time_start', 'status']);
});

// 1. Só meses fechados (o mês corrente nunca entra). A estimativa só precisa da base
//    1991-2020 (climatologia e fator de variância) e dos meses recentes.
var dataHojeNOAA = ee.Date(Date.now());
var dataLimiteFechada = ee.Date.fromYMD(dataHojeNOAA.get('year'), dataHojeNOAA.get('month'), 1);
var dataInicial = ee.Date('1991-01-01');
var totalMesesFechados = dataLimiteFechada.difference(dataInicial, 'month').round();

// 2. Média mensal. Mês incompleto vira -999 em tudo (descartado adiante). Mês completo mantém a
//    terra mascarada: o fallback antigo com max() pintava os continentes com -999.
var sstMensalImagens = ee.ImageCollection(ee.List.sequence(0, totalMesesFechados.subtract(1)).map(function(offset) {
  var dInicio = dataInicial.advance(offset, 'month');
  var dFim = dInicio.advance(1, 'month');
  var colMes = sstCol.filterDate(dInicio, dFim);
  var nDias = colMes.aggregate_array('system:time_start').distinct().size();
  var completo = nDias.eq(dFim.difference(dInicio, 'day').round());
  var imgMes = ee.Image(ee.Algorithms.If(completo, colMes.mean(),
                        ee.Image.constant(-999).toFloat().rename('sst')));
  var nomeBanda = ee.String('Y').cat(dInicio.get('year').format('%04d'))
                    .cat('M').cat(dInicio.get('month').format('%02d'));
  return imgMes.rename([nomeBanda]).set('system:time_start', dInicio.millis());
}));
var imagemEmpilhadaSST = sstMensalImagens.toBands();

// 3. Médias ponderadas pela área real do pixel, na grade nativa do OISST
function mediaPorArea(pilha, geom) {
  var somar = function(img) {
    return img.reduceRegion({reducer: ee.Reducer.sum(), geometry: geom, crs: projOISST,
                             maxPixels: 1e10, tileScale: 4});
  };
  var num = somar(pilha.multiply(areaPx));
  var den = somar(pilha.mask().multiply(areaPx));
  var nomes = pilha.bandNames();
  return ee.Dictionary.fromLists(nomes, nomes.map(function(b) {
    return ee.Number(num.get(b)).divide(ee.Number(den.get(b)));
  }));
}
var dictNino34 = mediaPorArea(imagemEmpilhadaSST, regiaoNino34);
var dictTrop = mediaPorArea(imagemEmpilhadaSST, regiaoTropical);

// 4. Reconstrução tabular
var listaNomesSST = imagemEmpilhadaSST.bandNames();
var sstMensal = ee.FeatureCollection(listaNomesSST.map(function(nome) {
  var str = ee.String(nome);
  var idxY = str.rindex('Y');
  var ano = ee.Number.parse(str.slice(idxY.add(1), idxY.add(5)));
  var mes = ee.Number.parse(str.slice(idxY.add(6), idxY.add(8)));
  return ee.Feature(null, {
    'ano': ano, 'mes': mes,
    'sst_nino34': dictNino34.get(nome),
    'sst_tropical': dictTrop.get(nome),
    'system:time_start': ee.Date.fromYMD(ano, mes, 1).millis()
  });
})).filter(ee.Filter.gt('sst_nino34', -900));

// 5. Climatologia 1991-2020, anomalias relativas e fator de variância (também 1991-2020,
//    igual ao script de auditoria do RONI)
var mesesENSO = ee.List.sequence(1, 12);
var climaBase = ee.FeatureCollection(mesesENSO.map(function(m) {
  var base = sstMensal.filter(ee.Filter.eq('mes', m))
                      .filter(ee.Filter.gte('ano', 1991))
                      .filter(ee.Filter.lte('ano', 2020));
  return ee.Feature(null, {
    'mes': m,
    'clima_nino34': base.aggregate_mean('sst_nino34'),
    'clima_tropical': base.aggregate_mean('sst_tropical')
  });
}));

var filtroMes = ee.Filter.equals({leftField: 'mes', rightField: 'mes'});
var joinClima = ee.Join.saveFirst('climatologia');
var sstComClima = ee.FeatureCollection(joinClima.apply(sstMensal, climaBase, filtroMes));

var anomalias = sstComClima.map(function(f) {
  var c = ee.Feature(f.get('climatologia'));
  var aNino = ee.Number(f.get('sst_nino34')).subtract(ee.Number(c.get('clima_nino34')));
  var aTrop = ee.Number(f.get('sst_tropical')).subtract(ee.Number(c.get('clima_tropical')));
  return f.set({'anom_nino34': aNino, 'anom_tropical': aTrop, 'anom_relativa': aNino.subtract(aTrop)});
});

var anomBase = anomalias.filter(ee.Filter.and(ee.Filter.gte('ano', 1991), ee.Filter.lte('ano', 2020)));
var stdNino34 = ee.Number(anomBase.reduceColumns(ee.Reducer.stdDev(), ['anom_nino34']).get('stdDev'));
var stdRel = ee.Number(anomBase.reduceColumns(ee.Reducer.stdDev(), ['anom_relativa']).get('stdDev'));
var fatorAjuste = stdNino34.divide(stdRel);

var anomaliasAjustadas = anomalias.map(function(f) {
  return f.set('anom_ajustada', ee.Number(f.get('anom_relativa')).multiply(fatorAjuste));
}).sort('system:time_start');

// 6. Média móvel de 3 meses centrada. Só entra trimestre com os 3 meses presentes.
var filtroJanelaTempo = ee.Filter.maxDifference({
  difference: 1000 * 60 * 60 * 24 * 40,
  leftField: 'system:time_start',
  rightField: 'system:time_start'
});
var joinTrimestral = ee.Join.saveAll('trimestre');
var onisBrutos = joinTrimestral.apply(anomaliasAjustadas, anomaliasAjustadas, filtroJanelaTempo);

var indiceRONI_Sat = ee.FeatureCollection(onisBrutos).map(function(f) {
  var listaValores = ee.List(f.get('trimestre')).map(function(feat) {
    return ee.Feature(feat).get('anom_ajustada');
  });
  var roni = ee.Number(listaValores.reduce(ee.Reducer.mean()));
  var roniArredondado = roni.multiply(10).round().divide(10);
  var sinal = ee.Algorithms.If(roniArredondado.gte(0.5), 1, ee.Algorithms.If(roniArredondado.lte(-0.5), -1, 0));
  var anoNum = ee.Number(f.get('ano'));
  var mesNum = ee.Number(f.get('mes'));
  return ee.Feature(null, {
    'ano': anoNum, 'mes': mesNum,
    'system:time_start': f.get('system:time_start'),
    'RONI': roniArredondado, 'RONI_2c': roni, 'sinal': sinal,
    'chave_join': anoNum.format('%04d').cat('_').cat(mesNum.format('%02d')),
    'Trimestre': labelsNOAA.get(mesNum.subtract(1)),
    'n_meses': listaValores.size(),
    'Fonte': 'Estimativa_OISST'
  });
}).filter(ee.Filter.eq('n_meses', 3));

// =========================================================================
// 7. SÉRIE COMPLETA: OFICIAL DO CPC + ESTIMATIVA OISST DEPOIS DA ÚLTIMA ESTAÇÃO OFICIAL
// =========================================================================
var roniOficial = ee.FeatureCollection(CFG.assets.roniPassado).map(function(f) {
  var ano = ee.Number(f.get('ano'));
  var mes = ee.Number(f.get('mes'));
  var r = ee.Number(f.get('RONI'));
  return f.set({
    'system:time_start': ee.Date.fromYMD(ano, mes, 1).millis(),
    'chave_join': ano.format('%04d').cat('_').cat(mes.format('%02d')),
    'sinal': ee.Algorithms.If(r.gte(0.5), 1, ee.Algorithms.If(r.lte(-0.5), -1, 0))
  });
});
var ultimaOficial = ee.Number(roniOficial.aggregate_max('system:time_start'));
var colecaoCompleta = roniOficial
  .merge(indiceRONI_Sat.filter(ee.Filter.gt('system:time_start', ultimaOficial)))
  .sort('system:time_start');

// Verificação: a regra de 5 estações conta por posição, então a série precisa ser contínua
var mesesEsperados = ee.Date(colecaoCompleta.aggregate_max('system:time_start'))
  .difference(ee.Date(colecaoCompleta.aggregate_min('system:time_start')), 'month').round().add(1);
// As duas verificações abaixo são impressas no Console quando o botão de simulação é clicado
// (imprimir ao carregar obrigaria o painel a calcular o OISST inteiro a cada abertura).

// Fase por episódio: limiar de ±0,5 mantido por pelo menos 5 estações seguidas
var listaSinais = colecaoCompleta.aggregate_array('sinal');
var listaFeaturesRONI = colecaoCompleta.toList(colecaoCompleta.size());
var totalMesesFeitos = listaSinais.size();

var indiceONI_FC = ee.FeatureCollection(ee.List.sequence(0, totalMesesFeitos.subtract(1)).map(function(i) {
  var iNum = ee.Number(i);
  var f = ee.Feature(listaFeaturesRONI.get(iNum));

  var checkWindow = function(offset) {
    var start = iNum.add(offset);
    var end = start.add(4);
    var valid = start.gte(0).and(end.lt(totalMesesFeitos));
    return ee.Algorithms.If(valid,
      ee.List.sequence(start, end).map(function(idx) { return listaSinais.get(idx); }).reduce(ee.Reducer.sum()), 0);
  };

  var w1 = ee.Number(checkWindow(-4));
  var w2 = ee.Number(checkWindow(-3));
  var w3 = ee.Number(checkWindow(-2));
  var w4 = ee.Number(checkWindow(-1));
  var w5 = ee.Number(checkWindow(0));

  var isElNino = w1.eq(5).or(w2.eq(5)).or(w3.eq(5)).or(w4.eq(5)).or(w5.eq(5));
  var isLaNina = w1.eq(-5).or(w2.eq(-5)).or(w3.eq(-5)).or(w4.eq(-5)).or(w5.eq(-5));

  // [V4 F6/M06-06] Fim da série: se o sinal do mês não é nulo e se repete em todas as estações até a
  // última, sem completar as 5 (senão já seria episódio acima), a fase ainda não está definida: a
  // série acabou antes. Só as 4 últimas estações podem cair aqui (antes saíam 'Neutro').
  var sinalI = ee.Number(listaSinais.get(iNum));
  var nAteFim = totalMesesFeitos.subtract(iNum);   // estações do mês i até o fim, inclusive
  var somaAteFim = ee.Number(ee.Algorithms.If(nAteFim.lte(4),
    ee.List.sequence(iNum, totalMesesFeitos.subtract(1)).map(function(idx) { return listaSinais.get(idx); })
      .reduce(ee.Reducer.sum()), 0));
  var isIndefinida = sinalI.abs().eq(1).and(nAteFim.lte(4)).and(somaAteFim.eq(sinalI.multiply(nAteFim)));

  var fase = ee.Algorithms.If(isElNino, 'El Nino', ee.Algorithms.If(isLaNina, 'La Nina',
               ee.Algorithms.If(isIndefinida, 'Indefinida', 'Neutro'))); // [V4 F6/M06-06]
  return f.set('FaseENSO', fase);
}));

// Filtro único de cenário, usado no recorte histórico e na exportação da matriz.
// Categorias de El Niño e La Niña exigem que o mês pertença a um episódio.
function filtroCenario(cenario) {
  var nino = ee.Filter.eq('FaseENSO', 'El Nino');
  var nina = ee.Filter.eq('FaseENSO', 'La Nina');
  var pos = function(a, b) { return ee.Filter.and(ee.Filter.gte('RONI', a), ee.Filter.lt('RONI', b)); };
  var neg = function(a, b) { return ee.Filter.and(ee.Filter.lte('RONI', a), ee.Filter.gt('RONI', b)); };
  var mapa = {
    'Super El Niño (≥ 2.0°C)':          ee.Filter.and(nino, ee.Filter.gte('RONI', 2.0)),
    'El Niño Forte (1.5 a 1.9°C)':      ee.Filter.and(nino, pos(1.5, 2.0)),
    'El Niño Moderado (1.0 a 1.4°C)':   ee.Filter.and(nino, pos(1.0, 1.5)),
    'El Niño Fraco (0.5 a 0.9°C)':      ee.Filter.and(nino, pos(0.5, 1.0)),
    'Anos Neutros':                     ee.Filter.eq('FaseENSO', 'Neutro'),
    'La Niña Fraca (-0.5 a -0.9°C)':    ee.Filter.and(nina, neg(-0.5, -1.0)),
    'La Niña Moderada (-1.0 a -1.4°C)': ee.Filter.and(nina, neg(-1.0, -1.5)),
    'La Niña Forte (-1.5 a -1.9°C)':    ee.Filter.and(nina, neg(-1.5, -2.0)),
    'Super La Niña (≤ -2.0°C)':         ee.Filter.and(nina, ee.Filter.lte('RONI', -2.0))
  };
  // [V4 F6/M06-06] 'Indefinida' e 'Sem_Dado' ficam fora de todos os cenários. As categorias já
  // exigem a fase exata; a exclusão explícita protege contra mudanças futuras no mapa acima.
  var filtroEscolhido = mapa[cenario];
  return filtroEscolhido ? ee.Filter.and(filtroEscolhido,
    ee.Filter.inList('FaseENSO', ['El Nino', 'La Nina', 'Neutro'])) : null;
}

// =========================================================================
// 8. MOTOR PREDITIVO POR ANÁLOGOS
// Compara o RONI atual e a trajetória dos últimos 5 meses com a MESMA estação de anos
// anteriores e conta o que aconteceu LEAD_MESES depois em cada análogo.
// =========================================================================
var LEAD_MESES = 3;        // prevê a estação 3 meses à frente da atual
var N_ANALOGOS = 10;
var EXCLUIR_ULTIMOS = 12;  // o evento em curso não serve de análogo para si mesmo
var PESO_TENDENCIA = 0.5;  // peso da trajetória de 5 meses na semelhança (ajustável)

var executarMotorPreditivo = function() {
  var serie = indiceONI_FC.sort('system:time_start');
  var vals = serie.aggregate_array('RONI');
  var anos = serie.aggregate_array('ano');
  var meses = serie.aggregate_array('mes');
  var n = vals.size();
  var iAtual = n.subtract(1);
  var fAtual = ee.Feature(serie.toList(1, iAtual).get(0));
  var oniAtual = ee.Number(vals.get(iAtual));
  var mesAtual = ee.Number(meses.get(iAtual));
  var tendenciaAtual = oniAtual.subtract(ee.Number(vals.get(iAtual.subtract(5))));
  var variacaoTri = oniAtual.subtract(ee.Number(vals.get(iAtual.subtract(1))));

  var candidatos = ee.FeatureCollection(
    ee.List.sequence(5, n.subtract(1 + EXCLUIR_ULTIMOS)).map(function(i) {
      i = ee.Number(i);
      var v = ee.Number(vals.get(i));
      var t = v.subtract(ee.Number(vals.get(i.subtract(5))));
      return ee.Feature(null, {
        'ano': anos.get(i), 'mes': meses.get(i),
        'similaridade': v.subtract(oniAtual).abs()
                          .add(t.subtract(tendenciaAtual).abs().multiply(PESO_TENDENCIA)),
        'roniEstacao': v, 'trajetoria': t,   // [V4.1 22/10] só para o CSV dos análogos
        'oniFuturo': vals.get(i.add(LEAD_MESES))
      });
    })).filter(ee.Filter.eq('mes', mesAtual));

  var topAnalogos = candidatos.sort('similaridade').limit(N_ANALOGOS);
  var qtdAnalogos = topAnalogos.size();
  var contar = function(filtro) { return topAnalogos.filter(filtro).size(); };
  var entre = function(a, b) { return ee.Filter.and(ee.Filter.gte('oniFuturo', a), ee.Filter.lt('oniFuturo', b)); };
  var entreNeg = function(a, b) { return ee.Filter.and(ee.Filter.lte('oniFuturo', a), ee.Filter.gt('oniFuturo', b)); };
  var pct = function(q) {
    return ee.Algorithms.If(qtdAnalogos.gt(0), ee.Number(q).multiply(100).divide(qtdAnalogos), 0);
  };

  var msgAlerta = ee.Algorithms.If(variacaoTri.gte(0.4),
    ee.String('Alerta: aquecimento de +').cat(variacaoTri.format('%.1f')).cat('°C em relação ao trimestre anterior'),
    ee.Algorithms.If(variacaoTri.lte(-0.4),
      ee.String('Alerta: resfriamento de ').cat(variacaoTri.format('%.1f')).cat('°C em relação ao trimestre anterior'),
      'Dinâmica oceânica estável em relação ao trimestre anterior.'));

  return ee.Dictionary({
    'roniAtual': oniAtual, 'trimestreAtual': fAtual.get('Trimestre'), 'anoAtual': fAtual.get('ano'),
    'fonteAtual': fAtual.get('Fonte'), 'horizonteMeses': LEAD_MESES,
    'anosAnalogos': topAnalogos.aggregate_array('ano'),
    // [V4.1 22/10] só para a apresentação: RONI de cada análogo LEAD_MESES depois, o valor do início da
    // trajetória, a variação do último mês, o mês e a fase da estação atual
    'oniFuturoAnalogos': topAnalogos.aggregate_array('oniFuturo'),
    'roniEstacaoAnalogos': topAnalogos.aggregate_array('roniEstacao'),
    'trajetoriaAnalogos': topAnalogos.aggregate_array('trajetoria'),
    'similaridadeAnalogos': topAnalogos.aggregate_array('similaridade'),
    'pesoTendencia': PESO_TENDENCIA,
    'roniInicioTendencia': vals.get(iAtual.subtract(5)), 'variacaoTri': variacaoTri,
    'mesAtual': mesAtual, 'faseAtual': fAtual.get('FaseENSO'),
    'tendencia': tendenciaAtual, 'msgAlerta': msgAlerta, 'amostrasUsadas': qtdAnalogos,
    'pElNino': pct(contar(ee.Filter.gte('oniFuturo', 0.5))),
    'pLaNina': pct(contar(ee.Filter.lte('oniFuturo', -0.5))),
    'pNeutro': pct(contar(entre(-0.49, 0.5))),
    'pSuperNino': pct(contar(ee.Filter.gte('oniFuturo', 2.0))), 'pForteNino': pct(contar(entre(1.5, 2.0))),
    'pModNino': pct(contar(entre(1.0, 1.5))), 'pFracoNino': pct(contar(entre(0.5, 1.0))),
    'pSuperNina': pct(contar(ee.Filter.lte('oniFuturo', -2.0))), 'pForteNina': pct(contar(entreNeg(-1.5, -2.0))),
    'pModNina': pct(contar(entreNeg(-1.0, -1.5))), 'pFracaNina': pct(contar(entreNeg(-0.5, -1.0))),
    // [V4 M06-15] continuidade da série (conferida no cliente, no clique de Simular): uma estação
    // por mês, sem lacuna e sem repetição
    'mesesEsperados': mesesEsperados, 'nSerie': colecaoCompleta.size(),
    'nChavesDistintas': colecaoCompleta.aggregate_array('chave_join').distinct().size(),
    // [V4 F6/M06-06] estações do fim da série com fase ainda indefinida
    'mesesIndefinida': indiceONI_FC.filter(ee.Filter.eq('FaseENSO', 'Indefinida')).aggregate_array('chave_join')
  });
};

// [V4 IC] Intervalo exato de 95% (Clopper–Pearson) para k desfechos em 10 análogos, em %.
// Tabela fixa: vale só com exatamente 10 análogos efetivos.
var IC95_CLOPPER_PEARSON_N10 = {
  0: [0, 30.8], 1: [0.3, 44.5], 2: [2.5, 55.6], 3: [6.7, 65.2], 4: [12.2, 73.8], 5: [18.7, 81.3],
  6: [26.2, 87.8], 7: [34.8, 93.3], 8: [44.4, 97.5], 9: [55.5, 99.7], 10: [69.2, 100]
};

function textoIC95(pctValor, nAnalogos) {
  if (nAnalogos !== 10) return '(IC indisponível)';
  var k = Math.round(pctValor * nAnalogos / 100);
  var ic = IC95_CLOPPER_PEARSON_N10[k];
  if (!ic) return '(IC indisponível)';
  return '(IC 95%: ' + ic[0].toFixed(1) + '–' + ic[1].toFixed(1) + '%)';
}

// [V4.1 22/10; textos reorganizados na 2026.10.7] Monta os textos do resultado do ENSO a partir do dicionário do motor (só apresentação:
// as probabilidades são as do servidor), em linguagem para leigos: meses por extenso, "acima/abaixo do
// normal" e as siglas e o intervalo de 95% explicados no "Como ler". Cada análogo é classificado pelo
// RONI LEAD_MESES depois, com os mesmos limites do motor; se a contagem do cliente não bater com a do
// servidor, devolve um aviso.
function montarTextosEnso(res) {
  var TRI = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ'];
  var MES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro',
             'outubro', 'novembro', 'dezembro'];
  var dec = function(v) { return (Math.round(Math.abs(v) * 10) / 10).toFixed(1).replace('.', ','); };
  var pct = function(p) { return String(Math.round(p * 10) / 10).replace('.', ',') + '%'; };
  // Trimestre do CPC -> meses por extenso. DJF de um ano começa em dezembro do ano anterior; NDJ termina
  // em janeiro do ano seguinte.
  var periodo = function(k, ano) {
    var m1 = (k + 11) % 12, m3 = (k + 1) % 12;
    var a1 = k === 0 ? ano - 1 : ano, a3 = k === 11 ? ano + 1 : ano;
    return a1 === a3 ? (MES[m1] + ' a ' + MES[m3] + ' de ' + a3)
                     : (MES[m1] + ' de ' + a1 + ' a ' + MES[m3] + ' de ' + a3);
  };
  var mesesSemAno = function(k) { return MES[(k + 11) % 12] + ' a ' + MES[(k + 1) % 12]; };
  var normal = function(v) {
    if (Math.abs(v) < 0.05) return 'na média normal';
    return dec(v) + ' °C ' + (v > 0 ? 'acima' : 'abaixo') + ' do normal';
  };
  var faixa = function(v) {
    if (v >= 2.0) return 'El Niño muito forte (Super El Niño)';
    if (v >= 1.5) return 'El Niño forte';
    if (v >= 1.0) return 'El Niño moderado';
    if (v >= 0.5) return 'El Niño fraco';
    if (v <= -2.0) return 'La Niña muito forte (Super La Niña)';
    if (v <= -1.5) return 'La Niña forte';
    if (v <= -1.0) return 'La Niña moderada';
    if (v <= -0.5) return 'La Niña fraca';
    return null;
  };
  var kAtual = TRI.indexOf(res.trimestreAtual);
  var kAlvo = (kAtual + res.horizonteMeses) % 12;
  var anoAlvo = res.anoAtual + Math.floor((kAtual + res.horizonteMeses) / 12);
  var kIni = (kAtual + 7) % 12;          // 5 trimestres antes do atual
  var anoIni = res.anoAtual - (kAtual < 5 ? 1 : 0);
  var nA = res.amostrasUsadas;
  var v0 = res.roniAtual;

  // [2026.10.7] Textos reorganizados (só apresentação; números e contagens iguais aos da 2026.10.6):
  //   AGORA = tópicos curtos; PRÓXIMOS 3 MESES = resposta curta primeiro, depois a contagem dos anos;
  //   detalhes = anos parecidos e só os avisos que mudam a leitura; nota = "Como ler" (fica escondida).
  var sinal = function(v) { return v > 0.04 ? '+' : (v < -0.04 ? '−' : ''); };

  // 1. Agora
  var titulo = '🌊 AGORA (' + periodo(kAtual, res.anoAtual) + ')';
  var linhas = [];
  var fx = faixa(v0);
  var chaveAtual = res.anoAtual + '_' + ('0' + res.mesAtual).slice(-2);
  var nIndef = (res.mesesIndefinida || []).length;
  var fenomeno = v0 > 0 ? 'El Niño' : 'La Niña';
  if (fx === null) {
    linhas.push('• Situação: neutro (nem El Niño, nem La Niña).');
  } else if (res.faseAtual === 'Indefinida' && (res.mesesIndefinida || []).indexOf(chaveAtual) !== -1) {
    // [V4.1 22/10, correção 1] a regra dos 5 trimestres é a da tabela histórica; o CPC pode já ter
    // declarado condições de El Niño/La Niña no boletim mensal (o painel não sabe o alerta em vigor)
    linhas.push('• Situação: já no nível de ' + fx + '. A tabela histórica do CPC/NOAA só registra o episódio ' +
                'depois de 5 trimestres seguidos ' + (v0 > 0 ? 'acima de +0,5 °C' : 'abaixo de −0,5 °C') +
                ' (até agora são ' + nIndef + '), mas o CPC pode já ter declarado condições de ' + fenomeno +
                ' no boletim do mês: confira o alerta no site do CPC.');
  } else if (res.faseAtual === 'El Nino' || res.faseAtual === 'La Nina') {
    linhas.push('• Situação: ' + fx + ', episódio já confirmado.');
  } else {
    linhas.push('• Situação: no nível de ' + fx + ', mas ainda não forma um episódio confirmado.');
  }
  linhas.push('• Temperatura do mar: ' + normal(v0) + ' (índice RONI ' + sinal(v0) + dec(v0) + ' °C).');
  var t = res.tendencia;
  var verbo = t > 0.04 ? 'esquentou ' + dec(t) + ' °C' : (t < -0.04 ? 'esfriou ' + dec(t) + ' °C' : 'ficou estável');
  linhas.push('• Últimos 5 meses: ' + verbo + ' (em ' + periodo(kIni, anoIni) + ' estava ' +
              normal(res.roniInicioTendencia) + ').');
  linhas.push('• Fonte: ' + (res.fonteAtual === 'Estimativa_OISST' ?
    'estimativa provisória por satélite (OISST); o CPC/NOAA ainda não publicou este trimestre.' :
    'CPC/NOAA (valor oficial).'));

  var vt = res.variacaoTri;
  var variacao, cor;
  if (vt >= 0.4) { variacao = '⚠️ Último mês: subiu ' + dec(vt) + ' °C (aquecimento rápido).'; cor = '#d73027'; }
  else if (vt <= -0.4) { variacao = '⚠️ Último mês: caiu ' + dec(vt) + ' °C (resfriamento rápido).'; cor = '#1d70b8'; }
  else if (vt > 0.04) { variacao = '• Último mês: subiu ' + dec(vt) + ' °C, sem mudança brusca.'; cor = '#0b5d1e'; }
  else if (vt < -0.04) { variacao = '• Último mês: caiu ' + dec(vt) + ' °C, sem mudança brusca.'; cor = '#0b5d1e'; }
  else { variacao = '• Último mês: praticamente igual.'; cor = '#0b5d1e'; }

  // 2. Análogos classificados pelo RONI LEAD_MESES depois (limites iguais aos do motor)
  var anos = res.anosAnalogos || [], fut = res.oniFuturoAnalogos || [];
  var g = {sNino: [], fNino: [], mNino: [], frNino: [], neutro: [], frNina: [], mNina: [], fNina: [], sNina: []};
  for (var i = 0; i < anos.length; i++) {
    var v = fut[i], a = anos[i];
    if (v >= 2.0) g.sNino.push(a); else if (v >= 1.5) g.fNino.push(a);
    else if (v >= 1.0) g.mNino.push(a); else if (v >= 0.5) g.frNino.push(a);
    else if (v <= -2.0) g.sNina.push(a); else if (v <= -1.5) g.fNina.push(a);
    else if (v <= -1.0) g.mNina.push(a); else if (v <= -0.5) g.frNina.push(a);
    else g.neutro.push(a);
  }
  Object.keys(g).forEach(function(c) { g[c].sort(function(x, y) { return x - y; }); });
  var nNino = g.sNino.length + g.fNino.length + g.mNino.length + g.frNino.length;
  var nNina = g.sNina.length + g.fNina.length + g.mNina.length + g.frNina.length;
  var aviso = null;
  if (nA > 0 && (Math.round(res.pElNino * nA / 100) !== nNino || Math.round(res.pLaNina * nA / 100) !== nNina ||
                 Math.round(res.pNeutro * nA / 100) !== g.neutro.length)) {
    aviso = 'ENSO: a classificação dos análogos no painel não bate com a contagem do servidor.';
  }

  var tituloPrevisao = '🔮 PRÓXIMOS 3 MESES (' + periodo(kAlvo, anoAlvo) + ')';
  var ordenados = anos.slice().sort(function(x, y) { return x - y; });
  var antes1961 = ordenados.filter(function(a) { return a < 1961; });   // sem dados de clima no SAB
  var listaAnos = function(l) {
    return l.length <= 1 ? l.join('') : l.slice(0, -1).join(', ') + ' e ' + l[l.length - 1];
  };
  var fases = [['El Niño', nNino, res.pElNino], ['neutralidade', g.neutro.length, res.pNeutro], ['La Niña', nNina, res.pLaNina]];
  var porQtd = fases.slice().sort(function(x, y) { return y[1] - x[1]; });
  var dom = porQtd[0];

  // Resposta curta: a fase que mais apareceu nos anos parecidos, com a palavra de chance pela contagem
  var analogos;
  if (nA === 0) {
    analogos = 'Nenhum ano parecido foi encontrado no histórico.';
  } else if (porQtd[1][1] === dom[1]) {
    analogos = 'Resposta curta: resultado dividido. ' + (porQtd[2][1] === dom[1] ?
      'El Niño, neutralidade e La Niña apareceram no mesmo número de anos parecidos.' :
      'Nos anos parecidos, ' + porQtd[0][0] + ' e ' + porQtd[1][0] + ' apareceram ' + dom[1] + ' vezes cada.') +
      '\nComo ficaram os ' + nA + ' anos parecidos:';
  } else {
    var chance = dom[1] === nA ? 'muito provável' : (dom[1] / nA >= 0.7 ? 'provável' :
                 (dom[1] / nA > 0.5 ? 'um pouco mais provável que as outras opções' : 'incerto: o mais frequente, mas sem maioria'));
    analogos = 'Resposta curta: ' + (dom[0] === 'neutralidade' ? 'neutralidade' : dom[0]) + ' ' + chance +
               ' (' + dom[1] + ' dos ' + nA + ' anos mais parecidos com agora tiveram ' +
               (dom[0] === 'neutralidade' ? 'neutralidade' : dom[0]) + ' nesses meses).' +
               '\nComo ficaram os ' + nA + ' anos parecidos:';
  }

  var qtd = function(k) { return k + ' de ' + nA + (nA === 1 ? ' ano' : ' anos'); };
  var sub = function(nome, l) { return l.length ? '\n   • ' + nome + ': ' + listaAnos(l) : ''; };
  var elnino = '🔥 El Niño: ' + qtd(nNino) + ' (' + pct(res.pElNino) + ')' +
    sub('muito forte (+2,0 °C ou mais)', g.sNino) + sub('forte (+1,5 a +1,9 °C)', g.fNino) +
    sub('moderado (+1,0 a +1,4 °C)', g.mNino) + sub('fraco (+0,5 a +0,9 °C)', g.frNino);
  var neutro = '⚪ Neutro: ' + qtd(g.neutro.length) + ' (' + pct(res.pNeutro) + ')' +
    (g.neutro.length ? '\n   • ' + listaAnos(g.neutro) : '');
  var lanina = '❄️ La Niña: ' + qtd(nNina) + ' (' + pct(res.pLaNina) + ')' +
    sub('fraca (−0,5 a −0,9 °C)', g.frNina) + sub('moderada (−1,0 a −1,4 °C)', g.mNina) +
    sub('forte (−1,5 a −1,9 °C)', g.fNina) + sub('muito forte (−2,0 °C ou menos)', g.sNina);

  // 3. Detalhes (sempre visíveis): anos parecidos e só os avisos que mudam a leitura
  var det = [];
  var avisoForca = null;
  if (nA > 0) {
    det.push('📅 Anos parecidos: ' + listaAnos(ordenados) + ' (o mais parecido foi ' + anos[0] + ').');
    var trajs = res.trajetoriaAnalogos || [];
    if (trajs.length && dom[0] !== 'neutralidade') {
      var iMaisRapido = 0;
      for (var j = 1; j < trajs.length; j++) {
        if ((res.tendencia >= 0 ? trajs[j] > trajs[iMaisRapido] : trajs[j] < trajs[iMaisRapido])) iMaisRapido = j;
      }
      var tMax = trajs[iMaisRapido];
      var maisRapidoAgora = res.tendencia >= 0 ? res.tendencia > tMax + 0.04 : res.tendencia < tMax - 0.04;
      if (maisRapidoAgora && Math.abs(res.tendencia) >= 0.5) {
        // [V4.1 22/10, correção 4] evento mais rápido que todos os análogos: força subestimada
        var verboT = res.tendencia >= 0 ? 'aquecimento' : 'resfriamento';
        avisoForca = '⚠️ Atenção: o ' + verboT + ' de agora (' + sinal(res.tendencia) + dec(res.tendencia) +
                     ' °C em 5 meses) é maior que o de todos os anos parecidos (no máximo ' +
                     (tMax >= 0 ? '+' : '−') + dec(tMax) + ' °C, em ' + anos[iMaisRapido] + '). Por isso, a força ' +
                     'real tende a ser maior que a indicada aqui.';
        det.push(avisoForca);
      }
    }
    det.push('🌦️ Como foram a chuva e a temperatura na sua região nesses anos? Use o item B, logo abaixo. ' +
             'Os dados de clima começam em 1961' +
             (antes1961.length ? ': ' + listaAnos(antes1961) + (antes1961.length === 1 ? ' fica' : ' ficam') +
              ' de fora.' : '.'));
  }
  det.push('Não é a previsão oficial: compare com a do CPC/NOAA.');
  var detalhes = det.join('\n');

  // 4. Como ler (atrás do botão). Intervalo de 95% (Clopper–Pearson, k de 10) em palavras, só para o
  // resultado principal e para a intensidade mais frequente; cobre só o tamanho da amostra.
  var ic = function(p) {
    var m = textoIC95(p, nA).match(/IC 95%: ([0-9.]+)–([0-9.]+)%/);
    return m ? [Math.round(parseFloat(m[1])), Math.round(parseFloat(m[2]))] : null;
  };
  var faixaTxt = function(p) { var x = ic(p); return 'entre ' + x[0] + '% e ' + x[1] + '%'; };
  var itens = ['• Como é feita: procuramos no histórico, desde 1950, os ' + nA + ' anos em que o oceano estava mais ' +
               'parecido com o de agora nesta mesma época (' + mesesSemAno(kAtual) + '), olhando o valor e a ' +
               'tendência dos últimos 5 meses. Depois vimos o que o oceano fez ' + res.horizonteMeses + ' meses ' +
               'depois (' + mesesSemAno(kAlvo) + ') naqueles anos. As porcentagens são a contagem desses anos.'];
  if (nA > 0 && ic(dom[2])) {
    var nomeDom = dom[0] === 'neutralidade' ? 'Neutralidade' : dom[0];
    var conta = 'Fazendo a conta da margem de erro (intervalo de confiança de 95%), a chance de ' +
                (dom[0] === 'neutralidade' ? 'neutralidade' : dom[0]) + ' fica ' + faixaTxt(dom[2]);
    if (dom[1] === nA) {
      itens.push('• Por que não é certeza, se deu ' + nA + ' em ' + nA + '? Porque ' + nA + ' anos é pouco. ' + conta +
                 ': muito provável, mas não garantido.');
    } else {
      itens.push('• Quão certo é? ' + nomeDom + ' apareceu em ' + dom[1] + ' dos ' + nA + ' anos (' + pct(dom[2]) +
                 '), mas ' + nA + ' anos é pouco. ' + conta + '.');
    }
    var subs = dom[0] === 'El Niño' ? [['muito forte', g.sNino], ['forte', g.fNino], ['moderado', g.mNino], ['fraco', g.frNino]] :
               (dom[0] === 'La Niña' ? [['fraca', g.frNina], ['moderada', g.mNina], ['forte', g.fNina], ['muito forte', g.sNina]] : []);
    var comAnos = subs.filter(function(x) { return x[1].length; });
    if (comAnos.length > 1) {
      var maior = comAnos.slice().sort(function(x, y) { return y[1].length - x[1].length; })[0];
      var pm = 100 * maior[1].length / nA;
      itens.push('• A força do fenômeno é bem mais incerta: "' + maior[0] + '" apareceu em ' + maior[1].length + ' dos ' +
                 nA + ' anos (' + pct(pm) + '), mas pela mesma conta pode ficar ' + faixaTxt(pm) + '.');
    }
    // [V4.1 22/10, correção 4] limite do método: não passa do maior valor visto nos anos parecidos
    if (fut.length && dom[0] !== 'neutralidade') {
      var extremo = dom[0] === 'El Niño' ? Math.max.apply(null, fut) : Math.min.apply(null, fut);
      itens.push('• O método só repete o que já aconteceu: entre os ' + nA + ' anos parecidos, o RONI de ' +
                 mesesSemAno(kAlvo) + ' foi no ' + (dom[0] === 'El Niño' ? 'máximo +' : 'mínimo −') + dec(extremo) +
                 ' °C. Ele não consegue indicar um evento mais forte que esse e, em eventos recordes, subestima a ' +
                 'força. Compare com as probabilidades de intensidade do CPC/NOAA.');
    }
    itens.push('• Essa margem de erro leva em conta só o número pequeno de anos. Ela não cobre o erro do próprio ' +
               'método: o oceano pode não repetir o que fez no passado.');
  } else {
    itens.push('• A margem de erro (intervalo de confiança de 95%) só é calculada com exatamente 10 anos parecidos.');
  }
  itens.push('• O que é o RONI: o índice do CPC/NOAA que compara a temperatura da superfície do mar no centro-leste ' +
             'do Pacífico equatorial com a média de todos os oceanos tropicais, em médias de 3 meses. Acima de ' +
             '+0,5 °C indica El Niño; abaixo de −0,5 °C, La Niña; entre os dois, neutro. Na tabela histórica do ' +
             'CPC, um episódio só é registrado quando isso dura 5 trimestres seguidos.');   // [V4.1 22/10, correção 1]
  itens.push('• Siglas: o CPC/NOAA nomeia cada trimestre pelas iniciais dos meses em inglês (' + res.trimestreAtual +
             ' = ' + periodo(kAtual, res.anoAtual) + '; ' + TRI[kAlvo] + ' = ' + periodo(kAlvo, anoAlvo) +
             '). Elas aparecem nos arquivos CSV da previsão e do item B.');
  var nota = 'ℹ️ Como ler\n' + itens.join('\n');

  return {titulo: titulo, situacao: linhas.join('\n'), variacao: variacao, corVariacao: cor,
          tituloPrevisao: tituloPrevisao, analogos: analogos, elnino: elnino, neutro: neutro, lanina: lanina,
          detalhes: detalhes, avisoForca: avisoForca, nota: nota, aviso: aviso};
}

// [V4.1 22/10] Linhas dos CSV da previsão ENSO, a partir do mesmo dicionário mostrado na tela (função pura,
// testada no teste_06_enso.js). Textos sem acento, para o Excel abrir sem estragar os caracteres.
function montarLinhasExportEnso(res, dataExtracao) {
  var TRI = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ'];
  var r1 = function(v) { return Math.round(v * 10) / 10; };
  var r2 = function(v) { return Math.round(v * 100) / 100; };
  var nA = res.amostrasUsadas;
  var kAtual = TRI.indexOf(res.trimestreAtual);
  var kAlvo = (kAtual + res.horizonteMeses) % 12;
  var anoAlvo = res.anoAtual + Math.floor((kAtual + res.horizonteMeses) / 12);
  var classe = function(v) {
    if (v >= 2.0) return ['El Nino', 'Muito forte (Super)'];
    if (v >= 1.5) return ['El Nino', 'Forte'];
    if (v >= 1.0) return ['El Nino', 'Moderado'];
    if (v >= 0.5) return ['El Nino', 'Fraco'];
    if (v <= -2.0) return ['La Nina', 'Muito forte (Super)'];
    if (v <= -1.5) return ['La Nina', 'Forte'];
    if (v <= -1.0) return ['La Nina', 'Moderada'];
    if (v <= -0.5) return ['La Nina', 'Fraca'];
    return ['Neutro', '-'];
  };
  var ic = function(p) {
    var m = textoIC95(p, nA).match(/IC 95%: ([0-9.]+)–([0-9.]+)%/);
    return m ? m[1] + ' a ' + m[2] : 'indisponivel';
  };
  var anos = res.anosAnalogos || [];
  var analogos = anos.map(function(a, i) {
    var c = classe(res.oniFuturoAnalogos[i]);
    var o = {'Ano': a, 'Ordem_Semelhanca': i + 1};   // sem chaves computadas (ES5 do Code Editor)
    // [V4.1 22/10, correção 3] RONI e trajetória sempre com 1 casa ("2.0", não "2"); distância com 2
    o['RONI_' + res.trimestreAtual + '_C'] = r1(res.roniEstacaoAnalogos[i]).toFixed(1);
    o['Trajetoria_5_Meses_C'] = r1(res.trajetoriaAnalogos[i]).toFixed(1);
    o['Distancia_Semelhanca'] = r2(res.similaridadeAnalogos[i]).toFixed(2);
    o['RONI_' + TRI[kAlvo] + '_C'] = r1(res.oniFuturoAnalogos[i]).toFixed(1);
    o['Fase_' + TRI[kAlvo]] = c[0];
    o['Intensidade_' + TRI[kAlvo]] = c[1];
    return o;
  }).sort(function(x, y) { return x.Ano - y.Ano; });
  var conta = function(fase, intens) {
    return analogos.filter(function(x) {
      return x['Fase_' + TRI[kAlvo]] === fase && (!intens || x['Intensidade_' + TRI[kAlvo]] === intens);
    }).length;
  };
  var p = function(k) { return nA > 0 ? r1(100 * k / nA) : 0; };
  var vt = res.variacaoTri;
  var resumo = {
    'Data_Extracao': dataExtracao,
    'Estacao_Atual': res.trimestreAtual + ' ' + res.anoAtual,
    'RONI_Atual_C': r1(res.roniAtual).toFixed(1), 'Fonte_Valor_Atual': res.fonteAtual, 'Fase_Atual': res.faseAtual,
    'Tendencia_5_Meses_C': r1(res.tendencia).toFixed(1), 'Variacao_Ultimo_Mes_C': r1(vt).toFixed(1),
    'Leitura_Ultimo_Mes': vt >= 0.4 ? 'aquecimento rapido' : (vt <= -0.4 ? 'resfriamento rapido' : 'sem mudanca brusca'),
    'Estacao_Prevista': TRI[kAlvo] + ' ' + anoAlvo, 'Horizonte_Meses': res.horizonteMeses,
    'N_Analogos': nA, 'Peso_Trajetoria': res.pesoTendencia,
    'Anos_Analogos': analogos.map(function(x) { return x.Ano; }).join(';'),
    'Analogo_Mais_Parecido': anos[0],
    'Prob_El_Nino_pct': res.pElNino, 'IC95_El_Nino_pct': ic(res.pElNino),
    'Prob_Neutro_pct': res.pNeutro, 'IC95_Neutro_pct': ic(res.pNeutro),
    'Prob_La_Nina_pct': res.pLaNina, 'IC95_La_Nina_pct': ic(res.pLaNina),
    'Prob_El_Nino_Muito_Forte_pct': p(conta('El Nino', 'Muito forte (Super)')),
    'Prob_El_Nino_Forte_pct': p(conta('El Nino', 'Forte')),
    'Prob_El_Nino_Moderado_pct': p(conta('El Nino', 'Moderado')),
    'Prob_El_Nino_Fraco_pct': p(conta('El Nino', 'Fraco')),
    'Prob_La_Nina_Fraca_pct': p(conta('La Nina', 'Fraca')),
    'Prob_La_Nina_Moderada_pct': p(conta('La Nina', 'Moderada')),
    'Prob_La_Nina_Forte_pct': p(conta('La Nina', 'Forte')),
    'Prob_La_Nina_Muito_Forte_pct': p(conta('La Nina', 'Muito forte (Super)')),
    'Observacao': 'Probabilidade = fracao dos anos analogos com a fase na estacao prevista; IC95 exato de Clopper-Pearson ' +
                  '(so para 10 analogos). Estimativa estatistica, nao e a previsao oficial do CPC/NOAA.'
  };
  var colsAnalogos = ['Ano', 'Ordem_Semelhanca', 'RONI_' + res.trimestreAtual + '_C', 'Trajetoria_5_Meses_C',
                      'Distancia_Semelhanca', 'RONI_' + TRI[kAlvo] + '_C', 'Fase_' + TRI[kAlvo], 'Intensidade_' + TRI[kAlvo]];
  return {resumo: resumo, colsResumo: Object.keys(resumo), analogos: analogos, colsAnalogos: colsAnalogos,
          sufixo: TRI[kAlvo] + '_' + anoAlvo};
}

// [V4.1 22/10] Lista legível dos meses que o filtro histórico usa: cada mês do calendário é classificado
// pelo trimestre do CPC centrado nele (o mesmo pareamento do filtrarHistoricoPorENSO, pela chave AAAA_MM).
// Entrada: lista de {ano, mes, RONI, FaseENSO, Fonte}. Saída sem acentos, em ordem cronológica.
function montarListaMesesEnso(lista) {
  var TRI = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ'];
  var MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  var MESX = ['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro',
              'outubro', 'novembro', 'dezembro'];
  var FASE = {'El Nino': 'El Nino', 'La Nina': 'La Nina', 'Neutro': 'Neutro', 'Indefinida': 'Indefinida (episodio em aberto)'};
  var intensidade = function(fase, v) {
    if (fase === 'El Nino') return v >= 2.0 ? 'Muito forte (Super)' : (v >= 1.5 ? 'Forte' : (v >= 1.0 ? 'Moderado' : 'Fraco'));
    if (fase === 'La Nina') return v <= -2.0 ? 'Muito forte (Super)' : (v <= -1.5 ? 'Forte' : (v <= -1.0 ? 'Moderada' : 'Fraca'));
    return '-';
  };
  return lista.slice().sort(function(a, b) { return (a.ano - b.ano) || (a.mes - b.mes); }).map(function(e) {
    var k = e.mes - 1;
    var m1 = (k + 11) % 12, m3 = (k + 1) % 12;
    var a1 = k === 0 ? e.ano - 1 : e.ano, a3 = k === 11 ? e.ano + 1 : e.ano;
    var periodo = MES[m1] + '/' + a1 + ' a ' + MES[m3] + '/' + a3;
    return {
      'Ano': e.ano, 'Mes': e.mes, 'Mes_Nome': MESX[k],
      'Trimestre_CPC': TRI[k], 'Meses_do_Trimestre': periodo,
      'RONI_C': (Math.round(e.RONI * 10) / 10).toFixed(1),   // [V4.1 22/10, correção 3]
      'Fase': FASE[e.FaseENSO] || e.FaseENSO, 'Intensidade': intensidade(e.FaseENSO, e.RONI),
      'Fonte_RONI': e.Fonte === 'Estimativa_OISST' ? 'Estimativa OISST (provisoria)' : 'CPC/NOAA'
    };
  });
}

// [V4.1 22/10] Link de download direto ao lado do botão (funciona no App publicado, sem a aba Tasks).
function gerarLinkCsvEnso(fc, colunas, nomeArquivo, label) {
  label.style().set({shown: true, color: '#555555', fontWeight: 'normal'});
  label.setUrl('');   // sem link enquanto o novo não fica pronto
  label.setValue('⏳ Gerando o link de ' + nomeArquivo + '.csv...');
  fc.getDownloadURL('csv', colunas, nomeArquivo, function(url, erro) {
    if (erro || !url) {
      label.setValue('❌ Não foi possível gerar o link de ' + nomeArquivo + '. Tente de novo.');
      label.style().set({color: '#d32f2f', fontWeight: 'bold'});
      logError('ENSO: falha ao gerar o link de ' + nomeArquivo, erro || '');
      return;
    }
    label.setValue('⬇️ Baixar ' + nomeArquivo + '.csv');
    label.setUrl(url);
    label.style().set({color: '#1d70b8', fontWeight: 'bold'});
  });
}

btn_calcular_enso.onClick(function() {
    // [V4 M06-15] a continuidade é impressa como true/false dentro do evaluate abaixo
    print('RONI: fator de variância do OISST (1991-2020)', fatorAjuste);
    painel_resultados_enso.style().set('shown', true);
    btn_calcular_enso.setDisabled(true);
    btn_calcular_enso.setLabel('⏳ Calculando probabilidades oceânicas...');
    btn_exportar_enso.style().set('shown', false);

    label_status_enso.setValue('Buscando os anos parecidos no histórico...');
    label_situacao_enso.setValue('');      // [V4.1 22/10]
    label_titulo_prev_enso.setValue('');   // [V4.1 22/10]
    label_analogos_enso.setValue('');      // [V4.1 22/10]
    label_alerta_enso.setValue('');
    label_prob_elnino.setValue('');
    label_prob_lanina.setValue('');
    label_prob_neutro.setValue('');
    label_nota_ic.setValue(''); // [V4 IC]
    label_detalhes_enso.setValue('');                 // [2026.10.7]
    label_nota_ic.style().set('shown', false);
    btn_como_ler_enso.style().set('shown', false);
    btn_como_ler_enso.setLabel('ℹ️ Como ler este resultado');

    executarMotorPreditivo().evaluate(function(res, erro) {
        btn_calcular_enso.setDisabled(false);
        btn_calcular_enso.setLabel('🔄 Atualizar');

        if (erro || !res) {
            label_status_enso.setValue('❌ Falha ao calcular previsão.' + (erro ? ' ' + erro : ''));
            return;
        }

        // [V4 M06-15] A regra das 5 estações e os análogos (i-5, i+3) contam por posição: com lacuna
        // ou repetição na série, o resultado sairia errado. Nesse caso, avisa e não mostra nada.
        var serieContinua = (res.nSerie === res.mesesEsperados) && (res.nChavesDistintas === res.nSerie);
        print('RONI: série mensal contínua?', serieContinua);
        // [V4 F6/M06-06] estações do fim da série ainda sem fase definida
        print('RONI: estações com fase Indefinida no fim da série: ' + res.mesesIndefinida.length, res.mesesIndefinida);
        if (!serieContinua) {
            label_status_enso.setValue('❌ A série do RONI tem lacuna ou repetição (' + res.nSerie + ' estações, ' +
              res.nChavesDistintas + ' meses distintos, ' + res.mesesEsperados + ' esperados). ' +
              'A simulação não foi mostrada. Confira o asset ' + CFG.assets.roniPassado + ' (etapa 2).');
            logError('RONI: série mensal não contínua; simulação ENSO suspensa.',
              {estacoes: res.nSerie, mesesDistintos: res.nChavesDistintas, mesesEsperados: res.mesesEsperados});
            return;
        }

        // [V4.1 22/10] Textos montados por montarTextosEnso (função pura, testada no teste_06_enso.js)
        var t = montarTextosEnso(res);
        ultimoResEnso = res;   // [V4.1 22/10] o CSV usa exatamente o resultado mostrado na tela
        label_link_enso_resumo.style().set('shown', false);
        label_link_enso_analogos.style().set('shown', false);
        [label_status_enso, label_situacao_enso, label_alerta_enso, label_titulo_prev_enso, label_analogos_enso,
         label_prob_elnino, label_prob_neutro, label_prob_lanina, label_detalhes_enso, label_nota_ic].forEach(function(lb) {
            lb.style().set('whiteSpace', 'pre-wrap');
        });
        label_status_enso.setValue(t.titulo);
        label_situacao_enso.setValue(t.situacao);
        label_alerta_enso.setValue(t.variacao);
        label_alerta_enso.style().set('color', t.corVariacao);
        label_titulo_prev_enso.setValue(t.tituloPrevisao);
        label_analogos_enso.setValue(t.analogos);
        label_prob_elnino.setValue(t.elnino);
        label_prob_neutro.setValue(t.neutro);
        label_prob_lanina.setValue(t.lanina);
        label_detalhes_enso.setValue(t.detalhes);   // [2026.10.7]
        label_nota_ic.setValue(t.nota);
        btn_como_ler_enso.style().set('shown', true);
        if (t.aviso) logError(t.aviso, {anos: res.anosAnalogos, oniFuturo: res.oniFuturoAnalogos});

        btn_exportar_enso.style().set('shown', true);
    });
});

var ultimoResEnso = null;   // [V4.1 22/10] último resultado mostrado na tela

btn_exportar_enso.onClick(function() {
    // [V4.1 22/10] Gera os CSV a partir do resultado já mostrado (sem recalcular) e mostra os links aqui.
    if (!ultimoResEnso) {
        label_link_enso_resumo.style().set({shown: true, color: '#d32f2f'});
        label_link_enso_resumo.setValue('Clique antes em Simular Cenário Futuro.');
        return;
    }
    var hoje = new Date();
    var dataTxt = hoje.getFullYear() + '-' + ('0' + (hoje.getMonth() + 1)).slice(-2) + '-' + ('0' + hoje.getDate()).slice(-2);
    var L = montarLinhasExportEnso(ultimoResEnso, dataTxt);
    gerarLinkCsvEnso(ee.FeatureCollection([ee.Feature(null, L.resumo)]), L.colsResumo,
                     'Previsao_ENSO_' + L.sufixo + '_Resumo', label_link_enso_resumo);
    gerarLinkCsvEnso(ee.FeatureCollection(L.analogos.map(function(x) { return ee.Feature(null, x); })), L.colsAnalogos,
                     'Previsao_ENSO_' + L.sufixo + '_Anos_Analogos', label_link_enso_analogos);
});

btn_exportar_historico_enso.onClick(function() {
  // [V4.1 22/10] Lista legível (um mês por linha) dos meses que o filtro usa, por link direto. Antes era
  // a matriz no formato da NOAA (anos x trimestres, quase toda vazia) enviada para a aba Tasks.
  var cenario = select_enso.getValue();
  var filtro = filtroCenario(cenario);
  var fcSel = (filtro ? indiceONI_FC.filter(filtro) : indiceONI_FC)
    .filter(ee.Filter.lte('system:time_start', dataLimiteFechada.millis()))
    .filter(ee.Filter.gte('ano', 1961));   // os dados de clima do SAB começam em 1961
  var nomeCenario = infoCenarioEnso(cenario).arquivo || 'Todos_os_meses';
  btn_exportar_historico_enso.setDisabled(true);
  label_link_enso_hist.style().set({shown: true, color: '#555555', fontWeight: 'normal'});
  label_link_enso_hist.setUrl('');
  label_link_enso_hist.setValue('⏳ Montando a lista de meses...');
  fcSel.reduceColumns(ee.Reducer.toList(5), ['ano', 'mes', 'RONI', 'FaseENSO', 'Fonte']).get('list')
    .evaluate(function(linhas, erro) {
      btn_exportar_historico_enso.setDisabled(false);
      if (erro || !linhas) {
        label_link_enso_hist.setValue('❌ Não foi possível montar a lista. Tente de novo.');
        label_link_enso_hist.style().set({color: '#d32f2f', fontWeight: 'bold'});
        logError('ENSO: falha ao montar a lista de meses', erro || '');
        return;
      }
      var tabela = montarListaMesesEnso(linhas.map(function(l) {
        return {ano: l[0], mes: l[1], RONI: l[2], FaseENSO: l[3], Fonte: l[4]};
      }));
      if (tabela.length === 0) {
        label_link_enso_hist.setValue('Nenhum mês com esse fenômeno no histórico.');
        return;
      }
      var cols = ['Ano', 'Mes', 'Mes_Nome', 'Trimestre_CPC', 'Meses_do_Trimestre', 'RONI_C', 'Fase', 'Intensidade', 'Fonte_RONI'];
      gerarLinkCsvEnso(ee.FeatureCollection(tabela.map(function(x) { return ee.Feature(null, x); })), cols,
                       'Meses_do_filtro_' + nomeCenario + '_' + tabela.length + '_meses', label_link_enso_hist);
    });
});
select_enso.onChange(function() { label_link_enso_hist.style().set('shown', false); });   // [V4.1 22/10]

function filtrarHistoricoPorENSO(icHistoricoBruto) {
  var cenario = select_enso.getValue();
  var filtro = filtroCenario(cenario);
  if (cenario === 'Todos os Anos' || !filtro) return icHistoricoBruto;

  var colComChave = icHistoricoBruto.map(function(img) {
    return img.set('chave_join', img.date().format('YYYY_MM'));
  });

  // outer: true mantém o dia mesmo sem par; ele recebe 'Sem_Dado' e sai dos filtros de cenário
  var filtroJoin = ee.Filter.equals({ leftField: 'chave_join', rightField: 'chave_join' });
  var join = ee.Join.saveFirst({matchKey: 'enso_info', outer: true});
  var colUnida = ee.ImageCollection(join.apply(colComChave, indiceONI_FC, filtroJoin));

  var icFiltrada = colUnida.map(function(img) {
    var tem = img.propertyNames().contains('enso_info');
    var info = ee.Feature(ee.Algorithms.If(tem, img.get('enso_info'),
      ee.Feature(null, {'FaseENSO': 'Sem_Dado', 'RONI': -99, 'Trimestre': 'N/A'})));
    return img.set('FaseENSO', info.get('FaseENSO'), 'RONI', info.get('RONI'),
                   'Trimestre', info.get('Trimestre'));
  });

  // [V4 F6/M06-06] Registro no Console dos meses do período que ficam fora de todos os cenários:
  // 'Indefinida' (fim da série, fase ainda aberta) e 'Sem_Dado' (sem RONI). Só informativo.
  var foraDosCenarios = icFiltrada.filter(ee.Filter.inList('FaseENSO', ['Indefinida', 'Sem_Dado']));
  ee.Dictionary({
    'Indefinida': foraDosCenarios.filter(ee.Filter.eq('FaseENSO', 'Indefinida')).aggregate_array('chave_join').distinct().sort(),
    'Sem_Dado': foraDosCenarios.filter(ee.Filter.eq('FaseENSO', 'Sem_Dado')).aggregate_array('chave_join').distinct().sort()
  }).evaluate(function(meses, erroMeses) {
    if (erroMeses || !meses) {
      logWarn('Filtro ENSO: não foi possível contar os meses sem fase definida.', erroMeses || '');
      return;
    }
    logInfo('Filtro ENSO (' + infoCenarioEnso(cenario).label + '): ' + meses.Indefinida.length + ' mês(es) com fase Indefinida e ' +
            meses.Sem_Dado.length + ' Sem_Dado ficaram fora do filtro.', meses);
  });

  return icFiltrada.filter(filtro);
}

// ============================================================
// MODULO 15: CALCULOS DE METRICAS CLIMATICAS
// ============================================================

function calcularMetricasClimaticas(ic_periodo) {
  var chuva_total = ic_periodo.select('pr_mm').reduce(ee.Reducer.sum()).rename('chuva_total');
  var tmin_media = ic_periodo.select('tmin_C').reduce(ee.Reducer.mean()).rename('tmin_media');
  var tmax_media = ic_periodo.select('tmax_C').reduce(ee.Reducer.mean()).rename('tmax_media');
  var u2_media = ic_periodo.select('u2').reduce(ee.Reducer.mean()).rename('u2_media');
  var rs_media = ic_periodo.select('rs').reduce(ee.Reducer.mean()).rename('rs_media');
  var tsolo_media = ic_periodo.select('tsolo_C').reduce(ee.Reducer.mean()).rename('tsolo_media');
  var tfolha_media = ic_periodo.select('tfolha_C').reduce(ee.Reducer.mean()).rename('tfolha_media');
  
  var chuva_efetiva_total = ic_periodo.map(function(img){ return img.select('pr_mm').subtract(img.select('runoff_sup_mm')).max(0).rename('chuva_efetiva'); }).reduce(ee.Reducer.sum()).rename('chuva_efetiva_total');
  var amplitude_termica = ic_periodo.map(function(img){ return img.select('tmax_C').subtract(img.select('tmin_C')).rename('amplitude_diaria'); }).reduce(ee.Reducer.mean()).rename('amplitude_termica');
  var deficit_hidrico = ic_periodo.map(function(img){ return img.select('et_potencial').subtract(img.select('et_real')).max(0).rename('deficit_diario'); }).reduce(ee.Reducer.sum()).rename('deficit_hidrico');
  var runoff_total = ic_periodo.map(function(img){ return img.select('runoff_sup_mm').add(img.select('runoff_sub_mm')).rename('runoff_total'); }).reduce(ee.Reducer.sum()).rename('runoff_total');

  var transpiracao_total = ic_periodo.select('transpiracao_mm').reduce(ee.Reducer.sum()).rename('transpiracao_total');
  
  var dias_secos = ic_periodo.select('pr_mm').map(function(img) { return img.lt(CFG.limiarDiaSeco); }).reduce(ee.Reducer.sum()).rename('dias_secos');
  var dias_frios = ic_periodo.select('tmin_C').map(function(img) { return img.lte(CFG.limiarFrio); }).reduce(ee.Reducer.sum()).rename('dias_frios');
  var dias_calor = ic_periodo.select('tmax_C').map(function(img) { return img.gte(CFG.limiarCalor); }).reduce(ee.Reducer.sum()).rename('dias_calor');
  
  var et_real_total = ic_periodo.select('et_real').reduce(ee.Reducer.sum()).rename('et_real_total');
  var et_potencial_total = ic_periodo.select('et_potencial').reduce(ee.Reducer.sum()).rename('et_potencial_total');
  var vpd_media = ic_periodo.select('vpd').reduce(ee.Reducer.mean()).rename('vpd_media');
  
  var umidade_solo_5 = ic_periodo.select('soil_moisture_0_5cm_m3_m3').reduce(ee.Reducer.mean()).rename('umidade_solo_5');
  var umidade_solo_100 = ic_periodo.select('soil_moisture_0_100cm_m3_m3').reduce(ee.Reducer.mean()).rename('umidade_solo_100');

  return { 
    chuva_total: chuva_total, tmin_media: tmin_media, tmax_media: tmax_media, u2_media: u2_media, rs_media: rs_media, 
    tsolo_media: tsolo_media, tfolha_media: tfolha_media, chuva_efetiva_total: chuva_efetiva_total, transpiracao_total: transpiracao_total, 
    runoff_total: runoff_total, dias_secos: dias_secos, dias_frios: dias_frios, dias_calor: dias_calor, amplitude_termica: amplitude_termica, 
    et_real_total: et_real_total, et_potencial_total: et_potencial_total, deficit_hidrico: deficit_hidrico, vpd_media: vpd_media,
    umidade_solo_5: umidade_solo_5, umidade_solo_100: umidade_solo_100
  };
}

// ============================================================
// MODULO 16: RENDERIZACAO DAS CAMADAS FINAIS NO MAPA
// ============================================================
function adicionarCamadasBaseMapa(regiaoInfo) {
  if (regiaoInfo.estados_contorno_fc) { 
    var contornoEstado = regiaoInfo.estados_contorno_fc.union(100);
    registrarCamada('limites_estaduais', 'Referência', 'Limites estaduais', contornoEstado.style({color: '#404040', fillColor: '00000000', width: 1}), {}, true); 
  }
  
  var geometriaFoco = regiaoInfo.poligonos_fc ? regiaoInfo.poligonos_fc : regiaoInfo.regiao_fc;
  
  registrarCamada('area_foco', 'Referência', 'Área de análise (Limite Exato)', geometriaFoco.style({color: '#d62728', fillColor: '00000000', width: 2}), {}, true);

  if (regiaoInfo.poligonos_expandidos_fc) {
    var expandidaUnion = regiaoInfo.poligonos_expandidos_fc.union(100);
    registrarCamada('area_expandida', 'Referência', 'Expansão de Borda (Azul)', expandidaUnion.style({color: '#0000FF', fillColor: '0000FF22', width: 2}), {}, false);
  }
}

function adicionarCamadasClimaticas(metrics, regiaoInfo, extras) {
  if (regiaoInfo.tipo === 'Coordenadas (Lat / Lon)') {
    logStep('Mapas de clima e vegetação desativados por padrão para geometrias customizadas (área reduzida). A extração do CSV segue operando em background.');
    construirPainelCamadas();
    return;
  }

  var regiao_geom = APP.regiaoGeom; 
  
  var suavizar = function(imagem) { 
    var projNativa = ee.Projection('EPSG:4326').atScale(CFG.escalaArea);
    return imagem.setDefaultProjection(projNativa)
                 .focal_mean({radius: 1.2, units: 'pixels'})
                 .resample('bilinear')
                 .clip(regiao_geom); 
  };

  var imagemEmpilhada = ee.Image.cat([
    suavizar(metrics.chuva_total).rename('chuva_total'),
    suavizar(metrics.tmin_media).rename('tmin_media'),
    suavizar(metrics.tmax_media).rename('tmax_media'),
    suavizar(metrics.amplitude_termica).rename('amp_termica'),
    suavizar(metrics.u2_media).rename('vento_media'),
    suavizar(metrics.rs_media).rename('rs_media'),
    suavizar(metrics.tsolo_media).rename('tsolo_media'),
    suavizar(metrics.tfolha_media).rename('tfolha_media'),
    suavizar(metrics.chuva_efetiva_total).rename('chuva_efetiva_total'),
    suavizar(metrics.runoff_total).rename('runoff_total'),
    suavizar(metrics.transpiracao_total).rename('transpiracao_total'),
    suavizar(metrics.et_real_total).rename('et_real_total'),
    suavizar(metrics.deficit_hidrico).rename('deficit_hidrico'),
    suavizar(metrics.vpd_media).rename('vpd_media'),
    suavizar(metrics.dias_secos).rename('dias_secos'),
    suavizar(metrics.dias_frios).rename('dias_frios'),
    suavizar(metrics.dias_calor).rename('dias_calor'),
    suavizar(metrics.umidade_solo_5).rename('umidade_solo_5'),
    suavizar(metrics.umidade_solo_100).rename('umidade_solo_100')
  ]);

  logStep('Calculando limites de renderização exatos baseados nos dados...');

  var limitesEstatisticos = imagemEmpilhada.reduceRegion({
    reducer: ee.Reducer.percentile([2, 98]),
    geometry: regiao_geom,
    scale: CFG.escalaArea,
    maxPixels: 1e9,
    bestEffort: true
  });

  limitesEstatisticos.evaluate(function(valores, erro) {
    if (erro) {
      logError('Falha ao calcular a coloração dinâmica.', erro);
      return;
    }

    var obterLimites = function(banda, fallbackMin, fallbackMax) {
      var pMin = valores[banda + '_p2'];
      var pMax = valores[banda + '_p98'];
      if (pMin === null || pMin === undefined || isNaN(pMin)) pMin = fallbackMin;
      if (pMax === null || pMax === undefined || isNaN(pMax)) pMax = fallbackMax;
      if (pMin === pMax) pMax = pMin + 0.1; 
      return { min: pMin, max: pMax };
    };

    var l_chuva = obterLimites('chuva_total', 0, 100);
    registrarCamada('chuva_total', 'Clima', 'Chuva Acumulada no Período (mm)', imagemEmpilhada.select('chuva_total'), {min: l_chuva.min, max: l_chuva.max, palette: CFG.paletas.chuvaTotal}, false);

    var l_tmin = obterLimites('tmin_media', 8, 20);
    registrarCamada('tmin_media', 'Clima', 'Temperatura mínima média (°C)', imagemEmpilhada.select('tmin_media'), {min: l_tmin.min, max: l_tmin.max, palette: CFG.paletas.tminMedia}, false);

    var l_tmax = obterLimites('tmax_media', 22, 32);
    registrarCamada('tmax_media', 'Clima', 'Temperatura máxima média (°C)', imagemEmpilhada.select('tmax_media'), {min: l_tmax.min, max: l_tmax.max, palette: CFG.paletas.tmaxMedia}, false);

    var l_amp = obterLimites('amp_termica', 7, 14);
    registrarCamada('amp_termica', 'Clima', 'Amplitude térmica média (°C)', imagemEmpilhada.select('amp_termica'), {min: l_amp.min, max: l_amp.max, palette: CFG.paletas.amplitudeTermica}, false);

    var l_vento = obterLimites('vento_media', 0.5, 3.0);
    registrarCamada('vento_media', 'Clima', 'Velocidade do Vento (m/s)', imagemEmpilhada.select('vento_media'), {min: l_vento.min, max: l_vento.max, palette: ['#f7fcf0', '#e0f3db', '#ccebc5', '#a8ddb5', '#7bccc4', '#4eb3d3', '#2b8cbe', '#08589e']}, false);

    var l_rs = obterLimites('rs_media', 14, 22);
    registrarCamada('rs_media', 'Clima', 'Radiação Solar Diária (MJ/m²)', imagemEmpilhada.select('rs_media'), {min: l_rs.min, max: l_rs.max, palette: ['#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#b10026']}, false);

    var l_tsolo = obterLimites('tsolo_media', 15, 28);
    registrarCamada('tsolo_media', 'Vegetação e solo', 'Temp do Solo (0-7cm) Média (°C)', imagemEmpilhada.select('tsolo_media'), {min: l_tsolo.min, max: l_tsolo.max, palette: ['#ffffd4', '#fed98e', '#fe9929', '#d95f0e', '#993404']}, false);

    var l_tfolha = obterLimites('tfolha_media', 12, 30);
    registrarCamada('tfolha_media', 'Vegetação e solo', 'Temp. de Superfície (skin) Média (°C)', imagemEmpilhada.select('tfolha_media'), {min: l_tfolha.min, max: l_tfolha.max, palette: ['#006837', '#78c679', '#ffffcc', '#fd8d3c', '#e31a1c']}, false);

    var l_chuva_ef = obterLimites('chuva_efetiva_total', 0, 85);
    registrarCamada('chuva_efetiva_total', 'Extremos', 'Chuva Efetiva (mm infiltrados)', imagemEmpilhada.select('chuva_efetiva_total'), {min: l_chuva_ef.min, max: l_chuva_ef.max, palette: ['#ffffff', '#bdc9e1', '#74a9cf', '#2b8cbe', '#045a8d']}, false);

    var l_runoff = obterLimites('runoff_total', 0, 50);
    registrarCamada('runoff_total', 'Extremos', 'Escoamento Total (superficial + subsuperficial) (mm)', imagemEmpilhada.select('runoff_total'), {min: l_runoff.min, max: l_runoff.max, palette: ['#ffffff', '#efedf5', '#bcbddc', '#756bb1', '#54278f']}, false);

    var l_transp = obterLimites('transpiracao_total', 0, 100);
    registrarCamada('transpiracao_total', 'Vegetação e solo', 'Transpiração da Cultura (mm)', imagemEmpilhada.select('transpiracao_total'), {min: l_transp.min, max: l_transp.max, palette: ['#ffffff', '#c7e9c0', '#74c476', '#238b45', '#00441b']}, false);

    var l_et = obterLimites('et_real_total', 0, 150);
    registrarCamada('et_real_total', 'Vegetação e solo', 'Evapotranspiração Real (mm)', imagemEmpilhada.select('et_real_total'), {min: l_et.min, max: l_et.max, palette: ['#ffffff', '#c2e699', '#78c679', '#31a354', '#006837', '#004529']}, false);

    var l_def = obterLimites('deficit_hidrico', 0, 50);
    registrarCamada('deficit_hidrico', 'Extremos', 'Déficit Hídrico (ETP - ETR)', imagemEmpilhada.select('deficit_hidrico'), {min: l_def.min, max: l_def.max, palette: ['#ffffff', '#fee090', '#f46d43', '#d73027', '#a50026']}, false);
    
    var l_vpd = obterLimites('vpd_media', 0.2, 1.8);
    registrarCamada('vpd_media', 'Extremos', 'Déficit de Pressão de Vapor (VPD)', imagemEmpilhada.select('vpd_media'), {min: l_vpd.min, max: l_vpd.max, palette: ['#99d594', '#ffffbf', '#fc8d59', '#d53e4f', '#9e0142', '#40004b']}, false);
    
    var l_dsecos = obterLimites('dias_secos', 0, 10);
    registrarCamada('dias_secos', 'Extremos', 'Dias secos (< 1 mm)', imagemEmpilhada.select('dias_secos'), {min: l_dsecos.min, max: l_dsecos.max, palette: CFG.paletas.diasSecos}, false);
    
    var l_dfrios = obterLimites('dias_frios', 0, 5);
    registrarCamada('dias_frios', 'Extremos', 'Dias frios (Tmin ≤ 4°C)', imagemEmpilhada.select('dias_frios'), {min: l_dfrios.min, max: l_dfrios.max, palette: CFG.paletas.diasFrios}, false);
    
    var l_dcalor = obterLimites('dias_calor', 0, 5);
    registrarCamada('dias_calor', 'Extremos', 'Dias de calor (Tmax ≥ 35°C)', imagemEmpilhada.select('dias_calor'), {min: l_dcalor.min, max: l_dcalor.max, palette: CFG.paletas.diasCalor}, false);
    
    var l_umidade5 = obterLimites('umidade_solo_5', 0.05, 0.45);
    registrarCamada('umidade_solo_5', 'Vegetação e solo', 'Umidade Volumétrica Solo (0 a 5cm) Média (m³/m³)', imagemEmpilhada.select('umidade_solo_5'), {min: l_umidade5.min, max: l_umidade5.max, palette: CFG.paletas.umidadeSolo}, false);

    var l_umidade100 = obterLimites('umidade_solo_100', 0.05, 0.45);
    registrarCamada('umidade_solo_100', 'Vegetação e solo', 'Umidade Volumétrica Solo (0 a 100cm) Média (m³/m³)', imagemEmpilhada.select('umidade_solo_100'), {min: l_umidade100.min, max: l_umidade100.max, palette: CFG.paletas.umidadeSolo}, false);

    construirPainelCamadas();
  });
}

// ============================================================
// MODULO 17: EXPORTAÇÃO E GERAÇÃO DE LINKS DIRETOS NO MAPA
// ============================================================
function limparNomeArquivo(nome) { 
  return removerAcentos(String(nome)).replace(/[^a-zA-Z0-9_-]/g, '_');
}

// [V4] colunasExtras: nomes das colunas novas que este CSV usa (copiadas da feição; vazias se ausentes)
function formatarExportacaoClima(fc, colunasExtras) {
  return fc.map(function(f) {
    var dataStr = ee.String(f.get('Data'));
    var partes = dataStr.split('-').cat(ee.List(['', '', ''])); 
    var fDict = f.toDictionary();
    
    // [22/10, 18h30] Números com PONTO decimal e as mesmas casas de antes ("18.40"): uma só operação por
    // valor (format), menos que o texto com vírgula da 2026.10.2 (format + replace) e que o arredondamento
    // numérico das 17h (multiply + round + divide), que deixou o CSV de um ano do Paraná pesado demais (503).
    // No CSV, "18.40" é lido como número por qualquer programa. Ausência (-9999) continua como célula vazia.
    var formatarParaPtBr = function(chave, formatoCadeia) {
      var val = ee.Number(fDict.get(chave, -9999));
      return ee.Algorithms.If(val.eq(-9999), null, val.format(formatoCadeia));
    };

    // Função equivalente para cálculos dinâmicos realizados no bloco
    var formatarValorDiretoPtBr = function(valBruto, formatoCadeia) {
      var valorNum = ee.Number(valBruto);
      return ee.Algorithms.If(valorNum.eq(-9999), null, valorNum.format(formatoCadeia));
    };
    
    var tmax = ee.Number(fDict.get('tmax_C', -9999));
    var tmin = ee.Number(fDict.get('tmin_C', -9999));
    var et_pot = ee.Number(fDict.get('et_potencial', -9999));
    var et_real = ee.Number(fDict.get('et_real', -9999));

    var ampTermicaBruta = ee.Algorithms.If(
        fDict.contains('amplitude_diaria'), 
        fDict.get('amplitude_diaria'), 
        ee.Algorithms.If(tmax.eq(-9999).or(tmin.eq(-9999)), -9999, tmax.subtract(tmin))
    );
    
    var deficitHidricoBruto = ee.Algorithms.If(
        fDict.contains('deficit_diario'), 
        fDict.get('deficit_diario'), 
        ee.Algorithms.If(et_pot.eq(-9999).or(et_real.eq(-9999)), -9999, et_pot.subtract(et_real).max(0))
    );

    var propsCSV = { // [V4] o objeto antes ia direto para o ee.Feature
      // [22/10, 18h30] fDict.get com valor padrão: mesmo resultado, sem listar as propriedades a cada linha
      'Tipo_Dado': fDict.get('Tipo_Dado', 'Agregado'),
      'Versao_Algoritmo': fDict.get('Versao_Algoritmo', ''),
      'Data_Completa': dataStr,
      'Ano': partes.get(0),
      'Mes': partes.get(1),
      'Dia': partes.get(2),
      'N_Ponto': f.get('ID_Ponto'), 
      'Latitude': formatarParaPtBr('Latitude', '%.5f'),
      'Longitude': formatarParaPtBr('Longitude', '%.5f'),
      'Estado': f.get('Estado'), 
      'Municipio': f.get('Municipio'),
      'Precipitacao_mm': formatarParaPtBr('pr_mm', '%.2f'), 
      'Chuva_Efetiva_mm': formatarParaPtBr('chuva_efetiva', '%.2f'), 
      'Runoff_Superficial_mm': formatarParaPtBr('runoff_sup_mm', '%.2f'),
      'Runoff_Subsuperficial_mm': formatarParaPtBr('runoff_sub_mm', '%.2f'),
      'Temperatura_Maxima_C': formatarParaPtBr('tmax_C', '%.2f'), 
      'Temperatura_Minima_C': formatarParaPtBr('tmin_C', '%.2f'), 
      'Amplitude_Termica_C': formatarValorDiretoPtBr(ampTermicaBruta, '%.2f'),
      'Temperatura_Solo_C': formatarParaPtBr('tsolo_C', '%.2f'), 
      'Temperatura_Folha_C': formatarParaPtBr('tfolha_C', '%.2f'), 
      'Umidade_Relativa_Porc': formatarParaPtBr('RH', '%.2f'), 
      'Vento_ms': formatarParaPtBr('u2', '%.2f'),                  
      'Radiacao_Solar_MJ_m2': formatarParaPtBr('rs', '%.2f'),          
      'Evapotranspiracao_Potencial_mm': formatarParaPtBr('et_potencial', '%.2f'), 
      'Evapotranspiracao_Real_mm': formatarParaPtBr('et_real', '%.2f'),
      'Transpiracao_Planta_mm': formatarParaPtBr('transpiracao_mm', '%.2f'),
      'Deficit_Hidrico_mm': formatarValorDiretoPtBr(deficitHidricoBruto, '%.2f'),
      'Deficit_Pressao_Vapor_kPa': formatarParaPtBr('vpd', '%.2f'),
      'Umidade_Volumetrica_Solo_0_5cm_m3_m3': formatarParaPtBr('soil_moisture_0_5cm_m3_m3', '%.3f'),
      'Umidade_Volumetrica_Solo_0_100cm_m3_m3': formatarParaPtBr('soil_moisture_0_100cm_m3_m3', '%.3f')
    };
    // [V4] colunas novas (Qualidade_Pixel, Janela_Chuva_UTC, Confianca_Prazo no diário; N_Dias,
    // Dias_no_Mes, Mes_Completo no mensal), copiadas como texto/número, sem conversão
    (colunasExtras || []).forEach(function(col) {
      propsCSV[col] = fDict.get(col, '');   // [22/10, 18h30] mesmo resultado, mais leve
    });
    return ee.Feature(null, propsCSV);
  });
}

// [V4] Colunas novas de cada CSV (o contrato V4 não muda as colunas que já existiam)
var COLUNAS_NOVAS_DIARIA = ['Qualidade_Pixel', 'Janela_Chuva_UTC', 'Confianca_Prazo'];
var COLUNAS_NOVAS_MENSAL = ['N_Dias', 'Dias_no_Mes', 'Mes_Completo'];
// [V4.1 22/10] Com o filtro ENSO do item B ligado, os CSV de dados ganham no FIM estas colunas (sem o
// filtro, os CSV ficam exatamente como antes). Os dias de previsão ficam com elas vazias.
var COLUNAS_ENSO = ['Filtro_ENSO', 'Fase_ENSO', 'Intensidade_ENSO', 'RONI_Trimestre_C', 'Trimestre_CPC'];

function sufixoArquivoEnso(cenario) {
  return cenario ? '_' + infoCenarioEnso(cenario).arquivo : '';
}

// Propriedades ENSO de uma imagem diária (gravadas por filtrarHistoricoPorENSO); vazias se não houver
function propsEnsoDaImagem(img, cenario) {
  var tem = img.propertyNames().contains('FaseENSO');
  // [V4.1 22/10, correção 2] sem fase = dia de previsão (o filtro só deixa passar o passado classificado e a
  // previsão): texto explícito em vez de colunas vazias; o trimestre do CPC sai da data
  var fase = ee.String(ee.Algorithms.If(tem, img.get('FaseENSO'), 'Previsao (sem classificacao)'));
  var triData = ee.List(['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ'])
                  .get(ee.Date(img.get('system:time_start')).get('month').subtract(1));
  var roni = ee.Number(ee.Algorithms.If(tem, img.get('RONI'), 0));
  var nino = fase.equals('El Nino'), nina = fase.equals('La Nina');
  var intens = ee.Algorithms.If(nino,
      ee.Algorithms.If(roni.gte(2.0), 'Muito forte (Super)', ee.Algorithms.If(roni.gte(1.5), 'Forte',
        ee.Algorithms.If(roni.gte(1.0), 'Moderado', 'Fraco'))),
    ee.Algorithms.If(nina,
      ee.Algorithms.If(roni.lte(-2.0), 'Muito forte (Super)', ee.Algorithms.If(roni.lte(-1.5), 'Forte',
        ee.Algorithms.If(roni.lte(-1.0), 'Moderada', 'Fraca'))),
      '-'));
  return {
    'Filtro_ENSO': infoCenarioEnso(cenario).ascii,
    'Fase_ENSO': fase,
    'Intensidade_ENSO': intens,
    'RONI_Trimestre_C': ee.Algorithms.If(tem, roni.format('%.1f'), '-'),   // [22/10] ponto decimal
    'Trimestre_CPC': ee.Algorithms.If(tem, img.get('Trimestre'), triData)
  };
}

// Copia as colunas ENSO da imagem mensal para a linha do CSV ({} sem o filtro)
function copiarColunasEnso(img, cenario) {
  var props = {};
  if (cenario) COLUNAS_ENSO.forEach(function(c) { props[c] = img.get(c); });
  return props;
}

// Anos do período que têm dias (com o filtro ENSO, muitos anos ficam vazios: não gera arquivo para eles)
function comAnosComDados(ic_periodo, anoInicio, anoFim, callback) {
  var todos = [];
  for (var a = anoInicio; a <= anoFim; a++) todos.push(a);
  if (!APP.filtroEnso) { callback(todos); return; }
  ic_periodo.aggregate_array('system:time_start').map(function(t) { return ee.Date(t).get('year'); })
    .distinct().sort().evaluate(function(anos, erro) {
      if (erro) { logError('Filtro ENSO: falha ao listar os anos com dados.', erro); callback(todos); return; }
      if (!anos || anos.length === 0) {
        painel_downloads_app.style().set('shown', true);
        painel_downloads_app.add(ui.Label('Nenhum mês do período escolhido teve o fenômeno "' + infoCenarioEnso(APP.filtroEnso).label +
          '". Amplie o período ou escolha outro fenômeno.', {fontSize: '11px', color: '#d32f2f', margin: '2px 0'}));
      }
      callback(anos || []);
    });
}

// [V4 revisão B-05] Colunas novas no FIM de cada CSV: as 30 colunas antigas ficam nas mesmas posições
// (quem lê o CSV por posição não quebra). Diário: Qualidade_Pixel, Janela_Chuva_UTC e Confianca_Prazo.
function getColunasClimaDiaria() {
  return getColunasClimaBase().concat(COLUNAS_NOVAS_DIARIA);
}

// [V4 F4/M06-04; revisão B-05] Mensal: N_Dias, Dias_no_Mes e Mes_Completo no fim
function getColunasClimaMensal() {
  return getColunasClimaBase().concat(COLUNAS_NOVAS_MENSAL);
}

function getColunasClimaBase() {
  return [
    'Tipo_Dado', 'Versao_Algoritmo', 'Data_Completa', 'Ano', 'Mes', 'Dia', 'N_Ponto', 'Latitude', 'Longitude', 'Estado', 'Municipio',
    'Precipitacao_mm', 'Chuva_Efetiva_mm', 'Runoff_Superficial_mm', 'Runoff_Subsuperficial_mm', 'Temperatura_Maxima_C', 'Temperatura_Minima_C', 
    'Amplitude_Termica_C', 'Temperatura_Solo_C', 'Temperatura_Folha_C', 'Umidade_Relativa_Porc', 'Vento_ms', 
    'Radiacao_Solar_MJ_m2', 'Evapotranspiracao_Potencial_mm', 'Evapotranspiracao_Real_mm', 'Transpiracao_Planta_mm', 
    'Deficit_Hidrico_mm', 'Deficit_Pressao_Vapor_kPa', 'Umidade_Volumetrica_Solo_0_5cm_m3_m3', 'Umidade_Volumetrica_Solo_0_100cm_m3_m3'
  ];
}

function gerarLinkDownloadCSV(fc, filename, colunas) {
  painel_downloads_app.style().set('shown', true);
  
  // Pré-aloca o espaço na ordem cronológica em que a função foi chamada no loop
  var linkLabel = ui.Label('⏳ Gerando: ' + filename + '...', {
    fontSize: '11px', 
    color: '#555555', 
    margin: '2px 0'
  });
  painel_downloads_app.add(linkLabel);

  var fcFiltrada = fc.select(colunas);

  // Retorna aos argumentos posicionais nativos da API JavaScript do Earth Engine
  fcFiltrada.getDownloadURL('csv', colunas, filename, function(url, errorMessage) {
    if (errorMessage) {
      var msgErro = 'Limite excedido. Reduza o período ou a área.';
      linkLabel.setValue('❌ Erro (' + filename + '): ' + msgErro);
      linkLabel.style().set({color: '#d32f2f', fontWeight: 'bold'});
      logError('Erro na geração do link para ' + filename, errorMessage);
    } else {
      // Modifica o rótulo existente em vez de criar um novo no fim da lista
      linkLabel.setValue('⬇️ Baixar ' + filename + '.csv');
      linkLabel.setUrl(url);
      linkLabel.style().set({color: '#1d70b8', fontSize: '13px', fontWeight: 'bold'});
    }
  });
}

function exportarDicionarioAutomatizado() {
var dicionario = [
      // [V4 F9/M06-11] Tipo_Dado: Previsao_GFS_Parcial e Desconhecido descritos corretamente
      ee.Feature(null, {'Variavel': 'Tipo_Dado', 'Descricao': 'Origem do dia: Historico_Observado (BR-DWGD), Provisorio_ERA5 (reanalise calibrada), Previsao_GFS (previsao calibrada), Previsao_GFS_Parcial (dia com rodada GFS incompleta: chuva, radiacao solar, ETo e as colunas que dependem delas ficam vazias), Sem_Dado, Desconhecido (valor de versao que o painel nao reconhece).', 'Unidade': '-'}),
      ee.Feature(null, {'Variavel': 'Versao_Algoritmo', 'Descricao': 'Versao do motor que gravou o dia. V1.0: historico (umidade do solo e escoamento corrigidos pelo painel na leitura). V1.3: ETo por Penman-Monteith nos dias provisorios e na previsao. V1.4: umidade do solo do ERA5 com reamostragem bilinear e previsao GFS calibrada por faixa de prazo. V1.5: so rodadas GFS 00Z completas, matriz GFS V2.1, mascara de 2025-12-31 e Confianca_Prazo nos dias GFS. No arquivo mensal, as versoes presentes no mes.', 'Unidade': '-'}),
      // [V4 F8/M06-05, V4 Conf, V4 F4/M06-04] colunas novas de metadados
      ee.Feature(null, {'Variavel': 'Janela_Chuva_UTC', 'Descricao': 'CSV diario. Janela de acumulo da chuva do dia, em UTC. 12-12 UTC (D-1 a D): BR-DWGD (historico), de 12 UTC do dia anterior a 12 UTC do dia (9 h a 9 h de Brasilia). 00-24 UTC: ERA5 e GFS, dia civil em UTC (21 h do dia anterior a 21 h do dia em Brasilia). Os valores nao sao ajustados entre as janelas.', 'Unidade': '-'}),
      // [V4.1 22/10] colunas que só aparecem com o filtro ENSO do item B ligado
      ee.Feature(null, {'Variavel': 'Filtro_ENSO', 'Descricao': 'So com o filtro ENSO do item B ligado. Fenomeno escolhido no filtro: o arquivo traz so os meses do passado em que ele ocorreu (os dias de previsao continuam todos e ficam com as colunas ENSO vazias).', 'Unidade': '-'}),
      ee.Feature(null, {'Variavel': 'Fase_ENSO', 'Descricao': 'So com o filtro ENSO. Fase do trimestre do CPC centrado no mes do dia: El Nino, La Nina ou Neutro (episodio = 5 trimestres seguidos acima de +0,5 ou abaixo de -0,5 C). Nos dias de previsao: Previsao (sem classificacao), com - na intensidade e no RONI.', 'Unidade': '-'}),
      ee.Feature(null, {'Variavel': 'Intensidade_ENSO', 'Descricao': 'So com o filtro ENSO. Intensidade pelo RONI do trimestre: Fraco (0,5 a 0,9), Moderado (1,0 a 1,4), Forte (1,5 a 1,9) ou Muito forte/Super (2,0 ou mais), em modulo; - no Neutro.', 'Unidade': '-'}),
      ee.Feature(null, {'Variavel': 'RONI_Trimestre_C', 'Descricao': 'So com o filtro ENSO. Indice RONI do CPC/NOAA do trimestre centrado no mes (anomalia relativa da temperatura do mar no Nino 3.4).', 'Unidade': 'C'}),
      ee.Feature(null, {'Variavel': 'Trimestre_CPC', 'Descricao': 'So com o filtro ENSO. Sigla do trimestre do CPC centrado no mes (ex.: OND = outubro a dezembro, usado nos dias de novembro).', 'Unidade': '-'}),
      ee.Feature(null, {'Variavel': 'Confianca_Prazo', 'Descricao': 'CSV diario. Confianca da previsao GFS pelo prazo, gravada pelo motor a partir da V1.5: alta (prazo de 1 a 5 dias), media (6 a 10), baixa (11 em diante). Vazia nos demais dias e nos dias gravados pelas versoes V1.3 e V1.4.', 'Unidade': '-'}),
      ee.Feature(null, {'Variavel': 'N_Dias', 'Descricao': 'CSV mensal. Numero de imagens diarias usadas no mes (dentro do periodo pedido e do filtro ENSO).', 'Unidade': 'dias'}),
      ee.Feature(null, {'Variavel': 'Dias_no_Mes', 'Descricao': 'CSV mensal. Numero de dias do mes no calendario.', 'Unidade': 'dias'}),
      ee.Feature(null, {'Variavel': 'Mes_Completo', 'Descricao': 'CSV mensal. sim quando N_Dias = Dias_no_Mes; nao em mes parcial (inicio ou fim do periodo, filtro ENSO, dias faltando). Somas de mes parcial nao sao totais mensais.', 'Unidade': '-'}),
      // [V4 F9/M06-11, V4 Q1] posicao e qualidade do ponto
      ee.Feature(null, {'Variavel': 'Latitude', 'Descricao': 'Latitude do centro do pixel da grade de 0,1 grau (nao e a sede do municipio).', 'Unidade': 'graus'}),
      ee.Feature(null, {'Variavel': 'Longitude', 'Descricao': 'Longitude do centro do pixel da grade de 0,1 grau (nao e a sede do municipio).', 'Unidade': 'graus'}),
      ee.Feature(null, {'Variavel': 'Qualidade_Pixel', 'Descricao': 'CSV diario. Classe do pixel na mascara de qualidade: A = SAB igual ao BR-DWGD; B = lagoas e estuarios onde o motor V1.0 descartou o BR-DWGD (desde o painel 2026.11.1 os dias de 1961 a 2025 saem com o BR-DWGD em chuva, temperaturas, UR, VPD, ETo, radiacao e vento, corrigidos na leitura); C = sem BR-DWGD, preenchido com ERA5, centro do pixel no Brasil (desde 2026.11.1 a radiacao dos dias de 1961 a 2025 e limitada a de ceu claro, FAO-56). Com a mascara, os pixels sem BR-DWGD com centro fora do Brasil (borda) ficam fora do CSV. Vazia se o pixel nao tem classe ou se a mascara ainda nao existe.', 'Unidade': '-'}),
      // [V4 F8/M06-05] referencia a janela do dia
      ee.Feature(null, {'Variavel': 'Precipitacao_mm', 'Descricao': 'Volume total de chuva no periodo. A janela de acumulo de cada dia esta na coluna Janela_Chuva_UTC.', 'Unidade': 'mm'}),
      // [K12, 22/10] formato dos números
      ee.Feature(null, {'Variavel': '(formato dos numeros)', 'Descricao': 'Desde 22/10/2026 os valores saem com PONTO decimal (ex.: 18.40), com as mesmas casas de antes; celula vazia = sem dado. No Excel em portugues, abra por Dados > De Texto/CSV e escolha o ponto como separador decimal.', 'Unidade': '-'}),
      // [V4 F9/M06-11] escoamento e chuva efetiva: indices nao validados (auditoria E3)
      ee.Feature(null, {'Variavel': 'Chuva_Efetiva_mm', 'Descricao': 'INDICE NAO VALIDADO: chuva menos o escoamento superficial (minimo zero). Herda a incerteza do escoamento (auditoria E3: fator do SMAP acima de 5 em ate 60% dos pixels na seca). Nao e medida da chuva que infiltrou. ATENCAO nos dias de 1961 a 2025: a chuva e a observada (BR-DWGD) e o escoamento e do modelo ERA5-Land, que responde a chuva do proprio modelo; por isso, dia a dia, o escoamento pode passar da chuva e a chuva efetiva sair 0 mesmo em dia chuvoso (auditoria K26: 1,1% dos dias com chuva de 5 mm ou mais, em 1981-1990). Use em somas mensais ou maiores, nao dia a dia.', 'Unidade': 'mm'}),
      ee.Feature(null, {'Variavel': 'Runoff_Superficial_mm', 'Descricao': 'INDICE NAO VALIDADO de escoamento superficial (enxurrada). Auditoria E3: fator do SMAP acima de 5 em ate 60% dos pixels na seca. ATENCAO nos dias de 1961 a 2025: o escoamento vem do modelo ERA5-Land (que responde a chuva do proprio modelo) e a chuva e a observada (BR-DWGD); dia a dia eles nao batem: o escoamento passa da chuva do dia em cerca de 29% dos pixel-dias (auditoria K26, 1981-1990), mas no total e cerca de 21% da chuva. Use em somas mensais ou maiores, nao dia a dia. De 2026 em diante, chuva e escoamento vem da mesma fonte (0,5% dos pixel-dias).', 'Unidade': 'mm'}),
      ee.Feature(null, {'Variavel': 'Runoff_Subsuperficial_mm', 'Descricao': 'INDICE NAO VALIDADO de escoamento por dentro do solo (fluxo subsuperficial). Mesma ressalva do escoamento superficial (auditoria E3).', 'Unidade': 'mm'}),
      ee.Feature(null, {'Variavel': 'Temperatura_Maxima_C', 'Descricao': 'Temperatura maxima do ar a 2 metros de altura.', 'Unidade': 'Celsius (C)'}),
      ee.Feature(null, {'Variavel': 'Temperatura_Minima_C', 'Descricao': 'Temperatura minima do ar a 2 metros de altura.', 'Unidade': 'Celsius (C)'}),
      ee.Feature(null, {'Variavel': 'Amplitude_Termica_C', 'Descricao': 'Diferenca entre a temperatura maxima e minima do dia.', 'Unidade': 'Celsius (C)'}),
      // [V4 F9/M06-11] Tsolo e Tfolha vazias nos dias GFS
      ee.Feature(null, {'Variavel': 'Temperatura_Solo_C', 'Descricao': 'Temperatura media da camada de 0 a 7 cm do solo (ERA5-Land). Vazia nos dias de previsao GFS.', 'Unidade': 'Celsius (C)'}),
      ee.Feature(null, {'Variavel': 'Temperatura_Folha_C', 'Descricao': 'Temperatura de superficie (skin temperature do ERA5-Land): temperatura teorica que fecha o balanco de energia da superficie. Nao e medida direta da folha. Vazia nos dias de previsao GFS.', 'Unidade': 'Celsius (C)'}),
      ee.Feature(null, {'Variavel': 'Umidade_Relativa_Porc', 'Descricao': 'Umidade relativa do ar. Nos dias provisorios, calculada das medias diarias de temperatura e ponto de orvalho do ERA5-Land e calibrada pelo BR-DWGD.', 'Unidade': '%'}),
      ee.Feature(null, {'Variavel': 'Vento_ms', 'Descricao': 'Velocidade media do vento a 2 metros de altura (convertida de 10 m pelo fator FAO-56).', 'Unidade': 'm/s'}),
      ee.Feature(null, {'Variavel': 'Radiacao_Solar_MJ_m2', 'Descricao': 'Radiacao solar global incidente na superficie.', 'Unidade': 'MJ/m2'}),
      ee.Feature(null, {'Variavel': 'Evapotranspiracao_Potencial_mm', 'Descricao': 'Evapotranspiracao de Referencia FAO-56 Penman-Monteith (demanda da atmosfera). No historico vem do BR-DWGD; nos dias provisorios e na previsao e calculada com a meteorologia calibrada.', 'Unidade': 'mm'}),
      ee.Feature(null, {'Variavel': 'Evapotranspiracao_Real_mm', 'Descricao': 'Evapotranspiracao Real (ERA5-Land no historico e nos dias provisorios; balanco de agua no solo na previsao), nunca maior que a potencial.', 'Unidade': 'mm'}),
      // [V4 F9/M06-11] origem real da transpiracao
      ee.Feature(null, {'Variavel': 'Transpiracao_Planta_mm', 'Descricao': 'Vem da banda de evaporacao do solo do ERA5-Land (evaporation_from_bare_soil_sum), que o motor usa como transpiracao por causa da troca de bandas apontada no catalogo do GEE; limitada a ET real. Nos dias GFS vem do balanco de agua do motor. Nao e medida da transpiracao da cultura.', 'Unidade': 'mm'}),
      ee.Feature(null, {'Variavel': 'Deficit_Hidrico_mm', 'Descricao': 'Estresse hidrico (Evapotranspiracao Potencial - Evapotranspiracao Real).', 'Unidade': 'mm'}),
      ee.Feature(null, {'Variavel': 'Deficit_Pressao_Vapor_kPa', 'Descricao': 'Deficit de Pressao de Vapor (VPD) medindo a secura do ar.', 'Unidade': 'kPa'}),
      ee.Feature(null, {'Variavel': 'Umidade_Volumetrica_Solo_0_5cm_m3_m3', 'Descricao': 'Umidade volumetrica da camada superficial: camada de 0 a 7 cm do ERA5-Land calibrada pela media mensal do SMAP L4 (0 a 5 cm).', 'Unidade': 'm3/m3'}),
      ee.Feature(null, {'Variavel': 'Umidade_Volumetrica_Solo_0_100cm_m3_m3', 'Descricao': 'Umidade volumétrica de água armazenada na zona radicular completa de 0 a 100 cm.', 'Unidade': 'm3/m3'})
    ];
  
  gerarLinkDownloadCSV(ee.FeatureCollection(dicionario), '00_Dicionario_Variaveis_SAB', ['Variavel', 'Descricao', 'Unidade']);
}

function exportarSerieDiaria(ic_periodo, nomesTarget, datas) {
  if (select_resolucao.getValue() !== 'Diária' || !nomesTarget || !datas) return;

  var anoInicio = parseInt(datas.isoInicio.split('-')[0], 10);
  var anoFim = parseInt(datas.isoFim.split('-')[0], 10);
  var cenarioEnso = APP.filtroEnso;   // [V4.1 22/10]
  var extrasDiaria = cenarioEnso ? COLUNAS_NOVAS_DIARIA.concat(COLUNAS_ENSO) : COLUNAS_NOVAS_DIARIA;

  comAnosComDados(ic_periodo, anoInicio, anoFim, function(anosComDados) {   // [V4.1 22/10]
  nomesTarget.forEach(function(nome) {
    var nomeSeguro = limparNomeArquivo(nome);
    var fcFiltrada = APP.regiaoFC.filter(ee.Filter.eq('Nome_Local_Export', nome));

    anosComDados.forEach(function(anoAtual) {
      var dataInicioAno = ee.Date.fromYMD(anoAtual, 1, 1);
      var dataFimAno = ee.Date.fromYMD(anoAtual, 12, 31).advance(1, 'day');

      var ic_ano = ic_periodo.filterDate(dataInicioAno, dataFimAno);

      var fc = ic_ano.map(function(img) {
        // Origem real do dia, gravada pelo motor Python no próprio banco
        var versaoImg = ee.String(ee.Algorithms.If(
          img.propertyNames().contains('versao'), img.get('versao'), 'definitiva'));
        var flagPrevisao = ee.Dictionary({
          'definitiva': 'Historico_Observado',
          'provisoria_era5': 'Provisorio_ERA5',
          'provisoria_gfs': 'Previsao_GFS',
          'provisoria_gfs_incompleta': 'Previsao_GFS_Parcial',
          'falha_latencia_gfs': 'Sem_Dado'
        }).get(versaoImg, 'Desconhecido'); // [V4 M06-23] versão nova ou inesperada não vira histórico
        // Versão do motor que gravou o dia (dias sem a propriedade são da V1.0)
        var algImg = ee.Algorithms.If(
          img.propertyNames().contains('versao_algoritmo'), img.get('versao_algoritmo'), 'V1.0');
        // [V4 F8/M06-05] Janela da chuva: BR-DWGD (versao 'definitiva' ou ausente) de 12 UTC de D-1 a
        // 12 UTC de D; os demais (ERA5, GFS) no dia civil em UTC. Só rótulo: os valores não mudam.
        var janelaChuva = ee.Algorithms.If(versaoImg.equals('definitiva'), '12-12 UTC (D-1 a D)', '00-24 UTC');
        // [V4 Conf] Confiança por prazo gravada pelo motor V1.5 nos dias GFS; vazia se não existir
        var confPrazo = ee.Algorithms.If(
          img.propertyNames().contains('Confianca_Prazo'), img.get('Confianca_Prazo'), '');

        var propsEnso = cenarioEnso ? propsEnsoDaImagem(img, cenarioEnso) : {};   // [V4.1 22/10]
        return img.reduceRegions({ collection: fcFiltrada, reducer: ee.Reducer.mean(), scale: APP.escalaAtual })
                  .map(function(f) {
                    return f.set('Data', ee.Date(img.get('system:time_start')).format('YYYY-MM-dd'))
                            .set('Tipo_Dado', flagPrevisao)
                            .set('Versao_Algoritmo', algImg)
                            .set('Janela_Chuva_UTC', janelaChuva)  // [V4 F8/M06-05]
                            .set('Confianca_Prazo', confPrazo)     // [V4 Conf]
                            .set(propsEnso);                       // [V4.1 22/10]
                  });
      }).flatten();

      var fcOrdenada = formatarExportacaoClima(fc, extrasDiaria); // [V4] [V4.1 22/10]
      var colunasSelecionadas = filtrarColunasPorVariaveis(getColunasClimaDiaria().concat(cenarioEnso ? COLUNAS_ENSO : [])); // [V4] [2026.10.5]
      var nomeArquivoFinal = 'Diaria_' + nomeSeguro + '_' + anoAtual + sufixoArquivoEnso(cenarioEnso);

      gerarLinkDownloadCSV(fcOrdenada, nomeArquivoFinal, colunasSelecionadas);
    });
  });
  });
}

function exportarSerieMensal(ic_periodo, nomesTarget, datas) {
  if (select_resolucao.getValue() !== 'Mensal' || !nomesTarget || !datas) return;

  var anoInicio = parseInt(datas.isoInicio.split('-')[0], 10);
  var anoFim = parseInt(datas.isoFim.split('-')[0], 10);

  var bandasSoma = ['pr_mm', 'chuva_efetiva', 'runoff_sup_mm', 'runoff_sub_mm', 'et_potencial', 'et_real', 'transpiracao_mm', 'deficit_diario'];
  var bandasMedia = ['tmax_C', 'tmin_C', 'RH', 'rs', 'u2', 'tsolo_C', 'tfolha_C', 'vpd', 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3', 'amplitude_diaria'];
  var cenarioEnso = APP.filtroEnso;   // [V4.1 22/10]
  var extrasMensal = cenarioEnso ? COLUNAS_NOVAS_MENSAL.concat(COLUNAS_ENSO) : COLUNAS_NOVAS_MENSAL;

  comAnosComDados(ic_periodo, anoInicio, anoFim, function(anosComDados) {   // [V4.1 22/10]
  nomesTarget.forEach(function(nome) {
    var nomeSeguro = limparNomeArquivo(nome);
    var fcFiltrada = APP.regiaoFC.filter(ee.Filter.eq('Nome_Local_Export', nome));

    anosComDados.forEach(function(anoAtual) {
      var startAno = ee.Date.fromYMD(anoAtual, 1, 1);
      var endAno = ee.Date.fromYMD(anoAtual, 12, 31).advance(1, 'day');
      var ic_ano = ic_periodo.filterDate(startAno, endAno);

      var mesesList = ee.List.sequence(0, 11);
      
      var ic_mensal = ee.ImageCollection.fromImages(mesesList.map(function(m) {
        var dStart = startAno.advance(m, 'month');
        var dEnd = dStart.advance(1, 'month');
        var ic_mes = ic_ano.filterDate(dStart, dEnd);

        var imgSum = ic_mes.select(bandasSoma).sum();
        var imgMean = ic_mes.select(bandasMedia).mean();
        var imgConsolidada = imgSum.addBands(imgMean);

        // Versões do motor presentes no mês (ex.: "V1.0" no histórico, "V1.3" em 2026)
        var versoesMes = ic_mes.map(function(im) {
          return im.set('alg_tmp', ee.Algorithms.If(
            im.propertyNames().contains('versao_algoritmo'), im.get('versao_algoritmo'), 'V1.0'));
        }).aggregate_array('alg_tmp').distinct().sort();

        var dataStr = dStart.format('YYYY-MM-dd');
        // [V4 F4/M06-04] dias do mês no calendário (último dia do mês, inteiro) e mês completo
        var diasNoMes = dEnd.advance(-1, 'day').get('day');
        // [V4.1 22/10] com o filtro ENSO, o mês leva a fase do trimestre centrado nele (igual em todos os dias)
        var propsEnsoMes = cenarioEnso ? propsEnsoDaImagem(ee.Image(ee.Algorithms.If(ic_mes.size().gt(0),
                                          ic_mes.first(), ee.Image(0).set('system:time_start', dStart.millis()))),
                                          cenarioEnso) : {};
        return imgConsolidada.set(propsEnsoMes).set('Data', dataStr, 'n_imgs', ic_mes.size(),
                                  'Versao_Algoritmo', ee.List(versoesMes).join('+'),
                                  'Dias_no_Mes', diasNoMes,
                                  'Mes_Completo', ee.Algorithms.If(ic_mes.size().eq(diasNoMes), 'sim', 'nao'));
      })).filter(ee.Filter.gt('n_imgs', 0));

      var fc_anual = ic_mensal.map(function(img) {
        return img.reduceRegions({
          collection: fcFiltrada,
          reducer: ee.Reducer.mean(),
          scale: APP.escalaAtual
        }).map(function(f) {
          return f.set('Data', img.get('Data')).set('Tipo_Dado', 'Agregado_Mensal')
                  .set('Versao_Algoritmo', img.get('Versao_Algoritmo'))
                  .set('N_Dias', img.get('n_imgs'))                // [V4 F4/M06-04]
                  .set('Dias_no_Mes', img.get('Dias_no_Mes'))      // [V4 F4/M06-04]
                  .set('Mes_Completo', img.get('Mes_Completo'))    // [V4 F4/M06-04]
                  .set(copiarColunasEnso(img, cenarioEnso));   // [V4.1 22/10]
        });
      }).flatten();

      var fcOrdenada = formatarExportacaoClima(fc_anual, extrasMensal); // [V4] [V4.1 22/10]
      var colunasSelecionadas = filtrarColunasPorVariaveis(getColunasClimaMensal().concat(cenarioEnso ? COLUNAS_ENSO : [])); // [V4] [2026.10.5]
      var nomeArquivoFinal = 'Mensal_' + nomeSeguro + '_' + anoAtual + sufixoArquivoEnso(cenarioEnso);

      gerarLinkDownloadCSV(fcOrdenada, nomeArquivoFinal, colunasSelecionadas);
    });
  });
  });
}

// ============================================================
// MODULO 18: MOTOR DE PROCESSAMENTO PRINCIPAL E PIPELINE
// ============================================================
function liberarBotaoProcessamento() {
  APP.processando = false;
  btn_processar.setLabel('PROCESSAR DADOS CLIMÁTICOS');
  btn_processar.setDisabled(false);
  if (APP.startTime) {
    var tempoSegundos = ((Date.now() - APP.startTime) / 1000).toFixed(1);
    logInfo('Processamento concluído em ' + tempoSegundos + ' segundos. Mapa destravado.');
  } else {
    logInfo('Processamento finalizado e mapa destravado');
  }
}

function registrarErroProcessamento(msg) {
  logError(msg);
  liberarBotaoProcessamento();
}

btn_processar.onClick(function() {
  if (APP.processando) return;

  // [V4 Q1] A verificação da máscara de qualidade é assíncrona (dura poucos segundos ao abrir o painel)
  if (APP.mascaraQualidadeOk === null || APP.brdwgdOk === null) {   // [2026.11.1] e a do BR-DWGD
    mostrarAlertaTela('⏳ A verificação da máscara de qualidade ainda está em andamento. Aguarde alguns segundos e clique de novo em PROCESSAR DADOS CLIMÁTICOS.');
    return;
  }

  var strInicio = box_inicio.getValue();
  if (!dataEhValida(strInicio)) {
    mostrarAlertaTela('⚠️ ERRO DE DATA: A data inicial informada é inválida. Verifique o dia inserido.');
    return; 
  }

  var isoInicioCheck = converterDataParaISO(strInicio);
  var anoInicioUser = parseInt(isoInicioCheck.split('-')[0], 10);
  
  if (anoInicioUser < 1961) {
    mostrarAlertaTela('⚠️ PERÍODO INVÁLIDO: O banco de dados oficial SAB inicia em 01/01/1961. Insira uma data a partir deste ano.');
    return;
  }
  
  // [2026.10.5] com "Todas as variáveis" desmarcada, pelo menos uma tem de estar marcada
  var varsEscolhidas = variaveisEscolhidas();
  if (varsEscolhidas && varsEscolhidas.length === 0) {
    mostrarAlertaTela('⚠️ Marque pelo menos uma variável, ou marque "Todas as variáveis".');
    return;
  }

  var strFim = box_fim.getValue();
  if (!dataEhValida(strFim)) {
    mostrarAlertaTela('⚠️ ERRO DE DATA: As datas informadas são inválidas ou não existem no calendário.');
    return; 
  }

  var isEstadoOuVariosMunis = (select_abrangencia.getValue() === 'Estados / Municípios') &&
                              (!check_filtrar_munis.getValue() || lista_cidades_array.length > 1);

  if (isEstadoOuVariosMunis) {
    var msg = 'A extração para múltiplos municípios ou estados inteiros exige processamento intensivo do servidor e pode gerar lentidão no carregamento das planilhas. Para maior rapidez, recomendamos reduzir o período total de anos analisado. Deseja continuar mesmo assim?';
    mostrarConfirmacaoTela(msg, iniciarProcessamentoReal);
  } else {
    iniciarProcessamentoReal();
  }
});

function iniciarProcessamentoReal() {
  APP.processando = true;
  APP.startTime = Date.now(); 
  APP.abrangenciaAtual = select_abrangencia.getValue();
  btn_processar.setDisabled(true);
  btn_processar.setLabel('⏳ PROCESSANDO MATRIZ...');

  limparMapaParaNovoProcessamento();

  var regiaoInfo = construirRegiaoSelecionada();
  if (!regiaoInfo) { registrarErroProcessamento('Não foi possível montar a região de análise.'); return; }

  APP.regiaoGeom = regiaoInfo.poligonos_fc ? regiaoInfo.poligonos_fc.geometry() : regiaoInfo.regiao_fc.geometry();
  APP.escalaAtual = regiaoInfo.escala;
  
  APP.regiaoFC = regiaoInfo.regiao_fc; 

  meuMapa.centerObject(APP.regiaoGeom, zoomPorAbrangencia(regiaoInfo.tipo));
  logInfo('Região validada', { nome: regiaoInfo.nome_local, tipo: regiaoInfo.tipo, escala: regiaoInfo.escala });

  logStep('Início do processamento principal');
  var datas = obterDatasInterface();
  if (!datas) { registrarErroProcessamento('Período inválido.'); return; }

  var fonte = select_fonte.getValue();

  if (check_previsao.getValue()) {
    var dataHojeRef = ee.Date(Date.now()).update({hour:0, minute:0, second:0});
    var diffDiasParaHoje = dataHojeRef.difference(datas.dataFim, 'day');
    
    if (diffDiasParaHoje.abs().lte(60)) {
       var ultimoDiaFuturo = dataHojeRef.advance(15, 'day');
       datas.dataFim = ultimoDiaFuturo;
       datas.dataFimGEE = ultimoDiaFuturo.advance(1, 'day'); 
       
       var partesIni = datas.isoInicio.split('-');
       var dIniJS = new Date(partesIni[0], partesIni[1] - 1, partesIni[2]);
       var dFimJS = new Date(); 
       dFimJS.setDate(dFimJS.getDate() + 15);
       datas.totalDias = Math.floor((dFimJS.getTime() - dIniJS.getTime()) / (1000 * 3600 * 24)) + 1;
       // 2026.10.3a: a data final em texto também avança; sem isso, de 17 a 31/12 os dias de
       // previsão de janeiro ficavam fora dos CSV (o laço por ano parava no ano antigo)
       // em UTC, como a data final do servidor (dataHojeRef + 15 dias)
       var dFimUTC = new Date(Date.now() + 15 * 864e5);
       datas.isoFim = dFimUTC.getUTCFullYear() + '-' + ('0' + (dFimUTC.getUTCMonth() + 1)).slice(-2) + '-' +
                      ('0' + dFimUTC.getUTCDate()).slice(-2);
       
       logInfo('Caixa de previsão ativa: Data final estendida automaticamente em 15 dias.');
    } else {
       logWarn('Caixa de previsão ignorada: O período selecionado é estritamente histórico.');
    }
  }

  // [V4 F2/M06-03] A avaliação inicial traz também o número de pares pixel × polígono: acima do
  // limite, a lista seria cortada e os pixels do fim da ordenação sumiriam do CSV sem aviso.
  ee.Dictionary({ n: regiaoInfo.regiao_fc.size(), nPares: regiaoInfo.n_pares }).evaluate(function(contagem, err) {
    var n = contagem ? contagem.n : 0;
    APP.nPontos = n;   // [2026.10.5] para decidir entre link na hora e e-mail
    if (err || !n || n === 0) { registrarErroProcessamento('Região não encontrada ou vazia.'); return; }
    if (contagem.nPares > CFG.limitePontosGrade) {
      mostrarAlertaTela('⚠️ ÁREA GRANDE DEMAIS: a seleção gera ' + contagem.nPares + ' pares pixel × polígono, acima do limite de ' +
                        CFG.limitePontosGrade + '. Para não descartar pontos em silêncio, o processamento foi cancelado. ' +
                        'Reduza a área (menos estados, municípios ou polígonos) e processe de novo.');
      registrarErroProcessamento('Grade com ' + contagem.nPares + ' pares pixel × polígono (limite ' + CFG.limitePontosGrade + '). Processamento cancelado.');
      return;
    }
    logInfo('Grade de extração: ' + contagem.nPares + ' pares pixel × polígono (limite ' + CFG.limitePontosGrade + ').');

    var ic_periodo = getClimateCollection(fonte, APP.regiaoGeom, datas.dataIni, datas.dataFimGEE);

    // --- FILTRO HISTÓRICO ENSO (só no passado; a previsão continua sempre incluída) ---
    APP.filtroEnso = null;   // [V4.1 22/10] cenário do filtro ENSO em uso (colunas e nomes dos CSV)
    if (check_usar_enso.getValue() && select_enso.getValue() !== 'Todos os Anos') {
      APP.filtroEnso = select_enso.getValue();
      // [V4.1 22/10, correção 2] separa pelo tipo de dado, não pela data de hoje: os dias de previsão
      // de datas já passadas (ainda sem ERA5) também ficam todos no arquivo
      var VERSOES_PREVISAO = ['provisoria_gfs', 'provisoria_gfs_incompleta', 'falha_latencia_gfs'];
      var ehPrevisao = ee.Filter.inList('versao', VERSOES_PREVISAO);
      var icFuturo = ic_periodo.filter(ehPrevisao);
      var icPassado = ic_periodo.filter(ee.Filter.or(ee.Filter.notNull(['versao']).not(), ehPrevisao.not()));
      ic_periodo = filtrarHistoricoPorENSO(icPassado).merge(icFuturo);
    }

    // A previsão GFS já está gravada no banco SAB pelo motor Python (dias provisórios).
    // A extensão de 15 dias feita acima já a inclui; gerar outra aqui duplicava os dias.
    ic_periodo = ic_periodo.sort('system:time_start');

    ee.Dictionary({ qtd_periodo: ic_periodo.size() }).evaluate(function(status, erro) {
      if (erro) {
        logError('❌ DETALHE TÉCNICO DO ERRO NO SERVIDOR:', erro); 
        mostrarAlertaTela('⚠️ Erro interno do Servidor.\n\nProvavelmente os ASSETS estão privados. Vá no painel do Earth Engine > aba Assets > Share > "Anyone can read".');
        registrarErroProcessamento('Falha ao validar coleções climáticas.');
        return;
      }

      if (!status.qtd_periodo || status.qtd_periodo === 0) {
        mostrarAlertaTela('⚠️ SEM DADOS: Nenhum dado de clima foi encontrado para o período informado.'); 
        registrarErroProcessamento('Processo cancelado. Matriz climática retornou vazia.');
        return; 
      }

      var isEstadoOuVariosMunis = (select_abrangencia.getValue() === 'Estados / Municípios') &&
                                  (!check_filtrar_munis.getValue() || lista_cidades_array.length > 1);

      if (isEstadoOuVariosMunis) {
        mostrarAlertaTela('⚠️ PROCESSAMENTO EM ANDAMENTO: A extração para amplas regiões pode levar alguns minutos. Como o sistema gera arquivos separados por ano automaticamente, aguarde a liberação dos links. Para análises mais rápidas no futuro, considere reduzir o período pesquisado.');
      }

      // =========================================================================
      // AUDITORIA APLICADA: GRAMPO TERMODINÂMICO ON-THE-FLY
      // =========================================================================
      ic_periodo = ic_periodo.map(function(img) {
        var imagem = ee.Image(img);
        
        // 1. Aplica o limite físico (A ET Real nunca ultrapassa a demanda da ET Potencial)
        var et_pot = imagem.select('et_potencial');
        var et_real_bruta = imagem.select('et_real');
        var transp_bruta = imagem.select('transpiracao_mm');
        
        var et_real_limitada = et_real_bruta.min(et_pot).rename('et_real');
        var transp_limitada = transp_bruta.min(et_real_limitada).rename('transpiracao_mm');
        
        // Sobrescreve as bandas antigas pelas bandas corrigidas fisicamente
        imagem = imagem.addBands([et_real_limitada, transp_limitada], null, true);

        // 2. Realiza o cálculo do déficit hídrico com a ET_Real já corrigida
        var tmax = imagem.select('tmax_C');
        var tmin = imagem.select('tmin_C');
        var amp_diaria = tmax.subtract(tmin).rename('amplitude_diaria').toFloat();
        var def_diario = et_pot.subtract(et_real_limitada).max(0).rename('deficit_diario').toFloat();
        var chuva_ef = imagem.select('pr_mm').subtract(imagem.select('runoff_sup_mm')).max(0).rename('chuva_efetiva').toFloat();
        
        return imagem.addBands(ee.Image.cat([amp_diaria, def_diario, chuva_ef]));
      });

      ic_periodo = ee.ImageCollection(ic_periodo);

      var metrics = calcularMetricasClimaticas(ic_periodo);
      APP.colecaoClimaticaAtual = ic_periodo;
      
      adicionarCamadasBaseMapa(regiaoInfo);
      garantirCamadasOpcionaisSempreVisiveisNoPainel(APP.regiaoGeom);
      
      // 2026.10.3a: o tipo gravado em regiaoInfo é 'Coordenadas (Lat / Lon)'; os dois rótulos antigos nunca ocorriam
      var pontosCoordsGeom = (regiaoInfo.tipo === 'Coordenadas (Lat / Lon)') ? regiaoInfo.lista_coords_puras : null;
      adicionarCamadasInfraestrutura(APP.regiaoGeom, APP.escalaAtual, pontosCoordsGeom);
      atualizarOverlaysIndependentes();
      
      try { adicionarCamadasClimaticas(metrics, regiaoInfo, { mascaraAtiva: false, maskAgro: null, colecao_umidade: null, constelacao_ndvi: null, totalDias: datas.totalDias }); }
      catch(e) { logWarn('Não foi possível carregar as camadas visuais.', e.message); }

      var camadaPixelsCobertura;
      if (select_abrangencia.getValue() === 'Estados / Municípios' && !check_filtrar_munis.getValue()) {
          var projNativa = ee.Projection('EPSG:4326', [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]);
          var areaAmostragem = APP.regiaoGeom.buffer(CFG.escalaArea, 1000);
          
          // [V4 revisão B-09] Mesma grade dos pontos de extração: sem os pixels de classe 4 quando a máscara existe
          var imgCobertura = ee.Image.pixelLonLat();
          if (APP.mascaraQualidadeOk === true) {
              imgCobertura = imgCobertura.updateMask(
                  ee.Image(CFG.assets.mascaraQualidade).select('classe').unmask(0, false).neq(4));
          }
          var amostrasGrid = imgCobertura.sample({
              region: areaAmostragem,
              projection: projNativa, 
              geometries: true,
              dropNulls: true
          });
          
          camadaPixelsCobertura = amostrasGrid.map(function(f) {
              return ee.Feature(f.geometry().buffer(CFG.escalaArea / 2, 100).bounds());
          }).filterBounds(APP.regiaoGeom);

      } else {
          camadaPixelsCobertura = APP.regiaoFC.map(function(f) { 
            return ee.Feature(f.geometry().buffer(CFG.escalaArea / 2, 100).bounds()); 
          });
      }
      
      registrarCamada('cobertura_pixels', 'Infraestrutura e pontos', 'Área de Cobertura', camadaPixelsCobertura.style({ color: '#FFA500', fillColor: '#FFA50033', width: 1 }), {}, true );     
      construirPainelCamadas();

      APP.regiaoFC.aggregate_array('Nome_Local_Export').distinct().evaluate(function(nomesTarget, erroNomes) {
        if (erroNomes || !nomesTarget) { registrarErroProcessamento('Falha ao extrair nomes para exportação individual.'); return; }
        
        exportarDicionarioAutomatizado();

        // [2026.10.5] Link na hora só para recortes que cabem nele; os grandes vão por e-mail
        var entrega = decidirEntrega(APP.nPontos, nomesTarget.length, datas);
        if (entrega.link) {
          exportarSerieDiaria(ic_periodo, nomesTarget, datas);
          exportarSerieMensal(ic_periodo, nomesTarget, datas);
          logInfo('Os links de download estão sendo gerados no painel esquerdo.');
        } else {
          painel_downloads_app.add(ui.Label('ℹ️ Recorte grande demais para o link na hora: use "Receber por e-mail" abaixo.',
                                            {fontSize: '11px', color: '#1d70b8', margin: '2px 0'}));
          logInfo('Recorte grande (' + entrega.linhas + ' linhas): links na hora não gerados; envio por e-mail oferecido.');
        }
        if (CFG.urlPedidoEmail) {
          mostrarPedidoEmail(entrega.motivo, montarCodigoPedido(datas));   // qualquer busca, com ou sem filtro ENSO
        } else if (entrega.grande) {
          painel_downloads_app.add(ui.Label(
            'Recorte grande para o link na hora: alguns links podem falhar. Se falharem, reduza o período ou a área.',
            {fontSize: '11px', color: '#d32f2f', margin: '2px 0'}));
        }
        liberarBotaoProcessamento();
      });
    });
  });
}

atualizarDicaData(select_fonte.getValue());
atualizarTextoListaEstados();
atualizarTextoListaMunis();
atualizarTextoListaCoords();
atualizarListaCidades();
// 2026.10.3a: chamada restaurada (existia na 2026.10.2 e foi perdida na 2026.10.3)
atualizarVisibilidadeEspacial(select_abrangencia.getValue());
// [V4 Q1] verifica uma vez, sem bloquear a abertura, se a máscara de qualidade já existe
verificarMascaraQualidade();
verificarBRDWGD();   // [2026.11.1]

