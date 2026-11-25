# Correção da chuva, da radiação e da ETo nos dias ERA5: teste fora da amostra

Protocolo aprovado e congelado antes de rodar (`pesquisa/PROTOCOLO_CORRECAO_ERA5_2026.md`, com a emenda 1: extremos em todos os pixels). Cada ano de teste é calibrado só com os anos anteriores. Referência: o que o banco entrega (BR-DWGD no núcleo), pixels entregues. Só leitura: nada foi gravado no Earth Engine.

Conferência da receita (média 1986-2025 recalculada × `SICSB_1986_2025`, janeiro e julho, 6 regiões, chuva e radiação): maior diferença 1.55% (limite 2%).

**Parcial:** 8 de 10 anos de teste completos ([2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]). A decisão só sai com os 10.

## Chuva: |viés anual| (mediana dos anos de teste) e r_anomalias

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil | Mediana das 5 |
|---|---|---|---|---|---|---|---|
| C0 | 6.8% (r 0.90) | 6.8% (r 0.98) | 8.7% (r 0.94) | 7.1% (r 0.98) | 8.4% (r 0.96) | 7.5% (r 0.90) | 7.09% |
| C1 | 6.3% (r 0.89) | 5.1% (r 0.98) | 7.5% (r 0.94) | 4.2% (r 0.98) | 2.6% (r 0.96) | 6.4% (r 0.91) | 5.09% |
| C2 | 6.6% (r 0.89) | 5.3% (r 0.98) | 8.8% (r 0.94) | 4.2% (r 0.98) | 3.5% (r 0.96) | 6.7% (r 0.90) | 5.33% |
| C3 | 5.0% (r 0.91) | 4.2% (r 0.98) | 6.8% (r 0.94) | 3.5% (r 0.98) | 2.4% (r 0.96) | 4.6% (r 0.93) | 4.19% |

### Viés anual da chuva no Brasil (%)

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

## Dias de chuva e maior chuva do mês, em todos os pixels entregues

Em cada célula: fração de dias com chuva (%) / erro do Rx1day (%). BR-DWGD: só a fração.

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| BR-DWGD | 65.0 | 29.8 | 41.7 | 32.1 | 36.0 | 48.4 |
| C0 | 65.6 / 47.8 | 34.0 / 53.0 | 42.8 / 44.1 | 34.5 / 43.4 | 38.3 / 39.1 | 50.1 / 46.4 |
| C1 | 66.2 / 48.1 | 34.1 / 54.0 | 43.2 / 44.9 | 34.9 / 44.3 | 38.9 / 39.9 | 50.5 / 47.0 |
| C2 | 66.1 / 47.8 | 34.1 / 53.6 | 43.3 / 44.5 | 35.0 / 44.1 | 38.8 / 39.6 | 50.5 / 46.7 |
| C3 | 66.1 / 48.0 | 34.5 / 53.6 | 43.4 / 44.5 | 35.2 / 43.8 | 39.0 / 39.4 | 50.6 / 46.8 |

## Radiação e ETo: viés nos meses de teste

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| C0 | +0.45 MJ / +2.8% | +0.43 MJ / +1.7% | +0.40 MJ / +1.5% | +0.10 MJ / -0.1% | +0.47 MJ / -0.1% | +0.40 MJ / +1.8% |
| C1 | +0.51 MJ / +3.1% | +0.48 MJ / +1.9% | +0.44 MJ / +1.7% | +0.27 MJ / +0.5% | +0.48 MJ / +0.0% | +0.46 MJ / +2.1% |
| C2 | +0.61 MJ / +3.5% | +0.52 MJ / +2.0% | +0.43 MJ / +1.7% | +0.22 MJ / +0.4% | +0.49 MJ / +0.0% | +0.51 MJ / +2.3% |
| C3 | +0.34 MJ / +2.3% | +0.29 MJ / +1.3% | +0.27 MJ / +1.0% | +0.15 MJ / +0.1% | +0.19 MJ / -1.1% | +0.29 MJ / +1.4% |

