# A correção de leitura dos pixels B e da radiação está IGUAL no painel (JS) e na rotina do e-mail (Python)?
# Compara as constantes numéricas, a lista do núcleo, o fim do histórico e os assets dos dois trechos.
# Rodar: python3 testes/teste_correcao_b_identica.py
import os
import re
import sys
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
js = open(os.path.join(AQUI, '..', '06_painel_sab_2026_11_5.js'), encoding='utf-8').read()
py = open(os.path.join(AQUI, '..', 'automacao_email', 'sab_pedidos', 'sab_pedido.py'), encoding='utf-8').read()
tj = js[js.index('var CORR_B = {'):js.index('function getSABCollection(')]
tp = py[py.index('def _brdwgd_do_dia('):py.index('def colecao(')]          # funções da correção
tp_const = py[py.index("BRDWGD = 'projects"):py.index("NUCLEO_B = [")]      # constantes (assets e fim)
tp = tp + tp_const
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


def numeros(t):
    t = re.sub(r'"""[\s\S]*?"""', '', t)        # docstrings
    t = re.sub(r'//.*|#.*', '', t)                      # comentários
    return Counter(x for x in re.findall(r'(?<![\w.])-?\d+\.\d+(?:e-?\d+)?|(?<![\w.])\d+e-?\d+', t))


nj, np_ = numeros(tj), numeros(tp)
confere(set(nj) == set(np_), f'mesmas constantes decimais (só no JS: {sorted(set(nj) - set(np_))}; só no Python: '
        f'{sorted(set(np_) - set(nj))})')
nuc = lambda t: re.search(r"\[('pr_mm', 'tmax_C'[^\]]*)\]", t).group(1)
confere(nuc(tj) == nuc(py), 'mesma lista e ordem das 8 bandas do núcleo')
confere("'2026-01-01'" in tj and "FIM_HISTORICO_CORRECAO = '2026-01-01'" in py, 'mesmo fim do histórico (2026-01-01, exclusivo)')
for a in ('projects/ee-alexandrexavier/assets/BR-DWGD', 'USGS/SRTMGL1_003'):
    confere(a in tj and a in py, f'mesmo asset: {a}')
confere('-32768' in tj and '-32768' in tp, 'mesmo valor ausente do BR-DWGD (-32768)')
confere(tj.count('.where(') == 2 and tp.count('.where(') == 2, 'duas substituições (núcleo B e radiação C) nos dois')
confere("classe.eq(2)" in tj and "classe.eq(2)" in tp and "classe.eq(3)" in tj and "classe.eq(3)" in tp,
        'classe 2 (B) recebe o BR-DWGD e classe 3 (C) a radiação limitada, nos dois')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
