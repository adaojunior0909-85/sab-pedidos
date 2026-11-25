# >>> SAB: monta a ENTREGA FINAL organizada por destino (onde cada arquivo é colado ou enviado). <<<
# Rodar a partir desta pasta:  python3 montar_entrega.py
# O que faz: copia, SEM MUDAR NENHUM BYTE, cada arquivo atual para a pasta do serviço onde ele vai (Code Editor,
# Colab, GitHub, Apps Script), escreve o índice 00_LEIA_PRIMEIRO.md (com a impressão digital SHA-256 de cada
# arquivo), junta o guia clique a clique e uma cópia completa da base de desenvolvimento (com os testes), e fecha
# tudo num zip. No fim confere que cada cópia tem o mesmo SHA-256 do original.
import hashlib
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
BRT = timezone(timedelta(hours=-3))   # [24/11/2026] hora de Brasília: o computador da sessão está em UTC
DATA = datetime.now(BRT).strftime('%Y-%m-%d')
NOME = f'SAB_entrega_final_{DATA}'
SAIDA = os.path.join(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(AQUI), NOME)

# (origem na base v41, destino na entrega, versão, onde roda, quando)
ARQUIVOS = [
    # ---- Earth Engine: Code Editor
    ('06_painel_sab_2026_11_5_PRONTO.js', '01_Earth_Engine_Code_Editor/06_painel_sab_2026_11_5_PRONTO.js', '2026.11.5',
     'Code Editor: script SAB_painel_2026_10_6 (Ctrl+A, colar) → app adao-alves-rodrigues-junior-sab',
     'NO AR desde 24/11/2026 (K16 v7.1 aprovada em 22/11, 22h40; PR #7 juntado em 23/11)'),
    ('04_conferencia_matriz_gfs.js', '01_Earth_Engine_Code_Editor/04_conferencia_matriz_gfs.js', 'V4',
     'Code Editor (só leitura)', 'só se a matriz GFS for refeita'),
    # ---- Colab: banco
    ('01a_mascara_qualidade_SIMULACAO.py', '02_Colab/banco/01a_mascara_qualidade_SIMULACAO.py', 'Q1 v4.1',
     'Colab (simulação)', 'feito; só se a máscara for refeita'),
    ('01b_mascara_qualidade_GRAVACAO.py', '02_Colab/banco/01b_mascara_qualidade_GRAVACAO.py', 'Q1 v4.1',
     'Colab (GRAVA o asset)', 'feito; só depois do 01a sem ❌'),
    ('02_auditoria_roni_cpc.py', '02_Colab/banco/02_auditoria_roni_cpc.py', 'V4',
     'Colab (GRAVA RONI_CPC_v6)', 'todo mês, depois do dia 10'),
    ('03_matriz_gfs_v2_1.py', '02_Colab/banco/03_matriz_gfs_v2_1.py', 'V2.1',
     'Colab (GRAVA a matriz)', 'feito; só se a calibração do GFS for refeita'),
    ('09a_matriz_eqm_SIMULACAO.py', '02_Colab/banco/09a_matriz_eqm_SIMULACAO.py', 'E1',
     'Colab (simulação)', 'etapa 2, passo E2-2'),
    ('09b_matriz_eqm_GRAVACAO.py', '02_Colab/banco/09b_matriz_eqm_GRAVACAO.py', 'E1',
     'Colab (GRAVA a matriz SICSB_EQM_1986_2025, asset novo)', 'etapa 2, passo E2-3, só depois do 09a sem ❌'),
    ('05a_motor_sab_v1_6_SIMULACAO.py', '02_Colab/banco/05a_motor_sab_v1_6_SIMULACAO.py', 'V1.6',
     'Colab (simulação)', 'etapa 2, passo E2-4; antes de qualquer mudança no motor'),
    ('05b_motor_sab_v1_6_GRAVACAO.py', '02_Colab/banco/05b_motor_sab_v1_6_GRAVACAO.py', 'V1.6',
     'GitHub sab-motor (automático 23h07, depois do E2-5)', 'automático; no Colab só se o GitHub parar'),
    ('07a_normais_CONFERIR_1991_2020.py', '02_Colab/banco/07a_normais_CONFERIR_1991_2020.py', 'B1.1a',
     'Colab (só leitura)', 'auditoria das normais'),
    ('07b_normais_CONFERIR_1961_1990.py', '02_Colab/banco/07b_normais_CONFERIR_1961_1990.py', 'B1.1a',
     'Colab (só leitura)', 'auditoria das normais'),
    ('08_auditoria_completa_SAB.py', '02_Colab/banco/08_auditoria_completa_SAB.py', 'A3 / 22-10',
     'Colab (só leitura)', 'a cada 3 meses ou depois de mudança'),
    # ---- Colab: envio por e-mail e validações
    ('automacao_email/colab_credencial.py', '02_Colab/envio_email/colab_credencial.py', 'v3',
     'Colab (gera o segredo EE_CREDENCIAL)', 'só se a credencial for revogada'),
    ('validacoes/K16_validacao_identidade_email.py', '02_Colab/validacoes/K16_validacao_identidade_email.py', 'K16 v7.1',
     'Colab', 'APROVADA em 22/11/2026 22h40 (rotina 2026.11.22 x painel 2026.11.5); repetir sempre que o cálculo mudar'),
    ('validacoes/K17_validacao_final_SAB.py', '02_Colab/validacoes/K17_validacao_final_SAB.py', 'K17',
     'Colab (só leitura)', 'validação final; depois, uma vez por ano ou depois de mudança no motor'),
    ('validacoes/K18_auditoria_era5_e_pixels_b.py', '02_Colab/validacoes/K18_auditoria_era5_e_pixels_b.py', 'K18',
     'Colab (só leitura)', 'uma vez: mede a revisão do ERA5 e a correção dos pixels B antes de decidir'),
    ('validacoes/K19_auditoria_profunda_SAB.py', '02_Colab/validacoes/K19_auditoria_profunda_SAB.py', 'K19',
     'Colab (só leitura, 1h30 a 3h)', 'auditoria profunda: QC de todos os dias, ETo, emenda 2026, homogeneidade, reprodução'),
    ('validacoes/K19b_auditoria_D5_D1.py', '02_Colab/validacoes/K19b_auditoria_D5_D1.py', 'K19b',
     'Colab (só leitura, 40 a 90 min)', 'só D5 e D1 (as que passaram da memória na rodada de 03/11, 19h29)'),
    ('validacoes/K20_validacao_correcao_pixels_b.py', '02_Colab/validacoes/K20_validacao_correcao_pixels_b.py', 'K20',
     'Colab (só leitura, 10 a 25 min)', 'antes de implantar a correção dos pixels B (etapa 1)'),
    ('validacoes/K21_validacao_v16_fora_da_amostra.py', '02_Colab/validacoes/K21_validacao_v16_fora_da_amostra.py', 'K21 v4',
     'Colab (só leitura, ~30 min)', 'E2-1, APROVADA em 08/11: valida o motor V1.6 revisto (vento pela média) fora da amostra'),
    ('validacoes/K22_conferencia_v16.py', '02_Colab/validacoes/K22_conferencia_v16.py', 'K22 v2',
     'Colab (só leitura, 15 a 40 min)', 'feita em 24/11/2026: 1 e 3 OK, 2 com 1 pixel-dia (borda); etapa 2 encerrada'),
    ('validacoes/K23_auditoria_emenda_tmax.py', '02_Colab/validacoes/K23_auditoria_emenda_tmax.py', 'K23 v2',
     'Colab (só leitura, 15 a 30 min)', 'E2-4b, feito em 09/11: emenda normal; ponto quente do GFS em Roraima (vai para a K24)'),
    ('validacoes/K24_auditoria_tmax_gfs.py', '02_Colab/validacoes/K24_auditoria_tmax_gfs.py', 'K24 v1',
     'Colab (só leitura, 20 a 60 min)', 'feita em 24/11/2026: sem excesso sistemático; a V1.7 da Tmax não é necessária'),
    # [18/11/2026] K26 na raiz da entrega (o teste_k26.py a procura ali)
    ('validacoes/K26_auditoria_final.py', 'K26_auditoria_final.py', 'K26 v1.12',
     'Colab (só leitura; RODADAS_EM_SEQUENCIA)', 'FECHADA em 22/11/2026; de novo só a rodada 1 (2026) depois de meados de dezembro'),
    # ---- GitHub sab-pedidos (repositório privado): mesma árvore do repositório
    ('automacao_email/sab_pedidos/sab_pedido.py', '03_GitHub_sab-pedidos/sab_pedido.py', '2026.11.22',
     'GitHub sab-pedidos (evento pedido_sab)', 'automático, a cada pedido'),
    ('automacao_email/sab_pedidos/sab_xlsx.py', '03_GitHub_sab-pedidos/sab_xlsx.py', '2026.11.01',
     'GitHub sab-pedidos (evento converter_xlsx)', 'automático, pedidos com Excel'),
    ('automacao_email/sab_pedidos/listar_municipios.py', '03_GitHub_sab-pedidos/listar_municipios.py', '2026.11.01',
     'GitHub sab-pedidos (manual)', 'feito; só se o GAUL mudar'),
    ('automacao_email/sab_pedidos/requirements.txt', '03_GitHub_sab-pedidos/requirements.txt', '2026.11.15',
     'GitHub sab-pedidos', '-'),
    ('automacao_email/sab_pedidos/README.md', '03_GitHub_sab-pedidos/README.md', '2026.11.18', 'GitHub sab-pedidos', '-'),
    ('automacao_email/sab_pedidos/.github/workflows/pedido_sab.yml', '03_GitHub_sab-pedidos/.github/workflows/pedido_sab.yml',
     '2026.11.15', 'GitHub sab-pedidos', 'automático'),
    ('automacao_email/sab_pedidos/.github/workflows/converter_xlsx.yml',
     '03_GitHub_sab-pedidos/.github/workflows/converter_xlsx.yml', '2026.11.15', 'GitHub sab-pedidos', 'automático'),
    ('automacao_email/sab_pedidos/.github/workflows/municipios.yml', '03_GitHub_sab-pedidos/.github/workflows/municipios.yml',
     '2026.11.15', 'GitHub sab-pedidos', 'manual'),
    ('automacao_email/sab_pedidos/testes/teste_sab_pedido.py', '03_GitHub_sab-pedidos/testes/teste_sab_pedido.py',
     '2026.11.18', 'GitHub sab-pedidos (antes de cada pedido)', 'automático'),
    ('automacao_email/sab_pedidos/testes/teste_sab_xlsx.py', '03_GitHub_sab-pedidos/testes/teste_sab_xlsx.py',
     '2026.11.01', 'GitHub sab-pedidos (antes de cada conversão)', 'automático'),
    ('automacao_email/sab_pedidos/testes/fumaca_sab_pedido.py', '03_GitHub_sab-pedidos/testes/fumaca_sab_pedido.py',
     '2026.11.01', 'computador (conferência local)', '-'),
    # [18/11/2026] arquivos novos do sab-pedidos (o repositório inteiro, inclusive pesquisa/, é copiado no fim)
    ('automacao_email/sab_pedidos/testes/verificar_uma_variavel_ee.py', '03_GitHub_sab-pedidos/testes/verificar_uma_variavel_ee.py',
     '2026.11.18', 'GitHub sab-pedidos (workflow Verificar correcao uma variavel, à mão)', 'só leitura: as 19 variáveis sozinhas x "todas"'),
    ('automacao_email/sab_pedidos/.github/workflows/verificar_correcao.yml', '03_GitHub_sab-pedidos/.github/workflows/verificar_correcao.yml',
     '2026.11.18', 'GitHub sab-pedidos', 'manual'),
    ('automacao_email/sab_pedidos/.github/workflows/piloto_temperatura.yml', '03_GitHub_sab-pedidos/.github/workflows/piloto_temperatura.yml',
     '2026.11.18', 'GitHub sab-pedidos (piloto da previsão estendida)', 'automático: dias 3 e 17, 08h17'),
    ('automacao_email/sab_pedidos/.github/workflows/pesquisa_extrair.yml', '03_GitHub_sab-pedidos/.github/workflows/pesquisa_extrair.yml',
     '2026.11.18', 'GitHub sab-pedidos (pesquisa)', 'manual'),
    ('automacao_email/sab_pedidos/.github/workflows/pesquisa_k26.yml', '03_GitHub_sab-pedidos/.github/workflows/pesquisa_k26.yml',
     '2026.11.18', 'GitHub sab-pedidos (pesquisa)', 'manual'),
    ('automacao_email/sab_pedidos/pesquisa/piloto.py', '03_GitHub_sab-pedidos/pesquisa/piloto.py', '2026.11.18',
     'GitHub sab-pedidos (piloto, pelo workflow)', 'automático: dias 3 e 17'),
    ('automacao_email/sab_pedidos/pesquisa/hindcast.py', '03_GitHub_sab-pedidos/pesquisa/hindcast.py', 'rodada 2',
     'computador ou Colab (sem Earth Engine)', 'só para refazer a pesquisa'),
    # ---- GitHub sab-motor (repositório público)
    # [24/11/2026] V1.7 (radiação 0 do ERA5-Land vira vazio): etapa A = só a simulação; o 05b da V1.7 entra na etapa B
    ('automacao_motor/sab-motor/05a_motor_sab_v1_7_SIMULACAO.py', '04_GitHub_sab-motor/05a_motor_sab_v1_7_SIMULACAO.py',
     'V1.7', 'GitHub sab-motor (modo simular)', 'simulação aprovada em 24/11 (PR #3 do sab-motor)'),
    ('automacao_motor/sab-motor/05b_motor_sab_v1_7_GRAVACAO.py', '04_GitHub_sab-motor/05b_motor_sab_v1_7_GRAVACAO.py',
     'V1.7', 'GitHub sab-motor (modo gravar)', 'NO AR desde 24/11/2026 21h11 (PR #3 do sab-motor; simulação aprovada)'),
    ('automacao_motor/sab-motor/05a_motor_sab_v1_6_SIMULACAO.py', '04_GitHub_sab-motor/05a_motor_sab_v1_6_SIMULACAO.py',
     'V1.6', 'GitHub sab-motor (modo simular)', 'manual'),
    ('automacao_motor/sab-motor/05b_motor_sab_v1_6_GRAVACAO.py', '04_GitHub_sab-motor/05b_motor_sab_v1_6_GRAVACAO.py',
     'V1.6', 'GitHub sab-motor (modo gravar)', '23h07 (subir só no E2-5)'),
    ('automacao_motor/sab-motor/05a_motor_sab_v1_5_SIMULACAO.py', '04_GitHub_sab-motor/05a_motor_sab_v1_5_SIMULACAO.py',
     'V1.5', 'GitHub sab-motor (só para voltar atrás)', '-'),
    ('automacao_motor/sab-motor/05b_motor_sab_v1_5_GRAVACAO.py', '04_GitHub_sab-motor/05b_motor_sab_v1_5_GRAVACAO.py',
     'V1.5', 'GitHub sab-motor (só para voltar atrás)', '-'),
    ('automacao_motor/sab-motor/rodar_motor.py', '04_GitHub_sab-motor/rodar_motor.py', '2026.11.25',
     'GitHub sab-motor (lançador com travas: grava e simula a V1.7)', 'no ar desde 24/11/2026 21h11 (PR #3 do sab-motor)'),
    ('automacao_motor/sab-motor/SHA256_MOTOR.txt', '04_GitHub_sab-motor/SHA256_MOTOR.txt', 'V1.5, V1.6 e V1.7', 'GitHub sab-motor', '-'),
    ('automacao_motor/sab-motor/requirements.txt', '04_GitHub_sab-motor/requirements.txt', '2026.11.15', 'GitHub sab-motor', '-'),
    ('automacao_motor/sab-motor/README.md', '04_GitHub_sab-motor/README.md', '2026.11.08', 'GitHub sab-motor', 'subir no E2-5'),
    ('automacao_motor/sab-motor/ATIVIDADE.md', '04_GitHub_sab-motor/ATIVIDADE.md', 'automático',
     'GitHub sab-motor (o workflow atualiza todo mês)', 'automático'),
    ('automacao_motor/sab-motor/.github/workflows/motor_05b.yml', '04_GitHub_sab-motor/.github/workflows/motor_05b.yml',
     '2026.11.15', 'GitHub sab-motor', 'automático: 02:07 UTC = 23h07 de Brasília'),
    ('automacao_motor/sab-motor/testes/teste_rodar_motor.py', '04_GitHub_sab-motor/testes/teste_rodar_motor.py',
     '2026.11.01', 'GitHub sab-motor (antes de cada execução)', 'automático'),
    # ---- Apps Script da planilha de respostas
    ('automacao_email/apps_script/Codigo.gs', '05_Apps_Script/Codigo.gs', '2026.11.15',
     'Apps Script da planilha (+ App da Web)', 'no ar (implantação Versão 7, 15/11/2026 20h13; conferida em 24/11); automático (a cada resposta; 1 min com pedido ativo; 10 min de segurança)'),
    ('automacao_email/apps_script/appsscript.json', '05_Apps_Script/appsscript.json', '2026.11.01',
     'Apps Script (manifesto)', '-'),
    ('automacao_email/apps_script/testes/teste_limite.js', '05_Apps_Script/testes/teste_limite.js', '2026.11.15',
     'computador (node testes/teste_limite.js)', '-'),
    ('automacao_email/texto_lgpd.txt', '05_Apps_Script/texto_lgpd.txt', '2026.11.01',
     'Formulário (texto do consentimento)', '-'),
    # ---- Scripts originais que criaram os assets fixos: SÓ REGISTRO (trava raise SystemExit no topo)
    ('originais_somente_registro/O0_motor_mestre_V1_0_SAB_V1_historico.py', '08_Scripts_originais_somente_registro/O0_motor_mestre_V1_0_SAB_V1_historico.py', 'V1.0 (original)',
     'registro: SAB_V1 histórico 1961–2025', '⛔ NÃO EXECUTAR'),
    ('originais_somente_registro/O0b_motor_mestre_V1_1.py', '08_Scripts_originais_somente_registro/O0b_motor_mestre_V1_1.py', 'V1.1 (original)',
     'registro: evolução do motor', '⛔ NÃO EXECUTAR'),
    ('originais_somente_registro/O1_motor_mestre_V1_3_SAB_V1.py', '08_Scripts_originais_somente_registro/O1_motor_mestre_V1_3_SAB_V1.py', 'V1.3 (original)',
     'registro: SAB_V1 histórico e SAB_V1_TMP', '⛔ NÃO EXECUTAR'),
    ('originais_somente_registro/O2_climatologia_SICSB_1986_2025.py', '08_Scripts_originais_somente_registro/O2_climatologia_SICSB_1986_2025.py', 'original',
     'registro: SICSB_1986_2025', '⛔ NÃO EXECUTAR'),
    ('originais_somente_registro/O3_matriz_GFS_V1_SICSB_MATRIZ_GFS.py', '08_Scripts_originais_somente_registro/O3_matriz_GFS_V1_SICSB_MATRIZ_GFS.py', 'V1 (original)',
     'registro: SICSB_MATRIZ_GFS (V1)', '⛔ NÃO EXECUTAR'),
    ('originais_somente_registro/O4_solo_SICSB_SOLO_2015_2025.py', '08_Scripts_originais_somente_registro/O4_solo_SICSB_SOLO_2015_2025.py', 'original',
     'registro: SICSB_SOLO_2015_2025', '⛔ NÃO EXECUTAR'),
    ('originais_somente_registro/O5_baselines_normais_B1_1.py', '08_Scripts_originais_somente_registro/O5_baselines_normais_B1_1.py', 'B1.1 (original)',
     'registro: Baselines', '⛔ NÃO EXECUTAR'),
    ('originais_somente_registro/O6_codigo1_RONI_Calibrado_Sazonal.py', '08_Scripts_originais_somente_registro/O6_codigo1_RONI_Calibrado_Sazonal.py', '"Código 1" (original)',
     'registro: RONI_Calibrado_Sazonal_1950_1980', '⛔ NÃO EXECUTAR'),
    # ---- Guia e documentação
    ('automacao_email/Guia_Envio_Email_SAB.html', '06_Guia_clique_a_clique/Guia_Envio_Email_SAB.html', '22/11/2026',
     'navegador (abre com duplo clique)', '-'),
    ('RELATORIO_TESTES.md', '06_Guia_clique_a_clique/RELATORIO_TESTES.md', '18/11/2026', 'leitura', '-'),
]


def sha(caminho):
    h = hashlib.sha256()
    with open(caminho, 'rb') as f:
        for bloco in iter(lambda: f.read(1 << 20), b''):
            h.update(bloco)
    return h.hexdigest()


def copiar(origem, destino):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copy2(origem, destino)


if __name__ == '__main__':
    if os.path.exists(SAIDA):
        shutil.rmtree(SAIDA)
    linhas = []
    for orig, dest, versao, onde, quando in ARQUIVOS:
        o = os.path.join(AQUI, orig)
        d = os.path.join(SAIDA, dest)
        copiar(o, d)
        assert sha(o) == sha(d), dest
        linhas.append(f'| `{dest}` | {versao} | {onde} | {quando} | `{sha(o)[:16]}` |')
    # [18/11/2026] o repositório sab-pedidos inteiro (inclusive pesquisa/), não só os arquivos da tabela
    rep = os.path.join(AQUI, 'automacao_email', 'sab_pedidos')
    for raiz, pastas, nomes in os.walk(rep):
        pastas[:] = [x for x in pastas if x != '__pycache__']
        for n in nomes:
            o = os.path.join(raiz, n)
            d = os.path.join(SAIDA, '03_GitHub_sab-pedidos', os.path.relpath(o, rep))
            if not os.path.exists(d):
                copiar(o, d)
            assert sha(o) == sha(d), d
    # base de desenvolvimento completa, com os testes (a mesma pasta em que tudo foi feito e testado)
    base = os.path.join(SAIDA, '07_Base_de_desenvolvimento_e_testes')
    shutil.copytree(AQUI, base, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'SAB_entrega_final_*'))
    modelo = open(os.path.join(AQUI, 'LEIA_PRIMEIRO_modelo.md'), encoding='utf-8').read()
    indice = modelo.replace('{{DATA}}', datetime.now(BRT).strftime('%d/%m/%Y %H:%M') + ' (Brasília)').replace('{{TABELA}}', '\n'.join(linhas))
    open(os.path.join(SAIDA, '00_LEIA_PRIMEIRO.md'), 'w', encoding='utf-8').write(indice)
    # impressões digitais de tudo
    todas = []
    for raiz, _, nomes in os.walk(SAIDA):
        for n in sorted(nomes):
            c = os.path.join(raiz, n)
            todas.append(f'{sha(c)}  {os.path.relpath(c, SAIDA)}')
    open(os.path.join(SAIDA, 'SHA256SUMS.txt'), 'w', encoding='utf-8').write('\n'.join(sorted(todas, key=lambda x: x[66:])) + '\n')
    z = shutil.make_archive(SAIDA, 'zip', os.path.dirname(SAIDA), NOME)
    print(f'{len(ARQUIVOS)} arquivos de uso + base completa | {len(todas)} arquivos no total | {z}')
