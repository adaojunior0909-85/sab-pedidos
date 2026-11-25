# A 2026.11.5 do painel só acrescenta a regra da radiação impossível (onde Rs fica abaixo de 3% de Ra, Rs, ETo e déficit
# do dia saem vazios): as funções radiacaoTopo e vazioRsImpossivel, a chamada dela no fim do grampo termodinâmico, o
# texto da linha Radiacao_Solar_MJ_m2 do dicionário, a versão e o cabeçalho. Confere que fora disso o painel é byte a byte o da 2026.11.4
# e que a regra e o texto são os mesmos da rotina do e-mail (sab_pedido.py 2026.11.22), como a K16 exige.
# Rodar: python3 testes/teste_06_2026_11_5.py
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'automacao_email', 'sab_pedidos'))
import sab_pedido as sp  # noqa: E402

ler = lambda n: open(os.path.join(AQUI, '..', n), encoding='utf-8').read()
novo, velho = ler('06_painel_sab_2026_11_5.js'), ler('06_painel_sab_2026_11_4.js')
rot = ler(os.path.join('automacao_email', 'sab_pedidos', 'sab_pedido.py'))
falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


DESC = r"(ee\.Feature\(null, \{'Variavel': 'Radiacao_Solar_MJ_m2', 'Descricao': ')([^']*)(')"
BLOCO = re.compile(r"// \[2026\.11\.5\] Radiação no topo da atmosfera.*?\n}\n\n// \[2026\.11\.5\] Onde Rs fica.*?\n}\n\n", re.S)
GRAMPO_NOVO = ("        // [2026.11.5] depois do grampo: radiação impossível (abaixo de 3% de Ra) vazia, com a ETo e o déficit do dia\n"
               "        return vazioRsImpossivel(imagem.addBands(ee.Image.cat([amp_diaria, def_diario, chuva_ef])));")
GRAMPO_VELHO = "        return imagem.addBands(ee.Image.cat([amp_diaria, def_diario, chuva_ef]));"


def neutro(src):
    """O painel sem o que a 2026.11.5 muda de propósito."""
    src = re.sub(r"// VERSÃO 2026\.11\.5 .*?(?=// VERSÃO 2026\.11\.4)", '', src, flags=re.S)
    src = re.sub(r"  versao: '2026\.11\.[45]', // (\[2026\.11\.5\] radiação abaixo de 3% de Ra sai vazia; )?", "  versao: 'X', // ", src)
    src = BLOCO.sub('', src)
    src = src.replace(GRAMPO_NOVO, GRAMPO_VELHO)
    return re.sub(DESC, r'\1<texto>\3', src)


confere(neutro(novo) == neutro(velho), 'fora da regra da radiação, do texto, da versão e do cabeçalho, igual à 2026.11.4')
confere("versao: '2026.11.5'" in novo, "versão '2026.11.5'")
confere(len(BLOCO.findall(novo)) == 1 and novo.count(GRAMPO_NOVO) == 1 and novo.count('vazioRsImpossivel(') == 2,
        'as duas funções novas e a regra chamada uma vez, no fim do grampo (depois da ET real limitada)')
lista = lambda t, nome: re.search(nome + r" = \[([^\]]*)\]", t).group(1).replace('"', "'")
confere(lista(novo, 'var BANDAS_RS_IMPOSSIVEL') == lista(rot, 'BANDAS_RS_IMPOSSIVEL') == "'rs', 'et_potencial', 'deficit_diario'",
        'as mesmas 3 bandas esvaziadas (Rs, ETo e déficit), na mesma ordem')
texto = re.search(DESC, novo).group(2)
rotina = {v: d for v, d, u in sp.DICIONARIO}
confere(texto == rotina['Radiacao_Solar_MJ_m2'], f'Radiacao_Solar_MJ_m2: texto idêntico ao da rotina {sp.VERSAO_ROTINA}')
# a mesma regra: limite 0,03 de Ra, rs.gte, updateMask, e o Ra pela mesma conta da radiacaoCeuClaro
js = novo[novo.index('function radiacaoTopo('):novo.index('function getSABCollection(')]
py = rot[rot.index('def _radiacao_topo('):rot.index('def colecao(')]
num = lambda t: sorted(re.findall(r'(?<![\w.])\d+\.\d+', re.sub(r'"""[\s\S]*?"""|//.*|#.*', '', t)))
confere(num(js) == num(py), f'mesmas constantes nas duas regras: {num(js)}')
confere(all(x in js and x in py for x in ('.gte(', 'multiply(0.03)', '.updateMask(', 'subtract(1.39)')),
        'mesmas operações: Rs >= 0,03 x Ra fica; o resto vira máscara')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
