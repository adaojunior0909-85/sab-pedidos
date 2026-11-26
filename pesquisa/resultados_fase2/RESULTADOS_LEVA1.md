# Fase 2, leva 1: M1 (garoa), M2-R1 (radiação) e M3-T2 (temperaturas, UR, vento)

Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (congelado no commit 9a12309 antes de rodar). Só leitura no Earth Engine. Nada é gravado: um método que passa vai ao responsável, que autoriza (ou não) a gravação.

## M1. Chuva (base: C3, a V1.8)

| Método | Mediana do |viés anual| (5 regiões) | Pior região | Dias de chuva: afastamento somado (p.p.) | r_anom mínimo |
|---|---|---|---|---|
| C0 | 8.39% | Centro-Oeste 9.8% | 9.54 | 0.891 |
| C3 | 4.28% | Centro-Oeste 5.7% | 12.56 | 0.891 |
| C3G | 4.31% | Centro-Oeste 5.8% | 8.23 | 0.889 |
| C3RG | 4.31% | Centro-Oeste 5.7% | 8.23 | 0.873 |

- **C3G**: 1 ✅ (+0.03 p.p.) · 2 ✅ (dias de chuva +34.5%) · 3 ✅ · 4 Rx1day ✅, p99 12.3% (C3 13.8%) → ✅

- **C3RG**: 1 ✅ (+0.03 p.p.) · 2 ✅ (dias de chuva +34.5%) · 3 ✅ · 4 Rx1day ✅, p99 12.4% (C3 13.8%) → ✅

**M1: troca para C3G (gravação só com autorização).**

## M2. Radiação e ETo (base: V1.7)

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| C0 | +0.55 MJ / +3.4% | +0.47 MJ / +2.2% | +0.41 MJ / +1.6% | +0.12 MJ / +0.0% | +0.48 MJ / +0.0% | +0.45 MJ / +2.2% |
| R1 | +0.32 MJ / +2.4% | +0.24 MJ / +1.4% | +0.21 MJ / +0.9% | +0.11 MJ / +0.1% | +0.15 MJ / -1.1% | +0.25 MJ / +1.4% |

R1: radiação no Brasil +0.21 MJ (precisa ≥ 0,2) · ETo +0.80 p.p. (≥ 1) · pior região -0.01 MJ / +1.07 p.p. · r_anom +0.025 → **não passa; a V1.7 fica**

## M3. Tmax, Tmin, UR, VPD e vento (base: V1.7)

| Variável | Base: viés Brasil | T2: viés Brasil | Pior região (piora) | r_anom (maior queda) | Passa? |
|---|---|---|---|---|---|
| tmax_C | +0.157 | +0.093 | -0.099 | +0.009 | ❌ |
| tmin_C | -0.034 | +0.010 | -0.011 | +0.035 | ❌ |
| RH | -0.113 | -0.516 | +0.261 | +0.019 | ❌ |
| vpd | +0.008 | +0.023 | +0.022 | +0.011 | ❌ |
| u2 | +0.067 | +0.025 | +0.010 | +0.052 | ❌ |

