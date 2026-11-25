# Envio dos dados por e-mail: histórico

| Data | Peça | Versão | O que mudou |
|---|---|---|---|
| 18/11/2026 | K16 v6 (resultado) | — | **APROVADA** às 22h13: A1-A6, B1, B2 (só a chuva, 5.475 linhas idênticas ao painel), dicionário e E1. Parte C: 3 variáveis a 75% e 54% do tempo de 19 (limite 70%): o limite do link na hora não muda. Libera o painel 2026.11.4. |
| 18/11/2026 | `sab_pedido.py`, testes | 2026.11.18 | Pedido de uma variável só saía com a coluna vazia: com uma banda só, o `reduceRegions` grava a média como `mean` e o `formatar()` procurava o nome da banda. `_redutor_media()` dá o nome da banda (`setOutputs`). Testado no Earth Engine (`testes/verificar_uma_variavel_ee.py`): 19 de 19 variáveis, diário e mensal, iguais ao pedido "todas". Pedidos de 2 ou mais variáveis não mudam (K16 igual). PR #2. |
| 18/11/2026 | `sab_pedido.py` | 2026.11.19 | Dicionário: aviso de que escoamento superficial e chuva efetiva de 1961-2025 não batem dia a dia com a chuva (auditoria K26; `pesquisa/ESCOAMENTO.md`). Nenhum valor muda. PR #3. |
| 18/11/2026 | `pesquisa/`, workflows | — | Pesquisa da previsão estendida e piloto de temperatura (dias 3 e 17), PR #4; K26 v1.9/v1.10 e testes do escoamento, PRs #5 e #6. Nada disso muda os pedidos. |
| 15/11/2026 | `requirements.txt`, workflows | 2026.11.15 | Versões fixas das bibliotecas e actions no Node 24 (PR #1 do `sab-pedidos`; registrado aqui em 18/11). |
| 08/11/2026 | `Codigo.gs` | 2026.11.08a | Pedido em sequência: antes cada etapa (arquivos prontos → conversão para Excel → e-mail → próximo da fila) só andava na volta seguinte de 10 em 10 min (até ~20 min a mais com Excel). Agora, com pedido calculando ou convertendo, `verificarPedidos` se reagenda para 1 min depois (acionador de uma vez só `verificarRapido`, um por vez); entrega e despacho do próximo na mesma volta; 5 min se a etapa passar de 45 min ou o dia passar de 600 voltas rápidas (cota de 90 min/dia); pedido gravado com o sistema ocupado marca `SAB_PENDENTE` e entra em 1 a 2 min. Acionador de 10 min fica de segurança. `teste_codigo_gs.js`: 126 conferências. |
| 08/11/2026 | `Codigo.gs` | 2026.11.08 | Motor uma vez por dia, às 23h07: janela única 22h50–01h00 (folga para o atraso do GitHub). Substitui a 2026.11.04a (no ar) e a 2026.11.05 (nunca implantada). `teste_codigo_gs.js`: janela da noite, folga até 01h00, manhã e tarde livres (112 conferências). |
| 08/11/2026 | K21 / K22 / 09 | K21 v4 / K22 v2 / 09 (texto) | Resultado da K21 v3a (16h33, 26 min): U UR ✅, U vento ❌ (viés +0,107 m/s, limite 0,10), R ✅, C ✅, E ✅, G ✅. K21 v4: avalia a V1.6 revista (vento pela média) com as mesmas regras, pontos e semente; U só a UR; o EQM do vento vira o item V (informação); E com o vento da V1.5; G vira informação; janela única 22h50–01h00, duração estimada 90 min. K22 v2: item 3 exige só a UR na faixa (vento informação) e o item 1 confere o método gravado (`UR eqm; vento media`). 09a/09b: só comentários (conta e matriz E1 iguais). |
| 29/10/2026 | `sab_pedido.py`, `pedido_sab.yml`, `Codigo.gs`, K16 | 2026.10.29a | Primeira versão: formulário → Apps Script → GitHub → Earth Engine → Drive → e-mail. |
| 30/10/2026 | `Codigo.gs` | 2026.10.30a | Títulos comparados sem acento/espaço; erro mostra as abas. |
| 30/10/2026 | `Codigo.gs` | 2026.10.30b | `diagnosticar`; coluna Detalhe mostra a espera e os erros. |
| 30/10/2026 | `Codigo.gs` / `sab_pedido.py` | 2026.10.30c / 30a | O Earth Engine criou duas pastas com o mesmo nome (exportações simultâneas): o script junta as pastas; a rotina espera o manifesto antes das outras exportações. Compartilhamento: se o link público for bloqueado (conta institucional), libera para o e-mail de quem pediu. |
| 30/10/2026 | `Codigo.gs` / `sab_pedido.py` | 2026.10.30d / 30b | Formulário completo (`montarFormulario`): Brasil inteiro, estados, municípios ("Município - UF", sem ligar para acento, com sugestões), pontos (decimal ou graus) e áreas; datas, previsão, resolução e variáveis. Rotina: tipos BR e C, estados separados (`sep=1`), 400 arquivos e 200 pontos por pedido. |
| 30/10/2026 | `Codigo.gs` / painel | 2026.10.30e / 2026.10.5 | App da Web (`doGet`): o painel registra o pedido direto, sem o formulário. Formulário: código e resumo numa seção que só quem vem do painel vê. Painel: variáveis do arquivo e escolha entre link na hora e e-mail. |
| 03/11/2026 | K17 (validação final dos dados) | K17 | Nova auditoria mestre, só leitura (trava em `ee.data` e `Task.start`). Embute sem mudança V1.0 (O0), V1.3 (O1), V1.5 (05b), O2 e O4 (SHA no log) e confere: P1 inventário, P2 histórico = V1.0 recalculada, P3 diferenças V1.0 × V1.3 × V1.5 por classe, P4 matrizes = O2/O4, P5 provisórios = V1.5, P6 coerência física, P7 × CHIRPS, P8 RONI × CPC, P9 máscara. Testes offline `teste_k17.py` (carga segura, rotas, decisões, trava e orquestração). |
| 03/11/2026 | K17 | K17 v2 | A v1 parou no P2 com "User memory limit exceeded" (5 versões do dia numa consulta de 1.000 pixels). Pixels sorteados uma vez e guardados no Colab; cada versão amostrada sozinha, em lotes de 500 que caem pela metade (até 50) se o servidor recusar por memória ou tempo, e o tamanho que funcionou é lembrado; um dia que falhar não derruba o P2. Cálculos e regra de decisão sem mudança. Nova fumaça `fumaca_k17.py` (servidor falso que recusa lotes acima de 250). |
| 03/11/2026 | K17 | K17 v3 | Resultado da v2: P1, P5, P6, P8 ✅; P2 ⚠️ (só 2020-01-15 e 2025-12-31, só ET real, transpiração e escoamento, que vêm direto do ERA5-Land); P4 sem memória; P9 ❌. P9: erro da K17 (comparava a máscara inteira com a conta da K1d, só centro no Brasil); agora receita do 01b x propriedades `n_classe_*` gravadas no asset. P4: coleções do código original capturadas (mean/reduce) e lidas como tabela por pixel, 40 pixels A, Matriz_Clima_01 e Matriz_Solo_07. P2: lê a data de atualização no catálogo (ERA5-Land, BR-DWGD) e a da gravação do dia; diferença explicada só se a fonte foi revista depois da gravação (regra acrescentada depois de ver o resultado da v2, dito ao responsável). Amostra estratificada por classe; P3 compara a correção de leitura com o gravado. Corrigido erro de precedência em `avaliar_mascara` achado pelo teste. |
| 03/11/2026 | K17 | K17 v4 | Rodada da v3 (11h44): P1, P5, P6, P8, P9 ✅; P2 e P4 ⚠️. A regra da v3 que dava P2 ✅ pela data `updateTime` do catálogo foi **retirada**: todas as imagens do ERA5-Land tinham a mesma data, a da própria execução, então ela não prova revisão. No lugar, `assinatura_p2` (só diagnóstico, não muda o status): 1961 a 2013 idênticos; 2020 e 2025 diferem só nas variáveis acumuladas do ERA5-Land. P4: BR-DWGD e ERA5 instantâneo exatos; diferem só acumuladas do ERA5 e o SMAP. Histórico gravado entre 24/08 e 26/09/2026 (não em lote em 13/09). |
| 03/11/2026 | K18 | K18 | Nova auditoria só leitura antes de decidir correções: Q1 (início da revisão do ERA5-Land: ET real e transpiração refeitas como a V1.0 nos pixels A, um dia por mês 2014–2025, com controle de fidelidade em 1961–2013 e na temperatura do solo) e Q2 (gravado × BR-DWGD nos pixels B, jan e jul de 1961 a 2025; controle nos A). Teste `teste_k18.py`. Recomendação registrada: não regravar o histórico; corrigir os pixels B na leitura depois da K18. |
| 03/11/2026 | K18 (resultado) | — | Rodada 17h55, controles 100%. Q1: revisão do ERA5-Land de jul/2017 (intermitente) e contínua desde out/2018; ~0,011 mm/dia de ET real nos pixels mudados, viés ~0: não corrigir. Q2: nos pixels B, núcleo térmico ≈ BR-DWGD; chuva com 4,8 mm/dia de diferença diária (viés +6%) e ETo 0,76 mm/dia: correção na leitura recomendada. |
| 03/11/2026 | K19 | K19 | Auditoria profunda numa célula (só leitura, 1h30 a 3h): D2 QC de todos os dias por ano e classe; D3 extremos anuais isolados; D4 ETo gravada × FAO-56 do motor e VPD; D5 emenda 2025→2026 (ERA5 bruto × correção na média × EQM, treino 2014–2023, teste 2024–2025); D6 homogeneidade relativa por estado (Pettitt, SNHT por permutação; × ERA5-Land e × CHIRPS) e costura de 2026; D1 reprodução das 16 bandas (1 dia/ano + 10 dias de 2026, Brasil inteiro, por classe). Termina com a lista de candidatas a correção. Recusa começar perto da janela do motor; zip parcial a cada parte. `teste_k19.py` (estatística com casos conhecidos, carga dos motores e execução completa simulada). |
| 03/11/2026 | K19 | K19 v2 | A v1 recebeu 429 no D2 (3 anos por pedido = pedidos simultâneos demais). Cota mensal conferida pelo responsável: nível Partner (360.000.000 EECU-s/mês), 0,05% usado. v2: um ano por pedido no D2 e no D6; 429 espera 1, 2 e 3 min. |
| 03/11/2026 | K19 | K19 v3 | D5 passa a medir também UR, radiação e vento (no motor V1.5 também corrigidos só na média em 2026: UR aditiva; radiação e vento multiplicativos, teto 5); D3 inclui a ETo máxima anual isolada. Cobertura por variável: D1 e D2 as 16; D5 as 6 do núcleo calibradas pelo ERA5; D6 as 7 com referência independente. |
| 03/11/2026 | K19 | K19 v4 / K19b | Rodada da v3 (19h29): D2, D3, D4, D6 completas; D5 e D1 sem memória (getRegion de um ano inteiro; V1.0 no Brasil inteiro por dia). v4: D5 mês a mês (divide os pontos se pesado); D1 nos pixels sorteados (A 200, B 100, C todos, borda 50), uma imagem por vez em lotes. K19b = as mesmas partes D5 e D1 sozinhas. |
| 03/11/2026 | K19 | v4.1 | Rodada da K19b (20h21): D5 e D1 completas. D1 dava ❌ em 2026 por regra da K19: em 2026 a chuva, a ETo e a radiação dos pixels A também vêm do ERA5; agora entram na assinatura do ERA5 acumulado. Resultado: 1961–2018 idênticos nas 16 bandas e 4 classes; 2019–2025 e jan–set/2026 só variáveis acumuladas do ERA5 (revisão da fonte); out/2026 idêntico. D5: chuva sem ganho com EQM; UR e vento com ganho (erro diário −22% e −33%). |
| 03/11/2026 | Guia e índice | — | Decisão final registrada (validado com ressalvas; histórico não regravado). Guia: "Validação final", "Quando o BR-DWGD passar a cobrir 2026", "Quando repetir as auditorias" e "Correções planejadas". Índice: plano de correções e ressalvas na seção 10. |
| 04/11/2026 | K21 / 09a-09b | K21 v3 / 09 v3 | A v2 também estourou a memória, mesmo com 2 pontos: o servidor não faz o percentil de 930 imagens num pedido interativo. K21 v3: o treino lê os dias de 1986–2015 por getRegion (um mês por pedido, como a D5 da K19b) e calcula os quantis em Python. 09 v3: a amostra de conferência também vem dos dias (getRegion) com quantis em Python; o 09b continua calculando a matriz no servidor, em lote (blocos de 32 px), e compara o gravado com os quantis do NumPy com tolerância (UR 2%, vento 0,2 m/s, chuva 0,5 mm). |
| 04/11/2026 | K21 / 09a-09b | K21 v2 / 09 v2 | A K21 v1 parou no treino com "User memory limit exceeded" (percentis de 930 imagens, 150 pontos e as duas fontes num pedido só). v2: ERA5 e BR-DWGD em pedidos separados, tileScale 16 e divisão dos pontos ao meio se o servidor recusar; no 09, a mesma amostra e a exportação em blocos de 32 px (shardSize). Contas e regras sem mudança. |
| 04/11/2026 | `Codigo.gs` / K19 | 2026.11.05 | Janelas do motor V1.6 (rodadas às 06h07 e 15h07): 05h50–08h30 e 14h50–16h30; a da noite sai. A K19 recusa começar também perto da janela da manhã. Substitui a 2026.11.04 e a 2026.11.04a. |
| 04/11/2026 | `Codigo.gs` | 2026.11.04a | `EMAIL_RESPONSAVEL` aceita mais de um e-mail separado por vírgula: todos contam como teste (aba Pedidos_Teste) e recebem os avisos; o *responder* dos e-mails vai só para o primeiro (uma lista no replyTo derrubaria o envio de todos os e-mails). |
| 04/11/2026 | `Codigo.gs` | 2026.11.04 | Registro dos pedidos em abas próprias: **Pedidos** (usuários, ID `SAB-0001`) e **Pedidos_Teste** (e-mail do responsável e `EMAILS_TESTE`, ID `TESTE-0001`, sem limite diário), uma linha por pedido em ordem de chegada, ID na 1ª coluna. A aba do Forms não é mais alterada (o Forms inseria respostas no meio das linhas do painel). Fila única para as duas abas, por ordem de chegada. `zerarPedidos()` apaga pedidos, respostas (planilha e Forms), colunas de controle antigas e pastas `SAB_pedido_`, e zera os contadores. Janelas do motor 14h50–16h30 e 22h50–00h30. `teste_codigo_gs.js`: 106 conferências. |
| 04/11/2026 | painel / K16 / K19 | 2026.11.3 / K16 v5 / K19 | Etapa 1 implantada (painel no app `adao-alves-rodrigues-junior-sab`, script `SAB_painel_2026_10_6`; pedido SAB2026-00020, CSV + Excel, 17 min). Painel 2026.11.2 (autoria e link oficial) e 2026.11.3 (envio por e-mail num clique: um quadro "Clique aqui para ENVIAR O PEDIDO" aparece quando os campos estão completos; mesmo endereço do pedido). K16 v5 embute a 2026.11.3. Janelas do motor na K19: 14h50–16h30 e 22h50–00h30 (o GitHub atrasa o motor ~40 min). |
| 03/11/2026 | `sab_pedido.py` / painel / K16 / K20 | 2026.11.03 / 2026.11.1 / K16 v4 / K20 | Etapa 1: correção de leitura dos pixels B (núcleo do BR-DWGD, dias de 1961 a 2025) e da radiação dos pixels C (≤ céu claro, FAO-56), igual no painel e na rotina (`corrigir_pixels_b`, `area_tem_pixels_bc`). K16 v4: caso A6 (Lagoa dos Patos, jan–mar/2024) e pastas do Drive com a versão. K20: validação só leitura da correção. Testes: `teste_k20.py`, `teste_correcao_b_identica.py`. |
| 03/11/2026 | K20 | K20 v2 | Rodada da v1 (22h24): V1, V2, V4 e V6 ✅ (1.800 pixel-dias B = BR-DWGD; A intocado); V3 e V5 sem dados porque o sampleRegions descartava o ponto quando faltava o BR-DWGD (pixels C e dias de 2026). v2: bandas amostradas com marcador de vazio (`unmask(AUSENTE)`), que volta a vazio no Colab. |

Pendências: K16 (identidade com o painel), troca da credencial do Earth Engine antes de abrir ao público,
token do GitHub com validade, conta institucional (@alunos.utfpr.edu.br) pode ser desativada após a formatura.

| Data | Peça | Versão | O que mudou |
|---|---|---|---|
| 30/10/2026 | `sab_pedido.py` / `Codigo.gs` / painel / K16 | 2026.10.30c / 30f / 2026.10.5 | Filtro ENSO no envio por e-mail: mesma série do painel (RONI do CPC + estimativa OISST), mesma regra de episódio, mesmos nomes de arquivo e 5 colunas. Formulário só para quem não usa o painel (sem a pergunta de origem), com o filtro El Niño / La Niña e o aviso de entrega pelo Google Drive. E-mail: zip anexado quando os CSV somam até 40 MB e o zip até 20 MB. Painel: caixa "Receber por e-mail" em qualquer busca, inclusive com o filtro ENSO. K16: caso A5 (ENSO). |
| 31/10/2026 | (versões do usuário) | 2026.10.31_Oficial / 2026.11.01_Segura | Brasil inteiro bloqueado à mão depois do estouro de memória do pedido P20261031213150mffz; testes do GitHub desligados; spam, Excel, PIX e IDs sequenciais no Apps Script. Auditadas e incorporadas abaixo (com as correções listadas). |
| 01/11/2026 | `sab_pedido.py` / `sab_xlsx.py` / `listar_municipios.py` / workflows / `Codigo.gs` / painel / K16 v2 / `colab_credencial.py` v3 / motor no GitHub | 2026.11.01 / 2026.10.6 | Ver abaixo. |

## 2026.11.01 (01/11/2026)

**Auditoria das versões coladas pelo usuário (31/10 e 01/11) antes de mudar:**
- `sab_pedido.py` (2026.10.31_Oficial): o bloqueio do Brasil inteiro estava certo, mas (1) o pedido de 27 estados
  marcados um a um continuava possível (o mesmo estouro); (2) o erro de memória do Earth Engine virava "falha" em vez de
  uma recusa explicada; (3) colunas ENSO sempre com `enso=True`, mas os dias de previsão ficavam "Previsao (sem
  classificacao)" e os meses recentes sem RONI ("Sem_Dado"), por isso "não completava"; (4) a K16 passava a montar nomes
  com "_" sobrando (sufixo vazio), o que reprovaria a identidade.
- `pedido_sab.yml`: testes desligados (procuravam o tipo BR). Religados, com os testes atualizados.
- `Codigo.gs` (2026.11.01_Segura): `SEM_DESPACHO_ENTRE: [0, 0]` desligou a proteção do horário do 05b; `gerarId_` soltava
  a trava do script dentro de outra função que já estava com ela (o LockService tem uma trava só por script): duas
  respostas ao mesmo tempo podiam furar a fila. As duas coisas foram corrigidas.

**Rotina dos pedidos (`sab_pedido.py` 2026.11.01):**
- Brasil inteiro (`tipo=BR`) recusado com explicação; no máximo 6 estados por pedido.
- **Estimativa do tamanho antes do Earth Engine** (área dos estados, polígonos e pontos x dias ou meses): acima de 1,5 x o
  limite de 10 milhões de linhas, recusa na hora. Erro de memória ou de tempo do Earth Engine vira recusa explicada.
- **Colunas ENSO sempre** (6: as 5 do painel + `Fonte_ENSO`), com ou sem filtro. Meses com o trimestre do OISST ainda
  incompleto: `Estimativa_OISST_parcial` (2 de 3 meses). Mês atual e dias de previsão: `Persistencia` do último valor.
  Só CPC e Estimativa_OISST entram nos filtros (como no painel). Sem filtro, uma falha da série RONI não derruba o pedido.
- `fmt=csv|xlsx|ambos` aceito e gravado no manifesto (coluna `Formato`).
- Dicionário: textos ENSO e do formato dos números (UTF-8, vírgula, "Não detectar tipos de dados", localidade
  Inglês (Estados Unidos)) e a linha nova `Fonte_ENSO`.

**Conversão para Excel (`sab_xlsx.py` + `converter_xlsx.yml`, novos):** baixa cada CSV do Drive, grava o .xlsx com números
como números (casas do painel), datas como datas, cabeçalho congelado, filtro e aba "Sobre"; sobe para a mesma pasta e
grava `00_Conversao_<ID>.csv`. Formato `xlsx`: o CSV de dados é apagado depois da conversão; `ambos`: ficam os dois.
Medido aqui: 200 mil linhas x 40 colunas em 28 s (1 milhão de linhas ~ 2,5 min).

**Lista de municípios (`listar_municipios.py` + `municipios.yml`, novos):** grava `SAB_municipios_GAUL2015.csv` na pasta
SAB_config do Drive, com os nomes exatos do GAUL que a rotina procura.

**Apps Script (`Codigo.gs` 2026.11.01):**
- Fila: não despacha nas janelas do motor (14h50–16h e 22h50–24h) nem com o motor na fila ou rodando no GitHub
  (API, propriedade `MOTOR_REPO`); `testarMotor()` mostra o estado.
- Excel: CSV prontos → aciona `converter_xlsx` (status `convertendo`, que não ocupa a vaga do Earth Engine) → entrega com
  os .xlsx; sem resposta em 6 h ou acima de 3 milhões de linhas, entrega o CSV com aviso.
- Formulário: estados em 5 listas por região; municípios escolhidos numa lista por estado (27 páginas, nomes do GAUL),
  com um campo opcional para municípios de outro estado; pergunta "Formato dos arquivos"; Brasil inteiro removido.
- E-mails: aviso de spam (confirmação e formulário); na entrega, instruções do Excel quando vai CSV, explicação das
  colunas ENSO, pedido de opinião e o PIX (46) 99907-5852 com o aviso das limitações do serviço gratuito.
- IDs sequenciais `SAB2026-00001` (sem a trava interna). Pastas de falha apagadas 7 dias depois (`falha_expirada`) e,
  uma vez por dia, pastas `SAB_pedido_` órfãs com mais de 7 dias.

**Painel 2026.10.6:** caixa do e-mail com o formato (CSV, Excel ou os dois), aviso de spam e limite de 6 estados.

**K16 v2:** colunas do painel idênticas + só as ENSO a mais; dicionário com a lista de linhas mudadas de propósito;
caso novo E1 (colunas ENSO dos dias recentes e da previsão, sem Sem_Dado).

**Motor no GitHub (repositório novo `sab-motor`, público):** `rodar_motor.py` confere o SHA-256 do 05b aprovado e as travas
(PROTEGER_HISTORICO, 2025-12-31, SIMULAR), espera os pedidos em andamento (até 45 min) e roda o 05b sem mudança, às
15h07 e 23h07 (cron 18:07 e 02:07 UTC). Concorrência 1. Registro mensal `ATIVIDADE.md` mantém o agendamento ligado.

**Credencial v3:** confere Earth Engine e Google Drive; a mesma linha vai para o segredo dos dois repositórios.

**Testes:** `teste_sab_pedido.py` (todos), `fumaca_sab_pedido.py` (16 casos), `teste_sab_xlsx.py`, `teste_rodar_motor.py`,
`teste_codigo_gs.js`, `teste_formulario_gs.js`, `teste_06_pedido_email.js/.py`, `teste_k16.py`, `fumaca_k16.py`
(aprovação e reprovação): todos passam.

## 2026.11.02 (02/11/2026): GitHub App no lugar dos tokens

`Codigo.gs` 2026.11.02: o acesso ao GitHub passa a ser por um GitHub App (propriedades `GITHUB_APP_ID` e
`GITHUB_APP_CHAVE`). O script assina um JWT (RS256) com a chave do App, descobre a instalação sozinho
(`GITHUB_APP_INSTALACAO`) e pede um token de instalação que vale 1 hora, guardado 50 minutos no cache. Serve para os
pedidos (`sab-pedidos`, Contents: Read and write) e para ver se o motor está rodando (`sab-motor`, Actions:
Read-only). Sem troca anual de token. A chave do GitHub (PKCS#1) é convertida para PKCS#8, o único formato que o Apps
Script assina; aceita a chave colada com ou sem quebras de linha. Função nova `testarApp()`. Os tokens antigos
(`GITHUB_TOKEN`, `MOTOR_TOKEN`) continuam aceitos se o App não estiver configurado. Teste com chave RSA real gerada no
formato do GitHub: assinatura conferida com a chave pública, token reaproveitado do cache, erros explicados.
- 2026.11.02b: `montarFormulario` relê as perguntas depois de apagar as antigas (antes dava "Item ausente" no
  formulário do usuário, que tinha a lista única de estados e os municípios digitados). O teste agora simula o Forms
  recusando a leitura de pergunta apagada.
- 2026.11.02c: no formulário, "Data final" deixa de ser obrigatória (com a previsão "Sim" ela fica em branco; o Forms
  barrava o envio) e vem depois da pergunta da previsão; sem previsão e sem data final, a recusa explica o que fazer.
- 2026.11.02d: `montarFormulario` em partes. O Apps Script derruba execuções de mais de 6 minutos, e as 27 listas de
  municípios (até 853 nomes) com a reordenação passavam disso. Agora para perto de 4 min 30 s com o aviso "rode de
  novo" e, na execução seguinte, pula as listas iguais e as perguntas já no lugar.
- 2026.11.02e: `montarFormulario` rápido. Cada pergunta procurada relia o título de todas as perguntas do formulário
  (cada leitura é uma consulta ao Forms; ~25 mil consultas): em 4 min 30 s montava só 9 estados. Agora lê os títulos
  uma vez e guarda quais listas de municípios já foram gravadas (propriedade SAB_FORM_LISTAS). O teste conta as
  leituras: 170 para 85 perguntas.
- 2026.11.02f: a pergunta "Estado dos municípios" em ordem alfabética (agrupada por região, sem o nome das regiões,
  parecia fora de ordem). As listas de estados continuam por região.
- 2026.11.03: "Tempo limite do bloqueio" no App da Web (linha 291). O script tem uma trava só; o doGet esperava 30 s
  por ela e caía quando o verificarPedidos (a cada 10 min, lendo o Drive) estava com ela, e o pedido se perdia. Agora o
  doGet e o aoEnviarFormulario usam tryLock: sem a trava, a linha é gravada sem ID (Detalhe "Aguardando registro") e o
  verificarPedidos a registra em até 10 minutos (registrarPendentes_, só linhas das últimas 24 h). O doGet também não
  grava de novo o mesmo pedido (mesmo e-mail e código, ainda em andamento, nas últimas 2 h): página recarregada ou link
  clicado duas vezes. Teste: 10 verificações novas em teste_codigo_gs.js.
- Painel 2026.10.7 (02/11/2026): só os textos do bloco El Niño / La Niña (ver `CHANGELOG_06.md`). O passo U17 do guia
  agora cria um script novo `SAB_painel_2026_10_7` no Code Editor em vez de editar o `SABTESTE1` (que fica de cópia).
- K16 v3 (03/11/2026): parte P. Os CSV do painel não precisam mais ser baixados à mão: a K16 roda o próprio painel
  2026.10.7 (embutido sem mudança, SHA-256 no LOG) no Node.js do Colab, com o Earth Engine de verdade
  (@google/earthengine). Só a tela é simulada (k16_painel_node.js): preenche cada caso, clica em PROCESSAR e baixa os
  mesmos links getDownloadURL do botão de download para MeuDrive/K16_painel/<caso>/. CSV já postos à mão são mantidos.
  Testes: testes/teste_k16_painel_node.js (painel inteiro com Earth Engine simulado) e testes/fumaca_k16_parte_p.py
  (Python -> Node -> arquivos no Drive). A v2 rodada em 03/11 01:00 não conferiu A1-A5/B1 por falta desses CSV.
