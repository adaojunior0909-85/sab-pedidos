# Monta os arquivos da etapa 2 a partir dos modelos desta pasta:
#   09a/09b (matriz EQM), validacoes/K21 (validação fora da amostra) e validacoes/K22 (conferência depois de implantar).
import os
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, '..')
mod = open(os.path.join(AQUI, 'matriz_eqm_modelo.py'), encoding='utf-8').read()
for arq, tit, sim in (('09a_matriz_eqm_SIMULACAO.py', 'matriz EQM em SIMULAÇÃO (não grava nada).', 'True'),
                      ('09b_matriz_eqm_GRAVACAO.py', 'matriz EQM GRAVANDO (só depois do 09a sem ❌).', 'False')):
    txt = mod.replace('<<TITULO>>', tit).replace('<<SIMULAR>>', sim)
    assert '<<' not in txt.split('\n', 1)[1], arq
    compile(txt, arq, 'exec')
    open(os.path.join(RAIZ, arq), 'w', encoding='utf-8').write(txt)
    print('montado:', arq)
for modelo, saida in (('k21_modelo.py', 'K21_validacao_v16_fora_da_amostra.py'),
                      ('k22_modelo.py', 'K22_conferencia_v16.py')):
    p = os.path.join(AQUI, modelo)
    if not os.path.exists(p):
        continue
    txt = open(p, encoding='utf-8').read()
    compile(txt, saida, 'exec')
    open(os.path.join(RAIZ, 'validacoes', saida), 'w', encoding='utf-8').write(txt)
    print('montado:', saida)
