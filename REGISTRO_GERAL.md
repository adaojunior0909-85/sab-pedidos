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
| 25/11, manhã | **Parte A pronta:** o método de 2026 subestima a chuva em todos os anos de 2021–2025 (Brasil −9,6%; Nordeste e Centro-Oeste −12%; na seca do Norte e do Centro-Oeste até −35% a −47%) e superestima ETo (+3,5%) e radiação; piora em 2023–2024 (viés não estacionário). **Parte B pronta (06h47):** 2026 × GLDAS-2.1 confirma a chuva baixa no Nordeste e no Centro-Oeste (fora da régua 2022–2024). **Protocolo da correção** dos dias ERA5 (C0 a C3, teste fora da amostra com origem móvel, regra de 4 condições; 2026 × CHIRPS só relatado) **aprovado e congelado antes de rodar**: `pesquisa/PROTOCOLO_CORRECAO_ERA5_2026.md`. Pasta de entrega remontável só pelo repositório (`entrega/`) | `registro/CONTINUAR_AQUI.md` |
| 25/11, tarde | **Protocolo da correção aprovado**, com a **emenda 1** (extremos em todos os pixels entregues e p99 em 1.500 pixels), congelado antes de rodar; **teste da correção disparado** (fila do branch de trabalho; a receita confere com o `SICSB_1986_2025` a 1,55%). **Motor V1.7** na 1ª rodada da noite (regravando 2026; histórico travado). "Saúde do banco" renomeada para **"Conferência da gravação"** (PR #11). Achado: os agendamentos do `sab-pedidos` não dispararam (o do motor dispara com 7–10 h de atraso) | `registro/CONTINUAR_AQUI.md` |

## 3. Regras que valem sempre

1. **Audite antes de mudar e simule antes de gravar** (01a antes do 01b, 05a antes do 05b). A K16 vem antes de abrir
   ao público qualquer mudança de cálculo.
2. **O histórico 1961–2025 nunca é reescrito.** Correções do histórico são feitas **na leitura** (painel e e-mail).
3. **Regra de decisão fixada ANTES de rodar** em toda pesquisa que pode mudar o banco (K21, escoamento, solo/folha,
   método de 2026, histórico por década): o resultado não muda a regra.
4. **Toda mudança no cálculo do painel exige a mesma mudança no `sab_pedido.py` e uma K16 nova.**
5. **Uma conversa por vez** mexendo no repositório; cada uma deixa o `registro/CONTINUAR_AQUI.md` em dia ao terminar.
6. Credenciais só nos segredos do GitHub e nas propriedades do Apps Script; nunca em arquivo, print ou conversa.

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
| As 16 (parte A) | o próprio método de 2026 (rota ERA5 do motor V1.7) aplicado a 2021–2025 × o banco (BR-DWGD no núcleo) | 2021–2025 | **o método SUBESTIMA a chuva em todos os anos e regiões: Brasil −9,6% (pior ano −13%), Nordeste −12%, Centro-Oeste −12% (pior ano −16%), Norte −9%, Sul −8%, Sudeste −7%**. ETo +3,5%, radiação +0,6 MJ/m²/dia, ET real +3%, UR −0,9 p.p., Tmax +0,2 °C; Tmin, vento e as variáveis do ERA5 sem desvio relevante. Explica a maior parte da chuva baixa de 2026 × CHIRPS (Centro-Oeste −21%, Nordeste −16%); o que sobra em 2026 está perto do pior ano. Hipótese: viés não estacionário (a calibração é a média de 1986–2025; nos anos recentes o ERA5-Land fica mais seco que o BR-DWGD). **Proposta: correção da chuva (e da radiação/ETo) dos dias ERA5, com protocolo fixado antes, simulação 05a e K16; o banco não muda antes disso** |
| As 16 (parte B) | GLDAS-2.1 (NASA) com régua 2022–2024 | 2026 (meses 1–10) | **pronta (25/11, 06h47).** Chuva de 2026 FORA da régua no **Nordeste** (SAB − GLDAS = −10,8%; régua +11,6 a +18,6) e no **Centro-Oeste** (−7,3%; régua +3,9 a +14,2): a terceira fonte independente (depois da Parte A e do CHIRPS) que aponta o método de 2026, não o clima. Radiação do Nordeste acima da régua (+0,2 contra −2,4 a −1,2 MJ), coerente com a Parte A. Tmax, Tmin, UR, VPD, ETo, ET real e umidade do solo dentro da régua em quase tudo. Fora da régua também: escoamento superficial (Norte, Sudeste, Sul, Brasil, acima) e subsuperficial (Norte, Sul), temperatura do solo e da folha (Norte e Centro-Oeste, abaixo), a investigar depois (variáveis do ERA5-Land; no histórico entram com a correção de leitura dos dias V1.0). `pesquisa/resultados_metodo_2026/RESULTADOS_B.md` (na `main`) |
| Chuva, radiação e ETo (correção dos dias ERA5) | o BR-DWGD, fora da amostra (cada ano calibrado só com os anteriores; 120 meses × 5 regiões; extremos em todos os pixels entregues e p99 em 1.500 pixels) | 2016–2025 | **CHUVA: o C3 passa nas 4 condições** (C0 × razão BR-DWGD/C0 da região e do mês nos 5 anos anteriores, limitada a [0,8; 1,5]): mediana do |viés anual| 8,4% → 4,3% (−4,1 p.p.); o Brasil melhora em 9 de 10 anos (2024: −13,6% → −6,2%); r_anomalias sem queda; dias de chuva, Rx1day e p99 dentro dos limites (p99 16,8% → 13,8%). C1 e C2 reprovam só na condição 1 (−2,1 e −1,8 p.p.). **RADIAÇÃO/ETo: nenhum passa** (o C3 reduz a radiação no Brasil +0,45 → +0,25 MJ, mas a ETo só cai 0,8 p.p. (precisava 1) e piora 1,1 p.p. no Sul): o C0 fica. 2026 × CHIRPS (só relato): o C3 aproxima o Nordeste (−15,6% → −4,1%; régua +6,6%) e o Centro-Oeste (−21,3% → −10,0%; régua −1,4%) e passa do ponto no Sul (+4,1% → +15,5%; régua +3,8%). `pesquisa/resultados_correcao_era5/RESULTADOS.md` |
| 10 variáveis | TerraClimate (e chuva × CHIRPS) por década, 5 regiões + 27 estados | 1961–2025 | na fila (resultado no apêndice) |
| Todas as referências | a mesma referência na grade do SAB × na resolução nativa (sensibilidade ao tamanho do pixel) | todos os meses usados | na fila (resultado no apêndice) |
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
- **Para continuar o trabalho numa conversa nova:** `registro/CONTINUAR_AQUI.md`.
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

# Apêndice automático (refeito em 26/11/2026 07:15, Brasília)

## A. Situação das rotinas automáticas (de `rotinas/PAINEL.md`)

| Rotina | Quando roda | Última execução | Situação | Resumo |
|---|---|---|---|---|
| Saúde do banco (motor gravou?) | toda segunda-feira, 14h29 | 24/11/2026 20:27 | ✅ | 343 dias de 2026 (319 ERA5 até 2026-11-15, 24 GFS até 2026-12-09); dia 2026-11-24 gravado há 11 h; versões {'V1.6': 343}; histórico intocado |
| RONI do mês (02_auditoria_roni_cpc.py) | todo dia 11, 10h23 | 24/11/2026 21:14 | ✅ | asset RONI_CPC_v6 regravado e conferido (921 estações) |
| K26, rodada 1 (2026 inteiro, só leitura) | todo dia 15, 15h41 | 24/11/2026 20:56 | 👀 | 343 dias de 2026 (até 2026-12-09); itens: A1 OK, B ATENCAO, C FALHA, G FALHA, H OK |
| Acerto da previsão GFS (1 a 15 dias) | todo dia, 16h13 | 24/11/2026 22:16 | ✅ | fotografia de 2026-11-24: 24 dias GFS (2026-11-16 a 2026-12-09) e a persistência (2026-11-15) |
| Conferência final (validações, escoamento e K26 de 1961 até a previsão) | de 2 em 2 horas, 10h17 a 20h17, até a fila acabar (depois desliga sozinha) | 25/11/2026 06:47 | ⏳ | 6 de 17 tarefas prontas |
| Piloto da previsão estendida (Tmin e Tmax) | dias 3 e 17, 08h17 | 24/11/2026 20:19 | ✅ | 1 emissão(ões); a última em 2026-11-16 |

## B. Resultado de cada validação

Cada bloco é a cópia do arquivo de resultado no momento em que este registro foi refeito.

### Conferência final (fila)

Arquivo: `rotinas/conferencia/CONFERENCIA_FINAL.md`

#### Conferência final do SAB (1961 até a previsão)

Atualizado em 25/11/2026 06:47 (Brasília) pela fila automática (`rotinas/conferencia/fila.py`). Ainda há tarefas na fila.

| Tarefa | Situação | Tentativas | Quando | Resultado |
|---|---|---|---|---|
| 2026 (ERA5 calibrado) contra CHIRPS (chuva) e MODIS (calor) | ✅ pronta | 1 | 25/11 03:28 | pesquisa/resultados_2026/RESULTADOS.md |
| Umidade do solo, temperatura da folha e do solo, ET real contra satélites (2016-2021) | ✅ pronta | 1 | 25/11 03:33 | pesquisa/resultados_solo_folha/RESULTADOS.md |
| Escoamento x vazão do CAMELS-BR: extração 1981-2018 (512 bacias) | ✅ pronta | 1 | 25/11 03:36 |  |
| Escoamento x CAMELS-BR: métricas e decisão do protocolo | ✅ pronta | 1 | 25/11 03:36 | pesquisa/resultados_escoamento/RESULTADOS.md |
| As 16 variáveis: o método de 2026 aplicado a 2021-2025 (contra o BR-DWGD) | ✅ pronta | 1 | 25/11 04:43 | pesquisa/resultados_metodo_2026/RESULTADOS_A.md |
| As 16 variáveis de 2026 contra o GLDAS-2.1 (NASA), régua 2022-2024 | ✅ pronta | 1 | 25/11 06:47 | pesquisa/resultados_metodo_2026/RESULTADOS_B.md |
| K26 rodada 7 (1981-1990) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada7/ |
| K26 rodada 1 (2026 inteiro (inclui os dias de previsão GFS)) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada1/ |
| K26 rodada 2 (2026: Rs = 0 cru do ERA5 e escoamento) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada2/ |
| K26 rodada 3 (2026: vento) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada3/ |
| K26 rodada 4 (2026: umidade do solo) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada4/ |
| K26 rodada 5 (1961-1970) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada5/ |
| K26 rodada 6 (1971-1980) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada6/ |
| K26 rodada 8 (1991-2000) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada8/ |
| K26 rodada 9 (2001-2010) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada9/ |
| K26 rodada 10 (2011-2020) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada10/ |
| K26 rodada 11 (2021-2025) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada11/ |

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

#### Parte A: o método de 2026 aplicado a 2021–2025 (anos com BR-DWGD)

Erro do método = rota ERA5 do motor V1.7 menos o que o banco entrega no mesmo mês (somas: % do total; médias: diferença na unidade). Em cada célula: o erro dos 5 anos juntos e, entre colchetes, o menor e o maior erro de um ano só. **Nas 8 primeiras linhas a referência é a observação (BR-DWGD)**; nas outras, o próprio ERA5 do histórico (mede só a emenda).

| Variável | Unid. | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|---|
| Chuva | % | -9.18 [-15.2 a -5.6] | -12.40 [-16.9 a -9.2] | -11.90 [-16.1 a -7.8] | -6.75 [-12.8 a -3.0] | -7.53 [-12.1 a +0.2] | -9.64 [-13.3 a -7.2] |
| Tmax | °C | +0.41 [+0.2 a +0.7] | -0.10 [-0.2 a +0.0] | +0.24 [+0.1 a +0.3] | +0.17 [+0.1 a +0.2] | +0.13 [-0.1 a +0.3] | +0.24 [+0.1 a +0.4] |
| Tmin | °C | -0.05 [-0.3 a +0.2] | -0.08 [-0.1 a -0.0] | -0.13 [-0.2 a -0.1] | -0.05 [-0.1 a -0.0] | -0.02 [-0.1 a +0.0] | -0.07 [-0.2 a +0.1] |
| Umidade relativa | p.p. | -0.32 [-0.9 a +0.6] | -2.13 [-2.9 a -1.6] | -0.41 [-0.9 a -0.0] | -1.28 [-1.4 a -1.1] | -1.80 [-2.0 a -1.5] | -0.88 [-1.2 a -0.5] |
| Déficit de pressão de vapor | kPa | +0.03 [-0.0 a +0.1] | +0.08 [+0.1 a +0.1] | +0.02 [+0.0 a +0.0] | +0.05 [+0.0 a +0.1] | +0.04 [+0.0 a +0.0] | +0.04 [+0.0 a +0.1] |
| ETo | % | +5.34 [+3.3 a +7.9] | +3.93 [+3.2 a +5.0] | +2.04 [+0.7 a +3.1] | +0.53 [+0.1 a +1.5] | +0.13 [-1.0 a +1.1] | +3.53 [+2.3 a +4.7] |
| Radiação solar | MJ/m²/dia | +0.80 [+0.6 a +1.2] | +0.64 [+0.4 a +0.9] | +0.44 [+0.2 a +0.6] | +0.19 [+0.0 a +0.5] | +0.35 [+0.2 a +0.6] | +0.60 [+0.5 a +0.8] |
| Vento | m/s | +0.12 [+0.0 a +0.2] | +0.23 [+0.2 a +0.2] | +0.01 [-0.0 a +0.0] | +0.01 [-0.0 a +0.0] | -0.07 [-0.2 a +0.0] | +0.09 [+0.0 a +0.1] |
| ET real | % | +4.82 [+4.0 a +5.2] | +1.71 [+1.3 a +2.0] | +2.08 [+1.9 a +2.3] | +1.09 [+0.9 a +1.3] | +2.01 [+1.2 a +2.9] | +3.31 [+2.7 a +3.5] |
| Transpiração | % | +2.03 [+1.7 a +2.4] | +0.04 [+0.0 a +0.1] | +0.33 [+0.2 a +0.5] | +0.09 [+0.1 a +0.1] | +0.59 [+0.4 a +0.8] | +1.17 [+1.0 a +1.4] |
| Escoamento superficial | % | -0.08 [-0.1 a -0.1] | -0.09 [-0.1 a -0.0] | -0.00 [-0.0 a +0.0] | -0.00 [-0.0 a +0.0] | -0.05 [-0.1 a -0.0] | -0.06 [-0.1 a -0.0] |
| Escoamento subsuperficial | % | -0.01 [-0.0 a -0.0] | -0.02 [-0.1 a +0.1] | -0.01 [-0.0 a +0.0] | -0.00 [-0.0 a +0.0] | +0.00 [-0.0 a +0.0] | -0.01 [-0.0 a -0.0] |
| Temperatura do solo | °C | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] |
| Temperatura da folha | °C | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] |
| Umidade do solo 0-5 cm | m³/m³ | +0.00 [-0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | -0.00 [-0.0 a +0.0] | +0.00 [+0.0 a +0.0] |
| Umidade do solo 0-100 cm | m³/m³ | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [-0.0 a +0.0] | +0.00 [+0.0 a +0.0] |

### 2026 × GLDAS-2.1

Arquivo: `pesquisa/resultados_metodo_2026/RESULTADOS_B.md`

#### Parte B: 2026 contra o GLDAS-2.1 (NASA), com 2022–2024 como régua

Meses 1 a 10 de cada ano (GLDAS até 2026-11-16; SAB ERA5 até 2026-11-15). Em cada célula: a diferença SAB − GLDAS em 2026 e, entre colchetes, a faixa da mesma diferença em 2022–2024 (quando o SAB é o BR-DWGD). ⚠️ = 2026 fora da faixa por mais que a tolerância (regra fixada antes de rodar).

| Variável | Unid. | Tol. | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|---|---|
| Chuva | % | 5.0 | +11.90 [+9.7 a +15.9] | ⚠️ -10.83 [+11.6 a +18.6] | ⚠️ -7.31 [+3.9 a +14.2] | +0.35 [-7.4 a +5.2] | +4.62 [+0.8 a +4.0] | +4.62 [+8.0 a +12.4] |
| Tmax | °C | 0.5 | +0.66 [+0.1 a +1.0] | +0.30 [+0.2 a +0.5] | +0.56 [+0.4 a +0.8] | +1.38 [+1.1 a +1.3] | +0.88 [+0.7 a +0.9] | +0.67 [+0.4 a +0.9] |
| Tmin | °C | 0.5 | +0.71 [+0.6 a +0.8] | +0.52 [+0.3 a +0.5] | -0.47 [-0.2 a -0.1] | -0.18 [+0.0 a +0.1] | +0.51 [+0.4 a +0.5] | +0.34 [+0.3 a +0.4] |
| Umidade relativa | p.p. | 3.0 | +5.74 [+2.8 a +6.3] | +2.55 [+4.5 a +5.2] | +8.01 [+5.3 a +7.2] | +1.50 [+0.9 a +2.6] | +0.24 [-0.6 a +1.4] | +4.72 [+3.2 a +5.4] |
| Déficit de pressão de vapor | kPa | 0.1 | -0.30 [-0.3 a -0.2] | -0.13 [-0.2 a -0.2] | -0.36 [-0.3 a -0.2] | -0.05 [-0.1 a -0.0] | -0.05 [-0.1 a -0.0] | -0.24 [-0.3 a -0.2] |
| ETo | % | 5.0 | -47.52 [-51.6 a -45.0] | -50.71 [-54.6 a -53.4] | -51.21 [-53.9 a -49.8] | -49.40 [-51.8 a -47.8] | -49.65 [-48.5 a -45.2] | -49.27 [-52.6 a -48.6] |
| Radiação solar | MJ/m²/dia | 0.5 | -1.08 [-3.3 a -0.6] | ⚠️ +0.19 [-2.4 a -1.2] | -0.67 [-2.7 a -0.7] | -1.12 [-2.0 a -0.4] | -0.96 [-1.9 a -0.2] | -0.77 [-2.8 a -0.7] |
| Vento | m/s | 0.2 | +0.01 [-0.2 a -0.1] | ⚠️ -0.33 [-0.6 a -0.6] | -0.27 [-0.3 a -0.2] | -0.40 [-0.4 a -0.4] | -0.26 [-0.2 a -0.1] | -0.17 [-0.3 a -0.3] |
| ET real | % | 5.0 | -19.28 [-24.3 a -20.3] | -13.01 [-9.9 a -6.3] | -16.98 [-16.4 a -12.0] | -7.52 [-9.1 a -5.8] | -8.07 [-14.6 a -5.8] | -16.27 [-18.1 a -15.6] |
| Transpiração | % | 5.0 | -12.00 [-11.9 a -2.3] | ⚠️ -22.03 [-15.1 a -12.8] | -8.48 [-6.2 a -1.5] | +1.77 [-3.2 a +3.1] | +7.23 [+4.2 a +14.6] | -10.01 [-8.3 a -3.4] |
| Escoamento superficial | % | 5.0 | ⚠️ +351.70 [+223.6 a +322.6] | +407.25 [+330.8 a +402.3] | +86.32 [+49.0 a +231.7] | ⚠️ +194.20 [+73.2 a +131.5] | ⚠️ +146.37 [+39.2 a +65.4] | ⚠️ +271.38 [+176.3 a +235.3] |
| Escoamento subsuperficial | % | 5.0 | ⚠️ -75.69 [-82.8 a -81.0] | -92.89 [-91.6 a -89.9] | -90.30 [-89.0 a -81.6] | -82.19 [-86.1 a -70.5] | ⚠️ -60.41 [-79.4 a -77.3] | -77.45 [-83.1 a -82.2] |
| Temperatura do solo | °C | 0.5 | ⚠️ +0.60 [+1.5 a +1.7] | +1.59 [+1.6 a +1.8] | ⚠️ +1.24 [+1.9 a +2.2] | +1.21 [+1.6 a +1.9] | +1.14 [+1.5 a +1.6] | ⚠️ +1.01 [+1.7 a +1.8] |
| Temperatura da folha | °C | 0.5 | ⚠️ +0.03 [+1.0 a +1.1] | +1.05 [+1.1 a +1.3] | ⚠️ +0.73 [+1.4 a +1.6] | +0.75 [+1.2 a +1.4] | +0.62 [+1.0 a +1.1] | ⚠️ +0.47 [+1.2 a +1.2] |
| Umidade do solo 0-5 cm | m³/m³ | 0.02 | +0.02 [-0.0 a +0.0] | -0.05 [-0.1 a -0.0] | -0.05 [-0.0 a -0.0] | -0.05 [-0.1 a -0.0] | +0.00 [-0.0 a -0.0] | -0.02 [-0.0 a -0.0] |
| Umidade do solo 0-100 cm | m³/m³ | 0.02 | +0.03 [+0.0 a +0.0] | -0.01 [-0.0 a -0.0] | -0.02 [-0.0 a +0.0] | -0.02 [-0.0 a -0.0] | +0.03 [+0.0 a +0.0] | +0.01 [-0.0 a +0.0] |

**Suspeitas em 2026:** Chuva no Nordeste; Chuva no Centro-Oeste; Radiação solar no Nordeste; Vento no Nordeste; Transpiração no Nordeste; Escoamento superficial no Norte; Escoamento superficial no Sudeste; Escoamento superficial no Sul; Escoamento superficial no Brasil; Escoamento subsuperficial no Norte; Escoamento subsuperficial no Sul; Temperatura do solo no Norte; Temperatura do solo no Centro-Oeste; Temperatura do solo no Brasil; Temperatura da folha no Norte; Temperatura da folha no Centro-Oeste; Temperatura da folha no Brasil

### Histórico por década × TerraClimate e CHIRPS

Arquivo: `pesquisa/resultados_historico/RESULTADOS.md`

(ainda não rodou)

### Tudo por mês do ano

Arquivo: `pesquisa/RESULTADOS_POR_MES.md`

(ainda não rodou)

### Sensibilidade à resolução

Arquivo: `pesquisa/resultados_resolucao/RESULTADOS.md`

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
| 26/11/2026 09:12 | Conferência: começou fase2_leva1  |
| 26/11/2026 09:12 | Conferência: fase2_leva1 (pendente)  |
| 26/11/2026 08:36 | Conferência: fase2_leva2 (ok)  |
| 26/11/2026 06:14 | Fila: o corte por tempo não conta como tentativa |
| 26/11/2026 04:16 | Conferência: começou fase2_leva2  |
| 26/11/2026 04:16 | Registro: leva 2 disparada |
| 26/11/2026 04:16 | Fase 2, leva 2 (só leitura): radiação por quantis regionais R2 (M2) e janela de 10 anos T1 para Tmax, Tmin e vento (M3); tarefa fase2_leva2 na fila |
| 26/11/2026 04:01 | Conferência: começou fase2_leva1  |
| 26/11/2026 04:01 | Conferência: fase2_leva1 (pendente)  |
| 25/11/2026 23:40 | Registro: o que será corrigido e a etapa final automática |
| 25/11/2026 23:22 | Registro: várias referências disparadas |
| 25/11/2026 23:19 | Protocolo da fase 2, emenda 1 (antes de rodar o M5): várias referências por variável; degrau confirmado em 2 independentes |
| 25/11/2026 23:10 | Registro: historico pronto |
| 25/11/2026 22:48 | Registro: fase 2 |
| 25/11/2026 22:48 | Conferência: começou fase2_leva1  |
| 25/11/2026 22:47 | Fase 2, leva 1 (só leitura): garoa C3G/C3RG (M1), radiação R1 (M2), Tmax/Tmin/UR/vento T2 (M3); tarefa fase2_leva1 na fila |
| 25/11/2026 22:45 | Fase 2, M1-C3R: não passa (mediana +0,8 p.p., r_anom -0,022); o C3 fica. Achado: o C3 piora os dias de chuva (9,5 -> 12,6 p.p.), alvo do M1-C3G |
| 25/11/2026 22:40 | Protocolo da fase 2 (correção de todas as variáveis): congelado antes de qualquer resultado |
| 25/11/2026 22:20 | Registro: V1.8 aprovada (PR sab-motor#4) |
| 25/11/2026 22:17 | Registro: a vigia dispara as rotinas por relógio |
| 25/11/2026 22:14 | Registro: K26 rodada 7 pronta |
| 25/11/2026 21:03 | Registro: relato 2026 x CHIRPS da correção |
| 25/11/2026 20:35 | Registro: prévia da V1.8 (1 dia) passou |
| 25/11/2026 20:16 | Registro: vigia automática e mapa da verificação |
| 25/11/2026 20:15 | Conferência: correcao_era5 (ok)  |
| 25/11/2026 20:08 | Registro: motor V1.8 etapa A e fila da main |
| 25/11/2026 20:01 | Conferência: começou correcao_era5  |
| 25/11/2026 20:01 | Registro: sab-pedidos público |
| 25/11/2026 20:00 | Fila: correcao_era5 volta para a fila (falta só 2026 x CHIRPS; repositório agora público) |
| 25/11/2026 18:29 | Registro: resultado da correção e minutos do Actions esgotados |
| 25/11/2026 18:29 | Correção ERA5: resultado com os 10 anos de teste — chuva troca para C3 (passa nas 4 condições); radiação/ETo: nenhum passa (o C0 fica). 2026 x CHIRPS pendente (sem minutos do GitHub) |
| 25/11/2026 18:28 | Correção ERA5: mês do 2026 x CHIRPS como int do Python (o Earth Engine recusa o int64 do numpy) |
| 25/11/2026 17:35 | Conferência: correcao_era5 (falhou)  |
| 25/11/2026 17:35 | Conferência: começou correcao_era5  |
| 25/11/2026 17:35 | Conferência: correcao_era5 (pendente)  |
| 25/11/2026 17:35 | Conferência: começou correcao_era5  |
| 25/11/2026 17:35 | Conferência: correcao_era5 (pendente)  |
| 25/11/2026 16:31 | Conferência: começou correcao_era5  |
| 25/11/2026 16:30 | Fila: repete a chamada da próxima execução se o GitHub responder erro (500 em 25/11 parou a cadeia) |
| 25/11/2026 16:15 | Conferência: correcao_era5 (pendente)  |
| 25/11/2026 15:55 | Registro em dia (25/11, ~13h): o que roda, decisões e o que falta auditar e corrigir |
| 25/11/2026 15:43 | Registro: rotina de saúde renomeada (PR #11); agendamentos atrasados |
| 25/11/2026 15:34 | Registro: resolucao roda completa (decisão do responsável); ritmo das cadeias |
| 25/11/2026 11:10 | Conferência: começou correcao_era5  |
| 25/11/2026 11:09 | Correção ERA5: a banda do sorteio dos pixels em inteiro (stratifiedSample); receita conferida (maior diferença 1,55%) |
| 25/11/2026 11:08 | Conferência: começou correcao_era5  |
| 25/11/2026 11:08 | Conferência: correcao_era5 (pendente)  |
| 25/11/2026 11:00 | Conferência: começou correcao_era5  |
| 25/11/2026 10:59 | Correção ERA5: climatologia do ERA5 pelo produto mensal e pedidos região por região (a 1ª tentativa estourou a memória); tarefa volta para a fila |
| 25/11/2026 10:57 | Conferência: começou correcao_era5  |
| 25/11/2026 10:57 | Conferência: correcao_era5 (pendente)  |
| 25/11/2026 10:48 | Conferência: começou correcao_era5  |
| 25/11/2026 10:48 | Registro: teste da correção disparado (emenda 1: extremos em todos os pixels) |
| 25/11/2026 10:47 | Protocolo da correção, emenda 1 (antes de rodar): extremos em todos os pixels entregues (dias de chuva e Rx1day por região) e p99 em 1.500 pixels |
| 25/11/2026 10:04 | Registro: script do teste da correção pronto, esperando autorização do disparo |
| 25/11/2026 10:04 | Teste da correção dos dias ERA5 (só leitura): script, testes sem Earth Engine e tarefa na fila (não disparada) |
| 25/11/2026 09:56 | Merge remote-tracking branch 'origin/validacoes-2' into claude/tender-maxwell-6ka6dt |
| 25/11/2026 09:56 | Registro: Parte B pronta (2026 x GLDAS confirma a chuva baixa no Nordeste e no Centro-Oeste); protocolo da correção aprovado e congelado |
| 25/11/2026 09:56 | Protocolo da correção dos dias ERA5: APROVADO e congelado antes de rodar (2026 x CHIRPS só como relato) |
| 25/11/2026 09:55 | Registro: protocolo da correção aprovado e congelado; próximo passo é o script do teste |
| 25/11/2026 09:55 | Protocolo da correção dos dias ERA5: APROVADO e congelado antes de rodar (2026 x CHIRPS só como relato) |
| 25/11/2026 09:53 | Merge remote-tracking branch 'origin/claude/tender-maxwell-6ka6dt' into claude/tender-maxwell-6ka6dt |
| 25/11/2026 09:53 | Registro: Parte B pronta (2026 x GLDAS confirma a chuva baixa no Nordeste e no Centro-Oeste); rascunho do protocolo trazido para o branch de trabalho |
| 25/11/2026 09:47 | Rascunho do protocolo: correção da chuva, radiação e ETo dos dias ERA5 (para aprovação; nada gravado) |
| 25/11/2026 09:50 | Registro: linha de 25/11 dentro da tabela da linha do tempo |
| 25/11/2026 09:50 | Registro: branches das conversas (claude/*), decisões esperando o responsável, protocolo da correção em rascunho e comando de retomada que busca todos os branches |
| 25/11/2026 09:47 | Conferência: metodo_2026_B (ok)  |
| 25/11/2026 09:33 | Entrega: a base de montagem (pasta 07), os extras e um script que remonta o zip só com o repositório |
| 25/11/2026 08:33 | Registro: resultado da Parte A (o método de 2026 subestima a chuva ~10% em 2021-2025) e o próximo trabalho |
| 25/11/2026 07:43 | Conferência: começou metodo_2026_B  |
| 25/11/2026 07:43 | Conferência: metodo_2026_A (ok)  |
| 25/11/2026 07:33 | Conferência: começou resolucao  |
| 25/11/2026 07:32 | Resolução: as duas médias voltam numa coleção só (o dicionário não trazia as features); fila limpa os campos da tentativa anterior; ponto de continuação revisto depois do teste de retomada |
| 25/11/2026 07:32 | Conferência: resolucao (falhou)  |
| 25/11/2026 07:26 | Conferência: começou resolucao  |
| 25/11/2026 07:26 | Conferência: resolucao (pendente)  |
| 25/11/2026 07:22 | Conferência: começou resolucao  |
| 25/11/2026 07:22 | Conferência: resolucao (pendente)  |
| 25/11/2026 07:20 | Registro: ponto de continuação para uma conversa nova e o registro geral em dia |
| 25/11/2026 07:15 | Conferência: começou resolucao  |
| 25/11/2026 07:15 | Conferência: começou historico  |
| 25/11/2026 07:14 | Mais pontos e o peso deles: 27 estados, intervalo de confiança e sensibilidade à resolução na fila |
| 25/11/2026 07:05 | Métodos: resolução de cada fonte, como entra na grade do SAB e por que pesa pouco nas médias regionais |
| 25/11/2026 07:04 | Conferência: começou historico  |
| 25/11/2026 07:04 | Validar histórico: a chuva do SAB é a banda pr_mm (a do TerraClimate é pr); nomes conferidos dos dois lados |
| 25/11/2026 07:02 | Conferência: começou historico  |
| 25/11/2026 07:02 | Conferência: historico (pendente)  |
| 25/11/2026 07:01 | Replicação: métodos completos e todas as métricas (região x período x mês) num arquivo só |
| 25/11/2026 06:58 | Conferência: começou historico  |
| 25/11/2026 06:57 | Validar histórico: a chuva do TerraClimate é a banda pr (não ppt); a tarefa volta para a fila |
| 25/11/2026 06:57 | Conferência: historico (falhou)  |
| 25/11/2026 06:53 | Conferência: começou historico  |
| 25/11/2026 06:53 | Conferência: historico (pendente)  |
| 25/11/2026 06:50 | Conferência: começou historico  |
| 25/11/2026 06:50 | Conferência: historico (pendente)  |
| 25/11/2026 06:48 | Registro geral do SAB: do início do código às últimas atualizações (refeito sozinho pela fila) |
| 25/11/2026 06:46 | Conferência: começou historico  |
| 25/11/2026 06:46 | Validação do histórico 1961-2025 por década (TerraClimate e CHIRPS) e resumo por mês do ano |
| 25/11/2026 06:41 | Conferência: começou metodo_2026_A  |
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
| 15/11/2026 20:29 | Manutenção: versões fixas das bibliotecas e actions no Node 24 |
| 04/11/2026 08:17 | sab_pedido.py |
| 04/11/2026 08:14 | sab_pedido.py |
| 03/11/2026 22:58 | sab_pedido.py |
| 01/11/2026 17:52 | Delete .github/workflows/motor_05b.yml |
| 01/11/2026 17:52 | Delete testes/teste_rodar_motor.py |
| 01/11/2026 17:49 | Add files via upload |
| 01/11/2026 17:48 | Add files via upload |
| 01/11/2026 17:14 | Add files via upload |
| 01/11/2026 17:14 | Add files via upload |
| 01/11/2026 17:13 | Add files via upload |
| 01/11/2026 17:11 | Add files via upload |
| 01/11/2026 17:08 | pedido_sab.yml |
| 01/11/2026 17:06 | README.md |
| 01/11/2026 17:05 | requirements.txt |
| 01/11/2026 17:04 | fumaca_sab_pedido.py |
| 01/11/2026 17:03 | teste_sab_pedido.py |
| 01/11/2026 17:01 | sab_pedido.py |
| 01/11/2026 08:47 | sab_pedido.py |
| 01/11/2026 08:18 | pedido_sab.yml |
| 01/11/2026 08:11 | pedido_sab.yml |
| 01/11/2026 07:11 | sab_pedido.py |
| 01/11/2026 01:53 | sab_pedido.py |
| 01/11/2026 01:29 | sab_pedido.py |
| 01/11/2026 01:19 | Rename sab_pedido_v2.py to sab_pedido.py |
| 01/11/2026 01:17 | Delete sab_pedido.py |
| 01/11/2026 01:16 | Add files via upload |
| 01/11/2026 00:33 | sab_pedido.py |

