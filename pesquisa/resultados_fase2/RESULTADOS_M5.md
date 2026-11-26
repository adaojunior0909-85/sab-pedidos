# Fase 2, M5: ajuste dos degraus confirmados do histórico (teste, só leitura)

Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (M5 e emenda 1). Detalhes de implementação no cabeçalho de `pesquisa/fase2_m5.py`. Ajuste: × fator (chuva, vento, radiação, somas) ou + diferença (temperaturas, UR, VPD). **Passa** = a década deixa de ser suspeita nas referências que a marcaram e nenhuma outra década passa a ser, em nenhuma fonte. Nada é gravado: o que passa vai ao responsável (correção só na leitura, com K16).

| Variável | Região | Década | Referências | Ajuste | Some nas refs? | Novas décadas suspeitas | Passa? | Nota |
|---|---|---|---|---|---|---|---|---|
| Umidade relativa | Nordeste | 1961-1970 | ERA5-Land, GLDAS | -4.677 | sim | 2001-2010 (gldas20) | ❌ |  |
| ETo | Nordeste | 1971-1980 | GLDAS, TerraClimate | × 0.963 | não | - | ❌ |  |
| ETo | Norte | 2001-2010 | GLDAS, TerraClimate | × 0.921 | sim | 1961-1970 (terraclimate) | ❌ |  |
| ET real | Sudeste | 2001-2010 | GLDAS, MOD16 | × 0.921 | sim | - | ✅ | variável do modelo: só relato (M4) |
| Chuva | Brasil | 2021-2025 | ERA5-Land, GLDAS, IMERG, PERSIANN, TerraClimate | × 0.890 | sim | - | ✅ |  |
| Chuva | Centro-Oeste | 2021-2025 | ERA5-Land, GLDAS, IMERG, PERSIANN, TerraClimate | × 0.899 | sim | - | ✅ |  |
| Chuva | Nordeste | 2021-2025 | ERA5-Land, GLDAS, IMERG, PERSIANN, TerraClimate | × 0.849 | sim | - | ✅ |  |
| Chuva | Norte | 2021-2025 | ERA5-Land, GLDAS, IMERG, PERSIANN, TerraClimate | × 0.884 | sim | 1961-1970 (terraclimate) | ❌ |  |
| Chuva | Sudeste | 1981-1990 | GLDAS, TerraClimate | × 0.958 | sim | - | ✅ |  |
| Chuva | Sudeste | 2021-2025 | ERA5-Land, TerraClimate | × 0.949 | sim | - | ✅ |  |
| Chuva | Sul | 2011-2020 | ERA5-Land, GLDAS | × 0.972 | não | - | ❌ |  |
| Chuva | Sul | 2021-2025 | ERA5-Land, GLDAS, IMERG, PERSIANN, TerraClimate | × 0.937 | sim | - | ✅ |  |
| Radiação | Brasil | 2021-2025 | ERA5-Land, GLDAS, TerraClimate | × 1.039 | sim | - | ✅ |  |
| Radiação | Centro-Oeste | 1961-1970 | ERA5-Land, TerraClimate | × 0.957 | não | - | ❌ |  |
| Radiação | Centro-Oeste | 2021-2025 | ERA5-Land, GLDAS | × 1.027 | não | - | ❌ |  |
| Radiação | Nordeste | 2021-2025 | ERA5-Land, GLDAS, TerraClimate | × 1.040 | sim | - | ✅ |  |
| Radiação | Norte | 2001-2010 | GLDAS, TerraClimate | × 0.954 | sim | 1961-1970 (era5); 1971-1980 (era5) | ❌ |  |
| Radiação | Norte | 2021-2025 | ERA5-Land, TerraClimate | × 1.063 | sim | 1981-1990 (terraclimate); 1991-2000 (terraclimate); 2011-2020 (gldas21) | ❌ |  |
| Escoamento total | Centro-Oeste | 1961-1970 | GLDAS, TerraClimate | × 0.557 | sim | 1981-1990 (gldas20); 1991-2000 (gldas20); 1991-2000 (terraclimate) | ❌ | variável do modelo: só relato (M4) |
| Escoamento total | Nordeste | 1961-1970 | GLDAS, TerraClimate | × 1.344 | não | 1981-1990 (gldas20); 1981-1990 (terraclimate); 2021-2025 (terraclimate) | ❌ | variável do modelo: só relato (M4) |
| Escoamento total | Nordeste | 1971-1980 | GLDAS, TerraClimate | × 0.808 | sim | 2001-2010 (gldas20) | ❌ | variável do modelo: só relato (M4) |
| Escoamento total | Nordeste | 1991-2000 | GLDAS, TerraClimate | × 0.878 | não | - | ❌ | variável do modelo: só relato (M4) |
| Escoamento total | Norte | 1961-1970 | GLDAS, TerraClimate | × 1.112 | sim | - | ✅ | variável do modelo: só relato (M4) |
| Escoamento total | Sudeste | 1961-1970 | GLDAS, TerraClimate | × 0.950 | não | - | ❌ | variável do modelo: só relato (M4) |
| Escoamento total | Sudeste | 1981-1990 | GLDAS, TerraClimate | × 0.895 | não | 1991-2000 (gldas20) | ❌ | variável do modelo: só relato (M4) |
| Escoamento total | Sudeste | 2001-2010 | GLDAS, TerraClimate | × 1.159 | sim | - | ✅ | variável do modelo: só relato (M4) |
| Escoamento total | Sudeste | 2011-2020 | GLDAS, TerraClimate | × 1.241 | não | - | ❌ | variável do modelo: só relato (M4) |
| Escoamento total | Sudeste | 2021-2025 | GLDAS, TerraClimate | × 0.801 | não | - | ❌ | variável do modelo: só relato (M4) |
| Escoamento total | Sul | 1991-2000 | GLDAS, TerraClimate | × 0.912 | sim | 1961-1970 (gldas20); 1981-1990 (gldas20) | ❌ | variável do modelo: só relato (M4) |
| Escoamento total | Sul | 2001-2010 | GLDAS, TerraClimate | × 1.110 | sim | 1971-1980 (gldas20); 2011-2020 (gldas20); 2011-2020 (gldas21) | ❌ | variável do modelo: só relato (M4) |
| Escoamento total | Sul | 2021-2025 | GLDAS, TerraClimate | × 0.954 | não | - | ❌ | variável do modelo: só relato (M4) |
| Tmin | Brasil | 1961-1970 | ERA5-Land, GLDAS, TerraClimate | +0.715 | sim | - | ✅ |  |
| Tmin | Centro-Oeste | 1961-1970 | ERA5-Land, TerraClimate | +0.639 | não | - | ❌ |  |
| Tmin | Nordeste | 1961-1970 | ERA5-Land, GLDAS, TerraClimate | +0.882 | não | - | ❌ |  |
| Tmin | Norte | 1961-1970 | ERA5-Land, GLDAS, TerraClimate | +0.776 | não | - | ❌ |  |
| Tmin | Sul | 1961-1970 | ERA5-Land, GLDAS | +0.572 | sim | - | ✅ |  |
| Vento | Nordeste | 1971-1980 | ERA5-Land, TerraClimate | × 0.852 | não | 1981-1990 (gldas20) | ❌ |  |
| Vento | Nordeste | 2011-2020 | ERA5-Land, TerraClimate | × 1.045 | sim | - | ✅ |  |
| Vento | Nordeste | 2021-2025 | ERA5-Land, TerraClimate | × 1.058 | não | 2011-2020 (gldas21) | ❌ |  |
| Vento | Sul | 1961-1970 | ERA5-Land, TerraClimate | × 1.182 | sim | - | ✅ |  |
| VPD | Brasil | 2001-2010 | GLDAS, TerraClimate | -0.083 | sim | - | ✅ |  |
| VPD | Brasil | 2011-2020 | GLDAS, TerraClimate | -0.061 | sim | - | ✅ |  |
| VPD | Centro-Oeste | 2001-2010 | GLDAS, TerraClimate | -0.142 | sim | - | ✅ |  |
| VPD | Centro-Oeste | 2011-2020 | GLDAS, TerraClimate | -0.069 | sim | - | ✅ |  |
| VPD | Nordeste | 1961-1970 | ERA5-Land, GLDAS, TerraClimate | +0.129 | sim | - | ✅ |  |
| VPD | Norte | 2001-2010 | GLDAS, TerraClimate | -0.118 | sim | - | ✅ |  |
| VPD | Norte | 2011-2020 | GLDAS, TerraClimate | -0.050 | sim | - | ✅ |  |
| VPD | Sudeste | 2001-2010 | GLDAS, TerraClimate | -0.085 | sim | - | ✅ |  |

**Passaram (variáveis do BR-DWGD): 20 de 34.** Chuva Brasil 2021-2025; Chuva Centro-Oeste 2021-2025; Chuva Nordeste 2021-2025; Chuva Sudeste 1981-1990; Chuva Sudeste 2021-2025; Chuva Sul 2021-2025; Radiação Brasil 2021-2025; Radiação Nordeste 2021-2025; Tmin Brasil 1961-1970; Tmin Sul 1961-1970; Vento Nordeste 2011-2020; Vento Sul 1961-1970; VPD Brasil 2001-2010; VPD Brasil 2011-2020; VPD Centro-Oeste 2001-2010; VPD Centro-Oeste 2011-2020; VPD Nordeste 1961-1970; VPD Norte 2001-2010; VPD Norte 2011-2020; VPD Sudeste 2001-2010
