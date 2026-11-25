# R3: painel 2026.11.5 no ar (conferido em 24/11/2026)

Arquivos baixados do app oficial (`adao-alves-rodrigues-junior-sab`) depois do R3:
- `00_Dicionario_Variaveis_SAB.csv`: a linha `Radiacao_Solar_MJ_m2` traz o texto novo da 2026.11.5 ("Vazia nos dias
  em que o valor gravado fica abaixo de 3% da radiacao no topo da atmosfera..."), igual ao do `sab_pedido.py`
  2026.11.22. É a prova de que o app no ar é o 2026.11.5.
- `Diaria_Pato_Branco_2026.csv`: Pato Branco, 24/11 a 09/12/2026 (previsão GFS), 15 pontos. Radiação preenchida em todos
  os dias, inclusive nos nublados (mínimo ~3 MJ/m² em 28/11, acima do limite de ~1,3 MJ/m²): a regra só esvazia o valor
  impossível. Temperatura do solo e da folha vazias nos dias GFS, como previsto (o GFS não tem essas variáveis).

Sequência: R1 K16 v7.1 APROVADA (22/11, 22h40) → R2 PR #7 juntado (23/11, por autorização escrita do responsável,
que estava sem acesso ao GitHub) → R3 painel colado e conferido (24/11).
