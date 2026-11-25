# Monta validacoes/K19_auditoria_profunda_SAB.py: embute, sem mudança, o motor V1.0 (O0, que gravou o histórico) e o
# V1.5 (05b, 2026 em diante), e copia da K17 as funções de carga segura (mesma fonte, sem duplicar à mão).
import hashlib
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, '..')
MARCA = '# ================================================ ORIGINAL ================================================\n'


def original(nome):
    txt = open(os.path.join(RAIZ, 'originais_somente_registro', nome), encoding='utf-8').read()
    assert txt.count(MARCA) == 1, nome
    return txt.split(MARCA, 1)[1]


k17 = open(os.path.join(AQUI, 'k17_modelo.py'), encoding='utf-8').read()
ini, fim = k17.index('PROIBIDO_NA_CARGA = ('), k17.index('\n\ndef iguais(')
carga = k17[ini:fim].rstrip() + '\n'
fontes = {'<<V10>>': original('O0_motor_mestre_V1_0_SAB_V1_historico.py'),
          '<<V15>>': open(os.path.join(RAIZ, '05b_motor_sab_v1_5_GRAVACAO.py'), encoding='utf-8').read()}
mod = open(os.path.join(AQUI, 'k19_modelo.py'), encoding='utf-8').read()
assert mod.count('<<CARGA>>') == 1
mod = mod.replace('<<CARGA>>', carga)
for marca, src in fontes.items():
    assert "'''" not in src and not src.endswith('\\'), marca
    assert mod.count(marca) == 1, marca
    mod = mod.replace(marca, src)
for marca, src in fontes.items():
    print(f'{marca:8} SHA-256 {hashlib.sha256(src.encode("utf-8")).hexdigest()}')
# K19 (todas as partes) e K19b (só D5 e D1, as que passaram da memória na rodada de 03/11, 19h29)
for arquivo, nome, partes, duracao in (('K19_auditoria_profunda_SAB.py', 'K19 v4', "('D2', 'D4', 'D5', 'D6', 'D1')", '180'),
                                       ('K19b_auditoria_D5_D1.py', 'K19b', "('D5', 'D1')", '90')):
    txt = mod.replace('<<NOME>>', nome).replace('<<PARTES>>', partes).replace('<<DURACAO>>', duracao)
    assert not any(m in txt for m in ('<<NOME>>', '<<PARTES>>', '<<DURACAO>>', '<<CARGA>>')), arquivo
    saida = os.path.join(RAIZ, 'validacoes', arquivo)
    open(saida, 'w', encoding='utf-8').write(txt)
    compile(txt, saida, 'exec')
    print(f'{nome} montada:', os.path.normpath(saida), f'({txt.count(chr(10))} linhas)')
