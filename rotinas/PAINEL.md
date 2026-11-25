# Painel de controle das rotinas automáticas do SAB

Atualizado em 25/11/2026 03:28 (Brasília). Cada rotina roda sozinha no GitHub Actions deste repositório e escreve aqui o último resultado. ✅ tudo certo · 👀 conferir os números · ⚠️ atenção · ❌ falhou · ⏳ ainda não rodou.

| Rotina | Quando roda | Última execução | Situação | Resumo |
|---|---|---|---|---|
| Saúde do banco (motor gravou?) | toda segunda-feira, 14h29 | 24/11/2026 20:27 | ✅ | 343 dias de 2026 (319 ERA5 até 2026-11-15, 24 GFS até 2026-12-09); dia 2026-11-24 gravado há 11 h; versões {'V1.6': 343}; histórico intocado |
| RONI do mês (02_auditoria_roni_cpc.py) | todo dia 11, 10h23 | 24/11/2026 21:14 | ✅ | asset RONI_CPC_v6 regravado e conferido (921 estações) |
| K26, rodada 1 (2026 inteiro, só leitura) | todo dia 15, 15h41 | 24/11/2026 20:56 | 👀 | 343 dias de 2026 (até 2026-12-09); itens: A1 OK, B ATENCAO, C FALHA, G FALHA, H OK |
| Acerto da previsão GFS (1 a 15 dias) | todo dia, 16h13 | 24/11/2026 22:16 | ✅ | fotografia de 2026-11-24: 24 dias GFS (2026-11-16 a 2026-12-09) e a persistência (2026-11-15) |
| Conferência final (validações, escoamento e K26 de 1961 até a previsão) | de 2 em 2 horas, 10h17 a 20h17, até a fila acabar (depois desliga sozinha) | 25/11/2026 03:28 | ⏳ | 1 de 15 tarefas prontas |
| Piloto da previsão estendida (Tmin e Tmax) | dias 3 e 17, 08h17 | 24/11/2026 20:19 | ✅ | 1 emissão(ões); a última em 2026-11-16 |

## Detalhes da última execução de cada rotina

### Saúde do banco (motor gravou?)

✅ 24/11/2026 20:27 (Brasília)

- 343 dias de 2026 (319 ERA5 até 2026-11-15, 24 GFS até 2026-12-09); dia 2026-11-24 gravado há 11 h; versões {'V1.6': 343}; histórico intocado

### RONI do mês (02_auditoria_roni_cpc.py)

✅ 24/11/2026 21:14 (Brasília)

- asset RONI_CPC_v6 regravado e conferido (921 estações)
- Estações acrescentadas do arquivo do CPC: [[2026, 'ASO', 1.97, 2.0]]
- Resultados: `rotinas/resultados/roni/2026-11-24`

### K26, rodada 1 (2026 inteiro, só leitura)

👀 24/11/2026 20:56 (Brasília)

- 343 dias de 2026 (até 2026-12-09); itens: A1 OK, B ATENCAO, C FALHA, G FALHA, H OK
- Rs = 0 (pixels entregues, pixel-dias pesados pela máscara): 1150 (antes 1176)
- Rs abaixo de 3% de Ra: 827 (antes 1021) · Rs acima do céu claro: 19 (antes 19)
- ETo gravada diferente da recalculada (G): 693 (antes 693)
- escoamento > chuva: 116517 (antes 116419) · escoamento > 200 mm: 3823 (antes 3823)
- C e G com FALHA são esperados (escoamento x chuva; Rs = 0 do litoral, que a leitura deixa vazio): o que importa é a tendência dos números entre uma execução e outra
- Resultados: `rotinas/resultados/k26_rodada1/2026-11-24`

### Acerto da previsão GFS (1 a 15 dias)

✅ 24/11/2026 22:16 (Brasília)

- fotografia de 2026-11-24: 24 dias GFS (2026-11-16 a 2026-12-09) e a persistência (2026-11-15)
- 0 dia(s) previsto(s) conferido(s) nesta execução
- ainda nenhum dia previsto virou ERA5 (o primeiro resultado sai em cerca de uma semana)
- Resultados: `rotinas/resultados/previsao/`

### Conferência final (validações, escoamento e K26 de 1961 até a previsão)

⏳ 25/11/2026 03:28 (Brasília)

- 1 de 15 tarefas prontas
- Resultados: `rotinas/conferencia/CONFERENCIA_FINAL.md`

### Piloto da previsão estendida (Tmin e Tmax)

✅ 24/11/2026 20:19 (Brasília)

- 1 emissão(ões); a última em 2026-11-16
- conferência: ainda nenhuma (os períodos previstos ainda não terminaram ou o ERA5 não chegou)
- Resultados: `pesquisa/piloto/`

---

Se uma rotina falhar, o GitHub também manda um e-mail para quem juntou este arquivo na main. Para rodar uma rotina fora de hora: aba **Actions** → escolha a rotina na esquerda → **Run workflow**.
