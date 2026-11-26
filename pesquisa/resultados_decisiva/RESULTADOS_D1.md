# D1. Pluviômetros estáveis da ANA (2010–2024) como verdade de chão

Protocolo `pesquisa/PROTOCOLO_ANALISE_DECISIVA.md`. Salto = (base ÷ posto) em 2020–24 contra 2010–19, nos mesmos meses; S = mediana dos postos (IC 95% por reamostragem). **DADOS** = S_BR ≥ +4% (IC > 0) e ≥ 2 famílias com |S| ≤ 3%; **CLIMA** = |S_BR| ≤ 3% e ≥ 2 famílias com S ≤ −4% (IC < 0).

Teste sintético (antes dos dados reais): grade com salto inventado → DADOS (a grade erra); chuva real inventada → CLIMA (as referências erram). **PASSOU**

Conta em dobro: 7727 saltos posto × base refeitos por outra implementação; maior diferença 6.8e-14. **OK**

## Resultado

| Região | Postos | BR-DWGD | CHIRPS (F3) | ERA5-Land (F5) | IMERG (F1) | PERSIANN (F1) | TerraClimate (F2) | Decisão |
|---|---|---|---|---|---|---|---|---|
| Norte | 116 | +2.5% [+0.8; +4.3] | -6.3% [-10.0; -2.6] | -7.5% [-10.6; -5.8] | -11.6% [-13.8; -7.7] | -11.3% [-15.1; -9.0] | -12.8% [-15.7; -10.2] | **CLIMA (as referências erram)** |
| Nordeste | 533 | -0.1% [-1.0; +0.9] | -12.9% [-14.6; -12.0] | -10.3% [-11.9; -8.4] | -19.0% [-20.2; -18.0] | -17.0% [-18.3; -15.8] | -12.0% [-14.5; -9.7] | **CLIMA (as referências erram)** |
| Centro-Oeste | 130 | -2.0% [-4.1; +0.2] | -5.1% [-6.9; -3.2] | -14.7% [-15.9; -12.4] | -7.1% [-8.9; -5.3] | -7.3% [-11.0; -4.9] | -18.6% [-19.7; -14.3] | **CLIMA (as referências erram)** |
| Sudeste | 264 | -3.1% [-4.0; -2.1] | -9.3% [-10.8; -7.9] | -2.7% [-4.8; -1.4] | -4.0% [-5.8; -3.1] | +0.5% [-1.3; +2.0] | -6.3% [-8.3; -5.2] | **inconclusivo** |
| Sul | 236 | +0.1% [-0.9; +1.1] | -3.7% [-5.4; -2.3] | -4.3% [-5.1; -3.1] | -5.3% [-6.3; -4.2] | -3.6% [-5.3; -1.8] | -9.5% [-10.6; -8.0] | **CLIMA (as referências erram)** |
| Brasil | 1279 | -0.6% [-1.1; -0.0] | -9.2% [-10.0; -8.5] | -7.1% [-7.7; -6.1] | -10.4% [-11.3; -9.7] | -8.0% [-8.9; -7.0] | -10.6% [-11.2; -9.6] | **CLIMA (as referências erram)** |

## Sensibilidade (relatada)

- base 2015–2019: Norte CLIMA (as referências erram) (BR +1.8%); Nordeste CLIMA (as referências erram) (BR -0.3%); Centro-Oeste CLIMA (as referências erram) (BR -1.6%); Sudeste CLIMA (as referências erram) (BR -1.8%); Sul inconclusivo (BR +1.3%); Brasil CLIMA (as referências erram) (BR -0.2%)
- só postos com todos os meses consistidos: Norte inconclusivo (< 30 postos) (0 postos); Nordeste inconclusivo (< 30 postos) (0 postos); Centro-Oeste inconclusivo (< 30 postos) (0 postos); Sudeste inconclusivo (< 30 postos) (0 postos); Sul inconclusivo (< 30 postos) (0 postos); Brasil inconclusivo (< 30 postos) (0 postos)

## Ano a ano (relato): mediana dos postos de (base ÷ posto) relativa à média de 2010–2019 do próprio posto, Brasil

| Ano | br | chirps | era5 | imerg | persiann | terraclimate | chuva dos postos (mediana, mm) |
|---|---|---|---|---|---|---|---|
| 2010 | -0.0% | -6.3% | +0.8% | +0.4% | +3.1% | +2.3% | 1148 |
| 2011 | -0.1% | -6.2% | +0.1% | -1.3% | +1.3% | -1.4% | 1400 |
| 2012 | -0.7% | -0.3% | -3.8% | -2.5% | -0.5% | +2.2% | 1035 |
| 2013 | -0.3% | -1.9% | -2.4% | -1.4% | +3.4% | -7.0% | 1304 |
| 2014 | -0.6% | +1.9% | -3.5% | +2.5% | +1.8% | +7.4% | 1014 |
| 2015 | -0.8% | +5.3% | -0.9% | +1.0% | +2.1% | +1.5% | 988 |
| 2016 | -1.0% | -3.0% | +3.3% | -3.2% | -23.0% | -4.7% | 1150 |
| 2017 | -1.0% | -1.6% | -0.1% | -2.1% | +2.7% | +0.8% | 1129 |
| 2018 | -1.0% | -1.7% | -3.3% | -5.0% | -1.1% | -5.6% | 1271 |
| 2019 | -1.0% | -0.4% | -3.5% | -1.9% | -2.5% | -11.0% | 1118 |
| 2020 | -1.0% | -8.9% | -3.5% | -7.5% | -8.3% | -9.1% | 1240 |
| 2021 | -1.1% | -9.2% | -8.9% | -9.1% | -6.6% | -13.0% | 1220 |
| 2022 | -1.1% | -10.7% | -8.6% | -12.6% | -8.5% | -10.7% | 1360 |
| 2023 | -1.3% | -8.7% | -12.8% | -15.4% | -13.1% | -13.9% | 1154 |
| 2024 | -2.1% | -11.8% | -8.1% | -14.6% | -11.8% | -11.6% | 1208 |

Conferência do nível dos dados: todos os meses usados são do nível 1 (bruto) em todos os anos (a ANA ainda não consistiu 2010–2024 nesses postos), então não há troca de dado consistido por bruto no meio da série.

