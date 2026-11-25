# Para continuar numa conversa nova (estado em 25/11/2026, ~04h40 de Brasília)

## Cole isto na conversa nova
> Continue o trabalho do SAB a partir do ponto salvo. Primeiro, só leia (não mude nem dispare nada): no repositório
> adaojunior0909-85/sab-pedidos, busque o branch validacoes-2 (git fetch origin validacoes-2) e leia
> registro/CONTINUAR_AQUI.md, REGISTRO_GERAL.md e pesquisa/METODOS_REPLICACAO.md desse branch. Depois confira a fila:
> os arquivos rotinas/conferencia/fila_estado*.json da main e do validacoes-2, os LOG em rotinas/conferencia/logs/ e
> as últimas execuções do workflow "Rotina - Conferência final (fila)". Me mostre, em português, um resumo do que
> terminou, do que está rodando, do que quebrou e qual é o próximo passo, e só então siga os próximos passos do
> CONTINUAR_AQUI.md. Responda sempre em português.

Horários: os commits do GitHub estão em UTC; a fila e os LOG, em Brasília (UTC−3).

## Regras que a conversa nova precisa seguir
- Responder só em português; passo a passo clique a clique quando o responsável tiver de fazer algo.
- Nunca pôr credenciais em arquivo ou conversa (a do Earth Engine fica só no segredo `EE_CREDENCIAL` do GitHub).
- Não juntar nada na `main` sem o responsável pedir: abrir PR e ele faz o merge.
- Tudo no Earth Engine é SÓ LEITURA nas validações; o histórico 1961–2025 nunca é regravado.
- Toda regra de decisão é fixada ANTES de rodar (está no cabeçalho de cada script).
- Não tentar contornar sites que bloqueiam acesso (INMET).

## O que está rodando sozinho (GitHub Actions, workflow "Rotina - Conferência final (fila)")
| Onde | Tarefa | Situação |
|---|---|---|
| `main` (fila de 2 em 2 h, 10h17–20h17) | `metodo_2026_A`: a rota ERA5 do motor V1.7 aplicada a 2021–2025 × o banco (16 variáveis) | rodando desde 03h41 de 25/11 |
| `main` | `metodo_2026_B`: 2026 × GLDAS-2.1, régua 2022–2024 | depois da A |
| `main` | K26 rodada 7 (25/11 à tarde); rodadas 1–4 (2026 e previsão) a partir de 26/11, depois que o motor V1.7 regravar 2026; rodadas 5, 6, 8–11 a partir de 01/12 | agendado |
| `validacoes-2` (cadeia `so=historico`) | histórico 1961–2025 × TerraClimate e CHIRPS, 5 regiões + Brasil + 27 estados | rodando (recomeçou 04h15) |
| `validacoes-2` (cadeia `so=resolucao`) | sensibilidade à resolução: cada referência na grade do SAB × nativa, todas as variáveis e meses | rodando |
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
   - a chuva de 2026 no Centro-Oeste (−21%) e no Nordeste (−16%) × CHIRPS: a Parte A diz se é o método (se o método
     também erra assim em 2021–2025, propor correção com protocolo fixado antes; o banco não muda sem simulação);
   - o resultado da sensibilidade à resolução (`pesquisa/resultados_resolucao/RESULTADOS.md`);
   - avisos no dicionário: ET real como índice (Norte r = 0,06 × MOD16); escoamento abaixo da vazão dos rios (−35%).
5. **Atualizar a pasta de entrega:** a base que monta o zip NÃO está no GitHub. Peça ao responsável para enviar na
   conversa o último zip (`SAB_entrega_final_2026-11-25.zip`). Extraia; a base é a pasta
   `07_Base_de_desenvolvimento_e_testes`. Atualize nela `automacao_email/sab_pedidos/` com o conteúdo do GitHub
   `sab-pedidos` (main + validacoes-2) e `automacao_motor/sab-motor/` com o `sab-motor`; acrescente uma seção datada
   no topo do `LEIA_PRIMEIRO_modelo.md`; rode `python3 rodar_todos_os_testes.py` (58 testes; precisa de Node) e
   `python3 montar_entrega.py <pasta de saída>`; copie da entrega anterior o que o montador não gera (pasta
   `09_Versoes_anteriores/` e os arquivos soltos da raiz: K22, K24, K25, K26, simular_K25/K26, o guia); copie o
   `REGISTRO_GERAL.md` para a raiz; refaça o `SHA256SUMS.txt` e o zip.
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
