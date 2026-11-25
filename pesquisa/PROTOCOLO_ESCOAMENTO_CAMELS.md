# Protocolo: escoamento do SAB contra a vazão observada (CAMELS-BR)

Fixado em 25/11/2026, **antes** de qualquer resultado. Nada aqui muda depois de rodar.

## Por quê
O escoamento do SAB (superficial e subsuperficial) nunca foi comparado com uma medida independente. A K26 achou o
escoamento acima da chuva do dia em 14% dos pixel-dias de 1961–2025, porque a chuva é a observada (BR-DWGD, 12–12 UTC)
e o escoamento é do modelo ERA5-Land (00–24 UTC), corrigido na leitura por um fator SMAP/ERA5 com teto 5 nos dias
V1.0. As duas correções diárias testadas antes foram reprovadas (`ESCOAMENTO.md`). Aqui a pergunta é outra: **no total
do mês, numa bacia, o escoamento do SAB bate com a água que sai pelo rio?**

## Referência
CAMELS-BR v1.1 (Chagas et al., 2020, *Earth System Science Data*; doi:10.5281/zenodo.3964745, CC-BY-4.0): vazão
diária observada pela ANA, em mm/dia na área da bacia, e os contornos das bacias.

- **Bacias:** área (GSIM) de 500 a 50.000 km², grau de regulação < 10% e uso consuntivo < 10% (pouca interferência
  humana). São 512 bacias.
- **Meses:** de 1981 a 2018, só os meses com pelo menos 25 dias de vazão observada.
- **Comparação:** total mensal (mm) da vazão observada × média, na bacia, do escoamento total (superficial +
  subsuperficial) de cada método, somado no mês. Grade do SAB (0,1°), pixel pesado pela fração dentro da bacia.

## Métodos comparados
- **M0, atual:** o escoamento total que o usuário recebe (SAB_V1 com a correção de leitura dos dias V1.0: fator mensal
  SMAP/ERA5 com teto 5, a mesma do painel e do `sab_pedido.py`).
- **M1, gravado:** o mesmo sem a correção de leitura (o que está no asset).
- **M2, ERA5-Land puro:** escoamento total do ERA5-Land mensal (`ECMWF/ERA5_LAND/MONTHLY_AGGR`), sem fator nenhum.
- **M3, coeficiente do ERA5 × chuva observada:** coeficiente de escoamento mensal do ERA5-Land no pixel (escoamento
  total ÷ chuva do ERA5-Land no mês, limitado a 0–1) × chuva mensal do SAB (BR-DWGD). Por construção, nunca passa da
  chuva observada.

## Métricas (por bacia, sobre os meses válidos)
KGE (Gupta et al., 2009), viés relativo do total (%) e correlação de Pearson dos totais mensais.

## Regra de decisão (para trocar o M0 por outro método)
Um método candidato só substitui o M0 se cumprir **as quatro** condições:
1. a mediana do KGE entre as bacias sobe pelo menos **0,10** em relação ao M0;
2. o KGE melhora em pelo menos **60%** das bacias;
3. as condições 1 e 2 valem **separadamente** nas duas metades: 1981–1999 e 2000–2018;
4. a mediana do |viés| não piora.

Se mais de um passar, fica o de maior mediana do KGE. Se nenhum passar, o M0 fica, e o resultado vira um aviso
quantitativo no dicionário (o quanto o escoamento do SAB erra no total do mês, por região).

O resultado é publicado por região hidrográfica da ANA (`gauge_region`) e no Brasil, passe ou não passe.
Um método aprovado não muda o banco atual: ele seria a base de um `SAB_V2`, montado em paralelo e auditado antes.
