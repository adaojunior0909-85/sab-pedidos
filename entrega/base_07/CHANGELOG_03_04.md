# CHANGELOG 03 e 04 — pacote SAB v4 (20/10/2026)

> **Revisão posterior (20/10/2026, tarde):** as auditorias independentes A e B pediram correções neste escopo. Elas estão em `CHANGELOG_REVISAO_AB.md`, que prevalece em caso de divergência.

Escopo: `03_matriz_gfs_v2.py` → **`03_matriz_gfs_v2_1.py`** (renomeado com `mv`; matriz **V2.1**) e `04_conferencia_matriz_gfs.js` (mesmo nome).
Base: `/home/claude/sab/v3_zip/`. Contrato: `SPEC_V4.md`. Referências: `revisao_03_04_matriz_gfs.md` (M03-xx, M04-xx) e `revisao_02_07_08.md` (M08-03, M08-10).
Todo trecho novo ou alterado leva `# [V4 ...]` / `// [V4 ...]`. O que não está listado aqui ficou byte a byte igual: Initialize, `extrair_sicsb`, `velocidade_u2`, `horas_da_faixa`, a máscara GAUL e o `Export.image.toAsset`, salvo a região. As contas do GFS são as mesmas, mas passam por `composto_seguro` (item M03-11 abaixo, acrescentado na revisão).

## Validação feita

| Verificação | Resultado |
|---|---|
| `python3 -m py_compile` e `python3 -m pyflakes` no 03 (Python 3.13 e 3.11, para a gramática de f-string do Colab) | OK, sem avisos |
| `node --check` no 04 | OK; sem `getInfo` e sem sintaxe ES6 |
| `testes/teste_03.py` (Python puro; lê as funções do próprio 03 com `ast`, sem cópia) | **633 verificações OK** |
| `testes/teste_04.js` (Node; roda o 04 inteiro com um `ee` simulado e responde cada `evaluate`) | **35 verificações OK** |
| Teste de mutação do `teste_03` (5 defeitos plantados numa cópia do 03) | os 5 foram detectados |
| `diff -u` completo do 03 e do 04 contra o v3, relido | ok |

O que o `teste_03.py` cobre:
- a data da rodada por prazo (rodada 00Z de D−(L−1)) e o corte pela criação;
- as horas esperadas (24 nos prazos 1 a 5, 8 nos prazos 6 a 15) e os blocos de chuva;
- a regra de completude, com hora faltando, imagem duplicada e estrutura antiga;
- coerência com o motor, lendo o `05a_motor_sab_v1_5_SIMULACAO.py` sem executá-lo:
  - `contagem_esperada` e `faixa_prazo` nos 15 prazos;
  - o 16º dia cai em L11a15;
  - `VERSAO_MATRIZ_GFS == 'V2.1'`;
  - `BANDAS_MEDIA_GFS` igual às 48 médias do 03, na mesma ordem;
- as 100 bandas e a ordem delas;
- as propriedades do contrato (o dicionário `props` é executado a partir do código);
- os máximos por mês, contra uma enumeração independente por rodada;
- o limiar de 85%;
- a decisão de reexecução.

## A. Script 03 → `03_matriz_gfs_v2_1.py`

### [V4 D1] Só GFS v16
- **Linhas:** 8-11, 17, 73-78 (`VERSAO_MATRIZ`, `MODELO_GFS`, `INICIO_RODADAS='2021-03-23'`, `FIM_DIAS='2025-12-31'`, `DATA_FIM='2026-01-01'`), 327-329.
- **Mudou:**
  - Saíram `DATA_INICIO='2017-02-08'` e `INICIO_FAIXA` (2017-02-08 / 2019-06-13).
  - Entram só rodadas 00Z criadas a partir de 2021-03-23, e o dia previsto vai até 2025-12-31.
- **Por quê:** decisão do usuário (SPEC D1). O v16 entrou em 22/03/2021 às 12 UTC. Pela estrutura de saídas não dá para separar o v15 do v16 (o F2 mostra 209 imagens em 2021-03-21 e em 2021-03-23), então a data é a única trava.
- **Verificar:** a 1ª linha do 🚀 cita "só GFS v16, rodadas 00Z de 2021-03-23 a 2025-12-31"; o 04 confere `inicio_rodadas`.
- **A CONFIRMAR:** se alguma versão **v17** entrou em operação antes de 31/12/2025. As atualizações v16.x não mudam a estrutura de saídas.

### [V4 M03-04] Corte pela data de criação da rodada
- **Linhas:** 108-111 (`inicio_dia_previsto`), 150 (`INICIO_RODADAS_MS`), 219 e 243 (`gfs_faixa` devolve `criacao`), 254 (`valido = completa.And(criacao.gte(INICIO_RODADAS_MS))`), 274 (`filterDate(inicio_dia_previsto(L), DATA_FIM)`).
- **Mudou:**
  - O prazo L só usa dias D ≥ 2021-03-23 + (L−1). A coleção do BR-DWGD já sai filtrada assim, para não montar pares impossíveis.
  - A condição `criacao ≥ 2021-03-23` também entra em `valido`, de forma explícita.
- **Por quê:** M03-04. A V2 comparava o dia previsto, e não a criação da rodada.
- **Verificar:** as contagens nunca passam do máximo da tabela (seção D). No 04, `n_pares ≤ máximo` dá ❌ se for violado.

### [V4 M03-03] Todos os dias de cada faixa
- **Linhas:** 80-82 (`FAIXAS = [('L1',[1]), ('L2a5',[2..5]), ('L6a10',[6..10]), ('L11a15',[11..15])]`), 101-105 (`horas_chuva`), 144-147 (`N_ESPERADO` para os prazos 1 a 15), 222-230 (`gfs_faixa`), 246-260 (`par_faixa`), 263-275 (`funcao_par`, `pares_da_faixa`), 285-295.
- **Mudou:**
  - Para cada prazo L, o par é o dia D do BR-DWGD com a rodada 00Z de D−(L−1), nas horas (24(L−1), 24L].
  - Os prazos da faixa são unidos com `merge` numa só coleção, com os mesmos nomes de banda da V2.
  - Cada faixa é reduzida separadamente, e as quatro são concatenadas na ordem das bandas da V2.
  - Mantidos sem mudança:
    - a completude (`size == N_ESPERADO[L]` e 4 blocos de chuva);
    - o bilinear por imagem;
    - a chuva como soma dos 4 blocos de 6 h;
    - a radiação como média dos 4 blocos × 0,0864.
  - Mudanças de custo, sem efeito no resultado:
    - a completude é contada na coleção sem o `.map(resample)`;
    - os blocos de chuva são filtrados **antes** do `.map(resample)`. Assim o 03 não depende de o `resample()` preservar `forecast_hours`.
- **Por quê:** M03-03. O motor aplica a matriz da faixa a todos os dias 2–5, 6–10 e 11–16, mas a V2 só tinha os dias 3, 8 e 13.
- **Verificar:** a linha `Mês MM: dias válidos por faixa {...}` deve ficar perto da tabela da seção D. O 04 mostra `n_{faixa}` mediano por pixel = `n_pares`.
- **Observação:** o 03 descarta um par (rodada × prazo) com imagem duplicada (`size ≠ N`). O motor V1.5 deduplica (`distinct('forecast_hours')`, M05-11). Os valores são os mesmos; só a amostra pode ser 1 ou 2 pares menor.

### [V4 M03-08] Máscara diária do BR-DWGD no GFS
- **Linhas:** 199-205 (`preparar_br`: as 6 bandas do BR-DWGD com a mesma pegada, pelo `mask().reduce(min)`), 253 (`img_gfs.updateMask(br.select('pr__sicsb_fx').mask())`), 279-283.
- **Mudou:**
  - O BR-DWGD do mês é filtrado e convertido **uma vez** (`br_mes = ....map(preparar_br)`) e reaproveitado pelos 15 prazos. Cada prazo só acrescenta um `filterDate`.
  - O GFS de cada par herda a máscara do dia, e as 12 bandas do par ficam com a mesma pegada.
- **Por quê:** M03-08. A V2 tinha as bandas sicsb em BR∩GAUL e as gfs no GAUL inteiro.
- **Verificar:** 04, bloco 2: "N pixels em todas as 100 bandas" (✅).
- **Efeito no motor:** nos ~1.100 pixels de borda sem BR-DWGD (classe C da auditoria J1), as bandas gfs passam a ficar mascaradas, como as sicsb. O motor já preenche as duas com `expandir_borda`, de modo que alvo e modelo passam a vir da mesma vizinhança.

### [V4 M03-06] Redutor combinado e bandas `n_`
- **Linhas:** 153 (`NOMES_N`), 155-158 (`REDUTOR = mean.combine(stdDev, sharedInputs=True).combine(count, sharedInputs=True)`), 288-301.
- **Mudou:**
  - Uma só redução por faixa. Antes eram duas: `pares.mean()` e `pares.reduce(stdDev)`.
  - `n_{fx}` = `Tmax__gfs_{fx}_count`, mascarado onde é 0 (mesma pegada das médias), em `toFloat` (Float32 com valores inteiros; mudado de `toInt16` na revisão do coordenador).
  - Bandas: 48 `_m_` + 48 `_s_`, na mesma ordem da V2, e depois `n_L1`, `n_L2a5`, `n_L6a10`, `n_L11a15`. Total de **100**.
- **Por quê:** M03-06 e o contrato SPEC.
- **Verificar:** 04, bloco 1 ("100 bandas na ordem do contrato") e bloco 2 (n mínimo e mediano).
- **Resolvido na revisão:** as bandas `n_` passaram a Float32, então todas as 100 bandas têm o mesmo tipo e não há risco de "compatible data types" na exportação.

### [V4 M03-05] Metadados e reexecução segura
- **Linhas:**
  - 86 (`GERADO_EM`, ISO UTC);
  - 134-141 (`decisao_mes`, pura);
  - 168-175 (`versoes_existentes`: `listAssets` + `ee.Image(...).get('versao_matriz').getInfo()`);
  - 295 (`n_pares[fx] = pares.aggregate_sum('valido')`);
  - 303-319 (`props`);
  - 331-347 (plano e conflitos).
- **Propriedades gravadas:**
  - `versao_matriz='V2.1'`, `modelo_gfs='GFS v16'`, `inicio_rodadas='2021-03-23'`, `fim_dias='2025-12-31'`, `mes_referencia` (int);
  - `leads_L1` a `leads_L11a15`;
  - `n_pares_L1` a `n_pares_L11a15`, calculados **no servidor, dentro da tarefa** (é a mesma expressão que o 03 imprime);
  - `metodo_pr='soma_blocos_6h'`, `metodo_rs='media_blocos_6h'`;
  - `janela='(00Z,24Z] UTC do dia previsto; rodada 00Z de D-(L-1)'`, `gerado_em`;
  - mantidas, com o texto atualizado: `periodo` e `faixas`.
- **Antes de enviar qualquer tarefa,** o script monta o plano dos 12 meses:
  - asset existente em V2.1: ⏩ pula;
  - asset sem versão ou de outra versão: ❌ por mês, com a instrução de "apague À MÃO (aba Assets do Code Editor ou `ee.data.deleteAsset('<caminho>')`) e rode de novo", e `RuntimeError`. **Nenhuma tarefa é enviada.**
- **Por quê:** M03-05. Uma matriz deixada por um 03 antigo seria aceita em silêncio.
- **Verificar:** rodar o 03 duas vezes seguidas:
  - na 2ª vez, todos os meses aparecem como ⏳ (tarefa na fila) ou ⏩ (já em V2.1);
  - com um asset V2 antigo, aparece ❌ e nada é enviado.

### [V4 M03-09] Tarefas na fila e erros visíveis
- **Linhas:** 85 (`ESTADOS_ATIVOS`, igual ao motor), 160-164, 178-180, 356-362, 389-394.
- **Mudou:**
  - Pula o mês cuja `GERAR_MATRIZ_GFS_V2_MM` esteja READY ou RUNNING (o mesmo valem SUBMITTED e PENDING). A mensagem avisa que uma tarefa de versão anterior deve ser cancelada.
  - A coleção só é criada se `getAsset` falhar, e um erro na criação para o script. O `except: pass` saiu.
  - Uma falha em `task.start()` imprime ❌ e para. Rodar de novo é seguro.
- **Por quê:** M03-09. O roteiro v3 proibia rodar o 03 de novo por risco de duplicar tarefas.
- **Verificar:** rodar com tarefas na fila mostra ⏳ e não duplica nada.

### [V4 M03-10] Contagem contra o máximo e região leve
- **Linhas:** 114-131 (`maximos_por_mes`, `abaixo_do_limiar`, testadas), 349, 364-381, 385 (`region=poligonoBrasil.bounds()`).
- **Mudou:**
  - A contagem passa a ser impressa contra o máximo possível do mês, com ⚠️ abaixo de 85%. Antes o limiar era fixo em `n < 60`.
  - Se o `getInfo` falhar, o erro é impresso e a exportação segue, gravando `n_pares_*` no asset.
  - A exportação usa o retângulo do Brasil, com o `crsTransform` nativo. A imagem já leva a máscara GAUL.
- **Mensagens (as do roteiro, iguais):**
  - `   Mês MM: dias válidos por faixa {'L1': n, 'L2a5': n, 'L6a10': n, 'L11a15': n}`, seguida de `(pares dia x prazo; máximo possível {...}; L1 x%, ...)`;
  - `✔️ Tarefa enviada: matriz GFS V2, mês MM.`;
  - `🎉 Tarefas enviadas: N (MM, ...)`.
- **Atenção:** os números agora são **pares dia×prazo**, não dias. A tabela do roteiro v3 (230 a 279...) fica inválida; use a da seção D.

### [V4 M03-14] Cabeçalho e comentários
- **Linhas:** 1-50, 215-219.
- **Corrigido:**
  - "média e desvio usadas pelo motor": o motor usa só as `_m_`;
  - as faixas passam a ser todos os prazos;
  - a explicação do erro do F5: o teste contava o f000, então 08/02/2017 não era o início real; há 384 h desde 24/07/2016, e o passo em ago-dez/2016 fica A CONFIRMAR;
  - saiu "Sem 2015-2016";
  - a docstring de Tmax/Tmin agora diz 24 saídas horárias nos dias 1 a 5 e 8 de 3 em 3 h depois;
  - o motor citado passa a ser o V1.5;
  - o 16º dia usa L11a15, por extrapolação.

## B. Script 04 → `04_conferencia_matriz_gfs.js` (reescrito, só leitura)

| Item | Linhas | O que confere | Critério |
|---|---|---|---|
| M04-04 | 172-228 | 12 matrizes; 100 bandas na ordem do contrato; propriedades do contrato (valores exatos, `mes_referencia`, `gerado_em`); `n_pares_*` contra `MAXIMO_PARES` (57-62) | ❌ ausente, banda faltando ou propriedade errada; ❌ `n_pares` ≤ 0 ou acima do máximo; ⚠️ abaixo de 85% |
| M04-04 / M03-08 | 298-318 | `count` nas 100 bandas (grade nativa); `n_{fx}` mínimo (`reduceRegion`) e mediano (amostra) | ❌ contagens diferentes; ✅ se mediana = `n_pares` e mínimo ≥ 90% |
| M04-01 | 232-291 (montagem), 320-352 (avaliação) | por mês e faixa: mediana [p5; p95] de GFS−BR para Tmax, Tmin e RH; fator BR/max(GFS, 1e-3) para pr, u2 e Rs (mediana, % > 5 e % < 0,2 exatos em todos os pixels); Σchuva GFS / Σchuva BR | ❌ \|viés Tmax/Tmin\| > 5 °C ou Σchuva fora de 0,5–2 (critérios do roteiro v3); ⚠️ nos limiares heurísticos de `LIM` (40-53) |
| M04-02 | 273-281, 354-365 | razão de gradientes do E4 (o mesmo `gradient()`/`hypot` e a mesma caixa do 08) por faixa, nos meses 01 e 07 | ✅ ≥ 0,30; ⚠️ entre 0,230 e 0,30; ❌ ≤ 0,230 (V1) |
| M04-03 | 368-414 | (Rs_m_gfs_L1/Rs_m_sicsb_L1 da V2.1) ÷ (a mesma razão da V1), somas nos pixels comuns, nos 12 meses. As bandas da V1 são descobertas pelo `bandNames` (`Rs_m_gfs` com `Rs_m_sicsb`, `Rs_m_sab`, `Rs_m_br` ou outra `Rs_m_*`); sem a V1, sai ⚠️ e o resto segue | informativo: ✅ entre 0,85 e 1,0; ⚠️ fora |
| M04-05 | 31-37, 121-128, 257-264 | todas as reduções em `EPSG:4326` + `crsTransform` nativo. Percentis exatos: amostra de 5.000 pixels na grade nativa (`sample` com `ee.Projection(CRS, TRANSFORM)`, `seed` 42) e `ee.Reducer.percentile({maxRaw: 20000})`, que guarda os valores brutos, sem histograma | — |

- **Execução:**
  - só `evaluate`, numa fila com no máximo 4 pedidos ao mesmo tempo, para evitar "Too many concurrent aggregations";
  - um erro de interpretação vira ❌ e a fila continua;
  - o relatório sai uma só vez no fim: 5 blocos e um `RESUMO: N ✅ | N ⚠️ | N ❌`, seguido da lista dos itens com ⚠️ ou ❌.
- **Mapa:** as camadas da Serra do Mar são as mesmas de antes (linhas 463-472).
- **Saída esperada:** com uma matriz sem defeitos, o `teste_04.js` produz `RESUMO: 165 ✅ | 0 ⚠️ | 0 ❌`.
- **A CONFIRMAR:**
  - os limiares heurísticos de `LIM` (cauda de T, viés de UR, mediana dos fatores, % de fatores extremos), a recalibrar na 1ª execução real. Junho a setembro podem dar ⚠️ de chuva por causa da seca (J4: na V1, o fator de chuva de julho tem p95 de 13,3);
  - o tempo de execução, estimado em 1 a 3 min.

## C. Custo (EECU) em relação à V2 atual

O custo é dominado pela leitura das imagens GFS com bilinear. O BR-DWGD é uma imagem de 6 bandas, sem reprojeção.

| | V2 (v3_zip) | V2.1 |
|---|---|---|
| Período (dia previsto) | 3.249 dias (8,9 anos); L11a15 com 2.394 | 1.745 dias (4,78 anos) |
| Pares por dia | 3,74 | 14,94 (×4,0) |
| Imagens GFS lidas por dia | 61,9 | 199,4 (×3,2) |
| Total de imagens GFS lidas | 201.096 | 348.000 |
| Total de pares (leituras do BR-DWGD) | 12.141 | 26.070 |

- **Estimativa:**
  - **cerca de 1,7 vez o EECU da V2**, se a V2 fizesse uma só passada sobre o GFS;
  - **cerca de 0,9 vez**, se as duas reduções da V2 (`mean()` e `reduce(stdDev)`) relessem o GFS cada uma (A CONFIRMAR, M03-06). A V2.1 faz uma só passada por faixa.
  - Faixa provável: **0,9 a 1,7 vez a V2**. Não há EECU absoluto para comparar, porque a V2 nunca foi executada (E5).
- **O "2,6 vezes mais pares por dia" da tarefa:** pela minha conta são ×4,0 em pares e ×3,2 em imagens GFS, que é o que pesa. Com ~0,54 do período, o total fica ×1,7.
- **Opções baratas avaliadas:**
  - `tileScale` e `bestEffort`: **não se aplicam**. São parâmetros de `reduceRegion`; `ImageCollection.reduce` e `Export.image.toAsset` não os têm. O `bestEffort` mudaria a escala, e a resolução não pode mudar. Nada aplicado.
  - Aplicadas, sem mudar o resultado:
    - redutor combinado (uma passada, M03-06);
    - completude por metadados, sem o `.map(resample)`;
    - chuva filtrada antes do `resample`;
    - BR-DWGD convertido uma vez por mês e reaproveitado pelos 15 prazos. Se o Earth Engine reaproveita a tile entre prazos fica A CONFIRMAR, mas essa parte é pequena;
    - exportação pelo retângulo, em vez do polígono.
  - Não aplicadas, porque mudariam o contrato ou o método:
    - cortar as bandas `_s_`, quase grátis no redutor combinado;
    - usar só os prazos pares, que custaria ×1,9 em vez de ×3,2 por dia mas contraria D2;
    - `temp.reduce(minMax)` no lugar de `max()` + `min()`, ganho marginal.
- **Tempo no Colab:**
  - o `getInfo` da contagem passa de ~1.100 para ~2.170 pares por mês (só metadados). Estimativa de 1 a 3 min por mês, 12 a 36 min no total (A CONFIRMAR);
  - se o `getInfo` estourar o tempo, o 03 imprime ⚠️ com o erro e exporta assim mesmo; as contagens ficam em `n_pares_*` e o 04 as mostra.

## D. Tabela de máximos esperados (para o roteiro v4)

Gerada por `testes/maximos_pares_v16.py`, que enumera as rodadas, e conferida contra `maximos_por_mes()` do 03, que enumera os dias.
- **Período:** rodadas 00Z de 2021-03-23 a 2025-12-31, dia previsto até 2025-12-31.
- **Deslocamento por prazo:** o prazo L começa em 2021-03-23 + (L−1).
- **Leitura:** máximo de pares dia×prazo; entre parênteses, o menor valor sem ⚠️ (85%).

| Mês | L1 | L2a5 | L6a10 | L11a15 |
|---|---|---|---|---|
| Jan | 124 (106) | 496 (422) | 620 (527) | 620 (527) |
| Fev | 113 (97) | 452 (385) | 565 (481) | 565 (481) |
| Mar | 133 (114) | 522 (444) | 630 (536) | 620 (527) |
| Abr | 150 (128) | 600 (510) | 750 (638) | 735 (625) |
| Mai | 155 (132) | 620 (527) | 775 (659) | 775 (659) |
| Jun | 150 (128) | 600 (510) | 750 (638) | 750 (638) |
| Jul | 155 (132) | 620 (527) | 775 (659) | 775 (659) |
| Ago | 155 (132) | 620 (527) | 775 (659) | 775 (659) |
| Set | 150 (128) | 600 (510) | 750 (638) | 750 (638) |
| Out | 155 (132) | 620 (527) | 775 (659) | 775 (659) |
| Nov | 150 (128) | 600 (510) | 750 (638) | 750 (638) |
| Dez | 155 (132) | 620 (527) | 775 (659) | 775 (659) |
| **Ano** | **1.745** | **6.970** | **8.690** | **8.665** |

- **Valores reais esperados:** a 98–100% do máximo. O F3 só aponta 3 falhas no período, e só nas horas-chave que ele examina:
  - 1 rodada ausente em 2022-04: até −1/−4/−5/−5 entre abril e maio;
  - 1 rodada sem h192 em 2022-08 e outra em 2022-09: −1 em L6a10.
- **Regra simples para o roteiro:** valor ≤ máximo e sem ⚠️. Um valor acima do máximo é erro.
- **Contas de conferência:**
  - jan = 4 × 31 (2022–2025);
  - fev = 28 + 28 + 29 + 28;
  - mar L1 = 9 + 4 × 31;
  - abr L11a15 = (29 + 28 + 27 + 26 + 25) + 4 × 150.

## E. Para os outros escopos

- **Roteiro v4, etapa 3:**
  - o arquivo agora é `03_matriz_gfs_v2_1.py`;
  - trocar a tabela pela da seção D;
  - rodar de novo passa a ser **seguro** (⏩/⏳);
  - se aparecer ❌ de versão antiga, apagar o asset à mão e rodar de novo.
- **Roteiro v4, etapa 4:** as mensagens mudaram. Conferir o `RESUMO` e parar em qualquer ❌.
- **08 (M08-10, E6):**
  - esperar 100 bandas e as propriedades do contrato;
  - a amostra por faixa está gravada em `n_pares_*` e em `n_{fx}` por pixel;
  - as datas do M08-03 (`DATAS_03`) passam a ser `inicio_rodadas = 2021-03-23` para todas as faixas.
- **Motor (05a/05b), só leitura:**
  - coerente com o 03 em horas, blocos, faixas, nomes de banda, `VERSAO_MATRIZ_GFS='V2.1'` e `BANDAS_MEDIA_GFS` (testado);
  - **A CONFIRMAR, risco baixo:** em `05a:834`, `chuva_blocos = gfs_dia.filter(inList('forecast_hours', ...))` filtra **depois** do `.map(resample)` e depende de `Image.resample()` preservar as propriedades. O 03 evita essa dependência filtrando antes.

## F. Riscos e pontos A CONFIRMAR

1. **`ee.Algorithms.If` preguiçoso (M03-11, herdado da V2):**
   - num par sem rodada, o ramo `cheia` não pode ser avaliado (o `rename` de 6 nomes falharia com 0 bandas);
   - o mesmo padrão já é usado pelo motor;
   - se falhar, a tarefa dá FAILED e não grava dado errado.
2. **Tempo do `getInfo` da contagem no Colab:** ~2.170 pares por mês. A falha é tratada (⚠️ e a exportação segue).
3. **EECU de 0,9 a 1,7 vez a V2.** A cota mensal pode acabar antes das 12 tarefas. Nada se perde: rodar de novo depois só envia o que falta.
4. ~~Exportação de Float32 com Int16~~: resolvido na revisão (todas as bandas em Float32).
5. **Fronteira v16/v17** antes de 31/12/2025.
6. **Limiares heurísticos do 04:** podem gerar ⚠️ na estação seca; calibrar na 1ª execução.
7. **Imagem duplicada:** o 03 descarta o par; o motor deduplica. A diferença é só de tamanho da amostra.
8. **`stdDev` populacional:** igual à V2; não é usado pelo motor.


## F. Mudanças feitas na revisão do coordenador (depois da entrega do agente)
- **[V4 M03-11] `composto_seguro`:** cada composição do GFS (chuva, Tmax, Tmin, UR, vento, radiação) recebe uma imagem totalmente mascarada com a banda certa. Isso não muda o valor quando há saídas e garante 1 banda quando a rodada falta. O ramo não escolhido do `ee.Algorithms.If` em `par_faixa` deixa de poder falhar no `rename`, e o risco F1 deixa de existir.
- **Bandas `n_` em Float32.** O SPEC e a seção E6 da 08 foram atualizados.
- **[V4 A-01] 04:** o fator conferido passa a ser o que o motor V1.5 aplica nos dias GFS:
  - chuva (BR+0,1)/(GFS+0,1), com teto 5;
  - vento e radiação BR/max(GFS, 1e-3) limitado a [0,5; 2].
  Os indicadores contam os pixels em que o limite atua. Antes, o 04 media o fator antigo e dava ⚠️ na seca por um defeito que a V1.5 já corrige (auditoria independente, A-01).
- **Teste:** o `teste_03` ganhou checagens estáticas do `composto_seguro` (7 usos) e do Float32.
