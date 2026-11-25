# REVISÃO FINAL DO PACOTE v4.1 (20/10/2026, noite)

Esta revisão parte do pacote v4.1 que você me enviou (`Downloads.rar`) e prevalece sobre os CHANGELOG anteriores quando houver divergência.

Cada arquivo foi conferido de três formas:
- todos os testes do pacote rodados de novo;
- checagem estática de todos os scripts (compilação Python, `node --check` e busca de nomes indefinidos);
- leitura do código das partes que gravam ou decidem algo.

Resultado: **só uma decisão de método precisava mudar**, a da Tmax e da Tmin da previsão. Ela levou junto o texto do roteiro, a auditoria 08 (que agora confere o método gravado) e dois testes.

## 1. Arquivos alterados

| Arquivo | O que mudou | Por quê |
|---|---|---|
| `05a_motor_sab_v1_5_SIMULACAO.py` e `05b_motor_sab_v1_5_GRAVACAO.py` | `METODO_TEMP_GFS = 'variancia'` (antes `'aditivo'`), com o comentário e o cabeçalho atualizados. A frase final da PRÉVIA 6 ganhou um caso novo: com a variância em uso, se só o aditivo passar no teste dos poucos dias da prévia, ela **não** manda voltar ao aditivo, mas sim parar e enviar a saída. | Validação K8 (ver item 3). Sem o caso novo, a prévia poderia mandar desfazer a escolha com base em 1 a 4 dias. |
| `08_auditoria_completa_SAB.py` | D14 confere que todo dia GFS V1.5 foi gravado com `metodo_temp_gfs = 'variancia'` (constante `METODO_TEMP_GFS_ESPERADO`; o inventário de 2026 passa a ler essa propriedade). | Garantir que a escolha chegou de fato ao banco. |
| `00_ROTEIRO_FINAL.md` | Método já decidido (nenhum arquivo a editar na 5a); etapa 5a e 5b conferem `variancia`; nota 6 e tabela A.3 com os números da K8; **regra nova: rode um script de cada vez** (erro 429); D14 na etapa 8; nome do zip e pasta de antigos na etapa 0.1; lista de conferência. | Coerência com a decisão e com o erro 429 da 1ª K8. |
| `SPEC_V4.md` | Padrão `'variancia'` no contrato de `metodo_temp_gfs`. | Contrato. |
| `testes/teste_05.py` | Espera `'variancia'`; uma única linha da constante e nenhuma com `'aditivo'`; o caso novo da frase da PRÉVIA 6; `precisa_refazer_gfs` testado com o método em uso. **198 verificações, 12 de 12 OK.** | Cobertura da mudança. |
| `testes/teste_08.py` | Inventário com `metodo_temp_gfs`; contrato exige `'variancia'`; dia gravado com o aditivo ou sem a propriedade é acusado. **Todos passaram.** | Cobertura da mudança. |
| `SHA256SUMS.txt` | Regenerado. | Integridade. |
| `CHANGELOG_REVISAO_FINAL.md` | Este arquivo (novo). | Registro. |

## 2. Arquivos conferidos e mantidos sem nenhuma mudança (byte a byte iguais ao v4.1)

| Arquivo | O que foi conferido |
|---|---|
| `01a_mascara_qualidade_SIMULACAO.py` e `01b_mascara_qualidade_GRAVACAO.py` | Diferem só na linha 1 e em `SIMULAR`. Classes A, B, C e D; B pela união de 5 dias; estrutura idêntica nos 5 dias; separação de C pelo centro do pixel (3 métodos); exportação uint8 com pirâmide pela moda e conferência depois de gravar. `teste_01` e `teste_01_uniao` OK. |
| `02_auditoria_roni_cpc.py` | Conciliação tabela x arquivo do CPC (empate, revisão nas 3 últimas estações, estação nova); troca `_TMP` → principal com `_ANTERIOR` guardado até a leitura de volta; recuperação de troca interrompida; ACL lida, reaplicada e comparada; restauração se a conferência falhar. `teste_02` e `teste_02_troca` OK. |
| `03_matriz_gfs_v2_1.py` | Só GFS v16 desde 23/03/2021; 12 tarefas com 100 bandas; travas contra versão conflitante e tarefa na fila. Contrato idêntico ao do 04 e do 08. Máximos de pares conferidos de forma independente (`maximos_pares_v16.py` = tabela do 04 e do roteiro). `teste_03`: 636 verificações OK. |
| `04_conferencia_matriz_gfs.js` | 100 bandas na ordem do contrato, propriedades V2.1, pares mínimos, fatores com os mesmos limites do motor. `teste_04`: 35 verificações OK. |
| `06_painel_sab_2026_10_4.js` | Máscara de qualidade, RONI_CPC_v6, colunas novas no fim do CSV, `Confianca_Prazo` com os mesmos valores que o motor grava. `teste_06_colunas` OK; `teste_06_enso`: 52 de 52. Fumaça com Earth Engine simulado: 0 erros de nome. O painel não precisa ler `metodo_temp_gfs`. |
| `07a_normais_CONFERIR_1991_2020.py` e `07b_normais_CONFERIR_1961_1990.py` | Diferem só na linha 1 e no período. `MODO_CONFERENCIA = True` bloqueia toda escrita (`Task.start`, criar, apagar, renomear, copiar, ACL). `teste_07` OK. Não tocam no `Código baselines.txt`. |
| CHANGELOGs anteriores, testes 01, 02, 03, 04, 06, 07, `fumaca_08_01.py`, `maximos_pares_v16.py` e `testes/dados/` | Sem mudança. `fumaca_08_01` OK. |

**Histórico 1961–2025:** nenhuma linha que protege o histórico foi tocada. Continuam `PROTEGER_HISTORICO = True`, `DATA_LIMITE_PROTECAO = '2025-12-31'` e `CONVERTER_EM_DEFINITIVO = False`, conferidos pelo `teste_05`.

## 3. Por que a variância (K8 refeita como a matriz calcula)

Na revisão, refiz a conta da K8 com as estatísticas de treino **mês a mês**, que é como a matriz V2.1 as calcula; a K8 original usava uma janela de 3 meses. Os dados são os de 2025, fora do treino: 300 pontos e 146.400 previsões.

| | Aditiva | Variância (adotada) | Observado |
|---|---|---|---|
| MAE da Tmax | 1,99 °C | **1,58 °C** | |
| Tmax acima de 35 °C | 17,8% | **12,4%** | 11,6% |
| Tmax acima de 40 °C | 0,28% | **0,08%** | 0,10% |
| MAE da Tmin | 1,070 °C | 1,085 °C | |
| Noites abaixo do P10 | 9,1% | 9,2% | 9,3% |

- Na Tmax, a diferença de MAE é de −0,41 °C (IC 95% de −0,45 a −0,37; bootstrap por dia, 122 dias), com ganho nos 4 prazos (1, 3, 8 e 13 dias).
- Na Tmin há empate prático: +0,015 °C de MAE, contra uma Tmin um pouco mais fiel na cauda fria. Não compensa ter um método diferente para cada variável.
- Com a janela de 3 meses da K8 original: variância 1,540 °C, quantis 1,546 °C e aditiva 1,972 °C.
- A razão dos desvios bate no limite [0,5; 2] em 12% dos casos da Tmax. O limite quase não muda o resultado: MAE de 1,582 °C com ele e 1,575 °C sem ele.

## 4. Pontos que continuam em aberto (não são erro de código)

- `system:time_start` na tabela do RONI: continua A CONFIRMAR na primeira gravação real. O roteiro já aceita esse ⚠️.
- Formato que o `ee.data.setAssetAcl` aceita na versão do Colab: o 02 tenta os dois formatos e avisa se nenhum der certo.
- Troca do `_TMP` no motor (apagar e renomear): não é atômica, mas a execução seguinte recupera. Mantida.
