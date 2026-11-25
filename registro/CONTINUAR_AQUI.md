# Para continuar numa conversa nova (estado em 25/11/2026, ~07h de Brasília; revisto às ~07h)

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
  - `claude/tender-maxwell-6ka6dt` (25/11, ~07h): o `validacoes-2` + a `main` (juntadas, com os arquivos de situação da
    `main`) + o protocolo aprovado. Branch de trabalho atual (script do teste da correção). O registro e o protocolo
    também estão no `validacoes-2`: uma versão só.
- **Uma conversa por vez.** Duas conversas mexendo no repositório ao mesmo tempo se atropelam: a antiga para quando a
  nova começa.

## Decisões esperando o responsável
0. ✅ **Protocolo da correção APROVADO (25/11, ~07h)**, incluindo 2026 × CHIRPS só como relato (fora da regra).
   Congelado no commit `1de7696` do `validacoes-2` (`161324a` no branch de trabalho) ANTES de rodar.
1. **Teste da correção DISPARADO (25/11, ~08h), rodando sozinho** na fila do branch `claude/tender-maxwell-6ka6dt`
   (cadeia `so=correcao_era5`; os resultados sobem nesse branch em `pesquisa/resultados_correcao_era5/`, o LOG em
   `rotinas/conferencia/logs/correcao_era5.txt` e o estado em `rotinas/conferencia/fila_estado_correcao_era5.json`).
   **Emenda 1 do protocolo** (pedida pelo responsável, antes de rodar; commit `91cd9b3`): a condição 4 passou a usar
   TODOS os pixels entregues (dias de chuva e Rx1day, em cada região) e o p99 em 1.500 pixels (300 por região) no
   lugar dos 150 da K21. Script `pesquisa/validar_correcao_era5.py`; testes sem Earth Engine
   `pesquisa/teste_correcao_era5.py` (23 conferências ok). Ordem: conferência da receita (para se não bater com o
   `SICSB_1986_2025`), pixels (30 anos de somas + 10 anos de dias), 120 meses regionais, 2026 × CHIRPS, resumo.
   Tempo estimado: várias horas, em mais de uma execução da fila. Se quebrar: ler o LOG, corrigir, apagar a entrada
   `correcao_era5` do `fila_estado_correcao_era5.json` e disparar de novo:
   `gh api -X POST repos/adaojunior0909-85/sab-pedidos/actions/workflows/rotina_conferencia.yml/dispatches -f ref=claude/tender-maxwell-6ka6dt -f 'inputs[so]=correcao_era5'`
   Quando terminar: ler `RESULTADOS.md`, levar ao responsável e trazer script e resultados para o `validacoes-2`.
2. **Criar a climatologia nova no Earth Engine** (ex.: `SICSB_2016_2025`): é ESCRITA; aprovação separada e só se algum
   método passar. O asset atual e o histórico não mudam.
3. **Juntar o PR `validacoes-2` → `main`** quando `historico` e `resolucao` terminarem.
   - Ritmo (25/11, 10h30): `historico` com 1961–1981 prontos (~15 min/ano; faltam ~11 h); `resolucao` com o CHIRPS de
     1981–1993 pronto (~25 min/ano; faltam ~40 h: o resto do CHIRPS e os 65 anos do TerraClimate). **Decisão do
     responsável (25/11): a `resolucao` roda completa, sem amostra de anos**, mesmo levando ~2 dias.

## O que está rodando sozinho (GitHub Actions, workflow "Rotina - Conferência final (fila)")
| Onde | Tarefa | Situação |
|---|---|---|
| `main` (fila de 2 em 2 h, 10h17–20h17) | `metodo_2026_A`: a rota ERA5 do motor V1.7 aplicada a 2021–2025 × o banco (16 variáveis) | **pronta** (04h43 de 25/11) |
| `main` | `metodo_2026_B`: 2026 × GLDAS-2.1, régua 2022–2024 | **pronta** (06h47 de 25/11) |
| `main` | K26 rodada 7 (25/11 à tarde); rodadas 1–4 (2026 e previsão) a partir de 26/11, depois que o motor V1.7 regravar 2026; rodadas 5, 6, 8–11 a partir de 01/12 | agendado |
| `validacoes-2` (cadeia `so=historico`) | histórico 1961–2025 × TerraClimate e CHIRPS, 5 regiões + Brasil + 27 estados | rodando (recomeçou 04h15) |
| `validacoes-2` (cadeia `so=resolucao`) | sensibilidade à resolução: cada referência na grade do SAB × nativa, todas as variáveis e meses | rodando (recomeçou 04h33, depois da correção do erro 'features') |
| `main` | rotinas fixas: previsão 16h13 diária, saúde (seg 14h29), RONI (dia 11), K26 (dia 15), piloto (dias 3 e 17) | ligadas |

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
   2026), peça para adicionar o repositório adaojunior0909-85/sab-motor. A `rotinas/PAINEL.md` (saúde do banco)
   mostra quantos dias estão em cada versão do motor.

## Avisos conhecidos
- `FAO/GAUL/2015/level1` aparece como obsoleto nos LOG (o Earth Engine recomenda o GAUL 2025). Ainda funciona; trocar
  muda os nomes dos municípios, então exige K16 nova (está na lista "Para depois" do `00_LEIA_PRIMEIRO.md`).

## Onde está o quê
- Registro de tudo, do início até hoje: `REGISTRO_GERAL.md` (parte à mão: `registro/REGISTRO_MANUAL.md`).
- Métodos para replicação: `pesquisa/METODOS_REPLICACAO.md`; métricas: `pesquisa/METRICAS_COMPLETAS.csv.gz`;
  pares: `pesquisa/DADOS_PAREADOS.csv.gz`.
- Situação das rotinas: `rotinas/PAINEL.md`; conferência: `rotinas/conferencia/CONFERENCIA_FINAL.md`.
