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
