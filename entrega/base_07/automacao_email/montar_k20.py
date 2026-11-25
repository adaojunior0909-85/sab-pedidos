# Monta validacoes/K20_validacao_correcao_pixels_b.py embutindo, sem mudança, a rotina sab_pedido.py 2026.11.03.
import hashlib
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
rot = open(os.path.join(AQUI, 'sab_pedidos', 'sab_pedido.py'), encoding='utf-8').read()
mod = open(os.path.join(AQUI, 'k20_modelo.py'), encoding='utf-8').read()
assert "'''" not in rot and mod.count('<<ROTINA>>') == 1
mod = mod.replace('<<ROTINA>>', rot)
saida = os.path.join(AQUI, '..', 'validacoes', 'K20_validacao_correcao_pixels_b.py')
open(saida, 'w', encoding='utf-8').write(mod)
compile(mod, saida, 'exec')
print('K20 montada:', os.path.normpath(saida), '| rotina SHA-256', hashlib.sha256(rot.encode('utf-8')).hexdigest()[:16])
