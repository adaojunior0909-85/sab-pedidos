# O excesso de chuva depois de 2020 vem do BR-DWGD? Leitura dos artigos (26/11/2026)

Pedido do responsável: "analise esses dois documentos do BR-DWGD para verificarmos realmente se é ele que está prevendo
excesso ou não, e compare com os documentos oficiais das outras bases de dados".

## 1. O que os dois artigos do BR-DWGD dizem

| | Xavier et al. 2016 (IJC 36: 2644–2659, doi 10.1002/joc.4518) | Xavier et al. 2022 (IJC, doi 10.1002/joc.7731) |
|---|---|---|
| Período | 1/1/1980 a 31/12/2013 | **1/1/1961 a 31/7/2020** |
| Resolução | 0,25° | 0,1° |
| Rede | 3.625 pluviômetros, 735 estações | 11.473 pluviômetros, 1.252 estações (642 convencionais, 610 automáticas), ANA e INMET por API |
| Chuva | IDW (5 vizinhos) | ADW (5 vizinhos) |
| Validação cruzada da chuva | R 0,61; Amazônia R 0,36 | R 0,653; viés 0,004 mm/dia; RMSE 8,2 mm; Amazônia R 0,38 |
| O fim do período | "atribuímos a queda de **2013** à demora dos órgãos em organizar e disponibilizar os dados" | "os anos recentes, **2019 e 2020**, têm uma quantidade **muito baixa** de dados de pluviômetros (...) supomos que os órgãos ainda não disponibilizaram os dados" |
| Avisos dos autores | Amazônia com 0,1 pluviômetro/1.000 km²; onde faltam estações o campo fica "liso" | o produto tem **valor limitado onde não há estação a 50 km**; a mudança da densidade de estações no tempo pode enganar a leitura de tendências; por isso entregam os controles **Count** (estações usadas) e **dist_nearest** (distância da estação mais próxima) |

O que isso significa para o SAB:
1. **Os dois artigos mostram o mesmo padrão**: o fim de cada versão é a parte mais fraca, porque os dados dos últimos
   anos ainda não chegaram (2013 na versão de 2016; 2019–2020 na de 2022).
2. **2021–2025 não está em nenhum artigo.** O que o asset `projects/ee-alexandrexavier/assets/BR-DWGD` tem depois de
   31/7/2020 é uma **extensão sem documentação publicada**: não sabemos que rede, quantas estações, nem se o método é o
   mesmo. Exatamente o período em que as 4 referências independentes acusam o salto.
3. O salto começa em **2020**, o ano que o próprio artigo diz ter "muito poucos dados" e cujo 2º semestre já é extensão.

## 2. O que dizem os documentos oficiais das outras bases (de onde vem a chuva de cada uma)

| Base | Como a chuva é feita (documentação oficial) | Usa os pluviômetros da ANA/INMET? | Chuva do SAB em 2020–2024 em relação a ela (×2001–2015) |
|---|---|---|---|
| **GLDAS-2.1** (Rodell et al. 2004; README GES DISC) | modelo forçado pela chuva do GPCP 1DD (satélite ajustado ao GPCC mensal) | só pelo GPCC (rede global, via GTS) | **+8 a +12%** |
| **IMERG Final** (Huffman et al., ATBD v06/v07) | satélites de micro-ondas + infravermelho, calibrados mês a mês pelo GPCC | só pelo GPCC | **+7 a +9%** |
| **PERSIANN-CDR** (Ashouri et al. 2015, BAMS) | infravermelho + rede neural, ajustado ao GPCP mensal | só pelo GPCP/GPCC | **+9 a +14%** |
| **TerraClimate** (Abatzoglou et al. 2018, Sci. Data) | climatologia WorldClim + anomalias do CRU TS (estações) e JRA-55 | só pelo CRU (rede global) | **+11%** |
| **CHIRPS v2** (Funk et al. 2015, Sci. Data) | satélite infravermelho + climatologia + **mistura com estações** (inclui redes nacionais) | **em parte** (o CHIRPS mistura estações; pode ter parte da mesma rede) | **0 a +5%** |
| **ERA5-Land** (Muñoz-Sabater et al. 2021, ESSD) | reanálise; a chuva é do modelo, **não assimila pluviômetros** | não | (é a base corrigida pela V1.8; não serve de juiz da chuva) |

O ponto decisivo: **quatro famílias de produtos feitas de jeitos completamente diferentes** (modelo de superfície,
micro-ondas, infravermelho com rede neural, interpolação de anomalias do CRU) mudam a relação com o SAB **no mesmo ano
(2020) e no mesmo sentido**, depois de 40 anos estáveis (±3%). Para o problema estar nelas, as quatro teriam de errar
juntas e para menos a partir de 2020. A única fonte que muda de natureza exatamente em 2020 é o BR-DWGD (fim do artigo,
rede rala, extensão sem documentação). O CHIRPS concordar mais é coerente: ele **também usa estações**, então pode
compartilhar parte do mesmo viés.

## 3. Conclusão (provável, ainda não definitiva)
- **Sim, o mais provável é que o excesso venha do BR-DWGD de 2020 em diante**, não das outras bases.
- O mecanismo ainda não está provado. Rede rala no ADW tende a aumentar os dias com chuva e a reduzir a intensidade
  (o campo "espalha" a chuva de poucos pluviômetros). Uma mudança na composição da rede (mais estações automáticas ou
  telemétricas, outras regiões) também pode mudar o total. Quem responde é o `pesquisa/investigar_brdwgd.py` (rodando
  desde 26/11 10h30): total, dias ≥ 1 mm, intensidade e cobertura ano a ano contra CHIRPS e ERA5, mais as bandas e
  propriedades de cada ano (se o asset tiver Count/dist_nearest, dá para ver a rede encolher).
- **Consequência para a V1.8:** as 60 razões do C3 saem de 2021–2025, justamente o trecho suspeito. Se o BR-DWGD estiver
  ~9% alto ali, a V1.8 empurra a chuva de 2026 ~9% para cima (o Sul +15,5% × CHIRPS é coerente com isso). **A
  suspensão do merge está confirmada pela leitura dos artigos.**
- **Caminho proposto (só com autorização):** refazer as razões do C3 com anos que os artigos cobrem com rede cheia
  (ex.: 2010–2018), repetir o teste fora da amostra da fase 1 com essa janela (protocolo novo congelado antes) e só
  então decidir a V1.8. O histórico 1961–2019 não é afetado; 2020–2025 do banco passa a ter um aviso (e, no M5, é
  candidato a ajuste na leitura, se confirmado por 2 referências — já está: 4).
