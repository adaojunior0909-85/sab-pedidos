# A7. A cadeia (2026 e a previsão) herdou o degrau de 2020–2025?

Protocolo `pesquisa/PROTOCOLO_AUDITORIA_PROFUNDA.md`, A7. Regra: mudança > tolerância do A1 em ≥ 2 regiões = a cadeia herdou o degrau.

## Quais anos entram em cada calibração

| Calibração | Asset / objeto | Anos | Onde está no código |
|---|---|---|---|
| Fator de clima dos dias ERA5 (2026 em diante, V1.7/V1.8) | `SICSB_1986_2025` | 1986–2025 (6 de 40 anos no trecho) | sab-motor 05a_motor_sab_v1_8_SIMULACAO.py, ASSET_CLIMATOLOGIA (l. 179) |
| UR por quantis (EQM) dos dias ERA5 | `SICSB_EQM_1986_2025` | 1986–2025 (6 de 40) | 05a v1_8, ASSET_EQM (l. 183) |
| Razões da chuva da V1.8 (C3) | `RAZAO_CHUVA_C3` | 2021–2025 (todos no trecho) | 05a v1_8, cabeçalho (l. 12–14) |
| Previsão GFS 1–15 dias (matriz V2.1) | `SICSB_MATRIZ_GFS_V2` | rodadas de 23/03/2021 a 31/12/2025 (todos no trecho) | entrega/base_07/03_matriz_gfs_v2_1.py, INICIO_RODADAS/FIM_DIAS (l. 97–98) |
| Umidade do solo (fator SMAP/ERA5) | `SICSB_SOLO_2015_2025` | 2015–2025 (não usa o BR-DWGD: fora do degrau) | 05a v1_8, ASSET_SOLO (l. 181) |
| Normais 1991–2020 (painel) | `07a_normais_CONFERIR_1991_2020.py` | 1991–2020 (1 de 30) | entrega/base_07/07a |

## Fator de clima (SICSB_1986_2025) refeito sem 2020–2025

Mudança média do fator nos 12 meses (maior mês entre parênteses); + = o fator sem 2020–2025 seria maior.

| Variável | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | regiões acima da tolerância |
|---|---|---|---|---|---|---|
| Umidade relativa | -0.25 (-0.60) | -0.38 (-0.50) | -0.21 (-0.62) | -0.30 (-0.47) | -0.34 (-0.43) | 0  |
| Chuva | -2.2% (-5.4%) | -2.1% (-3.4%) | -2.4% (-4.6%) | -1.4% (-2.9%) | -1.3% (-2.7%) | 0  |
| Radiação | +0.8% (+1.6%) | +0.5% (+0.7%) | +0.5% (+0.8%) | +0.2% (+0.6%) | +0.4% (+0.9%) | 0  |
| Tmax | +0.07 (+0.12) | -0.02 (-0.04) | +0.04 (+0.10) | +0.03 (+0.06) | +0.02 (+0.05) | 0  |
| Tmin | -0.01 (-0.03) | -0.01 (-0.03) | -0.02 (-0.07) | -0.01 (-0.03) | +0.00 (-0.03) | 0  |
| Vento | +2.2% (+3.3%) | +2.3% (+2.8%) | +0.2% (+1.8%) | +0.1% (+0.8%) | -0.7% (-1.4%) | 0  |
| VPD | +0.011 (+0.029) | +0.012 (+0.018) | +0.008 (+0.029) | +0.010 (+0.014) | +0.010 (+0.014) | 0  |

## Matriz do GFS e razões da V1.8 (feitas só com 2021–2025)

Não há como refazê-las sem esses anos (o GFS v16 começa em 2021). A herança é o degrau do A1 em 2021–2025: mediana das famílias, média dos anos, **só onde o A1 confirmou degrau persistente** (célula com "·" = sem degrau confirmado no A1: o valor de uma família só é relato e não conta para a regra).

| Variável | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | regiões acima da tolerância |
|---|---|---|---|---|---|---|
| Chuva | **+14.5%** | **+16.9%** | **+12.8%** | · +6.1% | **+9.4%** | 4 → herdou |
| Tmax | · -0.80 | · -0.18 | **-0.76** | **-0.70** | · -0.29 | 2 → herdou |
| Tmin | · -0.18 | · +0.02 | · +0.08 | · -0.07 | · +0.09 | 0  |
| Radiação | **-6.4%** | **-3.8%** | · -2.5% | · -1.1% | · -1.6% | 2 → herdou |
| Umidade relativa | · +3.26 | **+3.42** | · +5.24 | **+4.88** | · +2.48 | 2 → herdou |
| Vento | · -8.4% | · -14.3% | · -8.2% | · -1.4% | · -1.6% | 0  |
| ETo | · -8.6% | · -5.7% | · -10.4% | · -10.6% | · -5.5% | 0  |
| VPD | **-0.150** | **-0.137** | **-0.209** | **-0.193** | **-0.091** | 5 → herdou |

