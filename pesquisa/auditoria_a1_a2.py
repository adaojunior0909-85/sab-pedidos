# Auditoria profunda, testes A1 (degrau ano a ano), A2 (El Niño / La Niña), A6 (outros saltos) e o teste sintético.
# Regras: pesquisa/PROTOCOLO_AUDITORIA_PROFUNDA.md (congelado em a6ecac8; emendas 1 e 2), fixadas ANTES de rodar.
# Sem Earth Engine: usa os pares mensais que já subiram (resultados_historico, resultados_multifonte, resultados_power
# quando existir) e o RONI do CPC da rotina. Nada é gravado no banco.
#     python pesquisa/auditoria_a1_a2.py sintetico   (5.4: tem de passar antes de olhar os dados reais)
#     python pesquisa/auditoria_a1_a2.py             (tudo: sintético, A1, A2, A6, conta em dobro, sensibilidade)
import glob
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SAIDA = os.path.join(AQUI, 'resultados_auditoria')
REG = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'Brasil']
MULT = {'pr_mm', 'rs', 'u2', 'et_potencial'}                 # rel (%); o resto: dif
SOMA = {'pr_mm', 'et_potencial'}                             # no ano: soma (as outras: média)
TOL = {'pr_mm': 5.0, 'et_potencial': 3.0, 'rs': None, 'u2': 10.0, 'tmax_C': 0.3, 'tmin_C': 0.3, 'RH': 2.0, 'vpd': 0.05}
TOL_RS_MJ = 0.5                                               # radiação: tolerância em MJ/m²/dia (convertida em % abaixo)
VARS = ['pr_mm', 'tmax_C', 'tmin_C', 'rs', 'RH', 'u2', 'et_potencial', 'vpd']
NOME = {'pr_mm': 'Chuva', 'tmax_C': 'Tmax', 'tmin_C': 'Tmin', 'rs': 'Radiação', 'RH': 'Umidade relativa',
        'u2': 'Vento', 'et_potencial': 'ETo', 'vpd': 'VPD'}
UNID = {'pr_mm': '%', 'et_potencial': '%', 'rs': '%', 'u2': '%', 'tmax_C': '°C', 'tmin_C': '°C', 'RH': 'p.p.', 'vpd': 'kPa'}
BASE = (2001, 2015)
RUIDO = (2001, 2019)
AGORA = list(range(2020, 2025))
LANINA = ([1998, 1999, 2000, 2001, 2007, 2008, 2010, 2011, 2012], [2020, 2021, 2022, 2023])
ELNINO = ([1997, 1998, 2015, 2016], [2023, 2024])


def familia(base, var):
    """família de independência (seção 2 + emenda 1); None = só relato."""
    if base in ('imerg', 'persiann') or (base == 'gldas21' and var == 'pr_mm'):
        return 'F1'
    if base == 'terraclimate':
        return 'F2'
    if base == 'chirps':
        return 'F3'
    if base == 'power':
        return 'F4' if var != 'pr_mm' else os.environ.get('POWER_CHUVA_FAMILIA', 'F4')
    if base == 'era5':
        return 'F5'
    if base in ('gldas20', 'gldas21'):
        return None if var == 'pr_mm' else 'F6'
    return None


def carregar():
    h = pd.concat(pd.read_csv(x) for x in glob.glob(os.path.join(AQUI, 'resultados_historico', 'anos', '*.csv')))
    h['base'] = np.where(h.variavel == 'pr_chirps', 'chirps', 'terraclimate')
    h.loc[h.variavel == 'pr_chirps', 'variavel'] = 'pr_mm'
    h = h[(h.base != 'chirps') | (h.ano >= 1981)]
    partes = [h[['regiao', 'ano', 'mes', 'variavel', 'base', 'sab', 'referencia']]]
    for pasta in ('resultados_multifonte', 'resultados_power'):
        arqs = glob.glob(os.path.join(AQUI, pasta, '*', '*.csv'))
        if arqs:
            m = pd.concat(pd.read_csv(x) for x in arqs).rename(columns={'fonte': 'base'})
            partes.append(m[['regiao', 'ano', 'mes', 'variavel', 'base', 'sab', 'referencia']])
    d = pd.concat(partes, ignore_index=True)
    d = d[d.variavel.isin(VARS) & d.regiao.isin(REG)].dropna(subset=['sab', 'referencia'])
    d['familia'] = [familia(b, v) for b, v in zip(d.base, d.variavel)]
    return d.drop_duplicates(['regiao', 'ano', 'mes', 'variavel', 'base'])


def roni():
    # emenda 2: a série completa do CPC que a rotina salva (a tabela de auditoria só tem os meses auditados)
    arqs = sorted(glob.glob(os.path.join(RAIZ, 'rotinas', 'resultados', 'roni', '*', 'RONI_CPC_v6.csv')))
    r = pd.read_csv(arqs[-1])
    return r.set_index(['ano', 'mes'])['RONI'].astype(float)


# ---------------------------------------------------------------- A1 (implementação 1: pandas)
def anual(d):
    g = d.groupby(['regiao', 'variavel', 'base', 'familia', 'ano'], dropna=False)
    a = g.agg(n=('mes', 'nunique'), sab_s=('sab', 'sum'), ref_s=('referencia', 'sum'),
              sab_m=('sab', 'mean'), ref_m=('referencia', 'mean')).reset_index()
    a = a[a.n == 12]
    mult = a.variavel.isin(MULT)
    a['x'] = np.where(mult, a.sab_s / a.ref_s, a.sab_m - a.ref_m)
    a['ref_media'] = a.ref_m
    return a


def rel_ano(a, base=BASE):
    """rel (%) ou dif por série base, relativo à mediana do período-base (emenda 1, item 3)."""
    out = []
    for k, s in a.groupby(['regiao', 'variavel', 'base', 'familia'], dropna=False):
        b = s[s.ano.between(*base)]
        if len(b) < 8:
            continue
        med = b.x.median()
        s = s.copy()
        s['v'] = 100 * (s.x / med - 1) if k[1] in MULT else s.x - med
        out.append(s)
    return pd.concat(out) if out else pd.DataFrame()


def tolerancia(var, ref_media_rs=None):
    if var == 'rs':
        return 100 * TOL_RS_MJ / ref_media_rs
    return TOL[var]


def a1(a, base=BASE, fator_tol=1.0):
    r = rel_ano(a, base)
    r = r[r.familia.notna()]
    fam = r.groupby(['regiao', 'variavel', 'familia', 'ano']).agg(v=('v', 'median'), ref=('ref_media', 'median')).reset_index()
    linhas = []
    for (reg, var, f), s in fam.groupby(['regiao', 'variavel', 'familia']):
        ru = s[s.ano.between(*RUIDO)].v
        mad = (ru - ru.median()).abs().median() if len(ru) else np.nan
        tol = tolerancia(var, s.ref.median()) * fator_tol
        lim = max(3 * mad, tol) if pd.notna(mad) else tol
        for _, x in s.iterrows():
            linhas.append({'regiao': reg, 'variavel': var, 'familia': f, 'ano': int(x.ano), 'v': x.v, 'mad': mad,
                           'tol': tol, 'limite': lim, 'degrau': abs(x.v) > lim, 'sinal': int(np.sign(x.v))})
    return pd.DataFrame(linhas)


def confirmar(t):
    """degrau confirmado no ano (≥ 2 famílias, mesmo sinal) e persistente (≥ 3 anos de 2020–2024)."""
    c = []
    for (reg, var, ano), s in t.groupby(['regiao', 'variavel', 'ano']):
        dg = s[s.degrau]
        mais, menos = (dg.sinal > 0).sum(), (dg.sinal < 0).sum()
        c.append({'regiao': reg, 'variavel': var, 'ano': ano, 'familias': len(s), 'acima': int(mais), 'abaixo': int(menos),
                  'confirmado': max(mais, menos) >= 2, 'sinal': 1 if mais >= 2 else (-1 if menos >= 2 else 0)})
    c = pd.DataFrame(c)
    p = (c[c.ano.isin(AGORA)].groupby(['regiao', 'variavel'])
         .apply(lambda s: pd.Series({'anos_confirmados': int(s.confirmado.sum()),
                                     'persistente': s.confirmado.sum() >= 3,
                                     'sinal': int(np.sign(s[s.confirmado].sinal.sum()))}), include_groups=False)
         .reset_index())
    return c, p


# ---------------------------------------------------------------- A1 (implementação 2: numpy puro, para a conta em dobro)
def a1_numpy(d):
    chaves = {}
    for i, (reg, var, base, fam, ano, mes, sab, ref) in enumerate(zip(d.regiao, d.variavel, d.base, d.familia, d.ano,
                                                                       d.mes, d.sab.to_numpy(), d.referencia.to_numpy())):
        if fam is None:
            continue
        k = (reg, var, base, fam, int(ano))
        e = chaves.setdefault(k, [set(), 0.0, 0.0, []])
        e[0].add(int(mes))
        e[1] += sab
        e[2] += ref
        e[3].append((sab, ref))
    serie = {}
    for (reg, var, base, fam, ano), (meses, ss, rs_, pares) in chaves.items():
        if len(meses) != 12:
            continue
        if var in MULT:
            x = ss / rs_
        else:
            arr = np.array(pares)
            x = arr[:, 0].mean() - arr[:, 1].mean()
        serie.setdefault((reg, var, base, fam), {})[ano] = (x, np.mean([p[1] for p in pares]))
    fam = {}
    for (reg, var, base, f), anos in serie.items():
        b = [anos[y][0] for y in anos if BASE[0] <= y <= BASE[1]]
        if len(b) < 8:
            continue
        med = float(np.median(b))
        for y, (x, rm) in anos.items():
            v = 100 * (x / med - 1) if var in MULT else x - med
            fam.setdefault((reg, var, f, y), []).append((v, rm))
    out = {}
    for k, lst in fam.items():
        out[k] = float(np.median([v for v, _ in lst]))
    return out


# ---------------------------------------------------------------- A2
def mensal(d, base=BASE, sem_roni_extremo=False, rn=None):
    d = d[d.familia.notna()].copy()
    d = d[~((d.variavel == 'pr_mm') & (d.referencia < 5))]
    mult = d.variavel.isin(MULT)
    d['x'] = np.where(mult, d.sab / d.referencia, d.sab - d.referencia)
    out = []
    for k, s in d.groupby(['regiao', 'variavel', 'base', 'familia']):
        b = s[s.ano.between(*base)]
        if b.ano.nunique() < 8:
            continue
        clim = b.groupby('mes').x.median()
        s = s.copy()
        c = s.mes.map(clim)
        s['an'] = 100 * (s.x / c - 1) if k[1] in MULT else s.x - c
        out.append(s)
    m = pd.concat(out)
    m = m.groupby(['regiao', 'variavel', 'familia', 'ano', 'mes']).an.median().reset_index()
    if sem_roni_extremo and rn is not None:
        idx = pd.MultiIndex.from_arrays([m.ano, m.mes])
        m = m[np.abs(rn.reindex(idx).to_numpy()) <= 2]
    return m


def a2_serie(s, rn, tol):
    s = s.set_index(['ano', 'mes']).an.sort_index()
    melhor = None
    for lag in range(4):
        idx = s.index
        alvo = pd.MultiIndex.from_tuples([((a * 12 + m - 1 - lag) // 12, (a * 12 + m - 1 - lag) % 12 + 1) for a, m in idx])
        x = pd.Series(rn.reindex(alvo).to_numpy(), index=idx)
        tr = s[(idx.get_level_values(0) >= 1981) & (idx.get_level_values(0) <= 2019)]
        xt = x.reindex(tr.index)
        ok = xt.notna() & tr.notna()
        if ok.sum() < 60:
            continue
        r = np.corrcoef(xt[ok], tr[ok])[0, 1]
        if melhor is None or abs(r) > abs(melhor[1]):
            melhor = (lag, r, x, tr[ok], xt[ok])
    res = {'lag': None, 'r': np.nan, 'resid_medio': np.nan, 'ep': np.nan, 'a_ok': None,
           'lanina_dif': np.nan, 'elnino_dif': np.nan, 'b_ok': None, 'veredito': 'inconclusivo'}
    if melhor is None:
        return res
    lag, r, x, tr, xt = melhor
    b, a0 = np.polyfit(xt.to_numpy(), tr.to_numpy(), 1)
    resid_tr = tr - (a0 + b * xt)
    agora = s[s.index.get_level_values(0).isin(AGORA)]
    xa = x.reindex(agora.index)
    ok = xa.notna()
    if ok.sum() < 24:
        return {**res, 'lag': lag, 'r': r}
    resid = agora[ok] - (a0 + b * xa[ok])
    rho = max(0.0, pd.Series(resid_tr.to_numpy()).autocorr(1))
    n_ef = ok.sum() * (1 - rho) / (1 + rho)
    ep = resid_tr.std() / np.sqrt(n_ef)
    a_ok = abs(resid.mean()) < tol or abs(resid.mean()) < 2 * ep
    difs = []
    for (passado, presente), sinal, nome in ((LANINA, -1, 'lanina'), (ELNINO, 1, 'elnino')):
        def sel(anos):
            ii = [i for i in s.index if i[0] in anos and pd.notna(rn.get(i)) and (rn.get(i) <= -0.5 if sinal < 0 else rn.get(i) >= 0.5)]
            return s.reindex(ii).dropna()
        p, q = sel(passado), sel(presente)
        difs.append((nome, q.mean() - p.mean() if len(p) and len(q) else np.nan))
    dd = dict(difs)
    aval = [abs(v) < tol for v in dd.values() if pd.notna(v)]
    b_ok = None if not aval else all(aval)
    if b_ok is None:
        ver = 'inconclusivo'
    elif a_ok and b_ok:
        ver = 'explica'
    elif (not a_ok) and (not b_ok):
        ver = 'não explica'
    else:
        ver = 'inconclusivo'
    return {'lag': lag, 'r': r, 'resid_medio': resid.mean(), 'ep': ep, 'a_ok': a_ok,
            'lanina_dif': dd['lanina'], 'elnino_dif': dd['elnino'], 'b_ok': b_ok, 'veredito': ver}


def a2(m, rn, tols):
    linhas = []
    for (reg, var, f), s in m.groupby(['regiao', 'variavel', 'familia']):
        linhas.append({'regiao': reg, 'variavel': var, 'familia': f, **a2_serie(s, rn, tols[(reg, var)])})
    t = pd.DataFrame(linhas)
    v = []
    for (reg, var), s in t.groupby(['regiao', 'variavel']):
        ne, ex = (s.veredito == 'não explica').sum(), (s.veredito == 'explica').sum()
        ver = 'não explica' if ne >= 2 and ex == 0 else ('explica' if ex >= 2 and ne == 0 else 'inconclusivo')
        v.append({'regiao': reg, 'variavel': var, 'nao_explica': int(ne), 'explica': int(ex), 'veredito_A2': ver})
    return t, pd.DataFrame(v)


def tolerancias(a):
    t = {}
    for (reg, var), s in a.groupby(['regiao', 'variavel']):
        t[(reg, var)] = tolerancia(var, s.ref_media.median())
    return t


# ---------------------------------------------------------------- 5.4 teste sintético
def sintetico(d, rn):
    """CHIRPS e TerraClimate reais como 'testemunhas'; o SAB inventado. Caso 1: degrau de +10% a partir de 2020, sem
    ENSO. Caso 2: sem degrau, com efeito do ENSO (SAB/testemunha = 1 + 0,04 × RONI de 1 mês antes, nas duas famílias)."""
    rng = np.random.default_rng(1)
    base = d[(d.variavel == 'pr_mm') & (d.base.isin(['chirps', 'terraclimate']))].copy()
    res = {}
    for caso in ('degrau', 'enso'):
        s = base.copy()
        ruido = rng.normal(0, 0.03, len(s))
        if caso == 'degrau':
            f = 1 + ruido + np.where(s.ano >= 2020, 0.10, 0.0)
        else:
            idx = pd.MultiIndex.from_tuples([((a * 12 + m - 2) // 12, (a * 12 + m - 2) % 12 + 1) for a, m in zip(s.ano, s.mes)])
            f = 1 + ruido + 0.04 * np.nan_to_num(rn.reindex(idx).to_numpy())
        s['sab'] = s.referencia * f
        an = anual(s)
        t = a1(an)
        _, p = confirmar(t)
        m = mensal(s)
        _, v = a2(m, rn, tolerancias(an))
        pb = p[p.regiao == 'Brasil'].iloc[0]
        vb = v[v.regiao == 'Brasil'].iloc[0]
        res[caso] = (bool(pb.persistente), vb.veredito_A2)
    ok = res['degrau'] == (True, 'não explica') and res['enso'][1] == 'explica' and not res['enso'][0]
    return ok, res


# ---------------------------------------------------------------- relatório
def fmt(v, var):
    return f'{v:+.1f}%' if var in MULT else (f'{v:+.3f}' if var == 'vpd' else f'{v:+.2f}')


def main():
    os.makedirs(SAIDA, exist_ok=True)
    rn = roni()
    d = carregar()
    ok, res = sintetico(d, rn)
    print('teste sintético:', ok, res, flush=True)
    L = ['# Auditoria profunda: A1 (degrau ano a ano), A2 (El Niño / La Niña), A6 e conferências', '',
         'Protocolo `pesquisa/PROTOCOLO_AUDITORIA_PROFUNDA.md` (congelado em `a6ecac8`; emendas 1 e 2, antes de rodar), regras '
         'fixadas antes de rodar. Sinal: + = o SAB acima da testemunha em relação a 2001–2015. Famílias: F1 GPCC (IMERG, '
         'PERSIANN, GLDAS-2.1 chuva), F2 TerraClimate, F3 CHIRPS, F4 NASA POWER, F5 ERA5-Land, F6 GLDAS.', '',
         '## 5.4 Teste sintético (antes dos dados reais)', '',
         f'- SAB inventado com degrau de +10% desde 2020: persistente = {res["degrau"][0]}, A2 = {res["degrau"][1]} '
         '(esperado: True, não explica)',
         f'- SAB inventado só com efeito do ENSO: persistente = {res["enso"][0]}, A2 = {res["enso"][1]} '
         '(esperado: False, explica)',
         f'- **{"PASSOU" if ok else "FALHOU: os testes reais NÃO foram olhados"}**', '']
    if not ok:
        open(os.path.join(SAIDA, 'RESULTADOS_A1_A2.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        raise SystemExit('teste sintético falhou')
    if (sys.argv[1:] or [''])[0] == 'sintetico':
        print('\n'.join(L))
        return
    cob = d.groupby(['variavel', 'base']).ano.agg(['min', 'max']).reset_index()
    L += ['## Testemunhas usadas (anos com dado)', '', '| Variável | Base | Família | Anos |', '|---|---|---|---|']
    for r in cob.itertuples():
        L.append(f'| {NOME[r.variavel]} | {r.base} | {familia(r.base, r.variavel) or "só relato"} | {r.min}–{r.max} |')
    L.append('')
    an = anual(d)
    t = a1(an)
    c, p = confirmar(t)
    tols = tolerancias(an)
    m = mensal(d)
    t2, v2 = a2(m, rn, tols)
    t.to_csv(os.path.join(SAIDA, 'A1_por_familia_ano.csv'), index=False)
    c.to_csv(os.path.join(SAIDA, 'A1_confirmacao_ano.csv'), index=False)
    p.to_csv(os.path.join(SAIDA, 'A1_persistencia.csv'), index=False)
    t2.to_csv(os.path.join(SAIDA, 'A2_por_familia.csv'), index=False)
    v2.to_csv(os.path.join(SAIDA, 'A2_veredito.csv'), index=False)
    rel_ano(an).to_csv(os.path.join(SAIDA, 'A1_por_base_ano.csv'), index=False)

    # conta em dobro (5.2)
    nump = a1_numpy(d)
    fam_pd = (rel_ano(an).query('familia == familia').groupby(['regiao', 'variavel', 'familia', 'ano']).v.median())
    difs = [abs(fam_pd.get(k, np.nan) - v) for k, v in nump.items() if k in fam_pd.index]
    maxdif = np.nanmax(difs) if difs else np.nan
    faltam = len(set(nump) ^ set(fam_pd.index))
    L += ['## 5.2 Conta em dobro', '',
          f'A1 refeito por uma segunda implementação (numpy puro): {len(difs)} valores família × ano comparados; maior '
          f'diferença {maxdif:.2e}; chaves só numa das duas: {faltam}. '
          f'**{"OK" if maxdif < 0.01 and faltam == 0 else "DIFERENÇA: a decisão fica suspensa"}**', '']

    # tabela A1 por variável
    L += ['## A1. Degrau ano a ano (2015–2025)', '',
          'Em cada célula: o valor da família no ano; ⚠️ = degrau (|valor| > máx(3 × MAD de 2001–2019; tolerância)). '
          'Linha "confirmado": ≥ 2 famílias com degrau do mesmo sinal.', '']
    for var in VARS:
        tv = t[t.variavel == var]
        if tv.empty:
            continue
        L += [f'### {NOME[var]} ({UNID[var]})', '']
        for reg in REG:
            tr = tv[(tv.regiao == reg) & (tv.ano >= 2015)]
            if tr.empty:
                continue
            anos = sorted(tr.ano.unique())
            L += [f'**{reg}**', '', '| Família | ' + ' | '.join(map(str, anos)) + ' |', '|---|' + '---|' * len(anos)]
            for f, s in tr.groupby('familia'):
                s = s.set_index('ano')
                L.append(f'| {f} | ' + ' | '.join((('⚠️ ' if s.loc[a, 'degrau'] else '') + fmt(s.loc[a, 'v'], var))
                                                   if a in s.index else '-' for a in anos) + ' |')
            cc = c[(c.regiao == reg) & (c.variavel == var)].set_index('ano')
            L.append('| confirmado | ' + ' | '.join(('✅ ' + ('+' if cc.loc[a, 'sinal'] > 0 else '−'))
                                                     if a in cc.index and cc.loc[a, 'confirmado'] else '' for a in anos) + ' |')
            L.append('')
    # A2
    L += ['## A2. O clima (El Niño / La Niña) explica?', '',
          'Por família: regressão da anomalia mensal contra o RONI (1981–2019, defasagem 0–3 com o maior |r|), resíduo '
          'médio de 2020–2024 (condição a: < tolerância ou < 2 erros-padrão); análogos (condição b: diferença entre os '
          'episódios de agora e os do passado < tolerância, nas fases avaliáveis).', '',
          '| Variável | Região | Família | defas. | r | resíduo 2020–24 | 2 EP | (a) | La Niña agora − passado | '
          'El Niño agora − passado | (b) | veredito |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in t2.sort_values(['variavel', 'regiao', 'familia']).itertuples():
        def f_(x):
            return '-' if pd.isna(x) else fmt(x, r.variavel)
        L.append(f'| {NOME[r.variavel]} | {r.regiao} | {r.familia} | {r.lag if r.lag is not None else "-"} | '
                 f'{"-" if pd.isna(r.r) else f"{r.r:+.2f}"} | {f_(r.resid_medio)} | {f_(2 * r.ep) if pd.notna(r.ep) else "-"} | '
                 f'{"-" if r.a_ok is None else ("✅" if r.a_ok else "❌")} | {f_(r.lanina_dif)} | {f_(r.elnino_dif)} | '
                 f'{"sem dado" if r.b_ok is None else ("✅" if r.b_ok else "❌")} | {r.veredito} |')
    L.append('')
    # síntese
    L += ['## Síntese por variável × região (A1 persistente × A2)', '',
          '| Variável | Região | A1: anos confirmados 2020–24 (sinal) | A1 persistente | A2 | Leitura parcial (sem A3) |',
          '|---|---|---|---|---|---|']
    sint = p.merge(v2, on=['regiao', 'variavel'], how='outer')
    for r in sint.sort_values(['variavel', 'regiao']).itertuples():
        pers = bool(r.persistente) if pd.notna(r.persistente) else False
        if pers and r.veredito_A2 == 'não explica':
            leit = 'degrau dos dados (falta o A3 na chuva)' if r.variavel == 'pr_mm' else '**degrau dos dados**'
        elif r.veredito_A2 == 'explica':
            leit = 'clima'
        elif not pers:
            leit = 'sem degrau persistente'
        else:
            leit = 'inconclusivo'
        sn = '' if pd.isna(r.sinal) or r.sinal == 0 else (' (+)' if r.sinal > 0 else ' (−)')
        L.append(f'| {NOME[r.variavel]} | {r.regiao} | {"-" if pd.isna(r.anos_confirmados) else int(r.anos_confirmados)}{sn} | '
                 f'{"sim" if pers else "não"} | {r.veredito_A2 if pd.notna(r.veredito_A2) else "-"} | {leit} |')
    L.append('')
    # A6
    L += ['## A6. Os outros saltos da lista (anos confirmados por década)', '',
          '| Variável | Região | 1961–70 | 2001–10 |', '|---|---|---|---|']
    for var, reg in [('RH', 'Nordeste'), ('et_potencial', 'Norte'), ('tmin_C', 'Brasil'), ('vpd', 'Brasil'), ('rs', 'Brasil'),
                     ('u2', 'Brasil'), ('vpd', 'Norte'), ('rs', 'Norte')]:
        cc = c[(c.regiao == reg) & (c.variavel == var)]
        def conta(a0, a1_):
            s = cc[cc.ano.between(a0, a1_)]
            return f'{int(s.confirmado.sum())} de {len(s)}' if len(s) else 'sem 2 famílias'
        L.append(f'| {NOME[var]} | {reg} | {conta(1961, 1970)} | {conta(2001, 2010)} |')
    L += ['', 'Nota: 2001–2010 fica dentro da base 2001–2015; um degrau nessa década tende a ser subestimado (limitação '
          'registrada; a sensibilidade com base 1991–2019 abaixo mostra o efeito).', '']
    # sensibilidade 5.3
    L += ['## 5.3 Sensibilidade (relatada; não muda a regra)', '', '| Variante | Chuva: regiões com degrau persistente | '
          'Todas as variáveis: séries persistentes |', '|---|---|---|']
    variantes = [('regra', BASE, 1.0), ('base 1991–2019', (1991, 2019), 1.0), ('tolerância × 0,5', BASE, 0.5),
                 ('tolerância × 2', BASE, 2.0)]
    for nome, b, ft in variantes:
        _, pp = confirmar(a1(an, b, ft))
        L.append(f'| {nome} | {", ".join(pp[(pp.variavel == "pr_mm") & pp.persistente].regiao) or "nenhuma"} | '
                 f'{int(pp.persistente.sum())} |')
    _, vv = a2(mensal(d, sem_roni_extremo=True, rn=rn), rn, tols)
    L.append(f'| A2 sem os meses de |RONI| > 2 | chuva "não explica" em: '
             f'{", ".join(vv[(vv.variavel == "pr_mm") & (vv.veredito_A2 == "não explica")].regiao) or "nenhuma"} | - |')
    L.append('')
    open(os.path.join(SAIDA, 'RESULTADOS_A1_A2.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L[:40]))


if __name__ == '__main__':
    main()
