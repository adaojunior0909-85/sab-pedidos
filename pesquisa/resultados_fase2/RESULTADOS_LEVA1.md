# Fase 2, leva 1: M1 (garoa), M2-R1 (radiação) e M3-T2 (temperaturas, UR, vento)

Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (congelado no commit 9a12309 antes de rodar). Só leitura no Earth Engine. Nada é gravado: um método que passa vai ao responsável, que autoriza (ou não) a gravação.

**Parcial:** 9 de 10 anos de teste ([2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]). A decisão só sai com os 10.

## M1. Chuva (base: C3, a V1.8)

| Método | Mediana do |viés anual| (5 regiões) | Pior região | Dias de chuva: afastamento somado (p.p.) | r_anom mínimo |
|---|---|---|---|---|
| C0 | 7.83% | Centro-Oeste 8.9% | 9.58 | 0.888 |
| C3 | 4.26% | Centro-Oeste 6.7% | 12.51 | 0.909 |
| C3G | 4.14% | Centro-Oeste 6.8% | 8.77 | 0.906 |
| C3RG | 4.14% | Norte 6.1% | 8.77 | 0.889 |

- **C3G**: 1 ✅ (-0.13 p.p.) · 2 ✅ (dias de chuva +29.9%) · 3 ✅ · 4 Rx1day ✅, p99 pendente → ❌

- **C3RG**: 1 ✅ (-0.13 p.p.) · 2 ✅ (dias de chuva +29.9%) · 3 ❌ · 4 Rx1day ✅, p99 pendente → ❌

**M1: nenhum passou; o C3 (V1.8) fica (parcial).**

## M2. Radiação e ETo (base: V1.7)

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| C0 | +0.53 MJ / +3.4% | +0.44 MJ / +1.9% | +0.42 MJ / +1.7% | +0.12 MJ / -0.0% | +0.50 MJ / +0.1% | +0.45 MJ / +2.2% |
| R1 | +0.37 MJ / +2.7% | +0.25 MJ / +1.3% | +0.25 MJ / +1.1% | +0.13 MJ / +0.1% | +0.19 MJ / -1.0% | +0.29 MJ / +1.6% |

R1: radiação no Brasil +0.16 MJ (precisa ≥ 0,2) · ETo +0.61 p.p. (≥ 1) · pior região +0.01 MJ / +0.87 p.p. · r_anom +0.004 → **não passa; a V1.7 fica (parcial)**

## M3. Tmax, Tmin, UR, VPD e vento (base: V1.7)

| Variável | Base: viés Brasil | T2: viés Brasil | Pior região (piora) | r_anom (maior queda) | Passa? |
|---|---|---|---|---|---|
| tmax_C | +0.152 | +0.107 | -0.076 | +0.007 | ❌ |
| tmin_C | -0.024 | +0.017 | +0.006 | +0.033 | ❌ |
| RH | -0.075 | -0.621 | +0.490 | -0.001 | ❌ |
| vpd | +0.007 | +0.027 | +0.029 | +0.002 | ❌ |
| u2 | +0.070 | +0.031 | +0.013 | +0.067 | ❌ |

(parcial)
