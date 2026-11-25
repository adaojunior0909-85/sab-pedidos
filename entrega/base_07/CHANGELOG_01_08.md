# CHANGELOG V4: 01 (máscara de qualidade, script novo) e 08 (auditoria completa)

> **Revisão posterior (20/10/2026, tarde):** as auditorias independentes A e B pediram correções neste escopo. Elas estão em `CHANGELOG_REVISAO_AB.md`, que prevalece em caso de divergência (inclusive: o `01_mascara_qualidade.py` virou `01a_mascara_qualidade_SIMULACAO.py` e `01b_mascara_qualidade_GRAVACAO.py`).

Data: 20/10/2026. Base: `/home/claude/sab/v3_zip/`. Contrato: `/home/claude/sab/v4/SPEC_V4.md`, relido depois da revisão das 11:09 (bandas `n_*` da V2.1 em Float32).
Referências:
- `/home/claude/sab/entrega/revisoes/revisao_02_07_08.md` (itens M08-xx);
- auditoria J do usuário: script `56b7675b-auditoria_complementar_J.py` e `/home/claude/sab/auditoria_J/`;
- saída real da 08 atual: `/home/claude/sab/auditoria/LOG_COMPLETO.txt` e CSVs.

## Arquivos entregues

- `/home/claude/sab/v4/01_mascara_qualidade.py`: script **novo**, 475 linhas.
- `/home/claude/sab/v4/08_auditoria_completa_SAB.py`: 2.109 linhas (v3: 1.244). O diff tem 82 linhas removidas e 947 novas.
- `/home/claude/sab/v4/testes/teste_08.py`: lógica pura da 08, extraída do arquivo por AST.
- `/home/claude/sab/v4/testes/teste_01.py`: lógica pura do 01 e checagens do contrato.
- `/home/claude/sab/v4/testes/fumaca_08_01.py`: teste de fumaça, explicado abaixo.

Todo trecho novo ou alterado da 08 leva `# [V4 <ID>]`. O cabeçalho dos dois arquivos tem o bloco "MUDANÇAS V4 (20/10/2026)".

## Validação feita

| Verificação | Resultado |
|---|---|
| `python3 -m py_compile` (01, 08 e 3 testes) | OK |
| `python3 -m pyflakes` | 01 e testes sem aviso. Na 08 restam 2 avisos que **já existiam na v3**: `io` e `datetime.date` importados sem uso (linhas 58 e 66). Ficaram byte a byte iguais, pela regra 2 |
| `testes/teste_08.py` | todos passam (pandas 3.0.5 e 2.2.3) |
| `testes/teste_01.py` | todos passam (pandas 3.0.5 e 2.2.3) |
| `testes/fumaca_08_01.py` | todos passam (pandas 3.0.5 e 2.2.3) |
| `diff -u v3_zip/08 v4/08` relido inteiro | todas as remoções são intencionais. O bloco final de execução e resumo foi movido, sem mudar, para `gravar_resumo()` e para o `try/finally` |
| Ordem das seções e códigos antigos | conferidos por AST no `teste_08.py`. A ordem é A B C D **D14** E **E6** F G H **H5** I **Q1 J1 J3 J5**, e todos os códigos de `achado` da v3 continuam presentes |

**Testes de lógica pura.** Os testes não importam os scripts, porque eles conectam ao Earth Engine no import. As funções e constantes são tiradas do próprio arquivo via `ast`, e assim os testes exercitam o código que vai para o Colab. O que é coberto:
- F5: rodadas com e sem a hora 0 (172, 173, 208 e 209 imagens), dia sem rodada, falso início, janela já depois da transição e janela sem transição. O teste reproduz o erro antigo: o teste da v3 apontaria 2017-02-08, a primeira rodada sem a hora 0;
- regra do salto na emenda, com os dados reais do `J5_tmax_2026.csv` da J (+2,40 °C em 06/10 → 07/10), limite exato de 2,0 °C, queda e lacuna;
- regra do recorde: os 4 dias reais acima de 44,8 °C; exatamente 44,8 não conta;
- `ACEITOS` e a integração com `achado()` (status final, `status_original` e motivo);
- `status_d10`, `confianca_esperada`, `checar_d14` (8 casos de falha), `avaliar_roni` (11 casos), `checar_matriz_v21`, `checar_q1`, `avaliar_j1` e, no 01, `comparar_j1`, `classe4_ok`, `contar_discordancias` e `escolher_metodo`.

**Teste de fumaça (`fumaca_08_01.py`).** Carrega a 08 e o 01 até o laço de execução com um módulo `ee` **falso**: objetos encadeáveis que não calculam nada. Troca o `gi` por respostas fixas, montadas com os números reais da auditoria. Depois roda as seções novas e alteradas: D14, E6 (com e sem a matriz), H5 (com e sem o asset), Q1, J1, J3, J5 (com e sem CSV anterior), F5, `percentis`, `coerencia_fisica`/D10, o resumo com interrupção, e o `main()` do 01 nos casos simulação, asset com outra versão, asset Q1 e classes diferentes.
- O que ele pega: erros de Python e pandas no código que roda no Colab (nomes, colunas, formatos, fluxo de status).
- O que ele **não** valida: as chamadas do Earth Engine em si.
- O que ele já pegou: no J5, o CSV anterior era lido **depois** de gravar o novo `J5_tmax_2026.csv` com o mesmo nome. Corrigido: agora é lido antes.

---

## 01_mascara_qualidade.py (novo)

### [V4 Q1] Máscara de qualidade `SAB_MASCARA_QUALIDADE`

**Linhas:**
- configuração 44-83;
- regras puras 114-146: `comparar_j1`, `classe4_ok`, `contar_discordancias` e `escolher_metodo`;
- conexão e trava 150-186;
- funções do Earth Engine 189-322;
- `main()` 328-460;
- execução com `finally` (log e zip) 463-475.

**O que faz:**
1. `SIMULAR = True` por padrão. Em simulação, as funções de escrita do `ee.data` e o `Task.start` ficam bloqueados, como na J.
2. Classes no dia 2001-01-15 com a lógica da J1 (`classes_pixel` e `codigo_abc`):
   - A = ETo e chuva iguais ao BR-DWGD, com diferença de até 0,01;
   - B = BR-DWGD existe e o SAB difere;
   - C = SAB sem BR-DWGD.
3. Confere 1961-01-15 e 2025-01-15 pixel a pixel. A conta é `abc_ref.neq(abc_dia)` com soma unweighted. Se a soma passar de 0, o script para com ❌.
4. **Centro no Brasil (separa C em 3 e 4).** Decisão documentada:
   - os centros dos pixels C (1.109) são lidos com `pixelLonLat` e `toList` na grade nativa;
   - cada centro vira um **ponto**, testado contra o polígono GAUL level0 com `filterBounds`. Esse teste vetorial é a referência;
   - a rasterização só é aceita se concordar com esse teste em **todos** os pixels C, conferido com `reduceRegions` nos próprios pontos. A ordem de tentativa é: `paint` do polígono → `reduceToImage` do polígono → `pontos` (rasteriza os próprios centros dentro do Brasil);
   - se nenhuma concordar, o script para com ❌;
   - o log mostra qual método passou e os centros vão para `Q1_centros_classe_C.csv`.
5. Imagem `classe` (uint8). Fora do SAB fica mascarada. A classe 4 é C com o centro fora do Brasil.
6. Contagens unweighted por classe e comparação com a J1. Gera ⚠️ quando:
   - A, B ou C diferem da J1 (A 70.364, B 204, C 1.109) em mais de 1%;
   - a classe 4 se afasta de ~880 em mais de 10%.
   
   Na gravação, qualquer ⚠️ impede exportar.
7. Resumo por estado: GAUL level1, pixel no estado pelo centro, soma unweighted. Inclui uma linha "fora de todos os estados". Vai para `Q1_por_estado.csv`.
8. `SIMULAR = False`:
   - se o asset existir com `versao_mascara = 'Q1'`, o script não faz nada; com outra versão, para com ❌;
   - senão, exporta com `region` = retângulo amplo, `crs` e `crsTransform` nativos, `pyramidingPolicy {'classe': 'mode'}` e as propriedades do contrato (mais `metodo_centro`);
   - espera a tarefa;
   - confere o asset gravado: contagens iguais às calculadas, 0 pixels diferentes, propriedades e grade nativa.
9. Log novo a cada execução (`'w'`). Pasta `mascara_qualidade_<data>_<hhmmss>` e `.zip` no `finally`.

**Por quê:** decisão 3 do usuário (máscara de qualidade aplicada na leitura; a trava do histórico não é aberta) e a J1 (204 pixels B; 1.109 C, dos quais cerca de 880 com o centro fora dos estados).

**Diferença deliberada em relação à J1:** com `completo=True`, a ausência de BR-DWGD **fora da área da imagem do BR-DWGD** também conta como C (`unmask(0)`). Assim todo pixel do SAB recebe uma classe. O log imprime "C na máscara × C pela conta exata da J1" para mostrar a diferença, que se espera 0 ou poucos pixels.

**Como verificar:** rodar com `SIMULAR = True`. Esperado:
- "classes idênticas pixel a pixel nos 3 dias";
- "método aceito: …";
- contagens dentro de 1% da J1;
- classe 4 perto de 880.

Depois, com `False`, esperar "gravado e conferido". A 08 (Q1) repete a conferência.

**A CONFIRMAR:**
- a regra de rasterização do Earth Engine em `paint`/`reduceToImage` (centro ou interseção). O próprio script decide pelo teste vetorial;
- se `pixelLonLat` em `reduceRegion` devolve o centro do pixel. Se não devolver, a validação acusa discordância e o script para;
- o parâmetro `pyramidingPolicy` do `Export.image.toAsset` existe na API Python, mas não era usado no pacote. Se recusar, a exportação falha na hora, sem gravar nada;
- **compartilhamento:** o App publicado precisa ler o asset. O script só lembra de compartilhar; não mexe na ACL.

---

## 08_auditoria_completa_SAB.py

### [V4 M08-01] Log e resumo sempre gravados
**Linhas:** 183-187 (pasta e log), 2054-2083 (`gravar_resumo`), 2084-2109 (laço com `try/except KeyboardInterrupt/finally`).

**Mudou:**
- a pasta passa a ter os segundos: `%Y%m%d_%H%M%S`;
- o `LOG_COMPLETO.txt` é aberto com `'w'` logo depois de criado;
- o resumo, o JSON e o .zip vão para `gravar_resumo()`, chamada no `finally`;
- se o usuário interromper, entra um achado "Execução interrompida pelo usuário" e o resumo diz em qual seção parou;
- o resumo ganha a coluna `status_original` (ver M08-08).

**Evidência:** `LOG_COMPLETO.txt` linhas 1-22 e 23-44 têm o cabeçalho repetido (duas execuções no mesmo minuto).

**Verificar:** o log tem um cabeçalho só. Se a execução for interrompida, aparece "⏸️ EXECUÇÃO INTERROMPIDA NA SEÇÃO X" no resumo.

### [V4 M08-02 / M08-03] F2, F3 e F5 com as datas do 03 v4
**Linhas:**
- constante `INICIO_RODADAS_03 = '2021-03-23'` (148);
- regras puras `tem_384`, `tres_apos_240`, `detectar_transicao` e `status_f5` (275-306);
- F2 1584 e 1604-1624;
- F3 1646-1652;
- `transicoes_gfs` 1657-1699.

**Mudou:**
- **F2:** o esperado (1 h até 120 h, 3 h até 240 h, 3 h até 384 h) vale para rodadas desde 2021-03-23. As anteriores só aparecem na tabela. Entra a data 2021-03-22 (última 00Z do v15);
- **F3:** conta a partir de 2021-03 e exige 80% nas quatro horas-chave das faixas (h24, h120, h192, h312), não só na h24;
- **F5:** lê os metadados (`creation_time`, `forecast_hours`) em blocos de 10 dias. São cerca de 32 consultas, contra até cerca de 60 `aggregate_array` da v3. A transição é detectada **dia a dia**:
  - `tem_384` exige as horas 1 a 120 e a hora 384, sem contar a hora 0;
  - `tres_apos_240` exige as horas 243 a 384, de 3 em 3;
  - a transição é o primeiro dia que passa sem que o anterior passe, com pelo menos 90% dos 30 dias seguintes também passando;
- o status é OK quando o 03 começa depois das duas mudanças, ATENÇÃO quando começa antes e INFO quando uma data não foi achada. As datas reais vão no texto e em `F_gfs_transicoes_dia_a_dia.csv`.

**Evidência:** F2 do LOG (rodadas de 173/209 imagens têm a hora 0); F3 mostra h120/h192/h312 desde 2016-07 (8 dias) e completos desde 2016-08. A data antiga, 2017-02-08, era só a primeira rodada sem a hora 0 (reproduzido no `teste_08.py`).

**Verificar:** F5 deve dar OK, com 384 h desde cerca de 2016-07-2x e 3 h desde 2019-06-13. F2 deve dar OK nas rodadas desde 2021-03-23.

**A CONFIRMAR:**
- a data exata de 2016-07 (vem do acervo);
- o custo do `reduceColumns` em blocos de 10 dias (cerca de 8 mil linhas por consulta).

### [V4 M08-04 / M08-05] D10 com a máscara do SAB_2025_12_31 e contagens unweighted
**Linhas:** `status_d10` 319-326; `coerencia_fisica` 1148, 1154-1158, 1174, 1176, 1186-1209 e 1220-1236.

**Mudou:**
- **D11:** passa a usar `ee.Reducer.sum().unweighted()`, e `pixels` passa a ser `mask().gt(0)` (0/1);
- **D10:** compara a máscara de `pr_mm` de **cada dia amostrado** com a do `SAB_2025_12_31`, na região ampla, sem `MASCARA_BR`. Conta três tipos de pixel:
  - só no dia;
  - só na referência;
  - **fração de máscara diferente**. Este acréscimo vem do 05 v1.5, que adota a máscara de 2025-12-31 como canônica e pode ser fracionária, k/255;
- lista até 50 coordenadas em `D_mascara_coordenadas.csv`. A tabela por dia vai para `D_mascara_x_SAB_2025_12_31.csv`;
- **Status:** OK se nenhum dia difere; INFO se só diferem dias V1.3/V1.4; ATENÇÃO se diferir qualquer outra versão (V1.5 ou histórico V1.0).

**Evidência:** LOG:274-326 (70.455 × 70.459 nos dias GFS); a v3 tolerava 1%; contagens fracionárias como 101,1137 = 29/255.

**Verificar:** hoje o D10 deve sair INFO, com cerca de 4 pixels a mais nos dias GFS V1.3. Depois da 5b, OK.

**Atenção:** o número de "pixels" do D10/D11 muda, porque é contagem inteira, sem peso de borda. O alvo "D10 = 70454,976" citado no CHANGELOG_05 deixa de existir. O D10 passa a conferir diretamente a igualdade da máscara com a de 2025-12-31, que é o que o 05 v1.5 promete.

### [V4 M08-06] Percentis da seção E por amostragem
**Linhas:** 1378-1393 (`percentis`) e a constante `AMOSTRA_PERCENTIS` (149).

**Mudou:**
- os percentis 1, 5, 50, 95 e 99 passam a ser calculados pelo `pandas.quantile`, sobre `sample(numPixels=6000, seed=7, projection=ee.Projection(CRS).atScale(11132))` dentro do Brasil. É o mesmo padrão da J4, que rodou;
- a contagem `_count` continua sendo a total, com `ee.Reducer.count()`. Entra a coluna `_n_amostra`;
- o `acima5` não mudou.

**Evidência:** E1/E3 do LOG (p1 = p99 no Rs dos meses 3, 9 e 10; rsub com p1 a p95 iguais).

**Verificar:** percentis crescentes e diferentes; a mediana do E3-rsup deixa de ser 3,71.

**A CONFIRMAR:** dos 6.000 pontos sorteados, cerca de 2.500 caem no Brasil (a J4 teve 2.498). Não pedi mais pontos porque o `getInfo` de uma coleção é limitado a 5.000 elementos.

### [V4 M08-08] ACEITOS
**Linhas:** `ACEITOS` 171-177; `rebaixar_aceito` 309-316; `achado()` 218-224; `CONTEXTO['versoes_baselines']` no I1 (1874).

**Mudou:** C7, E4, H2, H4 e I1 em ATENÇÃO viram INFO, com "[ATENÇÃO aceita: motivo]" no significado e `status_original` no resumo. ERRO nunca é rebaixado. Proteção a mais: o I1 só é rebaixado se as Baselines tiverem **apenas** a versão B1.1.

**Verificar:** esses cinco itens aparecem como ℹ️ com o motivo.

### [V4 M08-11] D14: dias de 2026 (seção nova, roda com 'D')
**Linhas:** `checar_d14`, `status_d14` e `confianca_esperada` (370-427); `inventario_2026` (723-752); a seção (1343-1373).

**Critérios:**
- todos os dias V1.5;
- datas contíguas desde 2026-01-01;
- dias GFS com `rodada_gfs_ms % 86.400.000 == 0`;
- `Confianca_Prazo` igual ao esperado pelo prazo L (alta para 1-5, media para 6-10, baixa para 11 em diante), com a mesma conta do `prazo_L` do 05 v1.5;
- `provisoria_gfs_incompleta` ou `falha_latencia_gfs` só no último dia;
- emenda: primeiro dia GFS = último dia ERA5 + 1, e último dia ERA5 do SAB = último dia do ERA5-Land (G1);
- ordem das rotas definitiva → ERA5 → GFS;
- propriedades `fonte`, `janela_chuva_utc` e `matriz_gfs` do contrato. Os valores conferem com as constantes do 05 v1.5 (linhas 199-204).

**Status:** INFO "aguardando motor V1.5" enquanto não há dia V1.5. Depois, OK com todos os critérios ou ATENÇÃO.

**Verificar:** hoje sai INFO. Depois da 5b, OK. Os detalhes vão para `D14_dias_2026.csv`.

### [V4 M08-10] E6: matriz GFS V2.1 (seção nova, roda com 'E')
**Linhas:** `bandas_v21`, `checar_matriz_v21`, `criterio_detalhe` e `criterio_rs` (509-558); a seção (1472-1563).

**Confere:**
- 12 imagens com as 100 bandas;
- `n_*` em **Float32** (contrato revisado), com valores inteiros e ≥ 1, verificado em janeiro e julho;
- todas as propriedades do contrato. Elas conferem com o 03 v2.1, linhas 316-331;
- `n_pares_*` > 0;
- detalhe espacial do L1 em janeiro e julho contra a V1: razão de gradientes na Serra do Mar, OK se for ≥ 1,2 vez a da V1 e ≥ 0,3;
- Rs da V2.1 contra a V1: (GFS/BR na V2.1) ÷ (GFS/BR na V1) entre 0,85 e 0,99.

Sem a matriz: ATENÇÃO "Rode o 03".

**A CONFIRMAR:** os dois limiares numéricos são heurísticos e devem ser calibrados na 1ª execução.

### [V4 M08-09] H5: RONI_CPC_v6 × CPC (seção nova, roda com 'H')
**Linhas:** `avaliar_roni` (430-507) e a seção (1813-1851).

**Confere:**
- estação só no asset (ERRO);
- estação do CPC faltando no meio (ERRO);
- CPC com estação mais nova (ATENÇÃO "rode o 02");
- |RONI − RONI_2c do CPC| > 0,05 e |RONI_2c − CPC| > 1e-6: ERRO nas estações antigas, ATENÇÃO "o CPC revisou" nas 3 mais novas;
- mês central;
- `system:time_start` (e `data_ms`) = 1º dia do mês central;
- continuidade;
- `chave_join` gravada pelo 02 v4;
- a chave montada no servidor exatamente como o painel faz (`ee.Number(ano).format('%04d')…`) nas 3 primeiras estações.

Sem o asset: ATENÇÃO "Rode o 02".

**A CONFIRMAR:** se `format('%04d')` aceita `ano` gravado como double. O H5 é justamente esse teste: se falhar, sai ERRO "chave do painel não calculada".

### [V4 Q1] Q1: máscara de qualidade (seção nova)
**Linhas:** `checar_q1` (560-577) e a seção (1882-1915).

**Confere:**
- se o asset existe;
- as propriedades (`versao_mascara`, `dia_referencia`, `n_classe_1..4`) contra as contagens unweighted;
- a grade nativa;
- a igualdade pixel a pixel com as classes recalculadas em 2013-07-15. As classes 3 e 4 são fundidas em C, com a mesma regra `completo=True` do 01.

Sem o asset: ATENÇÃO "Rode o 01".

### [V4 J1] J1 permanente
**Linhas:** `avaliar_j1` (579-590) e a seção (1917-1958).

**Mudou:** classes A/B/C/D em 1961-01-15, 1990-12-31 e 2025-12-31, com a conta **exata** da J. São a lógica sem `unmask`, a soma padrão e os limites dos estados do GAUL level1, de modo que os números saem comparáveis um a um com a J.
- INFO se B = 204 e C = 1.109 nos três dias; senão, ATENÇÃO;
- nos dias `definitiva` de 2026, se houver, há um item `J1-2026`: OK se B = 0.

### [V4 J3] J3
**Linhas:** 1960-1973.

**Mudou:** homônimos dos estados no GAUL level1, sem "Name Unknown". Sai sempre como INFO, com a nota de que o painel 2026.10.4 filtra também por país.

### [V4 J5] J5
**Linhas:**
- regras puras `dias_acima_recorde`, `salto_emenda` e `comparar_gfs_x_era5` (329-367);
- constantes `RECORDE_TMAX_BR`, `SALTO_EMENDA_MAX_C` e `J5_CSV_ANTERIOR` (150-151, 87);
- a seção (1975-2049).

**Mudou:**
- Tmax nacional (máxima, média, % > 40 °C, % > 42 °C) de todos os dias de 2026, numa consulta por mês (`reduceRegion` dentro de `map`, calculado no servidor). Sai `J5_tmax_2026.csv` no formato da J;
- **J5a:** ATENÇÃO se algum dia passa de 44,8 °C;
- **J5b:** ATENÇÃO se o salto na emenda passa de 2 °C (em valor absoluto);
- **J5c:** com `J5_CSV_ANTERIOR` apontando para o CSV de uma execução anterior (desta 08 ou da J), compara previsão GFS × ERA5 nas datas que já viraram ERA5. ATENÇÃO se o viés médio da máxima passar de 2 °C. Sem o CSV, sai INFO com a instrução.

**Verificar (hoje, dias V1.3):** J5a deve dar ATENÇÃO (os 4 dias acima de 44,8) e J5b ATENÇÃO (+2,40 °C em 06/10 → 07/10).

**A CONFIRMAR:** o tempo da consulta mensal (cerca de 30 reduções por chamada). Se demorar, há `RODAR_J5 = False`.

### [V4] Execução por seção
**Linha:** 2089.

**Mudou:** `SECOES_A_RODAR` aceita a letra ('D' roda D e D14) ou o código ('D14').

**Constantes para desligar as seções novas:** `RODAR_D14`, `RODAR_E6`, `RODAR_Q1`, `RODAR_J1` e `RODAR_J5` (linhas 80-84).

---

## Resultado esperado na próxima execução (antes das etapas 1, 2, 3 e 5b)

| Item | Esperado |
|---|---|
| D14 | INFO, "aguardando motor V1.5" |
| E6 | ATENÇÃO, "rode o 03" |
| H5 | ATENÇÃO, "rode o 02" |
| Q1 | ATENÇÃO, "rode o 01" |
| J1 | INFO (B 204, C 1.109) |
| J3 | INFO |
| J5a e J5b | ATENÇÃO |
| J5c | INFO |
| F5 | OK |
| F2 e F3 | OK |
| D10 | INFO |
| C7, E4, H2, H4 e I1 | INFO, com o motivo |

Tempo estimado: 12 a 15 min, contra 7 min da v3. Os acréscimos são:
- D10: cerca de 1 min;
- E: cerca de 0,5 min;
- J5: 1 a 3 min;
- demais seções novas: menos de 1 min no total.

## Riscos

1. **Chamadas do Earth Engine não testadas aqui.** Sem credenciais, só o teste de fumaça com `ee` falso. As novidades em relação ao que já rodou no Colab são:
   - `Reducer.unweighted()`;
   - `paint` e `reduceToImage` (validadas em tempo de execução no 01);
   - `reduceRegions` em pontos;
   - `pyramidingPolicy`;
   - `reduceRegion` dentro de `map` (J5);
   - `FeatureCollection` a partir de `ImageCollection.map` que devolve `Feature`.
   
   Todas são APIs documentadas; uma falha vira "Seção X interrompida" (NÃO EXECUTADO) sem afetar as outras seções.
2. **D10/D11 mudam de número.** As contagens viram inteiras e unweighted, sem peso de borda; as porcentagens do D11 mudam um pouco. O alvo "70454,976" do CHANGELOG_05 deixa de valer: o D10 confere a igualdade da máscara (presença e fração).
3. **`SECOES_A_RODAR = ['C','E','F','G','H','I']`** passa a rodar também E6 e H5, por causa da regra da letra.
4. **Resumo com coluna nova** `status_original`. Quem lê o CSV por posição de coluna precisa ajustar.
5. **Limiares heurísticos** a calibrar na 1ª execução:
   - E6: detalhe ≥ 1,2 × V1 e ≥ 0,3; Rs entre 0,85 e 0,99;
   - J5c: viés de 2 °C;
   - 01: classe 4 dentro de 10% de 880.
6. **Dependência dos outros escopos.** O D14 e o E6 conferem nomes e valores do contrato. Os gravados pelo 05 v1.5 e pelo 03 v2.1 conferem com o código atual deles. Se algum mudar, o item acusa ATENÇÃO, que é o comportamento desejado.

## Pontos A CONFIRMAR (resumo)

- **01:**
  - regra de rasterização do Earth Engine (o script escolhe o método pelo teste vetorial e registra no log);
  - `pixelLonLat` no centro do pixel;
  - `pyramidingPolicy` aceito;
  - compartilhamento do asset para o App;
  - diferença "C na máscara × C da J1" (esperada 0 ou poucos).
- **08:**
  - data exata da transição de 384 h em 2016-07;
  - custo dos blocos de 10 dias do F5 e das consultas mensais do J5;
  - `format('%04d')` com `ano` double (é o que o H5 testa);
  - limiares heurísticos do E6 e do J5c;
  - amostra efetiva de cerca de 2.500 pixels por mês nos percentis.
