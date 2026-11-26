# Análise decisiva (fase 4): decisão da chuva 2020–2025 (26/11/2026, ~20h)

Protocolo `pesquisa/PROTOCOLO_ANALISE_DECISIVA.md` (congelado em d2d7dc1; emenda 1 antes de qualquer resultado do D1).

## Resultado
- **D1 (teste central), 1.279 pluviômetros estáveis da ANA** (os mesmos de 2010 a 2024, 25 estados; São Paulo e
  Tocantins não concluídos porque a ANA saiu do ar): nos próprios postos, **o BR-DWGD acompanha os pluviômetros**
  (Brasil −0,6%; regiões entre −3,1% e +2,5%), enquanto **todas as referências ficam abaixo deles desde 2020**:
  CHIRPS −9,2%, ERA5-Land −7,1%, IMERG −10,4%, PERSIANN −8,0%, TerraClimate −10,6% (Brasil; IC 95% inteiro abaixo de
  zero). Ano a ano, o degrau das referências contra os postos aparece em **2020** (de ±3% em 2010–2019 para −8 a −15%
  em 2020–2024). Todos os dados dos postos são do mesmo nível (bruto) em todos os anos.
  **Veredito pela regra: CLIMA (as referências erram)** no Brasil, Norte, Nordeste, Centro-Oeste e Sul; Sudeste
  inconclusivo (sem SP). Sensibilidade com base 2015–2019: o mesmo (Sul passa a inconclusivo, Sudeste a CLIMA).
- **D2:** as referências F1, F2 e F5 são coerentes entre si; o CHIRPS subiu ~6% contra elas desde 2020 (Brasil,
  Norte) — mesmo assim fica 9% abaixo dos pluviômetros.
- **D3** (rede do BR-DWGD): não feito (Google Drive bloqueou o download por cota); nova tentativa em 27/11. Não entra
  na decisão.

## Decisão (tabela do protocolo, saída "Manter o BR-DWGD")
| O quê | Decisão |
|---|---|
| Histórico 2020–2025 (chuva) | **manter o BR-DWGD**; o ajuste do M5 na chuva 2021–25 NÃO deve ser aplicado |
| 2026 (dias ERA5) | **a V1.8 (C3) está na direção certa**: ela leva o ERA5-Land ao nível do BR-DWGD, que concorda com os pluviômetros; o C3G (que passou na leva 1) é a versão melhorada |
| Previsão (matriz do GFS 2021–2025) | **manter**: a calibração foi feita contra uma chuva que os pluviômetros confirmam |
| Aviso no dicionário | registrar que as bases de satélite e de reanálise ficam ~8–10% abaixo dos pluviômetros desde 2020 |

## O que isso implica para as outras conclusões
- A "chuva alta do BR-DWGD" das fases 2 e 3 era, na verdade, **as referências baixas** depois de 2020.
- Os degraus de UR (+), VPD (−), Tmax (−, Sudeste) e radiação (−) do BR-DWGD desde 2020 vêm das mesmas referências
  (ERA5-Land, GLDAS, NASA POWER, TerraClimate), que ficaram mais secas; sem estação de chão para essas variáveis (o INMET
  bloqueia o acesso automático), **não há base para corrigi-los**: aviso no dicionário, nenhuma correção.
