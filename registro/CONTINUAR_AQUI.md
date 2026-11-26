# Para continuar numa conversa nova (estado em 26/11/2026, ~11h30 de Brasília)

## Cole isto na conversa nova
> Continue o trabalho do SAB a partir do ponto salvo. Primeiro, só leia (não mude nem dispare nada): no repositório
> adaojunior0909-85/sab-pedidos, busque todos os branches (git fetch origin) e leia registro/CONTINUAR_AQUI.md,
> REGISTRO_GERAL.md e pesquisa/METODOS_REPLICACAO.md do branch validacoes-2; veja também os branches claude/* (git
> branch -r), que guardam rascunhos de conversas anteriores. Depois confira a fila: os arquivos
> rotinas/conferencia/fila_estado*.json da main e do validacoes-2, os LOG em rotinas/conferencia/logs/ e as últimas
> execuções do workflow "Rotina - Conferência final (fila)". Me mostre, em português, um resumo do que terminou, do
> que está rodando, do que quebrou, das decisões que estão esperando por mim e qual é o próximo passo, e só então siga
> os próximos passos do CONTINUAR_AQUI.md. Responda sempre em português.

Horários: os commits do GitHub estão em UTC; a fila e os LOG, em Brasília (UTC−3).

## Regras que a conversa nova precisa seguir
- Responder só em português; passo a passo clique a clique quando o responsável tiver de fazer algo.
- Nunca pôr credenciais em arquivo ou conversa (a do Earth Engine fica só no segredo `EE_CREDENCIAL` do GitHub).
- Não juntar nada na `main` sem o responsável pedir: abrir PR e ele faz o merge.
- Tudo no Earth Engine é SÓ LEITURA nas validações; o histórico 1961–2025 nunca é regravado.
- Toda regra de decisão é fixada ANTES de rodar (está no cabeçalho de cada script).
- Não tentar contornar sites que bloqueiam acesso (INMET).

## Onde fica cada trabalho (branches)
- **`main`:** o que está no ar (rotinas, fila da conferência, resultados que a fila sobe).
- **`validacoes-2`:** as validações novas, o registro, a entrega (`entrega/`) e este arquivo. É o branch de referência
  até o PR dele ser juntado na `main`.
- **`claude/<nome>`:** cada conversa nova trabalha num branch próprio, com nome automático. **Ao começar, liste-os**
  (`git branch -r | grep claude/`) e leia o último commit de cada um: podem ter rascunhos esperando aprovação. Antes
  de encerrar uma conversa, traga o que importa para o `validacoes-2` (ou abra PR) e atualize este arquivo, para nada
  ficar perdido num branch esquecido.
  - `claude/gifted-brahmagupta-4wyvci` (25/11, 06h47): rascunho do protocolo da correção da chuva, da radiação e da
    ETo dos dias ERA5 (`pesquisa/PROTOCOLO_CORRECAO_ERA5_2026.md`). **Já copiado** para o branch abaixo; pode ser
    ignorado.
  - `claude/tender-maxwell-6ka6dt` (25/11): branch de trabalho atual = `validacoes-2` + `main` de 25/11 (antes do
    PR #11) + o teste da correção, **que roda NESSE branch** (resultados sobem nele). O registro, o protocolo, o
    script e o teste também estão no `validacoes-2`: uma versão só. Os resultados da correção vêm para o
    `validacoes-2` quando o teste acabar.
  - `renomear-conferencia-gravacao`: o PR #11 (juntado na `main` em 25/11, 12h45); pode ser apagado.
- **Uma conversa por vez.** Duas conversas mexendo no repositório ao mesmo tempo se atropelam: a antiga para quando a
  nova começa.

## Decisões (o que já foi decidido e o que espera o responsável)
- ⏳ **ESPERA O RESPONSÁVEL (26/11):** o que fazer com a V1.8 (PR sab-motor#4, merge suspenso). Recomendação:
  refazer as razões do C3 com anos estáveis (2010–2019, nunca o fim de 2025, que tem poucos pluviômetros), com
  protocolo novo congelado antes, e decidir depois do `investigar_brdwgd.py` (BR-DWGD × ERA5-Land, sem pluviômetros).
- ✅ **Protocolo da correção APROVADO** (25/11, ~07h), com 2026 × CHIRPS só como relato; congelado antes de rodar
  (commit `1de7696` do `validacoes-2`). ✅ **Emenda 1** (25/11, ~08h, pedida pelo responsável, antes de rodar; commit
  `91cd9b3`): a condição 4 usa TODOS os pixels entregues (dias de chuva e Rx1day, em cada uma das 5 regiões) e o p99
  em 1.500 pixels (300 por região) no lugar dos 150 da K21.
- ✅ **`resolucao` roda completa**, sem amostra de anos, mesmo levando ~2 dias (decisão de 25/11).
- ✅ **"Saúde do banco" virou "Conferência da gravação"** (PR #11, juntado em 25/11): `rotina_gravacao.yml`,
  `rotinas/gravacao/conferencia_gravacao.py`, `rotinas/estado/gravacao.json`.
- ✅ **Teste da correção TERMINOU (25/11, ~15h; os 120 meses):** **chuva → C3 passa** nas 4 condições (mediana do
  |viés anual| 8,4% → 4,3%; Brasil melhor em 9 de 10 anos); **radiação/ETo → nenhum passa** (o C0 fica). Resultado:
  `pesquisa/resultados_correcao_era5/RESULTADOS.md`. **Relato 2026 × CHIRPS pronto (25/11, 17h15; fora da regra):**
  viés do total jan–set contra o CHIRPS (régua 2024 → 2026 gravado → 2026 com C3): Nordeste +6,6 → −15,6 → −4,1;
  Centro-Oeste −1,4 → −21,3 → −10,0; Brasil +2,3 → −5,8 → +3,6; mas Sul +3,8 → +4,1 → +15,5, Sudeste −1,1 → −2,9 →
  +5,6 e Norte +2,4 → −1,2 → +7,1 (o C3 aproxima o NE e o CO e passa do ponto no Sul). Só relato: não muda a decisão.
- ✅ **Responsável (25/11, ~17h): "pode fazer tudo e vamos aguardar todos os resultados para tirarmos as nossas
  conclusões".** Feito: (a) a fila da `main` disparada à mão (K26 rodada 7); (b) **motor V1.8, etapa A**, no branch
  `claude/tender-maxwell-6ka6dt` do `sab-motor` (commit `5739ed0`): chuva dos dias ERA5 = V1.7 × `RAZAO_CHUVA_C3`
  (60 razões BR-DWGD/V1.7 de 2021–2025, da Parte A); radiação e ETo iguais à V1.7; sem climatologia nova; a gravação
  da noite CONTINUA na V1.7. Simulação disparada (Actions do `sab-motor` → Motor SAB, modo simular, nesse branch);
  a prévia `previa_v18.csv` exige que só a chuva mude e que a razão observada por região e dia seja a esperada (2%).
- ✅ **Prévia da V1.8 (1ª, 25/11 17h11): PASSOU** em todos os critérios, mas com **1 dia só** (15/11): a prévia compara
  com os dias já gravados na V1.7, e os 304 dias que a V1.7 regravou em 25/11 ainda estão na coleção temporária (o
  motor da noite os promove). Nesse dia: só a chuva mudou (Brasil +12,8%; as outras 15 variáveis idênticas em 100%
  dos pixels; rota GFS igual), a razão observada = a esperada em cada região (N 1,131; NE 1,147; CO 1,134; SE 1,123;
  S 1,053 × 1,054) e 0 incoerência física. **Rodar a simulação de novo depois do motor da noite de 25→26/11** (Actions
  do `sab-motor` → Motor SAB → Run workflow → branch `claude/tender-maxwell-6ka6dt`, modo simular) para a prévia
  cobrir os 11 meses. O workflow agora guarda o `previa_v18.csv` (commit `4dae9eb`).
- ✅ **K26 rodada 7 (1981–1990) pronta** (main, 25/11 18h25, 79 min): 3.652 dias sem buraco nem repetição (A1 OK); máscara
  igual nas 16 bandas (H OK); A3 e B em atenção (contagem do dia × máscara; escoamento fora da faixa em 15 mês-classe);
  C com a FALHA já conhecida (escoamento do ERA5 > chuva observada em 42,8 milhões de 258 milhões de pixel-dias; Rs
  acima do céu claro em 9.136). Comparar com a rodada 7 anterior (v1.8, 18/11) nas conclusões:
  `rotinas/resultados/k26_rodada7/2026-11-25/` (na `main`).
- 🔎 **26/11, ~10h45: leitura dos 2 artigos do BR-DWGD** (Xavier 2016 e 2022) × documentação oficial de GLDAS, IMERG,
  PERSIANN-CDR, TerraClimate, CHIRPS e ERA5-Land: o artigo de 2022 termina em 31/7/2020 e diz que 2019–2020 têm
  "muito poucos dados de pluviômetros"; 2021–2025 é extensão **sem documentação publicada**. Quatro famílias
  independentes mudam no mesmo ano (2020) e no mesmo sentido → o excesso provavelmente vem do BR-DWGD; suspensão da
  V1.8 confirmada. Proposta (só com autorização): refazer as razões do C3 com 2010–2018. Detalhes:
  `pesquisa/resultados_brdwgd/ANALISE_DOS_ARTIGOS.md` (validacoes-2); o mecanismo sai do `investigar_brdwgd.py`.
  **Revisto às ~11h15 com o site oficial e o relatório da v_3.2.4** (rede de ~5.700 pluviômetros em 2020–2024, não
  rala; só o fim de 2025 é ralo; IMERG/PERSIANN/GLDAS-2.1 dependem todos do GPCC): suspeito continua o BR-DWGD
  (composição da rede, salto maior no Norte/Nordeste), não provado; seção 4 do mesmo arquivo.
- ⚠️ **26/11, 07h15: MERGE DA V1.8 SUSPENSO, decisão volta ao responsável.** As várias referências (chuva por
  satélite completa) mostram a chuva do banco em **2021–2025 ~9% acima** da relação das décadas anteriores segundo
  4 fontes (GLDAS-2.1 +8,0%, IMERG +8,7%, PERSIANN +9,0%, TerraClimate +11,2%; as três primeiras dependem do GPCC e
  contam como uma família: ver a revisão de 11h15 acima); o CHIRPS na média do Brasil não (+0,0%), mas no Norte e
  Nordeste sim (+7 a +10%). As razões do C3 (V1.8) saem justamente do BR-DWGD de 2021–2025: se ele estiver alto, a V1.8 corrige demais
  (coerente com o Sul +15,5% × CHIRPS). A prévia de 26/11 10h30 roda (só leitura) e NÃO junta o PR sab-motor#4.
- ✅ **V1.8 APROVADA pelo responsável (25/11, ~19h20: "Junte e aprove o V1.8").** Etapa B pronta no PR
  adaojunior0909-85/sab-motor#4 (`ARQUIVOS['gravar']` = 05b v1_8; head `0b13fda`). Combinado: o merge vem DEPOIS da
  prévia com 2026 inteiro (26/11, 10h30, tarefa agendada "Refazer a prévia da V1.8 com 2026 inteiro"): se passar (≥ 8
  dias, todos os critérios), a tarefa junta o PR sozinha e a V1.8 grava a partir da noite de 26/11; se falhar, não junta
  e avisa. Juntar antes impediria a prévia (o motor apagaria os dias da V1.7 que ela compara).
- ⏳ **Depois da prévia:** K16 da V1.8 (o painel e o `sab_pedido.py` não mudam: a correção é na gravação, mas a K16
  confere que leitura e e-mail continuam iguais) e, só com aprovação do responsável, a etapa B (gravar com a V1.8: o
  motor refaz os dias de 2026; o histórico não muda). **Conclusões só quando todos os resultados saírem** (pedido do
  responsável): correção (+ 2026 × CHIRPS), `historico`, `resolucao`, K26 e a prévia da V1.8.
- ✅ **Minutos do GitHub Actions:** esgotados em 25/11 (~15h) com o `sab-pedidos` privado; **o responsável tornou o
  `sab-pedidos` público (25/11, ~17h)**: repositório público não gasta minutos. Antes, conferido: nenhuma credencial
  no histórico (só os nomes, em código e guias; as de verdade ficam nos segredos), nenhum e-mail de solicitante; o
  e-mail do responsável só como autor de commits, que já era público no `sab-motor`.
- ⏳ **Juntar o PR `validacoes-2` → `main`** quando `historico` e `resolucao` terminarem (eu abro, o responsável junta).
- ⏳ **Agendamentos do `sab-pedidos`:** se até a noite de 25/11 a previsão das 16h13 não tiver rodado sozinha, propor ao
  responsável o conserto (ver "O que falta auditar e corrigir", item 1).

## O que está rodando sozinho (GitHub Actions, workflow "Rotina - Conferência final (fila)")
| Onde | Tarefa | Situação (25/11, ~13h) |
|---|---|---|
| `claude/tender-maxwell-6ka6dt` (cadeia `so=correcao_era5`) | **teste da correção dos dias ERA5** (C0 a C3, fora da amostra 2016–2025; script `pesquisa/validar_correcao_era5.py`) | rodando desde 08h10 (3ª tentativa; as 2 primeiras quebraram por falta de memória e pelo tipo da banda do sorteio, corrigidos). **Receita conferida**: a média recalculada bate com o `SICSB_1986_2025` (maior diferença 1,55%, radiação do ERA5; limite 2%). Etapas: pixels (40 anos de somas + 10 de dias) → 120 meses regionais → 2026 × CHIRPS → `RESULTADOS.md`. Várias execuções de ~5 h |
| `validacoes-2` (cadeia `so=historico`) | histórico 1961–2025 × TerraClimate e CHIRPS, 5 regiões + Brasil + 27 estados | 1961–1981 prontos (~15 min/ano); faltam ~44 anos, ~11 h |
| `validacoes-2` (cadeia `so=resolucao`) | sensibilidade à resolução, cada referência na grade do SAB × nativa | CHIRPS 1981–1993 pronto (~25 min/ano); faltam ~40 h (resto do CHIRPS, 65 anos do TerraClimate, MODIS, SMAP, GLDAS) |
| `main` | `metodo_2026_A` e `metodo_2026_B` | **prontas** |
| `main` (fila de 2 em 2 h, 10h17–20h17) | K26 rodada 7; rodadas 1–4 (2026 e previsão) a partir de 26/11, depois que 2026 estiver todo na V1.7; rodadas 5, 6, 8–11 a partir de 01/12; depois do PR do `validacoes-2`: `por_mes` e `metricas` | esperando: **a fila da `main` não rodou por horário em 25/11** (ver auditoria, item 1) |
| `sab-motor` | motor da noite (23h07; o GitHub tem começado entre 06h40 e 09h20) | ok em 25/11 (08h09–09h00): **1ª rodada na V1.7**, mandou ao Earth Engine 319 dias ERA5 de 2026 e 25 dias GFS (até 10/12); histórico travado |
| `main` | rotinas fixas: previsão 16h13, conferência da gravação (seg 14h29), RONI (dia 11), K26 (dia 15), piloto (dias 3 e 17) | **nenhuma rodou por horário até 25/11, 13h** (todas as execuções foram à mão) |

As cadeias do `validacoes-2` se chamam de novo sozinhas até acabar. Se uma tarefa quebrar 3 vezes, fica `falhou` no
`fila_estado_<cadeia>.json` e o erro no LOG: corrigir o script, apagar a entrada da tarefa no json e disparar de novo:
`gh api -X POST repos/adaojunior0909-85/sab-pedidos/actions/workflows/rotina_conferencia.yml/dispatches -f ref=validacoes-2 -f 'inputs[so]=historico'`

## Próximos passos
1. **Se uma tarefa quebrou** (`falhou` no json ou erro no LOG): corrigir o script, apagar a entrada da tarefa no
   `fila_estado_<cadeia>.json` do `validacoes-2` (ou no `fila_estado.json` da `main`), subir e disparar de novo a
   cadeia (comando acima). Na `main`, a fila volta sozinha no próximo horário (de 2 em 2 h, 10h17–20h17).
2. **Quando `historico` e `resolucao` terminarem (ok)** no `validacoes-2`: abrir o PR `validacoes-2` → `main` (o
   responsável junta). Cuidado no PR: `rotinas/conferencia/fila_estado.json` muda nos dois lados; manter o da `main`
   e os `fila_estado_*.json` do branch.
3. **Depois do merge**, a fila da `main` roda sozinha `por_mes` e `metricas` (precisam da Parte A e da Parte B do
   `metodo_2026`, que rodam na `main`, e do `historico`). Não rodar `metricas_completas.py` antes disso: sairia
   incompleto.
4. Ler os resultados e escrever as conclusões em `registro/REGISTRO_MANUAL.md` (seção 4), principalmente:
   - **Parte A PRONTA (25/11, 04h43):** o método de 2026 subestima a chuva em TODOS os anos de 2021–2025 e regiões
     (Brasil −9,6%; Nordeste e Centro-Oeste −12%, pior ano −16%) e superestima ETo (+3,5%) e radiação (+0,6 MJ). Isso
     explica a maior parte da chuva baixa de 2026 × CHIRPS. PRÓXIMO TRABALHO PRINCIPAL: propor ao responsável a
     correção dos dias ERA5 (ex.: calibração pelos anos recentes, 2016–2025, ou fator por década), com protocolo e
     regra fixados ANTES, teste fora da amostra (como a K21: treino em uns anos, teste em outros), simulação 05a no
     sab-motor e K16. Nada é gravado sem o responsável aprovar. Ver `pesquisa/resultados_metodo_2026/RESULTADOS_A.md`;
   - **Parte B PRONTA (25/11, 06h47), já no `REGISTRO_MANUAL.md`:** 2026 × GLDAS-2.1 põe a chuva de 2026 fora da régua
     2022–2024 no Nordeste (−10,8% × +11,6 a +18,6) e no Centro-Oeste (−7,3% × +3,9 a +14,2), terceira confirmação
     de que o problema é o método. A investigar depois: escoamento e temperatura do solo/folha fora da régua no
     Norte/Centro-Oeste (`pesquisa/resultados_metodo_2026/RESULTADOS_B.md`, na `main`);
   - o resultado da sensibilidade à resolução (`pesquisa/resultados_resolucao/RESULTADOS.md`);
   - avisos no dicionário: ET real como índice (Norte r = 0,06 × MOD16); escoamento abaixo da vazão dos rios (−35%).
5. **Atualizar a pasta de entrega (o zip):** tudo o que é preciso está no repositório, na pasta `entrega/` (a base
   07, os extras e o script). Não é preciso enviar o zip na conversa. Passos: (a) num checkout com a `main` junta
   (`git merge origin/main`), escrever a seção nova, datada, no topo de `entrega/base_07/LEIA_PRIMEIRO_modelo.md`;
   (b) `bash entrega/montar_entrega.sh <pasta de saída>` (roda os 58 testes, monta, confere o SHA-256 e fecha o zip;
   ~10 min); (c) mandar o zip ao responsável. O zip passa de 30 MB: o responsável guarda no computador/Drive, não
   precisa reenviar. Se mudar algo da base (painel, Colab, Apps Script), mudar em `entrega/base_07/` e subir.
6. O repositório `sab-motor` não vem junto numa conversa nova: se precisar (ex.: conferir se o motor V1.7 regravou
   2026), peça para adicionar o repositório adaojunior0909-85/sab-motor. A `rotinas/PAINEL.md` (conferência da gravação)
   mostra quantos dias estão em cada versão do motor.

## Fase 2: correção de todas as variáveis (pedido do responsável em 25/11, ~19h40)
"Analisar tudo automaticamente e gravar SÓ com autorização, seja 2026, seja o banco todo." Protocolo
`pesquisa/PROTOCOLO_CORRECAO_FASE2.md`, **congelado antes de qualquer resultado** (commit `9a12309`):
| Módulo | O que testa | Situação (25/11, ~19h50) |
|---|---|---|
| M1-C3R | a razão do C3 só onde o viés é consistente | ❌ **não passou** (mediana +0,8 p.p.; r_anom −0,022); o C3 fica. Achado: o C3 piora os dias de chuva (afastamento 9,5 → 12,6 p.p.). `resultados_fase2/RESULTADOS_M1_C3R.md` |
| M1-C3G, C3RG | corte da garoa (+ C3; + C3 só onde consistente) | 🔄 rodando (cadeia `fase2_leva1`); parcial 2016–2018: o C3G derruba o afastamento dos dias de chuva de 22,0 para 3,5 p.p. com mediana +0,25 p.p. (falta o p99 e os outros 7 anos) |
| M2-R1 | radiação × razão regional (ETo recalculada) | 🔄 idem |
| M3-T2 | Tmax, Tmin, UR, vento: ajuste regional (VPD e ETo recalculadas) | 🔄 idem |
| M2-R2, M3-T1 | quantis da radiação; janela de 10 anos | ❌ **leva 2 pronta (26/11, 05h36): nenhum passou.** R2: radiação Brasil +0,45 → +0,25 MJ, mas ETo só −0,82 p.p. (precisa 1) e r_anom −0,039; T1: os desvios da V1.7 já são pequenos (Tmax +0,16 °C, vento +0,07 m/s) e não melhoram o bastante. `resultados_fase2/RESULTADOS_LEVA2.md` |
| M4 | ET real, transpiração, solo, folha, escoamento | conclusão fixada antes: sem referência para corrigir o nível → avisos no dicionário |
| M5 | histórico 1961–2025 | ⏳ **o `historico` terminou (25/11, 19h52)**; décadas com degrau: chuva × TerraClimate 2021–2025 em todas as regiões (+6 a +17%) e Sudeste 1981–90, mas o CHIRPS NÃO confirma (2021–25 Brasil +0,0%), e o CHIRPS marca o Centro-Oeste 2011–20 (−7,4%), que o TerraClimate não confirma → chuva sem correção pela regra; Tmin 1961–70 (correlação baixa: NE 0,11, CO 0,38), radiação 1961–80, vento, VPD, ETo e escoamento em várias décadas: falta a 2ª referência (ERA5 bruto), que a vigia roda. `pesquisa/resultados_historico/RESULTADOS.md` |
| M6 | previsão GFS | ⏳ ~24/12 (30 dias de fotografias) |
Qualquer método que passar vai ao responsável; **nada é gravado sem autorização**.

**Várias referências (emenda 1 da fase 2, 25/11 ~20h20, pedido do responsável: "o máximo de comparações e tudo
registrado"):** `pesquisa/validar_multifonte.py` compara o banco, mês a mês, nas 5 regiões, no Brasil e nos 27 estados,
com: ERA5-Land bruto (1961–2025), GLDAS-2.0 (1961–2014), GLDAS-2.1 (2000–2025), PERSIANN-CDR (1983–) e IMERG (2000–) na
chuva e MOD16 (2001–) na ET real; o resumo junta o TerraClimate e o CHIRPS do `historico`. Um degrau só é
**confirmado** se aparecer em ≥ 2 referências independentes. 5 cadeias no `validacoes-2` (`multifonte_*`), disparadas
em 25/11 ~20h30; resultado em `pesquisa/resultados_multifonte/RESULTADOS.md` e `TODAS_AS_COMPARACOES.csv` (tudo,
inclusive os estados). Tempo estimado: o GLDAS-2.0 é o mais longo (~1,5 dia).

## O que será corrigido (estado em 25/11, ~20h40)
| Situação | O quê |
|---|---|
| ✅ decidido e aprovado | **Chuva dos dias ERA5 de 2026 em diante (V1.8, C3)**: junta em 26/11 se a prévia com 2026 inteiro passar |
| ✅ já corrigido antes | Rs = 0 do litoral (V1.7); na leitura: pixels B pelo BR-DWGD, ET real ≤ ETo, Rs impossível vazio, solo/escoamento pelo SMAP nos dias V1.0 |
| 🔄 depende de teste | garoa da chuva de 2026 (C3G/C3RG); radiação e ETo de 2026 (R1, R2); Tmax/Tmin/UR/VPD/vento de 2026 (T2, T1); décadas do histórico confirmadas por ≥ 2 referências (M5, só na leitura); previsão (M6, ~24/12) |
| ❌ não corrigir | C1, C2, C3R na chuva; C1–C3 na radiação/ETo; chuva do histórico (degraus não confirmados, por ora); escoamento (nenhum método passou); ET real, transpiração, solo, folha (sem referência para o nível) → avisos no dicionário |

**Pedido final do responsável (25/11, ~20h40): "atualize tudo, automatize tudo, aguardo tudo acabar e as suas
recomendações".** A vigia faz a etapa final sozinha: PR `validacoes-2` → `main` (sem merge),
`registro/RECOMENDACOES_FINAIS.md` (cada variável × período: números, precisa corrigir?, método, recomendação), registro
em dia, pacote de entrega remontado e enviado, notificação no celular.

## Vigia automática (desde 25/11, ~17h)
Tarefa agendada **"SAB – vigiar os testes"** (a cada 2 h, minuto 13; dispara NA conversa do branch
`claude/tender-maxwell-6ka6dt`, que tem o GitHub ligado). Confere as cadeias, a simulação da V1.8, o motor da noite e se
os agendamentos do `sab-pedidos` voltaram; pode disparar de novo uma cadeia parada e corrigir um erro de código
pequeno (uma vez por tarefa por dia); notifica o celular só quando algo precisa do responsável, quando sai um
resultado importante ou quando tudo termina. Quando tudo terminar: abre o PR `validacoes-2` → `main` (sem merge) e
resume os resultados aqui. Nunca: merge, gravação no Earth Engine, motor gravando a V1.8.
**Desde 25/11, 19h17: a vigia também faz as vezes do agendamento do GitHub** (que não dispara no `sab-pedidos`): dispara
na `main`, quando o horário passou e não houve execução, a previsão (todo dia, 16h13), a conferência da gravação
(segunda, 14h29), o RONI (dia 11), a K26 mensal (dia 15), o piloto (dias 3 e 17) e a fila da `main` (a cada 2 h, 07h–20h30,
enquanto houver tarefa). Por isso ela NÃO se desliga quando os testes acabam; só se o responsável pedir ou se os
agendamentos voltarem (aparecerem execuções com event=schedule). Os pedidos por e-mail não dependem disso (o Apps
Script dispara na hora do pedido).

## O que é verificado (cobertura)
- **Consistência física (K26), o banco inteiro:** 1961 até o último dia da previsão, as 16 variáveis, ~1,7 bilhão
  de pixel-dias (rodadas 1–4: 2026 e previsão; 5–11: 1961–2025 por década).
- **Referências independentes:**

| Variável | Referência | Período |
|---|---|---|
| Chuva | TerraClimate; CHIRPS; BR-DWGD fora da amostra (correção); GLDAS | 1961–2025; 1981–2026; 2016–2025; 2026 |
| Tmax, Tmin, VPD, radiação, vento, ETo | TerraClimate; método de 2026 × BR-DWGD; GLDAS | 1961–2025; 2021–2025; 2026 |
| ET real | TerraClimate; MOD16; GLDAS | 1961–2025; 2016–2021; 2026 |
| Água no solo 0–100 cm | TerraClimate (correlação); GLDAS | 1961–2025; 2026 |
| Escoamento total | TerraClimate; vazão de 512 bacias (CAMELS-BR); GLDAS | 1961–2025; 1981–2018; 2026 |
| Umidade relativa | via VPD (TerraClimate); BR-DWGD; GLDAS | 1961–2025; 2021–2025; 2026 |
| Umidade do solo 0–5 cm | SMAP; GLDAS | 2016–2021; 2026 |
| Temperatura do solo e da folha | MODIS; GLDAS | 2016–2021; 2026 |
| Transpiração, escoamento subsuperficial | GLDAS | 2026 |
| Previsão GFS (1–15 dias) | o dia observado, por prazo | rotina diária desde 24/11 |

Limite: fora dos anos acima, umidade 0–5 cm, temperaturas do solo e da folha, transpiração e escoamento
subsuperficial só têm a conferência física (não há observação independente para o Brasil inteiro desde 1961).

## O que falta auditar e corrigir (lista viva; riscar quando fechar)
1. **Agendamentos do `sab-pedidos` não disparam:** nenhuma execução por horário (cron) no repositório, em nenhuma
   rotina, até 25/11 13h (a fila da `main` deveria ter rodado às 10h17 e 12h17). O `sab-motor` dispara, com 7–10 h de
   atraso. Conferir se a previsão das 16h13 de 25/11 roda sozinha. Se não: causa provável é o GitHub não ter
   registrado os horários dos workflows que entraram por PR; o conserto costuma ser um commit qualquer nos arquivos
   dos workflows na `main` (por PR) ou desligar e religar cada workflow no Actions. Até lá, disparar à mão o que for
   preciso (K26 rodada 7 e a previsão diária).
2. **Motor V1.7 regravando 2026:** conferir se as tarefas do Earth Engine de 25/11 terminaram (2026 todo na V1.7). A
   fila confere sozinha antes das rodadas 1–4 da K26; a conferência da gravação de segunda (30/11) também mostra.
   Depois, a K26 rodada 1 deve ver o Rs = 0 do litoral sumir (itens C/G: hoje 1.150 pixel-dias com Rs = 0).
3. **Achados da Parte B a investigar** (2026 × GLDAS fora da régua): escoamento superficial (Norte, Sudeste, Sul) e
   subsuperficial (Norte, Sul); temperatura do solo e da folha (Norte e Centro-Oeste, abaixo). Variáveis do ERA5-Land;
   no histórico entram com a correção de leitura dos dias V1.0. Fazer um protocolo (regra antes) se for mexer.
4. **Chuva de 2026 baixa no Nordeste e no Centro-Oeste** (Parte A, Parte B e CHIRPS concordam): o teste da correção
   decide se há conserto; se não, aviso no dicionário.
5. **Avisos do dicionário a escrever:** ET real como índice (Norte r = 0,06 × MOD16); escoamento abaixo da vazão dos
   rios (−35%); e, conforme o teste, a chuva de 2026.
6. **`FAO/GAUL/2015` obsoleto** (o Earth Engine recomenda o GAUL 2025): ainda funciona; trocar muda os nomes dos
   municípios e exige K16 nova.
7. **K26 rodada 1 (24/11):** itens C (escoamento > chuva) e G (ETo gravada ≠ recalculada; Rs = 0 do litoral) com FALHA
   esperada; acompanhar a tendência depois da V1.7.
8. **Receita da correção:** a radiação do ERA5 recalculada pelo produto mensal difere até 1,55% do asset (dentro do
   limite; igual para os 4 métodos). Registrar no resultado.
9. **Conclusões e entrega:** escrever as conclusões no `REGISTRO_MANUAL.md` (seção 4) quando cada resultado sair e
   remontar o zip (passo 5 abaixo).

## Avisos conhecidos
- `FAO/GAUL/2015/level1` aparece como obsoleto nos LOG (o Earth Engine recomenda o GAUL 2025). Ainda funciona; trocar
  muda os nomes dos municípios, então exige K16 nova (está na lista "Para depois" do `00_LEIA_PRIMEIRO.md`).

## Onde está o quê
- Registro de tudo, do início até hoje: `REGISTRO_GERAL.md` (parte à mão: `registro/REGISTRO_MANUAL.md`).
- Métodos para replicação: `pesquisa/METODOS_REPLICACAO.md`; métricas: `pesquisa/METRICAS_COMPLETAS.csv.gz`;
  pares: `pesquisa/DADOS_PAREADOS.csv.gz`.
- Situação das rotinas: `rotinas/PAINEL.md`; conferência: `rotinas/conferencia/CONFERENCIA_FINAL.md`.
