# A3. Testemunhas físicas da água (GRACE e SMAP)

Protocolo `pesquisa/PROTOCOLO_AUDITORIA_PROFUNDA.md`, A3. Erro = RMSE da previsão da testemunha pela chuva de cada base (regressão linear; no período de treino, deixar-um-de-fora; no teste, fora da amostra). REF = mediana, ano a ano (ou mês a mês), das anomalias das referências F1, F2 e F3. A testemunha fica **com as referências** se o erro com o SAB crescer > 25% do treino ao teste e o da REF ≤ 10%; **com o SAB** no caso inverso; senão neutra.

- GRACE: `NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI`, 238 imagens, de 2002-04 a 2024-09
- SMAP: `NASA/SMAP/SPL3SMP_E/006` (soil_moisture_am), de 2015-03-31 a 2026-11-24
- acesso em 26/11/2026

## GRACE: variação anual do armazenamento × chuva do ano hidrológico

| Região | erro SAB treino → teste | erro REF treino → teste | testemunha |
|---|---|---|---|
| Norte | 9.3 → 8.9 cm | 9.5 → 5.0 cm | neutra |
| Nordeste | 8.6 → 6.0 cm | 9.5 → 2.0 cm | neutra |
| Centro-Oeste | 5.4 → 7.0 cm | 5.4 → 11.0 cm | neutra |
| Sudeste | 8.1 → 8.1 cm | 8.2 → 9.7 cm | neutra |
| Sul | 8.8 → 10.1 cm | 8.4 → 11.6 cm | neutra |
| Brasil | 5.9 → 4.4 cm | 6.1 → 4.3 cm | neutra |

## SMAP: anomalia mensal da umidade do solo 0–5 cm × chuva do mês e do anterior

| Região | erro SAB treino → teste | erro REF treino → teste | testemunha |
|---|---|---|---|
| Norte | 0.0138 → 0.0252 | 0.0140 → 0.0241 | neutra |
| Nordeste | 0.0140 → 0.0150 | 0.0143 → 0.0198 | com o SAB |
| Centro-Oeste | 0.0150 → 0.0266 | 0.0151 → 0.0264 | neutra |
| Sudeste | 0.0142 → 0.0196 | 0.0142 → 0.0210 | neutra |
| Sul | 0.0204 → 0.0220 | 0.0203 → 0.0222 | neutra |
| Brasil | 0.0093 → 0.0122 | 0.0097 → 0.0111 | neutra |

