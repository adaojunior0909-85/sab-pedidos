# CHANGELOG V4: scripts 02 (RONI oficial do CPC) e 07a/07b (conferência das normais B1.1)

> **Revisão posterior (20/10/2026, tarde):** as auditorias independentes A e B pediram correções neste escopo. Elas estão em `CHANGELOG_REVISAO_AB.md`, que prevalece em caso de divergência.

Data: 20/10/2026. Base: `/home/claude/sab/v3_zip/`. Contrato: `/home/claude/sab/v4/SPEC_V4.md`.
Referência: `/home/claude/sab/entrega/revisoes/revisao_02_07_08.md` (itens M02-xx e M07-xx).

Arquivos entregues:
- `/home/claude/sab/v4/02_auditoria_roni_cpc.py` (719 linhas; 23 removidas e 321 novas em relação ao v3)
- `/home/claude/sab/v4/07a_normais_CONFERIR_1991_2020.py` (1.540 linhas; 53 removidas e 291 novas)
- `/home/claude/sab/v4/07b_normais_CONFERIR_1961_1990.py`, gerado a partir do 07a
- `/home/claude/sab/v4/testes/teste_02.py` e `/home/claude/sab/v4/testes/teste_07.py`

Todo trecho novo ou alterado está marcado com `# [V4 <ID>]`. O cabeçalho de cada arquivo tem o bloco "MUDANÇAS V4 (20/10/2026)".

## Validação feita

| Verificação | Resultado |
|---|---|
| `python3 -m py_compile` nos 3 scripts e nos 2 testes | OK |
| `python3 -m pyflakes` nos 3 scripts e nos 2 testes | nenhum aviso |
| `testes/teste_02.py` (pandas 3.0.5 e pandas 2.2.3, a série do Colab) | todos passam |
| `testes/teste_07.py` (pandas 3.0.5 e 2.2.3) | todos passam |
| `diff 07a 07b` | só as linhas 1 (título) e 146 (`PERIODO_VERIFICACAO`), como no v3 |
| `diff -u v3_zip/<arq> v4/<arq>` relido inteiro | todas as remoções são intencionais (lista abaixo) |
| Bloco de coerência física movido para `problemas_coerencia` | idêntico ao v3 linha a linha, depois das 4 trocas de nome (conferido por script) |

**Observação:** no v3, o 07a e o 07b diferem em **duas** linhas, não em uma: a 1 (título com o período) e a 115 (`PERIODO_VERIFICACAO`). Mantive as duas. O 07b é gerado por script a partir do 07a, trocando só essas duas linhas.

**Testes.** Os testes não importam os scripts, porque eles rodam o Earth Engine no import. Eles tiram do próprio arquivo, via `ast`, as funções e constantes testadas, e assim exercitam o código que vai para o Colab. Para rodar: `python3 /home/claude/sab/v4/testes/teste_02.py` e `python3 /home/claude/sab/v4/testes/teste_07.py` (o código de saída 1 indica falha).

**"Arquivo do CPC" simulado.** O download do CPC é bloqueado aqui. O teste usa:
- o `RONI_2c` real de 1950 a 2025, de `/home/claude/sab/auditoria/H_roni_antigo_x_cpc.csv` (baixado pelo 08 em 20/10/2026);
- 2026 simulado: JAS = 1,69, como no H3 do 08; os outros meses são valores de 2 casas compatíveis com a tabela.

O formato `SEAS YR ANOM` foi deduzido das colunas que o 08 gravou.

---

## 02_auditoria_roni_cpc.py

### [V4 M02-02] Estações novas do CPC entram sozinhas
- **Onde:**
  - cabeçalho, linhas 9-12, 19-22 e 40-44;
  - constantes, linhas 64-66: `URL_TABELA_CPC`, `AUTO_ESTACOES_NOVAS = True`, `ESTACOES_REVISAVEIS = 3`;
  - funções, linhas 279-397: `empate_2c`, `arred_sem_empate`, `ler_tabela`, `conciliar_oficial`, `linhas_tabela`, `carregar_oficial`;
  - linha do ano no fim do log, linhas 712-719.
- **O que mudou:** a conciliação virou uma função pura, `conciliar_oficial(tab, asc, auto_novas, n_revisaveis)`, sem rede e sem `ee`. Ela devolve `(oficial, rel)`. Regras:
  - estação digitada que o arquivo não tem: erro, como antes;
  - estação do arquivo que a tabela não tem:
    - sem empate: entra com `round(RONI_2c, 1)`. O `+ 0.0` evita "-0.0" na tabela;
    - empate (2ª casa = 5, testada sobre `abs(x)`, então -0,45 e -1,05 são empates): erro que mostra ano, trimestre e `RONI_2c`, com o link e a instrução de digitar o valor da tabela ERSSTv6 no lugar do NaN;
  - diferença acima de 0,05 entre a tabela e o arquivo:
    - nas 3 últimas estações **digitadas**: vale o valor do arquivo, com ⚠️ "Revisão do CPC em ...";
    - se o valor revisado for empate: erro pedindo o valor do site;
    - antes das 3 últimas: erro "Divergência acima do arredondamento ...", como antes.
  - Verificações novas do arquivo (erro com a linha): colunas esperadas, trimestre válido, valor numérico com |x| ≤ 9 e estação sem repetição.
  - Uma lacuna no meio da tabela (estação apagada sem querer) também é preenchida pelo arquivo, com a mesma regra do empate. O código da revisão já fazia isso para qualquer `right_only`.
  - `AUTO_ESTACOES_NOVAS = False` volta à parada antiga, com a mesma mensagem.
- **Mensagens:**
  - `Estações acrescentadas do arquivo do CPC: [[2026, 'ASO', 1.93, 1.9]]`, no formato [ano, trimestre, RONI_2c, RONI];
  - no fim, `📝 Tabela noaa_data com as estações de hoje ...`, seguida da linha do ano da última estação e de todo ano que ganhou estação nova ou revisão, no formato exato da tabela. Exemplo: `2026 -0.9 -0.8 -0.4 0.0 0.5 1.0 1.4 1.7 1.9 NaN NaN NaN`;
  - nenhuma mensagem supõe 920 estações: `✅ N estações oficiais conferidas (última: ...)` usa `len(oficial)`, e as demais usam o total real.
- **Por quê (evidência):**
  - conferi contra os dados reais, e o teste repete a conta: nas 912 estações de 1950 a 2025, 87 são empate (47 negativas);
  - nas 825 sem empate, `round(RONI_2c, 1)` é igual à tabela digitada em 100%;
  - o maior |tabela − arquivo| é 0,0500000000000003, dentro da tolerância de `0.05 + 1e-9`, que foi mantida.
- **Como verificar na execução:**
  - em novembro, o passo 5 mostra `Estações acrescentadas do arquivo do CPC: [[2026, 'ASO', ...]]` e `✅ 921 estações oficiais conferidas (última: ASO 2026 = ...)`;
  - num empate, a execução para no passo 5 com a mensagem nova.
- **A CONFIRMAR:**
  - o formato real do `RONI.ascii.txt` (colunas SEAS, YR, ANOM; inferido do 08). Se mudar, o script para com a lista de colunas lidas;
  - se o CPC pode revisar mais de 3 estações para trás (o cabeçalho antigo dizia "até dois meses"). Isso se ajusta em `ESTACOES_REVISAVEIS`.

### [V4 M02-01] Gravação sem janela e sem perder o compartilhamento
- **Onde:**
  - helpers, linhas 512-543: `asset_existe`, `acl_sem_dono`, `acl_resumo`, `aplicar_acl`;
  - troca, linhas 629-677;
  - cabeçalho, linhas 6-8.
- **O que mudou:** depois da exportação do `_TMP`:
  1. lê a ACL do asset atual com `ee.data.getAssetAcl`, se ele existir, e imprime;
  2. apaga um `RONI_CPC_v6_ANTERIOR` que tenha sobrado;
  3. renomeia o atual para `_ANTERIOR`. Se falhar: ❌ e nada é trocado;
  4. promove o `_TMP`. Se falhar, devolve o `_ANTERIOR` e para com ❌;
  5. reaplica a ACL sem a chave `owners` com `ee.data.setAssetAcl`, tentando primeiro texto JSON e depois dicionário;
  6. lê e imprime a ACL final.
  
  Os avisos ⚠️ não interrompem a execução:
  - a ACL não pôde ser reaplicada;
  - a ACL final difere da anterior (comparação sem `owners`, sem entradas vazias e com listas ordenadas);
  - não havia ACL anterior (primeira gravação).
  
  Todos mandam compartilhar à mão ("Anyone can read", roteiro 2.7). Não existe mais o momento em que o RONI fica sem asset.
- **Por quê:**
  - o v3 fazia `deleteAsset(ASSET_RONI)` e depois `renameAsset(TMP, ASSET_RONI)` (linhas 416 e 419 do v3);
  - o asset novo nascia com o compartilhamento padrão, e o App publicado perderia o RONI a cada rodada mensal;
  - entre o delete e o rename não havia asset nenhum.
- **Como verificar:**
  - o log mostra `ACL do asset atual: {...}` e depois `ACL final de RONI_CPC_v6: {...}`;
  - a ACL final deve ter `all_users_can_read: True` se a anterior tinha;
  - nenhum ⚠️ de compartilhamento deve aparecer.
- **A CONFIRMAR:**
  - o formato aceito por `ee.data.setAssetAcl` na versão do Colab (texto JSON ou dicionário). O código trata os dois e avisa se nenhum funcionar;
  - o nome da chave de leitura pública (`all_users_can_read`). O código não depende dele, porque compara a ACL inteira;
  - se `renameAsset` preserva a ACL. O código reaplica de qualquer jeito.

### [V4 M02-03] Leitura de volta e `chave_join`
- **Onde:**
  - `chave_join`, linhas 505-506 (entra também no CSV local `RONI_CPC_v6.csv`);
  - `ler_asset_roni` e `conferir_leitura`, linhas 545-608;
  - fluxo, linhas 679-710;
  - cabeçalho, linhas 13-16.
- **O que mudou:** cada feição ganha `chave_join` = 'AAAA_MM' (texto). Depois da troca e da ACL, o asset é lido de volta com 3 tentativas de `getInfo`. `ts_lido` é o `system:time_start` lido no servidor, ou -1 se a feição não o tiver. A função pura `conferir_leitura` compara:
  - o mesmo conjunto (ano, mês), sem repetição;
  - RONI e RONI_2c com |dif| < 1e-6, o que tolera gravação em float32;
  - Trimestre, `data_ms` e `chave_join`;
  - `system:time_start == data_ms`.
  
  Depois da comparação:
  - **se tudo bater:** imprime `✅ N estações conferidas no asset (estações, RONI, RONI_2c, Trimestre, mês central, data_ms, chave_join, system:time_start)` e apaga o `_ANTERIOR`;
  - **se não bater:** lista as divergências (até 10 por tipo), apaga o asset novo, renomeia o `_ANTERIOR` de volta, reaplica a ACL e para com ❌. Na primeira gravação, sem anterior, o asset novo é apagado e a execução para;
  - **se a leitura falhar 3 vezes:** para com ❌, mantendo o asset novo no lugar e o `_ANTERIOR`. A próxima execução apaga o que sobrou.
  
  Os prints antigos `✅ N estações gravadas em ... (esperado N).` continuam.
- **Por quê:** o v3 só imprimia a contagem (linha 421 do v3), sem comparar valores, tipos ou a data.
- **Como verificar:** a linha nova `✅ 920 estações conferidas no asset (...)`. O total é o real do mês.
- **A CONFIRMAR (risco principal deste item):** se `Export.table.toAsset` preserva o `system:time_start` das feições e se `propertyNames()` de uma feição o inclui.
  - Se ele não vier em **nenhuma** feição, isso vira só ⚠️ (A CONFIRMAR), sem restaurar o anterior. Assim não se bloqueia a rotina mensal por um comportamento da exportação: o painel recalcula a data a partir de `ano` e `mes` (06 v3:1582), e `data_ms` é conferido.
  - Se vier em parte das feições, ou com valor diferente: ❌.

### Mantido sem mudança no 02
Réplica OISST, comparação tripla, estatísticas, `arred1` e as mensagens que o roteiro cita (`Área Niño 3.4`, `Área trópicos`, `Fator de ajuste de variância`, `estações oficiais conferidas`, `estações gravadas em`). Ficaram fora do escopo: M02-04 a M02-08.

---

## 07a/07b_normais_CONFERIR

### [V4 M07-02] Modo conferência
- **Onde:**
  - `MODO_CONFERENCIA = True`, linhas 130-131;
  - trava, linhas 250-264, logo depois do `ee.Initialize`;
  - critério do PLANO, linhas 1448-1453;
  - frase final, linhas 1485-1490;
  - cabeçalho, linhas 4-5 e 95-96.
- **O que mudou:**
  - com `MODO_CONFERENCIA = True`:
    - se `SIMULAR` não for True, a execução para (`RuntimeError`);
    - `ee.batch.Task.start` e as funções de escrita de `ee.data` (com `hasattr`) passam a levantar "CONFERÊNCIA SOMENTE LEITURA". As funções são createAsset, deleteAsset, renameAsset, copyAsset, updateAsset, setAssetAcl, setAssetProperties, createFolder, startProcessing, exportImage, exportTable, startIngestion e cancelTask, a mesma lista da auditoria J e do 08;
  - novo critério: `PLANO: as N imagens já existem com os nomes esperados (enviar X, na fila Y)`, com ✅ só se X = Y = 0;
  - se `VERIFICAR = False` no modo conferência: critério ❌ "conferência numérica ligada";
  - frase final, com tudo ✅: `✅ Tudo conferido: as imagens gravadas batem com o cálculo independente. Não há nada a exportar; mantenha SIMULAR = True.` A frase antiga só aparece se alguém desligar `MODO_CONFERENCIA` (uso como gerador).
- **Por quê:** o roteiro 7.3 mandava ignorar a frase "mude SIMULAR para False". Com nomes divergentes, seguir essa frase subiria até 48 exportações pesadas.
- **Como verificar:** `🔒 MODO_CONFERENCIA: escrita no Earth Engine bloqueada (só leitura).` logo no início. Em `=== CRITÉRIOS ===`, a linha `✅ PLANO: as 48 imagens ... (enviar 0, na fila 0)`, e no fim a frase nova.

### [V4 M07-01] Assets gravados entram na conferência
- **Onde:**
  - funções `valores_como_referencia` e `problemas_coerencia`, linhas 717-764;
  - bloco dos gravados em `verificar`, linhas 1179-1223;
  - critérios em `main`, linhas 1469-1472.
- **O que mudou:** a imagem gravada de normais é amostrada uma vez (`g_n`), e a de limiares uma vez, só com as bandas dos dias conferidos (`g_l`). Critérios novos, por mês conferido:

  | Critério (mês MM) | Relatório | O que compara |
  |---|---|---|
  | `assets gravados = local` | c1 | inalterado, mesmo texto que o roteiro cita |
  | `P95/P99 gravados na faixa` | c2 | `comparar_percentis(g_n, umidos, MIN_DIAS_UMIDOS)` |
  | `limiares gravados na faixa` | c3 | `comparar_percentis(g_l, janelas, n_min)` |
  | `limiares gravados = recálculo EE` | c4 | `comparar(g_l, ee_l)`; banda ausente ou mascarada num só dos lados conta como divergência |
  | `coerência física dos gravados` | | o mesmo bloco de coerência, agora em `problemas_coerencia`, rodado sobre `g_n`/`g_l`; mensagens "⚠️ gravado: ..." |

  No modo conferência, um asset ausente vira o critério ❌ `asset gravado presente: <nome> (mês MM)`.
  
  O bloco de coerência do v3 foi movido sem mudar regra. Comparei por script: as 36 linhas são idênticas depois de trocar `loc_n.items()` → `nomes`, `ee_n`/`ee_l` → `vals_n`/`vals_l` e `DIAS_VERIFICACAO` → `dias`.
- **Por quê:** no v3, só as normais gravadas eram comparadas (linhas 1094-1103 do v3). Limiares e P95/P99 gravados nunca eram lidos, e a coerência rodava só sobre o recálculo.
- **Como verificar:** novas linhas no log, como `asset gravado Limiares_1991_2020_M02 (dias (1, 15, 28)): 60 de 60 na faixa; 60 de 60 iguais ao recálculo do Earth Engine`, e os critérios novos com ✅.
- **Ficou de fora:**
  - a conferência continua só nos meses de `MESES_VERIFICACAO` (agora 1, 2 e 8). Os 12 meses ficam para o M07-07;
  - os fatores de correção continuam vindo de `montar_correcao_mes` (M07-04);
  - extras e propriedades das coleções (M07-06);
  - unificação do 07a e do 07b (M07-08);
  - tolerância explícita do percentil (M07-09).
- **A CONFIRMAR:** c4 usa a tolerância padrão de `comparar` (rtol 5e-4, atol 1e-4). Gravado e recálculo são float32 do mesmo código e devem bater, mas se `ee.Reducer.percentile` (maxRaw=1000) não for determinístico entre execuções, c4 acusa.

### [V4 M07-05] Fevereiro na conferência
- **Onde:**
  - `MESES_VERIFICACAO = (1, 2, 8)` e `DIAS_POR_MES = {2: (1, 15, 28)}`, linhas 133-138;
  - `dias_verif` e `meses_da_serie_base`, linhas 693-707;
  - usos em `verificar`, linhas 1107, 1110, 1120, 1131, 1142 e 1159 (e 1200 no M07-01).
- **O que mudou:**
  - `dias_verif(mes)` devolve `DIAS_POR_MES[mes]` ou `DIAS_VERIFICACAO`, limitados ao último dia com limiar: 28 em fevereiro, como em `imagem_limiares`, e 30 nos meses de 30 dias;
  - os quatro pontos que usavam `DIAS_VERIFICACAO` fixo (limiares do EE, meses da série-base, janelas locais e o teste do dia 15) passam a usar `dias`;
  - a regra dos meses da série-base virou `meses_da_serie_base`, sem mudar a lógica.
- **Por quê:** fevereiro é o mês do bissexto. O limiar vai até o dia 28 e a janela do dia 28 inclui o 29/02. O dia 31 fixo não servia para fevereiro.
- **Como verificar:** critérios com "(mês 02)" e a linha `percentis diários (limiares dos dias (1, 15, 28) ...)`.
- **Custo:** cerca de 50% a mais no tempo da conferência (3 meses em vez de 2).

### [V4 M07-03] Relatório da regra do SPI de 20 anos com chuva
- **Onde:**
  - constantes `RELATORIO_SPI_20 = True` e `MIN_ANOS_COM_CHUVA_LEITURA = 20`, linhas 139-141;
  - `anos_com_chuva`, linha 710;
  - `reduzir_brasil` e `relatorio_spi_20`, linhas 1229-1272;
  - chamada em `main`, linhas 1473-1481.
- **O que mudou:** relatório só de leitura sobre as 12 normais gravadas de `PERIODO_VERIFICACAO`. Para cada mês e escala do SPI (1, 3 e 6) conta, com `ee.Reducer.sum().unweighted()` num `reduceRegion` na grade nativa (`crs`/`crsTransform` do banco, `limitesRegiao`):
  - os pixels com SPI ajustado;
  - os cortados pela regra `round(n × (1 − q0)) < 20`;
  - quantos seriam cortados sem o `round`;
  - a % cortada.
  
  O log explica o `round` com a conta feita na hora: `q0 = float32(1/3) = 0.333333343` e `30 × (1 − q0) = 19.999998`. É informação, não critério. Uma falha do relatório vira ⚠️ e não esconde os critérios. A constante desliga o relatório (12 `reduceRegion`).
- **Por quê:** a regra de leitura (roteiro, Parte A.4) não estava medida em lugar nenhum, e o `q0` gravado em float32 cria a armadilha.
- **Achado do teste:** sem o `round`, a regra corta por engano pixels com exatamente 20 anos com chuva quando n = 21, 22, 24, 25, 26, 28 ou 30. Os casos com n ≥ 24 são reais, porque a normal exige 24 anos. Isso ocorre mesmo com a conta em double, porque o problema é o `q0` gravado em float32. Com o `round`, os 990 casos (n de 1 a 30) recuperam o número exato de anos com chuva, em float32 e em double.
- **Como verificar:** tabela `📊 [M07-03] REGRA DE LEITURA DO SPI ...` com 12 linhas e as colunas `SPI{k}_ajustados`, `_cortados`, `_%cortados` e `_sem_round`.
- **Para o painel (fora deste escopo):** na integração, usar `spi{k}_n.multiply(1 - spi{k}_q0).round().gte(20)`.

### [V4 Q1] Relatório por classe da máscara de qualidade
- **Onde:** constantes `ASSET_MASCARA`, `RELATORIO_QUALIDADE` e `MES_RELATORIO_QUALIDADE = 1`, linhas 142-145; `relatorio_qualidade`, linhas 1275-1320; chamada em `main`, linhas 1473-1481.
- **O que mudou:** se `projects/clima-492922/assets/SAB_MASCARA_QUALIDADE` existir, o relatório:
  - imprime as propriedades `versao_mascara`, `dia_referencia` e `n_classe_1..4`;
  - conta, em janeiro das normais gravadas, os pixels com `pr_mm_media` válida por classe 1-4. Conta também os pixels do SAB sem normal e as normais fora da máscara (`sum().unweighted()`);
  - imprime a média e a máxima de `et_potencial_media` e `pr_mm_media` por classe e no grupo "2 a 4", com o mesmo redutor `mean().combine(max(), sharedInputs=True)` da J2, e uma linha que compara a classe 1 com as classes 2 a 4;
  - termina com ⚠️ dizendo que as normais nas classes 2 a 4 não vêm do BR-DWGD.
  
  Sem o asset: `⚠️ [Q1] ... não existe: rode o 01 ...`, e a execução continua.
- **Por quê:** a J2 mostrou ETo máxima de janeiro de 275 mm/mês na classe C, contra 188 na A. O contrato (SPEC_V4) manda o 07 relatar por classe.
- **A CONFIRMAR:** o asset da máscara ainda não existe; os nomes vêm do contrato (banda `classe`, valores 1-4, mascarada fora do SAB).

### [V4 cabeçalho]
- **Onde:** linhas 2-18 (bloco MUDANÇAS V4), 26-29 e 93-96.
- **O que mudou:**
  - o resumo não diz mais que o painel usa as normais: o painel (até a 2026.10.4) ainda não lê a pasta Baselines, e a integração fica para depois;
  - o passo 5 do COMO RODAR foi ajustado;
  - nota de que este arquivo é de conferência, então só o passo 1 roda.

---

## Impacto no roteiro (para quem mantém o `00_ROTEIRO_FINAL.md`; fora deste escopo)

**Etapa 2.**
- Acabou a edição manual da tabela. A "única exceção" da linha 3 e o passo 2.2 deixam de valer: só se digita um valor num empate, e o script diz qual.
- Linhas novas no log:
  - `Estações acrescentadas do arquivo do CPC: ...` (quando houver);
  - `ACL do asset atual` e `ACL final`;
  - `✅ N estações conferidas no asset (...)`;
  - `📝 Tabela noaa_data ...`.
- O passo 2.6 (compartilhar) passa a ser necessário só na primeira gravação, ou quando aparecer ⚠️ de compartilhamento.

**Etapa 7.**
- Remover o passo 7.2 ("Ignore a frase seguinte"). A frase final agora é `✅ Tudo conferido: as imagens gravadas batem ...`.
- O "PLANO ... enviar 0" virou critério.
- Critérios novos por mês, agora também "(mês 02)": `P95/P99 gravados na faixa`, `limiares gravados na faixa`, `limiares gravados = recálculo EE` e `coerência física dos gravados`.
- Dois relatórios informativos: `[M07-03]` e `[Q1]`. Antes de existir o 01, o `[Q1]` mostra ⚠️ "rode o 01", e isso é esperado.
- O tempo sobe cerca de 50%.

## Riscos
1. **M02-03, `system:time_start` na exportação de tabela.** Ausente em todas as feições: só aviso. Divergente ou parcial: rollback. Se a exportação gravar `data_ms` como float32, a conferência acusa e restaura o anterior. É um rollback seguro, mas bloquearia a atualização mensal até o ajuste.
2. **M02-01, `setAssetAcl`.** O formato e a semântica (reaplicar sem `owners`) não foram testados no Earth Engine. A falha não interrompe e avisa para compartilhar à mão.
3. **M02-02, revisão nas 3 últimas.** Uma revisão aceita com ⚠️ e não colada na tabela volta a parar a execução quando a estação sair das 3 últimas digitadas. O aviso diz isso.
4. **M07-01, c4 (gravado = recálculo).** Depende de o percentil do EE ser determinístico. Se não for, aparece ❌ falso.
5. **Tempo do 07.** Fevereiro e as leituras dos gravados (1 amostragem de limiares por mês) aumentam o tempo, e os dois relatórios somam 18 `reduceRegion` leves. Ambos se desligam por constante.
6. **Nada foi executado no Earth Engine.** As chamadas novas seguem padrões já usados no código ou na auditoria J executada pelo usuário: `reduceRegion` com `crsTransform` e `tileScale=4`, o redutor combinado `mean+max`, `propertyNames().contains` + `ee.Algorithms.If`, `getAsset`, `renameAsset` e `deleteAsset`. São novas no pacote, mas da API oficial: `ee.data.getAssetAcl`/`setAssetAcl` e `ee.Reducer.sum().unweighted()` (A CONFIRMAR na 1ª execução).
