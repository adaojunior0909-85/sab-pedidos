# FILA DA CONFERÊNCIA FINAL: roda sozinha, no GitHub, tudo o que falta para fechar a auditoria, uma tarefa atrás da
# outra, e guarda tudo no repositório (resultados, LOG de cada tarefa e rotinas/conferencia/CONFERENCIA_FINAL.md).
# O agendamento (rotina_conferencia.yml) chama esta fila de 2 em 2 horas; cada chamada pega as tarefas pendentes que
# podem rodar naquela hora e segue até acabar o tempo do job. Uma tarefa que quebra é tentada de novo (até 3 vezes) e
# não impede as outras. Quando não sobra nenhuma, escreve a conferência final e desliga o próprio agendamento.
#   código de saída de uma tarefa: 0 = pronta; 3 = adiantou, mas falta (continua na próxima); outro = quebrou
#     python rotinas/conferencia/fila.py            roda o que der
#     python rotinas/conferencia/fila.py --lista    só mostra a fila
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.dirname(AQUI))
import estado  # noqa: E402

LOGS = os.path.join(AQUI, 'logs')
FINAL = os.path.join(AQUI, 'CONFERENCIA_FINAL.md')
ORCAMENTO_MIN = float(os.environ.get('FILA_MINUTOS') or 320)     # o job tem 350 min
MAX_TENTATIVAS = 3
PY = [sys.executable, '-W', 'ignore']
K26 = PY + ['rotinas/k26/rodar_rodada1.py']
FIM_DA_JANELA = 22 * 60 + 50                                     # a K26 não começa se não acabar antes das 22h50
# K26: 2026 só depois das 11h (o motor tem rodado de manhã) e depois que o motor V1.7 regravou 2026
NOMES_K26 = {1: '2026 inteiro (inclui os dias de previsão GFS)', 2: '2026: Rs = 0 cru do ERA5 e escoamento',
             3: '2026: vento', 4: '2026: umidade do solo', 5: '1961-1970', 6: '1971-1980', 7: '1981-1990',
             8: '1991-2000', 9: '2001-2010', 10: '2011-2020', 11: '2021-2025'}
DURACAO_K26 = {1: 45, 2: 60, 3: 30, 4: 60}


def tarefa_k26(r, nao_antes=None):
    return {'id': f'k26_rodada{r}', 'nome': f'K26 rodada {r} ({NOMES_K26[r]})', 'cmd': K26, 'env': {'K26_RODADA': str(r)},
            'min': DURACAO_K26.get(r, 90), 'k26': True, 'ano2026': r <= 4, 'nao_antes': nao_antes,
            'resultado': f'rotinas/resultados/k26_rodada{r}/'}


TAREFAS = [
    {'id': 'validar_2026', 'nome': '2026 (ERA5 calibrado) contra CHIRPS (chuva) e MODIS (calor)',
     'cmd': PY + ['pesquisa/validar_2026_independente.py'], 'min': 20, 'resultado': 'pesquisa/resultados_2026/RESULTADOS.md'},
    {'id': 'solo_folha', 'nome': 'Umidade do solo, temperatura da folha e do solo, ET real contra satélites (2016-2021)',
     'cmd': PY + ['pesquisa/validar_solo_folha.py'], 'min': 40, 'resultado': 'pesquisa/resultados_solo_folha/RESULTADOS.md'},
    {'id': 'escoamento_extrair', 'nome': 'Escoamento x vazão do CAMELS-BR: extração 1981-2018 (512 bacias)',
     'cmd': PY + ['pesquisa/escoamento/escoamento_camels.py'], 'min': 30, 'parcial': True},
    {'id': 'escoamento_metricas', 'nome': 'Escoamento x CAMELS-BR: métricas e decisão do protocolo',
     'cmd': PY + ['pesquisa/escoamento/escoamento_metricas.py'], 'min': 5, 'depois_de': 'escoamento_extrair',
     'resultado': 'pesquisa/resultados_escoamento/RESULTADOS.md'},
    {'id': 'metodo_2026_A', 'nome': 'As 16 variáveis: o método de 2026 aplicado a 2021-2025 (contra o BR-DWGD)',
     'cmd': PY + ['pesquisa/validar_metodo_2026.py', 'A'], 'min': 30, 'parcial': True,
     'resultado': 'pesquisa/resultados_metodo_2026/RESULTADOS_A.md'},
    {'id': 'metodo_2026_B', 'nome': 'As 16 variáveis de 2026 contra o GLDAS-2.1 (NASA), régua 2022-2024',
     'cmd': PY + ['pesquisa/validar_metodo_2026.py', 'B'], 'min': 60,
     'resultado': 'pesquisa/resultados_metodo_2026/RESULTADOS_B.md'},
    {'id': 'historico', 'nome': 'O histórico 1961-2025, década por década, contra TerraClimate e CHIRPS',
     'cmd': PY + ['pesquisa/validar_historico.py'], 'min': 30, 'parcial': True,
     'resultado': 'pesquisa/resultados_historico/RESULTADOS.md'},
    {'id': 'por_mes', 'nome': 'Todas as validações abertas por mês do ano (estação chuvosa x seca)',
     'cmd': PY + ['pesquisa/resumo_por_mes.py'], 'min': 5, 'depois_de': ['metodo_2026_B', 'historico'],
     'resultado': 'pesquisa/RESULTADOS_POR_MES.md'},
    {'id': 'metricas', 'nome': 'Todas as métricas, região por região, período e mês (para replicação)',
     'cmd': PY + ['pesquisa/metricas_completas.py'], 'min': 5, 'depois_de': ['metodo_2026_B', 'historico'],
     'resultado': 'pesquisa/METODOS_REPLICACAO.md'},
    {'id': 'multifonte_era5', 'nome': 'O banco contra o ERA5-Land bruto, 1961-2025 (fase 2, emenda 1 do M5)',
     'cmd': PY + ['pesquisa/validar_multifonte.py', 'era5'], 'min': 30, 'parcial': True,
     'resultado': 'pesquisa/resultados_multifonte/RESULTADOS.md'},
    {'id': 'multifonte_gldas20', 'nome': 'O banco contra o GLDAS-2.0, 1961-2014 (fase 2, emenda 1 do M5)',
     'cmd': PY + ['pesquisa/validar_multifonte.py', 'gldas20'], 'min': 30, 'parcial': True,
     'resultado': 'pesquisa/resultados_multifonte/RESULTADOS.md'},
    {'id': 'multifonte_gldas21', 'nome': 'O banco contra o GLDAS-2.1, 2000-2025 (fase 2, emenda 1 do M5)',
     'cmd': PY + ['pesquisa/validar_multifonte.py', 'gldas21'], 'min': 30, 'parcial': True,
     'resultado': 'pesquisa/resultados_multifonte/RESULTADOS.md'},
    {'id': 'multifonte_chuva', 'nome': 'O banco contra PERSIANN-CDR e IMERG (chuva) (fase 2, emenda 1 do M5)',
     'cmd': PY + ['pesquisa/validar_multifonte.py', 'chuva'], 'min': 30, 'parcial': True,
     'resultado': 'pesquisa/resultados_multifonte/RESULTADOS.md'},
    {'id': 'multifonte_mod16', 'nome': 'O banco contra o MOD16 (ET real), 2001-2025 (fase 2, emenda 1 do M5)',
     'cmd': PY + ['pesquisa/validar_multifonte.py', 'mod16'], 'min': 30, 'parcial': True,
     'resultado': 'pesquisa/resultados_multifonte/RESULTADOS.md'},
    {'id': 'resolucao', 'nome': 'Sensibilidade à resolução: cada referência na grade do SAB x na resolução nativa',
     'cmd': PY + ['pesquisa/sensibilidade_resolucao.py'], 'min': 30, 'parcial': True,
     'resultado': 'pesquisa/resultados_resolucao/RESULTADOS.md'},
    tarefa_k26(7),                                   # a única década que ainda estava na contagem antiga (v1.8)
    *[tarefa_k26(r, '2026-11-26') for r in (1, 2, 3, 4)],        # 2026 e a previsão, depois da regravação V1.7
    *[tarefa_k26(r, '2026-12-01') for r in (5, 6, 8, 9, 10, 11)],  # o histórico (travado) de novo, no mês seguinte
]

# FILA_SO=id1,id2 roda só essas tarefas (ex.: num branch de teste); nesse modo a fila se chama de novo enquanto
# faltar alguma e nunca desliga o agendamento
SO = [x.strip() for x in (os.environ.get('FILA_SO') or '').split(',') if x.strip()]
if SO:
    TAREFAS = [t for t in TAREFAS if t['id'] in SO]
# cada cadeia FILA_SO tem o seu arquivo de estado (duas cadeias rodam juntas sem se atropelar); a leitura junta todos
ARQ_ESTADO = os.path.join(AQUI, 'fila_estado' + ('_' + '_'.join(SO) if SO else '') + '.json')


def ler():
    st = {}
    for arq in sorted(glob.glob(os.path.join(AQUI, 'fila_estado*.json')), key=lambda a: a == ARQ_ESTADO):
        try:
            st.update(json.load(open(arq)))
        except (OSError, ValueError):
            pass
    return st


def gravar(st):
    with open(ARQ_ESTADO, 'w') as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def git(*a, ok=False):
    r = subprocess.run(['git', *a], cwd=RAIZ, capture_output=True, text=True)
    if r.returncode and not ok:
        print(f'   git {" ".join(a)}: {r.stderr.strip()[:300]}')
    return r.returncode == 0


def subir(msg):
    """Sobe resultados, LOG e estado (sem perder o que outra rotina subiu no meio tempo)."""
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        return
    git('add', 'rotinas', 'pesquisa', 'registro', 'REGISTRO_GERAL.md')
    if git('diff', '--cached', '--quiet', ok=True):
        return
    git('commit', '-q', '-m', msg)
    ramo = os.environ.get('GITHUB_REF_NAME', 'main')
    for i in range(5):
        git('pull', '-q', '--rebase', '-X', 'theirs', 'origin', ramo, ok=True)
        subprocess.run(PY + ['rotinas/estado.py'], cwd=RAIZ, capture_output=True)
        git('add', 'rotinas/PAINEL.md')
        git('diff', '--cached', '--quiet', ok=True) or git('commit', '-q', '--amend', '--no-edit')
        if git('push', '-q', 'origin', f'HEAD:{ramo}'):
            return
        time.sleep(10 * (i + 1))


def pode(t, st, agora, sobra_min):
    e = st.get(t['id'], {})
    if e.get('situacao') in ('ok', 'falhou'):
        return False, 'já feita'
    antes = t.get('depois_de') or []
    antes = [antes] if isinstance(antes, str) else antes
    falta = [x for x in antes if st.get(x, {}).get('situacao') not in ('ok', 'falhou')]
    if falta:
        return False, f"espera {', '.join(falta)}"
    if t.get('nao_antes') and agora.strftime('%Y-%m-%d') < t['nao_antes']:
        return False, f"só a partir de {t['nao_antes']}"
    if t['min'] * 1.5 > sobra_min:
        return False, 'não cabe no tempo deste job'
    if t.get('k26'):
        m = agora.hour * 60 + agora.minute
        if m < (11 * 60 if t.get('ano2026') else 7 * 60) or m + t['min'] * 1.3 > FIM_DA_JANELA:
            return False, 'fora do horário da K26'
        if t.get('ano2026') and not motor_v17_pronto():
            return False, 'o motor V1.7 ainda não regravou 2026'
    return True, ''


_V17 = {}


def motor_v17_pronto():
    """Todos os dias ERA5 de 2026 já estão na V1.7 (consulta só leitura, uma vez por job)."""
    if 'ok' not in _V17:
        try:
            import ee
            sys.path.insert(0, RAIZ)
            import sab_pedido as sp
            ee.Initialize(project=sp.PROJETO)
            c = ee.ImageCollection(sp.SAB).filterDate('2026-01-01', '2027-01-01').filter(
                ee.Filter.eq('versao', 'provisoria_era5'))
            faltam = c.filter(ee.Filter.neq('versao_algoritmo', 'V1.7')).size().getInfo()
            _V17['ok'] = faltam == 0
            print(f'   motor V1.7: {"2026 todo regravado" if faltam == 0 else f"faltam {faltam} dias"}')
        except Exception as e:  # noqa: BLE001
            print(f'   motor V1.7: não consegui conferir ({str(e)[:150]})')
            _V17['ok'] = False
    return _V17['ok']


def rodar(t, st, sobra_min):
    e = st.setdefault(t['id'], {'tentativas': 0})
    for k in ('fim', 'minutos', 'codigo'):          # campos da tentativa anterior não se misturam com esta
        e.pop(k, None)
    e.update(tentativas=e.get('tentativas', 0) + 1, situacao='rodando', inicio=estado.agora().strftime('%d/%m %H:%M'))
    gravar(st)
    subir(f"Conferência: começou {t['id']} [skip ci]")
    env = dict(os.environ, PYTHONUNBUFFERED='1', **t.get('env', {}))
    if t.get('parcial'):
        env['TEMPO_MAX_MIN'] = str(int(sobra_min - 15))
    os.makedirs(LOGS, exist_ok=True)
    t0 = time.time()
    with open(os.path.join(LOGS, f"{t['id']}.txt"), 'a', encoding='utf-8') as log:
        commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
        try:
            from importlib.metadata import version
            vee = version('earthengine-api')
        except Exception:  # noqa: BLE001
            vee = '?'
        log.write(f"\n===== {estado.agora():%d/%m/%Y %H:%M} (Brasília), tentativa {e['tentativas']} =====\n"
                  f"código: commit {commit} | earthengine-api {vee} | Python {sys.version.split()[0]}\n")
        log.flush()
        p = subprocess.run(t['cmd'], cwd=RAIZ, env=env, stdout=log, stderr=subprocess.STDOUT,
                           timeout=60 * max(sobra_min - 5, 10))
    dur = (time.time() - t0) / 60
    if p.returncode == 0:
        e['situacao'] = 'ok'
    elif p.returncode == 3:
        e['situacao'], e['tentativas'] = 'pendente', 0       # adiantou: não conta como tentativa
    else:
        e['situacao'] = 'falhou' if e['tentativas'] >= MAX_TENTATIVAS else 'pendente'
    e.update(fim=estado.agora().strftime('%d/%m %H:%M'), minutos=round(dur), codigo=p.returncode)
    gravar(st)
    print(f"   {t['id']}: código {p.returncode} em {dur:.0f} min -> {e['situacao']}", flush=True)
    return dur


def numeros_k26(t):
    try:
        sys.path.insert(0, os.path.join(RAIZ, 'rotinas', 'k26'))
        import rodar_rodada1 as rr
        base = os.path.join(RAIZ, t['resultado'])
        dias = sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)))
        st = rr.numeros(os.path.join(base, dias[-1])).get('status', {})
        return f"pasta {t['resultado']}{dias[-1]}/; itens: " + ', '.join(f'{i} {s}' for i, s in st.items())
    except Exception as e:  # noqa: BLE001
        return f'(sem os números: {str(e)[:80]})'


def escrever_final(st, acabou):
    if SO:
        return                     # numa cadeia parcial, só os resultados e o estado dela; o resumo é da fila toda
    L = ['# Conferência final do SAB (1961 até a previsão)', '',
         f'Atualizado em {estado.agora():%d/%m/%Y %H:%M} (Brasília) pela fila automática '
         f'(`rotinas/conferencia/fila.py`). ' + ('**Todas as tarefas terminaram.**' if acabou else 'Ainda há tarefas na fila.'),
         '', '| Tarefa | Situação | Tentativas | Quando | Resultado |', '|---|---|---|---|---|']
    for t in TAREFAS:
        e = st.get(t['id'], {})
        s = {'ok': '✅ pronta', 'falhou': '❌ quebrou 3 vezes', 'rodando': '🔄 rodando'}.get(e.get('situacao'), '⏳ na fila')
        onde = numeros_k26(t) if t.get('k26') and e.get('situacao') == 'ok' else (t.get('resultado') or '')
        L.append(f"| {t['nome']} | {s} | {e.get('tentativas', 0)} | {e.get('fim', '')} | {onde} |")
    L += ['', 'O LOG de cada tarefa fica em `rotinas/conferencia/logs/<tarefa>.txt`. ❌ = me mande esse LOG.', '']
    for t in TAREFAS:
        r = t.get('resultado', '')
        if r.endswith('.md') and os.path.exists(os.path.join(RAIZ, r)) and st.get(t['id'], {}).get('situacao') == 'ok':
            L += ['---', '', f"## {t['nome']}", '', f'(cópia de `{r}`)', '']
            L += [x.replace('# ', '### ', 1) if x.startswith('# ') else x
                  for x in open(os.path.join(RAIZ, r), encoding='utf-8').read().splitlines()]
            L.append('')
    with open(FINAL, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    subprocess.run(PY + ['registro/gerar_registro.py'], cwd=RAIZ, capture_output=True)   # REGISTRO_GERAL.md em dia
    feitas = sum(st.get(t['id'], {}).get('situacao') == 'ok' for t in TAREFAS)
    falhas = [t['id'] for t in TAREFAS if st.get(t['id'], {}).get('situacao') == 'falhou']
    sit = ('atencao' if falhas else 'conferir') if acabou else ('atencao' if falhas else 'esperando')
    estado.registrar('conferencia', sit, [f'{feitas} de {len(TAREFAS)} tarefas prontas'
                                          + (f'; quebraram: {", ".join(falhas)}' if falhas else '')
                                          + ('; TERMINOU: leia o CONFERENCIA_FINAL.md' if acabou else '')],
                     'rotinas/conferencia/CONFERENCIA_FINAL.md')


def main():
    st = ler()
    if '--lista' in sys.argv:
        for t in TAREFAS:
            print(t['id'], st.get(t['id'], {}).get('situacao', 'na fila'), pode(t, st, estado.agora(), ORCAMENTO_MIN)[1])
        return
    inicio = time.time()
    while True:
        sobra = ORCAMENTO_MIN - (time.time() - inicio) / 60
        agora = estado.agora()
        prontas = [t for t in TAREFAS if pode(t, st, agora, sobra)[0]]
        if not prontas:
            break
        t = prontas[0]
        print(f"{agora:%d/%m %H:%M} -> {t['nome']}", flush=True)
        try:
            rodar(t, st, sobra)
        except subprocess.TimeoutExpired:
            st[t['id']].update(situacao='pendente', fim=estado.agora().strftime('%d/%m %H:%M'), codigo='tempo')
            gravar(st)
        acabou = all(st.get(x['id'], {}).get('situacao') in ('ok', 'falhou') for x in TAREFAS)
        escrever_final(st, acabou)
        subir(f"Conferência: {t['id']} ({st[t['id']]['situacao']}) [skip ci]")
    for t in TAREFAS:
        print(f"   {t['id']}: {st.get(t['id'], {}).get('situacao', 'na fila')} | {pode(t, st, estado.agora(), ORCAMENTO_MIN)[1]}")
    acabou = all(st.get(x['id'], {}).get('situacao') in ('ok', 'falhou') for x in TAREFAS)
    escrever_final(st, acabou)
    subir('Conferência: situação da fila [skip ci]')
    if SO and not acabou and os.environ.get('GITHUB_ACTIONS') == 'true':
        presas = [t['id'] for t in TAREFAS if st.get(t['id'], {}).get('situacao') not in ('ok', 'falhou')
                  and pode(t, st, estado.agora(), ORCAMENTO_MIN)[0]]
        if presas:
            print(f'Ainda faltam {presas}: chamando a fila de novo neste branch.')
            for i in range(4):          # [25/11] o GitHub às vezes responde 500/502: sem repetir, a cadeia parava
                r = subprocess.run(['gh', 'workflow', 'run', 'rotina_conferencia.yml', '--ref',
                                    os.environ.get('GITHUB_REF_NAME', 'main'), '-f', f'so={",".join(SO)}'], cwd=RAIZ)
                if r.returncode == 0:
                    break
                print(f'   a chamada falhou (código {r.returncode}); de novo em {60 * (i + 1)} s', flush=True)
                time.sleep(60 * (i + 1))
        return
    if acabou and not SO and os.environ.get('GITHUB_ACTIONS') == 'true':
        print('Fila vazia: desligando o agendamento da conferência.')
        subprocess.run(['gh', 'workflow', 'disable', 'rotina_conferencia.yml'], cwd=RAIZ)


if __name__ == '__main__':
    main()
