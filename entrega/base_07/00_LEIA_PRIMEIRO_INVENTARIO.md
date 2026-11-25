# LEIA PRIMEIRO: o que usar, o que guardar e o que aposentar (22/10/2026, 9h30)

## Resumo

- **Este zip é o único pacote válido**: `SAB_FINAL_v4_1_COMPLETO_2026-10-22.zip`. Todos os arquivos dele estão na versão final, depois da validação K11 e da auditoria 08 de 22/10/2026, 8h59 (45 ✅, 23 ℹ️, 3 ⚠️ explicadas e nenhum ❌).
- **Qualquer outro zip, pasta ou arquivo com nome parecido é antigo**, inclusive os que eu enviei antes, mesmo os de hoje cedo. Mova tudo isso para a pasta `SAB_ANTIGOS_NAO_USAR` (seção 3).
- **No dia a dia você roda só o 05b**, e o 02 uma vez por mês. Os demais scripts só rodam nas situações da última coluna da tabela 1.

---

## 1. Arquivos deste pacote (todos atuais)

| Arquivo | Para que serve | Onde | Grava? | Situação em 22/10/2026 | Quando rodar de novo |
|---|---|---|---|---|---|
| `01a_mascara_qualidade_SIMULACAO.py` | Confere a máscara de qualidade dos pixels (classes A, B, C e D) | Colab | Não | Rodado em 20/10 | Só se a auditoria 08 acusar o item Q1 |
| `01b_mascara_qualidade_GRAVACAO.py` | Grava o `SAB_MASCARA_QUALIDADE` | Colab | Sim (1 imagem) | Gravado em 20/10; Q1 ✅ (A 70.633, B 301, C 48 + 1.064) | Não precisa |
| `02_auditoria_roni_cpc.py` | Baixa o RONI oficial do CPC/NOAA, confere e grava o `RONI_CPC_v6` | Colab | Sim | 21/10: 920 estações; H5 ✅ | **Todo mês, depois do dia 5** |
| `03_matriz_gfs_v2_1.py` | Calibração GFS (NOAA) × BR-DWGD: grava a matriz `SICSB_MATRIZ_GFS_V2` (versão V2.1) | Colab | Sim (12 imagens) | 20/10; E6 ✅ | Só quando o GFS v17 entrar |
| `04_conferencia_matriz_gfs.js` | Conferência visual da matriz V2.1 contra a V1 | Code Editor | Não | Aprovada em 20/10 | Junto com um 03 novo |
| `05a_motor_sab_v1_5_SIMULACAO.py` | Motor V1.5 em simulação (mostra o que faria) | Colab | Não | 22/10, 8h39: PRÉVIA 6 ✅ | Antes de qualquer mudança no motor |
| `05b_motor_sab_v1_5_GRAVACAO.py` | Motor V1.5: grava os dias de 2026 (ERA5 e previsão GFS de 15 dias) | Colab | Só dias de 2026 | 22/10, 8h42: 16 dias gravados com a rodada de 22/10 | **Todo dia, depois das 10h** |
| `06_painel_sab_2026_10_4.js` | Painel (mapa, CSVs diário e mensal, ENSO) | Code Editor | Não | Em uso; CSVs conferidos em 22/10 | É o painel; substitui o antigo (seção 3.2) |
| `07a_normais_CONFERIR_1991_2020.py` | Confere as normais e os limiares 1991–2020 já gravados | Colab | Não | 22/10: tudo ✅ | Só se algo mudar na pasta Baselines |
| `07b_normais_CONFERIR_1961_1990.py` | Confere as normais e os limiares 1961–1990 já gravados | Colab | Não | 22/10: tudo ✅ | Idem |
| `08_auditoria_completa_SAB.py` | Auditoria completa, somente leitura | Colab | Não | 22/10, 8h59: nenhum ❌ | Antes e depois de qualquer mudança; por volta de 15/11 (J5c) |
| `validacoes/K8_validacao_quantis.py` | Validação: método da Tmax/Tmin da previsão | Colab | Não | 20/10: escala de variância adotada | Quando o GFS v17 entrar |
| `validacoes/K9_validacao_todas_variaveis.py` | Validação: todas as variáveis da previsão (2021–2025) | Colab | Não | 20/10 | Substituída na prática pela K9A |
| `validacoes/K9A_validacao_ampliada.py` | Validação: todas as variáveis, 2015–2025 | Colab | Não | 20/10: UR e radiação pela escala de variância | Quando o GFS v17 entrar |
| `validacoes/K10_diagnostico_tmax_recorde.py` | Diagnóstico: Tmax da previsão acima do recorde | Colab | Não | 22/10, 8h07: achou os 45,24 °C de Casa Nova-BA | Se a J5a da 08 der ⚠️ |
| `validacoes/K11_validacao_razao_desvios_prazos_longos.py` | Validação: teto da razão dos desvios nos prazos de 6 dias em diante | Colab | Não | 22/10, 8h30: TROCAR; já aplicado no 05a e no 05b | Quando o GFS v17 entrar |
| `validacoes/K12_simulacao_download_estadual.py` | Simulação: download do CSV diário de um ano do estado inteiro (erro 503 do Paraná) | Colab | Não | 22/10, 15h01: ano do Paraná completo em 12 links de 60.000 linhas; números com ponto aplicados no 06 | — |

**Documentos**
- `00_LEIA_PRIMEIRO_INVENTARIO.md`: este arquivo.
- `00_ROTEIRO_FINAL.md`: passo a passo clique a clique (Partes 2 a 6) e decisões e notas para a tese (Parte A).
- `SPEC_V4.md`: contrato técnico (bandas e propriedades de cada dia).
- `CHANGELOG_*.md`: histórico das mudanças. O mais recente é o `CHANGELOG_REVISAO_K9A.md` (seções 1 a 17); quando houver divergência, ele prevalece sobre os outros.
- `testes/`: testes automáticos que eu rodo antes de cada entrega. Você não precisa rodá-los.
- `SHA256SUMS.txt`: impressão digital de cada arquivo.

**Como reconhecer a versão atual de cada código:**
- **05a e 05b:** a saída mostra, logo no início, as três linhas
  - `Correção da Tmax/Tmin nos dias GFS: variancia`;
  - `Correção da UR e da radiação nos dias GFS: variancia`;
  - `Teto da razão dos desvios da Tmax/Tmin: 2.0 nos prazos 1 a 5 e 1.0 do 6 em diante`.

  Se faltar alguma delas, o arquivo é antigo.
- **06 (painel):** a linha 3 do código termina com `REVISÃO FINAL DE 22/10/2026 (ENSO explicado para leigos,`. No painel, o item B se chama "B. Como foi o clima em meses de El Niño, La Niña ou neutro". Logo abaixo, uma linha começa com `// REVISÃO DE 22/10/2026, 18h30`: é a versão com números com ponto, 1 arquivo por ano e linha do CSV mais leve.
- **08:** a linha 2 termina com `REVISÃO FINAL DE 22/10/2026`, e a D14 tem o critério `teto_razao_K11`.
- **Os demais:** basta o nome do arquivo estar igual ao da tabela e vir deste zip.

---

## 2. As calibrações: o que cada uma é, de onde veio e se mudou

| Calibração (asset) | O que corrige | Quem criou | Mudou neste trabalho? | O que fazer |
|---|---|---|---|---|
| `SICSB_1986_2025` (12 imagens `Matriz_Clima_MM`) | **BR-DWGD × ERA5-Land**: leva o ERA5 ao padrão do BR-DWGD, mês a mês, com os pares de 1986 a 2025. É usada nos dias de 2026 que vêm do ERA5 e na ETo de referência | Seu script original, anterior a este trabalho | **Não.** Só leitura. Auditada na seção E da 08 (E1 ✅; E2 ℹ️: correção mediana Tmax +1,87 °C, Tmin −0,62 °C) | **Manter.** Nunca recriar: os dias de 2026 dependem dela |
| `SICSB_SOLO_2015_2025` (12 imagens `Matriz_Solo_MM`) | **SMAP × ERA5-Land**: umidade do solo e escoamentos | Seu script original | **Não.** Só leitura | **Manter.** As ⚠️ E3-rsup e E3-rsub (fator acima de 5 em parte dos pixels) são limitação conhecida, para registrar na tese |
| `SICSB_MATRIZ_GFS` (V1) | **GFS (NOAA) × BR-DWGD**, versão antiga: usava só os prazos 1, 3, 8 e 13 e corrigia só a média, o que deixou a Tmax da previsão acima do recorde em 4 de 26 dias (roteiro, Parte A, notas 6 e A.1) | Seu script original | Substituída pela V2.1 no motor V1.5 | **Manter, sem usar.** A 04 e a 08 comparam a V2.1 com ela, e o desfazer da Parte 5 do roteiro precisa dela |
| `SICSB_MATRIZ_GFS_V2` (V2.1) | **GFS v16 (NOAA), só rodadas 00Z, × BR-DWGD**, por mês e faixa de prazo. Tmax e Tmin pela escala de variância (teto da razão 2 nos prazos 1 a 5 e 1 do 6 em diante, K11); UR e radiação também pela escala de variância (K9A); chuva por fator com teto 5; vento com fator de 0,5 a 2 | `03_matriz_gfs_v2_1.py` deste pacote | **É a nova** | **Em uso** |
| `RONI_Calibrado_Sazonal_1950_1980` | RONI antigo: a série do CPC até 1980 e a réplica OISST do seu "Código 1" depois | Seu "Código 1" (AUDITORIA CIENTÍFICA + COMPARAÇÃO TRIPLA DO RONI) | Substituído pelo `RONI_CPC_v6` | **Manter, sem usar.** Serve só para a comparação H4 da 08; o painel não lê mais |
| `RONI_CPC_v6` | RONI oficial do CPC/NOAA (ERSSTv6), 1950 até hoje | `02_auditoria_roni_cpc.py` | **É o novo** | **Em uso**; atualizar todo mês pelo 02 |
| `SAB_MASCARA_QUALIDADE` | Classe de cada pixel (A, B, C, D) | `01b` | **É a nova** | **Em uso** |
| `Baselines` (48 imagens B1.1) | Normais e limiares de 1961–1990 e 1991–2020 | Seu script de baselines, anterior a este trabalho | **Não** | **Manter.** Conferidas pelo 07a e pelo 07b em 22/10 |

**Sobre os scripts originais que criaram as matrizes (BR-DWGD × ERA5, solo, GFS V1) e as Baselines:** eles não fazem parte deste pacote porque **não precisam de atualização**. Os assets que eles criaram estão fixos e foram auditados. Guarde esses scripts como registro do método, para a metodologia da tese, mas **nunca os rode de novo**: rodar recriaria as matrizes ou as normais, e todo o resto depende delas. O mesmo vale para o `Código baselines.txt`.

---

## 3. O que fazer com o que é antigo

### 3.1 No seu computador

1. Crie a pasta `SAB_ANTIGOS_NAO_USAR` e mova para ela, sem apagar:
   - **todos os zips anteriores:** `SAB_correcoes_2026-10-19_v2` e `_v3`, `SAB_FINAL_2026-10-20`, `SAB_FINAL_v2`, `v3` e `v4_2026-10-20`, `SAB_FINAL_v4_1_REVISADO_2026-10-20`, `SAB_FINAL_v4_1_K9A_2026-10-20`, o `SAB_FINAL_v4_1_K11_2026-10-22` (de hoje, 8h36; este zip o substitui) e o `Downloads.rar`;
   - **as pastas avulsas** `atualizados_K9A` e `codigos_22-10`;
   - **arquivos soltos que eu enviei:** `01_validacao_quantis_K8.py` (é o atual `validacoes/K8_validacao_quantis.py`), `K9_validacao_todas_variaveis.py`, `K9A_validacao_ampliada.py`, `K10_...` e `K11_...` soltos, `K9_extra_validacao_cruzada.csv`, os `CHANGELOG_*.md` soltos, `auditoria_K_decisoes.py`, `auditoria_K1d_corrigida.py`, `auditoria_complementar_J.py`, `auditoria_SOMENTE_SECAO_C.py` e `_F.py`, `Auditoria_Cruzamento_SAB_v3.pdf` e `enso_novo.js` (já está dentro do painel 06);
   - **versões antigas dos scripts**, se ainda as tiver: `01_prechecagem_bases.py`, `03_matriz_gfs_v2.py` (sem o `_1`), `05_motor_sab_v1_4.py`, `05a/05b_motor_sab_v1_4_*`, `06_painel_sab.js`, `06_painel_sab_2026_10_3a.js`, `07a_inventario_baselines.js`, `07b_normais_SIMULACAO.py`, `07c_normais_PILOTO.py`, `07d/07e_normais_EXPORTAR_*.py`, `07f_normais_CONFERIR_1961_1990.py`, `GUIA_CLIQUE_A_CLIQUE.md` e o `00_ROTEIRO` antigo;
   - **os seus originais:** o motor V1.3, o painel antigo, o "Código 1" do RONI, os scripts das matrizes e o `Código baselines.txt`.
2. Crie a pasta `SAB_RESULTADOS_TESE` e **guarde nela, sem apagar nunca**, as saídas que são evidência para a tese:
   - todos os `auditoria_SAB_*.zip` (o mais importante é o de 22/10, 8h59);
   - `validacao_K9_*.zip`, os resultados da K9A, `validacao_K11_20261022_0830.zip`, `K10_diagnostico_tmax.csv`;
   - os CSVs de RONI do 02 e os CSVs do painel que você conferiu.
3. Pode apagar a pasta `SAB_ANTIGOS_NAO_USAR` depois da defesa, não antes: ela é a prova de como o sistema era.

### 3.2 No Code Editor do Earth Engine

| Script | O que fazer |
|---|---|
| Script do painel (o que você usa ou publicou) | Precisa conter o **06 deste zip**. Abra, aperte Ctrl+A, cole o 06 e salve. Confira a linha 3 (seção 1). |
| `BACKUP_PAINEL_2026_10_2` | **Não apague antes da defesa**: é a única forma de desfazer o painel (roteiro, Parte 5). Para evitar confusão, renomeie para `ANTIGO_NAO_USAR_painel_2026_10_2` (botão direito → Rename). Nunca publique este. |
| Outras cópias antigas do painel (10.2, 10.3, 10.3a ou o 06 de 20/10) | Pode apagar (botão direito → Delete), ou renomear com `ANTIGO_NAO_USAR_` na frente |
| `04_conferencia_matriz_gfs` | Pode manter; não atrapalha |
| App publicado, se existir | Em **Apps**, o App tem de apontar para o script do painel com o 06 (roteiro, 6.8). Depois de colar o 06, publique de novo |

### 3.3 No Colab e no Drive

| Item | O que fazer |
|---|---|
| Notebook do motor V1.3 e `BACKUP_MOTOR_V1.3` | **Nunca mais rode.** Ele refaria os dias de 2026 como V1.3, com a matriz antiga. Renomeie os dois para `NAO_RODAR_motor_V1.3`. Mantenha o backup só para o desfazer (roteiro, Parte 5). |
| Notebook do 05b (`05_motor_v15`) | É o do dia a dia. Confira se a célula tem o 05b deste zip: a saída tem de mostrar a linha do teto (seção 1). |
| Notebooks das etapas (01a, 01b, 02, 03, 07, 08, K8 a K11) | Podem ficar. Ao rodar de novo, apague a célula e cole o arquivo deste zip. |
| Pasta `cache_validacao_K9A` no Drive (`K9A_dados_brutos.parquet`) | **Manter.** A K11 usou esses dados, e eles servem para refazer as validações quando entrar o GFS v17. |
| CSVs exportados para o Drive | Nada |

### 3.4 No Earth Engine (aba Assets)

**Não apague nenhum asset.** Os 10 que existem hoje estão todos em uso ou servem de referência:

| Asset | Situação |
|---|---|
| `SAB_V1` | Em uso: 24.051 dias; 1961–2025 travado, 2026 em V1.5 |
| `SAB_V1_TMP` | Passagem do motor; fica vazia |
| `SAB_MASCARA_QUALIDADE`, `RONI_CPC_v6`, `SICSB_MATRIZ_GFS_V2` | Em uso (novos) |
| `SICSB_1986_2025`, `SICSB_SOLO_2015_2025`, `Baselines` | Em uso (originais, fixos) |
| `SICSB_MATRIZ_GFS` (V1), `RONI_Calibrado_Sazonal_1950_1980` | Sem uso; referência para a auditoria e para o desfazer |
| `RONI_CPC_v6_ANTERIOR` (se aparecer) | Sobra automática do 02; não apague à mão, o próprio 02 cuida dela |

---

## 4. Rotina daqui em diante

| Quando | O quê |
|---|---|
| Todo dia, depois das 10h | Reiniciar a sessão do Colab e rodar o **05b** |
| Todo mês, depois do dia 5 | Reiniciar a sessão e rodar o **02** |
| Por volta de 15/11/2026 | Subir o `J5_tmax_2026.csv` da auditoria de 22/10, 8h59, com o nome `/content/J5_previsao_anterior.csv`, e rodar o **08** (a J5c compara a previsão com o ERA5 dos mesmos dias) |
| Se a J5a der ⚠️ | Rodar a **K10** e me enviar |
| Quando o GFS v17 entrar | Rodar o **08** e me enviar (refazer a matriz e as validações só no período do v17) |
| Quando o BR-DWGD cobrir 2026 | Me pedir a V3 (o motor avisa com `⏸️ BR-DWGD já cobre até ...`) |

Regras que continuam valendo: um script de cada vez; reiniciar a sessão antes de cada script que grava (01b, 02, 03 e 05b); o histórico de 1961 a 2025 continua travado (`PROTEGER_HISTORICO = True`).
