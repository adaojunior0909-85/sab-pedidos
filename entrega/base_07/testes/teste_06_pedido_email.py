# Confere que os códigos que o painel 2026.10.7 gera são aceitos pela rotina do e-mail (sab_pedido.py).
# Rodar depois de: node testes/teste_06_pedido_email.js
import os
import sys
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'automacao_email', 'sab_pedidos'))
import sab_pedido as sp  # noqa: E402

falhas = 0
for linha in open(os.path.join(AQUI, 'dados', 'codigos_painel_2026_11_5.txt'), encoding='utf-8'):
    cod = linha.strip()
    if not cod:
        continue
    try:
        p = sp.validar(sp.ler_codigo(cod), date(2026, 11, 1))
        print(f"  ok   {p['tipo']} {sp.texto_local(p)[:60]} | variáveis: {','.join(p['variaveis'])}")
    except sp.PedidoInvalido as e:
        falhas += 1
        print(f'  FALHA {cod}: {e}')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'CÓDIGOS DO PAINEL ACEITOS PELA ROTINA'))
sys.exit(1 if falhas else 0)
