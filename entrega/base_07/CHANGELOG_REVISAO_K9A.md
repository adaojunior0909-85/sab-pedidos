# REVISÃO K9A DO PACOTE v4.1 (20/10/2026, noite)

Esta revisão parte do pacote `SAB_FINAL_v4_1_REVISADO_2026-10-20.zip` e prevalece sobre os CHANGELOG anteriores quando houver divergência.

Ela aplica a única mudança que a validação K9A indicou pela regra fixada antes de rodar:

- **Umidade relativa e radiação** dos dias de previsão GFS passam a ser corrigidas pela **escala de variância**, a mesma correção já usada na Tmax e na Tmin desde a K8.
- **Chuva, vento, Tmax e Tmin** continuam exatamente como estavam.
- **O histórico de 1961 a 2025 não é tocado.** A trava continua ligada (`PROTEGER_HISTORICO = True` até 2025-12-31), e o `teste_05` confere isso.

## 1. Arquivos alterados

| Arquivo | O que mudou |
|---|---|
| `05a_motor_sab_v1_5_SIMULACAO.py` e `05b_motor_sab_v1_5_GRAVACAO.py` | Ver os itens abaixo. Os dois continuam diferindo só na linha 1 e em `SIMULAR`. |
| `08_auditoria_completa_SAB.py` | D14 confere também `metodo_ur_rs_gfs = 'variancia'` em todo dia GFS V1.5 (constante `METODO_UR_RS_GFS_ESPERADO`); o inventário de 2026 lê a propriedade nova. |
| `03_matriz_gfs_v2_1.py` | **Só um comentário do cabeçalho**, que dizia que o motor usava apenas as médias da matriz. O cálculo e as 100 bandas são os mesmos: **não é preciso rodar o 03 de novo.** |
| `00_ROTEIRO_FINAL.md` | Ver os itens abaixo. |
| `SPEC_V4.md` | Contrato da propriedade `metodo_ur_rs_gfs`, das 32 bandas de desvio exigidas e do refazer por método. |
| `testes/teste_05.py` | Ver os itens abaixo. **1.714 verificações, 13 de 13 OK.** |
| `testes/teste_08.py` | O contrato exige `metodo_ur_rs_gfs = 'variancia'`. Um dia GFS com `'original'` ou sem a propriedade é acusado. **Todos passaram.** |
| `validacoes/` (pasta nova) | Ver os itens abaixo. |
| `SHA256SUMS.txt` | Regenerado. |
| `CHANGELOG_REVISAO_K9A.md` | Este arquivo (novo). |

**Mudanças no motor (05a e 05b):**
- Constante nova `METODO_UR_RS_GFS = 'variancia'`. Com `'original'`, volta à UR aditiva e à radiação com fator.
- Fórmulas dos dias GFS:
  - umidade relativa: `calib_variancia(...)`, limitada a [0, 100];
  - radiação: `calib_variancia(...)`, com valor mínimo 0;
  - o vento continua com o fator limitado a [0,5; 2].
- O motor passa a exigir na matriz as 16 bandas de desvio da UR e da radiação (`BANDAS_DESVIO_UR_RS`). Elas já existem na matriz V2.1.
- Propriedade nova nos dias GFS: `metodo_ur_rs_gfs`.
- O inventário e o `precisa_refazer_gfs` leem essa propriedade. Um dia gravado com outro método é refeito na execução seguinte; um dia sem a propriedade conta como `'original'`.
- Linha nova no início da execução: `Correção da UR e da radiação nos dias GFS: variancia ...`.

**Mudanças no roteiro (`00_ROTEIRO_FINAL.md`):**
- Parte A: decisão nova (A.1), nota 11 (K9 e K9A, com as limitações), linhas novas na A.3 e evidência da K9A na nota 6.
- Etapa 5a: a matriz agora mostra "32 de desvio", e há a linha nova da UR e da radiação.
- Etapa 5b: confere as duas linhas de método.
- Etapa 8: D14 confere também `metodo_ur_rs_gfs`.
- Parte 4: refazer a K9A no período do GFS v17.
- Lista de conferência atualizada.

**Mudanças no `teste_05`:**
- O padrão é `'variancia'`, e há uma única linha da constante.
- As 16 bandas novas têm os nomes do contrato V2.1 e não repetem as da temperatura.
- As fórmulas da UR, da radiação e do vento estão no código.
- O refazer automático e os padrões de leitura funcionam.
- **Equivalência numérica:** em 500 sorteios, a fórmula do motor dá o mesmo valor que a da K9A, com diferença menor que 10⁻⁹. Isso vale para a UR, para a radiação e para o método original da radiação.

**Pasta `validacoes/`:**
- `K8_validacao_quantis.py`: a versão executada.
- `K9_validacao_todas_variaveis.py`: a versão executada, com uma nota de registro.
- `K9A_validacao_ampliada.py`: já compara com o motor atual. Os métodos de antes da K9A entram como alternativas. Conferido offline: os números são idênticos aos da execução de 20/10, só os rótulos mudam.
- As três são somente leitura e não precisam ser rodadas de novo.

## 2. Arquivos conferidos e mantidos sem nenhuma mudança

`01a`, `01b`, `02`, `04`, `06`, `07a` e `07b` são byte a byte iguais ao pacote revisado anterior. Também ficaram iguais os CHANGELOGs anteriores, os testes 01, 02, 03, 04, 06 e 07, o `fumaca_08_01.py`, o `maximos_pares_v16.py` e a pasta `testes/dados/`.

Todos os testes do pacote passaram de novo:

| Teste | Resultado |
|---|---|
| `teste_03` | 636 verificações |
| `teste_04` | 35 verificações |
| `teste_05` | 1.714 verificações |
| `teste_06_enso` | 52 de 52 |
| `teste_01`, `teste_01_uniao`, `teste_02`, `teste_02_troca`, `teste_06_colunas`, `teste_07`, `teste_08` | OK |
| Fumaça da 08 e da 01 | OK |

- Todos os scripts compilam.
- A checagem de nomes não acusou nenhum nome indefinido.

## 3. Evidência (K9A; o detalhe está na Parte A, nota 11, do roteiro)

O teste usa o GFS v16, com treino de 2021 a 2024 e teste em 2025 inteiro: 300 pontos e 438.000 previsões. A margem de incerteza (IC 95%) vem de sorteios de dias.

| Variável | Antes | Agora | Ganho | Anos do v16 em que ganha |
|---|---|---|---|---|
| Umidade relativa (MAE, pontos) | 6,65 | 4,98 | −25% (IC −1,72 a −1,62) | 5 de 5 |
| Radiação (MAE, MJ/m²/dia) | 3,51 | 3,03 | −14% (IC −0,51 a −0,44) | 5 de 5 |
| ETo (MAE, mm/dia) | 0,704 | 0,611 | −13%; erro do total mensal de 6,3% para 5,7% | 5 de 5 |

**Limitações registradas na tese:**
- Dias com UR abaixo de 30%: 0,09% previstos contra 0,18% observados.
- Dias com ETo acima de 6 mm: 3,3% previstos contra 4,3% observados.
- O ganho da radiação não se repetiu nas versões antigas do GFS. A validação deve ser refeita quando o GFS v17 entrar.

## 4. Se a etapa 5b já tiver sido rodada com o pacote anterior

Não é preciso desfazer nada. Basta colar o 05b novo e rodar:
- os dias GFS sem `metodo_ur_rs_gfs` são refeitos sozinhos;
- os dias ERA5 e o histórico não mudam.

Antes disso, rode o 05a uma vez e confira a linha `Correção da UR e da radiação nos dias GFS: variancia`.

## 5. Correção de 20/10/2026, 23h: 01a e 01b (erro na 1ª execução real)

- **Erro:** o 01a parou com `ValueError: could not convert string to float: 'null'`, logo depois de `✅ estrutura (A+B, C e D) idêntica pixel a pixel nos 5 dias`.
- **Causa:** o `ee.Reducer.frequencyHistogram()` devolveu a chave `'null'`, de pixels sem valor na borda da máscara, junto com as contagens. A conversão de cada chave para número falhou.
- **Correção:** a conta "em quantos dos 5 dias cada pixel da união esteve em B" passou a ser feita por indicadores somados (`dias_0` a `dias_5`), como as outras contagens do script. O `frequencyHistogram` saiu.
- **Aviso novo:** se aparecer algum pixel da união com 0 dias, o log mostra um ℹ️.
- **O que não mudou:** as classes, a exportação e as conferências são as mesmas. O 01a e o 01b continuam diferindo só na linha 1 e em `SIMULAR`.
- **Testes:**
  - `fumaca_08_01.py` foi ajustado ao formato novo da resposta e passou;
  - `teste_01` e `teste_01_uniao` passaram.

## 6. Correção de 20/10/2026, 23h30: trava herdada na sessão e diagnóstico da união B

**a) A trava do 01a continuava ligada no 01b.**
- **O que aconteceu:** o 01b, rodado na mesma sessão do Colab logo depois do 01a, parou em `task.start()` com `SIMULAÇÃO: escrita bloqueada`. **Nada foi gravado.**
- **Causa:** o 01a bloqueia as funções de escrita do Earth Engine, e o bloqueio continua valendo nas células seguintes da sessão.
- **Correção:** os scripts que gravam (01b, 02, 03 e 05b) verificam, logo depois de conectar, se a trava está ligada. Se estiver, param antes de qualquer conta, com a instrução `Ambiente de execução → Reiniciar sessão`.
- **No roteiro:**
  - regra geral: sessão limpa antes de cada script que grava;
  - etapa 1.2: reiniciar a sessão antes do 01b.
- **Teste:** o `teste_02_troca` foi ajustado para ignorar o `if` novo da trava. Passou.

**b) O histograma de dias em B não era confiável.**
- **O que aconteceu:** a 1ª versão da correção das 23h mostrou `{0: 19, 1: 20, 2: 46, 3: 61, 4: 50, 5: 105}`, embora a conferência por dia estivesse limpa (só 1 coincidência).
- **Causa provável:** o `unmask(0)` mantém a pegada (footprint) da imagem de cada dia. Um pixel sem classe num dia contava como "não B".
- **Correção:**
  - para cada dia, cada pixel da união B é contado como B, A ou sem classe (`unmask(0, False)`), e o log mostra uma linha por dia e grava `Q1_uniao_B_por_dia.csv`;
  - o histograma considera só os pixels com classe nos 5 dias;
  - os pixels com algum dia sem classe aparecem num ℹ️ à parte.
- **A classificação não mudou.** Na execução das 23h23, a receita da J1 bateu exatamente (A 70.364, B 204, C 1.109), assim como as classes 3 = 48 (K1d: 48) e 4 = 1.064 (referência ~1.060).
- **Teste:** `fumaca_08_01.py` tem um caso novo (pixels sem classe num dia) e passou.

## 7. Correção de 20/10/2026, 23h55: 02 (exportação do RONI)

- **Erro:** a 1ª gravação real parou na exportação: `Exportação falhou: ... 'error_message': 'Unable to export features with null geometry.'`.
- **O que não mudou:** a tarefa falhou antes de qualquer troca de asset. Nada foi renomeado, apagado ou gravado, e o asset antigo `RONI_Calibrado_Sazonal_1950_1980` ficou intacto.
- **Causa:** a exportação de tabela para asset do Earth Engine recusa feições sem geometria.
- **Correção:** cada estação recebe um ponto fixo (0, 0), só para a exportação.
  - O painel (06), a auditoria 08 e a conferência de leitura do próprio 02 usam apenas as propriedades (ano, mes, RONI etc.), que não mudam.
  - As contas, a conciliação com o CPC e a troca com backup também não mudam.
- **Testes:** o `teste_02_troca` passou a simular `ee.Geometry.Point`. Ele e o `teste_02` passaram.

## 8. Correção de 21/10/2026, 18h: 05a/05b e 08 (lacuna no ERA5-Land)

- **Erro:** na 1ª execução real do 05b, as tarefas `SAB_M_2026_10_09_C1` e `SAB_M_2026_10_10_C1` falharam com `Image.select: Parameter 'input' is required and may not be null`.
- **O que não mudou:** nada foi gravado nesses dois dias. Eles continuam com os valores antigos (previsão V1.3) até a próxima execução, e os outros dias não foram afetados.
- **Causa:** o ERA5-Land DAILY_AGGR do Earth Engine publicou 2026-10-11 antes de 2026-10-09 e 2026-10-10. O motor usava a data máxima publicada como fim da rota ERA5 e mandou calcular dois dias que não tinham imagem.
- **Correção no motor (05a e 05b):** a rota ERA5 vai só até o último dia contínuo, sem lacuna (função nova `ultimo_dia_continuo`). Da lacuna em diante, os dias seguem pela previsão GFS, com a rodada 00Z do próprio dia. Quando o ERA5 preencher a lacuna, a execução seguinte refaz esses dias como ERA5, pelo mesmo caminho que já transforma dias de previsão em dias ERA5. O log mostra um ⚠️ com os dias que faltam.
- **Correção na auditoria 08:** a seção D14 confere a emenda ERA5 → GFS contra o mesmo último dia contínuo (`ultimo_dia_continuo_era5`).
- **Testes:**
  - `teste_05`: o caso real de 21/10 está incluído; 1.719 verificações, 14 de 14 OK;
  - `teste_08`: 2 casos novos, todos passaram;
  - o resto da bateria passou de novo.

## 9. Alteração de 22/10/2026: 06 (apresentação do ENSO no painel)

- **Pedido:** deixar o resultado da "Previsão da Próxima Estação" mais claro, com os anos análogos em ordem crescente.
- **Auditoria antes da mudança:** o motor de análogos foi reproduzido offline sobre a série oficial do 02. Os 10 anos e as probabilidades (100% El Niño; Super 50%, Forte 10%, Mod 30%, Fraco 10%) batem com a saída do painel do usuário em 21/10.
- **O que mudou:** só a apresentação, em três blocos:
  1. **Situação atual:**
     - estação e meses;
     - faixa de intensidade;
     - se o episódio já está confirmado;
     - trajetória de 5 meses, com o valor do início e o do fim;
     - variação do último mês;
     - fonte.
  2. **Previsão:**
     - estação prevista e seus meses;
     - os análogos em ordem crescente e o mais parecido;
     - cada fase e cada intensidade com os anos que caíram nela.
  3. **Como ler:**
     - o significado da porcentagem;
     - os intervalos de 95% (Clopper–Pearson).
- **Função nova:** `montarTextosEnso`, pura. O dicionário do motor ganhou campos só para a exibição: `oniFuturoAnalogos`, `roniInicioTendencia`, `variacaoTri`, `mesAtual` e `faseAtual`.
- **O que não mudou:**
  - o cálculo dos análogos, a semelhança, os limites e as probabilidades, que continuam vindo do servidor;
  - o CSV exportado.
- **Proteção:** a contagem por faixa é refeita no cliente. Se ela não bater com a do servidor, o Console mostra um aviso.
- **Testes:** `teste_06_enso` passou de 52 para 77 verificações, todas OK. Cobrem os textos esperados, a virada de ano (SON → DJF e NDJ → FMA do ano seguinte), a fonte OISST, o caso com 9 análogos e a contagem divergente. O `teste_04` e o `teste_06_colunas` passaram.
- **Roteiro:** a etapa 6.4, passo 3, foi atualizada com o texto novo.
- **Revisão de 22/10, 0h50 (texto para leigos):**
  - **Sem siglas no texto principal:** os meses aparecem por extenso ("julho a setembro de 2026"), respeitando a virada de ano de DJF e NDJ.
  - **"Acima/abaixo do normal" no lugar do sinal**, com concordância de gênero (o El Niño, a La Niña).
  - **Contagens em palavras:** "10 dos 10 anos" e "nenhum dos 10 anos". "Super" virou "Muito forte".
  - **Margem de 95% em palavras:** "pelo menos 69%", "até 45%".
  - **Novo no "Como ler":** o que é o RONI e o significado das siglas, que continuam no CSV.
  - **Descrição do bloco simplificada.**
  - **Testes:** `teste_06_enso` com 85 verificações, todas OK, incluindo os casos neutro, La Niña confirmada e La Niña ainda não oficial.
- **Revisão de 22/10, 1h05 ("Como ler" e frase do RONI):**
  - **Definição do RONI conferida na página do CPC:**
    - Niño 3.4 (5°N–5°S, 120°–170°W) menos a média dos oceanos tropicais (20°N–20°S);
    - reescalado para a variância do Niño 3.4;
    - média de 3 meses;
    - limiares de ±0,5 °C e 5 trimestres seguidos para o episódio.
  - **Correção do texto:** a frase "acima do normal" passou a dizer "já descontado o aquecimento geral dos oceanos tropicais". O RONI é uma anomalia relativa, e não a anomalia direta do Pacífico.
  - **Intervalos de 95% (Clopper–Pearson):** os números continuam certos. A lista com todos eles saiu; ficam só o intervalo do resultado principal e o da intensidade mais frequente, em palavras.
  - **Novo:** um aviso de que o intervalo cobre só o tamanho da amostra, e não o erro do método. A frase "a chance real fica em" exagerava isso.
  - **Testes:** `teste_06_enso` com 91 verificações, todas OK, incluindo o resultado misto (6 de 10) e o neutro dominante.
- **Revisão de 22/10, 1h30:**
  - **"O que aconteceu 3 meses depois"** passou a dizer o que foi comparado: o estado do oceano de outubro a dezembro dos anos parecidos (fase e força). Não são os efeitos no clima, que o texto agora remete ao item B.
  - **Margem de erro** escrita como intervalo fechado ("entre 69% e 100%"), com a pergunta "Por que não é certeza, se deu 10 em 10?".
  - **Testes:** `teste_06_enso` com 93 verificações, todas OK.
- **Revisão de 22/10, 1h50 (downloads do ENSO e item B):**
  - **Downloads por link direto (`getDownloadURL`), como os dados climáticos.** Os dois botões do ENSO usavam `Export.table.toDrive`, que só funciona na aba Tasks do Code Editor e não existe para quem usa o App publicado. O link aparece logo abaixo do botão.
  - **CSV da previsão em dois arquivos, iguais à tela:**
    - Resumo, com as estações atual e prevista, as probabilidades, as intensidades e os IC95;
    - Anos análogos, um ano por linha, com o RONI da estação, a trajetória, a distância de semelhança, o RONI da estação prevista, a fase e a intensidade.
  - **CSVs sem acentos**, para o Excel não estragar os caracteres. O CSV é montado a partir do resultado mostrado, sem recalcular, pela função pura `montarLinhasExportEnso`.
  - **Lista de meses (item B):** o ano sai inteiro (antes, 1950.0).
  - **Texto do item B e da previsão:** explicam que os efeitos no clima saem nos CSV dos dados, com o filtro marcado e PROCESSAR DADOS CLIMÁTICOS. O botão do item B baixa só a lista de meses.
  - **Testes:** `teste_06_enso` com 105 verificações, todas OK, incluindo a de que nenhum download do painel usa Export.
  - **Roteiro:** 6.4 (passo 4) e 6.5 atualizados.
- **Revisão de 22/10, 2h (item B mais claro):**
  - **Lista de meses:** a matriz no formato da NOAA (anos × trimestres, quase toda vazia, sem explicação) virou uma lista legível, um mês por linha, de 1961 até hoje. Colunas:
    - Ano, Mes e Mes_Nome;
    - Trimestre_CPC e os meses do trimestre;
    - RONI_C, Fase, Intensidade e Fonte_RONI.
  - **São exatamente os meses que o filtro mantém nos dados** (mesmo pareamento por AAAA_MM).
  - **Botão e textos:**
    - o botão passou a se chamar "Ver quais meses entram no filtro";
    - uma nota diz que a lista não tem dados de clima;
    - a descrição do item B virou 3 passos, deixando claro que a chuva e a temperatura saem nos arquivos de "Arquivos Prontos para Download".
  - **Testes:** `teste_06_enso` com 113 verificações, todas OK. Inclui os 19 meses de Super El Niño, iguais à matriz baixada pelo usuário.
- **Revisão de 22/10, 2h15 (efeitos do fenômeno nos CSV de dados):**
  - **Motivo:** o usuário baixou a lista do botão esperando chuva e temperatura.
  - **Colunas novas, só com o filtro ENSO do item B ligado:** os CSV diário e mensal ganham no fim `Filtro_ENSO`, `Fase_ENSO`, `Intensidade_ENSO`, `RONI_Trimestre_C` e `Trimestre_CPC`. Assim, chuva, temperatura e fenômeno ficam na mesma linha. Os dias de previsão ficam com essas colunas vazias.
  - **Nome do arquivo:** termina com o fenômeno (por exemplo, `Mensal_Pato_Branco_1982_Super_El_Nino`).
  - **Anos sem o fenômeno no período** não geram arquivo vazio. Se nenhum mês tiver o fenômeno, aparece um aviso.
  - **Sem o filtro, nada muda:** as mesmas colunas, os mesmos nomes e o mesmo fluxo síncrono. O dicionário ganhou as 5 colunas.
  - **Textos:**
    - item B em 4 passos, com o nome do arquivo e das colunas;
    - botão da lista renomeado para "Só a lista de meses do fenômeno (sem dados de clima)".
  - **Testes:** `teste_06_enso` com 119 verificações, todas OK; `teste_06_colunas` OK.
- **Revisão de 22/10, 2h30 (divergências entre os itens A e B apontadas pelo usuário):**
  1. **Nomes e faixas da lista do item B:** eram "Super El Niño (≥ 2.0°C)", "Anos Neutros", com ponto decimal. Agora são os mesmos do item A: "El Niño muito forte, Super (+2,0 °C ou mais)", "Neutro (entre −0,5 e +0,5 °C)", com vírgula. Uma tabela única (`CENARIOS_ENSO`) dá o rótulo, o valor interno (inalterado, usado pelo `filtroCenario`), o texto da coluna `Filtro_ENSO` e o sufixo do arquivo (`_El_Nino_Muito_Forte`).
  2. **Anos antes de 1961:** o item A busca anos parecidos desde 1950, mas os dados de clima começam em 1961. O texto agora diz quais anos parecidos ficam sem dados de clima (hoje, 1951 e 1957).
  3. **O que o filtro usa:** o item B filtra pelo tipo e pela força do fenômeno em cada mês desde 1961, e não pelos 10 anos parecidos. Isso agora está escrito no item B.
  4. **Títulos:** o título do item B virou "Como foi o clima em meses de El Niño, La Niña ou neutro", e a opção virou "Filtrar os dados do passado por fenômeno" (não eram médias).
  5. **Siglas:** "aparecem no CSV baixado" virou "nos arquivos CSV da previsão e do item B".
  - **Testes:** `teste_06_enso` com 123 verificações, todas OK. Conferem que os valores da lista são as 9 chaves do `filtroCenario` e que nenhum rótulo tem ponto decimal.
- **Revisão de 22/10, 2h40 (as 4 correções da análise dos arquivos do usuário):**
  1. **"Ainda não é oficial" removido.** O texto agora diz que a regra dos 5 trimestres é a da tabela histórica do CPC e que o CPC pode já ter declarado condições de El Niño ou La Niña no boletim mensal. Em 08/10/2026 o CPC estava em "El Niño Advisory". O mesmo ajuste foi feito na linha do RONI do "Como ler".
  2. **Arquivos com o filtro ENSO:**
     - passado e previsão agora são separados pelo tipo de dado (`versao`), e não pela data de hoje, então voltam os dias de previsão de datas passadas ainda sem ERA5;
     - nos dias de previsão, as colunas ENSO vêm preenchidas: `Fase_ENSO` = "Previsao (sem classificacao)", `-` na intensidade e no RONI, e `Trimestre_CPC` pela data.
  3. **RONI com uma casa decimal nos CSV** (lista de meses, anos análogos e resumo). Por exemplo, "2.0" em vez de "2".
  4. **Limite do método no "Como ler"**, com os valores do dia:
     - o maior RONI dos anos parecidos na estação prevista (hoje +2,3 °C), que o método não consegue ultrapassar;
     - um aviso quando o aquecimento ou resfriamento atual supera o de todos os anos parecidos (hoje +2,1 °C contra o máximo de +1,6 °C, em 1997).
  - **Testes:** `teste_06_enso` com 131 verificações, todas OK; `teste_04` e `teste_06_colunas` OK.

## 10. Auditoria 08 de 22/10/2026, 7h07: correção da seção F e diagnóstico K10

- **Resultado:** 43 OK, 22 INFO, 4 ATENÇÃO e 1 NÃO EXECUTADO. O código rodado é idêntico ao do pacote.
- **Seção F interrompida** (`ValueError: All arrays must be of the same length`, em `horas_00z`):
  - **Causa:** `Reducer.toList().repeat(2)` descarta os nulos de cada coluna em separado. Basta uma imagem GFS de 2016 sem `creation_time` ou sem `forecast_hours` para as duas listas saírem com tamanhos diferentes.
  - **Correção:** filtro `notNull` nas duas propriedades, também na F3 por precaução, e uma mensagem clara se as listas ainda divergirem.
  - **O que se perdeu:** só a F5 (datas das mudanças do GFS, informativa), que deixou de sair.
- **J5a (ATENÇÃO):** 2026-10-26, previsão GFS da rodada de 21/10 00Z, prazo L6 (confiança média), com Tmax máxima nacional de 45,24 °C, acima do recorde do INMET (44,8 °C). 0,31 % dos pixels passaram de 42 °C. A PRÉVIA 6 do 05a não pegou o caso porque testa só os prazos L1, L2, L8 e L11.
  - **Novo script `validacoes/K10_diagnostico_tmax_recorde.py`** (só leitura, não trava a sessão). Ele mostra:
    - o pixel do máximo e a fração dele dentro do Brasil;
    - o GFS bruto da mesma rodada e os parâmetros da matriz;
    - a decomposição entre o viés do modelo e o efeito da calibração;
    - a maior Tmax do histórico no pixel.
  - **Objetivo:** decidir entre (a) viés do GFS, (b) efeito da escala de variância e (c) pixel de borda, antes de mexer no motor.
- **Os outros 3 ATENÇÃO já são conhecidos:**
  - **A2:** as falhas de 09/10 e 10/10 (lacuna do ERA5, já corrigida) e a do RONI (null geometry, já corrigida).
  - **E3-rsup e E3-rsub:** fator SMAP/ERA5 acima de 5 na matriz de solo do histórico V1.0. É limitado a 5 na leitura, como já registrado.
- **Testes:** `fumaca_08_01` e `teste_08` OK.
- **Auditoria 08 de 22/10, 8h07 (com a seção F corrigida):** 44 OK, 22 INFO e 5 ATENÇÃO. F1, F2, F3 e F5 OK. Mudanças nos arquivos:
  - **F4 deixou de ser ATENÇÃO e virou INFO.** A radiação do GFS é média do bloco de 6 h, mas o motor (desde a V1.4) e a matriz V2.1 já usam a média dos blocos de 6 h. A ação sugerida antiga ("ajustar o motor e a matriz") estava desatualizada.
  - **Rótulos do K10:** os casos abaixo do recorde passaram a ser classificados em relação ao maior valor do histórico no pixel. Antes saíam como "indefinido".
- **K10 de 22/10, 8h15 (resultado):**
  - **26/10, Casa Nova-BA, previsão do 6º dia:** GFS bruto 35,41 °C e gravado 45,24 °C.
    - O deslocamento da média dá +4,71 °C (m_sicsb 34,89 contra m_gfs 30,18).
    - A razão dos desvios dá +5,12 °C (s_sicsb 1,93 / s_gfs 0,97 = 1,98, quase no teto de 2,0).
    - O valor gravado passa em 4,5 °C o maior valor do histórico no pixel (40,76 °C).
    - **Diagnóstico (b): artefato da escala de variância na faixa L6a10**, onde o GFS tem variância diária amortecida.
  - **27/10, Boa Vista-RR, previsão do 7º dia:** GFS bruto 40,55 °C e gravado 44,19 °C. Fica 1,6 °C acima do histórico do pixel (42,56 °C).
  - **05/11, Araçuaí-MG, previsão do 16º dia:** GFS bruto 40,45 °C e gravado 44,31 °C, dentro do histórico do pixel (44,77 °C, o recorde do INMET de 2023). Plausível.
  - **Decisão pendente:** mudança da razão dos desvios nos prazos longos. Validar antes (K11) e só depois mexer no motor.

## 11. Validação K11 (22/10/2026): razão dos desvios da Tmax e da Tmin nos prazos longos

- **Script:** `validacoes/K11_validacao_razao_desvios_prazos_longos.py`. É só leitura e não trava a sessão. Reaproveita os dados brutos da K9A no Drive (`K9A_dados_brutos.parquet`); sem eles, baixa só o GFS v16.
- **Métodos comparados:**
  - **M0:** o motor atual, com a razão entre 0,5 e 2 em todos os prazos.
  - **M1 (proposta):** razão entre 0,5 e 1 nos prazos de 6 dias em diante.
  - **M2:** razão entre 0,5 e 1,5 em todos os prazos.
  - **M3:** razão entre 0,5 e 1 em todos os prazos (informação).
  - **M4:** o M0 com teto físico, no máximo ou mínimo do ponto no mês ± 1 °C (informação).
  - **Aditiva:** referência.
- **Regra fixada antes de rodar:** vale para a Tmax e para a Tmin, cada uma por si, nos prazos 8 e 13 (6 dias em diante). O M1 só entra se cumprir os quatro critérios:
  1. no teste A (2025), o limite superior do IC 95 % da diferença de MAE fica abaixo de +0,5 % do MAE do M0;
  2. a taxa além do limite físico do ponto não aumenta, nem as previsões acima de 44,8 °C;
  3. a frequência do evento extremo (Tmax > 35 °C; Tmin ≤ 2 °C) não se afasta da observada mais que 0,5 ponto percentual além do M0;
  4. no teste B, em todos os anos de 2021 a 2025, o MAE fica no máximo 0,5 % acima do M0.
  - Se o M1 falhar, o M2 passa pela mesma regra em todos os prazos. Se nada passar, o M0 fica.
- **Evidência prévia da K9A:** no prazo 13, a Tmin pela variância previa geada em 0,154 % dos ponto-dias, contra 0,108 % observados. Pela aditiva, eram 0,120 %.
- **Teste offline:** `testes/teste_k11.py`, com dados sintéticos de variância amortecida. OK.
- **Roteiro:** etapa 8b nova.

## 12. Resultado da K11 (22/10/2026, 8h30) e mudança no motor

- **Execução:** reaproveitou os dados da K9A no Drive (2.862.000 pares), sem baixar nada.
- **Razão s_BR-DWGD/s_GFS antes de limitar:**
  - **Tmax:** mediana de 0,69 a 0,75 conforme o prazo. Passa de 1 em 17 % dos casos no prazo 1 e em 7 % no prazo 13.
  - **Tmin:** mediana de 1,02 a 1,08. Passa de 1 em 57 % a 64 % dos casos e de 2 em até 1,5 %.
- **Resultado pela regra fixada antes de rodar:** o M1 passou na Tmax e na Tmin, nos 4 critérios.

| Variável (prazos 8 e 13) | MAE M0 → M1 (IC 95 %) | Além do limite físico | Evento extremo, prev → prev (obs) | Teste B |
|---|---|---|---|---|
| Tmax | 1,891 → 1,879 (−0,6 %; −0,013 a −0,009) | 0,171 % → 0,163 % | > 35 °C: 12,20 % → 12,16 % (11,80 %) | 5 de 5 anos |
| Tmin | 1,272 → 1,205 (−5,3 %; −0,072 a −0,063) | 0,303 % → 0,151 % | geada ≤ 2 °C: 0,131 % → 0,088 % (0,108 %) | 5 de 5 anos |

- **GFS v15 (informação):** o M1 também ganha nos 3 anos.
- **Informação, fora da regra:**
  - **M3** (teto 1 em todos os prazos) erra ainda menos no 1º dia. Mas leva a geada prevista no 1º dia de 0,102 % para 0,078 % (obs. 0,108 %). Por isso os prazos 1 a 5 ficam como estão. Se quiser, isso pode ir para uma validação própria, com a regra fixada antes.
  - **M4** (teto físico) quase zera as previsões além do limite, mas cortaria um recorde verdadeiro. Não adotado.
  - Nos 300 pontos da amostra, nenhum caso passou de 44,8 °C, nem com o M0. O caso de Casa Nova não está na amostra; a mudança o corrige por construção: 45,30 → 40,12 °C no `teste_05`.
- **Mudança no 05a e no 05b:**
  - Constantes `RAZAO_DESVIO_MAX_LONGO = 1.0` e `FAIXAS_LONGAS = ('L6a10', 'L11a15')`.
  - `razao_desvios`, `calib_variancia` e a nova `teto_razao_temp(faixa)` recebem o teto.
  - A Tmax e a Tmin usam o teto da faixa. A UR e a radiação não mudam.
  - Propriedade nova `teto_razao_temp_gfs` nos dias GFS, lida por `info_de_propriedades` e pelo inventário (`repeat(7)`).
  - `precisa_refazer_gfs` recebe a faixa e refaz o dia gravado com outro teto. Dia sem a propriedade conta como 2.0, então os dias de prazo 6+ são refeitos na próxima execução.
  - Linha nova no início: `Teto da razão dos desvios da Tmax/Tmin: ...`.
- **08:**
  - `teto_razao_esperado()` e o critério `teto_razao_K11` na D14.
  - O inventário de 2026 lê `teto_razao_temp_gfs`, com padrão 2.0.
- **K10:** usa o teto gravado no dia para recalcular.
- **Testes:**
  - `teste_05`: 1.739 verificações, 15 de 15. Teste novo `teste_teto_razao_k11`, com o caso de Casa Nova.
  - `teste_08`: casos K11.
  - `fumaca_08_01` e os demais: OK.

## 13. Execução real com a K11 e consolidação final (22/10/2026, 9h30)

- **05a (8h39) e 05b (8h42):** o código rodado é idêntico ao do pacote.
  - A linha do teto da K11 apareceu; rodada de referência 2026-10-22 00Z.
  - O 05b gravou 16 dias (22/10 a 06/11). De 09/10 a 21/10, os dias continuam com a rodada do próprio dia (prazo 1). `PROTEGIDOS: nenhum`.
- **Auditoria 08 (8h59):** 45 ✅, 23 ℹ️, 3 ⚠️ e nenhum ❌.
  - D14 `teto_razao_K11` ✅ nos 29 dias GFS (2.0 nos prazos 1 a 5; 1.0 do 6 em diante).
  - J5a ✅: maior Tmax nacional de 44,08 °C em 26/10 (prazo 5), abaixo do recorde de 44,8 °C. Antes da K11 eram 45,24 °C.
  - J5b ✅: emenda ERA5 → GFS de −0,25 °C.
  - F4 passou de ⚠️ para ℹ️, como corrigido na seção 10.
  - ⚠️ restantes:
    - A2: 3 falhas antigas de 21/10, de antes das correções das seções 7 e 8; saem da janela de 30 dias por volta de 20/11.
    - E3-rsub e E3-rsup: matriz de solo, sem mudança; limitação registrada.
- **Consolidação (sem mudança de cálculo):**
  - Novo `00_LEIA_PRIMEIRO_INVENTARIO.md`: o que é atual, as calibrações (BR-DWGD × ERA5, SMAP × ERA5, GFS V1 e V2.1, RONI antigo e CPC), o que aposentar no computador, no Code Editor, no Colab e nos assets, e a rotina.
  - Linha 3 do `06_painel_sab_2026_10_4.js` e linha 2 do `08_auditoria_completa_SAB.py`: marca "REVISÃO FINAL DE 22/10/2026" (só comentário), para reconhecer a versão atual.
  - `00_ROTEIRO_FINAL.md`:
    - K10 e K11 na tabela inicial;
    - resultado da execução real na etapa 8b;
    - rotina de 15/11 apontando para a J5 da auditoria das 8h59;
    - nome do zip;
    - remissão ao inventário.
  - Zip renomeado para `SAB_FINAL_v4_1_COMPLETO_2026-10-22.zip`; o `SAB_FINAL_v4_1_K11_2026-10-22.zip` fica obsoleto.

## 14. Painel: download de áreas grandes, em SIMULAÇÃO (22/10/2026, 14h30). O painel 06 NÃO mudou

- **Problema relatado:** extração do Paraná inteiro, 1 mês, resolução diária. O link do CSV foi gerado, mas ao abrir voltou `{"error": {"code": 503, "message": "The service is currently unavailable."}}`.
- **Auditoria do código:**
  - o CSV é calculado na hora do clique (`getDownloadURL`);
  - um mês do Paraná dá cerca de 2.000 pontos × 31 dias = 62 mil linhas, com cerca de 21 números por linha convertidos em texto com vírgula no servidor (`formatarExportacaoClima`);
  - cada link refaz também a grade inteira (amostragem do estado, cruzamento com o contorno, ordenação e `toList`);
  - não há erro de lógica: é carga demais para um pedido de download.
- **Pedidos do usuário:** simular antes de alterar; e os números do CSV deixam de ser texto com vírgula (passam a número, com ponto).
- **Simulação `validacoes/K12_simulacao_download_estadual.py` (nova, só leitura):** monta o mesmo CSV do painel e baixa cada link no Colab, medindo resposta, tempo, tamanho e linhas:
  - A1, como hoje: texto com vírgula, grade refeita, 1 link;
  - A2, números com ponto, grade refeita, 1 link;
  - A3, números com ponto, grade pronta, 1 link;
  - B, números com ponto, grade pronta, em partes de 15.000 linhas (e de 8.000, se a de 15.000 falhar);
  - conferências: colunas na ordem do painel, todos os pontos e dias sem repetir, mesmos números do formato atual (diferença só de arredondamento) e mesmas células vazias.
- **1ª execução da K12 (14h31, Paraná, 2025, 1.889 pontos × 365 dias = 689.485 linhas):**
  - um link de 60.000 linhas (números com ponto, grade pronta) abriu em 115 s (13,4 MB);
  - no mesmo bloco de 15.000 linhas, texto com vírgula 35,7 s × número com ponto 43,0 s: a vírgula não é o gargalo; os valores batem (só arredondamento) e as células vazias são as mesmas;
  - ano em 12 partes, 3 links ao mesmo tempo: 9 partes abriram (de 112 a 267 s cada) e 13 pedidos voltaram 429 ("Too many concurrent aggregations") em 1 a 6 s, ou seja, fila cheia, não tamanho. A v1 tratava o 429 como parte grande e dividia; por isso faltaram 3 partes.
- **K12 v2 (15h):** um link por vez; no 429 espera 1 minuto e repete o mesmo link; nova etapa 1b repete o pedido do painel que deu 503 (out/2026, 1 link, texto, grade refeita) mudando uma coisa por vez.
- **Teste offline:** `testes/teste_k12.py` (funções de partes, leitura do CSV e comparação).
- **Proposta para depois da simulação:** números com ponto em vez de texto com vírgula, grade calculada uma vez e, se a K12 mostrar que precisa, partes por bloco de pontos (`..._parte01de05`). O tamanho da parte sai da K12.

## 15. Resultado da K12 v2 (22/10/2026, 15h01) e mudança no painel 06 (16h)

- **K12 v2, Paraná, 2025, CSV diário (1.889 pontos × 365 dias = 689.485 linhas), um link por vez:**
  - 1º bloco de 60.000 linhas: abriu em 106 s;
  - o pedido que deu 503 no painel (out/2026, 1 link de 58.559 linhas, texto com vírgula, grade refeita) **abriu** em 120 s; com a grade pronta, em 178 s; com grade pronta e números, em 230 s. Logo, o 503 foi carga momentânea do Earth Engine (por exemplo, as camadas do mapa sendo calculadas ou outro link aberto ao mesmo tempo), não erro do código;
  - texto com vírgula × número com ponto (mesmo bloco de 15.000 linhas): 31,5 s × 60,7 s, 4,05 MB × 3,37 MB. A vírgula não pesa no tempo; os valores são os mesmos (só arredondamento) e as células vazias também;
  - ano inteiro em 12 links de até 60.000 linhas: **12 de 12 abriram** (de 59 a 284 s; média 157 s; 155 MB no total), sem 429;
  - conferência do ano: colunas na ordem do painel, 689.485 linhas, nenhum par (ponto, dia) repetido, os 1.889 pontos e os 365 dias presentes;
  - tempo total da simulação: 44 min.
- **Mudança no 06 (o que a K12 validou; nenhum valor muda além do formato):**
  - **números com ponto decimal** nos CSV de clima (antes texto com vírgula), arredondados nas mesmas casas de antes (5 nas coordenadas, 3 na umidade do solo, 2 no resto; RONI_Trimestre_C com 1). Ausência continua vazia. O dicionário ganhou a linha "(formato dos numeros)", com o jeito de abrir no Excel em português;
  - `CFG.maxLinhasPorLink = 60000`: quando pontos × dias do ano passam disso, o ano sai em vários arquivos **por período** (`planejarPeriodos`): meses inteiros quando cabem 31 dias (Paraná: 1 mês por arquivo, 12 por ano, igual ao pedido de out/2026 que a K12 validou); senão, blocos de dias. Nome com o período: `Diaria_Parana_2025_01-01_a_01-31`. Mensal: blocos de meses (`Mensal_..._meses_01_a_06`), só acima de 60.000 linhas;
  - o número de pontos de cada local vem do servidor numa chamada só (`aggregate_histogram`), no lugar da lista de nomes;
  - aviso no painel de downloads, quando algum arquivo é dividido: baixar um link de cada vez; se der 429 ou 503, esperar 1 minuto e clicar de novo;
  - áreas pequenas não mudam de nome nem de número de arquivos (ex.: Pato Branco, ano inteiro: 1 arquivo).
- **Não adotado:** a grade calculada uma vez no navegador (versão de 14h). A K12 não mostrou ganho (120 s com a grade refeita × 178 s com ela pronta).
- **Testes:** `testes/teste_06_partes.js` (novo, 33 verificações: períodos do Paraná iguais aos da K12, ano bissexto, período no meio do mês, Minas Gerais, 1 dia por arquivo no extremo, mensal, nomes, código e formatação numérica com ee falso). `teste_06_colunas`, `teste_06_enso` e `teste_04` continuam passando.

## 16. Pedido do usuário: 1 arquivo por ano, como antes (22/10/2026, 17h)

- **Pedido:** cada ano num link só, independentemente da data inicial (ex.: de fevereiro de 2025 a dezembro de 2026 = 1 arquivo de 2025 e 1 de 2026), como era antes.
- **Painel 06:** volta à divisão de antes, 1 arquivo por ano (diário e mensal). A divisão por período da seção 15 saiu (guardada fora do pacote). **Fica só a troca validada pela K12:** números com ponto decimal (mesmas casas; ausência vazia; RONI_Trimestre_C com 1 casa) e a linha "(formato dos numeros)" no dicionário.
- **Testes:** `testes/teste_06_partes.js` substituído por `testes/teste_06_numeros.js` (código com 1 arquivo por ano, sem troca de ponto por vírgula, formatação numérica com ee falso).
- **Ponto resolvido (18h):** o usuário baixou o Paraná inteiro de 2025 num link só com o painel antigo (2026.10.2): `Diaria_Parana_2025.csv`, 47,6 MB. A comparação do código mostrou que o caminho do download é o mesmo na 2026.10.4 (mesmo `getDownloadURL`, um link por ano, mesma montagem da grade); a 2026.10.4 só acrescenta 3 colunas e a máscara de qualidade. Logo, o limite de 60.000 linhas da K12 era só o maior tamanho testado, não um limite do Earth Engine, e o 503 de outubro foi momentâneo (a K12 v2 abriu o mesmo pedido). A simulação K12c (link único) ficou desnecessária e saiu do pacote.

## 17. 503 no ano inteiro do Paraná com o painel das 17h (22/10/2026, 18h30)

- **Relato:** com o painel das 17h, o CSV diário do Paraná de 2025 (1 link) voltou `503 "Please try again."`; com o painel antigo (2026.10.2), o mesmo pedido baixou (`Diaria_Parana_2025.csv`, 47,6 MB).
- **Auditoria (comparação do código das duas versões):** o caminho do download é o mesmo. O que muda é o trabalho feito em CADA LINHA do CSV, que num ano do Paraná se repete cerca de 689 mil vezes:
  - 2026.10.2: 21 números × (format + troca do ponto pela vírgula) + 2 consultas à lista de propriedades;
  - 2026.10.4 das 17h: 21 números × (multiplicar + arredondar + dividir) + 5 consultas à lista de propriedades (as 3 colunas novas também). A K12 já tinha medido o arredondamento numérico mais lento que o texto com vírgula no mesmo bloco (43 × 36 s e 61 × 32 s);
  - um pedido desse tamanho fica perto do limite de tempo do serviço de download; com mais trabalho por linha, passa dele e o Earth Engine responde 503.
- **Mudança (só em `formatarExportacaoClima` e em `propsEnsoDaImagem`):**
  - números com ponto pelo `format` sozinho ("18.40"): 1 operação por valor, menos que as 2 da 2026.10.2;
  - `Tipo_Dado`, `Versao_Algoritmo` e as colunas novas lidas com `fDict.get(coluna, padrão)`: mesmo resultado, sem consultar a lista de propriedades a cada linha;
  - `RONI_Trimestre_C` com `format('%.1f')`.
  - Resultado: cada linha faz menos operações que na 2026.10.2. Valores e colunas iguais aos das 17h (mesmas casas decimais; vazio continua vazio).
- **Testes:** `teste_06_numeros.js` atualizado; `teste_06_colunas`, `teste_06_enso` e `teste_04` passam.
- **Confirmado no Earth Engine (22/10, 19h):** com esta versão, o CSV diário do Paraná de 2025 saiu num link só.
