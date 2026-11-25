# Parte B: 2026 contra o GLDAS-2.1 (NASA), com 2022–2024 como régua

Meses 1 a 10 de cada ano (GLDAS até 2026-11-16; SAB ERA5 até 2026-11-15). Em cada célula: a diferença SAB − GLDAS em 2026 e, entre colchetes, a faixa da mesma diferença em 2022–2024 (quando o SAB é o BR-DWGD). ⚠️ = 2026 fora da faixa por mais que a tolerância (regra fixada antes de rodar).

| Variável | Unid. | Tol. | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|---|---|
| Chuva | % | 5.0 | +11.90 [+9.7 a +15.9] | ⚠️ -10.83 [+11.6 a +18.6] | ⚠️ -7.31 [+3.9 a +14.2] | +0.35 [-7.4 a +5.2] | +4.62 [+0.8 a +4.0] | +4.62 [+8.0 a +12.4] |
| Tmax | °C | 0.5 | +0.66 [+0.1 a +1.0] | +0.30 [+0.2 a +0.5] | +0.56 [+0.4 a +0.8] | +1.38 [+1.1 a +1.3] | +0.88 [+0.7 a +0.9] | +0.67 [+0.4 a +0.9] |
| Tmin | °C | 0.5 | +0.71 [+0.6 a +0.8] | +0.52 [+0.3 a +0.5] | -0.47 [-0.2 a -0.1] | -0.18 [+0.0 a +0.1] | +0.51 [+0.4 a +0.5] | +0.34 [+0.3 a +0.4] |
| Umidade relativa | p.p. | 3.0 | +5.74 [+2.8 a +6.3] | +2.55 [+4.5 a +5.2] | +8.01 [+5.3 a +7.2] | +1.50 [+0.9 a +2.6] | +0.24 [-0.6 a +1.4] | +4.72 [+3.2 a +5.4] |
| Déficit de pressão de vapor | kPa | 0.1 | -0.30 [-0.3 a -0.2] | -0.13 [-0.2 a -0.2] | -0.36 [-0.3 a -0.2] | -0.05 [-0.1 a -0.0] | -0.05 [-0.1 a -0.0] | -0.24 [-0.3 a -0.2] |
| ETo | % | 5.0 | -47.52 [-51.6 a -45.0] | -50.71 [-54.6 a -53.4] | -51.21 [-53.9 a -49.8] | -49.40 [-51.8 a -47.8] | -49.65 [-48.5 a -45.2] | -49.27 [-52.6 a -48.6] |
| Radiação solar | MJ/m²/dia | 0.5 | -1.08 [-3.3 a -0.6] | ⚠️ +0.19 [-2.4 a -1.2] | -0.67 [-2.7 a -0.7] | -1.12 [-2.0 a -0.4] | -0.96 [-1.9 a -0.2] | -0.77 [-2.8 a -0.7] |
| Vento | m/s | 0.2 | +0.01 [-0.2 a -0.1] | ⚠️ -0.33 [-0.6 a -0.6] | -0.27 [-0.3 a -0.2] | -0.40 [-0.4 a -0.4] | -0.26 [-0.2 a -0.1] | -0.17 [-0.3 a -0.3] |
| ET real | % | 5.0 | -19.28 [-24.3 a -20.3] | -13.01 [-9.9 a -6.3] | -16.98 [-16.4 a -12.0] | -7.52 [-9.1 a -5.8] | -8.07 [-14.6 a -5.8] | -16.27 [-18.1 a -15.6] |
| Transpiração | % | 5.0 | -12.00 [-11.9 a -2.3] | ⚠️ -22.03 [-15.1 a -12.8] | -8.48 [-6.2 a -1.5] | +1.77 [-3.2 a +3.1] | +7.23 [+4.2 a +14.6] | -10.01 [-8.3 a -3.4] |
| Escoamento superficial | % | 5.0 | ⚠️ +351.70 [+223.6 a +322.6] | +407.25 [+330.8 a +402.3] | +86.32 [+49.0 a +231.7] | ⚠️ +194.20 [+73.2 a +131.5] | ⚠️ +146.37 [+39.2 a +65.4] | ⚠️ +271.38 [+176.3 a +235.3] |
| Escoamento subsuperficial | % | 5.0 | ⚠️ -75.69 [-82.8 a -81.0] | -92.89 [-91.6 a -89.9] | -90.30 [-89.0 a -81.6] | -82.19 [-86.1 a -70.5] | ⚠️ -60.41 [-79.4 a -77.3] | -77.45 [-83.1 a -82.2] |
| Temperatura do solo | °C | 0.5 | ⚠️ +0.60 [+1.5 a +1.7] | +1.59 [+1.6 a +1.8] | ⚠️ +1.24 [+1.9 a +2.2] | +1.21 [+1.6 a +1.9] | +1.14 [+1.5 a +1.6] | ⚠️ +1.01 [+1.7 a +1.8] |
| Temperatura da folha | °C | 0.5 | ⚠️ +0.03 [+1.0 a +1.1] | +1.05 [+1.1 a +1.3] | ⚠️ +0.73 [+1.4 a +1.6] | +0.75 [+1.2 a +1.4] | +0.62 [+1.0 a +1.1] | ⚠️ +0.47 [+1.2 a +1.2] |
| Umidade do solo 0-5 cm | m³/m³ | 0.02 | +0.02 [-0.0 a +0.0] | -0.05 [-0.1 a -0.0] | -0.05 [-0.0 a -0.0] | -0.05 [-0.1 a -0.0] | +0.00 [-0.0 a -0.0] | -0.02 [-0.0 a -0.0] |
| Umidade do solo 0-100 cm | m³/m³ | 0.02 | +0.03 [+0.0 a +0.0] | -0.01 [-0.0 a -0.0] | -0.02 [-0.0 a +0.0] | -0.02 [-0.0 a -0.0] | +0.03 [+0.0 a +0.0] | +0.01 [-0.0 a +0.0] |

**Suspeitas em 2026:** Chuva no Nordeste; Chuva no Centro-Oeste; Radiação solar no Nordeste; Vento no Nordeste; Transpiração no Nordeste; Escoamento superficial no Norte; Escoamento superficial no Sudeste; Escoamento superficial no Sul; Escoamento superficial no Brasil; Escoamento subsuperficial no Norte; Escoamento subsuperficial no Sul; Temperatura do solo no Norte; Temperatura do solo no Centro-Oeste; Temperatura do solo no Brasil; Temperatura da folha no Norte; Temperatura da folha no Centro-Oeste; Temperatura da folha no Brasil
