# Protocolo da fase 2: correção de todas as variáveis (analisar antes, gravar só com autorização)

**Pedido do responsável (25/11/2026, ~19h40):** "deixa tudo automatizado para primeiro analisar e aí gravar; caso dê
positivo, a gravação somente sob autorização, independente se irá pegar todo o banco ou somente 2026. Quero correção de
todas as variáveis." Este protocolo é **congelado num commit ANTES de qualquer resultado**; depois de rodar, nada nele
muda (uma emenda só antes de rodar o módulo afetado, datada, como a emenda 1 do protocolo da fase 1).

## Regras que valem para todos os módulos
1. **Só leitura** no Earth Engine durante os testes. Nada é gravado sem autorização explícita do responsável, módulo a
   módulo, depois de ver o resultado.
2. **Teste fora da amostra:** cada ano (ou período) avaliado é corrigido só com dados que não o incluem (origem móvel
   como na fase 1, ou deixando um ano de fora quando a referência cobre poucos anos).
3. **A base de comparação é o que o banco entrega hoje** (para a chuva de 2026, a V1.8 quando estiver gravando; para o
   resto, a V1.7). Um método só substitui a base se cumprir a regra do módulo.
4. **Caminho depois de um resultado positivo** (cada passo só com autorização):
   - dias de 2026 em diante (ERA5 e previsão): motor em simulação (05a) e prévia → gravação (05b; regrava só 2026);
   - histórico 1961–2025: **nunca é regravado no asset** (regra do projeto); a correção, se aprovada, entra **na leitura**
     (painel e `sab_pedido.py` juntos) com **K16 nova** antes de abrir ao público.
5. **Automação:** os testes rodam pela fila do GitHub; a vigia acompanha e, quando um módulo termina, avisa o responsável
   no celular com o veredito ("SAB: precisa de você – aprovar gravação de …" se algum método passou).
6. Onde **não existe referência independente confiável**, o módulo conclui por **aviso no dicionário**, não por correção:
   corrigir sem referência só troca um erro desconhecido por outro.

## M1. Chuva dos dias ERA5 (2026 em diante), além da V1.8
Achados que motivam: a V1.8 (C3) passa do ponto no Sul em 2026 × CHIRPS (+4,1% → +15,5%; régua +3,8%) e o ERA5 tem dias
de chuva demais (Nordeste 33,3% × 29,7% do BR-DWGD; "garoa").
- **Referência e desenho:** os da fase 1 (BR-DWGD, 2016–2025, origem móvel; 120 meses × 5 regiões; extremos em todos os
  pixels entregues e p99 em 1.500 pixels).
- **Métodos (lista fechada):**
  - **C3R, razão só onde o viés é consistente:** a razão do C3 é aplicada na região e no mês só se, nos 5 anos
    anteriores, |razão − 1| ≥ 0,05 **e** a razão de cada ano tiver o mesmo sinal (acima ou abaixo de 1) em pelo menos 4
    dos 5 anos; senão, razão 1 (fica a chuva da V1.7).
  - **C3G, garoa + C3:** antes da razão, o dia com chuva abaixo de um limiar vira 0; o limiar é de cada região e mês,
    estimado nos 1.500 pixels com os anos anteriores ao ano-alvo, para que a fração de dias ≥ 1 mm do ERA5 calibrado
    seja igual à do BR-DWGD; a razão do C3 é refeita depois do limiar.
  - **C3RG:** as duas juntas.
- **Regra (contra o C3):** um método substitui o C3 se cumprir **todas**:
  1. a mediana, nas 5 regiões, do |viés anual| não piora mais de **0,5 p.p.**;
  2. melhora em pelo menos um objetivo: (a) a soma, nas 5 regiões, do afastamento da fração de dias de chuva em relação
     ao BR-DWGD cai **20%** ou mais; ou (b) a pior região (maior |viés anual| mediano) melhora **2 p.p.** ou mais;
  3. o r_anomalias não cai mais de **0,02** em nenhuma região;
  4. o erro do Rx1day (todas as regiões) e do p99 (1.500 pixels) não cresce mais de **5%**.
  Mais de um passa: vence o de menor soma de afastamento da fração de dias de chuva; empate (< 5%): o mais simples (C3R,
  C3G, C3RG). Relato fora da regra: 2026 × CHIRPS, como na fase 1.

## M2. Radiação e ETo (2026 em diante)
Achado: a V1.7 deixa a radiação +0,45 MJ/m²/dia e a ETo +2,2% acima do BR-DWGD (2016–2025); C1, C2 e C3 reprovaram.
- **Métodos:**
  - **R1, razão multiplicativa regional:** Rs × (BR-DWGD ÷ V1.7) da região e do mês nos 5 anos anteriores, limitada a
    [0,85; 1,15], depois limitada ao céu claro;
  - **R2, mapeamento por quantis regional:** os decis da radiação diária do ERA5 calibrado e do BR-DWGD, por região e
    mês, nos 1.500 pixels, com os anos anteriores; a radiação do dia é levada do decil do ERA5 ao do BR-DWGD
    (interpolação linear entre decis; fora da faixa, desloca pela diferença do extremo); depois, céu claro.
  - Em todos, a ETo é recalculada pelo FAO-56 com a radiação corrigida.
- **Regra:** a do protocolo da fase 1 (|viés| da radiação no Brasil cai ≥ 0,2 MJ/m²/dia, o da ETo ≥ 1 p.p., nenhuma
  região piora mais de 0,1 MJ ou 0,5 p.p.), mais: o r_anomalias da radiação não cai mais de 0,02 em nenhuma região.

## M3. Tmax, Tmin, umidade relativa, VPD e vento (2026 em diante)
Achado (Parte A): desvios pequenos (Tmax +0,2 °C, UR −0,9 p.p., Tmin e vento ~0).
- **Métodos:** **T1** janela de 10 anos (a média de Y−10 a Y−1 no lugar de 1986–Y−1, como o C1); **T2** ajuste
  aditivo regional dos 5 anos anteriores (como o C3, aditivo; no vento, multiplicativo limitado a [0,9; 1,1]).
- **Regra, por variável:** substitui a base se o |viés| no Brasil cair pelo menos **0,1 °C** (Tmax, Tmin), **0,5 p.p.**
  (UR), **0,02 kPa** (VPD) ou **0,05 m/s** (vento), nenhuma região piorar mais que esse mesmo valor e o r_anomalias não
  cair mais de 0,02 em nenhuma região. A VPD e a ETo são sempre recalculadas das variáveis corrigidas.

## M4. Variáveis do modelo (ET real, transpiração, temperaturas do solo e da folha, umidade do solo, escoamento)
Todos os períodos. Referências disponíveis e por que elas não servem para corrigir o nível:
| Variável | Referência | Serve para corrigir? |
|---|---|---|
| Umidade do solo 0–5 cm | SMAP (2016–2021) | já é a referência da calibração atual (fator SMAP/ERA5): **não há o que corrigir além disso** |
| Umidade do solo 0–100 cm | nenhuma observação no país | **não** |
| Temperatura do solo e da folha | MODIS LST (2016–2021) | **não**: o MODIS mede a superfície num horário de passagem; o SAB é a média do dia (o nível difere por definição; r = 0,80 confirma o desenho) |
| ET real | MOD16 (2016–2021) | **não**: o MOD16 é outro modelo (no Norte, r = 0,06 entre os dois); trocar um pelo outro não é correção |
| Transpiração, escoamento subsuperficial | nenhuma | **não** |
| Escoamento total | vazão de 512 bacias (CAMELS-BR) | **já testado** (fase anterior): nenhum dos 3 métodos passou |
- **Conclusão fixada antes:** M4 não grava correção. Entrega: **avisos no dicionário** com os números medidos (ET real
  como índice; escoamento abaixo da vazão dos rios; temperaturas do solo e da folha como médias do dia, não comparáveis
  ao satélite), e o teste de **degrau no tempo** dessas variáveis no histórico (o M5 cobre).

## M5. Histórico 1961–2025 (as 8 variáveis do BR-DWGD e as do modelo)
Depende do teste `historico` (TerraClimate e CHIRPS, por década; regra de "década suspeita" fixada no
`pesquisa/validar_historico.py`).
- Uma correção só é considerada para **década × variável × região marcada como suspeita** pelo teste **e** confirmada por
  uma segunda referência independente (CHIRPS para a chuva desde 1981; para as outras, a reanálise ERA5 bruta, que não
  usa as estações do BR-DWGD).
- **Método (se houver suspeita confirmada):** ajuste do nível da década suspeita para a relação média com a referência
  nas décadas vizinhas (aditivo nas temperaturas, multiplicativo na chuva, vento e radiação), **só na leitura**.
- **Regra:** depois do ajuste, a década deixa de ser suspeita nas duas referências e nenhuma outra década passa a ser.
- Gravação: na leitura (painel + `sab_pedido.py`), K16 nova, só com autorização.

## M6. Previsão (GFS, 1 a 15 dias)
Depende de ~30 dias de fotografias da rotina diária (desde 24/11).
- **Medida:** para cada prazo e região, o erro do GFS calibrado × a persistência (o último dia observado repetido).
- **Regra:** num prazo em que o GFS calibrado erra mais que a persistência em 3 ou mais das 5 regiões, em Tmax, Tmin ou
  chuva, propõe-se (a) refazer a calibração daquele prazo pela matriz com os dados novos ou (b) não entregar aquele
  prazo; a escolha vai ao responsável com os números.

## Ordem e automação
1. **M1-C3R** (sem Earth Engine novo: usa os dados da fase 1) → resultado no mesmo dia.
2. **M1-C3G/C3RG, M2 e M3** (Earth Engine, pela fila; várias horas cada).
3. **M5** quando o `historico` terminar; **M6** com 30 dias de fotografias (~24/12).
4. **M4**: os avisos do dicionário entram com as conclusões.
Resultados em `pesquisa/resultados_fase2/` (um `RESULTADOS_<módulo>.md` por módulo).
