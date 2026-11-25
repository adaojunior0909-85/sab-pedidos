# ROTEIRO SAB v4.1, revisão K9A (20/10/2026): passo a passo clique a clique

Este roteiro substitui todos os anteriores (v2, v3 e v4). Ele junta cinco fontes:
- a auditoria de 20/10/2026;
- a auditoria complementar J (10:19);
- as decisões tomadas em 20/10/2026 (Parte A);
- as duas revisões independentes do pacote v4 (A: matriz, conferência e motor; B: máscara, RONI, painel, normais e auditoria), com todos os achados já corrigidos;
- as auditorias K (14:57) e K1d corrigida (15:05), que confirmaram as decisões e motivaram os ajustes da v4.1 (Parte A, A.3);
- a validação K8 (fora da amostra), que definiu a escala de variância como método da Tmax e da Tmin da previsão, e a revisão final do pacote (`CHANGELOG_REVISAO_FINAL.md`);
- as validações K9 e K9A (todas as variáveis da previsão, 2015 a 2025), que passaram a umidade relativa e a radiação para a escala de variância (Parte A, nota 11; `CHANGELOG_REVISAO_K9A.md`).

**Símbolos:** ✅ = conferido; ℹ️ = só informação, siga em frente; ⚠️ = pare, a não ser que o roteiro diga que aquele ⚠️ é aceitável; ❌ = pare sempre.

**Nenhum arquivo precisa ser editado.** A única exceção possível: se o script 02 parar por "empate" no RONI, ele mesmo diz qual valor digitar e onde. Os métodos da previsão já vêm decididos no 05a e no 05b: Tmax e Tmin pela escala de variância (`METODO_TEMP_GFS = 'variancia'`, K8) e umidade relativa e radiação também pela escala de variância (`METODO_UR_RS_GFS = 'variancia'`, K9A).

**Regra nova: rode um script de cada vez.** Não rode dois scripts do pacote ao mesmo tempo (nem em abas diferentes do Colab, nem Colab e Code Editor juntos). O Earth Engine limita os cálculos simultâneos do projeto e devolve `Too many concurrent aggregations` (erro 429), como aconteceu na primeira tentativa da K8. As tarefas de exportação que continuam na aba **Tasks** depois que o script terminou (como as 12 da etapa 3) não contam: elas podem terminar enquanto você roda a etapa seguinte. O que não pode é um script ainda rodando numa aba (o 05b, por exemplo, fica horas rodando) enquanto outro roda em outra; espere a linha final de um antes de começar o outro.

**Antes de cada script que grava (01b, 02, 03 e 05b), use uma sessão limpa do Colab:** um notebook novo ou, no mesmo notebook, **Ambiente de execução → Reiniciar sessão**. Os scripts de simulação e de auditoria (01a, 07, 08 e as validações) deixam a trava de somente leitura ligada na sessão; se ela estiver ligada, o script que grava para logo no início, sem gravar nada, e pede para reiniciar.

O pacote v4.1 tem 11 scripts de execução e, na pasta `validacoes`, as validações já executadas (K8, K9, K9A e K11) e o diagnóstico K10; todos somente leitura, **não precisam ser rodados de novo**. O inventário completo (o que é atual, o que aposentar e o que nunca rodar) está no `00_LEIA_PRIMEIRO_INVENTARIO.md`:

| Ordem | Arquivo | Onde | Grava algo? |
|---|---|---|---|
| 1a | `01a_mascara_qualidade_SIMULACAO.py` | Colab | Não |
| 1b | `01b_mascara_qualidade_GRAVACAO.py` | Colab | Cria `SAB_MASCARA_QUALIDADE` (1 imagem) |
| 2 | `02_auditoria_roni_cpc.py` | Colab | Cria ou atualiza `RONI_CPC_v6` |
| 3 | `03_matriz_gfs_v2_1.py` | Colab | Cria `SICSB_MATRIZ_GFS_V2` (12 imagens, versão V2.1) |
| 4 | `04_conferencia_matriz_gfs.js` | Code Editor | Não |
| 5a | `05a_motor_sab_v1_5_SIMULACAO.py` | Colab | Não |
| 5b | `05b_motor_sab_v1_5_GRAVACAO.py` | Colab | Só dias de 2026 do `SAB_V1` |
| 6 | `06_painel_sab_2026_10_4.js` | Code Editor | Não |
| 7a | `07a_normais_CONFERIR_1991_2020.py` | Colab | Não |
| 7b | `07b_normais_CONFERIR_1961_1990.py` | Colab | Não |
| 8 | `08_auditoria_completa_SAB.py` | Colab | Não |
| — | `validacoes/K8_validacao_quantis.py`, `validacoes/K9_validacao_todas_variaveis.py`, `validacoes/K9A_validacao_ampliada.py` e `validacoes/K11_validacao_razao_desvios_prazos_longos.py` | Colab | Não (só para refazer as validações, por exemplo quando entrar o GFS v17) |
| — | `validacoes/K10_diagnostico_tmax_recorde.py` | Colab | Não (só se a J5a da etapa 8 der ⚠️) |

---

## PARTE A. Decisões e notas para a tese

### A.1 Decisões tomadas em 20/10/2026

| Decisão | Escolha | Motivo |
|---|---|---|
| Período de treino da matriz GFS | Só GFS v16: rodadas 00Z de 23/03/2021 a 31/12/2025 | A calibração estatística deve ser treinada numa versão fixa do modelo (Hamill, Whitaker e Mullen, 2006, BAMS 87). O v16 entrou em 22/03/2021 às 12 UTC (NCEP/EMC). |
| Faixas de prazo | Todos os dias de cada faixa (1; 2 a 5; 6 a 10; 11 a 15) | A matriz antiga usava só os dias 1, 3, 8 e 13 e era aplicada à faixa inteira. |
| Pixels de borda do histórico | Máscara de qualidade aplicada na leitura; a trava do histórico continua fechada | Só 0,28% dos pixels têm o defeito, e reprocessar 23.741 dias não compensa. |
| Motor | Só rodadas 00Z completas. Último dia incompleto sem chuva, radiação e ETo. Marca de confiança por prazo. | Mesmas condições do treino da matriz. |
| Tmax e Tmin da previsão (revisão final) | **Escala de variância** (`METODO_TEMP_GFS = 'variancia'` no 05a e no 05b) | A K7 mostrou que a correção aditiva deixa o máximo diário cerca de 3 °C acima do observado; a K8 (validação fora da amostra em 2025) confirmou a variância como a melhor das três (A.3). A K9A confirmou de novo (2025 e cada ano de 2021 a 2025). |
| Tmax e Tmin da previsão nos prazos de 6 dias em diante (revisão K11, 22/10/2026) | **Razão dos desvios no máximo 1** (`RAZAO_DESVIO_MAX_LONGO = 1.0` no 05a e no 05b; nos prazos 1 a 5 continua 2) | A escala de variância inflava as anomalias nos prazos longos, e a previsão de 26/10 em Casa Nova-BA saiu com 45,24 °C, com o GFS em 35,41 °C (K10). K11, nos prazos 8 e 13: erro da Tmax −0,6 % e da Tmin −5,3 %, menos previsões além do limite físico do ponto e geada prevista mais perto da observada; ganho nos 5 anos do GFS v16. |
| Umidade relativa e radiação da previsão (revisão K9A) | **Escala de variância** (`METODO_UR_RS_GFS = 'variancia'` no 05a e no 05b); vento e chuva continuam como estavam | K9A: erro da UR −25%, da radiação −14% e da ETo −13%, com ganho em cada um dos 5 anos do GFS v16 (nota 11). |

### A.2 Para registrar na tese (não muda o código)

1. **Convenção do dia de chuva.**
   - No BR-DWGD, o dia D é a chuva das 12 UTC de D−1 às 12 UTC de D (leitura das 9 h). A evidência é a comparação com o IMERG: Spearman 0,690 contra 0,594 do dia civil, com 58 de 60 pontos de acordo.
   - ERA5 e GFS usam 00–24 UTC. As médias mensais praticamente não mudam: no teste com o IMERG, a mediana da razão foi 1,000 e o p5–p95 ficou entre 0,907 e 1,086.
   - Nas comparações diárias há defasagem de meio dia. As 12 h entre 12 UTC e 24 UTC de 31/12/2025 não caem em nenhum dia.
   - O CSV diário traz a coluna `Janela_Chuva_UTC`.
2. **Escoamento e "chuva efetiva" são índices não validados.**
   - O fator SMAP/ERA5 do escoamento superficial tem mediana de 1,6 em janeiro, 2,6 em abril, 6,7 em julho e 2,3 em outubro, com p99 de até 94,6 (auditoria J4, percentis exatos).
   - Em julho, mais da metade dos pixels bate no teto 5.
   - O balanço hídrico do banco não fecha: o resíduo é de cerca de 400 mm/ano (cabeçalho do 07).
   - Auditoria K6: o escoamento anual passa da chuva em 1,16% dos pixels em 1981 e em 0,05% a 0,3% nos outros anos (no ERA5, em 0%). O escoamento do SAB é 26% a 32% da chuva no Brasil, contra 33% a 43% no ERA5. A K6 leu o valor bruto; o painel já limita o fator dos dias V1.0 a 5 na leitura, e em 2026 (com o limite) ainda ocorre em 0,05% dos pixels.
3. **RONI.**
   - O CPC passou a usar oficialmente o índice relativo (RONI) em 01/02/2026 (aviso do NWS). O RONI é a anomalia do Niño 3.4 menos a média dos trópicos de 20°S a 20°N, reescalada, em média móvel de 3 meses (L'Heureux et al., 2024, J. Climate 37).
   - O asset antigo batia com o CPC de 1950 a 1979 e, a partir de 1980, continha a réplica OISST. Resultados antigos com o filtro de ENSO depois de 1980 devem ser refeitos.
4. **SPI das normais B1.1.**
   - A gama foi ajustada com no mínimo 10 anos com chuva. Na leitura, a regra é de pelo menos 20 anos com chuva, calculados como `round(n × (1 − q0))`.
   - O `round` é obrigatório: q0 é float32, e 30 × (1 − float32(1/3)) = 19,999998.
   - O painel 2026.10.4 ainda não lê as normais.
5. **Pixels do histórico que não vêm do BR-DWGD (auditorias J1, J2, K1 e K1d corrigida; o mesmo conjunto em todos os anos):**

   | Classe | Pixels com o centro no Brasil (K1d) | Soma ponderada pela área (J1) | O que é |
   |---|---|---|---|
   | A | 70.524 (99,59%) | 70.364 | Idêntico ao BR-DWGD |
   | B | 241 (0,34%); cerca de 300 contando o litoral com centro no mar | 204 (0,29% da área) | Lagoas e estuários (lagoas dos Patos e Mirim no RS, RN, MA, CE, PA…). O BR-DWGD existe, mas foi descartado porque o ERA5-Land é mascarado nesses pixels; o valor diário gravado não tem relação com o BR-DWGD (K1c: chuva de −24 a +21 mm entre os percentis 5 e 95). |
   | C | 48 (0,07%); cerca de 1.060 outros com o centro fora do Brasil | 1.109 (0,32% da área) | Sem BR-DWGD. 78% vêm do ERA5 calibrado; 22% (cerca de 239) não têm nem ERA5 e foram preenchidos pelos vizinhos. |

   - O conjunto de pixels é o mesmo de 1961 a 2025 (K1a, 65 anos): C, D e A + B constantes. Em 17 das 65 datas de julho, até 7,5 pixels B ficam iguais ao BR-DWGD por coincidência (dia seco e ETo baixa nas lagoas do RS); por isso a máscara define B pela união de 5 dias (v4.1).
   - ETo diária de até 14,6 mm nos pixels C, sobre o reservatório de Itaipu e os rios Paraná e Paraguai (K1c): é evaporação de água aberta, não ETo de referência.
   - Efeito nas normais 1991–2020 de tirar B e C (K1d corrigida, média ponderada pela área): menos de 0,1 °C nas temperaturas, menos de 0,2 ponto na UR e menos de 0,3% na ETo em qualquer estado e mês; até 2,2% da média anual do estado na chuva (MA), na ET real (RN) e na chuva máxima de 1 dia. No Brasil, no máximo 0,7%. Em área, B e C ocupam 4,5% do RJ, 3,3% do RN e do RS, e 0% de MG, GO, DF e TO.
   - Os pixels B e C se comportam como água e litoral: tirá-los baixa a Tmin, a UR, a ET real e os dias de chuva em vários estados nos 12 meses (sinal constante; teste binomial p = 0,0005, com meses não independentes).
   - Tratamento: máscara de qualidade na leitura. A classe 4 (C com centro fora do Brasil) sai das extrações, e as classes B e C aparecem na coluna `Qualidade_Pixel`. A rota definitiva do motor V1.5 foi corrigida para os anos futuros. **Para municípios do litoral e das lagoas**, use só os pixels A ou informe a fração B/C: ali ela pode ser bem maior que a do estado.
6. **Calibração por escala linear mensal.**
   - Corrige só a média mensal, não a variância, a frequência de dias com chuva nem os extremos (Teutschbein e Seibert, 2013, HESS 17).
   - Os extremos diários dos dias provisórios e de previsão não são comparáveis aos limiares das normais.
   - Evidência (J5): nos dias de previsão da matriz V1, a Tmax máxima nacional passou de 44,8 °C, o recorde do INMET (Araçuaí, 19/11/2023), em 4 de 26 dias, e houve salto de +2,4 °C na emenda com o ERA5.
   - A correção aditiva de outubro é negativa na mediana (−1,19 °C; J4), então a cauda quente vem do próprio GFS.
   - Evidência (K7, set–nov/2025, matriz V1): nos prazos de 8 e 13 dias o viés médio da Tmax é zero (p = 0,92 e 0,80), mas o máximo diário nacional fica +2,9 e +2,6 °C acima do BR-DWGD (teste t, gl = 30, p < 10⁻⁹), e a área acima de 40 °C é 6 vezes a observada. A correção da média não alcança a cauda.
   - A revisão de Teutschbein e Seibert (2012, J. Hydrol. 456–457, 12–29) avaliou seis métodos de correção para chuva e temperatura; o mapeamento de distribuição foi o melhor. A v4.1 usa a escala de variância (corrige média e variância com as bandas de desvio da matriz V2.1).
   - Evidência (K8, treino 2021–2024, teste em 2025 inteiro, 300 pontos, 146.400 previsões nos prazos 1, 3, 8 e 13 dias).
     - Com as estatísticas de treino mês a mês, como a matriz V2.1 calcula (conta refeita na revisão final): MAE da Tmax 1,58 °C com a variância contra 1,99 °C com a aditiva; diferença de −0,41 °C (IC 95% de −0,45 a −0,37, bootstrap por dia, 122 dias), com ganho nos 4 prazos. Dias com Tmax acima de 35 °C: 12,4% contra 17,8% (observado 11,6%); acima de 40 °C: 0,08% contra 0,28% (observado 0,10%).
     - Com a janela de 3 meses da própria K8: variância 1,540 °C, mapeamento de quantis 1,546 °C e aditiva 1,972 °C.
     - Tmin: empate prático. MAE 1,085 °C com a variância contra 1,070 °C com a aditiva (+0,015 °C); noites abaixo do P10 em 9,2% e 9,1% dos casos (observado 9,3%).
     - Como a variância empata com os quantis e não exige matriz nova, o mapeamento de quantis fica para a V3.
   - A K9A (todos os dias de 2021 a 2025, treino com cerca de 120 dias por ponto, prazo e mês) confirmou: MAE da Tmax 1,56 °C com a variância, 1,58 com os quantis e 1,96 com a aditiva, e a variância ganhou nos 5 anos do v16. Na Tmin a aditiva erra 0,6% menos (abaixo dos 3% da regra), mas a variância acerta melhor a frequência de geada (Tmin ≤ 2 °C: 0,119% contra 0,108% observado; aditiva 0,089%).
7. **Previsão.**
   - Os dias de prazo 11 a 15 (e o 16º) têm confiança baixa e não devem ser usados como dado.
   - A NOAA propôs o GFS v17 para outubro de 2026. Quando ele entrar, a matriz V2.1 (treinada no v16) precisa ser reavaliada.
8. **Análogos de ENSO.**
   - A "probabilidade" é a fração dos 10 análogos, não uma previsão calibrada.
   - O IC exato de 95% (Clopper–Pearson) para 10 de 10 vai de 69,2% a 100%; para 5 de 10, de 18,7% a 81,3%.
9. **Extração por município.** O CSV é por pixel, sem peso por área: qualquer pixel que encoste no município entra inteiro. Para a média do município, pondere pela área (melhoria futura).
10. **Janela da chuva do GFS (K3b).** Na mesma rodada, somar a chuva das 12 UTC da véspera às 12 UTC do dia combina melhor com o BR-DWGD que somar das 00 às 24 UTC: Spearman 0,711 contra 0,675 (+0,035; IC 95% de +0,027 a +0,045) e acerto de chuva ≥ 1 mm (ETS) 0,415 contra 0,370 (+0,045; IC de +0,035 a +0,056), bootstrap por dia com 93.896 pares; sem diferença na chuva ≥ 10 mm. Não foi adotada na v4.1: mudar só o GFS contaria 12 h duas vezes na emenda com os dias ERA5 (00–24 UTC), e a razão da chuva muda entre prazos (K3), o que exige refazer a matriz. Fica para a V3, com ERA5-Land horário e GFS na mesma janela.
11. **Validação de todas as variáveis da previsão (K9 e K9A).**
   - Desenho da K9A: os mesmos 300 pontos da K8; todos os dias de 01/07/2015 a 31/12/2025; prazos 1, 3, 8 e 13 dias; GFS composto como a matriz e o motor; estatísticas de treino por ponto, prazo e mês; cada versão do GFS treinada e testada só com ela mesma.
   - Três testes: (A) oficial, GFS v16, treino até 2024 e teste em 2025 (438.000 previsões); (B) no v16, cada ano de 2021 a 2025 testado com o treino nos outros; (C) o mesmo nas versões antigas v14 e v15 (só informação; o v13 ficou sem dados suficientes por falha do acervo do Earth Engine em 2015–2016).
   - Regra fixada antes de rodar: um método só substitui o do motor se errar pelo menos 3% menos no teste A, com o IC 95% (bootstrap de dias) inteiro a favor, sem piorar o volume, o acerto dos dias de chuva nem o erro do total mensal, e se errar menos em todos os anos do teste B.
   - Resultado (MAE no teste A): UR 6,65 → **4,98** pontos (−25%; IC −1,72 a −1,62); radiação 3,51 → **3,03** MJ/m²/dia (−14%; IC −0,51 a −0,44); ETo 0,704 → **0,611** mm/dia (−13%), com o erro do total mensal da ETo de 6,3% para 5,7%. As três passaram nos 5 anos do v16. Tmax, Tmin, vento e chuva: nenhuma alternativa passou na regra.
   - Controle da ETo: o Penman do motor alimentado com as variáveis do próprio BR-DWGD reproduz a ETo do BR-DWGD com erro de 0,038 mm/dia. A radiação explica cerca de 2/3 do erro da ETo da previsão.
   - Chuva: com o treino de 120 dias, o "GFS sem correção" erra 2,9% menos no erro diário (abaixo da regra), mas o motor tem menor erro do total mensal (34,2% contra 35,7%; na seca, 39,3% contra 45,6%) e melhor acerto dos dias de chuva. O fator foi mantido. O fator limitado a [0,5; 2] foi um pouco melhor nos totais mensais em todos os anos (0,4 a 1,2 ponto), abaixo da regra; fica como candidato da V3.
   - **Limitações registradas:** a variância prevê metade dos dias muito secos (UR < 30%: 0,09% contra 0,18% observado; com o método anterior, 0,20%) e menos dias de ETo acima de 6 mm (3,3% contra 4,3% observado). O mapeamento de quantis preserva a cauda seca da UR com quase o mesmo ganho, mas exige percentis na matriz (V3).
   - Nas versões antigas, o ganho da UR se repetiu (6 de 6 anos); o da radiação ficou perto de zero (4 de 6 anos, ±3%). O ganho da radiação depende da versão do modelo: a validação deve ser refeita quando o GFS v17 entrar (Parte 4).
   - "Melhor" significa mais próximo do BR-DWGD, que é a referência de toda a série histórica do SAB: a escala de variância reproduz a variabilidade diária do BR-DWGD, que é menor que a de um ponto isolado por ser um campo interpolado.

### A.3 O que as auditorias K e K1d mediram (20/10/2026, tarde)

| Decisão | Medida | Resultado |
|---|---|---|
| Só GFS v16 (K2) | Erro do GFS por versão, controlando o mês (prazo 1 dia, Brasil, erro-padrão HAC) | As versões antigas erram diferente: chuva 25% a 30% maior (χ²(2) = 169,8; p = 1,4 × 10⁻³⁷), UR +2,9 pontos, radiação +1,1 MJ, Tmin +0,39 °C. Tmax (+0,1 °C) e vento sem efeito prático. **Confirmada.** |
| Todos os dias da faixa (K3a) | Erro por prazo dentro de cada faixa (Friedman, 95 dias pareados) | Diferenças pequenas mas reais na faixa 2 a 5 (chuva χ²(3) = 60,8; radiação χ²(3) = 41,7); a média da faixa erra menos que 1 dia representativo; o L1 difere do L2 (Wilcoxon p < 10⁻⁷). **Confirmada.** |
| Só rodada 00Z (K4) | Completude e atraso das rodadas nos últimos 12 dias | 100% completas; a 00Z fica pronta em mediana 5,7 h depois (02h42 de Brasília) e no pior caso 12,3 h (09h18). **Confirmada; rode o motor depois das 10h.** |
| Chuva da previsão na seca (K5) | Regras de correção contra o BR-DWGD (79.376 pares, bootstrap por dia) | A V1.5 recupera o volume (0,64 para 0,78) e melhora o acerto dos dias de chuva (ETS +0,019; IC de +0,013 a +0,025), sem inflar a chuva forte; o erro absoluto sobe 0,06 mm. O "menor erro sem calibrar" vem de o erro absoluto favorecer quem prevê pouca chuva. **Mantida.** |
| Pixels de borda (K1a, K1c, K1d) | Estabilidade em 65 anos e efeito nas normais | Ver nota 5. **Confirmada; máscara ajustada (união de 5 dias).** |
| Escoamento (K6) | Escoamento anual maior que a chuva | Ver nota 2. **Fica como índice; correção para a V3.** |
| Tmax da previsão (K7) | Tmax do GFS corrigido pela matriz V1 contra o BR-DWGD | Ver nota 6. Cauda quente confirmada. |
| Método da Tmax (K8) | Aditiva x quantis x variância, fora da amostra (2025) | Ver nota 6. **Escala de variância adotada.** |
| Todas as variáveis da previsão (K9 e K9A) | Cada correção do motor contra as alternativas, 2015 a 2025, fora da amostra | Ver nota 11. **UR e radiação passam para a escala de variância; Tmax, Tmin, vento e chuva mantidos.** |
| Janela da chuva (K3b) | 00–24 UTC contra 12–12 UTC | Ver nota 10. **Fica para a V3.** |

- A K1d original apontava diferenças de até 239% nas normais. Era erro de conta do script (soma ponderada dividida por contagem simples): a K1d corrigida mostra no máximo 0,31% na UR, onde a original mostrava 9,2%.

---

## PARTE 1. O que acontece com cada coisa que já está no seu Earth Engine

| O que você tem hoje | O que acontece | Pode ser desfeito? |
|---|---|---|
| `SAB_V1`, dias de 1961 a 2025 (23.741 imagens) | **Nada.** A trava do motor impede tocar em qualquer dia até 31/12/2025. Os 204 pixels B e os 1.109 pixels C (Parte A, nota 5) são tratados na leitura, pela máscara de qualidade, e não no banco. | Não há o que desfazer |
| `SAB_V1`, dias de 2026 (279 provisórios ERA5 e 26 de previsão GFS, todos V1.3) | **São refeitos pela V1.5** na etapa 5b. Nos provisórios ERA5, só mudam as 2 bandas de umidade do solo (cerca de 0,4% na média), e entram as propriedades novas `fonte` e `janela_chuva_utc`. Nos dias de previsão, todas as bandas calibradas mudam (matriz V2.1, só rodada 00Z, calibração nova de chuva, vento, radiação e umidade relativa). | Sim: rodar o motor V1.3 de novo recria os dias V1.3 (conferido no código do V1.3) |
| `SAB_V1_TMP` (vazia) | Usada como passagem: cada dia novo é gravado nela e depois substitui o dia antigo no `SAB_V1`. | Não guarda nada |
| `SICSB_1986_2025` e `SICSB_SOLO_2015_2025` | Nada (só leitura) | Não há o que desfazer |
| `SICSB_MATRIZ_GFS` (V1) | Nada; o motor V1.5 passa a usar a V2.1 | Continua disponível |
| `RONI_Calibrado_Sazonal_1950_1980` | Nada; o painel passa a usar o `RONI_CPC_v6` | Continua disponível |
| Pasta `Baselines` (48 imagens B1.1) | Nada nos dados (só leitura). Só a permissão de leitura passa a ser pública na etapa 7. | A permissão pode ser revertida |
| Script do painel no Code Editor | Substituído pela versão 2026.10.4, depois de uma cópia de segurança | Sim: colar a cópia de volta |
| Notebook do motor V1.3 no Colab | Nada; o V1.5 roda num notebook novo | Continua disponível |
| CSVs já exportados para o Drive | Nada | Não há o que desfazer |
| **Assets novos** | `SAB_MASCARA_QUALIDADE` (etapa 1), `RONI_CPC_v6` (etapa 2) e `SICSB_MATRIZ_GFS_V2` (etapa 3) | Podem ser apagados |

**Cota de processamento.**
- As tarefas mais pesadas são a matriz GFS V2.1 (etapa 3: 12 tarefas, cerca de 348 mil imagens do GFS lidas) e o reprocessamento dos cerca de 305 dias de 2026 (etapa 5b).
- Se a cota mensal do projeto acabar, nada é perdido: o projeto só fica mais lento até o dia 1º do mês seguinte. Isso confere com a página "noncommercial tiers" do Earth Engine. O passo 0.4 mostra onde ver a cota.
- Na etapa 3, rodar o 03 de novo é seguro: ele pula os meses já prontos e os que estão na fila.

**Regra de ouro durante a transição.**
- **Até a etapa 5b:** você pode continuar rodando o motor V1.3 de sempre, sem mudar nada nele.
- **Depois da etapa 5b:** **nunca mais** rode o V1.3. Se ele rodar, refaz os dias de 2026 de volta para a V1.3, com a matriz antiga.

### Calendário sugerido

| Dia | Etapas |
|---|---|
| Dia 1 | 0, 1, 2 e 3 (a etapa 3 deixa tarefas rodando por horas) |
| Dia 2 | 4, 5a e 5b |
| Dia 3 | 5b de novo, 6, 7 e 8 |

---

## PARTE 2. Como fazer as operações básicas

Estas operações se repetem nas etapas. Volte aqui sempre que o roteiro mandar.

### 2.1 Abrir um arquivo do pacote e copiar o conteúdo

1. Abra a pasta `SAB_FINAL_v4_1` no Explorador de Arquivos.
2. Clique com o **botão direito** no arquivo, depois em **Abrir com** e em **Bloco de Notas**. Se o Bloco de Notas não aparecer, clique em **Escolher outro aplicativo** e escolha **Bloco de Notas**.
3. Dentro do Bloco de Notas, aperte **Ctrl+A** para selecionar tudo e **Ctrl+C** para copiar.

### 2.2 Rodar um arquivo `.py` no Colab

1. Abra o navegador em **https://colab.research.google.com**, já conectado na conta Google que usa o Earth Engine.
2. No menu do alto, clique em **Arquivo** e depois em **Novo notebook** (pode aparecer como **Novo notebook no Drive**).
3. Clique no nome `Untitled0.ipynb`, no canto superior esquerdo, apague, digite o nome indicado na etapa e aperte **Enter**.
4. Clique dentro da caixa cinza de código, a célula vazia.
5. Aperte **Ctrl+V** para colar o arquivo copiado no passo 2.1.
6. Aperte **Ctrl+Enter**, ou clique no botão redondo **▶** à esquerda da célula.
7. **Na primeira vez**, o Earth Engine pede autorização, de um destes dois jeitos:
   - abre uma janela "Permitir que este notebook acesse suas credenciais do Google?": clique em **Permitir**, escolha a sua conta e clique em **Continuar** ou **Permitir** até a janela fechar;
   - ou aparece um link no resultado: clique nele, escolha a conta, selecione o projeto **clima-492922**, clique em **Permitir**, copie o código que aparecer, volte ao Colab, cole o código na caixa que surgiu e aperte **Enter**.
8. Enquanto o código roda, o botão **▶** fica girando. **Não feche a aba.** A execução terminou quando o botão para de girar e aparece a mensagem final da etapa.
9. **Se aparecer "Reconectar" ou "Ambiente de execução desconectado"** no alto à direita: clique em **Reconectar** e repita o item 6. Os scripts retomam de onde pararam.

### 2.3 Salvar a saída do Colab num arquivo de texto

1. Abra o **Bloco de Notas** pelo menu Iniciar, com um arquivo novo e vazio.
2. No Colab, clique no **início** do texto de resultado, logo abaixo da célula.
3. Role até o **fim** do resultado, segure **Shift** e clique no final do texto.
4. Aperte **Ctrl+C**, vá ao Bloco de Notas e aperte **Ctrl+V**.
5. Clique em **Arquivo** e depois em **Salvar como**. Escolha a pasta `SAB_FINAL_v4_1`, use o nome indicado (por exemplo, `saida_etapa2.txt`) e clique em **Salvar**.

### 2.4 Baixar um arquivo gerado no Colab

1. Na barra lateral esquerda do Colab, clique no ícone de **pasta** (Arquivos).
2. Se o arquivo não aparecer, clique no ícone de **atualizar** (seta circular) no topo desse painel.
3. Clique com o **botão direito** no arquivo e depois em **Fazer download**.

### 2.5 Criar e rodar um script no Code Editor

1. Abra **https://code.earthengine.google.com**.
2. No canto superior direito, confira que o projeto ativo é **clima-492922**. Se não for, clique no ícone da sua conta e troque o projeto.
3. No painel esquerdo, clique na aba **Scripts**.
4. Clique no botão vermelho **NEW** e depois em **File**.
5. Na janela que abrir, digite o nome indicado na etapa e clique em **OK**.
6. O script novo abre vazio no editor central. Clique dentro dele e aperte **Ctrl+V**.
7. Aperte **Ctrl+S** para salvar.
8. Clique em **Run**, acima do editor.
9. Os resultados aparecem na aba **Console**, no painel direito. As tarefas aparecem na aba **Tasks**, ao lado dela.

### 2.6 Ver as tarefas no Code Editor

1. No painel direito, clique na aba **Tasks**.
2. As tarefas enviadas pelo Colab já aparecem rodando, com uma roda girando. Não é preciso clicar em nada.
3. Uma tarefa concluída aparece em **azul** (COMPLETED); uma tarefa com falha aparece em **vermelho** (FAILED).
4. Para ver o erro de uma tarefa vermelha, clique nela e copie a mensagem.
5. Se a lista não atualizar, clique no botão de **atualizar** da aba Tasks ou recarregue a página com **F5**.

### 2.7 Compartilhar um asset como leitura pública

1. No Code Editor, painel esquerdo, clique na aba **Assets**.
2. Clique no botão de **atualizar** (seta circular) no topo da aba.
3. Clique no **nome** do asset. Abre uma janela com os detalhes.
4. Clique em **SHARE**.
5. Marque a caixa **Anyone can read** e clique em **Done**.
6. Feche a janela de detalhes.

---

## PARTE 3. Execução

Diante de qualquer ⚠️, ❌ ou mensagem de erro em vermelho que este roteiro não diga que é esperada: **pare**, salve a saída (2.3) e me envie.

### Etapa 0. Preparação (20 min, nada é alterado)

**0.1 Arrumar os arquivos**
1. Crie a pasta `SAB_FINAL_v4_1` na área de trabalho.
2. Clique com o botão direito em `SAB_FINAL_v4_1_COMPLETO_2026-10-22.zip`, depois em **Extrair tudo**. Escolha a pasta `SAB_FINAL_v4_1` e clique em **Extrair**.
3. Crie a pasta `SAB_ANTIGOS_NAO_USAR`. Mova para ela todos os zips e arquivos anteriores, inclusive o `Código baselines.txt`, que **nunca** deve ser rodado. A lista completa, com o que fazer no Code Editor, no Colab e nos assets, está no `00_LEIA_PRIMEIRO_INVENTARIO.md`.

**0.2 Cópia de segurança do painel**
1. No Code Editor, na aba **Scripts**, clique no script atual do painel para abri-lo.
2. Clique dentro do editor e aperte **Ctrl+A** e depois **Ctrl+C**.
3. Clique em **NEW**, depois em **File**, digite `BACKUP_PAINEL_2026_10_2` e clique em **OK**.
4. Clique no editor vazio, aperte **Ctrl+V** e depois **Ctrl+S**.

**0.3 Cópia de segurança do motor**
1. No Colab, abra o notebook do motor V1.3 que você usa hoje.
2. Clique em **Arquivo** e depois em **Salvar uma cópia no Drive**.
3. Na cópia que abrir, clique no nome, troque por `BACKUP_MOTOR_V1.3` e aperte **Enter**.

**0.4 Ver o nível de cota do projeto**
1. Abra **https://console.cloud.google.com/earth-engine/configuration**.
2. No alto da página, confira que o projeto selecionado é **clima-492922**. Se não for, clique no seletor de projeto e escolha esse.
3. Anote o nível (tier): **Community** (150 EECU-horas por mês) ou **Contributor** (1.000 por mês).

**0.5 CSV de referência do histórico (com o painel atual)**
1. No Code Editor, abra o script original do painel e clique em **Run**. Espere o painel aparecer à esquerda do mapa.
2. Preencha:
   - **Modo de Operação do Sistema:** Dados Climáticos Locais;
   - **Resolução Desejada:** Diária;
   - **Nível de Análise:** Estados / Municípios;
   - **Passo 1:** Sul; **Passo 2:** Paraná, e clique em **+ Adicionar**;
   - marque **Deseja selecionar municípios específicos?**, escolha **Curitiba** e clique em **+ Adicionar**;
   - deixe **Filtrar os dados do passado por fenômeno** desmarcado (no painel antigo, "Filtrar médias passadas por fenômeno");
   - **datas:** início `01/11/2025`, fim `31/12/2025`;
   - deixe **Acoplar previsão** desmarcado.
3. Clique em **PROCESSAR DADOS CLIMÁTICOS**.
4. Em **Arquivos Prontos para Download**, clique no CSV diário para baixar.
5. Renomeie o arquivo baixado para `ANTES_Diaria_Curitiba_2025.csv` e guarde em `SAB_FINAL_v4_1`.

### Etapa 1. Máscara de qualidade (`01a` e `01b`, Colab, de 5 a 15 min cada)

**1.1 Simulação**
1. Rode o `01a_mascara_qualidade_SIMULACAO.py` no Colab (2.1 e 2.2), num notebook chamado `01_mascara`.
2. Confira no resultado:
   - `🔒` (trava de somente leitura) no início;
   - 5 linhas `AAAA-MM-DD: 0 pixel(s) com estrutura (A+B, C, D) diferente da referência; N pixel(s) B iguais ao BR-DWGD neste dia (coincidência)`. O primeiro número tem de ser 0 nas 5; o segundo pode ser maior que 0 nos dias de julho;
   - `✅ estrutura (A+B, C e D) idêntica pixel a pixel nos 5 dias`. Se houver coincidências, aparece também `ℹ️ N caso(s) de pixel B igual ao BR-DWGD ...`: é esperado (Parte A, nota 5);
   - 5 linhas `AAAA-MM-DD: dos N pixels da união B, X em B, Y em A, Z sem classe neste dia` (N perto de 300; Y é 0 ou poucos, as coincidências) e a linha `pixels da união B com classe nos 5 dias, por número de dias em B: {...}`, quase todos com 5 e alguns com 4. Se aparecer `ℹ️ ... sem classe em algum dos 5 dias` ou `ℹ️ ... pixel(s) B em só 1 ou 2 dos 5 dias`, siga até o fim, mas **me envie a saída antes de rodar o 01b**;
   - `✅ método aceito: ...` (o nome do método pode variar);
   - a linha `B pela receita da J1: só 2001-01-15 = ...; união dos 5 dias = ...`, com os dois números iguais ou o da união um pouco maior;
   - na tabela `Receita da J1 refeita agora x J1 de 20/10/2026`: A **70.364**, B **204** e C **1.109**, com `ok` = True nas três linhas;
   - a linha `máscara (sem ponderar, região ampla): ...` com as contagens da própria máscara, que contam o pixel inteiro: B perto de **300**, C dentro perto de **48** e C fora perto de **1.060** (valores aproximados; A fica um pouco acima de 70.364);
   - `✅ receita da J1 reproduzida dentro da tolerância; classe 3 = ... (K1d: 48); classe 4 = ... (referência ~1060)`;
   - se a classe 3 ou a 4 ficar longe dessas referências, aparece também `ℹ️ classe 3 = ...` ou `ℹ️ classe 4 = ...`. Não impede a gravação: a separação já foi validada pelo teste do centro do pixel;
   - no fim, `ℹ️ SIMULAR = True: nada foi gravado. Sem ⚠️: rode o 01b para gravar.`
3. Salve a saída como `saida_etapa1a.txt`. Se aparecer qualquer ⚠️ ou ❌, pare e me envie.

**1.2 Gravação**
1. **Reinicie a sessão do Colab antes de gravar:** no menu do alto, clique em **Ambiente de execução** e depois em **Reiniciar sessão** (confirme). O 01a deixa a trava de somente leitura ligada na sessão, e o 01b numa sessão sem reiniciar para com `❌ Esta sessão do Colab ainda tem a trava de somente leitura ...` (nada é gravado). Depois, no mesmo notebook, apague a célula (Ctrl+A e Delete), cole o `01b_mascara_qualidade_GRAVACAO.py` e rode.
2. Ele refaz as contas, exporta e espera a tarefa (de 5 a 15 min). Confira no fim: `✅ projects/clima-492922/assets/SAB_MASCARA_QUALIDADE gravado e conferido: ...`.
   - Se aparecer `❌ ... foi gravado antes da v4.1 ...`, é uma máscara de um pacote anterior: siga o que a mensagem diz (rodar o 01a; se houver pixels diferentes, apagar o asset na aba Assets e rodar o 01b de novo).
3. Salve a saída como `saida_etapa1b.txt`.
4. Se o painel for publicado como App, compartilhe `SAB_MASCARA_QUALIDADE` (2.7).

### Etapa 2. RONI oficial (`02_auditoria_roni_cpc.py`, Colab, cerca de 15 min)

1. **Não há nada a editar.** As estações novas que o CPC publicar (por exemplo, ASO 2026 em novembro) entram sozinhas.
   - O script só para num **empate**, quando o arquivo do CPC tem a 2ª casa decimal igual a 5. Nesse caso ele mostra a estação e manda abrir a tabela ERSST.v6 do site do CPC.
   - Para resolver: abra `02_auditoria_roni_cpc.py` no Bloco de Notas, aperte **Ctrl+F**, procure a linha do ano (por exemplo `2026 -0.9`), troque o `NaN` do trimestre indicado pelo valor do site, aperte **Ctrl+S** e rode de novo.
2. Rode o arquivo no Colab (2.1 e 2.2), num notebook chamado `02_roni`.
3. Confira no resultado:
   - `📐 Área Niño 3.4: 6,1..` (perto de 6,17 milhões) e `📐 Área trópicos 20S-20N: 174,..` (perto de 174 milhões);
   - `Fator de ajuste de variância (1991-2020): X`: **anote o X**;
   - `✅ N estações oficiais conferidas (última: ...)`. Hoje N = 920 e a última é JAS 2026 = +1.7. Depois de novembro, N cresce;
   - se houver estação nova: `Estações acrescentadas do arquivo do CPC: [...]`;
   - `✅ N estações gravadas em projects/clima-492922/assets/RONI_CPC_v6 (esperado N).`;
   - `✅ N estações conferidas no asset (...)`;
   - no fim, `📝 Tabela noaa_data ...`, com a linha do ano. Colar é opcional.
   - **⚠️ aceitável:** `⚠️ system:time_start não veio em nenhuma feição lida (A CONFIRMAR ...)`. É um ponto que só a execução real esclarece: o painel recalcula a data por ano e mês e a propriedade `data_ms` foi conferida. Anote e siga.
   - Se uma execução anterior tiver sido interrompida no meio da troca, pode aparecer `RONI_CPC_v6_ANTERIOR sem o asset principal ...: versão anterior devolvida ao lugar antes da troca.` O script se recupera sozinho.
4. **Compartilhamento:**
   - Na primeira gravação aparece `ℹ️ Não havia ACL anterior para reaplicar ...`. Se o painel for publicado como App, compartilhe `RONI_CPC_v6` (2.7) uma vez.
   - Nas rodadas seguintes, o script reaplica o compartilhamento sozinho. Só compartilhe de novo se aparecer ⚠️ sobre compartilhamento.
5. Salve a saída como `saida_etapa2.txt`.

### Etapa 3. Matriz GFS V2.1 (`03_matriz_gfs_v2_1.py`, Colab; de 15 a 45 min para enviar, horas para concluir)

1. Rode o arquivo no Colab (2.1 e 2.2), num notebook chamado `03_matriz_gfs`.
2. Ele usa só o GFS v16: rodadas 00Z de 23/03/2021 a 31/12/2025, com todos os dias de cada faixa (Parte A). Para cada mês aparecem 3 linhas:
   `   Mês 01: dias válidos por faixa {'L1': ..., 'L2a5': ..., 'L6a10': ..., 'L11a15': ...}`
   `      (pares dia x prazo; máximo possível {...}; L1 99.2%, ...)`
   `✔️ Tarefa enviada: matriz GFS V2, mês 01.`
3. Os números são **pares dia × prazo**. Cada valor deve ficar **igual ou um pouco abaixo** do máximo da tabela, sem ⚠️. O esperado é de 98% a 100%.

| Mês | L1 | L2a5 | L6a10 | L11a15 |
|---|---|---|---|---|
| Janeiro | 124 | 496 | 620 | 620 |
| Fevereiro | 113 | 452 | 565 | 565 |
| Março | 133 | 522 | 630 | 620 |
| Abril | 150 | 600 | 750 | 735 |
| Maio, julho, agosto, outubro, dezembro | 155 | 620 | 775 | 775 |
| Junho, setembro, novembro | 150 | 600 | 750 | 750 |

   - Um ⚠️ (abaixo de 85% do máximo) ou um valor **acima** do máximo: **pare e me envie a saída**.
   - Se a contagem demorar e aparecer `⚠️ Contagem de pares válidos do mês MM não calculada no Colab (...)`, tudo bem: a tarefa é enviada mesmo assim e a contagem fica gravada no asset (o 04 mostra).
4. Quando aparecer `🎉 Tarefas enviadas: 12 (...)`, salve a saída como `saida_etapa3.txt`. A aba do Colab pode ser fechada.
5. No Code Editor, acompanhe a aba **Tasks** (2.6). Espere as 12 tarefas `GERAR_MATRIZ_GFS_V2_01` a `_12` ficarem azuis.
6. **Rodar o 03 de novo é seguro:** ele pula com `⏩` os meses já prontos e com `⏳` os que estão na fila. Se uma tarefa ficar vermelha, copie a mensagem de erro, me envie e espere a correção antes de rodar de novo.

### Etapa 4. Conferência da matriz (`04_conferencia_matriz_gfs.js`, Code Editor, de 1 a 3 min)

1. Crie e rode o script `04_conferencia_matriz_gfs` (2.1 e 2.5).
2. Na aba **Console** aparecem 5 blocos, cada um com ✅, ⚠️ ou ❌:
   1. estrutura: 12 matrizes, 100 bandas, versão V2.1;
   2. cobertura e pares por pixel;
   3. viés e fatores por mês e faixa;
   4. detalhe espacial;
   5. radiação contra a V1.
   No fim vem a linha `RESUMO: n ✅ | n ⚠️ | n ❌`.
3. **Qualquer ❌: pare e me envie.** ⚠️ nos fatores dos meses secos (junho a setembro) é possível: me envie o Console para avaliar.
4. **No mapa:**
   - passe o mouse sobre o botão **Layers**, no canto superior direito;
   - desmarque e marque a camada **Tmax GFS faixa L1** algumas vezes, comparando com **Tmax BR-DWGD**;
   - o GFS deve mostrar o desenho da Serra do Mar e da Mantiqueira, mais suave que o BR-DWGD. Se aparecerem manchas lisas e grandes, aperte **PrtSc** e me envie a imagem.
5. Copie o Console inteiro para um arquivo `saida_etapa4.txt` (clique no Console, Ctrl+A e Ctrl+C).

### Etapa 5a. Motor V1.5 em simulação (`05a_motor_sab_v1_5_SIMULACAO.py`, Colab, de 15 a 50 min)

1. Rode o arquivo no Colab (2.1 e 2.2), num notebook chamado `05_motor_v15`.
2. Se aparecer `❌ A matriz ... não tem os meses ...` ou `❌ A matriz ... não é a V2.1 ...`, a etapa 3 ainda não terminou: espere as 12 tarefas azuis e rode de novo.
3. Confira, de cima para baixo:
   - `🛡️ TRAVA DO HISTÓRICO LIGADA: nenhum dia até 2025-12-31 será alterado.` e `🧪 MODO SIMULAÇÃO ATIVO`;
   - `✅ Matriz GFS V2.1: 12 meses com as 48 bandas de média e as 32 de desvio da Tmax, da Tmin, da UR e da radiação (modelo GFS v16, rodadas desde 2021-03-23, ...)` e, logo abaixo, as linhas `Correção da Tmax/Tmin nos dias GFS: variancia ...` e `Correção da UR e da radiação nos dias GFS: variancia ...`, e a linha `Teto da razão dos desvios da Tmax/Tmin: 2.0 nos prazos 1 a 5 e 1.0 do 6 em diante ...` (K11);
   - `🛰️ Rodadas 00Z na janela (...)`, com pelo menos 1 completa, e `🛰️ Rodada GFS de referência: AAAA-MM-DD 00Z` (sempre 00Z);
   - no bloco `RESUMO DA SIMULAÇÃO`: uma linha `recalcular provisoria_era5 V1.3 -> provisoria_era5 V1.5: ...`, linhas com `GFS` e **nenhuma** linha com `definitiva` ou `patch`;
   - na `PRÉVIA 3`: as 14 bandas do grupo `deve ficar igual` com `% pixels alterados` igual ou perto de 0;
   - na `PRÉVIA 2`, linha `Brasil`: `ΔUmid 0-5 %` e `ΔUmid 0-100 %` entre -2 e 2 (a auditoria mediu cerca de 0,4);
   - na `PRÉVIA 5`: `✅ Todos os critérios atendidos.` Ela inclui os critérios da rota GFS;
   - na `PRÉVIA 6` (rota GFS em memória): a tabela com o último dia ERA5, o 1º dia GFS e mais até 3 dias (prazos 2, 8 e 11), incluindo as linhas `Tmax pelo outro método (aditivo)`; as linhas ✅; a linha `ℹ️ ... GFS bruto ... -> calibrado ...`; para cada dia, `ℹ️ ... Tmax máxima nacional variancia X °C x aditivo Y °C`; a linha `ℹ️ razão dos desvios da Tmax ...`; e, por último, a linha da decisão da Tmax (`✅ Tmax: ...` ou `➜ DECISÃO ...`);
   - no fim, `🛡️ PROTEGIDOS: nenhum dia histórico precisaria de ação.`
   - pode aparecer `⚠️ ERA5-Land sem N dia(s) antes do último publicado ...` (correção 21/10, 18h). Não é erro e você não precisa fazer nada: o Earth Engine publicou um dia do ERA5 antes dos anteriores. O motor usa o ERA5 até o último dia sem lacuna e a previsão GFS depois dele. Quando a lacuna for preenchida, a execução seguinte refaz esses dias como ERA5.
4. **Conferência da Tmax.** O método já está decidido (`variancia`, K8). Leia a última linha da PRÉVIA 6 **sem editar nenhum arquivo**:
   - `✅ Tmax: o método em uso (variancia) passa ...`: siga.
   - `⚠️ Tmax: nesta execução 'aditivo' passou ... e 'variancia' não. NÃO troque o método ...`: pare e me envie. Poucos dias de previsão não bastam para desfazer a validação da K8 em 2025 inteiro.
   - `➜ DECISÃO ...: nenhum dos dois métodos ...`: pare e me envie. É a cauda quente do próprio GFS (Parte A, nota 6); a linha `GFS bruto -> calibrado` mostra o tamanho do problema.
   - `⚠️ Tmax: a emenda ERA5 -> GFS não foi testada ...`: o 1º dia GFS não foi calculado nesta execução. Rode o 05a de novo mais tarde.
   - Nos outros casos em que a PRÉVIA 5 disser "NÃO EXECUTE AINDA", pare e me envie.
5. Salve a saída como `saida_etapa5a.txt` e baixe o arquivo `previa_v15.csv` (2.4).
6. **Se tudo conferir, siga para a 5b. Se não, pare e me envie os dois arquivos.**

### Etapa 5b. Motor V1.5 gravando (`05b_motor_sab_v1_5_GRAVACAO.py`, Colab, horas)

1. No mesmo notebook `05_motor_v15`, clique dentro da célula e aperte **Ctrl+A** e depois **Delete**.
2. Copie o `05b_motor_sab_v1_5_GRAVACAO.py` (2.1), cole na célula e aperte **Ctrl+Enter**.
3. No início deve aparecer `🛡️ TRAVA DO HISTÓRICO LIGADA`, e **não** pode aparecer `MODO SIMULAÇÃO`. Confira também as linhas `Correção da Tmax/Tmin nos dias GFS: variancia ...`, `Correção da UR e da radiação nos dias GFS: variancia ...` e `Teto da razão dos desvios da Tmax/Tmin: 2.0 nos prazos 1 a 5 e 1.0 do 6 em diante ...`. Se aparecer `aditivo` ou `original`, ou se faltar alguma dessas linhas, você colou um arquivo antigo: pare e cole o 05b deste pacote.
4. Deixe a aba aberta. A parte da previsão grava um dia por vez e espera cada tarefa terminar. Cada dia GFS mostra `✔️ AAAA-MM-DD: exportado (rodada ... 00Z, prazo Ln, faixa ..., confiança ..., ...)`.
5. Terminou quando aparecer `✅ Execução encerrada. Vagas restantes na fila: ...`. Logo antes deve aparecer `🛡️ PROTEGIDOS: nenhum dia histórico precisaria de ação.`
6. Se o Colab desconectar antes do fim, clique em **Reconectar** e rode a célula de novo.
7. Salve a saída como `saida_etapa5b.txt`.
8. **No dia seguinte,** abra o mesmo notebook e rode a célula de novo, sem mudar nada.
9. A partir daqui, **este notebook é o seu motor de uso diário.** O `BACKUP_MOTOR_V1.3` não deve mais ser rodado.

### Etapa 6. Painel 2026.10.4 (`06_painel_sab_2026_10_4.js`, Code Editor)

**6.1 Trocar o código**
1. No Code Editor, abra o script **original** do painel (não o `BACKUP_...`).
2. Clique dentro do editor e aperte **Ctrl+A** e depois **Delete**.
3. Copie o `06_painel_sab_2026_10_4.js` (2.1), clique no editor vazio e aperte **Ctrl+V**.
4. Aperte **Ctrl+S** e clique em **Run**.
5. No **Console**, logo ao abrir, deve aparecer `Máscara de qualidade encontrada: ...`. Se aparecer o aviso "Máscara de qualidade ausente ou sem permissão de leitura", a etapa 1b não terminou ou, no App publicado, o asset ainda não foi compartilhado (2.7).

**6.2 Teste do histórico**
1. Repita exatamente o preenchimento do passo 0.5.
2. Baixe o CSV diário e renomeie para `DEPOIS_Diaria_Curitiba_2025.csv`.
3. O arquivo novo tem 3 colunas a mais, **no fim**: `Qualidade_Pixel`, `Janela_Chuva_UTC` e `Confianca_Prazo`. As 30 colunas antigas ficam nas mesmas posições (no CSV mensal, as novas `N_Dias`, `Dias_no_Mes` e `Mes_Completo` também vão para o fim).
4. Compare os dois arquivos coluna a coluna. Todas as colunas antigas devem ter os mesmos valores. A única diferença possível é nas duas colunas de umidade do solo, se o painel antigo as gravava com 2 casas decimais (o novo usa 3); arredondadas para 2 casas, devem ser iguais.
5. Nas colunas novas, o esperado é:
   - `Janela_Chuva_UTC` = `12-12 UTC (D-1 a D)` em todas as linhas;
   - `Confianca_Prazo` vazia;
   - `Qualidade_Pixel` = `A` em todos os pontos de Curitiba.
6. Se preferir, me envie os dois arquivos e eu comparo.

**6.3 Teste dos dias novos**
1. Mantenha Curitiba, troque o fim do período para **hoje** e o início para 30 dias antes, e marque **Acoplar previsão para os próximos 15 dias**.
2. Clique em **PROCESSAR DADOS CLIMÁTICOS** e baixe o CSV diário de 2026.
3. Confira as colunas:
   - `Tipo_Dado`: `Provisorio_ERA5` e `Previsao_GFS`. Com a rodada 00Z, o último dia normalmente sai completo; `Previsao_GFS_Parcial` só aparece se a rodada do dia ainda estiver chegando, e então chuva, radiação e ETo desse dia ficam vazias;
   - `Versao_Algoritmo`: `V1.5`;
   - `Janela_Chuva_UTC`: `00-24 UTC`;
   - `Confianca_Prazo` nos dias de previsão: `alta` nos 5 primeiros, `media` do 6º ao 10º e `baixa` do 11º em diante.

**6.4 Teste do ENSO**
1. No bloco de ENSO do painel, clique em **📊 Simular Cenário Futuro**.
2. No **Console**, nesta ordem:
   - `RONI: fator de variância do OISST (1991-2020)`, com um número perto do X anotado na etapa 2;
   - `RONI: série mensal contínua? true`;
   - `RONI: estações com fase Indefinida no fim da série: 4` (maio a agosto de 2026).
3. No painel deve aparecer (texto para leigos de 22/10; os números são os mesmos de antes):
   - `🌊 COMO ESTÁ O OCEANO AGORA (julho a setembro de 2026)`, com `O Pacífico equatorial está 1,7 °C acima do normal, já descontado o aquecimento geral dos oceanos tropicais (índice RONI +1,7 °C).`, a frase sobre a tabela histórica do CPC (`... e até agora são 4. Isso não impede o CPC de já declarar condições de El Niño nos boletins mensais ...`) e `Em 5 meses o oceano esquentou 2,1 °C: em fevereiro a abril de 2026 estava 0,4 °C abaixo do normal.`;
   - em verde: `No último mês subiu mais 0,3 °C, sem mudança brusca.`;
   - `🔮 O QUE ESPERAR PARA OUTUBRO A DEZEMBRO DE 2026`, com a explicação do que foi comparado (o oceano de outubro a dezembro dos anos parecidos, não os efeitos no clima, que ficam no item B) e `Anos parecidos: 1951, 1957, 1963, 1965, 1972, 1982, 1987, 1997, 2015 e 2023 (o mais parecido foi 1997).`;
   - `🔥 El Niño em 10 dos 10 anos (100%)`, com: muito forte, 5 anos (1965, 1972, 1982, 1997 e 2015); forte, 1 ano (1957); moderado, 3 anos (1963, 1987 e 2023); fraco, 1 ano (1951);
   - `⚪ Neutro em nenhum dos 10 anos (0%)` e `❄️ La Niña em nenhum dos 10 anos (0%)`;
   - embaixo, `ℹ️ Como ler`, com: não é a previsão oficial; `... a chance de El Niño fica entre 69% e 100%: muito provável, mas não garantido.`; `"muito forte" apareceu em 5 dos 10 anos (50%), mas pela mesma conta pode ficar entre 19% e 81%.`; o limite do método (`... foi no máximo +2,3 °C ...`) e o aviso `Atenção: o aquecimento de agora (+2,1 °C em 5 meses) é maior que o de todos os anos parecidos ...`; o limite da margem (não inclui o erro do método); o que é o RONI; e as siglas (`JAS = julho a setembro de 2026; OND = outubro a dezembro de 2026`).
4. Clique em **📥 Gerar link da previsão (CSV)**. Logo abaixo do botão aparecem dois links (sem passar pela aba Tasks):
   - `⬇️ Baixar Previsao_ENSO_OND_2026_Resumo.csv`: uma linha com as probabilidades, as intensidades (50/10/30/10) e os intervalos de 95%;
   - `⬇️ Baixar Previsao_ENSO_OND_2026_Anos_Analogos.csv`: um ano por linha, de 1951 a 2023, com o RONI de JAS, a trajetória, a ordem de semelhança e o RONI, a fase e a intensidade em OND.
5. Esses valores valem até o OISST fechar outubro (cerca de 05/11) ou até o 02 gravar a estação ASO. Depois disso, eles mudam, e é o esperado.

**6.5 Teste do filtro histórico**
1. No item **B. Como foi o clima em meses de El Niño, La Niña ou neutro**, marque **Filtrar os dados do passado por fenômeno** e escolha **El Niño forte (+1,5 a +1,9 °C)**. A lista usa os mesmos nomes e faixas do item A, com vírgula decimal.
2. Use Curitiba, resolução Diária, datas de `01/01/1972` a `31/12/1973`, e clique em **PROCESSAR DADOS CLIMÁTICOS**.
3. Os CSV aparecem como `Diaria_Curitiba_1972_El_Nino_Forte.csv` e `Diaria_Curitiba_1973_El_Nino_Forte.csv` e devem ter dias só de setembro, outubro e dezembro de 1972 e de janeiro de 1973. No fim de cada linha vêm 5 colunas novas: `Filtro_ENSO` = El Nino forte, `Fase_ENSO` = El Nino, `Intensidade_ENSO` = Forte, `RONI_Trimestre_C` (por exemplo, 1,8) e `Trimestre_CPC` (por exemplo, ASO). Os dias de previsão continuam todos (inclusive os de datas já passadas, ainda sem ERA5), com `Fase_ENSO` = Previsao (sem classificacao), `-` na intensidade e no RONI e o trimestre do CPC pela data. Sem o filtro, os CSV ficam como antes, sem essas colunas. Na lista de meses, o RONI sai com uma casa decimal (2.0). Opcional: o botão **📋 Só a lista de meses do fenômeno (sem dados de clima)** gera logo abaixo `⬇️ Baixar Meses_do_filtro_El_Nino_Forte_N_meses.csv`. É um mês por linha (ano, mês, trimestre do CPC com os meses por extenso, RONI, fase e intensidade), e devem aparecer set, out e dez/1972 e jan/1973 entre eles. Essa lista não tem chuva nem temperatura: os efeitos no clima estão nos CSV dos dados do passo 3, os mesmos meses. No Console: `Filtro ENSO (...): 0 mês(es) com fase Indefinida e 0 Sem_Dado ficaram fora do filtro.`
4. Se aparecer "Computation timed out", anote e me envie.

**6.6 Teste dos nomes de estados (GAUL)**
1. Desmarque o filtro de fenômeno. Escolha **Passo 1:** Norte; **Passo 2:** Amazonas, e clique em **+ Adicionar**. Marque **Deseja selecionar municípios específicos?** e abra a lista: só municípios do Amazonas (sem "Leticia", que é da Colômbia).
2. Repita com **Pará** (sem distritos do Suriname) e com **Centro-Oeste > Distrito Federal** (o mapa deve ir para Brasília, não para o México).

**6.7 Teste da área grande demais**
1. Escolha **Norte** e adicione os 7 estados, sem municípios específicos, resolução Diária e um período de 1 mês.
2. Clique em **PROCESSAR DADOS CLIMÁTICOS**. Deve aparecer o aviso `⚠️ ÁREA GRANDE DEMAIS: a seleção gera N pares pixel × polígono, acima do limite de 25000 ...` e nada é processado. Antes, a lista era cortada em silêncio.

**6.8 App publicado (só se existir)**
1. No alto do Code Editor, clique no botão **Apps**.
2. Na lista, clique no seu App.
3. Confirme que a fonte é o script do painel e clique em **Update** (ou **Publish**).
4. Confira se `SAB_MASCARA_QUALIDADE` (etapa 1) e `RONI_CPC_v6` (etapa 2) estão compartilhados como "Anyone can read" (2.7).

### Etapa 7. Conferência das normais já gravadas (`07a` e `07b`, Colab, de 30 a 90 min cada)

1. Rode o `07a_normais_CONFERIR_1991_2020.py` no Colab (2.1 e 2.2), num notebook chamado `07_normais`. Confira:
   - `🔒 MODO_CONFERENCIA: escrita no Earth Engine bloqueada (só leitura).`;
   - `📋 INVENTÁRIO 1961-1990: 10957 imagens | esperadas 10957 | faltando 0 | datas duplicadas 0`;
   - `📋 INVENTÁRIO 1991-2020: 10958 imagens | esperadas 10958 | faltando 0 | datas duplicadas 0`;
   - `📦 PLANO: 48 imagens | enviar 0 | já existem 48 | na fila 0`;
   - em `=== CRITÉRIOS ===`, todos com ✅. Agora são 3 meses (01, 02 e 08) e há critérios novos: `assets gravados = local`, `P95/P99 gravados na faixa`, `limiares gravados na faixa`, `limiares gravados = recálculo EE` e `coerência física dos gravados`;
   - os relatórios informativos `📊 [M07-03] REGRA DE LEITURA DO SPI ...` (pixels que a regra dos 20 anos com chuva cortaria) e `ℹ️ [Q1] ...` (normais por classe da máscara de qualidade). São só informação;
   - no fim, `✅ Tudo conferido: as imagens gravadas batem com o cálculo independente. Não há nada a exportar; mantenha SIMULAR = True.`
2. Salve a saída como `saida_etapa7a.txt`.
3. No mesmo notebook, apague a célula (Ctrl+A e Delete), cole o `07b_normais_CONFERIR_1961_1990.py` e rode. O esperado é o mesmo. Salve como `saida_etapa7b.txt`.
4. Compartilhe as 4 coleções da pasta **Baselines** (2.7). Clique na seta ao lado de **Baselines** para abrir a pasta e repita o 2.7 em cada uma:
   - `Limiares_Historico_1961_1990`;
   - `Limiares_Operacional_1991_2020`;
   - `Normais_Historico_1961_1990`;
   - `Normais_Operacional_1991_2020`.

Qualquer ❌ nas etapas 7a ou 7b: **pare e me envie**. Isso indicaria que as imagens gravadas diferem do método B1.1.

### Etapa 8. Auditoria final (`08_auditoria_completa_SAB.py`, Colab, de 12 a 20 min)

1. Rode o arquivo no Colab (2.1 e 2.2), num notebook chamado `08_auditoria`.
2. No fim, o Colab baixa um arquivo `auditoria_SAB_<data>_<hora>.zip`. Se não baixar, use o 2.4 na pasta `/content`.
3. O esperado depois das etapas 1 a 7:

| Item | Esperado |
|---|---|
| C1 a C6, D1 a D11 (histórico) | ✅, ou ℹ️ com o motivo |
| D10 | ✅; ou ℹ️ se só os dias de previsão GFS V1.5 tiverem pixels a menos que o `SAB_2025_12_31` (cobertura contida na canônica: a linha mostra quantos faltam e "0 fora da canônica") |
| C7, E4, H2, H4 e I1 | ℹ️ (já registrados na tese ou substituídos; o motivo aparece na linha) |
| F2, F3 e F5 | ✅ (F5 mostra como ℹ️ as datas reais das mudanças do GFS); F4 ℹ️ (radiação do GFS em blocos de 6 h, já tratada no 03 e no 05) |
| B2 e E5 | `RONI_CPC_v6`, `SICSB_MATRIZ_GFS_V2` e `SAB_MASCARA_QUALIDADE` existem |
| D7 e D14 | Dias de 2026 em `V1.5`: rodadas 00Z, `Confianca_Prazo`, `metodo_temp_gfs = 'variancia'` e `metodo_ur_rs_gfs = 'variancia'` nos dias GFS (um dia GFS gravado com outro método aparece em `propriedades_contrato_V1.5`); critério `teto_razao_K11`: 2.0 nos prazos 1 a 5 e 1.0 do 6 em diante |
| E6 | Matriz V2.1 com 100 bandas e as propriedades certas |
| H5 | `RONI_CPC_v6` igual ao arquivo do CPC. ⚠️ aceitável só se o único problema for `system:time_start não veio em nenhuma estação` (o mesmo ponto A CONFIRMAR da etapa 2) |
| Q1 | ✅ Máscara com as contagens da etapa 1 e a grade nativa. A linha do log mostra à parte os pixels B iguais ao BR-DWGD no dia conferido (coincidência, ignorados); mais de 20 deles vira ⚠️ (me envie) |
| J1 | ℹ️ (C 1.109 e A + B 70.568 constantes; B de 194 a 205, porque num dia de inverno alguns pixels B coincidem com o BR-DWGD: é o histórico, tratado na leitura) |
| J3 | ℹ️ (o painel 2026.10.4 já filtra o país) |
| J5 | Tmax dos dias V1.5 sem passar de 44,8 °C e sem salto acima de 2 °C na emenda. Se aparecer ⚠️ aqui, me envie: é o teste da cauda quente. Na primeira vez, J5c sai ℹ️ `sem CSV anterior (não achei /content/J5_previsao_anterior.csv)`: é o esperado até a verificação de 15/11 (Parte 4). |

4. Me envie o zip.
5. **Se a J5a der ⚠️** (algum dia de previsão acima de 44,8 °C), rode no Colab, numa célula nova, o `validacoes/K10_diagnostico_tmax_recorde.py`. Ele só lê e não trava a sessão. Me envie a saída e o `K10_diagnostico_tmax.csv`: o diagnóstico diz se o excesso vem do próprio GFS, da calibração ou de um pixel de borda.

### Etapa 8b. Validação K11 (`validacoes/K11_validacao_razao_desvios_prazos_longos.py`, Colab, de 10 a 30 min)

Por que existe: a auditoria de 22/10 achou a previsão de 26/10 em Casa Nova-BA com Tmax de 45,24 °C. O GFS bruto dava 35,41 °C, e a escala de variância multiplicou a anomalia por 1,98 (K10). A K11 testa, com os dados da K9A, se limitar essa razão a 1 nos prazos de 6 dias em diante resolve o problema sem piorar a previsão.

1. Numa célula nova do Colab, cole o arquivo inteiro e rode. Ele só lê e não trava a sessão.
   - Na 1ª vez, autorize o acesso ao Drive: ele usa os dados da K9A guardados em `cache_validacao_K9A`.
   - Se não achar esses dados, baixa de novo só o GFS v16 (de 1 a 2 horas).
2. No fim, o Colab baixa o `validacao_K11_<data>_<hora>.zip`. Me envie o zip.
3. Leia a seção `RESULTADO FINAL K11`, separada para a Tmax e a Tmin:
   - `➜ TROCAR` com o M1 ou o M2: eu altero o 05a e o 05b. É uma constante, e a regra já estava fixada antes de rodar.
   - `➜ MANTER`: nada muda no motor.
4. Não mude nada no motor antes do resultado.
5. **Resultado de 22/10/2026:** `➜ TROCAR` com o M1 na Tmax e na Tmin. O 05a e o 05b deste pacote já têm `RAZAO_DESVIO_MAX_LONGO = 1.0`. Rode o 05a (simulação) e depois o 05b. Os dias de previsão com 6 ou mais dias de antecedência são refeitos (aparecem como `refazer provisoria_gfs -> GFS` no resumo do 05a). Depois rode o 08: o critério novo `teto_razao_K11` da D14 tem de passar, e a J5a não deve acusar 45 °C.
6. **Conferido em 22/10/2026:** o 05a (8h39) e o 05b (8h42) rodaram com a linha do teto; o 05b gravou 16 dias com a rodada de 22/10 00Z. A auditoria 08 das 8h59 deu 45 ✅, 23 ℹ️, 3 ⚠️ (A2, E3-rsub e E3-rsup, já explicadas) e nenhum ❌: `teto_razao_K11` ✅ nos 29 dias GFS e J5a ✅, com a maior Tmax em 44,08 °C (26/10, prazo 5), abaixo do recorde (antes, 45,24 °C).

---

## PARTE 4. Rotinas depois da implantação

| Quando | O que fazer |
|---|---|
| Todo mês, depois do dia 5 | Etapa 2 inteira, sem editar nada, a não ser que ela pare por empate |
| Com a frequência de sempre, **depois das 10h** | Rodar o notebook `05_motor_v15` (o 05b), sem mudar nada. A rodada 00Z do GFS costuma ficar completa por volta das 03h, mas já atrasou até 09h18 (K4). Se rodar antes, o motor usa a 00Z completa anterior, sem erro: só fica um dia mais velho. |
| Por volta de 15/11/2026 | **Verificação da previsão:** quando o ERA5 já cobrir os dias de outubro que eram previsão, suba no Colab (painel Arquivos, botão de upload) o `J5_tmax_2026.csv` da auditoria de 22/10/2026, 8h59 (`auditoria_SAB_20261022_085950.zip`; previsão da rodada de 22/10, dias até 06/11), com o nome `J5_previsao_anterior.csv` e rode a etapa 8. O item J5 compara, nas mesmas datas, a previsão GFS com o ERA5. É a checagem real da cauda quente. |
| Quando a NOAA implantar o GFS v17 | Proposto para outubro de 2026; até 20/10 não achei o aviso de implantação. Rode a etapa 8 e me envie: a matriz V2.1 foi treinada no v16 e terá de ser reavaliada. Depois de alguns meses de v17, a validação `validacoes/K9A_validacao_ampliada.py` deve ser refeita só no período do v17 (o ganho da radiação dependeu da versão do modelo; Parte A, nota 11). |
| Antes e depois de qualquer mudança grande | Etapa 8 (auditoria) |
| Quando o BR-DWGD cobrir 2026 | Nada muda sozinho: o motor avisa `⏸️ BR-DWGD já cobre até ... dias aguardam decisão`. Me peça a V3: janela de chuva 12–12 UTC no ERA5 e no GFS (Parte A, nota 10), pixels B lidos do BR-DWGD, mapeamento de distribuição na Tmax e a decisão sobre converter os dias em definitivos. |

## PARTE 5. Como desfazer, se for preciso

- **Painel:** abra o script original, apague tudo, cole o conteúdo do `BACKUP_PAINEL_2026_10_2` e salve.
- **Dias de 2026:** abra o `BACKUP_MOTOR_V1.3` e rode-o. Ele refaz os dias de 2026 como V1.3, usando a matriz antiga, que continua existindo.
- **Assets novos:** na aba **Assets**, clique no asset e depois em **Delete**. Isso vale para `SAB_MASCARA_QUALIDADE`, `RONI_CPC_v6` e `SICSB_MATRIZ_GFS_V2`.
- **Sobra `RONI_CPC_v6_ANTERIOR`:** não apague à mão. Na execução seguinte do 02, ele é apagado depois da conferência ou, se o `RONI_CPC_v6` estiver faltando, volta para o lugar.

## PARTE 6. Lista de conferência

- [ ] 0: pastas arrumadas; backup do painel e do motor; tier anotado; `ANTES_Diaria_Curitiba_2025.csv`
- [ ] 1: 01a sem ⚠️ (estrutura igual nos 5 dias; receita da J1: A 70.364, B 204, C 1.109); 01b "gravado e conferido"
- [ ] 2: N estações conferidas e gravadas; fator X anotado; compartilhado (se houver App)
- [ ] 3: pares por faixa iguais ou um pouco abaixo da tabela; 12 tarefas azuis
- [ ] 4: RESUMO sem ❌; relevo no mapa
- [ ] 5a: trava; matriz V2.1; referência 00Z; nada "definitiva" ou "patch"; ΔUmid dentro de ±2; PRÉVIA 5 ✅ (com a PRÉVIA 6); `Correção da Tmax/Tmin nos dias GFS: variancia`, `Correção da UR e da radiação nos dias GFS: variancia` e a linha do teto da razão (K11); última linha da PRÉVIA 6 com ✅; nenhum protegido
- [ ] 5b: `variancia` nas linhas da correção da Tmax/Tmin e da UR e radiação; "Execução encerrada"; rodado de novo no dia seguinte; V1.3 aposentado
- [ ] 6: CSV histórico igual pelas colunas antigas; V1.5 e Confianca_Prazo em 2026; ENSO com IC e "true"; filtro de 1972-73 como esperado; Amazonas, Pará e DF só do Brasil; aviso de área grande; App atualizado
- [ ] 7: "Tudo conferido" no 07a e no 07b; 4 coleções compartilhadas
- [ ] 8: zip da auditoria final enviado
- [ ] Por volta de 15/11: etapa 8 com o `J5_previsao_anterior.csv`
