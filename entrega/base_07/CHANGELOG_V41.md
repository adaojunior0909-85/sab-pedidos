# CHANGELOG v4.1 (20/10/2026, tarde)

A v4.1 parte do pacote v4 (o mesmo do `Relatorio_SAB_v4.pdf`, com as revisões A e B já aplicadas). Ela faz só os ajustes que as auditorias K (14:57) e K1d corrigida (15:05) mostraram ser necessários. Este arquivo prevalece sobre os CHANGELOG anteriores quando houver divergência.

## Arquivos que mudaram

| Arquivo | O que mudou | Motivo |
|---|---|---|
| `01a_mascara_qualidade_SIMULACAO.py` e `01b_mascara_qualidade_GRAVACAO.py` | Ver item 1 | K1a e K1d |
| `08_auditoria_completa_SAB.py` | Ver item 2 | K1a e K1d |
| `05a_motor_sab_v1_5_SIMULACAO.py` e `05b_motor_sab_v1_5_GRAVACAO.py` | Ver item 3 | K7 |
| `00_ROTEIRO_FINAL.md` | Etapas 1, 5a e 8; Parte A (notas 2, 5, 6 e 10, e a seção A.3 nova); Parte 4 (motor depois das 10h; itens da V3); lista de conferência; pasta `SAB_FINAL_v4_1` | Todas as auditorias |
| `SPEC_V4.md` | Propriedades `dias_classes` e `metodo_temp_gfs`; regra da classe B; referências da K1d | Contrato |
| `testes/teste_01.py`, `teste_05.py`, `teste_08.py`, `fumaca_08_01.py` e o novo `teste_01_uniao.py` | Testes novos dos itens 1 a 4 | Cobertura |

**Iguais ao v4, byte a byte:**
- `02_auditoria_roni_cpc.py`;
- `03_matriz_gfs_v2_1.py`;
- `04_conferencia_matriz_gfs.js`;
- `06_painel_sab_2026_10_4.js`;
- `07a_normais_CONFERIR_1991_2020.py`;
- `07b_normais_CONFERIR_1961_1990.py`;
- os outros testes.

O `SHA256SUMS.txt` lista os hashes de todos os scripts desta entrega.

## 1. Máscara de qualidade (01a/01b): classe B pela união de 5 dias [V4.1 K1a, K1d]

**Problema.** A K1a mostrou que, em 17 de 65 datas de julho (26%; IC 95% de 16% a 39%), até 7,5 pixels B ficam iguais ao BR-DWGD por coincidência.
- Isso acontece em dia seco, com ETo baixa, sobretudo nas lagoas dos Patos e Mirim.
- O conjunto de pixels não muda: C, D e A + B são constantes nos 65 anos.

Com a regra do v4, que exigia classes idênticas pixel a pixel em 3 dias, a etapa 1 podia parar com ❌ sem haver erro. Além disso, uma coincidência no próprio dia de referência classificaria um pixel B como A para sempre.

**Correção:**
- `DIAS_CLASSES = ('2001-01-15', '1961-01-15', '1981-07-01', '2017-07-15', '2025-01-15')`.
- A, C e D vêm do dia de referência (2001-01-15).
- B é a união dos pixels "BR-DWGD existe e o SAB difere" nos 5 dias (`uniao_b` e `classes_estaveis`).
- A conferência exige só a estrutura (A+B, C e D) idêntica nos 5 dias (`estrutura`, `resumo_conferencia`). As coincidências aparecem com ℹ️.
- A comparação com a J1 também usa a união dos dias, com a receita da J1.
- Propriedade nova no asset: `dias_classes`.

**Referências da K1d:**
- A K1d corrigida mostrou que só 48 pixels C têm o centro no Brasil.
- As constantes `J1_C_FORA_APROX` (~880) e `TOL_C_FORA` saíram. Entraram `K1D_CENTRO_NO_BRASIL`, `C_FORA_APROX = 1060` e `TOL_INFO_C`.
- `referencias_c` gera só ℹ️: classe 3 perto de 48 e classe 4 perto de 1.060.

**Testes:**
- `teste_01`: dias da união, `referencias_c`, `resumo_conferencia` e trechos do código.
- `fumaca_08_01`:
  - coincidências em 1981-07-01 viram ℹ️ e não reprovam;
  - estrutura diferente para com ❌;
  - classes 3 = 48 e 4 = 1.060 sem ℹ️;
  - classe 4 = 700 só com ℹ️;
  - gravação com a propriedade nova conferida.

## 2. Auditoria 08: Q1 e J1 tolerantes às coincidências [V4.1 K1a, K1d]

**Q1** (o dia de conferência é 2013-07-15, um dia de julho):
- um pixel de classe 2 na máscara que está igual ao BR-DWGD no dia não conta como diferença;
- ele aparece à parte no log ("coincidência, ignorados");
- um pixel de classe 1 que difere do BR-DWGD continua contando;
- o log mostra as referências da K1d.

**J1:**
- o histórico fica ℹ️ com C = 1.109, A + B = 70.568 (±1) e B entre 194 e 205;
- antes, exigia B = 204 exato e daria ⚠️ falso num dia com coincidência;
- constantes novas: `J1_ESPERADO['AB']`, `J1_TOL_B = 10` e `K1D_C_DENTRO = 48`;
- `J1_C_FORA_APROX` passou de 880 para 1060.

**Testes:**
- `teste_08`: 5 casos novos de J1.
- `fumaca_08_01`: Q1 com 3 coincidências fica ✅ e mostra as 3 no log.

## 3. Motor (05a/05b): escala de variância na Tmax e na Tmin, escolhida na etapa 5a [V4.1 K7]

**Problema.**
- A K7 (set–nov/2025, matriz V1) mostrou que a correção aditiva acerta a média nos prazos de 8 e 13 dias (viés −0,02 e −0,06 °C; p = 0,92 e 0,80).
- Mesmo assim, deixa o máximo diário nacional +2,9 e +2,6 °C acima do BR-DWGD (t = 12,3 e 8,7; gl = 30), com a área acima de 40 °C cerca de 6 vezes a observada.
- A matriz V2.1 continua aditiva, então a cauda tende a continuar, e a PRÉVIA 6 provavelmente acusaria a Tmax.

**Correção.** Os dados mudam só se você escolher a variância na etapa 5a.
- `METODO_TEMP_GFS = 'aditivo'` (padrão, igual à V1.5 original) ou `'variancia'`.
- `calib_variancia`: m_sicsb + (x − m_gfs) × (s_sicsb / s_gfs), com `razao_desvios` limitada a [0,5; 2]. Usa as bandas de desvio que a matriz V2.1 já tem (contrato de 100 bandas). Não precisa de asset novo.
- `processarDia_GFS(..., metodo_temp=None)` aplica o método da constante ou o pedido pela PRÉVIA.
- O motor confere também as 16 bandas de desvio da Tmax e da Tmin (`BANDAS_DESVIO_TEMP`) antes de começar.
- Propriedade nova nos dias GFS: `metodo_temp_gfs`.

**PRÉVIA 6.** Calcula em memória, para cada dia, a Tmax pelos dois métodos e mostra:
- a Tmax máxima nacional de cada um;
- o salto na emenda pelo outro método;
- a razão média dos desvios BR-DWGD/GFS e a fração de pixels abaixo de 1;
- uma linha final de decisão (`decisao_tmax`): o método em uso passa; ou só o outro passa (com a linha exata a trocar no 05a e no 05b); ou nenhum passa.

A outra versão entra só na tabela e nas linhas ℹ️. O veredito da PRÉVIA 5 continua sendo o do método em uso.

**Testes:** `teste_05` (12 de 12; 192 verificações depois da revisão):
- constantes e as 16 bandas;
- valores numéricos de `calib_variancia` com uma imagem falsa de 1 pixel, incluindo os limites da razão e a igualdade com o aditivo quando os desvios são iguais;
- as três frases de `decisao_tmax`;
- trechos do código.

## 4. Revisão independente da v4.1 e o que foi feito

Um revisor que não participou da montagem leu o diff da v4.1 inteiro. Ele não achou nada bloqueante nem de gravidade alta. Os 13 pontos de uso, diagnóstico e documentação ficaram assim:

| Nº | Gravidade | Ponto | O que foi feito |
|---|---|---|---|
| V41-01 | Média | O texto `METODO_TEMP_GFS = 'aditivo'` aparecia também num comentário, e o Ctrl+F do roteiro cairia nele | Comentário reescrito (a busca só acha a constante; o teste_05 confere). O roteiro manda procurar a linha que começa com `METODO_TEMP_GFS =`. A etapa 5b confere a linha `Correção da Tmax/Tmin nos dias GFS: ...` |
| V41-02 | Média | O cálculo informativo do outro método ia no mesmo pedido que o critério obrigatório; uma falha dele reprovaria a PRÉVIA | Partes informativas separadas: se o pedido completo falhar, o dia é refeito só com o obrigatório e o outro método conta como não aprovado |
| V41-03 | Baixa | A frase "passa na emenda" podia sair sem a emenda testada | `decisao_tmax` recebe quais emendas foram testadas; sem a do método em uso, a frase é "⚠️ ... não decida o método agora" |
| V41-04 | Média (só com máscara antiga) | Uma máscara de pacote anterior, sem `dias_classes`, seria aceita | O 01b para com ❌ e explica o que fazer; o Q1 da 08 confere `dias_classes` |
| V41-05 | Baixa | O código aceita B até 205, mas o texto dizia 204 | Texto e roteiro: "de 194 a 205" |
| V41-06 | Baixa | Um pixel A que diferisse do BR-DWGD num único dia entraria na união sem aviso | Histograma de dias em B por pixel da união; ℹ️ se algum pixel esteve em B em só 1 ou 2 dias (`pixels_b_raros`) |
| V41-07 | Baixa | O Q1 ignorava qualquer número de coincidências | Mais de 20 (`Q1_MAX_COINC`; a K1a mediu até ~8) vira problema no Q1 |
| V41-08 | Baixa | Trocar o método não forçava refazer os dias GFS da mesma rodada | O inventário do motor lê `metodo_temp_gfs`; `precisa_refazer_gfs` refaz o dia se o método gravado for outro |
| V41-09 | Baixa | A PRÉVIA 6 não olhava a faixa de 6 a 10 dias | A PRÉVIA inclui o dia de prazo 8 |
| V41-10 | Baixa, A CONFIRMAR | Se o Earth Engine combinar as máscaras fracionárias de outro jeito, o B ponderado da união poderia cair | O log mostra o B da receita J1 só no dia de referência e na união, lado a lado |
| V41-11 | Baixa, A CONFIRMAR | A estrutura compara também D; uma pegada diferente do SAB num dos 5 dias pararia o 01 | Mantido de propósito: o ❌ é visível e nada é gravado; a K1a mediu D constante. Coberto pelo teste_01_uniao |
| V41-12 | Baixa | Testes que só conferiam texto do código | Novo `teste_01_uniao.py` (simulação em numpy das funções reais do 01); testes novos de `decisao_tmax`, `pixels_b_raros`, `checar_q1` e `precisa_refazer_gfs` |
| V41-13 | Baixa | Documentação: "cerca de 880" no SPEC; mensagem das bandas da matriz | SPEC corrigido; o motor imprime "48 bandas de média e as 16 de desvio da Tmax/Tmin". O `SHA256SUMS.txt` é gerado na montagem do zip |

## O que NÃO mudou de propósito

| Assunto | Por quê |
|---|---|
| Janela da chuva 12–12 UTC (K3b) | Mudar só o GFS contaria 12 h duas vezes na emenda com o ERA5 (00–24 UTC), e a razão da chuva muda entre prazos (K3). Fica para a V3, com ERA5-Land horário e a matriz refeita (roteiro, Parte A, nota 10). |
| Escoamento (K6) | Continua índice não validado, com os números da K6 no roteiro (nota 2). Correção para a V3. |
| Pixels B no painel | Continuam com a marca `B` na coluna `Qualidade_Pixel`. Ler o BR-DWGD direto nesses pixels fica para a V3. |
| Calibração da chuva (K5) | A V1.5 foi mantida: recupera o volume na seca sem inflar a chuva forte. |
| Decisões 2, 3 e 4 (K2, K3a, K4) | Confirmadas pelos dados (roteiro, Parte A, A.3). |

## A CONFIRMAR na primeira execução (novos)

- A escala de variância depende de as bandas `s` da matriz V2.1 serem o desvio-padrão diário dos pares, como o 03 grava. A PRÉVIA 6 mostra a razão média antes de qualquer gravação.
- As contagens sem ponderação da máscara são aproximadas: B perto de 300, classe 3 perto de 48, classe 4 perto de 1.060. Valores diferentes geram só ℹ️.
