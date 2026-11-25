# O painel PRONTO (o que vai para o Code Editor) é o painel-base com o endereço dos pedidos preenchido, e nada mais.
#   python3 montar_painel_pronto.py && python3 testes/teste_06_pronto.py
import os
import re
import sys
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ler = lambda n: open(os.path.join(RAIZ, n), encoding='utf-8').read()
base, pronto = ler('06_painel_sab_2026_11_5.js'), ler('06_painel_sab_2026_11_5_PRONTO.js')
url = re.search(r"  urlPedidoEmail: '(https://script\.google\.com/macros/s/[^']+/exec)',", pronto)
ok = bool(url) and pronto.replace(url.group(0), "  urlPedidoEmail: '',") == base and "versao: '2026.11.5'" in pronto
print(('  ok   ' if ok else '  FALHA ') + 'PRONTO = painel 2026.11.3 + endereço /exec dos pedidos')
print('TODOS OS TESTES PASSARAM' if ok else '1 FALHA(S)')
sys.exit(0 if ok else 1)
