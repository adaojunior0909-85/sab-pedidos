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
- **Escolha do método por célula** (região x estação x alvo x variável): só com 1982-2010 (registro 2 abaixo); o
  teste 2011-2025 só mede o método escolhido. Escolher pelo teste seria trapaça (viés de seleção).

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

Todas feitas ANTES de rodar o hindcast nos dados reais, por causa do teste com dados artificiais
(`teste_sintetico.py`: sinais plantados de ENSO e de tendência e regiões só com ruído, 3 sementes aleatórias).

1. **Tendência separada dos outros preditores.** Com a tendência como termo fixo em todos os modelos, uma oscilação
   longa (como as do ENSO) virava tendência falsa em 29 anos e era estendida para 2011-2025: no teste artificial, só
   a tendência dobrou o erro e contaminou os outros métodos. Agora cada método tem a versão sem tendência e a com
   tendência (sufixo `t`; C0 com tendência = C1), e a tendência é UMA por pixel, estimada com todas as quinzenas de
   emissão juntas (a de cada quinzena saía tão ruidosa quanto a própria tendência). Os métodos da tabela continuam,
   em duas versões; o ENS virou ENS = média de E2, P1, R2 e ENSt = média de C1, E2t, P1t, R2t.
2. **Escolha em duas decisões**, porque com 14 métodos a escolha pelo menor erro numa janela só de 11 anos virou
   sorte (pegou uma versão com tendência ruim enquanto o modelo certo tinha MSESS +0,31):
   a. usar tendência ou não, por variável e região, juntando estações e alvos: C1 x C0 numa validação PARA FRENTE
      dentro do treino (ajuste 1982-1999, validação 2000-2010), porque é a única decisão que depende de extrapolar;
   b. o método, dentro da família escolhida, pelo menor erro "deixando um ano de fora" em 1982-2010 (29 anos).
   A regra de aprovação não mudou.

Resultado do teste artificial depois das mudanças (3 sementes): o sinal de ENSO na Tmax do Sul foi achado e
aprovado (E2, MSESS +0,11 a +0,31), a tendência da Tmin foi achada (C1, +0,56 a +0,60) e 0 de 48 células só com
ruído foram aprovadas.

## Rodada 2 (escrita depois de ver a rodada 1 e ANTES de rodar a rodada 2)

A rodada 1 é a única pré-registrada antes de qualquer resultado. Como o teste 2011-2025 já foi visto, a rodada 2 é
**exploratória**: os números dela no teste tendem a parecer melhores do que são. Por isso:

- **Critério para aceitar a rodada 2 no lugar da 1: só os anos de treino.** A rodada 2 só substitui a 1 se, somando
  todas as células (5 regiões x 4 estações x 3 alvos), o erro dos métodos escolhidos cair nas duas medidas de
  treino: erro "ano de fora" 1982-2010 e erro da validação para frente 2000-2010, em cada variável. O teste
  2011-2025 é mostrado, mas não decide nada.
- **A prova definitiva é para frente** (piloto): previsões guardadas a partir de agora e conferidas depois.

Mudanças da rodada 2 (cada uma corrige um defeito visto na rodada 1, não é ajuste ao teste):

1. **Grade do lambda ampliada**, porque a escolha bateu no limite em quase todos os casos (R1 em 100 e R2 em 1000,
   os máximos): R1 = 0,3 a 1000; R2 = 10 a 100.000. A escolha continua pelo erro "ano de fora" no treino.
2. **Persistência da chuva na raiz e anomalias limitadas a ±3 desvios.** Uma quinzena seca com uma chuva isolada
   virava anomalia enorme (o P1 na raiz teve MSESS -1,35 no Brasil). Agora a anomalia da chuva é calculada na raiz
   da chuva, e toda anomalia de persistência (chuva, Tmax, Tmin) é limitada a ±3.
3. **Decisão "usar tendência" com os outros preditores junto.** Na rodada 1 ela comparava C1 x C0 (só a tendência),
   mas as anomalias recentes já carregam parte do aquecimento: no Paraná a família com tendência foi escolhida e o
   R2 sem tendência foi melhor. Agora a decisão (por variável e região, juntando estações e alvos, na validação
   para frente 2000-2010) compara ENSt x ENS.

Antes de rodar com os dados reais, o teste artificial (`teste_sintetico.py`, 3 sementes) precisa continuar passando.
