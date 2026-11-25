# SAB: entrega final organizada (gerada em {{DATA}})

**SAB: Banco de Dados Agrometeorológicos Diários do Brasil (1961–2026)**
Projeto Earth Engine `clima-492922` · Responsável: RODRIGUES JUNIOR, Adão Alves (UTFPR, Pato Branco)

## ▶ 25/11/2026: VALIDAÇÕES CONTRA REFERÊNCIAS DE FORA E CONFERÊNCIA FINAL AUTOMÁTICA

**O registro completo do projeto, do início do código até hoje, está em `REGISTRO_GERAL.md`** (na raiz desta pasta e
do GitHub `sab-pedidos`). **Para continuar numa conversa nova:** `03_GitHub_sab-pedidos/registro/CONTINUAR_AQUI.md`.
**Para outros autores replicarem e auditarem as validações:** `03_GitHub_sab-pedidos/pesquisa/METODOS_REPLICACAO.md`,
`METRICAS_COMPLETAS.csv.gz` (todas as métricas, região × período × mês, com intervalo de confiança de 95%) e
`DADOS_PAREADOS.csv.gz`.

**O que entrou (GitHub `sab-pedidos`: PRs #9 e #10 juntados em 25/11; o resto no branch `validacoes-2`, PR a abrir):**
- **Fila da conferência final** (`rotinas/conferencia/fila.py`, workflow *Rotina - Conferência final (fila)*): de 2 em
  2 horas (10h17–20h17) roda o que falta, sobe resultados e LOG (com o commit do código) e escreve
  `rotinas/conferencia/CONFERENCIA_FINAL.md`; refaz a **K26 de 1961 até a previsão** (1981–1990 em 25/11; 2026 e a
  previsão depois que o motor V1.7 regravar 2026; as outras décadas a partir de 01/12); desliga-se ao acabar.
- **Acerto da previsão GFS por prazo** (rotina diária, 16h13): fotografia da previsão e conferência contra o ERA5.
- **Resultados já prontos** (todas as regras fixadas antes de rodar):
  - **Chuva de 2026 × CHIRPS** (jan–set): **Centro-Oeste −21%, Nordeste −16%** (régua 2024: todas as regiões a ±7%);
    Norte −1%, Sudeste −3%, Sul +4%; desenho espacial 0,83 (régua 0,86). Confirma o sinal da K19 (MS, PI, GO). Em
    teste se é o método (a mesma conta do motor em 2021–2025) e contra o GLDAS-2.1 (NASA) nas 16 variáveis.
  - **Calor de set–out/2026 × MODIS:** o desenho bate (0,61–0,70; régua 0,33–0,38).
  - **Solo, folha e ET real × SMAP e MODIS (2016–2021):** umidade 0–5 cm r = 0,89, temperatura da folha 0,80, do solo
    0,80 → mantêm; **ET real 0,47 (Norte 0,06) → índice, com aviso**.
  - **Escoamento × vazão de 512 bacias (CAMELS-BR, 1981–2018):** o SAB fica abaixo do rio (viés mediano −35%, KGE
    0,31); nenhum dos 3 métodos alternativos passou nas 4 condições do protocolo → **o atual fica, com aviso por região**.
- **O método de 2026 aplicado a 2021–2025 (pronto, 25/11 05h30):** a conta do motor que fez 2026 **subestima a chuva
  em todos os anos e regiões** (Brasil −9,6%; Nordeste e Centro-Oeste −12%, pior ano −16%) e superestima ETo (+3,5%)
  e radiação (+0,6 MJ/m²/dia). Explica a maior parte da chuva baixa de 2026. Próximo trabalho: propor a correção dos
  dias ERA5 com regra fixada antes, teste fora da amostra, simulação 05a e K16 (nada muda no banco antes).
- **Na fila:** 2026 × GLDAS-2.1 nas 16 variáveis; histórico 1961–2025 por década × TerraClimate e CHIRPS (5 regiões + 27 estados); sensibilidade à
  resolução (cada referência na grade do SAB × na resolução nativa); tudo também por mês do ano.
- Nada do banco nem do painel mudou. O motor continua o V1.7.

## ▶ 24/11/2026, 21h20: TUDO NO AR. Em dezembro, só conferir o `rotinas/PAINEL.md` do `sab-pedidos`

- ✅ **PR #8 do `sab-pedidos` juntado** (21h11): as rotinas automáticas estão ligadas (saúde do banco às segundas,
  14h29; RONI no dia 11, 10h23; K26 no dia 15, 15h41; piloto nos dias 3 e 17).
- ✅ **PR #3 do `sab-motor` juntado** (21h11): **o motor grava na V1.7** a partir da próxima rodada (que tem começado de
  manhã) e refaz sozinho os 319 dias provisórios de 2026. A saúde do banco mostra a troca (quantos dias em cada versão).
- ✅ **RONI de novembro gravado** (21h14, pela rotina, à mão): 921 estações conferidas no `RONI_CPC_v6`, com a nova
  **ASO/2026 = +2,0 °C** do CPC; o compartilhamento público continuou o mesmo. O painel do SAB passa a mostrar o RONI
  oficial no lugar da estimativa OISST (+2,3 °C).

## ▶ 24/11/2026, à noite: ROTINAS AUTOMÁTICAS E MOTOR V1.7 (registro)

### 1. Rotinas automáticas (GitHub `sab-pedidos`, PR #8): você só confere o `rotinas/PAINEL.md`

| Rotina | Quando (Brasília) | O que faz | Grava? |
|---|---|---|---|
| Saúde do banco | toda segunda, 14h29 | confere se o motor gravou nas últimas noites | não |
| RONI do mês | todo dia 11, 10h23 | roda o `02_auditoria_roni_cpc.py` (sem mudança) e regrava o `RONI_CPC_v6` | **sim**, com cópia de segurança e conferência |
| K26, rodada 1 | todo dia 15, 15h41 | K26 v1.12 (sem mudança) em 2026 inteiro, ~35 min; compara com a execução anterior | não |
| Piloto (Tmin/Tmax) | dias 3 e 17, 08h17 | já existia; agora também escreve no painel | não |

Testadas no GitHub em 24/11: saúde ✅, RONI ✅ (teste só de auditoria) e K26 ✅. **Para ligar:** juntar o PR #8
(github.com/adaojunior0909-85/sab-pedidos/pulls → PR #8 → **Merge pull request** → **Confirm merge**). Depois, **rodar
o RONI uma vez à mão**, porque o de novembro ficou para trás (o CPC já publicou ASO/2026 = +2,0 °C e o painel ainda
mostra a estimativa OISST, +2,3 °C): aba **Actions** → **Rotina - RONI do mes** (esquerda) → **Run workflow** →
**Run workflow**. **Em dezembro:** abra `rotinas/PAINEL.md` no GitHub (ou me peça para ler).

### 2. Motor V1.7: radiação 0 do ERA5-Land vira vazio (preparado; nada mudou no motor ainda)

**Por quê, com números** (verificação no Earth Engine, `pesquisa/verificar_v17_rs.py`, 24/11): nas janelas 04–20/03 e
23/09–08/10/2026, além dos 124 pixels com Rs ~0, **mais ~1.230 pixels do litoral (872 entregues)** têm o Rs rebaixado
pelo 0 do mar na interpolação: **44% a 58% do nível dos dias normais vizinhos** (a ETo também cai). A leitura não pega
esses (ficam acima de 3% de Ra). **Na V1.7 eles voltam a 85%–107%**, como o resto do Brasil no mesmo dia (88%–98%); nos
dias normais a V1.7 **não muda nada**; e a réplica da conta da V1.6 reproduziu o gravado sem nenhuma diferença.

**A mudança** (`04_GitHub_sab-motor/05a_motor_sab_v1_7_SIMULACAO.py` e `05b_…_GRAVACAO.py`): uma linha, a radiação 0
do ERA5-Land vira vazio antes da calibração; `VERSAO_ALGORITMO = 'V1.7'` (o motor refaz sozinho os dias de 2026, o que
corrige também os já gravados). O histórico continua travado.

**Feito por mim em 24/11, com o acesso ao `sab-motor` que você autorizou (a `main` e a gravação da noite não mudaram):**
- ✅ **Etapa A:** branch `motor-v17-etapa-a` com os arquivos da V1.7, e a **simulação (05a V1.7) rodada no GitHub às
  21h03: todos os critérios atendidos.** 10 de 11 dias amostrados idênticos à V1.6. Em 15/03 (dentro da janela), só Rs,
  ETo, ET real e transpiração mudam, em 0,1% dos pixels (os do litoral): Rs +9,7 MJ/m² e ETo +1,5 mm onde mudou.
  Coerência física sem nenhum problema e rota GFS sem mudança. Log em
  `07_…/validacoes/resultados/05a_v17_simulacao_2026-11-24/`.
- ✅ **Etapa B preparada:** o **PR #3 do `sab-motor`** (github.com/adaojunior0909-85/sab-motor/pull/3) já traz o
  `rodar_motor.py` gravando com a V1.7.

✅ **PR #3 juntado em 24/11, 21h11.** Na próxima rodada do motor (que tem começado de manhã), ele passa a gravar na V1.7
e refaz sozinho os dias de 2026. Para voltar à
V1.6: no `rodar_motor.py`, `ARQUIVOS['gravar']` → `05b_motor_sab_v1_6_GRAVACAO.py`.

**Achado do histórico do motor:** a rodada agendada para 23h07 tem começado **de manhã** (06h40–09h20 de Brasília),
porque o GitHub atrasa o agendamento. Por isso, a K26 e a saúde do banco rodam à tarde. A "janela do motor" de
22h50–01h00 continua valendo como cuidado, mas o motor quase nunca está rodando nesse horário.

---

## ▶ 24/11/2026: RADIAÇÃO IMPOSSÍVEL VAZIA, NO AR NOS DOIS CAMINHOS ✅

- ✅ **R1, K16 v7.1 APROVADA** (22/11, 22h40): todos os casos idênticos, o A7 (Lagoa Mirim) também; R7: 102 radiações
  vazias, todas em 04–20/03, com ETo e déficit vazios e a ET real preenchida. A 1ª corrida (v7, 21h54) tinha 3 ❌ da
  própria K16, consertados na v7.1. Resultados em `07_…/validacoes/resultados/K16_v7_2026-11-22` e `K16_v7.1_2026-11-22`.
- ✅ **R2, PR #7 juntado** (23/11): o responsável estava sem acesso ao GitHub (recuperação da conta pelo suporte) e
  autorizou por escrito a junção pela sessão do Claude. A `main` do `sab-pedidos` tem o `sab_pedido.py` 2026.11.22.
- ✅ **R3, painel 2026.11.5 no app oficial** (conferido em 24/11 pelo dicionário baixado do app; registro em
  `07_…/validacoes/resultados/R3_painel_2026.11.5_no_ar_2026-11-24`).
- ✅ **K24 v1** (24/11, 20h07, 4 min): **sem excesso sistemático** da Tmax do GFS. Acima do recorde do pixel + 1 °C em
  0,009% dos pixel-dias GFS (16/11–09/12), contra 2,2% nos dias ERA5; **0 pontos quentes** (o de Roraima, de 09/11,
  sumiu); máxima nacional prevista ≤ 43,5 °C. **A V1.7 da Tmax não é necessária.** (Se um dia for: folga de 1 °C.)
  Observação: em out–nov/2026 os dias ERA5 passam do recorde 1991–2025 em até 4,8 °C (El Niño muito forte); rever
  quando o BR-DWGD de 2026 sair. Resultados em `07_…/validacoes/resultados/K24_v1_2026-11-24`.
- **K22 v2** (24/11, 20h04, 2 min): **1 ✅** (343 dias de 2026 na V1.6, método certo, histórico intocado); **3 ✅** (UR na
  emenda 2025→2026: 1,24 → **1,02**, faixa 0,85–1,15); **2 ❌ formal por 1 pixel-dia** (Rs acima do céu claro em
  15/09/2026, em 1.008.644). Causa provável: o motor limita o Rs ao céu claro ANTES de preencher a borda pela vizinhança
  (na K26, essas ocorrências de 2026 só aparecem em pixels B, C_interior e C_borda, nunca em A). Não pede voltar à V1.5.
  Resultados em `07_…/validacoes/resultados/K22_v2_2026-11-24`. **Etapa 2 (V1.6) encerrada.**
- ✅ **Apps Script conferido (24/11):** `Codigo.gs` 2026.11.15 salvo e **implantação ativa = Versão 7, de 15/11/2026, 20h13**
  (o teto de 30 pedidos por dia vale para o formulário e para o painel).
- **Pendente (fora do SAB):** o acesso à conta do GitHub, com o suporte. Quando voltar: Settings → Applications →
  Installed GitHub Apps (conferir o aplicativo do Claude) e Settings → Security log.

**Próximos passos:** (a) motor V1.7, preparado (ver a seção de cima); o limite do Rs ao céu claro depois do
preenchimento da borda (o 1 pixel-dia da K22) ficou fora, por ser desprezível e mexer na coerência Rs × ETo; (b) depois de meados de dezembro, rodada 1 da K26 (`RODADAS_EM_SEQUENCIA = [1]`);
(c) se quiser, o plano do projeto do escoamento (único candidato a um `SAB_V2`, em paralelo ao V1).

---

## ▶ 22/11/2026, à noite: RADIAÇÃO IMPOSSÍVEL SAI VAZIA. R1, R2 e R3 (registro)

**O que mudou.** A K26 achou Rs = 0 nas planilhas (de dia isso não existe) e, no litoral em 2026, uma ETo calculada com
esse 0. A correção é **na leitura** e o banco não muda: onde Rs fica abaixo de 3% da radiação no topo da atmosfera,
**Rs, ETo e déficit do dia saem vazios**. Vale no e-mail (`sab_pedido.py` **2026.11.22**,
[PR #7](https://github.com/adaojunior0909-85/sab-pedidos/pull/7)) e no painel (**2026.11.5**,
`01_Earth_Engine_Code_Editor/06_painel_sab_2026_11_5_PRONTO.js`). A ET real não muda (a regra vem depois do grampo).
- **Conferida no Earth Engine de verdade** (GitHub Actions, só leitura): em 10/03, 01/10 e 16/11/2026, 15/06/2025 e
  15/01/1965, mudam **só** os pixels com Rs abaixo do limite (124, 122, 1.142, 0 e 0), e só nessas três bandas.
- **Causa no litoral, achada** (`03_GitHub_sab-pedidos/pesquisa/diagnostico_rs_litoral.py`): em 04–20/03 e
  23/09–08/10/2026 o ERA5-Land do Earth Engine traz os pontos de mar e lagoa com radiação **0** em vez de vazios. O motor
  toma o 0 por valor e calcula a ETo com ele (cai de ~5 para 1–2,7 mm). **Isto corrige o que eu tinha escrito antes**:
  a ETo desses dias não está certa, e não são 13 pixels B, são 27 B + 1 A + 1 C_interior (+ 95 C_borda) em pixels
  inteiros. As contagens da K26 pesam cada pixel pela fração da máscara.
- **K16 v7.1** (`02_Colab/validacoes/K16_validacao_identidade_email.py`): caso novo **A7** (Lagoa Mirim, março de 2026)
  e conferência **R7** (radiação, ETo e déficit vazios nos dias certos). A parte C fica desligada (medida na v6).
  **58 testes offline OK.**

**Clique a clique** (guia `06_Guia_clique_a_clique/Guia_Envio_Email_SAB.html`, seção "Radiação impossível vazia"):
1. **R1, K16 v7** (Colab, 30–60 min, fora das 22h50–01h00): Arquivo → Novo notebook → Ambiente de execução → Reiniciar
   sessão → cole o `K16_validacao_identidade_email.py` inteiro → Ctrl+Enter. 1ª linha: `VALIDAÇÃO K16 v7.1`. Me envie o
   zip `validacao_K16_….zip`. **Com ❌, pare aqui.** (22/11, 21h54: a v7 já deu todos os casos A, B e o A7 idênticos;
   os ❌ foram da própria K16, consertados na v7.1. Rodar a v7.1 reaproveita tudo e só refaz a comparação.)
2. **R2, só com ✅:** abra o [PR #7](https://github.com/adaojunior0909-85/sab-pedidos/pull/7) → **Merge pull request**
   → **Confirm merge**.
3. **R3, no mesmo dia:** Code Editor → script `SAB_painel_2026_10_6` → Ctrl+A → Delete → cole o painel 2026.11.5 →
   Save → Run → Apps → lápis da linha `adao-alves-rodrigues-junior-sab` → *Overwrite with current contents of editor*
   → Update.

**Depois:** (a) proposta para o motor: tratar o Rs = 0 do ERA5-Land como vazio, para os dias novos (precisa de
simulação 05a antes; nada foi mudado no motor); (b) depois de meados de dezembro, rodada 1 da K26
(`RODADAS_EM_SEQUENCIA = [1]`).

---

## ▶ ATUALIZAÇÃO DE 22/11/2026, à tarde: K26 FECHADA (1961–2026)

**A K26 terminou.** Todas as rodadas estão feitas: 1961–2026, sem nenhum dia faltando, 1,7 bilhão de pixel-dias
entregues. Relatório completo (corrigido à noite) em `07_…/validacoes/resultados/K26_FINAL_1961_2026/K26_RESULTADO_FINAL.md`.
- **11 dos 20 testes físicos com zero violações nos 66 anos** (ET real ≤ ETo, transpiração ≤ ET real, Tmax ≥ Tmin, UR,
  solo, negativos, VPD, chuva ≥ 450 mm, Rs < topo da atmosfera, vento, temperatura). **H ✅** (máscara igual nas 16 bandas).
- **Escoamento > chuva** em 14,2% dos pixel-dias de 1961–2025 (> chuva + 10 mm em 0,67%), do mesmo tamanho em todas as
  décadas; em 2026, 0,48%. É a chuva observada × o escoamento do modelo (já está avisado no dicionário).
- **Rs = 0 nos C_interior** em todas as décadas (1.698 pixel-dias, 0,0001%). **2026:** Rs = 0 no litoral em 04–20/03
  e 23/09–08/10 e nos dias GFS (ver a seção acima).
- **K26 v1.12** (raiz): `RODADAS_EM_SEQUENCIA` roda várias rodadas numa colagem só (1, 5 e 6 em 176 min, 22/11).
  A v1.11 está em `09_Versoes_anteriores/`.
- Teste `fumaca_08_01.py` corrigido: dependia da data, e de 22/11 em diante a J5 da 08 já chega a 2027.

---

## ▶ ATUALIZAÇÃO DE 18/11/2026 (leia antes)

**O que mudou** (o código do e-mail está no GitHub `sab-pedidos`, branch `main`, PRs #2 a #6):
1. **Pedido de uma variável só saía com a coluna vazia** (ex.: `Diaria_Cascavel_2026`, só chuva). Causa: com uma banda
   só, o Earth Engine grava a média como `mean`, não com o nome da banda. Corrigido no `sab_pedido.py` **2026.11.18** e
   testado no Earth Engine: as 19 variáveis, diário e mensal, saíam vazias sozinhas e agora saem iguais ao pedido "todas".
   O painel não tinha o defeito (ele tira a média sempre com as 16 bandas).
2. **Aviso do escoamento no dicionário**, igual nos dois caminhos: `sab_pedido.py` **2026.11.19** e painel **2026.11.4**
   (`09_Versoes_anteriores/06_painel_sab_2026_11_4_PRONTO.js`, substituído pelo 2026.11.5 em 22/11). Escoamento superficial e chuva efetiva de
   1961-2025 não batem dia a dia com a chuva (chuva observada x escoamento do modelo; K26). Nenhum valor mudou.
3. **K16 v6** (`02_Colab/validacoes/K16_validacao_identidade_email.py`): embute a rotina 2026.11.19 e o painel
   2026.11.4 e tem o caso novo **B2** (Pato Branco 2025, só a chuva), que falharia com a rotina antiga. A K20 passou a
   embutir a rotina atual (é o `montar_k20.py`, como sempre).
4. **Pesquisa da previsão estendida** (`03_GitHub_sab-pedidos/pesquisa/`): temperatura tem acerto acima da média
   histórica até 90 dias em boa parte do Brasil; chuva não (`pesquisa/resultados/RESULTADOS.md`). **Piloto de Tmin e
   Tmax** emitido sozinho nos dias 3 e 17 (`pesquisa/piloto/`); primeira previsão: quinzena de 16/11/2026.
5. **K26 v1.10** (`K26_auditoria_final.py` na raiz): veredito de B, C e H só nos pixels entregues (a C_borda vira INFO);
   item H conta "tem valor"; rodada nova 12 = 2001-2025. Achados da rodada 7: `03_GitHub_sab-pedidos/pesquisa/K26_RECOMENDACOES.md`.
   Escoamento x chuva: duas correções testadas com regra fixada antes, nenhuma aprovada (`pesquisa/ESCOAMENTO.md`).
6. **Base 07 em dia de novo**: o `Codigo.gs` 2026.11.15, o `teste_limite.js` e o `requirements.txt` e o workflow do
   motor de 15/11 estavam só nas pastas 04/05; voltaram para a 07, de onde o `montar_entrega.py` monta tudo. O guia
   (06) foi remontado com os códigos atuais. **57 testes offline OK** (`RELATORIO_TESTES.md`). O motor não mudou.
   O que foi substituído está em `09_Versoes_anteriores/` (acrescentada à mão, fora do `montar_entrega.py`).

**Registro de 18/11/2026:**
- ✅ **K16 v6 APROVADA** (22h13; a 1ª corrida, das 20h30, não achou os CSV no Drive e foi refeita pelo progresso salvo):
  A1 a A6, B1, **B2 (só a chuva: 5.475 linhas idênticas ao painel)**, dicionário (o aviso do escoamento igual nos dois)
  e E1. Parte C: 3 variáveis levaram 75% e 54% do tempo de 19 (regra: até 70% nas duas), então o limite do link na
  hora não muda. Resultados em `07_…/validacoes/resultados/K16_v6_2026-11-18`.
- ✅ **Pedido de uma variável só conferido num pedido real** (Pato Branco, só a chuva): coluna `Precipitacao_mm` preenchida.
- **K26 rodada 7 (1981-1990, v1.8) e rodada 8 (1991-2000, v1.9, 99 min):** C ❌ só pelo escoamento (escoamento > chuva
  em 16,5% e 15,8% dos pixel-dias entregues; > chuva + 10 mm em 0,68%; > 200 mm/dia em ~0,004%); ET real, transpiração,
  Tmax/Tmin, UR e umidade do solo sem nenhuma violação; Rs/ETo anômalos < 0,0003%. H ✅ nos pixels entregues (v1.9).
  A3: as mesmas 1.247 células nas duas décadas (máscara estática). Resultados em `07_…/validacoes/resultados/K26_*`.

**Próximos passos, nesta ordem:**
1. ✅ ~~K16 v6~~ (aprovada em 18/11, 22h13).
2. **Colar o painel 2026.11.4** (liberado pela K16 v6) (guia, quadro do painel; ou o arquivo da pasta 01): script
   `SAB_painel_2026_10_6` → Ctrl+A → Delete → colar → Save → Run → Apps → lápis da linha
   `adao-alves-rodrigues-junior-sab` → *Overwrite with current contents of editor* → Update.
3. ✅ ~~K26~~ (fechada em 22/11/2026: rodadas 12, 1, 5 e 6 feitas; ver a atualização de 22/11).
4. **Refazer o pedido de Cascavel** (só chuva, 17/11 a 03/12/2026) com ID novo, se ainda quiser a planilha certa: 17/11
   do Ponto_00001 deve vir com 15,23 mm (um pedido de uma variável de Pato Branco já confirmou a correção).
5. **Piloto:** nada a fazer; a partir de meados de dezembro, `pesquisa/piloto/CONFERENCIA.md` mostra as conferências.

---

## ▶ PRÓXIMO PASSO (09/11/2026): copiar, colar e rodar

Nada a fazer hoje (09/11): a 1ª gravação com o motor V1.6 é a rodada automática desta noite (23h07; o GitHub começa ~23h47).

1. **10/11, depois das 08h: conferir a 1ª noite (guia, passo E2-5b, 5 min).** GitHub `sab-motor` → **Actions** → **Motor SAB**: a execução agendada de 09/11 (~23h47) com ✅; dentro dela, passo *Rodar o motor*: `🔏 SHA-256 conferido: e6c66b94…` e `✅ Motor terminou às …`. Depois, code.earthengine.google.com/tasks: as tarefas `SAB_M_2026_…` *Completed*; *Running* é só esperar; *Failed*: me envie a mensagem.
2. **10/11, entre 08h e 21h50: K24 (guia, passo E2-5c; Colab, só leitura, 20 a 60 min).** Colab → Arquivo → Novo notebook → Ambiente de execução → Reiniciar sessão → colar `02_Colab/validacoes/K24_auditoria_tmax_gfs.py` inteiro → Ctrl+Enter. 1ª linha do log: `K24 v1`. No fim, `✅ Sem excesso sistemático…` ou `⚠️ Excesso sistemático… a V1.7 … é justificada` (os dois são resultados válidos; nada muda no ar). Me envie o zip `auditoria_K24_….zip`.
3. **11/11, de manhã (começar até as 22h10): K22 v2 (guia, passo E2-6; Colab, só leitura, 15 a 40 min).** Antes, Actions: as rodadas de 09/11 e 10/11 com ✅. Colab → sessão nova → colar `02_Colab/validacoes/K22_conferencia_v16.py` → Ctrl+Enter. Esperado `1 OK`, `2 OK`, `3 OK` e `✅ MOTOR V1.6 CONFERIDO: etapa 2 concluída.` Com `⏳ O motor ainda está refazendo dias`: não é erro, rode de novo na manhã seguinte. Me envie o zip `validacao_K22_….zip`.
4. Depois da K24: se ela justificar, preparo a **V1.7** (teto da Tmax da previsão no recorde do pixel + folga) com validação fora da amostra antes de qualquer troca no GitHub.

**Registro de 09/11/2026:**
- ✅ **K23 v2** (01h39, 2 min): A ✅ (a V1.6 não mexe na Tmax da emenda), C ✅ (emenda pixel a pixel mais suave que a troca natural de um dia para o outro), D e E ⚠️. O salto da Tmax máxima nacional (41,4 → 44,3 °C) vem de um pixel de Roraima (-60,65; 2,85): nos dias GFS foi a máxima do Brasil em 16 de 22 dias (média 41,7 °C, máximo 44,3 °C), acima do recorde do pixel em out-nov de 1991-2025 (42,6 °C); nos dias ERA5, média 39,8 °C e máximo 41,1 °C. Vem da rota GFS da V1.5, que a V1.6 não muda. Decisão: seguir para o E2-5 e medir com a K24. Resultados em `07_…/validacoes/resultados/K23_v2_2026-11-09`.
- ✅ **E2-5 (motor V1.6 no GitHub):** os 5 arquivos do GitHub conferem com o pacote (`rodar_motor.py` 2026.11.08; SHA `de4baea7…` e `e6c66b94…`). A execução *simular* no GitHub deu ✅ e o `previa_v16.csv` dela é igual ao do Colab (`07_…/validacoes/resultados/E2-5_github_simular_2026-11-09`).
- Sobre "nada aconteceu às 23h" em 08/11: a rodada #8 levou 1 min porque não havia dia novo para gravar (normal).

**Registro de 08/11/2026:**

1. ✅ **Motor uma vez por dia, às 23h07** (H1 e H2 feitos; a rodada agendada da noite de 08/11 rodou uma vez só, em 1 min, sem dia novo para gravar).
2. ✅ **Feito em 08/11/2026:** K21 v4 APROVADA (18h41, 8 min; U UR, R, C e E ✅; ETo 0,487 → 0,474 mm, −2,6%; resultados em `07_…/validacoes/resultados/K21_v4_2026-11-08`). Pedido de teste TESTE-0010 com Excel pelo Apps Script 2026.11.08a: recebido 18h34m46, cálculo iniciado 18h34m52, arquivos prontos e conversão 18h36m37, entregue 18h38m55 (**4 min** do pedido ao e-mail; antes, até ~20 min a mais).
3. ✅ **Feito em 08/11/2026:** 09a (sem ❌), 09b (matriz `SICSB_EQM_1986_2025` gravada: 12 meses, 85 bandas, 0 de 12.750 valores fora da tolerância; 37 min) e 05a V1.6 (20h22): tudo o que a V1.6 muda passou (vento idêntico, UR +0,7%, ETo −0,35%, chuva −0,23%, radiação acima do céu claro 0,32% → 0, Tmax/Tmin/solo iguais, histórico intacto). Aviso único (PRÉVIA 5), da rota GFS: Tmax máxima nacional 41,4 °C (01/11, ERA5) → 44,3 °C (02/11, GFS), +2,8 °C, limite ±2 °C; investigado pela K23 (acima).

**K21 v3a (08/11/2026, 16h33, 26 min):** UR ✅ (erro diário 4,25 → 3,59%, −15,6%; variação 1,25x → 1,04x a do BR-DWGD), radiação ✅ (646 pixel-dias acima do céu claro → 0), teto da chuva ✅ (0,041% dos dias; erro mensal 36,50 → 36,36 mm), ETo ✅ (−3,2%), GFS ✅ (00Z completa ~05h30). **Vento ❌ com quantis**: erro −9,5%, mas viés +0,085 → +0,107 m/s, acima do limite de 0,10 fixado antes (o vento do BR-DWGD cai com o tempo: 1,16 m/s em 1986–2025, 1,09 m/s em 2016–2025; o treino é 1986–2015). **Decisão (08/11):** o vento dos dias ERA5 fica com a correção na média da V1.5; o motor V1.6 foi revisto (SHA novo) e a K21 v4 valida essa versão com as mesmas regras. Prova feita offline na amostra de 20 mil dias da v3a: ETo −2,6% (aprovaria). X: os 14 dias acima de 400 mm de 2026 são todos de 18/04, norte do PA; a V1.6 baixa o maior de 546 para 441 mm (o próprio ERA5 bruto); fica como ressalva.

---

Estado em 03/11/2026:
- **Sistema completo e validado.**
- O motor roda sozinho no GitHub uma vez por dia, às 23h07 (desde 08/11/2026, passos H1–H2; antes, 15h07 e 23h07).
- O envio por e-mail está ligado: o formulário e o painel geram os pedidos.
- A **K16 v3 foi aprovada em 03/11/2026, às 09h33**: o arquivo do e-mail é idêntico, célula a célula, ao do painel.
- Os **52 testes offline passaram** (veja `06_Guia_clique_a_clique/RELATORIO_TESTES.md`).
- **Validação final dos dados (K17, K18, K19 e K19b, 03/11/2026): validado com ressalvas documentadas.** O código reproduz o banco (1961–2018 idêntico nas 16 bandas; depois, só revisões do ERA5-Land na fonte), sem nenhum valor fisicamente impossível. O histórico não é regravado. **Etapa 1 IMPLANTADA em 04/11/2026** (painel 2026.11.1, hoje 2026.11.3, no script `SAB_painel_2026_10_6` e no app `adao-alves-rodrigues-junior-sab`; `sab_pedido.py` 2026.11.03 no GitHub; correção na leitura dos pixels B e da radiação; o banco não muda). K20 e K16 v4 aprovadas em 03/11; teste da Lagoa dos Patos e pedido por e-mail SAB2026-00020 (CSV + Excel, 17 min) conferidos. **Etapa 2 (motor V1.6, só 2026+) revista em 08/11 depois da K21 v3a (vento fora do EQM)**: passos E2-1 a E2-6 do guia (K21 v4 → 09a → 09b → 05a V1.6 → GitHub → K22 v2). Detalhes na seção 9; plano na seção 10.

- **Endereço do painel (desde 04/11/2026):** https://clima-492922.projects.earthengine.app/view/adao-alves-rodrigues-junior-sab (app `adao-alves-rodrigues-junior-sab`, código no script `SAB_painel_2026_10_6`). O app antigo foi apagado; não há app `teste1`. Painel **2026.11.3**: autoria e link oficial no topo; envio por e-mail num clique.
- **Pedidos (Apps Script 2026.11.04a no ar; 2026.11.08a no pacote: janela única do motor e pedido em sequência, conferido de minuto em minuto enquanto calcula ou converte, em vez de 10 em 10 min):** cada pedido vira uma linha, em ordem de chegada, na aba **Pedidos** (usuários, `SAB-0001`…) ou **Pedidos_Teste** (seu e-mail e `EMAILS_TESTE`, `TESTE-0001`…, sem limite diário); a aba do formulário fica só com as respostas. `zerarPedidos()` apaga tudo e recomeça a numeração. Passo a passo: guia, "Pedidos: abas novas e zerar".
- **Janela do motor (desde 08/11/2026):** uma rodada só, às 23h07; o GitHub começa uns 40 min depois (~23h47) e a rodada leva ~20 min. Nada no Colab e nenhum pedido novo entre **22h50 e 01h00**. Antes de fazer o H1, continuam valendo as janelas antigas (14h50–16h30 e 22h50–00h30). As validações antigas (K17 a K20) ainda citam as janelas antigas no texto: são mais restritivas, sem problema.
---

## 1. Como esta pasta está organizada

Cada pasta numerada corresponde a **um lugar onde o código é colado ou enviado**. Copie sempre daqui, nunca de prints ou de conversas antigas.

| Pasta | Vai para | Como |
|---|---|---|
| `01_Earth_Engine_Code_Editor/` | code.earthengine.google.com | colar no script e salvar; o painel também vai para os Apps |
| `02_Colab/` | colab.research.google.com | uma célula por arquivo, numa sessão nova |
| `03_GitHub_sab-pedidos/` | repositório **privado** `sab-pedidos` | mesma árvore de pastas (inclusive `.github/workflows`) |
| `04_GitHub_sab-motor/` | repositório **público** `sab-motor` | mesma árvore de pastas |
| `05_Apps_Script/` | Apps Script da planilha de respostas do formulário | colar no `Código.gs` e salvar |
| `06_Guia_clique_a_clique/` | navegador | `Guia_Envio_Email_SAB.html`: todos os passos, com os códigos e o botão Copiar |
| `07_Base_de_desenvolvimento_e_testes/` | seu computador (arquivo de registro) | tudo junto, com testes, validações antigas, histórico e changelogs |
| `08_Scripts_originais_somente_registro/` | **lugar nenhum: ⛔ NÃO EXECUTAR** | seus scripts originais que criaram os assets fixos, guardados para a metodologia da tese |
| `09_Versoes_anteriores/` | lugar nenhum (só registro) | o que foi substituído: `03_GitHub_sab-pedidos` de 09/11, as K26 v1.8 (18/11) e v1.11 (22/11), o painel 2026.11.4 e a K16 v6 (22/11) |
| raiz: `K22`…`K26`, `simular_K25/K26` | Colab | as auditorias K mais recentes; a K26 da raiz é a **v1.12** |

A pasta 07 é a base onde tudo foi escrito e testado. Os arquivos das pastas 01 a 05 são cópias exatas dela, com o mesmo SHA-256. Ela serve para registro e para rodar os testes. Para colar nos serviços, use as pastas 01 a 05.

## 2. Arquivos em uso (versão, onde roda, quando, impressão digital)

| Arquivo | Versão | Onde roda | Quando | SHA-256 (início) |
|---|---|---|---|---|
{{TABELA}}

A lista completa de impressões digitais está em `SHA256SUMS.txt`. Para conferir se um arquivo é este mesmo:
- **No Colab:** `!sha256sum arquivo`
- **No Windows (PowerShell):** `Get-FileHash arquivo`

## 2b. Cada asset e o código que o gerou

| Asset (Earth Engine) | Gerado por | Situação hoje |
|---|---|---|
| `SAB_V1`, de 2026 em diante | `05b_motor_sab_v1_6_GRAVACAO.py` (GitHub `sab-motor`, automático) | em uso desde 09/11/2026, 1× por dia (23h07) |
| `SAB_V1`, histórico 1961–2025 | `08_…/O0_motor_mestre_V1_0_SAB_V1_historico.py` (V1.0). **Conferido em 03/11/2026:** os 23.741 dias têm só `versao = definitiva`, sem `versao_algoritmo` — exatamente as propriedades que a V1.0 grava — e a umidade do solo sem teto (até 0,9989) que só a V1.0 produzia. Gravados entre 24/08 e 26/09/2026. **K17 (03/11/2026):** a V1.0 rodada hoje reproduz o gravado nas 16 bandas e 4 classes de 1961 a 2013; em 2020 e 2025 só diferem as variáveis acumuladas do ERA5-Land, revistas na fonte depois da gravação. Evolução: `O0b` (V1.1) e `O1` (V1.3) | travado; nunca é regravado |
| `SAB_V1_TMP` | `05b` (antes, `O1`) | área de passagem, vazia |
| `SAB_MASCARA_QUALIDADE` | `01b_mascara_qualidade_GRAVACAO.py` | em uso; leitura pública |
| `RONI_CPC_v6` | `02_auditoria_roni_cpc.py` | em uso; atualizado todo mês |
| `SICSB_MATRIZ_GFS_V2` | `03_matriz_gfs_v2_1.py` | em uso pelo motor V1.6 |
| `SICSB_1986_2025` | `08_…/O2_climatologia_SICSB_1986_2025.py` | em uso, só leitura |
| `SICSB_SOLO_2015_2025` | `08_…/O4_solo_SICSB_SOLO_2015_2025.py` | em uso, só leitura; leitura pública |
| `SICSB_MATRIZ_GFS` (V1) | `08_…/O3_matriz_GFS_V1_SICSB_MATRIZ_GFS.py` | sem uso; referência da 04 e da 08 |
| `Baselines` (48 imagens) | `08_…/O5_baselines_normais_B1_1.py` ("Código baselines") | em uso, só leitura; conferido pelo 07a/07b |
| `RONI_Calibrado_Sazonal_1950_1980` | CSV do `08_…/O6_codigo1_RONI_Calibrado_Sazonal.py` ("Código 1"), enviado à mão para o asset | sem uso; referência da 08 (H4) |

Os arquivos da pasta 08 começam com um cabeçalho (qual asset geraram, por que não rodar, SHA-256 do original) e com a linha `raise SystemExit(...)`. Se alguém colar no Colab por engano, a célula para **antes** de qualquer import ou gravação. Abaixo da linha `ORIGINAL`, o texto é o que você enviou, sem nenhuma mudança. Os arquivos como recebidos estão em `07_…/originais_somente_registro/recebidos_03-11-2026/`.

## 3. Mapa do sistema

```
                 ┌──────────── BANCO (Earth Engine, projeto clima-492922) ────────────┐
                 │ SAB_V1 (1961–2025 protegido + 2026 provisório + previsão GFS 15 d)  │
  GitHub         │ SAB_MASCARA_QUALIDADE · RONI_CPC_v6 · SICSB_SOLO_2015_2025          │
  sab-motor ───▶ │ SICSB_MATRIZ_GFS_V2 (calibração) · Baselines (normais)              │
  05b 23h07      └─────────────────────────────────────────────────────────────────────┘
                        ▲ lê                                   ▲ lê
                        │                                      │
   PAINEL (app GEE) ────┘                    GitHub sab-pedidos (sab_pedido.py)
   link na hora (até 100 mil linhas/arquivo)        │ exporta CSV → seu Drive (SAB_pedido_<ID>)
   ou "Receber por e-mail" ──┐                      │ sab_xlsx.py → .xlsx (se pedido)
                             ▼                      ▲
   FORMULÁRIO ──▶ PLANILHA + APPS SCRIPT (Codigo.gs) ┘  fila (1 por vez), IDs SAB2026-00001,
                  e-mails de confirmação e entrega, apagar a pasta depois de 7 dias
```

**Agenda automática:**

| Quando (horário de Brasília) | O quê | Onde ver |
|---|---|---|
| 23h07, todo dia (começa ~23h47) | motor 05b grava os dias novos, ERA5 provisório e previsão GFS | GitHub `sab-motor` → Actions |
| 22h50 à 01h00, e enquanto o motor roda | nenhum pedido novo começa (fila parada pelo motor) | aba Pedidos, coluna Detalhe |
| a cada 1 min com pedido ativo (5 min se a etapa passar de 45 min ou o dia passar de 600 voltas); de segurança, a cada 10 min | `verificarPedidos` (e `verificarRapido`): acompanha, converte, entrega e despacha o próximo em sequência; registra pedidos pendentes | Apps Script → Execuções |
| 1 vez por dia | limpeza das pastas `SAB_pedido_*` com mais de 7 dias | — |
| todo mês | commit em `ATIVIDADE.md`, para o GitHub não desligar o agendamento | `sab-motor` → Code |

## 4. Credenciais, segredos e propriedades (só os nomes, nunca os valores)

> **Nunca** tire print nem cole em conversa: o token, a credencial, o `refresh_token`, a chave `.pem` ou um `github_pat_`.

| Onde | Nome | O que é |
|---|---|---|
| GitHub `sab-pedidos` e `sab-motor` → Settings → Secrets and variables → Actions | `EE_CREDENCIAL` | credencial do Earth Engine + Drive, gerada pelo `colab_credencial.py` v3 (a mesma linha nos dois) |
| Apps Script → Configurações do projeto → Propriedades do script | `GITHUB_APP_ID`, `GITHUB_APP_CHAVE` | GitHub App: o token de 1 hora é gerado sozinho e nunca vence |
| idem | `GITHUB_REPO`, `MOTOR_REPO`, `EMAIL_RESPONSAVEL` | `usuario/sab-pedidos`, `usuario/sab-motor`, seu e-mail |
| idem (o script grava sozinho) | `GITHUB_APP_INSTALACAO`, `SAB_CONTADOR`, `SAB_FORM_LISTAS`, `SAB_LIMPEZA` | instalação do App, contador dos IDs, listas do formulário, limpeza diária |
| Earth Engine → Assets → Share | `SAB_V1`, `SAB_MASCARA_QUALIDADE`, `RONI_CPC_v6`, `SICSB_SOLO_2015_2025` | precisam de **Anyone can read**, senão o app público dá erro ("not found") |

## 5. Regras que valem sempre

1. **Audite antes de mudar e simule antes de gravar.** Use 01a antes do 01b e 05a antes do 05b. A K16 vem antes de abrir uma mudança de cálculo ao público.
2. **O histórico 1961–2025 nunca é reescrito.** As travas `PROTEGER_HISTORICO = True` e `DATA_LIMITE_PROTECAO = '2025-12-31'` ficam no 05a/05b. O lançador do GitHub confere essas travas e o SHA-256 antes de rodar.
3. **Uma rotina de cada vez no Colab**, numa sessão nova (*Ambiente de execução → Reiniciar sessão*), fora da janela do motor (22h50–01h00).
4. **Nunca rode o `Código baselines.txt`.**
5. **Números com ponto decimal nos CSV** e um arquivo por local e por ano.
6. **Toda mudança no cálculo do painel** exige a mesma mudança no `sab_pedido.py` e uma nova K16.

## 6. Tarefas de rotina (clique a clique)

### 6.1 Toda semana (5 minutos)
1. **Planilha de respostas** → coluna **Status**. Procure `falha`; a coluna **Detalhe** diz o motivo. Para tentar de novo: apague o `ID_Pedido` da linha e escreva `na_fila` no Status.
2. **GitHub** → `sab-motor` → **Actions**: as execuções devem estar verdes ✅. Se uma estiver vermelha ❌, clique nela → no passo vermelho → copie as últimas linhas do log (sem segredos).
3. **GitHub** → `sab-pedidos` → **Actions**: idem.
4. **Google Drive** → Armazenamento: se passar de 85%, os pedidos esperam. Esvazie a lixeira.

### 6.2 Todo mês, depois do dia 10: RONI do CPC (`02_auditoria_roni_cpc.py`)
1. O CPC publica o trimestre novo no começo do mês. Confira em https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt se já saiu.
2. Abra o Colab → **Arquivo → Novo notebook** → *Ambiente de execução → Reiniciar sessão*.
3. Copie o `02_Colab/banco/02_auditoria_roni_cpc.py` inteiro → cole na célula → **Ctrl+Enter**. Autorize com a conta do projeto.
4. **Resultado esperado:** perto do fim aparecem "✅ N estações gravadas em …RONI_CPC_v6" e "✅ N estações conferidas no asset". Se parar com ❌, mande o print **só** da mensagem.
5. O 02 mantém o compartilhamento do asset. Para conferir: abra o app público e clique em **📊 Ver a situação e a estimativa**; não deve aparecer "not found".

### 6.3 A cada 3 meses, ou depois de mudar algo no banco: auditoria (`08_auditoria_completa_SAB.py`)
- Funciona como o 02, mas **só lê**. Leva de 10 a 30 minutos. Guarde o zip que o Colab baixa no fim.

### 6.4 Se o motor do GitHub parar
1. `sab-motor` → **Actions** → **Motor SAB** → **Run workflow** → modo `simular` → **Run**. Se der verde, rode de novo com `gravar`.
2. Se o GitHub estiver fora do ar, rode o `05b` no Colab, numa sessão nova, como antes da automação.

## 7. Como atualizar cada peça (clique a clique)

| Peça | Passos |
|---|---|
| **Painel** (`06_painel_*_PRONTO.js`) | Code Editor → Scripts → abra o **`SAB_painel_2026_10_6`** (o único script do painel; o nome não acompanha a versão) → clique no código → Ctrl+A → Delete → cole o `_PRONTO` (já traz o endereço `/exec` dos pedidos) → **Save** → **Run** (sem erro vermelho) → **Apps** → lápis da linha **`adao-alves-rodrigues-junior-sab`** → *Overwrite with current contents of editor* → **Update** → teste numa aba anônima. Se o cálculo mudou: K16 antes do Update. Para voltar: cole a versão anterior do mesmo jeito. |
| **Apps Script** (`Codigo.gs`) | planilha → **Extensões → Apps Script** → `Código.gs` → Ctrl+A → Delete → cole → **Ctrl+S** (a 2ª linha diz a versão) → **Implantar → Gerenciar implantações** → lápis → *Versão: Nova versão* → **Implantar** (o endereço `/exec` não muda). |
| **Arquivo no GitHub** | repositório → abra o arquivo → lápis ✏️ → Ctrl+A → cole → **Commit changes**. Arquivo novo: **Add file → Create new file**; para pasta, digite `pasta/arquivo` no nome. |
| **Motor** (05a/05b) | simule a versão nova no Colab → troque **juntos** `05a`, `05b` e `SHA256_MOTOR.txt` no `sab-motor`. Sem o SHA certo, o lançador não roda (é de propósito). |
| **sab_pedido.py** | troque no `sab-pedidos` → rode a K16 (Colab) → só então deixe o envio aberto. |
| **Credencial do Earth Engine** | `02_Colab/envio_email/colab_credencial.py` no Colab → copie a linha → `EE_CREDENCIAL` nos dois repositórios → **Update secret** → *Editar → Limpar todas as saídas* no Colab. |

## 8. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| App: "Máscara de qualidade ausente…" ou "…not found" | asset sem *Anyone can read* | Assets → asset → Share → marcar *Anyone can read* → Done |
| Planilha parada em `na_fila` com "Aguardando: horário do motor" | janela do motor | nada; segue depois das 16h ou da meia-noite |
| `na_fila` com "GitHub respondeu 401/404" | GitHub App ou repositório | Apps Script → rodar `testarApp` → seguir o que ele disser |
| `falha` "pasta não apareceu no Drive" | credencial do GitHub em outra conta ou revogada | refazer a credencial (seção 7) |
| `convertendo` por mais de 6 h | conversão para Excel falhou | entrega só o CSV, com aviso; ver Actions → Converter para Excel |
| Página do painel: "Tempo limite do bloqueio" | Apps Script antigo | usar o `Codigo.gs` 2026.11.03 e criar uma Nova versão da implantação |
| E-mail não chega | Spam ou cota de 100 e-mails/dia | olhar o Spam; a cota volta no dia seguinte |
| Colab: 403 `accessNotConfigured` (Drive) | Drive API desligada no projeto da credencial | Console do Google Cloud → APIs → ativar Google Drive API |

## 9. Testes e validações

- **Testes offline:** na pasta `07_Base_de_desenvolvimento_e_testes`, rode `python3 rodar_todos_os_testes.py`. São 52 testes, cobrindo painel, motor, rotinas, Apps Script, scripts originais e as validações K16 a K22. Precisa de Python com numpy, pandas, xlsxwriter e openpyxl, e de Node 18 ou mais novo. O resultado vai para o `RELATORIO_TESTES.md`.
- **Validações no Earth Engine:**
  - K8 a K15 são o registro histórico, já aprovadas; ficam em `07_…/validacoes`.
  - A **K16 v3** é a que se repete: ela gera sozinha os CSV do painel e compara com os da rotina do e-mail.
  - A **K17 v4** (`02_Colab/validacoes/K17_validacao_final_SAB.py`; a v1 e a v2 pararam por memória no P2/P4, a v2 errou a referência do P9 e a regra de datas da v3 foi retirada) é a **validação final dos dados**, do histórico à previsão. Só leitura (trava: criar, apagar, renomear e exportar bloqueados). Traz embutidos, sem mudança, os códigos que gravaram os dados (V1.0, V1.3, V1.5, O2 e O4) e confere:
    - P1 inventário (24 mil dias, sem buraco, versão de cada período, 16 bandas);
    - P2 histórico gravado = V1.0 recalculada hoje (8 dias de 1961 a 2025, 1.000 pixels);
    - P3 onde e quanto V1.0, V1.3 e V1.5 diferem, por banda e por classe de pixel (medida para a tese);
    - P4 matrizes SICSB_1986_2025 e SICSB_SOLO_2015_2025 = códigos O2 e O4;
    - P5 provisórios de 2026 = V1.5 e propriedades da previsão;
    - P6 coerência física (ET real ≤ ETo, Tmax ≥ Tmin, UR 0–100 %, solo ≤ 0,9 depois da correção de leitura...);
    - P7 chuva do SAB × CHIRPS (fonte independente, só medida);
    - P8 RONI_CPC_v6 × arquivo oficial do CPC;
    - P9 máscara = a contagem que o 01b gravou no asset (pixel inteiro: B ~300, C ~48, borda ~1.060; a K1d, A 70.524, B 241, C 48, conta só o centro no Brasil).
    - **Aprovada** quando P1, P2, P4, P5, P8 e P9 saem ✅ e P6 não tem ❌.
    - **Resultado de 03/11/2026 (11h44, v3; a v4 só retira a regra de datas e acrescenta o diagnóstico):**
      - ✅ P1 (24.062 dias), P5 (2026 = V1.5), P6 (99 dias sem incoerência), P8 (RONI = CPC), P9 (máscara = 01b: A 70.633, B 301, C 48, borda 1.064).
      - ⚠️ P2: 1961, 1972, 1983, 1994, 2004 e 2013 idênticos nas 16 bandas e nas 4 classes. Em 15/01/2020 e 31/12/2025 diferem só as variáveis acumuladas do ERA5-Land (ET real, transpiração, escoamento; nos B/C/borda também chuva, ETo e radiação); BR-DWGD e variáveis instantâneas do ERA5 iguais. ET real nos pixels A: diferença média de 0,01 mm (correlação 1,000).
      - ⚠️ P4: as 14 bandas do BR-DWGD e as instantâneas do ERA5 reproduzem exatamente; diferem só as acumuladas do ERA5 (até 0,006 mm/dia na média) e o SMAP (até 0,003 m³/m³).
      - ℹ️ P7: chuva × CHIRPS r = 0,91 (viés +0,2 %) no histórico e 0,88 (−0,4 %) em 2026.
      - Pela regra fixada antes de rodar, a validação fica **pendente com ressalva**: a ressalva é a revisão da fonte, não o código. Recomendação: aceitar com a ressalva documentada (o histórico continua travado, sem regravar).
  - A **K18** (`02_Colab/validacoes/K18_auditoria_era5_e_pixels_b.py`, só leitura, 10 a 30 min) mede antes de qualquer decisão: Q1, a partir de quando o ERA5-Land mudou (um dia por mês de 2014 a 2025, com dias de controle); Q2, de quanto seria a correção na leitura dos pixels B (gravado × BR-DWGD, janeiro e julho de 1961 a 2025). Não aprova nem reprova: só mede.
    - **Resultado de 03/11/2026 (17h55), controles 100% iguais:**
      - Q1: a revisão do ERA5-Land começa em **julho de 2017** (jul, set, out e nov/2017 mudados; dez/2017 a set/2018 iguais) e vale para **todos os dias desde outubro de 2018**. Nos pixels mudados, a ET real difere ~0,011 mm/dia (~0,3%), viés ~0. Desprezível: **não corrigir**, só a ressalva na tese.
      - Q2 (pixels B, 130 meses): temperaturas, UR, radiação e vento ≈ BR-DWGD (diferença diária ≤ 0,1 °C / 0,4%). **Chuva**: diferença diária média de 4,8 mm (média de 5,9 mm/dia) e mensal de 48 mm por pixel, viés +6% (+22% nos anos 1960). **ETo**: 0,76 mm/dia (~20%). Controle nos A: gravado = BR-DWGD (diferença máx. 0,000002).
  - A **K19** (`02_Colab/validacoes/K19_auditoria_profunda_SAB.py`, só leitura, 1h30 a 3h, uma célula) procura qualquer outra divergência corrigível, em todo o período: D2 controle de qualidade físico em todos os 24 mil dias (WMO-No. 1269, ETCCDI, Rs ≤ céu claro FAO-56); D3 consistência espacial dos extremos anuais (Tmax, Tmin, chuva, ETo); D4 ETo gravada × FAO-56 do motor e VPD; D5 emenda 2025→2026 em chuva, Tmax, Tmin, UR, radiação e vento (correção na média × mapeamento de quantis, com o BR-DWGD como verdade; Teutschbein & Seibert 2012, Cannon et al. 2015); D6 homogeneidade relativa por estado (Pettitt, SNHT; SAB × ERA5-Land e × CHIRPS) e costura de 2026; D1 reprodução das 16 bandas em 1 dia por ano e 10 dias de 2026. Não aprova nem reprova: termina com a lista de **candidatas a correção** e onde cada uma pode ser corrigida (na leitura ou no motor 2026+).
    - **Resultado da K19 (03/11/2026: v3 às 19h29 com D2, D3, D4, D6; K19b às 20h21 com D5, D1):**
      - D1: **1961 a 2018 idênticos nas 16 bandas e nas 4 classes**; 2019–2025 e jan–set/2026 diferem só nas variáveis acumuladas do ERA5-Land (revisão da fonte; ET real ~0,005 mm/dia, chuva de 2026 nos A ~0,05–0,28 mm/dia); out/2026 idêntico.
      - D2 (1,67 bilhão de pixel-dias): nenhum valor impossível. Radiação acima do céu claro (FAO-56): 18% dos dias nos pixels C, 0,8% nos B, 1.695 pixel-dias nos A em 2026 (51 em 1987). Chuva > 400 mm/dia: 14 pixel-dias nos A em 2026 (máx. 546 mm, norte do PA/AP).
      - D3: Tmin mínimas isoladas nos A (~55 por década, constante: relevo); ETo e chuva isoladas concentradas nos B, C e borda (água).
      - D4: ETo do BR-DWGD × FAO-56 do motor: −0,8%; VPD idêntico. Sem degrau na emenda.
      - D5 (2024–2025, 150 pixels A, BR-DWGD como verdade): chuva — o EQM não melhora (frequência e erro mensal pioram): manter a correção na média; UR — EQM reduz o erro diário em 22% (desvios 1,24 → 1,03); vento — EQM reduz 33% (desvios 1,71 → 1,19); Tmax, Tmin e radiação — ganho pequeno (≤ 7%).
      - D6: início da série (1961 a ~1975) desloca-se do ERA5 em UR, Tmin e chuva (quebras ~1971 em 7–11 estados): rede de estações/ERA5 antigo; só documentar. 2026: chuva × CHIRPS fora do padrão em MS, PI e GO.
      - Recomendação: corrigir os pixels B **na leitura** (painel e e-mail), usando o BR-DWGD no núcleo (chuva, Tmax, Tmin, UR, VPD, ETo, radiação, vento) e limitando de novo ET real ≤ ETo e transpiração ≤ ET real; sem regravar o banco; com K16 nova.
    - Como rodar: Colab → Novo notebook → Ambiente de execução → Reiniciar sessão → cole o arquivo inteiro → Ctrl+Enter → autorize a conta → espere de 40 a 80 min (fora da janela do motor, 22h50–01h00) → o `validacao_K17_<data>.zip` baixa sozinho → envie o zip.

## 10. Para depois (não urgente)

**Correções planejadas (decisão de 03/11/2026, nenhuma feita ainda):**
- **Etapa 1, na leitura — IMPLANTADA em 04/11/2026** (painel `06_painel_sab_2026_11_1.js`, hoje `06_painel_sab_2026_11_3.js`, e `sab_pedido.py` 2026.11.03; o banco não muda): pixels B com o núcleo do BR-DWGD nos dias de 1961 a 2025; ET real ≤ ETo e transpiração ≤ ET real refeitos; radiação dos pixels C limitada ao céu claro (FAO-56), descrita na `Qualidade_Pixel` do dicionário. Validação: `K20_validacao_correcao_pixels_b.py` e K16 v4 (caso A6, Lagoa dos Patos). Passo a passo: guia, "Etapa 1: implantar a correção" (E1 a E4).
- **Etapa 2, motor V1.6 — revista em 08/11, aprovada (K21 v4, 08/11) e no ar desde 09/11/2026** (só 2026 em diante; histórico travado; a K22 v2, conferência depois das primeiras noites, ficou sem resultado registrado): UR dos dias ERA5 pelo mapeamento de quantis (matriz nova `SICSB_EQM_1986_2025`, script 09, 21 quantis, 1986–2025; os quantis do vento ficam na matriz, sem uso); radiação ≤ céu claro (FAO-56) nos dias ERA5 e GFS; teto da chuva = máx(ERA5 bruto, 1,5 × maior dia do BR-DWGD no pixel e mês); chuva e vento continuam com a correção na média (o EQM do vento reprovou no viés na K21 v3a). Rodada única às 23h07. Validação: K21 v4 (treino 1986–2015, teste 2016–2025, regra fixada antes), 09a, prévia do 05a V1.6, simulação no GitHub, K22 v2 depois de 2 rodadas. Volta: `rodar_motor.py` 2026.11.01.
- **Quando o BR-DWGD cobrir 2026:** o motor avisa no log (`⏸️ BR-DWGD já cobre até …`), sem converter sozinho (`CONVERTER_EM_DEFINITIVO = False`). Antes de ligar: auditoria da versão nova do BR-DWGD (revisou 1961–2025?) e 05a/05b com a chave ligada e o SHA novo. Passo a passo no guia, "Quando o BR-DWGD passar a cobrir 2026".
- **Ressalvas para a tese:** revisão do ERA5-Land desde jul/2017; início da série (1961 a ~1975) afastado do ERA5 em UR, Tmin e chuva; ET real ≤ ETo é escolha do modelo; vento do BR-DWGD com poucas estações.

**Outros:**
1. Workflows do GitHub: atualizar `actions/checkout` e `setup-python` para as versões com Node 24, por causa do aviso de descontinuação do Node 20.
2. GAUL 2015 → GAUL 2025 (aviso de asset descontinuado). Muda nomes de municípios, então precisa de K16 nova.
3. Link na hora com limite maior quando a pessoa escolhe poucas variáveis (a K16 mediu de 3 a 4 vezes mais rápido).
4. Dicionário: explicar que `Umidade_Volumetrica_Solo_0_5cm = 0,500` nos dias GFS significa camada cheia (balde de 25 mm).

## 11. Histórico e changelogs
Ficam todos em `07_Base_de_desenvolvimento_e_testes/`:
- `CHANGELOG_06.md` (painel), `automacao_email/CHANGELOG_EMAIL.md` (envio e Apps Script), `CHANGELOG_05.md` (motor) e os demais;
- versões antigas do painel (2026.10.4 a 10.6).

Os arquivos `00_LEIA_PRIMEIRO_INVENTARIO.md` (22/10) e `00_ROTEIRO_FINAL.md` (20/10) são registros da montagem; **este índice os substitui**.
