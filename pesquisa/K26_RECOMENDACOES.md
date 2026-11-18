# K26 (rodada 7, 1981-1990): o que os achados significam e o que mudou na v1.9

Base: o pacote K26_20261118_173417, o código da K26 v1.8 (`pesquisa/k26/K26_v1_8.py`) e três verificações só de
leitura: `verificar_k26.py`, `testar_escoamento.py` e `testar_escoamento2.py` (ESCOAMENTO.md) e `testar_mascara_h.py`.

**Correção de uma afirmação anterior:** este arquivo dizia que a K26 lia o banco bruto. Não lê: desde a v1.6 ela
mede o valor ENTREGUE (`LEITURA = 'entregue'`), com as mesmas correções de leitura do painel e dos pedidos. As
contagens da K26 e as das verificações batem; a diferença (16,5% x 29% no escoamento > chuva) vem da tolerância de
0,01 mm da K26 e da amostra (todos os dias x dia 15 de cada mês).

## O que cada achado significa

| Item | K26 v1.8 | Conferido | Situação |
|---|---|---|---|
| A1 | 3.652 dias, sem buraco nem repetição | — | OK |
| A2 | "versões: =3652", método vazio | o inventário grava '' quando a propriedade falta; o `fillna` não pega '' | Defeito de relatório; corrigido na v1.9 |
| A3 | 1.247 células com classe e sem valor no dia | — | Diferença de contagem (máscara estática x dia). Artigo: usar a máscara (72.046) |
| B | escoamento até 1.191 mm/dia na classe A; Rs e ETo fora da faixa só na C_borda | o escoamento extremo chega às planilhas (> 200 mm em 0,003% dos pixel-dias entregues) | Só o escoamento é problema real (ver C) |
| C | FALHA: escoamento > chuva em 16,5%; Rs e ETo anômalos | escoamento > chuva em 29% (sem tolerância) e chuva efetiva 0 em 1,1% dos dias com chuva >= 5 mm, nos pixels entregues; Rs > céu claro em 0,002% | **Problema real só no escoamento**: chuva observada x escoamento do modelo (ESCOAMENTO.md). Rs e ETo anômalos ficam quase todos na C_borda |
| H | até 8.856 pixel-dias a menos por mês na ET real e outras bandas do ERA5-Land, inclusive nos pixels entregues | nos 4 dias de 1985 conferidos, **os 70.982 pixels entregues têm valor em todas as bandas**; 1.205 (BR-DWGD) a 1.673 (ERA5-Land) deles têm máscara fracionária | **Não é vazamento**: a v1.8 somava a máscara fracionária dos pixels de costa |

## O que mudou na v1.9 (`pesquisa/k26/K26_v1_9.py`)

1. `RODADA = 8` (1991-2000), a próxima da sequência.
2. **Veredito de B, C e H só nos pixels ENTREGUES** (A, B, C_interior). O que acontece só na C_borda (fora das
   planilhas) vira INFO (`B_borda`, `C_borda`, `H_borda`).
3. **C anota a causa do escoamento > chuva** nos dias definitivos e aponta ESCOAMENTO.md. Continua FALHA, porque
   chega ao usuário.
4. **H conta "tem valor"** (máscara > 0) em vez de somar a máscara fracionária, e grava `K26_H_mascara_v19.csv`
   (as contagens antigas não se misturam).
5. **A2** escreve "V1.0 (sem propriedade)" em vez de vazio.
6. **`LEITURA = 'gravado'` volta a valer no modo rápido**: na v1.8 a condição tinha ido parar dentro de um
   comentário, e o modo rápido aplicava sempre a leitura corrigida.

Os vereditos novos de B, C e H foram refeitos fora do Earth Engine com os CSV da rodada 7: C nos entregues continua
FALHA (escoamento) e a C_borda vira INFO; B nos entregues fica só com o escoamento.

## Como rodar a rodada 8

Igual às outras: reiniciar a sessão, colar o arquivo inteiro e rodar. Os CSV das rodadas anteriores continuam
valendo em `/content/K26_acumulado/`, menos o `K26_H_mascara.csv` (a v1.9 usa outro arquivo e refaz o H da década).
Para o H das décadas já rodadas (1961-1990) com a contagem nova, rode as rodadas 5, 6 e 7 de novo só se quiser o
número exato para o artigo: o resultado esperado é "sem falta nos pixels entregues".

## O que continua em aberto

- **Escoamento dos dias de 1961-2025:** a correção pelo coeficiente do ERA5 foi testada e NÃO passou na regra (tira
  mais de 30% do escoamento em meses secos). Corrigir de verdade pede recalibrar o fator do SMAP sobre o escoamento
  corrigido: um projeto próprio. Enquanto isso, o dicionário dos pedidos avisa o usuário.
