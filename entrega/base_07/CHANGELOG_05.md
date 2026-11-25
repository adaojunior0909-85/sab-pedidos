# CHANGELOG 05: motor SAB

## 09/11/2026: V1.6 no GitHub e auditorias K23 v2 e K24 v1 (sem mudança no motor)

| Peça | Versão | O que mudou |
|---|---|---|
| motor no GitHub | V1.6 | E2-5 feito: arquivos conferidos com o pacote; execução *simular* com a mesma prévia do Colab. 1ª gravação na noite de 09/11 |
| `validacoes/K23_auditoria_emenda_tmax.py` | v2 | Rodada em 09/11 (2 min): emenda normal pixel a pixel; ponto quente da Tmax do GFS em Roraima acima do recorde do pixel (rota GFS da V1.5) |
| `validacoes/K24_auditoria_tmax_gfs.py` | v1 (novo) | Só leitura: Tmax do GFS x recorde do pixel (BR-DWGD, mesmo mês, 1991-2025) no Brasil todo, contra os últimos 30 dias ERA5; pontos quentes; GFS bruto recuperado pela inversa da calibração; tabela de teto (folga 0, 1, 2 °C). Regras P1/P3 e folga fixadas antes de rodar. Base da V1.7 |
| `testes/teste_k24.py` | novo | Janela do motor, agregação, P1, inversa da calibração (com limites da razão), escolha da folga |
| `validacoes/K22_conferencia_v16.py` | v2 | Sem mudança; data de uso: 11/11 |

## 08/11/2026: V1.6 revista depois da K21 v3a e motor uma vez por dia (23h07)

| Peça | Versão | O que mudou |
|---|---|---|
| `05a/05b_motor_sab_v1_6_*.py` | V1.6 (revista) | `METODO_UR_VENTO_ERA5` virou duas chaves: `METODO_UR_ERA5 = 'eqm'` e `METODO_VENTO_ERA5 = 'media'`. O vento dos dias ERA5 volta à correção na média da V1.5 (a K21 v3a reprovou o EQM do vento: viés +0,085 → +0,107 m/s, limite 0,10). Propriedade `metodo_ur_vento_era5` = `'UR eqm; vento media'`. Marca `f_solo` da prévia só com as bandas do EQM (UR). Matriz EQM (09) sem mudança: os quantis do vento ficam sem uso. SHA-256: 05a `de4baea7…`, 05b `e6c66b94…` |
| `SHA256_MOTOR.txt` | V1.5 e V1.6 | SHA novos da V1.6; V1.5 igual |
| `rodar_motor.py` | 2026.11.08 | Só textos e `VERSAO` (o horário fica no workflow) |
| `.github/workflows/motor_05b.yml` | 2026.11.08 | Uma rodada por dia: `cron: '7 2 * * *'` (23h07 de Brasília). Serve para a V1.5 (lançador 2026.11.01, no ar) e para a V1.6. Artefato da simulação passa a se chamar `previa` e leva `previa_v15.csv` e `previa_v16.csv` (antes só o da V1.5: a prévia da V1.6 não seria guardada) |
| `README.md` (sab-motor) | 2026.11.08 | Horário e V1.6 revista |
| `testes/teste_05_v16.py` | — | Contrato novo (UR eqm, vento media, propriedade) |

## CHANGELOG 05: motor SAB V1.5 (05a/05b), pacote v4 de 20/10/2026

> **Revisão posterior (20/10/2026, tarde):** as auditorias independentes A e B pediram correções neste escopo. Elas estão em `CHANGELOG_REVISAO_AB.md`, que prevalece em caso de divergência.

## Arquivos

| Arquivo | Situação |
|---|---|
| `05a_motor_sab_v1_5_SIMULACAO.py` | Renomeado com `mv` do `05a_motor_sab_v1_4_SIMULACAO.py` e editado (1.421 → 1.946 linhas) |
| `05b_motor_sab_v1_5_GRAVACAO.py` | Gerado do 05a final por `sed`: só a linha 1 (comentário) e a linha 109 (`SIMULAR = False`) mudam |
| `05b_motor_sab_v1_4_GRAVACAO.py` | Apagado da pasta v4 |
| `testes/teste_05.py` | Novo: 11 testes, 169 verificações, sem Earth Engine |

As linhas abaixo valem para o 05a e para o 05b, que têm o mesmo número de linhas. Todo trecho novo ou alterado está marcado com `# [V4 <ID>]`. O cabeçalho (linhas 5-34) traz o bloco "MUDANÇAS V4 (20/10/2026)".

## Validação feita

- `py_compile` e `pyflakes` sem nenhum aviso no 05a, no 05b e no teste.
- `python3 testes/teste_05.py`: 11 de 11 testes OK. As funções e constantes são extraídas do próprio 05a por `ast`, sem cópia à mão.
- `diff 05a 05b`: só as linhas 1 e 109 diferem. O teste `teste_05a_05b` confere isso.
- Diff completo relido contra `/home/claude/sab/v3_zip/05a_motor_sab_v1_4_SIMULACAO.py`. Nada fora da lista mudou.
- Mensagens citadas pelo roteiro, todas presentes (o teste `teste_mensagens` confere):
  - `MODO SIMULAÇÃO ATIVO`
  - `TRAVA DO HISTÓRICO LIGADA`
  - `RESUMO DA SIMULAÇÃO`
  - `PRÉVIA 2`, `PRÉVIA 3`, `PRÉVIA 5`
  - `Todos os critérios atendidos`
  - `PROTEGIDOS: nenhum dia`
  - `Vagas restantes na fila`
  - `não tem os meses`
  - `Execução encerrada`
  - `deve ficar igual`
  - `criar (GFS)` e `-> GFS`
- **`previa_v14.csv` passou a ser `previa_v15.csv`** (constante `ARQUIVO_PREVIA`, linha 207). O roteiro (etapa 5a, item 4) precisa ser atualizado.
- O Earth Engine não foi executado. Cada chamada foi revisada contra os padrões que o código já usa. As exceções estão em "A CONFIRMAR".

---

## Itens

### [V4 B1 / M05-08] Só rodadas 00Z completas
- **Linhas:**
  - constantes 146-151 (`MS_DIA`, `PRAZO_MAX_GFS`, `HORAS_RODADA_COMPLETA`, `N_SAIDAS_RODADA` com `assert == 208`);
  - `eh_rodada_00z` 759;
  - `selecionar_rodadas` 763-773;
  - `rodada_para_dia` 807-815;
  - `descobrir_rodadas_gfs` 1191-1228;
  - `executar_cadeia_gfs` 1249-1296.
- **O que mudou:**
  - Só entram rodadas com `creation_time % 86.400.000 == 0`.
  - Rodada completa = as 208 saídas de 1 a 384 h (120 horárias, 40 de 3 h até 240 h e 48 de 3 h até 384 h), sem a hora 0.
  - Uma só consulta (`ee.List(rodadas_00z).map(...)`) conta, em todas as rodadas 00Z da janela, as horas distintas dentro da lista esperada.
  - A referência é a 00Z completa mais recente.
  - Sem nenhuma completa, sai um ⚠️ e a cadeia GFS não roda; os dias existentes ficam como estão. Antes havia `RuntimeError` ou o uso da rodada incompleta.
  - Dias passados usam a 00Z do próprio dia, se estiver completa. Se não estiver, usam a 00Z completa anterior mais recente que ainda cubra o dia (prazo ≤ 16), como pede o M05-09.
  - Se nenhuma rodada cobrir um dia, a cadeia para nesse dia com ⚠️, porque o balde não pode pular um dia.
- **Como o código contava antes:**
  - `stats['n'] >= 198`, com `n = colecao_gfs_rodada(r).size()`, conta todas as imagens da rodada, inclusive a hora 0. Uma rodada completa tem 209 (F_gfs_horas_por_epoca.csv).
  - Faltando até 11 saídas, a rodada ainda passava.
  - Eram examinadas só as 4 últimas rodadas, de qualquer horário, com um `getInfo` por rodada.
- **Por quê:**
  - O 03 só usa rodadas 00Z.
  - Com 12Z, o 1º dia tem 12 h e 2 blocos (teste `teste_contagem_por_prazo`), e o prazo deixa de bater com as faixas da matriz. A revisão_03_04 trata disso no item M05-01.
- **Verificar no log:**
  - nova linha `🛰️ Rodadas 00Z na janela (...): N | completas (208 saídas de 1 a 384 h): K | incompletas: ...`;
  - `Rodada GFS de referência: AAAA-MM-DD 00Z`;
  - nos dias exportados, `rodada ... 00Z, prazo L.., faixa ..`.

### [V4 B1-horizonte / M05-28] Fim da cadeia e prazo 16
- **Linhas:** comentário 139-143 (o comentário errado "o 16º dia nunca fica completo" foi substituído), 216, `fim_horizonte` 801-805, `faixa_prazo` 780-791 (docstring), `executar_cadeia_gfs` 1262-1270.
- **O que mudou:**
  - `data_fim_processo = min(hoje + 15, dia da referência + 15)`, calculado depois de descobrir a referência.
  - O último dia é o prazo 16 (horas 361-384): completo com rodada 00Z (8 saídas e 4 blocos) e calibrado com a faixa L11a15, por extrapolação. Isso está documentado no código.
- **Verificar:** `📆 Dias GFS: ... o último é o prazo L16 da referência`.
- **Efeito colateral:** se a 00Z de hoje ainda estiver incompleta, a referência é a de ontem e o horizonte termina em hoje + 14. Um dia hoje + 15 gravado por uma execução antiga fica como está até a execução seguinte.

### [V4 B6 / M05-10 / M05-02 do relatório 03_04] Dias incompletos
- **Linhas:** 193-194 (`BANDAS_MASCARADAS_INCOMPLETO`), 859-873 (`img_chuva_balde`; radiação sem média simples), 918-931 (`pr_balde`, `rs_balde` e ETo do balde), 949-951 (balde com `pr_balde`), 982-986 (máscara na saída).
- **O que mudou:**
  - No dia `provisoria_gfs_incompleta`, `pr_mm`, `rs`, `et_potencial`, `et_real` e `transpiracao_mm` saem mascaradas.
  - O balde usa a chuva escalada por 4/n (média dos n blocos × 4) ou 0 sem blocos.
  - Acabou o recurso `gfs_dia...downward_shortwave_radiation_flux.mean()`. Sem nenhum bloco, a radiação fica mascarada e a ETo **só do balde** usa `Rs_m_sicsb_{faixa}`, a radiação média do BR-DWGD na matriz.
  - Em dia completo, `pr_balde = pr` e `rs_balde = rs` exatamente.
- **Por quê:** a matriz só usa dias completos. A média simples de radiação foi condenada pelo F4. A soma parcial subestima a chuva.
- **Verificar:** nenhum dia `provisoria_gfs_incompleta` com `rs` válido. Com rodadas 00Z completas, nenhum dia deve sair incompleto.
- **A CONFIRMAR (decisão de projeto):** a radiação climatológica no balde quando o dia não tem bloco nenhum. O caso é praticamente inalcançável com o B1.

### [V4 M05-11] Duplicatas e contagem exata
- **Linhas:** `colecao_gfs_dia` 740-757, extraída de `processarDia_GFS` para a PRÉVIA 6 usar a mesma seleção; `completo` 838-844.
- **O que mudou:**
  - `ee.ImageCollection(saidas.distinct('forecast_hours'))` antes do `resample`.
  - `completo = qtd_img.eq(n_img_esperado).And(qtd_chuva.eq(len(horas_chuva)))`, no lugar de `gte`, como no 03.
- **A CONFIRMAR:** `Collection.distinct` no cliente Python devolve um FeatureCollection. O `ee.ImageCollection(...)` só refaz o tipo para o `map`. Ver no 1º dia exportado `Imagens_Validas_GFS == Imagens_Esperadas_GFS` (24 ou 8).

### [V4 M05-09] Refazer dias incompletos ou com falha
- **Linhas:** `precisa_refazer_gfs` 817-825, chamada em 1300.
- **O que mudou:** um dia com a mesma rodada e a mesma versão, mas gravado como `provisoria_gfs_incompleta` ou `falha_latencia_gfs`, é refeito quando o dia tem os 4 blocos esperados. A escolha da rodada completa está no B1.

### [V4 B3 / M05-07] Conferência da matriz V2.1
- **Linhas:** 195-197, 736-738 (`BANDAS_MEDIA_GFS`, 48 nomes), 1024-1055.
- **O que mudou:**
  - A mensagem `❌ A matriz ... não tem os meses ...` continua (o roteiro a cita).
  - Em seguida, um único `getInfo` lê `bandNames()` e `toDictionary()` dos 12 meses.
  - O motor exige as 48 bandas `{v}_m_{sicsb|gfs}_{fx}` e `versao_matriz == 'V2.1'`. Se faltar algo, para com `RuntimeError("❌ ...")`, que lista mês a mês o que falta.
  - As bandas lidas preenchem o cache de `bandas_matriz_gfs`, o que elimina um `getInfo` por mês na cadeia.
- **Verificar:** linha `✅ Matriz GFS V2.1: 12 meses com as 48 bandas de média (modelo GFS v16, rodadas desde 2021-03-23, dias até 2025-12-31)`.
- **Coerência com o 03 novo (`03_matriz_gfs_v2_1.py`):** conferi os nomes das bandas, `VARS`, `versao_matriz`, `modelo_gfs`, `inicio_rodadas` e `fim_dias`. Batem.

### [V4 B4 / M05-05] `CRIT_SOLO_BRASIL = 2.0`
- **Linha:** 1382. A PRÉVIA 5 passa a mostrar `limite ±2%`, como o roteiro (etapa 5a, item 3) e o D13.

### [V4 B5 / M05-04] `CONVERTER_EM_DEFINITIVO = False`
- **Linhas:** 134-137, `limite_definitivo` 271-274, `dias_aguardando_decisao` 276-280, 297-306 (aviso), `status_dia` 1080-1082, rota 1165 e 1180, `executar_previa` 1807, `inicio_janela` 1899-1902.
- **O que mudou:**
  - `limite_def = ultima_data_brd if CONVERTER_EM_DEFINITIVO else min(ultima_data_brd, DATA_LIMITE_PROTECAO)`.
  - Esse limite é usado em `status_dia`, na escolha da rota (simulação e gravação), na janela operacional e na prévia.
  - Com False, nenhum dia depois de 2025-12-31 vira `definitiva`.
  - Aviso no início: `⏸️ BR-DWGD já cobre até X: N dias aguardam decisão (...)`.
- **Verificar:** hoje (BR-DWGD até 2025-12-31) o aviso não aparece. Os testes cobrem BR-DWGD até 2026-06-30 nos dois valores da opção.

### [V4 C1 / M05-01 e M05-02 do relatório do motor] Rota definitiva
- **Linhas:** 632-636 (`valido_br`), 649-652 (`.max(0)`), 655-668 (montagem).
- **O que mudou:**
  - Máscara `pr`, `Tmax` e `Tmin` `.gt(-32768)`, que exclui o -32768 e o dummy -99999.
  - `et_potencial`, `rs` e `u2` do BR-DWGD com `.max(0)`.
  - Montagem com o BR-DWGD primeiro: `br[b].updateMask(valido_br).unmask(era_cheia.select(b), sameFootprint=False)`.
  - Documentado no código: o histórico V1.0 tem 204 pixels (classe B da J1) com esse defeito, tratados na leitura pela máscara de qualidade (classe 2). A trava continua fechada.
- **Diferença do código proposto no relatório:** `sameFootprint=False`. Com o padrão (True), a saída ficaria com a pegada do BR-DWGD, cuja grade começa em -73,9° e não inclui as ilhas oceânicas, e pixels de borda que hoje vêm do ERA5 sumiriam.
- **Bandas que não são do BR-DWGD:** não mudam (`era_cheia` = o `fallback` antigo).
- **Efeito hoje:** nenhum. Com `CONVERTER_EM_DEFINITIVO = False` e a trava, a rota definitiva não roda.
- **A CONFIRMAR:** a união de pegadas com `sameFootprint=False`, no primeiro dia definitivo novo (D9 na grade inteira, como sugere o relatório).

### [V4 C2 / M05-03] Máscara canônica
- **Linhas:** 205-206, 234-235, 266-269 (`MASCARA_SAB`, global, lida uma vez), 540-549 (`finalizar`), 1057-1060 (o motor para se `SAB_2025_12_31` não existir).
- **O que mudou:** `finalizar` aplica `.updateMask(MASCARA_SAB)`, que é a máscara de `pr_mm` de `SAB_2025_12_31`, **no lugar** de `.clip(poligonoBrasil)`.
- **Por que tirei o clip (decisão para o auditor):**
  - O clip não é necessário para a pegada: a exportação usa `region=limitesRegiao` e a máscara já contém o recorte GAUL, porque o dia de referência foi gravado com esse clip.
  - Manter os dois poderia aplicar duas vezes a fração de borda, se `updateMask` multiplicar máscaras fracionárias.
  - Sem o clip, com a máscara própria da imagem igual a 1, o resultado é a máscara de referência sob qualquer regra de combinação.
  - Para voltar atrás, basta acrescentar `.clip(poligonoBrasil)` antes do `updateMask` na linha 549.
- **Efeito esperado:**
  - os dias GFS perdem os cerca de 4 pixels extras do D10;
  - a umidade do solo do GFS deixa de crescer 1 pixel por dia;
  - a cobertura dos dias ERA5 e definitivos fica igual à de hoje;
  - também reduz custo (M05-30).
- **A CONFIRMAR:** como `updateMask` combina máscaras fracionárias. Verificar no D10 do 08 com mínimo = máximo = 70454,976 em todos os dias V1.5 (ERA5 e GFS).

### [V4 C4 / M03-15] Calibração da rota GFS (a rota ERA5 não muda)
- **Linhas:** constantes 166-173, `calib_chuva_gfs` 478-482, `calib_limitada_gfs` 484-486, uso em 905-916.
- **O que mudou:**
  - Chuva: fator `(m_sicsb + 0,1)/(m_gfs + 0,1)` com teto `FATOR_MAX = 5` (`K_CHUVA_MM = 0.1` mm/dia).
  - Vento e radiação: fator da V1.0 limitado a [0,5; 2,0] (`FATOR_MIN_UV_RS`, `FATOR_MAX_UV_RS`).
  - Tmax, Tmin e UR continuam aditivas.
  - `calib_multiplicativa` não mudou e continua sendo a usada pela rota ERA5.
- **Por quê:** a J4 mediu, na matriz V1, julho, p95 = 13,3 e p99 = 59,2 para o fator de chuva. Fator 5 em vento ou radiação é fisicamente impossível.
- **Verificar:** na PRÉVIA 6, a coluna "Chuva média mm" do GFS V1.5 contra o dia gravado (V1.3).

### [V4 B8 / M05-17] Propriedades novas (contrato)
- **Linhas:** 198-204 (constantes), definitivos 675-676, ERA5 686-687, GFS 1006-1009, `confianca_prazo` 793-799.
- **O que mudou:**
  - Dias GFS: `Confianca_Prazo` ('alta' L1-5, 'media' L6-10, 'baixa' L11+), `fonte` = 'NOAA/GFS0P25 (rodada 00Z)', `janela_chuva_utc` = '00-24' e `matriz_gfs` = 'SICSB_MATRIZ_GFS_V2 V2.1'.
  - Dias ERA5: `fonte` = 'ECMWF/ERA5_LAND/DAILY_AGGR' e `janela_chuva_utc` = '00-24'.
  - Definitivos: `fonte` = 'BR-DWGD (ERA5 só onde falta)' e `janela_chuva_utc` = '12-12 (12 UTC D-1 a 12 UTC D)'.
  - Os valores de `versao` são os de sempre.
- **Verificar:** as propriedades de um dia exportado no Asset Manager.

### [V4 M05-22] Versão V1.5
- **Linhas:** 105, 119-121 (`'V1.5'` na tupla e `assert VERSAO_ALGORITMO in ALGORITMOS_DEFINITIVOS_VALIDOS`), 1888-1894 (avisos ⚠️ quando `APLICAR_PATCH_SOLO` ou `REPROCESSAR_VERSAO_ANTIGA` estão ligados junto com a trava).
- **Provisórios recalculados:** os ERA5 V1.3 e V1.4 têm `alg != 'V1.5'` e vão para `precisa_upgrade` pela rota ERA5. Os GFS são refeitos pela cadeia (`alg` diferente). Ver `teste_conversao_definitivo`.
- **Histórico:** nada até 2025-12-31 é tocado.
  - A trava (`dia_protegido`, `PROTEGER_HISTORICO and d <= DATA_LIMITE_PROTECAO`) e o relatório PROTEGIDOS ficaram iguais.
  - Agora `promover_tmp` e `exportar` também conferem a trava (ver M05-19).
- **Rótulos da prévia:** passaram a usar `VERSAO_ALGORITMO`: `Umid 0-5 V1.5`, `muda na V1.5`, `V1.5 (% pixels)` etc. `deve ficar igual` e `ΔUmid ... %` não mudaram.

### [V4 B2 / M05-06] PRÉVIA 6: rota GFS em memória
- **Linhas:** `contexto_gfs` 1246-1247, preenchido na cadeia; 1627-1804 (`dias_previa_gfs`, `_estado_previa_gfs`, `_nacional_gfs`, `executar_previa_gfs`, `_imprimir_previa_gfs`, `_previa_gfs_sozinha`); integração em 1813-1880.
- **O que faz:** sem exportar nada, calcula com `processarDia_GFS` o 1º dia GFS e os dias de prazo L2 e L11 da referência.
- **Por que não encadeia o balde:**
  - Encadear 10 dias em memória seria pesado.
  - Todos os dias partem do estado do último dia ERA5, recalculado em memória.
  - Chuva, Tmax, radiação e ETo não dependem do balde, então os números comparados são exatos.
- **O que imprime:** em um pedido por dia (`reduceRegion` com média e máximo combinados), a média e o máximo nacionais de Tmax e as médias de chuva, Rs e ETo para:
  - o dia V1.5;
  - o dia gravado na mesma data (hoje V1.3);
  - o último dia ERA5;
  - só no 1º dia, a Tmax máxima do **GFS bruto** (J6).
- **Critérios (⚠️ se falhar):**
  - dia completo (`provisoria_gfs`);
  - Tmax máxima nacional ≤ 44,8 °C, o recorde do INMET;
  - |salto da Tmax máxima nacional do último ERA5 para o 1º GFS| ≤ 2 °C.
- **Informativos (ℹ️):**
  - razão Rs V1.5/gravado;
  - Tmax bruto → calibrado, com a leitura "bruto já acima do recorde = viés do modelo; só o calibrado acima = efeito da calibração".
- **Veredito:**
  - As falhas entram na lista da PRÉVIA 5 com o prefixo `rota GFS (PRÉVIA 6):`. A PRÉVIA 5 ganha uma linha avisando disso, e a PRÉVIA 6 é impressa logo depois.
  - O 1º dia é obrigatório. Os outros dois, se não forem calculados, só geram um aviso (como a tolerância da prévia ERA5); se forem calculados, entram nos critérios.
  - Sem dias V1.3 para a prévia ERA5, a PRÉVIA 6 roda sozinha, com veredito próprio: `✅ Critérios da rota GFS (PRÉVIA 6) atendidos.`.
  - Os critérios das PRÉVIAS 1-4 não mudaram. Só o limite de solo mudou para ±2% (B4).
- **A CONFIRMAR:** memória e tempo do `reduceRegion` nacional (tenta `tileScale` 4 e depois 16).

### [V4 M05-19] Promoção do TMP e trava em `exportar`
- **Linhas:** `versao_tmp_aceita` 364-366, `promover_tmp` 368-390, simulação 405-427, `exportar` 1100-1102.
- **O que mudou:**
  - Antes de promover, o motor confere a trava e depois `versao_algoritmo` do TMP.
  - Se a versão não for a atual nem `VERSAO_PATCH`, o TMP é apagado (`🧹 ...`) e o dia é refeito pelo fluxo normal.
  - Na simulação aparece `Seriam apagados da coleção temporária ...`.
  - `exportar` levanta `❌ Trava do histórico` se receber um dia protegido.
  - O mecanismo apagar + renomear foi mantido; `copyAsset` não é usado.
- **Por que `VERSAO_PATCH` também é aceita:** os TMP do patch (opção `APLICAR_PATCH_SOLO`) gravam `versao_algoritmo = 'V1.0-P12'`. Sem essa exceção, o patch seria apagado em vez de promovido.
- **Fechou uma brecha:** `aguardar_dia_pronto` promovia sem conferir a trava.

---

## Fora do escopo da V1.5 (não feitos)
- M05-12: interpolação mensal da calibração.
- M05-16 e V3: janela de chuva 12-12 UTC no ERA5 e no GFS.
- ERA5 horário (M05-18 e M05-24).
- Constantes do FAO-56 na equação de Magnus (M05-23).
- Qualquer outra mudança na rota ERA5 além das propriedades. M05-26 (Tmax ≥ Tmin no ERA5) e M05-14 (escoamento) também não foram feitos.
- M05-13 (interpolação entre prazos), M05-15, M05-20, M05-21, M05-31 a M05-35 (o 05b continua gerado por `sed`, não por fonte única com hash).

## Impacto no roteiro e em outros arquivos (para o coordenador)
- Etapa 5a, item 3:
  - a linha esperada passa a ser `recalcular provisoria_era5 V1.3 -> provisoria_era5 V1.5`;
  - aparecem linhas novas: `✅ Matriz GFS V2.1 ...`, `🛰️ Rodadas 00Z na janela ...`, `📆 Dias GFS ...`, `🔎 PRÉVIA GFS V1.5 ...` e a PRÉVIA 6;
  - o critério ±2% agora coincide com o código.
- Etapa 5a, item 4: o arquivo passa a ser `previa_v15.csv`.
- Etapas 5a e 5b: os nomes dos arquivos e do notebook (`05_motor_v14`) citam V1.4.
- Etapa 6.3 (painel): "no último dia, `Previsao_GFS_Parcial`" deixa de ser esperado, porque com a rodada 00Z o prazo 16 fica completo. A `Versao_Algoritmo` passa a ser `V1.5`.
- Etapa 8 (08, D7): esperar `provisoria_era5 | V1.5` e `provisoria_gfs | V1.5`.
- 03: se a coleção `SICSB_MATRIZ_GFS_V2` tiver meses sem `versao_matriz = 'V2.1'`, o motor para com ❌. É preciso apagá-los antes de rodar o 03 V2.1.

## Riscos
1. **A PRÉVIA 6 pode reprovar a 5a.** Tmax acima de 44,8 °C ou salto acima de 2 °C entram no veredito. A J5 mostra que os dias GFS V1.3 falhariam nos dois. Se o viés vier do próprio GFS, a matriz V2.1 pode não bastar. Nesse caso o usuário recebe "NÃO EXECUTE AINDA" e a linha J6 (bruto x calibrado) diz de onde vem o problema.
2. A calibração nova do GFS (C4) não foi validada contra dados. Não há critério sobre chuva; a PRÉVIA 6 só mostra a média.
3. Previsão até 18 h mais velha (só 00Z). Se a 00Z do dia atrasar, a cadeia usa a de ontem e o horizonte encolhe 1 dia.
4. Um dia passado sem nenhuma 00Z completa que o cubra interrompe a cadeia ali. Os dias seguintes ficam com a versão anterior até uma execução em que a rodada exista.
5. Máscara canônica sem o clip (C2): depende do comportamento de `updateMask` com máscara fracionária. A conferência é o D10.
6. A simulação faz um `getAsset` por item do TMP (M05-19). É pouco, salvo se houver muitas sobras.

## A CONFIRMAR (em execução)
- `updateMask(MASCARA_SAB)` com máscara fracionária. Esperado: D10 = 70454,976 em todos os dias V1.5.
- `ee.ImageCollection(col.distinct('forecast_hours'))`: tipo e resultado. Esperado: `Imagens_Validas_GFS == Imagens_Esperadas_GFS`.
- Contagem das rodadas numa só consulta. Esperado: completas com 208 e a 00Z de hoje parcial enquanto chega. Usa `inList` com horas float, padrão já usado em produção nos blocos de chuva.
- `unmask(..., sameFootprint=False)` na rota definitiva. Só roda quando houver conversão; conferir no D9 da grade inteira.
- Radiação climatológica (`Rs_m_sicsb`) só no balde de um dia sem blocos (B6): decisão de projeto, caso quase inalcançável.
- Memória do `reduceRegion` nacional da PRÉVIA 6.

## V1.6 (04/11/2026, etapa 2): UR e vento por quantis, radiação no céu claro, teto da chuva

Só os dias de 2026 em diante (provisórios ERA5 e previsão GFS). O histórico 1961-2025 continua travado
(`PROTEGER_HISTORICO = True`, `DATA_LIMITE_PROTECAO = '2025-12-31'`); a rota definitiva, `status_dia`, `promover_tmp`,
`precisa_refazer_gfs`, `exportar` e `finalizar` são idênticos à V1.5 (conferido em `testes/teste_05_v16.py`).

- **[V1.6 EQM]** UR e vento dos dias ERA5 pelo mapeamento empírico de quantis (`aplicar_eqm`, 21 quantis da matriz
  `SICSB_EQM_1986_2025`, gerada pelo 09). Interpolação linear entre quantis; fora da faixa, deslocamento constante.
  Pixel sem BR-DWGD (classes B, C e borda) continua com a correção da V1.5 (`unmask`). `METODO_UR_VENTO_ERA5 = 'media'`
  volta à V1.5. Base: K19b (UR desvios 1,24 → 1,03 e erro -22%; vento 1,71 → 1,19 e erro -33%).
- **[V1.6 Rs]** `limitar_rs`: radiação ≤ Rso = (0,75 + 2e-5 z) Ra (FAO-56 eq. 37; `radiacao_ceu_claro`, mesma conta da
  ETo) nos dias ERA5 e GFS. K19: 1.695 pixel-dias de 2026 acima de 1,1 Rso.
- **[V1.6 chuva]** `teto_chuva`: min(chuva corrigida, máx(chuva bruta, 1,5 × `pr_max_br`)) nas rotas ERA5 e GFS. K19:
  546 mm em 2026 em (-55,35; 0,45), com o fator da média até 5x. A chuva continua com a escala da média (o EQM piorou a
  chuva na K19b).
- Prévia nova (`previa_v16.csv`): compara com os dias gravados pela V1.5 (`VERSAO_ANTERIOR`); critérios `CRIT_V16_*`
  (|Δ| da média no Brasil: UR 5%, vento 15%, ETo 10%, radiação 8%, chuva 5%; regiões com o dobro, aprox.); coerência
  nova "radiação acima do céu claro"; escoamento fora do critério "igual" (revisão do ERA5-Land na fonte, K17/K18).
- Propriedades novas: `metodo_ur_vento_era5`, `matriz_eqm`, `teto_chuva_fator`, `rs_limitado_rso`.
- Validação: K21 (fora da amostra), 09a/09b, 05a V1.6, simulação no GitHub, K22 (depois de implantar).
- GitHub `sab-motor`: `rodar_motor.py` 2026.11.05 (roda a V1.6; `SHA256_MOTOR.txt` lista V1.5 e V1.6 para a volta
  ser só o `rodar_motor.py` antigo); `motor_05b.yml` com as rodadas às 06h07 e 15h07 (a das 23h07 começava ~23h49,
  antes da rodada 00Z do GFS chegar, e terminava em 1 min).
