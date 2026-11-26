# Fase 2, leva 1: M1 (garoa), M2-R1 (radiação) e M3-T2 (temperaturas, UR, vento)

Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (congelado no commit 9a12309 antes de rodar). Só leitura no Earth Engine. Nada é gravado: um método que passa vai ao responsável, que autoriza (ou não) a gravação.

**Parcial:** 6 de 10 anos de teste ([2016, 2017, 2018, 2019, 2020, 2021]). A decisão só sai com os 10.

## M1. Chuva (base: C3, a V1.8)

| Método | Mediana do |viés anual| (5 regiões) | Pior região | Dias de chuva: afastamento somado (p.p.) | r_anom mínimo |
|---|---|---|---|---|
| C0 | 6.25% | Sul 8.3% | 13.82 | 0.882 |
| C3 | 4.19% | Centro-Oeste 6.8% | 16.06 | 0.888 |
| C3G | 3.87% | Centro-Oeste 6.9% | 6.69 | 0.883 |
| C3RG | 3.82% | Centro-Oeste 6.8% | 6.69 | 0.875 |

- **C3G**: 1 ✅ (-0.32 p.p.) · 2 ✅ (dias de chuva +58.4%) · 3 ✅ · 4 Rx1day ✅, p99 pendente → ❌

- **C3RG**: 1 ✅ (-0.37 p.p.) · 2 ✅ (dias de chuva +58.4%) · 3 ✅ · 4 Rx1day ✅, p99 pendente → ❌

**M1: nenhum passou; o C3 (V1.8) fica (parcial).**

## M2. Radiação e ETo (base: V1.7)

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| C0 | +0.28 MJ / +1.5% | +0.33 MJ / +0.9% | +0.36 MJ / +1.2% | +0.08 MJ / -0.3% | +0.45 MJ / -0.3% | +0.29 MJ / +1.0% |
| R1 | +0.27 MJ / +1.5% | +0.26 MJ / +0.7% | +0.33 MJ / +1.1% | +0.19 MJ / +0.1% | +0.23 MJ / -1.1% | +0.27 MJ / +0.9% |

R1: radiação no Brasil +0.02 MJ (precisa ≥ 0,2) · ETo +0.07 p.p. (≥ 1) · pior região +0.11 MJ / +0.75 p.p. · r_anom +0.003 → **não passa; a V1.7 fica (parcial)**

## M3. Tmax, Tmin, UR, VPD e vento (base: V1.7)

| Variável | Base: viés Brasil | T2: viés Brasil | Pior região (piora) | r_anom (maior queda) | Passa? |
|---|---|---|---|---|---|
| tmax_C | +0.082 | +0.082 | -0.019 | +0.009 | ❌ |
| tmin_C | -0.029 | +0.004 | +0.020 | +0.060 | ❌ |
| RH | +0.397 | -0.542 | +0.874 | +0.006 | ❌ |
| vpd | -0.014 | +0.023 | +0.024 | +0.005 | ❌ |
| u2 | +0.050 | +0.019 | +0.016 | +0.071 | ❌ |

(parcial)
