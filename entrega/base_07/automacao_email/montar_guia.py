# Monta o guia (HTML) embutindo os códigos atuais, com a impressão digital de cada um.
import hashlib, html, os, re
A = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(A, '..')
ARQ = {
 'pedido_sab.yml': ('sab_pedidos/.github/workflows/pedido_sab.yml', 'sab-pedidos · .github/workflows/'),
 'converter_xlsx.yml': ('sab_pedidos/.github/workflows/converter_xlsx.yml', 'sab-pedidos · .github/workflows/ (novo)'),
 'municipios.yml': ('sab_pedidos/.github/workflows/municipios.yml', 'sab-pedidos · .github/workflows/ (novo)'),
 'colab_credencial.py': ('colab_credencial.py', 'célula do Colab, rodar sozinha'),
 'texto_lgpd.txt': ('texto_lgpd.txt', 'descrição da pergunta Consentimento'),
 'Codigo.gs': ('apps_script/Codigo.gs', 'Apps Script da planilha'),
 'appsscript.json': ('apps_script/appsscript.json', 'manifesto do Apps Script'),
 'K16_validacao_identidade_email.py': ('../validacoes/K16_validacao_identidade_email.py', 'célula única do Colab; inclui a rotina sab_pedido.py'),
 'K17_validacao_final_SAB.py': ('../validacoes/K17_validacao_final_SAB.py', 'célula única do Colab; só leitura; inclui os códigos V1.0, V1.3, V1.5, O2 e O4'),
 'K18_auditoria_era5_e_pixels_b.py': ('../validacoes/K18_auditoria_era5_e_pixels_b.py', 'célula única do Colab; só leitura'),
 'K19_auditoria_profunda_SAB.py': ('../validacoes/K19_auditoria_profunda_SAB.py', 'célula única do Colab; só leitura; inclui os motores V1.0 e V1.5'),
 'K19b_auditoria_D5_D1.py': ('../validacoes/K19b_auditoria_D5_D1.py', 'célula única do Colab; só leitura; só D5 e D1'),
 'K20_validacao_correcao_pixels_b.py': ('../validacoes/K20_validacao_correcao_pixels_b.py', 'célula única do Colab; só leitura; inclui a rotina sab_pedido.py 2026.11.03'),
 'sab_pedido.py': ('sab_pedidos/sab_pedido.py', 'sab-pedidos · raiz'),
 'sab_xlsx.py': ('sab_pedidos/sab_xlsx.py', 'sab-pedidos · raiz (novo)'),
 'listar_municipios.py': ('sab_pedidos/listar_municipios.py', 'sab-pedidos · raiz (novo)'),
 'requirements.txt': ('sab_pedidos/requirements.txt', 'sab-pedidos · raiz'),
 'README.md': ('sab_pedidos/README.md', 'sab-pedidos · raiz'),
 'teste_sab_pedido.py': ('sab_pedidos/testes/teste_sab_pedido.py', 'sab-pedidos · testes/ (roda antes de cada pedido)'),
 'teste_sab_xlsx.py': ('sab_pedidos/testes/teste_sab_xlsx.py', 'sab-pedidos · testes/ (novo; roda antes de cada conversão)'),
 'fumaca_sab_pedido.py': ('sab_pedidos/testes/fumaca_sab_pedido.py', 'sab-pedidos · testes/ (só conferência local)'),
 'motor_05b.yml': ('../automacao_motor/sab-motor/.github/workflows/motor_05b.yml', 'sab-motor · .github/workflows/'),
 'rodar_motor.py': ('../automacao_motor/sab-motor/rodar_motor.py', 'sab-motor · raiz'),
 'SHA256_MOTOR.txt': ('../automacao_motor/sab-motor/SHA256_MOTOR.txt', 'sab-motor · raiz'),
 'requirements.txt (sab-motor)': ('../automacao_motor/sab-motor/requirements.txt', 'sab-motor · raiz, nome requirements.txt'),
 'README.md (sab-motor)': ('../automacao_motor/sab-motor/README.md', 'sab-motor · raiz, nome README.md'),
 'ATIVIDADE.md': ('../automacao_motor/sab-motor/ATIVIDADE.md', 'sab-motor · raiz'),
 'teste_rodar_motor.py': ('../automacao_motor/sab-motor/testes/teste_rodar_motor.py', 'sab-motor · testes/'),
 '05b_motor_sab_v1_5_GRAVACAO.py': ('../automacao_motor/sab-motor/05b_motor_sab_v1_5_GRAVACAO.py', 'sab-motor · raiz (upload; sem mudança)'),
 '05a_motor_sab_v1_5_SIMULACAO.py': ('../automacao_motor/sab-motor/05a_motor_sab_v1_5_SIMULACAO.py', 'sab-motor · raiz (upload; sem mudança)'),
 'K21_validacao_v16_fora_da_amostra.py': ('../validacoes/K21_validacao_v16_fora_da_amostra.py', 'célula única do Colab; só leitura; etapa 2, passo E2-1'),
 'K22_conferencia_v16.py': ('../validacoes/K22_conferencia_v16.py', 'célula única do Colab; só leitura; etapa 2, passo E2-6'),
 'K23_auditoria_emenda_tmax.py': ('../validacoes/K23_auditoria_emenda_tmax.py', 'célula única do Colab; só leitura; etapa 2, passo E2-4b'),
 'K24_auditoria_tmax_gfs.py': ('../validacoes/K24_auditoria_tmax_gfs.py', 'célula única do Colab; só leitura; etapa 2, passo E2-5c (ponto quente da Tmax do GFS)'),
 '09a_matriz_eqm_SIMULACAO.py': ('../09a_matriz_eqm_SIMULACAO.py', 'célula única do Colab; simulação; etapa 2, passo E2-2'),
 '09b_matriz_eqm_GRAVACAO.py': ('../09b_matriz_eqm_GRAVACAO.py', 'célula única do Colab; GRAVA a matriz nova; etapa 2, passo E2-3'),
 '06_painel_sab_2026_11_5_PRONTO.js': ('../06_painel_sab_2026_11_5_PRONTO.js', 'Code Editor do Earth Engine · painel completo'),
}
modelo = open(os.path.join(A, 'guia_modelo.html'), encoding='utf-8').read()
shas = []
def bloco(nome):
    rel, info = ARQ[nome]
    txt = open(os.path.join(A, rel), encoding='utf-8').read()
    n = txt.count('\n') + (0 if txt.endswith('\n') else 1)
    sha = hashlib.sha256(txt.encode('utf-8')).hexdigest()
    shas.append(f'<code>{nome}</code> {sha[:16]}…')
    ident = 'c_' + re.sub(r'[^a-z0-9]', '_', nome.lower()) + f'_{len(shas)}'
    aberto = ' open' if n <= 45 else ''
    cls = ' class="curto"' if n <= 45 else ''
    return (f'<details class="cod"{aberto}><summary><span class="nome">{html.escape(nome)}</span>'
            f'<span class="info">{html.escape(info)} · {n} linhas</span></summary>'
            f'<div class="barra"><button class="copiar" type="button" data-alvo="{ident}">Copiar</button></div>'
            f'<pre id="{ident}"{cls}>{html.escape(txt)}</pre></details>')
saida = re.sub(r'\{\{COD:([^}]+)\}\}', lambda m: bloco(m.group(1)), modelo)
saida = saida.replace('{{SHAS}}', ' · '.join(dict.fromkeys(shas)))
destino = os.path.join(A, 'Guia_Envio_Email_SAB.html')
open(destino, 'w', encoding='utf-8').write(saida)
print(destino, len(saida) // 1024, 'KB')
