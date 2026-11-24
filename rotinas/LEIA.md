# Rotinas automáticas do SAB

Tudo aqui roda sozinho no GitHub Actions deste repositório. **Para conferir, abra o [`PAINEL.md`](PAINEL.md)**: ele
mostra o último resultado de cada rotina, com os números e o que fazer se algo der errado.

| Rotina | Quando | O que faz | Grava no Earth Engine? |
|---|---|---|---|
| Saúde do banco (`saude/saude_semanal.py`) | toda segunda-feira, 09h29 | confere se o motor gravou nas últimas noites (dias de 2026 sem buraco, previsão até hoje + 10 dias, tudo na V1.6, histórico intocado) | não |
| RONI do mês (`roni/rodar_roni.py`) | todo dia 11, 10h23 | roda o `02_auditoria_roni_cpc.py` (sem mudança) e regrava o asset `RONI_CPC_v6`, com cópia de segurança e conferência | **sim** (só o RONI) |
| K26, rodada 1 (`k26/rodar_rodada1.py`) | todo dia 15, 09h41 | roda a K26 v1.12 (sem mudança) em 2026 inteiro, ~35 min, e compara com a execução anterior | não |
| Piloto (`../pesquisa/piloto.py`) | dias 3 e 17, 08h17 | emite a previsão estendida de Tmin e Tmax e confere as vencidas | não |

Horários de Brasília, todos longe da janela do motor (22h50 à 01h00). Os resultados de cada execução ficam em
`resultados/<rotina>/<data>/`; o estado de cada rotina, em `estado/<rotina>.json`.

- **Rodar fora de hora:** aba **Actions** → escolha a rotina na esquerda ("Rotina - …") → **Run workflow** → **Run workflow**.
- **Desligar uma rotina:** aba **Actions** → a rotina → **⋯** (canto direito) → **Disable workflow**.
- **Se uma rotina falhar,** o GitHub manda um e-mail para a conta que juntou estes arquivos na `main`, e o `PAINEL.md`
  mostra ❌ com o motivo.
- O `02_auditoria_roni_cpc.py` e o `K26_auditoria_final.py` daqui são cópias idênticas às da entrega
  (`07_Base_de_desenvolvimento_e_testes/02_auditoria_roni_cpc.py` e `validacoes/K26_auditoria_final.py`). Se um deles
  mudar lá, copie para cá também.
