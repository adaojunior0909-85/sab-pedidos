# Como remontar a pasta de entrega (o zip)

`bash entrega/montar_entrega.sh <pasta de saída>` (opcional: o caminho de um clone do `sab-motor` como 2º argumento).
Antes, escreva a seção nova, datada, no topo de `entrega/base_07/LEIA_PRIMEIRO_modelo.md`. O script copia a base, põe
dentro dela este repositório (o checkout atual), roda os 58 testes, monta a entrega, junta os extras e o
`REGISTRO_GERAL.md`, refaz o `SHA256SUMS.txt` e o zip. Não fala com o Earth Engine nem com o GitHub.
