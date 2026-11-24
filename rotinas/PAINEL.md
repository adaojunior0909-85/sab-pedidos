# Painel de controle das rotinas automáticas do SAB

Atualizado em 24/11/2026 20:22 (Brasília). Cada rotina roda sozinha no GitHub Actions deste repositório e escreve aqui o último resultado. ✅ tudo certo · 👀 conferir os números · ⚠️ atenção · ❌ falhou · ⏳ ainda não rodou.

| Rotina | Quando roda | Última execução | Situação | Resumo |
|---|---|---|---|---|
| Saúde do banco (motor gravou?) | toda segunda-feira, 09h29 | 24/11/2026 20:21 | ✅ | 343 dias de 2026 (319 ERA5 até 2026-11-15, 24 GFS até 2026-12-09); dia 2026-11-24 gravado há 11 h; histórico intocado |
| RONI do mês (02_auditoria_roni_cpc.py) | todo dia 11, 10h23 | 24/11/2026 20:22 | ✅ | teste (só auditoria; GRAVAR_ASSET = False): rodou sem erro; nada foi gravado |
| K26, rodada 1 (2026 inteiro, só leitura) | todo dia 15, 09h41 | 22/11/2026 15:47 | 👀 | 341 dias de 2026 (até 2026-12-07); itens: A1 OK, B ATENCAO, C FALHA, G FALHA, H OK |
| Piloto da previsão estendida (Tmin e Tmax) | dias 3 e 17, 08h17 | 24/11/2026 20:19 | ✅ | 1 emissão(ões); a última em 2026-11-16 |

## Detalhes da última execução de cada rotina

### Saúde do banco (motor gravou?)

✅ 24/11/2026 20:21 (Brasília)

- 343 dias de 2026 (319 ERA5 até 2026-11-15, 24 GFS até 2026-12-09); dia 2026-11-24 gravado há 11 h; histórico intocado

### RONI do mês (02_auditoria_roni_cpc.py)

✅ 24/11/2026 20:22 (Brasília)

- teste (só auditoria; GRAVAR_ASSET = False): rodou sem erro; nada foi gravado
- Estações acrescentadas do arquivo do CPC: [[2026, 'ASO', 1.97, 2.0]]
- Resultados: `rotinas/resultados/roni/2026-11-24`

### K26, rodada 1 (2026 inteiro, só leitura)

👀 22/11/2026 15:47 (Brasília)

- 341 dias de 2026 (até 2026-12-07); itens: A1 OK, B ATENCAO, C FALHA, G FALHA, H OK
- Rs = 0 (pixels entregues, pixel-dias pesados pela máscara): 1176
- Rs abaixo de 3% de Ra: 1021 · Rs acima do céu claro: 19
- ETo gravada diferente da recalculada (G): 693
- escoamento > chuva: 116419 · escoamento > 200 mm: 3823
- execução de referência (22/11, K26 v1.12 no Colab), antes da rotina automática
- Resultados: `rotinas/resultados/k26_rodada1/2026-11-22`

### Piloto da previsão estendida (Tmin e Tmax)

✅ 24/11/2026 20:19 (Brasília)

- 1 emissão(ões); a última em 2026-11-16
- conferência: ainda nenhuma (os períodos previstos ainda não terminaram ou o ERA5 não chegou)
- Resultados: `pesquisa/piloto/`

---

Se uma rotina falhar, o GitHub também manda um e-mail para quem juntou este arquivo na main. Para rodar uma rotina fora de hora: aba **Actions** → escolha a rotina na esquerda → **Run workflow**.
