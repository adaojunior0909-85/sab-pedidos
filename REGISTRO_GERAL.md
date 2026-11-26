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
| 25/11, noite | **Fase 1 pronta**: chuva dos dias ERA5 → C3 (passa nas 4 condições); radiação/ETo ficam. **V1.8** (C3 na gravação) montada no `sab-motor` (PR #4) e aprovada pelo responsável ("Junte e aprove o V1.8"), com merge combinado para depois da prévia de 26/11. **Protocolo da fase 2** (correção de todas as variáveis; analisar antes, gravar só com autorização) congelado (9a12309) e **emenda 1** (várias referências: TerraClimate, CHIRPS, PERSIANN-CDR, IMERG, GLDAS-2.0/2.1, ERA5-Land, MOD16; confirmação em ≥ 2 independentes). M1-C3R e leva 2 (R2, T1) **não passaram**. `sab-pedidos` tornado público (minutos do GitHub) | `pesquisa/PROTOCOLO_CORRECAO_FASE2.md`, `pesquisa/resultados_fase2/` |
| 26/11 | **Merge da V1.8 suspenso** (07h15): a chuva do banco sobe de repente em **2020** contra GLDAS-2.1, IMERG, PERSIANN-CDR, TerraClimate e (no Norte/Nordeste) CHIRPS, e fica +10 a +18% até 2024; as razões da V1.8 saem justamente de 2021–2025. **Investigação do BR-DWGD**: leitura dos artigos (Xavier 2016 e 2022), do site oficial e do relatório da **v_3.2.4** (1961–2025; 15.116 pluviômetros; rede de ~5.700 em 2020–2024, densa; **fim de 2025 ralo**); IMERG, PERSIANN e GLDAS-2.1 dependem do GPCC (contam como uma família). Suspeito principal: composição da rede do BR-DWGD (não provado). `investigar_brdwgd.py` na fila (BR bruto × CHIRPS × ERA5-Land, ano a ano) | `pesquisa/resultados_brdwgd/ANALISE_DOS_ARTIGOS.md` |

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
| 10 variáveis | TerraClimate (e chuva × CHIRPS) por década, 5 regiões + 27 estados | 1961–2025 | **pronto**: chuva com degrau em **2021–2025 em todas as regiões** × TerraClimate (Brasil +11,2%; até 2020, ±3%); × CHIRPS sem degrau na média da década (o CHIRPS também usa estações), mas +7 a +10% no Norte/Nordeste ano a ano. `pesquisa/resultados_historico/RESULTADOS.md` |
| Todas (várias referências) | TerraClimate, CHIRPS, PERSIANN-CDR, IMERG, GLDAS-2.0/2.1, ERA5-Land, MOD16 (emenda 1 da fase 2) | 1961–2025 | parcial (ERA5-Land e GLDAS-2.0 ainda na fila). **Confirmados** (≥ 2 independentes): chuva Brasil 2021–2025; UR Nordeste 1961–70; ETo Norte 2001–10; ET real Sudeste 2001–10. `pesquisa/resultados_multifonte/RESULTADOS.md` |
| Fase 2 (correção de todas) | BR-DWGD fora da amostra | 2016–2025 | M1-C3R ❌; M2-R2 ❌ (ETo +0,82 p.p., precisava 1); M3-T1 ❌; leva 1 (C3G, C3RG, R1, T2) na fila. `pesquisa/resultados_fase2/` |
| BR-DWGD bruto | CHIRPS diário, ERA5-Land bruto; artigos e site do autor | 1961–2025 | na fila; leitura dos documentos pronta: `pesquisa/resultados_brdwgd/ANALISE_DOS_ARTIGOS.md` |
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
- **A chuva do BR-DWGD de 2020 em diante** fica 10–18% acima da relação das décadas anteriores com TerraClimate,
  GLDAS-2.1, IMERG e PERSIANN (no Norte e Nordeste também com o CHIRPS); causa sob investigação (composição da rede
  na v_3.2.4). O **fim de 2025** tem poucos pluviômetros (dados ainda não liberados pelos órgãos).

---

# Apêndice automático (refeito em 26/11/2026 08:55, Brasília)

## A. Situação das rotinas automáticas (de `rotinas/PAINEL.md`)

| Rotina | Quando roda | Última execução | Situação | Resumo |
|---|---|---|---|---|
| Saúde do banco (motor gravou?) | toda segunda-feira, 14h29 | 24/11/2026 20:27 | ✅ | 343 dias de 2026 (319 ERA5 até 2026-11-15, 24 GFS até 2026-12-09); dia 2026-11-24 gravado há 11 h; versões {'V1.6': 343}; histórico intocado |
| RONI do mês (02_auditoria_roni_cpc.py) | todo dia 11, 10h23 | 24/11/2026 21:14 | ✅ | asset RONI_CPC_v6 regravado e conferido (921 estações) |
| K26, rodada 1 (2026 inteiro, só leitura) | todo dia 15, 15h41 | 24/11/2026 20:56 | 👀 | 343 dias de 2026 (até 2026-12-09); itens: A1 OK, B ATENCAO, C FALHA, G FALHA, H OK |
| Acerto da previsão GFS (1 a 15 dias) | todo dia, 16h13 | 24/11/2026 22:16 | ✅ | fotografia de 2026-11-24: 24 dias GFS (2026-11-16 a 2026-12-09) e a persistência (2026-11-15) |
| Conferência final (validações, escoamento e K26 de 1961 até a previsão) | de 2 em 2 horas, 10h17 a 20h17, até a fila acabar (depois desliga sozinha) | 25/11/2026 04:02 | ⏳ | 0 de 1 tarefas prontas |
| Piloto da previsão estendida (Tmin e Tmax) | dias 3 e 17, 08h17 | 24/11/2026 20:19 | ✅ | 1 emissão(ões); a última em 2026-11-16 |

## B. Resultado de cada validação

Cada bloco é a cópia do arquivo de resultado no momento em que este registro foi refeito.

### Conferência final (fila)

Arquivo: `rotinas/conferencia/CONFERENCIA_FINAL.md`

#### Conferência final do SAB (1961 até a previsão)

Atualizado em 25/11/2026 04:02 (Brasília) pela fila automática (`rotinas/conferencia/fila.py`). Ainda há tarefas na fila.

| Tarefa | Situação | Tentativas | Quando | Resultado |
|---|---|---|---|---|
| O histórico 1961-2025, década por década, contra TerraClimate e CHIRPS | ⏳ na fila | 1 | 25/11 04:02 | pesquisa/resultados_historico/RESULTADOS.md |

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

#### O histórico do SAB década por década (1961–2025) contra TerraClimate e CHIRPS

Em cada célula: viés da década (somas: % do total; médias: diferença na unidade) / correlação das anomalias mensais. ⚠️ = degrau (regra fixada antes de rodar, no cabeçalho do `pesquisa/validar_historico.py`). A umidade do solo do TerraClimate é em mm: só a correlação vale.

##### Chuva (TerraClimate)

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | +6.0 / 0.70 | -4.2 / 0.99 | -2.6 / 0.89 | -1.5 / 0.92 | +0.3 / 0.97 | +2.4 / 0.83 |
| 1971-1980 | +0.4 / 0.82 | -4.4 / 1.00 | +1.1 / 0.84 | +2.1 / 0.93 | +2.1 / 0.96 | +0.3 / 0.93 |
| 1981-1990 | +3.7 / 0.87 | -2.2 / 1.00 | +0.7 / 0.86 | ⚠️ +5.6 / 0.96 | +7.4 / 0.94 | +2.9 / 0.93 |
| 1991-2000 | -0.9 / 0.80 | -0.3 / 0.94 | -4.5 / 0.69 | -0.1 / 0.84 | +4.5 / 0.92 | -1.1 / 0.82 |
| 2001-2010 | -2.3 / 0.75 | -4.5 / 0.96 | -3.8 / 0.80 | -2.8 / 0.89 | +3.2 / 0.94 | -2.5 / 0.84 |
| 2011-2020 | +1.6 / 0.78 | -2.9 / 0.93 | -2.8 / 0.69 | -1.1 / 0.87 | +6.8 / 0.90 | +0.5 / 0.81 |
| 2021-2025 | ⚠️ +11.7 / 0.95 | ⚠️ +10.4 / 0.96 | ⚠️ +10.8 / 0.93 | ⚠️ +5.9 / 0.98 | ⚠️ +16.6 / 0.98 | ⚠️ +11.2 / 0.94 |

##### Chuva (CHIRPS, desde 1981)

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | - | - | - | - | - | - |
| 1971-1980 | - | - | - | - | - | - |
| 1981-1990 | -1.0 / 0.96 | -0.5 / 1.00 | -1.1 / 0.98 | +1.4 / 0.98 | +2.2 / 0.99 | -0.5 / 0.97 |
| 1991-2000 | -1.8 / 0.97 | -0.9 / 0.99 | -0.7 / 0.98 | +0.4 / 0.99 | +2.2 / 0.99 | -1.0 / 0.97 |
| 2001-2010 | -3.0 / 0.96 | -2.5 / 0.99 | -2.1 / 0.99 | +0.7 / 0.99 | +0.2 / 0.99 | -2.3 / 0.97 |
| 2011-2020 | -3.6 / 0.89 | -5.7 / 0.96 | ⚠️ -7.4 / 0.90 | -3.2 / 0.95 | -1.1 / 0.95 | -4.3 / 0.87 |
| 2021-2025 | +0.2 / 0.93 | +3.9 / 0.98 | -5.3 / 0.90 | +1.3 / 0.97 | +4.1 / 0.99 | +0.0 / 0.93 |

##### Tmax

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | +0.0 / 0.77 | +0.8 / 0.53 | +0.4 / 0.68 | +1.2 / 0.88 | +0.8 / 0.94 | +0.4 / 0.80 |
| 1971-1980 | +0.1 / 0.78 | +0.5 / 0.75 | +0.4 / 0.82 | +0.7 / 0.77 | +0.5 / 0.89 | +0.3 / 0.79 |
| 1981-1990 | +0.2 / 0.89 | +0.7 / 0.94 | +0.6 / 0.87 | +0.9 / 0.83 | +0.6 / 0.86 | +0.5 / 0.91 |
| 1991-2000 | +0.3 / 0.92 | +0.9 / 0.95 | +0.7 / 0.93 | +1.1 / 0.84 | +0.7 / 0.88 | +0.6 / 0.94 |
| 2001-2010 | +0.6 / 0.87 | +1.1 / 0.93 | +0.8 / 0.85 | +1.1 / 0.94 | +0.6 / 0.91 | +0.8 / 0.89 |
| 2011-2020 | +0.5 / 0.87 | +1.3 / 0.90 | +0.8 / 0.82 | +1.0 / 0.84 | +0.6 / 0.90 | +0.8 / 0.87 |
| 2021-2025 | +0.6 / 0.97 | ⚠️ +1.5 / 0.90 | +1.1 / 0.91 | +1.5 / 0.96 | +0.8 / 0.92 | +1.0 / 0.96 |

##### Tmin

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | ⚠️ +0.1 / 0.61 | ⚠️ +0.4 / 0.11 | ⚠️ +0.4 / 0.38 | ⚠️ +0.9 / 0.83 | +0.6 / 0.95 | ⚠️ +0.3 / 0.60 |
| 1971-1980 | +0.8 / 0.60 | +1.3 / 0.44 | +1.2 / 0.72 | +1.5 / 0.74 | +1.2 / 0.97 | +1.1 / 0.76 |
| 1981-1990 | +0.7 / 0.71 | +1.0 / 0.67 | +1.2 / 0.73 | +1.3 / 0.72 | +1.3 / 0.88 | +0.9 / 0.81 |
| 1991-2000 | +0.7 / 0.64 | +0.9 / 0.70 | +1.1 / 0.74 | +1.4 / 0.75 | +1.1 / 0.93 | +0.9 / 0.83 |
| 2001-2010 | +1.1 / 0.76 | +1.1 / 0.53 | +1.2 / 0.65 | +1.5 / 0.62 | +0.9 / 0.97 | +1.2 / 0.76 |
| 2011-2020 | +0.8 / 0.72 | +1.0 / 0.66 | +1.2 / 0.63 | +1.3 / 0.71 | +0.9 / 0.93 | +1.0 / 0.79 |
| 2021-2025 | +0.9 / 0.85 | +1.2 / 0.75 | +1.2 / 0.83 | +1.5 / 0.85 | +1.1 / 0.94 | +1.1 / 0.91 |

##### VPD

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | -0.1 / 0.55 | ⚠️ -0.1 / 0.21 | -0.1 / 0.23 | +0.0 / 0.68 | -0.1 / 0.71 | -0.1 / 0.49 |
| 1971-1980 | -0.2 / 0.57 | -0.1 / 0.46 | -0.1 / 0.65 | -0.1 / 0.69 | -0.1 / 0.72 | -0.1 / 0.63 |
| 1981-1990 | -0.1 / 0.24 | -0.0 / 0.77 | -0.1 / 0.55 | -0.0 / 0.59 | -0.1 / 0.66 | -0.1 / 0.52 |
| 1991-2000 | -0.2 / 0.73 | +0.0 / 0.68 | -0.1 / 0.65 | +0.0 / 0.57 | -0.0 / 0.67 | -0.1 / 0.75 |
| 2001-2010 | ⚠️ -0.0 / 0.35 | +0.1 / 0.60 | ⚠️ +0.0 / 0.35 | ⚠️ +0.1 / 0.62 | -0.0 / 0.65 | ⚠️ +0.0 / 0.26 |
| 2011-2020 | ⚠️ -0.0 / 0.62 | +0.1 / 0.71 | ⚠️ +0.0 / 0.71 | +0.1 / 0.59 | -0.0 / 0.74 | ⚠️ +0.0 / 0.63 |
| 2021-2025 | -0.1 / 0.98 | +0.0 / 0.95 | -0.0 / 0.90 | +0.0 / 0.98 | -0.1 / 0.98 | -0.1 / 0.97 |

##### Radiação

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | ⚠️ +2.6 / 0.01 | ⚠️ +2.5 / 0.54 | ⚠️ +3.0 / 0.28 | ⚠️ +2.6 / 0.52 | +1.3 / 0.58 | ⚠️ +2.6 / 0.32 |
| 1971-1980 | +1.8 / 0.00 | ⚠️ +2.1 / 0.33 | +2.2 / 0.28 | ⚠️ +2.4 / 0.37 | ⚠️ +1.5 / 0.40 | +2.0 / 0.09 |
| 1981-1990 | +1.3 / 0.55 | +1.8 / 0.89 | +1.8 / 0.60 | +1.8 / 0.91 | +0.8 / 0.74 | +1.5 / 0.67 |
| 1991-2000 | +1.6 / 0.47 | +1.8 / 0.81 | +2.0 / 0.72 | +1.7 / 0.86 | +1.3 / 0.84 | +1.7 / 0.68 |
| 2001-2010 | ⚠️ +2.6 / 0.60 | +1.4 / 0.86 | +1.8 / 0.60 | +1.8 / 0.91 | +1.2 / 0.76 | +2.0 / 0.71 |
| 2011-2020 | +2.1 / 0.56 | +1.8 / 0.93 | +2.1 / 0.84 | +1.9 / 0.94 | +1.0 / 0.92 | +2.0 / 0.78 |
| 2021-2025 | ⚠️ +1.1 / 0.42 | ⚠️ +1.0 / 0.80 | +1.5 / 0.73 | +1.7 / 0.83 | +0.9 / 0.76 | ⚠️ +1.2 / 0.58 |

##### Vento

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | +0.1 / 0.35 | +0.5 / 0.68 | -0.1 / 0.83 | -0.1 / 0.31 | ⚠️ -0.4 / 0.73 | +0.1 / 0.75 |
| 1971-1980 | +0.1 / 0.39 | ⚠️ +0.8 / 0.05 | -0.2 / 0.26 | +0.0 / 0.37 | ⚠️ -0.2 / 0.24 | ⚠️ +0.1 / -0.12 |
| 1981-1990 | +0.1 / 0.19 | +0.6 / 0.60 | -0.2 / 0.43 | +0.1 / 0.81 | -0.3 / 0.52 | +0.1 / 0.56 |
| 1991-2000 | +0.1 / 0.39 | +0.6 / 0.73 | -0.3 / 0.65 | -0.0 / 0.66 | -0.3 / 0.79 | +0.1 / 0.56 |
| 2001-2010 | -0.1 / 0.39 | +0.5 / 0.82 | -0.1 / 0.61 | -0.0 / 0.66 | -0.1 / 0.50 | +0.0 / 0.78 |
| 2011-2020 | ⚠️ -0.2 / 0.62 | ⚠️ +0.3 / 0.81 | -0.3 / 0.71 | -0.0 / 0.81 | -0.1 / 0.72 | -0.1 / 0.81 |
| 2021-2025 | ⚠️ -0.2 / 0.33 | ⚠️ +0.2 / 0.82 | -0.3 / 0.78 | -0.1 / 0.75 | -0.1 / 0.73 | -0.1 / 0.70 |

##### ETo

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | +12.5 / 0.30 | +16.3 / 0.63 | ⚠️ +10.6 / 0.47 | +13.4 / 0.60 | +0.9 / 0.72 | +12.2 / 0.64 |
| 1971-1980 | +7.7 / 0.34 | ⚠️ +19.6 / 0.33 | +5.9 / 0.55 | +11.4 / 0.54 | +2.6 / 0.69 | ⚠️ +9.7 / 0.47 |
| 1981-1990 | +6.2 / 0.64 | +16.4 / 0.87 | +5.0 / 0.70 | +10.4 / 0.93 | +0.3 / 0.79 | +8.1 / 0.80 |
| 1991-2000 | +7.3 / 0.67 | +17.1 / 0.82 | +5.0 / 0.79 | +9.5 / 0.90 | +2.8 / 0.88 | +8.8 / 0.81 |
| 2001-2010 | ⚠️ +14.0 / 0.72 | +15.3 / 0.90 | +8.5 / 0.74 | +11.6 / 0.93 | +3.3 / 0.84 | +12.2 / 0.85 |
| 2011-2020 | +10.4 / 0.75 | +15.8 / 0.93 | +8.1 / 0.87 | +12.2 / 0.92 | +3.4 / 0.91 | +10.8 / 0.87 |
| 2021-2025 | +3.3 / 0.79 | ⚠️ +10.4 / 0.89 | +3.6 / 0.88 | +9.5 / 0.90 | +1.6 / 0.90 | +5.3 / 0.88 |

##### ET real

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | +6.8 / 0.37 | -4.1 / 0.59 | +7.2 / 0.31 | +8.7 / 0.50 | -0.5 / -0.21 | +4.9 / 0.57 |
| 1971-1980 | +6.9 / 0.37 | +1.6 / 0.64 | +6.6 / 0.47 | +7.3 / 0.38 | +0.4 / 0.00 | +5.6 / 0.53 |
| 1981-1990 | +7.2 / 0.56 | ⚠️ +5.3 / 0.72 | +9.3 / 0.67 | +12.2 / 0.38 | +2.0 / 0.04 | +7.5 / 0.65 |
| 1991-2000 | +8.1 / 0.52 | +3.2 / 0.68 | +7.5 / 0.71 | +9.9 / 0.54 | +2.2 / 0.00 | +7.0 / 0.67 |
| 2001-2010 | +12.6 / 0.51 | -3.3 / 0.67 | +6.5 / 0.62 | +8.0 / 0.64 | +3.3 / 0.15 | +7.9 / 0.66 |
| 2011-2020 | +10.9 / 0.64 | -1.2 / 0.82 | +9.5 / 0.72 | +8.4 / 0.43 | +3.8 / 0.25 | +8.2 / 0.72 |
| 2021-2025 | +8.7 / 0.90 | +0.0 / 0.82 | +9.8 / 0.83 | +12.9 / 0.38 | ⚠️ +9.1 / 0.22 | +8.1 / 0.88 |

##### Umidade do solo 0-100 cm

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | ⚠️ -206.3 / 0.47 | -133.0 / 0.82 | -123.7 / 0.32 | -81.3 / 0.45 | -43.9 / 0.50 | -151.4 / 0.57 |
| 1971-1980 | -217.1 / 0.74 | -137.9 / 0.75 | -132.4 / 0.51 | -87.2 / 0.63 | -46.6 / 0.75 | -159.6 / 0.68 |
| 1981-1990 | -211.3 / 0.72 | -124.3 / 0.89 | -130.3 / 0.64 | -79.6 / 0.74 | -45.2 / 0.71 | -153.2 / 0.68 |
| 1991-2000 | -207.3 / 0.79 | -115.1 / 0.87 | -129.4 / 0.61 | -82.3 / 0.66 | -46.7 / 0.71 | -150.0 / 0.76 |
| 2001-2010 | -206.5 / 0.74 | -120.4 / 0.80 | -123.7 / 0.62 | -83.3 / 0.79 | -46.4 / 0.76 | -149.6 / 0.70 |
| 2011-2020 | -203.2 / 0.87 | -108.9 / 0.79 | -120.6 / 0.81 | -72.0 / 0.64 | -45.3 / 0.72 | -144.1 / 0.80 |
| 2021-2025 | -185.0 / 0.98 | -112.8 / 0.88 | -103.8 / 0.90 | -69.1 / 0.85 | -40.4 / 0.78 | -132.9 / 0.98 |

##### Escoamento total

| Década | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| 1961-1970 | ⚠️ -50.5 / 0.32 | ⚠️ -49.7 / 0.73 | ⚠️ -30.7 / 0.13 | ⚠️ -32.5 / 0.41 | -0.0 / 0.66 | -43.8 / 0.18 |
| 1971-1980 | -43.3 / 0.55 | ⚠️ -27.2 / 0.87 | -59.8 / 0.53 | -33.8 / 0.82 | +2.8 / 0.79 | -42.0 / 0.62 |
| 1981-1990 | -41.7 / 0.64 | -37.7 / 0.95 | ⚠️ -49.8 / 0.68 | ⚠️ -19.1 / 0.89 | ⚠️ +7.1 / 0.84 | -38.6 / 0.72 |
| 1991-2000 | -43.3 / 0.68 | ⚠️ -22.8 / 0.84 | -53.7 / 0.68 | ⚠️ -25.6 / 0.68 | ⚠️ +8.9 / 0.82 | -40.0 / 0.65 |
| 2001-2010 | -45.5 / 0.60 | ⚠️ -29.8 / 0.85 | -61.3 / 0.66 | ⚠️ -46.1 / 0.79 | ⚠️ -9.6 / 0.83 | -45.3 / 0.56 |
| 2011-2020 | -40.5 / 0.69 | -37.3 / 0.82 | -60.2 / 0.66 | ⚠️ -44.3 / 0.75 | ⚠️ -9.7 / 0.85 | -42.0 / 0.65 |
| 2021-2025 | -40.1 / 0.84 | -40.1 / 0.89 | -57.9 / 0.81 | ⚠️ -47.9 / 0.90 | ⚠️ -10.1 / 0.90 | -41.0 / 0.79 |

##### Degraus encontrados

Chuva (TerraClimate), Norte, 2021-2025; Chuva (TerraClimate), Nordeste, 2021-2025; Chuva (TerraClimate), Centro-Oeste, 2021-2025; Chuva (TerraClimate), Sudeste, 1981-1990; Chuva (TerraClimate), Sudeste, 2021-2025; Chuva (TerraClimate), Sul, 2021-2025; Chuva (TerraClimate), Brasil, 2021-2025; Chuva (CHIRPS, desde 1981), Centro-Oeste, 2011-2020; Tmax, Nordeste, 2021-2025; Tmin, Norte, 1961-1970; Tmin, Nordeste, 1961-1970; Tmin, Centro-Oeste, 1961-1970; Tmin, Sudeste, 1961-1970; Tmin, Brasil, 1961-1970; VPD, Norte, 2001-2010; VPD, Norte, 2011-2020; VPD, Nordeste, 1961-1970; VPD, Centro-Oeste, 2001-2010; VPD, Centro-Oeste, 2011-2020; VPD, Sudeste, 2001-2010; VPD, Brasil, 2001-2010; VPD, Brasil, 2011-2020; Radiação, Norte, 1961-1970; Radiação, Norte, 2001-2010; Radiação, Norte, 2021-2025; Radiação, Nordeste, 1961-1970; Radiação, Nordeste, 1971-1980; Radiação, Nordeste, 2021-2025; Radiação, Centro-Oeste, 1961-1970; Radiação, Sudeste, 1961-1970; Radiação, Sudeste, 1971-1980; Radiação, Sul, 1971-1980; Radiação, Brasil, 1961-1970; Radiação, Brasil, 2021-2025; Vento, Norte, 2011-2020; Vento, Norte, 2021-2025; Vento, Nordeste, 1971-1980; Vento, Nordeste, 2011-2020; Vento, Nordeste, 2021-2025; Vento, Sul, 1961-1970; Vento, Sul, 1971-1980; Vento, Brasil, 1971-1980; ETo, Norte, 2001-2010; ETo, Nordeste, 1971-1980; ETo, Nordeste, 2021-2025; ETo, Centro-Oeste, 1961-1970; ETo, Brasil, 1971-1980; ET real, Nordeste, 1981-1990; ET real, Sul, 2021-2025; Umidade do solo 0-100 cm, Norte, 1961-1970; Escoamento total, Norte, 1961-1970; Escoamento total, Nordeste, 1961-1970; Escoamento total, Nordeste, 1971-1980; Escoamento total, Nordeste, 1991-2000; Escoamento total, Nordeste, 2001-2010; Escoamento total, Centro-Oeste, 1961-1970; Escoamento total, Centro-Oeste, 1981-1990; Escoamento total, Sudeste, 1961-1970; Escoamento total, Sudeste, 1981-1990; Escoamento total, Sudeste, 1991-2000; Escoamento total, Sudeste, 2001-2010; Escoamento total, Sudeste, 2011-2020; Escoamento total, Sudeste, 2021-2025; Escoamento total, Sul, 1981-1990; Escoamento total, Sul, 1991-2000; Escoamento total, Sul, 2001-2010; Escoamento total, Sul, 2011-2020; Escoamento total, Sul, 2021-2025

### Tudo por mês do ano

Arquivo: `pesquisa/RESULTADOS_POR_MES.md`

(ainda não rodou)

### Sensibilidade à resolução

Arquivo: `pesquisa/resultados_resolucao/RESULTADOS.md`

(ainda não rodou)

### Correção dos dias ERA5 (fase 1)

Arquivo: `pesquisa/resultados_correcao_era5/RESULTADOS.md`

#### Correção da chuva, da radiação e da ETo nos dias ERA5: teste fora da amostra

Protocolo aprovado e congelado antes de rodar (`pesquisa/PROTOCOLO_CORRECAO_ERA5_2026.md`, com a emenda 1: extremos em todos os pixels). Cada ano de teste é calibrado só com os anos anteriores. Referência: o que o banco entrega (BR-DWGD no núcleo), pixels entregues. Só leitura: nada foi gravado no Earth Engine.

Conferência da receita (média 1986-2025 recalculada × `SICSB_1986_2025`, janeiro e julho, 6 regiões, chuva e radiação): maior diferença 1.55% (limite 2%).

##### Chuva: |viés anual| (mediana dos anos de teste) e r_anomalias

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil | Mediana das 5 |
|---|---|---|---|---|---|---|---|
| C0 | 6.8% (r 0.89) | 8.7% (r 0.98) | 9.8% (r 0.93) | 6.3% (r 0.98) | 8.4% (r 0.96) | 7.6% (r 0.89) | 8.39% |
| C1 | 6.3% (r 0.89) | 6.4% (r 0.98) | 7.5% (r 0.93) | 3.6% (r 0.98) | 3.1% (r 0.95) | 6.4% (r 0.89) | 6.28% |
| C2 | 6.6% (r 0.89) | 7.1% (r 0.98) | 9.2% (r 0.93) | 3.9% (r 0.98) | 4.2% (r 0.95) | 6.7% (r 0.89) | 6.59% |
| C3 | 5.5% (r 0.89) | 4.3% (r 0.98) | 5.7% (r 0.93) | 4.0% (r 0.98) | 2.6% (r 0.95) | 4.6% (r 0.90) | 4.28% |

###### Viés anual da chuva no Brasil (%)

| Ano | C0 | C1 | C2 | C3 |
|---|---|---|---|---|
| 2016 | +2.8 | +4.6 | +4.7 | +3.8 |
| 2017 | -2.2 | -2.2 | -1.4 | -1.9 |
| 2018 | -3.5 | -2.9 | -2.5 | -2.9 |
| 2019 | -7.1 | -6.5 | -6.2 | -6.2 |
| 2020 | -7.8 | -7.0 | -7.2 | -6.5 |
| 2021 | -8.6 | -7.2 | -7.8 | -5.4 |
| 2022 | -8.6 | -6.3 | -7.4 | -3.4 |
| 2023 | -13.6 | -11.1 | -12.3 | -8.1 |
| 2024 | -13.6 | -10.7 | -12.3 | -6.2 |
| 2025 | -7.3 | -2.6 | -4.7 | +3.1 |

##### Dias de chuva e maior chuva do mês, em todos os pixels entregues

Em cada célula: fração de dias com chuva (%) / erro do Rx1day (%). BR-DWGD: só a fração.

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| BR-DWGD | 64.4 | 29.7 | 41.4 | 31.7 | 36.1 | 48.0 |
| C0 | 64.1 / 48.6 | 33.3 / 53.0 | 42.3 / 44.6 | 34.1 / 43.7 | 38.5 / 39.0 | 49.1 / 46.9 |
| C1 | 64.8 / 48.8 | 33.5 / 54.0 | 42.7 / 45.4 | 34.6 / 44.5 | 39.1 / 39.9 | 49.7 / 47.5 |
| C2 | 64.7 / 48.6 | 33.4 / 53.6 | 42.7 / 45.0 | 34.6 / 44.3 | 39.0 / 39.6 | 49.6 / 47.2 |
| C3 | 64.9 / 49.3 | 33.9 / 54.0 | 43.0 / 45.1 | 34.9 / 44.1 | 39.2 / 39.5 | 49.9 / 47.6 |

##### Radiação e ETo: viés nos meses de teste

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| C0 | +0.55 MJ / +3.4% | +0.47 MJ / +2.2% | +0.41 MJ / +1.6% | +0.12 MJ / +0.0% | +0.48 MJ / +0.0% | +0.45 MJ / +2.2% |
| C1 | +0.54 MJ / +3.4% | +0.47 MJ / +2.1% | +0.38 MJ / +1.5% | +0.25 MJ / +0.6% | +0.45 MJ / -0.0% | +0.46 MJ / +2.2% |
| C2 | +0.66 MJ / +3.9% | +0.53 MJ / +2.3% | +0.42 MJ / +1.7% | +0.23 MJ / +0.5% | +0.48 MJ / +0.1% | +0.53 MJ / +2.5% |
| C3 | +0.32 MJ / +2.4% | +0.24 MJ / +1.4% | +0.21 MJ / +0.9% | +0.11 MJ / +0.1% | +0.15 MJ / -1.2% | +0.25 MJ / +1.4% |

##### Percentil 99 diário em 1500 pixels A (5.479.500 pixel-dias de 2016-2025)

Fração de dias com chuva no BR-DWGD nesses pixels: 40.8%.

| Método | Fração de dias com chuva (%) | Erro do percentil 99 |
|---|---|---|
| C0 | 42.9 | 16.8% |
| C1 | 43.3 | 13.7% |
| C2 | 43.3 | 14.3% |
| C3 | 43.6 | 13.8% |

##### Decisão (regra fixada antes)

###### Chuva

| Método | 1. mediana cai >= 3 p.p. | 2. Brasil melhora em >= 7 de 10 anos | 3. r_anom não cai > 0,02 | 4a. dias de chuva (todas as regiões) | 4b. Rx1day (todas as regiões) | 4c. p99 | Passa? |
|---|---|---|---|---|---|---|---|
| C1 | ❌ +2.11 p.p. | ✅ 9 | ✅ maior queda +0.003 | ✅ pior região +0.57 p.p. além do C0 | ✅ pior região +2.2% | ✅ 13.7% (C0 16.8%) | ❌ |
| C2 | ❌ +1.80 p.p. | ✅ 9 | ✅ maior queda +0.004 | ✅ pior região +0.50 p.p. além do C0 | ✅ pior região +1.5% | ✅ 14.3% (C0 16.8%) | ❌ |
| C3 | ✅ +4.11 p.p. | ✅ 9 | ✅ maior queda +0.003 | ✅ pior região +0.76 p.p. além do C0 | ✅ pior região +1.8% | ✅ 13.8% (C0 16.8%) | ✅ |

**Chuva: troca para C3.**

###### Radiação e ETo

| Método | |viés| da radiação no Brasil cai (MJ) | |viés| da ETo no Brasil cai (p.p.) | pior região (MJ / p.p.) | Passa? |
|---|---|---|---|---|
| C1 | -0.00 | -0.03 | +0.13 / +0.51 | ❌ |
| C2 | -0.08 | -0.33 | +0.11 / +0.53 | ❌ |
| C3 | +0.21 | +0.79 | -0.01 / +1.10 | ❌ |

**Radiação e ETo: nenhum método passou; o C0 (atual) fica.**

Nada é gravado por este teste. Se algum método passou, o próximo passo (com aprovação) é o motor em simulação (05a), a prévia de 2026 e a K16; uma janela de anos exige um asset novo (escrita, aprovação separada).

##### Só relatado (fora da regra): 2026 × CHIRPS

Meses 1 a 9; viés do total do período contra o CHIRPS (%). Régua: 2024, quando o SAB é o BR-DWGD. Método vencedor na chuva: C3.

| Região | 2024 (régua) | 2026 gravado | 2026 C0 | 2026 C1 | 2026 C2 | 2026 C3 |
|---|---|---|---|---|---|---|
| Norte | +2.4 | -1.2 | -1.3 | +3.5 | +0.8 | +7.1 |
| Nordeste | +6.6 | -15.6 | -15.9 | -10.8 | -12.7 | -4.1 |
| Centro-Oeste | -1.4 | -21.3 | -21.3 | -15.2 | -17.9 | -10.0 |
| Sudeste | -1.1 | -2.9 | -2.9 | +3.3 | +1.7 | +5.6 |
| Sul | +3.8 | +4.1 | +4.4 | +13.4 | +11.5 | +15.5 |
| Brasil | +2.3 | -5.8 | -5.9 | -0.4 | -2.9 | +3.6 |

### Fase 2, M1-C3R

Arquivo: `pesquisa/resultados_fase2/RESULTADOS_M1_C3R.md`

#### Fase 2, M1-C3R: a razão do C3 só onde o viés é consistente

Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (congelado no commit 9a12309 antes de rodar). Sem Earth Engine: os dados da fase 1. Base de comparação: o C3 (a V1.8).

Razão aplicada em 312 de 600 combinações ano-alvo × mês × região (52%). Pesos do Brasil (área): Norte 0.443, Nordeste 0.180, Centro-Oeste 0.192, Sudeste 0.113, Sul 0.072 (conferência no C3: erro máx. 0.00%).

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Mediana das 5 |
|---|---|---|---|---|---|---|
| C0 | 6.8% (r 0.89) | 8.7% (r 0.98) | 9.8% (r 0.93) | 6.3% (r 0.98) | 8.4% (r 0.96) | 8.39% |
| C3 | 5.5% (r 0.89) | 4.3% (r 0.98) | 5.7% (r 0.93) | 4.0% (r 0.98) | 2.6% (r 0.95) | 4.28% |
| C3R | 5.1% (r 0.87) | 5.3% (r 0.98) | 5.7% (r 0.93) | 3.8% (r 0.97) | 4.2% (r 0.95) | 5.09% |

| Método | Dias de chuva: afastamento somado (p.p.) | p99 (1.500 pixels) |
|---|---|---|
| C0 | 9.54 | 16.8% |
| C3 | 12.56 | 13.8% |
| C3R | 12.00 | 14.1% |

##### Regra (contra o C3)

1. mediana não piora > 0,5 p.p.: ❌ (+0.80 p.p.)
2. dias de chuva −20% (+4.5%) ou pior região (Centro-Oeste) −2 p.p. (+0.09 p.p.): ❌
3. r_anomalias não cai > 0,02: ❌ (maior queda +0.022)
4. Rx1day e p99 não crescem > 5%: ✅

**M1-C3R: não passa; o C3 (V1.8) fica.**

##### Só relato: 2026 × CHIRPS (jan–set, viés do total, %)

| Região | 2024 (régua) | 2026 C0 (V1.7) | 2026 C3 (V1.8) | 2026 C3R |
|---|---|---|---|---|
| Norte | +2.4 | -1.3 | +7.1 | +6.0 |
| Nordeste | +6.6 | -15.9 | -4.1 | -4.1 |
| Centro-Oeste | -1.4 | -21.3 | -10.0 | -10.0 |
| Sudeste | -1.1 | -2.9 | +5.6 | +5.3 |
| Sul | +3.8 | +4.4 | +15.5 | +11.6 |

### Fase 2, leva 1

Arquivo: `pesquisa/resultados_fase2/RESULTADOS_LEVA1.md`

(ainda não rodou)

### Fase 2, leva 2

Arquivo: `pesquisa/resultados_fase2/RESULTADOS_LEVA2.md`

#### Fase 2, leva 2: M2-R2 (quantis da radiação) e M3-T1 (janela de 10 anos)

Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (congelado antes de rodar). Só leitura. Nada é gravado sem autorização do responsável.

##### M2-R2. Radiação e ETo

| Região | V1.7: radiação / ETo | R2: radiação / ETo |
|---|---|---|
| Norte | +0.55 MJ / +3.4% | +0.31 MJ / +2.3% |
| Nordeste | +0.47 MJ / +2.2% | +0.23 MJ / +1.4% |
| Centro-Oeste | +0.41 MJ / +1.6% | +0.20 MJ / +0.8% |
| Sudeste | +0.12 MJ / +0.0% | +0.13 MJ / +0.1% |
| Sul | +0.48 MJ / +0.0% | +0.27 MJ / -0.7% |
| Brasil | +0.45 MJ / +2.2% | +0.25 MJ / +1.4% |

R2: radiação no Brasil +0.21 MJ (≥ 0,2) · ETo +0.82 p.p. (≥ 1) · pior região +0.01 MJ / +0.68 p.p. · r_anom +0.039 → **❌ não passa; a V1.7 fica**

##### M3-T1. Tmax, Tmin, VPD e vento

| Variável | V1.7: viés Brasil | T1: viés Brasil | Pior região (piora) | r_anom (maior queda) | Passa? |
|---|---|---|---|---|---|
| tmax_C | +0.157 | +0.141 | -0.033 | +0.008 | ❌ |
| tmin_C | -0.034 | +0.013 | +0.001 | +0.017 | ❌ |
| vpd | +0.008 | +0.009 | +0.012 | +0.004 | ❌ |
| u2 | +0.067 | +0.040 | +0.027 | +0.045 | ❌ |

### Várias referências (multifonte)

Arquivo: `pesquisa/resultados_multifonte/RESULTADOS.md`

#### O banco contra várias referências (1961–2025)

Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md`, emenda 1 (antes de rodar). Viés da década / correlação das anomalias mensais, por fonte. ⚠️ = degrau naquela fonte. **Confirmado** = degrau em ≥ 2 referências independentes (GLDAS-2.0 e 2.1 = uma; ERA5-Land não conta para as variáveis do modelo). Todas as comparações (também os 27 estados) em `TODAS_AS_COMPARACOES.csv`.

##### Fontes já comparadas

| Fonte | Variáveis | Anos com dado |
|---|---|---|
| chirps | Chuva | 1981–2024 |
| era5 | Chuva, Radiação, Tmax, Tmin, Umidade relativa, VPD, Vento | 1961–2005 |
| gldas20 | Chuva, ET real, ETo, Escoamento total, Radiação, Temperatura da folha, Temperatura do solo, Tmax, Tmin, Transpiração, Umidade do solo 0-100 cm, Umidade do solo 0-5 cm, Umidade relativa, VPD, Vento | 1961–2001 |
| gldas21 | Chuva, ET real, ETo, Escoamento total, Radiação, Temperatura da folha, Temperatura do solo, Tmax, Tmin, Transpiração, Umidade do solo 0-100 cm, Umidade do solo 0-5 cm, Umidade relativa, VPD, Vento | 2000–2025 |
| imerg | Chuva | 2000–2025 |
| mod16 | ET real, ETo | 2001–2025 |
| persiann | Chuva | 1983–2025 |
| terraclimate | Chuva, ET real, ETo, Escoamento total, Radiação, Tmax, Tmin, Umidade do solo 0-100 cm, VPD, Vento | 1961–2024 |

##### Degraus confirmados (≥ 2 referências independentes)

| Variável | Região | Década | Fontes que marcam |
|---|---|---|---|
| Umidade relativa | Nordeste | 1961-1970 | ERA5-Land, GLDAS |
| ETo | Norte | 2001-2010 | GLDAS, TerraClimate |
| ET real | Sudeste | 2001-2010 | GLDAS, MOD16 |
| Chuva | Brasil | 2021-2025 | GLDAS, IMERG, PERSIANN, TerraClimate |
| Chuva | Centro-Oeste | 2021-2025 | GLDAS, IMERG, PERSIANN, TerraClimate |
| Chuva | Nordeste | 2021-2025 | GLDAS, IMERG, PERSIANN, TerraClimate |
| Chuva | Norte | 2021-2025 | GLDAS, IMERG, PERSIANN, TerraClimate |
| Chuva | Sul | 2021-2025 | GLDAS, IMERG, PERSIANN, TerraClimate |
| Radiação | Brasil | 2021-2025 | GLDAS, TerraClimate |
| Radiação | Centro-Oeste | 1961-1970 | ERA5-Land, TerraClimate |
| Radiação | Nordeste | 2021-2025 | GLDAS, TerraClimate |
| Radiação | Norte | 1991-2000 | ERA5-Land, GLDAS |
| Radiação | Norte | 2001-2010 | GLDAS, TerraClimate |
| Escoamento total | Centro-Oeste | 1961-1970 | GLDAS, TerraClimate |
| Escoamento total | Nordeste | 1961-1970 | GLDAS, TerraClimate |
| Escoamento total | Norte | 1961-1970 | GLDAS, TerraClimate |
| Escoamento total | Sudeste | 1961-1970 | GLDAS, TerraClimate |
| Escoamento total | Sudeste | 2011-2020 | GLDAS, TerraClimate |
| Escoamento total | Sudeste | 2021-2025 | GLDAS, TerraClimate |
| Escoamento total | Sul | 2021-2025 | GLDAS, TerraClimate |
| Tmax | Norte | 2001-2010 | ERA5-Land, GLDAS |
| Tmin | Brasil | 1961-1970 | ERA5-Land, GLDAS, TerraClimate |
| Tmin | Nordeste | 1961-1970 | ERA5-Land, GLDAS, TerraClimate |
| Tmin | Norte | 1961-1970 | ERA5-Land, GLDAS, TerraClimate |
| Tmin | Norte | 2001-2010 | ERA5-Land, GLDAS |
| Tmin | Sul | 1961-1970 | ERA5-Land, GLDAS |
| Vento | Nordeste | 1961-1970 | ERA5-Land, GLDAS |
| VPD | Brasil | 2001-2010 | GLDAS, TerraClimate |
| VPD | Centro-Oeste | 2001-2010 | GLDAS, TerraClimate |
| VPD | Nordeste | 1961-1970 | ERA5-Land, GLDAS, TerraClimate |
| VPD | Norte | 2001-2010 | GLDAS, TerraClimate |
| VPD | Sudeste | 2001-2010 | GLDAS, TerraClimate |

##### Chuva

| Década | Região | chirps | era5 | gldas20 | gldas21 | imerg | persiann | terraclimate |
|---|---|---|---|---|---|---|---|---|
| 1961-1970 | Norte | - | ⚠️ +8.3 / 0.31 | +4.9 / 0.70 | - | - | - | +6.0 / 0.70 |
| 1961-1970 | Nordeste | - | ⚠️ +9.8 / 0.89 | -4.5 / 0.99 | - | - | - | -4.2 / 0.99 |
| 1961-1970 | Centro-Oeste | - | ⚠️ -17.8 / 0.35 | -8.3 / 0.89 | - | - | - | -2.6 / 0.89 |
| 1961-1970 | Sudeste | - | -4.5 / 0.77 | -4.6 / 0.92 | - | - | - | -1.5 / 0.92 |
| 1961-1970 | Sul | - | -5.0 / 0.82 | -2.8 / 0.97 | - | - | - | +0.3 / 0.97 |
| 1961-1970 | Brasil | - | ⚠️ +1.1 / 0.46 | +0.2 / 0.82 | - | - | - | +2.4 / 0.83 |
| 1971-1980 | Norte | - | -5.2 / 0.73 | +1.2 / 0.79 | - | - | - | +0.4 / 0.82 |
| 1971-1980 | Nordeste | - | ⚠️ -6.9 / 0.92 | -6.3 / 0.99 | - | - | - | -4.4 / 1.00 |
| 1971-1980 | Centro-Oeste | - | ⚠️ +5.4 / 0.81 | -2.2 / 0.86 | - | - | - | +1.1 / 0.84 |
| 1971-1980 | Sudeste | - | -0.7 / 0.94 | -1.2 / 0.94 | - | - | - | +2.1 / 0.93 |
| 1971-1980 | Sul | - | -5.5 / 0.89 | -2.5 / 0.96 | - | - | - | +2.1 / 0.96 |
| 1971-1980 | Brasil | - | -3.3 / 0.84 | -0.7 / 0.93 | - | - | - | +0.3 / 0.93 |
| 1981-1990 | Norte | -1.0 / 0.96 | -4.9 / 0.88 | +3.5 / 0.81 | - | - | -2.8 / 0.93 | +3.7 / 0.87 |
| 1981-1990 | Nordeste | -0.5 / 1.00 | -1.3 / 0.99 | -3.8 / 1.00 | - | - | -4.6 / 0.99 | -2.2 / 1.00 |
| 1981-1990 | Centro-Oeste | -1.1 / 0.98 | -3.9 / 0.91 | -3.8 / 0.87 | - | - | -3.5 / 0.96 | +0.7 / 0.86 |
| 1981-1990 | Sudeste | +1.4 / 0.98 | -5.2 / 0.97 | +1.3 / 0.95 | - | - | -7.2 / 0.98 | ⚠️ +5.6 / 0.96 |
| 1981-1990 | Sul | +2.2 / 0.99 | -4.9 / 0.96 | +2.8 / 0.94 | - | - | -8.4 / 0.98 | +7.4 / 0.94 |
| 1981-1990 | Brasil | -0.5 / 0.97 | -4.4 / 0.93 | +1.1 / 0.89 | - | - | -3.9 / 0.92 | +2.9 / 0.93 |
| 1991-2000 | Norte | -1.8 / 0.97 | -6.7 / 0.93 | -1.6 / 0.75 | - | - | -4.8 / 0.92 | -0.9 / 0.80 |
| 1991-2000 | Nordeste | -0.9 / 0.99 | -2.6 / 0.96 | -3.3 / 0.94 | - | - | -6.5 / 0.99 | -0.3 / 0.94 |
| 1991-2000 | Centro-Oeste | -0.7 / 0.98 | -4.9 / 0.93 | -8.1 / 0.67 | - | - | -3.9 / 0.94 | -4.5 / 0.69 |
| 1991-2000 | Sudeste | +0.4 / 0.99 | -6.6 / 0.96 | -4.3 / 0.83 | - | - | -8.9 / 0.98 | -0.1 / 0.83 |
| 1991-2000 | Sul | +2.2 / 0.99 | -9.4 / 0.96 | -0.1 / 0.92 | - | - | -8.9 / 0.99 | +4.5 / 0.92 |
| 1991-2000 | Brasil | -1.0 / 0.97 | -6.2 / 0.94 | -3.2 / 0.79 | - | - | -5.5 / 0.91 | -1.1 / 0.82 |
| 2001-2010 | Norte | -3.0 / 0.96 | -4.8 / 0.91 | - | -4.6 / 0.91 | -2.6 / 0.96 | -5.5 / 0.88 | -2.3 / 0.76 |
| 2001-2010 | Nordeste | -2.5 / 0.99 | +2.9 / 0.98 | - | -8.3 / 0.99 | -9.6 / 0.99 | -9.5 / 0.98 | -4.5 / 0.96 |
| 2001-2010 | Centro-Oeste | -2.1 / 0.98 | ⚠️ +5.7 / 0.94 | - | -4.0 / 0.95 | -4.4 / 0.98 | -4.5 / 0.95 | -3.8 / 0.80 |
| 2001-2010 | Sudeste | +0.7 / 0.99 | ⚠️ +2.2 / 0.98 | - | -7.5 / 0.97 | -6.5 / 0.99 | -10.1 / 0.98 | -2.8 / 0.89 |
| 2001-2010 | Sul | +0.2 / 0.98 | -0.3 / 0.96 | - | -8.4 / 0.98 | -7.6 / 0.98 | -10.1 / 0.98 | +3.2 / 0.94 |
| 2001-2010 | Brasil | -2.3 / 0.97 | -1.5 / 0.95 | - | -5.4 / 0.95 | -4.4 / 0.97 | -6.5 / 0.91 | -2.5 / 0.84 |
| 2011-2020 | Norte | -3.6 / 0.89 | - | - | -1.8 / 0.80 | -0.8 / 0.90 | -2.3 / 0.75 | +1.6 / 0.78 |
| 2011-2020 | Nordeste | -5.7 / 0.96 | - | - | ⚠️ -19.2 / 0.84 | -7.4 / 0.98 | -7.0 / 0.71 | -2.9 / 0.93 |
| 2011-2020 | Centro-Oeste | ⚠️ -7.4 / 0.90 | - | - | -7.4 / 0.91 | -2.3 / 0.94 | -2.5 / 0.62 | -2.8 / 0.69 |
| 2011-2020 | Sudeste | -3.2 / 0.95 | - | - | ⚠️ -24.1 / 0.74 | -7.0 / 0.99 | -5.0 / 0.71 | -1.1 / 0.87 |
| 2011-2020 | Sul | -1.1 / 0.95 | - | - | -5.0 / 0.96 | -7.6 / 0.98 | -6.3 / 0.93 | +6.8 / 0.90 |
| 2011-2020 | Brasil | -4.3 / 0.88 | - | - | -7.0 / 0.76 | -2.7 / 0.93 | -3.3 / 0.53 | +0.5 / 0.81 |
| 2021-2025 | Norte | +0.2 / 0.93 | - | - | ⚠️ +12.2 / 0.60 | ⚠️ +13.4 / 0.68 | ⚠️ +13.2 / 0.45 | ⚠️ +11.7 / 0.95 |
| 2021-2025 | Nordeste | +3.9 / 0.98 | - | - | ⚠️ +7.2 / 0.90 | ⚠️ +7.5 / 0.94 | ⚠️ +6.3 / 0.90 | ⚠️ +10.4 / 0.96 |
| 2021-2025 | Centro-Oeste | -5.3 / 0.91 | - | - | ⚠️ +4.6 / 0.84 | ⚠️ +4.4 / 0.83 | ⚠️ +6.8 / 0.61 | ⚠️ +10.8 / 0.93 |
| 2021-2025 | Sudeste | +1.3 / 0.97 | - | - | -5.5 / 0.93 | -4.6 / 0.98 | -4.3 / 0.84 | ⚠️ +5.9 / 0.98 |
| 2021-2025 | Sul | +4.1 / 0.99 | - | - | ⚠️ +1.0 / 0.97 | ⚠️ -0.4 / 0.98 | ⚠️ +0.9 / 0.89 | ⚠️ +16.6 / 0.98 |
| 2021-2025 | Brasil | +0.0 / 0.94 | - | - | ⚠️ +8.0 / 0.63 | ⚠️ +8.7 / 0.75 | ⚠️ +9.0 / 0.46 | ⚠️ +11.2 / 0.94 |

##### Tmax

| Década | Região | era5 | gldas20 | gldas21 | terraclimate |
|---|---|---|---|---|---|
| 1961-1970 | Norte | ⚠️ +1.2 / 0.49 | -1.0 / 0.82 | - | +0.0 / 0.77 |
| 1961-1970 | Nordeste | +0.5 / 0.82 | -0.5 / 0.63 | - | +0.8 / 0.53 |
| 1961-1970 | Centro-Oeste | +1.5 / 0.59 | -0.8 / 0.88 | - | +0.4 / 0.68 |
| 1961-1970 | Sudeste | +1.6 / 0.85 | +0.1 / 0.91 | - | +1.2 / 0.88 |
| 1961-1970 | Sul | +1.5 / 0.89 | -0.1 / 0.96 | - | +0.8 / 0.94 |
| 1961-1970 | Brasil | +1.2 / 0.70 | -0.7 / 0.90 | - | +0.4 / 0.80 |
| 1971-1980 | Norte | +1.7 / 0.69 | -0.8 / 0.70 | - | +0.1 / 0.78 |
| 1971-1980 | Nordeste | +0.6 / 0.80 | -0.7 / 0.43 | - | +0.5 / 0.75 |
| 1971-1980 | Centro-Oeste | +1.4 / 0.81 | -1.0 / 0.74 | - | +0.4 / 0.82 |
| 1971-1980 | Sudeste | +1.5 / 0.90 | -0.5 / 0.74 | - | +0.7 / 0.77 |
| 1971-1980 | Sul | +1.2 / 0.96 | -0.5 / 0.91 | - | +0.5 / 0.89 |
| 1971-1980 | Brasil | +1.4 / 0.74 | -0.8 / 0.66 | - | +0.3 / 0.79 |
| 1981-1990 | Norte | +1.8 / 0.89 | -0.6 / 0.83 | - | +0.2 / 0.89 |
| 1981-1990 | Nordeste | +0.9 / 0.97 | -0.4 / 0.75 | - | +0.7 / 0.94 |
| 1981-1990 | Centro-Oeste | +1.8 / 0.90 | -1.0 / 0.80 | - | +0.6 / 0.87 |
| 1981-1990 | Sudeste | +1.8 / 0.97 | -0.4 / 0.85 | - | +0.9 / 0.83 |
| 1981-1990 | Sul | +1.3 / 0.90 | -0.3 / 0.88 | - | +0.6 / 0.85 |
| 1981-1990 | Brasil | +1.6 / 0.93 | -0.6 / 0.85 | - | +0.5 / 0.91 |
| 1991-2000 | Norte | +2.0 / 0.81 | -0.6 / 0.86 | - | +0.3 / 0.92 |
| 1991-2000 | Nordeste | +1.1 / 0.96 | -0.3 / 0.81 | - | +0.9 / 0.95 |
| 1991-2000 | Centro-Oeste | +1.9 / 0.92 | -1.0 / 0.86 | - | +0.7 / 0.93 |
| 1991-2000 | Sudeste | +2.1 / 0.96 | -0.2 / 0.84 | - | +1.1 / 0.84 |
| 1991-2000 | Sul | +1.5 / 0.96 | -0.3 / 0.88 | - | +0.7 / 0.88 |
| 1991-2000 | Brasil | +1.8 / 0.90 | -0.5 / 0.89 | - | +0.6 / 0.94 |
| 2001-2010 | Norte | ⚠️ +2.5 / 0.89 | - | ⚠️ +2.0 / 0.58 | +0.6 / 0.87 |
| 2001-2010 | Nordeste | +1.2 / 0.94 | - | +0.9 / 0.82 | +1.1 / 0.93 |
| 2001-2010 | Centro-Oeste | +1.8 / 0.94 | - | ⚠️ +2.2 / 0.71 | +0.8 / 0.85 |
| 2001-2010 | Sudeste | +2.0 / 0.98 | - | ⚠️ +2.7 / 0.91 | +1.1 / 0.94 |
| 2001-2010 | Sul | +1.5 / 0.96 | - | +1.3 / 0.94 | +0.6 / 0.91 |
| 2001-2010 | Brasil | +2.0 / 0.93 | - | ⚠️ +1.8 / 0.73 | +0.8 / 0.89 |
| 2011-2020 | Norte | - | - | +0.3 / 0.78 | +0.5 / 0.87 |
| 2011-2020 | Nordeste | - | - | +1.1 / 0.82 | +1.3 / 0.90 |
| 2011-2020 | Centro-Oeste | - | - | +1.0 / 0.85 | +0.8 / 0.82 |
| 2011-2020 | Sudeste | - | - | +1.9 / 0.93 | +1.0 / 0.84 |
| 2011-2020 | Sul | - | - | +0.9 / 0.93 | +0.6 / 0.90 |
| 2011-2020 | Brasil | - | - | +0.8 / 0.89 | +0.8 / 0.88 |
| 2021-2025 | Norte | - | - | +0.5 / 0.94 | +0.6 / 0.96 |
| 2021-2025 | Nordeste | - | - | +0.4 / 0.96 | ⚠️ +1.5 / 0.90 |
| 2021-2025 | Centro-Oeste | - | - | +0.6 / 0.90 | +1.1 / 0.91 |
| 2021-2025 | Sudeste | - | - | ⚠️ +1.3 / 0.94 | +1.5 / 0.96 |
| 2021-2025 | Sul | - | - | +0.9 / 0.96 | +0.8 / 0.92 |
| 2021-2025 | Brasil | - | - | +0.6 / 0.96 | +1.0 / 0.96 |

##### Tmin

| Década | Região | era5 | gldas20 | gldas21 | terraclimate |
|---|---|---|---|---|---|
| 1961-1970 | Norte | ⚠️ -1.5 / 0.41 | ⚠️ -1.3 / 0.45 | - | ⚠️ +0.1 / 0.61 |
| 1961-1970 | Nordeste | ⚠️ -1.7 / 0.51 | ⚠️ -1.4 / 0.43 | - | ⚠️ +0.4 / 0.11 |
| 1961-1970 | Centro-Oeste | -1.9 / 0.63 | -1.3 / 0.62 | - | ⚠️ +0.4 / 0.38 |
| 1961-1970 | Sudeste | -1.5 / 0.82 | -0.9 / 0.80 | - | ⚠️ +0.9 / 0.83 |
| 1961-1970 | Sul | ⚠️ -1.3 / 0.96 | ⚠️ -1.1 / 0.96 | - | +0.6 / 0.95 |
| 1961-1970 | Brasil | ⚠️ -1.6 / 0.64 | ⚠️ -1.3 / 0.69 | - | ⚠️ +0.3 / 0.60 |
| 1971-1980 | Norte | -0.8 / 0.75 | -0.4 / 0.58 | - | +0.8 / 0.60 |
| 1971-1980 | Nordeste | -0.9 / 0.67 | -0.4 / 0.45 | - | +1.3 / 0.44 |
| 1971-1980 | Centro-Oeste | -1.4 / 0.81 | -0.8 / 0.75 | - | +1.2 / 0.72 |
| 1971-1980 | Sudeste | -1.1 / 0.88 | -0.6 / 0.75 | - | +1.5 / 0.74 |
| 1971-1980 | Sul | -0.7 / 0.98 | -0.5 / 0.97 | - | +1.2 / 0.97 |
| 1971-1980 | Brasil | -1.0 / 0.84 | -0.5 / 0.78 | - | +1.1 / 0.76 |
| 1981-1990 | Norte | -0.9 / 0.82 | -0.4 / 0.70 | - | +0.7 / 0.71 |
| 1981-1990 | Nordeste | -1.0 / 0.85 | -0.6 / 0.49 | - | +1.0 / 0.67 |
| 1981-1990 | Centro-Oeste | -1.4 / 0.86 | -0.8 / 0.73 | - | +1.2 / 0.72 |
| 1981-1990 | Sudeste | -1.1 / 0.96 | -0.8 / 0.73 | - | +1.3 / 0.72 |
| 1981-1990 | Sul | -0.4 / 0.89 | -0.3 / 0.88 | - | +1.3 / 0.88 |
| 1981-1990 | Brasil | -1.0 / 0.90 | -0.6 / 0.79 | - | +0.9 / 0.81 |
| 1991-2000 | Norte | -0.8 / 0.76 | -0.5 / 0.66 | - | +0.7 / 0.64 |
| 1991-2000 | Nordeste | -1.0 / 0.86 | -0.7 / 0.69 | - | +0.9 / 0.70 |
| 1991-2000 | Centro-Oeste | -1.4 / 0.84 | -1.0 / 0.67 | - | +1.1 / 0.74 |
| 1991-2000 | Sudeste | -0.9 / 0.94 | -0.7 / 0.77 | - | +1.4 / 0.75 |
| 1991-2000 | Sul | -0.4 / 0.98 | -0.5 / 0.94 | - | +1.1 / 0.93 |
| 1991-2000 | Brasil | -0.9 / 0.88 | -0.6 / 0.80 | - | +0.9 / 0.82 |
| 2001-2010 | Norte | ⚠️ -0.2 / 0.90 | - | ⚠️ +0.2 / 0.38 | +1.1 / 0.76 |
| 2001-2010 | Nordeste | -0.8 / 0.79 | - | +0.0 / 0.59 | +1.1 / 0.53 |
| 2001-2010 | Centro-Oeste | -1.3 / 0.91 | - | -0.5 / 0.80 | +1.2 / 0.65 |
| 2001-2010 | Sudeste | -0.7 / 0.92 | - | +0.2 / 0.89 | +1.5 / 0.62 |
| 2001-2010 | Sul | -0.5 / 0.98 | - | ⚠️ -0.2 / 0.95 | +0.9 / 0.97 |
| 2001-2010 | Brasil | -0.6 / 0.93 | - | +0.0 / 0.71 | +1.2 / 0.77 |
| 2011-2020 | Norte | - | - | +0.6 / 0.76 | +0.8 / 0.72 |
| 2011-2020 | Nordeste | - | - | +0.3 / 0.69 | +1.0 / 0.66 |
| 2011-2020 | Centro-Oeste | - | - | -0.2 / 0.80 | +1.2 / 0.63 |
| 2011-2020 | Sudeste | - | - | +0.1 / 0.85 | +1.3 / 0.71 |
| 2011-2020 | Sul | - | - | +0.3 / 0.96 | +0.9 / 0.93 |
| 2011-2020 | Brasil | - | - | +0.3 / 0.81 | +1.0 / 0.79 |
| 2021-2025 | Norte | - | - | +0.8 / 0.89 | +0.9 / 0.85 |
| 2021-2025 | Nordeste | - | - | +0.4 / 0.92 | +1.2 / 0.74 |
| 2021-2025 | Centro-Oeste | - | - | -0.1 / 0.94 | +1.2 / 0.83 |
| 2021-2025 | Sudeste | - | - | +0.1 / 0.97 | +1.5 / 0.85 |
| 2021-2025 | Sul | - | - | +0.5 / 0.99 | +1.1 / 0.94 |
| 2021-2025 | Brasil | - | - | +0.5 / 0.97 | +1.1 / 0.91 |

##### Umidade relativa

| Década | Região | era5 | gldas20 | gldas21 |
|---|---|---|---|---|
| 1961-1970 | Norte | ⚠️ +3.4 / 0.66 | -4.1 / 0.34 | - |
| 1961-1970 | Nordeste | ⚠️ +8.1 / 0.68 | ⚠️ -3.8 / 0.44 | - |
| 1961-1970 | Centro-Oeste | ⚠️ +4.9 / 0.49 | -1.2 / 0.47 | - |
| 1961-1970 | Sudeste | +2.6 / 0.78 | -7.5 / 0.58 | - |
| 1961-1970 | Sul | -0.3 / 0.71 | -9.3 / 0.46 | - |
| 1961-1970 | Brasil | ⚠️ +4.2 / 0.68 | -4.3 / 0.54 | - |
| 1971-1980 | Norte | -0.6 / 0.82 | -5.8 / 0.51 | - |
| 1971-1980 | Nordeste | +2.8 / 0.80 | -7.9 / 0.31 | - |
| 1971-1980 | Centro-Oeste | +2.3 / 0.82 | -3.4 / 0.47 | - |
| 1971-1980 | Sudeste | +2.3 / 0.94 | -8.1 / 0.49 | - |
| 1971-1980 | Sul | -1.5 / 0.94 | -11.0 / 0.70 | - |
| 1971-1980 | Brasil | +0.8 / 0.79 | -6.3 / 0.40 | - |
| 1981-1990 | Norte | ⚠️ -1.6 / 0.02 | -6.3 / -0.08 | - |
| 1981-1990 | Nordeste | +2.9 / 0.94 | -9.5 / 0.73 | - |
| 1981-1990 | Centro-Oeste | +1.3 / 0.89 | -2.8 / 0.78 | - |
| 1981-1990 | Sudeste | +0.9 / 0.93 | -9.3 / 0.74 | - |
| 1981-1990 | Sul | -0.9 / 0.86 | -10.4 / 0.60 | - |
| 1981-1990 | Brasil | +0.1 / 0.57 | -6.8 / 0.49 | - |
| 1991-2000 | Norte | -0.1 / 0.80 | -5.4 / 0.56 | - |
| 1991-2000 | Nordeste | +3.0 / 0.95 | -9.5 / 0.39 | - |
| 1991-2000 | Centro-Oeste | +2.6 / 0.91 | -1.5 / 0.69 | - |
| 1991-2000 | Sudeste | +0.5 / 0.96 | -9.0 / 0.74 | - |
| 1991-2000 | Sul | -2.3 / 0.94 | -11.5 / 0.82 | - |
| 1991-2000 | Brasil | +0.9 / 0.88 | -6.2 / 0.72 | - |
| 2001-2010 | Norte | -1.7 / 0.82 | - | ⚠️ -1.4 / 0.65 |
| 2001-2010 | Nordeste | +3.7 / 0.94 | - | -0.6 / 0.72 |
| 2001-2010 | Centro-Oeste | +2.6 / 0.87 | - | ⚠️ -4.2 / 0.76 |
| 2001-2010 | Sudeste | +0.5 / 0.96 | - | ⚠️ -10.7 / 0.82 |
| 2001-2010 | Sul | -0.6 / 0.94 | - | -4.8 / 0.78 |
| 2001-2010 | Brasil | +0.4 / 0.90 | - | -3.1 / 0.71 |
| 2011-2020 | Norte | - | - | +2.2 / 0.79 |
| 2011-2020 | Nordeste | - | - | -2.6 / 0.74 |
| 2011-2020 | Centro-Oeste | - | - | +0.5 / 0.74 |
| 2011-2020 | Sudeste | - | - | -7.6 / 0.73 |
| 2011-2020 | Sul | - | - | -3.6 / 0.74 |
| 2011-2020 | Brasil | - | - | -0.5 / 0.71 |
| 2021-2025 | Norte | - | - | +3.9 / 0.93 |
| 2021-2025 | Nordeste | - | - | ⚠️ +4.6 / 0.90 |
| 2021-2025 | Centro-Oeste | - | - | ⚠️ +6.1 / 0.81 |
| 2021-2025 | Sudeste | - | - | ⚠️ +1.0 / 0.88 |
| 2021-2025 | Sul | - | - | ⚠️ +0.3 / 0.88 |
| 2021-2025 | Brasil | - | - | ⚠️ +3.9 / 0.91 |

##### VPD

| Década | Região | era5 | gldas20 | gldas21 | terraclimate |
|---|---|---|---|---|---|
| 1961-1970 | Norte | ⚠️ -0.3 / 0.69 | +0.1 / 0.46 | - | -0.1 / 0.55 |
| 1961-1970 | Nordeste | ⚠️ -0.5 / 0.64 | ⚠️ +0.1 / 0.46 | - | ⚠️ -0.1 / 0.21 |
| 1961-1970 | Centro-Oeste | ⚠️ -0.3 / 0.57 | +0.0 / 0.64 | - | -0.1 / 0.23 |
| 1961-1970 | Sudeste | -0.2 / 0.79 | +0.2 / 0.70 | - | +0.0 / 0.68 |
| 1961-1970 | Sul | -0.1 / 0.69 | +0.2 / 0.58 | - | -0.1 / 0.71 |
| 1961-1970 | Brasil | ⚠️ -0.3 / 0.71 | +0.1 / 0.63 | - | -0.1 / 0.49 |
| 1971-1980 | Norte | -0.1 / 0.83 | +0.2 / 0.65 | - | -0.2 / 0.56 |
| 1971-1980 | Nordeste | -0.2 / 0.80 | +0.3 / 0.36 | - | -0.1 / 0.47 |
| 1971-1980 | Centro-Oeste | -0.2 / 0.82 | +0.1 / 0.61 | - | -0.1 / 0.65 |
| 1971-1980 | Sudeste | -0.2 / 0.94 | +0.2 / 0.59 | - | -0.1 / 0.69 |
| 1971-1980 | Sul | -0.0 / 0.94 | +0.3 / 0.76 | - | -0.1 / 0.72 |
| 1971-1980 | Brasil | -0.2 / 0.80 | +0.2 / 0.56 | - | -0.1 / 0.63 |
| 1981-1990 | Norte | ⚠️ -0.1 / 0.11 | +0.2 / -0.06 | - | -0.1 / 0.24 |
| 1981-1990 | Nordeste | -0.2 / 0.94 | +0.3 / 0.74 | - | -0.0 / 0.77 |
| 1981-1990 | Centro-Oeste | -0.2 / 0.87 | +0.1 / 0.80 | - | -0.1 / 0.55 |
| 1981-1990 | Sudeste | -0.1 / 0.94 | +0.3 / 0.77 | - | -0.0 / 0.59 |
| 1981-1990 | Sul | -0.1 / 0.85 | +0.3 / 0.66 | - | -0.1 / 0.66 |
| 1981-1990 | Brasil | -0.1 / 0.62 | +0.2 / 0.49 | - | -0.1 / 0.52 |
| 1991-2000 | Norte | -0.1 / 0.83 | +0.2 / 0.68 | - | -0.2 / 0.73 |
| 1991-2000 | Nordeste | -0.2 / 0.95 | +0.3 / 0.51 | - | +0.0 / 0.68 |
| 1991-2000 | Centro-Oeste | -0.2 / 0.91 | +0.0 / 0.76 | - | -0.1 / 0.66 |
| 1991-2000 | Sudeste | -0.1 / 0.95 | +0.3 / 0.81 | - | +0.0 / 0.56 |
| 1991-2000 | Sul | -0.0 / 0.95 | +0.3 / 0.86 | - | -0.0 / 0.67 |
| 1991-2000 | Brasil | -0.2 / 0.89 | +0.2 / 0.76 | - | -0.1 / 0.75 |
| 2001-2010 | Norte | -0.1 / 0.83 | - | ⚠️ +0.0 / 0.71 | ⚠️ -0.0 / 0.35 |
| 2001-2010 | Nordeste | -0.2 / 0.92 | - | -0.0 / 0.73 | +0.1 / 0.60 |
| 2001-2010 | Centro-Oeste | -0.2 / 0.88 | - | ⚠️ +0.1 / 0.80 | ⚠️ +0.0 / 0.34 |
| 2001-2010 | Sudeste | -0.1 / 0.97 | - | ⚠️ +0.3 / 0.86 | ⚠️ +0.1 / 0.62 |
| 2001-2010 | Sul | -0.1 / 0.94 | - | +0.1 / 0.79 | -0.0 / 0.65 |
| 2001-2010 | Brasil | -0.1 / 0.89 | - | ⚠️ +0.1 / 0.77 | ⚠️ +0.0 / 0.26 |
| 2011-2020 | Norte | - | - | -0.2 / 0.82 | ⚠️ -0.0 / 0.62 |
| 2011-2020 | Nordeste | - | - | ⚠️ +0.1 / 0.76 | +0.1 / 0.71 |
| 2011-2020 | Centro-Oeste | - | - | -0.1 / 0.78 | ⚠️ +0.0 / 0.71 |
| 2011-2020 | Sudeste | - | - | +0.2 / 0.80 | +0.1 / 0.59 |
| 2011-2020 | Sul | - | - | +0.1 / 0.77 | -0.0 / 0.74 |
| 2011-2020 | Brasil | - | - | -0.0 / 0.79 | ⚠️ +0.0 / 0.63 |
| 2021-2025 | Norte | - | - | -0.2 / 0.96 | -0.1 / 0.98 |
| 2021-2025 | Nordeste | - | - | ⚠️ -0.2 / 0.93 | +0.0 / 0.94 |
| 2021-2025 | Centro-Oeste | - | - | ⚠️ -0.3 / 0.86 | -0.0 / 0.90 |
| 2021-2025 | Sudeste | - | - | ⚠️ -0.0 / 0.92 | +0.0 / 0.98 |
| 2021-2025 | Sul | - | - | ⚠️ -0.0 / 0.91 | -0.1 / 0.98 |
| 2021-2025 | Brasil | - | - | ⚠️ -0.2 / 0.95 | -0.1 / 0.97 |

##### Radiação

| Década | Região | era5 | gldas20 | gldas21 | terraclimate |
|---|---|---|---|---|---|
| 1961-1970 | Norte | -0.0 / 0.47 | +0.0 / 0.17 | - | ⚠️ +2.6 / 0.01 |
| 1961-1970 | Nordeste | -0.5 / 0.86 | +0.0 / 0.57 | - | ⚠️ +2.5 / 0.54 |
| 1961-1970 | Centro-Oeste | ⚠️ -0.1 / 0.42 | -0.3 / 0.33 | - | ⚠️ +3.0 / 0.28 |
| 1961-1970 | Sudeste | -0.6 / 0.70 | -0.5 / 0.50 | - | ⚠️ +2.6 / 0.52 |
| 1961-1970 | Sul | -0.2 / 0.79 | +0.2 / 0.79 | - | +1.3 / 0.58 |
| 1961-1970 | Brasil | -0.2 / 0.54 | -0.1 / 0.36 | - | ⚠️ +2.6 / 0.32 |
| 1971-1980 | Norte | -0.1 / 0.57 | +0.0 / 0.38 | - | +1.8 / 0.00 |
| 1971-1980 | Nordeste | -0.1 / 0.79 | +0.2 / 0.62 | - | ⚠️ +2.1 / 0.33 |
| 1971-1980 | Centro-Oeste | -1.0 / 0.75 | -0.1 / 0.40 | - | +2.2 / 0.28 |
| 1971-1980 | Sudeste | -0.6 / 0.90 | -0.5 / 0.58 | - | ⚠️ +2.4 / 0.37 |
| 1971-1980 | Sul | -0.1 / 0.89 | +0.2 / 0.78 | - | ⚠️ +1.5 / 0.40 |
| 1971-1980 | Brasil | -0.3 / 0.72 | -0.0 / 0.52 | - | +2.0 / 0.09 |
| 1981-1990 | Norte | ⚠️ -0.7 / 0.69 | -0.3 / 0.40 | - | +1.3 / 0.55 |
| 1981-1990 | Nordeste | -0.3 / 0.94 | +0.2 / 0.88 | - | +1.8 / 0.89 |
| 1981-1990 | Centro-Oeste | -1.1 / 0.68 | -0.0 / 0.59 | - | +1.8 / 0.60 |
| 1981-1990 | Sudeste | -0.7 / 0.93 | -0.3 / 0.89 | - | +1.8 / 0.91 |
| 1981-1990 | Sul | -0.6 / 0.81 | -0.0 / 0.77 | - | +0.8 / 0.74 |
| 1981-1990 | Brasil | -0.7 / 0.78 | -0.2 / 0.61 | - | +1.5 / 0.67 |
| 1991-2000 | Norte | ⚠️ -0.7 / 0.59 | ⚠️ -0.8 / 0.58 | - | +1.6 / 0.47 |
| 1991-2000 | Nordeste | -0.2 / 0.90 | +0.1 / 0.86 | - | +1.8 / 0.81 |
| 1991-2000 | Centro-Oeste | -0.8 / 0.82 | -0.4 / 0.80 | - | +2.0 / 0.72 |
| 1991-2000 | Sudeste | -0.7 / 0.93 | -0.5 / 0.89 | - | +1.7 / 0.86 |
| 1991-2000 | Sul | -0.3 / 0.91 | -0.3 / 0.88 | - | +1.3 / 0.83 |
| 1991-2000 | Brasil | -0.6 / 0.76 | -0.5 / 0.71 | - | +1.7 / 0.68 |
| 2001-2010 | Norte | +0.1 / 0.84 | - | ⚠️ -0.7 / 0.50 | ⚠️ +2.6 / 0.60 |
| 2001-2010 | Nordeste | +0.1 / 0.93 | - | ⚠️ -0.3 / 0.76 | +1.4 / 0.86 |
| 2001-2010 | Centro-Oeste | -0.9 / 0.85 | - | -1.1 / 0.77 | +1.8 / 0.59 |
| 2001-2010 | Sudeste | -0.8 / 0.96 | - | -0.9 / 0.91 | +1.8 / 0.91 |
| 2001-2010 | Sul | -0.5 / 0.92 | - | -0.6 / 0.91 | +1.2 / 0.76 |
| 2001-2010 | Brasil | -0.3 / 0.86 | - | ⚠️ -0.7 / 0.56 | +2.0 / 0.71 |
| 2011-2020 | Norte | - | - | -1.6 / 0.64 | +2.1 / 0.56 |
| 2011-2020 | Nordeste | - | - | -1.3 / 0.88 | +1.8 / 0.94 |
| 2011-2020 | Centro-Oeste | - | - | -1.3 / 0.75 | +2.1 / 0.83 |
| 2011-2020 | Sudeste | - | - | -1.0 / 0.90 | +1.9 / 0.94 |
| 2011-2020 | Sul | - | - | -0.5 / 0.93 | +1.0 / 0.92 |
| 2011-2020 | Brasil | - | - | -1.4 / 0.70 | +2.0 / 0.79 |
| 2021-2025 | Norte | - | - | -2.0 / 0.18 | ⚠️ +1.1 / 0.42 |
| 2021-2025 | Nordeste | - | - | ⚠️ -2.1 / 0.63 | ⚠️ +1.0 / 0.80 |
| 2021-2025 | Centro-Oeste | - | - | ⚠️ -1.8 / 0.07 | +1.5 / 0.73 |
| 2021-2025 | Sudeste | - | - | ⚠️ -1.6 / 0.42 | +1.7 / 0.83 |
| 2021-2025 | Sul | - | - | ⚠️ -1.1 / 0.49 | +0.9 / 0.77 |
| 2021-2025 | Brasil | - | - | ⚠️ -1.9 / 0.19 | ⚠️ +1.2 / 0.58 |

##### Vento

| Década | Região | era5 | gldas20 | gldas21 | terraclimate |
|---|---|---|---|---|---|
| 1961-1970 | Norte | +0.2 / 0.02 | +0.3 / 0.25 | - | +0.1 / 0.35 |
| 1961-1970 | Nordeste | ⚠️ -0.3 / 0.64 | ⚠️ -0.5 / 0.63 | - | +0.5 / 0.68 |
| 1961-1970 | Centro-Oeste | +0.0 / 0.10 | +0.0 / 0.48 | - | -0.1 / 0.83 |
| 1961-1970 | Sudeste | +0.1 / 0.55 | -0.4 / 0.56 | - | -0.1 / 0.31 |
| 1961-1970 | Sul | -0.1 / 0.63 | -0.7 / 0.59 | - | ⚠️ -0.4 / 0.73 |
| 1961-1970 | Brasil | +0.0 / 0.19 | -0.1 / 0.56 | - | +0.1 / 0.75 |
| 1971-1980 | Norte | +0.3 / 0.01 | +0.3 / 0.39 | - | +0.1 / 0.39 |
| 1971-1980 | Nordeste | +0.1 / 0.33 | -0.2 / 0.19 | - | ⚠️ +0.8 / 0.05 |
| 1971-1980 | Centro-Oeste | +0.1 / 0.44 | +0.0 / 0.37 | - | -0.2 / 0.26 |
| 1971-1980 | Sudeste | +0.2 / 0.78 | -0.2 / 0.80 | - | +0.0 / 0.37 |
| 1971-1980 | Sul | +0.1 / 0.73 | -0.3 / 0.67 | - | ⚠️ -0.2 / 0.23 |
| 1971-1980 | Brasil | +0.2 / 0.45 | +0.1 / 0.29 | - | ⚠️ +0.1 / -0.12 |
| 1981-1990 | Norte | +0.2 / 0.22 | +0.3 / 0.03 | - | +0.1 / 0.19 |
| 1981-1990 | Nordeste | +0.0 / 0.61 | -0.2 / 0.68 | - | +0.6 / 0.60 |
| 1981-1990 | Centro-Oeste | +0.1 / 0.40 | -0.0 / 0.35 | - | -0.2 / 0.43 |
| 1981-1990 | Sudeste | +0.1 / 0.75 | -0.4 / 0.66 | - | +0.1 / 0.81 |
| 1981-1990 | Sul | -0.0 / 0.57 | -0.5 / 0.51 | - | -0.3 / 0.52 |
| 1981-1990 | Brasil | +0.1 / 0.49 | -0.0 / 0.51 | - | +0.1 / 0.56 |
| 1991-2000 | Norte | +0.2 / 0.42 | +0.3 / 0.28 | - | +0.1 / 0.39 |
| 1991-2000 | Nordeste | -0.0 / 0.76 | -0.3 / 0.68 | - | +0.6 / 0.72 |
| 1991-2000 | Centro-Oeste | +0.0 / 0.64 | -0.1 / 0.56 | - | -0.3 / 0.65 |
| 1991-2000 | Sudeste | -0.0 / 0.74 | ⚠️ -0.6 / 0.64 | - | -0.0 / 0.66 |
| 1991-2000 | Sul | -0.1 / 0.80 | -0.5 / 0.76 | - | -0.3 / 0.79 |
| 1991-2000 | Brasil | +0.1 / 0.59 | -0.0 / 0.36 | - | +0.1 / 0.56 |
| 2001-2010 | Norte | +0.2 / 0.48 | - | -0.0 / 0.48 | -0.1 / 0.40 |
| 2001-2010 | Nordeste | +0.0 / 0.83 | - | -0.5 / 0.84 | +0.5 / 0.82 |
| 2001-2010 | Centro-Oeste | +0.2 / 0.73 | - | ⚠️ -0.0 / 0.76 | -0.1 / 0.61 |
| 2001-2010 | Sudeste | -0.0 / 0.76 | - | -0.4 / 0.10 | -0.0 / 0.66 |
| 2001-2010 | Sul | -0.0 / 0.87 | - | -0.5 / 0.10 | -0.1 / 0.50 |
| 2001-2010 | Brasil | +0.1 / 0.77 | - | -0.2 / 0.73 | +0.0 / 0.78 |
| 2011-2020 | Norte | - | - | -0.1 / 0.58 | ⚠️ -0.2 / 0.62 |
| 2011-2020 | Nordeste | - | - | -0.8 / 0.82 | ⚠️ +0.3 / 0.81 |
| 2011-2020 | Centro-Oeste | - | - | -0.3 / 0.78 | -0.3 / 0.71 |
| 2011-2020 | Sudeste | - | - | -0.4 / 0.68 | -0.0 / 0.81 |
| 2011-2020 | Sul | - | - | -0.4 / 0.46 | -0.1 / 0.72 |
| 2011-2020 | Brasil | - | - | -0.3 / 0.79 | -0.1 / 0.81 |
| 2021-2025 | Norte | - | - | -0.1 / 0.47 | ⚠️ -0.2 / 0.33 |
| 2021-2025 | Nordeste | - | - | -0.6 / 0.93 | ⚠️ +0.2 / 0.82 |
| 2021-2025 | Centro-Oeste | - | - | -0.3 / 0.79 | -0.3 / 0.78 |
| 2021-2025 | Sudeste | - | - | -0.4 / 0.88 | -0.1 / 0.75 |
| 2021-2025 | Sul | - | - | -0.2 / 0.62 | -0.1 / 0.73 |
| 2021-2025 | Brasil | - | - | -0.3 / 0.82 | -0.1 / 0.70 |

##### ETo

| Década | Região | gldas20 | gldas21 | mod16 | terraclimate |
|---|---|---|---|---|---|
| 1961-1970 | Norte | -29.7 / 0.48 | - | - | +12.5 / 0.30 |
| 1961-1970 | Nordeste | ⚠️ -42.8 / 0.54 | - | - | +16.3 / 0.63 |
| 1961-1970 | Centro-Oeste | -39.3 / 0.51 | - | - | ⚠️ +10.6 / 0.47 |
| 1961-1970 | Sudeste | -36.1 / 0.60 | - | - | +13.4 / 0.60 |
| 1961-1970 | Sul | -31.4 / 0.66 | - | - | +0.9 / 0.72 |
| 1961-1970 | Brasil | -35.5 / 0.60 | - | - | +12.2 / 0.64 |
| 1971-1980 | Norte | -25.4 / 0.55 | - | - | +7.7 / 0.34 |
| 1971-1980 | Nordeste | -36.4 / 0.28 | - | - | ⚠️ +19.6 / 0.33 |
| 1971-1980 | Centro-Oeste | -35.7 / 0.43 | - | - | +5.9 / 0.56 |
| 1971-1980 | Sudeste | -33.6 / 0.63 | - | - | +11.4 / 0.54 |
| 1971-1980 | Sul | -27.6 / 0.83 | - | - | +2.6 / 0.69 |
| 1971-1980 | Brasil | -31.1 / 0.49 | - | - | ⚠️ +9.7 / 0.47 |
| 1981-1990 | Norte | -27.0 / 0.40 | - | - | +6.2 / 0.64 |
| 1981-1990 | Nordeste | -36.1 / 0.83 | - | - | +16.4 / 0.87 |
| 1981-1990 | Centro-Oeste | -35.4 / 0.50 | - | - | +5.0 / 0.70 |
| 1981-1990 | Sudeste | -32.0 / 0.81 | - | - | +10.4 / 0.93 |
| 1981-1990 | Sul | -29.5 / 0.72 | - | - | +0.3 / 0.79 |
| 1981-1990 | Brasil | -31.6 / 0.61 | - | - | +8.1 / 0.80 |
| 1991-2000 | Norte | -28.5 / 0.59 | - | - | +7.3 / 0.67 |
| 1991-2000 | Nordeste | -36.0 / 0.72 | - | - | +17.1 / 0.82 |
| 1991-2000 | Centro-Oeste | -37.0 / 0.60 | - | - | +5.0 / 0.79 |
| 1991-2000 | Sudeste | -34.8 / 0.82 | - | - | +9.5 / 0.90 |
| 1991-2000 | Sul | -28.5 / 0.83 | - | - | +2.8 / 0.88 |
| 1991-2000 | Brasil | -32.7 / 0.72 | - | - | +8.8 / 0.81 |
| 2001-2010 | Norte | - | ⚠️ -40.4 / 0.54 | -31.5 / 0.35 | ⚠️ +14.0 / 0.72 |
| 2001-2010 | Nordeste | - | -50.4 / 0.86 | -30.6 / 0.50 | +15.3 / 0.90 |
| 2001-2010 | Centro-Oeste | - | ⚠️ -42.1 / 0.81 | -35.6 / 0.36 | +8.5 / 0.74 |
| 2001-2010 | Sudeste | - | -39.5 / 0.90 | -35.1 / 0.45 | +11.6 / 0.93 |
| 2001-2010 | Sul | - | -43.3 / 0.79 | -34.8 / 0.45 | +3.3 / 0.84 |
| 2001-2010 | Brasil | - | -43.2 / 0.73 | -32.8 / 0.30 | +12.2 / 0.85 |
| 2011-2020 | Norte | - | -47.1 / 0.86 | -28.4 / 0.32 | +10.4 / 0.75 |
| 2011-2020 | Nordeste | - | -51.6 / 0.88 | -29.7 / 0.48 | +15.8 / 0.93 |
| 2011-2020 | Centro-Oeste | - | -47.6 / 0.76 | -30.3 / 0.52 | +8.1 / 0.87 |
| 2011-2020 | Sudeste | - | -42.7 / 0.88 | -31.5 / 0.54 | +12.2 / 0.92 |
| 2011-2020 | Sul | - | -43.7 / 0.88 | -30.8 / 0.50 | +3.4 / 0.91 |
| 2011-2020 | Brasil | - | -47.6 / 0.86 | -29.6 / 0.34 | +10.8 / 0.87 |
| 2021-2025 | Norte | - | -48.0 / 0.64 | -31.0 / 0.51 | +3.3 / 0.79 |
| 2021-2025 | Nordeste | - | -54.2 / 0.88 | -34.2 / 0.34 | ⚠️ +10.4 / 0.89 |
| 2021-2025 | Centro-Oeste | - | -51.2 / 0.76 | -33.5 / 0.75 | +3.6 / 0.88 |
| 2021-2025 | Sudeste | - | ⚠️ -49.6 / 0.81 | -34.9 / 0.68 | +9.5 / 0.90 |
| 2021-2025 | Sul | - | -47.1 / 0.77 | -31.4 / 0.72 | +1.6 / 0.90 |
| 2021-2025 | Brasil | - | -50.2 / 0.69 | -32.7 / 0.50 | +5.3 / 0.88 |

##### ET real

| Década | Região | gldas20 | gldas21 | mod16 | terraclimate |
|---|---|---|---|---|---|
| 1961-1970 | Norte | -10.8 / 0.35 | - | - | +6.8 / 0.37 |
| 1961-1970 | Nordeste | ⚠️ -10.6 / 0.75 | - | - | -4.1 / 0.59 |
| 1961-1970 | Centro-Oeste | ⚠️ -11.6 / 0.40 | - | - | +7.2 / 0.31 |
| 1961-1970 | Sudeste | -2.2 / 0.47 | - | - | +8.7 / 0.50 |
| 1961-1970 | Sul | -6.0 / 0.15 | - | - | -0.5 / -0.20 |
| 1961-1970 | Brasil | ⚠️ -9.8 / 0.63 | - | - | +4.9 / 0.57 |
| 1971-1980 | Norte | -3.9 / 0.39 | - | - | +6.9 / 0.37 |
| 1971-1980 | Nordeste | -2.1 / 0.65 | - | - | +1.6 / 0.64 |
| 1971-1980 | Centro-Oeste | -4.6 / 0.29 | - | - | +6.6 / 0.47 |
| 1971-1980 | Sudeste | +0.5 / 0.42 | - | - | +7.3 / 0.38 |
| 1971-1980 | Sul | -1.8 / 0.42 | - | - | +0.4 / 0.00 |
| 1971-1980 | Brasil | -3.2 / 0.50 | - | - | +5.6 / 0.53 |
| 1981-1990 | Norte | -4.8 / 0.31 | - | - | +7.2 / 0.56 |
| 1981-1990 | Nordeste | +0.3 / 0.83 | - | - | ⚠️ +5.3 / 0.72 |
| 1981-1990 | Centro-Oeste | -1.6 / 0.65 | - | - | +9.3 / 0.67 |
| 1981-1990 | Sudeste | +6.1 / 0.61 | - | - | +12.2 / 0.38 |
| 1981-1990 | Sul | -2.3 / 0.50 | - | - | +2.0 / 0.04 |
| 1981-1990 | Brasil | -2.2 / 0.65 | - | - | +7.5 / 0.65 |
| 1991-2000 | Norte | -7.1 / 0.47 | - | - | +8.1 / 0.52 |
| 1991-2000 | Nordeste | -0.4 / 0.74 | - | - | +3.2 / 0.68 |
| 1991-2000 | Centro-Oeste | -5.5 / 0.50 | - | - | +7.5 / 0.71 |
| 1991-2000 | Sudeste | +2.7 / 0.69 | - | - | +9.9 / 0.54 |
| 1991-2000 | Sul | -1.8 / 0.51 | - | - | +2.2 / 0.00 |
| 1991-2000 | Brasil | -4.6 / 0.54 | - | - | +7.0 / 0.67 |
| 2001-2010 | Norte | - | ⚠️ -14.7 / 0.43 | -16.9 / 0.34 | +12.6 / 0.51 |
| 2001-2010 | Nordeste | - | -6.4 / 0.86 | -18.3 / 0.78 | -3.3 / 0.67 |
| 2001-2010 | Centro-Oeste | - | -9.8 / 0.79 | ⚠️ +13.2 / 0.16 | +6.5 / 0.62 |
| 2001-2010 | Sudeste | - | ⚠️ -2.4 / 0.85 | ⚠️ +3.5 / 0.41 | +8.0 / 0.64 |
| 2001-2010 | Sul | - | -9.4 / 0.70 | ⚠️ +15.3 / 0.20 | +3.3 / 0.15 |
| 2001-2010 | Brasil | - | ⚠️ -11.2 / 0.69 | -8.8 / 0.40 | +7.9 / 0.66 |
| 2011-2020 | Norte | - | -20.8 / 0.42 | -16.1 / 0.06 | +10.9 / 0.64 |
| 2011-2020 | Nordeste | - | -13.5 / 0.75 | -21.7 / 0.77 | -1.2 / 0.82 |
| 2011-2020 | Centro-Oeste | - | -12.8 / 0.72 | -1.2 / 0.47 | +9.5 / 0.72 |
| 2011-2020 | Sudeste | - | -10.9 / 0.59 | -3.9 / 0.40 | +8.4 / 0.43 |
| 2011-2020 | Sul | - | -9.2 / 0.60 | +9.7 / 0.16 | +3.8 / 0.25 |
| 2011-2020 | Brasil | - | -16.7 / 0.62 | -11.6 / 0.24 | +8.2 / 0.71 |
| 2021-2025 | Norte | - | -21.5 / 0.33 | -19.3 / 0.22 | +8.7 / 0.90 |
| 2021-2025 | Nordeste | - | -9.2 / 0.87 | -21.1 / 0.83 | +0.0 / 0.82 |
| 2021-2025 | Centro-Oeste | - | -16.6 / 0.59 | +1.1 / 0.56 | +9.8 / 0.83 |
| 2021-2025 | Sudeste | - | -10.0 / 0.73 | -2.5 / 0.64 | +12.9 / 0.38 |
| 2021-2025 | Sul | - | -9.0 / 0.72 | +10.2 / 0.57 | ⚠️ +9.1 / 0.22 |
| 2021-2025 | Brasil | - | -17.2 / 0.45 | -13.0 / 0.47 | +8.1 / 0.88 |

##### Transpiração

| Década | Região | gldas20 | gldas21 |
|---|---|---|---|
| 1961-1970 | Norte | ⚠️ +31.7 / 0.40 | - |
| 1961-1970 | Nordeste | ⚠️ +13.4 / 0.49 | - |
| 1961-1970 | Centro-Oeste | ⚠️ +27.9 / 0.35 | - |
| 1961-1970 | Sudeste | ⚠️ +58.1 / 0.46 | - |
| 1961-1970 | Sul | ⚠️ +61.6 / 0.75 | - |
| 1961-1970 | Brasil | ⚠️ +32.8 / 0.41 | - |
| 1971-1980 | Norte | ⚠️ +46.8 / 0.61 | - |
| 1971-1980 | Nordeste | +26.5 / 0.47 | - |
| 1971-1980 | Centro-Oeste | +50.4 / 0.54 | - |
| 1971-1980 | Sudeste | +66.4 / 0.66 | - |
| 1971-1980 | Sul | +74.3 / 0.63 | - |
| 1971-1980 | Brasil | +48.5 / 0.57 | - |
| 1981-1990 | Norte | +41.0 / 0.70 | - |
| 1981-1990 | Nordeste | +24.4 / 0.72 | - |
| 1981-1990 | Centro-Oeste | ⚠️ +55.4 / 0.55 | - |
| 1981-1990 | Sudeste | ⚠️ +72.4 / 0.77 | - |
| 1981-1990 | Sul | +72.0 / 0.74 | - |
| 1981-1990 | Brasil | +46.7 / 0.64 | - |
| 1991-2000 | Norte | +35.9 / 0.74 | - |
| 1991-2000 | Nordeste | +20.0 / 0.60 | - |
| 1991-2000 | Centro-Oeste | +47.3 / 0.48 | - |
| 1991-2000 | Sudeste | +68.4 / 0.66 | - |
| 1991-2000 | Sul | +70.5 / 0.82 | - |
| 1991-2000 | Brasil | +41.5 / 0.66 | - |
| 2001-2010 | Norte | - | ⚠️ +6.7 / 0.83 |
| 2001-2010 | Nordeste | - | ⚠️ -5.2 / 0.80 |
| 2001-2010 | Centro-Oeste | - | +8.8 / 0.77 |
| 2001-2010 | Sudeste | - | ⚠️ +17.9 / 0.82 |
| 2001-2010 | Sul | - | +15.7 / 0.75 |
| 2001-2010 | Brasil | - | ⚠️ +7.3 / 0.79 |
| 2011-2020 | Norte | - | -5.7 / 0.51 |
| 2011-2020 | Nordeste | - | -13.6 / 0.66 |
| 2011-2020 | Centro-Oeste | - | +5.5 / 0.55 |
| 2011-2020 | Sudeste | - | +8.7 / 0.68 |
| 2011-2020 | Sul | - | +14.7 / 0.73 |
| 2011-2020 | Brasil | - | -1.6 / 0.42 |
| 2021-2025 | Norte | - | -5.1 / 0.39 |
| 2021-2025 | Nordeste | - | -12.8 / 0.76 |
| 2021-2025 | Centro-Oeste | - | ⚠️ -4.9 / 0.70 |
| 2021-2025 | Sudeste | - | ⚠️ -1.9 / 0.76 |
| 2021-2025 | Sul | - | ⚠️ +7.9 / 0.72 |
| 2021-2025 | Brasil | - | -4.7 / 0.51 |

##### Temperatura do solo

| Década | Região | gldas20 | gldas21 |
|---|---|---|---|
| 1961-1970 | Norte | -0.8 / 0.67 | - |
| 1961-1970 | Nordeste | +0.5 / 0.70 | - |
| 1961-1970 | Centro-Oeste | -0.2 / 0.62 | - |
| 1961-1970 | Sudeste | +0.1 / 0.88 | - |
| 1961-1970 | Sul | -0.0 / 0.92 | - |
| 1961-1970 | Brasil | -0.3 / 0.77 | - |
| 1971-1980 | Norte | -1.0 / 0.79 | - |
| 1971-1980 | Nordeste | +0.4 / 0.75 | - |
| 1971-1980 | Centro-Oeste | -0.2 / 0.80 | - |
| 1971-1980 | Sudeste | -0.3 / 0.85 | - |
| 1971-1980 | Sul | -0.1 / 0.93 | - |
| 1971-1980 | Brasil | -0.4 / 0.88 | - |
| 1981-1990 | Norte | -0.9 / 0.84 | - |
| 1981-1990 | Nordeste | +0.3 / 0.88 | - |
| 1981-1990 | Centro-Oeste | -0.3 / 0.84 | - |
| 1981-1990 | Sudeste | -0.4 / 0.94 | - |
| 1981-1990 | Sul | -0.1 / 0.96 | - |
| 1981-1990 | Brasil | -0.4 / 0.92 | - |
| 1991-2000 | Norte | -0.9 / 0.84 | - |
| 1991-2000 | Nordeste | +0.2 / 0.88 | - |
| 1991-2000 | Centro-Oeste | -0.4 / 0.85 | - |
| 1991-2000 | Sudeste | -0.4 / 0.89 | - |
| 1991-2000 | Sul | -0.3 / 0.93 | - |
| 1991-2000 | Brasil | -0.5 / 0.89 | - |
| 2001-2010 | Norte | - | +0.3 / 0.69 |
| 2001-2010 | Nordeste | - | +1.0 / 0.84 |
| 2001-2010 | Centro-Oeste | - | +1.3 / 0.79 |
| 2001-2010 | Sudeste | - | +1.3 / 0.90 |
| 2001-2010 | Sul | - | +0.8 / 0.97 |
| 2001-2010 | Brasil | - | +0.8 / 0.77 |
| 2011-2020 | Norte | - | +0.4 / 0.69 |
| 2011-2020 | Nordeste | - | +1.4 / 0.84 |
| 2011-2020 | Centro-Oeste | - | +1.3 / 0.78 |
| 2011-2020 | Sudeste | - | +1.5 / 0.86 |
| 2011-2020 | Sul | - | +1.1 / 0.94 |
| 2011-2020 | Brasil | - | +0.9 / 0.79 |
| 2021-2025 | Norte | - | ⚠️ +1.2 / 0.81 |
| 2021-2025 | Nordeste | - | +1.6 / 0.92 |
| 2021-2025 | Centro-Oeste | - | ⚠️ +1.8 / 0.91 |
| 2021-2025 | Sudeste | - | +1.7 / 0.88 |
| 2021-2025 | Sul | - | +1.5 / 0.95 |
| 2021-2025 | Brasil | - | ⚠️ +1.5 / 0.90 |

##### Temperatura da folha

| Década | Região | gldas20 | gldas21 |
|---|---|---|---|
| 1961-1970 | Norte | -1.2 / 0.67 | - |
| 1961-1970 | Nordeste | +0.1 / 0.70 | - |
| 1961-1970 | Centro-Oeste | -0.6 / 0.63 | - |
| 1961-1970 | Sudeste | -0.4 / 0.88 | - |
| 1961-1970 | Sul | -0.5 / 0.92 | - |
| 1961-1970 | Brasil | -0.7 / 0.78 | - |
| 1971-1980 | Norte | -1.3 / 0.79 | - |
| 1971-1980 | Nordeste | -0.0 / 0.74 | - |
| 1971-1980 | Centro-Oeste | -0.6 / 0.80 | - |
| 1971-1980 | Sudeste | -0.7 / 0.86 | - |
| 1971-1980 | Sul | -0.6 / 0.94 | - |
| 1971-1980 | Brasil | -0.8 / 0.88 | - |
| 1981-1990 | Norte | -1.2 / 0.84 | - |
| 1981-1990 | Nordeste | -0.2 / 0.88 | - |
| 1981-1990 | Centro-Oeste | -0.8 / 0.85 | - |
| 1981-1990 | Sudeste | -0.8 / 0.94 | - |
| 1981-1990 | Sul | -0.6 / 0.96 | - |
| 1981-1990 | Brasil | -0.9 / 0.92 | - |
| 1991-2000 | Norte | -1.3 / 0.83 | - |
| 1991-2000 | Nordeste | -0.3 / 0.88 | - |
| 1991-2000 | Centro-Oeste | -0.9 / 0.85 | - |
| 1991-2000 | Sudeste | -0.8 / 0.90 | - |
| 1991-2000 | Sul | -0.8 / 0.94 | - |
| 1991-2000 | Brasil | -0.9 / 0.89 | - |
| 2001-2010 | Norte | - | -0.2 / 0.72 |
| 2001-2010 | Nordeste | - | +0.6 / 0.84 |
| 2001-2010 | Centro-Oeste | - | +0.7 / 0.81 |
| 2001-2010 | Sudeste | - | +0.8 / 0.90 |
| 2001-2010 | Sul | - | +0.2 / 0.97 |
| 2001-2010 | Brasil | - | +0.3 / 0.79 |
| 2011-2020 | Norte | - | -0.1 / 0.70 |
| 2011-2020 | Nordeste | - | +0.9 / 0.84 |
| 2011-2020 | Centro-Oeste | - | +0.7 / 0.78 |
| 2011-2020 | Sudeste | - | +1.0 / 0.87 |
| 2011-2020 | Sul | - | +0.5 / 0.95 |
| 2011-2020 | Brasil | - | +0.4 / 0.78 |
| 2021-2025 | Norte | - | ⚠️ +0.7 / 0.81 |
| 2021-2025 | Nordeste | - | +1.1 / 0.91 |
| 2021-2025 | Centro-Oeste | - | ⚠️ +1.3 / 0.92 |
| 2021-2025 | Sudeste | - | +1.2 / 0.88 |
| 2021-2025 | Sul | - | +0.9 / 0.95 |
| 2021-2025 | Brasil | - | ⚠️ +1.0 / 0.89 |

##### Umidade do solo 0-5 cm

| Década | Região | gldas20 | gldas21 |
|---|---|---|---|
| 1961-1970 | Norte | -0.0 / 0.55 | - |
| 1961-1970 | Nordeste | -0.1 / 0.82 | - |
| 1961-1970 | Centro-Oeste | -0.1 / 0.44 | - |
| 1961-1970 | Sudeste | -0.1 / 0.68 | - |
| 1961-1970 | Sul | -0.0 / 0.70 | - |
| 1961-1970 | Brasil | -0.0 / 0.69 | - |
| 1971-1980 | Norte | -0.0 / 0.68 | - |
| 1971-1980 | Nordeste | -0.1 / 0.78 | - |
| 1971-1980 | Centro-Oeste | -0.1 / 0.62 | - |
| 1971-1980 | Sudeste | -0.1 / 0.74 | - |
| 1971-1980 | Sul | -0.0 / 0.84 | - |
| 1971-1980 | Brasil | -0.0 / 0.66 | - |
| 1981-1990 | Norte | -0.0 / 0.64 | - |
| 1981-1990 | Nordeste | -0.1 / 0.86 | - |
| 1981-1990 | Centro-Oeste | -0.1 / 0.77 | - |
| 1981-1990 | Sudeste | -0.1 / 0.86 | - |
| 1981-1990 | Sul | -0.0 / 0.80 | - |
| 1981-1990 | Brasil | -0.0 / 0.73 | - |
| 1991-2000 | Norte | -0.0 / 0.73 | - |
| 1991-2000 | Nordeste | -0.1 / 0.79 | - |
| 1991-2000 | Centro-Oeste | -0.1 / 0.73 | - |
| 1991-2000 | Sudeste | -0.1 / 0.80 | - |
| 1991-2000 | Sul | -0.0 / 0.83 | - |
| 1991-2000 | Brasil | -0.0 / 0.74 | - |
| 2001-2010 | Norte | - | +0.0 / 0.81 |
| 2001-2010 | Nordeste | - | -0.1 / 0.86 |
| 2001-2010 | Centro-Oeste | - | -0.1 / 0.83 |
| 2001-2010 | Sudeste | - | -0.1 / 0.86 |
| 2001-2010 | Sul | - | -0.0 / 0.87 |
| 2001-2010 | Brasil | - | -0.0 / 0.81 |
| 2011-2020 | Norte | - | +0.0 / 0.68 |
| 2011-2020 | Nordeste | - | -0.1 / 0.86 |
| 2011-2020 | Centro-Oeste | - | -0.1 / 0.79 |
| 2011-2020 | Sudeste | - | -0.1 / 0.79 |
| 2011-2020 | Sul | - | -0.0 / 0.87 |
| 2011-2020 | Brasil | - | -0.0 / 0.81 |
| 2021-2025 | Norte | - | +0.0 / 0.78 |
| 2021-2025 | Nordeste | - | -0.1 / 0.91 |
| 2021-2025 | Centro-Oeste | - | -0.0 / 0.79 |
| 2021-2025 | Sudeste | - | -0.1 / 0.80 |
| 2021-2025 | Sul | - | -0.0 / 0.79 |
| 2021-2025 | Brasil | - | -0.0 / 0.82 |

##### Umidade do solo 0-100 cm

| Década | Região | gldas20 | gldas21 | terraclimate |
|---|---|---|---|---|
| 1961-1970 | Norte | -0.0 / 0.58 | - | ⚠️ -206.3 / 0.47 |
| 1961-1970 | Nordeste | -0.0 / 0.85 | - | -133.0 / 0.82 |
| 1961-1970 | Centro-Oeste | -0.0 / 0.30 | - | -123.7 / 0.32 |
| 1961-1970 | Sudeste | -0.0 / 0.64 | - | -81.3 / 0.45 |
| 1961-1970 | Sul | -0.0 / 0.78 | - | -43.9 / 0.50 |
| 1961-1970 | Brasil | -0.0 / 0.65 | - | -151.4 / 0.57 |
| 1971-1980 | Norte | +0.0 / 0.73 | - | -217.1 / 0.74 |
| 1971-1980 | Nordeste | -0.0 / 0.77 | - | -137.9 / 0.75 |
| 1971-1980 | Centro-Oeste | -0.1 / 0.58 | - | -132.4 / 0.51 |
| 1971-1980 | Sudeste | -0.1 / 0.77 | - | -87.2 / 0.63 |
| 1971-1980 | Sul | -0.0 / 0.88 | - | -46.6 / 0.75 |
| 1971-1980 | Brasil | -0.0 / 0.68 | - | -159.6 / 0.68 |
| 1981-1990 | Norte | +0.0 / 0.71 | - | -211.3 / 0.72 |
| 1981-1990 | Nordeste | -0.0 / 0.92 | - | -124.3 / 0.89 |
| 1981-1990 | Centro-Oeste | -0.0 / 0.72 | - | -130.3 / 0.64 |
| 1981-1990 | Sudeste | -0.0 / 0.86 | - | -79.6 / 0.74 |
| 1981-1990 | Sul | -0.0 / 0.84 | - | -45.2 / 0.71 |
| 1981-1990 | Brasil | -0.0 / 0.71 | - | -153.2 / 0.68 |
| 1991-2000 | Norte | +0.0 / 0.80 | - | -207.3 / 0.79 |
| 1991-2000 | Nordeste | -0.0 / 0.86 | - | -115.1 / 0.87 |
| 1991-2000 | Centro-Oeste | -0.0 / 0.71 | - | -129.4 / 0.61 |
| 1991-2000 | Sudeste | -0.0 / 0.79 | - | -82.3 / 0.66 |
| 1991-2000 | Sul | -0.0 / 0.85 | - | -46.7 / 0.71 |
| 1991-2000 | Brasil | -0.0 / 0.72 | - | -150.0 / 0.76 |
| 2001-2010 | Norte | - | +0.0 / 0.85 | -206.5 / 0.74 |
| 2001-2010 | Nordeste | - | -0.0 / 0.92 | -120.4 / 0.80 |
| 2001-2010 | Centro-Oeste | - | -0.0 / 0.81 | -123.7 / 0.62 |
| 2001-2010 | Sudeste | - | -0.0 / 0.89 | -83.3 / 0.79 |
| 2001-2010 | Sul | - | +0.0 / 0.94 | -46.4 / 0.76 |
| 2001-2010 | Brasil | - | -0.0 / 0.81 | -149.6 / 0.70 |
| 2011-2020 | Norte | - | +0.0 / 0.70 | -203.2 / 0.87 |
| 2011-2020 | Nordeste | - | -0.0 / 0.82 | -108.9 / 0.79 |
| 2011-2020 | Centro-Oeste | - | -0.0 / 0.78 | -120.6 / 0.81 |
| 2011-2020 | Sudeste | - | -0.0 / 0.74 | -72.0 / 0.65 |
| 2011-2020 | Sul | - | +0.0 / 0.91 | -45.3 / 0.72 |
| 2011-2020 | Brasil | - | -0.0 / 0.77 | -144.1 / 0.80 |
| 2021-2025 | Norte | - | +0.0 / 0.85 | -185.0 / 0.98 |
| 2021-2025 | Nordeste | - | -0.0 / 0.94 | -112.8 / 0.88 |
| 2021-2025 | Centro-Oeste | - | -0.0 / 0.84 | -103.8 / 0.90 |
| 2021-2025 | Sudeste | - | -0.0 / 0.80 | -69.1 / 0.85 |
| 2021-2025 | Sul | - | +0.0 / 0.84 | -40.4 / 0.78 |
| 2021-2025 | Brasil | - | +0.0 / 0.88 | -132.9 / 0.98 |

##### Escoamento total

| Década | Região | gldas20 | gldas21 | terraclimate |
|---|---|---|---|---|
| 1961-1970 | Norte | ⚠️ -40.4 / 0.22 | - | ⚠️ -50.5 / 0.32 |
| 1961-1970 | Nordeste | ⚠️ -38.8 / 0.66 | - | ⚠️ -49.7 / 0.73 |
| 1961-1970 | Centro-Oeste | ⚠️ -16.0 / 0.24 | - | ⚠️ -30.7 / 0.13 |
| 1961-1970 | Sudeste | ⚠️ -23.8 / 0.28 | - | ⚠️ -32.5 / 0.41 |
| 1961-1970 | Sul | +2.1 / 0.71 | - | -0.0 / 0.66 |
| 1961-1970 | Brasil | -33.1 / 0.09 | - | -43.8 / 0.18 |
| 1971-1980 | Norte | -35.8 / 0.43 | - | -43.3 / 0.55 |
| 1971-1980 | Nordeste | -24.1 / 0.86 | - | ⚠️ -27.2 / 0.87 |
| 1971-1980 | Centro-Oeste | ⚠️ -55.1 / 0.52 | - | -59.8 / 0.53 |
| 1971-1980 | Sudeste | ⚠️ -30.0 / 0.82 | - | -33.8 / 0.82 |
| 1971-1980 | Sul | ⚠️ -6.3 / 0.78 | - | +2.8 / 0.79 |
| 1971-1980 | Brasil | -35.8 / 0.57 | - | -42.0 / 0.62 |
| 1981-1990 | Norte | -33.9 / 0.54 | - | -41.7 / 0.64 |
| 1981-1990 | Nordeste | -33.2 / 0.86 | - | -37.7 / 0.95 |
| 1981-1990 | Centro-Oeste | -47.2 / 0.65 | - | ⚠️ -49.8 / 0.68 |
| 1981-1990 | Sudeste | -20.8 / 0.86 | - | ⚠️ -19.1 / 0.89 |
| 1981-1990 | Sul | +1.3 / 0.83 | - | ⚠️ +7.1 / 0.84 |
| 1981-1990 | Brasil | -32.9 / 0.63 | - | -38.6 / 0.72 |
| 1991-2000 | Norte | -34.3 / 0.65 | - | -43.3 / 0.68 |
| 1991-2000 | Nordeste | -23.8 / 0.73 | - | ⚠️ -22.8 / 0.84 |
| 1991-2000 | Centro-Oeste | -48.0 / 0.62 | - | -53.7 / 0.68 |
| 1991-2000 | Sudeste | -24.0 / 0.64 | - | ⚠️ -25.6 / 0.68 |
| 1991-2000 | Sul | +2.9 / 0.81 | - | ⚠️ +8.9 / 0.82 |
| 1991-2000 | Brasil | -32.8 / 0.57 | - | -40.0 / 0.65 |
| 2001-2010 | Norte | - | ⚠️ -30.0 / 0.56 | -45.5 / 0.60 |
| 2001-2010 | Nordeste | - | -35.1 / 0.79 | ⚠️ -29.8 / 0.85 |
| 2001-2010 | Centro-Oeste | - | -47.9 / 0.77 | -61.3 / 0.66 |
| 2001-2010 | Sudeste | - | -43.2 / 0.84 | ⚠️ -46.1 / 0.79 |
| 2001-2010 | Sul | - | -19.1 / 0.85 | ⚠️ -9.6 / 0.83 |
| 2001-2010 | Brasil | - | ⚠️ -33.0 / 0.60 | -45.3 / 0.56 |
| 2011-2020 | Norte | - | -15.3 / 0.60 | -40.5 / 0.69 |
| 2011-2020 | Nordeste | - | ⚠️ -56.6 / 0.56 | -37.3 / 0.82 |
| 2011-2020 | Centro-Oeste | - | -46.4 / 0.73 | -60.2 / 0.66 |
| 2011-2020 | Sudeste | - | ⚠️ -63.3 / 0.52 | ⚠️ -44.3 / 0.75 |
| 2011-2020 | Sul | - | -18.0 / 0.86 | ⚠️ -9.7 / 0.85 |
| 2011-2020 | Brasil | - | -27.8 / 0.54 | -42.0 / 0.66 |
| 2021-2025 | Norte | - | ⚠️ +0.4 / 0.13 | -40.1 / 0.84 |
| 2021-2025 | Nordeste | - | ⚠️ -24.2 / 0.55 | -40.1 / 0.89 |
| 2021-2025 | Centro-Oeste | - | ⚠️ -18.4 / 0.70 | -57.9 / 0.81 |
| 2021-2025 | Sudeste | - | ⚠️ -31.1 / 0.65 | ⚠️ -47.9 / 0.90 |
| 2021-2025 | Sul | - | ⚠️ -9.2 / 0.89 | ⚠️ -10.1 / 0.90 |
| 2021-2025 | Brasil | - | ⚠️ -5.9 / 0.20 | -41.0 / 0.79 |

### BR-DWGD: artigos, site e relatório

Arquivo: `pesquisa/resultados_brdwgd/ANALISE_DOS_ARTIGOS.md`

#### O excesso de chuva depois de 2020 vem do BR-DWGD? Leitura dos artigos (26/11/2026)

Pedido do responsável: "analise esses dois documentos do BR-DWGD para verificarmos realmente se é ele que está prevendo
excesso ou não, e compare com os documentos oficiais das outras bases de dados".

##### 1. O que os dois artigos do BR-DWGD dizem

| | Xavier et al. 2016 (IJC 36: 2644–2659, doi 10.1002/joc.4518) | Xavier et al. 2022 (IJC, doi 10.1002/joc.7731) |
|---|---|---|
| Período | 1/1/1980 a 31/12/2013 | **1/1/1961 a 31/7/2020** |
| Resolução | 0,25° | 0,1° |
| Rede | 3.625 pluviômetros, 735 estações | 11.473 pluviômetros, 1.252 estações (642 convencionais, 610 automáticas), ANA e INMET por API |
| Chuva | IDW (5 vizinhos) | ADW (5 vizinhos) |
| Validação cruzada da chuva | R 0,61; Amazônia R 0,36 | R 0,653; viés 0,004 mm/dia; RMSE 8,2 mm; Amazônia R 0,38 |
| O fim do período | "atribuímos a queda de **2013** à demora dos órgãos em organizar e disponibilizar os dados" | "os anos recentes, **2019 e 2020**, têm uma quantidade **muito baixa** de dados de pluviômetros (...) supomos que os órgãos ainda não disponibilizaram os dados" |
| Avisos dos autores | Amazônia com 0,1 pluviômetro/1.000 km²; onde faltam estações o campo fica "liso" | o produto tem **valor limitado onde não há estação a 50 km**; a mudança da densidade de estações no tempo pode enganar a leitura de tendências; por isso entregam os controles **Count** (estações usadas) e **dist_nearest** (distância da estação mais próxima) |

O que isso significa para o SAB:
1. **Os dois artigos mostram o mesmo padrão**: o fim de cada versão é a parte mais fraca, porque os dados dos últimos
   anos ainda não chegaram (2013 na versão de 2016; 2019–2020 na de 2022).
2. **2021–2025 não está em nenhum artigo.** O que o asset `projects/ee-alexandrexavier/assets/BR-DWGD` tem depois de
   31/7/2020 é uma **extensão sem documentação publicada**: não sabemos que rede, quantas estações, nem se o método é o
   mesmo. Exatamente o período em que as 4 referências independentes acusam o salto.
3. O salto começa em **2020**, o ano que o próprio artigo diz ter "muito poucos dados" e cujo 2º semestre já é extensão.

##### 2. O que dizem os documentos oficiais das outras bases (de onde vem a chuva de cada uma)

| Base | Como a chuva é feita (documentação oficial) | Usa os pluviômetros da ANA/INMET? | Chuva do SAB em 2020–2024 em relação a ela (×2001–2015) |
|---|---|---|---|
| **GLDAS-2.1** (Rodell et al. 2004; README GES DISC) | modelo forçado pela chuva do GPCP 1DD (satélite ajustado ao GPCC mensal) | só pelo GPCC (rede global, via GTS) | **+8 a +12%** |
| **IMERG Final** (Huffman et al., ATBD v06/v07) | satélites de micro-ondas + infravermelho, calibrados mês a mês pelo GPCC | só pelo GPCC | **+7 a +9%** |
| **PERSIANN-CDR** (Ashouri et al. 2015, BAMS) | infravermelho + rede neural, ajustado ao GPCP mensal | só pelo GPCP/GPCC | **+9 a +14%** |
| **TerraClimate** (Abatzoglou et al. 2018, Sci. Data) | climatologia WorldClim + anomalias do CRU TS (estações) e JRA-55 | só pelo CRU (rede global) | **+11%** |
| **CHIRPS v2** (Funk et al. 2015, Sci. Data) | satélite infravermelho + climatologia + **mistura com estações** (inclui redes nacionais) | **em parte** (o CHIRPS mistura estações; pode ter parte da mesma rede) | **0 a +5%** |
| **ERA5-Land** (Muñoz-Sabater et al. 2021, ESSD) | reanálise; a chuva é do modelo, **não assimila pluviômetros** | não | (é a base corrigida pela V1.8; não serve de juiz da chuva) |

O ponto decisivo: **quatro famílias de produtos feitas de jeitos completamente diferentes** (modelo de superfície,
micro-ondas, infravermelho com rede neural, interpolação de anomalias do CRU) mudam a relação com o SAB **no mesmo ano
(2020) e no mesmo sentido**, depois de 40 anos estáveis (±3%). Para o problema estar nelas, as quatro teriam de errar
juntas e para menos a partir de 2020. A única fonte que muda de natureza exatamente em 2020 é o BR-DWGD (fim do artigo,
rede rala, extensão sem documentação). O CHIRPS concordar mais é coerente: ele **também usa estações**, então pode
compartilhar parte do mesmo viés.

##### 3. Conclusão (provável, ainda não definitiva)
- **Sim, o mais provável é que o excesso venha do BR-DWGD de 2020 em diante**, não das outras bases.
- O mecanismo ainda não está provado. Rede rala no ADW tende a aumentar os dias com chuva e a reduzir a intensidade
  (o campo "espalha" a chuva de poucos pluviômetros). Uma mudança na composição da rede (mais estações automáticas ou
  telemétricas, outras regiões) também pode mudar o total. Quem responde é o `pesquisa/investigar_brdwgd.py` (rodando
  desde 26/11 10h30): total, dias ≥ 1 mm, intensidade e cobertura ano a ano contra CHIRPS e ERA5, mais as bandas e
  propriedades de cada ano (se o asset tiver Count/dist_nearest, dá para ver a rede encolher).
- **Consequência para a V1.8:** as 60 razões do C3 saem de 2021–2025, justamente o trecho suspeito. Se o BR-DWGD estiver
  ~9% alto ali, a V1.8 empurra a chuva de 2026 ~9% para cima (o Sul +15,5% × CHIRPS é coerente com isso). **A
  suspensão do merge está confirmada pela leitura dos artigos.**
- **Caminho proposto (só com autorização):** refazer as razões do C3 com anos que os artigos cobrem com rede cheia
  (ex.: 2010–2018), repetir o teste fora da amostra da fase 1 com essa janela (protocolo novo congelado antes) e só
  então decidir a V1.8. O histórico 1961–2019 não é afetado; 2020–2025 do banco passa a ter um aviso (e, no M5, é
  candidato a ajuste na leitura, se confirmado por 2 referências — já está: 4).

##### 4. Correção depois do site oficial (26/11/2026, ~11h15)
Fonte: https://sites.google.com/site/alexandrecandidoxavierufes/brazilian-daily-weather-gridded-data (texto salvo em
`fontes/site_brdwgd_26-11-2026.txt`) e o relatório da versão v_3.2.4 (rascunho de 17/04/2026, Google Drive
1BXtsNRcq3JYmO-RAIMOOIyqJI-mOpU7S; figura dos pluviômetros em `fontes/relatorio_v3_2_4_pluviometros.png`).

**Notas de versão:** v_3.1 (mar/2023: chuva de 2001–2022 com mais pluviômetros); v_3.2.1 e v_3.2.2 (2023: arquivos e
contorno); v_3.2.3 (dez/2024: até 20/03/2024, projeto Climaterna); **v_3.2.4 (abr/2026: 1961–2025; no Earth Engine em
mai/2026)**. Relatório da v_3.2.4: 15.116 pluviômetros (11.632 manuais; 3.484 automáticos: 2.876 da ANA e 608 do INMET);
ADW na chuva; validação cruzada com R 0,648 e viés 0,001 mm/dia.

**O que muda na seção 1:** a extensão depois de 2020 **está documentada** (versões e relatório). E, na v_3.2.4, a rede de
2020–2024 **não é rala**: ~5.700 pluviômetros, perto do máximo histórico (o "muito poucos dados em 2019–2020" do artigo
de 2022 valia para a versão antiga). Portanto **a explicação "rede rala" não vale para 2020–2024**. Ela vale para o
**fim de 2025**: a figura mostra a rede despencando para ~1.000–2.000 nos últimos meses (de novo, dados ainda não
liberados).

**O que o site e o relatório não respondem:** (1) o relatório é rascunho, sem texto sobre quais pluviômetros entraram
em cada versão; (2) a validação cruzada compara a grade com os próprios pluviômetros: viés ≈ 0 mostra que a
interpolação é fiel à rede, **não** que a rede está certa; um viés da própria rede (composição, sensores) não aparece
nessa conta; (3) não há comparação com fontes independentes.

**Mudança na rede que coincide com o salto:** a figura mostra a parte manual subindo de ~4.400 (2016) para ~5.000
(2020–2024) e as automáticas/mescladas mudando em 2015–2024. O salto da chuva é maior no **Norte e Nordeste** (+20%
contra GLDAS-2.1, IMERG, PERSIANN; +7 a +10% até contra o CHIRPS) e menor no Sudeste, onde a rede é densa há décadas.

**Ressalva sobre as referências:** IMERG, PERSIANN-CDR (via GPCP) e GLDAS-2.1 (via GPCP) são todos ajustados ao GPCC,
cuja versão mais completa (Full Data) termina em 2020; depois entra a de monitoramento, com menos estações. Elas podem
mudar juntas, então valem como **uma** família, não três. Ainda assim, o TerraClimate (CRU, sem GPCC) e o CHIRPS (rede
própria) também mostram o salto: são **3 famílias de pluviômetros diferentes** apontando para o mesmo lado. O ERA5-Land
(sem pluviômetro nenhum) será a 4ª, no `investigar_brdwgd.py` (BR/ERA5 ano a ano).

**Conclusão revista:** o BR-DWGD continua sendo o suspeito mais provável, **mas não está provado**, e a causa não é a rede
rala (exceto no fim de 2025). A hipótese principal passa a ser **a composição da rede** (pluviômetros que entraram nas
versões 3.1–3.2.4, sobretudo no Norte e Nordeste). Para a V1.8, a recomendação fica: razões do C3 de anos estáveis
(2010–2019) e **nunca do fim de 2025**.

### BR-DWGD bruto ano a ano

Arquivo: `pesquisa/resultados_brdwgd/RESULTADOS.md`

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
| 26/11/2026 11:14 | Registro: análise profunda proposta (todo o banco) com o NASA POWER como testemunha, a pedido do responsável |
| 26/11/2026 11:10 | Registro em dia (26/11): investigação do BR-DWGD (artigos, site, relatório v_3.2.4), V1.8 suspensa esperando decisão, resultados da fase 2 e do multifonte no REGISTRO_GERAL |
| 26/11/2026 11:05 | BR-DWGD: análise revista com o site oficial e o relatório da v_3.2.4 (rede densa em 2020–2024; fim de 2025 ralo; referências GPCC contam como uma) |
| 26/11/2026 10:44 | Leitura dos artigos do BR-DWGD (2016, 2022) × documentação das outras bases: excesso de chuva pós-2020 provavelmente do BR-DWGD |
| 26/11/2026 10:30 | Conferência: começou brdwgd  |
| 26/11/2026 10:29 | Investigação do BR-DWGD bruto (salto da chuva em 2020): metadados por ano, decomposição da chuva (total, dias, intensidade, cobertura) × CHIRPS e ERA5, banco = bruto? |
| 26/11/2026 10:15 | Registro: leva 2 sem aprovação; merge da V1.8 suspenso (4 fontes indicam chuva do BR-DWGD 2021-25 ~9% alta) |
| 26/11/2026 10:14 | Várias referências: resumo refeito (chuva por satélite completa; ERA5-Land e GLDAS-2.0 parciais) |
| 26/11/2026 09:53 | Conferência: começou multifonte_gldas20  |
| 26/11/2026 09:52 | Conferência: multifonte_gldas20 (pendente)  |
| 26/11/2026 09:46 | Conferência: começou multifonte_era5  |
| 26/11/2026 09:45 | Conferência: multifonte_era5 (pendente)  |
| 26/11/2026 09:32 | Conferência: começou resolucao  |
| 26/11/2026 09:31 | Conferência: resolucao (pendente)  |
| 26/11/2026 08:53 | Conferência: multifonte_chuva (ok)  |
| 26/11/2026 06:13 | Fila: o corte por tempo (com progresso salvo) não conta como tentativa |
| 26/11/2026 05:59 | Várias referências: resumo refeito com todas as fontes prontas (MOD16 entrou) |
| 26/11/2026 05:50 | Conferência: multifonte_gldas21 (ok)  |
| 26/11/2026 05:14 | Conferência: multifonte_mod16 (ok)  |
| 26/11/2026 04:55 | Conferência: começou multifonte_mod16  |
| 26/11/2026 04:55 | Conferência: multifonte_mod16 (pendente)  |
| 26/11/2026 04:37 | Conferência: começou multifonte_gldas20  |
| 26/11/2026 04:37 | Conferência: começou multifonte_era5  |
| 26/11/2026 04:37 | Conferência: multifonte_gldas20 (pendente)  |
| 26/11/2026 04:37 | Conferência: multifonte_era5 (pendente)  |
| 26/11/2026 04:35 | Conferência: começou multifonte_gldas21  |
| 26/11/2026 04:35 | Conferência: multifonte_gldas21 (pendente)  |
| 26/11/2026 04:29 | Conferência: começou multifonte_chuva  |
| 26/11/2026 04:29 | Conferência: multifonte_chuva (pendente)  |
| 26/11/2026 04:16 | Conferência: começou resolucao  |
| 26/11/2026 04:16 | Registro: leva 2 disparada; parcial da leva 1 |
| 26/11/2026 04:16 | Conferência: resolucao (pendente)  |
| 25/11/2026 23:40 | Registro: o que será corrigido e a etapa final automática (recomendações, PR, pacote) |
| 25/11/2026 23:40 | Conferência: começou multifonte_mod16  |
| 25/11/2026 23:39 | Várias referências: MOD16A2GF (2001-; o MOD16A2 061 só começa em 2021) e mês vazio sem erro; mod16 volta à fila |
| 25/11/2026 23:22 | Conferência: começou multifonte_chuva  |
| 25/11/2026 23:22 | Conferência: multifonte_mod16 (falhou)  |
| 25/11/2026 23:22 | Conferência: começou multifonte_mod16  |
| 25/11/2026 23:22 | Conferência: multifonte_mod16 (pendente)  |
| 25/11/2026 23:22 | Conferência: começou multifonte_mod16  |
| 25/11/2026 23:22 | Conferência: multifonte_mod16 (pendente)  |
| 25/11/2026 23:22 | Conferência: começou multifonte_gldas20  |
| 25/11/2026 23:22 | Registro: várias referências (emenda 1 da fase 2) disparadas |
| 25/11/2026 23:22 | Conferência: começou multifonte_gldas21  |
| 25/11/2026 23:22 | Conferência: começou multifonte_mod16  |
| 25/11/2026 23:22 | Conferência: começou multifonte_era5  |
| 25/11/2026 23:21 | Várias referências contra o banco (fase 2, emenda 1): ERA5-Land bruto, GLDAS-2.0 e 2.1, PERSIANN-CDR, IMERG, MOD16; 5 cadeias na fila |
| 25/11/2026 23:10 | Registro: historico pronto; décadas com degrau e o que a 2ª referência precisa confirmar (M5) |
| 25/11/2026 23:01 | Conferência: começou resolucao  |
| 25/11/2026 23:00 | Conferência: resolucao (pendente)  |
| 25/11/2026 22:52 | Conferência: historico (ok)  |
| 25/11/2026 22:52 | Conferência: começou historico  |
| 25/11/2026 22:52 | Conferência: historico (pendente)  |
| 25/11/2026 22:48 | Fase 2: protocolo, M1-C3R (não passou), leva 1 rodando; registro |
| 25/11/2026 22:20 | Registro: V1.8 aprovada; PR sab-motor#4 junta depois da prévia com 2026 inteiro |
| 25/11/2026 22:17 | Registro: a vigia dispara as rotinas por relógio do sab-pedidos (o agendamento do GitHub não dispara) |
| 25/11/2026 22:14 | Registro: K26 rodada 7 pronta |
| 25/11/2026 21:03 | Correção ERA5: relato 2026 x CHIRPS (o C3 aproxima NE e CO; passa do ponto no Sul); teste completo |
| 25/11/2026 20:35 | Registro: prévia da V1.8 passou (1 dia); refazer depois do motor da noite |
| 25/11/2026 20:16 | Registro: vigia automática e mapa do que é verificado (variável x referência x período) |
| 25/11/2026 20:08 | Registro: motor V1.8 etapa A (simulação disparada) e fila da main disparada |
| 25/11/2026 20:01 | Registro: sab-pedidos público (minutos do Actions deixam de faltar) |
| 25/11/2026 18:29 | Correção ERA5: resultado (chuva → C3; radiação/ETo → C0 fica), dados e registro; minutos do Actions esgotados |
| 25/11/2026 17:53 | Conferência: começou resolucao  |
| 25/11/2026 17:53 | Conferência: resolucao (pendente)  |
| 25/11/2026 17:39 | Conferência: começou historico  |
| 25/11/2026 17:38 | Conferência: historico (pendente)  |
| 25/11/2026 16:30 | Fila: repete a chamada da próxima execução se o GitHub responder erro (500 em 25/11 parou uma cadeia) |
| 25/11/2026 15:55 | Registro em dia (25/11, ~13h): o que roda, decisões, lista do que falta auditar e corrigir; script e teste da correção também no validacoes-2 |
| 25/11/2026 15:43 | Registro: rotina de saúde renomeada para conferência da gravação (PR #11); agendamentos atrasados |
| 25/11/2026 15:34 | Registro: resolucao roda completa (decisão do responsável); ritmo das cadeias |
| 25/11/2026 12:38 | Conferência: começou resolucao  |
| 25/11/2026 12:37 | Conferência: resolucao (pendente)  |
| 25/11/2026 12:23 | Conferência: começou historico  |
| 25/11/2026 12:22 | Conferência: historico (pendente)  |
| 25/11/2026 10:48 | Protocolo da correção: emenda 1 (antes de rodar) e registro do teste disparado |
| 25/11/2026 10:05 | Registro: script do teste da correção pronto (branch de trabalho), esperando autorização do disparo |
| 25/11/2026 09:56 | Registro: Parte B pronta (2026 x GLDAS confirma a chuva baixa no Nordeste e no Centro-Oeste); protocolo da correção aprovado e congelado |
| 25/11/2026 09:56 | Protocolo da correção dos dias ERA5: APROVADO e congelado antes de rodar (2026 x CHIRPS só como relato) |
| 25/11/2026 09:50 | Registro: linha de 25/11 dentro da tabela da linha do tempo |
| 25/11/2026 09:50 | Registro: branches das conversas (claude/*), decisões esperando o responsável, protocolo da correção em rascunho e comando de retomada que busca todos os branches |
| 25/11/2026 09:33 | Entrega: a base de montagem (pasta 07), os extras e um script que remonta o zip só com o repositório |
| 25/11/2026 08:33 | Registro: resultado da Parte A (o método de 2026 subestima a chuva ~10% em 2021-2025) e o próximo trabalho |
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

