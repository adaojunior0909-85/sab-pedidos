# ESPECIFICAÇÃO DO PACOTE SAB v4.1 (20/10/2026) — contrato comum a todos os arquivos

> **v4.1 (20/10/2026, tarde):** ajustes depois das auditorias K e K1d corrigida. Eles estão marcados com `[V4.1 ...]` no código e descritos em `CHANGELOG_V41.md`. O resto do contrato v4 vale sem mudança.

## Contexto e decisões do usuário (fechadas)
- O pacote v3 (`/home/claude/sab/v3_zip/`) é idêntico ao v2. O v4 parte dele: cópias de trabalho em `/home/claude/sab/v4/`.
- Decisões do usuário em 20/10/2026:
  1. **Treino da matriz GFS: só GFS v16.** O v16 entrou em 22/03/2021 às 12 UTC, então a primeira rodada 00Z v16 é **2021-03-23 00Z**. O fim é o último dia com BR-DWGD, 2025-12-31.
  2. **Faixas de prazo: todos os dias de cada faixa.** L1 = {1}; L2a5 = {2,3,4,5}; L6a10 = {6,...,10}; L11a15 = {11,...,15}.
  3. **Pixels de borda do histórico: máscara de qualidade aplicada na leitura.** A trava do histórico NÃO é aberta.
  4. Motor: só rodadas 00Z completas; o último dia incompleto fica sem dado nas bandas que dependem dele; marca de confiança por prazo.
- O pacote será montado, auditado e depois reconferido por outro assistente. Por isso, toda mudança precisa ser rastreável.

## Material de referência (leia o que for do seu escopo)
- Relatórios de revisão com o código proposto por item: `/home/claude/sab/entrega/revisoes/revisao_03_04_matriz_gfs.md`, `revisao_05_motor.md`, `revisao_06_painel.md`, `revisao_02_07_08.md`.
- Catálogo: `/home/claude/sab/entrega/catalogo_melhorias_SAB.csv`.
- Auditoria 08 original: `/home/claude/sab/auditoria/` (LOG_COMPLETO.txt e CSVs).
- Auditoria complementar J, feita pelo usuário: script `/root/.claude/uploads/22d161fd-7b68-5ad7-86d3-02156273abdf/56b7675b-auditoria_complementar_J.py` e resultados em `/home/claude/sab/auditoria_J/`. Principais números:
  - J1: classes de pixel iguais nos 7 dias de 1961 a 2025:
    - A (SAB = BR-DWGD): 70.364 pixels;
    - B (BR-DWGD existe mas foi descartado; ERA5-Land mascarado em 100% deles): 204;
    - C (sem BR-DWGD, preenchido com ERA5): 1.109 (soma ponderada); [V4.1 K1d] só 48 têm o centro no Brasil, e cerca de 1.060 têm o centro fora (o antigo "cerca de 880" era estimativa por área);
    - D (BR-DWGD sem SAB): 73.
  - J3: homônimos no GAUL: Amazonas (Colômbia, Peru, Venezuela); Distrito Federal (México); "Para" (Suriname). O painel tira os acentos, então "Pará" vira "Para".
  - J4: percentis exatos por amostragem. O fator de chuva da matriz GFS V1 em julho tem p95 de 13,3 e p99 de 59,2.
  - J5: Tmax máxima nacional média de 44,1 °C nos dias GFS contra 41,2 °C nos dias ERA5. Há salto de 41,7 para 44,1 °C na emenda (06/10 → 07/10). Em 4 dias a máxima passa do recorde nacional de 44,8 °C.

## Regras de trabalho
1. Edite SÓ os arquivos do seu escopo, em `/home/claude/sab/v4/`. Não toque nos de outros escopos.
2. Mudança mínima e cirúrgica. Tudo o que não está na sua lista fica byte a byte igual. Marque cada trecho alterado ou novo com o comentário `[V4]` (em Python `# [V4] ...`, em JS `// [V4] ...`), com o ID do item (por exemplo `# [V4 M03-03]`).
3. Atualize o cabeçalho de cada arquivo com um bloco "MUDANÇAS V4 (20/10/2026)" que liste os itens.
4. Não invente APIs do Earth Engine. Se não tiver certeza de uma assinatura, use a forma que o próprio código já usa, ou deixe uma checagem em tempo de execução com mensagem clara e marque `A CONFIRMAR` no comentário.
5. Validação obrigatória antes de terminar:
   - `python3 -m py_compile` e `python3 -m pyflakes` nos .py; `node --check` nos .js;
   - teste offline (Python puro, sem `ee`) de toda lógica nova que não dependa do Earth Engine: datas, faixas, regras, arredondamento etc. Guarde os testes em `/home/claude/sab/v4/testes/` com o nome `teste_<arquivo>.py` e rode-os;
   - releia o seu diff inteiro (`diff -u /home/claude/sab/v3_zip/<arq> /home/claude/sab/v4/<arq>`).
6. Entregável de cada agente: `/home/claude/sab/v4/CHANGELOG_<escopo>.md`. Para cada item: ID, arquivo:linhas novas, o que mudou, por quê (evidência), como verificar na execução, e o que ficou A CONFIRMAR. A resposta final ao coordenador é um resumo curto desse arquivo, com a lista de riscos.
7. Português do Brasil nas mensagens de log e nos comentários, no mesmo estilo dos scripts atuais.

## Contrato comum (nomes que vários arquivos usam)

### Matriz GFS V2.1 (gerada pelo 03, lida pelo 04, 05 e 08)
- Coleção: `projects/clima-492922/assets/SICSB_MATRIZ_GFS_V2` (o nome não muda; a coleção ainda não existe). Imagens `Matriz_GFS_MM`, de MM = 01 a 12.
- Bandas:
  - as 96 atuais, `{var}_{m|s}_{sicsb|gfs}_{fx}`, com var em pr, Tmax, Tmin, RH, u2, Rs e fx em L1, L2a5, L6a10, L11a15;
  - **4 novas**, `n_L1`, `n_L2a5`, `n_L6a10`, `n_L11a15` (Float32 com valores inteiros; mudado de Int16 na revisão para evitar falha de exportação por tipos mistos): número de pares válidos por pixel;
  - total de **100 bandas**.
- Propriedades obrigatórias:
  - `versao_matriz` = 'V2.1'
  - `modelo_gfs` = 'GFS v16'
  - `inicio_rodadas` = '2021-03-23'
  - `fim_dias` = '2025-12-31'
  - `mes_referencia` = MM (int)
  - `leads_L1` = '1'; `leads_L2a5` = '2,3,4,5'; `leads_L6a10` = '6,7,8,9,10'; `leads_L11a15` = '11,12,13,14,15'
  - `n_pares_L1`, `n_pares_L2a5`, `n_pares_L6a10`, `n_pares_L11a15`: total de pares dia×prazo válidos no Brasil, calculado no servidor
  - `metodo_pr` = 'soma_blocos_6h'; `metodo_rs` = 'media_blocos_6h'
  - `janela` = '(00Z,24Z] UTC do dia previsto; rodada 00Z de D-(L-1)'
  - `gerado_em` (ISO)
- Regras do treino:
  - só rodadas com `creation_time` às 00Z e data de criação ≥ 2021-03-23;
  - dia previsto ≤ 2025-12-31;
  - rodada completa no dia (todas as horas esperadas e 4 blocos de chuva);
  - GFS mascarado pela máscara diária do BR-DWGD.

### Máscara de qualidade (gerada pelo novo 01, lida pelo 06, 07 e 08)
- Asset: `projects/clima-492922/assets/SAB_MASCARA_QUALIDADE` (imagem única), na grade nativa do BR-DWGD: `EPSG:4326`, `crsTransform [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]`.
  - [revisão B-01/B-02] O asset exportado guarda a origem da própria região de exportação (alinhada à grade, deslocada por um número inteiro de pixels). O 01 e o Q1 da 08 conferem a grade por escala igual e deslocamento inteiro, não por igualdade do `crsTransform`.
- Banda `classe` (uint8). Fora do SAB a banda é mascarada.

| Valor | Classe |
|---|---|
| 1 | A: SAB igual ao BR-DWGD |
| 2 | B: BR-DWGD existe mas foi descartado (ERA5-Land mascarado; lagoas e estuários) |
| 3 | C dentro: sem BR-DWGD, com o centro do pixel no Brasil |
| 4 | C fora: sem BR-DWGD, com o centro do pixel fora do Brasil (borda) |

- Propriedades: `versao_mascara` = 'Q1', `dia_referencia` = '2001-01-15', `n_classe_1` a `n_classe_4`, `gerado_em`; [V4.1] `dias_classes` = '2001-01-15,1961-01-15,1981-07-01,2017-07-15,2025-01-15'.
- [V4.1 K1a] A, C e D vêm do dia de referência; B é a UNIÃO, nos 5 dias, dos pixels em que o BR-DWGD existe e o SAB difere dele (um pixel B pode coincidir com o BR-DWGD num dia seco de inverno). A conferência entre os dias exige só a estrutura (A+B, C e D) idêntica.
- [V4.1 K1d] Referências, só informativas: classe 3 perto de 48 e classe 4 perto de 1.060 (K1d corrigida: 48 pixels C com o centro no Brasil).
- Uso:
  - o painel EXCLUI dos pontos de extração os pixels de classe 4;
  - o painel informa a classe no CSV (coluna `Qualidade_Pixel`: 'A', 'B', 'C');
  - o 07 e o 08 relatam por classe.

### Motor V1.5 (05a/05b): propriedades novas e valores gravados
- `VERSAO_ALGORITMO` = 'V1.5'.
- Dias GFS:
  - `Confianca_Prazo` = 'alta' (prazo L de 1 a 5), 'media' (6 a 10) ou 'baixa' (11 em diante);
  - `janela_chuva_utc` = '00-24';
  - `fonte` = 'NOAA/GFS0P25 (rodada 00Z)';
  - `matriz_gfs` = 'SICSB_MATRIZ_GFS_V2 V2.1';
  - [V4.1 K7] `metodo_temp_gfs` = 'aditivo' ou 'variancia' (constante `METODO_TEMP_GFS`; padrão 'variancia' desde a revisão final de 20/10/2026, validado pela K8; o 08 confere que os dias GFS V1.5 foram gravados com ele). 'variancia' = m_sicsb + (x − m_gfs) × (s_sicsb / s_gfs), razão limitada a [0,5; 2], só Tmax e Tmin dos dias GFS.
  - [K9A] `metodo_ur_rs_gfs` = 'original' ou 'variancia' (constante `METODO_UR_RS_GFS`; padrão 'variancia' desde a revisão K9A de 20/10/2026; o 08 confere que os dias GFS V1.5 foram gravados com ele). 'variancia' = m_sicsb + (x − m_gfs) × (s_sicsb / s_gfs), razão limitada a [0,5; 2], na umidade relativa (limitada a [0, 100]) e na radiação (≥ 0) dos dias GFS; 'original' = UR aditiva e radiação com fator limitado a [0,5; 2]. O vento continua com o fator limitado a [0,5; 2]. O motor exige na matriz V2.1, além das 48 bandas de média, as 32 de desvio: Tmax, Tmin, RH e Rs × (sicsb, gfs) × 4 faixas.
  - [K9A] Um dia GFS gravado com `metodo_temp_gfs` ou `metodo_ur_rs_gfs` diferente da constante em uso é refeito na execução seguinte (`precisa_refazer_gfs`); dias sem a propriedade contam como 'aditivo' e 'original'.
  - [K11, 22/10/2026] `teto_razao_temp_gfs` = teto da razão dos desvios usado na Tmax e na Tmin do dia GFS: 2.0 nas faixas L1 e L2a5 (`RAZAO_DESVIO_MAX`) e 1.0 nas faixas L6a10 e L11a15 (`RAZAO_DESVIO_MAX_LONGO`); a UR e a radiação continuam com 2.0. Dia sem a propriedade conta como 2.0; um dia gravado com teto diferente do da sua faixa é refeito (`precisa_refazer_gfs` recebe a faixa). O 08 confere na D14 (`teto_razao_K11`).
- Dias ERA5: `fonte` = 'ECMWF/ERA5_LAND/DAILY_AGGR'; `janela_chuva_utc` = '00-24'.
- Dias definitivos futuros: `fonte` = 'BR-DWGD (ERA5 só onde falta)'; `janela_chuva_utc` = '12-12 (12 UTC D-1 a 12 UTC D)'.
- Valores de `versao`: os de sempre (`definitiva`, `provisoria_era5`, `provisoria_gfs`, `provisoria_gfs_incompleta`, `falha_latencia_gfs`).

### Painel 2026.10.4 (06)
- Colunas novas no CSV diário: `Qualidade_Pixel`, `Janela_Chuva_UTC`, `Confianca_Prazo` (vazia fora dos dias GFS).
- Colunas novas no CSV mensal: `N_Dias`, `Dias_no_Mes`, `Mes_Completo`.
- [revisão B-05] As colunas novas vão no FIM de cada CSV; as 30 colunas existentes mantêm nome, formato e posição.

### Auditoria 08 v4
- Ganha seções novas, todas somente leitura. Os códigos dos itens antigos não mudam.
