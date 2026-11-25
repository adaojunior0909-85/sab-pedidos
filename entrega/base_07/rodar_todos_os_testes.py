# >>> SAB: roda TODOS os testes offline do pacote (sem Earth Engine, sem Drive, sem rede) e grava o relatório. <<<
# Para quê: antes de trocar qualquer código, e depois, provar que nada quebrou. Os testes não gravam nada fora
# de pastas temporárias.
# Como rodar (no seu computador ou no Colab, a partir desta pasta):
#     python3 rodar_todos_os_testes.py
# Precisa de: Python 3.10+ com numpy, pandas, xlsxwriter e openpyxl; Node.js 18+ (testes .js).
#   No Colab:  !pip install -q xlsxwriter openpyxl   (o resto já vem instalado)
# Saída: RELATORIO_TESTES.md nesta pasta (um teste por linha: OK/FALHA, tempo e a última linha da saída).
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))

# (grupo, comando, pasta de trabalho). A ordem segue o fluxo do sistema.
TESTES = [
    ('01 máscara de qualidade', [sys.executable, 'testes/teste_01.py'], ''),
    ('01 máscara de qualidade', [sys.executable, 'testes/teste_01_uniao.py'], ''),
    ('02 RONI oficial do CPC', [sys.executable, 'testes/teste_02.py'], ''),
    ('02 RONI oficial do CPC', [sys.executable, 'testes/teste_02_troca.py'], ''),
    ('03/04 matriz GFS', [sys.executable, 'testes/teste_03.py'], ''),
    ('03/04 matriz GFS', ['node', 'testes/teste_04.js'], ''),
    ('05 motor V1.5', [sys.executable, 'testes/teste_05.py'], ''),
    ('05 motor V1.6', [sys.executable, 'testes/teste_05_v16.py'], ''),
    ('09 matriz EQM', [sys.executable, 'modelos_e2/montar_e2.py'], ''),
    ('09 matriz EQM', [sys.executable, 'testes/teste_09.py'], ''),
    ('06 painel', ['node', 'testes/teste_06_enso.js'], ''),
    ('06 painel', ['node', 'testes/teste_06_colunas.js'], ''),
    ('06 painel', ['node', 'testes/teste_06_numeros.js'], ''),
    ('06 painel', ['node', 'testes/teste_06_pedido_email.js'], ''),
    ('06 painel', [sys.executable, 'testes/teste_06_pedido_email.py'], ''),
    ('06 painel', [sys.executable, 'testes/teste_06_2026_11_2.py'], ''),
    ('06 painel', ['node', 'testes/teste_06_2026_11_3.js'], ''),
    ('06 painel', [sys.executable, 'testes/teste_06_2026_11_4.py'], ''),
    ('06 painel', [sys.executable, 'testes/teste_06_2026_11_5.py'], ''),
    ('06 painel', [sys.executable, 'montar_painel_pronto.py'], ''),
    ('06 painel', [sys.executable, 'testes/teste_06_pronto.py'], ''),
    ('07 normais', [sys.executable, 'testes/teste_07.py'], ''),
    ('08 auditoria', [sys.executable, 'testes/teste_08.py'], ''),
    ('08 auditoria', [sys.executable, 'testes/fumaca_08_01.py'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/teste_k11.py'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/teste_k12.py'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/teste_k13.py'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/fumaca_k13.py'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/teste_k14.py'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/fumaca_k14.py'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/teste_k15.py'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/fumaca_k15.py'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/teste_k16.py'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/fumaca_k16.py'], ''),
    ('Validações K11 a K16', ['node', 'testes/teste_k16_painel_node.js'], ''),
    ('Validações K11 a K16', [sys.executable, 'testes/fumaca_k16_parte_p.py'], ''),
    ('K17 validação final', [sys.executable, 'automacao_email/montar_k17.py'], ''),
    ('K17 validação final', [sys.executable, 'testes/teste_k17.py'], ''),
    ('K17 validação final', [sys.executable, 'testes/fumaca_k17.py'], ''),
    ('K18 ERA5 e pixels B', [sys.executable, 'testes/teste_k18.py'], ''),
    ('K19 auditoria profunda', [sys.executable, 'automacao_email/montar_k19.py'], ''),
    ('K19 auditoria profunda', [sys.executable, 'testes/teste_k19.py'], ''),
    ('K20 correção dos pixels B', [sys.executable, 'automacao_email/montar_k20.py'], ''),
    ('K20 correção dos pixels B', [sys.executable, 'testes/teste_k20.py'], ''),
    ('K20 correção dos pixels B', [sys.executable, 'testes/teste_correcao_b_identica.py'], ''),
    ('K21 e K22 motor V1.6', [sys.executable, 'testes/teste_k21.py'], ''),
    ('K21 e K22 motor V1.6', [sys.executable, 'testes/teste_k22.py'], ''),
    ('K21 e K22 motor V1.6', [sys.executable, 'testes/teste_k23.py'], ''),
    ('K21 e K22 motor V1.6', [sys.executable, 'testes/teste_k24.py'], ''),
    ('K26 auditoria final', [sys.executable, 'testes/teste_k26.py'], ''),
    ('GitHub sab-pedidos', [sys.executable, 'testes/teste_sab_pedido.py'], 'automacao_email/sab_pedidos'),
    ('GitHub sab-pedidos', [sys.executable, 'testes/teste_sab_xlsx.py'], 'automacao_email/sab_pedidos'),
    ('GitHub sab-pedidos', [sys.executable, 'testes/fumaca_sab_pedido.py'], 'automacao_email/sab_pedidos'),
    ('GitHub sab-motor', [sys.executable, 'testes/teste_rodar_motor.py'], 'automacao_motor/sab-motor'),
    ('Apps Script', ['node', 'apps_script/teste_codigo_gs.js'], 'automacao_email'),
    ('Apps Script', ['node', 'apps_script/teste_formulario_gs.js'], 'automacao_email'),
    ('Apps Script', ['node', 'testes/teste_limite.js'], 'automacao_email/apps_script'),
    ('Scripts originais (registro)', [sys.executable, 'montar_originais.py'], 'originais_somente_registro'),
]


def rodar(cmd, pasta):
    cwd = os.path.join(AQUI, pasta) if pasta else AQUI
    if cmd[0] == 'node' and not shutil.which('node'):
        return None, 0.0, 'Node.js não instalado'
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=900,
                           env=dict(os.environ, PYTHONIOENCODING='utf-8', MPLBACKEND='Agg'))
        saida = (r.stdout + r.stderr).strip().splitlines()
        ultima = next((l for l in reversed(saida) if l.strip()), '')
        return r.returncode == 0, time.time() - t0, ultima.strip()[:160]
    except subprocess.TimeoutExpired:
        return False, time.time() - t0, 'passou de 15 minutos'


if __name__ == '__main__':
    linhas, ok, falhas, pulados = [], 0, 0, 0
    print(f'SAB: {len(TESTES)} testes offline\n')
    for grupo, cmd, pasta in TESTES:
        nome = os.path.join(pasta, cmd[-1]) if pasta else cmd[-1]
        res, seg, ultima = rodar(cmd, pasta)
        marca = '⏭️ PULADO' if res is None else ('✅ OK' if res else '❌ FALHA')
        ok += res is True
        falhas += res is False
        pulados += res is None
        print(f'{marca:10} {seg:6.1f} s  {nome}  | {ultima}', flush=True)
        linhas.append(f'| {grupo} | `{nome}` | {marca} | {seg:.1f} s | {ultima.replace("|", "/")} |')
    rel = os.path.join(AQUI, 'RELATORIO_TESTES.md')
    with open(rel, 'w', encoding='utf-8') as f:
        f.write(f'# Relatório dos testes offline do SAB ({datetime.now(timezone(timedelta(hours=-3))):%d/%m/%Y %H:%M}, Brasília)\n\n')
        f.write(f'**{ok} OK, {falhas} falha(s), {pulados} pulado(s)** de {len(TESTES)}. '
                f'Python {sys.version.split()[0]}; Node {"sim" if shutil.which("node") else "não"}.\n\n')
        f.write('| Grupo | Teste | Resultado | Tempo | Última linha da saída |\n|---|---|---|---|---|\n')
        f.write('\n'.join(linhas) + '\n')
    print(f'\n{ok} OK, {falhas} falha(s), {pulados} pulado(s). Relatório: {rel}')
    sys.exit(1 if falhas else 0)
