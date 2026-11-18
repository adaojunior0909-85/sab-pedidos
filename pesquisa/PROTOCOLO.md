# Pesquisa: previsão estendida de chuva e temperatura (além dos 16 dias do GFS)

Protocolo fixado **antes** de extrair qualquer dado (mesmo commit do extrator). Nada aqui pode mudar depois de ver
resultados sem registrar a mudança e o motivo no fim deste arquivo.

## Pergunta

Com o que o SAB já tem (BR-DWGD 1961-2025, ENSO, temperatura do mar do OISST), dá para prever **chuva total** e
**Tmax/Tmin médias** depois do horizonte do GFS melhor do que a média histórica? Onde, em que época e com que método?

Não se prevê o valor de cada dia além de 16 dias: o limite de previsibilidade do tempo impede. Os alvos são totais
e médias de períodos.

## Dados (fase 1, `extrair_dados.py`)

- Pixels classe A (BR-DWGD) numa malha de 1° no Brasil, malha de 0,25° no Paraná e o pixel de Cascavel-PR.
- BR-DWGD por quinzena (1-15 e 16-fim do mês), 1981 até o último dia disponível: chuva total, Tmax e Tmin médias.
- OISST v2.1 mensal (1982-): Niño 3.4, Niño 1+2, tropical 20S-20N, TNA, TSA, Atlântico Sudoeste, polos do IOD.

## Previsões simuladas (hindcast)

- **Emissão:** dias 1 e 16 de cada mês (início da quinzena q), anos 1982-2025.
- **Informação permitida:** só o que existiria no dia da emissão: BR-DWGD até a quinzena q-1 e OISST até o mês
  anterior ao da emissão. Nada da quinzena q em diante.
- **Alvos** (a quinzena q já é coberta pelo GFS):
  - `Q1` = quinzena q+1 (cerca dos dias 16-31 depois da emissão, "semanas 3 e 4");
  - `M2` = quinzenas q+2 e q+3 (cerca dos dias 31-60);
  - `M3` = quinzenas q+4 e q+5 (cerca dos dias 61-90).
- **Variáveis:** chuva total (mm), Tmax média e Tmin média (°C) do alvo.

## Métodos comparados

| Código | Método |
|---|---|
| C0 | Climatologia: média dos anos de treino (referência de todos os escores) |
| C1 | Climatologia com tendência linear no ano |
| P1 | C1 + persistência: anomalia da última quinzena e do último mês, por regressão |
| E1 | C1 + análogos de ENSO: média das anomalias dos anos de treino na mesma fase (Niño 3.4 relativo ≥ 0,5; ≤ -0,5; neutro) |
| E2 | C1 + regressão linear no Niño 3.4 relativo |
| R1 | C1 + regressão ridge com todos os preditores (ENSO, Niño 1+2, TNA, TSA, Atlântico Sudoeste, IOD, persistência), por pixel |
| R2 | Como R1, mas os coeficientes são ajustados juntando os pixels da mesma região (menos ruído) |
| ENS | Média de C1, E2, P1 e R2 |

Chuva: testada também com a raiz quadrada da chuva (distribuição assimétrica); a regressão é feita na escala da
raiz e devolvida em mm.

## Validação

- **Esquema A (principal, fora da amostra no tempo):** treino 1982-2010, teste 2011-2025. Tudo que é ajustado
  (climatologia, tendência, coeficientes, parâmetro do ridge, escolha do método) usa só 1982-2010.
- **Esquema B (estabilidade):** deixar um ano de fora, 1982-2025.
- **Escolha do método por célula** (região x estação x alvo x variável): pelo menor erro no esquema B **dentro de
  1982-2010**; o teste 2011-2025 só mede o método escolhido. Escolher pelo teste seria trapaça (viés de seleção).

## Métricas

- **MSESS** = 1 - EQM do método / EQM da climatologia C0. Positivo = melhor que a média histórica.
- **MAE** (mm ou °C), **ACC** (correlação das anomalias).
- **Acerto de tercil** (abaixo/normal/acima do normal; 33% = acaso) e **RPSS** (previsão em probabilidade, com a
  distribuição dos erros do treino).
- Intervalo de 95% por bootstrap de anos.

## Regra de aprovação (fixada antes)

Um método vira produto numa célula (região x estação x alvo x variável) só se, no esquema A:

1. MSESS ≥ 0,05 contra C0 **e** o limite inferior do IC 95% do MSESS > 0;
2. RPSS > 0;
3. no esquema B, MSESS > 0;
4. para métodos além de C1: MSESS também > 0 contra C1 (o ganho não pode ser só a tendência).

Onde nenhum método passar, o produto diz "sem sinal: use a média histórica".

## Fora do escopo desta fase

Mudar a previsão GFS dos dias 1-16 (já auditada nas K7, K9A, K11, K19, K21); modelos de longo prazo de fora do
Earth Engine (GEFS estendido, C3S); aprendizado de máquina não linear (só depois, se a regressão linear mostrar sinal).

## Registro de mudanças

(nenhuma)
