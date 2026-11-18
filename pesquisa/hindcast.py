# PESQUISA: previsão estendida de chuva e temperatura. FASE 2: previsões simuladas (hindcast) e escores.
# Segue pesquisa/PROTOCOLO.md (fixado antes dos dados). Roda sem Earth Engine, sobre pesquisa/dados/:
#     python pesquisa/hindcast.py [--dados pesquisa/dados] [--saida pesquisa/resultados]
# Tudo que é ajustado ou escolhido usa só os anos de treino (1982-2010); o teste 2011-2025 só mede.
import argparse
import glob
import os
import sys
import time
import unicodedata

import numpy as np
import pandas as pd
from scipy.special import ndtr

AQUI = os.path.dirname(os.path.abspath(__file__))
ANO_BASE = 1981              # primeiro ano do BR-DWGD extraído (só histórico da persistência)
ANO_INI = 1982               # primeiro ano de emissão (OISST completo)
TREINO_FIM = 2010            # esquema A: treino 1982-2010, teste 2011-
VALID_FIM_AJUSTE = 1999      # escolha do método: ajuste 1982-1999, validação 2000-2010 (dentro do treino)
ALVOS = {'Q1': (1,), 'M2': (2, 3), 'M3': (4, 5)}     # quinzenas depois da emissão (a quinzena 0 é do GFS)
VARIAVEIS = ('pr', 'tx', 'tn')
NOME_VAR = {'pr': 'Chuva (mm)', 'tx': 'Tmax (°C)', 'tn': 'Tmin (°C)'}
NOME_ALVO = {'Q1': 'Q1 (dias ~16-31)', 'M2': 'M2 (dias ~31-60)', 'M3': 'M3 (dias ~61-90)'}
ESTACOES = {'DJF': (12, 1, 2), 'MAM': (3, 4, 5), 'JJA': (6, 7, 8), 'SON': (9, 10, 11)}
SST_PRED = ('nino34_rel', 'nino12', 'tna', 'tsa', 'atsw', 'iod')
# [Rodada 2] grades ampliadas: na rodada 1 a escolha bateu no limite (R1 100, R2 1000)
LAMBDAS_R1 = (0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
LAMBDAS_R2 = (10.0, 100.0, 1000.0, 10000.0, 100000.0)
LIMITE_Z_PERS = 3.0          # [Rodada 2] anomalias de persistência limitadas a ±3 desvios
LAMBDA_FIXO = 1.0            # P1, E1 e E2 (preditores padronizados)
REGIOES = {
    'Norte': ['Acre', 'Amapá', 'Amazonas', 'Pará', 'Rondônia', 'Roraima', 'Tocantins'],
    'Nordeste': ['Alagoas', 'Bahia', 'Ceará', 'Maranhão', 'Paraíba', 'Pernambuco', 'Piauí', 'Rio Grande do Norte',
                 'Sergipe'],
    'Centro-Oeste': ['Distrito Federal', 'Goiás', 'Mato Grosso', 'Mato Grosso do Sul'],
    'Sudeste': ['Espírito Santo', 'Minas Gerais', 'Rio de Janeiro', 'São Paulo'],
    'Sul': ['Paraná', 'Rio Grande do Sul', 'Santa Catarina']}
N_BOOT = 1000


def sem_acento(t):
    return ''.join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower().strip()


UF_REGIAO = {sem_acento(uf): r for r, ufs in REGIOES.items() for uf in ufs}


def dias_quinzena(ano, q):
    m = q // 2 + 1
    fim_mes = (pd.Timestamp(ano, m, 1) + pd.offsets.MonthEnd(0)).day
    return 15 if q % 2 == 0 else fim_mes - 15


# --------------------------------------------------------------------------------------------------------- dados
def carregar(dados):
    pts = pd.read_csv(os.path.join(dados, 'pontos.csv'), dtype={'id': str})
    pts['regiao'] = pts['uf'].map(lambda u: UF_REGIAO.get(sem_acento(u), ''))
    pts = pts[pts['regiao'] != ''].reset_index(drop=True)
    br = pd.concat([pd.read_csv(a, dtype={'id': str}) for a in sorted(glob.glob(os.path.join(dados, 'brdwgd', '*.csv.gz')))])
    br = br[br['id'].isin(pts['id'])]
    anos = np.arange(ANO_BASE, int(br['ano'].max()) + 1)
    idx = {i: k for k, i in enumerate(pts['id'])}
    p = br['id'].map(idx).to_numpy()
    a = (br['ano'] - ANO_BASE).to_numpy()
    serie = {v: np.full((len(pts), len(anos) * 24), np.nan, dtype=np.float64) for v in VARIAVEIS}
    for q in range(24):
        if f'n_{q:02d}' not in br:
            continue
        esperado = br['ano'].map(lambda y, q=q: dias_quinzena(y, q)).to_numpy()
        ok = br[f'n_{q:02d}'].to_numpy() == esperado          # quinzena incompleta fica de fora
        for v in VARIAVEIS:
            serie[v][p[ok], a[ok] * 24 + q] = br[f'{v}_{q:02d}'].to_numpy()[ok]
    sst = pd.read_csv(os.path.join(dados, 'sst_mensal.csv'))
    dias_mes = sst.apply(lambda l: (pd.Timestamp(int(l['ano']), int(l['mes']), 1) + pd.offsets.MonthEnd(0)).day, axis=1)
    sst = sst[sst['n_dias'] >= dias_mes]                       # só meses completos
    n_meses = (len(anos) + 1) * 12
    caixas = {}
    for c in ('nino34', 'nino12', 'tropical', 'tna', 'tsa', 'atsw', 'iod_w', 'iod_e'):
        arr = np.full(n_meses, np.nan)
        mi = ((sst['ano'] - ANO_BASE) * 12 + sst['mes'] - 1).to_numpy()
        ok = (mi >= 0) & (mi < n_meses)
        arr[mi[ok]] = sst[c].to_numpy()[ok]
        caixas[c] = arr
    return pts, anos, serie, caixas


def anomalias_sst(caixas):
    """Anomalias mensais (climatologia 1982-2010 de cada mês) e os 6 preditores. nino34_rel é a média de 3 meses
    do Niño 3.4 menos a faixa tropical (como o RONI, sem o fator de variância)."""
    n = len(next(iter(caixas.values())))
    mes = np.arange(n) % 12
    ano = ANO_BASE + np.arange(n) // 12
    base = (ano >= ANO_INI) & (ano <= TREINO_FIM)
    anom = {}
    for c, arr in caixas.items():
        clima = np.array([np.nanmean(arr[base & (mes == m)]) for m in range(12)])
        anom[c] = arr - clima[mes]
    rel = anom['nino34'] - anom['tropical']
    rel3 = np.full(n, np.nan)
    rel3[2:] = (rel[2:] + rel[1:-1] + rel[:-2]) / 3
    return {'nino34_rel': rel3, 'nino12': anom['nino12'], 'tna': anom['tna'], 'tsa': anom['tsa'],
            'atsw': anom['atsw'], 'iod': anom['iod_w'] - anom['iod_e']}


def montar(serie, anos, sst, v, alvo):
    """Arrays de uma variável e alvo para as 24 quinzenas de emissão: Y [Q,P,NY] (alvo), S [Q,NY,6] (preditores do
    mar, padronizados no treino), PERS [Q,P,NY,2] (persistência), ENSO [Q,NY] (Niño 3.4 relativo bruto)."""
    S_ = serie[v]
    Sz = np.sqrt(np.clip(S_, 0, None)) if v == 'pr' else S_     # [Rodada 2] persistência da chuva na raiz
    P, T = S_.shape
    iy = np.arange(ANO_INI, anos[-1] + 1)
    NY = len(iy)
    treino_anos = (anos >= ANO_INI) & (anos <= TREINO_FIM)
    porq = Sz.reshape(P, len(anos), 24)
    clima_q = np.nanmean(porq[:, treino_anos, :], axis=1)
    dp_q = np.nanstd(porq[:, treino_anos, :], axis=1)
    dp_q[dp_q == 0] = np.nan
    Y = np.full((24, P, NY), np.nan)
    PERS = np.full((24, P, NY, 2), np.nan)
    SS = np.full((24, NY, len(SST_PRED)), np.nan)
    EN = np.full((24, NY), np.nan)
    for q in range(24):
        t = (iy - ANO_BASE) * 24 + q
        partes = []
        for off in ALVOS[alvo]:
            col = np.full((P, NY), np.nan)
            ok = t + off < T
            col[:, ok] = S_[:, t[ok] + off]
            partes.append(col)
        Y[q] = np.sum(partes, axis=0) if v == 'pr' else np.mean(partes, axis=0)
        z1 = np.clip((Sz[:, t - 1] - clima_q[:, (t - 1) % 24]) / dp_q[:, (t - 1) % 24], -LIMITE_Z_PERS, LIMITE_Z_PERS)
        z2 = np.clip((Sz[:, t - 2] - clima_q[:, (t - 2) % 24]) / dp_q[:, (t - 2) % 24], -LIMITE_Z_PERS, LIMITE_Z_PERS)
        PERS[q, :, :, 0] = z1
        PERS[q, :, :, 1] = (z1 + z2) / 2
        mi = (iy - ANO_BASE) * 12 + (q // 2) - 1          # mês anterior ao da emissão
        for k, c in enumerate(SST_PRED):
            SS[q, :, k] = sst[c][mi]
        EN[q] = sst['nino34_rel'][mi]
    tr = iy <= TREINO_FIM
    mu = np.nanmean(SS[:, tr, :], axis=1, keepdims=True)
    sd = np.nanstd(SS[:, tr, :], axis=1, keepdims=True)
    SS = (SS - mu) / sd
    return iy, Y, SS, PERS, EN


# ------------------------------------------------------------------------------------------------------ modelos
def ridge(X, y, w, pen):
    """Ridge ponderada em lote. X [B,n,k], y [B,n], w [B,n] (0/1), pen [k]. Devolve beta [B,k], Ainv [B,k,k]."""
    k = X.shape[-1]
    Xw = X * w[..., None]
    A = np.matmul(Xw.transpose(0, 2, 1), X) + np.diag(np.asarray(pen, float)) + 1e-9 * np.eye(k)
    b = np.matmul(Xw.transpose(0, 2, 1), np.nan_to_num(y)[..., None])[..., 0]
    Ainv = np.linalg.inv(A)
    return np.matmul(Ainv, b[..., None])[..., 0], Ainv


def ajustar_ponto(X, y, w, pen):
    """Ajuste por ponto: previsão de todos os anos com o ajuste em w e previsão 'deixando o ano de fora' (exata para
    ridge com penalidade fixa) nos anos de w. Devolve (pred, pred_loo, var_residuo)."""
    B, n, k = X.shape
    beta, Ainv = ridge(X, y, w, pen)
    pred = np.matmul(X, beta[..., None])[..., 0]
    h = np.einsum('bnk,bkl,bnl->bn', X, Ainv, X) * w
    res = np.where(w > 0, y - pred, np.nan)
    loo = np.where(w > 0, y - res / np.clip(1 - h, 1e-6, None), np.nan)
    nval = w.sum(1)
    var = np.nansum(res ** 2, axis=1) / np.clip(nval - 2, 1, None)
    ruim = nval < max(3, 2 + 1)
    pred[ruim] = np.nan
    loo[ruim] = np.nan
    return pred, loo, var


def desenhos(Y, SS, PERS, EN, iy):
    """Matrizes de cada método por ponto, SEM tendência: {nome: (X [Q,P,NY,k], lambda)}. A 1ª coluna (constante) não
    tem penalidade; lambda None = escolhido no treino (R1). As versões com tendência (_t) são estes mesmos modelos
    ajustados à série sem a tendência do ponto (tendencia_ponto) e somados a ela (registro 1 do protocolo)."""
    Q, P, NY = Y.shape
    um = np.ones((Q, P, NY, 1))
    sst = np.broadcast_to(SS[:, None, :, :], (Q, P, NY, SS.shape[-1]))
    nino = np.broadcast_to(SS[:, None, :, :1], (Q, P, NY, 1))
    cat = np.stack([(EN >= 0.5), (EN <= -0.5)], axis=-1).astype(float)
    cat = np.broadcast_to(cat[:, None, :, :], (Q, P, NY, 2))
    pers = np.nan_to_num(PERS)
    return {'C0': (um, 0.0),
            'P1': (np.concatenate([um, pers], -1), LAMBDA_FIXO),
            'E1': (np.concatenate([um, cat], -1), LAMBDA_FIXO),
            'E2': (np.concatenate([um, np.nan_to_num(nino)], -1), LAMBDA_FIXO),
            'R1': (np.concatenate([um, np.nan_to_num(sst), pers], -1), None)}


def tendencia_ponto(yf, w, ac):
    """[Registro 1] Uma tendência linear por ponto, com todas as quinzenas de emissão juntas (constante própria de
    cada quinzena, inclinação comum): 24 vezes mais dados que a tendência de cada quinzena, que saía tão ruidosa
    quanto a própria tendência. yf, w [Q,P,NY]; ac [NY] (anos/10 a partir de 2000). Devolve b [P]."""
    y0 = np.nan_to_num(yf)
    sw = np.clip(w.sum(-1, keepdims=True), 1e-9, None)
    yb = (w * y0).sum(-1, keepdims=True) / sw
    ab = (w * ac).sum(-1, keepdims=True) / sw
    num = (w * (y0 - yb) * (ac - ab)).sum((0, 2))
    den = (w * (ac - ab) ** 2).sum((0, 2))
    return np.where(den > 0, num / np.clip(den, 1e-9, None), 0.0)


def r2_ajustar(Xr1, yf, w, lam, reg_id):
    """R2: C1 por ponto e, sobre o resíduo padronizado, ridge com os coeficientes comuns aos pontos da região e às
    quinzenas de emissão vizinhas (q-1, q, q+1). Devolve (pred, var_residuo) para todos os anos."""
    Q, P, NY, k = Xr1.shape
    B = Q * P
    nl = 1
    Xc = np.ascontiguousarray(Xr1[..., :nl]).reshape(B, NY, nl)
    beta1, _ = ridge(Xc, yf.reshape(B, NY), w.reshape(B, NY), [0] * nl)
    c1 = np.matmul(Xc, beta1[..., None])[..., 0].reshape(Q, P, NY)
    r = yf - c1
    nval = w.sum(-1)
    sd = np.sqrt(np.nansum(np.where(w > 0, r, 0) ** 2, -1) / np.clip(nval - nl, 1, None))
    sd[sd == 0] = np.nan
    zr = r / sd[..., None]
    Z = Xr1[..., 2:]
    kz = Z.shape[-1]
    pred = c1.copy()
    for g in np.unique(reg_id):
        pg = reg_id == g
        Zg, zg = Z[:, pg], zr[:, pg]
        okg = (w[:, pg] > 0) & np.isfinite(zg)
        # somas por quinzena de emissão; a janela q-1..q+1 é a soma de 3 delas
        Zm = np.where(okg[..., None], Zg, 0)
        ZZ = np.einsum('qpnk,qpnl->qkl', Zm, Zm)
        Zy = np.einsum('qpnk,qpn->qk', Zm, np.where(okg, zg, 0))
        nq = okg.sum((1, 2))
        for q in range(Q):
            lo, hi = max(q - 1, 0), min(q + 2, Q)
            if nq[lo:hi].sum() < 10:
                continue
            beta = np.linalg.solve(ZZ[lo:hi].sum(0) + lam * np.eye(kz), Zy[lo:hi].sum(0))
            pred[q, pg] = c1[q, pg] + sd[q, pg][..., None] * (Zg[q] @ beta)
    res = np.where(w > 0, yf - pred, np.nan)
    var = np.nansum(res ** 2, -1) / np.clip(nval - 2, 1, None)
    return pred, var


def de_volta(pred, var, transf):
    """Volta à escala original: na raiz, E[x] = E[sqrt x]^2 + var(sqrt x)."""
    if transf == 'raiz':
        return np.clip(pred, 0, None) ** 2 + var[..., None]
    return pred


# ------------------------------------------------------------------------------------------------- uma variável
def rodar_config(Y, SS, PERS, EN, iy, reg_id, transf, log):
    """Todas as previsões de uma variável/alvo. Devolve {método: {'TL','V','A','B'}} [Q,P,NY] na escala original:
    TL = deixar um ano de fora dentro do treino (lambda e dispersão das probabilidades);
    V  = ajuste 1982-1999 -> validação 2000-2010 (escolha do método; registro 1 do protocolo);
    A  = treino 1982-2010 -> teste 2011- (só mede);  B = deixar um ano de fora em 1982-2025 (estabilidade).
    Versões _t: tendência por ponto (tendencia_ponto) ajustada em cada esquema; C0 com tendência = C1."""
    Q, P, NY = Y.shape
    yf0 = np.sqrt(np.clip(Y, 0, None)) if transf == 'raiz' else Y
    valido = np.isfinite(yf0)
    tr = iy <= TREINO_FIM
    W = {'TL': (valido & tr[None, None, :]).astype(float),
         'V': (valido & (iy <= VALID_FIM_AJUSTE)[None, None, :]).astype(float),
         'B': valido.astype(float)}
    W['A'] = W['TL']
    ac = (iy - 2000) / 10.0
    des = desenhos(Y, SS, PERS, EN, iy)
    B = Q * P
    out = {}
    for com_tend in (False, True):
        # tendência de cada esquema (TL e B usam a do próprio conjunto: pequeno vazamento, só nesses dois)
        tend = {e: (tendencia_ponto(yf0, W[e], ac)[None, :, None] * ac[None, None, :] if com_tend else 0.0)
                for e in ('TL', 'V', 'A', 'B')}
        suf = 't' if com_tend else ''
        for nome, (X, lam) in des.items():
            nome_s = ('C1' if nome == 'C0' else nome + 't') if com_tend else nome
            Xb = np.ascontiguousarray(X).reshape(B, NY, X.shape[-1])
            k = X.shape[-1]
            if lam is None:                                 # R1: lambda escolhido pelo erro "ano de fora" no treino
                melhor = None
                yb = (yf0 - tend['TL']).reshape(B, NY)
                for lam_ in LAMBDAS_R1:
                    _, loo, var = ajustar_ponto(Xb, yb, W['TL'].reshape(B, NY), [0] + [lam_] * (k - 1))
                    e = np.nanmean((de_volta(loo.reshape(Q, P, NY) + tend['TL'], var.reshape(Q, P), transf) - Y) ** 2)
                    if melhor is None or e < melhor[0]:
                        melhor = (e, lam_)
                lam = melhor[1]
                log.append(f'{nome_s} {transf}: lambda {lam}')
            pen = [0] + [lam] * (k - 1)
            r = {}
            for e in ('TL', 'V', 'A', 'B'):
                if e == 'A':
                    continue
                yb = (yf0 - tend[e]).reshape(B, NY)
                pred, loo, var = ajustar_ponto(Xb, yb, W[e].reshape(B, NY), pen)
                if e == 'TL':
                    r['A'] = de_volta(pred.reshape(Q, P, NY) + tend['A'], var.reshape(Q, P), transf)
                    r['TL'] = de_volta(loo.reshape(Q, P, NY) + tend['TL'], var.reshape(Q, P), transf)
                elif e == 'V':
                    r['V'] = de_volta(pred.reshape(Q, P, NY) + tend['V'], var.reshape(Q, P), transf)
                else:
                    r['B'] = de_volta(loo.reshape(Q, P, NY) + tend['B'], var.reshape(Q, P), transf)
            out[nome_s] = r
        # R2: regiões x quinzenas vizinhas; deixar um ano de fora tira o ano INTEIRO (todos os pontos), não uma linha
        Xr1 = np.ascontiguousarray(des['R1'][0])
        nome_s = 'R2' + suf
        melhor = None
        for lam in LAMBDAS_R2:
            tl = np.full((Q, P, NY), np.nan)
            for j in np.where(tr)[0]:
                w = W['TL'].copy()
                w[..., j] = 0
                t_j = tendencia_ponto(yf0, w, ac)[None, :, None] * ac if com_tend else 0.0
                pred, var = r2_ajustar(Xr1, yf0 - t_j, w, lam, reg_id)
                tl[..., j] = de_volta(pred + t_j, var, transf)[..., j]
            e = np.nanmean((tl - Y)[..., tr] ** 2)
            if melhor is None or e < melhor[0]:
                melhor = (e, lam, tl)
        lam = melhor[1]
        log.append(f'{nome_s} {transf}: lambda {lam}')
        pred, var = r2_ajustar(Xr1, yf0 - tend['A'], W['A'], lam, reg_id)
        pA = de_volta(pred + tend['A'], var, transf)
        pred, var = r2_ajustar(Xr1, yf0 - tend['V'], W['V'], lam, reg_id)
        pV = de_volta(pred + tend['V'], var, transf)
        pB = np.full((Q, P, NY), np.nan)
        for j in range(NY):
            w = W['B'].copy()
            w[..., j] = 0
            t_j = tendencia_ponto(yf0, w, ac)[None, :, None] * ac if com_tend else 0.0
            pred, var = r2_ajustar(Xr1, yf0 - t_j, w, lam, reg_id)
            pB[..., j] = de_volta(pred + t_j, var, transf)[..., j]
        out[nome_s] = {'TL': melhor[2], 'V': pV, 'A': pA, 'B': pB}
    for nome, comp in (('ENS', ('E2', 'P1', 'R2')), ('ENSt', ('C1', 'E2t', 'P1t', 'R2t'))):
        out[nome] = {e: np.mean([out[m][e] for m in comp], axis=0) for e in ('TL', 'V', 'A', 'B')}
    if transf == 'raiz':
        out = {f'{m}_raiz': d for m, d in out.items() if m != 'C0'}
    return out


# -------------------------------------------------------------------------------------------------------- escores
def escores(Y, prev, iy, mascara, sigma_tl, terc):
    """Escores de um método numa célula (mascara [Q,P] de quinzenas x pontos), no teste do esquema A e no B."""
    te = iy > TREINO_FIM
    c0A = prev['C0']['A']
    out = {}
    for m, d in prev.items():
        pA, pB, pTL = d['A'], d['B'], d['TL']
        sel = mascara[..., None] & te[None, None, :] & np.isfinite(Y) & np.isfinite(pA) & np.isfinite(c0A)
        if sel.sum() < 30:
            continue
        y, f, c = Y[sel], pA[sel], c0A[sel]
        ano = np.broadcast_to(iy[None, None, :], Y.shape)[sel]
        anos_u = np.unique(ano)
        se_m = np.array([np.sum((f[ano == a] - y[ano == a]) ** 2) for a in anos_u])
        se_c = np.array([np.sum((c[ano == a] - y[ano == a]) ** 2) for a in anos_u])
        msess = 1 - se_m.sum() / se_c.sum()
        rng = np.random.default_rng(42)
        boot = rng.integers(0, len(anos_u), (N_BOOT, len(anos_u)))
        bs = 1 - se_m[boot].sum(1) / se_c[boot].sum(1)
        c1A = prev['C1']['A'][sel] if 'C1' in prev else c
        msess_c1 = 1 - np.sum((f - y) ** 2) / np.sum((c1A - y) ** 2)
        fa, oa = f - c, y - c
        acc = float(np.corrcoef(fa, oa)[0, 1]) if np.std(fa) > 0 else 0.0
        t1, t2 = terc[0][sel], terc[1][sel]
        cat_o = (y > t1).astype(int) + (y > t2)
        cat_f = (f > t1).astype(int) + (f > t2)
        s = np.broadcast_to(sigma_tl[m][..., None], Y.shape)[sel]
        s = np.where(np.isfinite(s) & (s > 0), s, np.nan)
        p1 = ndtr((t1 - f) / s)
        p12 = ndtr((t2 - f) / s)
        o1, o12 = (cat_o == 0).astype(float), (cat_o <= 1).astype(float)
        rps = (p1 - o1) ** 2 + (p12 - o12) ** 2
        rps_c = (1 / 3 - o1) ** 2 + (2 / 3 - o12) ** 2
        rpss = 1 - np.nanmean(rps) / np.nanmean(rps_c)
        val = (iy > VALID_FIM_AJUSTE) & (iy <= TREINO_FIM)
        pV = d['V']
        v_sel = mascara[..., None] & val[None, None, :] & np.isfinite(Y) & np.isfinite(pV)
        mse_v = np.mean((pV[v_sel] - Y[v_sel]) ** 2) if v_sel.any() else np.nan
        tl_sel = mascara[..., None] & (~te)[None, None, :] & np.isfinite(Y) & np.isfinite(pTL)
        mse_tl = np.mean((pTL[tl_sel] - Y[tl_sel]) ** 2) if tl_sel.any() else np.nan
        b_sel = mascara[..., None] & np.isfinite(Y) & np.isfinite(pB) & np.isfinite(prev['C0']['B'])
        msess_b = 1 - np.sum((pB[b_sel] - Y[b_sel]) ** 2) / np.sum((prev['C0']['B'][b_sel] - Y[b_sel]) ** 2)
        out[m] = {'MSESS': msess, 'MSESS_ic_inf': np.percentile(bs, 2.5), 'MSESS_ic_sup': np.percentile(bs, 97.5),
                  'MSESS_vs_C1': msess_c1, 'ACC': acc, 'MAE': np.mean(np.abs(f - y)), 'MAE_C0': np.mean(np.abs(c - y)),
                  'acerto_tercil': np.mean(cat_f == cat_o), 'RPSS': rpss, 'MSESS_B': msess_b, 'EQM_validacao': mse_v, 'EQM_treino_loo': mse_tl,
                  'n': int(sel.sum())}
    return out


def tem_tendencia(m):
    base = m.split('_')[0]
    return base == 'C1' or (base.endswith('t') and base != 'C0')


def escolher(df):
    """[Registro 2 do protocolo] Escolha em duas decisões, só com o treino (o teste 2011- não entra):
    1. usar tendência ou não, por variável e região, juntando estações e alvos: C1 x C0 na validação para frente
       (ajuste 1982-1999, validação 2000-2010), a única decisão que depende de extrapolar no tempo;
    2. o método, dentro da família escolhida, pelo menor erro "ano de fora" em 1982-2010 (29 anos, mais estável)."""
    df = df.copy()
    df['familia_tendencia'] = df['metodo'].map(tem_tendencia)
    # [Rodada 2] a decisão compara ENSt x ENS (tendência junto com os outros preditores), não C1 x C0
    soma = df[df['metodo'].isin(['ENS', 'ENSt'])].pivot_table(index=['variavel', 'regiao'], columns='metodo',
                                                             values='EQM_validacao', aggfunc='sum')
    usar = (soma['ENSt'] < soma['ENS']).to_dict()
    df['usa_tendencia'] = [usar.get((v, r), False) for v, r in zip(df['variavel'], df['regiao'])]
    cand = df[(df['familia_tendencia'] == df['usa_tendencia']) | (df['metodo'] == 'C0')]
    cand = cand[(cand['metodo'] != 'C0') | ~cand['usa_tendencia']]
    return (cand.sort_values('EQM_treino_loo').groupby(['variavel', 'alvo', 'estacao', 'regiao'], as_index=False)
            .first())


def aprovado(r, m):
    base = r['MSESS'] >= 0.05 and r['MSESS_ic_inf'] > 0 and r['RPSS'] > 0 and r['MSESS_B'] > 0
    return bool(base and (m.split('_')[0] in ('C0', 'C1') or r['MSESS_vs_C1'] > 0))



# ------------------------------------------------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dados', default=os.path.join(AQUI, 'dados'))
    ap.add_argument('--saida', default=os.path.join(AQUI, 'resultados'))
    ap.add_argument('--variaveis', default=','.join(VARIAVEIS))
    ap.add_argument('--alvos', default=','.join(ALVOS))
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.saida, exist_ok=True)
    pts, anos, serie, caixas = carregar(a.dados)
    sst = anomalias_sst(caixas)
    regs = list(REGIOES)
    reg_id = pts['regiao'].map(regs.index).to_numpy()
    cascavel = pts['grupo'].astype(str).str.contains('Cascavel').to_numpy()
    celulas_reg = {r: pts['regiao'].to_numpy() == r for r in regs}
    celulas_reg['Paraná'] = pts['uf'].map(sem_acento).to_numpy() == 'parana'
    if cascavel.any():
        celulas_reg['Cascavel (pixel)'] = cascavel
    print(f'{len(pts)} pontos; anos {anos[0]}-{anos[-1]}; regiões: '
          + ', '.join(f'{r} {m.sum()}' for r, m in celulas_reg.items()))
    linhas, log = [], []
    for v in a.variaveis.split(','):
        for alvo in a.alvos.split(','):
            iy, Y, SS, PERS, EN = montar(serie, anos, sst, v, alvo)
            prev = {}
            for transf in (('mm', 'raiz') if v == 'pr' else ('mm',)):
                prev.update(rodar_config(Y, SS, PERS, EN, iy, reg_id, transf, log))
            tr = iy <= TREINO_FIM
            terc = (np.nanpercentile(Y[..., tr], 100 / 3, axis=-1)[..., None] + 0 * Y,
                    np.nanpercentile(Y[..., tr], 200 / 3, axis=-1)[..., None] + 0 * Y)
            sigma = {m: np.sqrt(np.nanmean((d['TL'] - Y)[..., tr] ** 2, axis=-1)) for m, d in prev.items()}
            for est, meses in ESTACOES.items():
                qmask = np.isin(np.arange(24) // 2 + 1, meses)
                for reg, pm in celulas_reg.items():
                    masc = qmask[:, None] & pm[None, :]
                    for m, r in escores(Y, prev, iy, masc, sigma, terc).items():
                        linhas.append({'variavel': v, 'alvo': alvo, 'estacao': est, 'regiao': reg, 'metodo': m,
                                       **r, 'aprovado_regra': aprovado(r, m)})
            print(f'  {v} {alvo}: {time.time() - t0:.0f} s | ' + ' | '.join(log[-3:]))
    df = pd.DataFrame(linhas)
    df.to_csv(os.path.join(a.saida, 'metricas_todos_os_metodos.csv'), index=False, float_format='%.4f')
    esc = escolher(df)
    esc['produto'] = np.where(esc['aprovado_regra'] & (esc['metodo'] != 'C0'), esc['metodo'],
                              'sem sinal: média histórica')
    esc.to_csv(os.path.join(a.saida, 'metodo_escolhido_por_celula.csv'), index=False, float_format='%.4f')
    relatorio(df, esc, a.saida, log, pts)
    print(f'✅ Terminado em {(time.time() - t0) / 60:.1f} min. Resultados em {a.saida}')


def relatorio(df, esc, saida, log, pts):
    L = ['# Resultados: previsão estendida de chuva e temperatura', '',
         f'Protocolo: `pesquisa/PROTOCOLO.md`. {len(pts)} pontos classe A. Treino 1982-2010; teste 2011 em diante. '
         'MSESS > 0 = melhor que a média histórica; acerto de tercil: 33% = acaso.', '',
         '## 1. Quantas células têm previsão aprovada (5 regiões x 4 estações = 20 por linha)', '',
         '| Variável | Alvo | Aprovadas | Métodos escolhidos nas aprovadas |', '|---|---|---|---|']
    macro = esc[esc['regiao'].isin(REGIOES)]
    for (v, alvo), g in macro.groupby(['variavel', 'alvo'], sort=False):
        ap_ = g[g['produto'] != 'sem sinal: média histórica']
        L.append(f'| {NOME_VAR[v]} | {NOME_ALVO[alvo]} | {len(ap_)} de {len(g)} | '
                 f'{", ".join(f"{m} ({n})" for m, n in ap_["metodo"].value_counts().items()) or "-"} |')
    for reg in ('Paraná', 'Cascavel (pixel)'):
        g = esc[esc['regiao'] == reg]
        if g.empty:
            continue
        L += ['', f'## {"2" if reg == "Paraná" else "3"}. {reg}: método escolhido (pelo treino) e escore no teste', '',
              '| Variável | Alvo | Estação | Método | MSESS (IC 95%) | Acerto tercil | RPSS | Produto |',
              '|---|---|---|---|---|---|---|---|']
        for _, r in g.iterrows():
            L.append(f"| {NOME_VAR[r['variavel']]} | {r['alvo']} | {r['estacao']} | {r['metodo']} | "
                     f"{r['MSESS']:+.2f} ({r['MSESS_ic_inf']:+.2f} a {r['MSESS_ic_sup']:+.2f}) | "
                     f"{100 * r['acerto_tercil']:.0f}% | {r['RPSS']:+.2f} | {r['produto']} |")
    L += ['', '## 4. Média de cada método no Brasil (sem escolha; MSESS médio das 20 células, teste)', '',
          '| Variável | Alvo | ' + ' | '.join(sorted(df['metodo'].unique())) + ' |',
          '|---|---|' + '---|' * df['metodo'].nunique()]
    tab = df[df['regiao'].isin(REGIOES)].pivot_table(index=['variavel', 'alvo'], columns='metodo', values='MSESS',
                                                      aggfunc='mean', sort=False)
    for (v, alvo), r in tab.iterrows():
        L.append(f'| {NOME_VAR[v]} | {alvo} | ' + ' | '.join(f'{r.get(m, np.nan):+.2f}' for m in sorted(df['metodo'].unique())) + ' |')
    L += ['', '## Parâmetros escolhidos no treino', ''] + [f'- {x}' for x in log]
    with open(os.path.join(saida, 'RESULTADOS.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
