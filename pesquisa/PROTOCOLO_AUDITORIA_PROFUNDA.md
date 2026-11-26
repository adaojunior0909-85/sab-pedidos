# Protocolo da auditoria profunda (fase 3): o banco inteiro, de 1961 à previsão de 15 dias

**Pedido do responsável (26/11/2026, ~12h–12h30):** decidir, para todo o banco e para o máximo de variáveis, se o salto
que aparece a partir de 2020 é do clima (por exemplo El Niño ou La Niña que as outras bases não teriam captado) ou dos
dados (o BR-DWGD v_3.2.4); usar o NASA POWER também como testemunha; "escreva o protocolo, atualize e vamos auditar isso
tudo de forma minuciosa".

Este protocolo é **congelado num commit ANTES de qualquer resultado** de seus testes. Uma emenda só antes de rodar o
teste afetado, datada. Depois de rodar, nada muda.

## 0. Regras gerais (valem para tudo)
1. **Só leitura** no Earth Engine e nas APIs. **Nada é gravado** no banco sem autorização explícita do responsável. O
   histórico 1961–2025 nunca é regravado no asset; uma correção aprovada entra na leitura (painel e `sab_pedido.py`
   juntos) com K16 nova.
2. **As outras bases são testemunhas, não alvo.** Elas só mostram ONDE e QUANDO o banco mudou de comportamento. Nenhuma
   correção copia o nível de outra base. Se houver correção, ela usa o próprio BR-DWGD (anos estáveis) ou a relação
   que se manteve estável por décadas (regra do M5 da fase 2).
3. **A régua é 1961–2019** (2001–2015 como base das razões, igual ao `validar_multifonte.py`), porque nela as bases
   concordaram com o banco a ±3% inclusive nos grandes El Niños e La Niñas.
4. Tudo o que cada teste medir é registrado em `pesquisa/resultados_auditoria/` (CSV com todos os números + um
   `RESULTADOS_<teste>.md`), passando ou não na regra.

## 1. Trechos do banco e o que cada um recebe
| Trecho | Origem do dado | Testes |
|---|---|---|
| 1961–1980 | BR-DWGD | A1, A2 (só famílias com dado), A6 |
| 1981–2019 | BR-DWGD | A1, A2 (régua e calibração do teste do ENSO), A3 (GRACE desde 2002, SMAP desde 2015), A5 |
| **2020–2025** | BR-DWGD (trecho suspeito) | **todos (A1 a A6)** |
| 2026 até ontem | ERA5-Land calibrado (V1.7; V1.8 suspensa) | A1 (2026), A3 (SMAP), A7 |
| Previsão 1–15 dias | GFS calibrado | A7 e o M6 da fase 2 (inalterado) |

Variáveis: as do BR-DWGD (chuva, Tmax, Tmin, radiação, umidade relativa, vento, ETo) e a VPD derivada. As variáveis do
modelo (solo, folha, ET real, transpiração, escoamento) seguem o M4 da fase 2 (aviso, sem correção) e entram só no
relato do A1.

## 2. Famílias de testemunhas (independência)
Duas bases da mesma família contam como **uma** testemunha.
| Família | Bases | Variáveis |
|---|---|---|
| F1 – pluviômetros do GPCC | IMERG Final, PERSIANN-CDR (via GPCP), GLDAS-2.1 (chuva do GPCP) | chuva |
| F2 – estações do CRU | TerraClimate | chuva, Tmax, Tmin, VPD, radiação, vento, ETo |
| F3 – estações próprias do CHIRPS | CHIRPS | chuva |
| F4 – MERRA-2 (NASA POWER) | NASA POWER: PRECTOTCORR (chuva do MERRA-2 corrigida por pluviômetros, Reichle et al. 2017), T2M_MAX, T2M_MIN, RH2M, WS2M; radiação ALLSKY_SFC_SW_DWN (GEWEX SRB 1984–2000, CERES SYN1deg 2001–) | todas as do BR-DWGD; **na chuva conta como F4 só se a documentação confirmar correção por uma rede distinta do GPCC (CPC/NOAA); senão entra em F1**. O trecho GEOS-IT (meses recentes, **sem** correção por pluviômetros) fica fora da regra, só relato |
| F5 – reanálise ECMWF | ERA5-Land bruto | chuva (sem pluviômetros), Tmax, Tmin, UR, VPD, radiação, vento |
| F6 – modelo de superfície GLDAS | GLDAS-2.0 (1961–2014), GLDAS-2.1 (2000–) | Tmax, Tmin, UR, VPD, radiação, vento (a chuva do 2.1 é F1) |
| F7 – água medida por satélite, sem pluviômetro | GRACE/GRACE-FO (armazenamento de água), SMAP (umidade do solo 0–5 cm) | chuva (indireto) |
| F8 – rios | vazão da ANA (só se o responsável liberar o acesso; CAMELS-BR até 2018 como régua) | chuva (indireto) |

Resolução: as médias são mensais por região e estado; o pixel grosso do POWER (0,5° × 0,625°; radiação 1°) e do GRACE
(~0,5° e efetivo ~300 km) não impede a conta. Estados com menos de 4 pixels da testemunha e o litoral ficam marcados.

## 3. Testes e regras (fixadas agora)

### A1. Degrau ano a ano (2020–2025 e 2026)
Para cada variável × testemunha × região (5 + Brasil) × ano: **rel** = (SAB ÷ testemunha no ano) ÷ (mediana de SAB ÷
testemunha em 2001–2015) − 1, em %, para chuva, radiação, vento e ETo; **dif** = (SAB − testemunha no ano) − (mediana
de 2001–2015) para Tmax, Tmin (°C), UR (p.p.) e VPD (kPa). Ruído de cada série: MAD de rel (ou dif) em 2001–2019.
- **Degrau no ano:** |rel ou dif| > máximo(3 × MAD; tolerância), com tolerância de 5% (chuva), 3% (ETo), 0,5 MJ/m²/dia
  (radiação), 0,3 °C (Tmax, Tmin), 2 p.p. (UR), 0,05 kPa (VPD), 10% (vento).
- **Degrau confirmado no ano:** em ≥ 2 famílias independentes, com o mesmo sinal.
- **Degrau persistente:** confirmado em ≥ 3 dos anos 2020–2024 (2025 relatado à parte por ter o fim do ano com poucos
  pluviômetros).

### A2. O clima explica? (El Niño / La Niña)
Índice: RONI do CPC (o da rotina `rotinas/roni`, tabela `auditoria_RONI_SAB_x_CPC.csv`, coluna RONI).
1. **Regressão:** em 1981–2019, por variável × família × região, a anomalia mensal de rel (ou dif), sem o ciclo do ano,
   contra o RONI do mesmo mês e com defasagem de 1 a 3 meses (o maior |r| dos 4, escolhido só com 1981–2019). Com a
   regressão, prevê-se o rel (ou dif) de 2020–2025 a partir do RONI observado. **Resíduo** = observado − previsto.
2. **Análogos:** a média de rel (ou dif) nos episódios do passado contra os de agora: La Niña 1998–2001, 2007–08 e
   2010–12 contra 2020–23; El Niño 1997–98 e 2015–16 contra 2023–24 (meses com RONI ≤ −0,5 ou ≥ +0,5).
- **O clima explica** se as duas valerem: (a) a média do resíduo em 2020–2024 fica abaixo da tolerância do A1 **ou**
  abaixo de 2 erros-padrão; (b) a diferença entre os episódios de agora e os análogos do passado fica abaixo da
  tolerância do A1, nas duas fases.
- **O clima não explica** se (a) e (b) falharem. Uma só falhando = **inconclusivo** naquele item.

### A3. Testemunhas físicas da água (só chuva)
- **GRACE/GRACE-FO** (Earth Engine; a coleção e o período disponíveis são registrados): por região, a variação anual
  do armazenamento (ΔS, abril→abril) contra a chuva anual de cada base. Em 2003–2019, regressão de ΔS na anomalia de
  chuva de cada base; em 2020–2024, o erro de previsão de ΔS com a chuva de cada base.
- **SMAP** (desde abr/2015): por região e mês, a anomalia da umidade do solo 0–5 cm contra a anomalia da chuva do mês e
  do anterior; em 2015–2019, regressão; em 2020–2025 (e 2026), o erro com a chuva de cada base.
- **Regra:** a testemunha física **fica com as referências** se o erro com a chuva do SAB em 2020–2024 crescer mais de
  25% em relação a 2003–2019 (GRACE) ou 2015–2019 (SMAP) **e** o erro com a mediana das referências não crescer mais de
  10%. **Fica com o SAB** no caso inverso. Senão, neutra.
- **Rios (F8):** só se o responsável liberar o acesso à ANA; regra igual (vazão anual × chuva anual, 1981–2018 contra
  2020–2024), em bacias com série completa.

### A4. A rede do BR-DWGD
- Se o asset no Earth Engine tiver os controles (número de estações e distância à mais próxima; o `investigar_brdwgd.py`
  registra as bandas), ou pelos arquivos `pr_Control` da v_3.2.4 (Dropbox/Drive do autor, baixados na fila): pixels de
  **rede estável** (número de estações usadas variando menos de 10% e distância à mais próxima variando menos de 10 km
  entre 2015–2019 e 2020–2024) contra pixels de **rede mudada** (o resto).
- **Regra:** a causa é a rede se o degrau da chuva (rel × CHIRPS e × F1) nos pixels de rede estável for menor que a
  metade do degrau nos de rede mudada, e a diferença passar a tolerância do A1. Sem os controles, o A4 é relatado como
  "não feito" e não entra na decisão.

### A5. Decomposição
Do `investigar_brdwgd.py`: dias ≥ 1 mm, intensidade (total ÷ dias), maior dia e cobertura, BR-DWGD × CHIRPS × ERA5-Land,
ano a ano; e se o banco (`sab_pedido.colecao`) é o BR-DWGD bruto (SAB/BR a 0,5%). Só descritivo (mostra COMO mudou).

### A6. Os outros saltos da lista
Os degraus já confirmados pelo multifonte (UR Nordeste 1961–70; ETo Norte 2001–10; ET real Sudeste 2001–10) e os
provisórios (Tmin/VPD/radiação/vento 1961–70; VPD/ETo/radiação Norte 2001–10) passam pelo A1 por ano e pelo A2,
com as mesmas regras, para separar clima de dado também neles.

### A7. Cadeia: 2026 e a previsão
- Registrar, lendo o código do motor (V1.7 e V1.8) e da matriz do GFS, **quais anos** entram em cada calibração.
- Se algum ano de 2020–2025 entra: medir quanto a calibração muda refeita sem 2020–2025 (só leitura, 05a), por região e
  mês. Mudança > tolerância do A1 em ≥ 2 regiões = **a cadeia herdou o degrau**.
- 2026 até ontem: A1 contra CHIRPS, IMERG, GLDAS-2.1 e NASA POWER (MERRA-2/GEOS-IT só relato), e SMAP pelo A3.

## 4. Decisão (por variável × região)
- **Degrau dos dados CONFIRMADO** se: A1 persistente **e** A2 "o clima não explica" **e**, na chuva, A3 com pelo menos
  uma testemunha física com as referências e nenhuma com o SAB. (O A4, se feito, indica a causa; não é exigido.)
- **Clima:** A2 "o clima explica" **ou**, na chuva, as testemunhas físicas com o SAB → nenhuma correção; registra-se que
  as referências erram naquele período.
- **Inconclusivo** em qualquer outro caso → **aviso no dicionário**, nenhuma correção.
- Para o degrau confirmado, vão ao responsável, com os números, as opções: (a) V1.8 com as razões do C3 só de anos
  estáveis (2010–2019), testada fora da amostra como na fase 1; (b) 2020–2025 do histórico: ajuste do nível na leitura
  pela regra do M5 (relação média das décadas vizinhas com as famílias confirmadas) **ou** só aviso; (c) a cadeia
  (2026/previsão) recalibrada sem os anos afetados, se o A7 mostrar herança. **Cada opção só com autorização.**

## 5. Auditoria minuciosa (como cada número é conferido)
1. **Receita:** antes de usar uma testemunha, o total anual do Brasil e de 3 estados é conferido contra o valor
   publicado ou o calculado por outra rota (tolerância 2%); unidades e escalas de cada banda registradas.
2. **Conta em dobro:** as regras do A1 e do A2 são calculadas por duas implementações independentes (pandas e numpy
   puro, com funções escritas separadamente); qualquer diferença > 0,01 p.p. (ou 0,001 na unidade) para a decisão.
3. **Sensibilidade (relatada, não muda a regra):** base 1991–2019 no lugar de 2001–2015; estados no lugar de regiões;
   tolerância × 0,5 e × 2; sem os meses de RONI > ±2.
4. **Teste sintético:** uma série com degrau inserido de propósito (+10% a partir de 2020) e uma com efeito de ENSO
   inserido (sem degrau) passam pelo A1/A2: o primeiro tem de sair "dados", o segundo "clima". Se falhar, o teste é
   corrigido ANTES de olhar os dados reais (emenda datada).
5. **Rastreabilidade:** cada RESULTADOS traz o commit do código, as coleções e versões lidas, as datas de acesso e o
   caminho de cada CSV; os LOG ficam em `rotinas/conferencia/logs/`.

## 6. Ordem e automação
1. Sem Earth Engine (dados que já subiram: `resultados_historico`, `resultados_multifonte`, RONI): **teste sintético
   (5.4) → A1 → A2 → A6** → resultado no mesmo dia.
2. Pela fila do GitHub: **NASA POWER** (API mensal regional, 1981–) → entra no A1/A2; **GRACE e SMAP** (A3);
   **controles da rede** (A4); A5 já está rodando (`brdwgd`).
3. A7 (leitura do código e 05a sem 2020–2025).
4. Decisão (seção 4) → aviso no celular → o responsável decide.
