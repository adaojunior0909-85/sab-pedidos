#!/usr/bin/env bash
# Remonta a PASTA DE ENTREGA do SAB (o zip SAB_entrega_final_<data>.zip) só com o que está neste repositório.
#   entrega/base_07/  a base de desenvolvimento e testes (a pasta 07 da entrega), menos a cópia do sab-pedidos
#   entrega/extras/   o que a entrega tem e o montador não gera (09_Versoes_anteriores e arquivos soltos da raiz)
# A cópia do sab-pedidos dentro da base é este próprio repositório (o checkout atual, sem a pasta entrega/).
# Para atualizar o motor, passe o caminho de um clone do sab-motor como 2º argumento.
# Antes de rodar: escrever a seção nova, datada, no topo de entrega/base_07/LEIA_PRIMEIRO_modelo.md.
#     bash entrega/montar_entrega.sh <pasta de saída> [caminho do clone do sab-motor]
# Precisa de Python 3 (numpy, pandas, xlsxwriter, openpyxl) e Node 18+ para os 58 testes, e do zip.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
SAIDA=$(mkdir -p "${1:?informe a pasta de saída}" && cd "$1" && pwd)
if git -C "$REPO" fetch -q origin main 2>/dev/null && ! git -C "$REPO" merge-base --is-ancestor origin/main HEAD; then
  echo "AVISO: a main tem mudanças que este checkout não tem (ex.: resultados da fila). Junte antes: git merge origin/main"
fi
TRAB=$(mktemp -d)
cp -a "$REPO/entrega/base_07" "$TRAB/07"
mkdir -p "$TRAB/07/automacao_email/sab_pedidos"
(cd "$REPO" && git ls-files -z | grep -zv '^entrega/' | xargs -0 -I{} cp --parents {} "$TRAB/07/automacao_email/sab_pedidos/")
if [ -n "${2:-}" ]; then
  rm -rf "$TRAB/07/automacao_motor/sab-motor" && mkdir -p "$TRAB/07/automacao_motor/sab-motor"
  (cd "$2" && git ls-files -z | xargs -0 -I{} cp --parents {} "$TRAB/07/automacao_motor/sab-motor/")
fi
cp "$TRAB/07/validacoes/K26_auditoria_final.py" "$TRAB/"   # o teste da K26 lê a cópia da raiz da entrega
cd "$TRAB/07"
python3 rodar_todos_os_testes.py | tail -1
python3 montar_entrega.py "$TRAB/saida" | tail -1
N=$(ls -d "$TRAB"/saida/SAB_entrega_final_*/ | head -1); N=${N%/}
cp -a "$REPO/entrega/extras/." "$N/"
cp "$REPO/REGISTRO_GERAL.md" "$N/REGISTRO_GERAL.md"
(cd "$N" && find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum | sed 's#  \./#  #' > SHA256SUMS.txt \
  && sha256sum -c --quiet SHA256SUMS.txt && echo "SHA-256 conferido")
NOME=$(basename "$N")
rm -rf "${SAIDA:?}/$NOME" "$SAIDA/$NOME.zip"
mv "$N" "$SAIDA/"
(cd "$SAIDA" && zip -qr "$NOME.zip" "$NOME")
echo "Pronto: $SAIDA/$NOME.zip ($(find "$SAIDA/$NOME" -type f | wc -l) arquivos)"
rm -rf "$TRAB"
