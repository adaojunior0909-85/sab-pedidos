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
   - **Parte A PRONTA (25/11, 05h30):** o método de 2026 subestima a chuva em TODOS os anos de 2021–2025 e regiões
     (Brasil −9,6%; Nordeste e Centro-Oeste −12%, pior ano −16%) e superestima ETo (+3,5%) e radiação (+0,6 MJ). Isso
     explica a maior parte da chuva baixa de 2026 × CHIRPS. PRÓXIMO TRABALHO PRINCIPAL: propor ao responsável a
     correção dos dias ERA5 (ex.: calibração pelos anos recentes, 2016–2025, ou fator por década), com protocolo e
     regra fixados ANTES, teste fora da amostra (como a K21: treino em uns anos, teste em outros), simulação 05a no
     sab-motor e K16. Nada é gravado sem o responsável aprovar. Ver `pesquisa/resultados_metodo_2026/RESULTADOS_A.md`;
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
