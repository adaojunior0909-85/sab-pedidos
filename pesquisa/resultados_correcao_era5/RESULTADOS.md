# Correção da chuva, da radiação e da ETo nos dias ERA5: teste fora da amostra

Protocolo aprovado e congelado antes de rodar (`pesquisa/PROTOCOLO_CORRECAO_ERA5_2026.md`, com a emenda 1: extremos em todos os pixels). Cada ano de teste é calibrado só com os anos anteriores. Referência: o que o banco entrega (BR-DWGD no núcleo), pixels entregues. Só leitura: nada foi gravado no Earth Engine.

Conferência da receita (média 1986-2025 recalculada × `SICSB_1986_2025`, janeiro e julho, 6 regiões, chuva e radiação): maior diferença 1.55% (limite 2%).

## Chuva: |viés anual| (mediana dos anos de teste) e r_anomalias

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil | Mediana das 5 |
|---|---|---|---|---|---|---|---|
| C0 | 6.8% (r 0.89) | 8.7% (r 0.98) | 9.8% (r 0.93) | 6.3% (r 0.98) | 8.4% (r 0.96) | 7.6% (r 0.89) | 8.39% |
| C1 | 6.3% (r 0.89) | 6.4% (r 0.98) | 7.5% (r 0.93) | 3.6% (r 0.98) | 3.1% (r 0.95) | 6.4% (r 0.89) | 6.28% |
| C2 | 6.6% (r 0.89) | 7.1% (r 0.98) | 9.2% (r 0.93) | 3.9% (r 0.98) | 4.2% (r 0.95) | 6.7% (r 0.89) | 6.59% |
| C3 | 5.5% (r 0.89) | 4.3% (r 0.98) | 5.7% (r 0.93) | 4.0% (r 0.98) | 2.6% (r 0.95) | 4.6% (r 0.90) | 4.28% |

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
| 2024 | -13.6 | -10.7 | -12.3 | -6.2 |
| 2025 | -7.3 | -2.6 | -4.7 | +3.1 |

## Dias de chuva e maior chuva do mês, em todos os pixels entregues

Em cada célula: fração de dias com chuva (%) / erro do Rx1day (%). BR-DWGD: só a fração.

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| BR-DWGD | 64.4 | 29.7 | 41.4 | 31.7 | 36.1 | 48.0 |
| C0 | 64.1 / 48.6 | 33.3 / 53.0 | 42.3 / 44.6 | 34.1 / 43.7 | 38.5 / 39.0 | 49.1 / 46.9 |
| C1 | 64.8 / 48.8 | 33.5 / 54.0 | 42.7 / 45.4 | 34.6 / 44.5 | 39.1 / 39.9 | 49.7 / 47.5 |
| C2 | 64.7 / 48.6 | 33.4 / 53.6 | 42.7 / 45.0 | 34.6 / 44.3 | 39.0 / 39.6 | 49.6 / 47.2 |
| C3 | 64.9 / 49.3 | 33.9 / 54.0 | 43.0 / 45.1 | 34.9 / 44.1 | 39.2 / 39.5 | 49.9 / 47.6 |

## Radiação e ETo: viés nos meses de teste

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| C0 | +0.55 MJ / +3.4% | +0.47 MJ / +2.2% | +0.41 MJ / +1.6% | +0.12 MJ / +0.0% | +0.48 MJ / +0.0% | +0.45 MJ / +2.2% |
| C1 | +0.54 MJ / +3.4% | +0.47 MJ / +2.1% | +0.38 MJ / +1.5% | +0.25 MJ / +0.6% | +0.45 MJ / -0.0% | +0.46 MJ / +2.2% |
| C2 | +0.66 MJ / +3.9% | +0.53 MJ / +2.3% | +0.42 MJ / +1.7% | +0.23 MJ / +0.5% | +0.48 MJ / +0.1% | +0.53 MJ / +2.5% |
| C3 | +0.32 MJ / +2.4% | +0.24 MJ / +1.4% | +0.21 MJ / +0.9% | +0.11 MJ / +0.1% | +0.15 MJ / -1.2% | +0.25 MJ / +1.4% |

## Percentil 99 diário em 1500 pixels A (5.479.500 pixel-dias de 2016-2025)

Fração de dias com chuva no BR-DWGD nesses pixels: 40.8%.

| Método | Fração de dias com chuva (%) | Erro do percentil 99 |
|---|---|---|
| C0 | 42.9 | 16.8% |
| C1 | 43.3 | 13.7% |
| C2 | 43.3 | 14.3% |
| C3 | 43.6 | 13.8% |

## Decisão (regra fixada antes)

### Chuva

| Método | 1. mediana cai >= 3 p.p. | 2. Brasil melhora em >= 7 de 10 anos | 3. r_anom não cai > 0,02 | 4a. dias de chuva (todas as regiões) | 4b. Rx1day (todas as regiões) | 4c. p99 | Passa? |
|---|---|---|---|---|---|---|---|
| C1 | ❌ +2.11 p.p. | ✅ 9 | ✅ maior queda +0.003 | ✅ pior região +0.57 p.p. além do C0 | ✅ pior região +2.2% | ✅ 13.7% (C0 16.8%) | ❌ |
| C2 | ❌ +1.80 p.p. | ✅ 9 | ✅ maior queda +0.004 | ✅ pior região +0.50 p.p. além do C0 | ✅ pior região +1.5% | ✅ 14.3% (C0 16.8%) | ❌ |
| C3 | ✅ +4.11 p.p. | ✅ 9 | ✅ maior queda +0.003 | ✅ pior região +0.76 p.p. além do C0 | ✅ pior região +1.8% | ✅ 13.8% (C0 16.8%) | ✅ |

**Chuva: troca para C3.**

### Radiação e ETo

| Método | |viés| da radiação no Brasil cai (MJ) | |viés| da ETo no Brasil cai (p.p.) | pior região (MJ / p.p.) | Passa? |
|---|---|---|---|---|
| C1 | -0.00 | -0.03 | +0.13 / +0.51 | ❌ |
| C2 | -0.08 | -0.33 | +0.11 / +0.53 | ❌ |
| C3 | +0.21 | +0.79 | -0.01 / +1.10 | ❌ |

**Radiação e ETo: nenhum método passou; o C0 (atual) fica.**

Nada é gravado por este teste. Se algum método passou, o próximo passo (com aprovação) é o motor em simulação (05a), a prévia de 2026 e a K16; uma janela de anos exige um asset novo (escrita, aprovação separada).

## Só relatado (fora da regra): 2026 × CHIRPS

Meses 1 a 9; viés do total do período contra o CHIRPS (%). Régua: 2024, quando o SAB é o BR-DWGD. Método vencedor na chuva: C3.

| Região | 2024 (régua) | 2026 gravado | 2026 C0 | 2026 C1 | 2026 C2 | 2026 C3 |
|---|---|---|---|---|---|---|
| Norte | +2.4 | -1.2 | -1.3 | +3.5 | +0.8 | +7.1 |
| Nordeste | +6.6 | -15.6 | -15.9 | -10.8 | -12.7 | -4.1 |
| Centro-Oeste | -1.4 | -21.3 | -21.3 | -15.2 | -17.9 | -10.0 |
| Sudeste | -1.1 | -2.9 | -2.9 | +3.3 | +1.7 | +5.6 |
| Sul | +3.8 | +4.1 | +4.4 | +13.4 | +11.5 | +15.5 |
| Brasil | +2.3 | -5.8 | -5.9 | -0.4 | -2.9 | +3.6 |

