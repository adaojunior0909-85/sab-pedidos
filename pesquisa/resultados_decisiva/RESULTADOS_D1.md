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
