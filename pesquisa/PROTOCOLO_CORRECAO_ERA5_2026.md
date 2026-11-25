# Protocolo: correção da chuva, da radiação e da ETo nos dias ERA5 (2026 e adiante)

**APROVADO pelo responsável em 25/11/2026 e congelado neste commit, ANTES de qualquer resultado.** Depois de rodar, nada nele muda. Nada no Earth Engine é gravado por este protocolo: o teste é só leitura. Uma mudança no motor só acontece depois, pelo caminho de sempre: 05a (simulação), K16, aprovação e 05b. O histórico de 1961–2025 nunca é regravado.

## Por quê
A Parte A (`pesquisa/resultados_metodo_2026/RESULTADOS_A.md`) aplicou a rota ERA5 do motor V1.7 a 2021–2025 e comparou
com o que o banco entrega nesses anos (BR-DWGD no núcleo):

- **Chuva:** fica abaixo em **todos** os anos e em todas as regiões. Brasil −9,6% (de −7,2% a −13,3% por ano),
  Nordeste −12,4%, Centro-Oeste −11,9%, Norte −9,2%, Sul −7,5%, Sudeste −6,8%. O pior ano é 2023 ou 2024 em quase todas
  as regiões.
- **Por mês do ano (2021–2025 juntos):** no Nordeste o déficit é quase constante (−3% a −18%). No Norte e no
  Centro-Oeste ele cresce muito na seca (Norte set −35%, Centro-Oeste jul −47% e set −41%).
- **ETo:** +3,5% no Brasil (Norte +5,3%, máximo +10% em junho). **Radiação:** +0,6 MJ/m²/dia. **UR:** −0,9 p.p. As
  três vêm juntas: radiação maior dá ETo maior.

**Hipótese:** o viés não é estacionário. A calibração atual é a média de 1986–2025 por pixel e mês
(`SICSB_1986_2025`), e nos anos recentes o ERA5-Land ficou mais seco e mais ensolarado do que o BR-DWGD. Uma calibração
pela média longa não acompanha essa mudança.

## Pergunta
Uma calibração que pesa os anos recentes reduz o erro da chuva (e da radiação e da ETo) **em anos que ela não viu**,
sem piorar a variação de mês a mês nem os extremos?

## Desenho: teste fora da amostra com origem móvel
- **Anos de teste:** 2016 a 2025 (10 anos com BR-DWGD).
- **Treino de cada ano-alvo Y:** só os anos **anteriores a Y**, como acontece na operação (2026 calibrado com dados até
  2025). O ano Y nunca entra no seu próprio treino.
- **Referência:** o BR-DWGD, ou seja, o que o banco entrega nos pixels A. Para conferir que a referência não é o
  problema, a chuva também é comparada com o CHIRPS nos mesmos anos. Esse resultado só é relatado e não entra na regra.
- **Amostra:** as médias das 5 regiões e do Brasil, com os pixels entregues de `SAB_MASCARA_QUALIDADE` (classes 1–3).
  Mais os mesmos 150 pixels da K21 para os extremos diários.

## Métodos comparados (lista fechada)
| Id | Chuva (dias ERA5) | Radiação (dias ERA5) |
|---|---|---|
| **C0, atual** | fator multiplicativo pixel × mês, média de 1986 a Y−1 (equivale ao V1.7) | o atual (fator da média, limitado a Rso) |
| **C1, janela de 10 anos** | o mesmo fator, com a média só de Y−10 a Y−1 | idem, janela Y−10 a Y−1 |
| **C2, janela de 15 anos** | o mesmo fator, Y−15 a Y−1 | idem, Y−15 a Y−1 |
| **C3, C0 + ajuste regional recente** | C0 × razão (BR-DWGD ÷ C0) da região e do mês em Y−5 a Y−1, limitada a [0,8; 1,5] | C0 + diferença (BR-DWGD − C0) da região e do mês em Y−5 a Y−1 |

Em todos os métodos continuam iguais: o teto da chuva diária, a radiação limitada à de céu claro, o 0 de radiação
tratado como vazio e a ETo recalculada pelo FAO-56 com a radiação corrigida.

## Métricas (só nos anos de teste)
1. |viés do total anual| da chuva (%) por região, por ano e na mediana dos 10 anos;
2. `r_anomalias` mensal da chuva por região (o ciclo anual retirado);
3. nos 150 pixels: fração de dias com chuva ≥ 1 mm e o percentil 99 diário, comparados com o BR-DWGD;
4. radiação: |viés| (MJ/m²/dia). ETo: |viés| (%).

## Regra de decisão (fixada antes)
Um método **substitui o C0 na chuva** só se cumprir **as quatro** condições:
1. a mediana, entre as 5 regiões, do |viés anual| cai pelo menos **3 p.p.** em relação ao C0;
2. no Brasil, o |viés anual| melhora em pelo menos **7 dos 10** anos de teste;
3. o `r_anomalias` não cai mais de **0,02** em nenhuma região;
4. nos 150 pixels, a fração de dias com chuva não se afasta do BR-DWGD mais **2 p.p.** do que o C0 já se afasta, e o
   erro do percentil 99 não cresce mais de **5%**.

Se mais de um método passar, vence o de menor mediana do |viés|. Se a diferença for menor que 0,5 p.p., vence o mais
simples, nesta ordem: C1, C2, C3.

**Radiação e ETo** (avaliadas juntas): um método substitui o C0 se o |viés| da radiação no Brasil cair pelo menos
**0,2 MJ/m²/dia**, o da ETo cair pelo menos **1 p.p.**, e nenhuma região piorar mais de 0,1 MJ ou 0,5 p.p.

**Só relatado (fora da regra, aprovado junto):** o método que vencer (ou o C0, se nenhum passar) é aplicado a **2026** e a chuva de 2026 é comparada com o **CHIRPS** por região, nos mesmos meses e com a mesma régua de `validar_2026_independente.py` (2024, quando o SAB é o BR-DWGD). Se a chuva corrigida de 2026 no Centro-Oeste e no Nordeste chegar perto do CHIRPS como em 2024, é uma confirmação independente. Esse resultado não muda a decisão.

Se nenhum método passar, o motor continua como está e o aviso da chuva de 2026 vai para o dicionário. O texto do aviso
usa os números da Parte A.

## Depois do teste (cada passo só com a aprovação do responsável)
1. Se um método passar: o motor V1.8 em simulação (05a no `sab-motor`), uma prévia de 2026 e a K16 nova.
2. Para usar uma janela de anos, a climatologia precisa de um asset novo (por exemplo, `SICSB_2016_2025`). **Criar esse
   asset é uma escrita no Earth Engine**, por isso depende de aprovação separada. O asset `SICSB_1986_2025` não muda.
3. O 05b regrava **só 2026** (provisório). O histórico de 1961–2025 não é tocado.

## Arquivos
- Script (a escrever depois da aprovação): `pesquisa/validar_correcao_era5.py`, só leitura, com esta regra no
  cabeçalho.
- Saída: `pesquisa/resultados_correcao_era5/` (CSV brutos por ano-alvo e `RESULTADOS.md`).
