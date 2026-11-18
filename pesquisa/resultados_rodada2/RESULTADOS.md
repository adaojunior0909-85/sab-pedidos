# Resultados: previsão estendida de chuva e temperatura

Protocolo: `pesquisa/PROTOCOLO.md`. 989 pontos classe A. Treino 1982-2010; teste 2011 em diante. MSESS > 0 = melhor que a média histórica; acerto de tercil: 33% = acaso.

## 1. Quantas células têm previsão aprovada (5 regiões x 4 estações = 20 por linha)

| Variável | Alvo | Aprovadas | Métodos escolhidos nas aprovadas |
|---|---|---|---|
| Chuva (mm) | M2 (dias ~31-60) | 3 de 20 | ENS_raiz (3) |
| Chuva (mm) | M3 (dias ~61-90) | 2 de 20 | R2 (1), ENS_raiz (1) |
| Chuva (mm) | Q1 (dias ~16-31) | 2 de 20 | ENS_raiz (1), R2 (1) |
| Tmin (°C) | M2 (dias ~31-60) | 12 de 20 | R2 (4), P1 (3), ENS (3), C1 (1), E2t (1) |
| Tmin (°C) | M3 (dias ~61-90) | 11 de 20 | ENS (6), R2 (2), E1t (1), P1 (1), C1 (1) |
| Tmin (°C) | Q1 (dias ~16-31) | 13 de 20 | P1 (4), R2 (3), ENS (3), R1 (1), R1t (1), E2t (1) |
| Tmax (°C) | M2 (dias ~31-60) | 6 de 20 | R2t (2), R1 (2), ENS (2) |
| Tmax (°C) | M3 (dias ~61-90) | 4 de 20 | R1t (2), R2t (1), R1 (1) |
| Tmax (°C) | Q1 (dias ~16-31) | 8 de 20 | R2t (3), ENS (2), R2 (2), C1 (1) |

## 2. Paraná: método escolhido (pelo treino) e escore no teste

| Variável | Alvo | Estação | Método | MSESS (IC 95%) | Acerto tercil | RPSS | Produto |
|---|---|---|---|---|---|---|---|
| Chuva (mm) | M2 | DJF | C0 | +0.00 (+0.00 a +0.00) | 30% | +0.00 | sem sinal: média histórica |
| Chuva (mm) | M2 | JJA | R2_raiz | -0.04 (-0.17 a +0.05) | 31% | -0.06 | sem sinal: média histórica |
| Chuva (mm) | M2 | MAM | E2_raiz | +0.01 (-0.12 a +0.17) | 35% | -0.00 | sem sinal: média histórica |
| Chuva (mm) | M2 | SON | E2_raiz | +0.04 (-0.06 a +0.12) | 35% | +0.03 | sem sinal: média histórica |
| Chuva (mm) | M3 | DJF | R2_raiz | -0.08 (-0.20 a +0.05) | 30% | -0.06 | sem sinal: média histórica |
| Chuva (mm) | M3 | JJA | R2_raiz | -0.03 (-0.18 a +0.07) | 34% | -0.06 | sem sinal: média histórica |
| Chuva (mm) | M3 | MAM | E2_raiz | +0.00 (-0.07 a +0.11) | 34% | -0.01 | sem sinal: média histórica |
| Chuva (mm) | M3 | SON | E2_raiz | +0.04 (-0.06 a +0.12) | 36% | +0.01 | sem sinal: média histórica |
| Chuva (mm) | Q1 | DJF | C0 | +0.00 (+0.00 a +0.00) | 28% | +0.00 | sem sinal: média histórica |
| Chuva (mm) | Q1 | JJA | R1_raiz | -0.01 (-0.04 a +0.02) | 36% | -0.04 | sem sinal: média histórica |
| Chuva (mm) | Q1 | MAM | E2_raiz | +0.03 (-0.06 a +0.14) | 36% | +0.01 | sem sinal: média histórica |
| Chuva (mm) | Q1 | SON | R2_raiz | +0.01 (-0.08 a +0.08) | 37% | -0.03 | sem sinal: média histórica |
| Tmin (°C) | M2 | DJF | E2t | -0.06 (-0.35 a +0.15) | 43% | -0.01 | sem sinal: média histórica |
| Tmin (°C) | M2 | JJA | C1 | +0.18 (+0.09 a +0.24) | 41% | +0.14 | C1 |
| Tmin (°C) | M2 | MAM | E1t | +0.16 (-0.03 a +0.28) | 45% | +0.14 | sem sinal: média histórica |
| Tmin (°C) | M2 | SON | E2t | +0.25 (+0.05 a +0.42) | 51% | +0.20 | E2t |
| Tmin (°C) | M3 | DJF | E1t | -0.04 (-0.47 a +0.22) | 45% | -0.01 | sem sinal: média histórica |
| Tmin (°C) | M3 | JJA | E1t | +0.23 (+0.11 a +0.29) | 46% | +0.18 | E1t |
| Tmin (°C) | M3 | MAM | C1 | +0.17 (+0.06 a +0.25) | 43% | +0.16 | C1 |
| Tmin (°C) | M3 | SON | E2t | +0.12 (-0.05 a +0.29) | 48% | +0.12 | sem sinal: média histórica |
| Tmin (°C) | Q1 | DJF | ENSt | +0.04 (-0.12 a +0.18) | 44% | +0.04 | sem sinal: média histórica |
| Tmin (°C) | Q1 | JJA | R1t | +0.17 (+0.08 a +0.24) | 36% | +0.10 | R1t |
| Tmin (°C) | Q1 | MAM | E1t | +0.01 (-0.19 a +0.16) | 40% | -0.01 | sem sinal: média histórica |
| Tmin (°C) | Q1 | SON | E2t | +0.19 (+0.10 a +0.27) | 44% | +0.17 | E2t |
| Tmax (°C) | M2 | DJF | C1 | +0.15 (-0.10 a +0.36) | 51% | +0.08 | sem sinal: média histórica |
| Tmax (°C) | M2 | JJA | R2t | +0.16 (-0.09 a +0.34) | 46% | +0.14 | sem sinal: média histórica |
| Tmax (°C) | M2 | MAM | C1 | -0.00 (-0.46 a +0.29) | 45% | +0.00 | sem sinal: média histórica |
| Tmax (°C) | M2 | SON | ENSt | +0.03 (-0.36 a +0.24) | 44% | -0.05 | sem sinal: média histórica |
| Tmax (°C) | M3 | DJF | C1 | +0.07 (-0.44 a +0.34) | 48% | +0.02 | sem sinal: média histórica |
| Tmax (°C) | M3 | JJA | ENSt | +0.22 (-0.07 a +0.36) | 48% | +0.15 | sem sinal: média histórica |
| Tmax (°C) | M3 | MAM | P1t | -0.05 (-0.49 a +0.29) | 46% | +0.01 | sem sinal: média histórica |
| Tmax (°C) | M3 | SON | C1 | +0.03 (-0.40 a +0.30) | 47% | -0.01 | sem sinal: média histórica |
| Tmax (°C) | Q1 | DJF | R1t | +0.13 (-0.03 a +0.29) | 48% | +0.07 | sem sinal: média histórica |
| Tmax (°C) | Q1 | JJA | C1 | +0.14 (+0.02 a +0.23) | 42% | +0.08 | C1 |
| Tmax (°C) | Q1 | MAM | E1t | -0.12 (-0.47 a +0.11) | 38% | -0.07 | sem sinal: média histórica |
| Tmax (°C) | Q1 | SON | R2t | +0.15 (-0.03 a +0.28) | 43% | +0.06 | sem sinal: média histórica |

## 3. Cascavel (pixel): método escolhido (pelo treino) e escore no teste

| Variável | Alvo | Estação | Método | MSESS (IC 95%) | Acerto tercil | RPSS | Produto |
|---|---|---|---|---|---|---|---|
| Chuva (mm) | M2 | DJF | E1 | -0.22 (-0.41 a +0.01) | 42% | -0.10 | sem sinal: média histórica |
| Chuva (mm) | M2 | JJA | R2_raiz | -0.16 (-0.50 a +0.09) | 32% | -0.08 | sem sinal: média histórica |
| Chuva (mm) | M2 | MAM | R1 | -0.04 (-0.13 a +0.08) | 37% | -0.04 | sem sinal: média histórica |
| Chuva (mm) | M2 | SON | E2_raiz | +0.04 (-0.08 a +0.13) | 44% | +0.04 | sem sinal: média histórica |
| Chuva (mm) | M3 | DJF | E1 | -0.11 (-0.30 a +0.07) | 38% | -0.07 | sem sinal: média histórica |
| Chuva (mm) | M3 | JJA | R2_raiz | -0.12 (-0.43 a +0.03) | 37% | -0.14 | sem sinal: média histórica |
| Chuva (mm) | M3 | MAM | R1 | -0.04 (-0.10 a +0.11) | 32% | -0.01 | sem sinal: média histórica |
| Chuva (mm) | M3 | SON | E2_raiz | +0.03 (-0.11 a +0.14) | 45% | +0.03 | sem sinal: média histórica |
| Chuva (mm) | Q1 | DJF | P1 | -0.35 (-0.62 a -0.13) | 27% | -0.13 | sem sinal: média histórica |
| Chuva (mm) | Q1 | JJA | C0 | +0.00 (+0.00 a +0.00) | 41% | -0.03 | sem sinal: média histórica |
| Chuva (mm) | Q1 | MAM | R1_raiz | -0.02 (-0.11 a +0.06) | 46% | -0.03 | sem sinal: média histórica |
| Chuva (mm) | Q1 | SON | R2_raiz | +0.01 (-0.18 a +0.15) | 34% | -0.11 | sem sinal: média histórica |
| Tmin (°C) | M2 | DJF | C0 | +0.00 (+0.00 a +0.00) | 30% | -0.02 | sem sinal: média histórica |
| Tmin (°C) | M2 | JJA | C0 | +0.00 (+0.00 a +0.00) | 27% | -0.02 | sem sinal: média histórica |
| Tmin (°C) | M2 | MAM | E1 | -0.03 (-0.20 a +0.09) | 31% | -0.00 | sem sinal: média histórica |
| Tmin (°C) | M2 | SON | E2 | +0.12 (-0.10 a +0.30) | 30% | +0.08 | sem sinal: média histórica |
| Tmin (°C) | M3 | DJF | E1 | -0.10 (-0.34 a +0.05) | 34% | -0.04 | sem sinal: média histórica |
| Tmin (°C) | M3 | JJA | E1 | +0.06 (-0.01 a +0.12) | 22% | +0.03 | sem sinal: média histórica |
| Tmin (°C) | M3 | MAM | C0 | +0.00 (+0.00 a +0.00) | 28% | +0.05 | sem sinal: média histórica |
| Tmin (°C) | M3 | SON | E2 | +0.09 (-0.05 a +0.21) | 28% | +0.04 | sem sinal: média histórica |
| Tmin (°C) | Q1 | DJF | R2 | -0.01 (-0.17 a +0.13) | 33% | +0.00 | sem sinal: média histórica |
| Tmin (°C) | Q1 | JJA | C0 | +0.00 (+0.00 a +0.00) | 18% | -0.04 | sem sinal: média histórica |
| Tmin (°C) | Q1 | MAM | E1 | -0.11 (-0.29 a -0.00) | 37% | -0.10 | sem sinal: média histórica |
| Tmin (°C) | Q1 | SON | E1 | -0.01 (-0.17 a +0.15) | 39% | +0.04 | sem sinal: média histórica |
| Tmax (°C) | M2 | DJF | C1 | +0.08 (-0.17 a +0.32) | 50% | +0.13 | sem sinal: média histórica |
| Tmax (°C) | M2 | JJA | R2t | +0.12 (-0.18 a +0.33) | 39% | +0.08 | sem sinal: média histórica |
| Tmax (°C) | M2 | MAM | E1t | -0.10 (-0.40 a +0.11) | 37% | -0.06 | sem sinal: média histórica |
| Tmax (°C) | M2 | SON | P1t | -0.14 (-0.58 a +0.07) | 29% | -0.23 | sem sinal: média histórica |
| Tmax (°C) | M3 | DJF | E1t | -0.21 (-0.73 a +0.16) | 41% | -0.14 | sem sinal: média histórica |
| Tmax (°C) | M3 | JJA | ENSt | +0.18 (-0.14 a +0.32) | 44% | +0.08 | sem sinal: média histórica |
| Tmax (°C) | M3 | MAM | C1 | -0.03 (-0.29 a +0.20) | 49% | +0.01 | sem sinal: média histórica |
| Tmax (°C) | M3 | SON | C1 | -0.09 (-0.56 a +0.22) | 44% | -0.07 | sem sinal: média histórica |
| Tmax (°C) | Q1 | DJF | C1 | +0.11 (-0.07 a +0.28) | 44% | +0.01 | sem sinal: média histórica |
| Tmax (°C) | Q1 | JJA | C1 | +0.07 (-0.08 a +0.18) | 43% | +0.05 | sem sinal: média histórica |
| Tmax (°C) | Q1 | MAM | E1t | -0.21 (-0.51 a -0.02) | 37% | -0.18 | sem sinal: média histórica |
| Tmax (°C) | Q1 | SON | R2t | +0.11 (-0.08 a +0.25) | 44% | +0.03 | sem sinal: média histórica |

## 4. Média de cada método no Brasil (sem escolha; MSESS médio das 20 células, teste)

| Variável | Alvo | C0 | C1 | C1_raiz | E1 | E1_raiz | E1t | E1t_raiz | E2 | E2_raiz | E2t | E2t_raiz | ENS | ENS_raiz | ENSt | ENSt_raiz | P1 | P1_raiz | P1t | P1t_raiz | R1 | R1_raiz | R1t | R1t_raiz | R2 | R2_raiz | R2t | R2t_raiz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Chuva (mm) | Q1 | +0.00 | -0.03 | -0.01 | -0.04 | -0.04 | -0.07 | -0.05 | -0.02 | -0.02 | -0.05 | -0.03 | +0.02 | +0.01 | -0.02 | -0.00 | -0.05 | -0.04 | -0.08 | -0.05 | +0.01 | +0.01 | -0.02 | -0.01 | +0.02 | +0.02 | -0.02 | +0.00 |
| Chuva (mm) | M2 | +0.00 | -0.05 | -0.02 | -0.05 | -0.04 | -0.10 | -0.07 | -0.02 | -0.02 | -0.08 | -0.05 | +0.02 | +0.02 | -0.04 | -0.00 | -0.04 | -0.04 | -0.10 | -0.06 | +0.02 | +0.02 | -0.03 | -0.01 | +0.02 | +0.02 | -0.04 | -0.00 |
| Chuva (mm) | M3 | +0.00 | -0.06 | -0.03 | -0.05 | -0.05 | -0.11 | -0.08 | -0.02 | -0.02 | -0.08 | -0.05 | +0.01 | +0.01 | -0.05 | -0.02 | -0.06 | -0.06 | -0.12 | -0.08 | +0.00 | +0.01 | -0.05 | -0.03 | +0.01 | +0.01 | -0.06 | -0.02 |
| Tmax (°C) | Q1 | +0.00 | +0.08 | +nan | -0.03 | +nan | +0.08 | +nan | -0.01 | +nan | +0.11 | +nan | +0.20 | +nan | +0.14 | +nan | +0.19 | +nan | +0.09 | +nan | +0.21 | +nan | +0.12 | +nan | +0.26 | +nan | +0.14 | +nan |
| Tmax (°C) | M2 | +0.00 | +0.09 | +nan | -0.02 | +nan | +0.12 | +nan | -0.01 | +nan | +0.13 | +nan | +0.20 | +nan | +0.14 | +nan | +0.18 | +nan | +0.09 | +nan | +0.24 | +nan | +0.14 | +nan | +0.27 | +nan | +0.13 | +nan |
| Tmax (°C) | M3 | +0.00 | +0.09 | +nan | -0.01 | +nan | +0.12 | +nan | -0.01 | +nan | +0.14 | +nan | +0.16 | +nan | +0.13 | +nan | +0.11 | +nan | +0.07 | +nan | +0.20 | +nan | +0.13 | +nan | +0.23 | +nan | +0.13 | +nan |
| Tmin (°C) | Q1 | +0.00 | +0.11 | +nan | -0.03 | +nan | +0.13 | +nan | -0.00 | +nan | +0.16 | +nan | +0.28 | +nan | +0.18 | +nan | +0.30 | +nan | +0.13 | +nan | +0.23 | +nan | +0.17 | +nan | +0.34 | +nan | +0.17 | +nan |
| Tmin (°C) | M2 | +0.00 | +0.13 | +nan | -0.02 | +nan | +0.16 | +nan | +0.00 | +nan | +0.18 | +nan | +0.29 | +nan | +0.19 | +nan | +0.32 | +nan | +0.15 | +nan | +0.25 | +nan | +0.20 | +nan | +0.36 | +nan | +0.15 | +nan |
| Tmin (°C) | M3 | +0.00 | +0.13 | +nan | -0.02 | +nan | +0.16 | +nan | +0.00 | +nan | +0.18 | +nan | +0.25 | +nan | +0.17 | +nan | +0.25 | +nan | +0.13 | +nan | +0.22 | +nan | +0.18 | +nan | +0.31 | +nan | +0.15 | +nan |

## Parâmetros escolhidos no treino

- R1 mm: lambda 100.0
- R2 mm: lambda 10000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 10000.0
- R1 raiz: lambda 100.0
- R2 raiz: lambda 10000.0
- R1t raiz: lambda 100.0
- R2t raiz: lambda 10000.0
- R1 mm: lambda 100.0
- R2 mm: lambda 10000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 10000.0
- R1 raiz: lambda 100.0
- R2 raiz: lambda 10000.0
- R1t raiz: lambda 100.0
- R2t raiz: lambda 10000.0
- R1 mm: lambda 100.0
- R2 mm: lambda 10000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 10000.0
- R1 raiz: lambda 100.0
- R2 raiz: lambda 10000.0
- R1t raiz: lambda 100.0
- R2t raiz: lambda 10000.0
- R1 mm: lambda 30.0
- R2 mm: lambda 10000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 10000.0
- R1 mm: lambda 30.0
- R2 mm: lambda 10000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 10000.0
- R1 mm: lambda 30.0
- R2 mm: lambda 10000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 10000.0
- R1 mm: lambda 100.0
- R2 mm: lambda 10000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 10000.0
- R1 mm: lambda 100.0
- R2 mm: lambda 10000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 100000.0
- R1 mm: lambda 100.0
- R2 mm: lambda 10000.0
- R1t mm: lambda 100.0
- R2t mm: lambda 100000.0
