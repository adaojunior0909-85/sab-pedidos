# Conferência final do SAB (1961 até a previsão)

Atualizado em 25/11/2026 04:43 (Brasília) pela fila automática (`rotinas/conferencia/fila.py`). Ainda há tarefas na fila.

| Tarefa | Situação | Tentativas | Quando | Resultado |
|---|---|---|---|---|
| 2026 (ERA5 calibrado) contra CHIRPS (chuva) e MODIS (calor) | ✅ pronta | 1 | 25/11 03:28 | pesquisa/resultados_2026/RESULTADOS.md |
| Umidade do solo, temperatura da folha e do solo, ET real contra satélites (2016-2021) | ✅ pronta | 1 | 25/11 03:33 | pesquisa/resultados_solo_folha/RESULTADOS.md |
| Escoamento x vazão do CAMELS-BR: extração 1981-2018 (512 bacias) | ✅ pronta | 1 | 25/11 03:36 |  |
| Escoamento x CAMELS-BR: métricas e decisão do protocolo | ✅ pronta | 1 | 25/11 03:36 | pesquisa/resultados_escoamento/RESULTADOS.md |
| As 16 variáveis: o método de 2026 aplicado a 2021-2025 (contra o BR-DWGD) | ✅ pronta | 1 | 25/11 04:43 | pesquisa/resultados_metodo_2026/RESULTADOS_A.md |
| As 16 variáveis de 2026 contra o GLDAS-2.1 (NASA), régua 2022-2024 | ⏳ na fila | 0 |  | pesquisa/resultados_metodo_2026/RESULTADOS_B.md |
| K26 rodada 7 (1981-1990) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada7/ |
| K26 rodada 1 (2026 inteiro (inclui os dias de previsão GFS)) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada1/ |
| K26 rodada 2 (2026: Rs = 0 cru do ERA5 e escoamento) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada2/ |
| K26 rodada 3 (2026: vento) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada3/ |
| K26 rodada 4 (2026: umidade do solo) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada4/ |
| K26 rodada 5 (1961-1970) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada5/ |
| K26 rodada 6 (1971-1980) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada6/ |
| K26 rodada 8 (1991-2000) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada8/ |
| K26 rodada 9 (2001-2010) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada9/ |
| K26 rodada 10 (2011-2020) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada10/ |
| K26 rodada 11 (2021-2025) | ⏳ na fila | 0 |  | rotinas/resultados/k26_rodada11/ |

O LOG de cada tarefa fica em `rotinas/conferencia/logs/<tarefa>.txt`. ❌ = me mande esse LOG.

---

## 2026 (ERA5 calibrado) contra CHIRPS (chuva) e MODIS (calor)

(cópia de `pesquisa/resultados_2026/RESULTADOS.md`)

### 2026 (ERA5 calibrado) contra referências independentes do ERA5

Gerado com: CHIRPS (pêntadas) até 2026-09-26, MODIS até 2026-11-09, SAB ERA5 até 2026-11-15. A régua é 2024, quando o SAB é o BR-DWGD (observado): 2026 está bom se concordar com os satélites tanto quanto 2024 concorda.

## Chuva mensal: SAB x CHIRPS

Meses 1 a 9; viés do TOTAL do período (os meses secos não pesam mais que os chuvosos).

| Ano | Região | Total SAB (mm) | Total CHIRPS (mm) | Viés do SAB (%) | Correlação espacial média (Brasil) |
|---|---|---|---|---|---|
| 2026 | Norte | 1629 | 1649 | -1.2 | 0.83 |
| 2026 | Nordeste | 633 | 749 | -15.6 | 0.83 |
| 2026 | Centro-Oeste | 840 | 1068 | -21.3 | 0.83 |
| 2026 | Sudeste | 885 | 911 | -2.9 | 0.83 |
| 2026 | Sul | 1252 | 1202 | +4.1 | 0.83 |
| 2026 | Brasil | 1187 | 1260 | -5.8 | 0.83 |
| 2024 | Norte | 1589 | 1552 | +2.4 | 0.86 |
| 2024 | Nordeste | 877 | 823 | +6.6 | 0.86 |
| 2024 | Centro-Oeste | 850 | 862 | -1.4 | 0.86 |
| 2024 | Sudeste | 676 | 683 | -1.1 | 0.86 |
| 2024 | Sul | 1377 | 1327 | +3.8 | 0.86 |
| 2024 | Brasil | 1201 | 1174 | +2.3 | 0.86 |

## Calor: anomalia da Tmax do SAB x anomalia da temperatura de superfície do MODIS
Atenção: o Terra (MODIS) saiu da órbita fixa em 2022 e passa cada vez mais cedo, então a temperatura de superfície dele esfria artificialmente ano a ano; o NÍVEL da anomalia do MODIS não serve. O que vale é a CORRELAÇÃO ESPACIAL (o desenho do calor no mapa), comparada à de 2024.


| Mês | Região | Anomalia Tmax SAB (°C) | Anomalia LST MODIS (°C) | Correlação espacial (Brasil) |
|---|---|---|---|---|
| 2024-09 | Brasil | +1.78 | -0.62 | 0.33 |
| 2024-09 | Centro-Oeste | +2.22 | -0.84 | 0.33 |
| 2024-09 | Nordeste | +0.73 | -2.42 | 0.33 |
| 2024-09 | Norte | +1.65 | +0.27 | 0.33 |
| 2024-09 | Sudeste | +2.61 | -0.68 | 0.33 |
| 2024-09 | Sul | +2.65 | -0.98 | 0.33 |
| 2024-10 | Brasil | +1.20 | -1.13 | 0.38 |
| 2024-10 | Centro-Oeste | +1.22 | -1.61 | 0.38 |
| 2024-10 | Nordeste | +0.91 | -2.65 | 0.38 |
| 2024-10 | Norte | +1.43 | -0.07 | 0.38 |
| 2024-10 | Sudeste | +0.75 | -2.18 | 0.38 |
| 2024-10 | Sul | +1.21 | -1.00 | 0.38 |
| 2026-09 | Brasil | +0.91 | -4.77 | 0.61 |
| 2026-09 | Centro-Oeste | +0.08 | -6.20 | 0.61 |
| 2026-09 | Nordeste | +1.46 | -5.60 | 0.61 |
| 2026-09 | Norte | +1.77 | -2.83 | 0.61 |
| 2026-09 | Sudeste | -0.31 | -7.02 | 0.61 |
| 2026-09 | Sul | -1.59 | -7.27 | 0.61 |
| 2026-10 | Brasil | +1.09 | -4.66 | 0.70 |
| 2026-10 | Centro-Oeste | +0.05 | -5.64 | 0.70 |
| 2026-10 | Nordeste | +1.51 | -6.35 | 0.70 |
| 2026-10 | Norte | +2.25 | -2.15 | 0.70 |
| 2026-10 | Sudeste | -0.15 | -7.80 | 0.70 |
| 2026-10 | Sul | -2.42 | -8.34 | 0.70 |

---

## Umidade do solo, temperatura da folha e do solo, ET real contra satélites (2016-2021)

(cópia de `pesquisa/resultados_solo_folha/RESULTADOS.md`)

### Solo, folha e ET real do SAB contra satélites independentes (2016–2021)

Correlação das anomalias mensais (ciclo do ano retirado), por região. Regra fixada antes de rodar: mediana das 5 regiões r ≥ 0,6 mantém; 0,3–0,6 mantém como índice com aviso; < 0,3 recomendo retirar.

| Variável | Referência | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil | Mediana (5 regiões) | Viés médio (SAB − ref.) | Recomendação |
|---|---|---|---|---|---|---|---|---|---|
| umidade_0_5cm | SMAP | 0.42 | 0.93 | 0.78 | 0.89 | 0.93 | 0.61 | 0.89 | -0.02 | mantém |
| tfolha_C | LST dia | 0.80 | 0.81 | 0.71 | 0.80 | 0.53 | 0.70 | 0.80 | -7.02 | mantém |
| tsolo_C | LST noite | 0.81 | 0.74 | 0.59 | 0.80 | 0.81 | 0.76 | 0.80 | +6.75 | mantém |
| et_real | MOD16 | 0.06 | 0.67 | 0.52 | 0.47 | 0.46 | 0.25 | 0.47 | -8.07 | mantém como índice (aviso) |

---

## Escoamento x CAMELS-BR: métricas e decisão do protocolo

(cópia de `pesquisa/resultados_escoamento/RESULTADOS.md`)

### Escoamento do SAB contra a vazão observada (CAMELS-BR), 1981–2018

Protocolo fixado antes de rodar: `pesquisa/PROTOCOLO_ESCOAMENTO_CAMELS.md`. Total mensal na bacia; bacias com pelo menos 24 meses válidos. Fonte da vazão: CAMELS-BR v1.1 (Chagas et al., 2020, doi:10.5281/zenodo.3964745, CC-BY-4.0).

## Brasil (mediana entre as bacias)

| Método | Período | Bacias | KGE | Viés (%) | |Viés| (%) | r |
|---|---|---|---|---|---|---|
| M0 atual (entregue) | 1981-2018 | 512 | 0.31 | -35 | 38 | 0.73 |
| M1 gravado | 1981-2018 | 512 | 0.30 | -30 | 38 | 0.71 |
| M2 ERA5-Land puro | 1981-2018 | 512 | 0.27 | -10 | 21 | 0.80 |
| M3 coef. ERA5 × chuva SAB | 1981-2018 | 512 | 0.30 | -15 | 20 | 0.86 |
| M0 atual (entregue) | 1981-1999 | 512 | 0.28 | -31 | 36 | 0.72 |
| M1 gravado | 1981-1999 | 512 | 0.28 | -27 | 37 | 0.71 |
| M2 ERA5-Land puro | 1981-1999 | 512 | 0.15 | -3 | 19 | 0.80 |
| M3 coef. ERA5 × chuva SAB | 1981-1999 | 512 | 0.22 | -12 | 18 | 0.87 |
| M0 atual (entregue) | 2000-2018 | 512 | 0.31 | -40 | 42 | 0.75 |
| M1 gravado | 2000-2018 | 512 | 0.30 | -35 | 40 | 0.73 |
| M2 ERA5-Land puro | 2000-2018 | 512 | 0.36 | -17 | 25 | 0.80 |
| M3 coef. ERA5 × chuva SAB | 2000-2018 | 512 | 0.39 | -18 | 24 | 0.87 |

## Por região hidrográfica (1981–2018, mediana)

| Região | Bacias | KGE M0 | Viés M0 (%) | KGE M1 | KGE M2 | KGE M3 | Viés M3 (%) |
|---|---|---|---|---|---|---|---|
| amazon | 22 | 0.33 | -46 | 0.42 | 0.66 | 0.70 | -2 |
| e_atlantic | 49 | 0.01 | -55 | -0.03 | 0.11 | 0.19 | -66 |
| eastern_ne_atlantic | 6 | -0.00 | -74 | 0.10 | -0.31 | -0.18 | -86 |
| paraguay | 2 | 0.06 | -70 | 0.47 | 0.56 | 0.54 | -32 |
| parana | 145 | 0.35 | -35 | 0.35 | 0.26 | 0.28 | -18 |
| parnaiba | 9 | -0.89 | +4 | -2.86 | -2.02 | -1.39 | +46 |
| s_atlantic | 41 | 0.48 | -30 | 0.49 | 0.63 | 0.70 | -15 |
| sao_francisco | 54 | -0.20 | -22 | -0.57 | 0.20 | 0.20 | -14 |
| se_atlantic | 83 | 0.34 | -38 | 0.35 | 0.13 | 0.19 | -10 |
| tocantins-araguaia | 33 | 0.20 | -52 | -0.04 | 0.05 | 0.02 | -2 |
| uruguay | 41 | 0.55 | -27 | 0.56 | 0.69 | 0.73 | -21 |
| western_ne_atlantic | 27 | 0.03 | +27 | -0.56 | -2.28 | -2.57 | +130 |

## Regra de decisão (as quatro condições)

| Candidato | 1. KGE +0,10 (todo) | 2. melhora em ≥ 60% | 3. vale nas duas metades | 4. |viés| não piora | Passa? |
|---|---|---|---|---|---|
| M1 gravado | ❌ (-0.01) | ❌ (57%) | ❌ | ✅ | não |
| M2 ERA5-Land puro | ❌ (-0.04) | ❌ (52%) | ❌ | ✅ | não |
| M3 coef. ERA5 × chuva SAB | ❌ (-0.01) | ❌ (58%) | ❌ | ✅ | não |

## Decisão

Nenhum candidato passou nas quatro condições: **o M0 fica**. O dicionário ganha o aviso quantitativo (KGE e viés do M0 por região, tabela acima).

---

## As 16 variáveis: o método de 2026 aplicado a 2021-2025 (contra o BR-DWGD)

(cópia de `pesquisa/resultados_metodo_2026/RESULTADOS_A.md`)

### Parte A: o método de 2026 aplicado a 2021–2025 (anos com BR-DWGD)

Erro do método = rota ERA5 do motor V1.7 menos o que o banco entrega no mesmo mês (somas: % do total; médias: diferença na unidade). Em cada célula: o erro dos 5 anos juntos e, entre colchetes, o menor e o maior erro de um ano só. **Nas 8 primeiras linhas a referência é a observação (BR-DWGD)**; nas outras, o próprio ERA5 do histórico (mede só a emenda).

| Variável | Unid. | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Brasil |
|---|---|---|---|---|---|---|---|
| Chuva | % | -9.18 [-15.2 a -5.6] | -12.40 [-16.9 a -9.2] | -11.90 [-16.1 a -7.8] | -6.75 [-12.8 a -3.0] | -7.53 [-12.1 a +0.2] | -9.64 [-13.3 a -7.2] |
| Tmax | °C | +0.41 [+0.2 a +0.7] | -0.10 [-0.2 a +0.0] | +0.24 [+0.1 a +0.3] | +0.17 [+0.1 a +0.2] | +0.13 [-0.1 a +0.3] | +0.24 [+0.1 a +0.4] |
| Tmin | °C | -0.05 [-0.3 a +0.2] | -0.08 [-0.1 a -0.0] | -0.13 [-0.2 a -0.1] | -0.05 [-0.1 a -0.0] | -0.02 [-0.1 a +0.0] | -0.07 [-0.2 a +0.1] |
| Umidade relativa | p.p. | -0.32 [-0.9 a +0.6] | -2.13 [-2.9 a -1.6] | -0.41 [-0.9 a -0.0] | -1.28 [-1.4 a -1.1] | -1.80 [-2.0 a -1.5] | -0.88 [-1.2 a -0.5] |
| Déficit de pressão de vapor | kPa | +0.03 [-0.0 a +0.1] | +0.08 [+0.1 a +0.1] | +0.02 [+0.0 a +0.0] | +0.05 [+0.0 a +0.1] | +0.04 [+0.0 a +0.0] | +0.04 [+0.0 a +0.1] |
| ETo | % | +5.34 [+3.3 a +7.9] | +3.93 [+3.2 a +5.0] | +2.04 [+0.7 a +3.1] | +0.53 [+0.1 a +1.5] | +0.13 [-1.0 a +1.1] | +3.53 [+2.3 a +4.7] |
| Radiação solar | MJ/m²/dia | +0.80 [+0.6 a +1.2] | +0.64 [+0.4 a +0.9] | +0.44 [+0.2 a +0.6] | +0.19 [+0.0 a +0.5] | +0.35 [+0.2 a +0.6] | +0.60 [+0.5 a +0.8] |
| Vento | m/s | +0.12 [+0.0 a +0.2] | +0.23 [+0.2 a +0.2] | +0.01 [-0.0 a +0.0] | +0.01 [-0.0 a +0.0] | -0.07 [-0.2 a +0.0] | +0.09 [+0.0 a +0.1] |
| ET real | % | +4.82 [+4.0 a +5.2] | +1.71 [+1.3 a +2.0] | +2.08 [+1.9 a +2.3] | +1.09 [+0.9 a +1.3] | +2.01 [+1.2 a +2.9] | +3.31 [+2.7 a +3.5] |
| Transpiração | % | +2.03 [+1.7 a +2.4] | +0.04 [+0.0 a +0.1] | +0.33 [+0.2 a +0.5] | +0.09 [+0.1 a +0.1] | +0.59 [+0.4 a +0.8] | +1.17 [+1.0 a +1.4] |
| Escoamento superficial | % | -0.08 [-0.1 a -0.1] | -0.09 [-0.1 a -0.0] | -0.00 [-0.0 a +0.0] | -0.00 [-0.0 a +0.0] | -0.05 [-0.1 a -0.0] | -0.06 [-0.1 a -0.0] |
| Escoamento subsuperficial | % | -0.01 [-0.0 a -0.0] | -0.02 [-0.1 a +0.1] | -0.01 [-0.0 a +0.0] | -0.00 [-0.0 a +0.0] | +0.00 [-0.0 a +0.0] | -0.01 [-0.0 a -0.0] |
| Temperatura do solo | °C | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] |
| Temperatura da folha | °C | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] |
| Umidade do solo 0-5 cm | m³/m³ | +0.00 [-0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | -0.00 [-0.0 a +0.0] | +0.00 [+0.0 a +0.0] |
| Umidade do solo 0-100 cm | m³/m³ | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [+0.0 a +0.0] | +0.00 [-0.0 a +0.0] | +0.00 [+0.0 a +0.0] |

