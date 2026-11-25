# A 2026.11.4 do painel só troca o TEXTO de duas linhas do dicionário (Chuva_Efetiva_mm e Runoff_Superficial_mm), a
# versão e o cabeçalho. Confere que fora disso o painel é byte a byte o da 2026.11.3 (cálculos e CSV iguais) e que as
# duas linhas são idênticas às do dicionário da rotina do e-mail (sab_pedido.py), como a K16 exige.
# Rodar: python3 testes/teste_06_2026_11_4.py
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'automacao_email', 'sab_pedidos'))
import sab_pedido as sp  # noqa: E402

ler = lambda n: open(os.path.join(AQUI, '..', n), encoding='utf-8').read()
novo, velho = ler('06_painel_sab_2026_11_4.js'), ler('06_painel_sab_2026_11_3.js')
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


MUDAM = ('Chuva_Efetiva_mm', 'Runoff_Superficial_mm')
DESC = r"(ee\.Feature\(null, \{'Variavel': '(%s)', 'Descricao': ')([^']*)(')"


def neutro(src):
    """O painel sem o que a 2026.11.4 muda de propósito: o bloco do cabeçalho 2026.11.4, a linha da versão e o texto
    das duas linhas do dicionário."""
    src = re.sub(r"// VERSÃO 2026\.11\.4 .*?(?=// VERSÃO 2026\.11\.3)", '', src, flags=re.S)
    src = re.sub(r"  versao: '2026\.11\.[34]', // (\[2026\.11\.4\] aviso do escoamento no dicionário; )?", "  versao: 'X', // ", src)
    return re.sub(DESC % '|'.join(MUDAM), r'\1<texto>\4', src)


confere(neutro(novo) == neutro(velho), 'fora do cabeçalho, da versão e das 2 linhas do dicionário, igual à 2026.11.3')
confere("versao: '2026.11.4'" in novo, "versão '2026.11.4'")
rotina = {v: d for v, d, u in sp.DICIONARIO}
painel = {m.group(2): m.group(3) for m in re.finditer(DESC % '|'.join(MUDAM), novo)}
for v in MUDAM:
    confere(painel.get(v) == rotina[v], f'{v}: texto idêntico ao da rotina {sp.VERSAO_ROTINA}')
    confere('ATENCAO nos dias de 1961 a 2025' in painel.get(v, ''), f'{v}: traz o aviso do escoamento')
todas = {m.group(1): m.group(2) for m in re.finditer(r"ee\.Feature\(null, \{'Variavel': '([^']+)', 'Descricao': '([^']*)'", novo)}
outras = [v for v in todas if v in rotina and v not in MUDAM and todas[v] != rotina[v]]
print(f'   (outras linhas do dicionário que já diferiam da rotina de propósito, como na K16: {outras})')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
