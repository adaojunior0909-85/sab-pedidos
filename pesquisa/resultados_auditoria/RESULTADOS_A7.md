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

Aguardando o ERA5-Land bruto até 2025 no `resultados_multifonte/era5` (hoje até 2005).

## Matriz do GFS e razões da V1.8 (feitas só com 2021–2025)

Não há como refazê-las sem esses anos (o GFS v16 começa em 2021). A herança é o degrau do A1 em 2021–2025: mediana das famílias, média dos anos, **só onde o A1 confirmou degrau persistente** (célula com "·" = sem degrau confirmado no A1: o valor de uma família só é relato e não conta para a regra).

| Variável | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | regiões acima da tolerância |
|---|---|---|---|---|---|---|
| Chuva | **+16.7%** | **+16.9%** | **+12.3%** | · +6.8% | **+12.0%** | 4 → herdou |
| Tmax | · -0.94 | · -0.29 | · -1.05 | **-0.94** | · -0.38 | 1  |
| Tmin | · -0.14 | · +0.08 | · -0.02 | · -0.15 | · +0.13 | 0  |
| Radiação | **-6.2%** | · -4.1% | · -2.6% | · -1.3% | · -1.3% | 1  |
| Umidade relativa | · +3.71 | **+4.42** | · +7.09 | **+8.08** | · +3.95 | 2 → herdou |
| Vento | · -6.4% | · -13.0% | · -9.7% | · -2.0% | · -0.1% | 0  |
| ETo | · -8.6% | · -5.7% | · -10.4% | · -10.6% | · -5.5% | 0  |
| VPD | · -0.189 | **-0.166** | **-0.286** | **-0.246** | · -0.103 | 3 → herdou |

