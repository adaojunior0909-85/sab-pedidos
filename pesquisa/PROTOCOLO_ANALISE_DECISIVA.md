# Protocolo da análise decisiva (fase 4): a chuva de 2020–2025 é real ou é dos dados?

**Pedido do responsável (26/11/2026, ~13h50):** "preciso de uma terceira análise mais profunda e detalhada para realmente
decidir o que fazer". Motivo: a auditoria profunda (fase 3) achou o salto da chuva do BR-DWGD desde 2020 em 4 famílias
de referências (inclusive o ERA5-Land, sem pluviômetro), o El Niño/La Niña não explica, mas as testemunhas físicas
(GRACE, SMAP) não separaram, e a regra deixou a chuva **inconclusiva**; já o M5 da fase 2 aprova o ajuste. Falta a
testemunha que é a verdade de chão: **os próprios pluviômetros, os mesmos o tempo todo**.

Congelado num commit **antes** de qualquer dado desta fase. Emenda só antes de rodar o teste afetado, datada.
Só leitura (Earth Engine, ANA, arquivos do autor). **Nada é gravado sem autorização do responsável.**

## D1 (teste central). Pluviômetros estáveis da ANA, 2010–2024
- **Fonte:** serviço público da ANA (`telemetriaws1.ana.gov.br/ServiceANA.asmx`, HidroInventario e HidroSerieHistorica,
  tipo 2 = chuva). Nível consistido (2) quando houver; senão, bruto (1).
- **Pluviômetro estável:** inventário com início ≤ 2009 e sem fim antes de 2025; ≥ 11 meses com total em **cada** ano de
  2010 a 2024; nenhum total anual fora de [0,3; 3] × a mediana do próprio posto em 2010–2019 (erro grosseiro).
  Amostra: todos os candidatos de cada estado, em ordem do código, até 150 estáveis por estado.
- **Comparações, no ponto do posto (pixel que o contém), total anual:** BR-DWGD bruto (o banco), CHIRPS (F3), ERA5-Land
  (F5), IMERG e PERSIANN (F1), TerraClimate (F2). Para cada posto e base X: q_X(y) = X(y) ÷ posto(y); salto do posto =
  média de q_X em 2020–2024 ÷ média de q_X em 2010–2019 − 1. **S_X** = mediana dos saltos dos postos (por região e
  Brasil). Intervalo de confiança de 95% por reamostragem dos postos (2.000 vezes).
- **Regra (por região e Brasil; ≥ 30 postos estáveis):**
  - **DADOS (a grade erra):** S_BR ≥ +4% com o IC inteiro acima de 0, **e** pelo menos 2 das famílias F1, F2, F3, F5 com
    |S_X| ≤ 3%. Quer dizer: os postos estáveis andam com as referências, e a grade do BR-DWGD se afasta deles.
  - **CLIMA (as referências erram):** |S_BR| ≤ 3%, **e** pelo menos 2 famílias com S_X ≤ −4% com o IC inteiro abaixo de
    0. Quer dizer: os postos estáveis mostram mais chuva de verdade, e as referências não acompanham.
  - **Inconclusivo:** qualquer outro caso.
- **Relato (fora da regra):** a média dos postos estáveis contra a média regional do banco ano a ano; o mesmo com os
  postos que entraram ou saíram (os não estáveis) para ver se a composição da rede puxa a média.

## D2. As referências entre si (sem o BR-DWGD)
Razão anual entre pares de famílias (F1/F2, F1/F3, F1/F5, F2/F3, F2/F5, F3/F5) por região, 2020–2024 contra 2010–2019.
**Regra:** se ≥ 2 pares que envolvem a mesma família mudam mais de 5% (e os outros não), essa família quebrou em 2020 e
sai das conclusões da fase 3 e da fase 4. Caso contrário, as referências são coerentes entre si.

## D3. A rede do BR-DWGD (o A4 da fase 3)
Com os arquivos de controle da v_3.2.4 (`pr_Control`, número de pluviômetros usados e distância ao mais próximo; pasta
pública do autor), por célula de 1°: **rede estável** (número médio de pluviômetros e distância média variando menos de
10% entre 2015–2019 e 2020–2024) × **rede mudada**. Salto da chuva do BR-DWGD contra CHIRPS e ERA5-Land em cada grupo.
**Regra:** a causa é a rede se o salto nas células de rede estável for menor que a metade do das de rede mudada e a
diferença passar de 4 p.p. Se o arquivo não puder ser lido na fila, o D3 é relatado como "não feito" (não entra na
decisão).

## D4. Vazão dos rios (relato)
Se o tempo permitir: grandes bacias com posto fluviométrico da ANA de série completa 2003–2024; balanço
chuva − ET real − vazão − ΔS (GRACE). Só relato; não entra na decisão.

## Decisão final da chuva 2020–2025 (por região)
- **Corrigir:** D1 = DADOS (e D2 sem família quebrada entre as que o D1 usou). D3, se feito, aponta a causa.
- **Manter o BR-DWGD:** D1 = CLIMA.
- **Inconclusivo** (D1 inconclusivo ou < 30 postos): manter com aviso no dicionário.

O que cada saída implica (vai ao responsável; nada é feito sem autorização):
| Saída | V1.8 / C3G (2026) | Histórico 2020–2025 (leitura, K16) | Previsão (matriz do GFS) |
|---|---|---|---|
| Corrigir | razões do C3 refeitas com 2010–2019 e teste fora da amostra (fase 1) antes de gravar | ajuste do M5 (fatores da fase 2) na leitura | matriz refeita com o BR-DWGD ajustado, ou fator de correção da chuva por região |
| Manter | V1.8 (ou C3G, que passou na leitura 1) como está | nada | nada |
| Inconclusivo | V1.8 suspensa; manter V1.7 | aviso | aviso |

## Auditoria (como na fase 3)
Conta em dobro do D1 (duas implementações); teste sintético antes dos dados reais (postos inventados com e sem salto da
grade); conferência de receita (3 postos: total anual da ANA × soma dos meses; pixel do BR-DWGD × leitura direta);
sensibilidade relatada (consistidos só; base 2015–2019; limiar de estável ≥ 12 meses).

## Ordem
1. D2 (sem rede nova) → 2. D1 pela fila (inventário, séries, amostragem no Earth Engine) → 3. D3 pela fila → 4. D4 se der.
Resultados em `pesquisa/resultados_decisiva/`.
