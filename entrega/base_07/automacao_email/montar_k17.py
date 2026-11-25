# Monta validacoes/K17_validacao_final_SAB.py embutindo, sem mudança, os códigos que gravaram os dados:
# V1.0 (O0), V1.3 (O1), V1.5 (05b) e as matrizes SICSB_1986_2025 (O2) e SICSB_SOLO_2015_2025 (O4).
import hashlib
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, '..')
ORIG = os.path.join(RAIZ, 'originais_somente_registro')
MARCA = '# ================================================ ORIGINAL ================================================\n'


def original(nome):
    """Texto do script original, sem o cabeçalho e sem a trava (o que vem depois da linha ORIGINAL)."""
    txt = open(os.path.join(ORIG, nome), encoding='utf-8').read()
    assert txt.count(MARCA) == 1, nome
    return txt.split(MARCA, 1)[1]


fontes = {
    '<<V10>>': original('O0_motor_mestre_V1_0_SAB_V1_historico.py'),
    '<<V13>>': original('O1_motor_mestre_V1_3_SAB_V1.py'),
    '<<V15>>': open(os.path.join(RAIZ, '05b_motor_sab_v1_5_GRAVACAO.py'), encoding='utf-8').read(),
    '<<CLIMA>>': original('O2_climatologia_SICSB_1986_2025.py'),
    '<<SOLO>>': original('O4_solo_SICSB_SOLO_2015_2025.py'),
}
mod = open(os.path.join(AQUI, 'k17_modelo.py'), encoding='utf-8').read()
for marca, src in fontes.items():
    assert "'''" not in src and not src.endswith('\\'), marca
    assert mod.count(marca) == 1, marca
    mod = mod.replace(marca, src)
saida = os.path.join(RAIZ, 'validacoes', 'K17_validacao_final_SAB.py')
open(saida, 'w', encoding='utf-8').write(mod)
for marca, src in fontes.items():
    print(f'{marca:10} SHA-256 {hashlib.sha256(src.encode("utf-8")).hexdigest()}')
print('K17 montada:', os.path.normpath(saida))
