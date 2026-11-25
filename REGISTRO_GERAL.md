# Registro geral do SAB: do início do código às últimas atualizações

**SAB: Banco de Dados Agrometeorológicos Diários do Brasil (1961–2026)**. Projeto Earth Engine `clima-492922`.
Este registro junta, num lugar só, o que foi feito, por quê, como foi conferido e onde está o detalhe. A parte de
cima é escrita à mão a cada etapa; o apêndice do fim (situação das rotinas, resultados das validações e a lista de
todas as mudanças do repositório) é refeito sozinho pela fila da conferência (`registro/gerar_registro.py`).

## 1. O que é o SAB, em uma página

- **16 variáveis diárias** em grade de 0,1° (~11 km) sobre o Brasil: chuva, Tmax, Tmin, umidade relativa, VPD, ETo
  (Penman-Monteith FAO-56), radiação solar, vento a 2 m, ET real, transpiração, temperatura do solo e da folha, umidade
  do solo (0–5 e 0–100 cm), escoamento superficial e subsuperficial. A leitura acrescenta amplitude térmica, déficit
  e chuva efetiva.
- **Três períodos, três fontes:**
  - **1961–2025, histórico (definitivo e travado):** as 8 variáveis do núcleo vêm do **BR-DWGD** (Xavier et al.;
    estações interpoladas); as outras 8 vêm do **ERA5-Land**, com correção de leitura do solo e do escoamento pelo SMAP.
    Gravado pela V1.0 do motor entre 24/08 e 26/09/2026; nunca é regravado (`PROTEGER_HISTORICO`).
  - **2026, provisório:** ERA5-Land **calibrado** para parecer o BR-DWGD (correção na média por pixel e mês;
    umidade relativa por mapeamento de quantis; teto da chuva; radiação limitada ao céu claro). Motor V1.7 desde 25/11.
  - **Previsão, 16 dias:** GFS (NOAA, rodada 00Z), calibrado pela matriz `SICSB_MATRIZ_GFS_V2`.
- **Máscara de qualidade** (`SAB_MASCARA_QUALIDADE`): A (BR-DWGD puro), B (pixel do litoral/água onde o valor
  gravado não vinha do BR-DWGD; corrigido na leitura), C_interior, C_borda (não entregue).
- **Como o usuário recebe:** o painel (app do Earth Engine, link na hora) ou o e-mail (formulário → planilha + Apps
  Script → GitHub `sab-pedidos` → `sab_pedido.py` → CSV/xlsx no Drive). Os dois caminhos fazem a mesma conta; a **K16**
  prova isso a cada mudança.
- **Gravação diária:** GitHub `sab-motor` (`rodar_motor.py` confere o SHA-256 do motor e as travas antes de rodar).

## 2. Linha do tempo

| Quando (2026) | O que aconteceu | Onde está o detalhe |
|---|---|---|
| até ago | Códigos originais: motor V1.0 (histórico), V1.1 e V1.3; climatologia `SICSB_1986_2025` (O2); solo `SICSB_SOLO_2015_2025` (O4); matriz GFS V1 (O3); normais/Baselines (O5); RONI calibrado (O6) | entrega, pasta `08_Scripts_originais_somente_registro` |
| 24/08–26/09 | Histórico 1961–2025 gravado pela V1.0 (23.741 dias) | `00_LEIA_PRIMEIRO.md`, seção 2b |
| 20/10 | **Pacote v4**: máscara de qualidade (01), RONI oficial do CPC (02), matriz GFS V2.1 (03/04), motor V1.5 (05), painel 2026.10.4 (06), normais (07), auditoria completa (08). Revisões independentes A e B; **v4.1** (escala de variância na Tmax/Tmin do GFS, K7/K8); **K9A** (UR e radiação do GFS pela variância) | `CHANGELOG_01_08`, `_02_07`, `_03_04`, `_05`, `_06`, `_V41`, `_REVISAO_AB`, `_REVISAO_FINAL`, `_REVISAO_K9A`; `00_ROTEIRO_FINAL.md` |
| 20–22/10 | Auditorias **K1 a K11** (máscara, CHIRPS, normais, GFS, razão dos desvios nos prazos longos) | `00_ROTEIRO_FINAL.md`, parte A.3 |
| fim de out | **K12 a K15**: link único, limites do link na hora (~100 mil linhas), números com ponto decimal, grampo termodinâmico (K14) | `CHANGELOG_06.md` |
| 01/11 | Atualização do pacote v41 | `00_ATUALIZACAO_2026_11_01.md` |
| 03/11 | **K17** (validação final dos dados: histórico = V1.0 recalculada; 2026 = V1.5; chuva × CHIRPS r = 0,91 histórico, 0,88 em 2026), **K18** (revisão do ERA5-Land desde jul/2017; pixels B com chuva 4,8 mm/dia diferente do BR-DWGD), **K19/K19b** (controle físico de 1,67 bilhão de pixel-dias; homogeneidade; **2026: chuva × CHIRPS fora do padrão em MS, PI e GO**) | `00_LEIA_PRIMEIRO.md`, seção 9 |
| 04/11 | **Etapa 1, correção na leitura**: pixels B com o núcleo do BR-DWGD; ET real ≤ ETo; radiação dos C ≤ céu claro. Painel 2026.11.1 e `sab_pedido.py` 2026.11.03; **K20** e **K16 v4** | seção 10 do `00_LEIA` |
| 08–09/11 | **Etapa 2, motor V1.6** (UR por quantis, radiação ≤ céu claro, teto da chuva), aprovado na **K21 v4** (treino 1986–2015, teste 2016–2025, regra fixada antes); no ar em 09/11. **K23 v2** e **K24 v1** | `CHANGELOG_05.md` |
| 15/11 | GitHub `sab-pedidos` PR #1 (manutenção de versões); Apps Script `Codigo.gs` 2026.11.15 (Versão 7, teto de 30 pedidos/dia); começa a **K26** (varredura total, rodadas 2, 3, 4) | `automacao_email/CHANGELOG_EMAIL.md` |
| 16–18/11 | K26 rodadas 5 (1961–1970), 7 (1981–1990, v1.8) e 8 (1991–2000). **Pedido de uma variável só saía vazio**: corrigido (`sab_pedido.py` 2026.11.18, PRs #2 a #6); aviso do escoamento no dicionário (2026.11.19 / painel 2026.11.4); **K16 v6** aprovada; pesquisa da **previsão estendida** (temperatura com acerto até 90 dias; chuva não) e **piloto** de Tmin/Tmax (dias 3 e 17) | `00_LEIA`, atualização de 18/11; `pesquisa/resultados/RESULTADOS.md` |
| 22/11 | **K26 fechada (1961–2026)**: 1,7 bilhão de pixel-dias; 11 de 20 testes físicos sem nenhuma violação; escoamento > chuva em 14% dos pixel-dias (modelo × observação). **Radiação impossível vazia na leitura** (Rs < 3% do topo da atmosfera → Rs, ETo e déficit vazios): `sab_pedido.py` 2026.11.22 (PR #7) e painel 2026.11.5; **K16 v7.1** aprovada | `K26_FINAL_1961_2026/K26_RESULTADO_FINAL.md` |
| 24/11 | Causa do Rs = 0 no litoral (ERA5-Land com 0 no mar em 04–20/03 e 23/09–08/10/2026); **motor V1.7** (Rs 0 vira vazio; PR #3 do `sab-motor`); **rotinas automáticas** (PR #8: saúde do banco, RONI, K26 mensal, piloto, painel `rotinas/PAINEL.md`); RONI de novembro (ASO = +2,0 °C); **K22 v2** e **K24 v1** registradas | `00_LEIA`, seções de 24/11 |
| 24–25/11 | **Validações extras e conferência final automática** (PRs #9 e #10): acerto da previsão GFS por prazo (rotina diária); 2026 × CHIRPS e MODIS; solo, folha e ET real × SMAP e MODIS; escoamento × vazão dos rios (CAMELS-BR); teste das 16 variáveis (método de 2026 em 2021–2025; 2026 × GLDAS-2.1); histórico por década × TerraClimate e CHIRPS; tudo também por mês do ano. A fila `rotinas/conferencia/fila.py` roda sozinha e refaz a K26 de 1961 até a previsão | `rotinas/conferencia/CONFERENCIA_FINAL.md` e a seção 4 abaixo |

## 3. Regras que valem sempre

1. **Audite antes de mudar e simule antes de gravar** (01a antes do 01b, 05a antes do 05b). A K16 vem antes de abrir
   ao público qualquer mudança de cálculo.
2. **O histórico 1961–2025 nunca é reescrito.** Correções do histórico são feitas **na leitura** (painel e e-mail).
3. **Regra de decisão fixada ANTES de rodar** em toda pesquisa que pode mudar o banco (K21, escoamento, solo/folha,
   método de 2026, histórico por década): o resultado não muda a regra.
4. **Toda mudança no cálculo do painel exige a mesma mudança no `sab_pedido.py` e uma K16 nova.**
5. Credenciais só nos segredos do GitHub e nas propriedades do Apps Script; nunca em arquivo, print ou conversa.

## 4. Validações contra referências de fora (o que cada uma mediu)

| Variável | Referência independente | Período | Resultado |
|---|---|---|---|
| Chuva | CHIRPS | histórico e 2026 (K17) | r = 0,91 (viés +0,2%) no histórico; 0,88 (−0,4%) em 2026 até out |
| Chuva | CHIRPS por região | jan–set/2026 × 2024 (régua) | 2024: todas as regiões a ±7%. **2026: Centro-Oeste −21%, Nordeste −16%** (Norte −1%, Sudeste −3%, Sul +4%); desenho espacial 0,83 (régua 0,86). Confirma o sinal da K19 (MS, PI, GO). Teste decisivo: método de 2026 em 2021–2025 e 2026 × GLDAS |
| Tmax (anomalia) | MODIS LST (Terra) | set–out/2026 × 2024 | desenho do calor 0,61–0,70 em 2026 (régua 0,33–0,38); nível do MODIS não serve (deriva da órbita do Terra) |
| Umidade do solo 0–5 cm | SMAP L3 | 2016–2021 | anomalias r = 0,89 (mediana das regiões); Norte 0,42 → mantém |
| Temperatura da folha | MODIS LST de dia (Aqua) | 2016–2021 | r = 0,80 → mantém (nível ~7 °C abaixo: horário diferente) |
| Temperatura do solo | MODIS LST de noite (Aqua) | 2016–2021 | r = 0,80 → mantém |
| ET real | MODIS MOD16 | 2016–2021 | r = 0,47 (Norte 0,06) → **mantém como índice, com aviso** |
| Escoamento total | vazão observada de 512 bacias (CAMELS-BR, ANA) | 1981–2018 | KGE mediano 0,31, viés −35% (o SAB fica abaixo do rio); nenhum dos 3 métodos alternativos passou nas 4 condições → **o atual fica, com aviso por região** |
| As 16 | o próprio método de 2026 em 2021–2025 (× BR-DWGD) e GLDAS-2.1 (NASA) com régua 2022–2024 | 2021–2026 | na fila (resultado no apêndice) |
| 10 variáveis | TerraClimate (e chuva × CHIRPS) por década | 1961–2025 | na fila (resultado no apêndice) |
| Previsão GFS 1–15 dias | ERA5 do dia, com a persistência como base | diária desde 24/11 | primeira medida por prazo depois de ~1 semana de fotografias |

## 5. Onde está cada coisa

- **Código em uso e versões:** `00_LEIA_PRIMEIRO.md` da entrega (seção 2) e os cabeçalhos de cada arquivo (cada mudança
  marcada com a versão e a data).
- **Changelogs:** `07_Base_de_desenvolvimento_e_testes/CHANGELOG_*.md` e `automacao_email/CHANGELOG_EMAIL.md`.
- **Resultados das auditorias K:** `07_…/validacoes/resultados/` (um diretório por execução).
- **Rotinas automáticas:** `rotinas/PAINEL.md` (situação de cada uma) e `rotinas/resultados/`.
- **Replicação e auditoria das validações:** `pesquisa/METODOS_REPLICACAO.md` (fontes, agregação, unidades, fórmulas,
  regras) + `pesquisa/METRICAS_COMPLETAS.csv.gz` (todas as métricas, região × período × mês) +
  `pesquisa/DADOS_PAREADOS.csv.gz` (os valores mensais de que saíram).
- **Pesquisas e validações novas:** `pesquisa/` (protocolos `PROTOCOLO*.md`, códigos e `resultados_*`).
- **Conferência final:** `rotinas/conferencia/CONFERENCIA_FINAL.md` (e os LOG em `rotinas/conferencia/logs/`).
- **Motor:** GitHub `sab-motor` (`05a`/`05b` de cada versão, `SHA256_MOTOR.txt`, `rodar_motor.py`).

## 6. Ressalvas para a tese (o que os dados não fazem)

- O ERA5-Land do Earth Engine foi revisto desde jul/2017 (variáveis acumuladas; diferença desprezível, não corrigida).
- O início da série (1961 a ~1975) se afasta do ERA5 em UR, Tmin e chuva (rede de estações da época).
- O escoamento é do modelo, não da observação: não bate dia a dia com a chuva e fica abaixo da vazão dos rios.
- ET real ≤ ETo é escolha do modelo; ET real é índice (concorda pouco com o MOD16 no Norte).
- 2026 é provisório até o BR-DWGD cobrir 2026; a chuva de 2026 está sob investigação no Centro-Oeste e no Nordeste.
- O vento do BR-DWGD vem de poucas estações.

---

# Apêndice automático (refeito em 25/11/2026 04:01, Brasília)

## A. Situação das rotinas automáticas (de `rotinas/PAINEL.md`)

| Rotina | Quando roda | Última execução | Situação | Resumo |
|---|---|---|---|---|
| Saúde do banco (motor gravou?) | toda segunda-feira, 14h29 | 24/11/2026 20:27 | ✅ | 343 dias de 2026 (319 ERA5 até 2026-11-15, 24 GFS até 2026-12-09); dia 2026-11-24 gravado há 11 h; versões {'V1.6': 343}; histórico intocado |
| RONI do mês (02_auditoria_roni_cpc.py) | todo dia 11, 10h23 | 24/11/2026 21:14 | ✅ | asset RONI_CPC_v6 regravado e conferido (921 estações) |
| K26, rodada 1 (2026 inteiro, só leitura) | todo dia 15, 15h41 | 24/11/2026 20:56 | 👀 | 343 dias de 2026 (até 2026-12-09); itens: A1 OK, B ATENCAO, C FALHA, G FALHA, H OK |
| Acerto da previsão GFS (1 a 15 dias) | todo dia, 16h13 | 24/11/2026 22:16 | ✅ | fotografia de 2026-11-24: 24 dias GFS (2026-11-16 a 2026-12-09) e a persistência (2026-11-15) |
| Conferência final (validações, escoamento e K26 de 1961 até a previsão) | de 2 em 2 horas, 10h17 a 20h17, até a fila acabar (depois desliga sozinha) | 25/11/2026 03:57 | ⚠️ | 0 de 1 tarefas prontas; quebraram: historico; TERMINOU: leia o CONFERENCIA_FINAL.md |
| Piloto da previsão estendida (Tmin e Tmax) | dias 3 e 17, 08h17 | 24/11/2026 20:19 | ✅ | 1 emissão(ões); a última em 2026-11-16 |

## B. Resultado de cada validação

Cada bloco é a cópia do arquivo de resultado no momento em que este registro foi refeito.

### Conferência final (fila)

Arquivo: `rotinas/conferencia/CONFERENCIA_FINAL.md`

#### Conferência final do SAB (1961 até a previsão)

Atualizado em 25/11/2026 03:57 (Brasília) pela fila automática (`rotinas/conferencia/fila.py`). **Todas as tarefas terminaram.**

| Tarefa | Situação | Tentativas | Quando | Resultado |
|---|---|---|---|---|
| O histórico 1961-2025, década por década, contra TerraClimate e CHIRPS | ❌ quebrou 3 vezes | 3 | 25/11 03:57 | pesquisa/resultados_historico/RESULTADOS.md |

O LOG de cada tarefa fica em `rotinas/conferencia/logs/<tarefa>.txt`. ❌ = me mande esse LOG.

### 2026 × CHIRPS e MODIS

Arquivo: `pesquisa/resultados_2026/RESULTADOS.md`

#### 2026 (ERA5 calibrado) contra referências independentes do ERA5

Gerado com: CHIRPS (pêntadas) até 2026-09-26, MODIS até 2026-11-09, SAB ERA5 até 2026-11-15. A régua é 2024, quando o SAB é o BR-DWGD (observado): 2026 está bom se concordar com os satélites tanto quanto 2024 concorda.

##### Chuva mensal: SAB x CHIRPS

Meses 1 a 9; viés do TOTAL do período (os meses secos não pesam mais que os chuvosos).

| Ano | Região | Total SAB (mm) | Total CHIRPS (mm) | Viés do SAB (%) | Correlação espacial média (Brasil) |
|---|---|---|---|---|---|
| 2026 | Norte | 1629 | 1649 | -1.2 | 0.83 |
| 2026 | Nordeste | 633 | 749 | -15.6 | 0.83 |
| 2026 | Centro-Oeste | 840 | 1068 | -21.3 | 0.83 |
| 2026 | Sudeste | 885 | 911 | -2.9 | 0.83 |
| 2026 | Sul | 1252 | 1202 | +4.1 | 0.83 |
| 2026 | Brasil | 1187 | 1260 | -5.8 | 0.83 |
| 2024 | Norte | 1589 | 1552 | +2.4 | 0.86 |
| 2024 | Nordeste | 877 | 823 | +6.6 | 0.86 |
| 2024 | Centro-Oeste | 850 | 862 | -1.4 | 0.86 |
| 2024 | Sudeste | 676 | 683 | -1.1 | 0.86 |
| 2024 | Sul | 1377 | 1327 | +3.8 | 0.86 |
| 2024 | Brasil | 1201 | 1174 | +2.3 | 0.86 |

##### Calor: anomalia da Tmax do SAB x anomalia da temperatura de superfície do MODIS
Atenção: o Terra (MODIS) saiu da órbita fixa em 2022 e passa cada vez mais cedo, então a temperatura de superfície dele esfria artificialmente ano a ano; o NÍVEL da anomalia do MODIS não serve. O que vale é a CORRELAÇÃO ESPACIAL (o desenho do calor no mapa), comparada à de 2024.


| Mês | Região | Anomalia Tmax SAB (°C) | Anomalia LST MODIS (°C) | Correlação espacial (Brasil) |
|---|---|---|---|---|
| 2024-09 | Brasil | +1.78 | -0.62 | 0.33 |
| 2024-09 | Centro-Oeste | +2.22 | -0.84 | 0.33 |
| 2024-09 | Nordeste | +0.73 | -2.42 | 0.33 |
| 2024-09 | Norte | +1.65 | +0.27 | 0.33 |
| 2024-09 | Sudeste | +2.61 | -0.68 | 0.33 |
| 2024-09 | Sul | +2.65 | -0.98 | 0.33 |
| 2024-10 | Brasil | +1.20 | -1.13 | 0.38 |
| 2024-10 | Centro-Oeste | +1.22 | -1.61 | 0.38 |
| 2024-10 | Nordeste | +0.91 | -2.65 | 0.38 |
| 2024-10 | Norte | +1.43 | -0.07 | 0.38 |
| 2024-10 | Sudeste | +0.75 | -2.18 | 0.38 |
| 2024-10 | Sul | +1.21 | -1.00 | 0.38 |
| 2026-09 | Brasil | +0.91 | -4.77 | 0.61 |
| 2026-09 | Centro-Oeste | +0.08 | -6.20 | 0.61 |
| 2026-09 | Nordeste | +1.46 | -5.60 | 0.61 |
| 2026-09 | Norte | +1.77 | -2.83 | 0.61 |
| 2026-09 | Sudeste | -0.31 | -7.02 | 0.61 |
| 2026-09 | Sul | -1.59 | -7.27 | 0.61 |
| 2026-10 | Brasil | +1.09 | -4.66 | 0.70 |
| 2026-10 | Centro-Oeste | +0.05 | -5.64 | 0.70 |
| 2026-10 | Nordeste | +1.51 | -6.35 | 0.70 |
| 2026-10 | Norte | +2.25 | -2.15 | 0.70 |
| 2026-10 | Sudeste | -0.15 | -7.80 | 0.70 |
| 2026-10 | Sul | -2.42 | -8.34 | 0.70 |

### Solo, folha e ET real × SMAP e MODIS

Arquivo: `pesquisa/resultados_solo_folha/RESULTADOS.md`

#### Solo, folha e ET real do SAB contra satélites independentes (2016–2021)

Correlação das anomalias mensais (ciclo do ano retirado), por região. Regra fixada antes de rodar: mediana das 5 regiões r ≥ 0,6 mantém; 0,3–0,6 mantém como índice com aviso; < 0,3 recomendo retirar.

| Variável | Referência | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil | Mediana (5 regiões) | Viés médio (SAB − ref.) | Recomendação |
|---|---|---|---|---|---|---|---|---|---|
| umidade_0_5cm | SMAP | 0.42 | 0.93 | 0.78 | 0.89 | 0.93 | 0.61 | 0.89 | -0.02 | mantém |
| tfolha_C | LST dia | 0.80 | 0.81 | 0.71 | 0.80 | 0.53 | 0.70 | 0.80 | -7.02 | mantém |
| tsolo_C | LST noite | 0.81 | 0.74 | 0.59 | 0.80 | 0.81 | 0.76 | 0.80 | +6.75 | mantém |
| et_real | MOD16 | 0.06 | 0.67 | 0.52 | 0.47 | 0.46 | 0.25 | 0.47 | -8.07 | mantém como índice (aviso) |

### Escoamento × CAMELS-BR

Arquivo: `pesquisa/resultados_escoamento/RESULTADOS.md`

#### Escoamento do SAB contra a vazão observada (CAMELS-BR), 1981–2018

Protocolo fixado antes de rodar: `pesquisa/PROTOCOLO_ESCOAMENTO_CAMELS.md`. Total mensal na bacia; bacias com pelo menos 24 meses válidos. Fonte da vazão: CAMELS-BR v1.1 (Chagas et al., 2020, doi:10.5281/zenodo.3964745, CC-BY-4.0).

##### Brasil (mediana entre as bacias)

| Método | Período | Bacias | KGE | Viés (%) | |Viés| (%) | r |
|---|---|---|---|---|---|---|
| M0 atual (entregue) | 1981-2018 | 512 | 0.31 | -35 | 38 | 0.73 |
| M1 gravado | 1981-2018 | 512 | 0.30 | -30 | 38 | 0.71 |
| M2 ERA5-Land puro | 1981-2018 | 512 | 0.27 | -10 | 21 | 0.80 |
| M3 coef. ERA5 × chuva SAB | 1981-2018 | 512 | 0.30 | -15 | 20 | 0.86 |
| M0 atual (entregue) | 1981-1999 | 512 | 0.28 | -31 | 36 | 0.72 |
| M1 gravado | 1981-1999 | 512 | 0.28 | -27 | 37 | 0.71 |
| M2 ERA5-Land puro | 1981-1999 | 512 | 0.15 | -3 | 19 | 0.80 |
| M3 coef. ERA5 × chuva SAB | 1981-1999 | 512 | 0.22 | -12 | 18 | 0.87 |
| M0 atual (entregue) | 2000-2018 | 512 | 0.31 | -40 | 42 | 0.75 |
| M1 gravado | 2000-2018 | 512 | 0.30 | -35 | 40 | 0.73 |
| M2 ERA5-Land puro | 2000-2018 | 512 | 0.36 | -17 | 25 | 0.80 |
| M3 coef. ERA5 × chuva SAB | 2000-2018 | 512 | 0.39 | -18 | 24 | 0.87 |

##### Por região hidrográfica (1981–2018, mediana)

| Região | Bacias | KGE M0 | Viés M0 (%) | KGE M1 | KGE M2 | KGE M3 | Viés M3 (%) |
|---|---|---|---|---|---|---|---|
| amazon | 22 | 0.33 | -46 | 0.42 | 0.66 | 0.70 | -2 |
| e_atlantic | 49 | 0.01 | -55 | -0.03 | 0.11 | 0.19 | -66 |
| eastern_ne_atlantic | 6 | -0.00 | -74 | 0.10 | -0.31 | -0.18 | -86 |
| paraguay | 2 | 0.06 | -70 | 0.47 | 0.56 | 0.54 | -32 |
| parana | 145 | 0.35 | -35 | 0.35 | 0.26 | 0.28 | -18 |
| parnaiba | 9 | -0.89 | +4 | -2.86 | -2.02 | -1.39 | +46 |
| s_atlantic | 41 | 0.48 | -30 | 0.49 | 0.63 | 0.70 | -15 |
| sao_francisco | 54 | -0.20 | -22 | -0.57 | 0.20 | 0.20 | -14 |
| se_atlantic | 83 | 0.34 | -38 | 0.35 | 0.13 | 0.19 | -10 |
| tocantins-araguaia | 33 | 0.20 | -52 | -0.04 | 0.05 | 0.02 | -2 |
| uruguay | 41 | 0.55 | -27 | 0.56 | 0.69 | 0.73 | -21 |
| western_ne_atlantic | 27 | 0.03 | +27 | -0.56 | -2.28 | -2.57 | +130 |

##### Regra de decisão (as quatro condições)

| Candidato | 1. KGE +0,10 (todo) | 2. melhora em ≥ 60% | 3. vale nas duas metades | 4. |viés| não piora | Passa? |
|---|---|---|---|---|---|
| M1 gravado | ❌ (-0.01) | ❌ (57%) | ❌ | ✅ | não |
| M2 ERA5-Land puro | ❌ (-0.04) | ❌ (52%) | ❌ | ✅ | não |
| M3 coef. ERA5 × chuva SAB | ❌ (-0.01) | ❌ (58%) | ❌ | ✅ | não |

##### Decisão

Nenhum candidato passou nas quatro condições: **o M0 fica**. O dicionário ganha o aviso quantitativo (KGE e viés do M0 por região, tabela acima).

### Método de 2026 em 2021–2025

Arquivo: `pesquisa/resultados_metodo_2026/RESULTADOS_A.md`

(ainda não rodou)

### 2026 × GLDAS-2.1

Arquivo: `pesquisa/resultados_metodo_2026/RESULTADOS_B.md`

(ainda não rodou)

### Histórico por década × TerraClimate e CHIRPS

Arquivo: `pesquisa/resultados_historico/RESULTADOS.md`

(ainda não rodou)

### Tudo por mês do ano

Arquivo: `pesquisa/RESULTADOS_POR_MES.md`

(ainda não rodou)

### Previsão estendida (pesquisa)

Arquivo: `pesquisa/resultados/RESULTADOS.md`

#### Resultados: previsão estendida de chuva e temperatura

Protocolo: `pesquisa/PROTOCOLO.md`. 989 pontos classe A. Treino 1982-2010; teste 2011 em diante. MSESS > 0 = melhor que a média histórica; acerto de tercil: 33% = acaso.

##### 1. Quantas células têm previsão aprovada (5 regiões x 4 estações = 20 por linha)

| Variável | Alvo | Aprovadas | Métodos escolhidos nas aprovadas |
|---|---|---|---|
| Chuva (mm) | M2 (dias ~31-60) | 3 de 20 | ENS_raiz (3) |
| Chuva (mm) | M3 (dias ~61-90) | 2 de 20 | ENS_raiz (2) |
| Chuva (mm) | Q1 (dias ~16-31) | 1 de 20 | ENS (1) |
| Tmin (°C) | M2 (dias ~31-60) | 11 de 20 | R2 (4), ENS (4), C1 (1), P1 (1), E2t (1) |
| Tmin (°C) | M3 (dias ~61-90) | 12 de 20 | ENS (7), R2 (2), R2t (1), E1t (1), C1 (1) |
| Tmin (°C) | Q1 (dias ~16-31) | 13 de 20 | R2 (5), ENS (5), P1 (1), R1t (1), E2t (1) |
| Tmax (°C) | M2 (dias ~31-60) | 7 de 20 | ENSt (2), R2t (2), ENS (2), E2t (1) |
| Tmax (°C) | M3 (dias ~61-90) | 6 de 20 | R1t (2), R2t (2), E2t (1), ENSt (1) |
| Tmax (°C) | Q1 (dias ~16-31) | 10 de 20 | ENSt (5), R2t (2), ENS (2), C1 (1) |

##### 2. Paraná: método escolhido (pelo treino) e escore no teste

| Variável | Alvo | Estação | Método | MSESS (IC 95%) | Acerto tercil | RPSS | Produto |
|---|---|---|---|---|---|---|---|
| Chuva (mm) | M2 | DJF | C0 | +0.00 (+0.00 a +0.00) | 30% | +0.00 | sem sinal: média histórica |
| Chuva (mm) | M2 | JJA | R2_raiz | -0.14 (-0.36 a +0.01) | 32% | -0.09 | sem sinal: média histórica |
| Chuva (mm) | M2 | MAM | E2_raiz | +0.01 (-0.12 a +0.17) | 35% | -0.00 | sem sinal: média histórica |
| Chuva (mm) | M2 | SON | E2_raiz | +0.04 (-0.06 a +0.12) | 35% | +0.03 | sem sinal: média histórica |
| Chuva (mm) | M3 | DJF | R2_raiz | -0.14 (-0.29 a +0.03) | 32% | -0.09 | sem sinal: média histórica |
| Chuva (mm) | M3 | JJA | R1_raiz | +0.00 (-0.06 a +0.06) | 33% | -0.02 | sem sinal: média histórica |
| Chuva (mm) | M3 | MAM | E2_raiz | +0.00 (-0.07 a +0.11) | 34% | -0.01 | sem sinal: média histórica |
| Chuva (mm) | M3 | SON | E2_raiz | +0.04 (-0.06 a +0.12) | 36% | +0.01 | sem sinal: média histórica |
| Chuva (mm) | Q1 | DJF | C0 | +0.00 (+0.00 a +0.00) | 28% | +0.00 | sem sinal: média histórica |
| Chuva (mm) | Q1 | JJA | R1_raiz | -0.01 (-0.04 a +0.02) | 36% | -0.04 | sem sinal: média histórica |
| Chuva (mm) | Q1 | MAM | E2_raiz | +0.03 (-0.06 a +0.14) | 36% | +0.01 | sem sinal: média histórica |
| Chuva (mm) | Q1 | SON | R2_raiz | -0.01 (-0.14 a +0.08) | 38% | -0.04 | sem sinal: média histórica |
| Tmin (°C) | M2 | DJF | E2t | -0.06 (-0.35 a +0.15) | 43% | -0.01 | sem sinal: média histórica |
| Tmin (°C) | M2 | JJA | C1 | +0.18 (+0.09 a +0.24) | 41% | +0.14 | C1 |
| Tmin (°C) | M2 | MAM | E1t | +0.16 (-0.03 a +0.28) | 45% | +0.14 | sem sinal: média histórica |
| Tmin (°C) | M2 | SON | E2t | +0.25 (+0.05 a +0.42) | 51% | +0.20 | E2t |
| Tmin (°C) | M3 | DJF | E1t | -0.04 (-0.47 a +0.22) | 45% | -0.01 | sem sinal: média histórica |
| Tmin (°C) | M3 | JJA | E1t | +0.23 (+0.11 a +0.29) | 46% | +0.18 | E1t |
| Tmin (°C) | M3 | MAM | C1 | +0.17 (+0.06 a +0.25) | 43% | +0.16 | C1 |
| Tmin (°C) | M3 | SON | E2t | +0.12 (-0.05 a +0.29) | 48% | +0.12 | sem sinal: média histórica |
| Tmin (°C) | Q1 | DJF | ENSt | +0.04 (-0.12 a +0.18) | 44% | +0.04 | sem sinal: média histórica |
| Tmin (°C) | Q1 | JJA | R1t | +0.17 (+0.08 a +0.24) | 36% | +0.10 | R1t |
| Tmin (°C) | Q1 | MAM | E1t | +0.01 (-0.19 a +0.16) | 40% | -0.01 | sem sinal: média histórica |
| Tmin (°C) | Q1 | SON | E2t | +0.19 (+0.10 a +0.27) | 44% | +0.17 | E2t |
| Tmax (°C) | M2 | DJF | C1 | +0.15 (-0.10 a +0.36) | 51% | +0.08 | sem sinal: média histórica |
| Tmax (°C) | M2 | JJA | ENSt | +0.26 (+0.04 a +0.38) | 51% | +0.21 | sem sinal: média histórica |
| Tmax (°C) | M2 | MAM | C1 | -0.00 (-0.46 a +0.29) | 45% | +0.00 | sem sinal: média histórica |
| Tmax (°C) | M2 | SON | ENSt | +0.03 (-0.35 a +0.24) | 44% | -0.05 | sem sinal: média histórica |
| Tmax (°C) | M3 | DJF | C1 | +0.07 (-0.44 a +0.34) | 48% | +0.02 | sem sinal: média histórica |
| Tmax (°C) | M3 | JJA | ENSt | +0.22 (-0.08 a +0.36) | 47% | +0.14 | sem sinal: média histórica |
| Tmax (°C) | M3 | MAM | P1t | -0.06 (-0.51 a +0.29) | 46% | +0.01 | sem sinal: média histórica |
| Tmax (°C) | M3 | SON | C1 | +0.03 (-0.40 a +0.30) | 47% | -0.01 | sem sinal: média histórica |
| Tmax (°C) | Q1 | DJF | R1t | +0.13 (-0.03 a +0.29) | 47% | +0.07 | sem sinal: média histórica |
| Tmax (°C) | Q1 | JJA | C1 | +0.14 (+0.02 a +0.23) | 42% | +0.08 | C1 |
| Tmax (°C) | Q1 | MAM | E1t | -0.12 (-0.47 a +0.11) | 38% | -0.07 | sem sinal: média histórica |
| Tmax (°C) | Q1 | SON | R2t | +0.13 (-0.09 a +0.28) | 43% | +0.04 | sem sinal: média histórica |

##### 3. Cascavel (pixel): método escolhido (pelo treino) e escore no teste

| Variável | Alvo | Estação | Método | MSESS (IC 95%) | Acerto tercil | RPSS | Produto |
|---|---|---|---|---|---|---|---|
| Chuva (mm) | M2 | DJF | E1 | -0.22 (-0.41 a +0.01) | 42% | -0.10 | sem sinal: média histórica |
| Chuva (mm) | M2 | JJA | R2_raiz | -0.34 (-0.87 a +0.03) | 31% | -0.12 | sem sinal: média histórica |
| Chuva (mm) | M2 | MAM | ENS | -0.05 (-0.17 a +0.14) | 38% | -0.03 | sem sinal: média histórica |
| Chuva (mm) | M2 | SON | E2_raiz | +0.04 (-0.08 a +0.13) | 44% | +0.04 | sem sinal: média histórica |
| Chuva (mm) | M3 | DJF | E1 | -0.11 (-0.30 a +0.07) | 38% | -0.07 | sem sinal: média histórica |
| Chuva (mm) | M3 | JJA | R2_raiz | -0.24 (-0.70 a -0.00) | 32% | -0.19 | sem sinal: média histórica |
| Chuva (mm) | M3 | MAM | R1 | -0.04 (-0.11 a +0.11) | 32% | -0.01 | sem sinal: média histórica |
| Chuva (mm) | M3 | SON | E2_raiz | +0.03 (-0.11 a +0.14) | 45% | +0.03 | sem sinal: média histórica |
| Chuva (mm) | Q1 | DJF | P1_raiz | -0.29 (-0.53 a -0.09) | 30% | -0.11 | sem sinal: média histórica |
| Chuva (mm) | Q1 | JJA | C0 | +0.00 (+0.00 a +0.00) | 41% | -0.03 | sem sinal: média histórica |
| Chuva (mm) | Q1 | MAM | R1_raiz | -0.02 (-0.11 a +0.06) | 47% | -0.03 | sem sinal: média histórica |
| Chuva (mm) | Q1 | SON | ENS_raiz | +0.07 (-0.03 a +0.13) | 40% | -0.04 | sem sinal: média histórica |
| Tmin (°C) | M2 | DJF | C0 | +0.00 (+0.00 a +0.00) | 30% | -0.02 | sem sinal: média histórica |
| Tmin (°C) | M2 | JJA | C0 | +0.00 (+0.00 a +0.00) | 27% | -0.02 | sem sinal: média histórica |
| Tmin (°C) | M2 | MAM | E1 | -0.03 (-0.20 a +0.09) | 31% | -0.00 | sem sinal: média histórica |
| Tmin (°C) | M2 | SON | E2 | +0.12 (-0.10 a +0.30) | 30% | +0.08 | sem sinal: média histórica |
| Tmin (°C) | M3 | DJF | E1 | -0.10 (-0.34 a +0.05) | 34% | -0.04 | sem sinal: média histórica |
| Tmin (°C) | M3 | JJA | E1 | +0.06 (-0.01 a +0.12) | 22% | +0.03 | sem sinal: média histórica |
| Tmin (°C) | M3 | MAM | C0 | +0.00 (+0.00 a +0.00) | 28% | +0.05 | sem sinal: média histórica |
| Tmin (°C) | M3 | SON | E2 | +0.09 (-0.05 a +0.21) | 28% | +0.04 | sem sinal: média histórica |
| Tmin (°C) | Q1 | DJF | C0 | +0.00 (+0.00 a +0.00) | 25% | -0.00 | sem sinal: média histórica |
| Tmin (°C) | Q1 | JJA | C0 | +0.00 (+0.00 a +0.00) | 18% | -0.04 | sem sinal: média histórica |
| Tmin (°C) | Q1 | MAM | E1 | -0.11 (-0.29 a -0.00) | 37% | -0.10 | sem sinal: média histórica |
| Tmin (°C) | Q1 | SON | E1 | -0.01 (-0.17 a +0.15) | 39% | +0.04 | sem sinal: média histórica |
| Tmax (°C) | M2 | DJF | C1 | +0.08 (-0.17 a +0.32) | 50% | +0.13 | sem sinal: média histórica |
| Tmax (°C) | M2 | JJA | R2t | +0.05 (-0.32 a +0.34) | 33% | +0.01 | sem sinal: média histórica |
| Tmax (°C) | M2 | MAM | E1t | -0.10 (-0.40 a +0.11) | 37% | -0.06 | sem sinal: média histórica |
| Tmax (°C) | M2 | SON | ENSt | -0.09 (-0.48 a +0.10) | 36% | -0.19 | sem sinal: média histórica |
| Tmax (°C) | M3 | DJF | E1t | -0.21 (-0.73 a +0.16) | 41% | -0.14 | sem sinal: média histórica |
| Tmax (°C) | M3 | JJA | ENSt | +0.17 (-0.15 a +0.32) | 43% | +0.07 | sem sinal: média histórica |
| Tmax (°C) | M3 | MAM | C1 | -0.03 (-0.29 a +0.20) | 49% | +0.01 | sem sinal: média histórica |
| Tmax (°C) | M3 | SON | C1 | -0.09 (-0.56 a +0.22) | 44% | -0.07 | sem sinal: média histórica |
| Tmax (°C) | Q1 | DJF | C1 | +0.11 (-0.07 a +0.28) | 44% | +0.01 | sem sinal: média histórica |
| Tmax (°C) | Q1 | JJA | C1 | +0.07 (-0.08 a +0.18) | 43% | +0.05 | sem sinal: média histórica |
| Tmax (°C) | Q1 | MAM | E1t | -0.21 (-0.51 a -0.02) | 37% | -0.18 | sem sinal: média histórica |
| Tmax (°C) | Q1 | SON | R2t | +0.09 (-0.15 a +0.26) | 43% | +0.00 | sem sinal: média histórica |

##### 4. Média de cada método no Brasil (sem escolha; MSESS médio das 20 células, teste)

| Variável | Alvo | C0 | C1 | C1_raiz | E1 | E1_raiz | E1t | E1t_raiz | E2 | E2_raiz | E2t | E2t_raiz | ENS | ENS_raiz | ENSt | ENSt_raiz | P1 | P1_raiz | P1t | P1t_raiz | R1 | R1_raiz | R1t | R1t_raiz | R2 | R2_raiz | R2t | R2t_raiz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Chuva (mm) | Q1 | +0.00 | -0.03 | -0.01 | -0.04 | -0.04 | -0.07 | -0.05 | -0.02 | -0.02 | -0.05 | -0.03 | +0.01 | -0.14 | -0.02 | -0.08 | -0.07 | -1.35 | -0.11 | -1.34 | +0.01 | +0.01 | -0.03 | -0.01 | +0.00 | -0.03 | -0.04 | -0.04 |
| Chuva (mm) | M2 | +0.00 | -0.05 | -0.02 | -0.05 | -0.04 | -0.10 | -0.07 | -0.02 | -0.02 | -0.08 | -0.05 | +0.02 | -0.20 | -0.04 | -0.12 | -0.09 | -1.59 | -0.14 | -1.57 | +0.02 | +0.01 | -0.04 | -0.02 | -0.00 | -0.06 | -0.07 | -0.08 |
| Chuva (mm) | M3 | +0.00 | -0.06 | -0.03 | -0.05 | -0.05 | -0.11 | -0.08 | -0.02 | -0.02 | -0.08 | -0.05 | +0.00 | -0.03 | -0.05 | -0.04 | -0.11 | -0.38 | -0.16 | -0.40 | +0.00 | +0.00 | -0.06 | -0.03 | -0.03 | -0.02 | -0.09 | -0.06 |
| Tmax (°C) | Q1 | +0.00 | +0.08 | +nan | -0.03 | +nan | +0.08 | +nan | -0.01 | +nan | +0.11 | +nan | +0.22 | +nan | +0.15 | +nan | +0.19 | +nan | +0.09 | +nan | +0.21 | +nan | +0.12 | +nan | +0.27 | +nan | +0.13 | +nan |
| Tmax (°C) | M2 | +0.00 | +0.09 | +nan | -0.02 | +nan | +0.12 | +nan | -0.01 | +nan | +0.13 | +nan | +0.22 | +nan | +0.15 | +nan | +0.18 | +nan | +0.09 | +nan | +0.24 | +nan | +0.14 | +nan | +0.28 | +nan | +0.12 | +nan |
| Tmax (°C) | M3 | +0.00 | +0.09 | +nan | -0.01 | +nan | +0.12 | +nan | -0.01 | +nan | +0.14 | +nan | +0.18 | +nan | +0.14 | +nan | +0.11 | +nan | +0.07 | +nan | +0.20 | +nan | +0.13 | +nan | +0.23 | +nan | +0.11 | +nan |
| Tmin (°C) | Q1 | +0.00 | +0.11 | +nan | -0.03 | +nan | +0.13 | +nan | -0.00 | +nan | +0.16 | +nan | +0.31 | +nan | +0.19 | +nan | +0.31 | +nan | +0.13 | +nan | +0.24 | +nan | +0.17 | +nan | +0.37 | +nan | +0.18 | +nan |
| Tmin (°C) | M2 | +0.00 | +0.13 | +nan | -0.02 | +nan | +0.16 | +nan | +0.00 | +nan | +0.18 | +nan | +0.33 | +nan | +0.21 | +nan | +0.32 | +nan | +0.15 | +nan | +0.26 | +nan | +0.20 | +nan | +0.39 | +nan | +0.19 | +nan |
| Tmin (°C) | M3 | +0.00 | +0.13 | +nan | -0.02 | +nan | +0.16 | +nan | +0.00 | +nan | +0.18 | +nan | +0.28 | +nan | +0.19 | +nan | +0.26 | +nan | +0.13 | +nan | +0.22 | +nan | +0.18 | +nan | +0.34 | +nan | +0.17 | +nan |

##### Parâmetros escolhidos no treino

- R1 mm: lambda 100.0
- R2 mm: lambda 1000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 1000.0
- R1 raiz: lambda 100.0
- R2 raiz: lambda 1000.0
- R1t raiz: lambda 100.0
- R2t raiz: lambda 1000.0
- R1 mm: lambda 100.0
- R2 mm: lambda 1000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 1000.0
- R1 raiz: lambda 100.0
- R2 raiz: lambda 1000.0
- R1t raiz: lambda 100.0
- R2t raiz: lambda 1000.0
- R1 mm: lambda 100.0
- R2 mm: lambda 1000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 1000.0
- R1 raiz: lambda 100.0
- R2 raiz: lambda 1000.0
- R1t raiz: lambda 100.0
- R2t raiz: lambda 1000.0
- R1 mm: lambda 30.0
- R2 mm: lambda 1000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 1000.0
- R1 mm: lambda 30.0
- R2 mm: lambda 1000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 1000.0
- R1 mm: lambda 30.0
- R2 mm: lambda 1000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 1000.0
- R1 mm: lambda 100.0
- R2 mm: lambda 1000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 1000.0
- R1 mm: lambda 100.0
- R2 mm: lambda 1000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 1000.0
- R1 mm: lambda 100.0
- R2 mm: lambda 1000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 1000.0

### Acerto da previsão GFS

Arquivo: `rotinas/resultados/previsao/ACERTO.md`

(ainda não rodou)

## C. Todas as mudanças do repositório `sab-pedidos` (da mais nova para a mais antiga)

As do `sab-motor` ficam no GitHub dele (Commits); as anteriores ao GitHub, nos changelogs da entrega.

| Quando | Mudança |
|---|---|
| 25/11/2026 06:57 | Validar histórico: a chuva do TerraClimate é a banda pr (não ppt); a tarefa volta para a fila |
| 25/11/2026 06:57 | Conferência: historico (falhou)  |
| 25/11/2026 06:53 | Conferência: começou historico  |
| 25/11/2026 06:53 | Conferência: historico (pendente)  |
| 25/11/2026 06:50 | Conferência: começou historico  |
| 25/11/2026 06:50 | Conferência: historico (pendente)  |
| 25/11/2026 06:48 | Registro geral do SAB: do início do código às últimas atualizações (refeito sozinho pela fila) |
| 25/11/2026 06:46 | Conferência: começou historico  |
| 25/11/2026 06:46 | Validação do histórico 1961-2025 por década (TerraClimate e CHIRPS) e resumo por mês do ano |
| 25/11/2026 03:39 | Merge pull request #10 from adaojunior0909-85/teste-metodo-2026 |
| 25/11/2026 06:39 | Teste das 16 variáveis de 2026: o método do motor em 2021-2025 e 2026 contra o GLDAS-2.1 (na fila) |
| 25/11/2026 06:36 | Conferência: escoamento_metricas (ok)  |
| 25/11/2026 06:36 | Conferência: começou escoamento_metricas  |
| 25/11/2026 06:36 | Conferência: escoamento_extrair (ok)  |
| 25/11/2026 06:33 | Conferência: começou escoamento_extrair  |
| 25/11/2026 06:33 | Conferência: solo_folha (ok)  |
| 25/11/2026 06:28 | Conferência: começou solo_folha  |
| 25/11/2026 06:28 | Conferência: validar_2026 (ok)  |
| 25/11/2026 06:19 | Conferência: começou validar_2026  |
| 25/11/2026 03:17 | Merge pull request #9 from adaojunior0909-85/validacoes-extra |
| 25/11/2026 02:42 | Validar 2026: viés da chuva pelo total do período (não pela média dos meses) |
| 25/11/2026 01:28 | Conferência final automática: fila no GitHub (validações, escoamento x CAMELS-BR, K26 de 1961 até a previsão) |
| 25/11/2026 01:20 | Pesquisa: protocolo do escoamento contra a vazão do CAMELS-BR, fixado antes de rodar  |
| 25/11/2026 01:17 | Pesquisa: validação de 2026 contra IMERG (chuva) e MODIS (calor), com 2024 como régua |
| 25/11/2026 01:16 | Rotina: acerto da previsão (2026-11-25) |
| 25/11/2026 01:15 | Rotina diária: acerto da previsão GFS por prazo (fotografa e confere) |
| 25/11/2026 01:13 | K26 à mão: rodar outra rodada (ex.: 7 = 1981-1990) pelo Run workflow, sem mexer no painel  |
| 25/11/2026 00:14 | Rotina: RONI do mês (2026-11-25) |
| 24/11/2026 21:11 | Merge pull request #8 from adaojunior0909-85/rotinas-automaticas |
| 25/11/2026 00:04 | Rotinas: LEIA com a V1.7  |
| 25/11/2026 00:04 | Rotinas: K26 e saúde à tarde, depois do motor (que tem rodado de manhã)  |
| 24/11/2026 23:56 | Rotina: K26 rodada 1 (2026-11-24) |
| 24/11/2026 23:27 | Rotina: saúde do banco (2026-11-24) |
| 24/11/2026 23:27 | Saúde do banco: aceita V1.6 e V1.7 durante a troca e mostra quantos dias há em cada versão |
| 24/11/2026 23:26 | Verificação da V1.7: mede os pixels vizinhos contaminados pelo 0 do mar |
| 24/11/2026 23:25 | Pesquisa: verificação prévia (só leitura) da mudança do motor V1.7 no Rs |
| 24/11/2026 23:22 | Rotina: RONI do mês (2026-11-24) |
| 24/11/2026 23:21 | Rotina: saúde do banco (2026-11-24) |
| 24/11/2026 23:21 | Rotinas: uma fila por rotina e painel refeito na hora de subir (sem perder a atualização de outra rotina) |
| 24/11/2026 23:20 | Rotinas automáticas: RONI do mês, K26 rodada 1, saúde do banco e painel de controle |
| 23/11/2026 07:41 | Merge pull request #7: sab_pedido 2026.11.22, radiação impossível sai vazia (K16 v7.1 aprovada em 22/11, 22h40) |
| 23/11/2026 00:09 | sab_pedido 2026.11.22: cabeçalho com a contagem em pixels inteiros |
| 23/11/2026 00:07 | sab_pedido 2026.11.22: a regra também esvazia a ETo e o déficit do dia |
| 23/11/2026 00:04 | Pesquisa: diagnóstico (só leitura) do Rs = 0 no litoral em 2026 |
| 23/11/2026 00:00 | Verificação da radiação: vazios por classe da máscara de qualidade |
| 22/11/2026 23:59 | Verificação da radiação: contagem em pixels inteiros (sem o peso da borda) |
| 22/11/2026 23:57 | sab_pedido 2026.11.22: radiação abaixo de 3% de Ra sai vazia |
| 18/11/2026 19:30 | Merge pull request #6 from adaojunior0909-85/k26-v1-10 |
| 18/11/2026 22:30 | K26 v1.10: rodada 12 = 2001-2025 de uma vez |
| 18/11/2026 19:27 | Merge pull request #5 from adaojunior0909-85/pesquisa-escoamento |
| 18/11/2026 22:17 | Pesquisa: K26 v1.9 conta "tem valor" no item H e recomendações corrigidas |
| 18/11/2026 22:16 | Pesquisa: teste 2 do escoamento (não recomendado), K26 v1.9 e checagem do item H |
| 18/11/2026 22:14 | Pesquisa: verificação da K26 |
| 18/11/2026 22:04 | Pesquisa: teste 2 do escoamento (coeficiente do ERA5 na chuva observada) |
| 18/11/2026 19:01 | Merge pull request #4 from adaojunior0909-85/pesquisa-previsao-estendida |
| 18/11/2026 18:59 | Merge pull request #3 from adaojunior0909-85/aviso-escoamento-dicionario |
| 18/11/2026 21:30 | Piloto: previsão e conferência (2026-11-18) |
| 18/11/2026 21:17 | Pesquisa: recomendações da K26 e primeira emissão do piloto |
| 18/11/2026 21:15 | Piloto da previsão estendida de temperatura (emissão e conferência)  |
| 18/11/2026 21:15 | Dicionário: aviso de que escoamento e chuva efetiva de 1961-2025 não batem dia a dia com a chuva |
| 18/11/2026 21:14 | Pesquisa: resultado do teste do escoamento (alinhamento rejeitado pela regra; causa é a fonte da chuva) |
| 18/11/2026 21:04 | Pesquisa: verificação da K26 |
| 18/11/2026 21:00 | Pesquisa: corrige o nome do passo do workflow da K26 (dois-pontos no YAML) |
| 18/11/2026 20:59 | Pesquisa: hipótese e teste do escoamento maior que a chuva (achado C da K26) |
| 18/11/2026 20:53 | Pesquisa: resultados da rodada 2 e comparação com a rodada 1 |
| 18/11/2026 20:52 | Pesquisa: verificação da K26 |
| 18/11/2026 20:44 | Pesquisa: verificação da K26 com uma soma por dia (limite de agregações do Earth Engine) |
| 18/11/2026 20:43 | Pesquisa: verificação da K26 no que o usuário recebe (só leitura) |
| 18/11/2026 20:31 | Pesquisa: comparador da rodada 1 x rodada 2 (critério de aceite só com anos de treino) |
| 18/11/2026 20:31 | Pesquisa: regras e código da rodada 2 (antes de rodar com os dados reais) |
| 18/11/2026 19:39 | Pesquisa: resultados da rodada 1 (protocolo pré-registrado) |
| 18/11/2026 19:21 | Ignora o cache do Python (__pycache__) |
| 18/11/2026 19:20 | Pesquisa: hindcast e teste com dados artificiais (antes dos dados reais) |
| 18/11/2026 19:12 | Pesquisa: dados extraídos do Earth Engine |
| 18/11/2026 19:04 | Pesquisa: protocolo e extrator da previsão estendida de chuva e temperatura |
| 18/11/2026 15:50 | Merge pull request #2 from adaojunior0909-85/correcao-pedido-uma-variavel |
| 18/11/2026 18:35 | Corrige pedido de uma variável só saindo com a coluna vazia |
| 15/11/2026 20:32 | Merge pull request #1 from adaojunior0909-85/manutencao-versoes |

