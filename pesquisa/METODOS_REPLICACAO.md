# Validação do SAB contra referências independentes: métodos para replicação e auditoria

Este documento descreve, com o detalhe necessário para outra pessoa refazer cada número, todas as comparações do SAB
com referências de fora: as fontes, a agregação no espaço e no tempo, as unidades, as fórmulas das métricas, as
regras de decisão (fixadas antes de rodar) e os arquivos de saída. Tudo é **só leitura** no Earth Engine.

## 1. Como refazer

1. Python 3.12 com `earthengine-api==1.7.51`, `pandas`, `numpy` (`requirements.txt` e `pesquisa/requirements.txt`).
2. Uma conta do Earth Engine. Os assets do SAB (`projects/clima-492922/assets/SAB_V1`, `SAB_MASCARA_QUALIDADE`,
   `SICSB_SOLO_2015_2025`) têm leitura pública; o projeto de cobrança é o da sua conta (troque `PROJETO` em
   `sab_pedido.py` se precisar).
3. Rode, na raiz do repositório (cada script diz no cabeçalho o que faz e a regra fixada):

| Comparação | Comando | Saída bruta (valores mensais pareados) |
|---|---|---|
| 2026 × CHIRPS (chuva) e MODIS (anomalia de calor) | `python pesquisa/validar_2026_independente.py` | `pesquisa/resultados_2026/validacao_2026_independente.csv` |
| Solo, folha, ET real × SMAP e MODIS (2016–2021) | `python pesquisa/validar_solo_folha.py` | `pesquisa/resultados_solo_folha/series_mensais.csv` |
| Escoamento × vazão CAMELS-BR (1981–2018) | `python pesquisa/escoamento/preparar_camels.py <pasta CAMELS>`; `python pesquisa/escoamento/escoamento_camels.py`; `python pesquisa/escoamento/escoamento_metricas.py` | `pesquisa/resultados_escoamento/anos/*.csv.gz` + `pesquisa/dados/camels/vazao_mensal.csv.gz` |
| As 16 variáveis: o método de 2026 em 2021–2025 | `python pesquisa/validar_metodo_2026.py A` | `pesquisa/resultados_metodo_2026/parte_a/*.csv` |
| As 16 variáveis: 2026 × GLDAS-2.1 (régua 2022–2024) | `python pesquisa/validar_metodo_2026.py B` | `pesquisa/resultados_metodo_2026/parte_b_gldas.csv` |
| Histórico 1961–2025 × TerraClimate e CHIRPS | `python pesquisa/validar_historico.py` | `pesquisa/resultados_historico/anos/*.csv` |
| Todas as métricas, região × período × mês | `python pesquisa/metricas_completas.py` | `pesquisa/METRICAS_COMPLETAS.csv.gz`, `pesquisa/DADOS_PAREADOS.csv.gz` |
| Resumo por mês do ano (legível) | `python pesquisa/resumo_por_mes.py` | `pesquisa/RESULTADOS_POR_MES.md` |

No repositório, essas tarefas rodam pela fila `rotinas/conferencia/fila.py` (GitHub Actions); o LOG de cada execução
fica em `rotinas/conferencia/logs/<tarefa>.txt`, com o commit do código e a versão da biblioteca do Earth Engine.

## 2. O dado do SAB comparado

- **O que o usuário recebe**, não o asset cru: a coleção montada por `sab_pedido.colecao()` (versão no cabeçalho do
  `sab_pedido.py`; 2026.11.22 nestas comparações). Ela aplica, como o painel: a correção de leitura do solo e do
  escoamento nos dias V1.0 (fator mensal SMAP/ERA5 com teto 5 e teto físico da umidade), a correção dos pixels B pelo
  BR-DWGD (1961–2025), o grampo termodinâmico (ET real ≤ ETo, transpiração ≤ ET real) e a radiação impossível vazia
  (Rs < 3% da radiação no topo da atmosfera → Rs, ETo e déficit vazios).
- Exceções, ditas em cada script: o escoamento M1 (o gravado, sem a correção de leitura) e o "método de 2026"
  (parte A), que é a rota ERA5 do motor V1.7 (`pesquisa/motor/05a_motor_sab_v1_7_SIMULACAO.py`, SHA-256 conferido
  antes de rodar; só as funções, sem nenhuma escrita).
- **Pixels usados:** só os entregues, classes 1 a 3 (A, B, C_interior) de `SAB_MASCARA_QUALIDADE`; a C_borda fica fora.

## 3. Agregação no espaço

- **Grade:** a do SAB, `EPSG:4326`, `crsTransform = [0,09999847412109375, 0, −73,9000015258789, 0, −0,09999847412109375,
  5,400000095367432]` (~0,1°). Toda referência é lida nessa grade (o Earth Engine reamostra na hora do cálculo; nada é
  exportado).
- **Regiões:** estados do FAO GAUL 2015 nível 1 (`FAO/GAUL/2015/level1`, `ADM0_NAME = Brazil`), unidos nas 5 regiões
  do IBGE pelo dicionário `UF_REGIAO` de `pesquisa/hindcast.py` (união com erro máximo de 100 m); "Brasil" = a união de
  todos os estados.
- **Média da região:** `reduceRegions(ee.Reducer.mean())`, que pesa cada pixel pela fração dele dentro do polígono e
  pela máscara (fracionária na borda); `tileScale` 8 ou 16 (só memória; não muda o resultado).
- **Bacias (escoamento):** os contornos do CAMELS-BR v1.1 (`14_CAMELS_BR_catchment_boundaries`), simplificados com
  tolerância 0,01° (1/10 do pixel), mesma média ponderada pela fração do pixel.

## 4. Agregação no tempo e unidades

- **Mês:** soma dos dias para chuva, ETo, ET real, transpiração e escoamento (mm/mês); média dos dias para o resto.
- **Conversões das referências** (como estão nos scripts):

| Referência | Banda | Conversão para a unidade do SAB |
|---|---|---|
| CHIRPS (pentadas) | `precipitation` | soma das pentadas que começam no mês (mm/mês) |
| MODIS MOD11A2 / MYD11A2 | `LST_Day_1km`, `LST_Night_1km` | × 0,02 − 273,15 (°C); média dos compostos de 8 dias do mês |
| MODIS MOD16A2GF | `ET` | × 0,1, soma dos compostos de 8 dias que começam no mês |
| SMAP SPL3SMP_E/006 | `soil_moisture_am` | m³/m³, média do mês |
| TerraClimate | `pr`, `tmmx`, `tmmn`, `vpd`, `srad`, `vs`, `pet`, `aet`, `soil`, `ro` | mm; × 0,1 °C; × 0,1 °C; × 0,01 kPa; × 0,1 W/m² × 0,0864 → MJ/m²/dia; × 0,01 m/s × 0,748 (10 m → 2 m, FAO-56 eq. 47); × 0,1 mm; × 0,1 mm; × 0,1 mm (só correlação: unidade diferente); mm |
| GLDAS-2.1 Noah 3 h | `Rainf_f_tavg`, `Evap_tavg` | kg m⁻² s⁻¹ × 86.400 × dias do mês (mm/mês) |
| | `PotEvap_tavg`, `Tveg_tavg` | W/m² × 0,0864/2,45 × dias (mm/mês) |
| | `Qs_acc`, `Qsb_acc` | soma das saídas de 3 h (mm/mês) |
| | `Tair_f_inst` | máxima e mínima de cada dia (8 saídas) − 273,15, média do mês (°C) |
| | `Qair_f_inst`, `Psurf_f_inst`, `Tair_f_inst` | e = q·p/(0,622 + 0,378 q); es = 611,2·exp(17,67 T/(T + 243,5)); UR = 100 e/es (≤ 100); VPD = (es − e)/1000 kPa |
| | `SWdown_f_tavg` | W/m² × 0,0864 (MJ/m²/dia) |
| | `Wind_f_inst` | × 0,748 (m/s a 2 m) |
| | `SoilTMP0_10cm_inst`, `AvgSurfT_inst` | − 273,15 (°C) |
| | `SoilMoi0_10cm_inst`; 0–10 + 10–40 + 40–100 cm | ÷ 100 (m³/m³ em 10 cm); ÷ 1000 (m³/m³ em 1 m) |
| CAMELS-BR | `streamflow_mm` (diária) | média dos dias observados × dias do mês; só meses com ≥ 25 dias observados |

## 5. As referências e o quanto são independentes

| Referência | O que é | Independência do SAB | Citação |
|---|---|---|---|
| CHIRPS v2 | satélite (IR) + estações | parcial: usa estações, algumas também no BR-DWGD; independente do ERA5 | Funk et al. (2015), *Sci. Data* 2:150066 |
| MODIS LST (Terra/Aqua) | temperatura da superfície por satélite | total; nível afetado pela deriva da órbita (Terra desde 2022, Aqua desde 2022) | Wan et al., MOD11 C6.1 |
| MODIS MOD16A2GF | ET por satélite (Penman-Monteith-Mu) | total; fraco em áreas de muita nuvem | Running et al., MOD16 C6.1 |
| SMAP L3 enhanced | umidade do solo 0–5 cm por micro-ondas | total; mas o fator de leitura do solo do SAB usa a média mensal do SMAP 2015–2025, por isso só a correlação das anomalias é independente | O'Neill et al., SPL3SMP_E v6 |
| TerraClimate | mensal, ~4 km: WorldClim + CRU TS + JRA-55 | parcial: CRU usa estações também no BR-DWGD | Abatzoglou et al. (2018), *Sci. Data* 5:170191 |
| GLDAS-2.1 | modelo Noah forçado por GDAS (NOAA), chuva GPCP e radiação AGRMET | independente do ECMWF/ERA5 e do BR-DWGD | Rodell et al. (2004), *BAMS* 85:381 |
| CAMELS-BR v1.1 | vazão observada da ANA, 512 bacias selecionadas | total | Chagas et al. (2020), *ESSD* 12:2075; doi:10.5281/zenodo.3964745 (CC-BY-4.0) |

## 6. Métricas (todas em `METRICAS_COMPLETAS.csv.gz`)

Para cada combinação de **comparação × referência × variável × região × período × mês** (s = SAB, o = referência,
sobre os n valores mensais do grupo):

| Coluna | Fórmula |
|---|---|
| `n` | número de valores mensais (no escoamento, bacia-meses) |
| `media_sab`, `media_ref` | médias de s e de o |
| `vies` | média de (s − o), na unidade da variável |
| `vies_pct` | 100 · (Σs / Σo − 1): viés do total (só faz sentido nas somas; coluna `soma` = verdadeiro) |
| `mae`, `rmse` | média de \|s − o\|; raiz da média de (s − o)² |
| `desvio_sab`, `desvio_ref` | desvio-padrão amostral |
| `r` | correlação de Pearson entre s e o |
| `r_anomalias` | Pearson entre as anomalias (s e o menos a média do mesmo mês do ano, em toda a série da comparação): tira o ciclo anual, mede se os anos secos/chuvosos e quentes/frios batem |
| `kge` | 1 − √((r − 1)² + (σs/σo − 1)² + (μs/μo − 1)²) (Gupta et al., 2009) |
| `nse` | 1 − Σ(s − o)² / Σ(o − ō)² (Nash e Sutcliffe, 1970) |

- **`periodo`:** `todos`, cada ano e, nas séries com 15 anos ou mais, cada década.
- **`mes`:** `todos` ou 1 a 12 (o mesmo mês do ano em todos os anos do período: mede a estação).
- Grupos com um valor só não têm métrica: o valor está em `DADOS_PAREADOS.csv.gz` (colunas `comparacao, referencia,
  variavel, regiao, ano, mes, sab, ref`).
- **Escoamento por bacia:** além das métricas por região hidrográfica (bacias juntas), `pesquisa/resultados_escoamento/
  metricas_bacias.csv` tem KGE, viés e r de cada uma das 512 bacias, como manda o protocolo.

## 7. Regras de decisão (fixadas antes de rodar; o commit que as fixou é anterior ao do resultado)

| Comparação | Regra | Onde |
|---|---|---|
| Escoamento | trocar o método atual só se outro subir a mediana do KGE em 0,10, melhorar em ≥ 60% das bacias, nas duas metades (1981–1999 e 2000–2018), sem piorar a mediana do \|viés\| | `pesquisa/PROTOCOLO_ESCOAMENTO_CAMELS.md` |
| Solo, folha, ET real | mediana das 5 regiões de `r_anomalias` ≥ 0,6 mantém; 0,3–0,6 índice com aviso; < 0,3 retirar | cabeçalho de `validar_solo_folha.py` |
| 2026 × GLDAS | suspeita se SAB − GLDAS em 2026 sair da faixa de 2022–2024 por mais que a tolerância (somas 5%; T 0,5 °C; UR 3 p.p.; VPD 0,1 kPa; Rs 0,5 MJ; vento 0,2 m/s; solo 0,02 m³/m³) | cabeçalho de `validar_metodo_2026.py` |
| Histórico por década | degrau se o viés da década se afastar da mediana das décadas por mais que a mesma tolerância, ou se `r_anomalias` < 0,5 com mediana ≥ 0,7 | cabeçalho de `validar_historico.py` |
| 2026 × CHIRPS/MODIS | sem regra de aprovação: medida, com 2024 (BR-DWGD) como régua | cabeçalho de `validar_2026_independente.py` |

## 8. O que pode mudar se alguém refizer mais tarde

Os dados de referência no Earth Engine são atualizados: o ERA5-Land já foi revisto (desde jul/2017, nas variáveis
acumuladas); o CHIRPS troca a versão preliminar pela final (com mais estações) semanas depois; o GLDAS-2.1 "early"
é substituído; o MODIS é reprocessado em coleções novas. Por isso cada LOG guarda a data da execução, e os CSV brutos
ficam no repositório: as métricas podem ser recalculadas deles sem o Earth Engine (`metricas_completas.py`). Não há
nenhum passo aleatório.
