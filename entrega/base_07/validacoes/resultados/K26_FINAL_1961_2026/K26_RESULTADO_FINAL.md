# K26: resultado final, 1961–2026 (fechado em 22/11/2026)

A K26 é somente leitura: lê o valor que o usuário **recebe** (`LEITURA = 'entregue'`). As contagens abaixo são só dos
pixels **entregues** (classes A, B e C_interior). A C_borda não vai às planilhas e fica de fora.

**Cobertura:** de 01/01/1961 a 07/12/2026, sem nenhum dia faltando (A1 ✅ em todas as rodadas). São **1.702.278.491
pixel-dias entregues**, e cada um passou pelos 20 testes da parte C.

| Período | Rodada (versão) | Pixel-dias |
|---|---|---|
| 1961–1970 | 5 (v1.12, 22/11) | 258.153.008 |
| 1971–1980 | 6 (v1.12, 22/11) | 258.223.697 |
| 1981–1990 | 7 (v1.8, 18/11) | 258.153.008 |
| 1991–2000 | 8 (v1.9, 18/11) | 258.223.697 |
| 2001–2025 | 12 (v1.11, 19/11) | 645.453.209 |
| 2026 (até 07/12) | 1 (v1.12, 22/11) | 24.071.872 |

Os números saem de `montar_tabela_decadas.py`, que lê as pastas `K26_rodada*` ao lado e grava `K26_tabela_decadas.csv`
e `K26_extremos_decadas.csv`.

## 1. O que nunca falhou, em 66 anos

Estes 11 testes deram **zero violações em todos os 1,7 bilhão de pixel-dias entregues**:
ET real > ETo · transpiração > ET real · Tmax < Tmin · UR fora de 0–100% · umidade do solo acima do máximo ·
valor negativo · VPD incoerente · chuva ≥ 450 mm/dia · Rs ≥ radiação no topo da atmosfera · vento fora da faixa ·
temperatura fora da faixa.

**H (máscara banda a banda): ✅** em todas as rodadas da v1.9 em diante. As 16 bandas têm o mesmo número de pixels
em todos os dias. A exceção é 1981–1990, que rodou na v1.8: a v1.8 contava as máscaras fracionárias e dava um ATENÇÃO
falso. Essa década não foi refeita com a v1.9 ou posterior; ver o passo 4.

## 2. Tabela por década (% dos pixel-dias entregues)

| Período | Escoamento > chuva | > chuva + 10 mm | > chuva + 50 mm | > 200 mm/dia | Rs > céu claro | Rs = 0 (pixel-dias) | Escoamento máximo |
|---|---|---|---|---|---|---|---|
| 1961–1970 | 13,72% | 0,689% | 0,065% | 0,0075% | 0,00001% | 264 (C_interior) | 1.647 mm (A, 1965) |
| 1971–1980 | 15,96% | 0,695% | 0,054% | 0,0053% | 0,00017% | 250 (C_interior) | 1.598 mm (B, 1974) |
| 1981–1990 | 16,59% | 0,646% | 0,044% | 0,0041% | 0,0035% | 241 (C_interior) | 1.763 mm (B, 1985) |
| 1991–2000 | 15,78% | 0,683% | 0,052% | 0,0039% | 0,00008% | 279 (C_interior) | 949 mm (A, 1991) |
| 2001–2025 | 12,13% | 0,663% | 0,074% | 0,0077% | 0,0185% | 664 (C_interior) | 1.865 mm (B, 2008) |
| **1961–2025** | **14,21%** | **0,672%** | — | **0,0061%** | **0,0077%** | **1.698** | 1.865 mm |
| 2026 | 0,48% | 0,147% | 0,036% | 0,0159% | 0,00008% | 1.176 (A 747, B 429) | 1.100 mm (A, fev) |

ETo = 0 num dia com radiação: 32, 59, 59, 67 e 116 pixel-dias por período até 2025, todos em C_interior; 0 em 2026.
Rs abaixo de 3% da radiação no topo da atmosfera: de 6 a 19 por período até 2025; 1.021 em 2026, quase todos em dias GFS.

Os pixel-dias da K26 são **pesados pela fração da máscara** de cada pixel. Os pixels de borda e do litoral contam menos
de 1, por isso os números absolutos acima ficam menores que a contagem em pixels inteiros (ver 3.3). As porcentagens são
frações de área e não mudam com isso.

## 3. Os achados

### 3.1 Escoamento × chuva (1961–2025): uma característica da montagem, igual em todas as décadas

O escoamento superficial passa da chuva do dia em 12–17% dos pixel-dias e passa da chuva + 10 mm em ~0,67%. O tamanho
é o mesmo nas cinco décadas. Em 2026 cai para 0,48%. A causa já estava documentada: até 2025 a chuva é a **observada**
(BR-DWGD, 12–12 UTC) e o escoamento vem do **ERA5-Land** (00–24 UTC), que responde à chuva do próprio modelo. Em 2026
os dois vêm do ERA5 e quase não divergem. As duas correções testadas foram reprovadas pela regra fixada antes
(`pesquisa/ESCOAMENTO.md`). O aviso já está no dicionário dos dois caminhos (sab_pedido 2026.11.19 e painel 2026.11.4).
Recalibrar o escoamento continua sendo decisão do responsável.

### 3.2 Rs = 0 nos C_interior (1961–2025): em todas as décadas

São de 241 a 664 pixel-dias por período, sempre em C_interior, com ETo = 0 em parte deles. Em ~1,7 bilhão de
pixel-dias isso dá 0,0001%, mas o valor chega às planilhas. Rs = 0 de dia é fisicamente impossível. A correção na
leitura (passo 1 da seção 4) cobre esses dias.

### 3.3 NOVO (2026): o Rs = 0 do litoral explica a ETo divergente dos "20 pixels", e a causa está no ERA5-Land

> **Correção de 22/11, à noite:** a 1ª versão deste relatório dizia "13 pixels B" e que "a ETo gravada está certa".
> As duas coisas estavam erradas. O diagnóstico no Earth Engine (`pesquisa/diagnostico_rs_litoral.py`, repositório
> `sab-pedidos`) mostrou o que está abaixo.

Desde a K25, os mesmos pixels B/C_borda tinham a ETo gravada diferente da ETo refeita em **04–20/03** e
**23/09–08/10/2026** (G ❌):

- **A causa está na fonte, não na lógica do motor.** Esses pontos de mar, lagoa e estuário normalmente vêm **vazios** no
  ERA5-Land, e o motor V1.6 os completa pela vizinhança (`expandir_borda`), com um Rs normal. Nas duas janelas, o
  ERA5-Land do Earth Engine (`ECMWF/ERA5_LAND/DAILY_AGGR`) traz os **mesmos pontos preenchidos com radiação 0**. O motor
  toma o 0 por valor, e a vizinhança não entra. Nos três pixels conferidos (Lagoa Mirim, costa do Amapá, Maranhão), o 0
  começa e termina exatamente nas mesmas datas.
- **A ETo desses dias também está errada.** O motor a calcula com esse Rs = 0. Na Lagoa Mirim ela fica em 2,3 mm em
  10/03, contra 5,2 mm em 01/03 e 4,5 mm em 21/03; na costa do Amapá, 0,9 mm em 20/03 contra 4,2 mm em 21/03.
- **Tamanho, em pixels inteiros:** em 10/03 são **124 pixels**: 27 B, 1 A e 1 C_interior entregues, mais 95 C_borda. A
  K26 mostrava 21 porque **as contagens da K26 pesam cada pixel pela fração da máscara**, e os pixels do litoral têm
  fração pequena. As porcentagens da K26 continuam valendo como fração de área; só os números absolutos de pixel-dias
  ficam menores que os de pixels inteiros.

Isso chegava aos usuários: nos dias de 2026 os pixels B não têm o BR-DWGD (ele vai até 2025) e eram entregues com o
valor do ERA5.

### 3.4 NOVO (2026): Rs = 0 nos dias GFS em pixels A

No dia GFS de **16/11/2026** são **1.142 pixels A** com Rs abaixo de 3% do topo da atmosfera, em pixels inteiros (a K26
mostrava 627, com o peso da máscara). Não há nenhum nos 317 dias ERA5 de 2026 nem em nenhuma década até 2025. Esses dias
são provisórios: o motor os reescreve toda noite, e o ERA5 os substitui depois.

### 3.5 Rs acima do céu claro

É no máximo 0,0185% (2001–2025), quase todo em pixels A, onde o Rs vem do BR-DWGD. Fica como INFO.

## 4. Próximos passos (atualizado em 22/11/2026, à noite)

1. ✅ **Correção na leitura, feita** (PR #7 do `sab-pedidos`, painel 2026.11.5). Onde Rs fica abaixo de 3% da
   radiação no topo da atmosfera, **Rs, ETo e déficit do dia saem vazios**, no e-mail e no painel. Cobre 3.2, 3.3 e 3.4.
   Conferida no Earth Engine de verdade: só esses pixels mudam, e só nessas três bandas. **Falta a K16 v7** (guia,
   passos R1 a R3); só depois dela se junta o PR #7 e se cola o painel.
2. **Motor (`sab-motor`), proposta, sem mudança ainda:** no `_componentes_era5`, tratar como **vazio** o Rs do ERA5-Land
   = 0 (de dia não existe), para a vizinhança completar como nos outros dias. Isso conserta os dias provisórios
   **novos**. Os de 2026 já gravados continuam com o 0 no banco, e a correção na leitura cobre todos eles. Precisa de
   simulação (05a) e de conferência antes de ir para o GitHub do motor.
3. **Próxima rodada 1 (2026)**, depois de meados de dezembro: ver se o Rs = 0 do GFS de 15–22/11 sumiu com o ERA5.
   Atenção: a K26 lê o valor entregue com a cópia **dela** da leitura (sem a regra nova), então ela continua mostrando
   o que está gravado no banco.
4. **Opcional:** refazer 1981–1990 (rodada 7) na v1.12, só para fechar o H dessa década na contagem nova
   (`RODADAS_EM_SEQUENCIA = [7]`, ~75 min).
