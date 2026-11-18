# Escoamento superficial maior que a chuva (achado C da K26): hipótese, teste e regra de aceite

Escrito ANTES de rodar o teste (`testar_escoamento.py`).

## O problema (verificacao_k26.py, dia 15 de cada mês de 1981-1990, pixels entregues A, B e C_interior)

No que o usuário recebe, o escoamento superficial passa da chuva do dia em 28,8% dos pixel-dias, passa da chuva
+ 10 mm em 0,65%, passa de 200 mm/dia em 0,003% (até 1.763 mm no banco), e a chuva efetiva sai 0 em 1,09% dos
pixel-dias com chuva >= 5 mm.

## Hipótese: janelas diferentes

Nos dias definitivos (até 2025), a chuva é do BR-DWGD, acumulada das 12h UTC de D-1 às 12h UTC de D. O escoamento
é do ERA5-Land, acumulado das 0h às 24h UTC de D. O escoamento da janela da chuva é, supondo distribuição uniforme
no dia, **0,5 x escoamento(D-1) + 0,5 x escoamento(D)**. Comparar o escoamento de D com a chuva de D compara
janelas deslocadas em 12 h: a chuva de uma tarde entra na chuva de D+1 e no escoamento de D.

(Dias de 2026 em diante: chuva e escoamento na mesma janela 00-24 UTC; o alinhamento não se aplica a eles.)

## Variantes testadas (na leitura corrigida que os pedidos entregam)

- `atual`: como hoje;
- `alinhado`: escoamento = 0,5 x escoamento(D-1) + 0,5 x escoamento(D), só nos dias definitivos;
- `alinhado_teto`: o alinhado, limitado à chuva do dia (o que sobrar de inconsistência vira escoamento = chuva).

## Regra de aceite (fixada antes)

O alinhamento é adotado se, em relação ao `atual`:

1. a chuva efetiva zerada em dia com chuva >= 5 mm cair pelo menos 50%;
2. o escoamento acima da chuva + 10 mm cair pelo menos 50%;
3. a soma do escoamento no período mudar menos de 2% (o alinhamento só redistribui no tempo; não pode criar nem
   tirar água).

O teto (`alinhado_teto`) só é adotado junto se, depois do alinhamento, retirar menos de 2% da soma do escoamento.
Se o alinhamento não passar, a hipótese está errada e nada é mudado no que se entrega; a decisão volta para a
mesa (opções de tirar os índices ou documentar).
