# CHANGELOG da revisão independente do pacote v4 (auditorias A e B, 20/10/2026)

Este arquivo prevalece sobre os outros CHANGELOG quando houver divergência.

> **v4.1 (20/10/2026, tarde):** os ajustes feitos depois das auditorias K e K1d estão em `CHANGELOG_V41.md`, que prevalece sobre este arquivo onde houver divergência.
- **Auditoria A:** 03, 04 e motor 05a/05b.
- **Auditoria B:** 01, 02, 06, 07a/07b e 08.

Os dois revisores não viram a montagem do pacote; leram o código e os testes. Cada achado abaixo foi corrigido no código e coberto por teste offline. Nenhum toca nos dados do histórico (1961–2025) nem abre a trava do motor.

## Achados e o que foi feito

| Nº | Gravidade | Arquivo | Problema | Correção | Teste |
|---|---|---|---|---|---|
| A-01 | Alta | 04 | A conferência media o fator de calibração antigo, que dava ⚠️ falso nos meses secos. | Passa a medir o fator do motor V1.5: chuva (BR+0,1)/(GFS+0,1) com teto 5; vento e radiação limitados a [0,5; 2]. | teste_04 |
| A-02 | Média | 05a/05b | O filtro de horas da rodada usava números decimais. | Usa inteiros, o mesmo formato que funcionou na auditoria J. | teste_05 (2 verificações novas) |
| A-03 | Média | 05a/05b e 08 | Um comentário prometia cobertura igual à do histórico nos dias GFS, mas o código só restringe. | O comentário passa a dizer "cobertura contida". O D10 da 08 trata os dias GFS V1.5 só com pixels faltando como ℹ️; pixel fora da canônica ou fração diferente continua ⚠️. | teste_08 (7 casos novos) |
| A-04 | Baixa | 03 | Cabeçalho, CHANGELOG e testes não registravam o `composto_seguro` nem o Float32. | Registro feito. | teste_03 (636 verificações) |
| B-01 | **Bloqueante** | 01 | A conferência pós-gravação exigia a origem exata do BR-DWGD. O asset exportado guarda a origem da própria região (12 pixels a oeste e ao norte), então uma gravação correta terminaria com ❌. | Nova função `grade_nativa`: aceita escala igual e deslocamento por número inteiro de pixels. | teste_01 e fumaça (gravação simulada com origem deslocada: aceita; meio pixel: recusa) |
| B-02 | Alta | 08 (Q1) | Mesma conta do B-01, que daria ⚠️ falso no Q1 em toda execução. | Mesma `grade_nativa`. | teste_08 e fumaça |
| B-03 | Média | 02 | Se uma restauração anterior tivesse falhado (sobra `RONI_CPC_v6_ANTERIOR` sem o asset principal), a execução seguinte apagaria a única cópia boa. | O `_ANTERIOR` volta ao lugar antes da troca. | teste_02_troca, cenário D (antes terminava sem nenhum RONI) e cenário D2 |
| B-04 | Média | 01 | A comparação com a J1 misturava receitas diferentes. O "~880" da classe 4 vem de soma ponderada por área, não do centro do pixel, então podia bloquear a gravação sem haver erro. | A comparação refaz a receita exata da J1 (soma padrão na caixa dos estados, sem completar o BR-DWGD). A classe 4 vira só ℹ️; a separação 3/4 continua validada pelo teste vetorial do centro. | teste_01 e fumaça (classe 4 = 1.000: só ℹ️) |
| B-05 | Média | 06 | As colunas novas entravam no meio do CSV e mudavam a posição de 28 das 30 colunas antigas. | As colunas novas vão para o fim; as antigas não mudam de lugar. | teste_06_colunas |
| B-06 | Média | 08 (H5) | A falta de `system:time_start` na tabela (ponto A CONFIRMAR) virava ERRO, embora o painel não dependa dele. | Vira ⚠️ com explicação, e a chave do painel é ordenada por `data_ms`. Se o `system:time_start` existir e estiver errado, continua ERRO. | teste_08 |
| B-07 | Média | 07a/07b | O relatório Q1 saía com ⚠️ em toda execução, e o roteiro manda parar diante de ⚠️. | Passa a ℹ️. | teste_07 |
| B-08 | Baixa | 06 | O dicionário do CSV parava na V1.4. | Descreve a V1.5. | teste_06_colunas |
| B-09 | Baixa | 06 | A camada "Área de Cobertura" mostrava pixels de classe 4 que o CSV já exclui. | Usa a mesma máscara dos pontos de extração. | teste_06_colunas |
| B-10 | Baixa | 06 e 02 | (a) O alerta do painel não citava o compartilhamento do App. (b) A contagem do asset gravado ficava fora do `try`. (c) A mensagem de restauração mandava renomear por cima de um asset que ainda existia. | (a) Alerta cita "compartilhe SAB_MASCARA_QUALIDADE". (b) Contagem dentro da conferência. (c) Mensagem manda apagar primeiro. | teste_06_colunas e teste_02_troca, cenário F |

## Mudanças pedidas na coordenação (fila anterior às auditorias)

- **01a/01b:** o 01 foi dividido em `01a_mascara_qualidade_SIMULACAO.py` (SIMULAR = True) e `01b_mascara_qualidade_GRAVACAO.py` (SIMULAR = False). Os dois diferem só na linha 1 (rótulo) e na linha do SIMULAR, o que o teste_01 confere. A simulação termina com `Sem ⚠️: rode o 01b para gravar.`
- **08, seção B2:** passa a listar `SAB_MASCARA_QUALIDADE` entre os assets novos.
- **08, J5:** `J5_CSV_ANTERIOR = '/content/J5_previsao_anterior.csv'` por padrão. Sem o arquivo, J5c sai ℹ️ dizendo onde procurou. A Parte 4 do roteiro manda enviar o CSV com esse nome por volta de 15/11.

## Roteiro e SPEC

- **Roteiro:**
  - legenda dos símbolos (ℹ️ não para);
  - etapa 1 com as mensagens novas;
  - ⚠️ aceitável do `system:time_start` nas etapas 2 e 8;
  - 6.1 com o alerta novo;
  - 6.2 com as colunas no fim;
  - etapa 7 com `ℹ️ [Q1]`;
  - etapa 8 com D10, H5, Q1 e J5c;
  - Parte 5 com a sobra `_ANTERIOR`.
- **SPEC:** classe 4 como estimativa, regra da grade gravada e colunas novas no fim.

## O que continua A CONFIRMAR (só a primeira execução real responde)

1. **`system:time_start` na exportação de tabela (02 e H5).** Os dois lados toleram a ausência.
2. **`pixelLonLat` no centro do pixel (01).** O 01 só aceita a rasterização que concorda com o teste vetorial do centro em todos os pixels C.
3. **`updateMask` com máscara fracionária (motor).** O D10 mostra qualquer fração diferente como ⚠️.
4. **`setAssetAcl` em texto JSON sem `owners` (02).** A auditoria B conferiu no código-fonte do earthengine-api 1.4.0 que é a mesma forma do `earthengine acl set public`.
5. **`pyramidingPolicy` `mode` (01)** e **`unweighted()` nas contagens.**
6. **Limiares heurísticos:** E6 (0,85–0,99 na radiação; razão de detalhe ≥ 1,2 e ≥ 0,3), J5c (viés > 2 °C) e os fatores do 04 na estação seca.
7. **PRÉVIA 6 do motor (Tmax ≤ 44,8 °C e salto ≤ 2 °C).** Pode falhar pela cauda quente do próprio GFS. A decisão de seguir é do usuário, com a linha "GFS bruto → calibrado" em mãos (roteiro, 5a.4).

## Verificação depois da revisão

- `py_compile` em todos os `.py`.
- `node --check` e acorn com `ecmaVersion: 5` no 04 e no 06.
- pyflakes: só `io` e `date` sem uso no 08, herdados da v3.

| Teste | Resultado |
|---|---|
| teste_01 | Todos passaram |
| teste_02 | Todos passaram |
| teste_02_troca (novo; 7 cenários) | Todos passaram |
| teste_03 | 636 verificações OK |
| teste_04.js | 35 OK |
| teste_05 | 11 de 11 (171 verificações; +2 do A-02) |
| teste_06_enso.js | 52 de 52 |
| teste_06_colunas.js (novo) | Todos passaram |
| teste_07 | Todos passaram |
| teste_08 | Todos passaram |
| fumaca_08_01 | FUMAÇA OK |
