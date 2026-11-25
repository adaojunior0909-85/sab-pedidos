# Teste offline da união de dias da classe B no 01 (v4.1), com uma imagem falsa em numpy.
# Semântica de máscara assumida (A CONFIRMAR no Earth Engine): operação binária -> máscara mínima;
# where(test, v) com test mascarado mantém a entrada. Origem: simulação da revisão independente da v4.1.
# Rodar: python3 testes/teste_01_uniao.py  (a partir da pasta do pacote)
# Simulação numpy (semântica de máscara do EE assumida: operação binária -> máscara mínima;
# where(test, v): test mascarado mantém a entrada) das funções novas do 01 (extraídas por AST).
import ast, sys
import numpy as np
import os
ARQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '01a_mascara_qualidade_SIMULACAO.py')
fonte = open(ARQ, encoding='utf-8').read()
nos = [n for n in ast.parse(fonte).body if isinstance(n, ast.FunctionDef)
       and n.name in ('codigo_abc', 'estrutura', 'uniao_b', 'classes_estaveis', 'resumo_conferencia')]

class Img:
    def __init__(self, v, m=None):
        self.v = np.array(v, dtype=float); self.m = np.ones_like(self.v) if m is None else np.array(m, dtype=float)
    def _b(self, o, f):
        o = o if isinstance(o, Img) else Img(np.full_like(self.v, o))
        return Img(f(self.v, o.v).astype(float), np.minimum(self.m, o.m))
    def And(self, o): return self._b(o, lambda a, b: (a != 0) & (b != 0))
    def Or(self, o): return self._b(o, lambda a, b: (a != 0) | (b != 0))
    def Not(self): return Img((self.v == 0).astype(float), self.m)
    def neq(self, o): return self._b(o, lambda a, b: a != b)
    def eq(self, o): return self._b(o, lambda a, b: a == b)
    def rename(self, *_): return self
    def where(self, t, val):
        val = val if isinstance(val, Img) else Img(np.full_like(self.v, val))
        ok = (t.m > 0) & (t.v != 0) & (val.m > 0) & (self.m > 0)
        return Img(np.where(ok, val.v, self.v), self.m)

N = 7
class EE:
    @staticmethod
    def Image(x): return Img(np.full(N, float(x)))
M = {'ee': EE}
exec(compile(ast.Module(body=nos, type_ignores=[]), ARQ, 'exec'), M)

def cl(sab_ok, br_ok, igual, sab_m=None):
    s = Img(sab_ok, sab_m); b = Img(br_ok); i = Img(igual)
    return {'A': s.And(b).And(i), 'B': s.And(b).And(i.Not()), 'C': s.And(b.Not()), 'D': s.Not().And(b)}
# pixels: 0 B c/ coincidência em julho; 1 B c/ coincidência no dia de ref; 2 A; 3 C; 4 D; 5 nada; 6 A com 1 dia "B" em janeiro
dias = ['2001-01-15', '1961-01-15', '1981-07-01', '2017-07-15', '2025-01-15']
base_s = [1, 1, 1, 1, 0, 0, 1]; base_b = [1, 1, 1, 0, 1, 0, 1]
ig = {d: [0, 0, 1, 0, 0, 0, 1] for d in dias}
ig['1981-07-01'][0] = 1; ig['2001-01-15'][1] = 1; ig['2025-01-15'][6] = 0
cls = {d: cl(base_s, base_b, ig[d]) for d in dias}
ref = cls[dias[0]]; bu = M['uniao_b'](cls)
abc = M['codigo_abc'](M['classes_estaveis'](ref, bu))
ref = cls[dias[0]]; bu = M['uniao_b'](cls)
abc = M['codigo_abc'](M['classes_estaveis'](ref, bu))
est_ref = M['estrutura'](ref)
FALHAS = []


def confere(cond, msg):
    print(('  ok   ' if cond else '  FALHA ') + msg)
    if not cond:
        FALHAS.append(msg)


# pixels: 0 B com coincidência em julho; 1 B com coincidência no dia de referência; 2 A; 3 C; 4 D; 5 nada;
# 6 A que fica B num único dia de janeiro (anomalia: entra na união e o histograma do 01 mostra 1 dia em B)
confere(abc.v.astype(int).tolist() == [2, 2, 1, 3, 0, 0, 2], 'classes: B, B, A, C, sem SAB, sem SAB, B')
esperado_b_iguais = {'2001-01-15': 2, '1961-01-15': 1, '1981-07-01': 2, '2017-07-15': 1, '2025-01-15': 0}
for d in dias:
    e = M['estrutura'](cls[d]).neq(est_ref)
    c = bu.And(cls[d]['A'])
    confere(int((e.v * (e.m > 0)).sum()) == 0, f'{d}: estrutura igual à do dia de referência')
    confere(int((c.v * (c.m > 0)).sum()) == esperado_b_iguais[d], f'{d}: {esperado_b_iguais[d]} pixel(s) B iguais no dia')
confere(abc.v[1] == 2, 'pixel B que coincidiu no próprio dia de referência continua B (o defeito da v4)')
n_b = sum(cls[d]['B'].v for d in dias) * bu.v
confere(int(n_b[6]) == 1 and int(n_b[0]) == 4 and int(n_b[1]) == 4, 'dias em B: 4 nos B com 1 coincidência; 1 no pixel anômalo')
m = np.ones(N)
m[4] = 0
cls2 = dict(cls)
cls2['1981-07-01'] = cl(base_s, base_b, ig['1981-07-01'], sab_m=m)
e = M['estrutura'](cls2['1981-07-01']).neq(est_ref)
confere(int(e.v.sum()) == 1, 'pegada do SAB diferente num dia: estrutura acusa (o 01 para com ❌)')
print(f'\n{"TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S)"}')
sys.exit(1 if FALHAS else 0)
