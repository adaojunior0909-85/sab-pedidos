/**
 * SAB: ENVIO DOS DADOS POR E-MAIL (Apps Script da planilha de respostas do formulário). Versão 2026.11.15
 * [2026.11.15] TETO GERAL DE PEDIDOS POR DIA (CONFIG.MAX_PEDIDOS_DIA = 30, de todos os e-mails, recusados inclusive). O
 *   endereço do App da Web está no painel público; antes, o único limite era por e-mail, e pedidos com e-mails
 *   diferentes podiam esgotar a cota diária do Gmail e mandar e-mails da conta do SAB para qualquer endereço. Acima do
 *   teto, o pedido é recusado sem e-mail ao solicitante (a página do painel mostra o motivo) e o responsável recebe UM
 *   aviso por dia. Pedidos da aba Pedidos_Teste não contam nem são barrados. Nada mais mudou.
 * [2026.11.08a] PEDIDO EM SEQUÊNCIA, SEM ESPERAR 10 MINUTOS ENTRE AS ETAPAS. Antes, cada etapa (arquivos prontos ->
 *   conversão para Excel -> e-mail -> próximo da fila) só andava na volta seguinte do verificarPedidos, de 10 em 10
 *   min: um pedido com Excel esperava até ~20 min a mais. Agora, enquanto houver pedido calculando ou convertendo,
 *   o verificarPedidos se agenda de novo para daqui a CONFIG.RAPIDO_MIN minuto (acionador de uma vez só,
 *   verificarRapido), e cada etapa segue na volta seguinte; a entrega e o despacho do próximo da fila acontecem na
 *   mesma volta. Depois de CONFIG.RAPIDO_JANELA_MIN min na mesma etapa, ou acima de CONFIG.RAPIDO_MAX_DIA voltas
 *   rápidas no dia (cota de execução do Apps Script), passa a CONFIG.RAPIDO_LENTO_MIN min. Sem pedido ativo, fica só
 *   o acionador de segurança de 10 em 10 min (registro de pendentes, janelas do motor, limpeza). Nada mais mudou.
 * [2026.11.08] Motor UMA vez por dia, às 23h07 (o GitHub começa ~40 min depois, ~23h47, e a rodada leva ~20 min). Uma
 *   janela só: 22h50 à 01h00 (folga para o atraso do GitHub). Vale para a V1.5 e para a V1.6. Substitui a 2026.11.04a
 *   (que está no ar) e a 2026.11.05 (que nunca foi implantada). Nada mais mudou.
 * [2026.11.05] Janelas do motor V1.6 (etapa 2): rodadas às 06h07 e 15h07 (o GitHub começa ~40 min depois). A janela da
 *   noite saiu; a da manhã vai até 08h30 (cobre também a rodada das 07h07, se a K21 indicar esse horário).
 * [2026.11.04] REGISTRO DOS PEDIDOS EM ABAS PRÓPRIAS. Cada pedido (formulário ou painel) vira UMA linha, na ordem de
 *   chegada, na aba "Pedidos" (usuários, ID SAB-0001, SAB-0002...) ou "Pedidos_Teste" (pedidos feitos com o e-mail do
 *   responsável ou com um dos EMAILS_TESTE; ID TESTE-0001...). A aba de respostas do formulário fica só com as respostas
 *   cruas: o script não escreve mais nela (antes o Forms inseria respostas no meio das linhas do painel e a ordem se
 *   perdia). zerarPedidos() apaga todos os pedidos, as respostas, as pastas SAB_pedido_ e zera a numeração.
 * =========================================================================================
 * O QUE FAZ
 *   1. aoEnviarFormulario: cada resposta do formulário vira um pedido com ID sequencial (SAB-0001) na aba Pedidos, entra
 *      na fila e recebe um e-mail de confirmação. Os dados pessoais (nome, e-mail, instituição) ficam SÓ nesta
 *      planilha.
 *   2. A fila manda ao GitHub só o ID e o código do pedido (local, período, variáveis, formato), um pedido por vez
 *      (CONFIG.MAX_EM_PREPARO), e nunca enquanto o motor SAB roda (CONFIG.JANELAS_MOTOR e a API do GitHub).
 *   3. verificarPedidos ([2026.11.08a] a cada 1 min enquanto há pedido ativo; de segurança, a cada 10 min): procura no Drive a pasta SAB_pedido_<ID>, lê o manifesto
 *      00_Pedido_<ID>.csv e, quando TODOS os arquivos listados estão lá: se o pedido pediu Excel, aciona a
 *      conversão no GitHub (sab_xlsx.py) e espera o 00_Conversao_<ID>.csv; depois compartilha a pasta como
 *      "qualquer pessoa com o link (leitor)" e manda o link por e-mail (com anexo .zip, se couber).
 *   4. Depois de CONFIG.DIAS_GUARDA dias, apaga a pasta do pedido (entregue ou com falha): o link deixa de
 *      funcionar e o espaço do Drive volta. A linha da planilha fica (registro do atendimento).
 *   5. montarFormulario (rodar uma vez, e de novo a cada mudança): monta no formulário as seções para escolher
 *      tudo sem o painel, SEM DIGITAR: estados por região, municípios por estado (lista do GAUL, a mesma que a
 *      rotina usa), pontos ou área; datas; diário ou mensal; El Niño/La Niña; formato (CSV ou Excel); variáveis.
 *   6. doGet (App da Web): o botão "Receber por e-mail" do painel abre este endereço com o pedido e os dados da
 *      pessoa; o pedido é registrado na hora, sem passar pelo formulário (mesma fila, limites e e-mails).
 *   [2026.11.03] O script tem UMA trava só. Se outra rotina estiver com ela (ex.: verificarPedidos lendo o Drive),
 *      o pedido não se perde mais: a linha é gravada sem ID e verificarPedidos a registra em 1 a 2 minutos
 *      (vale para o formulário e para o painel). Recarregar a página do painel não duplica o pedido.
 *
 * PROPRIEDADES DO SCRIPT (Configurações do projeto > Propriedades do script), nunca no código:
 *   GITHUB_APP_ID      [2026.11.02] número do GitHub App (App ID), criado uma vez; instalado no sab-pedidos e no
 *                      sab-motor, com Contents: Read and write e Actions: Read-only
 *   GITHUB_APP_CHAVE   a chave privada (.pem) do App, colada inteira. Com o App, o script gera sozinho um token que vale
 *                      1 hora a cada uso: NUNCA mais é preciso trocar token. (GITHUB_APP_INSTALACAO o script grava.)
 *   GITHUB_REPO        usuario/sab-pedidos
 *   MOTOR_REPO         usuario/sab-motor (opcional: sem ela, só as janelas de CONFIG.JANELAS_MOTOR seguram a fila)
 *   EMAIL_RESPONSAVEL  seu e-mail (recebe os avisos de falha e as respostas dos solicitantes). [2026.11.04a] Aceita mais de
 *                      um, separados por vírgula: os avisos vão para todos, as respostas para o primeiro. Pedidos feitos com eles
 *                      vão para a aba Pedidos_Teste (sem o limite diário por e-mail).
 *   EMAILS_TESTE       [2026.11.04] opcional: outros e-mails de teste, separados por vírgula (também vão para Pedidos_Teste)
 *   (Sem o App, ainda funcionam os tokens antigos: GITHUB_TOKEN para os pedidos e MOTOR_TOKEN para ler o motor.)
 *
 * DEPOIS DE COLAR: rode configurar() uma vez (cria as abas Pedidos e Pedidos_Teste e os acionadores), testarApp(),
 *   testarGitHub() (simulação),
 *   testarMotor() e montarFormulario(); depois atualize o App da Web (Implantar > Gerenciar implantações > lápis >
 *   Nova versão).
 * =========================================================================================
 */

const CONFIG = {
  NOME: 'SAB - Banco de Dados Agrometeorológicos',
  MAX_PEDIDOS_POR_EMAIL_DIA: 3,
  // [2026.11.15] Teto de pedidos de TODOS os e-mails em 24 h (recusados contam). Acima dele, o pedido é recusado SEM
  // e-mail ao solicitante: o endereço do App da Web está no painel público, e sem este teto alguém poderia mandar
  // centenas de pedidos com e-mails diferentes, esgotar a cota diária do Gmail e enviar spam pela conta do SAB.
  MAX_PEDIDOS_DIA: 30,
  MAX_EM_PREPARO: 1,           // pedidos calculando ao mesmo tempo (o Earth Engine roda as exportações em paralelo)
  HORAS_SEM_MANIFESTO: 6,      // nem o manifesto apareceu (GitHub sem resposta ou fila parada): falha
  // Nenhum pedido NOVO começa nestas janelas (horário de Brasília). Além delas, a fila também espera se a API do
  // GitHub mostrar o motor na fila ou rodando (MOTOR_REPO).
  // [2026.11.08] motor 1x por dia às 23h07; o GitHub começa ~40 min depois (~23h47) e a rodada leva ~20 min.
  JANELAS_MOTOR: [['22:50', '24:00'], ['00:00', '01:00']],
  // [2026.11.08a] Acompanhamento em sequência (ver o cabeçalho): volta rápida enquanto há pedido ativo
  RAPIDO_MIN: 1,               // minutos entre as voltas enquanto um pedido calcula ou converte
  RAPIDO_JANELA_MIN: 45,       // depois de 45 min na mesma etapa (pedido grande), as voltas ficam mais espaçadas
  RAPIDO_LENTO_MIN: 5,
  RAPIDO_MAX_DIA: 600,         // voltas rápidas por dia (~30 min de execução; a cota gratuita é 90 min por dia)
  HORAS_MAX_PREPARO: 48,       // arquivos não ficaram prontos: falha
  HORAS_MAX_CONVERSAO: 6,      // a conversão para Excel não terminou: entrega só o CSV, com aviso
  DIAS_GUARDA: 7,              // a pasta do pedido é apagada depois disso
  USO_MAX_DRIVE: 0.85,         // acima disso, novos pedidos esperam na fila
  TITULOS: {
    codigo: 'Código do pedido',
    resumo: 'Resumo do pedido',
    nome: 'Nome completo',
    email: ['E-mail para receber o link', 'Endereço de e-mail', 'Email Address', 'E-mail'],
    instituicao: 'Instituição',
    finalidade: 'Finalidade do uso dos dados',
    consentimento: 'Consentimento',
    origem: 'Como você quer fazer o pedido?',
    local: 'Local',
    estados: 'Estados',                                   // versões antigas (uma lista só); hoje, por região
    estadosRegiao: 'Estados - ',                          // + nome da região: 'Estados - Sul'
    estadoMun: 'Estado dos municípios',
    municipiosUF: 'Municípios - ',                        // + nome do estado: 'Municípios - Paraná'
    municipios: 'Municípios',                             // versões antigas (digitados)
    municipiosOutros: 'Municípios de outros estados (opcional)',
    pontos: 'Pontos (coordenadas)',
    vertices: 'Área (vértices do polígono)',
    dataIni: 'Data inicial',
    dataFim: 'Data final',
    previsao: 'Incluir a previsão dos próximos 15 dias?',
    enso: 'Filtrar por fenômeno El Niño / La Niña',
    resolucao: 'Resolução',
    formato: 'Formato dos arquivos',
    variaveis: 'Variáveis'
  },
  ORIGEM: {formulario: 'Vou escolher agora o local, o período e as variáveis', painel: 'Já escolhi no painel SAB (código preenchido)'},
  LOCAIS: {E: 'Estados', M: 'Municípios', C: 'Pontos (coordenadas)', P: 'Área desenhada (polígono)'},
  REGIOES: {'Norte': ['Acre', 'Amapá', 'Amazonas', 'Pará', 'Rondônia', 'Roraima', 'Tocantins'],
            'Nordeste': ['Alagoas', 'Bahia', 'Ceará', 'Maranhão', 'Paraíba', 'Pernambuco', 'Piauí',
                         'Rio Grande do Norte', 'Sergipe'],
            'Centro-Oeste': ['Distrito Federal', 'Goiás', 'Mato Grosso', 'Mato Grosso do Sul'],
            'Sudeste': ['Espírito Santo', 'Minas Gerais', 'Rio de Janeiro', 'São Paulo'],
            'Sul': ['Paraná', 'Rio Grande do Sul', 'Santa Catarina']},
  // rótulo no formulário -> código da rotina (sem vírgulas: o Forms junta as caixas marcadas com ", ")
  VARIAVEIS: [['Todas as variáveis', 'todas'], ['Precipitação (mm)', 'pr'], ['Chuva efetiva (mm)', 'ce'],
    ['Escoamento superficial (mm)', 'rsup'], ['Escoamento subsuperficial (mm)', 'rsub'],
    ['Temperatura máxima (°C)', 'tmax'], ['Temperatura mínima (°C)', 'tmin'], ['Amplitude térmica (°C)', 'amp'],
    ['Temperatura do solo (°C)', 'tsolo'], ['Temperatura de superfície (°C)', 'tfolha'],
    ['Umidade relativa do ar (%)', 'ur'], ['Vento a 2 m (m/s)', 'vento'], ['Radiação solar (MJ/m²)', 'rad'],
    ['Evapotranspiração potencial (mm)', 'etp'], ['Evapotranspiração real (mm)', 'etr'],
    ['Transpiração (mm)', 'transp'], ['Déficit hídrico (mm)', 'def'], ['Déficit de pressão de vapor (kPa)', 'dpv'],
    ['Umidade do solo de 0 a 5 cm (m³/m³)', 'us5'], ['Umidade do solo de 0 a 100 cm (m³/m³)', 'us100']],
  // rótulo no formulário -> fmt do código (sem vírgulas)
  FORMATOS: [['CSV (abre em qualquer programa; no Excel siga as instruções do e-mail)', 'csv'],
             ['Excel (.xlsx) com os números prontos para usar', 'xlsx'], ['CSV e Excel (.xlsx)', 'ambos']],
  UF: {AC: 'Acre', AL: 'Alagoas', AP: 'Amapá', AM: 'Amazonas', BA: 'Bahia', CE: 'Ceará', DF: 'Distrito Federal',
       ES: 'Espírito Santo', GO: 'Goiás', MA: 'Maranhão', MT: 'Mato Grosso', MS: 'Mato Grosso do Sul',
       MG: 'Minas Gerais', PA: 'Pará', PB: 'Paraíba', PR: 'Paraná', PE: 'Pernambuco', PI: 'Piauí',
       RJ: 'Rio de Janeiro', RN: 'Rio Grande do Norte', RS: 'Rio Grande do Sul', RO: 'Rondônia', RR: 'Roraima',
       SC: 'Santa Catarina', SP: 'São Paulo', SE: 'Sergipe', TO: 'Tocantins'},
  LIMITES: {estados: 6, municipios: 30, pontos: 200, areas: 10, vertices: 150, diasPrevisao: 15,
            linhasXlsx: 3000000},   // acima de 3 milhões de linhas, o pedido vai só em CSV (tempo da conversão)
  // Os mesmos cenários do filtro ENSO do painel (rótulo -> sufixo usado no código e no nome dos arquivos)
  ENSO: [['Sem filtro (todos os meses)', ''],
    ['El Niño muito forte, Super (+2,0 °C ou mais)', 'El_Nino_Muito_Forte'],
    ['El Niño forte (+1,5 a +1,9 °C)', 'El_Nino_Forte'], ['El Niño moderado (+1,0 a +1,4 °C)', 'El_Nino_Moderado'],
    ['El Niño fraco (+0,5 a +0,9 °C)', 'El_Nino_Fraco'], ['Neutro (entre −0,5 e +0,5 °C)', 'Neutro'],
    ['La Niña fraca (−0,5 a −0,9 °C)', 'La_Nina_Fraca'], ['La Niña moderada (−1,0 a −1,4 °C)', 'La_Nina_Moderada'],
    ['La Niña forte (−1,5 a −1,9 °C)', 'La_Nina_Forte'],
    ['La Niña muito forte, Super (−2,0 °C ou menos)', 'La_Nina_Muito_Forte']],
  // Anexa os arquivos (.zip) ao e-mail de entrega quando couberem: assim, quem não usa o Google Drive recebe direto
  ANEXO_MAX_CSV_MB: 40,
  ANEXO_MAX_ZIP_MB: 20,
  AVISO_ENTREGA: 'Os arquivos chegam POR E-MAIL: um link para uma pasta no Google Drive, que abre no navegador e não ' +
                 'exige conta Google; pedidos pequenos vêm também anexados (.zip). O link vale 7 dias. ATENÇÃO: os ' +
                 'e-mails automáticos podem cair na caixa de SPAM, Lixo eletrônico ou Promoções; procure lá também ' +
                 'e marque "Não é spam".',
  INSTRUCOES_EXCEL: 'COMO ABRIR O CSV NO EXCEL SEM ERRO NOS NÚMEROS (não abra com duplo clique):\n' +
    '  1. Abra o Excel em branco > aba Dados > Obter Dados > De Arquivo > De Texto/CSV e escolha o arquivo.\n' +
    '  2. Origem do Arquivo: 65001: Unicode (UTF-8) (mantém os acentos).\n' +
    '  3. Delimitador: Vírgula.\n' +
    '  4. Detecção de Tipo de Dados: Não detectar tipos de dados (o Excel não troca 18.40 por 1840 nem datas).\n' +
    '  5. Clique em Transformar Dados. Selecione as colunas numéricas (Ctrl + clique no título), botão direito > ' +
    'Alterar Tipo > Usando a Localidade... > Tipo de Dados: Número Decimal; Localidade: Inglês (Estados Unidos) > OK.\n' +
    '  6. Página Inicial > Fechar e Carregar.\n' +
    '  No LibreOffice Calc: Abrir > conjunto de caracteres Unicode (UTF-8), separador Vírgula, Idioma Inglês (EUA).\n' +
    '  Mais fácil: no próximo pedido, escolha o formato Excel (.xlsx), que já vem com os números prontos.',
  FEEDBACK: 'O QUE VOCÊ ACHOU? Responda a este e-mail contando como foi pedir os dados e o que achou deles (o que ' +
            'funcionou, o que faltou, algum valor estranho). Seu retorno orienta as próximas versões do SAB.',
  PIX: 'APOIE O SAB (opcional). O SAB é gratuito e roda em serviços de nuvem gratuitos, que limitam quantos dados ' +
       'podemos calcular e entregar por dia. Doações ajudam a manter e melhorar a automação e a atualização diária ' +
       'dos dados e da previsão. Chave PIX (celular): (46) 99907-5852. A doação é voluntária e não muda em nada o ' +
       'atendimento dos pedidos.',
  ARQUIVO_MUNICIPIOS: 'SAB_municipios_GAUL2015.csv',   // gravado pelo workflow "Lista de municípios" (GitHub)
  COLUNAS: ['ID_Pedido', 'Status', 'Detalhe', 'Enviado_em', 'Entregue_em', 'Link', 'Conversao_em'],
  // [2026.11.04] Registro: uma linha por pedido, em ordem de chegada, numa aba só do script
  ABA_PEDIDOS: 'Pedidos',
  ABA_TESTE: 'Pedidos_Teste',
  PREFIXO_ID: 'SAB-',
  PREFIXO_TESTE: 'TESTE-',
  CABECALHO: ['ID_Pedido', 'Recebido_em', 'Status', 'Detalhe', 'Origem', 'Nome completo', 'E-mail', 'Instituição',
              'Finalidade do uso dos dados', 'Consentimento', 'Código do pedido', 'Resumo do pedido', 'Enviado_em',
              'Entregue_em', 'Link', 'Conversao_em', 'Resposta_formulario'],
  ORIGEM_REGISTRO: {formulario: 'Formulário', painel: 'Painel SAB'},
  // Forma de citar o banco (aparece no e-mail de entrega); troque quando houver artigo, tese ou DOI
  CITACAO: 'RODRIGUES JUNIOR, Adão Alves. SAB - Banco de Dados Agrometeorológicos Diários do Brasil (1961-2026), ' +
           'versão 2026.10. Pato Branco: Universidade Tecnológica Federal do Paraná, 2026. Conjunto de dados no ' +
           'Google Earth Engine. Dados históricos: Xavier, A. C. et al. (2022). New improved Brazilian daily ' +
           'weather gridded data (1961–2020). International Journal of Climatology, 42(16), 8390–8404. ' +
           'https://doi.org/10.1002/joc.7731',
  CODIGO_TESTE: 'v=1;res=D;tipo=M;uf=Paraná;mun=Pato Branco;ini=2025-01-01;fim=2025-12-31;var=todas'
};

const FUSO = 'America/Sao_Paulo';

// ------------------------------------------------------------------ acionadores
function configurar() {
  const props = PropertiesService.getScriptProperties().getProperties();
  ['GITHUB_REPO', 'EMAIL_RESPONSAVEL'].forEach(function (p) {
    if (!props[p]) throw new Error('Falta a propriedade do script ' + p + ' (passo 6 do guia).');
  });
  if (!(props.GITHUB_APP_ID && props.GITHUB_APP_CHAVE) && !props.GITHUB_TOKEN) {
    throw new Error('Falta o acesso ao GitHub: as propriedades GITHUB_APP_ID e GITHUB_APP_CHAVE (GitHub App, passo U13).');
  }
  const aba = obterAba_();
  colunas_(aba);   // confere as perguntas do formulário
  const regs = abasRegistro_();   // [2026.11.04] cria as abas Pedidos e Pedidos_Teste, se faltarem
  const props0 = PropertiesService.getScriptProperties();
  if (!props0.getProperty('SAB_INICIO_REGISTRO')) props0.setProperty('SAB_INICIO_REGISTRO', new Date().toISOString());
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (['aoEnviarFormulario', 'verificarPedidos', 'verificarRapido'].indexOf(t.getHandlerFunction()) !== -1) ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('aoEnviarFormulario').forSpreadsheet(SpreadsheetApp.getActive()).onFormSubmit().create();
  ScriptApp.newTrigger('verificarPedidos').timeBased().everyMinutes(10).create();
  Logger.log('✅ Abas de registro: ' + regs.map(function (r) { return r.aba.getName(); }).join(' e ') +
             ' (respostas do formulário em "' + aba.getName() + '").');
  Logger.log('✅ Acionadores criados: aoEnviarFormulario (a cada resposta) e ' +
             'verificarPedidos (segurança, a cada 10 minutos; com pedido ativo, a cada ' + CONFIG.RAPIDO_MIN + ' min). Conta do script: ' + contaDoScript_() + '. Drive usado: ' +
             (usoDrive_() * 100).toFixed(1) + '%. Esta conta tem de ser a mesma do Earth Engine (clima-492922).');
}

// Simulação: aciona o GitHub com SIMULAR=1. Confira o resultado na aba Actions do repositório.
function testarGitHub() {
  const r = acionarGitHub_('TESTE_GITHUB', CONFIG.CODIGO_TESTE, true);
  Logger.log(r.ok ? '✅ GitHub aceitou o acionamento (204). Veja a execução "Pedido SAB" na aba Actions.'
                  : '❌ GitHub respondeu ' + r.codigo + ': ' + r.texto);
}

// [2026.11.02] Confere o GitHub App: chave, instalação, token de 1 hora e acesso aos dois repositórios
function testarApp() {
  const props = PropertiesService.getScriptProperties();
  if (!props.getProperty('GITHUB_APP_ID') || !props.getProperty('GITHUB_APP_CHAVE')) {
    Logger.log('❌ Faltam as propriedades GITHUB_APP_ID e GITHUB_APP_CHAVE (passo U13 do guia).');
    return;
  }
  CacheService.getScriptCache().remove('SAB_TOKEN_APP');
  let info;
  try {
    info = tokenApp_(true);
  } catch (erro) {
    Logger.log('❌ ' + (erro.message || erro));
    return;
  }
  Logger.log('✅ Chave do App aceita e token de 1 hora gerado (instalação ' + info.instalacao + ', vale até ' +
             info.expira + ').');
  Logger.log('   Permissões do token: ' + JSON.stringify(info.permissoes));
  const perm = info.permissoes || {};
  if (perm.contents !== 'write') Logger.log('❌ Falta "Contents: Read and write" no App (sem isso os pedidos não saem).');
  if (props.getProperty('MOTOR_REPO') && ['read', 'write'].indexOf(perm.actions) === -1) {
    Logger.log('⚠️ Falta "Actions: Read-only" no App (a fila só respeita as janelas de horário).');
  }
  [prop_('GITHUB_REPO'), props.getProperty('MOTOR_REPO')].filter(function (r) { return r; }).forEach(function (repo) {
    const r = UrlFetchApp.fetch('https://api.github.com/repos/' + repo, {muteHttpExceptions: true,
      headers: {Authorization: 'Bearer ' + info.token, Accept: 'application/vnd.github+json'}});
    Logger.log((r.getResponseCode() === 200 ? '✅ ' : '❌ ') + repo + ': ' + (r.getResponseCode() === 200 ?
      'o App tem acesso' : 'sem acesso (' + r.getResponseCode() + '): instale o App também neste repositório'));
  });
}

// Mostra se a fila seguraria um pedido agora (janela do motor ou motor rodando no GitHub)
function testarMotor() {
  const repo = PropertiesService.getScriptProperties().getProperty('MOTOR_REPO');
  Logger.log('MOTOR_REPO: ' + (repo || '(não definida: só as janelas de horário seguram a fila)'));
  const motivo = motorOcupado_(true);
  Logger.log(motivo ? '⏸️ A fila esperaria agora: ' + motivo : '▶️ A fila despacharia agora (motor parado e fora das janelas).');
}

// ------------------------------------------------------------------ 1. resposta do formulário
function aoEnviarFormulario(e) {
  const trava = LockService.getScriptLock();
  // [2026.11.03] sem waitLock: se outra rotina estiver com a trava, a resposta fica na planilha sem ID e
  // verificarPedidos a registra (antes a execução caía com "Tempo limite do bloqueio"). [2026.11.08a] em 1 a 2 min.
  if (!trava.tryLock(25000)) {
    marcarPendente_();
    Logger.log('⏳ Sistema ocupado: a resposta será registrada pelo verificarPedidos em 1 a 2 minutos.');
    return;
  }
  try {
    const aba = e && e.range ? e.range.getSheet() : obterAba_();
    const linha = e && e.range ? e.range.getRow() : aba.getLastRow();
    registrarResposta_(aba, colunas_(aba), linha);   // [2026.11.04] vira uma linha na aba Pedidos
  } finally {
    trava.releaseLock();
  }
}

// Uma linha da planilha (resposta do formulário ou pedido vindo do painel) vira pedido: confere, monta o código,
// aplica o limite por e-mail, põe na fila, manda a confirmação e aciona o GitHub se houver vaga.
// Devolve {ok, id, status, mensagem, resumo} para a página do pedido direto (doGet).
function processarLinha_(aba, linha, vForm) {
  const col = colunasRegistro_(aba);
  const teste = aba.getName() === CONFIG.ABA_TESTE;
  const v = lerLinha_(aba, linha, col);
  if (v.ID_Pedido) return {ok: true, id: v.ID_Pedido, status: v.Status, mensagem: 'Pedido já registrado.'};

  const id = gerarId_(teste);
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v.email)) {
    marcar_(aba, linha, col, {ID_Pedido: id, Status: 'recusado', Detalhe: 'E-mail inválido: ' + v.email});
    return {ok: false, id: id, status: 'recusado', mensagem: 'O e-mail "' + v.email + '" não é válido.'};
  }
  // [2026.11.15] Teto geral antes de qualquer e-mail sair (ver CONFIG.MAX_PEDIDOS_DIA)
  if (!teste && pedidosRecentes_(aba, col, null, linha) >= CONFIG.MAX_PEDIDOS_DIA) {
    marcar_(aba, linha, col, {ID_Pedido: id, Status: 'recusado', Detalhe: 'Limite diário geral de pedidos'});
    avisarLimiteGeral_();
    return {ok: false, id: id, status: 'recusado', mensagem: 'O SAB atingiu o limite de pedidos das últimas 24 horas. ' +
            'Tente de novo amanhã.'};
  }
  let pedido;
  try {
    pedido = montarCodigo_(vForm || v, new Date());   // [2026.11.04] respostas do formulário: lidas da aba do Forms
  } catch (erro) {
    const motivo = String(erro.message || erro);
    marcar_(aba, linha, col, {ID_Pedido: id, Status: 'recusado', Detalhe: motivo.slice(0, 300)});
    enviarEmail_(v.email, 'Pedido de dados SAB não aceito',
      'Olá, ' + v.nome + '.\n\nNão foi possível montar o seu pedido:\n\n' + motivo + '\n\nCorrija e envie de novo.\n\n' +
      assinatura_());
    return {ok: false, id: id, status: 'recusado', mensagem: motivo};
  }
  if (pedido.gerado || !v.codigo) {
    marcar_(aba, linha, col, {codigo: pedido.codigo, resumo: pedido.resumo || v.resumo});
    v.codigo = pedido.codigo;
    v.resumo = pedido.resumo || v.resumo;
  }
  if (!teste && pedidosRecentes_(aba, col, v.email, linha) >= CONFIG.MAX_PEDIDOS_POR_EMAIL_DIA) {
    marcar_(aba, linha, col, {ID_Pedido: id, Status: 'recusado', Detalhe: 'Limite diário por e-mail'});
    enviarEmail_(v.email, 'Pedido de dados SAB: limite diário atingido',
      'Olá, ' + v.nome + '.\n\nPara que todos sejam atendidos, cada e-mail pode fazer até ' +
      CONFIG.MAX_PEDIDOS_POR_EMAIL_DIA + ' pedidos a cada 24 horas. Tente de novo amanhã.\n\n' + assinatura_());
    return {ok: false, id: id, status: 'recusado', mensagem: 'Limite de ' + CONFIG.MAX_PEDIDOS_POR_EMAIL_DIA +
            ' pedidos por e-mail a cada 24 horas atingido. Tente de novo amanhã.'};
  }
  marcar_(aba, linha, col, {ID_Pedido: id, Status: 'na_fila', Detalhe: 'Aguardando vaga no cálculo'});
  enviarEmail_(v.email, 'Recebemos seu pedido de dados SAB (' + id + ')',
    'Olá, ' + v.nome + '.\n\nRecebemos seu pedido ' + id + ':\n\n' + v.resumo + '\n\n' +
    'Os arquivos são calculados no Google Earth Engine e você receberá outro e-mail assim que ' +
    'ficarem prontos. Costuma levar de 1 a 4 horas; pedidos grandes ou com fila podem levar até 2 dias.\n\n' +
    CONFIG.AVISO_ENTREGA + '\n\n' +
    assinatura_());
  despacharFila_();
  agendarRapido_(intervaloAcompanhamento_());   // [2026.11.08a] acompanha o pedido acionado agora, minuto a minuto
  return {ok: true, id: id, status: 'na_fila', resumo: v.resumo,
          mensagem: 'Pedido recebido. Você vai receber agora um e-mail de confirmação e, quando os arquivos ficarem ' +
                    'prontos, outro com o link.'};
}

// [2026.11.04] Uma resposta do formulário (linha da aba do Forms) vira uma linha na aba Pedidos (ou Pedidos_Teste) e é
// processada. A aba do Forms não é alterada. Devolve o resultado de processarLinha_.
function registrarResposta_(abaForm, colForm, linhaForm) {
  const vf = lerLinha_(abaForm, linhaForm, colForm);
  if (!vf.email && !vf.nome) return {ok: false, mensagem: 'Linha vazia.'};
  const ref = refResposta_(vf.carimbo, vf.email);
  const regs = abasRegistro_();
  if (regs.some(function (r) { return linhaPorRef_(r, ref); })) return {ok: true, mensagem: 'Resposta já registrada.'};
  const reg = registroDoEmail_(regs, vf.email);
  const linha = anexarPedido_(reg, {recebido: vf.carimbo instanceof Date ? vf.carimbo : new Date(vf.carimbo || Date.now()),
    origem: CONFIG.ORIGEM_REGISTRO.formulario, nome: vf.nome, email: vf.email, inst: String(vf.instituicao || ''),
    fin: String(vf.finalidade || ''), consent: String(vf.consentimento || ''), codigo: vf.codigo, resumo: vf.resumo, ref: ref});
  return processarLinha_(reg.aba, linha, vf);
}

// ------------------------------------------------------------------ pedido direto do painel (App da Web)
// O painel SAB abre este endereço com o pedido e os dados da pessoa; a página grava a linha na planilha, como se
// fosse uma resposta do formulário, e mostra o resultado. Publicar em Implantar > Nova implantação > App da Web.
function doGet(e) {
  const p = (e && e.parameter) || {};
  if (!p.codigo) {
    return pagina_('Pedido de dados SAB', 'Esta página recebe os pedidos feitos pelo painel SAB. Para pedir dados, use ' +
                   'o botão "Receber por e-mail" do painel ou o formulário.', null);
  }
  if (p.aceite !== '1') {
    return pagina_('Pedido não registrado', 'É preciso aceitar o uso dos dados (LGPD) no painel antes de enviar.', false);
  }
  const codigo = String(p.codigo).slice(0, 6000);
  const email = String(p.email || '').trim().slice(0, 120);
  let reg, aba, col;
  try {
    reg = registroDoEmail_(abasRegistro_(), email.toLowerCase());   // [2026.11.04] Pedidos ou Pedidos_Teste
    aba = reg.aba;
    col = reg.col;
  } catch (erro) {
    return pagina_('Pedido não registrado', 'Erro ao abrir a planilha de pedidos: ' + String(erro.message || erro) +
                   '. Tente de novo em alguns minutos.', false);
  }
  // [2026.11.03] Página recarregada ou link clicado duas vezes: não registra o mesmo pedido de novo
  const repetido = pedidoRepetido_(aba, col, email, codigo);
  if (repetido) {
    return pagina_('Pedido já recebido', (repetido.id ? 'Este pedido já foi registrado como ' + repetido.id + '. ' :
      'Este pedido já foi recebido e está sendo registrado. ') + 'Não precisa enviar de novo: a confirmação vai para ' +
      email + ' e, quando os arquivos ficarem prontos, chega outro e-mail com o link.', true);
  }
  const dados = {recebido: new Date(), origem: CONFIG.ORIGEM_REGISTRO.painel, codigo: codigo,
    resumo: String(p.resumo || '').slice(0, 500), nome: String(p.nome || '').slice(0, 120), email: email,
    inst: String(p.inst || '').slice(0, 160), fin: String(p.fin || '').slice(0, 80), consent: 'Aceito no painel SAB'};
  const trava = LockService.getScriptLock();
  // [2026.11.03] Antes: waitLock(30000), que derrubava a página com "Tempo limite do bloqueio" quando o
  // verificarPedidos estava com a trava. Agora, sem a trava, a linha é gravada sem ID e entra em 1 a 2 minutos.
  if (!trava.tryLock(20000)) {
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      return pagina_('Pedido não registrado', 'O e-mail "' + email + '" não é válido.', false);
    }
    dados.detalhe = 'Aguardando registro (sistema ocupado)';
    anexarPedido_(reg, dados);
    marcarPendente_();
    return pagina_('Pedido recebido', 'O sistema está ocupado neste momento, mas o seu pedido foi guardado. Em 1 a ' +
      '2 minutos você recebe o e-mail de confirmação com o número do pedido; quando os arquivos ficarem prontos, ' +
      'chega outro e-mail com o link. Não precisa enviar de novo.' + (p.resumo ? '\n\n' + String(p.resumo) : ''), true);
  }
  let r;
  try {
    r = processarLinha_(aba, anexarPedido_(reg, dados));
  } catch (erro) {
    r = {ok: false, mensagem: 'Erro ao registrar o pedido: ' + String(erro.message || erro)};
  } finally {
    trava.releaseLock();
  }
  return pagina_(r.ok ? 'Pedido recebido' : 'Pedido não registrado',
                 (r.id ? 'Pedido ' + r.id + '. ' : '') + r.mensagem + (r.resumo ? '\n\n' + r.resumo : ''), r.ok);
}

function pagina_(titulo, texto, ok) {
  const cor = ok === true ? '#1f6b52' : (ok === false ? '#b42318' : '#17241f');
  const esc = function (t) { return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); };
  const html = '<div style="font-family:Arial,sans-serif;max-width:560px;margin:40px auto;padding:0 16px;color:#17241f">' +
    '<h2 style="color:' + cor + '">' + esc(titulo) + '</h2>' +
    esc(texto).split('\n').map(function (l) { return '<p style="line-height:1.5">' + l + '</p>'; }).join('') +
    '<p style="color:#56645e;font-size:13px">' + esc(CONFIG.NOME) + '. Pode fechar esta aba.</p></div>';
  return HtmlService.createHtmlOutput(html).setTitle('Pedido SAB');
}

// ------------------------------------------------------------------ 2 a 4. acompanhamento
// [2026.11.08a] Em sequência: com pedido ativo, a próxima volta é agendada para daqui a CONFIG.RAPIDO_MIN minuto
// (verificarRapido, acionador de uma vez só); sem pedido ativo, só o acionador de segurança de 10 em 10 min.
function verificarRapido() {
  contarVoltaRapida_();
  verificarPedidos();
}

function verificarPedidos() {
  const trava = LockService.getScriptLock();
  if (!trava.tryLock(30000)) return;
  try {
    CacheService.getScriptCache().remove('SAB_PENDENTE');   // [2026.11.08a] o registro abaixo atende o aviso
    registrarPendentes_();   // [2026.11.03] pedidos que chegaram com o sistema ocupado
    const regs = abasRegistro_();
    regs.forEach(function (reg) {
      const aba = reg.aba, col = reg.col;
      const ultima = aba.getLastRow();
      const dados = ultima < 2 ? [] : aba.getRange(2, 1, ultima - 1, aba.getLastColumn()).getValues();
      for (let i = 0; i < dados.length; i++) {
        const linha = i + 2;
        const v = objeto_(dados[i], col);
        try {
          if (v.Status === 'enviado' || v.Status === 'em_preparo' || v.Status === 'convertendo') acompanhar_(aba, linha, col, v);
          else if (v.Status === 'entregue' || v.Status === 'falha') expirar_(aba, linha, col, v);
        } catch (erro) {
          Logger.log('❌ Pedido ' + v.ID_Pedido + ': ' + erro);
          marcar_(aba, linha, col, {Detalhe: 'Erro: ' + String(erro).slice(0, 200)});
        }
      }
    });
    limparOrfas_(regs);
    despacharFila_();
    agendarRapido_(intervaloAcompanhamento_());   // [2026.11.08a] etapa seguinte em 1 min, sem esperar os 10
  } finally {
    trava.releaseLock();
  }
}

// [2026.11.08a] Minutos até a próxima volta: CONFIG.RAPIDO_MIN com pedido calculando/convertendo (ou registro
// pendente); CONFIG.RAPIDO_LENTO_MIN se a etapa já passou de CONFIG.RAPIDO_JANELA_MIN min ou se o dia passou de
// CONFIG.RAPIDO_MAX_DIA voltas rápidas; 0 = nenhum pedido ativo (fica só o acionador de 10 em 10 min).
function intervaloAcompanhamento_() {
  const agora = Date.now();
  let minutos = 0;
  abasRegistro_().forEach(function (reg) {
    const ultima = reg.aba.getLastRow();
    if (ultima < 2) return;
    reg.aba.getRange(2, 1, ultima - 1, reg.aba.getLastColumn()).getValues().forEach(function (r) {
      const st = r[reg.col.Status - 1];
      if (['enviado', 'em_preparo', 'convertendo'].indexOf(st) === -1) return;
      const desde = st === 'convertendo' ? r[reg.col.Conversao_em - 1] : r[reg.col.Enviado_em - 1];
      const idade = (agora - new Date(desde || agora).getTime()) / 60000;
      const m = idade < CONFIG.RAPIDO_JANELA_MIN ? CONFIG.RAPIDO_MIN : CONFIG.RAPIDO_LENTO_MIN;
      minutos = minutos ? Math.min(minutos, m) : m;
    });
  });
  if (CacheService.getScriptCache().get('SAB_PENDENTE')) minutos = CONFIG.RAPIDO_MIN;
  if (minutos === CONFIG.RAPIDO_MIN && voltasRapidasHoje_() >= CONFIG.RAPIDO_MAX_DIA) minutos = CONFIG.RAPIDO_LENTO_MIN;
  return minutos;
}

// [2026.11.08a] Um acionador verificarRapido só (o anterior é apagado); minutos = 0 apaga e não cria
function agendarRapido_(minutos) {
  try {
    ScriptApp.getProjectTriggers().forEach(function (t) {
      if (t.getHandlerFunction() === 'verificarRapido') ScriptApp.deleteTrigger(t);
    });
    if (minutos > 0) ScriptApp.newTrigger('verificarRapido').timeBased().after(minutos * 60000).create();
  } catch (erro) {
    Logger.log('⚠️ Volta rápida não agendada (' + (erro.message || erro) + '); fica o acionador de 10 em 10 min.');
  }
}

// [2026.11.08a] Pedido gravado com o sistema ocupado: a volta rápida o registra em 1 a 2 min
function marcarPendente_() {
  CacheService.getScriptCache().put('SAB_PENDENTE', '1', 1800);
  agendarRapido_(CONFIG.RAPIDO_MIN);
}

function voltasRapidasHoje_() {
  const v = String(PropertiesService.getScriptProperties().getProperty('SAB_RAPIDO_DIA') || '').split('|');
  return v[0] === Utilities.formatDate(new Date(), FUSO, 'yyyy-MM-dd') ? Number(v[1]) || 0 : 0;
}

function contarVoltaRapida_() {
  PropertiesService.getScriptProperties().setProperty('SAB_RAPIDO_DIA',
    Utilities.formatDate(new Date(), FUSO, 'yyyy-MM-dd') + '|' + (voltasRapidasHoje_() + 1));
}

// [2026.11.03] Linhas das últimas 24 h sem ID e sem Status (formulário ou painel que chegaram com a trava ocupada):
// viram pedido agora, como se tivessem acabado de chegar. Linhas mais antigas não são tocadas.
function registrarPendentes_() {
  const desde = Math.max(Date.now() - 864e5, inicioRegistro_());
  // 1) linhas do painel gravadas sem ID (sistema ocupado)
  abasRegistro_().forEach(function (reg) {
    const aba = reg.aba, col = reg.col;
    const ultima = aba.getLastRow();
    if (ultima < 2) return;
    const dados = aba.getRange(2, 1, ultima - 1, aba.getLastColumn()).getValues();
    dados.forEach(function (r, i) {
      const quando = r[col.Recebido_em - 1] ? new Date(r[col.Recebido_em - 1]).getTime() : 0;
      if (!quando || quando < desde || r[col.ID_Pedido - 1] || r[col.Status - 1] || !String(r[col.email - 1]).trim()) return;
      try {
        processarLinha_(aba, i + 2);
      } catch (erro) {
        Logger.log('❌ ' + aba.getName() + ', linha ' + (i + 2) + ' sem registro: ' + erro);
        marcar_(aba, i + 2, col, {Detalhe: 'Erro ao registrar: ' + String(erro).slice(0, 200)});
      }
    });
  });
  // 2) respostas do formulário que não viraram pedido (sistema ocupado na hora da resposta)
  const abaForm = obterAba_(), colForm = colunas_(abaForm);
  const ultima = abaForm.getLastRow();
  if (ultima < 2) return;
  const linhas = abaForm.getRange(2, 1, ultima - 1, abaForm.getLastColumn()).getValues();
  linhas.forEach(function (r, i) {
    const quando = r[0] ? new Date(r[0]).getTime() : 0;
    if (!quando || quando < desde || !String(r[colForm.email - 1] || '').trim()) return;
    try {
      registrarResposta_(abaForm, colForm, i + 2);
    } catch (erro) {
      Logger.log('❌ Resposta do formulário da linha ' + (i + 2) + ' sem registro: ' + erro);
    }
  });
}

// [2026.11.03] Mesmo e-mail e mesmo código nas últimas 2 horas, ainda em andamento (ou esperando registro):
// {id} do pedido já existente (id vazio se ainda sem ID), ou null.
function pedidoRepetido_(aba, col, email, codigo) {
  const ultima = aba.getLastRow();
  if (ultima < 2 || !email || !codigo) return null;
  const dados = aba.getRange(2, 1, ultima - 1, aba.getLastColumn()).getValues();
  const desde = Date.now() - 2 * 3.6e6;
  const vivos = ['', 'na_fila', 'enviado', 'em_preparo', 'convertendo'];
  for (let i = dados.length - 1; i >= 0; i--) {
    const r = dados[i];
    const quando = r[col.Recebido_em - 1];
    if (!quando || new Date(quando).getTime() < desde) continue;
    if (String(r[col.email - 1]).trim().toLowerCase() !== email.toLowerCase()) continue;
    if (String(r[col.codigo - 1] || '').trim() !== codigo.trim()) continue;
    if (vivos.indexOf(String(r[col.Status - 1] || '')) === -1) continue;
    return {id: String(r[col.ID_Pedido - 1] || '')};
  }
  return null;
}

// Uma vez por dia: apaga as pastas SAB_pedido_<ID> com mais de DIAS_GUARDA dias que não pertencem a nenhum pedido em
// andamento ou entregue (ex.: pedido devolvido à fila com ID novo, testes antigos). Não toca em outras pastas.
function limparOrfas_(regs) {
  const props = PropertiesService.getScriptProperties();
  const hoje = Utilities.formatDate(new Date(), FUSO, 'yyyy-MM-dd');
  if (props.getProperty('SAB_LIMPEZA') === hoje) return;
  props.setProperty('SAB_LIMPEZA', hoje);
  const vivos = {};
  regs.forEach(function (reg) {
    const ultima = reg.aba.getLastRow();
    const dados = ultima < 2 ? [] : reg.aba.getRange(2, 1, ultima - 1, reg.aba.getLastColumn()).getValues();
    dados.forEach(function (r) {
      if (['na_fila', 'enviado', 'em_preparo', 'convertendo', 'entregue', 'falha'].indexOf(r[reg.col.Status - 1]) !== -1) {
        vivos[String(r[reg.col.ID_Pedido - 1])] = true;
      }
    });
  });
  const it = DriveApp.searchFolders('title contains "SAB_pedido_"');
  const apagar = [];
  while (it.hasNext()) {
    const p = it.next();
    const id = p.getName().replace(/^SAB_pedido_/, '');
    if (p.getName().indexOf('SAB_pedido_') !== 0 || vivos[id] || p.isTrashed()) continue;
    if ((Date.now() - p.getDateCreated().getTime()) / 864e5 > CONFIG.DIAS_GUARDA) apagar.push(p);
  }
  if (apagar.length) {
    Logger.log('🧹 Pastas órfãs apagadas: ' + apagar.map(function (p) { return p.getName(); }).join(', '));
    apagarPastas_(apagar);
  }
}

function acompanhar_(aba, linha, col, v) {
  const horas = (Date.now() - new Date(v.Enviado_em).getTime()) / 3.6e6;
  // O Earth Engine pode criar MAIS DE UMA pasta com o mesmo nome quando duas exportações começam juntas:
  // o pedido é a soma de todas as pastas SAB_pedido_<ID>; na entrega, tudo vai para a pasta do manifesto.
  const pastas = pastasDoPedido_(v.ID_Pedido);
  const man = lerManifesto_(pastas, v.ID_Pedido);
  if (!man) {
    marcar_(aba, linha, col, {Detalhe: (pastas.length ? 'Pasta achada; manifesto ainda não chegou' :
      'Pasta SAB_pedido_' + v.ID_Pedido + ' ainda não está no Drive de ' + contaDoScript_())});
    if (horas > CONFIG.HORAS_SEM_MANIFESTO) falhar_(aba, linha, col, v, 'O cálculo não começou ou a pasta não apareceu ' +
      'no Drive de ' + contaDoScript_() + ' (GitHub sem resposta ou Earth Engine em outra conta).');
    return;
  }
  if (man.status === 'recusado') {
    marcar_(aba, linha, col, {Status: 'recusado', Detalhe: man.motivo});
    enviarEmail_(v.email, 'Pedido de dados SAB não atendido (' + v.ID_Pedido + ')',
      'Olá, ' + v.nome + '.\n\nSeu pedido ' + v.ID_Pedido + ' não pôde ser atendido:\n\n' + man.motivo + '\n\n' +
      'Ajuste o pedido e envie de novo.\n\n' + assinatura_());
    apagarPastas_(pastas);
    return;
  }
  if (man.status === 'falha') { falhar_(aba, linha, col, v, man.motivo); return; }   // pastas ficam para diagnóstico

  const fmt = man.formato || formatoDoCodigo_(v.codigo);
  if (v.Status === 'convertendo') {
    const conv = lerMarcador_(pastas, v.ID_Pedido);
    const horasConv = (Date.now() - new Date(v.Conversao_em || v.Enviado_em).getTime()) / 3.6e6;
    if (conv) { entregar_(aba, linha, col, v, man, pastas, fmt, conv); return; }
    marcar_(aba, linha, col, {Detalhe: 'Convertendo para Excel (GitHub)'});
    if (horasConv > CONFIG.HORAS_MAX_CONVERSAO) {
      entregar_(aba, linha, col, v, man, pastas, fmt, {ok: 0, erros: ['a conversão não terminou em ' +
        CONFIG.HORAS_MAX_CONVERSAO + ' h']});
    }
    return;
  }

  const faltam = man.arquivos.filter(function (a) { return !temArquivo_(pastas, a); });
  const prontos = man.arquivos.length - faltam.length;
  if (faltam.length) {
    marcar_(aba, linha, col, {Status: 'em_preparo', Detalhe: prontos + ' de ' + man.arquivos.length + ' arquivos prontos'});
    if (horas > CONFIG.HORAS_MAX_PREPARO) falhar_(aba, linha, col, v, 'Arquivos não ficaram prontos em ' +
      CONFIG.HORAS_MAX_PREPARO + ' h. Faltam: ' + faltam.slice(0, 5).join(', ') + (faltam.length > 5 ? '...' : ''));
    return;
  }
  // tudo pronto: junta as pastas; com Excel, aciona a conversão e espera; senão, entrega
  const pasta = juntarPastas_(pastas, man.pasta);
  if (fmt !== 'csv') {
    if (man.linhas > CONFIG.LIMITES.linhasXlsx) {
      entregar_(aba, linha, col, v, man, [pasta], fmt, {ok: 0, erros: ['o pedido tem ' + man.linhas + ' linhas, acima ' +
        'do limite de ' + CONFIG.LIMITES.linhasXlsx + ' para a conversão automática']});
      return;
    }
    const r = dispararGitHub_('converter_xlsx', {pedido_id: v.ID_Pedido, pasta_id: pasta.getId(), modo: fmt});
    if (r.ok) {
      marcar_(aba, linha, col, {Status: 'convertendo', Detalhe: 'Convertendo para Excel (GitHub)', Conversao_em: new Date()});
    } else {
      marcar_(aba, linha, col, {Detalhe: 'GitHub recusou a conversão (' + r.codigo + '); nova tentativa na próxima volta'});
      avisarResponsavel_('[SAB] GitHub recusou a conversão para Excel', 'Código ' + r.codigo + ': ' + r.texto);
    }
    return;
  }
  entregar_(aba, linha, col, v, man, [pasta], fmt, null);
}

// Compartilha, monta a lista e manda o e-mail de entrega. conv: resultado da conversão para Excel (ou null)
function entregar_(aba, linha, col, v, man, pastas, fmt, conv) {
  const pasta = juntarPastas_(pastas, pastas.filter(function (p) { return p.getId() === man.pasta.getId(); })[0] || pastas[0]);
  const acesso = compartilhar_(pasta, v.email);
  let mb = 0, temCsv = false, temXlsx = false;
  const lista = [], arquivos = [];
  const it = pasta.getFiles();
  while (it.hasNext()) {
    const f = it.next();
    if (/^00_Conversao_/.test(f.getName())) continue;          // controle interno da conversão
    if (acesso === 'link') { try { f.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW); } catch (e) {} }
    mb += f.getSize() / 1e6;
    arquivos.push(f);
    lista.push(f.getName() + ' (' + (f.getSize() / 1e6).toFixed(1) + ' MB)');
    if (/\.xlsx$/.test(f.getName())) temXlsx = true;
    else if (!/^00_/.test(f.getName())) temCsv = true;
  }
  lista.sort();
  const anexo = anexoZip_(arquivos, mb, v.ID_Pedido);
  const validade = Utilities.formatDate(new Date(Date.now() + CONFIG.DIAS_GUARDA * 864e5), FUSO, 'dd/MM/yyyy');
  const notaConv = conv && conv.erros && conv.erros.length ?
    '\n\nATENÇÃO: você pediu o formato Excel, mas ' + (conv.ok ? 'parte dos arquivos não foi convertida (' :
    'a conversão não foi possível (') + conv.erros.slice(0, 3).join('; ') + '). Os CSV estão na pasta; siga as ' +
    'instruções abaixo para abrir no Excel.' : '';
  const enviado = enviarEmail_(v.email, 'Seus dados do SAB estão prontos (' + v.ID_Pedido + ')',
    'Olá, ' + v.nome + '.\n\nOs arquivos do seu pedido ' + v.ID_Pedido + ' estão prontos nesta pasta do Google Drive:\n\n' +
    pasta.getUrl() +
    (acesso === 'pessoa' ? '\n\n(Acesso liberado para o seu e-mail: abra o link com a conta Google ' + v.email + '.)' :
     '\n\nO link abre no navegador e não exige conta Google.') +
    (anexo ? '\n\nOs mesmos arquivos vão anexados a este e-mail (' + anexo.getName() + '): não é preciso abrir o Drive.' : '') +
    '\n\nO link fica disponível até ' + validade + '; depois disso a pasta é apagada. Para baixar tudo de uma vez pelo ' +
    'link, abra a pasta e use "Fazer download" no nome dela.' + notaConv + '\n\n' + v.resumo + '\n\nArquivos (' +
    lista.length + ', ' + mb.toFixed(1) + ' MB no total):\n' + lista.map(function (x) { return '  - ' + x; }).join('\n') +
    '\n\nComo ler: um arquivo por local e por ano; célula vazia = sem dado. As 6 últimas colunas dizem a situação do ' +
    'El Niño / La Niña em cada dia (Fase_ENSO, Intensidade_ENSO, RONI_Trimestre_C e a origem do valor em Fonte_ENSO). ' +
    'O significado de cada coluna está em 00_Dicionario_Variaveis_SAB e o que foi pedido, em 00_Pedido_' + v.ID_Pedido +
    '.csv.' + (temXlsx ? '\n\nOs arquivos .xlsx já trazem os números como números: abra com duplo clique.' : '') +
    (temCsv ? '\n\n' + CONFIG.INSTRUCOES_EXCEL : '') +
    (man.motivo ? '\n\nObservação: ' + man.motivo : '') + '\n\nComo citar: ' + CONFIG.CITACAO + '\n\n' + rodapeEntrega_(),
    anexo ? [anexo] : null);
  if (!enviado) { marcar_(aba, linha, col, {Detalhe: 'Pronto; e-mail na espera (cota diária do Gmail)'}); return; }
  marcar_(aba, linha, col, {Status: 'entregue', Detalhe: lista.length + ' arquivos, ' + mb.toFixed(1) + ' MB' +
                           (temXlsx ? ', com Excel' : '') + (notaConv ? ', conversão incompleta' : '') +
                           (anexo ? ', anexados' : '') +
                           (acesso === 'pessoa' ? ' (acesso só para o e-mail do solicitante)' : ''),
                           Entregue_em: new Date(), Link: pasta.getUrl()});
}

function formatoDoCodigo_(codigo) {
  const m = String(codigo || '').match(/(?:^|;)\s*fmt\s*=\s*(csv|xlsx|ambos)\s*(?:;|$)/i);
  return m ? m[1].toLowerCase() : 'csv';
}

// Entregue: apaga a pasta DIAS_GUARDA dias depois da entrega. Falha: apaga a pasta (deixada para diagnóstico)
// DIAS_GUARDA dias depois do envio. A linha da planilha fica, com o Status expirado ou falha_expirada.
function expirar_(aba, linha, col, v) {
  const desde = v.Status === 'entregue' ? v.Entregue_em : v.Enviado_em;
  if (!desde) return;
  if ((Date.now() - new Date(desde).getTime()) / 864e5 < CONFIG.DIAS_GUARDA) return;
  apagarPastas_(pastasDoPedido_(v.ID_Pedido));
  marcar_(aba, linha, col, v.Status === 'entregue' ?
    {Status: 'expirado', Detalhe: 'Pasta apagada após ' + CONFIG.DIAS_GUARDA + ' dias'} :
    {Status: 'falha_expirada', Detalhe: 'Pasta da falha apagada após ' + CONFIG.DIAS_GUARDA + ' dias. ' + v.Detalhe});
}

// "Qualquer pessoa com o link"; se a conta (ex.: institucional) proibir, libera só para o e-mail de quem pediu
function compartilhar_(pasta, email) {
  try {
    pasta.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    return 'link';
  } catch (erro) {
    pasta.addViewer(email);
    return 'pessoa';
  }
}

function falhar_(aba, linha, col, v, motivo) {
  marcar_(aba, linha, col, {Status: 'falha', Detalhe: motivo});
  enviarEmail_(v.email, 'Pedido de dados SAB com problema (' + v.ID_Pedido + ')',
    'Olá, ' + v.nome + '.\n\nHouve um problema no cálculo do seu pedido ' + v.ID_Pedido + '. O responsável já foi ' +
    'avisado e entrará em contato. Se preferir, tente de novo mais tarde com um período menor.\n\n' + assinatura_());
  enviarEmail_(prop_('EMAIL_RESPONSAVEL'), '[SAB] Falha no pedido ' + v.ID_Pedido,
    'Pedido: ' + v.ID_Pedido + '\nSolicitante: ' + v.nome + ' <' + v.email + '>\nCódigo: ' + v.codigo +
    '\nMotivo: ' + motivo + '\n\nConfira a aba Actions do GitHub e https://code.earthengine.google.com/tasks ' +
    '(tarefas SABPED_' + v.ID_Pedido + '_...). A pasta SAB_pedido_' + v.ID_Pedido + ' ficou no Drive para conferência.\n\n' +
    'Para tentar de novo: na aba Pedidos (ou Pedidos_Teste), apague o ID_Pedido desta linha e mude o Status para na_fila ' +
    '(o pedido ganha um ID novo e volta para a fila).');
}

// ------------------------------------------------------------------ fila e GitHub
function despacharFila_() {
  // [2026.11.04] As duas abas (Pedidos e Pedidos_Teste) dividem a mesma fila: um cálculo por vez, por ordem de chegada
  const itens = [];
  abasRegistro_().forEach(function (reg) {
    const ultima = reg.aba.getLastRow();
    if (ultima < 2) return;
    reg.aba.getRange(2, 1, ultima - 1, reg.aba.getLastColumn()).getValues().forEach(function (r, i) {
      itens.push({reg: reg, linha: i + 2, r: r, status: r[reg.col.Status - 1],
                  quando: new Date(r[reg.col.Recebido_em - 1] || 0).getTime()});
    });
  });
  let ativos = itens.filter(function (x) {
    return x.status === 'enviado' || x.status === 'em_preparo';   // 'convertendo' não usa o Earth Engine
  }).length;
  if (ativos >= CONFIG.MAX_EM_PREPARO) return;
  const fila = itens.filter(function (x) { return x.status === 'na_fila'; })
    .sort(function (a, b) { return a.quando - b.quando; });
  if (!fila.length) return;
  const ocupado = motorOcupado_(false);
  if (ocupado) {
    fila.forEach(function (x) { marcar_(x.reg.aba, x.linha, x.reg.col, {Detalhe: 'Aguardando: ' + ocupado}); });
    return;
  }
  for (let k = 0; k < fila.length && ativos < CONFIG.MAX_EM_PREPARO; k++) {
    const x = fila[k], aba = x.reg.aba, col = x.reg.col;
    let id = x.r[col.ID_Pedido - 1];
    if (!id) {                                  // pedido devolvido à fila pelo responsável: ID novo
      id = gerarId_(x.reg.teste);
      marcar_(aba, x.linha, col, {ID_Pedido: id});
    }
    if (usoDrive_() > CONFIG.USO_MAX_DRIVE) {
      marcar_(aba, x.linha, col, {Detalhe: 'Aguardando espaço no Drive'});
      avisarResponsavel_('[SAB] Drive acima de ' + Math.round(CONFIG.USO_MAX_DRIVE * 100) + '%',
        'Os pedidos estão esperando na fila até liberar espaço no Drive.');
      return;
    }
    const codigo = String(x.r[col.codigo - 1] || '').trim();
    const r = acionarGitHub_(id, codigo, false);
    if (r.ok) {
      marcar_(aba, x.linha, col, {Status: 'enviado', Detalhe: 'Cálculo iniciado', Enviado_em: new Date()});
      ativos++;
    } else {
      marcar_(aba, x.linha, col, {Detalhe: 'GitHub respondeu ' + r.codigo + ' (nova tentativa em 10 min)'});
      avisarResponsavel_('[SAB] GitHub recusou o acionamento',
        'Código ' + r.codigo + ': ' + r.texto + '\n\nRode testarApp() no Apps Script: ele diz se o problema é a chave ' +
        'do GitHub App, a instalação nos repositórios ou a permissão Contents: Read and write. Se for 404, confira ' +
        'GITHUB_REPO.');
      return;
    }
  }
}

// '' = pode despachar; senão, o motivo. Janela de horário OU motor na fila/rodando no GitHub (MOTOR_REPO).
function motorOcupado_(detalhar) {
  const agora = Utilities.formatDate(new Date(), FUSO, 'HH:mm');
  const janela = CONFIG.JANELAS_MOTOR.filter(function (j) { return agora >= j[0] && agora < j[1]; })[0];
  if (janela) return 'horário do motor SAB (' + janela[0] + ' às ' + janela[1] + ')';
  const props = PropertiesService.getScriptProperties();
  const repo = props.getProperty('MOTOR_REPO');
  if (!repo) return '';
  let token = props.getProperty('MOTOR_TOKEN');        // modo antigo: token só de leitura do sab-motor
  if (props.getProperty('GITHUB_APP_ID')) {
    try { token = tokenApp_(false); } catch (erro) { token = ''; if (detalhar) Logger.log('⚠️ ' + erro.message); }
  }
  const estados = ['in_progress', 'queued'];
  for (let k = 0; k < estados.length; k++) {
    const url = 'https://api.github.com/repos/' + repo + '/actions/runs?per_page=1&status=' + estados[k];
    let resp = UrlFetchApp.fetch(url, {muteHttpExceptions: true, headers: token ?
      {Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json'} : {Accept: 'application/vnd.github+json'}});
    if (resp.getResponseCode() !== 200 && token) {       // token vencido ou sem Actions: Read: tenta sem token (público)
      resp = UrlFetchApp.fetch(url, {muteHttpExceptions: true, headers: {Accept: 'application/vnd.github+json'}});
    }
    if (resp.getResponseCode() !== 200) {
      if (detalhar) Logger.log('⚠️ API do GitHub respondeu ' + resp.getResponseCode() + ' para ' + repo + ': ' +
                               resp.getContentText().slice(0, 200));
      return '';                                          // sem resposta: valem só as janelas de horário
    }
    if (Number(JSON.parse(resp.getContentText()).total_count || 0) > 0) {
      return 'motor SAB ' + (estados[k] === 'queued' ? 'na fila' : 'rodando') + ' no GitHub';
    }
  }
  return '';
}

function acionarGitHub_(id, codigo, simular) {
  const dados = {pedido_id: id, codigo: codigo};
  if (simular) dados.simular = '1';
  return dispararGitHub_('pedido_sab', dados);
}

function dispararGitHub_(evento, dados) {
  let token;
  try {
    token = tokenGitHub_();
  } catch (erro) {
    return {ok: false, codigo: 'App', texto: String(erro.message || erro).slice(0, 300)};
  }
  const resp = UrlFetchApp.fetch('https://api.github.com/repos/' + prop_('GITHUB_REPO') + '/dispatches', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    payload: JSON.stringify({event_type: evento, client_payload: dados}),
    headers: {Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json',
              'X-GitHub-Api-Version': '2022-11-28'}
  });
  if (resp.getResponseCode() === 401) CacheService.getScriptCache().remove('SAB_TOKEN_APP');   // token velho: refaz
  return {ok: resp.getResponseCode() === 204, codigo: resp.getResponseCode(), texto: resp.getContentText().slice(0, 300)};
}

// ------------------------------------------------------------------ GitHub App [2026.11.02]
// Token para chamar o GitHub: com o App (GITHUB_APP_ID + GITHUB_APP_CHAVE), um token de instalação que vale 1 hora,
// guardado 50 minutos no cache; sem o App, o token antigo GITHUB_TOKEN.
function tokenGitHub_() {
  return PropertiesService.getScriptProperties().getProperty('GITHUB_APP_ID') ? tokenApp_(false) : prop_('GITHUB_TOKEN');
}

function tokenApp_(detalhes) {
  const cache = CacheService.getScriptCache();
  if (!detalhes) {
    const salvo = cache.get('SAB_TOKEN_APP');
    if (salvo) return salvo;
  }
  const props = PropertiesService.getScriptProperties();
  const cab = {Authorization: 'Bearer ' + jwtApp_(), Accept: 'application/vnd.github+json',
               'X-GitHub-Api-Version': '2022-11-28'};
  let inst = props.getProperty('GITHUB_APP_INSTALACAO');
  if (!inst) {                                   // descobre a instalação pelo repositório dos pedidos (uma vez só)
    const r = UrlFetchApp.fetch('https://api.github.com/repos/' + prop_('GITHUB_REPO') + '/installation',
                                {headers: cab, muteHttpExceptions: true});
    if (r.getResponseCode() === 401) {
      throw new Error('O GitHub recusou a chave do App (401): confira GITHUB_APP_ID (o número "App ID") e se ' +
                      'GITHUB_APP_CHAVE é o arquivo .pem inteiro, do BEGIN ao END.');
    }
    if (r.getResponseCode() !== 200) {
      throw new Error('O GitHub App não está instalado em ' + prop_('GITHUB_REPO') + ' (' + r.getResponseCode() +
                      '): no App, "Install App" > Configure > escolha os repositórios sab-pedidos e sab-motor.');
    }
    inst = String(JSON.parse(r.getContentText()).id);
    props.setProperty('GITHUB_APP_INSTALACAO', inst);
  }
  const r2 = UrlFetchApp.fetch('https://api.github.com/app/installations/' + inst + '/access_tokens',
                               {method: 'post', headers: cab, muteHttpExceptions: true});
  if (r2.getResponseCode() !== 201) {
    if (r2.getResponseCode() === 404) props.deleteProperty('GITHUB_APP_INSTALACAO');   // App reinstalado: acha de novo
    throw new Error('O GitHub não gerou o token do App (' + r2.getResponseCode() + '): ' +
                    r2.getContentText().slice(0, 200));
  }
  const j = JSON.parse(r2.getContentText());
  cache.put('SAB_TOKEN_APP', j.token, 3000);     // 50 minutos (o token vale 60)
  return detalhes ? {token: j.token, instalacao: inst, expira: j.expires_at, permissoes: j.permissions} : j.token;
}

// JWT do App (RS256), válido por 9 minutos, só para pedir o token de instalação
function jwtApp_() {
  const agora = Math.floor(Date.now() / 1000);
  const b64u = function (x) { return Utilities.base64EncodeWebSafe(x).replace(/=+$/, ''); };
  const id = String(prop_('GITHUB_APP_ID')).trim();
  const cabecalho = b64u(JSON.stringify({alg: 'RS256', typ: 'JWT'}));
  const corpo = b64u(JSON.stringify({iat: agora - 60, exp: agora + 540, iss: /^\d+$/.test(id) ? Number(id) : id}));
  const assinatura = Utilities.computeRsaSha256Signature(cabecalho + '.' + corpo, chavePkcs8_(prop_('GITHUB_APP_CHAVE')));
  return cabecalho + '.' + corpo + '.' + b64u(assinatura);
}

// O GitHub entrega a chave em PKCS#1 ("BEGIN RSA PRIVATE KEY"); o Apps Script só assina com PKCS#8 ("BEGIN PRIVATE
// KEY"). Converte embrulhando a chave na estrutura do PKCS#8 (aceita a chave colada com ou sem quebras de linha).
function chavePkcs8_(texto) {
  const t = String(texto || '');
  const b64 = t.replace(/-----[^-]+-----/g, '').replace(/[^A-Za-z0-9+/=]/g, '');
  const pem = function (corpo) {
    return '-----BEGIN PRIVATE KEY-----\n' + corpo.match(/.{1,64}/g).join('\n') + '\n-----END PRIVATE KEY-----\n';
  };
  if (!b64) throw new Error('GITHUB_APP_CHAVE está vazia.');
  if (/BEGIN PRIVATE KEY/.test(t)) return pem(b64);
  if (!/BEGIN RSA PRIVATE KEY/.test(t)) {
    throw new Error('GITHUB_APP_CHAVE não parece a chave privada do App: cole o arquivo .pem inteiro, desde ' +
                    '"-----BEGIN RSA PRIVATE KEY-----" até "-----END RSA PRIVATE KEY-----".');
  }
  const pkcs1 = Utilities.base64Decode(b64).map(function (b) { return b & 255; });
  const tam = function (n) {
    if (n < 128) return [n];
    const bytes = [];
    while (n > 0) { bytes.unshift(n & 255); n = Math.floor(n / 256); }
    return [0x80 | bytes.length].concat(bytes);
  };
  const algoritmo = [0x30, 0x0d, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01, 0x05, 0x00];
  const corpo = [0x02, 0x01, 0x00].concat(algoritmo, [0x04], tam(pkcs1.length), pkcs1);
  const der = [0x30].concat(tam(corpo.length), corpo).map(function (b) { return b > 127 ? b - 256 : b; });
  return pem(Utilities.base64Encode(der));
}

// ------------------------------------------------------------------ Drive
function pastasDoPedido_(id) {
  const it = DriveApp.getFoldersByName('SAB_pedido_' + id);
  const lista = [];
  while (it.hasNext()) {
    const p = it.next();
    if (!p.isTrashed()) lista.push(p);
  }
  return lista;
}

function temArquivo_(pastas, nome) {
  return pastas.some(function (p) { return p.getFilesByName(nome).hasNext(); });
}

function lerManifesto_(pastas, id) {
  for (let i = 0; i < pastas.length; i++) {
    const it = pastas[i].getFilesByName('00_Pedido_' + id + '.csv');
    if (!it.hasNext()) continue;
    const linhas = Utilities.parseCsv(it.next().getBlob().getDataAsString('UTF-8'));
    if (linhas.length < 2) return null;
    const cab = linhas[0];
    const iS = cab.indexOf('Status'), iM = cab.indexOf('Motivo'), iA = cab.indexOf('Arquivo');
    const iL = cab.indexOf('Linhas_Esperadas'), iF = cab.indexOf('Formato');
    const dados = linhas.slice(1);
    return {
      pasta: pastas[i],
      status: dados[0][iS],
      motivo: dados[0][iM] || '',
      linhas: iL === -1 ? 0 : Number(dados[0][iL] || 0),
      formato: iF === -1 ? '' : String(dados[0][iF] || '').toLowerCase(),
      arquivos: dados.map(function (r) { return r[iA]; }).filter(function (a) { return a; })
    };
  }
  return null;
}

// 00_Conversao_<ID>.csv, gravado pelo sab_xlsx.py no fim da conversão: {ok: n, erros: [...]} ou null
function lerMarcador_(pastas, id) {
  for (let i = 0; i < pastas.length; i++) {
    const it = pastas[i].getFilesByName('00_Conversao_' + id + '.csv');
    if (!it.hasNext()) continue;
    const linhas = Utilities.parseCsv(it.next().getBlob().getDataAsString('UTF-8'));
    const cab = linhas[0] || [];
    const iA = cab.indexOf('Arquivo'), iS = cab.indexOf('Status'), iD = cab.indexOf('Detalhe');
    const r = {ok: 0, erros: []};
    linhas.slice(1).forEach(function (l) {
      if (l[iS] === 'ok') r.ok++;
      else r.erros.push(l[iA] + ': ' + l[iD]);
    });
    return r;
  }
  return null;
}

// Move os arquivos das pastas repetidas para a pasta do manifesto e apaga as repetidas
function juntarPastas_(pastas, principal) {
  pastas.forEach(function (p) {
    if (p.getId() === principal.getId()) return;
    const it = p.getFiles();
    while (it.hasNext()) it.next().moveTo(principal);
    apagarPastas_([p]);
  });
  return principal;
}

function apagarPastas_(pastas) {
  (pastas || []).forEach(function (pasta) {
    try {
      Drive.Files.remove(pasta.getId());        // apaga de vez (serviço avançado Drive, ver appsscript.json)
    } catch (erro) {
      pasta.setTrashed(true);                   // sem o serviço avançado: vai para a lixeira (30 dias)
    }
  });
}

function contaDoScript_() {
  try { return Session.getEffectiveUser().getEmail() || '(conta não identificada)'; }
  catch (erro) { return '(conta não identificada)'; }
}

// Diagnóstico: mostra a conta do script e procura no Drive dela as pastas dos pedidos
function diagnosticar() {
  Logger.log('Conta do script (dona da planilha, do Drive pesquisado e dos e-mails): ' + contaDoScript_());
  Logger.log('Drive usado: ' + (usoDrive_() * 100).toFixed(1) + '%');
  const it = DriveApp.searchFolders('title contains "SAB_pedido_"');
  let n = 0;
  while (it.hasNext() && n < 20) {
    const p = it.next();
    const arqs = [];
    const f = p.getFiles();
    while (f.hasNext()) arqs.push(f.next().getName());
    Logger.log('📁 ' + p.getName() + ': ' + arqs.length + ' arquivo(s) ' + arqs.sort().join(', '));
    n++;
  }
  if (!n) Logger.log('❌ Nenhuma pasta SAB_pedido_ no Drive desta conta. As exportações do Earth Engine estão indo ' +
                     'para o Drive de outra conta: refaça o formulário e a planilha na conta do Earth Engine.');
}

function usoDrive_() {
  const limite = DriveApp.getStorageLimit();
  return limite > 0 ? DriveApp.getStorageUsed() / limite : 0;
}

// ------------------------------------------------------------------ pedido escolhido no formulário
// Respostas do formulário -> {codigo, resumo, gerado}. Um pedido que já traz o código (painel) passa direto.
function montarCodigo_(v, agora) {
  const L = CONFIG.LIMITES;
  if (v.codigo) {                                     // veio do painel
    if (v.codigo.indexOf('v=1;') !== 0) {
      throw new Error('O código do pedido não está no formato do painel. Se você não veio do painel, deixe o campo ' +
                      '"Código do pedido" em branco e escolha o local, o período e as variáveis no formulário.');
    }
    if (/(^|;)\s*tipo\s*=\s*BR\s*(;|$)/i.test(v.codigo)) {
      throw new Error('O pedido do Brasil inteiro foi desativado (grande demais para o Earth Engine). Peça por estados, ' +
                      'até ' + L.estados + ' por pedido.');
    }
    return {codigo: v.codigo, resumo: v.resumo || '', gerado: false};
  }
  if (v.origem === CONFIG.ORIGEM.painel) {
    throw new Error('Você marcou que o pedido veio do painel, mas o código do pedido está vazio. Gere o pedido de novo ' +
                    'no painel ou escolha "' + CONFIG.ORIGEM.formulario + '".');
  }
  if (/brasil inteiro/i.test(v.local)) {
    throw new Error('O pedido do Brasil inteiro foi desativado (grande demais para o Earth Engine). Escolha Estados, ' +
                    'até ' + L.estados + ' por pedido.');
  }
  const tipo = Object.keys(CONFIG.LOCAIS).filter(function (k) { return CONFIG.LOCAIS[k] === v.local; })[0];
  if (!tipo) throw new Error('Escolha o local do pedido (estados, municípios, pontos ou área).');
  const res = /mensal/i.test(v.resolucao) ? 'M' : (/di[aá]ria/i.test(v.resolucao) ? 'D' : '');
  if (!res) throw new Error('Escolha a resolução: diária ou mensal.');

  // período
  const hoje = Utilities.formatDate(agora, FUSO, 'yyyy-MM-dd');
  const limite = Utilities.formatDate(new Date(agora.getTime() + L.diasPrevisao * 864e5), FUSO, 'yyyy-MM-dd');
  const ini = dataISO_(v.dataIni, 'inicial');
  let fim = /^sim/i.test(v.previsao) ? limite : dataISO_(v.dataFim, 'final');
  const notas = [];
  if (/^sim/i.test(v.previsao)) notas.push('com a previsão até ' + dataBR_(limite));
  if (ini < '1961-01-01') throw new Error('A data inicial é anterior a 01/01/1961, início do banco SAB.');
  if (fim > limite) { fim = limite; notas.push('data final ajustada para ' + dataBR_(limite) + ', fim da previsão'); }
  if (fim < ini) throw new Error('A data final (' + dataBR_(fim) + ') é anterior à inicial (' + dataBR_(ini) + ').');
  if (ini > hoje) throw new Error('A data inicial (' + dataBR_(ini) + ') é depois de hoje.');

  // variáveis, filtro ENSO e formato
  const mapa = {};
  CONFIG.VARIAVEIS.forEach(function (par) { mapa[par[0]] = par[1]; });
  let cods = separar_(v.variaveis).map(function (x) { return mapa[x]; }).filter(function (x) { return x; });
  if (!cods.length || cods.indexOf('todas') !== -1) cods = ['todas'];
  const nVars = cods[0] === 'todas' ? 'todas as variáveis' : cods.length + ' variável(is)';
  const ensoPar = CONFIG.ENSO.filter(function (par) { return par[0] === String(v.enso || '').trim(); })[0];
  const enso = ensoPar ? ensoPar[1] : '';
  if (v.enso && !ensoPar) throw new Error('Filtro El Niño / La Niña não reconhecido: "' + v.enso + '".');
  if (enso) notas.push('filtro ' + ensoPar[0] + '; a previsão entra sempre');
  const fmtPar = CONFIG.FORMATOS.filter(function (par) { return par[0] === String(v.formato || '').trim(); })[0];
  const fmt = fmtPar ? fmtPar[1] : 'csv';
  if (fmt !== 'csv') notas.push(fmt === 'xlsx' ? 'em Excel (.xlsx)' : 'em CSV e Excel (.xlsx)');

  // local
  let local = '', descricao = '';
  if (tipo === 'E') {
    const est = [];
    separar_(v.estadosSel + ', ' + v.estados).forEach(function (x) {
      const e = estadoCanonico_(x);
      if (!e) throw new Error('Estado não reconhecido: "' + x + '".');
      if (est.indexOf(e) === -1) est.push(e);
    });
    if (!est.length) throw new Error('Marque pelo menos um estado (nas listas por região).');
    if (est.length > L.estados) throw new Error('No máximo ' + L.estados + ' estados por pedido (você marcou ' +
                                                est.length + '). Divida em pedidos menores.');
    local = 'uf=' + est.join(',') + ';sep=1';      // pelo formulário: um arquivo por estado
    descricao = est.length === 1 ? est[0] : est.length + ' estados (' + est.join(', ') + '; um arquivo por estado)';
  } else if (tipo === 'M') {
    const ufs = [], muns = [];
    const juntar = function (nome, uf) {
      nome = String(nome).replace(/[;=|,]/g, ' ').replace(/\s+/g, ' ').trim();
      if (!nome) return;
      if (ufs.indexOf(uf) === -1) ufs.push(uf);
      if (muns.indexOf(nome) === -1) muns.push(nome);
    };
    if (v.estadoMun) {
      const uf = estadoCanonico_(v.estadoMun);
      if (!uf) throw new Error('Estado dos municípios não reconhecido: "' + v.estadoMun + '".');
      separar_(v.munPorEstado[uf] || '').forEach(function (m) { juntar(m, uf); });
    }
    linhas_(v.munOutros + '\n' + v.municipios).forEach(function (l, i) {
      const m = l.match(/^(.+?)\s*(?:[-–\/,;(]\s*|\s+)([A-Za-z]{2})\s*\)?\s*$/);
      if (!m) throw new Error('Município digitado "' + l + '": escreva o nome e a sigla do estado no fim, por exemplo ' +
                              '"Pato Branco - PR".');
      const uf = CONFIG.UF[m[2].toUpperCase()];
      if (!uf) throw new Error('Município digitado "' + l + '": "' + m[2] + '" não é uma UF do Brasil.');
      juntar(m[1], uf);
    });
    if (!muns.length) throw new Error('Marque pelo menos um município na lista do estado.');
    if (muns.length > L.municipios) throw new Error('No máximo ' + L.municipios + ' municípios por pedido.');
    local = 'uf=' + ufs.join(',') + ';mun=' + muns.join(',');
    descricao = muns.length === 1 ? muns[0] + ' (' + ufs[0] + ')' : muns.length + ' municípios (' + muns.join(', ') + ')';
  } else if (tipo === 'C') {
    const linhas = linhas_(v.pontos);
    if (!linhas.length) throw new Error('Escreva pelo menos um ponto, um por linha: "nome; latitude; longitude".');
    if (linhas.length > L.pontos) throw new Error('No máximo ' + L.pontos + ' pontos por pedido.');
    const pts = linhas.map(function (l, i) {
      const c = lerCoordenadas_(l, true, 'ponto ' + (i + 1));
      const nome = (c.nome || ('Ponto ' + (i + 1))).replace(/[;=|,]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 40);
      return c.lat.toFixed(6) + ' ' + c.lon.toFixed(6) + ' ' + nome;
    });
    local = 'pts=' + pts.join('|');
    descricao = pts.length + ' ponto(s)';
  } else {
    const blocos = String(v.vertices).replace(/\r/g, '').split(/\n\s*\n/)
      .map(linhas_).filter(function (b) { return b.length; });
    if (!blocos.length) throw new Error('Escreva os vértices da área, um por linha: "latitude; longitude".');
    if (blocos.length > L.areas) throw new Error('No máximo ' + L.areas + ' áreas por pedido.');
    let total = 0;
    const pols = blocos.map(function (b, k) {
      if (b.length < 4) throw new Error('A área ' + (k + 1) + ' tem ' + b.length + ' vértice(s); são precisos pelo menos 4.');
      total += b.length;
      return b.map(function (l, i) {
        const c = lerCoordenadas_(l, false, 'vértice ' + (i + 1) + ' da área ' + (k + 1));
        return c.lat.toFixed(6) + ' ' + c.lon.toFixed(6);
      }).join(',');
    });
    if (total > L.vertices) throw new Error('No máximo ' + L.vertices + ' vértices por pedido.');
    local = 'pol=' + pols.join('|');
    descricao = pols.length + ' área(s) desenhada(s)';
  }
  const codigo = ['v=1', 'res=' + res, 'tipo=' + tipo].concat(local ? [local] : [])
    .concat(['ini=' + ini, 'fim=' + fim, 'var=' + cods.join(',')]).concat(enso ? ['enso=' + enso] : [])
    .concat(fmt !== 'csv' ? ['fmt=' + fmt] : []).join(';');
  const resumo = descricao + ', ' + (res === 'D' ? 'diário' : 'mensal') + ', ' + dataBR_(ini) + ' a ' + dataBR_(fim) +
    ', ' + nVars + (notas.length ? ' (' + notas.join('; ') + ')' : '');
  return {codigo: codigo, resumo: resumo, gerado: true};
}

// "A, B, C" (caixas marcadas no Forms) -> ['A', 'B', 'C']
function separar_(texto) {
  return String(texto || '').split(', ').map(function (x) { return x.trim(); }).filter(function (x) { return x; });
}

// Nome do estado (com ou sem acento, como no GAUL) -> nome de CONFIG.UF, ou ''
function estadoCanonico_(nome) {
  const alvo = norm_(nome);
  const achado = Object.keys(CONFIG.UF).map(function (k) { return CONFIG.UF[k]; })
    .filter(function (e) { return norm_(e) === alvo; })[0];
  return achado || '';
}

function linhas_(texto) {
  return String(texto || '').replace(/\r/g, '').split('\n').map(function (l) { return l.trim(); })
    .filter(function (l) { return l; });
}

function dataISO_(valor, qual) {
  if (valor && typeof valor.getTime === 'function' && !isNaN(valor.getTime())) {   // data da planilha
    return Utilities.formatDate(valor, FUSO, 'yyyy-MM-dd');
  }
  const t = String(valor || '').trim();
  let m = t.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (m) return m[3] + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[1]).slice(-2);
  m = t.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) return t;
  throw new Error('Informe a data ' + qual + (qual === 'final' ? ' (ou marque "Sim" na previsão).' : '.'));
}

function dataBR_(iso) {
  const p = iso.split('-');
  return p[2] + '/' + p[1] + '/' + p[0];
}

// "nome; latitude; longitude" ou "latitude; longitude" (também separados por tabulação, ou por vírgula quando os
// números usam ponto). Cada coordenada em decimal (-26.2285 ou -26,2285) ou em graus (26°13'42"S, 52 40 16 W).
function lerCoordenadas_(linha, aceitaNome, onde) {
  let partes = linha.split(/\s*[;\t]\s*/).filter(function (x) { return x !== ''; });
  if (partes.length === 1) {
    const m = linha.match(/^(.*?[NS])\s+(.+[WOEL])$/i) || linha.match(/^(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)$/);
    if (m) partes = [m[1], m[2]];
  }
  let nome = '';
  if (aceitaNome && partes.length === 3) nome = partes.shift();
  if (partes.length !== 2) {
    throw new Error('No ' + onde + ' ("' + linha + '"), use ' + (aceitaNome ? '"nome; latitude; longitude"' :
                    '"latitude; longitude"') + ', separados por ponto e vírgula.');
  }
  return {nome: nome, lat: coordenada_(partes[0], 'lat', onde), lon: coordenada_(partes[1], 'lon', onde)};
}

function coordenada_(texto, eixo, onde) {
  const t = String(texto).trim().replace(/[−–]/g, '-').toUpperCase();
  const nums = (t.match(/\d+(?:[.,]\d+)?/g) || []).map(function (x) { return Number(x.replace(',', '.')); });
  const hemi = (t.match(/[NSEWLO]\s*$/) || t.match(/^\s*[NSEWLO]/) || [''])[0].trim();
  const graus = /[°º'"’”]/.test(t) || nums.length > 1 && /\s/.test(t.replace(/^-/, '').trim());
  if (!nums.length || nums.length > 3) throw new Error('No ' + onde + ', a coordenada "' + texto + '" não foi entendida.');
  let valor = graus ? nums[0] + (nums[1] || 0) / 60 + (nums[2] || 0) / 3600 : nums[0];
  if (!graus && nums.length !== 1) throw new Error('No ' + onde + ', a coordenada "' + texto + '" não foi entendida.');
  const negativo = /^-/.test(t) || ['S', 'W', 'O'].indexOf(hemi) !== -1;
  if (!negativo && !hemi && eixo === 'lon') valor = -valor;          // longitude do Brasil é sempre oeste
  if (graus && !hemi && !/^-/.test(t) && eixo === 'lat') {
    throw new Error('No ' + onde + ', indique N ou S na latitude em graus (ex.: 26°13\'42"S).');
  }
  if (negativo) valor = -Math.abs(valor);
  if (eixo === 'lat' && (valor < -34 || valor > 6)) {
    throw new Error('No ' + onde + ', a latitude ' + valor.toFixed(4) + ' fica fora do Brasil (use - ou S para o sul).');
  }
  if (eixo === 'lon' && (valor < -74 || valor > -34)) {
    throw new Error('No ' + onde + ', a longitude ' + valor.toFixed(4) + ' fica fora do Brasil.');
  }
  return valor;
}

// ------------------------------------------------------------------ montar o formulário (rodar uma vez)
// Pré-requisito: o arquivo SAB_municipios_GAUL2015.csv no Drive (workflow "Lista de municípios" do GitHub).
// Pode rodar de novo quando quiser: as perguntas existentes são reaproveitadas pelo título.
// [2026.11.02d] O Apps Script derruba execuções com mais de 6 minutos, e o Forms é lento: a montagem para sozinha
// perto de 4 min 30 s e avisa "rode de novo"; a execução seguinte pula o que já está pronto (listas iguais, perguntas
// já no lugar) e continua. limiteMs só existe para os testes.
function montarFormulario(limiteMs) {
  const t0 = Date.now();
  const LIMITE = typeof limiteMs === 'number' ? limiteMs : 270000;
  const esgotou = function () { return Date.now() - t0 > LIMITE; };
  const pararAqui = function (onde) {
    Logger.log('⏸️ Parte do formulário montada (' + onde + '). Para não passar dos 6 minutos do Apps Script, parei ' +
               'aqui. Rode montarFormulario de novo: ele continua de onde parou.');
  };
  const T = CONFIG.TITULOS;
  const props = PropertiesService.getScriptProperties();
  const url = SpreadsheetApp.getActive().getFormUrl();
  if (!url) throw new Error('Esta planilha não está ligada a um formulário (abra o script pela planilha de respostas).');
  const munPorUF = lerMunicipios_();
  const form = FormApp.openByUrl(url);
  const tipos = FormApp.ItemType;
  // [2026.11.02e] Cada getTitle/getType é uma consulta ao Forms: lê todas UMA vez e procura no índice (antes, cada
  // pergunta procurada relia o formulário inteiro: dezenas de milhares de consultas, e o tempo estourava).
  let existentes = [];
  const indexar = function () {
    existentes = form.getItems().map(function (i) { return {item: i, t: norm_(i.getTitle()), k: i.getType()}; });
  };
  indexar();
  const achar = function (titulo, tipo) {
    const alvo = norm_(titulo);
    const x = existentes.filter(function (e) { return e.t === alvo && e.k === tipo; })[0];
    return x ? x.item : null;
  };
  const obter = function (titulo, tipo, criar, converter) {
    const it = achar(titulo, tipo);
    return (it ? converter(it) : criar()).setTitle(titulo);
  };
  const pagina = function (t) { return obter(t, tipos.PAGE_BREAK, function () { return form.addPageBreakItem(); }, function (i) { return i.asPageBreakItem(); }); };
  const escolha = function (t) { return obter(t, tipos.MULTIPLE_CHOICE, function () { return form.addMultipleChoiceItem(); }, function (i) { return i.asMultipleChoiceItem(); }); };
  const caixas = function (t) { return obter(t, tipos.CHECKBOX, function () { return form.addCheckboxItem(); }, function (i) { return i.asCheckboxItem(); }); };
  const paragrafo = function (t) { return obter(t, tipos.PARAGRAPH_TEXT, function () { return form.addParagraphTextItem(); }, function (i) { return i.asParagraphTextItem(); }); };
  const data = function (t) { return obter(t, tipos.DATE, function () { return form.addDateItem(); }, function (i) { return i.asDateItem(); }); };

  const codigo = achar(T.codigo, tipos.TEXT);
  const resumo = achar(T.resumo, tipos.PARAGRAPH_TEXT);
  if (!codigo) throw new Error('Não achei a pergunta "' + T.codigo + '" (resposta curta) no formulário.');
  codigo.asTextItem().setRequired(false).setHelpText('Preenchido pelo painel SAB. Não altere.');

  // Saem as perguntas das versões anteriores: origem, página "Local do pedido", lista única de estados e
  // municípios digitados. As colunas antigas continuam na planilha, vazias.
  const velhas = existentes.filter(function (e) {
    return (e.t === norm_(T.origem) && e.k === tipos.MULTIPLE_CHOICE) || (e.t === norm_('Local do pedido') && e.k === tipos.PAGE_BREAK) ||
           (e.t === norm_(T.estados) && e.k === tipos.CHECKBOX) || (e.t === norm_(T.municipios) && e.k === tipos.PARAGRAPH_TEXT);
  });
  velhas.forEach(function (e) { form.deleteItem(e.item); });
  if (velhas.length) indexar();       // [2026.11.02b] sem reler, achar() pegava uma pergunta apagada: "Item ausente"

  const pEstados = pagina('Estados');
  const pMunicipios = pagina('Municípios');
  const regioes = Object.keys(CONFIG.REGIOES);
  const ufsOrdem = [];
  regioes.forEach(function (r) { CONFIG.REGIOES[r].forEach(function (e) { ufsOrdem.push(e); }); });
  const pMunUF = ufsOrdem.map(function (e) { return pagina('Municípios: ' + e); });
  const pPontos = pagina('Pontos');
  const pArea = pagina('Área desenhada');
  const pPeriodo = pagina('Período e variáveis');
  const pPainel = pagina('Pedido do painel');
  const pDados = pagina('Seus dados');

  const local = escolha(T.local).setRequired(true).setHelpText('Estados inteiros geram muitas linhas: para períodos ' +
    'longos, prefira a resolução mensal. Até ' + CONFIG.LIMITES.estados + ' estados por pedido.');
  local.setChoices([local.createChoice(CONFIG.LOCAIS.E, pEstados), local.createChoice(CONFIG.LOCAIS.M, pMunicipios),
                    local.createChoice(CONFIG.LOCAIS.C, pPontos), local.createChoice(CONFIG.LOCAIS.P, pArea)]);
  pEstados.setHelpText('Marque os estados nas listas por região (pode misturar regiões), até ' + CONFIG.LIMITES.estados +
    ' estados. Cada estado vem num arquivo próprio.');
  const estRegiao = regioes.map(function (r) {
    return caixas(T.estadosRegiao + r).setRequired(false).setChoiceValues(CONFIG.REGIOES[r]);
  });
  pMunicipios.setHelpText('Escolha o estado e, na página seguinte, marque os municípios na lista (os nomes são os do ' +
    'mapa de limites usado pelo SAB). Até ' + CONFIG.LIMITES.municipios + ' municípios por pedido.');
  const munOutros = paragrafo(T.municipiosOutros).setRequired(false).setHelpText(
    'Só se precisar de municípios de OUTRO estado no mesmo pedido: um por linha, com a sigla do estado. Exemplo:\n' +
    'Chapecó - SC\nCascavel - PR\nOs municípios do estado escolhido abaixo você marca na próxima página.');
  const estadoMun = escolha(T.estadoMun).setRequired(true);
  // [2026.11.02f] Lista única sem o nome das regiões: em ordem alfabética (agrupada por região parecia fora de ordem)
  const alfabetica = ufsOrdem.map(function (e, k) { return [e, k]; })
    .sort(function (a, b) { return a[0].localeCompare(b[0], 'pt'); });
  estadoMun.setChoices(alfabetica.map(function (x) { return estadoMun.createChoice(x[0], pMunUF[x[1]]); }));
  // Listas de municípios: as que já foram gravadas (marca SAB_FORM_LISTAS: tamanho, 1º e último nome) não são regravadas
  const feitas = JSON.parse(props.getProperty('SAB_FORM_LISTAS') || '{}');
  const munUF = [];
  for (let k = 0; k < ufsOrdem.length; k++) {
    if (esgotou()) { pararAqui('listas de municípios até ' + (k ? ufsOrdem[k - 1] : 'o início')); return; }
    const e = ufsOrdem[k];
    const nomes = munPorUF[e] || [];
    if (!nomes.length) throw new Error('A lista ' + CONFIG.ARQUIVO_MUNICIPIOS + ' não tem municípios de ' + e + '.');
    const marca = nomes.length + '|' + nomes[0] + '|' + nomes[nomes.length - 1];
    const existia = achar(T.municipiosUF + e, tipos.CHECKBOX);
    const cx = caixas(T.municipiosUF + e);
    if (!existia || feitas[e] !== marca) {
      pMunUF[k].setHelpText(nomes.length + ' municípios em ordem alfabética. Use Ctrl+F para achar um nome.');
      cx.setRequired(true).setChoiceValues(nomes);
      feitas[e] = marca;
      props.setProperty('SAB_FORM_LISTAS', JSON.stringify(feitas));
    }
    munUF.push(cx);
  }
  const pontos = paragrafo(T.pontos).setRequired(true).setHelpText(
    'Um ponto por linha: "nome; latitude; longitude". Aceita decimal ou graus. Exemplos:\n' +
    'Fazenda A; -26.2285; -52.6712\nSítio B; -26,1500; -52,7000\nÁrea C; 26°13\'42"S; 52°40\'16"W\n' +
    'Cada ponto recebe os dados do pixel de 0,1° (cerca de 11 km) que o contém. Até ' + CONFIG.LIMITES.pontos + ' pontos.');
  const vertices = paragrafo(T.vertices).setRequired(true).setHelpText(
    'Um vértice por linha: "latitude; longitude" (decimal ou graus), pelo menos 4 por área. Para mais de uma área, ' +
    'deixe uma linha em branco entre elas. Exemplo:\n-26.2; -52.7\n-26.2; -52.6\n-26.3; -52.6\n-26.3; -52.7\n' +
    'Até ' + CONFIG.LIMITES.areas + ' áreas e ' + CONFIG.LIMITES.vertices + ' vértices.');
  const dIni = data(T.dataIni).setRequired(true).setHelpText('A partir de 01/01/1961.');
  // [2026.11.02c] Não obrigatória: o Forms não deixa exigir só quando a previsão é "Não" (montarCodigo_ confere)
  const dFim = data(T.dataFim).setRequired(false).setHelpText('Marcou "Sim" na previsão acima? Deixe em branco: a data ' +
    'final vira o último dia da previsão. Marcou "Não"? Preencha a data final.');
  const prev = escolha(T.previsao).setRequired(true)
    .setHelpText('Sim: o arquivo vai da data inicial até o último dia da previsão do tempo calibrada (GFS), 15 dias à ' +
                 'frente, e a data final abaixo fica em branco. Não: preencha a data final abaixo.');
  prev.setChoiceValues(['Não', 'Sim']);
  const enso = escolha(T.enso).setRequired(true).setHelpText(
    'Todo arquivo traz, em cada dia, 6 colunas sobre o El Niño / La Niña: fase, intensidade, índice RONI do trimestre ' +
    '(CPC/NOAA), trimestre e a origem do valor (oficial, estimado ou, nos dias de previsão, persistência do último ' +
    'valor). Com um fenômeno escolhido aqui, o arquivo traz só os meses do passado em que ele ocorreu (episódio de 5 ' +
    'trimestres seguidos, como no painel SAB); os dias de previsão entram sempre.');
  enso.setChoiceValues(CONFIG.ENSO.map(function (p) { return p[0]; }));
  const resol = escolha(T.resolucao).setRequired(true)
    .setHelpText('Mensal: somas (chuva, evapotranspiração) e médias (temperaturas, umidade) de cada mês.');
  resol.setChoiceValues(['Diária', 'Mensal']);
  const formato = escolha(T.formato).setRequired(true).setHelpText(
    'CSV: texto com ponto decimal, abre em qualquer programa (no Excel, siga as instruções que vão no e-mail). ' +
    'Excel (.xlsx): números e datas prontos, abre com duplo clique, até ' + (CONFIG.LIMITES.linhasXlsx / 1e6) +
    ' milhões de linhas por pedido (acima disso vai só o CSV). O conteúdo é o mesmo nos dois.');
  formato.setChoiceValues(CONFIG.FORMATOS.map(function (p) { return p[0]; }));
  const vars = caixas(T.variaveis).setRequired(true)
    .setHelpText('Ponto, data, coordenadas, município, estado e qualidade do pixel vão sempre. Menos variáveis = arquivo menor.');
  vars.setChoiceValues(CONFIG.VARIAVEIS.map(function (p) { return p[0]; }));

  // Navegação: setGoToPage numa quebra de página vale para o FIM da seção anterior a ela
  pMunicipios.setGoToPage(pPeriodo);                       // fim de Estados -> Período
  pMunUF.forEach(function (p, k) {                         // fim de cada estado -> Período
    (k + 1 < pMunUF.length ? pMunUF[k + 1] : pPontos).setGoToPage(pPeriodo);
  });
  pArea.setGoToPage(pPeriodo);                             // fim de Pontos -> Período
  pPeriodo.setGoToPage(FormApp.PageNavigationType.CONTINUE);   // fim de Área -> Período (a seguinte)
  pPainel.setGoToPage(pDados);                             // fim de Período: pula a seção interna do painel
  pPainel.setHelpText('Uso interno. Não aparece para quem preenche o formulário.');
  pDados.setHelpText(CONFIG.AVISO_ENTREGA);

  let ordem = [local, pEstados].concat(estRegiao).concat([pMunicipios, munOutros, estadoMun]);
  pMunUF.forEach(function (p, k) { ordem.push(p, munUF[k]); });
  ordem = ordem.concat([pPontos, pontos, pArea, vertices, pPeriodo, dIni, prev, dFim, enso, resol, formato, vars,
                        pPainel, codigo, resumo, pDados])
    .concat([T.nome, T.email[0], T.instituicao, T.finalidade, T.consentimento].map(function (t) {
      const x = existentes.filter(function (e) { return e.t === norm_(t); })[0];
      return x ? x.item : null;
    })).filter(function (i) { return i; });
  for (let destino = 0; destino < ordem.length; destino++) {
    if (esgotou()) { pararAqui('ordem das perguntas: ' + destino + ' de ' + ordem.length); return; }
    const atual = ordem[destino].getIndex();
    if (atual !== destino) form.moveItem(atual, destino);   // só move o que está fora do lugar
  }
  form.setProgressBar(true);
  form.setDescription('Para quem não usa o painel SAB no Google Earth Engine (quem usa o painel faz o pedido por lá, ' +
    'no botão "Receber por e-mail"). Peça os dados diários ou mensais do SAB, de 1961 até a previsão, para estados, ' +
    'municípios, pontos ou uma área, com ou sem o filtro El Niño / La Niña, em CSV ou Excel. ' + CONFIG.AVISO_ENTREGA +
    ' Limites: até ' + CONFIG.LIMITES.estados + ' estados, 10 milhões de linhas e 3 pedidos por e-mail a cada 24 horas.');
  Logger.log('✅ Formulário montado (' + ufsOrdem.length + ' estados, ' +
             ufsOrdem.reduce(function (s, e) { return s + (munPorUF[e] || []).length; }, 0) + ' municípios): ' +
             form.getPublishedUrl());
}

// SAB_municipios_GAUL2015.csv (Estado, Municipio, nomes do GAUL) -> {nome do estado em CONFIG.UF: [municípios]}
function lerMunicipios_() {
  const it = DriveApp.getFilesByName(CONFIG.ARQUIVO_MUNICIPIOS);
  let arq = null;
  while (it.hasNext()) {
    const f = it.next();
    if (!f.isTrashed() && (!arq || f.getLastUpdated() > arq.getLastUpdated())) arq = f;
  }
  if (!arq) throw new Error('Não achei ' + CONFIG.ARQUIVO_MUNICIPIOS + ' no Drive. No GitHub (sab-pedidos), rode ' +
                            'Actions > Lista de municípios > Run workflow, espere o arquivo chegar na pasta SAB_config ' +
                            'e rode montarFormulario de novo.');
  const linhas = Utilities.parseCsv(arq.getBlob().getDataAsString('UTF-8'));
  const cab = linhas[0].map(norm_);
  const iE = cab.indexOf('estado'), iM = cab.indexOf('municipio');
  const saida = {}, fora = [];
  linhas.slice(1).forEach(function (l) {
    const e = estadoCanonico_(l[iE]);
    const m = String(l[iM] || '').replace(/,/g, ' ').replace(/\s+/g, ' ').trim();
    if (!m) return;
    if (!e) { if (fora.indexOf(l[iE]) === -1) fora.push(l[iE]); return; }
    saida[e] = saida[e] || [];
    if (saida[e].indexOf(m) === -1) saida[e].push(m);
  });
  Object.keys(saida).forEach(function (e) { saida[e].sort(function (a, b) { return a.localeCompare(b, 'pt'); }); });
  if (fora.length) Logger.log('ℹ️ Unidades do GAUL fora dos 27 estados (ignoradas): ' + fora.join(', '));
  return saida;
}

// ------------------------------------------------------------------ planilha
function obterAba_() {
  const abas = SpreadsheetApp.getActive().getSheets();
  const vistos = [];
  for (let i = 0; i < abas.length; i++) {
    if (ehAbaRegistro_(abas[i].getName())) continue;   // [2026.11.04] Pedidos e Pedidos_Teste não são do Forms
    const cab = abas[i].getRange(1, 1, 1, Math.max(1, abas[i].getLastColumn())).getValues()[0];
    if (cab.map(norm_).indexOf(norm_(CONFIG.TITULOS.codigo)) !== -1) return abas[i];
    vistos.push('"' + abas[i].getName() + '": ' + cab.join(' | '));
  }
  throw new Error('Nenhuma aba com a coluna "' + CONFIG.TITULOS.codigo + '". O script deve ser aberto pela planilha ' +
                  'de respostas (Extensões > Apps Script). Linha 1 de cada aba: ' + vistos.join(' || '));
}

// Compara títulos sem diferença de acento, maiúsculas e espaços (o Forms às vezes deixa espaço no fim)
function norm_(t) {
  return String(t || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, ' ').trim().toLowerCase();
}

// Colunas da aba de respostas do Forms (só leitura desde a 2026.11.04: o controle fica nas abas de registro)
function colunas_(aba) {
  const cab = aba.getRange(1, 1, 1, aba.getLastColumn()).getValues()[0];
  const porNome = {};
  cab.forEach(function (c, i) { if (!porNome[norm_(c)]) porNome[norm_(c)] = i + 1; });
  const achar = function (titulo) { return porNome[norm_(titulo)]; };
  const col = {};
  CONFIG.COLUNAS.forEach(function (c) { col[c] = achar(c); });
  const t = CONFIG.TITULOS;
  col.codigo = achar(t.codigo);
  col.resumo = achar(t.resumo);
  col.nome = achar(t.nome);
  col.instituicao = achar(t.instituicao);
  col.finalidade = achar(t.finalidade);
  col.consentimento = achar(t.consentimento);
  ['origem', 'local', 'estados', 'estadoMun', 'municipios', 'municipiosOutros', 'pontos', 'vertices', 'dataIni',
   'dataFim', 'previsao', 'resolucao', 'variaveis', 'enso', 'formato'].forEach(function (k) { col[k] = achar(t[k]); });
  col.estadosRegiao = Object.keys(CONFIG.REGIOES).map(function (r) { return achar(t.estadosRegiao + r); })
    .filter(function (x) { return x; });
  col.munUF = {};
  Object.keys(CONFIG.UF).forEach(function (k) {
    const e = CONFIG.UF[k], c = achar(t.municipiosUF + e);
    if (c) col.munUF[e] = c;
  });
  col.email = t.email.map(achar).filter(function (x) { return x; })[0];
  if (!col.codigo || !col.email || !col.nome) {
    throw new Error('A planilha precisa das perguntas "' + t.codigo + '", "' + t.nome + '" e de uma pergunta de e-mail ' +
                    '(' + t.email.join(' / ') + '). Títulos encontrados: ' + cab.join(' | '));
  }
  return col;
}

function lerLinha_(aba, linha, col) {
  return objeto_(aba.getRange(linha, 1, 1, aba.getLastColumn()).getValues()[0], col);
}

function objeto_(r, col) {
  const g = function (c) { return c ? r[c - 1] : ''; };
  const munPorEstado = {};
  Object.keys(col.munUF || {}).forEach(function (e) { munPorEstado[e] = String(g(col.munUF[e]) || ''); });
  return {
    carimbo: col.Recebido_em ? r[col.Recebido_em - 1] : r[0], codigo: String(g(col.codigo)).trim(), resumo: String(g(col.resumo) || '').trim(),
    nome: String(g(col.nome)).trim(), email: String(g(col.email)).trim().toLowerCase(),
    ID_Pedido: g(col.ID_Pedido), Status: g(col.Status), Detalhe: String(g(col.Detalhe) || ''),
    Enviado_em: g(col.Enviado_em), Entregue_em: g(col.Entregue_em), Conversao_em: g(col.Conversao_em),
    origem: String(g(col.origem) || '').trim(), local: String(g(col.local) || '').trim(),
    estados: String(g(col.estados) || ''),
    estadosSel: (col.estadosRegiao || []).map(function (c) { return String(g(c) || ''); })
      .filter(function (x) { return x; }).join(', '),
    estadoMun: String(g(col.estadoMun) || '').trim(), munPorEstado: munPorEstado,
    municipios: String(g(col.municipios) || ''), munOutros: String(g(col.municipiosOutros) || ''),
    pontos: String(g(col.pontos) || ''), vertices: String(g(col.vertices) || ''),
    dataIni: g(col.dataIni), dataFim: g(col.dataFim), previsao: String(g(col.previsao) || ''),
    resolucao: String(g(col.resolucao) || ''), variaveis: String(g(col.variaveis) || ''),
    enso: String(g(col.enso) || '').trim(), formato: String(g(col.formato) || '').trim()
  };
}

function marcar_(aba, linha, col, valores) {
  Object.keys(valores).forEach(function (k) { aba.getRange(linha, col[k]).setValue(valores[k]); });
}

// email = null: [2026.11.15] conta os pedidos REGISTRADOS (com ID) de TODOS os e-mails, inclusive os recusados (teto
// geral). Linhas ainda sem ID (gravadas com o sistema ocupado) não contam: senão uma leva delas se barraria toda.
function pedidosRecentes_(aba, col, email, linhaAtual) {
  const ultima = aba.getLastRow();
  if (ultima < 2) return 0;
  const dados = aba.getRange(2, 1, ultima - 1, aba.getLastColumn()).getValues();
  const desde = Date.now() - 864e5;
  return dados.filter(function (r, i) {
    if (i + 2 === linhaAtual || !(new Date(r[col.Recebido_em - 1]).getTime() >= desde)) return false;
    if (email === null) return !!r[col.ID_Pedido - 1];
    return String(r[col.email - 1]).trim().toLowerCase() === email && r[col.Status - 1] !== 'recusado';
  }).length;
}

// [2026.11.15] Avisa o responsável UMA vez por dia que o teto geral foi atingido (mais avisos gastariam a cota do Gmail)
function avisarLimiteGeral_() {
  const props = PropertiesService.getScriptProperties();
  const hoje = Utilities.formatDate(new Date(), FUSO, 'yyyy-MM-dd');
  if (props.getProperty('SAB_AVISO_LIMITE_GERAL') === hoje) return;
  props.setProperty('SAB_AVISO_LIMITE_GERAL', hoje);
  avisarResponsavel_('[SAB] Limite diário geral de pedidos atingido',
    'Chegaram ' + CONFIG.MAX_PEDIDOS_DIA + ' pedidos nas últimas 24 horas (CONFIG.MAX_PEDIDOS_DIA). Os seguintes estão ' +
    'sendo recusados sem e-mail ao solicitante (Status recusado, Detalhe "Limite diário geral de pedidos" na aba ' +
    'Pedidos). Se for uso legítimo, aumente CONFIG.MAX_PEDIDOS_DIA; se não, confira a aba Pedidos.');
}

// ID sequencial: SAB2026-00001, SAB2026-00002... O contador fica nas propriedades do script (SAB_CONTADOR).
// Não usa trava própria: quem chama (aoEnviarFormulario, doGet, verificarPedidos e registrarPendentes_) já está com a trava do script,
// e soltar uma trava aqui dentro soltaria a deles (o LockService tem uma trava só por script).
function gerarId_(teste) {
  const props = PropertiesService.getScriptProperties();
  const chave = teste ? 'SAB_CONTADOR_TESTE' : 'SAB_CONTADOR_PEDIDOS';   // [2026.11.04] SAB-0001 / TESTE-0001
  const n = parseInt(props.getProperty(chave) || '0', 10) + 1;
  props.setProperty(chave, String(n));
  return (teste ? CONFIG.PREFIXO_TESTE : CONFIG.PREFIXO_ID) + (n < 10000 ? ('000' + n).slice(-4) : String(n));
}

// ------------------------------------------------------------------ [2026.11.04] abas de registro dos pedidos
function ehAbaRegistro_(nome) {
  return nome === CONFIG.ABA_PEDIDOS || nome === CONFIG.ABA_TESTE;
}

// As duas abas de registro (criadas na primeira vez), cada uma com as suas colunas: [{aba, col, teste}]
function abasRegistro_() {
  const planilha = SpreadsheetApp.getActive();
  return [[CONFIG.ABA_PEDIDOS, false], [CONFIG.ABA_TESTE, true]].map(function (par) {
    let aba = planilha.getSheetByName(par[0]);
    if (!aba) {
      aba = planilha.insertSheet(par[0]);
      aba.getRange(1, 1, 1, CONFIG.CABECALHO.length).setValues([CONFIG.CABECALHO]).setFontWeight('bold');
      aba.setFrozenRows(1);
      ['Recebido_em', 'Enviado_em', 'Entregue_em', 'Conversao_em'].forEach(function (c) {
        aba.getRange(2, CONFIG.CABECALHO.indexOf(c) + 1, 999, 1).setNumberFormat('dd/MM/yyyy HH:mm:ss');
      });
    }
    return {aba: aba, col: colunasRegistro_(aba), teste: par[1]};
  });
}

function colunasRegistro_(aba) {
  let cab = aba.getRange(1, 1, 1, Math.max(1, aba.getLastColumn())).getValues()[0];
  CONFIG.CABECALHO.forEach(function (c) {          // coluna apagada à mão: volta no fim
    if (cab.map(norm_).indexOf(norm_(c)) === -1) {
      aba.getRange(1, cab.filter(function (x) { return x !== ''; }).length + 1).setValue(c);
      cab = aba.getRange(1, 1, 1, aba.getLastColumn()).getValues()[0];
    }
  });
  const pos = function (titulo) { return cab.map(norm_).indexOf(norm_(titulo)) + 1; };
  const col = {};
  CONFIG.COLUNAS.forEach(function (c) { col[c] = pos(c); });
  col.Recebido_em = pos('Recebido_em');
  col.Origem = pos('Origem');
  col.Resposta_formulario = pos('Resposta_formulario');
  col.codigo = pos('Código do pedido');
  col.resumo = pos('Resumo do pedido');
  col.nome = pos('Nome completo');
  col.email = pos('E-mail');
  col.instituicao = pos('Instituição');
  col.finalidade = pos('Finalidade do uso dos dados');
  col.consentimento = pos('Consentimento');
  return col;
}

// Pedidos feitos com o e-mail do responsável (ou com um dos EMAILS_TESTE) vão para Pedidos_Teste
function ehTeste_(email) {
  const props = PropertiesService.getScriptProperties();
  // [2026.11.04a] EMAIL_RESPONSAVEL também pode ter mais de um e-mail, separados por vírgula
  const lista = String(props.getProperty('EMAIL_RESPONSAVEL') || '').split(',').concat(String(props.getProperty('EMAILS_TESTE') || '').split(','))
    .map(function (x) { return x.trim().toLowerCase(); }).filter(function (x) { return x; });
  return lista.indexOf(String(email || '').trim().toLowerCase()) !== -1;
}

function registroDoEmail_(regs, email) {
  return regs.filter(function (r) { return r.teste === ehTeste_(email); })[0];
}

// Acrescenta o pedido no fim da aba (ordem de chegada) e devolve o número da linha
function anexarPedido_(reg, d) {
  const linha = new Array(Math.max(reg.aba.getLastColumn(), CONFIG.CABECALHO.length)).fill('');
  const por = function (k, valor) { if (reg.col[k]) linha[reg.col[k] - 1] = valor; };
  por('Recebido_em', d.recebido || new Date());
  por('Origem', d.origem || '');
  por('nome', d.nome || '');
  por('email', String(d.email || '').trim().toLowerCase());
  por('instituicao', d.inst || '');
  por('finalidade', d.fin || '');
  por('consentimento', d.consent || '');
  por('codigo', d.codigo || '');
  por('resumo', d.resumo || '');
  por('Detalhe', d.detalhe || '');
  por('Resposta_formulario', d.ref || '');
  reg.aba.appendRow(linha);
  return reg.aba.getLastRow();
}

// Identificador de uma resposta do formulário (carimbo + e-mail): impede que ela vire dois pedidos
function refResposta_(carimbo, email) {
  const d = carimbo instanceof Date ? carimbo : new Date(carimbo);
  return (isNaN(d.getTime()) ? String(carimbo) : Utilities.formatDate(d, FUSO, 'yyyy-MM-dd HH:mm:ss')) + ' ' +
         String(email || '').trim().toLowerCase();
}

function linhaPorRef_(reg, ref) {
  const ultima = reg.aba.getLastRow();
  if (ultima < 2 || !reg.col.Resposta_formulario) return 0;
  const refs = reg.aba.getRange(2, reg.col.Resposta_formulario, ultima - 1, 1).getValues();
  for (let i = 0; i < refs.length; i++) if (String(refs[i][0]) === ref) return i + 2;
  return 0;
}

// Respostas anteriores a este instante (as do sistema antigo) nunca viram pedido de novo
function inicioRegistro_() {
  const v = PropertiesService.getScriptProperties().getProperty('SAB_INICIO_REGISTRO');
  return v ? new Date(v).getTime() : Date.now();
}

// ------------------------------------------------------------------ [2026.11.04] zerar os pedidos
// Apaga as linhas 2 em diante. A planilha não deixa apagar todas as linhas abaixo do cabeçalho congelado: sobra uma
// linha em branco no fim.
function apagarLinhas_(aba) {
  const ultima = aba.getLastRow();
  if (ultima < 2) return;
  if (aba.getMaxRows() <= ultima) aba.insertRowsAfter(ultima, 1);
  aba.deleteRows(2, ultima - 1);
}

// Rodar à mão (Executar > zerarPedidos). Apaga TODOS os pedidos das abas Pedidos e Pedidos_Teste, as respostas do
// formulário (na planilha e no próprio Forms), as colunas de controle antigas da aba do Forms e todas as pastas
// SAB_pedido_ do Drive, e a numeração volta a SAB-0001 e TESTE-0001. Não roda com um pedido em cálculo.
function zerarPedidos() {
  const trava = LockService.getScriptLock();
  if (!trava.tryLock(30000)) throw new Error('O sistema está ocupado (verificarPedidos rodando). Tente de novo em 1 minuto.');
  try {
    const regs = abasRegistro_();
    const abaForm = obterAba_();
    const andamento = ['enviado', 'em_preparo', 'convertendo'];
    const ocupados = [];
    regs.forEach(function (reg) {
      const ultima = reg.aba.getLastRow();
      if (ultima < 2) return;
      reg.aba.getRange(2, 1, ultima - 1, reg.aba.getLastColumn()).getValues().forEach(function (r) {
        if (andamento.indexOf(r[reg.col.Status - 1]) !== -1) ocupados.push(r[reg.col.ID_Pedido - 1]);
      });
    });
    const cabForm = abaForm.getRange(1, 1, 1, abaForm.getLastColumn()).getValues()[0];
    const iStatus = cabForm.map(norm_).indexOf(norm_('Status'));
    if (iStatus !== -1 && abaForm.getLastRow() > 1) {
      abaForm.getRange(2, 1, abaForm.getLastRow() - 1, abaForm.getLastColumn()).getValues().forEach(function (r) {
        if (andamento.indexOf(r[iStatus]) !== -1) ocupados.push(r[cabForm.map(norm_).indexOf(norm_('ID_Pedido'))]);
      });
    }
    if (ocupados.length) {
      throw new Error('Há pedido em cálculo (' + ocupados.join(', ') + '). Espere a entrega e rode zerarPedidos() de novo.');
    }
    let n = 0;
    regs.forEach(function (reg) {
      const ultima = reg.aba.getLastRow();
      if (ultima > 1) { n += ultima - 1; apagarLinhas_(reg.aba); }
    });
    const nForm = Math.max(0, abaForm.getLastRow() - 1);
    if (nForm) apagarLinhas_(abaForm);
    for (let c = cabForm.length; c >= 1; c--) {          // colunas de controle que o sistema antigo criava no Forms
      if (CONFIG.COLUNAS.map(norm_).indexOf(norm_(cabForm[c - 1])) !== -1) abaForm.deleteColumn(c);
    }
    let respostasForms = 'sem formulário ligado';
    const url = SpreadsheetApp.getActive().getFormUrl();
    if (url) {
      const form = FormApp.openByUrl(url);
      respostasForms = form.getResponses().length + ' apagada(s) no Forms';
      form.deleteAllResponses();
    }
    const pastas = [];
    const it = DriveApp.searchFolders('title contains "SAB_pedido_"');
    while (it.hasNext()) {
      const p = it.next();
      if (p.getName().indexOf('SAB_pedido_') === 0 && !p.isTrashed()) pastas.push(p);
    }
    apagarPastas_(pastas);
    const props = PropertiesService.getScriptProperties();
    ['SAB_CONTADOR', 'SAB_CONTADOR_PEDIDOS', 'SAB_CONTADOR_TESTE', 'SAB_LIMPEZA'].forEach(function (k) { props.deleteProperty(k); });
    props.setProperty('SAB_INICIO_REGISTRO', new Date().toISOString());
    Logger.log('✅ Pedidos zerados: ' + n + ' linha(s) de pedido, ' + nForm + ' resposta(s) da planilha (' + respostasForms +
               ') e ' + pastas.length + ' pasta(s) SAB_pedido_ apagadas. O próximo pedido será SAB-0001 (teste: TESTE-0001).');
  } finally {
    trava.releaseLock();
  }
}

// ------------------------------------------------------------------ e-mail
function enviarEmail_(para, assunto, corpo, anexos) {
  if (MailApp.getRemainingDailyQuota() < 1) return false;
  // [2026.11.04a] a resposta vai para o PRIMEIRO e-mail do responsável (uma lista no replyTo derrubaria o envio)
  const msg = {to: para, subject: assunto, body: corpo, name: CONFIG.NOME,
               replyTo: String(prop_('EMAIL_RESPONSAVEL')).split(',')[0].trim()};
  if (anexos && anexos.length) msg.attachments = anexos;
  MailApp.sendEmail(msg);
  return true;
}

// Zip com todos os arquivos do pedido, quando couber no e-mail (o Gmail aceita até 25 MB de anexos)
function anexoZip_(arquivos, mbCsv, id) {
  if (!arquivos.length || mbCsv > CONFIG.ANEXO_MAX_CSV_MB) return null;
  try {
    const zip = Utilities.zip(arquivos.map(function (f) { return f.getBlob(); }), 'SAB_' + id + '.zip');
    return zip.getBytes().length <= CONFIG.ANEXO_MAX_ZIP_MB * 1e6 ? zip : null;
  } catch (erro) {
    Logger.log('Anexo não montado para ' + id + ': ' + erro);
    return null;
  }
}

function avisarResponsavel_(assunto, corpo) {
  const props = PropertiesService.getScriptProperties();
  const chave = 'AVISO_' + assunto;
  const ultimo = Number(props.getProperty(chave) || 0);
  if (Date.now() - ultimo < 6 * 3.6e6) return;   // no máximo um aviso igual a cada 6 horas
  props.setProperty(chave, String(Date.now()));
  enviarEmail_(prop_('EMAIL_RESPONSAVEL'), assunto, corpo);
}

function assinatura_() {
  return '--\n' + CONFIG.NOME + '\nResponda a este e-mail para falar com o responsável.\n' +
         'Seus dados (nome, e-mail e instituição) são usados só para atender este pedido e para estatísticas de uso ' +
         'do banco, e não são compartilhados (LGPD, Lei 13.709/2018).';
}

// Fim do e-mail de entrega: opinião, apoio (PIX) e a assinatura de sempre
function rodapeEntrega_() {
  return CONFIG.FEEDBACK + '\n\n' + CONFIG.PIX + '\n\n' + assinatura_();
}

function prop_(nome) {
  const v = PropertiesService.getScriptProperties().getProperty(nome);
  if (!v) throw new Error('Falta a propriedade do script ' + nome + '.');
  return v;
}
