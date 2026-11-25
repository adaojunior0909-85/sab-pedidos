# >>> SAB: separa os scripts ORIGINAIS recebidos em 03/11/2026, um por asset, com trava "NÃO EXECUTAR". <<<
# Rodar a partir desta pasta:  python3 montar_originais.py
# Entrada (como recebido, sem mudança): recebidos_03-11-2026/scripts_originais_recebidos.txt (5 scripts colados em
#   sequência) e recebidos_03-11-2026/codigo1_roni_recebido.py ("Código 1" do RONI).
# Saída: um arquivo .py por script. Antes do texto original vão (1) um cabeçalho que diz qual asset ele gerou,
#   por que não deve ser rodado e o SHA-256 do trecho original, e (2) a linha  raise SystemExit(...): se alguém
#   colar no Colab por engano, a célula para ANTES de qualquer import ou gravação. O texto original vem depois,
#   byte a byte; o teste no fim confere que o arquivo menos o cabeçalho é idêntico ao trecho recebido.
import hashlib
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(AQUI, 'recebidos_03-11-2026')
TXT = open(os.path.join(REC, 'scripts_originais_recebidos.txt'), encoding='utf-8').read().split('\n')

# (arquivo, linha inicial, linha final (inclusive, 1 = primeira), asset gerado, papel hoje, substituído por)
TRECHOS = [
    ('O1_motor_mestre_V1_3_SAB_V1.py', 1, 1331, 'SAB_V1 (dias provisórios e previsão de 2026, até a troca pela V1.5) e '
     'SAB_V1_TMP. NÃO gravou o histórico 1961–2025: esse é da V1.0 (O0_motor_mestre_V1_0_SAB_V1_historico.py); '
     'conferido no Earth Engine em 03/11/2026 (23.741 dias só com versao = definitiva, sem versao_algoritmo)',
     'Histórico 1961–2025 travado (PROTEGER_HISTORICO, DATA_LIMITE_PROTECAO = 2025-12-31).',
     '05a/05b_motor_sab_v1_5 (V1.5) para 2026 em diante; o histórico não é mais regravado'),
    ('O2_climatologia_SICSB_1986_2025.py', 1333, 1469, 'SICSB_1986_2025 (12 imagens Matriz_Clima_MM)',
     'Em uso, só leitura: calibração BR-DWGD × ERA5-Land dos dias provisórios (motor V1.5).', 'não substituído'),
    ('O3_matriz_GFS_V1_SICSB_MATRIZ_GFS.py', 1471, 1662, 'SICSB_MATRIZ_GFS (V1)',
     'Sem uso: referência da 04 e da 08 (comparação com a V2.1).', '03_matriz_gfs_v2_1.py (SICSB_MATRIZ_GFS_V2)'),
    ('O4_solo_SICSB_SOLO_2015_2025.py', 1664, 1801, 'SICSB_SOLO_2015_2025 (12 imagens Matriz_Solo_MM)',
     'Em uso, só leitura: fator SMAP/ERA5 da umidade do solo (motor V1.5 e correção de leitura do painel).',
     'não substituído'),
    ('O5_baselines_normais_B1_1.py', 1803, None, 'Baselines (48 imagens B1.1: normais e limiares 1961–1990 e 1991–2020)',
     'Em uso, só leitura. É o "Código baselines.txt": NUNCA rodar. A conferência é pelo 07a/07b (mesmo cálculo, travado).',
     '07a/07b_normais_CONFERIR (só conferem)'),
]


# Segundo envio (03/11/2026): células do Colab de 04 e 05/10/2026 (V1.0 e V1.1). As outras 3 células do mesmo arquivo
# (exclusão de dias GFS provisórios e duas extrações de conferência do GFS) ficam só no arquivo recebido.
TRECHOS_2 = [
    ('O0_motor_mestre_V1_0_SAB_V1_historico.py', 4, 809,
     'SAB_V1, histórico 1961–2025 (os 23.741 dias). Prova: este código grava SÓ a propriedade versao = definitiva '
     '(sem versao_algoritmo), exatamente o que o Earth Engine mostrou em 03/11/2026, e calibra o solo sem teto (o que '
     'explica a umidade de até 0,9989 nos dias antigos). Texto de 05/10/2026; o histórico foi gravado entre 24/08 e '
     '26/09/2026 (data de atualização de cada dia no asset). K17 v3 (03/11/2026): este código, rodado hoje, '
     'reproduz o gravado em todas as 16 bandas e classes de 1961 a 2013; em 2020 e 2025 só diferem as variáveis '
     'acumuladas do ERA5-Land, revistas na fonte depois da gravação',
     'Histórico travado; a correção de solo e escoamento é feita na leitura (painel e e-mail).',
     'V1.1 → V1.2 → V1.3 → 05a/05b V1.5 (2026 em diante)'),
    ('O0b_motor_mestre_V1_1.py', 923, 1781,
     'nenhum dia do histórico (conferido: 0 dias com versao_algoritmo); pode ter gravado dias provisórios de 2026, '
     'já recalculados pelas versões seguintes',
     'Sem efeito no banco hoje. Registro da evolução do motor.', 'V1.2 e V1.3 (O1) e depois V1.5'),
]


def cabecalho(asset, papel, subst, sha, origem):
    return (
        '# ⛔⛔⛔ NÃO EXECUTAR: SCRIPT ORIGINAL GUARDADO SÓ COMO REGISTRO DO MÉTODO (metodologia da tese) ⛔⛔⛔\n'
        f'# Gerou: projects/clima-492922/assets/{asset}\n'
        f'# Hoje: {papel}\n'
        f'# Substituído por: {subst}\n'
        '# Por que não rodar: ele RECRIARIA o asset acima; o banco, as calibrações e as validações (K8 a K16, 07a/07b,\n'
        '#   08) foram aprovados com o asset que já existe. Rodar de novo exigiria refazer e validar tudo.\n'
        f'# Recebido do responsável em 03/11/2026 ({origem}). Abaixo da linha ORIGINAL, o texto está sem nenhuma\n'
        f'#   mudança. SHA-256 do trecho original: {sha}\n'
        '# A linha raise SystemExit abaixo faz a célula parar antes de qualquer import ou gravação.\n'
        "raise SystemExit('⛔ Script original guardado só como registro. NÃO EXECUTAR (veja o cabeçalho).')\n"
        '# ================================================ ORIGINAL ================================================\n')


def gerar():
    feitos = []
    for nome, ini, fim, asset, papel, subst in TRECHOS:
        trecho = '\n'.join(TXT[ini - 1:fim] if fim else TXT[ini - 1:]).rstrip('\n') + '\n'
        sha = hashlib.sha256(trecho.encode('utf-8')).hexdigest()
        cab = cabecalho(asset, papel, subst, sha, f'scripts_originais_recebidos.txt, linhas {ini} a {fim or len(TXT)}')
        open(os.path.join(AQUI, nome), 'w', encoding='utf-8').write(cab + trecho)
        feitos.append((nome, asset, sha, cab, trecho))
    # [03/11/2026, 2º envio] motores V1.0 e V1.1 (células do Colab, sem as linhas de marcação e sem as saídas)
    txt2 = open(os.path.join(REC, 'motores_V1_0_V1_1_e_utilitarios_recebidos.txt'), encoding='utf-8').read().split('\n')
    for nome, ini, fim, asset, papel, subst in TRECHOS_2:
        trecho = '\n'.join(txt2[ini - 1:fim]).rstrip('\n') + '\n'
        sha = hashlib.sha256(trecho.encode('utf-8')).hexdigest()
        cab = cabecalho(asset, papel, subst, sha,
                        f'motores_V1_0_V1_1_e_utilitarios_recebidos.txt, linhas {ini} a {fim}')
        open(os.path.join(AQUI, nome), 'w', encoding='utf-8').write(cab + trecho)
        feitos.append((nome, asset, sha, cab, trecho))
    cod1 = open(os.path.join(REC, 'codigo1_roni_recebido.py'), encoding='utf-8').read()
    sha = hashlib.sha256(cod1.encode('utf-8')).hexdigest()
    cab = cabecalho('RONI_Calibrado_Sazonal_1950_1980. ATENÇÃO: este código LÊ esse asset e grava o CSV '
                    'RONI_Calibrado_Sazonal_1950_2026.csv; o conteúdo do asset veio do upload manual desse CSV',
                    'Sem uso: o painel e o e-mail leem o RONI_CPC_v6; a 08 (H4) ainda compara com ele.',
                    '02_auditoria_roni_cpc.py (RONI_CPC_v6, oficial do CPC)', sha, 'codigo1_roni_recebido.py, "Código 1"')
    open(os.path.join(AQUI, 'O6_codigo1_RONI_Calibrado_Sazonal.py'), 'w', encoding='utf-8').write(cab + cod1)
    feitos.append(('O6_codigo1_RONI_Calibrado_Sazonal.py', 'RONI_Calibrado_Sazonal_1950_1980', sha, cab, cod1))
    return feitos


if __name__ == '__main__':
    import ast
    for nome, asset, sha, cab, trecho in gerar():
        txt = open(os.path.join(AQUI, nome), encoding='utf-8').read()
        assert txt[len(cab):] == trecho, nome                                   # original intacto
        arv = ast.parse(txt)                                                    # Python válido
        primeiro = arv.body[0]
        assert isinstance(primeiro, ast.Raise), nome                            # a trava é a 1ª instrução
        print(f'✅ {nome:42} {asset[:48]:48} SHA {sha[:16]}')
