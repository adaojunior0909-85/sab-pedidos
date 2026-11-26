# Auditoria profunda: decisão (seção 4 do protocolo)

Regras fixadas antes de rodar (`pesquisa/PROTOCOLO_AUDITORIA_PROFUNDA.md`, seção 4): **degrau dos dados confirmado** = A1 persistente + A2 "não explica" + (na chuva) A3 com ≥ 1 testemunha física com as referências e nenhuma com o SAB; **clima** = A2 "explica" ou (na chuva) testemunha física com o SAB; senão **inconclusivo** (aviso no dicionário, nenhuma correção). Só as linhas com degrau persistente ou decisão diferente de "sem degrau" aparecem abaixo; a tabela inteira está em `DECISAO.csv`.

| Variável | Região | A1 (anos 2020–24) | A2 | A3 (água) | Decisão |
|---|---|---|---|---|---|
| Umidade relativa | Nordeste | 3 (persistente) | não explica | (não se aplica) | **DEGRAU DOS DADOS CONFIRMADO** |
| Umidade relativa | Sudeste | 3 (persistente) | não explica | (não se aplica) | **DEGRAU DOS DADOS CONFIRMADO** |
| Chuva | Brasil | 5 (persistente) | não explica | GRACE: neutra, SMAP: neutra | inconclusivo → aviso no dicionário |
| Chuva | Centro-Oeste | 5 (persistente) | não explica | GRACE: neutra, SMAP: neutra | inconclusivo → aviso no dicionário |
| Chuva | Nordeste | 5 (persistente) | não explica | GRACE: neutra, SMAP: com o SAB | clima (nenhuma correção) |
| Chuva | Norte | 4 (persistente) | não explica | GRACE: neutra, SMAP: neutra | inconclusivo → aviso no dicionário |
| Chuva | Sul | 5 (persistente) | inconclusivo | GRACE: neutra, SMAP: neutra | inconclusivo → aviso no dicionário |
| Radiação | Norte | 5 (persistente) | inconclusivo | (não se aplica) | inconclusivo → aviso no dicionário |
| Radiação | Sudeste | 0 | explica | (não se aplica) | clima (nenhuma correção) |
| Radiação | Sul | 0 | explica | (não se aplica) | clima (nenhuma correção) |
| Tmax | Sudeste | 3 (persistente) | não explica | (não se aplica) | **DEGRAU DOS DADOS CONFIRMADO** |
| Tmin | Brasil | 0 | explica | (não se aplica) | clima (nenhuma correção) |
| Tmin | Sul | 0 | explica | (não se aplica) | clima (nenhuma correção) |
| Vento | Centro-Oeste | 0 | explica | (não se aplica) | clima (nenhuma correção) |
| Vento | Sudeste | 0 | explica | (não se aplica) | clima (nenhuma correção) |
| Vento | Sul | 0 | explica | (não se aplica) | clima (nenhuma correção) |
| VPD | Centro-Oeste | 4 (persistente) | inconclusivo | (não se aplica) | inconclusivo → aviso no dicionário |
| VPD | Nordeste | 3 (persistente) | não explica | (não se aplica) | **DEGRAU DOS DADOS CONFIRMADO** |
| VPD | Sudeste | 3 (persistente) | não explica | (não se aplica) | **DEGRAU DOS DADOS CONFIRMADO** |

