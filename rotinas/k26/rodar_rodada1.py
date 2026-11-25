# Roda a K26 (K26_auditoria_final.py, sem mudança) só na rodada 1 (2026 inteiro: A, B, C, G, H, P, Z; ~35 min; só
# leitura) no GitHub Actions, guarda os CSV e o LOG em rotinas/resultados/k26_rodada1/<data>/ e registra no painel
# de controle os números que importam, ao lado dos da execução anterior.
#     python rotinas/k26/rodar_rodada1.py
import glob
import importlib.util
import json
import os
import shutil
import sys
import tempfile

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import estado  # noqa: E402

ENTREGUES = ('A', 'B', 'C_interior')
METRICAS = ('rs_zero', 'rs_lt_003ra', 'rs_gt_rso_motor', 'runoff_sup_gt_pr', 'runoff_sup_gt_200')


def carregar_k26():
    spec = importlib.util.spec_from_file_location('k26', os.path.join(AQUI, 'K26_auditoria_final.py'))
    k = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(k)          # importar não roda nada (o __main__ do arquivo fica de fora)
    return k


def numeros(pasta):
    """Os números da rodada que o painel mostra (pixels entregues: A, B e C_interior)."""
    n = {}
    cd = os.path.join(pasta, 'K26_CD_por_classe.csv')
    if os.path.exists(cd):
        c = pd.read_csv(cd, sep=';', decimal=',')
        e = c[c.nome_classe.isin(ENTREGUES)]
        n['pixel_dias'] = int(e.n_pix.sum())
        for m in METRICAS:
            if m in e:
                n[m] = int(e[m].sum())
    g = os.path.join(pasta, 'K26_G_resumo.csv')
    if os.path.exists(g):
        gg = pd.read_csv(g, sep=';', decimal=',')
        if 'eto_difere' in gg:
            n['eto_difere'] = int(gg['eto_difere'].sum())
    inv = os.path.join(pasta, 'K26_A_inventario.csv')
    if os.path.exists(inv):
        i = pd.read_csv(inv, sep=';', decimal=',')
        n['dias'] = len(i)
        n['ultimo_dia'] = str(i['data'].max())
    r = os.path.join(pasta, 'K26_RESUMO.csv')
    if os.path.exists(r):
        rr = pd.read_csv(r, sep=';', decimal=',')
        n['status'] = {str(x.item): str(x.status) for x in rr.itertuples()}
    return n


def main():
    dia = estado.agora().strftime('%Y-%m-%d')
    pasta_rel = f'rotinas/resultados/k26_rodada1/{dia}'
    destino = os.path.join(estado.RAIZ, pasta_rel)
    anterior = estado.ler_estados().get('k26', {}).get('detalhes', {})
    trabalho = tempfile.mkdtemp(prefix='k26_')
    k = carregar_k26()
    k.RAIZ = trabalho
    erro = None
    try:
        feitas = k.rodar_sequencia([1])
    except BaseException as e:          # noqa: BLE001
        feitas, erro = [], e
    pastas = sorted(p for p in glob.glob(os.path.join(trabalho, 'K26_rodada1_*')) if os.path.isdir(p))
    os.makedirs(destino, exist_ok=True)
    for p in pastas[-1:]:
        for f in os.listdir(p):
            shutil.copy2(os.path.join(p, f), destino)
    for f in glob.glob(os.path.join(trabalho, 'K26_SEQUENCIA_*', 'LOG_SEQUENCIA.txt')):
        shutil.copy2(f, destino)
    if erro is not None or not feitas or not pastas:
        estado.registrar('k26', 'falhou', [f'não terminou: {str(erro)[:200] if erro else "nenhuma rodada feita"}'],
                         pasta_rel)
        raise SystemExit(1)
    n = numeros(destino)
    st = n.get('status', {})
    quebradas = [i for i, s in st.items() if s == 'FALHOU']
    comparar = lambda m: (f"{n.get(m, '-')}" + (f" (antes {anterior[m]})" if m in anterior else ''))  # noqa: E731
    resumo = [f"{n.get('dias', '?')} dias de 2026 (até {n.get('ultimo_dia', '?')}); itens: "
              + ', '.join(f'{i} {s}' for i, s in st.items() if i in ('A1', 'B', 'C', 'G', 'H')),
              f"Rs = 0 (pixels entregues, pixel-dias pesados pela máscara): {comparar('rs_zero')}",
              f"Rs abaixo de 3% de Ra: {comparar('rs_lt_003ra')} · Rs acima do céu claro: {comparar('rs_gt_rso_motor')}",
              f"ETo gravada diferente da recalculada (G): {comparar('eto_difere')}",
              f"escoamento > chuva: {comparar('runoff_sup_gt_pr')} · escoamento > 200 mm: {comparar('runoff_sup_gt_200')}",
              'C e G com FALHA são esperados (escoamento x chuva; Rs = 0 do litoral, que a leitura deixa vazio): '
              'o que importa é a tendência dos números entre uma execução e outra']
    situacao = 'falhou' if quebradas else ('atencao' if st.get('H') not in ('OK', None) or st.get('A1') != 'OK'
                                           else 'conferir')
    if quebradas:
        resumo.insert(0, f'partes que não terminaram: {", ".join(quebradas)}')
    estado.registrar('k26', situacao, resumo, pasta_rel, {m: n[m] for m in METRICAS + ('eto_difere',) if m in n})
    print(json.dumps(n, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
