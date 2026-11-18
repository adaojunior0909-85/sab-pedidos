# PILOTO PARA FRENTE: previsão estendida de Tmax e Tmin (16 a 90 dias), só onde a pesquisa aprovou, guardada no dia
# em que é emitida e conferida depois, quando o dado chega. É a prova definitiva (PROTOCOLO.md): o hindcast mede o
# passado; o piloto mede previsões feitas sem saber o resultado.
#     python pesquisa/piloto.py emitir   [--data AAAA-MM-DD]   (dias 3 e 17 de cada mês: emissão na quinzena)
#     python pesquisa/piloto.py conferir                          (confere as previsões cujo período já passou)
# Só LÊ o Earth Engine (SAB_V1 nos 989 pontos da pesquisa e OISST). Grava em pesquisa/piloto/.
#
# Como cada previsão é feita (o mesmo do hindcast, com o treino até 2025):
#   - modelo de cada célula (região ou Paraná x estação x alvo x variável) = o método escolhido pela pesquisa
#     (Tmax: rodada 2; Tmin: rodada 1, pela regra de aceite) e SÓ nas células aprovadas; nas outras, nada é previsto
#     ("sem sinal": a referência é a média histórica);
#   - ajustado no BR-DWGD 1982-2025; a persistência usa as duas quinzenas antes da emissão no SAB_V1 (provisórios ERA5
#     e, nos últimos dias, a previsão GFS já gravada: é o que existe no dia da emissão);
#   - probabilidades dos tercis (abaixo, perto, acima do normal 1991-2020) com o erro "ano de fora" do método.
import argparse
import csv
import gzip
import os
import shutil
import sys
import tempfile
import time
from datetime import date, timedelta

import numpy as np
import pandas as pd
from scipy.special import ndtr

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..'))
import hindcast as hc  # noqa: E402

PASTA = os.path.join(AQUI, 'piloto')
DADOS = os.path.join(AQUI, 'dados')
ESCOLHA = {'tx': os.path.join(AQUI, 'resultados_rodada2', 'metodo_escolhido_por_celula.csv'),
           'tn': os.path.join(AQUI, 'resultados', 'metodo_escolhido_por_celula.csv')}
SEM = 'sem sinal: média histórica'
NORMAL = (1991, 2020)
COLS_PREV = ['emissao', 'emitida_em', 'id', 'lat', 'lon', 'uf', 'regiao', 'celula', 'variavel', 'alvo', 'inicio', 'fim', 'metodo',
             'previsto', 'climatologia', 'p_abaixo', 'p_normal', 'p_acima', 'limite_abaixo', 'limite_acima',
             'dias_gfs_na_persistencia']


def quinzena_de(d):
    return (d.month - 1) * 2 + (0 if d.day <= 15 else 1)


def inicio_quinzena(ano, q):
    return date(ano + (q // 24), (q % 24) // 2 + 1, 1 if q % 2 == 0 else 16)


def fim_quinzena(ano, q):
    a, qq = ano + q // 24, q % 24
    return inicio_quinzena(a, qq + 1) - timedelta(days=1) if qq < 23 else date(a, 12, 31)


# ---------------------------------------------------------------------------------------------- Earth Engine
def _ee():
    import ee
    import sab_pedido as sp
    ee.Initialize(project=sp.PROJETO)
    return ee, sp


def extrair_sab(ano, ate, pontos):
    """Quinzenas do SAB_V1 (como o BR-DWGD do extrator) nos pontos, só com dias ANTES de 'ate'; conta os dias de
    previsão GFS (para a persistência) e os dias provisórios ERA5 (para a conferência)."""
    ee, sp = _ee()
    col = ee.ImageCollection(sp.SAB)
    bandas, nomes = [], []
    for q in range(24):
        d0, d1 = inicio_quinzena(ano, q), fim_quinzena(ano, q) + timedelta(days=1)
        if d0 >= ate:
            break
        c = col.filterDate(str(d0), str(min(d1, ate))).map(lambda i: i.select(['pr_mm', 'tmax_C', 'tmin_C'])
                                                          .rename(['pr', 'tx', 'tn']).set('versao', i.get('versao')))
        gfs = c.filter(ee.Filter.stringStartsWith('versao', 'provisoria_gfs')).size()
        era = c.filter(ee.Filter.eq('versao', 'provisoria_era5')).size()
        vazio = ee.Image.constant(0).toFloat().updateMask(0)
        ou = (lambda red, c=c: ee.Image(ee.Algorithms.If(c.size().gt(0), red, vazio)))
        bandas += [ou(c.select('pr').sum()), ou(c.select('tx').mean()), ou(c.select('tn').mean()),
                   ou(c.select('pr').count().toFloat()),
                   ee.Image.constant(gfs).toFloat(), ee.Image.constant(era).toFloat()]
        nomes += [f'pr_{q:02d}', f'tx_{q:02d}', f'tn_{q:02d}', f'n_{q:02d}', f'gfs_{q:02d}', f'era5_{q:02d}']
    img = ee.Image.cat(bandas).rename(nomes)
    linhas = []
    for i in range(0, len(pontos), 250):
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([float(p['lon']), float(p['lat'])]), {'id': p['id']})
                                   for _, p in pontos.iloc[i:i + 250].iterrows()])
        for t in range(4):
            try:
                r = img.reduceRegions(collection=fc, reducer=ee.Reducer.first(), crs=sp.CRS,
                                      crsTransform=sp.TRANSFORM).getInfo()
                break
            except Exception as e:  # noqa: BLE001
                if t == 3:
                    raise
                print(f'   ⚠️ {str(e)[:120]}; nova tentativa')
                time.sleep(20 * (t + 1))
        for f in r['features']:
            p = f['properties']
            linhas.append({'id': p['id'], 'ano': ano, **{n: p.get(n) for n in nomes}})
    return pd.DataFrame(linhas), [n for n in nomes]


def atualizar_sst(pasta):
    """Os meses novos do OISST (o extrator pula os que já tem)."""
    import extrair_dados as ex
    ee, _ = _ee()
    ex.DADOS = pasta
    ex.sst()


# -------------------------------------------------------------------------------------------------- emitir
def escolhas():
    out = {}
    for v, arq in ESCOLHA.items():
        e = pd.read_csv(arq)
        e = e[(e['variavel'] == v) & (e['produto'] != SEM)]
        for _, r in e.iterrows():
            out[(v, r['alvo'], r['estacao'], r['regiao'])] = r['metodo']
    return out


def estacao_de(mes):
    return next(k for k, ms in hc.ESTACOES.items() if mes in ms)


def emitir(data_emissao):
    ano = data_emissao.year
    q = quinzena_de(data_emissao)
    emissao = inicio_quinzena(ano, q)            # a previsão é da quinzena que começa no dia 1 ou 16
    os.makedirs(os.path.join(PASTA, 'previsoes'), exist_ok=True)
    arq = os.path.join(PASTA, 'previsoes', f'{emissao}.csv')
    if os.path.exists(arq):
        print(f'Já existe a previsão emitida em {emissao}: nada a fazer (uma previsão emitida não é refeita).')
        return
    tmp = tempfile.mkdtemp(prefix='piloto_')
    shutil.copytree(DADOS, os.path.join(tmp, 'dados'))
    dados = os.path.join(tmp, 'dados')
    atualizar_sst(dados)
    pts = pd.read_csv(os.path.join(dados, 'pontos.csv'), dtype={'id': str})
    # o BR-DWGD termina em 2025: de 2026 até a emissão, as quinzenas vêm do SAB_V1, só com dias ANTES da emissão
    for a_ in range(2026, ano + 1):
        sab, nomes = extrair_sab(a_, min(emissao, date(a_ + 1, 1, 1)), pts)
        base = sab[['id', 'ano'] + [n for n in nomes if not n.startswith(('gfs_', 'era5_'))]]
        with gzip.open(os.path.join(dados, 'brdwgd', f'{a_}.csv.gz'), 'wt', newline='', encoding='utf-8') as f:
            base.to_csv(f, index=False)
    q1, q2 = (q - 1) % 24, (q - 2) % 24
    gfs_pers = int(sum(np.nan_to_num(pd.to_numeric(sab.get(f'gfs_{x:02d}', pd.Series([0.0])), errors='coerce').max())
                       for x in (q1, q2)))
    # treino até 2025; o ano da emissão entra só como ano a prever (o alvo dele não existe ainda)
    hc.TREINO_FIM, hc.VALID_FIM_AJUSTE = 2025, 2014
    pts_c, anos, serie, caixas = hc.carregar(dados)
    sst = hc.anomalias_sst(caixas)
    regs = list(hc.REGIOES)
    reg_id = pts_c['regiao'].map(regs.index).to_numpy()
    no_pr = pts_c['uf'].map(hc.sem_acento).to_numpy() == 'parana'
    esc = escolhas()
    est = estacao_de(emissao.month)
    linhas = []
    for v in ('tx', 'tn'):
        for alvo, offs in hc.ALVOS.items():
            celulas = {}
            for i in range(len(pts_c)):
                cel = 'Paraná' if no_pr[i] else pts_c['regiao'][i]
                m = esc.get((v, alvo, est, cel))
                if m:
                    celulas.setdefault(m, []).append((i, cel))
            if not celulas:
                continue
            iy, Y, SS, PERS, EN = hc.montar(serie, anos, sst, v, alvo)
            j = int(np.where(iy == ano)[0][0])
            prev = hc.rodar_config(Y, SS, PERS, EN, iy, reg_id, 'mm', [])
            tr = iy <= 2025
            normal = (iy >= NORMAL[0]) & (iy <= NORMAL[1])
            t1 = np.nanpercentile(Y[q][:, normal], 100 / 3, axis=-1)
            t2 = np.nanpercentile(Y[q][:, normal], 200 / 3, axis=-1)
            ini = inicio_quinzena(ano, q + offs[0])
            fim = fim_quinzena(ano, q + offs[-1])
            for m, lista in celulas.items():
                pred = prev[m]['A'][q, :, j]
                sig = np.sqrt(np.nanmean((prev[m]['TL'][q] - Y[q])[:, tr] ** 2, axis=-1))
                clim = prev['C0']['A'][q, :, j]
                for i, cel in lista:
                    if not np.isfinite(pred[i]):
                        continue
                    pa = float(ndtr((t1[i] - pred[i]) / sig[i]))
                    pn = float(ndtr((t2[i] - pred[i]) / sig[i])) - pa
                    linhas.append({'emissao': str(emissao), 'emitida_em': str(date.today()), 'id': pts_c['id'][i], 'lat': pts_c['lat'][i],
                                   'lon': pts_c['lon'][i], 'uf': pts_c['uf'][i], 'regiao': pts_c['regiao'][i],
                                   'celula': cel, 'variavel': v, 'alvo': alvo, 'inicio': str(ini), 'fim': str(fim),
                                   'metodo': m, 'previsto': round(float(pred[i]), 2),
                                   'climatologia': round(float(clim[i]), 2), 'p_abaixo': round(pa, 3),
                                   'p_normal': round(pn, 3), 'p_acima': round(1 - pa - pn, 3),
                                   'limite_abaixo': round(float(t1[i]), 2), 'limite_acima': round(float(t2[i]), 2),
                                   'dias_gfs_na_persistencia': gfs_pers})
            print(f'  {v} {alvo}: {sum(len(l) for l in celulas.values())} pontos previstos ({", ".join(celulas)})')
    with open(arq, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLS_PREV)
        w.writeheader()
        w.writerows(linhas)
    shutil.copy(os.path.join(dados, 'sst_mensal.csv'), os.path.join(DADOS, 'sst_mensal.csv'))
    print(f'✅ Previsão emitida em {emissao} (estação {est}): {len(linhas)} linhas em {arq}. '
          f'Persistência com {gfs_pers} dia(s) de previsão GFS.')


# ------------------------------------------------------------------------------------------------- conferir
def conferir(hoje):
    pasta_prev = os.path.join(PASTA, 'previsoes')
    arqs = sorted(os.listdir(pasta_prev)) if os.path.isdir(pasta_prev) else []
    if not arqs:
        print('Nenhuma previsão emitida ainda.')
        return
    prev = pd.concat([pd.read_csv(os.path.join(pasta_prev, a), dtype={'id': str}) for a in arqs])
    arq_conf = os.path.join(PASTA, 'conferencia.csv')
    feitas = pd.read_csv(arq_conf, dtype={'id': str}) if os.path.exists(arq_conf) else pd.DataFrame()
    if len(feitas):
        chave = set(zip(feitas['emissao'], feitas['id'], feitas['variavel'], feitas['alvo']))
        prev = prev[[k not in chave for k in zip(prev['emissao'], prev['id'], prev['variavel'], prev['alvo'])]]
    prev = prev[pd.to_datetime(prev['fim']).dt.date < hoje]
    if prev.empty:
        print('Nenhuma previsão nova com o período já terminado.')
        return
    pts = pd.read_csv(os.path.join(DADOS, 'pontos.csv'), dtype={'id': str})
    obs = {}
    for ano in sorted({int(x[:4]) for x in prev['inicio']} | {int(x[:4]) for x in prev['fim']}):
        df, _ = extrair_sab(ano, min(hoje, date(ano + 1, 1, 1)), pts)
        obs[ano] = df.set_index('id')
    novas = []
    for _, r in prev.iterrows():
        ini, fim = date.fromisoformat(r['inicio']), date.fromisoformat(r['fim'])
        vals, ok = [], True
        d = ini
        while d <= fim:
            q = quinzena_de(d)
            o = obs[d.year].loc[r['id']] if r['id'] in obs[d.year].index else None
            dias = (fim_quinzena(d.year, q) - inicio_quinzena(d.year, q)).days + 1
            n_era5 = None if o is None else o.get(f'era5_{q:02d}')
            if n_era5 is None or pd.isna(n_era5) or int(n_era5) < dias or pd.isna(o.get(f"{r['variavel']}_{q:02d}")):
                ok = False                       # só confere com a quinzena inteira em provisório ERA5
                break
            vals.append(float(o[f"{r['variavel']}_{q:02d}"]))
            d = fim_quinzena(d.year, q) + timedelta(days=1)
        if not ok:
            continue
        y = float(np.mean(vals))
        cat = 0 if y <= r['limite_abaixo'] else (2 if y > r['limite_acima'] else 1)
        cat_p = int(np.argmax([r['p_abaixo'], r['p_normal'], r['p_acima']]))
        o1, o12 = float(cat == 0), float(cat <= 1)
        rps = (r['p_abaixo'] - o1) ** 2 + (r['p_abaixo'] + r['p_normal'] - o12) ** 2
        rps_c = (1 / 3 - o1) ** 2 + (2 / 3 - o12) ** 2
        novas.append({**{k: r[k] for k in ('emissao', 'id', 'celula', 'variavel', 'alvo', 'inicio', 'fim', 'metodo',
                                           'previsto', 'climatologia')},
                      'observado': round(y, 2), 'erro_previsto': round(r['previsto'] - y, 2),
                      'erro_climatologia': round(r['climatologia'] - y, 2), 'tercil_observado': cat,
                      'tercil_mais_provavel': cat_p, 'rps': round(rps, 4), 'rps_climatologia': round(rps_c, 4)})
    if not novas:
        print('Os períodos terminados ainda não têm todos os dias em provisório ERA5; confiro na próxima.')
        return
    tudo = pd.concat([feitas, pd.DataFrame(novas)], ignore_index=True)
    tudo.to_csv(arq_conf, index=False)
    resumo(tudo)
    print(f'✅ {len(novas)} previsões conferidas agora; {len(tudo)} no total.')


def resumo(c):
    L = ['# Piloto: previsões conferidas', '',
         'Cada linha da tabela junta as previsões já conferidas. MSESS > 0 = a previsão errou menos que a média '
         'histórica; acerto do tercil: 33% = acaso; RPSS > 0 = as probabilidades foram melhores que 1/3 para cada '
         'tercil. Com poucas emissões, os números ainda oscilam muito.', '',
         '| Variável | Alvo | Emissões | Previsões | MSESS | Erro médio previsto (°C) | Erro médio média histórica (°C) | '
         'Acerto do tercil | RPSS |', '|---|---|---|---|---|---|---|---|---|']
    for (v, a), g in c.groupby(['variavel', 'alvo']):
        msess = 1 - (g['erro_previsto'] ** 2).sum() / (g['erro_climatologia'] ** 2).sum()
        L.append(f"| {hc.NOME_VAR[v]} | {a} | {g['emissao'].nunique()} | {len(g)} | {msess:+.2f} | "
                 f"{g['erro_previsto'].abs().mean():.2f} | {g['erro_climatologia'].abs().mean():.2f} | "
                 f"{100 * (g['tercil_observado'] == g['tercil_mais_provavel']).mean():.0f}% | "
                 f"{1 - g['rps'].mean() / g['rps_climatologia'].mean():+.2f} |")
    with open(os.path.join(PASTA, 'CONFERENCIA.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('acao', choices=['emitir', 'conferir'])
    ap.add_argument('--data', default=None, help='data da emissão (padrão: hoje)')
    a = ap.parse_args()
    d = date.fromisoformat(a.data) if a.data else date.today()
    if a.acao == 'emitir':
        emitir(d)
    else:
        conferir(d)
