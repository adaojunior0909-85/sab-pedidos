# A3 do protocolo da auditoria profunda: testemunhas físicas da água, sem pluviômetro (família F7). Só leitura.
#   GRACE/GRACE-FO (JPL mascons, NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI, lwe_thickness em cm; a coleção e o período
#     realmente disponíveis são registrados no FONTE.md);
#   SMAP L3 enhanced (NASA/SMAP/SPL3SMP_E/006, soil_moisture_am; o L4 NÃO serve: assimila chuva observada).
# Média mensal por região (5 + Brasil + 27 estados) nos pixels entregues do SAB, na grade do SAB (vm.reduzir).
#     python pesquisa/testemunha_agua.py           (extrai, retomável)
#     python pesquisa/testemunha_agua.py analise   (a regra do A3, sem Earth Engine)
import glob
import os
import sys
import time

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
SAIDA = os.path.join(AQUI, 'resultados_agua')
GRACE_IDS = ['NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI', 'NASA/GRACE/MASS_GRIDS_V04/MASCON']
SMAP_ID = 'NASA/SMAP/SPL3SMP_E/006'


def extrair():
    import validar_metodo_2026 as vm
    ee = vm.ee
    regs = vm.v.regioes(com_ufs=True)
    os.makedirs(os.path.join(SAIDA, 'grace'), exist_ok=True)
    os.makedirs(os.path.join(SAIDA, 'smap'), exist_ok=True)
    limite = time.time() + 60 * float(os.environ.get('TEMPO_MAX_MIN') or 1e9)
    fonte = []
    gid, gcol = None, None
    for g in GRACE_IDS:
        try:
            c = ee.ImageCollection(g).select('lwe_thickness')
            n = c.size().getInfo()
            if n:
                gid, gcol = g, c
                rng = c.reduceColumns(ee.Reducer.minMax(), ['system:time_start']).getInfo()
                fonte.append(f'- GRACE: `{g}`, {n} imagens, de {time.strftime("%Y-%m", time.gmtime(rng["min"] / 1000))} '
                             f'a {time.strftime("%Y-%m", time.gmtime(rng["max"] / 1000))}')
                break
        except Exception as e:  # noqa: BLE001
            fonte.append(f'- GRACE: `{g}` indisponível ({str(e)[:100]})')
    sc = ee.ImageCollection(SMAP_ID).select('soil_moisture_am')
    rng = sc.reduceColumns(ee.Reducer.minMax(), ['system:time_start']).getInfo()
    fonte.append(f'- SMAP: `{SMAP_ID}` (soil_moisture_am), de {time.strftime("%Y-%m-%d", time.gmtime(rng["min"] / 1000))} '
                 f'a {time.strftime("%Y-%m-%d", time.gmtime(rng["max"] / 1000))}')
    with open(os.path.join(SAIDA, 'FONTE.md'), 'w', encoding='utf-8') as f:
        f.write('# Testemunhas da água: coleções lidas\n\n' + '\n'.join(fonte) + f'\n- acesso em {time.strftime("%d/%m/%Y")}\n')
    for ano in range(2002, 2027):
        for nome, col in (('grace', gcol), ('smap', sc)):
            if col is None or (nome == 'smap' and ano < 2015):
                continue
            arq = os.path.join(SAIDA, nome, f'{ano}.csv')
            if os.path.exists(arq):
                continue
            if time.time() > limite:
                raise SystemExit(3)
            bandas, datas = [], []
            if nome == 'grace':
                c = col.filterDate(f'{ano}-01-01', f'{ano + 1}-01-01')
                lst = c.toList(40)
                n = c.size().getInfo()
                for k in range(n):
                    im = ee.Image(lst.get(k))
                    bandas.append(im.rename(f'b{k}'))
                    datas.append(im.date().format('YYYY-MM-dd'))
                datas = ee.List(datas).getInfo() if datas else []
            else:
                for m in range(1, 13):
                    ini = f'{ano}-{m:02d}-01'
                    fim = f'{ano + (m == 12)}-{(m % 12) + 1:02d}-01'
                    cm = col.filterDate(ini, fim)
                    vazio = ee.Image.constant(0).updateMask(ee.Image.constant(0)).toFloat()
                    bandas.append(ee.Image(ee.Algorithms.If(cm.size().gt(0), cm.mean().toFloat(), vazio)).rename(f'b{m - 1}'))
                    datas.append(f'{ano}-{m:02d}-15')
            if not bandas:
                continue
            img = ee.Image.cat(bandas).toFloat()
            nomes = [f'b{k}' for k in range(len(bandas))]
            for t in range(4):
                try:
                    res = vm.reduzir(img, regs, nomes)
                    break
                except Exception as e:  # noqa: BLE001
                    print(f'   ⚠️ {nome} {ano}: {str(e)[:150]}', flush=True)
                    time.sleep(20 * (t + 1))
            else:
                raise RuntimeError(f'{nome} {ano}: 4 tentativas')
            linhas = [{'regiao': reg, 'data': datas[k], 'valor': p.get(f'b{k}')} for reg, p in res.items()
                      for k in range(len(nomes))]
            pd.DataFrame(linhas).to_csv(arq, index=False)
            print(f'   {nome} {ano}: {len(nomes)} meses', flush=True)
    analise()


# ------------------------------------------------------------------ regra do A3
def chuva_mensal():
    """Chuva mensal por região: SAB e cada referência (F1 IMERG/PERSIANN/GLDAS-2.1, F2 TerraClimate, F3 CHIRPS)."""
    import auditoria_a1_a2 as A
    d = A.carregar()
    d = d[(d.variavel == 'pr_mm') & d.familia.isin(['F1', 'F2', 'F3'])]
    sab = d.drop_duplicates(['regiao', 'ano', 'mes']).set_index(['regiao', 'ano', 'mes']).sab.rename('SAB')
    ref = d.pivot_table(index=['regiao', 'ano', 'mes'], columns='base', values='referencia')
    return pd.concat([sab, ref], axis=1)


def anomalia_pct(s, base):
    return 100 * (s / s.loc[base].mean() - 1)


def erro_loo(x, y, treino, teste):
    """RMSE de deixar-um-de-fora no treino e RMSE fora da amostra no teste (regressão linear y ~ x)."""
    xt, yt = x.loc[treino], y.loc[treino]
    ok = xt.notna() & yt.notna()
    xt, yt = xt[ok], yt[ok]
    if len(xt) < 6:
        return np.nan, np.nan
    e = []
    for k in xt.index:
        b, a = np.polyfit(xt.drop(k), yt.drop(k), 1)
        e.append(yt[k] - (a + b * xt[k]))
    b, a = np.polyfit(xt, yt, 1)
    xs, ys = x.reindex(teste), y.reindex(teste)
    ok = xs.notna() & ys.notna()
    if ok.sum() < 3:
        return float(np.sqrt(np.mean(np.square(e)))), np.nan
    return float(np.sqrt(np.mean(np.square(e)))), float(np.sqrt(np.mean(np.square(ys[ok] - (a + b * xs[ok])))))


def analise():
    ch = chuva_mensal()
    L = ['# A3. Testemunhas físicas da água (GRACE e SMAP)', '',
         'Protocolo `pesquisa/PROTOCOLO_AUDITORIA_PROFUNDA.md`, A3. Erro = RMSE da previsão da testemunha pela chuva de cada '
         'base (regressão linear; no período de treino, deixar-um-de-fora; no teste, fora da amostra). REF = mediana, ano a '
         'ano (ou mês a mês), das anomalias das referências F1, F2 e F3. A testemunha fica **com as referências** se o erro '
         'com o SAB crescer > 25% do treino ao teste e o da REF ≤ 10%; **com o SAB** no caso inverso; senão neutra.', '']
    fonte = os.path.join(SAIDA, 'FONTE.md')
    if os.path.exists(fonte):
        L += [open(fonte, encoding='utf-8').read().split('\n', 2)[-1].strip(), '']
    vered = []
    # GRACE: ΔS do ano hidrológico (abril→abril) × chuva de maio a abril
    g = sorted(glob.glob(os.path.join(SAIDA, 'grace', '*.csv')))
    if g:
        gr = pd.concat(pd.read_csv(x) for x in g)
        gr['data'] = pd.to_datetime(gr.data)
        L += ['## GRACE: variação anual do armazenamento × chuva do ano hidrológico', '',
              '| Região | erro SAB treino → teste | erro REF treino → teste | testemunha |', '|---|---|---|---|']
        for reg in ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil']:
            s = gr[gr.regiao == reg].set_index('data').valor.sort_index()
            abril = s[s.index.month == 4]
            abril.index = abril.index.year
            ds = (abril.shift(-1) - abril).dropna()             # ΔS do ano hidrológico que começa em maio do ano y
            c = ch.loc[reg] if reg in ch.index.get_level_values(0) else None
            if c is None or ds.empty:
                continue
            c = c.reset_index()
            c['hidro'] = np.where(c.mes >= 5, c.ano, c.ano - 1)
            cont = c.groupby('hidro').size()
            anual = c.groupby('hidro').sum(min_count=12).drop(columns=['ano', 'mes'])
            anual = anual[cont.reindex(anual.index) == 12]
            treino, teste = list(range(2003, 2020)), list(range(2020, 2025))
            an = anual.apply(lambda s: anomalia_pct(s, [y for y in treino if y in s.dropna().index]))
            refs = [x for x in an.columns if x != 'SAB']
            x_sab, x_ref = an['SAB'], an[refs].median(axis=1)
            es0, es1 = erro_loo(x_sab, ds, treino, teste)
            er0, er1 = erro_loo(x_ref, ds, treino, teste)
            v = veredito(es0, es1, er0, er1)
            vered.append(('GRACE', reg, v))
            L.append(f'| {reg} | {es0:.1f} → {es1:.1f} cm | {er0:.1f} → {er1:.1f} cm | {v} |')
        L.append('')
    # SMAP: anomalia mensal da umidade × anomalia da chuva do mês e do anterior
    sm = sorted(glob.glob(os.path.join(SAIDA, 'smap', '*.csv')))
    if sm:
        s_ = pd.concat(pd.read_csv(x) for x in sm)
        s_['data'] = pd.to_datetime(s_.data)
        L += ['## SMAP: anomalia mensal da umidade do solo 0–5 cm × chuva do mês e do anterior', '',
              '| Região | erro SAB treino → teste | erro REF treino → teste | testemunha |', '|---|---|---|---|']
        for reg in ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil']:
            s = s_[s_.regiao == reg].dropna()
            if s.empty or reg not in ch.index.get_level_values(0):
                continue
            s = s.set_index([s.data.dt.year, s.data.dt.month]).valor
            s.index.names = ['ano', 'mes']
            c = ch.loc[reg]
            treino = [i for i in s.index if 2015 <= i[0] <= 2019]
            teste = [i for i in s.index if 2020 <= i[0] <= 2025]
            clim = s.loc[treino].groupby(level='mes').mean()
            ys = s - clim.reindex(s.index.get_level_values('mes')).to_numpy()

            def anom_chuva(col):
                x = c[col]
                cl = x.loc[[i for i in x.index if 2015 <= i[0] <= 2019]].groupby(level='mes').mean()
                a = 100 * (x / cl.reindex(x.index.get_level_values('mes')).to_numpy() - 1)
                return (a + a.shift(1)) / 2                          # mês e anterior
            x_sab = anom_chuva('SAB')
            refs = [x for x in c.columns if x != 'SAB']
            x_ref = pd.concat([anom_chuva(r_) for r_ in refs], axis=1).median(axis=1)
            es0, es1 = erro_loo(x_sab.clip(-100, 300), ys, treino, teste)
            er0, er1 = erro_loo(x_ref.clip(-100, 300), ys, treino, teste)
            v = veredito(es0, es1, er0, er1)
            vered.append(('SMAP', reg, v))
            L.append(f'| {reg} | {es0:.4f} → {es1:.4f} | {er0:.4f} → {er1:.4f} | {v} |')
        L.append('')
    pd.DataFrame(vered, columns=['testemunha', 'regiao', 'veredito']).to_csv(os.path.join(SAIDA, 'A3_veredito.csv'), index=False)
    with open(os.path.join(SAIDA, 'RESULTADOS_A3.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


def veredito(es0, es1, er0, er1):
    if any(pd.isna(x) for x in (es0, es1, er0, er1)) or es0 == 0 or er0 == 0:
        return 'sem dado'
    cs, cr = es1 / es0 - 1, er1 / er0 - 1
    if cs > 0.25 and cr <= 0.10:
        return 'com as referências'
    if cr > 0.25 and cs <= 0.10:
        return 'com o SAB'
    return 'neutra'


if __name__ == '__main__':
    analise() if (sys.argv[1:] or [''])[0] == 'analise' else extrair()
