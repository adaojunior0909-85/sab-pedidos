# K26 (rodada 7, 1981-1990): o que os achados significam e o que mudar

Base: o pacote K26_20261118_173417 e duas verificações só de leitura nesta branch:
`verificar_k26.py` (o que chega ao usuário) e `testar_escoamento.py` (hipótese das janelas, ESCOAMENTO.md).

## O que cada achado significa

| Item | K26 (banco bruto) | No que o usuário recebe | Situação |
|---|---|---|---|
| A1 | 3.652 dias, sem buraco nem repetição | — | OK |
| A2 | "versões: =3652", método vazio | — | Os dias V1.0 não têm a propriedade `versao_algoritmo`; o painel e os pedidos já tratam a falta como V1.0 |
| A3 | 1.247 células com classe e sem valor no dia | — | Diferença de contagem (máscara estática x dia). Artigo: usar a máscara (72.046) e dizer qual é |
| B | escoamento até 1.763 mm/dia; Rs até 59,7 MJ/m²; ETo até 25,7 mm na C_borda | escoamento > 200 mm em 0,003% dos pixel-dias; Rs e ETo da C_borda não vão às planilhas | Só o escoamento chega (ver C) |
| C | escoamento > chuva em 16,5% (todos os pixels); Rs > céu claro; Rs e ETo zerados | escoamento > chuva em **29%** dos pixel-dias entregues; chuva efetiva 0 em **1,1%** dos dias com chuva >= 5 mm; Rs > céu claro em 0,002% | **Só o escoamento é problema real** (causa: chuva observada x escoamento do modelo; ESCOAMENTO.md) |
| H | até 0,41% menos pixels nas bandas só do ERA5-Land | **nenhuma diferença** nos pixels entregues | Está fora das classes entregues (borda) |

## O que mudar no script da K26 (para as próximas rodadas)

1. **Medir também o que o usuário recebe**, não só o banco bruto: aplicar as correções de leitura do painel
   (escoamento e solo V1.0 com o fator do SMAP limitado a 5, pixels B com o BR-DWGD, Rs dos C_interior limitada) e
   separar os pixels entregues (A, B, C_interior) da C_borda em todas as partes. Hoje uma violação só na borda faz o
   item C sair FALHA sem chegar a ninguém.
2. **Item C em dois níveis:** FALHA só para o que chega ao usuário; o que fica na borda vira INFO.
3. **Escoamento x chuva com a janela e a fonte certas:** nos dias definitivos, a chuva é 12-12 UTC (BR-DWGD) e o
   escoamento é 00-24 UTC (ERA5-Land, chuva do modelo). Comparar dia a dia mede a diferença de fonte, não um erro de
   cálculo. Sugestão: reportar também a razão escoamento/chuva por mês e região (no total ela é ~21%, plausível).
4. **A2:** escrever "V1.0 (sem propriedade)" quando `versao_algoritmo` não existe, em vez de vazio.
5. **H:** contar a falta de pixels só dentro das classes entregues.
6. **Cobrir os outros períodos**, em especial 2026 (rotas ERA5 provisória e GFS, outro código), onde a K26 ainda
   não rodou.

## O que já foi feito

- Dicionário dos pedidos com o aviso sobre escoamento e chuva efetiva: PR #3 (só texto, nenhum valor muda).
- Correção proposta do escoamento histórico (coeficiente do ERA5 aplicado à chuva observada): precisa de teste
  próprio com regra fixada antes e de decisão do dono, porque mexe no histórico travado.
