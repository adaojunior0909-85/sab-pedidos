# Fase 2, M1-C3R: a razão do C3 só onde o viés é consistente

Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (congelado no commit 9a12309 antes de rodar). Sem Earth Engine: os dados da fase 1. Base de comparação: o C3 (a V1.8).

Razão aplicada em 312 de 600 combinações ano-alvo × mês × região (52%). Pesos do Brasil (área): Norte 0.443, Nordeste 0.180, Centro-Oeste 0.192, Sudeste 0.113, Sul 0.072 (conferência no C3: erro máx. 0.00%).

| Método | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Mediana das 5 |
|---|---|---|---|---|---|---|
| C0 | 6.8% (r 0.89) | 8.7% (r 0.98) | 9.8% (r 0.93) | 6.3% (r 0.98) | 8.4% (r 0.96) | 8.39% |
| C3 | 5.5% (r 0.89) | 4.3% (r 0.98) | 5.7% (r 0.93) | 4.0% (r 0.98) | 2.6% (r 0.95) | 4.28% |
| C3R | 5.1% (r 0.87) | 5.3% (r 0.98) | 5.7% (r 0.93) | 3.8% (r 0.97) | 4.2% (r 0.95) | 5.09% |

| Método | Dias de chuva: afastamento somado (p.p.) | p99 (1.500 pixels) |
|---|---|---|
| C0 | 9.54 | 16.8% |
| C3 | 12.56 | 13.8% |
| C3R | 12.00 | 14.1% |

## Regra (contra o C3)

1. mediana não piora > 0,5 p.p.: ❌ (+0.80 p.p.)
2. dias de chuva −20% (+4.5%) ou pior região (Centro-Oeste) −2 p.p. (+0.09 p.p.): ❌
3. r_anomalias não cai > 0,02: ❌ (maior queda +0.022)
4. Rx1day e p99 não crescem > 5%: ✅

**M1-C3R: não passa; o C3 (V1.8) fica.**

## Só relato: 2026 × CHIRPS (jan–set, viés do total, %)

| Região | 2024 (régua) | 2026 C0 (V1.7) | 2026 C3 (V1.8) | 2026 C3R |
|---|---|---|---|---|
| Norte | +2.4 | -1.3 | +7.1 | +6.0 |
| Nordeste | +6.6 | -15.9 | -4.1 | -4.1 |
| Centro-Oeste | -1.4 | -21.3 | -10.0 | -10.0 |
| Sudeste | -1.1 | -2.9 | +5.6 | +5.3 |
| Sul | +3.8 | +4.4 | +15.5 | +11.6 |
