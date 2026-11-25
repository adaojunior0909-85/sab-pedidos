# Acerto da previsão GFS do SAB, medido de verdade (só LÊ o Earth Engine).
# O SAB_V1 guarda só a última versão de cada dia: quando o ERA5 chega, a previsão daquele dia é sobrescrita. Por isso
# esta rotina, todo dia:
#   1. FOTOGRAFA a previsão em vigor (todos os dias GFS do banco) nos 706 pontos da grade de 1 grau da pesquisa, junto
#      com o último dia ERA5 (a "persistência": repetir o último dia conhecido, o palpite mais simples);
#   2. CONFERE as fotografias antigas: para cada dia previsto que já virou ERA5, o erro da previsão e o da persistência,
#      por prazo (dias entre a fotografia e o dia previsto), variável e região; guarda as somas em erros.csv e apaga a
#      fotografia quando todos os dias dela forem conferidos (ou depois de 45 dias);
#   3. RESUME em ACERTO.md: erro médio absoluto (MAE), viés e quanto a previsão erra menos que a persistência.
# A referência é o ERA5 calibrado (provisório) que substitui o dia: mede o quanto a previsão se afasta do que o próprio
# SAB grava depois. Quando o BR-DWGD cobrir 2026, dá para refazer contra o observado.
#     python rotinas/previsao/acerto_previsao.py
import glob
import os
import sys
from datetime import date, timedelta

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, 'pesquisa'))
import ee  # noqa: E402
import estado  # noqa: E402
import sab_pedido as sp  # noqa: E402
from hindcast import UF_REGIAO, sem_acento  # noqa: E402

PASTA = os.path.join(RAIZ, 'rotinas', 'resultados', 'previsao')
FOTOS = os.path.join(PASTA, 'fotografias')
ERROS = os.path.join(PASTA, 'erros.csv')
CONFERIDOS = os.path.join(PASTA, 'conferidos.csv')
VARIAVEIS = {'pr_mm': 'Chuva (mm)', 'tmax_C': 'Tmax (°C)', 'tmin_C': 'Tmin (°C)', 'RH': 'UR (%)', 'u2': 'Vento (m/s)',
             'rs': 'Radiação (MJ/m²)', 'et_potencial': 'ETo (mm)'}
PRAZOS_RESUMO = (1, 2, 3, 5, 7, 10, 13, 15)
MAX_DIAS_FOTO = 45


def pontos():
    p = pd.read_csv(os.path.join(RAIZ, 'pesquisa', 'dados', 'pontos.csv'), dtype={'id': str})
    p = p[p.grupo == 'BR_1grau'].copy()
    p['regiao'] = p['uf'].map(lambda u: UF_REGIAO.get(sem_acento(u), ''))
    return p


def amostrar(img, fc):
    """Valores das 7 variáveis do dia nos pontos (pixel da grade do SAB)."""
    r = img.select(list(VARIAVEIS)).reduceRegions(collection=fc, reducer=ee.Reducer.first(), crs=sp.CRS,
                                                   crsTransform=sp.TRANSFORM).getInfo()
    return pd.DataFrame([{'id': f['properties']['id'], **{v: f['properties'].get(v) for v in VARIAVEIS}}
                         for f in r['features']])


def inventario(hoje):
    col = ee.ImageCollection(sp.SAB).filterDate(str(hoje - timedelta(days=80)), str(hoje + timedelta(days=20)))
    idx, ver = ee.List([col.aggregate_array('system:index'), col.aggregate_array('versao')]).getInfo()
    dia = lambda i: date(int(i[4:8]), int(i[9:11]), int(i[12:14]))  # noqa: E731
    return {dia(i): v for i, v in zip(idx, ver)}


def imagem(d):
    return ee.Image(f"{sp.SAB}/SAB_{d:%Y_%m_%d}")


def fotografar(hoje, inv, pts, fc):
    arq = os.path.join(FOTOS, f'{hoje}.csv.gz')
    if os.path.exists(arq):
        return f'fotografia de {hoje} já existe'
    gfs = sorted(d for d, v in inv.items() if str(v).startswith('provisoria_gfs'))
    era5 = sorted(d for d, v in inv.items() if v == 'provisoria_era5')
    if not gfs or not era5:
        return 'sem dias GFS ou ERA5 para fotografar'
    linhas = []
    for d in gfs + [era5[-1]]:
        a = amostrar(imagem(d), fc)
        a.insert(0, 'data', str(d))
        a.insert(1, 'tipo', 'persistencia' if d == era5[-1] else 'previsao')
        a.insert(2, 'versao', inv[d])
        linhas.append(a)
    os.makedirs(FOTOS, exist_ok=True)
    pd.concat(linhas).round(3).to_csv(arq, index=False)
    return f'fotografia de {hoje}: {len(gfs)} dias GFS ({gfs[0]} a {gfs[-1]}) e a persistência ({era5[-1]})'


def conferir(hoje, inv, pts, fc):
    feitos = pd.read_csv(CONFERIDOS, dtype=str) if os.path.exists(CONFERIDOS) else pd.DataFrame(columns=['emissao', 'data'])
    ja = set(zip(feitos['emissao'], feitos['data']))
    obs_cache, novos_erros, novos_feitos, apagadas = {}, [], [], 0
    regiao = pts.set_index('id')['regiao']
    for arq in sorted(glob.glob(os.path.join(FOTOS, '*.csv.gz'))):
        emissao = os.path.basename(arq)[:10]
        f = pd.read_csv(arq, dtype={'id': str})
        prev = f[f.tipo == 'previsao']
        pers = f[f.tipo == 'persistencia'].set_index('id')[list(VARIAVEIS)]
        pendentes = [d for d in sorted(prev['data'].unique()) if (emissao, d) not in ja]
        for d in pendentes:
            dd = date.fromisoformat(d)
            if inv.get(dd) != 'provisoria_era5':
                continue
            if d not in obs_cache:
                obs_cache[d] = amostrar(imagem(dd), fc).set_index('id')[list(VARIAVEIS)]
            obs = obs_cache[d]
            p = prev[prev['data'] == d].set_index('id')[list(VARIAVEIS)]
            prazo = (dd - date.fromisoformat(emissao)).days
            for v in VARIAVEIS:
                j = pd.DataFrame({'p': p[v], 'o': obs[v], 'q': pers[v]}).dropna()
                if j.empty:
                    continue
                j['regiao'] = regiao.reindex(j.index).values
                for reg, g in [('Brasil', j)] + list(j.groupby('regiao')):
                    if not reg:
                        continue
                    e, ep = g['p'] - g['o'], g['q'] - g['o']
                    novos_erros.append({'emissao': emissao, 'data': d, 'prazo': prazo, 'variavel': v, 'regiao': reg,
                                        'n': len(g), 'soma_erro': round(e.sum(), 4), 'soma_abs': round(e.abs().sum(), 4),
                                        'soma_quad': round((e ** 2).sum(), 4), 'soma_abs_persist': round(ep.abs().sum(), 4)})
            novos_feitos.append({'emissao': emissao, 'data': d})
            ja.add((emissao, d))
        resta = [d for d in prev['data'].unique() if (emissao, d) not in ja]
        if not resta or (hoje - date.fromisoformat(emissao)).days > MAX_DIAS_FOTO:
            os.remove(arq)
            apagadas += 1
    if novos_erros:
        e = pd.DataFrame(novos_erros)
        e.to_csv(ERROS, mode='a', header=not os.path.exists(ERROS), index=False)
    if novos_feitos:
        pd.DataFrame(novos_feitos).to_csv(CONFERIDOS, mode='a', header=not os.path.exists(CONFERIDOS), index=False)
    return len(novos_feitos), apagadas


def resumir():
    if not os.path.exists(ERROS):
        return None
    e = pd.read_csv(ERROS)
    e = e[e.prazo >= 0]
    L = ['# Acerto da previsão GFS do SAB', '',
         'Erro médio absoluto (MAE) da previsão gravada pelo motor contra o ERA5 calibrado que depois substitui o dia, '
         'nos 706 pontos da grade de 1 grau, por prazo (dias entre a fotografia da previsão e o dia previsto). '
         '"Ganho" = quanto a previsão erra menos que a persistência (repetir o último dia ERA5): +30% = erra 30% menos; '
         'negativo = pior que repetir o último dia. Viés = previsão − ERA5.', '',
         f'Dias previstos conferidos: {e.drop_duplicates(["emissao", "data"]).shape[0]} (de {e.emissao.nunique()} '
         f'fotografia(s), {e.emissao.min()} a {e.emissao.max()}).', '']
    br = e[e.regiao == 'Brasil'].groupby(['variavel', 'prazo'])[['n', 'soma_erro', 'soma_abs', 'soma_abs_persist']].sum()
    br['mae'], br['vies'] = br.soma_abs / br.n, br.soma_erro / br.n
    br['ganho'] = 100 * (1 - br.soma_abs / br.soma_abs_persist)
    prazos = [p for p in PRAZOS_RESUMO if p in br.index.get_level_values('prazo')]
    L += ['## Brasil: MAE (ganho sobre a persistência)', '',
          '| Variável | ' + ' | '.join(f'{p} d' for p in prazos) + ' |', '|---|' + '---|' * len(prazos)]
    for v, nome in VARIAVEIS.items():
        cel = []
        for p in prazos:
            if (v, p) in br.index:
                r = br.loc[(v, p)]
                cel.append(f"{r.mae:.2f} ({r.ganho:+.0f}%)")
            else:
                cel.append('-')
        L.append(f'| {nome} | ' + ' | '.join(cel) + ' |')
    L += ['', '## Brasil: viés (previsão − ERA5)', '',
          '| Variável | ' + ' | '.join(f'{p} d' for p in prazos) + ' |', '|---|' + '---|' * len(prazos)]
    for v, nome in VARIAVEIS.items():
        L.append(f'| {nome} | ' + ' | '.join(f"{br.loc[(v, p)].vies:+.2f}" if (v, p) in br.index else '-'
                                              for p in prazos) + ' |')
    rg = e[(e.regiao != 'Brasil') & (e.prazo.between(1, 5))].groupby(['regiao', 'variavel'])[['n', 'soma_abs', 'soma_abs_persist']].sum()
    L += ['', '## Por região, prazos de 1 a 5 dias: MAE (ganho sobre a persistência)', '',
          '| Região | ' + ' | '.join(VARIAVEIS.values()) + ' |', '|---|' + '---|' * len(VARIAVEIS)]
    for reg in sorted(rg.index.get_level_values('regiao').unique()):
        cel = []
        for v in VARIAVEIS:
            if (reg, v) in rg.index:
                r = rg.loc[(reg, v)]
                cel.append(f"{r.soma_abs / r.n:.2f} ({100 * (1 - r.soma_abs / r.soma_abs_persist):+.0f}%)")
            else:
                cel.append('-')
        L.append(f'| {reg} | ' + ' | '.join(cel) + ' |')
    with open(os.path.join(PASTA, 'ACERTO.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    return br


def main():
    ee.Initialize(project=sp.PROJETO)
    os.makedirs(PASTA, exist_ok=True)
    hoje = estado.agora().date()
    pts = pontos()
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {'id': r.id}) for r in pts.itertuples()])
    inv = inventario(hoje)
    msg_foto = fotografar(hoje, inv, pts, fc)
    n_conf, apagadas = conferir(hoje, inv, pts, fc)
    br = resumir()
    print(msg_foto, f'| {n_conf} dia(s) previsto(s) conferido(s) agora; {apagadas} fotografia(s) encerrada(s)')
    resumo = [msg_foto, f'{n_conf} dia(s) previsto(s) conferido(s) nesta execução']
    situacao = 'ok'
    if br is not None and len(br):
        for v, p in (('tmax_C', 1), ('tmax_C', 5), ('pr_mm', 1), ('pr_mm', 5)):
            if (v, p) in br.index:
                r = br.loc[(v, p)]
                resumo.append(f'{VARIAVEIS[v]}, prazo {p} d: MAE {r.mae:.2f}, ganho sobre a persistência {r.ganho:+.0f}%')
        resumo.append('tabelas completas em rotinas/resultados/previsao/ACERTO.md')
        situacao = 'conferir'
    else:
        resumo.append('ainda nenhum dia previsto virou ERA5 (o primeiro resultado sai em cerca de uma semana)')
    estado.registrar('previsao', situacao, resumo, 'rotinas/resultados/previsao/')


if __name__ == '__main__':
    main()
