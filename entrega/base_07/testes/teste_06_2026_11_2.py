# A 2026.11.2 só acrescenta a autoria e o link oficial no topo do painel: confere que, tirando essas linhas, o código
# é o mesmo da 2026.11.1 (validada pela K20 e pela K16 v4).
#   python3 testes/teste_06_2026_11_2.py
import difflib
import os
import re
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ler = lambda n: open(os.path.join(RAIZ, n), encoding='utf-8').read().splitlines()
a, b = ler('06_painel_sab_2026_11_1.js'), ler('06_painel_sab_2026_11_2.js')
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


tirados = [l for l in difflib.ndiff(a, b) if l.startswith('- ')]
postos = [l[2:] for l in difflib.ndiff(a, b) if l.startswith('+ ')]
confere(len(tirados) == 1 and "versao: '2026.11.1'" in tirados[0], 'só a linha da versão foi trocada')
confere(len(postos) == 9, f'{len(postos)} linhas novas (cabeçalho, versão, autoria, link e os 2 rótulos)')
permitidas = ('//', "  versao: '2026.11.2'", '  autoria:', '  urlApp:', 'painel.add(ui.Label(CFG.autoria',
              "painel.add(ui.Label('🔗 Link oficial do painel'")
confere(all(l.strip() == '' or l.lstrip().startswith(permitidas) or l.startswith(permitidas) for l in postos),
        'nenhuma linha de cálculo nova')
link = re.search(r"urlApp: '([^']+)'", '\n'.join(b)).group(1)
confere(link == 'https://clima-492922.projects.earthengine.app/view/adao-alves-rodrigues-junior-sab', 'link oficial')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
