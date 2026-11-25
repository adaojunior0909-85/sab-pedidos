# Para continuar numa conversa nova (estado em 25/11/2026, ~04h30 de Brasília)

## Cole isto na conversa nova
> Continue o trabalho do SAB. Leia, no repositório adaojunior0909-85/sab-pedidos, branch `validacoes-2`, os arquivos
> `registro/CONTINUAR_AQUI.md`, `REGISTRO_GERAL.md` e `pesquisa/METODOS_REPLICACAO.md`, e confira a fila
> (`rotinas/conferencia/fila_estado*.json`, `rotinas/conferencia/logs/`). Responda sempre em português.

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
1. Quando `historico` e `resolucao` terminarem: rodar `python pesquisa/metricas_completas.py` e
   `python registro/gerar_registro.py`, subir, e abrir o PR `validacoes-2` → `main` (o responsável junta). Cuidado no
   PR: `rotinas/conferencia/fila_estado.json` muda nos dois lados; manter o da `main` e os `fila_estado_*.json` do branch.
2. Depois do merge: a fila da `main` roda `por_mes` e `metricas` sozinha (dependem de `metodo_2026_B` e `historico`).
3. Ler os resultados e escrever as conclusões no `registro/REGISTRO_MANUAL.md` (seção 4), principalmente:
   - a chuva de 2026 no Centro-Oeste (−21%) e no Nordeste (−16%) × CHIRPS: a Parte A diz se é o método (se o método
     também erra assim em 2021–2025, propor correção com protocolo fixado antes; o banco não muda sem simulação);
   - avisos no dicionário: ET real como índice (Norte r = 0,06 × MOD16); escoamento abaixo da vazão dos rios (−35%).
4. Atualizar a pasta de entrega (o último zip é `SAB_entrega_final_2026-11-24.zip`; o GitHub já tem tudo o que veio
   depois).

## Onde está o quê
- Registro de tudo, do início até hoje: `REGISTRO_GERAL.md` (parte à mão: `registro/REGISTRO_MANUAL.md`).
- Métodos para replicação: `pesquisa/METODOS_REPLICACAO.md`; métricas: `pesquisa/METRICAS_COMPLETAS.csv.gz`;
  pares: `pesquisa/DADOS_PAREADOS.csv.gz`.
- Situação das rotinas: `rotinas/PAINEL.md`; conferência: `rotinas/conferencia/CONFERENCIA_FINAL.md`.
