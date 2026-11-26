# Fase 2, leva 1: M1 (garoa), M2-R1 (radiação) e M3-T2 (temperaturas, UR, vento)

Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (congelado no commit 9a12309 antes de rodar). Só leitura no Earth Engine. Nada é gravado: um método que passa vai ao responsável, que autoriza (ou não) a gravação.

**Parcial:** 3 de 10 anos de teste ([2016, 2017, 2018]). A decisão só sai com os 10.

## M1. Chuva (base: C3, a V1.8)

| Método | Mediana do |viés anual| (5 regiões) | Pior região | Dias de chuva: afastamento somado (p.p.) | r_anom mínimo |
|---|---|---|---|---|
| C0 | 5.49% | Sul 9.8% | 19.96 | 0.936 |
| C3 | 4.11% | Centro-Oeste 6.7% | 21.99 | 0.928 |
| C3G | 4.36% | Centro-Oeste 6.8% | 3.45 | 0.927 |
| C3RG | 4.78% | Centro-Oeste 6.0% | 3.45 | 0.929 |

- **C3G**: 1 ✅ (+0.25 p.p.) · 2 ✅ (dias de chuva +84.3%) · 3 ✅ · 4 Rx1day ✅, p99 pendente → ❌

- **C3RG**: 1 ❌ (+0.67 p.p.) · 2 ✅ (dias de chuva +84.3%) · 3 ✅ · 4 Rx1day ✅, p99 pendente → ❌

**M1: nenhum passou; o C3 (V1.8) fica (parcial).**

## M2. Radiação e ETo (base: V1.7)

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|
| C0 | +0.05 MJ / +0.1% | +0.16 MJ / -0.6% | +0.16 MJ / -0.1% | -0.11 MJ / -1.3% | +0.33 MJ / -1.1% | +0.10 MJ / -0.3% |
| R1 | +0.13 MJ / +0.5% | +0.16 MJ / -0.6% | +0.31 MJ / +0.5% | +0.05 MJ / -0.7% | +0.22 MJ / -1.5% | +0.17 MJ / -0.0% |

R1: radiação no Brasil -0.07 MJ (precisa ≥ 0,2) · ETo +0.30 p.p. (≥ 1) · pior região +0.15 MJ / +0.47 p.p. · r_anom +0.014 → **não passa; a V1.7 fica (parcial)**

## M3. Tmax, Tmin, UR, VPD e vento (base: V1.7)

| Variável | Base: viés Brasil | T2: viés Brasil | Pior região (piora) | r_anom (maior queda) | Passa? |
|---|---|---|---|---|---|
| tmax_C | +0.033 | +0.071 | +0.034 | +0.006 | ❌ |
| tmin_C | +0.009 | +0.073 | +0.063 | +0.048 | ❌ |
| RH | +1.146 | +0.169 | +0.152 | +0.026 | ❌ |
| vpd | -0.043 | -0.003 | +0.003 | +0.014 | ✅ |
| u2 | +0.033 | +0.007 | +0.004 | +0.061 | ❌ |

(parcial)
