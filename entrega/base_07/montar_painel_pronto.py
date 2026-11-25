# Gera 06_painel_sab_2026_11_5_PRONTO.js: o painel com o endereço do App da Web dos pedidos já preenchido, para colar
# direto no script SAB_painel_2026_10_6 (app adao-alves-rodrigues-junior-sab). O arquivo-base fica com urlPedidoEmail
# vazio, porque a K16 e os testes rodam o painel sem o envio por e-mail.
import os
AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = '06_painel_sab_2026_11_5.js'
URL_PEDIDO = 'https://script.google.com/macros/s/AKfycbzNDVBp7HJgZo1xzi6BlhNUNJuTG9EwW_eYfhxSpTBu7XaB__MF-btlSTytz2mphPVC/exec'
src = open(os.path.join(AQUI, BASE), encoding='utf-8').read()
assert src.count("  urlPedidoEmail: '',") == 1
saida = os.path.join(AQUI, BASE.replace('.js', '_PRONTO.js'))
open(saida, 'w', encoding='utf-8').write(src.replace("  urlPedidoEmail: '',", f"  urlPedidoEmail: '{URL_PEDIDO}',"))
print('painel pronto:', saida)
