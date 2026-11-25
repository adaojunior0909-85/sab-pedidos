# Monta validacoes/K16_validacao_identidade_email.py embutindo a rotina sab_pedido.py sem mudança.
import hashlib, os
AQUI = os.path.dirname(os.path.abspath(__file__))
rot = open(os.path.join(AQUI, 'sab_pedidos', 'sab_pedido.py'), encoding='utf-8').read()
assert "'''" not in rot and not rot.endswith('\\')
mod = open(os.path.join(AQUI, 'k16_modelo.py'), encoding='utf-8').read()
assert mod.count('<<ROTINA>>') == 1
# [v3] o painel (sem mudança) e o operador da tela no Node
painel = open(os.path.join(AQUI, '..', '06_painel_sab_2026_11_5.js'), encoding='utf-8').read()
node = open(os.path.join(AQUI, 'k16_painel_node.js'), encoding='utf-8').read()
for nome, src in (('painel', painel), ('node', node)):
    assert "'''" not in src and not src.endswith('\\'), nome
assert mod.count('<<PAINEL>>') == 1 and mod.count('<<NODE>>') == 1
mod = mod.replace('<<PAINEL>>', painel).replace('<<NODE>>', node)
saida = os.path.join(AQUI, '..', 'validacoes', 'K16_validacao_identidade_email.py')
open(saida, 'w', encoding='utf-8').write(mod.replace('<<ROTINA>>', rot))
print('K16 montada | SHA-256 da rotina', hashlib.sha256(rot.encode('utf-8')).hexdigest(),
      '| SHA-256 do painel', hashlib.sha256(painel.encode('utf-8')).hexdigest())
