# CHANGELOG_06: Painel SAB 2026.10.4 (20/10/2026)

> **Revisão posterior (20/10/2026, tarde):** as auditorias independentes A e B pediram correções neste escopo. Elas estão em `CHANGELOG_REVISAO_AB.md`, que prevalece em caso de divergência.

- **Arquivo:** `/home/claude/sab/v4/06_painel_sab_2026_10_4.js` (renomeado com `mv` a partir de `06_painel_sab_2026_10_3a.js`; 2.782 linhas).
- **Base:** `/home/claude/sab/v3_zip/06_painel_sab_2026_10_3a.js`.
- **Diff:** 46 linhas removidas e 257 incluídas. Todas estão marcadas com `// [V4 <ID>]` ou ficam dentro de um bloco marcado. O resto está byte a byte igual, inclusive os espaços no fim de linha.
- **Teste offline:** `/home/claude/sab/v4/testes/teste_06_enso.js` (Node). O teste foi escrito em JS e não em Python, como pedia a tarefa, para extrair e executar o código do próprio painel.

## Validação feita

| Checagem | Resultado |
|---|---|
| `node --check` | OK |
| `acorn` com `ecmaVersion: 5` | OK. O teste negativo com `let` e arrow function é rejeitado, como esperado. |
| Referências não declaradas (`eslint-scope`, globais `ee`, `ui`, `print`, `Export`) | Nenhuma no arquivo inteiro |
| `teste_06_enso.js` | 52 de 52 verificações OK |
| Tabela de Clopper–Pearson | Conferida contra o cálculo exato pela binomial (no teste) e pelo `scipy.stats.beta`: todas as 22 bordas batem com arredondamento de 0,1 |
| Diff completo contra a v3 | Relido linha a linha. Nenhuma linha muda só por espaço em branco. |

O checador ES5 está em `/tmp/claude-0/-home-claude/22d161fd-7b68-5ad7-86d3-02156273abdf/scratchpad/acorn/checar_es5.js`.

Não foi possível rodar o Earth Engine. Cada chamada nova foi conferida contra o padrão que o próprio painel já usa e contra o tipo do objeto (cliente ou servidor). As exceções estão marcadas como A CONFIRMAR.

---

## Itens

### [V4 F1/M06-01] GAUL só do Brasil
- **Linhas:** 230-234.
- **O que mudou:** `estados` e `municipios` recebem `.filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))`.
- **Por quê:** a J3 confirmou nos dados os homônimos Amazonas (Colômbia, Peru e Venezuela, 19 municípios cada), Distrito Federal (México, 16) e "Para" (Suriname, 5). `formatarTextoBusca` tira os acentos, então "Pará" casa com "Para". O motor já filtra assim (05a:159).
- **Outros pontos conferidos:** todos partem das duas coleções filtradas, então nenhum filtro extra foi necessário.
  - lista de municípios do passo 3 (linha 927);
  - contorno no modo Coordenadas (`estados.filterBounds`, 1237);
  - contorno e polígonos de estados (1247, 1270);
  - municípios (1255);
  - `centerObject(APP.regiaoGeom)` (2602), que vem de `poligonos_fc`.
  - O `centerObject(fc)` da linha 873 centraliza o rascunho desenhado pelo usuário, não o GAUL.
- **Como verificar:**
  - Norte > Amazonas, marcar municípios: a lista não deve ter "Leticia" nem municípios venezuelanos ou peruanos.
  - Pará: a lista não deve ter distritos do Suriname.
  - Centro-Oeste > Distrito Federal: o mapa não deve centralizar no México.

### [V4 F2/M06-03] Fim do corte silencioso em 25.000
- **Linhas:**
  - 74: `CFG.limitePontosGrade = 25000`;
  - 1342-1345: `toList(CFG.limitePontosGrade)`;
  - 1380: `n_pares: gridComNomes.size()` no retorno de `construirRegiaoSelecionada`;
  - 2638-2650: avaliação inicial.
- **O que mudou:**
  - A avaliação inicial passou de `regiao_fc.size().evaluate(function(n, err)` para `ee.Dictionary({n, nPares}).evaluate(function(contagem, err)`.
  - Acima do limite, aparece `mostrarAlertaTela` ("ÁREA GRANDE DEMAIS… reduza a área"), o processamento é cancelado por `registrarErroProcessamento` e o Console recebe o número de pares.
  - Abaixo do limite, o Console registra "Grade de extração: N pares pixel × polígono".
  - O formato do `ID_Ponto` (`Ponto_%05d`, sequencial após a ordenação) não mudou.
- **Por quê:** Amazonas (cerca de 15.600 pixels) mais Pará (cerca de 12.500) passam de 25.000. A ordenação é município + lat + lon, então os pixels do fim da lista sumiam do CSV sem aviso.
- **Como verificar:**
  - Norte > Amazonas + Pará deve dar o alerta, com o número de pares.
  - Curitiba deve dar a linha "Grade de extração" no Console, e o CSV continua igual.

### [V4 Q1] Máscara de qualidade
- **Linhas:**
  - 104-106: `CFG.assets.mascaraQualidade`;
  - 149-151: `APP.mascaraQualidadeOk = null`;
  - 1289-1302: grade;
  - 1322: `Classe_Q`;
  - 1352 e 1360-1363: `Qualidade_Pixel`;
  - 1384-1400: `verificarMascaraQualidade()`;
  - 2548-2552: espera no botão PROCESSAR;
  - 2780-2781: chamada única ao abrir o painel;
  - 2300-2311: colunas;
  - dicionário em 2370-2373.
- **O que mudou:**
  - **Verificação assíncrona, uma vez só:** `ee.Image(asset).bandNames().evaluate(cb)`, o mesmo padrão `evaluate` com callback do resto do painel. A verificação confere também a banda `classe`. O resultado fica em `APP.mascaraQualidadeOk`: `null` (verificando), `true` ou `false`.
  - **Se o asset faltar:**
    - o Console recebe `logWarn` e a tela recebe `mostrarAlertaTela`, ambos com "Máscara de qualidade ausente: rode a etapa 1";
    - a grade não é filtrada;
    - `Qualidade_Pixel` sai vazia;
    - nenhum objeto `ee` aponta para o asset, então nada quebra.
  - **Se o usuário clicar em PROCESSAR antes de a verificação terminar:** aparece um alerta pedindo para esperar alguns segundos.
  - **Na grade, antes da amostragem:**
    - `pixelLonLat().addBands(classe.unmask(0, false).rename('classe_q')).updateMask(classe_q.neq(4))`;
    - o `sample(... dropNulls: true)`, que já existia, descarta a classe 4 antes do join com os polígonos;
    - a classe (0 = sem classe) segue como `Classe_Q` até o ponto e vira `Qualidade_Pixel` ('A', 'B', 'C' ou vazio).
  - **CSV diário:** a coluna `Qualidade_Pixel` fica logo depois de `Longitude`.
- **Por quê:** é a decisão 3 do usuário e o contrato do SPEC (máscara Q1). A J1 conta cerca de 880 pixels "C fora", com o centro fora do Brasil.
- **Como verificar:**
  1. Antes da etapa 1, abrir o painel: deve aparecer o alerta e o aviso no Console, e Curitiba deve processar normalmente com `Qualidade_Pixel` vazia.
  2. Depois da etapa 1, o Console deve mostrar "Máscara de qualidade encontrada".
  3. Num estado de borda (RS, AC ou RR), o número de pares no Console deve cair em relação à execução sem máscara, e no CSV devem aparecer as classes A, B e C.
  4. Em Curitiba, os mesmos pontos e o mesmo `N_Ponto` de antes, com Qualidade_Pixel = A.
- **A CONFIRMAR:** `unmask(0, false)`. O segundo argumento (`sameFootprint = false`) não é usado em outro ponto do painel. Ele existe para que o pixel fora do footprint do asset fique 0 e continue na grade, como hoje. Se não funcionar como esperado, o efeito se limita a pixels fora da grade do BR-DWGD (por exemplo, a oeste de −73,9° no Acre), que já saem vazios no CSV. Conferir comparando os pares de um estado de borda com e sem máscara: a diferença deve ser igual ao número de pixels de classe 4 na área.

### [V4 F4/M06-04] CSV mensal: N_Dias, Dias_no_Mes e Mes_Completo
- **Linhas:** 2494-2500, 2510-2512, 2516-2517, 2313-2318 (colunas), dicionário 2367-2369.
- **O que mudou:**
  - `Dias_no_Mes` = `dEnd.advance(-1,'day').get('day')`, um inteiro, como o `get('year').format('%04d')` que o painel já usa.
  - `Mes_Completo` = 'sim' se `ic_mes.size()` == `Dias_no_Mes`, senão 'nao'.
  - `N_Dias` = `n_imgs`.
  - As três colunas ficam depois de `Versao_Algoritmo`.
- **Por quê:** meses parciais (início e fim do período, filtro ENSO, previsão) apareciam como total do mês, e o 07 só aceita mês completo.
- **Como verificar:** um mensal de 15/01 a 20/03 deve dar jan com N_Dias = 17, Dias_no_Mes = 31, Mes_Completo = nao; fev com 28/28/sim; mar com 20/31/nao.
- **Observação:** um dia `falha_latencia_gfs` é uma imagem e conta em N_Dias, mesmo com a chuva mascarada.

### [V4 F8/M06-05] CSV diário: Janela_Chuva_UTC
- **Linhas:** 2432-2434 e 2444; colunas em 2304-2311; dicionário em 2365 e 2375.
- **O que mudou:**
  - `versao` 'definitiva', ou ausente (o histórico), dá '12-12 UTC (D-1 a D)'. Os demais valores dão '00-24 UTC'.
  - A coluna fica depois de `Versao_Algoritmo`. É só um rótulo: os valores não mudam.
- **Por quê:** C7. O BR-DWGD acumula de 12 a 12 UTC e o ERA5/GFS no dia civil em UTC; o CSV misturava as duas janelas sem avisar.
- **Como verificar:** o CSV de Curitiba em 2025 deve trazer '12-12 UTC (D-1 a D)', e os dias de 2026 ERA5/GFS devem trazer '00-24 UTC'.

### [V4 Conf] CSV diário: Confianca_Prazo
- **Linhas:** 2435-2437 e 2445; dicionário em 2366.
- **O que mudou:** a coluna recebe a propriedade `Confianca_Prazo` da imagem quando ela existe, e fica vazia quando não existe. Fica depois de `Janela_Chuva_UTC`.
- **Por quê:** é o contrato do motor V1.5. O rascunho do 05a V1.5 grava `'Confianca_Prazo'` com 'alta', 'media' ou 'baixa'.
- **Como verificar:** os dias V1.3 e V1.4 saem vazios. Depois do motor V1.5, os dias GFS saem 'alta', 'media' ou 'baixa', conforme o prazo.

### [V4 F6/M06-06] Fim da série ENSO: 'Indefinida'
- **Linhas:**
  - 1698-1709: regra dentro do map de `indiceONI_FC`;
  - 1731-1735: `filtroCenario`;
  - 1805-1806 e 1853-1854: Console no Simular;
  - 2006-2019: Console no filtro histórico.
- **O que mudou:**
  - **Regra:** se o sinal do mês não é nulo, se nAteFim = n − i ≤ 4 e se a soma dos sinais de i até o fim é igual a sinal × nAteFim, o mês é 'Indefinida'. A soma usa o mesmo padrão de `checkWindow` (`ee.List.sequence(...).map(get).reduce(sum)`) dentro de um `If` que só calcula a soma nas 4 últimas posições. A regra só vale quando o mês não é El Niño nem La Niña. Para usar só os métodos que o painel já usa, `abs().eq(1)` substitui `neq(0)`.
  - **Filtro:** todo cenário ganha `ee.Filter.inList('FaseENSO', ['El Nino','La Nina','Neutro'])`. Isso exclui 'Indefinida' e 'Sem_Dado' de forma explícita; antes já ficavam de fora só por construção.
  - **Console:**
    - o Simular imprime a lista de estações 'Indefinida';
    - o filtro histórico registra "Filtro ENSO (cenário): X mês(es) com fase Indefinida e Y Sem_Dado ficaram fora do filtro", com as listas.
- **Por quê:** mai a ago/2026 (0,5 / 1,0 / 1,4 / 1,7) saíam 'Neutro', e "Anos Neutros" incluía meses em pleno aquecimento.
- **Teste offline** (réplica fiel, com a tabela `noaa_data` lida do 02):
  - 920 estações, a última JAS 2026 = 1,7;
  - mai, jun, jul e ago/2026 = Indefinida; abr/2026 (0,0) continua Neutro; exatamente 4 Indefinida na série;
  - V3 × V4: só essas 4 estações mudam, todas de Neutro para Indefinida;
  - fora delas, as janelas do painel são iguais a `fases_episodio` do 02, sem nenhuma divergência;
  - **1972-73 sem mudança:** El Niño Forte = set, out e dez/1972 e jan/1973, tanto na V3 quanto na V4; nov/1972 (2,0) fica em Super;
  - "Anos Neutros" passa de 429 para 425 estações, e nenhum cenário contém Indefinida.
- **Cenários hipotéticos** (estimativa OISST acrescentada no fim):
  - ASO = 2,0: mai a set viram El Nino;
  - ASO = 0,3: mai a ago ficam Neutro, porque a sequência fecha com 4;
  - ASO = −0,6: set fica Indefinida;
  - 4 estações negativas no fim ficam Indefinida; 5 viram La Nina.
- **Como verificar no Code Editor:**
  - o Simular deve imprimir "RONI: estações com fase Indefinida no fim da série: 4" com `2026_05` a `2026_08`;
  - o 6.5 do roteiro (1972-73) deve dar o mesmo resultado, com "0 mês(es) com fase Indefinida e 0 Sem_Dado".
- **Observação:** o motor preditivo usa só o RONI, não a fase, então os análogos e as probabilidades do roteiro 6.4 não mudam.

### [V4 M06-15] Continuidade do RONI como true/false
- **Linhas:** 1801-1804 (chaves novas no dicionário de `executarMotorPreditivo`), 1826 e 1849-1862.
- **O que mudou:**
  - O dicionário devolve `mesesEsperados`, `nSerie` e `nChavesDistintas` (`aggregate_array('chave_join').distinct().size()`).
  - A comparação é feita no cliente, dentro do `evaluate` que já existia: `serieContinua = nSerie === mesesEsperados && nChavesDistintas === nSerie`, e `print('RONI: série mensal contínua?', serieContinua)` mostra `true` ou `false`.
  - Se der false, o status mostra "❌ A série do RONI tem lacuna ou repetição…", o `logError` registra o problema, não aparece nenhuma probabilidade e o botão de exportar fica oculto.
  - A contagem de chaves distintas pega a lacuna compensada por repetição, que a comparação antiga (só tamanho × esperado) deixava passar.
  - Usei a comparação no cliente em vez de `ee.Algorithms.IsEqual`, que o painel não usa em nenhum outro ponto.
- **Como verificar:**
  - o Console deve mostrar `RONI: série mensal contínua? true`;
  - essa linha agora aparece **depois** da linha do fator de variância, porque é impressa no callback.

### [V4 IC] Incerteza dos análogos
- **Linhas:**
  - 685-686 e 694: rótulo `label_nota_ic`;
  - 1810-1823: tabela `IC95_CLOPPER_PEARSON_N10` e `textoIC95()`;
  - 1838;
  - 1880-1906.
- **O que mudou:**
  - Ao lado de cada probabilidade (El Niño, La Niña, Neutro e as 8 subcategorias) aparece "(IC 95%: a–b%)", tirado da tabela fixa com k = round(p·n/100).
  - Se o número de análogos efetivos (`amostrasUsadas`) for diferente de 10, aparece "(IC indisponível)".
  - Cada subcategoria vai para uma linha própria ("↳ Detalhe: Super: 50.0% (IC 95%: 18.7–81.3%)").
  - `whiteSpace` passa de 'pre' para 'pre-wrap' nesses dois rótulos, para quebrar linha no painel de 400 px.
  - Nota nova: "A probabilidade é a fração dos N análogos em que o desfecho ocorreu, não uma previsão calibrada…".
  - `N_ANALOGOS` já era 10 e não mudou.
- **Teste:** a tabela e a função são extraídas do painel e executadas no Node.
  - As 11 linhas batem com o Clopper–Pearson exato.
  - textoIC95(100, 10) = "(IC 95%: 69.2–100.0%)"; com 9 análogos, 0 análogos ou probabilidade ausente dá "(IC indisponível)".
- **Como verificar:** o Simular deve mostrar `Probabilidade EL NIÑO: 100.0% (IC 95%: 69.2–100.0%)` e Super 50.0% (18.7–81.3%).
- **A CONFIRMAR:** o aspecto visual dos rótulos com 'pre-wrap'.

### [V4 M06-23] Versão desconhecida
- **Linha:** 2428.
- **O que mudou:** o padrão do `ee.Dictionary(...).get(versaoImg, …)` passa a ser 'Desconhecido'. A `versao` ausente continua 'definitiva' e, portanto, 'Historico_Observado'.
- **Dicionário:** linha 2362.
- **Como verificar:** nada muda nos dados atuais. Uma `versao` nova aparece como "Desconhecido".

### [V4 F9/M06-11] Dicionário de variáveis
- **Linhas:** 2361-2392.
- **O que mudou:**
  - **Tipo_Dado:** "Previsao_GFS_Parcial (dia com rodada GFS incompleta: chuva, radiação solar, ETo e as colunas que dependem delas ficam vazias)" e "Desconhecido".
  - **Escoamento e chuva efetiva:** viraram "ÍNDICE NÃO VALIDADO", com a evidência da E3 (fator do SMAP acima de 5 em até 60% dos pixels na seca).
  - **Transpiração:** "vem da banda de evaporação do solo do ERA5-Land (evaporation_from_bare_soil_sum)… nos dias GFS vem do balanço de água do motor".
  - **Tsolo e Tfolha:** "vazia nos dias de previsão GFS".
  - **Latitude e Longitude:** entradas novas, com "centro do pixel… não é a sede do município".
  - **Colunas novas:** Qualidade_Pixel, Janela_Chuva_UTC, Confianca_Prazo, N_Dias, Dias_no_Mes e Mes_Completo, cada uma marcada como diário ou mensal.
  - **Precipitacao_mm:** remete a Janela_Chuva_UTC.
- **Evidência:** 05a:457-459 (transpiração), 05a:720-728 (tsolo/tfolha mascarados no GFS), 05a V1.5 linha 193 (bandas mascaradas no dia incompleto).
- **A CONFIRMAR:** o texto da transpiração. Ele repete o comentário do motor ("troca de bandas apontada no catálogo do GEE").

### [V4 versão]
- **Linhas:** 73 (`CFG.versao = '2026.10.4'`) e 3-27 (bloco "MUDANÇAS V4 (20/10/2026)" no cabeçalho).

### Formato dos CSV (apoio a Q1, F8, Conf e F4)
- **Linhas:** 2215-2297 e 2300-2318.
- **O que mudou:**
  - `formatarExportacaoClima(fc, colunasExtras)` monta o mesmo objeto de antes em `propsCSV` e copia só as colunas novas daquele CSV, com o mesmo padrão `If(propertyNames().contains(c), get(c), '')`.
  - `getColunasClimaDiaria()` e `getColunasClimaMensal()` inserem as colunas novas com `splice` sobre `getColunasClimaBase()`, que não mudou.
  - Nenhuma coluna existente mudou de formato. As posições mudam porque há colunas inseridas no meio.
- **Diário:** Tipo_Dado, Versao_Algoritmo, **Janela_Chuva_UTC, Confianca_Prazo**, Data_Completa … Latitude, Longitude, **Qualidade_Pixel**, Estado …
- **Mensal:** Tipo_Dado, Versao_Algoritmo, **N_Dias, Dias_no_Mes, Mes_Completo**, Data_Completa …

---

## Riscos
1. **Teste ANTES/DEPOIS do roteiro (6.2):** o CSV diário da 10.4 tem 3 colunas a mais e as posições mudam. A comparação precisa ser feita pelo nome da coluna. Curitiba não tem pixel de classe 4, então os pontos e o `N_Ponto` devem ser os mesmos.
2. **`ID_Ponto` em seleções de borda:** com a máscara, a numeração muda porque os pixels de classe 4 saem antes da ordenação. Isso é esperado.
3. **Custo de servidor:**
   - o filtro ENSO dispara mais um `evaluate`, só informativo, que recalcula a cadeia OISST e RONI (M06-26 ficou fora do escopo);
   - a avaliação inicial calcula também `gridComNomes.size()`, mas no mesmo pedido;
   - o Simular agrega as chaves 'Indefinida', o que é barato porque a fase já era calculada.
4. **Botão PROCESSAR:** fica bloqueado com um aviso enquanto a verificação da máscara não volta (normalmente 1 a 2 s).
5. **Alerta ao abrir:** antes da etapa 1, todo usuário verá o alerta "máscara de qualidade ausente" ao abrir o painel (ou o App).
6. **Camada "Área de Cobertura" no modo Estados:** amostra a grade de novo sem a máscara (linhas 2735-2744). O mapa pode mostrar pixels de borda que o CSV não tem. Mudanças no mapa ficaram fora do escopo.
7. **Qualidade_Pixel fora do mensal:** a coluna está só no diário, como define o contrato do SPEC.

## A CONFIRMAR (no Code Editor)
1. `unmask(0, false)` mantém na grade os pixels sem classe, inclusive fora do footprint do asset (ver Q1).
2. `Dias_no_Mes` e `N_Dias` saem como inteiros no CSV ("31", não "31.0").
3. Aspecto dos rótulos ENSO com 'pre-wrap' e o IC.
4. Texto da transpiração no dicionário.
5. O roteiro precisa ser atualizado nos pontos 6.2 (colunas novas), 6.4 (ordem das linhas do Console, IC, linha "Indefinida") e com testes novos: Amazonas sem "Leticia", máscara, colunas do mensal e alerta acima de 25.000.

## Fora do escopo (não feito, de propósito)
- **M06-07:** leitura das Baselines, normais e limiares, e regra do SPI.
- **M06-02:** CSV ponderado por área, caixa exata, `Fracao_Pixel_na_Area`, ID estável por linha e coluna.
- **M06-14 e ajustes visuais:** mudanças no mapa e na legenda (grade do mapa, texto "valor ZERO", suavização, camada "Área de Cobertura" sem máscara).
- **M06-26, M06-27 e M06-28:** as demais otimizações (chaves ENSO avaliadas uma vez, correção V1.0 por filtro ou asset, grade única ou anos sem dados).
- **Demais itens da revisão não pedidos:**
  - M06-08: metadados e sufixo ENSO;
  - M06-09: estimativa de linhas e `Export.table`;
  - M06-10: exportações ENSO no App e subcategorias no CSV de previsão;
  - M06-12: máscara SAB fixa;
  - M06-13: `crsTransform` no `reduceRegions`;
  - M06-16: `toInt` antes de `format`;
  - M06-17: empates de análogos, `RONI_2c`, Neutro em −0,49;
  - M06-18: intensidade por episódio;
  - M06-19: aviso OISST provisório;
  - M06-20: hoje local × UTC;
  - M06-21: `centerObject` assíncrono;
  - M06-22: municípios homônimos e rótulos de erro;
  - M06-24: vírgula decimal;
  - M06-25: código morto.
- **CSV de previsão ENSO (`btn_exportar_enso`):** continua sem as colunas de IC.

## 2026.10.5 (30/10/2026): variáveis do arquivo e envio por e-mail

Arquivo: `06_painel_sab_2026_10_5.js`. Origem: validações K13 a K15 (link na hora aguenta ~100 mil linhas por
arquivo; a exportação em lote não tem esse teto). O cálculo, a grade e o formato dos números não mudam.

- **Variáveis do arquivo (bloco 8):** "Todas as variáveis" marcada por padrão; desmarcando, as 19 aparecem por
  grupo. `filtrarColunasPorVariaveis` tira do CSV só as colunas das variáveis não marcadas (identificação,
  qualidade e ENSO ficam sempre). Com todas marcadas, os CSV são idênticos aos da 2026.10.4.
- **Link na hora ou e-mail (`decidirEntrega`):** linhas do maior arquivo = pontos × dias do ano (teto 366) ou × 12;
  arquivos = locais × anos. Acima de `CFG.limiteLinhasLink` (100 mil) ou `CFG.limiteArquivosLink` (20), não gera
  os links e mostra só "Receber por e-mail". Com `CFG.urlPedidoEmail` vazio, o comportamento é o da 2026.10.4.
- **Qualquer busca por e-mail:** com o envio configurado, a caixa "Receber por e-mail" aparece em todo
  processamento, inclusive com o filtro ENSO (o código leva `enso=<cenário>`; a rotina aplica o mesmo recorte).
- **Pedido por e-mail (`montarCodigoPedido` + `painel_pedido_email`):** nome, e-mail, instituição, finalidade e
  aceite da LGPD; o link gerado abre o App da Web do Apps Script (`doGet`), que registra o pedido na planilha
  sem passar pelo formulário. O código do pedido usa os mesmos nomes da tela (estados, municípios do GAUL,
  vértices como estão na lista).
- **Testes:** `testes/teste_06_pedido_email.js` (funções novas com controles simulados) e
  `testes/teste_06_pedido_email.py` (os códigos gerados são aceitos pela rotina `sab_pedido.py`).
- **Pendente antes de abrir ao público:** K16 (identidade da rotina do e-mail com o painel).

---

## 2026.10.6 (01/11/2026): caixa "Receber por e-mail"

- **Arquivo:** `06_painel_sab_2026_10_6.js` (cópia da 2026.10.5 com 38 linhas a mais/diferentes, todas marcadas `[2026.10.6]`).
- **O que mudou (só a caixa do e-mail):**
  - lista **Formato dos arquivos**: CSV, Excel (.xlsx) ou CSV e Excel; a escolha vira `;fmt=xlsx` ou `;fmt=ambos` no código
    (função nova `pedidoComFormato`); CSV é o padrão e não muda o código;
  - aviso de **spam** e das **6 colunas ENSO** que os arquivos do e-mail trazem;
  - até **6 estados** por pedido por e-mail (o Brasil inteiro estourou a memória do Earth Engine em 31/10/2026, pedido
    P20261031213150mffz); acima disso o painel avisa e não gera o link;
  - texto da entrega cita o formato e que o Brasil inteiro não vai por e-mail.
- **Não mudou:** cálculo, grade, colunas e CSV do link na hora (os da K14/K16), filtro ENSO do item B, dicionário.
- **Conferido:** `node --check`; `acorn` ES5 (e o teste negativo com `let`/arrow rejeitado); `testes/teste_06_pedido_email.js`
  (com os casos de formato) e `testes/teste_06_pedido_email.py` (a rotina 2026.11.01 aceita todos os códigos gerados).

## 2026.10.7 (02/11/2026): textos do El Niño / La Niña mais claros

- **Arquivo:** `06_painel_sab_2026_10_7.js` (cópia da 2026.10.6; 130 linhas novas/diferentes, todas no bloco ENSO,
  marcadas `[2026.10.7]`).
- **Por quê:** o usuário achou o resultado do item A confuso (parágrafos longos, explicação do método misturada com o
  resultado, a resposta principal só no fim).
- **O que mudou (só textos e ordem na tela):**
  - item A: título "A. El Niño / La Niña agora e nos próximos 3 meses", descrição de 2 linhas, botão
    "📊 Ver a situação e a estimativa";
  - **AGORA** em 4 tópicos curtos (situação, temperatura do mar/RONI, últimos 5 meses, fonte) + último mês (colorido);
  - **PRÓXIMOS 3 MESES**: primeiro a *resposta curta* ("El Niño muito provável (10 dos 10 anos…)"; palavras: 10 de 10 =
    muito provável, ≥ 7 = provável, 6 = um pouco mais provável, ≤ 5 = incerto, empate = resultado dividido), depois a
    contagem por fase e força;
  - logo abaixo (sempre visível): anos parecidos, o aviso de força subestimada (quando o aquecimento/resfriamento de agora
    é maior que o de todos os anos parecidos), o convite para o item B e o lembrete da previsão oficial do CPC/NOAA;
  - explicação longa (como é feita, margem de erro, força incerta, limite do método, RONI, siglas) atrás do botão
    **ℹ️ Como ler este resultado** (abre e fecha);
  - item B: título "B. Clima do passado em meses de El Niño, La Niña ou neutro" e instruções em 3 passos; nota do botão
    da lista encurtada.
- **Não mudou:** motor de análogos, probabilidades, IC 95%, classificação dos meses, filtro do item B, CSV da previsão
  (`montarLinhasExportEnso`), colunas, link na hora e e-mail. A K16 continua valendo (nenhuma linha de cálculo mudou).
- **Conferido:** `node --check`; `acorn` ES5; `testes/teste_06_enso.js` (151 de 151, com os casos novos: 7 de 10, 5 de 10,
  empate, neutro dominante, aviso de força fora do "Como ler"); `teste_06_colunas.js`, `teste_06_numeros.js`,
  `teste_06_pedido_email.js/.py` apontando para a 2026.10.7.

## 2026.11.1 (03/11/2026, noite): correção de leitura dos pixels B e da radiação dos pixels C

Decidida depois das auditorias K18 e K19 (03/11/2026). **O banco não muda**; muda só o que o painel entrega.

- **Pixels B** (lagoas e estuários; o motor V1.0 descartou o BR-DWGD e preencheu com o ERA5 dos vizinhos): nos dias de 1961 a 2025, as 8 bandas do núcleo (chuva, Tmax, Tmin, UR, VPD, ETo, radiação, vento) passam a vir do BR-DWGD do dia, decodificado exatamente como a V1.0 faz nos pixels A (`brdwgdDoDia`, `corrigirPixelsB`). K18: a chuva diária desses pixels diferia 4,8 mm do BR-DWGD; a ETo, 20%.
- **Pixels C** (sem BR-DWGD): nos dias de 1961 a 2025, a radiação fica limitada à de céu claro, Rso = (0,75 + 2e-5 z) Ra (FAO-56, eq. 21 e 37; Allen 1996). K19: 18% dos dias passavam do limite.
- O grampo ET real ≤ ETo e transpiração ≤ ET real continua depois (agora sobre a ETo do BR-DWGD nos pixels B).
- Só entra quando a área pedida tem pixel B ou C (`areaTemPixelsBC`); fora disso o custo é o mesmo de antes. Dias de 2026 não mudam.
- `verificarBRDWGD`: se o app público não puder ler o BR-DWGD (asset de outro usuário), o painel segue sem a correção e avisa no Console. O botão PROCESSAR espera essa verificação, como já esperava a da máscara.
- Dicionário: texto da `Qualidade_Pixel` atualizado (igual no `sab_pedido.py` 2026.11.03).
- Validação: K20 (só leitura: B = BR-DWGD, A intocado, C ≤ céu claro, grampo, 2026 intocado, polígono A6 com pixels B) e K16 v4 (caso novo A6, Lagoa dos Patos). Teste `teste_correcao_b_identica.py`: as constantes da correção são as mesmas no JS e no Python.

## 2026.11.2 (04/11/2026): autoria e link oficial; app novo

- O painel ganhou no topo a linha de autoria (`CFG.autoria`: "Desenvolvido por Adão Alves Rodrigues Junior (UTFPR,
  Pato Branco)") e o link oficial clicável (`CFG.urlApp`).
- App novo `cloud/clima-492922/adao-alves-rodrigues-junior-sab`
  (https://clima-492922.projects.earthengine.app/view/adao-alves-rodrigues-junior-sab). O app antigo
  (`sab---sistema-agrometeorolgico-brasileiro`) foi apagado pelo autor em 04/11, por isso o aviso de endereço preparado
  para ele (`06b_aviso_endereco_antigo.js`) foi descartado.
- **Nada mais muda**: `testes/teste_06_2026_11_2.py` confere que, fora o cabeçalho, a versão, as duas chaves do CFG e os
  dois rótulos, o código é o da 2026.11.1 (K20 e K16 v4 aprovadas em 03/11 valem para ela).
- Implantação: a 2026.11.1 foi colada no script `SAB_painel_2026_10_6` (o nome do script não acompanha a versão) e
  publicada no app oficial em 04/11, 4h; teste da Lagoa dos Patos e pedido por e-mail SAB2026-00020 conferidos.

## 2026.11.3 (04/11/2026): envio por e-mail num clique

- A caixa "Receber por e-mail" tinha dois passos (botão **Gerar o pedido por e-mail** e depois o link "Clique aqui para
  enviar"). Agora há **um botão só, "Clique aqui para ENVIAR O PEDIDO"** (fundo claro e borda azul: o Earth Engine pinta todo link de azul), que aparece pronto assim que nome, e-mail, finalidade e o
  aceite da LGPD estão preenchidos; antes disso, uma linha diz tudo o que falta de uma vez.
- O envio continua sendo um link clicado: o painel do Earth Engine não tem como chamar outro site sozinho. O clique abre
  a aba de confirmação com o número do pedido, como antes.
- `montarUrlPedidoEmail` (função pura) monta o mesmo endereço da 2026.11.2: `testes/teste_06_2026_11_3.js` compara os dois
  nos 3 formatos, confere os avisos (campos faltando, mais de 6 estados, sem processar) e que o resto do painel é idêntico.
- Cálculos e CSV iguais aos da 2026.11.1 (K20 e K16 v4 valem).

### 04/11/2026: arrumação depois da implantação

- Só existe um script do painel, `SAB_painel_2026_10_6`, e um app, `adao-alves-rodrigues-junior-sab`. O arquivo para colar é
  `06_painel_sab_2026_11_3_PRONTO.js` (gerado por `montar_painel_pronto.py`: o painel-base com o endereço `/exec` dos
  pedidos; `testes/teste_06_pronto.py` confere que é só isso). O painel-base fica com `urlPedidoEmail` vazio para a K16.
- Testes do painel (`teste_06_colunas/enso/numeros/pedido_email`, `teste_correcao_b_identica`, `teste_k16_painel_node`) e
  a K16 (agora **v5**) apontam para a 2026.11.3, a que está no ar.
