# Dados do CAMELS-BR usados na comparação do escoamento

Derivados do **CAMELS-BR v1.1**: Chagas, V. B. P. et al. (2020). CAMELS-BR: hydrometeorological time series and
landscape attributes for 897 catchments in Brazil. *Earth System Science Data*, 12, 2075–2096.
Dados: doi:10.5281/zenodo.3964745. Licença **CC-BY-4.0** (uso livre com citação). A vazão é da ANA.

Gerados por `pesquisa/escoamento/preparar_camels.py` (seleção e simplificação descritas no protocolo,
`pesquisa/PROTOCOLO_ESCOAMENTO_CAMELS.md`):
- `bacias.csv`: as 512 bacias selecionadas e os atributos usados na seleção;
- `bacias.geojson`: os contornos simplificados (tolerância 0,01°);
- `vazao_mensal.csv.gz`: a vazão mensal observada (mm/mês), 1981–2018, nos meses com pelo menos 25 dias observados.
