# Para continuar numa conversa nova (estado em 25/11/2026, ~13h de Brasília)

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
- ✅ **Protocolo da correção APROVADO** (25/11, ~07h), com 2026 × CHIRPS só como relato; congelado antes de rodar
  (commit `1de7696` do `validacoes-2`). ✅ **Emenda 1** (25/11, ~08h, pedida pelo responsável, antes de rodar; commit
  `91cd9b3`): a condição 4 usa TODOS os pixels entregues (dias de chuva e Rx1day, em cada uma das 5 regiões) e o p99
  em 1.500 pixels (300 por região) no lugar dos 150 da K21.
- ✅ **`resolucao` roda completa**, sem amostra de anos, mesmo levando ~2 dias (decisão de 25/11).
- ✅ **"Saúde do banco" virou "Conferência da gravação"** (PR #11, juntado em 25/11): `rotina_gravacao.yml`,
  `rotinas/gravacao/conferencia_gravacao.py`, `rotinas/estado/gravacao.json`.
- ✅ **Teste da correção TERMINOU (25/11, ~15h; os 120 meses):** **chuva → C3 passa** nas 4 condições (mediana do
  |viés anual| 8,4% → 4,3%; Brasil melhor em 9 de 10 anos); **radiação/ETo → nenhum passa** (o C0 fica). Resultado:
  `pesquisa/resultados_correcao_era5/RESULTADOS.md`. Falta só o relato 2026 × CHIRPS (precisa de ~30 min de GitHub;
  o erro de tipo do mês já foi corrigido no commit `c4f63f5`; zerar a entrada `correcao_era5` do
  `fila_estado_correcao_era5.json` e disparar de novo a cadeia no branch de trabalho).
- ⏳ **Próximo, com aprovação do responsável:** o motor V1.8 em simulação (05a no `sab-motor`) com a chuva dos dias ERA5
  pelo C3. O C3 NÃO precisa de climatologia nova no Earth Engine: usa a `SICSB_1986_2025` de sempre × 60 razões (12
  meses × 5 regiões) tiradas de 2021–2025 (as da Parte A). Depois: prévia de 2026, K16, aprovação e 05b (regrava só
  2026; o histórico não muda).
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
